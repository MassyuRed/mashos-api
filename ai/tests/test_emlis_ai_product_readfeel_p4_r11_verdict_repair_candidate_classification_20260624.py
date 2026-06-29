# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache

import pytest

import emlis_ai_product_readfeel_p4_r11_residual_family_surface_audit as r11
import emlis_ai_product_readfeel_p4_r11_surface_specificity_role_verdict_audit as r11_r6r7
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
        run_id="p4_r11_r7_test_scope",
    )
    selection = r11.build_product_readfeel_p4_r11_case_ref_selection_coverage_audit_20260624(
        scope_matrix=scope,
        baseline_public_safe_index=baseline,
        run_id="p4_r11_r7_test_selection",
    )
    material = r11.build_product_readfeel_p4_r11_material_route_audit_20260624(
        case_ref_selection_payload=selection,
        local_baseline_cases=_local_cases(),
        run_id="p4_r11_r7_test_material",
    )
    return r11.build_product_readfeel_p4_r11_surface_path_audit_20260624(
        material_route_audit_payload=material,
        local_baseline_cases=_local_cases(),
        run_id="p4_r11_r7_test_surface_path",
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


def _specificity_payload() -> dict[str, object]:
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
    return r11_r6r7.build_product_readfeel_p4_r11_surface_specificity_role_audit_20260624(
        surface_path_audit_payload=surface_path,
        local_surface_probes=probes,
        run_id="p4_r11_r7_test_specificity",
    )


def _verdict_payload() -> dict[str, object]:
    return r11_r6r7.build_product_readfeel_p4_r11_verdict_repair_candidate_classification_20260624(
        surface_specificity_role_audit_payload=_specificity_payload(),
        run_id="p4_r11_r7_test_verdict",
    )


def test_r11_7_verdict_classification_splits_pass_yellow_repair_required_and_red_body_free() -> None:
    payload = _verdict_payload()
    summary = payload["summary"]
    rows = payload["audit_rows"]

    assert payload["schema_version"] == r11_r6r7.PRODUCT_READFEEL_P4_R11_VERDICT_REPAIR_CLASSIFICATION_VERSION_20260624
    assert payload["source_step"] == r11.P4_R11_R7_STEP_REF_20260624
    assert tuple(payload["implemented_steps"]) == r11_r6r7.P4_R11_R7_IMPLEMENTED_STEPS_20260624
    assert payload["next_implementation_step"] == r11.P4_R11_R8_STEP_REF_20260624
    assert payload["surface_specificity_role_audit_performed_here"] is True
    assert payload["verdict_classification_performed_here"] is True
    assert payload["summary_decision_handoff_performed_here"] is False
    assert payload["actual_audit_rows_created_here"] is False

    assert summary["audited_row_count"] == r11.P4_R11_TARGET_ROW_COUNT_20260624
    assert summary["verdict_counts"][r11_r6r7.P4_R11_VERDICT_PASS_20260624] > 0
    assert summary["verdict_counts"][r11_r6r7.P4_R11_VERDICT_YELLOW_20260624] >= 1
    assert summary["verdict_counts"][r11_r6r7.P4_R11_VERDICT_REPAIR_REQUIRED_20260624] >= 1
    assert summary["verdict_counts"][r11_r6r7.P4_R11_VERDICT_RED_20260624] >= 1
    assert summary["current_only_blocker_count"] >= 2
    assert summary["p4_targeted_repair_required"] is True
    assert summary["r54_return_candidate_after_r11_not_decided_until_r11_8"] is True
    assert summary["p8_start_allowed"] is False
    assert summary["release_allowed"] is False

    repair_row = next(row for row in rows if row["verdict"] == r11_r6r7.P4_R11_VERDICT_REPAIR_REQUIRED_20260624)
    assert repair_row["next_action"] == "p4_targeted_repair_required"
    assert repair_row["p5_p8_escape_boundary"]["current_only_repair_required_before_history_or_question"] is True
    assert repair_row["repair_candidate_layer_ids"]

    red_row = next(row for row in rows if row["verdict"] == r11_r6r7.P4_R11_VERDICT_RED_20260624)
    assert red_row["next_action"] == "p4_targeted_repair_required"
    assert red_row["risk_flags"]["overclaim_risk"] is True
    assert "visible_surface_acceptance_gate" in red_row["repair_candidate_layer_ids"]

    yellow_row = next(row for row in rows if row["verdict"] == r11_r6r7.P4_R11_VERDICT_YELLOW_20260624)
    assert yellow_row["next_action"] == "human_readfeel_review_note_only"
    assert yellow_row["p5_p8_escape_boundary"]["current_only_repair_required_before_history_or_question"] is False

    pass_row = next(row for row in rows if row["verdict"] == r11_r6r7.P4_R11_VERDICT_PASS_20260624)
    assert pass_row["next_action"] == "no_action_r54_return_candidate"
    assert pass_row["repair_candidate_layer_ids"] == []

    r11.assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(payload)
    _assert_body_free(payload)


def test_r11_7_requires_r11_6_surface_specificity_before_classification() -> None:
    specificity = _specificity_payload()
    broken = deepcopy(specificity)
    broken["audit_rows"][0]["surface_specificity_role_audit_performed_here"] = False

    with pytest.raises(ValueError, match="requires R11-6 surface specificity audit"):
        r11_r6r7.build_product_readfeel_p4_r11_verdict_repair_candidate_classification_20260624(
            surface_specificity_role_audit_payload=broken,
            run_id="p4_r11_r7_test_reject_skip_r11_6",
        )


def test_r11_7_pass_rows_do_not_create_p5_p8_release_or_actual_review_evidence() -> None:
    payload = _verdict_payload()
    pass_rows = [row for row in payload["audit_rows"] if row["verdict"] == r11_r6r7.P4_R11_VERDICT_PASS_20260624]
    assert pass_rows
    for row in pass_rows:
        assert row["next_action"] == "no_action_r54_return_candidate"
        assert row["p5_p8_escape_boundary"]["p5_masking_forbidden"] is False
        assert row["p5_p8_escape_boundary"]["p8_question_escape_forbidden"] is False
        assert row["actual_rating_rows_materialized_here"] is False
        assert row["actual_question_need_observation_rows_materialized_here"] is False
        assert row["actual_audit_rows_created_here"] is False

    assert payload["summary"]["p8_start_allowed"] is False
    assert payload["summary"]["release_allowed"] is False
    _assert_body_free(payload)
