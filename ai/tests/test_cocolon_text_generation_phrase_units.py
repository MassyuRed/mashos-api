# -*- coding: utf-8 -*-
from __future__ import annotations

from cocolon_text_generation_core.evidence import make_evidence_span_like
from cocolon_text_generation_core.phrase_units import (
    QUALITY_FLAG_EMOTION_LABEL_ONLY,
    QUALITY_FLAG_ORPHAN_PARTICLE,
    QUALITY_FLAG_TOO_LONG_QUOTE,
    QUALITY_FLAG_UNFINISHED_PHRASE,
    build_phrase_units,
    is_phrase_unit_body_candidate,
    phrase_unit_quality_flags,
)
from cocolon_text_generation_core.sentence_plan import (
    build_sentence_plan_for_roles,
    build_sentence_plans_for_role_groups,
    validate_sentence_plans,
)
from cocolon_text_generation_core.types import SentencePlan


def _span(span_id: str, raw_text: str, *, role: str = "observed_role"):
    return make_evidence_span_like(
        span_id=span_id,
        source_id="input-1",
        field_name="current_input",
        raw_text=raw_text,
        role=role,
    )


def test_phase4_rejects_known_unfinished_fragments() -> None:
    for text in ("なんであが", "考え始めが", "悪化するが"):
        flags = phrase_unit_quality_flags(text)
        assert QUALITY_FLAG_UNFINISHED_PHRASE in flags or QUALITY_FLAG_ORPHAN_PARTICLE in flags
        assert not is_phrase_unit_body_candidate(text)


def test_phase4_does_not_adopt_emotion_label_as_phrase_unit_body() -> None:
    result = build_phrase_units(
        [
            _span("s1", "不安。", role="emotion_label"),
            _span("s2", "怒り", role="emotion_label"),
            _span("s3", "片付けられたこと", role="small_action"),
        ]
    )

    assert [unit.text for unit in result.phrase_units] == ["片付けられたこと"]
    assert set(result.skipped_span_ids) == {"s1", "s2"}
    assert any(
        QUALITY_FLAG_EMOTION_LABEL_ONLY in candidate.get("quality_flags", [])
        for candidate in result.rejected_candidates
    )


def test_phase4_rejects_too_long_quote_as_common_phrase_unit() -> None:
    long_quote = "これは" + "とても" * 30 + "長い原文引用です"
    result = build_phrase_units([_span("s1", long_quote, role="raw_quote")])

    assert not result.phrase_units
    assert result.skipped_span_ids == ("s1",)
    assert QUALITY_FLAG_TOO_LONG_QUOTE in result.rejected_candidates[0]["quality_flags"]


def test_phase4_preserves_core_specific_role_strings_without_meaning_detection() -> None:
    result = build_phrase_units(
        [
            _span("s1", "問いとして残したい核", role="piece_question_core"),
            _span("s2", "答えとして残したい核", role="piece_answer_core"),
            _span("s3", "期間内に増えた観測", role="analysis_observation_period"),
        ],
        must_keep_roles=("piece_answer_core",),
    )

    assert [unit.role for unit in result.phrase_units] == [
        "piece_question_core",
        "piece_answer_core",
        "analysis_observation_period",
    ]
    assert [unit.must_keep for unit in result.phrase_units] == [False, True, False]
    assert all(unit.meta["role_meaning_interpreted"] is False for unit in result.phrase_units)


def test_phase4_builds_sentence_plan_from_exact_role_strings() -> None:
    phrase_result = build_phrase_units(
        [
            _span("s1", "問いとして残したい核", role="piece_question_core"),
            _span("s2", "答えとして残したい核", role="piece_answer_core"),
        ]
    )
    plan = build_sentence_plan_for_roles(
        phrase_result.phrase_units,
        sentence_plan_id="sp_piece_answer",
        roles=("piece_answer_core",),
        relation_type="answer_preservation",
        line_role="answer",
    )

    assert plan is not None
    assert plan.phrase_unit_ids == ("pu2",)
    assert plan.relation_type == "answer_preservation"
    assert plan.line_role == "answer"
    assert plan.meta["role_meaning_interpreted"] is False
    assert validate_sentence_plans([plan], phrase_result.phrase_units) == ()


def test_phase4_sentence_plan_result_keeps_optional_groups_fail_closed() -> None:
    phrase_result = build_phrase_units([_span("s1", "観測できる根拠", role="analysis_observation_period")])
    plan_result = build_sentence_plans_for_role_groups(
        phrase_result.phrase_units,
        [
            {
                "plan_id": "sp_analysis",
                "roles": ("analysis_observation_period",),
                "relation_type": "observation",
                "line_role": "period_observation",
            },
            {
                "plan_id": "sp_missing_optional",
                "roles": ("missing_role",),
                "must_include": False,
            },
        ],
    )

    assert [plan.sentence_plan_id for plan in plan_result.sentence_plans] == ["sp_analysis"]
    assert plan_result.skipped_plan_ids == ("sp_missing_optional",)
    assert plan_result.meta["role_meaning_interpreted"] is False
    assert plan_result.usable


def test_phase4_sentence_plan_validation_reports_missing_unit_id() -> None:
    bad_plan = SentencePlan(sentence_plan_id="sp_bad", phrase_unit_ids=("missing-pu",), relation_type="test")
    reasons = validate_sentence_plans([bad_plan], [])

    assert reasons == ("sentence_plan_unit_missing:sp_bad",)
