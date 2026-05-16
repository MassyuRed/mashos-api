from __future__ import annotations

from emlis_ai_complete_composer_client import (
    CocolonCompleteComposerClient,
    build_complete_composer_client_contract_meta,
    build_complete_composer_client_runtime_gate,
)
from emlis_ai_composer_client_registry import resolve_emlis_ai_composer_client
from emlis_ai_limited_composer_client import CocolonAPlanEquivalentComposerClient


def _payload(previous_rejection_reasons=None):
    return {
        "evidence_spans": [
            {
                "span_id": "e1",
                "raw_text": "でも少し整えたい気持ちもある",
                "detected_type": "event",
                "source_field": "memo",
                "confidence": 1.0,
            }
        ],
        "limited_observation_scope": {
            "coverage_groups": ["recovery"],
            "coverage_scope": "recovery",
        },
        "observation_graph": {
            "value_or_strength_signals": [{"claim_id": "c1"}],
            "safety_boundaries": [],
            "missing_information": [],
        },
        "composition_contract": {
            "previous_rejection_reasons": list(previous_rejection_reasons or []),
        },
    }


def test_complete_composer_client_contract_meta_keeps_public_contract_unchanged() -> None:
    meta = build_complete_composer_client_contract_meta()

    assert meta["complete_composer_client_added"] is True
    assert meta["ap0_green_required"] is True
    assert meta["rollout_allowed_required"] is True
    assert meta["used_evidence_required"] is True
    assert meta["comment_text_contract"] == "passed_only"
    assert meta["response_shape_changed"] is False
    assert meta["public_response_key_change"] is False
    assert meta["api_route_changed"] is False
    assert meta["db_physical_name_changed"] is False
    assert meta["rn_visible_title_changed"] is False
    assert meta["external_ai_allowed"] is False
    assert meta["local_llm_allowed"] is False
    assert meta["fixed_sentence_template_allowed"] is False


def test_complete_composer_client_fail_closed_until_ap0_and_rollout_allow() -> None:
    blocked_ap0 = CocolonCompleteComposerClient(rollout_allowed=True).generate(_payload())
    assert blocked_ap0["status"] == "unavailable"
    assert blocked_ap0["comment_text"] == ""
    assert "complete_initial_ap0_not_green" in blocked_ap0["rejection_reasons"]

    blocked_rollout = CocolonCompleteComposerClient(ap0_green=True, rollout_allowed=False).generate(_payload())
    assert blocked_rollout["status"] == "unavailable"
    assert blocked_rollout["comment_text"] == ""
    assert "complete_initial_rollout_not_allowed" in blocked_rollout["rejection_reasons"]


def test_complete_composer_client_generates_binding_first_candidate_when_gates_allow() -> None:
    client = CocolonCompleteComposerClient(ap0_green=True, rollout_allowed=True)
    response = client.generate(_payload())
    meta = response["composer_meta"]

    assert response["status"] == "generated"
    assert response["composer_source"] == "ai_generated"
    assert response["comment_text"]
    assert response["used_evidence_span_ids"]
    assert response["used_phrase_unit_ids"]
    assert meta["complete_composer_client_added"] is True
    assert meta["ready"] is True
    assert meta["comment_text_key_written"] is False
    assert meta["external_ai_used"] is False
    assert meta["local_llm_used"] is False
    assert meta["fixed_sentence_template_used"] is False
    assert meta["grounding_input"]["binding_count"] >= 1
    assert meta["sentence_bindings"]
    assert meta["complete_composer_candidate"]["status"] == "generated"


def test_complete_composer_client_runtime_gate_blocks_external_ai_and_missing_rollout() -> None:
    blocked = build_complete_composer_client_runtime_gate(
        payload={"external_ai_used": True},
        ap0_decision={"can_proceed_to_a1": True},
        release_allowed=False,
        require_ap0_green=True,
    )

    assert blocked["ready"] is False
    assert "rollout_gate_not_allowed" in blocked["blocking_reasons"]
    assert "external_ai_used" in blocked["blocking_reasons"]
    assert blocked["display_gate_relaxed"] is False
    assert blocked["response_shape_changed"] is False


def test_registry_routes_complete_initial_only_when_ap0_and_rollout_are_green() -> None:
    env = {
        "COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED": "true",
        "COCOLON_EMLIS_DEFAULT_COMPOSER": "complete_composer_initial",
    }
    blocked = resolve_emlis_ai_composer_client(env=env, release_allowed=True)
    assert blocked.composer_client is None
    assert "complete_initial_ap0_not_green" in blocked.rejection_reasons

    resolved = resolve_emlis_ai_composer_client(
        env=env,
        release_allowed=True,
        release_meta={"stage": "internal", "enabled": True},
        ap0_decision={"can_proceed_to_a1": True},
    )
    assert isinstance(resolved.composer_client, CocolonCompleteComposerClient)
    assert resolved.resolution_source == "cocolon_complete_composer_initial"
    assert resolved.flag_state["requested_composer"] == "complete_initial"
    assert resolved.flag_state["step10_complete_composer_client_requested"] is True

    legacy = resolve_emlis_ai_composer_client(
        env={
            "COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED": "true",
            "COCOLON_EMLIS_DEFAULT_COMPOSER": "a_plan_equivalent",
        },
        release_allowed=True,
    )
    assert isinstance(legacy.composer_client, CocolonAPlanEquivalentComposerClient)
