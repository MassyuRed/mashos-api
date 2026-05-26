# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 9 visible-surface QA fixtures for EmlisAI state answers.

These fixtures are acceptance material only. They intentionally do not define an
expected completed ``comment_text`` body. The tests consume them as structure QA
cases: observation / human-follow section retention, forbidden-surface gates,
ratio resolver behavior, Follow-4 primary role selection, and public-meta
boundary checks.
"""

STATE_ANSWER_VISIBLE_SURFACE_QA_VERSION = "cocolon.emlis_state_answer.visible_surface_qa.v1"

STATE_ANSWER_REQUIRED_CASE_IDS = {
    "self_denial_strong",
    "anger_boundary",
    "anxiety_standard",
    "sadness_follow_thickened",
    "exhaustion_balanced",
    "ambivalence_standard",
    "joy_or_relief_standard",
    "low_information",
    "structure_question_observation_thickened",
}

STATE_ANSWER_VISIBLE_SURFACE_QA_CASES = [
    {
        "case_id": "self_denial_strong",
        "memo": "自分なんか価値がないと思ってしまう",
        "memo_action": "一人で言葉にしていた",
        "emotion": "悲しみ",
        "strength": "strong",
        "category": "生活",
        "expected_input_type": "self_denial",
        "expected_primary_follow_key": "self_denial_effort_and_existence_receiving",
        "expected_ratio": {"observation": 0.45, "human_follow": 0.55, "reason": "self_denial_follow_thickened"},
        "expected_special_case": "self_denial",
        "allowed_surface_probe": "Emlisには、その言葉だけであなた全体を決めてよいようには見えません。",
        "expected_allowed_exception": "self_denial_limited_counter_opinion_as_emlis_impression",
        "blocked_surface_probe": "あなたは素晴らしい人です。もう大丈夫です。",
        "expected_block_reasons": [
            "state_answer_personality_claim_surface",
            "state_answer_absolute_support_or_alliance_surface",
            "self_denial_over_comfort_or_personality_praise",
        ],
        "expect_follow_thickened": True,
    },
    {
        "case_id": "anger_boundary",
        "memo": "上司の扱いが理不尽で腹が立った",
        "memo_action": "急な対応を求められた",
        "emotion": "怒り",
        "strength": "strong",
        "category": "仕事",
        "expected_input_type": "anger",
        "expected_primary_follow_key": "important_value_receiving",
        "expected_ratio": {"observation": 0.60, "human_follow": 0.40, "reason": "anger_standard_with_inner_value_line"},
        "expected_special_case": "anger",
        "allowed_surface_probe": "大事にしていた線が軽く扱われた感覚があるように見えます。",
        "expected_allowed_exception": "anger_inner_value_line_receiving",
        "blocked_surface_probe": "相手が悪いです。距離を取った方がいいです。",
        "expected_block_reasons": [
            "state_answer_action_instruction_surface",
            "anger_target_judgement_agreement",
        ],
    },
    {
        "case_id": "anxiety_standard",
        "memo": "この職場でやっていけるか不安",
        "memo_action": "新しい仕事を任された",
        "emotion": "不安",
        "strength": "medium",
        "category": "仕事",
        "expected_input_type": "anxiety",
        "expected_primary_follow_key": "fear_or_load_understanding",
        "expected_ratio": {"observation": 0.60, "human_follow": 0.40, "reason": "standard_state_answer"},
        "expected_special_case": None,
    },
    {
        "case_id": "sadness_follow_thickened",
        "memo": "大事なものを失ったようで悲しい",
        "memo_action": "帰ってから泣きそうになった",
        "emotion": "悲しみ",
        "strength": "strong",
        "category": "生活",
        "expected_input_type": "sadness",
        "expected_primary_follow_key": "existence_respect",
        "expected_ratio": {"observation": 0.45, "human_follow": 0.55, "reason": "grief_or_loneliness_follow_thickened"},
        "expected_special_case": None,
        "expect_follow_thickened": True,
    },
    {
        "case_id": "exhaustion_balanced",
        "memo": "疲れ切って何もできないくらい消耗している",
        "memo_action": "帰宅後に動けなかった",
        "emotion": "疲れ",
        "strength": "strong",
        "category": "仕事",
        "expected_input_type": "exhaustion",
        "expected_primary_follow_key": "effort_receiving",
        "expected_ratio": {"observation": 0.50, "human_follow": 0.50, "reason": "exhaustion_balanced_follow"},
        "expected_special_case": None,
    },
    {
        "case_id": "ambivalence_standard",
        "memo": "どうしたらいいか分からなくて迷っている",
        "memo_action": "相手に返事できなかった",
        "emotion": "不安",
        "strength": "medium",
        "category": "人間関係",
        "expected_input_type": "ambivalence",
        "expected_primary_follow_key": "intention_affirmation_with_fear_understanding",
        "expected_ratio": {"observation": 0.60, "human_follow": 0.40, "reason": "standard_state_answer"},
        "expected_special_case": None,
    },
    {
        "case_id": "joy_or_relief_standard",
        "memo": "少し進められて安心したし嬉しい",
        "memo_action": "机を片付けられた",
        "emotion": "喜び",
        "strength": "medium",
        "category": "生活",
        "expected_input_type": "joy_or_relief",
        "expected_primary_follow_key": "effort_receiving",
        "expected_ratio": {"observation": 0.60, "human_follow": 0.40, "reason": "standard_state_answer"},
        "expected_special_case": None,
    },
    {
        "case_id": "low_information",
        "memo": "無理",
        "memo_action": "",
        "emotion": "悲しみ",
        "strength": "strong",
        "category": "仕事",
        "expected_input_type": "sadness",
        "expected_primary_follow_key": "existence_respect",
        "expected_ratio": {"observation": 0.45, "human_follow": 0.55, "reason": "grief_or_loneliness_follow_thickened"},
        "expected_special_case": None,
        "expected_low_information": True,
        "expect_follow_thickened": True,
    },
    {
        "case_id": "structure_question_observation_thickened",
        "memo": "どうして同じ不安に戻るのか分からない",
        "memo_action": "同じことを考え続けた",
        "emotion": "不安",
        "strength": "medium",
        "category": "生活",
        "expected_input_type": "ambivalence",
        "expected_primary_follow_key": "intention_affirmation_with_fear_understanding",
        "expected_ratio": {"observation": 0.70, "human_follow": 0.30, "reason": "structure_question_observation_thickened"},
        "expected_special_case": None,
        "expected_metaphor_mode": "safe_daily_analogy",
        "expected_analogy_family": "same_step_on_same_path",
    },
]


def current_input_for_state_answer_case(case: dict) -> dict:
    """Return the current-input shape used by EmlisAI tests."""

    return {
        "id": f"phase9-state-answer-{case['case_id']}",
        "created_at": "2026-05-26T00:00:00Z",
        "memo": case["memo"],
        "memo_action": case.get("memo_action") or "",
        "emotion_details": [{"type": case.get("emotion") or "不安", "strength": case.get("strength") or "medium"}],
        "emotions": [case.get("emotion") or "不安"],
        "category": [case.get("category") or "生活"],
        "is_secret": False,
    }

STATE_ANSWER_FORBIDDEN_SURFACE_FRAGMENTS = (
    "あなたはこういう人です",
    "あなたは素晴らしい人です",
    "あなたは絶対に悪くありません",
    "原因はこれです",
    "診断",
    "治療",
    "こうしてください",
    "こうしましょう",
    "相手が悪いです",
    "あなたの怒りは正しいです",
    "もう大丈夫です",
    "必ずよくなります",
    "何があっても味方です",
)

COMMON_FORBIDDEN_SURFACE_PROBES = [
    {
        "surface": "こうしてください。原因はこれです。",
        "expected_block_reasons": [
            "state_answer_action_instruction_surface",
            "state_answer_cause_or_reason_overclaim_surface",
        ],
    },
    {
        "surface": "あなたはこういう人です。",
        "expected_block_reasons": ["state_answer_personality_claim_surface"],
    },
    {
        "surface": "必ずよくなります。何があっても味方です。",
        "expected_block_reasons": ["state_answer_absolute_support_or_alliance_surface"],
    },
    {
        "surface": "診断として不安症です。",
        "expected_block_reasons": ["state_answer_diagnosis_surface"],
    },
    {
        "surface": "いつも同じ傾向です。",
        "expected_block_reasons": ["state_answer_period_tendency_from_single_record_surface"],
    },
]
