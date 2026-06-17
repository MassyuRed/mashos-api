# -*- coding: utf-8 -*-
"""P7-8 Release Decision handoff material.

P7-8 turns P7 runner / Long-run Product Gate candidate material into a
body-free handoff for the existing release decision layer.  This module only
prepares input material.  It never performs a release decision, never promotes a
Product Pass candidate to Release Ready, and never mutates public/RN/API/DB
contracts.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Final

from emlis_ai_p7_contracts import (
    P7_INITIAL_HOLD_IDS,
    P7_INITIAL_RED_IDS,
    P7_PHASE,
    assert_false_markers,
    assert_p7_no_body_payload_or_contract_mutation,
    body_free_flags,
    clean_identifier,
    dedupe_identifiers,
    public_contract_flags,
    safe_mapping,
)
from emlis_ai_p7_long_run_gate_handoff import (
    P7_LONG_RUN_GATE_HANDOFF_SCHEMA_VERSION,
    assert_p7_long_run_gate_handoff_contract,
    build_p7_long_run_gate_handoff,
)
from emlis_ai_p7_hold004_positive_public_shape_boundary import (
    P7_HOLD004_POSITIVE_PUBLIC_SHAPE_REPAIRED_STATUS,
    P7_HOLD004_POSITIVE_PUBLIC_SHAPE_SCHEMA_VERSION,
    assert_p7_hold004_positive_public_shape_boundary_contract,
)
from emlis_ai_p7_hold004_step5_candidate_gate_classification import (
    P7_HOLD004_STEP5_R6_MATERIAL_CONNECTION_SCHEMA_VERSION,
    P7_HOLD004_STEP5_RED_ID,
)
from emlis_ai_p7_hold004_backend_suite_execution_results import (
    P7_HOLD004_BACKEND_SUITE_EXECUTION_SUMMARY_SCHEMA_VERSION,
    P7_HOLD004_PREVIOUS_BACKEND_COLLECT_BASELINE_ID,
    P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_SCHEMA_VERSION,
    P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_SCHEMA_VERSION_V2,
    P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_ALLOWED_SCHEMA_VERSIONS,
    P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_BLOCKED_BY_ITEM_FINGERPRINT_MISMATCH,
    P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_READY,
    P7_HOLD004_RECEIVED_SNAPSHOT_ITEM_FINGERPRINT_MISMATCH_BLOCKER_REF,
    assert_p7_hold004_backend_suite_execution_summary_contract,
)
from emlis_ai_p7_hold004_backend_suite_group_inventory_plan import (
    P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_ID,
    P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_ID,
)
from emlis_ai_p7_hold004_backend_suite_split_consistency import P7_HOLD004_BACKEND_COLLECT_BASELINE_ID
from emlis_ai_p7_hold_matrix import (
    P7_BACKEND_SUITE_SPLIT_MATRIX_SCHEMA_VERSION,
    P7_R10_HOLD_MATRIX_SCHEMA_VERSION,
    P7_REAL_DEVICE_MODAL_READFEEL_CHECK_SCHEMA_VERSION,
    assert_p7_backend_suite_split_matrix_contract,
    assert_p7_r10_hold_matrix_contract,
    assert_p7_real_device_modal_readfeel_check_contract,
    build_p7_backend_suite_split_matrix,
    build_p7_r10_hold_matrix,
    build_p7_real_device_modal_readfeel_check,
)
from emlis_ai_p7_red_ledger import P7_RED_LEDGER_SCHEMA_VERSION, assert_p7_red_ledger_contract, build_p7_red_ledger
from emlis_ai_p7_red_closure_classification import (
    P7_RED_CLOSURE_CLASSIFICATION_MATRIX_SCHEMA_VERSION,
    assert_p7_red_closure_classification_matrix_contract,
    build_p7_red_closure_classification_matrix,
    p7_closed_red_refs_from_classification,
    p7_unresolved_red_refs_from_classification,
)
from emlis_ai_p7_timeout_isolation import (
    assert_p7_e2e_isolation_result_contract,
    build_p7_connection_e2e_r13_passed_observation_result,
)
from emlis_ai_p7_runner_plan import P7_RUNNER_PLAN_SCHEMA_VERSION, assert_p7_runner_plan_contract, build_p7_runner_plan
from emlis_ai_product_release_decision import (
    PRODUCT_RELEASE_DECISION_PHASE,
    PRODUCT_RELEASE_DECISION_SCHEMA_VERSION,
    PRODUCT_RELEASE_DECISION_TARGET_STEP,
)

P7_RELEASE_HANDOFF_SCHEMA_VERSION: Final = "cocolon.emlis.p7.release_decision_handoff.v1"
P7_RELEASE_HANDOFF_STEP: Final = "P7-8_ReleaseDecisionHandoffMaterial_20260612"
P7_RELEASE_HANDOFF_SCOPE: Final = "P7_release_decision_handoff_material"
P7_RELEASE_HANDOFF_TARGET_MODULE: Final = "emlis_ai_product_release_decision"
P7_HOLD004_PHASE16_IMPLEMENTATION_RESULT_DOC_PATH: Final = (
    "docs/Cocolon_EmlisAI_P7_HOLD004_Phase16ComposerRedClassification_ImplementationResult_20260613.md"
)
P7_HOLD004_PHASE16_IMPLEMENTATION_RESULT_DOC_REF: Final = "p7_hold004_phase16_composer_result_20260613"
P7_HOLD004_POSITIVE_PUBLIC_SHAPE_IMPLEMENTATION_RESULT_DOC_PATH: Final = (
    "docs/Cocolon_EmlisAI_P7_HOLD004_PositivePublicShapeBoundary_ImplementationResult_20260614.md"
)
P7_HOLD004_POSITIVE_PUBLIC_SHAPE_IMPLEMENTATION_RESULT_DOC_REF: Final = (
    "p7_hold004_positive_public_shape_boundary_result_20260614"
)

_ALLOWED_INPUT_STATUSES: Final[frozenset[str]] = frozenset({"blocked", "review_required", "input_material_ready"})
_TIMEOUT_REF_IDS: Final[frozenset[str]] = frozenset({"P7-RED-003"})


def _as_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "" or isinstance(value, bool):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _listify(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (str, bytes, bytearray)):
        return [value]
    if isinstance(value, Mapping):
        return list(value.values())
    if isinstance(value, Iterable):
        return list(value)
    return [value]


def _refs_from(*sources: Mapping[str, Any], keys: Sequence[str]) -> list[str]:
    refs: list[Any] = []
    for source in sources:
        for key in keys:
            refs.extend(_listify(source.get(key)))
    return dedupe_identifiers(refs, limit=160, max_length=160)


def _source_runner_result_id(runner_result: Mapping[str, Any], long_run: Mapping[str, Any], default: Any) -> str:
    return clean_identifier(
        runner_result.get("runner_result_id")
        or runner_result.get("run_id")
        or long_run.get("material_id")
        or safe_mapping(long_run.get("candidate")).get("candidate_id")
        or default,
        default="p7_runner_result",
        max_length=120,
    )


def _timeout_refs(*, red_refs: Sequence[str], runner_result: Mapping[str, Any], long_run: Mapping[str, Any]) -> list[str]:
    refs: list[Any] = []
    refs.extend(ref for ref in red_refs if clean_identifier(ref) in _TIMEOUT_REF_IDS or "timeout" in clean_identifier(ref).lower())
    refs.extend(_listify(runner_result.get("timeout_refs")))
    refs.extend(_listify(runner_result.get("unresolved_timeout_refs")))
    refs.extend(_listify(long_run.get("timeout_refs")))
    return dedupe_identifiers(refs, limit=40, max_length=120)


def _unreviewed_refs(*, runner_result: Mapping[str, Any], long_run: Mapping[str, Any]) -> list[str]:
    refs: list[Any] = []
    refs.extend(_listify(runner_result.get("unreviewed_refs")))
    refs.extend(_listify(runner_result.get("rating_unreviewed_refs")))
    blind = safe_mapping(long_run.get("blind_qa_summary"))
    if _as_int(blind.get("review_missing_count"), 0) > 0:
        refs.append("blind_qa_review_missing")
    for reason in _listify(long_run.get("candidate_blocked_or_review_required_reason_codes")):
        text = clean_identifier(reason, max_length=120)
        if (
            "review_missing" in text
            or "unreviewed" in text
            or text in {"blind_qa_review_missing", "p5_human_qa_review_required"}
        ):
            refs.append(text)
    return dedupe_identifiers(refs, limit=80, max_length=120)


def _release_input_status(*, input_ready: bool, red_refs: Sequence[str], hold_refs: Sequence[str], timeout_refs: Sequence[str], unreviewed_refs: Sequence[str]) -> str:
    if red_refs or timeout_refs:
        return "blocked"
    if hold_refs or unreviewed_refs or not input_ready:
        return "review_required"
    return "input_material_ready"


def _followup_targets(reason_codes: Sequence[str], red_refs: Sequence[str], hold_refs: Sequence[str]) -> list[str]:
    targets: list[str] = []
    reason_set = {clean_identifier(code, max_length=120) for code in reason_codes}
    if red_refs:
        targets.append("P7_Red_Ledger")
    if hold_refs or {"blind_qa_review_missing", "p5_human_qa_review_required"} & reason_set:
        targets.append("P7_RatingsOnly_Blind_QA")
    if {"p5_history_line_sequence_value_not_increased", "p5_history_line_value_increase_not_observed"} & reason_set:
        targets.append("P5_User_Label_Connection")
    if {"p6_overclaim_risk_detected", "p6_unsafe_claim_risk_detected", "p6_visible_expansion_violation"} & reason_set:
        targets.append("P6_Structure_Insight")
    if {"surface_signature_repetition_detected", "mirror_only_detected", "template_major_detected"} & reason_set:
        targets.append("P7_ProductQualityRunner_LongRunGate")
    if "real_device_submit_modal_readfeel_unverified" in reason_set:
        targets.append("P7_RealDevice_Submit_Modal_Readfeel_Check")
    if "full_backend_suite_green_unconfirmed" in reason_set:
        targets.append("P7_Validation_Regression_Matrix")
    if {"phase16_complete_composer_candidate_boundary", "positive_public_fixture_shape_boundary"} & reason_set:
        targets.append("P7_HOLD004_Phase16_Classification")
    if "positive_public_shape_target_green_pending_full_suite" in reason_set:
        targets.append("P7_HOLD004_PositivePublicShapeBoundary")
    if "step5_display_binding_contract_consistency" in reason_set:
        targets.append("P7_HOLD004_Step5CandidateGatePreservation")
    return dedupe_identifiers(targets, limit=20, max_length=140)


def _ledger_refs_by_status(ledger: Mapping[str, Any], status: str) -> list[str]:
    refs: list[Any] = []
    wanted = clean_identifier(status, max_length=40)
    for raw_entry in _listify(ledger.get("entries")):
        entry = safe_mapping(raw_entry)
        if clean_identifier(entry.get("status"), max_length=40) == wanted:
            refs.append(entry.get("id"))
    return dedupe_identifiers(refs, limit=80, max_length=120)



def build_p7_release_decision_handoff(
    long_run_gate_handoff: Mapping[str, Any] | None = None,
    *,
    p7_runner_result: Mapping[str, Any] | None = None,
    runner_plan: Mapping[str, Any] | None = None,
    red_ledger: Mapping[str, Any] | None = None,
    red_closure_classification: Mapping[str, Any] | None = None,
    red_closure_classification_matrix: Mapping[str, Any] | None = None,
    connection_timeout_isolation_result: Mapping[str, Any] | None = None,
    real_device_check: Mapping[str, Any] | None = None,
    backend_suite_execution_summary: Mapping[str, Any] | None = None,
    backend_suite_split_matrix: Mapping[str, Any] | None = None,
    r10_hold_matrix: Mapping[str, Any] | None = None,
    hold004_phase16_classification: Mapping[str, Any] | None = None,
    hold004_path_matrix: Mapping[str, Any] | None = None,
    hold004_decision_rule: Mapping[str, Any] | None = None,
    hold004_adjacent_public_red_registration: Mapping[str, Any] | None = None,
    hold004_positive_public_shape_boundary: Mapping[str, Any] | None = None,
    hold004_step5_material_connection: Mapping[str, Any] | None = None,
    source_runner_result_id: Any = "p7_runner_result",
) -> dict[str, Any]:
    """Build P7 body-free material for the release decision layer.

    ``release_decision_input_ready`` means only that the body-free material can be
    handed to the release-decision module.  It is deliberately separate from
    ``release_allowed``, which remains false in every P7 handoff.
    """

    runner = safe_mapping(p7_runner_result)
    if p7_runner_result is not None:
        assert_p7_no_body_payload_or_contract_mutation(runner, source="p7_release_handoff.runner_result")

    long_run = safe_mapping(long_run_gate_handoff) if long_run_gate_handoff is not None else build_p7_long_run_gate_handoff()
    assert_p7_long_run_gate_handoff_contract(long_run)
    assert_p7_no_body_payload_or_contract_mutation(long_run, source="p7_release_handoff.long_run_gate_handoff")

    plan = safe_mapping(runner_plan) if runner_plan is not None else build_p7_runner_plan()
    assert_p7_runner_plan_contract(plan)
    assert_p7_no_body_payload_or_contract_mutation(plan, source="p7_release_handoff.runner_plan")

    ledger = safe_mapping(red_ledger) if red_ledger is not None else build_p7_red_ledger()
    assert_p7_red_ledger_contract(ledger)
    assert_p7_no_body_payload_or_contract_mutation(ledger, source="p7_release_handoff.red_ledger")

    connection_isolation = safe_mapping(connection_timeout_isolation_result)
    if connection_timeout_isolation_result is not None:
        assert_p7_e2e_isolation_result_contract(connection_isolation)
        assert_p7_no_body_payload_or_contract_mutation(
            connection_isolation,
            source="p7_release_handoff.connection_timeout_isolation_result",
        )

    backend_execution_summary = safe_mapping(backend_suite_execution_summary)
    if backend_suite_execution_summary is not None:
        assert_p7_hold004_backend_suite_execution_summary_contract(backend_execution_summary)
        assert_p7_no_body_payload_or_contract_mutation(
            backend_execution_summary,
            source="p7_release_handoff.backend_suite_execution_summary",
        )

    classification_source = red_closure_classification_matrix or red_closure_classification
    classification = (
        safe_mapping(classification_source)
        if classification_source is not None
        else build_p7_red_closure_classification_matrix(
            connection_timeout_isolation_result=connection_isolation
            if connection_timeout_isolation_result is not None
            else build_p7_connection_e2e_r13_passed_observation_result()
        )
    )
    assert_p7_red_closure_classification_matrix_contract(classification)
    assert_p7_no_body_payload_or_contract_mutation(classification, source="p7_release_handoff.red_closure_classification")
    closed_red_refs = p7_closed_red_refs_from_classification(classification)
    classification_unresolved_red_refs = p7_unresolved_red_refs_from_classification(classification)

    real_device = safe_mapping(real_device_check) if real_device_check is not None else build_p7_real_device_modal_readfeel_check()
    assert_p7_real_device_modal_readfeel_check_contract(real_device)
    assert_p7_no_body_payload_or_contract_mutation(real_device, source="p7_release_handoff.real_device_check")

    positive_public_shape = safe_mapping(hold004_positive_public_shape_boundary)
    if hold004_positive_public_shape_boundary is not None:
        assert_p7_hold004_positive_public_shape_boundary_contract(positive_public_shape)
        assert_p7_no_body_payload_or_contract_mutation(
            positive_public_shape,
            source="p7_release_handoff.positive_public_shape",
        )

    backend_split = (
        safe_mapping(backend_suite_split_matrix)
        if backend_suite_split_matrix is not None
        else build_p7_backend_suite_split_matrix(
            real_device_check=real_device,
            positive_recovery_red_closed=True,
            backend_suite_execution_summary=backend_execution_summary or None,
            red_closure_classification_matrix=classification,
            connection_timeout_isolation_result=connection_isolation or None,
            hold004_phase16_classification=hold004_phase16_classification,
            hold004_path_matrix=hold004_path_matrix,
            hold004_decision_rule=hold004_decision_rule,
            hold004_adjacent_public_red_registration=hold004_adjacent_public_red_registration,
            hold004_positive_public_shape_boundary=positive_public_shape or None,
            hold004_step5_material_connection=hold004_step5_material_connection,
        )
    )
    assert_p7_backend_suite_split_matrix_contract(backend_split)
    assert_p7_no_body_payload_or_contract_mutation(backend_split, source="p7_release_handoff.backend_suite_split_matrix")

    r10_matrix = (
        safe_mapping(r10_hold_matrix)
        if r10_hold_matrix is not None
        else build_p7_r10_hold_matrix(
            real_device_check=real_device,
            backend_suite_split_matrix=backend_split,
            backend_suite_execution_summary=backend_execution_summary or None,
            red_closure_classification_matrix=classification,
            connection_timeout_isolation_result=connection_isolation or None,
            hold004_phase16_classification=hold004_phase16_classification,
            hold004_path_matrix=hold004_path_matrix,
            hold004_decision_rule=hold004_decision_rule,
            hold004_adjacent_public_red_registration=hold004_adjacent_public_red_registration,
            hold004_positive_public_shape_boundary=positive_public_shape or None,
            hold004_step5_material_connection=hold004_step5_material_connection,
        )
    )
    assert_p7_r10_hold_matrix_contract(r10_matrix)
    assert_p7_no_body_payload_or_contract_mutation(r10_matrix, source="p7_release_handoff.r10_hold_matrix")

    hold004_required_followup_fixes = dedupe_identifiers(
        [
            *backend_split.get("hold004_required_followup_fixes", []),
            *r10_matrix.get("hold004_required_followup_fixes", []),
        ],
        limit=120,
        max_length=160,
    )
    hold004_phase16_classified_red_present = bool(
        backend_split.get("hold004_phase16_classified_red_present") is True
        or r10_matrix.get("hold004_phase16_classified_red_present") is True
    )
    hold004_candidate_boundary_registered = bool(
        backend_split.get("hold004_phase16_candidate_boundary_registered") is True
        or r10_matrix.get("hold004_phase16_candidate_boundary_registered") is True
        or "phase16_complete_composer_candidate_boundary" in hold004_required_followup_fixes
    )
    hold004_adjacent_public_red_registered = bool(
        backend_split.get("hold004_public_adjacent_red_registered") is True
        or r10_matrix.get("hold004_public_adjacent_red_registered") is True
        or "positive_public_fixture_shape_boundary" in hold004_required_followup_fixes
    )
    positive_shape_schema_version = clean_identifier(
        backend_split.get("hold004_positive_public_shape_boundary_schema_version")
        or r10_matrix.get("hold004_positive_public_shape_boundary_schema_version"),
        default="",
        max_length=160,
    )
    positive_shape_status = clean_identifier(
        backend_split.get("hold004_positive_public_shape_boundary_status")
        or r10_matrix.get("hold004_positive_public_shape_boundary_status"),
        default="",
        max_length=120,
    )
    positive_shape_target_green = bool(
        backend_split.get("hold004_positive_public_shape_target_green_confirmed") is True
        or r10_matrix.get("hold004_positive_public_shape_target_green_confirmed") is True
    )
    positive_shape_repaired_pending_full_suite = bool(
        backend_split.get("hold004_positive_public_shape_repaired_target_green_pending_full_suite") is True
        or r10_matrix.get("hold004_positive_public_shape_repaired_target_green_pending_full_suite") is True
    )
    positive_shape_true_self_denial_preserved = bool(
        backend_split.get("hold004_positive_public_shape_true_self_denial_regression_preserved") is True
        or r10_matrix.get("hold004_positive_public_shape_true_self_denial_regression_preserved") is True
    )
    positive_shape_emergency_preserved = bool(
        backend_split.get("hold004_positive_public_shape_emergency_regression_preserved") is True
        or r10_matrix.get("hold004_positive_public_shape_emergency_regression_preserved") is True
    )
    positive_shape_support_required_preserved = bool(
        backend_split.get("hold004_positive_public_shape_support_required_regression_preserved") is True
        or r10_matrix.get("hold004_positive_public_shape_support_required_regression_preserved") is True
    )
    positive_shape_input_material_confirmed = bool(
        backend_split.get("hold004_positive_public_shape_input_material_bundle_confirmed") is True
        or r10_matrix.get("hold004_positive_public_shape_input_material_bundle_confirmed") is True
    )
    positive_shape_public_e2e_confirmed = bool(
        backend_split.get("hold004_positive_public_shape_public_e2e_labelled_two_stage_confirmed") is True
        or r10_matrix.get("hold004_positive_public_shape_public_e2e_labelled_two_stage_confirmed") is True
    )
    step5_schema_version = clean_identifier(
        backend_split.get("hold004_step5_material_connection_schema_version")
        or r10_matrix.get("hold004_step5_material_connection_schema_version"),
        default="",
        max_length=160,
    )
    step5_status = clean_identifier(
        backend_split.get("hold004_step5_material_connection_status")
        or r10_matrix.get("hold004_step5_material_connection_status"),
        default="",
        max_length=120,
    )
    step5_red_classified = bool(
        backend_split.get("hold004_step5_candidate_gate_red_classified") is True
        or r10_matrix.get("hold004_step5_candidate_gate_red_classified") is True
    )
    step5_red_present = bool(
        backend_split.get("hold004_step5_display_binding_red_present") is True
        or r10_matrix.get("hold004_step5_display_binding_red_present") is True
    )
    step5_red_closed = bool(
        backend_split.get("hold004_step5_candidate_gate_red_closed") is True
        or r10_matrix.get("hold004_step5_candidate_gate_red_closed") is True
    )
    step5_contract_classification = clean_identifier(
        backend_split.get("hold004_step5_contract_classification")
        or r10_matrix.get("hold004_step5_contract_classification"),
        default="",
        max_length=160,
    )
    step5_required_followup_fixes = dedupe_identifiers(
        [
            *backend_split.get("hold004_step5_required_followup_fixes", []),
            *r10_matrix.get("hold004_step5_required_followup_fixes", []),
        ],
        limit=120,
        max_length=160,
    )
    step5_unresolved_red_refs = dedupe_identifiers(
        [
            *backend_split.get("hold004_step5_unresolved_red_refs", []),
            *r10_matrix.get("hold004_step5_unresolved_red_refs", []),
        ],
        limit=40,
        max_length=160,
    )
    step5_closed_red_refs = dedupe_identifiers(
        [
            *backend_split.get("hold004_step5_closed_red_refs", []),
            *r10_matrix.get("hold004_step5_closed_red_refs", []),
        ],
        limit=40,
        max_length=160,
    )
    backend_execution_summary_connected = bool(
        backend_split.get("backend_suite_execution_summary_connected") is True
        or r10_matrix.get("backend_suite_execution_summary_connected") is True
        or backend_execution_summary
    )
    backend_execution_summary_schema_version = clean_identifier(
        backend_split.get("backend_suite_execution_summary_schema_version")
        or r10_matrix.get("backend_suite_execution_summary_schema_version")
        or backend_execution_summary.get("schema_version"),
        default="",
        max_length=160,
    )
    backend_execution_summary_id = clean_identifier(
        backend_split.get("backend_suite_execution_summary_id")
        or r10_matrix.get("backend_suite_execution_summary_id")
        or backend_execution_summary.get("summary_id"),
        default="",
        max_length=160,
    )
    backend_execution_summary_collect_baseline_id = clean_identifier(
        backend_split.get("backend_suite_execution_summary_collect_baseline_id")
        or r10_matrix.get("backend_suite_execution_summary_collect_baseline_id")
        or backend_execution_summary.get("collect_baseline_id"),
        default="",
        max_length=160,
    )
    backend_execution_summary_inventory_id = clean_identifier(
        backend_split.get("backend_suite_execution_summary_inventory_id")
        or r10_matrix.get("backend_suite_execution_summary_inventory_id")
        or backend_execution_summary.get("inventory_id"),
        default="",
        max_length=160,
    )
    backend_execution_summary_plan_id = clean_identifier(
        backend_split.get("backend_suite_execution_summary_plan_id")
        or r10_matrix.get("backend_suite_execution_summary_plan_id")
        or backend_execution_summary.get("plan_id"),
        default="",
        max_length=160,
    )
    current_collect_baseline_connected = bool(
        backend_execution_summary_connected
        and backend_execution_summary_collect_baseline_id == P7_HOLD004_BACKEND_COLLECT_BASELINE_ID
        and backend_split.get("current_collect_baseline_connected") is True
        and r10_matrix.get("current_collect_baseline_connected") is True
    )
    current_group_inventory_connected = bool(
        backend_execution_summary_connected
        and backend_execution_summary_inventory_id == P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_ID
        and backend_split.get("current_group_inventory_connected") is True
        and r10_matrix.get("current_group_inventory_connected") is True
    )
    current_execution_plan_connected = bool(
        backend_execution_summary_connected
        and backend_execution_summary_plan_id == P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_ID
        and backend_split.get("current_execution_plan_connected") is True
        and r10_matrix.get("current_execution_plan_connected") is True
    )
    old_baseline_not_used_as_current = bool(
        backend_execution_summary_connected
        and backend_execution_summary_collect_baseline_id != P7_HOLD004_PREVIOUS_BACKEND_COLLECT_BASELINE_ID
        and backend_split.get("old_baseline_not_used_as_current") is True
        and r10_matrix.get("old_baseline_not_used_as_current") is True
    )
    backend_suite_group_02_count_current = bool(
        backend_execution_summary_connected
        and backend_split.get("backend_suite_group_02_count_current") is True
        and r10_matrix.get("backend_suite_group_02_count_current") is True
    )
    matrix_current_baseline_connection = safe_mapping(
        backend_split.get("matrix_current_baseline_connection")
        or r10_matrix.get("matrix_current_baseline_connection")
    )
    backend_execution_summary_all_groups_executed = bool(
        backend_split.get("backend_suite_execution_summary_all_groups_executed") is True
        or r10_matrix.get("backend_suite_execution_summary_all_groups_executed") is True
        or backend_execution_summary.get("all_groups_executed") is True
    )
    backend_execution_summary_group_run_results_recorded = bool(
        backend_split.get("backend_suite_execution_summary_group_run_results_recorded") is True
        or r10_matrix.get("backend_suite_execution_summary_group_run_results_recorded") is True
        or backend_execution_summary.get("group_run_results_recorded") is True
    )
    backend_execution_summary_split_all_groups_green_confirmed = bool(
        backend_split.get("backend_suite_execution_summary_split_all_groups_green_confirmed") is True
        or r10_matrix.get("backend_suite_execution_summary_split_all_groups_green_confirmed") is True
        or backend_execution_summary.get("split_all_groups_green_confirmed") is True
    )
    backend_execution_summary_failed_group_ids = dedupe_identifiers(
        [
            *backend_split.get("backend_suite_execution_summary_failed_group_ids", []),
            *r10_matrix.get("backend_suite_execution_summary_failed_group_ids", []),
            *backend_execution_summary.get("failed_group_ids", []),
        ],
        limit=40,
        max_length=120,
    )
    backend_execution_summary_timeout_group_ids = dedupe_identifiers(
        [
            *backend_split.get("backend_suite_execution_summary_timeout_group_ids", []),
            *r10_matrix.get("backend_suite_execution_summary_timeout_group_ids", []),
            *backend_execution_summary.get("timeout_group_ids", []),
        ],
        limit=40,
        max_length=120,
    )
    backend_execution_summary_not_run_group_ids = dedupe_identifiers(
        [
            *backend_split.get("backend_suite_execution_summary_not_run_group_ids", []),
            *r10_matrix.get("backend_suite_execution_summary_not_run_group_ids", []),
            *backend_execution_summary.get("not_run_group_ids", []),
        ],
        limit=40,
        max_length=120,
    )
    backend_execution_summary_partial_group_ids = dedupe_identifiers(
        [
            *backend_split.get("backend_suite_execution_summary_partial_group_ids", []),
            *r10_matrix.get("backend_suite_execution_summary_partial_group_ids", []),
            *backend_execution_summary.get("partial_group_ids", []),
        ],
        limit=40,
        max_length=120,
    )
    official_group_02_capture_readiness_schema_version = clean_identifier(
        backend_split.get("official_group_02_capture_readiness_schema_version")
        or r10_matrix.get("official_group_02_capture_readiness_schema_version"),
        default="",
        max_length=160,
    )
    official_group_02_capture_readiness_status = clean_identifier(
        backend_split.get("official_group_02_capture_readiness_status")
        or r10_matrix.get("official_group_02_capture_readiness_status"),
        default="",
        max_length=160,
    )
    official_group_02_capture_blocked = bool(
        backend_split.get("official_group_02_capture_blocked") is True
        or r10_matrix.get("official_group_02_capture_blocked") is True
    )
    official_group_02_capture_run_allowed = bool(
        backend_split.get("official_group_02_capture_run_allowed") is True
        or r10_matrix.get("official_group_02_capture_run_allowed") is True
    )
    official_group_02_capture_result_recording_allowed = bool(
        backend_split.get("official_group_02_capture_result_recording_allowed") is True
        or r10_matrix.get("official_group_02_capture_result_recording_allowed") is True
    )
    received_snapshot_item_fingerprint_mismatch_unresolved = bool(
        backend_split.get("received_snapshot_item_fingerprint_mismatch_unresolved") is True
        or r10_matrix.get("received_snapshot_item_fingerprint_mismatch_unresolved") is True
    )
    received_snapshot_baseline_fingerprint_reconciled = bool(
        backend_split.get("received_snapshot_baseline_fingerprint_reconciled") is True
        or r10_matrix.get("received_snapshot_baseline_fingerprint_reconciled") is True
    )
    received_snapshot_blocker_refs = dedupe_identifiers(
        [
            *backend_split.get("received_snapshot_blocker_refs", []),
            *r10_matrix.get("received_snapshot_blocker_refs", []),
        ],
        limit=80,
        max_length=180,
    )
    received_snapshot_required_followup_fixes = dedupe_identifiers(
        [
            *backend_split.get("received_snapshot_required_followup_fixes", []),
            *r10_matrix.get("received_snapshot_required_followup_fixes", []),
            P7_HOLD004_RECEIVED_SNAPSHOT_ITEM_FINGERPRINT_MISMATCH_BLOCKER_REF
            if received_snapshot_item_fingerprint_mismatch_unresolved
            else "",
        ],
        limit=120,
        max_length=180,
    )
    active_baseline_refresh_schema_version = clean_identifier(
        backend_split.get("active_baseline_refresh_schema_version")
        or r10_matrix.get("active_baseline_refresh_schema_version"),
        default="",
        max_length=160,
    )
    active_baseline_refresh_id = clean_identifier(
        backend_split.get("active_baseline_refresh_id") or r10_matrix.get("active_baseline_refresh_id"),
        default="",
        max_length=180,
    )
    runtime_builder_refresh_status_id = clean_identifier(
        backend_split.get("runtime_builder_refresh_status_id")
        or r10_matrix.get("runtime_builder_refresh_status_id"),
        default="",
        max_length=180,
    )
    post_adoption_received_snapshot_reconcile_id = clean_identifier(
        backend_split.get("post_adoption_received_snapshot_reconcile_id")
        or r10_matrix.get("post_adoption_received_snapshot_reconcile_id"),
        default="",
        max_length=180,
    )
    active_baseline_update_applied_to_runtime_builders = bool(
        backend_split.get("active_baseline_update_applied_to_runtime_builders") is True
        or r10_matrix.get("active_baseline_update_applied_to_runtime_builders") is True
    )
    source_snapshot_ref_updated_in_active_builders = bool(
        backend_split.get("source_snapshot_ref_updated_in_active_builders") is True
        or r10_matrix.get("source_snapshot_ref_updated_in_active_builders") is True
    )
    post_adoption_readiness_re_evaluated = bool(
        backend_split.get("post_adoption_readiness_re_evaluated") is True
        or r10_matrix.get("post_adoption_readiness_re_evaluated") is True
    )
    hold004_implementation_result_doc_refs = dedupe_identifiers(
        [
            P7_HOLD004_PHASE16_IMPLEMENTATION_RESULT_DOC_PATH
            if hold004_phase16_classified_red_present
            else "",
            P7_HOLD004_POSITIVE_PUBLIC_SHAPE_IMPLEMENTATION_RESULT_DOC_PATH
            if positive_shape_schema_version
            else "",
        ],
        limit=40,
        max_length=220,
    )
    positive_shape_implementation_result_documented = bool(positive_shape_schema_version)
    positive_shape_implementation_result_doc_ref = (
        P7_HOLD004_POSITIVE_PUBLIC_SHAPE_IMPLEMENTATION_RESULT_DOC_REF
        if positive_shape_implementation_result_documented
        else ""
    )

    red_refs = dedupe_identifiers(
        [*_refs_from(runner, long_run, keys=("unresolved_red_refs", "red_refs")), *_ledger_refs_by_status(ledger, "RED")],
        limit=160,
        max_length=160,
    )
    if closed_red_refs:
        closed_set = set(closed_red_refs)
        red_refs = dedupe_identifiers([ref for ref in red_refs if ref not in closed_set], limit=160, max_length=160)
    if classification_unresolved_red_refs:
        red_refs = dedupe_identifiers([*classification_unresolved_red_refs, *red_refs], limit=160, max_length=160)
    if step5_unresolved_red_refs:
        red_refs = dedupe_identifiers([*step5_unresolved_red_refs, *red_refs], limit=160, max_length=160)
    hold_refs = dedupe_identifiers(
        [
            *_refs_from(runner, long_run, keys=("unresolved_hold_refs", "hold_refs")),
            *_ledger_refs_by_status(ledger, "HOLD"),
            *real_device.get("hold_refs", []),
            *backend_split.get("unresolved_hold_refs", []),
            *r10_matrix.get("unresolved_hold_refs", []),
        ],
        limit=160,
        max_length=160,
    )
    if long_run_gate_handoff is None and not runner:
        initial_red_refs = [ref for ref in P7_INITIAL_RED_IDS if ref not in set(closed_red_refs)]
        red_refs = dedupe_identifiers([*initial_red_refs, *red_refs], limit=80, max_length=120)
        hold_refs = dedupe_identifiers([*P7_INITIAL_HOLD_IDS, *hold_refs], limit=80, max_length=120)
    timeout_refs = _timeout_refs(red_refs=red_refs, runner_result=runner, long_run=long_run)
    if closed_red_refs:
        closed_set = set(closed_red_refs)
        timeout_refs = dedupe_identifiers([ref for ref in timeout_refs if ref not in closed_set], limit=40, max_length=120)
    unreviewed_refs = _unreviewed_refs(runner_result=runner, long_run=long_run)
    required_fixes = dedupe_identifiers(
        [
            *_listify(long_run.get("candidate_blocked_or_review_required_reason_codes")),
            *_listify(long_run.get("required_followup_fixes")),
            *_listify(runner.get("required_followup_fixes")),
            *_listify(runner.get("candidate_blocked_or_review_required_reason_codes")),
            *hold004_required_followup_fixes,
            *step5_required_followup_fixes,
            *backend_execution_summary.get("required_followup_fixes", []),
            *received_snapshot_required_followup_fixes,
            "official_group_02_capture_blocked" if official_group_02_capture_blocked else "",
            "positive_public_shape_target_green_pending_full_suite" if positive_shape_target_green else "",
            "split_green_is_not_full_backend_suite_green" if backend_execution_summary_split_all_groups_green_confirmed else "",
            "un_split_full_backend_suite_green_not_confirmed" if backend_execution_summary_split_all_groups_green_confirmed else "",
        ],
        limit=160,
        max_length=160,
    )
    if real_device.get("real_device_submit_confirmed") is not True:
        required_fixes.append("real_device_submit_modal_readfeel_unverified")
    if runner.get("full_backend_suite_green_confirmed") is not True or backend_split.get("full_backend_suite_green_confirmed") is not True:
        required_fixes.append("full_backend_suite_green_unconfirmed")
    required_fixes = dedupe_identifiers(required_fixes, limit=160, max_length=160)

    long_run_input_ready = bool(long_run.get("release_decision_input_ready") is True and long_run.get("long_run_candidate_ready") is True)
    explicit_runner_ready = runner.get("release_decision_input_ready")
    source_input_ready = bool(long_run_input_ready and (explicit_runner_ready is not False))
    blockers = dedupe_identifiers([*red_refs, *hold_refs, *timeout_refs, *unreviewed_refs, *required_fixes], limit=240, max_length=160)
    input_ready = bool(source_input_ready and not blockers)
    input_status = _release_input_status(
        input_ready=input_ready,
        red_refs=red_refs,
        hold_refs=hold_refs,
        timeout_refs=timeout_refs,
        unreviewed_refs=unreviewed_refs,
    )

    candidate = safe_mapping(long_run.get("candidate"))
    sequence_coverage = safe_mapping(long_run.get("sequence_coverage"))
    risk_metrics = safe_mapping(long_run.get("risk_metrics"))
    blind_summary = safe_mapping(long_run.get("blind_qa_summary"))

    handoff = {
        "schema_version": P7_RELEASE_HANDOFF_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_RELEASE_HANDOFF_STEP,
        "scope": P7_RELEASE_HANDOFF_SCOPE,
        "source_runner_result_id": _source_runner_result_id(runner, long_run, source_runner_result_id),
        "source_runner_plan_schema_version": clean_identifier(plan.get("schema_version"), default=P7_RUNNER_PLAN_SCHEMA_VERSION, max_length=128),
        "source_red_ledger_schema_version": clean_identifier(ledger.get("schema_version"), default=P7_RED_LEDGER_SCHEMA_VERSION, max_length=128),
        "red_closure_classification_schema_version": (
            clean_identifier(classification.get("schema_version"), default="", max_length=128) if classification else ""
        ),
        "r10_hold_matrix_schema_version": clean_identifier(r10_matrix.get("schema_version"), default=P7_R10_HOLD_MATRIX_SCHEMA_VERSION, max_length=128),
        "real_device_check_schema_version": clean_identifier(
            real_device.get("schema_version"), default=P7_REAL_DEVICE_MODAL_READFEEL_CHECK_SCHEMA_VERSION, max_length=128
        ),
        "backend_suite_split_matrix_schema_version": clean_identifier(
            backend_split.get("schema_version"), default=P7_BACKEND_SUITE_SPLIT_MATRIX_SCHEMA_VERSION, max_length=128
        ),
        "backend_suite_execution_summary_connected": backend_execution_summary_connected,
        "backend_suite_execution_summary_schema_version": backend_execution_summary_schema_version,
        "backend_suite_execution_summary_id": backend_execution_summary_id,
        "backend_suite_execution_summary_collect_baseline_id": backend_execution_summary_collect_baseline_id,
        "backend_suite_execution_summary_inventory_id": backend_execution_summary_inventory_id,
        "backend_suite_execution_summary_plan_id": backend_execution_summary_plan_id,
        "current_collect_baseline_connected": current_collect_baseline_connected,
        "current_group_inventory_connected": current_group_inventory_connected,
        "current_execution_plan_connected": current_execution_plan_connected,
        "old_baseline_not_used_as_current": old_baseline_not_used_as_current,
        "backend_suite_group_02_count_current": backend_suite_group_02_count_current,
        "matrix_current_baseline_connection": matrix_current_baseline_connection,
        "backend_suite_execution_summary_all_groups_executed": backend_execution_summary_all_groups_executed,
        "backend_suite_execution_summary_group_run_results_recorded": backend_execution_summary_group_run_results_recorded,
        "backend_suite_execution_summary_split_all_groups_green_confirmed": (
            backend_execution_summary_split_all_groups_green_confirmed
        ),
        "backend_suite_execution_summary_failed_group_ids": backend_execution_summary_failed_group_ids,
        "backend_suite_execution_summary_timeout_group_ids": backend_execution_summary_timeout_group_ids,
        "backend_suite_execution_summary_not_run_group_ids": backend_execution_summary_not_run_group_ids,
        "backend_suite_execution_summary_partial_group_ids": backend_execution_summary_partial_group_ids,
        "official_group_02_capture_readiness_schema_version": official_group_02_capture_readiness_schema_version,
        "official_group_02_capture_readiness_status": official_group_02_capture_readiness_status,
        "official_group_02_capture_blocked": official_group_02_capture_blocked,
        "official_group_02_capture_run_allowed": official_group_02_capture_run_allowed,
        "official_group_02_capture_result_recording_allowed": official_group_02_capture_result_recording_allowed,
        "received_snapshot_baseline_fingerprint_reconciled": received_snapshot_baseline_fingerprint_reconciled,
        "received_snapshot_item_fingerprint_mismatch_unresolved": received_snapshot_item_fingerprint_mismatch_unresolved,
        "received_snapshot_blocker_refs": received_snapshot_blocker_refs,
        "received_snapshot_required_followup_fixes": received_snapshot_required_followup_fixes,
        "active_baseline_refresh_schema_version": active_baseline_refresh_schema_version,
        "active_baseline_refresh_id": active_baseline_refresh_id,
        "runtime_builder_refresh_status_id": runtime_builder_refresh_status_id,
        "post_adoption_received_snapshot_reconcile_id": post_adoption_received_snapshot_reconcile_id,
        "active_baseline_update_applied_to_runtime_builders": active_baseline_update_applied_to_runtime_builders,
        "source_snapshot_ref_updated_in_active_builders": source_snapshot_ref_updated_in_active_builders,
        "post_adoption_readiness_re_evaluated": post_adoption_readiness_re_evaluated,
        "source_long_run_gate_handoff_schema_version": clean_identifier(
            long_run.get("schema_version"), default=P7_LONG_RUN_GATE_HANDOFF_SCHEMA_VERSION, max_length=128
        ),
        "hold004_phase16_implementation_result_doc_path": P7_HOLD004_PHASE16_IMPLEMENTATION_RESULT_DOC_PATH,
        "hold004_phase16_implementation_result_doc_ref": P7_HOLD004_PHASE16_IMPLEMENTATION_RESULT_DOC_REF,
        "hold004_positive_public_shape_implementation_result_doc_path": (
            P7_HOLD004_POSITIVE_PUBLIC_SHAPE_IMPLEMENTATION_RESULT_DOC_PATH
        ),
        "hold004_positive_public_shape_implementation_result_doc_ref": (
            P7_HOLD004_POSITIVE_PUBLIC_SHAPE_IMPLEMENTATION_RESULT_DOC_REF
        ),
        "hold004_positive_public_shape_boundary_schema_version": positive_shape_schema_version,
        "hold004_positive_public_shape_boundary_status": positive_shape_status,
        "hold004_positive_public_shape_target_green_confirmed": positive_shape_target_green,
        "hold004_positive_public_shape_repaired_target_green_pending_full_suite": positive_shape_repaired_pending_full_suite,
        "hold004_positive_public_shape_true_self_denial_regression_preserved": positive_shape_true_self_denial_preserved,
        "hold004_positive_public_shape_emergency_regression_preserved": positive_shape_emergency_preserved,
        "hold004_positive_public_shape_support_required_regression_preserved": positive_shape_support_required_preserved,
        "hold004_positive_public_shape_input_material_bundle_confirmed": positive_shape_input_material_confirmed,
        "hold004_positive_public_shape_public_e2e_labelled_two_stage_confirmed": positive_shape_public_e2e_confirmed,
        "hold004_positive_public_shape_full_backend_suite_green_confirmed": False,
        "hold004_positive_public_shape_release_allowed": False,
        "hold004_step5_material_connection_schema_version": step5_schema_version,
        "hold004_step5_material_connection_status": step5_status,
        "hold004_step5_candidate_gate_red_classified": step5_red_classified,
        "hold004_step5_display_binding_red_present": step5_red_present,
        "hold004_step5_candidate_gate_red_closed": step5_red_closed,
        "hold004_step5_contract_classification": step5_contract_classification,
        "hold004_step5_required_followup_fixes": step5_required_followup_fixes,
        "hold004_step5_unresolved_red_refs": step5_unresolved_red_refs,
        "hold004_step5_closed_red_refs": step5_closed_red_refs,
        "hold004_step5_full_backend_suite_green_confirmed": False,
        "hold004_step5_release_allowed": False,
        "implementation_result_doc_refs": hold004_implementation_result_doc_refs,
        "handoff_target_module": P7_RELEASE_HANDOFF_TARGET_MODULE,
        "handoff_target_schema_version": PRODUCT_RELEASE_DECISION_SCHEMA_VERSION,
        "handoff_target_phase": PRODUCT_RELEASE_DECISION_PHASE,
        "handoff_target_step": PRODUCT_RELEASE_DECISION_TARGET_STEP,
        "release_decision_input_ready": input_ready,
        "release_input_status": input_status,
        "release_allowed": False,
        "real_device_submit_confirmed": False,
        "real_device_submit_modal_readfeel_verified": False,
        "full_backend_suite_green_confirmed": False,
        "full_backend_suite_green_claim_allowed": False,
        "split_all_groups_green_confirmed": backend_execution_summary_split_all_groups_green_confirmed,
        "split_green_is_full_backend_suite_green": False,
        "split_green_can_close_p7_hold004": False,
        "split_green_promoted_to_full_suite_green": False,
        "hold004_close_allowed": False,
        "release_decision_applied": False,
        "release_rollout_applied": False,
        "product_gate_ready": False,
        "product_gate_reached": False,
        "public_release_applied": False,
        "product_quality_released": False,
        "product_pass_is_release_ready": False,
        "product_pass_promoted_to_release_ready": False,
        "long_run_candidate_ready": bool(long_run.get("long_run_candidate_ready") is True),
        "long_run_candidate_is_release_ready": False,
        "product_gate_candidate_material_ready": bool(long_run.get("product_gate_candidate_material_ready") is True),
        "release_blockers": blockers,
        "required_followup_fixes": required_fixes,
        "required_followup_targets": _followup_targets(required_fixes, red_refs, hold_refs),
        "unresolved_red_refs": red_refs,
        "closed_red_refs": closed_red_refs,
        "classification_unresolved_red_refs": classification_unresolved_red_refs,
        "unresolved_hold_refs": hold_refs,
        "unresolved_timeout_refs": timeout_refs,
        "unreviewed_refs": unreviewed_refs,
        "release_decision_input_ready_requirements": {
            "source_long_run_candidate_ready_required": True,
            "unresolved_red_refs_absent_required": True,
            "unresolved_hold_refs_absent_required": True,
            "timeout_or_hang_absent_required": True,
            "ratings_unreviewed_absent_required": True,
            "full_backend_suite_green_claim_not_required": True,
            "real_device_submit_confirmed_required": True,
            "full_backend_suite_green_confirmed_required": True,
            "release_allowed_required": False,
            "body_free": True,
        },
        "source_material_status": {
            "p7_runner_result_connected": bool(runner),
            "long_run_gate_handoff_connected": bool(long_run),
            "runner_plan_connected": bool(plan),
            "long_run_candidate_status": clean_identifier(long_run.get("candidate_status"), default="review_required", max_length=80),
            "long_run_candidate_ready": bool(long_run.get("long_run_candidate_ready") is True),
            "release_decision_input_ready_from_long_run": long_run_input_ready,
            "review_missing_count": _as_int(blind_summary.get("review_missing_count"), 0),
            "p5_human_qa_completed": blind_summary.get("p5_human_qa_completed") is True,
            "p5_human_qa_review_status": clean_identifier(blind_summary.get("p5_human_qa_review_status"), default="review_required", max_length=80),
            "closed_red_count": len(closed_red_refs),
            "unresolved_red_count": len(red_refs),
            "unresolved_hold_count": len(hold_refs),
            "unresolved_timeout_count": len(timeout_refs),
            "unreviewed_count": len(unreviewed_refs),
            "real_device_submit_confirmed": real_device.get("real_device_submit_confirmed") is True,
            "full_backend_suite_green_confirmed": backend_split.get("full_backend_suite_green_confirmed") is True,
            "full_backend_suite_green_claim_allowed": False,
            "backend_suite_execution_summary_connected": backend_execution_summary_connected,
            "backend_suite_execution_summary_schema_version": backend_execution_summary_schema_version,
            "backend_suite_execution_summary_all_groups_executed": backend_execution_summary_all_groups_executed,
            "backend_suite_execution_summary_group_run_results_recorded": (
                backend_execution_summary_group_run_results_recorded
            ),
            "backend_suite_execution_summary_split_all_groups_green_confirmed": (
                backend_execution_summary_split_all_groups_green_confirmed
            ),
            "backend_suite_execution_summary_failed_group_ids": backend_execution_summary_failed_group_ids,
            "backend_suite_execution_summary_timeout_group_ids": backend_execution_summary_timeout_group_ids,
            "backend_suite_execution_summary_not_run_group_ids": backend_execution_summary_not_run_group_ids,
            "backend_suite_execution_summary_partial_group_ids": backend_execution_summary_partial_group_ids,
            "hold004_phase16_classified_red_present": hold004_phase16_classified_red_present,
            "hold004_phase16_candidate_boundary_registered": hold004_candidate_boundary_registered,
            "hold004_public_adjacent_red_registered": hold004_adjacent_public_red_registered,
            "hold004_phase16_implementation_result_documented": bool(hold004_phase16_classified_red_present),
            "hold004_phase16_implementation_result_doc_ref": (
                P7_HOLD004_PHASE16_IMPLEMENTATION_RESULT_DOC_REF if hold004_phase16_classified_red_present else ""
            ),
            "hold004_positive_public_shape_boundary_status": positive_shape_status,
            "hold004_positive_public_shape_target_green_confirmed": positive_shape_target_green,
            "hold004_positive_public_shape_repaired_target_green_pending_full_suite": positive_shape_repaired_pending_full_suite,
            "hold004_positive_public_shape_implementation_result_documented": (
                positive_shape_implementation_result_documented
            ),
            "hold004_positive_public_shape_implementation_result_doc_ref": (
                positive_shape_implementation_result_doc_ref
            ),
            "hold004_step5_material_connection_schema_version": step5_schema_version,
            "hold004_step5_candidate_gate_red_classified": step5_red_classified,
            "hold004_step5_display_binding_red_present": step5_red_present,
            "hold004_step5_candidate_gate_red_closed": step5_red_closed,
            "hold004_step5_required_followup_fixes": step5_required_followup_fixes,
            "official_group_02_capture_readiness_status": official_group_02_capture_readiness_status,
            "official_group_02_capture_blocked": official_group_02_capture_blocked,
            "received_snapshot_item_fingerprint_mismatch_unresolved": received_snapshot_item_fingerprint_mismatch_unresolved,
            "body_free": True,
        },
        "target_input_projection": {
            "measurement_run_material_present": True,
            "product_readfeel_scorecard_material_present": True,
            "phase11_long_run_product_gate_material_present": True,
            "runtime_surface_blind_qa_material_present": True,
            "blocker_matrix_material_present": bool(red_refs or hold_refs or blockers),
            "real_device_submit_confirmed": False,
            "full_backend_suite_green_confirmed": False,
            "full_backend_suite_green_claim_allowed": False,
            "backend_suite_execution_summary_connected": backend_execution_summary_connected,
            "backend_suite_execution_summary_split_all_groups_green_confirmed": (
                backend_execution_summary_split_all_groups_green_confirmed
            ),
            "split_green_promoted_to_full_suite_green": False,
            "split_green_is_full_backend_suite_green": False,
            "split_green_can_close_p7_hold004": False,
            "hold004_phase16_classified_red_present": hold004_phase16_classified_red_present,
            "hold004_phase16_candidate_boundary_registered": hold004_candidate_boundary_registered,
            "hold004_phase16_implementation_result_documented": bool(hold004_phase16_classified_red_present),
            "hold004_positive_public_shape_target_green_confirmed": positive_shape_target_green,
            "hold004_positive_public_shape_implementation_result_documented": (
                positive_shape_implementation_result_documented
            ),
            "hold004_positive_public_shape_full_backend_suite_green_confirmed": False,
            "hold004_positive_public_shape_release_allowed": False,
            "hold004_step5_candidate_gate_red_classified": step5_red_classified,
            "hold004_step5_display_binding_red_present": step5_red_present,
            "hold004_step5_candidate_gate_red_closed": step5_red_closed,
            "hold004_step5_full_backend_suite_green_confirmed": False,
            "hold004_step5_release_allowed": False,
            "official_group_02_capture_blocked": official_group_02_capture_blocked,
            "received_snapshot_item_fingerprint_mismatch_unresolved": received_snapshot_item_fingerprint_mismatch_unresolved,
            "release_decision_input_ready": input_ready,
            "release_allowed": False,
            "raw_body_removed_from_release_material": True,
            "body_free": True,
        },
        "material_summary": {
            "row_count": _as_int(long_run.get("row_count"), 0),
            "sequence_7_present": bool(sequence_coverage.get("sequence_7_present") is True),
            "history_line_value_increase_body_free": bool(long_run.get("p5_history_line_value_increase_body_free") is True),
            "p6_insight_overclaim_absence_body_free": bool(long_run.get("p6_insight_overclaim_absence_body_free") is True),
            "surface_signature_repetition_detected": bool(risk_metrics.get("surface_signature_repetition_detected") is True),
            "review_missing_count": _as_int(blind_summary.get("review_missing_count"), 0),
            "p5_human_qa_completed": blind_summary.get("p5_human_qa_completed") is True,
            "p5_human_qa_review_status": clean_identifier(blind_summary.get("p5_human_qa_review_status"), default="review_required", max_length=80),
            "p5_human_qa_local_body_review_packet_release_material": blind_summary.get("p5_human_qa_local_body_review_packet_release_material") is True,
            "p5_human_qa_scorecard_body_free": blind_summary.get("p5_human_qa_scorecard_body_free") is True,
            "p5_human_qa_release_material_body_free": blind_summary.get("p5_human_qa_release_material_body_free") is True,
            "candidate_material_ready": bool(candidate.get("candidate_material_ready") is True),
            "candidate_status": clean_identifier(candidate.get("candidate_status") or long_run.get("candidate_status"), default="review_required", max_length=80),
        },
        "manual_hold_status": {
            "r10_hold_matrix_schema_version": r10_matrix.get("schema_version"),
            "real_device_submit_confirmed": real_device.get("real_device_submit_confirmed") is True,
            "real_device_submit_hold_preserved": "P7-HOLD-003" in hold_refs,
            "real_device_automated_test_green_can_close": False,
            "full_backend_suite_green_confirmed": backend_split.get("full_backend_suite_green_confirmed") is True,
            "full_backend_suite_green_claim_allowed": False,
            "backend_suite_execution_summary_connected": backend_execution_summary_connected,
            "backend_suite_execution_summary_schema_version": backend_execution_summary_schema_version,
            "backend_suite_execution_summary_all_groups_executed": backend_execution_summary_all_groups_executed,
            "backend_suite_execution_summary_group_run_results_recorded": (
                backend_execution_summary_group_run_results_recorded
            ),
            "backend_suite_execution_summary_split_all_groups_green_confirmed": (
                backend_execution_summary_split_all_groups_green_confirmed
            ),
            "backend_suite_execution_summary_failed_group_ids": backend_execution_summary_failed_group_ids,
            "backend_suite_execution_summary_timeout_group_ids": backend_execution_summary_timeout_group_ids,
            "backend_suite_execution_summary_not_run_group_ids": backend_execution_summary_not_run_group_ids,
            "backend_suite_execution_summary_partial_group_ids": backend_execution_summary_partial_group_ids,
            "full_backend_suite_hold_preserved": "P7-HOLD-004" in hold_refs,
            "hold004_phase16_classified_red_present": hold004_phase16_classified_red_present,
            "hold004_phase16_candidate_boundary_registered": hold004_candidate_boundary_registered,
            "hold004_public_adjacent_red_registered": hold004_adjacent_public_red_registered,
            "hold004_required_followup_fixes": hold004_required_followup_fixes,
            "hold004_phase16_implementation_result_documented": bool(hold004_phase16_classified_red_present),
            "hold004_phase16_implementation_result_doc_ref": (
                P7_HOLD004_PHASE16_IMPLEMENTATION_RESULT_DOC_REF if hold004_phase16_classified_red_present else ""
            ),
            "hold004_positive_public_shape_boundary_status": positive_shape_status,
            "hold004_positive_public_shape_target_green_confirmed": positive_shape_target_green,
            "hold004_positive_public_shape_repaired_target_green_pending_full_suite": positive_shape_repaired_pending_full_suite,
            "hold004_positive_public_shape_true_self_denial_regression_preserved": positive_shape_true_self_denial_preserved,
            "hold004_positive_public_shape_emergency_regression_preserved": positive_shape_emergency_preserved,
            "hold004_positive_public_shape_support_required_regression_preserved": positive_shape_support_required_preserved,
            "hold004_positive_public_shape_input_material_bundle_confirmed": positive_shape_input_material_confirmed,
            "hold004_positive_public_shape_public_e2e_labelled_two_stage_confirmed": positive_shape_public_e2e_confirmed,
            "hold004_positive_public_shape_implementation_result_documented": (
                positive_shape_implementation_result_documented
            ),
            "hold004_positive_public_shape_implementation_result_doc_ref": (
                positive_shape_implementation_result_doc_ref
            ),
            "hold004_positive_public_shape_full_backend_suite_green_confirmed": False,
            "hold004_positive_public_shape_release_allowed": False,
            "hold004_step5_material_connection_schema_version": step5_schema_version,
            "hold004_step5_candidate_gate_red_classified": step5_red_classified,
            "hold004_step5_display_binding_red_present": step5_red_present,
            "hold004_step5_candidate_gate_red_closed": step5_red_closed,
            "hold004_step5_required_followup_fixes": step5_required_followup_fixes,
            "hold004_step5_unresolved_red_refs": step5_unresolved_red_refs,
            "hold004_step5_closed_red_refs": step5_closed_red_refs,
            "hold004_step5_full_backend_suite_green_confirmed": False,
            "hold004_step5_release_allowed": False,
            "official_group_02_capture_readiness_status": official_group_02_capture_readiness_status,
            "official_group_02_capture_blocked": official_group_02_capture_blocked,
            "official_group_02_capture_run_allowed": official_group_02_capture_run_allowed,
            "official_group_02_capture_result_recording_allowed": official_group_02_capture_result_recording_allowed,
            "received_snapshot_item_fingerprint_mismatch_unresolved": received_snapshot_item_fingerprint_mismatch_unresolved,
            "received_snapshot_blocker_refs": received_snapshot_blocker_refs,
            "split_green_is_full_backend_suite_green": False,
            "split_green_can_close_p7_hold004": False,
            "p7_complete_claim_allowed": False,
            "p8_start_allowed": False,
            "release_allowed": False,
            "body_free": True,
        },
        "release_boundary": {
            "p7_makes_release_decision": False,
            "release_allowed_true_requires_p10_release_readiness": True,
            "product_pass_candidate_is_release_ready": False,
            "long_run_candidate_is_release_ready": False,
            "public_release_applied": False,
            "real_device_submit_required_before_release": True,
            "full_backend_suite_required_before_release": True,
            "body_free": True,
        },
        "public_contract": public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
        "body_free": True,
    }
    assert_p7_release_decision_handoff_contract(handoff)
    return handoff


def build_p7_release_handoff(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Compatibility alias for the P7-8 shorter name."""

    return build_p7_release_decision_handoff(*args, **kwargs)


def build_p7_release_decision_handoff_material(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Compatibility alias used by tests and implementation-order notes."""

    return build_p7_release_decision_handoff(*args, **kwargs)


def assert_p7_release_decision_handoff_contract(handoff: Mapping[str, Any]) -> bool:
    data = safe_mapping(handoff)
    if data.get("schema_version") != P7_RELEASE_HANDOFF_SCHEMA_VERSION:
        raise ValueError("unexpected P7 release handoff schema_version")
    if data.get("phase") != P7_PHASE or data.get("scope") != P7_RELEASE_HANDOFF_SCOPE:
        raise ValueError("unexpected P7 release handoff phase/scope")
    if data.get("source_runner_plan_schema_version") != P7_RUNNER_PLAN_SCHEMA_VERSION:
        raise ValueError("P7 release handoff must reference the P7 runner plan")
    if data.get("source_red_ledger_schema_version") != P7_RED_LEDGER_SCHEMA_VERSION:
        raise ValueError("P7 release handoff must reference the P7 red ledger")
    classification_schema = clean_identifier(data.get("red_closure_classification_schema_version"), default="", max_length=128)
    if classification_schema and classification_schema != P7_RED_CLOSURE_CLASSIFICATION_MATRIX_SCHEMA_VERSION:
        raise ValueError("P7 release handoff has unexpected red closure classification schema")
    if data.get("r10_hold_matrix_schema_version") != P7_R10_HOLD_MATRIX_SCHEMA_VERSION:
        raise ValueError("P7 release handoff must reference the R10 HOLD matrix")
    if data.get("real_device_check_schema_version") != P7_REAL_DEVICE_MODAL_READFEEL_CHECK_SCHEMA_VERSION:
        raise ValueError("P7 release handoff must reference the real-device HOLD check")
    if data.get("backend_suite_split_matrix_schema_version") != P7_BACKEND_SUITE_SPLIT_MATRIX_SCHEMA_VERSION:
        raise ValueError("P7 release handoff must reference the backend suite split matrix")
    if data.get("source_long_run_gate_handoff_schema_version") != P7_LONG_RUN_GATE_HANDOFF_SCHEMA_VERSION:
        raise ValueError("P7 release handoff must source P7 Long-run Gate handoff material")
    if data.get("hold004_phase16_implementation_result_doc_path") != P7_HOLD004_PHASE16_IMPLEMENTATION_RESULT_DOC_PATH:
        raise ValueError("P7 release handoff must reference the HOLD-004 Phase16 implementation result document")
    if data.get("hold004_phase16_implementation_result_doc_ref") != P7_HOLD004_PHASE16_IMPLEMENTATION_RESULT_DOC_REF:
        raise ValueError("P7 release handoff must keep the HOLD-004 Phase16 result doc ref stable")
    if (
        data.get("hold004_positive_public_shape_implementation_result_doc_path")
        != P7_HOLD004_POSITIVE_PUBLIC_SHAPE_IMPLEMENTATION_RESULT_DOC_PATH
    ):
        raise ValueError("P7 release handoff must reference the positive public shape implementation result document")
    if (
        data.get("hold004_positive_public_shape_implementation_result_doc_ref")
        != P7_HOLD004_POSITIVE_PUBLIC_SHAPE_IMPLEMENTATION_RESULT_DOC_REF
    ):
        raise ValueError("P7 release handoff must keep the positive public shape result doc ref stable")
    if data.get("handoff_target_schema_version") != PRODUCT_RELEASE_DECISION_SCHEMA_VERSION:
        raise ValueError("P7 release handoff target schema changed")
    if data.get("release_allowed") is not False:
        raise ValueError("P7 release handoff must never allow release")
    for key in (
        "real_device_submit_confirmed",
        "real_device_submit_modal_readfeel_verified",
        "full_backend_suite_green_confirmed",
        "full_backend_suite_green_claim_allowed",
        "split_green_is_full_backend_suite_green",
        "split_green_can_close_p7_hold004",
        "split_green_promoted_to_full_suite_green",
        "hold004_close_allowed",
        "hold004_positive_public_shape_full_backend_suite_green_confirmed",
        "hold004_positive_public_shape_release_allowed",
        "hold004_step5_full_backend_suite_green_confirmed",
        "hold004_step5_release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7 release handoff must keep R10/R11 marker {key}=False")
    for key in (
        "release_decision_applied",
        "release_rollout_applied",
        "product_gate_ready",
        "product_gate_reached",
        "public_release_applied",
        "product_quality_released",
        "product_pass_is_release_ready",
        "product_pass_promoted_to_release_ready",
        "long_run_candidate_is_release_ready",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7 release handoff must keep {key}=False")
    if data.get("body_free") is not True:
        raise ValueError("P7 release handoff must be body-free")
    if data.get("backend_suite_execution_summary_connected") is True:
        if data.get("backend_suite_execution_summary_schema_version") != P7_HOLD004_BACKEND_SUITE_EXECUTION_SUMMARY_SCHEMA_VERSION:
            raise ValueError("P7 release handoff backend execution summary schema_version mismatch")
        if data.get("backend_suite_execution_summary_collect_baseline_id") != P7_HOLD004_BACKEND_COLLECT_BASELINE_ID:
            raise ValueError("P7 release handoff must connect current collect baseline id")
        if data.get("backend_suite_execution_summary_inventory_id") != P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_ID:
            raise ValueError("P7 release handoff must connect current group inventory id")
        if data.get("backend_suite_execution_summary_plan_id") != P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_ID:
            raise ValueError("P7 release handoff must connect current execution plan id")
        for key in ("current_collect_baseline_connected", "current_group_inventory_connected", "current_execution_plan_connected", "old_baseline_not_used_as_current", "backend_suite_group_02_count_current"):
            if data.get(key) is not True:
                raise ValueError(f"P7 release handoff must keep {key}=true")
        connection = safe_mapping(data.get("matrix_current_baseline_connection"))
        if connection.get("collect_baseline_id") != P7_HOLD004_BACKEND_COLLECT_BASELINE_ID:
            raise ValueError("P7 release handoff current baseline connection collect id mismatch")
        if connection.get("old_baseline_used_as_current") is not False:
            raise ValueError("P7 release handoff must not use old baseline as current")
        if data.get("split_green_is_full_backend_suite_green") is not False:
            raise ValueError("P7 release handoff must not treat split green as full backend-suite green")
        if data.get("split_green_can_close_p7_hold004") is not False:
            raise ValueError("P7 release handoff must not close HOLD-004 from split execution summary")
        if data.get("hold004_close_allowed") is not False:
            raise ValueError("P7 release handoff must keep HOLD-004 close disallowed")
        if data.get("backend_suite_execution_summary_split_all_groups_green_confirmed") is True:
            if data.get("full_backend_suite_green_confirmed") is not False:
                raise ValueError("P7 release handoff must not promote split green to full-suite green")
            if data.get("split_green_promoted_to_full_suite_green") is not False:
                raise ValueError("P7 release handoff must keep split green promotion false")
            if "P7-HOLD-004" not in dedupe_identifiers(data.get("unresolved_hold_refs"), limit=160, max_length=160):
                raise ValueError("P7 release handoff must keep HOLD-004 unresolved after split green")
    if data.get("official_group_02_capture_readiness_schema_version"):
        readiness_schema_version = clean_identifier(
            data.get("official_group_02_capture_readiness_schema_version"), default="", max_length=160
        )
        if readiness_schema_version not in P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_ALLOWED_SCHEMA_VERSIONS:
            raise ValueError("P7 release handoff official group_02 readiness schema_version mismatch")
        readiness_after_refresh = readiness_schema_version == P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_SCHEMA_VERSION_V2
        if data.get("received_snapshot_item_fingerprint_mismatch_unresolved") is True:
            if data.get("official_group_02_capture_readiness_status") != P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_BLOCKED_BY_ITEM_FINGERPRINT_MISMATCH:
                raise ValueError("P7 release handoff must expose unresolved received snapshot item mismatch")
            if data.get("official_group_02_capture_blocked") is not True:
                raise ValueError("P7 release handoff must keep official group_02 capture blocked")
            if data.get("official_group_02_capture_run_allowed") is not False:
                raise ValueError("P7 release handoff must not allow official capture run while mismatch is unresolved")
            if data.get("official_group_02_capture_result_recording_allowed") is not False:
                raise ValueError("P7 release handoff must not allow official capture recording while mismatch is unresolved")
            if P7_HOLD004_RECEIVED_SNAPSHOT_ITEM_FINGERPRINT_MISMATCH_BLOCKER_REF not in dedupe_identifiers(data.get("release_blockers"), limit=240, max_length=160):
                raise ValueError("P7 release handoff must keep received snapshot item mismatch as release blocker")
        if readiness_after_refresh:
            if data.get("official_group_02_capture_readiness_status") != P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_READY:
                raise ValueError("P7 release handoff after-refresh group_02 readiness must be READY")
            if data.get("received_snapshot_item_fingerprint_mismatch_unresolved") is not False:
                raise ValueError("P7 release handoff after-refresh readiness must resolve received mismatch")
            if data.get("received_snapshot_baseline_fingerprint_reconciled") is not True:
                raise ValueError("P7 release handoff after-refresh readiness must carry reconciled baseline")
            if data.get("official_group_02_capture_blocked") is not False:
                raise ValueError("P7 release handoff after-refresh readiness must unblock official capture")
            if data.get("official_group_02_capture_run_allowed") is not True:
                raise ValueError("P7 release handoff after-refresh readiness must allow official capture run")
            if data.get("official_group_02_capture_result_recording_allowed") is not True:
                raise ValueError("P7 release handoff after-refresh readiness must allow official capture result recording")
            if data.get("active_baseline_update_applied_to_runtime_builders") is not True:
                raise ValueError("P7 release handoff must carry runtime-builder refresh application")
            if data.get("source_snapshot_ref_updated_in_active_builders") is not True:
                raise ValueError("P7 release handoff must carry active builder source refresh")
            if data.get("release_allowed") is not False:
                raise ValueError("P7 release handoff readiness must not allow release")
    status = clean_identifier(data.get("release_input_status"), default="")
    if status not in _ALLOWED_INPUT_STATUSES:
        raise ValueError("P7 release input status changed")
    blockers = dedupe_identifiers(data.get("release_blockers"), limit=240, max_length=160)
    red_refs = dedupe_identifiers(data.get("unresolved_red_refs"), limit=160, max_length=160)
    closed_red_refs = dedupe_identifiers(data.get("closed_red_refs"), limit=160, max_length=160)
    if set(red_refs) & set(closed_red_refs):
        raise ValueError("P7 release handoff must not keep closed RED refs unresolved")
    if classification_schema:
        closed_red_set = set(closed_red_refs)
        unresolved_red_set = set(red_refs)
        timeout_ref_set = set(dedupe_identifiers(data.get("unresolved_timeout_refs"), limit=80, max_length=160))
        if not {"P7-RED-001", "P7-RED-002"}.issubset(closed_red_set):
            raise ValueError("P7 release handoff must carry R0-R5 Positive Recovery closure refs when classification is applied")
        extra_positive_reds = {"P7-RED-001", "P7-RED-002"} & unresolved_red_set
        if extra_positive_reds:
            raise ValueError("P7 release handoff must not keep closed Positive Recovery RED refs unresolved")
        red003_closed = "P7-RED-003" in closed_red_set
        if red003_closed:
            if "P7-RED-003" in unresolved_red_set or "P7-RED-003" in timeout_ref_set:
                raise ValueError("P7 release handoff must remove P7-RED-003 from unresolved RED/timeout refs after R13 closure")
        elif "P7-RED-003" not in unresolved_red_set:
            raise ValueError("P7 release handoff must keep P7-RED-003 unresolved when classification has not closed it")
    hold_refs = dedupe_identifiers(data.get("unresolved_hold_refs"), limit=160, max_length=160)
    timeout_refs = dedupe_identifiers(data.get("unresolved_timeout_refs"), limit=80, max_length=160)
    unreviewed_refs = dedupe_identifiers(data.get("unreviewed_refs"), limit=80, max_length=160)
    if data.get("release_decision_input_ready") is True:
        if status != "input_material_ready":
            raise ValueError("P7 release input ready must use input_material_ready status")
        if blockers or red_refs or hold_refs or timeout_refs or unreviewed_refs:
            raise ValueError("P7 release input cannot be ready with blockers/red/HOLD/timeout/unreviewed refs")
        if data.get("long_run_candidate_ready") is not True:
            raise ValueError("P7 release input ready requires long-run candidate material ready")
    else:
        if status == "input_material_ready":
            raise ValueError("P7 input_material_ready status requires release_decision_input_ready=True")
    requirements = safe_mapping(data.get("release_decision_input_ready_requirements"))
    required_false = ("release_allowed_required",)
    for key in required_false:
        if requirements.get(key) is not False:
            raise ValueError(f"P7 release handoff requirement {key} must be false")
    for key in (
        "source_long_run_candidate_ready_required",
        "unresolved_red_refs_absent_required",
        "unresolved_hold_refs_absent_required",
        "timeout_or_hang_absent_required",
        "ratings_unreviewed_absent_required",
        "full_backend_suite_green_claim_not_required",
        "real_device_submit_confirmed_required",
        "full_backend_suite_green_confirmed_required",
        "body_free",
    ):
        if requirements.get(key) is not True:
            raise ValueError(f"P7 release handoff requirement {key} must be true")
    material_summary = safe_mapping(data.get("material_summary"))
    if material_summary.get("p5_human_qa_local_body_review_packet_release_material") is not False:
        raise ValueError("P7 release handoff must not turn local human QA body packet into release material")
    if material_summary.get("p5_human_qa_scorecard_body_free") is not True or material_summary.get("p5_human_qa_release_material_body_free") is not True:
        raise ValueError("P7 release handoff must keep P5 human QA body-free material boundary")
    if material_summary.get("p5_human_qa_completed") is not True and "p5_human_qa_review_required" not in data.get("release_blockers", []):
        raise ValueError("P7 release handoff must keep P5 human QA as blocker until completed")
    manual = safe_mapping(data.get("manual_hold_status"))
    if manual.get("real_device_submit_confirmed") is not False:
        raise ValueError("P7 release handoff must keep real-device submit/modal read-feel unverified in R10/R11")
    if manual.get("real_device_submit_hold_preserved") is not True or "P7-HOLD-003" not in hold_refs:
        raise ValueError("P7 release handoff must keep P7-HOLD-003 until real-device confirmation")
    if manual.get("real_device_automated_test_green_can_close") is not False:
        raise ValueError("P7 release handoff must not close real-device HOLD by automated test green")
    if manual.get("full_backend_suite_green_confirmed") is not False:
        raise ValueError("P7 release handoff must keep full backend suite green unconfirmed in R10/R11")
    if manual.get("full_backend_suite_green_claim_allowed") is not False:
        raise ValueError("P7 release handoff must not allow full backend suite green claim")
    if manual.get("full_backend_suite_hold_preserved") is not True or "P7-HOLD-004" not in hold_refs:
        raise ValueError("P7 release handoff must keep P7-HOLD-004 until full backend suite confirmation")
    if manual.get("hold004_phase16_classified_red_present") is True:
        if manual.get("hold004_phase16_candidate_boundary_registered") is not True:
            raise ValueError("P7 release handoff must preserve classified HOLD-004 candidate boundary")
        if "phase16_complete_composer_candidate_boundary" not in dedupe_identifiers(
            manual.get("hold004_required_followup_fixes"),
            limit=120,
            max_length=160,
        ):
            raise ValueError("P7 release handoff must expose HOLD-004 Phase16 follow-up fixes")
        if P7_HOLD004_PHASE16_IMPLEMENTATION_RESULT_DOC_PATH not in dedupe_identifiers(
            data.get("implementation_result_doc_refs"),
            limit=40,
            max_length=220,
        ):
            raise ValueError("P7 release handoff must expose HOLD-004 Phase16 implementation result doc refs")
        if manual.get("hold004_phase16_implementation_result_documented") is not True:
            raise ValueError("P7 release handoff must carry the HOLD-004 Phase16 implementation result marker")
        if manual.get("hold004_phase16_implementation_result_doc_ref") != P7_HOLD004_PHASE16_IMPLEMENTATION_RESULT_DOC_REF:
            raise ValueError("P7 release handoff must carry the stable HOLD-004 Phase16 result doc ref")
    if data.get("hold004_positive_public_shape_boundary_schema_version"):
        if data.get("hold004_positive_public_shape_boundary_schema_version") != P7_HOLD004_POSITIVE_PUBLIC_SHAPE_SCHEMA_VERSION:
            raise ValueError("P7 release handoff positive public shape schema_version mismatch")
        if data.get("hold004_positive_public_shape_boundary_status") != P7_HOLD004_POSITIVE_PUBLIC_SHAPE_REPAIRED_STATUS:
            raise ValueError("P7 release handoff must keep positive public shape as repaired-pending-full-suite")
        for key in (
            "hold004_positive_public_shape_target_green_confirmed",
            "hold004_positive_public_shape_repaired_target_green_pending_full_suite",
            "hold004_positive_public_shape_true_self_denial_regression_preserved",
            "hold004_positive_public_shape_emergency_regression_preserved",
            "hold004_positive_public_shape_support_required_regression_preserved",
            "hold004_positive_public_shape_input_material_bundle_confirmed",
            "hold004_positive_public_shape_public_e2e_labelled_two_stage_confirmed",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7 release handoff must keep {key}=True")
        if data.get("hold004_positive_public_shape_full_backend_suite_green_confirmed") is not False:
            raise ValueError("P7 release handoff must not promote positive target green to full-suite green")
        if data.get("hold004_positive_public_shape_release_allowed") is not False:
            raise ValueError("P7 release handoff must keep positive public shape release_allowed=false")
        if P7_HOLD004_POSITIVE_PUBLIC_SHAPE_IMPLEMENTATION_RESULT_DOC_PATH not in dedupe_identifiers(
            data.get("implementation_result_doc_refs"),
            limit=40,
            max_length=220,
        ):
            raise ValueError("P7 release handoff must expose the positive public shape implementation result doc refs")
        if manual.get("hold004_positive_public_shape_implementation_result_documented") is not True:
            raise ValueError("P7 release handoff must carry the positive public shape implementation result marker")
        if (
            manual.get("hold004_positive_public_shape_implementation_result_doc_ref")
            != P7_HOLD004_POSITIVE_PUBLIC_SHAPE_IMPLEMENTATION_RESULT_DOC_REF
        ):
            raise ValueError("P7 release handoff must carry the stable positive public shape result doc ref")
        for key in (
            "hold004_positive_public_shape_target_green_confirmed",
            "hold004_positive_public_shape_repaired_target_green_pending_full_suite",
            "hold004_positive_public_shape_true_self_denial_regression_preserved",
            "hold004_positive_public_shape_emergency_regression_preserved",
            "hold004_positive_public_shape_support_required_regression_preserved",
            "hold004_positive_public_shape_input_material_bundle_confirmed",
            "hold004_positive_public_shape_public_e2e_labelled_two_stage_confirmed",
        ):
            if manual.get(key) is not True:
                raise ValueError(f"P7 release manual HOLD status must keep {key}=True")
        if manual.get("hold004_positive_public_shape_full_backend_suite_green_confirmed") is not False:
            raise ValueError("P7 release manual HOLD status must not claim positive public shape full-suite green")
        if manual.get("hold004_positive_public_shape_release_allowed") is not False:
            raise ValueError("P7 release manual HOLD status must keep positive public shape release_allowed=false")
        if "positive_public_shape_target_green_pending_full_suite" not in blockers:
            raise ValueError("P7 release handoff must keep positive public shape as pending full-suite follow-up")
    if data.get("hold004_step5_material_connection_schema_version"):
        if data.get("hold004_step5_material_connection_schema_version") != P7_HOLD004_STEP5_R6_MATERIAL_CONNECTION_SCHEMA_VERSION:
            raise ValueError("P7 release handoff Step5 material schema_version mismatch")
        if data.get("hold004_step5_candidate_gate_red_classified") is not True:
            raise ValueError("P7 release handoff must classify the Step5 candidate-gate material")
        if "step5_display_binding_contract_consistency" not in dedupe_identifiers(
            data.get("hold004_step5_required_followup_fixes"),
            limit=120,
            max_length=160,
        ):
            raise ValueError("P7 release handoff must expose the Step5 display-binding follow-up")
        if data.get("hold004_step5_full_backend_suite_green_confirmed") is not False:
            raise ValueError("P7 release handoff must not promote Step5 material to full-suite green")
        if data.get("hold004_step5_release_allowed") is not False:
            raise ValueError("P7 release handoff must keep Step5 release_allowed=false")
        if data.get("hold004_step5_display_binding_red_present") is True and data.get("hold004_step5_candidate_gate_red_closed") is not True:
            if P7_HOLD004_STEP5_RED_ID not in red_refs:
                raise ValueError("P7 release handoff must keep unresolved Step5 red in red refs")
            if P7_HOLD004_STEP5_RED_ID not in blockers:
                raise ValueError("P7 release handoff must keep unresolved Step5 red as blocker")
        if manual.get("hold004_step5_material_connection_schema_version") != data.get("hold004_step5_material_connection_schema_version"):
            raise ValueError("P7 release handoff manual HOLD status must mirror Step5 schema")
        if manual.get("hold004_step5_full_backend_suite_green_confirmed") is not False:
            raise ValueError("P7 release manual HOLD status must not claim Step5 full-suite green")
        if manual.get("hold004_step5_release_allowed") is not False:
            raise ValueError("P7 release manual HOLD status must keep Step5 release_allowed=false")
    if manual.get("received_snapshot_item_fingerprint_mismatch_unresolved") is True:
        if manual.get("official_group_02_capture_blocked") is not True:
            raise ValueError("P7 release manual HOLD status must keep official group_02 capture blocked")
        if manual.get("official_group_02_capture_run_allowed") is not False:
            raise ValueError("P7 release manual HOLD status must keep official group_02 capture run disallowed")
        if P7_HOLD004_RECEIVED_SNAPSHOT_ITEM_FINGERPRINT_MISMATCH_BLOCKER_REF not in dedupe_identifiers(manual.get("received_snapshot_blocker_refs"), limit=80, max_length=180):
            raise ValueError("P7 release manual HOLD status must keep received snapshot mismatch blocker")
    if manual.get("split_green_is_full_backend_suite_green") is not False:
        raise ValueError("P7 release handoff must not convert split green into full-suite green")
    for key in ("p7_complete_claim_allowed", "p8_start_allowed", "release_allowed"):
        if manual.get(key) is not False:
            raise ValueError(f"P7 manual HOLD status must keep {key}=False")
    if manual.get("body_free") is not True:
        raise ValueError("P7 manual HOLD status must be body-free")
    if "real_device_submit_modal_readfeel_unverified" not in blockers:
        raise ValueError("P7 release handoff must keep real-device submit/modal read-feel as blocker")
    if "full_backend_suite_green_unconfirmed" not in blockers:
        raise ValueError("P7 release handoff must keep full backend suite unconfirmed as blocker")
    projection = safe_mapping(data.get("target_input_projection"))
    if projection.get("release_allowed") is not False or projection.get("body_free") is not True:
        raise ValueError("P7 release handoff projection must remain body-free and release-closed")
    for key in (
        "real_device_submit_confirmed",
        "full_backend_suite_green_confirmed",
        "full_backend_suite_green_claim_allowed",
        "split_green_promoted_to_full_suite_green",
    ):
        if projection.get(key) is not False:
            raise ValueError(f"P7 release handoff projection must keep {key}=False")
    boundary = safe_mapping(data.get("release_boundary"))
    if boundary.get("p7_makes_release_decision") is not False:
        raise ValueError("P7 must not make the release decision")
    if boundary.get("release_allowed_true_requires_p10_release_readiness") is not True:
        raise ValueError("P7 release handoff must route release_allowed true to P10")
    if boundary.get("product_pass_candidate_is_release_ready") is not False or boundary.get("long_run_candidate_is_release_ready") is not False:
        raise ValueError("P7 release handoff must not convert candidates to Release Ready")
    if boundary.get("real_device_submit_required_before_release") is not True:
        raise ValueError("P7 release handoff must require real-device submit/modal read-feel before release")
    if boundary.get("full_backend_suite_required_before_release") is not True:
        raise ValueError("P7 release handoff must require full backend suite before release")
    assert_false_markers(safe_mapping(data.get("public_contract")), source="p7_release_handoff.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_release_handoff.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_release_handoff")
    return True


__all__ = [
    "P7_RELEASE_HANDOFF_SCHEMA_VERSION",
    "P7_RELEASE_HANDOFF_SCOPE",
    "P7_RELEASE_HANDOFF_STEP",
    "P7_RELEASE_HANDOFF_TARGET_MODULE",
    "P7_HOLD004_PHASE16_IMPLEMENTATION_RESULT_DOC_PATH",
    "P7_HOLD004_PHASE16_IMPLEMENTATION_RESULT_DOC_REF",
    "P7_HOLD004_POSITIVE_PUBLIC_SHAPE_IMPLEMENTATION_RESULT_DOC_PATH",
    "P7_HOLD004_POSITIVE_PUBLIC_SHAPE_IMPLEMENTATION_RESULT_DOC_REF",
    "assert_p7_release_decision_handoff_contract",
    "build_p7_release_decision_handoff",
    "build_p7_release_decision_handoff_material",
    "build_p7_release_handoff",
]
