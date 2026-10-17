"""Exercise Rust interpreter selection using a separate Unicode-path venv.

Run from the dev checkout: uv run python scripts/check_python_bridge_paths.py.
Same-version render wheels may be downloaded into the temporary venv only;
the project environment/lock stay untouched.
"""

from __future__ import annotations

import http.client
import importlib.metadata
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "mudplot-editor/Cargo.toml"


def _probe(binary: Path, executable: Path, prefix: Path, root: Path, mode: str):
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    log = root / f"{mode}.jsonl"
    temporary = root / "임시 data & (bridge)"
    temporary.mkdir(exist_ok=True)
    env = {
        **os.environ,
        "PATH": str(executable.parent) + os.pathsep + os.environ.get("PATH", ""),
        "PYTHONUTF8": "1",
        "PYTHONIOENCODING": "utf-8",
        "PYTHONDONTWRITEBYTECODE": "1",
        "MPLBACKEND": "Agg",
        "MPLCONFIGDIR": str(root / "matplotlib"),
        "MUDPLOT_PATH_PROBE_LOG": str(log),
        "TEMP": str(temporary),
        "TMP": str(temporary),
        "TMPDIR": str(temporary),
    }
    for name in ("PYTHONPATH", "PYTHONHOME", "MUDPLOT_PYTHON"):
        env.pop(name, None)
    args = [str(binary), "--bind", f"127.0.0.1:{port}"]
    if mode == "environment":
        env["MUDPLOT_PYTHON"] = str(executable)
    elif mode == "flag":
        env["MUDPLOT_PYTHON"] = str(root / "missing interpreter.exe")
        args += ["--python", str(executable)]
    elif mode == "invalid-flag":
        env["MUDPLOT_PYTHON"] = str(executable)
        args += ["--python", str(root / "missing interpreter.exe")]
        result = subprocess.run(
            args, cwd=ROOT, env=env, capture_output=True, text=True, timeout=30
        )
        assert result.returncode != 0 and "start Python bridge" in result.stderr
        assert not log.exists(), (
            "invalid --python must not silently use the environment"
        )
        return {"mode": mode, "rejected_without_fallback": True}
    else:
        assert mode == "default"
    process = subprocess.Popen(
        args,
        cwd=ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        deadline = time.monotonic() + 45
        while True:
            if process.poll() is not None:
                raise RuntimeError(
                    f"{mode}: editor exited before readiness: "
                    f"{process.communicate()[1]}"
                )
            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
            try:
                connection.request("GET", "/spec.json")
                response = connection.getresponse()
                assert response.status == 200
                assert json.loads(response.read())["version"] == "0.1"
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise
                time.sleep(0.1)
            finally:
                connection.close()
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=30)
        try:
            connection.request(
                "POST",
                "/action",
                json.dumps({"type": "SetTitle", "text": mode}),
                {"Content-Type": "application/json"},
            )
            response = connection.getresponse()
            assert response.status == 200
            assert json.loads(response.read())["panels"][0]["title"] == mode
            connection.request("GET", "/fig.png")
            response = connection.getresponse()
            assert response.status == 200 and response.read().startswith(b"\x89PNG")
        finally:
            connection.close()
    finally:
        if process.poll() is None:
            process.terminate()
        process.communicate(timeout=10)
    try:
        records = [
            json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()
        ]
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RuntimeError(
            f"{mode}: missing or invalid interpreter provenance"
        ) from error
    expected = (
        executable.parent / ("python3.exe" if os.name == "nt" else "python3")
        if mode == "default"
        else executable
    )
    assert len(records) >= 4
    assert all(Path(record["executable"]).samefile(expected) for record in records)
    assert all(Path(record["prefix"]).samefile(prefix) for record in records)
    assert all(record["version"] == sys.version.split()[0] for record in records)
    commands = {
        arg
        for record in records
        for arg in record["argv"]
        if arg in ("capabilities", "apply", "render")
    }
    assert commands == {"capabilities", "apply", "render"}
    paths = [
        arg
        for record in records
        for arg in record["argv"]
        if arg.endswith((".json", ".png"))
    ]
    assert paths and all(str(temporary) in arg for arg in paths)
    return {
        "mode": mode,
        "child_count": len(records),
        "separate_prefix": True,
        "executable": str(expected.relative_to(root)),
        "commands": sorted(commands),
        "unicode_argument_paths": True,
        "version": records[0]["version"],
        "argv_samples": [
            [arg.replace(str(root), "<temp>") for arg in record["argv"]]
            for record in records
        ],
    }


def main() -> int:
    subprocess.run(
        ["cargo", "build", "--locked", "--manifest-path", str(MANIFEST)],
        cwd=ROOT,
        check=True,
    )
    try:
        metadata = json.loads(
            subprocess.check_output(
                [
                    "cargo",
                    "metadata",
                    "--no-deps",
                    "--format-version=1",
                    "--manifest-path",
                    str(MANIFEST),
                ],
                cwd=ROOT,
                text=True,
                encoding="utf-8",
            )
        )
    except (
        OSError,
        subprocess.CalledProcessError,
        UnicodeError,
        json.JSONDecodeError,
    ) as error:
        raise RuntimeError("could not read Cargo target metadata") from error
    binary = (
        Path(metadata["target_directory"])
        / "debug"
        / ("mudplot-editor.exe" if os.name == "nt" else "mudplot-editor")
    )
    with tempfile.TemporaryDirectory(prefix="mudplot-python-paths-") as directory:
        root = Path(directory)
        prefix = root / "한글 bridge & (space)"
        subprocess.run(
            ["uv", "venv", "--python", sys.executable, str(prefix)], check=True
        )
        executable = prefix / (
            "Scripts/python.exe" if os.name == "nt" else "bin/python"
        )
        subprocess.run(
            [
                "uv",
                "pip",
                "install",
                "--python",
                str(executable),
                f"numpy=={importlib.metadata.version('numpy')}",
                f"matplotlib=={importlib.metadata.version('matplotlib')}",
            ],
            check=True,
        )
        if os.name == "nt":
            shutil.copy2(executable, executable.with_name("python3.exe"))
        env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
        site = Path(
            subprocess.check_output(
                [
                    str(executable),
                    "-c",
                    "import sysconfig; print(sysconfig.get_path('purelib'))",
                ],
                env=env,
                text=True,
                encoding="utf-8",
            ).strip()
        )
        assert site.resolve().is_relative_to(prefix.resolve())
        assert not prefix.samefile(Path(sys.prefix))
        with (site / "_mudplot_interpreter_probe.py").open(
            "x", encoding="utf-8"
        ) as handle:
            handle.write(
                "import json,os,sys\n"
                "path=os.environ.get('MUDPLOT_PATH_PROBE_LOG')\n"
                "if path:\n"
                "    with open(path,'a',encoding='utf-8') as log:\n"
                "        record={'executable':sys.executable,'prefix':sys.prefix,"
                "'argv':sys.orig_argv,'version':sys.version.split()[0]}\n"
                "        log.write(json.dumps(record,ensure_ascii=False)+'\\n')\n"
            )
        with (site / "_mudplot_interpreter_probe.pth").open(
            "x", encoding="utf-8"
        ) as handle:
            handle.write("import _mudplot_interpreter_probe\n")
        shadow = root / "other customizer"
        shadow.mkdir()
        with (shadow / "sitecustomize.py").open("x", encoding="utf-8") as handle:
            handle.write("marker='other customizer preserved'\n")
        shadow_log = root / "shadow.jsonl"
        subprocess.run(
            [
                str(executable),
                "-c",
                "import sitecustomize; "
                "assert sitecustomize.marker=='other customizer preserved'",
            ],
            env={
                **env,
                "PYTHONPATH": str(shadow),
                "MUDPLOT_PATH_PROBE_LOG": str(shadow_log),
            },
            check=True,
            timeout=20,
        )
        assert shadow_log.is_file() and '"executable"' in shadow_log.read_text(
            encoding="utf-8"
        )
        results = [
            _probe(binary, executable, prefix, root, mode)
            for mode in ("default", "environment", "flag", "invalid-flag")
        ]
        print(
            json.dumps(
                {
                    "platform": sys.platform,
                    "python": sys.version.split()[0],
                    "selection": results,
                    "foreign_sitecustomize_preserved": True,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
