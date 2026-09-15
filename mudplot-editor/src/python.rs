use std::ffi::OsString;
use std::fmt;
use std::fs;
use std::path::Path;
use std::process::Command;

use crate::model::{Action, FigureSpec};

#[derive(Debug)]
pub struct BridgeError(String);

impl fmt::Display for BridgeError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(&self.0)
    }
}

impl std::error::Error for BridgeError {}

#[derive(Clone, Debug)]
pub struct PythonBridge {
    executable: OsString,
}

impl PythonBridge {
    pub fn new(executable: impl Into<OsString>) -> Self {
        Self {
            executable: executable.into(),
        }
    }

    pub fn apply(&self, spec: &FigureSpec, action: &Action) -> Result<FigureSpec, BridgeError> {
        let dir = tempfile::tempdir().map_err(error("create temporary directory"))?;
        let spec_path = dir.path().join("spec.json");
        let action_path = dir.path().join("action.json");
        let output_path = dir.path().join("next.json");
        write_json(&spec_path, spec)?;
        write_json(&action_path, action)?;

        self.run([
            "-m",
            "mudplot",
            "apply",
            path(&spec_path)?,
            path(&action_path)?,
            "-o",
            path(&output_path)?,
        ])?;
        let bytes = fs::read(&output_path).map_err(error("read reduced spec"))?;
        serde_json::from_slice(&bytes).map_err(|e| BridgeError(format!("decode reduced spec: {e}")))
    }

    pub fn render(&self, spec: &FigureSpec) -> Result<Vec<u8>, BridgeError> {
        let dir = tempfile::tempdir().map_err(error("create temporary directory"))?;
        let spec_path = dir.path().join("spec.json");
        let output_path = dir.path().join("figure.png");
        write_json(&spec_path, spec)?;

        self.run([
            "-m",
            "mudplot",
            "render",
            path(&spec_path)?,
            path(&output_path)?,
        ])?;
        fs::read(output_path).map_err(error("read rendered PNG"))
    }

    fn run<const N: usize>(&self, args: [&str; N]) -> Result<(), BridgeError> {
        let output = Command::new(&self.executable)
            .args(args)
            .output()
            .map_err(error("start Python bridge"))?;
        if output.status.success() {
            return Ok(());
        }
        let stderr = String::from_utf8_lossy(&output.stderr);
        Err(BridgeError(format!(
            "Python bridge exited with {}: {}",
            output.status,
            stderr.trim()
        )))
    }
}

fn write_json(path: &Path, value: &impl serde::Serialize) -> Result<(), BridgeError> {
    let bytes = serde_json::to_vec_pretty(value)
        .map_err(|e| BridgeError(format!("encode bridge JSON: {e}")))?;
    fs::write(path, bytes).map_err(error("write bridge JSON"))
}

fn path(path: &Path) -> Result<&str, BridgeError> {
    path.to_str()
        .ok_or_else(|| BridgeError("temporary path is not valid UTF-8".into()))
}

fn error(context: &'static str) -> impl FnOnce(std::io::Error) -> BridgeError {
    move |e| BridgeError(format!("{context}: {e}"))
}
