"""Both source-proved clauses reach the ordinary map; private files stay old."""
from contextlib import ExitStack
from dataclasses import replace
import hashlib
from unittest.mock import patch

import pytest
import analysis_cumulative_service as service
from cocolon_meaning_experience_engine.cores.analysis import intent_compiler as compiler
from cocolon_meaning_experience_engine.cores.analysis import observed_route_realizer as author
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as admission
from test_analysis_model_observed_roles import material, propose, OWNER


def sample(role_negative=False, action_negative=False, punctuation='。'):
    snap = material('role')
    role = '僕の役割は受付係'+('ではなかった' if role_negative else 'だった')
    action = '僕は費用を記録'+('しなかった' if action_negative else 'した')
    snap['members'][0]['original']['memo'] = role+punctuation+action+punctuation
    return snap


def value_for(snap, change=None):
    # This synthetic helper accepts all three existing sentence terminators.
    normalized = snap['members'][0]['original']['memo'].replace('．','。').replace('.','。')
    original = snap['members'][0]['original']['memo']
    snap['members'][0]['original']['memo'] = normalized
    prepared = propose(snap, change=change)
    snap['members'][0]['original']['memo'] = original
    if original == normalized: return prepared
    import json
    from test_analysis_model_quoted_parent_units import call
    target = service.prepare_cumulative_category_units(OWNER,snap,prompt_version='selected_material.v4')
    return call(target,json.loads(prepared.response.raw))


@pytest.mark.parametrize('role_negative',[False,True])
@pytest.mark.parametrize('action_negative',[False,True])
@pytest.mark.parametrize('punctuation',['。','.'])
def test_both_existing_witnesses_keep_original_coordinates_and_private_clause(role_negative,action_negative,punctuation):
    snap=sample(role_negative,action_negative,punctuation);value=value_for(snap)
    old,old_counts=service.build_cumulative_written_role_map(OWNER,snap,model_input=value,clause=True)
    saved=service.serialize_cumulative_written_role_map(OWNER,snap,model_input=value,artifact=old,coverage=old_counts,clause=True)
    new,counts=service.build_cumulative_map(OWNER,snap,model_input=value)
    assert len(old.graph.nodes)==1 and old_counts['unparsed_count']==1
    assert new.graph.nodes[0]==old.graph.nodes[0]
    role,action=new.graph.nodes
    assert role.polarity==('negative' if role_negative else 'positive')
    assert action.polarity==('negative' if action_negative else 'positive')
    assert action.proposition.actor=='SELF' and action.modality=='fact' and action.temporal_scope=='past'
    assert counts['source_count']==counts['processed_count']==counts['mapped_count']==1
    assert counts['unparsed_count']==0 and new.graph.edges==()
    assert new.graph.unknown_gaps==compiler._written_role_action_gaps()
    frozen,fields,_=admission._admit_quoted_parent_units(value.request,value)
    shared=compiler.compile_observed_graph(frozen).nodes[0]
    assert action==replace(shared,node_ref='n2')
    text=snap['members'][0]['original']['memo'];e=action.evidence_refs[0]
    assert text[e.scalar_start:e.scalar_end]==action.visible_label
    assert e.literal_sha256==hashlib.sha256(action.visible_label.encode()).hexdigest()
    assert e.field_sha256==hashlib.sha256(text.encode()).hexdigest()
    assert action.proposition.source_parts[0]==('SELF_TOPIC',0,2)
    body=new.safe_text_projection(authenticated_owner_scope=OWNER)['text']
    assert '記録された役割' in body and ('行わなかった' if action_negative else '実行済み') in body
    assert 'まだ読み取れていない' not in body and 'つながり' in body
    with ExitStack() as stack:
        for obj,name in [(compiler,'compile_observed_graph'),(compiler,'compile_model_written_role_clause_graph'),
            (compiler,'compile_model_written_role_clause_action_graph'),(author,'realize_model_written_role_graph')]:
            stack.enter_context(patch.object(obj,name,side_effect=AssertionError('saved compile')))
        assert service.reload_cumulative_written_role_map(OWNER,snap,saved,clause=True)==(old,old_counts)


def test_fullwidth_stop_keeps_the_prior_role_until_shared_source_action_is_supported():
    snap=sample(punctuation='．')
    a,c=service.build_cumulative_map(OWNER,snap,model_input=value_for(snap))
    assert [n.node_kind for n in a.graph.nodes]==['ROLE'] and c['unparsed_count']==1


@pytest.mark.parametrize('negative',[False,True])
@pytest.mark.parametrize('root_style',['full','predicate'])
def test_tail_model_qualifiers_and_target_keep_original_nonzero_coordinates(negative,root_style):
    snap=sample(action_negative=negative)
    def change(packet):
        units=packet['fields'][0]['units'];action=units[1]
        if root_style=='predicate':action['quote']=action['quote'][2:]
        action['qualifiers']=([dict(kind='EXPLICIT_ACTOR',quote='僕')] if root_style=='full' else [])
        if negative:action['qualifiers'].append(dict(kind='NEGATION',quote='しなかった'))
        units.append(dict(quote='費用',node_kind=None,parent_quote=action['quote'],scope_role='CONTENT_TARGET',qualifiers=[]))
    value=value_for(snap,change)
    a,c=service.build_cumulative_map(OWNER,snap,model_input=value)
    assert len(a.graph.nodes)==2 and c['unparsed_count']==0
    assert a.graph.nodes[1].polarity==('negative' if negative else 'positive')


@pytest.mark.parametrize('defect',['missing','kind','false_actor','false_negation','modifier','dependent','extra_root'])
def test_bad_action_proposal_keeps_only_previously_proved_role(defect):
    snap=sample()
    def change(packet):
        units=packet['fields'][0]['units'];u=units[1]
        if defect=='missing':units.pop()
        if defect=='kind':u['node_kind']='SCENE'
        if defect=='false_actor':u['qualifiers']=[dict(kind='EXPLICIT_ACTOR',quote='費用')]
        if defect=='false_negation':u['qualifiers']=[dict(kind='NEGATION',quote='した')]
        if defect=='modifier':u['qualifiers']=[dict(kind='WRITTEN_MODIFIER',quote='記録')]
        if defect=='dependent':u.update(node_kind=None,parent_quote=units[0]['quote'],scope_role='CONTENT_TARGET')
        if defect=='extra_root':units.append(dict(quote='費用',node_kind='SCENE',parent_quote=None,scope_role=None,qualifiers=[]))
    value=value_for(snap,change)
    a,c=service.build_cumulative_map(OWNER,snap,model_input=value)
    # A role-owned tail is rejected by the prior clause witness too.
    if defect=='dependent':assert a is None
    else:assert a and [n.node_kind for n in a.graph.nodes]==['ROLE'] and c['unparsed_count']==1


@pytest.mark.parametrize('tail',['費用を記録した','姉は費用を記録した','僕は費用を記録したかもしれない',
    '僕は費用を記録したという話だった','僕は費用を記録したい','昨日、僕は費用を記録した',
    'その後、僕は費用を記録した','僕は「費用を記録した」と言った','僕は費用を記録した。まだ分からない'])
def test_omitted_other_uncertain_reported_and_extra_source_never_gain_self_action(tail):
    snap=sample();snap['members'][0]['original']['memo']='僕の役割は受付係だった。'+tail+'。'
    a,c=service.build_cumulative_map(OWNER,snap,model_input=propose(snap))
    assert a is None or all(n.node_kind!='ACTION_OR_NONACTION' for n in a.graph.nodes)
    assert c['unparsed_count']==1


@pytest.mark.parametrize('defect',['offset','utf8','field','literal','actor','extra_gap','missing_action','edge','source_scope_bypass'])
def test_complete_surface_cannot_drop_unread_without_exact_tail_evidence(defect):
    snap=sample();a,_=service.build_cumulative_map(OWNER,snap,model_input=value_for(snap))
    role,action=a.graph.nodes;e=action.evidence_refs[0];graph=a.graph
    if defect=='offset':action=replace(action,evidence_refs=(replace(e,scalar_start=0),))
    if defect=='utf8':action=replace(action,evidence_refs=(replace(e,utf8_start=e.field_utf8_start),))
    if defect=='field':action=replace(action,evidence_refs=(replace(e,field_sha256='0'*64),))
    if defect=='literal':action=replace(action,evidence_refs=(replace(e,literal_sha256='0'*64),))
    if defect=='actor':action=replace(action,proposition=replace(action.proposition,actor='UNSPECIFIED'))
    if defect=='source_scope_bypass':
        label=action.visible_label.replace('した','しなかった')
        action=replace(action,visible_label=label,proposition=compiler._proposition(label),polarity='negative')
    graph=replace(graph,nodes=(role,action))
    if defect=='extra_gap':graph=replace(graph,unknown_gaps=graph.unknown_gaps[:-1])
    if defect=='missing_action':graph=replace(graph,nodes=(role,))
    if defect=='edge':graph=replace(graph,source_updates=('forged',))
    if defect=='source_scope_bypass':graph=replace(graph,unknown_gaps=graph.unknown_gaps+(
        compiler.UnknownGap('g5',('n1',),'SOURCE_SCOPE','UNSUPPORTED_OR_UNCERTAIN_SOURCE_SCOPE'),))
    bad=replace(a,graph=graph)
    with pytest.raises(compiler.AnalysisSourceError):bad.safe_projection(authenticated_owner_scope=OWNER)
