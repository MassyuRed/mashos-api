"""Admitted answer clauses retain meaning when placed before a nominal head."""
import pytest
from test_cmee_emlis_received_discourse import actual, inverse
from test_cmee_emlis_q3_thread import begin, advance, MEMO
from test_emlis_q3_application import qdb, qcase, cont
from test_emlis_q2_application import run, answer


@pytest.mark.parametrize('reply,clause', [
    ('その時は重かったです。', 'その時に重かったこと'),
    ('今は怖くないです。', '回答した時点で怖くないこと'),
    ('その時は私は怖くなかったです。', 'その時にあなたは怖くなかったこと'),
    ('その時は少し重かったです。', 'その時に少し重かったこと'),
])
def test_admitted_finite_answer_is_attributive_without_losing_source(reply, clause):
    initial = begin()
    request = advance(initial, reply)
    context = actual(request=request)
    follow = context[0].artifact.reception
    assert clause in follow
    assert 'ですこと' not in follow
    assert inverse(context, follow, without_author=True).passed
    assert request.current_input_bundle == initial.current_input_bundle


@pytest.fixture(scope='module')
def attributed():
    return actual(request=advance(begin(), 'その時は私は怖くなかったです。'))


@pytest.mark.parametrize('old,new', [
    ('怖くなかった', '怖かった'), ('怖くなかった', '怖くない'),
    ('あなたは', '私は'), ('あなたは', '友人は'), ('あなたは', 'あなたも'),
    ('その時にあなたは', '回答した時点であなたは'),
    ('あなたは怖くなかったこと', '怖くなかったこと'),
    ('あなたは怖くなかったこと', 'あなたは怖かったこと'),
    ('その時にあなたは怖くなかったこと', '「その時にあなたは怖くなかったこと」'),
])
def test_changed_meaning_is_rejected_without_author(attributed, old, new):
    follow = attributed[0].artifact.reception
    changed = follow.replace(old, new, 1)
    assert changed != follow
    assert not inverse(attributed, changed, without_author=True).passed


def test_degree_is_not_lost_in_attributive_clause():
    context = actual(request=advance(begin(), 'その時は少し重かったです。'))
    follow = context[0].artifact.reception
    assert '少し重かったこと' in follow
    assert not inverse(context, follow.replace('少し重かったこと', '重かったこと'),
                       without_author=True).passed


def test_revision_keeps_prior_answer_time_and_replaces_full_predicate():
    request = advance(advance(begin(), '今は私は重いです。'),
                      '「私は重いです」ではなく「私は苦しいです」です。')
    context = actual(request=request)
    follow = context[0].artifact.reception
    assert '先の回答時点であなたは苦しいこと' in follow
    assert '重い' not in follow and 'ですこと' not in follow
    assert inverse(context, follow, without_author=True).passed


def test_answer_only_group_preserves_both_event_and_time_bindings():
    request = advance(advance(begin(MEMO.replace('寂しかった', '今は寂しい')),
                              'その時は重かったです。'), 'その時は怖くなかったです。')
    context = actual(request=request)
    follow = context[0].artifact.reception
    assert 'その時に重かったこと' in follow
    assert 'その時に怖くなかったこと' in follow
    assert inverse(context, follow, without_author=True).passed
    swapped = follow.replace('褒められた', 'TEMP').replace('誘われた', '褒められた').replace('TEMP', '誘われた')
    assert swapped != follow
    assert not inverse(context, swapped, without_author=True).passed


@pytest.mark.parametrize('reply', ['その時は重かったです。', '今は怖くないです。',
                                 'その時は私は怖くなかったです。'])
def test_saved_attributive_body_and_withdrawal_survive_authorless_reads(qcase, qdb, monkeypatch, reply):
    user, parent, service = qcase
    first = run(service.start(user, parent))
    current = run(answer(service, user, first, reply))
    assert current['current_observation'] is not None
    assert 'ですこと' not in current['current_observation']['text']
    with monkeypatch.context() as read:
        read.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved read rendered'))
        assert run(service.get(user, parent)) == current
        assert run(service.start(user, parent)) == current
    current = run(cont(service, user, current, 'continue-attributive'))
    current = run(answer(service, user, current, '「褒められた」は誤りです。', 'withdraw-attributive'))
    assert current['current_observation'] is not None
    assert '褒められた' not in current['current_observation']['text']
    assert current['original'] == first['original']
    monkeypatch.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved read rendered'))
    assert run(service.get(user, parent)) == current
    assert run(service.start(user, parent)) == current
