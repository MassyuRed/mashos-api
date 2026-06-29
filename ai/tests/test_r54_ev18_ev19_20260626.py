# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from copy import deepcopy

import pytest

import emlis_ai_p7_r54_actual_local_review_operation_reentry_20260625 as r54op
import emlis_ai_p7_r54_actual_review_execution_evidence_materialization_20260626 as ev
import test_r54_ev12_ev13_20260626 as prev12
import test_r54_ev16_ev17_20260626 as prev17


FORBIDDEN_DUMP_TOKENS = (
    '"raw_input":',
    '"raw_answer":',
    '"comment_text":',
    '"comment_text_body":',
    '"returned_emlis_surface":',
    '"current_input_review_surface":',
    '"bounded_owned_history_review_surface":',
    '"reviewer_free_text":',
    '"reviewer_note":',
    '"reviewer_notes":',
    '"question_text": "',
    '"draft_question_text": "',
    '"question_body":',
    '"local_absolute_path":',
    '"body_content_hash":',
    '"packet_content_hash":',
    '"terminal_output": "',
    '"stdout":',
    '"stderr":',
    '"traceback":',
)
FORBIDDEN_TRUE_TOKENS = (
    '"api_changed": true',
    '"db_changed": true',
    '"rn_changed": true',
    '"runtime_changed": true',
    '"api_route_changed": true',
    '"db_schema_changed": true',
    '"rn_visible_contract_changed": true',
    '"public_response_top_level_key_added": true',
    '"release_allowed": true',
    '"p7_complete": true',
    '"p8_start_allowed": true',
    '"p6_limited_human_readfeel_start_allowed": true',
    '"question_trigger_logic_implemented": true',
    '"question_api_implemented": true',
    '"question_db_schema_implemented": true',
    '"question_rn_ui_implemented": true',
    '"question_response_key_implemented": true',
    '"question_storage_schema_implemented": true',
    '"question_answer_persistence_implemented": true',
    '"question_plan_guard_implemented": true',
    '"question_text_materialized_here": true',
    '"draft_question_text_materialized_here": true',
    '"p8_question_implementation_spec_finalized_here": true',
    '"actual_human_review_run_here": true',
    '"actual_manual_review_run_here": true',
    '"body_full_packet_generated_here": true',
    '"actual_review_evidence_complete": true',
    '"p5_human_blind_qa_confirmed_final": true',
    '"existing_op20_reused_as_actual_p6_candidate_basis": true',
    '"existing_op20_reused_as_actual_p6_candidate_handoff_basis": true',
    '"existing_op21_reused_as_actual_p8_material_basis": true',
    '"existing_op21_reused_as_actual_p8_material_handoff_basis": true',
)


def _assert_ev18_ev19_body_free_no_promotion(
    material: dict[str, object],
    *,
    allow_actual_rows_and_disposal: bool = True,
    allow_p5_candidate: bool = True,
    allow_p6_candidate: bool = False,
    allow_p8_material_candidate: bool = False,
) -> None:
    dumped = json.dumps(material, ensure_ascii=False, sort_keys=True).lower()
    for forbidden in FORBIDDEN_DUMP_TOKENS:
        assert forbidden not in dumped
    for forbidden in FORBIDDEN_TRUE_TOKENS:
        assert forbidden not in dumped
    if not allow_actual_rows_and_disposal:
        assert '"actual_rating_rows_materialized_here": true' not in dumped
        assert '"actual_blocker_rows_materialized_here": true' not in dumped
        assert '"actual_question_need_observation_rows_materialized_here": true' not in dumped
        assert '"actual_disposal_receipt_materialized_here": true' not in dumped
        assert '"disposal_verified": true' not in dumped
    if not allow_p5_candidate:
        assert '"p5_human_blind_qa_confirmed_candidate": true' not in dumped
    if not allow_p6_candidate:
        assert '"p6_limited_human_readfeel_candidate": true' not in dumped
    if not allow_p8_material_candidate:
        assert '"p8_question_design_material_candidate": true' not in dumped


def _rows_with_p8_material_candidate() -> list[dict[str, object]]:
    rows = prev12._selection_rows()
    rows[0] = dict(rows[0])
    rows[0]["question_need_primary_class"] = "plus_single_question_candidate_later"
    rows[0]["ambiguity_kind_refs"] = ["missing_target"]
    rows[0]["one_question_fit_ref"] = "fits_one_question"
    rows[0]["repair_required_refs"] = ["no_repair_required"]
    rows[0]["plan_candidate_flags"] = {
        "plus_single_question_candidate_later": True,
        "premium_deep_dive_candidate_later": False,
        "p8_design_material_candidate": True,
        "p8_implementation_spec_finalized_here": False,
    }
    return rows


def _rows_with_yellow_first_row() -> list[dict[str, object]]:
    rows = prev12._selection_rows()
    rows[0] = dict(rows[0])
    rows[0]["axis_scores"] = {axis: 0.75 for axis in ev.P7_R54_EV08_RATING_AXIS_REFS}
    rows[0]["verdict"] = "YELLOW"
    rows[0]["sanitized_reason_ids"] = ["yellow_fixture_selection_only"]
    rows[0]["question_need_primary_class"] = "question_may_reduce_overread_risk"
    rows[0]["ambiguity_kind_refs"] = ["history_connection_basis_unclear"]
    rows[0]["one_question_fit_ref"] = "fits_one_question"
    rows[0]["plan_candidate_flags"] = {
        "plus_single_question_candidate_later": True,
        "premium_deep_dive_candidate_later": False,
        "p8_design_material_candidate": True,
        "p8_implementation_spec_finalized_here": False,
    }
    return rows


def _ev18_ready(rows: list[dict[str, object]] | None = None) -> tuple[dict[str, object], dict[str, object]]:
    _, ev17 = prev17._ev17_ready(rows)
    material = ev.build_p7_r54_ev18_p6_candidate_only_handoff(p5_decision_candidate_separation=ev17)
    assert ev.assert_p7_r54_ev18_p6_candidate_only_handoff_contract(material) is True
    return ev17, material


def _ev19_ready(rows: list[dict[str, object]] | None = None) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    ev17, ev18 = _ev18_ready(rows)
    material = ev.build_p7_r54_ev19_p8_material_candidate_only_handoff(p6_candidate_only_handoff=ev18)
    assert ev.assert_p7_r54_ev19_p8_material_candidate_only_handoff_contract(material) is True
    return ev17, ev18, material


def test_r54_ev18_builds_p6_candidate_only_handoff_without_starting_p6_p8_or_release() -> None:
    ev17, material = _ev18_ready()

    assert material["schema_version"] == ev.P7_R54_EV18_P6_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION
    assert set(material) == set(ev.P7_R54_EV18_REQUIRED_FIELD_REFS)
    assert material["policy_section"] == ev.P7_R54_EV18_STEP_REF
    assert material["operation_step_ref"] == ev.P7_R54_EV18_STEP_REF
    assert material["p6_candidate_handoff_status"] == ev.P7_R54_EV18_P6_CANDIDATE_HANDOFF_READY_STATUS_REF
    assert material["p6_candidate_handoff_ref"] == ev.P7_R54_EV18_P6_CANDIDATE_HANDOFF_REF
    assert material["p6_candidate_handoff_policy_ref"] == ev.P7_R54_EV18_CANDIDATE_ONLY_POLICY_REF
    assert material["p6_candidate_handoff_reason_refs"] == [ev.P7_R54_EV18_READY_REASON_REF]
    assert material["p6_limited_human_readfeel_candidate"] is True
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p6_candidate_only_not_start"] is True
    assert material["p6_start_blocked_here"] is True
    assert material["p8_material_candidate_handoff_allowed_next"] is True
    assert material["p8_material_candidate_row_count"] == 0
    assert material["p8_material_candidate_allowed_primary_class_counts"] == {}
    assert material["p8_question_design_material_candidate"] is False
    assert material["p8_start_allowed"] is False
    assert material["question_implementation_started_here"] is False
    assert material["p8_implementation_spec_finalized_here"] is False
    assert material["release_allowed"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["p5_human_blind_qa_confirmed_candidate"] is True
    assert material["p5_human_blind_qa_confirmed_final"] is False
    assert material["existing_op20_operation_current_refs"] == r54op.P7_R54_OPERATION_CURRENT_REFS
    assert material["existing_op20_current_refs_are_historical_here"] is True
    assert material["existing_op20_reused_as_actual_p6_candidate_basis"] is False
    assert material["existing_op20_reused_as_actual_p6_candidate_handoff_basis"] is False
    assert material["existing_op20_structural_contract_reused"] is True
    assert material["required_case_count"] == 24
    assert material["reviewed_case_count"] == 24
    assert material["rating_row_count"] == 24
    assert material["question_observation_row_count"] == 24
    assert material["verdict_counts"] == ev17["verdict_counts"]
    assert material["actual_rating_rows_materialized_here"] is True
    assert material["actual_blocker_rows_materialized_here"] is True
    assert material["actual_question_need_observation_rows_materialized_here"] is True
    assert material["actual_disposal_receipt_materialized_here"] is True
    assert material["disposal_verified"] is True
    assert material["next_required_step"] == ev.P7_R54_EV19_STEP_REF
    assert tuple(material["implemented_steps"]) == ev.P7_R54_EV18_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ev.P7_R54_EV18_NOT_YET_IMPLEMENTED_STEPS
    _assert_ev18_ev19_body_free_no_promotion(material, allow_p6_candidate=True)


def test_r54_ev19_ready_with_no_p8_material_stays_candidate_only_and_no_p8_start() -> None:
    _, ev18, material = _ev19_ready()

    assert material["schema_version"] == ev.P7_R54_EV19_P8_MATERIAL_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION
    assert set(material) == set(ev.P7_R54_EV19_REQUIRED_FIELD_REFS)
    assert material["policy_section"] == ev.P7_R54_EV19_STEP_REF
    assert material["operation_step_ref"] == ev.P7_R54_EV19_STEP_REF
    assert material["p8_material_candidate_handoff_status"] == ev.P7_R54_EV19_P8_MATERIAL_HANDOFF_READY_STATUS_REF
    assert material["p8_material_candidate_handoff_ref"] == ev.P7_R54_EV19_P8_MATERIAL_HANDOFF_REF
    assert material["p8_material_candidate_handoff_policy_ref"] == ev.P7_R54_EV19_CANDIDATE_ONLY_POLICY_REF
    assert material["p8_material_candidate_handoff_reason_refs"] == [ev.P7_R54_EV19_NO_MATERIAL_REASON_REF]
    assert material["question_need_observation_rows_aggregated"] is True
    assert material["question_need_observation_rows_aggregated_count"] == 24
    assert material["p8_material_candidate_allowed_primary_class_counts"] == {}
    assert material["p8_material_candidate_primary_class_refs"] == []
    assert material["p8_material_candidate_row_count"] == 0
    assert material["p8_question_design_material_candidate"] is False
    assert material["p8_question_design_material_candidate_ref"] == ""
    assert material["p8_design_material_candidate_only_not_start"] is True
    assert material["p8_start_allowed"] is False
    assert material["question_implementation_started_here"] is False
    assert material["p8_implementation_spec_finalized_here"] is False
    assert material["question_trigger_logic_implemented"] is False
    assert material["question_api_implemented"] is False
    assert material["question_db_schema_implemented"] is False
    assert material["question_rn_ui_implemented"] is False
    assert material["question_response_key_implemented"] is False
    assert material["question_storage_schema_implemented"] is False
    assert material["question_answer_persistence_implemented"] is False
    assert material["question_plan_guard_implemented"] is False
    assert material["question_text_materialized_here"] is False
    assert material["draft_question_text_materialized_here"] is False
    assert material["api_db_rn_response_key_changed_here"] is False
    assert material["runtime_changed_here"] is False
    assert material["p6_limited_human_readfeel_candidate"] is True
    assert material["ev18_p6_limited_human_readfeel_candidate"] is True
    assert material["ev18_p6_limited_human_readfeel_start_allowed"] is False
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["existing_op21_operation_current_refs"] == r54op.P7_R54_OPERATION_CURRENT_REFS
    assert material["existing_op21_current_refs_are_historical_here"] is True
    assert material["existing_op21_reused_as_actual_p8_material_basis"] is False
    assert material["existing_op21_reused_as_actual_p8_material_handoff_basis"] is False
    assert material["existing_op21_structural_contract_reused"] is True
    assert material["actual_disposal_receipt_materialized_here"] is True
    assert material["disposal_verified"] is True
    assert material["next_required_step"] == ev.P7_R54_EV20_NEXT_REQUIRED_STEP_REF
    assert tuple(material["implemented_steps"]) == ev.P7_R54_EV19_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ev.P7_R54_EV19_NOT_YET_IMPLEMENTED_STEPS
    assert ev18["p8_material_candidate_row_count"] == 0
    _assert_ev18_ev19_body_free_no_promotion(material, allow_p6_candidate=True)


def test_r54_ev19_aggregates_selection_only_p8_material_candidate_from_question_rows() -> None:
    rows = _rows_with_p8_material_candidate()
    _, ev18, material = _ev19_ready(rows)

    expected_counts = {"plus_single_question_candidate_later": 1}
    assert ev18["p8_material_candidate_allowed_primary_class_counts"] == expected_counts
    assert ev18["p8_material_candidate_row_count"] == 1
    assert material["p8_material_candidate_allowed_primary_class_counts"] == expected_counts
    assert material["p8_material_candidate_primary_class_refs"] == ["plus_single_question_candidate_later"]
    assert material["p8_material_candidate_row_count"] == 1
    assert material["p8_question_design_material_candidate"] is True
    assert material["p8_question_design_material_candidate_ref"] == ev.P7_R54_EV19_P8_MATERIAL_CANDIDATE_REF
    assert material["p8_material_candidate_handoff_reason_refs"] == [ev.P7_R54_EV19_READY_REASON_REF]
    assert material["p8_start_allowed"] is False
    assert material["question_implementation_started_here"] is False
    assert material["p8_implementation_spec_finalized_here"] is False
    assert material["question_text_materialized_here"] is False
    assert material["draft_question_text_materialized_here"] is False
    _assert_ev18_ev19_body_free_no_promotion(material, allow_p6_candidate=True, allow_p8_material_candidate=True)


def test_r54_ev18_blocks_when_ev17_is_not_p5_confirmed_candidate() -> None:
    _, ev17 = prev17._ev17_ready(_rows_with_yellow_first_row())
    material = ev.build_p7_r54_ev18_p6_candidate_only_handoff(p5_decision_candidate_separation=ev17)

    assert ev.assert_p7_r54_ev18_p6_candidate_only_handoff_contract(material) is True
    assert material["p6_candidate_handoff_status"] == ev.P7_R54_EV18_P6_CANDIDATE_HANDOFF_BLOCKED_STATUS_REF
    assert material["p6_limited_human_readfeel_candidate"] is False
    assert material["p6_candidate_handoff_materialized_here"] is False
    assert material["p8_material_candidate_handoff_allowed_next"] is False
    assert material["p8_material_candidate_row_count"] == 0
    assert material["p5_human_blind_qa_confirmed_candidate"] is False
    assert material["actual_rating_rows_materialized_here"] is False
    assert material["actual_question_need_observation_rows_materialized_here"] is False
    assert material["disposal_verified"] is False
    assert "p5_confirmed_candidate_not_available_for_ev18_p6_candidate_handoff" in material["open_execution_blocker_ids"]
    assert material["next_required_step"] == ev.P7_R54_EV18_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_ev18_ev19_body_free_no_promotion(
        material,
        allow_actual_rows_and_disposal=False,
        allow_p5_candidate=False,
    )


def test_r54_ev19_blocks_when_ev18_is_not_ready() -> None:
    _, ev17 = prev17._ev17_ready(_rows_with_yellow_first_row())
    ev18 = ev.build_p7_r54_ev18_p6_candidate_only_handoff(p5_decision_candidate_separation=ev17)
    material = ev.build_p7_r54_ev19_p8_material_candidate_only_handoff(p6_candidate_only_handoff=ev18)

    assert ev.assert_p7_r54_ev19_p8_material_candidate_only_handoff_contract(material) is True
    assert material["p8_material_candidate_handoff_status"] == ev.P7_R54_EV19_P8_MATERIAL_HANDOFF_BLOCKED_STATUS_REF
    assert material["p8_question_design_material_candidate"] is False
    assert material["question_need_observation_rows_aggregated"] is False
    assert material["question_need_observation_rows_aggregated_count"] == 0
    assert material["p8_material_candidate_row_count"] == 0
    assert material["p6_limited_human_readfeel_candidate"] is False
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert "ev18_p6_candidate_handoff_not_ready_for_p8_material_candidate_handoff" in material["open_execution_blocker_ids"]
    assert material["next_required_step"] == ev.P7_R54_EV19_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_ev18_ev19_body_free_no_promotion(
        material,
        allow_actual_rows_and_disposal=False,
        allow_p5_candidate=False,
    )


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("existing_op20_current_refs_are_historical_here", False),
        ("existing_op20_reused_as_actual_p6_candidate_basis", True),
        ("existing_op20_reused_as_actual_p6_candidate_handoff_basis", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("p5_human_blind_qa_confirmed_final", True),
        ("actual_review_evidence_complete", True),
        ("p6_candidate_only_not_start", False),
        ("p6_start_blocked_here", False),
        ("p8_material_candidate_handoff_allowed_next", False),
        ("question_implementation_started_here", True),
        ("p8_implementation_spec_finalized_here", True),
        ("question_text_included", True),
        ("draft_question_text_included", True),
        ("local_path_included", True),
    ],
)
def test_r54_ev18_contract_rejects_promotion_and_boundary_mutations(key: str, value: object) -> None:
    _, material = _ev18_ready()
    mutated = deepcopy(material)
    mutated[key] = value

    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev18_p6_candidate_only_handoff_contract(mutated)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("existing_op21_current_refs_are_historical_here", False),
        ("existing_op21_reused_as_actual_p8_material_basis", True),
        ("existing_op21_reused_as_actual_p8_material_handoff_basis", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("question_implementation_started_here", True),
        ("p8_implementation_spec_finalized_here", True),
        ("question_trigger_logic_implemented", True),
        ("question_api_implemented", True),
        ("question_db_schema_implemented", True),
        ("question_rn_ui_implemented", True),
        ("question_response_key_implemented", True),
        ("question_storage_schema_implemented", True),
        ("question_answer_persistence_implemented", True),
        ("question_plan_guard_implemented", True),
        ("question_text_materialized_here", True),
        ("draft_question_text_materialized_here", True),
        ("p8_design_material_candidate_only_not_start", False),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("question_text_included", True),
        ("draft_question_text_included", True),
        ("local_path_included", True),
    ],
)
def test_r54_ev19_contract_rejects_question_implementation_and_p8_start_mutations(key: str, value: object) -> None:
    _, _, material = _ev19_ready(_rows_with_p8_material_candidate())
    mutated = deepcopy(material)
    mutated[key] = value

    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev19_p8_material_candidate_only_handoff_contract(mutated)


def test_r54_ev18_rejects_20260625_refs_as_actual_basis() -> None:
    _, material = _ev18_ready()
    mutated = deepcopy(material)
    mutated["operation_current_refs"] = dict(r54op.P7_R54_OPERATION_CURRENT_REFS)

    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev18_p6_candidate_only_handoff_contract(mutated)


def test_r54_ev19_rejects_inline_question_text_or_body_payload() -> None:
    _, _, material = _ev19_ready(_rows_with_p8_material_candidate())
    mutated = deepcopy(material)
    mutated["question_text"] = "What should Cocolon ask next?"

    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev19_p8_material_candidate_only_handoff_contract(mutated)
