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


def _setup(monkeypatch, *, tier='free', named=False):
    row = _B6['_row'](tier=tier)
    text = ('私は友人のAliceさんと落ち着いて話したい。Aliceさんの都合はまだ分からない。'
            if named else '私は一人で落ち着いて考える時間を大切にしていない。')
    original = {'id': INPUT, 'created_at': datetime.now(timezone.utc).isoformat(),
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
    state = {'checks': 0, 'reviews': 0, 'posts': [], 'change_at': None}

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
    async def rpc(name, args):
        from psycopg.types.json import Jsonb
        assert name == 'piece_issue_preview_v2'
        state['posts'].append(deepcopy(args))
        return _B4['_rpc'](conn, name, dict(args, p_record=Jsonb(args['p_record'])))
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
