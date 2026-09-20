"""One subjective-change object with complete independent-action context.

Public synthetic sources extend test_cmee_emlis_subjective_change_reception.
The original saved singleton expectation is not overwritten by these tests.
"""

from helpers.retained_assertions import continue_assertions, retained_assertion
from dataclasses import replace
from functools import lru_cache
from types import SimpleNamespace
from unittest.mock import patch

import pytest
import emlis_ai_grounded_human_reception as reception
import emlis_ai_grounded_observation_gate as gate
import emlis_ai_grounded_sentence_surface as sentence_surface
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.emlis_answer_update import (
    prepare_emlis_meaning, build_updated_grounded_plan,
)
from cocolon_meaning_experience_engine.emlis_thread_projection import project_thread_meaning
from test_cmee_emlis_q3_thread import begin
from test_cmee_emlis_subjective_change_reception import SOURCES, ACTION


@lru_cache(maxsize=None)
def contextual_artifacts(memo):
    request = begin(memo, ACTION)
    prepared = prepare_emlis_meaning(request)
    plan = build_updated_grounded_plan(prepared)
    projection = project_thread_meaning(prepared, plan)
    resolver = prepared.thread.resolver()
    sentence = sentence_surface.build_grounded_sentence_plan(plan, resolver, recovery_stage='full')
    captured = []
    original = reception._source_grounded_target_np

    def capture(move, realization, **kwargs):
        if kwargs['material_change_object']:
            captured.append(realization)
        return original(move, realization, **kwargs)

    with patch.object(reception, '_source_grounded_target_np', side_effect=capture):
        result = MeaningExperienceEngine().generate(request)
    assert result.artifact is not None, result.reason_codes
    assert captured
    return plan, sentence, result.artifact.text, resolver, projection.selected_reception, captured[0]


@pytest.mark.parametrize('memo', SOURCES)
@continue_assertions
def test_contextual_subjective_change_keeps_background_and_separate_action(memo):
    plan, sentence, body, resolver, selected, realization = contextual_artifacts(memo)
    follow = body.split('Emlisから：', 1)[1].strip()
    retained_assertion(lambda: (realization.reference_mode == 'COMPOSITE'), "realization.reference_mode == 'COMPOSITE'")
    retained_assertion(lambda: (realization.target_slot_count == 1 and realization.context_slots == (1,)), 'realization.target_slot_count == 1 and realization.context_slots == (1,)')
    retained_assertion(lambda: (len(realization.semantic_fragments) == 2 and not realization.relations), 'len(realization.semantic_fragments) == 2 and (not realization.relations)')
    retained_assertion(lambda: (follow == (ACTION.rstrip('。') + 'ことを背景に、'
                      + memo.rstrip('。') + 'という変化を見過ごさず、受け止めています。'
                      + 'その反応を背景に、実際の行動を大切に思っています。')), "follow == ACTION.rstrip('。') + 'ことを背景に、' + memo.rstrip('。') + 'という変化を見過ごさず、受け止めています。' + 'その反応を背景に、実際の行動を大切に思っています。'")
    retained_assertion(lambda: (gate.evaluate_grounded_surface_body_inverse(
        body=body.encode(), plan=plan, sentence_plan=sentence,
        resolver=resolver, selected_subjective_input=selected).passed), 'gate.evaluate_grounded_surface_body_inverse(body=body.encode(), plan=plan, sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected).passed')


@pytest.mark.parametrize('mutation', (
    'drop_background', 'background_actor', 'background_time', 'background_negation',
    'invent_cause', 'drop_subjectivity', 'target_actor', 'target_time',
    'drop_attention', 'negate_attention', 'negate_reception', 'replace_case', 'drop_action',
))
@continue_assertions
def test_contextual_inverse_reads_both_sources_without_author_replay(monkeypatch, mutation):
    memo = SOURCES[0]
    plan, sentence, body, resolver, selected, _ = contextual_artifacts(memo)
    follow = body.split('Emlisから：', 1)[1].strip()

    def forbidden(*args, **kwargs):
        raise AssertionError('An independent inverse must not invoke the author')

    monkeypatch.setattr(reception, '_author_source_grounded_reception_clauses', forbidden)
    monkeypatch.setattr(reception, '_source_grounded_contextual_subjective_change', forbidden)

    def passes(text):
        monkeypatch.setattr(gate, 'replay_source_grounded_human_reception_from_plan',
                            lambda *a, **k: SimpleNamespace(text=text))
        return gate.evaluate_grounded_surface_body_inverse(
            body=body.replace(follow, text).encode(), plan=plan, sentence_plan=sentence,
            resolver=resolver, selected_subjective_input=selected).passed

    retained_assertion(lambda: (passes(follow)), 'passes(follow)')
    context = ACTION.rstrip('。') + 'ことを背景に、'
    before, after = {
        'drop_background': (context, ''),
        'background_actor': (context, '友人が' + context),
        'background_time': (context, '来月は' + context),
        'background_negation': ('片づけたこと', '片づけなかったこと'),
        'invent_cause': ('ことを背景に、', 'ことが原因で、'),
        'drop_subjectivity': ('できた感じ', 'できた'),
        'target_actor': (memo.rstrip('。'), '友人が' + memo.rstrip('。')),
        'target_time': (memo.rstrip('。'), '先月は' + memo.rstrip('。')),
        'drop_attention': ('見過ごさず、', ''),
        'negate_attention': ('見過ごさず、', '見過ごして、'),
        'negate_reception': ('受け止めています', '受け止めていません'),
        'replace_case': ('という変化を', 'という変化に'),
        'drop_action': ('その反応を背景に、実際の行動を大切に思っています。', ''),
    }[mutation]
    changed = follow.replace(before, after, 1)
    retained_assertion(lambda: (changed != follow and not passes(changed)), 'changed != follow and (not passes(changed))')


@pytest.mark.parametrize('axis', (
    'reference', 'target_count', 'target_owner', 'context_slot', 'target_kind',
    'target_actor', 'target_modality', 'target_quote', 'background_kind',
    'background_actor', 'background_modality', 'background_quote',
    'background_future', 'background_not_performed', 'background_not_past',
))
@continue_assertions
def test_contextual_object_requires_proven_single_target_and_performed_background(axis):
    *_, realization = contextual_artifacts(SOURCES[0])
    if len(realization.semantic_profiles) != 2:
        # The source-owned path now keeps the two sources independent. Retain
        # the old positive-setup failure; do not fabricate a COMPOSITE object.
        # The same inputs are exercised through the active path in the
        # retained-failure recovery tests, including actual meaning mutations.
        retained_assertion(lambda: len(realization.semantic_profiles) == 2,
                           'legacy contextual positive setup requires two profiles')
        return
    target, background = realization.semantic_profiles
    changes = {
        'reference': dict(reference_mode='ANAPHORIC'),
        'target_count': dict(target_slot_count=2),
        'context_slot': dict(context_slots=()),
        'target_kind': dict(semantic_profiles=(replace(target, nucleus_kind='action'), background)),
        'target_actor': dict(semantic_profiles=(replace(target, actor_kind='OTHER'), background)),
        'target_modality': dict(semantic_profiles=(replace(target, modality='fact'), background)),
        'target_quote': dict(semantic_profiles=(replace(target, quoted_boundary=True), background)),
        'background_kind': dict(semantic_profiles=(target, replace(background, nucleus_kind='reaction'))),
        'background_actor': dict(semantic_profiles=(target, replace(background, actor_kind='OTHER'))),
        'background_modality': dict(semantic_profiles=(target, replace(background, modality='intention'))),
        'background_quote': dict(semantic_profiles=(target, replace(background, quoted_boundary=True))),
        'background_future': dict(semantic_profiles=(target, replace(background, future_action=True))),
        'background_not_performed': dict(semantic_profiles=(target, replace(background, performed_action=False))),
        'background_not_past': dict(semantic_fragments=(realization.semantic_fragments[0], '片づける')),
    }.get(axis, {})
    retained_assertion(lambda: (reception._source_grounded_contextual_subjective_change(realization, 0)), 'reception._source_grounded_contextual_subjective_change(realization, 0)')
    retained_assertion(lambda: (not reception._source_grounded_contextual_subjective_change(
        replace(realization, **changes), 1 if axis == 'target_owner' else 0)), "not reception._source_grounded_contextual_subjective_change(replace(realization, **changes), 1 if axis == 'target_owner' else 0)")
