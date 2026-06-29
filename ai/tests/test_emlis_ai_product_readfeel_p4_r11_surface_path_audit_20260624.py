# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache

import pytest

import emlis_ai_product_readfeel_p4_r11_residual_family_surface_audit as r11
from fixtures.emlis_ai_product_readfeel_baseline_cases_20260609 import (
    build_product_readfeel_baseline_cases_20260609,
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
    '"p8_start_allowed": true',
    '"release_allowed": true',
    '"runtime_changed_here": true',
    '"question_implementation_started_here": true',
    '"actual_human_review_run_here": true',
    '"actual_rating_rows_materialized_here": true',
    '"actual_question_need_observation_rows_materialized_here": true',
    '"actual_audit_rows_created_here": true',
    '"json_schema_file_materialized": true',
    '"runtime_candidate_body_retained_here": true',
    '"p5_history_line_mixed_into_current_only_audit": true',
)


def _dump(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True).lower()


def _assert_body_free(value: object) -> None:
    dumped = _dump(value)
    for token in FORBIDDEN_BODY_TOKENS:
        assert token not in dumped
    for token in FORBIDDEN_PROMOTION_TOKENS:
        assert token not in dumped


@lru_cache(maxsize=1)
def _cached_sources() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    return (
        build_product_readfeel_baseline_public_safe_index_20260609(),
        build_product_readfeel_baseline_cases_20260609(),
    )


def _baseline() -> list[dict[str, object]]:
    return deepcopy(_cached_sources()[0])


def _local_cases() -> list[dict[str, object]]:
    return deepcopy(_cached_sources()[1])


def _material_audit() -> dict[str, object]:
    baseline = _baseline()
    scope = r11.build_product_readfeel_p4_r11_residual_family_scope_matrix_20260624(
        baseline_public_safe_index=baseline,
        run_id="p4_r11_r5_test_scope",
    )
    selection = r11.build_product_readfeel_p4_r11_case_ref_selection_coverage_audit_20260624(
        scope_matrix=scope,
        baseline_public_safe_index=baseline,
        run_id="p4_r11_r5_test_selection",
    )
    return r11.build_product_readfeel_p4_r11_material_route_audit_20260624(
        case_ref_selection_payload=selection,
        local_baseline_cases=_local_cases(),
        run_id="p4_r11_r5_test_material",
    )


def _surface_path_audit() -> dict[str, object]:
    return r11.build_product_readfeel_p4_r11_surface_path_audit_20260624(
        material_route_audit_payload=_material_audit(),
        local_baseline_cases=_local_cases(),
        run_id="p4_r11_r5_test_surface_path",
    )


def test_r11_5_surface_path_audit_classifies_route_kind_without_history_or_candidate_bodies() -> None:
    payload = _surface_path_audit()
    summary = payload["summary"]
    rows = payload["audit_rows"]

    assert payload["schema_version"] == r11.PRODUCT_READFEEL_P4_R11_SURFACE_PATH_AUDIT_VERSION_20260624
    assert payload["source_step"] == r11.P4_R11_R5_STEP_REF_20260624
    assert tuple(payload["implemented_steps"]) == r11.P4_R11_R5_IMPLEMENTED_STEPS_20260624
    assert payload["next_implementation_step"] == r11.P4_R11_R6_STEP_REF_20260624
    assert payload["material_route_audit_performed_here"] is True
    assert payload["surface_path_audit_performed_here"] is True
    assert payload["actual_audit_rows_created_here"] is False

    assert summary["audited_row_count"] == 24
    assert summary["history_line_surface_used_count"] == 0
    assert summary["history_line_candidate_seen_but_not_used_count"] >= 1
    assert summary["limited_grounding_reception_surface_used_count"] >= 1
    assert summary["complete_initial_surface_recomposition_used_count"] >= 1
    assert summary["runtime_candidate_body_retained_here"] is False
    assert summary["candidate_source_kind_only_retained_here"] is True
    assert summary["p5_history_line_mixed_into_current_only_audit"] is False
    assert summary["actual_rating_rows_materialized_here"] is False
    assert summary["actual_question_need_observation_rows_materialized_here"] is False

    for row in rows:
        audit = row["surface_path_audit"]
        assert row["source_step"] == r11.P4_R11_R5_STEP_REF_20260624
        assert row["material_route_audit_performed_here"] is True
        assert row["surface_path_audit_performed_here"] is True
        assert row["surface_specificity_role_audit_status"] == "not_run_r11_6"
        assert row["verdict_status"] == "not_run_r11_7"
        assert row["actual_audit_rows_created_here"] is False
        assert row["local_case_material_retained_here"] is False
        assert audit["surface_path_audit_status"] == "audited_r11_5"
        assert audit["surface_path_audit_performed_here"] is True
        assert audit["selected_surface_route_kind"] in r11.P4_R11_SURFACE_ROUTE_KINDS_20260624
        assert isinstance(audit["selected_public_candidate_source_kind"], str)
        assert audit["history_line_surface_used"] is False
        assert audit["p5_history_line_mixed_into_current_only_audit"] is False
        assert audit["runtime_candidate_body_retained_here"] is False
        assert audit["candidate_source_kind_only_retained_here"] is True
        assert audit["body_free"] is True

    r11.assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(payload)
    _assert_body_free(payload)


def test_r11_5_public_summary_remains_body_free_and_includes_material_and_route_ids_only() -> None:
    payload = _surface_path_audit()
    public_summary = r11.build_product_readfeel_p4_r11_public_summary_20260624(payload)
    dumped = r11.dump_product_readfeel_p4_r11_public_summary_20260624(payload)

    assert public_summary["schema_version"] == r11.PRODUCT_READFEEL_P4_R11_AUDIT_PUBLIC_SUMMARY_VERSION_20260624
    assert public_summary["source_step"] == r11.P4_R11_R5_STEP_REF_20260624
    assert public_summary["selected_ref_row_count"] == 24
    assert len(public_summary["selected_case_ref_rows"]) == 24
    assert any(row["material_quality"] for row in public_summary["selected_case_ref_rows"])
    assert any(row["selected_surface_route_kind"] for row in public_summary["selected_case_ref_rows"])
    assert '"surface_path_audit_status":"audited_r11_5"' in dumped

    _assert_body_free(public_summary)
    _assert_body_free(json.loads(dumped))


def test_r11_5_requires_r11_4_material_route_payload_before_surface_path_audit() -> None:
    material_payload = _material_audit()
    material_payload["audit_rows"][0]["material_route_audit_performed_here"] = False

    with pytest.raises(ValueError):
        r11.build_product_readfeel_p4_r11_surface_path_audit_20260624(
            material_route_audit_payload=material_payload,
            local_baseline_cases=_local_cases(),
            run_id="p4_r11_r5_missing_material_precondition",
        )
