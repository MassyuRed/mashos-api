"""Prepared shared API -> real CMEE/review -> disposable native PostgreSQL.

Reuse the existing B5 fixture and its guarded disposable database unchanged.
Bearer, saved-source IO, active-user Auth and PostgREST transport are synthetic.
Generation, review, response projection and native SQL remain real. No live
service, real Auth, lifespan, RN/device or product acceptance is claimed here.
"""
import asyncio
from copy import deepcopy
from pathlib import Path
import runpy
import socket

import pytest
import httpx

import app as shared
import middleware_active_user_touch as active_touch
import piece_v2_preview_service as service
import supabase_client
from piece_v2_runtime_control import create_piece_preview_application

_H = runpy.run_path(str(Path(__file__).with_name('test_b05_reviewed_preview_issuance.py')))
_B5 = _H['_B5']
database = _H['database']
_RUNTIME = {'ttl_seconds': 600, 'renderer_version': 'synthetic-renderer.v1'}


def _application(*, enabled=True):
    settings = ({'preview_requested': True, 'preview_ready': True,
                 'preview_runtime': dict(_RUNTIME)} if enabled else {})
    return shared.create_application(piece_preview_configuration=settings)


@pytest.fixture(autouse=True)
def isolated_external_boundaries(monkeypatch):
    async def no_active_user(_token):
        return None
    monkeypatch.setattr(active_touch, 'resolve_user_id_verified_cached', no_active_user)
    original = socket.socket.connect
    denied = []
    def only_disposable_database(sock, address):
        if not (isinstance(address, tuple) and address[:2] == ('127.0.0.1', 5432)):
            denied.append(True)
            raise AssertionError('Only the disposable loopback PostgreSQL is allowed')
        return original(sock, address)
    monkeypatch.setattr(socket.socket, 'connect', only_disposable_database)
    yield
    assert not denied


def test_shared_candidate_generates_persists_and_replays_exact_body(database, monkeypatch):
    conn, _, _ = database
    _, _, request, prepared, state = _H['_preview_http_harness'](database, monkeypatch)
    first = _H['_preview_http_post'](_application(), request)
    assert first.status_code == 200
    assert first.headers['x-cocolon-contract-id'] == 'emotion.piece.preview.v2'
    assert first.headers['cache-control'] == 'no-store'
    value = first.json()
    fields = ('piece_text', 'piece_text_hash', 'content_payload',
              'content_payload_hash', 'visual_recipe', 'visual_recipe_hash')
    for field in fields:
        assert value[field] == prepared.artifact_payload()[field]
    assert not ({'source_lineage', 'owner_user_id', 'safety_state',
                 'idempotency_replayed'} & set(value))
    stored = conn.execute('SELECT to_jsonb(r) FROM public.piece_records r').fetchone()[0]
    for field in fields:
        assert stored[field] == value[field]
    assert state['authors'] == state['actual_reviews'] == state['http_rpc'] == 1

    _H['_no_author'](monkeypatch)
    replay = _H['_preview_http_post'](_application(), request)
    assert replay.status_code == 200 and replay.json() == value
    assert replay.headers['x-cocolon-contract-id'] == 'emotion.piece.preview.v2'
    assert conn.execute('SELECT to_jsonb(r) FROM public.piece_records r').fetchone()[0] == stored
    assert conn.execute('SELECT count(*) FROM public.piece_records').fetchone() == (1,)
    assert state['authors'] == state['actual_reviews'] == state['http_rpc'] == 1
    assert _B5['_B4']['_used'](conn) == 0


def test_shared_candidate_empty_configuration_never_generates_or_persists(database, monkeypatch):
    conn, _, _ = database
    _, _, request, _, state = _H['_preview_http_harness'](database, monkeypatch)
    result = _H['_preview_http_post'](_application(enabled=False), request)
    assert result.status_code == 503 and result.json() == {'code': 'PIECE_FEATURE_DISABLED'}
    assert result.headers['x-cocolon-contract-id'] == 'emotion.piece.preview.v2'
    assert state['authors'] == state['actual_reviews'] == state['http_rpc'] == 0
    assert conn.execute('SELECT count(*) FROM public.piece_records').fetchone() == (0,)
    assert _B5['_B4']['_used'](conn) == 0


def _visual_application(kind):
    if kind == 'shared':
        return _application()
    assert kind == 'preview'
    return create_piece_preview_application(preview_requested=True,
        preview_ready=True, preview_runtime=dict(_RUNTIME))


def _visual_harness(database, monkeypatch, *, tier='premium'):
    """Use real orchestration/SQL; replace only Auth/source and HTTP transport."""
    from psycopg.types.json import Jsonb
    _, owner, request, prepared, state = _H['_preview_http_harness'](
        database, monkeypatch, tier=tier)
    conn, pg, _ = database
    # The older issuer fixture installs Q2 only. Visual mutation also requires
    # the existing Q3 context/feedback schema, even for original-only previews.
    conn.execute((_B5['_B4']['_ROOT'] /
        'supabase/migrations/20260911041749_emlis_q3_plan_rounds.sql').read_text())
    conn.execute((_B5['_B4']['_ROOT'] /
        'supabase/migrations/20261010050940_piece_v2_preview_visual_change.sql').read_text())
    previous_transport = supabase_client.sb_post_rpc
    state.update(visual_rpc=0, visual_reads=0, visual_after_commit=None,
                 visual_lose_ack=False)

    async def load(owner_id, preview_id):
        state['visual_reads'] += 1
        row = conn.execute('SELECT to_jsonb(r) FROM (SELECT ' +
            ','.join(service._REPLAY_COLUMNS) +
            ' FROM public.piece_records WHERE id=%s AND owner_user_id=%s) r',
            (preview_id, owner_id)).fetchone()
        return deepcopy(row[0]) if row else None

    async def transport(name, args, *, timeout):
        if name != 'piece_mutate_preview_visual_v2':
            return await previous_transport(name, args, timeout=timeout)
        assert timeout == 8.0
        state['visual_rpc'] += 1
        values = {k: Jsonb(v) if k in (
            'p_expected_record', 'p_visual_recipe', 'p_expected_source_state') else v
            for k, v in args.items()}
        try:
            result = _B5['_B4']['_rpc'](conn, name, values)
        except pg.errors.RaiseException as exc:
            # The same closed PostgREST error envelope read by production.
            return httpx.Response(400, json={'code': 'P0001', 'message': exc.diag.message_primary})
        if state['visual_after_commit']:
            state['visual_after_commit']()
        if state['visual_lose_ack']:
            raise TimeoutError(_B5['PRIVATE'])
        return httpx.Response(200, json=result)

    monkeypatch.setattr(service, '_load_owned_preview_for_replay', load)
    monkeypatch.setattr(supabase_client, 'sb_post_rpc', transport)
    return owner, request, prepared, state


def _visual_patch(app, preview, tier='premium'):
    selection = {'theme_id': 'quiet_night' if tier != 'free' else 'soft_paper',
                 'aspect_ratio': '9:16' if tier == 'premium' else '4:5',
                 'branding_mode': ('off' if tier == 'premium' else
                                   'required_small' if tier == 'free' else 'required_subtle')}

    async def call():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                    base_url='http://piece-test.invalid') as client:
            return await client.patch('/emotion/piece/preview/' + preview['preview_id'],
                headers={'Authorization': _B5['AUTH']}, json={
                    'expected_preview_revision': preview['preview_revision'],
                    'visual_selection': selection})
    return asyncio.run(call())


def _stored(conn):
    return conn.execute('SELECT to_jsonb(r) FROM public.piece_records r').fetchone()[0]


@pytest.mark.parametrize('kind', ['preview', 'shared'])
@pytest.mark.parametrize('lost_ack', [False, True])
def test_composed_cancel_after_visual_change_replays_terminal_native_row_even_when_stopped(
        database, monkeypatch, kind, lost_ack):
    conn, pg, _ = database
    _, request, _, state = _visual_harness(database, monkeypatch)
    app = _visual_application(kind)
    created = _H['_preview_http_post'](app, request)
    assert created.status_code == 200
    first = created.json()
    updated = _visual_patch(app, first)
    assert updated.status_code == 200
    latest = updated.json()
    _H['_no_author'](monkeypatch)
    previous_transport = supabase_client.sb_post_rpc
    attempts = []

    async def transport(name, args, *, timeout):
        if name != 'piece_cancel_preview_v2':
            return await previous_transport(name, args, timeout=timeout)
        attempts.append(deepcopy(args))
        try:
            result = _B5['_B4']['_rpc'](conn, name, args)
        except pg.errors.RaiseException as exc:
            return httpx.Response(400, json={'code': 'P0001', 'message': exc.diag.message_primary})
        if lost_ack and len(attempts) == 2:
            raise TimeoutError(_B5['PRIVATE'])
        return httpx.Response(200, json=result)
    monkeypatch.setattr(supabase_client, 'sb_post_rpc', transport)

    def cancel(preview):
        async def call():
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                        base_url='http://piece-test.invalid') as client:
                return await client.request('DELETE', '/emotion/piece/preview/' + preview['preview_id'],
                    headers={'Authorization': _B5['AUTH']},
                    json={'expected_preview_revision': preview['preview_revision']})
        return asyncio.run(call())

    # Stopping generation does not remove the existing owner cleanup path.
    app.state.piece_v2_runtime = {}
    stale = cancel(first)
    assert stale.status_code == 409 and stale.json() == {'code': 'PIECE_PREVIEW_STALE'}
    assert _stored(conn)['lifecycle_status'] == 'preview_draft'
    result = cancel(latest)
    assert result.status_code == (503 if lost_ack else 200)
    if lost_ack:
        assert result.json() == {'code': 'PIECE_TEMPORARILY_UNAVAILABLE'}
    else:
        assert result.json()['idempotency_replayed'] is False
    stored = _stored(conn)
    assert stored['lifecycle_status'] == 'cancelled' and stored['row_version'] == 3
    assert stored['preview_revision'] == latest['preview_revision'] == 2
    assert stored['piece_text_hash'] == latest['piece_text_hash']
    assert stored['visual_recipe_hash'] == latest['visual_recipe_hash']
    # Terminal replay must precede expiry; do not invent a new preview/key.
    conn.execute("UPDATE public.piece_records SET expires_at=clock_timestamp()-interval '1 second'")
    repeated = cancel(latest)
    assert repeated.status_code == 200
    assert repeated.json() == dict(preview_id=latest['preview_id'], preview_revision=2,
        row_version=3, lifecycle_status='cancelled', idempotency_replayed=True)
    assert repeated.headers['cache-control'] == 'no-store'
    if kind == 'shared':
        assert repeated.headers['x-cocolon-contract-id'] == 'emotion.piece.preview.cancel.v2'
    assert attempts[1] == attempts[2] and len(attempts) == 3
    assert _stored(conn)['row_version'] == 3
    assert state['authors'] == state['http_rpc'] == state['visual_rpc'] == 1
    assert _B5['_B4']['_used'](conn) == 0


@pytest.mark.parametrize('kind', ['preview', 'shared'])
@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
def test_composed_visual_change_replays_current_native_revision_without_new_author(
        database, monkeypatch, kind, tier):
    conn, _, _ = database
    _, request, _, state = _visual_harness(database, monkeypatch, tier=tier)
    app = _visual_application(kind)
    created = _H['_preview_http_post'](app, request)
    assert created.status_code == 200
    first, before = created.json(), _stored(conn)
    _H['_no_author'](monkeypatch)
    updated = _visual_patch(app, first, tier)
    assert updated.status_code == 200, updated.text
    assert updated.headers['cache-control'] == 'no-store'
    if kind == 'shared':
        assert updated.headers['x-cocolon-contract-id'] == 'emotion.piece.preview.visual.v2'
    latest, after = updated.json(), _stored(conn)
    assert latest['preview_revision'] == latest['row_version'] == 2
    changed = {'visual_recipe', 'visual_recipe_hash', 'preview_revision', 'row_version', 'updated_at'}
    assert {k: v for k, v in after.items() if k not in changed} == {
        k: v for k, v in before.items() if k not in changed}
    assert {k: v for k, v in latest.items() if k not in changed} == {
        k: v for k, v in first.items() if k not in changed}
    assert after['visual_recipe'] == latest['visual_recipe']
    assert latest['visual_recipe']['theme']['theme_id'] == ('soft_paper' if tier == 'free' else 'quiet_night')
    assert latest['visual_recipe']['aspect_ratio'] == ('9:16' if tier == 'premium' else '4:5')
    assert latest['visual_recipe']['branding']['branding_mode'] == (
        'off' if tier == 'premium' else 'required_small' if tier == 'free' else 'required_subtle')
    assert state['authors'] == state['http_rpc'] == state['visual_rpc'] == 1
    assert state['actual_reviews'] == 2

    stale = _visual_patch(app, first, tier)
    assert stale.status_code == 409 and stale.json() == {'code': 'PIECE_PREVIEW_STALE'}
    replay = _H['_preview_http_post'](_visual_application(kind), request)
    assert replay.status_code == 200 and replay.json() == latest
    assert _stored(conn) == after
    assert state['authors'] == state['http_rpc'] == state['visual_rpc'] == 1
    assert state['actual_reviews'] == 2
    assert conn.execute('SELECT count(*) FROM public.piece_records').fetchone() == (1,)
    assert _B5['_B4']['_used'](conn) == 0


@pytest.mark.parametrize('kind', ['preview', 'shared'])
@pytest.mark.parametrize('failure', ['stop_before_rpc', 'stop_after_commit', 'lost_ack'])
def test_composed_visual_unknown_outcome_recovers_same_native_record(
        database, monkeypatch, kind, failure):
    conn, _, _ = database
    _, request, _, state = _visual_harness(database, monkeypatch)
    app = _visual_application(kind)
    created = _H['_preview_http_post'](app, request)
    assert created.status_code == 200
    first, before = created.json(), _stored(conn)
    _H['_no_author'](monkeypatch)
    if failure == 'stop_before_rpc':
        original_review = _H['review'].review_prepared_original
        async def stop_after_review(candidate):
            result = await original_review(candidate)
            app.state.piece_v2_runtime = {}
            return result
        monkeypatch.setattr(_H['review'], 'review_prepared_original', stop_after_review)
    elif failure == 'stop_after_commit':
        state['visual_after_commit'] = lambda: setattr(app.state, 'piece_v2_runtime', {})
    else:
        state['visual_lose_ack'] = True
    failed = _visual_patch(app, first)
    assert failed.status_code == 503
    assert failed.json() == {'code': 'PIECE_TEMPORARILY_UNAVAILABLE'
        if failure == 'lost_ack' else 'PIECE_FEATURE_DISABLED'}
    assert failed.headers['cache-control'] == 'no-store'
    assert _B5['PRIVATE'] not in failed.text and first['piece_text'] not in failed.text
    committed = int(failure != 'stop_before_rpc')
    stored = _stored(conn)
    assert stored['preview_revision'] == stored['row_version'] == 1 + committed
    assert stored['piece_text'] == before['piece_text']
    assert stored['expires_at'] == before['expires_at']
    if not committed:
        assert stored == before
    replay = _H['_preview_http_post'](_visual_application(kind), request)
    assert replay.status_code == 200
    value = replay.json()
    assert value['preview_id'] == first['preview_id']
    assert value['preview_revision'] == 1 + committed
    assert value['visual_recipe'] == stored['visual_recipe']
    assert value['visual_recipe_hash'] == stored['visual_recipe_hash']
    assert value['piece_text'] == first['piece_text']
    assert _stored(conn) == stored
    assert state['visual_rpc'] == committed
    assert state['authors'] == state['http_rpc'] == 1
    assert state['actual_reviews'] == 2
    assert _B5['_B4']['_used'](conn) == 0


@pytest.mark.parametrize('kind', ['preview', 'shared'])
def test_composed_owner_reads_persisted_private_public_pages_without_generation(
        database, monkeypatch, kind):
    """Persist synthetic artifacts through real SQL/projection; Auth/HTTP are doubles."""
    import api_piece_v2 as api
    from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
    from piece_v2_source_adapter import PieceSavedSourceAdapter
    from piece_v2_runtime_control import PIECE_FEATURE_NAMES, piece_feature_flags_for_app
    h = runpy.run_path(str(Path(__file__).parents[1] / 'test_b07_piece_v2_owner_api.py'))
    conn, _, _ = database
    private = h['_native_save'](conn, visibility='private')
    public = h['_native_save'](conn, visibility='public')
    unsaved = h['_B5']['_issue'](conn, key='unsaved-owner-read')
    # The saved artifact remains readable without any source tables and even
    # when current entitlement cannot be resolved. No preview renderer/TTL.
    conn.execute("UPDATE public.profiles SET subscription_tier='unknown'")
    state = {'handler': None}
    h['_native_connect'](state, database)
    reads = []
    async def load(path, *, params, timeout):
        assert path == '/rest/v1/piece_records' and timeout == 8.0
        assert not (h['_FORBIDDEN_SELECT'] & set(params['select'].split(',')))
        reads.append(deepcopy(params))
        return state['handler'](params)
    async def verify(authorization):
        assert authorization in ('Bearer synthetic-owner', 'Bearer synthetic-viewer')
        return h['VIEWER'] if authorization.endswith('viewer') else h['OWNER']
    def forbidden(*args, **kwargs):
        pytest.fail('saved read may not author, inspect source/tier or write')
    monkeypatch.setattr(api, '_verify_bearer', verify)
    monkeypatch.setattr(supabase_client, 'sb_get', load)
    monkeypatch.setattr(supabase_client, 'sb_post_rpc', forbidden)
    monkeypatch.setattr(MeaningExperienceEngine, 'generate', forbidden)
    monkeypatch.setattr(PieceSavedSourceAdapter, 'resolve_original_handoff', forbidden)
    settings = dict(owner_read_requested=True, owner_read_ready=True)
    app = shared.create_application(piece_preview_configuration=settings) if kind == 'shared' else (
        create_piece_preview_application(**settings))
    assert piece_feature_flags_for_app(app) == {
        name: name == 'piece_v2_owner_read_enabled' for name in PIECE_FEATURE_NAMES}
    assert not hasattr(app.state, 'piece_preview_runtime')
    def get(path='history', *, params=None, viewer=False):
        async def call():
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                        base_url='http://piece-test.invalid') as client:
                return await client.get('/emotion/piece/' + path, params=params,
                    headers={'Authorization': 'Bearer synthetic-viewer' if viewer else 'Bearer synthetic-owner'})
        return asyncio.run(call())
    before = h['_native_state'](conn)
    expected = sorted([private, public], key=lambda row: (row['saved_at'], row['id']), reverse=True)
    first = get(params={'limit': '1'})
    assert first.status_code == 200 and first.json()['next_cursor']
    second = get(params={'limit': '1', 'cursor': first.json()['next_cursor']})
    assert second.status_code == 200 and second.json()['next_cursor'] is None
    for page, row in zip([first, second], expected):
        assert len(page.json()['items']) == 1
        h['_detail'](page.json()['items'][0], row)
        for identity in (row['id'], row['public_id']):
            detail = get(identity)
            assert detail.status_code == 200
            h['_detail'](detail.json(), row)
            assert detail.headers['cache-control'] == 'no-store'
            if kind == 'shared':
                assert detail.headers['x-cocolon-contract-id'] == 'emotion.piece.detail.v2'
    if kind == 'shared':
        assert first.headers['x-cocolon-contract-id'] == 'emotion.piece.history.v2'
    assert get(viewer=True).json()['items'] == []
    for row in (private, public):
        hidden = get(row['id'], viewer=True)
        assert hidden.status_code == 404 and hidden.json() == {'code': 'PIECE_NOT_FOUND'}
    assert get(unsaved['preview_id']).status_code == 404
    assert h['_native_state'](conn) == before
    # Stop after SQL returned the saved body. The HTTP boundary must suppress
    # that body, and subsequent reads must stop before database IO.
    original_handler = state['handler']
    def stop_after_read(params):
        result = original_handler(params)
        app.state.piece_v2_runtime['ready']['piece_v2_owner_read_enabled'] = False
        return result
    state['handler'] = stop_after_read
    stopped = get(private['id'])
    assert stopped.status_code == 503 and stopped.json() == {'code': 'PIECE_FEATURE_DISABLED'}
    assert private['piece_text'] not in stopped.text
    count = len(reads)
    assert get().status_code == 503 and len(reads) == count
    assert h['_native_state'](conn) == before
