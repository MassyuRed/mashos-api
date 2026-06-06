# -*- coding: utf-8 -*-
from __future__ import annotations

"""P0 body-free naming for EmlisAI public observation recovery states.

This module fixes the current red states as machine-readable names before any
P2+ recovery behavior is changed.  It separates public reachability, RN
visibility, and product-surface validity without changing RN/API/DB contracts,
without relaxing gates, and without serializing raw input or public body text.
"""

from collections.abc import Mapping, Sequence
from typing import Any, Final
import json

from emlis_ai_public_surface_requirement import (
    SURFACE_REQUIREMENT_LABELLED_TWO_STAGE,
    SURFACE_REQUIREMENT_LOW_INFORMATION_OBSERVATION,
    SURFACE_REQUIREMENT_PLAIN_STATE_ANSWER,
    is_labelled_two_stage_comment_text_shape,
    labelled_two_stage_comment_text_shape_summary,
)

PUBLIC_OBSERVATION_RECOVERY_STATUS_SCHEMA_VERSION: Final = (
    "cocolon.emlis.public_observation_recovery_status.v1"
)
PUBLIC_OBSERVATION_RECOVERY_STATUS_SOURCE_PHASE: Final = (
    "PublicObservationRecovery_P0_RedTestFailureNaming"
)

RECOVERY_STATE_PRODUCT_SURFACE_VALID: Final = "product_surface_valid"
RECOVERY_STATE_PUBLIC_FEEDBACK_ABSENT_COMPLETE_INITIAL_SURFACE_UNAVAILABLE: Final = (
    "public_feedback_absent_complete_initial_surface_unavailable"
)
RECOVERY_STATE_PUBLIC_FEEDBACK_ABSENT: Final = "public_feedback_absent"
RECOVERY_STATE_RN_NOT_VISIBLE: Final = "rn_not_visible"
RECOVERY_STATE_PRODUCT_SURFACE_INVALID_PLAIN_USED_FOR_TWO_STAGE_REQUIRED: Final = (
    "product_surface_invalid_plain_used_for_two_stage_required"
)
RECOVERY_STATE_PRODUCT_SURFACE_INVALID_TWO_STAGE_SHAPE: Final = (
    "product_surface_invalid_two_stage_shape"
)
RECOVERY_STATE_PRODUCT_SURFACE_INVALID_LOW_INFORMATION_MISROUTE: Final = (
    "product_surface_invalid_low_information_misroute"
)
RECOVERY_STATE_PRODUCT_SURFACE_INVALID_GENERIC: Final = "product_surface_invalid"

_RECOVERY_STATE_NAMES: Final[frozenset[str]] = frozenset(
    {
        RECOVERY_STATE_PRODUCT_SURFACE_VALID,
        RECOVERY_STATE_PUBLIC_FEEDBACK_ABSENT_COMPLETE_INITIAL_SURFACE_UNAVAILABLE,
        RECOVERY_STATE_PUBLIC_FEEDBACK_ABSENT,
        RECOVERY_STATE_RN_NOT_VISIBLE,
        RECOVERY_STATE_PRODUCT_SURFACE_INVALID_PLAIN_USED_FOR_TWO_STAGE_REQUIRED,
        RECOVERY_STATE_PRODUCT_SURFACE_INVALID_TWO_STAGE_SHAPE,
        RECOVERY_STATE_PRODUCT_SURFACE_INVALID_LOW_INFORMATION_MISROUTE,
        RECOVERY_STATE_PRODUCT_SURFACE_INVALID_GENERIC,
    }
)
_SOURCE_UNAVAILABLE_CODES: Final[tuple[str, ...]] = (
    "complete_initial_surface_unavailable",
    "source_unavailable",
    "composer_source_unavailable",
    "composer_unavailable",
    "surface_signature_unavailable",
)
_SURFACE_REPAIRABLE_CODES: Final[tuple[str, ...]] = (
    "surface_grammar",
    "relation_skeleton",
    "visible_surface",
    "runtime_surface",
    "koto_splice",
)
_SAFETY_CODES: Final[tuple[str, ...]] = (
    "safety_blocked",
    "requires_block",
    "emergency",
    "self_harm",
    "medical",
    "legal",
)
_INFRASTRUCTURE_CODES: Final[tuple[str, ...]] = (
    "timeout",
    "exception",
    "infrastructure_error",
    "reply_timeout_or_error",
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
        "body",
        "text",
        "surface_text",
        "surfaceText",
        "evidence_text",
        "evidenceText",
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
_REQUIRED_STATUS_KEYS: Final[frozenset[str]] = frozenset(
    {
        "schema_version",
        "source_phase",
        "public_reached",
        "rn_visible",
        "product_surface_valid",
        "recovery_state_name",
        "surface_requirement_family",
        "two_stage_required",
        "plain_state_answer_allowed",
        "low_information_allowed",
        "plain_surface_used",
        "low_information_surface_used",
        "labelled_two_stage_shape",
        "candidate_source_kind",
        "composer_source",
        "candidate_status",
        "candidate_generated_before_display_gate",
        "first_blocker_family",
        "first_blocker_code",
        "recovery_lane",
        "normal_observation_rebuild_used",
        "normal_observation_rebuild_allowed",
        "normal_observation_rebuild_blocker",
        "public_feedback_absence_reason_family",
        "body_free",
        "raw_input_included",
        "comment_text_body_included",
        "public_contract",
        "gate_policy",
    }
)
_REQUIRED_SHAPE_KEYS: Final[frozenset[str]] = frozenset(
    {
        "labels_present",
        "label_order_valid",
        "observation_section_non_empty",
        "reception_section_non_empty",
        "section_budget_checked",
        "comment_text_body_included",
    }
)


def name_public_observation_recovery_state(
    *,
    comment_text: Any = "",
    public_meta: Mapping[str, Any] | None = None,
    input_feedback_included: bool = False,
    surface_requirement: Mapping[str, Any] | None = None,
    candidate_generation: Mapping[str, Any] | None = None,
    normal_observation_rebuild_used: bool = False,
) -> dict[str, Any]:
    """Return the P0 red-state name and three-stage visibility booleans.

    ``comment_text`` is used only for shape checks.  It is never serialized into
    the returned mapping.
    """

    public = _as_mapping(public_meta)
    requirement = _as_mapping(surface_requirement)
    generation = _as_mapping(candidate_generation)

    observation_status = _clean_identifier(
        public.get("observation_status")
        or public.get("public_observation_status")
        or public.get("status"),
        max_length=96,
    )
    public_reached = bool(input_feedback_included)
    rn_visible = bool(public_reached and observation_status == "passed" and str(comment_text or "").strip())

    surface_family = _clean_identifier(requirement.get("surface_requirement_family"), max_length=96)
    if not surface_family:
        surface_family = SURFACE_REQUIREMENT_PLAIN_STATE_ANSWER
    two_stage_required = bool(requirement.get("two_stage_required"))
    plain_allowed = bool(requirement.get("plain_state_answer_allowed"))
    low_information_allowed = bool(requirement.get("low_information_allowed"))
    candidate_source_kind = _clean_identifier(
        generation.get("candidate_source_kind") or public.get("candidate_source_kind"),
        max_length=128,
    )
    composer_source = _clean_identifier(
        generation.get("composer_source") or public.get("composer_source"),
        max_length=96,
    )
    candidate_status = _clean_identifier(
        generation.get("candidate_status") or public.get("candidate_status"),
        max_length=96,
    )
    generated_before_display_gate = _safe_bool(
        generation.get("candidate_generated_before_display_gate")
        if "candidate_generated_before_display_gate" in generation
        else generation.get("generated_before_display_gate")
    )
    if candidate_status == "generated":
        generated_before_display_gate = True
    if composer_source == "unavailable" or candidate_status == "unavailable":
        generated_before_display_gate = False

    reason_codes = _reason_codes(public, generation, requirement)
    first_blocker_code = _first_blocker_code(public=public, generation=generation, reason_codes=reason_codes)
    first_blocker_family = _first_blocker_family(
        first_blocker_code=first_blocker_code,
        reason_codes=reason_codes,
        composer_source=composer_source,
        candidate_status=candidate_status,
        generated_before_display_gate=generated_before_display_gate,
    )
    shape = labelled_two_stage_comment_text_shape_summary(comment_text)
    labelled_shape_valid = is_labelled_two_stage_comment_text_shape(comment_text)
    plain_surface_used = bool(rn_visible and not labelled_shape_valid)
    low_information_surface_used = bool(
        surface_family == SURFACE_REQUIREMENT_LOW_INFORMATION_OBSERVATION
        or candidate_source_kind == "low_information_observation_composer"
        or "low_information" in candidate_source_kind
    )
    public_absence_reason_family = ""
    if not public_reached:
        public_absence_reason_family = first_blocker_family or "public_feedback_absent"

    recovery_lane = _recovery_lane(
        first_blocker_family=first_blocker_family,
        generated_before_display_gate=generated_before_display_gate,
        candidate_status=candidate_status,
        composer_source=composer_source,
    )
    normal_rebuild_allowed, normal_rebuild_blocker = _normal_observation_rebuild_allowance(
        first_blocker_family=first_blocker_family,
        generated_before_display_gate=generated_before_display_gate,
        composer_source=composer_source,
        candidate_status=candidate_status,
        two_stage_required=two_stage_required,
        plain_state_answer_allowed=plain_allowed,
        normal_observation_rebuild_used=normal_observation_rebuild_used,
    )

    product_surface_valid = False
    if rn_visible:
        if two_stage_required:
            product_surface_valid = bool(labelled_shape_valid)
        elif surface_family == SURFACE_REQUIREMENT_LOW_INFORMATION_OBSERVATION:
            product_surface_valid = bool(low_information_allowed and not two_stage_required)
        elif surface_family == SURFACE_REQUIREMENT_PLAIN_STATE_ANSWER:
            product_surface_valid = bool(plain_allowed)
        else:
            product_surface_valid = bool(plain_allowed and not two_stage_required)

    recovery_state_name = _recovery_state_name(
        public_reached=public_reached,
        rn_visible=rn_visible,
        product_surface_valid=product_surface_valid,
        first_blocker_code=first_blocker_code,
        first_blocker_family=first_blocker_family,
        two_stage_required=two_stage_required,
        plain_surface_used=plain_surface_used,
        labelled_shape_valid=labelled_shape_valid,
        low_information_surface_used=low_information_surface_used,
        low_information_allowed=low_information_allowed,
    )

    summary = {
        "schema_version": PUBLIC_OBSERVATION_RECOVERY_STATUS_SCHEMA_VERSION,
        "source_phase": PUBLIC_OBSERVATION_RECOVERY_STATUS_SOURCE_PHASE,
        "public_reached": public_reached,
        "rn_visible": rn_visible,
        "product_surface_valid": product_surface_valid,
        "recovery_state_name": recovery_state_name,
        "surface_requirement_family": surface_family,
        "two_stage_required": two_stage_required,
        "plain_state_answer_allowed": plain_allowed,
        "low_information_allowed": low_information_allowed,
        "plain_surface_used": plain_surface_used,
        "low_information_surface_used": low_information_surface_used,
        "labelled_two_stage_shape": _sanitize_shape_summary(shape),
        "candidate_source_kind": candidate_source_kind,
        "composer_source": composer_source,
        "candidate_status": candidate_status,
        "candidate_generated_before_display_gate": bool(generated_before_display_gate),
        "first_blocker_family": first_blocker_family,
        "first_blocker_code": first_blocker_code,
        "recovery_lane": recovery_lane,
        "normal_observation_rebuild_used": bool(normal_observation_rebuild_used),
        "normal_observation_rebuild_allowed": normal_rebuild_allowed,
        "normal_observation_rebuild_blocker": normal_rebuild_blocker,
        "public_feedback_absence_reason_family": public_absence_reason_family,
        "body_free": True,
        "raw_input_included": False,
        "comment_text_body_included": False,
        "public_contract": _false_public_contract(),
        "gate_policy": _false_gate_policy(),
    }
    assert_public_observation_recovery_status(summary)
    return summary


def assert_public_observation_recovery_status(value: Any) -> None:
    if not isinstance(value, Mapping):
        raise ValueError("public observation recovery status must be a mapping")
    actual = set(value.keys())
    if actual != set(_REQUIRED_STATUS_KEYS):
        raise ValueError(
            "public observation recovery status key set changed: "
            f"missing={sorted(set(_REQUIRED_STATUS_KEYS) - actual)} "
            f"extra={sorted(actual - set(_REQUIRED_STATUS_KEYS))}"
        )
    if value.get("schema_version") != PUBLIC_OBSERVATION_RECOVERY_STATUS_SCHEMA_VERSION:
        raise ValueError("unexpected public observation recovery status schema_version")
    if value.get("recovery_state_name") not in _RECOVERY_STATE_NAMES:
        raise ValueError("unknown public observation recovery state name")
    for key in ("public_reached", "rn_visible", "product_surface_valid"):
        if not isinstance(value.get(key), bool):
            raise ValueError(f"{key} must be boolean")
    shape = _as_mapping(value.get("labelled_two_stage_shape"))
    if set(shape.keys()) != set(_REQUIRED_SHAPE_KEYS):
        raise ValueError("labelled_two_stage_shape key set changed")
    public_contract = _as_mapping(value.get("public_contract"))
    if set(public_contract.keys()) != set(_PUBLIC_CONTRACT_KEYS):
        raise ValueError("public_contract key set changed")
    if any(public_contract.get(key) is not False for key in _PUBLIC_CONTRACT_KEYS):
        raise ValueError("P0 status must not change public contract")
    gate_policy = _as_mapping(value.get("gate_policy"))
    if set(gate_policy.keys()) != set(_GATE_POLICY_KEYS):
        raise ValueError("gate_policy key set changed")
    if any(gate_policy.get(key) is not False for key in _GATE_POLICY_KEYS):
        raise ValueError("P0 status must not relax gates")
    if value.get("body_free") is not True:
        raise ValueError("P0 status must be body-free")
    if value.get("raw_input_included") is not False or value.get("comment_text_body_included") is not False:
        raise ValueError("P0 status must not include raw/body text")
    _assert_no_forbidden_body_keys(value)
    json.dumps(dict(value), ensure_ascii=False, sort_keys=True)


def _recovery_state_name(
    *,
    public_reached: bool,
    rn_visible: bool,
    product_surface_valid: bool,
    first_blocker_code: str,
    first_blocker_family: str,
    two_stage_required: bool,
    plain_surface_used: bool,
    labelled_shape_valid: bool,
    low_information_surface_used: bool,
    low_information_allowed: bool,
) -> str:
    if product_surface_valid:
        return RECOVERY_STATE_PRODUCT_SURFACE_VALID
    if not public_reached:
        if first_blocker_code == "complete_initial_surface_unavailable":
            return RECOVERY_STATE_PUBLIC_FEEDBACK_ABSENT_COMPLETE_INITIAL_SURFACE_UNAVAILABLE
        return RECOVERY_STATE_PUBLIC_FEEDBACK_ABSENT
    if not rn_visible:
        return RECOVERY_STATE_RN_NOT_VISIBLE
    if two_stage_required and plain_surface_used:
        return RECOVERY_STATE_PRODUCT_SURFACE_INVALID_PLAIN_USED_FOR_TWO_STAGE_REQUIRED
    if two_stage_required and not labelled_shape_valid:
        return RECOVERY_STATE_PRODUCT_SURFACE_INVALID_TWO_STAGE_SHAPE
    if low_information_surface_used and not low_information_allowed:
        return RECOVERY_STATE_PRODUCT_SURFACE_INVALID_LOW_INFORMATION_MISROUTE
    if first_blocker_family:
        return RECOVERY_STATE_PRODUCT_SURFACE_INVALID_GENERIC
    return RECOVERY_STATE_PRODUCT_SURFACE_INVALID_GENERIC


def _normal_observation_rebuild_allowance(
    *,
    first_blocker_family: str,
    generated_before_display_gate: bool,
    composer_source: str,
    candidate_status: str,
    two_stage_required: bool,
    plain_state_answer_allowed: bool,
    normal_observation_rebuild_used: bool,
) -> tuple[bool, str]:
    if normal_observation_rebuild_used:
        return True, ""
    if first_blocker_family == "source_unavailable" or composer_source == "unavailable" or candidate_status == "unavailable":
        return False, "source_unavailable_not_rebuildable"
    if not generated_before_display_gate:
        return False, "original_candidate_not_generated"
    if two_stage_required:
        return False, "normal_observation_rebuild_blocked_two_stage_required"
    if not plain_state_answer_allowed:
        return False, "plain_state_answer_not_allowed"
    if first_blocker_family in {"surface_grammar", "relation_skeleton", "visible_surface", "runtime_surface", "koto_splice"}:
        return True, ""
    return False, "repairable_surface_failure_missing"


def _recovery_lane(
    *,
    first_blocker_family: str,
    generated_before_display_gate: bool,
    candidate_status: str,
    composer_source: str,
) -> str:
    if first_blocker_family == "source_unavailable" or composer_source == "unavailable" or candidate_status == "unavailable" or not generated_before_display_gate:
        return "complete_initial_surface_recomposition"
    if first_blocker_family in {"surface_grammar", "relation_skeleton", "visible_surface", "runtime_surface", "koto_splice"}:
        return "normal_observation_rebuild"
    if first_blocker_family == "safety":
        return "safety_fail_closed"
    if first_blocker_family == "infrastructure_error":
        return "infrastructure_fail_closed"
    return "none"


def _first_blocker_code(
    *,
    public: Mapping[str, Any],
    generation: Mapping[str, Any],
    reason_codes: Sequence[str],
) -> str:
    for key in (
        "first_backend_blocker",
        "first_blocker_code",
        "first_failure_reason",
        "candidate_failure_reason",
        "fail_closed_reason_code",
    ):
        text = _clean_identifier(public.get(key) or generation.get(key), max_length=160)
        if text:
            return text
    for reason in reason_codes:
        if reason:
            return _clean_identifier(reason, max_length=160)
    return ""


def _first_blocker_family(
    *,
    first_blocker_code: str,
    reason_codes: Sequence[str],
    composer_source: str,
    candidate_status: str,
    generated_before_display_gate: bool,
) -> str:
    codes = [_clean_lower(first_blocker_code), *[_clean_lower(reason) for reason in reason_codes]]
    if composer_source == "unavailable" or candidate_status == "unavailable" or not generated_before_display_gate:
        codes.append("source_unavailable")
    if _contains_any(codes, _SOURCE_UNAVAILABLE_CODES):
        return "source_unavailable"
    if _contains_any(codes, _SAFETY_CODES):
        return "safety"
    if _contains_any(codes, _INFRASTRUCTURE_CODES):
        return "infrastructure_error"
    for family in _SURFACE_REPAIRABLE_CODES:
        if _contains_any(codes, (family,)):
            return family
    return ""


def _reason_codes(*sources: Mapping[str, Any]) -> tuple[str, ...]:
    reasons: list[str] = []

    def collect(value: Any) -> None:
        if isinstance(value, Mapping):
            for key, child in value.items():
                if key in {
                    "rejection_reasons",
                    "reason_codes",
                    "surface_issue_codes",
                    "blockers",
                    "blocked_reasons",
                    "public_surface_blockers",
                }:
                    reasons.extend(_dedupe(child))
                    continue
                if key in {
                    "primary_reason",
                    "first_backend_blocker",
                    "first_blocker_code",
                    "first_failure_reason",
                    "candidate_failure_reason",
                    "fail_closed_reason_code",
                }:
                    text = _clean_identifier(child, max_length=160)
                    if text:
                        reasons.append(text)
                    continue
                collect(child)
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            for child in value:
                collect(child)

    for source in sources:
        collect(source)
    return _dedupe(reasons)


def _sanitize_shape_summary(value: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "labels_present": bool(value.get("labels_present")),
        "label_order_valid": bool(value.get("label_order_valid")),
        "observation_section_non_empty": bool(value.get("observation_section_non_empty")),
        "reception_section_non_empty": bool(value.get("reception_section_non_empty")),
        "section_budget_checked": bool(value.get("section_budget_checked")),
        "comment_text_body_included": False,
    }


def _contains_any(values: Sequence[str], needles: Sequence[str]) -> bool:
    return any(needle in value for value in values for needle in needles if needle)


def _false_public_contract() -> dict[str, bool]:
    return {key: False for key in _PUBLIC_CONTRACT_KEYS}


def _false_gate_policy() -> dict[str, bool]:
    return {key: False for key in _GATE_POLICY_KEYS}


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _as_sequence(value: Sequence[Any] | Any | None) -> Sequence[Any]:
    if value is None:
        return []
    if isinstance(value, (str, bytes, bytearray)):
        return [value.decode("utf-8", errors="ignore") if isinstance(value, (bytes, bytearray)) else value]
    if isinstance(value, Sequence):
        return value
    return [value]


def _dedupe(values: Sequence[Any] | Any | None) -> tuple[str, ...]:
    out: list[str] = []
    for value in _as_sequence(values):
        text = _clean_identifier(value, max_length=160)
        if text and text not in out:
            out.append(text)
    return tuple(out)


def _clean_identifier(value: Any, *, max_length: int = 160) -> str:
    return str(value or "").strip().replace(" ", "_")[:max_length]


def _clean_lower(value: Any) -> str:
    return _clean_identifier(value, max_length=160).lower()


def _safe_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return _clean_lower(value) in {"1", "true", "yes", "y", "on", "enabled", "enable", "green", "passed", "ok", "generated"}


def _assert_no_forbidden_body_keys(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in _BODY_FORBIDDEN_EXACT_KEYS:
                raise ValueError(f"public observation recovery status must stay body-free: {key}")
            _assert_no_forbidden_body_keys(child)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for child in value:
            _assert_no_forbidden_body_keys(child)


__all__ = [
    "PUBLIC_OBSERVATION_RECOVERY_STATUS_SCHEMA_VERSION",
    "PUBLIC_OBSERVATION_RECOVERY_STATUS_SOURCE_PHASE",
    "RECOVERY_STATE_PRODUCT_SURFACE_VALID",
    "RECOVERY_STATE_PUBLIC_FEEDBACK_ABSENT_COMPLETE_INITIAL_SURFACE_UNAVAILABLE",
    "RECOVERY_STATE_PUBLIC_FEEDBACK_ABSENT",
    "RECOVERY_STATE_RN_NOT_VISIBLE",
    "RECOVERY_STATE_PRODUCT_SURFACE_INVALID_PLAIN_USED_FOR_TWO_STAGE_REQUIRED",
    "RECOVERY_STATE_PRODUCT_SURFACE_INVALID_TWO_STAGE_SHAPE",
    "RECOVERY_STATE_PRODUCT_SURFACE_INVALID_LOW_INFORMATION_MISROUTE",
    "RECOVERY_STATE_PRODUCT_SURFACE_INVALID_GENERIC",
    "assert_public_observation_recovery_status",
    "name_public_observation_recovery_state",
]
