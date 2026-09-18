use std::ffi::OsString;
use std::fmt;
use std::fs;
use std::path::Path;
use std::process::{Command, Stdio};
use std::thread;
use std::time::{Duration, Instant};

use crate::model::{Action, Capabilities, FigureSpec};

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
    timeout: Duration,
}

impl PythonBridge {
    pub fn new(executable: impl Into<OsString>) -> Self {
        Self {
            executable: executable.into(),
            // ponytail: fixed local ceiling; make configurable if real renders exceed it.
            timeout: Duration::from_secs(120),
        }
    }

    pub fn capabilities(&self) -> Result<Capabilities, BridgeError> {
        let bytes = self.run(["-m", "mudplot", "capabilities"])?;
        serde_json::from_slice(&bytes).map_err(|e| BridgeError(format!("decode capabilities: {e}")))
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
        self.render_format(spec, "png")
    }

    pub fn render_format(&self, spec: &FigureSpec, format: &str) -> Result<Vec<u8>, BridgeError> {
        if !matches!(format, "png" | "pdf" | "svg") {
            return Err(BridgeError(format!("unsupported render format {format:?}")));
        }
        let dir = tempfile::tempdir().map_err(error("create temporary directory"))?;
        let spec_path = dir.path().join("spec.json");
        let output_path = dir.path().join(format!("figure.{format}"));
        write_json(&spec_path, spec)?;

        if format == "png" {
            self.run([
                "-m",
                "mudplot",
                "render",
                path(&spec_path)?,
                path(&output_path)?,
                "--preview",
            ])?;
        } else {
            self.run([
                "-m",
                "mudplot",
                "render",
                path(&spec_path)?,
                path(&output_path)?,
            ])?;
        }
        fs::read(output_path).map_err(error("read rendered figure"))
    }

    fn run<const N: usize>(&self, args: [&str; N]) -> Result<Vec<u8>, BridgeError> {
        let mut child = Command::new(&self.executable)
            .args(args)
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .map_err(error("start Python bridge"))?;
        let started = Instant::now();
        loop {
            if started.elapsed() >= self.timeout {
                let _ = child.kill();
                let _ = child.wait();
                return Err(BridgeError(format!(
                    "Python bridge timed out after {:?}",
                    self.timeout
                )));
            }
            if child
                .try_wait()
                .map_err(error("wait for Python bridge"))?
                .is_some()
            {
                break;
            }
            thread::sleep(Duration::from_millis(10));
        }
        let output = child
            .wait_with_output()
            .map_err(error("collect Python bridge output"))?;
        if output.status.success() {
            return Ok(output.stdout);
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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn bridge_processes_have_a_timeout() {
        let bridge = PythonBridge {
            executable: std::env::current_exe()
                .expect("current test executable")
                .into(),
            timeout: Duration::ZERO,
        };
        let error = bridge.run(["--help"]).expect_err("zero timeout must fail");
        assert!(error.to_string().contains("timed out"));
    }
}
