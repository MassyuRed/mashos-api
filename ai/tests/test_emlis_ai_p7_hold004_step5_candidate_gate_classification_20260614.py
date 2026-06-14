# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from collections.abc import Mapping

import pytest

from emlis_ai_p7_hold004_step5_candidate_gate_classification import (
    P7_HOLD004_STEP5_BASELINE_FREEZE_SCHEMA_VERSION,
    P7_HOLD004_STEP5_CONFLICT_MATRIX_SCHEMA_VERSION,
    P7_HOLD004_STEP5_DECISION_RULE_SCHEMA_VERSION,
    P7_HOLD004_STEP5_OBSERVATION_SCHEMA_VERSION,
    P7_HOLD004_STEP5_OWNER_LAYER_DECISION_SCHEMA_VERSION,
    P7_HOLD004_STEP5_R4A_FAIL_CLOSED_SCHEMA_VERSION,
    P7_HOLD004_STEP5_R4B_TRACE_REPAIR_SCHEMA_VERSION,
    P7_HOLD004_STEP5_R4C_STALE_EXPECTATION_UPDATE_SCHEMA_VERSION,
    P7_HOLD004_STEP5_R4D_MIXED_CONFLICT_HOLD_SCHEMA_VERSION,
    P7_HOLD004_STEP5_R5_META_EXTENSION_SCHEMA_VERSION,
    P7_HOLD004_STEP5_R6_MATERIAL_CONNECTION_SCHEMA_VERSION,
    P7_HOLD004_STEP5_RED_ID,
    assert_p7_hold004_step5_candidate_gate_baseline_freeze_contract,
    assert_p7_hold004_step5_candidate_gate_observation_contract,
    assert_p7_hold004_step5_conflicting_contract_pair_matrix_contract,
    assert_p7_hold004_step5_display_binding_contract_decision_rule_contract,
    assert_p7_hold004_step5_owner_layer_decision_contract,
    assert_p7_hold004_step5_r4a_display_gate_fail_closed_branch_contract,
    assert_p7_hold004_step5_r4b_display_binding_trace_repair_branch_contract,
    assert_p7_hold004_step5_r4c_stale_test_expectation_update_branch_contract,
    assert_p7_hold004_step5_r4d_mixed_contract_conflict_hold_branch_contract,
    assert_p7_hold004_step5_r5_meta_extension_material_contract,
    assert_p7_hold004_step5_r6_material_connection_contract,
    build_p7_hold004_step5_candidate_gate_baseline_freeze,
    build_p7_hold004_step5_candidate_gate_observation,
    build_p7_hold004_step5_conflicting_contract_pair_matrix,
    build_p7_hold004_step5_display_binding_contract_decision_rule,
    build_p7_hold004_step5_owner_layer_decision,
    build_p7_hold004_step5_r4a_display_gate_fail_closed_branch,
    build_p7_hold004_step5_r4b_display_binding_trace_repair_branch,
    build_p7_hold004_step5_r4c_stale_test_expectation_update_branch,
    build_p7_hold004_step5_r4d_mixed_contract_conflict_hold_branch,
    build_p7_hold004_step5_r5_meta_extension_material,
    build_p7_hold004_step5_r6_material_connection,
)
from emlis_ai_p7_hold_matrix import (
    assert_p7_backend_suite_split_matrix_contract,
    assert_p7_r10_hold_matrix_contract,
    build_p7_backend_suite_split_matrix,
    build_p7_r10_hold_matrix,
)
from emlis_ai_p7_release_handoff import (
    assert_p7_release_decision_handoff_contract,
    build_p7_release_decision_handoff,
)
from emlis_ai_p7_validation_matrix import (
    assert_p7_validation_regression_matrix_contract,
    build_p7_validation_regression_matrix,
)


_COMPLETE_INITIAL_ENV = {
    "COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED": "true",
    "COCOLON_EMLIS_DEFAULT_COMPOSER": "complete_initial",
    "COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT_STAGE": "all",
}

_SAMPLE_MEMO = "疲れているけれど、少し整えたい気持ちもある。"
_FORBIDDEN_EXACT_BODY_KEYS = {
    "raw_input",
    "current_input",
    "memo",
    "memo_action",
    "comment_text",
    "candidate_body",
    "surface_body",
    "text",
    "body",
}


def _clear_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED",
        "COCOLON_EMLIS_AI_LIMITED_COMPOSER_ENABLED",
        "EMLIS_AI_LIMITED_COMPOSER_ENABLED",
        "COCOLON_LIMITED_COMPOSER_ENABLED",
        "COCOLON_EMLIS_AI_DEFAULT_LIMITED_COMPOSER_ENABLED",
        "EMLIS_AI_DEFAULT_LIMITED_COMPOSER_ENABLED",
        "COCOLON_EMLIS_DEFAULT_COMPOSER",
        "COCOLON_EMLIS_AI_DEFAULT_COMPOSER",
        "EMLIS_AI_DEFAULT_COMPOSER",
        "COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT_STAGE",
        "COCOLON_EMLIS_AI_LIMITED_COMPOSER_ROLLOUT_STAGE",
        "EMLIS_AI_LIMITED_COMPOSER_ROLLOUT_STAGE",
        "COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT",
        "EMLIS_AI_LIMITED_COMPOSER_ROLLOUT",
    ):
        monkeypatch.delenv(name, raising=False)


def _enable_complete_initial(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_flags(monkeypatch)
    for key, value in _COMPLETE_INITIAL_ENV.items():
        monkeypatch.setenv(key, value)


def _sample_current_input(input_id: str) -> dict[str, object]:
    return {
        "id": input_id,
        "created_at": "2026-05-16T00:00:00Z",
        "memo": _SAMPLE_MEMO,
        "memo_action": "",
        "emotion_details": [{"type": "自己理解", "strength": "medium"}],
        "emotions": ["自己理解"],
        "category": ["生活"],
    }


async def _render_step5_reply(monkeypatch: pytest.MonkeyPatch):
    _enable_complete_initial(monkeypatch)
    from emlis_ai_reply_service import render_emlis_ai_reply

    return await render_emlis_ai_reply(
        user_id="p7-hold004-step5-candidate-gate-classification-user",
        subscription_tier="free",
        current_input=_sample_current_input("p7-hold004-step5-candidate-gate-classification-input"),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )


def _walk_keys(value) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, Mapping):
        for key, child in value.items():
            keys.add(str(key))
            keys.update(_walk_keys(child))
    elif isinstance(value, list):
        for child in value:
            keys.update(_walk_keys(child))
    return keys


def _assert_body_free_material(material: Mapping[str, object]) -> None:
    serialized = json.dumps(material, ensure_ascii=False, sort_keys=True)
    assert _SAMPLE_MEMO not in serialized
    assert not (_walk_keys(material) & _FORBIDDEN_EXACT_BODY_KEYS)


def _observed_step5_fixture(
    *,
    display_binding_missing: bool = True,
    display_expected_binding_count: int = 4,
    display_binding_missing_exception_allowed: bool = False,
    display_binding_missing_exception_id: str = "",
    public_comment_text_present: bool = True,
) -> dict[str, object]:
    return {
        "complete_initial_client_resolved": True,
        "candidate_generation_attempted": True,
        "complete_composer_client_generate_called": True,
        "candidate_generated": True,
        "candidate_generated_before_display_gate": True,
        "candidate_status": "generated",
        "candidate_status_before_display_gate": "generated",
        "candidate_status_after_display_gate": "passed",
        "composer_source": "ai_generated",
        "display_observation_status": "passed",
        "candidate_comment_text_present": True,
        "public_comment_text_present": public_comment_text_present,
        "non_passed_comment_text_empty": True,
        "passed_only_comment_text_contract_preserved": True,
        "existing_reader_grounding_template_display_gates_preserved": True,
        "reader_gate_evaluated": True,
        "grounding_gate_evaluated": True,
        "template_gate_evaluated": True,
        "display_gate_evaluated": True,
        "display_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "gate_results": {
            "display": {
                "evaluated": True,
                "passed": True,
                "binding_required": True,
                "binding_used": True,
                "binding_present": True,
                "binding_missing": display_binding_missing,
                "binding_count": 3,
                "expected_binding_count": display_expected_binding_count,
                "binding_missing_exception_allowed": display_binding_missing_exception_allowed,
                "binding_missing_exception_id": display_binding_missing_exception_id,
                "binding_support_source": "display_binding_aware_result",
                "rejection_reasons": [],
            },
            "grounding": {
                "evaluated": True,
                "passed": True,
                "binding_required": True,
                "binding_used": True,
                "binding_present": True,
                "binding_missing": False,
                "binding_count": 3,
                "expected_binding_count": 3,
                "binding_support_source": "low_information_observation_roles",
                "rejection_reasons": [],
            },
        },
    }


def _frozen_pre_repair_observation():
    return build_p7_hold004_step5_candidate_gate_observation(
        step5_meta=_observed_step5_fixture(),
        reply_comment_text_present=True,
    )


def _post_r4b_repaired_observation():
    return build_p7_hold004_step5_candidate_gate_observation(
        step5_meta=_observed_step5_fixture(
            display_binding_missing=False,
            display_expected_binding_count=3,
            public_comment_text_present=True,
        ),
        reply_comment_text_present=True,
    )


@pytest.mark.asyncio
async def test_r0_current_step5_red_observation_is_frozen_body_free_without_runtime_repair(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observation = _frozen_pre_repair_observation()

    assert observation["schema_version"] == P7_HOLD004_STEP5_OBSERVATION_SCHEMA_VERSION
    assert observation["red_id"] == P7_HOLD004_STEP5_RED_ID
    assert observation["classification_status"] == "CLASSIFIED_UNRESOLVED"
    assert observation["classification"] == "display_binding_missing_passed_public_assignment_conflict"
    assert {
        "display_gate_binding_contract",
        "binding_presence_meta_source",
        "test_contract_boundary",
    } <= set(observation["owner_layers"])
    assert "stale_or_regression_not_decided" in observation["reason_codes"]

    candidate = observation["candidate_summary"]
    assert candidate["candidate_status"] == "generated"
    assert candidate["candidate_status_before_display_gate"] == "generated"
    assert candidate["candidate_status_after_display_gate"] == "passed"
    assert candidate["candidate_generated"] is True
    assert candidate["candidate_comment_text_present"] is True

    gates = observation["gate_preservation_summary"]
    assert gates["existing_reader_grounding_template_display_gates_preserved"] is True
    assert gates["reader_gate_evaluated"] is True
    assert gates["grounding_gate_evaluated"] is True
    assert gates["template_gate_evaluated"] is True
    assert gates["display_gate_evaluated"] is True
    assert gates["display_gate_relaxed"] is False

    display = observation["display_binding_summary"]
    assert display["evaluated"] is True
    assert display["passed"] is True
    assert display["observation_status"] == "passed"
    assert display["binding_required"] is True
    assert display["binding_used"] is True
    assert display["binding_present"] is True
    assert display["binding_missing"] is True
    assert display["binding_missing_without_exception"] is True
    assert display["binding_count"] == 3
    assert display["expected_binding_count"] == 4
    assert display["display_binding_contract_consistent"] is False

    grounding = observation["grounding_binding_summary"]
    assert grounding["passed"] is True
    assert grounding["binding_missing"] is False
    assert grounding["binding_count"] == 3
    assert grounding["expected_binding_count"] == 3

    public = observation["public_assignment_summary"]
    assert public["public_comment_text_present"] is True
    assert public["reply_comment_text_present"] is True
    assert public["public_assignment_allowed_by_display_gate"] is False
    assert public["public_assignment_contract_consistent"] is False

    assert observation["full_backend_suite_green_confirmed"] is False
    assert observation["hold004_close_allowed"] is False
    assert observation["p7_complete"] is False
    assert observation["p8_start_allowed"] is False
    assert observation["release_allowed"] is False
    assert observation["body_free"] is True
    assert_p7_hold004_step5_candidate_gate_observation_contract(observation)
    _assert_body_free_material(observation)


@pytest.mark.asyncio
async def test_r0_baseline_freeze_records_first_red_and_keeps_release_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    observation = _frozen_pre_repair_observation()

    freeze = build_p7_hold004_step5_candidate_gate_baseline_freeze(observations=[observation])

    assert freeze["schema_version"] == P7_HOLD004_STEP5_BASELINE_FREEZE_SCHEMA_VERSION
    assert freeze["red_id"] == P7_HOLD004_STEP5_RED_ID
    assert freeze["status"] == "RED_REPRODUCED"
    assert freeze["full_backend_suite_collect_count"] == 2651
    assert freeze["full_backend_suite_first_red_reproduced"] is True
    assert P7_HOLD004_STEP5_RED_ID in freeze["unresolved_red_refs"]
    assert freeze["full_backend_suite_green_confirmed"] is False
    assert freeze["full_backend_suite_green_claim_allowed"] is False
    assert freeze["hold004_close_allowed"] is False
    assert freeze["p7_complete"] is False
    assert freeze["p8_start_allowed"] is False
    assert freeze["release_allowed"] is False
    assert freeze["body_free"] is True
    assert_p7_hold004_step5_candidate_gate_baseline_freeze_contract(freeze)
    _assert_body_free_material(freeze)


@pytest.mark.asyncio
async def test_r1_conflicting_contract_pair_matrix_keeps_expectations_separate(monkeypatch: pytest.MonkeyPatch) -> None:
    observation = _frozen_pre_repair_observation()

    matrix = build_p7_hold004_step5_conflicting_contract_pair_matrix(observations=[observation])

    assert matrix["schema_version"] == P7_HOLD004_STEP5_CONFLICT_MATRIX_SCHEMA_VERSION
    assert matrix["red_id"] == P7_HOLD004_STEP5_RED_ID
    assert matrix["status"] == "CONTRACT_CONFLICT_CLASSIFIED_UNRESOLVED"
    assert matrix["display_binding_contract_consistency_required"] is True
    assert matrix["public_display_permission_decided"] is False
    assert matrix["stale_or_regression_decided"] is False
    assert "display_binding_contract_consistency" in matrix["decision_axes"]
    assert "stale_test_vs_implementation_regression_not_decided" in matrix["decision_axes"]

    public_pair = matrix["contract_pairs"][0]
    assert public_pair["pair_id"] == "step5_fail_closed_vs_phase20_public_recovery"
    assert public_pair["candidate_generation_expected_by_both"] is True
    assert public_pair["left_public_assignment_expectation"] == "public_absent_fail_closed"
    assert public_pair["right_public_assignment_expectation"] == "public_present_after_recovery"
    assert public_pair["binding_contract_consistency_required"] is True
    assert public_pair["public_display_permission_decided"] is False
    assert public_pair["stale_or_regression_decided"] is False

    integration_pair = matrix["contract_pairs"][1]
    assert integration_pair["pair_id"] == "step5_step7_existing_gate_preservation_boundary"
    assert integration_pair["left_display_expectation"] == "candidate_path_must_not_bypass_existing_gates"
    assert integration_pair["right_display_expectation"] == "public_assignment_uses_existing_display_gate_when_gate_passes"
    assert integration_pair["binding_contract_consistency_required"] is True
    assert integration_pair["public_display_permission_decided"] is False

    row = matrix["observation_statuses"][0]
    assert row["classification"] == "display_binding_missing_passed_public_assignment_conflict"
    assert row["display_gate_passed"] is True
    assert row["display_binding_missing"] is True
    assert row["display_binding_contract_consistent"] is False
    assert row["public_comment_text_present"] is True
    assert row["public_assignment_contract_consistent"] is False

    assert matrix["full_backend_suite_green_confirmed"] is False
    assert matrix["hold004_close_allowed"] is False
    assert matrix["release_allowed"] is False
    assert matrix["p7_complete"] is False
    assert matrix["p8_start_allowed"] is False
    assert_p7_hold004_step5_conflicting_contract_pair_matrix_contract(matrix)
    _assert_body_free_material(matrix)


@pytest.mark.asyncio
async def test_r2_display_binding_decision_rule_blocks_missing_without_valid_exception_body_free(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observation = _frozen_pre_repair_observation()

    rule = build_p7_hold004_step5_display_binding_contract_decision_rule(observation=observation)

    assert rule["schema_version"] == P7_HOLD004_STEP5_DECISION_RULE_SCHEMA_VERSION
    assert rule["red_id"] == P7_HOLD004_STEP5_RED_ID
    assert rule["decision_rule_fixed"] is True
    assert rule["status"] == "DECISION_RULE_FIXED_RED_OPEN"
    assert rule["classification"] == "display_binding_missing_without_exception_blocks_public_assignment"
    assert rule["display_binding_contract_consistency_required"] is True
    assert rule["public_assignment_contract_consistency_required"] is True
    assert rule["current_public_assignment_allowed"] is False
    assert rule["runtime_public_behavior_changed"] is False
    assert rule["r4_branch_selected"] is False

    results = rule["rule_results"]
    assert results["display_binding_required"] is True
    assert results["display_binding_used"] is True
    assert results["display_binding_missing"] is True
    assert results["display_gate_passed"] is True
    assert results["binding_missing_exception_valid"] is False
    assert results["binding_missing_without_exception"] is True
    assert results["display_binding_contract_consistent"] is False
    assert results["public_comment_text_present"] is True
    assert results["public_assignment_contract_consistent"] is False
    assert results["public_assignment_contract_violation"] is True

    rule_rows = {row["rule_id"]: row for row in rule["rules"]}
    assert rule_rows["binding_missing_without_exception_blocks_display_contract_consistency"]["matched"] is True
    assert rule_rows["public_assignment_requires_display_binding_contract_consistency"]["matched"] is True
    assert rule_rows["public_display_requires_no_missing_or_valid_exception"]["matched"] is True

    assert rule["full_backend_suite_green_confirmed"] is False
    assert rule["hold004_close_allowed"] is False
    assert rule["release_allowed"] is False
    assert rule["p7_complete"] is False
    assert rule["p8_start_allowed"] is False
    assert_p7_hold004_step5_display_binding_contract_decision_rule_contract(rule)
    _assert_body_free_material(rule)


def test_r2_public_assignment_requires_no_missing_or_valid_exception() -> None:
    missing_without_id = build_p7_hold004_step5_candidate_gate_observation(
        step5_meta=_observed_step5_fixture(
            display_binding_missing=True,
            display_binding_missing_exception_allowed=True,
            display_binding_missing_exception_id="",
            public_comment_text_present=True,
        ),
        reply_comment_text_present=True,
    )
    missing_without_id_rule = build_p7_hold004_step5_display_binding_contract_decision_rule(
        observation=missing_without_id
    )
    assert missing_without_id_rule["rule_results"]["binding_missing_exception_allowed"] is True
    assert missing_without_id_rule["rule_results"]["binding_missing_exception_valid"] is False
    assert missing_without_id_rule["rule_results"]["display_binding_contract_consistent"] is False
    assert missing_without_id_rule["current_public_assignment_allowed"] is False

    no_missing = build_p7_hold004_step5_candidate_gate_observation(
        step5_meta=_observed_step5_fixture(
            display_binding_missing=False,
            display_expected_binding_count=3,
            public_comment_text_present=True,
        ),
        reply_comment_text_present=True,
    )
    no_missing_rule = build_p7_hold004_step5_display_binding_contract_decision_rule(observation=no_missing)
    assert no_missing_rule["status"] == "DECISION_RULE_FIXED_NO_CURRENT_RED"
    assert no_missing_rule["rule_results"]["display_binding_contract_consistent"] is True
    assert no_missing_rule["rule_results"]["public_assignment_contract_consistent"] is True
    assert no_missing_rule["current_public_assignment_allowed"] is True
    assert no_missing_rule["release_allowed"] is False
    assert_p7_hold004_step5_display_binding_contract_decision_rule_contract(no_missing_rule)

    valid_exception = build_p7_hold004_step5_candidate_gate_observation(
        step5_meta=_observed_step5_fixture(
            display_binding_missing=True,
            display_binding_missing_exception_allowed=True,
            display_binding_missing_exception_id="low_information_recovery_display_exception",
            public_comment_text_present=True,
        ),
        reply_comment_text_present=True,
    )
    valid_exception_rule = build_p7_hold004_step5_display_binding_contract_decision_rule(observation=valid_exception)
    assert valid_exception_rule["status"] == "DECISION_RULE_FIXED_NO_CURRENT_RED"
    assert valid_exception_rule["rule_results"]["binding_missing_exception_valid"] is True
    assert valid_exception_rule["rule_results"]["display_binding_contract_consistent"] is True
    assert valid_exception_rule["current_public_assignment_allowed"] is True
    assert valid_exception_rule["release_allowed"] is False
    assert_p7_hold004_step5_display_binding_contract_decision_rule_contract(valid_exception_rule)


@pytest.mark.asyncio
async def test_r3_owner_layer_decision_keeps_current_conflict_mixed_until_r4(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observation = _frozen_pre_repair_observation()
    matrix = build_p7_hold004_step5_conflicting_contract_pair_matrix(observations=[observation])
    rule = build_p7_hold004_step5_display_binding_contract_decision_rule(observation=observation)

    owner = build_p7_hold004_step5_owner_layer_decision(
        observation=observation,
        decision_rule=rule,
        conflict_matrix=matrix,
    )

    assert owner["schema_version"] == P7_HOLD004_STEP5_OWNER_LAYER_DECISION_SCHEMA_VERSION
    assert owner["red_id"] == P7_HOLD004_STEP5_RED_ID
    assert owner["owner_layer_decision_fixed"] is True
    assert owner["status"] == "OWNER_LAYER_MIXED_CONTRACT_CONFLICT"
    assert owner["classification"] == "mixed_contract_conflict"
    assert owner["owner_layer"] == "mixed"
    assert owner["next_branch"] == "R4-D"
    assert owner["r4_branch_executed"] is False
    assert {
        "step5_meta_boundary",
        "display_gate_binding_contract",
        "binding_presence_meta_source",
        "test_contract_boundary",
    } <= set(owner["owner_layers"])

    evaluations = owner["owner_rule_evaluations"]
    assert evaluations["implementation_rule_matched"] is True
    assert evaluations["binding_count_differential_observed"] is True
    assert evaluations["body_line_diff_only_evidence_confirmed"] is False
    assert evaluations["trace_rule_matched"] is False
    assert evaluations["unresolved_conflict_pair_present"] is True
    assert evaluations["stale_rule_matched"] is False
    assert evaluations["mixed_rule_matched"] is True

    assert owner["runtime_public_behavior_changed"] is False
    assert owner["full_backend_suite_green_confirmed"] is False
    assert owner["hold004_close_allowed"] is False
    assert owner["release_allowed"] is False
    assert owner["p7_complete"] is False
    assert owner["p8_start_allowed"] is False
    assert_p7_hold004_step5_owner_layer_decision_contract(owner)
    _assert_body_free_material(owner)


def test_r3_owner_layer_can_route_single_explicit_owners_without_executing_r4() -> None:
    observation = build_p7_hold004_step5_candidate_gate_observation(
        step5_meta=_observed_step5_fixture(),
        reply_comment_text_present=True,
    )
    rule = build_p7_hold004_step5_display_binding_contract_decision_rule(observation=observation)

    display_owner_observation = build_p7_hold004_step5_candidate_gate_observation(
        step5_meta=_observed_step5_fixture(display_expected_binding_count=3),
        reply_comment_text_present=True,
    )
    display_owner_rule = build_p7_hold004_step5_display_binding_contract_decision_rule(
        observation=display_owner_observation
    )
    display_owner = build_p7_hold004_step5_owner_layer_decision(
        observation=display_owner_observation,
        decision_rule=display_owner_rule,
    )
    assert display_owner["classification"] == "implementation_contract_red"
    assert display_owner["owner_layer"] == "display_gate_binding_contract"
    assert display_owner["next_branch"] == "R4-A"
    assert display_owner["r4_branch_executed"] is False
    assert display_owner["release_allowed"] is False
    assert_p7_hold004_step5_owner_layer_decision_contract(display_owner)

    implementation_owner = build_p7_hold004_step5_owner_layer_decision(
        observation=observation,
        decision_rule=rule,
    )
    assert implementation_owner["classification"] == "mixed_contract_conflict"
    assert implementation_owner["next_branch"] == "R4-D"
    assert implementation_owner["r4_branch_executed"] is False
    assert_p7_hold004_step5_owner_layer_decision_contract(implementation_owner)

    trace_owner = build_p7_hold004_step5_owner_layer_decision(
        observation=observation,
        decision_rule=rule,
        body_line_diff_only_evidence_confirmed=True,
    )
    assert trace_owner["classification"] == "meta_trace_inconsistency"
    assert trace_owner["owner_layer"] == "binding_presence_meta_source"
    assert trace_owner["next_branch"] == "R4-B"
    assert trace_owner["r4_branch_executed"] is False
    assert trace_owner["release_allowed"] is False
    assert_p7_hold004_step5_owner_layer_decision_contract(trace_owner)

    matrix = build_p7_hold004_step5_conflicting_contract_pair_matrix(observations=[observation])
    stale_owner = build_p7_hold004_step5_owner_layer_decision(
        observation=observation,
        decision_rule=rule,
        conflict_matrix=matrix,
        stale_public_recovery_canonical_evidence_confirmed=True,
    )
    assert stale_owner["classification"] == "stale_test_expectation"
    assert stale_owner["owner_layer"] == "test_contract_boundary"
    assert stale_owner["next_branch"] == "R4-C"
    assert stale_owner["r4_branch_executed"] is False
    assert stale_owner["release_allowed"] is False
    assert_p7_hold004_step5_owner_layer_decision_contract(stale_owner)



def test_r4a_display_gate_runtime_fails_closed_when_binding_missing_has_no_exception() -> None:
    from emlis_ai_display_gate import decide_emlis_observation_display
    from emlis_ai_types import GroundingReport, ListenerReaderReport, TemplateEchoReport

    decision = decide_emlis_observation_display(
        comment_text="synthetic display surface",
        reader_report=ListenerReaderReport(
            understandable=True,
            addressee_clear=True,
            speaker_integrity_ok=True,
            conversational=True,
            report_like=False,
            confidence=1.0,
        ),
        grounding_report=GroundingReport(
            passed=True,
            binding_used=True,
            binding_present=True,
            binding_missing=True,
            binding_count=1,
            expected_binding_count=2,
            binding_support_source="declared_relation_binding",
        ),
        template_echo_report=TemplateEchoReport(passed=True),
        trace_id="p7-hold004-r4a-runtime",
        composer_source="ai_generated",
        phase_completion_ready=True,
        binding_meta={
            "binding_required": True,
            "binding_expected": True,
            "binding_used": True,
            "binding_present": True,
            "binding_count": 1,
            "expected_binding_count": 2,
        },
    )

    assert decision.observation_status != "passed"
    assert decision.comment_text == ""
    assert "display_sentence_binding_missing" in decision.rejection_reasons

    display = decision.gate_trace["display_gate"]
    assert display["passed"] is False
    assert display["comment_text_allowed"] is False
    assert display["binding_required"] is True
    assert display["binding_used"] is True
    assert display["binding_missing"] is True
    assert display["binding_missing_exception_valid"] is False
    assert display["display_binding_contract_consistent"] is False
    assert display["display_gate_relaxed"] is False
    assert display["expected_binding_count_source"] == "candidate_body_line_count"


def test_r4a_display_gate_fail_closed_branch_is_fixed_body_free() -> None:
    observation = build_p7_hold004_step5_candidate_gate_observation(
        step5_meta=_observed_step5_fixture(display_expected_binding_count=3),
        reply_comment_text_present=True,
    )
    rule = build_p7_hold004_step5_display_binding_contract_decision_rule(observation=observation)
    owner = build_p7_hold004_step5_owner_layer_decision(observation=observation, decision_rule=rule)

    branch = build_p7_hold004_step5_r4a_display_gate_fail_closed_branch(
        observation=observation,
        decision_rule=rule,
        owner_decision=owner,
    )

    assert branch["schema_version"] == P7_HOLD004_STEP5_R4A_FAIL_CLOSED_SCHEMA_VERSION
    assert branch["branch"] == "R4-A"
    assert branch["status"] == "R4A_FAIL_CLOSED_REPAIR_BRANCH_FIXED"
    assert branch["classification"] == "display_binding_missing_without_exception_requires_fail_closed"
    assert branch["fail_closed_reason"] == "display_sentence_binding_missing"
    assert branch["expected_display_observation_status_after_branch"] == "rejected"
    assert branch["expected_public_comment_text_present_after_branch"] is False
    assert branch["display_binding_contract_consistent_after_branch"] is False
    assert branch["public_assignment_contract_consistent_after_branch"] is True
    assert branch["display_gate_relaxed"] is False
    assert branch["fixed_sentence_template_added"] is False
    assert branch["case_specific_branch_added"] is False
    assert branch["full_backend_suite_green_confirmed"] is False
    assert branch["hold004_close_allowed"] is False
    assert branch["release_allowed"] is False
    assert branch["p7_complete"] is False
    assert branch["p8_start_allowed"] is False
    assert_p7_hold004_step5_r4a_display_gate_fail_closed_branch_contract(branch)
    _assert_body_free_material(branch)


def test_r4b_trace_repair_branch_aligns_display_expected_count_to_grounding_body_free() -> None:
    before = _frozen_pre_repair_observation()
    after = _post_r4b_repaired_observation()
    rule = build_p7_hold004_step5_display_binding_contract_decision_rule(observation=before)
    owner = build_p7_hold004_step5_owner_layer_decision(
        observation=before,
        decision_rule=rule,
        body_line_diff_only_evidence_confirmed=True,
    )

    branch = build_p7_hold004_step5_r4b_display_binding_trace_repair_branch(
        pre_repair_observation=before,
        post_repair_observation=after,
        owner_decision=owner,
    )

    assert branch["schema_version"] == P7_HOLD004_STEP5_R4B_TRACE_REPAIR_SCHEMA_VERSION
    assert branch["branch"] == "R4-B"
    assert branch["status"] == "R4B_TRACE_REPAIR_APPLIED"
    assert branch["classification"] == "display_expected_count_aligned_to_accepted_grounding_sentence_count"
    assert branch["expected_binding_count_before"] == 4
    assert branch["expected_binding_count_after"] == 3
    assert branch["grounding_expected_binding_count"] == 3
    assert branch["display_binding_missing_before"] is True
    assert branch["display_binding_missing_after"] is False
    assert branch["display_binding_contract_consistent_after"] is True
    assert branch["public_assignment_contract_consistent_after"] is True
    assert branch["public_comment_text_present_after"] is True
    assert branch["runtime_public_behavior_changed"] is False
    assert branch["r4a_fail_closed_not_applied_to_current_repaired_path"] is True
    assert branch["r4c_stale_fail_closed_expectation_review_required"] is True
    assert branch["full_backend_suite_green_confirmed"] is False
    assert branch["hold004_close_allowed"] is False
    assert branch["release_allowed"] is False
    assert branch["p7_complete"] is False
    assert branch["p8_start_allowed"] is False
    assert_p7_hold004_step5_r4b_display_binding_trace_repair_branch_contract(branch)
    _assert_body_free_material(branch)


def test_r4a_runtime_display_gate_fails_closed_when_binding_still_missing_without_exception() -> None:
    from emlis_ai_display_gate import decide_emlis_observation_display
    from emlis_ai_types import GroundingReport, GroundingSentenceClaim, ListenerReaderReport, TemplateEchoReport

    decision = decide_emlis_observation_display(
        comment_text="body-free synthetic candidate",
        reader_report=ListenerReaderReport(
            understandable=True,
            addressee_clear=True,
            speaker_integrity_ok=True,
            conversational=True,
            report_like=False,
            confidence=1.0,
        ),
        grounding_report=GroundingReport(
            passed=True,
            sentence_claims=[
                GroundingSentenceClaim(
                    sentence_index=0,
                    sentence="synthetic",
                    evidence_span_ids=["span-1"],
                    relation_supported=True,
                    binding_used=True,
                    binding_sentence_id="sent-1",
                    binding_evidence_span_ids=["span-1"],
                    binding_phrase_unit_ids=["phrase-1"],
                    binding_relation_type="state_answer",
                    grounding_support_source="r4a_runtime_synthetic",
                )
            ],
            coverage_ratio=1.0,
            confidence=1.0,
            binding_used=True,
            binding_present=True,
            binding_missing=True,
            binding_count=1,
            expected_binding_count=2,
            binding_version="r4a.synthetic.binding.v1",
            binding_supported_sentence_count=1,
        ),
        template_echo_report=TemplateEchoReport(passed=True),
        composer_source="ai_generated",
        binding_meta={
            "binding_required": True,
            "binding_expected": True,
            "binding_used": True,
            "binding_present": True,
            "binding_count": 1,
            "expected_binding_count": 2,
            "sentence_count": 2,
            "body_sentence_count": 2,
            "binding_version": "r4a.synthetic.binding.v1",
            "binding_support_source": "r4a_runtime_synthetic",
            "raw_text_included": False,
            "raw_input_required_for_debug": False,
        },
    )

    display = decision.gate_trace["display_gate"]
    assert decision.observation_status == "rejected"
    assert decision.comment_text == ""
    assert "display_sentence_binding_missing" in decision.rejection_reasons
    assert display["passed"] is False
    assert display["comment_text_allowed"] is False
    assert display["binding_missing"] is True
    assert display["display_binding_contract_consistent"] is False
    assert display["expected_binding_count"] == 2
    assert display["display_binding_trace_repair_applied"] is False
    assert display["raw_text_included"] is False
    assert display["raw_input_required_for_debug"] is False


@pytest.mark.asyncio
async def test_r4b_runtime_repair_removes_display_binding_missing_without_silencing_public_recovery(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reply = await _render_step5_reply(monkeypatch)
    diagnostic = reply.meta["diagnostic_summary"]
    step5 = diagnostic["complete_initial_candidate_generation_path"]
    runtime = diagnostic["complete_initial_runtime"]
    display = step5["gate_results"]["display"]
    grounding = step5["gate_results"]["grounding"]
    display_trace = reply.meta["multi_perspective"]["gate_trace"]["display_gate"]

    assert reply.meta["observation_status"] == "passed"
    assert reply.comment_text.strip()
    assert step5["public_comment_text_present"] is True
    assert display["passed"] is True
    assert display["binding_missing"] is False
    assert display["binding_count"] == 3
    assert display["expected_binding_count"] == 3
    assert display["pre_repair_expected_binding_count"] == 4
    assert display["candidate_body_sentence_count"] == 4
    assert display["display_binding_expected_count_source"] == "accepted_grounding_sentence_count"
    assert display["display_binding_trace_repair_applied"] is True
    assert display["display_binding_trace_repair_reason"] == "display_expected_count_aligned_to_accepted_grounding_sentence_count"
    assert display["display_binding_contract_consistent"] is True
    assert display["raw_input_included"] is False
    assert display["comment_text_body_included"] is False
    assert display["candidate_body_included"] is False
    assert display["surface_body_included"] is False
    assert grounding["binding_missing"] is False
    assert grounding["expected_binding_count"] == 3
    assert runtime["binding_missing"] is False
    assert runtime["expected_binding_count"] == 3
    assert display_trace["binding_missing"] is False
    assert display_trace["expected_binding_count"] == 3
    assert display_trace["original_expected_binding_count"] == 4
    assert display_trace["expected_binding_count_source"] == "accepted_grounding_sentence_count"
    assert display_trace["display_binding_trace_repair_applied"] is True
    assert display_trace["display_binding_contract_consistent"] is True
    assert step5["step5_contract_classification"] == "candidate_generated_public_allowed"
    assert step5["display_binding_contract_consistent"] is True
    assert step5["public_assignment_contract_consistent"] is True
    assert step5["display_binding_missing_without_exception"] is False
    assert step5["display_binding_missing_exception_allowed"] is False
    assert step5["display_binding_missing_exception_id"] == ""
    assert step5["display_binding_rejection_reason_expected"] == ""
    assert step5["public_assignment_allowed_by_display_gate"] is True
    assert step5["public_assignment_blocked_by_binding_contract"] is False
    assert step5["step5_contract_boundary"]["body_free"] is True
    assert runtime["step5_contract_classification"] == step5["step5_contract_classification"]
    assert runtime["step5_contract_boundary"]["candidate_path_confirmed"] is True
    assert diagnostic["step5_contract_classification"] == step5["step5_contract_classification"]
    assert diagnostic["step5_display_binding_contract_consistent"] is True
    assert diagnostic["step5_public_assignment_contract_consistent"] is True
    assert diagnostic["step5_public_assignment_allowed_by_display_gate"] is True
    assert diagnostic["step5_public_assignment_blocked_by_binding_contract"] is False

    observation = build_p7_hold004_step5_candidate_gate_observation(
        step5_meta=step5,
        runtime_meta=runtime,
        reply_comment_text_present=bool(reply.comment_text),
    )
    assert observation["classification"] == "classified_without_current_red_reproduction"
    assert observation["display_binding_summary"]["display_binding_contract_consistent"] is True
    assert observation["public_assignment_summary"]["public_assignment_contract_consistent"] is True

    rule = build_p7_hold004_step5_display_binding_contract_decision_rule(observation=observation)
    assert rule["status"] == "DECISION_RULE_FIXED_NO_CURRENT_RED"
    assert rule["current_public_assignment_allowed"] is True
    assert rule["release_allowed"] is False
    _assert_body_free_material(observation)



def test_r4c_stale_test_expectation_updates_fail_closed_to_contract_consistency_body_free() -> None:
    before = _frozen_pre_repair_observation()
    after = _post_r4b_repaired_observation()
    matrix = build_p7_hold004_step5_conflicting_contract_pair_matrix(observations=[before])
    pre_rule = build_p7_hold004_step5_display_binding_contract_decision_rule(observation=before)
    owner = build_p7_hold004_step5_owner_layer_decision(
        observation=before,
        decision_rule=pre_rule,
        conflict_matrix=matrix,
    )
    r4b = build_p7_hold004_step5_r4b_display_binding_trace_repair_branch(
        pre_repair_observation=before,
        post_repair_observation=after,
        owner_decision=owner,
    )

    branch = build_p7_hold004_step5_r4c_stale_test_expectation_update_branch(
        observation=after,
        r4b_branch=r4b,
        conflict_matrix=matrix,
        owner_decision=owner,
    )

    assert branch["schema_version"] == P7_HOLD004_STEP5_R4C_STALE_EXPECTATION_UPDATE_SCHEMA_VERSION
    assert branch["branch"] == "R4-C"
    assert branch["status"] == "R4C_STALE_TEST_EXPECTATION_REPLACED"
    assert branch["classification"] == "stale_fail_closed_expectation_replaced_by_gate_preservation_and_binding_contract_consistency"
    assert branch["target_test_expectation_replaced"] is True
    assert branch["test_expectation_public_absence_removed"] is True
    assert branch["runtime_public_behavior_changed"] is False
    assert branch["removed_expectation_ids"] == [
        "step5_display_observation_status_must_not_pass",
        "reply_comment_text_must_be_empty",
        "public_comment_text_present_must_be_false",
    ]
    replacement = branch["replacement_contract_summary"]
    assert replacement["candidate_generated"] is True
    assert replacement["existing_gates_preserved"] is True
    assert replacement["display_gate_relaxed"] is False
    assert replacement["display_binding_contract_consistent"] is True
    assert replacement["display_binding_missing"] is False
    assert replacement["public_assignment_contract_consistent"] is True
    assert replacement["passed_only_comment_text_contract_preserved"] is True
    assert replacement["raw_input_included"] is False
    assert replacement["generated_candidate_text_included"] is False
    assert replacement["candidate_body_included"] is False
    assert replacement["comment_text_body_included"] is False
    assert branch["target_red_closed_by_r4b_r4c"] is True
    assert branch["closed_red_refs"] == [P7_HOLD004_STEP5_RED_ID]
    assert branch["unresolved_red_refs"] == []
    assert branch["unresolved_hold_refs"] == ["P7-HOLD-004"]
    assert branch["full_backend_suite_green_confirmed"] is False
    assert branch["hold004_close_allowed"] is False
    assert branch["release_allowed"] is False
    assert branch["p7_complete"] is False
    assert branch["p8_start_allowed"] is False
    assert_p7_hold004_step5_r4c_stale_test_expectation_update_branch_contract(branch)
    _assert_body_free_material(branch)


def test_r4d_mixed_contract_conflict_hold_branch_keeps_unresolved_red_as_release_blocker_body_free() -> None:
    before = _frozen_pre_repair_observation()
    rule = build_p7_hold004_step5_display_binding_contract_decision_rule(observation=before)
    matrix = build_p7_hold004_step5_conflicting_contract_pair_matrix(observations=[before])
    owner = build_p7_hold004_step5_owner_layer_decision(
        observation=before,
        decision_rule=rule,
        conflict_matrix=matrix,
    )

    branch = build_p7_hold004_step5_r4d_mixed_contract_conflict_hold_branch(
        observation=before,
        decision_rule=rule,
        conflict_matrix=matrix,
        owner_decision=owner,
    )

    assert branch["schema_version"] == P7_HOLD004_STEP5_R4D_MIXED_CONFLICT_HOLD_SCHEMA_VERSION
    assert branch["branch"] == "R4-D"
    assert branch["status"] == "R4D_MIXED_CONTRACT_CONFLICT_HELD"
    assert branch["classification"] == "mixed_contract_conflict_preserved_as_hold_material"
    assert branch["owner_layer"] == "mixed"
    assert set(branch["owner_layers"]) == {
        "step5_meta_boundary",
        "display_gate_binding_contract",
        "binding_presence_meta_source",
        "test_contract_boundary",
    }
    assert branch["mixed_owner_decision_confirmed"] is True
    assert branch["mixed_contract_conflict_preserved"] is True
    assert "display_binding_contract_consistency" in branch["mixed_conflict_components"]
    assert "display_binding_trace_expected_count_source" in branch["mixed_conflict_components"]
    assert "stale_fail_closed_test_expectation" in branch["mixed_conflict_components"]
    assert branch["display_binding_missing"] is True
    assert branch["display_binding_contract_consistent"] is False
    assert branch["display_gate_passed"] is True
    assert branch["public_comment_text_present"] is True
    assert branch["public_assignment_contract_consistent"] is False
    assert branch["selected_as_single_runtime_repair"] is False
    assert branch["runtime_public_behavior_changed"] is False
    assert branch["failing_test_kept_failed_when_r4d_selected"] is True
    assert branch["validation_matrix_connection_required"] is True
    assert branch["release_handoff_connection_required"] is True
    assert branch["validation_matrix_connection_deferred_to_r6"] is True
    assert branch["release_handoff_connection_deferred_to_r6"] is True
    assert branch["release_blocker"] is True
    assert branch["unresolved_red_refs"] == [P7_HOLD004_STEP5_RED_ID]
    assert branch["unresolved_hold_refs"] == ["P7-HOLD-004"]
    assert branch["full_backend_suite_green_confirmed"] is False
    assert branch["hold004_close_allowed"] is False
    assert branch["release_allowed"] is False
    assert branch["p7_complete"] is False
    assert branch["p8_start_allowed"] is False
    assert_p7_hold004_step5_r4d_mixed_contract_conflict_hold_branch_contract(branch)
    _assert_body_free_material(branch)


def test_r0_r1_step5_contracts_reject_body_payload_and_release_claim() -> None:
    observed_step5 = _observed_step5_fixture()

    observation = build_p7_hold004_step5_candidate_gate_observation(
        step5_meta=observed_step5,
        reply_comment_text_present=True,
    )
    closure = dict(observation)
    closure["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_step5_candidate_gate_observation_contract(closure)

    payload = dict(observation)
    payload["comment_text"] = "forbidden public body"
    with pytest.raises(ValueError):
        assert_p7_hold004_step5_candidate_gate_observation_contract(payload)

    freeze = build_p7_hold004_step5_candidate_gate_baseline_freeze(observations=[observation])
    freeze_payload = dict(freeze)
    freeze_payload["candidate_body"] = "forbidden candidate body"
    with pytest.raises(ValueError):
        assert_p7_hold004_step5_candidate_gate_baseline_freeze_contract(freeze_payload)

    matrix = build_p7_hold004_step5_conflicting_contract_pair_matrix(observations=[observation])
    matrix_payload = dict(matrix)
    matrix_payload["surface_body"] = "forbidden surface body"
    with pytest.raises(ValueError):
        assert_p7_hold004_step5_conflicting_contract_pair_matrix_contract(matrix_payload)

    rule = build_p7_hold004_step5_display_binding_contract_decision_rule(observation=observation)
    rule_payload = dict(rule)
    rule_payload["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_step5_display_binding_contract_decision_rule_contract(rule_payload)

    owner = build_p7_hold004_step5_owner_layer_decision(observation=observation, decision_rule=rule)
    owner_payload = dict(owner)
    owner_payload["comment_text"] = "forbidden public body"
    with pytest.raises(ValueError):
        assert_p7_hold004_step5_owner_layer_decision_contract(owner_payload)


def test_r6_connects_step5_material_to_p7_hold004_without_release_or_full_suite_green() -> None:
    before = _frozen_pre_repair_observation()
    rule = build_p7_hold004_step5_display_binding_contract_decision_rule(observation=before)
    matrix = build_p7_hold004_step5_conflicting_contract_pair_matrix(observations=[before])
    owner = build_p7_hold004_step5_owner_layer_decision(
        observation=before,
        decision_rule=rule,
        conflict_matrix=matrix,
    )
    r4d = build_p7_hold004_step5_r4d_mixed_contract_conflict_hold_branch(
        observation=before,
        decision_rule=rule,
        conflict_matrix=matrix,
        owner_decision=owner,
    )
    r5 = build_p7_hold004_step5_r5_meta_extension_material(observation=before)
    r6 = build_p7_hold004_step5_r6_material_connection(r5_meta_extension=r5, r4d_branch=r4d)

    assert r6["schema_version"] == P7_HOLD004_STEP5_R6_MATERIAL_CONNECTION_SCHEMA_VERSION
    assert r6["step5_display_binding_red_present"] is True
    assert r6["step5_candidate_gate_red_classified"] is True
    assert r6["release_blocker"] is True
    assert r6["full_backend_suite_green_confirmed"] is False
    assert r6["release_allowed"] is False
    assert P7_HOLD004_STEP5_RED_ID in r6["unresolved_red_refs"]
    assert "step5_display_binding_contract_consistency" in r6["required_followup_fixes"]
    assert_p7_hold004_step5_r6_material_connection_contract(r6)
    _assert_body_free_material(r6)

    backend = build_p7_backend_suite_split_matrix(hold004_step5_material_connection=r6)
    assert backend["hold004_step5_material_connection_schema_version"] == P7_HOLD004_STEP5_R6_MATERIAL_CONNECTION_SCHEMA_VERSION
    assert backend["hold004_step5_candidate_gate_red_classified"] is True
    assert backend["hold004_step5_display_binding_red_present"] is True
    assert backend["hold004_step5_full_backend_suite_green_confirmed"] is False
    assert backend["hold004_step5_release_allowed"] is False
    assert P7_HOLD004_STEP5_RED_ID in backend["hold004_step5_unresolved_red_refs"]
    assert "step5_display_binding_contract_consistency" in backend["hold004_step5_required_followup_fixes"]
    assert_p7_backend_suite_split_matrix_contract(backend)

    r10 = build_p7_r10_hold_matrix(
        backend_suite_split_matrix=backend,
        hold004_step5_material_connection=r6,
    )
    assert r10["hold004_step5_material_connection_schema_version"] == P7_HOLD004_STEP5_R6_MATERIAL_CONNECTION_SCHEMA_VERSION
    assert r10["hold004_step5_candidate_gate_red_classified"] is True
    assert r10["hold004_step5_display_binding_red_present"] is True
    assert r10["hold004_step5_full_backend_suite_green_confirmed"] is False
    assert r10["hold004_step5_release_allowed"] is False
    assert P7_HOLD004_STEP5_RED_ID in r10["hold004_step5_unresolved_red_refs"]
    assert_p7_r10_hold_matrix_contract(r10)

    handoff = build_p7_release_decision_handoff(
        backend_suite_split_matrix=backend,
        r10_hold_matrix=r10,
        hold004_step5_material_connection=r6,
    )
    assert handoff["hold004_step5_material_connection_schema_version"] == P7_HOLD004_STEP5_R6_MATERIAL_CONNECTION_SCHEMA_VERSION
    assert handoff["hold004_step5_candidate_gate_red_classified"] is True
    assert handoff["hold004_step5_display_binding_red_present"] is True
    assert handoff["hold004_step5_full_backend_suite_green_confirmed"] is False
    assert handoff["hold004_step5_release_allowed"] is False
    assert handoff["release_allowed"] is False
    assert P7_HOLD004_STEP5_RED_ID in handoff["hold004_step5_unresolved_red_refs"]
    assert_p7_release_decision_handoff_contract(handoff)

    validation = build_p7_validation_regression_matrix(
        backend_suite_split_matrix=backend,
        r10_hold_matrix=r10,
        release_handoff=handoff,
        hold004_step5_material_connection=r6,
    )
    assert validation["summary"]["hold004_step5_material_connection_schema_version"] == P7_HOLD004_STEP5_R6_MATERIAL_CONNECTION_SCHEMA_VERSION
    assert validation["summary"]["hold004_step5_candidate_gate_red_classified"] is True
    assert validation["summary"]["hold004_step5_display_binding_red_present"] is True
    assert validation["summary"]["hold004_step5_full_backend_suite_green_confirmed"] is False
    assert validation["summary"]["hold004_step5_release_allowed"] is False
    row_by_kind = {row["check_kind"]: row for row in validation["matrix_rows"]}
    assert row_by_kind["hold004_step5_material_connection"]["observed_status"] == "HOLD_UNCONFIRMED"
    assert row_by_kind["hold004_step5_material_connection"]["green_claim_allowed"] is False
    assert row_by_kind["hold004_step5_material_connection"]["release_blocking"] is True
    assert P7_HOLD004_STEP5_RED_ID in row_by_kind["hold004_step5_material_connection"]["red_refs"]
    assert_p7_validation_regression_matrix_contract(validation)
    _assert_body_free_material(validation)



def _r4_material_bundle_for_r5_r6():
    pre = _frozen_pre_repair_observation()
    post = _post_r4b_repaired_observation()
    rule = build_p7_hold004_step5_display_binding_contract_decision_rule(observation=pre)
    conflict = build_p7_hold004_step5_conflicting_contract_pair_matrix(observations=[pre])
    owner = build_p7_hold004_step5_owner_layer_decision(
        observation=pre,
        decision_rule=rule,
        conflict_matrix=conflict,
    )
    r4b = build_p7_hold004_step5_r4b_display_binding_trace_repair_branch(
        pre_repair_observation=pre,
        post_repair_observation=post,
        owner_decision=owner,
    )
    r4c = build_p7_hold004_step5_r4c_stale_test_expectation_update_branch(
        observation=post,
        r4b_branch=r4b,
        conflict_matrix=conflict,
        owner_decision=owner,
    )
    r4d = build_p7_hold004_step5_r4d_mixed_contract_conflict_hold_branch(
        observation=pre,
        decision_rule=rule,
        conflict_matrix=conflict,
        owner_decision=owner,
    )
    return pre, post, r4c, r4d


def test_r5_step5_meta_extension_separates_candidate_gate_display_and_public_assignment_body_free() -> None:
    _, post, r4c, r4d = _r4_material_bundle_for_r5_r6()

    material = build_p7_hold004_step5_r5_meta_extension_material(
        observation=post,
        r4c_branch=r4c,
        r4d_branch=r4d,
    )

    assert material["schema_version"] == P7_HOLD004_STEP5_R5_META_EXTENSION_SCHEMA_VERSION
    assert material["status"] == "R5_STEP5_META_EXTENSION_READY"
    assert material["classification"] == "candidate_generated_public_allowed"
    assert material["candidate_path_confirmed"] is True
    assert material["gate_preservation_confirmed"] is True
    assert material["display_binding_contract_consistent"] is True
    assert material["public_assignment_contract_consistent"] is True
    assert material["display_binding_missing_without_exception"] is False
    assert material["public_assignment_allowed_by_display_gate"] is True
    assert material["public_assignment_blocked_by_binding_contract"] is False
    assert material["diagnostic_summary_body_free_meta_only"] is True
    assert material["multi_perspective_body_free_meta_only"] is True
    assert material["public_response_top_level_key_changed"] is False
    assert material["public_response_top_level_key_added"] is False
    assert material["runtime_public_behavior_changed"] is False
    assert material["release_allowed"] is False
    assert material["p7_complete"] is False
    assert material["p8_start_allowed"] is False
    assert material["step5_contract_boundary"]["body_free"] is True
    assert "step5_display_binding_contract_consistency" in material["required_followup_fixes"]
    assert_p7_hold004_step5_r5_meta_extension_material_contract(material)
    _assert_body_free_material(material)


def test_r6_step5_material_connection_keeps_p7_hold004_release_blocker_without_full_suite_green() -> None:
    _, post, r4c, r4d = _r4_material_bundle_for_r5_r6()
    r5 = build_p7_hold004_step5_r5_meta_extension_material(
        observation=post,
        r4c_branch=r4c,
        r4d_branch=r4d,
    )

    connection = build_p7_hold004_step5_r6_material_connection(
        r5_meta_extension=r5,
        r4c_branch=r4c,
        r4d_branch=r4d,
    )

    assert connection["schema_version"] == P7_HOLD004_STEP5_R6_MATERIAL_CONNECTION_SCHEMA_VERSION
    assert connection["status"] == "R6_P7_HOLD004_STEP5_MATERIAL_CONNECTED"
    assert connection["classification"] == "step5_display_binding_material_connected_as_hold004_release_blocker"
    assert connection["step5_candidate_gate_red_classified"] is True
    assert connection["step5_display_binding_red_present"] is True
    assert connection["step5_candidate_gate_red_closed_by_r4c"] is True
    assert connection["step5_mixed_contract_conflict_held"] is True
    assert connection["validation_matrix_connection_ready"] is True
    assert connection["release_handoff_connection_ready"] is True
    assert connection["release_blocker"] is True
    assert connection["unresolved_hold_refs"] == ["P7-HOLD-004"]
    assert connection["unresolved_red_refs"] == [P7_HOLD004_STEP5_RED_ID]
    assert "step5_display_binding_contract_consistency" in connection["required_followup_fixes"]
    assert "full_backend_suite_next_red_classification" in connection["required_followup_fixes"]
    assert connection["full_backend_suite_green_confirmed"] is False
    assert connection["hold004_close_allowed"] is False
    assert connection["release_allowed"] is False
    assert connection["p7_complete"] is False
    assert connection["p8_start_allowed"] is False
    assert connection["public_response_top_level_key_changed"] is False
    assert connection["rn_visible_contract_changed"] is False
    assert connection["db_write_path_changed"] is False
    assert_p7_hold004_step5_r6_material_connection_contract(connection)
    _assert_body_free_material(connection)
