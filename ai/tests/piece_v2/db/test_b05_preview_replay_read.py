"""Restart read of actual CMEE/B9 persisted previews; no live Auth or PCE-4 claim.

Reuses the unchanged issuance fixture with an explicitly synthetic reviewer.
Native SELECT reads the issued record; source/Auth remain existing test doubles.
Optimistic repeat reads are NOT a transactionally locked snapshot.
"""
from __future__ import annotations

import asyncio
from copy import deepcopy
from pathlib import Path
import runpy
import sys
from types import SimpleNamespace

import pytest

_G = runpy.run_path(str(Path(__file__).with_name('test_b05_generated_preview_issuance.py')))
database = _G['database']
service = _G['service']
PieceContractError = _G['PieceContractError']
OWNER, INPUT, AUTH = _G['OWNER'], _G['INPUT'], _G['AUTH']
KEY = 'synthetic-generated-preview'
PRIVATE = 'SYNTHETIC_PRIVATE_REPLAY_ERROR'


def _persist(database, monkeypatch, tier='free', named=False):
    conn, _, _ = database
    owner, request, prepared, review, state = _G['_setup'](monkeypatch, tier=tier, named=named)
    first = _G['_issue'](owner, request, prepared, review, state, _G['_native_rpc'](conn, state))
    # A fresh service receives no prepared object, candidate, text or reviewer.
    restarted = service.PiecePreviewService(source_adapter=owner._source_adapter)
    state['checks'] = 0
    state['reads'] = []

    async def load_record(owner_id, preview_id):
        assert owner_id == OWNER
        state['reads'].append((owner_id, preview_id))
        row = conn.execute('SELECT to_jsonb(r) FROM (SELECT ' +
            ','.join(service._REPLAY_COLUMNS) +
            ' FROM public.piece_records WHERE id=%s AND owner_user_id=%s) r',
            (preview_id, owner_id)).fetchone()
        return deepcopy(row[0]) if row else None

    return restarted, request, first, state, load_record


def _read(owner, request, load_record, key=KEY):
    return asyncio.run(owner.read_original_preview(AUTH, request,
        idempotency_key=key, load_record=load_record))


def _assert_no_effect(conn, state):
    assert len(state['posts']) == 1 and state['reviews'] == 1
    assert _G['_B4']['_used'](conn) == 0


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
@pytest.mark.parametrize('named', [False, True])
def test_fresh_service_reads_same_bundle_without_prepared_object_or_author(database, monkeypatch, tier, named):
    conn, _, _ = database
    owner, request, first, state, load = _persist(database, monkeypatch, tier, named)
    before = conn.execute('SELECT to_jsonb(r) FROM public.piece_records r').fetchone()[0]
    result = _read(owner, request, load)
    assert result == dict(first, idempotency_replayed=True)
    assert conn.execute('SELECT to_jsonb(r) FROM public.piece_records r').fetchone()[0] == before
    assert state['checks'] == 2 and len(state['reads']) == 2
    assert 'source_lineage' not in result and 'owner_user_id' not in result
    assert 'preview_request_hash' not in result and INPUT not in str(result)
    _assert_no_effect(conn, state)


def test_missing_key_never_generates_or_inserts(database, monkeypatch):
    conn, _, _ = database
    owner, request, first, state, load = _persist(database, monkeypatch)
    with pytest.raises(PieceContractError) as error:
        _read(owner, request, load, key='different-unissued-key')
    assert error.value.code == 'PIECE_NOT_FOUND'
    assert len(state['reads']) == 1
    assert conn.execute('SELECT count(*) FROM public.piece_records').fetchone() == (1,)
    _assert_no_effect(conn, state)


@pytest.mark.parametrize('kind,code', [
    ('cancelled', 'PIECE_CONFLICT'), ('saved', 'PIECE_CONFLICT'),
    ('expired', 'PIECE_PREVIEW_EXPIRED'), ('owner', 'PIECE_NOT_FOUND'),
    ('id', 'PIECE_NOT_FOUND'), ('request', 'PIECE_CONFLICT'),
    ('lineage', 'PIECE_CONFLICT'), ('text', 'PIECE_HASH_MISMATCH'),
    ('recipe', 'PIECE_HASH_MISMATCH'), ('safety', 'PIECE_SAFETY_UNAVAILABLE'),
    ('version', 'PIECE_NOT_FOUND'), ('visibility', 'PIECE_CONFLICT'),
    ('naive-time', 'PIECE_TEMPORARILY_UNAVAILABLE'),
])
def test_nonreplayable_or_corrupt_rows_are_not_success(database, monkeypatch, kind, code):
    conn, _, _ = database
    owner, request, first, state, load = _persist(database, monkeypatch)
    async def changed(owner_id, preview_id):
        row = await load(owner_id, preview_id)
        if kind in ('cancelled', 'saved'):
            row['lifecycle_status'] = kind
        elif kind == 'expired':
            row['expires_at'] = '2000-01-01T00:00:00+00:00'
        elif kind in ('owner', 'id'):
            row['owner_user_id' if kind == 'owner' else 'id'] = '11111111-1111-1111-1111-111111111111'
        elif kind == 'request':
            row['preview_request_hash'] = '0' * 64
        elif kind == 'lineage':
            row['source_lineage']['source_input']['source_input_bundle_commitment'] = 'sha256:' + '0' * 64
        elif kind == 'text':
            row['piece_text'] = PRIVATE
        elif kind == 'recipe':
            row['visual_recipe_hash'] = '0' * 64
        elif kind == 'safety':
            row['safety_state'] = 'unavailable'
        elif kind == 'version':
            row['piece_contract_version'] = 'legacy'
        elif kind == 'visibility':
            row['visibility_scope'] = 'public'
        elif kind == 'naive-time':
            row['expires_at'] = '2099-01-01T00:00:00'
        return row
    with pytest.raises(PieceContractError) as error:
        _read(owner, request, changed)
    assert error.value.code == code and PRIVATE not in str(error.value)
    _assert_no_effect(conn, state)


@pytest.mark.parametrize('change_at', [1, 2])
def test_source_change_during_either_revalidation_is_rejected(database, monkeypatch, change_at):
    conn, _, _ = database
    owner, request, _, state, load = _persist(database, monkeypatch)
    state['change_at'] = change_at
    with pytest.raises(PieceContractError) as error:
        _read(owner, request, load)
    assert error.value.code == 'PIECE_CONFLICT'
    _assert_no_effect(conn, state)


@pytest.mark.parametrize('change', ['deleted', 'cancelled', 'revision', 'expired'])
def test_record_change_between_reads_is_never_a_replayed_success(database, monkeypatch, change):
    conn, _, _ = database
    owner, request, _, state, load = _persist(database, monkeypatch)
    async def changed(owner_id, preview_id):
        row = await load(owner_id, preview_id)
        if len(state['reads']) == 2:
            if change == 'deleted':
                return None
            if change == 'cancelled':
                row['lifecycle_status'] = 'cancelled'
            if change == 'revision':
                row['row_version'] += 1
            if change == 'expired':
                row['expires_at'] = '2000-01-01T00:00:00+00:00'
        return row
    with pytest.raises(PieceContractError) as error:
        _read(owner, request, changed)
    assert error.value.code == ('PIECE_NOT_FOUND' if change == 'deleted' else 'PIECE_CONFLICT')
    _assert_no_effect(conn, state)


def test_request_is_copied_before_any_read_can_mutate_it(database, monkeypatch):
    conn, _, _ = database
    owner, request, first, state, load = _persist(database, monkeypatch)
    async def mutating(owner_id, preview_id):
        request['visual_selection']['theme_id'] = PRIVATE
        return await load(owner_id, preview_id)
    assert _read(owner, request, mutating) == dict(first, idempotency_replayed=True)
    _assert_no_effect(conn, state)


@pytest.mark.parametrize('failure', ['exception', 'contract', 'cancel'])
def test_loader_failures_do_not_leak_retry_or_write(database, monkeypatch, failure):
    conn, _, _ = database
    owner, request, _, state, _ = _persist(database, monkeypatch)
    calls = []
    async def broken(*args):
        calls.append(args)
        if failure == 'cancel':
            raise asyncio.CancelledError()
        if failure == 'contract':
            raise PieceContractError('UNEXPECTED_PRIVATE_CODE', PRIVATE)
        raise RuntimeError(PRIVATE)
    with pytest.raises(asyncio.CancelledError if failure == 'cancel' else PieceContractError) as error:
        _read(owner, request, broken)
    assert len(calls) == 1
    if failure != 'cancel':
        assert error.value.code == 'PIECE_TEMPORARILY_UNAVAILABLE'
        assert PRIVATE not in str(error.value)
    _assert_no_effect(conn, state)


@pytest.mark.parametrize('status,rows,failed', [
    (200, [], False), (200, [{'synthetic': 1}], False),
    (200, [{}, {}], True), (200, {}, True), (403, [], True), (500, {'secret': PRIVATE}, True),
])
def test_default_loader_uses_owner_and_id_filters_without_writes(monkeypatch, status, rows, failed):
    calls = []
    async def get(path, *, params, timeout):
        calls.append((path, params, timeout))
        return SimpleNamespace(status_code=status, json=lambda: deepcopy(rows))
    monkeypatch.setitem(sys.modules, 'supabase_client', SimpleNamespace(sb_get=get))
    pid = '22222222-2222-2222-2222-222222222222'
    action = service._load_owned_preview_for_replay(OWNER, pid)
    if failed:
        with pytest.raises(PieceContractError) as error:
            asyncio.run(action)
        assert error.value.code == 'PIECE_TEMPORARILY_UNAVAILABLE'
    else:
        assert asyncio.run(action) == (rows[0] if rows else None)
    assert calls == [('/rest/v1/piece_records', {
        'select': ','.join(service._REPLAY_COLUMNS), 'id': 'eq.' + pid,
        'owner_user_id': 'eq.' + OWNER, 'limit': '2'}, 8.0)]
