"""Two source-witnessed fields share one observed frame, without a route edge."""
import copy
from dataclasses import replace
import json
from unittest.mock import patch

import pytest
import analysis_cumulative_service as service
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.cores.analysis import intent_compiler as compiler
from cocolon_meaning_experience_engine.cores.analysis import observed_route_realizer as author
from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import (
    AnalysisSemanticError, canonical, AnalysisSemanticUnsupported)
from cocolon_meaning_experience_engine.cores.analysis.source_adapter import AnalysisSourceError
from test_analysis_cumulative import OWNER, source_snapshot
from test_analysis_model_quoted_parent_units import call


def sample(role_negative=False, action_negative=False, swap=False):
    snap = source_snapshot(1)
    role = '私の役割は連絡係' + ('ではなかった。' if role_negative else 'だった。')
    action = '私は資料を' + ('調べなかった。' if action_negative else '調べた。')
    snap['members'][0]['original'].update(memo=action if swap else role, memo_action=role if swap else action)
    return snap


def prepared(snap):
    return service.prepare_cumulative_category_units(OWNER, snap, prompt_version='selected_material.v2')


def packet(p):
    material = json.loads(p.messages()[1]['content'])
    return dict(fields=[dict(field=f['field'], units=[dict(quote=f['text'].rstrip('。'),
        node_kind='ROLE' if 'の役割は' in f['text'] else 'ACTION_OR_NONACTION',
        parent_quote=None, scope_role=None, qualifiers=[])]) for f in material['fields']])


def build(snap=None, data=None):
    snap = sample() if snap is None else snap
    p = prepared(snap); value = call(p, packet(p) if data is None else data)
    artifact, coverage = service.build_cumulative_written_role_map(OWNER, snap, model_input=value, with_action=True)
    return snap, value, artifact, coverage


@pytest.mark.parametrize('role_negative', [False, True])
@pytest.mark.parametrize('action_negative', [False, True])
@pytest.mark.parametrize('swap', [False, True])
def test_role_and_action_keep_polarity_fields_evidence_and_missing_route(role_negative, action_negative, swap):
    snap, value, artifact, coverage = build(sample(role_negative, action_negative, swap))
    assert coverage['mapped_count'] == 1 and coverage['unparsed_count'] == 0
    assert len(artifact.graph.nodes) == 2 and artifact.graph.edges == ()
    assert {n.node_kind for n in artifact.graph.nodes} == {'ROLE', 'ACTION_OR_NONACTION'}
    role = next(n for n in artifact.graph.nodes if n.node_kind == 'ROLE')
    action = next(n for n in artifact.graph.nodes if n.node_kind == 'ACTION_OR_NONACTION')
    assert role.polarity == ('negative' if role_negative else 'positive')
    assert action.polarity == ('negative' if action_negative else 'positive')
    assert all(n.proposition.actor == 'SELF' and n.modality == 'fact' and n.temporal_scope == 'past'
        and n.selected_categories == ('仕事',) for n in artifact.graph.nodes)
    assert role.record_refs == action.record_refs
    assert len({e.source_envelope_id for n in artifact.graph.nodes for e in n.evidence_refs}) == 1
    assert {g.missing_scope for g in artifact.graph.unknown_gaps} == {
        'SCENE', 'ATTENTION_OR_THOUGHT', 'IMMEDIATE_RESULT_OR_AFTERMATH', 'ROUTE_CONNECTION'}
    visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
    body = artifact.safe_text_projection(authenticated_owner_scope=OWNER)
    assert all(n['visible_label'] in body['text'] for n in visual['nodes'])
    assert visual['edges'] == []
    candidate, counts = service.build_cumulative_quoted_parent_candidates(OWNER, snap, model_input=value)
    assert counts['mapped_count'] == 0 and all(u.actor == 'UNRESOLVED_NOT_OWNER_DERIVED'
        for f in candidate.graph.fields for u in f.units)
    action_field = next(f for f in candidate.graph.fields if f.units[0].node_kind == 'ACTION_OR_NONACTION')
    assert action.evidence_refs == (action_field.units[0].evidence,)
    assert action.evidence_refs[0].evidence_id != action_field.evidence.evidence_id
    with pytest.raises(AnalysisSemanticUnsupported):
        service.build_cumulative_written_role_map(OWNER, snap, model_input=value)


@pytest.mark.parametrize('text', ['資料を調べた。', '姉は資料を調べた。', '私は資料を調べたい。',
    '昨日、私は資料を調べた。', '私は資料を調べている。', '私は資料を調べた。まだ分からない。',
    'その後、私は資料を調べた。', '私は不安だった。', '私は仕事を続けるべきだ。'])
def test_pair_does_not_admit_unwitnessed_actor_time_stage_or_an_unread_remainder(text):
    snap = sample(); snap['members'][0]['original']['memo_action'] = text
    p = prepared(snap)
    with pytest.raises((AnalysisSemanticError, AnalysisSourceError)):
        service.build_cumulative_written_role_map(OWNER, snap, model_input=call(p, packet(p)), with_action=True)


@pytest.mark.parametrize('change', ['kind', 'role_modifier', 'action_modifier', 'false_negation', 'unread_role', 'extra_root'])
def test_pair_requires_the_actual_model_proposal_and_rejects_false_operators(change):
    snap=sample(); p=prepared(snap); data=packet(p)
    if change == 'kind': data['fields'][1]['units'][0]['node_kind'] = 'ROLE'
    if change == 'role_modifier': data['fields'][0]['units'][0]['qualifiers'] = [dict(kind='WRITTEN_MODIFIER',quote='だった')]
    if change == 'action_modifier': data['fields'][1]['units'][0]['qualifiers'] = [dict(kind='WRITTEN_MODIFIER',quote='調べた')]
    if change == 'false_negation': data['fields'][1]['units'][0]['qualifiers'] = [dict(kind='NEGATION',quote='調べた')]
    if change == 'unread_role': data['fields'][0]['units'] = []
    if change == 'extra_root': data['fields'][1]['units'].append(dict(quote='資料',node_kind='SCENE',parent_quote=None,scope_role=None,qualifiers=[]))
    with pytest.raises((AnalysisSemanticError, AnalysisSourceError)):
        service.build_cumulative_written_role_map(OWNER, snap, model_input=call(p,data), with_action=True)


def test_action_operator_is_bound_to_the_actual_subject_and_negative_predicate():
    snap=sample(True,True); p=prepared(snap); data=packet(p)
    data['fields'][0]['units'][0]['qualifiers']=[dict(kind='EXPLICIT_ACTOR',quote='私'),dict(kind='NEGATION',quote='ではなかった')]
    data['fields'][1]['units'][0]['qualifiers']=[dict(kind='EXPLICIT_ACTOR',quote='私は'),dict(kind='NEGATION',quote='なかった')]
    artifact,_=service.build_cumulative_written_role_map(OWNER,snap,model_input=call(p,data),with_action=True)
    assert all(n.polarity == 'negative' for n in artifact.graph.nodes)


def test_pair_saved_graph_and_both_projections_restore_without_engine_compilers_or_authors():
    snap,value,artifact,coverage=build(sample(True,True,True))
    raw=service.serialize_cumulative_written_role_map(OWNER,snap,model_input=value,artifact=artifact,
        coverage=coverage,with_action=True)
    from contextlib import ExitStack
    with ExitStack() as stack:
        for obj,name in [(MeaningExperienceEngine,'generate'),(compiler,'compile_observed_graph'),
            (compiler,'compile_analysis_unit_candidates'),(compiler,'compile_model_written_role_graph'),
            (compiler,'compile_model_written_role_action_graph'),(author,'realize_model_written_role_graph'),
            (author,'realize_analysis_unit_candidates')]:
            stack.enter_context(patch.object(obj,name,side_effect=AssertionError('no saved regeneration')))
        assert service.reload_cumulative_written_role_map(OWNER,snap,raw,with_action=True)==(artifact,coverage)
    with pytest.raises(AnalysisSemanticError):
        service.reload_cumulative_written_role_map(OWNER,snap,raw)


@pytest.mark.parametrize('change', ['polarity','source_parts','category','evidence','node_order','gap','edge','text','id'])
def test_pair_saved_meaning_and_body_tampering_is_rejected(change):
    snap,value,artifact,coverage=build()
    saved=json.loads(service.serialize_cumulative_written_role_map(OWNER,snap,model_input=value,
        artifact=artifact,coverage=coverage,with_action=True))
    a=saved['state']['artifact']; g=a['graph']
    if change == 'polarity': g['nodes'][1]['proposition']['polarity']='negative';g['nodes'][1]['polarity']='negative'
    if change == 'source_parts': g['nodes'][1]['proposition']['source_parts'][0][2]-=1
    if change == 'category': g['nodes'][0]['selected_categories']=['趣味']
    if change == 'evidence': g['nodes'][1]['evidence_refs'][0]['scalar_end']-=1
    if change == 'node_order': g['nodes'].reverse()
    if change == 'gap': g['unknown_gaps'].pop()
    if change == 'edge': g['edges'].append(dict())
    if change == 'text': a['text']['text']+='changed'
    if change == 'id': a['artifact_id']='artifact:changed'
    with pytest.raises((AnalysisSemanticError,AnalysisSourceError)):
        service.reload_cumulative_written_role_map(OWNER,snap,canonical(saved),with_action=True)
