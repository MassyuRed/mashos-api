from __future__ import annotations

import json

import pytest

from emlis_ai_observation_reply_contract import (
    MAX_OBSERVATION_INFERENCE_DEPTH,
    OBSERVATION_COMMENT_TEXT_CONTRACT,
    OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE,
    OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION,
    OBSERVATION_PUBLIC_STATUS_FOR_DISPLAY,
    OBSERVATION_REPLY_CONTRACT_VERSION,
    OBSERVATION_REPLY_KIND_ELIGIBLE,
    OBSERVATION_REPLY_KIND_LOW_INFORMATION,
    OBSERVATION_ROLE_EMPATHY,
    OBSERVATION_ROLE_INPUT_ARRANGEMENT,
    OBSERVATION_ROLE_LOW_INFO_KNOWN_SCOPE,
    OBSERVATION_ROLE_LOW_INFO_QUESTION,
    OBSERVATION_ROLE_LOW_INFO_RECEIVE,
    OBSERVATION_ROLE_STATE_VERBALIZATION,
    UNKNOWN_SLOT_EVENT,
    UNKNOWN_SLOT_TARGET,
    USER_FACT_GROUNDING_MODE_DISABLED,
    USER_FACT_GROUNDING_MODE_EXPLICIT_REFERENCE,
    USER_FACT_GROUNDING_MODE_IMPLICIT_FOCUS,
    assert_observation_reply_meta_contract,
    build_observation_reply_meta,
    dump_observation_reply_meta,
)


def test_step1_contract_builds_eligible_observation_meta_without_public_contract_changes() -> None:
    meta = build_observation_reply_meta(
        observation_reply_kind=OBSERVATION_REPLY_KIND_ELIGIBLE,
        plan="free",
        sentence_plan_observation_roles=[
            OBSERVATION_ROLE_EMPATHY,
            OBSERVATION_ROLE_INPUT_ARRANGEMENT,
            OBSERVATION_ROLE_STATE_VERBALIZATION,
        ],
        inference_depths=[1, 2, 3],
        primary_reason="current_input_has_relation",
    )

    assert meta["version"] == OBSERVATION_REPLY_CONTRACT_VERSION
    assert meta["observation_reply_kind"] == OBSERVATION_REPLY_KIND_ELIGIBLE
    assert meta["eligibility_status"] == OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE
    assert meta["eligible_for_full_observation"] is True
    assert meta["question_required"] is False
    assert meta["public_observation_status"] == OBSERVATION_PUBLIC_STATUS_FOR_DISPLAY
    assert meta["comment_text_contract"] == OBSERVATION_COMMENT_TEXT_CONTRACT
    assert meta["public_status_extended"] is False
    assert meta["observation_status_enum_extended"] is False
    assert meta["api_response_key_change"] is False
    assert meta["db_physical_name_changed"] is False
    assert meta["rn_visible_contract_changed"] is False
    assert meta["display_gate_relaxed"] is False
    assert meta["fixed_fallback_used"] is False
    assert meta["max_inference_depth_allowed"] == MAX_OBSERVATION_INFERENCE_DEPTH
    assert meta["inference_depths"] == [1, 2, 3]
    assert meta["user_fact_grounding_mode"] == USER_FACT_GROUNDING_MODE_DISABLED
    assert meta["facts_used"] == []
    assert meta["raw_input_included"] is False
    assert meta["comment_text_body_included"] is False

    assert_observation_reply_meta_contract(meta)


def test_step1_contract_builds_low_information_meta_as_internal_reply_kind_only() -> None:
    meta = build_observation_reply_meta(
        observation_reply_kind=OBSERVATION_REPLY_KIND_LOW_INFORMATION,
        plan="free",
        unknown_slots=[UNKNOWN_SLOT_EVENT, UNKNOWN_SLOT_TARGET],
        primary_reason="current_input_missing_event_and_target",
    )

    assert meta["observation_reply_kind"] == OBSERVATION_REPLY_KIND_LOW_INFORMATION
    assert meta["eligibility_status"] == OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION
    assert meta["eligible_for_full_observation"] is False
    assert meta["question_required"] is True
    assert meta["low_information_public_status_is_passed"] is True
    assert meta["public_observation_status"] == "passed"
    assert meta["user_fact_may_promote_to_eligible"] is False
    assert meta["must_not_promote_low_info_to_eligible"] is True
    assert meta["must_not_assert_current_event_from_user_fact"] is True
    assert meta["unknown_slots"] == [UNKNOWN_SLOT_EVENT, UNKNOWN_SLOT_TARGET]
    assert meta["sentence_plan_observation_roles"] == [
        OBSERVATION_ROLE_LOW_INFO_RECEIVE,
        OBSERVATION_ROLE_LOW_INFO_KNOWN_SCOPE,
        OBSERVATION_ROLE_LOW_INFO_QUESTION,
    ]

    assert_observation_reply_meta_contract(meta)


def test_step1_contract_blocks_free_user_facts_even_when_caller_passes_them() -> None:
    meta = build_observation_reply_meta(
        observation_reply_kind=OBSERVATION_REPLY_KIND_LOW_INFORMATION,
        plan="free",
        user_fact_grounding_mode=USER_FACT_GROUNDING_MODE_EXPLICIT_REFERENCE,
        user_fact_allowed=True,
        user_fact_may_hint=True,
        facts_used=[{"fact_id": "fact-env-001", "source_kind": "emotion_history"}],
    )

    assert meta["plan"] == "free"
    assert meta["user_fact_allowed"] is False
    assert meta["user_fact_read_enabled"] is False
    assert meta["user_fact_grounding_mode"] == USER_FACT_GROUNDING_MODE_DISABLED
    assert meta["user_fact_may_hint"] is False
    assert meta["facts_used"] == []
    assert meta["free_user_fact_blocked"] is True
    assert meta["user_fact_may_promote_to_eligible"] is False

    assert_observation_reply_meta_contract(meta)


def test_step1_contract_allows_subscription_fact_modes_without_promoting_low_info() -> None:
    explicit = build_observation_reply_meta(
        observation_reply_kind=OBSERVATION_REPLY_KIND_LOW_INFORMATION,
        plan="premium",
        user_fact_grounding_mode=USER_FACT_GROUNDING_MODE_EXPLICIT_REFERENCE,
        user_fact_allowed=True,
        user_fact_may_hint=True,
        facts_used=[{"fact_id": "fact-env-001", "source_kind": "emotion_history", "role": "past_input"}],
        unknown_slots=[UNKNOWN_SLOT_EVENT],
    )
    implicit = build_observation_reply_meta(
        observation_reply_kind=OBSERVATION_REPLY_KIND_ELIGIBLE,
        plan="plus",
        user_fact_grounding_mode=USER_FACT_GROUNDING_MODE_IMPLICIT_FOCUS,
        user_fact_allowed=True,
        facts_used=["fact-focus-001"],
        sentence_plan_observation_roles=[
            OBSERVATION_ROLE_INPUT_ARRANGEMENT,
            OBSERVATION_ROLE_STATE_VERBALIZATION,
        ],
    )

    assert explicit["plan"] == "subscription"
    assert explicit["user_fact_allowed"] is True
    assert explicit["user_fact_may_hint"] is True
    assert explicit["user_fact_grounding_mode"] == USER_FACT_GROUNDING_MODE_EXPLICIT_REFERENCE
    assert explicit["surface_disclosure_required"] is True
    assert explicit["facts_used"] == [
        {"fact_id": "fact-env-001", "source_kind": "emotion_history", "role": "past_input"}
    ]
    assert explicit["user_fact_may_promote_to_eligible"] is False
    assert explicit["eligible_for_full_observation"] is False

    assert implicit["plan"] == "subscription"
    assert implicit["user_fact_grounding_mode"] == USER_FACT_GROUNDING_MODE_IMPLICIT_FOCUS
    assert implicit["surface_disclosure_required"] is False
    assert implicit["facts_used"] == [{"fact_id": "fact-focus-001"}]
    assert implicit["eligible_for_full_observation"] is True

    assert_observation_reply_meta_contract(explicit)
    assert_observation_reply_meta_contract(implicit)


def test_step1_contract_dump_is_meta_only_and_text_free() -> None:
    meta = build_observation_reply_meta(
        observation_reply_kind=OBSERVATION_REPLY_KIND_LOW_INFORMATION,
        plan="free",
    )
    dumped = dump_observation_reply_meta(meta)
    parsed = json.loads(dumped)

    assert parsed["raw_input_included"] is False
    assert parsed["comment_text_included"] is False
    assert "疲れた" not in dumped
    assert "何がありましたか" not in dumped

    unsafe = dict(meta)
    unsafe["comment_text"] = "本文をmetaに入れてはいけない"
    with pytest.raises(ValueError):
        assert_observation_reply_meta_contract(unsafe)

    unsafe_flag = dict(meta)
    unsafe_flag["display_gate_relaxed"] = True
    with pytest.raises(ValueError):
        assert_observation_reply_meta_contract(unsafe_flag)


def test_step1_contract_rejects_invalid_low_info_promotion_and_fact_payload_text() -> None:
    with pytest.raises(ValueError):
        build_observation_reply_meta(
            observation_reply_kind=OBSERVATION_REPLY_KIND_LOW_INFORMATION,
            eligible_for_full_observation=True,
        )

    with pytest.raises(ValueError):
        build_observation_reply_meta(
            observation_reply_kind=OBSERVATION_REPLY_KIND_LOW_INFORMATION,
            question_required=False,
        )

    with pytest.raises(ValueError):
        build_observation_reply_meta(
            observation_reply_kind=OBSERVATION_REPLY_KIND_LOW_INFORMATION,
            plan="premium",
            user_fact_grounding_mode=USER_FACT_GROUNDING_MODE_EXPLICIT_REFERENCE,
            facts_used=[{"fact_id": "fact-unsafe", "text": "過去の本文をmetaに入れない"}],
        )

    with pytest.raises(ValueError):
        build_observation_reply_meta(
            observation_reply_kind=OBSERVATION_REPLY_KIND_ELIGIBLE,
            inference_depths=[4],
        )
