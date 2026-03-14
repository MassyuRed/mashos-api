from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional


def extract_client_meta(headers: Mapping[str, str]) -> dict:
    def _get(name: str) -> Optional[str]:
        try:
            value = headers.get(name)
        except Exception:
            value = None
        value = str(value or "").strip()
        return value or None

    return {
        "app_version": _get("X-App-Version"),
        "app_build": _get("X-App-Build"),
        "platform": _get("X-Platform"),
    }


def pick_first_present(payload: dict, keys: Iterable[str], default=None):
    if not isinstance(payload, dict):
        return default
    for key in keys:
        if key in payload:
            return payload.get(key)
    return default


def normalize_optional_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, (list, tuple)):
        return []

    out: list[str] = []
    seen = set()
    for item in value:
        s = str(item or "").strip()
        if not s or s in seen:
            continue
        out.append(s)
        seen.add(s)
    return out


def normalize_optional_bool(value: Any, default=None):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    s = str(value).strip().lower()
    if s in {"1", "true", "yes", "on"}:
        return True
    if s in {"0", "false", "no", "off"}:
        return False
    return default
