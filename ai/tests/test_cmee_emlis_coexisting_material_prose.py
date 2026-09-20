"""Source-owned coexisting feelings and tentative targets in finite prose.

Inputs extend existing public Q3 examples. The historical wording assertions
remain unchanged; these checks exercise the current meaning and real mutations.
"""
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from test_cmee_emlis_q3_thread import _current_material_with_requested_focus
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.emlis_answer_update import (
    prepare_emlis_meaning, build_updated_grounded_plan,
)
from cocolon_meaning_experience_engine.emlis_thread_projection import project_thread_meaning
from cocolon_meaning_experience_engine.emlis_thread_surface import realize_emlis_thread_body
from emlis_ai_grounded_observation_gate import evaluate_grounded_surface_body_inverse
import emlis_ai_grounded_sentence_surface as surface
from test_emlis_q3_application import qdb, qcase
from test_emlis_q2_application import run


MEMOS = (
    '嬉しい感じと怖い感じが同時にある。対象は一つではない気がする。',
    '理由はうまく説明できないけれど、嬉しい感じと緊張する感じが同時にある。対象も一つではない気がする。',
    '現在も、怖い感じと安心した感じがどちらもある。今は、対象は一つではない気がする。',
)


def _context(monkeypatch, memo=MEMOS[1], focus=0, q3=True, action='お茶を飲んだ。'):
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


@pytest.mark.parametrize('memo', MEMOS)
@pytest.mark.parametrize('focus', [0, 1])
@pytest.mark.parametrize('q3', [False, True])
@pytest.mark.parametrize('action', ['', 'お茶を飲んだ。'])
def test_finite_prose_preserves_focus_complete_hosts_and_independent_action(
        monkeypatch, memo, focus, q3, action):
    context = _context(monkeypatch, memo, focus, q3, action)
    request, result, plan, *_ = context
    first, second = memo.rstrip('。').split('。')
    expected = (first[:-1] + 'り、' + second if focus == 0
                else second[:-2] + 'して、' + first) + 'のですね。'
    assert result.artifact.reception.startswith(expected)
    assert result.artifact.reception.count(expected) == 1
    assert ('お茶を飲んだことを大切に思っています。' in result.artifact.reception) == bool(action)
    assert plan.response_plan.human_reception_plan.moves[0].target_nucleus_ids == (f'nucleus:s{focus+1}',)
    assert _read(context, result.artifact.reception).passed
    engine = MeaningExperienceEngine()
    checkpoint = engine.prepare_emlis_update(request)
    actual = engine.generate(replace(request, emlis_thread=replace(
        request.emlis_thread, prepared_meaning_checkpoint_ref=checkpoint.checkpoint_id)))
    if not q3 and memo == MEMOS[2]:
        # The initial source admission already excludes this experiencer/time
        # scope; finite prose does not expand that existing source contract.
        assert actual.artifact is None
        assert actual.reason_codes == ('current_experiencer_or_time_scope_unsupported',)
        return
    assert actual.artifact is not None, actual.reason_codes
    assert actual.artifact.reception == result.artifact.reception
    assert actual.question is None and actual.body_state == 'FINAL'


MUTATIONS = [
    ('嬉しい感じと', ''),
    ('嬉しい感じと緊張する感じ', '緊張する感じと嬉しい感じ'),
    ('嬉しい感じ', '寂しい感じ'),
    ('説明できない', '説明できる'),
    ('理由は', '友達の理由は'),
    ('同時に', '以前は'),
    ('対象も', '理由も'),
    ('一つではない', '一つである'),
    ('気がする', '確信する'),
    ('気がして', '確信して'),
    ('あり、', 'あるから、'),
    ('して、', 'したので、'),
    ('お茶を飲んだ', 'お茶を飲まなかった'),
]


@pytest.mark.parametrize('focus,old,new', [
    (focus, old, new) for focus in (0, 1) for old, new in MUTATIONS
    if not ((focus == 0 and old in {'気がして', 'して、'})
            or (focus == 1 and old in {'気がする', 'あり、'}))
])
def test_actual_mutations_are_rejected_without_author(monkeypatch, focus, old, new):
    context = _context(monkeypatch, focus=focus)
    original = context[1].artifact.reception
    changed = original.replace(old, new, 1)
    assert changed != original
    assert not _read(context, changed).passed


@pytest.mark.parametrize('focus', [0, 1])
def test_complete_clause_removal_swap_and_duplication_are_rejected(monkeypatch, focus):
    context = _context(monkeypatch, focus=focus)
    original = context[1].artifact.reception
    first, action, _ = original.split('。')
    changed = [action + '。', first + '。' + first + '。' + action + '。',
               action + '。' + first + '。',
               original.replace('対象も一つではない', '対象も一つではないことが原因で嬉しく、対象も一つではない')]
    for follow in changed:
        assert follow != original
        assert not _read(context, follow).passed


@pytest.mark.parametrize('ending', ['のです。', 'のだと受け取りました。'])
def test_reader_accepts_equivalent_acknowledgement_without_author(monkeypatch, ending):
    context = _context(monkeypatch)
    follow = context[1].artifact.reception.replace('のですね。', ending, 1)
    assert _read(context, follow).passed


@pytest.mark.parametrize('field,value', [('actor', 'other_person'), ('time_scope', 'past'),
                                       ('modality', 'fact'), ('polarity', 'positive')])
def test_valid_body_cannot_override_changed_source_scope(monkeypatch, field, value):
    context = _context(monkeypatch)
    plan = context[2]
    changed = replace(plan, nuclei=tuple(replace(n, semantic_frame=replace(
        n.semantic_frame, **{field: value})) if n.nucleus_id == 'nucleus:s2' else n
        for n in plan.nuclei))
    assert not _read(context, context[1].artifact.reception, changed).passed


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
def test_finite_reception_survives_saved_get_and_restart(qcase, qdb, tier, monkeypatch):
    user, parent, service = qcase
    assert 'code' not in qdb.query('update public.profiles set subscription_tier=$1 where id=$2', [tier, user])
    assert 'code' not in qdb.query('update public.emotions set memo=$1,memo_action=$2 where id=$3',
                                [MEMOS[1], 'お茶を飲んだ。', parent])
    current = run(service.start(user, parent))
    assert current['state'] == 'COMPLETED' and current['body_state'] == 'FINAL'
    assert current['pending_question'] is None and current['issued_count'] == 0
    assert current['question_limit'] == (3 if tier == 'premium' else 1)
    follow = current['current_observation']['text'].split('Emlisから：', 1)[1].strip()
    assert '同時にあり、対象も一つではない気がするのですね。' in follow
    assert 'お茶を飲んだことを大切に思っています。' in follow
    assert current['original']['memo'] == MEMOS[1]
    assert run(service.get(user, parent)) == current
    monkeypatch.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved read must not rerender'))
    assert run(service.get(user, parent)) == current
    assert run(service.start(user, parent)) == current
