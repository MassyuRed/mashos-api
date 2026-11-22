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


def split_positive_answer_proof(context, raw=None):
    """Read the two actual answer sentences against their own planned duties."""
    result, plan, sentence, resolver, selected = context
    line, = (line for line in sentence.lines if line.binding.line_role == 'human_follow')
    index = {m.move_id: m for m in plan.response_plan.human_reception_plan.moves}
    parts = [s + '。' for s in result.artifact.reception.removesuffix('。').split('。')]
    rows = []
    for clause, part in zip(line.reception_clause_plans, parts, strict=True):
        assert len(clause.move_ids) == 1
        move = index[clause.move_ids[0]]
        if move.reception_act == 'recognize_lived_change':
            rows.append((move, part))
    assert len(parts) == 3 and tuple(len(m.target_nucleus_ids) for m, _ in rows) == (2, 1)
    if raw is None:
        raw = ''.join(part for _, part in rows)
    actual_parts = [s + '。' for s in raw.removesuffix('。').split('。')]
    if len(actual_parts) != len(rows):
        return raw, None
    proof, offset = [], 0
    for (move, _), part in zip(rows, actual_parts, strict=True):
        local = gate.read_source_owned_discourse(part, move, plan, resolver, selected)
        if local is None:
            return raw, None
        assert len(local) == 2 * len(move.target_nucleus_ids)
        assert all(part.encode()[a:b] for a, b, _ in local)
        # Convert each sentence-local byte range to the actual joined block.
        proof.extend((a + offset, b + offset, source) for a, b, source in local)
        offset += len(part.encode())
    return raw, tuple(proof)


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
        assert len(group.target_nucleus_ids) == 2 and len(moves) == 3
        _, proof = split_positive_answer_proof(context)
        assert proof is not None and len(proof) == 6
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
    assert len(plan.response_plan.human_reception_plan.moves) == 3
    _, proof = split_positive_answer_proof(context)
    assert proof is not None and len(proof) == 6
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


@pytest.mark.parametrize('mutation', ['missing', 'duplicate', 'same_event', 'wrong_proof', 'unknown',
    'source_range', 'range_value', 'source_order', 'source_link', 'relation_source', 'answer_time', 'event_kind'])
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
    elif mutation == 'relation_source':
        relations = tuple(replace(r, source_span_ids=(*r.source_span_ids, r.source_span_ids[0]))
                          if r == first else r for r in relations)
    elif mutation == 'answer_time':
        nuclei = tuple(replace(n, semantic_frame=replace(n.semantic_frame, attribute_codes=tuple(
            'thread_time:answer_time' if c == 'thread_time:original_occasion' else c
            for c in n.semantic_frame.attribute_codes))) if n.nucleus_id == first.to_nucleus_id else n for n in nuclei)
    elif mutation in {'source_range', 'range_value', 'source_order', 'source_link', 'event_kind'}:
        other = next(n for n in nuclei if n.nucleus_id == second.from_nucleus_id)
        changed = []
        for n in nuclei:
            if n.nucleus_id == first.from_nucleus_id:
                if mutation == 'source_order':
                    n = replace(n, source_span_ids=other.source_span_ids)
                elif mutation == 'event_kind':
                    n = replace(n, semantic_frame=replace(n.semantic_frame, predicate_kind='state'))
                else:
                    codes = tuple(c for c in n.semantic_frame.attribute_codes
                                  if mutation != 'source_range' or not c.startswith('source_fragment_scalar_range:'))
                    codes = tuple('source_fragment_scalar_range:0:999' if mutation == 'range_value'
                        and c.startswith('source_fragment_scalar_range:') else 'source_received_event_link:kedo'
                        if mutation == 'source_link' and c.startswith('source_received_event_link:') else c for c in codes)
                    n = replace(n, semantic_frame=replace(n.semantic_frame, attribute_codes=codes))
            changed.append(n)
        nuclei = tuple(changed)
    else:
        nuclei = tuple(replace(n, kind='state', semantic_frame=replace(n.semantic_frame,
            predicate_kind='state', modality='uncertain')) if mutation == 'unknown' and n.nucleus_id == first.to_nucleus_id
            else replace(n, semantic_frame=replace(n.semantic_frame, attribute_codes=tuple(
                'thread_subject:distinct_source_occurrence:s999' if c.startswith('thread_subject:distinct_source_occurrence:') else c
                for c in n.semantic_frame.attribute_codes))) if mutation == 'wrong_proof' and n.nucleus_id == first.to_nucleus_id
            else n for n in nuclei)
    assert not gp._thread_retained_reaction_groups(nuclei, relations)


@pytest.mark.parametrize('memo', [
    '誘われたのに、嬉しくなかった。誘われたのに、悲しかった。頼まれたのに、寂しかった。',
    '褒められたのに、嬉しくなかった。誘われたのに、悲しかった。褒められたのに、寂しかった。',
])
def test_distinct_occurrence_proof_does_not_expand_a_mixed_original_event_set(memo):
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning, build_updated_grounded_plan
    request = advance(advance(begin(memo), 'その時は少し重かった。'), '今は少し苦しい。')
    plan = build_updated_grounded_plan(prepare_emlis_meaning(request))
    assert not any(c.startswith('thread_subject:distinct_source_occurrence:')
                   for n in plan.nuclei for c in n.semantic_frame.attribute_codes)


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


INITIAL_EXPLANATION_MEMOS = (
    ('褒められたのに、嬉しくなかった。誘われたのに、悲しかった。頼まれたのに、寂しかった。', 3),
    (EXACT_RECORD_MEMO, 3),
    ('誘われたのに、悲しかった。誘われたのに、寂しかった。', 2),
)


@pytest.mark.parametrize('memo,position', [(memo, position)
    for memo, count in INITIAL_EXPLANATION_MEMOS for position in range(count)])
def test_initial_finite_explanation_keeps_each_actual_answer_target(memo, position):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning
    request = begin(memo)
    for _ in range(position):
        request = advance(request, 'その時は少し怖かった。')
    request = advance(request, 'その時は少し重かったのです。')
    prepared = prepare_emlis_meaning(request)
    assert not prepared.checkpoint.unresolved_parts
    context = actual(request=request)
    result, plan, _, resolver, _ = context
    assert '「少し重かったのです」' in result.artifact.observation
    assert '少し重かったの' in result.artifact.reception
    assert read_body(context, result.artifact.text).passed
    assert MeaningExperienceEngine().generate(request).artifact.text == result.artifact.text
    updated = prepared.checkpoint.answer_update.updates[-1]
    about = [relation for relation in plan.relations if relation.type == 'evaluation_about_event'
             and relation.to_nucleus_id in updated.changed_claim_refs]
    assert len(about) == 1
    target = next(row for row in plan.nuclei if row.nucleus_id == about[0].from_nucleus_id)
    target_span = resolver.resolve(target.source_span_ids[0])
    original_clauses = memo.split('。')
    assert target_span.raw_text == original_clauses[position]
    assert target_span.start_index == sum(len(clause) + 1 for clause in original_clauses[:position])
    if count := memo.count('誘われたのに'):
        if count == len(memo.split('。')) - 1:
            expected = RECORD_PREFIXES if count == 3 else (RECORD_PREFIXES[0], RECORD_PREFIXES[2])
            assert all(prefix in result.artifact.reception for prefix in expected)


@pytest.mark.parametrize('reply,source,when', [
    ('その時は少し重かったのです。', '少し重かったのです', 'original_occasion'),
    ('今は少し重いのです。', '少し重いのです', 'answer_time'),
    ('今は私も少し怖くないのです。', '私も少し怖くないのです', 'answer_time'),
    ('その時は少し怖くなかったのだった。', '少し怖くなかったのだった', 'original_occasion'),
    ('その時は少し嬉しかったのです。', '少し嬉しかったのです', 'original_occasion'),
    ('今は嬉しいのです。', '嬉しいのです', 'answer_time'),
])
def test_initial_explanation_preserves_inner_tense_polarity_owner_and_time(reply, source, when):
    context = actual(request=advance(begin(), reply))
    result, plan, _, resolver, _ = context
    assert '「' + source + '」' in result.artifact.observation
    answer_nucleus = next(n for n in plan.nuclei if n.source_fields == ('answer_text_private',))
    assert 'thread_time:' + when in answer_nucleus.semantic_frame.attribute_codes
    assert read_body(context, result.artifact.text).passed


@pytest.mark.parametrize('reply', ['その時は少し楽しかったのです。', '今は楽しいのです。',
    'その時は友人は少し重かったのです。', 'その時は少し重かったので。',
    'その時は少し重かったらしいのです。', '少し重いのです。'])
def test_initial_explanation_does_not_invent_lexicon_owner_or_time(reply):
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning
    prepared = prepare_emlis_meaning(advance(begin(), reply))
    assert not prepared.accepted_nuclei
    assert prepared.checkpoint.unresolved_parts
    assert all(item.operation != 'WITHDRAW' for item in prepared.checkpoint.answer_update.updates)


@pytest.mark.parametrize('memo', [INITIAL_EXPLANATION_MEMOS[0][0], EXACT_RECORD_MEMO])
def test_initial_explanation_explicit_self_correction_keeps_other_original_reactions(memo):
    request = advance(begin(memo), '書き方を間違えた。その時は少し重かったのです。')
    context = actual(request=request)
    result = context[0]
    assert '「少し重かったのです」' in result.artifact.observation
    assert '「嬉しくなかった」' not in result.artifact.observation
    assert '悲し' in result.artifact.reception and '寂し' in result.artifact.reception
    assert read_body(context, result.artifact.text).passed


@pytest.fixture(scope='module')
def initial_explanation_context():
    return actual(request=advance(begin(EXACT_RECORD_MEMO), '今は私も少し怖くないのです。'))


@pytest.mark.parametrize('old,new', [('少し怖くない', '怖くない'), ('怖くない', '怖い'),
    ('あなたも', '相手も'), ('回答した時点では', 'その時は'),
    ('怖くない', '怖くなかった'), (RECORD_PREFIXES[0], RECORD_PREFIXES[2])])
def test_initial_explanation_meaning_mutations_fail_without_author_oracle(initial_explanation_context, old, new):
    context = initial_explanation_context
    result = context[0]
    changed = result.artifact.reception.replace(old, new, 1)
    assert changed != result.artifact.reception
    assert not read_body(context, result.artifact.text.replace(result.artifact.reception, changed, 1)).passed


@pytest.mark.parametrize('memo', [INITIAL_EXPLANATION_MEMOS[0][0], EXACT_RECORD_MEMO])
@pytest.mark.parametrize('last', ['「少し重かったのです」ではなく「少し苦しかったのです」です。',
                                 '「少し重かったのです」は誤りです。'])
def test_initial_explanation_saved_revision_withdrawal_and_nonregenerating_replay(qcase, qdb, monkeypatch, memo, last):
    user, parent, service = qcase
    qdb.query('update public.emotions set memo=$1 where id=$2', [memo, parent])
    first = current = run(service.start(user, parent))
    for position, reply in enumerate(('今は少し重かったのです。', 'その時は少し怖かった。', last)):
        if position:
            current = run(cont(service, user, current, f'initial-explanation-continue-{position}'))
        current = run(answer(service, user, current, reply, f'initial-explanation-answer-{position}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        body = current['current_observation']['text']
        if position == 2:
            assert '少し重かった' not in body
            if 'ではなく' in last:
                assert '「少し苦しかったのです」' in body and '先の回答時点では' in body
            else:
                assert '少し苦しかった' not in body
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved explanation must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current


@pytest.mark.parametrize('memo,position', [(memo, position)
    for memo, _ in INITIAL_EXPLANATION_MEMOS[:2] for position in range(3)])
def test_original_quoted_explanation_keeps_each_actual_target_and_other_reactions(memo, position):
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    old = ('嬉しくなかった', '悲しかった', '寂しかった')[position]
    new = '私も少し重くなかったのだった'
    request = advance(begin(memo), '「' + old + '」ではなく「' + new + '」です。')
    prepared = prepare_emlis_meaning(request)
    update = prepared.checkpoint.answer_update.updates[0]
    assert prepared.checkpoint.assessment_status == 'RESOLVED' and update.operation == 'REVISE'
    assert not prepared.checkpoint.unresolved_parts
    assert update.superseded_claim_refs == update.target_meaning_refs
    context = actual(request=request)
    result, plan, _, resolver, _ = context
    assert old not in result.artifact.text and '「' + new + '」' in result.artifact.observation
    assert 'あなたも少し重くなかったのでしたね' in result.artifact.reception
    assert all(other in result.artifact.observation for other in
               ('嬉しくなかった', '悲しかった', '寂しかった') if other != old)
    prior_contrast = [r for r in prepared.original_plan.relations if r.type == 'contrast'
                      and r.to_nucleus_id in update.target_meaning_refs]
    assert len(prior_contrast) == 1
    target = next(n for n in prepared.original_plan.nuclei if n.nucleus_id == prior_contrast[0].from_nucleus_id)
    span = resolver.resolve(target.source_span_ids[0])
    clauses = memo.split('。')
    assert span.raw_text == clauses[position]
    assert span.start_index == sum(len(c) + 1 for c in clauses[:position])
    if memo == INITIAL_EXPLANATION_MEMOS[1][0]:
        assert all(RECORD_PREFIXES[other] + '誘われた' in result.artifact.reception
                   for other in range(3) if other != position)
    assert MeaningExperienceEngine().generate(request).artifact.text == result.artifact.text
    assert read_body(context, result.artifact.text).passed


@pytest.mark.parametrize('new', ['少し重かったのです', '私も少し重くなかったのです',
    '私はとても重いのだ', '少し重くないのだった', '嬉しかったのです', '嬉しいのです'])
def test_original_quoted_explanation_keeps_new_subject_polarity_degree_and_tenses(new):
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning
    reply = '「嬉しくなかった」ではなく「' + new + '」です。'
    request = advance(begin(INITIAL_EXPLANATION_MEMOS[0][0]), reply)
    prepared = prepare_emlis_meaning(request)
    assert prepared.checkpoint.answer_update.updates[0].operation == 'REVISE'
    assert not prepared.checkpoint.unresolved_parts
    nucleus = prepared.accepted_nuclei[0]
    start = reply.index('「' + new + '」') + 1
    assert f'source_fragment_scalar_range:{start}:{start + len(new)}' in nucleus.semantic_frame.attribute_codes
    assert 'thread_time:original_occasion' in nucleus.semantic_frame.attribute_codes
    context = actual(request=request)
    assert '「' + new + '」' in context[0].artifact.observation
    assert '嬉しくなかった' not in context[0].artifact.text
    assert read_body(context, context[0].artifact.text).passed


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
def test_original_quoted_explanation_pure_meaning_keeps_memo_field_and_new_range(field):
    from test_cmee_emlis_q1_thread import initial, answered, ORIGINAL
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning
    kwargs = {'memo': ORIGINAL + '少し重かった。'} if field == 'memo' else {'memo_action': '少し重かった。'}
    reply = '「少し重かった」ではなく「少し重かったのです」です。'
    prepared = prepare_emlis_meaning(answered(reply, initial(**kwargs)))
    update = prepared.checkpoint.answer_update.updates[0]
    assert prepared.checkpoint.assessment_status == 'RESOLVED' and update.operation == 'REVISE'
    assert not prepared.checkpoint.unresolved_parts
    old = next(n for n in prepared.original_plan.nuclei if n.nucleus_id in update.target_meaning_refs)
    assert old.source_fields == (field,)
    new = prepared.accepted_nuclei[0]
    start = reply.index('「少し重かったのです」') + 1
    assert f'source_fragment_scalar_range:{start}:{start + len("少し重かったのです")}' in new.semantic_frame.attribute_codes


@pytest.mark.parametrize('new', ['友人は少し重かったのです', '少し楽しかったのです',
    '少し重かったので', '少し重かったらしいのです'])
def test_original_quoted_explanation_keeps_unsupported_replacement_boundary(new):
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning
    prepared = prepare_emlis_meaning(advance(begin(), '「嬉しくなかった」ではなく「' + new + '」です。'))
    assert not prepared.accepted_nuclei
    assert prepared.checkpoint.assessment_status == 'PARTIAL'
    assert prepared.checkpoint.unresolved_parts[0].reason_code == 'correction_replacement_unsupported'
    assert prepared.checkpoint.answer_update.updates[0].operation == 'WITHDRAW'


def test_original_quoted_explanation_does_not_guess_an_ambiguous_original_target():
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning
    memo = '誘われたのに、悲しかった。頼まれたのに、悲しかった。'
    prepared = prepare_emlis_meaning(advance(begin(memo), '「悲しかった」ではなく「少し重かったのです」です。'))
    assert not prepared.accepted_nuclei and not prepared.checkpoint.inactive_claim_refs
    assert not prepared.checkpoint.answer_update.updates
    assert prepared.checkpoint.unresolved_parts[0].reason_code == 'correction_target_unresolved'


@pytest.fixture(scope='module')
def original_quoted_explanation_context():
    return actual(request=advance(begin(INITIAL_EXPLANATION_MEMOS[1][0]),
        '「嬉しくなかった」ではなく「私も少し重くなかったのだった」です。'))


@pytest.mark.parametrize('old,new', [('少し重くなかった', '重くなかった'),
    ('重くなかった', '重かった'), ('あなたも', 'あなたは'), ('あなたも', '友人も'),
    ('重くなかった', '重くない'), ('のでしたね', 'のですね'),
    (RECORD_PREFIXES[0], RECORD_PREFIXES[2])])
def test_original_quoted_explanation_mutations_fail_without_author_oracle(original_quoted_explanation_context, old, new):
    context = original_quoted_explanation_context
    before = context[0].artifact.text
    changed = before.replace(old, new, 1)
    assert changed != before and not read_body(context, changed).passed


@pytest.mark.parametrize('memo', [INITIAL_EXPLANATION_MEMOS[0][0], INITIAL_EXPLANATION_MEMOS[1][0]])
@pytest.mark.parametrize('last', ['「少し重かったのです」ではなく「少し苦しかったのです」です。',
                                 '「少し重かったのです」は誤りです。'])
def test_original_quoted_explanation_saved_recorrection_withdrawal_and_nonregenerating_replay(qcase, qdb, monkeypatch, memo, last):
    user, parent, service = qcase
    qdb.query('update public.emotions set memo=$1 where id=$2', [memo, parent])
    first = current = run(service.start(user, parent))
    replies = ('「嬉しくなかった」ではなく「少し重かったのです」です。', '今は少し怖かった。', last)
    for position, reply in enumerate(replies):
        if position:
            current = run(cont(service, user, current, f'original-explanation-continue-{position}'))
        current = run(answer(service, user, current, reply, f'original-explanation-answer-{position}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        body = current['current_observation']['text']
        assert '嬉しくなかった' not in body and '悲しかった' in body and '寂しかった' in body
        if position == 2:
            assert '少し重かった' not in body
            if 'ではなく' in last:
                assert '「少し苦しかったのです」' in body
            else:
                assert '少し苦しかった' not in body
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved original explanation must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('position', [1, 2])
@pytest.mark.parametrize('new', ['少し重かった', '少し重かったのです', '私も少し重くなかったのだった'])
def test_same_name_original_reaction_revision_keeps_source_positions(field, position, new):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    old = ('嬉しくなかった', '悲しかった', '寂しかった')[position]
    request = begin(EXACT_RECORD_MEMO if field == 'memo' else '',
                    EXACT_RECORD_MEMO if field == 'memo_action' else '')
    request = advance(request, f'「{old}」ではなく「{new}」です。')
    context = actual(request=request)
    result, plan, _, resolver, _ = context
    assert MeaningExperienceEngine().generate(request).artifact.text == result.artifact.text
    assert old not in result.artifact.text and f'「{new}」' in result.artifact.observation
    events = [n for n in plan.nuclei if n.kind == 'event' and n.source_fields == (field,)]
    assert len(events) == 3
    assert [resolver.resolve(n.source_span_ids[0]).start_index for n in events] == [0, 15, 28]
    assert all(RECORD_PREFIXES[i] + '誘われた' in result.artifact.reception
               for i in range(3) if i != position)
    assert read_body(context, result.artifact.text).passed


@pytest.fixture(scope='module', params=[1, 2])
def same_name_original_revision_context(request):
    old = ('嬉しくなかった', '悲しかった', '寂しかった')[request.param]
    return actual(request=advance(begin(EXACT_RECORD_MEMO),
        f'「{old}」ではなく「私も少し重くなかったのだった」です。'))


def test_same_name_original_revision_rejects_position_changes_without_authors(same_name_original_revision_context):
    context = same_name_original_revision_context
    body = context[0].artifact.text
    present = [prefix for prefix in RECORD_PREFIXES if prefix in context[0].artifact.reception]
    assert len(present) == 2
    for prefix in present:
        for wrong in RECORD_PREFIXES:
            if wrong != prefix:
                changed = body.replace(prefix, wrong, 1)
                assert changed != body and not read_body(context, changed).passed
        changed = body.replace(prefix, '', 1)
        assert changed != body and not read_body(context, changed).passed
    changed = body.replace(present[0], '__position__', 1).replace(present[1], present[0], 1).replace('__position__', present[1], 1)
    assert changed != body and not read_body(context, changed).passed


@pytest.fixture(scope='module')
def same_name_middle_revision_context():
    return actual(request=advance(begin(EXACT_RECORD_MEMO),
        '「悲しかった」ではなく「私も少し重くなかったのだった」です。'))


@pytest.mark.parametrize('mutation', ['missing', 'start', 'end', 'duplicate', 'swapped_pairs', 'swapped_reactions', 'cause'])
def test_same_name_middle_revision_rejects_event_scope_corruption_without_authors(same_name_middle_revision_context, mutation):
    context = same_name_middle_revision_context
    body, observation = context[0].artifact.text, context[0].artifact.observation
    fact = '「誘われた」という出来事がありました。'
    first = '「誘われた」と「嬉しくなかった」が、異なる向きのまま同時にあります。'
    last = '「誘われた」と「寂しかった」が、異なる向きのまま同時にあります。'
    assert all(value in observation for value in (first, fact, last))
    if mutation in {'missing', 'start', 'end', 'duplicate'}:
        changed = observation.replace(fact, '', 1)
        if mutation == 'start':
            changed = fact + ' ' + changed
        elif mutation == 'end':
            changed += ' ' + fact
        elif mutation == 'duplicate':
            changed = observation.replace(fact, fact + ' ' + fact, 1)
    elif mutation == 'swapped_pairs':
        changed = observation.replace(first, '__pair__', 1).replace(last, first, 1).replace('__pair__', last, 1)
    elif mutation == 'swapped_reactions':
        changed = observation.replace('嬉しくなかった', '__reaction__', 1).replace('寂しかった', '嬉しくなかった', 1).replace('__reaction__', '寂しかった', 1)
    else:
        changed = observation.replace(first, first[:-1] + '、これが重さの原因です。', 1)
    assert changed != observation
    with patch.object(surface, '_render_relation', side_effect=AssertionError('no relation oracle')), patch.object(
            surface, '_render_observation_with_relations', side_effect=AssertionError('no line oracle')):
        assert not read_body(context, body.replace(observation, changed, 1)).passed


@pytest.mark.parametrize('position', [1, 2])
@pytest.mark.parametrize('last', ['「少し重かったのです」ではなく「少し苦しかったのです」です。',
                                 '「少し重かったのです」は誤りです。'])
def test_same_name_original_revision_saved_replay_keeps_original_and_positions(qcase, qdb, monkeypatch, position, last):
    user, parent, service = qcase
    qdb.query('update public.emotions set memo=$1 where id=$2', [EXACT_RECORD_MEMO, parent])
    first = current = run(service.start(user, parent))
    old = ('嬉しくなかった', '悲しかった', '寂しかった')[position]
    replies = (f'「{old}」ではなく「少し重かったのです」です。', last)
    for step, reply in enumerate(replies):
        if step:
            current = run(cont(service, user, current, f'same-name-revision-continue-{step}'))
        current = run(answer(service, user, current, reply, f'same-name-revision-answer-{step}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        body = current['current_observation']['text']
        assert old not in body
        assert all(RECORD_PREFIXES[i] + '誘われた' in body for i in range(3) if i != position), (step, body)
        if step == 1:
            assert '少し重かった' not in body
            assert ('「少し苦しかったのです」' in body) == ('ではなく' in last)
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved same-name revision must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current


@pytest.mark.parametrize('position', [1, 2])
def test_same_name_original_revision_first_saved_body_replays_without_regeneration(qcase, qdb, monkeypatch, position):
    user, parent, service = qcase
    qdb.query('update public.emotions set memo=$1 where id=$2', [EXACT_RECORD_MEMO, parent])
    first = run(service.start(user, parent))
    old = ('嬉しくなかった', '悲しかった', '寂しかった')[position]
    current = run(answer(service, user, first,
        f'「{old}」ではなく「私も少し重くなかったのだった」です。', f'same-name-first-revision-{position}'))
    assert current['body_state'] == 'REFINED' and current['original'] == first['original']
    body = current['current_observation']['text']
    assert old not in body and '私も少し重くなかったのだった' in body
    assert all(RECORD_PREFIXES[i] + '誘われた' in body for i in range(3) if i != position)
    assert qdb.query('select memo from public.emotions where id=$1', [parent])['rows'][0]['memo'] == EXACT_RECORD_MEMO
    with monkeypatch.context() as saved:
        saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('first saved revision must not regenerate'))
        assert run(service.get(user, parent)) == run(service.start(user, parent)) == current


@pytest.mark.parametrize('position', [1, 2])
def test_same_name_original_revision_next_answer_keeps_each_source_scope_without_authors(position):
    old = ('嬉しくなかった', '悲しかった', '寂しかった')[position]
    request = advance(advance(begin(EXACT_RECORD_MEMO),
        f'「{old}」ではなく「少し重かったのです」です。'), '今は少し怖かった。')
    context = actual(request=request)
    body = context[0].artifact.text
    assert all(RECORD_PREFIXES[i] + '誘われた' in body for i in range(3) if i != position)
    assert read_body(context, body).passed
    for prefix in (RECORD_PREFIXES[i] for i in range(3) if i != position):
        for wrong in RECORD_PREFIXES:
            if wrong != prefix:
                changed = body.replace(prefix, wrong, 1)
                assert changed != body and not read_body(context, changed).passed
    observation = context[0].artifact.observation
    answer_fact = re.search(r'「誘われた」ことについて、回答した時点の受け止めは「少し怖かった」と書かれています。', observation)
    assert answer_fact
    for changed in (body.replace(answer_fact[0], '', 1),
                    body.replace(answer_fact[0], answer_fact[0].replace('回答した時点', 'その時'), 1),
                    body.replace(answer_fact[0], answer_fact[0].replace('少し怖かった', '少し重かった'), 1),
                    body.replace(answer_fact[0], answer_fact[0][:-1] + '、これが重さの原因です。', 1)):
        assert changed != body and not read_body(context, changed).passed
    plan, resolver, selected = context[1], context[3], context[4]
    reception_plan = plan.response_plan.human_reception_plan
    moves = reception_plan.moves
    assert moves[0].move_role == 'significance'
    raw = next(part + '。' for part in context[0].artifact.reception.split('。') if part.startswith(RECORD_PREFIXES[0]))
    assert gate.read_received_discourse(raw, moves[0], plan, resolver, selected) is not None
    for changed_moves in (moves[1:], tuple(reversed(moves)),
                          (replace(moves[0], required=False), *moves[1:]),
                          (replace(moves[0], move_id='foreign-qualified-move'), *moves[1:])):
        altered = replace(plan, response_plan=replace(plan.response_plan,
            human_reception_plan=replace(reception_plan, moves=changed_moves)))
        assert gate.read_received_discourse(raw, moves[0], altered, resolver, selected) is None


@pytest.mark.parametrize('position', [1, 2])
def test_same_name_original_revision_next_saved_answer_keeps_positions_and_terminal_replay(qcase, qdb, monkeypatch, position):
    user, parent, service = qcase
    qdb.query('update public.emotions set memo=$1 where id=$2', [EXACT_RECORD_MEMO, parent])
    first = run(service.start(user, parent))
    old = ('嬉しくなかった', '悲しかった', '寂しかった')[position]
    current = run(answer(service, user, first,
        f'「{old}」ではなく「少し重かったのです」です。', 'same-name-next-first'))
    current = run(cont(service, user, current, 'same-name-next-continue'))
    current = run(answer(service, user, current, '今は少し怖かった。', 'same-name-next-answer'))
    assert current['body_state'] == 'REFINED' and current['original'] == first['original']
    body = current['current_observation']['text']
    assert all(RECORD_PREFIXES[i] + '誘われた' in body for i in range(3) if i != position)
    assert '少し怖かった' in body and '少し重かったのです' in body
    assert not current['can_continue']
    assert qdb.query('select memo from public.emotions where id=$1', [parent])['rows'][0]['memo'] == EXACT_RECORD_MEMO
    with monkeypatch.context() as saved:
        saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('next saved revision must not regenerate'))
        assert run(service.get(user, parent)) == run(service.start(user, parent)) == current


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('position', [0, 1, 2])
def test_withdrawn_event_keeps_immutable_written_positions(field, position):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    events = ('私は誘われた', '自分は誘われた', 'わたしは誘われた')
    feelings = ('嬉しくなかった', '悲しかった', '寂しかった')
    memo = ''.join(event + 'のに、' + feeling + '。' for event, feeling in zip(events, feelings))
    request = begin(memo if field == 'memo' else '', memo if field == 'memo_action' else '')
    request = advance(request, f'「{events[position]}」は誤りです。')
    context = actual(request=request)
    result, plan, _, resolver, _ = context
    assert MeaningExperienceEngine().generate(request).artifact.text == result.artifact.text
    active_events = [n for n in plan.nuclei if n.kind == 'event' and n.source_fields == (field,)]
    assert len(active_events) == 2
    assert events[position] not in result.artifact.text
    assert all(feeling in result.artifact.observation for feeling in feelings)
    expected = {RECORD_PREFIXES[i] for i in range(3) if i != position}
    assert {prefix for prefix in RECORD_PREFIXES if prefix in result.artifact.reception} == expected
    assert len(resolver.resolve_many(tuple(sid for sid in resolver.span_ids
        if resolver.resolve(sid).source_field == field))) == 3
    assert read_body(context, result.artifact.text).passed
    for prefix in expected:
        for wrong in set(RECORD_PREFIXES) - {prefix}:
            changed = result.artifact.text.replace(prefix, wrong, 1)
            assert changed != result.artifact.text and not read_body(context, changed).passed
    # Recovering an original written position must not revive its withdrawn event.
    changed = result.artifact.text.replace('その時は', events[position] + 'ので、その時は', 1)
    assert changed != result.artifact.text and not read_body(context, changed).passed


@pytest.mark.parametrize('position', [0, 1])
def test_withdrawn_event_keeps_position_of_single_remaining_event(position):
    events = ('私は誘われた', '自分は誘われた')
    memo = events[0] + 'のに、悲しかった。' + events[1] + 'のに、寂しかった。'
    context = actual(request=advance(begin(memo), f'「{events[position]}」は誤りです。'))
    result, plan, _, _, _ = context
    assert len([n for n in plan.nuclei if n.kind == 'event' and n.source_fields == ('memo',)]) == 1
    correct = ('後' if position == 0 else '先') + 'に書かれた方では、'
    wrong = ('先' if position == 0 else '後') + 'に書かれた方では、'
    assert correct + 'あなたは誘われた' in result.artifact.reception
    assert events[position] not in result.artifact.text
    assert read_body(context, result.artifact.text).passed
    assert not read_body(context, result.artifact.text.replace(correct, wrong)).passed


def test_withdrawn_event_position_rejects_duplicate_active_source_ranges():
    memo = '私は誘われたのに、悲しかった。自分は誘われたのに、寂しかった。'
    context = actual(request=advance(begin(memo), '「私は誘われた」は誤りです。'))
    _, plan, _, resolver, _ = context
    event = next(n for n in plan.nuclei if n.kind == 'event' and n.source_fields == ('memo',))
    altered = replace(plan, nuclei=plan.nuclei + (replace(event, nucleus_id='duplicate:event'),))
    assert reception._received_event_record_prefixes(altered, resolver) == {}
    with patch.object(reception, '_received_event_record_prefixes', side_effect=AssertionError('no position oracle')):
        assert gate._read_received_record_prefixes(altered, resolver) == {}


def test_withdrawn_event_position_preserves_received_answer_and_standalone_feeling_boundary():
    memo = '褒められたのに、嬉しくなかった。私は誘われたのに、悲しかった。自分は誘われたのに、寂しかった。'
    request = advance(advance(begin(memo), 'その時は少し重かった。'), 'その時は私も頼まれたようで、重かった。')
    context = actual(request=advance(request, '「私は誘われた」は誤りです。'))
    body = context[0].artifact.text
    assert context[0].artifact.reception == (
        'その時は悲しかったし、その時、あなたも頼まれたようで、重かったのですね。'
        '褒められたのに嬉しくなかったことと、その時に少し重かったことを見失わず、小さくせずに受け止めています。'
        '後に書かれた方では、あなたは誘われたのに、寂しさを感じたのですね。')
    assert '私は誘われた' not in body
    assert read_body(context, body).passed
    for old, new in [('後に書かれた方では、', '先に書かれた方では、'),
                     ('その時、あなたも頼まれたようで、重かった', 'その時、友人も頼まれたようで、重かった'),
                     ('その時、あなたも頼まれたようで、重かった', '回答した時点で、あなたも頼まれたようで、重かった')]:
        changed = body.replace(old, new)
        assert changed != body and not read_body(context, changed).passed


@pytest.mark.parametrize('prior_answer', [False, True])
@pytest.mark.parametrize('position', [0, 1, 2])
def test_withdrawn_event_positions_survive_saved_replay(qcase, qdb, monkeypatch, prior_answer, position):
    user, parent, _ = qcase
    service = active(monkeypatch)
    events = ('私は誘われた', '自分は誘われた', 'わたしは誘われた')
    memo = ''.join(event + 'のに、' + feeling + '。' for event, feeling in
                   zip(events, ('嬉しくなかった', '悲しかった', '寂しかった')))
    qdb.query('update public.emotions set memo=$1 where id=$2', [memo, parent])
    first = current = run(service.start(user, parent))
    if prior_answer:
        current = run(answer(service, user, current, '今は少し怖い。', 'written-place-first-answer'))
        current = run(cont(service, user, current, 'written-place-continue'))
    current = run(answer(service, user, current, f'「{events[position]}」は誤りです。', 'written-place-withdraw'))
    assert current['body_state'] == 'REFINED' and current['original'] == first['original']
    body = current['current_observation']['text']
    assert events[position] not in body
    # The first source with an existing answer uses the established complete
    # answer discourse, not the original-only qualified significance form.
    # Keep that eligibility boundary and check every displayed original place.
    assert {prefix for prefix in RECORD_PREFIXES if prefix in body} == {
        RECORD_PREFIXES[i] for i in range(3) if i != position and not (prior_answer and i == 0)}
    for i in range(3):
        assert (events[i] in body) == (i != position)
    if prior_answer:
        assert '少し怖い' in body and ('回答した時点' in body or '先の回答時点' in body)
    assert qdb.query('select memo from public.emotions where id=$1', [parent])['rows'][0]['memo'] == memo
    with monkeypatch.context() as saved:
        saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved withdrawal must not regenerate'))
        assert run(service.get(user, parent)) == run(service.start(user, parent)) == current


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('owner,link', [
    ('私は', 'のに'), ('自分は', 'けど'), ('わたしは', 'けれど'), ('私は', 'けれども'),
])
def test_explicit_received_topic_keeps_finite_negative_contrast(field, owner, link):
    memo = owner + '誘われた' + link + '、嬉しくなかった。頼まれたのに、悲しかった。'
    context = actual(request=begin(memo if field == 'memo' else '', memo if field == 'memo_action' else ''))
    result = context[0]
    clause = 'あなたは誘われた' + link + '、嬉しくなく'
    assert result.artifact.reception == clause + '、頼まれたのに、悲しさを感じたのですね。'
    assert 'あなたは誘われたことは' not in result.artifact.reception
    assert read_body(context, result.artifact.text).passed
    # Change only reception: observation must not donate its missing meaning.
    alternatives = [
        clause.replace('あなたは', '友人は'), clause.replace('あなたは', 'あなたが'),
        clause.replace('あなたは', ''), clause.replace('誘われた', '頼まれた'),
        clause.replace('嬉しくなく', '嬉しく'), clause.replace('嬉しくなく', '嬉しくないし'),
        clause.replace(link + '、', 'ので、'),
        clause.replace(link + '、', ('けど' if link == 'のに' else 'のに') + '、'), '',
    ]
    for wrong in alternatives:
        follow = result.artifact.reception.replace(clause, wrong, 1)
        assert follow != result.artifact.reception
        changed = result.artifact.text.replace(result.artifact.reception, follow, 1)
        assert changed != result.artifact.text and not read_body(context, changed).passed


@pytest.mark.parametrize('position', [0, 1, 2])
def test_explicit_received_topic_preserves_same_name_positions_and_old_reading(position):
    owners = ('私は', '自分は', 'わたしは')
    feelings = ['悲しかった', '寂しかった', '怖かった']
    feelings[position] = '嬉しくなかった'
    memo = ''.join(owner + '誘われたのに、' + feeling + '。'
                   for owner, feeling in zip(owners, feelings))
    context = actual(request=begin(memo))
    result = context[0]
    finite = 'あなたは誘われたのに、嬉しくな' + ('かった' if position == 2 else 'く')
    assert RECORD_PREFIXES[position] + finite in result.artifact.reception
    assert read_body(context, result.artifact.text).passed
    nominal = 'あなたは誘われたことは、嬉しさにはつながら' + ('なかった' if position == 2 else 'ず')
    legacy = result.artifact.text.replace(result.artifact.reception,
        result.artifact.reception.replace(finite, nominal, 1), 1)
    assert legacy != result.artifact.text and read_body(context, legacy).passed
    for wrong in set(RECORD_PREFIXES) - {RECORD_PREFIXES[position]}:
        changed = result.artifact.text.replace(RECORD_PREFIXES[position], wrong, 1)
        assert changed != result.artifact.text and not read_body(context, changed).passed


@pytest.mark.parametrize('owner', ['', '私が'])
def test_explicit_received_topic_keeps_other_nominal_owners(owner):
    context = actual(request=begin(owner + '誘われたのに、嬉しくなかった。頼まれたのに、悲しかった。'))
    expected = ('あなたが' if owner else '') + '誘われたことは、嬉しさにはつながらず'
    assert context[0].artifact.reception.startswith(expected)
    assert read_body(context, context[0].artifact.text).passed


@pytest.mark.parametrize('degree', ['少し', 'とても'])
def test_explicit_received_topic_keeps_existing_degree_scope(degree):
    context = actual(request=begin('私は誘われたのに、' + degree + '嬉しくなかった。頼まれたのに、悲しかった。'))
    result = context[0]
    assert 'あなたは誘われたのに、' + degree + '嬉しくなかったし、' in result.artifact.reception
    assert read_body(context, result.artifact.text).passed
    changed = result.artifact.text.replace(result.artifact.reception,
        result.artifact.reception.replace(degree, '', 1), 1)
    assert changed != result.artifact.text and not read_body(context, changed).passed


TOPIC_SEQUENCE_MEMO = ('褒められたのに、嬉しくなかった。私は誘われたのに、嬉しくなかった。'
                       '自分は頼まれたのに、悲しかった。')
TOPIC_SEQUENCE = ('今は少し怖い。', '「少し怖い」ではなく「私も少し重いです」です。',
                  '「自分は頼まれた」は誤りです。')


@pytest.mark.parametrize('steps', [1, 2, 3])
def test_explicit_received_topic_survives_answer_revision_and_withdrawal(steps):
    request = begin(TOPIC_SEQUENCE_MEMO)
    for reply in TOPIC_SEQUENCE[:steps]:
        request = advance(request, reply)
    context = actual(request=request)
    result = context[0]
    assert 'あなたは誘われたのに、嬉しくな' in result.artifact.reception
    assert 'あなたは誘われたことは' not in result.artifact.reception
    assert ('自分は頼まれた' in result.artifact.text) == (steps < 3)
    assert read_body(context, result.artifact.text).passed
    for old, new in [('あなたは誘われた', '友人は誘われた'),
                     ('あなたは誘われたのに、嬉しくな', 'あなたは誘われたのに、嬉し'),
                     ('先の回答時点' if steps > 1 else '回答した時点', 'その時')]:
        follow = result.artifact.reception.replace(old, new)
        assert follow != result.artifact.reception
        changed = result.artifact.text.replace(result.artifact.reception, follow, 1)
        assert changed != result.artifact.text and not read_body(context, changed).passed


@pytest.mark.parametrize('withdraw', ['褒められた', '自分は頼まれた'])
def test_explicit_received_topic_saved_sequence_keeps_original_and_exact_replay(qcase, qdb, monkeypatch, withdraw):
    user, parent, _ = qcase
    service = active(monkeypatch)
    qdb.query('update public.emotions set memo=$1 where id=$2', [TOPIC_SEQUENCE_MEMO, parent])
    first = current = run(service.start(user, parent))
    for index, reply in enumerate((*TOPIC_SEQUENCE[:2], f'「{withdraw}」は誤りです。')):
        if index:
            current = run(cont(service, user, current, f'topic-continue-{index}'))
        current = run(answer(service, user, current, reply, f'topic-answer-{index}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        body = current['current_observation']['text']
        assert 'あなたは誘われたのに、嬉しくな' in body and 'あなたは誘われたことは' not in body
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved topic sequence must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current
    assert withdraw not in body and not current['can_continue']
    assert qdb.query('select memo from public.emotions where id=$1', [parent])['rows'][0]['memo'] == TOPIC_SEQUENCE_MEMO


def test_explicit_received_topic_prior_saved_nominal_body_is_not_rewritten(qcase, qdb, monkeypatch):
    user, parent, _ = qcase
    service = active(monkeypatch)
    memo = '私は誘われたのに、嬉しくなかった。頼まれたのに、悲しかった。'
    qdb.query('update public.emotions set memo=$1 where id=$2', [memo, parent])
    author = reception._source_grounded_received_discourse

    def prior_author(*args, **kwargs):
        text = author(*args, **kwargs)
        return text.replace('あなたは誘われたのに、嬉しくなく',
            'あなたは誘われたことは、嬉しさにはつながらず') if text else text

    with monkeypatch.context() as prior:
        prior.setattr(reception, '_source_grounded_received_discourse', prior_author)
        current = run(service.start(user, parent))
    assert 'あなたは誘われたことは、嬉しさにはつながらず' in current['current_observation']['text']
    with monkeypatch.context() as saved:
        saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('prior saved nominal body must not regenerate'))
        assert run(service.get(user, parent)) == run(service.start(user, parent)) == current


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('position', [0, 1, 2])
def test_original_past_coordination_keeps_degree_negation_and_each_event(field, position):
    events = ('私は誘われた', '自分は頼まれた', 'わたしは褒められた')
    feelings = ['悲しかった', '怖かった', '寂しかった']
    feelings[position] = '少し嬉しくなかった'
    memo = ''.join(event + 'のに、' + feeling + '。' for event, feeling in zip(events, feelings))
    context = actual(request=begin(memo if field == 'memo' else '', memo if field == 'memo_action' else ''))
    result = context[0]
    follow = result.artifact.reception
    assert 'し、' not in follow
    predicate = '少し嬉しくなかった' if position == 2 else '少し嬉しくなく'
    assert predicate in follow and follow.endswith('のですね。')
    assert read_body(context, result.artifact.text).passed
    for old, new in [('少し', ''), ('嬉しくな', '嬉し'),
                     (predicate, '少し嬉しくないし'), ('あなたは', '友人は'),
                     ('のに、', 'ので、'), ('誘われた', '頼まれた')]:
        changed = follow.replace(old, new, 1)
        assert changed != follow
        assert not read_body(context, result.artifact.text.replace(follow, changed, 1)).passed


@pytest.mark.parametrize('same_names', [False, True])
def test_original_past_coordination_keeps_every_qualified_source_position(same_names):
    events = ('誘われた',) * 3 if same_names else ('誘われた', '頼まれた', '褒められた')
    feelings = ('少し嬉しくなかった', 'とても怖かった', '少し寂しかった')
    memo = ''.join(owner + event + 'のに、' + feeling + '。'
                   for owner, event, feeling in zip(('私は', '自分は', 'わたしは'), events, feelings))
    context = actual(request=begin(memo))
    body, follow = context[0].artifact.text, context[0].artifact.reception
    assert 'し、' not in follow
    assert all(part in follow for part in ('少し嬉しくなく', 'とても怖く', '少し寂しかった'))
    if same_names:
        assert [follow.index(prefix) for prefix in RECORD_PREFIXES] == sorted(follow.index(prefix) for prefix in RECORD_PREFIXES)
        swapped = follow.replace(RECORD_PREFIXES[1], RECORD_PREFIXES[2], 1)
        assert not read_body(context, body.replace(follow, swapped, 1)).passed
    assert read_body(context, body).passed
    # Saved additive prose remains independently readable; it is not rewritten.
    legacy = follow.replace('嬉しくなく、', '嬉しくなかったし、').replace('怖く、', '怖かったし、')
    assert legacy != follow and read_body(context, body.replace(follow, legacy, 1)).passed
    for old in ('少し嬉しくなく、', 'とても怖く、'):
        changed = follow.replace(old, '', 1)
        assert changed != follow and not read_body(context, body.replace(follow, changed, 1)).passed


@pytest.mark.parametrize('copular_first', [False, True])
def test_original_past_coordination_keeps_copular_scope_separate(copular_first):
    feelings = ('不安だった', '少し怖かった') if copular_first else ('少し怖かった', '不安だった')
    memo = ''.join(event + 'のに、' + feeling + '。'
                   for event, feeling in zip(('誘われた', '頼まれた'), feelings))
    context = actual(request=begin(memo))
    follow = context[0].artifact.reception
    assert feelings[0] + 'し、' in follow and feelings[1] + 'のですね。' in follow
    assert read_body(context, context[0].artifact.text).passed


PAST_COORDINATION_MEMO = ('褒められたのに、少し嬉しくなかった。'
                          '誘われたのに、少し悲しかった。頼まれたのに、寂しかった。')
PAST_COORDINATION_STEPS = ('今は少し苦しい。', '「少し苦しい」ではなく「少し怖い」です。',
                           '「褒められた」は誤りです。')


@pytest.mark.parametrize('steps', [1, 2, 3])
def test_original_past_coordination_preserves_answer_correction_and_withdrawal_times(steps):
    request = begin(PAST_COORDINATION_MEMO)
    for reply in PAST_COORDINATION_STEPS[:steps]:
        request = advance(request, reply)
    context = actual(request=request)
    body, follow = context[0].artifact.text, context[0].artifact.reception
    assert '少し嬉しくなかったし、' in follow
    assert '誘われたのに、少し悲しく、頼まれたのに、寂しさを感じたのですね。' in follow
    when = '回答した時点では' if steps == 1 else '先の回答時点では'
    assert when in follow
    assert ('褒められた' in body) == (steps < 3)
    assert ('少し苦しい' in body) == (steps == 1)
    assert read_body(context, body).passed
    for old, new in [(when, 'その時は'), ('少し悲しく', '少し悲しかったから'),
                     ('嬉しくなかった', '嬉しくない')]:
        changed = follow.replace(old, new, 1)
        assert changed != follow and not read_body(context, body.replace(follow, changed, 1)).passed


@pytest.mark.parametrize('legacy', [False, True])
def test_original_past_coordination_saved_body_and_updates_never_regenerate(qcase, qdb, monkeypatch, legacy):
    user, parent, _ = qcase
    service = active(monkeypatch)
    qdb.query('update public.emotions set memo=$1 where id=$2', [PAST_COORDINATION_MEMO, parent])
    author = reception._source_grounded_received_discourse

    def prior_author(*args, **kwargs):
        text = author(*args, **kwargs)
        if not text:
            return text
        return text.replace('少し嬉しくなく、', '少し嬉しくなかったし、').replace(
            '少し悲しく、', '少し悲しかったし、')

    with monkeypatch.context() as old:
        if legacy:
            old.setattr(reception, '_source_grounded_received_discourse', prior_author)
        first = current = run(service.start(user, parent))
    initial_body = current['current_observation']['text']
    assert ('少し悲しかったし、' in initial_body) == legacy
    with monkeypatch.context() as saved:
        saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved initial must not regenerate'))
        assert run(service.get(user, parent)) == run(service.start(user, parent)) == current
    for index, reply in enumerate(PAST_COORDINATION_STEPS):
        if index:
            current = run(cont(service, user, current, f'past-continue-{index}'))
        current = run(answer(service, user, current, reply, f'past-answer-{index}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        assert '誘われたのに、少し悲しく、頼まれたのに、寂しさを感じたのですね。' in current['current_observation']['text']
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved update must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current
    assert qdb.query('select memo from public.emotions where id=$1', [parent])['rows'][0]['memo'] == PAST_COORDINATION_MEMO


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('when,prefix', [('その時は', 'その時、'), ('今は', '回答した時点で、')])
@pytest.mark.parametrize('source,finite', [
    ('私は少し怖くなかったです', 'あなたは少し怖くなかった'),
    ('少し私も怖かった', 'あなたも少し怖かった'),
    ('僕には少し不安でした', 'あなたには少し不安だった'),
    ('私も少し不安です', 'あなたも少し不安だ'),
])
def test_received_answer_time_adjunct_keeps_whole_self_feeling(field, when, prefix, source, finite):
    original = '悲しかった' if field == 'memo' else '少し悲しかった'
    memo = f'誘われたのに、{original}。頼まれたのに、寂しかった。'
    request = begin(memo if field == 'memo' else '', memo if field == 'memo_action' else '')
    context = actual(request=advance(request, when + source + '。'))
    body, follow = context[0].artifact.text, context[0].artifact.reception
    delivered = finite[:-1] + 'な' if finite.endswith('だ') else finite
    assert original + 'し、' + prefix + delivered in follow
    assert '頼まれたのに、寂しさを感じた' in follow
    assert read_body(context, body).passed
    old_prefix = {'その時、': 'その時は', '回答した時点で、': '回答した時点では'}[prefix]
    legacy = follow.replace(prefix, old_prefix, 1)
    assert legacy != follow and read_body(context, body.replace(follow, legacy, 1)).passed
    changed_time = '回答した時点で、' if when == 'その時は' else 'その時、'
    mutations = [(prefix, changed_time), (prefix, '先の回答時点で、'),
                 (prefix, ''), ('あなた', '友人'),
                 (prefix + delivered, prefix + delivered.replace('少し', '', 1)),
                 (prefix + delivered, prefix + delivered.replace('あなた', 'あなたが', 1)),
                 ('のに、', 'ので、'), (prefix + delivered, '')]
    if '怖くな' in delivered:
        mutations.append(('怖くな', '怖'))
    elif delivered.endswith('かった'):
        mutations.append((delivered, delivered[:-3] + 'い'))
    else:
        mutations.append((delivered, delivered.replace('だった', 'だ')
                          if delivered.endswith('だった') else delivered[:-1] + 'だった'))
    for old, new in mutations:
        changed = follow.replace(old, new, 1)
        assert changed != follow
        assert not read_body(context, body.replace(follow, changed, 1)).passed


@pytest.mark.parametrize('position', [0, 1, 2])
def test_received_answer_time_adjunct_keeps_equal_event_source_positions(position):
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning
    request = begin(RECORD_TRIPLE_MEMO)
    for _ in range(position):
        request = advance(request, 'その時は少し重かった。')
    request = advance(request, 'その時は少し私は怖かった。')
    prepared = prepare_emlis_meaning(request)
    context = actual(request=request)
    result, plan, _, resolver, _ = context
    follow, body = result.artifact.reception, result.artifact.text
    assert 'その時、あなたは少し怖かった' in follow
    assert all(follow.count(prefix) == 1 for prefix in RECORD_PREFIXES)
    updated = prepared.checkpoint.answer_update.updates[-1]
    about = [r for r in plan.relations if r.type == 'evaluation_about_event'
             and r.to_nucleus_id in updated.changed_claim_refs]
    assert len(about) == 1
    target = next(n for n in plan.nuclei if n.nucleus_id == about[0].from_nucleus_id)
    clauses = RECORD_TRIPLE_MEMO.split('。')
    span = resolver.resolve(target.source_span_ids[0])
    assert span.raw_text == clauses[position]
    assert span.start_index == sum(len(clause) + 1 for clause in clauses[:position])
    assert read_body(context, body).passed
    changed = follow.replace(RECORD_PREFIXES[position], RECORD_PREFIXES[(position + 1) % 3], 1)
    assert not read_body(context, body.replace(follow, changed, 1)).passed


@pytest.mark.parametrize('reply', ['今は少し怖い。', '今は私は重いと思った。',
                                   '今は私は少し怖かったのです。', '今は私は不安なのだった。'])
def test_received_answer_time_adjunct_does_not_expand_other_predicates(reply):
    context = actual(request=advance(begin(MEMO), reply))
    follow, body = context[0].artifact.reception, context[0].artifact.text
    assert '回答した時点では' in follow and '回答した時点で、' not in follow
    assert read_body(context, body).passed
    changed = follow.replace('回答した時点では', '回答した時点で、', 1)
    assert not read_body(context, body.replace(follow, changed, 1)).passed


@pytest.mark.parametrize('source', ['少し私も怖くないです', 'とても私にも少し不安です',
                                    '少し私は怖くなかったです', '私にも少し不安です'])
def test_received_answer_time_adjunct_keeps_existing_unadmitted_modifier_boundary(source):
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning
    request = advance(begin(MEMO), 'その時は' + source + '。')
    prepared = prepare_emlis_meaning(request)
    assert not prepared.accepted_nuclei and prepared.checkpoint.unresolved_parts
    context = actual(request=request)
    assert context[0].artifact.reception == actual(request=begin(MEMO))[0].artifact.reception


def test_received_answer_time_adjunct_correction_keeps_prior_time_without_authors():
    request = advance(begin(MEMO), '今は私も少し不安です。')
    context = actual(request=advance(request, '「私も少し不安です」ではなく「私も少し苦しいです」です。'))
    follow, body = context[0].artifact.reception, context[0].artifact.text
    prefix, answer = '先の回答時点で、', 'あなたも少し苦しい'
    assert prefix + answer in follow and '少し不安' not in body
    assert read_body(context, body).passed
    for new in ('回答した時点で、', 'その時、', ''):
        changed = follow.replace(prefix, new, 1)
        assert not read_body(context, body.replace(follow, changed, 1)).passed
    for new in ('あなたは少し苦しい', 'あなたも苦しい', 'あなたも少し苦しかった'):
        changed = follow.replace(answer, new, 1)
        assert not read_body(context, body.replace(follow, changed, 1)).passed
    legacy = follow.replace(prefix, '先の回答時点では', 1)
    assert read_body(context, body.replace(follow, legacy, 1)).passed


@pytest.mark.parametrize('legacy', [False, True])
def test_received_answer_time_adjunct_saved_correction_withdrawal_and_old_replay(qcase, qdb, monkeypatch, legacy):
    user, parent, _ = qcase
    service = active(monkeypatch)
    qdb.query('update public.emotions set memo=$1 where id=$2', [RECORD_TRIPLE_MEMO, parent])
    first = current = run(service.start(user, parent))
    author = reception._source_grounded_received_discourse

    def prior_author(*args, **kwargs):
        text = author(*args, **kwargs)
        return text.replace('回答した時点で、', '回答した時点では') if text else text

    with monkeypatch.context() as old:
        if legacy:
            old.setattr(reception, '_source_grounded_received_discourse', prior_author)
        current = run(answer(service, user, current, '今は私も少し不安です。', 'owned-time-first'))
    expected = '回答した時点では' if legacy else '回答した時点で、'
    assert expected + 'あなたも少し不安な' in current['current_observation']['text']
    with monkeypatch.context() as saved:
        saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved answer must not regenerate'))
        assert run(service.get(user, parent)) == run(service.start(user, parent)) == current
    for index, reply in enumerate(('「私も少し不安です」ではなく「私も少し苦しいです」です。',
                                   '「私は誘われた」は誤りです。')):
        current = run(cont(service, user, current, f'owned-time-continue-{index}'))
        current = run(answer(service, user, current, reply, f'owned-time-answer-{index}'))
        body = current['current_observation']['text']
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        assert '先の回答時点で、あなたも少し苦しい' in body and '少し不安' not in body
        assert ('「私は誘われた」' in body) == (index == 0)
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved update must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current
    assert qdb.query('select memo from public.emotions where id=$1', [parent])['rows'][0]['memo'] == RECORD_TRIPLE_MEMO


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('answers', TWO_POSITIVE_PAIRS)
@pytest.mark.parametrize('old', ['嬉しくなかった', '悲しかった'])
def test_independent_past_revision_coordination_keeps_sources_and_answer_times(field, answers, old):
    memo = INITIAL_EXPLANATION_MEMOS[0][0]
    request = begin(memo if field == 'memo' else '', memo if field == 'memo_action' else '')
    for reply in (*answers, f'「{old}」ではなく「私も少し怖くなかったです」です。'):
        request = advance(request, reply)
    context = actual(request=request)
    result, plan, _, _, _ = context
    follow, body = result.artifact.reception, result.artifact.text
    revision = REVISION_INTRO + '当時、あなたも少し怖くなかった'
    assert 'し、' not in follow and revision + 'のですね。' in follow
    assert '頼まれたのに、寂しさを感じ、' in follow
    assert ('誘われたのに、悲しさを感じ、' if old == '嬉しくなかった'
            else '褒められたことは、嬉しさにはつながらず、') in follow
    assert old not in body and len(plan.response_plan.human_reception_plan.moves) == 3
    revised, = [n for n in plan.nuclei if 'thread_subject:revised_original_reaction' in n.semantic_frame.attribute_codes]
    assert revised.semantic_frame.time_scope == 'past'
    assert not any(revised.nucleus_id in (r.from_nucleus_id, r.to_nucleus_id) for r in plan.relations)
    positive = [n for n in plan.nuclei if n.source_fields == ('answer_text_private',)
                and n.semantic_frame.polarity == 'positive']
    assert len(positive) == 2
    assert {code for n in positive for code in n.semantic_frame.attribute_codes
            if code.startswith('thread_time:')} == {'thread_time:answer_time', 'thread_time:original_occasion'}
    assert read_body(context, body).passed
    legacy = follow.replace('感じ、', '感じたし、').replace('つながらず、', 'つながらなかったし、')
    assert legacy != follow and read_body(context, body.replace(follow, legacy, 1)).passed
    for before, after in [
        ('頼まれたのに、寂しさを感じ、', ''),
        ('頼まれたのに、寂しさを感じ、', '頼まれたのに、寂しさを感じたので、'),
        (REVISION_INTRO, ''), (REVISION_INTRO, '頼まれたことについて、'),
        ('当時、', '回答した時点で、'), ('当時、', '先の回答時点で、'),
        ('あなたも', 'あなたは'), ('あなたも', '友人も'),
        ('少し怖くなかった', '怖くなかった'), ('怖くなかった', '怖かった'),
        ('怖くなかった', '怖くない'), (revision + 'のですね。', ''),
        ('回答した時点では', 'その時は'),
    ]:
        changed = follow.replace(before, after, 1)
        assert changed != follow
        assert not read_body(context, body.replace(follow, changed, 1)).passed


@pytest.mark.parametrize('old', ['嬉しくなかった', '悲しかった'])
def test_independent_past_revision_coordination_keeps_corrected_copula_finite(old):
    context = actual(request=revised_original_request('私も少し不安でした', old=old))
    follow = context[0].artifact.reception
    assert follow.count('し、') == 2
    assert REVISION_INTRO + '当時、あなたも少し不安だったのですね。' in follow
    assert read_body(context, context[0].artifact.text).passed


@pytest.mark.parametrize('old', ['嬉しくなかった', '悲しかった'])
def test_independent_past_revision_coordination_keeps_original_copula_finite(old):
    memo = INITIAL_EXPLANATION_MEMOS[0][0].replace('寂しかった', '私も少し不安だった')
    request = begin(memo)
    for reply in (*TWO_POSITIVE_PAIRS[0], f'「{old}」ではなく「少し苦しかった」です。'):
        request = advance(request, reply)
    context = actual(request=request)
    follow = context[0].artifact.reception
    assert '頼まれたのに、あなたも少し不安だったし、' in follow
    assert REVISION_INTRO + '当時は少し苦しかったのですね。' in follow
    assert read_body(context, context[0].artifact.text).passed


@pytest.mark.parametrize('legacy', [False, True])
def test_independent_past_revision_coordination_saved_body_keeps_all_updates(qcase, qdb, monkeypatch, legacy):
    user, parent, _ = qcase
    service = active(monkeypatch)
    memo = INITIAL_EXPLANATION_MEMOS[0][0]
    qdb.query('update public.emotions set memo=$1 where id=$2', [memo, parent])
    first = current = run(service.start(user, parent))
    author = reception._source_grounded_received_discourse

    def prior_author(*args, **kwargs):
        text = author(*args, **kwargs)
        if text and REVISION_INTRO in text:
            return text.replace('感じ、', '感じたし、').replace('つながらず、', 'つながらなかったし、')
        return text

    with monkeypatch.context() as old:
        if legacy:
            old.setattr(reception, '_source_grounded_received_discourse', prior_author)
        for index, reply in enumerate((*TWO_POSITIVE_PAIRS[1], '「悲しかった」ではなく「私も少し怖くなかったです」です。')):
            if index:
                current = run(cont(service, user, current, f'independent-past-continue-{index}'))
            current = run(answer(service, user, current, reply, f'independent-past-answer-{index}'))
            assert current['body_state'] == 'REFINED' and current['original'] == first['original']
            with monkeypatch.context() as saved:
                saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved past revision must not regenerate'))
                assert run(service.get(user, parent)) == run(service.start(user, parent)) == current
    body = current['current_observation']['text']
    assert ('寂しさを感じたし、' in body) == legacy
    assert REVISION_INTRO + '当時、あなたも少し怖くなかったのですね。' in body
    assert '悲しかった' not in body and not current['can_continue']
    with monkeypatch.context() as saved:
        saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('final saved past revision must not regenerate'))
        assert run(service.get(user, parent)) == run(service.start(user, parent)) == current
    assert qdb.query('select memo from public.emotions where id=$1', [parent])['rows'][0]['memo'] == memo


REVISED_EXPLANATIONS = (
    ('私も少し怖くなかったのです', 'あなたも少し怖くなかったのですね'),
    ('少し重かったのです', '少し重かったのですね'),
    ('私も少し不安だったのです', 'あなたも少し不安だったのですね'),
    ('少し重かったのだ', '少し重かったのですね'),
    ('私も少し不安なのだった', 'あなたも少し不安なのでしたね'),
    ('少し重かったのだった', '少し重かったのでしたね'),
)


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('old', ['嬉しくなかった', '悲しかった'])
@pytest.mark.parametrize('source,finite', REVISED_EXPLANATIONS)
def test_independent_explanation_revision_preserves_complete_source_and_times(field, old, source, finite):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning
    memo = INITIAL_EXPLANATION_MEMOS[0][0]
    request = begin(memo if field == 'memo' else '', memo if field == 'memo_action' else '')
    answers = TWO_POSITIVE_PAIRS[old == '悲しかった']
    for reply in (*answers, f'「{old}」ではなく「{source}」です。'):
        request = advance(request, reply)
    prepared = prepare_emlis_meaning(request)
    assert not prepared.checkpoint.unresolved_parts
    context = actual(request=request)
    result, plan, _, _, _ = context
    body, follow = result.artifact.text, result.artifact.reception
    assert MeaningExperienceEngine().generate(request).artifact.text == body
    prefix = REVISION_INTRO + ('当時、' if source.startswith('私も') else '当時は')
    assert prefix + finite + '。' in follow
    assert source in result.artifact.observation and old not in body
    assert len(plan.response_plan.human_reception_plan.moves) == 3
    revised, = [n for n in plan.nuclei
                if 'thread_subject:revised_original_reaction' in n.semantic_frame.attribute_codes]
    assert revised.source_fields == ('answer_text_private',)
    assert revised.semantic_frame.time_scope == 'past'
    assert not any(revised.nucleus_id in (r.from_nucleus_id, r.to_nucleus_id) for r in plan.relations)
    assert '頼まれたのに、寂しさを感じたし、' in follow
    assert ('誘われたのに、悲しさを感じたし、' if old == '嬉しくなかった'
            else '褒められたことは、嬉しさにはつながらなかったし、') in follow
    assert read_body(context, body).passed
    mutations = [
        (prefix, ''), (REVISION_INTRO, '頼まれたことについて、'),
        ('当時、' if source.startswith('私も') else '当時は', '回答した時点では'),
        ('当時、' if source.startswith('私も') else '当時は', '先の回答時点では'),
        (finite, finite.replace('少し', '', 1)),
        (finite, '友人は' + finite),
        ('頼まれたのに、寂しさを感じたし、', ''),
        ('寂しさを感じたし、', '寂しさを感じたので、'),
        (prefix + finite + '。', ''),
        ('回答した時点では', 'その時は'),
    ]
    if 'あなたも' in finite:
        mutations += [(finite, finite.replace('あなたも', 'あなたは', 1))]
    for before, after in [('怖くなかった', '怖かった'), ('怖くなかった', '怖くない'),
                          ('重かった', '重い'), ('不安だった', '不安な')]:
        if before in finite:
            mutations += [(finite, finite.replace(before, after, 1))]
    ending = 'のでしたね' if source.endswith('のだった') else 'のですね'
    mutations += [(finite, finite.replace(ending, 'のですね' if ending == 'のでしたね' else 'のでしたね', 1)),
                  (finite, finite.replace(ending, 'ですね', 1))]
    for before, after in mutations:
        changed = follow.replace(before, after, 1)
        assert changed != follow
        assert not read_body(context, body.replace(follow, changed, 1)).passed
    if source.endswith('のだった'):
        legacy = follow.replace('のでしたね', 'のだったのですね', 1)
        assert read_body(context, body.replace(follow, legacy, 1)).passed


@pytest.mark.parametrize('source,legacy', [
    ('私も少し怖くなかったのです', False),
    ('私も少し不安なのだった', False),
    ('私も少し不安なのだった', True),
])
def test_independent_explanation_revision_saved_body_and_legacy_replay(qcase, qdb, monkeypatch, source, legacy):
    user, parent, _ = qcase
    service = active(monkeypatch)
    memo = INITIAL_EXPLANATION_MEMOS[0][0]
    qdb.query('update public.emotions set memo=$1 where id=$2', [memo, parent])
    first = current = run(service.start(user, parent))
    author = reception._source_grounded_received_discourse

    def prior_author(*args, **kwargs):
        text = author(*args, **kwargs)
        return text.replace('のでしたね', 'のだったのですね') if text else text

    with monkeypatch.context() as old:
        if legacy:
            old.setattr(reception, '_source_grounded_received_discourse', prior_author)
        for index, reply in enumerate((*TWO_POSITIVE_PAIRS[1], f'「悲しかった」ではなく「{source}」です。')):
            if index:
                current = run(cont(service, user, current, f'explanation-continue-{index}'))
            current = run(answer(service, user, current, reply, f'explanation-answer-{index}'))
            assert current['body_state'] == 'REFINED' and current['original'] == first['original']
            with monkeypatch.context() as saved:
                saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved explanation must not regenerate'))
                assert run(service.get(user, parent)) == run(service.start(user, parent)) == current
    assert source in current['current_observation']['text']
    assert '悲しかった' not in current['current_observation']['text']
    assert ('のだったのですね' in current['current_observation']['text']) == legacy
    assert not current['can_continue']
    with monkeypatch.context() as saved:
        saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved legacy explanation must not regenerate'))
        assert run(service.get(user, parent)) == run(service.start(user, parent)) == current
    assert qdb.query('select memo from public.emotions where id=$1', [parent])['rows'][0]['memo'] == memo


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('link', ['のに', 'けど', 'けれど', 'けれども'])
@pytest.mark.parametrize('reply', ['今は嬉しい。', '今は少し嬉しい。'])
def test_finite_original_temporal_pair_keeps_same_name_sources_and_times(field, link, reply):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    memo = RECORD_TRIPLE_MEMO.replace('のに', link)
    request = advance(begin(memo if field == 'memo' else '', memo if field == 'memo_action' else ''), reply)
    context = actual(request=request)
    result, plan, _, resolver, selected = context
    body, follow = result.artifact.text, result.artifact.reception
    assert MeaningExperienceEngine().generate(request).artifact.text == body
    assert follow.startswith('当時、' + RECORD_PREFIXES[0] + 'あなたは誘われた' + link + '、嬉しくなく、')
    assert ('回答した時点では' + reply[2:-1] + 'のですね。') in follow
    assert all(follow.count(prefix) == 1 for prefix in RECORD_PREFIXES)
    assert '悲しさ' in follow and '寂しさ' in follow
    assert len(plan.response_plan.human_reception_plan.moves) == 3
    assert follow.count('。') == 2
    assert read_body(context, body).passed
    pair = plan.response_plan.human_reception_plan.moves[:2]
    raw = follow.split('。')[0] + '。'
    first, second = gate.read_detached_feeling_pair(raw, pair, plan, resolver, selected)
    boundary = raw.encode().index('、回答した時点では'.encode())
    assert all(0 <= a < b <= boundary for a, b, _ in first)
    assert all(boundary < a < b <= len(raw.encode()) for a, b, _ in second)
    assert {source.decode() for _, _, source in first} == {'私は誘われた', '嬉しくなかった'}
    assert {source.decode() for _, _, source in second} == {reply[2:-1]}
    assert next(raw.encode()[a:b].decode() for a, b, source in first
                if source.decode() == '嬉しくなかった') == '嬉しくなく'
    target = next(n for n in plan.nuclei if n.nucleus_id == pair[0].target_nucleus_ids[0])
    span = resolver.resolve(target.source_span_ids[0])
    assert span.source_field == field and span.start_index == 0
    mutations = [
        ('当時、', ''), ('当時、', '今、'),
        (RECORD_PREFIXES[0], RECORD_PREFIXES[1]),
        ('あなたは誘われた', '友人は誘われた'),
        ('あなたは誘われた', 'あなたが誘われた'),
        ('あなたは誘われた', 'あなたは頼まれた'),
        ('嬉しくなく、', '嬉しく、'), ('嬉しくなく、', '嬉しくない、'),
        ('嬉しくなく、', ''), ('嬉しくなく、', '嬉しくなかったので、'),
        ('誘われた' + link + '、', '誘われたので、'),
        ('回答した時点では', 'その時は'), ('回答した時点では', '先の回答時点では'),
        ('回答した時点では', '回答した時点でも'),
        ('嬉しいのですね', '嬉しかったのですね'),
        ('嬉しいのですね', '嬉しくないのですね'),
        ('回答した時点では' + reply[2:-1], '回答した時点では友人は' + reply[2:-1]),
    ]
    if '少し' in reply:
        mutations.append(('少し嬉しい', '嬉しい'))
    for old, new in mutations:
        changed = follow.replace(old, new, 1)
        assert changed != follow
        assert not read_body(context, body.replace(follow, changed, 1)).passed
    changed = follow.replace(raw, '', 1)
    assert not read_body(context, body.replace(follow, changed, 1)).passed


def test_finite_original_temporal_pair_requires_actual_source_frames_and_about():
    context = actual(request=advance(begin(RECORD_TRIPLE_MEMO), '今は嬉しい。'))
    result, plan, _, resolver, selected = context
    pair = plan.response_plan.human_reception_plan.moves[:2]
    raw = result.artifact.reception.split('。')[0] + '。'
    for source_role, field, value in [('original', 'actor', 'other_person'),
        ('original', 'time_scope', 'present'), ('original', 'polarity', 'positive'),
        ('answer', 'actor', 'other_person'), ('answer', 'time_scope', 'past'),
        ('answer', 'polarity', 'negative')]:
        nid = pair[0].support_nucleus_ids[0] if source_role == 'original' else pair[1].target_nucleus_ids[0]
        changed = replace(plan, nuclei=tuple(replace(n, semantic_frame=replace(n.semantic_frame, **{field:value}))
            if n.nucleus_id == nid else n for n in plan.nuclei))
        assert gate.read_detached_feeling_pair(raw, pair, changed, resolver, selected) is None
    about, = [r for r in plan.relations if r.type == 'evaluation_about_event']
    other = next(n for n in plan.nuclei if n.kind == 'event' and n.nucleus_id != about.from_nucleus_id)
    changed = replace(plan, relations=tuple(replace(r, from_nucleus_id=other.nucleus_id)
        if r == about else r for r in plan.relations))
    assert gate.read_detached_feeling_pair(raw, pair, changed, resolver, selected) is None


@pytest.mark.parametrize('remaining', [
    ('その時は楽しかった。', '「嬉しくなかった」ではなく「少し苦しかった」です。'),
    ('「嬉しい」ではなく「少し楽しい」です。', '「少し楽しい」は誤りです。'),
    ('「嬉しい」ではなく「少し楽しい」です。', '「少し楽しい」ではなく「とても楽しい」です。'),
])
def test_finite_original_temporal_pair_saved_progress_correction_and_withdrawal(qcase, qdb, monkeypatch, remaining):
    user, parent, _ = qcase
    service = active(monkeypatch)
    qdb.query('update public.emotions set memo=$1 where id=$2', [RECORD_TRIPLE_MEMO, parent])
    first = current = run(service.start(user, parent))
    for index, reply in enumerate(('今は嬉しい。', *remaining)):
        if index:
            current = run(cont(service, user, current, f'finite-pair-continue-{index}'))
        current = run(answer(service, user, current, reply, f'finite-pair-answer-{index}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        body = current['current_observation']['text']
        if not index:
            assert '当時、' + RECORD_PREFIXES[0] + 'あなたは誘われたのに、嬉しくなく、回答した時点では嬉しい' in body
        elif '楽しい' in reply and '誤り' not in reply:
            assert '先の回答時点では' in body
        if index == 2:
            if '少し楽しい」は誤り' in reply:
                assert '楽しい' not in body and '嬉しくなかった' in body
            elif '苦しかった' in reply:
                assert '少し苦しかった' in body and '嬉しくなかった' not in body
                assert '回答した時点では嬉しい' in body and 'その時は楽しかった' in body
            else:
                assert 'とても楽しい' in body and '少し楽しい' not in body
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved finite pair must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current
    assert not current['can_continue']
    assert qdb.query('select memo from public.emotions where id=$1', [parent])['rows'][0]['memo'] == RECORD_TRIPLE_MEMO


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('memo', [EXACT_RECORD_MEMO, RECORD_TRIPLE_MEMO,
                                 '誘われたのに、嬉しくなかった。誘われたのに、悲しかった。'])
@pytest.mark.parametrize('answers', TWO_POSITIVE_PAIRS)
def test_same_name_positive_answers_keep_all_originals_and_each_written_target(field, memo, answers):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning
    request = begin(memo if field == 'memo' else '', memo if field == 'memo_action' else '')
    for reply in answers:
        request = advance(request, reply)
    prepared = prepare_emlis_meaning(request)
    context = actual(request=request)
    result, plan, _, resolver, selected = context
    body, follow = result.artifact.text, result.artifact.reception
    assert MeaningExperienceEngine().generate(request).artifact.text == body
    assert not prepared.checkpoint.unresolved_parts
    assert len(plan.response_plan.human_reception_plan.moves) == 3
    assert '嬉し' in follow and '悲しさ' in follow
    count = memo.count('。')
    if count == 3:
        assert '寂しさ' in follow
    prefixes = RECORD_PREFIXES if count == 3 else (RECORD_PREFIXES[0], RECORD_PREFIXES[2])
    event = 'あなたは誘われた' if memo == RECORD_TRIPLE_MEMO else '誘われた'
    answer_moves = [m for m in plan.response_plan.human_reception_plan.moves
                    if m.reception_act == 'recognize_lived_change']
    assert len(answer_moves) == 2
    for position, (move, reply) in enumerate(zip(answer_moves, answers)):
        answer_nid, = move.target_nucleus_ids
        about, = [r for r in plan.relations if r.type == 'evaluation_about_event'
                  and r.to_nucleus_id == answer_nid]
        original = next(n for n in plan.nuclei if n.nucleus_id == about.from_nucleus_id)
        span = resolver.resolve(original.source_span_ids[0])
        assert span.source_field == field
        clauses = memo.split('。')
        assert span.start_index == sum(len(c) + 1 for c in clauses[:position])
        when = '回答した時点では' if reply.startswith('今は') else 'その時は'
        feeling = reply[2:-1] if reply.startswith('今は') else reply[4:-1]
        clause = prefixes[position] + event + 'ことについて、' + when + feeling + 'のですね。'
        assert clause in follow
        proof = gate._read_answer_feeling_discourse(clause, move, plan, resolver, selected)
        assert proof is not None
        assert next(clause.encode()[a:b].decode() for a, b, source in proof
                    if source.decode() == clauses[position].split('のに')[0]) == event
        wrong = clause.replace(prefixes[position], prefixes[(position + 1) % len(prefixes)], 1)
        assert not read_body(context, body.replace(clause, wrong, 1)).passed
        assert not read_body(context, body.replace(clause, '', 1)).passed
        for old, new in [(when, '先の回答時点では'), (feeling, '嬉しくない'),
                         (feeling, '友人は' + feeling), ('ことについて、', 'ことが原因で、')]:
            changed = clause.replace(old, new, 1)
            assert changed != clause
            assert not read_body(context, body.replace(clause, changed, 1)).passed
    assert read_body(context, body).passed
    # Old unqualified saved answers remain readable; current prose names
    # each written target. Qualification must never alter the event proof.
    legacy = follow
    for prefix in prefixes:
        legacy = legacy.replace(prefix + event + 'ことについて、', event + 'ことについて、')
    assert legacy != follow and read_body(context, body.replace(follow, legacy, 1)).passed


@pytest.fixture(scope='module')
def same_name_positive_three_context():
    request = begin(EXACT_RECORD_MEMO)
    for reply in (*TWO_POSITIVE_PAIRS[0], '今は私も少し楽しいです。'):
        request = advance(request, reply)
    return actual(request=request)


@pytest.mark.parametrize('memo', [EXACT_RECORD_MEMO, RECORD_TRIPLE_MEMO])
@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('third', ['今は私も少し楽しいです。', 'その時は私は少し嬉しかったです。'])
def test_same_name_positive_group_retains_three_answers_and_originals(memo, field, third):
    request = begin(memo if field == 'memo' else '', memo if field == 'memo_action' else '')
    for reply in (*TWO_POSITIVE_PAIRS[0], third):
        request = advance(request, reply)
    context = actual(request=request)
    result, plan, _, resolver, selected = context
    follow = result.artifact.reception
    assert len(plan.response_plan.human_reception_plan.moves) == 3
    assert all(token in follow for token in ('嬉し', '悲しさ', '寂しさ', '回答した時点では嬉しい', 'その時は楽しかった'))
    assert all(follow.count(prefix) == 2 for prefix in RECORD_PREFIXES)
    expected = '回答した時点ではあなたも少し楽しい' if third.startswith('今は') else 'その時はあなたは少し嬉しかった'
    assert expected in follow
    with patch.object(reception, 'source_grounded_thread_answer_group', side_effect=AssertionError('no group author')):
        raw, proof = split_positive_answer_proof(context)
        assert proof is not None and len(proof) == 6
        event = 'あなたは誘われた' if memo == RECORD_TRIPLE_MEMO else '誘われた'
        assert [raw.encode()[a:b].decode() for a, b, _ in proof][::2] == [event] * 3
    assert read_body(context, result.artifact.text).passed
    legacy = raw
    if raw.startswith(event + 'ことについて、' + RECORD_PREFIXES[0]):
        legacy = raw[len(event + 'ことについて、'):]
        for prefix in RECORD_PREFIXES[:2]:
            legacy = legacy.replace(prefix, prefix + event + 'ことについて、', 1)
    assert read_body(context, result.artifact.text.replace(raw, legacy, 1)).passed
    for old, new in [(RECORD_PREFIXES[0], RECORD_PREFIXES[2]),
        (RECORD_PREFIXES[1], RECORD_PREFIXES[0]), (RECORD_PREFIXES[2], RECORD_PREFIXES[1]),
        ('回答した時点では嬉しい', 'その時は嬉しい'), ('嬉しいし、', '嬉しいので、'),
        ('その時は楽しかった', 'その時は楽しくなかった'), ('少し', ''),
        ('あなたも' if third.startswith('今は') else 'あなたは', '相手は')]:
        changed = raw.replace(old, new, 1)
        assert changed != raw and not read_body(context, result.artifact.text.replace(raw, changed, 1)).passed
    for position in range(3):
        first, last, empty = raw.split('。')
        assert not empty
        clauses = first.removesuffix('のですね').split('し、')
        assert len(clauses) == 2
        changed = (first + '。' if position == 2 else
            'し、'.join(clauses[:position] + clauses[position + 1:]) + 'のですね。' + last + '。')
        assert not read_body(context, result.artifact.text.replace(raw, changed, 1)).passed


@pytest.mark.parametrize('mutation', ['missing', 'duplicate', 'same_event', 'wrong_proof', 'unknown',
    'source_range', 'range_value', 'source_order', 'source_link', 'relation_source', 'answer_time', 'event_kind'])
def test_same_name_positive_occurrence_proof_keeps_existing_rejection_guards(same_name_positive_three_context, mutation):
    import emlis_ai_grounded_observation_plan as gp
    result, plan, _, resolver, selected = same_name_positive_three_context
    move, = [m for m in plan.response_plan.human_reception_plan.moves if m.reception_act == 'recognize_lived_change' and len(m.target_nucleus_ids) == 2]
    raw = result.artifact.reception.split('。')[1] + '。'
    assert gp._thread_retained_reaction_groups(plan.nuclei, plan.relations)
    assert gate._read_positive_answer_group_discourse(raw, move, plan, resolver, selected) is not None
    links = [r for r in plan.relations if r.type == 'evaluation_about_event']
    first, second = links[:2]
    nuclei, relations, coverage = plan.nuclei, plan.relations, plan.coverage_requirements
    if mutation == 'missing':
        relations = tuple(r for r in relations if r != first)
    elif mutation == 'duplicate':
        relations = (*relations, replace(first, relation_id='duplicate-about'))
        coverage = replace(coverage, required_relation_ids=(*coverage.required_relation_ids, 'duplicate-about'))
    elif mutation == 'same_event':
        relations = tuple(replace(r, from_nucleus_id=first.from_nucleus_id) if r == second else r for r in relations)
    elif mutation == 'relation_source':
        relations = tuple(replace(r, source_span_ids=(*r.source_span_ids, r.source_span_ids[0]))
                          if r == first else r for r in relations)
    elif mutation == 'answer_time':
        nuclei = tuple(replace(n, semantic_frame=replace(n.semantic_frame, attribute_codes=tuple(
            'thread_time:original_occasion' if c == 'thread_time:answer_time' else c
            for c in n.semantic_frame.attribute_codes))) if n.nucleus_id == first.to_nucleus_id else n for n in nuclei)
    elif mutation in {'source_range', 'range_value', 'source_order', 'source_link', 'event_kind'}:
        other = next(n for n in nuclei if n.nucleus_id == second.from_nucleus_id)
        changed = []
        for n in nuclei:
            if n.nucleus_id == first.from_nucleus_id:
                if mutation == 'source_order':
                    n = replace(n, source_span_ids=other.source_span_ids)
                elif mutation == 'event_kind':
                    n = replace(n, semantic_frame=replace(n.semantic_frame, predicate_kind='state'))
                else:
                    codes = tuple(c for c in n.semantic_frame.attribute_codes
                                  if mutation != 'source_range' or not c.startswith('source_fragment_scalar_range:'))
                    codes = tuple('source_fragment_scalar_range:0:999' if mutation == 'range_value'
                        and c.startswith('source_fragment_scalar_range:') else 'source_received_event_link:kedo'
                        if mutation == 'source_link' and c.startswith('source_received_event_link:') else c for c in codes)
                    n = replace(n, semantic_frame=replace(n.semantic_frame, attribute_codes=codes))
            changed.append(n)
        nuclei = tuple(changed)
    else:
        nuclei = tuple(replace(n, kind='state', semantic_frame=replace(n.semantic_frame,
            predicate_kind='state', modality='uncertain')) if mutation == 'unknown' and n.nucleus_id == first.to_nucleus_id
            else replace(n, semantic_frame=replace(n.semantic_frame, attribute_codes=tuple(
                'thread_subject:distinct_source_occurrence:s999' if c.startswith('thread_subject:distinct_source_occurrence:') else c
                for c in n.semantic_frame.attribute_codes))) if mutation == 'wrong_proof' and n.nucleus_id == first.to_nucleus_id
            else n for n in nuclei)
    changed = replace(plan, nuclei=nuclei, relations=relations, coverage_requirements=coverage)
    assert not gp._thread_retained_reaction_groups(nuclei, relations)
    if mutation in {'source_range', 'range_value'}:
        with pytest.raises(reception.GroundedHumanReceptionSurfaceError, match='typed_reception_source_fragment_contract_invalid'):
            gate._read_positive_answer_group_discourse(raw, move, changed, resolver, selected)
    else:
        assert gate._read_positive_answer_group_discourse(raw, move, changed, resolver, selected) is None


@pytest.mark.parametrize('last', ['今は少し楽しい。', '「嬉しい」ではなく「私も少し楽しいです」です。',
                                 '「嬉しい」は誤りです。', '「悲しかった」ではなく「少し苦しかった」です。'])
def test_same_name_positive_saved_add_revision_withdrawal_and_replay(qcase, qdb, monkeypatch, last):
    user, parent, _ = qcase
    service = active(monkeypatch)
    qdb.query('update public.emotions set memo=$1 where id=$2', [EXACT_RECORD_MEMO, parent])
    first = current = run(service.start(user, parent))
    for index, reply in enumerate((*TWO_POSITIVE_PAIRS[0], last)):
        if index:
            current = run(cont(service, user, current, f'same-positive-continue-{index}'))
        current = run(answer(service, user, current, reply, f'same-positive-answer-{index}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        body = current['current_observation']['text']
        if index == 1:
            assert all(s in body for s in ('嬉しさ', '悲しさ', '寂しさ', '回答した時点では嬉しい', 'その時は楽しかった'))
        if index == 2:
            assert 'その時は楽しかった' in body
            if '誤り' in reply:
                assert '回答した時点では嬉しい' not in body and '嬉しくなかった' in body
            elif '私も' in reply:
                assert '先の回答時点ではあなたも少し楽しい' in body
            elif '苦しかった' in reply:
                assert '悲しかった' not in body and '少し苦しかった' in body
            else:
                assert '誘われたことについて、' + RECORD_PREFIXES[0] in body
                assert RECORD_PREFIXES[2] + '誘われたことについて、回答した時点では少し楽しい' in body
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved positive occurrences must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current
    assert not current['can_continue']
    assert qdb.query('select memo from public.emotions where id=$1', [parent])['rows'][0]['memo'] == EXACT_RECORD_MEMO


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('answers', [('今は嬉しい。', 'その時は少し苦しかった。'),
                                    ('その時は少し重かった。', '今は楽しい。')])
def test_same_name_positive_and_negative_answers_keep_separate_sources(field, answers):
    request = begin(EXACT_RECORD_MEMO if field == 'memo' else '', EXACT_RECORD_MEMO if field == 'memo_action' else '')
    for reply in answers:
        request = advance(request, reply)
    context = actual(request=request)
    follow = context[0].artifact.reception
    assert all(value in follow for value in ('嬉し', '悲し', '寂し'))
    for reply in answers:
        when, feeling = ('回答した時点では', reply[2:-1]) if reply.startswith('今は') else ('その時は', reply[4:-1])
        assert when + feeling in follow
        altered = follow.replace(when + feeling, '先の回答時点では' + feeling, 1)
        assert not read_body(context, context[0].artifact.text.replace(follow, altered, 1)).passed
    assert read_body(context, context[0].artifact.text).passed


@pytest.mark.parametrize('memo', [EXACT_RECORD_MEMO, RECORD_TRIPLE_MEMO])
@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('third,finite', [
    ('今は少し安心です。', '回答した時点では少し安心な'),
    ('その時は私も幸せでした。', 'その時はあなたも幸せだった'),
    ('今は少し平穏だ。', '回答した時点では少し平穏な'),
])
def test_nominal_positive_answer_keeps_originals_and_three_answer_sources(memo, field, third, finite):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning
    request = begin(memo if field == 'memo' else '', memo if field == 'memo_action' else '')
    for reply in (*TWO_POSITIVE_PAIRS[0], third):
        request = advance(request, reply)
    prepared = prepare_emlis_meaning(request)
    assert not prepared.checkpoint.unresolved_parts
    answer_nucleus, = prepared.accepted_nuclei
    frame = answer_nucleus.semantic_frame
    assert (answer_nucleus.kind, frame.predicate_kind, frame.modality, frame.polarity) == (
        'reaction', 'feeling', 'feeling', 'positive')
    assert 'operator:feeling' in frame.attribute_codes
    context = actual(request=request)
    result, plan, _, resolver, selected = context
    body, follow = result.artifact.text, result.artifact.reception
    assert MeaningExperienceEngine().generate(request).artifact.text == body
    assert all(s in follow for s in ('嬉し', '悲しさ', '寂しさ',
        '回答した時点では嬉しい', 'その時は楽しかった', finite + 'のですね。'))
    assert all(follow.count(prefix) == 2 for prefix in RECORD_PREFIXES)
    assert len(plan.response_plan.human_reception_plan.moves) == 3
    with patch.object(reception, 'source_grounded_thread_answer_group', side_effect=AssertionError('no group author')):
        raw, proof = split_positive_answer_proof(context)
    assert proof is not None and len(proof) == 6
    event = 'あなたは誘われた' if memo == RECORD_TRIPLE_MEMO else '誘われた'
    assert [raw.encode()[a:b].decode() for a, b, _ in proof][::2] == [event] * 3
    assert proof[-1][2].decode() == third.removesuffix('。').removeprefix('今は').removeprefix('その時は')
    assert read_body(context, body).passed
    for old, new in [(RECORD_PREFIXES[2], RECORD_PREFIXES[0]), (finite, 'その時は不安だった'),
                     ('ことについて、', 'ことが原因で、'), ('その時は楽しかった', '回答した時点では楽しかった')]:
        changed = raw.replace(old, new, 1)
        assert changed != raw and not read_body(context, body.replace(raw, changed, 1)).passed
    if '少し' in finite:
        assert not read_body(context, body.replace(raw, raw.replace('少し', '', 1), 1)).passed
    if 'あなたも' in finite:
        assert not read_body(context, body.replace(raw, raw.replace('あなたも', '相手は', 1), 1)).passed
    for position in range(3):
        first, last, empty = raw.split('。')
        assert not empty
        clauses = first.removesuffix('のですね').split('し、')
        assert len(clauses) == 2
        changed = (first + '。' if position == 2 else
            'し、'.join(clauses[:position] + clauses[position + 1:]) + 'のですね。' + last + '。')
        assert not read_body(context, body.replace(raw, changed, 1)).passed


@pytest.mark.parametrize('position', [0, 1, 2])
@pytest.mark.parametrize('source', ['少し安心です', '私も少し幸せだ', '少し平穏でした'])
def test_nominal_positive_answer_each_group_position_keeps_copula_and_time(position, source):
    replies = ['今は嬉しい。', 'その時は楽しかった。']
    replies.insert(position, '今は' + source + '。')
    request = begin(EXACT_RECORD_MEMO)
    for reply in replies:
        request = advance(request, reply)
    context = actual(request=request)
    body, follow = context[0].artifact.text, context[0].artifact.reception
    assert all(s in follow for s in ('嬉し', '悲しさ', '寂しさ', '嬉しい', '楽しかった'))
    visible = source.replace('私も', 'あなたも')
    visible = (visible[:-3] + 'だった' if source.endswith('でした') else
               visible[:-2] + 'だ' if source.endswith('です') else visible)
    ending = visible[:-1] + 'な' if position > 0 and visible.endswith('だ') else visible
    expected = '回答した時点では' + ending + ('のですね。' if position > 0 else 'し、')
    assert expected in follow
    assert read_body(context, body).passed
    for changed in [expected.replace('回答した時点では', 'その時は'),
                    expected.replace('少し', ''),
                    expected.replace('だった', 'な') if 'だった' in expected else expected.replace('だし、', 'なし、')
                    if position == 0 else expected.replace('なのですね', 'だったのですね')]:
        assert changed != expected
        assert not read_body(context, body.replace(expected, changed, 1)).passed


@pytest.mark.parametrize('last,retained,removed', [
    ('今は少し平穏です。', '回答した時点では少し平穏', None),
    ('「少し安心です」ではなく「私も少し幸せです」です。', '先の回答時点ではあなたも少し幸せ', '少し安心'),
    ('「少し安心です」は誤りです。', 'その時は楽しかった', '少し安心'),
])
def test_nominal_positive_answer_saved_add_revision_withdrawal(qcase, qdb, monkeypatch, last, retained, removed):
    user, parent, _ = qcase
    service = active(monkeypatch)
    qdb.query('update public.emotions set memo=$1 where id=$2', [EXACT_RECORD_MEMO, parent])
    first = current = run(service.start(user, parent))
    for index, reply in enumerate(('今は少し安心です。', 'その時は楽しかった。', last)):
        if index:
            current = run(cont(service, user, current, f'nominal-continue-{index}'))
        current = run(answer(service, user, current, reply, f'nominal-answer-{index}'))
        assert current['body_state'] == 'REFINED'
        assert current['original'] == first['original']
        follow = current['current_observation']['text'].split('Emlisから：', 1)[1]
        assert all(s in follow for s in ('嬉し', '悲しさ', '寂しさ'))
        if index:
            assert 'その時は楽しかった' in follow
        if index == 2:
            assert retained in follow
            if removed:
                assert removed not in current['current_observation']['text']
        with monkeypatch.context() as stopped:
            stopped.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved nominal read must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current
    assert qdb.query('select memo from public.emotions where id=$1', [parent])['rows'][0]['memo'] == EXACT_RECORD_MEMO


def test_nominal_positive_answer_survives_its_event_withdrawal_without_reviving_it():
    request = advance(advance(begin(), '今は少し安心です。'), '「褒められた」は誤りです。')
    context = actual(request=request)
    body = context[0].artifact.text
    assert '褒められた' not in body
    assert '回答した時点では少し安心なのですね。' in body
    assert '誘われた' in body and '頼まれた' in body
    assert read_body(context, body).passed
    for old, new in [('少し安心な', '少し安心だった'), ('少し安心', '安心'),
                     ('回答した時点では', 'その時は')]:
        changed = body.replace(old, new, 1)
        assert changed != body and not read_body(context, changed).passed


@pytest.mark.parametrize('reply,polarity', [
    ('今は達成です。', None), ('今は安心が大切です。', None),
    ('今は友人は安心です。', None), ('今は安心なら嬉しい。', None),
    ('今は「安心です」と言われた。', None), ('今は安心かもしれない。', None),
    ('今はとても安心です。', None), ('今はあなたは安心です。', None),
    ('今は安心ではない。', 'negative'), ('今は安心した。', 'positive'),
    ('今は少し私は安心です。', 'positive'), ('今は安心を求めていた。', 'positive'),
])
def test_nominal_positive_answer_keeps_existing_nonfeeling_and_unresolved_boundaries(reply, polarity):
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning
    prepared = prepare_emlis_meaning(advance(begin(), reply))
    if polarity is None:
        assert not prepared.accepted_nuclei and prepared.checkpoint.unresolved_parts
    else:
        nucleus, = prepared.accepted_nuclei
        frame = nucleus.semantic_frame
        assert (nucleus.kind, frame.predicate_kind, frame.modality, frame.polarity) == (
            'value', 'value', 'fact', polarity)
        assert 'operator:feeling' not in frame.attribute_codes


@pytest.mark.parametrize('memo', [EXACT_RECORD_MEMO, RECORD_TRIPLE_MEMO])
@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('third,visible,polarity', [
    ('今は安心ではない。', '回答した時点では安心ではない', 'negative'),
    ('その時は私も安心ではなかった。', 'その時はあなたも安心ではなかった', 'negative'),
    ('今は少し私は安心です。', '回答した時点ではあなたは少し安心な', 'positive'),
    ('その時は少し私は幸せでした。', 'その時はあなたは少し幸せだった', 'positive'),
])
def test_nominal_negation_and_medial_owner_keep_all_sources(memo, field, third, visible, polarity):
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning
    req = begin(memo if field == 'memo' else '', memo if field == 'memo_action' else '')
    for reply in (*TWO_POSITIVE_PAIRS[0], third):
        req = advance(req, reply)
    prepared = prepare_emlis_meaning(req)
    assert not prepared.checkpoint.unresolved_parts
    nucleus, = prepared.accepted_nuclei
    frame = nucleus.semantic_frame
    assert (nucleus.kind, frame.predicate_kind, frame.modality, frame.polarity) == (
        'reaction', 'feeling', 'feeling', polarity)
    assert 'operator:feeling' in frame.attribute_codes
    context = actual(request=req)
    result, plan, _, _, _ = context
    body, follow = result.artifact.text, result.artifact.reception
    assert all(value in follow for value in ('嬉し', '悲し', '寂し',
        '回答した時点では嬉しい', 'その時は楽しかった', visible + 'のですね。'))
    assert all(prefix in follow for prefix in RECORD_PREFIXES)
    assert '不安' not in body
    retained = {nid for move in plan.response_plan.human_reception_plan.moves
                for nid in (*move.target_nucleus_ids, *move.support_nucleus_ids)}
    assert {'answer:s7', 'answer:s8', 'answer:s9'} <= retained
    assert read_body(context, body).passed
    changes = [(visible, ''), ('その時は楽しかった', ''),
               (RECORD_PREFIXES[2], RECORD_PREFIXES[0]),
               (visible, visible.replace('その時は', '回答した時点では') if third.startswith('その時は')
                else visible.replace('回答した時点では', 'その時は'))]
    if 'ではなかった' in visible:
        changes.extend([(visible, visible.replace('ではなかった', 'ではない')),
                        (visible, visible.replace('ではなかった', 'だった'))])
    elif 'ではない' in visible:
        changes.extend([(visible, visible.replace('ではない', 'な')),
                        (visible, visible.replace('安心ではない', '不安な'))])
    else:
        changes.append((visible, visible.replace('だった', 'な') if 'だった' in visible
                        else visible.replace('安心な', '安心ではない')))
    if '少し' in visible:
        changes.append((visible, visible.replace('少し', '')))
    if 'あなた' in visible:
        changes.append((visible, visible.replace('あなたは', 'あなたも') if 'あなたは' in visible
                        else visible.replace('あなたも', 'あなたは')))
    for old, new in changes:
        changed = body.replace(follow, follow.replace(old, new, 1), 1)
        assert changed != body and not read_body(context, changed).passed


@pytest.mark.parametrize('position', [0, 1, 2])
@pytest.mark.parametrize('source,visible', [
    ('少し私は安心です', 'あなたは少し安心'),
    ('少し私は安心ではない', 'あなたは少し安心ではない'),
])
def test_nominal_negation_and_medial_owner_each_answer_position(position, source, visible):
    replies = list(TWO_POSITIVE_PAIRS[0])
    replies.insert(position, '今は' + source + '。')
    req = begin(EXACT_RECORD_MEMO)
    for reply in replies:
        req = advance(req, reply)
    context = actual(request=req)
    body, follow = context[0].artifact.text, context[0].artifact.reception
    assert all(value in follow for value in ('嬉し', '悲し', '寂し',
        '回答した時点では嬉しい', 'その時は楽しかった', visible))
    assert '私' not in follow and '不安' not in follow
    assert read_body(context, body).passed
    for old, new in [(visible, visible.replace('あなたは', 'あなたも')),
                     (visible, visible.replace('少し', '')),
                     (visible, visible.replace('ではない', 'ではなかった') if 'ではない' in visible
                      else visible + 'ではない')]:
        changed = body.replace(follow, follow.replace(old, new, 1), 1)
        assert changed != body and not read_body(context, changed).passed


def test_nominal_negation_and_medial_owner_negative_group_reads_actual_sources():
    replies = ('今は安心ではない。', 'その時は私も幸せではなかった。', '今は少し私は平穏ではない。')
    req = begin(EXACT_RECORD_MEMO)
    for reply in replies:
        req = advance(req, reply)
    context = actual(request=req)
    result, plan, _, resolver, selected = context
    body, follow = result.artifact.text, result.artifact.reception
    assert all(value in follow for value in ('嬉し', '悲し', '寂し',
        '回答した時点では安心ではない', 'その時はあなたも幸せではなかった',
        '回答した時点ではあなたは少し平穏ではない'))
    moves = plan.response_plan.human_reception_plan.moves
    sentences = [part + '。' for part in follow.removesuffix('。').split('。')]
    sources = ['安心ではない', '私も幸せではなかった', '少し私は平穏ではない']
    assert len(moves) == len(sentences) == 3
    with patch.object(reception, '_source_grounded_received_discourse', side_effect=AssertionError('no received author')):
        for i, (raw, move, source) in enumerate(zip(sentences, moves, sources, strict=True)):
            assert f'answer:s{i + 7}' in move.support_nucleus_ids
            proof = gate.read_received_discourse(raw, move, plan, resolver, selected)
            assert proof is not None
            original = ('嬉しくなかった', '悲しかった', '寂しかった')[i]
            assert raw.encode()[proof[0][0]:proof[0][1]].decode() == original
            assert proof[0][2].decode() == original
            assert proof[-1][2].decode() == source
    assert read_body(context, body).passed
    for old, new in [('安心ではない', '安心ではなかった'), ('幸せではなかった', '幸せだった'),
                     ('あなたは少し平穏ではない', 'あなたは平穏ではない')]:
        changed = body.replace(follow, follow.replace(old, new, 1), 1)
        assert changed != body and not read_body(context, changed).passed


@pytest.mark.parametrize('last,retained,removed', [
    ('今は安心ではない。', '回答した時点では安心ではない', None),
    ('「少し私は安心です」ではなく「私も安心ではなかった」です。', '先の回答時点ではあなたも安心ではなかった', '少し私は安心です'),
    ('「少し私は安心です」は誤りです。', 'その時は楽しかった', '少し私は安心です'),
])
def test_nominal_negation_and_medial_owner_saved_update(qcase, qdb, monkeypatch, last, retained, removed):
    user, parent, _ = qcase
    service = active(monkeypatch)
    qdb.query('update public.emotions set memo=$1 where id=$2', [EXACT_RECORD_MEMO, parent])
    first = current = run(service.start(user, parent))
    for index, reply in enumerate(('今は少し私は安心です。', 'その時は楽しかった。', last)):
        if index:
            current = run(cont(service, user, current, f'nominal-owner-continue-{index}'))
        current = run(answer(service, user, current, reply, f'nominal-owner-answer-{index}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        body = current['current_observation']['text']
        follow = body.split('Emlisから：', 1)[1]
        assert all(value in follow for value in ('嬉し', '悲し', '寂し'))
        if index:
            assert 'その時は楽しかった' in follow
        if index == 2:
            assert retained in follow
            if removed:
                assert removed not in body and 'あなたは少し安心な' not in follow
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved nominal owner read must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current
    assert qdb.query('select memo from public.emotions where id=$1', [parent])['rows'][0]['memo'] == EXACT_RECORD_MEMO


@pytest.mark.parametrize('reply,visible', [
    ('今は安心ではない。', '安心ではないのですね。'),
    ('今は少し私は安心です。', 'あなたは少し安心なのですね。'),
])
def test_nominal_negation_and_medial_owner_survive_event_withdrawal(reply, visible):
    req = advance(advance(begin(), reply), '「褒められた」は誤りです。')
    context = actual(request=req)
    body, follow = context[0].artifact.text, context[0].artifact.reception
    assert '褒められた' not in body and '誘われた' in body and '頼まれた' in body
    assert visible in follow and '不安' not in follow
    assert read_body(context, body).passed
    changed = body.replace(follow, follow.replace(visible,
        visible.replace('ではない', 'ではなかった') if 'ではない' in visible
        else visible.replace('少し', ''), 1), 1)
    assert changed != body and not read_body(context, changed).passed


@pytest.mark.parametrize('source', ['少し私は安心ではないです', '私は不安ではないです',
    '少し友人は安心です', '少しあなたは安心です', 'とても私は安心です',
    '安心ではないかもしれない', '達成ではない', '少し私は彼は安心です'])
def test_nominal_negation_and_medial_owner_keep_unresolved_boundaries(source):
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning
    prepared = prepare_emlis_meaning(advance(begin(), '今は' + source + '。'))
    assert not prepared.accepted_nuclei and prepared.checkpoint.unresolved_parts


@pytest.mark.parametrize('source,visible,altered', [
    ('少し私は安心ではなかった', '当時、あなたは少し安心ではなかった', '当時、あなたは少し安心だった'),
    ('少し私は幸せでした', '当時、あなたは少し幸せだった', '当時、あなたは少し幸せではなかった'),
])
def test_nominal_negation_and_medial_owner_original_revision_keeps_other_answers(source, visible, altered):
    req = begin(EXACT_RECORD_MEMO)
    for reply in (*TWO_POSITIVE_PAIRS[0], f'「悲しかった」ではなく「{source}」です。'):
        req = advance(req, reply)
    context = actual(request=req)
    body, follow = context[0].artifact.text, context[0].artifact.reception
    assert '悲しかった' not in body and '悲しさ' not in follow
    assert all(value in follow for value in ('嬉し', '寂し', '回答した時点では嬉しい',
        'その時は楽しかった', '言い直してくださった気持ちについては、' + visible))
    assert read_body(context, body).passed
    for replacement in (altered, visible.replace('少し', ''), visible.replace('あなたは', 'あなたも'),
                        visible.replace('当時、', '回答した時点で、')):
        changed = body.replace(follow, follow.replace(visible, replacement, 1), 1)
        assert changed != body and not read_body(context, changed).passed


@pytest.mark.parametrize('memo', [EXACT_RECORD_MEMO, RECORD_TRIPLE_MEMO])
@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('third,visible', [
    ('今は安心ではありません。', '回答した時点では安心ではない'),
    ('その時は私も幸せではありませんでした。', 'その時はあなたも幸せではなかった'),
    ('今は少し私は安心ではありません。', '回答した時点ではあなたは少し安心ではない'),
    ('その時は少し平穏ではありませんでした。', 'その時は少し平穏ではなかった'),
])
def test_polite_nominal_negation_keeps_originals_and_each_answer(memo, field, third, visible):
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning
    req = begin(memo if field == 'memo' else '', memo if field == 'memo_action' else '')
    for reply in (*TWO_POSITIVE_PAIRS[0], third):
        req = advance(req, reply)
    prepared = prepare_emlis_meaning(req)
    assert not prepared.checkpoint.unresolved_parts
    nucleus, = prepared.accepted_nuclei
    frame = nucleus.semantic_frame
    assert (nucleus.kind, frame.predicate_kind, frame.modality, frame.polarity) == (
        'reaction', 'feeling', 'feeling', 'negative')
    assert 'operator:feeling' in frame.attribute_codes
    context = actual(request=req)
    body, follow = context[0].artifact.text, context[0].artifact.reception
    assert all(value in follow for value in ('嬉し', '悲し', '寂し',
        '回答した時点では嬉しい', 'その時は楽しかった', visible + 'のですね。'))
    assert all(prefix in follow for prefix in RECORD_PREFIXES)
    original_answer = third[4:-1] if third.startswith('その時は') else third[2:-1]
    assert original_answer in context[0].artifact.observation
    assert '不安' not in body and 'ありません' not in follow
    assert read_body(context, body).passed
    ending = 'なかった' if 'ではなかった' in visible else 'ない'
    polite = 'ありませんでした' if ending == 'なかった' else 'ありません'
    changes = [visible.replace(ending, 'ない' if ending == 'なかった' else 'なかった'),
               visible.replace('では' + ending, 'だった' if ending == 'なかった' else 'な'),
               visible.replace(ending, polite), visible.replace('安心では' + ending, '不安な'),
               visible.replace('回答した時点では', 'その時は') if third.startswith('今は')
               else visible.replace('その時は', '回答した時点では')]
    if '少し' in visible:
        changes.append(visible.replace('少し', ''))
    if 'あなた' in visible:
        changes.extend([visible.replace('あなた', '相手'),
                        visible.replace('あなたも', 'あなたは') if 'あなたも' in visible
                        else visible.replace('あなたは', 'あなたも')])
    for changed in set(changes) - {visible}:
        assert not read_body(context, body.replace(follow, follow.replace(visible, changed, 1), 1)).passed
    for old in (visible, 'その時は楽しかった', '回答した時点では嬉しい'):
        assert not read_body(context, body.replace(follow, follow.replace(old, '', 1), 1)).passed
    changed = body.replace(follow, follow.replace(RECORD_PREFIXES[2], RECORD_PREFIXES[0], 1), 1)
    assert not read_body(context, changed).passed


@pytest.mark.parametrize('position', [0, 1, 2])
@pytest.mark.parametrize('source,visible', [
    ('少し私は安心ではありません', 'あなたは少し安心ではない'),
    ('私も少し幸せではありませんでした', 'あなたも少し幸せではなかった'),
])
def test_polite_nominal_negation_each_answer_position(position, source, visible):
    replies = list(TWO_POSITIVE_PAIRS[0])
    replies.insert(position, '今は' + source + '。')
    req = begin(EXACT_RECORD_MEMO)
    for reply in replies:
        req = advance(req, reply)
    context = actual(request=req)
    body, follow = context[0].artifact.text, context[0].artifact.reception
    assert all(value in follow for value in ('嬉し', '悲し', '寂し',
        '回答した時点では嬉しい', 'その時は楽しかった', '回答した時点では' + visible))
    assert read_body(context, body).passed
    assert not read_body(context, body.replace(follow, follow.replace(visible, visible.replace('少し', ''), 1), 1)).passed


def test_polite_nominal_negation_three_negative_answers_restore_actual_source_bytes():
    sources = ['安心ではありません', '私も幸せではありませんでした', '少し私は平穏ではありません']
    req = begin(EXACT_RECORD_MEMO)
    for when, source in zip(('今は', 'その時は', '今は'), sources, strict=True):
        req = advance(req, when + source + '。')
    context = actual(request=req)
    result, plan, _, resolver, selected = context
    follow = result.artifact.reception
    assert all(s in follow for s in ('嬉しくなかった', '悲しかった', '寂しかった',
        '安心ではない', 'あなたも幸せではなかった', 'あなたは少し平穏ではない'))
    sentences = [part + '。' for part in follow.removesuffix('。').split('。')]
    moves = plan.response_plan.human_reception_plan.moves
    assert len(sentences) == len(moves) == 3
    with patch.object(reception, '_source_grounded_received_discourse', side_effect=AssertionError('no received author')):
        for raw, move, source in zip(sentences, moves, sources, strict=True):
            proof = gate.read_received_discourse(raw, move, plan, resolver, selected)
            assert proof is not None and proof[-1][2].decode() == source
            assert 'ありません' not in raw.encode()[proof[-1][0]:proof[-1][1]].decode()
    # The standalone answer reader also serves negative group clauses. Read
    # actual finite prose independently, including the polite past source.
    index = {n.nucleus_id: n for n in plan.nuclei}
    finite_answers = ('安心ではない', 'あなたも幸せではなかった', 'あなたは少し平穏ではない')
    for position, (source, finite) in enumerate(zip(sources, finite_answers, strict=True)):
        answer_nucleus = index[f'answer:s{position + 7}']
        relation, = [r for r in plan.relations if r.type == 'evaluation_about_event'
                     and r.to_nucleus_id == answer_nucleus.nucleus_id]
        when = 'original_occasion' if position == 1 else 'answer_time'
        temporal = 'その時は' if position == 1 else '回答した時点では'
        raw = RECORD_PREFIXES[position] + '誘われたことについて、' + temporal + finite + 'のですね。'
        proof = gate._read_answer_feeling_clause(raw, index[relation.from_nucleus_id],
            answer_nucleus, when, plan, resolver)
        assert proof is not None and proof[-1][2].decode() == source
        wrong = raw.replace(finite, finite.replace('なかった', 'ありませんでした')
                            if position == 1 else finite.replace('ない', 'ありません'))
        assert gate._read_answer_feeling_clause(wrong, index[relation.from_nucleus_id],
            answer_nucleus, when, plan, resolver) is None
    assert read_body(context, result.artifact.text).passed


@pytest.mark.parametrize('reply,visible', [
    ('今は少し私は安心ではありません。', '回答した時点で、あなたは少し安心ではない'),
    ('その時は私も幸せではありませんでした。', 'その時、あなたも幸せではなかった'),
])
def test_polite_nominal_negation_survives_event_withdrawal(reply, visible):
    req = advance(advance(begin(), reply), '「褒められた」は誤りです。')
    context = actual(request=req)
    body, follow = context[0].artifact.text, context[0].artifact.reception
    assert '褒められた' not in body and '誘われた' in body and '頼まれた' in body
    assert visible + 'のですね。' in follow
    assert read_body(context, body).passed
    for old, new in [('ではない', 'ではなかった'), ('ではなかった', 'ではない'),
                     ('あなた', '相手'), ('少し', '')]:
        if old in visible:
            assert not read_body(context, body.replace(follow, follow.replace(visible, visible.replace(old, new), 1), 1)).passed


@pytest.mark.parametrize('source,visible', [
    ('少し私は安心ではありません', '当時、あなたは少し安心ではない'),
    ('私も幸せではありませんでした', '当時、あなたも幸せではなかった'),
])
def test_polite_nominal_negation_original_revision_keeps_other_answers(source, visible):
    req = begin(EXACT_RECORD_MEMO)
    for reply in (*TWO_POSITIVE_PAIRS[0], f'「悲しかった」ではなく「{source}」です。'):
        req = advance(req, reply)
    context = actual(request=req)
    body, follow = context[0].artifact.text, context[0].artifact.reception
    assert '悲しかった' not in body and '悲しさ' not in follow
    assert all(value in follow for value in ('嬉し', '寂し', '回答した時点では嬉しい',
        'その時は楽しかった', '言い直してくださった気持ちについては、' + visible))
    assert read_body(context, body).passed
    assert not read_body(context, body.replace(follow, follow.replace(visible, visible.replace('当時、', 'その時、'), 1), 1)).passed


@pytest.mark.parametrize('last,retained,removed', [
    ('その時は私も幸せではありませんでした。', 'その時はあなたも幸せではなかった', None),
    ('「少し私は安心ではありません」ではなく「私も幸せではありませんでした」です。',
     '先の回答時点ではあなたも幸せではなかった', '少し私は安心ではありません'),
    ('「少し私は安心ではありません」は誤りです。', 'その時は楽しかった', '少し私は安心ではありません'),
])
def test_polite_nominal_negation_saved_add_revision_withdrawal(qcase, qdb, monkeypatch, last, retained, removed):
    user, parent, _ = qcase
    service = active(monkeypatch)
    qdb.query('update public.emotions set memo=$1 where id=$2', [EXACT_RECORD_MEMO, parent])
    first = current = run(service.start(user, parent))
    for index, reply in enumerate(('今は少し私は安心ではありません。', 'その時は楽しかった。', last)):
        if index:
            current = run(cont(service, user, current, f'polite-negative-continue-{index}'))
        current = run(answer(service, user, current, reply, f'polite-negative-answer-{index}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        body = current['current_observation']['text']
        follow = body.split('Emlisから：', 1)[1]
        assert all(value in follow for value in ('嬉し', '悲し', '寂し'))
        if index:
            assert 'その時は楽しかった' in follow
        if index == 2:
            assert retained in follow
            if removed:
                assert removed not in body and 'あなたは少し安心ではない' not in follow
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved polite negation must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current
    assert qdb.query('select memo from public.emotions where id=$1', [parent])['rows'][0]['memo'] == EXACT_RECORD_MEMO


@pytest.mark.parametrize('source', ['安心ではありませんか', '安心ではありませんと言われた',
    '安心ではありませんなら嬉しい', '友人は安心ではありません', '少しあなたは安心ではありません',
    'とても私は安心ではありません', '安心ではありませんかもしれない', '達成ではありません'])
def test_polite_nominal_negation_keeps_unresolved_boundaries(source):
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning
    prepared = prepare_emlis_meaning(advance(begin(), '今は' + source + '。'))
    assert not prepared.accepted_nuclei and prepared.checkpoint.unresolved_parts


@pytest.mark.parametrize('memo', [EXACT_RECORD_MEMO, RECORD_TRIPLE_MEMO])
@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('third,visible,polarity', [
    ('今は少し私は少し安心です。', '回答した時点では少しあなたは少し安心な', 'positive'),
    ('その時は少し私も少し幸せでした。', 'その時は少しあなたも少し幸せだった', 'positive'),
    ('今は少し私は少し安心ではない。', '回答した時点では少しあなたは少し安心ではない', 'negative'),
    ('その時は少し私も少し幸せではありませんでした。', 'その時は少しあなたも少し幸せではなかった', 'negative'),
])
def test_nominal_modifier_chains_keep_originals_and_answers(memo, field, third, visible, polarity):
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning
    req = begin(memo if field == 'memo' else '', memo if field == 'memo_action' else '')
    for reply in (*TWO_POSITIVE_PAIRS[0], third):
        req = advance(req, reply)
    prepared = prepare_emlis_meaning(req)
    assert not prepared.checkpoint.unresolved_parts
    nucleus, = prepared.accepted_nuclei
    frame = nucleus.semantic_frame
    assert (nucleus.kind, frame.predicate_kind, frame.modality, frame.polarity) == (
        'reaction', 'feeling', 'feeling', polarity)
    context = actual(request=req)
    body, follow = context[0].artifact.text, context[0].artifact.reception
    source = third[4:-1] if third.startswith('その時は') else third[2:-1]
    assert source in context[0].artifact.observation
    assert all(value in follow for value in ('嬉し', '悲し', '寂し',
        '回答した時点では嬉しい', 'その時は楽しかった', visible + 'のですね。'))
    assert all(prefix in follow for prefix in RECORD_PREFIXES)
    assert '不安' not in body and 'ありません' not in follow
    assert read_body(context, body).passed
    first_degree = visible.index('少し')
    last_degree = visible.rindex('少し')
    assert first_degree != last_degree
    wrong = [visible[:first_degree] + visible[first_degree + 2:],
             visible[:last_degree] + visible[last_degree + 2:],
             visible.replace('少しあなたは少し', 'あなたは少し少し') if 'あなたは' in visible
             else visible.replace('少しあなたも少し', 'あなたも少し少し'),
             visible.replace('あなた', '相手'),
             visible.replace('あなたは', 'あなたも') if 'あなたは' in visible
             else visible.replace('あなたも', 'あなたは'),
             visible.replace('回答した時点では', 'その時は') if third.startswith('今は')
             else visible.replace('その時は', '回答した時点では')]
    if polarity == 'negative':
        wrong.append(visible.replace('ではなかった', 'だった') if 'ではなかった' in visible
                     else visible.replace('ではない', 'な'))
        wrong.append(visible.replace('ではなかった', 'ではない') if 'ではなかった' in visible
                     else visible.replace('ではない', 'ではなかった'))
    else:
        wrong.append(visible.replace('だった', 'な') if visible.endswith('だった') else visible[:-1] + 'だった')
    for changed in wrong:
        assert changed != visible
        assert not read_body(context, body.replace(follow, follow.replace(visible, changed, 1), 1)).passed
    for old in (visible, '回答した時点では嬉しい', 'その時は楽しかった'):
        assert not read_body(context, body.replace(follow, follow.replace(old, '', 1), 1)).passed
    changed = body.replace(follow, follow.replace(RECORD_PREFIXES[2], RECORD_PREFIXES[0], 1), 1)
    assert not read_body(context, changed).passed


@pytest.mark.parametrize('source,visible,changed', [
    ('まだ私は少し安心です', 'まだあなたは少し安心な', '少しあなたはまだ安心な'),
    ('少し少し私も幸せでした', '少し少しあなたも幸せだった', '少しあなたも幸せだった'),
    ('少し少し安心です', '少し少し安心な', '少し安心な'),
    ('私は少し少し安心です', 'あなたは少し少し安心な', 'あなたは少し安心な'),
])
def test_nominal_modifier_chains_keep_bare_leading_and_medial_order(source, visible, changed):
    req = begin(EXACT_RECORD_MEMO)
    for reply in (*TWO_POSITIVE_PAIRS[0], '今は' + source + '。'):
        req = advance(req, reply)
    context = actual(request=req)
    body, follow = context[0].artifact.text, context[0].artifact.reception
    assert all(value in follow for value in ('嬉し', '悲し', '寂し',
        '回答した時点では嬉しい', 'その時は楽しかった', visible + 'のですね。'))
    assert read_body(context, body).passed
    assert not read_body(context, body.replace(follow, follow.replace(visible, changed, 1), 1)).passed


@pytest.mark.parametrize('position', [0, 1, 2])
@pytest.mark.parametrize('source,visible', [
    ('少し私は少し安心です', '少しあなたは少し安心'),
    ('少し私もまだ平穏ではありません', '少しあなたもまだ平穏ではない'),
])
def test_nominal_modifier_chains_each_answer_position(position, source, visible):
    replies = list(TWO_POSITIVE_PAIRS[0])
    replies.insert(position, '今は' + source + '。')
    req = begin(EXACT_RECORD_MEMO)
    for reply in replies:
        req = advance(req, reply)
    context = actual(request=req)
    body, follow = context[0].artifact.text, context[0].artifact.reception
    assert all(value in follow for value in ('嬉し', '悲し', '寂し',
        '回答した時点では嬉しい', 'その時は楽しかった', visible))
    assert read_body(context, body).passed
    assert not read_body(context, body.replace(follow, follow.replace(visible, visible.replace('少し', '', 1), 1), 1)).passed


def test_nominal_modifier_chains_negative_group_restores_whole_sources():
    sources = ['少し私は少し安心ではない', 'まだ私も少し幸せではありませんでした', '少し私もまだ平穏ではありません']
    req = begin(EXACT_RECORD_MEMO)
    for when, source in zip(('今は', 'その時は', '今は'), sources, strict=True):
        req = advance(req, when + source + '。')
    context = actual(request=req)
    result, plan, _, resolver, selected = context
    follow = result.artifact.reception
    assert all(s in follow for s in ('嬉しくなかった', '悲しかった', '寂しかった',
        '少しあなたは少し安心ではない', 'まだあなたも少し幸せではなかった', '少しあなたもまだ平穏ではない'))
    sentences = [part + '。' for part in follow.removesuffix('。').split('。')]
    moves = plan.response_plan.human_reception_plan.moves
    assert len(sentences) == len(moves) == 3
    with patch.object(reception, '_source_grounded_received_discourse', side_effect=AssertionError('no received author')):
        for raw, move, source in zip(sentences, moves, sources, strict=True):
            proof = gate.read_received_discourse(raw, move, plan, resolver, selected)
            assert proof is not None and proof[-1][2].decode() == source
            visible = raw.encode()[proof[-1][0]:proof[-1][1]].decode()
            assert visible.startswith(source[:source.index('私')] + 'あなた')
    assert read_body(context, result.artifact.text).passed


@pytest.mark.parametrize('reply,visible', [
    ('今は少し私は少し安心です。', '回答した時点で、少しあなたは少し安心な'),
    ('その時はまだ私も少し幸せではありませんでした。', 'その時、まだあなたも少し幸せではなかった'),
])
def test_nominal_modifier_chains_survive_event_withdrawal(reply, visible):
    req = advance(advance(begin(), reply), '「褒められた」は誤りです。')
    context = actual(request=req)
    body, follow = context[0].artifact.text, context[0].artifact.reception
    assert '褒められた' not in body and '誘われた' in body and '頼まれた' in body
    assert visible + 'のですね。' in follow
    assert read_body(context, body).passed
    for changed in (visible.replace('少し', '', 1), visible.replace('あなた', '相手')):
        assert not read_body(context, body.replace(follow, follow.replace(visible, changed, 1), 1)).passed


@pytest.mark.parametrize('source,visible', [
    ('少し私は少し安心です', '当時、少しあなたは少し安心な'),
    ('まだ私も少し幸せではありませんでした', '当時、まだあなたも少し幸せではなかった'),
])
def test_nominal_modifier_chains_original_revision_keeps_other_answers(source, visible):
    req = begin(EXACT_RECORD_MEMO)
    for reply in (*TWO_POSITIVE_PAIRS[0], f'「悲しかった」ではなく「{source}」です。'):
        req = advance(req, reply)
    context = actual(request=req)
    body, follow = context[0].artifact.text, context[0].artifact.reception
    assert '悲しかった' not in body and '悲しさ' not in follow
    assert all(value in follow for value in ('嬉し', '寂し', '回答した時点では嬉しい',
        'その時は楽しかった', '言い直してくださった気持ちについては、' + visible))
    assert read_body(context, body).passed
    assert not read_body(context, body.replace(follow, follow.replace(visible, visible.replace('少し', '', 1), 1), 1)).passed


@pytest.mark.parametrize('last,retained,removed', [
    ('今は少し私もまだ平穏ではありません。', '回答した時点では少しあなたもまだ平穏ではない', None),
    ('「少し私は少し安心です」ではなく「まだ私は少し幸せでした」です。',
     '先の回答時点ではまだあなたは少し幸せだった', '少し私は少し安心です'),
    ('「少し私は少し安心です」は誤りです。', 'その時は楽しかった', '少し私は少し安心です'),
])
def test_nominal_modifier_chains_saved_add_revision_withdrawal(qcase, qdb, monkeypatch, last, retained, removed):
    user, parent, _ = qcase
    service = active(monkeypatch)
    qdb.query('update public.emotions set memo=$1 where id=$2', [EXACT_RECORD_MEMO, parent])
    first = current = run(service.start(user, parent))
    for index, reply in enumerate(('今は少し私は少し安心です。', 'その時は楽しかった。', last)):
        if index:
            current = run(cont(service, user, current, f'modifier-nominal-continue-{index}'))
        current = run(answer(service, user, current, reply, f'modifier-nominal-answer-{index}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        body = current['current_observation']['text']
        follow = body.split('Emlisから：', 1)[1]
        assert all(value in follow for value in ('嬉し', '悲し', '寂し'))
        if index:
            assert 'その時は楽しかった' in follow
        if index == 2:
            assert retained in follow
            if removed:
                assert removed not in body and '少しあなたは少し安心な' not in follow
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved modifier chains must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current
    assert qdb.query('select memo from public.emotions where id=$1', [parent])['rows'][0]['memo'] == EXACT_RECORD_MEMO


@pytest.mark.parametrize('source', ['とても私には少し安心です', '全然私は少し安心です',
    '私は本当は少し安心です', '本当は私はまだ安心です', '少し友人は少し安心です',
    '少しあなたは少し安心です', '少し私は少し安心なら嬉しい', '少し私は少し安心かもしれない'])
def test_nominal_modifier_chains_keep_existing_unresolved_boundaries(source):
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning
    prepared = prepare_emlis_meaning(advance(begin(), '今は' + source + '。'))
    assert not prepared.accepted_nuclei and prepared.checkpoint.unresolved_parts


@pytest.mark.parametrize('source', ['少し私は私も安心です', '少し私が少し安心です',
    '少し私にも少し安心です', '少し私は突然安心です', '少し私は「安心です」と言われた'])
def test_nominal_modifier_chains_do_not_prove_unbound_sources(source):
    import emlis_ai_grounded_observation_plan as gp
    assert not gp._THREAD_POSITIVE_FEELING_COPULA_RE.fullmatch(source)
    assert not gp._THREAD_NEGATIVE_FEELING_COPULA_RE.fullmatch(source)
    assert reception._medial_feeling_owner(source) is None
    assert gate._thread_feeling_owner(source) is None


@pytest.mark.parametrize('memo', [EXACT_RECORD_MEMO, RECORD_TRIPLE_MEMO])
@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('source,visible,polarity', [
    ('安心なのです', '安心なのですね', 'positive'),
    ('少し私は少し安心なのです', '少しあなたは少し安心なのですね', 'positive'),
    ('私も幸せだったのです', 'あなたも幸せだったのですね', 'positive'),
    ('まだ私は少し平穏ではないのです', 'まだあなたは少し平穏ではないのですね', 'negative'),
    ('私も安心ではなかったのだ', 'あなたも安心ではなかったのですね', 'negative'),
    ('私は安心なのだった', 'あなたは安心なのでしたね', 'positive'),
])
def test_nominal_explained_answer_keeps_complete_sources(memo, field, source, visible, polarity):
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning
    req = begin(memo if field == 'memo' else '', memo if field == 'memo_action' else '')
    for reply in (*TWO_POSITIVE_PAIRS[0], '今は' + source + '。'):
        req = advance(req, reply)
    prepared = prepare_emlis_meaning(req)
    nucleus, = prepared.accepted_nuclei
    assert not prepared.checkpoint.unresolved_parts
    assert (nucleus.kind, nucleus.semantic_frame.predicate_kind, nucleus.semantic_frame.modality,
            nucleus.semantic_frame.polarity) == ('reaction', 'feeling', 'feeling', polarity)
    context = actual(request=req)
    body, follow = context[0].artifact.text, context[0].artifact.reception
    assert source in context[0].artifact.observation
    assert all(value in follow for value in ('嬉し', '悲し', '寂し',
        '回答した時点では嬉しい', 'その時は楽しかった', visible))
    assert all(prefix in follow for prefix in RECORD_PREFIXES)
    assert 'ですこと' not in follow and 'のですの' not in follow
    assert read_body(context, body).passed
    wrong = [visible.replace('のですね', 'ですね').replace('のでしたね', 'でしたね'),
             visible.replace('のですね', 'ののですね').replace('のでしたね', 'ののでしたね')]
    if 'あなた' in visible:
        wrong += [visible.replace('あなた', '友人'), visible.replace('あなた', '私')]
        wrong.append(visible.replace('あなたは', 'あなたも') if 'あなたは' in visible else visible.replace('あなたも', 'あなたは'))
    if '少し' in visible:
        wrong.append(visible.replace('少し', '', 1))
    if visible.startswith('少しあなたは少し'):
        wrong += [visible.replace('少しあなたは少し', 'あなたは少し少し'), visible.replace('は少し', 'は')]
    if 'ではなかった' in visible:
        wrong += [visible.replace('ではなかった', 'だった'), visible.replace('ではなかった', 'ではない')]
    elif 'ではない' in visible:
        wrong += [visible.replace('ではない', 'な'), visible.replace('ではない', 'ではなかった')]
    elif 'だったのですね' in visible:
        wrong.append(visible.replace('だったのですね', 'なのでしたね'))
    elif 'なのでしたね' in visible:
        wrong.append(visible.replace('なのでしたね', 'だったのですね'))
    else:
        wrong.append(visible.replace('なのですね', 'だったのですね'))
    for changed in wrong:
        assert changed != visible
        assert not read_body(context, body.replace(follow, follow.replace(visible, changed, 1), 1)).passed
    for old in (visible, '回答した時点では嬉しい', 'その時は楽しかった'):
        assert not read_body(context, body.replace(follow, follow.replace(old, '', 1), 1)).passed
    assert not read_body(context, body.replace(follow, follow.replace(RECORD_PREFIXES[2], RECORD_PREFIXES[0], 1), 1)).passed


@pytest.mark.parametrize('position', [0, 1, 2])
@pytest.mark.parametrize('source,finite,terminal', [
    ('少し私は少し安心なのです', '少しあなたは少し安心なのだ', '少しあなたは少し安心なのですね'),
    ('私は安心なのだった', 'あなたは安心なのだった', 'あなたは安心なのでしたね'),
    ('まだ私も少し平穏ではないのです', 'まだあなたも少し平穏ではないのだ', 'まだあなたも少し平穏ではないのですね'),
])
def test_nominal_explained_answer_all_positions_keep_explanation(position, source, finite, terminal):
    replies = list(TWO_POSITIVE_PAIRS[0])
    replies.insert(position, '今は' + source + '。')
    req = begin(EXACT_RECORD_MEMO)
    for reply in replies:
        req = advance(req, reply)
    context = actual(request=req)
    body, follow = context[0].artifact.text, context[0].artifact.reception
    assert all(value in follow for value in ('嬉し', '悲し', '寂し',
        '回答した時点では嬉しい', 'その時は楽しかった'))
    assert finite + 'し、' in follow or terminal in follow
    assert read_body(context, body).passed
    old = finite + 'し、' if finite + 'し、' in follow else terminal
    wrong = old.replace('のだった', 'だった').replace('のだし', 'だし').replace('のですね', 'ですね').replace('のでしたね', 'でしたね')
    assert wrong != old
    assert not read_body(context, body.replace(follow, follow.replace(old, wrong, 1), 1)).passed


@pytest.mark.parametrize('reply,visible', [
    ('今は少し私は少し安心なのです。', '回答した時点で、少しあなたは少し安心なのですね'),
    ('その時は私も幸せではなかったのです。', 'その時、あなたも幸せではなかったのですね'),
    ('今は私は安心なのだった。', '回答した時点で、あなたは安心なのでしたね'),
])
def test_nominal_explained_answer_event_withdrawal_keeps_independent_source(reply, visible):
    context = actual(request=advance(advance(begin(), reply), '「褒められた」は誤りです。'))
    body, follow = context[0].artifact.text, context[0].artifact.reception
    assert '褒められた' not in body and '誘われた' in body and '頼まれた' in body
    assert visible in follow and '嬉しくなかった' in follow
    assert read_body(context, body).passed
    for changed in (visible.replace('あなた', '相手'), visible.replace('のですね', 'ですね').replace('のでしたね', 'でしたね')):
        assert not read_body(context, body.replace(follow, follow.replace(visible, changed, 1), 1)).passed


@pytest.mark.parametrize('source,visible', [
    ('少し私は少し安心なのです', '少しあなたは少し安心なの'),
    ('私も幸せではなかったのです', 'あなたも幸せではなかったの'),
])
def test_nominal_explained_answer_original_revision_keeps_other_meanings(source, visible):
    req = begin(EXACT_RECORD_MEMO)
    for reply in (*TWO_POSITIVE_PAIRS[0], f'「悲しかった」ではなく「{source}」です。'):
        req = advance(req, reply)
    context = actual(request=req)
    body, follow = context[0].artifact.text, context[0].artifact.reception
    assert '悲しかった' not in body and '悲しさ' not in follow
    assert all(value in follow for value in ('嬉し', '寂し', '回答した時点では嬉しい',
        'その時は楽しかった', '言い直してくださった気持ちについては、当時、' + visible))
    assert read_body(context, body).passed
    assert not read_body(context, body.replace(follow, follow.replace(visible, visible.replace('あなた', '相手'), 1), 1)).passed


def test_nominal_explained_answer_negative_group_restores_actual_bytes():
    sources = ['少し私は少し安心ではないのです', 'まだ私も少し幸せではなかったのだ', '平穏ではないのだった']
    req = begin(EXACT_RECORD_MEMO)
    for when, source in zip(('今は', 'その時は', '今は'), sources, strict=True):
        req = advance(req, when + source + '。')
    context = actual(request=req)
    result, plan, _, resolver, selected = context
    follow = result.artifact.reception
    assert all(s in follow for s in ('嬉しくなかった', '悲しかった', '寂しかった',
        '少しあなたは少し安心ではないの', 'まだあなたも少し幸せではなかったの', '平穏ではないのでしたね'))
    sentences = [part + '。' for part in follow.removesuffix('。').split('。')]
    moves = plan.response_plan.human_reception_plan.moves
    assert len(sentences) == len(moves) == 3
    with patch.object(reception, '_source_grounded_received_discourse', side_effect=AssertionError('no received author')):
        for raw, move, source in zip(sentences, moves, sources, strict=True):
            proof = gate.read_received_discourse(raw, move, plan, resolver, selected)
            assert proof is not None and proof[-1][2].decode() == source
            assert raw.encode()[proof[-1][0]:proof[-1][1]]
    assert read_body(context, result.artifact.text).passed


@pytest.mark.parametrize('last,retained,removed', [
    ('今はまだ私も平穏ではないのです。', 'まだあなたも平穏ではないのですね', None),
    ('「少し私は少し安心なのです」ではなく「私は幸せだったのです」です。',
     '先の回答時点ではあなたは幸せだったのですね', '少し私は少し安心なのです'),
    ('「少し私は少し安心なのです」は誤りです。', 'その時は楽しかった', '少し私は少し安心なのです'),
])
def test_nominal_explained_answer_saved_add_revision_withdrawal(qcase, qdb, monkeypatch, last, retained, removed):
    user, parent, _ = qcase
    service = active(monkeypatch)
    qdb.query('update public.emotions set memo=$1 where id=$2', [EXACT_RECORD_MEMO, parent])
    first = current = run(service.start(user, parent))
    for index, reply in enumerate(('今は少し私は少し安心なのです。', 'その時は楽しかった。', last)):
        if index:
            current = run(cont(service, user, current, f'explained-nominal-continue-{index}'))
        current = run(answer(service, user, current, reply, f'explained-nominal-answer-{index}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        body = current['current_observation']['text']
        follow = body.split('Emlisから：', 1)[1]
        assert all(value in follow for value in ('嬉し', '悲し', '寂し'))
        if index:
            assert 'その時は楽しかった' in follow
        if index == 2:
            assert retained in follow
            if removed:
                assert removed not in body and '少しあなたは少し安心なの' not in follow
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved explanations must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current
    assert qdb.query('select memo from public.emotions where id=$1', [parent])['rows'][0]['memo'] == EXACT_RECORD_MEMO


@pytest.mark.parametrize('source', ['とても私には少し安心なのです', '全然私は少し安心なのです',
    '私は本当は少し安心なのです', '少し友人は安心なのです', '少しあなたは安心なのです',
    '安心なのですか', '安心なら嬉しい', '安心かもしれない'])
def test_nominal_explained_answer_keeps_unresolved_boundaries(source):
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning
    prepared = prepare_emlis_meaning(advance(begin(), '今は' + source + '。'))
    assert not prepared.accepted_nuclei and prepared.checkpoint.unresolved_parts


@pytest.mark.parametrize('source', ['少し私は私も安心なのです', '少し私が少し安心なのです',
    '少し私にも少し安心なのです', '少し私は突然安心なのです', '私は「安心なのです」と言われた',
    '私は安心ですのです'])
def test_nominal_explained_answer_does_not_prove_unbound_source(source):
    import emlis_ai_grounded_observation_plan as gp
    assert not gp._THREAD_NOMINAL_FEELING_EXPLANATION_RE.fullmatch(source)


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('event', ['誘われた', '私は誘われた'])
@pytest.mark.parametrize('source', ['安心なのです', '私も幸せだったのです',
                                  '私は安心なのだった', '少し私は少し安心なのです'])
def test_shared_answer_topic_keeps_every_occurrence_and_complete_source(field, event, source):
    memo = EXACT_RECORD_MEMO.replace('誘われた', event)
    req = begin(memo if field == 'memo' else '', memo if field == 'memo_action' else '')
    for reply in (*TWO_POSITIVE_PAIRS[0], '今は' + source + '。'):
        req = advance(req, reply)
    context = actual(request=req)
    result, plan, _, resolver, selected = context
    body, follow = result.artifact.text, result.artifact.reception
    raw, _ = split_positive_answer_proof(context)
    visible_event = event.replace('私は', 'あなたは')
    topic = visible_event + 'ことについて、'
    assert raw.startswith(topic) and raw.count(visible_event) == 2
    assert all(raw.count(label) == 1 for label in RECORD_PREFIXES)
    assert all(value in follow for value in ('嬉し', '悲し', '寂し',
        '回答した時点では嬉しい', 'その時は楽しかった'))
    assert source in result.artifact.observation
    with patch.object(reception, '_source_owned_positive_answer_group_sentence', side_effect=AssertionError('no group author')), patch.object(
            reception, '_detached_feeling_finite_surface', side_effect=AssertionError('no finite author')):
        _, proof = split_positive_answer_proof(context, raw)
        assert proof is not None
        assert [s.decode() for _, _, s in proof] == [event, '嬉しい', event, '楽しかった', event, source]
        assert proof[0][:2] == proof[2][:2] != proof[4][:2]
        assert raw.encode()[proof[0][0]:proof[0][1]].decode() == visible_event
        assert all(raw.encode()[a:b] for a, b, _ in proof)
        assert read_body(context, body).passed
        mutations = [raw.replace(topic, '', 1), raw.replace(visible_event, '頼まれた', 1),
            raw.replace(RECORD_PREFIXES[1], '', 1),
            raw.replace(RECORD_PREFIXES[2], RECORD_PREFIXES[0], 1),
            raw.replace(RECORD_PREFIXES[0], 'TEMP').replace(RECORD_PREFIXES[2], RECORD_PREFIXES[0]).replace('TEMP', RECORD_PREFIXES[2]),
            raw.replace('回答した時点では嬉しい', 'その時は嬉しい'),
            raw.replace('楽しかった', '嬉しかった'), raw.replace('その時は楽しかったのですね。', ''),
            raw.replace('嬉しい', '嬉しくない', 1)]
        for changed in mutations:
            assert changed != raw
            assert split_positive_answer_proof(context, changed)[1] is None
            assert not read_body(context, body.replace(raw, changed, 1)).passed
    # Old independently qualified clauses remain readable for saved content.
    legacy = raw[len(topic):]
    for label in RECORD_PREFIXES[:2]:
        legacy = legacy.replace(label, label + visible_event + 'ことについて、', 1)
    assert read_body(context, body.replace(raw, legacy, 1)).passed


@pytest.mark.parametrize('position', [0, 1, 2])
@pytest.mark.parametrize('source', ['少し私は少し安心なのです', '私も幸せだったのです', '私は安心なのだった'])
def test_shared_answer_topic_retains_explanation_at_each_position(position, source):
    replies = list(TWO_POSITIVE_PAIRS[0])
    replies.insert(position, '今は' + source + '。')
    req = begin(EXACT_RECORD_MEMO)
    for reply in replies:
        req = advance(req, reply)
    context = actual(request=req)
    raw, proof = split_positive_answer_proof(context)
    assert raw.startswith('誘われたことについて、先に書かれた方では、')
    assert read_body(context, context[0].artifact.text).passed
    assert proof[2 * position + 1][2].decode() == source
    actual_finite = raw.encode()[proof[2 * position + 1][0]:proof[2 * position + 1][1]].decode()
    assert actual_finite
    for wrong in (actual_finite.replace('あなた', '友人'), actual_finite.replace('だった', 'な'),
                  actual_finite.replace('少し', '', 1), actual_finite + 'らしい'):
        if wrong == actual_finite:
            continue
        changed = raw.replace(actual_finite, wrong, 1)
        assert split_positive_answer_proof(context, changed)[1] is None


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('source', ['嬉しかった', '私は安心なのです'])
def test_shared_answer_topic_keeps_two_answers_separate_from_original_revision(field, source):
    req = begin(EXACT_RECORD_MEMO if field == 'memo' else '', EXACT_RECORD_MEMO if field == 'memo_action' else '')
    for reply in (*TWO_POSITIVE_PAIRS[0], f'「悲しかった」ではなく「{source}」です。'):
        req = advance(req, reply)
    context = actual(request=req)
    follow = context[0].artifact.reception
    assert '誘われたことについて、先に書かれた方では、' in follow
    assert '悲しかった' not in context[0].artifact.text and '悲しさ' not in follow
    assert all(s in follow for s in ('嬉し', '寂し', '回答した時点では嬉しい',
        'その時は楽しかった', '言い直してくださった気持ちについては、当時'))
    assert read_body(context, context[0].artifact.text).passed
    wrong = follow.replace('間に書かれた方では、その時は楽しかった', '後に書かれた方では、その時は楽しかった')
    assert wrong != follow and not read_body(context, context[0].artifact.text.replace(follow, wrong)).passed


@pytest.mark.parametrize('memo', [
    '褒められたのに、嬉しくなかった。誘われたのに、悲しかった。頼まれたのに、寂しかった。',
    '誘われたのに、嬉しくなかった。頼まれたのに、悲しかった。誘われたのに、寂しかった。',
    '私は誘われたのに、嬉しくなかった。自分は誘われたのに、悲しかった。私は誘われたのに、寂しかった。'])
def test_shared_answer_topic_does_not_merge_unequal_source_events(memo):
    req = begin(memo)
    for reply in (*TWO_POSITIVE_PAIRS[0], '今は安心なのです。'):
        req = advance(req, reply)
    context = actual(request=req)
    follow = context[0].artifact.reception
    assert follow.count('ことについて、') == 3
    assert all(s in follow for s in ('嬉し', '悲し', '寂し', '回答した時点では嬉しい',
                                    'その時は楽しかった', '安心なのですね'))
    assert read_body(context, context[0].artifact.text).passed


@pytest.mark.parametrize('legacy', [False, True])
@pytest.mark.parametrize('last,shared', [('今は安心なのです。', True),
    ('「悲しかった」ではなく「私は安心なのです」です。', True), ('「嬉しい」は誤りです。', False)])
def test_shared_answer_topic_saved_add_revision_withdrawal_and_legacy(qcase, qdb, monkeypatch, last, shared, legacy):
    user, parent, _ = qcase
    service = active(monkeypatch)
    qdb.query('update public.emotions set memo=$1 where id=$2', [EXACT_RECORD_MEMO, parent])
    first = current = run(service.start(user, parent))
    author = reception._source_owned_positive_answer_group_sentence
    def previous_surface(*args, **kwargs):
        text = author(*args, **kwargs)
        if text and text.startswith('誘われたことについて、先に書かれた方では、'):
            event, text = text.split('ことについて、', 1)
            text = re.sub(r'(?:先|間|後)に書かれた方では、', lambda m: m.group() + event + 'ことについて、', text)
        return text
    with monkeypatch.context() as old:
        if legacy:
            old.setattr(reception, '_source_owned_positive_answer_group_sentence', previous_surface)
        for index, reply in enumerate((*TWO_POSITIVE_PAIRS[0], last)):
            if index:
                current = run(cont(service, user, current, f'shared-topic-continue-{index}'))
            current = run(answer(service, user, current, reply, f'shared-topic-answer-{index}'))
            assert current['body_state'] == 'REFINED' and current['original'] == first['original']
            with monkeypatch.context() as saved:
                saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved topic must not regenerate'))
                assert run(service.get(user, parent)) == run(service.start(user, parent)) == current
    follow = current['current_observation']['text'].split('Emlisから：', 1)[1]
    assert ('誘われたことについて、先に書かれた方では、' in follow) == (shared and not legacy)
    assert 'その時は楽しかった' in follow and '寂し' in follow and '嬉し' in follow
    if 'ではなく' in last:
        assert '悲し' not in follow and '言い直してくださった' in follow
    else:
        assert '悲し' in follow
    if last == '「嬉しい」は誤りです。':
        assert '回答した時点では嬉しい' not in follow
    with monkeypatch.context() as saved:
        saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('legacy replay must not regenerate'))
        assert run(service.get(user, parent)) == run(service.start(user, parent)) == current
    assert qdb.query('select memo from public.emotions where id=$1', [parent])['rows'][0]['memo'] == EXACT_RECORD_MEMO

@pytest.fixture(scope='module')
def shared_answer_topic_mixed_context():
    req = begin('誘われたのに、嬉しくなかった。頼まれたのに、悲しかった。誘われたのに、寂しかった。')
    for reply in (*TWO_POSITIVE_PAIRS[0], '今は安心なのです。'):
        req = advance(req, reply)
    return actual(request=req)


@pytest.mark.parametrize('mutation', ['missing', 'duplicate', 'same_event', 'wrong_proof', 'unknown',
    'source_range', 'range_value', 'source_order', 'source_link', 'relation_source', 'answer_time', 'event_kind'])
def test_shared_answer_topic_mixed_window_preserves_source_and_about_guards(shared_answer_topic_mixed_context, mutation):
    test_same_name_positive_occurrence_proof_keeps_existing_rejection_guards(
        shared_answer_topic_mixed_context, mutation)


@pytest.mark.parametrize('last', [None, '今は少し苦しい。'])
def test_shared_answer_topic_mixed_window_does_not_prove_incomplete_or_negative_answers(last):
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning, build_updated_grounded_plan
    req = begin('誘われたのに、嬉しくなかった。頼まれたのに、悲しかった。誘われたのに、寂しかった。')
    for reply in (*TWO_POSITIVE_PAIRS[0], *((last,) if last else ())):
        req = advance(req, reply)
    plan = build_updated_grounded_plan(prepare_emlis_meaning(req))
    assert not any(c.startswith('thread_subject:distinct_source_occurrence:')
                   for n in plan.nuclei for c in n.semantic_frame.attribute_codes)


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('events', [
    ('誘われた', '誘われた', '誘われた'),
    ('私は誘われた', '私は誘われた', '私は誘われた'),
    ('私は誘われた', '自分は誘われた', '私は誘われた'),
    ('褒められた', '誘われた', '頼まれた'),
])
def test_split_positive_answer_duties_keep_each_source_in_its_own_sentence(field, events):
    memo = ''.join(e + 'のに、' + f + '。' for e, f in zip(events,
        ('嬉しくなかった', '悲しかった', '寂しかった'), strict=True))
    sources = ('少し私は少し安心なのです', '私も幸せだったのです', '私は安心なのだった')
    req = begin(memo if field == 'memo' else '', memo if field == 'memo_action' else '')
    for when, source in zip(('今は', 'その時は', '今は'), sources, strict=True):
        req = advance(req, when + source + '。')
    context = actual(request=req)
    result, plan, sentence, _, _ = context
    body, follow = result.artifact.text, result.artifact.reception
    reception_plan = plan.response_plan.human_reception_plan
    assert len(reception_plan.moves) == reception_plan.depth_policy.max_sentences == 3
    assert follow.count('。') == 3
    assert all(s in follow for s in ('嬉し', '悲し', '寂し'))
    assert all(s in result.artifact.observation for s in sources)
    with patch.object(reception, '_source_owned_positive_answer_group_sentence', side_effect=AssertionError('no group author')), patch.object(
            reception, '_source_owned_answer_feeling_sentence', side_effect=AssertionError('no single author')), patch.object(
            reception, '_detached_feeling_finite_surface', side_effect=AssertionError('no finite author')):
        raw, proof = split_positive_answer_proof(context)
        assert proof is not None and len(proof) == 6
        assert [source.decode() for _, _, source in proof] == [x for pair in zip(events, sources, strict=True) for x in pair]
        assert read_body(context, body).passed
        first, last, empty = raw.split('。')
        assert not empty and first.count('し、') == 1 and 'し、' not in last
        assert 'その時はあなたも幸せだったのですね' in first
        assert '回答した時点ではあなたは安心なのでしたね' in last
        for changed in (last + '。' + first + '。', first + '。', last + '。',
                        first + '、' + last + '。',
                        raw.replace('その時は', '回答した時点では', 1),
                        raw.replace('あなたも', 'あなたは', 1),
                        raw.replace('幸せだったのですね', '幸せなのでしたね'),
                        raw.replace('少しあなたは少し', 'あなたは少し少し'),
                        raw.replace('安心なのでしたね', '安心なのですね')):
            assert changed != raw
            assert not read_body(context, body.replace(raw, changed, 1)).passed
    line, = (line for line in sentence.lines if line.binding.line_role == 'human_follow')
    assert len(line.reception_clause_plans) == 3
    assert len({mid for clause in line.reception_clause_plans for mid in clause.move_ids}) == 3


@pytest.mark.parametrize('style', ['shared', 'qualified', 'unqualified'])
def test_split_positive_answer_legacy_three_group_reader_and_saved_body(qcase, qdb, monkeypatch, style):
    import emlis_ai_grounded_observation_plan as gp
    current_groups = gp._thread_retained_reaction_groups
    author = reception._source_owned_positive_answer_group_sentence
    def legacy_groups(*args, **kwargs):
        groups = current_groups(*args, **kwargs)
        if (len(groups) == 3 and groups[0][0] == 'current_burden'
            and groups[1][0] == groups[2][0] == 'lived_change'
            and len(groups[1][1]) == 2 and len(groups[2][1]) == 1
            and not groups[1][2] and not groups[2][2]):
            return (groups[0], ('lived_change', groups[1][1] + groups[2][1], ()))
        return groups
    def legacy_surface(*args, **kwargs):
        text = author(*args, **kwargs)
        topic = '誘われたことについて、'
        if style != 'shared' and text and text.startswith(topic + RECORD_PREFIXES[0]):
            text = text[len(topic):]
            for label in RECORD_PREFIXES:
                text = text.replace(label, label + topic, 1)
            if style == 'unqualified':
                for label in RECORD_PREFIXES:
                    text = text.replace(label, '')
        return text
    user, parent, _ = qcase
    service = active(monkeypatch)
    qdb.query('update public.emotions set memo=$1 where id=$2', [EXACT_RECORD_MEMO, parent])
    replies = (*TWO_POSITIVE_PAIRS[0], '今は安心なのです。')
    with monkeypatch.context() as old:
        old.setattr(gp, '_thread_retained_reaction_groups', legacy_groups)
        old.setattr(reception, '_source_owned_positive_answer_group_sentence', legacy_surface)
        req = begin(EXACT_RECORD_MEMO)
        first = current = run(service.start(user, parent))
        for index, reply in enumerate(replies):
            req = advance(req, reply)
            if index:
                current = run(cont(service, user, current, f'old-three-continue-{index}'))
            current = run(answer(service, user, current, reply, f'old-three-answer-{index}'))
            assert current['original'] == first['original']
        legacy_context = actual(request=req)
    result, plan, _, resolver, selected = legacy_context
    assert len(plan.response_plan.human_reception_plan.moves) == 2
    assert result.artifact.reception.count('。') == 2
    move, = (m for m in plan.response_plan.human_reception_plan.moves if m.reception_act == 'recognize_lived_change')
    assert len(move.target_nucleus_ids) == 3
    raw = result.artifact.reception.split('。')[1] + '。'
    assert raw.count('誘われたことについて、') == (1 if style == 'shared' else 3)
    assert all(raw.count(label) == (0 if style == 'unqualified' else 1) for label in RECORD_PREFIXES)
    with patch.object(reception, '_source_owned_positive_answer_group_sentence', side_effect=AssertionError('no legacy author')), patch.object(
            reception, '_detached_feeling_finite_surface', side_effect=AssertionError('no legacy finite')):
        proof = gate.read_source_owned_discourse(raw, move, plan, resolver, selected)
        assert proof is not None and len(proof) == 6
        assert [source.decode() for _, _, source in proof] == [
            '誘われた', '嬉しい', '誘われた', '楽しかった', '誘われた', '安心なのです']
        assert all(raw.encode()[a:b] for a, b, _ in proof)
        for old, new in [('楽しかった', '嬉しかった'), ('その時は', '回答した時点では'),
                         ('安心なのですね', '安心だったのですね')]:
            assert gate.read_source_owned_discourse(raw.replace(old, new, 1), move, plan, resolver, selected) is None
    saved_follow = current['current_observation']['text'].split('Emlisから：', 1)[1]
    assert saved_follow.count('。') == 2
    saved_answer = saved_follow.split('。')[1]
    assert saved_answer.count('誘われたことについて、') == (1 if style == 'shared' else 3)
    assert all(saved_answer.count(label) == (0 if style == 'unqualified' else 1) for label in RECORD_PREFIXES)
    with monkeypatch.context() as saved:
        saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('legacy saved body must not regenerate'))
        assert run(service.get(user, parent)) == run(service.start(user, parent)) == current
    assert qdb.query('select memo from public.emotions where id=$1', [parent])['rows'][0]['memo'] == EXACT_RECORD_MEMO
