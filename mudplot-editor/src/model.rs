use serde::{Deserialize, Serialize};
use serde_json::{Map, Value};

/// Versioned FigureSpec envelope.
///
/// Python remains the schema validator and reducer in phase 1. Flattening the
/// schema body preserves every field (including forward-compatible additions)
/// instead of maintaining a second, inevitably drifting copy of ~70 fields.
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct FigureSpec {
    pub version: String,
    #[serde(flatten)]
    pub fields: Map<String, Value>,
}

/// One action from the JSON vocabulary in `docs/REFERENCE.md`.
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct Action {
    #[serde(rename = "type")]
    pub kind: String,
    #[serde(flatten)]
    pub fields: Map<String, Value>,
}

pub const DEFAULT_SPEC: &str = include_str!("../default_spec.json");

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn figure_spec_round_trip_preserves_schema_fields() {
        let spec: FigureSpec = serde_json::from_str(DEFAULT_SPEC).unwrap();
        let round_trip = serde_json::to_value(spec).unwrap();
        assert_eq!(round_trip["version"], "0.1");
        assert_eq!(round_trip["panels"][0]["layers"][0]["type"], "line");
    }

    #[test]
    fn action_envelope_preserves_typed_kind_and_fields() {
        let action: Action =
            serde_json::from_str(r#"{"type":"SetTitle","text":"from Rust","panel":0}"#).unwrap();
        assert_eq!(action.kind, "SetTitle");
        assert_eq!(action.fields["text"], "from Rust");
        assert_eq!(serde_json::to_value(action).unwrap()["panel"], 0);
    }
}
