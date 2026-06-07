# -*- coding: utf-8 -*-
from __future__ import annotations

"""P4 complete-initial surface availability diagnostics for EmlisAI.

This module names why a complete-initial public observation candidate did not
exist before the public display gate.  It is deliberately diagnostic-only: it
never renders text, never opens a public response lane, never relaxes gates, and
never promotes source-unavailable cases into ``normal_observation_rebuild``.
"""

from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Final
import json
import re

from emlis_ai_public_surface_requirement import (
    SURFACE_REQUIREMENT_INFRASTRUCTURE_FAIL_CLOSED,
    SURFACE_REQUIREMENT_LABELLED_TWO_STAGE,
    SURFACE_REQUIREMENT_LOW_INFORMATION_OBSERVATION,
    SURFACE_REQUIREMENT_PLAIN_STATE_ANSWER,
    SURFACE_REQUIREMENT_SAFETY_BLOCKED,
    SURFACE_REQUIREMENT_SELF_DENIAL_SAFE_STATE_ANSWER,
    public_surface_requirement_public_summary,
)

COMPLETE_INITIAL_SURFACE_AVAILABILITY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.complete_initial_surface_availability.v1"
)
COMPLETE_INITIAL_SURFACE_AVAILABILITY_SOURCE_PHASE: Final = (
    "PublicObservationRecovery_P4_CompleteInitialSurfaceAvailability"
)
COMPLETE_INITIAL_SURFACE_AVAILABILITY_PUBLIC_META_KEY: Final = (
    "complete_initial_surface_availability_summary"
)

RECOVERY_LANE_COMPLETE_INITIAL_SURFACE_RECOMPOSITION: Final = (
    "complete_initial_surface_recomposition"
)
RECOVERY_LANE_BLOCKED_BEFORE_RECOMPOSITION: Final = "blocked_before_recomposition"
RECOVERY_LANE_SOURCE_AVAILABILITY_INVESTIGATION: Final = "source_availability_investigation"
RECOVERY_LANE_NORMAL_OBSERVATION_REBUILD: Final = "normal_observation_rebuild"
RECOVERY_LANE_NONE: Final = "none"

NORMAL_REBUILD_BLOCKER_SOURCE_UNAVAILABLE_NOT_REBUILDABLE: Final = (
    "source_unavailable_not_rebuildable"
)
NORMAL_REBUILD_BLOCKER_TWO_STAGE_REQUIRED: Final = (
    "normal_observation_rebuild_blocked_two_stage_required"
)
NORMAL_REBUILD_BLOCKER_NOT_REPAIRABLE_SURFACE_FAILURE: Final = (
    "normal_observation_rebuild_not_repairable_surface_failure"
)
NORMAL_REBUILD_BLOCKER_NOT_NEEDED: Final = "normal_observation_rebuild_not_needed"
NORMAL_REBUILD_BLOCKER_NONE: Final = ""

_FIRST_BLOCKER_FAMILY_SOURCE_UNAVAILABLE: Final = "source_unavailable"
_FIRST_BLOCKER_FAMILY_SURFACE_REALIZER_UNAVAILABLE: Final = "surface_realizer_unavailable"
_FIRST_BLOCKER_FAMILY_AP0_ROLLOUT: Final = "ap0_rollout"
_FIRST_BLOCKER_FAMILY_COVERAGE: Final = "coverage"
_FIRST_BLOCKER_FAMILY_REQUIRED_STRUCTURE: Final = "required_structure"
_FIRST_BLOCKER_FAMILY_MATERIAL_QUALITY: Final = "material_quality"
_FIRST_BLOCKER_FAMILY_SURFACE_SIGNATURE: Final = "surface_signature_unavailable"
_FIRST_BLOCKER_FAMILY_SURFACE_FAILURE: Final = "surface_failure"
_FIRST_BLOCKER_FAMILY_SAFETY: Final = "safety"
_FIRST_BLOCKER_FAMILY_INFRASTRUCTURE: Final = "infrastructure"
_FIRST_BLOCKER_FAMILY_COMPOSER_DISABLED: Final = "composer_disabled"
_FIRST_BLOCKER_FAMILY_NONE: Final = ""
_FIRST_BLOCKER_FAMILY_UNKNOWN: Final = "unknown"

_SOURCE_UNAVAILABLE_CODES: Final[tuple[str, ...]] = (
    "limited_composer_shallow_empty_candidate",
    "sentence_plan_unavailable",
    "empty_comment_text_without_candidate",
    "composer_source_unavailable",
    "composer_unavailable",
    "complete_initial_surface_unavailable",
    "source_unavailable",
    "complete_initial_candidate_not_generated",
    "complete_initial_generation_not_attempted",
    "complete_initial_client_not_resolved",
)
_NON_BLOCKING_ROUTE_REASON_CODES: Final[frozenset[str]] = frozenset(
    {
        # Phase20-3 material routing names the source of an eligible material
        # decision.  It is not a blocker and must not shadow the limited
        # composer source-unavailable reason used by P4/P5 recovery.
        "phase20_3_material_quality_router",
    }
)
_SURFACE_REALIZER_CODES: Final[tuple[str, ...]] = (
    "surface_realizer_unavailable",
    "surface_realizer_not_connected",
    "complete_surface_realizer_unavailable",
    "complete_surface_realizer_not_connected",
    "section_surface_realizer_missing",
)
_AP0_ROLLOUT_CODES: Final[tuple[str, ...]] = (
    "ap0_blocked",
    "ap0_rollout_blocked",
    "rollout_stage_off",
    "rollout_stage_not_matched",
    "complete_initial_rollout_not_allowed",
    "limited_composer_rollout_not_allowed",
    "limited_composer_rollout_off",
)
_COVERAGE_CODES: Final[tuple[str, ...]] = (
    "coverage_missing",
    "coverage_mismatch",
    "coverage_insufficient",
    "surface_coverage_missing",
    "required_coverage_missing",
)
_REQUIRED_STRUCTURE_CODES: Final[tuple[str, ...]] = (
    "required_structure_missing",
    "required_structure_blocked",
    "required_section_missing",
    "two_stage_section_plan_missing",
    "section_budget_invalid",
)
_MATERIAL_QUALITY_CODES: Final[tuple[str, ...]] = (
    "material_insufficient",
    "low_information",
    "limited_grounding",
    "material_quality_low_information",
    "material_quality_limited_grounding",
    "material_unsupported",
    "unsupported_material",
    "material_quality_unsupported",
    "unsupported_input_material",
)
_SURFACE_SIGNATURE_CODES: Final[tuple[str, ...]] = (
    "surface_signature_unavailable",
    "surface_signature_missing",
    "complete_initial_surface_signature_unavailable",
)
_SURFACE_FAILURE_CODES: Final[tuple[str, ...]] = (
    "surface_grammar",
    "relation_skeleton",
    "visible_surface",
    "runtime_surface",
    "koto_splice",
    "surface_template_major",
    "runtime_surface_pre_return_gate_failed",
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
    "emlis_ai_reply_timeout",
    "emlis_ai_reply_error",
)
_COMPOSER_DISABLED_CODES: Final[tuple[str, ...]] = (
    "composer_disabled",
    "complete_initial_composer_disabled",
    "composer_client_disabled",
)
_BLOCKED_BEFORE_RECOMPOSITION_CODE_GROUPS: Final[tuple[tuple[str, ...], ...]] = (
    _SAFETY_CODES,
    _INFRASTRUCTURE_CODES,
    _COMPOSER_DISABLED_CODES,
    _AP0_ROLLOUT_CODES,
    _MATERIAL_QUALITY_CODES,
    _COVERAGE_CODES,
    _REQUIRED_STRUCTURE_CODES,
)
_LOW_MATERIAL_QUALITY_VALUES: Final[frozenset[str]] = frozenset(
    {
        "low_information",
        "limited_grounding",
        "material_insufficient",
        "insufficient_input_material",
        "unsupported",
        "material_unsupported",
        "unsupported_material",
        "material_quality_unsupported",
        "unsupported_input_material",
        "unknown",
    }
)
_SURFACE_REQUIREMENT_FAMILIES: Final[frozenset[str]] = frozenset(
    {
        SURFACE_REQUIREMENT_LABELLED_TWO_STAGE,
        SURFACE_REQUIREMENT_PLAIN_STATE_ANSWER,
        SURFACE_REQUIREMENT_LOW_INFORMATION_OBSERVATION,
        SURFACE_REQUIREMENT_SELF_DENIAL_SAFE_STATE_ANSWER,
        SURFACE_REQUIREMENT_SAFETY_BLOCKED,
        SURFACE_REQUIREMENT_INFRASTRUCTURE_FAIL_CLOSED,
        "unknown",
    }
)
_RECOMPOSITION_COMPATIBLE_SURFACE_REQUIREMENT_FAMILIES: Final[frozenset[str]] = frozenset(
    {
        SURFACE_REQUIREMENT_LABELLED_TWO_STAGE,
        SURFACE_REQUIREMENT_PLAIN_STATE_ANSWER,
    }
)
_RECOMPOSITION_BLOCKING_SURFACE_REQUIREMENT_FAMILIES: Final[frozenset[str]] = frozenset(
    {
        SURFACE_REQUIREMENT_LOW_INFORMATION_OBSERVATION,
        SURFACE_REQUIREMENT_SELF_DENIAL_SAFE_STATE_ANSWER,
        SURFACE_REQUIREMENT_SAFETY_BLOCKED,
        SURFACE_REQUIREMENT_INFRASTRUCTURE_FAIL_CLOSED,
    }
)
_HARD_BLOCKER_FAMILIES: Final[frozenset[str]] = frozenset(
    {
        _FIRST_BLOCKER_FAMILY_AP0_ROLLOUT,
        _FIRST_BLOCKER_FAMILY_COVERAGE,
        _FIRST_BLOCKER_FAMILY_REQUIRED_STRUCTURE,
        _FIRST_BLOCKER_FAMILY_MATERIAL_QUALITY,
        _FIRST_BLOCKER_FAMILY_SAFETY,
        _FIRST_BLOCKER_FAMILY_INFRASTRUCTURE,
        _FIRST_BLOCKER_FAMILY_COMPOSER_DISABLED,
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
_EXISTING_GATE_KEYS: Final[tuple[str, ...]] = (
    "reader_gate_evaluated",
    "grounding_gate_evaluated",
    "template_gate_evaluated",
    "display_gate_evaluated",
    "visible_surface_gate_evaluated",
    "runtime_surface_gate_evaluated",
)
_AVAILABILITY_DIAGNOSTIC_KEYS: Final[tuple[str, ...]] = (
    "ap0_or_rollout_blocked",
    "coverage_blocked",
    "required_structure_blocked",
    "material_quality_blocked",
    "surface_signature_unavailable",
    "surface_realizer_unavailable",
)
_REQUIRED_SUMMARY_KEYS: Final[frozenset[str]] = frozenset(
    {
        "schema_version",
        "source_phase",
        "complete_initial_client_resolved",
        "candidate_generation_attempted",
        "candidate_generated_before_display_gate",
        "candidate_status",
        "composer_source",
        "first_blocker_family",
        "first_blocker_code",
        "material_sufficient",
        "material_quality_family",
        "surface_requirement_family",
        "recovery_lane",
        "normal_observation_rebuild_allowed",
        "normal_observation_rebuild_blocker",
        "availability_diagnostics",
        "existing_gates_evaluated",
        "public_contract",
        "gate_policy",
        "body_free",
        "raw_input_included",
        "comment_text_body_included",
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
        "surface_text",
        "surfaceText",
        "candidate_body",
        "candidateBody",
        "surface_body",
        "surfaceBody",
        "body",
        "text",
    }
)
_IDENTIFIER_RE: Final = re.compile(r"^[A-Za-z0-9_.:/\-]+$")


def build_complete_initial_surface_availability_summary(
    *,
    internal_meta: Mapping[str, Any] | None = None,
    diagnostic_summary: Mapping[str, Any] | None = None,
    phase_gate: Mapping[str, Any] | None = None,
    candidate_generation_summary: Mapping[str, Any] | None = None,
    surface_requirement: Mapping[str, Any] | None = None,
    material_route: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a body-free P4 availability summary.

    The returned mapping classifies candidate-unavailable cases without trying
    to generate or recover a public body.  Source-unavailable cases explicitly
    keep ``normal_observation_rebuild_allowed`` false.
    """

    sources = _collect_sources(
        candidate_generation_summary,
        _without_prior_availability_summary(diagnostic_summary),
        _without_prior_availability_summary(phase_gate),
        _without_prior_availability_summary(internal_meta),
        material_route,
        surface_requirement,
    )
    requirement = _surface_requirement_summary(surface_requirement, sources)

    complete_initial_client_resolved = _pick_bool(
        sources,
        (
            "complete_initial_client_resolved",
            "step3_complete_initial_client_resolved",
            "complete_initial_client_used",
        ),
    )
    if complete_initial_client_resolved is None:
        complete_initial_client_resolved = _connection_status_resolved(sources)

    candidate_generation_attempted = _pick_bool(
        sources,
        (
            "candidate_generation_attempted",
            "complete_initial_candidate_generation_attempted",
            "step5_complete_initial_candidate_generation_attempted",
            "complete_composer_client_generate_called",
            "candidate_generation_path_confirmed",
            "step5_candidate_generation_path_confirmed",
        ),
    )
    if candidate_generation_attempted is None:
        candidate_generation_attempted = False

    candidate_status = _pick_identifier(
        sources,
        (
            "candidate_status",
            "candidate_status_before_display_gate",
            "complete_initial_candidate_status",
            "step5_complete_initial_candidate_status",
            "composer_status",
            "status",
        ),
    )
    composer_source = _pick_identifier(
        sources,
        (
            "composer_source",
            "candidate_source",
            "complete_initial_composer_source",
            "runtime_composer_source",
        ),
    )
    if not candidate_status:
        candidate_status = "unknown"
    if not composer_source:
        composer_source = "unknown"

    candidate_generated_before_display_gate = _pick_bool(
        sources,
        (
            "candidate_generated_before_display_gate",
            "complete_candidate_generated_before_display_gate",
            "complete_initial_candidate_generated",
            "complete_initial_candidate_generated_before_display_gate",
            "step5_complete_initial_candidate_generated",
            "candidate_generated",
        ),
    )
    if candidate_generated_before_display_gate is None:
        candidate_generated_before_display_gate = False
    if candidate_status == "generated" and composer_source == "ai_generated":
        candidate_generated_before_display_gate = True
    if candidate_status in {"unavailable", "not_generated", "not_attempted"} or composer_source == "unavailable":
        candidate_generated_before_display_gate = False

    material_quality_family = _material_quality_family(sources)
    material_sufficient = _material_sufficient(sources, material_quality_family=material_quality_family)
    surface_requirement_family = _surface_requirement_family(requirement, sources)
    if surface_requirement_family not in _SURFACE_REQUIREMENT_FAMILIES:
        surface_requirement_family = "unknown"

    reason_codes = _reason_codes(sources)
    first_blocker_code = _first_blocker_code(
        sources=sources,
        reason_codes=reason_codes,
        complete_initial_client_resolved=complete_initial_client_resolved,
        candidate_generation_attempted=candidate_generation_attempted,
        candidate_generated_before_display_gate=candidate_generated_before_display_gate,
        candidate_status=candidate_status,
        composer_source=composer_source,
    )
    first_blocker_family = _first_blocker_family(
        first_blocker_code,
        reason_codes=reason_codes,
        candidate_generated_before_display_gate=candidate_generated_before_display_gate,
        candidate_status=candidate_status,
        composer_source=composer_source,
    )
    first_blocker_family = _apply_lane_blocker_overrides(
        first_blocker_family,
        material_quality_family=material_quality_family,
        surface_requirement_family=surface_requirement_family,
    )
    availability_diagnostics = _availability_diagnostics(first_blocker_family, reason_codes)
    existing_gates_evaluated = _existing_gates_evaluated(sources)
    two_stage_required = bool(requirement.get("two_stage_required")) or surface_requirement_family == SURFACE_REQUIREMENT_LABELLED_TWO_STAGE

    normal_allowed, normal_blocker = _normal_rebuild_allowance(
        candidate_generated_before_display_gate=candidate_generated_before_display_gate,
        composer_source=composer_source,
        first_blocker_family=first_blocker_family,
        two_stage_required=two_stage_required,
    )
    recovery_lane = _recovery_lane(
        first_blocker_family=first_blocker_family,
        material_sufficient=material_sufficient,
        surface_requirement_family=surface_requirement_family,
        candidate_generated_before_display_gate=candidate_generated_before_display_gate,
        normal_observation_rebuild_allowed=normal_allowed,
    )

    summary = {
        "schema_version": COMPLETE_INITIAL_SURFACE_AVAILABILITY_SCHEMA_VERSION,
        "source_phase": COMPLETE_INITIAL_SURFACE_AVAILABILITY_SOURCE_PHASE,
        "complete_initial_client_resolved": bool(complete_initial_client_resolved),
        "candidate_generation_attempted": bool(candidate_generation_attempted),
        "candidate_generated_before_display_gate": bool(candidate_generated_before_display_gate),
        "candidate_status": candidate_status,
        "composer_source": composer_source,
        "first_blocker_family": first_blocker_family,
        "first_blocker_code": first_blocker_code,
        "material_sufficient": bool(material_sufficient),
        "material_quality_family": material_quality_family,
        "surface_requirement_family": surface_requirement_family,
        "recovery_lane": recovery_lane,
        "normal_observation_rebuild_allowed": bool(normal_allowed),
        "normal_observation_rebuild_blocker": normal_blocker,
        "availability_diagnostics": availability_diagnostics,
        "existing_gates_evaluated": existing_gates_evaluated,
        "public_contract": _false_public_contract(),
        "gate_policy": _false_gate_policy(),
        "body_free": True,
        "raw_input_included": False,
        "comment_text_body_included": False,
    }
    assert_complete_initial_surface_availability_summary(summary)
    return summary


def complete_initial_surface_availability_public_summary(
    summary: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Return the P4 body-free subset safe for public meta/logs."""

    source = _as_mapping(summary)
    if not source:
        return {}
    payload = {
        "schema_version": _clean_identifier(source.get("schema_version"), max_length=128)
        or COMPLETE_INITIAL_SURFACE_AVAILABILITY_SCHEMA_VERSION,
        "source_phase": _clean_identifier(source.get("source_phase"), max_length=128)
        or COMPLETE_INITIAL_SURFACE_AVAILABILITY_SOURCE_PHASE,
        "complete_initial_client_resolved": bool(source.get("complete_initial_client_resolved")),
        "candidate_generation_attempted": bool(source.get("candidate_generation_attempted")),
        "candidate_generated_before_display_gate": bool(source.get("candidate_generated_before_display_gate")),
        "candidate_status": _clean_identifier(source.get("candidate_status"), max_length=96) or "unknown",
        "composer_source": _clean_identifier(source.get("composer_source"), max_length=96) or "unknown",
        "first_blocker_family": _clean_identifier(source.get("first_blocker_family"), max_length=96),
        "first_blocker_code": _clean_identifier(source.get("first_blocker_code"), max_length=128),
        "material_sufficient": bool(source.get("material_sufficient")),
        "material_quality_family": _clean_identifier(source.get("material_quality_family"), max_length=96) or "unknown",
        "surface_requirement_family": _clean_identifier(source.get("surface_requirement_family"), max_length=96) or "unknown",
        "recovery_lane": _clean_identifier(source.get("recovery_lane"), max_length=96),
        "normal_observation_rebuild_allowed": bool(source.get("normal_observation_rebuild_allowed")),
        "normal_observation_rebuild_blocker": _clean_identifier(
            source.get("normal_observation_rebuild_blocker"), max_length=128
        ),
        "body_free": True,
        "raw_input_included": False,
        "comment_text_body_included": False,
    }
    _assert_no_forbidden_body_keys(payload)
    json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return payload


def assert_complete_initial_surface_availability_summary(value: Any) -> None:
    if not isinstance(value, Mapping):
        raise ValueError("complete initial surface availability summary must be a mapping")
    actual = set(value.keys())
    if actual != set(_REQUIRED_SUMMARY_KEYS):
        raise ValueError(
            "complete initial surface availability key set changed: "
            f"missing={sorted(set(_REQUIRED_SUMMARY_KEYS) - actual)} "
            f"extra={sorted(actual - set(_REQUIRED_SUMMARY_KEYS))}"
        )
    if value.get("schema_version") != COMPLETE_INITIAL_SURFACE_AVAILABILITY_SCHEMA_VERSION:
        raise ValueError("unexpected complete initial surface availability schema_version")
    if value.get("source_phase") != COMPLETE_INITIAL_SURFACE_AVAILABILITY_SOURCE_PHASE:
        raise ValueError("unexpected complete initial surface availability source_phase")
    for key in (
        "complete_initial_client_resolved",
        "candidate_generation_attempted",
        "candidate_generated_before_display_gate",
        "material_sufficient",
        "normal_observation_rebuild_allowed",
        "body_free",
    ):
        if not isinstance(value.get(key), bool):
            raise ValueError(f"{key} must be boolean")
    if value.get("raw_input_included") is not False or value.get("comment_text_body_included") is not False:
        raise ValueError("P4 availability summary must not include raw/body text")
    if value.get("body_free") is not True:
        raise ValueError("P4 availability summary must be body-free")
    for key in ("candidate_status", "composer_source", "first_blocker_family", "surface_requirement_family"):
        if not isinstance(value.get(key), str):
            raise ValueError(f"{key} must be string")
    availability = _as_mapping(value.get("availability_diagnostics"))
    if set(availability.keys()) != set(_AVAILABILITY_DIAGNOSTIC_KEYS):
        raise ValueError("availability_diagnostics key set changed")
    gates = _as_mapping(value.get("existing_gates_evaluated"))
    expected_gate_keys = set(_EXISTING_GATE_KEYS) | {"all_existing_gates_evaluated"}
    if set(gates.keys()) != expected_gate_keys:
        raise ValueError("existing_gates_evaluated key set changed")
    public_contract = _as_mapping(value.get("public_contract"))
    if set(public_contract.keys()) != set(_PUBLIC_CONTRACT_KEYS):
        raise ValueError("public_contract key set changed")
    if any(public_contract.get(key) is not False for key in _PUBLIC_CONTRACT_KEYS):
        raise ValueError("P4 availability summary must not change public contract")
    gate_policy = _as_mapping(value.get("gate_policy"))
    if set(gate_policy.keys()) != set(_GATE_POLICY_KEYS):
        raise ValueError("gate_policy key set changed")
    if any(gate_policy.get(key) is not False for key in _GATE_POLICY_KEYS):
        raise ValueError("P4 availability summary must not relax gates")
    _assert_no_forbidden_body_keys(value)
    json.dumps(dict(value), ensure_ascii=False, sort_keys=True)



def _without_prior_availability_summary(value: Mapping[str, Any] | None) -> Mapping[str, Any] | None:
    """Return context without a previously built availability summary.

    Availability summaries are outputs of this module, not authoritative inputs
    for a later rebuild.  Keeping an older summary in the source set can let an
    earlier ``material_sufficient=false / material_quality_family=unknown``
    shadow the Phase20-3 material route that reply_service now passes
    explicitly.
    """

    mapping = _as_mapping(value)
    if not mapping:
        return None
    cleaned = dict(mapping)
    for key in (
        COMPLETE_INITIAL_SURFACE_AVAILABILITY_PUBLIC_META_KEY,
        "public_observation_complete_initial_surface_availability",
        "complete_initial_availability_summary",
    ):
        cleaned.pop(key, None)
    return cleaned


def _collect_sources(*values: Mapping[str, Any] | None) -> list[Mapping[str, Any]]:
    sources: list[Mapping[str, Any]] = []
    seen: set[int] = set()

    def add(value: Any, *, depth: int = 0) -> None:
        if depth > 4:
            return
        mapping = _as_mapping(value)
        if not mapping:
            return
        marker = id(mapping)
        if marker in seen:
            return
        seen.add(marker)
        sources.append(mapping)
        for key in (
            COMPLETE_INITIAL_SURFACE_AVAILABILITY_PUBLIC_META_KEY,
            "public_observation_complete_initial_surface_availability",
            "complete_initial_availability_summary",
            "diagnostic_summary",
            "multi_perspective",
            "phase_gate",
            "complete_initial_candidate_generation_path",
            "step5_candidate_generation_path",
            "complete_initial_runtime",
            "step5_complete_initial_runtime",
            "runtime",
            "step16_rollout_metrics",
            "rollout_metrics",
            "complete_initial_resolution",
            "step4_complete_initial_resolution",
            "complete_initial_resolution_path",
            "step4_resolution_path",
            "surface_requirement",
            "public_surface_requirement",
        ):
            child = mapping.get(key)
            if isinstance(child, Mapping):
                add(child, depth=depth + 1)

    for item in values:
        add(item)
    return sources


def _surface_requirement_summary(
    surface_requirement: Mapping[str, Any] | None,
    sources: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    direct = public_surface_requirement_public_summary(surface_requirement)
    if direct:
        return direct
    for source in sources:
        for key in ("surface_requirement", "public_surface_requirement"):
            nested = public_surface_requirement_public_summary(_as_mapping(source.get(key)))
            if nested:
                return nested
    return {}


def _surface_requirement_family(requirement: Mapping[str, Any], sources: Sequence[Mapping[str, Any]]) -> str:
    direct = _clean_identifier(requirement.get("surface_requirement_family"), max_length=96)
    if direct:
        return direct
    for source in sources:
        value = _clean_identifier(source.get("surface_requirement_family"), max_length=96)
        if value:
            return value
    if _pick_bool(sources, ("two_stage_required", "state_answer_two_stage_display_required")) is True:
        return SURFACE_REQUIREMENT_LABELLED_TWO_STAGE
    return "unknown"


def _connection_status_resolved(sources: Sequence[Mapping[str, Any]]) -> bool:
    for source in sources:
        client_status = _clean_identifier(source.get("client_status"), max_length=80)
        if client_status == "resolved":
            return True
        connection_status = _clean_identifier(source.get("connection_status"), max_length=120)
        if connection_status in {"default_client_resolved", "resolved", "complete_initial_resolved"}:
            return True
        requested = _clean_identifier(source.get("requested_composer"), max_length=96)
        if requested == "complete_initial" and connection_status:
            return connection_status.endswith("resolved")
    return False


def _material_quality_family(sources: Sequence[Mapping[str, Any]]) -> str:
    for source in sources:
        for key in (
            "material_quality_family",
            "material_quality",
            "eligibility_status",
            "input_material_quality",
            "observation_material_quality",
        ):
            value = _clean_identifier(source.get(key), max_length=96)
            if value:
                return value
        route = _as_mapping(source.get("material_route"))
        if route:
            value = _clean_identifier(route.get("material_quality"), max_length=96)
            if value:
                return value
    return "unknown"


def _material_sufficient(sources: Sequence[Mapping[str, Any]], *, material_quality_family: str) -> bool:
    explicit = _pick_bool(
        sources,
        (
            "material_sufficient",
            "material_ready",
            "eligible_for_full_observation",
            "structure_dictionary_material_ready",
            "sufficient_input_material",
        ),
    )
    if explicit is not None:
        return bool(explicit)
    if material_quality_family and material_quality_family not in _LOW_MATERIAL_QUALITY_VALUES:
        return True
    return False


def _reason_codes(sources: Sequence[Mapping[str, Any]]) -> list[str]:
    out: list[str] = []
    for source in sources:
        for key in (
            "reason_codes",
            "rejection_reasons",
            "display_rejection_reasons",
            "surface_blocker_reasons",
            "release_blockers",
            "repair_abort_reasons",
            "blocking_codes",
        ):
            for item in _as_sequence(source.get(key)):
                reason = _clean_identifier(item, max_length=128)
                if reason in _NON_BLOCKING_ROUTE_REASON_CODES:
                    continue
                if reason and reason not in out:
                    out.append(reason)
        for key in (
            "first_blocker_code",
            "first_backend_blocker",
            "primary_reason",
            "fail_closed_reason_code",
            "blocker_code",
            "public_feedback_absence_reason_code",
        ):
            reason = _clean_identifier(source.get(key), max_length=128)
            if reason in _NON_BLOCKING_ROUTE_REASON_CODES:
                continue
            if reason and reason not in out:
                out.append(reason)
    return out[:32]


def _first_blocker_code(
    *,
    sources: Sequence[Mapping[str, Any]],
    reason_codes: Sequence[str],
    complete_initial_client_resolved: bool,
    candidate_generation_attempted: bool,
    candidate_generated_before_display_gate: bool,
    candidate_status: str,
    composer_source: str,
) -> str:
    priority_blocker = _blocked_before_recomposition_reason_code(reason_codes)
    if priority_blocker:
        return priority_blocker
    source_unavailable_reason = _source_unavailable_reason_code(reason_codes)
    if source_unavailable_reason:
        return source_unavailable_reason
    for source in sources:
        for key in (
            "first_blocker_code",
            "first_backend_blocker",
            "primary_reason",
            "fail_closed_reason_code",
            "blocker_code",
        ):
            value = _clean_identifier(source.get(key), max_length=128)
            if value:
                return value
    if reason_codes:
        return str(reason_codes[0])
    if not complete_initial_client_resolved:
        return "complete_initial_client_not_resolved"
    if not candidate_generation_attempted:
        return "complete_initial_generation_not_attempted"
    if not candidate_generated_before_display_gate:
        if composer_source == "unavailable" or candidate_status in {"unavailable", "not_generated", "not_attempted", "unknown"}:
            return "complete_initial_surface_unavailable"
        return "complete_initial_candidate_not_generated"
    return ""


def _first_blocker_family(
    first_blocker_code: str,
    *,
    reason_codes: Sequence[str],
    candidate_generated_before_display_gate: bool,
    candidate_status: str,
    composer_source: str,
) -> str:
    codes = [first_blocker_code, *list(reason_codes)]
    if _contains_any(codes, _SAFETY_CODES):
        return _FIRST_BLOCKER_FAMILY_SAFETY
    if _contains_any(codes, _INFRASTRUCTURE_CODES):
        return _FIRST_BLOCKER_FAMILY_INFRASTRUCTURE
    if _contains_any(codes, _COMPOSER_DISABLED_CODES):
        return _FIRST_BLOCKER_FAMILY_COMPOSER_DISABLED
    if _contains_any(codes, _AP0_ROLLOUT_CODES):
        return _FIRST_BLOCKER_FAMILY_AP0_ROLLOUT
    if _contains_any(codes, _MATERIAL_QUALITY_CODES):
        return _FIRST_BLOCKER_FAMILY_MATERIAL_QUALITY
    if _contains_any(codes, _COVERAGE_CODES):
        return _FIRST_BLOCKER_FAMILY_COVERAGE
    if _contains_any(codes, _REQUIRED_STRUCTURE_CODES):
        return _FIRST_BLOCKER_FAMILY_REQUIRED_STRUCTURE
    if _contains_any((first_blocker_code,), _SOURCE_UNAVAILABLE_CODES):
        return _FIRST_BLOCKER_FAMILY_SOURCE_UNAVAILABLE
    if _contains_any(codes, _SURFACE_REALIZER_CODES):
        return _FIRST_BLOCKER_FAMILY_SURFACE_REALIZER_UNAVAILABLE
    if _contains_any(codes, _SURFACE_SIGNATURE_CODES):
        return _FIRST_BLOCKER_FAMILY_SURFACE_SIGNATURE
    if _contains_any(codes, _SOURCE_UNAVAILABLE_CODES):
        return _FIRST_BLOCKER_FAMILY_SOURCE_UNAVAILABLE
    if _contains_any(codes, _SURFACE_FAILURE_CODES):
        return _FIRST_BLOCKER_FAMILY_SURFACE_FAILURE
    if not candidate_generated_before_display_gate and (
        composer_source == "unavailable" or candidate_status in {"unavailable", "not_generated", "not_attempted", "unknown"}
    ):
        return _FIRST_BLOCKER_FAMILY_SOURCE_UNAVAILABLE
    if first_blocker_code:
        return _FIRST_BLOCKER_FAMILY_UNKNOWN
    return _FIRST_BLOCKER_FAMILY_NONE


def _apply_lane_blocker_overrides(
    first_blocker_family: str,
    *,
    material_quality_family: str,
    surface_requirement_family: str,
) -> str:
    """Keep Step 5 lane decisions fail-closed before recomposition.

    Source-unavailable can move toward complete-initial surface recomposition only
    when the material is eligible and the surface requirement is a compatible
    public observation family.  Safety, infrastructure, unsupported material,
    and blocked surface families must not be reopened by a shallow-empty composer
    reason.
    """

    if first_blocker_family in _HARD_BLOCKER_FAMILIES:
        return first_blocker_family
    if surface_requirement_family == SURFACE_REQUIREMENT_SAFETY_BLOCKED:
        return _FIRST_BLOCKER_FAMILY_SAFETY
    if surface_requirement_family == SURFACE_REQUIREMENT_INFRASTRUCTURE_FAIL_CLOSED:
        return _FIRST_BLOCKER_FAMILY_INFRASTRUCTURE
    if surface_requirement_family in {
        SURFACE_REQUIREMENT_LOW_INFORMATION_OBSERVATION,
        SURFACE_REQUIREMENT_SELF_DENIAL_SAFE_STATE_ANSWER,
    }:
        return _FIRST_BLOCKER_FAMILY_MATERIAL_QUALITY
    if material_quality_family in {
        "unsupported",
        "material_unsupported",
        "unsupported_material",
        "material_quality_unsupported",
        "unsupported_input_material",
    }:
        return _FIRST_BLOCKER_FAMILY_MATERIAL_QUALITY
    return first_blocker_family


def _availability_diagnostics(first_blocker_family: str, reason_codes: Sequence[str]) -> dict[str, bool]:
    codes = [*reason_codes, first_blocker_family]
    return {
        "ap0_or_rollout_blocked": bool(first_blocker_family == _FIRST_BLOCKER_FAMILY_AP0_ROLLOUT or _contains_any(codes, _AP0_ROLLOUT_CODES)),
        "coverage_blocked": bool(first_blocker_family == _FIRST_BLOCKER_FAMILY_COVERAGE or _contains_any(codes, _COVERAGE_CODES)),
        "required_structure_blocked": bool(first_blocker_family == _FIRST_BLOCKER_FAMILY_REQUIRED_STRUCTURE or _contains_any(codes, _REQUIRED_STRUCTURE_CODES)),
        "material_quality_blocked": bool(first_blocker_family == _FIRST_BLOCKER_FAMILY_MATERIAL_QUALITY or _contains_any(codes, _MATERIAL_QUALITY_CODES)),
        "surface_signature_unavailable": bool(first_blocker_family == _FIRST_BLOCKER_FAMILY_SURFACE_SIGNATURE or _contains_any(codes, _SURFACE_SIGNATURE_CODES)),
        "surface_realizer_unavailable": bool(first_blocker_family == _FIRST_BLOCKER_FAMILY_SURFACE_REALIZER_UNAVAILABLE or _contains_any(codes, _SURFACE_REALIZER_CODES)),
    }


def _existing_gates_evaluated(sources: Sequence[Mapping[str, Any]]) -> dict[str, bool]:
    result: dict[str, bool] = {}
    for key in _EXISTING_GATE_KEYS:
        result[key] = bool(_pick_bool(sources, (key,)) is True)
    for source in sources:
        gate_results = _as_mapping(source.get("gate_results"))
        if not gate_results:
            continue
        gate_map = {
            "reader": "reader_gate_evaluated",
            "grounding": "grounding_gate_evaluated",
            "template_echo": "template_gate_evaluated",
            "display": "display_gate_evaluated",
            "visible_surface": "visible_surface_gate_evaluated",
            "runtime_surface": "runtime_surface_gate_evaluated",
        }
        for raw_gate, output_key in gate_map.items():
            payload = _as_mapping(gate_results.get(raw_gate))
            if payload and payload.get("evaluated") is True:
                result[output_key] = True
    result["all_existing_gates_evaluated"] = all(result.get(key) is True for key in _EXISTING_GATE_KEYS[:4])
    return result


def _normal_rebuild_allowance(
    *,
    candidate_generated_before_display_gate: bool,
    composer_source: str,
    first_blocker_family: str,
    two_stage_required: bool,
) -> tuple[bool, str]:
    if first_blocker_family in {
        _FIRST_BLOCKER_FAMILY_SOURCE_UNAVAILABLE,
        _FIRST_BLOCKER_FAMILY_SURFACE_REALIZER_UNAVAILABLE,
        _FIRST_BLOCKER_FAMILY_SURFACE_SIGNATURE,
    } or not candidate_generated_before_display_gate or composer_source == "unavailable":
        return False, NORMAL_REBUILD_BLOCKER_SOURCE_UNAVAILABLE_NOT_REBUILDABLE
    if two_stage_required:
        return False, NORMAL_REBUILD_BLOCKER_TWO_STAGE_REQUIRED
    if first_blocker_family == _FIRST_BLOCKER_FAMILY_SURFACE_FAILURE and composer_source == "ai_generated":
        return True, NORMAL_REBUILD_BLOCKER_NONE
    if not first_blocker_family:
        return False, NORMAL_REBUILD_BLOCKER_NOT_NEEDED
    return False, NORMAL_REBUILD_BLOCKER_NOT_REPAIRABLE_SURFACE_FAILURE


def _recovery_lane(
    *,
    first_blocker_family: str,
    material_sufficient: bool,
    surface_requirement_family: str,
    candidate_generated_before_display_gate: bool,
    normal_observation_rebuild_allowed: bool,
) -> str:
    if normal_observation_rebuild_allowed:
        return RECOVERY_LANE_NORMAL_OBSERVATION_REBUILD
    if first_blocker_family in _HARD_BLOCKER_FAMILIES:
        return RECOVERY_LANE_BLOCKED_BEFORE_RECOMPOSITION
    if first_blocker_family in {
        _FIRST_BLOCKER_FAMILY_SOURCE_UNAVAILABLE,
        _FIRST_BLOCKER_FAMILY_SURFACE_REALIZER_UNAVAILABLE,
        _FIRST_BLOCKER_FAMILY_SURFACE_SIGNATURE,
    }:
        if not material_sufficient:
            return RECOVERY_LANE_SOURCE_AVAILABILITY_INVESTIGATION
        if surface_requirement_family in _RECOMPOSITION_COMPATIBLE_SURFACE_REQUIREMENT_FAMILIES:
            return RECOVERY_LANE_COMPLETE_INITIAL_SURFACE_RECOMPOSITION
        if surface_requirement_family in _RECOMPOSITION_BLOCKING_SURFACE_REQUIREMENT_FAMILIES:
            return RECOVERY_LANE_BLOCKED_BEFORE_RECOMPOSITION
        return RECOVERY_LANE_SOURCE_AVAILABILITY_INVESTIGATION
    if not candidate_generated_before_display_gate:
        return RECOVERY_LANE_SOURCE_AVAILABILITY_INVESTIGATION
    return RECOVERY_LANE_NONE


def _pick_bool(sources: Sequence[Mapping[str, Any]], keys: Sequence[str]) -> bool | None:
    for source in sources:
        for key in keys:
            value = source.get(key)
            if isinstance(value, bool):
                return value
    return None


def _pick_identifier(sources: Sequence[Mapping[str, Any]], keys: Sequence[str]) -> str:
    for source in sources:
        for key in keys:
            value = _clean_identifier(source.get(key), max_length=128)
            if value:
                return value
    return ""


def _source_unavailable_reason_code(reason_codes: Sequence[str]) -> str:
    cleaned_reason_codes = [_clean_identifier(value, max_length=160) for value in reason_codes]
    for source_unavailable_code in _SOURCE_UNAVAILABLE_CODES:
        for value in cleaned_reason_codes:
            if not value:
                continue
            if value == source_unavailable_code or source_unavailable_code in value:
                return value
    return ""


def _blocked_before_recomposition_reason_code(reason_codes: Sequence[str]) -> str:
    cleaned_reason_codes = [_clean_identifier(value, max_length=160) for value in reason_codes]
    for group in _BLOCKED_BEFORE_RECOMPOSITION_CODE_GROUPS:
        for value in cleaned_reason_codes:
            if not value:
                continue
            if _contains_any((value,), group):
                return value
    return ""


def _contains_any(values: Iterable[str], needles: Iterable[str]) -> bool:
    cleaned = [_clean_identifier(value, max_length=160) for value in values]
    for value in cleaned:
        if not value:
            continue
        for needle in needles:
            if value == needle or needle in value:
                return True
    return False


def _false_public_contract() -> dict[str, bool]:
    return {key: False for key in _PUBLIC_CONTRACT_KEYS}


def _false_gate_policy() -> dict[str, bool]:
    return {key: False for key in _GATE_POLICY_KEYS}


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _as_sequence(value: Any) -> list[Any]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return list(value)
    if value is None:
        return []
    return [value]


def _clean_identifier(value: Any, *, max_length: int = 128) -> str:
    text = str(value or "").strip()[:max_length]
    if not text:
        return ""
    if _IDENTIFIER_RE.match(text):
        return text
    cleaned = "".join(char if re.match(r"[A-Za-z0-9_.:/\-]", char) else "_" for char in text)
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned[:max_length]


def _assert_no_forbidden_body_keys(value: Any) -> None:
    if isinstance(value, Mapping):
        forbidden = set(value.keys()) & _BODY_FORBIDDEN_EXACT_KEYS
        if forbidden:
            raise ValueError(f"P4 availability summary leaked body keys: {sorted(forbidden)}")
        for child in value.values():
            _assert_no_forbidden_body_keys(child)
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for item in value:
            _assert_no_forbidden_body_keys(item)


__all__ = [
    "COMPLETE_INITIAL_SURFACE_AVAILABILITY_PUBLIC_META_KEY",
    "COMPLETE_INITIAL_SURFACE_AVAILABILITY_SCHEMA_VERSION",
    "COMPLETE_INITIAL_SURFACE_AVAILABILITY_SOURCE_PHASE",
    "NORMAL_REBUILD_BLOCKER_SOURCE_UNAVAILABLE_NOT_REBUILDABLE",
    "RECOVERY_LANE_COMPLETE_INITIAL_SURFACE_RECOMPOSITION",
    "assert_complete_initial_surface_availability_summary",
    "build_complete_initial_surface_availability_summary",
    "complete_initial_surface_availability_public_summary",
]
