mod model;
mod python;
mod specialized;

use std::net::{IpAddr, SocketAddr};
use std::sync::{Arc, Mutex, MutexGuard};

use askama::Template;
use axum::body::{Body, Bytes};
use axum::extract::{DefaultBodyLimit, Form, FromRequest, Query, Request, State};
use axum::http::{HeaderMap, HeaderValue, Method, StatusCode, header, uri::Authority};
use axum::middleware::{self, Next};
use axum::response::{Html, IntoResponse, Response};
use axum::routing::{get, post};
use axum::{Json, Router};
use serde::Deserialize;
use serde_json::{Map, Value, json};

pub use model::{Action, Capabilities, FigureSpec};
pub use python::PythonBridge;

const HTMX: &[u8] = include_bytes!("../../dashboard/static/htmx.min.js");
const EDITOR_JS: &[u8] = include_bytes!("../../dashboard/static/editor.js");
// ponytail: bounded inline data keeps a local mistake from exhausting memory;
// raise this ceiling only when real embedded datasets need more than 16 MiB.
const MAX_BODY_BYTES: usize = 16 * 1024 * 1024;

#[derive(Clone)]
struct AppState {
    // ponytail: one global session plus synchronous bridge is enough locally;
    // use cookie-keyed sessions + spawn_blocking if concurrent users matter.
    session: Arc<Mutex<Session>>,
    bridge: PythonBridge,
    controls: Arc<Controls>,
}

struct Controls {
    layers: Vec<LayerChoice>,
    themes: Vec<String>,
    projections: Vec<String>,
    coordinate_roles: Vec<(String, String)>,
    coordinate_names: String,
}

struct LayerChoice {
    name: String,
    required: String,
    optional: String,
}

struct CurrentControls {
    title: String,
    theme: String,
    projection: String,
    width: String,
    height: String,
    active: usize,
    panel_count: usize,
    panel_names: Vec<String>,
    layout_actions: Vec<(String, String)>,
    shared_guides_action: String,
    facet_template_action: Option<String>,
    layer_actions: Vec<(usize, String)>,
    cluster_cuts: Vec<ClusterCutControl>,
    axes: Vec<specialized::AxisControls>,
    has_y2: bool,
    has_z: bool,
    layout: String,
}

struct ClusterCutControl {
    axis: &'static str,
    label: &'static str,
    height: String,
    items: Vec<ClusterCutItem>,
    partitioned: bool,
    selected: String,
}

struct ClusterCutItem {
    index: u64,
    label: String,
    chosen: bool,
}

fn cluster_cuts(layout: &Value) -> Vec<ClusterCutControl> {
    [("row", "Row"), ("col", "Column")]
        .into_iter()
        .filter_map(|(axis, label)| {
            let entry = layout.get("matrix_cuts")?.get(axis)?;
            let anchor = entry["anchor"].as_u64();
            let items = entry["items"]
                .as_array()?
                .iter()
                .filter_map(|item| {
                    let index = item["index"].as_u64()?;
                    Some(ClusterCutItem {
                        index,
                        label: item["label"].as_str()?.into(),
                        chosen: anchor == Some(index),
                    })
                })
                .collect();
            let partitioned = entry["partition"].is_object();
            let selected = entry["partition"]["selected"]
                .as_array()
                .map(|ids| {
                    ids.iter()
                        .map(Value::to_string)
                        .collect::<Vec<_>>()
                        .join(", ")
                })
                .filter(|text| !text.is_empty())
                .unwrap_or_else(|| "None".into());
            Some(ClusterCutControl {
                axis,
                label,
                height: if entry["height"].is_number() {
                    entry["height"].to_string()
                } else {
                    String::new()
                },
                items,
                partitioned,
                selected,
            })
        })
        .collect()
}

impl CurrentControls {
    fn from_spec(spec: &FigureSpec, active: usize, layouts: &Value) -> Self {
        let panel = spec
            .fields
            .get("panels")
            .and_then(Value::as_array)
            .and_then(|panels| panels.get(active))
            .and_then(Value::as_object);
        let size = spec.fields.get("size").and_then(Value::as_array);
        Self {
            active,
            panel_count: layouts.as_array().map_or(0, Vec::len),
            panel_names: layouts.as_array().map_or_else(Vec::new, |items| {
                items
                    .iter()
                    .enumerate()
                    .map(|(i, layout)| {
                        format!(
                            "{}: {}",
                            i,
                            layout
                                .get("panel_id")
                                .and_then(Value::as_str)
                                .unwrap_or("(anonymous)")
                        )
                    })
                    .collect()
            }),
            layout_actions: layout_actions(spec, active, layouts),
            shared_guides_action: {
                let mut bytes = b"{\"type\":\"SetSharedGuides\",\"guides\":".to_vec();
                serde_json::to_writer_pretty(
                    &mut bytes,
                    spec.fields.get("shared_guides").unwrap_or(&Value::Null),
                )
                .expect("a stored JSON value is serializable");
                bytes.push(b'}');
                String::from_utf8(bytes).expect("JSON serialization emits valid UTF-8")
            },
            facet_template_action: spec.fields
                .get("facet_template")
                .and_then(|recipe| recipe.get("template"))
                .map(|template| {
                    let mut bytes = b"{\"type\":\"SetFacetTemplate\",\"template\":".to_vec();
                    serde_json::to_writer_pretty(&mut bytes, template)
                        .expect("a stored JSON value is serializable");
                    bytes.extend_from_slice(b",\"reset_orders\":false}");
                    String::from_utf8(bytes).expect("JSON serialization emits valid UTF-8")
                }),
            layer_actions: panel
                .and_then(|panel| panel.get("layers"))
                .and_then(Value::as_array)
                .map_or_else(Vec::new, |layers| {
                    layers
                        .iter()
                        .enumerate()
                        .map(|(index, layer)| {
                            use std::io::Write;

                            // Serialize the actual stored layer by reference:
                            // no Rust FigureSpec defaults or shadow field map.
                            let mut bytes = Vec::new();
                            write!(
                                bytes,
                                "{{\"type\":\"ReplaceLayer\",\"panel\":{active},\"layer_index\":{index},\"layer\":"
                            )
                            .expect("an in-memory JSON prefix is writable");
                            serde_json::to_writer_pretty(&mut bytes, layer)
                                .expect("a stored JSON value is serializable");
                            bytes.push(b'}');
                            (
                                index,
                                String::from_utf8(bytes)
                                    .expect("JSON serialization emits valid UTF-8"),
                            )
                        })
                        .collect()
                }),
            cluster_cuts: layouts.get(active).map(cluster_cuts).unwrap_or_default(),
            axes: if layouts.get(active).is_some() {
                specialized::AxisControls::from_panel(panel)
            } else {
                Vec::new()
            },
            has_y2: panel.is_some_and(|panel| panel.get("y2").is_some_and(Value::is_object)),
            has_z: panel.is_some_and(|panel| panel.get("z").is_some_and(Value::is_object)),
            layout: layouts.get(active).unwrap_or(&Value::Null).to_string(),
            title: panel
                .and_then(|panel| panel.get("title"))
                .and_then(Value::as_str)
                .unwrap_or_default()
                .to_owned(),
            theme: spec
                .fields
                .get("theme")
                .and_then(Value::as_object)
                .and_then(|theme| theme.get("name"))
                .and_then(Value::as_str)
                .unwrap_or("paper")
                .to_owned(),
            projection: panel
                .and_then(|panel| panel.get("projection"))
                .and_then(Value::as_str)
                .unwrap_or("2d")
                .to_owned(),
            width: size
                .and_then(|size| size.first())
                .map_or_else(|| "3.5".to_owned(), Value::to_string),
            height: size
                .and_then(|size| size.get(1))
                .map_or_else(|| "2.625".to_owned(), Value::to_string),
        }
    }
}

impl From<Capabilities> for Controls {
    fn from(capabilities: Capabilities) -> Self {
        let mut layers: Vec<_> = capabilities
            .layers
            .into_iter()
            .map(|(name, fields)| LayerChoice {
                name,
                required: fields.required.join(", "),
                optional: fields.optional.join(", "),
            })
            .collect();
        if let Some(line) = layers.iter().position(|layer| layer.name == "line") {
            layers.swap(0, line);
        }
        Self {
            layers,
            themes: capabilities.themes,
            projections: capabilities.projections,
            coordinate_roles: capabilities
                .coordinate_pipeline
                .roles
                .into_iter()
                .map(|(kind, roles)| (kind, roles.join(", ")))
                .collect(),
            coordinate_names: capabilities.coordinate_pipeline.names.join(", "),
        }
    }
}

struct Session {
    initial: FigureSpec,
    spec: FigureSpec,
    history: Vec<FigureSpec>,
    future: Vec<FigureSpec>,
    png: Bytes,
    error: Option<String>,
    revision: u64,
    active_panel: usize,
    layouts: Value,
}

impl Session {
    fn new(bridge: &PythonBridge) -> Result<Self, Box<dyn std::error::Error>> {
        let spec = serde_json::from_str(model::DEFAULT_SPEC)?;
        let (png, layouts) = bridge.preview(&spec)?;
        Ok(Self {
            initial: spec.clone(),
            spec,
            history: Vec::new(),
            future: Vec::new(),
            png: png.into(),
            error: None,
            revision: 1,
            active_panel: 0,
            layouts,
        })
    }

    fn apply(&mut self, bridge: &PythonBridge, action: &Action) -> Result<(), String> {
        let next = bridge
            .apply(&self.spec, action)
            .map_err(|e| e.to_string())?;
        let (png, layouts) = bridge.preview(&next).map_err(|e| e.to_string())?;
        self.history.push(std::mem::replace(&mut self.spec, next));
        self.future.clear();
        self.png = png.into();
        self.set_layouts(layouts);
        self.error = None;
        self.revision += 1;
        Ok(())
    }

    fn open(&mut self, bridge: &PythonBridge, spec: FigureSpec) -> Result<(), String> {
        let (png, layouts) = bridge.preview(&spec).map_err(|e| e.to_string())?;
        self.history.push(std::mem::replace(&mut self.spec, spec));
        self.future.clear();
        self.png = png.into();
        self.set_layouts(layouts);
        self.error = None;
        self.revision += 1;
        Ok(())
    }

    fn undo(&mut self, bridge: &PythonBridge) -> Result<(), String> {
        let Some(previous) = self.history.last() else {
            return Ok(());
        };
        let (png, layouts) = bridge.preview(previous).map_err(|e| e.to_string())?;
        let previous = self.history.pop().expect("history was checked");
        self.future
            .push(std::mem::replace(&mut self.spec, previous));
        self.png = png.into();
        self.set_layouts(layouts);
        self.error = None;
        self.revision += 1;
        Ok(())
    }

    fn redo(&mut self, bridge: &PythonBridge) -> Result<(), String> {
        let Some(next) = self.future.last() else {
            return Ok(());
        };
        let (png, layouts) = bridge.preview(next).map_err(|e| e.to_string())?;
        let next = self.future.pop().expect("future was checked");
        self.history.push(std::mem::replace(&mut self.spec, next));
        self.png = png.into();
        self.set_layouts(layouts);
        self.error = None;
        self.revision += 1;
        Ok(())
    }

    fn reset(&mut self, bridge: &PythonBridge) -> Result<(), String> {
        let (png, layouts) = bridge.preview(&self.initial).map_err(|e| e.to_string())?;
        self.history
            .push(std::mem::replace(&mut self.spec, self.initial.clone()));
        self.future.clear();
        self.png = png.into();
        self.set_layouts(layouts);
        self.error = None;
        self.revision += 1;
        Ok(())
    }

    fn set_layouts(&mut self, layouts: Value) {
        if let Some(id) = self
            .layouts
            .get(self.active_panel)
            .and_then(|item| item.get("panel_id"))
            .and_then(Value::as_str)
            && let Some(index) = layouts.as_array().and_then(|items| {
                items
                    .iter()
                    .position(|item| item.get("panel_id").and_then(Value::as_str) == Some(id))
            })
        {
            self.active_panel = index;
        }
        self.active_panel = self.active_panel.min(
            layouts
                .as_array()
                .map_or(0, |items| items.len().saturating_sub(1)),
        );
        self.layouts = layouts;
    }
}

fn layout_actions(spec: &FigureSpec, active: usize, layouts: &Value) -> Vec<(String, String)> {
    let panels = spec
        .fields
        .get("panels")
        .and_then(Value::as_array)
        .map(Vec::as_slice)
        .unwrap_or(&[]);
    let effective = layouts.as_array().map(Vec::as_slice).unwrap_or(&[]);
    let ids: Vec<Value> = effective
        .iter()
        .map(|p| p.get("panel_id").cloned().unwrap_or(Value::Null))
        .collect();
    let mut actions = Vec::new();
    if let Some(layout) = spec.fields.get("panel_layout").filter(|v| !v.is_null()) {
        let placements: Map<String, Value> = panels
            .iter()
            .filter_map(|p| {
                Some((
                    p.get("panel_id")?.as_str()?.to_owned(),
                    p.get("placement")?.clone(),
                ))
            })
            .collect();
        actions.push((
            "Apply complete panel layout",
            json!({"type":"SetPanelLayout","layout":layout,"placements":placements}),
        ));
        if let Some(panel) = panels.get(active) {
            actions.push(("Move active panel", json!({"type":"SetPanelPlacement","panel_id":panel.get("panel_id"),"placement":panel.get("placement")})));
        }
    }
    let mosaic_ids: Vec<String> = effective
        .iter()
        .map(|panel| {
            panel
                .get("suggested_panel_id")
                .and_then(Value::as_str)
                .unwrap_or("")
                .to_owned()
        })
        .collect();
    actions.push((
        "Apply mosaic",
        json!({"type":"SetMosaic","rows":[mosaic_ids],"width_ratios":vec![1;effective.len()]}),
    ));
    actions.push((
        "Nest current grid",
        json!({"type":"NestLayout","rows":1,"cols":2,"width_ratios":[3,1]}),
    ));
    if let Some(id) = effective
        .get(active)
        .and_then(|p| p.get("panel_id"))
        .and_then(Value::as_str)
    {
        actions.push((
            "Add inset panel",
            json!({"type":"AddInset","parent":id,"bounds":[0.1,0.1,0.3,0.3]}),
        ));
        actions.push((
            "Rename active panel",
            json!({"type":"RenamePanel","panel_id":id,"new_id":id}),
        ));
        actions.push((
            "Reorder panels",
            json!({"type":"ReorderPanels","panel_ids":ids}),
        ));
        actions.push((
            "Remove active leaf panel",
            json!({"type":"RemovePanel","panel_id":id}),
        ));
    }
    actions
        .into_iter()
        .map(|(label, value)| {
            (
                label.to_owned(),
                serde_json::to_string_pretty(&value).expect("layout action is JSON"),
            )
        })
        .collect()
}

#[derive(Template)]
#[template(path = "page.html", escape = "html")]
struct PageTemplate<'a> {
    version: &'static str,
    spec_json: &'a str,
    error: &'a str,
    has_error: bool,
    revision: u64,
    controls: &'a Controls,
    current: &'a CurrentControls,
}

#[derive(Template)]
#[template(path = "fragment.html", escape = "html")]
struct FragmentTemplate<'a> {
    spec_json: &'a str,
    error: &'a str,
    has_error: bool,
    revision: u64,
    controls: &'a Controls,
    current: &'a CurrentControls,
}

#[derive(Deserialize)]
struct RawActionForm {
    json: String,
}

#[derive(Deserialize)]
struct ClusterCutForm {
    revision: u64,
    panel: usize,
    axis: String,
    #[serde(default)]
    height: String,
    #[serde(default)]
    anchor: String,
    #[serde(default)]
    clear: bool,
}

#[derive(Deserialize)]
struct PanelTextForm {
    text: String,
    #[serde(default)]
    panel: String,
}

#[derive(Deserialize)]
struct NamedForm {
    name: String,
}

#[derive(Deserialize)]
struct ProjectionForm {
    projection: String,
    #[serde(default)]
    panel: String,
}

#[derive(Deserialize)]
struct SizeForm {
    width: String,
    height: String,
}

#[derive(Deserialize)]
struct LayerForm {
    layer_type: String,
    fields: String,
    #[serde(default)]
    panel: String,
}

#[derive(Deserialize)]
struct OpenSpecForm {
    json: String,
}

type WebError = (StatusCode, String);

pub fn app(python: impl Into<std::ffi::OsString>) -> Result<Router, Box<dyn std::error::Error>> {
    let bridge = PythonBridge::new(python);
    let controls = Arc::new(Controls::from(bridge.capabilities()?));
    let state = AppState {
        session: Arc::new(Mutex::new(Session::new(&bridge)?)),
        bridge,
        controls,
    };
    Ok(Router::new()
        .route("/", get(index))
        .route("/fig.png", get(figure_png))
        .route("/fig.pdf", get(figure_pdf))
        .route("/fig.svg", get(figure_svg))
        .route("/spec.json", get(spec_json))
        .route("/static/htmx.min.js", get(htmx))
        .route("/static/editor.js", get(editor_js))
        .route("/control/panel", post(specialized::select_panel))
        .route("/control/axis", post(specialized::set_axis))
        .route("/control/secondary", post(specialized::secondary_axis))
        .route("/control/z", post(specialized::setup_z))
        .route("/control/move", post(specialized::move_handle))
        .route("/control/cluster-cut", post(set_cluster_cut))
        .route("/action", post(action_json))
        .route("/action/raw", post(action_raw))
        .route("/control/title", post(set_title))
        .route("/control/theme", post(set_theme))
        .route("/control/projection", post(set_projection))
        .route("/control/size", post(set_size))
        .route("/layers", post(add_layer))
        .route("/open", post(open_spec))
        .route("/undo", post(undo))
        .route("/redo", post(redo))
        .route("/reset", post(reset))
        .layer(DefaultBodyLimit::max(MAX_BODY_BYTES))
        .layer(middleware::from_fn(protect_local_boundary))
        .with_state(state))
}

pub async fn serve(
    addr: SocketAddr,
    python: impl Into<std::ffi::OsString>,
) -> Result<(), Box<dyn std::error::Error>> {
    ensure_loopback(addr)?;
    let app = app(python)?;
    let listener = tokio::net::TcpListener::bind(addr).await?;
    println!("mudplot Rust editor running at http://{addr}/ (Ctrl+C to stop)");
    axum::serve(listener, app).await?;
    Ok(())
}

async fn protect_local_boundary(request: Request, next: Next) -> Response {
    let mut response = if !has_loopback_host(request.headers()) {
        (StatusCode::FORBIDDEN, "non-loopback Host is not allowed").into_response()
    } else if request.method() == Method::POST && is_cross_origin(request.headers()) {
        (
            StatusCode::FORBIDDEN,
            "cross-origin mutations are not allowed",
        )
            .into_response()
    } else if request
        .headers()
        .get(header::CONTENT_LENGTH)
        .and_then(|value| value.to_str().ok())
        .and_then(|value| value.parse::<u64>().ok())
        .is_some_and(|length| length > MAX_BODY_BYTES as u64)
    {
        (
            StatusCode::PAYLOAD_TOO_LARGE,
            "request body exceeds the 16 MiB limit",
        )
            .into_response()
    } else {
        let (parts, body) = request.into_parts();
        let mut limited = Request::new(body);
        DefaultBodyLimit::max(MAX_BODY_BYTES).apply(&mut limited);
        match Bytes::from_request(limited, &()).await {
            Ok(bytes) => {
                next.run(Request::from_parts(parts, Body::from(bytes)))
                    .await
            }
            Err(rejection) => rejection.into_response(),
        }
    };
    let headers = response.headers_mut();
    headers.insert(
        header::CONTENT_SECURITY_POLICY,
        HeaderValue::from_static(
            "default-src 'self'; img-src 'self'; script-src 'self'; style-src 'unsafe-inline'; \
             object-src 'none'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'",
        ),
    );
    headers.insert(
        header::X_CONTENT_TYPE_OPTIONS,
        HeaderValue::from_static("nosniff"),
    );
    headers.insert(header::X_FRAME_OPTIONS, HeaderValue::from_static("DENY"));
    headers.insert(
        header::REFERRER_POLICY,
        HeaderValue::from_static("no-referrer"),
    );
    headers.insert(
        header::HeaderName::from_static("cross-origin-opener-policy"),
        HeaderValue::from_static("same-origin"),
    );
    headers.insert(
        header::HeaderName::from_static("cross-origin-resource-policy"),
        HeaderValue::from_static("same-origin"),
    );
    headers.insert(
        header::HeaderName::from_static("permissions-policy"),
        HeaderValue::from_static("camera=(), microphone=(), geolocation=()"),
    );
    headers.insert(header::CACHE_CONTROL, HeaderValue::from_static("no-store"));
    response
}

fn has_loopback_host(headers: &HeaderMap) -> bool {
    headers
        .get(header::HOST)
        .and_then(|value| value.to_str().ok())
        .is_some_and(is_loopback_host)
}

fn is_cross_origin(headers: &HeaderMap) -> bool {
    if headers
        .get("sec-fetch-site")
        .and_then(|value| value.to_str().ok())
        == Some("cross-site")
    {
        return true;
    }
    let Some(origin) = headers
        .get(header::ORIGIN)
        .and_then(|value| value.to_str().ok())
    else {
        return false;
    };
    let Some(host) = headers
        .get(header::HOST)
        .and_then(|value| value.to_str().ok())
    else {
        return true;
    };
    origin != format!("http://{host}")
}

fn is_loopback_host(host: &str) -> bool {
    let Ok(authority) = host.parse::<Authority>() else {
        return false;
    };
    if host.contains('@') {
        return false;
    }
    let authority_host = authority.host();
    let bare_host = authority_host
        .strip_prefix('[')
        .and_then(|value| value.strip_suffix(']'))
        .unwrap_or(authority_host);
    let loopback = bare_host.eq_ignore_ascii_case("localhost")
        || bare_host.parse::<IpAddr>().is_ok_and(|ip| ip.is_loopback());
    if !loopback {
        return false;
    }
    match authority.as_str().strip_prefix(authority_host) {
        Some("") => true,
        Some(port) => port
            .strip_prefix(':')
            .is_some_and(|value| value.parse::<u16>().is_ok()),
        None => false,
    }
}

async fn index(State(state): State<AppState>) -> Result<Html<String>, WebError> {
    let session = lock(&state);
    let spec_json = pretty_spec(&session)?;
    let current = CurrentControls::from_spec(&session.spec, session.active_panel, &session.layouts);
    PageTemplate {
        version: env!("CARGO_PKG_VERSION"),
        spec_json: &spec_json,
        error: session.error.as_deref().unwrap_or(""),
        has_error: session.error.is_some(),
        revision: session.revision,
        controls: &state.controls,
        current: &current,
    }
    .render()
    .map(Html)
    .map_err(internal)
}

#[derive(Deserialize)]
struct PreviewQuery {
    revision: Option<u64>,
}

async fn figure_png(State(state): State<AppState>, Query(query): Query<PreviewQuery>) -> Response {
    let session = lock(&state);
    if query
        .revision
        .is_some_and(|revision| revision != session.revision)
    {
        return (
            StatusCode::CONFLICT,
            "preview changed; reload the current figure",
        )
            .into_response();
    }
    (
        [
            (header::CONTENT_TYPE, "image/png"),
            (header::CACHE_CONTROL, "no-store"),
        ],
        session.png.clone(),
    )
        .into_response()
}

async fn figure_pdf(State(state): State<AppState>) -> Result<Response, WebError> {
    export_figure(&state, "pdf")
}

async fn figure_svg(State(state): State<AppState>) -> Result<Response, WebError> {
    export_figure(&state, "svg")
}

fn export_figure(state: &AppState, format: &'static str) -> Result<Response, WebError> {
    let spec = lock(state).spec.clone();
    let data = state
        .bridge
        .render_format(&spec, format)
        .map_err(internal)?;
    let (content_type, disposition) = match format {
        "pdf" => ("application/pdf", "attachment; filename=figure.pdf"),
        "svg" => ("image/svg+xml", "attachment; filename=figure.svg"),
        _ => unreachable!("route selects a supported export format"),
    };
    Ok((
        [
            (header::CONTENT_TYPE, content_type),
            (header::CONTENT_DISPOSITION, disposition),
            (header::CACHE_CONTROL, "no-store"),
        ],
        Bytes::from(data),
    )
        .into_response())
}

async fn spec_json(State(state): State<AppState>) -> impl IntoResponse {
    (
        [(header::CACHE_CONTROL, "no-store")],
        Json(lock(&state).spec.clone()),
    )
}

async fn htmx() -> impl IntoResponse {
    (
        [(
            header::CONTENT_TYPE,
            "application/javascript; charset=utf-8",
        )],
        HTMX,
    )
}

async fn editor_js() -> impl IntoResponse {
    (
        [(
            header::CONTENT_TYPE,
            "application/javascript; charset=utf-8",
        )],
        EDITOR_JS,
    )
}

async fn action_json(State(state): State<AppState>, headers: HeaderMap, body: Bytes) -> Response {
    let content_type = headers
        .get(header::CONTENT_TYPE)
        .and_then(|value| value.to_str().ok())
        .and_then(|value| value.split(';').next())
        .unwrap_or("")
        .trim();
    if !content_type.eq_ignore_ascii_case("application/json")
        && !content_type.to_ascii_lowercase().ends_with("+json")
    {
        return (
            StatusCode::UNSUPPORTED_MEDIA_TYPE,
            Json(json!({ "error": "Content-Type must be application/json" })),
        )
            .into_response();
    }
    let action = match std::str::from_utf8(&body)
        .map_err(|e| e.to_string())
        .and_then(|text| model::from_json_strict(text).map_err(|e| e.to_string()))
    {
        Ok(action) => action,
        Err(message) => {
            return (
                StatusCode::UNPROCESSABLE_ENTITY,
                Json(json!({ "error": format!("invalid action JSON: {message}") })),
            )
                .into_response();
        }
    };
    let mut session = lock(&state);
    match session.apply(&state.bridge, &action) {
        Ok(()) => Json(session.spec.clone()).into_response(),
        Err(message) => {
            session.error = Some(message.clone());
            (StatusCode::BAD_REQUEST, Json(json!({ "error": message }))).into_response()
        }
    }
}

async fn action_raw(
    State(state): State<AppState>,
    Form(form): Form<RawActionForm>,
) -> Result<Response, WebError> {
    let mut session = lock(&state);
    let result = model::from_json_strict::<Action>(&form.json)
        .map_err(|e| format!("invalid action JSON: {e}"))
        .and_then(|action| session.apply(&state.bridge, &action));
    if let Err(message) = result {
        session.error = Some(message);
    }
    fragment(&session, &state.controls)
}

async fn set_title(
    State(state): State<AppState>,
    Form(form): Form<PanelTextForm>,
) -> Result<Response, WebError> {
    let mut session = lock(&state);
    let result = (|| {
        let panel = parse_panel(&form.panel)?;
        let index = usize::try_from(panel).map_err(|_| "panel does not exist")?;
        let current = session
            .spec
            .fields
            .get("panels")
            .and_then(|panels| panels.get(index));
        let citation = current
            .and_then(|p| p.get("title_citation"))
            .cloned()
            .unwrap_or(Value::Null);
        let href = current
            .and_then(|p| p.get("title_href"))
            .cloned()
            .unwrap_or(Value::Null);
        session.apply(
            &state.bridge,
            &action(
                "SetTitle",
                [
                    ("text", Value::from(form.text)),
                    ("panel", Value::from(panel)),
                    ("citation", citation),
                    ("href", href),
                ],
            ),
        )
    })();
    if let Err(message) = result {
        session.error = Some(message);
    }
    fragment(&session, &state.controls)
}

async fn set_theme(
    State(state): State<AppState>,
    Form(form): Form<NamedForm>,
) -> Result<Response, WebError> {
    apply_form(
        &state,
        Ok(action("SetTheme", [("name", Value::from(form.name))])),
    )
}

async fn set_projection(
    State(state): State<AppState>,
    Form(form): Form<ProjectionForm>,
) -> Result<Response, WebError> {
    apply_form(
        &state,
        parse_panel(&form.panel).map(|panel| {
            action(
                "SetProjection",
                [
                    ("projection", Value::from(form.projection)),
                    ("panel", Value::from(panel)),
                ],
            )
        }),
    )
}

async fn set_size(
    State(state): State<AppState>,
    Form(form): Form<SizeForm>,
) -> Result<Response, WebError> {
    let result = parse_number(&form.width, "width").and_then(|width| {
        parse_number(&form.height, "height").map(|height| {
            action(
                "SetSize",
                [
                    ("width", Value::from(width)),
                    ("height", Value::from(height)),
                ],
            )
        })
    });
    apply_form(&state, result)
}

async fn add_layer(
    State(state): State<AppState>,
    Form(form): Form<LayerForm>,
) -> Result<Response, WebError> {
    let result = (|| {
        if !state
            .controls
            .layers
            .iter()
            .any(|layer| layer.name == form.layer_type)
        {
            return Err(format!("unknown layer type {:?}", form.layer_type));
        }
        let Value::Object(mut layer) = model::from_json_strict::<Value>(&form.fields)
            .map_err(|e| format!("invalid layer JSON: {e}"))?
        else {
            return Err("layer fields must be a JSON object".into());
        };
        layer.insert("type".into(), Value::from(form.layer_type));
        Ok(action(
            "AddLayer",
            [
                ("layer", Value::Object(layer)),
                ("panel", Value::from(parse_panel(&form.panel)?)),
            ],
        ))
    })();
    apply_form(&state, result)
}

async fn set_cluster_cut(
    State(state): State<AppState>,
    Form(form): Form<ClusterCutForm>,
) -> Result<Response, WebError> {
    mutate(&state, |session, bridge| {
        if session.revision != form.revision || session.active_panel != form.panel {
            return Err("preview changed; use the current cluster cut controls".into());
        }
        let key = match form.axis.as_str() {
            "row" => "row_cut",
            "col" => "col_cut",
            _ => return Err("cut axis must be row or col".into()),
        };
        let mut layer = session
            .spec
            .fields
            .get("panels")
            .and_then(|panels| panels.get(form.panel))
            .and_then(|panel| panel.get("layers"))
            .and_then(Value::as_array)
            .filter(|layers| layers.len() == 1 && layers[0]["type"] == "clustermap")
            .and_then(|layers| layers[0].as_object())
            .cloned()
            .ok_or_else(|| "cut requires an existing clustermap".to_owned())?;
        let cluster = layer.entry("cluster".to_owned()).or_insert(Value::Null);
        if cluster.is_null() {
            *cluster = json!({});
        }
        let config = cluster.as_object_mut().ok_or("cluster must be an object")?;
        if form.clear {
            config.remove(key);
        } else {
            let height = parse_number(&form.height, "cut height")?;
            let mut cut = json!({"height": height});
            if !form.anchor.is_empty() {
                let anchor = form
                    .anchor
                    .parse::<u64>()
                    .map_err(|_| "cut anchor must be an original item index")?;
                cut["anchor"] = json!(anchor);
            }
            config.insert(key.into(), cut);
        }
        session.apply(
            bridge,
            &action(
                "ReplaceLayer",
                [
                    ("panel", json!(form.panel)),
                    ("layer_index", json!(0)),
                    ("layer", Value::Object(layer)),
                ],
            ),
        )
    })
}

async fn open_spec(
    State(state): State<AppState>,
    Form(form): Form<OpenSpecForm>,
) -> Result<Response, WebError> {
    let result = model::from_json_strict::<FigureSpec>(&form.json)
        .map_err(|e| format!("invalid FigureSpec JSON: {e}"));
    let mut session = lock(&state);
    if let Err(message) = result.and_then(|spec| session.open(&state.bridge, spec)) {
        session.error = Some(message);
    }
    fragment(&session, &state.controls)
}

async fn undo(State(state): State<AppState>) -> Result<Response, WebError> {
    mutate(&state, |session, bridge| session.undo(bridge))
}

async fn redo(State(state): State<AppState>) -> Result<Response, WebError> {
    mutate(&state, |session, bridge| session.redo(bridge))
}

async fn reset(State(state): State<AppState>) -> Result<Response, WebError> {
    mutate(&state, |session, bridge| session.reset(bridge))
}

fn apply_form(state: &AppState, result: Result<Action, String>) -> Result<Response, WebError> {
    let mut session = lock(state);
    if let Err(message) = result.and_then(|action| session.apply(&state.bridge, &action)) {
        session.error = Some(message);
    }
    fragment(&session, &state.controls)
}

fn action<const N: usize>(kind: &str, fields: [(&str, Value); N]) -> Action {
    Action {
        kind: kind.into(),
        fields: fields
            .into_iter()
            .map(|(name, value)| (name.into(), value))
            .collect::<Map<_, _>>(),
    }
}

fn parse_panel(value: &str) -> Result<u64, String> {
    if value.is_empty() {
        return Ok(0);
    }
    value
        .parse()
        .map_err(|_| "panel must be a nonnegative integer".into())
}

fn parse_number(value: &str, name: &str) -> Result<f64, String> {
    value
        .parse()
        .ok()
        .filter(|number: &f64| number.is_finite())
        .ok_or_else(|| format!("{name} must be a finite number"))
}

fn mutate(
    state: &AppState,
    operation: impl FnOnce(&mut Session, &PythonBridge) -> Result<(), String>,
) -> Result<Response, WebError> {
    let mut session = lock(state);
    if let Err(message) = operation(&mut session, &state.bridge) {
        session.error = Some(message);
    }
    fragment(&session, &state.controls)
}

fn fragment(session: &Session, controls: &Controls) -> Result<Response, WebError> {
    let spec_json = pretty_spec(session)?;
    let current = CurrentControls::from_spec(&session.spec, session.active_panel, &session.layouts);
    let html = FragmentTemplate {
        spec_json: &spec_json,
        error: session.error.as_deref().unwrap_or(""),
        has_error: session.error.is_some(),
        revision: session.revision,
        controls,
        current: &current,
    }
    .render()
    .map_err(internal)?;
    let mut response = Html(html).into_response();
    response.headers_mut().insert(
        "X-Mudplot-View-Generation",
        HeaderValue::from_str(&session.revision.to_string()).map_err(internal)?,
    );
    Ok(response)
}

fn pretty_spec(session: &Session) -> Result<String, WebError> {
    serde_json::to_string_pretty(&session.spec).map_err(internal)
}

fn lock(state: &AppState) -> MutexGuard<'_, Session> {
    state
        .session
        .lock()
        .unwrap_or_else(std::sync::PoisonError::into_inner)
}

fn internal(error: impl std::fmt::Display) -> WebError {
    (StatusCode::INTERNAL_SERVER_ERROR, error.to_string())
}

fn ensure_loopback(addr: SocketAddr) -> Result<(), String> {
    if addr.ip().is_loopback() {
        Ok(())
    } else {
        Err("phase-1 editor only accepts a loopback bind address".into())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn editor_rejects_non_loopback_bind_addresses() {
        for address in ["127.0.0.1:8766", "[::1]:8766"] {
            assert!(ensure_loopback(address.parse().unwrap()).is_ok());
        }
        for address in ["0.0.0.0:8766", "[::]:8766", "[2001:db8::1]:8766"] {
            assert!(ensure_loopback(address.parse().unwrap()).is_err());
        }
    }

    #[test]
    fn local_http_boundary_rejects_cross_origin_and_dns_rebinding() {
        let mut headers = HeaderMap::new();
        headers.insert(header::HOST, "127.0.0.1:8766".parse().unwrap());
        assert!(has_loopback_host(&headers));
        assert!(!is_cross_origin(&headers));

        headers.insert(header::ORIGIN, "https://attacker.example".parse().unwrap());
        assert!(is_cross_origin(&headers));
        headers.insert(header::ORIGIN, "http://127.0.0.1:8766".parse().unwrap());
        assert!(!is_cross_origin(&headers));

        headers.insert(header::HOST, "attacker.example".parse().unwrap());
        assert!(!has_loopback_host(&headers));
        for host in ["[::1]:8766", "localhost", "127.0.0.1:0"] {
            headers.insert(header::HOST, host.parse().unwrap());
            assert!(has_loopback_host(&headers), "{host}");
        }
        for host in [
            "user@127.0.0.1:8766",
            "127.0.0.1:999999",
            "127.0.0.1:",
            "[::2]:8766",
        ] {
            headers.insert(header::HOST, host.parse().unwrap());
            assert!(!has_loopback_host(&headers), "{host}");
        }
    }

    #[test]
    fn every_failed_bridge_operation_preserves_state_history_future_and_cache() {
        fn snapshot(session: &Session) -> Value {
            json!({"initial": session.initial, "spec": session.spec,
                "history": session.history, "future": session.future,
                "active_panel": session.active_panel, "layouts": session.layouts,
                "png": session.png.as_ref(), "error": session.error, "revision": session.revision})
        }
        let directory = tempfile::tempdir().unwrap();
        let bridge = PythonBridge::new(directory.path().join("missing-python"));
        let original: FigureSpec = serde_json::from_str(model::DEFAULT_SPEC).unwrap();
        let mut changed = original.clone();
        changed
            .fields
            .insert("suptitle".into(), json!("prospective"));
        let mut session = Session {
            initial: original.clone(),
            spec: changed.clone(),
            history: vec![original.clone()],
            future: vec![changed.clone()],
            png: vec![1, 2, 3].into(),
            error: Some("prior error".into()),
            revision: 17,
            active_panel: 0,
            layouts: json!([]),
        };
        let before = snapshot(&session);
        let action: Action = serde_json::from_str(r#"{"type":"SetTitle","text":"new"}"#).unwrap();
        assert!(session.apply(&bridge, &action).is_err());
        assert_eq!(snapshot(&session), before);
        assert!(session.open(&bridge, original).is_err());
        assert_eq!(snapshot(&session), before);
        assert!(session.undo(&bridge).is_err());
        assert_eq!(snapshot(&session), before);
        assert!(session.redo(&bridge).is_err());
        assert_eq!(snapshot(&session), before);
        assert!(session.reset(&bridge).is_err());
        assert_eq!(snapshot(&session), before);
    }

    #[test]
    fn visual_form_numbers_fail_before_action_dispatch() {
        assert_eq!(parse_panel("").unwrap(), 0);
        assert!(parse_panel("-1").is_err());
        assert!(parse_panel("1.5").is_err());
        assert!(parse_number("NaN", "width").is_err());
        assert!(parse_number("infinite", "height").is_err());
    }
}
