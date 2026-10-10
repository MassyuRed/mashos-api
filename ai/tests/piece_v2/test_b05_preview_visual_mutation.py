"""Persisted visual-only PATCH with synthetic Auth/DB and real CMEE review.

The source/row/transport are test doubles. The original author runs only to
construct the fixture; mutation and restart replay must never call it again.
Native SQL concurrency lives in the separate disposable-database suite. These
cases do not admit a renderer, save-time fit, production route or live tier.
"""
from __future__ import annotations

import asyncio
from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
from pathlib import Path
import sys
from uuid import UUID

import httpx
import pytest
from fastapi import FastAPI, HTTPException

_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_ROOT / 'ai/services/ai_inference'))

import api_piece_v2 as api
import piece_v2_preview_service as service
import piece_v2_safety_review as safety
import supabase_client as shared
from piece_v2_contract import PieceContractError, canonical_json_bytes, canonical_sha256_hex
from piece_v2_runtime_control import PIECE_FEATURE_NAMES
from piece_v2_store import _PREVIEW_RESPONSE_FIELDS
from piece_v2_visual import build_visual_recipe
from test_b05b_piece_visual_change import Adapter, INPUT, OWNER, choice, request

AUTH = 'Bearer synthetic-owner'
VIEWER = '40000000-0000-4000-8000-000000000099'
KEY = 'synthetic-existing-preview'
PRIVATE = 'SYNTHETIC_PRIVATE_DIAGNOSTIC_NOT_FOR_RESPONSE'
PREVIEW_FLAG = 'piece_v2_preview_enabled'
RPC = 'piece_mutate_preview_visual_v2'
RPC_FIELDS = {'p_owner_user_id', 'p_preview_id', 'p_expected_preview_revision',
    'p_expected_record', 'p_visual_recipe', 'p_visual_recipe_hash',
    'p_expected_subscription_tier', 'p_expected_source_state'}
PUBLIC_FIELDS = {'api_contract_version', 'piece_contract_version', 'preview_id',
    'preview_revision', 'row_version', 'expires_at', 'visibility_scope',
    'content_status', 'format_type', 'eligible_formats', 'content_payload',
    'content_payload_hash', 'piece_text', 'piece_text_hash', 'visual_recipe',
    'visual_recipe_hash', 'renderer_version', 'quota', 'plan_capabilities'}
UNCHANGED = ('id', 'owner_user_id', 'piece_contract_version', 'lifecycle_status',
    'preview_request_hash', 'expires_at', 'visibility_scope', 'source_lineage',
    'format_type', 'preview_eligible_formats', 'content_payload',
    'content_payload_hash', 'piece_text', 'piece_text_hash', 'safety_state',
    'renderer_version')
run = asyncio.run


def mutation(selection=None, revision=1):
    return {'expected_preview_revision': revision,
            'visual_selection': choice('quiet_night', '9:16', 'off')
            if selection is None else deepcopy(selection)}


def persisted_result(row, *, replay=False):
    value = dict(row, preview_id=row['id'], eligible_formats=row['preview_eligible_formats'],
                 idempotency_replayed=replay)
    return {key: deepcopy(value[key]) for key in _PREVIEW_RESPONSE_FIELDS}


@pytest.fixture
def harness(monkeypatch):
    adapter = Adapter('premium')
    # The pre-issuance helper's fixture intentionally has only control refs.
    # Add the full synthetic persisted lineage before any artifact is created.
    lineage = adapter.handoff.lineage_payload()
    lineage['source_input'].update(source_owner_user_id=OWNER,
        source_recorded_at=adapter.handoff.original.recorded_at)
    lineage['observation'].update(emlis_observation_result_state='terminal_success',
        supplemental_answer_version=None, supplemental_answer_bundle_commitment=None)
    lineage.update(handoff_contract_version='cocolon.cross_core.source_handoff.v1',
        piece_source_lineage_version='piece.source_lineage.v1',
        semantic_source_roles=['original_input'], lineage_control_roles=['emlis_observation_result'],
        piece_generation_eligibility={'contract_version': 'piece.generation_eligibility.v1',
            'decision': 'eligible', 'reason_codes': []}, body_free=True)
    adapter.handoff = replace(adapter.handoff, _lineage_json=canonical_json_bytes(lineage))
    owner = service.PiecePreviewService(source_adapter=adapter)
    original_request = request(adapter.handoff)
    prepared = run(owner.prepare_original(AUTH, original_request))
    artifact = prepared.artifact_payload()
    assert run(safety.review_prepared_original(prepared)) == 'ready'
    key_hash = hashlib.sha256(KEY.encode()).hexdigest()
    pid = str(UUID(hashlib.sha256(f'piece.preview.v2:{OWNER}:{key_hash}'.encode()).hexdigest()[:32]))
    row = {key: deepcopy(artifact[key]) for key in (
        'format_type', 'content_payload', 'content_payload_hash', 'piece_text',
        'piece_text_hash', 'visual_recipe', 'visual_recipe_hash')}
    row.update(id=pid, owner_user_id=OWNER, piece_contract_version='piece.record.v2',
        lifecycle_status='preview_draft', preview_request_hash=canonical_sha256_hex(original_request),
        preview_revision=1, row_version=1,
        expires_at=(datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
        visibility_scope='private', source_lineage=adapter.handoff.lineage_payload(),
        preview_eligible_formats=artifact['eligible_formats'], safety_state='ready',
        renderer_version='synthetic-retained-renderer.v1')
    assert set(row) == set(service._REPLAY_COLUMNS)
    adapter.checks = 0
    state = {'row': row, 'original': deepcopy(row), 'request': original_request,
        'adapter': adapter, 'owner': owner, 'reads': [], 'posts': [], 'reviews': [],
        'auth': [], 'quota': [], 'read_hook': None, 'before_rpc': None,
        'after_rpc': None, 'review_hook': None, 'review_error': None,
        'review_verdict': None, 'transport_error': None, 'source_error': None,
        'quota_tier': 'premium', 'result_hook': None}
    real_review = safety.review_prepared_original
    real_resolve = adapter.resolve_original_handoff

    def no_author(*args, **kwargs):
        pytest.fail('Persisted visual mutation/replay must not generate Piece text')
    monkeypatch.setattr(service, 'generate_piece_candidate', no_author)

    async def resolve(authorization, input_id):
        if state['source_error']:
            raise state['source_error']
        return await real_resolve(authorization, input_id)
    adapter.resolve_original_handoff = resolve

    async def review(candidate):
        state['reviews'].append(candidate)
        if state['review_hook']:
            state['review_hook'](candidate)
        if state['review_error']:
            raise state['review_error']
        if state['review_verdict'] is not None:
            return state['review_verdict']
        return await real_review(candidate)
    monkeypatch.setattr(safety, 'review_prepared_original', review)
    monkeypatch.setattr(service, 'PieceSavedSourceAdapter', lambda: adapter)

    async def load(owner_id, preview_id):
        state['reads'].append((owner_id, preview_id))
        if state['read_hook']:
            state['read_hook']()
        current = state['row']
        return deepcopy(current) if current is not None and owner_id == OWNER and preview_id == pid else None

    async def rpc(name, args):
        assert name == RPC and set(args) == RPC_FIELDS
        state['posts'].append(deepcopy(args))
        if state['before_rpc']:
            state['before_rpc']()
        if state['transport_error']:
            raise state['transport_error']
        current = state['row']
        assert args['p_owner_user_id'] == OWNER and args['p_preview_id'] == pid
        assert args['p_expected_record'] == current
        assert args['p_expected_preview_revision'] == current['preview_revision']
        current.update(visual_recipe=deepcopy(args['p_visual_recipe']),
            visual_recipe_hash=args['p_visual_recipe_hash'],
            preview_revision=current['preview_revision'] + 1, row_version=current['row_version'] + 1)
        if state['after_rpc']:
            state['after_rpc']()
        result = persisted_result(current)
        if state['result_hook']:
            state['result_hook'](result)
        return result

    state.update(load=load, rpc=rpc, pid=pid)
    app = FastAPI()
    app.include_router(api.router)
    flags = dict.fromkeys(PIECE_FEATURE_NAMES, False)
    flags[PREVIEW_FLAG] = True
    app.state.piece_v2_runtime = {'requested': flags.copy(), 'ready': flags.copy()}
    # No runtime renderer/TTL configuration: mutation retains the stored ones.
    state['app'] = app

    async def verify(authorization):
        state['auth'].append(authorization)
        if authorization not in (AUTH, 'Bearer synthetic-viewer'):
            raise HTTPException(401, PRIVATE)
        return VIEWER if authorization.endswith('viewer') else OWNER
    monkeypatch.setattr(api, '_verify_bearer', verify)

    async def get(path, *, params, timeout):
        assert path == '/rest/v1/piece_records' and timeout == 8.0
        assert params['select'] == ','.join(service._REPLAY_COLUMNS)
        assert params['limit'] == '2'
        value = await load(params['owner_user_id'].removeprefix('eq.'), params['id'].removeprefix('eq.'))
        return httpx.Response(200, json=[] if value is None else [value])

    async def post(name, args, *, timeout):
        assert timeout == 8.0
        if name == 'piece_read_quota_v2':
            state['quota'].append(deepcopy(args))
            return httpx.Response(200, json={'subscription_tier': state['quota_tier'],
                'saved_count': 2, 'server_now': datetime.now(timezone.utc).isoformat()})
        return httpx.Response(200, json=await rpc(name, args))
    monkeypatch.setattr(shared, 'sb_get', get)
    monkeypatch.setattr(shared, 'sb_post_rpc', post)
    return state


def mutate(state, body=None, **overrides):
    options = dict(authenticated_user_id=OWNER, preview_id=state['pid'],
        request=mutation() if body is None else body, expected_subscription_tier=state['quota_tier'],
        rpc=state['rpc'], load_record=state['load'])
    options.update(overrides)
    return run(state['owner'].mutate_original_visual(AUTH, **options))


def send(state, *, body=None, content=None, headers=None, query='', method='PATCH'):
    async def call():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=state['app']),
                base_url='https://test.invalid') as client:
            kwargs = {'headers': {'Authorization': AUTH} if headers is None else headers}
            kwargs['content' if content is not None else 'json'] = content if content is not None else (
                mutation() if body is None else body)
            return await client.request(method, '/emotion/piece/preview/' + state['pid'] + query, **kwargs)
    return run(call())


def error(response, status, code):
    assert response.status_code == status and response.json() == {'code': code}
    assert response.headers['cache-control'] == 'no-store'
    assert PRIVATE not in response.text


@pytest.mark.parametrize('selection', [choice('quiet_night'), choice(ratio='9:16'),
    choice(branding='off'), choice('quiet_night', '9:16', 'off')])
def test_service_mutates_only_recipe_with_current_source_fence_and_no_author(harness, selection):
    s = harness
    result = mutate(s, mutation(selection))
    assert result['preview_id'] == s['pid'] and result['preview_revision'] == result['row_version'] == 2
    assert len(s['posts']) == len(s['reviews']) == 1
    assert {k: s['row'][k] for k in UNCHANGED} == {k: s['original'][k] for k in UNCHANGED}
    assert result['piece_text'].encode() == s['original']['piece_text'].encode()
    assert result['visual_recipe_hash'] == canonical_sha256_hex(result['visual_recipe'])
    args = s['posts'][0]
    assert args['p_expected_record'] == s['original']
    assert args['p_expected_subscription_tier'] == 'premium'
    assert args['p_expected_source_state'] == {
        'original': s['adapter'].handoff.original.original_payload(),
        'thread_id': s['adapter'].handoff.thread_id,
        'thread_revision': s['adapter'].handoff.thread_revision,
        'lineage': s['row']['source_lineage']}
    assert s['reviews'][0].artifact_payload()['piece_text'] == result['piece_text']


@pytest.mark.parametrize('body', [None, [], {}, {'expected_preview_revision': 1},
    dict(mutation(), requested_format='quote'), dict(mutation(), owner_user_id=VIEWER),
    dict(mutation(), piece_text=PRIVATE), dict(mutation(), content_payload={}),
    dict(mutation(), visual_recipe={}), dict(mutation(), source_ref={}),
    mutation(revision=True), mutation(revision=0), mutation(revision='1'),
    mutation(revision=9223372036854775808),
    {'expected_preview_revision': 1, 'visual_selection': {'theme_id': None}},
    {'expected_preview_revision': 1, 'visual_selection': dict(choice(), extra=PRIVATE)}])
def test_closed_mutation_request_rejects_before_any_read(harness, body):
    s = harness
    with pytest.raises(PieceContractError) as caught:
        run(s['owner'].mutate_original_visual(AUTH, authenticated_user_id=OWNER,
            preview_id=s['pid'], request=body, expected_subscription_tier='premium',
            rpc=s['rpc'], load_record=s['load']))
    assert caught.value.code == 'PIECE_REQUEST_INVALID' and caught.value.detail is None
    assert s['reads'] == s['posts'] == s['reviews'] == []


@pytest.mark.parametrize('field,value,code', [
    ('preview_revision', 2, 'PIECE_PREVIEW_STALE'),
    ('lifecycle_status', 'saved', 'PIECE_CONFLICT'),
    ('lifecycle_status', 'cancelled', 'PIECE_CONFLICT'),
    ('expires_at', '2000-01-01T00:00:00+00:00', 'PIECE_PREVIEW_EXPIRED'),
    ('piece_text_hash', '0' * 64, 'PIECE_HASH_MISMATCH'),
    ('content_payload_hash', '0' * 64, 'PIECE_HASH_MISMATCH'),
    ('visual_recipe_hash', '0' * 64, 'PIECE_HASH_MISMATCH')])
def test_noncurrent_or_corrupt_preview_cannot_be_repaired(harness, field, value, code):
    s = harness; s['row'][field] = value
    with pytest.raises(PieceContractError) as caught:
        mutate(s)
    assert caught.value.code == code and caught.value.detail is None
    assert s['posts'] == s['reviews'] == []


@pytest.mark.parametrize('check', [1, 2])
def test_source_change_during_visual_preparation_prevents_write(harness, check):
    s = harness
    def changed(n):
        if n == check:
            s['adapter'].handoff = replace(s['adapter'].handoff, thread_revision=2)
    s['adapter'].on_check = changed
    with pytest.raises(PieceContractError, match='^PIECE_CONFLICT$'):
        mutate(s)
    assert s['posts'] == []


def test_source_change_during_safety_review_prevents_write(harness):
    s = harness
    def changed(_candidate):
        s['adapter'].handoff = replace(s['adapter'].handoff, thread_revision=2)
    s['review_hook'] = changed
    with pytest.raises(PieceContractError, match='^PIECE_CONFLICT$'):
        mutate(s)
    assert len(s['reviews']) == 1 and s['posts'] == []


@pytest.mark.parametrize('code', ['PIECE_SOURCE_NOT_FOUND', 'PIECE_SOURCE_NOT_ELIGIBLE',
                                'PIECE_AUTH_REQUIRED'])
def test_lost_source_access_preserves_exact_body_free_code(harness, code):
    s = harness; s['source_error'] = PieceContractError(code, PRIVATE)
    with pytest.raises(PieceContractError) as caught:
        mutate(s)
    assert caught.value.code == code and caught.value.detail is None
    assert s['posts'] == s['reviews'] == []


def test_current_tier_must_equal_quota_snapshot(harness):
    s = harness
    with pytest.raises(PieceContractError, match='^PIECE_CONFLICT$'):
        mutate(s, expected_subscription_tier='free')
    assert s['posts'] == s['reviews'] == []


@pytest.mark.parametrize('selection,allowed', [(choice('quiet_night'), True),
    (choice(ratio='9:16'), False), (choice(branding='off'), False)])
def test_visual_entitlement_uses_fresh_plus_tier_not_previous_premium(harness, selection, allowed):
    s = harness
    s['adapter'].handoff = replace(s['adapter'].handoff,
        original=replace(s['adapter'].handoff.original, subscription_tier='plus'))
    s['quota_tier'] = 'plus'
    if allowed:
        result = mutate(s, mutation(selection))
        assert result['visual_recipe']['theme']['theme_id'] == 'quiet_night'
        assert result['visual_recipe']['aspect_ratio'] == '4:5'
        assert result['visual_recipe']['branding']['branding_mode'] == 'required_subtle'
        assert s['posts'][0]['p_expected_subscription_tier'] == 'plus'
    else:
        with pytest.raises(PieceContractError, match='^PIECE_VISUAL_SELECTION_NOT_ALLOWED$'):
            mutate(s, mutation(selection))
        assert s['posts'] == []


@pytest.mark.parametrize('verdict', ['transformed', 'blocked', 'ineligible'])
def test_visual_change_cannot_change_or_bypass_persisted_safety_state(harness, verdict):
    s = harness; s['review_verdict'] = verdict
    with pytest.raises(PieceContractError, match='^PIECE_SAFETY_UNAVAILABLE$'):
        mutate(s)
    assert len(s['reviews']) == 1 and s['posts'] == []
    assert s['row'] == s['original']


def test_request_selection_is_detached_before_first_await(harness):
    s = harness; body = mutation()
    s['read_hook'] = lambda: body['visual_selection'].update(theme_id='soft_paper', branding_mode=None)
    result = mutate(s, body)
    assert result['visual_recipe']['theme']['theme_id'] == 'quiet_night'
    assert result['visual_recipe']['branding']['branding_mode'] == 'off'


@pytest.mark.parametrize('at', ['source', 'review', 'rpc'])
def test_cancellation_propagates_without_recovery_write(harness, at):
    s = harness
    s[{'source': 'source_error', 'review': 'review_error', 'rpc': 'transport_error'}[at]] = asyncio.CancelledError()
    with pytest.raises(asyncio.CancelledError):
        mutate(s)
    assert len(s['posts']) == (1 if at == 'rpc' else 0)
    assert s['row'] == s['original']


def test_lost_mutation_ack_is_not_automatically_retried_or_newly_issued(harness):
    s = harness
    def lose_ack():
        raise httpx.ReadTimeout(PRIVATE)
    s['after_rpc'] = lose_ack
    with pytest.raises(PieceContractError) as caught:
        mutate(s)
    assert caught.value.code == 'PIECE_TEMPORARILY_UNAVAILABLE' and caught.value.detail is None
    assert len(s['posts']) == 1 and s['row']['preview_revision'] == 2
    assert {k: s['row'][k] for k in UNCHANGED} == {k: s['original'][k] for k in UNCHANGED}
    with pytest.raises(PieceContractError, match='^PIECE_PREVIEW_STALE$'):
        mutate(s)
    assert len(s['posts']) == 1
    replay = run(s['owner'].read_original_preview(AUTH, s['request'], idempotency_key=KEY,
        expected_subscription_tier='premium', load_record=s['load']))
    assert replay['preview_revision'] == 2 and replay['idempotency_replayed'] is True
    assert len(s['posts']) == 1


@pytest.mark.parametrize('field,value', [('piece_text', PRIVATE), ('preview_revision', 1),
    ('row_version', 1), ('renderer_version', 'substituted-renderer.v1'),
    ('expires_at', '2099-01-01T00:00:00+00:00'), ('idempotency_replayed', True),
    ('private_debug', PRIVATE)])
def test_malformed_success_ack_is_not_exposed_or_retried(harness, field, value):
    s = harness; s['result_hook'] = lambda result: result.update({field: value})
    with pytest.raises(PieceContractError, match='^PIECE_TEMPORARILY_UNAVAILABLE$'):
        mutate(s)
    assert len(s['posts']) == 1 and s['row']['preview_revision'] == 2


def test_same_create_request_key_recovers_current_revision_without_author_or_write(harness):
    s = harness; current = mutate(s)
    s['posts'].clear(); s['reviews'].clear(); s['reads'].clear()
    result = run(s['owner'].read_original_preview(AUTH, s['request'], idempotency_key=KEY,
        expected_subscription_tier='premium', load_record=s['load']))
    assert result == dict(current, idempotency_replayed=True)
    assert result['visual_recipe'] != s['original']['visual_recipe']
    assert result['expires_at'] == s['original']['expires_at']
    assert s['posts'] == s['reviews'] == []


@pytest.mark.parametrize('revision', [1, 2])
def test_create_replay_still_binds_original_request_hash_after_visual_change(harness, revision):
    s = harness
    if revision == 2:
        mutate(s)
    altered = deepcopy(s['request']); altered['visual_selection'] = choice('quiet_night')
    s['posts'].clear(); s['reviews'].clear()
    with pytest.raises(PieceContractError, match='^PIECE_CONFLICT$'):
        run(s['owner'].read_original_preview(AUTH, altered, idempotency_key=KEY,
            expected_subscription_tier='premium', load_record=s['load']))
    assert s['posts'] == s['reviews'] == []


def test_revision_one_replay_does_not_adopt_different_valid_recipe(harness):
    s = harness
    recipe = build_visual_recipe(s['row']['format_type'], tier='premium',
        language=s['row']['content_payload']['language'], theme='quiet_night')
    s['row'].update(visual_recipe=recipe, visual_recipe_hash=canonical_sha256_hex(recipe))
    with pytest.raises(PieceContractError, match='^PIECE_VISUAL_SELECTION_NOT_ALLOWED$'):
        run(s['owner'].read_original_preview(AUTH, s['request'], idempotency_key=KEY,
            expected_subscription_tier='premium', load_record=s['load']))
    assert s['posts'] == s['reviews'] == []


def test_http_patch_uses_current_plan_and_exact_preview_response_without_runtime_upgrade(harness):
    s = harness; response = send(s)
    assert response.status_code == 200 and response.headers['cache-control'] == 'no-store'
    value = response.json()
    assert set(value) == PUBLIC_FIELDS
    assert value['preview_id'] == s['pid'] and value['preview_revision'] == value['row_version'] == 2
    assert value['renderer_version'] == s['original']['renderer_version']
    assert value['quota']['saved_count'] == 2 and value['quota']['subscription_tier'] == 'premium'
    assert value['plan_capabilities']['format_selection'] == 'eligible_choice'
    assert value['plan_capabilities']['aspect_ratios'] == ['4:5', '9:16']
    assert s['quota'] == [{'p_owner_user_id': OWNER}] and s['auth'] == [AUTH]
    assert len(s['posts']) == len(s['reviews']) == 1
    assert not hasattr(s['app'].state, 'piece_preview_runtime')
    assert 'source_lineage' not in value and PRIVATE not in response.text


@pytest.mark.parametrize('headers', [{}, {'Authorization': 'Bearer bad'},
    [('Authorization', AUTH), ('Authorization', AUTH)]])
def test_http_auth_precedes_feature_gate_and_private_body_parsing(harness, headers):
    s = harness; s['app'].state.piece_v2_runtime = {}
    response = send(s, headers=headers, content=PRIVATE.encode())
    error(response, 401, 'PIECE_AUTH_REQUIRED')
    assert response.headers['www-authenticate'] == 'Bearer'
    assert s['quota'] == s['reads'] == s['posts'] == []


def test_http_default_off_does_not_parse_or_start_quota_or_preview_io(harness):
    s = harness; s['app'].state.piece_v2_runtime = {}
    error(send(s, content=PRIVATE.encode()), 503, 'PIECE_FEATURE_DISABLED')
    assert s['auth'] == [AUTH] and s['quota'] == s['reads'] == s['posts'] == []


@pytest.mark.parametrize('content', [b'null', b'[]', b'{', b'\xff'])
def test_http_malformed_json_returns_closed_error_without_io(harness, content):
    s = harness
    error(send(s, content=content), 400, 'PIECE_REQUEST_INVALID')
    assert s['quota'] == s['reads'] == s['posts'] == []


def test_http_query_and_client_format_are_rejected_before_io(harness):
    s = harness
    error(send(s, query='?subscription_tier=premium'), 400, 'PIECE_REQUEST_INVALID')
    error(send(s, body=dict(mutation(), requested_format='quote')), 400, 'PIECE_REQUEST_INVALID')
    assert s['quota'] == s['reads'] == s['posts'] == []


def test_http_mutation_uses_revision_not_a_new_creation_key(harness):
    s = harness
    error(send(s, headers={'Authorization': AUTH, 'Idempotency-Key': 'new-key'}),
          400, 'PIECE_REQUEST_INVALID')
    assert s['quota'] == s['reads'] == s['posts'] == []


@pytest.mark.parametrize('body,code,status', [(mutation(revision=2), 'PIECE_PREVIEW_STALE', 409),
    (mutation(choice('unknown-theme')), 'PIECE_VISUAL_SELECTION_NOT_ALLOWED', 422)])
def test_http_stale_revision_or_unavailable_visual_choice_has_no_write(harness, body, code, status):
    s = harness
    error(send(s, body=body), status, code)
    assert s['posts'] == [] and s['row'] == s['original']


def test_http_other_owner_is_concealed_without_source_review_or_write(harness):
    s = harness
    error(send(s, headers={'Authorization': 'Bearer synthetic-viewer'}), 404, 'PIECE_NOT_FOUND')
    assert s['reads'] == [(VIEWER, s['pid'])] and s['reviews'] == s['posts'] == []


@pytest.mark.parametrize('where,write_count', [('review', 0), ('after_rpc', 1)])
def test_http_stop_latches_before_dispatch_or_after_committed_write(harness, where, write_count):
    s = harness
    def stop(*_args):
        s['app'].state.piece_v2_runtime = {}
    s['review_hook' if where == 'review' else 'after_rpc'] = stop
    error(send(s), 503, 'PIECE_FEATURE_DISABLED')
    assert len(s['posts']) == write_count
    assert s['row']['preview_revision'] == 1 + write_count


def test_http_lost_ack_returns_body_free_unavailable_once(harness):
    s = harness; s['transport_error'] = httpx.ReadTimeout(PRIVATE)
    error(send(s), 503, 'PIECE_TEMPORARILY_UNAVAILABLE')
    assert len(s['posts']) == 1


def test_http_cancellation_remains_cancellation_through_all_wrappers(harness):
    s = harness; s['transport_error'] = asyncio.CancelledError()
    with pytest.raises(asyncio.CancelledError):
        send(s)
    assert len(s['posts']) == 1 and s['row'] == s['original']

