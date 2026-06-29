# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache
from pathlib import Path

import emlis_ai_product_readfeel_p4_r11_residual_family_surface_audit as r11
import emlis_ai_product_readfeel_p4_r11_surface_specificity_role_verdict_audit as r11_r6r7
import emlis_ai_product_readfeel_p4_r11_summary_decision_handoff as r11_r8
from fixtures.emlis_ai_product_readfeel_baseline_cases_20260609 import (
    build_product_readfeel_baseline_cases_20260609,
    build_product_readfeel_baseline_public_safe_index_20260609,
)

R11_9_TARGETED_TEST_FILE_REFS = (
    "tests/test_emlis_ai_product_readfeel_p4_r11_scope_matrix_20260624.py",
    "tests/test_emlis_ai_product_readfeel_p4_r11_body_free_schema_20260624.py",
    "tests/test_emlis_ai_product_readfeel_p4_r11_case_ref_selection_coverage_20260624.py",
    "tests/test_emlis_ai_product_readfeel_p4_r11_material_route_audit_20260624.py",
    "tests/test_emlis_ai_product_readfeel_p4_r11_surface_path_audit_20260624.py",
    "tests/test_emlis_ai_product_readfeel_p4_r11_surface_specificity_role_audit_20260624.py",
    "tests/test_emlis_ai_product_readfeel_p4_r11_verdict_repair_candidate_classification_20260624.py",
    "tests/test_emlis_ai_product_readfeel_p4_r11_summary_decision_handoff_20260624.py",
    "tests/test_emlis_ai_product_readfeel_p4_r11_decision_handoff_20260624.py",
    "tests/test_emlis_ai_product_readfeel_p4_r11_targeted_tests_20260624.py",
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


def _r11_pipeline_to_decision_handoff() -> dict[str, object]:
    baseline = _baseline()
    scope = r11.build_product_readfeel_p4_r11_residual_family_scope_matrix_20260624(
        baseline_public_safe_index=baseline,
        run_id="p4_r11_r9_test_scope",
    )
    selection = r11.build_product_readfeel_p4_r11_case_ref_selection_coverage_audit_20260624(
        scope_matrix=scope,
        baseline_public_safe_index=baseline,
        run_id="p4_r11_r9_test_selection",
    )
    material = r11.build_product_readfeel_p4_r11_material_route_audit_20260624(
        case_ref_selection_payload=selection,
        local_baseline_cases=_local_cases(),
        run_id="p4_r11_r9_test_material",
    )
    surface = r11.build_product_readfeel_p4_r11_surface_path_audit_20260624(
        material_route_audit_payload=material,
        local_baseline_cases=_local_cases(),
        run_id="p4_r11_r9_test_surface_path",
    )
    probes = [
        {
            "case_ref_id": row["case_ref_id"],
            "local_visible_surface": " ".join(str(role) for role in row.get("required_surface_role_ids") or ()),
        }
        for row in surface["audit_rows"]
        if isinstance(row, dict)
    ]
    specificity = r11_r6r7.build_product_readfeel_p4_r11_surface_specificity_role_audit_20260624(
        surface_path_audit_payload=surface,
        local_surface_probes=probes,
        run_id="p4_r11_r9_test_specificity",
    )
    verdict = r11_r6r7.build_product_readfeel_p4_r11_verdict_repair_candidate_classification_20260624(
        surface_specificity_role_audit_payload=specificity,
        run_id="p4_r11_r9_test_verdict",
    )
    return r11_r8.build_product_readfeel_p4_r11_summary_decision_handoff_20260624(
        verdict_repair_classification_payload=verdict,
        run_id="p4_r11_r9_test_decision",
    )


def test_r11_9_targeted_test_manifest_lists_current_r11_target_files() -> None:
    test_refs = R11_9_TARGETED_TEST_FILE_REFS
    assert "tests/test_emlis_ai_product_readfeel_p4_r11_decision_handoff_20260624.py" in test_refs
    assert "tests/test_emlis_ai_product_readfeel_p4_r11_targeted_tests_20260624.py" in test_refs
    for test_ref in test_refs:
        assert Path(test_ref).exists(), test_ref


def test_r11_9_targeted_pipeline_reaches_r11_8_without_body_or_p5_p8_release_promotion() -> None:
    payload = _r11_pipeline_to_decision_handoff()
    summary = payload["summary"]
    handoff = payload["decision_handoff"]

    assert payload["source_step"] == r11.P4_R11_R8_STEP_REF_20260624
    assert payload["next_implementation_step"] == r11.P4_R11_R9_STEP_REF_20260624
    assert tuple(payload["implemented_steps"]) == r11_r8.P4_R11_R8_IMPLEMENTED_STEPS_20260624
    assert tuple(payload["not_yet_implemented_steps"]) == r11_r8.P4_R11_R8_NOT_YET_IMPLEMENTED_STEPS_20260624
    assert payload["targeted_tests_performed_here"] is False

    public_summary = r11_r8.build_product_readfeel_p4_r11_public_decision_summary_20260624(
        summary_decision_handoff_payload=payload,
        run_id="p4_r11_r9_test_public_decision_summary",
    )
    assert public_summary["decision_ref"] == handoff["decision_ref"]
    assert public_summary["next_required_step"] == handoff["next_required_step"]
    assert public_summary["p8_start_allowed"] is False
    assert public_summary["release_allowed"] is False

    assert summary["audited_row_count"] == r11.P4_R11_TARGET_ROW_COUNT_20260624
    assert handoff["r55_decision_preserved"] is True
    assert handoff["p5_human_review_evidence_created_here"] is False
    assert handoff["question_observation_rows_created_here"] is False
    assert handoff["p6_start_allowed"] is False
    assert handoff["p8_start_allowed"] is False
    assert handoff["release_allowed"] is False

    r11.assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(payload)
    _assert_body_free(payload)
