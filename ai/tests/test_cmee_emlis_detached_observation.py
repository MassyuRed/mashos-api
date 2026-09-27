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
