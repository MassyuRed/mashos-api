# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 13 display-quality QA probes for EmlisAI two-stage reception.

The strings in this module are test-only acceptance probes.  They are not
runtime reply templates and must not be copied into production services.  Tests
use them to verify section shape, required feature families, forbidden surface
blocking, and public-contract boundaries without pinning generated
``comment_text`` to exact output.
"""

PHASE13_TWO_STAGE_DISPLAY_QA_VERSION = "cocolon.emlis_two_stage_reception.display_quality_qa.v1"

PHASE13_TWO_STAGE_DISPLAY_QA_CASES = [
    {
        "case_id": "daily_unpleasant_encounter_A",
        "qa_label": "A",
        "reception_mode": "daily_unpleasant_reception",
        "accepted_surface_probe": (
            "見えたこと：\n"
            "不快で怖さもある出来事に出くわして、怒りが残っているように見えます。\n\n"
            "Emlisから：\n"
            "うわ、それは嫌でしたね。\n"
            "怖さも怒りも残るのは自然です。"
        ),
        "observation_sentence_count_min": 1,
        "observation_sentence_count_max": 1,
        "reception_sentence_count_min": 1,
        "reception_sentence_count_max": 2,
        "required_fragment_groups": (
            ("不快", "怖", "怒り"),
            ("嫌でした", "自然"),
        ),
        "forbidden_fragment_groups": (
            ("何があったか残してみませんか",),
            ("相手が悪い",),
            ("あなたの怒りは正しい",),
        ),
        "blocked_surface_probes": (
            {
                "surface": (
                    "見えたこと：\n"
                    "まだ詳しい出来事までは見えません。\n\n"
                    "Emlisから：\n"
                    "何があったか残してみませんか。"
                ),
                "expected_reason_any": (
                    "daily_reception_question_escape_when_event_fact_present",
                    "two_stage_daily_reception_low_information_question_escape",
                ),
            },
            {
                "surface": (
                    "見えたこと：\n"
                    "不快な出来事に出くわしたように見えます。\n\n"
                    "Emlisから：\n"
                    "相手が悪いです。あなたの怒りは正しいです。"
                ),
                "expected_reason_any": (
                    "target_judgement_agreement",
                    "two_stage_target_judgement_agreement_surface",
                ),
            },
        ),
    },
    {
        "case_id": "self_confidence_uncertainty_B",
        "qa_label": "B",
        "reception_mode": "self_denial_support",
        "accepted_surface_probe": (
            "見えたこと：\n"
            "自信をつけたい気持ちと、これでいいのかという不安が同じ入力に残っているように見えます。\n\n"
            "Emlisから：\n"
            "Emlisには、ここにあるものが「中途半端」だけだとは見えません。\n"
            "直したい気持ちも、挑戦しているところも、一緒に残っています。"
        ),
        "observation_sentence_count_min": 1,
        "observation_sentence_count_max": 1,
        "reception_sentence_count_min": 2,
        "reception_sentence_count_max": 2,
        "required_fragment_groups": (
            ("自信", "不安"),
            ("中途半端", "だけだとは見えません"),
            ("直したい", "挑戦"),
        ),
        "forbidden_fragment_groups": (
            ("中途半端な人",),
            ("自信を持ちましょう",),
            ("得意こと",),
        ),
        "blocked_surface_probes": (
            {
                "surface": (
                    "見えたこと：\n"
                    "中途半端な人だと思っているように見えます。\n\n"
                    "Emlisから：\n"
                    "あなたは本当はすごい人です。自信を持ちましょう。"
                ),
                "expected_reason_any": (
                    "reception_section_personality_claim_surface",
                    "reception_section_action_instruction_surface",
                    "self_denial_identity_claim_as_fact",
                    "state_answer_personality_claim_surface",
                    "state_answer_action_instruction_surface",
                ),
            },
            {
                "surface": (
                    "見えたこと：\n"
                    "自信をつけたいって気持ちになってことが見えます。\n\n"
                    "Emlisから：\n"
                    "得意ことが見つかるはずです。"
                ),
                "expected_reason_any": (
                    "two_stage_koto_splice_or_malformed_nominalization",
                    "two_stage_bad_grammar_or_koto_splice_surface",
                ),
            },
        ),
    },
    {
        "case_id": "positive_change_after_work_streaming",
        "qa_label": "ログ1",
        "reception_mode": "daily_positive_reception",
        "accepted_surface_probe": (
            "見えたこと：\n"
            "仕事後の疲れがある中で、誰かと話したい気持ちが強く出てきた変化が見えます。\n\n"
            "Emlisから：\n"
            "それだけ気持ちが動いたこと自体、かなり大きい変化に見えます。\n"
            "嬉しさと動揺が一緒にあるのも自然です。"
        ),
        "observation_sentence_count_min": 1,
        "observation_sentence_count_max": 1,
        "reception_sentence_count_min": 2,
        "reception_sentence_count_max": 2,
        "required_fragment_groups": (
            ("疲れ", "話したい", "変化"),
            ("嬉しさ", "動揺"),
        ),
        "forbidden_fragment_groups": (
            ("配信をもっと見ましょう",),
            ("我慢しなくていいです",),
            ("完全に回復しています",),
        ),
        "blocked_surface_probes": (
            {
                "surface": (
                    "見えたこと：\n"
                    "話したい気持ちが出ています。\n\n"
                    "Emlisから：\n"
                    "我慢しなくていいです。"
                ),
                "expected_reason_any": (
                    "reception_section_action_instruction_surface",
                    "state_answer_action_instruction_surface",
                ),
            },
            {
                "surface": (
                    "見えたこと：\n"
                    "仕事後でも完全に回復しています。\n\n"
                    "Emlisから：\n"
                    "もう大丈夫です。"
                ),
                "expected_reason_any": (
                    "reception_section_stable_growth_or_recovery_assertion",
                    "reception_section_stable_state_overclaim",
                ),
            },
        ),
    },
    {
        "case_id": "self_blame_to_gentle_self_observation",
        "qa_label": "ログ2",
        "reception_mode": "self_understanding_follow",
        "accepted_surface_probe": (
            "見えたこと：\n"
            "自分を責める流れから、自分の気持ちを少し優しく見ようとする方向へ移っているように見えます。\n\n"
            "Emlisから：\n"
            "昨日の自分を否定するだけで終わらせずに見直そうとしているところが、ここには残っています。\n"
            "完璧に元気になることより、気持ちを見てあげることを大事にしているのが伝わります。"
        ),
        "observation_sentence_count_min": 1,
        "observation_sentence_count_max": 1,
        "reception_sentence_count_min": 2,
        "reception_sentence_count_max": 2,
        "required_fragment_groups": (
            ("責める", "優しく"),
            ("否定するだけで終わらせず", "見直そう"),
            ("気持ちを見てあげる",),
        ),
        "forbidden_fragment_groups": (
            ("成長しています",),
            ("もう大丈夫",),
            ("自分を責めないでください",),
        ),
        "blocked_surface_probes": (
            {
                "surface": (
                    "見えたこと：\n"
                    "自己責めを乗り越えて成長しています。\n\n"
                    "Emlisから：\n"
                    "もう大丈夫です。"
                ),
                "expected_reason_any": (
                    "reception_section_stable_growth_or_recovery_assertion",
                    "reception_section_stable_state_overclaim",
                ),
            },
        ),
    },
    {
        "case_id": "independence_life_health_money_pace",
        "qa_label": "ログ3",
        "reception_mode": "standard_state_answer",
        "accepted_surface_probe": (
            "見えたこと：\n"
            "自立したい気持ちと、体調を見ながら長く続けられるペースを作りたい気持ちが並んでいます。\n\n"
            "Emlisから：\n"
            "無理に頑張り切るより、続けられる形を探しているのが良い線に見えます。\n"
            "生活、体調、お金を自分で見ようとしているところまで、ちゃんと残っています。"
        ),
        "observation_sentence_count_min": 1,
        "observation_sentence_count_max": 1,
        "reception_sentence_count_min": 2,
        "reception_sentence_count_max": 2,
        "required_fragment_groups": (
            ("自立", "体調", "ペース"),
            ("生活", "お金"),
            ("続けられる",),
        ),
        "forbidden_fragment_groups": (
            ("もっと頑張りましょう",),
            ("自立できます",),
            ("お金の問題が原因",),
        ),
        "blocked_surface_probes": (
            {
                "surface": (
                    "見えたこと：\n"
                    "自立したい気持ちが見えます。\n\n"
                    "Emlisから：\n"
                    "自立できます。"
                ),
                "expected_reason_any": (
                    "reception_section_stable_growth_or_recovery_assertion",
                    "reception_section_stable_state_overclaim",
                ),
            },
            {
                "surface": (
                    "見えたこと：\n"
                    "自立したい気持ちが見えます。\n\n"
                    "Emlisから：\n"
                    "お金の問題が原因です。"
                ),
                "expected_reason_any": (
                    "reception_section_new_fact_overclaim",
                ),
            },
        ),
    },
]

PHASE13_TWO_STAGE_DISPLAY_QA_CASE_IDS = {
    case["case_id"] for case in PHASE13_TWO_STAGE_DISPLAY_QA_CASES
}


def phase13_two_stage_display_qa_case_by_id(case_id: str) -> dict:
    for case in PHASE13_TWO_STAGE_DISPLAY_QA_CASES:
        if case["case_id"] == case_id:
            return case
    raise KeyError(case_id)


def iter_phase13_blocked_surface_probes() -> tuple[dict, ...]:
    probes: list[dict] = []
    for case in PHASE13_TWO_STAGE_DISPLAY_QA_CASES:
        for index, probe in enumerate(case.get("blocked_surface_probes") or ()):  # pragma: no branch
            probes.append(
                {
                    "probe_id": f"{case['case_id']}#{index}",
                    "case_id": case["case_id"],
                    "reception_mode": case["reception_mode"],
                    **probe,
                }
            )
    return tuple(probes)
