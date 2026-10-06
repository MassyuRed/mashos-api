"""New B5 persistence tests, not the previously blocked B5-B HTTP test file.

Reuse unchanged B2 canonical synthetic fixtures and B4 disposable native DB.
Safety/tier/source admission and renderer identity are synthetic inputs here,
NOT evidence of an authenticated API, real CMEE issuance or device acceptance.
"""
from __future__ import annotations

import asyncio
from copy import deepcopy
import hashlib
from pathlib import Path
import runpy
from uuid import UUID, uuid4

import pytest

_B4 = runpy.run_path(str(Path(__file__).with_name('test_b04_piece_v2_atomic_transactions.py')))
database = _B4['database']
_B2, _OWNER, _VIEWER = _B4['_B2'], _B4['_OWNER'], _B4['_VIEWER']
_KEYS = {'source_lineage', 'format_type', 'content_payload', 'content_payload_hash',
         'piece_text', 'piece_text_hash', 'safety_state', 'visual_recipe',
         'visual_recipe_hash', 'renderer_version'}


def _record(fmt='short_essay', state='ready'):
    source = _B2['_record'](fmt=fmt)
    value = {k: source[k] for k in _KEYS}
    value.update(safety_state=state, eligible_formats=[fmt])
    return value


def _args(record=None, key='synthetic-preview', fingerprint='a'*64, owner=_OWNER, ttl=600):
    from psycopg.types.json import Jsonb
    return dict(p_owner_user_id=owner, p_idempotency_key_hash=hashlib.sha256(key.encode()).hexdigest(),
                p_request_hash=fingerprint, p_record=Jsonb(record or _record()), p_ttl_seconds=ttl)


def _issue(conn, **kwargs):
    return _B4['_rpc'](conn, 'piece_issue_preview_v2', _args(**kwargs))


def _cancel_args(preview, owner=_OWNER, revision=1):
    return dict(p_owner_user_id=owner, p_preview_id=preview['preview_id'], p_expected_preview_revision=revision)


def _count(conn):
    return conn.execute('SELECT count(*) FROM public.piece_records').fetchone()[0]


@pytest.mark.parametrize('fmt', ['short_essay', 'quote', 'declaration'])
@pytest.mark.parametrize('state', ['ready', 'adjusted'])
def test_b05_native_issue_replay_and_exact_persisted_body(database, fmt, state):
    conn, _, _ = database
    record = _record(fmt, state)
    before = _B2['_legacy_identity'](conn)
    first = _issue(conn, record=record)
    second = _issue(conn, record=record, ttl=1200)
    assert first['idempotency_replayed'] is False and second['idempotency_replayed'] is True
    assert dict(first, idempotency_replayed=True) == second
    assert first['preview_revision'] == first['row_version'] == 1
    assert first['visibility_scope'] == 'private'
    for k, v in record.items():
        if k != 'source_lineage':
            assert first[k] == v
    assert 'source_lineage' not in first and 'owner_user_id' not in first
    assert conn.execute('SELECT piece_text,content_payload,visual_recipe FROM public.piece_records').fetchone() == (
        record['piece_text'], record['content_payload'], record['visual_recipe'])
    assert _count(conn) == 1 and _B4['_used'](conn) == 0
    assert conn.execute('SELECT count(*) FROM public.piece_quota_month_locks').fetchone() == (0,)
    assert conn.execute('SELECT count(*) FROM public.pieces_v2_staging').fetchone() == (0,)
    assert _B2['_legacy_identity'](conn) == before


@pytest.mark.parametrize('same_key,same_request', [(True, True), (True, False), (False, True)])
def test_b05_native_concurrent_request_identity(database, same_key, same_request):
    conn, pg, url = database
    calls = [('piece_issue_preview_v2', _args()),
             ('piece_issue_preview_v2', _args(key='synthetic-preview' if same_key else 'different',
                                            fingerprint='a'*64 if same_request else 'b'*64))]
    results = _B4['_parallel'](pg, url, calls)
    successes = [r for r in results if isinstance(r, dict)]
    if same_key and same_request:
        assert len(successes) == 2 and successes[0]['preview_id'] == successes[1]['preview_id']
        assert sorted(r['idempotency_replayed'] for r in successes) == [False, True]
        assert successes[0]['expires_at'] == successes[1]['expires_at']
        assert _count(conn) == 1
    elif same_key:
        assert len(successes) == 1 and results.count('PIECE_CONFLICT') == 1 and _count(conn) == 1
    else:
        assert len(successes) == 2 and successes[0]['preview_id'] != successes[1]['preview_id']
        assert _count(conn) == 2
    assert _B4['_used'](conn) == 0


def test_b05_native_owner_scope_and_source_owner_mismatch(database):
    conn, pg, _ = database
    first = _issue(conn)
    with pytest.raises(pg.errors.RaiseException, match='(?m)^PIECE_REQUEST_INVALID$'):
        _issue(conn, owner=_VIEWER)
    record = _record()
    record['source_lineage']['source_input']['source_owner_user_id'] = str(_VIEWER)
    second = _issue(conn, owner=_VIEWER, record=record)
    assert first['preview_id'] != second['preview_id'] and _count(conn) == 2
    for pid in (first['preview_id'], str(uuid4())):
        with pytest.raises(pg.errors.RaiseException, match='(?m)^PIECE_NOT_FOUND$'):
            _B4['_rpc'](conn, 'piece_cancel_preview_v2', _cancel_args({'preview_id': pid}, owner=_VIEWER))
    assert _B4['_used'](conn) == 0


@pytest.mark.parametrize('key,value', [('safety_state', 'unavailable'), ('raw_input', 'SYNTHETIC_RAW'),
    ('owner_user_id', str(_VIEWER)), ('visibility_scope', 'public'), ('save_limit', 999),
    ('eligible_formats', []), ('eligible_formats', ['short_essay', 'short_essay']),
    ('eligible_formats', ['question_answer']), ('piece_text_hash', '0'*64)])
def test_b05_native_invalid_candidate_no_effect(database, key, value):
    conn, pg, _ = database
    record = _record(); record[key] = value
    with pytest.raises(pg.errors.RaiseException, match='(?m)^PIECE_REQUEST_INVALID$'):
        _issue(conn, record=record)
    assert _count(conn) == 0 and _B4['_used'](conn) == 0


@pytest.mark.parametrize('field,value,code', [
    ('p_owner_user_id', None, 'PIECE_AUTH_REQUIRED'),
    ('p_idempotency_key_hash', None, 'PIECE_REQUEST_INVALID'),
    ('p_request_hash', 'bad', 'PIECE_REQUEST_INVALID'),
    ('p_ttl_seconds', 0, 'PIECE_REQUEST_INVALID'),
    ('p_ttl_seconds', None, 'PIECE_REQUEST_INVALID')])
def test_b05_native_invalid_identity_no_effect(database, field, value, code):
    conn, pg, _ = database
    args = _args(); args[field] = value
    with pytest.raises(pg.errors.RaiseException, match='(?m)^'+code+'$'):
        _B4['_rpc'](conn, 'piece_issue_preview_v2', args)
    assert _count(conn) == 0 and _B4['_used'](conn) == 0


def test_b05_native_expired_retry_never_extends_lifetime(database):
    conn, pg, _ = database
    p = _issue(conn)
    conn.execute("UPDATE public.piece_records SET expires_at=clock_timestamp()-interval '1 second'")
    before = conn.execute('SELECT expires_at,row_version FROM public.piece_records').fetchone()
    with pytest.raises(pg.errors.RaiseException, match='(?m)^PIECE_PREVIEW_EXPIRED$'):
        _issue(conn)
    with pytest.raises(pg.errors.RaiseException, match='(?m)^PIECE_PREVIEW_EXPIRED$'):
        _B4['_rpc'](conn, 'piece_cancel_preview_v2', _cancel_args(p))
    assert conn.execute('SELECT expires_at,row_version FROM public.piece_records').fetchone() == before
    assert _count(conn) == 1 and _B4['_used'](conn) == 0


def test_b05_native_cancel_concurrently_once_and_cannot_save_or_reissue(database):
    conn, pg, url = database
    p = _issue(conn)
    with pytest.raises(pg.errors.RaiseException, match='(?m)^PIECE_PREVIEW_STALE$'):
        _B4['_rpc'](conn, 'piece_cancel_preview_v2', _cancel_args(p, revision=2))
    results = _B4['_parallel'](pg, url, [('piece_cancel_preview_v2', _cancel_args(p))]*2)
    assert all(isinstance(r, dict) for r in results)
    assert sorted(r['idempotency_replayed'] for r in results) == [False, True]
    assert [r['row_version'] for r in results] == [2, 2]
    with pytest.raises(pg.errors.RaiseException, match='(?m)^PIECE_CONFLICT$'):
        _issue(conn)
    row = dict(p, id=UUID(p['preview_id']))
    with pytest.raises(pg.errors.RaiseException, match='(?m)^PIECE_CONFLICT$'):
        _B4['_save'](conn, row)
    assert _count(conn) == 1 and _B4['_used'](conn) == 0


def test_b05_native_issue_save_visibility_delete_and_retry_no_resurrection(database):
    conn, pg, _ = database
    p = _issue(conn)
    row = dict(p, id=UUID(p['preview_id']))
    first = _B4['_save'](conn, row)
    replay = _B4['_save'](conn, row)
    assert first['consumption_id'] == replay['consumption_id'] and _B4['_used'](conn) == 1
    assert conn.execute('SELECT piece_text,visual_recipe FROM public.piece_records').fetchone() == (p['piece_text'], p['visual_recipe'])
    # An actual same-value update does not fabricate a new row version.
    args = dict(p_owner_user_id=_OWNER, p_piece_id=p['preview_id'], p_expected_row_version=2, p_visibility_scope='private')
    for _ in range(2):
        assert _B4['_rpc'](conn, 'piece_set_visibility_v2', args)['row_version'] == 2
    for operation, args in [('piece_issue_preview_v2', _args()), ('piece_cancel_preview_v2', _cancel_args(p))]:
        with pytest.raises(pg.errors.RaiseException, match='(?m)^PIECE_CONFLICT$'):
            _B4['_rpc'](conn, operation, args)
    _B4['_rpc'](conn, 'piece_delete_v2', _B4['_delete_args'](row))
    with pytest.raises(pg.errors.RaiseException, match='(?m)^PIECE_CONFLICT$'):
        _issue(conn)
    assert _count(conn) == 0 and _B4['_used'](conn) == 1


def test_b05_native_permissions_and_failed_insert_rollback(database):
    conn, pg, _ = database
    signatures = ['public.piece_issue_preview_v2(uuid,text,text,jsonb,integer)',
                  'public.piece_cancel_preview_v2(uuid,uuid,bigint)']
    for signature in signatures:
        assert conn.execute('SELECT prosecdef,proconfig FROM pg_proc WHERE oid=%s::regprocedure', (signature,)).fetchone() == (True, ['search_path=pg_catalog'])
        for role in ('anon', 'authenticated', 'service_role'):
            assert conn.execute('SELECT has_function_privilege(%s,%s,%s)', (role, signature, 'EXECUTE')).fetchone() == (role == 'service_role',)
    for role in ('anon', 'authenticated'):
        with pytest.raises(pg.errors.InsufficientPrivilege):
            _B4['_rpc'](conn, 'piece_issue_preview_v2', _args(), role=role)
    conn.execute("CREATE FUNCTION public.synthetic_issue_failure() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'SYNTHETIC_INSERT_FAILURE'; END $$")
    conn.execute('CREATE TRIGGER synthetic_issue_failure BEFORE INSERT ON public.piece_records FOR EACH ROW EXECUTE FUNCTION public.synthetic_issue_failure()')
    with pytest.raises(pg.errors.RaiseException, match='SYNTHETIC_INSERT_FAILURE'):
        _issue(conn)
    assert _count(conn) == 0 and _B4['_used'](conn) == 0


def _adapter_kwargs(record=None):
    return dict(authenticated_user_id=str(_OWNER), record=record or _record(),
                request_fingerprint='a'*64, idempotency_key='synthetic-preview', ttl_seconds=600)


def test_b05_adapter_uses_native_rpc_then_cancels_without_raw_source_projection(database):
    from piece_v2_store import issue_piece_preview, cancel_piece_preview
    from psycopg.types.json import Jsonb
    conn, _, _ = database
    calls = []
    async def rpc(name, args):
        calls.append(name)
        bound = dict(args)
        if 'p_record' in bound:
            bound['p_record'] = Jsonb(bound['p_record'])
        return _B4['_rpc'](conn, name, bound)
    p = asyncio.run(issue_piece_preview(**_adapter_kwargs(), rpc=rpc))
    repeat = asyncio.run(issue_piece_preview(**_adapter_kwargs(), rpc=rpc))
    assert p['preview_id'] == repeat['preview_id'] and repeat['idempotency_replayed']
    cancelled = asyncio.run(cancel_piece_preview(authenticated_user_id=str(_OWNER), preview_id=p['preview_id'], expected_preview_revision=1, rpc=rpc))
    assert cancelled['lifecycle_status'] == 'cancelled'
    assert calls == ['piece_issue_preview_v2', 'piece_issue_preview_v2', 'piece_cancel_preview_v2']
    assert _count(conn) == 1 and _B4['_used'](conn) == 0


@pytest.mark.parametrize('field,value', [('raw_input', 'SYNTHETIC_FORBIDDEN'), ('safety_state', 'unavailable'),
    ('piece_text_hash', '0'*64), ('eligible_formats', ['short_essay', 'short_essay']),
    ('renderer_version', '/tmp/private.png'), ('content_payload_hash', '0'*64)])
def test_b05_adapter_rejects_invalid_candidate_before_io(field, value):
    from piece_v2_store import issue_piece_preview
    record = _record(); record[field] = value
    calls = []
    async def forbidden(*args):
        calls.append(args)
        raise AssertionError
    with pytest.raises(_B4['PieceContractError']) as rejected:
        asyncio.run(issue_piece_preview(**_adapter_kwargs(record), rpc=forbidden))
    assert rejected.value.code == 'PIECE_REQUEST_INVALID' and not calls


def test_b05_adapter_masks_provider_body_and_unknown_response():
    from piece_v2_store import issue_piece_preview
    async def error(*args):
        raise RuntimeError('SYNTHETIC_PROVIDER_PRIVATE_BODY')
    async def unexpected(*args):
        return {'raw_input': 'SYNTHETIC_PROVIDER_PRIVATE_BODY'}
    for rpc in (error, unexpected):
        with pytest.raises(_B4['PieceContractError']) as rejected:
            asyncio.run(issue_piece_preview(**_adapter_kwargs(), rpc=rpc))
        assert str(rejected.value) == 'PIECE_TEMPORARILY_UNAVAILABLE'
