from __future__ import annotations

import ast
import builtins
import contextlib
import importlib
import io
import json
import traceback
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
import sys

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _parse_banned_ast(values: List[str]) -> List[type]:
    ast_nodes: List[type] = []
    for name in values:
        node = getattr(ast, name, None)
        if not isinstance(node, type) or not issubclass(node, ast.AST):
            raise ValueError(f"Unsupported AST node: {name}")
        ast_nodes.append(node)
    return ast_nodes

def _json_safe(value: Any) -> Any:
    try:
        json.dumps(value)
        return value
    except TypeError:
        return repr(value)

def _resolve_scope_tokens(scope: Dict[str, Any]):
    try:
        if not scope:
            return {}
        return eval(scope)
    except Exception as e:
        raise ValueError(f"Invalid when parsing local_scope: {e}")

def _run_typhon(payload: Dict[str, Any]) -> Dict[str, Any]:
    mode = payload.get("mode", "rce")
    options: Dict[str, Any] = payload.get("options", {})
    local_scope = options.get("local_scope")
    if local_scope is not None:
        local_scope = _resolve_scope_tokens(local_scope)

    common_kwargs = {
        "local_scope": local_scope,
        "banned_chr": options.get("banned_chr", []),
        "allowed_chr": options.get("allowed_chr", []),
        "banned_ast": _parse_banned_ast(options.get("banned_ast", [])),
        "banned_re": options.get("banned_re", []),
        "max_length": options.get("max_length"),
        "allow_unicode_bypass": bool(options.get("allow_unicode_bypass", False)),
        "print_all_payload": bool(options.get("print_all_payload", False)),
        "interactive": bool(options.get("interactive", True)),
        "depth": int(options.get("depth", 5)),
        "recursion_limit": int(options.get("recursion_limit", 200)),
        "log_level": str(options.get("log_level", "INFO")).upper(),
    }

    capture_out = io.StringIO()
    capture_err = io.StringIO()
    result = None
    error = None
    exit_code = None

    with contextlib.redirect_stdout(capture_out), contextlib.redirect_stderr(capture_err):
        try:
            import Typhon

            if mode == "rce":
                cmd = str(payload.get("cmd", "")).strip()
                result = Typhon.bypassRCE(cmd=cmd, **common_kwargs)
            elif mode == "read":
                filepath = str(payload.get("filepath", "")).strip()
                rce_method = str(payload.get("rce_method", "exec")).strip()
                is_allow_exception_leak = bool(
                    payload.get("is_allow_exception_leak", True)
                )
                result = Typhon.bypassREAD(
                    filepath=filepath,
                    RCE_method=rce_method,
                    is_allow_exception_leak=is_allow_exception_leak,
                    **common_kwargs,
                )
            else:
                raise ValueError("mode must be 'rce' or 'read'.")
        except SystemExit as exc:
            if exc.code is None:
                exit_code = 0
            elif isinstance(exc.code, int):
                exit_code = exc.code
            else:
                exit_code = 1
        except Exception:
            error = traceback.format_exc()

    stdout_text = capture_out.getvalue()
    stderr_text = capture_err.getvalue()
    output = stdout_text
    if stderr_text:
        output = f"{output}\n[stderr]\n{stderr_text}".strip()

    success = exit_code == 0
    return {
        "ok": error is None,
        "success": success,
        "exit_code": exit_code,
        "output": output,
        "result": _json_safe(result),
        "error": error,
    }


def main() -> int:
    import sys

    raw = sys.stdin.read()
    if not raw.strip():
        print(json.dumps({"ok": False, "error": "No JSON payload provided."}))
        return 1

    try:
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise ValueError("JSON payload must be an object.")
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"Invalid JSON input: {exc}"}))
        return 1

    try:
        result = _run_typhon(payload)
    except Exception:
        result = {"ok": False, "error": traceback.format_exc()}

    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
