"""B7 owner history/detail through ASGI, shared HTTP client and native SQL.

Authentication and the PostgREST HTTP envelope are synthetic. Native cases
issue and save admitted synthetic previews with real candidate M4 functions in
B4's explicitly acknowledged disposable PostgreSQL database. No production
registration, real Auth, safety issuer, source author, or device is claimed.
"""
from __future__ import annotations

import asyncio
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import re
import runpy
from uuid import uuid4

import httpx
import pytest
from fastapi import FastAPI, HTTPException

_B6 = runpy.run_path(str(Path(__file__).with_name('test_b06_piece_v2_save_api.py')))
_B4, _B5, _ROOT = _B6['_B4'], _B6['_B5'], _B6['_ROOT']
database = _B6['database']
OWNER, VIEWER = _B6['OWNER'], _B6['VIEWER']
PRIVATE = 'SYNTHETIC_PRIVATE_SOURCE_OR_PROVIDER_DIAGNOSTIC'
_DETAIL_FIELDS = {'api_contract_version', 'piece_contract_version', 'piece_id', 'public_id',
    'lifecycle_status', 'visibility_scope', 'row_version', 'saved_at', 'format_type',
    'piece_text', 'piece_text_hash', 'content_payload', 'content_payload_hash', 'content_status',
    'visual_recipe', 'visual_recipe_hash', 'renderer_version', 'export_contract_version',
    'render_interface_version', 'render_reproducibility_version'}
_FORBIDDEN_SELECT = {'source_input_id', 'source_input_version', 'source_input_bundle_commitment',
    'source_lineage', 'save_idempotency_key_hash', 'preview_request_hash', 'preview_eligible_formats'}


def _row(*, owner=OWNER, stamp='2026-10-06T00:00:00+00:00', state='saved'):
    row = _B6['_row']('premium')
    row.update(owner_user_id=owner, public_id='piece:'+row['id'], lifecycle_status=state,
        expires_at=None, row_version=2, saved_at=stamp, source_input_id=PRIVATE,
        renderer_version='synthetic-test-renderer.v1',
        export_contract_version='piece.export_contract.v1',
        render_interface_version='piece.render_interface.v1',
        render_reproducibility_version='piece.render_reproducibility.v1')
    return row


def _stamp(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def _boundary(params):
    expression = params.get('or')
    if expression is None:
        return None
    # This translates the observed PostgREST keyset predicate, not the opaque
    # client cursor. The database below performs the actual ordering/filter.
    match = re.fullmatch(r'\(saved_at\.lt\.([^,]+),and\(saved_at\.eq\.([^,]+),id\.lt\.([0-9a-f-]+)\)\)', expression)
    assert match and match[1] == match[2]
    return match[1], match[3]


def _memory_rows(rows, params):
    rows = [r for r in rows if r['owner_user_id'] == params['owner_user_id'][3:]
        and r['lifecycle_status'] == 'saved']
    if 'id' in params:
        rows = [r for r in rows if r['id'] == params['id'][3:]]
    else:
        rows = sorted(rows, key=lambda r: (_stamp(r['saved_at']), r['id']), reverse=True)
        boundary = _boundary(params)
        if boundary:
            rows = [r for r in rows if (_stamp(r['saved_at']), r['id']) < (_stamp(boundary[0]), boundary[1])]
    columns = params['select'].split(',')
    return [{k: r[k] for k in columns} for r in rows[:int(params['limit'])]]


@pytest.fixture
def harness(monkeypatch):
    import api_piece_v2 as api
    import supabase_client as shared
    from piece_v2_source_adapter import PieceSavedSourceAdapter
    from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
    state = {'rows': [_row()], 'reads': [], 'auth': [], 'handler': None,
        'verified': OWNER, 'auth_error': None}
    async def verify(authorization):
        state['auth'].append(authorization)
        if state['auth_error']:
            raise state['auth_error']
        if authorization not in ('Bearer synthetic-owner', 'Bearer synthetic-viewer'):
            raise HTTPException(401, PRIVATE)
        return VIEWER if authorization.endswith('viewer') else state['verified']
    def no_author(*args, **kwargs):
        pytest.fail('an owner read must not author a replacement Piece')
    async def no_source(*args, **kwargs):
        pytest.fail('an owner read must not re-read the original source or current tier')
    monkeypatch.setattr(api, '_verify_bearer', verify)
    monkeypatch.setattr(MeaningExperienceEngine, 'generate', no_author)
    monkeypatch.setattr(PieceSavedSourceAdapter, 'resolve_original_handoff', no_source)
    monkeypatch.setattr(shared, 'SUPABASE_URL', 'https://piece.invalid')
    monkeypatch.setattr(shared, 'SUPABASE_SERVICE_ROLE_KEY', 'synthetic-service-only')
    app = FastAPI(); app.include_router(api.router)
    def upstream(request):
        assert request.method == 'GET', 'history/detail must not issue writes'
        assert request.url.path == '/rest/v1/piece_records'
        assert request.headers['authorization'] == 'Bearer synthetic-service-only'
        assert request.headers['apikey'] == 'synthetic-service-only'
        assert request.extensions['timeout']['read'] == 8.0
        params = dict(request.url.params)
        assert params['owner_user_id'].startswith('eq.')
        assert params['lifecycle_status'] == 'eq.saved'
        assert not (_FORBIDDEN_SELECT & set(params['select'].split(',')))
        assert '*' not in params['select']
        if 'id' in params:
            assert params['limit'] == '2'
        else:
            assert params['order'] == 'saved_at.desc,id.desc'
            assert 'offset' not in params
        state['reads'].append(params)
        if state['handler']:
            return state['handler'](params)
        return httpx.Response(200, json=_memory_rows(state['rows'], params))
    def call(path='history', *, query=None, headers=None):
        async def run():
            async with httpx.AsyncClient(transport=httpx.MockTransport(upstream)) as backend:
                async def client(): return backend
                monkeypatch.setattr(shared, 'get_async_client', client)
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                    base_url='https://test.invalid') as http:
                    return await http.get('/emotion/piece/'+path, params=query,
                        headers={'Authorization':'Bearer synthetic-owner'} if headers is None else headers)
        return asyncio.run(run())
    return call, state


def _error(response, status, code):
    assert response.status_code == status and response.json() == {'code': code}
    assert response.headers['cache-control'] == 'no-store'
    assert PRIVATE not in response.text


def _detail(payload, row):
    assert set(payload) == _DETAIL_FIELDS
    assert payload['api_contract_version'] == 'piece.api.v2'
    assert payload['piece_contract_version'] == 'piece.record.v2'
    assert payload['piece_id'] == row['id'] and payload['public_id'] == 'piece:'+row['id']
    assert _stamp(payload['saved_at']) == _stamp(row['saved_at'])
    assert payload['content_status'] == row['safety_state']
    for key in _DETAIL_FIELDS - {'api_contract_version','piece_id','saved_at','content_status'}:
        assert payload[key] == row[key]
    assert PRIVATE not in str(payload)


def test_history_is_owner_only_saved_and_returns_exact_persisted_artifacts(harness):
    call, state = harness
    private, public = state['rows'][0], _row(stamp='2026-10-05T00:00:00+00:00')
    public['visibility_scope'] = 'public'; public['safety_state'] = 'adjusted'
    state['rows'] += [public, _row(owner=VIEWER), _row(state='preview_draft')]
    response = call()
    assert response.status_code == 200 and response.headers['cache-control'] == 'no-store'
    body = response.json()
    assert set(body) == {'api_contract_version', 'items', 'next_cursor'}
    assert body['api_contract_version'] == 'piece.api.v2' and body['next_cursor'] is None
    assert len(body['items']) == 2
    _detail(body['items'][0], private); _detail(body['items'][1], public)
    assert state['reads'][0]['owner_user_id'] == 'eq.'+OWNER
    assert state['reads'][0]['limit'] == '21'


@pytest.mark.parametrize('public_form', [False, True])
def test_detail_accepts_piece_identity_and_authenticates_every_repeat(harness, public_form):
    call, state = harness; row = state['rows'][0]
    path = ('piece:' if public_form else '')+row['id']
    for _ in range(2):
        response = call(path)
        assert response.status_code == 200 and response.headers['cache-control'] == 'no-store'
        _detail(response.json(), row)
    assert state['auth'] == ['Bearer synthetic-owner']*2
    assert [p['id'] for p in state['reads']] == ['eq.'+row['id']]*2


@pytest.mark.parametrize('headers', [{}, {'Authorization':'Basic invalid'},
    [('Authorization','Bearer synthetic-owner'),('Authorization','Bearer synthetic-viewer')]])
def test_read_auth_is_required_before_backend_access(harness, headers):
    call, state = harness
    _error(call(headers=headers), 401, 'PIECE_AUTH_REQUIRED')
    assert state['reads'] == []


@pytest.mark.parametrize('query', [{'limit':'0'}, {'limit':'101'}, {'limit':'1.5'},
    {'limit':'not-a-number'}, [('limit','1'),('limit','2')], {'user_id':VIEWER},
    {'cursor':PRIVATE}, [('cursor','a'),('cursor','b')]])
def test_history_rejects_untrusted_query_before_backend_read(harness, query):
    call, state = harness
    _error(call(query=query), 400, 'PIECE_REQUEST_INVALID')
    assert state['reads'] == []


def test_detail_query_and_invalid_id_remain_body_free(harness):
    call, state = harness
    _error(call(state['rows'][0]['id'], query={'user_id':VIEWER}), 400, 'PIECE_REQUEST_INVALID')
    _error(call('not-a-uuid-'+PRIVATE), 404, 'PIECE_NOT_FOUND')
    assert state['reads'] == []


def test_empty_owner_history_has_no_cursor(harness):
    call, state = harness; state['rows'] = []
    response = call()
    assert response.status_code == 200
    assert response.json() == {'api_contract_version':'piece.api.v2','items':[],'next_cursor':None}


@pytest.mark.parametrize('kind', ['other-owner', 'preview', 'missing'])
def test_inaccessible_detail_is_always_concealed_404(harness, kind):
    call, state = harness; row = state['rows'][0]
    if kind == 'other-owner': row['owner_user_id'] = VIEWER
    elif kind == 'preview': row['lifecycle_status'] = 'preview_draft'
    else: state['rows'] = []
    _error(call(row['id']), 404, 'PIECE_NOT_FOUND')


@pytest.mark.parametrize('changed', [
    {'piece_text':PRIVATE}, {'content_payload_hash':'a'*64}, {'visual_recipe_hash':'b'*64},
    {'safety_state':'unavailable'}, {'public_id':'piece:'+str(uuid4())},
    {'saved_at':PRIVATE}, {'row_version':True}, {'renderer_version':''},
    {'export_contract_version':'unsupported'},
])
def test_corrupt_stored_artifact_never_returns_partial_content(harness, changed):
    call, state = harness
    state['rows'][0].update(changed)
    _error(call(state['rows'][0]['id']), 503, 'PIECE_TEMPORARILY_UNAVAILABLE')


@pytest.mark.parametrize('status,payload', [(404,{'message':PRIVATE}), (401,{'message':PRIVATE}),
    (500,{'message':PRIVATE}), (200,{'piece_text':PRIVATE}), (200,[None])])
def test_untrusted_backend_envelope_is_private_unavailable(harness, status, payload):
    call, state = harness
    state['handler'] = lambda _: httpx.Response(status, json=payload)
    _error(call(), 503, 'PIECE_TEMPORARILY_UNAVAILABLE')
    assert len(state['reads']) == 1


def test_transport_failure_uses_shared_bounded_read_retry_without_public_leak(harness, monkeypatch):
    call, state = harness
    monkeypatch.setenv('SUPABASE_HTTP_RETRY_COUNT', '1')
    monkeypatch.setenv('SUPABASE_HTTP_RETRY_BACKOFF_SECONDS', '0.1')
    def fail(_): raise httpx.ReadTimeout(PRIVATE)
    state['handler'] = fail
    _error(call(), 503, 'PIECE_TEMPORARILY_UNAVAILABLE')
    assert len(state['reads']) == 2


def test_history_rejects_backend_owner_leak_and_bad_order_as_a_whole(harness):
    call, state = harness
    a, b = state['rows'][0], _row(stamp='2026-10-05T00:00:00+00:00')
    state['rows'] = [a, b]
    for failure in ('owner', 'order'):
        def corrupt(params):
            rows = _memory_rows(state['rows'], params)
            if failure == 'owner': rows[1]['owner_user_id'] = VIEWER
            else: rows.reverse()
            return httpx.Response(200, json=rows)
        state['handler'] = corrupt
        _error(call(), 503, 'PIECE_TEMPORARILY_UNAVAILABLE')


def test_cursor_is_owner_bound_and_continuation_reauthenticates(harness):
    call, state = harness; state['rows'].append(_row(stamp='2026-10-05T00:00:00+00:00'))
    first = call(query={'limit':'1'})
    assert first.status_code == 200
    cursor = first.json()['next_cursor']
    assert isinstance(cursor, str) and cursor
    read_count = len(state['reads'])
    _error(call(query={'limit':'1','cursor':cursor}, headers={'Authorization':'Bearer synthetic-viewer'}),
        400, 'PIECE_REQUEST_INVALID')
    assert len(state['reads']) == read_count
    next_page = call(query={'limit':'1','cursor':cursor})
    assert next_page.status_code == 200 and next_page.json()['next_cursor'] is None
    assert len(state['auth']) == 3


def _native_connect(state, database):
    conn, _, _ = database
    from psycopg import sql
    def handler(params):
        columns = params['select'].split(',')
        where = ['owner_user_id=%s', 'lifecycle_status=%s']
        values = [params['owner_user_id'][3:], params['lifecycle_status'][3:]]
        if 'id' in params:
            where.append('id=%s'); values.append(params['id'][3:])
        else:
            boundary = _boundary(params)
            if boundary:
                where.append('(saved_at,id)<(%s::timestamptz,%s::uuid)'); values.extend(boundary)
        values.append(int(params['limit']))
        query = sql.SQL('SELECT to_jsonb(r) FROM (SELECT {} FROM public.piece_records WHERE {} ORDER BY saved_at DESC,id DESC LIMIT %s) r').format(
            sql.SQL(',').join(sql.Identifier(k) for k in columns), sql.SQL(' AND '.join(where)))
        with conn.transaction():
            conn.execute('SET LOCAL ROLE service_role')
            rows = [r[0] for r in conn.execute(query, values).fetchall()]
        return httpx.Response(200, json=rows)
    state['handler'] = handler


def _native_save(conn, *, key=None, visibility='private'):
    key = key or str(uuid4())
    record = _B5['_record']()
    preview = _B5['_issue'](conn, record=record, key=key)
    row = dict(record, id=preview['preview_id'])
    _B4['_rpc'](conn, 'piece_save_v2', _B4['_args'](row, key=key, visibility=visibility))
    return conn.execute('SELECT to_jsonb(r) FROM public.piece_records r WHERE id=%s', (preview['preview_id'],)).fetchone()[0]


def _native_state(conn):
    return (conn.execute('SELECT to_jsonb(r) FROM public.piece_records r ORDER BY id').fetchall(),
        _B4['_used'](conn), conn.execute('SELECT count(*) FROM public.piece_quota_month_locks').fetchone(),
        conn.execute('SELECT count(*) FROM public.piece_delete_receipts').fetchone())


def test_native_issue_save_read_persists_after_tier_change_without_source(database, harness):
    conn, _, _ = database; call, state = harness
    row = _native_save(conn)
    # No emotions/Q2 source tables exist in this fixture. A saved owner read
    # remains available after a downgrade and preserves the saved visual recipe.
    conn.execute("UPDATE public.profiles SET subscription_tier='unknown'")
    _native_connect(state, database)
    before = _native_state(conn)
    detail = call(row['id']); history = call()
    assert detail.status_code == history.status_code == 200
    _detail(detail.json(), row); _detail(history.json()['items'][0], row)
    assert _native_state(conn) == before


def test_native_detail_and_history_reflect_visibility_and_physical_deletion(database, harness):
    conn, _, _ = database; call, state = harness
    row = _native_save(conn); _native_connect(state, database)
    changed = _B4['_rpc'](conn, 'piece_set_visibility_v2', {'p_owner_user_id':OWNER,
        'p_piece_id':row['id'], 'p_expected_row_version':row['row_version'], 'p_visibility_scope':'public'})
    detail = call(row['id']); history = call()
    assert detail.status_code == history.status_code == 200
    assert detail.json()['visibility_scope'] == history.json()['items'][0]['visibility_scope'] == 'public'
    assert detail.json()['row_version'] == changed['row_version']
    _B4['_rpc'](conn, 'piece_delete_v2', {'p_owner_user_id':OWNER, 'p_piece_id':row['id'],
        'p_expected_row_version':changed['row_version'], 'p_idempotency_key_hash':hashlib.sha256(b'delete').hexdigest()})
    _error(call(row['id']), 404, 'PIECE_NOT_FOUND')
    assert call().json()['items'] == [] and _B4['_used'](conn) == 1


def test_native_history_keyset_handles_ties_deleted_boundary_and_new_head(database, harness):
    conn, _, _ = database; call, state = harness
    conn.execute("UPDATE public.profiles SET subscription_tier='premium'")
    rows = [_native_save(conn) for _ in range(5)]
    conn.execute("UPDATE public.piece_records SET saved_at='2026-10-05T00:00:00+00:00'")
    ids = sorted((r['id'] for r in rows), reverse=True)
    _native_connect(state, database)
    first = call(query={'limit':'2'})
    assert first.status_code == 200
    assert [r['piece_id'] for r in first.json()['items']] == ids[:2]
    cursor = first.json()['next_cursor']; assert cursor
    boundary = next(r for r in rows if r['id'] == ids[1])
    _B4['_rpc'](conn, 'piece_delete_v2', {'p_owner_user_id':OWNER, 'p_piece_id':boundary['id'],
        'p_expected_row_version':boundary['row_version'], 'p_idempotency_key_hash':hashlib.sha256(b'delete-boundary').hexdigest()})
    added = _native_save(conn)
    conn.execute("UPDATE public.piece_records SET saved_at='2026-10-06T00:00:00+00:00' WHERE id=%s", (added['id'],))
    before = _native_state(conn)
    second = call(query={'limit':'2','cursor':cursor})
    assert second.status_code == 200
    assert [r['piece_id'] for r in second.json()['items']] == ids[2:4]
    third = call(query={'limit':'2','cursor':second.json()['next_cursor']})
    assert third.status_code == 200 and third.json()['next_cursor'] is None
    assert [r['piece_id'] for r in third.json()['items']] == ids[4:]
    assert _native_state(conn) == before


def test_native_other_owner_and_unsaved_record_cannot_be_read(database, harness):
    conn, _, _ = database; call, state = harness
    saved = _native_save(conn)
    preview = _B5['_issue'](conn, key='unsaved')
    _native_connect(state, database)
    _error(call(saved['id'], headers={'Authorization':'Bearer synthetic-viewer'}), 404, 'PIECE_NOT_FOUND')
    _error(call(preview['preview_id']), 404, 'PIECE_NOT_FOUND')
    assert call(headers={'Authorization':'Bearer synthetic-viewer'}).json()['items'] == []
    assert [r['piece_id'] for r in call().json()['items']] == [saved['id']]


def test_owner_routes_remain_unregistered_in_production():
    assert 'api_piece_v2' not in (_ROOT/'ai/services/ai_inference/app.py').read_text()
