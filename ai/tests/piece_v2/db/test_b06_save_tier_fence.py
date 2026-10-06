"""Server pre-save tier expectation -> B4 atomic save, not B6 HTTP completion.

Reuse the unchanged B4 disposable native database fixture. These tests do not
approve a candidate, change source/format policy, authenticate a real user or
claim deployed Supabase/RN coverage. Existing B2-B5 tests are unchanged.
"""
from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from queue import Queue
import runpy
import time
from uuid import uuid4

import pytest

_B4 = runpy.run_path(str(Path(__file__).with_name('test_b04_piece_v2_atomic_transactions.py')))
database = _B4['database']
_OWNER = _B4['_OWNER']
_preview, _args, _rpc, _used = (_B4[k] for k in ('_preview', '_args', '_rpc', '_used'))
from piece_v2_contract import PieceContractError
from piece_v2_store import save_piece


def _request(row):
    return {'preview_id': str(row['id']), 'expected_preview_revision': 1,
            'piece_text_hash': row['piece_text_hash'],
            'content_payload_hash': row['content_payload_hash'],
            'visual_recipe_hash': row['visual_recipe_hash']}


def _state(conn, row):
    return conn.execute('SELECT to_jsonb(r) FROM public.piece_records r WHERE id=%s',
                        (row['id'],)).fetchone()[0]


def _stub_request():
    return {'preview_id': str(uuid4()), 'expected_preview_revision': 1,
            'piece_text_hash': 'a'*64, 'content_payload_hash': 'b'*64,
            'visual_recipe_hash': 'c'*64}


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium', None])
def test_tier_fence_adapter_binds_only_internal_argument(tier):
    request, calls = _stub_request(), []
    async def rpc(name, args):
        calls.append((name, dict(args)))
        return {'piece_id': request['preview_id'], 'consumption_id': str(uuid4()),
                'lifecycle_status': 'saved', 'visibility_scope': 'private',
                'row_version': 2, 'saved_at': '2026-10-06T00:00:00+00:00',
                'idempotency_replayed': False}
    result = asyncio.run(save_piece(authenticated_user_id=str(_OWNER), request=request,
        idempotency_key='synthetic-fence', rpc=rpc, expected_subscription_tier=tier))
    assert len(calls) == 1 and calls[0][0] == 'piece_save_v2'
    args = calls[0][1]
    assert ('p_expected_subscription_tier' in args) == (tier is not None)
    if tier is not None:
        assert args['p_expected_subscription_tier'] == tier
    assert args['p_owner_user_id'] == str(_OWNER)
    assert result['visibility_scope'] == 'private' and not result['idempotency_replayed']


@pytest.mark.parametrize('tier', ['', 'unknown', 'Premium', True, 1, [], {}])
def test_tier_fence_adapter_rejects_invalid_expectation_before_io(tier):
    calls = []
    async def rpc(*args):
        calls.append(args)
        raise AssertionError('must not reach RPC')
    with pytest.raises(PieceContractError) as caught:
        asyncio.run(save_piece(authenticated_user_id=str(_OWNER), request=_stub_request(),
            idempotency_key='synthetic-fence', rpc=rpc, expected_subscription_tier=tier))
    assert caught.value.code == 'PIECE_REQUEST_INVALID' and calls == []


@pytest.mark.parametrize('field', ['subscription_tier', 'expected_subscription_tier',
                                    'p_expected_subscription_tier'])
def test_tier_fence_is_not_a_client_request_field(field):
    request, calls = _stub_request(), []
    request[field] = 'premium'
    async def rpc(*args):
        calls.append(args)
    with pytest.raises(PieceContractError) as caught:
        asyncio.run(save_piece(authenticated_user_id=str(_OWNER), request=request,
            idempotency_key='synthetic-fence', rpc=rpc, expected_subscription_tier='free'))
    assert caught.value.code == 'PIECE_REQUEST_INVALID' and calls == []


@pytest.mark.parametrize('current,expected', [
    ('free','plus'), ('free','premium'), ('plus','free'),
    ('plus','premium'), ('premium','free'), ('premium','plus'),
])
def test_tier_fence_native_changed_tier_has_no_save_or_quota_effect(database, current, expected):
    conn, pg, _ = database
    row = _preview(conn)
    conn.execute('UPDATE public.profiles SET subscription_tier=%s WHERE id=%s', (current,_OWNER))
    before, legacy = _state(conn,row), _B4['_B2']['_legacy_identity'](conn)
    args = _args(row)
    args['p_expected_subscription_tier'] = expected
    with pytest.raises(pg.errors.RaiseException) as caught:
        _rpc(conn, 'piece_save_v2', args)
    assert caught.value.diag.message_primary == 'PIECE_CONFLICT'
    assert _state(conn,row) == before and _used(conn) == 0
    assert conn.execute('SELECT count(*) FROM public.piece_quota_month_locks').fetchone() == (0,)
    assert _B4['_B2']['_legacy_identity'](conn) == legacy


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
def test_tier_fence_native_matching_tier_uses_database_quota_owner(database, tier):
    conn, _, _ = database
    row = _preview(conn)
    conn.execute('UPDATE public.profiles SET subscription_tier=%s WHERE id=%s', (tier,_OWNER))
    args = dict(_args(row), p_expected_subscription_tier=tier)
    result = _rpc(conn, 'piece_save_v2', args)
    assert result['lifecycle_status'] == 'saved' and _used(conn) == 1
    assert conn.execute('SELECT subscription_tier_at_consumption FROM public.piece_quota_consumptions').fetchone() == (tier,)
    for key in ('piece_text','piece_text_hash','content_payload_hash','visual_recipe_hash'):
        assert _state(conn,row)[key] == row[key]


@pytest.mark.parametrize('invalid', ['', 'unknown', 'PREMIUM'])
def test_tier_fence_native_invalid_expectation_is_not_a_grant(database, invalid):
    conn, pg, _ = database
    row = _preview(conn)
    before = _state(conn,row)
    with pytest.raises(pg.errors.RaiseException) as caught:
        _rpc(conn, 'piece_save_v2', dict(_args(row), p_expected_subscription_tier=invalid))
    assert caught.value.diag.message_primary == 'PIECE_REQUEST_INVALID'
    assert _state(conn,row) == before and _used(conn) == 0


def test_tier_fence_native_null_keeps_existing_low_level_quota_check(database):
    conn, pg, _ = database
    row = _preview(conn)
    _B4['_seed_usage'](conn,5)
    before = _state(conn,row)
    with pytest.raises(pg.errors.RaiseException) as caught:
        _rpc(conn, 'piece_save_v2', dict(_args(row), p_expected_subscription_tier=None))
    assert caught.value.diag.message_primary == 'PIECE_QUOTA_EXHAUSTED'
    assert _state(conn,row) == before and _used(conn) == 5


@pytest.mark.parametrize('stored_tier', [None, 'unknown'])
def test_tier_fence_native_unknown_database_tier_remains_free(database, stored_tier):
    conn, pg, _ = database
    row = _preview(conn)
    conn.execute('UPDATE public.profiles SET subscription_tier=%s WHERE id=%s', (stored_tier,_OWNER))
    with pytest.raises(pg.errors.RaiseException) as caught:
        _rpc(conn, 'piece_save_v2', dict(_args(row), p_expected_subscription_tier='premium'))
    assert caught.value.diag.message_primary == 'PIECE_CONFLICT' and _used(conn) == 0
    assert _rpc(conn, 'piece_save_v2', dict(_args(row), p_expected_subscription_tier='free'))['lifecycle_status'] == 'saved'
    assert _used(conn) == 1


def test_tier_fence_native_replay_after_downgrade_preserves_saved_record(database):
    conn, _, _ = database
    row = _preview(conn)
    conn.execute("UPDATE public.profiles SET subscription_tier='premium' WHERE id=%s", (_OWNER,))
    args = dict(_args(row), p_expected_subscription_tier='premium')
    first = _rpc(conn, 'piece_save_v2', args)
    before = _state(conn,row)
    conn.execute("UPDATE public.profiles SET subscription_tier='free' WHERE id=%s", (_OWNER,))
    second = _rpc(conn, 'piece_save_v2', args)
    assert second['idempotency_replayed'] and not first['idempotency_replayed']
    assert first['consumption_id'] == second['consumption_id']
    assert _state(conn,row) == before and _used(conn) == 1


@pytest.mark.parametrize('commit_change', [True, False])
def test_tier_fence_native_reads_profile_after_real_lock_wait(database, commit_change):
    conn, pg, url = database
    row = _preview(conn)
    conn.execute("UPDATE public.profiles SET subscription_tier='premium' WHERE id=%s", (_OWNER,))
    before = _state(conn,row)
    args = dict(_args(row), p_expected_subscription_tier='premium')
    worker_pid = Queue()
    def worker():
        with pg.connect(url, autocommit=True, connect_timeout=3) as other:
            other.execute("SET statement_timeout='8s'")
            worker_pid.put(other.info.backend_pid)
            try:
                return _rpc(other,'piece_save_v2',args)
            except pg.Error as exc:
                return exc.diag.message_primary
    pool = ThreadPoolExecutor(max_workers=1)
    try:
        conn.execute('BEGIN')
        conn.execute("UPDATE public.profiles SET subscription_tier='free' WHERE id=%s", (_OWNER,))
        future = pool.submit(worker)
        pid = worker_pid.get(timeout=5)
        deadline = time.monotonic()+5
        while True:
            blockers = conn.execute('SELECT pg_blocking_pids(%s)', (pid,)).fetchone()[0]
            if conn.info.backend_pid in blockers:
                break
            assert time.monotonic() < deadline, 'save never reached the held profile lock'
            time.sleep(0.01)
        assert not future.done()
        conn.execute('COMMIT' if commit_change else 'ROLLBACK')
        result = future.result(timeout=10)
        if commit_change:
            assert result == 'PIECE_CONFLICT'
            assert _state(conn,row) == before and _used(conn) == 0
        else:
            assert result['lifecycle_status'] == 'saved' and _used(conn) == 1
    finally:
        conn.execute('ROLLBACK')
        pool.shutdown(wait=True)


def test_tier_fence_native_adapter_binds_expectation_then_recovers_same_request(database):
    conn, pg, _ = database
    row = _preview(conn)
    before, calls = _state(conn,row), []
    async def transport(name,args):
        calls.append((name,dict(args)))
        try:
            return _rpc(conn,name,args)
        except pg.errors.RaiseException as exc:
            raise PieceContractError(exc.diag.message_primary) from None
    with pytest.raises(PieceContractError) as caught:
        asyncio.run(save_piece(authenticated_user_id=str(_OWNER), request=_request(row),
            idempotency_key='synthetic-fence', rpc=transport, expected_subscription_tier='premium'))
    assert caught.value.code == 'PIECE_CONFLICT'
    assert len(calls) == 1 and _state(conn,row) == before and _used(conn) == 0
    result = asyncio.run(save_piece(authenticated_user_id=str(_OWNER), request=_request(row),
        idempotency_key='synthetic-fence', rpc=transport, expected_subscription_tier='free'))
    assert result['lifecycle_status'] == 'saved' and _used(conn) == 1 and len(calls) == 2
