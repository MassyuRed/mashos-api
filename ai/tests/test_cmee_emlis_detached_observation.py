"""Independent feelings keep their sources and times after partial withdrawal."""
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import patch
import pytest
import re

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
            assert ('その時は「怖かった」' if second.startswith('その時') else '回答した時点では「怖い」') in body
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
    original = '「苦しかった」と、当時の気持ちを言い直されています。'
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
    ('し、', 'ので、'),
    ('誘われたのに、悲しさを感じたし、', ''),
    ('頼まれたのに、寂しさを感じたし、', ''),
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
    changed = body.replace('言い直されています。', '言い換えられています。').replace('のですね。', 'のです。')
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
    ('その時は「少し嬉しかった」', '回答した時点では「少し嬉しかった」'),
    ('「誘われた」ことについて、回答した時点の', '「誘われた」ことについて、その時の'),
    ('「誘われた」ことについて、', '「頼まれた」ことについて、'),
    ('「誘われた」ことについて、', '「誘われた」ことのおかげで'),
    ('「苦しかった」と、当時の気持ちを言い直されています', '「苦しかった」と、回答した時点の気持ちを言い直されています'),
    ('「苦しかった」と、当時の気持ちを言い直されています', '「苦しかった」と、気持ちを言い直されています'),
    ('「苦しかった」と、当時の気持ちを言い直されています', '「悲しかった」と、当時の気持ちを言い直されています'),
    ('「苦しかった」と、当時の気持ちを言い直されています', '誘われたので、「苦しかった」と、当時の気持ちを言い直されています'),
    ('「苦しかった」と、当時の気持ちを言い直されています。', ''),
    ('「誘われた」ことについて、回答した時点の受け止めは「楽しい」と書かれています。', ''),
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
    changed = body.replace('のですね。', 'のです。')
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
    assert f'「誘われた」ことについて、その時の受け止めは「{source}」' in observation
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
    assert len(plan.response_plan.human_reception_plan.moves) == (3 if positive == '今は嬉しい。' else 2)
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
    ('「誘われた」ことについて、その時の', '「頼まれた」ことについて、その時の'),
    ('「誘われた」ことについて、その時の', '「誘われた」ことについて、回答した時点の'),
    ('「誘われた」ことについて、その時の', '「誘われた」ことについて、'),
    ('「誘われた」ことについて、', '「誘われた」ことのせいで'),
    ('「誘われた」ことについて、その時の受け止めは「少し怖くなかった」と書かれています。', ''),
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
            assert '「誘われた」ことについて、その時の受け止めは「苦しかった」' in body
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
    assert ('その時は「少し嬉しかった」' if '少し' in positive
            else '回答した時点では「嬉しい」') in observation
    assert len(plan.coverage_requirements.required_nucleus_ids) == 6
    assert len(plan.relations) == 3
    assert not any('nucleus:s2:event' in (r.from_nucleus_id, r.to_nucleus_id) for r in plan.relations)
    assert len(plan.response_plan.human_reception_plan.moves) == (3 if positive == '今は嬉しい。' else 2)
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
        assert ('その時は「少し嬉しかった」' if '少し' in answers[0]
                else '回答した時点では「嬉しい」') in lines[0]
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
    ('回答した時点では「嬉しい」', 'その時は「嬉しい」'),
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
    assert ('その時は「少し嬉しかった」' if '少し' in positive
            else '回答した時点では「嬉しい」') in body
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
        observation = result.artifact.observation
        assert (f'「{event}」ことについて、その時の受け止めは「{source}」' in observation
            or any(clause.strip().startswith('それぞれの出来事について、その時の受け止めとして、')
                and f'「{event}」ことには「{source}」' in clause
                and clause.endswith('と書かれています') for clause in observation.split('。')))
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
        assert f'「{event}」ことには「{feeling}」' in result.artifact.observation
    assert result.artifact.observation.count('その時の受け止めとして、') == 1
    assert '「頼まれた」と「寂しかった」' in result.artifact.observation
    assert '頼まれたのに、寂しさを感じたのですね。' in result.artifact.reception
    assert read_body(context, result.artifact.text).passed


@pytest.mark.parametrize('event', ['褒められた', '誘われた'])
@pytest.mark.parametrize('when', ['', '回答した時点', '先の回答時点'])
def test_multiple_original_corrections_cannot_borrow_another_clause_time(
        multiple_original_correction_context, event, when):
    context = multiple_original_correction_context
    body = context[0].artifact.text
    # Expand the shared time into independently accepted local clauses,
    # then alter only one event's time. The other time must not discharge it.
    body = re.sub(r'それぞれの出来事について、その時の受け止めとして、((?:「[^「」]+」ことには「[^「」]+」、)+「[^「」]+」ことには「[^「」]+」)と書かれています。',
        lambda m: 'とあり、また'.join(f'「{e}」ことについて、その時の受け止めは「{v}」'
            for e, v in re.findall(r'「([^「」]+)」ことには「([^「」]+)」', m[1])) + 'と書かれています。', body)
    assert read_body(context, body).passed
    old = f'「{event}」ことについて、その時の受け止めは'
    new = f'「{event}」ことについて、{when + "の" if when else ""}受け止めは'
    assert old in body
    assert not read_body(context, body.replace(old, new, 1)).passed


@pytest.mark.parametrize('old,new', [
    ('「褒められた」ことには', '「誘われた」ことには'),
    ('「誘われた」ことには', '「頼まれた」ことには'),
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
    assert 'と書かれています。' in body
    legacy = re.sub(r'それぞれの出来事について、その時の受け止めとして、((?:「[^「」]+」ことには「[^「」]+」、)+「[^「」]+」ことには「[^「」]+」)と書かれています。',
        lambda m: '、また'.join(f'「{e}」ことに対するその時の受け止めとして、「{v}」'
            for e, v in re.findall(r'「([^「」]+)」ことには「([^「」]+)」', m[1])) + 'が示されています。', body)
    assert legacy != body and read_body(context, legacy).passed


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


NONADJACENT_CORRECTION_SOURCES = [*MULTIPLE_ORIGINAL_CORRECTIONS, ('楽しかった', '私は不安でした')]


def nonadjacent_correction_answers(prior, sources):
    return (*(('今は嬉しい。',) if prior else ()),
            f'「嬉しくなかった」ではなく「{sources[0]}」です。',
            f'「寂しかった」ではなく「{sources[1]}」です。')


@pytest.fixture(scope='module', params=[(prior, sources) for prior in (False, True)
    for sources in NONADJACENT_CORRECTION_SOURCES])
def nonadjacent_correction_context(request):
    prior, sources = request.param
    req = begin()
    for text in nonadjacent_correction_answers(prior, sources):
        req = advance(req, text)
    return prior, sources, actual(request=req)


def test_nonadjacent_corrections_keep_complete_duties_and_original_event_order(nonadjacent_correction_context):
    prior, sources, context = nonadjacent_correction_context
    result, plan, _, _, _ = context
    body, observation, follow = result.artifact.text, result.artifact.observation, result.artifact.reception
    assert observation.index('「褒められた」') < observation.index('「誘われた」') < observation.index('「頼まれた」')
    assert '一つの流れ' not in body and 'その出発点' not in body
    assert '嬉しくなかった' not in body and '寂しかった' not in body
    assert '「誘われた」と「悲しかった」' in observation and '誘われたのに、悲しさ' in follow
    independent = sources[0] if prior else sources[1]
    assert f'「{independent}」と、当時の気持ちを言い直されています。' in observation
    assert REVISION_INTRO in follow and 'でしたこと' not in follow
    if prior:
        assert '「褒められた」ことについて、回答した時点の受け止めは「嬉しい」' in observation
        assert f'「頼まれた」ことについて、その時の受け止めは「{sources[1]}」' in observation
        assert '回答した時点では嬉しいのですね。' in follow
    else:
        assert f'「褒められた」ことについて、その時の受け止めは「{sources[0]}」' in observation
        assert '「頼まれた」という出来事がありました。' in observation
        assert '頼まれたことについて' not in follow and '頼まれた時は' not in follow
    moves = plan.response_plan.human_reception_plan.moves
    owned = {nid for move in moves for nid in (*move.target_nucleus_ids, *move.support_nucleus_ids)}
    required_feelings = {n.nucleus_id for n in plan.nuclei if n.kind == 'reaction' and n.retention == 'required'}
    assert required_feelings <= owned and len(moves) <= 3
    revised, = (n for n in plan.nuclei if 'thread_subject:revised_original_reaction' in n.semantic_frame.attribute_codes)
    assert not any(revised.nucleus_id in (r.from_nucleus_id, r.to_nucleus_id) for r in plan.relations)
    assert read_body(context, body).passed


@pytest.mark.parametrize('part,old,new', [
    ('observation', '当時の気持ちを言い直されています。', '回答した時点の気持ちを言い直されています。'),
    ('observation', 'と、当時の気持ちを言い直されています。', 'という気持ちが書かれています。'),
    ('observation', '「誘われた」と「悲しかった」', '「頼まれた」と「悲しかった」'),
    ('observation', 'ことについて、その時の受け止めは', 'ことについて、受け止めは'),
    ('reception', REVISION_INTRO, ''),
    ('reception', REVISION_INTRO, '頼まれたことについて、'),
    ('reception', '当時', '回答した時点'),
    ('reception', '悲しさ', '嬉しさ'),
])
def test_nonadjacent_corrections_reject_lost_reassigned_or_retimed_meaning(nonadjacent_correction_context, part, old, new):
    _, _, context = nonadjacent_correction_context
    original = getattr(context[0].artifact, part)
    changed = original.replace(old, new, 1)
    assert changed != original
    assert not read_body(context, context[0].artifact.text.replace(original, changed, 1)).passed


@pytest.mark.parametrize('prior', [False, True])
@pytest.mark.parametrize('sources', NONADJACENT_CORRECTION_SOURCES)
def test_nonadjacent_corrections_saved_rounds_reuse_exact_body(qcase, qdb, monkeypatch, prior, sources):
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
    texts = nonadjacent_correction_answers(prior, sources)
    for index, text in enumerate(texts):
        if index:
            current = run(cont(service, user, current, f'nonadjacent-continue-{index}'))
            saved_reads()
        current = run(answer(service, user, current, text, f'nonadjacent-answer-{index}'))
        assert current['body_state'] == 'REFINED', current
        saved_reads()
    body = current['current_observation']['text']
    assert all(source in body for source in sources)
    assert '嬉しくなかった' not in body and '寂しかった' not in body
    assert '一つの流れ' not in body and 'その出発点' not in body
    assert '頼まれた' in body
    assert current['state'] == 'COMPLETED' and not current['can_continue']


@pytest.mark.parametrize('neighbor', ['contrast', 'other_relation', 'other_field', 'about_only'])
def test_bare_event_never_partially_joins_an_unsupported_neighbor(neighbor):
    plan = actual(request=begin())[1]
    groups = (('nucleus:s1:event', 'nucleus:s1:reaction'), ('nucleus:s2:event',),
              ('nucleus:s3:event', 'nucleus:s3:reaction'))
    nuclei = {n.nucleus_id: n for n in plan.nuclei}
    relations = {r.relation_id: r for r in plan.relations if r.from_nucleus_id != 'nucleus:s2:event'}
    right = next(r for r in relations.values() if r.from_nucleus_id == 'nucleus:s3:event')
    if neighbor == 'other_relation':
        relations['unsupported'] = replace(right, relation_id='unsupported', type='user_stated_cause')
    elif neighbor in {'other_field', 'about_only'}:
        nucleus = nuclei['nucleus:s3:reaction']
        nuclei[nucleus.nucleus_id] = replace(nucleus, source_fields=('answer_text_private',))
        if neighbor == 'about_only':
            relations[right.relation_id] = replace(right, type='evaluation_about_event')
    merged = surface._merge_parallel_contrast_groups(groups, tuple(relations), nuclei, relations,
        bridge_detached_feelings=True)
    if neighbor == 'contrast':
        assert merged == (('nucleus:s1:event', 'nucleus:s1:reaction', 'nucleus:s2:event',
                           'nucleus:s3:event', 'nucleus:s3:reaction'),)
    else:
        assert merged == groups


INDEPENDENT_REVISION_FINITE = {
    '少し私は苦しかったです': 'あなたは少し苦しかった',
    '私は少し苦しかったです': 'あなたは少し苦しかった',
    '少し私は不安でした': 'あなたは少し不安だった',
    '私は少し不安でした': 'あなたは少し不安だった',
    '私も少し怖くなかったです': 'あなたも少し怖くなかった',
    '少し私には苦しかったです': 'あなたには少し苦しかった',
    '楽しかった': '楽しかった',
    '私は不安でした': 'あなたは不安だった',
}


def two_independent_revision_answers(sources):
    return ('今は嬉しい。', f'「嬉しくなかった」ではなく「{sources[0]}」です。',
            f'「悲しかった」ではなく「{sources[1]}」です。')


@pytest.fixture(scope='module', params=NONADJACENT_CORRECTION_SOURCES)
def two_independent_revisions_context(request):
    req = begin()
    for text in two_independent_revision_answers(request.param):
        req = advance(req, text)
    return request.param, actual(request=req)


def test_two_independent_revisions_keep_every_duty_and_fact(two_independent_revisions_context):
    from collections import Counter
    sources, context = two_independent_revisions_context
    result, plan, _, _, _ = context
    observation, follow = result.artifact.observation, result.artifact.reception
    assert observation.index('「褒められた」') < observation.index('「誘われた」') < observation.index('「頼まれた」')
    assert '「誘われた」という出来事がありました。' in observation
    assert 'その出発点' not in observation and '一つの流れ' not in observation
    assert '嬉しくなかった' not in result.artifact.text and '悲しかった' not in result.artifact.text
    assert '褒められたことについて、回答した時点では嬉しいのですね。' in follow
    assert '「頼まれた」と「寂しかった」' in observation and '頼まれたのに、寂しさを感じた' in follow
    assert observation.count('当時の気持ちを、') == 1
    assert ('二つとも' in observation) == (sources[0] == sources[1])
    assert ('それぞれ' in observation) == (sources[0] != sources[1])
    shared = follow.startswith('二つの言い直しでは、どちらも')
    assert follow.count(REVISION_INTRO) == (2 if sources[0] == '楽しかった' else 0)
    assert shared == (INDEPENDENT_REVISION_FINITE[sources[0]] == INDEPENDENT_REVISION_FINITE[sources[1]])
    if not shared and sources[0] != '楽しかった':
        assert follow.startswith('言い直してくださった気持ちは、') and 'し、それとは別に当時' in follow
    for source, count in Counter(sources).items():
        assert observation.count(f'「{source}」') == (1 if sources[0] == sources[1] else count)
    for finite, count in Counter(INDEPENDENT_REVISION_FINITE[s] for s in sources).items():
        assert follow.count(finite) == (1 if shared else count)
    assert 'でしたの' not in follow and 'でしたこと' not in follow
    assert '私' not in follow and '誘われた' not in follow
    moves = plan.response_plan.human_reception_plan.moves
    assert len(moves) == 3
    owned = {nid for move in moves for nid in (*move.target_nucleus_ids, *move.support_nucleus_ids)}
    assert {n.nucleus_id for n in plan.nuclei if n.kind == 'reaction' and n.retention == 'required'} <= owned
    revisions = [n for n in plan.nuclei if 'thread_subject:revised_original_reaction' in n.semantic_frame.attribute_codes]
    assert len(revisions) == 2
    assert not any(n.nucleus_id in (r.from_nucleus_id, r.to_nucleus_id) for n in revisions for r in plan.relations)
    assert all(any(move.reception_act == ('recognize_lived_change' if n.semantic_frame.polarity == 'positive'
        else 'stay_with_current_burden') and n.nucleus_id in move.target_nucleus_ids for move in moves) for n in revisions)
    assert read_body(context, result.artifact.text).passed


@pytest.mark.parametrize('permutation', ['reverse', 'rotate'])
def test_two_independent_revisions_keep_source_order_across_plan_passes(two_independent_revisions_context, permutation):
    from emlis_ai_grounded_observation_plan import _thread_retained_reaction_groups
    _, context = two_independent_revisions_context
    plan = context[1]
    nuclei = tuple(reversed(plan.nuclei)) if permutation == 'reverse' else (*plan.nuclei[2:], *plan.nuclei[:2])
    assert _thread_retained_reaction_groups(nuclei, plan.relations) == _thread_retained_reaction_groups(plan.nuclei, plan.relations)


@pytest.mark.parametrize('mutation', ['delete', 'duplicate', 'before_answer', 'cause', 'present', 'wrong_event'])
def test_two_independent_revisions_reject_changed_compressed_fact(two_independent_revisions_context, mutation):
    _, context = two_independent_revisions_context
    original = context[0].artifact.observation
    fact = '「誘われた」という出来事がありました。'
    assert original.count(fact) == 1
    if mutation == 'before_answer':
        changed = fact + ' ' + original.replace(fact, '', 1)
    else:
        replacement = {'delete': '', 'duplicate': fact + ' ' + fact,
            'cause': 'そのため、' + fact, 'present': fact.replace('ありました', 'あります'),
            'wrong_event': fact.replace('誘われた', '褒められた')}[mutation]
        changed = original.replace(fact, replacement, 1)
    assert not read_body(context, context[0].artifact.text.replace(original, changed, 1)).passed


@pytest.mark.parametrize('mutation', ['current_missing', 'current_time', 'pair_missing', 'pair_target',
    'first_revision_time', 'second_revision_time', 'second_revision_missing', 'revision_cause'])
def test_two_independent_revisions_reject_lost_or_reassigned_duties(two_independent_revisions_context, mutation):
    sources, context = two_independent_revisions_context
    body = context[0].artifact.text
    if mutation in {'first_revision_time', 'second_revision_time', 'second_revision_missing'}:
        original = context[0].artifact.observation
        # Expand the accepted shared frame for a change to only one source's
        # time. Both distinct time duties remain protected independently.
        before = f'「{sources[0]}」と、当時の気持ちを言い直されており、'
        second = f'「{sources[1]}」と、当時の気持ちを言い直されています。'
        line = original.splitlines()[-1]
        expanded = before + 'それとは別に' + second
        assert read_body(context, body.replace(line, expanded, 1)).passed
        if mutation == 'first_revision_time': before = before.replace('当時', '回答した時点', 1)
        elif mutation == 'second_revision_time': second = second.replace('当時', '回答した時点', 1)
        else: second = ''
        changed = original.replace(line, before + ('それとは別に' + second if second else ''), 1)
    else:
        original = context[0].artifact.reception
        old, new = {
            'current_missing': ('褒められたことについて、回答した時点では嬉しいのですね。', ''),
            'current_time': ('回答した時点では嬉しい', 'その時は嬉しい'),
            'pair_missing': ('頼まれたのに、寂しさを感じた', ''),
            'pair_target': ('頼まれたのに、寂しさ', '誘われたのに、寂しさ'),
            'revision_cause': (('二つの言い直しでは、どちらも' if original.startswith('二つの言い直しでは、どちらも')
                else '言い直してくださった気持ちは、' if original.startswith('言い直してくださった気持ちは、')
                else REVISION_INTRO), '誘われたことが原因で、'),
        }[mutation]
        changed = original.replace(old, new, 1)
    assert changed != original
    assert not read_body(context, body.replace(original, changed, 1)).passed


@pytest.mark.parametrize('slot', [0, 1])
@pytest.mark.parametrize('mutation', ['person', 'degree', 'polarity', 'tense'])
def test_two_independent_revisions_reject_each_feeling_change(two_independent_revisions_context, slot, mutation):
    sources, context = two_independent_revisions_context
    original = context[0].artifact.reception
    finite = INDEPENDENT_REVISION_FINITE[sources[slot]]
    offset = original.find(finite)
    if (slot and INDEPENDENT_REVISION_FINITE[sources[0]] == finite
        and not original.startswith('二つの言い直しでは、どちらも')):
        offset = original.find(finite, offset + len(finite))
    assert offset >= 0
    if mutation == 'person': changed_finite = finite.replace('あなた', '友人', 1) if 'あなた' in finite else '友人は' + finite
    elif mutation == 'degree': changed_finite = finite.replace('少し', '', 1) if '少し' in finite else '少し' + finite
    elif mutation == 'polarity':
        changed_finite = (finite.replace('くなかった', 'かった') if 'くなかった' in finite else
            finite[:-3] + 'ではなかった' if finite.endswith('だった') else finite[:-3] + 'くなかった')
    else:
        changed_finite = (finite[:-3] + 'だ' if finite.endswith('だった') else
            finite[:-5] + 'くない' if finite.endswith('くなかった') else finite[:-3] + 'い')
    changed = original[:offset] + changed_finite + original[offset + len(finite):]
    assert changed != original
    assert not read_body(context, context[0].artifact.text.replace(original, changed, 1)).passed


@pytest.mark.parametrize('sources', NONADJACENT_CORRECTION_SOURCES)
def test_two_independent_revisions_saved_rounds_reuse_every_source(qcase, qdb, monkeypatch, sources):
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
    for index, text in enumerate(two_independent_revision_answers(sources)):
        if index:
            current = run(cont(service, user, current, f'independent-revisions-continue-{index}'))
            saved_reads()
        current = run(answer(service, user, current, text, f'independent-revisions-answer-{index}'))
        assert current['body_state'] == 'REFINED', current
        saved_reads()
    body = current['current_observation']['text']
    assert all(source in body for source in sources)
    assert '嬉しくなかった' not in body and '悲しかった' not in body
    assert '「誘われた」という出来事がありました。' in body
    assert '頼まれたのに、寂しさを感じた' in body
    assert '回答した時点では嬉しいのですね。' in body
    assert current['state'] == 'COMPLETED' and not current['can_continue']


def test_shared_revision_reader_restores_each_distinct_source_without_authors(two_independent_revisions_context):
    sources, context = two_independent_revisions_context
    if sources[0] == '楽しかった':
        assert read_body(context, context[0].artifact.text).passed
        return  # Separate polarity Moves retain their existing individual readers.
    result, plan, _, resolver, selected = context
    move, = [m for m in plan.response_plan.human_reception_plan.moves
             if not m.support_nucleus_ids and len(m.target_nucleus_ids) == 2]
    raw = result.artifact.reception.split('。')[0] + '。'
    with patch.object(reception, '_source_owned_detached_burden_sentence', side_effect=AssertionError('no author')), patch.object(
            reception, '_detached_feeling_finite_surface', side_effect=AssertionError('no finite author')):
        proof = gate._read_detached_burden_discourse(raw, move, plan, resolver, selected)
    assert proof is not None and len(proof) == 2
    assert [value.decode() for _, _, value in proof] == list(sources)
    if raw.startswith('二つの言い直しでは、どちらも'):
        assert proof[0][:2] == proof[1][:2]
    else:
        assert proof[0][1] < proof[1][0]
    assert all(raw.encode()[start:end] for start, end, _ in proof)


@pytest.mark.parametrize('old,new', [
    ('二つの言い直しでは、どちらも', ''),
    ('二つの言い直しでは、どちらも', '一つの言い直しでは、'),
    ('二つの言い直しでは、どちらも', '二つの言い直しでは、一方は'),
    ('二つの言い直しでは、どちらも', '二つの出来事が原因で、'),
    ('当時、', ''), ('当時、', '同時に、'), ('当時、', '回答した時点で、'),
])
@pytest.mark.parametrize('sources', NONADJACENT_CORRECTION_SOURCES[:3])
def test_shared_revision_rejects_lost_count_reference_or_time(sources, old, new):
    request = begin()
    for answer_text in two_independent_revision_answers(sources):
        request = advance(request, answer_text)
    context = actual(request=request)
    original = context[0].artifact.reception
    changed = original.replace(old, new, 1)
    assert changed != original
    assert not read_body(context, context[0].artifact.text.replace(original, changed, 1)).passed


@pytest.mark.parametrize('sources', [
    ('私も少し怖くなかったです', '私は少し怖くなかったです'),
    ('私は不安でした', '私は少し不安でした'),
    ('私は少し苦しかったです', '私は少し怖くなかったです'),
])
def test_unequal_revisions_cannot_borrow_one_shared_predicate(sources):
    request = begin()
    for answer_text in two_independent_revision_answers(sources):
        request = advance(request, answer_text)
    context = actual(request=request)
    original = context[0].artifact.reception
    intro = '言い直してくださった気持ちは、'
    assert original.startswith(intro) and 'し、それとは別に' in original
    first, rest = original[len(intro):].split('し、それとは別に', 1)
    changed = '二つの言い直しでは、どちらも' + first + 'のですね。' + rest.split('。', 1)[1]
    assert not read_body(context, context[0].artifact.text.replace(original, changed, 1)).passed


@pytest.mark.parametrize('sources', NONADJACENT_CORRECTION_SOURCES[:4])
def test_shared_revision_reader_keeps_previous_explicit_wording(sources):
    request = begin()
    for answer_text in two_independent_revision_answers(sources):
        request = advance(request, answer_text)
    context = actual(request=request)
    original = context[0].artifact.reception
    old_parts = [REVISION_INTRO + '当時、' + INDEPENDENT_REVISION_FINITE[s] for s in sources]
    old = old_parts[0] + 'し、それとは別に' + old_parts[1] + 'のですね。'
    changed = old + original.split('。', 1)[1]
    assert changed != original
    assert read_body(context, context[0].artifact.text.replace(original, changed, 1)).passed


@pytest.mark.parametrize('mutation', ['time_missing', 'answer_time', 'prior_time', 'simultaneous',
    'count_missing', 'one_only', 'cause', 'wrong_event', 'duplicate'])
def test_shared_observation_revision_rejects_frame_changes(two_independent_revisions_context, mutation):
    _, context = two_independent_revisions_context
    original = context[0].artifact.observation.splitlines()[-1]
    assert original.startswith('当時の気持ちを、')
    marker = '二つとも' if '二つとも' in original else 'それぞれ'
    old, new = {
        'time_missing': ('当時の', ''), 'answer_time': ('当時の', '回答した時点の'),
        'prior_time': ('当時の', '先の回答時点の'), 'simultaneous': ('当時の', '同時の'),
        'count_missing': (marker, ''), 'one_only': (marker, '一つだけ'),
        'cause': ('当時の気持ちを、', '誘われたことが原因で、当時の気持ちを、'),
        'wrong_event': ('当時の気持ちを、', '頼まれたことへの当時の気持ちを、'),
        'duplicate': (original, original + original),
    }[mutation]
    changed = original.replace(old, new, 1)
    assert changed != original
    assert not read_body(context, context[0].artifact.text.replace(original, changed, 1)).passed


@pytest.mark.parametrize('slot', [0, 1])
def test_shared_observation_revision_requires_each_sources_own_time(two_independent_revisions_context, slot):
    sources, context = two_independent_revisions_context
    result, plan, sentence, resolver, _ = context
    index = {n.nucleus_id: n for n in plan.nuclei}
    line, = [line for line in sentence.lines if len(line.binding.nucleus_ids) == 2
        and all('thread_subject:revised_original_reaction' in index[nid].semantic_frame.attribute_codes
                for nid in line.binding.nucleus_ids)]
    nuclei = tuple(index[nid] for nid in line.binding.nucleus_ids)
    assert len({n.nucleus_id for n in nuclei}) == len({n.source_span_ids for n in nuclei}) == 2
    raw = result.artifact.observation.splitlines()[-1]
    with patch.object(surface, '_render_observation', side_effect=AssertionError('no author oracle')):
        assert gate._body_inverse_detached_observation(raw, nuclei, plan, resolver)
        target = nuclei[slot]
        changed = replace(target, semantic_frame=replace(target.semantic_frame,
            attribute_codes=tuple('thread_time:answer_time' if c == 'thread_time:original_occasion' else c
                                  for c in target.semantic_frame.attribute_codes)))
        altered = tuple(changed if i == slot else n for i, n in enumerate(nuclei))
        assert not gate._body_inverse_detached_observation(raw, altered, plan, resolver)


@pytest.mark.parametrize('slot', [0, 1])
def test_shared_observation_revision_keeps_each_exact_quote(two_independent_revisions_context, slot):
    sources, context = two_independent_revisions_context
    original = context[0].artifact.observation.splitlines()[-1]
    quoted = f'「{sources[slot]}」'
    changed = original.replace(quoted, '「友人は嬉しかった」', 1)
    assert changed != original
    assert not read_body(context, context[0].artifact.text.replace(original, changed, 1)).passed


def test_shared_observation_revision_keeps_explicit_pair_and_equivalent_ending(two_independent_revisions_context):
    sources, context = two_independent_revisions_context
    original = context[0].artifact.observation.splitlines()[-1]
    expanded = (f'「{sources[0]}」と、当時の気持ちを言い直されており、それとは別に'
                f'「{sources[1]}」と、当時の気持ちを言い直されています。')
    for changed in (expanded, original.replace('言い直され', '言い換えられ')):
        assert changed != original
        assert read_body(context, context[0].artifact.text.replace(original, changed, 1)).passed


@pytest.mark.parametrize('sources', [s for s in NONADJACENT_CORRECTION_SOURCES if s[0] != s[1]])
@pytest.mark.parametrize('mutation', ['swap', 'duplicate_first', 'share_first'])
def test_shared_observation_revision_cannot_exchange_or_merge_distinct_sources(sources, mutation):
    req = begin()
    for text in two_independent_revision_answers(sources):
        req = advance(req, text)
    context = actual(request=req)
    original = context[0].artifact.observation.splitlines()[-1]
    quoted = ('二つとも' + f'「{sources[0]}」' if mutation == 'share_first'
              else 'それぞれ' + (f'「{sources[1]}」、「{sources[0]}」' if mutation == 'swap'
                                  else f'「{sources[0]}」、「{sources[0]}」'))
    changed = f'当時の気持ちを、{quoted}と言い直されています。'
    assert changed != original
    assert not read_body(context, context[0].artifact.text.replace(original, changed, 1)).passed


# ABOUT remains tied to each event even after its original contrast is
# revised. Read the new sentence independently, including polite/unknown
# answers and a corrected prior answer; no author replay supplies its time.
NONSHARED_ABOUT_ANSWERS = [
    ('今は嬉しい。', '回答した時点', '嬉しい'),
    ('その時は重かった。', 'その時', '重かった'),
    ('今は少し不安です。', '回答した時点', '少し不安です'),
    ('今は私も怖くないです。', '回答した時点', '私も怖くないです'),
    ('今はわからない。', '回答した時点', 'わからない'),
    ('prior', '先の回答時点', '私は苦しいです'),
    ('grouped', 'その時', '私は少し不安でした'),
]


@pytest.fixture(scope='module', params=NONSHARED_ABOUT_ANSWERS)
def nonshared_about_context(request):
    answer_text, when, source = request.param
    if answer_text == 'grouped':
        req = begin('褒められたのに、嬉しくなかった。誘われたのに、悲しかった。')
        sequence = multiple_original_correction_answers((source, source))
    elif answer_text == 'prior':
        req = begin()
        sequence = ('今は私は重いです。', '「私は重いです」ではなく「私は苦しいです」です。',
                    '「嬉しくなかった」ではなく「怖くなかった」です。')
    else:
        req = begin()
        sequence = (answer_text, '「嬉しくなかった」ではなく「少し苦しかった」です。')
    for text in sequence:
        req = advance(req, text)
    return actual(request=req), when, source, answer_text == 'grouped'


def test_nonshared_about_reads_event_time_and_complete_answer(nonshared_about_context):
    context, when, source, grouped = nonshared_about_context
    observation = context[0].artifact.observation
    clause = f'「褒められた」ことについて、{when}の受け止めは「{source}」'
    if grouped:
        assert observation == (clause + 'とあり、また'
            f'「誘われた」ことについて、その時の受け止めは「{source}」と書かれています。')
    else:
        assert clause + 'と書かれています。' in observation
    assert read_body(context, context[0].artifact.text).passed


@pytest.mark.parametrize('ending', ['が見えます。', 'が示されています。'])
def test_nonshared_about_reads_complete_legacy_grammar(nonshared_about_context, ending):
    context, _, _, _ = nonshared_about_context
    body = context[0].artifact.text
    observation = context[0].artifact.observation
    legacy = observation.replace('」ことについて、', '」ことに対する')
    legacy = legacy.replace('の受け止めは', 'の受け止めとして、')
    legacy = legacy.replace('とあり、また', '、また').replace('と書かれています。', ending)
    assert legacy != observation
    assert read_body(context, body.replace(observation, legacy, 1)).passed


@pytest.mark.parametrize('mutation', ['event', 'time_missing', 'time_changed', 'answer',
    'cause', 'mixed_prefix', 'mixed_ending', 'extra_cause'])
def test_nonshared_about_rejects_reassignment_and_mixed_grammar(nonshared_about_context, mutation):
    context, when, source, grouped = nonshared_about_context
    observation = context[0].artifact.observation
    left = f'「褒められた」ことについて、{when}の受け止めは'
    changes = {
        'event': ('「褒められた」ことについて、', '「誘われた」ことについて、'),
        'time_missing': (left, '「褒められた」ことについて、受け止めは'),
        'time_changed': (left, '「褒められた」ことについて、'
                         + ('回答した時点' if when == 'その時' else 'その時') + 'の受け止めは'),
        'answer': (f'「{source}」', '「友人は嬉しい」'),
        'cause': ('「褒められた」ことについて、', '「褒められた」ことのせいで、'),
        'mixed_prefix': ('「褒められた」ことについて、', '「褒められた」ことに対する'),
        'mixed_ending': ('とあり、また', '、また') if grouped else ('と書かれています。', 'が見えます。'),
        'extra_cause': (f'「{source}」', f'「{source}」、それが悲しさの原因だ'),
    }
    old, new = changes[mutation]
    changed = observation.replace(old, new, 1)
    assert changed != observation
    assert not read_body(context, context[0].artifact.text.replace(observation, changed, 1)).passed


@pytest.mark.parametrize('nonshared_about_context', [NONSHARED_ABOUT_ANSWERS[-1]], indirect=True)
@pytest.mark.parametrize('legacy', [False, True])
@pytest.mark.parametrize('addition', ['それが原因で', 'そのため', '友人の反応として'])
def test_nonshared_about_rejects_invented_link_between_complete_clauses(
        nonshared_about_context, legacy, addition):
    context, _, _, _ = nonshared_about_context
    observation = context[0].artifact.observation
    if legacy:
        observation = observation.replace('」ことについて、', '」ことに対する')
        observation = observation.replace('の受け止めは', 'の受け止めとして、')
        observation = observation.replace('とあり、また', '、また').replace('と書かれています。', 'が見えます。')
    connector = '、また' if legacy else 'とあり、また'
    changed = observation.replace(connector, connector + addition, 1)
    assert changed != observation
    assert not read_body(context, context[0].artifact.text.replace(context[0].artifact.observation, changed, 1)).passed


@pytest.fixture(scope='module', params=[False, True])
def adjacent_about_time_context(request):
    req = begin()
    if request.param:
        req = advance(req, '今は嬉しい。')
    old = ('悲しかった', '寂しかった') if request.param else ('嬉しくなかった', '悲しかった')
    for previous, source in zip(old, ('私も少し怖くなかったです', '少し私には苦しかったです')):
        req = advance(req, f'「{previous}」ではなく「{source}」です。')
    return actual(request=req), request.param


def test_adjacent_about_shares_only_explanation_and_retains_each_pair(adjacent_about_time_context):
    context, prior = adjacent_about_time_context
    obs = context[0].artifact.observation
    events = ('誘われた', '頼まれた') if prior else ('褒められた', '誘われた')
    expected = (f'それぞれの出来事について、その時の受け止めとして、「{events[0]}」ことには「私も少し怖くなかったです」、'
                f'「{events[1]}」ことには「少し私には苦しかったです」と書かれています。')
    assert expected in obs and obs.count('の受け止めとして、') == 1
    if prior:
        assert obs.startswith('「褒められた」のに「嬉しくなかった」、')
        assert '回答した時点では「嬉しい」' in obs
    with patch.object(surface, '_render_relation', side_effect=AssertionError('no author oracle')):
        assert read_body(context, context[0].artifact.text).passed


@pytest.mark.parametrize('old,new', [
    ('その時の受け止めとして、', '回答した時点の受け止めとして、'),
    ('その時の受け止めとして、', '先の回答時点の受け止めとして、'),
    ('その時の受け止めとして、', '受け止めとして、'),
    ('その時の受け止めとして、', '友人のその時の受け止めとして、'),
    ('ことには', 'ことが原因で'),
    ('怖くなかったです」、「', '怖くなかったです」、そのため「'),
    ('怖くなかったです」、「', '怖くなかったです」、友人の反応として「'),
    ('私も少し怖くなかったです', '私も少し怖かったです'),
    ('私も少し怖くなかったです', '私も少し怖くないです'),
    ('私も少し怖くなかったです', '私は少し怖くなかったです'),
    ('少し私には苦しかったです', '私には苦しかったです'),
    ('少し私には苦しかったです', '少し友人には苦しかったです'),
    ('少し私には苦しかったです', '私も少し怖くなかったです'),
    ('と書かれています。', 'ので、嬉しくなったのですね。'),
])
def test_adjacent_about_rejects_time_source_actor_and_link_changes(adjacent_about_time_context, old, new):
    context, _ = adjacent_about_time_context
    obs = context[0].artifact.observation
    changed = obs.replace(old, new, 1)
    assert changed != obs
    with patch.object(surface, '_render_relation', side_effect=AssertionError('no author oracle')):
        assert not read_body(context, context[0].artifact.text.replace(obs, changed, 1)).passed


@pytest.mark.parametrize('mutation', ['swap', 'drop', 'duplicate', 'extra', 'swap_answers'])
def test_adjacent_about_requires_ordered_unique_event_answer_pairs(adjacent_about_time_context, mutation):
    context, prior = adjacent_about_time_context
    obs = context[0].artifact.observation
    events = ('誘われた', '頼まれた') if prior else ('褒められた', '誘われた')
    a = f'「{events[0]}」ことには「私も少し怖くなかったです」'
    b = f'「{events[1]}」ことには「少し私には苦しかったです」'
    joined = a + '、' + b
    changed = {'swap': b + '、' + a, 'drop': a, 'duplicate': a + '、' + a,
               'extra': joined + '、' + a,
               'swap_answers': f'「{events[0]}」ことには「少し私には苦しかったです」、「{events[1]}」ことには「私も少し怖くなかったです」'}[mutation]
    assert joined in obs
    assert not read_body(context, context[0].artifact.text.replace(joined, changed, 1)).passed


@pytest.mark.parametrize('prior', [False, True])
def test_adjacent_about_does_not_cross_middle_contrast_or_correction_tail(prior):
    req = advance(begin(), '今は嬉しい。') if prior else begin()
    for old, source in (('嬉しくなかった', '私は少し不安でした'), ('寂しかった', '私も少し怖くなかったです')):
        req = advance(req, f'「{old}」ではなく「{source}」です。')
    context = actual(request=req)
    obs = context[0].artifact.observation
    assert 'ことには' not in obs
    assert '「誘われた」と「悲しかった」' in obs
    assert read_body(context, context[0].artifact.text).passed


def test_adjacent_about_cannot_reassign_a_shared_event_to_another_answer():
    req = advance(begin(), '今は嬉しい。')
    for old, source in (('悲しかった', '私も少し怖くなかったです'), ('寂しかった', '少し私には苦しかったです')):
        req = advance(req, f'「{old}」ではなく「{source}」です。')
    context = actual(request=req)
    body = context[0].artifact.text
    old = '「頼まれた」ことには「少し私には苦しかったです」と書かれています。'
    new = '「頼まれた」ことには「少し私には苦しかったです」、「褒められた」ことには「私も少し怖くなかったです」と書かれています。'
    assert old in body and not read_body(context, body.replace(old, new, 1)).passed


@pytest.mark.parametrize('second', ['私は少し不安でした', '私も少し怖くなかったです'])
def test_repeated_event_wording_keeps_individual_about_clauses(second):
    req = begin('褒められたのに、嬉しくなかった。褒められたのに、悲しかった。頼まれたのに、寂しかった。')
    for old, source in zip(('嬉しくなかった', '悲しかった'), ('私は少し不安でした', second)):
        req = advance(req, f'「{old}」ではなく「{source}」です。')
    context = actual(request=req)
    observation = context[0].artifact.observation
    assert 'ことには' not in observation
    assert observation.count('「褒められた」ことについて、その時の受け止めは') == 2
    for source in ('私は少し不安でした', second):
        assert f'受け止めは「{source}」と書かれています。' in observation
    with patch.object(surface, '_render_relation', side_effect=AssertionError('no author oracle')):
        assert read_body(context, context[0].artifact.text).passed


def test_adjacent_about_saved_current_answer_and_past_pair_keep_original_and_reads(qcase, qdb, monkeypatch):
    user, parent, _ = qcase
    service = active(monkeypatch)
    first = current = run(service.start(user, parent))
    for index, text in enumerate(('今は嬉しい。', '「悲しかった」ではなく「私は少し不安でした」です。',
                                  '「寂しかった」ではなく「私も少し怖くなかったです」です。')):
        if index:
            current = run(cont(service, user, current, f'adjacent-about-continue-{index}'))
        current = run(answer(service, user, current, text, f'adjacent-about-answer-{index}'))
        assert current['body_state'] == 'REFINED'
        assert current['original'] == first['original']
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved reads must not regenerate'))
            assert run(service.get(user, parent)) == current
            assert run(service.start(user, parent)) == current
    body = current['current_observation']['text']
    assert 'それぞれの出来事について、その時の受け止めとして、' in body
    assert '回答した時点では「嬉しい」' in body
    assert '「誘われた」ことには「私は少し不安でした」、「頼まれた」ことには「私も少し怖くなかったです」' in body
    assert current['state'] == 'COMPLETED' and not current['can_continue']


def test_adjacent_about_cannot_repeat_a_complete_group(adjacent_about_time_context):
    context, _ = adjacent_about_time_context
    body = context[0].artifact.text
    group = re.search(r'それぞれの出来事について、その時の受け止めとして、[^。]+。', body)[0]
    assert not read_body(context, body.replace(group, group + ' ' + group, 1)).passed


@pytest.mark.parametrize('prior', [False, True])
@pytest.mark.parametrize('sources,finite', [
    (('少し私は苦しかったです', '私は少し苦しかったです'), 'あなたは少し苦し'),
    (('少し私は不安でした', '私は少し不安でした'), 'あなたは少し不安だった'),
    (('私も少し怖くなかったです', '私も少し怖くなかったです'), 'あなたも少し怖くな'),
    (('私は少し不安です', '私は少し不安です'), 'あなたは少し不安'),
])
def test_shared_event_feeling_retains_each_occasion_and_one_complete_predicate(prior, sources, finite):
    req = advance(begin(), '今は嬉しい。') if prior else begin()
    old = ('悲しかった', '寂しかった') if prior else ('嬉しくなかった', '悲しかった')
    events = ('誘われた', '頼まれた') if prior else ('褒められた', '誘われた')
    for previous, source in zip(old, sources):
        req = advance(req, f'「{previous}」ではなく「{source}」です。')
    context = actual(request=req)
    follow = context[0].artifact.reception
    assert f'{events[0]}時も、{events[1]}時も、{finite}' in follow
    assert follow.count(finite) == 1
    for source in sources:
        assert f'「{source}」' in context[0].artifact.observation
    if prior:
        assert '回答した時点では嬉しい' in follow
    with patch.object(reception, '_source_grounded_received_discourse', side_effect=AssertionError('no author oracle')):
        assert read_body(context, context[0].artifact.text).passed


@pytest.fixture(scope='module', params=[False, True])
def shared_event_feeling_context(request):
    req = advance(begin(), '今は嬉しい。') if request.param else begin()
    old = ('悲しかった', '寂しかった') if request.param else ('嬉しくなかった', '悲しかった')
    events = ('誘われた', '頼まれた') if request.param else ('褒められた', '誘われた')
    for previous in old:
        req = advance(req, f'「{previous}」ではなく「私も少し怖くなかったです」です。')
    return actual(request=req), events


@pytest.mark.parametrize('mutation', ['drop_first', 'drop_second', 'swap', 'duplicate',
    'time_first', 'time_second', 'simultaneous', 'cause', 'actor', 'particle',
    'degree', 'negation', 'tense', 'extra_event', 'contrast_event'])
def test_shared_event_feeling_rejects_lost_or_changed_meaning(shared_event_feeling_context, mutation):
    context, (first, second) = shared_event_feeling_context
    follow = context[0].artifact.reception
    pair = first + '時も、' + second + '時も、'
    old, new = {
        'drop_first': (first + '時も、', ''), 'drop_second': (second + '時も、', ''),
        'swap': (pair, second + '時も、' + first + '時も、'),
        'duplicate': (pair, first + '時も、' + first + '時も、'),
        'time_first': (first + '時も', first + 'ことへの回答した時点も'),
        'time_second': (second + '時も', second + 'ことへの先の回答時点も'),
        'simultaneous': (pair, '同時に' + pair), 'cause': (pair, pair + 'そのため'),
        'actor': ('あなたも', '友人も'), 'particle': ('あなたも', 'あなたは'),
        'degree': ('少し', ''), 'negation': ('怖くな', '怖'),
        'tense': ('怖くなかった' if '怖くなかった' in follow else '怖くなく', '怖くない'),
        'extra_event': (pair, pair + '断られた時も、'),
        'contrast_event': (pair, pair + ('褒められた' if first == '誘われた' else '頼まれた') + '時も、'),
    }[mutation]
    changed = follow.replace(old, new, 1)
    assert changed != follow
    with patch.object(reception, '_source_grounded_received_discourse', side_effect=AssertionError('no author oracle')):
        assert not read_body(context, context[0].artifact.text.replace(follow, changed, 1)).passed


@pytest.mark.parametrize('slot', [0, 1])
@pytest.mark.parametrize('field,value', [('time', 'answer_time'), ('actor', 'other_person'), ('polarity', 'positive')])
def test_shared_event_feeling_requires_each_sources_own_frame(slot, field, value):
    req = begin()
    for old in ('嬉しくなかった', '悲しかった'):
        req = advance(req, f'「{old}」ではなく「私は少し不安でした」です。')
    result, plan, _, resolver, selected = actual(request=req)
    move = plan.response_plan.human_reception_plan.moves[0]
    assert {'nucleus:s1:event', 'nucleus:s2:event'} <= set(move.target_nucleus_ids)
    follow = result.artifact.reception.split('。', 1)[0] + '。'
    answers = [n for n in plan.nuclei if n.source_fields == ('answer_text_private',)]
    target = answers[slot]
    if field == 'time':
        frame = replace(target.semantic_frame, attribute_codes=tuple(
            'thread_time:' + value if c.startswith('thread_time:') else c for c in target.semantic_frame.attribute_codes))
    else:
        frame = replace(target.semantic_frame, **{field:value})
    altered = replace(plan, nuclei=tuple(replace(n, semantic_frame=frame) if n == target else n for n in plan.nuclei))
    with patch.object(reception, '_source_grounded_received_discourse', side_effect=AssertionError('no author oracle')):
        assert gate.read_received_discourse(follow, move, plan, resolver, selected) is not None
        assert gate.read_received_discourse(follow, move, altered, resolver, selected) is None


@pytest.mark.parametrize('sources', [
    ('私は少し不安でした', '私も少し不安でした'),
    ('私は不安でした', '私は少し不安でした'),
    ('私は少し不安でした', '私は少し不安です'),
    ('私も少し怖くなかったです', '私は少し怖くなかったです'),
])
def test_shared_event_feeling_does_not_merge_different_complete_predicates(sources):
    req = begin()
    for old, source in zip(('嬉しくなかった', '悲しかった'), sources):
        req = advance(req, f'「{old}」ではなく「{source}」です。')
    context = actual(request=req)
    assert '時も、' not in context[0].artifact.reception
    assert read_body(context, context[0].artifact.text).passed


@pytest.mark.parametrize('repeated', [False, True])
def test_shared_event_feeling_keeps_nonadjacent_or_repeated_events_separate(repeated):
    memo = ('褒められたのに、嬉しくなかった。褒められたのに、悲しかった。頼まれたのに、寂しかった。'
            if repeated else '褒められたのに、嬉しくなかった。誘われたのに、悲しかった。頼まれたのに、寂しかった。')
    req = begin(memo)
    for old in ('嬉しくなかった', '悲しかった' if repeated else '寂しかった'):
        req = advance(req, f'「{old}」ではなく「私は少し不安でした」です。')
    context = actual(request=req)
    assert '時も、' not in context[0].artifact.reception
    assert read_body(context, context[0].artifact.text).passed


@pytest.mark.parametrize('ending', ['のです。', 'のだと受け取りました。'])
def test_shared_event_feeling_keeps_complete_legacy_form_and_equivalent_ending(ending):
    req = advance(begin(), '今は嬉しい。')
    for old in ('悲しかった', '寂しかった'):
        req = advance(req, f'「{old}」ではなく「私は少し不安でした」です。')
    context = actual(request=req)
    follow = context[0].artifact.reception
    shared = '誘われた時も、頼まれた時も、あなたは少し不安だったのですね。'
    assert shared in follow
    expanded = ('誘われた時は、あなたは少し不安だったし、頼まれた時は、あなたは少し不安だった' + ending)
    for replacement in (shared.removesuffix('のですね。') + ending, expanded):
        changed = follow.replace(shared, replacement, 1)
        assert read_body(context, context[0].artifact.text.replace(follow, changed, 1)).passed


def test_shared_event_feeling_saved_corrections_and_withdrawal_reuse_exact_dto(qcase, qdb, monkeypatch):
    user, parent, _ = qcase
    service = active(monkeypatch)
    first = current = run(service.start(user, parent))
    answers = ('「嬉しくなかった」ではなく「私は少し不安でした」です。',
               '「悲しかった」ではなく「私は少し不安でした」です。', '「褒められた」は誤りです。')
    for index, text in enumerate(answers):
        if index:
            current = run(cont(service, user, current, f'shared-event-continue-{index}'))
        current = run(answer(service, user, current, text, f'shared-event-answer-{index}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        body = current['current_observation']['text']
        if index == 1:
            assert '褒められた時も、誘われた時も、あなたは少し不安だった' in body
        if index == 2:
            assert '褒められた' not in body and '時も、' not in body
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved reads must not regenerate'))
            assert run(service.get(user, parent)) == current
            assert run(service.start(user, parent)) == current
    assert current['state'] == 'COMPLETED' and not current['can_continue']


@pytest.mark.parametrize('count', [2, 3])
@pytest.mark.parametrize('last', [False, True])
@pytest.mark.parametrize('positive,finite', [('今は嬉しい。', '嬉しい'),
    ('今は私も少し嬉しいです。', 'あなたも少し嬉しい')])
def test_temporal_edge_keeps_original_and_current_answer_adjacent(count, last, positive, finite):
    clauses = ('褒められたのに、嬉しくなかった。', '誘われたのに、悲しかった。', '頼まれたのに、寂しかった。')
    events = ('褒められた', '誘われた', '頼まれた')[:count]
    req = begin(''.join(clauses[:count]))
    for text in (*(('その時は重かった。', 'その時は怖かった。')[:count - 1] if last else ()), positive):
        req = advance(req, text)
    context = actual(request=req)
    result, plan, _, _, _ = context
    follow = result.artifact.reception
    parts = follow.split('。')[:-1]
    assert len(parts) == 2 and follow.count('のですね') == 2
    focus = 1 if last else 0
    assert parts[focus].startswith('当時、' + (events[-1] if last else events[0]))
    assert parts[focus].endswith('、回答した時点では' + finite + 'のですね')
    assert all(follow.count(event) == 1 for event in events)
    assert [follow.index(event) for event in events] == sorted(follow.index(event) for event in events)
    moves = plan.response_plan.human_reception_plan.moves
    assert len(moves) == 3 and all(m.required for m in moves)
    assert moves[focus].reception_act == 'stay_with_current_burden'
    assert moves[focus + 1].reception_act == 'recognize_lived_change'
    assert moves[focus].move_role == moves[focus + 1].move_role == 'felt_response'
    assert moves[2 if not last else 0].move_role == 'attention'
    assert len({reception.reception_move_predicate_family(m) for m in moves}) == 3
    assert read_body(context, result.artifact.text).passed


@pytest.fixture(scope='module', params=[False, True])
def temporal_edge_context(request):
    req = begin()
    for text in (*(('その時は重かった。', 'その時は怖かった。') if request.param else ()),
                 '今は私も少し嬉しいです。'):
        req = advance(req, text)
    return actual(request=req), request.param


@pytest.mark.parametrize('mutation', ['drop_original', 'drop_answer', 'drop_remaining', 'interpose',
    'swap_times', 'replace_event', 'answer_time', 'prior_time', 'original_polarity', 'answer_actor',
    'answer_particle', 'answer_degree', 'answer_polarity', 'cause', 'original_tense'])
def test_temporal_edge_independent_inverse_rejects_missing_or_reassigned_meaning(temporal_edge_context, mutation):
    context, last = temporal_edge_context
    follow = context[0].artifact.reception
    parts = follow.split('。')[:-1]
    focus = 1 if last else 0
    left, right = parts[focus].split('、回答した時点では', 1)
    parts[focus:focus + 1] = [left, '回答した時点では' + right]
    other = 0 if last else 2
    answer_slot = focus + 1
    if mutation.startswith('drop_'):
        slot = {'drop_original':focus, 'drop_answer':answer_slot, 'drop_remaining':other}[mutation]
        parts.pop(slot)
    elif mutation == 'interpose':
        parts = [parts[focus], parts[other], parts[answer_slot]]
    elif mutation == 'swap_times':
        parts[focus], parts[answer_slot] = parts[answer_slot], parts[focus]
    elif mutation == 'replace_event':
        parts[focus] = parts[focus].replace('頼まれた' if last else '褒められた', '誘われた', 1)
    elif mutation in {'answer_time', 'prior_time'}:
        parts[answer_slot] = parts[answer_slot].replace('回答した時点では',
            'その時は' if mutation == 'answer_time' else '先の回答時点では', 1)
    elif mutation == 'original_polarity':
        parts[focus] = parts[focus].replace('寂しさ', '嬉しさ') if last else parts[focus].replace('つながらず', 'つながり')
    elif mutation == 'original_tense':
        parts[focus] = parts[focus].replace('感じ', '感じる') if last else parts[focus].replace('つながらず', 'つながらない')
    elif mutation == 'cause':
        parts[answer_slot] = 'そのおかげで、' + parts[answer_slot]
    else:
        old, new = {'answer_actor':('あなたも', '友人も'), 'answer_particle':('あなたも', 'あなたは'),
            'answer_degree':('少し', ''), 'answer_polarity':('嬉しい', '嬉しくない')}[mutation]
        parts[answer_slot] = parts[answer_slot].replace(old, new, 1)
    if mutation not in {'drop_original', 'drop_answer', 'drop_remaining', 'interpose', 'swap_times'}:
        parts[focus:answer_slot + 1] = [parts[focus] + '、' + parts[answer_slot]]
    changed = '。'.join(parts) + '。'
    assert changed != follow
    assert not read_body(context, context[0].artifact.text.replace(follow, changed, 1)).passed


def test_temporal_edge_prior_answer_and_complete_acknowledgement_remain_supported():
    req = advance(advance(begin(), '今は嬉しい。'), '「嬉しい」ではなく「少し楽しい」です。')
    context = actual(request=req)
    follow = context[0].artifact.reception
    assert 'つながらず、先の回答時点では少し楽しいのですね。' in follow
    assert follow.count('褒められた') == 1
    for ending in ('のですね', 'のです', 'のだと受け取りました'):
        changed = follow.replace('楽しいのですね。', '楽しい' + ending + '。', 1)
        assert read_body(context, context[0].artifact.text.replace(follow, changed, 1)).passed
    assert not read_body(context, context[0].artifact.text.replace('先の回答時点では', '回答した時点では', 1)).passed


@pytest.mark.parametrize('sequence', [('その時は重かった。', '今は嬉しい。'), ('その時は嬉しかった。',),
    ('今は嬉しい。', '「褒められた」は誤りです。'), ('今は嬉しい。', '「嬉しくなかった」ではなく「重かった」です。')])
def test_temporal_edge_does_not_reorder_middle_past_or_detached_duties(sequence):
    req = begin()
    for text in sequence:
        req = advance(req, text)
    context = actual(request=req)
    assert 'selection:source_owned_answer_adjacent' not in context[1].response_plan.human_reception_plan.depth_policy.selection_reason_codes
    assert read_body(context, context[0].artifact.text).passed


@pytest.mark.parametrize('withdraw', ['褒められた', '誘われた'])
def test_temporal_edge_saved_correction_and_withdrawal_reuse_original_and_body(qcase, qdb, monkeypatch, withdraw):
    user, parent, _ = qcase
    service = active(monkeypatch)
    first = current = run(service.start(user, parent))
    for index, text in enumerate(('今は嬉しい。', '「嬉しい」ではなく「少し楽しい」です。', f'「{withdraw}」は誤りです。')):
        if index:
            current = run(cont(service, user, current, f'temporal-edge-continue-{index}'))
        current = run(answer(service, user, current, text, f'temporal-edge-answer-{index}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        follow = current['current_observation']['text'].split('Emlisから：', 1)[1]
        if index < 2:
            assert follow.count('褒められた') == 1
            assert '当時、褒められたことは、嬉しさにはつながらず、' in follow
            assert ('回答した時点では嬉しい' if not index else '先の回答時点では少し楽しい') in follow
        else:
            assert withdraw not in current['current_observation']['text']
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved reads must not regenerate'))
            assert run(service.get(user, parent)) == current
            assert run(service.start(user, parent)) == current
    assert current['state'] == 'COMPLETED' and not current['can_continue']


@pytest.mark.parametrize('old,new', [
    ('当時、', ''), ('当時、', '今、'), ('当時、', '当時からずっと、'),
    ('当時、', '同時に、'), ('当時、', '当時、当時、'),
    ('、回答した時点では', '、そのため回答した時点では'),
    ('、回答した時点では', '、その後は'),
    ('、回答した時点では', '、回答した時点でも'),
    ('、回答した時点では', '、誘われたことについて、回答した時点では'),
    ('嬉しいのですね', '嬉しくなれたのですね'),
])
def test_temporal_pair_keeps_each_time_and_adds_no_relation(temporal_edge_context, old, new):
    context, _ = temporal_edge_context
    follow = context[0].artifact.reception
    changed = follow.replace(old, new, 1)
    assert changed != follow
    with patch.object(reception, '_source_grounded_received_discourse', side_effect=AssertionError('no author')):
        assert not read_body(context, context[0].artifact.text.replace(follow, changed, 1)).passed


@pytest.mark.parametrize('source_role,field,value', [
    ('original', 'actor', 'other_person'), ('original', 'time_scope', 'present'),
    ('original', 'polarity', 'positive'), ('answer', 'actor', 'other_person'),
    ('answer', 'time_scope', 'past'), ('answer', 'polarity', 'negative'),
])
def test_temporal_pair_proves_both_source_frames(temporal_edge_context, source_role, field, value):
    context, last = temporal_edge_context
    result, plan, _, resolver, selected = context
    moves = plan.response_plan.human_reception_plan.moves
    pair = moves[1:3] if last else moves[:2]
    nid = pair[0].support_nucleus_ids[0] if source_role == 'original' else pair[1].target_nucleus_ids[0]
    target = next(n for n in plan.nuclei if n.nucleus_id == nid)
    changed = replace(plan, nuclei=tuple(replace(n, semantic_frame=replace(n.semantic_frame, **{field:value}))
        if n == target else n for n in plan.nuclei))
    raw = result.artifact.reception.split('。')[1 if last else 0] + '。'
    assert gate.read_detached_feeling_pair(raw, pair, plan, resolver, selected) is not None
    assert gate.read_detached_feeling_pair(raw, pair, changed, resolver, selected) is None


def test_temporal_pair_source_ranges_do_not_cross_time_boundary(temporal_edge_context):
    context, last = temporal_edge_context
    result, plan, _, resolver, selected = context
    pair = plan.response_plan.human_reception_plan.moves[1:3] if last else plan.response_plan.human_reception_plan.moves[:2]
    raw = result.artifact.reception.split('。')[1 if last else 0] + '。'
    first, second = gate.read_detached_feeling_pair(raw, pair, plan, resolver, selected)
    boundary = raw.encode().index('、回答した時点では'.encode())
    assert first and second
    assert all(0 <= a < b <= boundary for a, b, _ in first)
    assert all(boundary < a < b <= len(raw.encode()) for a, b, _ in second)
    assert {source.decode() for _, _, source in first} == {'寂しかった' if last else '嬉しくなかった'}
    assert {source.decode() for _, _, source in second} == {'私も少し嬉しいです'}


def test_temporal_pair_does_not_expand_single_event_sentence_budget():
    context = actual(request=advance(begin('褒められたのに、嬉しくなかった。'), '今は嬉しい。'))
    plan = context[1]
    assert plan.response_plan.human_reception_plan.depth_policy.max_moves_per_sentence == 1
    assert '当時、' not in context[0].artifact.reception
    assert read_body(context, context[0].artifact.text).passed


@pytest.mark.parametrize('layout', ['front', 'front-past', 'front-current', 'back'])
@pytest.mark.parametrize('sources,finite', [
    (('少し私は苦しかったです', '私は少し苦しかったです'), 'あなたは少し苦しかった'),
    (('少し私は不安でした', '私は少し不安でした'), 'あなたは少し不安だった'),
    (('私も少し怖くなかったです', '私も少し怖くなかったです'), 'あなたも少し怖くなかった'),
    (('私は少し不安です', '私は少し不安です'), 'あなたは少し不安な'),
])
def test_adjacent_revisions_close_before_other_occasion(layout, sources, finite):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    req = begin()
    old = ('嬉しくなかった', '悲しかった')
    events, remaining, shared_position = ('褒められた', '誘われた'), '頼まれた', 0
    if layout == 'back':
        req = advance(req, 'その時は少し重かった。')
        old, events, remaining, shared_position = ('悲しかった', '寂しかった'), ('誘われた', '頼まれた'), '褒められた', 1
    for previous, source in zip(old, sources):
        req = advance(req, f'「{previous}」ではなく「{source}」です。')
    if layout in {'front-past', 'front-current'}:
        req = advance(req, 'その時は少し重かった。' if layout == 'front-past' else '今は少し苦しい。')
    context = actual(request=req)
    result, plan, _, _, _ = context
    follow = result.artifact.reception
    sentences = follow.split('。')[:-1]
    assert len(sentences) == 2
    shared, separate = sentences[shared_position], sentences[1-shared_position]
    assert shared == events[0] + '時も、' + events[1] + '時も、' + finite + 'のですね'
    assert remaining not in shared and remaining in separate
    assert all(event not in separate for event in events)
    assert all(previous not in result.artifact.text for previous in old)
    if layout == 'front-current':
        assert '回答した時点では少し苦しい' in separate
    elif layout in {'back', 'front-past'}:
        assert '少し重かった' in separate
    moves = plan.response_plan.human_reception_plan.moves
    assert len(moves) == 2 and len(moves[shared_position].target_nucleus_ids) == 2
    owned = [set((*m.target_nucleus_ids, *m.support_nucleus_ids)) for m in moves]
    assert owned[0].isdisjoint(owned[1])
    for relation in plan.relations:
        if relation.retention == 'required':
            assert sum({relation.from_nucleus_id, relation.to_nucleus_id} <= ids for ids in owned) == 1
    assert MeaningExperienceEngine().generate(req).artifact.text == result.artifact.text
    assert read_body(context, result.artifact.text).passed
    changes = [follow.replace(shared + '。', '', 1), follow.replace(separate + '。', '', 1),
               follow.replace(separate, shared, 1), follow.replace(events[1], remaining, 1),
               follow.replace('時も', '回答した時点も', 1), follow.replace('あなた', '相手', 1),
               follow.replace('少し', '', 1), follow.replace('あなたも', 'あなたは', 1)
                   if 'あなたも' in follow else follow.replace('あなたは', 'あなたも', 1)]
    for changed in changes:
        assert changed != follow and not read_body(context, result.artifact.text.replace(follow, changed, 1)).passed


@pytest.mark.parametrize('back', [False, True])
@pytest.mark.parametrize('sources,retained', [
    (('私は少し不安でした', '私も少し不安でした'), ('あなたは少し不安だった', 'あなたも少し不安だった')),
    (('私は不安でした', '私は少し不安でした'), ('あなたは不安だった', 'あなたは少し不安だった')),
    (('私は少し不安でした', '私は少し不安です'), ('あなたは少し不安だった', 'あなたは少し不安な')),
    (('私も少し怖くなかったです', '私は少し怖かったです'), ('あなたも少し怖くなく', 'あなたは少し怖かった')),
])
def test_adjacent_revisions_keep_different_predicates(back, sources, retained):
    req = advance(begin(), '今は少し重い。') if back else begin()
    old = ('悲しかった', '寂しかった') if back else ('嬉しくなかった', '悲しかった')
    events = ('誘われた', '頼まれた') if back else ('褒められた', '誘われた')
    for previous, source in zip(old, sources):
        req = advance(req, f'「{previous}」ではなく「{source}」です。')
    context = actual(request=req)
    body, follow = context[0].artifact.text, context[0].artifact.reception
    sentences = follow.split('。')[:-1]
    assert len(sentences) == 2 and '時も、' not in follow
    selected = sentences[int(back)]
    assert all(event in selected for event in events) and all(value in selected for value in retained)
    assert ('褒められた' if back else '頼まれた') not in selected
    assert read_body(context, body).passed
    changed = follow.replace(retained[1], retained[0], 1)
    assert changed != follow and not read_body(context, body.replace(follow, changed, 1)).passed


@pytest.mark.parametrize('back', [False, True])
def test_adjacent_revisions_read_complete_repeated_self_nominals(back):
    req = advance(begin(), 'その時は少し重かった。') if back else begin()
    old = ('悲しかった', '寂しかった') if back else ('嬉しくなかった', '悲しかった')
    for previous in old:
        req = advance(req, f'「{previous}」ではなく「私は私には少し不安だったのです」です。')
    context = actual(request=req)
    body, follow = context[0].artifact.text, context[0].artifact.reception
    sentences = follow.split('。')[:-1]
    assert len(sentences) == 2
    nominal = '私は私には少し不安だったのだという、その時のあなたの気持ち'
    assert sentences[int(back)].count(nominal) == 2
    assert read_body(context, body).passed
    for old, new in [(nominal, ''), ('私には', '私にも'), ('私は', '相手は'),
                     ('少し', ''), ('不安だった', '不安ではなかった'), ('その時の', '回答した時点の'),
                     ('のだという', 'という')]:
        changed = follow.replace(old, new, 1)
        assert changed != follow and not read_body(context, body.replace(follow, changed, 1)).passed


@pytest.mark.parametrize('replies', [
    ('「嬉しくなかった」ではなく「私は少し不安でした」です。',
     '「悲しかった」ではなく「私は少し不安でした」です。', '今は少し苦しい。'),
    ('その時は少し重かった。', '「悲しかった」ではなく「私は少し不安でした」です。',
     '「寂しかった」ではなく「私も少し怖くなかったです」です。'),
    ('「嬉しくなかった」ではなく「私は私には少し不安だったのです」です。',
     '「悲しかった」ではなく「私は私には少し不安だったのです」です。', '「頼まれた」は誤りです。'),
    ('「嬉しくなかった」ではなく「私は少し不安でした」です。',
     '「悲しかった」ではなく「私も少し怖くなかったです」です。',
     '「私も少し怖くなかったです」ではなく「私も少し寂しかったです」です。'),
])
def test_adjacent_revisions_saved_updates_keep_original_and_exact_reads(qcase, qdb, monkeypatch, replies):
    user, parent, _ = qcase
    service = active(monkeypatch)
    first = current = run(service.start(user, parent))
    for position, text in enumerate(replies):
        if position:
            current = run(cont(service, user, current, f'adjacent-scope-continue-{position}'))
        current = run(answer(service, user, current, text, f'adjacent-scope-answer-{position}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        body = current['current_observation']['text']
        if 'ではなく' in text:
            removed = text.split('「')[1].split('」')[0]
            assert removed not in body
        if position == 1 and replies[0].startswith('「嬉しくなかった」'):
            assert len(body.split('Emlisから：', 1)[1].strip().split('。')[:-1]) == 2
        if text == '「頼まれた」は誤りです。':
            assert '頼まれた' not in body and '寂しかった' in body
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved adjacent revisions must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current


@pytest.mark.parametrize('source', [
    '私も少し怖くなかったです', '私は少し苦しかったです',
    '少し私は苦しいです', '少し怖いです',
])
def test_answer_adjective_politeness_does_not_modify_koto(source):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    memo = '褒められたのに、嬉しくなかった。誘われたのに、悲しかった。褒められたのに、寂しかった。'
    req = advance(begin(memo), '「嬉しくなかった」ではなく「私は少し不安でした」です。')
    req = advance(req, 'その時は少し重かった。')
    req = advance(req, f'「寂しかった」ではなく「{source}」です。')
    context = actual(request=req)
    body, follow = context[0].artifact.text, context[0].artifact.reception
    nominal = 'その時に' + source[:-2] + 'こと'
    finite = {'私も少し怖くなかったです': 'あなたも少し怖くなかった',
              '私は少し苦しかったです': 'あなたは少し苦しかった',
              '少し私は苦しいです': 'あなたは少し苦しい',
              '少し怖いです': '少し怖い'}[source]
    # Test the source-owned adjective in either existing grammatical form.
    # Scope every change to this answer, not an earlier owner or modifier.
    target = nominal if nominal in follow else finite
    assert source in context[0].artifact.observation
    assert target in follow and 'ですこと' not in follow
    assert MeaningExperienceEngine().generate(req).artifact.text == body
    assert read_body(context, body).passed
    replacements = ['その時に' + source + 'こと',
                    target.replace('その時に', '回答した時点で', 1)
                    if target == nominal else '回答した時点では' + target,
                    target.replace('少し', '', 1), '']
    owner = '私' if target == nominal else 'あなた'
    if '私' in source:
        replacements += [target.replace(owner, '相手', 1),
                         target.replace(owner + 'も', owner + 'は', 1) if '私も' in source
                         else target.replace(owner + 'は', owner + 'も', 1)]
    if '怖くなかった' in source:
        replacements.append(target.replace('怖くなかった', '怖かった', 1))
    changes = [follow.replace(target, changed, 1) for changed in replacements]
    scope = ('褒められたことについて、' if target == nominal else '褒められた時は、') + target
    assert scope in follow
    changes.append(follow.replace(scope, scope.replace('褒められた', '誘われた', 1), 1))
    for changed in changes:
        assert changed != follow and not read_body(context, body.replace(follow, changed, 1)).passed


@pytest.mark.parametrize('when', ['その時は', '今は'])
@pytest.mark.parametrize('source', ['私も少し怖くないです', '少し私は苦しいです'])
def test_answer_adjective_politeness_keeps_added_answer_time(when, source):
    memo = '褒められたのに、嬉しくなかった。誘われたのに、悲しかった。褒められたのに、寂しかった。'
    req = advance(begin(memo), '「嬉しくなかった」ではなく「私は少し不安でした」です。')
    req = advance(req, 'その時は少し重かった。')
    context = actual(request=advance(req, when + source + '。'))
    body, follow = context[0].artifact.text, context[0].artifact.reception
    prefix = 'その時に' if when == 'その時は' else '回答した時点で'
    nominal = prefix + source[:-2] + 'こと'
    assert nominal in follow and 'ですこと' not in follow
    assert source in context[0].artifact.observation
    assert read_body(context, body).passed
    changed = follow.replace(prefix, '回答した時点で' if when == 'その時は' else 'その時に', 1)
    assert changed != follow and not read_body(context, body.replace(follow, changed, 1)).passed


@pytest.mark.parametrize('last', [
    '「寂しかった」ではなく「私も少し怖くなかったです」です。',
    '今は私も少し怖くないです。',
])
def test_answer_adjective_politeness_saved_updates_keep_original_and_exact_reads(qcase, qdb, monkeypatch, last):
    user, parent, _ = qcase
    memo = '褒められたのに、嬉しくなかった。誘われたのに、悲しかった。褒められたのに、寂しかった。'
    assert 'code' not in qdb.query('update public.emotions set memo=$2 where id=$1', [parent, memo])
    service = active(monkeypatch)
    first = current = run(service.start(user, parent))
    for position, text in enumerate((
        '「嬉しくなかった」ではなく「私は少し不安でした」です。',
        'その時は少し重かった。',
        last,
    )):
        if position:
            current = run(cont(service, user, current, f'adjective-continue-{position}'))
        current = run(answer(service, user, current, text, f'adjective-answer-{position}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        if position == 2:
            body = current['current_observation']['text']
            assert 'ですこと' not in body
            if last.startswith('「'):
                assert ('その時に私も少し怖くなかったこと' in body
                        or '褒められた時は、あなたも少し怖くなかった' in body)
                assert '寂しかった' not in body and '私も少し怖くなかったです' in body
            else:
                assert '回答した時点で私も少し怖くないこと' in body
                assert '寂しかった' in body and '私も少し怖くないです' in body
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved adjective nominal must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current


@pytest.mark.parametrize('event', ['褒められた', '頼まれた', '私は褒められた', 'わたしが褒められた'])
def test_repeated_edge_events_retain_all_three_accepted_occasions(event):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    memo = f'{event}のに、嬉しくなかった。誘われたのに、悲しかった。{event}のに、寂しかった。'
    req = advance(begin(memo), '「嬉しくなかった」ではなく「私は少し不安でした」です。')
    req = advance(req, 'その時は少し重かった。')
    req = advance(req, '「寂しかった」ではなく「私も少し怖くなかったです」です。')
    context = actual(request=req)
    body, follow = context[0].artifact.text, context[0].artifact.reception
    visible = re.sub(r'^(?:私|わたし)(?=は|が)', 'あなた', event)
    clauses = [visible + '時は、あなたは少し不安だった',
               '誘われたのに、悲しかったし、その時は少し重かった',
               visible + '時は、あなたも少し怖くなかった']
    assert all(clause in follow for clause in clauses)
    assert [follow.index(clause) for clause in clauses] == sorted(follow.index(clause) for clause in clauses)
    assert follow.count('のですね') == 1 and '寂しかった' not in body and '嬉しくなかった' not in body
    assert MeaningExperienceEngine().generate(req).artifact.text == body
    assert read_body(context, body).passed
    for clause in clauses:
        for changed in ('', clause.replace('少し', '', 1), (clause.replace('その時は', '回答した時点では', 1) if 'その時は' in clause else clause.replace('時は', '今は', 1))):
            assert changed != clause
            assert not read_body(context, body.replace(follow, follow.replace(clause, changed, 1), 1)).passed
    changed = follow.replace(clauses[0], clauses[2], 1)
    assert not read_body(context, body.replace(follow, changed, 1)).passed
    if visible != event:
        for replacement in (event, visible.replace('あなた', '相手', 1), visible.replace('が', 'は') if 'が' in visible else visible.replace('は', 'が')):
            changed = follow.replace(visible, replacement, 1)
            assert changed != follow and not read_body(context, body.replace(follow, changed, 1)).passed


@pytest.mark.parametrize('owner', ['私', '自分'])
def test_repeated_edge_events_saved_reads_keep_all_occasions(qcase, qdb, monkeypatch, owner):
    user, parent, _ = qcase
    memo = f'{owner}は褒められたのに、嬉しくなかった。誘われたのに、悲しかった。{owner}は褒められたのに、寂しかった。'
    assert 'code' not in qdb.query('update public.emotions set memo=$2 where id=$1', [parent, memo])
    service = active(monkeypatch)
    first = current = run(service.start(user, parent))
    for position, text in enumerate(('「嬉しくなかった」ではなく「私は少し不安でした」です。',
                                     'その時は少し重かった。',
                                     '「寂しかった」ではなく「私も少し怖くなかったです」です。')):
        if position:
            current = run(cont(service, user, current, f'edge-continue-{position}'))
        current = run(answer(service, user, current, text, f'edge-answer-{position}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        if position == 2:
            observation, follow = current['current_observation']['text'].split('Emlisから：', 1)
            assert f'{owner}は褒められた' in observation
            assert follow.count('あなたは褒められた時は') == 2
            assert all(value in follow for value in ('あなたは少し不安だった', '誘われたのに、悲しかったし、その時は少し重かった', 'あなたも少し怖くなかった'))
            assert '寂しかった' not in observation and '嬉しくなかった' not in observation
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved occurrence replies must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current


def test_repeated_edge_events_preserve_complete_owned_nominal_scopes():
    source = '私は私には少し不安だったのです'
    memo = '褒められたのに、嬉しくなかった。誘われたのに、悲しかった。褒められたのに、寂しかった。'
    req = advance(begin(memo), f'「嬉しくなかった」ではなく「{source}」です。')
    req = advance(req, 'その時は少し重かった。')
    context = actual(request=advance(req, f'「寂しかった」ではなく「{source}」です。'))
    body, follow = context[0].artifact.text, context[0].artifact.reception
    owned = '褒められたことについて、私は私には少し不安だったのだという、その時のあなたの気持ち'
    assert follow.count(owned) == 2
    assert '誘われたのに悲しかったこと' in follow and 'その時に少し重かったこと' in follow
    assert 'のですこと' not in follow and follow.count('受け止めています') == 1
    assert read_body(context, body).passed
    for target, changed in ((owned, ''), (owned, owned.replace('私には', '相手には', 1)),
                            (owned, owned.replace('その時の', '回答した時点の', 1)),
                            ('少し重かったこと', '少し軽かったこと')):
        assert not read_body(context, body.replace(follow, follow.replace(target, changed, 1), 1)).passed


@pytest.mark.parametrize('corruption', ['source_range', 'source_order', 'relation_source', 'relation_owner', 'answer_time', 'answer_actor'])
def test_repeated_edge_events_require_occurrence_provenance(corruption):
    from emlis_ai_grounded_observation_plan import _thread_retained_reaction_groups
    memo = '褒められたのに、嬉しくなかった。誘われたのに、悲しかった。褒められたのに、寂しかった。'
    req = advance(begin(memo), '「嬉しくなかった」ではなく「私は少し不安でした」です。')
    req = advance(req, 'その時は少し重かった。')
    plan = actual(request=advance(req, '「寂しかった」ではなく「私も少し怖くなかったです」です。'))[1]
    nuclei, relations = list(plan.nuclei), list(plan.relations)
    groups = _thread_retained_reaction_groups(nuclei, relations)
    assert len(groups) == 1 and len(groups[0][1]) == 3
    events = groups[0][1]
    about = next(r for r in relations if r.type == 'evaluation_about_event' and r.from_nucleus_id == events[0])
    nid = about.to_nucleus_id if corruption.startswith('answer_') else events[0]
    pos = next(i for i, n in enumerate(nuclei) if n.nucleus_id == nid)
    n = nuclei[pos]
    if corruption == 'source_range':
        codes = tuple(c for c in n.semantic_frame.attribute_codes if not c.startswith('source_fragment_scalar_range:'))
        nuclei[pos] = replace(n, semantic_frame=replace(n.semantic_frame, attribute_codes=codes))
    elif corruption == 'source_order':
        last = next(n for n in nuclei if n.nucleus_id == events[-1])
        nuclei[pos] = replace(n, source_span_ids=last.source_span_ids)
    elif corruption == 'relation_source':
        relations[relations.index(about)] = replace(about, source_span_ids=about.source_span_ids + about.source_span_ids[:1])
    elif corruption == 'relation_owner':
        relations[relations.index(about)] = replace(about, from_nucleus_id=events[-1])
    elif corruption == 'answer_time':
        codes = tuple('thread_time:answer_time' if c == 'thread_time:original_occasion' else c for c in n.semantic_frame.attribute_codes)
        nuclei[pos] = replace(n, semantic_frame=replace(n.semantic_frame, attribute_codes=codes))
    else:
        nuclei[pos] = replace(n, semantic_frame=replace(n.semantic_frame, actor='other_person'))
    assert _thread_retained_reaction_groups(nuclei, relations) != groups


@pytest.mark.parametrize('events,initial,middle', [
    (('褒められた', '私は誘われた', '自分は誘われた'), True, 'その時は少し重かった。'),
    (('私は誘われた', '自分は誘われた', 'わたしは誘われた'), True, 'その時は少し重かった。'),
    (('褒められた', '私は誘われた', '自分は誘われた'), False, 'その時は少し重かった。'),
    (('私は誘われた', '自分は誘われた', 'わたしは誘われた'), False, 'その時は少し重かった。'),
    (('褒められた', '私が誘われた', '自分が誘われた'), False, 'その時は少し重かった。'),
    (('褒められた', '私は誘われた', '自分は誘われた'), False, '今は少し苦しい。'),
])
def test_equal_visible_event_names_keep_finite_source_occurrences(events, initial, middle):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    memo = ''.join(event + 'のに、' + feeling + '。' for event, feeling in zip(events, ('嬉しくなかった', '悲しかった', '寂しかった')))
    req = begin(memo)
    if not initial:
        for reply in ('「嬉しくなかった」ではなく「私は少し不安でした」です。', middle,
                      '「寂しかった」ではなく「私も少し怖くなかったです」です。'):
            req = advance(req, reply)
    context = actual(request=req)
    body, follow = context[0].artifact.text, context[0].artifact.reception
    assert '受け止めています' not in follow and follow.count('のですね') == 1
    assert all(event in context[0].artifact.observation for event in events)
    assert not re.search(r'(?:私|自分|わたし)(?:は|が)', follow)
    if initial:
        expected = ('嬉しさにはつながらず', '悲しさを感じ', '寂しさを感じた')
    else:
        expected = ('あなたは少し不安だった', '回答した時点では少し苦しい' if middle.startswith('今は') else '少し重かった',
                    'あなたも少し怖くなかった')
        assert ('のに、悲しかったし、回答した時点では' if middle.startswith('今は') else 'のに、悲しかったし、その時は') in follow
        assert '嬉しくなかった' not in body and '寂しかった' not in body
    positions = [follow.index(value) for value in expected]
    assert positions == sorted(positions)
    assert MeaningExperienceEngine().generate(req).artifact.text == body
    assert read_body(context, body).passed


@pytest.fixture(scope='module')
def equal_visible_event_context():
    memo = '褒められたのに、嬉しくなかった。私は誘われたのに、悲しかった。自分は誘われたのに、寂しかった。'
    req = advance(begin(memo), '「嬉しくなかった」ではなく「私は少し不安でした」です。')
    req = advance(req, 'その時は少し重かった。')
    return actual(request=advance(req, '「寂しかった」ではなく「私も少し怖くなかったです」です。'))


@pytest.mark.parametrize('change', ['missing', 'duplicate', 'swap', 'degree', 'negative', 'particle', 'actor', 'time', 'cause'])
def test_equal_visible_event_names_reject_missing_extra_or_reassigned_clauses(equal_visible_event_context, change):
    context = equal_visible_event_context
    body, follow = context[0].artifact.text, context[0].artifact.reception
    middle = 'あなたは誘われたのに、悲しかったし、その時は少し重かった'
    last = 'あなたは誘われた時は、あなたも少し怖くなかった'
    assert middle in follow and last in follow
    if change == 'missing':
        changed = follow.replace(middle + 'し、', '', 1)
    elif change == 'duplicate':
        changed = follow.replace(last, middle + 'し、' + last, 1)
    elif change == 'swap':
        changed = follow.replace(middle, '@middle@', 1).replace(last, middle, 1).replace('@middle@', last)
    else:
        old, new = {'degree': ('少し重かった', '重かった'), 'negative': ('怖くなかった', '怖かった'),
                    'particle': ('あなたも少し', 'あなたは少し'), 'actor': (middle, middle.replace('あなた', '相手', 1)),
                    'time': (middle, middle.replace('その時は', '回答した時点では', 1)), 'cause': ('し、', 'ので、')}[change]
        changed = follow.replace(old, new, 1)
    assert changed != follow and not read_body(context, body.replace(follow, changed, 1)).passed


def test_equal_visible_event_names_restore_each_original_event_byte_range(equal_visible_event_context):
    _, plan, _, resolver, selected = equal_visible_event_context
    raw = equal_visible_event_context[0].artifact.reception
    move, = plan.response_plan.human_reception_plan.moves
    proof = gate.read_received_discourse(raw, move, plan, resolver, selected)
    assert proof is not None
    events = [(a, b, value.decode()) for a, b, value in proof if value.decode() in ('私は誘われた', '自分は誘われた')]
    assert [value for _, _, value in events] == ['私は誘われた', '自分は誘われた']
    assert events[0][1] < events[1][0]
    assert all(raw.encode()[a:b].decode() == 'あなたは誘われた' for a, b, _ in events)


@pytest.mark.parametrize('owner', ['私', '自分'])
def test_perceived_answer_owner_is_recovered_from_its_complete_visible_clause(owner):
    memo = '褒められたのに、嬉しくなかった。私は誘われたのに、悲しかった。自分は誘われたのに、寂しかった。'
    req = advance(begin(memo), '「嬉しくなかった」ではなく「私は少し不安でした」です。')
    req = advance(req, f'その時は{owner}は頼まれたようで、重かった。')
    context = actual(request=advance(req, '「寂しかった」ではなく「私も少し怖くなかったです」です。'))
    body, follow = context[0].artifact.text, context[0].artifact.reception
    phrase = 'あなたは頼まれたようで、重かった'
    assert phrase in follow and owner + 'は頼まれたようで、重かった' in context[0].artifact.observation
    assert read_body(context, body).passed
    for changed in (phrase.replace('あなたは', owner + 'は', 1), phrase.replace('は頼まれた', 'も頼まれた', 1),
                    phrase.replace('ようで', 'ので', 1), phrase.replace('重かった', '軽かった', 1)):
        assert not read_body(context, body.replace(follow, follow.replace(phrase, changed, 1), 1)).passed


@pytest.mark.parametrize('answer_source', ['私は誘われたようで、重かった', '私が頼まれたようで、重かった', '私が頼まれたようで、少し重かった'])
def test_unresolved_perceived_owner_or_surplus_visible_anchor_keeps_nominal(answer_source):
    memo = '褒められたのに、嬉しくなかった。私は誘われたのに、悲しかった。自分は誘われたのに、寂しかった。'
    req = advance(begin(memo), '「嬉しくなかった」ではなく「私は少し不安でした」です。')
    req = advance(req, 'その時は' + answer_source + '。')
    context = actual(request=advance(req, '「寂しかった」ではなく「私も少し怖くなかったです」です。'))
    body, follow = context[0].artifact.text, context[0].artifact.reception
    # The complete contrast/time prefix separates a repeated answer event
    # from the live event boundaries. Keep both revisions and every source
    # duty; a surplus boundary must still fail the independent reader.
    if answer_source.startswith('私が'):
        assert answer_source.replace('私が', 'あなたが', 1) + 'し、' in follow
    else:
        clause = 'あなたは誘われたのに、悲しかったし、その時はあなたは誘われたようで、重かった'
        assert clause + 'し、' in follow
        for changed in (clause.replace('その時は', '', 1),
                        clause.replace('その時は', '回答した時点では', 1),
                        clause.replace('その時はあなたは', 'その時は相手は', 1),
                        clause.replace('ようで', 'ので', 1),
                        clause.replace('その時は', 'その時は、あなたは誘われた', 1)):
            assert changed != clause
            assert not read_body(context, body.replace(follow, follow.replace(clause, changed, 1), 1)).passed
    assert '私は少し不安でした' in context[0].artifact.observation
    assert answer_source in context[0].artifact.observation
    assert '私も少し怖くなかったです' in context[0].artifact.observation
    assert read_body(context, body).passed


@pytest.mark.parametrize('all_same', [False, True])
def test_equal_visible_event_names_saved_updates_keep_original_and_exact_reads(qcase, qdb, monkeypatch, all_same):
    user, parent, _ = qcase
    first_event = 'わたしは誘われた' if all_same else '褒められた'
    memo = first_event + 'のに、嬉しくなかった。私は誘われたのに、悲しかった。自分は誘われたのに、寂しかった。'
    assert 'code' not in qdb.query('update public.emotions set memo=$2 where id=$1', [parent, memo])
    service = active(monkeypatch)
    first = current = run(service.start(user, parent))
    for position, text in enumerate(('「嬉しくなかった」ではなく「私は少し不安でした」です。',
                                     'その時は少し重かった。',
                                     '「寂しかった」ではなく「私も少し怖くなかったです」です。')):
        if position:
            current = run(cont(service, user, current, f'visible-event-continue-{position}'))
        current = run(answer(service, user, current, text, f'visible-event-answer-{position}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        if position == 2:
            _, follow = current['current_observation']['text'].split('Emlisから：', 1)
            assert follow.count('あなたは誘われた時は') == (2 if all_same else 1)
            assert follow.count('あなたは誘われた') == (3 if all_same else 2)
            assert follow.count('あなたは誘われたのに、悲しかったし、その時は') == 1
            assert all(value in follow for value in ('あなたは少し不安だった', '悲しかったし、その時は少し重かった', 'あなたも少し怖くなかった'))
            assert '受け止めています' not in follow
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved visible event occurrences must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current
@pytest.mark.parametrize('owner', ['私', '自分', 'わたし'])
@pytest.mark.parametrize('particle', ['は', 'が'])
@pytest.mark.parametrize('when,source,visible', [
    ('今は', '私は少し嬉しいです', '回答した時点ではあなたは少し嬉しい'),
    ('その時は', '私も少し楽しかったです', 'その時はあなたも少し楽しかった'),
])
def test_positive_answer_keeps_event_owner_and_its_answer_time(owner, particle, when, source, visible):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    event = owner + particle + '誘われた'
    memo = f'褒められたのに、嬉しくなかった。{event}のに、悲しかった。頼まれたのに、寂しかった。'
    request = advance(advance(begin(memo), 'その時は少し重かった。'), when + source + '。')
    context = actual(request=request)
    body, follow = context[0].artifact.text, context[0].artifact.reception
    clause = 'あなた' + particle + '誘われたことについて、' + visible + 'のですね。'
    assert follow.endswith(clause) and '受け止めています' not in follow
    assert not re.search(r'(?:私|自分|わたし)(?:は|が|も)', follow)
    assert all(value in context[0].artifact.observation for value in (event, source, '嬉しくなかった', '悲しかった', '寂しかった'))
    assert MeaningExperienceEngine().generate(request).artifact.text == body
    assert read_body(context, body).passed
    for changed in (clause.replace('あなた' + particle, owner + particle, 1),
                    clause.replace('あなた' + particle, '相手' + particle, 1),
                    clause.replace('あなた' + particle, 'あなた' + ('が' if particle == 'は' else 'は'), 1),
                    clause.replace('少し', '', 1), clause.replace('その時は', '回答した時点では', 1)
                    if when == 'その時は' else clause.replace('回答した時点では', 'その時は', 1)):
        assert changed != clause
        assert not read_body(context, body.replace(follow, follow.replace(clause, changed, 1), 1)).passed


@pytest.fixture(scope='module', params=[
    ('私は褒められた', '自分が誘われた', 'わたしは頼まれた'),
    ('私は誘われた', '自分は誘われた', 'わたしは誘われた'),
    ('褒められた', '私は誘われた', '自分は誘われた'),
])
def positive_owned_event_group(request):
    events = request.param
    memo = ''.join(event + 'のに、' + feeling + '。' for event, feeling in zip(events, ('嬉しくなかった', '悲しかった', '寂しかった')))
    req = begin(memo)
    for reply in ('今は私も少し嬉しいです。', 'その時は私は楽しかったです。', 'その時は少し嬉しかった。'):
        req = advance(req, reply)
    return events, req, actual(request=req)


def test_positive_owned_event_group_restores_each_original_source_byte_range(positive_owned_event_group):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    events, request, context = positive_owned_event_group
    result, plan, _, resolver, selected = context
    body, follow = result.artifact.text, result.artifact.reception
    move, = (m for m in plan.response_plan.human_reception_plan.moves if m.reception_act == 'recognize_lived_change')
    group = follow[follow.index('。') + 1:]
    proof = gate._read_positive_answer_group_discourse(group, move, plan, resolver, selected)
    assert proof is not None
    event_proofs = [(a, b, value.decode()) for a, b, value in proof if value.decode() in events]
    assert [value for _, _, value in event_proofs] == list(events)
    assert all(group.encode()[a:b].decode() == re.sub(r'^(?:私|自分|わたし)(?=は|が)', 'あなた', value)
               for a, b, value in event_proofs)
    assert all(event_proofs[i][1] < event_proofs[i + 1][0] for i in range(2))
    assert all(event in result.artifact.observation for event in events)
    assert '受け止めています' not in follow and not re.search(r'(?:私|自分|わたし)(?:は|が|も)', follow)
    assert MeaningExperienceEngine().generate(request).artifact.text == body
    assert read_body(context, body).passed


@pytest.mark.parametrize('change', ['missing', 'duplicate', 'swap', 'degree', 'polarity', 'particle', 'actor', 'time', 'cause'])
def test_positive_owned_event_group_rejects_missing_extra_or_reassigned_answers(positive_owned_event_group, change):
    events, _, context = positive_owned_event_group
    body, follow = context[0].artifact.text, context[0].artifact.reception
    visible = [re.sub(r'^(?:私|自分|わたし)(?=は|が)', 'あなた', event) for event in events]
    middle = visible[1] + 'ことについて、その時はあなたは楽しかった'
    last = visible[2] + 'ことについて、その時は少し嬉しかった'
    assert middle in follow and last in follow
    if change == 'missing':
        changed = follow.replace(middle + 'し、', '', 1)
    elif change == 'duplicate':
        changed = follow.replace(last, middle + 'し、' + last, 1)
    elif change == 'swap':
        changed = follow.replace(middle, '@middle@', 1).replace(last, middle, 1).replace('@middle@', last)
    else:
        old, new = {'degree': ('少し嬉しかった', '嬉しかった'), 'polarity': ('少し嬉しかった', '少し嬉しくなかった'),
                    'particle': ('あなたは楽しかった', 'あなたも楽しかった'),
                    'actor': (middle, middle.replace('あなた', '相手', 1)),
                    'time': (middle, middle.replace('その時は', '回答した時点では', 1)), 'cause': ('し、', 'ので、')}[change]
        changed = follow.replace(old, new, 1)
    assert changed != follow and not read_body(context, body.replace(follow, changed, 1)).passed


@pytest.mark.parametrize('owner', ['私', '自分', 'わたし'])
@pytest.mark.parametrize('withdraw', [False, True])
def test_positive_owned_event_answer_correction_and_withdrawal_keep_separate_times(owner, withdraw):
    event = owner + 'は誘われた'
    request = advance(begin(event + 'のに、悲しかった。頼まれたのに、寂しかった。'), '今は私は少し嬉しいです。')
    reply = f'「{event}」は誤りです。' if withdraw else '「私は少し嬉しいです」ではなく「私も少し楽しいです」です。'
    context = actual(request=advance(request, reply))
    body, follow = context[0].artifact.text, context[0].artifact.reception
    assert '受け止めています' not in follow and read_body(context, body).passed
    assert '頼まれたのに、寂しさを感じた' in follow
    if withdraw:
        assert '誘われた' not in body
        assert 'その時は悲しかった' in follow and '回答した時点で、あなたは少し嬉しい' in follow
    else:
        assert '少し嬉しい' not in body and '悲しさを感じ' in follow
        assert '先の回答時点ではあなたも少し楽しい' in follow
        changed = follow.replace('先の回答時点では', '回答した時点では', 1)
        assert not read_body(context, body.replace(follow, changed, 1)).passed


@pytest.mark.parametrize('owner', ['僕', '私も', '私は私が'])
def test_positive_owned_event_does_not_broaden_unresolved_subjects(owner):
    event = owner + ('誘われた' if owner.endswith(('も', 'が')) else 'は誘われた')
    request = advance(begin(event + 'のに、悲しかった。頼まれたのに、寂しかった。'), '今は私は少し嬉しいです。')
    context = actual(request=advance(request, '「私は少し嬉しいです」ではなく「私も少し楽しいです」です。'))
    assert event in context[0].artifact.reception and '受け止めています' in context[0].artifact.reception
    assert read_body(context, context[0].artifact.text).passed


@pytest.mark.parametrize('withdraw', [False, True])
def test_positive_owned_event_saved_correction_and_withdrawal_keep_exact_reads(qcase, qdb, monkeypatch, withdraw):
    user, parent, _ = qcase
    memo = '私は誘われたのに、悲しかった。頼まれたのに、寂しかった。'
    assert 'code' not in qdb.query('update public.emotions set memo=$2 where id=$1', [parent, memo])
    service = active(monkeypatch)
    first = current = run(service.start(user, parent))
    replies = ('今は私は少し嬉しいです。', '「私は誘われた」は誤りです。' if withdraw
               else '「私は少し嬉しいです」ではなく「私も少し楽しいです」です。')
    for position, text in enumerate(replies):
        if position:
            current = run(cont(service, user, current, f'positive-owner-continue-{position}'))
        current = run(answer(service, user, current, text, f'positive-owner-answer-{position}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        body = current['current_observation']['text']
        _, follow = body.split('Emlisから：', 1)
        assert '受け止めています' not in follow
        if position and withdraw:
            assert '誘われた' not in body and '回答した時点で、あなたは少し嬉しい' in follow
        elif position:
            assert '少し嬉しい' not in body and '先の回答時点ではあなたも少し楽しい' in follow
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved positive owner replies must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current


@pytest.mark.parametrize('all_same', [False, True])
def test_positive_owned_event_group_saved_updates_preserve_each_occurrence(qcase, qdb, monkeypatch, all_same):
    user, parent, _ = qcase
    events = ('わたしは誘われた' if all_same else '褒められた', '私は誘われた', '自分は誘われた')
    memo = ''.join(event + 'のに、' + feeling + '。' for event, feeling in zip(events, ('嬉しくなかった', '悲しかった', '寂しかった')))
    assert 'code' not in qdb.query('update public.emotions set memo=$2 where id=$1', [parent, memo])
    service = active(monkeypatch)
    first = current = run(service.start(user, parent))
    for position, text in enumerate(('今は私も少し嬉しいです。', 'その時は私は楽しかったです。', 'その時は少し嬉しかった。')):
        if position:
            current = run(cont(service, user, current, f'positive-group-continue-{position}'))
        current = run(answer(service, user, current, text, f'positive-group-answer-{position}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        if position == 2:
            observation, follow = current['current_observation']['text'].split('Emlisから：', 1)
            assert all(event in observation for event in events)
            assert follow.count('あなたは誘われたことについて、') == (3 if all_same else 2)
            assert all(value in follow for value in ('回答した時点ではあなたも少し嬉しい', 'その時はあなたは楽しかった', 'その時は少し嬉しかった'))
            assert '受け止めています' not in follow
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved positive group occurrences must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current


@pytest.mark.parametrize('position', [0, 1, 2])
@pytest.mark.parametrize('source', ['次も説明を求められるようで、苦しかった', '断れないようで、重かった',
                                     '私は頼まれたようで、重かった', '自分は頼まれたようで,重かった',
                                     '私も頼まれたようで、重かった'])
def test_perceived_answer_retains_each_source_and_existing_middle_fallback(position, source):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    events = ('褒められた', '私は誘われた', '自分は誘われた')
    memo = ''.join(event + 'のに、' + feeling + '。' for event, feeling in zip(events, ('嬉しくなかった', '悲しかった', '寂しかった')))
    req = begin(memo)
    for _ in range(position):
        req = advance(req, 'その時は少し重かった。')
    req = advance(req, 'その時は' + source + '。')
    context = actual(request=req)
    body, follow = context[0].artifact.text, context[0].artifact.reception
    visible = re.sub(r'^(?:私|自分)(?=は|も)', 'あなた', source)
    event = re.sub(r'^(?:私|自分)(?=は|が)', 'あなた', events[position])
    reaction = ('嬉しくなかった', '悲しかった', '寂しかった')[position]
    clause = event + 'のに、' + reaction + 'し、その時は' + visible
    # The middle significance Move now uses the same finite source grammar
    # only when all three ordered event/reaction/answer scopes are proved.
    assert clause in follow or clause[:-3] + 'く' in follow
    assert source in context[0].artifact.observation and 'として届' not in follow
    assert MeaningExperienceEngine().generate(req).artifact.text == body
    assert read_body(context, body).passed


@pytest.fixture(scope='module')
def perceived_finite_group_context():
    memo = '褒められたのに、嬉しくなかった。私は誘われたのに、悲しかった。自分は誘われたのに、寂しかった。'
    req = advance(begin(memo), '「嬉しくなかった」ではなく「私は少し不安でした」です。')
    req = advance(req, 'その時は私も頼まれたようで、重かった。')
    return actual(request=advance(req, '「寂しかった」ではなく「私も少し怖くなかったです」です。'))


@pytest.mark.parametrize('old,new', [
    ('あなたも', 'あなたは'), ('頼まれたようで', '頼まれたので'), ('頼まれたようで', '頼まれなかったようで'),
    ('頼まれたようで、重かった', '重かった'), ('頼まれたようで、重かった', '頼まれたようだった'),
    ('重かった', '軽かった'), ('重かった', '重くなかった'), ('重かった', '重い'),
    ('悲しく、', ''), ('悲しく、', '悲しくなく、'),
    ('あなたは誘われた時は', '相手は誘われた時は'), ('あなたは誘われた時は', 'あなたが誘われた時は'),
    ('時は', '今は'),
])
def test_perceived_finite_group_rejects_changed_subject_scope_or_predicate(perceived_finite_group_context, old, new):
    context = perceived_finite_group_context
    body, follow = context[0].artifact.text, context[0].artifact.reception
    clause = 'あなたは誘われたのに、悲しかったし、その時はあなたも頼まれたようで、重かった'
    assert clause in follow and read_body(context, body).passed
    # Keep the original parameter IDs and mutation purposes while targeting
    # the explicit contrast / complete reaction in the current wording.
    replacements = {'悲しく、': '悲しかったし、', '悲しくなく、': '悲しくなかったし、',
                    'あなたは誘われた時は': 'あなたは誘われたのに',
                    '相手は誘われた時は': '相手は誘われたのに',
                    'あなたが誘われた時は': 'あなたが誘われたのに',
                    'あなたは褒められた時は': 'あなたは褒められたのに',
                    '誘われた時は': 'その時は', '誘われた今は': '回答した時点では',
                    '時は': 'その時は', '今は': '回答した時点では'}
    old, new = replacements.get(old, old), replacements.get(new, new)
    changed = clause.replace(old, new, 1)
    assert changed != clause
    assert not read_body(context, body.replace(follow, follow.replace(clause, changed, 1), 1)).passed


@pytest.mark.parametrize('operation', ['answer_correction', 'original_correction', 'withdraw'])
def test_perceived_finite_saved_updates_keep_sources_and_exact_reads(qcase, qdb, monkeypatch, operation):
    user, parent, _ = qcase
    memo = '誘われたのに、悲しかった。頼まれたのに、寂しかった。'
    assert 'code' not in qdb.query('update public.emotions set memo=$2 where id=$1', [parent, memo])
    service = active(monkeypatch)
    first = current = run(service.start(user, parent))
    reply = {'answer_correction': '「私は頼まれたようで、重かった」ではなく「自分は頼まれたようで、苦しかった」です。',
             'original_correction': '「悲しかった」ではなく「怖かった」です。',
             'withdraw': '「誘われた」は誤りです。'}[operation]
    for position, text in enumerate(('その時は私は頼まれたようで、重かった。', reply)):
        if position:
            current = run(cont(service, user, current, f'perceived-finite-continue-{position}'))
        current = run(answer(service, user, current, text, f'perceived-finite-answer-{position}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        body = current['current_observation']['text']
        _, follow = body.split('Emlisから：', 1)
        assert 'として届' not in follow
        if not position:
            assert '誘われたのに、悲しかったし、その時はあなたは頼まれたようで、重かった' in follow
        elif operation == 'answer_correction':
            assert '重かった' not in body and 'あなたは頼まれたようで、苦しかった' in follow
        elif operation == 'original_correction':
            assert '悲しかった' not in body and '怖かった' in body
        else:
            assert '誘われた' not in body and 'その時は悲しかった' in follow
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved perceived replies must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current


def test_perceived_finite_group_saved_updates_keep_all_occurrences(qcase, qdb, monkeypatch):
    user, parent, _ = qcase
    memo = '褒められたのに、嬉しくなかった。私は誘われたのに、悲しかった。自分は誘われたのに、寂しかった。'
    assert 'code' not in qdb.query('update public.emotions set memo=$2 where id=$1', [parent, memo])
    service = active(monkeypatch)
    first = current = run(service.start(user, parent))
    replies = ('「嬉しくなかった」ではなく「私は少し不安でした」です。', 'その時は私も頼まれたようで、重かった。',
               '「寂しかった」ではなく「私も少し怖くなかったです」です。')
    for position, text in enumerate(replies):
        if position:
            current = run(cont(service, user, current, f'perceived-group-continue-{position}'))
        current = run(answer(service, user, current, text, f'perceived-group-answer-{position}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        if position == 2:
            observation, follow = current['current_observation']['text'].split('Emlisから：', 1)
            assert '嬉しくなかった' not in observation and '寂しかった' not in observation
            assert 'あなたは誘われたのに、悲しかったし、その時はあなたも頼まれたようで、重かった' in follow
            assert 'あなたは誘われた時は、あなたも少し怖くなかった' in follow
            assert 'として届' not in follow
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved perceived group must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current


def test_perceived_finite_reader_still_restores_the_prior_saved_wording(perceived_finite_group_context):
    context = perceived_finite_group_context
    body, follow = context[0].artifact.text, context[0].artifact.reception
    current = 'あなたは誘われたのに、悲しかったし、その時はあなたも頼まれたようで、重かった'
    prior = 'あなたは誘われたことは、悲しさを伴い、あなたも頼まれたような重さとして届いた'
    assert current in follow
    assert read_body(context, body.replace(follow, follow.replace(current, prior, 1), 1)).passed


@pytest.fixture(scope='module')
def middle_received_scope_context():
    memo = '褒められたのに、嬉しくなかった。私は誘われたのに、悲しかった。自分は誘われたのに、寂しかった。'
    req = advance(begin(memo), 'その時は少し重かった。')
    return actual(request=advance(req, 'その時は私も頼まれたようで、重かった。'))


@pytest.mark.parametrize('old,new', [
    ('あなたも', 'あなたは'), ('頼まれたようで', '頼まれたので'),
    ('頼まれたようで', '頼まれなかったようで'),
    ('あなたも頼まれたようで、', ''), ('、重かった', ''),
    ('重かった', '軽かった'), ('重かった', '重くなかった'), ('重かった', '重い'),
    ('悲しく、', ''), ('悲しく、', '悲しくなく、'),
    ('あなたは誘われた時は', '相手は誘われた時は'),
    ('あなたは誘われた時は', 'あなたが誘われた時は'), ('時は', '今は'),
])
def test_middle_received_scope_rejects_changed_meaning(middle_received_scope_context, old, new):
    context = middle_received_scope_context
    body, follow = context[0].artifact.text, context[0].artifact.reception
    middle = 'あなたは誘われたのに、悲しかったし、その時はあなたも頼まれたようで、重かったのですね。'
    assert middle in follow and read_body(context, body).passed
    # Keep the original parameter IDs and mutation purposes while targeting
    # the explicit contrast / complete reaction in the current wording.
    replacements = {'悲しく、': '悲しかったし、', '悲しくなく、': '悲しくなかったし、',
                    'あなたは誘われた時は': 'あなたは誘われたのに',
                    '相手は誘われた時は': '相手は誘われたのに',
                    'あなたが誘われた時は': 'あなたが誘われたのに',
                    'あなたは褒められた時は': 'あなたは褒められたのに',
                    '誘われた時は': 'その時は', '誘われた今は': '回答した時点では',
                    '時は': 'その時は', '今は': '回答した時点では'}
    old, new = replacements.get(old, old), replacements.get(new, new)
    changed = middle.replace(old, new, 1)
    assert changed != middle
    assert not read_body(context, body.replace(follow, follow.replace(middle, changed, 1), 1)).passed


@pytest.mark.parametrize('change', ['optional', 'act', 'role', 'missing', 'reverse',
                                     'reaction', 'answer', 'target', 'foreign_move'])
def test_middle_received_scope_requires_complete_ordered_plan(middle_received_scope_context, change):
    _, plan, _, resolver, selected = middle_received_scope_context
    reception_plan = plan.response_plan.human_reception_plan
    moves = reception_plan.moves
    middle = moves[1]
    raw = 'あなたは誘われた時は悲しく、あなたも頼まれたようで、重かったのですね。'
    assert gate.read_received_discourse(raw, middle, plan, resolver, selected) is not None
    if change == 'optional':
        changed = replace(middle, required=False)
    elif change == 'act':
        changed = replace(middle, reception_act=moves[0].reception_act + '_changed')
    elif change == 'role':
        changed = replace(middle, move_role='attention')
    elif change in {'reaction', 'answer'}:
        field = 'memo' if change == 'reaction' else 'answer_text_private'
        source_ids = {n.nucleus_id for n in plan.nuclei if field in n.source_fields}
        supports = tuple(value for value in middle.support_nucleus_ids if value not in source_ids)
        assert supports != middle.support_nucleus_ids
        changed = replace(middle, support_nucleus_ids=supports)
    elif change == 'target':
        changed = replace(middle, target_nucleus_ids=moves[0].target_nucleus_ids)
    else:
        changed = middle
    altered_moves = (moves[0], changed, moves[2])
    if change == 'missing':
        altered_moves = moves[1:]
    elif change == 'reverse':
        altered_moves = tuple(reversed(moves))
    elif change == 'foreign_move':
        changed = replace(middle, move_id=middle.move_id + '_foreign')
        altered_moves = moves
    altered = replace(plan, response_plan=replace(plan.response_plan,
        human_reception_plan=replace(reception_plan, moves=altered_moves)))
    assert gate.read_received_discourse(raw, changed, altered, resolver, selected) is None


def test_middle_received_scope_still_reads_prior_saved_nominal_wording(qcase, qdb, monkeypatch):
    user, parent, _ = qcase
    memo = '褒められたのに、嬉しくなかった。私は誘われたのに、悲しかった。自分は誘われたのに、寂しかった。'
    assert 'code' not in qdb.query('update public.emotions set memo=$2 where id=$1', [parent, memo])
    service = active(monkeypatch)
    current = run(service.start(user, parent))
    author = reception._source_grounded_reception_fragment

    def prior_author(*args, **kwargs):
        # Materialize the pre-u35 saved grammar through the existing fallback.
        kwargs['middle_received_scope'] = False
        return author(*args, **kwargs)

    with monkeypatch.context() as prior:
        prior.setattr(reception, '_source_grounded_reception_fragment', prior_author)
        for position, text in enumerate(('その時は少し重かった。', 'その時は私も頼まれたようで、重かった。')):
            if position:
                current = run(cont(service, user, current, f'prior-middle-continue-{position}'))
            current = run(answer(service, user, current, text, f'prior-middle-answer-{position}'))
    assert current['body_state'] == 'REFINED'
    assert '私も頼まれたようだという、その時の重さを見失わず、小さくせずに受け止めています。' in current['current_observation']['text']
    with monkeypatch.context() as saved:
        saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('prior saved wording must not regenerate'))
        assert run(service.get(user, parent)) == run(service.start(user, parent)) == current


def test_middle_received_scope_does_not_admit_standalone_feeling_after_withdrawal():
    memo = '褒められたのに、嬉しくなかった。私は誘われたのに、悲しかった。自分は誘われたのに、寂しかった。'
    req = advance(advance(begin(memo), 'その時は少し重かった。'), 'その時は私も頼まれたようで、重かった。')
    req = advance(req, '「私は誘われた」は誤りです。')
    context = actual(request=req)
    assert context[0].artifact.reception == ('その時は悲しかったし、その時、あなたも頼まれたようで、重かったのですね。'
        '褒められたのに嬉しくなかったことと、その時に少し重かったことを見失わず、小さくせずに受け止めています。'
        'あなたは誘われたのに、寂しさを感じたのですね。')
    assert read_body(context, context[0].artifact.text).passed


@pytest.mark.parametrize('operation', ['answer_correction', 'original_correction', 'withdraw'])
def test_middle_received_scope_saved_updates_keep_exact_reads(qcase, qdb, monkeypatch, operation):
    user, parent, _ = qcase
    memo = '褒められたのに、嬉しくなかった。私は誘われたのに、悲しかった。自分は誘われたのに、寂しかった。'
    assert 'code' not in qdb.query('update public.emotions set memo=$2 where id=$1', [parent, memo])
    service = active(monkeypatch)
    first = current = run(service.start(user, parent))
    reply = {'answer_correction': '「私も頼まれたようで、重かった」ではなく「私は頼まれたようで、苦しかった」です。',
             'original_correction': '「悲しかった」ではなく「怖かった」です。',
             'withdraw': '「私は誘われた」は誤りです。'}[operation]
    for position, text in enumerate(('その時は少し重かった。', 'その時は私も頼まれたようで、重かった。', reply)):
        if position:
            current = run(cont(service, user, current, f'middle-scope-continue-{position}'))
        current = run(answer(service, user, current, text, f'middle-scope-answer-{position}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        body = current['current_observation']['text']
        observation, follow = body.split('Emlisから：', 1)
        if position == 1:
            assert 'あなたは誘われたのに、悲しかったし、その時はあなたも頼まれたようで、重かった' in follow
        elif position == 2 and operation == 'answer_correction':
            assert 'あなたは誘われたのに、悲しかったし、その時はあなたは頼まれたようで、苦しかった' in follow
            assert '私も頼まれたようで、重かった' not in observation
        elif position == 2 and operation == 'original_correction':
            assert '悲しかった' not in body and '怖かった' in observation
        elif position == 2:
            assert '私は誘われた' not in body and 'その時は悲しかった' in follow
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved middle scope must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current


GA_OWNER_MEMO = ('褒められたのに、嬉しくなかった。私は誘われたのに、悲しかった。'
                 '自分は誘われたのに、寂しかった。')


@pytest.mark.parametrize('owner', ['私', '自分'])
@pytest.mark.parametrize('position', [0, 1, 2])
def test_single_ga_answer_keeps_particle_and_own_occasion(owner, position):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    source = owner + 'が頼まれたようで、重かった'
    request = begin(GA_OWNER_MEMO)
    for reply in ['その時は少し重かった。'] * position + ['その時は' + source + '。']:
        request = advance(request, reply)
    context = actual(request=request)
    body, follow = context[0].artifact.text, context[0].artifact.reception
    assert source in context[0].artifact.observation
    assert 'あなたが頼まれたようで、重かったのですね' in follow
    assert follow.count('あなたが頼まれた') == 1
    assert MeaningExperienceEngine().generate(request).artifact.text == body
    assert read_body(context, body).passed


@pytest.fixture(scope='module')
def single_ga_context():
    request = advance(begin(GA_OWNER_MEMO), 'その時は少し重かった。')
    return actual(request=advance(request, 'その時は私が頼まれたようで、少し重かった。'))


@pytest.mark.parametrize('old,new', [
    ('あなたが頼まれた', 'あなたは頼まれた'), ('あなたが頼まれた', 'あなたも頼まれた'),
    ('あなたが頼まれた', 'あなたには頼まれた'), ('あなたが頼まれた', '友人が頼まれた'),
    ('頼まれたようで', '頼まれたので'), ('頼まれたようで', '頼まれなかったようで'),
    ('少し重かった', '重かった'), ('少し重かった', '少し重くなかった'),
    ('少し重かった', '少し軽かった'), ('少し重かった', '少し重い'),
    ('悲しく、', ''), ('あなたは誘われた時は', 'あなたは褒められた時は'),
    ('誘われた時は', '誘われた今は'),
])
def test_single_ga_inverse_rejects_changed_case_meaning_or_scope(single_ga_context, old, new):
    context = single_ga_context
    body, follow = context[0].artifact.text, context[0].artifact.reception
    middle = 'あなたは誘われたのに、悲しかったし、その時はあなたが頼まれたようで、少し重かったのですね。'
    assert middle in follow and read_body(context, body).passed
    # Keep baseline parameter IDs and the same semantic mutation duties.
    replacements = {'悲しく、': '悲しかったし、',
                    'あなたは誘われた時は': 'あなたは誘われたのに',
                    'あなたは褒められた時は': 'あなたは褒められたのに',
                    '誘われた時は': 'その時は', '誘われた今は': '回答した時点では',
                    '時は': 'その時は', '今は': '回答した時点では'}
    old, new = replacements.get(old, old), replacements.get(new, new)
    changed = middle.replace(old, new, 1)
    assert changed != middle
    assert not read_body(context, body.replace(follow, follow.replace(middle, changed, 1), 1)).passed


@pytest.mark.parametrize('source,nominal', [
    ('私が少し怖かったです', '私が少し怖かったこと'),
    ('少し自分が不安だったのです', '少し自分が不安だったのだということ'),
    ('私が少し不安でした', '私が少し不安だったこと'),
    ('少し私が不安なのだった', '少し私が不安なのだったということ'),
    ('私が怖かったようで、重かった', '私が怖かったようだという、その時の重さ'),
    ('私が不安だったようで、重かった', '私が不安だったようだという、その時の重さ'),
])
def test_ga_feeling_target_is_not_reinterpreted_as_experiencer(source, nominal):
    request = advance(begin(GA_OWNER_MEMO), 'その時は少し重かった。')
    context = actual(request=advance(request, 'その時は' + source + '。'))
    body, follow = context[0].artifact.text, context[0].artifact.reception
    assert source in context[0].artifact.observation and nominal in follow
    assert 'あなたが' not in follow and read_body(context, body).passed
    changed = follow.replace(nominal, nominal.replace('自分が', 'あなたが').replace('私が', 'あなたが'), 1)
    assert changed != follow and not read_body(context, body.replace(follow, changed, 1)).passed


def test_ga_feeling_target_correction_keeps_whole_prior_answer_perspective():
    request = begin(GA_OWNER_MEMO)
    for reply in ('その時は少し重かった。', '今は私が少し苦しい。',
                  '「私が少し苦しい」ではなく「自分が少し怖い」です。'):
        request = advance(request, reply)
    context = actual(request=request)
    body, follow = context[0].artifact.text, context[0].artifact.reception
    assert '先の回答時点では「自分が少し怖い」' in context[0].artifact.observation
    assert '先の回答時点で自分が少し怖いこと' in follow
    assert 'あなたが少し怖い' not in body and '私が少し苦しい' not in body
    assert read_body(context, body).passed


def test_ga_positive_feeling_keeps_existing_unavailable_boundary():
    request = advance(begin(GA_OWNER_MEMO), 'その時は少し重かった。')
    request = advance(request, 'その時は私が少し嬉しいです。')
    with pytest.raises(ValueError, match='emlis_thread_body_independent_validation_failed'):
        actual(request=request)


@pytest.mark.parametrize('source,nominal', [
    ('私が私には不安だったのです', '私が私には不安だったのだということ'),
    ('私が私を責めたようで、重かった', '私が私を責めたようだという、その時の重さ'),
    ('私が私に頼まれたようで、重かった', '私が私に頼まれたようだという、その時の重さ'),
    ('私が私も頼まれたようで、重かった', '私が私も頼まれたようだという、その時の重さ'),
    ('私が私が頼まれたようで、重かった', '私が私が頼まれたようだという、その時の重さ'),
    ('私があなたに頼まれたようで、重かった', '私があなたに頼まれたようだという、その時の重さ'),
])
def test_ga_with_later_person_keeps_whole_source_perspective(source, nominal):
    request = advance(begin(GA_OWNER_MEMO), 'その時は少し重かった。')
    context = actual(request=advance(request, 'その時は' + source + '。'))
    body, follow = context[0].artifact.text, context[0].artifact.reception
    assert source in context[0].artifact.observation and nominal in follow
    assert 'あなたが' not in follow and read_body(context, body).passed
    changed = follow.replace(nominal, nominal.replace('私が', 'あなたが', 1), 1)
    assert changed != follow and not read_body(context, body.replace(follow, changed, 1)).passed


@pytest.mark.parametrize('operation', ['answer_correction', 'original_correction', 'withdraw'])
def test_single_ga_saved_updates_keep_original_and_exact_reads(qcase, qdb, monkeypatch, operation):
    user, parent, _ = qcase
    assert 'code' not in qdb.query('update public.emotions set memo=$2 where id=$1', [parent, GA_OWNER_MEMO])
    service = active(monkeypatch)
    first = current = run(service.start(user, parent))
    source = '私が頼まれたようで、重かった'
    reply = {'answer_correction': '「' + source + '」ではなく「自分が頼まれたようで、苦しかった」です。',
             'original_correction': '「悲しかった」ではなく「怖かった」です。',
             'withdraw': '「私は誘われた」は誤りです。'}[operation]
    for position, text in enumerate(('その時は少し重かった。', 'その時は' + source + '。', reply)):
        if position:
            current = run(cont(service, user, current, f'ga-continue-{position}'))
        current = run(answer(service, user, current, text, f'ga-answer-{position}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        body = current['current_observation']['text']
        observation, follow = body.split('Emlisから：', 1)
        assert '今回の観測に反映できていない' not in body
        if position == 1:
            assert 'あなたは誘われたのに、悲しかったし、その時はあなたが頼まれたようで、重かった' in follow
        elif position == 2 and operation == 'answer_correction':
            assert source not in observation and '自分が頼まれたようで、苦しかった' in observation
            assert 'あなたが頼まれたようで、苦しかった' in follow
        elif position == 2 and operation == 'original_correction':
            assert '悲しかった' not in body and '怖かった' in observation
        elif position == 2:
            assert '私は誘われた' not in body and 'その時は悲しかった' in follow
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved ga body must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current


def test_single_ga_still_reads_prior_saved_nominal_wording(qcase, qdb, monkeypatch):
    user, parent, _ = qcase
    memo = '褒められたのに、嬉しくなかった。私は誘われたのに、悲しかった。自分は誘われたのに、寂しかった。'
    assert 'code' not in qdb.query('update public.emotions set memo=$2 where id=$1', [parent, memo])
    service = active(monkeypatch)
    current = run(service.start(user, parent))
    author = reception._source_grounded_reception_fragment

    def prior_author(*args, **kwargs):
        # Materialize the pre-u36 saved grammar through the existing fallback.
        kwargs['middle_received_scope'] = False
        return author(*args, **kwargs)

    with monkeypatch.context() as prior:
        prior.setattr(reception, '_source_grounded_reception_fragment', prior_author)
        for position, text in enumerate(('その時は少し重かった。', 'その時は私が頼まれたようで、重かった。')):
            if position:
                current = run(cont(service, user, current, f'prior-ga-continue-{position}'))
            current = run(answer(service, user, current, text, f'prior-ga-answer-{position}'))
    assert current['body_state'] == 'REFINED'
    assert '私が頼まれたようだという、その時の重さを見失わず、小さくせずに受け止めています。' in current['current_observation']['text']
    with monkeypatch.context() as saved:
        saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('prior saved wording must not regenerate'))
        assert run(service.get(user, parent)) == run(service.start(user, parent)) == current


@pytest.mark.parametrize('comma', ['、', ','])
def test_single_ga_negative_perception_preserves_source_negation(comma):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    source = '私が頼まれなかったようで' + comma + '重かった'
    request = advance(begin(GA_OWNER_MEMO), 'その時は少し重かった。')
    request = advance(request, 'その時は' + source + '。')
    context = actual(request=request)
    body, follow = context[0].artifact.text, context[0].artifact.reception
    assert source in context[0].artifact.observation
    assert source.replace('私が', 'あなたが', 1) + 'のですね' in follow
    assert MeaningExperienceEngine().generate(request).artifact.text == body
    assert read_body(context, body).passed
    changed = follow.replace('頼まれなかったようで', '頼まれたようで', 1)
    assert changed != follow and not read_body(context, body.replace(follow, changed, 1)).passed


@pytest.mark.parametrize('connector', ['のに', 'けど', 'けれど', 'けれども'])
@pytest.mark.parametrize('position', [0, 1, 2])
def test_perceived_original_answer_preserves_explicit_contrast(connector, position):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    events = ('褒められた', '私は誘われた', '自分は誘われた')
    reactions = ('嬉しくなかった', '悲しかった', '寂しかった')
    memo = ''.join(event + connector + '、' + feeling + '。'
                   for event, feeling in zip(events, reactions))
    request = begin(memo)
    for reply in ['その時は少し重かった。'] * position + ['その時は私が頼まれたようで、重かった。']:
        request = advance(request, reply)
    context = actual(request=request)
    body, follow = context[0].artifact.text, context[0].artifact.reception
    event = re.sub(r'^(?:私|自分)(?=は|が)', 'あなた', events[position])
    clause = event + connector + '、' + reactions[position] + 'し、その時はあなたが頼まれたようで、重かった'
    assert clause in follow
    assert MeaningExperienceEngine().generate(request).artifact.text == body
    assert read_body(context, body).passed
    # The reader must not take the original connective from Observation.
    changed = follow.replace(clause, clause.replace(connector + '、', 'ので、', 1), 1)
    assert changed != follow
    assert not read_body(context, body.replace(follow, changed, 1)).passed


@pytest.fixture(scope='module')
def perceived_original_contrast_context():
    request = advance(begin(GA_OWNER_MEMO), 'その時は私が頼まれなかったようで、重かった。')
    return actual(request=request)


@pytest.mark.parametrize('old,new', [
    ('褒められたのに、', '褒められたので、'),
    ('褒められたのに、', '褒められた、'),
    ('褒められたのに、', '褒められたけど、'),
    ('嬉しくなかったし、', ''),
    ('嬉しくなかったし、', '嬉しかったし、'),
    ('嬉しくなかったし、', '嬉しくないし、'),
    ('その時は', ''), ('その時は', '回答した時点では'),
    ('頼まれなかったようで、', '頼まれたようで、'),
    ('頼まれなかったようで、', '頼まれなかったので、'),
    ('重かった', '少し重かった'), ('あなたが', 'あなたは'),
])
def test_perceived_original_contrast_rejects_relation_time_and_meaning_changes(perceived_original_contrast_context, old, new):
    context = perceived_original_contrast_context
    body, follow = context[0].artifact.text, context[0].artifact.reception
    assert read_body(context, body).passed
    changed = follow.replace(old, new, 1)
    assert changed != follow
    assert not read_body(context, body.replace(follow, changed, 1)).passed


def test_perceived_original_contrast_keeps_prior_finite_reader(perceived_original_contrast_context):
    context = perceived_original_contrast_context
    body, follow = context[0].artifact.text, context[0].artifact.reception
    current = '褒められたのに、嬉しくなかったし、その時は'
    assert current in follow
    legacy = follow.replace(current, '褒められた時は嬉しくなく、', 1)
    assert read_body(context, body.replace(follow, legacy, 1)).passed


@pytest.mark.parametrize('source,visible', [
    ('私が頼まれたようで、少し重かった', 'あなたが頼まれたようで、少し重かった'),
    ('重かったと思った', '重かったと思った'),
    ('少し重かった', '少し重かった'),
    ('私は少し不安でした', 'あなたは少し不安だった'),
    ('不安でした', '不安だった'), ('不安です', '不安な'),
    ('不安だったのです', '不安だった'),
    ('少し怖くなかった', '少し怖くなかった'), ('苦しいです', '苦しい'),
])
@pytest.mark.parametrize('position', [0, 1, 2])
def test_original_contrast_is_independent_of_admitted_answer_grammar(source, visible, position):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    request = begin(GA_OWNER_MEMO)
    for reply in ['その時は断れないようで、重かった。'] * position + ['その時は' + source + '。']:
        request = advance(request, reply)
    context = actual(request=request)
    body, follow = context[0].artifact.text, context[0].artifact.reception
    event = ('褒められた', 'あなたは誘われた', 'あなたは誘われた')[position]
    reaction = ('嬉しくなかった', '悲しかった', '寂しかった')[position]
    prefix = event + 'のに、' + reaction + 'し、その時は'
    clause = prefix + visible + 'のですね'
    assert clause in follow
    assert MeaningExperienceEngine().generate(request).artifact.text == body
    assert read_body(context, body).passed
    # Source type cannot donate the original relation or answer time.
    for changed in (clause.replace('のに、', 'ので、', 1),
                    clause.replace(reaction + 'し、', '', 1),
                    clause.replace('その時は', '回答した時点では', 1)):
        assert changed != clause
        assert not read_body(context, body.replace(follow, follow.replace(clause, changed, 1), 1)).passed


@pytest.mark.parametrize('connector', ['けど', 'けれど', 'けれども'])
def test_multiple_answer_grammars_keep_each_original_connector(connector):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    request = begin(GA_OWNER_MEMO.replace('のに', connector))
    for source in ('少し怖くなかった', '不安でした', '重かったと思った'):
        request = advance(request, 'その時は' + source + '。')
    context = actual(request=request)
    body, follow = context[0].artifact.text, context[0].artifact.reception
    assert MeaningExperienceEngine().generate(request).artifact.text == body
    assert read_body(context, body).passed
    for event, reaction in zip(('褒められた', 'あなたは誘われた', 'あなたは誘われた'),
                               ('嬉しくなかった', '悲しかった', '寂しかった')):
        prefix = event + connector + '、' + reaction + 'し、その時は'
        assert prefix in follow
        changed = follow.replace(prefix, prefix.replace(connector + '、', 'のに、', 1), 1)
        assert changed != follow
        assert not read_body(context, body.replace(follow, changed, 1)).passed


@pytest.mark.parametrize('source,visible', [
    ('少し苦しい', '少し苦しい'),
    ('少し不安です', '少し不安な'),
    ('少し不安でした', '少し不安だった'),
    ('私は少し不安です', 'あなたは少し不安な'),
    ('断れないようで、重かった', '断れないようで、重かった'),
    ('結果だけで、そこまでの苦労は見てもらえていないと思った',
     '結果だけで、そこまでの苦労は見てもらえていないと思った'),
])
@pytest.mark.parametrize('position,correct', [(0, False), (1, False), (2, False), (0, True), (1, True)])
def test_answer_time_original_relation_keeps_each_source_and_scope(source, visible, position, correct):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    request = begin(GA_OWNER_MEMO)
    replies = ['その時は少し怖かった。'] * position + ['今は' + source + '。']
    if correct:
        replies.append('「' + source + '」ではなく「とても苦しかった」です。')
        visible = 'とても苦しかった'
    for reply in replies:
        request = advance(request, reply)
    context = actual(request=request)
    body, follow = context[0].artifact.text, context[0].artifact.reception
    event = ('褒められた', 'あなたは誘われた', 'あなたは誘われた')[position]
    reaction = ('嬉しくなかった', '悲しかった', '寂しかった')[position]
    time = '先の回答時点では' if correct else '回答した時点では'
    clause = event + 'のに、' + reaction + 'し、' + time + visible + 'のですね'
    assert clause in follow and clause.count(time) == 1
    assert MeaningExperienceEngine().generate(request).artifact.text == body
    assert read_body(context, body).passed
    # Read Reception independently: Observation must not supply a lost relation,
    # original reaction, degree, or answer occasion.
    for changed in (clause.replace('のに、', 'ので、', 1),
                    clause.replace(reaction + 'し、', '', 1),
                    clause.replace(reaction + 'し、', reaction.replace('かった', 'ない') + 'し、', 1),
                    clause.replace(time, 'その時は', 1),
                    clause.replace(time, '', 1),
                    clause.replace(visible, visible.replace('少し', '').replace('とても', ''), 1)
                        if '少し' in visible or 'とても' in visible
                        else clause.replace(visible, '苦しかった', 1)):
        assert changed != clause
        assert not read_body(context, body.replace(follow, follow.replace(clause, changed, 1), 1)).passed


@pytest.mark.parametrize('connector', ['のに', 'けど', 'けれど', 'けれども'])
@pytest.mark.parametrize('correct', [False, True])
def test_answer_time_relation_does_not_invent_a_cause(connector, correct):
    request = advance(begin(GA_OWNER_MEMO.replace('のに', connector)), '今は少し苦しい。')
    if correct:
        request = advance(request, '「少し苦しい」ではなく「とても苦しい」です。')
    context = actual(request=request)
    body, follow = context[0].artifact.text, context[0].artifact.reception
    time = '先の回答時点では' if correct else '回答した時点では'
    prefix = '褒められた' + connector + '、嬉しくなかったし、' + time
    assert prefix in follow and read_body(context, body).passed
    for altered in (prefix.replace(connector + '、', 'ので、', 1),
                    prefix.replace(connector + '、', '、', 1),
                    prefix.replace('嬉しくなかった', '嬉しかった', 1)):
        assert altered != prefix
        assert not read_body(context, body.replace(prefix, altered, 1)).passed


@pytest.mark.parametrize('correct', [False, True])
def test_answer_time_relation_still_reads_prior_finite_wording(correct):
    request = advance(begin(GA_OWNER_MEMO), '今は少し苦しい。')
    if correct:
        request = advance(request, '「少し苦しい」ではなく「とても苦しい」です。')
    context = actual(request=request)
    body, follow = context[0].artifact.text, context[0].artifact.reception
    current = '褒められたのに、嬉しくなかったし、'
    assert current in follow
    legacy = body.replace(current, '褒められた時は嬉しくなく、', 1)
    assert legacy != body and read_body(context, legacy).passed


@pytest.mark.parametrize('last', ['「少し苦しい」ではなく「とても苦しい」です。', '「悲しかった」は誤りです。'])
def test_answer_time_relation_saved_updates_reuse_original_and_exact_body(qcase, qdb, monkeypatch, last):
    from test_emlis_q3_application import cont
    user, parent, service = qcase
    qdb.query('update public.emotions set memo=$1 where id=$2', [GA_OWNER_MEMO, parent])
    first = current = run(service.start(user, parent))
    for position, reply in enumerate(('その時は少し怖かった。', '今は少し苦しい。', last)):
        if position:
            current = run(cont(service, user, current, f'answer-time-relation-continue-{position}'))
        current = run(answer(service, user, current, reply, f'answer-time-relation-answer-{position}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        body = current['current_observation']['text']
        assert '今回の観測に反映できていない' not in body
        if position == 1:
            assert 'あなたは誘われたのに、悲しかったし、回答した時点では少し苦しいのですね' in body
        if position == 2 and 'ではなく' in last:
            assert 'あなたは誘われたのに、悲しかったし、先の回答時点ではとても苦しいのですね' in body
        if position == 2 and '誤り' in last:
            assert '悲しかった' not in body and '少し苦しい' in body and '寂し' in body
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved body must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current


RECORD_PAIR_MEMO = ('褒められたのに、嬉しくなかった。私は誘われたのに、悲しかった。'
                    '自分は誘われたのに、寂しかった。')
RECORD_TRIPLE_MEMO = ('私は誘われたのに、嬉しくなかった。自分は誘われたのに、悲しかった。'
                      'わたしは誘われたのに、寂しかった。')
RECORD_PREFIXES = ('先に書かれた方では、', '間に書かれた方では、', '後に書かれた方では、')


@pytest.mark.parametrize('memo,prefixes,event', [
    (RECORD_PAIR_MEMO, (RECORD_PREFIXES[0], RECORD_PREFIXES[2]), 'あなたは誘われた'),
    (RECORD_TRIPLE_MEMO, RECORD_PREFIXES, 'あなたは誘われた'),
    (RECORD_PAIR_MEMO.replace('私は', '私が').replace('自分は', '自分が'),
     (RECORD_PREFIXES[0], RECORD_PREFIXES[2]), 'あなたが誘われた'),
])
@pytest.mark.parametrize('stage', ['initial', 'then', 'now'])
def test_equal_event_records_are_visible_with_original_feelings_and_answers(memo, prefixes, event, stage):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning, build_updated_grounded_plan
    request = begin(memo)
    if stage != 'initial':
        for reply in ('「嬉しくなかった」ではなく「私は少し不安でした」です。',
                      '今は少し苦しい。' if stage == 'now' else 'その時は少し重かった。',
                      '「寂しかった」ではなく「私も少し怖くなかったです」です。'):
            request = advance(request, reply)
    meaning = prepare_emlis_meaning(request)
    preserved = build_updated_grounded_plan(meaning)
    context = actual(request=request)
    result, plan, _, resolver, selected = context
    follow = result.artifact.reception
    assert MeaningExperienceEngine().generate(request).artifact.text == result.artifact.text
    assert plan.nuclei == preserved.nuclei and plan.relations == preserved.relations
    assert meaning.thread.original.normalized_current_input['memo'] == memo
    positions = []
    for prefix in prefixes:
        assert follow.count(prefix) == 1 and prefix + event in follow
        positions.append(follow.index(prefix))
    assert positions == sorted(positions)
    assert '先に起きた' not in follow and '後に起きた' not in follow and '別の日' not in follow
    if stage == 'initial':
        assert '悲しさを感じ' in follow and '寂しさを感じた' in follow
    else:
        assert 'あなたは少し不安だった' in follow and 'あなたも少し怖くなかった' in follow
        assert ('回答した時点では少し苦しい' if stage == 'now' else 'その時は少し重かった') in follow
    assert read_body(context, result.artifact.text).passed
    # The independent reader restores only the actual event byte range;
    # the written-position qualifier is not part of the original event.
    restored = []
    for move in plan.response_plan.human_reception_plan.moves:
        proof = gate.read_received_discourse(follow, move, plan, resolver, selected)
        if proof is not None:
            restored += [(a, b, source) for a, b, source in proof
                         if source.decode() in ('私は誘われた', '自分は誘われた', 'わたしは誘われた',
                                                '私が誘われた', '自分が誘われた')]
    assert len(restored) == len(prefixes)
    assert all(follow.encode()[a:b].decode() == event for a, b, _ in restored)


@pytest.fixture(scope='module')
def equal_event_record_context():
    request = advance(begin(RECORD_PAIR_MEMO), '「嬉しくなかった」ではなく「私は少し不安でした」です。')
    request = advance(request, '今は少し苦しい。')
    return actual(request=advance(request, '「寂しかった」ではなく「私も少し怖くなかったです」です。'))


@pytest.mark.parametrize('mutation', ['swap_positions', 'middle', 'drop_one', 'duplicate', 'extra',
                                     'real_time', 'actor', 'particle', 'degree', 'negative', 'answer_time', 'cause'])
def test_equal_event_record_qualifiers_and_source_meanings_are_independently_read(equal_event_record_context, mutation):
    context = equal_event_record_context
    body, follow = context[0].artifact.text, context[0].artifact.reception
    first, _, last = RECORD_PREFIXES
    if mutation == 'swap_positions':
        changed = follow.replace(first, '@first@').replace(last, first).replace('@first@', last)
    else:
        old, new = {
            'middle': (first, RECORD_PREFIXES[1]), 'drop_one': (first, ''),
            'duplicate': (first, first + first), 'extra': ('褒められた時は', first + '褒められた時は'),
            'real_time': (first, '先に起きた方では、'),
            'actor': (first + 'あなたは', first + '相手は'),
            'particle': (first + 'あなたは', first + 'あなたが'),
            'degree': ('少し苦しい', '苦しい'), 'negative': ('怖くなかった', '怖かった'),
            'answer_time': ('回答した時点では', 'その時は'), 'cause': ('し、', 'ので、'),
        }[mutation]
        changed = follow.replace(old, new, 1)
    assert changed != follow and not read_body(context, body.replace(follow, changed, 1)).passed


def test_unqualified_equal_event_legacy_body_still_restores_original_sources(equal_event_record_context):
    context = equal_event_record_context
    body = context[0].artifact.text
    legacy = body
    for prefix in RECORD_PREFIXES:
        legacy = legacy.replace(prefix, '')
    assert legacy != body and read_body(context, legacy).passed


@pytest.mark.parametrize('memo,prefixes', [(RECORD_PAIR_MEMO, (RECORD_PREFIXES[0], RECORD_PREFIXES[2])),
                                        (RECORD_TRIPLE_MEMO, RECORD_PREFIXES)])
def test_equal_event_record_qualifiers_cross_independent_move_boundaries(memo, prefixes):
    context = actual(request=advance(advance(begin(memo), '今は少し苦しい。'), 'その時は少し重かった。'))
    result, plan, _, resolver, selected = context
    moves = plan.response_plan.human_reception_plan.moves
    assert len(moves) == 3
    clauses = result.artifact.reception.split('。')[:-1]
    assert len(clauses) == 3
    assert all(prefix in result.artifact.reception for prefix in prefixes)
    for clause, move in zip(clauses, moves, strict=True):
        assert gate.read_received_discourse(clause + '。', move, plan, resolver, selected) is not None
    assert read_body(context, result.artifact.text).passed


@pytest.mark.parametrize('memo', [MEMO + '褒められたのに、嬉しくなかった。',
    RECORD_PAIR_MEMO.replace('自分は誘われた', '自分が誘われた')])
def test_distinct_complete_event_names_keep_unqualified_grammar(memo):
    context = actual(request=begin(memo))
    body = context[0].artifact.text
    assert not any(prefix in body for prefix in RECORD_PREFIXES)
    assert read_body(context, body).passed
    follow = context[0].artifact.reception
    altered = RECORD_PREFIXES[0] + follow
    assert not read_body(context, body.replace(follow, altered, 1)).passed


@pytest.mark.parametrize('memo', [RECORD_PAIR_MEMO, RECORD_TRIPLE_MEMO])
@pytest.mark.parametrize('last', ['「少し重かった」ではなく「少し苦しかったのです」です。',
                                 '「少し重かった」は誤りです。'])
def test_equal_event_record_saved_revisions_withdrawals_and_original_replay(qcase, qdb, monkeypatch, memo, last):
    user, parent, service = qcase
    qdb.query('update public.emotions set memo=$1 where id=$2', [memo, parent])
    first = current = run(service.start(user, parent))
    for position, reply in enumerate(('今は少し怖かった。', '今は少し重かった。', last)):
        if position:
            current = run(cont(service, user, current, f'record-continue-{position}'))
        current = run(answer(service, user, current, reply, f'record-answer-{position}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        body = current['current_observation']['text']
        assert '先に書かれた方では、' in body and '後に書かれた方では、' in body
        if position == 2:
            assert '少し重かった' not in body
            if 'ではなく' in last:
                assert '「少し苦しかったのです」' in body and '先の回答時点では' in body
            else:
                assert '少し苦しかった' not in body
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved record body must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current


@pytest.mark.parametrize('memo', [RECORD_PAIR_MEMO,
    '褒められたのに、嬉しくなかった。誘われたのに、悲しかった。頼まれたのに、寂しかった。'])
@pytest.mark.parametrize('content', ['重い', 'あなたは誘われた'])
def test_written_position_phrase_in_answer_remains_source_content(memo, content):
    source = '私は先に書かれた方では、' + content + 'と思った'
    request = advance(begin(memo), '今は' + source + '。')
    context = actual(request=request)
    body, follow = context[0].artifact.text, context[0].artifact.reception
    assert '「' + source + '」' in context[0].artifact.observation
    assert source.replace('私は', 'あなたは', 1) in follow or source in follow
    assert read_body(context, body).passed
    if content == '重い' and memo == RECORD_PAIR_MEMO:
        # One phrase belongs to the complete answer, another to the original
        # later event group. Neither is consumed as the other's qualifier.
        assert follow.count(RECORD_PREFIXES[0]) == 2
        assert RECORD_PREFIXES[2] + 'あなたは誘われた' in follow


EXACT_RECORD_MEMO = ('誘われたのに、嬉しくなかった。誘われたのに、悲しかった。'
                     '誘われたのに、寂しかった。')


def exact_record_request(revised, when='今は', last=None, memo=EXACT_RECORD_MEMO):
    request = begin(memo)
    replies = ('「嬉しくなかった」ではなく「私は少し不安でした」です。'
               if revised else 'その時は少し重かった。', when + '少し苦しい。')
    for reply in replies + ((last,) if last else ()):
        request = advance(request, reply)
    return request


@pytest.mark.parametrize('revised', [False, True])
@pytest.mark.parametrize('when', ['今は', 'その時は'])
@pytest.mark.parametrize('last', [None, '「少し苦しい」ではなく「少し怖かった」です。',
                                '「少し苦しい」は誤りです。'])
def test_exact_event_occurrences_keep_every_active_reaction_and_answer(revised, when, last):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning
    request = exact_record_request(revised, when, last)
    context = actual(request=request)
    result, plan, _, resolver, selected = context
    follow = result.artifact.reception
    assert MeaningExperienceEngine().generate(request).artifact.text == result.artifact.text
    assert prepare_emlis_meaning(request).thread.original.normalized_current_input['memo'] == EXACT_RECORD_MEMO
    assert all(prefix + '誘われた' in follow for prefix in RECORD_PREFIXES)
    assert '寂しさを感じ' in follow and '悲しかった' in result.artifact.observation
    assert ('悲しさを感じ' if last and '誤り' in last else '悲しかった') in follow
    assert ('あなたは少し不安だった' if revised else '少し重かった') in follow
    assert ('嬉しくなかった' in follow) == (not revised)
    if last:
        assert '少し苦しい' not in follow
        if 'ではなく' in last:
            assert ('先の回答時点では' if when == '今は' else 'その時は') + '少し怖かった' in follow
    else:
        assert ('回答した時点では' if when == '今は' else 'その時は') + '少し苦しい' in follow
    assert read_body(context, result.artifact.text).passed
    for clause, move in zip(follow.split('。')[:-1], plan.response_plan.human_reception_plan.moves, strict=True):
        assert gate.read_received_discourse(clause + '。', move, plan, resolver, selected) is not None


def test_exact_three_original_revisions_keep_both_corrections_and_middle_answer():
    request = exact_record_request(True, last='「寂しかった」ではなく「私も少し怖くなかったです」です。')
    context = actual(request=request)
    body = context[0].artifact.text
    follow = context[0].artifact.reception
    assert 'あなたは少し不安だった' in follow and '悲しかった' in follow
    assert '回答した時点では少し苦しい' in follow and 'あなたも少し怖くなかった' in follow
    assert '嬉しくなかった' not in body and '寂しかった' not in body
    assert read_body(context, body).passed


@pytest.mark.parametrize('when', ['今は', 'その時は'])
def test_two_exact_event_occurrences_keep_both_originals_and_answers(when):
    memo = '誘われたのに、悲しかった。誘われたのに、寂しかった。'
    request = advance(advance(begin(memo), 'その時は少し重かった。'), when + '少し苦しい。')
    context = actual(request=request)
    follow = context[0].artifact.reception
    assert RECORD_PREFIXES[0] + '誘われたのに、悲しかったし、その時は少し重かった' in follow
    assert RECORD_PREFIXES[2] + '誘われたのに、寂しかったし、' in follow
    assert ('回答した時点では' if when == '今は' else 'その時は') + '少し苦しい' in follow
    assert read_body(context, context[0].artifact.text).passed


@pytest.fixture(scope='module')
def exact_record_context():
    return actual(request=exact_record_request(True))


@pytest.mark.parametrize('old,new', [
    ('先に書かれた方では、', '後に書かれた方では、'),
    ('間に書かれた方では、', '先に書かれた方では、'),
    ('先に書かれた方では、', '先に起きた方では、'),
    ('あなたは少し不安だった', '相手は少し不安だった'),
    ('あなたは少し不安だった', 'あなたは不安だった'),
    ('あなたは少し不安だった', 'あなたは少し不安だ'),
    ('悲しかったし、', ''),
    ('回答した時点では少し苦しい', 'その時は少し苦しい'),
    ('回答した時点では少し苦しい', ''),
    ('誘われたのに、悲しかった', '誘われたので、悲しかった'),
])
def test_exact_record_reception_cannot_borrow_or_drop_another_occurrences_meaning(exact_record_context, old, new):
    context = exact_record_context
    body, follow = context[0].artifact.text, context[0].artifact.reception
    changed = follow.replace(old, new, 1)
    assert changed != follow and not read_body(context, body.replace(follow, changed, 1)).passed


@pytest.mark.parametrize('mutation', ['missing', 'duplicate', 'same_event', 'wrong_proof', 'unknown'])
def test_exact_record_occurrence_proof_does_not_replace_about_or_feeling_guards(exact_record_context, mutation):
    import emlis_ai_grounded_observation_plan as gp
    plan = exact_record_context[1]
    links = [r for r in plan.relations if r.type == 'evaluation_about_event']
    first, second = links
    nuclei, relations = plan.nuclei, plan.relations
    if mutation == 'missing':
        relations = tuple(r for r in relations if r != first)
    elif mutation == 'duplicate':
        relations = (*relations, replace(first, relation_id='duplicate-about'))
    elif mutation == 'same_event':
        relations = tuple(replace(r, from_nucleus_id=first.from_nucleus_id) if r == second else r for r in relations)
    else:
        nuclei = tuple(replace(n, kind='state', semantic_frame=replace(n.semantic_frame,
            predicate_kind='state', modality='uncertain')) if mutation == 'unknown' and n.nucleus_id == first.to_nucleus_id
            else replace(n, semantic_frame=replace(n.semantic_frame, attribute_codes=tuple(
                'thread_subject:distinct_source_occurrence:s999' if c.startswith('thread_subject:distinct_source_occurrence:') else c
                for c in n.semantic_frame.attribute_codes))) if mutation == 'wrong_proof' and n.nucleus_id == first.to_nucleus_id
            else n for n in nuclei)
    assert not gp._thread_retained_reaction_groups(nuclei, relations)


@pytest.mark.parametrize('revised', [False, True])
@pytest.mark.parametrize('last', ['「少し苦しい」ではなく「少し怖かった」です。',
                                '「少し苦しい」は誤りです。'])
def test_exact_record_saved_corrections_withdrawals_and_generate_free_replay(qcase, qdb, monkeypatch, revised, last):
    user, parent, service = qcase
    qdb.query('update public.emotions set memo=$1 where id=$2', [EXACT_RECORD_MEMO, parent])
    first = current = run(service.start(user, parent))
    replies = ('「嬉しくなかった」ではなく「私は少し不安でした」です。'
               if revised else 'その時は少し重かった。', '今は少し苦しい。', last)
    for position, reply in enumerate(replies):
        if position:
            current = run(cont(service, user, current, f'exact-record-continue-{position}'))
        current = run(answer(service, user, current, reply, f'exact-record-answer-{position}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        follow = current['current_observation']['text'].split('Emlisから\n')[-1]
        assert all(prefix + '誘われた' in follow for prefix in RECORD_PREFIXES)
        assert '悲し' in follow and '寂し' in follow
        assert ('少し不安' if revised else '少し重かった') in follow
        if position == 2:
            assert '少し苦しい' not in follow
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved exact body must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current
