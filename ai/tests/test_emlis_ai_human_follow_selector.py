from __future__ import annotations

import json
from collections import Counter

import pytest

from cocolon_environment_state_output_frame import build_environment_state_output_frame
from emlis_ai_human_follow_selector import (
    EMLIS_AI_HUMAN_FOLLOW_SELECTOR_MATERIAL_ID,
    EMLIS_AI_HUMAN_FOLLOW_SELECTOR_PHASE,
    EMLIS_AI_HUMAN_FOLLOW_SELECTOR_SCHEMA_VERSION,
    FOLLOW_EFFORT_RECEIVING,
    FOLLOW_EXISTENCE_RESPECT,
    FOLLOW_EXPLICIT_REACTION_RECEIVING,
    FOLLOW_FEAR_OR_LOAD_UNDERSTANDING,
    FOLLOW_IDENTITY_COUNTER_WITH_EVIDENCE,
    FOLLOW_IMPORTANT_VALUE_RECEIVING,
    FOLLOW_NOT_OVER_EXPLAINING_DAILY_EVENT,
    FOLLOW_INTENTION_AFFIRMATION,
    FOLLOW_INTENTION_AND_FEAR,
    FOLLOW_REASON_VISIBILITY_RECEIVING,
    FOLLOW_RESPONSIBILITY_SCOPE_OBSERVATION,
    FOLLOW_SELF_DENIAL_EFFORT_EXISTENCE,
    build_emlis_ai_human_follow_selection,
    human_follow_selection_composer_payload,
    human_follow_selection_forward_meta,
    human_follow_selection_gate_report,
)
from emlis_ai_state_answer_surface_contract import build_emlis_state_answer_surface_contract
from fixtures.emlis_ai_two_stage_reception_cases import (
    current_input_for_two_stage_reception_case,
    two_stage_reception_case_by_id,
)


def _input(
    *,
    memo: str,
    emotion: str,
    strength: str = "medium",
    action: str = "その場で考え続けた",
    category: str = "生活",
) -> dict[str, object]:
    return {
        "id": f"follow-selector-{emotion}-{strength}",
        "created_at": "2026-05-26T00:00:00Z",
        "memo": memo,
        "memo_action": action,
        "emotion_details": [{"type": emotion, "strength": strength}],
        "emotions": [emotion],
        "category": [category],
        "is_secret": False,
    }


@pytest.mark.parametrize(
    ("case_name", "current_input", "expected_input_type", "expected_primary"),
    [
        (
            "anxiety",
            _input(memo="この職場でやっていけるか不安", emotion="不安", category="仕事", action="新しい仕事を任された"),
            "anxiety",
            FOLLOW_FEAR_OR_LOAD_UNDERSTANDING,
        ),
        (
            "anger",
            _input(memo="上司の扱いが理不尽で腹が立った", emotion="怒り", strength="strong", category="仕事", action="急な仕事を頼まれた"),
            "anger",
            FOLLOW_IMPORTANT_VALUE_RECEIVING,
        ),
        (
            "sadness",
            _input(memo="大事なものを失ったようで悲しい", emotion="悲しみ", strength="strong", action="帰ってから泣きそうになった"),
            "sadness",
            FOLLOW_EXISTENCE_RESPECT,
        ),
        (
            "self_denial",
            _input(memo="自分はダメな人間だと思ってしまう", emotion="悲しみ", strength="strong", category="仕事", action="ミスを思い出していた"),
            "self_denial",
            FOLLOW_SELF_DENIAL_EFFORT_EXISTENCE,
        ),
        (
            "ambivalence",
            _input(memo="どうしたらいいか分からなくて迷っている", emotion="不安", category="人間関係", action="相手に返事できなかった"),
            "ambivalence",
            FOLLOW_INTENTION_AND_FEAR,
        ),
        (
            "guilt",
            _input(memo="相手に迷惑をかけた気がして罪悪感がある", emotion="不安", category="人間関係", action="謝るべきか考え続けた"),
            "guilt",
            FOLLOW_INTENTION_AFFIRMATION,
        ),
        (
            "loneliness",
            _input(memo="誰にも言えなくて孤独で寂しい", emotion="悲しみ", strength="strong", category="人間関係", action="一人で抱えていた"),
            "loneliness",
            FOLLOW_EXISTENCE_RESPECT,
        ),
        (
            "exhaustion",
            _input(memo="疲れ切って何もできないくらい消耗している", emotion="疲れ", strength="strong", category="仕事", action="帰宅後に動けなかった"),
            "exhaustion",
            FOLLOW_EFFORT_RECEIVING,
        ),
        (
            "joy_or_relief",
            _input(memo="少し進められて安心したし嬉しい", emotion="喜び", category="生活", action="机を片付けられた"),
            "joy_or_relief",
            FOLLOW_EFFORT_RECEIVING,
        ),
        (
            "self_understanding",
            _input(memo="理由が少し見えて自己理解が進んだ", emotion="自己理解", category="生活", action="言葉に整理した"),
            "self_understanding",
            FOLLOW_REASON_VISIBILITY_RECEIVING,
        ),
    ],
)
def test_phase3_follow4_selector_resolves_input_type_and_follow_slots(
    case_name: str,
    current_input: dict[str, object],
    expected_input_type: str,
    expected_primary: str,
) -> None:
    meta = build_emlis_ai_human_follow_selection(current_input).as_meta()
    encoded = json.dumps(meta, ensure_ascii=False, sort_keys=True)
    slot_counts = Counter(slot["slot"] for slot in meta["follow_key_slots"])

    assert meta["schema_version"] == EMLIS_AI_HUMAN_FOLLOW_SELECTOR_SCHEMA_VERSION
    assert meta["material_id"] == EMLIS_AI_HUMAN_FOLLOW_SELECTOR_MATERIAL_ID
    assert meta["source_phase"] == EMLIS_AI_HUMAN_FOLLOW_SELECTOR_PHASE
    assert meta["selection"]["input_type"] == expected_input_type
    assert meta["primary_follow_key"] == expected_primary
    assert len(meta["secondary_follow_keys"]) == 2
    assert meta["afterglow_follow_key"]
    assert slot_counts == {"primary": 1, "secondary": 2, "afterglow": 1}
    assert meta["follow_key_slots_count"] == 4
    assert meta["follow_mode"] == "emlis_impression_not_fact"
    assert meta["emotion_label_only_selection"] is False
    assert meta["personality_claim_allowed"] is False
    assert all(slot["personality_claim_allowed"] is False for slot in meta["follow_key_slots"])
    assert all(slot["completed_reply_generated"] is False for slot in meta["follow_key_slots"])
    assert current_input["memo"] not in encoded
    assert current_input["memo_action"] not in encoded
    assert '"comment_text":' not in encoded
    assert '"raw_text":' not in encoded


def test_phase3_selector_uses_output_theme_candidates_and_relation_roles_together() -> None:
    current_input = _input(
        memo="どうしたらいいか分からなくて、このままでいいのか迷っている",
        emotion="不安",
        category="人間関係",
        action="相手に返事できなかった",
    )
    frame = build_environment_state_output_frame(
        current_input,
        observation_structure_relation_ids=["unformed_self_insight", "thought_action_discrepancy"],
    )

    meta = build_emlis_ai_human_follow_selection(
        current_input,
        environment_state_output_frame=frame,
        relation_role_ids=["unformed_self_insight", "thought_action_discrepancy"],
    ).as_meta()
    summary = meta["selector_input_summary"]

    assert meta["selection"]["input_type"] == "ambivalence"
    assert summary["uses_environment_state_output_frame"] is True
    assert summary["uses_output_theme_candidates"] is True
    assert summary["uses_relation_role_ids"] is True
    assert "unformed_self_insight" in summary["relation_role_ids"]
    assert "output_theme_candidates" in meta["selection"]["selector_basis"]
    assert "relation_role_ids" in meta["selection"]["selector_basis"]
    assert meta["selection"]["emotion_label_only_selection"] is False


def test_phase3_self_denial_and_anger_keep_special_boundaries_without_personality_claims() -> None:
    self_denial = build_emlis_ai_human_follow_selection(
        _input(memo="自分なんか価値がないと思ってしまう", emotion="悲しみ", strength="strong", action="一日中その言葉が残っていた")
    ).as_meta()
    anger = build_emlis_ai_human_follow_selection(
        _input(memo="不公平な扱いで怒りが出た", emotion="怒り", strength="strong", action="職場で急な対応を求められた", category="仕事")
    ).as_meta()

    assert self_denial["strong_follow_candidate"] is True
    assert self_denial["guard_policy"]["limited_counter_opinion_allowed"] is True
    assert self_denial["guard_policy"]["self_denial_requires_evidence_for_counter_opinion"] is True
    assert FOLLOW_IDENTITY_COUNTER_WITH_EVIDENCE in self_denial["secondary_follow_keys"]
    assert self_denial["personality_claim_allowed"] is False

    assert anger["selection"]["input_type"] == "anger"
    assert anger["primary_follow_key"] == FOLLOW_IMPORTANT_VALUE_RECEIVING
    assert anger["guard_policy"]["target_judgement_agreement_allowed"] is False
    assert anger["guard_policy"]["anger_target_judgement_agreement_allowed"] is False
    assert anger["personality_claim_allowed"] is False


def test_phase3_selector_helpers_return_forward_gate_and_composer_payloads() -> None:
    selection = build_emlis_ai_human_follow_selection(
        _input(memo="相手に迷惑をかけた気がして申し訳ない", emotion="不安", category="人間関係")
    )

    forward_meta = human_follow_selection_forward_meta(selection)
    gate_report = human_follow_selection_gate_report(forward_meta)
    composer_payload = human_follow_selection_composer_payload(forward_meta)

    assert forward_meta["material_id"] == EMLIS_AI_HUMAN_FOLLOW_SELECTOR_MATERIAL_ID
    assert gate_report["human_follow_selector_connected"] is True
    assert gate_report["personality_claim_allowed"] is False
    assert composer_payload["human_follow_selector_material_only"] is True
    assert composer_payload["comment_text_generated"] is False
    assert composer_payload["raw_text_included"] is False


def test_phase3_selector_is_connected_into_state_answer_surface_contract() -> None:
    current_input = _input(
        memo="上司の扱いが理不尽で怒りが出た",
        emotion="怒り",
        strength="strong",
        category="仕事",
        action="急な対応を求められた",
    )

    contract = build_emlis_state_answer_surface_contract(current_input).as_meta()
    follow_layer = contract["human_follow_layer"]

    assert follow_layer["human_follow_selector_connected"] is True
    assert follow_layer["selector_phase"] == EMLIS_AI_HUMAN_FOLLOW_SELECTOR_PHASE
    assert follow_layer["input_type"] == "anger"
    assert follow_layer["primary_follow_key"] == FOLLOW_IMPORTANT_VALUE_RECEIVING
    assert len(follow_layer["secondary_follow_keys"]) == 2
    assert follow_layer["personality_claim_allowed"] is False
    assert follow_layer["human_follow_selector_gate_report"]["target_judgement_agreement_allowed"] is False
    assert contract["completed_reply_generated"] is False
    assert contract["public_response_key_added"] is False



def _phase9_case_input(case_id: str) -> dict[str, object]:
    return current_input_for_two_stage_reception_case(two_stage_reception_case_by_id(case_id))


def test_phase9_daily_unpleasant_A_uses_explicit_reaction_receiving_without_heavy_anger_value_line() -> None:
    current_input = _phase9_case_input("daily_unpleasant_encounter_A")

    meta = build_emlis_ai_human_follow_selection(current_input).as_meta()
    encoded = json.dumps(meta, ensure_ascii=False, sort_keys=True)
    all_follow_keys = [meta["primary_follow_key"], *meta["secondary_follow_keys"], meta["afterglow_follow_key"]]

    assert meta["selection"]["input_type"] == "daily_unpleasant_reception"
    assert meta["selector_input_summary"]["reception_mode_id"] == "daily_unpleasant_reception"
    assert meta["selector_input_summary"]["phase9_daily_unpleasant_follow_allowed"] is True
    assert meta["primary_follow_key"] == FOLLOW_EXPLICIT_REACTION_RECEIVING
    assert FOLLOW_FEAR_OR_LOAD_UNDERSTANDING in meta["secondary_follow_keys"]
    assert FOLLOW_NOT_OVER_EXPLAINING_DAILY_EVENT in meta["secondary_follow_keys"]
    assert FOLLOW_IMPORTANT_VALUE_RECEIVING not in all_follow_keys
    assert meta["selection"]["daily_input_over_anger_structure_prevented"] is True
    assert meta["selection"]["important_value_receiving_overweighted_allowed"] is False
    assert meta["guard_policy"]["daily_input_over_anger_structure_prevented"] is True
    assert meta["guard_policy"]["daily_reception_does_not_require_target_judgement"] is True
    assert meta["guard_policy"]["target_judgement_agreement_allowed"] is False
    assert meta["comment_text_generated"] is False
    assert meta["public_response_key_added"] is False
    assert current_input["memo"] not in encoded
    assert current_input["memo_action"] not in encoded
    assert '"comment_text":' not in encoded
    assert '"raw_text":' not in encoded


def test_phase9_self_confidence_uncertainty_B_is_not_daily_and_keeps_identity_effort_follow() -> None:
    current_input = _phase9_case_input("self_confidence_uncertainty_B")

    meta = build_emlis_ai_human_follow_selection(current_input).as_meta()
    encoded = json.dumps(meta, ensure_ascii=False, sort_keys=True)
    all_follow_keys = [meta["primary_follow_key"], *meta["secondary_follow_keys"], meta["afterglow_follow_key"]]

    assert meta["selection"]["input_type"] == "self_confidence_uncertainty"
    assert meta["selector_input_summary"]["reception_mode_id"] in {"self_denial_support", "uncertainty_support"}
    assert meta["selector_input_summary"]["phase9_daily_unpleasant_follow_allowed"] is False
    assert meta["primary_follow_key"] == FOLLOW_IDENTITY_COUNTER_WITH_EVIDENCE
    assert FOLLOW_IDENTITY_COUNTER_WITH_EVIDENCE in all_follow_keys
    assert FOLLOW_EFFORT_RECEIVING in all_follow_keys
    assert meta["guard_policy"]["self_denial_requires_evidence_for_counter_opinion"] is True
    assert meta["guard_policy"]["limited_counter_opinion_allowed"] is True
    assert meta["selection"]["daily_input_over_anger_structure_prevented"] is False
    assert current_input["memo"] not in encoded
    assert '"comment_text":' not in encoded
    assert '"raw_text":' not in encoded


def test_phase9_reception_section_material_uses_human_follow_primary_for_A() -> None:
    current_input = _phase9_case_input("daily_unpleasant_encounter_A")

    contract = build_emlis_state_answer_surface_contract(current_input).as_meta()
    follow_layer = contract["human_follow_layer"]
    reception_section = contract["reception_section_material"]

    assert follow_layer["input_type"] == "daily_unpleasant_reception"
    assert follow_layer["primary_follow_key"] == FOLLOW_EXPLICIT_REACTION_RECEIVING
    assert reception_section["display_label"] == "Emlisから"
    assert reception_section["primary_reception_key"] == FOLLOW_EXPLICIT_REACTION_RECEIVING
    assert FOLLOW_NOT_OVER_EXPLAINING_DAILY_EVENT in reception_section["secondary_reception_keys"]
    assert reception_section["reception_mode_id"] == "daily_unpleasant_reception"
    assert contract["completed_reply_generated"] is False
    assert contract["public_response_key_added"] is False
