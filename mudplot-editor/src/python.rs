use std::ffi::OsString;
use std::fmt;
use std::fs;
use std::io::{Read, Seek};
use std::path::Path;
use std::process::Command;
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
        let mut stdout = tempfile::tempfile().map_err(error("capture Python bridge stdout"))?;
        let mut stderr = tempfile::tempfile().map_err(error("capture Python bridge stderr"))?;
        let child_stdout = stdout
            .try_clone()
            .map_err(error("capture Python bridge stdout"))?;
        let child_stderr = stderr
            .try_clone()
            .map_err(error("capture Python bridge stderr"))?;
        let mut child = Command::new(&self.executable)
            .args(args)
            .stdout(child_stdout)
            .stderr(child_stderr)
            .spawn()
            .map_err(error("start Python bridge"))?;
        let started = Instant::now();
        let status = loop {
            if started.elapsed() >= self.timeout {
                let _ = child.kill();
                let _ = child.wait();
                return Err(BridgeError(format!(
                    "Python bridge timed out after {:?}",
                    self.timeout
                )));
            }
            match child.try_wait() {
                Ok(Some(status)) => break status,
                Ok(None) => thread::sleep(Duration::from_millis(10)),
                Err(e) => {
                    let _ = child.kill();
                    let _ = child.wait();
                    return Err(error("wait for Python bridge")(e));
                }
            }
        };
        let output = if status.success() {
            &mut stdout
        } else {
            &mut stderr
        };
        output
            .rewind()
            .map_err(error("read Python bridge output"))?;
        let mut bytes = Vec::new();
        output
            .read_to_end(&mut bytes)
            .map_err(error("read Python bridge output"))?;
        if status.success() {
            return Ok(bytes);
        }
        Err(BridgeError(format!(
            "Python bridge exited with {status}: {}",
            String::from_utf8_lossy(&bytes).trim()
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

    #[test]
    fn bridge_handles_output_larger_than_a_pipe() {
        let bridge = PythonBridge {
            executable: std::env::current_exe()
                .expect("current test executable")
                .into(),
            timeout: Duration::from_secs(2),
        };
        let output = bridge
            .run([
                "--ignored",
                "--exact",
                "python::tests::bridge_large_output_helper",
                "--nocapture",
            ])
            .expect("large output must not fill the child pipes");
        assert!(output.len() >= 1024 * 1024);
    }

    #[test]
    #[ignore]
    fn bridge_large_output_helper() -> std::io::Result<()> {
        use std::io::Write;

        let bytes = vec![b'x'; 1024 * 1024];
        std::io::stdout().write_all(&bytes)?;
        std::io::stderr().write_all(&bytes)?;
        Ok(())
    }
}
