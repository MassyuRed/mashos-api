"""Explicit private clause admission; synthetic fixtures, no model gold rewrite."""
import copy
from contextlib import ExitStack
from dataclasses import replace
import hashlib
import json
from unittest.mock import patch

import pytest
import analysis_cumulative_service as service
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.cores.analysis import intent_compiler as compiler
from cocolon_meaning_experience_engine.cores.analysis import observed_route_realizer as author
from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import (
    AnalysisModelQuotedParentUnitsResponse, AnalysisSemanticError, canonical)
from cocolon_meaning_experience_engine.cores.analysis.source_adapter import AnalysisSourceError
from test_analysis_cumulative import OWNER, source_snapshot


ERRORS = (AnalysisSemanticError, AnalysisSourceError)


def sample(role='僕の役割は受付係だった', tail='費用を記録した'):
    snap = source_snapshot(1)
    snap['members'][0]['original'].update(memo=role+'。'+tail+'。', memo_action='')
    return snap


def proposal(snap, *, prompt='selected_material.v4', change=None):
    p = service.prepare_cumulative_category_units(OWNER, snap, prompt_version=prompt)
    fields = json.loads(p.messages()[1]['content'])['fields']
    text = fields[0]['text']; role, tail = text.rstrip('。').split('。')
    units = [dict(quote=role, node_kind='ROLE', parent_quote=None, scope_role=None,
        qualifiers=[dict(kind='EXPLICIT_ACTOR', quote='僕')] if role.startswith('僕') else []),
        dict(quote=tail, node_kind='ACTION_OR_NONACTION', parent_quote=None, scope_role=None, qualifiers=[])]
    data = dict(fields=[dict(field=1, units=units)])
    if change: change(data)
    raw = canonical(data)
    return replace(p, response=AnalysisModelQuotedParentUnitsResponse(p.request_ref,
        hashlib.sha256(canonical(p.messages()).encode()).hexdigest(), hashlib.sha256(raw.encode()).hexdigest(), 'stop', raw))


def build(snap=None, **kw):
    snap = sample() if snap is None else snap
    value = proposal(snap, **kw)
    artifact, coverage = service.build_cumulative_written_role_map(OWNER, snap, model_input=value, clause=True)
    return snap, value, artifact, coverage


@pytest.mark.parametrize('prompt', ['selected_material.v2', 'selected_material.v4'])
@pytest.mark.parametrize('copula', ['だった', 'ではなかった', 'ではありませんでした'])
@pytest.mark.parametrize('tail', ['費用を記録した', '予定を記録した', '僕は予定を記録しなかった'])
def test_only_role_is_adopted_with_partial_literal_and_complete_field_binding(prompt, copula, tail):
    snap, value, artifact, coverage = build(sample('僕の役割は受付係'+copula, tail), prompt=prompt)
    node, = artifact.graph.nodes
    assert node.node_kind == 'ROLE' and node.proposition.actor == 'SELF'
    assert node.proposition.role_state == 'WRITTEN_PAST_ROLE_CLAUSE'
    assert node.polarity == ('positive' if copula == 'だった' else 'negative')
    assert node.modality == 'fact' and node.temporal_scope == 'past' and not artifact.graph.edges
    assert node.selected_categories == ('仕事',) and node.selected_category_context
    assert coverage['mapped_count'] == coverage['unparsed_count'] == coverage['source_count'] == 1
    text = snap['members'][0]['original']['memo']; label = text.split('。')[0]
    e, = node.evidence_refs
    assert (e.scalar_start, e.scalar_end) == (0, len(label))
    assert e.utf8_start == e.field_utf8_start and e.utf8_end-e.utf8_start == len(label.encode())
    assert e.field_utf8_end-e.field_utf8_start == len(text.encode())
    assert e.literal_sha256 == hashlib.sha256(label.encode()).hexdigest()
    assert e.field_sha256 == hashlib.sha256(text.encode()).hexdigest()
    assert {g.missing_scope for g in artifact.graph.unknown_gaps} == {
        'SCENE', 'ATTENTION_OR_THOUGHT', 'ACTION_OR_NONACTION', 'IMMEDIATE_RESULT_OR_AFTERMATH', 'SOURCE_SCOPE'}
    visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
    body = artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
    assert len(visual['nodes']) == 1 and visual['edges'] == []
    assert tail not in body and label in body and 'まだ読み取れていない' in body
    with pytest.raises(ERRORS):
        service.build_cumulative_written_role_map(OWNER, snap, model_input=value)


def test_saved_read_requires_explicit_clause_and_never_calls_generation_compilers_or_authors():
    snap, value, artifact, coverage = build()
    raw = service.serialize_cumulative_written_role_map(OWNER, snap, model_input=value,
        artifact=artifact, coverage=coverage, clause=True)
    with ExitStack() as stack:
        for obj, name in [(MeaningExperienceEngine, 'generate'), (compiler, 'compile_observed_graph'),
            (compiler, 'compile_analysis_unit_candidates'), (compiler, 'compile_model_written_role_graph'),
            (compiler, 'compile_model_written_role_action_graph'), (compiler, 'compile_model_written_role_clause_graph'),
            (author, 'realize_model_written_role_graph'), (author, 'realize_analysis_unit_candidates')]:
            stack.enter_context(patch.object(obj, name, side_effect=AssertionError('saved regeneration')))
        assert service.reload_cumulative_written_role_map(OWNER, snap, raw, clause=True) == (artifact, coverage)
    assert json.loads(raw)['state']['response']['raw'] == value.response.raw
    for flags in ({}, dict(with_action=True), dict(with_action=True, clause=True), dict(clause=1)):
        with pytest.raises(ERRORS): service.reload_cumulative_written_role_map(OWNER, snap, raw, **flags)


@pytest.mark.parametrize('tail', ['僕は予定を記録したと思った', '僕は予定を記録している',
    '僕は予定を記録したかもしれない', '僕は予定を記録したという話だった',
    '僕は予定を記録したわけではない', '僕は予定を記録したが違った',
    '僕は「予定を記録した」と言った', '昨日、予定を記録した',
    'その後、予定を記録した', '予定を記録した。まだ分からない'])
def test_open_uncertain_report_or_extra_scope_cannot_close_the_role(tail):
    snap = sample(tail=tail)
    # Proposal still points to source; arbitrary tail splitting is not a gold reader.
    if '。' in tail:
        with pytest.raises(ERRORS):
            compiler._written_role_clause_witness(snap['members'][0]['original']['memo'])
    else:
        with pytest.raises(ERRORS): build(snap)


@pytest.mark.parametrize('role', ['僕の役割は受付係だったと思った', '僕の役割は受付係かもしれない',
    '姉の役割は受付係だった', '僕の役割は受付係だったという話だった'])
def test_role_itself_requires_explicit_self_finite_source(role):
    with pytest.raises(ERRORS): build(sample(role=role))


@pytest.mark.parametrize('change', ['kind', 'false_actor', 'false_negative', 'modifier', 'whole_quote',
    'role_child_tail', 'overlap', 'no_role'])
def test_model_proposal_cannot_change_or_extend_the_source_witness(change):
    def edit(data):
        units=data['fields'][0]['units']; root=units[0]
        if change=='kind': root['node_kind']='SCENE'
        if change=='false_actor': root['qualifiers']=[dict(kind='EXPLICIT_ACTOR',quote='受付係')]
        if change=='false_negative': root['qualifiers']=[dict(kind='NEGATION',quote='だった')]
        if change=='modifier': root['qualifiers']=[dict(kind='WRITTEN_MODIFIER',quote='だった')]
        if change=='whole_quote': root['quote'] += '。'+units[1]['quote']
        if change=='role_child_tail': units[1].update(node_kind=None,parent_quote=root['quote'],scope_role='CONTENT_TARGET')
        if change=='overlap': units.append(dict(quote='受付係',node_kind='SCENE',parent_quote=None,scope_role=None,qualifiers=[]))
        if change=='no_role': units.pop(0)
    with pytest.raises(ERRORS): build(change=edit)


@pytest.mark.parametrize('change', ['polarity', 'source_parts', 'state', 'category', 'scalar', 'utf8',
    'literal', 'field_hash', 'evidence_id', 'field_bounds', 'gap', 'edge', 'text', 'diagram', 'id',
    'raw', 'response_hash', 'coverage', 'schema'])
def test_saved_original_meaning_remainder_and_views_are_immutable(change):
    snap,value,artifact,coverage=build()
    saved=json.loads(service.serialize_cumulative_written_role_map(OWNER,snap,model_input=value,
        artifact=artifact,coverage=coverage,clause=True))
    a=saved['state']['artifact']; g=a['graph']; n=g['nodes'][0]; e=n['evidence_refs'][0]
    if change=='polarity': n['polarity']=n['proposition']['polarity']='negative'
    if change=='source_parts': n['proposition']['source_parts'][0][2]-=1
    if change=='state': n['proposition']['role_state']='WRITTEN_PAST_ROLE'
    if change=='category': n['selected_categories']=['生活']
    if change=='scalar': e['scalar_end']+=1
    if change=='utf8': e['utf8_end']+=1
    if change=='literal': e['literal_sha256']='0'*64
    if change=='field_hash': e['field_sha256']='0'*64
    if change=='evidence_id': e['evidence_id']='changed'
    if change=='field_bounds': e['field_utf8_end']=e['utf8_end']
    if change=='gap': g['unknown_gaps'].pop()
    if change=='edge': g['edges'].append({})
    if change=='text': a['text']['text']+='changed'
    if change=='diagram': a['diagram']['nodes'][0]['visible_label']+='changed'
    if change=='id': a['artifact_id']='artifact:changed'
    if change=='raw': saved['state']['response']['raw']+=' '
    if change=='response_hash': saved['state']['response']['raw_sha256']='0'*64
    if change=='coverage': saved['coverage']['unparsed_count']=0
    if change=='schema': saved['state']['schema_version']='cocolon.cmee.analysis_model_written_role_state.v1'
    with pytest.raises(ERRORS): service.reload_cumulative_written_role_map(OWNER,snap,canonical(saved),clause=True)


@pytest.mark.parametrize('change', ['memo_action', 'record', 'category', 'record_id', 'owner', 'period'])
def test_saved_clause_is_bound_to_the_entire_original_snapshot(change):
    snap,value,artifact,coverage=build()
    raw=service.serialize_cumulative_written_role_map(OWNER,snap,model_input=value,artifact=artifact,coverage=coverage,clause=True)
    other=copy.deepcopy(snap); original=other['members'][0]['original']
    if change=='memo_action': original['memo_action']='予定を記録した。'
    if change=='record': original['memo']+='追記。'
    if change=='category': original['category']=['生活']
    if change=='record_id': original['id']='00000000-0000-0000-0000-000000000099'
    if change=='owner':
        with pytest.raises(ERRORS):
            service.reload_cumulative_written_role_map('00000000-0000-0000-0000-000000000002',snap,raw,clause=True)
        return
    if change=='period': other['now']='2026-11-02T08:00:00+00:00';other['period_end']=other['now']
    with pytest.raises(ERRORS): service.reload_cumulative_written_role_map(OWNER,other,raw,clause=True)
