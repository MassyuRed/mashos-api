# -*- coding: utf-8 -*-
"""P7-R53 R12/R13 tests for blocker and question-observation rows."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parent))

import emlis_ai_p7_r51_p5_human_blind_qa_actual_local_manual_run as r51
import emlis_ai_p7_r53_r51_actual_local_review_execution_evidence_materialization as r53
from test_emlis_ai_p7_r53_r51_actual_local_review_execution_evidence_materialization_r10_r11_20260621 import (
    _r53_r10_ready,
    _r53_r9_ready_and_manifest,
    _sanitized_review_result_rows,
)


def _assert_no_body_payload_key_like_values(material: dict[str, object]) -> None:
    serialized = repr(material)
    for forbidden_key_repr in (
        "'raw_input':",
        "'raw_answer':",
        "'comment_text':",
        "'body':",
        "'returned_emlis_surface':",
        "'current_input_review_surface':",
        "'bounded_owned_history_surface':",
        "'reviewer_free_text':",
        "'reviewer_notes':",
        "'question_text':",
        "'draft_question_text':",
        "'local_absolute_path':",
        "'body_content_hash':",
        "'packet_content_hash':",
    ):
        assert forbidden_key_repr not in serialized


def _assert_common_no_p8_release_or_runtime_change(material: dict[str, object]) -> None:
    assert material["body_free"] is True
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["p8_start_allowed"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False
    assert material["api_db_rn_response_key_changed_here"] is False
    assert material["runtime_changed_here"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["body_full_packets_created_local_only"] is False
    assert material["actual_reviewer_notes_materialized_here"] is False


def _r53_r10_from_rows(rows: list[dict[str, object]]) -> dict[str, object]:
    form, manifest = _r53_r9_ready_and_manifest()
    capture = r53.build_p7_r53_actual_human_review_result_capture_bodyfree(
        reviewer_instruction_rating_form_freeze=form,
        case_manifest_freeze=manifest,
        review_result_rows=rows,
    )
    assert r53.assert_p7_r53_actual_human_review_result_capture_bodyfree_contract(capture) is True
    return capture


def _r53_r11_from_r10(capture: dict[str, object]) -> dict[str, object]:
    normalization = r53.build_p7_r53_rating_row_normalization_bodyfree(
        actual_human_review_result_capture=capture,
    )
    assert r53.assert_p7_r53_rating_row_normalization_bodyfree_contract(normalization) is True
    return normalization


def _r53_r11_ready() -> dict[str, object]:
    return _r53_r11_from_r10(_r53_r10_ready())


def _r53_r12_ready() -> dict[str, object]:
    ingestion = r53.build_p7_r53_readfeel_blocker_execution_blocker_ingestion_bodyfree(
        rating_row_normalization_bodyfree=_r53_r11_ready(),
    )
    assert r53.assert_p7_r53_readfeel_blocker_execution_blocker_ingestion_bodyfree_contract(ingestion) is True
    return ingestion


def _red_review_rows() -> list[dict[str, object]]:
    rows = deepcopy(_sanitized_review_result_rows())
    rows[0]["axis_scores"] = {
        "history_connection_naturalness": 0.2,
        "creepy_absence": 0.1,
        "overclaim_absence": 0.2,
        "self_blame_non_amplification": 0.2,
        "wants_more_input_or_accumulation": 0.2,
        "non_shallow_repeat": 0.2,
    }
    rows[0]["verdict"] = "RED"
    rows[0]["sanitized_reason_ids"] = ["p5_history_creepy_or_surveillance_feeling"]
    rows[0]["blocker_ids"] = ["p5_history_creepy_or_surveillance_feeling"]
    rows[0]["question_need_primary_class"] = "not_question_p5_surface_repair_required"
    rows[0]["ambiguity_kind_refs"] = ["history_connection_basis_unclear"]
    rows[0]["one_question_fit_ref"] = "repair_required_not_question"
    rows[0]["repair_required_refs"] = ["p5_surface_repair_required"]
    return rows


def _question_candidate_rows() -> list[dict[str, object]]:
    rows = deepcopy(_sanitized_review_result_rows())
    rows[0]["question_need_primary_class"] = "plus_single_question_candidate_later"
    rows[0]["ambiguity_kind_refs"] = ["missing_target"]
    rows[0]["one_question_fit_ref"] = "fits_one_question"
    rows[0]["repair_required_refs"] = ["no_repair_required"]
    return rows


def test_r53_r12_default_blocker_ingestion_is_blocked_without_ready_rating_rows() -> None:
    ingestion = r53.build_p7_r53_readfeel_blocker_execution_blocker_ingestion_bodyfree()

    assert ingestion["schema_version"] == r53.P7_R53_READFEEL_EXECUTION_BLOCKER_INGESTION_SCHEMA_VERSION
    assert set(ingestion) == set(r53.P7_R53_READFEEL_EXECUTION_BLOCKER_INGESTION_REQUIRED_FIELD_REFS)
    assert ingestion["policy_section"] == "R53-12_readfeel_blocker_execution_blocker_ingestion"
    assert ingestion["blocker_ingestion_status"] == "BLOCKED_BY_R53_11_RATING_ROW_NORMALIZATION"
    assert ingestion["r11_rating_rows_ready_for_blocker_ingestion"] is False
    assert ingestion["readfeel_blocker_row_count"] == 0
    assert ingestion["execution_blocker_row_count"] >= 1
    assert ingestion["readfeel_blocker_row_builder_ready"] is False
    assert ingestion["execution_blocker_row_builder_ready"] is False
    assert ingestion["actual_blocker_rows_materialized_here"] is False
    assert ingestion["actual_execution_blocker_rows_materialized_here"] is False
    assert ingestion["actual_question_need_observation_rows_materialized_here"] is False
    assert ingestion["execution_blocker_ids"]
    assert ingestion["open_execution_blocker_ids"] == ingestion["execution_blocker_ids"]
    assert ingestion["next_required_step"] == r53.P7_R53_R12_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert tuple(ingestion["implemented_steps"]) == r53.P7_R53_R9_IMPLEMENTED_STEPS

    _assert_common_no_p8_release_or_runtime_change(ingestion)
    _assert_no_body_payload_key_like_values(ingestion)


def test_r53_r12_ready_ingests_zero_readfeel_and_zero_execution_blockers_for_all_pass_rows() -> None:
    ingestion = _r53_r12_ready()

    assert ingestion["blocker_ingestion_status"] == "READY_FOR_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION"
    assert ingestion["review_session_status"] == "R53_READFEEL_EXECUTION_BLOCKERS_INGESTED_BODYFREE"
    assert ingestion["r11_rating_rows_ready_for_blocker_ingestion"] is True
    assert ingestion["r51_r10_next_required_step"] == r51.P7_R51_R10_NEXT_REQUIRED_STEP_REF
    assert ingestion["rating_row_count"] == 24
    assert ingestion["readfeel_blocker_row_count"] == 0
    assert ingestion["execution_blocker_row_count"] == 0
    assert ingestion["open_readfeel_blocker_count"] == 0
    assert ingestion["open_execution_blocker_count"] == 0
    assert ingestion["readfeel_and_execution_blockers_separated"] is True
    assert ingestion["execution_blockers_do_not_assign_readfeel_verdict"] is True
    assert ingestion["execution_blocker_cases_do_not_create_rating_rows"] is True
    assert ingestion["actual_human_review_run_here"] is True
    assert ingestion["actual_manual_review_run_here"] is True
    assert ingestion["actual_rating_rows_materialized_here"] is True
    assert ingestion["actual_blocker_rows_materialized_here"] is True
    assert ingestion["actual_execution_blocker_rows_materialized_here"] is True
    assert ingestion["actual_question_need_observation_rows_materialized_here"] is False
    assert ingestion["p5_actual_review_still_not_run"] is False
    assert ingestion["execution_blocker_ids"] == []
    assert ingestion["r53_12_readfeel_blocker_execution_blocker_ingestion_built"] is True
    assert ingestion["next_required_step"] == r53.P7_R53_R12_NEXT_REQUIRED_STEP_REF
    assert tuple(ingestion["implemented_steps"]) == r53.P7_R53_R12_IMPLEMENTED_STEPS
    assert tuple(ingestion["not_yet_implemented_steps"]) == r53.P7_R53_R12_NOT_YET_IMPLEMENTED_STEPS
    assert r51.assert_p7_r51_readfeel_blocker_execution_blocker_ingestion_bodyfree_contract(
        ingestion["r51_r10_readfeel_execution_blocker_ingestion_bodyfree"],
        allowed_true_false_key_refs=r53.P7_R53_R12_ALLOWED_TRUE_FALSE_KEY_REFS,
    ) is True

    _assert_common_no_p8_release_or_runtime_change(ingestion)
    _assert_no_body_payload_key_like_values(ingestion)


def test_r53_r12_readfeel_blocker_rows_do_not_become_execution_blockers() -> None:
    capture = _r53_r10_from_rows(_red_review_rows())
    normalization = _r53_r11_from_r10(capture)
    ingestion = r53.build_p7_r53_readfeel_blocker_execution_blocker_ingestion_bodyfree(
        rating_row_normalization_bodyfree=normalization,
    )

    assert ingestion["blocker_ingestion_status"] == "READY_FOR_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION"
    assert ingestion["readfeel_blocker_row_count"] == 1
    assert ingestion["execution_blocker_row_count"] == 0
    assert ingestion["readfeel_blocker_counts"] == {"p5_history_creepy_or_surveillance_feeling": 1}
    assert ingestion["execution_blocker_counts"] == {}
    assert ingestion["execution_blocker_ids"] == []
    row = ingestion["readfeel_blocker_rows"][0]  # type: ignore[index]
    assert isinstance(row, dict)
    assert row["schema_version"] == r51.P7_R51_READFEEL_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION
    assert row["blocker_id"] == "p5_history_creepy_or_surveillance_feeling"
    assert row["blocker_kind"] != "EXECUTION_BLOCKER"
    assert row["blocker_status"] == "OPEN"
    assert row["body_free"] is True
    assert r51.assert_p7_r51_readfeel_blocker_row_bodyfree_contract(row) is True

    _assert_no_body_payload_key_like_values(ingestion)


@pytest.mark.parametrize(
    "key,value",
    [
        ("execution_blockers_do_not_assign_readfeel_verdict", False),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("body_full_packet_generated_here", True),
        ("body_full_packets_created_local_only", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("api_db_rn_response_key_changed_here", True),
        ("runtime_changed_here", True),
    ],
)
def test_r53_r12_rejects_misclassification_question_rows_bodyfull_or_release_promotion(key: str, value: object) -> None:
    ingestion = _r53_r12_ready()
    ingestion[key] = value
    with pytest.raises(ValueError):
        r53.assert_p7_r53_readfeel_blocker_execution_blocker_ingestion_bodyfree_contract(ingestion)


def test_r53_r13_default_question_row_normalization_is_blocked_without_r12_and_r10() -> None:
    normalization = r53.build_p7_r53_question_need_observation_row_normalization_bodyfree()

    assert normalization["schema_version"] == r53.P7_R53_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION_SCHEMA_VERSION
    assert set(normalization) == set(r53.P7_R53_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION_REQUIRED_FIELD_REFS)
    assert normalization["policy_section"] == "R53-13_question_need_observation_row_normalization"
    assert normalization["question_observation_normalizer_status"] == "BLOCKED_BY_R53_12_OR_R53_10_PRECHECK"
    assert normalization["r12_ready_for_question_need_observation_row_normalization"] is False
    assert normalization["r10_actual_review_capture_ready_for_question_observation"] is False
    assert normalization["question_observation_row_count"] == 0
    assert normalization["question_need_observation_rows"] == []
    assert normalization["all_required_question_need_observation_rows_present"] is False
    assert normalization["question_text_or_draft_text_saved_here"] is False
    assert normalization["actual_question_need_observation_rows_materialized_here"] is False
    assert normalization["p5_actual_review_still_not_run"] is True
    assert normalization["execution_blocker_ids"]
    assert normalization["open_execution_blocker_ids"] == normalization["execution_blocker_ids"]
    assert normalization["next_required_step"] == r53.P7_R53_R13_BLOCKED_NEXT_REQUIRED_STEP_REF

    _assert_common_no_p8_release_or_runtime_change(normalization)
    _assert_no_body_payload_key_like_values(normalization)


def test_r53_r13_ready_normalizes_24_bodyfree_question_observation_rows_without_question_text() -> None:
    capture = _r53_r10_ready()
    ingestion = _r53_r12_ready()
    normalization = r53.build_p7_r53_question_need_observation_row_normalization_bodyfree(
        readfeel_blocker_execution_blocker_ingestion_bodyfree=ingestion,
        actual_human_review_result_capture=capture,
    )

    assert normalization["question_observation_normalizer_status"] == "READY_FOR_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD"
    assert normalization["review_session_status"] == "R53_QUESTION_NEED_OBSERVATION_ROWS_NORMALIZED_BODYFREE"
    assert normalization["r12_ready_for_question_need_observation_row_normalization"] is True
    assert normalization["r10_actual_review_capture_ready_for_question_observation"] is True
    assert normalization["r51_r11_next_required_step"] == r51.P7_R51_R11_NEXT_REQUIRED_STEP_REF
    assert normalization["question_observation_row_count"] == 24
    assert normalization["row_case_ref_sets_match_review_capture"] is True
    assert normalization["row_case_ref_sets_match_rating_rows"] is True
    assert normalization["all_required_question_need_observation_rows_present"] is True
    assert normalization["primary_class_ambiguity_one_question_fit_are_canonical_refs"] is True
    assert normalization["question_text_absent_for_all_rows"] is True
    assert normalization["draft_question_text_absent_for_all_rows"] is True
    assert normalization["reviewer_free_text_absent_for_all_rows"] is True
    assert normalization["raw_input_absent_for_all_rows"] is True
    assert normalization["returned_surface_absent_for_all_rows"] is True
    assert normalization["local_path_absent_for_all_rows"] is True
    assert normalization["body_hash_absent_for_all_rows"] is True
    assert normalization["question_api_implemented"] is False
    assert normalization["question_db_schema_implemented"] is False
    assert normalization["question_rn_ui_implemented"] is False
    assert normalization["question_response_key_implemented"] is False
    assert normalization["question_storage_schema_implemented"] is False
    assert normalization["p8_question_implementation_spec_finalized_here"] is False
    assert normalization["actual_human_review_run_here"] is True
    assert normalization["actual_manual_review_run_here"] is True
    assert normalization["actual_rating_rows_materialized_here"] is True
    assert normalization["actual_blocker_rows_materialized_here"] is True
    assert normalization["actual_execution_blocker_rows_materialized_here"] is True
    assert normalization["actual_question_need_observation_rows_materialized_here"] is True
    assert normalization["actual_question_need_observation_summary_materialized_here"] is False
    assert normalization["p5_actual_review_still_not_run"] is False
    assert normalization["execution_blocker_ids"] == []
    assert normalization["r53_13_question_need_observation_row_normalization_built"] is True
    assert normalization["next_required_step"] == r53.P7_R53_R13_NEXT_REQUIRED_STEP_REF
    assert tuple(normalization["implemented_steps"]) == r53.P7_R53_R13_IMPLEMENTED_STEPS
    assert tuple(normalization["not_yet_implemented_steps"]) == r53.P7_R53_R13_NOT_YET_IMPLEMENTED_STEPS
    assert r51.assert_p7_r51_question_need_observation_row_normalizer_bodyfree_contract(
        normalization["r51_r11_question_need_observation_row_normalizer_bodyfree"],
        allowed_true_false_key_refs=r53.P7_R53_R13_ALLOWED_TRUE_FALSE_KEY_REFS,
    ) is True
    for row in normalization["question_need_observation_rows"]:  # type: ignore[index]
        assert isinstance(row, dict)
        assert row["schema_version"] == r51.P7_R51_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_SCHEMA_VERSION
        assert row["body_free"] is True
        assert row["question_text_included"] is False
        assert row["draft_question_text_included"] is False
        assert row["reviewer_free_text_included"] is False

    _assert_common_no_p8_release_or_runtime_change(normalization)
    _assert_no_body_payload_key_like_values(normalization)


def test_r53_r13_plus_question_candidate_is_material_only_and_does_not_start_p8() -> None:
    capture = _r53_r10_from_rows(_question_candidate_rows())
    rating_rows = _r53_r11_from_r10(capture)
    ingestion = r53.build_p7_r53_readfeel_blocker_execution_blocker_ingestion_bodyfree(
        rating_row_normalization_bodyfree=rating_rows,
    )
    normalization = r53.build_p7_r53_question_need_observation_row_normalization_bodyfree(
        readfeel_blocker_execution_blocker_ingestion_bodyfree=ingestion,
        actual_human_review_result_capture=capture,
    )

    assert normalization["question_observation_normalizer_status"] == "READY_FOR_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD"
    assert normalization["question_need_primary_class_counts"]["plus_single_question_candidate_later"] == 1  # type: ignore[index]
    assert normalization["ambiguity_kind_counts"]["missing_target"] == 1  # type: ignore[index]
    assert normalization["one_question_fit_counts"]["fits_one_question"] == 1  # type: ignore[index]
    assert normalization["plan_candidate_flag_counts"]["plus_single_question_candidate_later"] == 1  # type: ignore[index]
    assert normalization["plan_candidate_flag_counts"]["p8_design_material_candidate"] >= 1  # type: ignore[index]
    assert normalization["p8_start_allowed"] is False
    assert normalization["question_api_implemented"] is False
    assert normalization["question_text_or_draft_text_saved_here"] is False
    assert normalization["p5_weakness_not_hidden_by_question_candidates_here"] is False

    _assert_no_body_payload_key_like_values(normalization)


@pytest.mark.parametrize(
    "key,value",
    [
        ("question_text_included_allowed", True),
        ("draft_question_text_included_allowed", True),
        ("reviewer_free_text_included_allowed", True),
        ("raw_input_allowed", True),
        ("returned_surface_allowed", True),
        ("local_path_allowed", True),
        ("body_hash_allowed", True),
        ("p8_question_implementation_spec_finalized_here", True),
        ("question_trigger_logic_implemented_here", True),
        ("question_api_implemented", True),
        ("question_db_schema_implemented", True),
        ("question_rn_ui_implemented", True),
        ("question_response_key_implemented", True),
        ("question_storage_schema_implemented", True),
        ("question_text_or_draft_text_saved_here", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("api_db_rn_response_key_changed_here", True),
        ("runtime_changed_here", True),
    ],
)
def test_r53_r13_rejects_question_text_question_implementation_body_leak_or_release_promotion(key: str, value: object) -> None:
    normalizer = r53.build_p7_r53_question_need_observation_row_normalization_bodyfree(
        readfeel_blocker_execution_blocker_ingestion_bodyfree=_r53_r12_ready(),
        actual_human_review_result_capture=_r53_r10_ready(),
    )
    normalizer[key] = value
    with pytest.raises(ValueError):
        r53.assert_p7_r53_question_need_observation_row_normalization_bodyfree_contract(normalizer)


def test_r53_r13_rejects_question_observation_row_that_attempts_to_include_question_text() -> None:
    normalizer = r53.build_p7_r53_question_need_observation_row_normalization_bodyfree(
        readfeel_blocker_execution_blocker_ingestion_bodyfree=_r53_r12_ready(),
        actual_human_review_result_capture=_r53_r10_ready(),
    )
    normalizer["question_need_observation_rows"][0]["question_text_included"] = True  # type: ignore[index]
    with pytest.raises(ValueError):
        r53.assert_p7_r53_question_need_observation_row_normalization_bodyfree_contract(normalizer)
