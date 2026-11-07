"""Model-key-only Analysis route on an existing Jupyter HTTP port.

Load through ServerApp.extra_services. This handler deliberately does not use
Jupyter's identity provider: a model key must never issue a Jupyter login cookie.
All other Jupyter routes keep their original authentication and XSRF settings.
"""
from __future__ import annotations

import hmac
import json
from pathlib import Path

from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado.web import HTTPError, RequestHandler, authenticated

UPSTREAM = "http://127.0.0.1:8000/v1/chat/completions"
MAX_BYTES = 262144


class AnalysisBridge(RequestHandler):
    def initialize(self, key_path="/workspace/analysis.env"):
        values = dict(line.strip().split("=", 1) for line in Path(key_path).read_text().splitlines()
                      if line.strip() and not line.lstrip().startswith("#"))
        self._key = values.get("COCOLON_ANALYSIS_MODEL_API_KEY", "")
        if len(self._key) < 24:
            raise RuntimeError("analysis_bridge_configuration_invalid")

    def _require_key(self):
        if not hmac.compare_digest(self.request.headers.get("Authorization", ""),
                                   "Bearer " + self._key):
            raise HTTPError(401)

    def get_current_user(self):
        self._require_key()
        return "analysis-model"

    def check_xsrf_cookie(self):
        # Only this dedicated machine route uses its separate bearer credential.
        # A Jupyter session cookie is never sufficient to call the model.
        self._require_key()

    def prepare(self):
        self._require_key()
        if self.request.method != "POST":
            raise HTTPError(405)
        if not 0 < len(self.request.body) <= MAX_BYTES:
            raise HTTPError(413)

    @authenticated
    async def post(self):
        try:
            response = await AsyncHTTPClient().fetch(HTTPRequest(UPSTREAM, method="POST",
                body=self.request.body, headers={"Authorization": "Bearer " + self._key,
                    "Content-Type": "application/json"}, follow_redirects=False,
                connect_timeout=3, request_timeout=215), raise_error=False)
        except Exception:
            raise HTTPError(503) from None
        self.set_status(response.code if 100 <= response.code <= 599 else 503)
        self.set_header("Content-Type", "application/json")
        self.set_header("Cache-Control", "no-store")
        # Do not forward cookies, redirect locations, or upstream credentials.
        self.finish(response.body)

    def write_error(self, status_code, **kwargs):
        self.set_header("Content-Type", "application/json")
        self.set_header("Cache-Control", "no-store")
        self.finish(json.dumps({"error": "analysis_bridge_unavailable", "status": status_code}))


default_handlers = [(r"/cocolon-analysis/v1/chat/completions", AnalysisBridge)]
