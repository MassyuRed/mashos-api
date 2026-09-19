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


@pytest.mark.parametrize('thought', [
    '返事が遅いだけなのに、避けられたのかもと考えてしまう。',
    '予定が決まらないだけなのに、忘れられたのかもしれないと思ってしまう。',
    '私が避けられたのかもって考えちゃう。',
    '今は忘れられたのかもと考えている。',
])
def test_present_cognitive_host_keeps_inner_possibility_and_not_an_inferred_feeling(thought):
    from emlis_ai_grounded_observation_plan import _source_current_cognition
    request = begin(thought, ACTION)
    prepared = prepare_emlis_meaning(request)
    plan = build_updated_grounded_plan(prepared)
    witnesses = [n for n in plan.nuclei if _source_current_cognition(n)]
    assert len(witnesses) == 1
    assert witnesses[0].semantic_frame.predicate_kind == 'state'
    result = MeaningExperienceEngine().generate(request)
    assert result.artifact, result.reason_codes
    assert thought.rstrip('。') in result.artifact.reception
    assert not any(word in result.artifact.reception for word in ('不安な気持ち', '悲しい気持ち', 'まだ分からない'))
    _assert_original_thought_has_required_reception_evidence(prepared, thought)


@pytest.mark.parametrize('text', [
    '友人は避けられたのかもって考えちゃう。',
    '友人が避けられたのかもって考えている。',
    '友人によると、避けられたのかもって考えちゃう。',
    '「避けられたのかもって考えちゃう」と友人が言った。',
    '友人の感想です。避けられたのかもって考えちゃう。',
    '友人は困った。避けられたのかもって考えちゃう。',
    '避けられたのかもって考えちゃう？',
    '避けられたのかもって考えてしまった。',
    '避けられたのかもって考えない。',
    '避けられたのかもって考えるとは限らない。',
    'もし避けられたのかもって考えるなら、休む。',
    '明日は避けられたのかもって考える。',
    '避けられたのかもって考える予定です。',
    '避けられたのかもって考えるのが怖い。',
    '避けられたのかもって考えると言われた。',
])
def test_unasserted_or_other_owned_host_cannot_borrow_present_self_witness(text):
    from emlis_ai_grounded_observation_plan import _source_current_cognition
    plan = build_updated_grounded_plan(prepare_emlis_meaning(begin(text, ACTION)))
    assert not any(_source_current_cognition(n) for n in plan.nuclei)


@pytest.mark.parametrize('operation,removed,new', [
    ('「重かった」ではなく「苦しかった」です。', 'その時の重さ', '苦しさ'),
    ('「重かった」は誤りです。', 'その時の重さ', None),
])
def test_correcting_or_withdrawing_an_unrelated_answer_retains_the_original_cognition(operation, removed, new):
    thought = THOUGHTS[0]
    request = advance(advance(begin('誘われたのに、悲しかった。頼まれたのに、寂しかった。' + thought, ACTION),
                              'その時は重かった。'), operation)
    prepared = prepare_emlis_meaning(request)
    result = MeaningExperienceEngine().generate(request)
    assert result.artifact, result.reason_codes
    assert removed not in result.artifact.reception
    if new is not None:
        assert new in result.artifact.reception
    assert thought.rstrip('。') in result.artifact.reception
    assert '机を拭いた' in result.artifact.reception
    _assert_original_thought_has_required_reception_evidence(prepared, thought)


def test_cognition_and_answer_partitions_cover_complete_claims_without_borrowing_action_basis():
    from cocolon_meaning_experience_engine.emlis_thread_projection import project_thread_meaning
    prepared = prepare_emlis_meaning(advance(begin('誘われたのに、悲しかった。' + THOUGHTS[0], ACTION),
                                             'その時は重かった。'))
    plan = build_updated_grounded_plan(prepared)
    selected = project_thread_meaning(prepared, plan).selected_reception
    assert len(plan.response_plan.human_reception_plan.moves) == 3
    for claim in {row.projected_claim_ref for row in selected.decisions}:
        rows = [row for row in selected.decisions if row.projected_claim_ref == claim]
        contributions = [ref for row in rows for ref in row.selected_contribution_refs]
        assert len(contributions) == len(set(contributions))
        assert set(contributions) == set(rows[0].subjective_proposition.target_contribution_refs)


@pytest.mark.parametrize('answered', [False, True])
def test_independent_inverse_rejects_lost_uncertainty_owner_time_and_missing_cognition(monkeypatch, answered):
    from cocolon_meaning_experience_engine.emlis_thread_projection import project_thread_meaning
    from cocolon_meaning_experience_engine.emlis_thread_surface import realize_emlis_thread_body
    from emlis_ai_grounded_observation_gate import evaluate_grounded_surface_body_inverse
    import emlis_ai_grounded_sentence_surface as surface
    import emlis_ai_grounded_human_reception as reception
    import emlis_ai_grounded_observation_gate as gate
    from types import SimpleNamespace
    thought = THOUGHTS[0]
    request = begin(('誘われたのに、悲しかった。' if answered else '') + thought, ACTION)
    if answered:
        request = advance(request, 'その時は重かった。')
    prepared = prepare_emlis_meaning(request)
    plan = build_updated_grounded_plan(prepared)
    resolver = prepared.thread.resolver()
    projection = project_thread_meaning(prepared, plan)
    result = realize_emlis_thread_body(prepared)
    assert result.artifact
    sentence = surface.build_grounded_sentence_plan(plan, resolver, recovery_stage='full')
    def forbidden(*args, **kwargs):
        raise AssertionError('Independent inverse must not call the author again')
    monkeypatch.setattr(reception, '_author_source_grounded_reception_clauses', forbidden)
    def passed(follow):
        # As in the existing inverse tests, neutralize replay equality only.
        # The source/body checks must reject corruption with the author disabled.
        monkeypatch.setattr(gate, "replay_source_grounded_human_reception_from_plan",
                            lambda *a, **kw: SimpleNamespace(text=follow))
        body = result.artifact.text.replace(result.artifact.reception, follow)
        return evaluate_grounded_surface_body_inverse(body=body.encode(), plan=plan,
            sentence_plan=sentence, resolver=resolver,
            selected_subjective_input=projection.selected_reception).passed
    follow = result.artifact.reception
    assert passed(follow)
    for changed in [follow.replace('のかもって考えちゃう', 'と分かった'),
                    follow.replace('考えちゃう', '考えていた'),
                    follow.replace('避けられたのかも', '友人が避けられたのかも'),
                    follow.replace(thought.rstrip('。'), ''),
                    follow.replace('返事が遅いだけなのに、', '')]:
        assert changed != follow
        assert not passed(changed)
