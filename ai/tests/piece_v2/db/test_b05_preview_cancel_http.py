"""B5 cancellation HTTP integration; distinct from the blocked issuance tests.

ASGI and the actual shared HTTP client/JSON encoding are exercised. The auth
verifier is synthetic; HTTPX MockTransport simulates the PostgREST envelope and
executes the unchanged cancellation SQL on B4's disposable native PostgreSQL.
No real auth server, deployed API, preview safety admission or device is claimed.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
import runpy
from uuid import UUID, uuid4

import httpx
import pytest
from fastapi import FastAPI, HTTPException

_B5 = runpy.run_path(str(Path(__file__).with_name('test_b05_preview_persistence.py')))
database = _B5['database']
_B4 = _B5['_B4']
_OWNER, _VIEWER = str(_B5['_OWNER']), str(_B5['_VIEWER'])
_PID = '10000000-0000-4000-8000-000000000001'
_PRIVATE = 'SYNTHETIC_PRIVATE_PROVIDER_TEXT'


def _result(pid=_PID):
    return {'preview_id': pid, 'preview_revision': 1, 'row_version': 2,
            'lifecycle_status': 'cancelled', 'idempotency_replayed': False}


def _error(response, status, code):
    assert response.status_code == status
    assert response.json() == {'code': code}
    assert response.headers['cache-control'] == 'no-store'
    assert _PRIVATE not in response.text


@pytest.fixture
def harness(monkeypatch):
    import api_piece_v2 as api
    import supabase_client as shared
    app = FastAPI()
    app.include_router(api.router)
    state = {'calls': [], 'auth': [], 'handler': None, 'verified': _OWNER, 'auth_error': None}

    async def verify(authorization):
        state['auth'].append(authorization)
        if state['auth_error'] is not None:
            raise state['auth_error']
        if authorization not in ('Bearer synthetic-owner', 'Bearer synthetic-viewer'):
            raise HTTPException(401, _PRIVATE)
        return _VIEWER if authorization.endswith('viewer') else state['verified']

    monkeypatch.setattr(api, '_verify_bearer', verify)
    monkeypatch.setattr(shared, 'SUPABASE_URL', 'https://piece.invalid')
    monkeypatch.setattr(shared, 'SUPABASE_SERVICE_ROLE_KEY', 'synthetic-service-only')

    def upstream(request):
        assert request.method == 'POST'
        assert request.url == 'https://piece.invalid/rest/v1/rpc/piece_cancel_preview_v2'
        assert request.headers['authorization'] == 'Bearer synthetic-service-only'
        assert request.headers['apikey'] == 'synthetic-service-only'
        args = json.loads(request.content)
        assert set(args) == {'p_owner_user_id', 'p_preview_id', 'p_expected_preview_revision'}
        state['calls'].append(args)
        handler = state['handler']
        return handler(args) if handler is not None else httpx.Response(200, json=_result())

    def call(pid=_PID, body=None, headers=None, content=None, query='', method='DELETE'):
        async def run():
            async with httpx.AsyncClient(transport=httpx.MockTransport(upstream)) as backend:
                async def get_client():
                    return backend
                monkeypatch.setattr(shared, 'get_async_client', get_client)
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                             base_url='https://test.invalid') as client:
                    kwargs = {'headers': {'Authorization': 'Bearer synthetic-owner'} if headers is None else headers}
                    if content is not None:
                        kwargs['content'] = content
                    else:
                        kwargs['json'] = {'expected_preview_revision': 1} if body is None else body
                    return await client.request(method, '/emotion/piece/preview/' + pid + query, **kwargs)
        return asyncio.run(run())

    return call, state


def _connect_native(state, database, *, lose_ack=False):
    conn, pg, _ = database
    def handler(args):
        try:
            value = _B4['_rpc'](conn, 'piece_cancel_preview_v2', args)
        except pg.Error as exc:
            return httpx.Response(400, json={'code': exc.sqlstate,
                'message': exc.diag.message_primary, 'details': _PRIVATE, 'hint': _PRIVATE})
        if lose_ack:
            raise httpx.ReadTimeout(_PRIVATE)
        return httpx.Response(200, json=value)
    state['handler'] = handler


def test_cancel_http_uses_verified_owner_and_only_revision(harness):
    call, state = harness
    response = call()
    assert response.status_code == 200 and response.json() == _result()
    assert response.headers['cache-control'] == 'no-store'
    assert state['auth'] == ['Bearer synthetic-owner']
    assert state['calls'] == [{'p_owner_user_id': _OWNER, 'p_preview_id': _PID,
                              'p_expected_preview_revision': 1}]


@pytest.mark.parametrize('headers', [{}, {'Authorization': ''}, {'Authorization': 'Basic synthetic'},
    {'Authorization': 'Bearer'}, {'Authorization': 'Bearer too many'},
    [('Authorization', 'Bearer synthetic-owner'), ('Authorization', 'Bearer synthetic-viewer')]])
def test_cancel_http_rejects_missing_or_ambiguous_auth_before_read(harness, headers):
    call, state = harness
    response = call(headers=headers, content=b'not-json ' + _PRIVATE.encode())
    _error(response, 401, 'PIECE_AUTH_REQUIRED')
    assert response.headers['www-authenticate'] == 'Bearer'
    assert state['auth'] == state['calls'] == []


@pytest.mark.parametrize('verified', ['', 'not-a-user', str(UUID(int=0)), 1, None])
def test_cancel_http_rejects_invalid_verified_identity(harness, verified):
    call, state = harness
    state['verified'] = verified
    _error(call(), 401, 'PIECE_AUTH_REQUIRED')
    assert state['calls'] == []


@pytest.mark.parametrize('status,expected', [(401, 401), (403, 401), (500, 503)])
def test_cancel_http_sanitizes_auth_failure(harness, status, expected):
    call, state = harness
    state['auth_error'] = HTTPException(status, _PRIVATE)
    _error(call(), expected, 'PIECE_AUTH_REQUIRED' if expected == 401 else 'PIECE_TEMPORARILY_UNAVAILABLE')
    assert state['calls'] == []


@pytest.mark.parametrize('body', [[], {}, {'user_id': _VIEWER, 'expected_preview_revision': 1},
    {'expected_preview_revision': 1, 'piece_text': _PRIVATE}, {'expected_preview_revision': True},
    {'expected_preview_revision': 0}, {'expected_preview_revision': -1},
    {'expected_preview_revision': 1.0}, {'expected_preview_revision': '1'},
    {'expected_preview_revision': 2**63}, {'expected_preview_revision': None}])
def test_cancel_http_invalid_request_has_no_rpc(harness, body):
    call, state = harness
    _error(call(body=body), 400, 'PIECE_REQUEST_INVALID')
    assert state['calls'] == []


@pytest.mark.parametrize('content', [b'null', b'{', b'"SYNTHETIC_PRIVATE_PROVIDER_TEXT"', b'\xff'])
def test_cancel_http_invalid_json_never_echoes_input(harness, content):
    call, state = harness
    _error(call(content=content), 400, 'PIECE_REQUEST_INVALID')
    assert state['calls'] == []


@pytest.mark.parametrize('pid,query', [('invalid-uuid', ''), (_PID, '?user_id=synthetic-other')])
def test_cancel_http_rejects_bad_path_and_query(harness, pid, query):
    call, state = harness
    _error(call(pid=pid, query=query), 400, 'PIECE_REQUEST_INVALID')
    assert state['calls'] == []


@pytest.mark.parametrize('code,status', [('PIECE_REQUEST_INVALID', 400), ('PIECE_AUTH_REQUIRED', 401),
    ('PIECE_NOT_FOUND', 404), ('PIECE_PREVIEW_STALE', 409), ('PIECE_PREVIEW_EXPIRED', 409),
    ('PIECE_CONFLICT', 409)])
def test_cancel_http_maps_only_explicit_sql_errors(harness, code, status):
    call, state = harness
    state['handler'] = lambda _: httpx.Response(400, json={
        'code': 'P0001', 'message': code, 'details': _PRIVATE, 'hint': _PRIVATE})
    _error(call(), status, code)
    assert len(state['calls']) == 1


@pytest.mark.parametrize('status,payload', [(404, {'code': 'PGRST202', 'message': _PRIVATE}),
    (401, {'code': 'PGRST301', 'message': 'PIECE_AUTH_REQUIRED'}),
    (500, {'code': 'P0001', 'message': 'PIECE_NOT_FOUND'}),
    (400, {'code': '23505', 'message': 'PIECE_CONFLICT'}),
    (400, {'code': 'P0001', 'message': 'PIECE_NOT_FOUND ' + _PRIVATE}),
    (400, {'code': 'P0001', 'message': [_PRIVATE]}), (400, [_PRIVATE]),
    (200, {'code': 'P0001', 'message': 'PIECE_NOT_FOUND'}),
    (200, dict(_result(), source_lineage=_PRIVATE)),
    (200, dict(_result(), preview_id=str(uuid4()))),
    (200, dict(_result(), preview_revision=2)),
    (200, dict(_result(), lifecycle_status='saved'))])
def test_cancel_http_invalid_backend_response_is_concealed(harness, status, payload):
    call, state = harness
    state['handler'] = lambda _: httpx.Response(status, json=payload)
    _error(call(), 503, 'PIECE_TEMPORARILY_UNAVAILABLE')
    assert len(state['calls']) == 1


def test_cancel_http_non_json_response_is_unknown_not_retried(harness):
    call, state = harness
    state['handler'] = lambda _: httpx.Response(502, text=_PRIVATE)
    _error(call(), 503, 'PIECE_TEMPORARILY_UNAVAILABLE')
    assert len(state['calls']) == 1


def test_cancel_http_does_not_swallow_task_cancellation(harness):
    call, state = harness
    state['auth_error'] = asyncio.CancelledError()
    with pytest.raises(asyncio.CancelledError):
        call()
    assert state['calls'] == []


def test_cancel_http_native_success_repeat_and_save_rejection(harness, database):
    call, state = harness
    conn, pg, _ = database
    preview = _B5['_issue'](conn)
    before = _B5['_B2']['_legacy_identity'](conn)
    _connect_native(state, database)
    first, second = call(preview['preview_id']), call(preview['preview_id'])
    assert first.status_code == second.status_code == 200
    assert first.json()['idempotency_replayed'] is False
    assert second.json() == dict(first.json(), idempotency_replayed=True)
    assert first.json()['row_version'] == 2
    assert len(state['auth']) == len(state['calls']) == 2
    with pytest.raises(pg.errors.RaiseException, match='(?m)^PIECE_CONFLICT$'):
        _B4['_save'](conn, dict(preview, id=UUID(preview['preview_id'])))
    assert _B4['_used'](conn) == 0
    assert conn.execute('SELECT lifecycle_status,row_version FROM public.piece_records').fetchone() == ('cancelled', 2)
    assert _B5['_B2']['_legacy_identity'](conn) == before


def test_cancel_http_native_other_owner_and_missing_are_same(harness, database):
    call, state = harness
    conn, _, _ = database
    preview = _B5['_issue'](conn)
    _connect_native(state, database)
    headers = {'Authorization': 'Bearer synthetic-viewer'}
    other, missing = call(preview['preview_id'], headers=headers), call(str(uuid4()), headers=headers)
    _error(other, 404, 'PIECE_NOT_FOUND')
    _error(missing, 404, 'PIECE_NOT_FOUND')
    assert other.content == missing.content
    assert conn.execute('SELECT lifecycle_status,row_version FROM public.piece_records').fetchone() == ('preview_draft', 1)
    assert _B4['_used'](conn) == 0


def test_cancel_http_native_stale_and_expired_have_no_effect(harness, database):
    call, state = harness
    conn, _, _ = database
    preview = _B5['_issue'](conn)
    _connect_native(state, database)
    _error(call(preview['preview_id'], body={'expected_preview_revision': 2}), 409, 'PIECE_PREVIEW_STALE')
    conn.execute("UPDATE public.piece_records SET expires_at=clock_timestamp()-interval '1 second'")
    _error(call(preview['preview_id']), 409, 'PIECE_PREVIEW_EXPIRED')
    assert conn.execute('SELECT lifecycle_status,row_version FROM public.piece_records').fetchone() == ('preview_draft', 1)
    assert _B4['_used'](conn) == 0


def test_cancel_http_native_lost_ack_then_same_retry(harness, database):
    call, state = harness
    conn, _, _ = database
    preview = _B5['_issue'](conn)
    _connect_native(state, database, lose_ack=True)
    _error(call(preview['preview_id']), 503, 'PIECE_TEMPORARILY_UNAVAILABLE')
    assert len(state['calls']) == 1
    assert conn.execute('SELECT lifecycle_status,row_version FROM public.piece_records').fetchone() == ('cancelled', 2)
    _connect_native(state, database)
    recovered = call(preview['preview_id'])
    assert recovered.status_code == 200 and recovered.json()['idempotency_replayed'] is True
    assert recovered.json()['row_version'] == 2 and len(state['calls']) == 2
    assert _B4['_used'](conn) == 0


def test_only_cancel_route_exists_and_production_registration_is_unchanged(harness):
    call, state = harness
    assert call(method='POST').status_code == 405
    assert state['calls'] == []
    root = Path(__file__).resolve().parents[4]
    assert 'api_piece_v2' not in (root / 'ai/services/ai_inference/app.py').read_text()
