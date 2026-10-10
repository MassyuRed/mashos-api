"""Actual bounded PCE-4 review -> B5 issuance on disposable PostgreSQL.

CMEE/B9, source/format/meaning checks, review and SQL are real code. Authentication,
saved-state reads, source records, TTL and renderer identity are synthetic.
These tests do not establish real Auth/PostgREST, HTTP/RN, general safety coverage,
production readiness, or human acceptance. Earlier synthetic-review tests stay.
"""
from __future__ import annotations

import asyncio
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import runpy

import pytest

_B5 = runpy.run_path(str(Path(__file__).with_name('test_b05_generated_preview_issuance.py')))
database = _B5['database']
from piece_v2_contract import PieceContractError, canonical_json_bytes, canonical_sha256_hex
import piece_v2_preview_service as service
import piece_v2_safety_review as review


def _no_author(monkeypatch):
    import cocolon_meaning_experience_engine.engine as engine
    import cocolon_meaning_experience_engine.piece_v1c as piece
    def forbidden(*args, **kwargs):
        raise AssertionError('Review/issuance must not author or regenerate text.')
    monkeypatch.setattr(service, 'generate_piece_candidate', forbidden)
    monkeypatch.setattr(engine.MeaningExperienceEngine, 'generate', forbidden)
    monkeypatch.setattr(piece, 'realize_piece_artifact', forbidden)
    monkeypatch.setattr(piece, 'generate_piece_artifact', forbidden)


def _changed(prepared, *, blocks=None, fmt=None, eligible=None, edit=None):
    value = prepared.artifact_payload()
    payload = value['content_payload']
    if blocks is not None:
        payload['body_blocks'] = blocks
    if fmt is not None:
        payload['format_type'] = value['format_type'] = fmt
    if eligible is not None:
        value['eligible_formats'] = eligible
    value['piece_text'] = '\n\n'.join(payload['body_blocks'])
    value['piece_text_hash'] = sha256(value['piece_text'].encode('utf-8')).hexdigest()
    value['content_payload_hash'] = canonical_sha256_hex(payload)
    if edit is not None:
        edit(value)
    return replace(prepared, _artifact_json=canonical_json_bytes(value))


def _source_changed(prepared, text):
    original = prepared.handoff.original.original_payload()
    original['memo'] = text
    row = _B5['_B6']['_row'](tier=prepared.handoff.original.subscription_tier)
    row['source_lineage']['source_input']['source_recorded_at'] = original['created_at']
    handoff = _B5['_B6']['_handoff'](row,
        tier=prepared.handoff.original.subscription_tier, original=original)
    return replace(prepared, handoff=handoff)


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
@pytest.mark.parametrize('named', [False, True], ids=['ready', 'role-transformed'])
def test_actual_review_issues_same_generated_body_and_replays_without_author(database, monkeypatch, tier, named):
    conn, _, _ = database
    owner, request, prepared, _, state = _B5['_setup'](monkeypatch, tier=tier, named=named)
    original, artifact = prepared.handoff.original._original_json, prepared._artifact_json
    expected = prepared.artifact_payload()
    _no_author(monkeypatch)
    assert asyncio.run(review.review_prepared_original(prepared)) == ('transformed' if named else 'ready')
    rpc = _B5['_native_rpc'](conn, state)
    first = _B5['_issue'](owner, request, prepared, review.review_prepared_original, state, rpc)
    second = _B5['_issue'](owner, request, prepared, review.review_prepared_original, state, rpc)
    assert second == dict(first, idempotency_replayed=True)
    assert first['idempotency_replayed'] is False
    assert first['safety_state'] == ('adjusted' if named else 'ready')
    for key in ('piece_text', 'piece_text_hash', 'content_payload', 'content_payload_hash',
                'format_type', 'eligible_formats', 'visual_recipe', 'visual_recipe_hash'):
        assert first[key] == expected[key]
    assert conn.execute('SELECT piece_text, content_payload, visual_recipe FROM public.piece_records').fetchone() == (
        expected['piece_text'], expected['content_payload'], expected['visual_recipe'])
    assert conn.execute('SELECT count(*) FROM public.piece_records').fetchone() == (1,)
    assert _B5['_B4']['_used'](conn) == 0
    assert prepared.handoff.original._original_json == original
    assert prepared._artifact_json == artifact
    assert 'source_lineage' not in first and 'owner_user_id' not in first


@pytest.mark.parametrize('mutation', ['negation', 'object', 'extra-claim', 'empty', 'uncertainty', 'name', 'role'])
def test_hash_consistent_unfaithful_body_cannot_pass_real_review_or_write(database, monkeypatch, mutation):
    conn, _, _ = database
    named = mutation in {'uncertainty', 'name', 'role'}
    owner, request, prepared, _, state = _B5['_setup'](monkeypatch, named=named)
    _no_author(monkeypatch)
    blocks = prepared.artifact_payload()['content_payload']['body_blocks']
    if mutation == 'negation':
        blocks = [b.replace('大切にしていない', '大切にしている') for b in blocks]
    elif mutation == 'object':
        blocks = [b.replace('一人で落ち着いて考える時間', '誰かに褒められる時間') for b in blocks]
    elif mutation == 'extra-claim':
        blocks[-1] += '私は自分を必ず変えられる。'
    elif mutation == 'empty':
        blocks = []
    elif mutation == 'uncertainty':
        blocks = [b.replace('まだ分からない', '分かっている') for b in blocks]
    elif mutation == 'name':
        blocks = [b.replace('友人', '友人のAliceさん', 1) for b in blocks]
    else:
        blocks = [b.replace('友人', '同僚') for b in blocks]
    altered = _changed(prepared, blocks=blocks)
    assert altered._artifact_json != prepared._artifact_json
    assert asyncio.run(review.review_prepared_original(altered)) == 'ineligible'
    reviewed = []

    async def actual_review(candidate):
        reviewed.append(candidate)
        return await review.review_prepared_original(candidate)

    with pytest.raises(PieceContractError) as error:
        _B5['_issue'](owner, request, altered, actual_review,
                      state, _B5['_native_rpc'](conn, state))
    if mutation == 'empty':
        # Empty body_blocks violates the existing content contract before the
        # service calls its reviewer. Do not weaken that early rejection.
        assert error.value.code == 'PIECE_REQUEST_INVALID'
        assert reviewed == []
    else:
        # Well-shaped, hash-consistent meaning changes must reach the actual
        # reviewer and fail there, not pass via an unrelated transient error.
        assert error.value.code == 'PIECE_SAFETY_UNAVAILABLE'
        assert reviewed == [altered]
    assert not state['posts']
    assert conn.execute('SELECT count(*) FROM public.piece_records').fetchone() == (0,)
    assert _B5['_B4']['_used'](conn) == 0


_RISK = [
    ('私は連絡先test@example.invalidを残したい。', 'ineligible'),
    ('私はｔｅｓｔ＠ｅｘａｍｐｌｅ．ｉｎｖａｌｉｄを残したい。', 'ineligible'),
    ('私はhttps://example.invalidへ案内したい。', 'ineligible'),
    ('私は@private_exampleへ案内したい。', 'ineligible'),
    ('私は090-1234-5678を伝えたい。', 'ineligible'),
    ('私はpassword=synthetic-secretを残したい。', 'ineligible'),
    ('私は勤務先を公開してやりたい。', 'blocked'),
    ('私は相手を殺してやる。', 'blocked'),
    ('友人は詐欺師だ。私は距離を置きたい。', 'ineligible'),
    ('私は\u202e連絡先を残したい。', 'ineligible'),
]


@pytest.mark.parametrize('text,verdict', _RISK)
def test_source_scan_is_not_replaced_by_clean_piece_body(monkeypatch, text, verdict):
    _, _, prepared, _, _ = _B5['_setup'](monkeypatch)
    altered = _source_changed(prepared, text)
    def no_meaning(*args, **kwargs):
        raise AssertionError('Unsafe source must stop before meaning planning.')
    monkeypatch.setattr(review, 'build_piece_source_meaning', no_meaning)
    _no_author(monkeypatch)
    assert altered.artifact_payload() == prepared.artifact_payload()
    assert asyncio.run(review.review_prepared_original(altered)) == verdict


@pytest.mark.parametrize('text,verdict', _RISK)
def test_post_format_scan_is_not_replaced_by_source_scan(monkeypatch, text, verdict):
    _, _, prepared, _, _ = _B5['_setup'](monkeypatch)
    altered = _changed(prepared, blocks=[text])
    def no_meaning_gate(*args, **kwargs):
        raise AssertionError('Unsafe visible text must stop before S7.')
    monkeypatch.setattr(review, 'validate_source_meaning_preservation', no_meaning_gate)
    _no_author(monkeypatch)
    assert altered.handoff == prepared.handoff
    assert asyncio.run(review.review_prepared_original(altered)) == verdict


@pytest.mark.parametrize('mutation', ['duplicate', 'reorder', 'unknown', 'omitted', 'quote-context', 'declaration-context'])
def test_format_offer_and_selected_format_are_source_checked(monkeypatch, mutation):
    named = mutation in {'quote-context', 'declaration-context'}
    _, _, prepared, _, _ = _B5['_setup'](monkeypatch, named=named)
    eligible = prepared.artifact_payload()['eligible_formats']
    if mutation == 'duplicate':
        altered = _changed(prepared, eligible=eligible + eligible[:1])
    elif mutation == 'reorder':
        assert len(eligible) > 1
        altered = _changed(prepared, eligible=list(reversed(eligible)))
    elif mutation == 'unknown':
        altered = _changed(prepared, eligible=eligible + ['unregistered'])
    elif mutation == 'omitted':
        assert len(eligible) > 1
        altered = _changed(prepared, eligible=eligible[:1])
    else:
        fmt = 'quote' if mutation == 'quote-context' else 'declaration'
        altered = _changed(prepared, fmt=fmt, eligible=eligible + [fmt])
    _no_author(monkeypatch)
    assert asyncio.run(review.review_prepared_original(altered)) == 'ineligible'


@pytest.mark.parametrize('mutation', ['payload-hash', 'text-hash', 'language', 'title', 'extra-field', 'contract', 'visibility'])
def test_no_projection_of_unreviewed_content_or_future_contract(monkeypatch, mutation):
    _, _, prepared, _, _ = _B5['_setup'](monkeypatch)
    def edit(value):
        if mutation == 'payload-hash':
            value['content_payload_hash'] = '0' * 64
        elif mutation == 'text-hash':
            value['piece_text_hash'] = '0' * 64
        elif mutation == 'extra-field':
            value['unreviewed_body'] = _B5['PRIVATE']
        elif mutation == 'contract':
            value['piece_contract_version'] = 'unknown'
        elif mutation == 'visibility':
            value['visibility_scope'] = 'public'
        else:
            value['content_payload'][mutation] = 'en' if mutation == 'language' else _B5['PRIVATE']
            value['content_payload_hash'] = canonical_sha256_hex(value['content_payload'])
    _no_author(monkeypatch)
    assert asyncio.run(review.review_prepared_original(_changed(prepared, edit=edit))) == 'ineligible'


@pytest.mark.parametrize('change_at', [1, 2])
def test_real_review_does_not_bypass_existing_current_source_fence(database, monkeypatch, change_at):
    conn, _, _ = database
    owner, request, prepared, _, state = _B5['_setup'](monkeypatch)
    _no_author(monkeypatch)
    state['change_at'] = change_at
    with pytest.raises(PieceContractError) as error:
        _B5['_issue'](owner, request, prepared, review.review_prepared_original,
                      state, _B5['_native_rpc'](conn, state))
    assert error.value.code == 'PIECE_CONFLICT'
    assert not state['posts']
    assert conn.execute('SELECT count(*) FROM public.piece_records').fetchone() == (0,)


@pytest.mark.parametrize('failure', ['unexpected', 'cancel'])
def test_review_failure_is_body_free_and_cancellation_propagates(monkeypatch, failure):
    _, _, prepared, _, _ = _B5['_setup'](monkeypatch)
    def fail(*args, **kwargs):
        if failure == 'cancel':
            raise asyncio.CancelledError()
        raise RuntimeError(_B5['PRIVATE'])
    monkeypatch.setattr(review, 'build_piece_source_meaning', fail)
    with pytest.raises(asyncio.CancelledError if failure == 'cancel' else PieceContractError) as error:
        asyncio.run(review.review_prepared_original(prepared))
    if failure != 'cancel':
        assert error.value.code == 'PIECE_TEMPORARILY_UNAVAILABLE'
        assert _B5['PRIVATE'] not in str(error.value)


@pytest.mark.parametrize('candidate', [None, {}, True, 'ready'])
def test_client_values_are_not_server_prepared_artifacts(candidate):
    assert asyncio.run(review.review_prepared_original(candidate)) == 'ineligible'


# The same existing native fixture, now entered before preparation. These
# counters exclude the fixture's initial reference artifact construction.
def _orchestration(database, monkeypatch, *, tier='free', named=False):
    conn, _, _ = database
    generate = service.generate_piece_candidate
    actual_review = review.review_prepared_original
    owner, request, prepared, _, state = _B5['_setup'](monkeypatch, tier=tier, named=named)
    state.update(authors=0, actual_reviews=0, reads=[])

    def author(*args, **kwargs):
        state['authors'] += 1
        return generate(*args, **kwargs)

    async def reviewer(candidate):
        state['actual_reviews'] += 1
        return await actual_review(candidate)

    monkeypatch.setattr(service, 'generate_piece_candidate', author)
    monkeypatch.setattr(review, 'review_prepared_original', reviewer)
    rpc = _B5['_native_rpc'](conn, state)

    async def load(owner_id, preview_id):
        assert owner_id == _B5['OWNER']
        state['reads'].append((owner_id, preview_id))
        row = conn.execute('SELECT to_jsonb(r) FROM (SELECT ' +
            ','.join(service._REPLAY_COLUMNS) +
            ' FROM public.piece_records WHERE id=%s AND owner_user_id=%s) r',
            (preview_id, owner_id)).fetchone()
        return deepcopy(row[0]) if row else None

    return owner, request, prepared, state, rpc, load


def _orchestrate(owner, request, rpc, load, **overrides):
    kwargs = dict(idempotency_key='synthetic-generated-preview', ttl_seconds=600,
                  renderer_version='synthetic-renderer.v1', rpc=rpc, load_record=load)
    kwargs.update(overrides)
    return asyncio.run(owner.issue_original(_B5['AUTH'], request, **kwargs))


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
@pytest.mark.parametrize('named', [False, True], ids=['ready', 'role-transformed'])
def test_orchestrated_first_issue_and_restart_use_one_author_and_actual_review(database, monkeypatch, tier, named):
    conn, _, _ = database
    owner, request, prepared, state, rpc, load = _orchestration(database, monkeypatch, tier=tier, named=named)
    first = _orchestrate(owner, request, rpc, load)
    assert not first['idempotency_replayed']
    assert first['safety_state'] == ('adjusted' if named else 'ready')
    for field in ('piece_text', 'content_payload', 'visual_recipe', 'piece_text_hash',
                  'content_payload_hash', 'visual_recipe_hash'):
        assert first[field] == prepared.artifact_payload()[field]
    before = conn.execute('SELECT to_jsonb(r) FROM public.piece_records r').fetchone()[0]
    _no_author(monkeypatch)

    async def no_review(*args):
        raise AssertionError('Replay must not review again.')

    monkeypatch.setattr(review, 'review_prepared_original', no_review)
    restarted = service.PiecePreviewService(source_adapter=owner._source_adapter)
    second = _orchestrate(restarted, request, rpc, load, ttl_seconds=1200)
    assert second == dict(first, idempotency_replayed=True)
    assert conn.execute('SELECT to_jsonb(r) FROM public.piece_records r').fetchone()[0] == before
    assert state['authors'] == state['actual_reviews'] == len(state['posts']) == 1
    assert len(state['reads']) == 4
    assert _B5['_B4']['_used'](conn) == 0


@pytest.mark.parametrize('kind,code', [
    ('cancelled', 'PIECE_CONFLICT'), ('expired', 'PIECE_PREVIEW_EXPIRED'),
    ('request', 'PIECE_CONFLICT'), ('text', 'PIECE_HASH_MISMATCH'),
    ('missing-first-read', 'PIECE_NOT_FOUND'), ('missing-second-read', 'PIECE_NOT_FOUND'),
])
def test_orchestration_never_recreates_nonreplayable_or_disappearing_rows(database, monkeypatch, kind, code):
    conn, _, _ = database
    owner, request, _, state, rpc, load = _orchestration(database, monkeypatch)
    _orchestrate(owner, request, rpc, load)
    before = conn.execute('SELECT to_jsonb(r) FROM public.piece_records r').fetchone()[0]
    calls = 0

    async def changed(owner_id, preview_id):
        nonlocal calls
        calls += 1
        row = await load(owner_id, preview_id)
        # Call one is the existence probe. Later errors must not become create.
        if (kind == 'missing-first-read' and calls == 2
                or kind == 'missing-second-read' and calls == 3):
            return None
        if kind == 'cancelled':
            row['lifecycle_status'] = 'cancelled'
        elif kind == 'expired':
            row['expires_at'] = '2000-01-01T00:00:00+00:00'
        elif kind == 'request':
            row['preview_request_hash'] = '0' * 64
        elif kind == 'text':
            row['piece_text'] = _B5['PRIVATE']
        return row

    with pytest.raises(PieceContractError) as error:
        _orchestrate(owner, request, rpc, changed)
    assert error.value.code == code
    assert state['authors'] == state['actual_reviews'] == len(state['posts']) == 1
    assert conn.execute('SELECT to_jsonb(r) FROM public.piece_records r').fetchone()[0] == before
    assert _B5['_B4']['_used'](conn) == 0


@pytest.mark.parametrize('failure', ['not-found', 'unexpected', 'cancel'])
def test_initial_lookup_error_is_not_an_absent_row_or_a_creation_retry(database, monkeypatch, failure):
    conn, _, _ = database
    owner, request, _, state, rpc, _ = _orchestration(database, monkeypatch)

    async def failing_load(*args):
        if failure == 'cancel':
            raise asyncio.CancelledError()
        if failure == 'not-found':
            raise PieceContractError('PIECE_NOT_FOUND', _B5['PRIVATE'])
        raise RuntimeError(_B5['PRIVATE'])

    with pytest.raises(asyncio.CancelledError if failure == 'cancel' else PieceContractError) as error:
        _orchestrate(owner, request, rpc, failing_load)
    if failure != 'cancel':
        assert error.value.code == ('PIECE_NOT_FOUND' if failure == 'not-found' else 'PIECE_TEMPORARILY_UNAVAILABLE')
        assert _B5['PRIVATE'] not in str(error.value)
    assert state['authors'] == state['actual_reviews'] == len(state['posts']) == 0
    assert conn.execute('SELECT count(*) FROM public.piece_records').fetchone() == (0,)


def test_orchestrated_lost_reply_recovers_by_read_without_second_generation_or_write(database, monkeypatch):
    conn, _, _ = database
    owner, request, _, state, native, load = _orchestration(database, monkeypatch)

    async def lost_reply(name, args):
        await native(name, args)
        raise TimeoutError(_B5['PRIVATE'])

    with pytest.raises(PieceContractError) as error:
        _orchestrate(owner, request, lost_reply, load)
    assert error.value.code == 'PIECE_TEMPORARILY_UNAVAILABLE'
    assert _B5['PRIVATE'] not in str(error.value)
    assert state['authors'] == state['actual_reviews'] == len(state['posts']) == 1
    _no_author(monkeypatch)
    restarted = service.PiecePreviewService(source_adapter=owner._source_adapter)
    result = _orchestrate(restarted, request, lost_reply, load)
    assert result['idempotency_replayed'] is True
    assert state['authors'] == state['actual_reviews'] == len(state['posts']) == 1
    assert conn.execute('SELECT count(*) FROM public.piece_records').fetchone() == (1,)
    assert _B5['_B4']['_used'](conn) == 0


@pytest.mark.parametrize('overrides', [
    {'ttl_seconds': True}, {'ttl_seconds': 0}, {'ttl_seconds': 2147483648},
    {'renderer_version': ''}, {'renderer_version': '/private/renderer'},
    {'idempotency_key': ''},
])
def test_orchestrated_invalid_server_configuration_stops_before_lookup_or_generation(database, monkeypatch, overrides):
    conn, _, _ = database
    owner, request, _, state, rpc, load = _orchestration(database, monkeypatch)
    with pytest.raises(PieceContractError) as error:
        _orchestrate(owner, request, rpc, load, **overrides)
    assert error.value.code == 'PIECE_REQUEST_INVALID'
    assert not state['reads']
    assert state['authors'] == state['actual_reviews'] == len(state['posts']) == 0
    assert conn.execute('SELECT count(*) FROM public.piece_records').fetchone() == (0,)


@pytest.mark.parametrize('change_at', [1, 2, 3])
def test_orchestrated_current_source_change_still_prevents_issue(database, monkeypatch, change_at):
    conn, _, _ = database
    owner, request, _, state, rpc, load = _orchestration(database, monkeypatch)
    state['change_at'] = change_at
    with pytest.raises(PieceContractError) as error:
        _orchestrate(owner, request, rpc, load)
    assert error.value.code == 'PIECE_CONFLICT'
    assert not state['posts']
    assert conn.execute('SELECT count(*) FROM public.piece_records').fetchone() == (0,)
    assert _B5['_B4']['_used'](conn) == 0


def test_orchestrated_candidate_must_pass_actual_review_before_native_write(database, monkeypatch):
    conn, _, _ = database
    owner, request, prepared, state, rpc, load = _orchestration(database, monkeypatch)
    blocks = [b.replace('大切にしていない', '大切にしている')
              for b in prepared.artifact_payload()['content_payload']['body_blocks']]
    altered = _changed(prepared, blocks=blocks)
    assert altered._artifact_json != prepared._artifact_json

    async def altered_preparation(*args):
        return altered

    monkeypatch.setattr(owner, 'prepare_original', altered_preparation)
    with pytest.raises(PieceContractError) as error:
        _orchestrate(owner, request, rpc, load)
    assert error.value.code == 'PIECE_SAFETY_UNAVAILABLE'
    assert state['actual_reviews'] == 1 and not state['posts']
    assert conn.execute('SELECT count(*) FROM public.piece_records').fetchone() == (0,)


# HTTP below calls the real orchestration, CMEE/B9, bounded reviewer, store
# and disposable SQL. Bearer lookup, source/state reads and PostgREST transport
# remain synthetic. Nothing is registered in the production application.
def _preview_http_harness(database, monkeypatch, *, tier='free', named=False):
    import httpx
    from fastapi import FastAPI, HTTPException
    import api_piece_v2 as api
    import supabase_client

    owner, request, prepared, state, native, load = _orchestration(
        database, monkeypatch, tier=tier, named=named)
    conn, _, _ = database
    conn.execute((_B5['_B4']['_ROOT'] / 'supabase/migrations/20261010_005_piece_v2_quota_read.sql').read_text())
    actual_issue = owner.issue_original
    state.update(http_auth=0, http_rpc=0, quota_rpc=0)

    async def verify(authorization):
        state['http_auth'] += 1
        if authorization != _B5['AUTH']:
            raise HTTPException(401, detail=_B5['PRIVATE'])
        return _B5['OWNER']

    async def issue(authorization, value, **kwargs):
        assert set(kwargs) == {'idempotency_key', 'ttl_seconds', 'renderer_version', 'rpc', 'expected_subscription_tier'}
        result = await actual_issue(authorization, value, load_record=load, **kwargs)
        state['last_internal_result'] = deepcopy(result)
        return result

    async def transport(name, args, *, timeout):
        if name == 'piece_read_quota_v2':
            assert args == {'p_owner_user_id': _B5['OWNER']} and timeout == 8.0
            state['quota_rpc'] += 1
            if state.get('quota_failure'):
                return httpx.Response(404, json={'private': _B5['PRIVATE']})
            result = _B5['_B4']['_rpc'](conn, name, args)
            return httpx.Response(200, json=result)
        assert name == 'piece_issue_preview_v2' and timeout == 8.0
        state['http_rpc'] += 1
        if 'provider_response' in state:
            status, value = state['provider_response']
            return httpx.Response(status, json=value)
        result = await native(name, args)
        if state.get('lose_ack'):
            raise TimeoutError(_B5['PRIVATE'])
        return httpx.Response(200, json=result)

    monkeypatch.setattr(api, '_verify_bearer', verify)
    monkeypatch.setattr(owner, 'issue_original', issue)
    monkeypatch.setattr(service, 'PiecePreviewService', lambda: owner)
    monkeypatch.setattr(supabase_client, 'sb_post_rpc', transport)
    app = FastAPI()
    # Synthetic readiness for this isolated fixture, not live admission.
    app.state.piece_v2_runtime = {
        'requested': {'piece_v2_preview_enabled': True},
        'ready': {'piece_v2_preview_enabled': True},
    }
    app.state.piece_preview_runtime = {
        'ttl_seconds': 600, 'renderer_version': 'synthetic-renderer.v1'}
    app.include_router(api.router)
    return app, owner, request, prepared, state


def _preview_http_post(app, value, *, headers=None, raw=None, suffix=''):
    import httpx
    if headers is None:
        headers = [('authorization', _B5['AUTH']),
                   ('idempotency-key', 'synthetic-generated-preview')]

    async def call():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                    base_url='http://piece-test.invalid') as client:
            kwargs = {'json': value} if raw is None else {'content': raw}
            return await client.post('/emotion/piece/preview' + suffix,
                                     headers=headers, **kwargs)
    return asyncio.run(call())


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
@pytest.mark.parametrize('named', [False, True])
def test_http_first_issue_and_replay_deliver_exact_persisted_artifact(database, monkeypatch, tier, named):
    from piece_v2_contract import PIECE_V2_CONTRACT_VERSIONS
    conn, _, _ = database
    app, _, request, prepared, state = _preview_http_harness(
        database, monkeypatch, tier=tier, named=named)
    first = _preview_http_post(app, request)
    assert first.status_code == 200
    assert first.headers['cache-control'] == 'no-store'
    value = first.json()
    assert set(value) == {
        'api_contract_version', 'piece_contract_version', 'preview_id',
        'preview_revision', 'row_version', 'expires_at', 'visibility_scope',
        'format_type', 'eligible_formats', 'piece_text', 'piece_text_hash',
        'content_payload', 'content_payload_hash', 'visual_recipe',
        'visual_recipe_hash', 'renderer_version', 'content_status', 'quota', 'plan_capabilities'}
    assert value['api_contract_version'] == PIECE_V2_CONTRACT_VERSIONS['api_contract_version']
    assert value['piece_contract_version'] == PIECE_V2_CONTRACT_VERSIONS['piece_contract_version']
    assert value['quota']['subscription_tier'] == tier
    assert value['quota']['saved_count'] == 0
    assert value['plan_capabilities']['format_selection'] == {
        'free': 'fixed', 'plus': 'automatic', 'premium': 'eligible_choice'}[tier]
    assert value['content_status'] == ('adjusted' if named else 'ready')
    assert value['visibility_scope'] == 'private'
    for field in ('piece_text', 'piece_text_hash', 'content_payload',
                  'content_payload_hash', 'visual_recipe', 'visual_recipe_hash'):
        assert value[field] == prepared.artifact_payload()[field]
    before = conn.execute('SELECT to_jsonb(r) FROM public.piece_records r').fetchone()[0]
    assert (value['piece_text'], value['content_payload'], value['visual_recipe']) == (
        before['piece_text'], before['content_payload'], before['visual_recipe'])
    _no_author(monkeypatch)

    async def no_review(*args):
        raise AssertionError('HTTP replay must not review again.')

    monkeypatch.setattr(review, 'review_prepared_original', no_review)
    app.state.piece_preview_runtime['ttl_seconds'] = 1200
    second = _preview_http_post(app, request)
    assert second.status_code == 200 and second.json() == value
    assert state['http_auth'] == 2
    assert state['authors'] == state['actual_reviews'] == state['http_rpc'] == len(state['posts']) == 1
    assert conn.execute('SELECT to_jsonb(r) FROM public.piece_records r').fetchone()[0] == before
    assert _B5['_B4']['_used'](conn) == 0


def test_http_lost_ack_is_503_then_same_key_read_without_rewrite(database, monkeypatch):
    conn, _, _ = database
    app, _, request, _, state = _preview_http_harness(database, monkeypatch)
    state['lose_ack'] = True
    first = _preview_http_post(app, request)
    assert first.status_code == 503
    assert first.json() == {'code': 'PIECE_TEMPORARILY_UNAVAILABLE'}
    before = conn.execute('SELECT to_jsonb(r) FROM public.piece_records r').fetchone()[0]
    _no_author(monkeypatch)
    second = _preview_http_post(app, request)
    assert second.status_code == 200
    assert second.json()['piece_text'] == before['piece_text']
    assert second.json()['visual_recipe'] == before['visual_recipe']
    assert state['authors'] == state['actual_reviews'] == state['http_rpc'] == len(state['posts']) == 1
    assert conn.execute('SELECT to_jsonb(r) FROM public.piece_records r').fetchone()[0] == before
    assert _B5['_B4']['_used'](conn) == 0


@pytest.mark.parametrize('runtime', [None, {},
    {'ttl_seconds': True, 'renderer_version': 'synthetic-renderer.v1'},
    {'ttl_seconds': 0, 'renderer_version': 'synthetic-renderer.v1'},
    {'ttl_seconds': 600, 'renderer_version': '/private/renderer'},
    {'ttl_seconds': 600, 'renderer_version': ''},
])
def test_http_unadmitted_server_config_never_issues(database, monkeypatch, runtime):
    conn, _, _ = database
    app, _, request, _, state = _preview_http_harness(database, monkeypatch)
    if runtime is None:
        del app.state.piece_preview_runtime
    else:
        app.state.piece_preview_runtime = runtime
    result = _preview_http_post(app, request)
    assert result.status_code == 503
    assert result.json() == {'code': 'PIECE_TEMPORARILY_UNAVAILABLE'}
    assert state['authors'] == state['actual_reviews'] == state['http_rpc'] == 0
    assert not state['reads']
    assert conn.execute('SELECT count(*) FROM public.piece_records').fetchone() == (0,)


@pytest.mark.parametrize('field', ['owner_user_id', 'piece_text', 'content_payload',
    'safety_state', 'ttl_seconds', 'renderer_version', 'subscription_tier'])
def test_http_client_cannot_replace_server_truth(database, monkeypatch, field):
    conn, _, _ = database
    app, _, request, _, state = _preview_http_harness(database, monkeypatch)
    request[field] = _B5['PRIVATE']
    result = _preview_http_post(app, request)
    assert result.status_code == 400
    assert result.json() == {'code': 'PIECE_REQUEST_INVALID'}
    assert state['authors'] == state['actual_reviews'] == state['http_rpc'] == 0
    assert conn.execute('SELECT count(*) FROM public.piece_records').fetchone() == (0,)


@pytest.mark.parametrize('case,code,status', [
    ('no-auth', 'PIECE_AUTH_REQUIRED', 401),
    ('duplicate-auth', 'PIECE_AUTH_REQUIRED', 401),
    ('wrong-auth', 'PIECE_AUTH_REQUIRED', 401),
    ('no-key', 'PIECE_REQUEST_INVALID', 400),
    ('duplicate-key', 'PIECE_REQUEST_INVALID', 400),
    ('blank-key', 'PIECE_REQUEST_INVALID', 400),
    ('query', 'PIECE_REQUEST_INVALID', 400),
    ('malformed-json', 'PIECE_REQUEST_INVALID', 400),
    ('array-body', 'PIECE_REQUEST_INVALID', 400),
])
def test_http_request_failures_are_closed_and_do_not_generate(database, monkeypatch, case, code, status):
    app, _, request, _, state = _preview_http_harness(database, monkeypatch)
    headers = [('authorization', _B5['AUTH']), ('idempotency-key', 'synthetic-generated-preview')]
    kwargs = {}
    if case == 'no-auth':
        headers = headers[1:]
    elif case == 'duplicate-auth':
        headers.append(headers[0])
    elif case == 'wrong-auth':
        headers[0] = ('authorization', 'Bearer wrong-synthetic-user')
    elif case == 'no-key':
        headers = headers[:1]
    elif case == 'duplicate-key':
        headers.append(headers[1])
    elif case == 'blank-key':
        headers[1] = ('idempotency-key', ' ')
    elif case == 'query':
        kwargs['suffix'] = '?ttl_seconds=600'
    elif case == 'malformed-json':
        kwargs['raw'] = ('{"memo":"' + _B5['PRIVATE']).encode()
    else:
        request = [_B5['PRIVATE']]
    result = _preview_http_post(app, request, headers=headers, **kwargs)
    assert result.status_code == status and result.json() == {'code': code}
    assert result.headers['cache-control'] == 'no-store'
    if status == 401:
        assert result.headers['www-authenticate'] == 'Bearer'
    assert state['authors'] == state['actual_reviews'] == state['http_rpc'] == 0


@pytest.mark.parametrize('status,value,expected_status,code', [
    (400, {'code': 'P0001', 'message': 'PIECE_CONFLICT'}, 409, 'PIECE_CONFLICT'),
    (400, {'code': 'P0001', 'message': 'PIECE_PREVIEW_EXPIRED'}, 409, 'PIECE_PREVIEW_EXPIRED'),
    (401, {'code': 'P0001', 'message': 'PIECE_AUTH_REQUIRED'}, 503, 'PIECE_TEMPORARILY_UNAVAILABLE'),
    (404, {'code': 'P0001', 'message': 'PIECE_NOT_FOUND'}, 503, 'PIECE_TEMPORARILY_UNAVAILABLE'),
    (400, {'code': 'XX000', 'message': 'PIECE_CONFLICT'}, 503, 'PIECE_TEMPORARILY_UNAVAILABLE'),
    (400, {'code': 'P0001', 'message': 'private diagnostic'}, 503, 'PIECE_TEMPORARILY_UNAVAILABLE'),
    (200, {}, 503, 'PIECE_TEMPORARILY_UNAVAILABLE'),
    (200, [], 503, 'PIECE_TEMPORARILY_UNAVAILABLE'),
])
def test_http_rpc_protocol_failure_is_not_auth_absence_or_success(database, monkeypatch, status, value, expected_status, code):
    conn, _, _ = database
    app, _, request, _, state = _preview_http_harness(database, monkeypatch)
    state['provider_response'] = (status, value)
    result = _preview_http_post(app, request)
    assert result.status_code == expected_status and result.json() == {'code': code}
    assert state['http_rpc'] == 1 and not state['posts']
    assert conn.execute('SELECT count(*) FROM public.piece_records').fetchone() == (0,)


def test_http_actual_safety_rejection_never_reaches_sql(database, monkeypatch):
    conn, _, _ = database
    app, owner, request, prepared, state = _preview_http_harness(database, monkeypatch)
    blocks = [b.replace('大切にしていない', '大切にしている')
              for b in prepared.artifact_payload()['content_payload']['body_blocks']]
    altered = _changed(prepared, blocks=blocks)

    async def altered_preparation(*args):
        return altered

    monkeypatch.setattr(owner, 'prepare_original', altered_preparation)
    result = _preview_http_post(app, request)
    assert result.status_code == 422
    assert result.json() == {'code': 'PIECE_SAFETY_UNAVAILABLE'}
    assert state['actual_reviews'] == 1 and state['http_rpc'] == 0
    assert conn.execute('SELECT count(*) FROM public.piece_records').fetchone() == (0,)


@pytest.mark.parametrize('kind', ['extra-source', 'text', 'public', 'expiry', 'review-state'])
def test_http_never_serializes_corrupted_or_unclosed_service_output(database, monkeypatch, kind):
    app, owner, request, _, state = _preview_http_harness(database, monkeypatch)
    assert _preview_http_post(app, request).status_code == 200
    result = state['last_internal_result']
    if kind == 'extra-source':
        result['source_lineage'] = {'private': _B5['PRIVATE']}
    elif kind == 'text':
        result['piece_text'] = _B5['PRIVATE']
    elif kind == 'public':
        result['visibility_scope'] = 'public'
    elif kind == 'expiry':
        result['expires_at'] = '2026-10-08T00:00:00'
    else:
        result['safety_state'] = 'unreviewed'

    async def invalid_result(*args, **kwargs):
        return result

    monkeypatch.setattr(owner, 'issue_original', invalid_result)
    response = _preview_http_post(app, request)
    assert response.status_code == 503
    assert response.json() == {'code': 'PIECE_TEMPORARILY_UNAVAILABLE'}
    assert state['http_rpc'] == 1


@pytest.mark.parametrize('cancel', [False, True])
def test_http_unexpected_failure_is_closed_and_task_cancellation_propagates(database, monkeypatch, cancel):
    app, owner, request, _, state = _preview_http_harness(database, monkeypatch)

    async def fail(*args, **kwargs):
        if cancel:
            raise asyncio.CancelledError()
        raise RuntimeError(_B5['PRIVATE'])

    monkeypatch.setattr(owner, 'issue_original', fail)
    if cancel:
        with pytest.raises(asyncio.CancelledError):
            _preview_http_post(app, request)
    else:
        response = _preview_http_post(app, request)
        assert response.status_code == 503
        assert response.json() == {'code': 'PIECE_TEMPORARILY_UNAVAILABLE'}
    assert state['http_rpc'] == 0


# PCE-6 display metadata is fresh; persisted artifact identity is immutable.
@pytest.mark.parametrize('count', [0, 5, 7])
def test_http_quota_display_does_not_admit_or_block_preview(database, monkeypatch, count):
    conn, _, _ = database
    app, _, request, _, state = _preview_http_harness(database, monkeypatch)
    _B5['_B4']['_seed_usage'](conn, count)
    first = _preview_http_post(app, request)
    assert first.status_code == 200
    value = first.json()
    assert value['quota']['saved_count'] == count
    assert value['quota']['remaining_count'] == max(0, 5 - count)
    assert value['quota']['can_save'] is (count < 5)
    assert value['plan_capabilities'] == {'format_selection': 'fixed',
        'theme_ids': ['soft_paper'], 'aspect_ratios': ['4:5'], 'branding_modes': ['required_small']}
    stored = conn.execute('SELECT to_jsonb(r) FROM public.piece_records r').fetchone()[0]
    _B5['_B4']['_seed_usage'](conn, 1)
    _no_author(monkeypatch)
    again = _preview_http_post(app, request)
    assert again.status_code == 200
    latest = again.json()
    assert latest.pop('quota')['saved_count'] == count + 1
    value.pop('quota')
    assert latest == value
    assert conn.execute('SELECT to_jsonb(r) FROM public.piece_records r').fetchone()[0] == stored
    assert state['quota_rpc'] == 2 and state['authors'] == state['http_rpc'] == 1


def test_http_missing_quota_read_stops_before_generation_or_persistence(database, monkeypatch):
    conn, _, _ = database
    app, _, request, _, state = _preview_http_harness(database, monkeypatch)
    conn.execute('DROP FUNCTION public.piece_read_quota_v2(uuid)')
    result = _preview_http_post(app, request)
    assert result.status_code == 503 and result.json() == {'code': 'PIECE_TEMPORARILY_UNAVAILABLE'}
    assert state['quota_rpc'] == 1 and state['authors'] == state['http_rpc'] == 0
    assert not state['reads'] and not state['posts']
    assert conn.execute('SELECT count(*) FROM public.piece_records').fetchone() == (0,)


@pytest.mark.parametrize('replay', [False, True])
def test_http_quota_source_tier_mismatch_is_conflict(database, monkeypatch, replay):
    conn, _, _ = database
    app, _, request, _, state = _preview_http_harness(database, monkeypatch)
    if replay:
        assert _preview_http_post(app, request).status_code == 200
    before = conn.execute('SELECT to_jsonb(r) FROM public.piece_records r').fetchall()
    conn.execute("UPDATE public.profiles SET subscription_tier='plus' WHERE id=%s", (_B5['OWNER'],))
    _no_author(monkeypatch)
    result = _preview_http_post(app, request)
    assert result.status_code == 409 and result.json() == {'code': 'PIECE_CONFLICT'}
    assert state['authors'] == state['http_rpc'] == int(replay)
    assert conn.execute('SELECT to_jsonb(r) FROM public.piece_records r').fetchall() == before


def test_http_replay_checks_quota_tier_again_after_initial_probe(database, monkeypatch):
    app, owner, request, _, state = _preview_http_harness(database, monkeypatch)
    assert _preview_http_post(app, request).status_code == 200
    _no_author(monkeypatch)
    calls = 0
    async def change_at_replay(*args):
        nonlocal calls
        calls += 1
        handoff = state['handoff']
        return handoff if calls == 1 else replace(handoff,
            original=replace(handoff.original, subscription_tier='plus'))
    monkeypatch.setattr(owner._source_adapter, 'resolve_original_handoff', change_at_replay)
    result = _preview_http_post(app, request)
    assert result.status_code == 409 and result.json() == {'code': 'PIECE_CONFLICT'}
    assert calls == 2 and state['authors'] == state['http_rpc'] == 1
