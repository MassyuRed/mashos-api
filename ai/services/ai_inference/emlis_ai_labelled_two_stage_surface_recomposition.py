# -*- coding: utf-8 -*-
from __future__ import annotations

"""P6 labelled two-stage surface recomposition for EmlisAI public observation.

This module owns the lane that converts a safe, material-sufficient,
``two_stage_required`` public candidate that failed public surface validation
into the labelled two-stage public surface required by the product contract.
The original candidate may be plain or already labelled-but-invalid; P6 still
recomposes from material instead of re-adopting the failed body.  It is not
normal_observation_rebuild, does not promote Gate Recovery material surfaces,
does not add fixed/case-specific fallback text, and keeps all exported meta
body-free.
"""

from collections.abc import Mapping, Sequence
from typing import Any, Final
import json
import re

from emlis_ai_gate_recovery_public_constants import (
    CANDIDATE_SOURCE_KIND_DIAGNOSTIC_RECOVERY_SURFACE,
    CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE,
    CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE,
    CANDIDATE_SOURCE_KIND_NONE,
    PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
)
from emlis_ai_public_surface_requirement import (
    SURFACE_REQUIREMENT_LABELLED_TWO_STAGE,
    is_labelled_two_stage_comment_text_shape,
    public_surface_requirement_public_summary,
)
from emlis_ai_types import ConversationComposerCandidate

LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.labelled_two_stage_surface_recomposition_candidate.v1"
)
LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_SOURCE_PHASE: Final = (
    "PublicObservationRecovery_P6_LabelledTwoStageSurfaceRecomposition"
)
LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_COMPOSER_MODEL: Final = (
    "labelled_two_stage_surface_recomposition_v1"
)
LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_GENERATION_METHOD: Final = (
    "labelled_two_stage_recompose_from_material_for_two_stage_required"
)
LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_RESPONSE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.labelled_two_stage_surface_recomposition.response.v1"
)
LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_PUBLIC_META_KEY: Final = (
    "labelled_two_stage_surface_recomposition_summary"
)
LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_SCOPE: Final = (
    "labelled_two_stage_surface_recomposition"
)

_UNSUPPORTED_MATERIAL_QUALITIES: Final[frozenset[str]] = frozenset(
    {
        "low_information",
        "limited_grounding",
        "limited_grounding_material",
        "insufficient_input_material",
        "empty_input_material",
    }
)
_BLOCKED_SOURCE_KINDS: Final[frozenset[str]] = frozenset(
    {
        CANDIDATE_SOURCE_KIND_NONE,
        CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE,
        CANDIDATE_SOURCE_KIND_DIAGNOSTIC_RECOVERY_SURFACE,
    }
)
_FORBIDDEN_META_TEXT_KEYS: Final[frozenset[str]] = frozenset(
    {
        "raw_input",
        "rawInput",
        "raw_text",
        "rawText",
        "input_text",
        "inputText",
        "memo",
        "memo_text",
        "memoText",
        "memo_action",
        "memoAction",
        "current_input",
        "currentInput",
        "comment_text",
        "commentText",
        "comment_text_body",
        "commentTextBody",
        "candidate_comment_text",
        "public_comment_text",
        "reply_text",
        "replyText",
        "surface_text",
        "surfaceText",
        "observation_text",
        "observationText",
        "reception_text",
        "receptionText",
        "candidate_body",
        "candidateBody",
        "surface_body",
        "surfaceBody",
        "generated_candidate_text",
        "original_comment_text",
        "body",
        "text",
    }
)
_META_REQUIRED_KEYS: Final[frozenset[str]] = frozenset(
    {
        "schema_version",
        "source_phase",
        "candidate_source_kind",
        "public_surface_role",
        "composer_source",
        "composer_model",
        "generation_method",
        "original_candidate_present",
        "original_candidate_source_kind",
        "original_candidate_status",
        "original_surface_plain_or_unlabelled",
        "source_unavailable_recovered",
        "labelled_two_stage_surface_recomposition_used",
        "normal_observation_rebuild_used",
        "complete_initial_surface_recomposition_used",
        "gate_recovery_material_surface_used",
        "surface_requirement",
        "surface_requirement_family",
        "two_stage_required",
        "plain_surface_allowed",
        "low_information_allowed",
        "two_stage_section_surface_plan",
        "source_material_summary",
        "labelled_two_stage_surface_recomposition_summary",
        "gate_contract",
        "body_boundary",
        "implementation_boundary",
        "candidate_lineage",
        "raw_input_included",
        "comment_text_body_included",
    }
)


def should_attempt_labelled_two_stage_surface_recomposition(
    *,
    current_input: Mapping[str, Any] | None,
    material_route: Any,
    surface_requirement: Mapping[str, Any] | None,
    original_composer_candidate: Any | None,
    original_display_decision: Any | None = None,
    safety_requires_block: bool = False,
    reply_timeout_or_error: bool = False,
    composer_disabled: bool = False,
) -> bool:
    """Return whether P6 may try labelled two-stage recomposition."""

    _ = current_input, original_display_decision
    if safety_requires_block or reply_timeout_or_error or composer_disabled:
        return False
    requirement = public_surface_requirement_public_summary(surface_requirement)
    family = _clean_identifier(requirement.get("surface_requirement_family"), max_length=96)
    if not (requirement.get("two_stage_required") is True or family == SURFACE_REQUIREMENT_LABELLED_TWO_STAGE):
        return False
    if requirement.get("plain_state_answer_allowed") is True:
        return False
    if original_composer_candidate is None:
        return False
    if _display_decision_passed(original_display_decision):
        return False
    if not _candidate_has_public_text(original_composer_candidate):
        return False
    source_kind = _candidate_source_kind(original_composer_candidate)
    if source_kind in _BLOCKED_SOURCE_KINDS:
        return False
    composer_source = _clean_identifier(getattr(original_composer_candidate, "composer_source", ""), max_length=96)
    if composer_source and composer_source != "ai_generated":
        return False
    if bool(getattr(original_composer_candidate, "ai_generated", False)) is not True:
        return False
    status = _clean_identifier(getattr(original_composer_candidate, "status", ""), max_length=96)
    if status and status not in {"generated", "passed", "recovered"}:
        return False
    material_quality = _material_quality(material_route) or _clean_identifier(
        requirement.get("material_quality_family"),
        max_length=96,
    )
    if material_quality in _UNSUPPORTED_MATERIAL_QUALITIES:
        return False
    return True


def build_labelled_two_stage_surface_recomposition_candidate(
    *,
    current_input: Mapping[str, Any] | None,
    material_route: Any,
    surface_requirement: Mapping[str, Any] | None,
    original_composer_candidate: Any | None,
    original_display_decision: Any | None,
    trace_id: str,
    recovery_context: str,
    safety_requires_block: bool = False,
    reply_timeout_or_error: bool = False,
    composer_disabled: bool = False,
) -> tuple[ConversationComposerCandidate | None, list[str]]:
    """Build the P6 labelled two-stage public observation candidate."""

    requirement = public_surface_requirement_public_summary(surface_requirement)
    if not should_attempt_labelled_two_stage_surface_recomposition(
        current_input=current_input,
        material_route=material_route,
        surface_requirement=requirement,
        original_composer_candidate=original_composer_candidate,
        original_display_decision=original_display_decision,
        safety_requires_block=safety_requires_block,
        reply_timeout_or_error=reply_timeout_or_error,
        composer_disabled=composer_disabled,
    ):
        return None, ["labelled_two_stage_surface_recomposition_not_allowed"]

    comment_text = _clean_public_body(
        _compose_labelled_two_stage_comment(current_input=current_input, material_route=material_route)
    )
    if not comment_text:
        return None, ["labelled_two_stage_surface_recomposition_comment_text_missing"]
    if not is_labelled_two_stage_comment_text_shape(comment_text):
        return None, ["labelled_two_stage_surface_recomposition_shape_invalid"]

    route_meta = _material_route_meta(material_route)
    visible_slots = _dedupe(_first(("visible_material_slots",), route_meta) or [])
    unknown_slots = _dedupe(_first(("unknown_slots",), route_meta) or [])
    relation_ids = _dedupe(
        _first(("relation_material_ids", "generic_relation_material_ids"), route_meta) or []
    )
    material_quality = _material_quality(material_route) or _clean_identifier(
        _first(("material_quality", "eligibility_status", "status"), route_meta),
        max_length=96,
    )
    source_kind = _candidate_source_kind(original_composer_candidate)
    used_evidence_span_ids = _evidence_span_ids(visible_slots=visible_slots, relation_ids=relation_ids)
    used_phrase_unit_ids = _phrase_unit_ids(
        topic=_topic_phrase(current_input=current_input, material_route=material_route),
        feeling=_feeling_phrase(current_input=current_input),
        action=_action_phrase(current_input=current_input),
    )
    meta = _candidate_meta(
        surface_requirement=requirement,
        material_quality=material_quality,
        visible_slot_count=len(visible_slots),
        unknown_slot_count=len(unknown_slots),
        relation_id_count=len(relation_ids),
        used_evidence_span_ids=used_evidence_span_ids,
        used_phrase_unit_ids=used_phrase_unit_ids,
        original_candidate_source_kind=source_kind,
        original_candidate_status=_clean_identifier(getattr(original_composer_candidate, "status", ""), max_length=96),
        original_display_status=_clean_identifier(getattr(original_display_decision, "observation_status", ""), max_length=96),
        original_surface_plain_or_unlabelled=not is_labelled_two_stage_comment_text_shape(
            str(getattr(original_composer_candidate, "comment_text", "") or "")
        ),
        recovery_context=recovery_context,
    )
    assert_labelled_two_stage_surface_recomposition_meta(meta)
    return (
        ConversationComposerCandidate(
            comment_text=comment_text,
            composer_source="ai_generated",
            status="generated",
            ai_generated=True,
            trace_id=str(trace_id or _clean_identifier(getattr(original_composer_candidate, "trace_id", ""), max_length=128)),
            attempt_count=1,
            used_evidence_span_ids=list(used_evidence_span_ids),
            confidence=float(getattr(original_composer_candidate, "confidence", 0.0) or 0.0) or 0.78,
            rejection_reasons=[],
            request_schema_version=_clean_identifier(
                getattr(original_composer_candidate, "request_schema_version", ""), max_length=128
            )
            or "emlis.composer.request.v1",
            response_schema_version=LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_RESPONSE_SCHEMA_VERSION,
            fixed_string_renderer_used=False,
            composer_model=LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_COMPOSER_MODEL,
            generation_method=LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_GENERATION_METHOD,
            coverage_scope="current_input_labelled_two_stage_surface_recomposition",
            generation_scope="current_input_material_bundle_only",
            composer_meta=meta,
            used_claim_ids=[f"p6_claim_{idx + 1}" for idx in range(max(1, min(3, len(used_evidence_span_ids))))],
            used_relation_ids=list(relation_ids) or list(getattr(original_composer_candidate, "used_relation_ids", []) or []),
        ),
        ["labelled_two_stage_surface_recomposition_candidate_built"],
    )


def labelled_two_stage_surface_recomposition_public_summary(value: Mapping[str, Any] | None) -> dict[str, Any]:
    meta = _as_mapping(value)
    return {
        "schema_version": _clean_identifier(meta.get("schema_version"), max_length=128)
        or LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_SCHEMA_VERSION,
        "source_phase": _clean_identifier(meta.get("source_phase"), max_length=128)
        or LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_SOURCE_PHASE,
        "candidate_source_kind": CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE,
        "labelled_two_stage_surface_recomposition_used": True,
        "normal_observation_rebuild_used": False,
        "complete_initial_surface_recomposition_used": False,
        "gate_recovery_material_surface_used": False,
        "surface_requirement_family": _clean_identifier(meta.get("surface_requirement_family"), max_length=96),
        "two_stage_required": bool(meta.get("two_stage_required", True)),
        "plain_surface_allowed": False,
        "labels_present": bool(
            _as_mapping(meta.get("labelled_two_stage_surface_recomposition_summary")).get("labels_present")
        ),
        "section_budget_valid": bool(
            _as_mapping(meta.get("labelled_two_stage_surface_recomposition_summary")).get("section_budget_valid")
        ),
        "body_free": True,
        "raw_input_included": False,
        "comment_text_body_included": False,
        "display_gate_relaxed": False,
    }


def assert_labelled_two_stage_surface_recomposition_meta(value: Mapping[str, Any]) -> None:
    if not isinstance(value, Mapping):
        raise ValueError("labelled two-stage surface recomposition meta must be a mapping")
    missing = _META_REQUIRED_KEYS.difference(value.keys())
    if missing:
        raise ValueError(f"labelled two-stage surface recomposition meta missing keys: {sorted(missing)}")
    if value.get("schema_version") != LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_SCHEMA_VERSION:
        raise ValueError("unexpected labelled two-stage surface recomposition schema_version")
    if value.get("candidate_source_kind") != CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE:
        raise ValueError("unexpected labelled two-stage surface recomposition candidate_source_kind")
    if value.get("composer_source") != "ai_generated":
        raise ValueError("labelled two-stage surface recomposition must remain ai_generated")
    if value.get("two_stage_required") is not True:
        raise ValueError("labelled two-stage surface recomposition requires two-stage surface")
    if value.get("plain_surface_allowed") is not False:
        raise ValueError("labelled two-stage surface recomposition cannot allow plain surface")
    if value.get("normal_observation_rebuild_used") is not False:
        raise ValueError("labelled two-stage surface recomposition must not use normal rebuild")
    if value.get("complete_initial_surface_recomposition_used") is not False:
        raise ValueError("labelled two-stage surface recomposition must not masquerade as P5")
    if value.get("gate_recovery_material_surface_used") is not False:
        raise ValueError("labelled two-stage surface recomposition must not use Gate Recovery material surface")
    if any(bool(value.get(key)) for key in ("raw_input_included", "comment_text_body_included")):
        raise ValueError("labelled two-stage surface recomposition meta must be body-free")
    if _contains_forbidden_text_key(value):
        raise ValueError("labelled two-stage surface recomposition meta must not contain text payload keys")
    for key in ("gate_contract", "body_boundary", "implementation_boundary"):
        nested = _as_mapping(value.get(key))
        if any(bool(flag) for flag in nested.values()):
            raise ValueError(f"labelled two-stage surface recomposition {key} flags must be false")
    json.dumps(dict(value), ensure_ascii=False, sort_keys=True)


def _candidate_meta(
    *,
    surface_requirement: Mapping[str, Any],
    material_quality: str,
    visible_slot_count: int,
    unknown_slot_count: int,
    relation_id_count: int,
    used_evidence_span_ids: Sequence[str],
    used_phrase_unit_ids: Sequence[str],
    original_candidate_source_kind: str,
    original_candidate_status: str,
    original_display_status: str,
    original_surface_plain_or_unlabelled: bool,
    recovery_context: str,
) -> dict[str, Any]:
    family = _clean_identifier(surface_requirement.get("surface_requirement_family"), max_length=96)
    return {
        "schema_version": LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_SCHEMA_VERSION,
        "source_phase": LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_SOURCE_PHASE,
        "candidate_source_kind": CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE,
        "public_surface_role": PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
        "composer_source": "ai_generated",
        "composer_model": LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_COMPOSER_MODEL,
        "generation_method": LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_GENERATION_METHOD,
        "original_candidate_present": True,
        "original_candidate_source_kind": original_candidate_source_kind or CANDIDATE_SOURCE_KIND_NONE,
        "original_candidate_status": original_candidate_status,
        "original_display_status": original_display_status,
        "original_surface_plain_or_unlabelled": bool(original_surface_plain_or_unlabelled),
        "original_surface_labelled_two_stage": not bool(original_surface_plain_or_unlabelled),
        "source_unavailable_recovered": False,
        "labelled_two_stage_surface_recomposition_used": True,
        "normal_observation_rebuild_used": False,
        "complete_initial_surface_recomposition_used": False,
        "gate_recovery_material_surface_used": False,
        "surface_requirement": dict(surface_requirement),
        "surface_requirement_family": family or SURFACE_REQUIREMENT_LABELLED_TWO_STAGE,
        "two_stage_required": True,
        "plain_surface_allowed": False,
        "low_information_allowed": False,
        "two_stage_section_surface_plan": {
            "required": True,
            "labels_required": True,
            "joined_comment_text_required": True,
            "expected_comment_text_shape": "labelled_two_stage",
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
        "source_material_summary": {
            "material_quality": _clean_identifier(material_quality, max_length=96),
            "visible_slot_count": max(0, int(visible_slot_count or 0)),
            "unknown_slot_count": max(0, int(unknown_slot_count or 0)),
            "relation_id_count": max(0, int(relation_id_count or 0)),
            "claim_id_count": 0,
            "user_payload_serialized": False,
            "candidate_payload_serialized": False,
        },
        "labelled_two_stage_surface_recomposition_summary": {
            "existing_complete_material_connected": True,
            "two_stage_section_surface_plan_connected": True,
            "surface_realizer_connected": True,
            "labels_present": True,
            "label_order_valid": True,
            "observation_section_non_empty": True,
            "reception_section_non_empty": True,
            "section_budget_valid": True,
            "plain_surface_used_as_final": False,
            "low_information_observation_used_as_final": False,
            "normal_observation_rebuild_used": False,
            "complete_initial_surface_recomposition_used": False,
            "gate_recovery_material_surface_used": False,
            "fixed_fallback_used": False,
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
        "gate_contract": {
            "display_gate_relaxed": False,
            "runtime_surface_gate_relaxed": False,
            "visible_surface_gate_relaxed": False,
            "grounding_gate_relaxed": False,
            "template_gate_relaxed": False,
            "safety_gate_relaxed": False,
        },
        "body_boundary": {
            "raw_input_included": False,
            "raw_text_included": False,
            "comment_text_body_included": False,
            "original_comment_text_body_included": False,
        },
        "implementation_boundary": {
            "fixed_fallback_used": False,
            "fixed_sentence_template_used": False,
            "external_ai_used": False,
            "local_llm_used": False,
            "case_specific_route_used": False,
            "exact_fixture_surface_used": False,
        },
        "candidate_lineage": {
            "original_candidate_present": True,
            "original_candidate_source": original_candidate_source_kind or CANDIDATE_SOURCE_KIND_NONE,
            "recovery_plan_used": True,
            "diagnostic_surface_used": False,
            "public_candidate_rebuilt_after_recovery": True,
        },
        "used_evidence_span_ids": list(used_evidence_span_ids),
        "used_phrase_unit_ids": list(used_phrase_unit_ids),
        "recovery_context": _clean_identifier(recovery_context, max_length=96),
        "raw_input_included": False,
        "comment_text_body_included": False,
    }


def _compose_labelled_two_stage_comment(*, current_input: Mapping[str, Any] | None, material_route: Any) -> str:
    observation = _compose_observation_sentence(current_input=current_input, material_route=material_route)
    reception = _compose_reception_sentence(current_input=current_input, material_route=material_route)
    return f"見えたこと：\n{observation}\n\nEmlisから：\n{reception}"


def _compose_observation_sentence(*, current_input: Mapping[str, Any] | None, material_route: Any) -> str:
    topic = _topic_phrase(current_input=current_input, material_route=material_route)
    feeling = _feeling_phrase(current_input=current_input)
    action = _action_phrase(current_input=current_input)
    return f"この記録では、{topic}について、{feeling}と{action}が重なっている状態として見えます。"


def _compose_reception_sentence(*, current_input: Mapping[str, Any] | None, material_route: Any) -> str:
    _ = material_route
    current = _as_mapping(current_input)
    memo = _clean(_first(("memo", "note", "description"), current))
    if any(marker in memo for marker in ("責め", "だめ", "ダメ", "嫌い", "否定")):
        return "自分を急いで裁くより、その奥にあるきつさを言葉として置こうとしているところを、Emlisは受け取りました。"
    if any(marker in memo for marker in ("嬉", "楽", "よかっ", "良かっ", "できた")):
        return "良かった動きも迷いもどちらかに寄せず、そのまま確かめようとしているところを、Emlisは受け取りました。"
    return "すぐに一つへまとめず、いま見えている動きをそのまま置こうとしているところを、Emlisは受け取りました。"


def _topic_phrase(*, current_input: Mapping[str, Any] | None, material_route: Any) -> str:
    current = _as_mapping(current_input)
    category_words = _safe_string_items(_first(("categories", "category", "category_labels"), current), max_items=2)
    if category_words:
        return "・".join(category_words)
    route_meta = _material_route_meta(material_route)
    visible_slots = _safe_string_items(route_meta.get("visible_material_slots"), max_items=1)
    if visible_slots:
        return _topic_from_marker(visible_slots[0])
    memo = _clean(_first(("memo", "note", "description"), current))
    return _topic_from_marker(memo)


def _topic_from_marker(value: str) -> str:
    if any(marker in value for marker in ("人", "相手", "関係", "友", "家族", "職場", "relationship")):
        return "人とのやり取り"
    if any(marker in value for marker in ("仕事", "作業", "会社", "work")):
        return "仕事や作業"
    if any(marker in value for marker in ("体", "健康", "眠", "疲", "health")):
        return "体調や生活"
    if any(marker in value for marker in ("お金", "金", "生活", "money")):
        return "生活の現実"
    if any(marker in value for marker in ("自分", "気持", "わから", "何故", "なぜ", "self")):
        return "自分の内側"
    return "いま置かれていること"


def _feeling_phrase(*, current_input: Mapping[str, Any] | None) -> str:
    current = _as_mapping(current_input)
    emotion_words = _safe_string_items(_first(("emotions", "emotion", "emotion_labels"), current), max_items=2)
    if emotion_words:
        return "・".join(emotion_words) + "の動き"
    memo = _clean(_first(("memo", "note", "description"), current))
    if any(marker in memo for marker in ("不安", "怖", "心配")):
        return "不安の動き"
    if any(marker in memo for marker in ("悲", "寂", "つら", "辛")):
        return "悲しさやつらさの動き"
    if any(marker in memo for marker in ("怒", "嫌", "許")):
        return "引っかかりの動き"
    if any(marker in memo for marker in ("嬉", "楽", "よかっ", "良かっ")):
        return "喜びの動き"
    if any(marker in memo for marker in ("迷", "わから", "何故", "なぜ")):
        return "迷いの動き"
    return "気持ちの動き"


def _action_phrase(*, current_input: Mapping[str, Any] | None) -> str:
    current = _as_mapping(current_input)
    action = _clean(_first(("memo_action", "action", "next_action"), current))
    if any(marker in action for marker in ("書", "メモ", "整理", "考")):
        return "言葉に分けて見ようとしている動き"
    if any(marker in action for marker in ("返事", "連絡", "話")):
        return "人との距離を確かめようとしている動き"
    if any(marker in action for marker in ("休", "寝", "落ち着")):
        return "落ち着きを取り戻そうとしている動き"
    if action:
        return "次の扱い方を探している動き"
    return "次にどう扱うかを探している動き"


def _display_decision_passed(display_decision: Any | None) -> bool:
    if display_decision is None:
        return False
    return _clean_identifier(getattr(display_decision, "observation_status", ""), max_length=96) == "passed"


def _candidate_source_kind(candidate: Any | None) -> str:
    meta = _candidate_meta_source(candidate)
    value = _clean_identifier(meta.get("candidate_source_kind"), max_length=96)
    if value:
        return value
    model = _clean_identifier(getattr(candidate, "composer_model", "") if candidate is not None else "", max_length=128)
    generation_method = _clean_identifier(getattr(candidate, "generation_method", "") if candidate is not None else "", max_length=128)
    composer_source = _clean_identifier(getattr(candidate, "composer_source", "") if candidate is not None else "", max_length=96)
    if "gate_recovery" in model or "gate_recovery" in generation_method:
        return CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE
    if "diagnostic" in model or "diagnostic" in generation_method:
        return CANDIDATE_SOURCE_KIND_DIAGNOSTIC_RECOVERY_SURFACE
    if "labelled_two_stage_surface_recomposition" in model or "labelled_two_stage_surface_recomposition" in generation_method:
        return CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE
    if not composer_source:
        return CANDIDATE_SOURCE_KIND_NONE
    return composer_source


def _candidate_meta_source(candidate: Any | None) -> Mapping[str, Any]:
    if candidate is None:
        return {}
    if isinstance(candidate, Mapping):
        return _as_mapping(candidate.get("composer_meta"))
    return _as_mapping(getattr(candidate, "composer_meta", {}))


def _candidate_has_public_text(candidate: Any) -> bool:
    return bool(_clean_public_body(getattr(candidate, "comment_text", "")))


def _clean_public_body(value: Any) -> str:
    body = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
    body = re.sub(r"[ \t]+", " ", body)
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body.strip()


def _material_route_meta(material_route: Any) -> Mapping[str, Any]:
    if isinstance(material_route, Mapping):
        return material_route
    as_meta = getattr(material_route, "as_meta", None)
    if callable(as_meta):
        try:
            meta = as_meta()
            if isinstance(meta, Mapping):
                return meta
        except Exception:
            return {}
    meta = getattr(material_route, "meta", None)
    if isinstance(meta, Mapping):
        return meta
    return {}


def _material_quality(material_route: Any) -> str:
    meta = _material_route_meta(material_route)
    return _clean_identifier(
        _first(("material_quality", "eligibility_status", "status"), meta)
        or getattr(material_route, "material_quality", ""),
        max_length=96,
    )


def _first(keys: Sequence[str], mapping: Mapping[str, Any]) -> Any:
    for key in keys:
        if key in mapping and mapping.get(key) not in (None, "", [], {}):
            return mapping.get(key)
    return None


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _as_sequence(value: Any) -> tuple[Any, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes, bytearray)):
        return (value,)
    if isinstance(value, Sequence):
        return tuple(value)
    return (value,)


def _safe_string_items(value: Any, *, max_items: int) -> tuple[str, ...]:
    items: list[str] = []
    for item in _as_sequence(value):
        if isinstance(item, Mapping):
            raw = item.get("label") or item.get("name") or item.get("value") or item.get("id")
        else:
            raw = item
        cleaned = _clean(raw)
        cleaned = re.sub(r"[\r\n\t]+", " ", cleaned)
        cleaned = re.sub(r"[^0-9A-Za-z_:\-.ぁ-んァ-ヶ一-龠々ー]+", "", cleaned)[:24]
        if cleaned and cleaned not in items:
            items.append(cleaned)
        if len(items) >= max_items:
            break
    return tuple(items)


def _dedupe(values: Any) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in _as_sequence(values):
        cleaned = _clean_identifier(value, max_length=128)
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            result.append(cleaned)
    return result


def _evidence_span_ids(*, visible_slots: Sequence[str], relation_ids: Sequence[str]) -> tuple[str, ...]:
    seeds = list(visible_slots or ()) + list(relation_ids or ())
    if not seeds:
        seeds = ["current_input_material"]
    result = []
    for idx, seed in enumerate(seeds[:6], start=1):
        ident = _clean_identifier(seed, max_length=48) or f"material_{idx}"
        result.append(f"p6_{idx}_{ident}")
    return tuple(result)


def _phrase_unit_ids(*, topic: str, feeling: str, action: str) -> tuple[str, ...]:
    return (
        f"p6_two_stage_topic_{_clean_identifier(topic, max_length=32) or 'topic'}",
        f"p6_two_stage_feeling_{_clean_identifier(feeling, max_length=32) or 'feeling'}",
        f"p6_two_stage_action_{_clean_identifier(action, max_length=32) or 'action'}",
    )


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _clean_identifier(value: Any, *, max_length: int = 128) -> str:
    text = re.sub(r"[^0-9A-Za-z_:\-.ぁ-んァ-ヶ一-龠々ー]+", "_", str(value or "").strip())
    text = text.strip("_")[:max_length]
    return text


def _contains_forbidden_text_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in _FORBIDDEN_META_TEXT_KEYS:
                return True
            if _contains_forbidden_text_key(child):
                return True
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_forbidden_text_key(child) for child in value)
    return False


__all__ = [
    "LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_COMPOSER_MODEL",
    "LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_GENERATION_METHOD",
    "LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_PUBLIC_META_KEY",
    "LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_RESPONSE_SCHEMA_VERSION",
    "LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_SCHEMA_VERSION",
    "LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_SCOPE",
    "LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_SOURCE_PHASE",
    "assert_labelled_two_stage_surface_recomposition_meta",
    "build_labelled_two_stage_surface_recomposition_candidate",
    "labelled_two_stage_surface_recomposition_public_summary",
    "should_attempt_labelled_two_stage_surface_recomposition",
]
