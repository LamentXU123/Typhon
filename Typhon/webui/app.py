import ast
import ctypes
import json
import logging
import platform
import queue
import re
import sys
import threading
import traceback
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse


_ROOT = Path(__file__).resolve().parent
_INDEX_HTML = _ROOT / "templates" / "index.html"
_STATIC_DIR = _ROOT / "static"

_lock = threading.Lock()
_worker_thread = None  # type: Optional[threading.Thread]

_ANSI_RE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def _strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)


class _QueueWriter:
    def __init__(self, q: queue.Queue):
        self._q = q
        self._buf = ""
        self._is_progress = False

    def write(self, s: str):
        self._buf += s
        while True:
            cr = self._buf.find("\r")
            nl = self._buf.find("\n")
            if cr == -1 and nl == -1:
                break

            if nl != -1 and (cr == -1 or nl < cr):
                line = _strip_ansi(self._buf[:nl])
                self._buf = self._buf[nl + 1 :]
                self._q.put({"type": "log", "text": line})
                self._is_progress = False
                continue

            if cr + 1 < len(self._buf) and self._buf[cr + 1] == "\n":
                line = _strip_ansi(self._buf[:cr])
                self._buf = self._buf[cr + 2 :]
                self._q.put({"type": "log", "text": line})
                self._is_progress = False
                continue

            before = _strip_ansi(self._buf[:cr])
            self._buf = self._buf[cr + 1 :]
            if before.strip():
                t = "progress" if self._is_progress else "log"
                self._q.put({"type": t, "text": before})
            self._is_progress = True

    def flush(self):
        if self._buf.strip():
            t = "progress" if self._is_progress else "log"
            self._q.put({"type": t, "text": _strip_ansi(self._buf)})
            self._buf = ""


class _QueueLogHandler(logging.Handler):
    def __init__(self, q: queue.Queue):
        super().__init__()
        self._q = q
        self.setFormatter(logging.Formatter("%(levelname)s %(message)s"))

    def emit(self, record):
        if record.name.startswith("Typhon"):
            self._q.put({"type": "log", "text": self.format(record)})


def _parse_list(value, name: str) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        if value.endswith(",]"):
            value = value[:-2] + ']'
        value = value.strip()
        if not value:
            return []
        try:
            p = json.loads(value)
            for x in p:
                if not isinstance(x, str):
                    raise ValueError(f"Invalid {name}: Not a list of strings")
            return p
        except json.JSONDecodeError:
            raise
    raise ValueError(f"'{name}' must be a list or comma-separated string")

def _parse_ast(name):
    output = []
    for i in name:
        if i[:4] == 'ast.':
            i = i[4:]
        try:
            ast_i = eval(f'ast.{i}')
        except:
            raise ValueError(f"Invalid {name}: Unknown ast node '{i}'")
        output.append(ast_i)
    return output

def _common_params(data: Dict) -> Dict:
    max_length = data.get("max_length")
    if max_length is not None:
        max_length = int(max_length)

    local_scope = data.get("local_scope")
    if local_scope is None or (isinstance(local_scope, str) and not local_scope.strip()):
        local_scope = {}
    else:
        try:
            local_scope = eval(local_scope)
        except Exception as e:
            raise ValueError(f"Invalid 'local_scope': {e}")
        if not isinstance(local_scope, dict):
            raise ValueError("Invalid 'local_scope': Not a dict")

    return dict(
        local_scope=local_scope,
        banned_chr=_parse_list(data.get("banned_chr"), "banned_chr"),
        allowed_chr=_parse_list(data.get("allowed_chr"), "allowed_chr"),
        banned_ast=_parse_ast(list(_parse_list(data.get("banned_ast"), "banned_ast"))),
        banned_re=list(_parse_list(data.get("banned_re"), "banned_re")),
        max_length=max_length,
        depth=int(data.get("depth", 5)),
        recursion_limit=int(data.get("recursion_limit", 200)),
        allow_unicode_bypass=bool(data.get("allow_unicode_bypass", False)),
        print_all_payload=bool(data.get("print_all_payload", False)),
        interactive=bool(data.get("interactive", True)),
        log_level=str(data.get("log_level", "INFO")).upper(),
    )


def _start_worker(func_name: str, func_kwargs: Dict) -> Tuple[queue.Queue, threading.Event, Dict]:
    q: queue.Queue = queue.Queue()
    done = threading.Event()
    result = {"success": False, "error": ""}

    def worker():
        with _lock:
            old_stdout = sys.stdout
            writer = _QueueWriter(q)
            sys.stdout = writer

            root_logger = logging.getLogger()
            log_handler = _QueueLogHandler(q)
            root_logger.addHandler(log_handler)

            try:
                from ..Typhon import bypassRCE, bypassREAD

                if func_name == "rce":
                    bypassRCE(**func_kwargs)
                else:
                    bypassREAD(**func_kwargs)

            except SystemExit as e:
                result["success"] = (e.code == 0)
                if e.code != 0:
                    result["error"] = f"Typhon exited with code {e.code}"

            except Exception:
                result["error"] = traceback.format_exc()

            finally:
                writer.flush()
                sys.stdout = old_stdout
                root_logger.removeHandler(log_handler)
                done.set()

    global _worker_thread
    _worker_thread = threading.Thread(target=worker, daemon=True)
    _worker_thread.start()
    return q, done, result


class _WebUIHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        logging.getLogger("Typhon.webui").info("%s - %s", self.address_string(), fmt % args)

    def _send_bytes(self, status: int, body: bytes, content_type: str):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status: int, payload: Dict):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._send_bytes(status, body, "application/json; charset=utf-8")

    def _read_json(self) -> Dict:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        if not raw:
            return {}
        try:
            obj = json.loads(raw.decode("utf-8"))
        except Exception:
            raise ValueError("invalid json body")
        if not isinstance(obj, dict):
            raise ValueError("json body must be an object")
        return obj

    def _serve_index(self):
        body = _INDEX_HTML.read_bytes()
        self._send_bytes(HTTPStatus.OK, body, "text/html; charset=utf-8")

    def _serve_static(self, path: str):
        rel = path[len("/static/") :]
        safe = Path(rel)
        if safe.is_absolute() or ".." in safe.parts:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        fp = (_STATIC_DIR / safe).resolve()
        if _STATIC_DIR not in fp.parents and fp != _STATIC_DIR:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        if not fp.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        ctype = "application/octet-stream"
        if fp.suffix == ".png":
            ctype = "image/png"
        body = fp.read_bytes()
        self._send_bytes(HTTPStatus.OK, body, ctype)

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            return self._serve_index()
        if path.startswith("/static/"):
            return self._serve_static(path)
        if path == "/api/version":
            from ..Typhon import VERSION

            return self._send_json(
                HTTPStatus.OK,
                {"typhon_version": VERSION, "python_version": platform.python_version()},
            )
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self):
        path = urlparse(self.path).path

        if path == "/api/cancel":
            global _worker_thread
            t = _worker_thread
            if t is None or not t.is_alive():
                return self._send_json(HTTPStatus.OK, {"ok": False, "reason": "no running task"})
            res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
                ctypes.c_ulong(t.ident),
                ctypes.py_object(SystemExit),
            )
            return self._send_json(HTTPStatus.OK, {"ok": (res == 1)})

        if path in ("/api/bypass/rce/stream", "/api/bypass/read/stream"):
            try:
                data = self._read_json()
            except ValueError as e:
                return self._send_json(HTTPStatus.BAD_REQUEST, {"success": False, "error": str(e)})

            func_name = "rce" if path.endswith("/rce/stream") else "read"

            if func_name == "rce":
                cmd = str(data.get("cmd", "")).strip()
                if not cmd:
                    return self._send_json(HTTPStatus.BAD_REQUEST, {"success": False, "error": "'cmd' is required"})
                try:
                    params = _common_params(data)
                except (ValueError, TypeError) as e:
                    return self._send_json(HTTPStatus.BAD_REQUEST, {"success": False, "error": str(e)})
                params["cmd"] = cmd
            else:
                filepath = str(data.get("filepath", "")).strip()
                if not filepath:
                    return self._send_json(
                        HTTPStatus.BAD_REQUEST, {"success": False, "error": "'filepath' is required"}
                    )
                rce_method = str(data.get("RCE_method", "exec")).strip().lower()
                if rce_method not in ("exec", "eval"):
                    return self._send_json(
                        HTTPStatus.BAD_REQUEST,
                        {"success": False, "error": "'RCE_method' must be 'exec' or 'eval'"},
                    )
                try:
                    params = _common_params(data)
                except (ValueError, TypeError) as e:
                    return self._send_json(HTTPStatus.BAD_REQUEST, {"success": False, "error": str(e)})
                params["filepath"] = filepath
                params["RCE_method"] = rce_method
                params["is_allow_exception_leak"] = bool(data.get("is_allow_exception_leak", True))

            q, done, result = _start_worker(func_name, params)

            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("X-Accel-Buffering", "no")
            self.send_header("Connection", "keep-alive")
            self.end_headers()

            def send_event(item: dict):
                payload = f"data: {json.dumps(item, ensure_ascii=False)}\n\n".encode("utf-8")
                self.wfile.write(payload)
                self.wfile.flush()

            try:
                while not done.is_set() or not q.empty():
                    try:
                        item = q.get(timeout=0.05)
                        send_event(item)
                    except queue.Empty:
                        self.wfile.write(b": keepalive\n\n")
                        self.wfile.flush()

                while not q.empty():
                    item = q.get_nowait()
                    send_event(item)

                send_event({"type": "done", "success": result["success"], "error": result["error"]})
            except BrokenPipeError:
                return
            except ConnectionResetError:
                return
            return

        self.send_error(HTTPStatus.NOT_FOUND)


def run(host: str = "127.0.0.1", port: int = 6240) -> None:
    logging.basicConfig(level="INFO", format="%(levelname)s %(message)s")
    if not _INDEX_HTML.is_file():
        raise FileNotFoundError(f"Missing WebUI template: {_INDEX_HTML}")

    print("=" * 50)
    print(f"  Typhon WebUI  —  http://{host}:{port}")
    print("=" * 50)

    server = ThreadingHTTPServer((host, port), _WebUIHandler)
    try:
        server.serve_forever(poll_interval=0.2)
    finally:
        server.server_close()


if __name__ == "__main__":
    run()
