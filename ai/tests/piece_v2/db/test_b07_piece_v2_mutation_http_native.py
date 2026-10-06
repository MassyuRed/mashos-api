"""B7 HTTP -> shared HTTP client -> unchanged B4 disposable native PostgreSQL.

Bearer verification and the PostgREST transport are synthetic. SQL, transactions,
row locks, child purging and receipts are real in the existing B4 isolated fixture.
No live Supabase/Auth, production router, source/safety admission or RN is tested.
"""
from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextvars import ContextVar
import hashlib
import json
from pathlib import Path
import runpy
import time
from uuid import uuid4

import httpx
import pytest
from fastapi import FastAPI, HTTPException

_B4 = runpy.run_path(str(Path(__file__).with_name('test_b04_piece_v2_atomic_transactions.py')))
database = _B4['database']
_B2 = _B4['_B2']
_OWNER, _VIEWER = str(_B4['_OWNER']), str(_B4['_VIEWER'])
_PRIVATE = 'SYNTHETIC_B7_PRIVATE_PROVIDER_DETAIL'
_KEY = 'synthetic-b7-delete'


@pytest.fixture
def harness(monkeypatch, database):
    import api_piece_v2 as api
    import supabase_client as shared
    _, pg, url = database
    state = {'calls': [], 'auth': [], 'lose_ack': False}
    client_context = ContextVar('piece_b7_test_http_client')
    app = FastAPI()
    app.include_router(api.router)

    async def verify(authorization):
        state['auth'].append(authorization)
        if authorization == 'Bearer synthetic-owner':
            return _OWNER
        if authorization == 'Bearer synthetic-viewer':
            return _VIEWER
        raise HTTPException(401, _PRIVATE)

    async def get_client():
        return client_context.get()

    monkeypatch.setattr(api, '_verify_bearer', verify)
    monkeypatch.setattr(shared, 'SUPABASE_URL', 'https://piece.invalid')
    monkeypatch.setattr(shared, 'SUPABASE_SERVICE_ROLE_KEY', 'synthetic-service-only')
    monkeypatch.setattr(shared, 'get_async_client', get_client)

    def execute(name, args):
        with pg.connect(url, autocommit=True, connect_timeout=3,
                        application_name='piece-b7-http-native') as conn:
            conn.execute("SET statement_timeout='8s'")
            try:
                value = _B4['_rpc'](conn, name, args)
            except pg.Error as exc:
                return httpx.Response(400, json={'code': exc.sqlstate,
                    'message': exc.diag.message_primary, 'details': _PRIVATE, 'hint': _PRIVATE})
        if state['lose_ack']:
            raise httpx.ReadTimeout(_PRIVATE)
        return httpx.Response(200, json=value)

    async def upstream(request):
        assert request.method == 'POST'
        name = request.url.path.rsplit('/', 1)[-1]
        assert name in ('piece_set_visibility_v2', 'piece_delete_v2')
        assert str(request.url) == 'https://piece.invalid/rest/v1/rpc/' + name
        assert request.headers['authorization'] == 'Bearer synthetic-service-only'
        assert request.headers['apikey'] == 'synthetic-service-only'
        args = json.loads(request.content)
        expected = {'p_owner_user_id', 'p_piece_id', 'p_expected_row_version'}
        expected.add('p_visibility_scope' if name == 'piece_set_visibility_v2' else 'p_idempotency_key_hash')
        assert set(args) == expected
        state['calls'].append((name, args))
        return await asyncio.to_thread(execute, name, args)

    async def send(op, pid, *, version=2, scope='public', owner='owner', key=_KEY):
        body = {'expected_row_version': version}
        if op == 'visibility':
            body['visibility_scope'] = scope
        method = 'PATCH' if op == 'visibility' else 'DELETE'
        path = '/emotion/piece/' + str(pid) + ('/visibility' if op == 'visibility' else '')
        async with httpx.AsyncClient(transport=httpx.MockTransport(upstream)) as backend:
            token = client_context.set(backend)
            try:
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                             base_url='https://test.invalid') as client:
                    return await client.request(method, path, json=body, headers={
                        'Authorization': 'Bearer synthetic-' + owner, 'Idempotency-Key': key})
            finally:
                client_context.reset(token)

    def call(op, pid, **kwargs):
        return asyncio.run(send(op, pid, **kwargs))

    state['send'] = send
    return call, state


def _saved(database, visibility='private'):
    conn, _, _ = database
    row = _B4['_preview'](conn)
    result = _B4['_save'](conn, row, visibility=visibility)
    assert result['row_version'] == 2
    return row, result


def _row(conn, pid):
    return conn.execute('SELECT to_jsonb(r) FROM public.piece_records r WHERE id=%s', (pid,)).fetchone()[0]


def _error(response, status, code):
    assert response.status_code == status, response.text
    assert response.json() == {'code': code}
    assert response.headers['cache-control'] == 'no-store'
    assert _PRIVATE not in response.text


@pytest.mark.parametrize('scope', ['public', 'private'])
def test_native_visibility_preserves_saved_artifact_and_quota(harness, database, scope):
    call, state = harness
    conn, _, _ = database
    row, saved = _saved(database, 'private' if scope == 'public' else 'public')
    before = _row(conn, row['id'])
    legacy = _B2['_legacy_identity'](conn)
    response = call('visibility', row['id'], scope=' ' + scope + ' ')
    assert response.status_code == 200, response.text
    assert response.json() == {'piece_id': str(row['id']), 'visibility_scope': scope, 'row_version': 3}
    after = _row(conn, row['id'])
    for field in ('piece_text', 'piece_text_hash', 'content_payload', 'content_payload_hash',
                  'visual_recipe', 'visual_recipe_hash', 'source_lineage', 'safety_state', 'saved_at'):
        assert after[field] == before[field]
    assert after['visibility_scope'] == scope and after['row_version'] == 3
    assert _B4['_used'](conn) == 1
    assert conn.execute('SELECT consumption_id::text FROM public.piece_quota_consumptions').fetchone() == (saved['consumption_id'],)
    assert _B2['_legacy_identity'](conn) == legacy
    assert len(state['calls']) == 1


@pytest.mark.parametrize('op', ['visibility', 'delete'])
def test_native_other_owner_and_missing_are_concealed(harness, database, op):
    call, state = harness
    conn, _, _ = database
    row, _ = _saved(database)
    before = _row(conn, row['id'])
    other = call(op, row['id'], owner='viewer')
    missing = call(op, uuid4(), owner='viewer')
    _error(other, 404, 'PIECE_NOT_FOUND')
    _error(missing, 404, 'PIECE_NOT_FOUND')
    assert other.content == missing.content
    assert _row(conn, row['id']) == before
    assert _B4['_used'](conn) == 1
    assert len(state['calls']) == 2


@pytest.mark.parametrize('op', ['visibility', 'delete'])
def test_native_stale_version_has_no_effect(harness, database, op):
    call, _ = harness
    conn, _, _ = database
    row, _ = _saved(database)
    before = _row(conn, row['id'])
    _error(call(op, row['id'], version=1), 409, 'PIECE_CONFLICT')
    assert _row(conn, row['id']) == before
    assert conn.execute('SELECT count(*) FROM public.piece_delete_receipts').fetchone() == (0,)
    assert _B4['_used'](conn) == 1


def test_native_delete_purges_children_and_replays_persisted_receipt(harness, database):
    call, state = harness
    conn, _, _ = database
    row, saved = _saved(database)
    legacy = _B2['_legacy_identity'](conn)
    _B2['_insert'](conn, 'piece_record_metrics', dict(piece_id=row['id']))
    _B2['_insert'](conn, 'piece_record_reads', dict(piece_id=row['id'], viewer_user_id=_B4['_VIEWER']))
    _B2['_insert'](conn, 'piece_record_resonances', dict(piece_id=row['id'], owner_user_id=_B4['_OWNER'], viewer_user_id=_B4['_VIEWER']))
    _B2['_insert'](conn, 'piece_export_receipts', dict(owner_user_id=_B4['_OWNER'], piece_id=row['id'],
        idempotency_key_hash='f'*64, piece_text_hash=row['piece_text_hash'], visual_recipe_hash=row['visual_recipe_hash'], outcome='succeeded'))
    first = call('delete', row['id'])
    assert first.status_code == 200, first.text
    assert first.json()['idempotency_replayed'] is False
    second = call('delete', row['id'])
    assert second.status_code == 200, second.text
    assert second.json() == dict(first.json(), idempotency_replayed=True)
    for table in ('piece_records', 'piece_record_metrics', 'piece_record_reads', 'piece_record_resonances'):
        assert conn.execute('SELECT count(*) FROM public.' + table).fetchone() == (0,)
    for table in ('piece_delete_receipts', 'piece_export_receipts'):
        assert conn.execute('SELECT count(*) FROM public.' + table).fetchone() == (1,)
    assert conn.execute('SELECT receipt_id::text FROM public.piece_delete_receipts').fetchone() == (first.json()['receipt_id'],)
    assert conn.execute('SELECT consumption_id::text FROM public.piece_quota_consumptions').fetchone() == (saved['consumption_id'],)
    assert _B4['_used'](conn) == 1
    assert _B2['_legacy_identity'](conn) == legacy
    assert state['calls'][0] == state['calls'][1]
    assert state['calls'][0][1]['p_idempotency_key_hash'] == hashlib.sha256(_KEY.encode()).hexdigest()
    _error(call('visibility', row['id']), 404, 'PIECE_NOT_FOUND')


def test_native_delete_lost_ack_has_no_retry_and_same_key_recovers(harness, database):
    call, state = harness
    conn, _, _ = database
    row, _ = _saved(database)
    state['lose_ack'] = True
    _error(call('delete', row['id']), 503, 'PIECE_TEMPORARILY_UNAVAILABLE')
    assert len(state['calls']) == 1
    assert conn.execute('SELECT count(*) FROM public.piece_records').fetchone() == (0,)
    receipt = conn.execute('SELECT receipt_id::text FROM public.piece_delete_receipts').fetchone()[0]
    state['lose_ack'] = False
    recovered = call('delete', row['id'])
    assert recovered.status_code == 200, recovered.text
    assert recovered.json()['receipt_id'] == receipt
    assert recovered.json()['idempotency_replayed'] is True
    assert len(state['calls']) == 2 and _B4['_used'](conn) == 1


@pytest.mark.parametrize('op', ['visibility', 'delete'])
def test_native_concurrent_same_version_requests(harness, database, op):
    _, state = harness
    conn, _, _ = database
    row, _ = _saved(database)
    async def run():
        return await asyncio.gather(state['send'](op, row['id']), state['send'](op, row['id']))
    results = asyncio.run(run())
    if op == 'visibility':
        assert sorted(r.status_code for r in results) == [200, 409]
        assert _row(conn, row['id'])['row_version'] == 3
        _error(next(r for r in results if r.status_code == 409), 409, 'PIECE_CONFLICT')
    else:
        assert [r.status_code for r in results] == [200, 200]
        assert results[0].json()['receipt_id'] == results[1].json()['receipt_id']
        assert sorted(r.json()['idempotency_replayed'] for r in results) == [False, True]
        assert conn.execute('SELECT count(*) FROM public.piece_delete_receipts').fetchone() == (1,)
    assert len(state['calls']) == 2 and _B4['_used'](conn) == 1


@pytest.mark.parametrize('op', ['visibility', 'delete'])
def test_native_http_rechecks_version_after_real_row_lock_wait(harness, database, op):
    call, _ = harness
    conn, pg, url = database
    row, _ = _saved(database)
    with pg.connect(url, autocommit=False, connect_timeout=3) as holder:
        holder.execute('SELECT id FROM public.piece_records WHERE id=%s FOR UPDATE', (row['id'],))
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(call, op, row['id'])
            try:
                deadline = time.monotonic() + 5
                while time.monotonic() < deadline:
                    waiting = conn.execute("SELECT count(*) FROM pg_stat_activity WHERE datname=current_database() AND application_name='piece-b7-http-native' AND %s=ANY(pg_blocking_pids(pid))", (holder.info.backend_pid,)).fetchone()[0]
                    if waiting:
                        break
                    time.sleep(0.01)
                else:
                    pytest.fail('B7_HTTP_DID_NOT_WAIT_ON_ROW_LOCK')
                assert not future.done()
                holder.execute("UPDATE public.piece_records SET visibility_scope='public',row_version=3 WHERE id=%s", (row['id'],))
            finally:
                holder.commit()
            _error(future.result(timeout=10), 409, 'PIECE_CONFLICT')
    assert _row(conn, row['id'])['row_version'] == 3
    assert conn.execute('SELECT count(*) FROM public.piece_delete_receipts').fetchone() == (0,)
    assert _B4['_used'](conn) == 1


def test_native_delete_failure_rolls_back_and_hides_provider_detail(harness, database):
    call, state = harness
    conn, _, _ = database
    row, _ = _saved(database)
    conn.execute("CREATE FUNCTION public.synthetic_b7_fail() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'SYNTHETIC_B7_PRIVATE_PROVIDER_DETAIL'; END $$")
    conn.execute('CREATE TRIGGER synthetic_b7_fail BEFORE DELETE ON public.piece_records FOR EACH ROW EXECUTE FUNCTION public.synthetic_b7_fail()')
    _error(call('delete', row['id']), 503, 'PIECE_TEMPORARILY_UNAVAILABLE')
    assert len(state['calls']) == 1
    assert _row(conn, row['id'])['row_version'] == 2
    assert conn.execute('SELECT count(*) FROM public.piece_delete_receipts').fetchone() == (0,)
    assert _B4['_used'](conn) == 1
