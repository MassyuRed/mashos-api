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
    assert f'「{source}」と、当時の気持ちを言い直されています。' in result.artifact.observation
    assert '言い直してくださった気持ちについては、' + ('当時、' if source.startswith('私') else '当時は') + finite + 'のですね。' in result.artifact.reception
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
    'また、「苦しかった」と、回答した時点の気持ちを言い直されています。',
    'また、「苦しかった」と、先の回答時点の気持ちを言い直されています。',
    'また、「苦しかった」と、気持ちを言い直されています。',
    'また、「苦しい」と、当時の気持ちを言い直されています。',
    'また、「苦しくなかった」と、当時の気持ちを言い直されています。',
    'また、「友人が苦しかった」と、当時の気持ちを言い直されています。',
    'また、「嬉しくなかった」と、当時の気持ちを言い直されています。',
    'その背景には、「苦しかった」という状態も重なっています。',
    '褒められたので、「苦しかった」と、当時の気持ちを言い直されています。',
    'また、「苦しかった」と、当時の気持ちを言い直されています。苦しさは誘われたことによるものです。',
    '苦しさは誘われたことによるものです。また、「苦しかった」と、当時の気持ちを言い直されています。',
    '「誘われた」から「苦しかった」へつながっています。また、「苦しかった」と、当時の気持ちを言い直されています。',
    'また、「苦しかった」と、当時の気持ちを言い直されています。また、「苦しかった」と、当時の気持ちを言い直されています。',
    '',
])
def test_revised_original_observation_owns_its_time_even_with_other_time_tokens(revised_original_context, replacement):
    body = revised_original_context[0].artifact.text
    original = 'また、「苦しかった」と、当時の気持ちを言い直されています。'
    assert original in body
    assert not read_body(revised_original_context, body.replace(original, replacement, 1)).passed


@pytest.mark.parametrize('old,new', [
    ('言い直してくださった気持ちについては、当時は苦しかったのですね。', ''),
    ('言い直してくださった気持ちについては、当時は苦しかった', '言い直してくださった気持ちについては、回答した時点では苦しかった'),
    ('言い直してくださった気持ちについては、当時は苦しかった', '言い直してくださった気持ちについては、苦しかった'),
    ('言い直してくださった気持ちについては、当時は苦しかった', '言い直してくださった気持ちについては、当時は苦しくなかった'),
    ('言い直してくださった気持ちについては、当時は苦しかった', '言い直してくださった気持ちについては、当時は苦しい'),
    ('言い直してくださった気持ちについては、当時は苦しかった', '言い直してくださった気持ちについては、当時は嬉しくなかった'),
    ('言い直してくださった気持ちについては、当時は苦しかった', '言い直してくださった気持ちについては、当時は友人が苦しかった'),
    ('言い直してくださった気持ちについては、当時は苦しかった', '褒められたことについて、言い直してくださった気持ちについては、当時は苦しかった'),
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
    changed = body.replace('言い直されています。', '言い換えられています。').replace('のですね、また、', 'のです、また、')
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
    assert '「少し苦しかった」と、当時の気持ちを言い直されています' in body and '言い直してくださった気持ちについては、当時は少し苦しかった' in body
    assert all(s in body for s in ('褒められた', '誘われた', '頼まれた', '悲し', '寂し', '楽し'))
    assert '嬉しくなかった' not in body


def test_revised_original_can_be_corrected_again_without_reviving_old_relations():
    context = actual(request=advance(revised_original_request(answers=('今は嬉しい。',)),
        '「苦しかった」ではなく「少し怖かった」です。'))
    result, plan, _, _, _ = context
    assert '苦しかった' not in result.artifact.text and '嬉しくなかった' not in result.artifact.text
    assert '「少し怖かった」と、当時の気持ちを言い直されています' in result.artifact.observation
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
    assert f'「{source}」と、当時の気持ちを言い直されています。' in observation
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
    ('「苦しかった」と、当時の気持ちを言い直されています', '「苦しかった」と、回答した時点の気持ちを言い直されています'),
    ('「苦しかった」と、当時の気持ちを言い直されています', '「苦しかった」と、気持ちを言い直されています'),
    ('「苦しかった」と、当時の気持ちを言い直されています', '「悲しかった」と、当時の気持ちを言い直されています'),
    ('「苦しかった」と、当時の気持ちを言い直されています', '誘われたので、「苦しかった」と、当時の気持ちを言い直されています'),
    ('「苦しかった」と、当時の気持ちを言い直されています。', ''),
    ('「誘われた」ことに対する回答した時点の受け止めとして、「楽しい」が見えます。', ''),
    ('「頼まれた」と「寂しかった」が、異なる向きのまま同時にあります。', ''),
    ('「苦しかった」と、当時の気持ちを言い直されています。',
     '「苦しかった」と、当時の気持ちを言い直されています。苦しさは誘われたことによるものです。'),
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
    assert '「少し苦しかった」と、当時の気持ちを言い直されています' in body
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


@pytest.mark.parametrize('answers', [(), ('今は嬉しい。',), ('その時は少し嬉しかった。',)])
@pytest.mark.parametrize('source', ['苦しかった', '少し苦しかった', '私は苦しかったです', '怖くなかった'])
def test_third_original_revision_preserves_separate_event_and_past_feeling(answers, source):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning
    request = revised_original_request(source, answers, old='寂しかった')
    public = MeaningExperienceEngine().generate(request)
    assert public.artifact is not None, public.reason_codes
    context = actual(request=request)
    result, plan, sentence, _, _ = context
    assert result.artifact.text == public.artifact.text
    body = result.artifact.text
    lines = result.artifact.observation.splitlines()
    assert len(lines) == 3
    assert lines[1] == '「頼まれた」という出来事がありました。'
    assert lines[2] == f'「{source}」と、当時の気持ちを言い直されています。'
    assert all(value in lines[0] for value in ('褒められた', '嬉しくなかった', '誘われた', '悲しかった'))
    assert '寂しかった' not in body and '一つの流れ' not in body
    assert '出発点' not in body and '今回の中心' not in body
    assert len(plan.coverage_requirements.required_nucleus_ids) == 6 + len(answers)
    assert len(plan.relations) == 2 + len(answers)
    replacement, = [n for n in plan.nuclei if 'thread_subject:revised_original_reaction' in n.semantic_frame.attribute_codes]
    assert not any({r.from_nucleus_id, r.to_nucleus_id} & {'nucleus:s3:event', replacement.nucleus_id}
                   for r in plan.relations)
    assert len(plan.response_plan.human_reception_plan.moves) == 2 + len(answers)
    observation_lines = [row for row in sentence.lines if row.binding.line_role != 'human_follow']
    assert len(observation_lines) == 3
    assert observation_lines[1].binding.nucleus_ids == ('nucleus:s3:event',)
    assert observation_lines[2].binding.nucleus_ids == (replacement.nucleus_id,)
    assert not any('semantic_arc_fragment:justified' in row.binding.functional_atom_ids for row in sentence.lines)
    checkpoint = prepare_emlis_meaning(request).checkpoint
    assert {'nucleus:s3:reaction', 'relation:r3'} <= set(checkpoint.inactive_claim_refs)
    assert 'nucleus:s3:event' not in checkpoint.inactive_claim_refs
    if answers:
        assert ('その時の受け止めとして、「少し嬉しかった」' if '少し' in answers[0]
                else '回答した時点の受け止めとして、「嬉しい」') in lines[0]
    assert read_body(context, body).passed


@pytest.fixture(scope='module')
def third_original_revision_context():
    return actual(request=revised_original_request('少し怖くなかった', ('今は嬉しい。',), old='寂しかった'))


@pytest.mark.parametrize('old,new', [
    ('「頼まれた」という出来事がありました。', ''),
    ('「頼まれた」という出来事がありました。', '「誘われた」という出来事がありました。'),
    ('「頼まれた」という出来事がありました。', '「友人が頼まれた」という出来事がありました。'),
    ('「頼まれた」という出来事がありました。', '「頼まれなかった」という出来事がありました。'),
    ('「頼まれた」という出来事がありました。', '「頼まれる」という出来事がありました。'),
    ('という出来事がありました。', 'という出来事があります。'),
    ('「頼まれた」という出来事がありました。', '今回の中心には、「頼まれた」があります。'),
    ('「頼まれた」という出来事がありました。', 'その出発点には、「頼まれた」という出来事がありました。'),
    ('「頼まれた」という出来事がありました。', '「頼まれた」という出来事がありました。寂しかったのですね。'),
    ('「頼まれた」という出来事がありました。', '「頼まれた」という出来事がありましたが、それが苦しさの原因です。'),
    ('「少し怖くなかった」と、当時の気持ちを言い直されています', '「少し怖くなかった」と、回答した時点の気持ちを言い直されています'),
    ('「少し怖くなかった」と、当時の気持ちを言い直されています', '「怖くなかった」と、当時の気持ちを言い直されています'),
    ('「少し怖くなかった」と、当時の気持ちを言い直されています', '「少し怖かった」と、当時の気持ちを言い直されています'),
    ('「少し怖くなかった」と、当時の気持ちを言い直されています', '「寂しかった」と、当時の気持ちを言い直されています'),
    ('「少し怖くなかった」と、当時の気持ちを言い直されています', '頼まれたので、「少し怖くなかった」と、当時の気持ちを言い直されています'),
    ('「嬉しくなかった」', '「嬉しかった」'),
    ('「悲しかった」', '「悲しくなかった」'),
    ('その出来事に対する回答した時点の', 'その出来事に対するその時の'),
])
def test_third_original_revision_rejects_body_corruption_without_authors(third_original_revision_context, old, new):
    context = third_original_revision_context
    body = context[0].artifact.text
    changed = body.replace(old, new, 1)
    assert changed != body
    with patch.object(surface, '_render_relation', side_effect=AssertionError('no relation oracle')):
        assert not read_body(context, changed).passed


@pytest.mark.parametrize('field,value', [('actor', 'other_person'), ('time_scope', 'present'), ('modality', 'uncertain')])
def test_third_original_revision_requires_original_event_fact(third_original_revision_context, field, value):
    result, plan, sentence, resolver, selected = third_original_revision_context
    nuclei = tuple(replace(n, semantic_frame=replace(n.semantic_frame, **{field: value}))
                   if n.nucleus_id == 'nucleus:s3:event' else n for n in plan.nuclei)
    context = result, replace(plan, nuclei=nuclei), sentence, resolver, selected
    assert not read_body(context, result.artifact.text).passed


def test_third_original_revision_accepts_equivalent_feeling_ending(third_original_revision_context):
    context = third_original_revision_context
    body = context[0].artifact.text
    changed = body.replace('言い直されています。', '言い換えられています。')
    assert changed != body and read_body(context, changed).passed


@pytest.mark.parametrize('positive', ['今は嬉しい。', 'その時は少し嬉しかった。'])
def test_third_original_revision_saves_body_and_unchanged_original(qcase, qdb, monkeypatch, positive):
    user, parent, service = qcase
    first = current = run(service.start(user, parent))
    for i, text in enumerate((None, positive, '「寂しかった」ではなく「苦しかった」です。')):
        if text is not None:
            if i > 1:
                current = run(cont(service, user, current, f'third-revision-continue-{i}'))
            current = run(answer(service, user, current, text, f'third-revision-answer-{i}'))
            assert current['body_state'] == 'REFINED', current
        assert current['original'] == first['original']
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved read must not regenerate'))
            assert run(service.get(user, parent)) == current
            assert run(service.start(user, parent)) == current
    body = current['current_observation']['text']
    assert '「頼まれた」という出来事がありました。' in body
    assert '「苦しかった」と、当時の気持ちを言い直されています' in body
    assert '寂しかった' not in body
    assert all(s in body for s in ('褒められた', '嬉しくなかった', '誘われた', '悲しかった'))
    assert ('その時の受け止めとして、「少し嬉しかった」' if '少し' in positive
            else '回答した時点の受け止めとして、「嬉しい」') in body
    assert not current['can_continue']


@pytest.mark.parametrize('answers', [(), ('今は嬉しい。',)])
@pytest.mark.parametrize('source,finite', [
    ('苦しかったです', '言い直してくださった気持ちについては、当時は苦しかった'),
    ('私は苦しかったです', '言い直してくださった気持ちについては、当時、あなたは苦しかった'),
    ('私も少し怖くなかったです', '言い直してくださった気持ちについては、当時、あなたも少し怖くなかった'),
    ('少し私は苦しかったです', '言い直してくださった気持ちについては、当時、あなたは少し苦しかった'),
    ('私にはとても苦しかったです', '言い直してくださった気持ちについては、当時、あなたにはとても苦しかった'),
])
def test_revised_finite_reception_preserves_speaker_particle_degree_and_past(answers, source, finite):
    context = actual(request=revised_original_request(source, answers, old='寂しかった'))
    result, plan, _, _, _ = context
    follow = result.artifact.reception
    assert follow.startswith(finite + 'のですね。')
    assert 'これまで' not in follow and 'ですこと' not in follow
    assert all(s in result.artifact.text for s in ('褒められた', '嬉しくなかった', '誘われた', '悲しかった'))
    assert f'「{source}」と、当時の気持ちを言い直されています' in result.artifact.observation
    assert len(plan.response_plan.human_reception_plan.moves) == 2 + len(answers)
    assert read_body(context, result.artifact.text).passed


@pytest.mark.parametrize('answers', [(), ('今は嬉しい。',)])
def test_revised_finite_reception_does_not_admit_unsupported_replacement(answers):
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning
    request = revised_original_request('僕にもあまり嬉しくなかったです', answers, old='寂しかった')
    prepared = prepare_emlis_meaning(request)
    assert not prepared.accepted_nuclei
    assert prepared.checkpoint.assessment_status == 'PARTIAL'
    assert any(p.reason_code == 'correction_replacement_unsupported'
               for p in prepared.checkpoint.unresolved_parts)
    context = actual(request=request)
    assert '今回の観測に反映できていない部分があります' in context[0].artifact.observation
    assert '嬉しくなかったです' not in context[0].artifact.reception
    assert read_body(context, context[0].artifact.text).passed


@pytest.fixture(scope='module')
def revised_finite_context():
    return actual(request=revised_original_request('私も少し怖くなかったです', ('今は嬉しい。',), old='寂しかった'))


@pytest.mark.parametrize('old,new', [
    ('あなたも', '私も'), ('あなたも', '友人も'), ('あなたも', 'あなたは'),
    ('あなたも', ''), ('少し', ''), ('怖くなかった', '怖かった'),
    ('怖くなかった', '怖くない'), ('言い直してくださった気持ちについては、当時、', '言い直してくださった気持ちについては、回答した時点で、'),
    ('言い直してくださった気持ちについては、当時、', '言い直してくださった気持ちについては、先の回答時点で、'), ('言い直してくださった気持ちについては、当時、', '言い直してくださった気持ちについては、'),
    ('言い直してくださった気持ちについては、当時、', 'これまで、言い直してくださった気持ちについては、当時、'), ('言い直してくださった気持ちについては、当時、', '頼まれたので、言い直してくださった気持ちについては、当時、'),
    ('のですね。', 'のですね。寂しかったのですね。'),
    ('のですね。', 'ので、今は安心なのですね。'),
])
def test_revised_finite_reception_rejects_changes_without_authors(revised_finite_context, old, new):
    context = revised_finite_context
    follow = context[0].artifact.reception
    changed = follow.replace(old, new, 1)
    assert changed != follow
    body = context[0].artifact.text.replace(follow, changed)
    assert not read_body(context, body).passed


@pytest.mark.parametrize('ending', ['のです。', 'のだと受け取りました。'])
def test_revised_finite_reception_reads_equivalent_acknowledgement(revised_finite_context, ending):
    context = revised_finite_context
    follow = context[0].artifact.reception
    body = context[0].artifact.text.replace(follow, follow.replace('のですね。', ending, 1))
    assert read_body(context, body).passed


@pytest.mark.parametrize('field,value', [('actor', 'other_person'), ('time_scope', 'present'),
                                        ('polarity', 'positive'), ('modality', 'fact')])
def test_revised_finite_reception_requires_admitted_self_past(revised_finite_context, field, value):
    result, plan, _, resolver, selected = revised_finite_context
    nucleus = next(n for n in plan.nuclei if 'thread_subject:revised_original_reaction' in n.semantic_frame.attribute_codes)
    move = next(m for m in plan.response_plan.human_reception_plan.moves if m.target_nucleus_ids == (nucleus.nucleus_id,))
    changed = replace(nucleus, semantic_frame=replace(nucleus.semantic_frame, **{field: value}))
    bad_plan = replace(plan, nuclei=tuple(changed if n == nucleus else n for n in plan.nuclei))
    first = result.artifact.reception.split('。')[0] + '。'
    assert gate._read_detached_feeling_discourse(first, move, bad_plan, resolver, selected) is None


@pytest.mark.parametrize('marker', ['thread_subject:independent_source_replacement',
                                  'thread_subject:revised_original_reaction',
                                  'lexical:preserve_source_predicate', 'lexical:no_new_sensation_family'])
def test_revised_finite_reception_requires_complete_revision_provenance(revised_finite_context, marker):
    result, plan, _, resolver, selected = revised_finite_context
    nucleus = next(n for n in plan.nuclei if 'thread_subject:revised_original_reaction' in n.semantic_frame.attribute_codes)
    move = next(m for m in plan.response_plan.human_reception_plan.moves if m.target_nucleus_ids == (nucleus.nucleus_id,))
    changed = replace(nucleus, semantic_frame=replace(nucleus.semantic_frame,
        attribute_codes=tuple(c for c in nucleus.semantic_frame.attribute_codes if c != marker)))
    bad_plan = replace(plan, nuclei=tuple(changed if n == nucleus else n for n in plan.nuclei))
    first = result.artifact.reception.split('。')[0] + '。'
    assert gate._read_detached_feeling_discourse(first, move, bad_plan, resolver, selected) is None


@pytest.mark.parametrize('source,finite', [('私は苦しかったです', 'あなたは苦しかった'),
                                         ('私も少し怖くなかったです', 'あなたも少し怖くなかった')])
def test_revised_finite_reception_saved_reads_keep_original_and_corrected_body(qcase, qdb, monkeypatch, source, finite):
    user, parent, service = qcase
    first = current = run(service.start(user, parent))
    for i, text in enumerate((None, '今は嬉しい。', f'「寂しかった」ではなく「{source}」です。')):
        if text is not None:
            if i > 1:
                current = run(cont(service, user, current, f'revised-finite-continue-{i}'))
            current = run(answer(service, user, current, text, f'revised-finite-answer-{i}'))
            assert current['body_state'] == 'REFINED', current
        assert current['original'] == first['original']
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved reads must not regenerate'))
            assert run(service.get(user, parent)) == current
            assert run(service.start(user, parent)) == current
    body = current['current_observation']['text']
    assert f'言い直してくださった気持ちについては、当時、{finite}のですね。' in body
    assert 'これまで' not in body and 'ですこと' not in body
    assert not current['can_continue']


def revised_then_withdrawn_request(source='私も少し怖くなかったです',
                                   positive='今は嬉しい。', withdrawn='誘われた'):
    request = revised_original_request(source, (positive,))
    return advance(request, f'「{withdrawn}」は誤りです。')


@pytest.mark.parametrize('withdrawn,detached,retained', [
    ('誘われた', '悲しかった', '頼まれた'), ('頼まれた', '寂しかった', '誘われた')])
@pytest.mark.parametrize('positive', ['今は嬉しい。', 'その時は少し嬉しかった。'])
@pytest.mark.parametrize('source,finite', [
    ('苦しかった', '言い直してくださった気持ちについては、当時は苦しかった'),
    ('私は苦しかったです', '言い直してくださった気持ちについては、当時、あなたは苦しかった'),
    ('私も少し怖くなかったです', '言い直してくださった気持ちについては、当時、あなたも少し怖くなかった'),
    ('少し私は苦しかったです', '言い直してくださった気持ちについては、当時、あなたは少し苦しかった'),
    ('私にはとても苦しかったです', '言い直してくださった気持ちについては、当時、あなたにはとても苦しかった'),
])
def test_revision_withdrawal_keeps_both_independent_reactions_and_existing_answer(
        withdrawn, detached, retained, positive, source, finite):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning
    request = revised_then_withdrawn_request(source, positive, withdrawn)
    public = MeaningExperienceEngine().generate(request)
    assert public.artifact is not None, public.reason_codes
    context = actual(request=request)
    result, plan, sentence, _, _ = context
    body, follow = result.artifact.text, result.artifact.reception
    assert body == public.artifact.text
    assert f'その時は{detached}し、それとは別に{finite}のですね。' in follow
    assert withdrawn not in body and '嬉しくなかった' not in body
    assert retained in follow and '褒められたことについて' in follow
    assert ('その時は少し嬉しかった' if '少し' in positive else '回答した時点では嬉しい') in follow
    assert f'その時の「{detached}」という気持ちが書かれており、それとは別に「{source}」と、当時の気持ちを言い直されています' in result.artifact.observation
    moves = plan.response_plan.human_reception_plan.moves
    assert len(moves) == 3
    group, = (m for m in moves if len(m.target_nucleus_ids) == 2 and not m.support_nucleus_ids)
    assert not any(nid in (r.from_nucleus_id, r.to_nucleus_id)
                   for nid in group.target_nucleus_ids for r in plan.relations)
    assert set(plan.coverage_requirements.required_nucleus_ids) <= {
        nid for line in sentence.lines if line.binding.line_role != 'human_follow'
        for nid in line.binding.nucleus_ids}
    checkpoint = prepare_emlis_meaning(request).checkpoint
    assert 'nucleus:s1:reaction' in checkpoint.inactive_claim_refs
    assert set(group.target_nucleus_ids).isdisjoint(checkpoint.inactive_claim_refs)
    assert read_body(context, body).passed


@pytest.fixture(scope='module')
def revision_withdrawal_context():
    return actual(request=revised_then_withdrawn_request())


@pytest.mark.parametrize('old,new', [
    ('その時は悲しかったし、', ''),
    ('し、それとは別に言い直してくださった気持ちについては、当時、あなたも少し怖くなかった', ''),
    ('あなたも', '私も'), ('あなたも', '友人も'), ('あなたも', 'あなたは'),
    ('あなたも', ''), ('少し', ''), ('怖くなかった', '怖かった'),
    ('怖くなかった', '怖くない'),
    ('言い直してくださった気持ちについては、当時、', '言い直してくださった気持ちについては、回答した時点で、'), ('言い直してくださった気持ちについては、当時、', '言い直してくださった気持ちについては、先の回答時点で、'),
    ('その時は悲しかった', '回答した時点では悲しかった'),
    ('悲しかったし、', '悲しかったので、'),
    ('言い直してくださった気持ちについては、当時、', '誘われたので、言い直してくださった気持ちについては、当時、'),
    ('のですね。', 'のですね。嬉しくなかったのですね。'),
])
def test_revision_withdrawal_rejects_missing_or_reassigned_meaning_without_authors(
        revision_withdrawal_context, old, new):
    context = revision_withdrawal_context
    follow = context[0].artifact.reception
    changed = follow.replace(old, new, 1)
    assert changed != follow
    assert not read_body(context, context[0].artifact.text.replace(follow, changed)).passed


def test_revision_withdrawal_rejects_swapping_whole_source_clauses(revision_withdrawal_context):
    context = revision_withdrawal_context
    body = context[0].artifact.text
    old = 'その時は悲しかったし、それとは別に言い直してくださった気持ちについては、当時、あなたも少し怖くなかった'
    new = '言い直してくださった気持ちについては、当時、あなたも少し怖くなかったし、その時は悲しかった'
    assert old in context[0].artifact.reception
    assert not read_body(context, body.replace(old, new)).passed


@pytest.mark.parametrize('ending', ['のです。', 'のだと受け取りました。'])
def test_revision_withdrawal_reads_equivalent_acknowledgement(revision_withdrawal_context, ending):
    context = revision_withdrawal_context
    follow = context[0].artifact.reception
    assert read_body(context, context[0].artifact.text.replace(follow, follow.replace('のですね。', ending, 1))).passed


@pytest.mark.parametrize('marker', ['thread_subject:revised_original_reaction',
                                  'thread_subject:independent_source_replacement'])
def test_revision_withdrawal_does_not_group_unproved_independent_answers(revision_withdrawal_context, marker):
    from emlis_ai_grounded_observation_plan import _thread_retained_reaction_groups, GroundedObservationPlanError
    _, plan, _, _, _ = revision_withdrawal_context
    nucleus = next(n for n in plan.nuclei if 'thread_subject:revised_original_reaction' in n.semantic_frame.attribute_codes)
    changed = replace(nucleus, semantic_frame=replace(nucleus.semantic_frame,
        attribute_codes=tuple(c for c in nucleus.semantic_frame.attribute_codes if c != marker)))
    nuclei = tuple(changed if n == nucleus else n for n in plan.nuclei)
    with pytest.raises(GroundedObservationPlanError):
        _thread_retained_reaction_groups(nuclei, plan.relations)


@pytest.mark.parametrize('source,positive', [('私は苦しかったです', '今は嬉しい。'),
                                          ('私も少し怖くなかったです', 'その時は少し嬉しかった。')])
def test_revision_withdrawal_saved_sequence_keeps_original_and_reads(qcase, qdb, monkeypatch, source, positive):
    user, parent, service = qcase
    first = current = run(service.start(user, parent))
    for i, text in enumerate((None, positive,
            f'「嬉しくなかった」ではなく「{source}」です。', '「誘われた」は誤りです。')):
        if text is not None:
            if i > 1:
                current = run(cont(service, user, current, f'revision-withdraw-continue-{i}'))
            current = run(answer(service, user, current, text, f'revision-withdraw-answer-{i}'))
            assert current['body_state'] == 'REFINED', current
        assert current['original'] == first['original']
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved reads must not regenerate'))
            assert run(service.get(user, parent)) == current
            assert run(service.start(user, parent)) == current
    body = current['current_observation']['text']
    assert f'その時の「悲しかった」という気持ちが書かれており、それとは別に「{source}」と、当時の気持ちを言い直されています' in body
    assert '誘われた' not in body and '嬉しくなかった' not in body
    assert '頼まれた' in body and '寂し' in body and '褒められた' in body
    assert not current['can_continue']


@pytest.mark.parametrize('old,answers,retained', [
    ('悲しかった', (), ('褒められた', '嬉しさにはつながらず', '頼まれたのに、寂しさ')),
    ('寂しかった', (), ('褒められた', '嬉しさにはつながらず', '誘われたのに、悲しさ')),
    ('嬉しくなかった', ('今は嬉しい。',), ('誘われたのに、悲しさ', '頼まれたのに、寂しさ')),
    ('寂しかった', ('今は嬉しい。',), ('褒められた', '嬉しさにはつながらず', '誘われたのに、悲しさ')),
])
@pytest.mark.parametrize('source,finite', [('楽しかった', '言い直してくださった気持ちについては、当時は楽しかった'),
    ('私は楽しかったです', '言い直してくださった気持ちについては、当時、あなたは楽しかった'),
    ('私も少し楽しかったです', '言い直してくださった気持ちについては、当時、あなたも少し楽しかった')])
def test_positive_original_revision_keeps_independent_occasion_and_other_duties(old, answers, retained, source, finite):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning
    request = revised_original_request(source, answers, old)
    public = MeaningExperienceEngine().generate(request)
    assert public.artifact is not None, public.reason_codes
    context = actual(request=request)
    result, plan, sentence, _, _ = context
    assert result.artifact.text == public.artifact.text
    assert f'{finite}のですね。' in result.artifact.reception
    assert all(s in result.artifact.reception for s in retained)
    assert old not in result.artifact.text
    assert f'「{source}」と、当時の気持ちを言い直されています' in result.artifact.observation
    assert not any(s in result.artifact.reception for s in ('楽しくなった', '前向き', 'おかげ', 'これまで'))
    if answers:
        assert '褒められたことについて、回答した時点では嬉しい' in result.artifact.reception
    revised, = (n for n in plan.nuclei if 'thread_subject:revised_original_reaction' in n.semantic_frame.attribute_codes)
    assert revised.semantic_frame.polarity == 'positive'
    assert not any(revised.nucleus_id in (r.from_nucleus_id, r.to_nucleus_id) for r in plan.relations)
    assert len(plan.response_plan.human_reception_plan.moves) == 2 + len(answers)
    assert set(plan.coverage_requirements.required_nucleus_ids) <= {
        nid for line in sentence.lines if line.binding.line_role != 'human_follow' for nid in line.binding.nucleus_ids}
    prepared = prepare_emlis_meaning(request)
    assert prepared.accepted_nuclei and prepared.checkpoint.assessment_status == 'RESOLVED'
    assert read_body(context, result.artifact.text).passed


@pytest.fixture(scope='module')
def positive_original_revision_context():
    return actual(request=revised_original_request('私も少し楽しかったです', ('今は嬉しい。',), old='寂しかった'))


@pytest.mark.parametrize('old,new', [
    ('あなたも', '私も'), ('あなたも', '友人も'), ('あなたも', 'あなたは'), ('あなたも', ''),
    ('少し', ''), ('楽しかった', '楽しくなかった'), ('楽しかった', '楽しい'),
    ('言い直してくださった気持ちについては、当時、', '言い直してくださった気持ちについては、回答した時点で、'), ('言い直してくださった気持ちについては、当時、', '言い直してくださった気持ちについては、先の回答時点で、'), ('言い直してくださった気持ちについては、当時、', '言い直してくださった気持ちについては、'),
    ('言い直してくださった気持ちについては、当時、', '頼まれたことについて、言い直してくださった気持ちについては、当時、'), ('言い直してくださった気持ちについては、当時、', '褒められたので、言い直してくださった気持ちについては、当時、'),
    ('楽しかったのですね。', '楽しかったのですね。寂しかったのですね。'),
    ('言い直してくださった気持ちについては、当時、あなたも少し楽しかったのですね。', ''),
    ('言い直してくださった気持ちについては、当時、あなたも少し楽しかったのですね。', '褒められたことについて、回答した時点では嬉しいのですね。'),
])
def test_positive_original_revision_rejects_lost_or_changed_reception_without_authors(positive_original_revision_context, old, new):
    context = positive_original_revision_context
    follow = context[0].artifact.reception
    changed = follow.replace(old, new, 1)
    assert changed != follow
    assert not read_body(context, context[0].artifact.text.replace(follow, changed)).passed


@pytest.mark.parametrize('old,new', [
    ('と、当時の気持ちを言い直されています', 'と、回答した時点の気持ちを言い直されています'),
    ('と、当時の気持ちを言い直されています', 'と、先の回答時点の気持ちを言い直されています'),
    ('と、当時の気持ちを言い直されています', 'と、頼まれたことへの当時の気持ちを言い直されています'),
    ('「私も少し楽しかったです」', '「私も少し楽しくなかったです」'),
    ('「私も少し楽しかったです」と、当時の気持ちを言い直されています。', ''),
])
def test_positive_original_revision_rejects_lost_or_changed_observation_without_authors(positive_original_revision_context, old, new):
    context = positive_original_revision_context
    observation = context[0].artifact.observation
    changed = observation.replace(old, new, 1)
    assert changed != observation
    assert not read_body(context, context[0].artifact.text.replace(observation, changed)).passed


@pytest.mark.parametrize('ending', ['のです。', 'のだと受け取りました。'])
def test_positive_original_revision_reads_equivalent_acknowledgement(positive_original_revision_context, ending):
    context = positive_original_revision_context
    follow = context[0].artifact.reception
    changed = follow.replace('楽しかったのですね。', '楽しかった' + ending)
    assert read_body(context, context[0].artifact.text.replace(follow, changed)).passed


@pytest.mark.parametrize('marker', ['thread_subject:independent_source_replacement',
    'thread_subject:revised_original_reaction', 'lexical:preserve_source_predicate', 'lexical:no_new_sensation_family'])
def test_positive_original_revision_requires_complete_provenance(positive_original_revision_context, marker):
    result, plan, _, resolver, selected = positive_original_revision_context
    nucleus = next(n for n in plan.nuclei if 'thread_subject:revised_original_reaction' in n.semantic_frame.attribute_codes)
    move = next(m for m in plan.response_plan.human_reception_plan.moves if m.target_nucleus_ids == (nucleus.nucleus_id,))
    changed = replace(nucleus, semantic_frame=replace(nucleus.semantic_frame,
        attribute_codes=tuple(c for c in nucleus.semantic_frame.attribute_codes if c != marker)))
    bad_plan = replace(plan, nuclei=tuple(changed if n == nucleus else n for n in plan.nuclei))
    clause = result.artifact.reception.split('。')[-2] + '。'
    assert gate._read_detached_feeling_discourse(clause, move, bad_plan, resolver, selected) is None


@pytest.mark.parametrize('field,value', [('actor', 'other_person'), ('time_scope', 'present'),
    ('polarity', 'negative'), ('modality', 'fact')])
def test_positive_original_revision_requires_admitted_self_past(positive_original_revision_context, field, value):
    result, plan, _, resolver, selected = positive_original_revision_context
    nucleus = next(n for n in plan.nuclei if 'thread_subject:revised_original_reaction' in n.semantic_frame.attribute_codes)
    move = next(m for m in plan.response_plan.human_reception_plan.moves if m.target_nucleus_ids == (nucleus.nucleus_id,))
    changed = replace(nucleus, semantic_frame=replace(nucleus.semantic_frame, **{field: value}))
    bad_plan = replace(plan, nuclei=tuple(changed if n == nucleus else n for n in plan.nuclei))
    clause = result.artifact.reception.split('。')[-2] + '。'
    assert gate._read_detached_feeling_discourse(clause, move, bad_plan, resolver, selected) is None


@pytest.mark.parametrize('replacement', ['とても楽しかった', '私は苦しかったです'])
def test_positive_original_revision_can_be_corrected_again_without_inheriting_event(replacement):
    request = revised_original_request('私も少し楽しかったです', (), old='寂しかった')
    request = advance(request, f'「私も少し楽しかったです」ではなく「{replacement}」です。')
    context = actual(request=request)
    result, plan, _, _, _ = context
    assert '私も少し楽しかった' not in result.artifact.text
    assert f'「{replacement}」と、当時の気持ちを言い直されています' in result.artifact.observation
    assert '誘われたのに、悲しさ' in result.artifact.reception
    assert '褒められたことは、嬉しさにはつながらず' in result.artifact.reception
    revised, = (n for n in plan.nuclei if 'thread_subject:revised_original_reaction' in n.semantic_frame.attribute_codes)
    assert not any(revised.nucleus_id in (r.from_nucleus_id, r.to_nucleus_id) for r in plan.relations)
    assert len(plan.response_plan.human_reception_plan.moves) == 2
    assert read_body(context, result.artifact.text).passed


def test_positive_original_revision_does_not_expand_negative_group_or_move_capacity():
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning, build_updated_grounded_plan
    from emlis_ai_grounded_observation_plan import (
        _thread_revised_original_reaction, _thread_retained_reaction_groups)
    request = revised_original_request('楽しかった', TWO_POSITIVE_PAIRS[0], old='嬉しくなかった')
    plan = build_updated_grounded_plan(prepare_emlis_meaning(request))
    revised, = (n for n in plan.nuclei if 'thread_subject:revised_original_reaction' in n.semantic_frame.attribute_codes)
    assert not _thread_revised_original_reaction(revised, plan.relations)
    assert _thread_revised_original_reaction(revised, plan.relations, polarity='positive')
    assert _thread_retained_reaction_groups(plan.nuclei, plan.relations) == ()


@pytest.mark.parametrize('old,source,finite', [('嬉しくなかった', '私は楽しかったです', 'あなたは楽しかった'),
    ('寂しかった', '私も少し楽しかったです', 'あなたも少し楽しかった')])
def test_positive_original_revision_saved_sequence_keeps_original_and_reads(qcase, qdb, monkeypatch, old, source, finite):
    user, parent, service = qcase
    first = current = run(service.start(user, parent))
    for i, text in enumerate((None, '今は嬉しい。', f'「{old}」ではなく「{source}」です。')):
        if text is not None:
            if i > 1:
                current = run(cont(service, user, current, f'positive-original-continue-{i}'))
            current = run(answer(service, user, current, text, f'positive-original-answer-{i}'))
            assert current['body_state'] == 'REFINED', current
        assert current['original'] == first['original']
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved reads must not regenerate'))
            assert run(service.get(user, parent)) == current
            assert run(service.start(user, parent)) == current
    body = current['current_observation']['text']
    assert f'言い直してくださった気持ちについては、当時、{finite}のですね。' in body
    assert old not in body
    assert all(s in body for s in ('褒められた', '誘われた', '頼まれた'))
    assert current['can_continue'] == (old == '嬉しくなかった')


@pytest.mark.parametrize('old,retained', [
    ('嬉しくなかった', ('誘われたのに、悲しさ', '頼まれたのに、寂しさ')),
    ('悲しかった', ('褒められたことは、嬉しさにはつながらず', '頼まれたのに、寂しさ')),
    ('寂しかった', ('褒められたことは、嬉しさにはつながらず', '誘われたのに、悲しさ')),
])
@pytest.mark.parametrize('answers', TWO_POSITIVE_PAIRS)
@pytest.mark.parametrize('source,finite', [('楽しかった', '楽しかった'),
    ('私は楽しかったです', 'あなたは楽しかった'),
    ('私も少し楽しかったです', 'あなたも少し楽しかった')])
def test_positive_answer_group_retains_two_answers_correction_and_surviving_reactions(old, retained, answers, source, finite):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning
    request = revised_original_request(source, answers, old=old)
    public = MeaningExperienceEngine().generate(request)
    assert public.artifact is not None, public.reason_codes
    context = actual(request=request)
    result, plan, sentence, _, _ = context
    assert result.artifact.text == public.artifact.text
    follow = result.artifact.reception
    assert all(text in follow for text in retained)
    first = '回答した時点では嬉しい' if answers == TWO_POSITIVE_PAIRS[0] else 'その時は少し嬉しかった'
    second = 'その時は楽しかった' if answers == TWO_POSITIVE_PAIRS[0] else '回答した時点では楽しい'
    assert f'褒められたことについて、{first}' in follow
    assert f'誘われたことについて、{second}' in follow
    assert finite + 'のですね。' in follow
    assert old not in result.artifact.text
    moves = plan.response_plan.human_reception_plan.moves
    group, = (m for m in moves if m.reception_act == 'recognize_lived_change' and len(m.target_nucleus_ids) > 1)
    if old == '寂しかった':
        assert len(group.target_nucleus_ids) == 3 and len(moves) == 2
        assert f'頼まれたことについて、その時は{finite}' in follow
    else:
        assert len(group.target_nucleus_ids) == 2 and len(moves) == 3
        revised, = (n for n in plan.nuclei if 'thread_subject:revised_original_reaction' in n.semantic_frame.attribute_codes)
        assert revised.nucleus_id not in group.target_nucleus_ids
        assert not any(revised.nucleus_id in (r.from_nucleus_id, r.to_nucleus_id) for r in plan.relations)
        assert '頼まれたことについて、その時は' not in follow
    assert set(plan.coverage_requirements.required_nucleus_ids) <= {
        nid for line in sentence.lines if line.binding.line_role != 'human_follow' for nid in line.binding.nucleus_ids}
    assert not any(text in follow for text in ('楽しくなった', '前向き', 'おかげ', 'これまで'))
    assert prepare_emlis_meaning(request).checkpoint.assessment_status == 'RESOLVED'
    assert read_body(context, result.artifact.text).passed


@pytest.fixture(scope='module')
def positive_answer_group_context():
    answers = ('今は私は嬉しいです。', 'その時は私も少し楽しかったです。')
    return actual(request=revised_original_request('楽しかった', answers, old='嬉しくなかった'))


@pytest.mark.parametrize('old,new', [
    ('褒められたことについて、回答した時点ではあなたは嬉しいし、', ''),
    ('し、誘われたことについて、その時はあなたも少し楽しかった', ''),
    ('褒められたことについて、', '頼まれたことについて、'),
    ('誘われたことについて、', '褒められたことについて、'),
    ('回答した時点では', 'その時は'), ('その時はあなたも', '回答した時点ではあなたも'),
    ('回答した時点では', '先の回答時点では'), ('回答した時点では', ''),
    ('あなたは', '私は'), ('あなたは', '友人は'), ('あなたも', 'あなたは'), ('あなたも', ''),
    ('少し', ''), ('嬉しいし、', '嬉しくないし、'), ('楽しかった', '楽しい'),
    ('嬉しいし、', '嬉しいので、'),
    ('言い直してくださった気持ちについては、当時は楽しかったのですね。', ''),
    ('言い直してくださった気持ちについては、当時は楽しかったのですね。', '頼まれたことについて、言い直してくださった気持ちについては、当時は楽しかったのですね。'),
])
def test_positive_answer_group_rejects_omission_reassignment_and_added_cause_without_authors(
        positive_answer_group_context, old, new):
    context = positive_answer_group_context
    follow = context[0].artifact.reception
    changed = follow.replace(old, new, 1)
    assert changed != follow
    assert not read_body(context, context[0].artifact.text.replace(follow, changed)).passed


@pytest.mark.parametrize('ending', ['のです。', 'のだと受け取りました。'])
def test_positive_answer_group_reads_equivalent_acknowledgement(positive_answer_group_context, ending):
    context = positive_answer_group_context
    follow = context[0].artifact.reception
    changed = follow.replace('少し楽しかったのですね。', '少し楽しかった' + ending)
    assert changed != follow
    assert read_body(context, context[0].artifact.text.replace(follow, changed)).passed


@pytest.mark.parametrize('field,value', [('actor', 'other_person'), ('time_scope', 'past'),
    ('polarity', 'negative'), ('modality', 'fact')])
def test_positive_answer_group_requires_each_admitted_source_frame(positive_answer_group_context, field, value):
    result, plan, _, resolver, selected = positive_answer_group_context
    move, = (m for m in plan.response_plan.human_reception_plan.moves if len(m.target_nucleus_ids) == 2 and not m.support_nucleus_ids)
    nucleus = next(n for n in plan.nuclei if n.nucleus_id == move.target_nucleus_ids[0])
    changed = replace(nucleus, semantic_frame=replace(nucleus.semantic_frame, **{field: value}))
    bad_plan = replace(plan, nuclei=tuple(changed if n == nucleus else n for n in plan.nuclei))
    clause = next(s + '。' for s in result.artifact.reception.split('。') if '褒められたことについて、' in s)
    assert gate._read_positive_answer_group_discourse(clause, move, bad_plan, resolver, selected) is None


def test_positive_answer_group_reader_derives_every_duty_without_forward_group(positive_answer_group_context):
    result, plan, _, resolver, selected = positive_answer_group_context
    move, = (m for m in plan.response_plan.human_reception_plan.moves if len(m.target_nucleus_ids) == 2 and not m.support_nucleus_ids)
    clause = next(s + '。' for s in result.artifact.reception.split('。') if '褒められたことについて、' in s)
    with patch.object(reception, 'source_grounded_thread_answer_group', side_effect=AssertionError('no forward group oracle')):
        proof = gate._read_positive_answer_group_discourse(clause, move, plan, resolver, selected)
        assert proof is not None and len(proof) == 4
        missing = clause.replace('褒められたことについて、回答した時点ではあなたは嬉しいし、', '')
        assert gate._read_positive_answer_group_discourse(missing, move, plan, resolver, selected) is None


@pytest.mark.parametrize('answers', TWO_POSITIVE_PAIRS)
def test_positive_answer_group_also_retains_three_linked_adds(answers):
    request = begin()
    for text in (*answers, 'その時は楽しかった。'):
        request = advance(request, text)
    context = actual(request=request)
    result, plan, _, _, _ = context
    follow = result.artifact.reception
    assert all(s in follow for s in ('褒められたことについて、', '誘われたことについて、',
        '頼まれたことについて、その時は楽しかった', '嬉しさにはつながらず',
        '誘われたのに、悲しさ', '頼まれたのに、寂しさ'))
    assert len(plan.response_plan.human_reception_plan.moves) == 2
    assert read_body(context, result.artifact.text).passed


@pytest.mark.parametrize('old', ['嬉しくなかった', '悲しかった', '寂しかった'])
@pytest.mark.parametrize('answers', TWO_POSITIVE_PAIRS)
def test_positive_answer_group_saved_sequence_keeps_original_and_exact_reads(qcase, qdb, monkeypatch, old, answers):
    user, parent, service = qcase
    first = current = run(service.start(user, parent))
    for i, text in enumerate((*answers, f'「{old}」ではなく「私も少し楽しかったです」です。')):
        if i:
            current = run(cont(service, user, current, f'positive-group-continue-{i}'))
        current = run(answer(service, user, current, text, f'positive-group-answer-{i}'))
        assert current['body_state'] == 'REFINED', current
        assert current['original'] == first['original']
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved reads must not regenerate'))
            assert run(service.get(user, parent)) == current
            assert run(service.start(user, parent)) == current
    body = current['current_observation']['text']
    assert 'あなたも少し楽しかったのですね。' in body
    assert old not in body
    assert all(s in body for s in ('褒められたことについて、', '誘われたことについて、'))
    assert not current['can_continue']
# Revision action and original occasion are separate body-visible facts. An
# independent revision must not borrow the nearest event as its antecedent.
REVISION_INTRO = '言い直してくださった気持ちについては、'


@pytest.mark.parametrize('old', ['嬉しくなかった', '悲しかった', '寂しかった'])
@pytest.mark.parametrize('answers', [(), ('今は嬉しい。',), *TWO_POSITIVE_PAIRS])
@pytest.mark.parametrize('source,finite', [
    ('楽しかった', '当時は楽しかった'), ('私も少し楽しかったです', '当時、あなたも少し楽しかった'),
    ('苦しかった', '当時は苦しかった'), ('私も少し怖くなかったです', '当時、あなたも少し怖くなかった')])
def test_explicit_revision_reference_keeps_source_and_existing_about(old, answers, source, finite):
    context = actual(request=revised_original_request(source, answers, old))
    result, plan, _, _, _ = context
    revised = [n for n in plan.nuclei if 'thread_subject:revised_original_reaction' in n.semantic_frame.attribute_codes]
    if ('嬉しくなかった', '悲しかった', '寂しかった').index(old) == len(answers):
        assert not revised
        assert REVISION_INTRO not in result.artifact.reception
        assert '言い直されています' not in result.artifact.observation
        event = ORIGINAL_EVENTS[len(answers)]
        assert f'「{event}」ことに対するその時の受け止めとして、「{source}」' in result.artifact.observation
    else:
        nucleus, = revised
        assert not any(nucleus.nucleus_id in (r.from_nucleus_id, r.to_nucleus_id) for r in plan.relations)
        assert result.artifact.observation.count(f'「{source}」と、当時の気持ちを言い直されています。') == 1
        assert result.artifact.reception.count(REVISION_INTRO + finite + 'のですね。') == 1
        assert nucleus.semantic_frame.actor == 'current_user'
        assert nucleus.semantic_frame.time_scope == 'past'
    assert old not in result.artifact.text
    assert read_body(context, result.artifact.text).passed


@pytest.fixture(scope='module', params=['single', 'tail', 'relations', 'withdrawal'])
def explicit_revision_reference_context(request):
    if request.param == 'withdrawal':
        req = revised_then_withdrawn_request()
    else:
        source = '私も少し楽しかったです' if request.param in ('single', 'tail') else '私も少し怖くなかったです'
        req = revised_original_request(source,
            ('今は嬉しい。',) if request.param == 'single' else TWO_POSITIVE_PAIRS[0],
            old='寂しかった' if request.param == 'single' else '嬉しくなかった')
    return actual(request=req)


@pytest.mark.parametrize('part,old,new', [
    ('observation', 'と、当時の気持ちを言い直されています。', 'という気持ちが書かれています。'),
    ('observation', '当時の気持ち', '回答した時点の気持ち'),
    ('observation', 'と、当時の気持ち', 'と、誘われたことについて当時の気持ち'),
    ('reception', REVISION_INTRO, ''),
    ('reception', REVISION_INTRO, '誘われたことについて、'),
    ('reception', '当時、', 'その時、'),
    ('reception', '当時、', '回答した時点で、'),
    ('reception', 'あなたも', 'あなたは'),
    ('reception', '少し', ''),
])
def test_explicit_revision_reference_rejects_ambiguous_or_reassigned_body_without_authors(
        explicit_revision_reference_context, part, old, new):
    context = explicit_revision_reference_context
    original = getattr(context[0].artifact, part)
    changed = original.replace(old, new, 1)
    assert changed != original
    body = context[0].artifact.text.replace(original, changed, 1)
    with patch.object(reception, '_revised_feeling_discourse_prefix', side_effect=AssertionError('no prefix oracle')), patch.object(
            surface, '_render_extra_context', side_effect=AssertionError('no tail oracle')), patch.object(
            surface, '_render_relation', side_effect=AssertionError('no relation oracle')):
        assert not read_body(context, body).passed


def test_explicit_revision_reference_reads_equivalent_endings_without_authors(explicit_revision_reference_context):
    context = explicit_revision_reference_context
    body = context[0].artifact.text
    changed = body.replace('言い直されています。', '言い換えられています。').replace('のですね。', 'のです。')
    assert changed != body and read_body(context, changed).passed


@pytest.mark.parametrize('source', ['少し楽しかった', '少し苦しかった'])
def test_explicit_revision_reference_recorrection_does_not_revive_event(source):
    request = advance(revised_original_request('楽しかった', ('今は嬉しい。',)),
                      f'「楽しかった」ではなく「{source}」です。')
    context = actual(request=request)
    body = context[0].artifact.text
    assert f'「{source}」と、当時の気持ちを言い直されています。' in body
    assert REVISION_INTRO + f'当時は{source}のですね。' in body
    assert '嬉しくなかった' not in body and '「楽しかった」' not in body
    assert read_body(context, body).passed


@pytest.mark.parametrize('part', ['observation', 'reception'])
@pytest.mark.parametrize('replacement', ['', 'そのため', '同じ気持ちについて'])
def test_explicit_revision_reference_group_requires_separate_correction(revision_withdrawal_context, part, replacement):
    context = revision_withdrawal_context
    original = getattr(context[0].artifact, part)
    assert original.count('それとは別に') == 1
    changed = original.replace('それとは別に', replacement)
    assert not read_body(context, context[0].artifact.text.replace(original, changed)).passed


MULTIPLE_ORIGINAL_CORRECTIONS = [
    ('少し私は苦しかったです', '私は少し苦しかったです'),
    ('少し私は不安でした', '私は少し不安でした'),
    ('私は少し不安でした', '私は少し不安でした'),
    ('私も少し怖くなかったです', '少し私には苦しかったです'),
]


def multiple_original_correction_answers(sources):
    return tuple(f'「{old}」ではなく「{source}」です。'
                 for old, source in zip(('嬉しくなかった', '悲しかった'), sources))


@pytest.fixture(scope='module', params=MULTIPLE_ORIGINAL_CORRECTIONS)
def multiple_original_correction_context(request):
    req = begin()
    for text in multiple_original_correction_answers(request.param):
        req = advance(req, text)
    return actual(request=req)


@pytest.mark.parametrize('sources', MULTIPLE_ORIGINAL_CORRECTIONS)
def test_multiple_original_corrections_deliver_every_event_and_own_feeling(sources):
    req = begin()
    for text in multiple_original_correction_answers(sources):
        req = advance(req, text)
    context = actual(request=req)
    result = context[0]
    assert '嬉しくなかった' not in result.artifact.text and '悲しかった' not in result.artifact.text
    for event, feeling in zip(('褒められた', '誘われた'), sources):
        assert f'「{event}」ことに対するその時の受け止めとして、「{feeling}」' in result.artifact.observation
    assert '「頼まれた」と「寂しかった」' in result.artifact.observation
    assert '頼まれたのに、寂しさを感じたのですね。' in result.artifact.reception
    assert read_body(context, result.artifact.text).passed


@pytest.mark.parametrize('event', ['褒められた', '誘われた'])
@pytest.mark.parametrize('when', ['', '回答した時点', '先の回答時点'])
def test_multiple_original_corrections_cannot_borrow_another_clause_time(
        multiple_original_correction_context, event, when):
    context = multiple_original_correction_context
    body = context[0].artifact.text
    old = f'「{event}」ことに対するその時の受け止めとして、'
    new = f'「{event}」ことに対する{when + "の" if when else ""}受け止めとして、'
    assert old in body
    assert not read_body(context, body.replace(old, new, 1)).passed


@pytest.mark.parametrize('old,new', [
    ('「褒められた」ことに対する', '「誘われた」ことに対する'),
    ('「誘われた」ことに対する', '「頼まれた」ことに対する'),
    ('少し', ''), ('私は', '友人は'), ('私は', '私も'),
    ('不安でした', '不安ではありませんでした'), ('不安でした', '不安です'),
])
def test_identical_corrected_feelings_still_require_each_exact_source(old, new):
    req = begin()
    for text in multiple_original_correction_answers(MULTIPLE_ORIGINAL_CORRECTIONS[2]):
        req = advance(req, text)
    context = actual(request=req)
    body = context[0].artifact.text
    assert old in body and not read_body(context, body.replace(old, new, 1)).passed


def test_multiple_original_corrections_allow_equivalent_observation_ending(multiple_original_correction_context):
    context = multiple_original_correction_context
    body = context[0].artifact.text
    assert 'が見えます。' in body
    assert read_body(context, body.replace('が見えます。', 'が示されています。')).passed


@pytest.mark.parametrize('sources', MULTIPLE_ORIGINAL_CORRECTIONS)
@pytest.mark.parametrize('last', ['「寂しかった」ではなく「私も少し怖くなかったです」です。', '「頼まれた」は誤りです。'])
def test_multiple_original_corrections_persist_and_reuse_exact_body(qcase, qdb, monkeypatch, sources, last):
    user, parent, _ = qcase
    service = active(monkeypatch)
    first = current = run(service.start(user, parent))

    def saved_reads():
        assert current['original'] == first['original']
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved reads must not regenerate'))
            assert run(service.get(user, parent)) == current
            assert run(service.start(user, parent)) == current

    saved_reads()
    for index, text in enumerate((*multiple_original_correction_answers(sources), last)):
        if index:
            current = run(cont(service, user, current, f'multiple-correction-continue-{index}'))
            saved_reads()
        current = run(answer(service, user, current, text, f'multiple-correction-answer-{index}'))
        assert current['body_state'] == 'REFINED', current
        saved_reads()
    body = current['current_observation']['text']
    assert all(source in body for source in sources)
    assert '嬉しくなかった' not in body and '悲しかった' not in body
    assert ('頼まれた' not in body) == ('誤り' in last)
    assert current['state'] == 'COMPLETED' and not current['can_continue']


@pytest.fixture(scope='module', params=MULTIPLE_ORIGINAL_CORRECTIONS)
def three_original_corrections_context(request):
    req = begin()
    for text in (*multiple_original_correction_answers(request.param),
                 '「寂しかった」ではなく「私も少し怖くなかったです」です。'):
        req = advance(req, text)
    return actual(request=req)


def test_three_original_corrections_use_complete_finite_feelings(three_original_corrections_context):
    context = three_original_corrections_context
    result, plan, _, resolver, selected = context
    follow = result.artifact.reception
    assert all(f'{event}ことについて、その時は' in follow
               for event in ('褒められた', '誘われた', '頼まれた'))
    assert follow.endswith('あなたも少し怖くなかったのですね。')
    assert '私' not in follow and 'でしたこと' not in follow and '受け止めています' not in follow
    move, = plan.response_plan.human_reception_plan.moves
    assert len(move.target_nucleus_ids) == 3 and not move.support_nucleus_ids
    with patch.object(reception, 'source_grounded_thread_answer_group',
                      side_effect=AssertionError('no forward group oracle')):
        proof = gate._read_positive_answer_group_discourse(follow, move, plan, resolver, selected)
        assert proof is not None and len(proof) == 6
    assert read_body(context, result.artifact.text).passed


@pytest.mark.parametrize('event', ['褒められた', '誘われた', '頼まれた'])
@pytest.mark.parametrize('when', ['', '回答した時点では', '先の回答時点では'])
def test_three_original_corrections_keep_each_reception_time(three_original_corrections_context, event, when):
    context = three_original_corrections_context
    body = context[0].artifact.text
    old = event + 'ことについて、その時は'
    assert old in body
    assert not read_body(context, body.replace(old, event + 'ことについて、' + when, 1)).passed


@pytest.mark.parametrize('old,new', [
    ('褒められたことについて、', '誘われたことについて、'),
    ('誘われたことについて、', ''),
    ('あなたも少し怖くなかった', 'あなたも少し怖かった'),
    ('あなたも少し怖くなかった', 'あなたも少し怖くない'),
    ('あなたも少し怖くなかった', 'あなたも怖くなかった'),
    ('あなたも少し怖くなかった', 'あなたは少し怖くなかった'),
    ('あなたも少し怖くなかった', '友人も少し怖くなかった'),
    ('し、頼まれたことについて、', 'ので、頼まれたことについて、'),
])
def test_three_original_corrections_reject_missing_or_changed_duties(three_original_corrections_context, old, new):
    context = three_original_corrections_context
    body = context[0].artifact.text
    assert old in body and not read_body(context, body.replace(old, new, 1)).passed


@pytest.mark.parametrize('field,value', [('actor', 'other_person'), ('time_scope', 'present'),
    ('polarity', 'positive'), ('modality', 'fact')])
def test_three_original_corrections_reader_requires_admitted_frames(three_original_corrections_context, field, value):
    result, plan, _, resolver, selected = three_original_corrections_context
    move, = plan.response_plan.human_reception_plan.moves
    nucleus = next(n for n in plan.nuclei if n.nucleus_id == move.target_nucleus_ids[1])
    changed = replace(nucleus, semantic_frame=replace(nucleus.semantic_frame, **{field: value}))
    bad_plan = replace(plan, nuclei=tuple(changed if n == nucleus else n for n in plan.nuclei))
    assert gate._read_positive_answer_group_discourse(result.artifact.reception, move, bad_plan, resolver, selected) is None
