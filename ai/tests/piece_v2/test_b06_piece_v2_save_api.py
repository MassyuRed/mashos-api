"""B6 ASGI/shared-client/native-SQL integration with synthetic auth/handoff.

The persisted preview and admission handoff are synthetic: this does not claim
production Auth/PostgREST, a safety-approved issuer, CMEE acceptance or a device.
Native cases apply the unchanged Q2 schema and the current unapplied M4 to a
fresh disposable database. No live credentials, source rows or skip fallback.
"""
from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from queue import Queue
import runpy
import sys
import time
from uuid import uuid4

import httpx
import pytest
from fastapi import FastAPI, HTTPException

_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_ROOT / 'ai/services/ai_inference'))
_B5 = runpy.run_path(str(Path(__file__).with_name('db') / 'test_b05_preview_persistence.py'))
_B4, _B2 = _B5['_B4'], _B5['_B2']
database = _B4['database']
from piece_v2_contract import PieceContractError, canonical_json_bytes, canonical_sha256_hex
from piece_v2_source_adapter import PieceSavedHandoff, PieceSavedOriginal
from piece_v2_visual import build_visual_recipe
import piece_v2_save_service as service
import piece_v2_store
import api_piece_v2 as api
import supabase_client as shared

OWNER, VIEWER = str(_B5['_OWNER']), str(_B5['_VIEWER'])
INPUT, THREAD, OBS = (str(uuid4()) for _ in range(3))
PRIVATE = 'SYNTHETIC_PRIVATE_SOURCE_OR_BACKEND_DIAGNOSTIC'


def _row(tier='free', fmt='short_essay', formats=None):
    row = _B2['_record'](fmt=fmt)
    row.update(id=str(row['id']), owner_user_id=OWNER, piece_contract_version='piece.record.v2',
        lifecycle_status='preview_draft', preview_revision=1, visibility_scope='private',
        expires_at=(datetime.now(timezone.utc)+timedelta(minutes=10)).isoformat(),
        preview_eligible_formats=formats or [fmt], source_input_id=INPUT)
    row['source_lineage']['source_input']['source_input_id'] = INPUT
    row['source_lineage']['observation']['emlis_observation_result_identity'] = OBS
    row['visual_recipe'] = build_visual_recipe(fmt, tier=tier)
    row['visual_recipe_hash'] = canonical_sha256_hex(row['visual_recipe'])
    return row


def _handoff(row, tier='free', original=None):
    original = original or {'id': INPUT, 'created_at': datetime.now(timezone.utc).replace(
        tzinfo=None).isoformat(), 'memo': PRIVATE, 'memo_action': None,
        'category': [], 'emotions': [], 'emotion_details': []}
    saved = PieceSavedOriginal(OWNER, INPUT, 'emlis.current_input_bundle.v1',
        row['source_lineage']['source_input']['source_input_bundle_commitment'],
        'sha256:' + canonical_sha256_hex(original), original['created_at'], tier,
        canonical_json_bytes(original), b'{}')
    return PieceSavedHandoff(saved, THREAD, 1, canonical_json_bytes(row['source_lineage']))


def _request(row):
    return {'preview_id': row['id'], 'expected_preview_revision': row['preview_revision'],
        **{k: row[k] for k in ('piece_text_hash', 'content_payload_hash', 'visual_recipe_hash')}}


def _result(row, replay=False):
    return {'piece_id': row['id'], 'consumption_id': str(uuid4()), 'lifecycle_status': 'saved',
        'visibility_scope': 'private', 'row_version': 2, 'saved_at': datetime.now(timezone.utc).isoformat(),
        'idempotency_replayed': replay}


@pytest.fixture
def harness(monkeypatch):
    row = _row()
    state = {'row': row, 'handoff': _handoff(row), 'reads': [], 'posts': [], 'auth': [],
        'source': [], 'handler': None, 'read_handler': None, 'source_error': None, 'source_hook': None}
    async def verify(auth):
        state['auth'].append(auth)
        if auth not in ('Bearer synthetic-owner', 'Bearer synthetic-viewer'):
            raise HTTPException(401, PRIVATE)
        return VIEWER if auth.endswith('viewer') else OWNER
    class Adapter:
        async def resolve_original_handoff(self, authorization, input_id):
            state['source'].append((authorization, input_id))
            if state['source_error']:
                raise state['source_error']
            if state['source_hook']:
                state['source_hook']()
            return state['handoff']
    monkeypatch.setattr(api, '_verify_bearer', verify)
    monkeypatch.setattr(service, 'PieceSavedSourceAdapter', Adapter)
    monkeypatch.setattr(shared, 'SUPABASE_URL', 'https://piece.invalid')
    monkeypatch.setattr(shared, 'SUPABASE_SERVICE_ROLE_KEY', 'synthetic-service-only')
    def upstream(request):
        assert request.headers['authorization'] == 'Bearer synthetic-service-only'
        if request.method == 'GET':
            assert request.url.path == '/rest/v1/piece_records'
            state['reads'].append(dict(request.url.params))
            if state['read_handler']:
                return state['read_handler'](request)
            rows = [] if state['row'] is None or request.url.params['owner_user_id'] != 'eq.'+OWNER else [state['row']]
            return httpx.Response(200, json=rows)
        assert request.method == 'POST' and request.url.path == '/rest/v1/rpc/piece_save_v2'
        args = json.loads(request.content)
        state['posts'].append(args)
        return state['handler'](args) if state['handler'] else httpx.Response(200, json=_result(state['row']))
    app = FastAPI(); app.include_router(api.router)
    from piece_v2_runtime_control import PIECE_FEATURE_NAMES
    app.state.piece_v2_runtime = {
        'requested': dict.fromkeys(PIECE_FEATURE_NAMES, True),
        'ready': dict.fromkeys(PIECE_FEATURE_NAMES, True)}
    state['app'] = app
    def call(body=None, headers=None, content=None, query=''):
        async def run():
            async with httpx.AsyncClient(transport=httpx.MockTransport(upstream)) as backend:
                async def client(): return backend
                monkeypatch.setattr(shared, 'get_async_client', client)
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='https://test.invalid') as http:
                    kwargs = {'headers': {'Authorization': 'Bearer synthetic-owner',
                        'Idempotency-Key': 'synthetic-save'} if headers is None else headers}
                    kwargs['content' if content is not None else 'json'] = content if content is not None else (
                        _request(state['row']) if body is None else body)
                    return await http.post('/emotion/piece/save'+query, **kwargs)
        return asyncio.run(run())
    return call, state


def _error(response, status, code):
    assert response.status_code == status and response.json() == {'code': code}
    assert response.headers['cache-control'] == 'no-store'
    assert PRIVATE not in response.text


def test_http_first_save_binds_current_source_tier_and_private_default(harness):
    call, s = harness
    response = call()
    assert response.status_code == 200
    assert s['auth'] == ['Bearer synthetic-owner']
    assert s['reads'][0]['owner_user_id'] == 'eq.'+OWNER
    assert s['reads'][0]['id'] == 'eq.'+s['row']['id']
    assert s['source'] == [('Bearer synthetic-owner', INPUT)]
    assert len(s['posts']) == 1
    sent = s['posts'][0]
    assert sent['p_owner_user_id'] == OWNER and sent['p_visibility_scope'] == 'private'
    assert sent['p_expected_subscription_tier'] == 'free'
    assert sent['p_expected_source_state']['original'] == s['handoff'].original.original_payload()
    assert sent['p_expected_source_state']['lineage'] == s['row']['source_lineage']
    assert not {'piece_text', 'content_payload', 'visual_recipe', 'source_lineage'} & response.json().keys()
    assert PRIVATE not in response.text


@pytest.mark.parametrize('headers,status', [({},401), ({'Authorization':'Bearer bad'},401),
    ({'Authorization':'Bearer synthetic-owner'},400),
    ({'Authorization':'Bearer synthetic-owner','Idempotency-Key':' '},400),
    ([('Authorization','Bearer synthetic-owner'),('Authorization','Bearer synthetic-viewer'),('Idempotency-Key','x')],401),
    ([('Authorization','Bearer synthetic-owner'),('Idempotency-Key','x'),('Idempotency-Key','y')],400)])
def test_http_rejects_missing_ambiguous_credentials_before_reads(harness, headers, status):
    call,s = harness
    _error(call(headers=headers,content=b'{'),status,'PIECE_AUTH_REQUIRED' if status==401 else 'PIECE_REQUEST_INVALID')
    assert s['reads'] == s['posts'] == []


@pytest.mark.parametrize('field', ['user_id','subscription_tier','expected_subscription_tier',
    'piece_text','source_lineage','expected_source_state','replay_only'])
def test_http_client_cannot_inject_identity_body_or_admission(harness, field):
    call,s = harness
    _error(call(body=dict(_request(s['row']),**{field:PRIVATE})),400,'PIECE_REQUEST_INVALID')
    assert s['reads'] == s['posts'] == []


@pytest.mark.parametrize('content', [b'null',b'[]',b'{',b'\xff'])
def test_http_malformed_body_is_private(harness, content):
    call,s = harness
    _error(call(content=content),400,'PIECE_REQUEST_INVALID')
    assert s['reads'] == s['posts'] == []


def test_http_other_owner_is_concealed(harness):
    call,s = harness
    _error(call(headers={'Authorization':'Bearer synthetic-viewer','Idempotency-Key':'x'}),404,'PIECE_NOT_FOUND')
    assert s['source'] == s['posts'] == []


@pytest.mark.parametrize('key,changed,code', [('expected_preview_revision',2,'PIECE_PREVIEW_STALE'),
    ('piece_text_hash','a'*64,'PIECE_HASH_MISMATCH'),('content_payload_hash','a'*64,'PIECE_HASH_MISMATCH'),
    ('visual_recipe_hash','a'*64,'PIECE_HASH_MISMATCH')])
def test_http_stale_or_changed_hash_has_no_save(harness,key,changed,code):
    call,s = harness
    _error(call(body=dict(_request(s['row']),**{key:changed})),409,code)
    assert s['source'] == s['posts'] == []


@pytest.mark.parametrize('state', ['cancelled','rejected','expired','deleted'])
def test_http_terminal_preview_is_not_saved(harness,state):
    call,s = harness; s['row']['lifecycle_status']=state
    _error(call(),409,'PIECE_CONFLICT'); assert s['posts'] == []


def test_http_expired_preview_has_no_save(harness):
    call,s=harness; s['row']['expires_at']='2000-01-01T00:00:00+00:00'
    _error(call(),409,'PIECE_PREVIEW_EXPIRED'); assert s['posts'] == []


@pytest.mark.parametrize('state', [None,'unavailable','blocked','unknown'])
def test_http_never_fabricates_safety_admission(harness,state):
    call,s=harness; s['row']['safety_state']=state
    _error(call(),422,'PIECE_SAFETY_UNAVAILABLE'); assert s['posts'] == []


@pytest.mark.parametrize('tier,fmt,formats,accepted', [
    ('free','short_essay',['short_essay','quote','declaration'],True),
    ('free','quote',['quote','short_essay'],False),
    ('plus','declaration',['short_essay','quote','declaration'],True),
    ('plus','quote',['short_essay','quote'],True),
    ('plus','short_essay',['short_essay'],True),
    ('plus','quote',['quote','declaration'],False),
    ('premium','quote',['quote','declaration'],True)])
def test_http_applies_current_format_policy_without_generation(harness,tier,fmt,formats,accepted):
    call,s=harness; s['row']=_row(tier,fmt,formats); s['handoff']=_handoff(s['row'],tier)
    if accepted:
        assert call().status_code==200 and len(s['posts'])==1
    else:
        _error(call(),422,'PIECE_FORMAT_NOT_ELIGIBLE'); assert s['posts']==[]


def test_http_current_plan_does_not_silently_rewrite_recipe(harness):
    call,s=harness; s['row']=_row('premium'); s['handoff']=_handoff(s['row'],'free')
    original=deepcopy(s['row'])
    _error(call(),422,'PIECE_VISUAL_SELECTION_NOT_ALLOWED')
    assert s['posts']==[] and s['row']==original


def test_http_source_lineage_change_is_conflict(harness):
    call,s=harness
    changed=deepcopy(s['row']); changed['source_lineage']['observation']['emlis_observation_result_identity']=str(uuid4())
    s['handoff']=_handoff(changed)
    _error(call(),409,'PIECE_CONFLICT'); assert s['posts']==[]


@pytest.mark.parametrize('code,status', [('PIECE_SOURCE_NOT_FOUND',404),('PIECE_SOURCE_NOT_ELIGIBLE',422),
    ('PIECE_AUTH_REQUIRED',401),('PIECE_TEMPORARILY_UNAVAILABLE',503)])
def test_http_source_failure_never_calls_save(harness,code,status):
    call,s=harness; s['source_error']=PieceContractError(code)
    _error(call(),status,code); assert s['posts']==[]


def test_http_saved_replay_does_not_require_source_or_current_tier(harness):
    call,s=harness; s['row']['lifecycle_status']='saved'; s['row']['expires_at']=None
    s['source_error']=AssertionError('saved replay must not read source')
    s['handler']=lambda args: httpx.Response(200,json=_result(s['row'],True))
    assert call().json()['idempotency_replayed'] is True
    assert s['source']==[] and s['posts'][0]['p_replay_only'] is True
    assert 'p_expected_subscription_tier' not in s['posts'][0]
    assert 'p_expected_source_state' not in s['posts'][0]


@pytest.mark.parametrize('status,payload', [(400,{'code':'P0001','message':'PIECE_CONFLICT '+PRIVATE}),
    (400,{'code':'23505','message':'PIECE_CONFLICT'}),(401,{'message':PRIVATE}),
    (404,{'message':PRIVATE}),(200,{'piece_text':PRIVATE})])
def test_http_invalid_ack_does_not_leak_or_retry(harness,status,payload):
    call,s=harness; s['handler']=lambda args:httpx.Response(status,json=payload)
    _error(call(),503,'PIECE_TEMPORARILY_UNAVAILABLE'); assert len(s['posts'])==1


def _native(harness,database):
    call,s=harness; conn,pg,_=database
    from psycopg.types.json import Jsonb
    conn.execute('CREATE SCHEMA auth')
    conn.execute('CREATE TABLE auth.users(id uuid PRIMARY KEY)')
    conn.execute('INSERT INTO auth.users VALUES (%s)',(OWNER,))
    conn.execute('CREATE TABLE public.emotions(id uuid PRIMARY KEY,user_id uuid,created_at timestamp,memo text,memo_action text,category jsonb,emotions jsonb,emotion_details jsonb)')
    original=s['handoff'].original.original_payload()
    conn.execute('INSERT INTO public.emotions VALUES (%s,%s,%s,%s,NULL,%s,%s,%s)',
        (INPUT,OWNER,original['created_at'],original['memo'],Jsonb([]),Jsonb([]),Jsonb([])))
    conn.execute((_ROOT/'supabase/migrations/20260911020509_emlis_input_threads_q2.sql').read_text())
    original=conn.execute('SELECT public.emlis_parent_source(e) FROM public.emotions e').fetchone()[0]
    s['handoff']=_handoff(s['row'],original=original)
    conn.execute("INSERT INTO public.emlis_input_threads(id,user_id,original_emotion_id,revision,state,issued_count,source_snapshot,data) VALUES(%s,%s,%s,1,'COMPLETED',0,%s,'{}')",(THREAD,OWNER,INPUT,Jsonb(original)))
    conn.execute("INSERT INTO public.emlis_thread_events(id,thread_id,seq,kind,round_index,payload) VALUES(%s,%s,1,'OBSERVATION',0,'{}')",(OBS,THREAD))
    conn.execute('UPDATE public.emlis_input_threads SET last_observation_event_id=%s',(OBS,))
    row=s['row']; record={k:row[k] for k in _B5['_KEYS']}
    record['eligible_formats']=row['preview_eligible_formats']
    preview=_B5['_issue'](conn,record=record)
    row['id']=preview['preview_id']
    def read(request):
        result=conn.execute('SELECT to_jsonb(r) FROM public.piece_records r WHERE id=%s AND owner_user_id=%s',
            (row['id'],request.url.params['owner_user_id'][3:])).fetchone()
        return httpx.Response(200,json=[result[0]] if result else [])
    def write(args):
        args=dict(args)
        if 'p_expected_source_state' in args: args['p_expected_source_state']=Jsonb(args['p_expected_source_state'])
        try: result=_B4['_rpc'](conn,'piece_save_v2',args)
        except pg.Error as exc:
            return httpx.Response(400,json={'code':exc.sqlstate,'message':exc.diag.message_primary,'details':PRIVATE})
        return httpx.Response(200,json=result)
    s['read_handler'],s['handler']=read,write
    return call,s


def test_native_http_save_lost_ack_replay_and_downgrade(database,harness):
    call,s=_native(harness,database); conn,_,_=database; write=s['handler']
    def lose(args):
        response=write(args); assert response.status_code==200
        raise httpx.ReadTimeout(PRIVATE)
    s['handler']=lose
    _error(call(),503,'PIECE_TEMPORARILY_UNAVAILABLE')
    assert _B4['_used'](conn)==1 and len(s['posts'])==1
    conn.execute('DELETE FROM public.emotions WHERE id=%s',(INPUT,))
    conn.execute("UPDATE public.profiles SET subscription_tier='unknown'")
    s['handler']=write; result=call()
    assert result.status_code==200 and result.json()['idempotency_replayed'] is True
    assert _B4['_used'](conn)==1 and len(s['source'])==1
    assert conn.execute('SELECT piece_text FROM public.piece_records').fetchone()[0]==s['row']['piece_text']


@pytest.mark.parametrize('change', ['source','thread','delete','tier'])
def test_native_http_rejects_state_changed_after_admission(database,harness,change):
    call,s=_native(harness,database); conn,_,_=database
    def mutate():
        if change=='source': conn.execute("UPDATE public.emotions SET memo='changed'")
        elif change=='thread': conn.execute('UPDATE public.emlis_input_threads SET revision=revision+1')
        elif change=='delete': conn.execute('DELETE FROM public.emotions')
        else: conn.execute("UPDATE public.profiles SET subscription_tier='premium'")
    s['source_hook']=mutate
    _error(call(),404 if change=='delete' else 409,'PIECE_NOT_FOUND' if change=='delete' else 'PIECE_CONFLICT')
    assert _B4['_used'](conn)==0
    assert conn.execute('SELECT lifecycle_status FROM public.piece_records').fetchone()==('preview_draft',)


@pytest.mark.parametrize('lock_target', ['source','thread'])
@pytest.mark.parametrize('commit_change', [True,False])
def test_native_save_observes_actual_source_lock_wait(database,harness,lock_target,commit_change):
    _,s=_native(harness,database); conn,pg,url=database
    h=s['handoff']; args=piece_v2_store.save_request_arguments(OWNER,_request(s['row']),'lock-save')
    from psycopg.types.json import Jsonb
    args.update(p_expected_subscription_tier='free',p_expected_source_state=Jsonb({
        'original':h.original.original_payload(),'thread_id':THREAD,'thread_revision':1,'lineage':h.lineage_payload()}))
    pids=Queue()
    def worker():
        with pg.connect(url,autocommit=True,connect_timeout=3) as other:
            other.execute("SET statement_timeout='8s'"); pids.put(other.info.backend_pid)
            try:return _B4['_rpc'](other,'piece_save_v2',args)
            except pg.Error as exc:return exc.diag.message_primary
    pool=ThreadPoolExecutor(max_workers=1)
    try:
        conn.execute('BEGIN')
        conn.execute("UPDATE public.emotions SET memo='changed'" if lock_target=='source' else
            'UPDATE public.emlis_input_threads SET revision=revision+1')
        future=pool.submit(worker); pid=pids.get(timeout=5); deadline=time.monotonic()+5
        while conn.info.backend_pid not in conn.execute('SELECT pg_blocking_pids(%s)',(pid,)).fetchone()[0]:
            assert time.monotonic()<deadline; time.sleep(.01)
        assert not future.done()
        conn.execute('COMMIT' if commit_change else 'ROLLBACK'); result=future.result(timeout=10)
        if commit_change: assert result=='PIECE_CONFLICT' and _B4['_used'](conn)==0
        else: assert result['lifecycle_status']=='saved' and _B4['_used'](conn)==1
    finally:
        conn.execute('ROLLBACK'); pool.shutdown(wait=True)


def test_native_replay_only_never_performs_first_save(database):
    conn,pg,_=database; row=_B4['_preview'](conn)
    with pytest.raises(pg.errors.RaiseException) as caught:
        _B4['_rpc'](conn,'piece_save_v2',dict(_B4['_args'](row),p_replay_only=True))
    assert caught.value.diag.message_primary=='PIECE_CONFLICT' and _B4['_used'](conn)==0


def test_production_app_keeps_piece_v2_router_unregistered():
    assert 'api_piece_v2' not in (_ROOT/'ai/services/ai_inference/app.py').read_text()


# PCE-7 operation stops, using the real admission/store and synthetic transport.
@pytest.mark.parametrize('configuration', [None, {}, {'requested': {}, 'ready': {}}])
def test_save_default_off_precedes_body_and_io(harness, configuration):
    call, s = harness
    s['app'].state.piece_v2_runtime = configuration
    _error(call(content=b'{private'), 503, 'PIECE_FEATURE_DISABLED')
    assert len(s['auth']) == 1
    assert s['reads'] == s['source'] == s['posts'] == []
    _error(call(headers={}, content=b'{private'), 401, 'PIECE_AUTH_REQUIRED')


@pytest.mark.parametrize('flag', ['piece_v2_save_enabled', 'piece_v2_preview_enabled'])
def test_save_checks_dependency_and_replay_stop(harness, flag):
    call, s = harness
    s['row']['lifecycle_status'] = 'saved'
    s['app'].state.piece_v2_runtime['ready'][flag] = False
    _error(call(), 503, 'PIECE_FEATURE_DISABLED')
    assert s['reads'] == s['posts'] == []


@pytest.mark.parametrize('scope', ['public', ' public '])
@pytest.mark.parametrize('flag', ['piece_v2_public_write_enabled', 'piece_v2_public_read_enabled'])
def test_public_save_stop_cannot_be_bypassed_with_padding(harness, scope, flag):
    call, s = harness
    s['app'].state.piece_v2_runtime['requested'][flag] = False
    _error(call(body=dict(_request(s['row']), visibility_scope=scope)), 503, 'PIECE_FEATURE_DISABLED')
    assert s['reads'] == s['source'] == s['posts'] == []
    assert call().status_code == 200  # private save has no public/owner-read prerequisite


def test_private_save_does_not_require_owner_read(harness):
    call, s = harness
    s['app'].state.piece_v2_runtime['requested']['piece_v2_owner_read_enabled'] = False
    assert call().status_code == 200
    assert len(s['posts']) == 1


@pytest.mark.parametrize('stage', ['read', 'source'])
def test_stop_during_admission_prevents_save_dispatch(harness, stage):
    call, s = harness
    def stop():
        s['app'].state.piece_v2_runtime['requested']['piece_v2_save_enabled'] = False
    if stage == 'source':
        s['source_hook'] = stop
    else:
        def read(request):
            stop()
            return httpx.Response(200, json=[s['row']])
        s['read_handler'] = read
    _error(call(), 503, 'PIECE_FEATURE_DISABLED')
    assert s['posts'] == []
    if stage == 'read':
        assert s['source'] == []


@pytest.mark.parametrize('lost_ack', [False, True])
def test_stop_after_save_dispatch_never_retries(harness, lost_ack):
    call, s = harness
    def write(args):
        s['app'].state.piece_v2_runtime['requested']['piece_v2_save_enabled'] = False
        if lost_ack:
            raise httpx.ReadTimeout(PRIVATE)
        return httpx.Response(200, json=_result(s['row']))
    s['handler'] = write
    _error(call(), 503, 'PIECE_FEATURE_DISABLED')
    assert len(s['posts']) == 1


def test_native_stop_before_save_keeps_preview_and_quota_untouched(database, harness):
    call, s = _native(harness, database)
    conn, _, _ = database
    def stop():
        s['app'].state.piece_v2_runtime['requested']['piece_v2_save_enabled'] = False
    s['source_hook'] = stop
    _error(call(), 503, 'PIECE_FEATURE_DISABLED')
    assert s['posts'] == [] and _B4['_used'](conn) == 0
    assert conn.execute('SELECT lifecycle_status FROM public.piece_records WHERE id=%s',
                        (s['row']['id'],)).fetchone()[0] == 'preview_draft'
