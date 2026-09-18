"""Ground a later action reference in its actual, complete adjacent context.

Public synthetic strings only. Existing literal expectations remain intact.
"""
from dataclasses import replace
from functools import lru_cache
from types import SimpleNamespace
from unittest.mock import patch

import pytest
import emlis_ai_grounded_human_reception as reception
import emlis_ai_grounded_observation_gate as gate
import emlis_ai_grounded_sentence_surface as sentence_surface
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning, build_updated_grounded_plan
from cocolon_meaning_experience_engine.emlis_thread_projection import project_thread_meaning
from test_cmee_emlis_q3_thread import begin

SOURCES = (
    '休憩したら、頭の切り替えができた感じ。',
    '作業を終えて、頭の切り替えができた感じ。',
    '少し休んで、頭の切り替えができた感じ。',
)
ACTIONS = ('机の上を片づけた。', '短いメモを書いた。')


@lru_cache(maxsize=None)
def artifacts(memo=SOURCES[0], action=ACTIONS[0]):
    request = begin(memo, action)
    prepared = prepare_emlis_meaning(request)
    plan = build_updated_grounded_plan(prepared)
    resolver = prepared.thread.resolver()
    selected = project_thread_meaning(prepared, plan).selected_reception
    sentence = sentence_surface.build_grounded_sentence_plan(plan, resolver, recovery_stage='full')
    result = MeaningExperienceEngine().generate(request)
    assert result.artifact is not None, result.reason_codes
    return plan, sentence, result.artifact.text, resolver, selected


@pytest.mark.parametrize('memo', SOURCES)
@pytest.mark.parametrize('action', ACTIONS)
def test_complete_background_is_not_recited_as_reciprocal_context(memo, action):
    plan, sentence, body, resolver, selected = artifacts(memo, action)
    follow = body.split('Emlisから：', 1)[1].strip()
    assert follow == (action.rstrip('。') + 'ことを背景に、'
                      + memo.rstrip('。') + 'という変化を見過ごさず、受け止めています。'
                      + 'また、その行動を大切に思っています。')
    assert follow.count('背景') == 1 and follow.count(action.rstrip('。')) == 1
    assert follow.count(memo.rstrip('。')) == 1
    assert len(plan.response_plan.human_reception_plan.moves) == 2
    assert all(m.required for m in plan.response_plan.human_reception_plan.moves)
    assert gate.evaluate_grounded_surface_body_inverse(
        body=body.encode(), plan=plan, sentence_plan=sentence,
        resolver=resolver, selected_subjective_input=selected).passed


@pytest.mark.parametrize('mutation', (
    'drop_action_source', 'source_actor', 'source_time', 'source_negation',
    'drop_context_source', 'drop_subjectivity', 'context_actor', 'context_time',
    'drop_first_sentence', 'swap_sentences', 'other_action', 'generic_action',
    'invent_cause', 'drop_coordination', 'negate_reception', 'new_actor',
    'new_time', 'wrong_case', 'add_background_marker', 'drop_action_reception',
))
def test_inverse_requires_actual_adjacent_sources_not_author_replay(monkeypatch, mutation):
    plan, sentence, body, resolver, selected = artifacts()
    follow = body.split('Emlisから：', 1)[1].strip()
    def forbidden(*a, **k):
        raise AssertionError('Independent inverse must not use the author or its reuse rule')
    # Freeze already resolved lexical references; the actual independent
    # sentence/antecedent check is neither replaced nor made to use the author.
    original_resolver = gate.resolve_grounded_reception_move_referent
    refs = {m.move_id: original_resolver(
        plan.response_plan.human_reception_plan, m,
        {n.nucleus_id: n for n in plan.nuclei}, resolver,
        allow_short_anchor=False, recovery_stage='full', allow_anaphoric_topic=True,
        final_source_fidelity=True, plan=plan)
        for m in plan.response_plan.human_reception_plan.moves}
    monkeypatch.setattr(reception, '_author_source_grounded_reception_clauses', forbidden)
    monkeypatch.setattr(reception, '_source_grounded_adjacent_action_context', forbidden)
    monkeypatch.setattr(gate, 'resolve_grounded_reception_move_referent',
                        lambda *a, **k: refs[(k.get('move') or a[1]).move_id])
    def passes(text):
        monkeypatch.setattr(gate, 'replay_source_grounded_human_reception_from_plan',
                            lambda *a, **k: SimpleNamespace(text=text))
        return gate.evaluate_grounded_surface_body_inverse(
            body=body.replace(follow, text).encode(), plan=plan, sentence_plan=sentence,
            resolver=resolver, selected_subjective_input=selected).passed
    assert passes(follow)
    first, second = follow.split('。')[:2]
    old, new = {
        'drop_action_source': (ACTIONS[0].rstrip('。') + 'ことを背景に、', ''),
        'source_actor': ('机の上を片づけた', '友人が机の上を片づけた'),
        'source_time': ('机の上を片づけた', '来月は机の上を片づけた'),
        'source_negation': ('片づけたこと', '片づけなかったこと'),
        'drop_context_source': (SOURCES[0].rstrip('。'), '何かが変わった感じ'),
        'drop_subjectivity': ('できた感じ', 'できた'),
        'context_actor': (SOURCES[0].rstrip('。'), '友人が' + SOURCES[0].rstrip('。')),
        'context_time': (SOURCES[0].rstrip('。'), '先月は' + SOURCES[0].rstrip('。')),
        'drop_first_sentence': (first + '。', ''),
        'swap_sentences': (follow, second + '。' + first + '。'),
        'other_action': ('その行動', '別の行動'),
        'generic_action': ('その行動', '実際の行動'),
        'invent_cause': ('また、その行動', 'そのため、その行動'),
        'drop_coordination': ('また、', ''),
        'negate_reception': ('大切に思っています', '大切に思っていません'),
        'new_actor': ('また、その行動', 'また、友人のその行動'),
        'new_time': ('また、その行動', 'また、来月のその行動'),
        'wrong_case': ('その行動を', 'その行動に'),
        'add_background_marker': ('また、その行動', '別の背景の中で、実際の行動'),
        'drop_action_reception': (second + '。', ''),
    }[mutation]
    changed = follow.replace(old, new, 1)
    assert changed != follow and not passes(changed)


@pytest.mark.parametrize('axis', (
    'first_move', 'not_required', 'not_adjacent_reference', 'missing_context',
    'same_target', 'recovery', 'other_actor', 'future', 'not_retained', 'quoted',
))
def test_reference_choice_does_not_cross_source_or_recovery_boundary(axis):
    plan, _, _, resolver, _ = artifacts()
    reception_plan = plan.response_plan.human_reception_plan
    move = reception_plan.moves[1]
    indices = {n.nucleus_id: n for n in plan.nuclei}
    resolve = reception._source_grounded_adjacent_action_context
    assert resolve(reception_plan, move, plan, indices, resolver, 'full') is not None
    stage = 'full'
    if axis == 'first_move':
        move = reception_plan.moves[0]
    elif axis == 'recovery':
        stage = 'hedged'
    elif axis in {'other_actor', 'future', 'not_retained'}:
        n = indices[move.target_nucleus_ids[0]]
        if axis == 'not_retained':
            n = replace(n, retention='optional')
        else:
            frame = replace(n.semantic_frame, **(
                {'actor': 'other'} if axis == 'other_actor' else {'modality': 'intention'}))
            n = replace(n, semantic_frame=frame)
        indices[n.nucleus_id] = n
    elif axis == 'quoted':
        original = resolver
        resolver = SimpleNamespace(resolve_many=lambda *a: (
            SimpleNamespace(source_field='memo', raw_text='「別の人の言葉」'),),
            span_ids=original.span_ids)
    else:
        changes = {
            'not_required': {'required': False},
            'not_adjacent_reference': {'reference_mode': 'short_anchor_if_ambiguous'},
            'missing_context': {'support_nucleus_ids': ()},
            'same_target': {'support_nucleus_ids': move.target_nucleus_ids},
        }[axis]
        move = replace(move, **changes)
        reception_plan = replace(reception_plan, moves=(reception_plan.moves[0], move))
        plan = replace(plan, response_plan=replace(plan.response_plan, human_reception_plan=reception_plan))
    assert resolve(reception_plan, move, plan, indices, resolver, stage) is None
