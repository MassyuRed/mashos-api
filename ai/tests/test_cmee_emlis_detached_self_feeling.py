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


@pytest.mark.parametrize('occasion,prefix', [('今は', '回答した時点で、'), ('その時は', 'その時、')])
@pytest.mark.parametrize('source,visible', [
    ('私は嬉しいのです', 'あなたは嬉しい'),
    ('私も嬉しかったのだ', 'あなたも嬉しかった'),
    ('私には少し怖くなかったのです', 'あなたには少し怖くなかった'),
    ('僕には嬉しかったのです', 'あなたには嬉しかった'),
    ('自分は苦しいのだ', 'あなたは苦しい'),
])
def test_detached_explanation_keeps_complete_answer_and_other_reactions(occasion, prefix, source, visible):
    initial = begin()
    context = actual(request=advance(advance(initial, occasion + source + '。'), WITHDRAW))
    follow = context[0].artifact.reception
    assert prefix + visible + 'のですね。' in follow
    assert '褒められた' not in context[0].artifact.text
    assert 'その時は嬉しくなかった' in follow
    assert '悲しさを感じ' in follow and '寂しさを感じた' in follow
    assert '受け止めています' not in follow and 'ですこと' not in follow
    assert inverse(context, follow, without_author=True).passed
    changes = [(visible + 'のですね', visible + 'ですね'),
               (visible + 'のですね', visible + 'ののですね'),
               (visible, visible + 'らしい'), ('あなた', '私'), ('あなた', '友人'),
               (prefix, '先の回答時点で、'), (prefix, '褒められたことについて、' + prefix),
               ('その時は嬉しくなかった', 'その時は嬉しかった'),
               ('悲しさを感じ', '嬉しさを感じ')]
    if '少し' in visible:
        changes += [('少し', ''), ('怖くなかった', '怖かった')]
    if 'あなたも' in visible:
        changes += [('あなたも', 'あなたは')]
    if 'あなたには' in visible:
        changes += [('あなたには', 'あなたにも')]
    if visible.endswith('しかった'):
        changes += [(visible, visible[:-3] + 'い')]
    for old, new in changes:
        changed = follow.replace(old, new, 1)
        assert changed != follow
        assert not inverse(context, changed, without_author=True).passed


@pytest.mark.parametrize('occasion,prefix', [('今は', '回答した時点では'), ('その時は', 'その時は')])
def test_detached_explanation_without_explicit_subject_preserves_time(occasion, prefix):
    context = actual(request=advance(advance(begin(), occasion + '嬉しいのです。'), WITHDRAW))
    follow = context[0].artifact.reception
    assert prefix + '嬉しいのですね。' in follow
    assert inverse(context, follow, without_author=True).passed


def test_detached_explanation_intermediate_clause_retains_its_own_no():
    context = actual(request=advance(advance(begin(), '今は私は苦しいのです。'), WITHDRAW))
    _, plan, _, resolver, selected = context
    moves = reception.reception_active_moves(plan.response_plan.human_reception_plan, 'full')[:2]
    assert len(moves) == 2
    # Exercise the independent reader's other operand position with the same
    # proven sources. This does not change the product's selected Move order.
    clause = '回答した時点で、あなたは苦しいのだし、その時は嬉しくなかったのですね。'
    proof = gate.read_detached_feeling_pair(clause, moves[::-1], plan, resolver, selected)
    assert proof is not None
    assert proof[0][0][2].decode() == '私は苦しいのです'
    for old, new in [('苦しいのだし', '苦しいし'), ('苦しいのだし', '苦しいののだし'),
                     ('苦しいのだし', '苦しいので'), ('あなたは', '私には')]:
        assert gate.read_detached_feeling_pair(clause.replace(old, new), moves[::-1],
                                              plan, resolver, selected) is None


@pytest.mark.parametrize('source,invalid', [
    ('私は私には嬉しいのです', 'あなたは嬉しい'),
    ('少し私は嬉しいのです', 'あなたは少し嬉しい'),
    ('私は嬉しいのだった', 'あなたは嬉しかった'),
    ('私は不安なのです', 'あなたは不安'),
])
def test_detached_explanation_does_not_erase_unproven_source_parts(source, invalid):
    context = actual(request=advance(advance(begin(), '今は' + source + '。'), WITHDRAW))
    _, plan, _, resolver, selected = context
    move = next(m for m in plan.response_plan.human_reception_plan.moves
                if any(n.nucleus_id in m.target_nucleus_ids and n.source_fields == ('answer_text_private',)
                       for n in plan.nuclei))
    assert gate._read_detached_feeling_discourse('回答した時点で、' + invalid + 'のですね。',
                                               move, plan, resolver, selected) is None
    assert inverse(context, context[0].artifact.reception, without_author=True).passed


@pytest.mark.parametrize('occasion,prefix', [('今は', '先の回答時点で、'), ('その時は', 'その時、')])
def test_detached_explanation_revision_preserves_source_time_after_event_withdrawal(occasion, prefix):
    request = advance(advance(begin(), occasion + '私は嬉しいのです。'), WITHDRAW)
    context = actual(request=advance(request, '「私は嬉しいのです」ではなく「私も少し嬉しかったのだ」です。'))
    follow = context[0].artifact.reception
    assert prefix + 'あなたも少し嬉しかったのですね。' in follow
    assert '褒められた' not in context[0].artifact.text and 'あなたは嬉しい' not in follow
    assert inverse(context, follow, without_author=True).passed


@pytest.mark.parametrize('occasion', ['今は', 'その時は'])
@pytest.mark.parametrize('last', ['correction', 'withdrawal'])
def test_detached_explanation_saved_updates_and_authorless_reopen(qcase, qdb, monkeypatch, occasion, last):
    user, parent, service = qcase
    first = run(service.start(user, parent))
    current = run(answer(service, user, first, occasion + '私は嬉しいのです。'))
    for stage in ('answer', 'event_withdrawal', last):
        if stage == 'event_withdrawal':
            current = run(cont(service, user, current, 'continue-detached-event'))
            current = run(answer(service, user, current, WITHDRAW, 'withdraw-detached-event'))
        elif stage in ('correction', 'withdrawal'):
            current = run(cont(service, user, current, 'continue-detached-final'))
            text = ('「私は嬉しいのです」ではなく「私も少し嬉しかったのだ」です。'
                    if stage == 'correction' else '「私は嬉しいのです」は誤りです。')
            current = run(answer(service, user, current, text, 'update-detached-final'))
        body = current['current_observation']['text']
        assert current['original'] == first['original']
        assert '悲しさを感じ' in body and '寂しさを感じた' in body
        if stage != 'answer':
            assert '褒められた' not in body
            assert 'その時は嬉しくなかった' in body
        if stage == 'event_withdrawal':
            assert 'あなたは嬉しいのですね' in body
        elif stage == 'correction':
            prefix = '先の回答時点で、' if occasion == '今は' else 'その時、'
            assert prefix + 'あなたも少し嬉しかったのですね' in body
        elif stage == 'withdrawal':
            assert 'あなたは嬉しい' not in body and '私は嬉しいのです' not in body
        with monkeypatch.context() as m:
            m.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved read must not generate'))
            assert run(service.get(user, parent)) == current
            assert run(service.start(user, parent)) == current
