"""Offline kinds-only proposals: trusted call binding and source-owned quotes."""
import asyncio
import copy
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
from unittest.mock import patch
from uuid import UUID

import pytest
import analysis_cumulative_service as service
from analysis_observed_service import private_storage_evidence, _checked_projection
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import (
    AnalysisModelFieldKindsResponse, AnalysisSemanticError, AnalysisSemanticUnsupported,
    canonical, prepare_analysis_model_field_kinds)
from cocolon_meaning_experience_engine.cores.analysis.source_adapter import (
    AnalysisSourceError, AnalysisSupplement, commitment)
from test_analysis_model_fields import sample
from test_analysis_cumulative import OWNER


def synthetic_call(prepared, *, raw=None, kinds=None, finish='stop'):
    # Simulate one trusted caller: capture input identity BEFORE obtaining raw.
    request_ref = prepared.request_ref
    sent = prepared.messages()
    messages_sha256 = hashlib.sha256(canonical(sent).encode()).hexdigest()
    if raw is None:
        fields = json.loads(sent[1]['content'])['fields']
        selected = kinds if kinds is not None else ['UNRESOLVED', 'ACTION_OR_NONACTION', 'IMMEDIATE_RESULT_OR_AFTERMATH']
        assert len(selected) == len(fields)
        raw = json.dumps({'fields': [dict(field=f['field'], node_kind=k)
            for f,k in zip(fields, selected)]}, ensure_ascii=False)
    response = AnalysisModelFieldKindsResponse(request_ref, messages_sha256,
        hashlib.sha256(raw.encode()).hexdigest(), finish, raw)
    return replace(prepared, response=response)


def prepared(snap=None):
    return service.prepare_cumulative_model_field_kinds(OWNER, sample() if snap is None else snap)


def test_kinds_only_reaches_existing_graph_and_preserves_source_scope():
    snap=sample(); value=synthetic_call(prepared(snap))
    material=json.loads(value.messages()[1]['content'])
    assert [f['field'] for f in material['fields']]==[1,2,3]
    assert all(set(f)=={'field','field_path','text'} for f in material['fields'])
    assert 'request_ref' not in material and 'source_set_ref' not in material
    artifact,coverage=service.build_cumulative_map(OWNER,snap,model_input=value)
    assert coverage['mapped_count']==coverage['unparsed_count']==coverage['source_count']==2
    projection=artifact.safe_projection(authenticated_owner_scope=OWNER)
    assert projection['edges']==[] and len(projection['nodes'])==2
    assert [n['visible_label'] for n in projection['nodes']]==[
        snap['members'][0]['original']['memo_action']+'（原文・分類候補）',
        snap['members'][1]['original']['memo']+'（原文・分類候補）']
    assert all(n.proposition is None and n.polarity==n.modality==n.temporal_scope=='AS_WRITTEN_UNRESOLVED'
        for n in artifact.graph.nodes)
    assert artifact.graph.nodes[-1].quoted_field.evidence.scalar_end==26
    _checked_projection(projection,str(UUID(artifact.artifact_id[9:])))
    assert '昨日' not in json.dumps(private_storage_evidence(artifact),ensure_ascii=False)


@pytest.mark.parametrize('change',['missing','duplicate','extra','reverse','bool','float','string','zero','unknown_kind','extra_key','v1_keys','extra_root'])
def test_raw_shape_and_order_fail_closed(change):
    p=prepared(); data=json.loads(synthetic_call(p).response.raw)
    if change=='missing': data['fields'].pop()
    if change=='duplicate': data['fields'][1]=copy.deepcopy(data['fields'][0])
    if change=='extra': data['fields'].append(copy.deepcopy(data['fields'][0]))
    if change=='reverse': data['fields'].reverse()
    if change in {'bool','float','string','zero'}: data['fields'][0]['field']={'bool':True,'float':1.0,'string':'1','zero':0}[change]
    if change=='unknown_kind': data['fields'][0]['node_kind']='PERSONALITY'
    if change=='extra_key': data['fields'][0]['cause']='invented'
    if change=='v1_keys': data['fields'][0].update(quote='x',start=0,end=1)
    if change=='extra_root': data['request_ref']=p.request_ref
    with pytest.raises(AnalysisSemanticError):
        service.build_cumulative_map(OWNER,sample(),model_input=synthetic_call(p,raw=json.dumps(data)))


@pytest.mark.parametrize('raw',['duplicate_root','duplicate_row','{"fields":NaN}','```json\n{}\n```'])
def test_duplicate_keys_nonfinite_and_wrappers_are_not_repaired(raw):
    p=prepared()
    good=synthetic_call(p).response.raw
    if raw=='duplicate_root': raw='{"fields":'+json.dumps(json.loads(good)['fields'])+','+good[1:]
    if raw=='duplicate_row': raw=good.replace('"field": 1','"field": 1, "field": 1',1)
    with pytest.raises(AnalysisSemanticError,match='analysis_semantic_json_invalid'):
        service.build_cumulative_map(OWNER,sample(),model_input=synthetic_call(p,raw=raw))


@pytest.mark.parametrize('finish',[None,'length','timeout','error','unknown'])
def test_finish_failure_precedes_complete_json(finish):
    with pytest.raises(AnalysisSemanticError,match='generation_incomplete'):
        service.build_cumulative_map(OWNER,sample(),model_input=synthetic_call(prepared(),finish=finish))


@pytest.mark.parametrize('change',['whole_response','raw_only','messages_hash','request_ref','no_response'])
def test_response_is_bound_to_the_actual_call_context(change):
    p=prepared(); value=synthetic_call(p)
    other=sample(); other['members'][0]['original']['memo']='別の入力について考えた。'
    other_value=synthetic_call(prepared(other),kinds=['ROLE','SCENE','UNRESOLVED'])
    if change=='whole_response': value=replace(p,response=other_value.response)
    if change=='raw_only': value=replace(value,response=replace(value.response,raw=other_value.response.raw))
    if change=='messages_hash': value=replace(value,response=replace(value.response,messages_sha256=other_value.response.messages_sha256))
    if change=='request_ref': value=replace(value,response=replace(value.response,request_ref=other_value.response.request_ref))
    if change=='no_response': value=p
    with pytest.raises(AnalysisSemanticError,match='response_binding_invalid'):
        service.build_cumulative_map(OWNER,sample(),model_input=value)


@pytest.mark.parametrize('change',['guard','version','owner'])
def test_source_changes_cannot_rebind_a_prior_response(change):
    snap=sample(); value=synthetic_call(prepared(snap)); owner=OWNER
    if change=='guard': snap['guard']='analysis-db-cumulative-v1:'+'b'*64
    if change=='version': snap['members'][0]['original']['memo']+='今は違う。'
    if change=='owner': owner=str(UUID(int=2))
    with pytest.raises(AnalysisSemanticError):
        service.build_cumulative_map(owner,snap,model_input=value)


def test_v1_default_and_its_model_request_are_unchanged():
    snap=sample(); old=service.prepare_cumulative_model_fields(OWNER,snap); new=prepared(snap)
    assert old.request_ref!=new.request_ref
    old_material=json.loads(old.messages()[1]['content'])
    assert 'request_ref' in old_material and 'field_ref' in old_material['fields'][0]
    assert 'quoteはtext全文' in old.messages()[0]['content']
    legacy,coverage=service.build_cumulative_map(OWNER,snap)
    assert legacy is None and coverage['mapped_count']==0 and coverage['unparsed_count']==2
    with patch.object(service,'prepare_cumulative_model_field_kinds',side_effect=AssertionError('not default')):
        assert service.build_cumulative_map(OWNER,snap)[0] is None


def test_all_unresolved_and_a_wholly_unresolved_record():
    p=prepared(); snap=sample()
    artifact,c=service.build_cumulative_map(OWNER,snap,model_input=synthetic_call(p,kinds=['UNRESOLVED']*3))
    assert artifact is None and c['mapped_count']==0 and c['unparsed_count']==2
    artifact,c=service.build_cumulative_map(OWNER,snap,model_input=synthetic_call(p,kinds=['UNRESOLVED','ACTION_OR_NONACTION','UNRESOLVED']))
    assert c['mapped_count']==1 and c['unparsed_count']==2
    assert all(g.between_node_refs for g in artifact.graph.unknown_gaps)
    _checked_projection(artifact.safe_projection(authenticated_owner_scope=OWNER),str(UUID(artifact.artifact_id[9:])))


def test_safety_supplement_correction_and_comparison_are_not_bypassed():
    p=prepared(); member=p.request.members[0]
    for text in ['今日は休んだ。','「今日は休んだ」を撤回します。']:
        s=AnalysisSupplement('answer',OWNER,member.saved_record_ref,member.saved_record_version,text,commitment(text))
        request=replace(p.request,members=(replace(member,supplements=(s,)),))
        with pytest.raises(AnalysisSemanticUnsupported):
            prepare_analysis_model_field_kinds(request,source_guard=p.source_guard)
    with pytest.raises(AnalysisSemanticUnsupported):
        prepare_analysis_model_field_kinds(replace(p.request,comparison_previous_request=p.request),source_guard=p.source_guard)
    snap=sample();snap['members'][1]['original']['memo']='死にたい。'
    with pytest.raises(AnalysisSourceError,match='analysis_separate_safety_required'):
        prepared(snap)


def test_synthetic_call_real_sql_commit_and_non_generating_read(monkeypatch):
    if not os.environ.get('Q2_PGLITE_MODULE'):
        pytest.skip('PostgreSQL WASM dependency is not configured')
    from test_emlis_q3_application import Q3Database
    db=Q3Database()
    try:
        db.migrate()
        for name in ('20261003134440_analysis_observed_artifacts.sql','20261004041627_analysis_period_comparison.sql','20261101080144_cumulative_watashi_map.sql'):
            db.proc.stdin.write(json.dumps({'script':True,'sql':(Path(__file__).parents[2]/'supabase/migrations'/name).read_text()})+'\n')
            db.proc.stdin.flush(); assert 'code' not in json.loads(db.proc.stdout.readline())
        db.query('insert into auth.users values ($1)',[OWNER])
        db.query("insert into public.profiles values ($1,'free')",[OWNER])
        for raw in sample()['members']:
            r=raw['original']
            db.query('insert into public.emotions values ($1,$2,$3,$4,$5,$6,$7,$8)',[r['id'],OWNER,r['created_at'],r['memo'],r['memo_action'],r['category'],r['emotions'],json.dumps(r['emotion_details'])])
        async def rpc(name,payload):
            args=','.join(f'{k} => ${i}' for i,k in enumerate(payload,1))
            params=[json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for v in payload.values()]
            result=await asyncio.to_thread(db.query,f'select public.{name}({args}) as value',params,'service_role')
            assert 'code' not in result,result
            return result['rows'][0]['value']
        run=asyncio.run
        snap=run(rpc('analysis_cumulative_source_snapshot',{'p_user_id':OWNER}))
        artifact,coverage=service.build_cumulative_map(OWNER,snap,model_input=synthetic_call(prepared(snap)))
        projection=artifact.safe_projection(authenticated_owner_scope=OWNER)
        text=artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
        private=private_storage_evidence(artifact)
        private.update(coverage=coverage,source_record_refs=[x['original']['id'] for x in snap['members']])
        rid=run(rpc('analysis_cumulative_commit',dict(p_user_id=OWNER,p_guard=snap['guard'],p_artifact_id=artifact.artifact_id,p_private_evidence=private,p_projection=projection,p_text=text,p_start=snap['period_start'],p_end=snap['period_end'])))
        monkeypatch.setattr(service,'_rpc',rpc)
        with patch.object(MeaningExperienceEngine,'generate',side_effect=AssertionError('read must not generate')):
            for history in (False,True):
                row=run(service.read_maps(OWNER,history=history))['items'][0]
                assert row['id']==rid and row['content_text']==text
                assert row['content_json']['watashiMap']==projection
                assert row['content_json']['map_context']==coverage
        db.query('delete from public.emotions where id=$1',[snap['members'][0]['original']['id']])
        assert run(service.read_maps(OWNER,history=True))['items']==[]
    finally:
        db.proc.stdin.close();db.proc.wait(timeout=10)
