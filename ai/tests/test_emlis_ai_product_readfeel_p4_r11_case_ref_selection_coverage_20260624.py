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
from fixtures.emlis_ai_product_readfeel_p4_target_cases_20260610 import (
    build_product_readfeel_p4_target_case_selection_from_p3_9_20260610,
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
    '"p8_start_allowed": true',
    '"release_allowed": true',
    '"runtime_changed_here": true',
    '"question_implementation_started_here": true',
    '"actual_human_review_run_here": true',
    '"actual_rating_rows_materialized_here": true',
    '"actual_question_need_observation_rows_materialized_here": true',
    '"actual_audit_rows_created_here": true',
    '"json_schema_file_materialized": true',
    '"case_ref_supplemented_by_fabrication": true',
)


def _dump(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True).lower()


def _assert_body_free_selection(value: object) -> None:
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


def _scope(baseline: list[dict[str, object]] | None = None) -> dict[str, object]:
    return r11.build_product_readfeel_p4_r11_residual_family_scope_matrix_20260624(
        baseline_public_safe_index=baseline or _baseline(),
        run_id="p4_r11_r3_test_scope",
    )


def _selection(baseline: list[dict[str, object]] | None = None) -> dict[str, object]:
    source = baseline or _baseline()
    return r11.build_product_readfeel_p4_r11_case_ref_selection_coverage_audit_20260624(
        scope_matrix=_scope(source),
        baseline_public_safe_index=source,
        run_id="p4_r11_r3_test_selection",
    )


def test_r11_3_case_ref_selection_selects_24_unique_body_free_refs_without_actual_audit_rows() -> None:
    selection = _selection()
    summary = selection["summary"]
    rows = selection["selected_case_ref_rows"]
    audit_rows = selection["audit_rows"]

    assert selection["schema_version"] == r11.PRODUCT_READFEEL_P4_R11_CASE_REF_SELECTION_VERSION_20260624
    assert selection["source_step"] == r11.P4_R11_R3_STEP_REF_20260624
    assert selection["case_ref_selection_performed_here"] is True
    assert selection["actual_audit_rows_created_here"] is False
    assert selection["case_ref_supplemented_by_fabrication"] is False
    assert tuple(selection["implemented_steps"]) == r11.P4_R11_R3_IMPLEMENTED_STEPS_20260624
    assert selection["next_implementation_step"] == r11.P4_R11_R4_STEP_REF_20260624

    assert summary["coverage_status"] == "complete"
    assert summary["target_row_count"] == 24
    assert summary["selected_ref_row_count"] == 24
    assert summary["selected_unique_case_ref_count"] == 24
    assert summary["insufficient_scope_group_ids"] == []
    assert summary["case_ref_selection_performed_here"] is True
    assert summary["case_ref_supplemented_by_fabrication"] is False
    assert summary["raw_input_or_local_synthetic_body_brought_into_summary"] is False
    assert summary["actual_audit_rows_created_here"] is False
    assert summary["p4_r11_audit_rows_not_r54_rating_rows"] is True
    assert summary["p4_r11_audit_rows_not_question_observation_rows"] is True

    assert len(rows) == 24
    assert len(audit_rows) == 24
    assert len({row["case_ref_id"] for row in rows}) == 24
    assert set(summary["selected_counts_by_scope_group"]) == set(r11.P4_R11_TARGET_SCOPE_GROUP_IDS_20260624)
    assert all(count == 4 for count in summary["selected_counts_by_scope_group"].values())

    for row in rows:
        assert row["case_origin"] == "p3_baseline_public_safe_index"
        assert row["case_ref_selection_performed_here"] is True
        assert row["actual_audit_rows_created_here"] is False
        assert row["local_case_material_retained_here"] is False
        assert row["local_synthetic_body_retained_here"] is False
        assert row["body_free"] is True
        assert row["comment_text_body_included"] is False
        assert row["surface_body_included"] is False
        assert row["case_ref_id"].startswith("p3-")
        assert row["residual_family_id"] in r11.P4_R11_TARGET_SCOPE_GROUP_IDS_20260624
        assert len(row["required_surface_role_ids"]) >= 5

    for row in audit_rows:
        assert row["source_step"] == r11.P4_R11_R3_STEP_REF_20260624
        assert row["case_ref_selection_performed_here"] is True
        assert row["actual_audit_rows_created_here"] is False
        assert row["material_route_audit_status"] == "not_run_r11_4"
        assert row["surface_path_audit_status"] == "not_run_r11_5"
        assert row["surface_specificity_role_audit_status"] == "not_run_r11_6"
        assert row["verdict_status"] == "not_run_r11_7"
        assert row["history_line_surface_used"] is False

    r11.assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(selection)
    _assert_body_free_selection(selection)


def test_r11_3_public_summary_is_body_free_and_keeps_case_ref_rows_only() -> None:
    selection = _selection()
    public_summary = r11.build_product_readfeel_p4_r11_public_summary_20260624(selection)
    dumped = r11.dump_product_readfeel_p4_r11_public_summary_20260624(selection)

    assert public_summary["schema_version"] == r11.PRODUCT_READFEEL_P4_R11_AUDIT_PUBLIC_SUMMARY_VERSION_20260624
    assert public_summary["source_step"] == r11.P4_R11_R3_STEP_REF_20260624
    assert public_summary["case_ref_selection_performed_here"] is True
    assert public_summary["actual_audit_rows_created_here"] is False
    assert public_summary["selected_ref_row_count"] == 24
    assert len(public_summary["selected_case_ref_rows"]) == 24
    assert '"case_ref_selection_performed_here":true' in dumped

    _assert_body_free_selection(public_summary)
    _assert_body_free_selection(json.loads(dumped))


def test_r11_3_insufficient_coverage_is_reported_without_fabricating_or_reusing_missing_family() -> None:
    baseline = [case for case in _baseline() if case.get("family") != "long_meaning_arc"]
    selection = _selection(baseline)
    summary = selection["summary"]

    assert summary["coverage_status"] == "insufficient_public_safe_case_refs"
    assert r11.SCOPE_GROUP_LONG_MEANING_ARC in summary["insufficient_scope_group_ids"]
    assert summary["candidate_counts_by_scope_group"][r11.SCOPE_GROUP_LONG_MEANING_ARC] == 0
    assert summary["selected_counts_by_scope_group"][r11.SCOPE_GROUP_LONG_MEANING_ARC] == 0
    assert summary["selected_ref_row_count"] < 24
    assert summary["selected_unique_case_ref_count"] == summary["selected_ref_row_count"]
    assert summary["case_ref_supplemented_by_fabrication"] is False
    assert summary["raw_input_or_local_synthetic_body_brought_into_summary"] is False
    assert selection["case_ref_supplemented_by_fabrication"] is False
    assert selection["actual_audit_rows_created_here"] is False

    _assert_body_free_selection(selection)


def test_r11_3_rejects_body_bearing_baseline_source_instead_of_sanitizing_it_late() -> None:
    baseline = _baseline()
    unsafe = deepcopy(baseline[0])
    unsafe["memo"] = "raw local input must not enter R11-3"
    baseline.append(unsafe)

    with pytest.raises(ValueError):
        r11.build_product_readfeel_p4_r11_case_ref_selection_coverage_audit_20260624(
            scope_matrix=_scope(),
            baseline_public_safe_index=baseline,
            run_id="p4_r11_r3_unsafe_baseline",
        )


def test_r11_3_contract_scope_guard_still_rejects_case_ref_selection_true_for_r11_0_r11_1_materials() -> None:
    selection = _selection()
    with pytest.raises(ValueError):
        r11.assert_product_readfeel_p4_r11_contract_scope_meta_only_20260624(selection)

    r11.assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(selection)


def test_r11_3_can_attach_existing_p4_target_selection_ids_without_body_material() -> None:
    baseline = _baseline()
    p4_target_selection = build_product_readfeel_p4_target_case_selection_from_p3_9_20260610(
        baseline_public_safe_index=baseline,
        run_id="p4_r11_r3_existing_p4_selection_source",
    )
    selection = r11.build_product_readfeel_p4_r11_case_ref_selection_coverage_audit_20260624(
        scope_matrix=_scope(baseline),
        baseline_public_safe_index=baseline,
        p4_target_case_selection=p4_target_selection,
        run_id="p4_r11_r3_with_existing_p4_selection_ids",
    )

    rows_with_existing_p4_selection = [
        row
        for row in selection["selected_case_ref_rows"]
        if row["p4_target_selection_groups"]
        or row["p4_target_blocker_ids"]
        or row["p4_target_layer_ids"]
    ]
    assert rows_with_existing_p4_selection
    for row in rows_with_existing_p4_selection:
        assert row["case_ref_id"].startswith("p3-")
        assert row["actual_audit_rows_created_here"] is False
        assert row["local_case_material_retained_here"] is False
        assert row["comment_text_body_included"] is False
        assert row["surface_text_included"] is False

    r11.assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(selection)
    _assert_body_free_selection(selection)
