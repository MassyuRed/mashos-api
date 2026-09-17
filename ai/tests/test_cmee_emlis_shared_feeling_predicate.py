"""Independent feelings retain their own objects under a shared reception.

The scenarios below are existing public synthetic examples. Frozen inputs,
legacy expectations and historical receipts are deliberately not rewritten.
"""
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from test_cmee_emlis_q3_thread import (
    RECEIVED_PAST_FEELING, NOMINAL_COGNITION_FEELING,
    NOMINAL_PAST_JOY, NOMINAL_PAST_RELIEF,
    initial, begin, prepare_emlis_meaning, build_updated_grounded_plan,
    realize_emlis_thread_body, project_thread_meaning,
)
import emlis_ai_grounded_sentence_surface as surface
from emlis_ai_grounded_observation_gate import evaluate_grounded_surface_body_inverse

PAIRS = ((RECEIVED_PAST_FEELING, NOMINAL_COGNITION_FEELING),
         (NOMINAL_PAST_JOY, NOMINAL_PAST_RELIEF))
ACTION = '机を拭いた。'


def actual(pair, *, premium=False, action=ACTION):
    prepared = prepare_emlis_meaning((begin if premium else initial)(
        '。'.join(pair) + '。', action))
    plan = build_updated_grounded_plan(prepared)
    result = realize_emlis_thread_body(prepared)
    assert result.artifact, result.reason_codes
    resolver = prepared.thread.resolver()
    selected = project_thread_meaning(prepared, plan).selected_reception
    sentence = surface.build_grounded_sentence_plan(plan, resolver, recovery_stage='full')
    return result, plan, sentence, resolver, selected


@pytest.mark.parametrize('pair', PAIRS)
@pytest.mark.parametrize('premium', [False, True])
def test_both_feelings_remain_complete_under_one_reception_without_merging_duties(pair, premium):
    result, plan, sentence, resolver, selected = actual(pair, premium=premium)
    follow = result.artifact.reception
    assert follow == (pair[0] + 'という気持ちも、' + pair[1]
        + 'という気持ちも、見過ごさず、受け止めています。'
        + '机を拭いたことを大切に思っています。')
    moves = plan.response_plan.human_reception_plan.moves
    assert len(moves) == 3 and all(m.required for m in moves)
    assert len({m.target_nucleus_ids for m in moves}) == 3
    assert [m.reception_act for m in moves] == ['recognize_lived_change'] * 2 + ['honor_concrete_effort']
    assert len(follow.split('。')) - 1 == 2
    assert follow.count('受け止めています') == 1
    inverse = evaluate_grounded_surface_body_inverse(body=result.artifact.text.encode(),
        plan=plan, sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected)
    assert inverse.passed, inverse.failure_codes


@pytest.mark.parametrize('pair', PAIRS)
def test_two_duties_without_action_keep_the_two_sentence_minimum(pair):
    result, plan, *_ = actual(pair, action='')
    follow = result.artifact.reception
    assert plan.response_plan.human_reception_plan.depth_policy.min_sentences == 2
    assert follow.count('。') == 2 and follow.count('受け止めています') == 2
    assert all(source + 'という気持ち' in follow for source in pair)


@pytest.fixture(scope='module', params=PAIRS)
def context(request):
    return request.param, actual(request.param)


def independent(context, changed):
    _, (result, plan, sentence, resolver, selected) = context
    follow = result.artifact.reception
    with patch('emlis_ai_grounded_observation_gate.replay_source_grounded_human_reception_from_plan',
               return_value=SimpleNamespace(text=changed)), patch(
               'emlis_ai_grounded_human_reception._author_source_grounded_reception_clauses',
               side_effect=AssertionError('the independent proof cannot replay the author')):
        return evaluate_grounded_surface_body_inverse(
            body=result.artifact.text.replace(follow, changed).encode(), plan=plan,
            sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected).passed


def test_independent_read_accepts_both_complete_objects_without_the_author(context):
    assert independent(context, context[1][0].artifact.reception)


@pytest.mark.parametrize('mutation', [
    'omit_first', 'omit_second', 'duplicate_first', 'duplicate_second', 'swap',
    'shorten_first', 'shorten_second', 'foreign_actor_first', 'foreign_actor_second',
    'past_to_present', 'add_negation', 'quoted_first', 'quoted_pair',
    'causal_connector', 'contrast_connector', 'remove_first_case', 'remove_second_case',
    'change_attention', 'remove_attention', 'remove_reception', 'negate_reception',
    'future_reception', 'add_temporal_prefix', 'remove_action', 'change_action',
])
def test_independent_read_rejects_missing_or_reassigned_scope(context, mutation):
    pair, (result, *_rest) = context
    follow = result.artifact.reception
    first, second = (source + 'という気持ち' for source in pair)
    both = first + 'も、' + second + 'も、'
    replacements = {
        'omit_first': (first + 'も、', ''),
        'omit_second': (second + 'も、', ''),
        'duplicate_first': (second, first),
        'duplicate_second': (first, second),
        'swap': (both, second + 'も、' + first + 'も、'),
        'shorten_first': (first, 'その気持ち'),
        'shorten_second': (second, 'その気持ち'),
        'foreign_actor_first': (first, '弟が' + first),
        'foreign_actor_second': (second, '弟が' + second),
        'past_to_present': (pair[0], pair[0] + '今も'),
        'add_negation': (pair[1], pair[1] + 'わけではない'),
        'quoted_first': (first, '「' + first + '」'),
        'quoted_pair': (both, '「' + both + '」'),
        'causal_connector': (first + 'も、', first + 'だから、'),
        'contrast_connector': (first + 'も、', first + 'のに、'),
        'remove_first_case': (first + 'も、', first + '、'),
        'remove_second_case': (second + 'も、', second + '、'),
        'change_attention': ('見過ごさず、', '見過ごして、'),
        'remove_attention': ('見過ごさず、', ''),
        'remove_reception': ('受け止めています', ''),
        'negate_reception': ('受け止めています', '受け止めていません'),
        'future_reception': ('受け止めています', '受け止めるつもりです'),
        'add_temporal_prefix': (first, '昨日は' + first),
        'remove_action': ('机を拭いたことを大切に思っています。', ''),
        'change_action': ('机を拭いたこと', '机を拭くつもりでいること'),
    }
    old, new = replacements[mutation]
    changed = follow.replace(old, new)
    assert changed != follow
    assert not independent(context, changed)


@pytest.mark.parametrize('boundary', [
    'legacy_plan', 'answer_source', 'foreign_actor', 'untyped_feeling',
    'single_move_budget', 'safety_mode', 'overlapping_evidence', 'same_target', 'recovery',
])
def test_shared_sentence_admission_requires_the_same_source_scope_and_depth(context, boundary):
    from dataclasses import replace
    from emlis_ai_grounded_human_reception import _independent_recognition_pair
    from emlis_ai_grounded_observation_plan import FINAL_STAGE1_GROUNDED_PROJECTION_VERSION
    _, (_, plan, *_rest) = context
    rp = plan.response_plan.human_reception_plan
    assert _independent_recognition_pair(rp, 'full', plan=plan)
    stage = 'full'
    target = rp.moves[0].target_nucleus_ids[0]
    nucleus = next(n for n in plan.nuclei if n.nucleus_id == target)
    replacement = None
    if boundary == 'legacy_plan':
        plan = replace(plan, source_contracts=tuple(c for c in plan.source_contracts
                       if c != FINAL_STAGE1_GROUNDED_PROJECTION_VERSION))
    elif boundary == 'answer_source': replacement = replace(nucleus, source_fields=('answer_text_private',))
    elif boundary == 'foreign_actor':
        replacement = replace(nucleus, semantic_frame=replace(nucleus.semantic_frame, actor='other_person'))
    elif boundary == 'untyped_feeling':
        replacement = replace(nucleus, semantic_frame=replace(nucleus.semantic_frame,
            attribute_codes=tuple(c for c in nucleus.semantic_frame.attribute_codes
                if c not in {'lexical:source_nominal_cognition_feeling',
                             'lexical:source_received_past_feeling', 'lexical:source_nominal_past_feeling'})))
    elif boundary == 'single_move_budget':
        rp = replace(rp, depth_policy=replace(rp.depth_policy, max_moves_per_sentence=1))
    elif boundary == 'safety_mode':
        rp = replace(rp, depth_policy=replace(rp.depth_policy, safety_mode='help_seeking_bounded'))
    elif boundary == 'overlapping_evidence':
        rp = replace(rp, moves=(rp.moves[0], replace(rp.moves[1],
                     source_evidence_span_ids=rp.moves[0].source_evidence_span_ids), rp.moves[2]))
    elif boundary == 'same_target':
        rp = replace(rp, moves=(rp.moves[0], replace(rp.moves[1],
                     target_nucleus_ids=rp.moves[0].target_nucleus_ids), rp.moves[2]))
    elif boundary == 'recovery': stage = 'optional_removed'
    if replacement is not None:
        plan = replace(plan, nuclei=tuple(replacement if n.nucleus_id == target else n for n in plan.nuclei))
    plan = replace(plan, response_plan=replace(plan.response_plan, human_reception_plan=rp))
    assert not _independent_recognition_pair(rp, stage, plan=plan)
