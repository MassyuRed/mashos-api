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
    request = begin('褒められたのに、悲しかった。誘われたのに、悲しかった。頼まれたのに、寂しかった。')
    request = advance(advance(request, WITHDRAW), '「誘われた」は誤りです。')
    context = actual(request=request)
    _, plan, _, resolver, _ = context
    clauses = reception.build_grounded_reception_clause_plans(
        plan.response_plan.human_reception_plan, 'full', plan=plan, resolver=resolver)
    assert all(len(c.move_ids) == 1 for c in clauses)
    assert context[0].artifact.reception.count('その時は悲しかった') == 2


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
