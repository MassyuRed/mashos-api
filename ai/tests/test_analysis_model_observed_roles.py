"""Existing ROLE witnesses reach the ordinary row without a new saved schema."""
import asyncio
from contextlib import ExitStack
from dataclasses import replace
import json
from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest
import analysis_cumulative_service as service
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.cores.analysis import intent_compiler as compiler
from cocolon_meaning_experience_engine.cores.analysis import observed_route_realizer as author
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as admission
from test_analysis_cumulative import OWNER, source_snapshot
from test_analysis_model_quoted_parent_units import call


def material(mode, negative=False, swap=False):
    snap=source_snapshot(1)
    role='僕の役割は受付係'+('ではなかった。' if negative else 'だった。')
    action='僕は費用を記録した。'
    memo,other=(role,action) if mode=='pair' else (role+'費用を記録した。','') if mode=='clause' else (role,'')
    if swap:memo,other=other,memo
    snap['members'][0]['original'].update(memo=memo,memo_action=other)
    return snap


def propose(snap, *, prompt='selected_material.v4', change=None):
    prepared=service.prepare_cumulative_category_units(OWNER,snap,prompt_version=prompt)
    rows=json.loads(prepared.messages()[1]['content'])['fields']
    packet=dict(fields=[dict(field=f['field'],units=[dict(quote=text,
        node_kind='ROLE' if 'の役割は' in text else 'ACTION_OR_NONACTION',
        parent_quote=None,scope_role=None,qualifiers=[])
        for text in f['text'].rstrip('。').split('。')]) for f in rows])
    if change:change(packet)
    return call(prepared,packet)


@pytest.mark.parametrize('mode',['role','pair','clause'])
@pytest.mark.parametrize('negative',[False,True])
@pytest.mark.parametrize('prompt',['selected_material.v2','selected_material.v4'])
def test_existing_role_graph_is_shared_but_ordinary_identity_and_coverage_are_used(mode,negative,prompt):
    snap=material(mode,negative);value=propose(snap,prompt=prompt)
    flags=dict(with_action=mode=='pair',clause=mode=='clause')
    private,private_counts=service.build_cumulative_written_role_map(OWNER,snap,model_input=value,**flags)
    ordinary,counts=service.build_cumulative_map(OWNER,snap,model_input=value)
    assert ordinary.graph==private.graph and counts==private_counts
    assert ordinary.source_members==private.source_members and ordinary.category_records==private.category_records
    UUID(ordinary.artifact_id[9:])
    assert ordinary.artifact_id!=private.artifact_id and ordinary.graph.edges==()
    role=next(n for n in ordinary.graph.nodes if n.node_kind=='ROLE')
    assert role.proposition.actor=='SELF' and role.temporal_scope=='past' and role.modality=='fact'
    assert role.polarity==('negative' if negative else 'positive')
    assert role.selected_categories==('仕事',) and counts['unparsed_count']==int(mode=='clause')
    assert counts['mapped_count']==counts['processed_count']==counts['source_count']==1
    assert len(ordinary.graph.nodes)==(2 if mode=='pair' else 1)
    gaps={g.missing_scope for g in ordinary.graph.unknown_gaps}
    assert ('SOURCE_SCOPE' in gaps)==(mode=='clause')
    assert ('ROUTE_CONNECTION' in gaps)==(mode=='pair')
    text=ordinary.safe_text_projection(authenticated_owner_scope=OWNER)['text']
    assert '受付係' in text and '記録された役割' in text
    if mode=='clause':assert '費用を記録' not in text and 'まだ読み取れていない' in text
    # No semantic dispatch or new ROLE is added to the provider-free route.
    finite,finite_counts=service.build_cumulative_map(OWNER,snap)
    assert finite is None or all(n.node_kind!='ROLE' for n in finite.graph.nodes)
    assert finite_counts['unparsed_count']==1


@pytest.mark.parametrize('mode',['role','pair'])
@pytest.mark.parametrize('negative',[False,True])
def test_swapped_complete_fields_use_existing_same_source_witness(mode,negative):
    snap=material(mode,negative,swap=True)
    a,c=service.build_cumulative_map(OWNER,snap,model_input=propose(snap))
    assert a and c['unparsed_count']==0
    assert next(n for n in a.graph.nodes if n.node_kind=='ROLE').evidence_refs[0].field_path=='memo_action'
    assert not a.graph.edges


@pytest.mark.parametrize('mode',['role','pair','clause'])
@pytest.mark.parametrize('defect',['kind','false_actor','false_negation','modifier','empty'])
def test_source_role_cannot_override_an_incorrect_model_unit(mode,defect):
    snap=material(mode)
    def change(packet):
        units=packet['fields'][0]['units'];u=units[0]
        if defect=='kind':u['node_kind']='SCENE'
        elif defect=='empty':units.clear()
        else:u['qualifiers']=[dict(kind={'false_actor':'EXPLICIT_ACTOR',
            'false_negation':'NEGATION','modifier':'WRITTEN_MODIFIER'}[defect],
            quote='受付係' if defect=='false_actor' else 'だった')]
    a,c=service.build_cumulative_map(OWNER,snap,model_input=propose(snap,change=change))
    assert a is None or all(n.node_kind!='ROLE' for n in a.graph.nodes)
    assert c['unparsed_count']==1
    if mode=='pair':assert a and len(a.graph.nodes)==1 and a.graph.nodes[0].node_kind=='ACTION_OR_NONACTION'


@pytest.mark.parametrize('memo',['姉の役割は受付係だった。','僕の役割は受付係だったかもしれない。',
    '友人は「僕の役割は受付係だった」と言った。','僕の役割は受付係だったという話だった。',
    '僕の役割は受付係だった。まだ分からない。'])
def test_nonwitnessed_role_never_becomes_an_observed_role(memo):
    snap=material('role');snap['members'][0]['original']['memo']=memo
    a,c=service.build_cumulative_map(OWNER,snap,model_input=propose(snap))
    assert a is None and c['mapped_count']==0 and c['unparsed_count']==1


@pytest.mark.parametrize('mode',['role','pair','clause'])
def test_normal_file_and_rpc_saved_read_never_calls_a_model_compiler_or_author(mode,tmp_path):
    snap=material(mode);value=propose(snap)
    a,c=service.build_cumulative_map(OWNER,snap,model_input=value)
    row=dict(id=str(UUID(a.artifact_id[9:])),source_profile=service.PROFILE,report_mode='standard',
        content_text=a.safe_text_projection(authenticated_owner_scope=OWNER)['text'],
        content_json=dict(report_mode='standard',watashiMap=a.safe_projection(authenticated_owner_scope=OWNER),map_context=c))
    expected=dict(items=[row],subscription_tier='free',matched=True,history_limit=2)
    path=tmp_path/'normal.json';path.write_text(admission.canonical(expected))
    rpc=AsyncMock(return_value=json.loads(path.read_text()))
    with ExitStack() as stack:
        for obj,name in [(MeaningExperienceEngine,'generate'),(compiler,'compile_observed_graph'),
            (compiler,'compile_model_observed_actions'),(compiler,'compile_model_written_role_graph'),
            (compiler,'compile_model_written_role_action_graph'),(compiler,'compile_model_written_role_clause_graph'),
            (author,'realize_observed_graph'),(author,'realize_model_written_role_graph'),
            (admission,'generate_analysis_model_observed_actions')]:
            stack.enter_context(patch.object(obj,name,side_effect=AssertionError('saved generation')))
        stack.enter_context(patch.object(service,'_rpc',rpc))
        assert asyncio.run(service.read_maps(OWNER,report_id=row['id']))==expected
    assert rpc.call_args.args[1]['p_user_id']==OWNER
    # Reuse the private serialization contract and prove its unchanged output.
    flags=dict(with_action=mode=='pair',clause=mode=='clause')
    old,counts=service.build_cumulative_written_role_map(OWNER,snap,model_input=value,**flags)
    saved=service.serialize_cumulative_written_role_map(OWNER,snap,model_input=value,artifact=old,coverage=counts,**flags)
    with patch.object(MeaningExperienceEngine,'generate',side_effect=AssertionError('model')):
        assert service.reload_cumulative_written_role_map(OWNER,snap,saved,**flags)==(old,counts)
    assert value.response.raw not in admission.canonical(service.private_storage_evidence(a))


@pytest.mark.parametrize('mode',['role','pair','clause'])
@pytest.mark.parametrize('defect',['owner','record','category','hash'])
def test_role_consumer_preserves_response_and_source_binding(mode,defect):
    snap=material(mode);value=propose(snap);owner=OWNER
    if defect=='owner':owner='00000000-0000-0000-0000-000000000002'
    if defect=='record':snap['members'][0]['original']['memo']+='変更'
    if defect=='category':snap['members'][0]['original']['category']=['生活']
    if defect=='hash':value=replace(value,response=replace(value.response,raw_sha256='0'*64))
    with pytest.raises((admission.AnalysisSemanticError,compiler.AnalysisSourceError)):
        service.build_cumulative_map(owner,snap,model_input=value)
