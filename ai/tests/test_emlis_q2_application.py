"""Synthetic end-to-end application tests against the actual migration/RPC SQL.

Run with Q2_PGLITE_MODULE=/path/to/@electric-sql/pglite (0.5.8).
This exercises PostgreSQL transactions, not a dictionary replacement for storage.
"""
import asyncio
import copy
import json
import os
from pathlib import Path
import subprocess
import threading
from uuid import uuid4

import httpx
import pytest
from emlis_thread_service import EmlisThreadService
from emlis_thread_store import EmlisThreadStore, ThreadStoreError
import emlis_thread_store

ORIGINAL = '褒められたのに、嬉しくなかった。'
ANSWER = '次も同じ成果を求められるようで、重かった。'
CORRECTION = '相手が嫌なのではなく、自分ではまだ納得していなかった。'

class Database:
    def __init__(self):
        self.lock = threading.Lock()
        self.proc = subprocess.Popen(['node', str(Path(__file__).parent / 'helpers/emlis_q2_postgres.cjs')],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        assert json.loads(self.proc.stdout.readline()) == {'ready': True}

    def query(self, sql, params=(), role=None):
        with self.lock:
            self.proc.stdin.write(json.dumps(dict(sql=sql, params=params, role=role)) + '\n')
            self.proc.stdin.flush()
            return json.loads(self.proc.stdout.readline())

    async def rpc(self, name, payload, **kwargs):
        assert name in {'emlis_thread_read', 'emlis_thread_commit'}
        args = ','.join(f'{k} => ${i}' for i, k in enumerate(payload, 1))
        params = [json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v for v in payload.values()]
        result = await asyncio.to_thread(self.query, f'select public.{name}({args}) as value', params, 'service_role')
        return httpx.Response(400 if 'code' in result else 200, headers={'content-type':'application/json'},
            content=json.dumps(result if 'code' in result else result['rows'][0]['value'], ensure_ascii=False))

@pytest.fixture(scope='module')
def db():
    if not os.environ.get('Q2_PGLITE_MODULE'):
        pytest.skip('Q2 PostgreSQL WASM test dependency is not configured')
    value = Database()
    yield value
    value.proc.stdin.close()
    value.proc.wait(timeout=10)

@pytest.fixture
def case(db, monkeypatch):
    user, input_id = str(uuid4()), str(uuid4())
    assert 'code' not in db.query('insert into auth.users values ($1)', [user])
    db.query("insert into public.profiles values ($1,'free')", [user])
    db.query("insert into public.emotions values ($1,$2,now() at time zone 'UTC',$3,'',array['仕事'],array['不安'],$4)",
        [input_id, user, ORIGINAL, json.dumps([dict(type='不安', strength='medium')], ensure_ascii=False)])
    monkeypatch.setattr(emlis_thread_store, 'sb_post_rpc', db.rpc)
    return user, input_id, EmlisThreadService()

def run(awaitable):
    return asyncio.run(awaitable)

def answer(service, user, dto, text=ANSWER, key='answer-1'):
    return service.answer(user, dto['thread_id'], question_id=dto['pending_question']['question_id'],
        expected_revision=dto['revision'], idempotency_key=key, answer_text=text,
        authored_at='2026-09-11T00:00:00+00:00')

def test_persisted_round_and_restart_get_do_not_generate(case):
    user, parent, service = case
    initial = run(service.start(user, parent))
    assert initial['state'] == 'AWAITING_ANSWER', initial
    completed = run(answer(service, user, initial))
    assert completed['body_state'] == 'REFINED', completed
    assert completed['answer_saved'] and completed['meaning_updated']
    assert ANSWER.rstrip('。') in completed['current_observation']['text']
    assert completed['issued_count'] == 1 and completed['pending_question'] is None
    assert [e['kind'] for e in completed['timeline']] == ['OBSERVATION','QUESTION','ANSWER','OBSERVATION']
    class NoAuthor:
        def __getattr__(self, name):
            raise AssertionError('GET or replay attempted generation')
    restarted = EmlisThreadService(engine=NoAuthor())
    assert run(restarted.get(user, parent)) == completed
    replay = run(answer(restarted, user, initial))
    assert replay['attempt_id'] == completed['attempt_id']
    assert len(replay['timeline']) == 4
    public = json.dumps(completed)
    assert all(x not in public for x in ('source_prefix_ref','meaning_graph','artifact','checkpoint_id','raw_utf8'))

@pytest.mark.parametrize('text,body_state', [
    ('わからない。', 'UNCHANGED'), ('はい。', 'ANSWER_UNREFLECTED'),
    ('その時は寂しかった。どう表したらいいかはまだ分からない。', 'PARTIALLY_REFINED'),
    ('今は嬉しい。', 'REFINED'), ('「嬉しくなかった」ではなく「嬉しかった」です。', 'REFINED'),
])
def test_answer_dispositions_remain_distinct(case, monkeypatch, text, body_state):
    user, parent, service = case
    initial = run(service.start(user, parent))
    if body_state in {'UNCHANGED', 'ANSWER_UNREFLECTED'}:
        monkeypatch.setattr(service.engine, 'generate', lambda *_: pytest.fail('must not generate'))
    result = run(answer(service, user, initial, text))
    assert result['body_state'] == body_state, result
    assert result['answer_saved']
    if body_state == 'UNCHANGED':
        assert result['current_observation'] == initial['current_observation']
        assert not result['meaning_updated']
    if body_state == 'ANSWER_UNREFLECTED':
        assert result['current_observation'] is None
        assert not any(e.get('is_current') for e in result['timeline'])
    if text == '今は嬉しい。':
        assert '回答した時点' in result['current_observation']['text']

def test_correction_survives_body_failure_and_get(case, monkeypatch):
    user, parent, service = case
    initial = run(service.start(user, parent))
    def fail(*args):
        raise ValueError('must never enter response or diagnostics')
    monkeypatch.setattr('cocolon_meaning_experience_engine.emlis_thread_engine.realize_emlis_thread_body', fail)
    result = run(answer(service, user, initial, '「嬉しくなかった」は誤りです。'))
    assert result['body_state'] == 'MEANING_UPDATED_BODY_UNAVAILABLE'
    assert result['meaning_updated'] and result['answer_saved']
    assert result['current_observation'] is None and not result['can_retry']
    assert not any(e.get('is_current') for e in result['timeline'])
    assert run(EmlisThreadService().get(user, parent)) == result
    snapshot = run(service.store.read(user, input_id=parent))
    cp = next(e for e in snapshot['events'] if e['id'] == snapshot['thread']['current_meaning_event_id'])
    assert cp['payload']['inactive_claim_refs']
    assert 'must never' not in json.dumps(snapshot)

def test_transient_body_save_failure_retries_same_operation_and_checkpoint(case, db, monkeypatch):
    user, parent, service = case
    initial = run(service.start(user, parent))
    failed = False
    async def fail_body_once(name, payload, **kwargs):
        nonlocal failed
        if not failed and payload.get('p_next', {}).get('latest_answer_event_id') and any(e['kind']=='OBSERVATION' for e in payload.get('p_events', [])):
            failed = True
            return httpx.Response(503, json={'code':'57P03'})
        return await db.rpc(name, payload, **kwargs)
    monkeypatch.setattr(emlis_thread_store, 'sb_post_rpc', fail_body_once)
    result = run(answer(service, user, initial))
    assert result['can_retry'] and result['meaning_updated'] and result['current_observation'] is None
    before = run(service.store.read(user, input_id=parent))
    monkeypatch.setattr(service.engine, 'prepare_emlis_update', lambda *_: pytest.fail('checkpoint must be reused'))
    retried = run(service.action(user, result['thread_id'], action='retry_response', expected_revision=result['revision'],
        idempotency_key='retry-1', operation_id=result['operation_id']))
    assert retried['body_state'] == 'REFINED' and retried['operation_id'] == result['operation_id']
    assert retried['attempt_id'] != result['attempt_id']
    after = run(service.store.read(user, input_id=parent))
    assert after['thread']['current_meaning_event_id'] == before['thread']['current_meaning_event_id']
    assert len([e for e in after['events'] if e['kind']=='ANSWER']) == 1
    assert len([e for e in after['events'] if e['kind']=='MEANING_UPDATE']) == 2
    assert after['thread']['issued_count'] == 1

@pytest.mark.parametrize('lost_stage', ['ANSWER','MEANING_UPDATE','OBSERVATION'])
def test_lost_commit_ack_reconciles_without_duplicate_work(case, db, monkeypatch, lost_stage):
    user, parent, service = case
    initial = run(service.start(user, parent))
    fired = False
    async def lose_ack(name, payload, **kwargs):
        nonlocal fired
        result = await db.rpc(name, payload, **kwargs)
        if not fired and any(e['kind']==lost_stage for e in payload.get('p_events', [])):
            fired = True
            raise httpx.ReadTimeout('source must never be exposed')
        return result
    monkeypatch.setattr(emlis_thread_store, 'sb_post_rpc', lose_ack)
    with pytest.raises(ThreadStoreError, match='save_result_unknown'):
        run(answer(service, user, initial))
    fresh = run(EmlisThreadService().get(user, parent))
    assert fresh['answer_saved'] and not fresh['can_retry']
    replay = run(answer(service, user, initial))
    assert replay['attempt_id'] == fresh['attempt_id']
    assert len([e for e in replay['timeline'] if e['kind']=='ANSWER']) == 1
    if lost_stage == 'OBSERVATION':
        assert fresh['body_state'] == 'REFINED' and fresh['current_observation']

@pytest.mark.parametrize('same_key', [True,False])
def test_simultaneous_submits_have_one_answer(case, same_key):
    user, parent, service = case
    initial = run(service.start(user, parent))
    async def compete():
        return await asyncio.gather(answer(service,user,initial,key='first'),
            answer(EmlisThreadService(),user,initial,key='first' if same_key else 'second'),return_exceptions=True)
    results = run(compete())
    successes = [r for r in results if isinstance(r,dict)]
    assert len(successes) == (2 if same_key else 1), results
    if same_key:
        assert len({r['attempt_id'] for r in successes}) == 1
    else:
        assert next(r for r in results if isinstance(r,Exception)).status == 409
    snapshot = run(service.store.read(user,input_id=parent))
    assert len([e for e in snapshot['events'] if e['kind']=='ANSWER']) == 1

def test_invalid_answers_keys_and_actions_do_not_consume_question(case):
    user, parent, service = case
    initial = run(service.start(user,parent))
    for text in ('', '   ', 'あ'*2001):
        with pytest.raises(ThreadStoreError): run(answer(service,user,initial,text))
    for action_name in ('continue','retry_response'):
        with pytest.raises(ThreadStoreError):
            run(service.action(user,initial['thread_id'],action=action_name,expected_revision=initial['revision'],idempotency_key='bad'))
    assert run(service.get(user,parent)) == initial
    result = run(answer(service,user,initial))
    with pytest.raises(ThreadStoreError,match='idempotency_conflict'):
        run(answer(service,user,initial,'different'))
    with pytest.raises(ThreadStoreError):
        run(answer(service,user,initial,key='different'))
    assert run(service.get(user,parent)) == result

def test_skip_is_explicit_and_close_get_is_read_only(case):
    user,parent,service=case
    initial=run(service.start(user,parent))
    for _ in range(3): assert run(service.get(user,parent)) == initial
    args=dict(action='skip',expected_revision=initial['revision'],idempotency_key='skip',question_id=initial['pending_question']['question_id'])
    skipped=run(service.action(user,initial['thread_id'],**args))
    assert skipped['state']=='COMPLETED' and not skipped['answer_saved']
    assert skipped['current_observation']==initial['current_observation']
    assert run(service.action(user,initial['thread_id'],**args))['revision']==skipped['revision']
    with pytest.raises(ThreadStoreError): run(answer(service,user,initial))

@pytest.mark.parametrize('role', ['anon','authenticated'])
def test_clients_cannot_read_private_tables_or_call_rpc(case, db, role):
    user,parent,service=case
    run(service.start(user,parent))
    for table in ('emlis_input_threads','emlis_thread_events'):
        assert db.query(f'select * from public.{table}',role=role)['code']=='42501'
    assert db.query('select public.emlis_thread_read($1,$2,null)',[user,parent],role)['code']=='42501'

@pytest.mark.parametrize('change', ['foreign_owner','source','retention','parent_delete','account_delete','tier'])
def test_owner_parent_access_and_cascade(case, db, change):
    user,parent,service=case
    initial=run(service.start(user,parent))
    before=run(service.store.read(user,input_id=parent))
    if change=='foreign_owner':
        with pytest.raises(ThreadStoreError) as exc: run(service.get(str(uuid4()),parent))
        assert exc.value.status==404
        return
    if change=='source': db.query("update public.emotions set memo='changed' where id=$1",[parent])
    elif change=='retention': db.query("update public.emotions set created_at='2020-01-01' where id=$1",[parent])
    elif change=='tier': db.query("update public.profiles set subscription_tier='premium' where id=$1",[user])
    elif change=='parent_delete': db.query('delete from public.emotions where id=$1',[parent])
    elif change=='account_delete': db.query('delete from auth.users where id=$1',[user])
    with pytest.raises(ThreadStoreError): run(service.store.commit(user,before,before['thread'],[]))
    if change in {'parent_delete','account_delete'}:
        assert db.query('select count(*) as n from public.emlis_thread_events where thread_id=$1',[initial['thread_id']])['rows'][0]['n']==0
        with pytest.raises(ThreadStoreError): run(service.start(user,parent))
    elif change!='tier':
        with pytest.raises(ThreadStoreError): run(service.get(user,parent))

def test_expired_attempt_is_unknown_and_cannot_commit_or_retry(case, db):
    user,parent,service=case
    initial=run(service.start(user,parent))
    class StopWorker(BaseException): pass
    service.engine.prepare_emlis_update=lambda *_: (_ for _ in ()).throw(StopWorker())
    with pytest.raises(StopWorker): run(answer(service,user,initial))
    snapshot=run(service.store.read(user,input_id=parent))
    db.query("update public.emlis_input_threads set processing_deadline_at=now()-interval '1 second' where id=$1",[initial['thread_id']])
    expired=run(service.get(user,parent))
    assert expired['state']=='RESPONSE_FAILED' and expired['failure_code']=='save_result_unknown' and not expired['can_retry']
    with pytest.raises(ThreadStoreError):
        run(service.store.commit(user,snapshot,snapshot['thread'],[],finishing_attempt=snapshot['thread']['active_attempt_id']))

def test_verified_api_contract_default_off_and_round(case, monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from api_emlis_thread import register_emlis_thread_routes
    import api_account_visibility
    user,parent,service=case
    initial=run(service.start(user,parent))
    async def resolve(token):
        if token != 'synthetic-owner-token':
            from fastapi import HTTPException
            raise HTTPException(401,'Invalid bearer token')
        return user
    monkeypatch.setattr(api_account_visibility,'_resolve_user_id_from_token',resolve)
    app=FastAPI()
    register_emlis_thread_routes(app,service=service)
    with TestClient(app) as client:
        url=f'/emlis/threads/by-input/{parent}'
        assert client.get(url).status_code==404
        monkeypatch.setenv('COCOLON_EMLIS_THREAD_DEVELOPMENT','true')
        monkeypatch.setenv('COCOLON_ENV','development')
        assert client.get(url).status_code==401
        assert client.get(url,headers={'Authorization':'Bearer forged'}).status_code==401
        headers={'Authorization':'Bearer synthetic-owner-token'}
        got=client.get(url,headers=headers)
        assert got.status_code==200 and got.json()==initial
        assert got.headers['cache-control']=='private, no-store'
        post=f"/emlis/threads/{initial['thread_id']}/answers"
        body=dict(question_id=initial['pending_question']['question_id'],expected_revision=initial['revision'],
                  idempotency_key='api-answer',answer_text=ANSWER,authored_at='2026-09-11T00:00:00+00:00')
        for extra in ({'user_id':user},{'plan':'premium'},{'source_prefix_ref':'forged'},{'answer_text':' '}):
            assert client.post(post,json={**body,**extra},headers=headers).status_code==422
        result=client.post(post,json=body,headers=headers)
        assert result.status_code==200 and result.json()['body_state']=='REFINED'
        assert client.post(post,json=body,headers=headers).json()['attempt_id']==result.json()['attempt_id']
        assert client.get(url,headers=headers).json()==result.json()
        monkeypatch.setenv('COCOLON_ENV','production')
        assert client.get(url,headers=headers).status_code==404

def test_confirmed_worker_cancellation_allows_explicit_retry(case, monkeypatch):
    user,parent,service=case
    initial=run(service.start(user,parent))
    def interrupt(*_): raise asyncio.CancelledError()
    original=service.engine.generate
    monkeypatch.setattr(service.engine,'generate',interrupt)
    with pytest.raises(asyncio.CancelledError): run(answer(service,user,initial))
    failed=run(service.get(user,parent))
    assert failed['failure_code']=='worker_interrupted' and failed['can_retry'] and failed['meaning_updated']
    monkeypatch.setattr(service.engine,'generate',original)
    recovered=run(service.action(user,failed['thread_id'],action='retry_response',expected_revision=failed['revision'],
        idempotency_key='retry-worker',operation_id=failed['operation_id']))
    assert recovered['body_state']=='REFINED' and recovered['operation_id']==failed['operation_id']

@pytest.mark.parametrize('tier', ['free','plus','premium'])
def test_q2_all_tiers_use_one_round_current_input_only(case,db,tier):
    user,parent,service=case
    db.query('update public.profiles set subscription_tier=$2 where id=$1',[user,tier])
    initial=run(service.start(user,parent))
    final=run(answer(service,user,initial))
    assert final['issued_count']==1 and final['question_limit']==1 and not final['can_continue']
    from emlis_thread_service import _request
    req=_request(run(service.store.read(user,input_id=parent)))
    assert not req.emlis_thread.admitted_history and req.emlis_thread.capability_snapshot=='FREE_Q1'

@pytest.mark.parametrize('text', ['死にたい。','自殺したい。'])
def test_safety_answer_does_not_become_normal_observation(case,text):
    user,parent,service=case
    initial=run(service.start(user,parent))
    result=run(answer(service,user,initial,text))
    assert result['failure_code']=='separate_safety_owner_required'
    assert result['answer_saved'] and not result['can_retry'] and result['current_observation'] is None

def test_saved_input_development_entry_uses_thread_and_keeps_old_wire(case,monkeypatch):
    from emlis_ai_reply_service import render_emlis_ai_reply
    from emlis_ai_current_input_bundle import normalize_emlis_current_input
    user,parent,service=case
    monkeypatch.setenv('COCOLON_ENV','development')
    monkeypatch.setenv('COCOLON_EMLIS_THREAD_DEVELOPMENT','true')
    monkeypatch.setattr('emlis_ai_reply_service._step10_dormant_v3_public_hook',lambda **_: pytest.fail('second author'))
    # Keep this Q2 wire-compatibility check on the old saved profile; Q3 has
    # an actual migrated-entry test in test_emlis_q3_application.
    def selected_owner(*,runtime_profile):
        assert runtime_profile == 'q3.plan.sequential.v1'
        return service
    monkeypatch.setattr('emlis_thread_service.EmlisThreadService',selected_owner)
    normalized=normalize_emlis_current_input({'id':parent,'created_at':'2026-09-10T00:00:00Z','memo':ORIGINAL})
    reply=run(render_emlis_ai_reply(user_id=user,subscription_tier='free',current_input=normalized))
    assert reply.comment_text=='' and reply.meta['observation_status']=='unavailable'
    assert run(service.get(user,parent))['state']=='AWAITING_ANSWER'
