from __future__ import annotations

import contextvars
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Optional


@dataclass
class RequestMetrics:
    request_id: str
    method: str
    path: str
    started_monotonic: float = field(default_factory=time.monotonic)
    supabase_calls: int = 0
    supabase_errors: int = 0
    supabase_time_ms: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    cache_coalesced: int = 0
    extra: Dict[str, Any] = field(default_factory=dict)


_current_metrics: contextvars.ContextVar[Optional[RequestMetrics]] = contextvars.ContextVar(
    "cocolon_request_metrics",
    default=None,
)


def begin_request_metrics(request_id: str, method: str, path: str):
    metrics = RequestMetrics(
        request_id=str(request_id or "").strip(),
        method=str(method or "GET").upper(),
        path=str(path or "").strip() or "/",
    )
    return _current_metrics.set(metrics)


def finish_request_metrics(token) -> None:
    try:
        _current_metrics.reset(token)
    except Exception:
        _current_metrics.set(None)


def _get_metrics() -> Optional[RequestMetrics]:
    return _current_metrics.get()


def record_supabase_call(*, elapsed_ms: float, status_code: Optional[int] = None, error: Optional[str] = None) -> None:
    metrics = _get_metrics()
    if metrics is None:
        return
    metrics.supabase_calls += 1
    try:
        metrics.supabase_time_ms += max(0.0, float(elapsed_ms or 0.0))
    except Exception:
        pass
    if error or (status_code is not None and int(status_code) >= 400):
        metrics.supabase_errors += 1


def record_cache_hit(namespace: str) -> None:
    metrics = _get_metrics()
    if metrics is None:
        return
    metrics.cache_hits += 1
    if namespace:
        metrics.extra[f"cache_hit::{namespace}"] = int(metrics.extra.get(f"cache_hit::{namespace}") or 0) + 1


def record_cache_miss(namespace: str) -> None:
    metrics = _get_metrics()
    if metrics is None:
        return
    metrics.cache_misses += 1
    if namespace:
        metrics.extra[f"cache_miss::{namespace}"] = int(metrics.extra.get(f"cache_miss::{namespace}") or 0) + 1


def record_cache_coalesced(namespace: str) -> None:
    metrics = _get_metrics()
    if metrics is None:
        return
    metrics.cache_coalesced += 1
    if namespace:
        metrics.extra[f"cache_coalesced::{namespace}"] = int(metrics.extra.get(f"cache_coalesced::{namespace}") or 0) + 1


def set_metric(name: str, value: Any) -> None:
    metrics = _get_metrics()
    if metrics is None:
        return
    key = str(name or "").strip()
    if not key:
        return
    metrics.extra[key] = value


def snapshot_request_metrics() -> Dict[str, Any]:
    metrics = _get_metrics()
    if metrics is None:
        return {}
    payload = asdict(metrics)
    payload["supabase_time_ms"] = round(float(payload.get("supabase_time_ms") or 0.0), 2)
    payload.pop("started_monotonic", None)
    extra = payload.pop("extra", None) or {}
    payload.update(extra)
    return payload
