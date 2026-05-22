from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from emlis_ai_capability import resolve_emlis_ai_capability_for_tier
from emlis_ai_observation_eligibility_service import route_observation_eligibility
from emlis_ai_observation_reply_contract import (
    OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE,
    OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION,
    OBSERVATION_REPLY_KIND_ELIGIBLE,
    OBSERVATION_REPLY_KIND_LOW_INFORMATION,
    USER_FACT_GROUNDING_MODE_DISABLED,
    USER_FACT_GROUNDING_MODE_EXPLICIT_REFERENCE,
    USER_FACT_GROUNDING_MODE_IMPLICIT_FOCUS,
    UNKNOWN_SLOT_EVENT,
)
from emlis_ai_user_fact_grounding_boundary import (
    FORBIDDEN_USER_FACT_USE_ASSERT_CURRENT_EVENT,
    FORBIDDEN_USER_FACT_USE_PERSONALITY_TENDENCY,
    FORBIDDEN_USER_FACT_USE_PROMOTE_LOW_INFO,
    USER_FACT_GROUNDING_BOUNDARY_STEP,
    USER_FACT_USE_FOCUS_SELECTION,
    USER_FACT_USE_INTERNAL_QUESTION_ANSWER,
    USER_FACT_USE_RELATION_WEIGHT,
    assert_user_fact_grounding_decision_contract,
    collect_user_fact_refs_from_source_bundle,
    dump_user_fact_grounding_decision,
    resolve_user_fact_grounding_boundary,
)


def _input(memo: str) -> dict:
    return {
        "id": f"obs-step3-{abs(hash(memo))}",
        "created_at": "2026-05-20T00:00:00Z",
        "memo": memo,
        "memo_action": "",
        "emotion_details": [{"type": "疲れ", "strength": "medium"}],
        "emotions": ["疲れ"],
        "category": ["生活"],
    }


def test_step3_free_blocks_user_facts_even_when_they_are_supplied() -> None:
    eligibility = route_observation_eligibility(
        current_input=_input("環境を変えたいけど、変えられなくて疲れた。"),
        subscription_tier="free",
    )
    decision = resolve_user_fact_grounding_boundary(
        subscription_tier="free",
        eligibility_decision=eligibility,
        user_facts=[
            {
                "fact_id": "fact-env-001",
                "source_kind": "derived_user_model",
                "text": "環境を変えたいと以前残していた",
            }
        ],
    )
    meta = decision.as_meta()

    assert meta["source_step"] == USER_FACT_GROUNDING_BOUNDARY_STEP
    assert meta["plan"] == "free"
    assert meta["mode"] == USER_FACT_GROUNDING_MODE_DISABLED
    assert meta["user_fact_allowed"] is False
    assert meta["user_fact_read_enabled"] is False
    assert meta["facts_used"] == []
    assert meta["facts_ignored"] == [{"fact_id": "fact-env-001", "source_kind": "derived_user_model"}]
    assert meta["free_violation_guard"] is True
    assert meta["free_user_fact_blocked"] is True
    assert meta["fact_raw_text_stripped"] is True
    assert meta["observation_reply_meta"]["facts_used"] == []
    assert meta["observation_reply_meta"]["free_user_fact_blocked"] is True
    assert_user_fact_grounding_decision_contract(meta)


def test_step3_subscription_implicit_focus_uses_sanitized_refs_without_surface_disclosure() -> None:
    eligibility = route_observation_eligibility(
        current_input=_input("環境を変えたいけど、変えられなくて疲れた。"),
        subscription_tier="premium",
    )
    decision = resolve_user_fact_grounding_boundary(
        subscription_tier="premium",
        eligibility_decision=eligibility,
        user_facts=[
            {
                "fact_id": "fact-env-001",
                "source_kind": "derived_user_model",
                "text": "以前、環境を変えたいと書いていた",
            }
        ],
    )
    meta = decision.as_meta()
    dumped = dump_user_fact_grounding_decision(decision)

    assert meta["plan"] == "subscription"
    assert meta["mode"] == USER_FACT_GROUNDING_MODE_IMPLICIT_FOCUS
    assert meta["user_fact_allowed"] is True
    assert meta["user_fact_read_enabled"] is True
    assert meta["user_fact_may_hint"] is True
    assert meta["surface_disclosure_required"] is False
    assert meta["facts_used"] == [{"fact_id": "fact-env-001", "source_kind": "derived_user_model"}]
    assert USER_FACT_USE_FOCUS_SELECTION in meta["allowed_uses"]
    assert USER_FACT_USE_RELATION_WEIGHT in meta["allowed_uses"]
    assert USER_FACT_USE_INTERNAL_QUESTION_ANSWER not in meta["allowed_uses"]
    assert meta["observation_reply_meta"]["user_fact_grounding_mode"] == USER_FACT_GROUNDING_MODE_IMPLICIT_FOCUS
    assert "環境を変えたい" not in dumped
    assert "以前" not in dumped
    assert "text" not in json.loads(dumped)["facts_used"][0]


def test_step3_subscription_explicit_reference_requires_surface_disclosure() -> None:
    decision = resolve_user_fact_grounding_boundary(
        subscription_tier="plus",
        observation_reply_kind=OBSERVATION_REPLY_KIND_ELIGIBLE,
        eligibility_status=OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE,
        requested_mode=USER_FACT_GROUNDING_MODE_EXPLICIT_REFERENCE,
        user_facts=[{"fact_id": "fact-env-001", "source_kind": "past_input"}],
    )
    meta = decision.as_meta()

    assert meta["mode"] == USER_FACT_GROUNDING_MODE_EXPLICIT_REFERENCE
    assert meta["surface_disclosure_required"] is True
    assert USER_FACT_USE_INTERNAL_QUESTION_ANSWER in meta["allowed_uses"]
    assert meta["observation_reply_meta"]["surface_disclosure_required"] is True
    assert meta["observation_reply_meta"]["user_fact_grounding_mode"] == USER_FACT_GROUNDING_MODE_EXPLICIT_REFERENCE


def test_step3_current_input_past_reference_switches_subscription_to_explicit_mode() -> None:
    decision = resolve_user_fact_grounding_boundary(
        subscription_tier="premium",
        current_input=_input("前に話した環境のこと、また同じ感じで疲れた"),
        observation_reply_kind=OBSERVATION_REPLY_KIND_ELIGIBLE,
        eligibility_status=OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE,
        user_facts=[{"fact_id": "fact-env-001", "source_kind": "past_input"}],
    )
    meta = decision.as_meta()

    assert meta["mode"] == USER_FACT_GROUNDING_MODE_EXPLICIT_REFERENCE
    assert meta["surface_disclosure_required"] is True


def test_step3_low_information_may_hint_but_never_promotes_or_answers_current_event() -> None:
    eligibility = route_observation_eligibility(
        current_input=_input("疲れた"),
        subscription_tier="premium",
        user_facts=[{"fact_id": "fact-env-001", "source_kind": "derived_user_model", "text": "環境の話"}],
    )
    decision = resolve_user_fact_grounding_boundary(
        subscription_tier="premium",
        eligibility_decision=eligibility,
        user_facts=[{"fact_id": "fact-env-001", "source_kind": "derived_user_model", "text": "環境の話"}],
    )
    meta = decision.as_meta()
    dumped = dump_user_fact_grounding_decision(meta)

    assert meta["eligibility_status"] == OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION
    assert meta["observation_reply_kind"] == OBSERVATION_REPLY_KIND_LOW_INFORMATION
    assert meta["eligible_for_full_observation"] is False
    assert meta["question_required"] is True
    assert UNKNOWN_SLOT_EVENT in meta["unknown_slots"]
    assert meta["user_fact_may_hint"] is True
    assert meta["user_fact_may_promote_to_eligible"] is False
    assert meta["low_information_protected"] is True
    assert USER_FACT_USE_FOCUS_SELECTION in meta["allowed_uses"]
    assert USER_FACT_USE_RELATION_WEIGHT in meta["allowed_uses"]
    assert USER_FACT_USE_INTERNAL_QUESTION_ANSWER not in meta["allowed_uses"]
    assert meta["observation_reply_meta"]["observation_reply_kind"] == OBSERVATION_REPLY_KIND_LOW_INFORMATION
    assert meta["observation_reply_meta"]["question_required"] is True
    assert "環境の話" not in dumped


def test_step3_uses_capability_as_primary_plan_boundary() -> None:
    free_capability = resolve_emlis_ai_capability_for_tier("free")
    premium_capability = resolve_emlis_ai_capability_for_tier("premium")

    free_decision = resolve_user_fact_grounding_boundary(
        capability=free_capability,
        user_facts=[{"fact_id": "fact-001", "source_kind": "past_input"}],
    ).as_meta()
    premium_decision = resolve_user_fact_grounding_boundary(
        capability=premium_capability,
        user_facts=[{"fact_id": "fact-001", "source_kind": "past_input"}],
    ).as_meta()

    assert free_decision["plan"] == "free"
    assert free_decision["facts_used"] == []
    assert premium_decision["plan"] == "subscription"
    assert premium_decision["facts_used"] == [{"fact_id": "fact-001", "source_kind": "past_input"}]


def test_step3_collects_only_sanitized_source_bundle_fact_refs() -> None:
    source_bundle = SimpleNamespace(
        derived_user_model=SimpleNamespace(
            hypotheses=[SimpleNamespace(key="hyp_env", text="raw hypothesis must not surface", status="active")],
            open_topic_anchors=[SimpleNamespace(anchor_key="topic_env", label="環境")],
            recovery_anchors=[],
            interpretive_frame=SimpleNamespace(
                value_anchors=[SimpleNamespace(key="value_self", label="自分")],
                meaning_map=[SimpleNamespace(key="meaning_env", trigger="環境", likely_meaning="変えたい")],
            ),
        ),
        last_input={"id": "last-001", "memo": "raw last input"},
        same_day_recent_inputs=[{"id": "same-day-001", "memo": "raw same day"}],
        similar_inputs=[{"id": "similar-001", "memo": "raw similar"}],
        latest_today_question_answer={"id": "tq-001", "free_text": "raw tq"},
    )

    refs = collect_user_fact_refs_from_source_bundle(source_bundle)
    dumped_refs = json.dumps(refs, ensure_ascii=False, sort_keys=True)

    assert {ref["fact_id"] for ref in refs} >= {
        "hyp_env",
        "topic_env",
        "value_self",
        "meaning_env",
        "last-001",
        "same-day-001",
        "similar-001",
        "tq-001",
    }
    assert "raw" not in dumped_refs
    assert "環境" not in dumped_refs
    assert "変えたい" not in dumped_refs


def test_step3_forbidden_uses_are_always_present() -> None:
    meta = resolve_user_fact_grounding_boundary(
        subscription_tier="premium",
        user_facts=[{"fact_id": "fact-001", "source_kind": "derived_user_model"}],
    ).as_meta()

    assert FORBIDDEN_USER_FACT_USE_PROMOTE_LOW_INFO in meta["forbidden_uses"]
    assert FORBIDDEN_USER_FACT_USE_ASSERT_CURRENT_EVENT in meta["forbidden_uses"]
    assert FORBIDDEN_USER_FACT_USE_PERSONALITY_TENDENCY in meta["forbidden_uses"]


def test_step3_contract_rejects_raw_text_keys_and_forbidden_true_flags() -> None:
    valid = resolve_user_fact_grounding_boundary(
        subscription_tier="premium",
        user_facts=[{"fact_id": "fact-001", "source_kind": "derived_user_model"}],
    ).as_meta()

    invalid_text = dict(valid)
    invalid_text["facts_used"] = [{"fact_id": "fact-001", "text": "raw text"}]
    with pytest.raises(ValueError):
        assert_user_fact_grounding_decision_contract(invalid_text)

    invalid_flag = dict(valid)
    invalid_flag["user_fact_may_promote_to_eligible"] = True
    with pytest.raises(ValueError):
        assert_user_fact_grounding_decision_contract(invalid_flag)
