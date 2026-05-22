from __future__ import annotations

from typing import Any

import pytest

from emlis_ai_complete_composer_types import CompleteSentencePlanLine, CompleteSentencePlanV2
from emlis_ai_low_information_observation_composer import compose_low_information_observation
from emlis_ai_observation_reply_contract import (
    OBSERVATION_REPLY_KIND_ELIGIBLE,
    OBSERVATION_REPLY_KIND_LOW_INFORMATION,
    OBSERVATION_ROLE_EMPATHY,
    OBSERVATION_ROLE_INPUT_ARRANGEMENT,
    OBSERVATION_ROLE_LOW_INFO_KNOWN_SCOPE,
    OBSERVATION_ROLE_LOW_INFO_QUESTION,
    OBSERVATION_ROLE_LOW_INFO_RECEIVE,
    OBSERVATION_ROLE_STATE_VERBALIZATION,
    UNKNOWN_SLOT_RELATION,
    UNKNOWN_SLOT_TARGET,
    USER_FACT_GROUNDING_MODE_DISABLED,
)
from emlis_ai_observation_surface_realizer_tone import (
    OBSERVATION_SURFACE_REALIZER_TONE_STEP,
    QUESTION_SURFACE_KIND_WHICH_PART_FEELS_HEAVY,
    assert_observation_surface_realizer_tone_contract,
    build_observation_surface_realizer_tone_contract_meta,
    build_observation_surface_template_report,
    build_observation_surface_tone_report,
    dump_observation_surface_realizer_tone,
    realize_eligible_observation_surface,
    realize_low_information_observation_surface,
    select_observation_question_ending,
)


def _input(memo: str) -> dict[str, Any]:
    return {
        "id": f"obs-surface-step9-{abs(hash(memo))}",
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
        "reply_text",
    }
    if isinstance(value, dict):
        return any(key in forbidden or _has_raw_or_comment_key(item) for key, item in value.items())
    if isinstance(value, (list, tuple, set)):
        return any(_has_raw_or_comment_key(item) for item in value)
    return False


def _eligible_sentence_plan() -> CompleteSentencePlanV2:
    return CompleteSentencePlanV2(
        plan_id="step9_observation_surface_eligible",
        sentence_budget=3,
        coverage_group="observation_reply",
        sentence_plans=(
            CompleteSentencePlanLine(
                sentence_id="s_opening",
                line_role="opening",
                relation_type="receive",
                phrase_unit_ids=("pu_receive",),
                evidence_span_ids=("ev_receive",),
                meta={
                    "observation_roles": [OBSERVATION_ROLE_EMPATHY, OBSERVATION_ROLE_INPUT_ARRANGEMENT],
                    "surface_role_merge": ["empathy+input_arrangement"],
                    "observation_reply_kind": OBSERVATION_REPLY_KIND_ELIGIBLE,
                    "user_fact_grounding_mode": USER_FACT_GROUNDING_MODE_DISABLED,
                },
            ),
            CompleteSentencePlanLine(
                sentence_id="s_relation",
                line_role="relation",
                relation_type="pressure",
                phrase_unit_ids=("pu_relation",),
                evidence_span_ids=("ev_relation",),
                meta={
                    "observation_roles": [OBSERVATION_ROLE_STATE_VERBALIZATION],
                    "inference_depth": 2,
                    "observation_reply_kind": OBSERVATION_REPLY_KIND_ELIGIBLE,
                    "user_fact_grounding_mode": USER_FACT_GROUNDING_MODE_DISABLED,
                },
            ),
        ),
        meta={
            "observation_reply_kind": OBSERVATION_REPLY_KIND_ELIGIBLE,
            "eligibility_status": "eligible",
            "question_required": False,
            "user_fact_grounding_mode": USER_FACT_GROUNDING_MODE_DISABLED,
        },
    )


def test_step9_contract_meta_is_meta_only_and_preserves_runtime_contracts() -> None:
    meta = build_observation_surface_realizer_tone_contract_meta()

    assert meta["source_step"] == OBSERVATION_SURFACE_REALIZER_TONE_STEP
    assert meta["surface_realizer_observation_roles_supported"] is True
    assert meta["low_info_question_ending_by_unknown_slot"] is True
    assert meta["eligible_relation_state_verbalization_enabled"] is True
    assert meta["tone_guard_blocks_empathy_only"] is True
    assert meta["template_guard_detects_skeleton_repeat"] is True
    assert meta["comment_text_generated"] is False
    assert meta["public_status_extended"] is False
    assert meta["observation_status_enum_extended"] is False
    assert meta["api_route_changed"] is False
    assert meta["db_physical_name_changed"] is False
    assert meta["rn_visible_contract_changed"] is False
    assert meta["display_gate_relaxed"] is False
    assert meta["external_ai_used"] is False
    assert _has_raw_or_comment_key(meta) is False
    assert_observation_surface_realizer_tone_contract(meta)


def test_step9_low_information_surface_selects_question_ending_from_unknown_slots() -> None:
    selection = select_observation_question_ending([UNKNOWN_SLOT_TARGET, UNKNOWN_SLOT_RELATION])
    assert selection["question_surface_kind"] == QUESTION_SURFACE_KIND_WHICH_PART_FEELS_HEAVY
    assert selection["must_not_be_complete_sentence"] is True
    assert selection["comment_text_generated"] is False

    draft = compose_low_information_observation(
        current_input=_input("疲れた"),
        eligibility_decision={
            "status": "low_information",
            "observation_reply_kind": OBSERVATION_REPLY_KIND_LOW_INFORMATION,
            "eligible_for_full_observation": False,
            "primary_reason": "insufficient_current_input_information",
            "current_input_evidence_score": 0.2,
            "relation_confidence": 0.1,
            "ambiguity_reasons": ["target_missing", "relation_missing"],
            "known_fragments": [],
            "unknown_slots": [UNKNOWN_SLOT_TARGET, UNKNOWN_SLOT_RELATION],
            "question_required": True,
            "user_fact_allowed": False,
            "user_fact_may_hint": False,
            "user_fact_may_promote_to_eligible": False,
        },
        subscription_tier="free",
    )
    surface = realize_low_information_observation_surface(draft)
    meta = surface.as_meta()

    assert meta["observation_reply_kind"] == OBSERVATION_REPLY_KIND_LOW_INFORMATION
    assert meta["eligible_for_full_observation"] is False
    assert meta["question_required"] is True
    assert meta["question_surface_kind"] == QUESTION_SURFACE_KIND_WHICH_PART_FEELS_HEAVY
    assert meta["question_ending_selected_by_unknown_slot"] is True
    assert meta["low_info_receive_present"] is True
    assert meta["low_info_known_scope_present"] is True
    assert meta["low_info_question_present"] is True
    assert meta["contains_humility_marker"] is True
    assert meta["contains_question"] is True
    assert meta["question_not_only"] is True
    assert "どの部分が重くなっていますか" in surface.body
    assert "もっと詳しく教えてください" not in surface.body
    assert meta["tone_guard_passed"] is True
    assert meta["template_guard_passed"] is True
    assert meta["comment_text_generated"] is False
    assert meta["display_gate_relaxed"] is False
    assert _has_raw_or_comment_key(meta) is False
    assert_observation_surface_realizer_tone_contract(surface)


def test_step9_eligible_surface_requires_relation_connected_state_verbalization() -> None:
    surface = realize_eligible_observation_surface(sentence_plan=_eligible_sentence_plan())
    meta = surface.as_meta()

    assert meta["observation_reply_kind"] == OBSERVATION_REPLY_KIND_ELIGIBLE
    assert meta["eligible_for_full_observation"] is True
    assert meta["question_required"] is False
    assert meta["eligible_input_arrangement_present"] is True
    assert meta["eligible_state_verbalization_present"] is True
    assert meta["eligible_state_verbalization_relation_connected"] is True
    assert set(meta["sentence_plan_observation_roles"]).issuperset(
        {OBSERVATION_ROLE_EMPATHY, OBSERVATION_ROLE_INPUT_ARRANGEMENT, OBSERVATION_ROLE_STATE_VERBALIZATION}
    )
    assert "負荷" in surface.body
    assert "ように見えます" in surface.body
    assert meta["tone_guard_passed"] is True
    assert meta["template_guard_passed"] is True
    assert meta["comment_text_generated"] is False
    assert _has_raw_or_comment_key(meta) is False
    assert_observation_surface_realizer_tone_contract(surface)


def test_step9_tone_and_template_guards_reject_comfort_only_question_only_and_public_contract_drift() -> None:
    tone_report = build_observation_surface_tone_report(
        text="つらかったですね。無理しないでくださいね。",
        observation_reply_kind=OBSERVATION_REPLY_KIND_ELIGIBLE,
    )
    assert tone_report["tone_guard_passed"] is False
    assert tone_report["generic_comfort_detected"] is True

    template_report = build_observation_surface_template_report(
        text="よければ、何がありましたか。",
        observation_reply_kind=OBSERVATION_REPLY_KIND_LOW_INFORMATION,
    )
    assert template_report["template_guard_passed"] is False
    assert template_report["question_only_detected"] is True

    valid = realize_low_information_observation_surface(current_input=_input("なんか無理"))
    invalid_public_status = dict(valid.as_meta())
    invalid_public_status["observation_status_enum_extended"] = True
    with pytest.raises(ValueError):
        assert_observation_surface_realizer_tone_contract(invalid_public_status)

    invalid_comment_text_key = dict(valid.as_meta())
    invalid_comment_text_key["comment_text"] = "Step10より前にReplyEnvelopeへ書かない"
    with pytest.raises(ValueError):
        assert_observation_surface_realizer_tone_contract(invalid_comment_text_key)

    invalid_empathy_only = dict(realize_eligible_observation_surface(sentence_plan=_eligible_sentence_plan()).as_meta())
    invalid_empathy_only["empathy_only_detected"] = True
    with pytest.raises(ValueError):
        assert_observation_surface_realizer_tone_contract(invalid_empathy_only)


def test_step9_dump_does_not_include_surface_text_or_raw_user_payload() -> None:
    surface = realize_low_information_observation_surface(current_input=_input("疲れた"))
    dumped = dump_observation_surface_realizer_tone(surface)

    assert "疲れた" not in dumped
    assert "commentText" not in dumped
    assert "realized_text" not in dumped
    assert "今は" not in dumped
    assert "よければ" not in dumped


def test_step9_short_import_path_reexports_tone_implementation() -> None:
    import emlis_ai_observation_surface_realizer as short_path

    assert short_path.OBSERVATION_SURFACE_REALIZER_STEP == OBSERVATION_SURFACE_REALIZER_TONE_STEP
    assert callable(short_path.realize_observation_surface)


def test_step9_complete_surface_realizer_exposes_observation_role_meta_without_public_contract_change() -> None:
    from emlis_ai_complete_surface_realizer import (
        build_complete_surface_realization_v2,
        build_complete_surface_realizer_contract_meta,
    )

    realization = build_complete_surface_realization_v2(sentence_plan=_eligible_sentence_plan())
    line_meta = realization.surface_lines[0].as_meta()
    contract = build_complete_surface_realizer_contract_meta()

    assert line_meta["observation_surface_realizer_step"] == OBSERVATION_SURFACE_REALIZER_TONE_STEP
    assert OBSERVATION_ROLE_EMPATHY in line_meta["observation_roles"]
    assert line_meta["observation_reply_kind"] == OBSERVATION_REPLY_KIND_ELIGIBLE
    assert line_meta["comment_text_generated"] is False
    assert contract["surface_realizer_observation_roles_supported"] is True
    assert contract["low_information_observation_roles_supported"] is True
    assert contract["unknown_slot_question_ending_policy_enabled"] is True
    assert contract["public_response_key_change"] is False
    assert contract["api_route_changed"] is False
    assert contract["db_physical_name_changed"] is False


def test_step9_template_echo_guard_consumes_observation_surface_reports_fail_closed() -> None:
    from emlis_ai_template_echo_guard import guard_template_echo

    report = guard_template_echo(
        comment_text="よければ、何がありましたか。",
        evidence_spans=[],
        composer_source="ai_generated",
        composer_meta={
            "observation_surface_template_report": {
                "release_blocker": True,
                "template_guard_reasons": ["low_info_question_only"],
            },
            "observation_surface_tone_report": {
                "release_blocker": True,
                "tone_guard_reasons": ["generic_comfort"],
            },
        },
    )

    assert report.passed is False
    assert "observation_surface_template_guard" in report.rejection_reasons
    assert "observation_surface_template:low_info_question_only" in report.rejection_reasons
    assert "observation_surface_tone_guard" in report.rejection_reasons
    assert "observation_surface_tone:generic_comfort" in report.rejection_reasons
