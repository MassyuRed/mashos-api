from __future__ import annotations

import json

from emlis_ai_observation_eligibility_service import (
    OBSERVATION_ELIGIBILITY_ROUTER_STEP,
    assert_observation_eligibility_decision_contract,
    dump_observation_eligibility_decision,
    route_observation_eligibility,
)
from emlis_ai_observation_reply_contract import (
    OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE,
    OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION,
    OBSERVATION_REPLY_KIND_ELIGIBLE,
    OBSERVATION_REPLY_KIND_LOW_INFORMATION,
    UNKNOWN_SLOT_EVENT,
    UNKNOWN_SLOT_TARGET,
)


def _input(memo: str) -> dict:
    return {
        "id": f"obs-step2-{abs(hash(memo))}",
        "created_at": "2026-05-20T00:00:00Z",
        "memo": memo,
        "memo_action": "",
        "emotion_details": [{"type": "疲れ", "strength": "medium"}],
        "emotions": ["疲れ"],
        "category": ["生活"],
    }


def test_step2_routes_short_emotion_only_to_low_information_observation() -> None:
    decision = route_observation_eligibility(
        current_input=_input("疲れた"),
        subscription_tier="free",
        user_facts=[{"fact_id": "past-env", "text": "環境を変えたいと以前残していた"}],
    )
    meta = decision.as_meta()

    assert meta["source_step"] == OBSERVATION_ELIGIBILITY_ROUTER_STEP
    assert meta["status"] == OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION
    assert meta["observation_reply_kind"] == OBSERVATION_REPLY_KIND_LOW_INFORMATION
    assert meta["eligible_for_full_observation"] is False
    assert meta["question_required"] is True
    assert UNKNOWN_SLOT_EVENT in meta["unknown_slots"]
    assert UNKNOWN_SLOT_TARGET in meta["unknown_slots"]
    assert meta["user_fact_allowed"] is False
    assert meta["user_fact_may_hint"] is False
    assert meta["user_fact_may_promote_to_eligible"] is False
    assert meta["free_user_fact_blocked"] is True
    assert meta["facts_used"] == []
    assert meta["facts_ignored"] == [{"fact_id": "past-env"}]
    assert meta["observation_reply_meta"]["facts_used"] == []
    assert_observation_eligibility_decision_contract(meta)


def test_step2_routes_clear_wish_blockage_burden_relation_to_eligible_observation() -> None:
    decision = route_observation_eligibility(
        current_input=_input("環境を変えたいけど、変えられなくて疲れた。"),
        subscription_tier="free",
    )
    meta = decision.as_meta()

    assert meta["status"] == OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE
    assert meta["observation_reply_kind"] == OBSERVATION_REPLY_KIND_ELIGIBLE
    assert meta["eligible_for_full_observation"] is True
    assert meta["question_required"] is False
    assert meta["current_input_evidence_score"] >= 0.58
    assert meta["relation_confidence"] >= 0.42
    assert "wish" in meta["detected_signal_roles"]
    assert "target" in meta["detected_signal_roles"]
    assert meta["observation_reply_meta"]["eligibility_status"] == OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE
    assert meta["observation_reply_meta"]["observation_reply_kind"] == OBSERVATION_REPLY_KIND_ELIGIBLE
    assert meta["observation_reply_meta"]["public_observation_status"] == "passed"


def test_step2_routes_short_but_targeted_fear_to_eligible_observation() -> None:
    decision = route_observation_eligibility(
        current_input=_input("明日が怖い"),
        subscription_tier="free",
    )
    meta = decision.as_meta()

    assert meta["status"] == OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE
    assert meta["observation_reply_kind"] == OBSERVATION_REPLY_KIND_ELIGIBLE
    assert meta["eligible_for_full_observation"] is True
    assert "target" in meta["detected_signal_roles"]
    assert "state" in meta["detected_signal_roles"]


def test_step2_routes_long_ambiguous_reference_to_low_information_observation() -> None:
    decision = route_observation_eligibility(
        current_input=_input("あれがまたこうなって、結局だめだった。もう無理かもしれない。"),
        subscription_tier="free",
    )
    meta = decision.as_meta()

    assert meta["status"] == OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION
    assert meta["observation_reply_kind"] == OBSERVATION_REPLY_KIND_LOW_INFORMATION
    assert meta["eligible_for_full_observation"] is False
    assert meta["question_required"] is True
    assert "vague_reference_without_target" in meta["ambiguity_reasons"]
    assert UNKNOWN_SLOT_EVENT in meta["unknown_slots"]
    assert meta["user_fact_may_promote_to_eligible"] is False


def test_step2_subscription_user_fact_may_hint_but_never_promotes_low_information() -> None:
    decision = route_observation_eligibility(
        current_input=_input("疲れた"),
        subscription_tier="premium",
        user_facts=[
            {
                "fact_id": "fact-env-001",
                "source_kind": "derived_user_model",
                "text": "以前、環境を変えたいという入力があった",
            }
        ],
    )
    meta = decision.as_meta()

    assert meta["status"] == OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION
    assert meta["observation_reply_kind"] == OBSERVATION_REPLY_KIND_LOW_INFORMATION
    assert meta["eligible_for_full_observation"] is False
    assert meta["question_required"] is True
    assert meta["user_fact_allowed"] is True
    assert meta["user_fact_may_hint"] is True
    assert meta["user_fact_may_promote_to_eligible"] is False
    assert meta["facts_used"] == [
        {"fact_id": "fact-env-001", "source_kind": "derived_user_model"}
    ]
    assert meta["observation_reply_meta"]["user_fact_grounding_mode"] == "implicit_focus"
    assert meta["observation_reply_meta"]["facts_used"] == [
        {"fact_id": "fact-env-001", "source_kind": "derived_user_model"}
    ]
    dumped = dump_observation_eligibility_decision(decision)
    assert "環境を変えたい" not in dumped
    assert "以前" not in dumped


def test_step2_free_ignores_mixed_in_user_fact_refs() -> None:
    decision = route_observation_eligibility(
        current_input=_input("環境を変えたいけど、変えられなくて疲れた。"),
        subscription_tier="free",
        user_facts=[{"fact_id": "fact-env-001", "source_kind": "derived_user_model"}],
    )
    meta = decision.as_meta()

    assert meta["status"] == OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE
    assert meta["user_fact_allowed"] is False
    assert meta["user_fact_may_hint"] is False
    assert meta["facts_used"] == []
    assert meta["facts_ignored"] == [{"fact_id": "fact-env-001", "source_kind": "derived_user_model"}]
    assert meta["free_user_fact_blocked"] is True
    assert meta["observation_reply_meta"]["facts_used"] == []
    assert meta["observation_reply_meta"]["free_user_fact_blocked"] is True


def test_step2_decision_meta_is_diagnostic_only_and_contains_no_input_or_comment_body() -> None:
    decision = route_observation_eligibility(
        current_input=_input("このままじゃいけないと分かっているのに行動できない"),
        subscription_tier="plus",
        user_facts=[{"fact_id": "fact-action-001", "text": "本文は残さない"}],
    )
    meta = decision.as_meta()
    dumped = dump_observation_eligibility_decision(meta)
    parsed = json.loads(dumped)

    assert parsed["raw_input_included"] is False
    assert parsed["comment_text_included"] is False
    assert parsed["comment_text_body_included"] is False
    assert "このまま" not in dumped
    assert "行動できない" not in dumped
    assert "本文は残さない" not in dumped
    assert "Emlis" not in dumped
    assert parsed["observation_reply_meta"]["public_status_extended"] is False
    assert parsed["observation_reply_meta"]["api_route_changed"] is False
    assert parsed["observation_reply_meta"]["db_physical_name_changed"] is False


def test_step2_uses_capability_when_subscription_tier_is_not_supplied() -> None:
    from emlis_ai_capability import resolve_emlis_ai_capability_for_tier

    premium_capability = resolve_emlis_ai_capability_for_tier("premium")
    decision = route_observation_eligibility(
        current_input=_input("疲れた"),
        capability=premium_capability,
        user_facts=[{"fact_id": "fact-env-001", "source_kind": "derived_user_model"}],
    )
    meta = decision.as_meta()

    assert meta["plan"] == "subscription"
    assert meta["user_fact_allowed"] is True
    assert meta["user_fact_may_hint"] is True
    assert meta["facts_used"] == [{"fact_id": "fact-env-001", "source_kind": "derived_user_model"}]
    assert meta["user_fact_may_promote_to_eligible"] is False
