"""Recipient perspective for source-owned feelings after event withdrawal."""
from dataclasses import replace
import pytest
import emlis_ai_grounded_human_reception as reception
import emlis_ai_grounded_observation_gate as gate
from test_cmee_emlis_received_discourse import actual, inverse
from test_cmee_emlis_q3_thread import begin, advance
from test_cmee_emlis_detached_feeling_discourse import WITHDRAW
from test_emlis_q3_application import qdb, qcase, cont
from test_emlis_q2_application import run, answer


@pytest.mark.parametrize('text,finite', [
    ('その時は私は重かった。', 'その時、あなたは重かった'),
    ('その時は私は怖くなかったです。', 'その時、あなたは怖くなかった'),
    ('今は私は苦しいです。', '回答した時点で、あなたは苦しい'),
    ('今は私も怖くない。', '回答した時点で、あなたも怖くない'),
    ('今は自分は嬉しい。', '回答した時点で、あなたは嬉しい'),
    ('今は私には重い。', '回答した時点で、あなたには重い'),
])
def test_complete_self_source_keeps_particle_time_and_polarity(text, finite):
    context = actual(request=advance(advance(begin(), text), WITHDRAW))
    follow = context[0].artifact.reception
    assert finite + 'のですね。' in follow
    assert 'ですこと' not in follow and '受け止めています' not in follow
    assert '褒められた' not in context[0].artifact.text
    assert 'その時は嬉しくなかった' in follow
    assert inverse(context, follow, without_author=True).passed


@pytest.fixture(scope='module')
def self_context():
    return actual(request=advance(advance(begin(), '今は私も怖くないです。'), WITHDRAW))


@pytest.mark.parametrize('old,new', [
    ('あなたも', '私も'), ('あなたも', '友人も'), ('あなたも', 'あなたは'),
    ('あなたも', ''), ('怖くない', '怖い'), ('怖くない', '怖くなかった'),
    ('回答した時点で、', 'その時、'), ('回答した時点で、', ''),
    ('し、', 'ので、'), ('し、', 'のに、'),
    ('し、回答した時点で、あなたも怖くない', ''),
])
def test_complete_meaning_mutations_fail_without_author(self_context, old, new):
    follow = self_context[0].artifact.reception
    mutated = follow.replace(old, new, 1)
    assert mutated != follow
    assert not inverse(self_context, mutated, without_author=True).passed


def test_inverse_restores_original_pronoun_particle_and_polite_bytes(self_context):
    result, plan, _, resolver, selected = self_context
    moves = reception.reception_active_moves(plan.response_plan.human_reception_plan, 'full')[:2]
    clause = result.artifact.reception.split('。')[0] + '。'
    proof = gate.read_detached_feeling_pair(clause, moves, plan, resolver, selected)
    assert proof is not None
    start, end, source = proof[1][0]
    assert clause.encode()[start:end].decode() == 'あなたも怖くない'
    assert source.decode() == '私も怖くないです'


def test_dative_topic_cannot_become_additive():
    context = actual(request=advance(advance(begin(), '今は私には重い。'), WITHDRAW))
    follow = context[0].artifact.reception
    assert 'あなたには' in follow
    assert not inverse(context, follow.replace('あなたには', 'あなたにも'), without_author=True).passed


def test_unsupported_answer_is_not_admitted_by_surface_change():
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    result = MeaningExperienceEngine().generate(advance(begin(), '今は私にも重い。'))
    assert result.artifact is None
    assert 'answer_syntax_unsupported' in result.reason_codes


@pytest.mark.parametrize('field,value', [('actor', 'other_person'), ('polarity', 'positive')])
def test_source_owner_and_polarity_remain_required(self_context, field, value):
    result, plan, _, resolver, selected = self_context
    moves = reception.reception_active_moves(plan.response_plan.human_reception_plan, 'full')[:2]
    target = moves[1].target_nucleus_ids[0]
    changed = replace(plan, nuclei=tuple(replace(n, semantic_frame=replace(n.semantic_frame, **{field:value}))
                      if n.nucleus_id == target else n for n in plan.nuclei))
    clause = result.artifact.reception.split('。')[0] + '。'
    assert gate.read_detached_feeling_pair(clause, moves, changed, resolver, selected) is None


@pytest.mark.parametrize('ending', ['のです。', 'のだと受け取りました。'])
def test_equivalent_ending_is_readable(self_context, ending):
    assert inverse(self_context, self_context[0].artifact.reception.replace('のですね。', ending)).passed


def test_prior_answer_revision_retains_person_and_earlier_time():
    request = advance(advance(begin(), '今は私は重いです。'), WITHDRAW)
    context = actual(request=advance(request, '「私は重いです」ではなく「私は苦しいです」です。'))
    follow = context[0].artifact.reception
    assert '先の回答時点で、あなたは苦しいのですね。' in follow
    assert '重い' not in follow and '褒められた' not in context[0].artifact.text
    assert inverse(context, follow, without_author=True).passed


def test_ambiguous_ga_keeps_existing_realization():
    context = actual(request=advance(advance(begin(), '今は私が怖い。'), WITHDRAW))
    assert 'あなたが怖い' not in context[0].artifact.reception
    assert inverse(context, context[0].artifact.reception, without_author=True).passed


@pytest.mark.parametrize('text', ['今は私は苦しいです。', '今は私も怖くない。'])
def test_persisted_recipient_perspective_is_not_rerendered(qcase, qdb, text, monkeypatch):
    user, parent, service = qcase
    first = run(service.start(user, parent))
    current = run(answer(service, user, first, text))
    current = run(cont(service, user, current, 'continue-self'))
    current = run(answer(service, user, current, WITHDRAW, 'withdraw-self'))
    follow = current['current_observation']['text'].split('Emlisから：', 1)[1]
    assert 'あなた' in follow and '私' not in follow and '受け止めています' not in follow
    assert current['original'] == first['original']
    monkeypatch.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved read must not generate'))
    assert run(service.get(user, parent)) == current
    assert run(service.start(user, parent)) == current
