from __future__ import annotations

from typing import Any

import pytest

from emlis_ai_input_material_bundle import (
    MATERIAL_QUALITY_LOW_INFORMATION,
    build_emlis_input_material_bundle,
)
from emlis_ai_low_information_observation_composer import (
    LOW_INFORMATION_OBSERVATION_COMPOSER_STEP,
    OBSERVED_SCOPE_EMOTION_WEIGHT,
    QUESTION_SURFACE_KIND_WHAT_HAPPENED,
    QUESTION_SURFACE_KIND_WHAT_CHANGED,
    QUESTION_SURFACE_KIND_WHAT_IS_HARD_TO_SAY,
    QUESTION_SURFACE_KIND_WHICH_PART_FEELS_HEAVY,
    assert_low_information_observation_composer_contract,
    build_emlis_ai_low_information_observation,
    compose_low_information_observation,
    dump_low_information_observation_composition,
)
from emlis_ai_observation_eligibility_service import route_observation_eligibility
from emlis_ai_observation_reply_contract import (
    OBSERVATION_REPLY_KIND_LOW_INFORMATION,
    OBSERVATION_ROLE_LOW_INFO_KNOWN_SCOPE,
    OBSERVATION_ROLE_LOW_INFO_QUESTION,
    OBSERVATION_ROLE_LOW_INFO_RECEIVE,
    UNKNOWN_SLOT_CURRENT_FEELING_TARGET,
    UNKNOWN_SLOT_DESIRED_DIRECTION,
    UNKNOWN_SLOT_RELATION,
    UNKNOWN_SLOT_TARGET,
    USER_FACT_GROUNDING_MODE_DISABLED,
    USER_FACT_GROUNDING_MODE_EXPLICIT_REFERENCE,
    USER_FACT_GROUNDING_MODE_IMPLICIT_FOCUS,
)
from emlis_ai_user_fact_grounding_boundary import resolve_user_fact_grounding_boundary


def _input(memo: str) -> dict[str, Any]:
    return {
        "id": f"low-info-step8-{abs(hash(memo))}",
        "created_at": "2026-05-20T00:00:00Z",
        "memo": memo,
        "memo_action": "",
        "emotion_details": [{"type": "疲れ", "strength": "medium"}],
        "emotions": ["疲れ"],
        "category": ["生活"],
    }


def _has_raw_or_comment_key(value: Any) -> bool:
    forbidden = {
        "raw_input",
        "rawInput",
        "raw_text",
        "rawText",
        "source_text",
        "sourceText",
        "input_text",
        "user_input",
        "current_input",
        "memo",
        "memo_text",
        "comment_text",
        "commentText",
        "public_comment_text",
        "candidate_comment_text",
    }
    if isinstance(value, dict):
        return any(key in forbidden or _has_raw_or_comment_key(item) for key, item in value.items())
    if isinstance(value, (list, tuple, set)):
        return any(_has_raw_or_comment_key(item) for item in value)
    return False


def test_step8_free_short_low_information_input_gets_observation_body_and_question() -> None:
    draft = compose_low_information_observation(
        current_input=_input("疲れた"),
        subscription_tier="free",
    )
    meta = draft.as_meta()

    assert meta["source_step"] == LOW_INFORMATION_OBSERVATION_COMPOSER_STEP
    assert meta["observation_reply_kind"] == OBSERVATION_REPLY_KIND_LOW_INFORMATION
    assert meta["eligible_for_full_observation"] is False
    assert meta["question_required"] is True
    assert meta["body_non_empty"] is True
    assert meta["body_line_count"] == 3
    assert meta["contains_known_scope_observation"] is True
    assert meta["contains_humility_marker"] is True
    assert meta["contains_question"] is True
    assert meta["question_surface_kind"] == QUESTION_SURFACE_KIND_WHAT_HAPPENED
    assert OBSERVED_SCOPE_EMOTION_WEIGHT in meta["observed_scope"]
    assert set(meta["sentence_plan_observation_roles"]) == {
        OBSERVATION_ROLE_LOW_INFO_RECEIVE,
        OBSERVATION_ROLE_LOW_INFO_KNOWN_SCOPE,
        OBSERVATION_ROLE_LOW_INFO_QUESTION,
    }
    assert meta["user_fact_grounding_mode"] == USER_FACT_GROUNDING_MODE_DISABLED
    assert meta["facts_used"] == []
    assert "以前" not in draft.body
    assert "疲れた" not in draft.body
    assert "もっと詳しく教えてください" not in draft.body
    assert meta["comment_text_generated"] is False
    assert meta["display_gate_relaxed"] is False
    assert _has_raw_or_comment_key(meta) is False
    assert_low_information_observation_composer_contract(draft, current_input=_input("疲れた"))


def test_phase20_4_low_information_surface_uses_input_material_bundle_visible_and_unknown_slots() -> None:
    current_input = _input("疲れた")
    bundle = build_emlis_input_material_bundle(current_input)

    draft = compose_low_information_observation(
        current_input=current_input,
        input_material_bundle=bundle,
        subscription_tier="free",
    )
    meta = draft.as_meta()

    assert bundle.material_quality == MATERIAL_QUALITY_LOW_INFORMATION
    assert meta["phase20_4_low_information_material_surface_ready"] is True
    assert meta["low_information_surface_from_visible_material_slots"] is True
    assert meta["unknown_prompt_from_unknown_slots"] is True
    assert meta["visible_material_slots"] == list(bundle.visible_material_slots)
    assert meta["material_unknown_slots"] == list(bundle.unknown_slots)
    assert set(meta["unknown_slots"]).issuperset({"event", "cause"})
    assert "ここから見えているのは" in draft.body
    assert "詳しい出来事まではまだ見えていません" in draft.body
    assert "疲れた" not in draft.body
    assert meta["question_not_only"] is True
    assert meta["fixed_fallback_used"] is False
    assert meta["fixed_sentence_template_used"] is False
    assert _has_raw_or_comment_key(meta) is False
    assert_low_information_observation_composer_contract(draft, current_input=current_input)


def test_step8_long_ambiguous_input_stays_low_information_without_asserting_target() -> None:
    draft = build_emlis_ai_low_information_observation(
        current_input=_input("あれがまたこうなって、結局だめだった。もう無理かもしれない。"),
        subscription_tier="free",
    )
    meta = draft.as_meta()

    assert meta["observation_reply_kind"] == OBSERVATION_REPLY_KIND_LOW_INFORMATION
    assert meta["must_not_assert_current_event_from_user_fact"] is True
    assert meta["must_not_promote_low_info_to_eligible"] is True
    assert meta["contains_question"] is True
    assert any(slot in meta["unknown_slots"] for slot in ["event", "target", "relation"])
    assert "環境の件" not in draft.body
    assert "前と同じ" not in draft.body
    assert_low_information_observation_composer_contract(draft)


def test_step8_subscription_explicit_user_fact_discloses_past_but_does_not_promote_or_assert_current_event() -> None:
    user_facts = [
        {
            "id": "uf_env_weight_001",
            "text": "環境を変えたいという過去の生テキストはComposerへ出さない",
            "kind": "past_observation",
        }
    ]
    eligibility = route_observation_eligibility(
        current_input=_input("疲れた"),
        subscription_tier="premium",
        user_facts=user_facts,
    )
    boundary = resolve_user_fact_grounding_boundary(
        current_input=_input("以前にも似た感じで、疲れた"),
        eligibility_decision=eligibility,
        subscription_tier="premium",
        user_facts=user_facts,
        explicit_reference_requested=True,
    )
    draft = compose_low_information_observation(
        current_input=_input("疲れた"),
        eligibility_decision=eligibility,
        user_fact_grounding_decision=boundary,
        subscription_tier="premium",
    )
    meta = draft.as_meta()

    assert meta["plan"] == "subscription"
    assert meta["user_fact_grounding_mode"] == USER_FACT_GROUNDING_MODE_EXPLICIT_REFERENCE
    assert meta["surface_disclosure_required"] is True
    assert meta["facts_used"] == [{"fact_id": "uf_env_weight_001", "source_kind": "past_observation"}]
    assert "以前" in draft.body
    assert "今回何が起きたかまではまだ見えていません" in draft.body
    assert "環境を変えたい" not in draft.body
    assert meta["eligible_for_full_observation"] is False
    assert meta["user_fact_may_promote_to_eligible"] is False
    assert meta["assert_current_event_from_user_fact"] is False
    assert meta["user_fact_used_for_current_event_assertion"] is False
    dumped = dump_low_information_observation_composition(draft)
    assert "過去の生テキスト" not in dumped
    assert "commentText" not in dumped
    assert_low_information_observation_composer_contract(draft)


def test_step8_subscription_implicit_user_fact_keeps_fact_as_focus_hint_without_surface_disclosure() -> None:
    user_facts = [{"id": "uf_repeat_weight_001", "kind": "past_observation", "text": "raw fact must be stripped"}]
    draft = compose_low_information_observation(
        current_input=_input("なんか無理"),
        subscription_tier="plus",
        user_facts=user_facts,
    )
    meta = draft.as_meta()

    assert meta["plan"] == "subscription"
    assert meta["user_fact_grounding_mode"] == USER_FACT_GROUNDING_MODE_IMPLICIT_FOCUS
    assert meta["surface_disclosure_required"] is False
    assert meta["facts_used"] == [{"fact_id": "uf_repeat_weight_001", "source_kind": "past_observation"}]
    assert meta["user_fact_focus_hint_ids"] == ["uf_repeat_weight_001"]
    assert "以前" not in draft.body
    assert "過去" not in draft.body
    assert "raw fact" not in dump_low_information_observation_composition(draft)
    assert_low_information_observation_composer_contract(draft)


def test_step8_question_surface_changes_when_unknown_slot_is_target_or_relation() -> None:
    eligibility = route_observation_eligibility(current_input=_input("疲れた"), subscription_tier="free")
    custom_meta = dict(eligibility.as_meta())
    custom_meta["unknown_slots"] = [UNKNOWN_SLOT_TARGET, UNKNOWN_SLOT_RELATION]
    custom_meta["observation_reply_meta"] = dict(custom_meta["observation_reply_meta"])
    custom_meta["observation_reply_meta"]["unknown_slots"] = [UNKNOWN_SLOT_TARGET, UNKNOWN_SLOT_RELATION]

    draft = compose_low_information_observation(
        current_input=_input("疲れた"),
        eligibility_decision=custom_meta,
        subscription_tier="free",
    )
    meta = draft.as_meta()

    assert meta["question_surface_kind"] == QUESTION_SURFACE_KIND_WHICH_PART_FEELS_HEAVY
    assert "詳しく残せそうなら、どのあたりが重くなっているか残してみませんか" in draft.body
    assert "どの部分が重くなっていますか" not in draft.body
    assert_low_information_observation_composer_contract(draft)


def test_step8_question_surface_changes_for_direction_and_hard_to_say_slots() -> None:
    for slots, expected_kind, expected_surface in (
        (
            [UNKNOWN_SLOT_DESIRED_DIRECTION],
            QUESTION_SURFACE_KIND_WHAT_CHANGED,
            "詳しく残せそうなら、何が変わったのか残してみませんか",
        ),
        (
            [UNKNOWN_SLOT_CURRENT_FEELING_TARGET],
            QUESTION_SURFACE_KIND_WHAT_IS_HARD_TO_SAY,
            "詳しく残せそうなら、どこから言いにくくなっているか残してみませんか",
        ),
    ):
        eligibility = route_observation_eligibility(current_input=_input("疲れた"), subscription_tier="free")
        custom_meta = dict(eligibility.as_meta())
        custom_meta["unknown_slots"] = list(slots)
        custom_meta["observation_reply_meta"] = dict(custom_meta["observation_reply_meta"])
        custom_meta["observation_reply_meta"]["unknown_slots"] = list(slots)

        draft = compose_low_information_observation(
            current_input=_input("疲れた"),
            eligibility_decision=custom_meta,
            subscription_tier="free",
        )

        assert draft.as_meta()["question_surface_kind"] == expected_kind
        assert expected_surface in draft.body
        assert "よければ、何がありましたか" not in draft.body
        assert_low_information_observation_composer_contract(draft)


def test_step8_rejects_eligible_decision_question_only_and_contract_drift() -> None:
    eligible = route_observation_eligibility(
        current_input=_input("環境を変えたいけど変えられなくて疲れた"),
        subscription_tier="free",
    )
    with pytest.raises(ValueError):
        compose_low_information_observation(
            current_input=_input("環境を変えたいけど変えられなくて疲れた"),
            eligibility_decision=eligible,
            subscription_tier="free",
        )

    valid_draft = compose_low_information_observation(current_input=_input("疲れた"), subscription_tier="free")
    valid = {"body": valid_draft.body, **valid_draft.as_meta()}

    invalid_question_only = dict(valid)
    invalid_question_only["body"] = "詳しく残せそうなら、何があったか残してみませんか。"
    with pytest.raises(ValueError):
        assert_low_information_observation_composer_contract(invalid_question_only)

    invalid_legacy_question = dict(valid)
    invalid_legacy_question["body"] = "今は、言葉になる前の重さが先に出ているように見えます。まだ詳しい出来事までは見えませんが、軽く流せるものではなさそうです。よければ、何がありましたか。"
    with pytest.raises(ValueError):
        assert_low_information_observation_composer_contract(invalid_legacy_question)

    invalid_public_status = dict(valid)
    invalid_public_status["observation_status_enum_extended"] = True
    with pytest.raises(ValueError):
        assert_low_information_observation_composer_contract(invalid_public_status)

    invalid_comment_text_key = dict(valid)
    invalid_comment_text_key["comment_text"] = "まだReplyEnvelopeには入れない"
    with pytest.raises(ValueError):
        assert_low_information_observation_composer_contract(invalid_comment_text_key)
