"""Real semantic lifecycle with a synthetic HTTP provider and owned RPC store.

These tests exercise routing/storage/compatibility, not 4B reading quality.
"""
import asyncio
from copy import deepcopy
import json
from pathlib import Path
from uuid import UUID
from unittest.mock import AsyncMock

from fastapi import FastAPI, HTTPException
import httpx
import pytest

import analysis_cumulative_service as service
import analysis_model_source as sources
import analysis_semantic_map as semantic
from cocolon_meaning_experience_engine.cores.analysis.observed_route_realizer import CATEGORY_LABEL_PREFIX
from test_analysis_cumulative import OWNER
from test_analysis_cumulative_model_source import sql_source
from test_analysis_semantic_map import candidate, sample


MODEL = 'synthetic-semantic-4b'
ENDPOINT = 'https://synthetic-semantic.invalid/v1/chat/completions'


def row_from_projection(projection, snapshot, coverage):
    return dict(id=str(UUID(projection['projection_of'][9:-2])), source_profile='cumulative.v1',
        report_mode='standard', report_type='latest', title='わたしマップ',
        period_start=snapshot['period_start'], period_end=snapshot['period_end'],
        generated_at=snapshot['period_end'], snapshot_month=None, captured_at=None,
        content_text=service._projection_text(projection),
        content_json=dict(report_mode='standard', watashiMap=deepcopy(projection),
            map_context=deepcopy(coverage)))


class OwnedStore:
    def __init__(self, snapshot=None, current=None):
        self.snapshot = deepcopy(sample() if snapshot is None else snapshot)
        self.current = deepcopy(current)
        self.calls = []
        self.saved = []

    async def __call__(self, name, payload):
        self.calls.append((name, deepcopy(payload)))
        assert payload['p_user_id'] == OWNER
        if name == 'analysis_cumulative_read':
            items = [deepcopy(self.current)] if self.current else []
            if items and payload.get('p_id') and items[0]['id'] != payload['p_id']:
                items = []
            return dict(items=items, subscription_tier='free', matched=True, history_limit=2)
        if name == 'analysis_cumulative_source_snapshot':
            return deepcopy(self.snapshot)
        assert name == 'analysis_cumulative_commit'
        if payload['p_guard'] != self.snapshot['guard']:
            raise HTTPException(409, 'analysis_source_changed')
        if payload.get('p_existing_id'):
            assert self.current['id'] == payload['p_existing_id']
            return self.current['id']
        self.saved.append(deepcopy(payload))
        projection = payload['p_projection']
        self.current = row_from_projection(projection, self.snapshot,
            payload['p_private_evidence']['coverage'])
        assert self.current['content_text'] == payload['p_text']
        return self.current['id']


def semantic_source(handler):
    return sources.SelfHostedSemanticAnalysisModelSource(endpoint=ENDPOINT, model=MODEL,
        api_key='synthetic-private-key', transport=httpx.MockTransport(handler))


def completion(packet=None, *, finish='stop'):
    return dict(model=MODEL, choices=[dict(finish_reason=finish,
        message=dict(role='assistant', content=semantic._canonical(candidate() if packet is None else packet)))])


def setup_store(monkeypatch, store):
    monkeypatch.setattr(service, '_rpc', store)
    monkeypatch.setattr(service, 'observed_mode', lambda: 'development')
    # A semantic error must never be disguised by the old finite compiler.
    monkeypatch.setattr(service, 'build_cumulative_map', lambda *a, **kw:
        (_ for _ in ()).throw(AssertionError('finite fallback')))


def test_semantic_http_save_non_generating_reread_and_compatibility(monkeypatch):
    store = OwnedStore()
    setup_store(monkeypatch, store)
    acquired = []

    def handler(request):
        body = json.loads(request.content)
        acquired.append(body)
        assert request.headers['authorization'] == 'Bearer synthetic-private-key'
        assert body['model'] == MODEL and body['max_tokens'] == 4096
        assert body['chat_template_kwargs'] == {'enable_thinking': False}
        assert 'それぞれの世界における座標' in body['messages'][0]['content']
        material = json.loads(body['messages'][1]['content'])
        assert len(material['records']) == 2 and len(material['fields']) == 3
        return httpx.Response(200, json=completion())

    source = semantic_source(handler)

    async def run():
        created = await service.ensure_map(OWNER, model_source=source)
        # Stored viewing must not reacquire either a provider or a CMEE author.
        monkeypatch.setattr(semantic.MeaningExperienceEngine, 'generate', lambda *a, **k:
            (_ for _ in ()).throw(AssertionError('stored read re-entered CMEE generation')))
        reread = await service.ensure_map(OWNER, model_source=source)
        read_only = await service.ensure_map(OWNER, ensure=False, model_source=source)
        assert created['refreshed'] and not reread['refreshed'] and not read_only['refreshed']
        assert created['meta'] == reread['meta'] == read_only['meta']
        assert created['content_text'] == reread['content_text']
        assert len(acquired) == len(store.saved) == 1
        assert store.saved[0]['p_private_evidence']['graph']['nodes'][1]['record_refs']
        projection = created['meta']
        assert projection['wire_kind'] == 'watashi.map.v3'
        assert service.map_response_for_renderer(created, 'semantic.v1') is created
        legacy = service.map_response_for_renderer(created, None)
        assert legacy['meta']['wire_kind'] == 'watashi.map.v2'
        assert legacy['meta']['edges'] == []
        assert [n['node_ref'] for n in legacy['meta']['nodes']] == [n['node_ref'] for n in projection['nodes']]
        for node in projection['nodes']:
            assert all(qualifier in legacy['content_text'] for qualifier in node['unknowns'])
            assert all(context in legacy['content_text'] for context in node['context'])
        assert legacy['content_text'] == service._projection_text(legacy['meta'])
        service._checked_v2_projection(legacy['meta'], created['report_id'])
        assert created['meta']['wire_kind'] == 'watashi.map.v3'
        detail = {'status': 'ok', 'item': deepcopy(store.current)}
        old_detail = service.map_response_for_renderer(detail, None)
        assert old_detail['item']['content_json']['watashiMap'] == legacy['meta']
        assert detail['item']['content_json']['watashiMap'] == projection

    asyncio.run(run())


@pytest.mark.parametrize('defect', ['http_error', 'length', 'bad_quote', 'bad_relation'])
def test_invalid_semantic_acquisition_never_commits_or_uses_finite_fallback(monkeypatch, defect):
    store = OwnedStore()
    setup_store(monkeypatch, store)

    def handler(request):
        if defect == 'http_error':
            return httpx.Response(503, json={'error': 'synthetic-private-upstream-detail'})
        packet = candidate()
        if defect == 'bad_quote':
            packet['nodes'][0]['evidence'][0]['quote'] = 'source does not contain this'
        if defect == 'bad_relation':
            packet['edges'][0]['relation_kind'] = 'CAUSES'
        return httpx.Response(200, json=completion(packet, finish='length' if defect == 'length' else 'stop'))

    async def run():
        with pytest.raises(HTTPException) as exc:
            await service.ensure_map(OWNER, model_source=semantic_source(handler))
        assert exc.value.status_code == (503 if defect in {'http_error', 'length'} else 422)
        assert 'synthetic-private' not in str(exc.value.detail)
        assert store.saved == [] and store.current is None
        assert not any(name == 'analysis_cumulative_commit' for name, _ in store.calls)

    asyncio.run(run())


def test_semantic_replaces_fully_category_current_v2_without_force(monkeypatch):
    snapshot = sample()
    legacy = dict(schema_version='cocolon.cmee.analysis_watashi_map_safe_projection.v1alpha1',
        wire_kind='watashi.map.v2', projection_of='artifact:' + UUID(int=900).hex + '@1',
        artifact_version=1, period_label='これまでの記録',
        period_comparison=dict(state='NO_PREVIOUS', reason_codes=[], safe_change_kinds=[]),
        nodes=[dict(node_ref='n1', node_kind='ATTENTION_OR_THOUGHT',
            visible_label=CATEGORY_LABEL_PREFIX + '価値観\n自分で選びたい', evidence_badge_count=1)],
        edges=[], annotation_badges=[], unknown_gaps=[], conflict_badges=[],
        accessibility_linear_order=['n1'])
    counts = dict(profile='cumulative.v1', source_count=2, processed_count=2,
        mapped_count=1, unparsed_count=2, excluded_count=0, exclusion_reasons={}, stale_supplement_count=0)
    store = OwnedStore(snapshot, row_from_projection(legacy, snapshot, counts))
    setup_store(monkeypatch, store)

    async def run():
        result = await service.ensure_map(OWNER, model_source=semantic_source(
            lambda request: httpx.Response(200, json=completion())))
        assert result['refreshed'] and result['meta']['wire_kind'] == 'watashi.map.v3'
        assert len(store.saved) == 1 and store.saved[0]['p_force'] is True

    asyncio.run(run())


def test_empty_or_all_safety_sources_never_reach_http_provider(monkeypatch):
    calls = []
    source = semantic_source(lambda request: calls.append(request) or httpx.Response(200, json=completion()))

    async def run():
        empty = sample()
        empty['members'] = []
        store = OwnedStore(empty)
        setup_store(monkeypatch, store)
        result = await service.ensure_map(OWNER, model_source=source)
        assert result['has_visible_content'] is False and result['map_context']['source_count'] == 0
        unsafe = sample()
        for member in unsafe['members']:
            member['original']['memo'] = '死にたい。'
        store = OwnedStore(unsafe)
        setup_store(monkeypatch, store)
        result = await service.ensure_map(OWNER, model_source=source)
        assert result['has_visible_content'] is False
        assert result['map_context']['source_count'] == result['map_context']['excluded_count'] == 2
        assert store.saved == [] and calls == []

    asyncio.run(run())


def test_safety_record_is_excluded_before_http_without_erasing_eligible_history(monkeypatch):
    snapshot = sample()
    snapshot['members'][1]['original']['memo'] = '死にたい。'
    store = OwnedStore(snapshot)
    setup_store(monkeypatch, store)
    packet = candidate()
    packet['nodes'] = packet['nodes'][:1]
    packet['edges'] = []
    acquired = []

    def handler(request):
        material = json.loads(json.loads(request.content)['messages'][1]['content'])
        acquired.append(material)
        assert len(material['records']) == len(material['fields']) == 1
        assert '死にたい' not in json.dumps(material, ensure_ascii=False)
        return httpx.Response(200, json=completion(packet))

    async def run():
        result = await service.ensure_map(OWNER, model_source=semantic_source(handler))
        assert result['refreshed'] and len(acquired) == len(store.saved) == 1
        counts = result['map_context']
        assert counts['source_count'] == 2 and counts['processed_count'] == counts['excluded_count'] == 1
        assert counts['exclusion_reasons'] == {'analysis_separate_safety_required': 1}
        assert len(store.saved[0]['p_private_evidence']['source_members']) == 1

    asyncio.run(run())


def test_ordinary_factory_semantic_selector_and_configuration_change_prevents_save(monkeypatch):
    store = OwnedStore()
    setup_store(monkeypatch, store)
    for key, value in dict(COCOLON_ANALYSIS_MODEL_SOURCE=sources.SEMANTIC_SELECTOR,
            COCOLON_ANALYSIS_MODEL_ENDPOINT=ENDPOINT, COCOLON_ANALYSIS_MODEL=MODEL,
            COCOLON_ANALYSIS_MODEL_API_KEY='synthetic-private-key').items():
        monkeypatch.setenv(key, value)
    original_client = httpx.AsyncClient
    acquired = []

    def handler(request):
        acquired.append(request)
        monkeypatch.setenv('COCOLON_ANALYSIS_MODEL', 'new-config-before-commit')
        return httpx.Response(200, json=completion())

    def client(*args, **kwargs):
        kwargs['transport'] = httpx.MockTransport(handler)
        return original_client(*args, **kwargs)

    monkeypatch.setattr(sources.httpx, 'AsyncClient', client)
    sources._configured_source.cache_clear()
    source = sources.application_analysis_model_source()
    assert sources.is_semantic_analysis_model_source(source)

    async def run():
        with pytest.raises(HTTPException) as exc:
            # No explicit provider argument: this is the ordinary configured path.
            await service.ensure_map(OWNER)
        assert exc.value.status_code == 503
        assert len(acquired) == 1 and store.saved == []

    asyncio.run(run())
    sources._configured_source.cache_clear()


def test_source_changed_during_semantic_response_is_not_committed(monkeypatch):
    store = OwnedStore()
    setup_store(monkeypatch, store)

    def handler(request):
        store.snapshot['guard'] = 'analysis-db-cumulative-v1:' + 'b'*64
        return httpx.Response(200, json=completion())

    async def run():
        with pytest.raises(HTTPException) as exc:
            await service.ensure_map(OWNER, model_source=semantic_source(handler))
        assert exc.value.status_code == 409
        assert store.saved == [] and store.current is None

    asyncio.run(run())


def test_overlapping_semantic_readers_share_one_acquisition_and_detached_results(monkeypatch):
    store = OwnedStore()
    setup_store(monkeypatch, store)
    acquired = []

    async def handler(request):
        acquired.append(request)
        await asyncio.sleep(0)
        return httpx.Response(200, json=completion())

    source = semantic_source(handler)

    async def run():
        first, second = await asyncio.gather(service.ensure_map(OWNER, model_source=source),
            service.ensure_map(OWNER, model_source=source))
        assert first == second and len(acquired) == len(store.saved) == 1
        first['meta']['nodes'][0]['title'] = 'caller local edit'
        assert second['meta']['nodes'][0]['title'] != first['meta']['nodes'][0]['title']
        assert store.current['content_json']['watashiMap']['nodes'][0]['title'] != first['meta']['nodes'][0]['title']

    asyncio.run(run())


def test_authenticated_latest_and_detail_negotiate_actual_semantic_wire(monkeypatch):
    import api_self_structure as latest
    import api_self_structure_reports as reports
    store = OwnedStore()
    setup_store(monkeypatch, store)
    monkeypatch.setenv('COCOLON_ANALYSIS_OBSERVED_MODE', 'development')
    monkeypatch.setattr(latest, '_resolve_user_id_from_token', AsyncMock(return_value=OWNER))
    monkeypatch.setattr(reports, '_require_user_id', AsyncMock(return_value=OWNER))
    acquired = []

    def handler(request):
        acquired.append(request)
        return httpx.Response(200, json=completion())

    source = semantic_source(handler)
    monkeypatch.setattr(sources, 'application_analysis_model_source', lambda: source)
    app = FastAPI()
    latest.register_self_structure_routes(app)
    reports.register_self_structure_report_routes(app)

    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url='http://synthetic') as client:
            denied = await client.get('/self-structure/latest')
            assert denied.status_code == 401 and acquired == []
            headers = {'Authorization': 'Bearer synthetic', 'X-Watashi-Map-Renderer': 'semantic.v1'}
            created = await client.get('/self-structure/latest', headers=headers)
            assert created.status_code == 200, created.text
            body = created.json()
            assert body['meta']['wire_kind'] == 'watashi.map.v3'
            old = await client.get('/self-structure/latest?ensure=false',
                headers={'Authorization': 'Bearer synthetic'})
            assert old.status_code == 200 and old.json()['meta']['wire_kind'] == 'watashi.map.v2'
            path = '/self-structure/reports/' + body['report_id']
            new_detail = await client.get(path, headers=headers)
            assert new_detail.status_code == 200, new_detail.text
            assert new_detail.json()['item']['content_json']['watashiMap'] == body['meta']
            old_detail = await client.get(path, headers={'Authorization': 'Bearer synthetic'})
            assert old_detail.status_code == 200, old_detail.text
            assert old_detail.json()['item']['content_json']['watashiMap'] == old.json()['meta']
            assert len(acquired) == len(store.saved) == 1
            assert 'source_envelope_id' not in created.text + new_detail.text
            assert 'synthetic-private-key' not in created.text + new_detail.text

    asyncio.run(run())


def test_semantic_actual_isolated_sql_save_evidence_non_generating_reads_and_immutable_month(sql_source):
    """Actual migrations/RPC/JSON storage; HTTP model result remains synthetic."""
    db, _ = sql_source
    migration = Path(__file__).parents[2] / 'supabase/migrations/20261107071033_analysis_semantic_map_wire.sql'
    db.proc.stdin.write(json.dumps({'script': True, 'sql': migration.read_text()}) + '\n')
    db.proc.stdin.flush()
    assert 'code' not in json.loads(db.proc.stdout.readline())
    snapshot = sample()
    assert 'code' not in db.query('insert into auth.users values ($1)', [OWNER])
    assert 'code' not in db.query("insert into public.profiles values ($1,'free')", [OWNER])
    for member in snapshot['members']:
        original = member['original']
        assert 'code' not in db.query('insert into public.emotions values ($1,$2,$3,$4,$5,$6,$7,$8)',
            [original['id'], OWNER, original['created_at'], original['memo'], original['memo_action'],
             original['category'], original['emotions'], json.dumps(original['emotion_details'])])
    acquired = []

    def handler(request):
        material = json.loads(json.loads(request.content)['messages'][1]['content'])
        assert len(material['records']) == 2 and len(material['fields']) == 3
        acquired.append(material)
        return httpx.Response(200, json=completion())

    source = semantic_source(handler)

    async def run():
        first = await service.ensure_map(OWNER, model_source=source)
        assert first['refreshed'] and first['meta']['wire_kind'] == 'watashi.map.v3'
        first_private = db.query('select private_evidence from public.analysis_observed_artifacts where id=$1',
            [first['report_id']])['rows'][0]['private_evidence']
        assert len(first_private['source_members']) == 2
        assert first_private['coverage'] == first['map_context']
        assert first_private['graph']['nodes'][1]['record_refs'] == [snapshot['members'][1]['original']['id']]
        assert first_private['graph']['nodes'][1]['evidence_refs']
        # The additive migration admits only the matching public/private pair.
        def mismatched_insert(number, *, private_schema=None, wire_kind=None):
            new_id = str(UUID(int=number))
            artifact_id = 'artifact:' + UUID(new_id).hex
            private, projection = deepcopy(first_private), deepcopy(first['meta'])
            private['projection_of'] = projection['projection_of'] = artifact_id + '@1'
            if private_schema:
                private['schema_version'] = private_schema
            if wire_kind:
                projection['wire_kind'] = wire_kind
            return db.query('insert into public.analysis_observed_artifacts('
                'id,artifact_id,artifact_version,user_id,report_type,report_mode,access_tier,'
                'period_start,period_end,source_guard,private_evidence,safe_projection,content_text,source_profile) '
                'select $1::uuid,$2,artifact_version,user_id,report_type,report_mode,access_tier,'
                'period_start,period_end,source_guard,$3::jsonb,$4::jsonb,content_text,source_profile '
                'from public.analysis_observed_artifacts where id=$5',
                [new_id, artifact_id, json.dumps(private), json.dumps(projection), first['report_id']])
        wrong_private = mismatched_insert(8001, private_schema='analysis.private-evidence.v1')
        assert wrong_private.get('code') == '23514'
        wrong_wire = mismatched_insert(8002, wire_kind='watashi.map.v2')
        assert wrong_wire.get('code') == '23514'
        unchanged = db.query('select private_evidence,safe_projection from public.analysis_observed_artifacts where id=$1',
            [first['report_id']])['rows'][0]
        assert unchanged['private_evidence'] == first_private and unchanged['safe_projection'] == first['meta']
        current = await service.ensure_map(OWNER, model_source=source)
        monthly = await service.ensure_map(OWNER, monthly=True, force=True, model_source=source)
        readonly = await service.ensure_map(OWNER, ensure=False, force=True, model_source=source)
        detail = (await service.read_maps(OWNER, report_id=first['report_id']))['items'][0]
        for value in (current, monthly, readonly):
            assert not value['refreshed'] and value['report_id'] == first['report_id']
            assert value['meta'] == first['meta'] and value['content_text'] == first['content_text']
        assert detail['content_json']['watashiMap'] == first['meta']
        assert len(acquired) == 1
        evidence = await service.map_evidence(OWNER, first['report_id'], 'n2', month=monthly['snapshot_month'])
        assert len(evidence['items']) == 1
        item = evidence['items'][0]
        original = snapshot['members'][1]['original']
        assert item['id'] == original['id'] and item['memo'] == original['memo']
        assert item['memo_action'] == original['memo_action'] and item['version_state'] == 'CURRENT'
        assert item['answers'] == [] and len(acquired) == 1
        # Explicit current regeneration must not overwrite the saved monthly map.
        second = await service.ensure_map(OWNER, force=True, model_source=source)
        assert second['refreshed'] and second['report_id'] != first['report_id']
        assert len(acquired) == 2
        month_after = await service.ensure_map(OWNER, monthly=True, force=True, model_source=source)
        assert month_after['report_id'] == monthly['report_id']
        assert month_after['meta'] == monthly['meta'] and month_after['content_text'] == monthly['content_text']
        assert month_after['captured_at'] == monthly['captured_at'] and len(acquired) == 2
        assert db.query('select count(*) as n from public.analysis_cumulative_months')['rows'][0]['n'] == 1
        assert db.query('select count(*) as n from public.analysis_observed_artifacts')['rows'][0]['n'] == 2

    asyncio.run(run())


def test_background_latest_responds_without_generating_and_status_never_requeues(monkeypatch):
    import api_self_structure as latest
    import astor_job_queue as queue
    import supabase_client
    store = OwnedStore()
    setup_store(monkeypatch, store)
    monkeypatch.setenv('COCOLON_ANALYSIS_OBSERVED_MODE', 'development')
    monkeypatch.setenv('ASTOR_WORKER_QUEUE_ENABLED', 'true')
    monkeypatch.setattr(latest, '_resolve_user_id_from_token', AsyncMock(return_value=OWNER))
    provider = AsyncMock(side_effect=AssertionError('background request acquired model'))
    monkeypatch.setattr(sources, 'application_analysis_model_source', provider)
    job_state = {'status': None}
    async def queue_read(path, *, params, **kwargs):
        assert params['user_id'] == 'eq.' + OWNER
        assert params['job_key'] == 'eq.myprofile_latest_refresh:' + OWNER
        return httpx.Response(200, json=[] if job_state['status'] is None else [dict(
            status=job_state['status'], job_type='myprofile_latest_refresh_v1')])
    async def enqueue(**kwargs):
        assert kwargs['payload']['force'] is False
        job_state['status'] = 'queued'
    enqueue_mock = AsyncMock(side_effect=enqueue)
    monkeypatch.setattr(queue, 'enqueue_job', enqueue_mock)
    monkeypatch.setattr(supabase_client, 'sb_get', queue_read)
    app = FastAPI()
    latest.register_self_structure_routes(app)

    async def scenario():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url='http://synthetic') as client:
            headers = {'Authorization': 'Bearer synthetic', 'X-Watashi-Map-Renderer': 'semantic.v1'}
            denied = await client.get('/self-structure/latest?background=true')
            assert denied.status_code == 401 and enqueue_mock.await_count == 0
            first = await client.get('/self-structure/latest?background=true', headers=headers)
            assert first.status_code == 200, first.text
            assert first.json()['has_visible_content'] is False
            assert first.json()['refresh_status'] == 'queued'
            repeated = await client.get('/self-structure/latest?background=true', headers=headers)
            assert repeated.json()['refresh_status'] == 'queued'
            assert enqueue_mock.await_count == 1
            job_state['status'] = 'running'
            running = await client.get('/self-structure/latest/status', headers=headers)
            assert running.status_code == 200 and running.json()['refresh_status'] == 'running'
            job_state['status'] = 'done'  # An empty-material generation has no saved current.
            empty = await client.get('/self-structure/latest/status', headers=headers)
            assert empty.status_code == 200 and empty.json()['refresh_status'] is None
            assert not empty.json()['has_visible_content']
            read_only = await client.get('/self-structure/latest?background=true&ensure=false&force=true', headers=headers)
            assert read_only.status_code == 200 and read_only.json()['refresh_status'] is None
            assert enqueue_mock.await_count == 1
            assert store.saved == []
            provider.assert_not_called()
    asyncio.run(scenario())


def test_background_manual_update_keeps_current_until_worker_commits_and_preserves_sync_default(monkeypatch):
    import api_self_structure as latest
    store = OwnedStore()
    setup_store(monkeypatch, store)
    monkeypatch.setenv('COCOLON_ANALYSIS_OBSERVED_MODE', 'development')
    monkeypatch.setattr(latest, '_resolve_user_id_from_token', AsyncMock(return_value=OWNER))
    acquired = []
    source = semantic_source(lambda request: (acquired.append(request) or httpx.Response(200, json=completion())))
    monkeypatch.setattr(sources, 'application_analysis_model_source', lambda: source)
    pending = AsyncMock(return_value='queued')
    monkeypatch.setattr(service, 'request_map_refresh', pending)
    monkeypatch.setattr(service, 'map_refresh_status', AsyncMock(return_value='queued'))
    app = FastAPI()
    latest.register_self_structure_routes(app)
    async def scenario():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url='http://synthetic') as client:
            headers = {'Authorization': 'Bearer synthetic', 'X-Watashi-Map-Renderer': 'semantic.v1'}
            created = await client.get('/self-structure/latest', headers=headers)
            assert created.status_code == 200 and len(acquired) == len(store.saved) == 1
            pending.assert_not_awaited()
            before = deepcopy(created.json())
            refreshing = await client.get('/self-structure/latest?background=true&force=true', headers=headers)
            body = refreshing.json()
            assert refreshing.status_code == 200 and body['refresh_status'] == 'queued'
            assert body['report_id'] == before['report_id'] and body['meta'] == before['meta']
            assert body['content_text'] == before['content_text']
            pending.assert_awaited_once_with(OWNER, force=True, trigger='manual')
            assert len(acquired) == len(store.saved) == 1
            # Source changes hide the old current rather than returning its previous artifact.
            store.current = None
            hidden = await client.get('/self-structure/latest?background=true&ensure=false', headers=headers)
            assert hidden.status_code == 200 and hidden.json()['has_visible_content'] is False
            assert hidden.json()['meta'] is None and hidden.json()['content_text'] is None
            assert len(acquired) == 1
    asyncio.run(scenario())


def test_background_queue_failure_does_not_hide_authorized_saved_content_or_status(monkeypatch):
    import api_self_structure as latest
    store = OwnedStore()
    setup_store(monkeypatch, store)
    monkeypatch.setenv('COCOLON_ANALYSIS_OBSERVED_MODE', 'development')
    monkeypatch.setattr(latest, '_resolve_user_id_from_token', AsyncMock(return_value=OWNER))
    source = semantic_source(lambda request: httpx.Response(200, json=completion()))
    monkeypatch.setattr(sources, 'application_analysis_model_source', lambda: source)
    unavailable = HTTPException(503, 'SYNTHETIC_PRIVATE_QUEUE_DETAIL')
    reserve = AsyncMock(side_effect=unavailable)
    status = AsyncMock(side_effect=unavailable)
    monkeypatch.setattr(service, 'request_map_refresh', reserve)
    monkeypatch.setattr(service, 'map_refresh_status', status)
    app = FastAPI()
    latest.register_self_structure_routes(app)
    async def scenario():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url='http://synthetic') as client:
            headers = {'Authorization': 'Bearer synthetic', 'X-Watashi-Map-Renderer': 'semantic.v1'}
            created = await client.get('/self-structure/latest', headers=headers)
            assert created.status_code == 200
            before = created.json()
            for query in ('background=true&force=true', 'background=true&ensure=false'):
                saved = await client.get('/self-structure/latest?' + query, headers=headers)
                assert saved.status_code == 200, saved.text
                body = saved.json()
                assert body['refresh_status'] == 'failed' and body['has_visible_content']
                assert body['report_id'] == before['report_id'] and body['meta'] == before['meta']
                assert body['content_text'] == before['content_text']
                assert 'SYNTHETIC_PRIVATE_QUEUE_DETAIL' not in saved.text
            saved_status = await client.get('/self-structure/latest/status', headers=headers)
            assert saved_status.status_code == 200
            assert saved_status.json()['has_visible_content'] is True
            assert saved_status.json()['refresh_status'] == 'failed'
            assert saved_status.json()['version_key'] == before['meta']['projection_of']
            assert 'SYNTHETIC_PRIVATE_QUEUE_DETAIL' not in saved_status.text
            assert len(store.saved) == 1
    asyncio.run(scenario())


@pytest.mark.parametrize('status_path', [False, True])
def test_background_saved_read_guard_failure_is_not_downgraded_to_queue_failure(monkeypatch, status_path):
    import api_self_structure as latest
    monkeypatch.setenv('COCOLON_ANALYSIS_OBSERVED_MODE', 'development')
    monkeypatch.setattr(latest, '_resolve_user_id_from_token', AsyncMock(return_value=OWNER))
    monkeypatch.setattr(service, 'read_maps', AsyncMock(side_effect=HTTPException(409, 'analysis_source_changed')))
    reserve, status = AsyncMock(), AsyncMock()
    monkeypatch.setattr(service, 'request_map_refresh', reserve)
    monkeypatch.setattr(service, 'map_refresh_status', status)
    app = FastAPI()
    latest.register_self_structure_routes(app)
    async def scenario():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url='http://synthetic') as client:
            path = '/self-structure/latest/status' if status_path else '/self-structure/latest?background=true'
            response = await client.get(path, headers={'Authorization': 'Bearer synthetic'})
            assert response.status_code == 409
            assert response.json() == {'detail': 'analysis_source_changed'}
            reserve.assert_not_awaited()
            status.assert_not_awaited()
    asyncio.run(scenario())
