"""Shared past-change context, authored once and read from adjacent body bytes.

All examples are extensions of the existing public synthetic plant scenario.
They are not private evaluation inputs. Existing frozen expectations stay intact.
"""

from helpers.retained_assertions import continue_assertions, retained_assertion
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from test_cmee_emlis_q3_thread import (
    ACTION_CHANGE_CONTRAST_MEMO, begin, initial, prepare_emlis_meaning,
    build_updated_grounded_plan, realize_emlis_thread_body, project_thread_meaning,
)
import emlis_ai_grounded_sentence_surface as surface
from emlis_ai_grounded_observation_gate import evaluate_grounded_surface_body_inverse


FUTURE = '明日、棚を動かす。'
CHANGE = '机の上が広くなってうれしかった'
CONTINUATIONS = (
    ACTION_CHANGE_CONTRAST_MEMO.replace('いつも', 'ずっと'),
    ACTION_CHANGE_CONTRAST_MEMO.replace('いつも見ていた', '見続けていた'),
)


def _actual(memo=CONTINUATIONS[0], *, premium=True, ending='まだ配置は見つかっていない。'):
    request = (begin if premium else initial)(memo + ending, FUTURE)
    prepared = prepare_emlis_meaning(request)
    plan = build_updated_grounded_plan(prepared)
    result = realize_emlis_thread_body(prepared)
    assert result.artifact, result.reason_codes
    resolver = prepared.thread.resolver()
    selected = project_thread_meaning(prepared, plan).selected_reception
    sentence = surface.build_grounded_sentence_plan(plan, resolver, recovery_stage='full')
    return result, plan, sentence, resolver, selected


@pytest.mark.parametrize('premium', [False, True])
@pytest.mark.parametrize('memo', CONTINUATIONS)
@pytest.mark.parametrize('ending', ['まだ配置は見つかっていない。', 'まだ配置は見つかっていません。'])
@continue_assertions
def test_continuing_contrast_refers_to_one_complete_preceding_change(premium, memo, ending):
    result, plan, sentence, resolver, selected = _actual(memo, premium=premium, ending=ending)
    follow = result.artifact.reception
    first, second, last, empty = follow.split('。')
    retained_assertion(lambda: (not empty), 'not empty')
    retained_assertion(lambda: (first == '窓辺の鉢を棚へ移したことが' + CHANGE + 'ことを支えていることを見過ごさず、大切に思っています'), "first == '窓辺の鉢を棚へ移したことが' + CHANGE + 'ことを支えていることを見過ごさず、大切に思っています'")
    retained_assertion(lambda: (second.startswith('その一方で、')), "second.startswith('その一方で、')")
    retained_assertion(lambda: (follow.count(CHANGE) == 1), 'follow.count(CHANGE) == 1')
    retained_assertion(lambda: (memo.split('一方で、')[1].rstrip('。') in second), "memo.split('一方で、')[1].rstrip('。') in second")
    retained_assertion(lambda: (second.endswith('ことを見過ごさず、小さくせずに受け止めています')), "second.endswith('ことを見過ごさず、小さくせずに受け止めています')")
    retained_assertion(lambda: (ending[:-1] in last), 'ending[:-1] in last')
    retained_assertion(lambda: (len(plan.response_plan.human_reception_plan.moves) == 3), 'len(plan.response_plan.human_reception_plan.moves) == 3')
    inverse = evaluate_grounded_surface_body_inverse(body=result.artifact.text.encode(), plan=plan,
        sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected)
    retained_assertion(lambda: (inverse.passed), 'inverse.passed', lambda: (inverse.failure_codes))


@pytest.mark.parametrize('premium', [False, True])
def test_unqualified_current_scope_keeps_the_existing_explicit_contrast(premium):
    result, *_ = _actual(ACTION_CHANGE_CONTRAST_MEMO, premium=premium)
    follow = result.artifact.reception
    assert 'その一方で、' not in follow
    assert follow.count(CHANGE) == 2
    assert CHANGE + '一方で、いつも見ていた葉' in follow


@pytest.fixture
def actual_context():
    return _actual()


def _independent_passes(context, changed):
    result, plan, sentence, resolver, selected = context
    original = result.artifact.reception
    # An echoing replay cannot make the independent body proof pass.
    with patch('emlis_ai_grounded_observation_gate.replay_source_grounded_human_reception_from_plan',
               return_value=SimpleNamespace(text=changed)), patch(
               'emlis_ai_grounded_human_reception._author_source_grounded_reception_clauses',
               side_effect=AssertionError('independent inverse must not replay the author')):
        return evaluate_grounded_surface_body_inverse(
            body=result.artifact.text.replace(original, changed).encode(), plan=plan,
            sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected).passed


def test_independent_body_read_accepts_the_complete_actual_antecedent(actual_context):
    assert _independent_passes(actual_context, actual_context[0].artifact.reception)


@pytest.mark.parametrize('mutation', [
    'remove_first', 'remove_change', 'replace_change', 'change_actor', 'future_action',
    'negate_change', 'past_change_to_present', 'reverse_support', 'remove_connector',
    'wrong_connector', 'negate_burden', 'past_burden', 'remove_burden_context',
    'quoted_antecedent', 'remove_attention', 'insert_unrelated_sentence',
])
@continue_assertions
def test_independent_body_read_rejects_missing_or_changed_adjacent_meaning(actual_context, mutation):
    follow = actual_context[0].artifact.reception
    first, second, last, _ = follow.split('。')
    if mutation == 'remove_first': first = ''
    elif mutation == 'remove_change': first = first.replace(CHANGE, '')
    elif mutation == 'replace_change': first = first.replace(CHANGE, '机がきれいだった')
    elif mutation == 'change_actor': first = '弟が' + first
    elif mutation == 'future_action': first = first.replace('棚へ移したこと', '棚へ移すこと')
    elif mutation == 'negate_change': first = first.replace('うれしかった', 'うれしくなかった')
    elif mutation == 'past_change_to_present': first = first.replace('うれしかった', 'うれしい')
    elif mutation == 'reverse_support': first = first.replace('ことが', 'ことを', 1).replace('ことを支えて', 'ことが支えて', 1)
    elif mutation == 'remove_connector': second = second.replace('その一方で、', '')
    elif mutation == 'wrong_connector': second = second.replace('その一方で、', 'そのため、')
    elif mutation == 'negate_burden': second = second.replace('寂しさも残っている', '寂しさは残っていない')
    elif mutation == 'past_burden': second = second.replace('寂しさも残っている', '寂しさも残っていた')
    elif mutation == 'remove_burden_context': second = second.replace('ずっと見ていた葉が遠くなり、', '')
    elif mutation == 'quoted_antecedent': first = '「' + first + '」'
    elif mutation == 'remove_attention': first = first.replace('を見過ごさず、', 'を')
    elif mutation == 'insert_unrelated_sentence': first += '。お茶を飲みました'
    changed = '。'.join(x for x in (first, second, last) if x) + '。'
    retained_assertion(lambda: (changed != follow), 'changed != follow')
    retained_assertion(lambda: (not _independent_passes(actual_context, changed)), 'not _independent_passes(actual_context, changed)')
