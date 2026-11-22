"""Admitted polite feelings retain source meaning after event withdrawal."""
import pytest
from dataclasses import replace
import emlis_ai_grounded_human_reception as reception
import emlis_ai_grounded_observation_gate as gate
from test_cmee_emlis_received_discourse import actual, inverse
from test_cmee_emlis_q3_thread import begin, advance
from test_cmee_emlis_detached_feeling_discourse import WITHDRAW
from test_emlis_q3_application import qdb, qcase, cont
from test_emlis_q2_application import run, answer


@pytest.mark.parametrize('answer_text,finite', [
    ('その時は重かったです。', 'その時は重かった'),
    ('その時は怖くなかったです。', 'その時は怖くなかった'),
    ('今は苦しいです。', '回答した時点では苦しい'),
    ('今は怖くないです。', '回答した時点では怖くない'),
    ('今は嬉しいです。', '回答した時点では嬉しい'),
])
def test_complete_polite_feeling_is_finite_and_independently_readable(answer_text, finite):
    context = actual(request=advance(advance(begin(), answer_text), WITHDRAW))
    follow = context[0].artifact.reception
    assert finite + 'のですね。' in follow
    assert 'ですこと' not in follow and '受け止めています' not in follow
    assert '褒められた' not in context[0].artifact.text
    assert 'その時は嬉しくなかった' in follow
    assert inverse(context, follow, without_author=True).passed


@pytest.fixture(scope='module')
def polite_context():
    return actual(request=advance(advance(begin(), 'その時は重かったです。'), WITHDRAW))


@pytest.mark.parametrize('old,new', [
    ('重かった', '重い'), ('重かった', '軽かった'),
    ('重かった', '重くなかった'), ('その時は重かった', '回答した時点では重かった'),
    ('し、その時は重かった', ''), ('し、', 'ので、'),
    ('重かった', '私が重かった'), ('重かった', '友人が重かった'),
])
def test_mutation_rejects_actual_meaning_change_without_author(polite_context, old, new):
    follow = polite_context[0].artifact.reception
    changed = follow.replace(old, new, 1)
    assert changed != follow
    assert not inverse(polite_context, changed, without_author=True).passed


@pytest.mark.parametrize('ending', ['のです。', 'のだと受け取りました。'])
def test_equivalent_ending_keeps_source_proof(polite_context, ending):
    follow = polite_context[0].artifact.reception.replace('のですね。', ending)
    assert inverse(polite_context, follow).passed


def test_inverse_restores_full_polite_source_bytes(polite_context):
    result, plan, _, resolver, selected = polite_context
    moves = reception.reception_active_moves(plan.response_plan.human_reception_plan, 'full')[:2]
    raw = result.artifact.reception.split('。')[0] + '。'
    proof = gate.read_detached_feeling_pair(raw, moves, plan, resolver, selected)
    assert proof is not None
    start, end, source = proof[1][0]
    assert raw.encode()[start:end].decode() == '重かった'
    assert source.decode() == '重かったです'


def test_missing_source_range_is_rejected_without_an_exception(polite_context):
    result, plan, _, resolver, selected = polite_context
    moves = reception.reception_active_moves(plan.response_plan.human_reception_plan, 'full')[:2]
    target = moves[1].target_nucleus_ids[0]
    changed = replace(plan, nuclei=tuple(replace(n, semantic_frame=replace(n.semantic_frame,
        attribute_codes=tuple(c for c in n.semantic_frame.attribute_codes
                              if not c.startswith('source_fragment_scalar_range:'))))
        if n.nucleus_id == target else n for n in plan.nuclei))
    raw = result.artifact.reception.split('。')[0] + '。'
    assert gate.read_detached_feeling_pair(raw, moves, changed, resolver, selected) is None


def test_revised_polite_answer_retains_prior_answer_time():
    request = advance(advance(begin(), '今は重いです。'), WITHDRAW)
    context = actual(request=advance(request, '「重いです」ではなく「苦しいです」です。'))
    follow = context[0].artifact.reception
    assert '先の回答時点では苦しいのですね。' in follow
    assert '重い' not in follow and '褒められた' not in context[0].artifact.text
    assert inverse(context, follow, without_author=True).passed



@pytest.mark.parametrize('text', ['その時は重かったです。', '今は怖くないです。'])
def test_polite_withdrawal_saved_body_survives_get_and_restart(qcase, qdb, text, monkeypatch):
    user, parent, service = qcase
    first = run(service.start(user, parent))
    current = run(answer(service, user, first, text))
    current = run(cont(service, user, current, 'continue-polite'))
    current = run(answer(service, user, current, WITHDRAW, 'withdraw-polite'))
    body = current['current_observation']['text']
    assert 'ですこと' not in body and '受け止めています' not in body
    assert '褒められた' not in body and current['original'] == first['original']
    monkeypatch.setattr(service.engine, 'generate', lambda *_: pytest.fail('GET must not render'))
    assert run(service.get(user, parent)) == current
    assert run(service.start(user, parent)) == current
