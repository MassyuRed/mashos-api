# -*- coding: utf-8 -*-
"""P7-R53 R18/R19 tests for P5 decision separation and P6 candidate handoff."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

_R53_R18_CONFIRMED_CACHE: dict[str, object] | None = None
_R53_R18_REPAIR_CACHE: dict[str, object] | None = None
_R53_R19_READY_CACHE: dict[str, object] | None = None

sys.path.append(str(Path(__file__).resolve().parent))

import emlis_ai_p7_r51_p5_human_blind_qa_actual_local_manual_run as r51
import emlis_ai_p7_r53_r51_actual_local_review_execution_evidence_materialization as r53
from test_emlis_ai_p7_r53_r51_actual_local_review_execution_evidence_materialization_r12_r13_20260621 import (
    _red_review_rows,
    _r53_r10_from_rows,
    _r53_r11_from_r10,
)
from test_emlis_ai_p7_r53_r51_actual_local_review_execution_evidence_materialization_r14_r15_20260621 import (
    _assert_common_no_p8_release_or_runtime_change,
    _assert_no_body_payload_key_like_values,
)
from test_emlis_ai_p7_r53_r51_actual_local_review_execution_evidence_materialization_r16_r17_20260621 import (
    _r53_r16_ready,
    _r53_r17_ready,
)


def _assert_no_p5_final_p6_start_p8_release(material: dict[str, object]) -> None:
    _assert_common_no_p8_release_or_runtime_change(material)
    assert material["p5_human_blind_qa_confirmed"] is False
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p8_question_design_material_candidate"] is False
    assert material["p8_question_implementation_spec_finalized_here"] is False
    assert material["question_trigger_logic_implemented_here"] is False
    assert material["api_db_rn_response_key_changed_here"] is False
    assert material["local_packet_exported"] is False
    assert material["content_hash_of_body_stored"] is False
    _assert_no_body_payload_key_like_values(material)


def _r53_r17_repair_return_summary() -> dict[str, object]:
    capture = _r53_r10_from_rows(_red_review_rows())
    rating_rows = _r53_r11_from_r10(capture)
    blocker_ingestion = r53.build_p7_r53_readfeel_blocker_execution_blocker_ingestion_bodyfree(
        rating_row_normalization_bodyfree=rating_rows,
    )
    assert r53.assert_p7_r53_readfeel_blocker_execution_blocker_ingestion_bodyfree_contract(blocker_ingestion) is True
    question_rows = r53.build_p7_r53_question_need_observation_row_normalization_bodyfree(
        readfeel_blocker_execution_blocker_ingestion_bodyfree=blocker_ingestion,
        actual_human_review_result_capture=capture,
    )
    assert r53.assert_p7_r53_question_need_observation_row_normalization_bodyfree_contract(question_rows) is True
    consistency_guard = r53.build_p7_r53_rating_question_consistency_guard_bodyfree(
        rating_row_normalization_bodyfree=rating_rows,
        readfeel_blocker_execution_blocker_ingestion_bodyfree=blocker_ingestion,
        question_need_observation_row_normalization_bodyfree=question_rows,
    )
    assert r53.assert_p7_r53_rating_question_consistency_guard_bodyfree_contract(consistency_guard) is True
    summary = r53.build_p7_r53_body_free_post_review_summary_bodyfree(
        purge_disposal_receipt_bodyfree=_r53_r16_ready(),
        rating_row_normalization_bodyfree=rating_rows,
        readfeel_blocker_execution_blocker_ingestion_bodyfree=blocker_ingestion,
        question_need_observation_row_normalization_bodyfree=question_rows,
        rating_question_consistency_guard_bodyfree=consistency_guard,
    )
    assert r53.assert_p7_r53_body_free_post_review_summary_bodyfree_contract(summary) is True
    return summary


def _r53_r18_confirmed() -> dict[str, object]:
    global _R53_R18_CONFIRMED_CACHE
    if _R53_R18_CONFIRMED_CACHE is None:
        material = r53.build_p7_r53_p5_decision_candidate_separation_bodyfree(
            body_free_post_review_summary_bodyfree=_r53_r17_ready(),
        )
        assert r53.assert_p7_r53_p5_decision_candidate_separation_bodyfree_contract(material) is True
        _R53_R18_CONFIRMED_CACHE = material
    return deepcopy(_R53_R18_CONFIRMED_CACHE)


def _r53_r18_repair_return() -> dict[str, object]:
    global _R53_R18_REPAIR_CACHE
    if _R53_R18_REPAIR_CACHE is None:
        material = r53.build_p7_r53_p5_decision_candidate_separation_bodyfree(
            body_free_post_review_summary_bodyfree=_r53_r17_repair_return_summary(),
        )
        assert r53.assert_p7_r53_p5_decision_candidate_separation_bodyfree_contract(material) is True
        _R53_R18_REPAIR_CACHE = material
    return deepcopy(_R53_R18_REPAIR_CACHE)


def _r53_r19_ready() -> dict[str, object]:
    global _R53_R19_READY_CACHE
    if _R53_R19_READY_CACHE is None:
        handoff = r53.build_p7_r53_p6_limited_human_readfeel_candidate_handoff_bodyfree(
            p5_decision_candidate_separation_bodyfree=_r53_r18_confirmed(),
        )
        assert r53.assert_p7_r53_p6_limited_human_readfeel_candidate_handoff_bodyfree_contract(handoff) is True
        _R53_R19_READY_CACHE = handoff
    return deepcopy(_R53_R19_READY_CACHE)


def test_r53_r18_default_inconclusive_keeps_missing_summary_and_disposal_blockers_visible() -> None:
    material = r53.build_p7_r53_p5_decision_candidate_separation_bodyfree()

    assert material["schema_version"] == r53.P7_R53_P5_DECISION_CANDIDATE_SEPARATION_SCHEMA_VERSION
    assert set(material) == set(r53.P7_R53_P5_DECISION_CANDIDATE_SEPARATION_REQUIRED_FIELD_REFS)
    assert material["policy_section"] == "R53-18_p5_decision_candidate_separation"
    assert material["p5_decision_status"] == "P5_REVIEW_INCONCLUSIVE"
    assert material["p5_review_inconclusive"] is True
    assert material["p5_review_inconclusive_requirements_met"] is True
    assert material["p5_human_blind_qa_confirmed_candidate"] is False
    assert material["p5_repair_return_candidate"] is False
    assert material["r17_ready_for_p5_decision_candidate_separation"] is False
    assert material["rating_row_count"] == 0
    assert material["question_observation_row_count"] == 0
    assert material["p5_actual_review_still_not_run"] is True
    assert material["execution_blocker_ids"]
    assert all(str(ref).startswith("r53_") for ref in material["execution_blocker_ids"])
    assert material["next_required_step"] == r53.P7_R53_R18_INCONCLUSIVE_NEXT_REQUIRED_STEP_REF
    assert tuple(material["implemented_steps"]) == r53.P7_R53_R18_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == r53.P7_R53_R18_NOT_YET_IMPLEMENTED_STEPS

    _assert_no_p5_final_p6_start_p8_release(material)


def test_r53_r18_confirmed_candidate_is_candidate_only_not_p5_final() -> None:
    material = _r53_r18_confirmed()

    assert material["p5_decision_status"] == "P5_CONFIRMED_CANDIDATE"
    assert material["review_session_status"] == "R53_P5_CONFIRMED_CANDIDATE_SEPARATED_BODYFREE"
    assert material["p5_confirmed_candidate_requirements_met"] is True
    assert material["p5_human_blind_qa_confirmed_candidate"] is True
    assert material["p5_human_blind_qa_confirmed"] is False
    assert material["p5_repair_return_candidate"] is False
    assert material["p5_review_inconclusive"] is False
    assert material["p5_decision_candidate_only"] is True
    assert material["pass_count"] == 24
    assert material["red_count"] == 0
    assert material["repair_required_count"] == 0
    assert material["yellow_count"] == 0
    assert material["all_axis_targets_met"] is True
    assert material["disposal_verified"] is True
    assert material["body_removed"] is True
    assert material["reviewer_notes_removed"] is True
    assert material["actual_human_review_run_here"] is True
    assert material["actual_rating_rows_materialized_here"] is True
    assert material["post_review_summary_materialized_here"] is True
    assert material["p6_limited_human_readfeel_start_allowed_candidate"] is False
    assert material["next_required_step"] == r53.P7_R53_R18_CONFIRMED_NEXT_REQUIRED_STEP_REF
    assert r51.assert_p7_r51_p5_confirmed_repair_return_inconclusive_decision_bodyfree_contract(
        material["r51_r17_p5_decision_bodyfree"],
        allowed_true_false_key_refs=(
            "actual_human_review_run_here",
            "actual_manual_review_run_here",
            "actual_rating_rows_materialized_here",
            "actual_blocker_rows_materialized_here",
            "actual_execution_blocker_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_question_need_observation_summary_materialized_here",
            "actual_disposal_run_here",
            "disposal_receipt_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "post_review_summary_materialized_here",
            "p5_human_blind_qa_confirmed_candidate",
        ),
    ) is True

    _assert_no_p5_final_p6_start_p8_release(material)


def test_r53_r18_repair_return_keeps_p5_weakness_as_p5_repair_material_not_question_or_p6_escape() -> None:
    material = _r53_r18_repair_return()

    assert material["p5_decision_status"] == "P5_REPAIR_RETURN_CANDIDATE"
    assert material["p5_repair_return_candidate"] is True
    assert material["p5_human_blind_qa_confirmed_candidate"] is False
    assert material["p5_review_inconclusive"] is False
    assert material["red_count"] == 1
    assert material["repair_required_count"] == 0
    assert material["critical_repair_blocker_count"] >= 1
    assert material["repair_observation_count"] >= 1
    assert "p5_history_creepy_or_surveillance_feeling" in material["p5_decision_blocker_refs"]
    assert "red_verdict_present" in material["p5_decision_reason_refs"]
    assert material["p6_limited_human_readfeel_start_allowed_candidate"] is False
    assert material["p8_question_design_material_candidate"] is False
    assert material["next_required_step"] == r53.P7_R53_R18_REPAIR_RETURN_NEXT_REQUIRED_STEP_REF

    _assert_no_p5_final_p6_start_p8_release(material)


def test_r53_r18_rejects_more_than_one_p5_decision_flag_or_release_promotion() -> None:
    base = _r53_r18_confirmed()
    forbidden_pairs = [
        ("p5_human_blind_qa_confirmed", True),
        ("p5_repair_return_candidate", True),
        ("p5_review_inconclusive", True),
        ("p6_limited_human_readfeel_start_allowed_candidate", True),
        ("p6_limited_human_readfeel_candidate", True),
        ("p8_question_design_material_candidate", True),
        ("p8_start_allowed", True),
        ("p7_complete", True),
        ("release_allowed", True),
        ("api_db_rn_response_key_changed_here", True),
        ("runtime_changed_here", True),
        ("body_full_packet_generated_here", True),
    ]
    for key, value in forbidden_pairs:
        material = deepcopy(base)
        material[key] = value
        with pytest.raises(ValueError):
            r53.assert_p7_r53_p5_decision_candidate_separation_bodyfree_contract(material)


def test_r53_r19_ready_creates_p6_candidate_handoff_but_not_p6_start_or_p8_start() -> None:
    handoff = _r53_r19_ready()

    assert handoff["schema_version"] == r53.P7_R53_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_HANDOFF_SCHEMA_VERSION
    assert set(handoff) == set(r53.P7_R53_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_HANDOFF_REQUIRED_FIELD_REFS)
    assert handoff["policy_section"] == "R53-19_p6_limited_human_readfeel_candidate_handoff"
    assert handoff["p6_candidate_handoff_status"] == "P6_LIMITED_HUMAN_READFEEL_CANDIDATE_READY"
    assert handoff["review_session_status"] == "R53_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_READY_BODYFREE"
    assert handoff["r18_ready_for_p6_candidate_handoff"] is True
    assert handoff["p5_human_blind_qa_confirmed_candidate"] is True
    assert handoff["p5_repair_return_candidate"] is False
    assert handoff["p5_review_inconclusive"] is False
    assert handoff["p5_weakness_not_hidden_by_p6"] is True
    assert handoff["p5_repair_not_compensated_by_p6"] is True
    assert handoff["p6_limited_family_scope_only"] is True
    assert handoff["p6_candidate_uses_bodyfree_summary_only"] is True
    assert handoff["p6_limited_human_readfeel_candidate"] is True
    assert handoff["p6_limited_human_readfeel_start_allowed_candidate"] is True
    assert handoff["p6_limited_human_readfeel_start_allowed"] is False
    assert handoff["p8_question_design_material_candidate"] is False
    assert handoff["p8_start_allowed"] is False
    assert handoff["release_allowed"] is False
    assert handoff["missing_requirement_refs"] == []
    assert handoff["next_required_step"] == r53.P7_R53_R19_NEXT_REQUIRED_STEP_REF
    assert tuple(handoff["implemented_steps"]) == r53.P7_R53_R19_IMPLEMENTED_STEPS
    assert tuple(handoff["not_yet_implemented_steps"]) == r53.P7_R53_R19_NOT_YET_IMPLEMENTED_STEPS
    assert r51.assert_p7_r51_p6_limited_human_readfeel_candidate_handoff_bodyfree_contract(
        handoff["r51_r18_p6_candidate_handoff_bodyfree"],
        allowed_true_false_key_refs=(
            "actual_human_review_run_here",
            "actual_manual_review_run_here",
            "actual_rating_rows_materialized_here",
            "actual_blocker_rows_materialized_here",
            "actual_execution_blocker_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_question_need_observation_summary_materialized_here",
            "actual_disposal_run_here",
            "disposal_receipt_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "post_review_summary_materialized_here",
            "p5_human_blind_qa_confirmed_candidate",
            "p6_limited_human_readfeel_start_allowed_candidate",
        ),
    ) is True

    _assert_no_p5_final_p6_start_p8_release(handoff)


def test_r53_r19_blocks_p6_candidate_when_p5_decision_is_repair_or_inconclusive() -> None:
    for p5_decision in (_r53_r18_repair_return(), r53.build_p7_r53_p5_decision_candidate_separation_bodyfree()):
        handoff = r53.build_p7_r53_p6_limited_human_readfeel_candidate_handoff_bodyfree(
            p5_decision_candidate_separation_bodyfree=p5_decision,
        )
        assert handoff["p6_candidate_handoff_status"] == "P6_LIMITED_HUMAN_READFEEL_CANDIDATE_BLOCKED_BY_P5_DECISION"
        assert handoff["p6_limited_human_readfeel_candidate"] is False
        assert handoff["p6_limited_human_readfeel_start_allowed_candidate"] is False
        assert handoff["p6_limited_human_readfeel_start_allowed"] is False
        assert handoff["missing_requirement_refs"]
        assert handoff["next_required_step"] == r53.P7_R53_R19_BLOCKED_NEXT_REQUIRED_STEP_REF
        assert tuple(handoff["implemented_steps"]) == r53.P7_R53_R18_IMPLEMENTED_STEPS
        _assert_no_p5_final_p6_start_p8_release(handoff)


def test_r53_r19_rejects_p6_start_p8_start_release_or_body_export_mutations() -> None:
    base = _r53_r19_ready()
    forbidden_pairs = [
        ("p5_human_blind_qa_confirmed", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_question_design_material_candidate", True),
        ("p8_start_allowed", True),
        ("p7_complete", True),
        ("release_allowed", True),
        ("hold004_close_allowed", True),
        ("api_db_rn_response_key_changed_here", True),
        ("runtime_changed_here", True),
        ("body_full_packet_generated_here", True),
        ("body_full_packets_created_local_only", True),
        ("local_packet_exported", True),
        ("content_hash_of_body_stored", True),
    ]
    for key, value in forbidden_pairs:
        handoff = deepcopy(base)
        handoff[key] = value
        with pytest.raises(ValueError):
            r53.assert_p7_r53_p6_limited_human_readfeel_candidate_handoff_bodyfree_contract(handoff)
