"""Real IF compiler/service with synthetic authenticated storage and model I/O."""
import asyncio
import copy
from dataclasses import asdict, replace
from datetime import datetime, timezone
import json
import importlib.util
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import httpx
import pytest
from fastapi import HTTPException
import analysis_if_route_service as service
import analysis_if_route_store as store
from analysis_if_model_source import SelfHostedAnalysisIfModelSource
from analysis_observed_service import private_storage_evidence
import analysis_cumulative_service as cumulative
from test_analysis_cumulative import OWNER, source_snapshot
from test_analysis_if_routes import packet, response


def base_fixture():
    snapshot = source_snapshot(2, tier='premium')
    artifact, coverage = cumulative.build_cumulative_map(OWNER, snapshot)
    private = private_storage_evidence(artifact)
    private['coverage'] = coverage
    private['source_record_refs'] = [r['original']['id'] for r in snapshot['members']]
    return dict(snapshot=snapshot, private=private, id=str(UUID(artifact.artifact_id[9:])),
        projection=artifact.safe_projection(authenticated_owner_scope=OWNER),
        text=artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'])


def request_body(base, *, key='test-person-operation', count=2):
    return dict(base_observed_map_ref=base['projection']['projection_of'],
        branch_point_id=base['projection']['nodes'][0]['node_ref'],
        branch_intent_text='次は自分の意見を言ってみたい。',
        constraint_texts=['相手が話している間は、話を遮りたくない。'],
        constraints_confirmed=False, requested_candidate_count=count,
        scenario_choice_texts=[], idempotency_key=key)


def base_context(base, guard=None):
    return dict(base_observed_map_ref=base['projection']['projection_of'],
        base_source_guard=guard or base['snapshot']['guard'],base_projection=base['projection'],
        base_private_evidence=base['private'],subscription_tier='premium',
        source_record_refs=[r['original']['id'] for r in base['snapshot']['members']])


def sql_fixture(guard=None, base=None):
    """Real immutable artifacts; PGlite supplies its own DB-native guard."""
    base = base_fixture() if base is None else copy.deepcopy(base)
    body = request_body(base)
    context = base_context(base, guard)
    key, _ = service._identity(OWNER, body)
    request = service._request(OWNER, body, context, key)
    pure = service._pure()
    prepared = pure.prepare_if_model_request(request)
    outcome = service._engine().generate(prepared.request,semantic_input=response(prepared))
    assert outcome.artifact is not None, outcome.reason_codes
    selected = outcome.artifact.safe_projection(authenticated_owner_scope=OWNER)['scenarios'][0]['scenario_ref']
    saved = service._engine().save_analysis_route_intent(outcome.artifact, authenticated_owner_scope=OWNER,
        selected_scenario_ref=selected,
        selection_source=service._session_source(OWNER, 'sql-selection', 'selection', selected),
        note_source=service._session_source(OWNER, 'sql-selection', 'note', '次に考えるときのために残します。'),
        saved_at='2026-11-14T09:00:00+00:00')
    return dict(base=base,set_storage=outcome.artifact.to_storage(),saved_storage=saved.to_storage(),
        operation_material=service._freeze_prepared(prepared),provider_receipt=asdict(response(prepared)))


class MemoryRpc:
    def __init__(self, base):
        self.base = base
        self.rows = {'scenario_set': [], 'saved_intent': []}
        self.calls = []
        self.tier = 'premium'
        self.operations = {}
        self.commit_failures = 0
        self.receive_ack_failure = False
        self.reserve_ack_failure = False

    async def __call__(self, name, p):
        self.calls.append((name, copy.deepcopy(p)))
        if p['p_user_id'] != OWNER or self.tier != 'premium':
            raise HTTPException(403, 'analysis_if_access_unavailable')
        if name == 'analysis_if_base_context':
            return copy.deepcopy(base_context(self.base))
        if name == 'analysis_if_operation_reserve':
            operation = self.operations.get(p['p_key_hash'])
            if operation is not None:
                if operation['request_hash'] != p['p_request_hash']:
                    raise HTTPException(409,'analysis_if_request_conflict')
                if p.get('p_reclaim') is True and operation['state']=='RESERVED':
                    operation['token']=str(uuid4())
                    return dict(state='RESERVED',operation_id=operation['id'],call_token=operation['token'],
                        material=copy.deepcopy(operation['material']),receipt=None,artifact_id=None)
                return dict(state=operation['state'],operation_id=operation['id'],call_token=None,
                    material=copy.deepcopy(operation['material']) if operation['state']=='RECEIVED' else None,
                    receipt=copy.deepcopy(operation['receipt']) if operation['state']=='RECEIVED' else None,
                    artifact_id=operation.get('artifact_id'))
            if p['p_material'] is None:
                return None
            operation=dict(state='RESERVED',id=str(UUID(int=500+len(self.operations))),
                token=str(UUID(int=600+len(self.operations))),request_hash=p['p_request_hash'],
                material=copy.deepcopy(p['p_material']),receipt=None)
            self.operations[p['p_key_hash']]=operation
            if self.reserve_ack_failure:
                self.reserve_ack_failure=False
                raise HTTPException(503,'synthetic_reserve_ack_lost')
            return dict(state='RESERVED',operation_id=operation['id'],call_token=operation['token'],
                material=None,receipt=None,artifact_id=None)
        if name in {'analysis_if_operation_start','analysis_if_operation_receive','analysis_if_operation_fail'}:
            operation=self.operations[p['p_key_hash']]
            valid_token=p['p_token']==operation['token']
            if name=='analysis_if_operation_start':
                started=valid_token and operation['state']=='RESERVED'
                if started:
                    operation['state']='CALL_STARTED'
                return dict(started=started)
            if name=='analysis_if_operation_receive':
                if not valid_token:
                    return dict(received=False)
                if operation['state']=='CALL_STARTED':
                    operation['state']='RECEIVED'
                    operation['receipt']=copy.deepcopy(p['p_receipt'])
                if self.receive_ack_failure:
                    self.receive_ack_failure=False
                    raise HTTPException(503,'synthetic_ack_lost')
                return dict(received=operation['state']=='RECEIVED')
            failed=valid_token and operation['state'] in {'RESERVED','CALL_STARTED'}
            if failed:
                operation['state']='FAILED'
            return dict(failed=failed)
        kind = p.get('p_kind')
        if name == 'analysis_if_artifacts_read':
            rows = self.rows[kind]
            if p.get('p_id'):
                rows = [r for r in rows if r['id'] == p['p_id']]
            if p.get('p_set_ref'):
                rows = [r for r in rows if r['storage']['bundle']['primary_artifact'].get('candidate_set_id', '')+'@1' == p['p_set_ref']]
            if p.get('p_key_hash'):
                rows = [r for r in rows if r['key'] == p['p_key_hash']]
                if rows and rows[0]['request'] != p['p_request_hash']:
                    raise HTTPException(409, 'analysis_if_request_conflict')
            rows = rows[p['p_offset']:p['p_offset']+p['p_limit']]
            return dict(items=[{k:r[k] for k in ('id','storage','created_at')} for r in rows], subscription_tier=self.tier)
        if name in {'analysis_if_set_commit','analysis_if_intent_commit'}:
            kind = 'scenario_set' if name == 'analysis_if_set_commit' else 'saved_intent'
            if kind=='scenario_set':
                operation=self.operations[p['p_key_hash']]
                assert operation['state']=='RECEIVED'
                if self.commit_failures:
                    self.commit_failures-=1
                    raise HTTPException(503,'synthetic_commit_ack_unknown')
            payload = p['p_storage']
            identity = str(UUID(payload['safe_projection']['projection_of'][9:41]))
            self.rows[kind].append(dict(id=identity,storage=copy.deepcopy(payload),
                created_at='2026-11-14T09:00:00+00:00',key=p['p_key_hash'],request=p['p_request_hash']))
            if kind=='scenario_set':
                operation['state']='COMPLETED'
                operation['artifact_id']=identity
            return identity
        raise AssertionError(name)


@pytest.fixture
def setup(monkeypatch):
    monkeypatch.setenv('COCOLON_ANALYSIS_OBSERVED_MODE','development')
    base = base_fixture()
    rpc = MemoryRpc(base)
    monkeypatch.setattr(store, '_rpc', rpc)
    return base, rpc


@pytest.mark.asyncio
async def test_normal_model_save_and_reads_keep_identity_without_regeneration(setup, monkeypatch):
    base, rpc = setup
    model = AsyncMock(side_effect=lambda p: response(p))
    body = request_body(base)
    created = await service.create_scenario_set(OWNER, body, model_source=model)
    assert created['status'] == 'GENERATED' and len(created['projection']['scenarios']) == 2
    assert created['scenario_set_ref'].startswith('scenario-set:')
    saved = await service.save_intent(OWNER, dict(source_scenario_set_ref=created['scenario_set_ref'],
        selected_scenario_ref=created['projection']['scenarios'][1]['scenario_ref'],
        user_note='自分で考えるために残します。',idempotency_key='person-selected-second'))
    assert saved['projection']['visible_note'] == '自分で考えるために残します。'
    assert saved['selected_scenario_label'] == created['projection']['scenarios'][1]['visible_label']
    assert saved['projection']['projection_of'] != created['projection']['projection_of']
    assert rpc.rows['saved_intent'][0]['storage']['bundle']['epistemic_partition'] == 'USER_SAVED_INTENT'
    monkeypatch.setattr(service._pure(), 'prepare_if_model_request', lambda *a: pytest.fail('read generated'))
    monkeypatch.setattr(service._pure(), 'admit_if_model_response', lambda *a: pytest.fail('read admitted a new proposal'))
    assert (await service.get_artifact(OWNER,'scenario_set',created['id']))['projection'] == created['projection']
    assert (await service.get_artifact(OWNER,'saved_intent',saved['id']))['content_text'] == saved['content_text']
    assert (await service.create_scenario_set(OWNER,body,model_source=model))['idempotency_replayed'] is True
    assert (await service.list_artifacts(OWNER,'scenario_set'))['items'][0]['id'] == created['id']
    assert model.await_count == 1
    public = json.dumps([created,saved])
    assert 'private_evidence' not in public and 'session_sources' not in public and 'model_receipt' not in public


@pytest.mark.asyncio
async def test_missing_intent_or_constraints_asks_before_model_or_write(setup):
    base, rpc = setup
    for field,value,reason in [('branch_intent_text',None,'analysis_if_intent_required'),
                                ('constraint_texts',[],'analysis_if_constraints_required')]:
        model = AsyncMock(side_effect=AssertionError('insufficient material called model'))
        body = dict(request_body(base),**{field:value,'idempotency_key':field})
        result = await service.create_scenario_set(OWNER,body,model_source=model)
        assert result['status'] == 'QUESTION_PENDING' and result['reason_codes'] == [reason]
        assert result['artifact'] is None and result['clarification_request']['answer_source_role'] == 'SIMULATION_SESSION_MATERIAL'
        model.assert_not_awaited()
    assert not rpc.rows['scenario_set']


@pytest.mark.asyncio
async def test_concurrent_duplicate_does_one_model_call_and_one_write(setup):
    base,rpc = setup
    started,release = asyncio.Event(),asyncio.Event()
    async def provider(prepared):
        started.set()
        await release.wait()
        return response(prepared)
    model = AsyncMock(side_effect=provider)
    first=asyncio.create_task(service.create_scenario_set(OWNER,request_body(base),model_source=model))
    await started.wait()
    second=asyncio.create_task(service.create_scenario_set(OWNER,request_body(base),model_source=model))
    release.set()
    a,b=await asyncio.gather(first,second)
    assert a['id']==b['id'] and model.await_count==1 and len(rpc.rows['scenario_set'])==1
    with pytest.raises(HTTPException) as caught:
        await service.create_scenario_set(OWNER,dict(request_body(base),branch_intent_text='別の意向です。'),model_source=model)
    assert caught.value.status_code==409 and model.await_count==1


@pytest.mark.asyncio
async def test_model_failure_off_or_runtime_stop_never_commits(setup,monkeypatch):
    base,rpc=setup
    body=request_body(base)
    monkeypatch.setenv('COCOLON_ANALYSIS_MODEL_SOURCE','off')
    with pytest.raises(HTTPException) as caught:
        await service.create_scenario_set(OWNER,body)
    assert caught.value.status_code==503
    with pytest.raises(HTTPException):
        await service.create_scenario_set(OWNER,dict(body,idempotency_key='model-failed'),model_source=AsyncMock(side_effect=RuntimeError('synthetic')))
    async def stopping(prepared):
        monkeypatch.setenv('COCOLON_ANALYSIS_OBSERVED_MODE','read_only')
        return response(prepared)
    with pytest.raises(HTTPException):
        await service.create_scenario_set(OWNER,dict(body,idempotency_key='runtime-stopped'),model_source=stopping)
    assert not rpc.rows['scenario_set']


@pytest.mark.asyncio
async def test_nonmember_selection_and_corrupt_saved_data_fail_closed(setup):
    base,rpc=setup
    created=await service.create_scenario_set(OWNER,request_body(base),model_source=AsyncMock(side_effect=lambda p:response(p)))
    with pytest.raises(HTTPException) as caught:
        await service.save_intent(OWNER,dict(source_scenario_set_ref=created['scenario_set_ref'],
            selected_scenario_ref='analysis-if-scenario:outside@1',user_note=None,idempotency_key='invalid-selection'))
    assert caught.value.status_code==422 and not rpc.rows['saved_intent']
    rpc.rows['scenario_set'][0]['storage']['content_text']='corrupt'
    with pytest.raises(HTTPException) as caught:
        await service.get_artifact(OWNER,'scenario_set',created['id'])
    assert caught.value.status_code==503


@pytest.mark.asyncio
async def test_actual_if_transport_is_one_bounded_request_with_bound_receipt(setup):
    base,rpc=setup
    calls=[]
    async def handler(req):
        data=json.loads(req.content)
        calls.append(data)
        materials=json.loads(data['messages'][1]['content'])
        assert materials['requested_candidate_count']==2
        # The application uses the actual frozen prepare object for the mock
        # response, just as the configured transport returns its raw receipt.
        key,_=service._identity(OWNER,request_body(base))
        prepared=service._pure().prepare_if_model_request(service._request(OWNER,request_body(base),base_context(base),key))
        return httpx.Response(200,json=dict(model='existing-4b',choices=[dict(finish_reason='stop',
            message=dict(role='assistant',content=json.dumps(packet(prepared),ensure_ascii=False)))]))
    model=SelfHostedAnalysisIfModelSource(endpoint='https://synthetic.invalid/v1/chat/completions',
        model='existing-4b',api_key='synthetic-only',transport=httpx.MockTransport(handler))
    result=await service.create_scenario_set(OWNER,request_body(base),model_source=model)
    assert result['status']=='GENERATED' and len(calls)==1
    assert calls[0]['chat_template_kwargs']=={'enable_thinking':False}
    assert rpc.rows['scenario_set'][0]['storage']['model_receipt']['finish_reason']=='stop'


@pytest.mark.asyncio
@pytest.mark.parametrize('selector,budget', [('self_hosted.v1', 2048),
    ('self_hosted.semantic.v1', 4096)])
async def test_configured_if_transport_matches_existing_analysis_server_budget(setup, monkeypatch,
        selector, budget):
    """Use the real request handler in memory: no socket, GPU or model call."""
    from io import BytesIO
    from types import SimpleNamespace
    import time
    import analysis_if_model_source as source
    from ai.tools.serve_emlis_natural_reply import make_handler

    base, rpc = setup
    frozen_settings = (selector, 'https://synthetic.invalid/v1/chat/completions',
        'existing-analysis-4b', 'fictional-key-only')
    monkeypatch.setattr(source, '_settings', lambda: frozen_settings)
    model = source.application_analysis_if_model_source()
    seen = []
    key, _ = service._identity(OWNER, request_body(base))
    prepared = service._pure().prepare_if_model_request(service._request(OWNER,
        request_body(base), base_context(base), key))

    def generate(messages, deadline):
        seen.append(messages)
        return json.dumps(packet(prepared), ensure_ascii=False), 'stop'

    handler_type = make_handler(generate, api_key=frozen_settings[3],
        model_name=frozen_settings[2], deadline=time.monotonic() + 20,
        max_requests=1, max_new_tokens=budget)

    def handle(request):
        body = json.loads(request.content)
        assert body['max_tokens'] == budget
        assert body['model'] == frozen_settings[2]
        assert body['messages'] == prepared.messages()
        handler = handler_type.__new__(handler_type)
        handler.path = '/v1/chat/completions'
        handler.headers = dict(request.headers)
        handler.headers['Content-Length'] = str(len(request.content))
        handler.headers['Authorization'] = request.headers['authorization']
        handler.rfile = BytesIO(request.content)
        handler.connection = SimpleNamespace(settimeout=lambda seconds: None)
        captured = []
        handler.reply = lambda status, value: captured.append((status, value))
        handler.do_POST()
        status, value = captured[0]
        return httpx.Response(status, json=value)

    model._transport = httpx.MockTransport(handle)
    result = await service.create_scenario_set(OWNER, request_body(base), model_source=model)
    assert result['status'] == 'GENERATED' and len(seen) == 1
    assert len(rpc.rows['scenario_set']) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize('failure',['status','truncated','wrong_model','tool'])
async def test_transport_failure_never_retries_or_saves(setup,failure):
    base,rpc=setup
    calls=[]
    async def handler(req):
        calls.append(req)
        if failure=='status':
            return httpx.Response(503,json={'untrusted':'synthetic only'})
        message=dict(role='assistant',content='{}')
        if failure=='tool':
            message['tool_calls']=[{'name':'unexpected'}]
        return httpx.Response(200,json=dict(model='other' if failure=='wrong_model' else 'existing-4b',
            choices=[dict(finish_reason='length' if failure=='truncated' else 'stop',message=message)]))
    model=SelfHostedAnalysisIfModelSource(endpoint='https://synthetic.invalid/v1/chat/completions',
        model='existing-4b',api_key='synthetic-only',transport=httpx.MockTransport(handler))
    with pytest.raises(HTTPException) as caught:
        await service.create_scenario_set(OWNER,request_body(base),model_source=model)
    assert caught.value.status_code==503 and len(calls)==1 and not rpc.rows['scenario_set']


@pytest.mark.asyncio
async def test_another_service_instance_cannot_start_same_provider_operation(setup):
    base,rpc=setup
    spec=importlib.util.spec_from_file_location('analysis_if_second_service',service.__file__)
    second_service=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(second_service)
    assert second_service._locks is not service._locks
    started,release=asyncio.Event(),asyncio.Event()
    async def provider(prepared):
        started.set()
        await release.wait()
        return response(prepared)
    model=AsyncMock(side_effect=provider)
    first=asyncio.create_task(service.create_scenario_set(OWNER,request_body(base),model_source=model))
    await started.wait()
    other_model=AsyncMock(side_effect=AssertionError('another process repeated provider'))
    pending=await second_service.create_scenario_set(OWNER,request_body(base),model_source=other_model)
    assert pending['status']=='PENDING' and pending['state']=='CALL_STARTED'
    other_model.assert_not_awaited()
    release.set()
    completed=await first
    again=await second_service.create_scenario_set(OWNER,request_body(base),model_source=other_model)
    assert again['id']==completed['id'] and again['idempotency_replayed']
    assert model.await_count==1 and len(rpc.rows['scenario_set'])==1


@pytest.mark.asyncio
@pytest.mark.parametrize('failure',['receipt_ack','commit_after_receipt'])
async def test_received_raw_survives_failure_and_resumes_without_new_provider(setup,failure):
    base,rpc=setup
    rpc.receive_ack_failure=failure=='receipt_ack'
    rpc.commit_failures=1 if failure=='commit_after_receipt' else 0
    model=AsyncMock(side_effect=lambda p:response(p))
    with pytest.raises(HTTPException) as caught:
        await service.create_scenario_set(OWNER,request_body(base),model_source=model)
    assert caught.value.status_code==503
    key,_=service._identity(OWNER,request_body(base))
    operation=rpc.operations[key]
    assert operation['state']=='RECEIVED' and operation['receipt']['finish_reason']=='stop'
    raw=operation['receipt']['raw']
    no_provider=AsyncMock(side_effect=AssertionError('resumption regenerated'))
    completed=await service.create_scenario_set(OWNER,request_body(base),model_source=no_provider)
    assert completed['status']=='GENERATED' and model.await_count==1
    assert rpc.rows['scenario_set'][0]['storage']['model_receipt']['raw']==raw
    no_provider.assert_not_awaited()


@pytest.mark.asyncio
async def test_cancelled_started_operation_is_terminal_for_the_same_key(setup):
    base,rpc=setup
    started=asyncio.Event()
    async def cancelled_provider(prepared):
        started.set()
        await asyncio.Event().wait()
    model=AsyncMock(side_effect=cancelled_provider)
    task=asyncio.create_task(service.create_scenario_set(OWNER,request_body(base),model_source=model))
    await started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    no_provider=AsyncMock(side_effect=AssertionError('cancelled operation regenerated'))
    with pytest.raises(HTTPException) as caught:
        await service.create_scenario_set(OWNER,request_body(base),model_source=no_provider)
    assert caught.value.status_code==409 and model.await_count==1
    no_provider.assert_not_awaited()


@pytest.mark.asyncio
async def test_read_only_after_received_preserves_raw_for_explicit_resume(setup,monkeypatch):
    base,rpc=setup
    async def model(prepared):
        monkeypatch.setenv('COCOLON_ANALYSIS_OBSERVED_MODE','read_only')
        return response(prepared)
    with pytest.raises(HTTPException):
        await service.create_scenario_set(OWNER,request_body(base),model_source=model)
    key,_=service._identity(OWNER,request_body(base))
    assert rpc.operations[key]['state']=='RECEIVED' and not rpc.rows['scenario_set']
    monkeypatch.setenv('COCOLON_ANALYSIS_OBSERVED_MODE','development')
    no_provider=AsyncMock(side_effect=AssertionError('runtime restart regenerated'))
    assert (await service.create_scenario_set(OWNER,request_body(base),model_source=no_provider))['status']=='GENERATED'
    no_provider.assert_not_awaited()


@pytest.mark.asyncio
async def test_read_only_during_start_claim_does_not_call_provider(setup,monkeypatch):
    base,rpc=setup
    original_start=store.start
    async def start_and_stop(*args):
        result=await original_start(*args)
        monkeypatch.setenv('COCOLON_ANALYSIS_OBSERVED_MODE','read_only')
        return result
    monkeypatch.setattr(store,'start',start_and_stop)
    no_provider=AsyncMock(side_effect=AssertionError('runtime stop was ignored'))
    with pytest.raises(HTTPException):
        await service.create_scenario_set(OWNER,request_body(base),model_source=no_provider)
    key,_=service._identity(OWNER,request_body(base))
    assert rpc.operations[key]['state']=='FAILED'
    no_provider.assert_not_awaited()


@pytest.mark.asyncio
async def test_lost_reservation_ack_reclaims_frozen_material_without_refresh(setup,monkeypatch):
    base,rpc=setup
    rpc.reserve_ack_failure=True
    model=AsyncMock(side_effect=lambda p:response(p))
    with pytest.raises(HTTPException) as caught:
        await service.create_scenario_set(OWNER,request_body(base),model_source=model)
    assert caught.value.status_code==503
    key,_=service._identity(OWNER,request_body(base))
    old_token=rpc.operations[key]['token']
    original_material=copy.deepcopy(rpc.operations[key]['material'])
    monkeypatch.setattr(store,'base_context',AsyncMock(side_effect=AssertionError('reclaim refreshed base')))
    result=await service.create_scenario_set(OWNER,request_body(base),model_source=model)
    assert result['status']=='GENERATED' and model.await_count==1
    assert model.await_args.args[0]==service._restore_prepared(original_material)
    assert rpc.operations[key]['token']!=old_token
    assert await store.start(OWNER,key,old_token)=={'started':False}


@pytest.mark.asyncio
async def test_read_only_reserved_lookup_does_not_replace_token_or_material(setup,monkeypatch):
    base,rpc=setup
    body=request_body(base)
    key,request_hash=service._identity(OWNER,body)
    prepared=service._pure().prepare_if_model_request(service._request(OWNER,body,base_context(base),key))
    await store.reserve(OWNER,key,request_hash,base_ref=body['base_observed_map_ref'],
        guard=base_context(base)['base_source_guard'],material=service._freeze_prepared(prepared))
    before=copy.deepcopy(rpc.operations[key])
    monkeypatch.setenv('COCOLON_ANALYSIS_OBSERVED_MODE','read_only')
    model=AsyncMock(side_effect=AssertionError('read-only lookup called provider'))
    result=await service.create_scenario_set(OWNER,body,model_source=model)
    assert result['status']=='PENDING' and result['state']=='RESERVED'
    assert rpc.operations[key]==before
    assert all(not p.get('p_reclaim') for name,p in rpc.calls if name=='analysis_if_operation_reserve')
    model.assert_not_awaited()


@pytest.mark.asyncio
async def test_reclaim_fences_original_service_before_its_start_claim(setup,monkeypatch):
    base,rpc=setup
    spec=importlib.util.spec_from_file_location('analysis_if_reclaim_service',service.__file__)
    other=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(other)
    original_start=store.start
    paused,release=asyncio.Event(),asyncio.Event()
    old_tokens=[]
    async def delayed_start(*args):
        if not old_tokens:
            old_tokens.append(args[2])
            paused.set()
            await release.wait()
        return await original_start(*args)
    monkeypatch.setattr(store,'start',delayed_start)
    old_model=AsyncMock(side_effect=AssertionError('fenced original token called provider'))
    original=asyncio.create_task(service.create_scenario_set(OWNER,request_body(base),model_source=old_model))
    await paused.wait()
    new_model=AsyncMock(side_effect=lambda p:response(p))
    completed=await other.create_scenario_set(OWNER,request_body(base),model_source=new_model)
    release.set()
    pending=await original
    assert pending['status']=='PENDING' and completed['status']=='GENERATED'
    old_model.assert_not_awaited()
    assert new_model.await_count==1 and len(rpc.rows['scenario_set'])==1
    again=await service.create_scenario_set(OWNER,request_body(base),model_source=old_model)
    assert again['id']==completed['id'] and again['idempotency_replayed']


def old_instruction_prepared(prepared, instruction_version='legacy'):
    from cocolon_meaning_experience_engine.cores.analysis.if_route_realizer import (
        _IF_MODEL_INSTRUCTION_LEGACY, _IF_MODEL_INSTRUCTION_PERSON_ALTERNATIVES,
        _IF_MODEL_INSTRUCTION_UNKNOWN_ORDER)
    from cocolon_meaning_experience_engine.cores.analysis.source_adapter import commitment
    messages=prepared.messages()
    messages[0]['content']=({'legacy':_IF_MODEL_INSTRUCTION_LEGACY,
        'person_alternatives':_IF_MODEL_INSTRUCTION_PERSON_ALTERNATIVES,
        'unknown_order':_IF_MODEL_INSTRUCTION_UNKNOWN_ORDER}[instruction_version])
    ref='analysis-if-request:'+commitment([asdict(prepared.request),json.loads(prepared.base_seed_json),messages])[7:]
    return replace(prepared,request_ref=ref,messages_json=json.dumps(messages,ensure_ascii=False,sort_keys=True,separators=(',',':')))


@pytest.mark.asyncio
@pytest.mark.parametrize('state',['RESERVED','RECEIVED'])
@pytest.mark.parametrize('instruction_version',['legacy','person_alternatives','unknown_order'])
async def test_prior_instruction_operation_keeps_its_exact_material_and_raw(setup,state,instruction_version):
    base,rpc=setup;body=request_body(base);key,request_hash=service._identity(OWNER,body)
    current=service._pure().prepare_if_model_request(service._request(OWNER,body,base_context(base),key))
    legacy=old_instruction_prepared(current,instruction_version)
    assert legacy.request_ref!=current.request_ref and legacy.messages()!=current.messages()
    op=await store.reserve(OWNER,key,request_hash,base_ref=body['base_observed_map_ref'],
        guard=base_context(base)['base_source_guard'],material=service._freeze_prepared(legacy))
    receipt=response(legacy)
    if state=='RECEIVED':
        assert await store.start(OWNER,key,op['call_token'])=={'started':True}
        assert await store.receive(OWNER,key,op['call_token'],asdict(receipt))=={'received':True}
        model=AsyncMock(side_effect=AssertionError('received raw was regenerated'))
    else:
        async def old_provider(prepared):
            assert prepared==legacy and prepared.messages_json==legacy.messages_json
            return receipt
        model=AsyncMock(side_effect=old_provider)
    result=await service.create_scenario_set(OWNER,body,model_source=model)
    assert result['status']=='GENERATED' and model.await_count==(state=='RESERVED')
    stored=rpc.rows['scenario_set'][0]['storage']
    assert stored['model_receipt']==asdict(receipt)
    assert stored['model_receipt']['request_ref']==legacy.request_ref


@pytest.mark.parametrize('instruction_version',['legacy','person_alternatives','unknown_order'])
def test_if_prior_instruction_admission_refuses_mixed_or_unrecognized_bindings(instruction_version):
    from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import digest
    base=base_fixture();body=request_body(base);key,_=service._identity(OWNER,body)
    current=service._pure().prepare_if_model_request(service._request(OWNER,body,base_context(base),key))
    legacy=old_instruction_prepared(current,instruction_version);receipt=response(legacy)
    assert service._engine().generate(legacy.request,semantic_input=receipt).status.value=='GENERATED'
    mixed=replace(receipt,messages_sha256=digest(current.messages()))
    assert service._engine().generate(legacy.request,semantic_input=mixed).status.value=='REJECTED'
    assert service._engine().generate(legacy.request,semantic_input=replace(receipt,request_ref='invented')).status.value=='REJECTED'
