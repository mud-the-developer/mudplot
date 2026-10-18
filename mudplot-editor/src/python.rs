use std::ffi::OsString;
use std::fmt;
use std::fs;
use std::io::{Read, Seek};
use std::path::Path;
use std::process::{Child, Command, Stdio};
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
        let bytes = fs::read(output_path).map_err(error("read rendered figure"))?;
        if bytes.is_empty() {
            return Err(BridgeError("empty rendered figure".into()));
        }
        Ok(bytes)
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
        let mut command = Command::new(&self.executable);
        command.args(args).stdout(child_stdout).stderr(child_stderr);
        #[cfg(unix)]
        {
            use std::os::unix::process::CommandExt;
            command.process_group(0);
        }
        let mut child = command.spawn().map_err(error("start Python bridge"))?;
        let started = Instant::now();
        let status = loop {
            if started.elapsed() >= self.timeout {
                return Err(stop_with_error(
                    &mut child,
                    format!("Python bridge timed out after {:?}", self.timeout),
                ));
            }
            match child.try_wait() {
                Ok(Some(status)) => break status,
                Ok(None) => thread::sleep(Duration::from_millis(10)),
                Err(e) => {
                    return Err(stop_with_error(
                        &mut child,
                        format!("wait for Python bridge: {e}"),
                    ));
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
        const MAX_ERROR_BYTES: usize = 64 * 1024;
        let limit = if status.success() {
            u64::MAX
        } else {
            (MAX_ERROR_BYTES + 1) as u64
        };
        let mut bytes = Vec::new();
        output
            .take(limit)
            .read_to_end(&mut bytes)
            .map_err(error("read Python bridge output"))?;
        if status.success() {
            return Ok(bytes);
        }
        let truncated = bytes.len() > MAX_ERROR_BYTES;
        bytes.truncate(MAX_ERROR_BYTES);
        Err(BridgeError(format!(
            "Python bridge exited with {status}: {}{}",
            String::from_utf8_lossy(&bytes).trim(),
            if truncated { " [stderr truncated]" } else { "" }
        )))
    }
}

// shortcut: detached workers need OS jobs/subreapers if they become supported.
fn stop_with_error(child: &mut Child, mut reason: String) -> BridgeError {
    let tree_result = (|| -> std::io::Result<()> {
        let pid = child.id().to_string();
        #[cfg(windows)]
        let mut command = {
            let root = std::env::var_os("SystemRoot")
                .ok_or_else(|| std::io::Error::other("SystemRoot is missing"))?;
            let mut command = Command::new(Path::new(&root).join("System32/taskkill.exe"));
            command.args(["/PID", &pid, "/T", "/F"]);
            command
        };
        #[cfg(unix)]
        let mut command = {
            let mut command = Command::new("/bin/kill");
            command.args(["-KILL", "--", &format!("-{pid}")]);
            command
        };
        let mut cleanup = command
            .stdin(Stdio::null())
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn()?;
        let started = Instant::now();
        loop {
            match cleanup.try_wait() {
                Ok(Some(status)) if status.success() => return Ok(()),
                Ok(Some(status)) => {
                    return Err(std::io::Error::other(format!(
                        "cleanup exited with {status}"
                    )));
                }
                Ok(None) if started.elapsed() < Duration::from_secs(2) => {
                    thread::sleep(Duration::from_millis(10))
                }
                result => {
                    if cleanup.kill().is_ok() {
                        let _ = cleanup.wait();
                    }
                    return Err(match result {
                        Err(e) => e,
                        _ => std::io::Error::new(
                            std::io::ErrorKind::TimedOut,
                            "cleanup exceeded two seconds",
                        ),
                    });
                }
            }
        }
    })();
    // Keep the child handle until tree cleanup, so only this owned PID/group is targeted.
    let wait_result = match child.kill() {
        Ok(()) => child.wait().map(|_| ()),
        Err(e) => match child.try_wait() {
            Ok(Some(_)) => Ok(()),
            Ok(None) => Err(e),
            Err(e) => Err(e),
        },
    };
    if let Err(e) = tree_result.and(wait_result) {
        reason.push_str(&format!("; process-tree cleanup failed: {e}"));
    }
    BridgeError(reason)
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
    fn controlled_slow_child_times_out_and_next_child_can_succeed() {
        let executable = std::env::current_exe().unwrap();
        let bridge = PythonBridge {
            executable: executable.clone().into(),
            timeout: Duration::from_millis(100),
        };
        let started = Instant::now();
        let error = bridge
            .run([
                "--ignored",
                "--exact",
                "python::tests::bridge_slow_output_helper",
                "--nocapture",
            ])
            .expect_err("slow controlled child must time out");
        assert!(error.to_string().contains("timed out"));
        assert!(started.elapsed() < Duration::from_secs(4));
        let healthy = PythonBridge {
            executable: executable.into(),
            timeout: Duration::from_secs(5),
        };
        assert!(!healthy.run(["--help"]).unwrap().is_empty());
    }

    #[cfg(windows)]
    #[test]
    fn cleanup_failure_is_reported_without_blocking_next_child() {
        let dir = tempfile::tempdir().unwrap();
        let output = Command::new(std::env::current_exe().unwrap())
            .args([
                "--ignored",
                "--exact",
                "python::tests::bridge_cleanup_failure_helper",
                "--nocapture",
            ])
            .env("SystemRoot", dir.path().join("missing-system-root"))
            .output()
            .unwrap();
        assert!(
            output.status.success(),
            "{}",
            String::from_utf8_lossy(&output.stderr)
        );
    }

    #[cfg(windows)]
    #[test]
    #[ignore]
    fn bridge_cleanup_failure_helper() {
        let executable = std::env::current_exe().unwrap();
        let bridge = PythonBridge {
            executable: executable.clone().into(),
            timeout: Duration::from_millis(100),
        };
        let error = bridge
            .run([
                "--ignored",
                "--exact",
                "python::tests::bridge_slow_output_helper",
                "--nocapture",
            ])
            .unwrap_err()
            .to_string();
        assert!(error.contains("timed out") && error.contains("process-tree cleanup failed"));
        let healthy = PythonBridge {
            executable: executable.into(),
            timeout: Duration::from_secs(5),
        };
        assert!(!healthy.run(["--help"]).unwrap().is_empty());
    }

    #[test]
    fn timeout_stops_owned_descendant_and_bridge_recovers() {
        let dir = tempfile::tempdir().unwrap();
        let ready = dir.path().join("descendant.txt");
        let argument = format!("--skip={}", ready.display());
        let executable = std::env::current_exe().unwrap();
        let bridge = PythonBridge {
            executable: executable.clone().into(),
            timeout: Duration::from_secs(2),
        };
        let error = bridge
            .run([
                "--ignored",
                "--exact",
                "python::tests::bridge_parent_descendant_helper",
                "--nocapture",
                &argument,
            ])
            .expect_err("controlled parent must time out");
        assert!(error.to_string().contains("timed out"));
        assert!(!error.to_string().contains("cleanup failed"));
        assert!(
            ready.exists(),
            "controlled helper never spawned its descendant"
        );
        thread::sleep(Duration::from_secs(3));
        assert!(
            !ready.with_extension("done").exists(),
            "owned descendant survived timeout"
        );
        let healthy = PythonBridge {
            executable: executable.into(),
            timeout: Duration::from_secs(5),
        };
        assert!(!healthy.run(["--help"]).unwrap().is_empty());
    }

    #[test]
    #[ignore]
    fn bridge_parent_descendant_helper() {
        let argument = std::env::args().find(|s| s.starts_with("--skip=")).unwrap();
        let ready = argument.strip_prefix("--skip=").unwrap();
        let mut child = Command::new(std::env::current_exe().unwrap())
            .args([
                "--ignored",
                "--exact",
                "python::tests::bridge_descendant_output_helper",
                "--nocapture",
                &argument,
            ])
            .spawn()
            .unwrap();
        fs::write(ready, format!("{} {}", std::process::id(), child.id())).unwrap();
        thread::sleep(Duration::from_secs(10));
        child.wait().unwrap();
    }

    #[test]
    #[ignore]
    fn bridge_descendant_output_helper() {
        let argument = std::env::args().find(|s| s.starts_with("--skip=")).unwrap();
        let ready = Path::new(argument.strip_prefix("--skip=").unwrap());
        thread::sleep(Duration::from_secs(4));
        fs::write(ready.with_extension("done"), "descendant completed").unwrap();
    }

    #[test]
    #[ignore]
    fn bridge_slow_output_helper() {
        std::thread::sleep(Duration::from_secs(3));
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
    fn bridge_failure_stderr_is_separate_and_bounded() {
        let bridge = PythonBridge {
            executable: std::env::current_exe().unwrap().into(),
            timeout: Duration::from_secs(5),
        };
        let error = bridge
            .run([
                "--ignored",
                "--exact",
                "python::tests::bridge_failure_output_helper",
                "--nocapture",
            ])
            .expect_err("nonzero helper must fail")
            .to_string();
        assert!(error.contains("exited with"));
        assert!(!error.contains("stdout-only-marker"));
        assert!(
            error.len() < 70_000,
            "stderr must not become an enormous UI error"
        );
        assert!(error.contains("truncated"));
    }

    #[test]
    #[ignore]
    fn bridge_failure_output_helper() -> std::io::Result<()> {
        use std::io::Write;
        std::io::stdout().write_all(b"stdout-only-marker")?;
        std::io::stderr().write_all(&vec![b'e'; 1024 * 1024])?;
        std::process::exit(7);
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
