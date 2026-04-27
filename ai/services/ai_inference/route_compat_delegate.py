from __future__ import annotations

import inspect
from typing import Any, Dict, Tuple

from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder


def _fastapi_default_value(default: Any) -> Tuple[bool, Any]:
    if default is inspect.Signature.empty:
        return False, None
    if hasattr(default, "default"):
        nested_default = getattr(default, "default")
        if nested_default is not inspect.Signature.empty:
            return True, nested_default
    return True, default


def find_registered_route_endpoint(app: FastAPI, *, path: str, method: str = "GET"):
    target_path = str(path or "").strip()
    target_method = str(method or "GET").strip().upper()
    for route in getattr(app, "routes", []) or []:
        if str(getattr(route, "path", "") or "") != target_path:
            continue
        methods = {str(m or "").upper() for m in (getattr(route, "methods", set()) or set())}
        if target_method not in methods:
            continue
        endpoint = getattr(route, "endpoint", None)
        if endpoint is not None:
            return endpoint
    return None


async def call_registered_route_json(
    app: FastAPI,
    *,
    path: str,
    method: str = "GET",
    detail: str,
    **values: Any,
) -> Any:
    endpoint = find_registered_route_endpoint(app, path=path, method=method)
    if endpoint is None:
        raise HTTPException(status_code=502, detail=f"{detail}: route not registered")

    kwargs: Dict[str, Any] = {}
    try:
        signature = inspect.signature(endpoint)
    except Exception:
        signature = None

    if signature is not None:
        for name, param in signature.parameters.items():
            if name in values:
                kwargs[name] = values[name]
                continue
            has_default, default_value = _fastapi_default_value(param.default)
            if has_default:
                kwargs[name] = default_value
    else:
        kwargs = dict(values)

    try:
        result = endpoint(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return jsonable_encoder(result)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"{detail}: {exc}") from exc
