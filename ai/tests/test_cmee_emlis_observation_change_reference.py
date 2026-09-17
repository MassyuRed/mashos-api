"""A shared observation endpoint stays source-bound without a second long quote.

Examples extend the existing public synthetic plant scenario. Historical
inputs, expectations, sentence budgets, and required meanings stay unchanged.
"""
from dataclasses import replace
from unittest.mock import patch

import pytest

from test_cmee_emlis_shared_change_context import _actual, CONTINUATIONS, CHANGE
from test_cmee_emlis_q3_thread import ACTION_CHANGE_CONTRAST_MEMO
from emlis_ai_grounded_observation_gate import evaluate_grounded_surface_body_inverse
import emlis_ai_grounded_sentence_surface as surface

MEMOS = (
    *CONTINUATIONS,
    ACTION_CHANGE_CONTRAST_MEMO,
    CONTINUATIONS[0].replace('窓辺の鉢', '窓際の鉢').replace('棚', '台'),
    CONTINUATIONS[0].replace('机の上が広く', '作業台の上が広く'),
    CONTINUATIONS[0].replace('机の上が広く', '机の上が思っていたよりずっと広く'),
)


@pytest.mark.parametrize('premium', [False, True])
@pytest.mark.parametrize('memo', MEMOS)
def test_one_named_change_serves_both_selected_relations(memo, premium):
    result, plan, sentence, resolver, selected = _actual(memo, premium=premium)
    observation = result.artifact.observation
    assert 'という行動からその変化へつながっています。' in observation
    first, second, *_ = observation.split('。')
    assert first.count('という変化') == 1 and '異なる向き' in first
    assert 'その変化' in second and second.count('「') == 1
    line = sentence.lines[0]
    index = {r.relation_id: r for r in plan.relations}
    contrast, support = (index[rid] for rid in line.binding.relation_ids)
    assert (contrast.type, support.type) == ('contrast', 'action_supports_change')
    assert contrast.from_nucleus_id == support.to_nucleus_id
    assert len(line.binding.nucleus_ids) == 3
    # The reception and its depth obligations are not shortened by this fix.
    assert result.artifact.reception.count('。') == 3
    checked = evaluate_grounded_surface_body_inverse(body=result.artifact.text.encode(),
        plan=plan, sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected)
    assert checked.passed, checked.failure_codes


@pytest.fixture(scope='module', params=['normal', 'limited'])
def context(request):
    actual = _actual()
    if request.param == 'normal':
        return actual
    # Exercise the existing limited author with the same source-bound duties;
    # only the observation line's rendering function differs in this unit test.
    from types import SimpleNamespace
    result, plan, sentence, resolver, selected = actual
    line = sentence.lines[0]
    rendered = surface._render_final_stage1_limited_scope(
        line.binding, {n.nucleus_id: n for n in plan.nuclei},
        {r.relation_id: r for r in plan.relations}, resolver)
    assert 'という行動からその変化へのつながりも確認できます。' in rendered
    observation = result.artifact.observation.replace(
        result.artifact.observation.splitlines()[0], rendered, 1)
    sentence = replace(sentence, lines=(replace(line, surface_function='render_limited_scope'),
                                       *sentence.lines[1:]))
    artifact = SimpleNamespace(observation=observation, reception=result.artifact.reception,
        text=result.artifact.text.replace(result.artifact.observation, observation))
    return SimpleNamespace(artifact=artifact), plan, sentence, resolver, selected


def independent(context, observation, *, plan_override=None):
    result, plan, sentence, resolver, selected = context
    with patch.object(surface, '_shared_observation_change_relation',
                      side_effect=AssertionError('inverse must not use author eligibility')), \
         patch.object(surface, '_render_relation',
                      side_effect=AssertionError('inverse must not use the author')), \
         patch.object(surface, '_render_final_stage1_limited_scope',
                      side_effect=AssertionError('inverse must not use the limited author')):
        return evaluate_grounded_surface_body_inverse(
            body=result.artifact.text.replace(result.artifact.observation, observation).encode(),
            plan=plan_override or plan, sentence_plan=sentence, resolver=resolver,
            selected_subjective_input=selected).passed


def test_independent_inverse_accepts_actual_shared_antecedent_without_author(context):
    assert independent(context, context[0].artifact.observation)


@pytest.mark.parametrize('mutation', [
    'remove_first_sentence', 'remove_change', 'replace_change', 'truncate_change',
    'negate_change', 'change_time', 'change_actor', 'swap_contrast',
    'remove_feeling', 'change_feeling', 'remove_action', 'change_action',
    'future_action', 'negate_action', 'reverse_direction', 'change_referent',
    'quoted_referent', 'remove_referent', 'causal_invention', 'insert_sentence',
    'swap_sentences', 'duplicate_referent', 'current_instead_of_same_change',
])
def test_independent_inverse_rejects_unbound_reordered_or_changed_reference(context, mutation):
    observation = context[0].artifact.observation
    first, second, *tail = observation.split('。')
    if mutation == 'remove_first_sentence': first = ''
    elif mutation == 'remove_change': first = first.replace(CHANGE, '')
    elif mutation == 'replace_change': first = first.replace(CHANGE, '机がきれいになった')
    elif mutation == 'truncate_change': first = first.replace(CHANGE, 'うれしかった')
    elif mutation == 'negate_change': first = first.replace('うれしかった', 'うれしくなかった')
    elif mutation == 'change_time': first = first.replace('うれしかった', 'うれしい')
    elif mutation == 'change_actor': first = first.replace(CHANGE, '弟は' + CHANGE)
    elif mutation == 'swap_contrast':
        import re
        quoted = re.findall('「([^「」]+)」', first)
        first = first.replace('「' + quoted[0] + '」という変化と「' + quoted[1] + '」',
                              '「' + quoted[1] + '」と「' + quoted[0] + '」という変化')
    elif mutation == 'remove_feeling': first = first.replace('手元に緑がない寂しさも残っている', '')
    elif mutation == 'change_feeling': first = first.replace('寂しさも残っている', '寂しさは残っていない')
    elif mutation == 'remove_action': second = second.replace('窓辺の鉢を棚へ移した', '')
    elif mutation == 'change_action': second = second.replace('窓辺の鉢を棚へ移した', '窓辺の鉢を捨てた')
    elif mutation == 'future_action': second = second.replace('移した', '移すつもりだ')
    elif mutation == 'negate_action': second = second.replace('移した', '移さなかった')
    elif mutation == 'reverse_direction': second = second.replace('からその変化へ', 'へその変化から')
    elif mutation == 'change_referent': second = second.replace('その変化', 'その寂しさ')
    elif mutation == 'quoted_referent': second = second.replace('その変化', '「その変化」')
    elif mutation == 'remove_referent': second = second.replace('その変化', '')
    elif mutation == 'causal_invention':
        second = second.replace('その変化へつながっています', 'その変化の唯一の原因です')
        second = second.replace('その変化へのつながりも確認できます', 'その変化の唯一の原因です')
    elif mutation == 'insert_sentence': first += '。別の変化もありました'
    elif mutation == 'swap_sentences': first, second = second.strip(), first
    elif mutation == 'duplicate_referent': second += '、その変化もあります'
    elif mutation == 'current_instead_of_same_change': second = second.replace('その変化', '今の変化')
    changed = '。'.join([first, second, *tail])
    assert changed != observation
    assert not independent(context, changed)


@pytest.mark.parametrize('boundary', [
    'relation_order', 'other_target', 'different_source', 'foreign_actor',
    'answer_source', 'future_change', 'inferred_relation', 'extra_relation',
    'scope_hedge',
])
def test_reference_admission_preserves_source_identity_and_scope(context, boundary):
    result, plan, sentence, resolver, selected = context
    binding = sentence.lines[0].binding
    nuclei = {n.nucleus_id: n for n in plan.nuclei}
    relations = {r.relation_id: r for r in plan.relations}
    contrast, support = (relations[rid] for rid in binding.relation_ids)
    assert surface._shared_observation_change_relation(binding, nuclei, relations, resolver) == support.relation_id
    change = nuclei[support.to_nucleus_id]
    if boundary == 'relation_order': binding = replace(binding, relation_ids=tuple(reversed(binding.relation_ids)))
    elif boundary == 'other_target': relations[support.relation_id] = replace(support, to_nucleus_id=contrast.to_nucleus_id)
    elif boundary == 'different_source': nuclei[change.nucleus_id] = replace(change, source_span_ids=nuclei[contrast.to_nucleus_id].source_span_ids)
    elif boundary == 'foreign_actor': nuclei[change.nucleus_id] = replace(change, semantic_frame=replace(change.semantic_frame, actor='other_person'))
    elif boundary == 'answer_source': nuclei[change.nucleus_id] = replace(change, source_fields=('answer_text_private',))
    elif boundary == 'future_change': nuclei[change.nucleus_id] = replace(change, semantic_frame=replace(change.semantic_frame, time_scope='future'))
    elif boundary == 'inferred_relation': relations[support.relation_id] = replace(support, grounding_kind='bounded_structural_inference')
    elif boundary == 'extra_relation': binding = replace(binding, relation_ids=(*binding.relation_ids, next(r for r in relations if r not in binding.relation_ids)))
    elif boundary == 'scope_hedge': binding = replace(binding, functional_atom_ids=(*binding.functional_atom_ids, 'scope_hedge'))
    assert surface._shared_observation_change_relation(binding, nuclei, relations, resolver) is None
    changed_plan = replace(plan, nuclei=tuple(nuclei.values()), relations=tuple(relations.values()))
    if boundary not in {'relation_order', 'extra_relation', 'scope_hedge'}:
        assert not independent(context, result.artifact.observation, plan_override=changed_plan)
