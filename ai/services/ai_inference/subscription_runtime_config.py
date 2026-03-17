# -*- coding: utf-8 -*-
from __future__ import annotations

import os
from typing import Any, Dict, Iterable, List, Tuple

from subscription_config import get_subscription_config_audit_snapshot


def _bool_env(*names: str, default: bool = False) -> bool:
    for name in names:
        raw = os.getenv(name)
        if raw is None:
            continue
        return str(raw).strip().lower() in {"1", "true", "yes", "on"}
    return default


def enforce_subscription_env_if_requested() -> Dict[str, Any]:
    audit = get_subscription_config_audit_snapshot()
    strict = _bool_env(
        "COCOLON_IAP_ENFORCE_RUNTIME_CONFIG",
        "COCOLON_IAP_FAIL_FAST_ON_STARTUP",
        default=False,
    )
    if strict and (audit.get("warnings") or []):
        raise RuntimeError(" ; ".join(str(item) for item in (audit.get("warnings") or [])))
    return audit


def format_subscription_env_audit_lines(audit: Dict[str, Any]) -> List[Tuple[str, str]]:
    lines: List[Tuple[str, str]] = []
    ios = audit.get("ios") or {}
    android = audit.get("android") or {}
    frontend = audit.get("frontend_public") or {}

    lines.append((
        "info",
        f"[subscription.phase3] ios_ready={bool(ios.get('verification_ready'))} android_ready={bool(android.get('verification_ready'))}",
    ))
    lines.append((
        "info",
        f"[subscription.phase3] ios_bundle_id={ios.get('bundle_id') or '-'} android_package_name={android.get('package_name') or '-'}",
    ))

    if frontend.get("EXPO_PUBLIC_MYMODEL_API_URL"):
        lines.append((
            "info",
            f"[subscription.phase3] public_api_base={frontend.get('EXPO_PUBLIC_MYMODEL_API_URL')}",
        ))

    for warning in audit.get("warnings") or []:
        lines.append(("warning", f"[subscription.phase3] {warning}"))
    return lines
