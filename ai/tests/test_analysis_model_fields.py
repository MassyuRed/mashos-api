"""Explicit model fields: source integrity, unresolved meaning and SQL replay."""
import asyncio
import copy
from dataclasses import replace
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
    AnalysisSemanticError, AnalysisSemanticUnsupported, prepare_analysis_model_fields)
from cocolon_meaning_experience_engine.cores.analysis.source_adapter import (
    AnalysisSourceError, AnalysisSupplement, commitment)
from test_analysis_cumulative import OWNER, source_snapshot


def sample():
    snap = source_snapshot(2)
    snap['members'][0]['original'].update(
        memo='断ったことを後悔してはいない。でも、相手がどう思ったかは分からない。',
        memo_action='疲れていたので、今日の集まりへの誘いは断った。')
    snap['members'][1]['original'].update(
        memo='昨日は分からなかった問題が、今日は解けてうれしい。🙂', memo_action='')
    return snap


def packet(prepared, kinds=None):
    material = json.loads(prepared.messages()[1]['content'])
    kinds = kinds or ['UNRESOLVED','ACTION_OR_NONACTION','IMMEDIATE_RESULT_OR_AFTERMATH']
    return dict(schema_version=material['schema_version'], request_ref=material['request_ref'],
        source_set_ref=material['source_set_ref'], fields=[dict(field_ref=f['field_ref'],
        node_kind=k, quote=f['text'], start=0, end=len(f['text'])) for f,k in zip(material['fields'], kinds)])


def candidate(prepared, data=None):
    return replace(prepared, raw=json.dumps(data if data is not None else packet(prepared), ensure_ascii=False), finish_reason='stop')


def test_source_reaches_normal_graph_as_unresolved_candidate():
    snap=sample(); old, counts=service.build_cumulative_map(OWNER,snap)
    assert old is None and counts['mapped_count']==0
    prepared=service.prepare_cumulative_model_fields(OWNER,snap)
    artifact, counts=service.build_cumulative_map(OWNER,snap,model_input=candidate(prepared))
    assert counts['mapped_count']==counts['unparsed_count']==counts['processed_count']==2
    projection=artifact.safe_projection(authenticated_owner_scope=OWNER)
    assert len(projection['nodes'])==2 and projection['edges']==[]
    assert snap['members'][0]['original']['memo_action']+'（原文・分類候補）'==projection['nodes'][0]['visible_label']
    assert all(n.proposition is None and n.polarity=='AS_WRITTEN_UNRESOLVED' for n in artifact.graph.nodes)
    assert len(artifact.graph.unknown_gaps)==2
    _checked_projection(projection,str(UUID(artifact.artifact_id[9:])))
    private=private_storage_evidence(artifact)
    assert 'quoted_field' not in json.dumps(private) and '昨日' not in json.dumps(private,ensure_ascii=False)
    assert '断った' in artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']


@pytest.mark.parametrize('change',['missing','duplicate','extra','quote','partial','bool','owner_set','request','unknown_key','kind'])
def test_invalid_model_packet_is_rejected(change):
    snap=sample(); prepared=service.prepare_cumulative_model_fields(OWNER,snap); data=packet(prepared)
    if change=='missing': data['fields'].pop()
    if change=='duplicate': data['fields'][1]=copy.deepcopy(data['fields'][0])
    if change=='extra': data['fields'].append(copy.deepcopy(data['fields'][0]))
    if change=='quote': data['fields'][0]['quote']=data['fields'][0]['quote'].replace('はいない','はいる')
    if change=='partial': data['fields'][0].update(quote='後悔',start=5,end=7)
    if change=='bool': data['fields'][0]['start']=False
    if change=='owner_set': data['source_set_ref']='foreign'
    if change=='request': data['request_ref']='other'
    if change=='unknown_key': data['fields'][0]['cause']='疲れたから後悔'
    if change=='kind': data['fields'][0]['node_kind']='PERSONALITY'
    with pytest.raises(AnalysisSemanticError):
        service.build_cumulative_map(OWNER,snap,model_input=candidate(prepared,data))


@pytest.mark.parametrize('change',['guard','version','owner'])
def test_bound_candidate_rejects_changed_source(change):
    snap=sample(); prepared=service.prepare_cumulative_model_fields(OWNER,snap)
    if change=='guard': snap['guard']='analysis-db-cumulative-v1:'+'b'*64
    if change=='version': snap['members'][0]['original']['memo']+='今は違う。'
    owner=str(UUID(int=2)) if change=='owner' else OWNER
    with pytest.raises(AnalysisSemanticError):
        service.build_cumulative_map(owner,snap,model_input=candidate(prepared))


@pytest.mark.parametrize('text',['「私は仕事を続けたい」を撤回します。','「私は仕事を続けたい」を「今は続けたくない」に訂正します。','今日は休んだ。'])
def test_supplement_and_correction_explicitly_unsupported(text):
    prepared=service.prepare_cumulative_model_fields(OWNER,sample()); member=prepared.request.members[0]
    supplement=AnalysisSupplement('answer',OWNER,member.saved_record_ref,member.saved_record_version,text,commitment(text))
    request=replace(prepared.request,members=(replace(member,supplements=(supplement,)),))
    with pytest.raises(AnalysisSemanticUnsupported,match='scope_unsupported'):
        prepare_analysis_model_fields(request,source_guard=prepared.source_guard)


def test_comparison_and_safety_not_bypassed():
    prepared=service.prepare_cumulative_model_fields(OWNER,sample())
    with pytest.raises(AnalysisSemanticUnsupported):
        prepare_analysis_model_fields(replace(prepared.request,comparison_previous_request=prepared.request),source_guard=prepared.source_guard)
    snap=sample(); snap['members'][1]['original']['memo']='死にたい。'
    with pytest.raises(AnalysisSourceError,match='analysis_separate_safety_required'):
        service.prepare_cumulative_model_fields(OWNER,snap)


def test_all_unresolved_is_unavailable_without_fallback():
    snap=sample(); prepared=service.prepare_cumulative_model_fields(OWNER,snap)
    artifact, counts=service.build_cumulative_map(OWNER,snap,model_input=candidate(prepared,packet(prepared,['UNRESOLVED']*3)))
    assert artifact is None and counts['mapped_count']==0 and counts['unparsed_count']==2


def test_one_wholly_unresolved_record_does_not_make_invalid_saved_gaps():
    snap=sample(); prepared=service.prepare_cumulative_model_fields(OWNER,snap)
    artifact, counts=service.build_cumulative_map(OWNER,snap,model_input=candidate(prepared,
        packet(prepared,['UNRESOLVED','ACTION_OR_NONACTION','UNRESOLVED'])))
    projection=artifact.safe_projection(authenticated_owner_scope=OWNER)
    _checked_projection(projection,str(UUID(artifact.artifact_id[9:])))
    assert counts['mapped_count']==1 and counts['unparsed_count']==2
    assert all(g.between_node_refs for g in artifact.graph.unknown_gaps)


@pytest.mark.parametrize('finish',[None,'length','timeout','error','unknown'])
def test_incomplete_generation_is_rejected_even_with_valid_json(finish):
    snap=sample(); prepared=service.prepare_cumulative_model_fields(OWNER,snap)
    with pytest.raises(AnalysisSemanticError,match='generation_incomplete'):
        service.build_cumulative_map(OWNER,snap,model_input=replace(candidate(prepared),finish_reason=finish))


@pytest.mark.parametrize('change',['owner','set','version','text','kind','evidence','polarity'])
def test_quote_projection_rechecks_artifact_binding(change):
    snap=sample(); prepared=service.prepare_cumulative_model_fields(OWNER,snap)
    artifact,_=service.build_cumulative_map(OWNER,snap,model_input=candidate(prepared))
    node=artifact.graph.nodes[0]; q=node.quoted_field
    if change=='owner': artifact=replace(artifact,owner_scope='other')
    if change=='set': artifact=replace(artifact,source_set_ref='other')
    if change=='version': q=replace(q,record_version='other')
    if change=='text': node=replace(node,visible_label='誘いを断らなかった。')
    if change=='kind': node=replace(node,node_kind='ROLE')
    if change=='evidence': q=replace(q,evidence=replace(q.evidence,scalar_start=1))
    if change=='polarity': node=replace(node,polarity='positive')
    artifact=replace(artifact,graph=replace(artifact.graph,nodes=(replace(node,quoted_field=q),)+artifact.graph.nodes[1:]))
    with pytest.raises(AnalysisSourceError):
        artifact.safe_projection(authenticated_owner_scope=artifact.owner_scope)


def test_real_sql_commit_read_same_text_graph_and_identity(monkeypatch):
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
        prepared=service.prepare_cumulative_model_fields(OWNER,snap)
        artifact,coverage=service.build_cumulative_map(OWNER,snap,model_input=candidate(prepared))
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
        assert '分類候補' in text
        db.query('delete from public.emotions where id=$1',[snap['members'][0]['original']['id']])
        assert run(service.read_maps(OWNER,history=True))['items']==[]
    finally:
        db.proc.stdin.close();db.proc.wait(timeout=10)
