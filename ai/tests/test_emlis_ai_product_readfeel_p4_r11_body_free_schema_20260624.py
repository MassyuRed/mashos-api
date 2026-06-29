# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache

import pytest

import emlis_ai_product_readfeel_p4_r11_residual_family_surface_audit as r11
from fixtures.emlis_ai_product_readfeel_baseline_cases_20260609 import (
    build_product_readfeel_baseline_public_safe_index_20260609,
)

FORBIDDEN_BODY_TOKENS = (
    '"raw_input":',
    '"raw_text":',
    '"current_input":',
    '"memo":',
    '"memo_text":',
    '"memo_action":',
    '"comment_text":',
    '"comment_text_body":',
    '"candidate_body":',
    '"surface_text":',
    '"display_text":',
    '"visible_text":',
    '"reviewer_note":',
    '"question_text":',
    '"draft_question_text":',
    '"stdout":',
    '"stderr":',
    '"traceback_body":',
)

FORBIDDEN_PROMOTION_TOKENS = (
    '"p5_human_blind_qa_confirmed": true',
    '"p5_human_blind_qa_confirmed_final": true',
    '"p6_limited_human_readfeel_start_allowed": true',
    '"p6_start_allowed": true',
    '"p8_start_allowed": true',
    '"p7_complete": true',
    '"release_allowed": true',
    '"runtime_changed_here": true',
    '"question_implementation_started_here": true',
    '"actual_human_review_run_here": true',
    '"actual_rating_rows_materialized_here": true',
    '"actual_question_need_observation_rows_materialized_here": true',
    '"actual_audit_rows_created_here": true',
    '"json_schema_file_materialized": true',
)


def _dump(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True).lower()


def _assert_body_free_without_promotion(value: object) -> None:
    dumped = _dump(value)
    for token in FORBIDDEN_BODY_TOKENS:
        assert token not in dumped
    for token in FORBIDDEN_PROMOTION_TOKENS:
        assert token not in dumped


@lru_cache(maxsize=1)
def _cached_baseline() -> tuple[list[dict[str, object]]]:
    return (build_product_readfeel_baseline_public_safe_index_20260609(),)


def _baseline() -> list[dict[str, object]]:
    return deepcopy(_cached_baseline()[0])


def _scope() -> dict[str, object]:
    return r11.build_product_readfeel_p4_r11_residual_family_scope_matrix_20260624(
        baseline_public_safe_index=_baseline(),
        run_id="p4_r11_r2_test_scope",
    )


def _scope_group(group_id: str) -> dict[str, object]:
    scope = _scope()
    return next(dict(group) for group in scope["scope_groups"] if group["scope_group_id"] == group_id)


def test_r11_2_audit_row_shell_is_body_free_meta_only_and_not_actual_audit_result() -> None:
    group = _scope_group(r11.SCOPE_GROUP_DAILY_POSITIVE_RECOVERY)
    row = r11.build_product_readfeel_p4_r11_audit_row_20260624(
        case_ref_id="p4-r11-r2-row-shell-001",
        residual_family_id=r11.SCOPE_GROUP_DAILY_POSITIVE_RECOVERY,
        residual_focus_slice_ids=group["residual_focus_slice_ids"],
        priority_band=group["priority_band"],
        required_surface_role_ids=group["required_surface_role_ids"],
        run_id="p4_r11_r2_test_row_shell",
    )

    assert row["schema_version"] == r11.PRODUCT_READFEEL_P4_R11_AUDIT_ROW_VERSION_20260624
    assert row["source_step"] == r11.P4_R11_R2_STEP_REF_20260624
    assert row["case_ref_id"] == "p4-r11-r2-row-shell-001"
    assert row["residual_family_id"] == r11.SCOPE_GROUP_DAILY_POSITIVE_RECOVERY
    assert row["body_free_audit_row_shell_created_here"] is True
    assert row["case_ref_selection_performed_here"] is False
    assert row["actual_audit_rows_created_here"] is False
    assert row["actual_rating_rows_materialized_here"] is False
    assert row["actual_question_need_observation_rows_materialized_here"] is False
    assert row["material_route_audit_status"] == "not_run_r11_4"
    assert row["surface_path_audit_status"] == "not_run_r11_5"
    assert row["surface_specificity_role_audit_status"] == "not_run_r11_6"
    assert row["verdict_status"] == "not_run_r11_7"
    assert row["decision_handoff_status"] == "not_run_r11_8"
    assert row["verdict"] is None
    assert row["next_action"] == "not_run_r11_7"
    assert row["json_schema_file_materialized"] is False
    assert row["runtime_changed_here"] is False
    assert row["p8_start_allowed"] is False
    assert row["release_allowed"] is False
    assert row["body_boundary"]["body_free"] is True
    assert row["body_boundary"]["comment_text_body_included"] is False
    assert row["p5_p8_escape_boundary"]["p5_masking_forbidden"] is True
    assert row["p5_p8_escape_boundary"]["p8_question_escape_forbidden"] is True

    r11.assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(row)
    _assert_body_free_without_promotion(row)


def test_r11_2_audit_root_keeps_schema_as_code_only_and_does_not_run_case_selection() -> None:
    payload = r11.build_product_readfeel_p4_r11_residual_surface_audit_20260624(
        run_id="p4_r11_r2_test_audit_root",
    )
    summary = payload["summary"]

    assert payload["schema_version"] == r11.PRODUCT_READFEEL_P4_R11_RESIDUAL_SURFACE_AUDIT_VERSION_20260624
    assert payload["source_step"] == r11.P4_R11_R2_STEP_REF_20260624
    assert payload["body_free_audit_row_guard_fixed_here"] is True
    assert payload["case_ref_selection_performed_here"] is False
    assert payload["actual_audit_rows_created_here"] is False
    assert payload["json_schema_file_materialized"] is False
    assert payload["audit_rows"] == []
    assert tuple(payload["implemented_steps"]) == r11.P4_R11_R2_IMPLEMENTED_STEPS_20260624
    assert payload["next_implementation_step"] == r11.P4_R11_R3_STEP_REF_20260624

    assert summary["target_row_count"] == 24
    assert summary["audit_row_shell_count"] == 0
    assert summary["audited_row_count"] == 0
    assert summary["coverage_status"] == "not_run_r11_3"
    assert summary["case_ref_selection_performed_here"] is False
    assert summary["actual_audit_rows_created_here"] is False
    assert summary["p4_r11_audit_rows_not_r54_rating_rows"] is True
    assert summary["p4_r11_audit_rows_not_question_observation_rows"] is True

    public_summary = r11.build_product_readfeel_p4_r11_public_summary_20260624(payload)
    assert public_summary["case_ref_selection_performed_here"] is False
    assert public_summary["selected_case_ref_rows"] == []

    _assert_body_free_without_promotion(payload)
    _assert_body_free_without_promotion(public_summary)


@pytest.mark.parametrize(
    "key",
    [
        "raw_input",
        "raw_text",
        "source_text",
        "input",
        "input_text",
        "user_input",
        "current_input",
        "memo",
        "memo_text",
        "memo_action",
        "comment_text",
        "commentText",
        "comment_text_body",
        "candidate_body",
        "reply_text",
        "surface_text",
        "display_text",
        "visible_text",
        "reviewer_note",
        "question_text",
        "draft_question_text",
        "stdout",
        "stderr",
        "traceback_body",
        "body",
        "text",
    ],
)
def test_r11_2_meta_only_guard_rejects_body_keys(key: str) -> None:
    with pytest.raises(ValueError):
        r11.assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(
            {"schema_version": "bad", key: "body must not enter R11-2"}
        )


@pytest.mark.parametrize(
    "flag",
    [
        "p8_start_allowed",
        "release_allowed",
        "runtime_changed_here",
        "question_implementation_started_here",
        "actual_human_review_run_here",
        "actual_audit_rows_created_here",
        "actual_rating_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "json_schema_file_materialized",
        "fixed_sentence_template_used",
        "case_specific_runtime_branch",
    ],
)
def test_r11_2_meta_only_guard_rejects_forbidden_true_flags(flag: str) -> None:
    with pytest.raises(ValueError):
        r11.assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(
            {"schema_version": "bad", flag: True}
        )


def test_r11_2_audit_guard_allows_case_ref_selection_flag_only_for_r11_3_materials() -> None:
    payload = {
        "schema_version": "case_ref_selection_flag_only",
        "case_ref_selection_performed_here": True,
        "actual_audit_rows_created_here": False,
        "runtime_changed_here": False,
        "p8_start_allowed": False,
        "release_allowed": False,
    }
    r11.assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(payload)

    with pytest.raises(ValueError):
        r11.assert_product_readfeel_p4_r11_contract_scope_meta_only_20260624(payload)
