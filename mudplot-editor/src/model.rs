use std::collections::{BTreeMap, BTreeSet};
use std::fmt;

use serde::de::{self, DeserializeOwned, MapAccess, SeqAccess, Visitor};
use serde::{Deserialize, Deserializer, Serialize};
use serde_json::{Map, Value};

/// Versioned FigureSpec envelope.
///
/// Python remains the schema validator and reducer in phase 1. Flattening the
/// schema body preserves every field (including forward-compatible additions)
/// instead of maintaining a second, inevitably drifting copy of ~70 fields.
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct FigureSpec {
    #[serde(default = "default_spec_version")]
    pub version: String,
    #[serde(flatten)]
    pub fields: Map<String, Value>,
}

/// The capability subset needed to build visual controls.
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct Capabilities {
    pub layers: BTreeMap<String, LayerCapability>,
    pub themes: Vec<String>,
    pub projections: Vec<String>,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct LayerCapability {
    pub required: Vec<String>,
    pub optional: Vec<String>,
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

fn default_spec_version() -> String {
    let default: Value = serde_json::from_str(DEFAULT_SPEC).expect("embedded default spec is JSON");
    default["version"]
        .as_str()
        .expect("embedded spec has a version")
        .to_owned()
}

pub(crate) fn from_json_strict<T: DeserializeOwned>(text: &str) -> Result<T, serde_json::Error> {
    // ponytail: two bounded passes preserve arbitrary precision; use one custom
    // deserializer only if 16 MiB request parsing profiles hot.
    let mut deserializer = serde_json::Deserializer::from_str(text);
    StrictJson::deserialize(&mut deserializer)?;
    deserializer.end()?;
    reject_reserved_keys(text)?;
    serde_json::from_str(text)
}

fn reject_reserved_keys(mut text: &str) -> Result<(), serde_json::Error> {
    // serde fabricates this key for big numbers; inspect original string tokens instead.
    while let Some(start) = text.find('"') {
        let mut strings = serde_json::Deserializer::from_str(&text[start..]).into_iter::<String>();
        let Some(key) = strings.next() else { break };
        let key = key?;
        text = &text[start + strings.byte_offset()..];
        if key == "$serde_json::private::Number" && text.trim_start().starts_with(':') {
            return Err(de::Error::custom(
                "JSON object key $serde_json::private::Number is reserved",
            ));
        }
    }
    Ok(())
}

struct StrictJson;

impl<'de> Deserialize<'de> for StrictJson {
    fn deserialize<D: Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        deserializer.deserialize_any(StrictJsonVisitor)
    }
}

struct StrictJsonVisitor;

impl<'de> Visitor<'de> for StrictJsonVisitor {
    type Value = StrictJson;

    fn expecting(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("a JSON value without duplicate object keys")
    }

    fn visit_bool<E>(self, _: bool) -> Result<Self::Value, E> {
        Ok(StrictJson)
    }

    fn visit_i64<E>(self, _: i64) -> Result<Self::Value, E> {
        Ok(StrictJson)
    }

    fn visit_i128<E>(self, _: i128) -> Result<Self::Value, E> {
        Ok(StrictJson)
    }

    fn visit_u64<E>(self, _: u64) -> Result<Self::Value, E> {
        Ok(StrictJson)
    }

    fn visit_u128<E>(self, _: u128) -> Result<Self::Value, E> {
        Ok(StrictJson)
    }

    fn visit_f64<E>(self, _: f64) -> Result<Self::Value, E> {
        Ok(StrictJson)
    }

    fn visit_str<E>(self, _: &str) -> Result<Self::Value, E> {
        Ok(StrictJson)
    }

    fn visit_string<E>(self, _: String) -> Result<Self::Value, E> {
        Ok(StrictJson)
    }

    fn visit_none<E>(self) -> Result<Self::Value, E> {
        Ok(StrictJson)
    }

    fn visit_some<D: Deserializer<'de>>(self, deserializer: D) -> Result<Self::Value, D::Error> {
        StrictJson::deserialize(deserializer)
    }

    fn visit_unit<E>(self) -> Result<Self::Value, E> {
        Ok(StrictJson)
    }

    fn visit_seq<A: SeqAccess<'de>>(self, mut sequence: A) -> Result<Self::Value, A::Error> {
        while sequence.next_element::<StrictJson>()?.is_some() {}
        Ok(StrictJson)
    }

    fn visit_map<A: MapAccess<'de>>(self, mut map: A) -> Result<Self::Value, A::Error> {
        let mut keys = BTreeSet::new();
        while let Some(key) = map.next_key::<String>()? {
            if !keys.insert(key.clone()) {
                return Err(de::Error::custom(format!(
                    "duplicate JSON object key {key:?}"
                )));
            }
            map.next_value::<StrictJson>()?;
        }
        Ok(StrictJson)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn omitted_spec_version_uses_the_embedded_current_default() {
        let expected: FigureSpec = serde_json::from_str(DEFAULT_SPEC).unwrap();
        let actual: FigureSpec = from_json_strict(r#"{"suptitle":"omitted version"}"#).unwrap();
        assert_eq!(actual.version, expected.version);
        assert_eq!(actual.fields["suptitle"], "omitted version");
        assert!(from_json_strict::<FigureSpec>(r#"{"version":null}"#).is_err());
    }

    #[test]
    fn figure_spec_round_trip_preserves_schema_fields() {
        let spec: FigureSpec = serde_json::from_str(DEFAULT_SPEC).unwrap();
        let round_trip = serde_json::to_value(spec).unwrap();
        assert_eq!(round_trip["version"], "0.1");
        assert_eq!(round_trip["panels"][0]["layers"][0]["type"], "line");
    }

    #[test]
    fn full_field_fixture_preserves_types_values_and_array_order() {
        let fixture: Value = from_json_strict(include_str!(
            "../../tests/fixtures/review_full_spec_fields.json"
        ))
        .expect("shared full-field fixture");
        let figures = fixture["figures"].as_array().expect("fixture figures");
        assert_eq!(figures.len(), 3);
        let mut restored = Vec::new();
        for (index, original) in figures.iter().enumerate() {
            let text = serde_json::to_string(original).unwrap();
            let spec: FigureSpec = from_json_strict(&text).unwrap();
            let encoded = serde_json::to_string(&spec).unwrap();
            let actual: Value = from_json_strict(&encoded).unwrap();
            assert_eq!(&actual, original, "structural fixture {index}");
            restored.push(actual);
        }
        if let Ok(path) = std::env::var("MUDPLOT_CODEC_PROBE_OUT") {
            std::fs::write(path, serde_json::to_vec(&restored).unwrap())
                .expect("write explicitly requested test-only round-trip artifact");
        }
    }

    #[test]
    fn figure_spec_round_trip_preserves_arbitrary_precision_json_integers() {
        let integer = "1234567890123456789012345678901234567890";
        let json = format!(r#"{{"version":"0.1","future_id":{integer}}}"#);
        let spec: FigureSpec = from_json_strict(&json).unwrap();
        assert_eq!(spec.fields["future_id"].to_string(), integer);
        assert!(serde_json::to_string(&spec).unwrap().contains(integer));

        let reserved = r#"{"version":"0.1","future":{"$serde_json::private::Number":"literal"}}"#;
        assert!(from_json_strict::<FigureSpec>(reserved).is_err());
    }

    #[test]
    fn strict_json_rejects_reserved_number_objects_without_reinterpreting_them() {
        for input in [
            r#"{"$serde_json::private::Number":"1"}"#,
            r#"{"outer":{"$serde_json::private::Number":"1"}}"#,
            r#"{"outer":[{"$serde_json::private::Number":"1"}]}"#,
            r#"{"outer":[{"\u0024serde_json::private::Number":"1"}]}"#,
        ] {
            assert!(
                from_json_strict::<Value>(input).is_err(),
                "accepted {input}"
            );
        }
        for text in [
            r#"{"text":"$serde_json::private::Number: literal, not a key"}"#,
            r#"{"text":"{\"$serde_json::private::Number\":\"1\"}"}"#,
        ] {
            assert!(from_json_strict::<Value>(text).is_ok());
        }
    }

    #[test]
    fn strict_json_rejects_duplicate_keys_at_any_depth() {
        for input in [
            r#"{"x":1,"x":1}"#,
            r#"{"x":1,"x":2}"#,
            r#"{"outer":{"x":1,"x":1}}"#,
            r#"{"outer":{"x":1,"x":2}}"#,
            r#"{"outer":[{"x":1,"x":1}]}"#,
            r#"{"outer":[{"x":1,"x":2}]}"#,
        ] {
            let error = from_json_strict::<Value>(input).expect_err("duplicate key must fail");
            assert!(
                error
                    .to_string()
                    .contains("duplicate JSON object key \"x\"")
            );
        }
    }

    #[test]
    fn strict_json_preserves_signed_integer_boundaries_and_valid_unicode() {
        for integer in [
            "9007199254740991",
            "9007199254740992",
            "9007199254740993",
            "9223372036854775807",
            "9223372036854775808",
            "18446744073709551615",
            "18446744073709551616",
            "100000000000000000000000000000000000000000000000000000000000000000000000000000001",
        ] {
            for sign in ["", "-"] {
                let number = format!("{sign}{integer}");
                let input =
                    format!(r#"{{"version":"0.1","data":{{"columns":{{"unused":[{number}]}}}}}}"#);
                let spec: FigureSpec = from_json_strict(&input).unwrap();
                let output = serde_json::to_string(&spec).unwrap();
                let restored: Value = from_json_strict(&output).unwrap();
                assert_eq!(restored["data"]["columns"]["unused"][0].to_string(), number);
            }
        }
        let value: Value = from_json_strict(r#"{"text":"한글 Ω \ud83d\ude00"}"#).unwrap();
        assert_eq!(value["text"], "한글 Ω 😀");
        for invalid in [r#"{"text":"\ud800"}"#, r#"{"text":"\udfff"}"#] {
            assert!(from_json_strict::<Value>(invalid).is_err());
        }
    }

    #[test]
    fn generated_capabilities_cover_visual_controls() {
        let capabilities: Capabilities =
            serde_json::from_str(include_str!("../../schemas/capabilities.json")).unwrap();
        assert_eq!(capabilities.layers.len(), 37);
        assert_eq!(capabilities.layers["clustermap"].required, ["matrix"]);
        for field in ["cluster", "heatmap", "colorbar"] {
            assert!(
                capabilities.layers["clustermap"]
                    .optional
                    .contains(&field.into())
            );
        }
        assert_eq!(capabilities.layers["lineplot"].required, ["x", "y"]);
        assert!(
            capabilities.layers["lineplot"]
                .optional
                .contains(&"semantics".into())
        );
        assert!(
            capabilities.layers["scatter"]
                .optional
                .contains(&"semantics".into())
        );
        assert!(
            capabilities.layers["violin"]
                .optional
                .contains(&"weights".into())
        );
        assert_eq!(capabilities.projections, ["2d", "polar", "3d"]);
        assert!(capabilities.themes.contains(&"paper".into()));
        assert_eq!(capabilities.layers["line"].required, ["x", "y"]);
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
