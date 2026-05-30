# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 0/1 fixtures for EmlisAI two-stage reception.

This module is acceptance material for the design fixed on 2026-05-26.
It intentionally stops at fixture definition.  It does not call production
runtime code, does not add public response keys, and does not pin exact
``comment_text`` bodies.  Later implementation phases should consume these
cases as structure-level QA material: reception mode, ratio profile, section
shape, low-information boundary, forbidden surface, and public-contract
boundary.
"""

TWO_STAGE_RECEPTION_FIXTURE_VERSION = "cocolon.emlis_two_stage_reception.fixtures.v1"
TWO_STAGE_RECEPTION_DESIGN_SOURCE = (
    "Cocolon_EmlisAI_二段受け取り構造_DailyReception_受け取り補助辞書_"
    "詳細設計書_実装順_華恋用_2026-05-26"
)

TWO_STAGE_LABELS = {
    "observation": "見えたこと",
    "reception": "Emlisから",
}

TWO_STAGE_LABEL_MARKERS = {
    "observation": "見えたこと：",
    "reception": "Emlisから：",
}

TWO_STAGE_COMMENT_TEXT_SHAPE = (
    "見えたこと：\n{observation_section_text}\n\n"
    "Emlisから：\n{reception_section_text}"
)

PHASE0_DESIGN_LOCK = {
    "phase_id": "Phase 0: 設計固定",
    "design_source": TWO_STAGE_RECEPTION_DESIGN_SOURCE,
    "two_stage_labels": TWO_STAGE_LABELS,
    "comment_text_shape": TWO_STAGE_COMMENT_TEXT_SHAPE,
    "public_contract": {
        "public_response_key_added": False,
        "rn_visible_contract_changed": False,
        "observation_status_public_enum_extended": False,
        "comment_text_is_only_visible_body": True,
        "rn_display_title_changed": False,
        "rn_display_condition_changed": False,
    },
    "fixed_boundaries": {
        "visible_body_public_key": "input_feedback.comment_text",
        "visible_status_contract": "input_feedback.emlis_ai.observation_status == passed",
        "observation_status_new_public_enum_allowed": False,
        "observation_text_public_key_allowed": False,
        "reception_text_public_key_allowed": False,
        "general_dictionary_required": False,
        "completed_reply_template_allowed_in_fixture": False,
        "runtime_example_specific_branch_allowed": False,
    },
    "initial_implementation_scope": (
        "Phase 0: 設計固定",
        "Phase 1: fixture追加",
    ),
    "deferred_implementation_phases": (
        "Shared Evidence Builder実装",
        "受け取り補助辞書の骨格実装",
        "Reception Mode Resolver実装",
        "Observation Eligibility Router接続",
        "Ratio Policy更新",
        "State Answer Surface Contract更新",
        "Composer Role Plan更新",
        "Human Follow / Reception Section更新",
        "Cross Gate実装",
        "Public Feedback Meta / Submit接続確認",
        "RN契約回帰",
        "表示品質QA",
        "速度回帰",
        "前提資料更新",
    ),
}

TWO_STAGE_RECEPTION_EVALUATION_AXES = (
    "reception_mode",
    "ratio_profile",
    "low_information_boundary",
    "section_shape",
    "forbidden_surface",
    "public_contract",
)

COMMON_SECTION_SHAPE_EXPECTATION = {
    "two_stage_labels_required": True,
    "observation_label": TWO_STAGE_LABELS["observation"],
    "reception_label": TWO_STAGE_LABELS["reception"],
    "observation_section_must_precede_reception_section": True,
    "observation_section_required": True,
    "reception_section_required": True,
    "observation_section_must_not_include_human_follow": True,
    "reception_section_must_not_include_new_observation_claim": True,
    "public_response_key_added": False,
    "rn_visible_contract_changed": False,
    "exact_text_match_required": False,
}

COMMON_FORBIDDEN_SURFACE_FRAGMENTS = (
    "診断",
    "治療",
    "病気",
    "性格",
    "人格",
    "原因は",
    "こうしてください",
    "こうしましょう",
    "必ず",
    "絶対",
    "もう大丈夫",
    "何があっても味方",
)

TWO_STAGE_RECEPTION_REQUIRED_CASE_IDS = {
    "daily_unpleasant_encounter_A",
    "self_confidence_uncertainty_B",
    "positive_change_after_work_streaming",
    "self_blame_to_gentle_self_observation",
    "independence_life_health_money_pace",
}

TWO_STAGE_RECEPTION_CASES = [
    {
        "case_id": "daily_unpleasant_encounter_A",
        "source_label": "A",
        "source_issue": "日常の不快イベント / daily_unpleasant_reception",
        "current_input": {
            "id": "two-stage-reception-daily-unpleasant-A",
            "created_at": "2026-05-26T00:00:00Z",
            "memo": "この世で1番気持ち悪い瞬間に出くわしてしまいイライラが止まらなかった。＆恐怖",
            "memo_action": "立ちションのおじさんとすれ違ってしまった",
            "emotion_details": [{"type": "怒り", "strength": "medium"}],
            "emotions": ["怒り"],
            "category": ["生活"],
            "is_secret": False,
        },
        "expected_reception_mode": "daily_unpleasant_reception",
        "expected_reception_mode_any": ("daily_unpleasant_reception",),
        "expected_ratio_contract": {
            "expected_ratio_reason": "daily_unpleasant_reception_light",
            "range_key": "daily_reception",
            "observation_min": 0.10,
            "observation_max": 0.30,
            "observation_units": 1,
            "human_follow_units_min": 1,
            "observation_zero_allowed": False,
            "human_follow_zero_allowed": False,
        },
        "expected_low_information_boundary": {
            "low_information_question_required": False,
            "low_information_question_allowed": False,
            "must_not_route_to": "low_information_question",
            "reason": "event_fact_present_and_explicit_negative_reaction",
        },
        "expected_section_shape": COMMON_SECTION_SHAPE_EXPECTATION,
        "required_surface_features": (
            "two_stage_labels",
            "daily_unpleasant_observation",
            "natural_short_reception",
            "event_fact_not_missing",
            "explicit_reaction_received",
        ),
        "forbidden_surface_fragments": COMMON_FORBIDDEN_SURFACE_FRAGMENTS
        + (
            "まだ詳しい出来事までは見えません",
            "何があったか残してみませんか",
            "相手が悪い",
            "あなたの怒りは正しい",
            "危険な目に遭いました",
            "トラウマ",
        ),
        "forbidden_inferences": (
            "unknown_word_meaning_assertion",
            "target_judgement_agreement",
            "actual_danger_level_assertion",
            "future_risk_assertion",
        ),
    },
    {
        "case_id": "self_confidence_uncertainty_B",
        "source_label": "B",
        "source_issue": "自信のなさ・自己否定寄り・不安 / self_denial_support + uncertainty_support",
        "current_input": {
            "id": "two-stage-reception-self-confidence-B",
            "created_at": "2026-05-26T00:01:00Z",
            "memo": (
                "毎日毎日時間が過ぎていく間に 私は私のここが好き\n"
                "だなって思える所がなくて、自信をつけたいけれど\n"
                "常に自信がなくて出来た達成感がある時は自信がつく\n"
                "でも、いい所は全て中途半端\n"
                "ちょっとでも自分が自分を好きになれるように\n"
                "直したい、頑張りたいって気持ちになって\n"
                "色々挑戦して見てるけど\n"
                "これでいいのかな、大丈夫なのかな 頑張れてるかなって\n"
                "毎日不安で余裕ない\n"
                "私のここが好き 私はこれが得意！って自信もって\n"
                "言える時が来るといいな それも自分次第"
            ),
            "memo_action": "",
            "emotion_details": [{"type": "平穏", "strength": "medium"}],
            "emotions": ["平穏"],
            "category": ["価値観"],
            "is_secret": False,
        },
        "expected_reception_mode": None,
        "expected_reception_mode_any": ("self_denial_support", "uncertainty_support"),
        "expected_ratio_contract": {
            "expected_ratio_reason_any": (
                "self_denial_follow_thickened",
                "self_confidence_uncertainty_follow_thickened",
            ),
            "range_key": "self_negative_or_uncertainty",
            "observation_min": 0.30,
            "observation_max": 0.45,
            "observation_units_min": 1,
            "human_follow_units_min": 1,
            "observation_zero_allowed": False,
            "human_follow_zero_allowed": False,
            "follow_thickened": True,
        },
        "expected_low_information_boundary": {
            "low_information_question_required": False,
            "low_information_question_allowed": False,
            "must_not_route_to": "daily_unpleasant_reception",
            "reason": "self_confidence_uncertainty_with_attempts_present",
        },
        "expected_section_shape": COMMON_SECTION_SHAPE_EXPECTATION,
        "required_surface_features": (
            "two_stage_labels",
            "self_denial_not_fact",
            "effort_or_attempt_received",
            "uncertainty_received",
        ),
        "forbidden_surface_fragments": COMMON_FORBIDDEN_SURFACE_FRAGMENTS
        + (
            "中途半端な人",
            "あなたは本当はすごい人",
            "自信を持ちましょう",
            "って気持ちになってこと",
            "得意こと",
            "同じ流れ",
            "同じ場所",
        ),
        "forbidden_inferences": (
            "identity_claim_accepted_as_fact",
            "personality_praise_overcomfort",
            "action_instruction",
        ),
    },
    {
        "case_id": "positive_change_after_work_streaming",
        "source_label": "Emlisの観測が表示されなかったログ1",
        "source_issue": "嬉しさ・動揺・会話欲求・我慢 / daily_positive_reception + self_understanding_follow",
        "current_input": {
            "id": "two-stage-reception-positive-change-log1",
            "created_at": "2026-05-26T00:02:00Z",
            "memo": (
                "自分の中で大きな変化な事が起きてびっくりしたのと\n"
                "嬉しいのがあって上手く表現できないくらい動揺してる\n"
                "いつもなら仕事があった日はいつもくたくたで\n"
                "ご飯食べるのもなにかするのも元気がないんだけど\n"
                "今日は配信聞いて、誰かとお話したい！って気持ちが\n"
                "とても強くてびっくりしてる\n"
                "今日の夜、可能な限りは配信見よう\n"
                "最低でも15〜20分でやめないとだけど\n"
                "もっと長く話したいのになぁ\n"
                "我慢しないと"
            ),
            "memo_action": "",
            "emotion_details": [{"type": "自己理解", "strength": "medium"}],
            "emotions": ["自己理解"],
            "category": ["人間関係", "生活"],
            "is_secret": False,
        },
        "expected_reception_mode": None,
        "expected_reception_mode_any": ("daily_positive_reception", "self_understanding_follow"),
        "expected_ratio_contract": {
            "expected_ratio_reason_any": (
                "daily_positive_reception_light",
                "standard_state_answer",
            ),
            "range_key_any": ("daily_reception", "standard_state_answer"),
            "observation_min": 0.10,
            "observation_max": 0.60,
            "observation_units_min": 1,
            "human_follow_units_min": 1,
            "observation_zero_allowed": False,
            "human_follow_zero_allowed": False,
        },
        "expected_low_information_boundary": {
            "low_information_question_required": False,
            "low_information_question_allowed": False,
            "reason": "positive_change_and_conversation_wish_present",
        },
        "expected_section_shape": COMMON_SECTION_SHAPE_EXPECTATION,
        "required_surface_features": (
            "two_stage_labels",
            "positive_change_seen",
            "surprise_or_emotional_movement_received",
            "restriction_not_action_instruction",
        ),
        "forbidden_surface_fragments": COMMON_FORBIDDEN_SURFACE_FRAGMENTS
        + (
            "配信をもっと見ましょう",
            "我慢しなくていいです",
            "完全に回復しています",
        ),
        "forbidden_inferences": (
            "stable_recovery_assertion",
            "action_instruction",
            "personality_change_assertion",
        ),
    },
    {
        "case_id": "self_blame_to_gentle_self_observation",
        "source_label": "Emlisの観測が表示されなかったログ2",
        "source_issue": "自己責めから優しく見ようとする流れ / self_understanding_follow",
        "current_input": {
            "id": "two-stage-reception-self-blame-log2",
            "created_at": "2026-05-26T00:03:00Z",
            "memo": (
                "昨日はちょっと気持ちが沈んじゃって、\n"
                "「なんで私はこうなんだろう」って自分を責める時間が少しあったんだよね。\n\n"
                "気づいたら心がちょっと荒れてきてて\n"
                "本当はそんなに自分を追い込まなくていいのに\n"
                "頭の中でぐるぐる考えちゃってた。\n\n"
                "でも、そんな時間を過ごしてみて思ったのは\n"
                "「あ、私ちゃんと向き合わないとまた同じことで苦しくなるな」ってこと。\n\n"
                "落ち込むこと自体が悪いんじゃなくて\n"
                "その気持ちを放置したままにするのが\n"
                "たぶん一番しんどくなる気がしたんだよね。\n\n"
                "だから今日は\n"
                "自分を責めるんじゃなくて\n"
                "「なんでこう感じたんだろう？」って\n"
                "少しだけ優しく見てあげる日にしたい。\n\n"
                "昨日みたいに気持ちが沈む日があってもそこで終わりにするんじゃなくて\n"
                "ちゃんと気づいて、少しずつ整えていけたら\n"
                "それも私の成長の一つになると思うから。\n\n"
                "今日頑張りたいことは\n"
                "完璧に元気になることじゃなくて\n"
                "自分の気持ちをちゃんと見てあげること。\n\n"
                "昨日の自分を否定するんじゃなくて\n"
                "「そんな日もあるよね」って言える自分でいたい。\n\n"
                "それが今の私にできる\n"
                "小さくても大事な頑張りだと思ってる。"
            ),
            "memo_action": "",
            "emotion_details": [
                {"type": "平穏", "strength": "medium"},
                {"type": "喜び", "strength": "medium"},
            ],
            "emotions": ["平穏", "喜び"],
            "category": ["価値観"],
            "is_secret": False,
        },
        "expected_reception_mode": "self_understanding_follow",
        "expected_reception_mode_any": ("self_understanding_follow",),
        "expected_ratio_contract": {
            "expected_ratio_reason_any": (
                "standard_state_answer",
                "self_understanding_follow",
            ),
            "range_key_any": ("standard_state_answer", "self_understanding_follow"),
            "observation_min": 0.30,
            "observation_max": 0.60,
            "observation_units_min": 1,
            "human_follow_units_min": 1,
            "observation_zero_allowed": False,
            "human_follow_zero_allowed": False,
        },
        "expected_low_information_boundary": {
            "low_information_question_required": False,
            "low_information_question_allowed": False,
            "reason": "self_blame_and_gentle_self_observation_direction_present",
        },
        "expected_section_shape": COMMON_SECTION_SHAPE_EXPECTATION,
        "required_surface_features": (
            "two_stage_labels",
            "self_blame_flow_seen",
            "gentle_observation_direction_seen",
            "small_effort_received",
        ),
        "forbidden_surface_fragments": COMMON_FORBIDDEN_SURFACE_FRAGMENTS
        + (
            "成長しています",
            "もう大丈夫",
            "自分を責めないでください",
        ),
        "forbidden_inferences": (
            "stable_growth_assertion",
            "absolute_recovery_assertion",
            "action_instruction",
        ),
    },
    {
        "case_id": "independence_life_health_money_pace",
        "source_label": "Emlisの観測が表示されなかったログ3",
        "source_issue": "自立・生活・体調・お金・続けるペース / standard_state_answer + effort_support",
        "current_input": {
            "id": "two-stage-reception-independence-log3",
            "created_at": "2026-05-26T00:04:00Z",
            "memo": (
                "自分が少しずつ自立していけるように\n"
                "意識していきたいこと\n"
                "生活のこと、体調のこと、お金のこと\n"
                "色んなことを自分で考えて動けるようになりたい。\n\n"
                "まず大切にしたいのは、自分の体調をちゃんと見ながら\n"
                "生活すること。\n"
                "無理をして頑張りすぎるんじゃなくて\n"
                "長く続けていけるペースを作っていきたい"
            ),
            "memo_action": "",
            "emotion_details": [
                {"type": "喜び", "strength": "medium"},
                {"type": "平穏", "strength": "medium"},
            ],
            "emotions": ["喜び", "平穏"],
            "category": ["仕事", "生活"],
            "is_secret": False,
        },
        "expected_reception_mode": None,
        "expected_reception_mode_any": ("standard_state_answer", "effort_support"),
        "expected_ratio_contract": {
            "expected_ratio_reason_any": ("standard_state_answer", "effort_support"),
            "range_key_any": ("standard_state_answer", "effort_support"),
            "observation_min": 0.45,
            "observation_max": 0.60,
            "observation_units_min": 1,
            "human_follow_units_min": 1,
            "observation_zero_allowed": False,
            "human_follow_zero_allowed": False,
        },
        "expected_low_information_boundary": {
            "low_information_question_required": False,
            "low_information_question_allowed": False,
            "reason": "independence_health_life_money_pace_context_present",
        },
        "expected_section_shape": COMMON_SECTION_SHAPE_EXPECTATION,
        "required_surface_features": (
            "two_stage_labels",
            "independence_intention_seen",
            "health_pace_seen",
            "life_money_context_seen",
        ),
        "forbidden_surface_fragments": COMMON_FORBIDDEN_SURFACE_FRAGMENTS
        + (
            "もっと頑張りましょう",
            "自立できます",
            "お金の問題が原因",
        ),
        "forbidden_inferences": (
            "future_success_assertion",
            "money_as_cause_assertion",
            "action_instruction",
        ),
    },
]


def current_input_for_two_stage_reception_case(case: dict) -> dict:
    """Return the normalized current-input fixture shape for later phases."""

    return dict(case["current_input"])


def two_stage_reception_case_by_id(case_id: str) -> dict:
    """Return one two-stage reception fixture by id."""

    for case in TWO_STAGE_RECEPTION_CASES:
        if case["case_id"] == case_id:
            return case
    raise KeyError(case_id)


def split_two_stage_comment_text(comment_text: str) -> dict:
    """Split a labelled two-stage ``comment_text`` candidate.

    The helper is intentionally small and deterministic so later QA tests can
    validate section shape without binding to exact completed sentences.
    """

    text = (comment_text or "").strip()
    observation_marker = TWO_STAGE_LABEL_MARKERS["observation"]
    reception_marker = TWO_STAGE_LABEL_MARKERS["reception"]
    if observation_marker not in text or reception_marker not in text:
        return {
            "labels_present": False,
            "label_order_valid": False,
            "observation_text": "",
            "reception_text": "",
        }

    observation_index = text.index(observation_marker)
    reception_index = text.index(reception_marker)
    label_order_valid = observation_index < reception_index
    if not label_order_valid:
        return {
            "labels_present": True,
            "label_order_valid": False,
            "observation_text": "",
            "reception_text": "",
        }

    observation_text = text[observation_index + len(observation_marker):reception_index].strip()
    reception_text = text[reception_index + len(reception_marker):].strip()
    return {
        "labels_present": True,
        "label_order_valid": True,
        "observation_text": observation_text,
        "reception_text": reception_text,
    }


def evaluate_forbidden_surface_fragments(comment_text: str, case: dict) -> tuple[str, ...]:
    """Return forbidden fragments present in a candidate surface."""

    text = comment_text or ""
    return tuple(fragment for fragment in case["forbidden_surface_fragments"] if fragment in text)
