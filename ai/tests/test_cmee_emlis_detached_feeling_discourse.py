"""Withdrawal leaves independent, timed feelings in the shared response."""
from dataclasses import replace
import pytest

import emlis_ai_grounded_human_reception as reception
import emlis_ai_grounded_observation_gate as gate
from test_cmee_emlis_received_discourse import actual, inverse
from test_cmee_emlis_q1_thread import initial, answered
from test_cmee_emlis_q3_thread import begin, advance, MEMO
from test_emlis_q3_application import qdb, qcase, cont
from test_emlis_q2_application import run, answer

WITHDRAW = '「褒められた」は誤りです。'


@pytest.fixture(scope='module')
def paired():
    return actual(request=advance(advance(begin(), '今は怖くない。'), WITHDRAW))


def test_adjacent_duties_share_a_sentence_without_losing_contributions(paired):
    result, plan, sentence, resolver, selected = paired
    follow = result.artifact.reception
    assert follow.startswith('その時は嬉しくなかったし、回答した時点では怖くないのですね。')
    assert follow.count('。') == 2 and '受け止めています' not in follow
    assert '誘われたのに、悲しさを感じ、頼まれたのに、寂しさを感じた' in follow
    assert '褒められた' not in result.artifact.text
    moves = reception.reception_active_moves(plan.response_plan.human_reception_plan, 'full')
    clauses = reception.build_grounded_reception_clause_plans(
        plan.response_plan.human_reception_plan, 'full', plan=plan, resolver=resolver)
    assert tuple(mid for c in clauses for mid in c.move_ids) == tuple(m.move_id for m in moves)
    refs = [set(d.selected_contribution_refs) for d in selected.decisions]
    assert sum(map(len, refs)) == len(set().union(*refs))
    assert set().union(*refs) == set(selected.decisions[0].subjective_proposition.target_contribution_refs)
    assert inverse(paired, follow, without_author=True).passed


@pytest.mark.parametrize('old,new', [
    ('嬉しくなかった', '嬉しかった'), ('嬉しくなかった', '嬉しくない'),
    ('その時は', '回答した時点では'), ('回答した時点では', 'その時は'),
    ('回答した時点では', ''), ('怖くない', '怖い'),
    ('怖くない', '怖くなかった'), ('し、', 'ので、'),
    ('し、', 'のに、'), ('し、', 'し、そのため'),
    ('その時は', 'その時は友人が'), ('嬉しくなかった', '「嬉しくなかった」'),
    ('その時は', '褒められた時は'), ('し、回答した時点では怖くない', ''),
])
def test_changed_complete_meaning_fails_without_author(paired, old, new):
    follow = paired[0].artifact.reception
    changed = follow.replace(old, new, 1)
    assert changed != follow
    assert not inverse(paired, changed, without_author=True).passed


@pytest.mark.parametrize('ending', ['のです。', 'のだと受け取りました。'])
def test_equal_reading_is_not_bound_to_author_suffix(paired, ending):
    follow = paired[0].artifact.reception.replace('のですね。', ending)
    assert inverse(paired, follow).passed


@pytest.mark.parametrize('field,value', [('actor', 'other_person'), ('polarity', 'positive')])
def test_reader_requires_the_source_owner_and_polarity(paired, field, value):
    result, plan, _, resolver, selected = paired
    moves = reception.reception_active_moves(plan.response_plan.human_reception_plan, 'full')[:2]
    target = moves[0].target_nucleus_ids[0]
    changed = replace(plan, nuclei=tuple(replace(n, semantic_frame=replace(n.semantic_frame, **{field:value}))
                      if n.nucleus_id == target else n for n in plan.nuclei))
    clause = result.artifact.reception.split('。')[0] + '。'
    assert gate.read_detached_feeling_pair(clause, moves, changed, resolver, selected) is None


@pytest.mark.parametrize('count', [1, 2, 3])
@pytest.mark.parametrize('q3', [False, True])
def test_single_detached_original_keeps_other_event_pairs(count, q3):
    memo = '。'.join(MEMO.split('。')[:count]) + '。'
    request = advance(begin(memo), WITHDRAW) if q3 else answered(WITHDRAW, initial(memo))
    context = actual(request=request)
    follow = context[0].artifact.reception
    assert 'その時は嬉しくなかったのですね。' in follow
    assert '褒められた' not in context[0].artifact.text
    for event in ('誘われた', '頼まれた')[:count-1]:
        assert event in follow
    assert inverse(context, follow, without_author=True).passed


@pytest.mark.parametrize('prior', ['その時は重かった。', '今は嬉しい。'])
def test_past_and_nonadjacent_positive_answer_keep_their_times(prior):
    context = actual(request=advance(advance(begin(), prior), WITHDRAW))
    follow = context[0].artifact.reception
    expected = 'その時は重かった' if prior.startswith('その時') else '回答した時点では嬉しい'
    assert expected in follow and 'その時は嬉しくなかった' in follow
    assert '褒められた' not in context[0].artifact.text
    assert inverse(context, follow, without_author=True).passed


@pytest.mark.parametrize('prior', ['その時は重かったです。', 'その時は私は重かった。'])
def test_uncomposable_source_keeps_singleton_topology(prior):
    context = actual(request=advance(advance(begin(), prior), WITHDRAW))
    _, plan, _, resolver, _ = context
    clauses = reception.build_grounded_reception_clause_plans(
        plan.response_plan.human_reception_plan, 'full', plan=plan, resolver=resolver)
    assert all(len(c.move_ids) == 1 for c in clauses)
    assert inverse(context, context[0].artifact.reception, without_author=True).passed


def test_same_source_on_different_events_is_not_coordinated():
    # Keep this historical case's identity; distinct duties can now share
    # their predicate only with an explicit acknowledgement of both mentions.
    request = begin('褒められたのに、悲しかった。誘われたのに、悲しかった。頼まれたのに、寂しかった。')
    request = advance(advance(request, WITHDRAW), '「誘われた」は誤りです。')
    context = actual(request=request)
    _, plan, _, resolver, _ = context
    clauses = reception.build_grounded_reception_clause_plans(
        plan.response_plan.human_reception_plan, 'full', plan=plan, resolver=resolver)
    assert tuple(len(c.move_ids) for c in clauses) == (2, 1)
    assert context[0].artifact.reception.count('その時は悲しかった') == 1
    assert 'という気持ちを、どちらの言葉からも受け取りました。' in context[0].artifact.reception
    assert inverse(context, context[0].artifact.reception, without_author=True).passed


def test_correction_of_detached_answer_keeps_earlier_answer_time():
    request = advance(advance(begin(), '今は重い。'), WITHDRAW)
    context = actual(request=advance(request, '「重い」ではなく「苦しい」です。'))
    follow = context[0].artifact.reception
    assert '先の回答時点では苦しい' in follow and '重い' not in follow
    assert '褒められた' not in context[0].artifact.text
    assert inverse(context, follow, without_author=True).passed


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
def test_withdrawal_body_is_saved_and_get_never_rerenders(qcase, qdb, tier, monkeypatch):
    user, parent, service = qcase
    qdb.query('update public.profiles set subscription_tier=$1 where id=$2', [tier, user])
    first = run(service.start(user, parent))
    current = run(answer(service, user, first, WITHDRAW))
    assert current['current_observation'] is not None
    assert 'その時は嬉しくなかったのですね。' in current['current_observation']['text']
    assert current['original'] == first['original']
    monkeypatch.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved GET must not render'))
    assert run(service.get(user, parent)) == current
    assert run(service.start(user, parent)) == current


def test_paired_body_survives_personal_continue_and_saved_restart(qcase, qdb, monkeypatch):
    user, parent, service = qcase
    first = run(service.start(user, parent))
    current = run(answer(service, user, first, '今は怖くない。'))
    current = run(cont(service, user, current, 'continue-withdrawal'))
    current = run(answer(service, user, current, WITHDRAW, 'withdraw-event'))
    assert '嬉しくなかったし、回答した時点では怖くないのですね。' in current['current_observation']['text']
    assert current['original'] == first['original']
    monkeypatch.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved restart must not render'))
    assert run(service.get(user, parent)) == current
    assert run(service.start(user, parent)) == current


def repeated_mentions_context(source='悲しかった', start=0):
    events = ('褒められた', '誘われた', '頼まれた')
    feelings = ['寂しかった'] * 3
    feelings[start:start + 2] = [source, source]
    request = begin('。'.join(event + 'のに、' + feeling
                             for event, feeling in zip(events, feelings)) + '。')
    withdrawn = events[start:start + 2]
    # Preserve this historical sequence. Middle-first delivery has its own
    # immediate and subsequent-state checks below.
    for event in reversed(withdrawn) if start else withdrawn:
        request = advance(request, '「' + event + '」は誤りです。')
    return actual(request=request)


@pytest.mark.parametrize('source', ['悲しかった', '嬉しくなかった', '寂しかった',
    '怖かった', '少し悲しかった', '悲しくなかった', 'とても寂しかった'])
@pytest.mark.parametrize('start', [0, 1])
def test_repeated_mentions_keep_two_duties_in_one_complete_predicate(source, start):
    context = repeated_mentions_context(source, start)
    result, plan, _, resolver, selected = context
    follow = result.artifact.reception
    shared = 'その時は' + source + 'という気持ちを、どちらの言葉からも受け取りました。'
    assert shared in follow and follow.count(source) == 1
    assert follow.count('。') == 2
    moves = reception.reception_active_moves(plan.response_plan.human_reception_plan, 'full')
    clauses = reception.build_grounded_reception_clause_plans(
        plan.response_plan.human_reception_plan, 'full', plan=plan, resolver=resolver)
    assert tuple(mid for clause in clauses for mid in clause.move_ids) == tuple(m.move_id for m in moves)
    assert sorted(len(c.move_ids) for c in clauses) == [1, 2]
    refs = [set(d.selected_contribution_refs) for d in selected.decisions]
    assert all(refs) and sum(map(len, refs)) == len(set().union(*refs))
    assert set().union(*refs) == set(selected.decisions[0].subjective_proposition.target_contribution_refs)
    pair_ids = next(c.move_ids for c in clauses if len(c.move_ids) == 2)
    pair = tuple(next(m for m in moves if m.move_id == mid) for mid in pair_ids)
    assert pair[0].target_nucleus_ids != pair[1].target_nucleus_ids
    assert not set(pair[0].source_evidence_span_ids) & set(pair[1].source_evidence_span_ids)
    proof = gate.read_detached_feeling_pair(shared, pair, plan, resolver, selected)
    assert proof is not None and len(proof) == 2
    for part in proof:
        assert len(part) == 1
        a, b, original = part[0]
        assert shared.encode()[a:b].decode() == source
        assert original.decode() == source
    for event in ('褒められた', '誘われた', '頼まれた')[start:start + 2]:
        assert event not in result.artifact.text
    remaining = '頼まれた' if start == 0 else '褒められた'
    assert remaining + 'のに、寂しさを感じた' in follow
    assert inverse(context, follow, without_author=True).passed


@pytest.fixture(scope='module')
def repeated_mentions():
    return repeated_mentions_context('少し悲しかった')


@pytest.mark.parametrize('old,new', [
    ('どちらの言葉からも', '一方の言葉から'), ('どちらの言葉からも', ''),
    ('どちらの言葉からも', '三つの言葉から'), ('どちらの言葉からも', 'どちらの出来事からも'),
    ('その時は', '回答した時点では'), ('その時は', ''),
    ('少し悲しかった', '悲しかった'), ('少し悲しかった', 'とても悲しかった'),
    ('少し悲しかった', '少し悲しくなかった'), ('少し悲しかった', '少し悲しい'),
    ('その時は', 'その時は友人が'), ('その時は', '褒められた時は'),
    ('という気持ちを、', 'から、'), ('という気持ちを、', 'という気持ちがずっと続き、'),
    ('頼まれたのに、寂しさを感じたのですね。', ''),
])
def test_repeated_mentions_reject_missing_or_invented_meaning(repeated_mentions, old, new):
    follow = repeated_mentions[0].artifact.reception
    changed = follow.replace(old, new, 1)
    assert changed != follow
    assert not inverse(repeated_mentions, changed, without_author=True).passed


@pytest.mark.parametrize('change', ['actor', 'polarity', 'source_alias', 'same_move', 'same_evidence'])
def test_repeated_mentions_reader_requires_two_independent_sources(repeated_mentions, change):
    result, plan, _, resolver, selected = repeated_mentions
    moves = reception.reception_active_moves(plan.response_plan.human_reception_plan, 'full')[:2]
    target = moves[1].target_nucleus_ids[0]
    source = next(n for n in plan.nuclei if n.nucleus_id == moves[0].target_nucleus_ids[0])
    if change in {'actor', 'polarity'}:
        field, value = ('actor', 'other_person') if change == 'actor' else ('polarity', 'positive')
        plan = replace(plan, nuclei=tuple(replace(n, semantic_frame=replace(n.semantic_frame, **{field:value}))
                                         if n.nucleus_id == target else n for n in plan.nuclei))
    elif change == 'source_alias':
        plan = replace(plan, nuclei=tuple(replace(n, source_span_ids=source.source_span_ids)
                                         if n.nucleus_id == target else n for n in plan.nuclei))
    elif change == 'same_move':
        moves = (moves[0], moves[0])
    else:
        moves = (moves[0], replace(moves[1], source_evidence_span_ids=moves[0].source_evidence_span_ids))
    raw = result.artifact.reception.split('。')[0] + '。'
    assert gate.read_detached_feeling_pair(raw, moves, plan, resolver, selected) is None


def test_repeated_mentions_three_equal_sources_do_not_become_two():
    request = begin('褒められたのに、悲しかった。誘われたのに、悲しかった。頼まれたのに、悲しかった。')
    for event in ('褒められた', '誘われた', '頼まれた'):
        request = advance(request, '「' + event + '」は誤りです。')
    context = actual(request=request)
    result, plan, _, resolver, selected = context
    assert 'どちらの言葉' not in result.artifact.reception
    moves = reception.reception_active_moves(plan.response_plan.human_reception_plan, 'full')
    assert len(moves) == 3
    assert gate.read_detached_feeling_pair(
        'その時は悲しかったという気持ちを、どちらの言葉からも受け取りました。',
        moves[:2], plan, resolver, selected) is None
    assert inverse(context, result.artifact.reception, without_author=True).passed


@pytest.mark.parametrize('occasion', ['今は', 'その時は'])
@pytest.mark.parametrize('source', ['嬉しくなかった', '嬉しくなかったです'])
def test_repeated_mentions_different_source_times_do_not_share_predicate(occasion, source):
    request = advance(advance(begin(), occasion + '怖かった。'), WITHDRAW)
    request = advance(request, '「怖かった」ではなく「' + source + '」です。')
    context = actual(request=request)
    result, plan, _, resolver, selected = context
    follow = result.artifact.reception
    if occasion == 'その時は':
        assert 'その時は嬉しくなかったという気持ちを、どちらの言葉からも受け取りました。' in follow
        moves = reception.reception_active_moves(plan.response_plan.human_reception_plan, 'full')[:2]
        raw = follow.split('。')[0] + '。'
        proof = gate.read_detached_feeling_pair(raw, moves, plan, resolver, selected)
        assert proof is not None
        assert tuple(part[0][2].decode() for part in proof) == ('嬉しくなかった', source)
        assert all(raw.encode()[part[0][0]:part[0][1]].decode() == '嬉しくなかった' for part in proof)
    else:
        assert 'どちらの言葉' not in follow
        assert 'その時は嬉しくなかった' in follow and '先の回答時点では嬉しくなかった' in follow
        moves = reception.reception_active_moves(plan.response_plan.human_reception_plan, 'full')[:2]
        assert gate.read_detached_feeling_pair(
            'その時は嬉しくなかったという気持ちを、どちらの言葉からも受け取りました。',
            moves, plan, resolver, selected) is None
    assert inverse(context, follow, without_author=True).passed


@pytest.mark.parametrize('route', ['two_memo', 'answer_correction', 'answer_withdrawal'])
def test_repeated_mentions_saved_operations_and_authorless_reopen(qcase, qdb, route, monkeypatch):
    user, parent, service = qcase
    if route == 'two_memo':
        qdb.query('update public.emotions set memo=$1 where id=$2', [
            '褒められたのに、悲しかった。誘われたのに、悲しかった。頼まれたのに、寂しかった。', parent])
        steps = (WITHDRAW, '「誘われた」は誤りです。', '「頼まれた」は誤りです。')
    else:
        steps = ('その時は怖かった。', WITHDRAW,
                 '「怖かった」ではなく「嬉しくなかった」です。' if route == 'answer_correction'
                 else '「怖かった」は誤りです。')
    first = current = run(service.start(user, parent))
    for index, text in enumerate(steps):
        if index:
            current = run(cont(service, user, current, 'continue-repeated-' + str(index)))
        current = run(answer(service, user, current, text, 'answer-repeated-' + str(index)))
        body = current['current_observation']['text']
        assert current['original'] == first['original']
        if route == 'two_memo' and index == 1 or route == 'answer_correction' and index == 2:
            assert 'という気持ちを、どちらの言葉からも受け取りました。' in body
        if route == 'two_memo' and index == 2:
            # The unchanged Move order separates the equal duties after all
            # events are withdrawn. Do not claim this topology is repaired.
            assert 'どちらの言葉' not in body
            assert body.split('Emlisから：', 1)[1].count('悲しかった') == 2
            assert 'その時は寂しかったのですね。' in body
        if route != 'two_memo' and index == 2:
            assert '怖かった' not in body
            assert '誘われた' in body and '頼まれた' in body
        if route == 'answer_withdrawal' and index == 2:
            assert 'どちらの言葉' not in body
        with monkeypatch.context() as stopped:
            stopped.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved read generated'))
            assert run(service.get(user, parent)) == current
            assert run(service.start(user, parent)) == current


MIDDLE_FEELINGS = ('悲しかった', '嬉しくなかった', '寂しかった', '怖かった',
                   '少し悲しかった', '悲しくなかった', 'とても寂しかった')
EVENTS = ('褒められた', '誘われた', '頼まれた')


def middle_request(source='少し悲しかった', position=1):
    memo = f'褒められたのに、嬉しくなかった。誘われたのに、{source}。頼まれたのに、{source}。'
    return advance(begin(memo), f'「{EVENTS[position]}」は誤りです。')


@pytest.mark.parametrize('source', MIDDLE_FEELINGS)
@pytest.mark.parametrize('position', [0, 1, 2])
def test_withdrawal_at_each_position_delivers_all_surviving_pairs(source, position):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning
    from test_cmee_emlis_detached_observation import read_body
    request = middle_request(source, position)
    public = MeaningExperienceEngine().generate(request)
    assert public.artifact is not None, public.reason_codes
    context = actual(request=request)
    result, plan, sentence, _, selected = context
    assert result.artifact.text == public.artifact.text
    assert EVENTS[position] not in result.artifact.text
    ids = set(plan.coverage_requirements.required_nucleus_ids)
    withdrawn = f'nucleus:s{position + 1}:event'
    assert withdrawn not in ids
    assert f'nucleus:s{position + 1}:reaction' in ids
    assert withdrawn in prepare_emlis_meaning(request).checkpoint.inactive_claim_refs
    observation = [line for line in sentence.lines if line.binding.line_role != 'human_follow']
    detached = next(line for line in observation if not line.binding.relation_ids)
    assert detached.binding.nucleus_ids == (f'nucleus:s{position + 1}:reaction',)
    pairs = next(line for line in observation if line.binding.relation_ids)
    remaining = [i for i in range(3) if i != position]
    assert len(observation) == 2 and len(pairs.binding.relation_ids) == 2
    assert pairs.binding.nucleus_ids == tuple(
        f'nucleus:s{i + 1}:{kind}' for i in remaining for kind in ('event', 'reaction'))
    for i in remaining:
        assert EVENTS[i] in result.artifact.observation and EVENTS[i] in result.artifact.reception
    moves = reception.reception_active_moves(plan.response_plan.human_reception_plan, 'full')
    assert len(moves) == 2
    refs = [set(d.selected_contribution_refs) for d in selected.decisions]
    assert all(refs) and sum(map(len, refs)) == len(set().union(*refs))
    assert read_body(context, result.artifact.text).passed


@pytest.mark.parametrize('source', MIDDLE_FEELINGS)
def test_middle_first_then_last_keeps_both_detached_mentions(source):
    from test_cmee_emlis_detached_observation import read_body
    request = middle_request(source)
    first = actual(request=request)
    assert f'その時は{source}のですね。' in first[0].artifact.reception
    context = actual(request=advance(request, '「頼まれた」は誤りです。'))
    body = context[0].artifact.text
    assert '誘われた' not in body and '頼まれた' not in body
    assert f'その時は{source}という気持ちを、どちらの言葉からも受け取りました。' in body
    assert '褒められた' in context[0].artifact.observation
    assert '褒められた' in context[0].artifact.reception
    assert read_body(context, body).passed


def test_middle_withdrawal_with_distinct_feelings_retains_their_owners():
    from test_cmee_emlis_detached_observation import read_body
    context = actual(request=advance(begin(), '「誘われた」は誤りです。'))
    body = context[0].artifact.text
    assert '「褒められた」の一方で「嬉しくなかった」' in body
    assert '「頼まれた」の一方で「寂しかった」' in body
    assert 'その時の気持ちとして、「悲しかった」' in body
    assert read_body(context, body).passed


def test_middle_withdrawal_keeps_an_answer_owned_by_the_first_event():
    from test_cmee_emlis_detached_observation import read_body
    request = advance(advance(begin(), '今は重い。'), '「誘われた」は誤りです。')
    context = actual(request=request)
    body = context[0].artifact.text
    assert '「褒められた」一方で「嬉しくなかった」とあり、' in body
    assert 'その出来事について、回答した時点の受け止めは「重い」' in body
    assert '褒められた時は嬉しくなく、回答した時点では重い' in context[0].artifact.reception
    assert 'その時は悲しかった' in body and '誘われた' not in body
    assert read_body(context, body).passed


@pytest.mark.parametrize('old,new', [
    ('「嬉しくなかった」', '「嬉しかった」'),
    ('「少し悲しかった」', '「悲しかった」'),
    ('「少し悲しかった」', '「少し悲しい」'),
    ('「頼まれた」', '「誘われた」'),
    ('その時の気持ちとして、', '回答した時点の気持ちとして、'),
    ('その時の気持ちとして、', '頼まれた時の気持ちとして、'),
    ('その時の気持ちとして、「少し悲しかった」が見えます。', ''),
    ('「褒められた」の一方で「嬉しくなかった」、また「頼まれた」の一方で「少し悲しかった」',
     '「褒められた」の一方で「少し悲しかった」、また「頼まれた」の一方で「嬉しくなかった」'),
    ('その時は少し悲しかったのですね。', ''),
    ('その時は少し悲しかった', '頼まれた時は少し悲しかった'),
])
def test_middle_withdrawal_rejects_changed_meaning_without_either_author(old, new):
    from test_cmee_emlis_detached_observation import read_body
    context = actual(request=middle_request())
    body = context[0].artifact.text
    changed = body.replace(old, new, 1)
    assert changed != body
    assert not read_body(context, changed).passed


@pytest.mark.parametrize('route', ['middle_then_last', 'correct_reaction', 'withdraw_reaction'])
def test_middle_first_saved_series_never_replaces_original_or_renders_on_read(qcase, qdb, monkeypatch, route):
    user, parent, service = qcase
    if route == 'middle_then_last':
        qdb.query('update public.emotions set memo=$1 where id=$2',
                 ['褒められたのに、嬉しくなかった。誘われたのに、少し悲しかった。頼まれたのに、少し悲しかった。', parent])
        answers = ('「誘われた」は誤りです。', '「頼まれた」は誤りです。')
    else:
        answers = ('「誘われた」は誤りです。', '「悲しかった」ではなく「怖かった」です。'
                   if route == 'correct_reaction' else '「悲しかった」は誤りです。')
    first = current = run(service.start(user, parent))
    bodies = []
    for index, text in enumerate(answers):
        if index:
            current = run(cont(service, user, current, f'middle-continue-{index}'))
        current = run(answer(service, user, current, text, f'middle-answer-{index}'))
        assert current['body_state'] == 'REFINED', current
        assert current['current_observation'] is not None
        body = current['current_observation']['text']
        assert '誘われた' not in body and '褒められた' in body
        assert current['original'] == first['original']
        assert body not in bodies
        bodies.append(body)
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved read must not render'))
            assert run(service.get(user, parent)) == current
            assert run(service.start(user, parent)) == current
    if route == 'middle_then_last':
        assert '頼まれた' not in bodies[-1] and 'どちらの言葉からも' in bodies[-1]
    elif route == 'correct_reaction':
        assert 'その時は悲しかった' in bodies[0]
        assert '怖かった' in bodies[1] and '悲しかった' not in bodies[1]
        assert current['state'] == 'COMPLETED' and not current['can_continue']
    else:
        assert 'その時は悲しかった' in bodies[0] and '悲しかった' not in bodies[1]


def test_middle_observation_accepts_an_equivalent_ending_without_either_author():
    from test_cmee_emlis_detached_observation import read_body
    context = actual(request=middle_request())
    body = context[0].artifact.text.replace('が見えます。', 'が読み取れます。')
    assert body != context[0].artifact.text
    assert read_body(context, body).passed
