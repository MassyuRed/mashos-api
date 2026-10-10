"""Prepared shared API -> real CMEE/review -> disposable native PostgreSQL.

Reuse the existing B5 fixture and its guarded disposable database unchanged.
Bearer, saved-source IO, active-user Auth and PostgREST transport are synthetic.
Generation, review, response projection and native SQL remain real. No live
service, real Auth, lifespan, RN/device or product acceptance is claimed here.
"""
from pathlib import Path
import runpy
import socket

import pytest

import app as shared
import middleware_active_user_touch as active_touch

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
