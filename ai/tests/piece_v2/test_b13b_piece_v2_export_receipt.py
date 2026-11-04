"""B13-B candidate: synthetic HTTP/Auth, actual disposable PostgreSQL storage."""
from __future__ import annotations

import asyncio
from hashlib import sha256
import json
import os
from pathlib import Path
import runpy
import subprocess

import httpx
import pytest

_B7 = runpy.run_path(str(Path(__file__).with_name('test_b07_piece_v2_owner_api.py')))
OWNER, VIEWER = _B7['OWNER'], _B7['VIEWER']
import api_piece_v2 as api
import piece_v2_owner_service as owner_service
import supabase_client
from piece_v2_export_receipt_service import ACK_HEADER, RPC, FIXED
from piece_v2_runtime_control import create_piece_preview_application

KEY = 'b' * 32
RENDERER = 'piece.rn_bitmap_renderer.ios.v2'


def payload(row):
    return {**FIXED, 'piece_id': row['public_id'], 'expected_row_version': row['row_version'],
        'piece_text_hash': row['piece_text_hash'], 'visual_recipe_hash': row['visual_recipe_hash'],
        'renderer_version': row['renderer_version'], 'output_profile': 'png_1080x1350_srgb_v1',
        'mime_type': 'image/png', 'width': 1080, 'height': 1350, 'asset_sha256': 'c' * 64,
        'generated_at': '2026-11-04T01:00:00.000Z'}


def new_app(ready=True):
    return create_piece_preview_application(owner_read_requested=True, owner_read_ready=True,
        export_requested=True, export_ready=True, export_receipt_ready=ready)


@pytest.fixture
def client(monkeypatch):
    row = _B7['_row']()
    row['renderer_version'] = RENDERER
    path = '/emotion/piece/' + row['id']
    calls = []
    app = new_app()

    async def verify(auth):
        return OWNER if auth == 'Bearer owner' else VIEWER

    async def load(params):
        return [row] if params['owner_user_id'] == 'eq.' + OWNER else []

    async def stub_rpc(name, args, **kwargs):
        assert name == RPC and kwargs == {'timeout': 8.0}
        calls.append(args)
        return httpx.Response(200, json={'export_id': 'ae4e2b94-a730-44f4-9ef1-1fb81773782e'})

    monkeypatch.setattr(api, '_verify_bearer', verify)
    monkeypatch.setattr(owner_service, 'load_saved_records', load)
    monkeypatch.setattr(supabase_client, 'sb_post_rpc', stub_rpc)

    def request(method='POST', value=None, headers=None, *, route='', **options):
        async def run():
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='https://test.invalid') as h:
                sent = [('Authorization', 'Bearer owner'), (ACK_HEADER, '1'), ('Idempotency-Key', KEY)] if headers is None else headers
                return await h.request(method, path + (route or ('/export' if method == 'GET' else '/export-receipt')),
                    headers=sent, json=value, **options)
        return asyncio.run(run())
    return row, calls, app, request


def test_exact_receipt_and_opt_in_legacy_export_shape(client):
    row, calls, app, request = client
    legacy = request('GET', headers={'Authorization': 'Bearer owner'})
    aware = request('GET')
    assert legacy.status_code == aware.status_code == 200
    assert ACK_HEADER not in legacy.headers and aware.headers[ACK_HEADER] == '1'
    assert aware.json() == legacy.json()
    sent = payload(row)
    result = request(value=sent)
    assert result.status_code == 200 and result.headers['Cache-Control'] == 'no-store'
    assert result.json() == {'export_id': 'ae4e2b94-a730-44f4-9ef1-1fb81773782e',
                            **{k: v for k, v in sent.items() if k != 'expected_row_version'}}
    assert len(calls) == 1
    assert calls[0]['p_idempotency_key_hash'] == sha256(('piece.export_receipt.v1:' + KEY).encode()).hexdigest()
    assert len(calls[0]['p_request_identity_hash']) == 64
    assert row['piece_text'] not in result.text and row['piece_text'] not in str(calls)


@pytest.mark.parametrize('changes', [
    {'body': 'SECRET'}, {'recipient': 'SECRET'}, {'uri': 'file:///SECRET'}, {'outcome': 'succeeded'},
    {'persistent_server_asset': 0}, {'body_free': 1}, {'height': 1920}, {'width': True},
    {'asset_sha256': 'A'*64}, {'piece_id': 'SECRET'}, {'generated_at': '2026-02-30T01:00:00.000Z'},
])
def test_receipt_closed_shape_and_no_echo(client, changes):
    row, calls, _, request = client
    result = request(value={**payload(row), **changes})
    assert result.status_code == 400 and result.json() == {'code':'PIECE_REQUEST_INVALID'}
    assert 'SECRET' not in result.text and calls == []


def test_receipt_requires_owner_current_snapshot_and_explicit_storage_readiness(client):
    row, calls, app, request = client
    assert request(value=payload(row), headers={'Authorization':'Bearer viewer', ACK_HEADER:'1',
        'Idempotency-Key':KEY}).status_code == 404
    assert request(value={**payload(row), 'expected_row_version': 123}).status_code == 409
    assert request(value={**payload(row), 'visual_recipe_hash': 'd'*64}).status_code == 409
    assert request(content='{"body_free":true,"body_free":false}').status_code == 400
    assert request(content=' '*2049).status_code == 400
    app.state.piece_export_receipt_ready = False
    assert ACK_HEADER not in request('GET').headers
    assert request(value=payload(row)).json() == {'code':'PIECE_FEATURE_DISABLED'}
    assert calls == []


@pytest.fixture
def sql():
    if not os.environ.get('Q2_PGLITE_MODULE'):
        pytest.skip('set Q2_PGLITE_MODULE to disposable PGlite')
    proc = subprocess.Popen(['node', str(Path(__file__).resolve().parents[1] / 'helpers/piece_export_receipt_postgres.cjs')],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    try:
        assert json.loads(proc.stdout.readline()) == {'ready': True}

        def query(statement, params=(), role=None):
            proc.stdin.write(json.dumps({'sql': statement, 'params': params, 'role': role}) + '\n')
            proc.stdin.flush()
            return json.loads(proc.stdout.readline())

        yield query
    finally:
        proc.stdin.close()
        proc.wait(timeout=10)


def seed(sql, row):
    row = {**row, 'save_idempotency_key_hash': 'a'*64}
    del row['public_id'], row['preview_eligible_formats']
    row['source_input_id'] = row['source_lineage']['source_input']['source_input_id']
    columns = tuple(row)
    values = [json.dumps(x, ensure_ascii=False) if isinstance(x, (dict, list)) else x for x in row.values()]
    result = sql(f"insert into public.piece_records ({','.join(columns)}) values "
                 f"({','.join('$'+str(i) for i in range(1,len(columns)+1))})", values)
    assert 'code' not in result, result
    return row


def test_real_postgresql_receipt_atomic_replay_privilege_and_retention(sql):
    row = seed(sql, {**_B7['_row'](), 'renderer_version': RENDERER})
    query = 'select public.' + RPC + '(' + ','.join('$'+str(i) for i in range(1,11)) + ') as value'
    args = [OWNER, row['id'], row['row_version'], KEY*2, 'a'*64, row['piece_text_hash'],
            row['visual_recipe_hash'], 'c'*64, RENDERER, 'png_1080x1350_srgb_v1']

    def change(index, value):
        out = args.copy()
        out[index] = value
        return out

    for role in ('anon', 'authenticated'):
        assert sql(query, args, role)['code'] == '42501'
    assert sql('select * from public.piece_export_receipts', role='service_role')['code'] == '42501'
    assert sql(query, change(0, VIEWER), 'service_role')['message'] == 'PIECE_NOT_FOUND'
    for index, invalid in [(2, 1), (5, 'f'*64), (6, 'f'*64), (8, 'piece.rn_bitmap_renderer.ios.v1'),
                           (9, 'png_1080x1920_srgb_v1')]:
        assert sql(query, change(index, invalid), 'service_role')['message'] == 'PIECE_CONFLICT'
    assert sql('select count(*)::int as n from public.piece_export_receipts')['rows'] == [{'n':0}]
    accepted = sql(query, args, 'service_role')
    assert set(accepted['rows'][0]['value']) == {'export_id'}
    assert sql(query, args, 'service_role') == accepted
    for index in (4, 7):
        assert sql(query, change(index, 'd'*64), 'service_role')['message'] == 'PIECE_CONFLICT'
    stored = sql('select to_jsonb(r) as value from public.piece_export_receipts r')['rows']
    assert len(stored) == 1
    assert set(stored[0]['value']) == {'receipt_id','owner_user_id','piece_id','idempotency_key_hash',
        'piece_text_hash','visual_recipe_hash','export_contract_version','outcome','error_code',
        'created_at','asset_sha256','request_identity_hash'}
    assert stored[0]['value']['asset_sha256'] == 'c'*64
    assert 'code' not in sql('delete from public.piece_records where id=$1', [row['id']])
    assert sql(query, args, 'service_role')['message'] == 'PIECE_NOT_FOUND'
    assert sql('select to_jsonb(r) as value from public.piece_export_receipts r')['rows'] == stored

def test_http_lost_commit_ack_reuses_same_postgres_receipt(client, sql, monkeypatch):
    row, _, _, request = client
    seed(sql, row)
    writes = []

    async def use_postgres(name, args, **kwargs):
        assert name == RPC
        arguments = ','.join(k + ' => $' + str(i) for i, k in enumerate(args, 1))
        saved = sql(f'select public.{name}({arguments}) as value', list(args.values()), 'service_role')
        if 'code' in saved:
            return httpx.Response(400, json=saved)
        writes.append(saved['rows'][0]['value'])
        if len(writes) == 1:
            raise httpx.ReadError('PRIVATE transport failure after SQL commit')
        return httpx.Response(200, json=writes[-1])

    monkeypatch.setattr(supabase_client, 'sb_post_rpc', use_postgres)
    result = request(value=payload(row))
    assert result.status_code == 503 and result.json() == {'code':'PIECE_TEMPORARILY_UNAVAILABLE'}
    assert request(value=payload(row)).json()['export_id'] == writes[0]['export_id']
    assert writes[0] == writes[1]
    assert request(value={**payload(row), 'asset_sha256': 'e'*64}).status_code == 409
    assert sql('select count(*)::int as n from public.piece_export_receipts')['rows'] == [{'n':1}]
