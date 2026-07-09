# -*- coding: utf-8 -*-
"""R54-AHR Post-PNT closed material next boundary confirmation PCM-OP04/OP05 tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_20260707 as pcm
from r54_ahr_post_pnt_pcm_compact_pnt_op08_fixture_20260708 import (
    compact_closed_pnt_op08_for_pcm_regression,
)


PCM_R4_FORBIDDEN_EXECUTION_KEYS = (
    "pnt_op08_default_builder_called_here",
    "pnt_op08_default_material_synthesized_here",
    "pnt_op08_builder_called_here",
    "pnt_op08_material_synthesized_here",
    "pnt_r11_decision_table_used_as_single_lane_here",
    "selected_post_nci_next_boundary_executed_here",
    "selected_pcm_next_boundary_executed_here",
    "selected_pcm_next_boundary_execution_allowed_here",
    "execution_allowed_here",
    "dhr_op05_called_here",
    "dhr_op05_builder_called_here",
    "dhr_op06_called_here",
    "dhr_op07_materialized_here",
    "dmd_execution_started_here",
    "r52_actual_execution_started_here",
    "actual_body_full_packet_generated_here",
    "actual_review_started_here",
    "actual_rows_created_here",
    "actual_question_need_observation_rows_created_here",
    "actual_disposal_or_purge_executed_here",
    "raw_evidence_request_created_here",
    "repair_executed_here",
    "p8_start_allowed",
    "p8_question_design_started",
    "p8_question_implementation_started",
    "question_text_materialized",
    "api_changed",
    "db_changed",
    "rn_changed",
    "runtime_changed",
    "response_key_changed",
    "json_schema_file_created_here",
    "p7_complete",
    "release_allowed",
    "full_backend_suite_green_confirmed",
    "rn_contract_green_confirmed",
    "rn_real_device_modal_verified_claimed_here",
)


PCM_R4_SIX_LANE_EXPECTED_LANE_REFS = (
    pcm.P7_R54_AHR_POST_PNT_PCM_LANE_DHR_OP05_MANUAL_HANDOFF_BOUNDARY_DESIGN_CANDIDATE_REF,
    pcm.P7_R54_AHR_POST_PNT_PCM_LANE_RETRY_OR_START_ACTUAL_LOCAL_ONLY_REVIEW_ROUTE_CANDIDATE_REF,
    pcm.P7_R54_AHR_POST_PNT_PCM_LANE_WAIT_EXTERNAL_BODYFREE_CLAIM_REINTAKE_CANDIDATE_REF,
    pcm.P7_R54_AHR_POST_PNT_PCM_LANE_REPAIR_RDB_CANDIDATE_OR_UPSTREAM_RESULT_CANDIDATE_REF,
    pcm.P7_R54_AHR_POST_PNT_PCM_LANE_MANUAL_HOLD_UNRESOLVED_POST_RDB08_CANDIDATE_REF,
    pcm.P7_R54_AHR_POST_PNT_PCM_LANE_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_CANDIDATE_REF,
)


PCM_R4_EXPECTED_NEXT_WORK_CLASS_REFS = (
    pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_NEXT_DESIGN_CANDIDATE_REF,
    pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_NEXT_DESIGN_CANDIDATE_REF,
    pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_WAIT_HOLD_REF,
    pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_NEXT_DESIGN_CANDIDATE_REF,
    pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_STOP_REF,
    pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_STOP_REF,
)


def _closed_pnt_op08(index: int = 0) -> dict[str, object]:
    return compact_closed_pnt_op08_for_pcm_regression(index)


def _pcm_op01_from_closed(index: int = 0) -> dict[str, object]:
    return pcm.build_p7_r54_ahr_post_pnt_pcm_op01_explicit_closed_pnt_op08_material_intake(
        pnt_op08_bodyfree_result_memo_closure_material=_closed_pnt_op08(index),
    )


def _pcm_op02_from_closed(index: int = 0) -> dict[str, object]:
    op01 = _pcm_op01_from_closed(index)
    return pcm.build_p7_r54_ahr_post_pnt_pcm_op02_closed_material_contract_validation(op01)


def _pcm_op03_from_closed(index: int = 0) -> dict[str, object]:
    op02 = _pcm_op02_from_closed(index)
    return pcm.build_p7_r54_ahr_post_pnt_pcm_op03_single_selected_lane_confirmation(op02)


def _pcm_op04_from_closed(index: int = 0) -> dict[str, object]:
    op03 = _pcm_op03_from_closed(index)
    return pcm.build_p7_r54_ahr_post_pnt_pcm_op04_next_work_class_resolver(op03)


def _assert_pcm_r4_no_downstream_execution(material: dict[str, object]) -> None:
    for key in PCM_R4_FORBIDDEN_EXECUTION_KEYS:
        if key in material:
            assert material[key] is False, key
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["body_free"] is True
    assert material["dhr_op05_call_allowed_here"] is False
    assert material["dhr_op05_builder_call_allowed_here"] is False
    assert material["actual_review_start_allowed_here"] is False
    assert material["repair_execution_allowed_here"] is False
    assert material["p8_question_design_allowed_here"] is False
    assert material["api_db_rn_response_key_change_allowed_here"] is False
    assert material["json_schema_file_creation_allowed_here"] is False


@pytest.mark.parametrize(
    ("case_index", "expected_lane", "expected_next_work_class"),
    [
        (index, lane, next_work_class)
        for index, (lane, next_work_class) in enumerate(zip(PCM_R4_SIX_LANE_EXPECTED_LANE_REFS, PCM_R4_EXPECTED_NEXT_WORK_CLASS_REFS))
    ],
    ids=["dhr", "retry", "wait", "repair", "unresolved", "blocked"],
)
def test_pcm_op04_resolves_each_confirmed_single_lane_to_next_work_class_without_execution(
    case_index: int,
    expected_lane: str,
    expected_next_work_class: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    op03 = _pcm_op03_from_closed(case_index)

    def _unexpected_pnt_op08_builder_call(*_args: object, **_kwargs: object) -> dict[str, object]:
        raise AssertionError("PCM-OP04 must not synthesize PNT-OP08 material")

    monkeypatch.setattr(
        pcm.pnt,
        "build_p7_r54_ahr_post_nci_pnt_op08_bodyfree_post_nci_triage_result_memo_closure",
        _unexpected_pnt_op08_builder_call,
    )

    op04 = pcm.build_p7_r54_ahr_post_pnt_pcm_op04_next_work_class_resolver(op03)

    assert pcm.assert_p7_r54_ahr_post_pnt_pcm_op04_next_work_class_resolver_contract(op04) is True
    assert op04["pcm_op04_status_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_OP04_STATUS_NEXT_WORK_CLASS_RESOLVED_STOPPED_REF
    assert op04["selected_pnt_lane_ref"] == expected_lane
    assert op04["selected_pcm_next_work_class_ref"] == expected_next_work_class
    assert op04["selected_pcm_next_work_class_ref_allowed"] is True
    assert op04["selected_pcm_next_boundary_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_LANE_TO_SELECTED_PCM_NEXT_BOUNDARY_REF_MAP[expected_lane]
    assert op04["selected_pcm_next_boundary_kind_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_LANE_TO_SELECTED_PCM_NEXT_BOUNDARY_KIND_REF_MAP[expected_lane]
    assert op04["selected_pcm_next_boundary_not_executed"] is True
    assert op04["next_required_step"] == pcm.P7_R54_AHR_POST_PNT_PCM_OP05_STEP_REF
    assert op04["pcm_op04_next_work_class_resolved_stopped"] is True
    assert op04["pcm_op04_blocker_refs"] == []
    _assert_pcm_r4_no_downstream_execution(op04)


@pytest.mark.parametrize(
    ("case_index", "expected_lane", "expected_next_work_class"),
    [
        (index, lane, next_work_class)
        for index, (lane, next_work_class) in enumerate(zip(PCM_R4_SIX_LANE_EXPECTED_LANE_REFS, PCM_R4_EXPECTED_NEXT_WORK_CLASS_REFS))
    ],
    ids=["dhr", "retry", "wait", "repair", "unresolved", "blocked"],
)
def test_pcm_op05_materializes_next_design_wait_or_stop_envelope_without_downstream_execution(
    case_index: int,
    expected_lane: str,
    expected_next_work_class: str,
) -> None:
    op04 = _pcm_op04_from_closed(case_index)

    op05 = pcm.build_p7_r54_ahr_post_pnt_pcm_op05_next_design_candidate_envelope_materialization(op04)

    assert pcm.assert_p7_r54_ahr_post_pnt_pcm_op05_next_design_candidate_envelope_materialization_contract(op05) is True
    assert op05["selected_pnt_lane_ref"] == expected_lane
    assert op05["selected_pcm_next_work_class_ref"] == expected_next_work_class
    assert op05["selected_pcm_next_boundary_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_LANE_TO_SELECTED_PCM_NEXT_BOUNDARY_REF_MAP[expected_lane]
    assert op05["selected_pcm_next_boundary_not_executed"] is True
    assert op05["next_required_step"] == pcm.P7_R54_AHR_POST_PNT_PCM_OP06_STEP_REF
    assert op05["pcm_op05_blocker_refs"] == []
    if expected_next_work_class == pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_NEXT_DESIGN_CANDIDATE_REF:
        assert op05["pcm_op05_status_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_OP05_STATUS_NEXT_DESIGN_CANDIDATE_ENVELOPE_MATERIALIZED_STOPPED_REF
        assert op05["next_design_document_allowed"] is True
        assert op05["manual_wait_required"] is False
        assert op05["manual_stop_required"] is False
    elif expected_next_work_class == pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_WAIT_HOLD_REF:
        assert op05["pcm_op05_status_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_OP05_STATUS_WAIT_HOLD_ENVELOPE_MATERIALIZED_STOPPED_REF
        assert op05["next_design_document_allowed"] is False
        assert op05["manual_wait_required"] is True
        assert op05["manual_stop_required"] is False
        assert op05["pcm_op05_wait_hold_envelope_materialized_without_raw_evidence"] is True
    else:
        assert op05["pcm_op05_status_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_OP05_STATUS_STOP_ENVELOPE_MATERIALIZED_STOPPED_REF
        assert op05["next_design_document_allowed"] is False
        assert op05["manual_wait_required"] is False
        assert op05["manual_stop_required"] is True
        assert op05["pcm_op05_stop_envelope_materialized_without_next_design_promotion"] is True
    _assert_pcm_r4_no_downstream_execution(op05)


def test_pcm_op05_dhr_op05_lane_materializes_design_candidate_without_dhr_call() -> None:
    op05 = pcm.build_p7_r54_ahr_post_pnt_pcm_op05_next_design_candidate_envelope_materialization(_pcm_op04_from_closed(0))

    assert pcm.assert_p7_r54_ahr_post_pnt_pcm_op05_next_design_candidate_envelope_materialization_contract(op05) is True
    assert op05["selected_pnt_lane_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_LANE_DHR_OP05_MANUAL_HANDOFF_BOUNDARY_DESIGN_CANDIDATE_REF
    assert op05["selected_pcm_next_boundary_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_SELECTED_NEXT_BOUNDARY_DHR_OP05_PREFLIGHT_DESIGN_WITHOUT_CALL_REF
    assert op05["next_design_document_candidate_ref"] == pcm.pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_NEXT_DESIGN_DOCUMENT_CANDIDATE_REF_MAP[op05["selected_pnt_lane_ref"]]
    assert op05["pcm_op05_dhr_op05_design_candidate_envelope_materialized_without_call"] is True
    assert op05["dhr_op05_call_allowed_here"] is False
    assert op05["dhr_op05_builder_call_allowed_here"] is False
    _assert_pcm_r4_no_downstream_execution(op05)


def test_pcm_op05_retry_start_lane_materializes_candidate_without_actual_review_start() -> None:
    op05 = pcm.build_p7_r54_ahr_post_pnt_pcm_op05_next_design_candidate_envelope_materialization(_pcm_op04_from_closed(1))

    assert pcm.assert_p7_r54_ahr_post_pnt_pcm_op05_next_design_candidate_envelope_materialization_contract(op05) is True
    assert op05["pcm_op05_retry_start_design_candidate_envelope_materialized_without_actual_review"] is True
    assert op05["actual_review_start_allowed_here"] is False
    assert op05["selected_pcm_next_boundary_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_SELECTED_NEXT_BOUNDARY_ACTUAL_LOCAL_ONLY_REVIEW_RETRY_START_DESIGN_WITHOUT_EXECUTION_REF
    _assert_pcm_r4_no_downstream_execution(op05)


def test_pcm_op05_repair_lane_materializes_candidate_without_repair_execution() -> None:
    op05 = pcm.build_p7_r54_ahr_post_pnt_pcm_op05_next_design_candidate_envelope_materialization(_pcm_op04_from_closed(3))

    assert pcm.assert_p7_r54_ahr_post_pnt_pcm_op05_next_design_candidate_envelope_materialization_contract(op05) is True
    assert op05["pcm_op05_repair_design_candidate_envelope_materialized_without_repair_execution"] is True
    assert op05["repair_design_candidate"] is True
    assert op05["repair_execution_allowed_here"] is False
    assert op05["selected_pcm_next_boundary_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_SELECTED_NEXT_BOUNDARY_RDB_OR_UPSTREAM_REPAIR_DESIGN_WITHOUT_EXECUTION_REF
    _assert_pcm_r4_no_downstream_execution(op05)


@pytest.mark.parametrize(
    ("mutation_key", "mutation_value", "expected_blocker"),
    [
        ("question_text", "blocked_question", "op04_input_forbidden_payload_key_detected"),
        ("dhr_op05_called_here", True, "op04_input_promotion_or_autorun_claim_detected"),
        ("api_changed", True, "op04_input_promotion_or_autorun_claim_detected"),
        ("response_key_changed", True, "op04_input_promotion_or_autorun_claim_detected"),
    ],
)
def test_pcm_op04_blocks_dhr_p8_release_api_db_rn_or_body_payload_claims(
    mutation_key: str,
    mutation_value: object,
    expected_blocker: str,
) -> None:
    op03 = _pcm_op03_from_closed()
    op03[mutation_key] = mutation_value

    op04 = pcm.build_p7_r54_ahr_post_pnt_pcm_op04_next_work_class_resolver(op03)

    assert pcm.assert_p7_r54_ahr_post_pnt_pcm_op04_next_work_class_resolver_contract(op04) is True
    assert op04["pcm_op04_status_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_OP04_STATUS_BLOCKED_NEXT_WORK_CLASS_PROMOTION_AUTORUN_REF
    assert expected_blocker in op04["pcm_op04_blocker_refs"]
    assert op04["next_required_step"] == pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_BLOCKED_NEXT_WORK_CLASS_RESOLVER_REF
    _assert_pcm_r4_no_downstream_execution(op04)


@pytest.mark.parametrize(
    ("mutation_key", "mutation_value", "expected_blocker"),
    [
        ("body_full_packet", {"unsafe": True}, "op05_input_forbidden_payload_key_detected"),
        ("p8_question_design_started", True, "op05_input_promotion_or_autorun_claim_detected"),
        ("release_allowed", True, "op05_input_promotion_or_autorun_claim_detected"),
        ("db_changed", True, "op05_input_promotion_or_autorun_claim_detected"),
    ],
)
def test_pcm_op05_blocks_dhr_p8_release_api_db_rn_or_body_payload_claims(
    mutation_key: str,
    mutation_value: object,
    expected_blocker: str,
) -> None:
    op04 = _pcm_op04_from_closed()
    op04[mutation_key] = mutation_value

    op05 = pcm.build_p7_r54_ahr_post_pnt_pcm_op05_next_design_candidate_envelope_materialization(op04)

    assert pcm.assert_p7_r54_ahr_post_pnt_pcm_op05_next_design_candidate_envelope_materialization_contract(op05) is True
    assert op05["pcm_op05_status_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_OP05_STATUS_BLOCKED_NEXT_WORK_CLASS_PROMOTION_AUTORUN_REF
    assert expected_blocker in op05["pcm_op05_blocker_refs"]
    assert op05["next_required_step"] == pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_BLOCKED_NEXT_DESIGN_CANDIDATE_ENVELOPE_REF
    _assert_pcm_r4_no_downstream_execution(op05)


def test_pcm_op04_repairs_missing_or_unconfirmed_op03_material_without_lane_synthesis() -> None:
    missing = pcm.build_p7_r54_ahr_post_pnt_pcm_op04_next_work_class_resolver()
    assert pcm.assert_p7_r54_ahr_post_pnt_pcm_op04_next_work_class_resolver_contract(missing) is True
    assert missing["pcm_op04_status_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_OP04_STATUS_REPAIR_REQUIRED_FOR_NEXT_WORK_CLASS_INPUTS_REF
    assert "pcm_op03_single_selected_lane_confirmation_material_missing" in missing["pcm_op04_blocker_refs"]
    assert missing["selected_pnt_lane_ref"] == "missing"
    assert missing["next_required_step"] == pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_REPAIR_NEXT_WORK_CLASS_INPUTS_REF
    _assert_pcm_r4_no_downstream_execution(missing)

    op03 = deepcopy(_pcm_op03_from_closed())
    op03["single_selected_pnt_lane_confirmed"] = False
    op04 = pcm.build_p7_r54_ahr_post_pnt_pcm_op04_next_work_class_resolver(op03)
    assert pcm.assert_p7_r54_ahr_post_pnt_pcm_op04_next_work_class_resolver_contract(op04) is True
    assert op04["pcm_op04_status_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_OP04_STATUS_REPAIR_REQUIRED_FOR_NEXT_WORK_CLASS_INPUTS_REF
    assert "pcm_op03_single_selected_lane_confirmation_contract_invalid" in op04["pcm_op04_blocker_refs"]
    assert op04["selected_pnt_lane_ref"] == "missing"
    _assert_pcm_r4_no_downstream_execution(op04)


def test_pcm_op05_repairs_missing_or_unresolved_op04_material_without_envelope_synthesis() -> None:
    missing = pcm.build_p7_r54_ahr_post_pnt_pcm_op05_next_design_candidate_envelope_materialization()
    assert pcm.assert_p7_r54_ahr_post_pnt_pcm_op05_next_design_candidate_envelope_materialization_contract(missing) is True
    assert missing["pcm_op05_status_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_OP05_STATUS_REPAIR_REQUIRED_FOR_NEXT_WORK_CLASS_INPUTS_REF
    assert "pcm_op04_next_work_class_resolver_material_missing" in missing["pcm_op05_blocker_refs"]
    assert missing["selected_pnt_lane_ref"] == "missing"
    assert missing["next_required_step"] == pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_REPAIR_NEXT_DESIGN_CANDIDATE_ENVELOPE_INPUTS_REF
    _assert_pcm_r4_no_downstream_execution(missing)

    op04 = deepcopy(_pcm_op04_from_closed())
    op04["selected_pcm_next_work_class_ref"] = "unknown"
    op05 = pcm.build_p7_r54_ahr_post_pnt_pcm_op05_next_design_candidate_envelope_materialization(op04)
    assert pcm.assert_p7_r54_ahr_post_pnt_pcm_op05_next_design_candidate_envelope_materialization_contract(op05) is True
    assert op05["pcm_op05_status_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_OP05_STATUS_REPAIR_REQUIRED_FOR_NEXT_WORK_CLASS_INPUTS_REF
    assert "pcm_op04_next_work_class_resolver_contract_invalid" in op05["pcm_op05_blocker_refs"]
    assert op05["selected_pnt_lane_ref"] == "missing"
    _assert_pcm_r4_no_downstream_execution(op05)


def test_pcm_op04_op05_full_title_aliases_match_short_builders_and_asserts() -> None:
    op03 = _pcm_op03_from_closed()
    op04_short = pcm.build_p7_r54_ahr_post_pnt_pcm_op04_next_work_class_resolver(op03)
    op04_alias = pcm.build_p7_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op04_next_work_class_resolver(op03)
    assert op04_short == op04_alias
    assert pcm.assert_p7_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op04_next_work_class_resolver_contract(op04_alias) is True

    op05_short = pcm.build_p7_r54_ahr_post_pnt_pcm_op05_next_design_candidate_envelope_materialization(op04_short)
    op05_alias = pcm.build_p7_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op05_next_design_candidate_envelope_materialization(op04_short)
    assert op05_short == op05_alias
    assert pcm.assert_p7_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op05_next_design_candidate_envelope_materialization_contract(op05_alias) is True
