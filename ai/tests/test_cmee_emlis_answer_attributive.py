"""Admitted answers retain meaning in finite prose and remaining nominal paths."""
import pytest
from test_cmee_emlis_received_discourse import actual, inverse, assert_complete_occasion_scopes
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
    if reply == 'その時は私は怖くなかったです。':
        clause = '褒められた時は嬉しくなく、あなたは怖くなかったのですね'
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
    # Preserve each mutation's meaning after the answer ends its own sentence.
    if '怖くなく' in old:
        old = old.replace('怖くなく', '怖くなかった')
        new = '怖かった' if new == '怖く' else new.replace('怖くなく', '怖くなかった')
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
    assert '褒められたことについて、その時は重かったし、' in follow
    assert '誘われたことについて、その時は怖くなかったのですね。' in follow
    assert inverse(context, follow, without_author=True).passed
    swapped = follow.replace('褒められた', 'TEMP').replace('誘われた', '褒められた').replace('TEMP', '誘われた')
    assert swapped != follow
    assert not inverse(context, swapped, without_author=True).passed
    for old, new in (
        ('褒められたことについて、その時は', '褒められたことについて、回答した時点では'),
        ('誘われたことについて、その時は', '誘われたことについて、'),
        ('怖くなかった', '怖かった'),
    ):
        changed = follow.replace(old, new, 1)
        assert changed != follow and not inverse(context, changed, without_author=True).passed


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
    ('今は不安です。', 'emlis_thread_body_generated'),
    ('今は私にも嬉しいです。', 'answer_syntax_unsupported'),
    ('今は友人には嬉しいです。', 'answer_syntax_unsupported'),
    ('今は私が嬉しいです。', 'emlis_thread_body_generated'),
    ('今は私は僕には嬉しいです。', 'emlis_thread_body_generated'),
    ('その時は私は私には怖かったです。', 'emlis_thread_body_generated'),
])
def test_finite_answer_accepts_proven_noun_and_keeps_unproven_boundaries(reply, reason):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    outcome = MeaningExperienceEngine().generate(advance(begin(), reply))
    assert outcome.reason_codes == (reason,)
    if reply == '今は不安です。':
        context = actual(request=advance(begin(), reply))
        follow = outcome.artifact.reception
        assert '回答した時点では不安なのですね。' in follow
        assert inverse(context, follow, without_author=True).passed
    elif outcome.artifact is not None:
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
    if occasion == '今は':
        split_follow = ('褒められた時は嬉しくなく、回答した時点ではあなたは私には怖かったのですね。'
                        '誘われたのに、悲しさを感じ、頼まれたのに、寂しさを感じたのですね。')
        assert not inverse(context, split_follow, without_author=True).passed


@pytest.mark.parametrize('occasion', ['今は', 'その時は'])
@pytest.mark.parametrize('copula', ['です', 'でした'])
@pytest.mark.parametrize('preceding', [None, 0, 1, 2])
def test_copular_answer_retains_tense_event_and_reactions(occasion, copula, preceding):
    single = preceding is None
    initial = begin('褒められたのに、嬉しくなかった。' if single else MEMO)
    request = initial
    for reply in ('その時は怖かった。', '今は重い。')[:preceding or 0]:
        request = advance(request, reply)
    request = advance(request, occasion + '不安' + copula + '。')
    context = actual(request=request)
    follow = context[0].artifact.reception
    target = ('褒められた', '誘われた', '頼まれた')[preceding or 0]
    final = preceding != 1
    predicate = '不安だった' if copula == 'でした' else '不安な'
    assert predicate + ('のですね' if final else 'こと') in follow
    assert target + ('時は' if final else 'のに悲しかったことと、') in follow
    assert '嬉しくなく' in follow
    if not single:
        assert '悲し' in follow and '寂し' in follow
        assert all(follow.count(event) == 1 for event in ('褒められた', '誘われた', '頼まれた'))
    time = '回答した時点では' if final else '回答した時点で'
    if occasion == '今は':
        assert time + predicate in follow
    else:
        assert ('褒められた時は' if preceding in (None, 0) else
                'その出来事について、その時に' if preceding == 1 else '頼まれた時は') in follow
    assert request.current_input_bundle == initial.current_input_bundle
    assert ('受け止めています' in follow) == (preceding in (1, 2))
    assert 'だのですね' not in follow
    if not single:
        groups = ((0,), (1, 2)) if preceding == 0 else ((0,), (1,), (2,))
        assert_complete_occasion_scopes(context, ('褒められた', '誘われた', '頼まれた'), groups)
    assert inverse(context, follow, without_author=True).passed
    changed_tense = '不安な'
    if copula == 'です':
        changed_tense = '不安だった'
    corruptions = [
        follow.replace(predicate, changed_tense, 1),
        follow.replace('不安', '安心', 1),
        follow.replace('不安', '友人は不安', 1),
        follow.replace('不安', '少し不安', 1),
        follow.replace('嬉しくなく', '嬉しく', 1),
        follow.replace(target, target + 'おかげで', 1),
    ]
    if occasion == '今は':
        corruptions.append(follow.replace(time + predicate, 'その時は' + predicate, 1))
    else:
        corruptions.append(follow.replace(predicate, '回答した時点では' + predicate, 1))
    if not single:
        corruptions.append(follow.replace(target, '別の出来事', 1))
    if copula == 'です':
        # な is attributive only: 不安なし must not mean 不安だし.
        corruptions.append(follow.replace(predicate, '不安だ', 1))
    for changed in corruptions:
        assert changed != follow
        assert not inverse(context, changed, without_author=True).passed


@pytest.mark.parametrize('occasion', ['今は', 'その時は'])
@pytest.mark.parametrize('copula', ['です', 'でした'])
def test_copular_answer_keeps_event_after_original_reaction_withdrawal(occasion, copula):
    request = advance(advance(begin(), occasion + '不安' + copula + '。'),
                      '「嬉しくなかった」は誤りです。')
    context = actual(request=request)
    follow = context[0].artifact.reception
    assert '褒められた' in follow and '嬉し' not in follow
    assert '不安' in follow and '悲しさ' in follow and '寂しさ' in follow
    assert inverse(context, follow, without_author=True).passed
    changed = follow.replace('褒められた', '誘われた', 1)
    assert changed != follow and not inverse(context, changed, without_author=True).passed


@pytest.mark.parametrize('occasion', ['今は', 'その時は'])
def test_copular_grammar_preserves_another_admitted_noun(occasion):
    context = actual(request=advance(begin(), occasion + 'もやもやでした。'))
    follow = context[0].artifact.reception
    ending = 'のですね'
    assert 'もやもやだった' + ending in follow and '嬉しくなく' in follow
    assert '悲しさ' in follow and '寂しさ' in follow
    assert inverse(context, follow, without_author=True).passed
    changed = follow.replace('もやもやだった' + ending,
                             'もやもやな' + ending)
    assert changed != follow and not inverse(context, changed, without_author=True).passed


@pytest.mark.parametrize('occasion', ['今は', 'その時は'])
@pytest.mark.parametrize('old,new', [('不安です', '不安でした'), ('不安でした', '不安です')])
def test_saved_copular_answer_correction_withdrawal_and_authorless_reopen(
        qcase, qdb, monkeypatch, occasion, old, new):
    user, parent, service = qcase
    first = run(service.start(user, parent))
    current = run(answer(service, user, first, occasion + old + '。'))
    assert current['current_observation'] is not None
    with monkeypatch.context() as read:
        read.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved read rendered'))
        assert run(service.get(user, parent)) == current
        assert run(service.start(user, parent)) == current
    current = run(cont(service, user, current, 'continue-copula-correction'))
    current = run(answer(service, user, current,
        f'「{old}」ではなく「{new}」です。', 'correct-copula'))
    body = current['current_observation']['text']
    predicate = '不安だった' if new.endswith('でした') else '不安な'
    ending = 'のですね'
    assert predicate + ending in body and old not in body
    assert '嬉しくなく' in body and '悲しさ' in body and '寂しさ' in body
    if occasion == '今は':
        assert '先の回答時点では' + predicate in body
    else:
        assert '褒められた時は嬉しくなく、' + predicate in body
    assert current['original'] == first['original']
    with monkeypatch.context() as read:
        read.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved read rendered'))
        assert run(service.get(user, parent)) == current
        assert run(service.start(user, parent)) == current
    current = run(cont(service, user, current, 'continue-copula-withdrawal'))
    current = run(answer(service, user, current, f'「{new}」は誤りです。', 'withdraw-copula'))
    assert current['current_observation']['text'] == first['current_observation']['text']
    assert current['original'] == first['original']
    with monkeypatch.context() as read:
        read.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved read rendered'))
        assert run(service.get(user, parent)) == current
        assert run(service.start(user, parent)) == current

@pytest.mark.parametrize('memo', ['褒められたのに、嬉しくなかった。', MEMO])
@pytest.mark.parametrize('occasion', ['今は', 'その時は'])
@pytest.mark.parametrize('source,visible,past', [
    ('私は不安です', 'あなたは不安', False),
    ('私も少し不安です', 'あなたも少し不安', False),
    ('自分は不安でした', 'あなたは不安', True),
    ('少し不安だ', '少し不安', False),
    ('私は不安だった', 'あなたは不安', True),
    ('不安だ', '不安', False),
])
def test_scoped_copular_answer_is_finite_with_complete_meaning(memo, occasion, source, visible, past):
    initial = begin(memo)
    request = advance(initial, occasion + source + '。')
    context = actual(request=request)
    follow = context[0].artifact.reception
    predicate = visible + ('だった' if past else 'な')
    assert predicate + 'のですね' in follow
    assert '褒められた時は嬉しくなく、' in follow
    assert '受け止めています' not in follow and 'ですこと' not in follow
    assert 'だのですね' not in follow
    if occasion == '今は':
        assert '回答した時点では' + predicate in follow
    else:
        assert '褒められた時は嬉しくなく、' + predicate in follow
    assert request.current_input_bundle == initial.current_input_bundle
    assert inverse(context, follow, without_author=True).passed
    if memo == MEMO:
        assert all(follow.count(event) == 1 for event in ('褒められた', '誘われた', '頼まれた'))
        assert '悲しさ' in follow and '寂しさ' in follow
    opposite = visible + 'な' if past else visible + 'だった'
    corruptions = [
        follow.replace(predicate, opposite, 1),
        follow.replace('不安', '安心', 1),
        follow.replace('不安', '不安ではない', 1),
        follow.replace('嬉しくなく', '嬉しく', 1),
        follow.replace('褒められた', '別の出来事', 1),
        follow.replace('褒められた', '褒められたおかげで', 1),
        follow.replace('あなた', '友人', 1) if 'あなた' in follow else follow.replace(visible, '友人は' + visible, 1),
        follow.replace('少し', '', 1) if '少し' in follow else follow.replace('不安', '少し不安', 1),
        follow.replace('回答した時点では', '先の回答時点では', 1)
        if occasion == '今は' else follow.replace(predicate, '回答した時点では' + predicate, 1),
    ]
    if not past:
        corruptions.append(follow.replace(predicate, visible + 'だ', 1))
    if 'あなたは' in follow:
        corruptions.append(follow.replace('あなたは', 'あなたも', 1))
    elif 'あなたも' in follow:
        corruptions.append(follow.replace('あなたも', 'あなたは', 1))
    for changed in corruptions:
        assert changed != follow
        assert not inverse(context, changed, without_author=True).passed


@pytest.mark.parametrize('preceding', [1, 2])
@pytest.mark.parametrize('source,predicate', [
    ('私には不安でした', 'あなたには不安だった'),
    ('私は少し不安です', 'あなたは少し不安'),
])
def test_scoped_copular_answer_keeps_middle_and_last_event(preceding, source, predicate):
    request = begin()
    for reply in ('その時は怖かった。', '今は重い。')[:preceding]:
        request = advance(request, reply)
    context = actual(request=advance(request, '今は' + source + '。'))
    follow = context[0].artifact.reception
    final = preceding == 2
    if source.endswith('です'):
        predicate += 'な'
    time = '回答した時点では' if final else '回答した時点で'
    assert time + predicate + ('のですね' if final else 'こと') in follow
    assert_complete_occasion_scopes(context, ('褒められた', '誘われた', '頼まれた'), ((0,), (1,), (2,)))
    assert all(follow.count(event) == 1 for event in ('褒められた', '誘われた', '頼まれた'))
    assert '嬉しくなく' in follow and '悲し' in follow and '寂し' in follow
    assert inverse(context, follow, without_author=True).passed
    target = ('誘われた', '頼まれた')[preceding - 1]
    changed = follow.replace(target, '別の出来事', 1)
    assert not inverse(context, changed, without_author=True).passed
    particle = 'には' if 'あなたには' in follow else 'は'
    changed = follow.replace('あなた' + particle, 'あなたも', 1)
    assert not inverse(context, changed, without_author=True).passed


@pytest.mark.parametrize('source,visible', [
    ('私は少しだけ不安だった', 'あなたは少しだけ不安だった'),
    ('やや不安だった', 'やや不安だった'),
])
def test_existing_finite_past_outside_noun_inflection_remains_readable(source, visible):
    context = actual(request=advance(begin(), '今は' + source + '。'))
    follow = context[0].artifact.reception
    assert '回答した時点では' + visible + 'のですね。' in follow
    assert inverse(context, follow, without_author=True).passed
    assert not inverse(context, follow.replace(visible, '不安だった', 1),
                       without_author=True).passed


@pytest.mark.parametrize('source,invalid', [
    ('私は私には不安です', 'あなたは私には不安'),
    ('少し私は不安です', '少し私は不安'),
    ('私は不安なのです', 'あなたは不安なの'),
    ('私は不安だそうです', 'あなたは不安だそう'),
])
def test_unproven_copula_host_does_not_gain_a_new_finite_reading(source, invalid):
    context = actual(request=advance(begin(), '今は' + source + '。'))
    follow = ('褒められた時は嬉しくなく、回答した時点では' + invalid + 'だし、'
              '誘われたのに、悲しさを感じたし、頼まれたのに、寂しさを感じたのですね。')
    if source == '私は不安なのです':
        # This explicit explanation now has its own proven finite reading.
        # Its の shares the final acknowledgement in this separate scope.
        expected = ('褒められた時は嬉しくなく、回答した時点ではあなたは不安なのですね。'
                    '誘われたのに、悲しさを感じ、頼まれたのに、寂しさを感じたのですね。')
        assert context[0].artifact.reception == expected
        assert inverse(context, expected, without_author=True).passed
        assert not inverse(context, expected.replace('不安なのですね', '不安ですね'),
                           without_author=True).passed
        return
    assert not inverse(context, follow, without_author=True).passed
    split_follow = ('褒められた時は嬉しくなく、回答した時点では' + invalid + 'なのですね。'
                    '誘われたのに、悲しさを感じ、頼まれたのに、寂しさを感じたのですね。')
    assert not inverse(context, split_follow, without_author=True).passed
    if source == '少し私は不安です':
        # A single medial owner now has a proven finite reading. The
        # first-person candidate above must still be rejected.
        expected = split_follow.replace('少し私は不安', 'あなたは少し不安', 1)
        assert context[0].artifact.reception == expected
        assert inverse(context, expected, without_author=True).passed
        return
    if source != '私は不安だそうです':
        # Existing nominal fallbacks remain available, with their known
        # surface defects; this change does not expand source admission.
        assert '受け止めています' in context[0].artifact.reception


@pytest.mark.parametrize('occasion', ['今は', 'その時は'])
def test_scoped_copular_answer_keeps_event_after_original_reaction_withdrawal(occasion):
    request = advance(advance(begin(), occasion + '私は少し不安です。'),
                      '「嬉しくなかった」は誤りです。')
    context = actual(request=request)
    follow = context[0].artifact.reception
    assert '褒められた' in follow and '嬉し' not in follow
    assert 'あなたは少し不安だし' in follow
    assert '悲しさ' in follow and '寂しさ' in follow
    assert inverse(context, follow, without_author=True).passed
    assert not inverse(context, follow.replace('褒められた', '誘われた', 1),
                       without_author=True).passed


@pytest.mark.parametrize('occasion', ['今は', 'その時は'])
@pytest.mark.parametrize('old,new,visible', [
    ('私は不安です', '私も少し不安でした', 'あなたも少し不安だった'),
    ('私には不安でした', '私は少し不安です', 'あなたは少し不安だ'),
])
def test_saved_scoped_copular_revision_withdrawal_and_authorless_reopen(
        qcase, qdb, monkeypatch, occasion, old, new, visible):
    user, parent, service = qcase
    first = run(service.start(user, parent))
    current = run(answer(service, user, first, occasion + old + '。'))
    assert current['current_observation'] is not None
    with monkeypatch.context() as read:
        read.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved read rendered'))
        assert run(service.get(user, parent)) == current
        assert run(service.start(user, parent)) == current
    current = run(cont(service, user, current, 'continue-scoped-copula-correction'))
    current = run(answer(service, user, current,
        f'「{old}」ではなく「{new}」です。', 'correct-scoped-copula'))
    body = current['current_observation']['text']
    if visible.endswith('だ'):
        visible = visible[:-1] + 'な'
    ending = 'のですね'
    assert visible + ending in body and old not in body
    assert '嬉しくなく' in body and '悲しさ' in body and '寂しさ' in body
    assert ('先の回答時点では' + visible if occasion == '今は'
            else '褒められた時は嬉しくなく、' + visible) in body
    assert current['original'] == first['original']
    with monkeypatch.context() as read:
        read.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved read rendered'))
        assert run(service.get(user, parent)) == current
        assert run(service.start(user, parent)) == current
    current = run(cont(service, user, current, 'continue-scoped-copula-withdrawal'))
    current = run(answer(service, user, current, f'「{new}」は誤りです。', 'withdraw-scoped-copula'))
    assert current['current_observation']['text'] == first['current_observation']['text']
    assert current['original'] == first['original']
    with monkeypatch.context() as read:
        read.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved read rendered'))
        assert run(service.get(user, parent)) == current
        assert run(service.start(user, parent)) == current


@pytest.mark.parametrize('memo', ['褒められたのに、嬉しくなかった。', MEMO])
@pytest.mark.parametrize('occasion', ['今は', 'その時は'])
@pytest.mark.parametrize('source,visible,other_tense', [
    ('私は不安なのです', 'あなたは不安な', 'あなたは不安だった'),
    ('私も少し不安なのです', 'あなたも少し不安な', 'あなたも少し不安だった'),
    ('私には不安だったのです', 'あなたには不安だった', 'あなたには不安な'),
    ('怖いのです', '怖い', '怖かった'),
    ('私は怖かったのです', 'あなたは怖かった', 'あなたは怖い'),
    ('私は怖くないのです', 'あなたは怖くない', 'あなたは怖くなかった'),
    ('私は怖くなかったのです', 'あなたは怖くなかった', 'あなたは怖くない'),
    ('私は不安なのだ', 'あなたは不安な', 'あなたは不安だった'),
    ('私は不安ではないのです', 'あなたは不安ではない', 'あなたは不安ではなかった'),
    ('私は不安ではなかったのです', 'あなたは不安ではなかった', 'あなたは不安ではない'),
])
def test_explanatory_answer_preserves_complete_source_in_finite_prose(
        memo, occasion, source, visible, other_tense):
    initial = begin(memo)
    request = advance(initial, occasion + source + '。')
    context = actual(request=request)
    follow = context[0].artifact.reception
    ending = 'のですね'
    assert visible + ending in follow
    assert '褒められた時は嬉しくなく、' in follow
    assert 'ですこと' not in follow and '受け止めています' not in follow
    assert 'なのなのですね' not in follow
    assert request.current_input_bundle == initial.current_input_bundle
    if occasion == '今は':
        assert '回答した時点では' + visible + ending in follow
    else:
        assert '褒められた時は嬉しくなく、' + visible + ending in follow
    if memo == MEMO:
        assert all(follow.count(event) == 1 for event in ('褒められた', '誘われた', '頼まれた'))
        assert '悲しさ' in follow and '寂しさ' in follow
    assert inverse(context, follow, without_author=True).passed
    plain = visible[:-1] if visible.endswith('な') else visible
    corruptions = [
        follow.replace(visible + ending, other_tense + ending, 1),
        follow.replace(visible + ending, plain + 'ですね', 1),
        follow.replace(visible + ending, visible + 'のな' + ending, 1),
        follow.replace('嬉しくなく', '嬉しく', 1),
        follow.replace('褒められた', '誘われた', 1),
        follow.replace('褒められた', '褒められたおかげで', 1),
        follow.replace('あなた', '友人', 1) if 'あなた' in follow else follow.replace(visible, '友人は' + visible, 1),
        follow.replace('少し', '', 1) if '少し' in follow else follow.replace(visible, '少し' + visible, 1),
        follow.replace('回答した時点では', '先の回答時点では', 1)
        if occasion == '今は' else follow.replace(visible, '回答した時点では' + visible, 1),
    ]
    if 'くない' in visible:
        corruptions.append(follow.replace('くない', 'い', 1))
    elif 'くなかった' in visible:
        corruptions.append(follow.replace('くなかった', 'かった', 1))
    elif 'ではなかった' in visible:
        corruptions.append(follow.replace('ではなかった', 'だった', 1))
    elif 'ではない' in visible:
        corruptions.append(follow.replace('ではない', 'な', 1))
    if 'あなたは' in follow:
        corruptions.append(follow.replace('あなたは', 'あなたも', 1))
    if 'あなたも' in follow:
        corruptions.append(follow.replace('あなたも', 'あなたは', 1))
    if 'あなたには' in follow:
        corruptions.append(follow.replace('あなたには', 'あなたにも', 1))
    for changed in corruptions:
        assert changed != follow
        assert not inverse(context, changed, without_author=True).passed


@pytest.mark.parametrize('preceding', [1, 2])
@pytest.mark.parametrize('source,visible', [
    ('私は不安なのです', 'あなたは不安な'),
    ('私には怖くなかったのです', 'あなたには怖くなかった'),
])
def test_explanatory_answer_keeps_intermediate_and_final_attachment(preceding, source, visible):
    request = begin()
    for reply in ('その時は怖かった。', '今は重い。')[:preceding]:
        request = advance(request, reply)
    context = actual(request=advance(request, '今は' + source + '。'))
    follow = context[0].artifact.reception
    ending = 'のですね' if preceding == 2 else 'のだということ'
    time = '回答した時点では' if preceding == 2 else '回答した時点で'
    assert time + visible + ending in follow
    assert_complete_occasion_scopes(context, ('褒められた', '誘われた', '頼まれた'), ((0,), (1,), (2,)))
    assert all(follow.count(event) == 1 for event in ('褒められた', '誘われた', '頼まれた'))
    assert inverse(context, follow, without_author=True).passed
    target = ('誘われた', '頼まれた')[preceding - 1]
    assert not inverse(context, follow.replace(target, '別の出来事', 1),
                       without_author=True).passed
    changed = follow.replace(visible + ending, visible + 'のな' + ending, 1)
    assert not inverse(context, changed, without_author=True).passed


@pytest.mark.parametrize('source,original,changed', [
    ('私は不安です', 'あなたは不安だし', 'あなたは不安なのだし'),
    ('私は怖かったです', 'あなたは怖かったし', 'あなたは怖かったのだし'),
    ('私は不安なのだった', 'あなたは不安なのだったし', 'あなたは不安だったのだし'),
])
def test_explanation_cannot_be_added_or_move_the_outer_past(source, original, changed):
    final_original, final_changed = {
        '私は不安です': ('あなたは不安なのですね', '友人は不安なのですね'),
        '私は怖かったです': ('あなたは怖かったのですね', 'あなたは怖いのですね'),
        '私は不安なのだった': ('あなたは不安なのでしたね', 'あなたは不安だったのですね'),
    }[source]
    for preceding in (False, True):
        request = advance(begin(), 'その時は怖かった。') if preceding else begin()
        context = actual(request=advance(request, '今は' + source + '。'))
        follow = context[0].artifact.reception
        if preceding:
            # The middle answer now uses the existing nominal grammar. Keep
            # explanation-addition and outer-past movement as real mutations.
            original, changed = {
                '私は不安です': ('あなたは不安なこと', 'あなたは不安なのだということ'),
                '私は怖かったです': ('あなたは怖かったこと', 'あなたは怖かったのだということ'),
                '私は不安なのだった': ('あなたは不安なのだったということ', 'あなたは不安だったのだということ'),
            }[source]
            assert original in follow
            corrupt = follow.replace(original, changed, 1)
        else:
            # Plain/explanatory の already share the existing final grammar;
            # verify the complete split body and a real meaning change here.
            assert follow == ('褒められた時は嬉しくなく、回答した時点では' + final_original + '。'
                              '誘われたのに、悲しさを感じ、頼まれたのに、寂しさを感じたのですね。')
            corrupt = follow.replace(final_original, final_changed, 1)
        assert inverse(context, follow, without_author=True).passed
        assert corrupt != follow and not inverse(context, corrupt, without_author=True).passed


@pytest.mark.parametrize('source,invalid', [
    ('私は私には不安なのです', 'あなたは私には不安なのだし'),
    ('少し私は不安なのです', '少し私は不安なのだし'),
    ('私は不安なのだそうです', 'あなたは不安なのだし'),
])
def test_unproven_explanation_cannot_erase_subject_or_hearsay(source, invalid):
    context = actual(request=advance(begin(), '今は' + source + '。'))
    follow = ('褒められた時は嬉しくなく、回答した時点では' + invalid + '、'
              '誘われたのに、悲しさを感じたし、頼まれたのに、寂しさを感じたのですね。')
    assert not inverse(context, follow, without_author=True).passed
    split_follow = ('褒められた時は嬉しくなく、回答した時点では'
                    + invalid.removesuffix('のだし') + 'のですね。'
                    '誘われたのに、悲しさを感じ、頼まれたのに、寂しさを感じたのですね。')
    assert not inverse(context, split_follow, without_author=True).passed


@pytest.mark.parametrize('occasion', ['今は', 'その時は'])
def test_explanatory_answer_keeps_event_after_original_reaction_withdrawal(occasion):
    request = advance(advance(begin(), occasion + '私は少し不安なのです。'),
                      '「嬉しくなかった」は誤りです。')
    context = actual(request=request)
    follow = context[0].artifact.reception
    assert '褒められた' in follow and '嬉し' not in follow
    assert 'あなたは少し不安なのだし' in follow
    assert '悲しさ' in follow and '寂しさ' in follow
    assert inverse(context, follow, without_author=True).passed
    assert not inverse(context, follow.replace('不安なのだし', '不安だし', 1),
                       without_author=True).passed


@pytest.mark.parametrize('occasion', ['今は', 'その時は'])
@pytest.mark.parametrize('old,new,visible', [
    ('私は不安なのです', '私も少し不安だったのです', 'あなたも少し不安だったのだ'),
    ('私には怖いのです', '私は怖くなかったのです', 'あなたは怖くなかったのだ'),
])
def test_saved_explanatory_revision_withdrawal_and_authorless_reopen(
        qcase, qdb, monkeypatch, occasion, old, new, visible):
    user, parent, service = qcase
    first = run(service.start(user, parent))
    current = run(answer(service, user, first, occasion + old + '。'))
    assert current['current_observation'] is not None
    for stage in ('answer', 'correction', 'withdrawal'):
        if stage == 'correction':
            current = run(cont(service, user, current, 'continue-explanatory-correction'))
            current = run(answer(service, user, current,
                f'「{old}」ではなく「{new}」です。', 'correct-explanatory'))
            body = current['current_observation']['text']
            visible = visible[:-2]  # The source の shares the final acknowledgement.
            ending = 'のですね'
            assert visible + ending in body and old not in body
            assert '嬉しくなく' in body and '悲しさ' in body and '寂しさ' in body
            assert ('先の回答時点では' + visible if occasion == '今は'
                    else '褒められた時は嬉しくなく、' + visible) in body
        elif stage == 'withdrawal':
            current = run(cont(service, user, current, 'continue-explanatory-withdrawal'))
            current = run(answer(service, user, current, f'「{new}」は誤りです。', 'withdraw-explanatory'))
            assert current['current_observation']['text'] == first['current_observation']['text']
        assert current['original'] == first['original']
        with monkeypatch.context() as read:
            read.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved read rendered'))
            assert run(service.get(user, parent)) == current
            assert run(service.start(user, parent)) == current
