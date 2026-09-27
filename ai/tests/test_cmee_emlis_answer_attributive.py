"""Admitted answers retain meaning in finite prose and remaining nominal paths."""
import pytest
from test_cmee_emlis_received_discourse import actual, inverse
from test_cmee_emlis_q3_thread import begin, advance, MEMO
from test_emlis_q3_application import qdb, qcase, cont
from test_emlis_q2_application import run, answer


@pytest.mark.parametrize('reply,clause', [
    ('その時は重かったです。', '褒められた時は嬉しくなく、重く'),
    ('今は怖くないです。', '回答した時点では怖くない'),
    ('その時は私は怖くなかったです。', '褒められた時は嬉しくなく、あなたは怖くなく'),
    ('その時は少し重かったです。', '褒められた時は嬉しくなく、少し重く'),
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
    ('怖くなく', '怖く'), ('怖くなく', '怖くない'),
    ('あなたは', '私は'), ('あなたは', '友人は'), ('あなたは', 'あなたも'),
    ('褒められた時は', '褒められたことについて、回答した時点では'),
    ('あなたは怖くなく', '怖くなく'),
    ('あなたは怖くなく', 'あなたは怖かった'),
    ('あなたは怖くなく', '「あなたは怖くなく」'),
])
def test_changed_meaning_is_rejected_without_author(attributed, old, new):
    follow = attributed[0].artifact.reception
    changed = follow.replace(old, new, 1)
    assert changed != follow
    assert not inverse(attributed, changed, without_author=True).passed


def test_degree_is_not_lost_in_attributive_clause():
    context = actual(request=advance(begin(), 'その時は少し重かったです。'))
    follow = context[0].artifact.reception
    assert '少し重く' in follow
    assert not inverse(context, follow.replace('少し重く', '重く'),
                       without_author=True).passed


def test_revision_keeps_prior_answer_time_and_replaces_full_predicate():
    request = advance(advance(begin(), '今は私は重いです。'),
                      '「私は重いです」ではなく「私は苦しいです」です。')
    context = actual(request=request)
    follow = context[0].artifact.reception
    assert '先の回答時点ではあなたは苦しい' in follow
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


@pytest.mark.parametrize('memo', ['褒められたのに、嬉しくなかった。', MEMO])
@pytest.mark.parametrize('reply,visible,changed', [
    ('今は嬉しいです。', '嬉しい', '嬉しくない'),
    ('今は私には楽しいです。', 'あなたには楽しい', '友人には楽しい'),
    ('その時は私も嬉しかったです。', 'あなたも嬉しかった', 'あなたも嬉しい'),
    ('今は怖いです。', '怖い', '怖くない'),
    ('今は私は少し怖くないです。', 'あなたは少し怖くない', 'あなたは怖くない'),
    ('今は自分は苦しい。', 'あなたは苦しい', 'あなたも苦しい'),
    ('その時は私には怖くなかったです。', 'あなたには怖くな', 'あなたには怖'),
    ('その時は怖いです。', '怖い', '怖かった'),
    ('その時は私には少し怖いです。', 'あなたには少し怖い', 'あなたには怖い'),
    ('その時は私は少し怖くないです。', 'あなたは少し怖くない', 'あなたは少し怖かった'),
])
def test_finite_answer_retains_original_reaction_and_complete_source(memo, reply, visible, changed):
    initial = begin(memo)
    request = advance(initial, reply)
    context = actual(request=request)
    follow = context[0].artifact.reception
    assert visible in follow and '褒められた' in follow
    assert '受け止めています' not in follow and 'ですのですね' not in follow
    if reply.startswith('今は'):
        assert '回答した時点では' in follow
    else:
        assert 'その時は' in follow or '褒められた時は' in follow
    if memo == MEMO:
        assert '誘われたのに、悲しさを感じ' in follow
        assert '頼まれたのに、寂しさを感じた' in follow
    assert request.current_input_bundle == initial.current_input_bundle
    assert inverse(context, follow, without_author=True).passed
    lost_reaction = (follow.replace('嬉しくなく', '嬉しく', 1)
                     if '嬉しくなく' in follow else
                     follow.replace('嬉しさにはつながら', '嬉しさにつなが', 1))
    for corrupt in (follow.replace(visible, changed, 1), lost_reaction,
                    follow.replace('褒められた', '叱られた', 1),
                    follow.replace('褒められた', '褒められたおかげで', 1)):
        assert corrupt != follow
        assert not inverse(context, corrupt, without_author=True).passed


@pytest.mark.parametrize('occasion,old,new,visible', [
    ('今は', '私も嬉しいです', '私も楽しいです', '先の回答時点ではあなたも楽しい'),
    ('その時は', '私には嬉しかったです', '私には楽しかったです', 'その時はあなたには楽しかった'),
    ('今は', '私は少し怖くないです', '私は少し苦しくないです', '先の回答時点ではあなたは少し苦しくない'),
    ('その時は', '私は怖くなかったです', '私は寂しくなかったです', 'あなたは寂しくな'),
])
def test_saved_finite_answer_revision_withdrawal_and_reopen(qcase, qdb, monkeypatch,
                                                         occasion, old, new, visible):
    user, parent, service = qcase
    first = run(service.start(user, parent))
    current = run(answer(service, user, first, occasion + old + '。'))
    assert current['current_observation'] is not None
    with monkeypatch.context() as read:
        read.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved read rendered'))
        assert run(service.get(user, parent)) == current
        assert run(service.start(user, parent)) == current
    current = run(cont(service, user, current, 'continue-finite-correction'))
    current = run(answer(service, user, current,
        f'「{old}」ではなく「{new}」です。', 'correct-finite'))
    body = current['current_observation']['text']
    assert visible in body and 'ですのですね' not in body
    assert '誘われた' in body and '悲しさ' in body and '寂しさ' in body
    assert current['original'] == first['original']
    with monkeypatch.context() as read:
        read.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved read rendered'))
        assert run(service.get(user, parent)) == current
        assert run(service.start(user, parent)) == current
    current = run(cont(service, user, current, 'continue-finite-withdrawal'))
    current = run(answer(service, user, current, f'「{new}」は誤りです。', 'withdraw-finite'))
    assert current['current_observation']['text'] == first['current_observation']['text']
    with monkeypatch.context() as read:
        read.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved read rendered'))
        assert run(service.get(user, parent)) == current
        assert run(service.start(user, parent)) == current


@pytest.mark.parametrize('reply,reason', [
    ('今は不安です。', 'emlis_refined_body_unavailable'),
    ('今は私にも嬉しいです。', 'answer_syntax_unsupported'),
    ('今は友人には嬉しいです。', 'answer_syntax_unsupported'),
    ('今は私が嬉しいです。', 'emlis_thread_body_generated'),
    ('今は私は僕には嬉しいです。', 'emlis_thread_body_generated'),
    ('その時は私は私には怖かったです。', 'emlis_thread_body_generated'),
])
def test_finite_answer_keeps_unproven_source_on_existing_path(reply, reason):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    outcome = MeaningExperienceEngine().generate(advance(begin(), reply))
    assert outcome.reason_codes == (reason,)
    if outcome.artifact is not None:
        # These remain on the previous nominal path, including its known
        # surface limitations; they do not acquire a new finite reading.
        assert '受け止めています' in outcome.artifact.reception
    else:
        assert reason != 'emlis_thread_body_generated'


@pytest.mark.parametrize('occasion', ['その時は', '今は'])
def test_partial_self_conversion_cannot_become_a_new_finite_reading(occasion):
    context = actual(request=advance(begin(), occasion + '私は私には怖かったです。'))
    follow = ('褒められた時は嬉しくなく、あなたは私には怖く、'
              '誘われたのに、悲しさを感じ、頼まれたのに、寂しさを感じたのですね。'
              if occasion == 'その時は' else
              '褒められた時は嬉しくなく、回答した時点ではあなたは私には怖かったし、'
              '誘われたのに、悲しさを感じたし、頼まれたのに、寂しさを感じたのですね。')
    assert not inverse(context, follow, without_author=True).passed
