mod model;
mod python;

use std::net::{IpAddr, SocketAddr};
use std::sync::{Arc, Mutex, MutexGuard};

use askama::Template;
use axum::body::Bytes;
use axum::extract::{DefaultBodyLimit, Form, Request, State};
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
}

impl CurrentControls {
    fn from_spec(spec: &FigureSpec) -> Self {
        let panel = spec
            .fields
            .get("panels")
            .and_then(Value::as_array)
            .and_then(|panels| panels.first())
            .and_then(Value::as_object);
        let size = spec.fields.get("size").and_then(Value::as_array);
        Self {
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
                .map_or_else(|| "5".to_owned(), Value::to_string),
            height: size
                .and_then(|size| size.get(1))
                .map_or_else(|| "3.5".to_owned(), Value::to_string),
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
        }
    }
}

struct Session {
    initial: FigureSpec,
    spec: FigureSpec,
    history: Vec<FigureSpec>,
    future: Vec<FigureSpec>,
    png: Vec<u8>,
    error: Option<String>,
    revision: u64,
}

impl Session {
    fn new(bridge: &PythonBridge) -> Result<Self, Box<dyn std::error::Error>> {
        let spec = serde_json::from_str(model::DEFAULT_SPEC)?;
        let png = bridge.render(&spec)?;
        Ok(Self {
            initial: spec.clone(),
            spec,
            history: Vec::new(),
            future: Vec::new(),
            png,
            error: None,
            revision: 1,
        })
    }

    fn apply(&mut self, bridge: &PythonBridge, action: &Action) -> Result<(), String> {
        let next = bridge
            .apply(&self.spec, action)
            .map_err(|e| e.to_string())?;
        let png = bridge.render(&next).map_err(|e| e.to_string())?;
        self.history.push(self.spec.clone());
        self.spec = next;
        self.future.clear();
        self.png = png;
        self.error = None;
        self.revision += 1;
        Ok(())
    }

    fn open(&mut self, bridge: &PythonBridge, spec: FigureSpec) -> Result<(), String> {
        let png = bridge.render(&spec).map_err(|e| e.to_string())?;
        self.history.push(self.spec.clone());
        self.spec = spec;
        self.future.clear();
        self.png = png;
        self.error = None;
        self.revision += 1;
        Ok(())
    }

    fn undo(&mut self, bridge: &PythonBridge) -> Result<(), String> {
        let Some(previous) = self.history.last().cloned() else {
            return Ok(());
        };
        let png = bridge.render(&previous).map_err(|e| e.to_string())?;
        self.history.pop();
        self.future
            .push(std::mem::replace(&mut self.spec, previous));
        self.png = png;
        self.error = None;
        self.revision += 1;
        Ok(())
    }

    fn redo(&mut self, bridge: &PythonBridge) -> Result<(), String> {
        let Some(next) = self.future.last().cloned() else {
            return Ok(());
        };
        let png = bridge.render(&next).map_err(|e| e.to_string())?;
        self.future.pop();
        self.history.push(std::mem::replace(&mut self.spec, next));
        self.png = png;
        self.error = None;
        self.revision += 1;
        Ok(())
    }

    fn reset(&mut self, bridge: &PythonBridge) -> Result<(), String> {
        let png = bridge.render(&self.initial).map_err(|e| e.to_string())?;
        self.history.push(self.spec.clone());
        self.spec = self.initial.clone();
        self.future.clear();
        self.png = png;
        self.error = None;
        self.revision += 1;
        Ok(())
    }
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
    if !has_loopback_host(request.headers()) {
        return (StatusCode::FORBIDDEN, "non-loopback Host is not allowed").into_response();
    }
    if request.method() == Method::POST && is_cross_origin(request.headers()) {
        return (
            StatusCode::FORBIDDEN,
            "cross-origin mutations are not allowed",
        )
            .into_response();
    }
    let mut response = next.run(request).await;
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
    let current = CurrentControls::from_spec(&session.spec);
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

async fn figure_png(State(state): State<AppState>) -> impl IntoResponse {
    let png = lock(&state).png.clone();
    (
        [
            (header::CONTENT_TYPE, "image/png"),
            (header::CACHE_CONTROL, "no-store"),
        ],
        Bytes::from(png),
    )
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
) -> Result<Html<String>, WebError> {
    let mut session = lock(&state);
    let result = model::from_json_strict::<Action>(&form.json)
        .map_err(|e| format!("invalid action JSON: {e}"))
        .and_then(|action| session.apply(&state.bridge, &action));
    if let Err(message) = result {
        session.error = Some(message);
    }
    fragment(&session, &state.controls).map(Html)
}

async fn set_title(
    State(state): State<AppState>,
    Form(form): Form<PanelTextForm>,
) -> Result<Html<String>, WebError> {
    apply_form(
        &state,
        parse_panel(&form.panel).map(|panel| {
            action(
                "SetTitle",
                [
                    ("text", Value::from(form.text)),
                    ("panel", Value::from(panel)),
                ],
            )
        }),
    )
}

async fn set_theme(
    State(state): State<AppState>,
    Form(form): Form<NamedForm>,
) -> Result<Html<String>, WebError> {
    apply_form(
        &state,
        Ok(action("SetTheme", [("name", Value::from(form.name))])),
    )
}

async fn set_projection(
    State(state): State<AppState>,
    Form(form): Form<ProjectionForm>,
) -> Result<Html<String>, WebError> {
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
) -> Result<Html<String>, WebError> {
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
) -> Result<Html<String>, WebError> {
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

async fn open_spec(
    State(state): State<AppState>,
    Form(form): Form<OpenSpecForm>,
) -> Result<Html<String>, WebError> {
    let result = model::from_json_strict::<FigureSpec>(&form.json)
        .map_err(|e| format!("invalid FigureSpec JSON: {e}"));
    let mut session = lock(&state);
    if let Err(message) = result.and_then(|spec| session.open(&state.bridge, spec)) {
        session.error = Some(message);
    }
    fragment(&session, &state.controls).map(Html)
}

async fn undo(State(state): State<AppState>) -> Result<Html<String>, WebError> {
    mutate(&state, |session, bridge| session.undo(bridge))
}

async fn redo(State(state): State<AppState>) -> Result<Html<String>, WebError> {
    mutate(&state, |session, bridge| session.redo(bridge))
}

async fn reset(State(state): State<AppState>) -> Result<Html<String>, WebError> {
    mutate(&state, |session, bridge| session.reset(bridge))
}

fn apply_form(state: &AppState, result: Result<Action, String>) -> Result<Html<String>, WebError> {
    let mut session = lock(state);
    if let Err(message) = result.and_then(|action| session.apply(&state.bridge, &action)) {
        session.error = Some(message);
    }
    fragment(&session, &state.controls).map(Html)
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
) -> Result<Html<String>, WebError> {
    let mut session = lock(state);
    if let Err(message) = operation(&mut session, &state.bridge) {
        session.error = Some(message);
    }
    fragment(&session, &state.controls).map(Html)
}

fn fragment(session: &Session, controls: &Controls) -> Result<String, WebError> {
    let spec_json = pretty_spec(session)?;
    let current = CurrentControls::from_spec(&session.spec);
    FragmentTemplate {
        spec_json: &spec_json,
        error: session.error.as_deref().unwrap_or(""),
        has_error: session.error.is_some(),
        revision: session.revision,
        controls,
        current: &current,
    }
    .render()
    .map_err(internal)
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
        assert!(ensure_loopback("127.0.0.1:8766".parse().unwrap()).is_ok());
        assert!(ensure_loopback("0.0.0.0:8766".parse().unwrap()).is_err());
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
    fn visual_form_numbers_fail_before_action_dispatch() {
        assert_eq!(parse_panel("").unwrap(), 0);
        assert!(parse_panel("-1").is_err());
        assert!(parse_panel("1.5").is_err());
        assert!(parse_number("NaN", "width").is_err());
        assert!(parse_number("infinite", "height").is_err());
    }
}
