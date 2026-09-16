"""Public synthetic regressions for a still-open original-meaning omission.

These cases exercise the real initial/answer path. They do not exempt the
existing inverse, introduce a renderer, or make an inner possibility a fact.
The defect is already present at the product source bound to 7c3dff8.
"""
import pytest

from test_cmee_emlis_q3_thread import (
    MeaningExperienceEngine,
    advance,
    begin,
    build_updated_grounded_plan,
    initial,
    prepare_emlis_meaning,
)


THOUGHTS = (
    "返事が遅いだけなのに、避けられたのかもって考えちゃう。",
    "予定が決まらないだけなのに、忘れられたのかもって考えちゃう。",
)
ACTION = "机を拭いた。"


def _assert_original_thought_has_required_reception_evidence(prepared, thought):
    """Check source participation, not one prescribed wording or family."""
    resolver = prepared.thread.resolver()
    expected = {
        span.span_id
        for span in resolver.resolve_many(resolver.span_ids)
        if span.source_field == "memo" and span.raw_text == thought.rstrip("。")
    }
    assert len(expected) == 1, "Synthetic original clause must keep its exact evidence"
    plan = build_updated_grounded_plan(prepared)
    received = {
        span_id
        for move in plan.response_plan.human_reception_plan.moves
        if move.required
        for span_id in move.source_evidence_span_ids
    }
    assert expected <= received, "Original uncertain thought lost its Reception duty"


@pytest.mark.parametrize("thought", THOUGHTS)
@pytest.mark.parametrize("premium", [False, True])
def test_original_uncertain_thought_is_not_replaced_by_separate_action(thought, premium):
    request = (begin if premium else initial)(thought, ACTION)
    prepared = prepare_emlis_meaning(request)
    result = MeaningExperienceEngine().generate(request)
    assert result.artifact, result.reason_codes
    assert thought.rstrip("。") in result.artifact.observation
    assert ACTION.rstrip("。") in result.artifact.observation
    assert result.question is None
    _assert_original_thought_has_required_reception_evidence(prepared, thought)
    # A source possibility must not disappear into an unqualified assertion.
    # Permit an explicit paraphrase; do not require an exact full-source quote.
    assert any(word in result.artifact.reception for word in ("かも", "可能性"))
    assert request.emlis_thread.current_round == 0


@pytest.mark.parametrize("thought", THOUGHTS)
@pytest.mark.parametrize("premium", [False, True])
def test_unrelated_answer_does_not_drop_original_uncertain_thought(thought, premium):
    request = (begin if premium else initial)("誘われたのに、悲しかった。" + thought, ACTION)
    old_source = request.current_input_bundle
    request = advance(request, "その時は重かった。")
    prepared = prepare_emlis_meaning(request)
    result = MeaningExperienceEngine().generate(request)
    assert request.current_input_bundle == old_source
    assert request.emlis_thread.current_round == 1
    assert request.emlis_thread.question_control_context.question_limit == (3 if premium else 1)
    assert result.artifact, result.reason_codes
    _assert_original_thought_has_required_reception_evidence(prepared, thought)
    assert any(word in result.artifact.reception for word in ("かも", "可能性"))
    assert "その時の重さ" in result.artifact.reception
