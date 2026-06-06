# -*- coding: utf-8 -*-
from __future__ import annotations

"""P3 product-surface validation for EmlisAI public observation recovery.

This module separates RN visibility from product surface validity.  It validates
whether a public ``comment_text`` satisfies the surface requirement resolved by
P1 without changing RN/API/DB contracts, without relaxing gates, and without
serializing raw input or generated body text into meta.
"""

from collections.abc import Mapping, Sequence
from typing import Any, Final
import json

from emlis_ai_gate_recovery_public_constants import (
    ALLOWED_PUBLIC_CANDIDATE_SOURCE_KINDS,
    CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE,
    CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_COMPOSER,
    CANDIDATE_SOURCE_KIND_COMPLETE_SELF_REPAIR_CANDIDATE,
    CANDIDATE_SOURCE_KIND_DIAGNOSTIC_RECOVERY_SURFACE,
    CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE,
    CANDIDATE_SOURCE_KIND_LIMITED_COMPOSER,
    CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER,
    CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE,
    CANDIDATE_SOURCE_KIND_SELF_DENIAL_SAFE_STATE_ANSWER,
    FORBIDDEN_PUBLIC_CANDIDATE_SOURCE_KINDS,
)
from emlis_ai_public_surface_requirement import (
    LABELLED_TWO_STAGE_RECEPTION_BOUNDARY,
    SURFACE_REQUIREMENT_INFRASTRUCTURE_FAIL_CLOSED,
    SURFACE_REQUIREMENT_LABELLED_TWO_STAGE,
    SURFACE_REQUIREMENT_LOW_INFORMATION_OBSERVATION,
    SURFACE_REQUIREMENT_PLAIN_STATE_ANSWER,
    SURFACE_REQUIREMENT_SAFETY_BLOCKED,
    SURFACE_REQUIREMENT_SELF_DENIAL_SAFE_STATE_ANSWER,
    is_labelled_two_stage_comment_text_shape,
    labelled_two_stage_comment_text_shape_summary,
    public_surface_requirement_public_summary,
)

PRODUCT_SURFACE_VALIDATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.product_surface_validation.v1"
)
PRODUCT_SURFACE_VALIDATION_SOURCE_PHASE: Final = (
    "PublicObservationRecovery_P3_ProductSurfaceValidation"
)
PRODUCT_SURFACE_VALIDATION_PUBLIC_META_KEY: Final = "product_surface_validation"

CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_SURFACE_RECOMPOSITION_CANDIDATE: Final = (
    "complete_initial_surface_recomposition_candidate"
)
CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE: Final = (
    "labelled_two_stage_surface_recomposition_candidate"
)

PRODUCT_SURFACE_VALID: Final = "product_surface_valid"
PRODUCT_SURFACE_INVALID_PUBLIC_FEEDBACK_NOT_REACHED: Final = (
    "product_surface_invalid_public_feedback_not_reached"
)
PRODUCT_SURFACE_INVALID_RN_NOT_VISIBLE: Final = "product_surface_invalid_rn_not_visible"
PRODUCT_SURFACE_INVALID_PUBLIC_GATE_BLOCKED: Final = (
    "product_surface_invalid_public_gate_blocked"
)
PRODUCT_SURFACE_INVALID_CANDIDATE_SOURCE_NOT_ALLOWED: Final = (
    "product_surface_invalid_candidate_source_not_allowed"
)
PRODUCT_SURFACE_INVALID_PLAIN_USED_FOR_TWO_STAGE_REQUIRED: Final = (
    "product_surface_invalid_plain_used_for_two_stage_required"
)
PRODUCT_SURFACE_INVALID_TWO_STAGE_SHAPE_REQUIRED: Final = (
    "product_surface_invalid_two_stage_shape_required"
)
PRODUCT_SURFACE_INVALID_LOW_INFORMATION_MISROUTE: Final = (
    "product_surface_invalid_low_information_misroute"
)
PRODUCT_SURFACE_INVALID_PLAIN_STATE_ANSWER_NOT_ALLOWED: Final = (
    "product_surface_invalid_plain_state_answer_not_allowed"
)
PRODUCT_SURFACE_INVALID_SURFACE_REQUIREMENT_UNSATISFIED: Final = (
    "product_surface_invalid_surface_requirement_unsatisfied"
)

# Public aliases used by P3 tests and ProductQuality integration.
PRODUCT_SURFACE_BLOCKER_NONE: Final = PRODUCT_SURFACE_VALID
PRODUCT_SURFACE_BLOCKER_PUBLIC_FEEDBACK_ABSENT: Final = PRODUCT_SURFACE_INVALID_PUBLIC_FEEDBACK_NOT_REACHED
PRODUCT_SURFACE_BLOCKER_RN_NOT_VISIBLE: Final = PRODUCT_SURFACE_INVALID_RN_NOT_VISIBLE
PRODUCT_SURFACE_BLOCKER_PUBLIC_GATE_BLOCKED: Final = PRODUCT_SURFACE_INVALID_PUBLIC_GATE_BLOCKED
PRODUCT_SURFACE_BLOCKER_CANDIDATE_SOURCE_NOT_ALLOWED: Final = PRODUCT_SURFACE_INVALID_CANDIDATE_SOURCE_NOT_ALLOWED
PRODUCT_SURFACE_BLOCKER_PLAIN_USED_FOR_TWO_STAGE_REQUIRED: Final = (
    PRODUCT_SURFACE_INVALID_PLAIN_USED_FOR_TWO_STAGE_REQUIRED
)
PRODUCT_SURFACE_BLOCKER_TWO_STAGE_SHAPE_REQUIRED: Final = PRODUCT_SURFACE_INVALID_TWO_STAGE_SHAPE_REQUIRED
PRODUCT_SURFACE_BLOCKER_TWO_STAGE_SHAPE: Final = PRODUCT_SURFACE_INVALID_TWO_STAGE_SHAPE_REQUIRED
PRODUCT_SURFACE_BLOCKER_LOW_INFORMATION_MISROUTE: Final = PRODUCT_SURFACE_INVALID_LOW_INFORMATION_MISROUTE
PRODUCT_SURFACE_BLOCKER_PLAIN_STATE_ANSWER_NOT_ALLOWED: Final = PRODUCT_SURFACE_INVALID_PLAIN_STATE_ANSWER_NOT_ALLOWED
PRODUCT_SURFACE_BLOCKER_SURFACE_REQUIREMENT_UNSATISFIED: Final = PRODUCT_SURFACE_INVALID_SURFACE_REQUIREMENT_UNSATISFIED
PRODUCT_SURFACE_BLOCKER_SURFACE_REQUIREMENT_UNSUPPORTED: Final = PRODUCT_SURFACE_INVALID_SURFACE_REQUIREMENT_UNSATISFIED

_BLOCKER_FAMILY_NONE: Final = ""
_BLOCKER_FAMILY_PUBLIC_FEEDBACK: Final = "public_feedback_contract"
_BLOCKER_FAMILY_RN_VISIBLE: Final = "rn_visible_contract"
_BLOCKER_FAMILY_PUBLIC_GATE: Final = "public_gate"
_BLOCKER_FAMILY_CANDIDATE_SOURCE: Final = "candidate_source"
_BLOCKER_FAMILY_TWO_STAGE_SHAPE: Final = "two_stage_shape_required"
_BLOCKER_FAMILY_LOW_INFORMATION: Final = "low_information_misroute"
_BLOCKER_FAMILY_PLAIN_STATE_ANSWER: Final = "plain_state_answer_contract"
_BLOCKER_FAMILY_SURFACE_REQUIREMENT: Final = "surface_requirement"

_FUTURE_PUBLIC_CANDIDATE_SOURCE_KINDS: Final[frozenset[str]] = frozenset(
    {
        CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_SURFACE_RECOMPOSITION_CANDIDATE,
        CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE,
    }
)
_LOW_INFORMATION_SOURCE_KINDS: Final[frozenset[str]] = frozenset(
    {CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER}
)
_ALLOWED_SURFACE_REQUIREMENT_FAMILIES: Final[frozenset[str]] = frozenset(
    {
        SURFACE_REQUIREMENT_LABELLED_TWO_STAGE,
        SURFACE_REQUIREMENT_PLAIN_STATE_ANSWER,
        SURFACE_REQUIREMENT_LOW_INFORMATION_OBSERVATION,
        SURFACE_REQUIREMENT_SELF_DENIAL_SAFE_STATE_ANSWER,
        SURFACE_REQUIREMENT_SAFETY_BLOCKED,
        SURFACE_REQUIREMENT_INFRASTRUCTURE_FAIL_CLOSED,
    }
)
_PUBLIC_CONTRACT_KEYS: Final[tuple[str, ...]] = (
    "public_response_key_added",
    "rn_visible_contract_changed",
    "response_shape_changed",
    "api_route_changed",
    "db_physical_name_changed",
)
_GATE_POLICY_KEYS: Final[tuple[str, ...]] = (
    "display_gate_relaxed",
    "runtime_surface_gate_relaxed",
    "visible_surface_gate_relaxed",
    "grounding_gate_relaxed",
    "template_gate_relaxed",
    "safety_gate_relaxed",
)
_GATE_VALIDATION_KEYS: Final[tuple[str, ...]] = (
    "public_gate_blocked",
    "visible_surface_gate_blocked",
    "runtime_surface_gate_blocked",
    "display_gate_blocked",
    "state_answer_gate_blocked",
    "two_stage_gate_blocked",
    "first_blocker_family",
    "first_blocker_code",
    "blocking_codes",
    "body_free",
    "raw_input_included",
    "comment_text_body_included",
)
_SHAPE_KEYS: Final[tuple[str, ...]] = (
    "labels_present",
    "label_order_valid",
    "observation_section_non_empty",
    "reception_section_non_empty",
    "section_budget_checked",
    "section_budget_valid",
    "comment_text_body_included",
)
_ORIGIN_KEYS: Final[tuple[str, ...]] = (
    "candidate_source_kind",
    "public_candidate_source_allowed",
    "gate_recovery_material_surface_used_as_public_body",
    "diagnostic_recovery_surface_used_as_public_body",
    "normal_observation_rebuild_used",
    "complete_initial_surface_recomposition_used",
    "labelled_two_stage_recomposition_used",
    "low_information_observation_used",
    "body_free",
    "raw_input_included",
    "comment_text_body_included",
)
_REQUIRED_SUMMARY_KEYS: Final[frozenset[str]] = frozenset(
    {
        "schema_version",
        "source_phase",
        "public_reached",
        "rn_visible",
        "public_feedback_inclusion_contract_passed",
        "product_surface_valid",
        "surface_requirement_family",
        "surface_requirement_satisfied",
        "surface_requirement",
        "two_stage_required",
        "plain_state_answer_allowed",
        "low_information_allowed",
        "plain_surface_used",
        "plain_surface_allowed",
        "low_information_surface_used",
        "labelled_two_stage_shape",
        "candidate_source_kind",
        "composer_source",
        "candidate_status",
        "candidate_generated_before_display_gate",
        "surface_origin",
        "gate_recovery_material_surface_used_as_public_body",
        "diagnostic_recovery_surface_used_as_public_body",
        "normal_observation_rebuild_used",
        "complete_initial_surface_recomposition_used",
        "labelled_two_stage_recomposition_used",
        "low_information_observation_used",
        "gate_validation",
        "blocker_family",
        "blocker_code",
        "decision_reasons",
        "public_contract",
        "gate_policy",
        "body_free",
        "raw_input_included",
        "comment_text_body_included",
    }
)
_VALID_BLOCKER_CODES: Final[frozenset[str]] = frozenset(
    {
        PRODUCT_SURFACE_VALID,
        PRODUCT_SURFACE_INVALID_PUBLIC_FEEDBACK_NOT_REACHED,
        PRODUCT_SURFACE_INVALID_RN_NOT_VISIBLE,
        PRODUCT_SURFACE_INVALID_PUBLIC_GATE_BLOCKED,
        PRODUCT_SURFACE_INVALID_CANDIDATE_SOURCE_NOT_ALLOWED,
        PRODUCT_SURFACE_INVALID_PLAIN_USED_FOR_TWO_STAGE_REQUIRED,
        PRODUCT_SURFACE_INVALID_TWO_STAGE_SHAPE_REQUIRED,
        PRODUCT_SURFACE_INVALID_LOW_INFORMATION_MISROUTE,
        PRODUCT_SURFACE_INVALID_PLAIN_STATE_ANSWER_NOT_ALLOWED,
        PRODUCT_SURFACE_INVALID_SURFACE_REQUIREMENT_UNSATISFIED,
    }
)
_BODY_FORBIDDEN_EXACT_KEYS: Final[frozenset[str]] = frozenset(
    {
        "raw_input",
        "rawInput",
        "raw_text",
        "rawText",
        "input_text",
        "inputText",
        "user_input",
        "userInput",
        "current_input",
        "currentInput",
        "memo",
        "memo_text",
        "memoText",
        "memo_action",
        "memoAction",
        "comment_text",
        "commentText",
        "comment_text_body",
        "commentTextBody",
        "candidate_comment_text",
        "candidateCommentText",
        "public_comment_text",
        "publicCommentText",
        "observation_text",
        "observationText",
        "reception_text",
        "receptionText",
        "evidence_text",
        "evidenceText",
        "body",
        "text",
        "candidate_body",
        "candidateBody",
        "surface_body",
        "surfaceBody",
        "surface_text",
        "surfaceText",
    }
)


def build_product_surface_validation_summary(
    *,
    input_feedback_included: bool | None = None,
    comment_text: Any = "",
    emlis_ai_public_meta: Mapping[str, Any] | None = None,
    public_meta: Mapping[str, Any] | None = None,
    surface_requirement: Mapping[str, Any] | None = None,
    candidate_generation_summary: Mapping[str, Any] | None = None,
    candidate_generation: Mapping[str, Any] | None = None,
    gate_validation_summary: Mapping[str, Any] | None = None,
    public_reached: bool | None = None,
    normal_observation_rebuild_used: bool | None = None,
) -> dict[str, Any]:
    """Return a body-free P3 product-surface validation summary.

    ``comment_text`` is inspected for structural booleans only.  It is never
    copied into the returned payload.
    """

    public = _as_mapping(emlis_ai_public_meta if emlis_ai_public_meta is not None else public_meta)
    generation = _as_mapping(
        candidate_generation_summary if candidate_generation_summary is not None else candidate_generation
    )
    requirement = _requirement_summary(surface_requirement or resolve_product_surface_requirement_from_sources(public, generation))
    gate_validation = _gate_validation_summary(gate_validation_summary, public_meta=public)

    observation_status = _clean_identifier(
        public.get("observation_status")
        or public.get("public_observation_status")
        or generation.get("observation_status"),
        max_length=64,
    )
    comment_present = bool(str(comment_text or "").strip())
    public_reached_bool = bool(
        input_feedback_included if input_feedback_included is not None else (
            public_reached if public_reached is not None else observation_status == "passed"
        )
    )
    public_gate_blocked = bool(gate_validation["public_gate_blocked"])
    rn_visible = bool(
        public_reached_bool
        and observation_status == "passed"
        and comment_present
        and not public_gate_blocked
    )
    public_feedback_contract_passed = bool(rn_visible)

    surface_family = _surface_family(requirement.get("surface_requirement_family"))
    two_stage_required = bool(requirement.get("two_stage_required")) or surface_family == SURFACE_REQUIREMENT_LABELLED_TWO_STAGE
    plain_allowed_by_requirement = bool(requirement.get("plain_state_answer_allowed"))
    low_information_allowed = bool(requirement.get("low_information_allowed"))

    candidate_source_kind = _candidate_source_kind(generation, public)
    composer_source = _clean_identifier(
        generation.get("composer_source") or public.get("composer_source"),
        max_length=96,
    )
    candidate_status = _clean_identifier(
        generation.get("candidate_status") or generation.get("status") or public.get("candidate_status"),
        max_length=96,
    )
    candidate_generated_before_display_gate = _candidate_generated_before_display_gate(
        generation=generation,
        candidate_status=candidate_status,
        composer_source=composer_source,
    )

    labelled_shape = _labelled_shape_summary(comment_text)
    labelled_shape_valid = bool(
        labelled_shape["labels_present"]
        and labelled_shape["label_order_valid"]
        and labelled_shape["observation_section_non_empty"]
        and labelled_shape["reception_section_non_empty"]
        and labelled_shape["section_budget_valid"]
    )
    low_information_surface_used = _is_low_information_surface(
        candidate_source_kind=candidate_source_kind,
        surface_family=surface_family,
        generation=generation,
        public_meta=public,
    )
    plain_surface_used = bool(
        rn_visible
        and not labelled_shape_valid
        and not low_information_surface_used
        and surface_family not in {SURFACE_REQUIREMENT_SAFETY_BLOCKED, SURFACE_REQUIREMENT_INFRASTRUCTURE_FAIL_CLOSED}
    )
    plain_surface_allowed = bool(
        plain_allowed_by_requirement
        and not two_stage_required
        and surface_family in {SURFACE_REQUIREMENT_PLAIN_STATE_ANSWER, SURFACE_REQUIREMENT_SELF_DENIAL_SAFE_STATE_ANSWER}
    )

    origin = _surface_origin_summary(candidate_source_kind, normal_observation_rebuild_used=normal_observation_rebuild_used)
    public_candidate_source_allowed = bool(origin["public_candidate_source_allowed"])
    surface_requirement_satisfied = _surface_requirement_satisfied(
        rn_visible=rn_visible,
        surface_family=surface_family,
        two_stage_required=two_stage_required,
        plain_surface_allowed=plain_surface_allowed,
        low_information_allowed=low_information_allowed,
        labelled_shape_valid=labelled_shape_valid,
        low_information_surface_used=low_information_surface_used,
        candidate_source_kind=candidate_source_kind,
        public_candidate_source_allowed=public_candidate_source_allowed,
    )
    blocker_family, blocker_code = _blocker(
        public_reached=public_reached_bool,
        rn_visible=rn_visible,
        public_gate_blocked=public_gate_blocked,
        public_candidate_source_allowed=public_candidate_source_allowed,
        two_stage_required=two_stage_required,
        plain_surface_used=plain_surface_used,
        labelled_shape_valid=labelled_shape_valid,
        low_information_surface_used=low_information_surface_used,
        low_information_allowed=low_information_allowed,
        plain_surface_allowed=plain_surface_allowed,
        surface_requirement_satisfied=surface_requirement_satisfied,
        surface_family=surface_family,
        candidate_source_kind=candidate_source_kind,
        gate_validation=gate_validation,
    )
    product_surface_valid = bool(rn_visible and surface_requirement_satisfied and blocker_code == PRODUCT_SURFACE_VALID)

    summary = {
        "schema_version": PRODUCT_SURFACE_VALIDATION_SCHEMA_VERSION,
        "source_phase": PRODUCT_SURFACE_VALIDATION_SOURCE_PHASE,
        "public_reached": public_reached_bool,
        "rn_visible": rn_visible,
        "public_feedback_inclusion_contract_passed": public_feedback_contract_passed,
        "product_surface_valid": product_surface_valid,
        "surface_requirement_family": surface_family,
        "surface_requirement_satisfied": bool(surface_requirement_satisfied),
        "surface_requirement": requirement,
        "two_stage_required": two_stage_required,
        "plain_state_answer_allowed": plain_allowed_by_requirement,
        "low_information_allowed": low_information_allowed,
        "plain_surface_used": plain_surface_used,
        "plain_surface_allowed": plain_surface_allowed,
        "low_information_surface_used": low_information_surface_used,
        "labelled_two_stage_shape": labelled_shape,
        "candidate_source_kind": candidate_source_kind,
        "composer_source": composer_source,
        "candidate_status": candidate_status,
        "candidate_generated_before_display_gate": candidate_generated_before_display_gate,
        "surface_origin": origin,
        "gate_recovery_material_surface_used_as_public_body": bool(origin["gate_recovery_material_surface_used_as_public_body"]),
        "diagnostic_recovery_surface_used_as_public_body": bool(origin["diagnostic_recovery_surface_used_as_public_body"]),
        "normal_observation_rebuild_used": bool(origin["normal_observation_rebuild_used"]),
        "complete_initial_surface_recomposition_used": bool(origin["complete_initial_surface_recomposition_used"]),
        "labelled_two_stage_recomposition_used": bool(origin["labelled_two_stage_recomposition_used"]),
        "low_information_observation_used": bool(origin["low_information_observation_used"]),
        "gate_validation": gate_validation,
        "blocker_family": blocker_family,
        "blocker_code": blocker_code,
        "decision_reasons": _decision_reasons(
            product_surface_valid=product_surface_valid,
            blocker_code=blocker_code,
            surface_family=surface_family,
            two_stage_required=two_stage_required,
            plain_surface_used=plain_surface_used,
            low_information_surface_used=low_information_surface_used,
            candidate_source_kind=candidate_source_kind,
            gate_validation=gate_validation,
        ),
        "public_contract": _false_public_contract(),
        "gate_policy": _false_gate_policy(),
        "body_free": True,
        "raw_input_included": False,
        "comment_text_body_included": False,
    }
    assert_product_surface_validation_summary(summary)
    return summary


def product_surface_validation_public_summary(
    summary: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Return the body-free subset safe for public/ProductQuality meta."""

    source = _as_mapping(summary)
    if not source:
        return {}
    blocker_code = _clean_identifier(source.get("blocker_code"), max_length=128)
    if not blocker_code:
        blocker_code = PRODUCT_SURFACE_VALID if bool(source.get("product_surface_valid")) else ""
    payload = {
        "schema_version": _clean_identifier(source.get("schema_version"), max_length=128)
        or PRODUCT_SURFACE_VALIDATION_SCHEMA_VERSION,
        "source_phase": _clean_identifier(source.get("source_phase"), max_length=128)
        or PRODUCT_SURFACE_VALIDATION_SOURCE_PHASE,
        "public_reached": bool(source.get("public_reached")),
        "rn_visible": bool(source.get("rn_visible")),
        "public_feedback_inclusion_contract_passed": bool(
            source.get("public_feedback_inclusion_contract_passed")
        ),
        "product_surface_valid": bool(source.get("product_surface_valid")),
        "surface_requirement_family": _surface_family(source.get("surface_requirement_family")),
        "surface_requirement_satisfied": bool(source.get("surface_requirement_satisfied")),
        "two_stage_required": bool(source.get("two_stage_required")),
        "plain_surface_used": bool(source.get("plain_surface_used")),
        "plain_surface_allowed": bool(source.get("plain_surface_allowed")),
        "low_information_surface_used": bool(source.get("low_information_surface_used")),
        "candidate_source_kind": _clean_identifier(source.get("candidate_source_kind"), max_length=128),
        "normal_observation_rebuild_used": bool(source.get("normal_observation_rebuild_used")),
        "complete_initial_surface_recomposition_used": bool(source.get("complete_initial_surface_recomposition_used")),
        "labelled_two_stage_recomposition_used": bool(source.get("labelled_two_stage_recomposition_used")),
        "low_information_observation_used": bool(source.get("low_information_observation_used")),
        "blocker_family": _clean_identifier(source.get("blocker_family"), max_length=96),
        "blocker_code": blocker_code,
        "body_free": True,
        "raw_input_included": False,
        "comment_text_body_included": False,
    }
    _assert_no_forbidden_body_keys(payload)
    json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return payload


def resolve_product_surface_requirement_from_sources(*sources: Mapping[str, Any] | None) -> dict[str, Any]:
    """Find a body-free P1 surface requirement summary from nested meta sources."""

    for source in sources:
        found = _find_surface_requirement(_as_mapping(source), depth=0)
        if found:
            return found
    return {}


def assert_product_surface_validation_summary(value: Any) -> None:
    if not isinstance(value, Mapping):
        raise ValueError("product surface validation summary must be a mapping")
    actual = set(value.keys())
    if actual != set(_REQUIRED_SUMMARY_KEYS):
        raise ValueError(
            "product surface validation key set changed: "
            f"missing={sorted(set(_REQUIRED_SUMMARY_KEYS) - actual)} "
            f"extra={sorted(actual - set(_REQUIRED_SUMMARY_KEYS))}"
        )
    if value.get("schema_version") != PRODUCT_SURFACE_VALIDATION_SCHEMA_VERSION:
        raise ValueError("unexpected product surface validation schema_version")
    if value.get("source_phase") != PRODUCT_SURFACE_VALIDATION_SOURCE_PHASE:
        raise ValueError("unexpected product surface validation source_phase")
    for key in (
        "public_reached",
        "rn_visible",
        "public_feedback_inclusion_contract_passed",
        "product_surface_valid",
        "surface_requirement_satisfied",
        "two_stage_required",
        "plain_state_answer_allowed",
        "low_information_allowed",
        "plain_surface_used",
        "plain_surface_allowed",
        "low_information_surface_used",
        "candidate_generated_before_display_gate",
        "gate_recovery_material_surface_used_as_public_body",
        "diagnostic_recovery_surface_used_as_public_body",
        "normal_observation_rebuild_used",
        "complete_initial_surface_recomposition_used",
        "labelled_two_stage_recomposition_used",
        "low_information_observation_used",
    ):
        if not isinstance(value.get(key), bool):
            raise ValueError(f"{key} must be boolean")
    if value.get("surface_requirement_family") not in _ALLOWED_SURFACE_REQUIREMENT_FAMILIES:
        raise ValueError("unknown product surface requirement family")
    if value.get("blocker_code") not in _VALID_BLOCKER_CODES:
        raise ValueError("unknown product surface blocker code")
    _assert_shape(value.get("labelled_two_stage_shape"))
    _assert_origin(value.get("surface_origin"))
    _assert_gate_validation(value.get("gate_validation"))
    _assert_public_contract(value.get("public_contract"))
    _assert_gate_policy(value.get("gate_policy"))
    if value.get("body_free") is not True:
        raise ValueError("P3 summary must be body-free")
    if value.get("raw_input_included") is not False or value.get("comment_text_body_included") is not False:
        raise ValueError("P3 summary must not include raw/comment text")
    _assert_no_forbidden_body_keys(value)
    json.dumps(dict(value), ensure_ascii=False, sort_keys=True)


def _find_surface_requirement(source: Mapping[str, Any], *, depth: int) -> dict[str, Any]:
    if not source or depth > 6:
        return {}
    try:
        direct = public_surface_requirement_public_summary(source)
    except Exception:
        direct = {}
    if direct and source.get("schema_version") == "cocolon.emlis.public_surface_requirement.v1":
        return direct
    for key in (
        "surface_requirement",
        "public_surface_requirement",
        "required_public_surface",
        "recovery_plan",
        "product_surface_validation",
        "public_observation_product_surface_validation",
        "product_surface_validation_summary",
        "surface_quality",
        "diagnostic_summary",
        "reply_service_public_boundary",
        "phase20_5_gate_recovery_public_candidate_builder",
        "phase20_5_gate_recovery_public_boundary",
        "phase20_13_post_final_gate_recovery",
        "gate_recovery_public_boundary_decision",
        "normal_observation_rebuild",
    ):
        child = _as_mapping(source.get(key))
        if not child:
            continue
        found = _find_surface_requirement(child, depth=depth + 1)
        if found:
            return found
    return {}


def _requirement_summary(surface_requirement: Mapping[str, Any] | None) -> dict[str, Any]:
    summary = public_surface_requirement_public_summary(surface_requirement)
    if summary:
        return summary
    return {
        "schema_version": "cocolon.emlis.public_surface_requirement.v1",
        "source_phase": "PublicObservationRecovery_P1_SurfaceRequirementDecision",
        "surface_requirement_family": SURFACE_REQUIREMENT_PLAIN_STATE_ANSWER,
        "two_stage_required": False,
        "plain_state_answer_allowed": True,
        "low_information_allowed": False,
        "required_comment_text_shape": {
            "kind": "plain_state_answer",
            "starts_with": "",
            "contains_boundary": "",
            "labels_required": False,
            "observation_section_required": True,
            "reception_section_required": False,
            "comment_text_body_included": False,
        },
        "decision_sources": ["p3_default_plain_state_answer"],
        "material_quality_family": "unknown",
        "input_material_classification": {
            "memo_present": False,
            "memo_action_present": False,
            "emotions_present": False,
            "categories_present": False,
            "memo_text_len": 0,
            "memo_action_text_len": 0,
            "high_information_input": False,
            "low_information_material": False,
            "body_free": True,
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
        "body_free": True,
        "raw_input_included": False,
        "comment_text_body_included": False,
        "public_contract": _false_public_contract(),
        "gate_policy": _false_gate_policy(),
    }


def _surface_requirement_satisfied(
    *,
    rn_visible: bool,
    surface_family: str,
    two_stage_required: bool,
    plain_surface_allowed: bool,
    low_information_allowed: bool,
    labelled_shape_valid: bool,
    low_information_surface_used: bool,
    candidate_source_kind: str,
    public_candidate_source_allowed: bool,
) -> bool:
    if not rn_visible or not public_candidate_source_allowed:
        return False
    if surface_family in {SURFACE_REQUIREMENT_SAFETY_BLOCKED, SURFACE_REQUIREMENT_INFRASTRUCTURE_FAIL_CLOSED}:
        return False
    if two_stage_required or surface_family == SURFACE_REQUIREMENT_LABELLED_TWO_STAGE:
        return bool(
            labelled_shape_valid
            and not low_information_surface_used
            and candidate_source_kind != CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
        )
    if surface_family == SURFACE_REQUIREMENT_LOW_INFORMATION_OBSERVATION:
        return bool(low_information_allowed and low_information_surface_used)
    if surface_family in {SURFACE_REQUIREMENT_PLAIN_STATE_ANSWER, SURFACE_REQUIREMENT_SELF_DENIAL_SAFE_STATE_ANSWER}:
        return bool(plain_surface_allowed and not low_information_surface_used)
    return False


def _blocker(
    *,
    public_reached: bool,
    rn_visible: bool,
    public_gate_blocked: bool,
    public_candidate_source_allowed: bool,
    two_stage_required: bool,
    plain_surface_used: bool,
    labelled_shape_valid: bool,
    low_information_surface_used: bool,
    low_information_allowed: bool,
    plain_surface_allowed: bool,
    surface_requirement_satisfied: bool,
    surface_family: str,
    candidate_source_kind: str,
    gate_validation: Mapping[str, Any],
) -> tuple[str, str]:
    if not public_reached:
        return (_BLOCKER_FAMILY_PUBLIC_FEEDBACK, PRODUCT_SURFACE_INVALID_PUBLIC_FEEDBACK_NOT_REACHED)
    if not rn_visible:
        return (_BLOCKER_FAMILY_RN_VISIBLE, PRODUCT_SURFACE_INVALID_RN_NOT_VISIBLE)
    if public_gate_blocked:
        return (_BLOCKER_FAMILY_PUBLIC_GATE, PRODUCT_SURFACE_INVALID_PUBLIC_GATE_BLOCKED)
    if not public_candidate_source_allowed:
        return (_BLOCKER_FAMILY_CANDIDATE_SOURCE, PRODUCT_SURFACE_INVALID_CANDIDATE_SOURCE_NOT_ALLOWED)
    if low_information_surface_used and not low_information_allowed:
        return (_BLOCKER_FAMILY_LOW_INFORMATION, PRODUCT_SURFACE_INVALID_LOW_INFORMATION_MISROUTE)
    if two_stage_required and plain_surface_used:
        return (_BLOCKER_FAMILY_TWO_STAGE_SHAPE, PRODUCT_SURFACE_INVALID_PLAIN_USED_FOR_TWO_STAGE_REQUIRED)
    if two_stage_required and candidate_source_kind == CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE:
        return (_BLOCKER_FAMILY_TWO_STAGE_SHAPE, PRODUCT_SURFACE_INVALID_PLAIN_USED_FOR_TWO_STAGE_REQUIRED)
    if two_stage_required and not labelled_shape_valid:
        return (_BLOCKER_FAMILY_TWO_STAGE_SHAPE, PRODUCT_SURFACE_INVALID_TWO_STAGE_SHAPE_REQUIRED)
    if surface_family == SURFACE_REQUIREMENT_LOW_INFORMATION_OBSERVATION and not low_information_surface_used:
        return (_BLOCKER_FAMILY_LOW_INFORMATION, PRODUCT_SURFACE_INVALID_LOW_INFORMATION_MISROUTE)
    if surface_family in {SURFACE_REQUIREMENT_PLAIN_STATE_ANSWER, SURFACE_REQUIREMENT_SELF_DENIAL_SAFE_STATE_ANSWER} and not plain_surface_allowed:
        return (_BLOCKER_FAMILY_PLAIN_STATE_ANSWER, PRODUCT_SURFACE_INVALID_PLAIN_STATE_ANSWER_NOT_ALLOWED)
    if not surface_requirement_satisfied:
        blocker_family = _clean_identifier(gate_validation.get("first_blocker_family"), max_length=96)
        return (blocker_family or _BLOCKER_FAMILY_SURFACE_REQUIREMENT, PRODUCT_SURFACE_INVALID_SURFACE_REQUIREMENT_UNSATISFIED)
    return (_BLOCKER_FAMILY_NONE, PRODUCT_SURFACE_VALID)


def _decision_reasons(
    *,
    product_surface_valid: bool,
    blocker_code: str,
    surface_family: str,
    two_stage_required: bool,
    plain_surface_used: bool,
    low_information_surface_used: bool,
    candidate_source_kind: str,
    gate_validation: Mapping[str, Any],
) -> tuple[str, ...]:
    reasons: list[str] = []
    reasons.append(PRODUCT_SURFACE_VALID if product_surface_valid else blocker_code)
    if two_stage_required:
        reasons.append("two_stage_required")
    if plain_surface_used:
        reasons.append("plain_surface_used")
    if low_information_surface_used:
        reasons.append("low_information_surface_used")
    if surface_family:
        reasons.append(f"surface_requirement:{surface_family}")
    if candidate_source_kind:
        reasons.append(f"candidate_source:{candidate_source_kind}")
    first_blocker = _clean_identifier(gate_validation.get("first_blocker_code"), max_length=128)
    if first_blocker:
        reasons.append(f"public_gate_blocker:{first_blocker}")
    return _dedupe(reasons)[:12]


def _labelled_shape_summary(comment_text: Any) -> dict[str, bool]:
    shape = labelled_two_stage_comment_text_shape_summary(comment_text)
    body = str(comment_text or "")
    budget_valid = False
    if is_labelled_two_stage_comment_text_shape(body):
        before, _, after = body.partition(LABELLED_TWO_STAGE_RECEPTION_BOUNDARY)
        observation_section = before.replace("見えたこと：\n", "", 1).strip()
        reception_section = after.strip()
        budget_valid = bool(
            10 <= len(observation_section) <= 420
            and 8 <= len(reception_section) <= 360
            and len(body) <= 900
        )
    return {
        "labels_present": bool(shape.get("labels_present")),
        "label_order_valid": bool(shape.get("label_order_valid")),
        "observation_section_non_empty": bool(shape.get("observation_section_non_empty")),
        "reception_section_non_empty": bool(shape.get("reception_section_non_empty")),
        "section_budget_checked": True,
        "section_budget_valid": bool(budget_valid),
        "comment_text_body_included": False,
    }


def _gate_validation_summary(value: Mapping[str, Any] | None, *, public_meta: Mapping[str, Any]) -> dict[str, Any]:
    source = _as_mapping(value)
    blocking_codes = _blocking_codes(source, public_meta)
    first_blocker_code = _clean_identifier(
        source.get("first_blocker_code")
        or source.get("first_backend_blocker")
        or source.get("public_blocker_code")
        or (blocking_codes[0] if blocking_codes else ""),
        max_length=128,
    )
    first_blocker_family = _clean_identifier(
        source.get("first_blocker_family")
        or source.get("blocker_family")
        or _blocker_family_from_code(first_blocker_code),
        max_length=96,
    )
    visible_blocked = bool(source.get("visible_surface_gate_blocked") or _contains_marker(blocking_codes, "visible"))
    runtime_blocked = bool(source.get("runtime_surface_gate_blocked") or _contains_marker(blocking_codes, "runtime"))
    display_blocked = bool(source.get("display_gate_blocked") or _contains_marker(blocking_codes, "display"))
    state_answer_blocked = bool(source.get("state_answer_gate_blocked") or _contains_marker(blocking_codes, "state_answer"))
    two_stage_blocked = bool(source.get("two_stage_gate_blocked") or _contains_marker(blocking_codes, "two_stage"))
    public_gate_blocked = bool(
        source.get("public_gate_blocked")
        or visible_blocked
        or runtime_blocked
        or display_blocked
        or state_answer_blocked
        or two_stage_blocked
        or first_blocker_code
        or _public_gate_blocks(public_meta)
    )
    return {
        "public_gate_blocked": bool(public_gate_blocked),
        "visible_surface_gate_blocked": bool(visible_blocked),
        "runtime_surface_gate_blocked": bool(runtime_blocked),
        "display_gate_blocked": bool(display_blocked),
        "state_answer_gate_blocked": bool(state_answer_blocked),
        "two_stage_gate_blocked": bool(two_stage_blocked),
        "first_blocker_family": first_blocker_family,
        "first_blocker_code": first_blocker_code,
        "blocking_codes": blocking_codes,
        "body_free": True,
        "raw_input_included": False,
        "comment_text_body_included": False,
    }


def _surface_origin_summary(candidate_source_kind: str, *, normal_observation_rebuild_used: bool | None) -> dict[str, Any]:
    gate_recovery_material_used = candidate_source_kind == CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE
    diagnostic_recovery_used = candidate_source_kind == CANDIDATE_SOURCE_KIND_DIAGNOSTIC_RECOVERY_SURFACE
    normal_rebuild_used = bool(
        normal_observation_rebuild_used
        if normal_observation_rebuild_used is not None
        else candidate_source_kind == CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
    )
    complete_recomposition_used = candidate_source_kind == CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_SURFACE_RECOMPOSITION_CANDIDATE
    labelled_recomposition_used = candidate_source_kind == CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE
    low_information_used = candidate_source_kind in _LOW_INFORMATION_SOURCE_KINDS
    explicitly_forbidden = candidate_source_kind in set(FORBIDDEN_PUBLIC_CANDIDATE_SOURCE_KINDS) | {
        CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE,
        CANDIDATE_SOURCE_KIND_DIAGNOSTIC_RECOVERY_SURFACE,
    }
    known_public = candidate_source_kind in set(ALLOWED_PUBLIC_CANDIDATE_SOURCE_KINDS) | _FUTURE_PUBLIC_CANDIDATE_SOURCE_KINDS
    # Unknown/empty candidate source is diagnostic debt, not a P3 public leak by itself.
    public_candidate_source_allowed = bool(not explicitly_forbidden and (known_public or not candidate_source_kind))
    return {
        "candidate_source_kind": candidate_source_kind,
        "public_candidate_source_allowed": public_candidate_source_allowed,
        "gate_recovery_material_surface_used_as_public_body": bool(gate_recovery_material_used),
        "diagnostic_recovery_surface_used_as_public_body": bool(diagnostic_recovery_used),
        "normal_observation_rebuild_used": bool(normal_rebuild_used),
        "complete_initial_surface_recomposition_used": bool(complete_recomposition_used),
        "labelled_two_stage_recomposition_used": bool(labelled_recomposition_used),
        "low_information_observation_used": bool(low_information_used),
        "body_free": True,
        "raw_input_included": False,
        "comment_text_body_included": False,
    }


def _candidate_generated_before_display_gate(
    *,
    generation: Mapping[str, Any],
    candidate_status: str,
    composer_source: str,
) -> bool:
    explicit = generation.get("candidate_generated_before_display_gate")
    if explicit is None:
        explicit = generation.get("generated_before_display_gate")
    result = _safe_bool(explicit)
    if result is None:
        result = False
    if candidate_status == "generated":
        result = True
    if candidate_status in {"unavailable", "not_generated"} or composer_source == "unavailable":
        result = False
    return bool(result)


def _is_low_information_surface(
    *,
    candidate_source_kind: str,
    surface_family: str,
    generation: Mapping[str, Any],
    public_meta: Mapping[str, Any],
) -> bool:
    if surface_family == SURFACE_REQUIREMENT_LOW_INFORMATION_OBSERVATION:
        return True
    values = {
        candidate_source_kind,
        _clean_identifier(generation.get("observation_reply_kind"), max_length=96),
        _clean_identifier(generation.get("reply_kind"), max_length=96),
        _clean_identifier(public_meta.get("observation_reply_kind"), max_length=96),
    }
    return any("low_information" in value for value in values if value)


def _candidate_source_kind(generation: Mapping[str, Any], public_meta: Mapping[str, Any]) -> str:
    return _clean_identifier(
        generation.get("candidate_source_kind")
        or generation.get("public_candidate_source_kind")
        or generation.get("adopted_candidate_source_kind")
        or public_meta.get("candidate_source_kind")
        or public_meta.get("public_candidate_source_kind"),
        max_length=128,
    )


def _surface_family(value: Any) -> str:
    text = _clean_identifier(value, max_length=96)
    return text if text in _ALLOWED_SURFACE_REQUIREMENT_FAMILIES else SURFACE_REQUIREMENT_PLAIN_STATE_ANSWER


def _blocking_codes(source: Mapping[str, Any], public_meta: Mapping[str, Any]) -> tuple[str, ...]:
    candidates: list[Any] = []
    for key in (
        "blocking_codes",
        "blocker_codes",
        "rejection_reasons",
        "public_gate_blocking_codes",
    ):
        candidates.extend(_as_sequence(source.get(key)))
        candidates.extend(_as_sequence(public_meta.get(key)))
    for gate_key in (
        "runtime_surface_pre_return_gate",
        "visible_surface_acceptance_gate",
        "display_gate",
        "state_answer_gate_boundary",
        "two_stage_reception_gate",
    ):
        gate = _as_mapping(public_meta.get(gate_key))
        candidates.extend(_as_sequence(gate.get("rejection_reasons")))
        candidates.extend(_as_sequence(gate.get("blocking_codes")))
        candidates.extend(_as_sequence(gate.get("blocker_codes")))
    return _dedupe(candidates)


def _public_gate_blocks(public_meta: Mapping[str, Any]) -> bool:
    for key in (
        "runtime_surface_pre_return_gate",
        "visible_surface_acceptance_gate",
        "display_gate",
        "state_answer_gate_boundary",
        "two_stage_reception_gate",
    ):
        gate = _as_mapping(public_meta.get(key))
        if not gate:
            continue
        passed = _safe_bool(gate.get("passed"))
        if passed is False:
            return True
        if _safe_bool(gate.get("blocked")) is True or _safe_bool(gate.get("terminal_surface_block")) is True:
            return True
        action = _clean_identifier(gate.get("action"), max_length=80)
        if action in {"rerender_surface", "reroute_low_information", "block", "fail_closed"}:
            return True
    return False


def _blocker_family_from_code(code: str) -> str:
    if not code:
        return ""
    if "visible" in code:
        return "visible_surface"
    if "runtime" in code:
        return "runtime_surface"
    if "display" in code:
        return "display_gate"
    if "state_answer" in code:
        return "state_answer_gate"
    if "two_stage" in code:
        return "two_stage_gate"
    return "public_gate"


def _contains_marker(values: Sequence[Any], marker: str) -> bool:
    return any(marker in _clean_identifier(value, max_length=128) for value in values)


def _assert_shape(value: Any) -> None:
    mapping = _as_mapping(value)
    if set(mapping.keys()) != set(_SHAPE_KEYS):
        raise ValueError("labelled_two_stage_shape key set changed")
    for key in _SHAPE_KEYS:
        if not isinstance(mapping.get(key), bool):
            raise ValueError(f"labelled_two_stage_shape.{key} must be boolean")


def _assert_origin(value: Any) -> None:
    mapping = _as_mapping(value)
    if set(mapping.keys()) != set(_ORIGIN_KEYS):
        raise ValueError("surface_origin key set changed")
    for key in _ORIGIN_KEYS:
        if key == "candidate_source_kind":
            continue
        if not isinstance(mapping.get(key), bool):
            raise ValueError(f"surface_origin.{key} must be boolean")


def _assert_gate_validation(value: Any) -> None:
    mapping = _as_mapping(value)
    if set(mapping.keys()) != set(_GATE_VALIDATION_KEYS):
        raise ValueError("gate_validation key set changed")
    for key in (
        "public_gate_blocked",
        "visible_surface_gate_blocked",
        "runtime_surface_gate_blocked",
        "display_gate_blocked",
        "state_answer_gate_blocked",
        "two_stage_gate_blocked",
        "body_free",
        "raw_input_included",
        "comment_text_body_included",
    ):
        if not isinstance(mapping.get(key), bool):
            raise ValueError(f"gate_validation.{key} must be boolean")


def _assert_public_contract(value: Any) -> None:
    mapping = _as_mapping(value)
    if set(mapping.keys()) != set(_PUBLIC_CONTRACT_KEYS):
        raise ValueError("public_contract key set changed")
    if any(mapping.get(key) is not False for key in _PUBLIC_CONTRACT_KEYS):
        raise ValueError("P3 validation must not change public contract")


def _assert_gate_policy(value: Any) -> None:
    mapping = _as_mapping(value)
    if set(mapping.keys()) != set(_GATE_POLICY_KEYS):
        raise ValueError("gate_policy key set changed")
    if any(mapping.get(key) is not False for key in _GATE_POLICY_KEYS):
        raise ValueError("P3 validation must not relax gates")


def _false_public_contract() -> dict[str, bool]:
    return {key: False for key in _PUBLIC_CONTRACT_KEYS}


def _false_gate_policy() -> dict[str, bool]:
    return {key: False for key in _GATE_POLICY_KEYS}


def _as_mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _as_sequence(value: Any) -> Sequence[Any]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes, bytearray)):
        return (value,)
    if isinstance(value, Sequence):
        return value
    return (value,)


def _clean_identifier(value: Any, *, max_length: int = 160) -> str:
    return str(value or "").strip().replace(" ", "_")[:max_length]


def _safe_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "on", "enabled", "enable", "green", "passed", "pass", "ok", "allow"}:
        return True
    if text in {"0", "false", "no", "n", "off", "disabled", "red", "failed", "fail", "blocked", "block"}:
        return False
    return None


def _dedupe(values: Sequence[Any]) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = _clean_identifier(value, max_length=160)
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return tuple(result)


def _assert_no_forbidden_body_keys(value: Any) -> None:
    if isinstance(value, Mapping):
        forbidden = set(value.keys()) & _BODY_FORBIDDEN_EXACT_KEYS
        if forbidden:
            raise ValueError(f"P3 summary contains body-like key(s): {sorted(forbidden)}")
        for child in value.values():
            _assert_no_forbidden_body_keys(child)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for item in value:
            _assert_no_forbidden_body_keys(item)


__all__ = [
    "CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_SURFACE_RECOMPOSITION_CANDIDATE",
    "CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE",
    "PRODUCT_SURFACE_BLOCKER_CANDIDATE_SOURCE_NOT_ALLOWED",
    "PRODUCT_SURFACE_BLOCKER_LOW_INFORMATION_MISROUTE",
    "PRODUCT_SURFACE_BLOCKER_NONE",
    "PRODUCT_SURFACE_BLOCKER_PLAIN_STATE_ANSWER_NOT_ALLOWED",
    "PRODUCT_SURFACE_BLOCKER_PLAIN_USED_FOR_TWO_STAGE_REQUIRED",
    "PRODUCT_SURFACE_BLOCKER_PUBLIC_FEEDBACK_ABSENT",
    "PRODUCT_SURFACE_BLOCKER_PUBLIC_GATE_BLOCKED",
    "PRODUCT_SURFACE_BLOCKER_RN_NOT_VISIBLE",
    "PRODUCT_SURFACE_BLOCKER_SURFACE_REQUIREMENT_UNSATISFIED",
    "PRODUCT_SURFACE_BLOCKER_SURFACE_REQUIREMENT_UNSUPPORTED",
    "PRODUCT_SURFACE_BLOCKER_TWO_STAGE_SHAPE",
    "PRODUCT_SURFACE_BLOCKER_TWO_STAGE_SHAPE_REQUIRED",
    "PRODUCT_SURFACE_INVALID_CANDIDATE_SOURCE_NOT_ALLOWED",
    "PRODUCT_SURFACE_INVALID_LOW_INFORMATION_MISROUTE",
    "PRODUCT_SURFACE_INVALID_PLAIN_STATE_ANSWER_NOT_ALLOWED",
    "PRODUCT_SURFACE_INVALID_PLAIN_USED_FOR_TWO_STAGE_REQUIRED",
    "PRODUCT_SURFACE_INVALID_PUBLIC_FEEDBACK_NOT_REACHED",
    "PRODUCT_SURFACE_INVALID_PUBLIC_GATE_BLOCKED",
    "PRODUCT_SURFACE_INVALID_RN_NOT_VISIBLE",
    "PRODUCT_SURFACE_INVALID_SURFACE_REQUIREMENT_UNSATISFIED",
    "PRODUCT_SURFACE_INVALID_TWO_STAGE_SHAPE_REQUIRED",
    "PRODUCT_SURFACE_VALID",
    "PRODUCT_SURFACE_VALIDATION_PUBLIC_META_KEY",
    "PRODUCT_SURFACE_VALIDATION_SCHEMA_VERSION",
    "PRODUCT_SURFACE_VALIDATION_SOURCE_PHASE",
    "assert_product_surface_validation_summary",
    "build_product_surface_validation_summary",
    "product_surface_validation_public_summary",
    "resolve_product_surface_requirement_from_sources",
]
