"""Offline saved refined admission with synthetic committed control records.

The real source-prefix/answer-envelope readers validate the fixture. These
tests do not assert Emlis meaning inference, live auth/DB or preview support.
"""
import asyncio
import copy
from dataclasses import asdict, replace
import json

from fastapi import HTTPException
import pytest

import api_account_visibility
from emlis_thread_service import _request, RUNTIME_PROFILE, Q3_PROFILE
from cocolon_meaning_experience_engine.emlis_thread_contracts import (
    EmlisClarificationV1, EmlisQuestionDecisionV1, SupplementalAnswerSource, SEMANTIC_SCHEMA,
)
from cocolon_meaning_experience_engine.emlis_thread_source import admit_emlis_thread
from cocolon_meaning_experience_engine.source_kernel import freeze_text_source
from piece_v2_contract import PieceContractError, canonical_json_bytes
from piece_v2_source_adapter import PieceSavedSourceAdapter, project_saved_refined_source

OWNER = '40000000-0000-4000-8000-000000000001'
INPUT = '50000000-0000-4000-8000-000000000001'
THREAD = '60000000-0000-4000-8000-000000000001'
OP = '70000000-0000-4000-8000-000000000001'
ATTEMPT = '80000000-0000-4000-8000-000000000001'
ANSWER = '90000000-0000-4000-8000-000000000002'
AUTH = 'Bearer refined-synthetic-session'
STAMP = '2026-11-09T00:30:00+00:00'
ORIGINAL_TEXT = '私は同僚に資料の確認を頼んだ。'
ANSWER_TEXT = '私は司書に展示の設営を相談した。'


def event(n, kind, payload, *, eid=None):
    return dict(id=eid or f'90000000-0000-4000-8000-{n:012d}', thread_id=THREAD, seq=n,
        kind=kind, round_index=1, question_id='synthetic-question' if kind in {'QUESTION','ANSWER'} else None,
        operation_id=OP, attempt_id=ATTEMPT, recorded_at=STAMP, payload=payload)


def snapshot(profile=RUNTIME_PROFILE, tier='free'):
    original = dict(id=INPUT, created_at='2026-11-09T00:00:00', memo=None,
        memo_action=ORIGINAL_TEXT, category=['仕事'], emotions=['自己理解'],
        emotion_details=[dict(type='自己理解', strength='medium')])
    thread = dict(id=THREAD, user_id=OWNER, original_emotion_id=INPUT, revision=8,
        state='COMPLETED', source_snapshot=copy.deepcopy(original), issued_count=0,
        latest_answer_event_id=ANSWER, current_meaning_event_id=None, last_observation_event_id=None,
        active_operation_id=None, active_attempt_id=None, processing_deadline_at=None,
        data=dict(runtime_profile=profile, body_state='REFINED', answer_assessment='RESOLVED',
            meaning_updated=True, failure_code=None, operation_id=OP, attempt_id=ATTEMPT,
            context_guards=[], context_feedback=[], evaluated_tier=tier))
    result = dict(original=original, thread=thread, events=[], tier=tier,
        now='2026-11-09T01:00:00+00:00', context=dict(history=[],feedback=[]))
    original_ref = freeze_text_source(_request(result)).envelope.envelope_id
    thread['data']['original_source_ref'] = original_ref
    question = EmlisClarificationV1('synthetic-question', 'synthetic-request', THREAD, original_ref,
        EmlisQuestionDecisionV1('ASK', target_ref='synthetic-target'), 'PRIVATE QUESTION BODY')
    answer = SupplementalAnswerSource(ANSWER, THREAD, question.question_id, 1, original_ref,
        ANSWER_TEXT, STAMP)
    result['events'] = [event(1,'QUESTION',asdict(question)),event(2,'ANSWER',{'source':asdict(answer)},eid=ANSWER)]
    thread['issued_count'] = 1
    request = _request(result)
    admitted = admit_emlis_thread(request)
    initial_prefix = admit_emlis_thread(replace(request,
        emlis_thread=replace(request.emlis_thread,answers=(),current_round=0))).source_prefix_ref
    thread['source_prefix_ref'] = thread['evaluated_prefix_ref'] = admitted.source_prefix_ref
    cp = dict(semantic_schema_version=SEMANTIC_SCHEMA, checkpoint_id='synthetic-checkpoint',
        source_prefix_ref=admitted.source_prefix_ref, assessment_status='RESOLVED', unresolved_parts=[],
        answer_update=dict(disposition='MATERIAL_UPDATE', answer_source_ref=admitted.answers[0].envelope.envelope_id,
            question_ref=question.question_id, unresolved_parts=[],
            updates=[dict(operation='ADD',superseded_claim_refs=[],affected_dependency_refs=[])]))
    result['events'] += [event(3,'MEANING_UPDATE',cp),event(4,'OBSERVATION',dict(stage='REFINED',
        source_prefix_ref=admitted.source_prefix_ref,meaning_checkpoint_ref=cp['checkpoint_id'],
        text='PRIVATE EMLIS BODY',artifact={'private':'PRIVATE INFERENCE'})),
        event(5,'OPERATION',dict(status='COMPLETED',failure_code=None))]
    thread['current_meaning_event_id'] = result['events'][2]['id']
    thread['last_observation_event_id'] = result['events'][3]['id']
    initial_cp=event(10,'MEANING_UPDATE',dict(semantic_schema_version=SEMANTIC_SCHEMA,
        checkpoint_id='synthetic-initial',source_prefix_ref=initial_prefix,answer_update=None))
    initial_obs=event(11,'OBSERVATION',dict(stage='INITIAL',source_prefix_ref=initial_prefix,
        meaning_checkpoint_ref='synthetic-initial',text='PRIVATE INITIAL BODY'))
    initial_cp['round_index']=initial_obs['round_index']=0
    q,a,cp,obs,finish=result['events']
    result['events']=[initial_cp,initial_obs,q,event(12,'OPERATION',dict(status='AWAITING_ANSWER',failure_code=None)),a,cp,obs,finish]
    for seq,row in enumerate(result['events'],1): row['seq']=seq
    return result


class Store:
    def __init__(self,value): self.value=value; self.calls=[]
    async def read(self,owner,*,input_id=None):
        self.calls.append((owner,input_id)); return copy.deepcopy(self.value)
    async def context(self,*args): return dict(history=[],feedback=[])
    async def commit(self,*args,**kwargs): pytest.fail('read-only handoff attempted write')


@pytest.fixture(autouse=True)
def auth(monkeypatch):
    async def verify(token):
        if token!='refined-synthetic-session': raise HTTPException(401,'private token diagnostic')
        return OWNER
    monkeypatch.setattr(api_account_visibility,'_resolve_user_id_from_token',verify)


def resolve(value,*,opted_in=True,answer_id=ANSWER):
    return asyncio.run(PieceSavedSourceAdapter(store=Store(value)).resolve_refined_handoff(
        AUTH,INPUT,supplemental_answer_identity=answer_id,opted_in=opted_in))


@pytest.mark.parametrize('profile,tier',[(RUNTIME_PROFILE,'free'),(Q3_PROFILE,'free'),(Q3_PROFILE,'plus'),(Q3_PROFILE,'premium')])
def test_committed_additive_answer_retains_separate_sources_and_explicit_opt_in(profile,tier):
    value=snapshot(profile,tier); before=copy.deepcopy(value)
    saved=resolve(value); line=saved.lineage_payload()
    assert value==before
    assert saved.original.original_payload()==value['original']
    assert saved.supplemental.answer_text_private==ANSWER_TEXT
    assert line['semantic_source_roles']==['original_input','supplemental_answer']
    assert line['observation']['question_need_decision_identity']==value['events'][2]['id']
    assert line['observation']['supplemental_answer_identity']==ANSWER
    assert 'PRIVATE' not in json.dumps(line) and ANSWER_TEXT not in repr(saved)
    projected=project_saved_refined_source(saved,opted_in=True)
    assert projected.original.original_text==ORIGINAL_TEXT
    assert projected.original.saved_original_json==canonical_json_bytes(value['original'])
    assert projected.supplemental==saved.supplemental and projected.supplemental_owner_id==OWNER
    assert projected.supplemental_update_operation=='ADD'
    assert projected.original_commitment!=projected.supplemental_commitment
    with pytest.raises(PieceContractError): project_saved_refined_source(saved,opted_in=False)
    with pytest.raises(TypeError): project_saved_refined_source(saved)
    with pytest.raises(TypeError): PieceSavedSourceAdapter().resolve_refined_handoff(AUTH,INPUT,supplemental_answer_identity=ANSWER)


@pytest.mark.parametrize('change',[
    'opt_out','wrong_answer','no_thread','other_owner','stale_original','active','refining',
    'unreflected','partial','unresolved','unupdated','natural','semantic','latest_answer',
    'prefix','evaluated_prefix','answer_text','answer_parent','answer_question','answer_version',
    'missing_question','duplicate_answer','duplicate_id','unsorted','other_event_thread',
    'checkpoint_prefix','checkpoint_schema','checkpoint_answer','checkpoint_question',
    'checkpoint_unresolved','update_unresolved','update_replace','update_withdraw','update_affected',
    'observation_stage','observation_checkpoint','observation_prefix','observation_attempt',
    'missing_finish','failed_finish','future_answer','future_observation','missing_optin',
    'missing_initial','initial_prefix','initial_checkpoint','initial_finish','initial_attempt','question_schema',
])
def test_unfinished_changed_or_nonadditive_saved_state_is_not_refined_material(change):
    value=snapshot(); t=value['thread']; d=t['data']; rows=value['events']
    e=[rows[n] for n in (2,4,5,6,7)]; cp=e[2]['payload']; update=cp['answer_update']
    if change=='opt_out':
        with pytest.raises(PieceContractError): resolve(value,opted_in=False)
        return
    if change=='wrong_answer':
        with pytest.raises(PieceContractError): resolve(value,answer_id=INPUT)
        return
    if change=='missing_optin':
        with pytest.raises(TypeError): PieceSavedSourceAdapter(store=Store(value)).resolve_refined_handoff(AUTH,INPUT,supplemental_answer_identity=ANSWER)
        return
    if change=='no_thread': value['thread']=None
    elif change=='other_owner': t['user_id']=INPUT
    elif change=='stale_original': value['original']['memo_action']+=' '
    elif change=='active': t['active_attempt_id']=ATTEMPT
    elif change=='refining': t['state']='REFINING'
    elif change=='unreflected': d['body_state']='ANSWER_UNREFLECTED'
    elif change=='partial': d['body_state']='PARTIALLY_REFINED'
    elif change=='unresolved': d['answer_assessment']='UNRESOLVED'
    elif change=='unupdated': d['meaning_updated']=False
    elif change=='natural': d['response_profile']='natural_reply.v1'
    elif change=='semantic': d['semantic_profile']='other'
    elif change=='latest_answer': t['latest_answer_event_id']=INPUT
    elif change=='prefix': t['source_prefix_ref']='stale'
    elif change=='evaluated_prefix': t['evaluated_prefix_ref']='stale'
    elif change=='answer_text': e[1]['payload']['source']['answer_text_private']+=' '
    elif change=='answer_parent': e[1]['payload']['source']['original_source_ref']='other'
    elif change=='answer_question': e[1]['payload']['source']['question_id']='other'
    elif change=='answer_version': e[1]['payload']['source']['source_version']='other'
    elif change=='missing_question': rows.remove(e[0])
    elif change=='duplicate_answer': rows.append(event(20,'ANSWER',copy.deepcopy(e[1]['payload'])))
    elif change=='duplicate_id': e[2]['id']=e[0]['id']
    elif change=='unsorted': rows.reverse()
    elif change=='other_event_thread': e[2]['thread_id']=INPUT
    elif change=='checkpoint_prefix': cp['source_prefix_ref']='other'
    elif change=='checkpoint_schema': cp['semantic_schema_version']='other'
    elif change=='checkpoint_answer': update['answer_source_ref']='other'
    elif change=='checkpoint_question': update['question_ref']='other'
    elif change=='checkpoint_unresolved': cp['unresolved_parts']=[{'reason':'unresolved'}]
    elif change=='update_unresolved': update['unresolved_parts']=[{'reason':'unresolved'}]
    elif change=='update_replace': update['updates'][0]['operation']='REPLACE'
    elif change=='update_withdraw': update['updates'][0]['superseded_claim_refs']=['old']
    elif change=='update_affected': update['updates'][0]['affected_dependency_refs']=['old']
    elif change=='observation_stage': e[3]['payload']['stage']='INITIAL'
    elif change=='observation_checkpoint': e[3]['payload']['meaning_checkpoint_ref']='other'
    elif change=='observation_prefix': e[3]['payload']['source_prefix_ref']='other'
    elif change=='observation_attempt': e[3]['attempt_id']=INPUT
    elif change=='missing_finish': rows.remove(e[4])
    elif change=='failed_finish': e[4]['payload']['failure_code']='failed'
    elif change=='future_answer': e[1]['payload']['source']['recorded_at']='2026-11-10T00:30:00+00:00'
    elif change=='future_observation': e[3]['recorded_at']='2026-11-10T00:30:00+00:00'
    elif change=='missing_initial': rows.pop(1)
    elif change=='initial_prefix': rows[1]['payload']['source_prefix_ref']='other'
    elif change=='initial_checkpoint': rows[0]['payload']['answer_update']={'unexpected':'update'}
    elif change=='initial_finish': rows[3]['payload']['status']='COMPLETED'
    elif change=='initial_attempt': rows[1]['attempt_id']=INPUT
    elif change=='question_schema': e[0]['payload']['schema_version']='other'
    else: raise AssertionError(change)
    with pytest.raises(PieceContractError): resolve(value)


def test_original_live_handoff_stays_original_only_and_refined_revalidation_is_read_only():
    value=snapshot(); store=Store(value); adapter=PieceSavedSourceAdapter(store=store)
    saved=asyncio.run(adapter.resolve_refined_handoff(AUTH,INPUT,supplemental_answer_identity=ANSWER,opted_in=True))
    assert asyncio.run(adapter.revalidate_refined_handoff(AUTH,saved,opted_in=True))==saved
    with pytest.raises(PieceContractError): asyncio.run(adapter.resolve_original_handoff(AUTH,INPUT))
    store.value['thread']['revision']+=1
    with pytest.raises(PieceContractError) as exc: asyncio.run(adapter.revalidate_refined_handoff(AUTH,saved,opted_in=True))
    assert exc.value.code=='PIECE_CONFLICT'


def test_projection_cannot_replace_or_alias_separate_answer_commitment():
    saved=resolve(snapshot()); line=saved.lineage_payload()
    line['observation']['supplemental_answer_bundle_commitment']=saved.original.record_commitment
    corrupted=replace(saved,_lineage_json=canonical_json_bytes(line))
    with pytest.raises(PieceContractError): project_saved_refined_source(corrupted,opted_in=True)


@pytest.mark.parametrize('change',['stage','roles','owner','schema','body','extra','thread','noncanonical'])
def test_projection_rejects_inconsistent_or_noncanonical_private_lineage(change):
    saved=resolve(snapshot()); line=saved.lineage_payload()
    if change=='stage': line['observation']['emlis_observation_stage']='normal_observation'
    elif change=='roles': line['semantic_source_roles']=['original_input']
    elif change=='owner': line['source_input']['source_owner_user_id']=INPUT
    elif change=='schema': line['handoff_contract_version']='other'
    elif change=='body': line['body_free']=False
    elif change=='extra': line['private_body']='forbidden'
    elif change=='thread': saved=replace(saved,thread_id=INPUT)
    raw=json.dumps(line).encode() if change=='noncanonical' else canonical_json_bytes(line)
    with pytest.raises(PieceContractError): project_saved_refined_source(replace(saved,_lineage_json=raw),opted_in=True)


def test_actual_q2_sql_accepted_addition_can_be_read_without_authoring_or_writing(monkeypatch):
    """Real existing Emlis/SQL result, retrieval only; no Piece success claim."""
    import os
    from uuid import uuid4
    import emlis_thread_store
    from emlis_thread_service import EmlisThreadService
    from test_emlis_q2_application import Database, run, answer as answer_question
    assert os.environ.get('Q2_PGLITE_MODULE'), 'retained SQL runtime required'
    db=Database(); owner,parent=str(uuid4()),str(uuid4())
    try:
        async def verify(token):
            assert token=='refined-synthetic-session'
            return owner
        monkeypatch.setattr(api_account_visibility,'_resolve_user_id_from_token',verify)
        monkeypatch.setattr(emlis_thread_store,'sb_post_rpc',db.rpc)
        assert 'code' not in db.query('INSERT INTO auth.users VALUES ($1)',[owner])
        assert 'code' not in db.query("INSERT INTO public.profiles VALUES ($1,'free')",[owner])
        assert 'code' not in db.query("INSERT INTO public.emotions VALUES ($1,$2,now() at time zone 'UTC',$3,'',array['仕事'],array['不安'],$4::jsonb)",
            [parent,owner,'褒められたのに、嬉しくなかった。',json.dumps([dict(type='不安',strength='medium')],ensure_ascii=False)])
        service=EmlisThreadService(); started=run(service.start(owner,parent))
        completed=run(answer_question(service,owner,started,'その時は重かった。'))
        assert completed['body_state']=='REFINED' and completed['meaning_updated'] is True
        stored=run(service.store.read(owner,input_id=parent)); answer_id=stored['thread']['latest_answer_event_id']
        before=db.query('SELECT to_jsonb(t) AS row FROM public.emlis_input_threads t WHERE id=$1',[completed['thread_id']])
        events_before=db.query('SELECT to_jsonb(e) AS row FROM public.emlis_thread_events e WHERE thread_id=$1 ORDER BY seq',[completed['thread_id']])
        class ForbiddenEngine:
            def __getattr__(self,name): raise AssertionError('retrieval cannot author or infer')
        service.engine=ForbiddenEngine()
        adapter=PieceSavedSourceAdapter(store=service.store)
        handoff=run(adapter.resolve_refined_handoff(AUTH,parent,supplemental_answer_identity=answer_id,opted_in=True))
        assert handoff.original.original_payload()['memo']=='褒められたのに、嬉しくなかった。'
        assert handoff.supplemental.answer_text_private=='その時は重かった。'
        assert run(adapter.revalidate_refined_handoff(AUTH,handoff,opted_in=True))==handoff
        assert db.query('SELECT to_jsonb(t) AS row FROM public.emlis_input_threads t WHERE id=$1',[completed['thread_id']])==before
        assert db.query('SELECT to_jsonb(e) AS row FROM public.emlis_thread_events e WHERE thread_id=$1 ORDER BY seq',[completed['thread_id']])==events_before
    finally:
        db.proc.stdin.close(); db.proc.wait(timeout=10)
