import os
import sys
import io

_real_stdout, sys.stdout = sys.stdout, io.StringIO()
try:
    import ast
    import json
    import queue
    import threading
    import logging
    import http.client
    import unittest
    from unittest.mock import patch

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    logging.basicConfig(handlers=[logging.NullHandler()], force=True)

    from Typhon.webui.app import (
        _strip_ansi, _parse_list, _parse_ast, _common_params,
        _QueueWriter, _QueueLogHandler, ThreadingHTTPServer, _WebUIHandler,
    )
finally:
    sys.stdout = _real_stdout

def _q2list(q: queue.Queue):
    items = []
    while not q.empty():
        items.append(q.get_nowait())
    return items

def _http(host, port, method, path, body=None, timeout=5):
    headers = {}
    if body is not None:
        headers = {
            "Content-Type": "application/json",
            "Content-Length": str(len(body)),
        }
    conn = http.client.HTTPConnection(host, port, timeout=timeout)
    conn.request(method, path, body=body, headers=headers)
    resp = conn.getresponse()
    data = resp.read()
    conn.close()
    return resp.status, resp.getheader("Content-Type") or "", data


def _read_sse(host, port, path, body_bytes, timeout=10):
    conn = http.client.HTTPConnection(host, port, timeout=timeout)
    conn.request(
        "POST", path, body=body_bytes,
        headers={
            "Content-Type": "application/json",
            "Content-Length": str(len(body_bytes)),
        },
    )
    resp = conn.getresponse()
    status = resp.status
    ctype = resp.getheader("Content-Type") or ""
    events = []
    if status != 200:
        resp.read()
        conn.close()
        return status, ctype, events
    try:
        while True:
            line = resp.readline()
            if not line:
                break
            text = line.decode("utf-8", errors="replace").rstrip("\r\n")
            if text.startswith("data: "):
                try:
                    ev = json.loads(text[6:])
                    events.append(ev)
                    if ev.get("type") == "done":
                        conn.close()
                        return status, ctype, events
                except json.JSONDecodeError:
                    pass
    except Exception:
        pass
    conn.close()
    return status, ctype, events


# ---------------------------------------------------------------------------
# TestStripAnsi
# ---------------------------------------------------------------------------

class TestStripAnsi(unittest.TestCase):
    def test_strips_color_codes(self):
        self.assertEqual(_strip_ansi("\x1B[31mRed\x1B[0m"), "Red")

    def test_strips_bold(self):
        self.assertEqual(_strip_ansi("\x1B[1mBold\x1B[0m"), "Bold")

    def test_no_ansi_unchanged(self):
        self.assertEqual(_strip_ansi("plain text"), "plain text")

    def test_empty_string(self):
        self.assertEqual(_strip_ansi(""), "")

    def test_only_ansi_becomes_empty(self):
        self.assertEqual(_strip_ansi("\x1B[0m"), "")

    def test_multiple_sequences(self):
        self.assertEqual(
            _strip_ansi("\x1B[32mGreen\x1B[0m and \x1B[31mRed\x1B[0m"),
            "Green and Red",
        )


# ---------------------------------------------------------------------------
# TestParseList
# ---------------------------------------------------------------------------

class TestParseList(unittest.TestCase):
    def test_none_returns_empty(self):
        self.assertEqual(_parse_list(None, "test"), [])

    def test_empty_string_returns_empty(self):
        self.assertEqual(_parse_list("", "test"), [])

    def test_whitespace_only_returns_empty(self):
        self.assertEqual(_parse_list("   ", "test"), [])

    def test_list_passthrough(self):
        self.assertEqual(_parse_list(["a", "b"], "test"), ["a", "b"])

    def test_json_array_string(self):
        self.assertEqual(_parse_list('["import", "os"]', "test"), ["import", "os"])

    def test_trailing_comma_json(self):
        self.assertEqual(_parse_list('["a", "b",]', "test"), ["a", "b"])

    def test_trailing_whitespace_with_trailing_comma(self):
        self.assertEqual(_parse_list('  ["a", "b",]  ', "test"), ["a", "b"])

    def test_single_item(self):
        self.assertEqual(_parse_list('["__builtins__"]', "test"), ["__builtins__"])

    def test_invalid_type_raises(self):
        with self.assertRaises((ValueError, TypeError)):
            _parse_list(123, "test")

    def test_non_string_elements_raise(self):
        with self.assertRaises(ValueError):
            _parse_list([1, 2, 3], "test")

    def test_json_parse_error_raises(self):
        with self.assertRaises(json.JSONDecodeError):
            _parse_list("[invalid json", "test")

    def test_json_non_list_raises(self):
        with self.assertRaises(Exception):
            _parse_list('{"key": "val"}', "test")


# ---------------------------------------------------------------------------
# TestParseAst
# ---------------------------------------------------------------------------

class TestParseAst(unittest.TestCase):
    def test_empty_list(self):
        self.assertEqual(_parse_ast([]), [])

    def test_valid_nodes_without_prefix(self):
        self.assertEqual(
            _parse_ast(["Import", "Call", "Attribute"]),
            [ast.Import, ast.Call, ast.Attribute],
        )

    def test_ast_prefix_stripped(self):
        self.assertEqual(_parse_ast(["ast.Import"]), [ast.Import])

    def test_mixed_prefix(self):
        self.assertEqual(_parse_ast(["ast.Import", "Call"]), [ast.Import, ast.Call])

    def test_invalid_node_raises(self):
        with self.assertRaises(ValueError):
            _parse_ast(["FakeNonExistentNode"])


# ---------------------------------------------------------------------------
# TestCommonParams
# ---------------------------------------------------------------------------

class TestCommonParams(unittest.TestCase):
    def test_defaults(self):
        result = _common_params({})
        self.assertEqual(result["local_scope"], {})
        self.assertEqual(result["banned_chr"], [])
        self.assertEqual(result["allowed_chr"], [])
        self.assertEqual(result["banned_ast"], [])
        self.assertEqual(result["banned_re"], [])
        self.assertIsNone(result["max_length"])
        self.assertEqual(result["depth"], 5)
        self.assertEqual(result["recursion_limit"], 200)
        self.assertFalse(result["allow_unicode_bypass"])
        self.assertFalse(result["print_all_payload"])
        self.assertTrue(result["interactive"])
        self.assertEqual(result["log_level"], "INFO")

    def test_local_scope_dict_string(self):
        result = _common_params({"local_scope": '{"x": 1}'})
        self.assertEqual(result["local_scope"], {"x": 1})

    def test_local_scope_none_builtins(self):
        result = _common_params({"local_scope": '{"__builtins__": None}'})
        self.assertEqual(result["local_scope"], {"__builtins__": None})

    def test_empty_local_scope_string(self):
        result = _common_params({"local_scope": "   "})
        self.assertEqual(result["local_scope"], {})

    def test_invalid_local_scope_not_dict(self):
        with self.assertRaises(ValueError):
            _common_params({"local_scope": '"a string"'})

    def test_invalid_local_scope_syntax_error(self):
        with self.assertRaises(ValueError):
            _common_params({"local_scope": "{bad python}"})

    def test_max_length_int(self):
        result = _common_params({"max_length": "100"})
        self.assertEqual(result["max_length"], 100)

    def test_banned_chr_list(self):
        result = _common_params({"banned_chr": '["import", "os"]'})
        self.assertEqual(result["banned_chr"], ["import", "os"])

    def test_allowed_chr_list(self):
        result = _common_params({"allowed_chr": '["a", "b", "c"]'})
        self.assertEqual(result["allowed_chr"], ["a", "b", "c"])

    def test_banned_re_list(self):
        result = _common_params({"banned_re": '[".*import.*"]'})
        self.assertEqual(result["banned_re"], [".*import.*"])

    def test_banned_ast_nodes(self):
        result = _common_params({"banned_ast": '["Import"]'})
        self.assertEqual(result["banned_ast"], [ast.Import])

    def test_log_level_uppercased(self):
        result = _common_params({"log_level": "debug"})
        self.assertEqual(result["log_level"], "DEBUG")

    def test_depth_and_recursion_limit(self):
        result = _common_params({"depth": "10", "recursion_limit": "500"})
        self.assertEqual(result["depth"], 10)
        self.assertEqual(result["recursion_limit"], 500)

    def test_bool_flags(self):
        result = _common_params({
            "allow_unicode_bypass": True,
            "print_all_payload": True,
            "interactive": False,
        })
        self.assertTrue(result["allow_unicode_bypass"])
        self.assertTrue(result["print_all_payload"])
        self.assertFalse(result["interactive"])


# ---------------------------------------------------------------------------
# TestQueueWriter
# ---------------------------------------------------------------------------

class TestQueueWriter(unittest.TestCase):
    def test_newline_emits_log_event(self):
        q = queue.Queue()
        w = _QueueWriter(q)
        w.write("Hello\n")
        items = _q2list(q)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["type"], "log")
        self.assertEqual(items[0]["text"], "Hello")

    def test_multiple_newlines(self):
        q = queue.Queue()
        w = _QueueWriter(q)
        w.write("a\nb\nc\n")
        items = _q2list(q)
        self.assertEqual([i["text"] for i in items], ["a", "b", "c"])

    def test_flush_sends_remaining_buffer(self):
        q = queue.Queue()
        w = _QueueWriter(q)
        w.write("no newline")
        self.assertTrue(q.empty())
        w.flush()
        items = _q2list(q)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["text"], "no newline")

    def test_flush_empty_buffer_emits_nothing(self):
        q = queue.Queue()
        w = _QueueWriter(q)
        w.flush()
        self.assertTrue(q.empty())

    def test_strips_ansi_from_log(self):
        q = queue.Queue()
        w = _QueueWriter(q)
        w.write("\x1B[32mGreen\x1B[0m\n")
        item = q.get_nowait()
        self.assertEqual(item["text"], "Green")

    def test_carriage_return_progress_type(self):
        q = queue.Queue()
        w = _QueueWriter(q)
        # First \r: is_progress was False → emits "log"
        w.write("step one\r")
        # Second \r: is_progress is now True → emits "progress"
        w.write("step two\r")
        items = _q2list(q)
        self.assertIn("progress", [i["type"] for i in items])

    def test_crlf_emits_log(self):
        q = queue.Queue()
        w = _QueueWriter(q)
        w.write("line\r\n")
        items = _q2list(q)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["type"], "log")
        self.assertEqual(items[0]["text"], "line")

    def test_partial_write_buffered_until_flush(self):
        q = queue.Queue()
        w = _QueueWriter(q)
        w.write("part1")
        w.write("part2")
        self.assertTrue(q.empty())
        w.flush()
        self.assertEqual(q.get_nowait()["text"], "part1part2")


# ---------------------------------------------------------------------------
# TestQueueLogHandler
# ---------------------------------------------------------------------------

class TestQueueLogHandler(unittest.TestCase):
    def _make_handler(self):
        q = queue.Queue()
        return q, _QueueLogHandler(q)

    def test_typhon_logger_captured(self):
        q, handler = self._make_handler()
        logger = logging.getLogger("Typhon.test.webui_unit")
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        try:
            logger.info("hello from Typhon")
            item = q.get_nowait()
            self.assertEqual(item["type"], "log")
            self.assertIn("hello from Typhon", item["text"])
        finally:
            logger.removeHandler(handler)

    def test_non_typhon_logger_ignored(self):
        q, handler = self._make_handler()
        logger = logging.getLogger("other.namespace.not.typhon")
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        try:
            logger.info("should be ignored")
            self.assertTrue(q.empty())
        finally:
            logger.removeHandler(handler)

    def test_format_includes_level_and_message(self):
        q, handler = self._make_handler()
        logger = logging.getLogger("Typhon.test.format_check")
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        try:
            logger.warning("watch out!")
            item = q.get_nowait()
            self.assertIn("WARNING", item["text"])
            self.assertIn("watch out!", item["text"])
        finally:
            logger.removeHandler(handler)

    def test_debug_level_captured(self):
        q, handler = self._make_handler()
        logger = logging.getLogger("Typhon.test.debug_level")
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        try:
            logger.debug("debug detail")
            item = q.get_nowait()
            self.assertIn("DEBUG", item["text"])
        finally:
            logger.removeHandler(handler)


# ---------------------------------------------------------------------------
# TestWebUIServer  (integration — starts a real ThreadingHTTPServer)
# ---------------------------------------------------------------------------

class TestWebUIServer(unittest.TestCase):

    _HOST = "127.0.0.1"
    _PORT = 0
    _server = None
    _server_thread = None

    @classmethod
    def setUpClass(cls):
        cls._server = ThreadingHTTPServer((cls._HOST, cls._PORT), _WebUIHandler)
        cls._PORT = cls._server.server_address[1]
        cls._server_thread = threading.Thread(
            target=cls._server.serve_forever,
            kwargs={"poll_interval": 0.1},
            daemon=True,
        )
        cls._server_thread.start()

    @classmethod
    def tearDownClass(cls):
        if cls._server:
            cls._server.shutdown()
            cls._server.server_close()

    # ------------------------------------------------------------------ helpers

    def _get(self, path, timeout=5):
        return _http(self._HOST, self._PORT, "GET", path, timeout=timeout)

    def _post(self, path, data, timeout=5):
        body = json.dumps(data).encode("utf-8")
        return _http(self._HOST, self._PORT, "POST", path, body, timeout)

    def _post_raw(self, path, raw_body, timeout=5):
        conn = http.client.HTTPConnection(self._HOST, self._PORT, timeout=timeout)
        conn.request(
            "POST", path, body=raw_body,
            headers={
                "Content-Type": "application/json",
                "Content-Length": str(len(raw_body)),
            },
        )
        resp = conn.getresponse()
        body = resp.read()
        conn.close()
        return resp.status, body

    def _stream(self, path, data, timeout=10):
        body_bytes = json.dumps(data).encode("utf-8")
        return _read_sse(self._HOST, self._PORT, path, body_bytes, timeout=timeout)

    def _get_done(self, events):
        return next((e for e in events if e.get("type") == "done"), None)

    # ------------------------------------------------------------------ GET

    def test_get_root_returns_html(self):
        status, ctype, body = self._get("/")
        self.assertEqual(status, 200)
        self.assertIn("text/html", ctype)
        self.assertIn(b"TYPHON", body)

    def test_get_index_html_alias(self):
        status, ctype, body = self._get("/index.html")
        self.assertEqual(status, 200)
        self.assertIn("text/html", ctype)

    def test_get_version_json_structure(self):
        status, ctype, body = self._get("/api/version")
        self.assertEqual(status, 200)
        self.assertIn("application/json", ctype)
        data = json.loads(body)
        self.assertIn("typhon_version", data)
        self.assertIn("python_version", data)
        self.assertIsInstance(data["typhon_version"], str)
        self.assertIsInstance(data["python_version"], str)

    def test_get_static_png(self):
        status, ctype, body = self._get("/static/typhon.png")
        self.assertEqual(status, 200)
        self.assertEqual(ctype, "image/png")
        self.assertGreater(len(body), 0)

    def test_get_unknown_path_404(self):
        status, _, _ = self._get("/not_a_real_route")
        self.assertEqual(status, 404)

    def test_get_static_path_traversal_blocked(self):
        status, _, _ = self._get("/static/../app.py")
        self.assertEqual(status, 404)

    def test_get_static_nonexistent_file_404(self):
        status, _, _ = self._get("/static/does_not_exist.png")
        self.assertEqual(status, 404)

    # ------------------------------------------------------------------ POST /api/cancel

    def test_cancel_no_running_task(self):
        status, _, body = self._post("/api/cancel", {})
        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertFalse(data["ok"])
        self.assertIn("no running task", data.get("reason", ""))

    # ------------------------------------------------------------------ POST /api/bypass/rce/stream — validation

    def test_rce_missing_cmd_400(self):
        status, _, body = self._post("/api/bypass/rce/stream", {})
        self.assertEqual(status, 400)
        data = json.loads(body)
        self.assertFalse(data["success"])
        self.assertIn("cmd", data["error"])

    def test_rce_empty_cmd_400(self):
        status, _, body = self._post("/api/bypass/rce/stream", {"cmd": "   "})
        self.assertEqual(status, 400)
        self.assertFalse(json.loads(body)["success"])

    def test_rce_invalid_local_scope_400(self):
        status, _, body = self._post(
            "/api/bypass/rce/stream",
            {"cmd": "id", "local_scope": "not_a_dict_value"},
        )
        self.assertEqual(status, 400)
        self.assertFalse(json.loads(body)["success"])

    def test_rce_invalid_json_body_400(self):
        status, _ = self._post_raw("/api/bypass/rce/stream", b"not json")
        self.assertEqual(status, 400)

    def test_rce_invalid_banned_ast_400(self):
        status, _, body = self._post(
            "/api/bypass/rce/stream",
            {"cmd": "id", "banned_ast": '["FakeNonExistentASTNode"]'},
        )
        self.assertEqual(status, 400)
        self.assertFalse(json.loads(body)["success"])

    # ------------------------------------------------------------------ POST /api/bypass/read/stream — validation

    def test_read_missing_filepath_400(self):
        status, _, body = self._post("/api/bypass/read/stream", {})
        self.assertEqual(status, 400)
        data = json.loads(body)
        self.assertFalse(data["success"])
        self.assertIn("filepath", data["error"])

    def test_read_empty_filepath_400(self):
        status, _, body = self._post("/api/bypass/read/stream", {"filepath": "  "})
        self.assertEqual(status, 400)
        self.assertFalse(json.loads(body)["success"])

    def test_read_invalid_rce_method_400(self):
        status, _, body = self._post(
            "/api/bypass/read/stream",
            {"filepath": "/flag", "RCE_method": "shell"},
        )
        self.assertEqual(status, 400)
        data = json.loads(body)
        self.assertFalse(data["success"])
        self.assertIn("RCE_method", data["error"])

    def test_read_invalid_local_scope_400(self):
        status, _, body = self._post(
            "/api/bypass/read/stream",
            {"filepath": "/flag", "RCE_method": "exec", "local_scope": "badvalue"},
        )
        self.assertEqual(status, 400)
        self.assertFalse(json.loads(body)["success"])

    def test_post_unknown_path_404(self):
        status, _, _ = self._post("/api/unknown", {})
        self.assertEqual(status, 404)

    # ------------------------------------------------------------------ SSE streaming — RCE

    def test_rce_stream_returns_sse_content_type(self):
        with patch("Typhon.Typhon.bypassRCE", side_effect=SystemExit(0)):
            status, ctype, _ = self._stream(
                "/api/bypass/rce/stream", {"cmd": "whoami", "interactive": False}
            )
        self.assertEqual(status, 200)
        self.assertIn("text/event-stream", ctype)

    def test_rce_stream_contains_done_event(self):
        with patch("Typhon.Typhon.bypassRCE", side_effect=SystemExit(0)):
            _, _, events = self._stream(
                "/api/bypass/rce/stream", {"cmd": "whoami", "interactive": False}
            )
        self.assertIsNotNone(self._get_done(events), "No 'done' event received")

    def test_rce_stream_exit0_success_true(self):
        with patch("Typhon.Typhon.bypassRCE", side_effect=SystemExit(0)):
            _, _, events = self._stream(
                "/api/bypass/rce/stream", {"cmd": "id", "interactive": False}
            )
        done = self._get_done(events)
        self.assertTrue(done["success"])
        self.assertEqual(done.get("error", ""), "")

    def test_rce_stream_exit1_success_false(self):
        with patch("Typhon.Typhon.bypassRCE", side_effect=SystemExit(1)):
            _, _, events = self._stream(
                "/api/bypass/rce/stream", {"cmd": "id", "interactive": False}
            )
        self.assertFalse(self._get_done(events)["success"])

    def test_rce_stream_exception_produces_error(self):
        with patch("Typhon.Typhon.bypassRCE", side_effect=RuntimeError("boom")):
            _, _, events = self._stream(
                "/api/bypass/rce/stream", {"cmd": "id", "interactive": False}
            )
        done = self._get_done(events)
        self.assertFalse(done["success"])
        self.assertIn("boom", done.get("error", ""))

    def test_rce_stream_stdout_captured_as_log_event(self):
        def fake_rce(**kwargs):
            print("test-output-marker-xyz")
            raise SystemExit(0)

        with patch("Typhon.Typhon.bypassRCE", side_effect=fake_rce):
            _, _, events = self._stream(
                "/api/bypass/rce/stream", {"cmd": "id", "interactive": False}
            )
        log_texts = [e.get("text", "") for e in events if e.get("type") == "log"]
        self.assertTrue(
            any("test-output-marker-xyz" in t for t in log_texts),
            f"Marker not found in log events: {log_texts}",
        )

    def test_rce_stream_params_forwarded(self):
        received = {}

        def capture_rce(**kwargs):
            received.update(kwargs)
            raise SystemExit(0)

        with patch("Typhon.Typhon.bypassRCE", side_effect=capture_rce):
            self._stream("/api/bypass/rce/stream", {
                "cmd": "whoami",
                "interactive": False,
                "banned_chr": '["import", "os"]',
                "depth": "3",
                "recursion_limit": "100",
                "allow_unicode_bypass": True,
            })
        self.assertEqual(received.get("cmd"), "whoami")
        self.assertFalse(received.get("interactive"))
        self.assertEqual(received.get("banned_chr"), ["import", "os"])
        self.assertEqual(received.get("depth"), 3)
        self.assertEqual(received.get("recursion_limit"), 100)
        self.assertTrue(received.get("allow_unicode_bypass"))

    def test_all_sse_events_have_type_field(self):
        with patch("Typhon.Typhon.bypassRCE", side_effect=SystemExit(0)):
            _, _, events = self._stream(
                "/api/bypass/rce/stream", {"cmd": "id", "interactive": False}
            )
        for ev in events:
            self.assertIn("type", ev, f"Event missing 'type': {ev}")

    def test_done_event_has_success_field(self):
        with patch("Typhon.Typhon.bypassRCE", side_effect=SystemExit(0)):
            _, _, events = self._stream(
                "/api/bypass/rce/stream", {"cmd": "id", "interactive": False}
            )
        done = self._get_done(events)
        self.assertIn("success", done)

    def test_log_event_has_text_field(self):
        def fake_rce(**kwargs):
            print("some log line")
            raise SystemExit(0)

        with patch("Typhon.Typhon.bypassRCE", side_effect=fake_rce):
            _, _, events = self._stream(
                "/api/bypass/rce/stream", {"cmd": "id", "interactive": False}
            )
        for ev in (e for e in events if e.get("type") == "log"):
            self.assertIn("text", ev, f"Log event missing 'text': {ev}")

    # ------------------------------------------------------------------ SSE streaming — READ

    def test_read_stream_returns_sse_content_type(self):
        with patch("Typhon.Typhon.bypassREAD", side_effect=SystemExit(0)):
            status, ctype, _ = self._stream(
                "/api/bypass/read/stream",
                {"filepath": "/flag", "RCE_method": "exec", "interactive": False},
            )
        self.assertEqual(status, 200)
        self.assertIn("text/event-stream", ctype)

    def test_read_stream_contains_done_event(self):
        with patch("Typhon.Typhon.bypassREAD", side_effect=SystemExit(0)):
            _, _, events = self._stream(
                "/api/bypass/read/stream",
                {"filepath": "/flag", "RCE_method": "exec", "interactive": False},
            )
        self.assertIsNotNone(self._get_done(events))

    def test_read_stream_eval_method_accepted(self):
        with patch("Typhon.Typhon.bypassREAD", side_effect=SystemExit(0)):
            status, _, events = self._stream(
                "/api/bypass/read/stream", {
                    "filepath": "/flag",
                    "RCE_method": "eval",
                    "is_allow_exception_leak": True,
                    "interactive": False,
                },
            )
        self.assertEqual(status, 200)
        self.assertIsNotNone(self._get_done(events))

    def test_read_stream_exit0_success_true(self):
        with patch("Typhon.Typhon.bypassREAD", side_effect=SystemExit(0)):
            _, _, events = self._stream(
                "/api/bypass/read/stream",
                {"filepath": "/etc/passwd", "RCE_method": "exec"},
            )
        self.assertTrue(self._get_done(events)["success"])

    def test_read_stream_exception_produces_error(self):
        with patch("Typhon.Typhon.bypassREAD", side_effect=ValueError("no gadget")):
            _, _, events = self._stream(
                "/api/bypass/read/stream",
                {"filepath": "/flag", "RCE_method": "exec"},
            )
        done = self._get_done(events)
        self.assertFalse(done["success"])
        self.assertIn("no gadget", done.get("error", ""))

    def test_read_stream_params_forwarded(self):
        received = {}

        def capture_read(**kwargs):
            received.update(kwargs)
            raise SystemExit(0)

        with patch("Typhon.Typhon.bypassREAD", side_effect=capture_read):
            self._stream("/api/bypass/read/stream", {
                "filepath": "/etc/shadow",
                "RCE_method": "eval",
                "is_allow_exception_leak": True,
                "interactive": False,
                "banned_chr": '["open", "__"]',
            })
        self.assertEqual(received.get("filepath"), "/etc/shadow")
        self.assertEqual(received.get("RCE_method"), "eval")
        self.assertTrue(received.get("is_allow_exception_leak"))
        self.assertFalse(received.get("interactive"))
        self.assertEqual(received.get("banned_chr"), ["open", "__"])

    def test_read_stream_stdout_captured_as_log_event(self):
        def fake_read(**kwargs):
            print("read-test-output-marker-abc")
            raise SystemExit(0)

        with patch("Typhon.Typhon.bypassREAD", side_effect=fake_read):
            _, _, events = self._stream(
                "/api/bypass/read/stream",
                {"filepath": "/flag", "RCE_method": "exec"},
            )
        log_texts = [e.get("text", "") for e in events if e.get("type") == "log"]
        self.assertTrue(
            any("read-test-output-marker-abc" in t for t in log_texts),
            f"Marker not found in log events: {log_texts}",
        )


if __name__ == "__main__":
    import __main__
    buf = io.StringIO()
    _real_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        runner = unittest.TextTestRunner(stream=buf, verbosity=0)
        result = runner.run(unittest.TestLoader().loadTestsFromModule(__main__))
    finally:
        sys.stdout = _real_stdout
    if not result.wasSuccessful():
        print(buf.getvalue(), end="")
        sys.exit(1)
