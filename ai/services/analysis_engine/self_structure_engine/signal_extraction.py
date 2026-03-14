from __future__ import annotations

"""
Self structure engine signal extraction.

Intended location:
    analysis_engine/self_structure_engine/signal_extraction.py

Role in the pipeline:
    SelfStructureInput / snapshot item
        -> lightweight surface analysis
        -> target extraction
        -> thinking / action tag extraction
        -> local template-role evidence
        -> SignalExtractionResult

This module is intentionally thin:
- it does not read or write the DB
- it does not update identity_state
- it does not build report text
- it does not perform monthly aggregation

It only converts one input item into one deterministic evidence object.
"""

from dataclasses import asdict, is_dataclass
from typing import Any, Iterable, List, Mapping, Optional, Sequence

try:  # package import
    from ..models import (
        SelfStructureInput,
        SignalExtractionResult,
        SurfaceSignals,
        TargetCandidate,
        TagScore,
        RoleScore,
    )
except Exception:  # standalone / local fallback
    try:
        from models_updated import (  # type: ignore
            SelfStructureInput,
            SignalExtractionResult,
            SurfaceSignals,
            TargetCandidate,
            TagScore,
            RoleScore,
        )
    except Exception:
        from models import (  # type: ignore
            SelfStructureInput,
            SignalExtractionResult,
            SurfaceSignals,
            TargetCandidate,
            TagScore,
            RoleScore,
        )

try:  # package import
    from .rules import (
        normalize_text,
        detect_surface_signals,
        estimate_reliability,
        extract_target_candidates as _extract_target_candidates,
        select_targets as _select_targets,
        extract_thinking_tags as _extract_thinking_tags,
        extract_action_tags as _extract_action_tags,
        score_role_templates as _score_role_templates,
    )
except Exception:  # standalone / local fallback
    from rules import (  # type: ignore
        normalize_text,
        detect_surface_signals,
        estimate_reliability,
        extract_target_candidates as _extract_target_candidates,
        select_targets as _select_targets,
        extract_thinking_tags as _extract_thinking_tags,
        extract_action_tags as _extract_action_tags,
        score_role_templates as _score_role_templates,
    )


# ============================================================================
# Internal normalization helpers
# ============================================================================

SUPPORTED_STAGES = {"standard", "deep"}


def _to_item_dict(item: SelfStructureInput | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(item, Mapping):
        return dict(item)
    if is_dataclass(item):
        data = asdict(item)
        if hasattr(item, "__dict__"):
            for k, v in vars(item).items():
                if k not in data:
                    data[k] = v
        return data
    if hasattr(item, "__dict__"):
        return dict(vars(item))
    raise TypeError(f"Unsupported item type for signal extraction: {type(item)!r}")


def _ensure_stage(stage: str) -> str:
    norm = normalize_text(stage)
    if norm not in SUPPORTED_STAGES:
        raise ValueError(f"Unsupported stage: {stage!r}. Expected one of {sorted(SUPPORTED_STAGES)}")
    return norm


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return normalize_text(str(value))


def _safe_category_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_categories(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        vals = [_safe_category_text(value)]
    elif isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        vals = [_safe_category_text(v) for v in value]
    else:
        vals = [_safe_category_text(value)]
    out: List[str] = []
    seen = set()
    for v in vals:
        if not v:
            continue
        if v in seen:
            continue
        seen.add(v)
        out.append(v)
    return out


def _set_category_attrs(obj: Any, categories: Sequence[str]) -> None:
    vals = list(categories or [])
    try:
        setattr(obj, "categories", vals)
    except Exception:
        pass
    try:
        setattr(obj, "category", vals[0] if len(vals) == 1 else vals)
    except Exception:
        pass


# ============================================================================
# Public text-prep helpers
# ============================================================================

def get_primary_text(item: SelfStructureInput | Mapping[str, Any]) -> str:
    data = _to_item_dict(item)
    return _safe_text(data.get("text_primary", ""))


def get_secondary_text(item: SelfStructureInput | Mapping[str, Any]) -> str:
    data = _to_item_dict(item)
    return _safe_text(data.get("text_secondary", ""))


def get_question_text(item: SelfStructureInput | Mapping[str, Any]) -> str:
    data = _to_item_dict(item)
    return _safe_text(data.get("question_text", ""))


def get_categories(item: SelfStructureInput | Mapping[str, Any]) -> List[str]:
    data = _to_item_dict(item)
    raw = data.get("categories")
    if raw is None:
        raw = data.get("category")
    return _normalize_categories(raw)


def build_analysis_text(item: SelfStructureInput | Mapping[str, Any]) -> str:
    """
    Build the text used for surface signals, reliability, and tag extraction.

    Deliberately excludes `question_text` because question wording may bias
    thinking / action detection. The answer text itself should stay primary.
    """
    primary = get_primary_text(item)
    secondary = get_secondary_text(item)
    joined = "\n".join(x for x in (primary, secondary) if x)
    return normalize_text(joined)


def build_target_text(item: SelfStructureInput | Mapping[str, Any]) -> str:
    """
    Build the text used for target extraction.

    For declarative sources, `question_text` can help recover the implicit
    target (e.g. the answer says "まとめ役" while the question says "職場では...").
    This is used only for target inference, not for thinking/action tags.

    Category labels are included here as domain hints, but intentionally
    excluded from build_analysis_text() so they do not distort reliability
    scoring or raw thinking/action extraction.
    """
    data = _to_item_dict(item)
    source_type = normalize_text(data.get("source_type", ""))
    primary = get_primary_text(data)
    secondary = get_secondary_text(data)
    question = get_question_text(data)
    categories = get_categories(data)

    parts = [*categories, primary, secondary]
    if source_type in {"deep_insight", "mymodel_create", "today_question"} and question:
        parts.append(question)
    target_hint = normalize_text(data.get("target_hint", ""))
    role_hint = normalize_text(data.get("role_hint", ""))
    world_kind_hint = normalize_text(data.get("world_kind_hint", ""))
    analysis_tags = data.get("analysis_tags") or []
    if target_hint:
        parts.append(target_hint)
    if world_kind_hint:
        parts.append(world_kind_hint)
    if role_hint:
        parts.append(role_hint)
    if isinstance(analysis_tags, list):
        parts.extend([normalize_text(x) for x in analysis_tags if normalize_text(x)])

    return normalize_text("\n".join(x for x in parts if x))


# ============================================================================
# Reliability / extraction shaping
# ============================================================================

def _limit_thinking_tags(tags: Sequence[TagScore], reliability: str) -> List[TagScore]:
    if reliability == "low":
        return list(tags[:1])
    if reliability == "medium":
        return list(tags[:2])
    return list(tags)


def _limit_action_tags(tags: Sequence[TagScore], reliability: str) -> List[TagScore]:
    if reliability == "low":
        return []
    if reliability == "medium":
        return list(tags[:1])
    return list(tags)


def _should_emit_role_scores(
    reliability: str,
    thinking_tags: Sequence[TagScore],
    action_tags: Sequence[TagScore],
) -> bool:
    if reliability == "low":
        return False
    if not thinking_tags and not action_tags:
        return False
    return True


# ============================================================================
# Public extraction helpers (thin wrappers over rules.py)
# ============================================================================

def extract_target_candidates(
    item_or_text: SelfStructureInput | Mapping[str, Any] | str,
    source_type: str | None = None,
) -> List[TargetCandidate]:
    if isinstance(item_or_text, str):
        text = normalize_text(item_or_text)
        return _extract_target_candidates(text=text, source_type=source_type or "")
    data = _to_item_dict(item_or_text)
    text = build_target_text(data)
    return _extract_target_candidates(text=text, source_type=normalize_text(data.get("source_type", "")))


def select_targets(
    candidates: Sequence[TargetCandidate],
    stage: str,
) -> tuple[Optional[TargetCandidate], List[TargetCandidate]]:
    return _select_targets(candidates=candidates, stage=_ensure_stage(stage))


def extract_thinking_tags(
    item_or_primary: SelfStructureInput | Mapping[str, Any] | str,
    *,
    text_secondary: str = "",
    source_type: str = "",
    reliability: str = "medium",
    surface: Optional[SurfaceSignals] = None,
) -> List[TagScore]:
    if isinstance(item_or_primary, str):
        primary = normalize_text(item_or_primary)
        secondary = normalize_text(text_secondary)
        src = normalize_text(source_type)
    else:
        data = _to_item_dict(item_or_primary)
        primary = get_primary_text(data)
        secondary = get_secondary_text(data)
        src = normalize_text(data.get("source_type", ""))
    tags = _extract_thinking_tags(
        text_primary=primary,
        text_secondary=secondary,
        source_type=src,
        reliability=reliability,
        surface=surface,
    )
    return _limit_thinking_tags(tags, reliability=reliability)


def extract_action_tags(
    item_or_primary: SelfStructureInput | Mapping[str, Any] | str,
    *,
    text_secondary: str = "",
    source_type: str = "",
    reliability: str = "medium",
    surface: Optional[SurfaceSignals] = None,
) -> List[TagScore]:
    if isinstance(item_or_primary, str):
        primary = normalize_text(item_or_primary)
        secondary = normalize_text(text_secondary)
        src = normalize_text(source_type)
    else:
        data = _to_item_dict(item_or_primary)
        primary = get_primary_text(data)
        secondary = get_secondary_text(data)
        src = normalize_text(data.get("source_type", ""))
    tags = _extract_action_tags(
        text_primary=primary,
        text_secondary=secondary,
        source_type=src,
        reliability=reliability,
        surface=surface,
    )
    return _limit_action_tags(tags, reliability=reliability)


def score_role_templates(
    thinking_tags: Sequence[TagScore],
    action_tags: Sequence[TagScore],
    primary_target: Optional[TargetCandidate] = None,
    reliability: str = "medium",
) -> List[RoleScore]:
    if not _should_emit_role_scores(reliability, thinking_tags, action_tags):
        return []
    return _score_role_templates(
        thinking_tags=thinking_tags,
        action_tags=action_tags,
        primary_target=primary_target,
    )


# ============================================================================
# Main orchestrator
# ============================================================================

def extract_signal_result(
    item: SelfStructureInput | Mapping[str, Any],
    stage: str = "standard",
    now_ts: str | None = None,  # reserved for future compatibility
) -> SignalExtractionResult:
    """
    Convert one self-structure input item into one deterministic evidence object.

    Parameters
    ----------
    item:
        SelfStructureInput or dict-like payload.
    stage:
        "standard" or "deep".
    now_ts:
        Reserved for future compatibility; currently unused at extraction stage.
    """
    _ = now_ts  # explicit keep for stable signature
    data = _to_item_dict(item)
    stage = _ensure_stage(stage)

    source_type = normalize_text(data.get("source_type", ""))
    source_id = str(data.get("source_id", "") or "")
    timestamp = str(data.get("timestamp", "") or "")
    categories = get_categories(data)

    text_primary = get_primary_text(data)
    text_secondary = get_secondary_text(data)

    analysis_text = build_analysis_text(data)
    target_text = build_target_text(data)

    surface = detect_surface_signals(analysis_text)
    _set_category_attrs(surface, categories)
    reliability = estimate_reliability(
        text=analysis_text,
        source_type=source_type,
        surface=surface,
    )

    target_candidates = _extract_target_candidates(
        text=target_text,
        source_type=source_type,
    )
    primary_target, secondary_targets = _select_targets(
        candidates=target_candidates,
        stage=stage,
    )

    thinking_tags = extract_thinking_tags(
        data,
        reliability=reliability,
        surface=surface,
    )
    action_tags = extract_action_tags(
        data,
        reliability=reliability,
        surface=surface,
    )

    role_scores = score_role_templates(
        thinking_tags=thinking_tags,
        action_tags=action_tags,
        primary_target=primary_target,
        reliability=reliability,
    )

    result = SignalExtractionResult(
        source_type=source_type,
        source_id=source_id,
        timestamp=timestamp,
        reliability=reliability,
        surface=surface,
        primary_target=primary_target,
        secondary_targets=secondary_targets,
        thinking_tags=thinking_tags,
        action_tags=action_tags,
        role_scores=role_scores,
        raw_text_primary=text_primary,
        raw_text_secondary=text_secondary,
    )
    _set_category_attrs(result, categories)
    return result


def extract_signal_results(
    items: Iterable[SelfStructureInput | Mapping[str, Any]],
    stage: str = "standard",
    now_ts: str | None = None,
) -> List[SignalExtractionResult]:
    stage = _ensure_stage(stage)
    return [
        extract_signal_result(item=item, stage=stage, now_ts=now_ts)
        for item in items
    ]


__all__ = [
    "get_primary_text",
    "get_secondary_text",
    "get_question_text",
    "get_categories",
    "build_analysis_text",
    "build_target_text",
    "extract_target_candidates",
    "select_targets",
    "extract_thinking_tags",
    "extract_action_tags",
    "score_role_templates",
    "extract_signal_result",
    "extract_signal_results",
]
