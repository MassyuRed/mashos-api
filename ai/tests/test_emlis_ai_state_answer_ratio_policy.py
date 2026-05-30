from __future__ import annotations

import json

import pytest

from emlis_ai_state_answer_ratio_policy import (
    DEFAULT_HUMAN_FOLLOW_RATIO,
    DEFAULT_OBSERVATION_RATIO,
    EMLIS_AI_STATE_ANSWER_RATIO_POLICY_MATERIAL_ID,
    EMLIS_AI_STATE_ANSWER_RATIO_POLICY_PHASE,
    EMLIS_AI_STATE_ANSWER_RATIO_POLICY_SCHEMA_VERSION,
    build_emlis_ai_state_answer_ratio_policy,
    state_answer_ratio_policy_composer_payload,
    state_answer_ratio_policy_forward_meta,
    state_answer_ratio_policy_gate_report,
)
from emlis_ai_state_answer_surface_contract import build_emlis_state_answer_surface_contract


def _input(
    *,
    memo: str,
    emotion: str,
    strength: str = "medium",
    action: str = "その場で考え続けた",
    category: str = "生活",
) -> dict[str, object]:
    return {
        "id": f"ratio-policy-{emotion}-{strength}",
        "created_at": "2026-05-26T00:00:00Z",
        "memo": memo,
        "memo_action": action,
        "emotion_details": [{"type": emotion, "strength": strength}],
        "emotions": [emotion],
        "category": [category],
        "is_secret": False,
    }


def test_phase4_ratio_policy_resolves_standard_observation6_follow4_without_text_leak() -> None:
    current_input = _input(
        memo="この職場でやっていけるか不安",
        emotion="不安",
        category="仕事",
        action="新しい仕事を任された",
    )

    meta = build_emlis_ai_state_answer_ratio_policy(current_input).as_meta()
    encoded = json.dumps(meta, ensure_ascii=False, sort_keys=True)

    assert meta["schema_version"] == EMLIS_AI_STATE_ANSWER_RATIO_POLICY_SCHEMA_VERSION
    assert meta["material_id"] == EMLIS_AI_STATE_ANSWER_RATIO_POLICY_MATERIAL_ID
    assert meta["source_phase"] == EMLIS_AI_STATE_ANSWER_RATIO_POLICY_PHASE
    assert meta["state_answer_ratio_policy_connected"] is True
    assert meta["default_ratio"] == {
        "observation": DEFAULT_OBSERVATION_RATIO,
        "human_follow": DEFAULT_HUMAN_FOLLOW_RATIO,
    }
    assert meta["resolved_ratio"] == {
        "observation": 0.6,
        "human_follow": 0.4,
        "reason": "standard_state_answer",
        "range_key": "standard",
        "resolver_phase": EMLIS_AI_STATE_ANSWER_RATIO_POLICY_PHASE,
    }
    assert meta["ratio_basis"]["character_count_exact"] is False
    assert meta["ratio_basis"]["section_role_unit_plan"]["observation_units"] > 0
    assert meta["ratio_basis"]["section_role_unit_plan"]["human_follow_units"] > 0
    assert meta["observation_zero_allowed"] is False
    assert meta["human_follow_zero_allowed"] is False
    assert meta["comfort_only_allowed"] is False
    assert current_input["memo"] not in encoded
    assert current_input["memo_action"] not in encoded
    assert '"comment_text":' not in encoded
    assert '"raw_text":' not in encoded
    assert "<generator object" not in encoded


@pytest.mark.parametrize(
    ("case_name", "current_input", "expected_reason", "expected_ratio"),
    [
        (
            "self_denial",
            _input(
                memo="自分はダメな人間だと思ってしまう",
                emotion="悲しみ",
                strength="strong",
                category="仕事",
                action="ミスを思い出していた",
            ),
            "self_denial_follow_thickened",
            {"observation": 0.45, "human_follow": 0.55},
        ),
        (
            "sadness",
            _input(
                memo="大事なものを失ったようで悲しい",
                emotion="悲しみ",
                strength="strong",
                action="帰ってから泣きそうになった",
            ),
            "grief_or_loneliness_follow_thickened",
            {"observation": 0.45, "human_follow": 0.55},
        ),
        (
            "loneliness",
            _input(
                memo="誰にも言えなくて孤独で寂しい",
                emotion="悲しみ",
                strength="strong",
                category="人間関係",
                action="一人で抱えていた",
            ),
            "grief_or_loneliness_follow_thickened",
            {"observation": 0.45, "human_follow": 0.55},
        ),
        (
            "exhaustion",
            _input(
                memo="疲れ切って何もできないくらい消耗している",
                emotion="疲れ",
                strength="strong",
                category="仕事",
                action="帰宅後に動けなかった",
            ),
            "exhaustion_balanced_follow",
            {"observation": 0.5, "human_follow": 0.5},
        ),
    ],
)
def test_phase4_ratio_policy_thickens_follow_for_self_denial_grief_loneliness_and_exhaustion(
    case_name: str,
    current_input: dict[str, object],
    expected_reason: str,
    expected_ratio: dict[str, float],
) -> None:
    contract = build_emlis_state_answer_surface_contract(current_input).as_meta()
    ratio_policy = contract["ratio_policy"]
    ratio = ratio_policy["resolved_ratio"]
    unit_plan = ratio_policy["ratio_basis"]["section_role_unit_plan"]

    assert ratio["reason"] == expected_reason
    assert ratio["observation"] == expected_ratio["observation"]
    assert ratio["human_follow"] == expected_ratio["human_follow"]
    assert ratio["observation"] > 0
    assert ratio["human_follow"] > 0
    assert ratio_policy["comfort_only_allowed"] is False
    assert unit_plan["observation_units"] > 0
    assert unit_plan["human_follow_units"] > 0
    assert contract["observation_layer"]["steps"]
    assert contract["human_follow_layer"]["follow_key_slots"]


def test_phase4_ratio_policy_thickens_observation_for_user_structure_question() -> None:
    current_input = _input(
        memo="なぜ同じ不安に戻るのか、どういうことなのか知りたい",
        emotion="不安",
        category="生活",
        action="同じことで考え続けていた",
    )

    contract = build_emlis_state_answer_surface_contract(current_input).as_meta()
    ratio_policy = contract["ratio_policy"]
    ratio = ratio_policy["resolved_ratio"]
    unit_plan = ratio_policy["ratio_basis"]["section_role_unit_plan"]

    assert ratio["reason"] == "structure_question_observation_thickened"
    assert ratio["observation"] == 0.7
    assert ratio["human_follow"] == 0.3
    assert ratio_policy["resolver_context"]["structure_question_detected"] is True
    assert unit_plan["observation_units"] > unit_plan["human_follow_units"]
    assert ratio_policy["ratio_basis"]["character_count_exact"] is False


def test_phase4_ratio_policy_keeps_self_denial_follow_temperature_over_structure_question() -> None:
    current_input = _input(
        memo="なぜ自分はダメな人間だと思ってしまうのか分からない",
        emotion="悲しみ",
        strength="strong",
        category="仕事",
        action="ミスを何度も思い出していた",
    )

    ratio_policy = build_emlis_state_answer_surface_contract(current_input).as_meta()["ratio_policy"]

    assert ratio_policy["resolver_context"]["structure_question_detected"] is True
    assert ratio_policy["resolved_ratio"]["reason"] == "self_denial_follow_thickened"
    assert ratio_policy["resolved_ratio"]["human_follow"] > ratio_policy["resolved_ratio"]["observation"]
    assert ratio_policy["resolver_context"]["safety_precedence"] == "emotional_temperature_over_structure_question"


def test_phase4_ratio_policy_helpers_return_forward_gate_and_composer_payloads() -> None:
    policy = build_emlis_ai_state_answer_ratio_policy(
        _input(memo="このまま続けられるか不安", emotion="不安", category="仕事")
    )

    forward_meta = state_answer_ratio_policy_forward_meta(policy)
    gate_report = state_answer_ratio_policy_gate_report(forward_meta)
    composer_payload = state_answer_ratio_policy_composer_payload(forward_meta)

    assert forward_meta["material_id"] == EMLIS_AI_STATE_ANSWER_RATIO_POLICY_MATERIAL_ID
    assert gate_report["state_answer_ratio_policy_connected"] is True
    assert gate_report["ratio_is_character_count_exact"] is False
    assert gate_report["observation_zero_allowed"] is False
    assert gate_report["human_follow_zero_allowed"] is False
    assert gate_report["comfort_only_allowed"] is False
    assert composer_payload["state_answer_ratio_policy_material_only"] is True
    assert composer_payload["comment_text_generated"] is False
    assert composer_payload["raw_text_included"] is False


def test_phase4_ratio_policy_is_connected_into_state_answer_surface_contract() -> None:
    current_input = _input(
        memo="上司の扱いが理不尽で腹が立った",
        emotion="怒り",
        strength="strong",
        category="仕事",
        action="急な対応を求められた",
    )

    contract = build_emlis_state_answer_surface_contract(current_input).as_meta()
    gate_report = contract["ratio_policy"]

    assert gate_report["state_answer_ratio_policy_connected"] is True
    assert gate_report["material_id"] == EMLIS_AI_STATE_ANSWER_RATIO_POLICY_MATERIAL_ID
    assert gate_report["schema_version"] == EMLIS_AI_STATE_ANSWER_RATIO_POLICY_SCHEMA_VERSION
    assert gate_report["resolved_ratio"]["reason"] == "anger_standard_with_inner_value_line"
    assert gate_report["resolved_ratio"]["observation"] == 0.6
    assert gate_report["resolved_ratio"]["human_follow"] == 0.4
    assert contract["completed_reply_generated"] is False
    assert contract["public_response_key_added"] is False


def test_phase6_ratio_policy_reads_reception_mode_for_daily_unpleasant_fixture() -> None:
    from fixtures.emlis_ai_two_stage_reception_cases import (
        current_input_for_two_stage_reception_case,
        two_stage_reception_case_by_id,
    )

    current_input = current_input_for_two_stage_reception_case(
        two_stage_reception_case_by_id("daily_unpleasant_encounter_A")
    )

    meta = build_emlis_ai_state_answer_ratio_policy(current_input).as_meta()
    ratio = meta["resolved_ratio"]
    unit_plan = meta["ratio_basis"]["section_role_unit_plan"]
    reception_summary = meta["resolver_context"]["reception_mode_summary"]

    assert ratio["reason"] == "daily_unpleasant_reception_light"
    assert ratio["range_key"] == "daily_reception"
    assert 0.10 <= ratio["observation"] <= 0.30
    assert ratio["human_follow"] > ratio["observation"]
    assert unit_plan["observation_units"] == 1
    assert unit_plan["human_follow_units"] == 3
    assert reception_summary["reception_mode_id"] == "daily_unpleasant_reception"
    assert reception_summary["ratio_preset"] == "daily_unpleasant_reception_light"
    assert reception_summary["raw_text_included"] is False
    assert meta["phase6_reception_mode_ratio_policy_connected"] is True
    assert meta["comment_text_generated"] is False


def test_phase6_ratio_policy_reads_reception_mode_for_daily_positive_fixture() -> None:
    from fixtures.emlis_ai_two_stage_reception_cases import (
        current_input_for_two_stage_reception_case,
        two_stage_reception_case_by_id,
    )

    current_input = current_input_for_two_stage_reception_case(
        two_stage_reception_case_by_id("positive_change_after_work_streaming")
    )

    meta = build_emlis_ai_state_answer_ratio_policy(current_input).as_meta()
    ratio = meta["resolved_ratio"]
    unit_plan = meta["ratio_basis"]["section_role_unit_plan"]

    assert ratio["reason"] == "daily_positive_reception_light"
    assert ratio["range_key"] == "daily_reception"
    assert ratio["observation"] == 0.2
    assert ratio["human_follow"] == 0.8
    assert unit_plan["observation_units"] == 1
    assert unit_plan["human_follow_units"] == 3


def test_phase6_ratio_policy_keeps_self_confidence_uncertainty_follow_thickened() -> None:
    current_input = _input(
        memo="これでいいのかな、大丈夫なのかな、頑張れてるかなって不安",
        emotion="平穏",
        category="価値観",
        action="自分の挑戦を振り返っていた",
    )

    meta = build_emlis_ai_state_answer_ratio_policy(current_input).as_meta()
    ratio = meta["resolved_ratio"]
    unit_plan = meta["ratio_basis"]["section_role_unit_plan"]

    assert ratio["reason"] == "self_confidence_uncertainty_follow_thickened"
    assert ratio["range_key"] == "self_negative_or_uncertainty"
    assert 0.30 <= ratio["observation"] <= 0.45
    assert ratio["human_follow"] > ratio["observation"]
    assert unit_plan["observation_units"] == 2
    assert unit_plan["human_follow_units"] == 4
    assert meta["observation_zero_allowed"] is False
    assert meta["human_follow_zero_allowed"] is False



def test_phase6_ratio_policy_keeps_b_fixture_self_negative_or_uncertainty_follow_thickened() -> None:
    from fixtures.emlis_ai_two_stage_reception_cases import (
        current_input_for_two_stage_reception_case,
        two_stage_reception_case_by_id,
    )

    current_input = current_input_for_two_stage_reception_case(
        two_stage_reception_case_by_id("self_confidence_uncertainty_B")
    )

    meta = build_emlis_ai_state_answer_ratio_policy(current_input).as_meta()
    ratio = meta["resolved_ratio"]
    unit_plan = meta["ratio_basis"]["section_role_unit_plan"]
    reception_summary = meta["resolver_context"]["reception_mode_summary"]

    assert ratio["reason"] in {
        "self_denial_follow_thickened",
        "self_confidence_uncertainty_follow_thickened",
    }
    assert ratio["range_key"] == "self_negative_or_uncertainty"
    assert 0.30 <= ratio["observation"] <= 0.45
    assert ratio["human_follow"] > ratio["observation"]
    assert unit_plan["observation_units"] > 0
    assert unit_plan["human_follow_units"] > 0
    assert reception_summary["reception_mode_id"] in {"self_denial_support", "uncertainty_support"}
    assert meta["observation_zero_allowed"] is False
    assert meta["human_follow_zero_allowed"] is False

def test_phase6_ratio_policy_accepts_explicit_reception_mode_without_public_contract_change() -> None:
    current_input = _input(
        memo="このままでいいのか少し不安",
        emotion="不安",
        category="生活",
        action="予定を見直していた",
    )

    meta = build_emlis_ai_state_answer_ratio_policy(
        current_input,
        reception_mode="uncertainty_support",
    ).as_meta()
    encoded = json.dumps(meta, ensure_ascii=False, sort_keys=True)

    assert meta["resolved_ratio"]["reason"] == "self_confidence_uncertainty_follow_thickened"
    assert meta["resolver_context"]["reception_mode_summary"]["source"] == "provided_reception_mode"
    assert meta["public_response_key_added"] is False
    assert meta["rn_visible_contract_changed"] is False
    assert current_input["memo"] not in encoded
    assert current_input["memo_action"] not in encoded
    assert '"comment_text":' not in encoded
    assert '"raw_text":' not in encoded
