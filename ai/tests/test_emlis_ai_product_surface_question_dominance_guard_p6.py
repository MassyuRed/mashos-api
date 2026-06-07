# -*- coding: utf-8 -*-
from __future__ import annotations

"""P6 product-surface validation tests for reception-required surfaces.

P6 keeps RN/API/DB/Gate contracts unchanged while ensuring limited_grounding
and true low_information public surfaces cannot fall back to reception-less,
question-first, or question-dominant replies.
"""

import json

from emlis_ai_gate_recovery_public_constants import (
    CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE,
    CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER,
)
from emlis_ai_input_material_bundle import build_emlis_input_material_bundle
from emlis_ai_product_surface_validation import (
    PRODUCT_SURFACE_BLOCKER_LOW_INFORMATION_MISROUTE,
    PRODUCT_SURFACE_BLOCKER_NONE,
    PRODUCT_SURFACE_BLOCKER_QUESTION_BEFORE_RECEPTION,
    PRODUCT_SURFACE_BLOCKER_QUESTION_DOMINANT_SURFACE,
    PRODUCT_SURFACE_BLOCKER_RECEPTION_SECTION_MISSING,
    assert_product_surface_validation_summary,
    build_product_surface_validation_summary,
    product_surface_validation_public_summary,
)
from emlis_ai_public_surface_requirement import (
    SURFACE_REQUIREMENT_LABELLED_TWO_STAGE,
    SURFACE_REQUIREMENT_LOW_INFORMATION_OBSERVATION,
    resolve_public_surface_requirement,
)

LIMITED_VALID_COMMENT = (
    "見えたこと：\n"
    "今は、気力が戻ってきたタイミングを逃したくない気持ちと、人と近くありたい願いが一緒に出ている状態に見えます。\n\n"
    "Emlisから：\n"
    "また何かに挑戦したいと思えたことを、今の回復の動きとして大切に受け取りました。"
)
LOW_INFORMATION_VALID_COMMENT = (
    "見えたこと：\n"
    "今は、詳しい出来事まではまだ見えていませんが、何かを残そうとしている入口までは見えています。\n\n"
    "Emlisから：\n"
    "まだ整理できていない状態でも、そのまま置いたことをEmlisは受け取りました。"
    "詳しく残せそうなら、あとで一つだけ残してみませんか。"
)
LOW_INFORMATION_NO_RECEPTION_COMMENT = (
    "見えたこと：\n"
    "今は、詳しい出来事まではまだ見えていませんが、何かを残そうとしている入口までは見えています。"
)
LOW_INFORMATION_QUESTION_BEFORE_RECEPTION_COMMENT = (
    "見えたこと：\n"
    "詳しく残せそうなら、何があったか残してみませんか。\n\n"
    "Emlisから：\n"
    "そのまま置いたことをEmlisは受け取りました。"
)
LOW_INFORMATION_QUESTION_DOMINANT_COMMENT = (
    "見えたこと：\n"
    "今は、何かを残そうとしている入口までは見えています。\n\n"
    "Emlisから：\n"
    "そのまま置いたことをEmlisは受け取りました。"
    "詳しく残せそうなら、何があったか残してみませんか。"
    "あとで一つだけ足してみませんか。"
    "もう少し書けそうなら、何が変わったのか残してみませんか。"
)


def _passed_public_meta() -> dict[str, object]:
    return {
        "observation_status": "passed",
        "runtime_surface_pre_return_gate": {"passed": True, "action": "allow"},
        "visible_surface_acceptance_gate": {"classification": "pass", "action": "allow"},
        "display_gate": {"passed": True},
        "state_answer_gate_boundary": {"passed": True},
    }


def _limited_current_input() -> dict[str, object]:
    return {
        "memo": (
            "沢山甘えられて寂しい時にそばに居てくれるような存在やっぱりいいなって思う "
            "気力が出てきた時は恋愛もしたくなる。でもやる気力が出てきたのが嬉しいし "
            "このタイミングでいろんな事に挑戦して、いずれは素敵な人と出会えたらいいな"
        ),
        "memo_action": "",
        "emotion_details": [{"type": "平穏", "strength": "medium"}],
        "category": ["生活", "人生"],
    }


def _low_information_current_input() -> dict[str, object]:
    return {
        "memo": "疲れた",
        "memo_action": "",
        "emotion_details": [{"type": "悲しみ", "strength": "strong"}],
        "category": ["生活"],
    }


def _surface_requirement_for(current_input: dict[str, object]) -> dict[str, object]:
    bundle = build_emlis_input_material_bundle(current_input)
    return resolve_public_surface_requirement(
        current_input=current_input,
        material_route=bundle.as_meta(),
        composer_meta={},
        diagnostic_summary={},
    )


def _candidate(source_kind: str) -> dict[str, object]:
    return {
        "candidate_source_kind": source_kind,
        "composer_source": "ai_generated",
        "candidate_status": "generated",
    }


def test_p6_accepts_limited_grounding_labelled_reception_without_question() -> None:
    requirement = _surface_requirement_for(_limited_current_input())
    assert requirement["surface_requirement_family"] == SURFACE_REQUIREMENT_LABELLED_TWO_STAGE
    assert requirement["material_quality_family"] == "limited_grounding"

    summary = build_product_surface_validation_summary(
        comment_text=LIMITED_VALID_COMMENT,
        emlis_ai_public_meta=_passed_public_meta(),
        surface_requirement=requirement,
        candidate_generation_summary=_candidate(
            CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE
        ),
        input_feedback_included=True,
    )

    assert summary["rn_visible"] is True
    assert summary["product_surface_valid"] is True
    assert summary["blocker_code"] == PRODUCT_SURFACE_BLOCKER_NONE
    assert summary["low_information_surface_used"] is False
    assert summary["question_dominance_guard"]["checked"] is True
    assert summary["question_dominance_guard"]["passed"] is True
    assert summary["question_dominance_guard"]["reception_section_present"] is True
    assert summary["question_dominance_guard"]["question_surface_present"] is False
    assert_product_surface_validation_summary(summary)


def test_p6_rejects_limited_grounding_low_information_source_misroute() -> None:
    requirement = _surface_requirement_for(_limited_current_input())
    assert requirement["surface_requirement_family"] == SURFACE_REQUIREMENT_LABELLED_TWO_STAGE
    assert requirement["low_information_allowed"] is False

    summary = build_product_surface_validation_summary(
        comment_text=LIMITED_VALID_COMMENT,
        emlis_ai_public_meta=_passed_public_meta(),
        surface_requirement=requirement,
        candidate_generation_summary=_candidate(CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER),
        input_feedback_included=True,
    )

    assert summary["rn_visible"] is True
    assert summary["product_surface_valid"] is False
    assert summary["low_information_surface_used"] is True
    assert summary["blocker_code"] == PRODUCT_SURFACE_BLOCKER_LOW_INFORMATION_MISROUTE
    assert_product_surface_validation_summary(summary)


def test_p6_accepts_low_information_reception_with_question_after_reception() -> None:
    requirement = _surface_requirement_for(_low_information_current_input())
    assert requirement["surface_requirement_family"] == SURFACE_REQUIREMENT_LOW_INFORMATION_OBSERVATION
    assert requirement["material_quality_family"] == "low_information"

    summary = build_product_surface_validation_summary(
        comment_text=LOW_INFORMATION_VALID_COMMENT,
        emlis_ai_public_meta=_passed_public_meta(),
        surface_requirement=requirement,
        candidate_generation_summary=_candidate(CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER),
        input_feedback_included=True,
    )

    assert summary["rn_visible"] is True
    assert summary["product_surface_valid"] is True
    assert summary["blocker_code"] == PRODUCT_SURFACE_BLOCKER_NONE
    assert summary["low_information_surface_used"] is True
    guard = summary["question_dominance_guard"]
    assert guard["checked"] is True
    assert guard["passed"] is True
    assert guard["reception_section_present"] is True
    assert guard["question_after_reception"] is True
    assert guard["question_before_reception"] is False
    assert guard["question_dominant"] is False
    assert_product_surface_validation_summary(summary)


def test_p6_rejects_low_information_without_reception_section() -> None:
    requirement = _surface_requirement_for(_low_information_current_input())

    summary = build_product_surface_validation_summary(
        comment_text=LOW_INFORMATION_NO_RECEPTION_COMMENT,
        emlis_ai_public_meta=_passed_public_meta(),
        surface_requirement=requirement,
        candidate_generation_summary=_candidate(CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER),
        input_feedback_included=True,
    )

    assert summary["rn_visible"] is True
    assert summary["product_surface_valid"] is False
    assert summary["blocker_code"] == PRODUCT_SURFACE_BLOCKER_RECEPTION_SECTION_MISSING
    assert summary["question_dominance_guard"]["reception_section_present"] is False
    assert "reception_section_missing" in summary["decision_reasons"]
    assert_product_surface_validation_summary(summary)


def test_p6_rejects_question_before_reception() -> None:
    requirement = _surface_requirement_for(_low_information_current_input())

    summary = build_product_surface_validation_summary(
        comment_text=LOW_INFORMATION_QUESTION_BEFORE_RECEPTION_COMMENT,
        emlis_ai_public_meta=_passed_public_meta(),
        surface_requirement=requirement,
        candidate_generation_summary=_candidate(CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER),
        input_feedback_included=True,
    )

    assert summary["rn_visible"] is True
    assert summary["product_surface_valid"] is False
    assert summary["blocker_code"] == PRODUCT_SURFACE_BLOCKER_QUESTION_BEFORE_RECEPTION
    assert summary["question_dominance_guard"]["question_before_reception"] is True
    assert "question_before_reception" in summary["decision_reasons"]
    assert_product_surface_validation_summary(summary)


def test_p6_rejects_question_dominant_after_reception() -> None:
    requirement = _surface_requirement_for(_low_information_current_input())

    summary = build_product_surface_validation_summary(
        comment_text=LOW_INFORMATION_QUESTION_DOMINANT_COMMENT,
        emlis_ai_public_meta=_passed_public_meta(),
        surface_requirement=requirement,
        candidate_generation_summary=_candidate(CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER),
        input_feedback_included=True,
    )

    assert summary["rn_visible"] is True
    assert summary["product_surface_valid"] is False
    assert summary["blocker_code"] == PRODUCT_SURFACE_BLOCKER_QUESTION_DOMINANT_SURFACE
    guard = summary["question_dominance_guard"]
    assert guard["question_after_reception"] is True
    assert guard["question_dominant"] is True
    assert "question_dominant_surface" in summary["decision_reasons"]
    assert_product_surface_validation_summary(summary)


def test_p6_public_summary_keeps_question_guard_body_free() -> None:
    requirement = _surface_requirement_for(_low_information_current_input())
    summary = build_product_surface_validation_summary(
        comment_text=LOW_INFORMATION_QUESTION_DOMINANT_COMMENT,
        emlis_ai_public_meta=_passed_public_meta(),
        surface_requirement=requirement,
        candidate_generation_summary=_candidate(CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER),
        input_feedback_included=True,
    )

    public_summary = product_surface_validation_public_summary(summary)
    guard = public_summary["question_dominance_guard"]
    assert guard["checked"] is True
    assert guard["passed"] is False
    assert guard["question_dominant"] is True
    assert guard["body_free"] is True
    assert guard["raw_input_included"] is False
    assert guard["comment_text_body_included"] is False

    dumped = json.dumps(public_summary, ensure_ascii=False, sort_keys=True)
    assert LOW_INFORMATION_QUESTION_DOMINANT_COMMENT not in dumped
    assert '"comment_text":' not in dumped
    assert '"raw_input":' not in dumped
    assert "memo" not in dumped
