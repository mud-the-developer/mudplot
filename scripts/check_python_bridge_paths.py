"""Probe interpreter selection and controlled bridge faults in an isolated venv.

Run from the dev checkout: uv run python scripts/check_python_bridge_paths.py.
Same-version render wheels may be downloaded into the temporary venv only;
the project environment/lock stay untouched.
"""

from __future__ import annotations

import hashlib
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
    fault_file = root / "fault-mode.txt"
    fault_file.write_text("", encoding="utf-8")
    if mode == "faults" or mode.startswith("cap-"):
        env["MUDPLOT_BRIDGE_FAULT_FILE"] = str(fault_file)
        args += ["--python", str(executable)]
        if mode.startswith("cap-") and mode != "cap-noise":
            fault_file.write_text(mode, encoding="utf-8")
            result = subprocess.run(
                args, cwd=ROOT, env=env, capture_output=True, text=True, timeout=30
            )
            expected_error = (
                "exited with" if mode == "cap-exit" else "decode capabilities"
            )
            assert result.returncode != 0 and expected_error in result.stderr
            assert "stdout-only-marker" not in result.stderr
            return {"mode": mode, "startup_error": expected_error}
    elif mode == "environment":
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
            fault_results = (
                _failure_cases(connection, fault_file) if mode == "faults" else []
            )
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
        if arg.endswith((".json", ".png", ".pdf", ".svg"))
    ]
    assert paths and all(str(temporary) in arg for arg in paths)
    return {
        "mode": mode,
        "faults": fault_results,
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


def _failure_cases(connection: http.client.HTTPConnection, fault_file: Path):
    def snapshot():
        connection.request("GET", "/spec.json")
        response = connection.getresponse()
        assert response.status == 200
        spec = json.loads(response.read())
        connection.request("GET", "/fig.png")
        response = connection.getresponse()
        assert response.status == 200
        return spec, hashlib.sha256(response.read()).hexdigest()

    def action(title):
        connection.request(
            "POST",
            "/action",
            json.dumps({"type": "SetTitle", "text": title}),
            {"Content-Type": "application/json"},
        )
        response = connection.getresponse()
        return response.status, response.read()

    assert action("A")[0] == 200
    before = snapshot()
    assert action("B")[0] == 200
    future = snapshot()
    connection.request("POST", "/undo", b"")
    response = connection.getresponse()
    assert response.status == 200
    response.read()
    assert snapshot() == before
    rows = []
    for mode, expected in (
        ("apply-empty", "decode reduced spec"),
        ("apply-json", "decode reduced spec"),
        ("apply-exit", "exited with"),
        ("apply-stderr", "stderr truncated"),
        ("render-exit", "exited with"),
        ("render-missing", "read rendered figure"),
        ("render-empty", "empty rendered figure"),
        ("missing-optional", "mudplot[regression]"),
    ):
        fault_file.write_text(mode, encoding="utf-8")
        if mode == "missing-optional":
            payload = {
                "type": "AddLayer",
                "layer": {
                    "type": "regplot",
                    "x": "x",
                    "y": "y",
                    "regression": {"model": "robust"},
                    "confidence": None,
                },
            }
            connection.request(
                "POST",
                "/action",
                json.dumps(payload),
                {"Content-Type": "application/json"},
            )
            response = connection.getresponse()
            status, body = response.status, response.read()
        else:
            status, body = action("must not commit")
        fault_file.write_text("", encoding="utf-8")
        assert status == 400 and expected in body.decode(), (mode, status, body[:200])
        assert len(body) < 70_000 and b"stdout-only-marker" not in body
        assert snapshot() == before, mode
        connection.request("POST", "/redo", b"")
        response = connection.getresponse()
        assert response.status == 200
        response.read()
        assert snapshot() == future, mode
        connection.request("POST", "/undo", b"")
        response = connection.getresponse()
        assert response.status == 200
        response.read()
        assert snapshot() == before, mode
        rows.append(
            {
                "mode": mode,
                "error": expected,
                "state_png_redo_preserved": True,
                "spec_sha256": hashlib.sha256(
                    json.dumps(before[0], sort_keys=True).encode()
                ).hexdigest(),
                "png_sha256": before[1],
                "redo_png_sha256": future[1],
            }
        )
    for format_ in ("pdf", "svg"):
        fault_file.write_text("render-empty", encoding="utf-8")
        connection.request("GET", f"/fig.{format_}")
        response = connection.getresponse()
        assert response.status == 500 and b"empty rendered figure" in response.read()
        fault_file.write_text("", encoding="utf-8")
        assert snapshot() == before
        rows.append(
            {"mode": f"empty-{format_}", "export_rejected_state_preserved": True}
        )
    assert action("recovered")[0] == 200
    assert snapshot()[0]["panels"][0]["title"] == "recovered"
    return rows


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
        with (site / "_mudplot_bridge_fault.py").open("x", encoding="utf-8") as handle:
            handle.write(
                "import os,sys\nfrom pathlib import Path\n"
                "flag=os.environ.get('MUDPLOT_BRIDGE_FAULT_FILE')\n"
                "if flag and '-m' in sys.orig_argv and 'mudplot' in sys.orig_argv:\n"
                "    mode=Path(flag).read_text(encoding='utf-8')\n"
                "    args=sys.orig_argv\n"
                "    choices=('capabilities','apply','render')\n"
                "    operation=next((s for s in choices if s in args),'')\n"
                "    selected=(mode.startswith('cap-') and operation=='capabilities')\n"
                "    selected=selected or mode.startswith(operation+'-')\n"
                "    if mode=='cap-noise' and operation=='capabilities':\n"
                "        sys.stderr.write('e'*1048576);sys.stderr.flush()\n"
                "    elif mode and selected:\n"
                "        if mode.endswith(('exit','stderr')):\n"
                "            sys.stdout.write('stdout-only-marker')\n"
                "            sys.stdout.flush()\n"
                "            text='e'*1048576 if mode.endswith('stderr') else 'err'\n"
                "            sys.stderr.write(text)\n"
                "            sys.stderr.flush();os._exit(7)\n"
                "        if operation=='capabilities':\n"
                "            sys.stdout.write('{bad' if mode=='cap-json' else '')\n"
                "            sys.stdout.flush()\n"
                "        elif mode!='render-missing':\n"
                "            index=args.index('-o')+1 if operation=='apply' else 0\n"
                "            output=args[index or args.index('render')+2]\n"
                "            data=b'{bad' if mode=='apply-json' else b''\n"
                "            Path(output).write_bytes(data)\n"
                "        os._exit(0)\n"
            )
        with (site / "_mudplot_bridge_fault.pth").open("x", encoding="utf-8") as handle:
            handle.write("import _mudplot_bridge_fault\n")
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
            for mode in (
                "default",
                "environment",
                "flag",
                "invalid-flag",
                "cap-empty",
                "cap-json",
                "cap-exit",
                "cap-noise",
                "faults",
            )
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
