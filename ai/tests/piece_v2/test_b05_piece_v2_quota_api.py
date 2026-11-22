"""Quota HTTP/RPC integration; synthetic Auth/PostgREST, real disposable SQL.

No live credentials, activation or save admission. Native coverage reuses the
unchanged B4 guard/fixtures and applies only the new source-only read function.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
import runpy
from uuid import uuid4

import httpx
import pytest
from fastapi import FastAPI, HTTPException

_B4 = runpy.run_path(str(Path(__file__).with_name('db') / 'test_b04_piece_v2_atomic_transactions.py'))
database = _B4['database']
_QUOTA_READ_SQL = _B4['_ROOT'] / 'supabase/migrations/20261010_005_piece_v2_quota_read.sql'
OWNER, VIEWER = str(_B4['_OWNER']), str(_B4['_VIEWER'])
PRIVATE = 'SYNTHETIC_PRIVATE_BACKEND_DIAGNOSTIC'


@pytest.fixture
def harness(monkeypatch):
    import api_piece_v2 as api
    import supabase_client as shared
    from piece_v2_runtime_control import PIECE_FEATURE_NAMES
    state = {'snapshot': {'subscription_tier': 'free', 'saved_count': 2,
        'server_now': '2026-10-10T00:00:00+00:00'}, 'calls': [], 'handler': None, 'auth': []}
    async def verify(authorization):
        state['auth'].append(authorization)
        if authorization != 'Bearer synthetic-owner':
            raise HTTPException(401, PRIVATE)
        return OWNER
    monkeypatch.setattr(api, '_verify_bearer', verify)
    monkeypatch.setattr(shared, 'SUPABASE_URL', 'https://piece.invalid')
    monkeypatch.setattr(shared, 'SUPABASE_SERVICE_ROLE_KEY', 'synthetic-service-only')
    # Even with retries configured, shared-client POST must not retry.
    monkeypatch.setenv('SUPABASE_HTTP_RETRY_COUNT', '2')
    app = FastAPI(); app.include_router(api.router)
    flags = dict.fromkeys(PIECE_FEATURE_NAMES, False)
    flags['piece_v2_preview_enabled'] = True
    app.state.piece_v2_runtime = {'requested': flags.copy(), 'ready': flags.copy()}
    state['app'] = app
    def upstream(request):
        assert request.method == 'POST'
        assert request.url.path == '/rest/v1/rpc/piece_read_quota_v2'
        assert not request.url.params
        assert request.headers['authorization'] == 'Bearer synthetic-service-only'
        assert request.headers['apikey'] == 'synthetic-service-only'
        assert request.extensions['timeout']['read'] == 8.0
        args = json.loads(request.content)
        assert args == {'p_owner_user_id': OWNER}
        state['calls'].append(args)
        if state['handler']:
            response = state['handler'](args)
            if response is not None:
                return response
        return httpx.Response(200, json=state['snapshot'])
    def call(*, query=None, headers=None, content=None):
        async def run():
            async with httpx.AsyncClient(transport=httpx.MockTransport(upstream)) as backend:
                async def client(): return backend
                monkeypatch.setattr(shared, 'get_async_client', client)
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                        base_url='https://test.invalid') as http:
                    return await http.request('GET', '/emotion/piece/quota', params=query,
                        content=content, headers={'Authorization': 'Bearer synthetic-owner'}
                        if headers is None else headers)
        return asyncio.run(run())
    return call, state


def _error(response, status, code):
    assert response.status_code == status and response.json() == {'code': code}
    assert response.headers['cache-control'] == 'no-store'
    assert PRIVATE not in response.text


@pytest.mark.parametrize('tier,count,limit,remaining,can_save', [
    ('free', 0, 5, 5, True), ('free', 5, 5, 0, False),
    ('plus', 29, 30, 1, True), ('plus', 31, 30, 0, False),
    ('premium', 10000, None, None, True)])
def test_quota_returns_exact_save_contract_with_only_preview_enabled(harness, tier, count, limit, remaining, can_save):
    call, state = harness
    state['snapshot'].update(subscription_tier=tier, saved_count=count)
    response = call()
    assert response.status_code == 200 and response.headers['cache-control'] == 'no-store'
    assert response.json() == {'contract_version': 'piece.quota_consumption.v1',
        'subscription_tier': tier, 'month_key': '2026-10', 'save_limit': limit,
        'saved_count': count, 'remaining_count': remaining, 'can_save': can_save}
    assert len(state['calls']) == 1 and state['auth'] == ['Bearer synthetic-owner']


def test_quota_reads_current_plan_and_usage_on_every_call(harness):
    call, state = harness
    assert call().json()['remaining_count'] == 3
    state['snapshot'].update(subscription_tier='plus', saved_count=6)
    assert call().json()['remaining_count'] == 24
    assert len(state['calls']) == 2 and len(state['auth']) == 2


@pytest.mark.parametrize('headers', [{}, {'Authorization': 'Bearer wrong'},
    [('Authorization', 'Bearer synthetic-owner'), ('Authorization', 'Bearer synthetic-owner')]])
def test_quota_auth_precedes_schema_flags_and_io(harness, headers):
    call, state = harness; state['app'].state.piece_v2_runtime = None
    response = call(query={'owner_user_id': VIEWER}, headers=headers)
    _error(response, 401, 'PIECE_AUTH_REQUIRED')
    assert response.headers['www-authenticate'] == 'Bearer' and state['calls'] == []


@pytest.mark.parametrize('query,content', [({'subscription_tier': 'premium'}, None),
    ({'month_key': '2020-01'}, None), ({'owner_user_id': VIEWER}, None),
    ({'limit': '100'}, None), (None, b'{"count":0}')])
def test_quota_rejects_client_authority_and_body(harness, query, content):
    call, state = harness
    _error(call(query=query, content=content), 400, 'PIECE_REQUEST_INVALID')
    assert state['calls'] == []


def test_quota_default_off_before_request_validation(harness):
    call, state = harness; state['app'].state.piece_v2_runtime = None
    _error(call(query={'invalid': PRIVATE}), 503, 'PIECE_FEATURE_DISABLED')
    assert state['calls'] == []


@pytest.mark.parametrize('failure', ['missing_rpc', 'denied', 'json', 'timeout'])
def test_quota_upstream_failure_is_unavailable_not_zero_or_retried(harness, failure):
    call, state = harness
    def handler(args):
        if failure == 'timeout': raise httpx.ReadTimeout(PRIVATE)
        if failure == 'json': return httpx.Response(200, content=PRIVATE)
        return httpx.Response(404 if failure == 'missing_rpc' else 403, json={'details': PRIVATE})
    state['handler'] = handler
    _error(call(), 503, 'PIECE_TEMPORARILY_UNAVAILABLE')
    assert len(state['calls']) == 1


@pytest.mark.parametrize('field,value', [('subscription_tier', 'unknown'),
    ('subscription_tier', []), ('saved_count', True), ('saved_count', -1),
    ('saved_count', '0'), ('saved_count', 9223372036854775808),
    ('server_now', '2026-10-10T00:00:00'), ('server_now', PRIVATE),
    ('server_now', None), ('private_detail', PRIVATE)])
def test_quota_malformed_snapshot_fails_closed(harness, field, value):
    call, state = harness; state['snapshot'][field] = value
    _error(call(), 503, 'PIECE_TEMPORARILY_UNAVAILABLE')


@pytest.mark.parametrize('snapshot', [{}, [], None])
def test_quota_missing_snapshot_is_not_zero(harness, snapshot):
    call, state = harness; state['snapshot'] = snapshot
    _error(call(), 503, 'PIECE_TEMPORARILY_UNAVAILABLE')


@pytest.mark.parametrize('upstream_error', [False, True])
def test_quota_disabled_during_rpc_withholds_result(harness, upstream_error):
    call, state = harness
    def handler(args):
        state['app'].state.piece_v2_runtime['requested']['piece_v2_preview_enabled'] = False
        if upstream_error: raise httpx.ReadTimeout(PRIVATE)
    state['handler'] = handler
    _error(call(), 503, 'PIECE_FEATURE_DISABLED')
    assert len(state['calls']) == 1
    _error(call(), 503, 'PIECE_FEATURE_DISABLED')
    assert len(state['calls']) == 1


def test_quota_task_cancellation_propagates(harness):
    call, state = harness
    def handler(args): raise asyncio.CancelledError()
    state['handler'] = handler
    with pytest.raises(asyncio.CancelledError): call()


@pytest.mark.parametrize('stamp,month', [
    ('2026-10-31T14:59:59+00:00', '2026-10'), ('2026-10-31T15:00:00Z', '2026-11')])
def test_quota_projects_db_jst_month_not_api_clock(harness, stamp, month):
    call, state = harness; state['snapshot']['server_now'] = stamp
    assert call().json()['month_key'] == month


@pytest.fixture
def quota_database(database):
    conn, pg, url = database
    before = conn.execute("SELECT oid,relacl,relrowsecurity,relforcerowsecurity FROM pg_class WHERE relnamespace='public'::regnamespace AND relkind IN ('r','v') ORDER BY oid").fetchall()
    conn.execute(_QUOTA_READ_SQL.read_text())
    assert conn.execute("SELECT oid,relacl,relrowsecurity,relforcerowsecurity FROM pg_class WHERE relnamespace='public'::regnamespace AND relkind IN ('r','v') ORDER BY oid").fetchall() == before
    assert conn.execute("SELECT rolbypassrls FROM pg_roles WHERE rolname='service_role'").fetchone() == (False,)
    return conn, pg, url


def test_quota_native_save_delete_retains_consumption_and_filters_owner_month(harness, quota_database):
    call, state = harness; conn, _, _ = quota_database
    preview = _B4['_preview'](conn); _B4['_save'](conn, preview)
    _B4['_rpc'](conn, 'piece_delete_v2', _B4['_delete_args'](preview))
    assert conn.execute('SELECT count(*) FROM public.piece_records').fetchone() == (0,)
    assert _B4['_used'](conn) == 1
    for owner, previous in [(VIEWER, False), (OWNER, True)]:
        conn.execute("WITH stamp AS (SELECT clock_timestamp() - CASE WHEN %s THEN interval '2 months' ELSE interval '0' END AS t) INSERT INTO public.piece_quota_consumptions(owner_user_id,piece_id,month_key,subscription_tier_at_consumption,consumed_at,save_idempotency_key_hash) SELECT %s,%s,to_char(t AT TIME ZONE 'Asia/Tokyo','YYYY-MM'),'free',t,%s FROM stamp",
            (previous, owner, uuid4(), uuid4().hex*2))
    def handler(args):
        # The real service-role call, without direct profile/ledger SELECT.
        with conn.transaction():
            conn.execute('SET TRANSACTION READ ONLY')
            return httpx.Response(200, json=_B4['_rpc'](conn, 'piece_read_quota_v2', args))
    state['handler'] = handler
    first = call().json()
    assert first['saved_count'] == 1 and first['remaining_count'] == 4
    for tier, expected, remaining in [('plus', 'plus', 29), (None, 'free', 4), ('unknown', 'free', 4)]:
        conn.execute('UPDATE public.profiles SET subscription_tier=%s WHERE id=%s', (tier, OWNER))
        result = call().json()
        assert result['subscription_tier'] == expected and result['remaining_count'] == remaining
    conn.execute('DELETE FROM public.profiles WHERE id=%s', (OWNER,))
    assert call().json()['remaining_count'] == 4
    assert _B4['_used'](conn) == 3
    assert conn.execute('SELECT count(*) FROM public.piece_records').fetchone() == (0,)
    viewer = _B4['_rpc'](conn, 'piece_read_quota_v2', {'p_owner_user_id': VIEWER})
    assert viewer['saved_count'] == 1
    absent = _B4['_rpc'](conn, 'piece_read_quota_v2', {'p_owner_user_id': str(uuid4())})
    assert absent['saved_count'] == 0 and absent['subscription_tier'] == 'free'


def test_quota_native_execute_boundary_and_no_table_grant(quota_database):
    conn, pg, _ = quota_database
    identity = conn.execute("SELECT prosecdef,provolatile,proconfig,pg_get_userbyid(proowner)=current_user FROM pg_proc WHERE oid='public.piece_read_quota_v2(uuid)'::regprocedure").fetchone()
    assert identity == (True, 's', ['search_path=pg_catalog', 'row_security=off'], True)
    for role in ('anon', 'authenticated'):
        with pytest.raises(pg.errors.InsufficientPrivilege):
            _B4['_rpc'](conn, 'piece_read_quota_v2', {'p_owner_user_id': OWNER}, role=role)
    for table in ('profiles', 'piece_quota_consumptions'):
        with pytest.raises(pg.errors.InsufficientPrivilege):
            with conn.transaction():
                conn.execute('SET LOCAL ROLE service_role')
                conn.execute('SELECT * FROM public.'+table)
    for owner in (None, '00000000-0000-0000-0000-000000000000'):
        with pytest.raises(pg.errors.RaiseException, match='(?m)^PIECE_AUTH_REQUIRED$'):
            _B4['_rpc'](conn, 'piece_read_quota_v2', {'p_owner_user_id': owner})
    with pytest.raises(pg.errors.RaiseException, match='(?m)^PIECE_QUOTA_READ_TARGET_EXISTS$'):
        conn.execute(_QUOTA_READ_SQL.read_text())
