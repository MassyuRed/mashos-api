# -*- coding: utf-8 -*-
"""P7-HOLD-004 Phase16 Complete Composer red classification material.

R0/R1 scope only:
- freeze the currently reproduced Phase16 Complete Composer red as body-free
  observation material;
- classify it under P7-HOLD-004 without repairing Composer runtime behavior;
- keep P7 completion, P8 start, and release readiness closed.

The material intentionally stores identifiers, statuses, counts, booleans, and
reason codes only.  It never serializes raw input, candidate bodies, surface
bodies, reviewer free text, terminal output, or user-visible reply bodies.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final

from emlis_ai_p7_contracts import (
    P7_PHASE,
    assert_false_markers,
    assert_p7_no_body_payload_or_contract_mutation,
    body_free_flags,
    clean_identifier,
    dedupe_identifiers,
    public_contract_flags,
    safe_mapping,
)

P7_HOLD004_PHASE16_STEP: Final = "P7-HOLD-004_R0_R1_Phase16ComposerRedClassification_20260613"
P7_HOLD004_PHASE16_HOLD_ID: Final = "P7-HOLD-004"
P7_HOLD004_PHASE16_OBSERVATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.phase16_composer_observation.v1"
)
P7_HOLD004_PHASE16_BASELINE_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.phase16_baseline_freeze.v1"
)
P7_HOLD004_PHASE16_COMPOSER_CLASSIFICATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.phase16_composer_classification.v1"
)

_ALLOWED_PATH_STATUSES: Final[frozenset[str]] = frozenset(
    {
        "generated",
        "unavailable",
        "passed",
        "failed",
        "public_feedback_labelled",
        "public_feedback_unlabelled",
        "not_run",
        "blocked",
    }
)
_ALLOWED_CLASSIFICATION_STATUSES: Final[frozenset[str]] = frozenset(
    {
        "CLASSIFIED_UNRESOLVED",
        "IMPLEMENTATION_REPAIR_REQUIRED",
        "STALE_CONTRACT_REPLACEMENT_REQUIRED",
        "REPAIRED_PENDING_REGRESSION",
        "CLASSIFIED_CLOSED_FOR_TARGET_ONLY",
    }
)
_ALLOWED_CLASSIFICATIONS: Final[frozenset[str]] = frozenset(
    {
        "candidate_readiness_display_gate_boundary_mixed",
        "tone_guard_surface_readiness_regression",
        "two_stage_surface_structural_failure",
        "public_recovery_expected_direct_contract_stale",
        "metadata_summary_gap",
        "classified_unresolved",
    }
)
_ALLOWED_OWNER_LAYERS: Final[frozenset[str]] = frozenset(
    {
        "complete_composer_candidate_boundary",
        "complete_surface_realizer_tone_boundary",
        "two_stage_surface_structural_boundary",
        "phase17_self_repair_handoff_boundary",
        "public_recovery_layer",
        "stale_contract_expectation",
        "metadata_summary_boundary",
        "unknown",
    }
)
_ALLOWED_DECISION_KINDS: Final[frozenset[str]] = frozenset(
    {
        "repair_candidate_display_boundary",
        "replace_stale_direct_contract",
        "structural_repair_required",
        "classification_only",
    }
)
_ALLOWED_REPAIR_BRANCHES: Final[frozenset[str]] = frozenset({"R4-A", "R4-B", "R4-structural", "none"})
_STRUCTURAL_TWO_STAGE_ERROR_PREFIXES: Final[tuple[str, ...]] = ("two_stage_",)
_DISPLAY_QUALITY_REASON_MARKERS: Final[tuple[str, ...]] = (
    "tone_guard",
    "template_like",
    "ending_family_repetition",
    "phase17_surface_mode_policy_missing",
    "phase17_product_visible_fixture_not_reached",
)


def _clean_status(value: Any, *, default: str = "not_run") -> str:
    status = clean_identifier(value, default=default, max_length=80)
    return status if status in _ALLOWED_PATH_STATUSES else default


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return bool(value)
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on", "passed", "green"}


def _object_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    out: dict[str, Any] = {}
    for key in ("status", "composer_source", "composer_meta", "comment_text"):
        if hasattr(value, key):
            out[key] = getattr(value, key)
    return out


def _composer_meta_from_observed(observed_result: Any, composer_meta: Mapping[str, Any] | None = None) -> dict[str, Any]:
    explicit = safe_mapping(composer_meta)
    if explicit:
        return explicit
    data = _object_mapping(observed_result)
    return safe_mapping(data.get("composer_meta"))


def _observed_status_from_result(observed_result: Any, observed_status: Any = None) -> str:
    if observed_status is not None:
        return _clean_status(observed_status)
    data = _object_mapping(observed_result)
    status = data.get("status")
    if status is None and data.get("input_feedback_meta"):
        return "public_feedback_labelled" if data.get("input_feedback_comment") else "public_feedback_unlabelled"
    return _clean_status(status)


def _dedupe_from(*values: Any, limit: int = 80, max_length: int = 160) -> list[str]:
    flattened: list[Any] = []
    for value in values:
        if value is None:
            continue
        if isinstance(value, (str, bytes)):
            flattened.append(value)
        elif isinstance(value, Mapping):
            flattened.extend(value.values())
        elif isinstance(value, Sequence):
            flattened.extend(value)
        else:
            flattened.append(value)
    return dedupe_identifiers(flattened, limit=limit, max_length=max_length)


def _surface_meta(meta: Mapping[str, Any]) -> dict[str, Any]:
    surface = safe_mapping(meta.get("surface_realizer"))
    if surface:
        return surface
    return safe_mapping(meta.get("surface_meta"))


def _two_stage_summary_from_meta(meta: Mapping[str, Any]) -> dict[str, Any]:
    direct = safe_mapping(meta.get("two_stage_surface_realization"))
    if direct:
        return direct
    surface = _surface_meta(meta)
    nested = safe_mapping(surface.get("two_stage_surface_realization"))
    if nested:
        return nested
    counts = safe_mapping(meta.get("two_stage_section_line_counts"))
    if any(
        key in meta
        for key in (
            "two_stage_surface_realization_required",
            "two_stage_surface_realization_applied",
            "two_stage_surface_labels_present",
            "two_stage_surface_structural_ready",
            "two_stage_observation_section_non_empty",
            "two_stage_reception_section_non_empty",
        )
    ):
        return {
            "required": meta.get("two_stage_surface_realization_required"),
            "applied": meta.get("two_stage_surface_realization_applied"),
            "labels_present": meta.get("two_stage_surface_labels_present"),
            "section_order_valid": meta.get("two_stage_section_order_valid", True),
            "observation_section_non_empty": meta.get("two_stage_observation_section_non_empty"),
            "reception_section_non_empty": meta.get("two_stage_reception_section_non_empty"),
            "section_line_counts": counts,
            "validation_errors": meta.get("two_stage_validation_error_codes") or [],
            "daily_unpleasant_surface_quality_applied": meta.get("daily_unpleasant_surface_quality_applied"),
            "two_stage_mode_specific_surface_applied": meta.get("two_stage_mode_specific_surface_applied"),
        }
    return {}


def _section_line_counts(two_stage: Mapping[str, Any]) -> dict[str, int]:
    counts = safe_mapping(two_stage.get("section_line_counts"))
    out: dict[str, int] = {}
    for key in ("observation", "reception"):
        try:
            out[key] = int(counts.get(key) or 0)
        except (TypeError, ValueError):
            out[key] = 0
    return out


def _validation_error_codes(meta: Mapping[str, Any]) -> list[str]:
    surface = _surface_meta(meta)
    two_stage = _two_stage_summary_from_meta(meta)
    return _dedupe_from(
        surface.get("validation_errors"),
        meta.get("surface_validation_error_codes"),
        two_stage.get("validation_errors"),
        meta.get("two_stage_validation_error_codes"),
        limit=80,
        max_length=160,
    )


def _reason_codes(meta: Mapping[str, Any]) -> list[str]:
    surface = _surface_meta(meta)
    return _dedupe_from(
        meta.get("primary_reason"),
        meta.get("rejection_reasons"),
        meta.get("phase16_7_unavailable_reason_codes"),
        meta.get("two_stage_unavailable_reason_codes"),
        meta.get("phase17_7_unavailable_reason_codes"),
        meta.get("phase17_7_self_repair_handoff_reason_codes"),
        meta.get("surface_display_quality_reason_codes_before_display_gate"),
        surface.get("phase17_7_surface_repair_reason_codes"),
        surface.get("anti_template_major_reasons"),
        limit=100,
        max_length=160,
    )


def _two_stage_surface_summary(meta: Mapping[str, Any]) -> dict[str, Any]:
    two_stage = _two_stage_summary_from_meta(meta)
    counts = _section_line_counts(two_stage)
    validation_errors = _dedupe_from(two_stage.get("validation_errors"), limit=80, max_length=160)
    observation_non_empty = _bool(two_stage.get("observation_section_non_empty")) or counts.get("observation", 0) > 0
    reception_non_empty = _bool(two_stage.get("reception_section_non_empty")) or counts.get("reception", 0) > 0
    section_order_valid = bool(two_stage.get("section_order_valid", True))
    if any(str(error).endswith("section_order_invalid") for error in validation_errors):
        section_order_valid = False
    return {
        "required": _bool(two_stage.get("required") or meta.get("two_stage_applicability_required")),
        "applied": _bool(two_stage.get("applied") or meta.get("two_stage_surface_realization_applied")),
        "labels_present": _bool(two_stage.get("labels_present")),
        "section_order_valid": section_order_valid,
        "observation_section_non_empty": observation_non_empty,
        "reception_section_non_empty": reception_non_empty,
        "section_line_counts": counts,
        "validation_error_codes": validation_errors,
        "daily_unpleasant_surface_quality_applied": _bool(
            two_stage.get("daily_unpleasant_surface_quality_applied")
            or safe_mapping(two_stage.get("daily_unpleasant_reception_surface_quality")).get("applied")
        ),
        "two_stage_mode_specific_surface_applied": _bool(
            two_stage.get("two_stage_mode_specific_surface_applied")
            or safe_mapping(two_stage.get("two_stage_mode_specific_surface_policy")).get("applied")
        ),
        "comment_text_body_included": False,
        "raw_input_included": False,
    }


def _surface_quality_summary(meta: Mapping[str, Any]) -> dict[str, Any]:
    surface = _surface_meta(meta)
    validation_errors = _validation_error_codes(meta)
    reason_codes = _reason_codes(meta)
    structural = _two_stage_surface_summary(meta)
    structural_ready = (
        meta.get("two_stage_surface_structural_ready") is True
        or meta.get("surface_structural_ready_before_display_gate") is True
        or (
            bool(structural.get("applied"))
            and bool(structural.get("labels_present"))
            and bool(structural.get("section_order_valid"))
            and bool(structural.get("observation_section_non_empty"))
            and bool(structural.get("reception_section_non_empty"))
            and not any(str(error).startswith(_STRUCTURAL_TWO_STAGE_ERROR_PREFIXES) for error in structural.get("validation_error_codes", []))
        )
    )
    display_quality_blocked = bool(
        meta.get("surface_display_quality_blocked_before_display_gate")
        or meta.get("surface_display_quality_blocked")
        or any(
            any(marker in str(code) for marker in _DISPLAY_QUALITY_REASON_MARKERS)
            for code in [*validation_errors, *reason_codes]
        )
        or (surface.get("ready") is False and structural_ready)
    )
    return {
        "surface_status": clean_identifier(
            surface.get("status") or meta.get("surface_status"),
            default=clean_identifier(meta.get("status"), default="unknown", max_length=80),
            max_length=80,
        ),
        "surface_ready": bool(surface.get("ready")) if "ready" in surface else bool(meta.get("surface_ready") or meta.get("ready")),
        "surface_structural_ready": structural_ready,
        "surface_display_quality_blocked": display_quality_blocked,
        "validation_error_codes": validation_errors,
        "phase17_reason_codes": _dedupe_from(meta.get("phase17_7_unavailable_reason_codes"), limit=80, max_length=160),
        "self_repair_handoff_reason_codes": _dedupe_from(
            meta.get("phase17_7_self_repair_handoff_reason_codes"), limit=80, max_length=160
        ),
        "gate_relaxed": False,
    }


def _owner_layer_for_observation(
    *,
    observed_status: str,
    two_stage_surface_summary: Mapping[str, Any],
    surface_quality_summary: Mapping[str, Any],
    public_reached: bool,
) -> str:
    structural_ready = bool(surface_quality_summary.get("surface_structural_ready"))
    if public_reached:
        return "public_recovery_layer"
    if observed_status == "unavailable" and structural_ready and surface_quality_summary.get("surface_display_quality_blocked") is True:
        return "complete_surface_realizer_tone_boundary"
    if observed_status == "unavailable" and not structural_ready and two_stage_surface_summary.get("required") is True:
        return "two_stage_surface_structural_boundary"
    if observed_status == "unavailable":
        return "complete_composer_candidate_boundary"
    return "unknown"


def build_p7_hold004_phase16_composer_observation(
    *,
    path_id: Any,
    test_ref: Any,
    fixture_family: Any = "daily_unpleasant_encounter_A",
    observed_result: Any = None,
    composer_meta: Mapping[str, Any] | None = None,
    observed_status: Any = None,
    expected_status_kind: Any = "generated_candidate_before_display_gate",
    public_reached: bool = False,
    labelled_two_stage_reached: bool = False,
    candidate_generated_before_display_gate: bool | None = None,
    reason_codes: Sequence[Any] = (),
    validation_error_codes: Sequence[Any] = (),
) -> dict[str, Any]:
    """Build one body-free path observation row for HOLD-004 Phase16 red."""

    status = _observed_status_from_result(observed_result, observed_status)
    meta = _composer_meta_from_observed(observed_result, composer_meta)
    two_stage_summary = _two_stage_surface_summary(meta)
    quality_summary = _surface_quality_summary(meta)
    observed_reason_codes = _dedupe_from(_reason_codes(meta), reason_codes, limit=100, max_length=160)
    observed_validation_errors = _dedupe_from(_validation_error_codes(meta), validation_error_codes, limit=100, max_length=160)
    if candidate_generated_before_display_gate is None:
        candidate_generated_before_display_gate = _bool(meta.get("candidate_generated_before_display_gate")) or status == "generated"
    public_path_reached = bool(public_reached or status.startswith("public_feedback"))
    labelled_reached = bool(labelled_two_stage_reached or status == "public_feedback_labelled")
    owner_layer = _owner_layer_for_observation(
        observed_status=status,
        two_stage_surface_summary=two_stage_summary,
        surface_quality_summary=quality_summary,
        public_reached=public_path_reached,
    )
    observation = {
        "schema_version": P7_HOLD004_PHASE16_OBSERVATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_HOLD004_PHASE16_STEP,
        "hold_id": P7_HOLD004_PHASE16_HOLD_ID,
        "observation_id": clean_identifier(
            f"p7_hold004_phase16_{clean_identifier(path_id, default='unknown_path', max_length=100)}",
            max_length=160,
        ),
        "path_id": clean_identifier(path_id, default="unknown_path", max_length=160),
        "test_ref": clean_identifier(test_ref, default="unknown_test_ref", max_length=220),
        "fixture_family": clean_identifier(fixture_family, default="unknown_fixture_family", max_length=120),
        "observed_status": status,
        "expected_status_kind": clean_identifier(expected_status_kind, default="unknown_expected_status", max_length=160),
        "public_reached": public_path_reached,
        "labelled_two_stage_reached": labelled_reached,
        "candidate_generated_before_display_gate": bool(candidate_generated_before_display_gate),
        "owner_layer": owner_layer,
        "reason_codes": observed_reason_codes,
        "validation_error_codes": observed_validation_errors,
        "two_stage_surface_summary": two_stage_summary,
        "surface_quality_summary": quality_summary,
        "release_allowed": False,
        "p8_start_allowed": False,
        "body_free": True,
        "public_contract": public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
    }
    assert_p7_hold004_phase16_composer_observation_contract(observation)
    return observation


def assert_p7_hold004_phase16_composer_observation_contract(observation: Mapping[str, Any]) -> bool:
    data = safe_mapping(observation)
    if data.get("schema_version") != P7_HOLD004_PHASE16_OBSERVATION_SCHEMA_VERSION:
        raise ValueError("unexpected HOLD-004 Phase16 observation schema_version")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_PHASE16_HOLD_ID:
        raise ValueError("unexpected HOLD-004 Phase16 observation phase/hold")
    if data.get("observed_status") not in _ALLOWED_PATH_STATUSES:
        raise ValueError("unsupported HOLD-004 Phase16 observed_status")
    if data.get("owner_layer") not in _ALLOWED_OWNER_LAYERS:
        raise ValueError("unsupported HOLD-004 Phase16 owner_layer")
    if data.get("release_allowed") is not False or data.get("p8_start_allowed") is not False:
        raise ValueError("HOLD-004 Phase16 observation must not allow release or P8 start")
    if data.get("body_free") is not True:
        raise ValueError("HOLD-004 Phase16 observation must be body-free")
    two_stage = safe_mapping(data.get("two_stage_surface_summary"))
    if two_stage.get("comment_text_body_included") is not False or two_stage.get("raw_input_included") is not False:
        raise ValueError("HOLD-004 two-stage summary must keep body markers false")
    quality = safe_mapping(data.get("surface_quality_summary"))
    if quality.get("gate_relaxed") is not False:
        raise ValueError("HOLD-004 surface quality summary must not relax gates")
    if data.get("labelled_two_stage_reached") is True and data.get("public_reached") is not True and data.get("observed_status") != "generated":
        raise ValueError("labelled public feedback requires public_reached or generated path")
    assert_false_markers(safe_mapping(data.get("public_contract")), source="p7_hold004_phase16_observation.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_hold004_phase16_observation.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_hold004_phase16_observation")
    return True


def _select_summary(observations: Sequence[Mapping[str, Any]], key: str) -> dict[str, Any]:
    for observation in observations:
        summary = safe_mapping(safe_mapping(observation).get(key))
        if summary.get("required") is True or summary.get("surface_structural_ready") is True or summary.get("validation_error_codes"):
            return summary
    return safe_mapping(safe_mapping(observations[0]).get(key)) if observations else {}


def classify_p7_hold004_phase16_composer_red(observations: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Return the R1 classification decision material for Phase16 observations.

    This is intentionally not R3 final decision logic.  It classifies the red as
    unresolved and points to the owner boundary without performing any repair.
    """

    rows = [safe_mapping(row) for row in observations]
    structural_failure = any(
        safe_mapping(row.get("two_stage_surface_summary")).get("required") is True
        and safe_mapping(row.get("surface_quality_summary")).get("surface_structural_ready") is False
        and row.get("observed_status") == "unavailable"
        for row in rows
    )
    boundary_mixed = any(
        row.get("observed_status") == "unavailable"
        and safe_mapping(row.get("surface_quality_summary")).get("surface_structural_ready") is True
        and safe_mapping(row.get("surface_quality_summary")).get("surface_display_quality_blocked") is True
        for row in rows
    )
    public_labelled = any(row.get("public_reached") is True and row.get("labelled_two_stage_reached") is True for row in rows)
    if structural_failure:
        classification = "two_stage_surface_structural_failure"
        owner_layers = ["two_stage_surface_structural_boundary", "complete_composer_candidate_boundary"]
    elif boundary_mixed:
        classification = "candidate_readiness_display_gate_boundary_mixed"
        owner_layers = ["complete_surface_realizer_tone_boundary", "complete_composer_candidate_boundary"]
        if public_labelled:
            owner_layers.append("public_recovery_layer")
    elif public_labelled and any(row.get("observed_status") == "unavailable" for row in rows):
        classification = "public_recovery_expected_direct_contract_stale"
        owner_layers = ["public_recovery_layer", "stale_contract_expectation"]
    else:
        classification = "classified_unresolved"
        owner_layers = ["unknown"]
    return {
        "classification": classification,
        "owner_layers": dedupe_identifiers(owner_layers, limit=8, max_length=120),
        "status": "CLASSIFIED_UNRESOLVED",
        "decision_kind": "classification_only",
        "repair_branch": "none",
        "public_daily_path_labelled": public_labelled,
        "direct_or_conversation_unavailable": any(
            row.get("observed_status") == "unavailable" and row.get("public_reached") is not True for row in rows
        ),
    }


def _path_status_row(observation: Mapping[str, Any]) -> dict[str, Any]:
    data = safe_mapping(observation)
    return {
        "path_id": clean_identifier(data.get("path_id"), default="unknown_path", max_length=160),
        "observed_status": _clean_status(data.get("observed_status")),
        "expected_status_kind": clean_identifier(data.get("expected_status_kind"), default="unknown_expected_status", max_length=160),
        "public_reached": data.get("public_reached") is True,
        "labelled_two_stage_reached": data.get("labelled_two_stage_reached") is True,
        "candidate_generated_before_display_gate": data.get("candidate_generated_before_display_gate") is True,
        "owner_layer": clean_identifier(data.get("owner_layer"), default="unknown", max_length=120),
        "reason_codes": dedupe_identifiers(data.get("reason_codes"), limit=80, max_length=160),
        "validation_error_codes": dedupe_identifiers(data.get("validation_error_codes"), limit=80, max_length=160),
    }


def build_p7_hold004_phase16_composer_classification(
    *,
    observations: Sequence[Mapping[str, Any]],
    classification_id: Any = "p7_hold004_phase16_complete_composer_daily_unpleasant_A",
) -> dict[str, Any]:
    """Build the body-free R1 classification material for P7-HOLD-004."""

    sanitized_observations: list[dict[str, Any]] = []
    for observation in observations:
        assert_p7_hold004_phase16_composer_observation_contract(observation)
        sanitized_observations.append(dict(observation))
    if not sanitized_observations:
        raise ValueError("HOLD-004 Phase16 classification requires at least one observation")
    decision = classify_p7_hold004_phase16_composer_red(sanitized_observations)
    source_refs = dedupe_identifiers((row.get("test_ref") for row in sanitized_observations), limit=40, max_length=220)
    classification = {
        "schema_version": P7_HOLD004_PHASE16_COMPOSER_CLASSIFICATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_HOLD004_PHASE16_STEP,
        "hold_id": P7_HOLD004_PHASE16_HOLD_ID,
        "classification_id": clean_identifier(classification_id, default="p7_hold004_phase16_complete_composer_unknown", max_length=160),
        "status": decision["status"],
        "classification": decision["classification"],
        "owner_layers": decision["owner_layers"],
        "source_test_refs": source_refs,
        "path_statuses": [_path_status_row(row) for row in sanitized_observations],
        "two_stage_surface_summary": _select_summary(sanitized_observations, "two_stage_surface_summary"),
        "surface_quality_summary": _select_summary(sanitized_observations, "surface_quality_summary"),
        "decision": {
            "decision_kind": decision["decision_kind"],
            "repair_branch": decision["repair_branch"],
            "full_suite_green_claim_allowed": False,
            "hold004_close_allowed": False,
            "p7_complete_claim_allowed": False,
            "p8_start_allowed": False,
            "release_allowed": False,
        },
        "required_followup_fixes": ["phase16_complete_composer_candidate_boundary"],
        "public_daily_path_labelled": decision["public_daily_path_labelled"],
        "direct_or_conversation_unavailable": decision["direct_or_conversation_unavailable"],
        "full_backend_suite_green_confirmed": False,
        "full_backend_suite_green_claim_allowed": False,
        "hold004_close_allowed": False,
        "release_allowed": False,
        "p8_start_allowed": False,
        "body_free": True,
        "public_contract": public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
    }
    assert_p7_hold004_phase16_composer_classification_contract(classification)
    return classification


def assert_p7_hold004_phase16_composer_classification_contract(classification: Mapping[str, Any]) -> bool:
    data = safe_mapping(classification)
    if data.get("schema_version") != P7_HOLD004_PHASE16_COMPOSER_CLASSIFICATION_SCHEMA_VERSION:
        raise ValueError("unexpected HOLD-004 Phase16 classification schema_version")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_PHASE16_HOLD_ID:
        raise ValueError("unexpected HOLD-004 Phase16 classification phase/hold")
    if data.get("status") not in _ALLOWED_CLASSIFICATION_STATUSES:
        raise ValueError("unsupported HOLD-004 Phase16 classification status")
    if data.get("classification") not in _ALLOWED_CLASSIFICATIONS:
        raise ValueError("unsupported HOLD-004 Phase16 classification")
    owner_layers = dedupe_identifiers(data.get("owner_layers"), limit=20, max_length=120)
    if not owner_layers or any(layer not in _ALLOWED_OWNER_LAYERS for layer in owner_layers):
        raise ValueError("unsupported HOLD-004 Phase16 owner layer")
    path_statuses = data.get("path_statuses")
    if not isinstance(path_statuses, list) or not path_statuses:
        raise ValueError("HOLD-004 Phase16 classification requires path_statuses")
    for path_status in path_statuses:
        row = safe_mapping(path_status)
        if row.get("observed_status") not in _ALLOWED_PATH_STATUSES:
            raise ValueError("unsupported HOLD-004 Phase16 path status")
    decision = safe_mapping(data.get("decision"))
    if decision.get("decision_kind") not in _ALLOWED_DECISION_KINDS:
        raise ValueError("unsupported HOLD-004 Phase16 decision kind")
    if decision.get("repair_branch") not in _ALLOWED_REPAIR_BRANCHES:
        raise ValueError("unsupported HOLD-004 Phase16 repair branch")
    for key in (
        "full_suite_green_claim_allowed",
        "hold004_close_allowed",
        "p7_complete_claim_allowed",
        "p8_start_allowed",
        "release_allowed",
    ):
        if decision.get(key) is not False:
            raise ValueError(f"HOLD-004 Phase16 decision must keep {key}=False")
    for key in (
        "full_backend_suite_green_confirmed",
        "full_backend_suite_green_claim_allowed",
        "hold004_close_allowed",
        "release_allowed",
        "p8_start_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"HOLD-004 Phase16 classification must keep {key}=False")
    if data.get("body_free") is not True:
        raise ValueError("HOLD-004 Phase16 classification must be body-free")
    assert_false_markers(safe_mapping(data.get("public_contract")), source="p7_hold004_phase16_classification.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_hold004_phase16_classification.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_hold004_phase16_classification")
    return True


def build_p7_hold004_phase16_baseline_freeze(
    *,
    observations: Sequence[Mapping[str, Any]],
    full_backend_suite_collect_count: int = 2604,
    target_test_file_failure_count: int = 2,
    full_backend_suite_maxfail_first_failure_ref: Any = "tests/test_emlis_ai_complete_composer_two_stage_surface_connection.py",
) -> dict[str, Any]:
    """Build R0 body-free baseline freeze material for the reproduced red."""

    sanitized_observations: list[dict[str, Any]] = []
    for observation in observations:
        assert_p7_hold004_phase16_composer_observation_contract(observation)
        sanitized_observations.append(dict(observation))
    if not sanitized_observations:
        raise ValueError("HOLD-004 Phase16 baseline freeze requires observations")
    direct_red = any(row.get("observed_status") == "unavailable" for row in sanitized_observations)
    freeze = {
        "schema_version": P7_HOLD004_PHASE16_BASELINE_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_HOLD004_PHASE16_STEP,
        "hold_id": P7_HOLD004_PHASE16_HOLD_ID,
        "freeze_id": "p7_hold004_phase16_baseline_freeze_20260613",
        "status": "RED_REPRODUCED" if direct_red else "BASELINE_RECORDED",
        "observations": sanitized_observations,
        "path_statuses": [_path_status_row(row) for row in sanitized_observations],
        "full_backend_suite_collect_count": int(full_backend_suite_collect_count),
        "target_test_file_failure_count": int(target_test_file_failure_count),
        "full_backend_suite_maxfail_first_failure_ref": clean_identifier(
            full_backend_suite_maxfail_first_failure_ref, default="unknown_first_failure", max_length=220
        ),
        "full_backend_suite_green_confirmed": False,
        "full_backend_suite_green_claim_allowed": False,
        "p7_hold004_preserved": True,
        "release_allowed": False,
        "p8_start_allowed": False,
        "body_free": True,
        "public_contract": public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
    }
    assert_p7_hold004_phase16_baseline_freeze_contract(freeze)
    return freeze


def assert_p7_hold004_phase16_baseline_freeze_contract(freeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(freeze)
    if data.get("schema_version") != P7_HOLD004_PHASE16_BASELINE_FREEZE_SCHEMA_VERSION:
        raise ValueError("unexpected HOLD-004 Phase16 baseline freeze schema_version")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_PHASE16_HOLD_ID:
        raise ValueError("unexpected HOLD-004 Phase16 baseline freeze phase/hold")
    if data.get("full_backend_suite_green_confirmed") is not False:
        raise ValueError("HOLD-004 baseline freeze must not confirm full backend suite green")
    if data.get("full_backend_suite_green_claim_allowed") is not False:
        raise ValueError("HOLD-004 baseline freeze must not allow full backend suite green claim")
    if data.get("p7_hold004_preserved") is not True:
        raise ValueError("HOLD-004 baseline freeze must preserve P7-HOLD-004")
    if data.get("release_allowed") is not False or data.get("p8_start_allowed") is not False:
        raise ValueError("HOLD-004 baseline freeze must keep release and P8 closed")
    if data.get("body_free") is not True:
        raise ValueError("HOLD-004 baseline freeze must be body-free")
    observations = data.get("observations")
    if not isinstance(observations, list) or not observations:
        raise ValueError("HOLD-004 baseline freeze requires observation rows")
    for observation in observations:
        assert_p7_hold004_phase16_composer_observation_contract(safe_mapping(observation))
    assert_false_markers(safe_mapping(data.get("public_contract")), source="p7_hold004_phase16_baseline_freeze.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_hold004_phase16_baseline_freeze.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_hold004_phase16_baseline_freeze")
    return True


__all__ = [
    "P7_HOLD004_PHASE16_BASELINE_FREEZE_SCHEMA_VERSION",
    "P7_HOLD004_PHASE16_COMPOSER_CLASSIFICATION_SCHEMA_VERSION",
    "P7_HOLD004_PHASE16_HOLD_ID",
    "P7_HOLD004_PHASE16_OBSERVATION_SCHEMA_VERSION",
    "P7_HOLD004_PHASE16_STEP",
    "assert_p7_hold004_phase16_baseline_freeze_contract",
    "assert_p7_hold004_phase16_composer_classification_contract",
    "assert_p7_hold004_phase16_composer_observation_contract",
    "build_p7_hold004_phase16_baseline_freeze",
    "build_p7_hold004_phase16_composer_classification",
    "build_p7_hold004_phase16_composer_observation",
    "classify_p7_hold004_phase16_composer_red",
]
