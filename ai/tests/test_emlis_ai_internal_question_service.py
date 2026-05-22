from __future__ import annotations

import json

import pytest

from emlis_ai_internal_question_service import (
    ANSWER_STATUS_ANSWERED_BY_CURRENT_INPUT,
    ANSWER_STATUS_SUPPORTED_BY_USER_FACT,
    ANSWER_STATUS_UNANSWERED,
    INTERNAL_QUESTION_KIND_WHAT_IS_UNKNOWN,
    INTERNAL_QUESTION_KIND_WHAT_RELATION,
    INTERNAL_QUESTION_KIND_WHY_THIS_BURDEN,
    INTERNAL_QUESTION_KIND_WHY_THIS_WORD,
    INTERNAL_QUESTION_LAYER_STEP,
    SURFACE_USE_DISSOLVED,
    SURFACE_USE_QUESTION,
    assert_internal_question_set_contract,
    build_internal_question_set,
    dump_internal_question_set,
)
from emlis_ai_observation_eligibility_service import route_observation_eligibility
from emlis_ai_observation_reply_contract import (
    OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE,
    OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION,
    OBSERVATION_REPLY_KIND_ELIGIBLE,
    OBSERVATION_REPLY_KIND_LOW_INFORMATION,
    UNKNOWN_SLOT_EVENT,
    USER_FACT_GROUNDING_MODE_EXPLICIT_REFERENCE,
    USER_FACT_GROUNDING_MODE_IMPLICIT_FOCUS,
)
from emlis_ai_user_fact_grounding_boundary import resolve_user_fact_grounding_boundary


def _input(memo: str) -> dict:
    return {
        "id": f"obs-step4-{abs(hash(memo))}",
        "created_at": "2026-05-20T00:00:00Z",
        "memo": memo,
        "memo_action": "",
        "emotion_details": [{"type": "疲れ", "strength": "medium"}],
        "emotions": ["疲れ"],
        "category": ["生活"],
    }


def _by_kind(meta: dict, kind: str) -> list[dict]:
    return [item for item in meta["questions"] if item["kind"] == kind]


def test_step4_builds_eligible_internal_questions_from_current_input() -> None:
    current_input = _input("環境を変えたいけど、変えられなくて疲れた。")
    eligibility = route_observation_eligibility(current_input=current_input, subscription_tier="free")
    result = build_internal_question_set(current_input=current_input, eligibility_decision=eligibility)
    meta = result.as_meta()

    assert meta["source_step"] == INTERNAL_QUESTION_LAYER_STEP
    assert meta["observation_reply_kind"] == OBSERVATION_REPLY_KIND_ELIGIBLE
    assert meta["eligibility_status"] == OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE
    assert meta["question_required"] is False
    assert meta["overclaim_guard_passed"] is True
    assert meta["max_inference_depth_allowed"] == 3
    assert meta["answered_by_current_input_count"] >= 2
    assert meta["unanswered_count"] == 0
    assert meta["supported_by_user_fact_count"] == 0

    kinds = {item["kind"] for item in meta["questions"]}
    assert INTERNAL_QUESTION_KIND_WHY_THIS_WORD in kinds
    assert INTERNAL_QUESTION_KIND_WHAT_RELATION in kinds
    assert INTERNAL_QUESTION_KIND_WHY_THIS_BURDEN in kinds
    assert all(item["answer_status"] == ANSWER_STATUS_ANSWERED_BY_CURRENT_INPUT for item in meta["questions"])
    assert max(item["inference_depth"] for item in meta["questions"]) == 3
    assert not any(item["surface_use"] == SURFACE_USE_QUESTION for item in meta["questions"])
    assert_internal_question_set_contract(meta)


def test_step4_low_information_keeps_unanswered_question_surface() -> None:
    current_input = _input("疲れた")
    result = build_internal_question_set(current_input=current_input, subscription_tier="free")
    meta = result.as_meta()

    assert meta["observation_reply_kind"] == OBSERVATION_REPLY_KIND_LOW_INFORMATION
    assert meta["eligibility_status"] == OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION
    assert meta["question_required"] is True
    assert meta["low_information_question_surface_required"] is True
    assert UNKNOWN_SLOT_EVENT in meta["unknown_slots"]
    assert meta["unanswered_count"] >= 1
    unknown_questions = _by_kind(meta, INTERNAL_QUESTION_KIND_WHAT_IS_UNKNOWN)
    assert unknown_questions
    assert unknown_questions[0]["answer_status"] == ANSWER_STATUS_UNANSWERED
    assert unknown_questions[0]["surface_use"] == SURFACE_USE_QUESTION
    assert unknown_questions[0]["supporting_user_fact_ids"] == []
    assert max(item["inference_depth"] for item in meta["questions"]) <= 2
    assert_internal_question_set_contract(meta)


def test_step4_subscription_explicit_user_fact_can_support_eligible_internal_question() -> None:
    current_input = _input("前に話した環境のこと、また同じ感じで疲れた。")
    eligibility = route_observation_eligibility(current_input=current_input, subscription_tier="premium")
    grounding = resolve_user_fact_grounding_boundary(
        subscription_tier="premium",
        current_input=current_input,
        eligibility_decision=eligibility,
        requested_mode=USER_FACT_GROUNDING_MODE_EXPLICIT_REFERENCE,
        user_facts=[{"fact_id": "fact-env-001", "source_kind": "past_input", "text": "環境の過去入力"}],
    )
    result = build_internal_question_set(
        current_input=current_input,
        eligibility_decision=eligibility,
        user_fact_grounding_decision=grounding,
    )
    meta = result.as_meta()
    dumped = dump_internal_question_set(result)

    assert meta["observation_reply_kind"] == OBSERVATION_REPLY_KIND_ELIGIBLE
    assert meta["user_fact_grounding_mode"] == USER_FACT_GROUNDING_MODE_EXPLICIT_REFERENCE
    assert meta["supported_by_user_fact_count"] == 1
    supported = [item for item in meta["questions"] if item["answer_status"] == ANSWER_STATUS_SUPPORTED_BY_USER_FACT]
    assert supported[0]["supporting_user_fact_ids"] == ["fact-env-001"]
    assert supported[0]["surface_use"] == SURFACE_USE_DISSOLVED
    assert supported[0]["inference_depth"] <= 3
    assert "環境の過去入力" not in dumped
    assert "text" not in json.dumps(meta["observation_reply_meta"].get("facts_used", []), ensure_ascii=False)
    assert_internal_question_set_contract(meta)


def test_step4_low_information_subscription_fact_stays_focus_hint_not_internal_answer() -> None:
    current_input = _input("疲れた")
    result = build_internal_question_set(
        current_input=current_input,
        subscription_tier="premium",
        user_facts=[{"fact_id": "fact-env-001", "source_kind": "derived_user_model", "text": "環境の話"}],
    )
    meta = result.as_meta()
    dumped = dump_internal_question_set(meta)

    assert meta["observation_reply_kind"] == OBSERVATION_REPLY_KIND_LOW_INFORMATION
    assert meta["question_required"] is True
    assert meta["user_fact_grounding_mode"] == USER_FACT_GROUNDING_MODE_IMPLICIT_FOCUS
    assert meta["user_fact_focus_hint_ids"] == ["fact-env-001"]
    assert meta["supported_by_user_fact_count"] == 0
    assert all(item["answer_status"] != ANSWER_STATUS_SUPPORTED_BY_USER_FACT for item in meta["questions"])
    assert any(item["answer_status"] == ANSWER_STATUS_UNANSWERED for item in meta["questions"])
    assert "環境の話" not in dumped
    assert_internal_question_set_contract(meta)


def test_step4_auto_resolves_step2_and_step3_when_not_supplied() -> None:
    meta = build_internal_question_set(
        current_input=_input("このままじゃいけないと分かっているのに行動できない。"),
        subscription_tier="free",
    ).as_meta()

    assert meta["observation_reply_kind"] == OBSERVATION_REPLY_KIND_ELIGIBLE
    assert meta["answered_by_current_input_count"] >= 2
    assert meta["plan"] == "free"
    assert meta["observation_reply_meta"]["public_observation_status"] == "passed"
    assert_internal_question_set_contract(meta)


def test_step4_contract_is_meta_only_and_rejects_overclaim_or_public_drift() -> None:
    valid = build_internal_question_set(current_input=_input("疲れた"), subscription_tier="free").as_meta()
    dumped = dump_internal_question_set(valid)

    assert "疲れた" not in dumped
    assert "何がありましたか" not in dumped
    assert valid["raw_input_included"] is False
    assert valid["comment_text_body_included"] is False

    invalid_text = dict(valid)
    invalid_text["raw_input"] = "疲れた"
    with pytest.raises(ValueError):
        assert_internal_question_set_contract(invalid_text)

    invalid_depth = dict(valid)
    invalid_depth["questions"] = [dict(item) for item in valid["questions"]]
    invalid_depth["questions"][0]["inference_depth"] = 4
    with pytest.raises(ValueError):
        assert_internal_question_set_contract(invalid_depth)

    invalid_flag = dict(valid)
    invalid_flag["api_route_changed"] = True
    with pytest.raises(ValueError):
        assert_internal_question_set_contract(invalid_flag)


def test_step4_contract_rejects_low_info_answered_by_user_fact() -> None:
    valid = build_internal_question_set(
        current_input=_input("疲れた"),
        subscription_tier="premium",
        user_facts=[{"fact_id": "fact-env-001", "source_kind": "derived_user_model"}],
    ).as_meta()
    invalid = dict(valid)
    invalid["questions"] = [dict(item) for item in valid["questions"]]
    invalid["questions"][0]["answer_status"] = ANSWER_STATUS_SUPPORTED_BY_USER_FACT
    invalid["questions"][0]["supporting_user_fact_ids"] = ["fact-env-001"]
    invalid["questions"][0]["allowed_user_fact_uses"] = ["internal_question_answer"]

    with pytest.raises(ValueError):
        assert_internal_question_set_contract(invalid)
