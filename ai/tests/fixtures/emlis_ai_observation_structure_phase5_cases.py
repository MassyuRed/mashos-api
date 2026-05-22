# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 5 fixtures for the Emlis observation structure dictionary.

These cases are blind-QA material for the structure dictionary connection.  They
pin relation / boundary expectations only and deliberately do not pin completed
``comment_text`` strings.  Natural language quality remains a human blind-QA
rubric dimension, separated from machine-checkable contract metrics.
"""

from typing import Any

PHASE5_OBSERVATION_STRUCTURE_FIXTURE_VERSION = "emlis.observation_structure.phase5_fixtures.v1"
PHASE5_OBSERVATION_STRUCTURE_PHASE = "Phase5_Test_Fixture_Blind_QA"
PHASE5_BLIND_QA_RUBRIC_VERSION = "emlis.observation_structure.phase5_blind_qa_rubric.v1"

PHASE5_REQUIRED_CASE_IDS = (
    "phase5_state_text_gap_sadness_strong_daijoubu",
    "phase5_emotion_nesting_anger_sadness_tired",
    "phase5_low_information_work_muri_anxiety_strong",
    "phase5_category_overlap_work_relationship_boss_muri",
    "phase5_thought_action_discrepancy_smiled_but_disliked",
    "phase5_self_insight_values_people_pleasing",
    "phase5_light_calm_life_sleepy",
    "phase5_unexpressed_output_stop_could_not_say",
    "phase5_self_shape_alignment_aligned_to_context",
    "phase5_action_conversion_history_gaman",
    "phase5_action_conversion_history_with_thought_action_gap",
    "phase5_conversion_history_closure_gaman_unfinished",
    "phase5_unformed_self_insight_wakaranai",
)

PHASE5_MACHINE_QA_DIMENSIONS = (
    "input_bundle_grounding",
    "relation_selection",
    "low_information_boundary",
    "category_not_cause_boundary",
    "thought_action_boundary",
    "self_insight_mode",
    "no_raw_text_meta",
    "public_contract_preservation",
)

PHASE5_HUMAN_BLIND_QA_DIMENSIONS = (
    "read_feeling",
    "input_arrangement",
    "state_verbalization",
    "user_agency_distance",
    "non_template_naturalness",
    "overclaim_absence",
)

PHASE5_BLIND_QA_RUBRIC: dict[str, Any] = {
    "version": PHASE5_BLIND_QA_RUBRIC_VERSION,
    "target_phase": PHASE5_OBSERVATION_STRUCTURE_PHASE,
    "exact_comment_text_locked": False,
    "dictionary_returns_completed_reply": False,
    "machine_metrics_separated_from_human_read_feeling": True,
    "machine_dimensions": list(PHASE5_MACHINE_QA_DIMENSIONS),
    "human_blind_qa_dimensions": list(PHASE5_HUMAN_BLIND_QA_DIMENSIONS),
    "must_not_include_raw_input_or_comment_text": True,
    "public_contract_preservation_required": True,
    "release_claim_allowed": False,
}

PHASE5_OBSERVATION_STRUCTURE_BLIND_QA_CASES: list[dict[str, Any]] = [
    {
        "case_id": "phase5_state_text_gap_sadness_strong_daijoubu",
        "label": "悲しみ/強 + 大丈夫",
        "current_input": {
            "id": "phase5-001",
            "created_at": "2026-05-21T00:00:00Z",
            "memo": "大丈夫",
            "memo_action": "",
            "emotion_details": [{"type": "悲しみ", "strength": "strong"}],
            "category": ["仕事"],
        },
        "expected_entry_ids": ["gap_word_daijoubu", "user_agency_prompt"],
        "expected_relation_ids": ["state_text_gap", "low_information_weight", "user_agency_prompt"],
        "forbidden_relation_ids": ["category_overlap", "thought_action_discrepancy", "self_insight_discovery"],
        "expected_low_information_candidate": True,
        "expected_material_fields": ["memo", "emotion_details", "category"],
    },
    {
        "case_id": "phase5_emotion_nesting_anger_sadness_tired",
        "label": "怒り/強 + 悲しみ/中 + 疲れた",
        "current_input": {
            "id": "phase5-002",
            "created_at": "2026-05-21T00:01:00Z",
            "memo": "もう疲れた",
            "memo_action": "",
            "emotion_details": [
                {"type": "怒り", "strength": "strong"},
                {"type": "悲しみ", "strength": "medium"},
            ],
            "category": ["人間関係"],
        },
        "expected_entry_ids": ["word_tired", "emotion_nesting", "user_agency_prompt"],
        "expected_relation_ids": ["emotion_nesting", "low_information_weight", "user_agency_prompt"],
        "forbidden_relation_ids": ["category_overlap", "thought_action_discrepancy", "self_insight_discovery"],
        "expected_low_information_candidate": True,
        "expected_material_fields": ["memo", "emotion_details", "category"],
    },
    {
        "case_id": "phase5_low_information_work_muri_anxiety_strong",
        "label": "仕事 + 無理 + 不安/強",
        "current_input": {
            "id": "phase5-003",
            "created_at": "2026-05-21T00:02:00Z",
            "memo": "無理",
            "memo_action": "",
            "emotion_details": [{"type": "不安", "strength": "strong"}],
            "category": ["仕事"],
        },
        "expected_entry_ids": ["word_muri", "user_agency_prompt"],
        "expected_relation_ids": ["low_information_weight", "user_agency_prompt"],
        "forbidden_relation_ids": ["category_overlap", "thought_action_discrepancy", "self_insight_discovery"],
        "expected_low_information_candidate": True,
        "expected_material_fields": ["memo", "emotion_details", "category"],
    },
    {
        "case_id": "phase5_category_overlap_work_relationship_boss_muri",
        "label": "仕事/人間関係 + 上司 + 無理",
        "current_input": {
            "id": "phase5-004",
            "created_at": "2026-05-21T00:03:00Z",
            "memo": "もう無理",
            "memo_action": "上司に急に追加の仕事を頼まれた",
            "emotion_details": [{"type": "不安", "strength": "strong"}],
            "category": ["仕事", "人間関係"],
        },
        "expected_entry_ids": ["word_muri", "category_parallel_overlap"],
        "expected_relation_ids": ["category_parallel", "category_overlap"],
        "forbidden_relation_ids": ["low_information_weight", "user_agency_prompt", "thought_action_discrepancy"],
        "expected_low_information_candidate": False,
        "expected_material_fields": ["memo", "memo_action", "category"],
    },
    {
        "case_id": "phase5_thought_action_discrepancy_smiled_but_disliked",
        "label": "笑って対応した + 本当は嫌だった + 怒り/強",
        "current_input": {
            "id": "phase5-005",
            "created_at": "2026-05-21T00:04:00Z",
            "memo": "本当は嫌だった",
            "memo_action": "笑って対応した",
            "emotion_details": [{"type": "怒り", "strength": "strong"}],
            "category": ["人間関係"],
        },
        "expected_entry_ids": ["thought_action_discrepancy"],
        "expected_relation_ids": ["thought_action_discrepancy"],
        "forbidden_relation_ids": ["category_overlap", "low_information_weight", "user_agency_prompt", "self_insight_discovery"],
        "expected_low_information_candidate": False,
        "expected_material_fields": ["memo", "memo_action"],
    },
    {
        "case_id": "phase5_self_insight_values_people_pleasing",
        "label": "自己理解 + 価値観 + 人に合わせすぎていた",
        "current_input": {
            "id": "phase5-006",
            "created_at": "2026-05-21T00:05:00Z",
            "memo": "私は人に合わせすぎてたのかもしれない",
            "memo_action": "",
            "emotion_details": [{"type": "自己理解", "strength": "medium"}],
            "category": ["価値観"],
        },
        "expected_entry_ids": ["self_insight"],
        "expected_relation_ids": ["self_insight_discovery"],
        "forbidden_relation_ids": ["category_overlap", "thought_action_discrepancy", "low_information_weight", "user_agency_prompt"],
        "expected_low_information_candidate": False,
        "expected_material_fields": ["emotion_details"],
    },
    {
        "case_id": "phase5_light_calm_life_sleepy",
        "label": "生活 + 平穏/weak + 眠い",
        "current_input": {
            "id": "phase5-007",
            "created_at": "2026-05-21T00:06:00Z",
            "memo": "眠い",
            "memo_action": "",
            "emotion_details": [{"type": "平穏", "strength": "weak"}],
            "category": ["生活"],
        },
        "expected_entry_ids": [],
        "expected_relation_ids": [],
        "forbidden_relation_ids": [
            "state_text_gap",
            "emotion_nesting",
            "category_overlap",
            "thought_action_discrepancy",
            "self_insight_discovery",
            "low_information_weight",
            "user_agency_prompt",
        ],
        "expected_low_information_candidate": False,
        "expected_material_fields": [],
    },
    {
        "case_id": "phase5_unexpressed_output_stop_could_not_say",
        "label": "言えなかった単独 / 未出力の停止",
        "current_input": {
            "id": "phase5-action-001",
            "created_at": "2026-05-22T00:00:00Z",
            "memo": "言えなかった",
            "memo_action": "",
            "emotion_details": [{"type": "悲しみ", "strength": "medium"}],
            "category": ["人間関係"],
        },
        "expected_entry_ids": ["word_could_not_say"],
        "expected_relation_ids": ["unexpressed_output_stop"],
        "forbidden_relation_ids": [
            "thought_action_discrepancy",
            "low_information_weight",
            "user_agency_prompt",
        ],
        "expected_low_information_candidate": False,
        "expected_material_fields": ["memo"],
    },
    {
        "case_id": "phase5_self_shape_alignment_aligned_to_context",
        "label": "合わせた単独 / 自己形状の一時変換",
        "current_input": {
            "id": "phase5-action-002",
            "created_at": "2026-05-22T00:01:00Z",
            "memo": "合わせた",
            "memo_action": "",
            "emotion_details": [{"type": "平穏", "strength": "weak"}],
            "category": ["人間関係"],
        },
        "expected_entry_ids": ["word_aligned_to_context"],
        "expected_relation_ids": ["self_shape_alignment"],
        "forbidden_relation_ids": [
            "thought_action_discrepancy",
            "priority_pressure",
            "low_information_weight",
            "user_agency_prompt",
        ],
        "expected_low_information_candidate": False,
        "expected_material_fields": ["memo"],
    },
    {
        "case_id": "phase5_action_conversion_history_gaman",
        "label": "我慢した単独 / 行動変換履歴",
        "current_input": {
            "id": "phase5-action-003",
            "created_at": "2026-05-22T00:02:00Z",
            "memo": "我慢した",
            "memo_action": "",
            "emotion_details": [{"type": "悲しみ", "strength": "medium"}],
            "category": ["人間関係"],
        },
        "expected_entry_ids": ["word_gaman"],
        "expected_relation_ids": ["action_conversion_history"],
        "forbidden_relation_ids": [
            "thought_action_discrepancy",
            "conversion_history_closure",
            "load_accumulation",
            "low_information_weight",
            "user_agency_prompt",
        ],
        "expected_low_information_candidate": False,
        "expected_material_fields": ["memo"],
    },
    {
        "case_id": "phase5_action_conversion_history_with_thought_action_gap",
        "label": "我慢した + memo/memo_action差分",
        "current_input": {
            "id": "phase5-action-004",
            "created_at": "2026-05-22T00:03:00Z",
            "memo": "本当は嫌だったけど我慢した",
            "memo_action": "言わずに対応した",
            "emotion_details": [{"type": "怒り", "strength": "strong"}],
            "category": ["人間関係"],
        },
        "expected_entry_ids": ["word_gaman"],
        "expected_relation_ids": ["action_conversion_history", "thought_action_discrepancy"],
        "forbidden_relation_ids": [
            "conversion_history_closure",
            "load_accumulation",
            "low_information_weight",
            "user_agency_prompt",
        ],
        "expected_low_information_candidate": False,
        "expected_material_fields": ["memo", "memo_action"],
    },
    {
        "case_id": "phase5_conversion_history_closure_gaman_unfinished",
        "label": "我慢した + 未完了の閉じ方根拠",
        "current_input": {
            "id": "phase5-action-005",
            "created_at": "2026-05-22T00:04:00Z",
            "memo": "我慢したけど、まだ引っかかっている",
            "memo_action": "言わずに対応した",
            "emotion_details": [{"type": "悲しみ", "strength": "strong"}],
            "category": ["人間関係"],
        },
        "expected_entry_ids": ["word_gaman"],
        "expected_relation_ids": [
            "action_conversion_history",
            "conversion_history_closure",
            "thought_action_discrepancy",
        ],
        "forbidden_relation_ids": [
            "load_accumulation",
            "low_information_weight",
            "user_agency_prompt",
        ],
        "expected_low_information_candidate": False,
        "expected_material_fields": ["memo", "memo_action"],
    },
    {
        "case_id": "phase5_unformed_self_insight_wakaranai",
        "label": "わからない / 未形化自己理解",
        "current_input": {
            "id": "phase5-action-006",
            "created_at": "2026-05-22T00:05:00Z",
            "memo": "わからない",
            "memo_action": "",
            "emotion_details": [{"type": "不安", "strength": "medium"}],
            "category": ["自分"],
        },
        "expected_entry_ids": ["word_wakaranai"],
        "expected_relation_ids": ["unformed_self_insight"],
        "forbidden_relation_ids": [
            "low_information_weight",
            "user_agency_prompt",
            "thought_action_discrepancy",
            "category_overlap",
            "pressure_gap",
            "action_blocked",
            "priority_pressure",
            "load_accumulation",
            "conversion_history_closure",
        ],
        "expected_low_information_candidate": False,
        "expected_material_fields": ["memo"],
    },
]

PHASE5_CATEGORY_BOUNDARY_CASES: list[dict[str, Any]] = [
    {
        "case_id": "phase5_category_parallel_work_health_without_bridge",
        "label": "仕事/健康 + 仕事のことで無理 / health bridgeなし",
        "current_input": {
            "id": "phase5-boundary-001",
            "created_at": "2026-05-21T00:07:00Z",
            "memo": "仕事のことで無理",
            "memo_action": "",
            "emotion_details": [{"type": "不安", "strength": "strong"}],
            "category": ["仕事", "健康"],
        },
        "expected_relation_ids": ["category_parallel"],
        "forbidden_relation_ids": ["category_overlap"],
        "expected_low_information_candidate": False,
    },
    {
        "case_id": "phase5_category_overlap_work_health_with_bridge",
        "label": "仕事/健康 + 残業が続いて眠れていない",
        "current_input": {
            "id": "phase5-boundary-002",
            "created_at": "2026-05-21T00:08:00Z",
            "memo": "体が持たない気がする",
            "memo_action": "残業が続いて眠れていない",
            "emotion_details": [{"type": "不安", "strength": "strong"}],
            "category": ["仕事", "健康"],
        },
        "expected_relation_ids": ["category_parallel", "category_overlap"],
        "forbidden_relation_ids": ["low_information_weight", "user_agency_prompt"],
        "expected_low_information_candidate": False,
    },
]

__all__ = [
    "PHASE5_BLIND_QA_RUBRIC",
    "PHASE5_BLIND_QA_RUBRIC_VERSION",
    "PHASE5_CATEGORY_BOUNDARY_CASES",
    "PHASE5_HUMAN_BLIND_QA_DIMENSIONS",
    "PHASE5_MACHINE_QA_DIMENSIONS",
    "PHASE5_OBSERVATION_STRUCTURE_BLIND_QA_CASES",
    "PHASE5_OBSERVATION_STRUCTURE_FIXTURE_VERSION",
    "PHASE5_OBSERVATION_STRUCTURE_PHASE",
    "PHASE5_REQUIRED_CASE_IDS",
]
