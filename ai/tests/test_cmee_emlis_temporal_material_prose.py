"""Finite reception keeps recalled time, conditional relief and open cause.

These public grammar examples retain existing admission and selection. Actual
body mutations are checked independently while the forward author is disabled.
"""
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from test_cmee_emlis_q3_thread import TEMPORAL_MEMOS, _current_material_with_requested_focus
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.emlis_answer_update import (
    prepare_emlis_meaning, build_updated_grounded_plan,
)
from cocolon_meaning_experience_engine.emlis_thread_projection import project_thread_meaning
from cocolon_meaning_experience_engine.emlis_thread_surface import realize_emlis_thread_body
from emlis_ai_grounded_observation_gate import evaluate_grounded_surface_body_inverse
import emlis_ai_grounded_observation_plan as observation_plan
import emlis_ai_grounded_sentence_surface as surface
from test_emlis_q3_application import qdb, qcase
from test_emlis_q2_application import run


def _context(monkeypatch, memo=TEMPORAL_MEMOS[2], focus=0, q3=True, action='お茶を飲んだ。'):
    request = _current_material_with_requested_focus(monkeypatch, memo, action, q3, focus)
    prepared = prepare_emlis_meaning(request)
    plan = build_updated_grounded_plan(prepared)
    result = realize_emlis_thread_body(prepared)
    assert result.artifact is not None, result.reason_codes
    selected = project_thread_meaning(prepared, plan).selected_reception
    resolver = prepared.thread.resolver()
    sentence = surface.build_grounded_sentence_plan(plan, resolver)
    return request, result, plan, resolver, sentence, selected


def _read(context, follow, plan_override=None):
    _, result, plan, resolver, sentence, selected = context
    with patch('emlis_ai_grounded_human_reception._author_source_grounded_reception_clauses',
               side_effect=AssertionError('author must not run')), patch(
            'emlis_ai_grounded_human_reception._source_grounded_reception_fragment',
            side_effect=AssertionError('author must not run')), patch(
            'emlis_ai_grounded_observation_gate.replay_source_grounded_human_reception_from_plan',
            return_value=SimpleNamespace(text=follow)):
        return evaluate_grounded_surface_body_inverse(
            body=result.artifact.text.replace(result.artifact.reception, follow).encode(),
            plan=plan_override or plan, resolver=resolver, sentence_plan=sentence,
            selected_subjective_input=selected)


CASES = [
    (TEMPORAL_MEMOS[0], True, ''),
    (TEMPORAL_MEMOS[0], False, 'お茶を飲んだ。'),
    (TEMPORAL_MEMOS[1], True, 'お茶を飲んだ。'),
    (TEMPORAL_MEMOS[1], False, ''),
    (TEMPORAL_MEMOS[2], True, 'お茶を飲んだ。'),
    (TEMPORAL_MEMOS[2], False, ''),
]


@pytest.mark.parametrize('memo,q3,action', CASES)
@pytest.mark.parametrize('focus', [0, 1])
def test_temporal_prose_keeps_both_hosts_focus_and_initial_admission(
        monkeypatch, memo, q3, action, focus):
    context = _context(monkeypatch, memo, focus, q3, action)
    request, result, plan, resolver, _, selected = context
    group = observation_plan._source_temporal_material_group(plan.nuclei, plan.relations)
    current, unknown = group[:2]
    assert (current.kind, current.semantic_frame.modality, current.semantic_frame.polarity) == ('change', 'fact', 'mixed')
    assert (unknown.kind, unknown.semantic_frame.modality, unknown.semantic_frame.polarity) == ('uncertainty', 'uncertain', 'negative')
    assert plan.response_plan.human_reception_plan.moves[0].target_nucleus_ids == (group[focus].nucleus_id,)
    current_text, unknown_text = [resolver.resolve(n.source_span_ids[0]).raw_text for n in group[:2]]
    normalized_current = current_text.replace('残っています', '残っている')
    expected = (normalized_current[:-1] + 'て、' + unknown_text if focus == 0 else
                unknown_text[:-2] + 'ず、' + normalized_current) + 'のですね。'
    assert result.artifact.reception.startswith(expected)
    assert result.artifact.reception.count(expected) == 1
    assert ('お茶を飲んだことを大切に思っています。' in result.artifact.reception) == bool(action)
    contributions = [set(d.selected_contribution_refs) for d in selected.decisions]
    assert len(contributions) == 1 + bool(action) and all(contributions)
    if action:
        assert not contributions[0] & contributions[1]
    assert _read(context, result.artifact.reception).passed
    engine = MeaningExperienceEngine()
    checkpoint = engine.prepare_emlis_update(request)
    actual = engine.generate(replace(request, emlis_thread=replace(
        request.emlis_thread, prepared_meaning_checkpoint_ref=checkpoint.checkpoint_id)))
    if not q3 and memo != TEMPORAL_MEMOS[1]:
        assert actual.artifact is None and actual.body_state == 'UNAVAILABLE'
        assert actual.reason_codes == ('current_experiencer_or_time_scope_unsupported',)
    else:
        assert actual.artifact is not None, actual.reason_codes
        assert actual.artifact.reception == result.artifact.reception
        assert actual.question is None and actual.body_state == 'FINAL'


MUTATIONS = [
    ('以前に疲れがあった時', '現在も疲れている時'),
    ('思い出した', '想像した'),
    ('今の原因', '昨日の原因'),
    ('今の原因', '友達の原因'),
    ('原因が同じかは', '原因は'),
    ('横になると', '横になったから'),
    ('軽くなり', '軽くならず'),
    ('なお疲れも', 'もう疲れは'),
    ('疲れも', '痛みも'),
    ('お茶を飲んだ', 'お茶を飲まなかった'),
]


@pytest.mark.parametrize('focus', [0, 1])
@pytest.mark.parametrize('old,new', MUTATIONS)
def test_actual_temporal_scope_mutation_is_rejected_without_author(monkeypatch, focus, old, new):
    context = _context(monkeypatch, focus=focus)
    original = context[1].artifact.reception
    changed = original.replace(old, new, 1)
    assert changed != original
    assert not _read(context, changed).passed


@pytest.mark.parametrize('focus', [0, 1])
def test_temporal_polarity_deletion_duplication_and_order_are_rejected(monkeypatch, focus):
    context = _context(monkeypatch, focus=focus)
    original = context[1].artifact.reception
    reception, action, _ = original.split('。')
    unknown = 'わからない' if focus == 0 else 'わからず'
    residue = '残っていて' if focus == 0 else '残っている'
    changed = [
        original.replace(unknown, 'わかる' if focus == 0 else 'わかり', 1),
        original.replace(residue, '残っていた', 1),
        action + '。',
        reception + '。' + reception + '。' + action + '。',
        action + '。' + reception + '。',
        original.replace('横になると', '', 1),
        original.replace('今の原因が同じかは', '今の原因が同じなので', 1),
    ]
    for follow in changed:
        assert follow != original
        assert not _read(context, follow).passed


def test_temporal_degree_and_limited_unknown_cannot_be_strengthened(monkeypatch):
    context = _context(monkeypatch, memo=TEMPORAL_MEMOS[1])
    original = context[1].artifact.reception
    for old, new in [('少し楽', 'すっかり楽'), ('同じかもまだ分からない', '何も分からない')]:
        changed = original.replace(old, new, 1)
        assert changed != original
        assert not _read(context, changed).passed


@pytest.mark.parametrize('ending', ['のです。', 'のだと受け取りました。'])
def test_equivalent_temporal_acknowledgement_is_read_without_author(monkeypatch, ending):
    context = _context(monkeypatch)
    assert _read(context, context[1].artifact.reception.replace('のですね。', ending, 1)).passed


@pytest.mark.parametrize('slot,field,value', [
    (0, 'actor', 'other_person'), (0, 'time_scope', 'past'),
    (0, 'polarity', 'positive'), (1, 'modality', 'fact'), (1, 'polarity', 'positive'),
])
def test_valid_temporal_body_cannot_override_changed_source_frame(monkeypatch, slot, field, value):
    context = _context(monkeypatch)
    plan = context[2]
    group = observation_plan._source_temporal_material_group(plan.nuclei, plan.relations)
    changed = replace(plan, nuclei=tuple(replace(n, semantic_frame=replace(
        n.semantic_frame, **{field: value})) if n.nucleus_id == group[slot].nucleus_id else n
        for n in plan.nuclei))
    assert not _read(context, context[1].artifact.reception, changed).passed


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
def test_temporal_prose_survives_saved_get_and_restart(qcase, qdb, tier, monkeypatch):
    user, parent, service = qcase
    assert 'code' not in qdb.query('update public.profiles set subscription_tier=$1 where id=$2', [tier, user])
    assert 'code' not in qdb.query('update public.emotions set memo=$1,memo_action=$2 where id=$3',
                                [TEMPORAL_MEMOS[2], 'お茶を飲んだ。', parent])
    current = run(service.start(user, parent))
    assert current['state'] == 'COMPLETED' and current['body_state'] == 'FINAL'
    assert current['pending_question'] is None and current['issued_count'] == 0
    assert current['question_limit'] == (3 if tier == 'premium' else 1)
    follow = current['current_observation']['text'].split('Emlisから：', 1)[1].strip()
    assert '現在は横になると軽くなり、なお疲れも残っていて、' in follow
    assert '以前に疲れがあった時を思い出したけど、今の原因が同じかはわからないのですね。' in follow
    assert 'お茶を飲んだことを大切に思っています。' in follow
    assert current['original']['memo'] == TEMPORAL_MEMOS[2]
    assert run(service.get(user, parent)) == current
    monkeypatch.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved read must not rerender'))
    assert run(service.get(user, parent)) == current
    assert run(service.start(user, parent)) == current
