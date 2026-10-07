"""Actual CMEE/B9 -> B5 store connection, with an explicitly synthetic review.

Auth, saved-state reads and the safety verdict are test doubles. In particular
this file does NOT establish PCE-4 safety, real Auth/PostgREST, a renderer or a
public preview issuer. It exercises the new internal connection only, using
actual generated text and disposable native SQL, not a prewritten Piece body.
It neither replaces nor recreates the earlier withheld B5 preparation tests.
"""
from __future__ import annotations

import asyncio
from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
import runpy

import pytest

_B6 = runpy.run_path(str(Path(__file__).parents[1] / 'test_b06_piece_v2_save_api.py'))
_B4 = _B6['_B4']
database = _B6['database']
from piece_v2_contract import PieceContractError, canonical_sha256_hex
import piece_v2_preview_service as service

OWNER, INPUT = _B6['OWNER'], _B6['INPUT']
AUTH = 'Bearer synthetic-owner'
PRIVATE = 'SYNTHETIC_PRIVATE_DIAGNOSTIC_NOT_FOR_RESPONSE'


def _source_created_at(value):
    # Build synthetic source bytes in the native timestamp JSON representation
    # before handoff/hash creation. Never normalize an admitted source later.
    text = value.replace(tzinfo=None).isoformat()
    return text.rstrip('0').rstrip('.') if '.' in text else text


@pytest.mark.parametrize('microsecond', [0, 100000, 838320, 297540, 123456])
def test_synthetic_source_timestamp_matches_native_json_without_precision_loss(database, microsecond):
    conn, _, _ = database
    value = datetime(2026, 10, 7, 7, 8, 55, microsecond, tzinfo=timezone.utc)
    expected = conn.execute('SELECT to_jsonb(%s::timestamp)',
                            (value.replace(tzinfo=None),)).fetchone()[0]
    actual = _source_created_at(value)
    assert actual == expected
    assert datetime.fromisoformat(actual) == value.replace(tzinfo=None)


def _setup(monkeypatch, *, tier='free', named=False):
    row = _B6['_row'](tier=tier)
    text = ('私は友人のAliceさんと落ち着いて話したい。Aliceさんの都合はまだ分からない。'
            if named else '私は一人で落ち着いて考える時間を大切にしていない。')
    original = {'id': INPUT, 'created_at': _source_created_at(datetime.now(timezone.utc)),
                'memo': text, 'memo_action': None, 'category': [],
                'emotions': [], 'emotion_details': []}
    row['source_lineage']['source_input']['source_recorded_at'] = original['created_at']
    handoff = _B6['_handoff'](row, tier=tier, original=original)
    lineage = handoff.lineage_payload()
    source_ref = {k: lineage['source_input'][k] for k in (
        'source_input_id', 'source_input_version', 'source_input_bundle_commitment')}
    source_ref.update({k: lineage['observation'][k] for k in (
        'emlis_observation_stage', 'emlis_observation_result_identity',
        'question_need_decision_identity', 'supplemental_answer_identity')})
    request = {'source_ref': source_ref, 'requested_format': None,
               'visual_selection': {'theme_id': None, 'aspect_ratio': None, 'branding_mode': None}}
    state = {'checks': 0, 'reviews': 0, 'posts': [], 'change_at': None, 'handoff': handoff}

    class Adapter:
        async def resolve_original_handoff(self, authorization, input_id):
            assert authorization == AUTH and input_id == INPUT
            return handoff

        async def revalidate_original_handoff(self, authorization, previous):
            assert authorization == AUTH and previous == handoff
            state['checks'] += 1
            if state['checks'] == state['change_at']:
                return replace(handoff, thread_revision=handoff.thread_revision + 1)
            return handoff

    owner = service.PiecePreviewService(source_adapter=Adapter())
    prepared = asyncio.run(owner.prepare_original(AUTH, request))
    assert prepared.handoff == handoff
    assert prepared.artifact_payload()['piece_text']
    if named:
        assert 'Alice' not in prepared.artifact_payload()['piece_text']
        assert '友人の都合はまだ分からない。' in prepared.artifact_payload()['piece_text']
    else:
        assert '大切にしていない。' in prepared.artifact_payload()['piece_text']
    state['checks'] = 0

    def no_author(*args, **kwargs):
        raise AssertionError('Issuance must not regenerate a prepared body.')
    monkeypatch.setattr(service, 'generate_piece_candidate', no_author)

    async def review(candidate):
        state['reviews'] += 1
        assert candidate is prepared
        # A deliberately synthetic decision, NOT an implemented safety owner.
        assert candidate.handoff.original.original_payload() == original
        return 'transformed' if named else 'ready'

    return owner, request, prepared, review, state


def _issue(owner, request, prepared, review, state, rpc, **overrides):
    kwargs = dict(idempotency_key='synthetic-generated-preview', ttl_seconds=600,
                  renderer_version='synthetic-renderer.v1', rpc=rpc, safety_review=review)
    kwargs.update(overrides)
    return asyncio.run(owner.issue_prepared_original(AUTH, request, prepared, **kwargs))


def _native_rpc(conn, state):
    from psycopg.types.json import Jsonb
    if not state.get('native_source_ready'):
        # Match the existing B6 native source fixture rather than bypassing the
        # new final DB admission. All rows/credentials remain synthetic.
        h = state['handoff']
        original = h.original.original_payload()
        conn.execute('CREATE SCHEMA auth')
        conn.execute('CREATE TABLE auth.users(id uuid PRIMARY KEY)')
        conn.execute('INSERT INTO auth.users VALUES (%s)', (OWNER,))
        conn.execute('CREATE TABLE public.emotions(id uuid PRIMARY KEY,user_id uuid,created_at timestamp,memo text,memo_action text,category jsonb,emotions jsonb,emotion_details jsonb)')
        conn.execute('INSERT INTO public.emotions VALUES (%s,%s,%s,%s,NULL,%s,%s,%s)',
            (INPUT, OWNER, original['created_at'], original['memo'], Jsonb([]), Jsonb([]), Jsonb([])))
        conn.execute((_B6['_ROOT'] / 'supabase/migrations/20260911020509_emlis_input_threads_q2.sql').read_text())
        actual = conn.execute('SELECT public.emlis_parent_source(e) FROM public.emotions e').fetchone()[0]
        assert actual == original
        conn.execute("UPDATE public.profiles SET subscription_tier=%s WHERE id=%s",
            (h.original.subscription_tier, OWNER))
        conn.execute("INSERT INTO public.emlis_input_threads(id,user_id,original_emotion_id,revision,state,issued_count,source_snapshot,data) VALUES(%s,%s,%s,1,'COMPLETED',0,%s,'{}')",
            (h.thread_id, OWNER, INPUT, Jsonb(original)))
        obs = h.lineage_payload()['observation']['emlis_observation_result_identity']
        conn.execute("INSERT INTO public.emlis_thread_events(id,thread_id,seq,kind,round_index,payload) VALUES(%s,%s,1,'OBSERVATION',0,'{}')",
            (obs, h.thread_id))
        conn.execute('UPDATE public.emlis_input_threads SET last_observation_event_id=%s', (obs,))
        state['native_source_ready'] = True
    async def rpc(name, args):
        assert name == 'piece_issue_preview_v2'
        state['posts'].append(deepcopy(args))
        values = {k: Jsonb(v) if k in ('p_record', 'p_expected_source_state') else v
                  for k, v in args.items()}
        return _B4['_rpc'](conn, name, values)
    return rpc


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
@pytest.mark.parametrize('named', [False, True], ids=['synthetic-ready', 'synthetic-transformed'])
def test_generated_body_is_persisted_and_replayed_without_another_author(database, monkeypatch, tier, named):
    conn, _, _ = database
    owner, request, prepared, review, state = _setup(monkeypatch, tier=tier, named=named)
    original_bytes = prepared.handoff.original._original_json
    expected = prepared.artifact_payload()
    first = _issue(owner, request, prepared, review, state, _native_rpc(conn, state))
    second = _issue(owner, request, prepared, review, state, _native_rpc(conn, state), ttl_seconds=1200)
    assert first['idempotency_replayed'] is False
    assert second == dict(first, idempotency_replayed=True)
    assert first['safety_state'] == ('adjusted' if named else 'ready')
    for key in ('piece_text', 'piece_text_hash', 'content_payload', 'content_payload_hash',
                'format_type', 'eligible_formats', 'visual_recipe', 'visual_recipe_hash'):
        assert first[key] == expected[key]
    assert first['visibility_scope'] == 'private'
    assert first['preview_revision'] == first['row_version'] == 1
    assert 'source_lineage' not in first and 'owner_user_id' not in first
    assert prepared.handoff.original._original_json == original_bytes
    assert conn.execute('SELECT piece_text,content_payload,visual_recipe FROM public.piece_records').fetchone() == (
        expected['piece_text'], expected['content_payload'], expected['visual_recipe'])
    assert conn.execute('SELECT count(*) FROM public.piece_records').fetchone() == (1,)
    assert _B4['_used'](conn) == 0
    assert len(state['posts']) == 2 and state['reviews'] == 2 and state['checks'] == 4
    assert all(p['p_request_hash'] == canonical_sha256_hex(request) for p in state['posts'])


@pytest.mark.parametrize('verdict', [None, True, {}, 'adjusted', 'blocked', 'ineligible', 'unavailable'])
def test_missing_or_nonadmitted_review_cannot_issue(database, monkeypatch, verdict):
    conn, _, _ = database
    owner, request, prepared, _, state = _setup(monkeypatch)
    async def review(candidate):
        state['reviews'] += 1
        return verdict
    reviewer = None if verdict is None else review
    with pytest.raises(PieceContractError) as error:
        _issue(owner, request, prepared, reviewer, state, _native_rpc(conn, state))
    assert error.value.code == 'PIECE_SAFETY_UNAVAILABLE'
    assert not state['posts']
    assert conn.execute('SELECT count(*) FROM public.piece_records').fetchone() == (0,)
    assert _B4['_used'](conn) == 0


@pytest.mark.parametrize('change_at', [1, 2], ids=['before-review', 'during-review'])
def test_changed_saved_state_never_reaches_persistence(database, monkeypatch, change_at):
    conn, _, _ = database
    owner, request, prepared, review, state = _setup(monkeypatch)
    state['change_at'] = change_at
    with pytest.raises(PieceContractError) as error:
        _issue(owner, request, prepared, review, state, _native_rpc(conn, state))
    assert error.value.code == 'PIECE_CONFLICT'
    assert not state['posts'] and state['reviews'] == change_at - 1
    assert conn.execute('SELECT count(*) FROM public.piece_records').fetchone() == (0,)


@pytest.mark.parametrize('failure', ['exception', 'contract', 'cancel'])
def test_review_errors_do_not_leak_or_write(database, monkeypatch, failure):
    conn, _, _ = database
    owner, request, prepared, _, state = _setup(monkeypatch)
    async def review(candidate):
        if failure == 'cancel':
            raise asyncio.CancelledError()
        if failure == 'contract':
            raise PieceContractError('UNEXPECTED_PRIVATE_CODE', PRIVATE)
        raise RuntimeError(PRIVATE)
    with pytest.raises(asyncio.CancelledError if failure == 'cancel' else PieceContractError) as error:
        _issue(owner, request, prepared, review, state, _native_rpc(conn, state))
    if failure != 'cancel':
        assert error.value.code == 'PIECE_TEMPORARILY_UNAVAILABLE'
        assert PRIVATE not in str(error.value)
    assert not state['posts']


def test_request_and_artifact_copies_cannot_change_the_reviewed_write(database, monkeypatch):
    conn, _, _ = database
    owner, request, prepared, review, state = _setup(monkeypatch)
    expected_request = canonical_sha256_hex(request)
    expected = prepared.artifact_payload()
    async def mutating_review(candidate):
        request['source_ref']['source_input_bundle_commitment'] = 'sha256:' + '0' * 64
        candidate.artifact_payload()['piece_text'] = PRIVATE
        return await review(candidate)
    result = _issue(owner, request, prepared, mutating_review, state, _native_rpc(conn, state))
    assert state['posts'][0]['p_request_hash'] == expected_request
    assert result['piece_text'] == expected['piece_text']
    assert PRIVATE not in str(result)


@pytest.mark.parametrize('change,code', [('source', 'PIECE_CONFLICT'),
    ('format', 'PIECE_FORMAT_NOT_ELIGIBLE'), ('visual', 'PIECE_VISUAL_SELECTION_NOT_ALLOWED')])
def test_request_must_describe_the_same_prepared_artifact(database, monkeypatch, change, code):
    conn, _, _ = database
    owner, request, prepared, review, state = _setup(monkeypatch)
    if change == 'source':
        request['source_ref']['source_input_bundle_commitment'] = 'sha256:' + '0' * 64
    elif change == 'format':
        request['requested_format'] = 'quote'
    else:
        request['visual_selection']['theme_id'] = 'not-a-theme'
    with pytest.raises(PieceContractError) as error:
        _issue(owner, request, prepared, review, state, _native_rpc(conn, state))
    assert error.value.code == code
    assert not state['posts'] and state['reviews'] == 0


def test_committed_unknown_reply_is_not_retried_automatically(database, monkeypatch):
    conn, _, _ = database
    owner, request, prepared, review, state = _setup(monkeypatch)
    native = _native_rpc(conn, state)
    async def lost_reply(name, args):
        await native(name, args)
        raise TimeoutError(PRIVATE)
    with pytest.raises(PieceContractError) as error:
        _issue(owner, request, prepared, review, state, lost_reply)
    assert error.value.code == 'PIECE_TEMPORARILY_UNAVAILABLE'
    assert PRIVATE not in str(error.value) and len(state['posts']) == 1
    result = _issue(owner, request, prepared, review, state, native)
    assert result['idempotency_replayed'] is True and len(state['posts']) == 2
    assert conn.execute('SELECT count(*) FROM public.piece_records').fetchone() == (1,)
    assert _B4['_used'](conn) == 0


# Final transactional source admission, independent of the synthetic reviewer.
"""B5 final source fence with disposable PostgreSQL and synthetic admission.

Use the existing Q2/Q3 fixtures and lock protocol; no live Auth, user input or
safety acceptance. Generated-body coverage remains in the existing B5 tests.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from pathlib import Path
from queue import Queue
import runpy
import time

import pytest

_SF_C = runpy.run_path(str(Path(__file__).with_name('test_b06_save_context_fence.py')))
_SF_B6, _SF_B4 = _SF_C['_B6'], _SF_C['_B4']
source_fence_database, source_fence_harness = _SF_C['database'], _SF_C['harness']
SF_OWNER, SF_INPUT, SF_THREAD = (_SF_C[k] for k in ('OWNER', 'INPUT', 'THREAD'))
_sf_store = _SF_B6['piece_v2_store']
from piece_v2_contract import PieceContractError

SF_KEY = 'synthetic-source-fenced-preview'
SF_REQUEST_HASH = 'f' * 64


def _sf_setup(source_fence_database, source_fence_harness, tier='premium'):
    _, state = _SF_C['_fixture'](source_fence_database, source_fence_harness, tier=tier)
    conn, _, _ = source_fence_database
    row = state['row']
    record = {k: deepcopy(row[k]) for k in _SF_B6['_B5']['_KEYS']}
    record['eligible_formats'] = list(row['preview_eligible_formats'])
    # Remove only the synthetic B6 preview; B5 must perform its own issuance.
    conn.execute('DELETE FROM public.piece_records')
    h = state['handoff']
    state['candidate'] = record
    state['expectation'] = {'original': h.original.original_payload(),
        'thread_id': h.thread_id, 'thread_revision': h.thread_revision,
        'lineage': h.lineage_payload()}
    state['tier'] = tier
    state['issue_posts'] = []
    assert h.original.subscription_tier == tier
    assert conn.execute('SELECT subscription_tier FROM public.profiles WHERE id=%s',
                        (SF_OWNER,)).fetchone() == (tier,)
    assert state['q3_data']['evaluated_tier'] == tier
    return state


def _sf_args(state):
    from psycopg.types.json import Jsonb
    return {'p_owner_user_id': SF_OWNER, 'p_idempotency_key_hash': _sf_store._key_hash(SF_KEY),
        'p_request_hash': SF_REQUEST_HASH, 'p_record': Jsonb(state['candidate']),
        'p_ttl_seconds': 600, 'p_expected_subscription_tier': state['tier'],
        'p_expected_source_state': Jsonb(state['expectation'])}


def _sf_issue(source_fence_database, state, *, mutate=None, **overrides):
    conn, pg, _ = source_fence_database
    from psycopg.types.json import Jsonb
    async def rpc(name, args):
        assert name == 'piece_issue_preview_v2'
        state['issue_posts'].append(deepcopy(args))
        if mutate:
            mutate()
        values = {k: Jsonb(v) if k in ('p_record', 'p_expected_source_state') else v
                  for k, v in args.items()}
        try:
            return _SF_B4['_rpc'](conn, name, values)
        except pg.Error as exc:
            # Diagnostic is confined to synthetic native tests and contains
            # SQL function/line information, never a provider response body.
            state['sql_error_context'] = exc.diag.context
            raise PieceContractError(exc.diag.message_primary) from None
    kwargs = dict(authenticated_user_id=SF_OWNER, record=state['candidate'],
        idempotency_key=SF_KEY, request_fingerprint=SF_REQUEST_HASH, ttl_seconds=600,
        expected_subscription_tier=state['tier'], expected_source_state=state['expectation'], rpc=rpc)
    kwargs.update(overrides)
    return asyncio.run(_sf_store.issue_piece_preview(**kwargs))


def _sf_mutate(conn, state, target):
    if target == 'source':
        conn.execute("UPDATE public.emotions SET memo='changed' WHERE id=%s", (SF_INPUT,))
    elif target == 'source-delete':
        conn.execute('DELETE FROM public.emotions WHERE id=%s', (SF_INPUT,))
    elif target == 'thread':
        conn.execute('UPDATE public.emlis_input_threads SET revision=revision+1 WHERE id=%s', (SF_THREAD,))
    elif target == 'tier':
        conn.execute("UPDATE public.profiles SET subscription_tier='free' WHERE id=%s", (SF_OWNER,))
    elif target == 'history-source':
        conn.execute("UPDATE public.emotions SET memo='changed' WHERE id=%s", (state['history_id'],))
    elif target == 'history-delete':
        conn.execute('DELETE FROM public.emotions WHERE id=%s', (state['history_id'],))
    elif target == 'history-thread':
        conn.execute('UPDATE public.emlis_input_threads SET revision=revision+1 WHERE id=%s',
                     (state['history_thread_id'],))
    elif target == 'feedback':
        conn.execute("UPDATE public.emlis_frame_feedback SET version=version+1,status='REJECTED'")
    elif target == 'feedback-delete':
        conn.execute('DELETE FROM public.emlis_frame_feedback')
    else:
        raise AssertionError(target)


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
def test_current_source_issues_and_replays_the_exact_bundle_without_quota(source_fence_database, source_fence_harness, tier):
    state = _sf_setup(source_fence_database, source_fence_harness, tier)
    conn, _, _ = source_fence_database
    before = deepcopy(state['candidate'])
    try:
        first = _sf_issue(source_fence_database, state)
    except PieceContractError:
        pytest.fail('Synthetic current-source issuance failed at: ' +
                    str(state.get('sql_error_context')), pytrace=False)
    try:
        again = _sf_issue(source_fence_database, state, ttl_seconds=1200)
    except PieceContractError:
        pytest.fail('Synthetic current-source replay failed at: ' +
                    str(state.get('sql_error_context')), pytrace=False)
    assert again == dict(first, idempotency_replayed=True)
    assert first['idempotency_replayed'] is False
    for key in before.keys() - {'source_lineage'}:
        assert first[key] == before[key]
    assert state['candidate'] == before
    assert first['visibility_scope'] == 'private'
    assert first['preview_revision'] == first['row_version'] == 1
    assert 'source_lineage' not in first and 'original' not in first
    assert conn.execute('SELECT count(*) FROM public.piece_records').fetchone() == (1,)
    assert _SF_B4['_used'](conn) == 0
    assert conn.execute('SELECT count(*) FROM public.piece_quota_month_locks').fetchone() == (0,)
    assert all(p['p_expected_source_state'] == state['expectation'] for p in state['issue_posts'])


@pytest.mark.parametrize('target', ['source', 'source-delete', 'thread', 'tier',
    'history-source', 'history-delete', 'history-thread', 'feedback', 'feedback-delete'])
@pytest.mark.parametrize('replay', [False, True])
def test_post_admission_change_cannot_issue_or_replay_stale_preview(source_fence_database, source_fence_harness, target, replay):
    state = _sf_setup(source_fence_database, source_fence_harness)
    conn, _, _ = source_fence_database
    if replay:
        _sf_issue(source_fence_database, state)
    before = _SF_C['_piece_state'](conn)
    with pytest.raises(PieceContractError) as error:
        _sf_issue(source_fence_database, state, mutate=lambda: _sf_mutate(conn, state, target))
    assert error.value.code == ('PIECE_NOT_FOUND' if target == 'source-delete' else 'PIECE_CONFLICT')
    assert _SF_C['_piece_state'](conn) == before
    assert _SF_B4['_used'](conn) == 0


@pytest.mark.parametrize('target', ['source', 'tier', 'thread', 'history-source', 'history-thread', 'feedback'])
@pytest.mark.parametrize('commit_change', [True, False])
def test_actual_lock_wait_observes_commit_or_rollback(source_fence_database, source_fence_harness, target, commit_change):
    state = _sf_setup(source_fence_database, source_fence_harness)
    conn, pg, url = source_fence_database
    before, pids = _SF_C['_piece_state'](conn), Queue()
    args = _sf_args(state)
    def worker():
        with pg.connect(url, autocommit=True, connect_timeout=3) as other:
            other.execute("SET statement_timeout='8s'")
            pids.put(other.info.backend_pid)
            try:
                return _SF_B4['_rpc'](other, 'piece_issue_preview_v2', args)
            except pg.Error as exc:
                return exc.diag.message_primary
    pool = ThreadPoolExecutor(max_workers=1)
    try:
        conn.execute('BEGIN')
        _sf_mutate(conn, state, target)
        future = pool.submit(worker)
        pid, deadline = pids.get(timeout=5), time.monotonic()+5
        while conn.info.backend_pid not in conn.execute('SELECT pg_blocking_pids(%s)', (pid,)).fetchone()[0]:
            assert not future.done(), future.result()
            assert time.monotonic() < deadline, 'issuance never waited on the modified source/context'
            time.sleep(.01)
        assert not future.done()
        conn.execute('COMMIT' if commit_change else 'ROLLBACK')
        result = future.result(timeout=10)
        if commit_change:
            assert result == 'PIECE_CONFLICT'
            assert _SF_C['_piece_state'](conn) == before
        else:
            assert result['piece_text'] == state['candidate']['piece_text']
            assert result['visual_recipe'] == state['candidate']['visual_recipe']
            assert result['idempotency_replayed'] is False
        assert _SF_B4['_used'](conn) == 0
        assert conn.execute('SELECT count(*) FROM public.piece_quota_month_locks').fetchone() == (0,)
    finally:
        conn.execute('ROLLBACK')
        pool.shutdown(wait=True)


@pytest.mark.parametrize('change', ['missing-tier', 'missing-source', 'bad-tier', 'extra-field', 'wrong-owner'])
def test_invalid_server_expectation_is_rejected_before_rpc(source_fence_database, source_fence_harness, change):
    state = _sf_setup(source_fence_database, source_fence_harness)
    overrides = {}
    if change == 'missing-tier':
        overrides['expected_subscription_tier'] = None
    elif change == 'missing-source':
        overrides['expected_source_state'] = None
    elif change == 'bad-tier':
        overrides['expected_subscription_tier'] = 'unknown'
    elif change == 'extra-field':
        state['expectation']['client_text'] = 'not permitted'
    else:
        state['expectation']['lineage']['source_input']['source_owner_user_id'] = _SF_B6['VIEWER']
    with pytest.raises(PieceContractError) as error:
        _sf_issue(source_fence_database, state, **overrides)
    assert error.value.code == 'PIECE_REQUEST_INVALID'
    assert not state['issue_posts']


def test_fenced_overload_is_service_only_and_preserves_legacy_signature(source_fence_database):
    conn, _, _ = source_fence_database
    for signature in ('public.piece_issue_preview_v2(uuid,text,text,jsonb,integer)',
                      'public.piece_issue_preview_v2(uuid,text,text,jsonb,integer,text,jsonb)'):
        assert conn.execute('SELECT has_function_privilege(%s,%s,%s)',
                            ('service_role', signature, 'EXECUTE')).fetchone() == (True,)
        for role in ('anon', 'authenticated'):
            assert conn.execute('SELECT has_function_privilege(%s,%s,%s)',
                                (role, signature, 'EXECUTE')).fetchone() == (False,)
