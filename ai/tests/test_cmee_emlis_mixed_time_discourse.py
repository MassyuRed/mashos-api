"""Independent events keep finite past/current scopes in the shared reception."""
import pytest

from test_cmee_emlis_received_discourse import actual, inverse
from test_cmee_emlis_q3_thread import begin, advance, MEMO
from test_emlis_q3_application import qdb, qcase
from test_emlis_q2_application import run, answer


def mixed(position=1, current='今は怖くない。'):
    request = begin()
    for index in range(3):
        request = advance(request, current if index == position else 'その時は重かった。')
    return actual(request=request)


@pytest.mark.parametrize('position', [0, 1, 2])
@pytest.mark.parametrize('current,source', [
    ('今は怖い。', '怖い'), ('今は怖くない。', '怖くない'),
    ('今は重い。', '重い'),
])
def test_each_event_retains_its_own_finite_time_and_order(position, current, source):
    context = mixed(position, current)
    follow = context[0].artifact.reception
    events = ('褒められた', '誘われた', '頼まれた')
    reactions = ('嬉しくなく', '悲しく', '寂しく')
    parts = follow.removesuffix('のですね。').split('し、')
    assert len(parts) == 3
    for i, part in enumerate(parts):
        expected = ('回答した時点では' + source if i == position else '重かった')
        assert part == events[i] + '時は' + reactions[i] + '、' + expected
        assert follow.count(events[i]) == 1
    assert 'ことと' not in follow and '受け止めています' not in follow
    assert inverse(context, follow, without_author=True).passed


@pytest.mark.parametrize('old,new', [
    ('怖くないし、', '怖くなかったし、'), ('怖くないし、', '怖いし、'),
    ('回答した時点では', 'その時は'), ('回答した時点では', '先の回答時点では'),
    ('回答した時点では', ''), ('回答した時点では', '回答した時点では友人は'),
    ('嬉しくなく、', ''), ('悲しく、', '悲しくなく、'),
    ('重かったし、', '重いし、'), ('し、誘われた', 'ので、誘われた'),
    ('し、頼まれた', 'し、そのため頼まれた'),
])
def test_actual_changed_meaning_is_rejected_without_author(old, new):
    context = mixed()
    follow = context[0].artifact.reception
    changed = follow.replace(old, new)
    assert changed != follow
    assert not inverse(context, changed, without_author=True).passed


def test_swapping_complete_answers_between_events_is_not_accepted():
    context = mixed()
    follow = context[0].artifact.reception
    changed = follow.replace('重かったし、', 'SWAPし、', 1).replace(
        '回答した時点では怖くないし、', '重かったし、', 1).replace(
        'SWAPし、', '回答した時点では怖くないし、', 1)
    assert changed != follow
    assert not inverse(context, changed, without_author=True).passed


def test_prior_answer_correction_keeps_originals_and_other_event():
    request = advance(begin('褒められたのに、嬉しくなかった。誘われたのに、悲しかった。'), '今は重い。')
    context = actual(request=advance(request, '「重い」ではなく「苦しい」です。'))
    follow = context[0].artifact.reception
    assert '褒められた時は嬉しくなく、先の回答時点では苦しいし、' in follow
    assert '誘われたのに、悲しさを感じたのですね。' in follow
    assert '重い' not in follow
    assert inverse(context, follow, without_author=True).passed
    assert not inverse(context, follow.replace('先の回答時点では', '回答した時点では'), without_author=True).passed


def test_separate_current_answers_do_not_acquire_a_later_past_tense():
    request = begin()
    for text in ('今は怖い。', '今は重い。', 'その時は苦しかった。'):
        request = advance(request, text)
    context = actual(request=request)
    follow = context[0].artifact.reception
    assert '回答した時点では怖いし、' in follow
    assert '回答した時点では重いし、' in follow
    assert follow.endswith('頼まれた時は寂しく、苦しかったのですね。')
    assert inverse(context, follow, without_author=True).passed


@pytest.mark.parametrize('ending', ['のです。', 'のだと受け取りました。'])
def test_valid_acknowledgement_does_not_depend_on_author_spelling(ending):
    context = mixed()
    follow = context[0].artifact.reception.replace('のですね。', ending)
    assert inverse(context, follow).passed


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
def test_mixed_time_body_survives_saved_get_and_no_author_restart(qcase, qdb, tier, monkeypatch):
    user, parent, service = qcase
    qdb.query('update public.profiles set subscription_tier=$1 where id=$2', [tier, user])
    qdb.query('update public.emotions set memo=$1 where id=$2', [MEMO, parent])
    first = run(service.start(user, parent))
    current = run(answer(service, user, first, '今は怖くない。'))
    assert current['current_observation'] is not None
    follow = current['current_observation']['text'].split('Emlisから：', 1)[1]
    assert '褒められた時は嬉しくなく、回答した時点では怖くないし、' in follow
    assert '誘われたのに、悲しさを感じたし、頼まれたのに、寂しさを感じたのですね。' in follow
    assert current['original'] == first['original']
    monkeypatch.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved GET must not render'))
    assert run(service.get(user, parent)) == current
    assert run(service.start(user, parent)) == current
