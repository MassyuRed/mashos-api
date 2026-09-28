"""Independent feelings keep their sources and times after partial withdrawal."""
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import patch
import pytest

import emlis_ai_grounded_human_reception as reception
import emlis_ai_grounded_observation_gate as gate
import emlis_ai_grounded_sentence_surface as surface
from test_cmee_emlis_received_discourse import actual
from test_cmee_emlis_q3_thread import begin, advance
from test_emlis_q3_application import qdb, qcase, cont
from test_emlis_q2_application import run, answer
from test_emlis_q4_application import active

MEMO = '誘われたのに、悲しかった。頼まれたのに、寂しかった。'
WITHDRAW = '「誘われた」は誤りです。'


def context_for(text, correction=None):
    memo = MEMO + ('褒められたのに、嬉しくなかった。' if correction else '')
    request = advance(advance(begin(memo), text), WITHDRAW)
    return actual(request=advance(request, correction) if correction else request)


def read_body(context, body):
    result, plan, sentence, resolver, selected = context
    with patch.object(gate, 'replay_source_grounded_human_reception_from_plan',
                      return_value=SimpleNamespace(text=result.artifact.reception)), patch.object(
            reception, '_author_source_grounded_reception_clauses', side_effect=AssertionError('no author oracle')), patch.object(
            surface, '_render_observation', side_effect=AssertionError('no observation oracle')):
        return gate.evaluate_grounded_surface_body_inverse(body=body.encode(), plan=plan,
            sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected)


@pytest.mark.parametrize('text,when,source', [
    ('その時は私は怖くなかったです。', 'その時', '私は怖くなかったです'),
    ('今は私も怖くないです。', '回答した時点', '私も怖くないです'),
    ('今は嬉しい。', '回答した時点', '嬉しい'),
])
def test_partial_withdrawal_delivers_each_independent_feeling(text, when, source):
    context = context_for(text)
    body = context[0].artifact.text
    assert f'その時の「悲しかった」と、{when}の「{source}」' in body
    assert '誘われた' not in body
    assert '「頼まれた」と「寂しかった」' in body
    assert '頼まれたのに、寂しさを感じた' in body
    assert read_body(context, body).passed


@pytest.fixture(scope='module')
def current_context():
    return context_for('今は私も怖くないです。')


@pytest.mark.parametrize('old,new', [
    ('その時の「悲しかった」', '回答した時点の「悲しかった」'),
    ('回答した時点の「私も怖くないです」', 'その時の「私も怖くないです」'),
    ('回答した時点の「私も怖くないです」', '先の回答時点の「私も怖くないです」'),
    ('回答した時点の', ''), ('その時の', ''),
    ('「悲しかった」', '「悲しい」'), ('「悲しかった」', '「友人が悲しかった」'),
    ('「私も怖くないです」', '「私も怖いです」'),
    ('「私も怖くないです」', '「怖くないです」'),
    ('「私も怖くないです」', '「私は怖くないです」'),
    ('「私も怖くないです」', '「私も怖くなかったです」'),
    ('と、回答した時点の「私も怖くないです」', ''),
    ('と、', 'ので、'), ('と、', 'のに、'),
    ('その時の', '誘われたその時の'),
    ('という気持ちが書かれています。', 'という気持ちが、頼まれたことから生まれています。'),
])
def test_observation_changes_fail_independently_of_both_authors(current_context, old, new):
    body = current_context[0].artifact.text
    changed = body.replace(old, new, 1)
    assert changed != body
    assert not read_body(current_context, changed).passed


def test_swapped_times_fail_even_when_both_time_tokens_remain(current_context):
    body = current_context[0].artifact.text
    changed = body.replace('その時の「悲しかった」と、回答した時点の「私も怖くないです」',
                           '回答した時点の「悲しかった」と、その時の「私も怖くないです」')
    assert changed != body
    assert not read_body(current_context, changed).passed


def test_equivalent_observation_ending_is_readable(current_context):
    body = current_context[0].artifact.text.replace('書かれています。', '記されています。')
    assert read_body(current_context, body).passed


def test_corrected_answer_keeps_its_prior_answer_time():
    context = context_for('今は私は重いです。', '「私は重いです」ではなく「私は苦しいです」です。')
    body = context[0].artifact.text
    assert '先の回答時点の「私は苦しいです」' in body
    assert '重い' not in body and '誘われた' not in body
    assert read_body(context, body).passed
    assert not read_body(context, body.replace('先の回答時点の', '回答した時点の')).passed


@pytest.mark.parametrize('field,value', [('actor', 'other_person'), ('polarity', 'positive')])
def test_original_source_frame_is_still_proven(current_context, field, value):
    result, plan, sentence, resolver, _ = current_context
    line = next(row for row in sentence.lines if len(row.binding.nucleus_ids) == 2 and not row.binding.relation_ids)
    index = {n.nucleus_id:n for n in plan.nuclei}
    nuclei = tuple(index[nid] for nid in line.binding.nucleus_ids)
    changed = (replace(nuclei[0], semantic_frame=replace(nuclei[0].semantic_frame, **{field:value})), nuclei[1])
    raw = result.artifact.text.splitlines()[1]
    assert not gate._body_inverse_detached_observation(raw, changed, plan, resolver)


@pytest.mark.parametrize('correct_prior', [False, True])
def test_partial_withdrawal_and_prior_correction_survive_saved_reads(qcase, qdb, correct_prior, monkeypatch):
    user, parent, _ = qcase
    service = active(monkeypatch)
    memo = MEMO + ('褒められたのに、嬉しくなかった。' if correct_prior else '')
    qdb.query('update public.emotions set memo=$1 where id=$2', [memo, parent])
    first = run(service.start(user, parent))
    current = run(answer(service, user, first, '今は私は重いです。'))
    current = run(cont(service, user, current, 'continue-observation'))
    current = run(answer(service, user, current, WITHDRAW, 'withdraw-observation'))
    body = current['current_observation']['text']
    assert 'その時の「悲しかった」と、回答した時点の「私は重いです」' in body
    if correct_prior:
        current = run(cont(service, user, current, 'continue-correction'))
        current = run(answer(service, user, current, '「私は重いです」ではなく「私は苦しいです」です。', 'correct-observation'))
        assert '先の回答時点の「私は苦しいです」' in current['current_observation']['text']
    assert current['original'] == first['original']
    monkeypatch.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved reads must not regenerate'))
    assert run(service.get(user, parent)) == current
    assert run(service.start(user, parent)) == current


# An admitted unknown answer remains an epistemic state after its event is
# withdrawn; it must never be folded into the detached-feeling grammar.
UNKNOWN_ANSWERS = (
    ('今はまだよく分からない。', 'まだよく分からない'),
    ('現在は分からない。', '分からない'),
)


def detached_unknown_request(prior, count=3):
    from test_cmee_emlis_q3_thread import MEMO as three_events
    memo = '。'.join(three_events.split('。')[:count]) + '。'
    return advance(advance(begin(memo), prior), '「褒められた」は誤りです。')


@pytest.mark.parametrize('prior,source', UNKNOWN_ANSWERS)
@pytest.mark.parametrize('count', [2, 3])
def test_detached_unknown_delivers_state_and_every_remaining_feeling(prior, source, count):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning
    request = detached_unknown_request(prior, count)
    public = MeaningExperienceEngine().generate(request)
    assert public.artifact is not None, public.reason_codes
    context = actual(request=request)
    result, plan, sentence, _, selected = context
    assert result.artifact.text == public.artifact.text
    state, = (n for n in plan.nuclei if n.source_fields == ('answer_text_private',))
    assert (state.kind, state.semantic_frame.predicate_kind, state.semantic_frame.modality,
            state.semantic_frame.time_scope) == ('state', 'state', 'uncertain', 'present')
    assert not any(state.nucleus_id in (r.from_nucleus_id, r.to_nucleus_id) for r in plan.relations)
    state_line, = (line for line in sentence.lines if line.binding.line_role != 'human_follow'
                   and state.nucleus_id in line.binding.nucleus_ids)
    assert state_line.binding.nucleus_ids == (state.nucleus_id,)
    assert not state_line.binding.relation_ids
    assert f'回答した時点では、「{source}」と書かれています。' in result.artifact.observation
    assert 'その時は嬉しくなかった' in result.artifact.reception
    assert '褒められた' not in result.artifact.text
    for event, feeling in [('誘われた', '悲し'), ('頼まれた', '寂し')][:count-1]:
        assert event in result.artifact.observation and event in result.artifact.reception
        assert feeling in result.artifact.reception
    checkpoint = prepare_emlis_meaning(request).checkpoint
    assert 'nucleus:s1:event' in checkpoint.inactive_claim_refs
    assert state.nucleus_id not in checkpoint.inactive_claim_refs
    assert read_body(context, result.artifact.text).passed


@pytest.fixture(scope='module')
def detached_unknown_context():
    return actual(request=detached_unknown_request(UNKNOWN_ANSWERS[0][0]))


@pytest.mark.parametrize('changed', [
    '回答した時点では、「分からない」と書かれています。',
    '回答した時点では、「まだ分からない」と書かれています。',
    '回答した時点では、「まだよく分かった」と書かれています。',
    '回答した時点では、「まだよく分からなかった」と書かれています。',
    '先の回答時点では、「まだよく分からない」と書かれています。',
    'その時では、「まだよく分からない」と書かれています。',
    '「まだよく分からない」と書かれています。',
    '回答した時点の気持ちとして、「まだよく分からない」が見えます。',
    '回答した時点では、友人が「まだよく分からない」と書かれています。',
    '回答した時点では、「友人はまだよく分からない」と書かれています。',
    '回答した時点では、「まだよく分からない」と誘われたことについて書かれています。',
    '褒められた回答した時点では、「まだよく分からない」と書かれています。',
    '回答した時点では、「まだよく分からない」と書かれています。そのため悲しかったのです。',
    '',
])
def test_detached_unknown_observation_rejects_changed_scope_without_authors(detached_unknown_context, changed):
    context = detached_unknown_context
    body = context[0].artifact.text
    original = '回答した時点では、「まだよく分からない」と書かれています。'
    assert original in body
    assert not read_body(context, body.replace(original, changed, 1)).passed


def test_detached_unknown_observation_accepts_equivalent_ending_without_authors(detached_unknown_context):
    body = detached_unknown_context[0].artifact.text
    assert read_body(detached_unknown_context, body.replace('と書かれています。', 'と記されています。')).passed


@pytest.mark.parametrize('old,new', [
    ('回答した時点でまだよく分からないこと', '回答した時点で分からないこと'),
    ('回答した時点でまだよく分からないこと', '回答した時点でまだ分からないこと'),
    ('回答した時点でまだよく分からないこと', 'その時にまだよく分からないこと'),
    ('回答した時点でまだよく分からないこと', '回答した時点でまだよく分からない気持ち'),
    ('回答した時点でまだよく分からないこと', '誘われたことについて、回答した時点でまだよく分からないこと'),
    ('回答した時点でまだよく分からないこと', '回答した時点でよく分かったこと'),
])
def test_detached_unknown_reception_rejects_changed_meaning_without_authors(detached_unknown_context, old, new):
    context = detached_unknown_context
    body = context[0].artifact.text
    assert old in context[0].artifact.reception
    assert not read_body(context, body.replace(old, new, 1)).passed


@pytest.mark.parametrize('prior,source', UNKNOWN_ANSWERS)
@pytest.mark.parametrize('operation', ['correct', 'withdraw'])
def test_detached_unknown_saved_correction_or_withdrawal_keeps_original_and_reads(qcase, qdb, monkeypatch, prior, source, operation):
    from test_emlis_q2_application import run, answer
    user, parent, service = qcase
    replacement = '分からない' if source == 'まだよく分からない' else 'まだよく分からない'
    final_answer = (f'「{source}」ではなく「{replacement}」です。' if operation == 'correct'
                    else f'「{source}」は誤りです。')
    first = current = run(service.start(user, parent))
    for index, text in enumerate((prior, '「褒められた」は誤りです。', final_answer)):
        if index:
            current = run(cont(service, user, current, f'unknown-continue-{index}'))
        current = run(answer(service, user, current, text, f'unknown-answer-{index}'))
        assert current['body_state'] == 'REFINED', current
        assert current['original'] == first['original']
        body = current['current_observation']['text']
        if index:
            assert '褒められた' not in body and 'その時は嬉しくなかった' in body
        if index == 1:
            assert f'回答した時点では、「{source}」と書かれています。' in body
        if index == 2:
            if operation == 'correct':
                assert f'先の回答時点では、「{replacement}」と書かれています。' in body
            else:
                assert '分からない' not in body
        for event in ('誘われた', '頼まれた'):
            assert event in body
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved reads must not regenerate'))
            assert run(service.get(user, parent)) == current
            assert run(service.start(user, parent)) == current


# A detached epistemic answer remains independent even when its sentence
# shares an observation line with other events and supplemental answers.
COMPOUND_UNKNOWN = '今はまだよく分からない。'
COMPOUND_STATE = 'また、回答した時点では、「まだよく分からない」と書かれています。'


def compound_unknown_request(unknown=COMPOUND_UNKNOWN, second='今は怖い。', reverse=False):
    request = begin()
    answers = (second, unknown) if reverse else (unknown, second)
    for text in (*answers, '「誘われた」は誤りです。' if reverse else '「褒められた」は誤りです。'):
        request = advance(request, text)
    return request


@pytest.mark.parametrize('unknown,source', UNKNOWN_ANSWERS)
@pytest.mark.parametrize('second', ['その時は怖かった。', '今は怖い。', '現在は分からない。'])
@pytest.mark.parametrize('reverse', [False, True])
def test_compound_unknown_withdrawal_delivers_each_retained_source(unknown, source, second, reverse):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning
    request = compound_unknown_request(unknown, second, reverse)
    output = MeaningExperienceEngine().generate(request)
    assert output.artifact is not None, output.reason_codes
    context = actual(request=request)
    result, plan, sentence, resolver, selected = context
    assert result.artifact.text == output.artifact.text
    states = [n for n in plan.nuclei if n.source_fields == ('answer_text_private',)
              and 'thread_subject:withdrawn_source_event' in n.semantic_frame.attribute_codes]
    state, = states
    assert (state.kind, state.semantic_frame.predicate_kind, state.semantic_frame.modality) == ('state', 'state', 'uncertain')
    assert not any(state.nucleus_id in (r.from_nucleus_id, r.to_nucleus_id) for r in plan.relations)
    assert f'回答した時点では、「{source}」と書かれています。' in result.artifact.observation
    withdrawn, retained = ('誘われた', '褒められた') if reverse else ('褒められた', '誘われた')
    assert withdrawn not in result.artifact.text
    assert retained in result.artifact.observation and retained in result.artifact.reception
    assert '頼まれた' in result.artifact.text and '寂し' in result.artifact.reception
    assert ('その時は悲しかった' if reverse else 'その時は嬉しくなかった') in result.artifact.reception
    assert '分からない' in result.artifact.reception
    assert ('怖' if '怖' in second else '分からない') in result.artifact.reception
    assert len(plan.response_plan.human_reception_plan.moves) <= 3
    required = set(plan.coverage_requirements.required_nucleus_ids)
    covered = {nid for line in sentence.lines if line.binding.line_role != 'human_follow' for nid in line.binding.nucleus_ids}
    assert required <= covered
    assert state.nucleus_id not in prepare_emlis_meaning(request).checkpoint.inactive_claim_refs
    assert read_body(context, result.artifact.text).passed


@pytest.fixture(scope='module')
def compound_unknown_context():
    return actual(request=compound_unknown_request())


@pytest.mark.parametrize('changed', [
    'また、先の回答時点では、「まだよく分からない」と書かれています。',
    'また、その時では、「まだよく分からない」と書かれています。',
    'また、「まだよく分からない」と書かれています。',
    'また、回答した時点では、「分からない」と書かれています。',
    'また、回答した時点では、「まだ分からない」と書かれています。',
    'また、回答した時点では、「まだよく分かった」と書かれています。',
    'また、回答した時点では、「まだよく分からなかった」と書かれています。',
    'また、回答した時点では、「友人はまだよく分からない」と書かれています。',
    'また、回答した時点では、「まだよく分からない」という気持ちが書かれています。',
    'その背景には、「まだよく分からない」という状態も重なっています。',
    'また、回答した時点では、「まだよく分からない」と誘われたことについて書かれています。',
    '褒められた回答した時点では、「まだよく分からない」と書かれています。',
    COMPOUND_STATE + 'そのため悲しかったのです。',
    COMPOUND_STATE + COMPOUND_STATE,
    '',
])
def test_compound_unknown_scope_changes_fail_without_authors(compound_unknown_context, changed):
    context = compound_unknown_context
    body = context[0].artifact.text
    assert COMPOUND_STATE in context[0].artifact.observation
    # A different answer retains the correct token on the same line, so a
    # line-wide presence check alone would wrongly accept missing attribution.
    assert body.replace(COMPOUND_STATE, '').split('Emlisから：')[0].count('回答した時点') >= 1
    assert not read_body(context, body.replace(COMPOUND_STATE, changed, 1)).passed


def test_compound_unknown_equivalent_ending_passes_without_authors(compound_unknown_context):
    body = compound_unknown_context[0].artifact.text
    assert read_body(compound_unknown_context, body.replace(COMPOUND_STATE,
        COMPOUND_STATE.replace('書かれています', '記されています'))).passed


@pytest.mark.parametrize('unknown,source', UNKNOWN_ANSWERS)
@pytest.mark.parametrize('second', ['その時は怖かった。', '今は怖い。'])
def test_compound_unknown_saved_withdrawal_preserves_original_and_reads(qcase, qdb, monkeypatch, unknown, source, second):
    user, parent, service = qcase
    first = current = run(service.start(user, parent))
    for index, text in enumerate((unknown, second, '「褒められた」は誤りです。')):
        if index:
            current = run(cont(service, user, current, f'compound-continue-{index}'))
        current = run(answer(service, user, current, text, f'compound-answer-{index}'))
        assert current['body_state'] == 'REFINED', current
        assert current['original'] == first['original']
        body = current['current_observation']['text']
        assert '誘われた' in body and '頼まれた' in body
        if index == 2:
            assert '褒められた' not in body
            assert f'回答した時点では、「{source}」と書かれています。' in body
            assert 'その時は嬉しくなかった' in body
            assert ('その時の受け止め' if second.startswith('その時') else '回答した時点の受け止め') in body
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved reads must not regenerate'))
            assert run(service.get(user, parent)) == current
            assert run(service.start(user, parent)) == current
# A negative original reaction and a detached answer may share a reception
# sentence only when each keeps its source and explicit occasion.
@pytest.mark.parametrize('unknown,source', (*UNKNOWN_ANSWERS,
    ('今は私にはまだよく分からない。', '私にはまだよく分からない')))
@pytest.mark.parametrize('positive', ['今は嬉しい。', 'その時は嬉しかった。'])
@pytest.mark.parametrize('reverse', [False, True])
def test_detached_burden_group_with_positive_retains_each_source(unknown, source, positive, reverse):
    context = actual(request=compound_unknown_request(unknown, positive, reverse))
    result, plan, _, resolver, selected = context
    body, follow = result.artifact.text, result.artifact.reception
    withdrawn = '誘われた' if reverse else '褒められた'
    assert withdrawn not in body
    assert ('その時は悲しかったし、' if reverse else 'その時は嬉しくなかったし、') in follow
    visible_source = source.replace('私には', 'あなたには')
    assert ('回答した時点で、' if source.startswith('私には') else '回答した時点では') + visible_source in follow
    assert ('その時は嬉しかった' if positive.startswith('その時') else '回答した時点では嬉しい') in follow
    assert '頼まれた' in follow and '寂し' in follow
    moves = plan.response_plan.human_reception_plan.moves
    assert len(moves) == 3
    group, = [m for m in moves if len(m.target_nucleus_ids) == 2 and not m.support_nucleus_ids]
    assert gate.read_source_owned_discourse(follow.split('。')[0] + '。', group, plan, resolver, selected)
    state, = [n for n in plan.nuclei if n.nucleus_id in group.target_nucleus_ids and n.kind == 'state']
    assert state.semantic_frame.modality == 'uncertain'
    assert not any(state.nucleus_id in (r.from_nucleus_id, r.to_nucleus_id) for r in plan.relations)
    assert read_body(context, body).passed


@pytest.fixture(scope='module')
def detached_burden_context():
    return actual(request=compound_unknown_request(second='今は嬉しい。'))


@pytest.mark.parametrize('old,new', [
    ('その時は嬉しくなかったし、', ''), ('回答した時点ではまだよく分からない', ''),
    ('嬉しくなかった', '嬉しかった'), ('嬉しくなかった', '嬉しくない'),
    ('まだよく分からない', 'よく分からない'), ('まだよく分からない', 'まだ分からない'),
    ('まだよく分からない', 'まだよく分かる'), ('まだよく分からない', '友人はまだよく分からない'),
    ('その時は', '今も'), ('回答した時点では', 'その時は'),
    ('回答した時点では', '先の回答時点では'), ('回答した時点では', ''),
    ('し、', 'から、'), ('し、', 'ので、'), ('し、', 'のに、'),
    ('し、', 'し、そのため'), ('し、', 'し、同じ出来事について'),
    ('その時は', '褒められたその時は'),
])
def test_detached_burden_mutations_fail_without_authors(detached_burden_context, old, new):
    context = detached_burden_context
    result = context[0]
    first, rest = result.artifact.reception.split('。', 1)
    changed = first.replace(old, new) + '。' + rest
    assert changed != result.artifact.reception
    assert not read_body(context, result.artifact.text.replace(result.artifact.reception, changed)).passed


@pytest.mark.parametrize('ending', ['のです。', 'のだと受け取りました。'])
def test_detached_burden_accepts_same_meaning_without_author_spelling(detached_burden_context, ending):
    body = detached_burden_context[0].artifact.text
    follow = detached_burden_context[0].artifact.reception.replace('のですね。', ending, 1)
    assert read_body(detached_burden_context, body.replace(detached_burden_context[0].artifact.reception, follow)).passed


@pytest.mark.parametrize('reverse', [False, True])
def test_detached_burden_saved_reads_preserve_body_and_original(qcase, qdb, monkeypatch, reverse):
    user, parent, service = qcase
    first = current = run(service.start(user, parent))
    answers = ('今は嬉しい。', COMPOUND_UNKNOWN) if reverse else (COMPOUND_UNKNOWN, '今は嬉しい。')
    for index, text in enumerate((*answers, '「誘われた」は誤りです。' if reverse else '「褒められた」は誤りです。')):
        if index:
            current = run(cont(service, user, current, f'detached-continue-{index}'))
        current = run(answer(service, user, current, text, f'detached-answer-{index}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        if index == 2:
            body = current['current_observation']['text']
            assert ('誘われた' if reverse else '褒められた') not in body
            assert '回答した時点ではまだよく分からない' in body
            assert ('その時は悲しかったし、' if reverse else 'その時は嬉しくなかったし、') in body
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved reads must not generate'))
            assert run(service.get(user, parent)) == current
            assert run(service.start(user, parent)) == current


@pytest.mark.parametrize('negative,clause', [
    ('その時は怖かった。', 'その時は怖かった'),
    ('今は少し怖い。', '回答した時点では少し怖い'),
])
def test_detached_burden_negative_answer_retains_degree_and_occasion(negative, clause):
    context = actual(request=compound_unknown_request(negative, '今は嬉しい。'))
    body = context[0].artifact.text
    assert f'その時は嬉しくなかったし、{clause}のですね。' in body
    assert read_body(context, body).passed
    assert not read_body(context, body.replace(clause, '回答した時点では怖い')).passed


@pytest.mark.parametrize('event', ['褒められた', '頼まれた'])
def test_detached_burden_does_not_drop_two_positive_duties_to_fit(event):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning, build_updated_grounded_plan
    from emlis_ai_grounded_observation_plan import GroundedObservationPlanError
    request = advance(advance(advance(begin(), '今は嬉しい。'), 'その時は嬉しかった。'), f'「{event}」は誤りです。')
    prepared = prepare_emlis_meaning(request)
    assert len(prepared.checkpoint.accepted_update_refs) == 3
    assert not {'answer:s7', 'answer:s8'} & set(prepared.checkpoint.inactive_claim_refs)
    with pytest.raises(GroundedObservationPlanError, match='human_reception_withdrawal_capacity_gap'):
        build_updated_grounded_plan(prepared)
    result = MeaningExperienceEngine().generate(request)
    assert result.artifact is None and result.reason_codes == ('emlis_refined_body_unavailable',)


@pytest.mark.parametrize('replacement', ['あなたは', '友人には', ''])
def test_detached_burden_self_case_cannot_be_changed_or_lost(replacement):
    context = actual(request=compound_unknown_request('今は私にはまだよく分からない。', '今は嬉しい。'))
    body = context[0].artifact.text
    assert 'あなたには' in body
    assert not read_body(context, body.replace('あなたには', replacement)).passed


TWO_POSITIVE_PAIRS = (
    ('今は嬉しい。', 'その時は楽しかった。'),
    ('その時は少し嬉しかった。', '今は楽しい。'),
)
ORIGINAL_EVENTS = ('褒められた', '誘われた', '頼まれた')


def two_positive_request(event='褒められた', answers=TWO_POSITIVE_PAIRS[0]):
    request = begin()
    for text in (*answers, f'「{event}」は誤りです。'):
        request = advance(request, text)
    return request


@pytest.mark.parametrize('event', ORIGINAL_EVENTS)
@pytest.mark.parametrize('answers', TWO_POSITIVE_PAIRS)
def test_two_positive_withdrawal_keeps_all_originals_and_answer_owners(event, answers):
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning
    request = two_positive_request(event, answers)
    context = actual(request=request)
    result, plan, _, _, _ = context
    body = result.artifact.text
    assert event not in body
    for surviving in set(ORIGINAL_EVENTS) - {event}:
        assert surviving in result.artifact.observation and surviving in result.artifact.reception
    for feeling in ('嬉しくなかった' if event == '褒められた' else '嬉しさにはつながらなかった', '悲し', '寂し'):
        assert feeling in result.artifact.reception
    for text in answers:
        when = 'その時は' if text.startswith('その時') else '回答した時点では'
        assert when + text.split('は', 1)[1][:-1] in result.artifact.reception
    moves = plan.response_plan.human_reception_plan.moves
    assert len(moves) == 3
    positive = [m for m in moves if m.reception_act == 'recognize_lived_change']
    assert {m.target_nucleus_ids for m in positive} == {('answer:s7',), ('answer:s8',)}
    detached_id = f'nucleus:s{ORIGINAL_EVENTS.index(event) + 1}:reaction'
    burden, = [m for m in moves if m.reception_act == 'stay_with_current_burden']
    assert detached_id in burden.target_nucleus_ids
    assert not any(detached_id in (r.from_nucleus_id, r.to_nucleus_id) for r in plan.relations)
    for source_event, answer_id in zip(ORIGINAL_EVENTS[:2], ('answer:s7', 'answer:s8')):
        links = [r for r in plan.relations if r.type == 'evaluation_about_event' and r.to_nucleus_id == answer_id]
        assert len(links) == (0 if source_event == event else 1)
        if links:
            assert links[0].from_nucleus_id == f'nucleus:s{ORIGINAL_EVENTS.index(source_event) + 1}:event'
    checkpoint = prepare_emlis_meaning(request).checkpoint
    assert len(checkpoint.accepted_update_refs) == 3
    assert not {'answer:s7', 'answer:s8', detached_id} & set(checkpoint.inactive_claim_refs)
    assert read_body(context, body).passed


@pytest.fixture(scope='module')
def two_positive_context():
    return actual(request=two_positive_request())


@pytest.mark.parametrize('old,new', [
    ('その時は嬉しくなかったのですね、また、', ''),
    ('その時は嬉しくなかった', 'その時は嬉しかった'),
    ('その時は嬉しくなかった', 'その時は嬉しくない'),
    ('その時は嬉しくなかった', '今は嬉しくなかった'),
    ('その時は嬉しくなかった', '回答した時点では嬉しくなかった'),
    ('その時は嬉しくなかった', '嬉しくなかった'),
    ('その時は嬉しくなかった', '友人はその時は嬉しくなかった'),
    ('その時は嬉しくなかった', '褒められたその時は嬉しくなかった'),
    ('、また、', 'ので、'), ('、また、', 'のに、'),
    ('、また、', '、また、そのため'),
    ('誘われたのに、悲しさを感じたのですね、また、', ''),
    ('誘われたことについて、その時は楽しかった', '頼まれたことについて、その時は楽しかった'),
    ('誘われたことについて、その時は楽しかった', '誘われたことのおかげで、その時は楽しかった'),
    ('その時は楽しかった', '回答した時点では楽しかった'),
    ('回答した時点では嬉しいのですね。', ''),
    ('回答した時点では嬉しい', 'その時は嬉しい'),
    ('回答した時点では嬉しい', '褒められたことについて、回答した時点では嬉しい'),
])
def test_two_positive_withdrawal_rejects_lost_or_reassigned_meaning_without_authors(two_positive_context, old, new):
    result = two_positive_context[0]
    follow = result.artifact.reception.replace(old, new, 1)
    assert follow != result.artifact.reception
    assert not read_body(two_positive_context, result.artifact.text.replace(result.artifact.reception, follow)).passed


def test_two_positive_withdrawal_accepts_equivalent_acknowledgement(two_positive_context):
    result = two_positive_context[0]
    follow = result.artifact.reception.replace('のですね、また、', 'のです、また、')
    assert follow != result.artifact.reception
    assert read_body(two_positive_context, result.artifact.text.replace(result.artifact.reception, follow)).passed


def test_two_positive_withdrawal_retains_answer_degree_without_authors():
    context = actual(request=two_positive_request(answers=TWO_POSITIVE_PAIRS[1]))
    result = context[0]
    follow = result.artifact.reception.replace('少し嬉しかった', '嬉しかった')
    assert follow != result.artifact.reception
    assert not read_body(context, result.artifact.text.replace(result.artifact.reception, follow)).passed


@pytest.mark.parametrize('mutation', ['time', 'polarity', 'modality', 'predicate', 'relation', 'governing', 'actor', 'quote', 'answer_slot'])
def test_two_positive_composite_ir_consumes_every_independent_slot(two_positive_context, mutation):
    _, plan, _, resolver, _ = two_positive_context
    rp = plan.response_plan.human_reception_plan
    group, = [m for m in rp.moves if m.reception_act == 'stay_with_current_burden']
    ir = reception._project_source_grounded_reception_move_realization(rp, group,
        {n.nucleus_id: n for n in plan.nuclei}, resolver,
        plan=plan, recovery_stage='full', clause_form='FINITE')
    reception._validate_source_grounded_move_ir(ir)
    if mutation == 'time': changed = replace(ir, time_scope='past')
    elif mutation == 'polarity': changed = replace(ir, polarity='neutral')
    elif mutation == 'modality': changed = replace(ir, modality='fact')
    elif mutation == 'predicate': changed = replace(ir, predicate_kind='event')
    elif mutation == 'relation': changed = replace(ir, relations=(replace(ir.relations[0], endpoint_slots=(0, 3)), *ir.relations[1:]))
    elif mutation == 'governing': changed = replace(ir, governing_relation_slots=(0,))
    elif mutation == 'answer_slot': changed = replace(ir, nominalization_plan=tuple(
        c.replace(':none:detached:none', ':none:detached:3:FINITE:answer_time') for c in ir.nominalization_plan))
    else:
        profile = replace(ir.semantic_profiles[0], **({'actor_kind': 'OTHER'} if mutation == 'actor' else {'quoted_boundary': True}))
        changed = replace(ir, semantic_profiles=(profile, *ir.semantic_profiles[1:]))
    with pytest.raises(reception.GroundedHumanReceptionSurfaceError):
        reception._validate_source_grounded_move_ir(changed)


@pytest.mark.parametrize('event', ORIGINAL_EVENTS)
def test_two_positive_withdrawal_saved_reads_keep_all_three_states(qcase, qdb, monkeypatch, event):
    user, parent, service = qcase
    first = current = run(service.start(user, parent))
    with monkeypatch.context() as saved:
        saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved initial reads must not generate'))
        assert run(service.get(user, parent)) == current
        assert run(service.start(user, parent)) == current
    for index, text in enumerate((*TWO_POSITIVE_PAIRS[0], f'「{event}」は誤りです。')):
        if index:
            current = run(cont(service, user, current, f'two-positive-continue-{index}'))
        current = run(answer(service, user, current, text, f'two-positive-answer-{index}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        if index == 2:
            body = current['current_observation']['text']
            assert event not in body
            assert '回答した時点では嬉しい' in body and 'その時は楽しかった' in body
            assert all(feeling in body for feeling in ('嬉しくなかった', '悲し', '寂し'))
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved reads must not generate'))
            assert run(service.get(user, parent)) == current
            assert run(service.start(user, parent)) == current


# Explicit correction invalidates the old contrast; the admitted replacement
# keeps its own original occasion without inheriting a new event relation.
def revised_original_request(source='苦しかった', answers=TWO_POSITIVE_PAIRS[0], old='嬉しくなかった'):
    request = begin()
    for text in (*answers, f'「{old}」ではなく「{source}」です。'):
        request = advance(request, text)
    return request


@pytest.mark.parametrize('answers', TWO_POSITIVE_PAIRS)
@pytest.mark.parametrize('source,finite', [
    ('苦しかった', '苦しかった'), ('少し苦しかった', '少し苦しかった'),
    ('私は苦しかったです', 'あなたは苦しかった'), ('怖くなかった', '怖くなかった'),
])
def test_revised_original_retains_both_positives_and_remaining_reactions(answers, source, finite):
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning
    request = revised_original_request(source, answers)
    context = actual(request=request)
    result, plan, _, _, _ = context
    assert f'その時の気持ちとして、「{source}」が見えます。' in result.artifact.observation
    assert f'その時は{finite}のですね。' in result.artifact.reception
    assert '嬉しくなかった' not in result.artifact.text
    assert all(s in result.artifact.reception for s in ('褒められた', '誘われた', '頼まれた', '悲し', '寂し'))
    moves = plan.response_plan.human_reception_plan.moves
    assert len(moves) == 3
    assert {m.target_nucleus_ids for m in moves if m.reception_act == 'recognize_lived_change'} == {('answer:s7',), ('answer:s8',)}
    for event, aid in (('nucleus:s1:event', 'answer:s7'), ('nucleus:s2:event', 'answer:s8')):
        assert any(r.type == 'evaluation_about_event' and (r.from_nucleus_id, r.to_nucleus_id) == (event, aid)
                   for r in plan.relations)
    replacement, = [n for n in plan.nuclei if n.nucleus_id == 'answer:s9']
    assert 'thread_subject:revised_original_reaction' in replacement.semantic_frame.attribute_codes
    assert 'thread_subject:withdrawn_source_event' not in replacement.semantic_frame.attribute_codes
    assert not any(replacement.nucleus_id in (r.from_nucleus_id, r.to_nucleus_id) for r in plan.relations)
    checkpoint = prepare_emlis_meaning(request).checkpoint
    assert len(checkpoint.accepted_update_refs) == 3
    assert {'nucleus:s1:reaction', 'relation:r1'} <= set(checkpoint.inactive_claim_refs)
    assert not {'answer:s7', 'answer:s8', 'answer:s9', 'nucleus:s1:event'} & set(checkpoint.inactive_claim_refs)
    assert read_body(context, result.artifact.text).passed


@pytest.fixture(scope='module')
def revised_original_context():
    return actual(request=revised_original_request())


@pytest.mark.parametrize('replacement', [
    'また、回答した時点の気持ちとして、「苦しかった」が見えます。',
    'また、先の回答時点の気持ちとして、「苦しかった」が見えます。',
    'また、気持ちとして、「苦しかった」が見えます。',
    'また、その時の気持ちとして、「苦しい」が見えます。',
    'また、その時の気持ちとして、「苦しくなかった」が見えます。',
    'また、その時の気持ちとして、「友人が苦しかった」が見えます。',
    'また、その時の気持ちとして、「嬉しくなかった」が見えます。',
    'その背景には、「苦しかった」という状態も重なっています。',
    '褒められたので、その時の気持ちとして、「苦しかった」が見えます。',
    'また、その時の気持ちとして、「苦しかった」が見えます。苦しさは誘われたことによるものです。',
    '苦しさは誘われたことによるものです。また、その時の気持ちとして、「苦しかった」が見えます。',
    '「誘われた」から「苦しかった」へつながっています。また、その時の気持ちとして、「苦しかった」が見えます。',
    'また、その時の気持ちとして、「苦しかった」が見えます。また、その時の気持ちとして、「苦しかった」が見えます。',
    '',
])
def test_revised_original_observation_owns_its_time_even_with_other_time_tokens(revised_original_context, replacement):
    body = revised_original_context[0].artifact.text
    original = 'また、その時の気持ちとして、「苦しかった」が見えます。'
    assert original in body
    assert not read_body(revised_original_context, body.replace(original, replacement, 1)).passed


@pytest.mark.parametrize('old,new', [
    ('その時は苦しかったのですね。', ''),
    ('その時は苦しかった', '回答した時点では苦しかった'),
    ('その時は苦しかった', '苦しかった'),
    ('その時は苦しかった', 'その時は苦しくなかった'),
    ('その時は苦しかった', 'その時は苦しい'),
    ('その時は苦しかった', 'その時は嬉しくなかった'),
    ('その時は苦しかった', 'その時は友人が苦しかった'),
    ('その時は苦しかった', '褒められたことについて、その時は苦しかった'),
    ('、また、', 'ので、'),
    ('誘われたのに、悲しさを感じたのですね、また、', ''),
    ('頼まれたのに、寂しさを感じたのですね、また、', ''),
    ('誘われたことについて、その時は楽しかったのですね。', ''),
    ('褒められたことについて、回答した時点では嬉しいのですね。', ''),
])
def test_revised_original_reception_rejects_missing_or_reassigned_duties(revised_original_context, old, new):
    result = revised_original_context[0]
    changed = result.artifact.reception.replace(old, new, 1)
    assert changed != result.artifact.reception
    assert not read_body(revised_original_context, result.artifact.text.replace(result.artifact.reception, changed)).passed


def test_revised_original_equivalent_endings_are_read_without_authors(revised_original_context):
    body = revised_original_context[0].artifact.text
    changed = body.replace('「苦しかった」が見えます。', '「苦しかった」が読み取れます。').replace('のですね、また、', 'のです、また、')
    assert read_body(revised_original_context, changed).passed


@pytest.mark.parametrize('mutation', ['time', 'polarity', 'actor', 'quote', 'relation', 'governing', 'answer_slot'])
def test_revised_original_composite_ir_keeps_replacement_independent(revised_original_context, mutation):
    _, plan, _, resolver, _ = revised_original_context
    rp = plan.response_plan.human_reception_plan
    move, = [m for m in rp.moves if m.reception_act == 'stay_with_current_burden']
    ir = reception._project_source_grounded_reception_move_realization(rp, move,
        {n.nucleus_id: n for n in plan.nuclei}, resolver,
        plan=plan, recovery_stage='full', clause_form='FINITE')
    reception._validate_source_grounded_move_ir(ir)
    marker, = [c for c in ir.nominalization_plan if ':none:replacement:none' in c]
    slot = int(marker.split(':')[1])
    if mutation == 'time': changed = replace(ir, time_scope='past')
    elif mutation == 'polarity': changed = replace(ir, polarity='neutral')
    elif mutation == 'relation': changed = replace(ir, relations=(replace(ir.relations[0], endpoint_slots=(0, slot)), *ir.relations[1:]))
    elif mutation == 'governing': changed = replace(ir, governing_relation_slots=())
    elif mutation == 'answer_slot': changed = replace(ir, nominalization_plan=tuple(
        c.replace(':none:replacement:none', ':none:replacement:0:FINITE:answer_time') for c in ir.nominalization_plan))
    else:
        profiles = tuple(replace(p, **({'actor_kind': 'OTHER'} if mutation == 'actor' else {'quoted_boundary': True}))
                         if i == slot else p for i, p in enumerate(ir.semantic_profiles))
        changed = replace(ir, semantic_profiles=profiles)
    assert changed != ir
    with pytest.raises(reception.GroundedHumanReceptionSurfaceError):
        reception._validate_source_grounded_move_ir(changed)


@pytest.mark.parametrize('answers', TWO_POSITIVE_PAIRS)
def test_revised_original_current_question_target_keeps_existing_about(answers):
    context = actual(request=revised_original_request(answers=answers, old='寂しかった'))
    result, plan, _, _, _ = context
    assert all(s in result.artifact.reception for s in ('褒められた', '誘われた', '頼まれた', '嬉し', '悲し', '苦し'))
    assert any(r.type == 'evaluation_about_event' and (r.from_nucleus_id, r.to_nucleus_id)
               == ('nucleus:s3:event', 'answer:s9') for r in plan.relations)
    assert not any('thread_subject:revised_original_reaction' in n.semantic_frame.attribute_codes for n in plan.nuclei)
    assert read_body(context, result.artifact.text).passed


@pytest.mark.parametrize('answers', TWO_POSITIVE_PAIRS)
def test_revised_original_second_position_keeps_existing_fragmentation_gap_visible(answers):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    result = MeaningExperienceEngine().generate(revised_original_request(answers=answers, old='悲しかった'))
    assert result.artifact is None and result.reason_codes == ('emlis_refined_body_unavailable',)


@pytest.mark.parametrize('answers', TWO_POSITIVE_PAIRS)
def test_revised_original_saved_reads_preserve_initial_and_all_answers(qcase, qdb, monkeypatch, answers):
    user, parent, service = qcase
    first = current = run(service.start(user, parent))
    with monkeypatch.context() as saved:
        saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved initial reads must not regenerate'))
        assert run(service.get(user, parent)) == current
        assert run(service.start(user, parent)) == current
    for index, text in enumerate((*answers, '「嬉しくなかった」ではなく「少し苦しかった」です。')):
        if index:
            current = run(cont(service, user, current, f'revised-original-continue-{index}'))
        current = run(answer(service, user, current, text, f'revised-original-answer-{index}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved reads must not regenerate'))
            assert run(service.get(user, parent)) == current
            assert run(service.start(user, parent)) == current
    body = current['current_observation']['text']
    assert 'その時の気持ちとして、「少し苦しかった」' in body and 'その時は少し苦しかった' in body
    assert all(s in body for s in ('褒められた', '誘われた', '頼まれた', '悲し', '寂し', '楽し'))
    assert '嬉しくなかった' not in body


def test_revised_original_can_be_corrected_again_without_reviving_old_relations():
    context = actual(request=advance(revised_original_request(answers=('今は嬉しい。',)),
        '「苦しかった」ではなく「少し怖かった」です。'))
    result, plan, _, _, _ = context
    assert '苦しかった' not in result.artifact.text and '嬉しくなかった' not in result.artifact.text
    assert 'その時の気持ちとして、「少し怖かった」' in result.artifact.observation
    assert '少し怖かった' in result.artifact.reception
    replacement, = [n for n in plan.nuclei if 'thread_subject:revised_original_reaction' in n.semantic_frame.attribute_codes]
    assert not any(replacement.nucleus_id in (r.from_nucleus_id, r.to_nucleus_id) for r in plan.relations)
    assert read_body(context, result.artifact.text).passed


@pytest.mark.parametrize('answers', TWO_POSITIVE_PAIRS)
@pytest.mark.parametrize('source', ['苦しかった', '少し苦しかった', '私は苦しかったです', '怖くなかった'])
def test_middle_revision_delivers_complete_contrasts_and_ordered_answer(answers, source):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning
    request = revised_original_request(source, answers, old='悲しかった')
    public = MeaningExperienceEngine().generate(request)
    assert public.artifact is not None, public.reason_codes
    context = actual(request=request)
    result, plan, sentence, _, _ = context
    assert result.artifact.text == public.artifact.text
    observation = result.artifact.observation
    assert observation.index('褒められた') < observation.index('誘われた') < observation.index('頼まれた')
    assert f'その時の気持ちとして、「{source}」が見えます。' in observation
    assert '悲しかった' not in result.artifact.text
    assert len([n for n in plan.nuclei if n.retention == 'required']) == 8
    assert len(plan.relations) == 4 and all(r.retention == 'required' for r in plan.relations)
    assert {(r.from_nucleus_id, r.to_nucleus_id) for r in plan.relations if r.type == 'contrast'} == {
        ('nucleus:s1:event', 'nucleus:s1:reaction'), ('nucleus:s3:event', 'nucleus:s3:reaction')}
    assert {(r.from_nucleus_id, r.to_nucleus_id) for r in plan.relations if r.type == 'evaluation_about_event'} == {
        ('nucleus:s1:event', 'answer:s7'), ('nucleus:s2:event', 'answer:s8')}
    relation_lines = [line for line in sentence.lines if line.binding.relation_ids]
    assert len(relation_lines) == 1
    assert set(relation_lines[0].binding.relation_ids) == {r.relation_id for r in plan.relations}
    assert 'answer:s9' not in relation_lines[0].binding.nucleus_ids
    assert not any('semantic_arc_fragment:justified' in line.binding.functional_atom_ids for line in sentence.lines)
    assert len(plan.response_plan.human_reception_plan.moves) == 3
    checkpoint = prepare_emlis_meaning(request).checkpoint
    assert len(checkpoint.accepted_update_refs) == 3
    assert {'nucleus:s2:reaction', 'relation:r2'} <= set(checkpoint.inactive_claim_refs)
    assert not {'answer:s7', 'answer:s8', 'answer:s9', 'nucleus:s2:event'} & set(checkpoint.inactive_claim_refs)
    assert read_body(context, result.artifact.text).passed


@pytest.fixture(scope='module')
def middle_revision_context():
    return actual(request=revised_original_request(answers=TWO_POSITIVE_PAIRS[1], old='悲しかった'))


@pytest.mark.parametrize('old,new', [
    ('「嬉しくなかった」', '「嬉しかった」'),
    ('「少し嬉しかった」', '「嬉しかった」'),
    ('「少し嬉しかった」', '「少し嬉しい」'),
    ('「楽しい」', '「友人は楽しい」'),
    ('「楽しい」', '「楽しくない」'),
    ('「寂しかった」', '「寂しくなかった」'),
    ('その出来事に対するその時の', 'その出来事に対する回答した時点の'),
    ('「誘われた」ことに対する回答した時点の', '「誘われた」ことに対するその時の'),
    ('「誘われた」ことに対する', '「頼まれた」ことに対する'),
    ('「誘われた」ことに対する', '「誘われた」ことのおかげで'),
    ('その時の気持ちとして、「苦しかった」', '回答した時点の気持ちとして、「苦しかった」'),
    ('その時の気持ちとして、「苦しかった」', '気持ちとして、「苦しかった」'),
    ('その時の気持ちとして、「苦しかった」', 'その時の気持ちとして、「悲しかった」'),
    ('その時の気持ちとして、「苦しかった」', '誘われたので、その時の気持ちとして、「苦しかった」'),
    ('その時の気持ちとして、「苦しかった」が見えます。', ''),
    ('「誘われた」ことに対する回答した時点の受け止めとして、「楽しい」が見えます。', ''),
    ('「頼まれた」と「寂しかった」が、異なる向きのまま同時にあります。', ''),
    ('その時の気持ちとして、「苦しかった」が見えます。',
     'その時の気持ちとして、「苦しかった」が見えます。苦しさは誘われたことによるものです。'),
])
def test_middle_revision_rejects_observation_meaning_changes_without_authors(middle_revision_context, old, new):
    result = middle_revision_context[0]
    changed = result.artifact.observation.replace(old, new, 1)
    assert changed != result.artifact.observation
    body = result.artifact.text.replace(result.artifact.observation, changed, 1)
    assert not read_body(middle_revision_context, body).passed


def test_middle_revision_accepts_equivalent_reception_ending(middle_revision_context):
    body = middle_revision_context[0].artifact.text
    changed = body.replace('のですね、また、', 'のです、また、')
    assert changed != body and read_body(middle_revision_context, changed).passed


@pytest.mark.parametrize('answers', TWO_POSITIVE_PAIRS)
def test_middle_revision_saved_reads_preserve_initial_and_all_answers(qcase, qdb, monkeypatch, answers):
    user, parent, service = qcase
    first = current = run(service.start(user, parent))
    for index, text in enumerate((None, *answers, '「悲しかった」ではなく「少し苦しかった」です。')):
        if text is not None:
            if index > 1:
                current = run(cont(service, user, current, f'middle-revision-continue-{index}'))
            current = run(answer(service, user, current, text, f'middle-revision-answer-{index}'))
            assert current['body_state'] == 'REFINED'
        assert current['original'] == first['original']
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved reads must not regenerate'))
            assert run(service.get(user, parent)) == current
            assert run(service.start(user, parent)) == current
    body = current['current_observation']['text']
    assert '悲しかった' not in body
    assert 'その時の気持ちとして、「少し苦しかった」' in body
    assert all(s in body for s in ('褒められた', '誘われた', '頼まれた', '嬉し', '寂し', '楽し'))


# A revision of the current question target owns a real ABOUT relation. It
# must not require (or receive) independent-replacement provenance to join
# the surrounding source-proven contrasts in one observation.
@pytest.mark.parametrize('positive', ['今は嬉しい。', 'その時は少し嬉しかった。'])
@pytest.mark.parametrize('source', ['苦しかった', '少し苦しかった', '私は苦しかったです', '怖くなかった'])
def test_current_focus_revision_keeps_about_and_surviving_meaning(positive, source):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning
    request = revised_original_request(source, (positive,), old='悲しかった')
    public = MeaningExperienceEngine().generate(request)
    assert public.artifact is not None, public.reason_codes
    context = actual(request=request)
    result, plan, sentence, _, _ = context
    assert result.artifact.text == public.artifact.text
    body = result.artifact.text
    observation = result.artifact.observation
    assert observation.index('褒められた') < observation.index('誘われた') < observation.index('頼まれた')
    assert f'「誘われた」ことに対するその時の受け止めとして、「{source}」' in observation
    assert '悲しかった' not in body
    assert all(s in body for s in ('嬉しくなかった', '寂しかった', source))
    assert all(s in result.artifact.reception for s in ('褒められた', '誘われた', '頼まれた'))
    assert '少し嬉しかった' in body if '少し' in positive else '回答した時点では嬉しい' in body
    assert len([n for n in plan.nuclei if n.retention == 'required']) == 7
    assert len(plan.relations) == 4 and all(r.retention == 'required' for r in plan.relations)
    assert {(r.from_nucleus_id, r.to_nucleus_id) for r in plan.relations if r.type == 'contrast'} == {
        ('nucleus:s1:event', 'nucleus:s1:reaction'), ('nucleus:s3:event', 'nucleus:s3:reaction')}
    assert {(r.from_nucleus_id, r.to_nucleus_id) for r in plan.relations if r.type == 'evaluation_about_event'} == {
        ('nucleus:s1:event', 'answer:s7'), ('nucleus:s2:event', 'answer:s8')}
    assert not any('thread_subject:revised_original_reaction' in n.semantic_frame.attribute_codes
                   or 'thread_subject:withdrawn_source_event' in n.semantic_frame.attribute_codes for n in plan.nuclei)
    lines = [line for line in sentence.lines if line.binding.line_role != 'human_follow']
    assert len(lines) == 1 and set(lines[0].binding.relation_ids) == {r.relation_id for r in plan.relations}
    assert not any('semantic_arc_fragment:justified' in line.binding.functional_atom_ids for line in sentence.lines)
    assert len(plan.response_plan.human_reception_plan.moves) == 2
    checkpoint = prepare_emlis_meaning(request).checkpoint
    assert len(checkpoint.accepted_update_refs) == 2
    assert {'nucleus:s2:reaction', 'relation:r2'} <= set(checkpoint.inactive_claim_refs)
    assert not {'answer:s7', 'answer:s8', 'nucleus:s2:event'} & set(checkpoint.inactive_claim_refs)
    assert read_body(context, body).passed


@pytest.fixture(scope='module')
def current_focus_revision_context():
    return actual(request=revised_original_request('少し怖くなかった', ('今は嬉しい。',), old='悲しかった'))


@pytest.mark.parametrize('old,new', [
    ('「嬉しくなかった」', '「嬉しかった」'),
    ('「寂しかった」', '「寂しくなかった」'),
    ('「嬉しい」', '「友人は嬉しい」'),
    ('「少し怖くなかった」', '「少し怖かった」'),
    ('「少し怖くなかった」', '「怖くなかった」'),
    ('「少し怖くなかった」', '「少し怖くない」'),
    ('「少し怖くなかった」', '「悲しかった」'),
    ('「誘われた」ことに対するその時の', '「頼まれた」ことに対するその時の'),
    ('「誘われた」ことに対するその時の', '「誘われた」ことに対する回答した時点の'),
    ('「誘われた」ことに対するその時の', '「誘われた」ことに対する'),
    ('「誘われた」ことに対する', '「誘われた」ことのせいで'),
    ('「誘われた」ことに対するその時の受け止めとして、「少し怖くなかった」が見えます。', ''),
    ('「頼まれた」と「寂しかった」が、異なる向きのまま同時にあります。', ''),
    ('回答した時点では嬉しいのですね。', 'その時は嬉しかったのですね。'),
    ('誘われた時は、少し怖くなく', '誘われた時は、少し怖く'),
    ('誘われた時は、少し怖くなく、', ''),
])
def test_current_focus_revision_rejects_body_mutations_without_authors(current_focus_revision_context, old, new):
    body = current_focus_revision_context[0].artifact.text
    changed = body.replace(old, new, 1)
    assert changed != body
    assert not read_body(current_focus_revision_context, changed).passed


def test_current_focus_revision_reads_equivalent_reception_without_authors(current_focus_revision_context):
    body = current_focus_revision_context[0].artifact.text
    changed = body.replace('のですね。', 'のです。')
    assert changed != body and read_body(current_focus_revision_context, changed).passed


@pytest.mark.parametrize('last,final_state', [
    ('「苦しかった」ではなく「少し怖かった」です。', 'REFINED'),
    # Withdrawing the newly reachable replacement still leaves a bare event
    # between the contrasts. Preserve this unresolved gap and no-stale-body
    # storage behavior; do not claim that the ABOUT composition fixes it.
    ('「苦しかった」は誤りです。', 'MEANING_UPDATED_BODY_UNAVAILABLE'),
])
def test_current_focus_revision_saved_recorrection_and_known_withdrawal_gap(qcase, qdb, monkeypatch, last, final_state):
    user, parent, service = qcase
    first = current = run(service.start(user, parent))
    sequence = ('今は嬉しい。', '「悲しかった」ではなく「苦しかった」です。', last)
    for index, text in enumerate((None, *sequence)):
        if text is not None:
            if index > 1:
                current = run(cont(service, user, current, f'current-focus-continue-{index}'))
            current = run(answer(service, user, current, text, f'current-focus-answer-{index}'))
            assert current['body_state'] == (final_state if index == 3 else 'REFINED'), current
        assert current['original'] == first['original']
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved reads must not regenerate'))
            assert run(service.get(user, parent)) == current
            assert run(service.start(user, parent)) == current
        if index == 2:
            body = current['current_observation']['text']
            assert '悲しかった' not in body
            assert '「誘われた」ことに対するその時の受け止めとして、「苦しかった」' in body
    if final_state == 'MEANING_UPDATED_BODY_UNAVAILABLE':
        assert current['current_observation'] is None
        assert current['answer_saved'] and current['meaning_updated']
        assert current['state'] == 'RESPONSE_FAILED'
        return
    body = current['current_observation']['text']
    assert '苦しかった' not in body and '悲しかった' not in body
    assert all(s in body for s in ('褒められた', '誘われた', '頼まれた', '嬉しくなかった', '寂しかった'))
    assert '回答した時点では嬉しい' in body
    if '少し' in last:
        assert '少し怖かった' in body


def withdrawn_current_focus_request(positive='今は嬉しい。', order=None):
    pairs = order or (('褒められた', '嬉しくなかった'), ('誘われた', '悲しかった'), ('頼まれた', '寂しかった'))
    request = begin(''.join(f'{event}のに、{reaction}。' for event, reaction in pairs))
    for text in (positive, f'「{pairs[1][1]}」ではなく「苦しかった」です。', '「苦しかった」は誤りです。'):
        request = advance(request, text)
    return request


from itertools import permutations


@pytest.mark.parametrize('positive', ['今は嬉しい。', 'その時は少し嬉しかった。'])
@pytest.mark.parametrize('order', tuple(permutations((
    ('褒められた', '嬉しくなかった'), ('誘われた', '悲しかった'), ('頼まれた', '寂しかった')))))
def test_withdrawn_current_focus_keeps_independent_event_in_source_order(positive, order):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning
    request = withdrawn_current_focus_request(positive, order)
    public = MeaningExperienceEngine().generate(request)
    assert public.artifact is not None, public.reason_codes
    context = actual(request=request)
    result, plan, sentence, _, _ = context
    assert public.artifact.text == result.artifact.text
    body, observation = result.artifact.text, result.artifact.observation
    assert observation.index(order[0][0]) < observation.index(order[1][0]) < observation.index(order[2][0])
    assert f'「{order[1][0]}」という出来事がありました。' in observation
    assert order[1][1] not in body and '苦しかった' not in body
    assert all(value in observation for value in (*order[0], *order[2]))
    assert ('その時の受け止めとして、「少し嬉しかった」' if '少し' in positive
            else '回答した時点の受け止めとして、「嬉しい」') in observation
    assert len(plan.coverage_requirements.required_nucleus_ids) == 6
    assert len(plan.relations) == 3
    assert not any('nucleus:s2:event' in (r.from_nucleus_id, r.to_nucleus_id) for r in plan.relations)
    assert len(plan.response_plan.human_reception_plan.moves) == 2
    lines = [line for line in sentence.lines if line.binding.line_role != 'human_follow']
    assert len(lines) == 1 and 'nucleus:s2:event' in lines[0].binding.nucleus_ids
    assert not any('semantic_arc_fragment:justified' in line.binding.functional_atom_ids for line in sentence.lines)
    checkpoint = prepare_emlis_meaning(request).checkpoint
    assert {'nucleus:s2:reaction', 'answer:s8', 'relation:r2'} <= set(checkpoint.inactive_claim_refs)
    assert 'nucleus:s2:event' not in checkpoint.inactive_claim_refs
    assert read_body(context, body).passed


@pytest.fixture(scope='module')
def withdrawn_current_focus_context():
    return actual(request=withdrawn_current_focus_request('その時は少し嬉しかった。'))


@pytest.mark.parametrize('replacement', [
    '',
    '「頼まれた」という出来事がありました。',
    '「友人が誘われた」という出来事がありました。',
    '「誘われなかった」という出来事がありました。',
    '「誘われる」という出来事がありました。',
    '「誘われた」という出来事があります。',
    'その出発点には、「誘われた」という出来事がありました。',
    '「誘われた」ために、苦しかったのですね。',
    '「誘われた」という出来事がありました。悲しかったのですね。',
    '「誘われた」という出来事がありました。苦しかったのですね。',
    '「誘われた」という出来事がありました。感情はありません。',
    '誘われたことが苦しさの原因です。「誘われた」という出来事がありました。',
    '「誘われた」という出来事がありました。「誘われた」という出来事がありました。',
])
def test_withdrawn_current_focus_rejects_event_corruption_without_authors(withdrawn_current_focus_context, replacement):
    context = withdrawn_current_focus_context
    body = context[0].artifact.text
    changed = body.replace('「誘われた」という出来事がありました。', replacement, 1)
    assert changed != body
    with patch.object(surface, '_render_relation', side_effect=AssertionError('no relation oracle')), patch.object(
            surface, '_render_observation_with_relations', side_effect=AssertionError('no line oracle')):
        report = read_body(context, changed)
    assert not report.passed
    assert any('body_inverse_independent_event_scope_mismatch' in reason for reason in report.failure_codes)


@pytest.mark.parametrize('edge', ['start', 'end'])
def test_withdrawn_current_focus_rejects_moved_event(withdrawn_current_focus_context, edge):
    context = withdrawn_current_focus_context
    original = context[0].artifact.observation
    fact = '「誘われた」という出来事がありました。'
    remaining = original.replace(fact, '').strip()
    changed = (fact + ' ' + remaining) if edge == 'start' else (remaining + ' ' + fact)
    assert changed != original
    assert not read_body(context, context[0].artifact.text.replace(original, changed)).passed


@pytest.mark.parametrize('field,value', [('actor', 'other_person'), ('time_scope', 'present'), ('modality', 'uncertain')])
def test_withdrawn_current_focus_independent_inverse_requires_past_fact(withdrawn_current_focus_context, field, value):
    result, plan, sentence, resolver, selected = withdrawn_current_focus_context
    nuclei = tuple(replace(n, semantic_frame=replace(n.semantic_frame, **{field: value}))
                   if n.nucleus_id == 'nucleus:s2:event' else n for n in plan.nuclei)
    changed = (result, replace(plan, nuclei=nuclei), sentence, resolver, selected)
    assert not read_body(changed, result.artifact.text).passed


def test_withdrawn_current_focus_accepts_equivalent_reception(withdrawn_current_focus_context):
    context = withdrawn_current_focus_context
    body = context[0].artifact.text
    changed = body.replace('のですね。', 'のです。')
    assert changed != body and read_body(context, changed).passed


@pytest.mark.parametrize('tail', ['が、誘われたせいです。', 'が、誘われたときは苦しかったのですね。'])
def test_withdrawn_current_focus_rejects_extra_clause_in_neighbor(withdrawn_current_focus_context, tail):
    context = withdrawn_current_focus_context
    body = context[0].artifact.text
    changed = body.replace('異なる向きのまま同時にあります。', '異なる向きのまま同時にあります' + tail)
    assert changed != body and not read_body(context, changed).passed


@pytest.mark.parametrize('positive', ['今は嬉しい。', 'その時は少し嬉しかった。'])
def test_withdrawn_current_focus_saves_restored_body_and_unchanged_original(qcase, qdb, monkeypatch, positive):
    user, parent, service = qcase
    first = current = run(service.start(user, parent))
    for i, text in enumerate((None, positive, '「悲しかった」ではなく「苦しかった」です。', '「苦しかった」は誤りです。')):
        if text is not None:
            if i > 1:
                current = run(cont(service, user, current, f'withdrawn-current-continue-{i}'))
            current = run(answer(service, user, current, text, f'withdrawn-current-answer-{i}'))
            assert current['body_state'] == 'REFINED', current
        assert current['original'] == first['original']
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved read must not regenerate'))
            assert run(service.get(user, parent)) == current
            assert run(service.start(user, parent)) == current
    body = current['current_observation']['text']
    assert '「誘われた」という出来事がありました。' in body
    assert '悲しかった' not in body and '苦しかった' not in body
    assert all(s in body for s in ('褒められた', '嬉しくなかった', '頼まれた', '寂しかった'))
