# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step17 broad-input fixtures for EmlisAI B-R1.

These fixtures are A-P0 judgement material. They intentionally describe
structure-level expectations only: profile / coverage / evidence / quality
boundary. They never pin an exact ``comment_text`` sentence.
"""

STEP17_FIXTURE_VERSION = "emlis.step17_broad_input_fixtures.v1"
STEP17_PHASE = "B-R1"
STEP17_STEP = "Step17_broad_input_fixtures"

# Step17 coverage target: daily life, body condition, relationships, study,
# work, long input, history scope, and cross-core contexts.
STEP17_REQUIRED_INPUT_AREAS = (
    "life",
    "body_condition",
    "relationship",
    "study",
    "work",
    "long_meaning_arc",
    "history_scope",
    "cross_core_scope",
)

STEP17_REQUIRED_COVERAGE_GROUPS = (
    "energy_fatigue",
    "anxiety",
    "anger_hurt",
    "positive_recovery",
    "relationship",
    "limit_escape",
    "value_wish",
    "long_meaning_arc",
)

STEP17_FORBIDDEN_SURFACES = (
    "一般的に",
    "普通は",
    "多くの人",
    "心理学的には",
    "医学的には",
    "診断",
    "治療",
    "病気",
    "本当の願い",
    "本心",
    "性格",
    "人格",
    "あなたは",
    "あなたの本質",
    "一緒に見ます",
    "急いで片づけず",
)

STEP17_BROAD_DAILY_INPUT_CASES = [
    {
        "case_id": "step17_body_fatigue_focus",
        "input_area": "body_condition",
        "emotion": "自己理解",
        "category": "体調",
        "memo": """昨日から疲れが抜けない。
朝の予定が詰まっていて、昼には集中が切れていた。
少し休みたい気持ちがある。""",
        "expected_profile": "energy_fatigue",
        "expected_coverage_scope": "partial_observation",
        "required_coverage_groups": ["energy_fatigue", "limit_escape"],
        "min_used_current_evidence": 2,
    },
    {
        "case_id": "step17_study_anticipation_focus",
        "input_area": "study",
        "emotion": "不安",
        "category": "学習",
        "memo": """明日の発表のことを考えると手が止まる。
失敗しそうで不安が強い。
ちゃんとできない気がして進めない。""",
        "expected_profile": "self_understanding_loop",
        "expected_coverage_scope": "partial_observation",
        "required_coverage_groups": ["anxiety", "long_meaning_arc"],
        "min_used_current_evidence": 2,
    },
    {
        "case_id": "step17_work_value_wish_focus",
        "input_area": "work",
        "emotion": "自己理解",
        "category": "仕事",
        "memo": """資料を直したいのに、頭が回らない。
でも自分の時間を大事にしたい。""",
        "expected_profile": "value_wish",
        "expected_coverage_scope": "partial_observation",
        "required_coverage_groups": ["value_wish"],
        "min_used_current_evidence": 2,
    },
    {
        "case_id": "step17_relationship_burden_focus",
        "input_area": "relationship",
        "emotion": "不安",
        "category": "人間関係",
        "memo": """本当は相談したい。
でも相手の時間を奪う気がして言い出せない。
助けを借りたいのに、困らせそうで怖い。
一人で考え続けるのはつらい。""",
        "expected_profile": "relationship_approach_avoidance",
        "expected_coverage_scope": "partial_observation",
        "required_coverage_groups": ["relationship", "anxiety", "value_wish"],
        "min_used_current_evidence": 3,
    },
    {
        "case_id": "step17_life_positive_recovery_focus",
        "input_area": "life",
        "emotion": "喜び",
        "category": "生活",
        "memo": """今日は洗い物を少し終えた。
台所が整って、気持ちが落ち着いた。
自分でも少し進められてほっとした。""",
        "expected_profile": "positive_progress",
        "expected_coverage_scope": "partial_observation",
        "required_coverage_groups": ["positive_recovery"],
        "min_used_current_evidence": 2,
    },
    {
        "case_id": "step17_work_anger_hurt_focus",
        "input_area": "work",
        "emotion": "怒り",
        "category": "仕事",
        "memo": """相手の返し方が雑でむっとした。
丁寧に伝えようとしていたのに、軽く扱われた感じがしてしんどい。
もう説明する気力がなくなっている。""",
        "expected_profile": "anger_hurt_boundary",
        "expected_coverage_scope": "partial_observation",
        "required_coverage_groups": ["anger_hurt", "relationship"],
        "min_used_current_evidence": 2,
    },
]

STEP17_LONG_MEANING_ARC_CASE = {
    "case_id": "step17_long_meaning_arc_work_repair",
    "input_area": "long_meaning_arc",
    "emotion": "自己理解",
    "category": "仕事",
    "memo": """ここ数日、仕事の疲れが抜けない。
資料を直したいのに、頭が回らなくて手が止まる。
でも自分の時間を大事にしたい気持ちはある。
さっきお茶を飲んだら少し落ち着いた。
今日はもう休みたい。""",
    "expected_profile": "long_meaning_arc",
    "expected_coverage_scope": "partial_observation",
    "required_coverage_groups": ["long_meaning_arc", "energy_fatigue", "value_wish", "limit_escape"],
    "min_used_current_evidence": 3,
    "min_body_lines": 3,
    "min_sentence_plans": 3,
}

STEP17_CONTEXT_SCOPE_CASES = [
    {
        "case_id": "step17_history_scope_current_input_grounded",
        "input_area": "history_scope",
        "emotion": "自己理解",
        "category": "仕事",
        "memo": """今日は仕事の疲れが溜まっていた。
予定を考えると頭が回らない。
それでも自分のペースを大事にしたい。""",
        "expected_profile": "energy_fatigue",
        "expected_coverage_scope": "partial_observation",
        "required_coverage_groups": ["value_wish", "energy_fatigue"],
        "min_used_current_evidence": 2,
        "external_context_kind": "history",
        "external_context_spans": [
            {
                "span_id": "history-step17-previous-piece",
                "source_field": "history",
                "detected_type": "history_context",
                "raw_text": "前回の履歴では、夜に一人で抱え込む話が中心だった。",
                "must_not_surface_terms": ["前回の履歴", "抱え込む話"],
            }
        ],
    },
    {
        "case_id": "step17_cross_core_scope_current_input_grounded",
        "input_area": "cross_core_scope",
        "emotion": "自己理解",
        "category": "生活",
        "memo": """週末に部屋を整えたい。
でも疲れが溜まっていて、予定を考えると頭が回らない。
それでも自分のペースを守りたい。""",
        "expected_profile": "energy_fatigue",
        "expected_coverage_scope": "partial_observation",
        "required_coverage_groups": ["value_wish", "energy_fatigue"],
        "min_used_current_evidence": 1,
        "external_context_kind": "cross_core",
        "external_context_spans": [
            {
                "span_id": "cross-core-step17-piece-anchor",
                "source_field": "cross_core_context",
                "detected_type": "piece_anchor",
                "raw_text": "Piece 側には『公開する問いを整えたい』というアンカーがある。",
                "must_not_surface_terms": ["公開する問い", "Piece 側"],
            },
            {
                "span_id": "cross-core-step17-analysis-anchor",
                "source_field": "cross_core_context",
                "detected_type": "analysis_anchor",
                "raw_text": "Analysis 側には『責任感が強いタイプ』という未使用の観測がある。",
                "must_not_surface_terms": ["責任感が強いタイプ", "Analysis 側"],
            },
        ],
    },
]

STEP17_SURFACE_VARIATION_SERIES = [
    {
        "case_id": "step17_surface_variation_energy_fatigue_a",
        "input_area": "body_condition",
        "emotion": "自己理解",
        "category": "体調",
        "memo": """昨日から疲れが抜けない。
朝の予定が詰まっていて、昼には集中が切れていた。
少し休みたい気持ちがある。""",
        "expected_profile": "energy_fatigue",
    },
    {
        "case_id": "step17_surface_variation_energy_fatigue_b",
        "input_area": "body_condition",
        "emotion": "自己理解",
        "category": "体調",
        "memo": """寝ても疲れが残っている。
午後には頭が回らなくて、やることが多すぎる感じがあった。
いったん深呼吸して少し休めた。""",
        "expected_profile": "energy_fatigue",
    },
]

STEP17_GENERAL_KNOWLEDGE_COMPLETION_BAD_OUTPUTS = [
    {
        "case_id": "step17_reject_general_psychology_completion",
        "comment_text": "Mashさん、Emlisです。\n一般的に疲れている時は判断力が落ちるので、あなたは休むべきです。",
        "expected_reasons_any": ["general_knowledge_completion", "phase8_deep_overclaim", "phase14_general_knowledge_completion"],
    },
    {
        "case_id": "step17_reject_personality_type_completion",
        "comment_text": "Mashさん、Emlisです。\nあなたは責任感が強いタイプなので、全部抱え込みやすい性格です。",
        "expected_reasons_any": ["personality_label", "phase8_deep_overclaim", "phase14_personality_label"],
    },
]

__all__ = [
    "STEP17_BROAD_DAILY_INPUT_CASES",
    "STEP17_CONTEXT_SCOPE_CASES",
    "STEP17_FIXTURE_VERSION",
    "STEP17_FORBIDDEN_SURFACES",
    "STEP17_GENERAL_KNOWLEDGE_COMPLETION_BAD_OUTPUTS",
    "STEP17_LONG_MEANING_ARC_CASE",
    "STEP17_PHASE",
    "STEP17_REQUIRED_COVERAGE_GROUPS",
    "STEP17_REQUIRED_INPUT_AREAS",
    "STEP17_STEP",
    "STEP17_SURFACE_VARIATION_SERIES",
]
