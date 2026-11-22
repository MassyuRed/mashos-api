"""Model-key-only Analysis route on an existing Jupyter HTTP port.

Load through ServerApp.extra_services. This handler deliberately does not use
Jupyter's identity provider: a model key must never issue a Jupyter login cookie.
All other Jupyter routes keep their original authentication and XSRF settings.
"""
from __future__ import annotations

import asyncio
import hmac
import json
from pathlib import Path

from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado.iostream import StreamClosedError
from tornado.web import HTTPError, RequestHandler, authenticated

UPSTREAM = "http://127.0.0.1:8000/v1/chat/completions"
MAX_BYTES = 262144
HEARTBEAT_SECONDS = 20


class AnalysisBridge(RequestHandler):
    key_name = "COCOLON_ANALYSIS_MODEL_API_KEY"
    request_seconds = 215

    def initialize(self, key_path="/workspace/analysis.env"):
        values = dict(line.strip().split("=", 1) for line in Path(key_path).read_text().splitlines()
                      if line.strip() and not line.lstrip().startswith("#"))
        self._key = values.get(self.key_name, "")
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
        pending = None
        started = False
        try:
            pending = asyncio.ensure_future(AsyncHTTPClient().fetch(HTTPRequest(UPSTREAM, method="POST",
                body=self.request.body, headers={"Authorization": "Bearer " + self._key,
                    "Content-Type": "application/json"}, follow_redirects=False,
                connect_timeout=3, request_timeout=self.request_seconds), raise_error=False))
            while not pending.done():
                done, _ = await asyncio.wait({pending}, timeout=HEARTBEAT_SECONDS)
                if not done:
                    self.set_header("Content-Type", "application/json")
                    self.set_header("Cache-Control", "no-store")
                    # JSON permits leading whitespace. Flush progress without
                    # altering the eventual model content or its bound hash.
                    self.write(b" ")
                    await self.flush()
                    started = True
            response = await pending
        except StreamClosedError:
            return
        except Exception:
            if started:
                self.finish(json.dumps({"error": "analysis_bridge_unavailable", "status": 503}))
                return
            raise HTTPError(503) from None
        finally:
            if pending is not None and not pending.done():
                pending.cancel()
        if not started:
            self.set_status(response.code if 100 <= response.code <= 599 else 503)
        elif response.code != 200:
            self.finish(json.dumps({"error": "analysis_bridge_unavailable", "status": 503}))
            return
        self.set_header("Content-Type", "application/json")
        self.set_header("Cache-Control", "no-store")
        # Do not forward cookies, redirect locations, or upstream credentials.
        self.finish(response.body)

    def write_error(self, status_code, **kwargs):
        self.set_header("Content-Type", "application/json")
        self.set_header("Cache-Control", "no-store")
        self.finish(json.dumps({"error": "analysis_bridge_unavailable", "status": status_code}))


class NaturalReplyBridge(AnalysisBridge):
    key_name = "EMLIS_NATURAL_REPLY_API_KEY"
    request_seconds = 245

    def initialize(self, key_path="/workspace/natural-reply.env"):
        super().initialize(key_path=key_path)


default_handlers = [(r"/cocolon-analysis/v1/chat/completions", AnalysisBridge),
                    (r"/cocolon-emlis/v1/chat/completions", NaturalReplyBridge)]
