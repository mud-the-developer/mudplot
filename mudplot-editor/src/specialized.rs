use super::*;

pub(super) struct AxisControls {
    pub name: &'static str,
    pub label: String,
    pub scale: String,
    pub allow_new_scales: bool,
    pub lo: String,
    pub hi: String,
}

impl AxisControls {
    pub(super) fn from_panel(panel: Option<&Map<String, Value>>) -> Vec<Self> {
        ["x", "y", "y2", "z"]
            .into_iter()
            .filter_map(|name| {
                let axis = panel
                    .and_then(|panel| panel.get(name))
                    .and_then(Value::as_object);
                if matches!(name, "y2" | "z") && axis.is_none() {
                    return None;
                }
                let limits = axis.and_then(|a| a.get("limits")).and_then(Value::as_array);
                Some(Self {
                    name,
                    allow_new_scales: name != "z"
                        && panel
                            .and_then(|p| p.get("projection"))
                            .and_then(Value::as_str)
                            .unwrap_or("2d")
                            == "2d",
                    label: axis
                        .and_then(|a| a.get("label"))
                        .and_then(Value::as_str)
                        .unwrap_or("")
                        .to_owned(),
                    scale: axis
                        .and_then(|a| a.get("scale"))
                        .and_then(Value::as_str)
                        .unwrap_or("linear")
                        .to_owned(),
                    lo: limits
                        .and_then(|v| v.first())
                        .map(Value::to_string)
                        .unwrap_or_default(),
                    hi: limits
                        .and_then(|v| v.get(1))
                        .map(Value::to_string)
                        .unwrap_or_default(),
                })
            })
            .collect()
    }
}

#[derive(Deserialize)]
pub(super) struct PanelForm {
    panel: usize,
}

pub(super) async fn select_panel(
    State(state): State<AppState>,
    Form(form): Form<PanelForm>,
) -> Result<Response, WebError> {
    let mut session = lock(&state);
    if session.layouts.get(form.panel).is_none() {
        session.error = Some("panel does not exist".into());
    } else {
        session.active_panel = form.panel;
        session.error = None;
        // Selection invalidates old handles without rendering or adding history.
        session.revision += 1;
    }
    fragment(&session, &state.controls)
}

#[derive(Deserialize)]
pub(super) struct AxisForm {
    panel: usize,
    axis: String,
    operation: String,
    #[serde(default)]
    text: String,
    #[serde(default)]
    scale: String,
    #[serde(default)]
    lo: String,
    #[serde(default)]
    hi: String,
}

pub(super) async fn set_axis(
    State(state): State<AppState>,
    Form(form): Form<AxisForm>,
) -> Result<Response, WebError> {
    let mut session = lock(&state);
    let result = (|| {
        if !["x", "y", "y2", "z"].contains(&form.axis.as_str()) {
            return Err("axis must be x, y, y2 or z".into());
        }
        session
            .layouts
            .get(form.panel)
            .ok_or("panel does not exist")?;
        let panel = session
            .spec
            .fields
            .get("panels")
            .and_then(|v| v.get(form.panel));
        if matches!(form.axis.as_str(), "y2" | "z")
            && !panel
                .and_then(|panel| panel.get(&form.axis))
                .is_some_and(Value::is_object)
        {
            return Err("enable the axis before editing it".into());
        }
        let mut fields = Map::from_iter([
            ("panel".into(), Value::from(form.panel)),
            ("axis".into(), Value::from(form.axis)),
        ]);
        let kind = match form.operation.as_str() {
            "label" => {
                fields.insert("text".into(), Value::from(form.text));
                "SetAxisLabel"
            }
            "scale" => {
                if !["linear", "log", "symlog", "asinh", "logit"].contains(&form.scale.as_str()) {
                    return Err("unknown scale".into());
                }
                fields.insert("scale".into(), Value::from(form.scale));
                "SetScale"
            }
            "limits" => {
                let (lo, hi) = if form.lo.is_empty() && form.hi.is_empty() {
                    (Value::Null, Value::Null)
                } else {
                    (
                        Value::from(parse_number(&form.lo, "lower limit")?),
                        Value::from(parse_number(&form.hi, "upper limit")?),
                    )
                };
                fields.insert("lo".into(), lo);
                fields.insert("hi".into(), hi);
                "SetLimits"
            }
            _ => return Err("unknown axis operation".into()),
        };
        // Granular actions retain temporal clocks, sharing and later axis options.
        session.apply(
            &state.bridge,
            &Action {
                kind: kind.into(),
                fields,
            },
        )
    })();
    if let Err(message) = result {
        session.error = Some(message);
    }
    fragment(&session, &state.controls)
}

#[derive(Deserialize)]
pub(super) struct SecondaryForm {
    panel: usize,
    operation: String,
}

pub(super) async fn secondary_axis(
    State(state): State<AppState>,
    Form(form): Form<SecondaryForm>,
) -> Result<Response, WebError> {
    let mut session = lock(&state);
    let result = (|| {
        session
            .layouts
            .get(form.panel)
            .ok_or("panel does not exist")?;
        let panel = session
            .spec
            .fields
            .get("panels")
            .and_then(|v| v.get(form.panel));
        if panel
            .and_then(|panel| panel.get("projection"))
            .and_then(Value::as_str)
            .unwrap_or("2d")
            != "2d"
        {
            return Err("secondary y requires a 2d panel".into());
        }
        let label = match form.operation.as_str() {
            "enable"
                if !panel
                    .and_then(|panel| panel.get("y2"))
                    .is_some_and(Value::is_object) =>
            {
                Value::from("")
            }
            "remove" => Value::Null,
            _ => return Err("secondary axis is already enabled or operation is invalid".into()),
        };
        session.apply(
            &state.bridge,
            &action(
                "SetSecondaryAxis",
                [("label", label), ("panel", Value::from(form.panel))],
            ),
        )
    })();
    if let Err(message) = result {
        session.error = Some(message);
    }
    fragment(&session, &state.controls)
}

pub(super) async fn setup_z(
    State(state): State<AppState>,
    Form(form): Form<SecondaryForm>,
) -> Result<Response, WebError> {
    let mut session = lock(&state);
    let result = (|| {
        let panel = session
            .spec
            .fields
            .get("panels")
            .and_then(|v| v.get(form.panel))
            .ok_or("panel does not exist")?;
        if panel.get("projection").and_then(Value::as_str) != Some("3d")
            || panel.get("z").is_some_and(Value::is_object)
            || form.operation != "enable"
        {
            return Err("z setup requires a 3d panel without an existing z axis".into());
        }
        session.apply(
            &state.bridge,
            &action("SetZAxis", [("panel", Value::from(form.panel))]),
        )
    })();
    if let Err(message) = result {
        session.error = Some(message);
    }
    fragment(&session, &state.controls)
}

#[derive(Deserialize)]
pub(super) struct MoveForm {
    panel: usize,
    revision: u64,
    kind: String,
    #[serde(default)]
    layer_index: usize,
    x: String,
    y: String,
}

pub(super) async fn move_handle(
    State(state): State<AppState>,
    Form(form): Form<MoveForm>,
) -> Result<Response, WebError> {
    let mut session = lock(&state);
    let result = (|| {
        if form.revision != session.revision || form.panel != session.active_panel {
            return Err("preview changed; use the current loaded handle".into());
        }
        let layout = session
            .layouts
            .get(form.panel)
            .ok_or("panel does not exist")?;
        let handles = layout
            .get("handles")
            .and_then(Value::as_array)
            .ok_or("no renderer handles")?;
        if !handles.iter().any(|handle| {
            handle.get("kind").and_then(Value::as_str) == Some(&form.kind)
                && (form.kind != "layer-at"
                    || handle.get("layer_index").and_then(Value::as_u64)
                        == Some(form.layer_index as u64))
        }) {
            return Err("handle is unavailable for this projection or artist".into());
        }
        let x = parse_number(&form.x, "x")?;
        let y = parse_number(&form.y, "y")?;
        let point = json!([x, y]);
        let action = match form.kind.as_str() {
            "title" => action(
                "SetTitlePosition",
                [("position", point), ("panel", Value::from(form.panel))],
            ),
            "layer-at" => action(
                "SetLayerAt",
                [
                    ("at", point),
                    ("panel", Value::from(form.panel)),
                    ("layer_index", Value::from(form.layer_index)),
                ],
            ),
            "legend" => {
                let legend = session
                    .spec
                    .fields
                    .get("panels")
                    .and_then(|v| v.get(form.panel))
                    .and_then(|p| p.get("legend"));
                action(
                    "SetLegend",
                    [
                        ("panel", Value::from(form.panel)),
                        ("bbox_to_anchor", point),
                        (
                            "show",
                            legend
                                .and_then(|l| l.get("show"))
                                .cloned()
                                .unwrap_or(Value::Bool(true)),
                        ),
                        (
                            "title",
                            legend
                                .and_then(|l| l.get("title"))
                                .cloned()
                                .unwrap_or(Value::Null),
                        ),
                        (
                            "location",
                            legend
                                .and_then(|l| l.get("location"))
                                .cloned()
                                .unwrap_or_else(|| Value::from("best")),
                        ),
                        (
                            "frame",
                            legend
                                .and_then(|l| l.get("frame"))
                                .cloned()
                                .unwrap_or(Value::Bool(false)),
                        ),
                    ],
                )
            }
            _ => return Err("unknown handle".into()),
        };
        session.apply(&state.bridge, &action)
    })();
    if let Err(message) = result {
        session.error = Some(message);
    }
    fragment(&session, &state.controls)
}
