import sys
import re
import json
import logging
import traceback
import queue
import threading
import ctypes

from flask import Flask, request, jsonify, render_template

from ..Typhon import bypassRCE, bypassREAD

app = Flask(__name__)

_lock = threading.Lock()
_worker_thread: threading.Thread = None

_ANSI_RE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def strip_ansi(text: str) -> str:
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
                line = strip_ansi(self._buf[:nl])
                self._buf = self._buf[nl + 1:]
                self._q.put({"type": "log", "text": line})
                self._is_progress = False

            else:
                if cr + 1 < len(self._buf) and self._buf[cr + 1] == "\n":
                    line = strip_ansi(self._buf[:cr])
                    self._buf = self._buf[cr + 2:]
                    self._q.put({"type": "log", "text": line})
                    self._is_progress = False
                else:
                    before = strip_ansi(self._buf[:cr])
                    self._buf = self._buf[cr + 1:]
                    if before.strip():
                        t = "progress" if self._is_progress else "log"
                        self._q.put({"type": t, "text": before})
                    self._is_progress = True

    def flush(self):
        if self._buf.strip():
            t = "progress" if self._is_progress else "log"
            self._q.put({"type": t, "text": strip_ansi(self._buf)})
            self._buf = ""

class _QueueLogHandler(logging.Handler):
    def __init__(self, q: queue.Queue):
        super().__init__()
        self._q = q
        self.setFormatter(logging.Formatter("%(levelname)s %(message)s"))

    def emit(self, record):
        self._q.put({"type": "log", "text": self.format(record)})

def _parse_list(value, name: str):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return []
        try:
            p = json.loads(value)
            if isinstance(p, list):
                for x in p:
                    if not isinstance(x, str):
                        raise ValueError(f"Invalid {name}: Not a list of strings")
                return p
        except json.JSONDecodeError:
            pass
        if "," not in value:
            return p
        return [s.strip() for s in value.split(",") if s.strip()]
    raise ValueError(f"'{name}' must be a list or comma-separated string")


def _common_params(data: dict) -> dict:
    max_length = data.get("max_length")
    if max_length is not None:
        max_length = int(max_length)

    local_scope = data.get("local_scope")
    if local_scope is None or (isinstance(local_scope, str) and not local_scope.strip()):
        local_scope = None
    else:
        try:
            local_scope = eval(local_scope)
        except Exception as e:
            raise ValueError(f"Invalid 'local_scope': {e}")
        if not isinstance(local_scope, dict):
            raise ValueError(f"Invalid 'local_scope': Not a dict")

    return dict(
        local_scope=local_scope,
        banned_chr=_parse_list(data.get("banned_chr"), "banned_chr"),
        allowed_chr=_parse_list(data.get("allowed_chr"), "allowed_chr"),
        banned_ast=_parse_list(data.get("banned_ast"), "banned_ast"),
        banned_re=_parse_list(data.get("banned_re"), "banned_re"),
        max_length=max_length,
        depth=int(data.get("depth", 5)),
        recursion_limit=int(data.get("recursion_limit", 200)),
        allow_unicode_bypass=bool(data.get("allow_unicode_bypass", False)),
        print_all_payload=bool(data.get("print_all_payload", False)),
        interactive=bool(data.get("interactive", True)),
        log_level=str(data.get("log_level", "INFO")).upper(),
    )

def _stream_response(func_name: str, func_kwargs: dict):
    q: queue.Queue = queue.Queue()
    done = threading.Event()
    result = {"success": False, "error": ""}

    def worker():
        with _lock:
            old_stdout = sys.stdout
            writer = _QueueWriter(q)
            sys.stdout = writer

            log_handler = _QueueLogHandler(q)
            typhon_log = logging.getLogger("Typhon")
            typhon_log.addHandler(log_handler)

            try:
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
                typhon_log.removeHandler(log_handler)
                done.set()

    global _worker_thread
    _worker_thread = threading.Thread(target=worker, daemon=True)
    _worker_thread.start()

    def generate():
        while not done.is_set() or not q.empty():
            try:
                item = q.get(timeout=0.05)
                yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"
            except queue.Empty:
                yield ": keepalive\n\n"

        while not q.empty():
            item = q.get_nowait()
            yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"

        done_payload = {
            "type": "done",
            "success": result["success"],
            "error": result["error"],
        }
        yield f"data: {json.dumps(done_payload, ensure_ascii=False)}\n\n"

    return app.response_class(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/version")
def api_version():
    from ..Typhon import VERSION
    import platform
    return jsonify(typhon_version=VERSION, python_version=platform.python_version())


@app.route("/api/cancel", methods=["POST"])
def api_cancel():
    global _worker_thread
    t = _worker_thread
    if t is None or not t.is_alive():
        return jsonify(ok=False, reason="no running task")
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
        ctypes.c_ulong(t.ident),
        ctypes.py_object(SystemExit)
    )
    return jsonify(ok=(res == 1))


@app.route("/api/bypass/rce/stream", methods=["POST"])
def api_bypass_rce_stream():
    data = request.get_json(silent=True) or {}
    cmd = data.get("cmd", "").strip()
    if not cmd:
        return jsonify(success=False, error="'cmd' is required"), 400
    try:
        params = _common_params(data)
    except (ValueError, TypeError) as e:
        return jsonify(success=False, error=str(e)), 400
    params["cmd"] = cmd
    return _stream_response("rce", params)


@app.route("/api/bypass/read/stream", methods=["POST"])
def api_bypass_read_stream():
    data = request.get_json(silent=True) or {}
    filepath = data.get("filepath", "").strip()
    if not filepath:
        return jsonify(success=False, error="'filepath' is required"), 400
    rce_method = data.get("RCE_method", "exec").strip().lower()
    if rce_method not in ("exec", "eval"):
        return jsonify(success=False, error="'RCE_method' must be 'exec' or 'eval'"), 400
    try:
        params = _common_params(data)
    except (ValueError, TypeError) as e:
        return jsonify(success=False, error=str(e)), 400
    params["filepath"] = filepath
    params["RCE_method"] = rce_method
    params["is_allow_exception_leak"] = bool(data.get("is_allow_exception_leak", True))
    return _stream_response("read", params)

if __name__ == "__main__":
    print("=" * 50)
    print("  Typhon WebUI  —  http://127.0.0.1:6240")
    print("=" * 50)
    app.run(host="0.0.0.0", port=6240, debug=False, threaded=True)
