"""The inference key cannot become a Jupyter management credential."""
import asyncio
import io
import json
from pathlib import Path
import tempfile
from unittest.mock import AsyncMock, patch

from tornado.httpclient import HTTPRequest, HTTPResponse
from tornado.httputil import HTTPHeaders
from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application

from ai.tools.analysis_jupyter_bridge import AnalysisBridge, MAX_BYTES, UPSTREAM

KEY = "synthetic-analysis-key-for-test-only"
ROUTE = "/cocolon-analysis/v1/chat/completions"


class BridgeTests(AsyncHTTPTestCase):
    def setUp(self):
        self.files = tempfile.TemporaryDirectory()
        self.key_path = Path(self.files.name) / "analysis.env"
        self.key_path.write_text("COCOLON_ANALYSIS_MODEL_API_KEY=" + KEY + "\n")
        self.key_path.chmod(0o600)
        super().setUp()

    def tearDown(self):
        super().tearDown()
        self.files.cleanup()

    def get_app(self):
        return Application([(ROUTE, AnalysisBridge, {"key_path": str(self.key_path)})],
                           xsrf_cookies=True)

    def request(self, body=b"{}", **kwargs):
        return self.fetch(ROUTE, method="POST", body=body,
            headers={"Authorization": "Bearer " + KEY, **kwargs.pop("headers", {})}, **kwargs)

    def test_exact_bearer_passes_original_body_without_cookies_or_redirects(self):
        reply = HTTPResponse(HTTPRequest(UPSTREAM), 200, buffer=io.BytesIO(b'{"ok":true}'),
            headers=HTTPHeaders({"Set-Cookie": "must-not-forward=1"}))
        with patch("ai.tools.analysis_jupyter_bridge.AsyncHTTPClient") as client:
            client.return_value.fetch = AsyncMock(return_value=reply)
            response = self.request(b'{"messages":["synthetic"]}', headers={"Cookie": "jupyter=synthetic"})
            sent = client.return_value.fetch.call_args.args[0]
        assert response.code == 200 and response.body == b'{"ok":true}'
        assert sent.url == UPSTREAM and sent.body == b'{"messages":["synthetic"]}'
        assert sent.headers.get("Cookie") is None and not sent.follow_redirects
        assert sent.headers["Authorization"] == "Bearer " + KEY
        assert "Set-Cookie" not in response.headers

    def test_missing_wrong_key_or_jupyter_cookie_never_calls_upstream(self):
        for headers in ({}, {"Authorization": "Bearer wrong"}, {"Cookie": "jupyter=synthetic"}):
            with patch("ai.tools.analysis_jupyter_bridge.AsyncHTTPClient") as client:
                response = self.fetch(ROUTE, method="POST", body=b"{}", headers=headers)
            assert response.code == 401 and "Set-Cookie" not in response.headers
            client.assert_not_called()

    def test_get_is_not_a_management_or_health_endpoint(self):
        response = self.fetch(ROUTE, headers={"Authorization": "Bearer " + KEY})
        assert response.code == 405 and "Set-Cookie" not in response.headers

    def test_empty_and_oversized_body_are_rejected_before_upstream(self):
        for body in (b"", b"x" * (MAX_BYTES + 1)):
            with patch("ai.tools.analysis_jupyter_bridge.AsyncHTTPClient") as client:
                response = self.request(body)
            assert response.code == 413
            client.assert_not_called()

    def test_unavailable_model_fails_without_forwarding_exception_or_cookie(self):
        with patch("ai.tools.analysis_jupyter_bridge.AsyncHTTPClient") as client:
            client.return_value.fetch = AsyncMock(side_effect=RuntimeError("private upstream text"))
            response = self.request()
        assert response.code == 503 and b"private upstream text" not in response.body
        assert "Set-Cookie" not in response.headers

    def test_slow_model_sends_progress_before_exact_json_without_cookie(self):
        chunks = []
        async def delayed(*args, **kwargs):
            await asyncio.sleep(0.04)
            assert chunks and all(chunk == b" " for chunk in chunks)
            return HTTPResponse(HTTPRequest(UPSTREAM), 200,
                buffer=io.BytesIO(b'{"choices":[{"message":{"content":"unchanged"}}]}'))
        with patch("ai.tools.analysis_jupyter_bridge.AsyncHTTPClient") as client, \
                patch("ai.tools.analysis_jupyter_bridge.HEARTBEAT_SECONDS", 0.01):
            client.return_value.fetch = AsyncMock(side_effect=delayed)
            response = self.request(streaming_callback=chunks.append)
        assert response.code == 200 and len(chunks) > 1
        assert json.loads(b"".join(chunks))["choices"][0]["message"]["content"] == "unchanged"
        assert "Set-Cookie" not in response.headers

    def test_failure_after_progress_stays_explicit_error_without_private_text(self):
        async def delayed(*args, **kwargs):
            await asyncio.sleep(0.03)
            raise RuntimeError("private upstream text")
        with patch("ai.tools.analysis_jupyter_bridge.AsyncHTTPClient") as client, \
                patch("ai.tools.analysis_jupyter_bridge.HEARTBEAT_SECONDS", 0.01):
            client.return_value.fetch = AsyncMock(side_effect=delayed)
            response = self.request()
        assert response.body.startswith(b" ") and b"private upstream text" not in response.body
        assert json.loads(response.body) == {"error": "analysis_bridge_unavailable", "status": 503}
        assert "Set-Cookie" not in response.headers
