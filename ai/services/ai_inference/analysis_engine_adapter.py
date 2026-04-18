from __future__ import annotations

"""
Adapters between snapshot / DB-oriented payloads and analysis_engine transport models.

This module intentionally stays light and deterministic:
- no DB access
- no business logic / scoring
- no report generation

It provides two adapters:
1) build_emotion_entries_from_rows()
   Raw emotion rows -> EmotionEntry[] for emotion structure analysis.
2) build_self_structure_inputs_from_snapshot_payload()
   snapshot payload / self_structure_view -> SelfStructureInput[] for self structure analysis.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence
import importlib.util
import sys

try:  # package import
    from analysis_engine.models import EmotionEntry, SelfStructureInput
except Exception:  # standalone / local fallback
    _HERE = Path(__file__).resolve().parent
    _loaded = False
    for _candidate in (_HERE / "models_updated.py", _HERE / "models.py"):
        if not _candidate.exists():
            continue
        _spec = importlib.util.spec_from_file_location("_analysis_engine_models_local", _candidate)
        if _spec and _spec.loader:
            _mod = importlib.util.module_from_spec(_spec)
            sys.modules.setdefault(_spec.name, _mod)
            _spec.loader.exec_module(_mod)
            EmotionEntry = _mod.EmotionEntry  # type: ignore[attr-defined]
            SelfStructureInput = _mod.SelfStructureInput  # type: ignore[attr-defined]
            _loaded = True
            break
    if not _loaded:
        raise


JP_TO_LABEL = {
    "喜び": "joy",
    "悲しみ": "sadness",
    "不安": "anxiety",
    "怒り": "anger",
    "平穏": "peace",
}

STRENGTH_TO_INTENSITY = {
    "weak": 1,
    "medium": 2,
    "strong": 3,
}

SELF_INSIGHT_LABELS = {"自己理解", "SelfInsight"}

_SOURCE_TYPE_ALIASES = {
    "emotion": "emotion_input",
    "emotion_input": "emotion_input",
    "emotion_inputs": "emotion_input",
    "echo": "echo",
    "echoes": "echo",
    "discovery": "discovery",
    "discoveries": "discovery",
    "today_question": "today_question",
    "today_questions": "today_question",
}

_DEFAULT_SOURCE_WEIGHT = {
    "emotion_input": 1.0,
    "echo": 0.4,
    "discovery": 0.4,
    "today_question": 1.05,
}

# (source_type, grouped-key-in-payload)
_SOURCE_VIEW_KEYS: List[tuple[str, str]] = [
    ("emotion_input", "emotion_inputs"),
    ("emotion_input", "emotion_input"),
    ("echo", "echoes"),
    ("echo", "echo"),
    ("discovery", "discoveries"),
    ("discovery", "discovery"),
    ("today_question", "today_questions"),
    ("today_question", "today_question"),
]


# ============================================================================
# Common helpers
# ============================================================================

def _safe_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _coerce_str_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        out: List[str] = []
        for item in value:
            s = _safe_str(item)
            if s:
                out.append(s)
        return out
    s = _safe_str(value)
    return [s] if s else []


def _normalize_category_values(value: Any) -> List[str]:
    """Normalize category payload into a de-duplicated string list.

    Supports:
    - text[]-like list/tuple
    - JSON-ish scalar strings
    - comma / slash separated fallback strings
    """
    if value is None:
        return []

    if isinstance(value, (list, tuple)):
        raw_items = list(value)
    else:
        s = _safe_str(value)
        if not s:
            return []
        # Conservative split fallback for hand-entered strings.
        if "," in s:
            raw_items = [part.strip() for part in s.split(",")]
        elif "/" in s:
            raw_items = [part.strip() for part in s.split("/")]
        else:
            raw_items = [s]

    out: List[str] = []
    seen = set()
    for item in raw_items:
        s = _safe_str(item)
        if not s or s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out


def _extract_categories(raw: Mapping[str, Any]) -> List[str]:
    for key in (
        "categories",
        "category",
        "category_key",
        "category_name",
        "input_category",
        "selected_category",
        "context_category",
    ):
        if key in raw:
            cats = _normalize_category_values(raw.get(key))
            if cats:
                return cats
    return []


def _self_structure_input_supported_fields() -> set[str]:
    fields_obj = getattr(SelfStructureInput, "__dataclass_fields__", None)
    if isinstance(fields_obj, dict):
        return set(fields_obj.keys())
    return set()


def _parse_iso_to_local_date(iso_str: str) -> str:
    s = _safe_str(iso_str)
    if not s:
        return ""
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    # snapshot 側がJST基準で期間を切っている想定のため、
    # ここでは ISO -> local date 文字列で十分。
    return dt.astimezone().date().isoformat()


def _parse_sortable_timestamp(ts: str) -> datetime:
    s = _safe_str(ts)
    if not s:
        return datetime.min.replace(tzinfo=timezone.utc)
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return datetime.min.replace(tzinfo=timezone.utc)


def _normalize_source_type(raw: Any, default: str = "emotion_input") -> str:
    s = _safe_str(raw).lower()
    if not s:
        return default
    return _SOURCE_TYPE_ALIASES.get(s, s)


def _coerce_source_weight(source_type: str, raw: Any) -> float:
    try:
        if raw is not None and str(raw).strip() != "":
            return float(raw)
    except Exception:
        pass
    return _DEFAULT_SOURCE_WEIGHT.get(source_type, 1.0)


def _pick_first_text(row: Mapping[str, Any], keys: Sequence[str]) -> str:
    for key in keys:
        value = row.get(key)
        s = _safe_str(value)
        if s:
            return s
    return ""


# ============================================================================
# Emotion structure adapter
# ============================================================================

def _normalize_details(row: Dict[str, Any]) -> List[Dict[str, Any]]:
    details = row.get("emotion_details")
    if isinstance(details, list):
        out: List[Dict[str, Any]] = []
        for it in details:
            if not isinstance(it, dict):
                continue
            t = _safe_str(it.get("type"))
            s = _safe_str(it.get("strength") or "medium").lower() or "medium"
            if not t or t in SELF_INSIGHT_LABELS:
                continue
            if s not in STRENGTH_TO_INTENSITY:
                s = "medium"
            out.append({"type": t, "strength": s})
        return out

    emos = row.get("emotions")
    if isinstance(emos, list):
        out = []
        for t in emos:
            tt = _safe_str(t)
            if not tt or tt in SELF_INSIGHT_LABELS:
                continue
            out.append({"type": tt, "strength": "medium"})
        return out

    return []


def build_emotion_entries_from_rows(rows: List[Dict[str, Any]]) -> List[EmotionEntry]:
    entries: List[EmotionEntry] = []

    for row in rows or []:
        row_id = _safe_str(row.get("id"))
        created_at = _safe_str(row.get("created_at"))
        memo = row.get("memo") or None

        if not row_id or not created_at:
            continue

        date_str = _parse_iso_to_local_date(created_at)
        details = _normalize_details(row)

        for idx, d in enumerate(details):
            jp = _safe_str(d.get("type"))
            label = JP_TO_LABEL.get(jp)
            if not label:
                continue

            strength = _safe_str(d.get("strength") or "medium").lower() or "medium"
            intensity = STRENGTH_TO_INTENSITY.get(strength, 2)

            entries.append(
                EmotionEntry(
                    id=f"{row_id}:{idx}",
                    timestamp=created_at,
                    date=date_str,
                    label=label,
                    intensity=intensity,
                    memo=memo,
                )
            )

    entries.sort(key=lambda x: (_parse_sortable_timestamp(x.timestamp), x.id))
    return entries


# ============================================================================
# Self structure adapter
# ============================================================================

def _default_snapshot_timestamp(snapshot_payload: Any) -> str:
    if isinstance(snapshot_payload, Mapping):
        for key in ("generated_at", "created_at", "updated_at", "timestamp"):
            s = _safe_str(snapshot_payload.get(key))
            if s:
                return s
        payload = snapshot_payload.get("payload")
        if isinstance(payload, Mapping):
            for key in ("generated_at", "created_at", "updated_at", "timestamp"):
                s = _safe_str(payload.get(key))
                if s:
                    return s
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _iter_self_structure_items(snapshot_payload: Any) -> Iterable[tuple[str, Dict[str, Any]]]:
    """
    Accept a variety of shapes and yield (default_source_type, item_dict).

    Supported inputs:
    - self_structure_view dict: {"items": [...]}
    - snapshot payload: {"self_structure_view": {...}}
    - snapshot payload: {"views": {"self_structure_view": {...}}}
    - grouped payload: {"emotion_inputs": [...], ...}
    - direct list of items
    """
    if snapshot_payload is None:
        return

    if isinstance(snapshot_payload, list):
        for raw in snapshot_payload:
            if isinstance(raw, Mapping):
                yield ("emotion_input", dict(raw))
        return

    if not isinstance(snapshot_payload, Mapping):
        return

    # direct self_structure_view at top level
    if "self_structure_view" in snapshot_payload:
        view = snapshot_payload.get("self_structure_view")
        yield from _iter_self_structure_items(view)
        return

    # nested in payload.views
    views = snapshot_payload.get("views")
    if isinstance(views, Mapping) and "self_structure_view" in views:
        yield from _iter_self_structure_items(views.get("self_structure_view"))
        return

    # self_structure_view itself
    items = snapshot_payload.get("items")
    if isinstance(items, list):
        for raw in items:
            if isinstance(raw, Mapping):
                default_source_type = _normalize_source_type(raw.get("source_type"), default="emotion_input")
                yield (default_source_type, dict(raw))
        return

    # grouped source lists fallback
    found_any = False
    for default_source_type, key in _SOURCE_VIEW_KEYS:
        rows = snapshot_payload.get(key)
        if isinstance(rows, list):
            found_any = True
            for raw in rows:
                if isinstance(raw, Mapping):
                    yield (default_source_type, dict(raw))
    if found_any:
        return

    # last resort: if dict already looks like one item
    if any(k in snapshot_payload for k in ("source_type", "text_primary", "text_secondary", "source_id")):
        yield (_normalize_source_type(snapshot_payload.get("source_type"), default="emotion_input"), dict(snapshot_payload))


def _coerce_self_structure_item(
    raw: Mapping[str, Any],
    *,
    default_source_type: str,
    default_ts: str,
    idx: int,
) -> SelfStructureInput:
    source_type = _normalize_source_type(raw.get("source_type"), default=default_source_type)
    source_id = _safe_str(raw.get("source_id") or raw.get("id") or f"{source_type}:{idx}")
    timestamp = _safe_str(raw.get("timestamp") or raw.get("created_at") or raw.get("updated_at") or default_ts) or default_ts

    text_primary = _pick_first_text(
        raw,
        ["text_primary", "answer_text", "answer", "response_text", "text", "content", "body", "memo", "message"],
    )
    text_secondary = _pick_first_text(
        raw,
        ["text_secondary", "memo_action", "action_text", "context_text", "notes", "note"],
    )

    prompt_key = _pick_first_text(raw, ["prompt_key", "question_key", "q_key"]) or None
    question_text = _pick_first_text(raw, ["question_text", "question", "prompt", "prompt_text", "title"]) or None

    categories = _extract_categories(raw)
    category = categories[0] if categories else None

    kwargs = dict(
        source_type=source_type,
        source_id=source_id,
        timestamp=timestamp,
        text_primary=text_primary,
        text_secondary=text_secondary,
        prompt_key=prompt_key,
        question_text=question_text,
        emotion_signals=_coerce_str_list(raw.get("emotion_signals")),
        action_signals=_coerce_str_list(raw.get("action_signals")),
        social_signals=_coerce_str_list(raw.get("social_signals")),
        source_weight=_coerce_source_weight(source_type, raw.get("source_weight")),
        answer_mode=_pick_first_text(raw, ["answer_mode"]) or None,
        choice_key=_pick_first_text(raw, ["choice_key", "selected_choice_key"]) or None,
        role_hint=_pick_first_text(raw, ["role_hint"]) or None,
        target_hint=_pick_first_text(raw, ["target_hint"]) or None,
        world_kind_hint=_pick_first_text(raw, ["world_kind_hint"]) or None,
        analysis_tags=_coerce_str_list(raw.get("analysis_tags")),
    )

    supported_fields = _self_structure_input_supported_fields()
    if category is not None and "category" in supported_fields:
        kwargs["category"] = category
    if categories and "categories" in supported_fields:
        kwargs["categories"] = categories

    item = SelfStructureInput(**kwargs)

    # Forward-compatible escape hatch: keep category data attached even when the
    # current transport dataclass has not yet been expanded. Later layers can
    # read these via getattr(..., "category", None) / getattr(..., "categories", []).
    try:
        if category is not None:
            setattr(item, "category", category)
        if categories:
            setattr(item, "categories", categories)
    except Exception:
        pass

    return item


def build_self_structure_inputs_from_items(
    items: Sequence[Mapping[str, Any]],
    *,
    default_source_type: str = "emotion_input",
    default_timestamp: Optional[str] = None,
) -> List[SelfStructureInput]:
    default_ts = _safe_str(default_timestamp) or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    out: List[SelfStructureInput] = []

    for idx, raw in enumerate(items or []):
        if isinstance(raw, SelfStructureInput):
            out.append(raw)
        elif isinstance(raw, Mapping):
            out.append(
                _coerce_self_structure_item(
                    raw,
                    default_source_type=default_source_type,
                    default_ts=default_ts,
                    idx=idx,
                )
            )

    out.sort(key=lambda x: (_parse_sortable_timestamp(x.timestamp), x.source_id, x.source_type))
    return out


def build_self_structure_inputs_from_snapshot_payload(snapshot_payload: Any) -> List[SelfStructureInput]:
    """
    Convert snapshot payload or self_structure_view into SelfStructureInput[].

    Accepted shapes:
    - payload.views.self_structure_view
    - payload.self_structure_view
    - self_structure_view itself
    - grouped dict payload with source lists
    - direct list[dict]
    """
    default_ts = _default_snapshot_timestamp(snapshot_payload)
    staged: List[tuple[str, Dict[str, Any]]] = list(_iter_self_structure_items(snapshot_payload))

    out: List[SelfStructureInput] = []
    for idx, (default_source_type, raw) in enumerate(staged):
        out.append(
            _coerce_self_structure_item(
                raw,
                default_source_type=default_source_type,
                default_ts=default_ts,
                idx=idx,
            )
        )

    out.sort(key=lambda x: (_parse_sortable_timestamp(x.timestamp), x.source_id, x.source_type))
    return out


__all__ = [
    "build_emotion_entries_from_rows",
    "build_self_structure_inputs_from_items",
    "build_self_structure_inputs_from_snapshot_payload",
]
