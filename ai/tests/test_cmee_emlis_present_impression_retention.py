"""Synthetic regressions for a present impression beside an independent action.

A finite cognitive host does not assert its embedded proposition as fact.
These tests use the existing sole body path and independent inverse.
"""

from helpers.retained_assertions import continue_assertions, retained_assertion
from dataclasses import replace
from types import SimpleNamespace
import pytest
from test_cmee_emlis_q3_thread import (
    begin, initial, advance, MeaningExperienceEngine,
    prepare_emlis_meaning, build_updated_grounded_plan,
)
from test_cmee_emlis_original_cognition_retention import (
    _assert_original_thought_has_required_reception_evidence,
)
from emlis_ai_grounded_observation_plan import _source_current_cognition

ACTION = '机を拭いた。'
IMPRESSIONS = (
    '少し続けられる気がする。',
    '今なら少し書ける気がします。',
    '以前は止めていた練習だけど、今なら少し続けられる気がする。',
    '少し続けられない気がする。',
)

@pytest.mark.parametrize('thought', IMPRESSIONS)
@pytest.mark.parametrize('premium', [False, True])
def test_present_impression_remains_tentative_and_has_its_own_reception_duty(thought, premium):
    req = (begin if premium else initial)(thought, ACTION)
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    witnesses = [n for n in plan.nuclei if _source_current_cognition(n)]
    assert len(witnesses) == 1
    # Fact concerns the present cognitive host, never the embedded possibility.
    assert witnesses[0].semantic_frame.predicate_kind == 'state'
    assert not any(c == 'operator:performed_action' for c in witnesses[0].semantic_frame.attribute_codes)
    out = MeaningExperienceEngine().generate(req)
    assert out.artifact, out.reason_codes
    assert thought.rstrip('。') in out.artifact.reception
    assert '机を拭いた' in out.artifact.reception
    assert out.question is None
    assert req.emlis_thread.current_round == 0
    _assert_original_thought_has_required_reception_evidence(prepared, thought)

@pytest.mark.parametrize('thought', IMPRESSIONS[:3])
@pytest.mark.parametrize('premium', [False, True])
@continue_assertions
def test_unrelated_answer_does_not_replace_the_original_impression(thought, premium):
    req = (begin if premium else initial)('誘われたのに、悲しかった。' + thought, ACTION)
    old_source = req.current_input_bundle
    req = advance(req, 'その時は重かった。')
    out = MeaningExperienceEngine().generate(req)
    retained_assertion(lambda: (out.artifact), 'out.artifact', lambda: (out.reason_codes))
    retained_assertion(lambda: (req.current_input_bundle == old_source), 'req.current_input_bundle == old_source')
    retained_assertion(lambda: (req.emlis_thread.current_round == 1), 'req.emlis_thread.current_round == 1')
    retained_assertion(lambda: (req.emlis_thread.question_control_context.question_limit == (3 if premium else 1)), 'req.emlis_thread.question_control_context.question_limit == (3 if premium else 1)')
    retained_assertion(lambda: (thought.rstrip('。') in out.artifact.reception), "thought.rstrip('。') in out.artifact.reception")
    retained_assertion(lambda: ('その時の重さ' in out.artifact.reception), "'その時の重さ' in out.artifact.reception")
    retained_assertion(lambda: ('机を拭いた' in out.artifact.reception), "'机を拭いた' in out.artifact.reception")
    _assert_original_thought_has_required_reception_evidence(prepare_emlis_meaning(req), thought)

@pytest.mark.parametrize('text', [
    '友人は少し続けられる気がする。',
    '友人が少し続けられる気がする。',
    '友人も少し続けられる気がする。',
    'Alexも少し続けられる気がする。',
    '友人には少し続けられる気がする。',
    '友人によると、少し続けられる気がする。',
    '「少し続けられる気がする」と友人が言った。',
    '友人の感想です。少し続けられる気がする。',
    '友人は困った。少し続けられる気がする。',
    '少し続けられる気がする？',
    '少し続けられる気がした。',
    '少し続けられる気がしない。',
    '少し続けられる気がするとは限らない。',
    'もし少し続けられる気がするなら、休む。',
    '明日は少し続けられる気がする。',
    '少し続けられる気がする予定です。',
    '少し続けられる気がするのが怖い。',
    '少し続けられる気がすると言われた。',
    '少し続けられる気がするらしい。',
    '以前は友人の感想によると続けられるけど、今なら書ける気がする。',
])
def test_unasserted_or_other_owned_impression_cannot_borrow_a_present_self_witness(text):
    plan = build_updated_grounded_plan(prepare_emlis_meaning(begin(text, ACTION)))
    assert not any(_source_current_cognition(n) for n in plan.nuclei)

@pytest.mark.parametrize('operation,removed,new', [
    ('「重かった」ではなく「苦しかった」です。', 'その時の重さ', '苦しさ'),
    ('「重かった」は誤りです。', 'その時の重さ', None),
])
@continue_assertions
def test_unrelated_correction_and_withdrawal_keep_impression_and_action(operation, removed, new):
    thought = IMPRESSIONS[2]
    req = begin('誘われたのに、悲しかった。頼まれたのに、寂しかった。' + thought, ACTION)
    req = advance(advance(req, 'その時は重かった。'), operation)
    out = MeaningExperienceEngine().generate(req)
    retained_assertion(lambda: (out.artifact), 'out.artifact', lambda: (out.reason_codes))
    retained_assertion(lambda: (removed not in out.artifact.reception), 'removed not in out.artifact.reception')
    if new is not None:
        retained_assertion(lambda: (new in out.artifact.reception), 'new in out.artifact.reception')
    retained_assertion(lambda: (thought.rstrip('。') in out.artifact.reception), "thought.rstrip('。') in out.artifact.reception")
    retained_assertion(lambda: ('机を拭いた' in out.artifact.reception), "'机を拭いた' in out.artifact.reception")
    _assert_original_thought_has_required_reception_evidence(prepare_emlis_meaning(req), thought)

@pytest.mark.parametrize('answered', [False, True])
def test_independent_inverse_rejects_lost_impression_scope_and_reassigned_owner(monkeypatch, answered):
    from cocolon_meaning_experience_engine.emlis_thread_projection import project_thread_meaning
    from cocolon_meaning_experience_engine.emlis_thread_surface import realize_emlis_thread_body
    import emlis_ai_grounded_sentence_surface as surface
    import emlis_ai_grounded_human_reception as reception
    import emlis_ai_grounded_observation_gate as gate
    thought = IMPRESSIONS[2]
    req = begin(('誘われたのに、悲しかった。' if answered else '') + thought, ACTION)
    if answered:
        req = advance(req, 'その時は重かった。')
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    resolver = prepared.thread.resolver()
    projection = project_thread_meaning(prepared, plan)
    result = realize_emlis_thread_body(prepared)
    assert result.artifact
    sentence = surface.build_grounded_sentence_plan(plan, resolver, recovery_stage='full')
    def forbidden(*args, **kwargs):
        raise AssertionError('Independent inverse must not call the author again')
    monkeypatch.setattr(reception, '_author_source_grounded_reception_clauses', forbidden)
    def passes(follow):
        # Disable replay equality alone; source-bound inverse remains active.
        monkeypatch.setattr(gate, 'replay_source_grounded_human_reception_from_plan',
                            lambda *a, **kw: SimpleNamespace(text=follow))
        body = result.artifact.text.replace(result.artifact.reception, follow)
        return gate.evaluate_grounded_surface_body_inverse(body=body.encode(), plan=plan,
            sentence_plan=sentence, resolver=resolver,
            selected_subjective_input=projection.selected_reception).passed
    follow = result.artifact.reception
    assert passes(follow)
    for mutation in [follow.replace('気がする', 'と分かった'),
                     follow.replace('気がする', '気がした'),
                     follow.replace('続けられる気がする', '続けられない気がする'),
                     follow.replace('今なら少し', '友人なら少し'),
                     follow.replace('以前は止めていた練習だけど、', ''),
                     follow.replace(thought.rstrip('。'), '')]:
        assert mutation != follow
        assert not passes(mutation)
