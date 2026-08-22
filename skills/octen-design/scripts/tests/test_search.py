"""Regression tests for skills/octen-design/scripts/search.py.

Runs the real script (imported as a module) against a local mock HTTP server.
No mocks of the code under test — only the remote API is simulated.
Stdlib only, no network access:  python3 tests/test_search.py
"""

import base64
import contextlib
import io
import json
import os
import shutil
import socket
import sys
import tempfile
import threading
import types
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
import search  # noqa: E402

TINY_PNG = base64.b64decode(
    b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


class MockHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

    def log_message(self, *args):
        pass

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            self.server.requests.append(json.loads(body))
        except ValueError:
            self.server.requests.append(body)
        script = self.server.api_script
        step = script.pop(0) if script else {"status": 200, "json": {"data": {"results": []}}}
        status = step.get("status", 200)
        payload = json.dumps(step["json"]).encode() if "json" in step else step.get("body", b"")
        try:
            if step.get("truncate"):
                # Promise more bytes than we send, then drop the connection:
                # the client's read() raises http.client.IncompleteRead.
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload) + 90))
                self.end_headers()
                self.wfile.write(payload[:10] or b"0123456789")
                self.wfile.flush()
                self.connection.close()
                return
            self.send_response(status)
            self.send_header("Content-Type", step.get("ctype", "application/json"))
            for k, v in step.get("headers", {}).items():
                self.send_header(k, v)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_GET(self):
        if self.path.startswith("/img/ok"):
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(TINY_PNG)))
            self.end_headers()
            self.wfile.write(TINY_PNG)
        elif self.path in self.server.redirect_targets:
            self.send_response(302)
            self.send_header("Location", self.server.redirect_targets[self.path])
            self.send_header("Content-Length", "0")
            self.end_headers()
        else:
            self.send_response(404)
            self.send_header("Content-Length", "0")
            self.end_headers()


class SearchScriptTest(unittest.TestCase):
    def setUp(self):
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), MockHandler)
        self.server.api_script = []
        self.server.requests = []
        self.server.redirect_targets = {}
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"

        self._old_api_url = search.API_URL
        search.API_URL = f"{self.base}/api"
        os.environ["OCTEN_API_KEY"] = "test-key"

        self.sleeps = []
        self._old_time = search.time
        search.time = types.SimpleNamespace(sleep=self.sleeps.append)

        self.out = tempfile.mkdtemp(prefix="uirefs-test-")

    def tearDown(self):
        search.API_URL = self._old_api_url
        search.time = self._old_time
        self.server.shutdown()
        self.server.server_close()
        shutil.rmtree(self.out, ignore_errors=True)

    # ---- helpers ----

    def good_response(self, n=1, **extra):
        results = []
        for i in range(n):
            r = {"url": f"{self.base}/img/ok.png", "title": f"hit {i}",
                 "source_page": "https://example.com", "html_snippet": "<div>x</div>"}
            r.update(extra)
            results.append(r)
        return {"status": 200, "json": {"code": 0, "data": {"results": results}}}

    def run_main(self, argv):
        old_argv = sys.argv
        sys.argv = ["search.py"] + argv + ["--out", self.out]
        stdout, stderr = io.StringIO(), io.StringIO()
        exc = None
        try:
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                try:
                    search.main()
                except SystemExit as e:
                    exc = e
        finally:
            sys.argv = old_argv
        return exc, stdout.getvalue(), stderr.getvalue()

    def manifest(self):
        return json.loads((Path(self.out) / "results.json").read_text(encoding="utf-8"))

    # ---- call_api robustness ----

    def test_non_json_body_becomes_topic_error_not_crash(self):
        """200 + HTML body on one topic must not crash the run or lose the other topic."""
        self.server.api_script = [
            {"status": 200, "body": b"<html>gateway error</html>", "ctype": "text/html"},
            self.good_response(2),
        ]
        exc, out, err = self.run_main(["dashboard", "--topics", "design", "general"])
        self.assertIsNone(exc, "run must survive a non-JSON body on one topic")
        m = self.manifest()
        self.assertEqual(len(m["octen_refs"]), 2)
        self.assertIn("design", m["topic_errors"])
        self.assertTrue(m["partial"])

    def test_read_phase_failure_is_retried(self):
        """A truncated response body (IncompleteRead) is transient: retry, then succeed."""
        self.server.api_script = [
            {"status": 200, "truncate": True, "json": {"code": 0}},
            self.good_response(1),
        ]
        exc, out, err = self.run_main(["dashboard", "--topics", "design"])
        self.assertIsNone(exc)
        m = self.manifest()
        self.assertEqual(len(m["octen_refs"]), 1)
        self.assertEqual(m["topic_errors"], {})
        self.assertFalse(m["partial"])
        self.assertEqual(len(self.server.requests), 2, "failed read must be retried")

    def test_retry_attempts_are_logged(self):
        self.server.api_script = [
            {"status": 500, "json": {"msg": "boom"}},
            {"status": 500, "json": {"msg": "boom"}},
            self.good_response(1),
        ]
        exc, out, err = self.run_main(["dashboard", "--topics", "design"])
        self.assertIsNone(exc)
        self.assertEqual(len(self.server.requests), 3)
        self.assertGreaterEqual(err.count("retrying in"), 2,
                                f"each failed attempt must be logged to stderr, got: {err!r}")

    # ---- partial / total failure semantics ----

    def test_all_failed_duplicate_topics_exit_nonzero(self):
        """--topics general general with every call 403 must NOT exit 0 with 'NO RESULTS'."""
        self.server.api_script = [
            {"status": 403, "json": {"msg": "no beta access"}},
            {"status": 403, "json": {"msg": "no beta access"}},
        ]
        exc, out, err = self.run_main(["dashboard", "--topics", "general", "general"])
        self.assertIsNotNone(exc, "total failure must exit non-zero")
        self.assertNotEqual(exc.code, 0)
        self.assertNotIn("NO RESULTS", out,
                         "a total auth failure must not be presented as an empty query")

    def test_partial_failure_recorded_in_manifest_and_report(self):
        self.server.api_script = [
            {"status": 403, "json": {"msg": "no beta access"}},
            self.good_response(1),
        ]
        exc, out, err = self.run_main(["dashboard", "--topics", "design", "general"])
        self.assertIsNone(exc, "partial success still exits 0")
        m = self.manifest()
        self.assertTrue(m["partial"])
        self.assertIn("design", m["topic_errors"])
        self.assertIn("403", m["topic_errors"]["design"])
        self.assertEqual(len(m["octen_refs"]), 1)
        self.assertIn("FAILED", out, "the report must mark the failed topic as failed, not empty")

    def test_all_failed_overwrites_stale_manifest(self):
        stale = {"query": "OLD", "topics": ["design"], "octen_refs": [{"title": "stale"}]}
        (Path(self.out) / "results.json").write_text(json.dumps(stale), encoding="utf-8")
        self.server.api_script = [{"status": 403, "json": {"msg": "no beta access"}}]
        exc, out, err = self.run_main(["dashboard", "--topics", "design"])
        self.assertIsNotNone(exc)
        self.assertNotEqual(exc.code, 0)
        m = self.manifest()
        self.assertEqual(m["query"], "dashboard", "stale manifest from a previous run must be replaced")
        self.assertEqual(m["octen_refs"], [])
        self.assertIn("design", m["topic_errors"])

    def test_unexpected_envelope_is_a_topic_error(self):
        """A 200 whose body has no 'data' object is an API contract problem, not zero hits."""
        self.server.api_script = [{"status": 200, "json": {"foo": 1}}]
        exc, out, err = self.run_main(["dashboard", "--topics", "design"])
        self.assertIsNotNone(exc, "an envelope mismatch with no results at all must exit non-zero")
        m = self.manifest()
        self.assertIn("design", m["topic_errors"])
        self.assertNotIn("NO RESULTS", out)

    # ---- download / snippet resilience ----

    def test_download_failure_reason_recorded(self):
        self.server.api_script = [self.good_response(1, url=f"{self.base}/img/missing.png")]
        # no thumbnail: remove it if present, and point url at a 404
        self.server.api_script[0]["json"]["data"]["results"][0].pop("thumbnail", None)
        exc, out, err = self.run_main(["dashboard", "--topics", "design"])
        self.assertIsNone(exc)
        ref = self.manifest()["octen_refs"][0]
        self.assertIsNone(ref["local_image"])
        self.assertTrue(ref.get("image_error"),
                        "the manifest must say WHY the image is missing")
        self.assertIn("download", err.lower(), "download failures must be visible on stderr")

    def test_bad_snippet_type_does_not_kill_the_run(self):
        self.server.api_script = [self.good_response(1, html_snippet={"unexpected": "dict"})]
        exc, out, err = self.run_main(["dashboard", "--topics", "design"])
        self.assertIsNone(exc, "a malformed html_snippet must not crash the whole run")
        ref = self.manifest()["octen_refs"][0]
        self.assertIsNone(ref["html_snippet_file"])
        self.assertTrue(ref.get("snippet_error"))

    def test_redirect_to_ftp_is_not_followed(self):
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        listener.settimeout(3)
        ftp_port = listener.getsockname()[1]
        connected = threading.Event()

        def accept():
            try:
                conn, _ = listener.accept()
                connected.set()
                conn.close()
            except socket.timeout:
                pass

        t = threading.Thread(target=accept, daemon=True)
        t.start()
        self.server.redirect_targets["/redir/ftp"] = f"ftp://127.0.0.1:{ftp_port}/x.png"
        result = search.download_image(f"{self.base}/redir/ftp", Path(self.out) / "x")
        path = result[0] if isinstance(result, tuple) else result
        self.assertIsNone(path)
        t.join(4)
        listener.close()
        self.assertFalse(connected.is_set(),
                         "a redirect to a non-http(s) scheme must not be followed")

    # ---- input validation against the official contract ----

    def test_count_out_of_range_rejected_locally(self):
        """OpenAPI: /image-search count is 1-10. --count 50 must fail before any API call."""
        self.server.api_script = [self.good_response(1)]
        exc, out, err = self.run_main(["dashboard", "--topics", "design", "--count", "50"])
        self.assertIsNotNone(exc, "--count 50 must be rejected")
        self.assertNotEqual(exc.code, 0)
        self.assertEqual(len(self.server.requests), 0, "no API call may be made with an invalid count")

    def test_local_image_checked_against_encoded_size(self):
        """OpenAPI: image data is 'at most 5MB after encoding'. A 4MB raw file encodes to ~5.3MB."""
        f = Path(self.out) / "big.png"
        f.write_bytes(b"\x00" * (4 * 1024 * 1024))
        with self.assertRaises(SystemExit) as ctx:
            search.image_input(str(f))
        self.assertIn("base64", str(ctx.exception.code).lower())

    def test_uppercase_scheme_image_url_is_a_url_not_a_path(self):
        entry = search.image_input("HTTPS://example.com/a.png")
        self.assertEqual(entry, {"type": "image", "url": "HTTPS://example.com/a.png"})

    def test_query_plus_image_rejected_single_input_contract(self):
        """OpenAPI + live: /image-search accepts exactly ONE input; text+image 400s server-side."""
        f = Path(self.out) / "small.png"
        f.write_bytes(TINY_PNG)
        exc, out, err = self.run_main(["dashboard", "--image", str(f), "--topics", "design"])
        self.assertIsNotNone(exc, "query + --image must be rejected locally (API accepts one input)")
        self.assertNotEqual(exc.code, 0)
        self.assertEqual(len(self.server.requests), 0)

    def test_image_only_sends_single_image_input(self):
        f = Path(self.out) / "small.png"
        f.write_bytes(TINY_PNG)
        self.server.api_script = [self.good_response(1)]
        exc, out, err = self.run_main(["--image", str(f), "--topics", "design"])
        self.assertIsNone(exc)
        inputs = self.server.requests[0]["inputs"]
        self.assertEqual(len(inputs), 1)
        self.assertEqual(inputs[0]["type"], "image")

    # ---- filename safety ----

    def test_distinct_topics_do_not_collide_after_slugify(self):
        self.assertNotEqual(search.safe_topic_slug("a b"), search.safe_topic_slug("a_b"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
