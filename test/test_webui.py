import os
import sys
import io
import json
import queue
import threading
import logging
import http.client
import unittest
from unittest.mock import patch

# Set up path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging
logging.basicConfig(handlers=[logging.NullHandler()], force=True)

from Typhon.webui_module.app import (
    _strip_ansi, _parse_list, _parse_ast, _common_params,
    _QueueWriter, _QueueLogHandler, run
)

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


# ---------------------------------------------------------------------------
# TestParseAst
# ---------------------------------------------------------------------------

class TestParseAst(unittest.TestCase):
    def test_valid_nodes_without_prefix(self):
        import ast
        self.assertEqual(
            _parse_ast(["Import", "Call", "Attribute"]),
            [ast.Import, ast.Call, ast.Attribute],
        )

    def test_ast_prefix_stripped(self):
        import ast
        self.assertEqual(_parse_ast(["ast.Import"]), [ast.Import])

    def test_mixed_prefix(self):
        import ast
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
        result = _common_params({"banned_re": '[\".*import.*\"]'})
        self.assertEqual(result["banned_re"], [".*import.*"])

    def test_banned_ast_nodes(self):
        import ast
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


# ---------------------------------------------------------------------------
# TestWebUIFunction
# ---------------------------------------------------------------------------

class TestWebUIFunction(unittest.TestCase):
    def test_webui_import(self):
        from Typhon import webui
        self.assertIsNotNone(webui)

    @patch('Typhon.webui_module.app.run')
    def test_webui_calls_run(self, mock_run):
        from Typhon import webui
        webui(host="127.0.0.1", port=8080, use_current_scope=False)
        mock_run.assert_called_once_with(host="127.0.0.1", port=8080, injected_scope=None)


if __name__ == "__main__":
    unittest.main()
