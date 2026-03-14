from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

JST = timezone(timedelta(hours=9))
PUBLISH_READY_STATUSES = frozenset({"READY", "PUBLISHED"})
ALLOWED_TIER_VALUES = frozenset({"free", "plus", "premium"})


def normalize_content_json(raw: Any) -> Dict[str, Any]:
    if isinstance(raw, dict):
        return dict(raw)
    if isinstance(raw, str):
        try:
            data = json.loads(raw)
        except Exception:
            return {}
        return dict(data) if isinstance(data, dict) else {}
    return {}


def normalize_tier_str(raw: Any) -> str:
    tier = str(raw or "").strip().lower()
    return tier if tier in ALLOWED_TIER_VALUES else "free"


def parse_iso_utc(value: Any) -> Optional[datetime]:
    s = str(value or "").strip()
    if not s:
        return None
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _to_utc_iso_z(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    dt = value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def extract_publish_meta(content_json: Any) -> Dict[str, Any]:
    cj = normalize_content_json(content_json)
    publish = cj.get("publish")
    return dict(publish) if isinstance(publish, dict) else {}


def extract_publish_status(content_json: Any) -> str:
    publish = extract_publish_meta(content_json)
    return str(publish.get("status") or "").strip().upper()


def is_ready_or_published_status(status: Any) -> bool:
    return str(status or "").strip().upper() in PUBLISH_READY_STATUSES


def _extract_myweb_metrics_total_all(content_json: Any) -> int:
    cj = normalize_content_json(content_json)

    metrics = cj.get("metrics") if isinstance(cj.get("metrics"), dict) else {}
    try:
        total_all = int(metrics.get("totalAll") or 0)
    except Exception:
        total_all = 0
    if total_all > 0:
        return total_all

    standard = cj.get("standardReport") if isinstance(cj.get("standardReport"), dict) else {}
    std_metrics = standard.get("metrics") if isinstance(standard.get("metrics"), dict) else {}
    try:
        std_total_all = int(std_metrics.get("totalAll") or 0)
    except Exception:
        std_total_all = 0
    if std_total_all > 0:
        return std_total_all

    return 0


def myweb_report_has_visible_content(content_json: Any) -> bool:
    return _extract_myweb_metrics_total_all(content_json) > 0


def myweb_daily_has_visible_content(content_json: Any) -> bool:
    return myweb_report_has_visible_content(content_json)


def _month_boundaries(now_utc: datetime) -> Dict[str, datetime]:
    now_jst = now_utc.astimezone(JST)
    cur_month_start_jst = datetime(now_jst.year, now_jst.month, 1, tzinfo=JST)
    if now_jst.month == 1:
        prev_year, prev_month = now_jst.year - 1, 12
    else:
        prev_year, prev_month = now_jst.year, now_jst.month - 1
    prev_month_start_jst = datetime(prev_year, prev_month, 1, tzinfo=JST)
    if cur_month_start_jst.month == 12:
        next_year, next_month = cur_month_start_jst.year + 1, 1
    else:
        next_year, next_month = cur_month_start_jst.year, cur_month_start_jst.month + 1
    next_month_start_jst = datetime(next_year, next_month, 1, tzinfo=JST)
    return {
        "prev_month_start_utc": prev_month_start_jst.astimezone(timezone.utc),
        "cur_month_start_utc": cur_month_start_jst.astimezone(timezone.utc),
        "next_month_start_utc": next_month_start_jst.astimezone(timezone.utc),
    }


def history_retention_window_utc(tier_str: Any, now_utc: Optional[datetime] = None) -> Dict[str, Any]:
    tier = normalize_tier_str(tier_str)
    now = (now_utc or datetime.now(timezone.utc)).astimezone(timezone.utc)

    if tier == "premium":
        return {
            "tier": tier,
            "mode": "unlimited",
            "start_utc": None,
            "end_utc_exclusive": None,
        }

    if tier == "plus":
        return {
            "tier": tier,
            "mode": "rolling_365d",
            "start_utc": now - timedelta(days=365),
            # query-side uses lt, so keep a tiny exclusive cushion
            "end_utc_exclusive": now + timedelta(milliseconds=1),
        }

    bounds = _month_boundaries(now)
    return {
        "tier": tier,
        "mode": "current_and_previous_month_jst",
        "start_utc": bounds["prev_month_start_utc"],
        "end_utc_exclusive": bounds["next_month_start_utc"],
    }


def timestamp_in_history_retention(value: Any, tier_str: Any, now_utc: Optional[datetime] = None) -> bool:
    ts = parse_iso_utc(value)
    if ts is None:
        return False
    window = history_retention_window_utc(tier_str, now_utc=now_utc)
    start = window.get("start_utc")
    end = window.get("end_utc_exclusive")
    if isinstance(start, datetime) and ts < start:
        return False
    if isinstance(end, datetime) and ts >= end:
        return False
    return True


def history_retention_bounds_for_query(tier_str: Any, now_utc: Optional[datetime] = None) -> Dict[str, Any]:
    window = history_retention_window_utc(tier_str, now_utc=now_utc)
    start = window.get("start_utc")
    end = window.get("end_utc_exclusive")
    return {
        "tier": window.get("tier") or normalize_tier_str(tier_str),
        "mode": str(window.get("mode") or "unlimited"),
        "gte_iso": _to_utc_iso_z(start) if isinstance(start, datetime) else None,
        "lt_iso": _to_utc_iso_z(end) if isinstance(end, datetime) else None,
    }


def myweb_retention_ok(period_end_iso: Any, tier_str: Any, *, now_utc: Optional[datetime] = None) -> bool:
    return timestamp_in_history_retention(period_end_iso, tier_str, now_utc=now_utc)


def decide_myweb_report_publish(
    row: Any,
    *,
    tier_str: Any = "free",
    requested_report_type: Optional[str] = None,
    now_utc: Optional[datetime] = None,
) -> Optional[Dict[str, Any]]:
    if not isinstance(row, dict):
        return None

    out = dict(row)
    report_type = str(out.get("report_type") or "").strip().lower()
    requested = str(requested_report_type or "").strip().lower()
    if requested and report_type != requested:
        return None

    content_json = normalize_content_json(out.get("content_json"))
    if not is_ready_or_published_status(extract_publish_status(content_json)):
        return None
    if not myweb_report_has_visible_content(content_json):
        return None
    if not myweb_retention_ok(out.get("period_end"), tier_str, now_utc=now_utc):
        return None

    out["content_json"] = content_json
    return out


def myprofile_report_has_visible_content(row: Any) -> bool:
    if not isinstance(row, dict):
        return False
    if str(row.get("content_text") or "").strip():
        return True
    return bool(normalize_content_json(row.get("content_json")))


def myprofile_report_retention_ok(period_end_iso: Any, tier_str: Any, *, now_utc: Optional[datetime] = None) -> bool:
    return timestamp_in_history_retention(period_end_iso, tier_str, now_utc=now_utc)


def decide_myprofile_report_publish(
    row: Any,
    *,
    requested_report_type: Optional[str] = None,
    tier_str: Optional[Any] = None,
    now_utc: Optional[datetime] = None,
) -> Optional[Dict[str, Any]]:
    if not isinstance(row, dict):
        return None

    out = dict(row)
    report_type = str(out.get("report_type") or "").strip()
    requested = str(requested_report_type or "").strip()
    if requested and report_type != requested:
        return None
    if not report_type:
        return None

    out["content_json"] = normalize_content_json(out.get("content_json"))
    if not myprofile_report_has_visible_content(out):
        return None
    if tier_str is not None and not myprofile_report_retention_ok(out.get("period_end"), tier_str, now_utc=now_utc):
        return None
    return out
