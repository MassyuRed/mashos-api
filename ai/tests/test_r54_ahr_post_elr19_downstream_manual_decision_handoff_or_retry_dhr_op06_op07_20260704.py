# -*- coding: utf-8 -*-
"""R54-AHR Post-ELR19 DHR-OP06/OP07 branch resolver and manual material tests."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704 as dhr
from test_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op18_op19_20260703 import (
    _op17_waiting,
)
from test_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op02_op03_20260704 import (
    _op02_accepted_intake,
)
from test_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op04_op05_20260704 import (
    _assert_bodyfree_no_touch_no_promotion,
    _op04_confirmed_separation,
    _op04_not_confirmed_separation,
)


def _op05_retry_or_start_preflight() -> dict[str, object]:
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan(
        actual_source_claim_separation=_op04_not_confirmed_separation(),
    )
    assert material["dhr_op05_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_PREFLIGHT_SCAN_WAITING_OR_INCOMPLETE_REF
    assert material["actual_source_claim_confirmed_for_downstream_handoff"] is False
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan_contract(material)
    return material


def _op05_handoff_ready_preflight() -> dict[str, object]:
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan(
        actual_source_claim_separation=_op04_confirmed_separation(),
    )
    assert material["dhr_op05_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_PREFLIGHT_SCAN_CLEAR_BODYFREE_REF
    assert material["actual_source_claim_confirmed_for_downstream_handoff"] is True
    assert material["dmd_handoff_plan_candidate_allowed"] is True
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan_contract(material)
    return material


def _op05_repair_preflight() -> dict[str, object]:
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan(
        actual_source_claim_separation=_op04_confirmed_separation(),
        additional_bodyfree_materials=[{"release_allowed": True}],
    )
    assert material["dhr_op05_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_PREFLIGHT_SCAN_REPAIR_REQUIRED_REF
    assert material["preflight_repair_required"] is True
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan_contract(material)
    return material


def _op05_waiting_preflight() -> dict[str, object]:
    op03 = dhr.build_p7_r54_ahr_post_elr19_dhr_op03_elr_op17_dmd_compatible_receipt_candidate_extraction(
        elr_op18_downstream_manual_decision_hold_intake=_op02_accepted_intake(),
        elr_op17_dmd_compatible_receipt_candidate=_op17_waiting(),
    )
    assert op03["dhr_op03_waiting_for_complete_evidence"] is True
    op04 = dhr.build_p7_r54_ahr_post_elr19_dhr_op04_actual_source_claim_separation_invalid_source_classification(
        elr_op17_dmd_compatible_receipt_candidate_extraction=op03,
    )
    assert op04["dhr_op04_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_ACTUAL_SOURCE_WAITING_FOR_EXTERNAL_BODYFREE_CLAIM_REF
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan(
        actual_source_claim_separation=op04,
    )
    assert material["dhr_op05_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_PREFLIGHT_SCAN_WAITING_OR_INCOMPLETE_REF
    assert material["op04_actual_source_claim_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_ACTUAL_SOURCE_WAITING_FOR_EXTERNAL_BODYFREE_CLAIM_REF
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan_contract(material)
    return material


def _op06_retry_or_start_branch() -> dict[str, object]:
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op06_handoff_or_retry_deterministic_branch_resolver(
        bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan=_op05_retry_or_start_preflight(),
    )
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op06_handoff_or_retry_deterministic_branch_resolver_contract(material)
    return material


def _op06_handoff_ready_branch() -> dict[str, object]:
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op06_handoff_or_retry_deterministic_branch_resolver(
        bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan=_op05_handoff_ready_preflight(),
    )
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op06_handoff_or_retry_deterministic_branch_resolver_contract(material)
    return material


def test_dhr_op06_resolves_current_confirmed_material_default_to_retry_or_start() -> None:
    material = _op06_retry_or_start_branch()

    assert set(material) == set(dhr.P7_R54_AHR_POST_ELR19_DHR_OP06_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP06_SCHEMA_VERSION
    assert material["operation_step_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP06_STEP_REF
    assert material["op05_contract_valid"] is True
    assert material["op05_actual_source_claim_confirmed_for_downstream_handoff"] is False
    assert material["branch_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_BRANCH_RETRY_OR_START_REQUIRED_BEFORE_DOWNSTREAM_HANDOFF_REF
    assert material["selected_branch_ref"] == material["branch_ref"]
    assert material["dhr_op06_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP06_STATUS_RETRY_OR_START_REQUIRED_REF
    assert material["retry_or_start_precedence_applied"] is True
    assert material["retry_or_start_actual_local_only_human_review_required"] is True
    assert material["dmd_handoff_allowed_as_manual_decision_candidate"] is False
    assert material["next_required_step"] == dhr.P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_RETRY_OR_START_ACTUAL_LOCAL_ONLY_HUMAN_REVIEW_OPERATION_REF
    assert material["next_dhr_step_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_DHR_OP07_REF
    _assert_bodyfree_no_touch_no_promotion(material)


def test_dhr_op06_resolves_handoff_ready_only_for_confirmed_external_source_and_clear_scan() -> None:
    material = _op06_handoff_ready_branch()

    assert material["branch_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_BRANCH_DMD_HANDOFF_READY_MANUAL_DECISION_REQUIRED_NO_AUTO_EXECUTION_REF
    assert material["dhr_op06_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP06_STATUS_DMD_HANDOFF_READY_MANUAL_DECISION_REQUIRED_REF
    assert material["op05_preflight_scan_passed"] is True
    assert material["op05_actual_source_claim_confirmed_for_downstream_handoff"] is True
    assert material["op05_dmd_handoff_plan_candidate_allowed"] is True
    assert material["handoff_ready_selected_after_no_repair_no_wait_no_retry"] is True
    assert material["dmd_handoff_ready_manual_decision_required_no_auto_execution"] is True
    assert material["dmd_handoff_allowed_as_manual_decision_candidate"] is True
    assert material["dmd_direct_call_safe_without_adapter"] is False
    assert material["dmh_op18_finalizer_fake_generation_allowed"] is False
    assert material["dmd_execution_started_here"] is False
    assert material["next_required_step"] == dhr.P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_MANUAL_DECISION_EXECUTE_OR_DECLINE_DMD_HANDOFF_WITHOUT_AUTO_PROMOTION_REF
    _assert_bodyfree_no_touch_no_promotion(material)


def test_dhr_op06_prioritizes_repair_before_handoff_or_retry() -> None:
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op06_handoff_or_retry_deterministic_branch_resolver(
        bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan=_op05_repair_preflight(),
    )

    assert material["branch_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_BRANCH_BODYFREE_EVIDENCE_REPAIR_REQUIRED_REF
    assert material["dhr_op06_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP06_STATUS_REPAIR_REQUIRED_REF
    assert material["repair_precedence_applied"] is True
    assert material["bodyfree_evidence_boundary_repair_required"] is True
    assert "dhr_op05_promotion_claim_detected" in material["branch_blocker_refs"]
    assert material["next_required_step"] == dhr.P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_STOP_AND_REPAIR_POST_ELR19_BODYFREE_EVIDENCE_BOUNDARY_REF
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op06_handoff_or_retry_deterministic_branch_resolver_contract(material)
    _assert_bodyfree_no_touch_no_promotion(material)


def test_dhr_op06_prioritizes_wait_when_elr_candidate_is_still_waiting() -> None:
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op06_handoff_or_retry_deterministic_branch_resolver(
        bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan=_op05_waiting_preflight(),
    )

    assert material["branch_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_BRANCH_WAIT_FOR_ELR_COMPLETE_EVIDENCE_OR_MANUAL_HOLD_REF
    assert material["dhr_op06_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP06_STATUS_WAITING_REF
    assert material["wait_precedence_applied"] is True
    assert material["elr_complete_evidence_or_manual_hold_waiting_required"] is True
    assert material["retry_or_start_actual_local_only_human_review_required"] is False
    assert material["next_required_step"] == dhr.P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_WAIT_FOR_ELR_COMPLETE_EVIDENCE_OR_MANUAL_HOLD_MATERIAL_REF
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op06_handoff_or_retry_deterministic_branch_resolver_contract(material)
    _assert_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("branch_ref", dhr.P7_R54_AHR_POST_ELR19_DHR_BRANCH_DMD_HANDOFF_READY_MANUAL_DECISION_REQUIRED_NO_AUTO_EXECUTION_REF),
        ("dmd_handoff_allowed_as_manual_decision_candidate", True),
        ("dmd_direct_call_safe_without_adapter", True),
        ("dmh_op18_finalizer_fake_generation_allowed", True),
        ("dmd_execution_started_here", True),
        ("r52_actual_execution_started_here", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("manual_decision_auto_executes_downstream", True),
    ],
)
def test_dhr_op06_contract_rejects_branch_or_promotion_mutations(field: str, bad_value: object) -> None:
    material = _op06_retry_or_start_branch()
    material[field] = bad_value
    with pytest.raises(ValueError):
        dhr.assert_p7_r54_ahr_post_elr19_dhr_op06_handoff_or_retry_deterministic_branch_resolver_contract(material)


def test_dhr_op06_contract_requires_exactly_one_branch_flag() -> None:
    material = _op06_retry_or_start_branch()
    material["dmd_handoff_ready_manual_decision_required_no_auto_execution"] = True
    with pytest.raises(ValueError):
        dhr.assert_p7_r54_ahr_post_elr19_dhr_op06_handoff_or_retry_deterministic_branch_resolver_contract(material)


def test_dhr_op07_materializes_retry_or_start_manual_decision_without_auto_starting_review() -> None:
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op07_manual_decision_materialization(
        handoff_or_retry_deterministic_branch_resolver=_op06_retry_or_start_branch(),
    )

    assert set(material) == set(dhr.P7_R54_AHR_POST_ELR19_DHR_OP07_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP07_SCHEMA_VERSION
    assert material["operation_step_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP07_STEP_REF
    assert material["manual_decision_materialized"] is True
    assert material["manual_decision_materialized_bodyfree"] is True
    assert material["manual_decision_required"] is True
    assert material["manual_decision_required_without_auto_execution"] is True
    assert material["selected_branch_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_BRANCH_RETRY_OR_START_REQUIRED_BEFORE_DOWNSTREAM_HANDOFF_REF
    assert material["dhr_op07_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP07_STATUS_RETRY_OR_START_REQUIRED_REF
    assert material["recommended_next_step_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_RETRY_OR_START_ACTUAL_LOCAL_ONLY_HUMAN_REVIEW_OPERATION_REF
    assert material["retry_or_start_required"] is True
    assert material["auto_starts_actual_review"] is False
    assert material["auto_executes_dmd"] is False
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op07_manual_decision_materialization_contract(material)
    _assert_bodyfree_no_touch_no_promotion(material)


def test_dhr_op07_materializes_handoff_ready_as_manual_candidate_without_dmd_execution() -> None:
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op07_manual_decision_materialization(
        handoff_or_retry_deterministic_branch_resolver=_op06_handoff_ready_branch(),
    )

    assert material["selected_branch_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_BRANCH_DMD_HANDOFF_READY_MANUAL_DECISION_REQUIRED_NO_AUTO_EXECUTION_REF
    assert material["dhr_op07_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP07_STATUS_DMD_HANDOFF_READY_MANUAL_DECISION_REQUIRED_REF
    assert material["dmd_handoff_allowed_as_manual_decision_candidate"] is True
    assert material["recommended_next_step_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_MANUAL_DECISION_EXECUTE_OR_DECLINE_DMD_HANDOFF_WITHOUT_AUTO_PROMOTION_REF
    assert material["auto_executes_dmd"] is False
    assert material["auto_executes_r52"] is False
    assert material["auto_starts_p8"] is False
    assert material["release_allowed"] is False
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op07_manual_decision_materialization_contract(material)
    _assert_bodyfree_no_touch_no_promotion(material)


def test_dhr_op07_materializes_repair_branch_with_bodyfree_blockers() -> None:
    op06 = dhr.build_p7_r54_ahr_post_elr19_dhr_op06_handoff_or_retry_deterministic_branch_resolver(
        bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan=_op05_repair_preflight(),
    )
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op07_manual_decision_materialization(
        handoff_or_retry_deterministic_branch_resolver=op06,
    )

    assert material["selected_branch_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_BRANCH_BODYFREE_EVIDENCE_REPAIR_REQUIRED_REF
    assert material["repair_required"] is True
    assert material["branch_blocker_ref_count"] > 0
    assert material["recommended_next_step_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_STOP_AND_REPAIR_POST_ELR19_BODYFREE_EVIDENCE_BOUNDARY_REF
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op07_manual_decision_materialization_contract(material)
    _assert_bodyfree_no_touch_no_promotion(material)


def test_dhr_op07_materializes_wait_branch_without_retry_or_handoff_promotion() -> None:
    op06 = dhr.build_p7_r54_ahr_post_elr19_dhr_op06_handoff_or_retry_deterministic_branch_resolver(
        bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan=_op05_waiting_preflight(),
    )
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op07_manual_decision_materialization(
        handoff_or_retry_deterministic_branch_resolver=op06,
    )

    assert material["selected_branch_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_BRANCH_WAIT_FOR_ELR_COMPLETE_EVIDENCE_OR_MANUAL_HOLD_REF
    assert material["waiting_required"] is True
    assert material["retry_or_start_required"] is False
    assert material["dmd_handoff_allowed_as_manual_decision_candidate"] is False
    assert material["recommended_next_step_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_WAIT_FOR_ELR_COMPLETE_EVIDENCE_OR_MANUAL_HOLD_MATERIAL_REF
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op07_manual_decision_materialization_contract(material)
    _assert_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("auto_executes_dmd", True),
        ("auto_executes_r52", True),
        ("auto_starts_actual_review", True),
        ("auto_starts_p8", True),
        ("release_allowed", True),
        ("manual_decision_auto_executes_downstream", True),
        ("selected_branch_ref", dhr.P7_R54_AHR_POST_ELR19_DHR_BRANCH_DMD_HANDOFF_READY_MANUAL_DECISION_REQUIRED_NO_AUTO_EXECUTION_REF),
        ("recommended_next_step_ref", "p8_question_design_start"),
    ],
)
def test_dhr_op07_contract_rejects_manual_material_promotion_mutations(field: str, bad_value: object) -> None:
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op07_manual_decision_materialization(
        handoff_or_retry_deterministic_branch_resolver=_op06_retry_or_start_branch(),
    )
    material[field] = bad_value
    with pytest.raises(ValueError):
        dhr.assert_p7_r54_ahr_post_elr19_dhr_op07_manual_decision_materialization_contract(material)


def test_dhr_op06_op07_full_title_aliases_match_canonical_builders_and_asserts() -> None:
    op05 = _op05_retry_or_start_preflight()
    canonical_op06 = dhr.build_p7_r54_ahr_post_elr19_dhr_op06_handoff_or_retry_deterministic_branch_resolver(
        bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan=op05,
    )
    alias_op06 = dhr.build_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op06_handoff_or_retry_deterministic_branch_resolver(
        bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan=op05,
    )
    assert canonical_op06 == alias_op06
    assert dhr.assert_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op06_handoff_or_retry_deterministic_branch_resolver_contract(alias_op06)

    canonical_op07 = dhr.build_p7_r54_ahr_post_elr19_dhr_op07_manual_decision_materialization(
        handoff_or_retry_deterministic_branch_resolver=canonical_op06,
    )
    alias_op07 = dhr.build_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op07_manual_decision_materialization(
        handoff_or_retry_deterministic_branch_resolver=canonical_op06,
    )
    assert canonical_op07 == alias_op07
    assert dhr.assert_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op07_manual_decision_materialization_contract(alias_op07)
