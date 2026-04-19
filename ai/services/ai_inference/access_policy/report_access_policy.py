from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from publish_governance import (
    decide_myprofile_report_publish,
    decide_myweb_report_publish,
    history_retention_bounds_for_query,
    normalize_tier_str,
)


def build_history_retention(tier_str: Any, *, now_utc: Optional[datetime] = None) -> Dict[str, Any]:
    now = (now_utc or datetime.now(timezone.utc)).astimezone(timezone.utc)
    return history_retention_bounds_for_query(normalize_tier_str(tier_str), now_utc=now)


def apply_myweb_report_access(
    row: Dict[str, Any],
    *,
    tier_str: Any,
    requested_report_type: Optional[str] = None,
    now_utc: Optional[datetime] = None,
) -> Optional[Dict[str, Any]]:
    now = (now_utc or datetime.now(timezone.utc)).astimezone(timezone.utc)
    return decide_myweb_report_publish(
        row,
        tier_str=normalize_tier_str(tier_str),
        requested_report_type=(str(requested_report_type or "").strip() or None),
        now_utc=now,
    )


def apply_myprofile_report_access(
    row: Dict[str, Any],
    *,
    tier_str: Any,
    requested_report_type: Optional[str] = None,
    now_utc: Optional[datetime] = None,
) -> Optional[Dict[str, Any]]:
    now = (now_utc or datetime.now(timezone.utc)).astimezone(timezone.utc)
    kwargs = {
        "tier_str": normalize_tier_str(tier_str),
        "now_utc": now,
    }
    report_type = str(requested_report_type or "").strip()
    if report_type:
        kwargs["requested_report_type"] = report_type
    return decide_myprofile_report_publish(row, **kwargs)


__all__ = [
    "apply_myprofile_report_access",
    "apply_myweb_report_access",
    "build_history_retention",
]
