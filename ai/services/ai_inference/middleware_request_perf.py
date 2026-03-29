from __future__ import annotations

import logging
import os
import time
from uuid import uuid4

from fastapi import FastAPI, Request

from observability import log_event
from request_metrics import begin_request_metrics, finish_request_metrics, snapshot_request_metrics

logger = logging.getLogger("request_perf")

try:
    REQUEST_SLOW_LOG_THRESHOLD_MS = float(os.getenv("REQUEST_SLOW_LOG_THRESHOLD_MS", "700") or "700")
except Exception:
    REQUEST_SLOW_LOG_THRESHOLD_MS = 700.0

LOG_ALL_REQUESTS = (os.getenv("REQUEST_LOG_ALL", "false").strip().lower() in {"1", "true", "yes", "on"})


def install_request_perf_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def _request_perf_middleware(request: Request, call_next):
        request_id = str(getattr(request.state, "cocolon_request_id", "") or "").strip() or uuid4().hex[:12]
        token = begin_request_metrics(request_id, request.method, request.url.path)
        started = time.perf_counter()
        status_code = 500
        error_name = None

        try:
            response = await call_next(request)
            status_code = int(getattr(response, "status_code", 200) or 200)
            return response
        except Exception as exc:
            error_name = type(exc).__name__
            raise
        finally:
            wall_ms = (time.perf_counter() - started) * 1000.0
            metrics = snapshot_request_metrics()
            finish_request_metrics(token)

            should_log = (
                LOG_ALL_REQUESTS
                or wall_ms >= REQUEST_SLOW_LOG_THRESHOLD_MS
                or status_code >= 500
                or bool(error_name)
            )
            if should_log:
                fields = {
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": status_code,
                    "wall_ms": round(wall_ms, 2),
                    **(metrics or {}),
                }
                if error_name:
                    fields["error"] = error_name
                level = "warning" if (wall_ms >= REQUEST_SLOW_LOG_THRESHOLD_MS or status_code >= 500 or error_name) else "info"
                log_event(logger, "http_request_perf", level=level, **fields)
