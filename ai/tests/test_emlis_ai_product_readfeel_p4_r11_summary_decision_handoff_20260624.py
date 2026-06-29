# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache

import pytest

import emlis_ai_product_readfeel_p4_r11_residual_family_surface_audit as r11
import emlis_ai_product_readfeel_p4_r11_surface_specificity_role_verdict_audit as r11_r6r7
import emlis_ai_product_readfeel_p4_r11_summary_decision_handoff as r11_r8
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
    '"p6_start_allowed": true',
    '"p8_start_allowed": true',
    '"release_allowed": true',
    '"runtime_changed_here": true',
    '"question_implementation_started_here": true',
    '"actual_human_review_run_here": true',
    '"actual_rating_rows_materialized_here": true',
    '"actual_question_need_observation_rows_materialized_here": true',
    '"actual_audit_rows_created_here": true',
    '"json_schema_file_materialized": true',
    '"local_visible_surface_retained_here": true',
    '"local_comment_text_retained_here": true',
    '"detector_fragment_retained_here": true',
    '"exact_sentence_match_required": true',
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


def _surface_path_audit() -> dict[str, object]:
    baseline = _baseline()
    scope = r11.build_product_readfeel_p4_r11_residual_family_scope_matrix_20260624(
        baseline_public_safe_index=baseline,
        run_id="p4_r11_r8_test_scope",
    )
    selection = r11.build_product_readfeel_p4_r11_case_ref_selection_coverage_audit_20260624(
        scope_matrix=scope,
        baseline_public_safe_index=baseline,
        run_id="p4_r11_r8_test_selection",
    )
    material = r11.build_product_readfeel_p4_r11_material_route_audit_20260624(
        case_ref_selection_payload=selection,
        local_baseline_cases=_local_cases(),
        run_id="p4_r11_r8_test_material",
    )
    return r11.build_product_readfeel_p4_r11_surface_path_audit_20260624(
        material_route_audit_payload=material,
        local_baseline_cases=_local_cases(),
        run_id="p4_r11_r8_test_surface_path",
    )


def _passing_probe_for_row(row: dict[str, object]) -> str:
    return " ".join(str(role) for role in row.get("required_surface_role_ids") or ())


def _probe_rows(
    surface_path_payload: dict[str, object],
    *,
    overrides: dict[str, str] | None = None,
) -> list[dict[str, str]]:
    overrides = overrides or {}
    probes: list[dict[str, str]] = []
    for row in surface_path_payload["audit_rows"]:
        assert isinstance(row, dict)
        case_ref = str(row["case_ref_id"])
        probes.append(
            {
                "case_ref_id": case_ref,
                "local_visible_surface": overrides.get(case_ref, _passing_probe_for_row(row)),
            }
        )
    return probes


def _first_case_ref(surface_path_payload: dict[str, object], residual_family_id: str) -> str:
    for row in surface_path_payload["audit_rows"]:
        assert isinstance(row, dict)
        if row.get("residual_family_id") == residual_family_id:
            return str(row["case_ref_id"])
    raise AssertionError(f"missing residual family in R11 test fixture: {residual_family_id}")


def _verdict_payload_mixed() -> dict[str, object]:
    surface_path = _surface_path_audit()
    change_ref = _first_case_ref(surface_path, r11.SCOPE_GROUP_CHANGE_FUTURE_INTENTION_TRANSITION)
    daily_ref = _first_case_ref(surface_path, r11.SCOPE_GROUP_DAILY_POSITIVE_RECOVERY)
    relationship_ref = _first_case_ref(surface_path, r11.SCOPE_GROUP_RELATIONSHIP_GRATITUDE_RECOVERY)
    structure_ref = _first_case_ref(surface_path, r11.SCOPE_GROUP_STRUCTURE_QUESTION)
    probes = _probe_rows(
        surface_path,
        overrides={
            change_ref: (
                "current_change_nucleus_visible "
                "recovered_energy_or_transition_visible "
                "category_emotion_action_generic"
            ),
            daily_ref: (
                "positive_event_or_small_change_visible "
                "positive_temperature_kept "
                "observation_not_overweighted "
                "reception_warmth_present "
                "no_generic_praise_only "
                "positive_temperature_cooling"
            ),
            relationship_ref: (
                "relationship_or_gratitude_nucleus_visible "
                "user_side_wish_or_reaction_visible "
                "relationship_target_judgement"
            ),
            structure_ref: (
                "question_context_visible "
                "state_answer_attempt_visible "
                "comfort_not_primary "
                "observation_ratio_high_enough "
                "no_question_escape "
                "observation_ratio_low"
            ),
        },
    )
    specificity = r11_r6r7.build_product_readfeel_p4_r11_surface_specificity_role_audit_20260624(
        surface_path_audit_payload=surface_path,
        local_surface_probes=probes,
        run_id="p4_r11_r8_test_specificity_mixed",
    )
    return r11_r6r7.build_product_readfeel_p4_r11_verdict_repair_candidate_classification_20260624(
        surface_specificity_role_audit_payload=specificity,
        run_id="p4_r11_r8_test_verdict_mixed",
    )


def _verdict_payload_all_pass() -> dict[str, object]:
    surface_path = _surface_path_audit()
    specificity = r11_r6r7.build_product_readfeel_p4_r11_surface_specificity_role_audit_20260624(
        surface_path_audit_payload=surface_path,
        local_surface_probes=_probe_rows(surface_path),
        run_id="p4_r11_r8_test_specificity_all_pass",
    )
    return r11_r6r7.build_product_readfeel_p4_r11_verdict_repair_candidate_classification_20260624(
        surface_specificity_role_audit_payload=specificity,
        run_id="p4_r11_r8_test_verdict_all_pass",
    )


def test_r11_8_handoff_sends_current_only_blockers_to_p4_r12_not_p5_p8_or_release() -> None:
    payload = r11_r8.build_product_readfeel_p4_r11_summary_decision_handoff_20260624(
        verdict_repair_classification_payload=_verdict_payload_mixed(),
        run_id="p4_r11_r8_test_handoff_mixed",
    )
    summary = payload["summary"]
    decision = payload["decision_handoff"]

    assert payload["schema_version"] == r11_r8.PRODUCT_READFEEL_P4_R11_SUMMARY_DECISION_HANDOFF_VERSION_20260624
    assert payload["source_step"] == r11.P4_R11_R8_STEP_REF_20260624
    assert tuple(payload["implemented_steps"]) == r11_r8.P4_R11_R8_IMPLEMENTED_STEPS_20260624
    assert payload["next_implementation_step"] == r11.P4_R11_R9_STEP_REF_20260624
    assert payload["summary_decision_handoff_performed_here"] is True
    assert payload["targeted_tests_performed_here"] is False

    assert summary["audited_row_count"] == r11.P4_R11_TARGET_ROW_COUNT_20260624
    assert summary["coverage_status"] == "complete"
    assert summary["current_only_blocker_count"] >= 2
    assert summary["p4_targeted_repair_required"] is True
    assert summary["r54_return_candidate_after_r11"] is False
    assert summary["decision_ref"] == r11_r8.P4_R11_DECISION_TARGETED_REPAIR_REQUIRED_BEFORE_R54_20260624
    assert summary["next_required_step"] == r11_r8.P4_R11_NEXT_STEP_P4_R12_TARGETED_REPAIR_20260624

    assert decision["decision_ref"] == r11_r8.P4_R11_DECISION_TARGETED_REPAIR_REQUIRED_BEFORE_R54_20260624
    assert decision["next_required_step"] == r11_r8.P4_R11_NEXT_STEP_P4_R12_TARGETED_REPAIR_20260624
    assert decision["r55_decision_preserved"] is True
    assert decision["r54_actual_review_still_required"] is True
    assert decision["p5_human_review_evidence_created_here"] is False
    assert decision["question_observation_rows_created_here"] is False
    assert decision["p6_start_allowed"] is False
    assert decision["p8_start_allowed"] is False
    assert decision["release_allowed"] is False

    r11.assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(payload)
    _assert_body_free(payload)


def test_r11_8_all_pass_is_only_r54_return_candidate_and_still_requires_actual_review() -> None:
    payload = r11_r8.build_product_readfeel_p4_r11_summary_decision_handoff_20260624(
        verdict_repair_classification_payload=_verdict_payload_all_pass(),
        run_id="p4_r11_r8_test_handoff_all_pass",
    )
    summary = payload["summary"]
    decision = payload["decision_handoff"]

    assert summary["current_only_blocker_count"] == 0
    assert summary["red_count"] == 0
    assert summary["repair_required_count"] == 0
    assert summary["decision_ref"] == r11_r8.P4_R11_DECISION_RETURN_TO_R54_ACTUAL_REVIEW_CANDIDATE_20260624
    assert summary["next_required_step"] == r11_r8.P4_R11_NEXT_STEP_R54_ACTUAL_LOCAL_ONLY_HUMAN_REVIEW_20260624
    assert summary["r54_return_candidate_after_r11"] is True
    assert decision["r54_actual_review_still_required"] is True
    assert decision["p5_human_review_evidence_created_here"] is False
    assert decision["question_observation_rows_created_here"] is False
    assert decision["p8_start_allowed"] is False
    assert decision["release_allowed"] is False
    _assert_body_free(payload)


def test_r11_8_insufficient_coverage_does_not_invent_case_refs_or_repair_decision() -> None:
    source = _verdict_payload_all_pass()
    broken = deepcopy(source)
    broken["summary"]["coverage_status"] = "insufficient_public_safe_case_refs"
    broken["summary"]["audited_row_count"] = r11.P4_R11_TARGET_ROW_COUNT_20260624 - 1

    payload = r11_r8.build_product_readfeel_p4_r11_summary_decision_handoff_20260624(
        verdict_repair_classification_payload=broken,
        run_id="p4_r11_r8_test_handoff_insufficient",
    )
    summary = payload["summary"]
    decision = payload["decision_handoff"]

    assert summary["decision_ref"] == r11_r8.P4_R11_DECISION_INSUFFICIENT_COVERAGE_EXPAND_AUDIT_20260624
    assert summary["next_required_step"] == r11_r8.P4_R11_NEXT_STEP_P4_R11_CASE_COVERAGE_EXPANSION_20260624
    assert summary["case_coverage_expansion_required"] is True
    assert decision["case_coverage_expansion_required"] is True
    assert decision["p8_start_allowed"] is False
    assert decision["release_allowed"] is False
    _assert_body_free(payload)


def test_r11_8_rejects_payload_that_skips_r11_7_verdict_classification() -> None:
    source = _verdict_payload_mixed()
    broken = deepcopy(source)
    broken["audit_rows"][0]["verdict_classification_performed_here"] = False

    with pytest.raises(ValueError, match="requires R11-7 verdict classification"):
        r11_r8.build_product_readfeel_p4_r11_summary_decision_handoff_20260624(
            verdict_repair_classification_payload=broken,
            run_id="p4_r11_r8_test_reject_skip_r11_7",
        )


def test_r11_8_public_decision_summary_is_body_free_and_has_no_public_contract_change() -> None:
    handoff = r11_r8.build_product_readfeel_p4_r11_summary_decision_handoff_20260624(
        verdict_repair_classification_payload=_verdict_payload_mixed(),
        run_id="p4_r11_r8_test_handoff_public_summary_source",
    )
    public_summary = r11_r8.build_product_readfeel_p4_r11_public_decision_summary_20260624(
        summary_decision_handoff_payload=handoff,
        run_id="p4_r11_r8_test_public_summary",
    )

    assert public_summary["schema_version"] == r11_r8.PRODUCT_READFEEL_P4_R11_PUBLIC_DECISION_SUMMARY_VERSION_20260624
    assert public_summary["decision_ref"] == r11_r8.P4_R11_DECISION_TARGETED_REPAIR_REQUIRED_BEFORE_R54_20260624
    assert public_summary["r55_decision_preserved"] is True
    assert public_summary["p5_human_review_evidence_created_here"] is False
    assert public_summary["question_observation_rows_created_here"] is False
    assert public_summary["p8_start_allowed"] is False
    assert public_summary["release_allowed"] is False
    assert public_summary["public_response_key_added"] is False
    assert public_summary["response_shape_changed"] is False
    assert public_summary["runtime_changed_here"] is False
    _assert_body_free(public_summary)
