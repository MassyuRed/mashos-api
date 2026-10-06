"""B6 Q3 save-context fence against real isolated PostgreSQL transactions.

Auth, admitted preview, and source-adapter handoff are synthetic. The unchanged
Q2/Q3 migrations and candidate M4 execute natively in a disposable DB. These
checks do not claim production safety issuance, CMEE quality, or device coverage.
Normal Q3 thread/feedback writers serialize through profiles FOR UPDATE; the
missing-history-thread case covers that protocol, not arbitrary SQL phantoms.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from pathlib import Path
from queue import Queue
import runpy
import time
from uuid import uuid4

import pytest

_B6 = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'test_b06_piece_v2_save_api.py'))
_B4, _ROOT = _B6['_B4'], _B6['_ROOT']
database, harness = _B6['database'], _B6['harness']
OWNER, INPUT, THREAD, PRIVATE = (_B6[key] for key in ('OWNER', 'INPUT', 'THREAD', 'PRIVATE'))


def _history(conn, *, hours=48, with_thread=True):
    """An earlier source; SQL builds its exact timestamp/hash guard."""
    from psycopg.types.json import Jsonb
    source_id, thread_id = str(uuid4()), str(uuid4())
    conn.execute("INSERT INTO public.emotions(id,user_id,created_at,memo,category,emotions,emotion_details) "
        "SELECT %s,%s,created_at-(%s * interval '1 hour'),%s,'[]','[]','[]' FROM public.emotions WHERE id=%s",
        (source_id, OWNER, hours, PRIVATE, INPUT))
    original = conn.execute('SELECT public.emlis_parent_source(e) FROM public.emotions e WHERE id=%s',
        (source_id,)).fetchone()[0]
    if with_thread:
        conn.execute("INSERT INTO public.emlis_input_threads(id,user_id,original_emotion_id,revision,state,issued_count,source_snapshot,data) "
            "VALUES(%s,%s,%s,1,'COMPLETED',0,%s,'{}')", (thread_id, OWNER, source_id, Jsonb(original)))
    return source_id, thread_id, original


def _fixture(database, harness, *, tier='plus', history_thread=True):
    from psycopg.types.json import Jsonb
    _, state = harness
    state['row'] = _B6['_row'](tier)
    state['handoff'] = _B6['_handoff'](state['row'], tier)
    call, state = _B6['_native'](harness, database)
    conn, _, _ = database
    conn.execute((_ROOT / 'supabase/migrations/20260911041749_emlis_q3_plan_rounds.sql').read_text())
    conn.execute('UPDATE public.profiles SET subscription_tier=%s WHERE id=%s', (tier, OWNER))
    state['handoff'] = _B6['_handoff'](state['row'], tier,
        original=state['handoff'].original.original_payload())
    source_id, history_thread_id, original = _history(conn, with_thread=history_thread)
    if tier == 'premium':
        conn.execute("INSERT INTO public.emlis_frame_feedback(user_id,source_emotion_id,frame_key,frame_ref,status) "
            "VALUES(%s,%s,'synthetic-frame','synthetic-ref','CONFIRMED')", (OWNER, source_id))
    context = conn.execute('SELECT public.emlis_thread_context(%s,%s)', (OWNER, INPUT)).fetchone()[0]
    data = {'runtime_profile': 'q3.plan.sequential.v1', 'evaluated_tier': tier,
        'context_guards': [h['guard'] for h in context['history']],
        'context_feedback': [[f['frame_key'], f['version']] for f in context['feedback']]}
    conn.execute('UPDATE public.emlis_input_threads SET data=%s WHERE id=%s', (Jsonb(data), THREAD))
    state.update(history_id=source_id, history_thread_id=history_thread_id,
        history_original=original, q3_data=data)
    return call, state


def _piece_state(conn):
    return (conn.execute('SELECT to_jsonb(r) FROM public.piece_records r ORDER BY id').fetchall(),
        _B4['_used'](conn), conn.execute('SELECT count(*) FROM public.piece_quota_month_locks').fetchone())


def _assert_conflict(response):
    _B6['_error'](response, 409, 'PIECE_CONFLICT')
    assert PRIVATE not in response.text


def _save_args(state, key='q3-lock-save'):
    from psycopg.types.json import Jsonb
    h = state['handoff']
    args = _B6['piece_v2_store'].save_request_arguments(OWNER, _B6['_request'](state['row']), key)
    args.update(p_expected_subscription_tier=h.original.subscription_tier,
        p_expected_source_state=Jsonb({'original': h.original.original_payload(),
            'thread_id': THREAD, 'thread_revision': 1, 'lineage': h.lineage_payload()}))
    return args


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
def test_q3_current_context_saves_once_without_rewriting_piece(database, harness, tier):
    call, state = _fixture(database, harness, tier=tier)
    conn, _, _ = database
    text_before = state['row']['piece_text']
    result = call()
    assert result.status_code == 200 and result.json()['idempotency_replayed'] is False
    assert _B4['_used'](conn) == 1
    assert conn.execute('SELECT piece_text,lifecycle_status FROM public.piece_records').fetchone() == (text_before, 'saved')
    assert PRIVATE not in result.text
    assert len(state['q3_data']['context_guards']) == (0 if tier == 'free' else 1)


@pytest.mark.parametrize('change', ['history-edit', 'history-delete', 'history-thread-revision',
    'history-no-longer-selected', 'feedback-update', 'feedback-delete', 'feedback-new-key', 'evaluated-tier'])
def test_q3_context_changed_after_admission_has_no_piece_or_quota_write(database, harness, change):
    from psycopg.types.json import Jsonb
    tier = 'premium' if change.startswith('feedback') else 'plus'
    call, state = _fixture(database, harness, tier=tier)
    conn, _, _ = database
    before = _piece_state(conn)
    def mutate():
        if change == 'history-edit':
            conn.execute("UPDATE public.emotions SET memo='changed' WHERE id=%s", (state['history_id'],))
        elif change == 'history-delete':
            conn.execute('DELETE FROM public.emotions WHERE id=%s', (state['history_id'],))
        elif change == 'history-thread-revision':
            conn.execute('UPDATE public.emlis_input_threads SET revision=revision+1 WHERE id=%s', (state['history_thread_id'],))
        elif change == 'history-no-longer-selected':
            for hours in (1, 2, 3):
                _history(conn, hours=hours)
        elif change == 'feedback-update':
            conn.execute("UPDATE public.emlis_frame_feedback SET version=version+1,status='REJECTED'")
        elif change == 'feedback-delete':
            conn.execute('DELETE FROM public.emlis_frame_feedback')
        elif change == 'feedback-new-key':
            conn.execute("INSERT INTO public.emlis_frame_feedback(user_id,source_emotion_id,frame_key,frame_ref,status) "
                "VALUES(%s,%s,'second-frame','second-ref','CONFIRMED')", (OWNER, state['history_id']))
        else:
            data = dict(state['q3_data'], evaluated_tier='premium')
            conn.execute('UPDATE public.emlis_input_threads SET data=%s WHERE id=%s', (Jsonb(data), THREAD))
    state['source_hook'] = mutate
    _assert_conflict(call())
    assert _piece_state(conn) == before
    assert len(state['posts']) == 1


@pytest.mark.parametrize('field,value', [
    ('context_guards', {'private': PRIVATE}),
    ('context_guards', [['not-a-uuid', 'a'*32, 1]]),
    ('context_guards', [[INPUT, 'a'*32]]),
    ('context_feedback', [['synthetic-frame', PRIVATE]]),
    ('evaluated_tier', None),
])
def test_q3_malformed_persisted_context_is_fixed_private_conflict(database, harness, field, value):
    from psycopg.types.json import Jsonb
    call, state = _fixture(database, harness, tier='premium')
    conn, _, _ = database
    data = deepcopy(state['q3_data']); data[field] = value
    conn.execute('UPDATE public.emlis_input_threads SET data=%s WHERE id=%s', (Jsonb(data), THREAD))
    before = _piece_state(conn)
    _assert_conflict(call())
    assert _piece_state(conn) == before


def _locked_save(database, state, mutate, commit_change):
    """Wait for PostgreSQL's blocker report, never infer a lock from elapsed time."""
    conn, pg, url = database
    before, pids = _piece_state(conn), Queue()
    args = _save_args(state)
    def worker():
        with pg.connect(url, autocommit=True, connect_timeout=3) as other:
            other.execute("SET statement_timeout='8s'")
            pids.put(other.info.backend_pid)
            try:
                return _B4['_rpc'](other, 'piece_save_v2', args)
            except pg.Error as exc:
                return exc.diag.message_primary
    pool = ThreadPoolExecutor(max_workers=1)
    try:
        conn.execute('BEGIN')
        mutate()
        future = pool.submit(worker)
        pid, deadline = pids.get(timeout=5), time.monotonic()+5
        while conn.info.backend_pid not in conn.execute('SELECT pg_blocking_pids(%s)', (pid,)).fetchone()[0]:
            assert time.monotonic() < deadline, 'save never waited on the modified context'
            time.sleep(.01)
        assert not future.done()
        conn.execute('COMMIT' if commit_change else 'ROLLBACK')
        result = future.result(timeout=10)
        if commit_change:
            assert result == 'PIECE_CONFLICT'
            assert _piece_state(conn) == before
        else:
            assert result['lifecycle_status'] == 'saved'
            assert _B4['_used'](conn) == 1
        assert PRIVATE not in str(result)
    finally:
        conn.execute('ROLLBACK')
        pool.shutdown(wait=True)


@pytest.mark.parametrize('target', ['history-source', 'history-thread', 'feedback'])
@pytest.mark.parametrize('commit_change', [True, False])
def test_q3_save_waits_for_consumed_context_commit_or_rollback(database, harness, target, commit_change):
    _, state = _fixture(database, harness, tier='premium' if target == 'feedback' else 'plus')
    conn, _, _ = database
    def mutate():
        if target == 'history-source':
            conn.execute("UPDATE public.emotions SET memo='changed' WHERE id=%s", (state['history_id'],))
        elif target == 'history-thread':
            conn.execute('UPDATE public.emlis_input_threads SET revision=revision+1 WHERE id=%s', (state['history_thread_id'],))
        else:
            conn.execute("UPDATE public.emlis_frame_feedback SET version=version+1,status='REJECTED'")
    _locked_save(database, state, mutate, commit_change)


def test_q3_saved_replay_survives_committed_source_context_and_tier_changes(database, harness):
    call, state = _fixture(database, harness, tier='premium')
    conn, _, _ = database
    first = call()
    assert first.status_code == 200
    before = _piece_state(conn)
    conn.execute("UPDATE public.emlis_frame_feedback SET version=version+1,status='REJECTED'")
    conn.execute('DELETE FROM public.emotions')
    conn.execute("UPDATE public.profiles SET subscription_tier='free'")
    state['source_error'] = AssertionError('saved replay must not read source/context')
    replay = call()
    assert replay.status_code == 200 and replay.json()['idempotency_replayed'] is True
    assert dict(first.json(), idempotency_replayed=True) == replay.json()
    assert _piece_state(conn) == before and _B4['_used'](conn) == 1
    assert len(state['source']) == 1 and PRIVATE not in replay.text


@pytest.mark.parametrize('create_history_thread', [False, True])
def test_q3_revision_zero_history_uses_profile_writer_protocol(database, harness, create_history_thread):
    from psycopg.types.json import Jsonb
    call, state = _fixture(database, harness, history_thread=False)
    conn, _, _ = database
    assert state['q3_data']['context_guards'][0][2] == 0
    if not create_history_thread:
        assert call().status_code == 200 and _B4['_used'](conn) == 1
        return
    def mutate():
        # The supported Q3 writer takes this lock before adding thread/feedback.
        conn.execute('SELECT id FROM public.profiles WHERE id=%s FOR UPDATE', (OWNER,))
        conn.execute("INSERT INTO public.emlis_input_threads(id,user_id,original_emotion_id,revision,state,issued_count,source_snapshot,data) "
            "VALUES(%s,%s,%s,1,'COMPLETED',0,%s,'{}')",
            (state['history_thread_id'], OWNER, state['history_id'], Jsonb(state['history_original'])))
    _locked_save(database, state, mutate, True)


def test_q3_history_retention_expires_during_actual_quota_lock_wait(database, harness):
    from psycopg.types.json import Jsonb
    _, state = _fixture(database, harness)
    conn, pg, url = database
    # Keep the source valid at the save statement's start, then let its
    # retention expire while that same statement is blocked on quota.
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
    month = conn.execute("SELECT to_char(clock_timestamp() AT TIME ZONE 'Asia/Tokyo','YYYY-MM')").fetchone()[0]
    conn.execute('INSERT INTO public.piece_quota_month_locks(owner_user_id,month_key) VALUES(%s,%s)', (OWNER, month))
    before, pids, args = _piece_state(conn), Queue(), _save_args(state, 'q3-retention-save')
    def worker():
        with pg.connect(url, autocommit=True, connect_timeout=3) as other:
            other.execute("SET statement_timeout='8s'")
            pids.put(other.info.backend_pid)
            try:
                return _B4['_rpc'](other, 'piece_save_v2', args)
            except pg.Error as exc:
                return exc.diag.message_primary
    pool = ThreadPoolExecutor(max_workers=1)
    try:
        conn.execute('BEGIN')
        conn.execute('SELECT 1 FROM public.piece_quota_month_locks WHERE owner_user_id=%s AND month_key=%s FOR UPDATE',
            (OWNER, month))
        future = pool.submit(worker)
        pid, deadline = pids.get(timeout=5), time.monotonic()+5
        while conn.info.backend_pid not in conn.execute('SELECT pg_blocking_pids(%s)', (pid,)).fetchone()[0]:
            assert time.monotonic() < deadline, 'save never waited on quota'
            time.sleep(.01)
        assert not future.done()
        assert conn.execute("SELECT query_start < (%s::timestamp AT TIME ZONE 'UTC')+interval '365 days' "
            'FROM pg_stat_activity WHERE pid=%s', (original['created_at'], pid)).fetchone() == (True,)
        while not conn.execute("SELECT clock_timestamp() > (%s::timestamp AT TIME ZONE 'UTC')+interval '365 days'",
            (original['created_at'],)).fetchone()[0]:
            assert time.monotonic() < deadline, 'history retention did not expire'
            time.sleep(.01)
        conn.execute('COMMIT')
        result = future.result(timeout=10)
        assert result == 'PIECE_CONFLICT' and PRIVATE not in str(result)
        assert _piece_state(conn) == before and _B4['_used'](conn) == 0
    finally:
        conn.execute('ROLLBACK')
        pool.shutdown(wait=True)
