# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import json
from collections.abc import Mapping

import pytest

from emlis_ai_p7_hold004_step5_candidate_gate_classification import (
    P7_HOLD004_STEP5_R6_MATERIAL_CONNECTION_SCHEMA_VERSION,
    P7_HOLD004_STEP5_RED_ID,
    assert_p7_hold004_step5_candidate_gate_observation_contract,
    assert_p7_hold004_step5_conflicting_contract_pair_matrix_contract,
    assert_p7_hold004_step5_display_binding_contract_decision_rule_contract,
    assert_p7_hold004_step5_r5_meta_extension_material_contract,
    assert_p7_hold004_step5_r6_material_connection_contract,
    build_p7_hold004_step5_candidate_gate_observation,
    build_p7_hold004_step5_conflicting_contract_pair_matrix,
    build_p7_hold004_step5_display_binding_contract_decision_rule,
    build_p7_hold004_step5_owner_layer_decision,
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
        user_id="p7-hold004-step5-r7-r8-target-validation-user",
        subscription_tier="free",
        current_input=_sample_current_input("p7-hold004-step5-r7-r8-target-validation-input"),
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
                "binding_missing_exception_allowed": False,
                "binding_missing_exception_id": "",
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


def _pre_repair_observation() -> dict[str, object]:
    return build_p7_hold004_step5_candidate_gate_observation(
        step5_meta=_observed_step5_fixture(),
        reply_comment_text_present=True,
    )


def _post_repair_observation() -> dict[str, object]:
    return build_p7_hold004_step5_candidate_gate_observation(
        step5_meta=_observed_step5_fixture(
            display_binding_missing=False,
            display_expected_binding_count=3,
            public_comment_text_present=True,
        ),
        reply_comment_text_present=True,
    )


def _r6_validation_bundle() -> dict[str, Mapping[str, object]]:
    pre = _pre_repair_observation()
    post = _post_repair_observation()
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
    r5 = build_p7_hold004_step5_r5_meta_extension_material(
        observation=post,
        r4c_branch=r4c,
        r4d_branch=r4d,
    )
    r6 = build_p7_hold004_step5_r6_material_connection(
        r5_meta_extension=r5,
        r4c_branch=r4c,
        r4d_branch=r4d,
    )
    backend = build_p7_backend_suite_split_matrix(hold004_step5_material_connection=r6)
    r10 = build_p7_r10_hold_matrix(
        backend_suite_split_matrix=backend,
        hold004_step5_material_connection=r6,
    )
    handoff = build_p7_release_decision_handoff(
        backend_suite_split_matrix=backend,
        r10_hold_matrix=r10,
        hold004_step5_material_connection=r6,
    )
    validation = build_p7_validation_regression_matrix(
        backend_suite_split_matrix=backend,
        r10_hold_matrix=r10,
        release_handoff=handoff,
        hold004_step5_material_connection=r6,
    )
    return {
        "pre": pre,
        "post": post,
        "rule": rule,
        "conflict": conflict,
        "r5": r5,
        "r6": r6,
        "backend": backend,
        "r10": r10,
        "handoff": handoff,
        "validation": validation,
    }


def test_r7_target_contracts_cover_binding_public_conflict_and_body_free_requirements() -> None:
    pre = _pre_repair_observation()
    post = _post_repair_observation()
    pre_rule = build_p7_hold004_step5_display_binding_contract_decision_rule(observation=pre)
    post_rule = build_p7_hold004_step5_display_binding_contract_decision_rule(observation=post)
    conflict = build_p7_hold004_step5_conflicting_contract_pair_matrix(observations=[pre])

    assert pre["display_binding_summary"]["binding_missing"] is True
    assert pre["display_binding_summary"]["passed"] is True
    assert pre_rule["rule_results"]["binding_missing_without_exception"] is True
    assert pre_rule["rule_results"]["display_binding_contract_consistent"] is False
    assert pre_rule["rule_results"]["public_assignment_contract_consistent"] is False

    assert post["display_binding_summary"]["binding_missing"] is False
    assert post_rule["rule_results"]["display_binding_contract_consistent"] is True
    assert post_rule["rule_results"]["public_assignment_contract_consistent"] is True
    assert post_rule["current_public_assignment_allowed"] is True

    pair_ids = {row["pair_id"] for row in conflict["contract_pairs"]}
    assert "step5_fail_closed_vs_phase20_public_recovery" in pair_ids
    assert "step5_step7_existing_gate_preservation_boundary" in pair_ids
    assert conflict["public_display_permission_decided"] is False
    assert conflict["stale_or_regression_decided"] is False
    assert conflict["display_binding_contract_consistency_required"] is True

    for material in (pre, post, pre_rule, post_rule, conflict):
        _assert_body_free_material(material)
    assert_p7_hold004_step5_candidate_gate_observation_contract(pre)
    assert_p7_hold004_step5_candidate_gate_observation_contract(post)
    assert_p7_hold004_step5_display_binding_contract_decision_rule_contract(pre_rule)
    assert_p7_hold004_step5_display_binding_contract_decision_rule_contract(post_rule)
    assert_p7_hold004_step5_conflicting_contract_pair_matrix_contract(conflict)


def test_r7_runtime_target_step5_meta_preserves_gates_and_public_assignment_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reply = asyncio.run(_render_step5_reply(monkeypatch))
    diagnostic = reply.meta["diagnostic_summary"]
    step5 = diagnostic["complete_initial_candidate_generation_path"]
    display = step5["gate_results"]["display"]
    display_trace = reply.meta["multi_perspective"]["gate_trace"]["display_gate"]

    assert reply.meta["observation_status"] == "passed"
    assert reply.comment_text.strip()
    assert step5["candidate_generated"] is True
    assert step5["candidate_generated_before_display_gate"] is True
    assert step5["existing_reader_grounding_template_display_gates_preserved"] is True
    assert step5["display_gate_relaxed"] is False

    assert display["passed"] is True
    assert display["binding_missing"] is False
    assert display["binding_count"] == 3
    assert display["expected_binding_count"] == 3
    assert display["display_binding_contract_consistent"] is True
    assert display["display_binding_trace_repair_applied"] is True
    assert display_trace["display_binding_contract_consistent"] is True
    assert display_trace["display_binding_trace_repair_applied"] is True

    assert step5["public_comment_text_present"] is True
    assert step5["passed_only_comment_text_contract_preserved"] is True
    assert step5["display_binding_contract_consistent"] is True
    assert step5["public_assignment_contract_consistent"] is True
    assert step5["public_assignment_allowed_by_display_gate"] is True
    assert step5["public_assignment_blocked_by_binding_contract"] is False

    for key in (
        "raw_input_included",
        "generated_candidate_text_included",
        "candidate_text_included",
    ):
        assert step5[key] is False

    # The runtime Step5 diagnostic does not expose public/candidate/surface body
    # content.  Existing body flags are checked directly above; absent body keys
    # stay absent instead of becoming new public response shape.
    for absent_key in (
        "comment_text_body",
        "candidate_body",
        "surface_body",
        "comment_text_body_included",
        "candidate_body_included",
        "surface_body_included",
    ):
        assert absent_key not in step5


def test_r8_subset_validation_chain_keeps_hold004_unresolved_without_release_or_full_suite_green() -> None:
    bundle = _r6_validation_bundle()
    r6 = bundle["r6"]
    backend = bundle["backend"]
    r10 = bundle["r10"]
    handoff = bundle["handoff"]
    validation = bundle["validation"]

    assert r6["schema_version"] == P7_HOLD004_STEP5_R6_MATERIAL_CONNECTION_SCHEMA_VERSION
    assert r6["step5_candidate_gate_red_classified"] is True
    assert r6["step5_display_binding_red_present"] is True
    assert r6["release_blocker"] is True
    assert r6["full_backend_suite_green_confirmed"] is False
    assert r6["hold004_close_allowed"] is False
    assert r6["release_allowed"] is False
    assert r6["p7_complete"] is False
    assert r6["p8_start_allowed"] is False
    assert P7_HOLD004_STEP5_RED_ID in r6["unresolved_red_refs"]
    assert "full_backend_suite_next_red_classification" in r6["required_followup_fixes"]

    assert backend["hold004_step5_candidate_gate_red_classified"] is True
    assert backend["hold004_step5_full_backend_suite_green_confirmed"] is False
    assert backend["hold004_step5_release_allowed"] is False
    assert r10["hold004_step5_full_backend_suite_green_confirmed"] is False
    assert r10["hold004_step5_release_allowed"] is False
    assert handoff["hold004_step5_full_backend_suite_green_confirmed"] is False
    assert handoff["hold004_step5_release_allowed"] is False
    assert handoff["release_allowed"] is False

    row_by_kind = {row["check_kind"]: row for row in validation["matrix_rows"]}
    hold004_row = row_by_kind["hold004_step5_material_connection"]
    assert hold004_row["observed_status"] == "HOLD_UNCONFIRMED"
    assert hold004_row["green_claim_allowed"] is False
    assert hold004_row["release_blocking"] is True
    assert P7_HOLD004_STEP5_RED_ID in hold004_row["red_refs"]
    assert validation["summary"]["hold004_step5_full_backend_suite_green_confirmed"] is False
    assert validation["summary"]["hold004_step5_release_allowed"] is False

    for material in (r6, backend, r10, handoff, validation):
        _assert_body_free_material(material)
    assert_p7_hold004_step5_r6_material_connection_contract(r6)
    assert_p7_backend_suite_split_matrix_contract(backend)
    assert_p7_r10_hold_matrix_contract(r10)
    assert_p7_release_decision_handoff_contract(handoff)
    assert_p7_validation_regression_matrix_contract(validation)


def test_r7_target_material_rejects_body_payload_and_release_claim_regressions() -> None:
    bundle = _r6_validation_bundle()
    r5 = dict(bundle["r5"])
    r6 = dict(bundle["r6"])

    r5["comment_text"] = "body must not enter R7 target material"
    with pytest.raises(ValueError):
        assert_p7_hold004_step5_r5_meta_extension_material_contract(r5)

    r6["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_step5_r6_material_connection_contract(r6)
