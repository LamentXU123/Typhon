from __future__ import annotations

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from flask import Flask, jsonify, render_template, request

WEBUI_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = WEBUI_DIR.parent
RUNNER_FILE = WEBUI_DIR / "runner.py"

app = Flask(__name__, template_folder="templates", static_folder="static")


def _to_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return default

def _to_int(value: Any, default: int | None = None) -> int | None:
    if value is None:
        return default
    if isinstance(value, str) and value.strip() == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_list(value: Any) -> List[str]:
    if value is None:
        return []
    try:
        return [str(item).strip() for item in eval(list) if str(item).strip()]
    except:
        normalized = value.replace("\r\n", "\n").replace("\r", "\n")
        items: List[str] = []
        for line in normalized.split("\n"):
            for token in line.split(","):
                cleaned = token.strip()
                if cleaned:
                    items.append(cleaned)
        return items
    return [str(value).strip()] if str(value).strip() else []


def _validate_and_build_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    mode = str(data.get("mode", "rce")).strip().lower()
    if mode not in {"rce", "read"}:
        raise ValueError("mode must be 'rce' or 'read'.")

    cmd = str(data.get("cmd", "")).strip()
    filepath = str(data.get("filepath", "")).strip()
    rce_method = str(data.get("rce_method", "exec")).strip().lower()
    if mode == "rce" and not cmd:
        raise ValueError("cmd is required in rce mode.")
    if mode == "read":
        if not filepath:
            raise ValueError("filepath is required in read mode.")
        if rce_method not in {"exec", "eval"}:
            raise ValueError("rce_method must be 'exec' or 'eval'.")

    payload = {
        "mode": mode,
        "cmd": cmd,
        "filepath": filepath,
        "rce_method": rce_method,
        "is_allow_exception_leak": _to_bool(
            data.get("is_allow_exception_leak"), default=True
        ),
        "options": {
            "local_scope": data.get("local_scope"),
            "banned_chr": _parse_list(data.get("banned_chr")),
            "allowed_chr": _parse_list(data.get("allowed_chr")),
            "banned_ast": _parse_list(data.get("banned_ast")),
            "banned_re": _parse_list(data.get("banned_re")),
            "max_length": _to_int(data.get("max_length"), None),
            "allow_unicode_bypass": _to_bool(
                data.get("allow_unicode_bypass"), default=False
            ),
            "print_all_payload": _to_bool(
                data.get("print_all_payload"), default=False
            ),
            "interactive": _to_bool(data.get("interactive"), default=True),
            "depth": _to_int(data.get("depth"), 5),
            "recursion_limit": _to_int(data.get("recursion_limit"), 200),
            "log_level": str(data.get("log_level", "INFO")).strip().upper()
            or "INFO",
        },
    }

    if payload["options"]["depth"] is None:
        payload["options"]["depth"] = 5
    if payload["options"]["recursion_limit"] is None:
        payload["options"]["recursion_limit"] = 200
    if payload["options"]["log_level"] not in {"DEBUG", "INFO", "QUIET"}:
        payload["options"]["log_level"] = "INFO"

    return payload


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/health")
def health():
    return jsonify({"ok": True, "service": "typhon-webui"})


@app.post("/api/run")
def run_typhon():
    req_data = request.get_json(silent=True) or {}
    try:
        payload = _validate_and_build_payload(req_data)
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400

    start = time.perf_counter()
    try:
        proc = subprocess.run(
            [sys.executable, str(RUNNER_FILE)],
            input=json.dumps(payload, ensure_ascii=False),
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
    except:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        import traceback
        return (
            jsonify(
                {
                    "ok": False,
                    "error": f"Failed to run runner: \r\n{traceback.format_exc()}",
                    "duration_ms": elapsed_ms,
                }
            ),
            408,
        )

    elapsed_ms = int((time.perf_counter() - start) * 1000)
    stdout = (proc.stdout or "").strip()
    stderr = (proc.stderr or "").strip()
    if not stdout:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "Runner returned empty output.",
                    "runner_exit_code": proc.returncode,
                    "runner_stderr": stderr,
                    "duration_ms": elapsed_ms,
                }
            ),
            500,
        )

    try:
        runner_result = json.loads(stdout)
    except json.JSONDecodeError:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "Failed to parse runner output as JSON.",
                    "runner_exit_code": proc.returncode,
                    "runner_stdout": stdout,
                    "runner_stderr": stderr,
                    "duration_ms": elapsed_ms,
                }
            ),
            500,
        )

    runner_result["duration_ms"] = elapsed_ms
    runner_result["runner_exit_code"] = proc.returncode
    if stderr:
        runner_result["runner_stderr"] = stderr
    http_code = 200 if runner_result.get("ok", False) else 500
    return jsonify(runner_result), http_code


if __name__ == "__main__":
    host = os.getenv("TYPHON_WEBUI_HOST", "127.0.0.1")
    port = int(os.getenv("TYPHON_WEBUI_PORT", "6240"))
    debug = os.getenv("TYPHON_WEBUI_DEBUG", "0") == "1"
    app.run(host=host, port=port, debug=debug)
