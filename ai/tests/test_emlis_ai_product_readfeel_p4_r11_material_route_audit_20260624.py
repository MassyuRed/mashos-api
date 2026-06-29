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
    '"material_quality_forced_to_eligible": true',
    '"low_information_or_limited_grounding_upgraded_here": true',
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


def _selection() -> dict[str, object]:
    baseline = _baseline()
    scope = r11.build_product_readfeel_p4_r11_residual_family_scope_matrix_20260624(
        baseline_public_safe_index=baseline,
        run_id="p4_r11_r4_test_scope",
    )
    return r11.build_product_readfeel_p4_r11_case_ref_selection_coverage_audit_20260624(
        scope_matrix=scope,
        baseline_public_safe_index=baseline,
        run_id="p4_r11_r4_test_selection",
    )


def _material_audit(local_cases: list[dict[str, object]] | None = None) -> dict[str, object]:
    return r11.build_product_readfeel_p4_r11_material_route_audit_20260624(
        case_ref_selection_payload=_selection(),
        local_baseline_cases=local_cases if local_cases is not None else _local_cases(),
        run_id="p4_r11_r4_test_material_route",
    )


def test_r11_4_material_route_audit_normalizes_current_material_ids_without_creating_review_rows() -> None:
    payload = _material_audit()
    summary = payload["summary"]
    rows = payload["audit_rows"]

    assert payload["schema_version"] == r11.PRODUCT_READFEEL_P4_R11_MATERIAL_ROUTE_AUDIT_VERSION_20260624
    assert payload["source_step"] == r11.P4_R11_R4_STEP_REF_20260624
    assert tuple(payload["implemented_steps"]) == r11.P4_R11_R4_IMPLEMENTED_STEPS_20260624
    assert payload["next_implementation_step"] == r11.P4_R11_R5_STEP_REF_20260624
    assert payload["material_route_audit_performed_here"] is True
    assert payload["surface_path_audit_performed_here"] is False
    assert payload["actual_audit_rows_created_here"] is False

    assert summary["audited_row_count"] == 24
    assert summary["target_row_count"] == 24
    assert summary["coverage_status"] == "complete"
    assert summary["current_only_material_available_row_count"] == 24
    assert summary["material_quality_forced_to_eligible"] is False
    assert summary["low_information_or_limited_grounding_upgraded_here"] is False
    assert summary["actual_rating_rows_materialized_here"] is False
    assert summary["actual_question_need_observation_rows_materialized_here"] is False
    assert set(summary["material_quality_counts"]) <= set(r11.P4_R11_ALLOWED_MATERIAL_QUALITIES_20260624)
    assert summary["limited_grounding_row_count"] >= 1

    assert len(rows) == 24
    for row in rows:
        audit = row["material_audit"]
        assert row["source_step"] == r11.P4_R11_R4_STEP_REF_20260624
        assert row["material_route_audit_performed_here"] is True
        assert row["surface_path_audit_performed_here"] is False
        assert row["surface_path_audit_status"] == "not_run_r11_5"
        assert row["verdict_status"] == "not_run_r11_7"
        assert row["actual_audit_rows_created_here"] is False
        assert row["local_case_material_retained_here"] is False
        assert row["local_synthetic_body_retained_here"] is False
        assert audit["material_route_audit_status"] == "audited_r11_4"
        assert audit["material_route_audit_performed_here"] is True
        assert audit["material_quality"] in r11.P4_R11_ALLOWED_MATERIAL_QUALITIES_20260624
        assert isinstance(audit["visible_material_slot_ids"], list)
        assert isinstance(audit["semantic_material_ids"], list)
        assert isinstance(audit["semantic_focus_ids"], list)
        assert audit["semantic_material_count"] == len(audit["semantic_material_ids"])
        assert isinstance(audit["unknown_slot_count"], int)
        assert audit["current_only_material_available"] is True
        assert audit["raw_memo_or_action_retained_here"] is False
        assert audit["material_quality_forced_to_eligible"] is False
        assert audit["low_information_or_limited_grounding_upgraded_here"] is False

    r11.assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(payload)
    _assert_body_free(payload)


def test_r11_4_missing_local_material_is_reported_as_source_unavailable_without_fabrication() -> None:
    local_cases = _local_cases()
    removed_case_ref = _selection()["audit_rows"][0]["case_ref_id"]
    local_cases = [case for case in local_cases if case.get("case_id") != removed_case_ref]

    payload = _material_audit(local_cases)
    row = next(row for row in payload["audit_rows"] if row["case_ref_id"] == removed_case_ref)
    audit = row["material_audit"]

    assert audit["material_quality"] == r11.P4_R11_MATERIAL_QUALITY_SOURCE_UNAVAILABLE_20260624
    assert audit["material_source_available"] is False
    assert audit["current_only_material_available"] is False
    assert audit["material_route_audit_status"] == "source_unavailable_r11_4"
    assert payload["summary"]["source_unavailable_row_count"] == 1
    assert row["local_case_material_available"] is False
    assert row["local_case_material_retained_here"] is False
    assert row["local_synthetic_body_retained_here"] is False

    r11.assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(payload)
    _assert_body_free(payload)


def test_r11_4_rejects_body_bearing_selection_payload_before_material_normalization() -> None:
    selection = _selection()
    selection["audit_rows"][0]["comment_text"] = "body must not enter R11-4 selection source"

    with pytest.raises(ValueError):
        r11.build_product_readfeel_p4_r11_material_route_audit_20260624(
            case_ref_selection_payload=selection,
            local_baseline_cases=_local_cases(),
            run_id="p4_r11_r4_unsafe_selection",
        )
