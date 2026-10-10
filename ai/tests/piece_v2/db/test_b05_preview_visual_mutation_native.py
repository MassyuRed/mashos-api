"""Issued-preview visual mutation against disposable native PostgreSQL.

Reuse the existing synthetic B6/Q3 handoff and B4 local-only database boundary.
These tests exercise SQL row/source fences, not live Auth, safety review, native
rendering, renderer admission, or production migration application.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from queue import Queue
import runpy
import time
from uuid import uuid4

import pytest

_CTX = runpy.run_path(str(Path(__file__).with_name('test_b06_save_context_fence.py')))
_B6, _B4, _ROOT = (_CTX[k] for k in ('_B6', '_B4', '_ROOT'))
database, harness = _CTX['database'], _CTX['harness']
OWNER, INPUT, THREAD, PRIVATE = (_CTX[k] for k in ('OWNER', 'INPUT', 'THREAD', 'PRIVATE'))
from piece_v2_contract import canonical_sha256_hex
from piece_v2_visual import build_visual_recipe

_MIGRATION = _ROOT / 'supabase/migrations/20261010050940_piece_v2_preview_visual_change.sql'
_FUNCTION = 'piece_mutate_preview_visual_v2'
_SIGNATURE = 'public.' + _FUNCTION + '(uuid,uuid,bigint,jsonb,jsonb,text,text,jsonb)'
_SNAPSHOT_FIELDS = {
    'id', 'owner_user_id', 'piece_contract_version', 'lifecycle_status',
    'preview_request_hash', 'preview_revision', 'row_version', 'expires_at',
    'visibility_scope', 'source_lineage', 'format_type', 'preview_eligible_formats',
    'content_payload', 'content_payload_hash', 'piece_text', 'piece_text_hash',
    'safety_state', 'visual_recipe', 'visual_recipe_hash', 'renderer_version',
}
_RESPONSE_FIELDS = {
    'preview_id', 'preview_revision', 'row_version', 'expires_at', 'visibility_scope',
    'format_type', 'eligible_formats', 'content_payload', 'content_payload_hash',
    'piece_text', 'piece_text_hash', 'safety_state', 'visual_recipe',
    'visual_recipe_hash', 'renderer_version', 'idempotency_replayed',
}
_CHANGED = {'visual_recipe', 'visual_recipe_hash', 'preview_revision', 'row_version', 'updated_at'}


def _row(conn):
    return conn.execute('SELECT to_jsonb(r) FROM public.piece_records r').fetchone()[0]


def _setup(database, harness, *, tier='plus', apply=True):
    _, state = _CTX['_fixture'](database, harness, tier=tier)
    conn, _, _ = database
    if apply:
        conn.execute(_MIGRATION.read_text())
    return state


def _args(conn, state, *, recipe=None):
    row = _row(conn)
    handoff = state['handoff']
    tier = handoff.original.subscription_tier
    if recipe is None:
        recipe = build_visual_recipe(row['format_type'], tier=tier,
            language=row['content_payload']['language'],
            theme='quiet_night' if tier != 'free' else None,
            aspect_ratio='9:16' if tier == 'premium' else None,
            branding='off' if tier == 'premium' else None)
    return dict(p_owner_user_id=OWNER, p_preview_id=row['id'],
        p_expected_preview_revision=row['preview_revision'],
        p_expected_record={key: row[key] for key in _SNAPSHOT_FIELDS},
        p_visual_recipe=recipe, p_visual_recipe_hash=canonical_sha256_hex(recipe),
        p_expected_subscription_tier=tier,
        p_expected_source_state={'original': handoff.original.original_payload(),
            'thread_id': THREAD, 'thread_revision': 1, 'lineage': handoff.lineage_payload()})


def _bound(args):
    from psycopg.types.json import Jsonb
    return {key: Jsonb(value) if key in ('p_expected_record', 'p_visual_recipe', 'p_expected_source_state')
            else value for key, value in args.items()}


def _mutate(conn, args, **kwargs):
    return _B4['_rpc'](conn, _FUNCTION, _bound(args), **kwargs)


def _no_quota(conn):
    assert _B4['_used'](conn) == 0
    assert conn.execute('SELECT count(*) FROM public.piece_quota_month_locks').fetchone() == (0,)
    assert conn.execute('SELECT count(*) FROM public.pieces_v2_staging').fetchone() == (0,)


def _reject(database, args, code):
    conn, pg, _ = database
    before = _row(conn)
    with pytest.raises(pg.errors.RaiseException) as error:
        _mutate(conn, args)
    assert error.value.diag.message_primary == code
    assert PRIVATE not in str(error.value)
    assert _row(conn) == before
    _no_quota(conn)


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
def test_visual_update_preserves_complete_body_identity_expiry_and_quota(database, harness, tier):
    state = _setup(database, harness, tier=tier)
    conn, _, _ = database
    before, legacy = _row(conn), _B4['_B2']['_legacy_identity'](conn)
    args = _args(conn, state)
    result = _mutate(conn, args)
    after = _row(conn)
    assert set(result) == _RESPONSE_FIELDS
    assert result['idempotency_replayed'] is False
    assert result['preview_revision'] == result['row_version'] == 2
    assert result['preview_id'] == before['id'] and result['expires_at'] == before['expires_at']
    assert after['visual_recipe'] == args['p_visual_recipe']
    assert after['visual_recipe_hash'] == args['p_visual_recipe_hash']
    assert after['updated_at'] > before['updated_at']
    assert {k: v for k, v in after.items() if k not in _CHANGED} == {
        k: v for k, v in before.items() if k not in _CHANGED}
    for key in ('piece_text', 'piece_text_hash', 'content_payload', 'content_payload_hash',
                'safety_state', 'renderer_version', 'format_type'):
        assert result[key] == before[key]
    assert result['eligible_formats'] == before['preview_eligible_formats']
    _no_quota(conn)
    assert _B4['_B2']['_legacy_identity'](conn) == legacy


def test_visual_concurrent_same_revision_updates_once_and_rejects_stale_retry(database, harness):
    state = _setup(database, harness)
    conn, pg, url = database
    args = _args(conn, state)
    results = _B4['_parallel'](pg, url, [(_FUNCTION, _bound(args))] * 2)
    assert len([r for r in results if isinstance(r, dict)]) == 1
    assert results.count('PIECE_PREVIEW_STALE') == 1
    assert _row(conn)['preview_revision'] == _row(conn)['row_version'] == 2
    _reject(database, args, 'PIECE_PREVIEW_STALE')


def test_visual_update_invalidates_old_save_revision_and_preserves_new_save_identity(database, harness):
    state = _setup(database, harness)
    conn, pg, _ = database
    before = _row(conn)
    _mutate(conn, _args(conn, state))
    with pytest.raises(pg.errors.RaiseException, match='(?m)^PIECE_PREVIEW_STALE$'):
        _B4['_save'](conn, before)
    _no_quota(conn)
    after = _row(conn)
    next_mutation = _args(conn, state)
    save_args = _B4['_args'](after)
    save_args['p_expected_preview_revision'] = 2
    saved = _B4['_rpc'](conn, 'piece_save_v2', save_args)
    assert saved['lifecycle_status'] == 'saved' and saved['row_version'] == 3
    assert _B4['_used'](conn) == 1
    assert _row(conn)['visual_recipe_hash'] == after['visual_recipe_hash']
    # Saved rows cannot be turned back into mutable previews.
    with pytest.raises(pg.errors.RaiseException, match='(?m)^PIECE_CONFLICT$'):
        _mutate(conn, next_mutation)
    assert _B4['_used'](conn) == 1


@pytest.mark.parametrize('cancel_first', [True, False])
def test_visual_cancel_serialization_and_current_revision(database, harness, cancel_first):
    state = _setup(database, harness)
    conn, pg, _ = database
    args = _args(conn, state)
    cancel = {k: args[k] for k in ('p_owner_user_id', 'p_preview_id', 'p_expected_preview_revision')}
    if cancel_first:
        _B4['_rpc'](conn, 'piece_cancel_preview_v2', cancel)
        _reject(database, args, 'PIECE_CONFLICT')
    else:
        _mutate(conn, args)
        with pytest.raises(pg.errors.RaiseException, match='(?m)^PIECE_PREVIEW_STALE$'):
            _B4['_rpc'](conn, 'piece_cancel_preview_v2', cancel)
        cancel['p_expected_preview_revision'] = 2
        assert _B4['_rpc'](conn, 'piece_cancel_preview_v2', cancel)['lifecycle_status'] == 'cancelled'
    _no_quota(conn)


@pytest.mark.parametrize('target', ['foreign-owner', 'unknown-preview', 'expired'])
def test_visual_owner_missing_and_expired_rows_are_unchanged(database, harness, target):
    state = _setup(database, harness)
    conn, _, _ = database
    args = _args(conn, state)
    code = 'PIECE_NOT_FOUND'
    if target == 'foreign-owner':
        args['p_owner_user_id'] = str(_B4['_VIEWER'])
    elif target == 'unknown-preview':
        args['p_preview_id'] = str(uuid4())
    else:
        conn.execute("UPDATE public.piece_records SET expires_at=clock_timestamp()-interval '1 second'")
        code = 'PIECE_PREVIEW_EXPIRED'
    _reject(database, args, code)


@pytest.mark.parametrize('field,value', [
    ('p_owner_user_id', None), ('p_preview_id', None), ('p_expected_preview_revision', 0),
    ('p_visual_recipe_hash', 'bad'), ('p_visual_recipe', None),
    ('p_expected_subscription_tier', None), ('p_expected_subscription_tier', 'unknown'),
    ('p_expected_source_state', None), ('p_expected_record', None),
])
def test_visual_malformed_arguments_have_no_effect(database, harness, field, value):
    state = _setup(database, harness)
    conn, _, _ = database
    args = _args(conn, state); args[field] = value
    _reject(database, args, 'PIECE_AUTH_REQUIRED' if field == 'p_owner_user_id' else 'PIECE_REQUEST_INVALID')


@pytest.mark.parametrize('change,code', [
    ('extra', 'PIECE_REQUEST_INVALID'), ('missing', 'PIECE_REQUEST_INVALID'),
    ('body', 'PIECE_CONFLICT'), ('renderer', 'PIECE_CONFLICT'),
    ('row-version', 'PIECE_CONFLICT'), ('expiry', 'PIECE_CONFLICT'),
    ('request-hash', 'PIECE_CONFLICT'), ('recipe', 'PIECE_CONFLICT'),
    ('format-recipe', 'PIECE_REQUEST_INVALID'), ('unknown-recipe-key', 'PIECE_REQUEST_INVALID'),
])
def test_visual_exact_snapshot_and_existing_recipe_constraints(database, harness, change, code):
    state = _setup(database, harness)
    conn, _, _ = database
    args = _args(conn, state)
    snapshot = args['p_expected_record']
    if change == 'extra': snapshot['raw_input'] = PRIVATE
    elif change == 'missing': del snapshot['safety_state']
    elif change == 'body': snapshot['piece_text'] += 'changed'
    elif change == 'renderer': snapshot['renderer_version'] += '.changed'
    elif change == 'row-version': snapshot['row_version'] += 1
    elif change == 'expiry': snapshot['expires_at'] = '2099-01-01T00:00:00Z'
    elif change == 'request-hash': snapshot['preview_request_hash'] = 'b' * 64
    elif change == 'recipe': snapshot['visual_recipe'] = args['p_visual_recipe']
    elif change == 'format-recipe': args['p_visual_recipe']['format_type'] = 'quote'
    else: args['p_visual_recipe']['client_extra'] = PRIVATE
    _reject(database, args, code)


def test_visual_snapshot_accepts_equivalent_expiry_timezone_spelling(database, harness):
    state = _setup(database, harness)
    conn, _, _ = database
    args = _args(conn, state)
    assert args['p_expected_record']['expires_at'].endswith('+00:00')
    args['p_expected_record']['expires_at'] = args['p_expected_record']['expires_at'][:-6] + 'Z'
    assert _mutate(conn, args)['preview_revision'] == 2
    _no_quota(conn)


def _change(conn, state, target):
    if target == 'preview':
        conn.execute('UPDATE public.piece_records SET preview_revision=preview_revision+1,row_version=row_version+1')
    elif target == 'original':
        conn.execute("UPDATE public.emotions SET memo='changed' WHERE id=%s", (INPUT,))
    elif target == 'profile':
        conn.execute("UPDATE public.profiles SET subscription_tier='free' WHERE id=%s", (OWNER,))
    elif target == 'thread':
        conn.execute('UPDATE public.emlis_input_threads SET revision=revision+1 WHERE id=%s', (THREAD,))
    elif target == 'history-source':
        conn.execute("UPDATE public.emotions SET memo='changed' WHERE id=%s", (state['history_id'],))
    elif target == 'history-thread':
        conn.execute('UPDATE public.emlis_input_threads SET revision=revision+1 WHERE id=%s', (state['history_thread_id'],))
    else:
        conn.execute("UPDATE public.emlis_frame_feedback SET version=version+1,status='REJECTED'")


def _wait_for_lock(conn, pid, deadline):
    while conn.info.backend_pid not in conn.execute('SELECT pg_blocking_pids(%s)', (pid,)).fetchone()[0]:
        assert time.monotonic() < deadline, 'mutation did not wait on the held row'
        time.sleep(.01)


def _waiting_call(database, args, hold, release, expected):
    """Observe a real blocker before releasing its transaction, not a sleep race."""
    conn, pg, url = database
    pids = Queue()
    def worker():
        with pg.connect(url, autocommit=True, connect_timeout=3) as other:
            other.execute("SET statement_timeout='8s'")
            pids.put(other.info.backend_pid)
            try:
                return _mutate(other, args)
            except pg.Error as exc:
                return exc.diag.message_primary
    pool = ThreadPoolExecutor(max_workers=1)
    try:
        conn.execute('BEGIN')
        hold()
        future = pool.submit(worker)
        pid, deadline = pids.get(timeout=5), time.monotonic() + 5
        _wait_for_lock(conn, pid, deadline)
        assert not future.done()
        release(pid, deadline)
        result = future.result(timeout=10)
        if expected is None:
            assert isinstance(result, dict) and result['preview_revision'] == 2
        else:
            assert result == expected
        assert PRIVATE not in str(result)
        _no_quota(conn)
        return result
    finally:
        conn.execute('ROLLBACK')
        pool.shutdown(wait=True)


@pytest.mark.parametrize('target', ['preview', 'original', 'profile', 'thread',
                                    'history-source', 'history-thread', 'feedback'])
@pytest.mark.parametrize('commit_change', [True, False])
def test_visual_waits_for_row_source_tier_and_consumed_context_commit_or_rollback(database, harness, target, commit_change):
    state = _setup(database, harness, tier='premium' if target == 'feedback' else 'plus')
    conn, _, _ = database
    before, args = _row(conn), _args(conn, state)
    expected = ('PIECE_PREVIEW_STALE' if target == 'preview' else 'PIECE_CONFLICT') if commit_change else None
    _waiting_call(database, args, lambda: _change(conn, state, target),
        lambda pid, deadline: conn.execute('COMMIT' if commit_change else 'ROLLBACK'), expected)
    if commit_change and target != 'preview':
        assert _row(conn) == before
    elif commit_change:
        after = _row(conn)
        assert {k: v for k, v in after.items() if k not in ('preview_revision', 'row_version')} == {
            k: v for k, v in before.items() if k not in ('preview_revision', 'row_version')}


@pytest.mark.parametrize('expiry', ['preview', 'history'])
def test_visual_postwait_clock_rejects_expiry_after_statement_start(database, harness, expiry):
    from psycopg.types.json import Jsonb
    state = _setup(database, harness)
    conn, _, _ = database
    if expiry == 'preview':
        conn.execute("UPDATE public.piece_records SET expires_at=clock_timestamp()+interval '1.5 seconds'")
        cutoff = conn.execute('SELECT expires_at FROM public.piece_records').fetchone()[0]
    else:
        conn.execute("UPDATE public.emotions SET created_at=clock_timestamp() AT TIME ZONE 'UTC' "
            "-interval '365 days'+interval '1.5 seconds' WHERE id=%s", (state['history_id'],))
        original = conn.execute('SELECT public.emlis_parent_source(e) FROM public.emotions e WHERE id=%s',
            (state['history_id'],)).fetchone()[0]
        conn.execute('UPDATE public.emlis_input_threads SET source_snapshot=%s WHERE id=%s',
            (Jsonb(original), state['history_thread_id']))
        context = conn.execute('SELECT public.emlis_thread_context(%s,%s)', (OWNER, INPUT)).fetchone()[0]
        assert len(context['history']) == 1
        data = dict(state['q3_data'], context_guards=[h['guard'] for h in context['history']])
        conn.execute('UPDATE public.emlis_input_threads SET data=%s WHERE id=%s', (Jsonb(data), THREAD))
        cutoff = conn.execute("SELECT created_at AT TIME ZONE 'UTC'+interval '365 days' "
            'FROM public.emotions WHERE id=%s', (state['history_id'],)).fetchone()[0]
    before, args = _row(conn), _args(conn, state)
    def hold():
        conn.execute('SELECT id FROM public.profiles WHERE id=%s FOR UPDATE', (OWNER,))
    def release(pid, deadline):
        assert conn.execute('SELECT query_start < %s FROM pg_stat_activity WHERE pid=%s',
            (cutoff, pid)).fetchone() == (True,)
        while not conn.execute('SELECT clock_timestamp() > %s', (cutoff,)).fetchone()[0]:
            assert time.monotonic() < deadline, 'fixture lifetime did not expire'
            time.sleep(.01)
        conn.execute('COMMIT')
    _waiting_call(database, args, hold, release,
        'PIECE_PREVIEW_EXPIRED' if expiry == 'preview' else 'PIECE_CONFLICT')
    assert _row(conn) == before


def test_visual_service_only_acl_preexisting_target_and_failed_update_rollback(database, harness):
    state = _setup(database, harness, apply=False)
    conn, pg, _ = database
    before_acl = conn.execute("SELECT oid,relacl,relrowsecurity,relforcerowsecurity FROM pg_class "
        "WHERE relnamespace='public'::regnamespace AND relkind IN ('r','v') ORDER BY oid").fetchall()
    conn.execute('ALTER DEFAULT PRIVILEGES GRANT EXECUTE ON FUNCTIONS TO authenticated')
    conn.execute(_MIGRATION.read_text())
    assert conn.execute("SELECT oid,relacl,relrowsecurity,relforcerowsecurity FROM pg_class "
        "WHERE relnamespace='public'::regnamespace AND relkind IN ('r','v') ORDER BY oid").fetchall() == before_acl
    assert conn.execute('SELECT prosecdef,proconfig FROM pg_proc WHERE oid=%s::regprocedure',
        (_SIGNATURE,)).fetchone() == (True, ['search_path=pg_catalog'])
    for role in ('anon', 'authenticated', 'service_role'):
        assert conn.execute('SELECT has_function_privilege(%s,%s,%s)',
            (role, _SIGNATURE, 'EXECUTE')).fetchone() == (role == 'service_role',)
    args = _args(conn, state)
    for role in ('anon', 'authenticated'):
        with pytest.raises(pg.errors.InsufficientPrivilege):
            _mutate(conn, args, role=role)
    with pytest.raises(pg.errors.RaiseException, match='(?m)^PIECE_PREVIEW_VISUAL_TARGET_EXISTS$'):
        conn.execute(_MIGRATION.read_text())
    before = _row(conn)
    conn.execute("CREATE FUNCTION public.synthetic_visual_failure() RETURNS trigger LANGUAGE plpgsql "
        "AS $$ BEGIN RAISE EXCEPTION 'SYNTHETIC_UPDATE_FAILURE'; END $$")
    conn.execute('CREATE TRIGGER synthetic_visual_failure BEFORE UPDATE ON public.piece_records '
        'FOR EACH ROW EXECUTE FUNCTION public.synthetic_visual_failure()')
    with pytest.raises(pg.errors.RaiseException, match='SYNTHETIC_UPDATE_FAILURE'):
        _mutate(conn, args)
    assert _row(conn) == before
    _no_quota(conn)
