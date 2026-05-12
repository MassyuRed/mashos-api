from __future__ import annotations

import logging
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

from supabase_client import sb_get

logger = logging.getLogger("kokoro_weather_service")
JST = timezone(timedelta(hours=9))
DAY = timedelta(days=1)

EMOTION_KEYS: Tuple[str, ...] = ("joy", "sadness", "anxiety", "anger", "calm")
KEY_TO_JP = {"joy": "喜び", "sadness": "悲しみ", "anxiety": "不安", "anger": "怒り", "calm": "平穏"}
JP_TO_KEY = {v: k for k, v in KEY_TO_JP.items()}
SELF_INSIGHT_LABELS = {"自己理解", "SelfInsight"}
STRENGTH_SCORE = {"weak": 1, "medium": 2, "strong": 3}

LABEL_CURRENT_WEATHER = "今のこころ天気"
EMPTY_TITLE = "今日はまだ観測がありません"
EMPTY_ACTION_LABEL = "前回のこころ天気を見る"

WEATHER_LABELS = {
    "clear": "ひらけ気味",
    "partly_cloudy": "うすぐもり",
    "cloudy": "くもり",
    "soft_rain": "しっとり",
    "windy": "風あり",
    "mixed": "変化多め",
    "unknown": "観測少なめ",
}
BUCKET_DEFS: Tuple[Tuple[str, str, int, int], ...] = (
    ("late_night", "深夜", 0, 6),
    ("morning", "朝", 6, 12),
    ("daytime", "昼", 12, 18),
    ("night", "夜", 18, 24),
)

TEMPERATURE_SPREAD_THRESHOLD = 6.0
TRANSITION_COUNT_THRESHOLD = 2
TOP2_MIN_SHARE_FOR_MIX = 15
TOP2_MAX_GAP_FOR_MIX = 15
PEAK_BUCKET_SHARE_THRESHOLD = 0.50
PEAK_BUCKET_MIN_INPUTS = 3


def _round1(value: Any) -> float:
    try:
        return round(float(value), 1)
    except Exception:
        return 0.0


def _coerce_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return int(default)
        if isinstance(value, bool):
            return int(value)
        return int(round(float(value)))
    except Exception:
        return int(default)


def _clamp(value: float, low: float, high: float) -> float:
    return max(float(low), min(float(high), float(value)))


def _format_degree(value: Any) -> str:
    n = _round1(value)
    return f"{int(n)}°" if float(n).is_integer() else f"{n:.1f}°"


def _parse_iso_utc(value: Any) -> Optional[datetime]:
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


def _iso_z(dt: datetime) -> str:
    value = dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _iso_jst(dt: datetime) -> str:
    value = dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)
    return value.astimezone(JST).isoformat()


def get_today_jst_period(now_utc: Optional[datetime] = None) -> Tuple[datetime, datetime]:
    now = now_utc or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    now = now.astimezone(timezone.utc)
    now_jst = now.astimezone(JST)
    start_jst = datetime(now_jst.year, now_jst.month, now_jst.day, tzinfo=JST)
    return start_jst.astimezone(timezone.utc), now


def _period_payload(start_utc: datetime, end_utc: datetime) -> Dict[str, Any]:
    return {
        "start": _iso_jst(start_utc),
        "end": _iso_jst(end_utc),
        "start_utc": _iso_z(start_utc),
        "end_utc": _iso_z(end_utc),
    }


def build_no_observation_current_weather(
    *,
    start_utc: Optional[datetime] = None,
    end_utc: Optional[datetime] = None,
    previous_available: bool = False,
) -> Dict[str, Any]:
    if start_utc is None or end_utc is None:
        start_utc, end_utc = get_today_jst_period()
    return {
        "status": "no_observation",
        "period_mode": "today_jst",
        "label": LABEL_CURRENT_WEATHER,
        "period": _period_payload(start_utc, end_utc),
        "empty_title": EMPTY_TITLE,
        "empty_action_label": EMPTY_ACTION_LABEL,
        "previous_available": bool(previous_available),
    }


def build_error_current_weather(
    *,
    start_utc: Optional[datetime] = None,
    end_utc: Optional[datetime] = None,
    error: str = "failed_to_load_current_weather",
) -> Dict[str, Any]:
    if start_utc is None or end_utc is None:
        start_utc, end_utc = get_today_jst_period()
    return {
        "status": "error",
        "period_mode": "today_jst",
        "label": LABEL_CURRENT_WEATHER,
        "period": _period_payload(start_utc, end_utc),
        "error": str(error or "failed_to_load_current_weather"),
        "empty_title": EMPTY_TITLE,
        "empty_action_label": EMPTY_ACTION_LABEL,
        "previous_available": False,
    }


def with_previous_available(current_weather: Dict[str, Any], previous_available: bool) -> Dict[str, Any]:
    out = dict(current_weather or {})
    if str(out.get("status") or "") == "no_observation":
        out["previous_available"] = bool(previous_available)
    return out


def _map_emotion_key(value: Any) -> Optional[str]:
    raw = str(value or "").strip()
    if not raw:
        return None
    if raw in JP_TO_KEY:
        return JP_TO_KEY[raw]
    if raw in EMOTION_KEYS:
        return raw
    return None


def _normalize_details(row: Dict[str, Any]) -> List[Dict[str, Any]]:
    details = row.get("emotion_details") if isinstance(row.get("emotion_details"), list) else None
    if isinstance(details, list):
        return [item for item in details if isinstance(item, dict)]
    emotions = row.get("emotions") if isinstance(row.get("emotions"), list) else []
    return [{"type": token, "strength": "medium"} for token in emotions if str(token or "").strip()]


def _row_emotion_weights(row: Dict[str, Any]) -> Dict[str, int]:
    weights = {key: 0 for key in EMOTION_KEYS}
    for item in _normalize_details(row):
        raw_type = str(item.get("type") or item.get("emotion") or item.get("key") or "").strip()
        if raw_type in SELF_INSIGHT_LABELS:
            continue
        key = _map_emotion_key(raw_type)
        if not key:
            continue
        strength = str(item.get("strength") or item.get("level") or "medium").strip().lower()
        weights[key] += int(STRENGTH_SCORE.get(strength, STRENGTH_SCORE["medium"]))
    return weights


def _dominant_key_from_weights(weights: Dict[str, int]) -> Optional[str]:
    best_key: Optional[str] = None
    best_value = 0
    for key in EMOTION_KEYS:
        value = int(weights.get(key) or 0)
        if value > best_value:
            best_key = key
            best_value = value
    return best_key if best_value > 0 else None


def _row_temperature(weights: Dict[str, int]) -> Optional[float]:
    total = sum(int(weights.get(key) or 0) for key in EMOTION_KEYS)
    if total <= 0:
        return None
    active_count = sum(1 for key in EMOTION_KEYS if int(weights.get(key) or 0) > 0)
    return _round1(_clamp(12.0 + (total * 3.0) + max(0, active_count - 1) * 1.5, 8.0, 32.0))


def _bucket_key_for_created_at(value: Any) -> Optional[str]:
    dt = _parse_iso_utc(value)
    if dt is None:
        return None
    hour = dt.astimezone(JST).hour
    for key, _label, start, end in BUCKET_DEFS:
        if start <= hour < end:
            return key
    return None


def _bucket_label(bucket_key: str) -> str:
    for key, label, _start, _end in BUCKET_DEFS:
        if key == bucket_key:
            return label
    return "時間帯"


def _share_pct(totals: Dict[str, int]) -> Dict[str, int]:
    total_all = sum(int(totals.get(key) or 0) for key in EMOTION_KEYS)
    if total_all <= 0:
        return {key: 0 for key in EMOTION_KEYS}
    return {key: int(round((int(totals.get(key) or 0) / total_all) * 100)) for key in EMOTION_KEYS}


def _transition_count(row_dominants: Iterable[Optional[str]]) -> int:
    count = 0
    prev: Optional[str] = None
    for item in row_dominants:
        key = str(item or "").strip() or None
        if not key:
            continue
        if prev is not None and key != prev:
            count += 1
        prev = key
    return count


def _top_pairs(share_pct: Dict[str, int]) -> List[Tuple[str, int]]:
    return sorted(((key, int(share_pct.get(key) or 0)) for key in EMOTION_KEYS), key=lambda item: item[1], reverse=True)


def _is_mixed(share_pct: Dict[str, int]) -> bool:
    pairs = _top_pairs(share_pct)
    if len(pairs) < 2:
        return False
    _top_key, top1 = pairs[0]
    _second_key, top2 = pairs[1]
    return top2 >= TOP2_MIN_SHARE_FOR_MIX and (top1 - top2) <= TOP2_MAX_GAP_FOR_MIX


def _classify_weather(
    *,
    share_pct: Dict[str, int],
    transition_count: int,
    temperature_spread: float,
    input_count: int,
) -> Tuple[str, str]:
    if input_count <= 0:
        return "unknown", WEATHER_LABELS["unknown"]
    pairs = _top_pairs(share_pct)
    dominant_key, dominant_share = pairs[0] if pairs else ("", 0)
    if _is_mixed(share_pct):
        return "mixed", WEATHER_LABELS["mixed"]
    if transition_count >= TRANSITION_COUNT_THRESHOLD or temperature_spread >= 8.0:
        return "windy", WEATHER_LABELS["windy"]
    if dominant_key == "calm" and dominant_share >= 45 and temperature_spread <= 5.0:
        return "clear", WEATHER_LABELS["clear"]
    if dominant_key in {"calm", "joy"}:
        return "partly_cloudy", WEATHER_LABELS["partly_cloudy"]
    if dominant_key == "sadness" and dominant_share >= 45 and temperature_spread <= 5.0:
        return "soft_rain", WEATHER_LABELS["soft_rain"]
    return "cloudy", WEATHER_LABELS["cloudy"]


def _build_observation_memo(
    *,
    temperature_high: float,
    temperature_low: float,
    transition_count: int,
    share_pct: Dict[str, int],
    bucket_counts: Dict[str, int],
    input_count: int,
) -> Dict[str, Any]:
    temperature_spread = _round1(temperature_high - temperature_low)
    memo_score = 0
    reasons: List[str] = []
    if temperature_spread >= TEMPERATURE_SPREAD_THRESHOLD:
        memo_score += 1
        reasons.append("spread")
    if transition_count >= TRANSITION_COUNT_THRESHOLD:
        memo_score += 1
        reasons.append("transition")
    if _is_mixed(share_pct):
        memo_score += 1
        reasons.append("mixed")
    peak_bucket_key = None
    if input_count > 0 and bucket_counts:
        peak_bucket_key, peak_count = max(bucket_counts.items(), key=lambda item: item[1])
        peak_bucket_share = float(peak_count) / float(max(1, input_count))
        if peak_bucket_share >= PEAK_BUCKET_SHARE_THRESHOLD and input_count >= PEAK_BUCKET_MIN_INPUTS:
            memo_score += 1
            reasons.append("peak_bucket")
    visible = memo_score >= 2
    if not visible:
        return {"visible": False, "label": "", "detail": "", "score": memo_score, "reasons": reasons}
    if "spread" in reasons:
        detail = "大きなゆらぎを観測しました。"
    elif "transition" in reasons:
        detail = "気持ちの切り替わりが多く見えていました。"
    elif "mixed" in reasons:
        detail = "複数の気持ちが近い強さで重なっていました。"
    elif peak_bucket_key:
        detail = f"{_bucket_label(peak_bucket_key)}にこころの動きが大きく見えていました。"
    else:
        detail = "流れの変化が見えていました。"
    return {"visible": True, "label": "観測メモあり", "detail": detail, "score": memo_score, "reasons": reasons}


def build_current_kokoro_weather_from_rows(
    rows: List[Dict[str, Any]],
    *,
    start_utc: Optional[datetime] = None,
    end_utc: Optional[datetime] = None,
    previous_available: bool = False,
) -> Dict[str, Any]:
    if start_utc is None or end_utc is None:
        start_utc, end_utc = get_today_jst_period()
    usable_rows = [row for row in rows or [] if isinstance(row, dict)]
    if not usable_rows:
        return build_no_observation_current_weather(start_utc=start_utc, end_utc=end_utc, previous_available=previous_available)

    totals = {key: 0 for key in EMOTION_KEYS}
    row_dominants: List[Optional[str]] = []
    row_temperatures: List[float] = []
    bucket_counts: Counter[str] = Counter()
    for row in usable_rows:
        weights = _row_emotion_weights(row)
        dominant = _dominant_key_from_weights(weights)
        if dominant:
            row_dominants.append(dominant)
        temp = _row_temperature(weights)
        if temp is not None:
            row_temperatures.append(temp)
        for key in EMOTION_KEYS:
            totals[key] += int(weights.get(key) or 0)
        bucket_key = _bucket_key_for_created_at(row.get("created_at"))
        if bucket_key:
            bucket_counts[bucket_key] += 1

    total_all = sum(int(totals.get(key) or 0) for key in EMOTION_KEYS)
    if total_all <= 0 or not row_temperatures:
        return build_no_observation_current_weather(start_utc=start_utc, end_utc=end_utc, previous_available=previous_available)

    shares = _share_pct(totals)
    pairs = _top_pairs(shares)
    dominant_key = pairs[0][0] if pairs else None
    dominant_share = int(shares.get(dominant_key or "") or 0)
    transition_count = _transition_count(row_dominants)
    temperature_current = _round1(sum(row_temperatures) / max(1, len(row_temperatures)))
    temperature_high = _round1(max(row_temperatures))
    temperature_low = _round1(min(row_temperatures))
    temperature_spread = _round1(temperature_high - temperature_low)
    weather_key, weather_label = _classify_weather(
        share_pct=shares,
        transition_count=transition_count,
        temperature_spread=temperature_spread,
        input_count=len(usable_rows),
    )
    observation_memo = _build_observation_memo(
        temperature_high=temperature_high,
        temperature_low=temperature_low,
        transition_count=transition_count,
        share_pct=shares,
        bucket_counts=dict(bucket_counts),
        input_count=len(usable_rows),
    )
    if temperature_spread >= 8.0 or transition_count >= TRANSITION_COUNT_THRESHOLD:
        fluctuation_level = "high"
        fluctuation_label = "ゆらぎ大きめ"
    elif temperature_spread >= 4.0 or _is_mixed(shares):
        fluctuation_level = "medium"
        fluctuation_label = "ゆらぎ中くらい"
    else:
        fluctuation_level = "low"
        fluctuation_label = "ゆらぎ少なめ"

    return {
        "status": "ok",
        "period_mode": "today_jst",
        "label": LABEL_CURRENT_WEATHER,
        "period": _period_payload(start_utc, end_utc),
        "weather": {"key": weather_key, "label": weather_label},
        "temperature": {
            "current": temperature_current,
            "high": temperature_high,
            "low": temperature_low,
            "unit": "kokoro_degree",
            "display": _format_degree(temperature_current),
            "high_display": _format_degree(temperature_high),
            "low_display": _format_degree(temperature_low),
        },
        "dominant_emotion": {"key": dominant_key, "label": KEY_TO_JP.get(dominant_key or "", ""), "share_pct": dominant_share},
        "emotion_share_pct": shares,
        "fluctuation": {"level": fluctuation_level, "label": fluctuation_label, "temperature_spread": temperature_spread, "transition_count": transition_count},
        "observation_memo": observation_memo,
        "input_count": len(usable_rows),
    }


async def _fetch_today_emotion_rows(user_id: str, *, start_utc: datetime, end_utc: datetime) -> List[Dict[str, Any]]:
    uid = str(user_id or "").strip()
    if not uid:
        return []
    start_iso = _iso_z(start_utc)
    end_iso = _iso_z(end_utc)
    resp = await sb_get(
        "/rest/v1/emotions",
        params={
            "select": "created_at,emotions,emotion_details,is_secret",
            "user_id": f"eq.{uid}",
            "and": f"(created_at.gte.{start_iso},created_at.lte.{end_iso},is_secret.eq.false)",
            "order": "created_at.asc",
            "limit": "5000",
        },
        timeout=8.0,
    )
    if resp.status_code >= 300:
        logger.warning("kokoro current weather emotions select failed: status=%s body=%s", resp.status_code, (getattr(resp, "text", "") or "")[:800])
        raise RuntimeError("failed_to_load_current_weather")
    try:
        data = resp.json()
    except Exception:
        return []
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]
    if isinstance(data, dict):
        return [data]
    return []


async def build_current_kokoro_weather(
    user_id: str,
    *,
    now_utc: Optional[datetime] = None,
    previous_available: bool = False,
) -> Dict[str, Any]:
    start_utc, end_utc = get_today_jst_period(now_utc)
    try:
        rows = await _fetch_today_emotion_rows(user_id, start_utc=start_utc, end_utc=end_utc)
        return build_current_kokoro_weather_from_rows(rows, start_utc=start_utc, end_utc=end_utc, previous_available=previous_available)
    except Exception as exc:
        logger.warning("failed to build current kokoro weather user_id=%s err=%r", str(user_id or "")[:12], exc)
        return build_error_current_weather(start_utc=start_utc, end_utc=end_utc)


# -----------------------------------------------------------------------------
# Report kokoroWeather payloads
# -----------------------------------------------------------------------------

def _normalize_dt_utc(value: Any, fallback: Optional[datetime] = None) -> datetime:
    if isinstance(value, datetime):
        dt = value
    else:
        dt = _parse_iso_utc(value)
        if dt is None:
            dt = fallback or datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _period_label(start_utc: datetime, end_utc: datetime, report_type: str) -> str:
    start_jst = _normalize_dt_utc(start_utc).astimezone(JST)
    end_jst = _normalize_dt_utc(end_utc).astimezone(JST)
    if report_type == "daily":
        return f"{start_jst.month}/{start_jst.day}"
    return f"{start_jst.month}/{start_jst.day} 〜 {end_jst.month}/{end_jst.day}"


def _weekday_ja(dt: datetime) -> str:
    return "月火水木金土日"[dt.astimezone(JST).weekday()]


def _day_label(dt: datetime) -> str:
    jst = dt.astimezone(JST)
    return f"{jst.month}/{jst.day}({_weekday_ja(jst)})"


def _normalize_emotion_counts(raw: Any) -> Dict[str, int]:
    out = {key: 0 for key in EMOTION_KEYS}
    if isinstance(raw, dict):
        for key in EMOTION_KEYS:
            out[key] = max(0, _coerce_int(raw.get(key), 0))
    return out


def _row_weights_total(rows: List[Dict[str, Any]]) -> Dict[str, int]:
    totals = {key: 0 for key in EMOTION_KEYS}
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        weights = _row_emotion_weights(row)
        for key in EMOTION_KEYS:
            totals[key] += int(weights.get(key) or 0)
    return totals


def _counts_from_item(item: Any) -> Dict[str, int]:
    if not isinstance(item, dict):
        return {key: 0 for key in EMOTION_KEYS}
    for candidate_key in ("weightedCounts", "weighted_counts", "totals", "counts", "emotionCounts", "emotion_counts"):
        candidate = item.get(candidate_key)
        counts = _normalize_emotion_counts(candidate)
        if sum(counts.values()) > 0:
            return counts
    return _normalize_emotion_counts(item)


def _dominant_from_counts(counts: Dict[str, int]) -> Optional[str]:
    return _dominant_key_from_weights(counts)


def _temperature_from_counts(counts: Dict[str, int]) -> Optional[float]:
    total = sum(int(counts.get(key) or 0) for key in EMOTION_KEYS)
    if total <= 0:
        return None
    active_count = sum(1 for key in EMOTION_KEYS if int(counts.get(key) or 0) > 0)
    return _round1(_clamp(12.0 + (total * 1.4) + max(0, active_count - 1) * 1.2, 8.0, 32.0))


def _summary_from_counts(
    counts: Dict[str, int],
    *,
    input_count: int,
    temperatures: Optional[List[float]] = None,
    transition_count: int = 0,
    bucket_counts: Optional[Dict[str, int]] = None,
) -> Dict[str, Any]:
    totals = _normalize_emotion_counts(counts)
    total_all = sum(totals.values())
    shares = _share_pct(totals)
    dominant_key = _dominant_key_from_weights(totals)
    dominant_share = int(shares.get(dominant_key or "") or 0)
    temps = [float(t) for t in (temperatures or []) if isinstance(t, (int, float))]
    fallback_temp = _temperature_from_counts(totals)
    if not temps and fallback_temp is not None:
        temps = [fallback_temp]
    if temps:
        temperature_current = _round1(sum(temps) / max(1, len(temps)))
        temperature_high = _round1(max(temps))
        temperature_low = _round1(min(temps))
    else:
        temperature_current = 0.0
        temperature_high = 0.0
        temperature_low = 0.0
    spread = _round1(temperature_high - temperature_low)
    weather_key, weather_label = _classify_weather(
        share_pct=shares,
        transition_count=transition_count,
        temperature_spread=spread,
        input_count=input_count if input_count > 0 else total_all,
    )
    observation_memo = _build_observation_memo(
        temperature_high=temperature_high,
        temperature_low=temperature_low,
        transition_count=transition_count,
        share_pct=shares,
        bucket_counts=bucket_counts or {},
        input_count=max(input_count, 1 if total_all > 0 else 0),
    )
    if spread >= 8.0 or transition_count >= TRANSITION_COUNT_THRESHOLD:
        fluctuation = {"level": "high", "label": "ゆらぎ大きめ", "temperature_spread": spread, "transition_count": transition_count}
    elif spread >= 4.0 or _is_mixed(shares):
        fluctuation = {"level": "medium", "label": "ゆらぎ中くらい", "temperature_spread": spread, "transition_count": transition_count}
    else:
        fluctuation = {"level": "low", "label": "ゆらぎ少なめ", "temperature_spread": spread, "transition_count": transition_count}
    return {
        "weather_key": weather_key,
        "weather_label": weather_label,
        "temperature_current": temperature_current,
        "temperature_high": temperature_high,
        "temperature_low": temperature_low,
        "temperature_display": _format_degree(temperature_current),
        "temperature_high_display": _format_degree(temperature_high),
        "temperature_low_display": _format_degree(temperature_low),
        "dominant_emotion": {"key": dominant_key, "label": KEY_TO_JP.get(dominant_key or "", ""), "share_pct": dominant_share},
        "emotion_share_pct": shares,
        "total_all": total_all,
        "input_count": input_count,
        "fluctuation": fluctuation,
        "observation_memo": observation_memo,
    }


def _rows_in_range(rows: List[Dict[str, Any]], start_utc: datetime, end_utc: datetime) -> List[Dict[str, Any]]:
    start = _normalize_dt_utc(start_utc)
    end = _normalize_dt_utc(end_utc)
    out: List[Dict[str, Any]] = []
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        dt = _parse_iso_utc(row.get("created_at"))
        if dt is None:
            continue
        if start <= dt < end:
            out.append(row)
    return out


def _time_bucket_weather_from_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    bucket_rows: Dict[str, List[Dict[str, Any]]] = {key: [] for key, _label, _start, _end in BUCKET_DEFS}
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        bucket_key = _bucket_key_for_created_at(row.get("created_at"))
        if bucket_key in bucket_rows:
            bucket_rows[bucket_key].append(row)
    items: List[Dict[str, Any]] = []
    for bucket_key, label, _start, _end in BUCKET_DEFS:
        bucket_values = bucket_rows.get(bucket_key, [])
        counts = _row_weights_total(bucket_values)
        row_dominants = [_dominant_key_from_weights(_row_emotion_weights(row)) for row in bucket_values]
        row_temperatures = [temp for row in bucket_values for temp in [_row_temperature(_row_emotion_weights(row))] if temp is not None]
        summary = _summary_from_counts(
            counts,
            input_count=len(bucket_values),
            temperatures=row_temperatures,
            transition_count=_transition_count(row_dominants),
            bucket_counts={bucket_key: len(bucket_values)} if bucket_values else {},
        )
        items.append(
            {
                "kind": "time_bucket",
                "bucket_key": bucket_key,
                "label": label,
                "weather_key": summary["weather_key"],
                "weather_label": summary["weather_label"],
                "temperature": summary["temperature_current"],
                "temperature_display": summary["temperature_display"],
                "temperature_high": summary["temperature_high"],
                "temperature_low": summary["temperature_low"],
                "dominant_emotion": summary["dominant_emotion"],
                "emotion_share_pct": summary["emotion_share_pct"],
                "input_count": len(bucket_values),
                "observation_memo": summary["observation_memo"],
            }
        )
    return items


def _time_bucket_weather_from_existing(raw_buckets: Any) -> List[Dict[str, Any]]:
    if not isinstance(raw_buckets, list):
        return []
    out: List[Dict[str, Any]] = []
    for item in raw_buckets:
        if not isinstance(item, dict):
            continue
        bucket_key = str(item.get("bucket") or item.get("bucket_key") or item.get("key") or "").strip()
        label = str(item.get("label") or _bucket_label(bucket_key)).strip() or "時間帯"
        counts = _counts_from_item(item)
        input_count = _coerce_int(item.get("inputCount") or item.get("input_count") or item.get("count"), 0)
        summary = _summary_from_counts(counts, input_count=input_count)
        out.append(
            {
                "kind": "time_bucket",
                "bucket_key": bucket_key or None,
                "label": label,
                "weather_key": summary["weather_key"],
                "weather_label": summary["weather_label"],
                "temperature": summary["temperature_current"],
                "temperature_display": summary["temperature_display"],
                "temperature_high": summary["temperature_high"],
                "temperature_low": summary["temperature_low"],
                "dominant_emotion": summary["dominant_emotion"],
                "emotion_share_pct": summary["emotion_share_pct"],
                "input_count": input_count,
                "observation_memo": summary["observation_memo"],
            }
        )
    return out


def _day_weather_item(
    *,
    dt_utc: datetime,
    rows: Optional[List[Dict[str, Any]]] = None,
    existing_day: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    row_values = rows or []
    counts = _row_weights_total(row_values) if row_values else _counts_from_item(existing_day or {})
    row_dominants = [_dominant_key_from_weights(_row_emotion_weights(row)) for row in row_values]
    row_temperatures = [temp for row in row_values for temp in [_row_temperature(_row_emotion_weights(row))] if temp is not None]
    summary = _summary_from_counts(
        counts,
        input_count=len(row_values) if row_values else _coerce_int((existing_day or {}).get("inputCount") or (existing_day or {}).get("count"), 0),
        temperatures=row_temperatures,
        transition_count=_transition_count(row_dominants),
    )
    date_key = str((existing_day or {}).get("dateKey") or (existing_day or {}).get("date_key") or "").strip()
    if not date_key:
        j = dt_utc.astimezone(JST)
        date_key = f"{j.year:04d}-{j.month:02d}-{j.day:02d}"
    label = str((existing_day or {}).get("label") or _day_label(dt_utc)).strip()
    return {
        "kind": "day",
        "date_key": date_key,
        "label": label,
        "weather_key": summary["weather_key"],
        "weather_label": summary["weather_label"],
        "temperature": summary["temperature_current"],
        "temperature_display": summary["temperature_display"],
        "temperature_high": summary["temperature_high"],
        "temperature_high_display": summary["temperature_high_display"],
        "temperature_low": summary["temperature_low"],
        "temperature_low_display": summary["temperature_low_display"],
        "dominant_emotion": summary["dominant_emotion"],
        "emotion_share_pct": summary["emotion_share_pct"],
        "input_count": summary["input_count"],
        "observation_memo": summary["observation_memo"],
        "time_buckets": _time_bucket_weather_from_rows(row_values) if row_values else [],
    }


def _week_weather_item(*, index: int, rows: Optional[List[Dict[str, Any]]] = None, existing_week: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    row_values = rows or []
    counts = _row_weights_total(row_values) if row_values else _counts_from_item(existing_week or {})
    row_dominants = [_dominant_key_from_weights(_row_emotion_weights(row)) for row in row_values]
    row_temperatures = [temp for row in row_values for temp in [_row_temperature(_row_emotion_weights(row))] if temp is not None]
    summary = _summary_from_counts(
        counts,
        input_count=len(row_values) if row_values else _coerce_int((existing_week or {}).get("inputCount") or (existing_week or {}).get("count"), 0),
        temperatures=row_temperatures,
        transition_count=_transition_count(row_dominants),
    )
    label = str((existing_week or {}).get("label") or f"第{index + 1}週").strip()
    return {
        "kind": "week",
        "week_index": index,
        "label": label,
        "weather_key": summary["weather_key"],
        "weather_label": summary["weather_label"],
        "temperature": summary["temperature_current"],
        "temperature_display": summary["temperature_display"],
        "temperature_high": summary["temperature_high"],
        "temperature_high_display": summary["temperature_high_display"],
        "temperature_low": summary["temperature_low"],
        "temperature_low_display": summary["temperature_low_display"],
        "dominant_emotion": summary["dominant_emotion"],
        "emotion_share_pct": summary["emotion_share_pct"],
        "input_count": summary["input_count"],
        "observation_memo": summary["observation_memo"],
        "time_buckets": _time_bucket_weather_from_rows(row_values) if row_values else [],
    }


def build_time_bucket_weather(
    rows: Optional[List[Dict[str, Any]]] = None,
    *,
    existing_time_buckets: Any = None,
) -> List[Dict[str, Any]]:
    if rows:
        return _time_bucket_weather_from_rows([row for row in rows if isinstance(row, dict)])
    return _time_bucket_weather_from_existing(existing_time_buckets)


def build_report_kokoro_weather(
    *,
    report_type: str,
    rows: Optional[List[Dict[str, Any]]] = None,
    period_start_utc: Any,
    period_end_utc: Any,
    existing_metrics: Optional[Dict[str, Any]] = None,
    existing_days: Optional[List[Dict[str, Any]]] = None,
    existing_weeks: Optional[List[Dict[str, Any]]] = None,
    existing_time_buckets: Any = None,
    movement: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build additive content_json.kokoroWeather for daily / weekly / monthly reports.

    The payload is intentionally display-oriented and fail-closed.  It never changes
    the report body, publish policy, DB names, or daily/weekly/monthly internal keys.
    """
    rt = str(report_type or "").strip().lower()
    if rt not in {"daily", "weekly", "monthly"}:
        rt = "weekly"
    start = _normalize_dt_utc(period_start_utc)
    end = _normalize_dt_utc(period_end_utc, fallback=start + DAY)
    row_values = [row for row in (rows or []) if isinstance(row, dict)]
    metrics = existing_metrics if isinstance(existing_metrics, dict) else {}
    metric_counts = _normalize_emotion_counts(metrics.get("totals") or metrics.get("weightedCounts") or metrics.get("counts"))
    if sum(metric_counts.values()) <= 0 and row_values:
        metric_counts = _row_weights_total(row_values)
    summary_temperatures = [temp for row in row_values for temp in [_row_temperature(_row_emotion_weights(row))] if temp is not None]
    summary_dominants = [_dominant_key_from_weights(_row_emotion_weights(row)) for row in row_values]
    bucket_counts: Counter[str] = Counter()
    for row in row_values:
        bucket_key = _bucket_key_for_created_at(row.get("created_at"))
        if bucket_key:
            bucket_counts[bucket_key] += 1
    summary = _summary_from_counts(
        metric_counts,
        input_count=len(row_values) if row_values else _coerce_int(metrics.get("inputCount") or metrics.get("totalInputs") or metrics.get("totalAll"), 0),
        temperatures=summary_temperatures,
        transition_count=_transition_count(summary_dominants),
        bucket_counts=dict(bucket_counts),
    )
    if isinstance(movement, dict) and str(movement.get("key") or "").strip() and not summary.get("observation_memo", {}).get("visible"):
        memo = dict(summary.get("observation_memo") or {})
        memo.update({"visible": True, "label": "観測メモあり", "detail": "流れの変化が見えていました。", "reasons": ["movement"]})
        summary["observation_memo"] = memo

    items: List[Dict[str, Any]] = []
    if rt == "daily":
        time_buckets = build_time_bucket_weather(row_values, existing_time_buckets=existing_time_buckets)
        items = time_buckets
    elif rt == "weekly":
        day_map: Dict[str, List[Dict[str, Any]]] = {}
        for row in row_values:
            dt = _parse_iso_utc(row.get("created_at"))
            if dt is None:
                continue
            j = dt.astimezone(JST)
            key = f"{j.year:04d}-{j.month:02d}-{j.day:02d}"
            day_map.setdefault(key, []).append(row)
        if isinstance(existing_days, list) and existing_days:
            for idx, day in enumerate(existing_days[:7]):
                dt = start + idx * DAY
                key = str((day or {}).get("dateKey") or (day or {}).get("date_key") or "").strip()
                items.append(_day_weather_item(dt_utc=dt, rows=day_map.get(key, []), existing_day=day if isinstance(day, dict) else None))
        else:
            for idx in range(7):
                dt = start + idx * DAY
                j = dt.astimezone(JST)
                key = f"{j.year:04d}-{j.month:02d}-{j.day:02d}"
                items.append(_day_weather_item(dt_utc=dt, rows=day_map.get(key, [])))
    else:
        week_map: Dict[int, List[Dict[str, Any]]] = {}
        for row in row_values:
            dt = _parse_iso_utc(row.get("created_at"))
            if dt is None:
                continue
            idx_raw = int(((dt - start).total_seconds()) // (7 * 86400))
            idx = max(0, min(3, idx_raw))
            week_map.setdefault(idx, []).append(row)
        if isinstance(existing_weeks, list) and existing_weeks:
            for idx, week in enumerate(existing_weeks[:4]):
                items.append(_week_weather_item(index=idx, rows=week_map.get(idx, []), existing_week=week if isinstance(week, dict) else None))
        else:
            for idx in range(4):
                items.append(_week_weather_item(index=idx, rows=week_map.get(idx, [])))

    has_observation = bool(
        (summary.get("input_count") or 0) > 0
        or sum(_coerce_int(item.get("weighted_total") or item.get("input_count"), 0) for item in items) > 0
        or sum(_coerce_int(v, 0) for v in metric_counts.values()) > 0
    )
    payload = {
        "version": "kokoro.weather.v1",
        "status": "ok" if has_observation else "no_observation",
        "report_type": rt,
        "period_label": _period_label(start, end, rt),
        "period": _period_payload(start, end),
        "summary": summary,
        "items": items,
    }
    if rt == "daily":
        payload["time_buckets"] = items
    return payload


__all__ = [
    "build_current_kokoro_weather",
    "build_current_kokoro_weather_from_rows",
    "build_report_kokoro_weather",
    "build_time_bucket_weather",
    "build_error_current_weather",
    "build_no_observation_current_weather",
    "get_today_jst_period",
    "with_previous_available",
]
