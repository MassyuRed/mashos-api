"""Existing preview application -> real CMEE/review/store/disposable PostgreSQL.

Reuse the B5 HTTP fixture without changing its assertions or source setup. Its
Bearer verification, saved-source reads and PostgREST transport are synthetic;
CMEE, B9, review, orchestration, response projection and PostgreSQL are not.
This is not a deployed service, real Auth, RN/device or product acceptance.
"""
from __future__ import annotations

import asyncio
from pathlib import Path
import runpy

import httpx
import pytest

from piece_v2_runtime_control import create_piece_preview_application

_H = runpy.run_path(str(Path(__file__).with_name('test_b05_reviewed_preview_issuance.py')))
_B5 = _H['_B5']
database = _H['database']
_RUNTIME = {'ttl_seconds': 600, 'renderer_version': 'synthetic-renderer.v1'}


def _application(*, enabled=True):
    # These are existing fixture values, not admitted deployment settings.
    return create_piece_preview_application(
        preview_requested=enabled, preview_ready=enabled,
        preview_runtime=dict(_RUNTIME))


def _harness(database, monkeypatch, **options):
    # The prior fixture constructs an unserved reference app. Only the existing
    # factory's new app below receives requests; no routes are copied/modified.
    _, owner, request, prepared, state = _H['_preview_http_harness'](
        database, monkeypatch, **options)
    return _application(), owner, request, prepared, state


def _post(app, request):
    return _H['_preview_http_post'](app, request)


def _bootstrap(app):
    async def get():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                    base_url='http://piece-test.invalid') as client:
            return await client.get('/app/bootstrap')
    return asyncio.run(get())


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
@pytest.mark.parametrize('named', [False, True], ids=['ready', 'role-transformed'])
def test_composed_application_generates_persists_and_replays_exact_body(
        database, monkeypatch, tier, named):
    conn, _, _ = database
    app, _, request, prepared, state = _harness(
        database, monkeypatch, tier=tier, named=named)
    assert {(r.path, tuple(sorted(r.methods))) for r in app.routes} == {
        ('/app/bootstrap', ('GET',)), ('/app/startup', ('GET',)),
        ('/emotion/piece/source-ref/{saved_input_id}', ('GET',)),
        ('/emotion/piece/preview', ('POST',)),
    }
    bootstrap = _bootstrap(app)
    assert bootstrap.status_code == 200
    flags = {k: v for k, v in bootstrap.json()['feature_flags'].items()
             if k.startswith('piece_v2_')}
    assert len(flags) == 8 and flags.pop('piece_v2_preview_enabled') is True
    assert not any(flags.values())

    first = _post(app, request)
    assert first.status_code == 200
    assert first.headers['cache-control'] == 'no-store'
    value = first.json()
    assert value['content_status'] == ('adjusted' if named else 'ready')
    for field in ('piece_text', 'piece_text_hash', 'content_payload',
                  'content_payload_hash', 'visual_recipe', 'visual_recipe_hash'):
        assert value[field] == prepared.artifact_payload()[field]
    assert not ({'source_lineage', 'owner_user_id', 'safety_state',
                 'idempotency_replayed'} & set(value))
    stored = conn.execute('SELECT to_jsonb(r) FROM public.piece_records r').fetchone()[0]
    assert stored['piece_text'] == value['piece_text']
    assert stored['content_payload'] == value['content_payload']
    assert stored['visual_recipe'] == value['visual_recipe']
    assert state['authors'] == state['actual_reviews'] == state['http_rpc'] == 1

    _H['_no_author'](monkeypatch)
    replay = _post(_application(), request)
    assert replay.status_code == 200 and replay.json() == value
    assert conn.execute('SELECT to_jsonb(r) FROM public.piece_records r').fetchone()[0] == stored
    assert conn.execute('SELECT count(*) FROM public.piece_records').fetchone() == (1,)
    assert state['authors'] == state['actual_reviews'] == state['http_rpc'] == 1
    assert _B5['_B4']['_used'](conn) == 0


def test_composed_off_state_never_generates_or_persists(database, monkeypatch):
    conn, _, _ = database
    _, _, request, _, state = _harness(database, monkeypatch)
    app = _application(enabled=False)
    flags = _bootstrap(app).json()['feature_flags']
    assert not any(v for k, v in flags.items() if k.startswith('piece_v2_'))
    result = _post(app, request)
    assert result.status_code == 503 and result.json() == {'code': 'PIECE_FEATURE_DISABLED'}
    assert state['authors'] == state['actual_reviews'] == state['http_rpc'] == 0
    assert conn.execute('SELECT count(*) FROM public.piece_records').fetchone() == (0,)
    assert _B5['_B4']['_used'](conn) == 0


def test_composed_stop_after_actual_review_prevents_native_write(database, monkeypatch):
    conn, _, _ = database
    app, _, request, _, state = _harness(database, monkeypatch)
    review = _H['review']
    actual_review = review.review_prepared_original

    async def review_then_stop(candidate):
        verdict = await actual_review(candidate)
        app.state.piece_v2_runtime = {}
        return verdict

    monkeypatch.setattr(review, 'review_prepared_original', review_then_stop)
    result = _post(app, request)
    assert result.status_code == 503 and result.json() == {'code': 'PIECE_FEATURE_DISABLED'}
    assert state['authors'] == state['actual_reviews'] == 1
    assert state['http_rpc'] == 0 and not state['posts']
    assert conn.execute('SELECT count(*) FROM public.piece_records').fetchone() == (0,)
    assert _B5['_B4']['_used'](conn) == 0


def test_composed_lost_ack_replays_native_row_without_second_generation(database, monkeypatch):
    conn, _, _ = database
    app, _, request, _, state = _harness(database, monkeypatch)
    state['lose_ack'] = True
    lost = _post(app, request)
    assert lost.status_code == 503
    assert lost.json() == {'code': 'PIECE_TEMPORARILY_UNAVAILABLE'}
    assert state['authors'] == state['actual_reviews'] == state['http_rpc'] == 1
    stored = conn.execute('SELECT to_jsonb(r) FROM public.piece_records r').fetchone()[0]
    _H['_no_author'](monkeypatch)
    state['lose_ack'] = False
    replay = _post(_application(), request)
    assert replay.status_code == 200 and replay.json()['piece_text'] == stored['piece_text']
    assert conn.execute('SELECT to_jsonb(r) FROM public.piece_records r').fetchone()[0] == stored
    assert conn.execute('SELECT count(*) FROM public.piece_records').fetchone() == (1,)
    assert state['authors'] == state['actual_reviews'] == state['http_rpc'] == 1
    assert _B5['_B4']['_used'](conn) == 0


def test_composed_application_does_not_approve_hash_consistent_meaning_change(database, monkeypatch):
    conn, _, _ = database
    app, owner, request, prepared, state = _harness(database, monkeypatch)
    blocks = [b.replace('大切にしていない', '大切にしている')
              for b in prepared.artifact_payload()['content_payload']['body_blocks']]
    altered = _H['_changed'](prepared, blocks=blocks)
    assert altered._artifact_json != prepared._artifact_json

    async def altered_preparation(*args):
        return altered

    monkeypatch.setattr(owner, 'prepare_original', altered_preparation)
    result = _post(app, request)
    assert result.status_code == 422 and result.json() == {'code': 'PIECE_SAFETY_UNAVAILABLE'}
    assert state['actual_reviews'] == 1 and state['http_rpc'] == 0
    assert conn.execute('SELECT count(*) FROM public.piece_records').fetchone() == (0,)
    assert _B5['_B4']['_used'](conn) == 0


@pytest.mark.parametrize('change_at', [1, 2, 3])
def test_composed_source_change_never_becomes_success(database, monkeypatch, change_at):
    conn, _, _ = database
    app, _, request, _, state = _harness(database, monkeypatch)
    state['change_at'] = change_at
    result = _post(app, request)
    assert result.status_code == 409 and result.json() == {'code': 'PIECE_CONFLICT'}
    assert state['http_rpc'] == 0 and not state['posts']
    assert conn.execute('SELECT count(*) FROM public.piece_records').fetchone() == (0,)
    assert _B5['_B4']['_used'](conn) == 0
