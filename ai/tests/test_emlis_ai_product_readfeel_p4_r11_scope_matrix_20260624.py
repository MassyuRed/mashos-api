# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache
from typing import Any

import pytest

import emlis_ai_p7_r55_r54_evidence_reconcile_r52_reintake_decision_materialization as r55
import emlis_ai_product_readfeel_p4_r11_residual_family_surface_audit as r11
from emlis_ai_product_readfeel_current_output_inventory import PRODUCT_READFEEL_REQUIRED_FAMILIES
from fixtures.emlis_ai_product_readfeel_baseline_cases_20260609 import (
    build_product_readfeel_baseline_public_safe_index_20260609,
)

FORBIDDEN_DUMP_TOKENS = (
    '"raw_input":',
    '"current_input":',
    '"memo":',
    '"memo_action":',
    '"comment_text":',
    '"comment_text_body":',
    '"candidate_body":',
    '"surface_text":',
    '"reviewer_note":',
    '"question_text":',
    '"draft_question_text":',
    '"stdout":',
    '"stderr":',
    '"traceback":',
)
FORBIDDEN_TRUE_TOKENS = (
    '"p5_human_blind_qa_confirmed": true',
    '"p5_human_blind_qa_confirmed_final": true',
    '"p6_limited_human_readfeel_start_allowed": true',
    '"p6_start_allowed": true',
    '"p8_start_allowed": true',
    '"p7_complete": true',
    '"release_allowed": true',
    '"runtime_changed_here": true',
    '"api_db_rn_response_key_changed_here": true',
    '"question_implementation_started_here": true',
    '"actual_human_review_run_here": true',
    '"actual_rating_rows_materialized_here": true',
    '"actual_question_need_observation_rows_materialized_here": true',
    '"actual_audit_rows_created_here": true',
    '"case_ref_selection_performed_here": true',
    '"runtime_family_rename_applied": true',
    '"new_runtime_family_constant_added": true',
)


def _dump(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True).lower()


def _assert_body_free_no_promotion(value: object) -> None:
    dumped = _dump(value)
    for token in FORBIDDEN_DUMP_TOKENS:
        assert token not in dumped
    for token in FORBIDDEN_TRUE_TOKENS:
        assert token not in dumped


@lru_cache(maxsize=1)
def _cached_r55_summary() -> tuple[dict[str, Any]]:
    summary = r55.build_p7_r55_final_summary_bodyfree()
    assert r55.assert_p7_r55_final_summary_bodyfree_contract(summary) is True
    return (summary,)


def _r55_summary() -> dict[str, Any]:
    return deepcopy(_cached_r55_summary()[0])


@lru_cache(maxsize=1)
def _cached_baseline() -> tuple[list[dict[str, Any]]]:
    return (build_product_readfeel_baseline_public_safe_index_20260609(),)


def _baseline() -> list[dict[str, Any]]:
    return deepcopy(_cached_baseline()[0])


def _freeze() -> dict[str, Any]:
    return r11.build_product_readfeel_p4_r11_contract_freeze_20260624(
        r55_final_summary=_r55_summary(),
        run_id="p4_r11_test_contract_freeze",
    )


def _scope() -> dict[str, Any]:
    return r11.build_product_readfeel_p4_r11_residual_family_scope_matrix_20260624(
        contract_freeze=_freeze(),
        baseline_public_safe_index=_baseline(),
        run_id="p4_r11_test_scope_matrix",
    )


def _groups_by_id(scope: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(group["scope_group_id"]): dict(group) for group in scope["scope_groups"]}


def test_r11_0_contract_freeze_preserves_r10_r55_and_does_not_promote_p5_p6_p8_release() -> None:
    freeze = _freeze()

    assert freeze["schema_version"] == r11.PRODUCT_READFEEL_P4_R11_CONTRACT_FREEZE_VERSION_20260624
    assert freeze["source_step"] == r11.P4_R11_R0_STEP_REF_20260624
    assert freeze["source_phase"] == r11.PRODUCT_READFEEL_P4_R11_PHASE_20260624
    assert freeze["contract_freeze_fixed"] is True
    assert freeze["p4_r11_runtime_no_touch_step"] is True

    assert freeze["r10_closed_red_ref"] == r11.P4_R11_R10_CLOSED_RED_REF_20260624
    assert freeze["r10_closed_red_reopened_here"] is False
    assert set(r11.P4_R11_R10_BLOCKER_KIND_REFS_20260624).issubset(set(freeze["r10_blocker_kind_refs"]))

    assert freeze["r55_decision_ref"] == r11.P4_R11_R55_DECISION_REF_20260624
    assert freeze["r55_next_required_step"] == r11.P4_R11_R55_NEXT_REQUIRED_STEP_REF_20260624
    assert freeze["next_required_step"] == r11.P4_R11_R55_NEXT_REQUIRED_STEP_REF_20260624
    assert freeze["r55_decision_preserved"] is True
    assert freeze["r55_not_replaced_by_p4_r11"] is True

    assert freeze["actual_review_evidence_complete"] is False
    assert freeze["rating_row_count"] == 0
    assert freeze["question_observation_row_count"] == 0
    assert freeze["disposal_verified"] is False
    assert freeze["p6_hold"] is True
    assert freeze["p8_hold"] is True
    assert freeze["release_hold"] is True
    assert freeze["p6_limited_human_readfeel_start_allowed"] is False
    assert freeze["p8_start_allowed"] is False
    assert freeze["p7_complete"] is False
    assert freeze["release_allowed"] is False
    assert freeze["scope_matrix_fixed_here"] is False
    assert freeze["case_ref_selection_performed_here"] is False
    assert freeze["actual_audit_rows_created_here"] is False
    assert freeze["runtime_changed_here"] is False
    assert freeze["question_implementation_started_here"] is False
    assert tuple(freeze["implemented_steps"]) == r11.P4_R11_R0_IMPLEMENTED_STEPS_20260624
    assert freeze["next_implementation_step"] == r11.P4_R11_R1_STEP_REF_20260624

    r11.assert_product_readfeel_p4_r11_contract_scope_meta_only_20260624(freeze)
    _assert_body_free_no_promotion(freeze)


@pytest.mark.parametrize(
    "key",
    [
        "p8_start_allowed",
        "release_allowed",
        "p6_limited_human_readfeel_start_allowed",
        "runtime_changed_here",
        "question_implementation_started_here",
        "api_db_rn_response_key_changed_here",
        "actual_human_review_run_here",
        "actual_rating_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "case_ref_selection_performed_here",
        "actual_audit_rows_created_here",
        "runtime_family_rename_applied",
        "new_runtime_family_constant_added",
    ],
)
def test_r11_0_contract_guard_rejects_promotion_runtime_question_review_and_scope_overreach(key: str) -> None:
    freeze = _freeze()
    freeze[key] = True
    with pytest.raises(ValueError):
        r11.assert_product_readfeel_p4_r11_contract_scope_meta_only_20260624(freeze)


def test_r11_0_contract_guard_rejects_body_bearing_payload_and_bad_r55_decision() -> None:
    unsafe = _freeze()
    unsafe["summary"] = {"comment_text": "Emlis本文をR11-0へ残してはいけない"}
    with pytest.raises(ValueError):
        r11.assert_product_readfeel_p4_r11_contract_scope_meta_only_20260624(unsafe)

    bad_r55 = _r55_summary()
    bad_r55["r55_decision_ref"] = "R55_P8_START_ALLOWED_SHOULD_NOT_EXIST"
    with pytest.raises(ValueError):
        r11.build_product_readfeel_p4_r11_contract_freeze_20260624(r55_final_summary=bad_r55)


def test_r11_1_scope_matrix_freezes_six_residual_groups_with_24_target_rows_without_runtime_family_rename() -> None:
    scope = _scope()
    summary = scope["summary"]
    groups = _groups_by_id(scope)

    assert scope["schema_version"] == r11.PRODUCT_READFEEL_P4_R11_SCOPE_MATRIX_VERSION_20260624
    assert scope["source_step"] == r11.P4_R11_R1_STEP_REF_20260624
    assert scope["contract_freeze_schema_version"] == r11.PRODUCT_READFEEL_P4_R11_CONTRACT_FREEZE_VERSION_20260624
    assert scope["scope_matrix_fixed_here"] is True
    assert scope["case_ref_selection_performed_here"] is False
    assert scope["actual_audit_rows_created_here"] is False
    assert tuple(scope["implemented_steps"]) == r11.P4_R11_R1_IMPLEMENTED_STEPS_20260624
    assert scope["next_implementation_step"] == r11.P4_R11_R2_STEP_REF_20260624

    assert summary["target_scope_group_ids"] == list(r11.P4_R11_TARGET_SCOPE_GROUP_IDS_20260624)
    assert summary["target_scope_group_count"] == 6
    assert summary["minimum_case_refs_per_scope_group"] == 4
    assert summary["target_row_count"] == 24
    assert summary["coverage_status"] == "complete"
    assert summary["case_coverage_ready_for_r11_3"] is True
    assert summary["scope_matrix_only"] is True
    assert summary["case_ref_selection_performed_here"] is False
    assert summary["actual_audit_rows_created_here"] is False
    assert summary["p4_r11_does_not_replace_r54_actual_review"] is True
    assert summary["p4_r11_audit_rows_not_r54_rating_rows"] is True
    assert summary["p4_r11_audit_rows_not_question_observation_rows"] is True
    assert summary["change_future_intention_transition_is_runtime_family"] is False
    assert summary["runtime_family_rename_applied"] is False
    assert summary["new_runtime_family_constant_added"] is False
    assert summary["p8_start_allowed"] is False
    assert summary["release_allowed"] is False

    assert set(groups) == set(r11.P4_R11_TARGET_SCOPE_GROUP_IDS_20260624)
    for group in groups.values():
        assert group["minimum_case_ref_count"] == 4
        assert group["candidate_case_ref_count"] >= 4
        assert group["coverage_status"] == "candidate_refs_available"
        assert group["coverage_below_minimum"] is False
        assert group["runtime_family_rename_applied"] is False
        assert group["new_runtime_family_constant_added"] is False
        assert group["case_ref_selection_performed_here"] is False
        assert group["actual_audit_rows_created_here"] is False
        assert group["comment_text_body_included"] is False
        assert group["surface_body_included"] is False
        assert group["runtime_changed_here"] is False
        assert group["fixed_sentence_template_used"] is False

    change = groups[r11.SCOPE_GROUP_CHANGE_FUTURE_INTENTION_TRANSITION]
    assert change["residual_focus_slice_only"] is True
    assert change["scope_group_id"] not in PRODUCT_READFEEL_REQUIRED_FAMILIES
    assert change["candidate_case_ref_count"] == 15
    assert "future_direction" in change["residual_focus_slice_ids"]
    assert "recovered_energy" in change["residual_focus_slice_ids"]

    assert groups[r11.SCOPE_GROUP_DAILY_POSITIVE_RECOVERY]["candidate_case_ref_count"] == 10
    assert groups[r11.SCOPE_GROUP_RELATIONSHIP_GRATITUDE_RECOVERY]["candidate_case_ref_count"] == 15
    assert groups[r11.SCOPE_GROUP_LONG_MEANING_ARC]["candidate_case_ref_count"] == 5
    assert groups[r11.SCOPE_GROUP_STRUCTURE_QUESTION]["candidate_case_ref_count"] == 5
    assert groups[r11.SCOPE_GROUP_SELF_DENIAL_YELLOW_REMAINDER]["candidate_case_ref_count"] == 5

    r11.assert_product_readfeel_p4_r11_contract_scope_meta_only_20260624(scope)
    _assert_body_free_no_promotion(scope)


def test_r11_1_scope_matrix_does_not_materialize_case_refs_audit_rows_json_schema_or_question_design() -> None:
    scope = _scope()
    dumped = _dump(scope)

    assert '"case_ref_selection_performed_here": true' not in dumped
    assert '"actual_audit_rows_created_here": true' not in dumped
    assert '"json_schema_file_materialized": true' not in dumped
    assert '"question_trigger_logic_implemented": true' not in dumped
    assert '"p8_question_implementation_spec_finalized_here": true' not in dumped
    assert '"runtime_family_rename_applied": true' not in dumped
    assert '"new_runtime_family_constant_added": true' not in dumped
    assert '"p3-daily_positive-001"' not in dumped
    assert '"p3-long_meaning_arc-001"' not in dumped

    public_summary = r11.build_product_readfeel_p4_r11_contract_scope_public_summary_20260624(scope)
    assert public_summary["schema_version"] == r11.PRODUCT_READFEEL_P4_R11_PUBLIC_SUMMARY_VERSION_20260624
    assert len(public_summary["scope_group_refs"]) == 6
    assert public_summary["summary"]["target_row_count"] == 24
    _assert_body_free_no_promotion(public_summary)

    dumped_public = r11.dump_product_readfeel_p4_r11_contract_scope_public_summary_20260624(scope)
    assert '"comment_text"' not in dumped_public
    assert '"candidate_body"' not in dumped_public
    assert '"p8_start_allowed":true' not in dumped_public
