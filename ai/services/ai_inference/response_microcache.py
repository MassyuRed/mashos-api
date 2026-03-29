from __future__ import annotations

import asyncio
import copy
import hashlib
import json
import os
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Optional

from request_metrics import record_cache_coalesced, record_cache_hit, record_cache_miss


JsonProducer = Callable[[], Awaitable[Any]]
TtlResolver = Callable[[Any], float]


@dataclass
class CacheEntry:
    value: Any
    expires_at: float


_ENABLED = (os.getenv("RESPONSE_MICROCACHE_ENABLED", "true").strip().lower() != "false")
try:
    _MAX_ITEMS = int(os.getenv("RESPONSE_MICROCACHE_MAX_ITEMS", "1024") or "1024")
except Exception:
    _MAX_ITEMS = 1024
_MAX_ITEMS = max(64, _MAX_ITEMS)

_cache: "OrderedDict[str, CacheEntry]" = OrderedDict()
_inflight: Dict[str, asyncio.Future] = {}
_lock = asyncio.Lock()


def _namespace_for_key(key: str) -> str:
    raw = str(key or "").strip()
    if not raw:
        return "microcache"
    return raw.split(":", 1)[0] or "microcache"


def build_cache_key(prefix: str, payload: Optional[Dict[str, Any]] = None) -> str:
    base = str(prefix or "").strip().rstrip(":")
    if not payload:
        return base
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]
    return f"{base}:{digest}"


def _trim_unlocked(now_ts: float) -> None:
    expired = [key for key, entry in list(_cache.items()) if float(entry.expires_at) <= now_ts]
    for key in expired:
        _cache.pop(key, None)
    while len(_cache) > _MAX_ITEMS:
        try:
            _cache.popitem(last=False)
        except Exception:
            break


async def get_or_compute(
    key: str,
    ttl_seconds: float,
    producer: JsonProducer,
    *,
    ttl_resolver: Optional[TtlResolver] = None,
) -> Any:
    if not _ENABLED:
        record_cache_miss(_namespace_for_key(key))
        return await producer()

    cache_key = str(key or "").strip()
    if not cache_key:
        record_cache_miss("microcache")
        return await producer()

    namespace = _namespace_for_key(cache_key)
    now_ts = time.monotonic()

    async with _lock:
        entry = _cache.get(cache_key)
        if entry is not None and float(entry.expires_at) > now_ts:
            try:
                _cache.move_to_end(cache_key)
            except Exception:
                pass
            record_cache_hit(namespace)
            return copy.deepcopy(entry.value)
        if entry is not None:
            _cache.pop(cache_key, None)

        fut = _inflight.get(cache_key)
        if fut is not None:
            record_cache_coalesced(namespace)
            wait_future = fut
        else:
            record_cache_miss(namespace)
            wait_future = None
            loop = asyncio.get_running_loop()
            fut = loop.create_future()
            _inflight[cache_key] = fut

    if wait_future is not None:
        result = await wait_future
        return copy.deepcopy(result)

    try:
        value = await producer()
        ttl_value = float(ttl_seconds or 0.0)
        if ttl_resolver is not None:
            try:
                ttl_value = float(ttl_resolver(value) or 0.0)
            except Exception:
                ttl_value = float(ttl_seconds or 0.0)
        if ttl_value > 0:
            expires_at = time.monotonic() + ttl_value
            async with _lock:
                _cache[cache_key] = CacheEntry(value=copy.deepcopy(value), expires_at=expires_at)
                try:
                    _cache.move_to_end(cache_key)
                except Exception:
                    pass
                _trim_unlocked(time.monotonic())
        fut.set_result(copy.deepcopy(value))
        return value
    except Exception as exc:
        fut.set_exception(exc)
        raise
    finally:
        async with _lock:
            if _inflight.get(cache_key) is fut:
                _inflight.pop(cache_key, None)


async def invalidate_exact(key: str) -> int:
    cache_key = str(key or "").strip()
    if not cache_key:
        return 0
    async with _lock:
        existed = 1 if cache_key in _cache else 0
        _cache.pop(cache_key, None)
        return existed


async def invalidate_prefix(prefix: str) -> int:
    prefix_s = str(prefix or "").strip()
    if not prefix_s:
        return 0
    async with _lock:
        keys = [key for key in list(_cache.keys()) if key.startswith(prefix_s)]
        for key in keys:
            _cache.pop(key, None)
        return len(keys)
