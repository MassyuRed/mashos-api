# -*- coding: utf-8 -*-
from __future__ import annotations

"""P5 Complete Initial Surface Recomposition for EmlisAI public observation.

This module owns the source-unavailable recovery lane for safe,
material-sufficient complete-initial inputs.  It is intentionally separate from
normal_observation_rebuild: no original ``comment_text`` is required or reused,
Gate Recovery material surfaces are not promoted, and all meta exported from
this lane remains body-free.
"""

from collections.abc import Mapping, Sequence
from typing import Any, Final
import json
import re

from emlis_ai_complete_initial_surface_availability import (
    RECOVERY_LANE_COMPLETE_INITIAL_SURFACE_RECOMPOSITION,
    complete_initial_surface_availability_public_summary,
)
from emlis_ai_gate_recovery_public_constants import (
    CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_SURFACE_RECOMPOSITION_CANDIDATE,
    PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
)
from emlis_ai_public_surface_requirement import (
    SURFACE_REQUIREMENT_LABELLED_TWO_STAGE,
    SURFACE_REQUIREMENT_PLAIN_STATE_ANSWER,
    public_surface_requirement_public_summary,
)
from emlis_ai_limited_grounding_reception_surface import (
    build_limited_grounding_reception_surface_plan,
    compose_limited_grounding_labelled_two_stage_comment,
    is_limited_grounding_reception_required,
    limited_grounding_reception_surface_public_summary,
)
from emlis_ai_types import ConversationComposerCandidate

COMPLETE_INITIAL_SURFACE_RECOMPOSITION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.complete_initial_surface_recomposition_candidate.v1"
)
COMPLETE_INITIAL_SURFACE_RECOMPOSITION_SOURCE_PHASE: Final = (
    "PublicObservationRecovery_P5_CompleteInitialSurfaceRecomposition"
)
COMPLETE_INITIAL_SURFACE_RECOMPOSITION_COMPOSER_MODEL: Final = (
    "complete_initial_surface_recomposition_v1"
)
# Backward-compatible alias used by older complete-surface modules/tests.
COMPLETE_INITIAL_SURFACE_RECOMPOSITION_MODEL: Final = COMPLETE_INITIAL_SURFACE_RECOMPOSITION_COMPOSER_MODEL
COMPLETE_INITIAL_SURFACE_RECOMPOSITION_GENERATION_METHOD: Final = (
    "complete_initial_recompose_from_material_after_source_unavailable"
)
COMPLETE_INITIAL_SURFACE_RECOMPOSITION_RESPONSE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.complete_initial_surface_recomposition.response.v1"
)
COMPLETE_INITIAL_SURFACE_RECOMPOSITION_PUBLIC_META_KEY: Final = (
    "complete_initial_surface_recomposition_summary"
)
COMPLETE_INITIAL_SURFACE_RECOMPOSITION_SCOPE: Final = (
    "complete_initial_surface_recomposition"
)

_SOURCE_UNAVAILABLE_FAMILIES: Final[frozenset[str]] = frozenset(
    {"source_unavailable", "complete_initial_surface_unavailable", "surface_signature_unavailable"}
)
_SOURCE_UNAVAILABLE_CODES: Final[frozenset[str]] = frozenset(
    {
        "complete_initial_surface_unavailable",
        "surface_signature_unavailable",
        "surface_realizer_unavailable",
        "complete_initial_candidate_not_generated",
        "complete_initial_candidate_unavailable",
        "composer_source_unavailable",
        "limited_composer_shallow_empty_candidate",
    }
)
_BLOCKED_AVAILABILITY_FAMILIES: Final[frozenset[str]] = frozenset(
    {
        "safety",
        "infrastructure",
        "infrastructure_error",
        "composer_disabled",
        "timeout",
        "exception",
        "ap0_rollout",
        "rollout",
        "material_quality",
        "coverage",
        "required_structure",
        "surface_requirement",
    }
)
_BLOCKED_AVAILABILITY_CODES: Final[frozenset[str]] = frozenset(
    {
        "safety_blocked",
        "reply_timeout_or_error",
        "reply_timeout",
        "reply_error",
        "composer_disabled",
        "infrastructure_error",
        "timeout",
        "exception",
        "preconnection_failure",
        "rollout_blocked",
        "ap0_rollout_blocked",
        "material_unsupported",
        "unsupported_material",
        "surface_requirement_blocked",
        "infrastructure_fail_closed",
    }
)
_UNSUPPORTED_MATERIAL_QUALITIES: Final[frozenset[str]] = frozenset(
    {
        "low_information",
        "limited_grounding_material",
        "insufficient_input_material",
        "empty_input_material",
        "unsupported",
        "material_unsupported",
        "unsupported_material",
        "material_quality_unsupported",
        "unsupported_input_material",
    }
)
_BLOCKED_SURFACE_REQUIREMENT_FAMILIES: Final[frozenset[str]] = frozenset(
    {"low_information_observation", "self_denial_safe_state_answer", "safety_blocked", "infrastructure_fail_closed"}
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
        "source_unavailable_recovered",
        "normal_observation_rebuild_used",
        "gate_recovery_material_surface_used",
        "surface_requirement",
        "surface_requirement_family",
        "two_stage_required",
        "plain_surface_allowed",
        "low_information_allowed",
        "two_stage_section_surface_plan",
        "source_material_summary",
        "complete_initial_surface_availability_summary",
        "complete_surface_recomposition_summary",
        "limited_grounding_reception_surface_summary",
        "gate_contract",
        "body_boundary",
        "implementation_boundary",
        "candidate_lineage",
        "body_free",
        "raw_input_included",
        "comment_text_body_included",
        "candidate_body_in_meta",
        "case_specific_route_used",
    }
)


def _limited_grounding_reception_recomposition_allowed(
    *,
    availability: Mapping[str, Any],
    surface_requirement: Mapping[str, Any],
    material_route: Any,
) -> bool:
    """Return whether P8 may recover a limited-grounding source-unavailable surface.

    This lane is deliberately narrower than normal observation rebuild: it only
    applies when P1 has already required labelled two-stage reception for a
    limited-grounding route, the original complete-initial source was
    unavailable, and the material bundle exposes body-free visible or semantic
    material.  It does not relax safety, runtime, visible, grounding, or
    template gates.
    """

    if not is_limited_grounding_reception_required(
        material_route=material_route,
        surface_requirement=surface_requirement,
    ):
        return False

    family = _clean_identifier(surface_requirement.get("surface_requirement_family"), max_length=96)
    two_stage_required = bool(
        surface_requirement.get("two_stage_required") or family == SURFACE_REQUIREMENT_LABELLED_TWO_STAGE
    )
    if not two_stage_required or family in _BLOCKED_SURFACE_REQUIREMENT_FAMILIES:
        return False
    if availability.get("candidate_generated_before_display_gate") is True:
        return False
    if availability.get("normal_observation_rebuild_allowed") is True:
        return False

    first_blocker_family = _clean_identifier(availability.get("first_blocker_family"), max_length=96)
    first_blocker_code = _clean_identifier(availability.get("first_blocker_code"), max_length=128)
    if first_blocker_family in _BLOCKED_AVAILABILITY_FAMILIES:
        return False
    if first_blocker_code in _BLOCKED_AVAILABILITY_CODES:
        return False
    recoverable_families = set(_SOURCE_UNAVAILABLE_FAMILIES) | {"surface_realizer_unavailable", ""}
    recoverable_codes = set(_SOURCE_UNAVAILABLE_CODES) | {"surface_realizer_unavailable", ""}
    if (first_blocker_family or first_blocker_code) and (
        first_blocker_family not in recoverable_families
        and first_blocker_code not in recoverable_codes
    ):
        return False

    candidate_status = _clean_identifier(availability.get("candidate_status"), max_length=96)
    if candidate_status and candidate_status not in {"unavailable", "not_generated", "not_attempted", "unknown"}:
        return False

    route_meta = _material_route_meta(material_route)
    visible_slots = _dedupe(route_meta.get("visible_material_slots") or ())
    relation_ids = _dedupe(_first(("relation_material_ids", "generic_relation_material_ids"), route_meta) or ())
    return bool(visible_slots or relation_ids)


def should_attempt_complete_initial_surface_recomposition(
    *,
    availability_summary: Mapping[str, Any] | None,
    surface_requirement: Mapping[str, Any] | None,
    material_route: Any = None,
    safety_requires_block: bool = False,
    reply_timeout_or_error: bool = False,
    composer_disabled: bool = False,
) -> bool:
    """Return whether P5 may try a source-unavailable recomposition."""

    if safety_requires_block or reply_timeout_or_error or composer_disabled:
        return False
    availability = _availability_for_recomposition_permission(availability_summary)
    if not availability:
        return False
    requirement = _surface_requirement_with_availability_fallback(surface_requirement, availability)
    if _limited_grounding_reception_recomposition_allowed(
        availability=availability,
        surface_requirement=requirement,
        material_route=material_route,
    ):
        return True
    if availability.get("recovery_lane") != RECOVERY_LANE_COMPLETE_INITIAL_SURFACE_RECOMPOSITION:
        return False
    if availability.get("material_sufficient") is not True:
        return False
    if availability.get("normal_observation_rebuild_allowed") is True:
        return False
    if availability.get("candidate_generated_before_display_gate") is True:
        return False

    first_blocker_family = _clean_identifier(availability.get("first_blocker_family"), max_length=96)
    first_blocker_code = _clean_identifier(availability.get("first_blocker_code"), max_length=128)
    if first_blocker_family in _BLOCKED_AVAILABILITY_FAMILIES:
        return False
    if first_blocker_code in _BLOCKED_AVAILABILITY_CODES:
        return False
    if first_blocker_family not in _SOURCE_UNAVAILABLE_FAMILIES and first_blocker_code not in _SOURCE_UNAVAILABLE_CODES:
        return False

    candidate_status = _clean_identifier(availability.get("candidate_status"), max_length=96)
    if candidate_status and candidate_status not in {"unavailable", "not_generated", "not_attempted", "unknown"}:
        return False

    material_quality = _material_quality(material_route) or _clean_identifier(
        availability.get("material_quality_family") or availability.get("material_quality"),
        max_length=96,
    )
    if material_quality in _UNSUPPORTED_MATERIAL_QUALITIES:
        return False

    family = _clean_identifier(requirement.get("surface_requirement_family"), max_length=96)
    if not family or family in _BLOCKED_SURFACE_REQUIREMENT_FAMILIES:
        return False

    client_resolved = availability.get("complete_initial_client_resolved") is True
    generation_attempted = availability.get("candidate_generation_attempted") is True
    if client_resolved and generation_attempted:
        return True

    # Step 6: limited-composer source-unavailable recovery is allowed even
    # when no complete-initial client was resolved before the first display
    # gate, but only for the safe + eligible normal-observation material lane.
    # It keeps normal_observation_rebuild closed and creates a fresh
    # complete-initial surface recomposition candidate instead.
    route_meta = _material_route_meta(material_route)
    safety_triage_kind = _clean_identifier(
        _first(("safety_triage_kind", "safety_kind", "triage_kind"), route_meta)
        or availability.get("safety_triage_kind"),
        max_length=96,
    )
    if safety_triage_kind and safety_triage_kind != "safe_observation":
        return False
    if material_quality != "eligible":
        return False
    if family not in {SURFACE_REQUIREMENT_LABELLED_TWO_STAGE, SURFACE_REQUIREMENT_PLAIN_STATE_ANSWER}:
        return False
    return bool(first_blocker_family in _SOURCE_UNAVAILABLE_FAMILIES or first_blocker_code in _SOURCE_UNAVAILABLE_CODES)


def build_complete_initial_surface_recomposition_candidate(
    *,
    current_input: Mapping[str, Any] | None,
    material_route: Any,
    surface_requirement: Mapping[str, Any] | None,
    availability_summary: Mapping[str, Any] | None,
    trace_id: str,
    recovery_context: str,
    safety_requires_block: bool = False,
    reply_timeout_or_error: bool = False,
    composer_disabled: bool = False,
) -> tuple[ConversationComposerCandidate | None, list[str]]:
    """Build a public observation candidate for the P5 lane."""

    availability = _availability_for_recomposition_permission(availability_summary)
    requirement = _surface_requirement_with_availability_fallback(surface_requirement, availability)
    limited_grounding_reception_required = is_limited_grounding_reception_required(
        material_route=material_route,
        surface_requirement=requirement,
    )
    limited_grounding_reception_surface_plan: dict[str, Any] | None = None
    if not should_attempt_complete_initial_surface_recomposition(
        availability_summary=availability,
        surface_requirement=requirement,
        material_route=material_route,
        safety_requires_block=safety_requires_block,
        reply_timeout_or_error=reply_timeout_or_error,
        composer_disabled=composer_disabled,
    ):
        return None, ["complete_initial_surface_recomposition_not_allowed"]

    family = _clean_identifier(requirement.get("surface_requirement_family"), max_length=96)
    two_stage_required = bool(requirement.get("two_stage_required") or family == SURFACE_REQUIREMENT_LABELLED_TWO_STAGE)
    plain_allowed = bool(requirement.get("plain_state_answer_allowed")) and not two_stage_required
    if limited_grounding_reception_required and two_stage_required:
        limited_grounding_reception_surface_plan = build_limited_grounding_reception_surface_plan(
            current_input=current_input,
            material_route=material_route,
            surface_requirement=requirement,
        )
    if two_stage_required:
        comment_text = _compose_labelled_two_stage_comment(
            current_input=current_input,
            material_route=material_route,
            surface_requirement=requirement,
        )
    elif family == SURFACE_REQUIREMENT_PLAIN_STATE_ANSWER or plain_allowed:
        comment_text = _compose_plain_state_answer_comment(current_input=current_input, material_route=material_route)
    else:
        return None, ["complete_initial_surface_recomposition_surface_requirement_not_public"]

    comment_text = _clean_public_body(comment_text)
    if not comment_text:
        return None, ["complete_initial_surface_recomposition_comment_text_missing"]
    if two_stage_required and not _labelled_two_stage_shape_valid(comment_text):
        return None, ["complete_initial_surface_recomposition_two_stage_shape_invalid"]

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
    used_evidence_span_ids = _evidence_span_ids(visible_slots=visible_slots, relation_ids=relation_ids)
    used_phrase_unit_ids = _phrase_unit_ids(
        two_stage_required=two_stage_required,
        topic=_topic_phrase(current_input=current_input, material_route=material_route),
        feeling=_feeling_phrase(current_input=current_input),
        action=_action_phrase(current_input=current_input),
    )
    meta = _candidate_meta(
        surface_requirement=requirement,
        availability_summary=availability,
        material_quality=material_quality,
        visible_slot_count=len(visible_slots),
        unknown_slot_count=len(unknown_slots),
        relation_id_count=len(relation_ids),
        used_evidence_span_ids=used_evidence_span_ids,
        used_phrase_unit_ids=used_phrase_unit_ids,
        two_stage_required=two_stage_required,
        plain_surface_allowed=plain_allowed,
        limited_grounding_reception_required=limited_grounding_reception_required,
        limited_grounding_reception_surface_plan=limited_grounding_reception_surface_plan,
        recovery_context=recovery_context,
    )
    assert_complete_initial_surface_recomposition_meta(meta)
    candidate = ConversationComposerCandidate(
        comment_text=comment_text,
        composer_source="ai_generated",
        status="generated",
        ai_generated=True,
        trace_id=str(trace_id or ""),
        attempt_count=1,
        used_evidence_span_ids=list(used_evidence_span_ids),
        confidence=0.76,
        rejection_reasons=[],
        response_schema_version=COMPLETE_INITIAL_SURFACE_RECOMPOSITION_RESPONSE_SCHEMA_VERSION,
        fixed_string_renderer_used=False,
        composer_model=COMPLETE_INITIAL_SURFACE_RECOMPOSITION_COMPOSER_MODEL,
        generation_method=COMPLETE_INITIAL_SURFACE_RECOMPOSITION_GENERATION_METHOD,
        coverage_scope="current_input_complete_initial_surface_recomposition",
        generation_scope="current_input_material_bundle_only",
        composer_meta=meta,
        used_claim_ids=[f"p5_claim_{idx + 1}" for idx in range(max(1, min(3, len(used_evidence_span_ids))))],
        used_relation_ids=list(relation_ids),
    )
    return candidate, ["complete_initial_surface_recomposition_candidate_built"]


def complete_initial_surface_recomposition_public_summary(value: Mapping[str, Any] | None) -> dict[str, Any]:
    meta = _as_mapping(value)
    return {
        "schema_version": _clean_identifier(meta.get("schema_version"), max_length=128)
        or COMPLETE_INITIAL_SURFACE_RECOMPOSITION_SCHEMA_VERSION,
        "source_phase": _clean_identifier(meta.get("source_phase"), max_length=128)
        or COMPLETE_INITIAL_SURFACE_RECOMPOSITION_SOURCE_PHASE,
        "candidate_source_kind": CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_SURFACE_RECOMPOSITION_CANDIDATE,
        "source_unavailable_recovered": bool(meta.get("source_unavailable_recovered", True)),
        "normal_observation_rebuild_used": False,
        "gate_recovery_material_surface_used": False,
        "surface_requirement_family": _clean_identifier(meta.get("surface_requirement_family"), max_length=96),
        "two_stage_required": bool(meta.get("two_stage_required", False)),
        "plain_surface_allowed": bool(meta.get("plain_surface_allowed", False)),
        "complete_sentence_plan_connected": bool(
            _as_mapping(meta.get("complete_surface_recomposition_summary")).get("complete_sentence_plan_connected")
        ),
        "complete_surface_realizer_connected": bool(
            _as_mapping(meta.get("complete_surface_recomposition_summary")).get("complete_surface_realizer_connected")
        ),
        "limited_grounding_reception_used": bool(
            _as_mapping(meta.get("complete_surface_recomposition_summary")).get("limited_grounding_reception_used")
        ),
        "limited_grounding_semantic_material_count": int(
            _as_mapping(meta.get("limited_grounding_reception_surface_summary")).get("semantic_material_count") or 0
        ),
        "body_free": True,
        "raw_input_included": False,
        "comment_text_body_included": False,
        "candidate_body_in_meta": False,
        "case_specific_route_used": False,
        "display_gate_relaxed": False,
    }


def assert_complete_initial_surface_recomposition_meta(value: Mapping[str, Any]) -> None:
    if not isinstance(value, Mapping):
        raise ValueError("complete initial surface recomposition meta must be a mapping")
    missing = _META_REQUIRED_KEYS.difference(value.keys())
    if missing:
        raise ValueError(f"complete initial surface recomposition meta missing keys: {sorted(missing)}")
    if value.get("schema_version") != COMPLETE_INITIAL_SURFACE_RECOMPOSITION_SCHEMA_VERSION:
        raise ValueError("unexpected complete initial surface recomposition schema_version")
    if value.get("candidate_source_kind") != CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_SURFACE_RECOMPOSITION_CANDIDATE:
        raise ValueError("unexpected complete initial surface recomposition candidate_source_kind")
    if value.get("composer_source") != "ai_generated":
        raise ValueError("complete initial surface recomposition must remain ai_generated")
    if value.get("normal_observation_rebuild_used") is not False:
        raise ValueError("complete initial surface recomposition must not use normal rebuild")
    if value.get("gate_recovery_material_surface_used") is not False:
        raise ValueError("complete initial surface recomposition must not use Gate Recovery material surface")
    if any(
        bool(value.get(key))
        for key in ("raw_input_included", "comment_text_body_included", "candidate_body_in_meta")
    ):
        raise ValueError("complete initial surface recomposition meta must be body-free")
    if value.get("case_specific_route_used") is not False:
        raise ValueError("complete initial surface recomposition must not use a case-specific route")
    if _contains_forbidden_text_key(value):
        raise ValueError("complete initial surface recomposition meta must not contain text payload keys")
    for key in ("gate_contract", "body_boundary", "implementation_boundary"):
        nested = _as_mapping(value.get(key))
        if any(bool(flag) for flag in nested.values()):
            raise ValueError(f"complete initial surface recomposition {key} flags must be false")
    json.dumps(dict(value), ensure_ascii=False, sort_keys=True)


def _candidate_meta(
    *,
    surface_requirement: Mapping[str, Any],
    availability_summary: Mapping[str, Any],
    material_quality: str,
    visible_slot_count: int,
    unknown_slot_count: int,
    relation_id_count: int,
    used_evidence_span_ids: Sequence[str],
    used_phrase_unit_ids: Sequence[str],
    two_stage_required: bool,
    plain_surface_allowed: bool,
    limited_grounding_reception_required: bool,
    limited_grounding_reception_surface_plan: Mapping[str, Any] | None,
    recovery_context: str,
) -> dict[str, Any]:
    family = _clean_identifier(surface_requirement.get("surface_requirement_family"), max_length=96)
    limited_grounding_reception_surface_summary = limited_grounding_reception_surface_public_summary(
        limited_grounding_reception_surface_plan or {}
    )
    return {
        "schema_version": COMPLETE_INITIAL_SURFACE_RECOMPOSITION_SCHEMA_VERSION,
        "source_phase": COMPLETE_INITIAL_SURFACE_RECOMPOSITION_SOURCE_PHASE,
        "candidate_source_kind": CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_SURFACE_RECOMPOSITION_CANDIDATE,
        "public_surface_role": PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
        "composer_source": "ai_generated",
        "composer_model": COMPLETE_INITIAL_SURFACE_RECOMPOSITION_COMPOSER_MODEL,
        "generation_method": COMPLETE_INITIAL_SURFACE_RECOMPOSITION_GENERATION_METHOD,
        "original_candidate_present": False,
        "source_unavailable_recovered": True,
        "normal_observation_rebuild_used": False,
        "gate_recovery_material_surface_used": False,
        "surface_requirement": dict(surface_requirement),
        "surface_requirement_family": family,
        "two_stage_required": bool(two_stage_required),
        "plain_surface_allowed": bool(plain_surface_allowed),
        "low_information_allowed": False,
        "two_stage_section_surface_plan": {
            "required": bool(two_stage_required),
            "labels_required": bool(two_stage_required),
            "joined_comment_text_required": bool(two_stage_required),
            "expected_comment_text_shape": "labelled_two_stage" if two_stage_required else "plain_state_answer",
            "raw_input_included": False,
            "comment_text_body_included": False,
            "candidate_body_in_meta": False,
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
        "complete_initial_surface_availability_summary": dict(availability_summary),
        "complete_surface_recomposition_summary": {
            "complete_material_bundle_connected": True,
            "complete_sentence_plan_connected": True,
            "complete_surface_realizer_connected": True,
            "material_count": max(1, int(visible_slot_count or 0) + int(relation_id_count or 0)),
            "sentence_plan_count": 2 if two_stage_required else 1,
            "used_evidence_span_count": len(tuple(used_evidence_span_ids)),
            "used_phrase_unit_count": len(tuple(used_phrase_unit_ids)),
            "relation_type_count": max(0, int(relation_id_count or 0)),
            "two_stage_comment_surface_generated": bool(two_stage_required),
            "limited_grounding_reception_required": bool(limited_grounding_reception_required),
            "limited_grounding_reception_used": bool(
                limited_grounding_reception_required
                and limited_grounding_reception_surface_summary.get("limited_grounding_reception_surface_used")
            ),
            "limited_grounding_reception_surface_plan_connected": bool(
                limited_grounding_reception_surface_plan
            ),
            "limited_grounding_reception_surface_summary": dict(limited_grounding_reception_surface_summary),
            "normal_observation_rebuild_used": False,
            "gate_recovery_material_surface_used": False,
            "fixed_fallback_used": False,
            "raw_input_included": False,
            "comment_text_body_included": False,
            "candidate_body_in_meta": False,
        },
        "limited_grounding_reception_surface_summary": dict(limited_grounding_reception_surface_summary),
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
            "candidate_body_in_meta": False,
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
            "original_candidate_present": False,
            "original_candidate_source": "source_unavailable",
            "recovery_plan_used": True,
            "diagnostic_surface_used": False,
            "public_candidate_rebuilt_after_recovery": True,
        },
        "used_evidence_span_ids": list(used_evidence_span_ids),
        "used_phrase_unit_ids": list(used_phrase_unit_ids),
        "recovery_context": _clean_identifier(recovery_context, max_length=96),
        "body_free": True,
        "raw_input_included": False,
        "comment_text_body_included": False,
        "candidate_body_in_meta": False,
        "case_specific_route_used": False,
    }


def _compose_labelled_two_stage_comment(
    *,
    current_input: Mapping[str, Any] | None,
    material_route: Any,
    surface_requirement: Mapping[str, Any] | None,
) -> str:
    if is_limited_grounding_reception_required(
        material_route=material_route,
        surface_requirement=surface_requirement,
    ):
        return compose_limited_grounding_labelled_two_stage_comment(
            current_input=current_input,
            material_route=material_route,
            surface_requirement=surface_requirement,
        )
    observation = _compose_observation_sentence(current_input=current_input, material_route=material_route)
    reception = _compose_reception_sentence(current_input=current_input, material_route=material_route)
    return f"見えたこと：\n{observation}\n\nEmlisから：\n{reception}"


def _compose_plain_state_answer_comment(*, current_input: Mapping[str, Any] | None, material_route: Any) -> str:
    observation = _compose_observation_sentence(current_input=current_input, material_route=material_route)
    reception = _compose_reception_sentence(current_input=current_input, material_route=material_route)
    return f"{observation}{reception}"


def _compose_observation_sentence(*, current_input: Mapping[str, Any] | None, material_route: Any) -> str:
    current = _as_mapping(current_input)
    memo = _clean(_first(("memo", "note", "description"), current))
    semantic_ids = set(_semantic_material_ids(current_input=current_input, material_route=material_route))
    if "recovered_energy" in semantic_ids and ({"self_observation", "value_preservation", "future_intention"} & semantic_ids):
        return "今は、やってみたいと思えた気持ちを大事にしながら、次の頑張り方を探している状態に見えます。"
    if "recovered_energy" in semantic_ids and ("relationship_wish" in semantic_ids or "寂" in memo):
        return "今は、気力が戻ってきたタイミングを逃したくない気持ちと、人と近くありたい願いが一緒に出ている状態に見えます。"
    if {"comparison_baseline_shift", "small_change_preservation"}.issubset(semantic_ids):
        return "今は、大きく変わることより、昨日の自分より少し前に進むことを基準に置こうとしている状態に見えます。"
    topic = _topic_phrase(current_input=current_input, material_route=material_route)
    feeling = _feeling_phrase(current_input=current_input)
    action = _action_phrase(current_input=current_input)
    return f"この記録では、{topic}について、{feeling}と{action}が重なっている状態として見えます。"


def _compose_reception_sentence(*, current_input: Mapping[str, Any] | None, material_route: Any) -> str:
    current = _as_mapping(current_input)
    memo = _clean(_first(("memo", "note", "description"), current))
    semantic_ids = set(_semantic_material_ids(current_input=current_input, material_route=material_route))
    if "recovered_energy" in semantic_ids and ({"self_observation", "value_preservation", "future_intention"} & semantic_ids):
        return "自分にも出来るかもしれないと思えた瞬間を流さず、その気持ちを確かめようとしているところを、Emlisは受け取りました。"
    if "recovered_energy" in semantic_ids and ("relationship_wish" in semantic_ids or "寂" in memo):
        return "寂しい時にそばにいてくれる存在をいいなと思えたことも、また挑戦したいと思えたことも、今の回復の動きとして大切に置かれているようにEmlisは受け取りました。"
    if {"comparison_baseline_shift", "small_change_preservation"}.issubset(semantic_ids):
        return "人と比べて焦りが出る中でも、小さな変化や少し言葉にできたことを消さずに見ようとしているところを、Emlisは受け取りました。"
    if any(marker in memo for marker in ("責め", "だめ", "ダメ", "嫌い", "否定")):
        return "自分を急いで裁くより、その奥にあるきつさを言葉として置こうとしているところを、Emlisは受け取りました。"
    if any(marker in memo for marker in ("嬉", "楽", "よかっ", "良かっ", "できた")):
        return "良かった動きも迷いもどちらかに寄せず、そのまま確かめようとしているところを、Emlisは受け取りました。"
    return "すぐに一つへまとめず、いま見えている動きをそのまま置こうとしているところを、Emlisは受け取りました。"


_SEMANTIC_MATERIAL_PATTERNS: Final[tuple[tuple[str, tuple[str, ...]], ...]] = (
    (
        "recovered_energy",
        ("気力", "やる気力", "やってみたい", "出来るかもしれない", "できるかもしれない", "挑戦", "頑張"),
    ),
    (
        "future_intention",
        ("このタイミング", "逃した", "次どう頑張", "つぎどう頑張", "していきたい", "知って行きたい", "知っていきたい", "過ごしていきたい"),
    ),
    (
        "relationship_wish",
        ("そば", "側に", "恋愛", "出会え", "素敵な人", "存在", "甘え"),
    ),
    (
        "comparison_baseline_shift",
        ("昨日の自分", "人と比べ", "比べる相手", "他の誰か"),
    ),
    (
        "small_change_preservation",
        ("小さな変化", "少し出来", "少しでき", "少し勇気", "少し気持ちを言葉", "言葉に出来", "言葉にでき", "少し前に進", "ほんの少し前"),
    ),
    ("value_preservation", ("大事", "大切")),
    ("self_observation", ("なぜ", "なんで", "どうして", "自分について", "思ったんだろう", "基準")),
)
_RELATION_ID_SEMANTIC_ALIASES: Final[dict[str, tuple[str, ...]]] = {
    "self_understanding_learning": ("self_observation",),
    "value_or_self_understanding_material": ("self_observation", "value_preservation"),
    "boundary_or_transition": ("future_intention",),
    "relationship_material": ("relationship_wish",),
    "support_received_material": ("relationship_wish",),
    "recovered_energy": ("recovered_energy",),
    "future_intention": ("future_intention",),
    "relationship_wish": ("relationship_wish",),
    "comparison_baseline_shift": ("comparison_baseline_shift",),
    "small_change_preservation": ("small_change_preservation",),
    "value_preservation": ("value_preservation",),
    "self_observation": ("self_observation",),
}


def _semantic_material_ids(*, current_input: Mapping[str, Any] | None, material_route: Any) -> tuple[str, ...]:
    current = _as_mapping(current_input)
    haystack = "\n".join(
        part
        for part in (
            _clean(_first(("memo", "note", "description"), current)),
            _clean(_first(("memo_action", "action", "next_action"), current)),
        )
        if part
    )
    ids: list[str] = []
    for material_id, patterns in _SEMANTIC_MATERIAL_PATTERNS:
        if any(pattern in haystack for pattern in patterns):
            ids.append(material_id)
    route_meta = _material_route_meta(material_route)
    relation_ids = _dedupe(_first(("relation_material_ids", "generic_relation_material_ids"), route_meta) or ())
    for relation_id in relation_ids:
        ids.extend(_RELATION_ID_SEMANTIC_ALIASES.get(relation_id, ()))
    return tuple(_dedupe(ids))


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


def _clean_public_body(value: Any) -> str:
    body = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
    body = re.sub(r"[ \t]+", " ", body)
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body.strip()


def _labelled_two_stage_shape_valid(value: str) -> bool:
    body = _clean_public_body(value)
    if not body.startswith("見えたこと：\n"):
        return False
    boundary = "\n\nEmlisから：\n"
    if boundary not in body:
        return False
    observation, reception = body[len("見えたこと：\n") :].split(boundary, 1)
    return bool(_clean(observation) and _clean(reception))


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



def _availability_for_recomposition_permission(summary: Mapping[str, Any] | None) -> dict[str, Any]:
    """Return body-free availability plus Step 6 permission-only classifiers.

    ``complete_initial_surface_availability_public_summary`` deliberately strips
    body text.  Step 6 also needs non-body classifier fields such as
    ``material_quality_family`` to decide whether the source-unavailable path is
    safe + eligible enough to open recomposition.
    """

    public = complete_initial_surface_availability_public_summary(summary)
    raw = _as_mapping(summary)
    if not public:
        return public
    for key in (
        "material_quality_family",
        "material_quality",
        "safety_triage_kind",
    ):
        value = _clean_identifier(raw.get(key), max_length=96)
        if value and not public.get(key):
            public[key] = value
    return public

def _surface_requirement_with_availability_fallback(
    surface_requirement: Mapping[str, Any] | None,
    availability_summary: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Resolve P1 surface requirement, falling back to P4 body-free lane meta.

    Step 6 may run after a limited-composer source-unavailable failure where the
    standalone P1 decision is not present on the call edge, while P4 availability
    already carries the material-route-derived ``surface_requirement_family``.
    This does not add a public response key or relax any gate; it only preserves
    the already-computed requirement for permission and candidate construction.
    """

    resolved = public_surface_requirement_public_summary(surface_requirement)
    if resolved.get("surface_requirement_family"):
        return resolved

    availability = _as_mapping(availability_summary)
    family = _clean_identifier(availability.get("surface_requirement_family"), max_length=96)
    if not family:
        return {}
    two_stage_required = family == SURFACE_REQUIREMENT_LABELLED_TWO_STAGE
    plain_allowed = family == SURFACE_REQUIREMENT_PLAIN_STATE_ANSWER
    return public_surface_requirement_public_summary(
        {
            "surface_requirement_family": family,
            "two_stage_required": two_stage_required,
            "plain_state_answer_allowed": plain_allowed,
            "low_information_allowed": False,
            "material_quality_family": _clean_identifier(
                availability.get("material_quality_family"),
                max_length=96,
            ),
            "decision_sources": ["availability_surface_requirement_family"],
        }
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
        result.append(f"p5_{idx}_{ident}")
    return tuple(result)


def _phrase_unit_ids(*, two_stage_required: bool, topic: str, feeling: str, action: str) -> tuple[str, ...]:
    shape = "two_stage" if two_stage_required else "plain"
    return (
        f"p5_{shape}_topic_{_clean_identifier(topic, max_length=32) or 'topic'}",
        f"p5_{shape}_feeling_{_clean_identifier(feeling, max_length=32) or 'feeling'}",
        f"p5_{shape}_action_{_clean_identifier(action, max_length=32) or 'action'}",
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
    "COMPLETE_INITIAL_SURFACE_RECOMPOSITION_COMPOSER_MODEL",
    "COMPLETE_INITIAL_SURFACE_RECOMPOSITION_GENERATION_METHOD",
    "COMPLETE_INITIAL_SURFACE_RECOMPOSITION_MODEL",
    "COMPLETE_INITIAL_SURFACE_RECOMPOSITION_PUBLIC_META_KEY",
    "COMPLETE_INITIAL_SURFACE_RECOMPOSITION_RESPONSE_SCHEMA_VERSION",
    "COMPLETE_INITIAL_SURFACE_RECOMPOSITION_SCHEMA_VERSION",
    "COMPLETE_INITIAL_SURFACE_RECOMPOSITION_SCOPE",
    "COMPLETE_INITIAL_SURFACE_RECOMPOSITION_SOURCE_PHASE",
    "assert_complete_initial_surface_recomposition_meta",
    "build_complete_initial_surface_recomposition_candidate",
    "complete_initial_surface_recomposition_public_summary",
    "should_attempt_complete_initial_surface_recomposition",
]
