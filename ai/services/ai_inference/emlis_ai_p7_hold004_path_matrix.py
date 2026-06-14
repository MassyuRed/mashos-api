# -*- coding: utf-8 -*-
"""P7-HOLD-004 Phase16 path matrix and decision-rule material.

R2/R3 scope only:
- keep the R0/R1 Phase16 Complete Composer red material intact;
- separate direct, conversation, public daily, and adjacent public fixture paths;
- fix the decision rule before runtime repair or contract replacement;
- keep P7-HOLD-004 unresolved, P8 closed, release closed, and all material
  body-free.

The module stores only identifiers, statuses, booleans, counts, and reason codes.
It does not serialize raw input, reply bodies, candidate bodies, surface bodies,
reviewer free text, or terminal output.
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
from emlis_ai_p7_hold004_phase16_composer_classification import (
    P7_HOLD004_PHASE16_HOLD_ID,
    P7_HOLD004_PHASE16_STEP,
    assert_p7_hold004_phase16_composer_observation_contract,
)

P7_HOLD004_PHASE16_PATH_MATRIX_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.phase16_path_matrix.v1"
)
P7_HOLD004_PHASE16_PATH_MATRIX_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.phase16_path_matrix_row.v1"
)
P7_HOLD004_PHASE16_DECISION_RULE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.phase16_decision_rule.v1"
)
P7_HOLD004_PHASE16_PUBLIC_ADJACENT_RED_REGISTRATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.phase16_public_adjacent_red_registration.v1"
)
P7_HOLD004_PHASE16_R2_R3_STEP: Final = "P7-HOLD-004_R2_R3_PathMatrixDecisionRule_20260613"
P7_HOLD004_PHASE16_PATH_MATRIX_ID: Final = "p7_hold004_phase16_complete_composer_path_matrix_20260613"
P7_HOLD004_PHASE16_DECISION_RULE_ID: Final = "p7_hold004_phase16_complete_composer_decision_rule_20260613"
P7_HOLD004_PHASE16_PUBLIC_ADJACENT_RED_REGISTRATION_ID: Final = (
    "p7_hold004_phase16_public_adjacent_red_registration_20260613"
)
P7_HOLD004_PHASE16_R4B_REPLACEMENT_DESIGN_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.phase16_r4b_stale_contract_replacement_design.v1"
)
P7_HOLD004_PHASE16_R4B_REPLACEMENT_DESIGN_ID: Final = (
    "p7_hold004_phase16_r4b_stale_contract_replacement_design_20260613"
)

_REQUIRED_PRIMARY_PATH_IDS: Final[tuple[str, ...]] = (
    "complete_composer_direct_daily_unpleasant_A",
    "conversation_composer_daily_unpleasant_A",
    "emotion_submit_public_daily_unpleasant_A",
)
_ADJACENT_PUBLIC_PATH_ID: Final = "emotion_submit_public_product_visible_fixture_suite"
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
_ALLOWED_DECISION_STATUSES: Final[frozenset[str]] = frozenset(
    {
        "IMPLEMENTATION_REPAIR_REQUIRED",
        "STALE_CONTRACT_REPLACEMENT_REQUIRED",
        "STRUCTURAL_REPAIR_REQUIRED",
        "CLASSIFIED_UNRESOLVED",
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
_ALLOWED_CLASSIFICATIONS: Final[frozenset[str]] = frozenset(
    {
        "candidate_readiness_display_gate_boundary_mixed",
        "public_recovery_expected_direct_contract_stale",
        "two_stage_surface_structural_failure",
        "classified_unresolved",
    }
)
_DISPLAY_BLOCKER_MARKERS: Final[tuple[str, ...]] = (
    "tone_guard",
    "ending_family_repetition",
    "template_like",
    "phase17_surface_mode_policy_missing",
    "phase17_product_visible_fixture_not_reached",
)
_STRUCTURAL_ERROR_MARKERS: Final[tuple[str, ...]] = (
    "section_missing",
    "label_missing",
    "section_order_invalid",
    "two_stage_structural",
    "two_stage_section",
    "forbidden_surface_hit",
)


def _status(value: Any, *, default: str = "not_run") -> str:
    status = clean_identifier(value, default=default, max_length=80)
    return status if status in _ALLOWED_PATH_STATUSES else default


def _owner(value: Any, *, default: str = "unknown") -> str:
    owner_layer = clean_identifier(value, default=default, max_length=120)
    return owner_layer if owner_layer in _ALLOWED_OWNER_LAYERS else default


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return bool(value)
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on", "passed", "green"}


def _as_int(value: Any, *, default: int = 0) -> int:
    try:
        if value is None or value == "" or isinstance(value, bool):
            return int(default)
        return int(float(value))
    except (TypeError, ValueError):
        return int(default)


def _surface_display_ready(*, structural_ready: bool, display_quality_blocked: bool, observed_status: str, labelled: bool) -> bool:
    if labelled or observed_status in {"generated", "public_feedback_labelled", "passed"}:
        return True
    return structural_ready and not display_quality_blocked


def _row_from_observation(observation: Mapping[str, Any]) -> dict[str, Any]:
    assert_p7_hold004_phase16_composer_observation_contract(observation)
    data = safe_mapping(observation)
    two_stage = safe_mapping(data.get("two_stage_surface_summary"))
    quality = safe_mapping(data.get("surface_quality_summary"))
    structural_ready = quality.get("surface_structural_ready") is True
    display_quality_blocked = quality.get("surface_display_quality_blocked") is True
    observed_status = _status(data.get("observed_status"))
    labelled = data.get("labelled_two_stage_reached") is True
    return build_p7_hold004_phase16_path_matrix_row(
        path_id=data.get("path_id"),
        test_ref=data.get("test_ref"),
        fixture_family=data.get("fixture_family"),
        observed_status=observed_status,
        expected_contract_status=data.get("expected_status_kind"),
        public_reached=data.get("public_reached") is True,
        labelled_two_stage_reached=labelled,
        candidate_generated_before_display_gate=data.get("candidate_generated_before_display_gate") is True,
        surface_structural_ready=structural_ready,
        surface_display_ready=_surface_display_ready(
            structural_ready=structural_ready,
            display_quality_blocked=display_quality_blocked,
            observed_status=observed_status,
            labelled=labelled,
        ),
        surface_display_quality_blocked=display_quality_blocked,
        two_stage_surface_required=two_stage.get("required") is True,
        two_stage_surface_applied=two_stage.get("applied") is True,
        two_stage_labels_present=two_stage.get("labels_present") is True,
        two_stage_section_order_valid=two_stage.get("section_order_valid") is not False,
        observation_section_non_empty=two_stage.get("observation_section_non_empty") is True,
        reception_section_non_empty=two_stage.get("reception_section_non_empty") is True,
        two_stage_validation_error_codes=two_stage.get("validation_error_codes"),
        reason_codes=data.get("reason_codes"),
        validation_error_codes=data.get("validation_error_codes"),
        owner_layer=data.get("owner_layer"),
        red_refs=["P7-HOLD-004-PHASE16-COMPLETE-COMPOSER-RED"]
        if observed_status == "unavailable" and data.get("public_reached") is not True
        else [],
        hold_refs=[P7_HOLD004_PHASE16_HOLD_ID],
        is_primary_target=clean_identifier(data.get("path_id"), max_length=160) in _REQUIRED_PRIMARY_PATH_IDS,
        is_adjacent_red=False,
    )


def build_p7_hold004_phase16_path_matrix_row(
    *,
    path_id: Any,
    test_ref: Any,
    fixture_family: Any,
    observed_status: Any,
    expected_contract_status: Any,
    public_reached: Any = False,
    labelled_two_stage_reached: Any = False,
    candidate_generated_before_display_gate: Any = False,
    surface_structural_ready: Any = False,
    surface_display_ready: Any = False,
    surface_display_quality_blocked: Any = False,
    two_stage_surface_required: Any = False,
    two_stage_surface_applied: Any = False,
    two_stage_labels_present: Any = False,
    two_stage_section_order_valid: Any = True,
    observation_section_non_empty: Any = False,
    reception_section_non_empty: Any = False,
    two_stage_validation_error_codes: Sequence[Any] | Any = (),
    reason_codes: Sequence[Any] | Any = (),
    validation_error_codes: Sequence[Any] | Any = (),
    owner_layer: Any = "unknown",
    red_refs: Sequence[Any] | Any = (),
    hold_refs: Sequence[Any] | Any = (P7_HOLD004_PHASE16_HOLD_ID,),
    is_primary_target: Any = False,
    is_adjacent_red: Any = False,
) -> dict[str, Any]:
    """Build one R2 path matrix row from body-free identifiers and flags."""

    row_status = _status(observed_status)
    path = clean_identifier(path_id, default="unknown_path", max_length=160)
    row = {
        "schema_version": P7_HOLD004_PHASE16_PATH_MATRIX_ROW_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_HOLD004_PHASE16_R2_R3_STEP,
        "hold_id": P7_HOLD004_PHASE16_HOLD_ID,
        "row_id": clean_identifier(f"p7_hold004_phase16_path_{path}", max_length=180),
        "path_id": path,
        "test_ref": clean_identifier(test_ref, default="unknown_test_ref", max_length=220),
        "fixture_family": clean_identifier(fixture_family, default="unknown_fixture_family", max_length=120),
        "observed_status": row_status,
        "expected_contract_status": clean_identifier(expected_contract_status, default="unknown_expected_status", max_length=160),
        "public_reached": _bool(public_reached),
        "labelled_two_stage_reached": _bool(labelled_two_stage_reached),
        "candidate_generated_before_display_gate": _bool(candidate_generated_before_display_gate),
        "surface_structural_ready": _bool(surface_structural_ready),
        "surface_display_ready": _bool(surface_display_ready),
        "surface_display_quality_blocked": _bool(surface_display_quality_blocked),
        "two_stage_surface_required": _bool(two_stage_surface_required),
        "two_stage_surface_applied": _bool(two_stage_surface_applied),
        "two_stage_labels_present": _bool(two_stage_labels_present),
        "two_stage_section_order_valid": _bool(two_stage_section_order_valid),
        "observation_section_non_empty": _bool(observation_section_non_empty),
        "reception_section_non_empty": _bool(reception_section_non_empty),
        "two_stage_validation_error_codes": dedupe_identifiers(two_stage_validation_error_codes, limit=80, max_length=160),
        "owner_layer": _owner(owner_layer),
        "reason_codes": dedupe_identifiers(reason_codes, limit=100, max_length=160),
        "validation_error_codes": dedupe_identifiers(validation_error_codes, limit=100, max_length=160),
        "red_refs": dedupe_identifiers(red_refs, limit=40, max_length=120),
        "hold_refs": dedupe_identifiers(hold_refs, limit=40, max_length=120),
        "is_primary_target": _bool(is_primary_target),
        "is_adjacent_red": _bool(is_adjacent_red),
        "body_free": True,
        "public_contract": public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
    }
    assert_p7_hold004_phase16_path_matrix_row_contract(row)
    return row


def assert_p7_hold004_phase16_path_matrix_row_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    if data.get("schema_version") != P7_HOLD004_PHASE16_PATH_MATRIX_ROW_SCHEMA_VERSION:
        raise ValueError("unexpected HOLD-004 Phase16 path matrix row schema_version")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_PHASE16_HOLD_ID:
        raise ValueError("unexpected HOLD-004 Phase16 path matrix row phase/hold")
    if data.get("observed_status") not in _ALLOWED_PATH_STATUSES:
        raise ValueError("unsupported HOLD-004 Phase16 path matrix observed_status")
    if data.get("owner_layer") not in _ALLOWED_OWNER_LAYERS:
        raise ValueError("unsupported HOLD-004 Phase16 path matrix owner_layer")
    if data.get("body_free") is not True:
        raise ValueError("HOLD-004 Phase16 path matrix row must be body-free")
    if P7_HOLD004_PHASE16_HOLD_ID not in dedupe_identifiers(data.get("hold_refs"), limit=40, max_length=120):
        raise ValueError("HOLD-004 Phase16 path matrix row must keep P7-HOLD-004")
    if data.get("labelled_two_stage_reached") is True and data.get("public_reached") is not True and data.get("observed_status") != "generated":
        raise ValueError("labelled two-stage row requires public_reached or generated path")
    assert_false_markers(safe_mapping(data.get("public_contract")), source="p7_hold004_phase16_path_row.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_hold004_phase16_path_row.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_hold004_phase16_path_row")
    return True


def build_p7_hold004_phase16_adjacent_public_fixture_row(
    *,
    test_ref: Any = "tests/test_emotion_submit_two_stage_reception_e2e.py",
    fixture_family: Any = "positive_change_after_work_streaming",
    reason_codes: Sequence[Any] | Any = ("positive_public_fixture_labelled_two_stage_mismatch",),
) -> dict[str, Any]:
    """Build the R2 adjacent public-path red row without merging it into daily_A."""

    return build_p7_hold004_phase16_path_matrix_row(
        path_id=_ADJACENT_PUBLIC_PATH_ID,
        test_ref=test_ref,
        fixture_family=fixture_family,
        observed_status="public_feedback_unlabelled",
        expected_contract_status="public_labelled_two_stage_input_feedback",
        public_reached=True,
        labelled_two_stage_reached=False,
        candidate_generated_before_display_gate=False,
        surface_structural_ready=False,
        surface_display_ready=False,
        surface_display_quality_blocked=True,
        owner_layer="public_recovery_layer",
        reason_codes=reason_codes,
        red_refs=("P7-HOLD-004-ADJACENT-PUBLIC-SHAPE-RED",),
        hold_refs=(P7_HOLD004_PHASE16_HOLD_ID,),
        is_primary_target=False,
        is_adjacent_red=True,
    )


def _rows_from_inputs(
    *,
    observations: Sequence[Mapping[str, Any]],
    extra_rows: Sequence[Mapping[str, Any]],
    include_default_adjacent_public_red: bool,
) -> list[dict[str, Any]]:
    rows = [_row_from_observation(observation) for observation in observations]
    for row in extra_rows:
        assert_p7_hold004_phase16_path_matrix_row_contract(row)
        rows.append(dict(row))
    if include_default_adjacent_public_red and not any(row.get("path_id") == _ADJACENT_PUBLIC_PATH_ID for row in rows):
        rows.append(build_p7_hold004_phase16_adjacent_public_fixture_row())
    return rows


def build_p7_hold004_phase16_path_matrix(
    *,
    observations: Sequence[Mapping[str, Any]],
    extra_rows: Sequence[Mapping[str, Any]] = (),
    include_default_adjacent_public_red: bool = True,
    matrix_id: Any = P7_HOLD004_PHASE16_PATH_MATRIX_ID,
) -> dict[str, Any]:
    """Build R2 path matrix material for the Phase16 Complete Composer red."""

    rows = _rows_from_inputs(
        observations=observations,
        extra_rows=extra_rows,
        include_default_adjacent_public_red=include_default_adjacent_public_red,
    )
    if not rows:
        raise ValueError("HOLD-004 Phase16 path matrix requires at least one row")
    path_ids = [str(row.get("path_id")) for row in rows]
    direct_rows = [row for row in rows if row.get("path_id") == "complete_composer_direct_daily_unpleasant_A"]
    conversation_rows = [row for row in rows if row.get("path_id") == "conversation_composer_daily_unpleasant_A"]
    public_daily_rows = [row for row in rows if row.get("path_id") == "emotion_submit_public_daily_unpleasant_A"]
    adjacent_rows = [row for row in rows if row.get("is_adjacent_red") is True]
    direct_unavailable = any(row.get("observed_status") == "unavailable" for row in direct_rows)
    conversation_unavailable = any(row.get("observed_status") == "unavailable" for row in conversation_rows)
    public_daily_labelled = any(
        row.get("public_reached") is True and row.get("labelled_two_stage_reached") is True for row in public_daily_rows
    )
    adjacent_public_red_registered = any(
        row.get("path_id") == _ADJACENT_PUBLIC_PATH_ID and row.get("is_adjacent_red") is True for row in rows
    )
    matrix = {
        "schema_version": P7_HOLD004_PHASE16_PATH_MATRIX_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_HOLD004_PHASE16_R2_R3_STEP,
        "source_classification_step": P7_HOLD004_PHASE16_STEP,
        "hold_id": P7_HOLD004_PHASE16_HOLD_ID,
        "matrix_id": clean_identifier(matrix_id, default=P7_HOLD004_PHASE16_PATH_MATRIX_ID, max_length=160),
        "rows": rows,
        "path_statuses": {str(row["path_id"]): row["observed_status"] for row in rows},
        "path_count": len(rows),
        "primary_target_path_ids": dedupe_identifiers(_REQUIRED_PRIMARY_PATH_IDS, limit=10, max_length=160),
        "observed_path_ids": dedupe_identifiers(path_ids, limit=40, max_length=160),
        "adjacent_red_path_ids": dedupe_identifiers((row.get("path_id") for row in adjacent_rows), limit=20, max_length=160),
        "direct_unavailable": direct_unavailable,
        "conversation_unavailable": conversation_unavailable,
        "direct_or_conversation_unavailable": direct_unavailable or conversation_unavailable,
        "public_daily_path_labelled": public_daily_labelled,
        "adjacent_public_red_registered": adjacent_public_red_registered,
        "direct_and_conversation_are_separate": bool(direct_rows and conversation_rows and direct_rows[0].get("path_id") != conversation_rows[0].get("path_id")),
        "public_daily_pass_not_merged_with_direct_red": bool(public_daily_labelled and (direct_unavailable or conversation_unavailable)),
        "adjacent_public_red_not_merged_with_daily_A": adjacent_public_red_registered,
        "release_ready_claim_allowed": False,
        "full_backend_suite_green_confirmed": False,
        "full_backend_suite_green_claim_allowed": False,
        "hold004_close_allowed": False,
        "p7_complete_claim_allowed": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "unresolved_hold_refs": [P7_HOLD004_PHASE16_HOLD_ID],
        "required_followup_fixes": dedupe_identifiers(
            [
                "phase16_complete_composer_candidate_boundary" if direct_unavailable or conversation_unavailable else "",
                "positive_public_fixture_shape_boundary" if adjacent_public_red_registered else "",
            ],
            limit=20,
            max_length=160,
        ),
        "body_free": True,
        "public_contract": public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
    }
    assert_p7_hold004_phase16_path_matrix_contract(matrix)
    return matrix


def assert_p7_hold004_phase16_path_matrix_contract(matrix: Mapping[str, Any]) -> bool:
    data = safe_mapping(matrix)
    if data.get("schema_version") != P7_HOLD004_PHASE16_PATH_MATRIX_SCHEMA_VERSION:
        raise ValueError("unexpected HOLD-004 Phase16 path matrix schema_version")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_PHASE16_HOLD_ID:
        raise ValueError("unexpected HOLD-004 Phase16 path matrix phase/hold")
    rows = data.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("HOLD-004 Phase16 path matrix requires rows")
    path_ids: set[str] = set()
    for row in rows:
        row_data = safe_mapping(row)
        assert_p7_hold004_phase16_path_matrix_row_contract(row_data)
        path_ids.add(str(row_data.get("path_id")))
    missing = set(_REQUIRED_PRIMARY_PATH_IDS) - path_ids
    if missing:
        raise ValueError(f"HOLD-004 Phase16 path matrix missing primary paths: {sorted(missing)}")
    if data.get("direct_unavailable") is not True or data.get("conversation_unavailable") is not True:
        raise ValueError("HOLD-004 Phase16 path matrix must preserve direct/conversation unavailable rows")
    if data.get("public_daily_path_labelled") is not True:
        raise ValueError("HOLD-004 Phase16 path matrix must preserve the public daily labelled path")
    if data.get("direct_and_conversation_are_separate") is not True:
        raise ValueError("HOLD-004 Phase16 path matrix must separate direct and conversation paths")
    if data.get("public_daily_pass_not_merged_with_direct_red") is not True:
        raise ValueError("HOLD-004 Phase16 path matrix must not merge public daily pass with direct red")
    for key in (
        "release_ready_claim_allowed",
        "full_backend_suite_green_confirmed",
        "full_backend_suite_green_claim_allowed",
        "hold004_close_allowed",
        "p7_complete_claim_allowed",
        "p8_start_allowed",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"HOLD-004 Phase16 path matrix must keep {key}=False")
    if P7_HOLD004_PHASE16_HOLD_ID not in dedupe_identifiers(data.get("unresolved_hold_refs"), limit=40, max_length=120):
        raise ValueError("HOLD-004 Phase16 path matrix must keep P7-HOLD-004 unresolved")
    if data.get("body_free") is not True:
        raise ValueError("HOLD-004 Phase16 path matrix must be body-free")
    assert_false_markers(safe_mapping(data.get("public_contract")), source="p7_hold004_phase16_path_matrix.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_hold004_phase16_path_matrix.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_hold004_phase16_path_matrix")
    return True


def _reason_or_validation_has_any(row: Mapping[str, Any], markers: Sequence[str]) -> bool:
    codes = [*dedupe_identifiers(row.get("reason_codes"), limit=100), *dedupe_identifiers(row.get("validation_error_codes"), limit=100)]
    return any(any(marker in code for marker in markers) for code in codes)


def _primary_red_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        safe_mapping(row)
        for row in rows
        if row.get("path_id") in {"complete_composer_direct_daily_unpleasant_A", "conversation_composer_daily_unpleasant_A"}
    ]


def _implementation_rule_evaluations(
    *,
    rows: Sequence[Mapping[str, Any]],
    candidate_display_separation_required: bool,
) -> dict[str, bool]:
    primary = _primary_red_rows(rows)
    if not primary:
        return {
            "two_stage_surface_applied": False,
            "labels_present": False,
            "section_validation_clear": False,
            "candidate_shape_material_available": False,
            "display_quality_reason_present": False,
            "candidate_display_separation_required": bool(candidate_display_separation_required),
        }
    return {
        "two_stage_surface_applied": all(row.get("two_stage_surface_applied") is True for row in primary),
        "labels_present": all(row.get("two_stage_labels_present") is True for row in primary),
        "section_validation_clear": all(not row.get("two_stage_validation_error_codes") for row in primary),
        "candidate_shape_material_available": all(
            row.get("observation_section_non_empty") is True and row.get("reception_section_non_empty") is True for row in primary
        ),
        "display_quality_reason_present": any(_reason_or_validation_has_any(row, _DISPLAY_BLOCKER_MARKERS) for row in primary),
        "candidate_display_separation_required": bool(candidate_display_separation_required),
    }


def _structural_failure_rule_matched(rows: Sequence[Mapping[str, Any]]) -> bool:
    primary = _primary_red_rows(rows)
    if not primary:
        return False
    for row in primary:
        structural_red = _reason_or_validation_has_any(row, _STRUCTURAL_ERROR_MARKERS)
        if row.get("two_stage_surface_required") is True and (
            row.get("two_stage_surface_applied") is not True
            or row.get("two_stage_labels_present") is not True
            or row.get("observation_section_non_empty") is not True
            or row.get("reception_section_non_empty") is not True
            or row.get("two_stage_section_order_valid") is not True
            or row.get("surface_structural_ready") is not True
            or structural_red
        ):
            return True
    return False


def build_p7_hold004_phase16_decision_rule(
    *,
    path_matrix: Mapping[str, Any],
    candidate_display_separation_required: bool = True,
    stale_direct_contract_evidence_confirmed: bool = False,
    decision_rule_id: Any = P7_HOLD004_PHASE16_DECISION_RULE_ID,
) -> dict[str, Any]:
    """Build R3 decision rule material before entering R4 repair/replacement."""

    assert_p7_hold004_phase16_path_matrix_contract(path_matrix)
    matrix = safe_mapping(path_matrix)
    rows = [safe_mapping(row) for row in matrix.get("rows", [])]
    implementation_evaluations = _implementation_rule_evaluations(
        rows=rows,
        candidate_display_separation_required=candidate_display_separation_required,
    )
    implementation_rule_matched = all(implementation_evaluations.values())
    structural_failure_rule_matched = _structural_failure_rule_matched(rows)
    stale_contract_rule_matched = (
        bool(stale_direct_contract_evidence_confirmed)
        and matrix.get("public_daily_path_labelled") is True
        and matrix.get("direct_or_conversation_unavailable") is True
        and not bool(candidate_display_separation_required)
    )

    if structural_failure_rule_matched:
        status = "STRUCTURAL_REPAIR_REQUIRED"
        classification = "two_stage_surface_structural_failure"
        decision_kind = "structural_repair_required"
        repair_branch = "R4-structural"
        owner_layers = ["two_stage_surface_structural_boundary", "complete_composer_candidate_boundary"]
    elif stale_contract_rule_matched:
        status = "STALE_CONTRACT_REPLACEMENT_REQUIRED"
        classification = "public_recovery_expected_direct_contract_stale"
        decision_kind = "replace_stale_direct_contract"
        repair_branch = "R4-B"
        owner_layers = ["public_recovery_layer", "stale_contract_expectation"]
    elif implementation_rule_matched:
        status = "IMPLEMENTATION_REPAIR_REQUIRED"
        classification = "candidate_readiness_display_gate_boundary_mixed"
        decision_kind = "repair_candidate_display_boundary"
        repair_branch = "R4-A"
        owner_layers = ["complete_surface_realizer_tone_boundary", "complete_composer_candidate_boundary"]
    else:
        status = "CLASSIFIED_UNRESOLVED"
        classification = "classified_unresolved"
        decision_kind = "classification_only"
        repair_branch = "none"
        owner_layers = ["unknown"]

    rule = {
        "schema_version": P7_HOLD004_PHASE16_DECISION_RULE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_HOLD004_PHASE16_R2_R3_STEP,
        "source_classification_step": P7_HOLD004_PHASE16_STEP,
        "hold_id": P7_HOLD004_PHASE16_HOLD_ID,
        "decision_rule_id": clean_identifier(decision_rule_id, default=P7_HOLD004_PHASE16_DECISION_RULE_ID, max_length=160),
        "path_matrix_schema_version": clean_identifier(
            matrix.get("schema_version"), default=P7_HOLD004_PHASE16_PATH_MATRIX_SCHEMA_VERSION, max_length=128
        ),
        "status": status,
        "classification": classification,
        "owner_layers": dedupe_identifiers(owner_layers, limit=10, max_length=120),
        "decision_rule_fixed": True,
        "decision_kind": decision_kind,
        "repair_branch": repair_branch,
        "implementation_rule_matched": implementation_rule_matched,
        "stale_contract_rule_matched": stale_contract_rule_matched,
        "structural_failure_rule_matched": structural_failure_rule_matched,
        "implementation_rule_evaluations": implementation_evaluations,
        "rule_inputs": {
            "candidate_display_separation_required": bool(candidate_display_separation_required),
            "stale_direct_contract_evidence_confirmed": bool(stale_direct_contract_evidence_confirmed),
            "direct_or_conversation_unavailable": matrix.get("direct_or_conversation_unavailable") is True,
            "public_daily_path_labelled": matrix.get("public_daily_path_labelled") is True,
            "adjacent_public_red_registered": matrix.get("adjacent_public_red_registered") is True,
        },
        "next_branch": repair_branch,
        "required_followup_fixes": dedupe_identifiers(
            [
                "phase16_complete_composer_candidate_boundary" if repair_branch == "R4-A" else "",
                "phase16_direct_contract_replacement" if repair_branch == "R4-B" else "",
                "phase16_two_stage_structural_repair" if repair_branch == "R4-structural" else "",
                *matrix.get("required_followup_fixes", []),
            ],
            limit=40,
            max_length=160,
        ),
        "safety_boundaries": {
            "generated_not_public_display_permission": True,
            "unavailable_not_safe_success": True,
            "display_gate_relaxed": False,
            "grounding_gate_relaxed": False,
            "template_gate_relaxed": False,
            "fixed_sentence_template_added": False,
            "runtime_fixture_branch_added": False,
        },
        "release_ready_claim_allowed": False,
        "full_backend_suite_green_confirmed": False,
        "full_backend_suite_green_claim_allowed": False,
        "hold004_close_allowed": False,
        "p7_complete_claim_allowed": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "unresolved_hold_refs": [P7_HOLD004_PHASE16_HOLD_ID],
        "body_free": True,
        "public_contract": public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
    }
    assert_p7_hold004_phase16_decision_rule_contract(rule)
    return rule


def _adjacent_public_row_from_matrix(path_matrix: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(path_matrix, Mapping):
        return build_p7_hold004_phase16_adjacent_public_fixture_row()
    matrix = safe_mapping(path_matrix)
    rows = matrix.get("rows") or []
    for row in rows:
        row_data = safe_mapping(row)
        if row_data.get("path_id") == _ADJACENT_PUBLIC_PATH_ID and row_data.get("is_adjacent_red") is True:
            assert_p7_hold004_phase16_path_matrix_row_contract(row_data)
            return dict(row_data)
    return build_p7_hold004_phase16_adjacent_public_fixture_row()


def build_p7_hold004_phase16_public_adjacent_red_registration(
    *,
    path_matrix: Mapping[str, Any] | None = None,
    adjacent_row: Mapping[str, Any] | None = None,
    primary_target_paths_repaired: bool = False,
    registration_id: Any = P7_HOLD004_PHASE16_PUBLIC_ADJACENT_RED_REGISTRATION_ID,
) -> dict[str, Any]:
    """Build the R6 body-free registration for the adjacent public-path red.

    R6 intentionally records the positive public fixture shape red as a separate
    next split target.  Even if R4-A made the daily_A direct/conversation paths
    generated again, this material does not close P7-HOLD-004 and does not claim
    full backend suite green.
    """

    row = dict(adjacent_row or _adjacent_public_row_from_matrix(path_matrix))
    assert_p7_hold004_phase16_path_matrix_row_contract(row)
    if row.get("path_id") != _ADJACENT_PUBLIC_PATH_ID or row.get("is_adjacent_red") is not True:
        raise ValueError("R6 adjacent red registration requires the adjacent public fixture row")
    registration = {
        "schema_version": P7_HOLD004_PHASE16_PUBLIC_ADJACENT_RED_REGISTRATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": "P7-HOLD-004_R6_PublicPathAdjacentRedSeparation_20260613",
        "source_path_matrix_schema_version": clean_identifier(
            safe_mapping(path_matrix).get("schema_version") if isinstance(path_matrix, Mapping) else "",
            default=P7_HOLD004_PHASE16_PATH_MATRIX_SCHEMA_VERSION,
            max_length=128,
        ),
        "hold_id": P7_HOLD004_PHASE16_HOLD_ID,
        "registration_id": clean_identifier(
            registration_id, default=P7_HOLD004_PHASE16_PUBLIC_ADJACENT_RED_REGISTRATION_ID, max_length=180
        ),
        "status": "ADJACENT_PUBLIC_RED_REGISTERED_UNRESOLVED",
        "classification": "positive_public_fixture_shape_boundary",
        "primary_target_fixture_family": "daily_unpleasant_encounter_A",
        "primary_target_path_ids": list(_REQUIRED_PRIMARY_PATH_IDS[:2]),
        "primary_target_paths_repaired": bool(primary_target_paths_repaired),
        "primary_target_repair_does_not_close_adjacent_red": True,
        "daily_A_direct_red_not_merged_with_positive_public_red": True,
        "adjacent_public_red_registered": True,
        "adjacent_public_red_path_id": row.get("path_id"),
        "adjacent_public_red_fixture_family": row.get("fixture_family"),
        "adjacent_public_red_observed_status": row.get("observed_status"),
        "adjacent_public_red_expected_contract_status": row.get("expected_contract_status"),
        "adjacent_public_red_test_ref": row.get("test_ref"),
        "adjacent_public_red_reason_codes": dedupe_identifiers(row.get("reason_codes"), limit=40, max_length=160),
        "next_split_target": "positive_public_fixture_shape_boundary",
        "required_followup_fixes": ["positive_public_fixture_shape_boundary"],
        "release_ready_claim_allowed": False,
        "full_backend_suite_green_confirmed": False,
        "full_backend_suite_green_claim_allowed": False,
        "hold004_close_allowed": False,
        "p7_complete_claim_allowed": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "unresolved_hold_refs": [P7_HOLD004_PHASE16_HOLD_ID],
        "body_free": True,
        "public_contract": public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
    }
    assert_p7_hold004_phase16_public_adjacent_red_registration_contract(registration)
    return registration


def assert_p7_hold004_phase16_public_adjacent_red_registration_contract(registration: Mapping[str, Any]) -> bool:
    data = safe_mapping(registration)
    if data.get("schema_version") != P7_HOLD004_PHASE16_PUBLIC_ADJACENT_RED_REGISTRATION_SCHEMA_VERSION:
        raise ValueError("unexpected HOLD-004 Phase16 adjacent red registration schema_version")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_PHASE16_HOLD_ID:
        raise ValueError("unexpected HOLD-004 Phase16 adjacent red registration phase/hold")
    if data.get("status") != "ADJACENT_PUBLIC_RED_REGISTERED_UNRESOLVED":
        raise ValueError("R6 adjacent red registration must remain unresolved")
    if data.get("adjacent_public_red_registered") is not True:
        raise ValueError("R6 adjacent red registration must register the adjacent public red")
    if data.get("daily_A_direct_red_not_merged_with_positive_public_red") is not True:
        raise ValueError("R6 must keep daily_A target and positive public red separate")
    if data.get("primary_target_repair_does_not_close_adjacent_red") is not True:
        raise ValueError("R6 target repair must not close adjacent red")
    if data.get("next_split_target") != "positive_public_fixture_shape_boundary":
        raise ValueError("R6 adjacent red next split target mismatch")
    for key in (
        "release_ready_claim_allowed",
        "full_backend_suite_green_confirmed",
        "full_backend_suite_green_claim_allowed",
        "hold004_close_allowed",
        "p7_complete_claim_allowed",
        "p8_start_allowed",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"R6 adjacent red registration must keep {key}=False")
    if P7_HOLD004_PHASE16_HOLD_ID not in dedupe_identifiers(data.get("unresolved_hold_refs"), limit=40, max_length=120):
        raise ValueError("R6 adjacent red registration must preserve P7-HOLD-004")
    if data.get("body_free") is not True:
        raise ValueError("R6 adjacent red registration must be body-free")
    assert_false_markers(safe_mapping(data.get("public_contract")), source="p7_hold004_phase16_adjacent_red.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_hold004_phase16_adjacent_red.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_hold004_phase16_adjacent_red")
    return True



def build_p7_hold004_phase16_r4b_stale_contract_replacement_design(
    *,
    decision_rule: Mapping[str, Any],
    replacement_design_id: Any = P7_HOLD004_PHASE16_R4B_REPLACEMENT_DESIGN_ID,
) -> dict[str, Any]:
    """Build the R4-B stale-contract replacement design material.

    R4-B is a design branch, not an automatic rewrite.  It may only become
    executable when R3 selected the stale-contract branch with explicit stale
    evidence.  The material keeps unavailable distinct from success and keeps
    the public daily path guard even when a legacy direct ``generated``
    expectation would be replaced.
    """

    assert_p7_hold004_phase16_decision_rule_contract(decision_rule)
    decision = safe_mapping(decision_rule)
    rule_inputs = safe_mapping(decision.get("rule_inputs"))
    selected = decision.get("repair_branch") == "R4-B" and decision.get("decision_kind") == "replace_stale_direct_contract"
    stale_evidence_confirmed = bool(rule_inputs.get("stale_direct_contract_evidence_confirmed"))
    replacement_allowed = bool(selected and stale_evidence_confirmed)
    design = {
        "schema_version": P7_HOLD004_PHASE16_R4B_REPLACEMENT_DESIGN_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": "P7-HOLD-004_R4-B_StaleContractReplacementDesign_20260613",
        "source_decision_rule_schema_version": clean_identifier(
            decision.get("schema_version"), default=P7_HOLD004_PHASE16_DECISION_RULE_SCHEMA_VERSION, max_length=128
        ),
        "hold_id": P7_HOLD004_PHASE16_HOLD_ID,
        "replacement_design_id": clean_identifier(
            replacement_design_id, default=P7_HOLD004_PHASE16_R4B_REPLACEMENT_DESIGN_ID, max_length=180
        ),
        "status": "REPLACEMENT_READY_PENDING_IMPLEMENTATION" if replacement_allowed else "DESIGNED_NOT_APPLIED",
        "r4b_design_available": True,
        "r4b_selected_by_decision_rule": bool(selected),
        "r4a_selected_by_decision_rule": decision.get("repair_branch") == "R4-A",
        "requires_explicit_stale_contract_evidence": True,
        "stale_contract_evidence_confirmed": stale_evidence_confirmed,
        "legacy_direct_generated_expectation_replacement_allowed": replacement_allowed,
        "target_test_replacement_required": replacement_allowed,
        "target_test_rewrite_applied": False,
        "existing_target_test_green_expected_after_r4a": decision.get("repair_branch") == "R4-A",
        "target_test_refs": [
            "tests/test_emlis_ai_complete_composer_two_stage_surface_connection.py",
        ],
        "public_path_guard_test_refs": [
            "tests/test_emotion_submit_two_stage_reception_e2e.py::test_phase16_8_emotion_submit_path_returns_public_two_stage_input_feedback",
        ],
        "replacement_contract_shape": {
            "direct_generated_expectation_replaced": replacement_allowed,
            "direct_path_unavailable_reason_body_free_required": True,
            "two_stage_surface_applied_tone_blocker_public_recovery_separated": True,
            "public_daily_labelled_two_stage_path_required": True,
            "public_path_silence_guard_required": True,
            "generated_not_public_display_permission": True,
            "unavailable_not_safe_success": True,
            "exact_comment_text_assertion_allowed": False,
            "raw_input_assertion_allowed": False,
            "case_id_branch_allowed": False,
        },
        "prohibited_changes": {
            "display_gate_relaxed": False,
            "grounding_gate_relaxed": False,
            "template_gate_relaxed": False,
            "tone_guard_removed": False,
            "fixed_sentence_template_added": False,
            "runtime_fixture_branch_added": False,
            "public_response_key_added": False,
        },
        "release_ready_claim_allowed": False,
        "full_backend_suite_green_confirmed": False,
        "full_backend_suite_green_claim_allowed": False,
        "hold004_close_allowed": False,
        "p7_complete_claim_allowed": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "unresolved_hold_refs": [P7_HOLD004_PHASE16_HOLD_ID],
        "body_free": True,
        "public_contract": public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
    }
    assert_p7_hold004_phase16_r4b_stale_contract_replacement_design_contract(design)
    return design


def assert_p7_hold004_phase16_r4b_stale_contract_replacement_design_contract(design: Mapping[str, Any]) -> bool:
    data = safe_mapping(design)
    if data.get("schema_version") != P7_HOLD004_PHASE16_R4B_REPLACEMENT_DESIGN_SCHEMA_VERSION:
        raise ValueError("unexpected HOLD-004 Phase16 R4-B replacement design schema_version")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_PHASE16_HOLD_ID:
        raise ValueError("unexpected HOLD-004 Phase16 R4-B replacement design phase/hold")
    if data.get("source_decision_rule_schema_version") != P7_HOLD004_PHASE16_DECISION_RULE_SCHEMA_VERSION:
        raise ValueError("R4-B replacement design must reference the R3 decision rule schema")
    if data.get("status") not in {"DESIGNED_NOT_APPLIED", "REPLACEMENT_READY_PENDING_IMPLEMENTATION"}:
        raise ValueError("unsupported HOLD-004 Phase16 R4-B replacement design status")
    if data.get("r4b_design_available") is not True:
        raise ValueError("R4-B replacement design material must be available")
    selected = data.get("r4b_selected_by_decision_rule") is True
    stale_evidence = data.get("stale_contract_evidence_confirmed") is True
    replacement_allowed = data.get("legacy_direct_generated_expectation_replacement_allowed") is True
    if replacement_allowed != bool(selected and stale_evidence):
        raise ValueError("R4-B replacement allowance must require selected branch and stale evidence")
    if data.get("target_test_rewrite_applied") is not False:
        raise ValueError("R4-B design step must not rewrite tests by itself")
    shape = safe_mapping(data.get("replacement_contract_shape"))
    for key in (
        "direct_path_unavailable_reason_body_free_required",
        "two_stage_surface_applied_tone_blocker_public_recovery_separated",
        "public_daily_labelled_two_stage_path_required",
        "public_path_silence_guard_required",
        "generated_not_public_display_permission",
        "unavailable_not_safe_success",
    ):
        if shape.get(key) is not True:
            raise ValueError(f"R4-B replacement design must keep {key}=True")
    for key in ("exact_comment_text_assertion_allowed", "raw_input_assertion_allowed", "case_id_branch_allowed"):
        if shape.get(key) is not False:
            raise ValueError(f"R4-B replacement design must keep {key}=False")
    prohibited = safe_mapping(data.get("prohibited_changes"))
    for key in (
        "display_gate_relaxed",
        "grounding_gate_relaxed",
        "template_gate_relaxed",
        "tone_guard_removed",
        "fixed_sentence_template_added",
        "runtime_fixture_branch_added",
        "public_response_key_added",
    ):
        if prohibited.get(key) is not False:
            raise ValueError(f"R4-B replacement design must keep prohibited change {key}=False")
    for key in (
        "release_ready_claim_allowed",
        "full_backend_suite_green_confirmed",
        "full_backend_suite_green_claim_allowed",
        "hold004_close_allowed",
        "p7_complete_claim_allowed",
        "p8_start_allowed",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"HOLD-004 Phase16 R4-B design must keep {key}=False")
    if P7_HOLD004_PHASE16_HOLD_ID not in dedupe_identifiers(data.get("unresolved_hold_refs"), limit=40, max_length=120):
        raise ValueError("R4-B replacement design must keep P7-HOLD-004 unresolved")
    if data.get("body_free") is not True:
        raise ValueError("R4-B replacement design must be body-free")
    assert_false_markers(safe_mapping(data.get("public_contract")), source="p7_hold004_phase16_r4b_design.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_hold004_phase16_r4b_design.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_hold004_phase16_r4b_design")
    return True


def assert_p7_hold004_phase16_decision_rule_contract(rule: Mapping[str, Any]) -> bool:
    data = safe_mapping(rule)
    if data.get("schema_version") != P7_HOLD004_PHASE16_DECISION_RULE_SCHEMA_VERSION:
        raise ValueError("unexpected HOLD-004 Phase16 decision rule schema_version")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_PHASE16_HOLD_ID:
        raise ValueError("unexpected HOLD-004 Phase16 decision rule phase/hold")
    if data.get("path_matrix_schema_version") != P7_HOLD004_PHASE16_PATH_MATRIX_SCHEMA_VERSION:
        raise ValueError("HOLD-004 Phase16 decision rule must reference the R2 path matrix schema")
    if data.get("status") not in _ALLOWED_DECISION_STATUSES:
        raise ValueError("unsupported HOLD-004 Phase16 decision status")
    if data.get("classification") not in _ALLOWED_CLASSIFICATIONS:
        raise ValueError("unsupported HOLD-004 Phase16 decision classification")
    if data.get("decision_kind") not in _ALLOWED_DECISION_KINDS:
        raise ValueError("unsupported HOLD-004 Phase16 decision kind")
    if data.get("repair_branch") not in _ALLOWED_REPAIR_BRANCHES:
        raise ValueError("unsupported HOLD-004 Phase16 repair branch")
    if data.get("decision_rule_fixed") is not True:
        raise ValueError("HOLD-004 Phase16 decision rule must be fixed before R4")
    if data.get("status") == "IMPLEMENTATION_REPAIR_REQUIRED" and data.get("repair_branch") != "R4-A":
        raise ValueError("implementation repair decision must route to R4-A")
    if data.get("status") == "STALE_CONTRACT_REPLACEMENT_REQUIRED" and data.get("repair_branch") != "R4-B":
        raise ValueError("stale contract decision must route to R4-B")
    if data.get("status") == "STRUCTURAL_REPAIR_REQUIRED" and data.get("repair_branch") != "R4-structural":
        raise ValueError("structural decision must route to R4-structural")
    if data.get("status") == "CLASSIFIED_UNRESOLVED" and data.get("repair_branch") != "none":
        raise ValueError("unresolved classification must not route to a repair branch")
    safety = safe_mapping(data.get("safety_boundaries"))
    if safety.get("generated_not_public_display_permission") is not True:
        raise ValueError("decision rule must keep generated separate from public display permission")
    if safety.get("unavailable_not_safe_success") is not True:
        raise ValueError("decision rule must not treat unavailable as safe success")
    for key in (
        "display_gate_relaxed",
        "grounding_gate_relaxed",
        "template_gate_relaxed",
        "fixed_sentence_template_added",
        "runtime_fixture_branch_added",
    ):
        if safety.get(key) is not False:
            raise ValueError(f"HOLD-004 Phase16 safety boundary must keep {key}=False")
    for key in (
        "release_ready_claim_allowed",
        "full_backend_suite_green_confirmed",
        "full_backend_suite_green_claim_allowed",
        "hold004_close_allowed",
        "p7_complete_claim_allowed",
        "p8_start_allowed",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"HOLD-004 Phase16 decision rule must keep {key}=False")
    if P7_HOLD004_PHASE16_HOLD_ID not in dedupe_identifiers(data.get("unresolved_hold_refs"), limit=40, max_length=120):
        raise ValueError("HOLD-004 Phase16 decision rule must keep P7-HOLD-004 unresolved")
    if data.get("body_free") is not True:
        raise ValueError("HOLD-004 Phase16 decision rule must be body-free")
    assert_false_markers(safe_mapping(data.get("public_contract")), source="p7_hold004_phase16_decision_rule.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_hold004_phase16_decision_rule.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_hold004_phase16_decision_rule")
    return True


__all__ = [
    "P7_HOLD004_PHASE16_DECISION_RULE_ID",
    "P7_HOLD004_PHASE16_DECISION_RULE_SCHEMA_VERSION",
    "P7_HOLD004_PHASE16_PATH_MATRIX_ID",
    "P7_HOLD004_PHASE16_PATH_MATRIX_ROW_SCHEMA_VERSION",
    "P7_HOLD004_PHASE16_PATH_MATRIX_SCHEMA_VERSION",
    "P7_HOLD004_PHASE16_PUBLIC_ADJACENT_RED_REGISTRATION_SCHEMA_VERSION",
    "P7_HOLD004_PHASE16_R2_R3_STEP",
    "P7_HOLD004_PHASE16_R4B_REPLACEMENT_DESIGN_ID",
    "P7_HOLD004_PHASE16_R4B_REPLACEMENT_DESIGN_SCHEMA_VERSION",
    "assert_p7_hold004_phase16_decision_rule_contract",
    "assert_p7_hold004_phase16_path_matrix_contract",
    "assert_p7_hold004_phase16_path_matrix_row_contract",
    "assert_p7_hold004_phase16_public_adjacent_red_registration_contract",
    "assert_p7_hold004_phase16_r4b_stale_contract_replacement_design_contract",
    "build_p7_hold004_phase16_adjacent_public_fixture_row",
    "build_p7_hold004_phase16_decision_rule",
    "build_p7_hold004_phase16_path_matrix",
    "build_p7_hold004_phase16_path_matrix_row",
    "build_p7_hold004_phase16_public_adjacent_red_registration",
    "build_p7_hold004_phase16_r4b_stale_contract_replacement_design",
]
