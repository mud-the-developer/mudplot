mod model;
mod python;

use std::net::SocketAddr;
use std::sync::{Arc, Mutex, MutexGuard};

use askama::Template;
use axum::body::Bytes;
use axum::extract::{DefaultBodyLimit, Form, State};
use axum::http::{StatusCode, header};
use axum::response::{Html, IntoResponse, Response};
use axum::routing::{get, post};
use axum::{Json, Router};
use serde::Deserialize;
use serde_json::json;

pub use model::{Action, FigureSpec};
pub use python::PythonBridge;

const HTMX: &[u8] = include_bytes!("../../dashboard/static/htmx.min.js");

#[derive(Clone)]
struct AppState {
    // ponytail: one global session plus synchronous bridge is enough locally;
    // use cookie-keyed sessions + spawn_blocking if concurrent users matter.
    session: Arc<Mutex<Session>>,
    bridge: PythonBridge,
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
    spec_json: &'a str,
    error: &'a str,
    has_error: bool,
    revision: u64,
}

#[derive(Template)]
#[template(path = "fragment.html", escape = "html")]
struct FragmentTemplate<'a> {
    spec_json: &'a str,
    error: &'a str,
    has_error: bool,
    revision: u64,
}

#[derive(Deserialize)]
struct RawActionForm {
    json: String,
}

type WebError = (StatusCode, String);

pub fn app(python: impl Into<std::ffi::OsString>) -> Result<Router, Box<dyn std::error::Error>> {
    let bridge = PythonBridge::new(python);
    let state = AppState {
        session: Arc::new(Mutex::new(Session::new(&bridge)?)),
        bridge,
    };
    Ok(Router::new()
        .route("/", get(index))
        .route("/fig.png", get(figure_png))
        .route("/spec.json", get(spec_json))
        .route("/static/htmx.min.js", get(htmx))
        .route("/action", post(action_json))
        .route("/action/raw", post(action_raw))
        .route("/undo", post(undo))
        .route("/redo", post(redo))
        .route("/reset", post(reset))
        .layer(DefaultBodyLimit::max(1024 * 1024))
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

async fn index(State(state): State<AppState>) -> Result<Html<String>, WebError> {
    let session = lock(&state);
    let spec_json = pretty_spec(&session)?;
    PageTemplate {
        spec_json: &spec_json,
        error: session.error.as_deref().unwrap_or(""),
        has_error: session.error.is_some(),
        revision: session.revision,
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

async fn spec_json(State(state): State<AppState>) -> Json<FigureSpec> {
    Json(lock(&state).spec.clone())
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

async fn action_json(State(state): State<AppState>, Json(action): Json<Action>) -> Response {
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
    let result = serde_json::from_str::<Action>(&form.json)
        .map_err(|e| format!("invalid action JSON: {e}"))
        .and_then(|action| session.apply(&state.bridge, &action));
    if let Err(message) = result {
        session.error = Some(message);
    }
    fragment(&session).map(Html)
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

fn mutate(
    state: &AppState,
    operation: impl FnOnce(&mut Session, &PythonBridge) -> Result<(), String>,
) -> Result<Html<String>, WebError> {
    let mut session = lock(state);
    if let Err(message) = operation(&mut session, &state.bridge) {
        session.error = Some(message);
    }
    fragment(&session).map(Html)
}

fn fragment(session: &Session) -> Result<String, WebError> {
    let spec_json = pretty_spec(session)?;
    FragmentTemplate {
        spec_json: &spec_json,
        error: session.error.as_deref().unwrap_or(""),
        has_error: session.error.is_some(),
        revision: session.revision,
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
}
