from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from publish_governance import decide_myweb_report_publish, normalize_content_json
from response_microcache import get_or_compute
from supabase_client import sb_get

try:
    from subscription import SubscriptionTier  # type: ignore
    from subscription_store import get_subscription_tier_for_user  # type: ignore
except Exception:  # pragma: no cover
    SubscriptionTier = None  # type: ignore
    get_subscription_tier_for_user = None  # type: ignore

ANALYSIS_SUMMARY_READER_CACHE_TTL_SECONDS = 10.0
EMOTION_KEYS = ("joy", "sadness", "anxiety", "anger", "calm")
KEY_TO_JP: Dict[str, str] = {
    "joy": "喜び",
    "sadness": "悲しみ",
    "anxiety": "不安",
    "anger": "怒り",
    "calm": "平穏",
}


def _coerce_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return int(default)
        if isinstance(value, bool):
            return int(value)
        return int(float(value))
    except Exception:
        return int(default)


def _coerce_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return float(default)
        if isinstance(value, bool):
            return float(int(value))
        return float(value)
    except Exception:
        return float(default)


async def _resolve_viewer_tier(user_id: str) -> str:
    tier_str = "free"
    if user_id and SubscriptionTier is not None and get_subscription_tier_for_user is not None:
        try:
            tier_enum = await get_subscription_tier_for_user(user_id, default=SubscriptionTier.FREE)
            tier_str = tier_enum.value if hasattr(tier_enum, "value") else str(tier_enum)
        except Exception:
            tier_str = "free"
    return str(tier_str or "free")


async def _fetch_latest_report_row(user_id: str, report_type: str, *, tier_str: str) -> Optional[Dict[str, Any]]:
    resp = await sb_get(
        "/rest/v1/myweb_reports",
        params={
            "select": "id,report_type,period_start,period_end,content_json,updated_at,generated_at,status,publish_status,title",
            "user_id": f"eq.{user_id}",
            "report_type": f"eq.{report_type}",
            "order": "period_end.desc,updated_at.desc,generated_at.desc",
            "limit": "20",
        },
        timeout=8.0,
    )
    if resp.status_code not in (200, 206):
        raise RuntimeError(f"Failed to load latest {report_type} MyWeb report")
    rows = resp.json() if hasattr(resp, "json") else []
    rows = rows if isinstance(rows, list) else []
    for row in rows:
        if not isinstance(row, dict):
            continue
        published_row = decide_myweb_report_publish(row, tier_str=tier_str, requested_report_type=report_type)
        if published_row:
            return published_row
    return None


def _pick_standard_report(content_json: Dict[str, Any]) -> Dict[str, Any]:
    standard = content_json.get("standardReport")
    if isinstance(standard, dict):
        return standard
    alt = content_json.get("standard_report")
    if isinstance(alt, dict):
        return alt
    return {}


def _pick_emotion_labels(standard_report: Dict[str, Any]) -> Dict[str, str]:
    features = standard_report.get("features") if isinstance(standard_report.get("features"), dict) else {}
    raw = features.get("emotionLabels") if isinstance(features.get("emotionLabels"), dict) else {}
    labels: Dict[str, str] = {}
    for key in EMOTION_KEYS:
        labels[key] = str(raw.get(key) or KEY_TO_JP.get(key, key)).strip() or KEY_TO_JP.get(key, key)
    return labels


def _pick_top_emotions(standard_report: Dict[str, Any], *, limit: int = 3) -> List[List[Any]]:
    metrics = standard_report.get("metrics") if isinstance(standard_report.get("metrics"), dict) else {}
    weighted = metrics.get("weightedCounts") if isinstance(metrics.get("weightedCounts"), dict) else {}
    share = metrics.get("share") if isinstance(metrics.get("share"), dict) else {}
    labels = _pick_emotion_labels(standard_report)

    source_map: Dict[str, Any] = weighted if weighted else share if share else {}
    if not source_map:
        return []

    ranked = []
    for key, value in source_map.items():
        emotion_key = str(key or "").strip()
        if emotion_key not in EMOTION_KEYS:
            continue
        ranked.append((emotion_key, _coerce_float(value, 0.0)))
    ranked.sort(key=lambda item: item[1], reverse=True)

    out: List[List[Any]] = []
    for emotion_key, score in ranked[: max(1, int(limit))]:
        label = labels.get(emotion_key) or KEY_TO_JP.get(emotion_key, emotion_key)
        out.append([label, int(round(score))])
    return out


def _extract_weekly_summary(row: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not isinstance(row, dict):
        return {"count": 0, "top": [], "error": ""}
    content_json = normalize_content_json(row.get("content_json"))
    standard_report = _pick_standard_report(content_json)
    metrics = standard_report.get("metrics") if isinstance(standard_report.get("metrics"), dict) else {}
    count = _coerce_int(metrics.get("eventCount"), 0)
    if count <= 0:
        count = _coerce_int(metrics.get("totalAll"), 0)
    return {
        "count": count,
        "top": _pick_top_emotions(standard_report),
        "error": "",
    }


def _extract_monthly_summary(row: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not isinstance(row, dict):
        return {"count": 0, "error": ""}
    content_json = normalize_content_json(row.get("content_json"))
    standard_report = _pick_standard_report(content_json)
    metrics = standard_report.get("metrics") if isinstance(standard_report.get("metrics"), dict) else {}
    count = _coerce_int(metrics.get("totalAll"), 0)
    if count <= 0:
        counts = metrics.get("counts") if isinstance(metrics.get("counts"), dict) else {}
        count = sum(_coerce_int(counts.get(key), 0) for key in EMOTION_KEYS)
    return {
        "count": count,
        "error": "",
    }


async def _build_payload(user_id: str) -> Dict[str, Any]:
    tier_str = await _resolve_viewer_tier(user_id)
    weekly_row, monthly_row = await asyncio.gather(
        _fetch_latest_report_row(user_id, "weekly", tier_str=tier_str),
        _fetch_latest_report_row(user_id, "monthly", tier_str=tier_str),
    )
    return {
        "weekly": _extract_weekly_summary(weekly_row),
        "monthly": _extract_monthly_summary(monthly_row),
    }


async def get_myweb_home_summary_from_artifacts(user_id: str) -> Dict[str, Any]:
    uid = str(user_id or "").strip()
    if not uid:
        return {
            "weekly": {"count": 0, "top": [], "error": ""},
            "monthly": {"count": 0, "error": ""},
        }

    return await get_or_compute(
        f"analysis_summary_reader:home:{uid}",
        ANALYSIS_SUMMARY_READER_CACHE_TTL_SECONDS,
        lambda: _build_payload(uid),
    )
