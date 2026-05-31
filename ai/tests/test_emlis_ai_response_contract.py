from __future__ import annotations

"""Phase20-1 guard: EmlisAI uses an internal response_kind contract.

The public/RN boundary still speaks observation_status. These tests keep the
new internal response contract additive and prevent safety/infra states from
being disguised as normal Emlis observations.
"""

import pytest

from emlis_ai_public_feedback_meta import (
    build_public_emlis_input_feedback_meta,
    should_include_public_input_feedback,
)
from emlis_ai_response_contract import (
    EMLIS_INTERNAL_RESPONSE_CONTRACT_META_KEY,
    EMLIS_INTERNAL_RESPONSE_CONTRACT_SCHEMA_VERSION,
    EmlisInternalRepairAttempt,
    EmlisInternalResponseKind,
    build_emlis_internal_response_contract,
    build_emlis_internal_response_contract_from_legacy_state,
    comment_text_required_for_response_kind,
    grounding_scope_for_response_kind,
    public_input_feedback_allowed_for_response_kind,
    public_observation_status_for_response_kind,
    public_status_from_internal_response_contract,
    response_kind_from_legacy_public_state,
    safety_triage_kind_for_response_kind,
    validate_emlis_internal_response_contract,
)


OBSERVATION_KIND_EXPECTATIONS = {
    EmlisInternalResponseKind.NORMAL_OBSERVATION.value: {
        "public_status": "passed",
        "comment_required": True,
        "public_feedback_allowed": True,
        "safety_triage_kind": "safe_observation",
        "grounding_scope": "current_input_only",
    },
    EmlisInternalResponseKind.LOW_INFORMATION_OBSERVATION.value: {
        "public_status": "passed",
        "comment_required": True,
        "public_feedback_allowed": True,
        "safety_triage_kind": "safe_observation",
        "grounding_scope": "current_input_only",
    },
    EmlisInternalResponseKind.LIMITED_GROUNDING_OBSERVATION.value: {
        "public_status": "passed",
        "comment_required": True,
        "public_feedback_allowed": True,
        "safety_triage_kind": "safe_observation",
        "grounding_scope": "current_input_only",
    },
    EmlisInternalResponseKind.SELF_DENIAL_SAFE_STATE_ANSWER.value: {
        "public_status": "passed",
        "comment_required": True,
        "public_feedback_allowed": True,
        "safety_triage_kind": "self_denial_safe_state_answer",
        "grounding_scope": "current_input_only",
    },
    EmlisInternalResponseKind.SAFETY_SUPPORT_REQUIRED.value: {
        "public_status": "safety_blocked",
        "comment_required": False,
        "public_feedback_allowed": False,
        "safety_triage_kind": "safety_support_required",
        "grounding_scope": "none",
    },
    EmlisInternalResponseKind.SAFETY_BLOCKED_EMERGENCY.value: {
        "public_status": "safety_blocked",
        "comment_required": False,
        "public_feedback_allowed": False,
        "safety_triage_kind": "safety_blocked_emergency",
        "grounding_scope": "none",
    },
    EmlisInternalResponseKind.INFRASTRUCTURE_ERROR.value: {
        "public_status": "unavailable",
        "comment_required": False,
        "public_feedback_allowed": False,
        "safety_triage_kind": "not_evaluated",
        "grounding_scope": "none",
    },
}


def test_phase20_1_internal_response_kind_mapping_is_fixed() -> None:
    assert set(OBSERVATION_KIND_EXPECTATIONS) == {kind.value for kind in EmlisInternalResponseKind}

    for response_kind, expected in OBSERVATION_KIND_EXPECTATIONS.items():
        assert public_observation_status_for_response_kind(response_kind) == expected["public_status"]
        assert comment_text_required_for_response_kind(response_kind) is expected["comment_required"]
        assert public_input_feedback_allowed_for_response_kind(response_kind) is expected["public_feedback_allowed"]
        assert safety_triage_kind_for_response_kind(response_kind) == expected["safety_triage_kind"]
        assert grounding_scope_for_response_kind(response_kind) == expected["grounding_scope"]


def test_phase20_1_contract_schema_payload_is_complete_and_repair_attempts_are_bounded() -> None:
    contract = build_emlis_internal_response_contract(
        EmlisInternalResponseKind.LIMITED_GROUNDING_OBSERVATION,
        reason="phase20_1_limited_grounding_contract",
        repair_attempts=(
            EmlisInternalRepairAttempt(
                attempt_index=0,
                repair_kind="grounding_narrow",
                from_gate="grounding_gate",
                result="passed",
            ),
        ),
    )

    assert contract == {
        "schema_version": EMLIS_INTERNAL_RESPONSE_CONTRACT_SCHEMA_VERSION,
        "response_kind": "limited_grounding_observation",
        "public_observation_status": "passed",
        "comment_text_required": True,
        "public_input_feedback_allowed": True,
        "reason": "phase20_1_limited_grounding_contract",
        "safety_triage_kind": "safe_observation",
        "grounding_scope": "current_input_only",
        "repair_attempts": [
            {
                "attempt_index": 0,
                "repair_kind": "grounding_narrow",
                "from_gate": "grounding_gate",
                "result": "passed",
            }
        ],
    }
    assert validate_emlis_internal_response_contract(contract) == []

    with pytest.raises(ValueError):
        build_emlis_internal_response_contract("phase19_case_route", reason="must_not_exist")
    with pytest.raises(ValueError):
        build_emlis_internal_response_contract(
            "normal_observation",
            reason="bad_repair",
            repair_attempts=(
                {"attempt_index": 0, "repair_kind": "case_specific_route", "from_gate": "display", "result": "passed"},
            ),
        )


def test_phase20_1_legacy_state_bridge_does_not_convert_safety_or_infra_to_normal_observation() -> None:
    assert (
        response_kind_from_legacy_public_state(
            observation_status="passed",
            observation_reply_kind="low_information_observation",
        )
        == "low_information_observation"
    )
    assert (
        response_kind_from_legacy_public_state(
            observation_status="safety_blocked",
            rejection_reasons=["self_harm_emergency"],
        )
        == "safety_blocked_emergency"
    )
    assert response_kind_from_legacy_public_state(observation_status="unavailable") == "infrastructure_error"

    emergency = build_emlis_internal_response_contract_from_legacy_state(
        observation_status="safety_blocked",
        rejection_reasons=["self_harm_emergency"],
    )
    assert emergency["response_kind"] == "safety_blocked_emergency"
    assert emergency["public_observation_status"] == "safety_blocked"
    assert emergency["public_input_feedback_allowed"] is False

    infra = build_emlis_internal_response_contract_from_legacy_state(observation_status="unavailable")
    assert infra["response_kind"] == "infrastructure_error"
    assert infra["public_observation_status"] == "unavailable"
    assert infra["comment_text_required"] is False


def test_phase20_1_public_meta_uses_internal_contract_fallback_without_leaking_internal_response_kind() -> None:
    contract = build_emlis_internal_response_contract(
        "low_information_observation",
        reason="phase20_1_public_contract_bridge",
    )
    public_meta = build_public_emlis_input_feedback_meta(
        {
            "version": "emlis_ai_v3",
            "kernel_version": "multi_perspective_observation.v1",
            EMLIS_INTERNAL_RESPONSE_CONTRACT_META_KEY: contract,
        },
        comment_text_present=True,
        subscription_tier="free",
    )

    assert public_status_from_internal_response_contract(contract) == "passed"
    assert public_meta["observation_status"] == "passed"
    assert should_include_public_input_feedback("見えている範囲だけを返す本文です。", public_meta) is True
    assert EMLIS_INTERNAL_RESPONSE_CONTRACT_META_KEY not in public_meta
    assert "response_kind" not in public_meta
    assert "public_input_feedback_allowed" not in public_meta
    assert "comment_text_required" not in public_meta


def test_phase20_7_public_meta_prefers_internal_contract_for_displayable_kinds_and_blocks_non_observation_contracts() -> None:
    passed_target_contract = build_emlis_internal_response_contract(
        "normal_observation",
        reason="phase20_7_internal_contract_public_boundary",
    )
    existing_rejected_public_meta = build_public_emlis_input_feedback_meta(
        {
            "observation_status": "rejected",
            "rejection_reasons": ["display_gate_failed"],
            EMLIS_INTERNAL_RESPONSE_CONTRACT_META_KEY: passed_target_contract,
        },
        comment_text_present=True,
        subscription_tier="free",
    )
    assert existing_rejected_public_meta["observation_status"] == "passed"
    assert should_include_public_input_feedback("本文があればPhase20-7 internal contractで表示へ接続する。", existing_rejected_public_meta) is True

    emergency_contract = build_emlis_internal_response_contract(
        "safety_blocked_emergency",
        reason="phase20_1_safety_emergency_not_converted",
    )
    emergency_public_meta = build_public_emlis_input_feedback_meta(
        {EMLIS_INTERNAL_RESPONSE_CONTRACT_META_KEY: emergency_contract},
        comment_text_present=True,
        subscription_tier="free",
    )
    assert emergency_public_meta["observation_status"] == "safety_blocked"
    assert should_include_public_input_feedback("緊急安全境界をEmlis観測として偽装しない。", emergency_public_meta) is False

    infra_contract = build_emlis_internal_response_contract(
        "infrastructure_error",
        reason="phase20_1_infra_not_faked",
    )
    infra_public_meta = build_public_emlis_input_feedback_meta(
        {EMLIS_INTERNAL_RESPONSE_CONTRACT_META_KEY: infra_contract},
        comment_text_present=True,
        subscription_tier="free",
    )
    assert infra_public_meta["observation_status"] == "unavailable"
    assert should_include_public_input_feedback("infraでは観測本文を偽装しない。", infra_public_meta) is False
