# -*- coding: utf-8 -*-
"""R54 actual local-only review operation re-entry OP20/OP21 contract tests."""

from __future__ import annotations

from copy import deepcopy
import json
from functools import lru_cache

import emlis_ai_p7_r54_actual_local_review_operation_reentry_20260625 as op
from test_emlis_ai_p7_r54_actual_local_review_operation_reentry_op14_op15_20260625 import (
    _op11_with_modified_first_row,
)
from test_emlis_ai_p7_r54_actual_local_review_operation_reentry_op18_op19_20260625 import (
    _op18_ready,
)


def _assert_bodyfree_no_question_or_start(material: dict[str, object]) -> None:
    dumped = json.dumps(material, ensure_ascii=False, sort_keys=True).lower()
    forbidden_tokens = (
        '"raw_input"',
        '"comment_text"',
        '"returned_emlis_body"',
        '"bounded_history_surface"',
        '"reviewer_free_text"',
        '"reviewer_notes_body"',
        '"local_path":',
        '"body_hash"',
        '"body_full_packet_content"',
        '"question_text":',
        '"draft_question_text":',
        '"question_implementation_started_here": true',
        '"p8_start_allowed": true',
        '"p6_limited_human_readfeel_start_allowed": true',
        '"release_allowed": true',
    )
    for token in forbidden_tokens:
        assert token not in dumped
    assert material["body_free"] is True
    assert material["question_text_included"] is False
    assert material["draft_question_text_included"] is False
    assert material["local_path_included"] is False


@lru_cache(maxsize=1)
def _cached_op19_ready() -> tuple[dict[str, object]]:
    material = op.build_p7_r54_op19_p5_decision_candidate_separation(
        bodyfree_post_review_summary=_op18_ready()
    )
    assert op.assert_p7_r54_op19_p5_decision_candidate_separation_contract(material) is True
    return (material,)


def _op19_ready() -> dict[str, object]:
    return deepcopy(_cached_op19_ready()[0])


@lru_cache(maxsize=1)
def _cached_op20_ready() -> tuple[dict[str, object]]:
    material = op.build_p7_r54_op20_p6_candidate_handoff(
        p5_decision_candidate_separation=_op19_ready()
    )
    assert op.assert_p7_r54_op20_p6_candidate_handoff_contract(material) is True
    return (material,)


def _op20_ready() -> dict[str, object]:
    return deepcopy(_cached_op20_ready()[0])


def _op18_ready_with_single_p8_material_candidate() -> dict[str, object]:
    op11 = _op11_with_modified_first_row(
        question_need_primary_class="plus_single_question_candidate_later",
        ambiguity_kind_refs=["missing_target"],
        one_question_fit_ref="fits_one_question",
        repair_required_refs=["no_repair_required"],
    )
    op12 = op.build_p7_r54_op12_rating_row_normalization(
        sanitized_review_result_capture=op11
    )
    op13 = op.build_p7_r54_op13_readfeel_blocker_execution_blocker_ingestion(
        rating_row_normalization=op12
    )
    op14 = op.build_p7_r54_op14_question_need_observation_normalization(
        blocker_ingestion=op13,
        rating_row_normalization=op12,
        sanitized_review_result_capture=op11,
    )
    op15 = op.build_p7_r54_op15_rating_question_consistency_guard(
        question_need_observation_normalization=op14,
        rating_row_normalization=op12,
    )
    op16 = op.build_p7_r54_op16_pause_abort_expiration_protocol(
        rating_question_consistency_guard=op15,
        review_operation_status_ref=op.P7_R54_OP10_REVIEW_COMPLETED_SELECTIONS_CAPTURED_STATUS_REF,
    )
    op17 = op.build_p7_r54_op17_purge_disposal_receipt(
        pause_abort_expiration_protocol=op16,
        body_removed=True,
        reviewer_notes_removed=True,
        temporary_form_removed=True,
        local_packet_exported=False,
        content_hash_of_body_stored=False,
        disposal_receipt_ref=op.P7_R54_OP17_DISPOSAL_RECEIPT_REF,
    )
    material = op.build_p7_r54_op18_bodyfree_post_review_summary(
        purge_disposal_receipt=op17,
        rating_row_normalization=op12,
        blocker_ingestion=op13,
        question_need_observation_normalization=op14,
        rating_question_consistency_guard=op15,
    )
    assert op.assert_p7_r54_op18_bodyfree_post_review_summary_contract(material) is True
    return material


def _op20_ready_with_single_p8_material_candidate() -> dict[str, object]:
    op19 = op.build_p7_r54_op19_p5_decision_candidate_separation(
        bodyfree_post_review_summary=_op18_ready_with_single_p8_material_candidate()
    )
    material = op.build_p7_r54_op20_p6_candidate_handoff(
        p5_decision_candidate_separation=op19
    )
    assert op.assert_p7_r54_op20_p6_candidate_handoff_contract(material) is True
    return material


def test_op20_op21_symbols_are_exported() -> None:
    expected = {
        "P7_R54_OPERATION_P6_CANDIDATE_HANDOFF_SCHEMA_VERSION",
        "P7_R54_OPERATION_P8_MATERIAL_CANDIDATE_HANDOFF_SCHEMA_VERSION",
        "P7_R54_OP20_P6_CANDIDATE_HANDOFF_READY_STATUS_REF",
        "P7_R54_OP21_P8_MATERIAL_HANDOFF_READY_STATUS_REF",
        "build_p7_r54_op20_p6_candidate_handoff",
        "assert_p7_r54_op20_p6_candidate_handoff_contract",
        "build_p7_r54_op21_p8_material_candidate_handoff",
        "assert_p7_r54_op21_p8_material_candidate_handoff_contract",
        "build_p7_r54_operation_p6_candidate_handoff_bodyfree",
        "build_p7_r54_operation_p8_material_candidate_handoff_bodyfree",
    }
    assert expected.issubset(set(op.__all__))


def test_op20_default_blocks_without_p5_confirmed_candidate() -> None:
    material = op.build_p7_r54_op20_p6_candidate_handoff()

    assert op.assert_p7_r54_op20_p6_candidate_handoff_contract(material) is True
    assert material["p6_candidate_handoff_status"] == op.P7_R54_OP20_P6_CANDIDATE_HANDOFF_BLOCKED_STATUS_REF
    assert material["p6_limited_human_readfeel_candidate"] is False
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p8_material_candidate_handoff_allowed_next"] is False
    assert material["p8_question_design_material_candidate"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert material["next_required_step"] == op.P7_R54_OP20_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert material["open_execution_blocker_ids"]
    _assert_bodyfree_no_question_or_start(material)


def test_op20_confirmed_p5_creates_p6_candidate_only() -> None:
    material = _op20_ready()

    assert material["p6_candidate_handoff_status"] == op.P7_R54_OP20_P6_CANDIDATE_HANDOFF_READY_STATUS_REF
    assert material["p6_limited_human_readfeel_candidate"] is True
    assert material["p6_limited_human_readfeel_candidate_ref"] == op.P7_R54_OP20_P6_CANDIDATE_REF
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p6_candidate_only_not_start"] is True
    assert material["p8_material_candidate_handoff_allowed_next"] is True
    assert material["p8_question_design_material_candidate"] is False
    assert material["p8_start_allowed"] is False
    assert material["p5_human_blind_qa_confirmed_candidate"] is True
    assert material["p5_human_blind_qa_confirmed_final"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["release_allowed"] is False
    assert material["next_required_step"] == op.P7_R54_OP21_STEP_REF
    assert tuple(material["implemented_steps"]) == op.P7_R54_OP20_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == op.P7_R54_OP20_NOT_YET_IMPLEMENTED_STEPS
    _assert_bodyfree_no_question_or_start(material)


def test_op21_default_blocks_without_op20_ready() -> None:
    material = op.build_p7_r54_op21_p8_material_candidate_handoff()

    assert op.assert_p7_r54_op21_p8_material_candidate_handoff_contract(material) is True
    assert material["p8_material_candidate_handoff_status"] == op.P7_R54_OP21_P8_MATERIAL_HANDOFF_BLOCKED_STATUS_REF
    assert material["p8_question_design_material_candidate"] is False
    assert material["question_need_observation_rows_aggregated"] is False
    assert material["p8_start_allowed"] is False
    assert material["question_implementation_started_here"] is False
    assert material["p8_implementation_spec_finalized_here"] is False
    assert material["question_trigger_logic_implemented"] is False
    assert material["question_answer_persistence_implemented"] is False
    assert material["question_api_implemented"] is False
    assert material["question_db_schema_implemented"] is False
    assert material["question_rn_ui_implemented"] is False
    assert material["question_response_key_implemented"] is False
    assert material["release_allowed"] is False
    assert material["next_required_step"] == op.P7_R54_OP21_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert material["open_execution_blocker_ids"]
    _assert_bodyfree_no_question_or_start(material)


def test_op21_ready_without_question_material_is_handoff_only() -> None:
    material = op.build_p7_r54_op21_p8_material_candidate_handoff(
        p6_candidate_handoff=_op20_ready()
    )

    assert material["p8_material_candidate_handoff_status"] == op.P7_R54_OP21_P8_MATERIAL_HANDOFF_READY_STATUS_REF
    assert material["p8_question_design_material_candidate"] is False
    assert material["p8_material_candidate_row_count"] == 0
    assert material["p8_material_candidate_handoff_reason_refs"] == [op.P7_R54_OP21_NO_MATERIAL_REASON_REF]
    assert material["question_need_observation_rows_aggregated"] is True
    assert material["question_need_observation_rows_aggregated_count"] == 24
    assert material["p6_limited_human_readfeel_candidate"] is True
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["question_implementation_started_here"] is False
    assert material["p8_implementation_spec_finalized_here"] is False
    assert material["next_required_step"] == op.P7_R54_OP22_STEP_REF
    _assert_bodyfree_no_question_or_start(material)


def test_op21_with_question_observation_material_sets_p8_candidate_only() -> None:
    material = op.build_p7_r54_op21_p8_material_candidate_handoff(
        p6_candidate_handoff=_op20_ready_with_single_p8_material_candidate()
    )

    assert material["p8_material_candidate_handoff_status"] == op.P7_R54_OP21_P8_MATERIAL_HANDOFF_READY_STATUS_REF
    assert material["p8_question_design_material_candidate"] is True
    assert material["p8_question_design_material_candidate_ref"] == op.P7_R54_OP21_P8_MATERIAL_CANDIDATE_REF
    assert material["p8_material_candidate_row_count"] == 1
    assert material["p8_material_candidate_primary_class_counts"] == {"plus_single_question_candidate_later": 1}
    assert material["p8_material_candidate_handoff_reason_refs"] == [op.P7_R54_OP21_READY_REASON_REF]
    assert material["p8_start_allowed"] is False
    assert material["question_implementation_started_here"] is False
    assert material["p8_implementation_spec_finalized_here"] is False
    assert material["question_trigger_logic_implemented"] is False
    assert material["question_answer_persistence_implemented"] is False
    assert material["question_api_implemented"] is False
    assert material["question_db_schema_implemented"] is False
    assert material["question_rn_ui_implemented"] is False
    assert material["question_response_key_implemented"] is False
    assert material["release_allowed"] is False
    _assert_bodyfree_no_question_or_start(material)


def test_op20_op21_aliases_match_primary_builders() -> None:
    assert op.build_p7_r54_operation_p6_candidate_handoff is op.build_p7_r54_op20_p6_candidate_handoff
    assert op.assert_p7_r54_operation_p6_candidate_handoff_contract is op.assert_p7_r54_op20_p6_candidate_handoff_contract
    assert op.build_p7_r54_operation_p8_material_candidate_handoff is op.build_p7_r54_op21_p8_material_candidate_handoff
    assert op.assert_p7_r54_operation_p8_material_candidate_handoff_contract is op.assert_p7_r54_op21_p8_material_candidate_handoff_contract
    assert op.build_p7_r54_operation_p6_candidate_handoff_bodyfree is op.build_p7_r54_op20_p6_candidate_handoff
    assert op.build_p7_r54_operation_p8_material_candidate_handoff_bodyfree is op.build_p7_r54_op21_p8_material_candidate_handoff
