# -*- coding: utf-8 -*-
"""R54-AHR Post-NCI selected handoff-or-stop decision triage PNT-OP04/OP05 tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_20260707 as pnt
from test_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op02_op03_20260707 import (
    PNT_R3_FORBIDDEN_EXECUTION_KEYS,
    _pnt_op02_from_nci_op08,
    _six_lane_cases,
)


PNT_R4_FORBIDDEN_EXECUTION_KEYS = (
    *PNT_R3_FORBIDDEN_EXECUTION_KEYS,
    "selected_post_nci_next_boundary_executed_here",
)


def _op03_from_nci_op08(nci_op08: dict[str, object]) -> dict[str, object]:
    op02 = _pnt_op02_from_nci_op08(nci_op08)
    return pnt.build_p7_r54_ahr_post_nci_pnt_op03_selected_handoff_or_stop_lane_consistency_resolver(op02)


def _op04_from_nci_op08(nci_op08: dict[str, object]) -> dict[str, object]:
    return pnt.build_p7_r54_ahr_post_nci_pnt_op04_next_boundary_selection_materialization(
        _op03_from_nci_op08(nci_op08),
    )


def _assert_r4_no_downstream_execution(material: dict[str, object]) -> None:
    for key in PNT_R4_FORBIDDEN_EXECUTION_KEYS:
        assert material[key] is False, key
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["body_free"] is True


@pytest.mark.parametrize(
    ("nci_op08", "expected_lane", "expected_ref", "_expected_kind", "_expected_status", "_expected_flag"),
    _six_lane_cases(),
)
def test_pnt_op04_materializes_all_six_next_boundary_or_stop_outcomes_without_execution(
    nci_op08: dict[str, object],
    expected_lane: str,
    expected_ref: str,
    _expected_kind: str,
    _expected_status: str,
    _expected_flag: str,
) -> None:
    op04 = _op04_from_nci_op08(nci_op08)

    assert pnt.assert_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op04_next_boundary_selection_materialization_contract(op04) is True
    expected_group = pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_OUTCOME_GROUP_REF_MAP[expected_lane]
    expected_kind = pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_NEXT_DESIGN_OR_STOP_KIND_REF_MAP[expected_lane]
    assert op04["selected_pnt_lane_ref"] == expected_lane
    assert op04["selected_post_nci_outcome_group_ref"] == expected_group
    assert op04["selected_post_nci_next_boundary_ref"] == expected_ref
    assert op04["selected_post_nci_next_boundary_kind_ref"] == expected_kind
    assert op04["selected_post_nci_next_boundary_not_executed"] is True
    assert op04["selected_post_nci_next_boundary_execution_allowed_here"] is False
    assert op04["selected_post_nci_next_boundary_materialized_here"] is True
    assert op04["next_design_document_candidate_ref"] == pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_NEXT_DESIGN_DOCUMENT_CANDIDATE_REF_MAP[expected_lane]
    assert op04["next_design_document_allowed"] is pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_NEXT_DESIGN_DOCUMENT_ALLOWED_MAP[expected_lane]
    assert op04["manual_wait_required"] is pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_MANUAL_WAIT_REQUIRED_MAP[expected_lane]
    assert op04["manual_stop_required"] is pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_MANUAL_STOP_REQUIRED_MAP[expected_lane]
    assert op04["repair_design_candidate"] is pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_REPAIR_DESIGN_CANDIDATE_MAP[expected_lane]
    assert op04["next_required_step"] == pnt.P7_R54_AHR_POST_NCI_PNT_OP05_STEP_REF
    assert op04["pnt_op04_blocker_refs"] == []
    _assert_r4_no_downstream_execution(op04)


@pytest.mark.parametrize(
    ("nci_op08", "expected_lane", "expected_ref", "_expected_kind", "_expected_status", "_expected_flag"),
    _six_lane_cases(),
)
def test_pnt_op05_passes_bodyfree_no_touch_guard_for_all_valid_op04_outcomes(
    nci_op08: dict[str, object],
    expected_lane: str,
    expected_ref: str,
    _expected_kind: str,
    _expected_status: str,
    _expected_flag: str,
) -> None:
    op04 = _op04_from_nci_op08(nci_op08)
    op05 = pnt.build_p7_r54_ahr_post_nci_pnt_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard(op04)

    assert pnt.assert_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard_contract(op05) is True
    assert op05["pnt_op05_status_ref"] == pnt.P7_R54_AHR_POST_NCI_PNT_OP05_STATUS_GUARD_PASSED_REF
    assert op05["pnt_op05_guard_passed"] is True
    assert op05["selected_post_nci_next_boundary_ref"] == expected_ref
    assert op05["selected_post_nci_outcome_group_ref"] == pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_OUTCOME_GROUP_REF_MAP[expected_lane]
    assert op05["selected_post_nci_next_boundary_not_executed"] is True
    assert op05["selected_post_nci_next_boundary_execution_allowed_here"] is False
    assert op05["next_design_document_allowed"] is pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_NEXT_DESIGN_DOCUMENT_ALLOWED_MAP[expected_lane]
    assert op05["manual_wait_required"] is pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_MANUAL_WAIT_REQUIRED_MAP[expected_lane]
    assert op05["manual_stop_required"] is pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_MANUAL_STOP_REQUIRED_MAP[expected_lane]
    assert op05["repair_design_candidate"] is pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_REPAIR_DESIGN_CANDIDATE_MAP[expected_lane]
    assert op05["next_required_step"] == pnt.P7_R54_AHR_POST_NCI_PNT_OP06_STEP_REF
    assert op05["pnt_op05_blocker_refs"] == []
    _assert_r4_no_downstream_execution(op05)


def test_pnt_op04_repairs_when_op03_lane_is_not_resolved_for_next_boundary_selection() -> None:
    op03 = _op03_from_nci_op08(_six_lane_cases()[0][0])
    mutated = deepcopy(op03)
    mutated["selected_pnt_lane_resolved"] = False
    mutated["pnt_op03_blocker_refs"] = ["manual_test_unresolved_lane"]
    mutated["pnt_op03_blocker_ref_count"] = 1

    op04 = pnt.build_p7_r54_ahr_post_nci_pnt_op04_next_boundary_selection_materialization(mutated)

    assert pnt.assert_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op04_next_boundary_selection_materialization_contract(op04) is True
    assert op04["pnt_op04_status_ref"] == pnt.P7_R54_AHR_POST_NCI_PNT_OP04_STATUS_REPAIR_REQUIRED_REF
    assert "pnt_op03_lane_resolver_contract_invalid" in op04["pnt_op04_blocker_refs"]
    assert op04["selected_post_nci_next_boundary_materialized_here"] is False
    assert op04["next_required_step"] == pnt.P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_REPAIR_NEXT_BOUNDARY_SELECTION_REF
    _assert_r4_no_downstream_execution(op04)


@pytest.mark.parametrize(
    ("mutation_key", "mutation_value", "expected_blocker"),
    [
        ("dhr_op05_called_here", True, "op04_input_promotion_or_autorun_claim_detected"),
        ("p8_question_design_started", True, "op04_input_promotion_or_autorun_claim_detected"),
        ("api_changed", True, "op04_input_api_db_rn_runtime_response_key_or_p8_question_touch_detected"),
        ("question_text", "blocked_question", "op04_input_forbidden_payload_key_detected"),
        ("raw_input", "blocked_raw_input", "op04_input_forbidden_payload_key_detected"),
    ],
)
def test_pnt_op04_blocks_body_leak_promotion_and_no_touch_mutation_before_guard(
    mutation_key: str,
    mutation_value: object,
    expected_blocker: str,
) -> None:
    op03 = _op03_from_nci_op08(_six_lane_cases()[0][0])
    mutated = deepcopy(op03)
    mutated[mutation_key] = mutation_value

    op04 = pnt.build_p7_r54_ahr_post_nci_pnt_op04_next_boundary_selection_materialization(mutated)

    assert pnt.assert_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op04_next_boundary_selection_materialization_contract(op04) is True
    assert op04["pnt_op04_status_ref"] == pnt.P7_R54_AHR_POST_NCI_PNT_OP04_STATUS_BLOCKED_PROMOTION_AUTORUN_REF
    assert expected_blocker in op04["pnt_op04_blocker_refs"]
    assert op04["selected_post_nci_next_boundary_materialized_here"] is False
    assert op04["next_required_step"] == pnt.P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_BLOCKED_NEXT_BOUNDARY_SELECTION_REF
    _assert_r4_no_downstream_execution(op04)


@pytest.mark.parametrize(
    ("mutation_key", "mutation_value", "expected_blocker"),
    [
        ("question_text", "blocked_question", "op05_guard_forbidden_payload_key_detected"),
        ("raw_evidence", "blocked_raw_evidence", "op05_guard_forbidden_payload_key_detected"),
        ("local_path", "/tmp/not_allowed", "op05_guard_forbidden_payload_key_detected"),
        ("hash", "blocked_hash", "op05_guard_forbidden_payload_key_detected"),
        ("stdout", "terminal body leak", "op05_guard_body_like_value_detected"),
        ("selected_post_nci_next_boundary_execution_allowed_here", True, "op05_guard_promotion_or_autorun_claim_detected"),
        ("dhr_op05_called_here", True, "op05_guard_promotion_or_autorun_claim_detected"),
        ("actual_review_start_allowed_here", True, "op05_guard_promotion_or_autorun_claim_detected"),
        ("raw_evidence_request_allowed_here", True, "op05_guard_promotion_or_autorun_claim_detected"),
        ("p8_question_design_started", True, "op05_guard_promotion_or_autorun_claim_detected"),
        ("release_allowed", True, "op05_guard_promotion_or_autorun_claim_detected"),
        ("api_changed", True, "op05_guard_api_db_rn_runtime_response_key_or_p8_question_touch_detected"),
        ("db_changed", True, "op05_guard_api_db_rn_runtime_response_key_or_p8_question_touch_detected"),
        ("rn_changed", True, "op05_guard_api_db_rn_runtime_response_key_or_p8_question_touch_detected"),
        ("response_key_changed", True, "op05_guard_api_db_rn_runtime_response_key_or_p8_question_touch_detected"),
    ],
)
def test_pnt_op05_blocks_body_payload_dhr_p8_release_api_db_rn_response_key_and_execution_claims(
    mutation_key: str,
    mutation_value: object,
    expected_blocker: str,
) -> None:
    op04 = _op04_from_nci_op08(_six_lane_cases()[0][0])
    mutated = deepcopy(op04)
    mutated[mutation_key] = mutation_value

    op05 = pnt.build_p7_r54_ahr_post_nci_pnt_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard(mutated)

    assert pnt.assert_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard_contract(op05) is True
    assert op05["pnt_op05_status_ref"] == pnt.P7_R54_AHR_POST_NCI_PNT_OP05_STATUS_BLOCKED_REF
    assert expected_blocker in op05["pnt_op05_blocker_refs"]
    assert op05["next_required_step"] == pnt.P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_BLOCKED_OP05_GUARD_REF
    _assert_r4_no_downstream_execution(op05)


def test_pnt_op05_repairs_when_op04_material_is_missing_or_not_selection_ready() -> None:
    missing = pnt.build_p7_r54_ahr_post_nci_pnt_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard(None)

    assert pnt.assert_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard_contract(missing) is True
    assert missing["pnt_op05_status_ref"] == pnt.P7_R54_AHR_POST_NCI_PNT_OP05_STATUS_REPAIR_REQUIRED_REF
    assert "pnt_op04_next_boundary_selection_material_missing" in missing["pnt_op05_blocker_refs"]
    assert missing["next_required_step"] == pnt.P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_REPAIR_OP05_GUARD_INPUTS_REF
    _assert_r4_no_downstream_execution(missing)


def test_pnt_op04_op05_full_title_aliases_match_short_builders_and_asserts() -> None:
    assert (
        pnt.build_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op04_next_boundary_selection_materialization
        is pnt.build_p7_r54_ahr_post_nci_pnt_op04_next_boundary_selection_materialization
    )
    assert (
        pnt.assert_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op04_next_boundary_selection_materialization_contract
        is pnt.assert_p7_r54_ahr_post_nci_pnt_op04_next_boundary_selection_materialization_contract
    )
    assert (
        pnt.build_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard
        is pnt.build_p7_r54_ahr_post_nci_pnt_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard
    )
    assert (
        pnt.assert_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard_contract
        is pnt.assert_p7_r54_ahr_post_nci_pnt_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard_contract
    )
