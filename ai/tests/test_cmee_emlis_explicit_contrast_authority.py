"""An adjacent source contrast outranks a proximity detector's blocked-act label.

Public synthetic sources; no historical expectations are changed.
"""
from dataclasses import replace
import pytest
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning, build_updated_grounded_plan
from emlis_ai_grounded_observation_plan import build_grounded_observation_plan, _final_stage1_normalize_relation_authority
from test_cmee_emlis_q1_thread import initial
from test_cmee_emlis_source_owned_focus import application
from test_cmee_emlis_received_discourse import actual, inverse
from test_emlis_q3_application import qdb, qcase
from test_emlis_q2_application import run, answer

SOURCES = (
    ('作品を見てもらえてうれしかった', 'どこがよかったのかは分からない'),
    ('話を聞いてもらえてうれしかった', 'どの部分が伝わったのかは分からない'),
    ('手紙を読んでもらえてうれしかった', '何が伝わったのかは分からない'),
)


@pytest.mark.parametrize('first,second', SOURCES)
@pytest.mark.parametrize('marker', ['ただ、', 'でも、'])
def test_proximity_does_not_turn_unknown_basis_into_blocked_action(first, second, marker):
    req = application(first+'。'+marker+second+'。', '机を拭いた。')
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    relation = next(r for r in plan.relations if r.retention == 'required')
    assert relation.type == 'contrast'
    assert relation.grounding_kind == 'user_stated_relation'
    assert any(r.startswith('conflict.') for r in relation.source_relation_ids)
    out = MeaningExperienceEngine().generate(req)
    assert out.artifact is not None, out.reason_codes
    assert '止まり' not in out.artifact.observation
    assert first+'一方で、分からないのは' in out.artifact.reception
    assert second.replace('は分からない', '') in out.artifact.reception
    assert out.question is None and not out.automatic_progression


@pytest.mark.parametrize('mutation', ['field', 'direction', 'missing_marker', 'intervening_source', 'explicit_edge'])
def test_marker_authority_requires_same_field_adjacent_order_and_detector_provenance(mutation):
    first, second = SOURCES[0]
    req = initial(first+'。ただ、'+second+'。')
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    spans = tuple(prepared.thread.resolver().resolve_many(prepared.thread.resolver().span_ids))
    relation = next(r for r in plan.relations if r.retention == 'required')
    relation = replace(relation, type='attempt_and_block')
    marker = next(s for s in spans if s.detected_type == 'relation_marker')
    nuclei = plan.nuclei
    if mutation == 'field':
        spans = tuple(replace(s, source_field='memo_action') if s == marker else s for s in spans)
    elif mutation == 'direction':
        relation = replace(relation, from_nucleus_id=relation.to_nucleus_id, to_nucleus_id=relation.from_nucleus_id)
    elif mutation == 'missing_marker':
        spans = tuple(s for s in spans if s != marker)
    elif mutation == 'intervening_source':
        spans += (replace(marker, span_id='other', detected_type='event', raw_text='別の出来事'),)
    else:
        relation = replace(relation, source_relation_ids=('explicit.e1', *relation.source_relation_ids))
    assert _final_stage1_normalize_relation_authority((relation,), nuclei, spans)[0].type == 'attempt_and_block'


@pytest.mark.parametrize('old,new', [
    ('うれしかった', 'うれしくなかった'),
    ('分からないのは', '分かっているのは'),
    ('一方で、', 'そのため、'),
    ('どこがよかったのか', 'どこが悪かったのか'),
])
def test_actual_inverse_rejects_changed_feeling_unknown_cause_and_object(old, new):
    first, second = SOURCES[0]
    ctx = actual(request=initial(first+'。ただ、'+second+'。', '机を拭いた。'))
    body = ctx[0].artifact.reception
    changed = body.replace(old, new)
    assert changed != body
    assert inverse(ctx, body, without_author=True).passed
    assert not inverse(ctx, changed, without_author=True).passed


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
@pytest.mark.parametrize('first,second', SOURCES)
def test_saved_no_question_body_survives_get_and_restart(qdb, qcase, monkeypatch, tier, first, second):
    user, parent, service = qcase
    qdb.query('update public.profiles set subscription_tier=$2 where id=$1', [user, tier])
    qdb.query('update public.emotions set memo=$1,memo_action=$2 where id=$3',
        [first+'。ただ、'+second+'。', '机を拭いた。', parent])
    dto = run(service.start(user, parent))
    assert dto['current_observation'] is not None
    assert first+'一方で、分からないのは' in dto['current_observation']['text']
    assert dto['pending_question'] is None
    assert run(service.get(user, parent)) == dto
    monkeypatch.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved restart rerendered'))
    assert run(service.start(user, parent)) == dto
    assert run(service.get(user, parent)) == dto


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
@pytest.mark.parametrize('reply', ['その時は重かった。', '今は嬉しい。',
    '「嬉しくなかった」は誤りです。', 'あの時も本当は嬉しかった。書き方を間違えた。'])
def test_saved_answer_and_revision_keep_independent_contrast(qdb, qcase, monkeypatch, tier, reply):
    user, parent, service = qcase
    first, second = SOURCES[0]
    memo = '褒められたのに、嬉しくなかった。'+first+'。ただ、'+second+'。'
    qdb.query('update public.profiles set subscription_tier=$2 where id=$1', [user, tier])
    qdb.query('update public.emotions set memo=$1,memo_action=$2 where id=$3', [memo, '机を拭いた。', parent])
    before = run(service.start(user, parent))
    assert before['current_observation'] is not None and before['pending_question'] is not None
    assert run(service.get(user, parent)) == before
    after = run(answer(service, user, before, reply))
    assert after['original'] == before['original']
    assert after['answer_saved'] and after['current_observation'] is not None
    assert first in after['current_observation']['text'] and second in after['current_observation']['text']
    assert '止まり' not in after['current_observation']['text']
    assert after['question_limit'] == (3 if tier == 'premium' else 1)
    assert run(service.get(user, parent)) == after
    monkeypatch.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved restart rerendered'))
    assert run(service.start(user, parent)) == after


def test_active_plan_is_not_retyped_by_final_projection():
    first, second = SOURCES[0]
    data = dict(memo=first+'。ただ、'+second+'。', memo_action='机を拭いた。')
    before = build_grounded_observation_plan(data)
    assert any(r.type == 'attempt_and_block' for r in before.relations)
    build_updated_grounded_plan(prepare_emlis_meaning(application(data['memo'], data['memo_action'])))
    assert build_grounded_observation_plan(data) == before


@pytest.mark.parametrize('first,second', SOURCES)
@pytest.mark.parametrize('reply,clock', [
    ('その時は重かった。', 'その時'),
    ('今は嬉しい。', '回答した時点'),
    ('あの時も本当は嬉しかった。書き方を間違えた。', 'その時'),
])
def test_answer_focus_keeps_independent_original_contrast_in_reception(first, second, reply, clock):
    from test_cmee_emlis_q3_thread import advance
    req = application('褒められたのに、嬉しくなかった。'+first+'。ただ、'+second+'。', '机を拭いた。')
    updated = advance(req, reply)
    out = MeaningExperienceEngine().generate(updated)
    assert out.artifact is not None, out.reason_codes
    body = out.artifact.reception
    assert first+'一方で、' in body
    assert second.replace('は分からない', '') in body and '分からないのは' in body
    assert clock in body and '褒められたことについて' in body
    assert '机を拭いたこと' in body
    assert body.index('褒められたことについて') < body.index(first) < body.index('机を拭いたこと')
    assert updated.emlis_thread.original_source_ref == req.emlis_thread.original_source_ref


@pytest.mark.parametrize('reply', ['その時は重かった。', '今は嬉しい。'])
@pytest.mark.parametrize('change', ['feeling', 'unknown', 'relation', 'answer_time', 'action', 'drop_contrast'])
def test_updated_reception_inverse_reads_each_distinct_source_duty(reply, change):
    from test_cmee_emlis_q3_thread import advance
    first, second = SOURCES[0]
    req = application('褒められたのに、嬉しくなかった。'+first+'。ただ、'+second+'。', '机を拭いた。')
    ctx = actual(request=advance(req, reply))
    body = ctx[0].artifact.reception
    assert first in body
    replacements = {
        'feeling': ('うれしかった', 'うれしくなかった'),
        'unknown': ('分からないのは', '分かっているのは'),
        'relation': ('一方で、', 'そのため、'),
        'answer_time': (('その時', '回答した時点') if reply.startswith('その時')
                        else ('回答した時点', 'その時')),
        'action': ('机を拭いた', '机を拭かなかった'),
        'drop_contrast': (next(s+'。' for s in body.split('。') if first in s), ''),
    }
    old, new = replacements[change]
    mutated = body.replace(old, new)
    assert mutated != body
    assert inverse(ctx, body, without_author=True).passed
    assert not inverse(ctx, mutated, without_author=True).passed


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
@pytest.mark.parametrize('reply', ['その時は重かった。', '今は嬉しい。',
    'あの時も本当は嬉しかった。書き方を間違えた。'])
def test_saved_updated_reception_retains_original_relation(qdb, qcase, monkeypatch, tier, reply):
    user, parent, service = qcase
    first, second = SOURCES[0]
    memo = '褒められたのに、嬉しくなかった。'+first+'。ただ、'+second+'。'
    qdb.query('update public.profiles set subscription_tier=$2 where id=$1', [user, tier])
    qdb.query('update public.emotions set memo=$1,memo_action=$2 where id=$3', [memo, '机を拭いた。', parent])
    before = run(service.start(user, parent))
    after = run(answer(service, user, before, reply))
    assert after['answer_saved'] and after['current_observation'] is not None
    body = after['current_observation']['text'].split('Emlisから：', 1)[1]
    assert first+'一方で、' in body
    assert second.replace('は分からない', '') in body and '分からないのは' in body
    assert '褒められたことについて' in body and '机を拭いたこと' in body
    assert after['original'] == before['original']
    assert run(service.get(user, parent)) == after
    monkeypatch.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved restart rerendered'))
    assert run(service.start(user, parent)) == after
