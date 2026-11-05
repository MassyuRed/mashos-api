"""Explicit source lifecycle; all responses here are independently synthetic."""
import asyncio
from dataclasses import replace
import json
import os
from pathlib import Path
from unittest.mock import AsyncMock, patch
from uuid import UUID

from fastapi import HTTPException
import pytest

import analysis_cumulative_service as service
from test_analysis_cumulative import OWNER, source_snapshot
from test_analysis_model_observed_roles import material
from test_analysis_model_quoted_parent_units import call


def synthetic_response(prepared):
    fields = json.loads(prepared.messages()[1]['content'])['fields']
    packet = dict(fields=[dict(field=f['field'], units=[dict(quote=text,
        node_kind='ROLE' if 'の役割は' in text else 'ACTION_OR_NONACTION',
        parent_quote=None, scope_role=None, qualifiers=[])
        for text in f['text'].rstrip('。').split('。')]) for f in fields])
    return call(prepared, packet).response


def run(awaitable):
    return asyncio.run(awaitable)


@pytest.mark.parametrize('defect', ['request', 'messages', 'raw', 'hash', 'finish',
    'missing', 'wrong_type', 'invalid_json', 'source_failure', 'stale_clock', 'foreign_owner'])
def test_bad_response_is_not_saved_or_replaced_with_finite_output(monkeypatch, defect):
    snap = material('pair')
    prepared = service.prepare_cumulative_category_units(OWNER, snap, prompt_version='selected_material.v4')
    response = synthetic_response(prepared)
    if defect == 'request': response = replace(response, request_ref='foreign')
    if defect == 'messages': response = replace(response, messages_sha256='0'*64)
    if defect == 'raw': response = replace(response, raw=response.raw+' ')
    if defect == 'hash': response = replace(response, raw_sha256='0'*64)
    if defect == 'finish': response = replace(response, finish_reason='length')
    if defect == 'missing': response = None
    if defect == 'wrong_type': response = prepared
    if defect == 'invalid_json': response = call(prepared, raw='{"fields":NaN}').response
    if defect == 'stale_clock': snap = dict(snap, now='2026-11-01T08:00:01+00:00', period_end='2026-11-01T08:00:01+00:00')
    if defect == 'foreign_owner':
        other = service.prepare_cumulative_category_units(str(UUID(int=2)), snap, prompt_version='selected_material.v4')
        response = synthetic_response(other)
    source = AsyncMock(side_effect=ValueError('unavailable')) if defect == 'source_failure' else AsyncMock(return_value=response)
    async def rpc(name, payload):
        if name == 'analysis_cumulative_read':
            return dict(items=[], subscription_tier='free', matched=True, history_limit=2)
        assert name == 'analysis_cumulative_source_snapshot', 'invalid response reached commit'
        return snap
    monkeypatch.setattr(service, '_rpc', rpc)
    monkeypatch.setattr(service, 'observed_mode', lambda:'development')
    with pytest.raises(HTTPException) as error:
        run(service.ensure_map(OWNER, model_source=source))
    assert error.value.status_code == 422
    source.assert_awaited_once()


@pytest.mark.parametrize('scope', ['empty', 'multiple', 'safety'])
def test_unqualified_source_does_not_acquire_a_response(monkeypatch, scope):
    snap = source_snapshot(0 if scope == 'empty' else 2 if scope == 'multiple' else 1)
    if scope == 'safety': snap['members'][0]['original']['memo'] = '死にたい。'
    source = AsyncMock(side_effect=AssertionError('unqualified source acquisition'))
    monkeypatch.setattr(service, 'read_maps', AsyncMock(return_value={'items':[]}))
    monkeypatch.setattr(service, '_rpc', AsyncMock(return_value=snap))
    monkeypatch.setattr(service, 'observed_mode', lambda:'development')
    with pytest.raises(HTTPException) as error:
        run(service.ensure_map(OWNER, model_source=source))
    assert error.value.status_code == 422
    source.assert_not_awaited()


@pytest.mark.parametrize('ensure,mode', [(False,'development'), (True,'read_only'), (True,'off')])
def test_read_only_routes_never_acquire_a_response(monkeypatch, ensure, mode):
    source = AsyncMock(side_effect=AssertionError('read generated'))
    monkeypatch.setattr(service, 'read_maps', AsyncMock(return_value={'items':[]}))
    monkeypatch.setattr(service, '_rpc', AsyncMock(side_effect=AssertionError('read wrote')))
    monkeypatch.setattr(service, 'observed_mode', lambda:mode)
    assert not run(service.ensure_map(OWNER, ensure=ensure, model_source=source))['has_visible_content']
    source.assert_not_awaited()


@pytest.fixture
def sql_source(monkeypatch):
    if not os.environ.get('Q2_PGLITE_MODULE'):
        pytest.skip('PostgreSQL WASM dependency is not configured')
    from test_emlis_q3_application import Q3Database
    db = Q3Database()
    try:
        db.migrate()
        for name in ('20261003134440_analysis_observed_artifacts.sql', '20261004041627_analysis_period_comparison.sql',
                     '20261101080144_cumulative_watashi_map.sql'):
            db.proc.stdin.write(json.dumps({'script':True, 'sql':(Path(__file__).parents[2]/'supabase/migrations'/name).read_text()})+'\n')
            db.proc.stdin.flush()
            assert 'code' not in json.loads(db.proc.stdout.readline())
        async def rpc(name, payload):
            args = ','.join(f'{key} => ${i}' for i,key in enumerate(payload,1))
            params = [json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for v in payload.values()]
            result = await asyncio.to_thread(db.query, f'select public.{name}({args}) as value', params, 'service_role')
            if 'code' in result: raise HTTPException(409, result['code'])
            return result['rows'][0]['value']
        monkeypatch.setattr(service, '_rpc', rpc)
        monkeypatch.setattr(service, 'observed_mode', lambda:'development')
        yield db, rpc
    finally:
        db.proc.stdin.close()
        db.proc.wait(timeout=10)


def insert_material(db, mode):
    original = material(mode)['members'][0]['original']
    assert 'code' not in db.query('insert into auth.users values ($1)', [OWNER])
    assert 'code' not in db.query("insert into public.profiles values ($1,'free')", [OWNER])
    assert 'code' not in db.query('insert into public.emotions values ($1,$2,$3,$4,$5,$6,$7,$8)',
        [original['id'], OWNER, original['created_at'], original['memo'], original['memo_action'],
         original['category'], original['emotions'], json.dumps(original['emotion_details'])])
    return original


@pytest.mark.parametrize('mode', ['role', 'pair', 'clause'])
def test_real_sql_fresh_source_normal_commit_and_immutable_month(sql_source, monkeypatch, mode):
    db, rpc = sql_source
    original = insert_material(db, mode)
    earlier = run(rpc('analysis_cumulative_source_snapshot', {'p_user_id':OWNER}))
    stale = service.prepare_cumulative_category_units(OWNER, earlier, prompt_version='selected_material.v4')
    received = []
    async def source(prepared):
        assert prepared.response is None and prepared.prompt_version == 'selected_material.v4'
        assert prepared.source_guard == earlier['guard']
        assert prepared.request_ref != stale.request_ref
        received.append(prepared)
        return synthetic_response(prepared)
    first = run(service.ensure_map(OWNER, model_source=source))
    assert first['has_visible_content'] and first['refreshed'] and len(received) == 1
    assert '受付係' in first['content_text'] and '記録された役割' in first['content_text']
    assert len(first['meta']['nodes']) == (2 if mode == 'pair' else 1)
    assert first['map_context']['unparsed_count'] == int(mode == 'clause')
    if mode == 'clause': assert '費用を記録' not in first['content_text']
    raw = db.query('select private_evidence from public.analysis_observed_artifacts where id=$1', [first['report_id']])['rows'][0]['private_evidence']
    assert raw['source_record_refs'] == [original['id']]
    assert raw['coverage'] == first['map_context']
    assert 'raw_sha256' not in json.dumps(raw)
    # Actual read validators and SQL run; only generation and source are forbidden.
    forbidden = AsyncMock(side_effect=AssertionError('saved read acquired a response'))
    with patch.object(service, 'build_cumulative_map', side_effect=AssertionError('saved read generated')):
        current = run(service.ensure_map(OWNER, model_source=forbidden))
        monthly = run(service.ensure_map(OWNER, monthly=True, force=True, model_source=forbidden))
        readonly = run(service.ensure_map(OWNER, ensure=False, force=True, model_source=forbidden))
        detail = run(service.read_maps(OWNER, report_id=first['report_id']))['items'][0]
    forbidden.assert_not_awaited()
    for value in (current,monthly,readonly):
        assert value['meta'] == first['meta'] and value['content_text'] == first['content_text']
        assert value['report_id'] == first['report_id'] and not value['refreshed']
    assert detail['content_json']['watashiMap'] == first['meta']
    evidence = run(service.map_evidence(OWNER, first['report_id'], first['meta']['nodes'][0]['node_ref'], month=monthly['snapshot_month']))
    assert evidence['items'] and all(x['version_state'] == 'CURRENT' for x in evidence['items'])
    # A later valid rebuild updates current, but never rewrites this month's capture.
    db.query("update public.emotions set memo=replace(memo,'だった','ではなかった') where id=$1", [original['id']])
    async def updated(prepared): return synthetic_response(prepared)
    second = run(service.ensure_map(OWNER, force=True, model_source=updated))
    assert second['refreshed'] and second['report_id'] != first['report_id']
    assert second['content_text'] != first['content_text']
    history = run(service.ensure_map(OWNER, monthly=True, force=True, model_source=forbidden))
    assert history['meta'] == monthly['meta'] and history['content_text'] == monthly['content_text']
    assert history['captured_at'] == monthly['captured_at']
    forbidden.assert_not_awaited()


def test_real_sql_source_edit_during_response_rejects_commit(sql_source):
    db, _ = sql_source
    original = insert_material(db, 'pair')
    calls = []
    async def source(prepared):
        response = synthetic_response(prepared)
        calls.append(prepared.request_ref)
        db.query("update public.emotions set memo=memo || '変更。' where id=$1", [original['id']])
        return response
    with pytest.raises(HTTPException) as error:
        run(service.ensure_map(OWNER, model_source=source))
    assert error.value.status_code == 409 and error.value.detail == '40001'
    assert len(calls) == 1
    assert db.query('select count(*) as n from public.analysis_observed_artifacts')['rows'][0]['n'] == 0
    assert db.query('select count(*) as n from public.analysis_cumulative_months')['rows'][0]['n'] == 0


def test_real_sql_saved_supplement_does_not_acquire_a_response(sql_source, monkeypatch):
    db, _ = sql_source
    original = insert_material(db, 'pair')
    import emlis_thread_store
    from emlis_thread_service import EmlisThreadService, Q3_PROFILE
    from test_emlis_q3_application import answer
    monkeypatch.setattr(emlis_thread_store, 'sb_post_rpc', db.rpc)
    db.query("update public.emotions set memo=$2,memo_action='',created_at=(now()-interval '1 day') at time zone 'UTC',emotions=array['不安'],emotion_details=$3 where id=$1",
        [original['id'], '褒められたのに、嬉しくなかった。', json.dumps([dict(type='不安',strength='medium')])])
    emlis = EmlisThreadService(runtime_profile=Q3_PROFILE)
    dto = run(emlis.start(OWNER, original['id']))
    assert dto.get('pending_question') is not None
    run(answer(emlis, OWNER, dto, 'その時は重かった。', 'analysis-supplement'))
    source = AsyncMock(side_effect=AssertionError('supplement response acquired'))
    with pytest.raises(HTTPException) as error:
        run(service.ensure_map(OWNER, model_source=source))
    assert error.value.status_code == 422
    source.assert_not_awaited()
