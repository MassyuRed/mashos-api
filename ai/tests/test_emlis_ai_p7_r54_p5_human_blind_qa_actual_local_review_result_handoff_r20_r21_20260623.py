# -*- coding: utf-8 -*-
from __future__ import annotations

from copy import deepcopy

import pytest

import emlis_ai_p7_r54_p5_human_blind_qa_actual_local_review_result_handoff as r54
from test_emlis_ai_p7_r54_p5_human_blind_qa_actual_local_review_result_handoff_r18_r19_20260623 import (
    _assert_body_free_no_runtime_promotion,
    _r10_ready_with_transform,
    _ready_summary,
    _repair_summary,
    _review_row_from_manifest_row,
    _summary_from_capture,
    _yellow_summary,
)


def _p8_material_candidate_summary(tmp_path) -> dict[str, object]:
    def transform(rows: list[dict[str, object]], manifest: dict[str, object]) -> list[dict[str, object]]:
        updated = list(rows)
        source = manifest["controller_manifest_rows"][0]
        updated[0] = _review_row_from_manifest_row(
            source,
            question_need_primary_class="question_may_reduce_overread_risk",
            one_question_fit_ref="fits_one_question",
        )
        return updated

    return _summary_from_capture(tmp_path, _r10_ready_with_transform(tmp_path, transform=transform))


def _r19_from_summary(summary: dict[str, object]) -> dict[str, object]:
    decision = r54.build_p7_r54_p5_decision_candidate_separation_bodyfree(
        body_free_post_review_summary=summary,
    )
    return r54.build_p7_r54_p6_limited_human_readfeel_candidate_handoff_bodyfree(
        p5_decision_candidate_separation=decision,
    )


def _r20_from_summary(summary: dict[str, object]) -> dict[str, object]:
    return r54.build_p7_r54_p8_question_design_material_candidate_handoff_bodyfree(
        p6_limited_human_readfeel_candidate_handoff=_r19_from_summary(summary),
        body_free_post_review_summary=summary,
    )


def test_r54_r20_default_blocks_until_r19_and_r17_are_ready() -> None:
    handoff = r54.build_p7_r54_p8_question_design_material_candidate_handoff_bodyfree()

    assert set(handoff) == set(r54.P7_R54_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_REQUIRED_FIELD_REFS)
    assert handoff["schema_version"] == r54.P7_R54_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_SCHEMA_VERSION
    assert handoff["policy_section"] == r54.P7_R54_R20_STEP_REF
    assert handoff["p8_question_design_material_candidate_status"] == "BLOCKED_BY_R54_19_P6_CANDIDATE_HANDOFF"
    assert handoff["p8_question_design_material_candidate_materialized_here"] is False
    assert handoff["p8_question_design_material_candidate"] is False
    assert handoff["p8_start_allowed"] is False
    assert handoff["question_text_designed_here"] is False
    assert handoff["draft_question_text_designed_here"] is False
    assert handoff["r54_20_p8_question_design_material_candidate_handoff_built"] is False
    assert handoff["next_required_step"] == r54.P7_R54_R20_BLOCKED_NEXT_REQUIRED_STEP_REF

    assert r54.assert_p7_r54_p8_question_design_material_candidate_handoff_bodyfree_contract(handoff) is True
    _assert_body_free_no_runtime_promotion(handoff)


def test_r54_r20_p8_material_candidate_can_be_true_but_p8_start_remains_false(tmp_path) -> None:
    handoff = _r20_from_summary(_p8_material_candidate_summary(tmp_path))

    assert handoff["p8_question_design_material_candidate_status"] == "P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_TRUE"
    assert handoff["p8_question_design_material_candidate"] is True
    assert handoff["p8_material_candidate_observation_count"] == 1
    assert handoff["p8_material_candidate_primary_class_counts"]["question_may_reduce_overread_risk"] == 1
    assert handoff["p5_human_blind_qa_confirmed_candidate"] is True
    assert handoff["p5_repair_or_inconclusive_not_p8_material"] is False
    assert handoff["p8_start_allowed"] is False
    assert handoff["p7_complete"] is False
    assert handoff["release_allowed"] is False
    assert handoff["question_text_designed_here"] is False
    assert handoff["draft_question_text_designed_here"] is False
    assert handoff["p8_question_api_designed_here"] is False
    assert handoff["p8_question_db_schema_designed_here"] is False
    assert handoff["p8_question_rn_ui_designed_here"] is False
    assert handoff["p8_question_trigger_logic_designed_here"] is False
    assert handoff["p8_question_response_key_designed_here"] is False
    assert handoff["p8_question_plan_guard_designed_here"] is False
    assert r54.P7_R54_R20_P8_START_ALLOWED_FALSE_REASON_REF in handoff["p8_start_allowed_false_reason_refs"]
    assert handoff["next_required_step"] == r54.P7_R54_R20_NEXT_REQUIRED_STEP_REF

    assert r54.assert_p7_r54_p8_question_design_material_candidate_handoff_bodyfree_contract(handoff) is True
    _assert_body_free_no_runtime_promotion(handoff)


def test_r54_r20_no_question_observation_is_materialized_but_not_p8_candidate(tmp_path) -> None:
    handoff = _r20_from_summary(_ready_summary(tmp_path))

    assert handoff["p8_question_design_material_candidate_status"] == "P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_NOT_AVAILABLE_NO_OBSERVATION"
    assert handoff["p8_question_design_material_candidate"] is False
    assert handoff["p8_material_candidate_observation_count"] == 0
    assert handoff["p8_question_design_material_candidate_materialized_here"] is True
    assert handoff["p8_start_allowed"] is False
    assert handoff["next_required_step"] == r54.P7_R54_R20_NEXT_REQUIRED_STEP_REF

    assert r54.assert_p7_r54_p8_question_design_material_candidate_handoff_bodyfree_contract(handoff) is True
    _assert_body_free_no_runtime_promotion(handoff)


def test_r54_r20_p5_repair_or_inconclusive_never_becomes_p8_material(tmp_path) -> None:
    repair_handoff = _r20_from_summary(_repair_summary(tmp_path))
    yellow_handoff = _r20_from_summary(_yellow_summary(tmp_path))

    assert repair_handoff["p8_question_design_material_candidate_status"] == "P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_NOT_AVAILABLE_P5_REPAIR_RETURN"
    assert repair_handoff["p8_question_design_material_candidate"] is False
    assert repair_handoff["p5_repair_or_inconclusive_not_p8_material"] is True
    assert repair_handoff["not_question_repair_observation_count"] >= 1

    assert yellow_handoff["p8_question_design_material_candidate_status"] == "P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_NOT_AVAILABLE_P5_INCONCLUSIVE"
    assert yellow_handoff["p8_question_design_material_candidate"] is False
    assert yellow_handoff["p5_repair_or_inconclusive_not_p8_material"] is True

    assert r54.assert_p7_r54_p8_question_design_material_candidate_handoff_bodyfree_contract(repair_handoff) is True
    assert r54.assert_p7_r54_p8_question_design_material_candidate_handoff_bodyfree_contract(yellow_handoff) is True
    _assert_body_free_no_runtime_promotion(repair_handoff)
    _assert_body_free_no_runtime_promotion(yellow_handoff)


def test_r54_r20_contract_rejects_p8_start_question_text_or_p8_design_mutation(tmp_path) -> None:
    handoff = _r20_from_summary(_p8_material_candidate_summary(tmp_path))
    for key in (
        "p8_start_allowed",
        "p7_complete",
        "release_allowed",
        "question_text_included",
        "draft_question_text_included",
        "question_text_designed_here",
        "draft_question_text_designed_here",
        "p8_question_api_designed_here",
        "p8_question_db_schema_designed_here",
        "p8_question_rn_ui_designed_here",
        "p8_question_trigger_logic_designed_here",
        "p8_question_response_key_designed_here",
        "p8_question_plan_guard_designed_here",
        "actual_human_review_run_here",
        "actual_manual_review_run_here",
        "local_absolute_path_included",
        "body_content_hash_included",
    ):
        mutated = deepcopy(handoff)
        mutated[key] = True
        with pytest.raises(ValueError):
            r54.assert_p7_r54_p8_question_design_material_candidate_handoff_bodyfree_contract(mutated)


def test_r54_r21_default_blocks_until_r20_is_ready() -> None:
    validation = r54.build_p7_r54_final_no_body_leak_no_question_text_no_touch_validation_bodyfree()

    assert set(validation) == set(r54.P7_R54_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_REQUIRED_FIELD_REFS)
    assert validation["schema_version"] == r54.P7_R54_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_SCHEMA_VERSION
    assert validation["policy_section"] == r54.P7_R54_R21_STEP_REF
    assert validation["final_validation_status"] == "FINAL_VALIDATION_BLOCKED_BY_R54_20_P8_MATERIAL_HANDOFF"
    assert validation["final_validation_passed"] is False
    assert validation["ready_for_r52_reintake_handoff"] is False
    assert validation["p8_start_allowed"] is False
    assert validation["r54_21_final_no_body_leak_no_question_text_no_touch_validation_built"] is False
    assert validation["next_required_step"] == r54.P7_R54_R21_BLOCKED_NEXT_REQUIRED_STEP_REF

    assert r54.assert_p7_r54_final_no_body_leak_no_question_text_no_touch_validation_bodyfree_contract(validation) is True
    _assert_body_free_no_runtime_promotion(validation)


def test_r54_r21_passes_clean_p8_material_candidate_without_starting_p8(tmp_path) -> None:
    r20 = _r20_from_summary(_p8_material_candidate_summary(tmp_path))
    validation = r54.build_p7_r54_final_no_body_leak_no_question_text_no_touch_validation_bodyfree(
        p8_question_design_material_candidate_handoff=r20,
    )

    assert validation["final_validation_status"] == "FINAL_BODY_FREE_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_READY"
    assert validation["final_validation_passed"] is True
    assert validation["ready_for_r52_reintake_handoff"] is True
    assert validation["body_leak_detected"] is False
    assert validation["question_text_detected"] is False
    assert validation["no_touch_violation_detected"] is False
    assert validation["no_touch_touched_refs"] == []
    assert validation["p8_question_design_material_candidate"] is True
    assert validation["p8_start_allowed"] is False
    assert validation["p7_complete"] is False
    assert validation["release_allowed"] is False
    assert validation["next_required_step"] == r54.P7_R54_R21_NEXT_REQUIRED_STEP_REF

    assert r54.assert_p7_r54_final_no_body_leak_no_question_text_no_touch_validation_bodyfree_contract(validation) is True
    _assert_body_free_no_runtime_promotion(validation)


def test_r54_r21_blocks_detected_question_text_body_leak_or_no_touch_violation(tmp_path) -> None:
    r20 = _r20_from_summary(_p8_material_candidate_summary(tmp_path))

    question_blocked = r54.build_p7_r54_final_no_body_leak_no_question_text_no_touch_validation_bodyfree(
        p8_question_design_material_candidate_handoff=r20,
        additional_bodyfree_materials_to_scan=(
            {"material_id": "bad_question_material", "question_text": "should not be retained"},
        ),
    )
    assert question_blocked["final_validation_status"] == "FINAL_VALIDATION_BLOCKED_BY_QUESTION_TEXT"
    assert question_blocked["question_text_detected"] is True
    assert question_blocked["final_validation_passed"] is False
    assert question_blocked["p8_start_allowed"] is False

    body_blocked = r54.build_p7_r54_final_no_body_leak_no_question_text_no_touch_validation_bodyfree(
        p8_question_design_material_candidate_handoff=r20,
        additional_bodyfree_materials_to_scan=(
            {"material_id": "bad_body_material", "comment_text": "surface body must not be retained"},
        ),
    )
    assert body_blocked["final_validation_status"] == "FINAL_VALIDATION_BLOCKED_BY_BODY_LEAK"
    assert body_blocked["body_leak_detected"] is True
    assert body_blocked["final_validation_passed"] is False

    no_touch_blocked = r54.build_p7_r54_final_no_body_leak_no_question_text_no_touch_validation_bodyfree(
        p8_question_design_material_candidate_handoff=r20,
        additional_bodyfree_materials_to_scan=(
            {"material_id": "bad_touch_material", "api_route_changed_here": True},
        ),
    )
    assert no_touch_blocked["final_validation_status"] == "FINAL_VALIDATION_BLOCKED_BY_NO_TOUCH_VIOLATION"
    assert no_touch_blocked["no_touch_violation_detected"] is True
    assert "api_route_changed_here" in no_touch_blocked["no_touch_touched_refs"]
    assert no_touch_blocked["final_validation_passed"] is False

    assert r54.assert_p7_r54_final_no_body_leak_no_question_text_no_touch_validation_bodyfree_contract(question_blocked) is True
    assert r54.assert_p7_r54_final_no_body_leak_no_question_text_no_touch_validation_bodyfree_contract(body_blocked) is True
    assert r54.assert_p7_r54_final_no_body_leak_no_question_text_no_touch_validation_bodyfree_contract(no_touch_blocked) is True
    _assert_body_free_no_runtime_promotion(question_blocked)
    _assert_body_free_no_runtime_promotion(body_blocked)
    _assert_body_free_no_runtime_promotion(no_touch_blocked)


def test_r54_r21_contract_rejects_promotions_or_false_clean_status(tmp_path) -> None:
    validation = r54.build_p7_r54_final_no_body_leak_no_question_text_no_touch_validation_bodyfree(
        p8_question_design_material_candidate_handoff=_r20_from_summary(_p8_material_candidate_summary(tmp_path)),
    )
    for key in (
        "p8_start_allowed",
        "p7_complete",
        "release_allowed",
        "hold004_close_allowed",
        "p5_human_blind_qa_confirmed_final",
        "p5_decision_finalized_here",
        "p6_limited_human_readfeel_start_allowed",
        "actual_human_review_run_here",
        "actual_manual_review_run_here",
        "body_full_packet_generated_here",
        "actual_body_full_packet_generated_here",
        "question_text_included",
        "draft_question_text_included",
        "api_route_changed_here",
        "db_schema_changed_here",
        "rn_visible_contract_changed_here",
        "runtime_changed_here",
        "question_api_implemented",
        "question_db_schema_implemented",
        "question_rn_ui_implemented",
        "question_trigger_logic_implemented",
        "question_response_key_implemented",
    ):
        mutated = deepcopy(validation)
        mutated[key] = True
        with pytest.raises(ValueError):
            r54.assert_p7_r54_final_no_body_leak_no_question_text_no_touch_validation_bodyfree_contract(mutated)
