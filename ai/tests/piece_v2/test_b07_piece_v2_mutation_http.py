"""B7 HTTP-to-existing-B4 wiring only; synthetic Auth and PostgREST replies.

These tests execute the real router and the unchanged terminal store adapter.
They do not prove SQL purge/locking, live Auth, RN, feed invalidation or safety.
"""
import asyncio
import hashlib
import json
import sys
from types import SimpleNamespace

import httpx
import pytest
from fastapi import FastAPI, HTTPException

import api_piece_v2 as api

OWNER = '11111111-1111-4111-8111-111111111111'
OTHER = '44444444-4444-4444-8444-444444444444'
PID = '22222222-2222-4222-8222-222222222222'
RID = '33333333-3333-4333-8333-333333333333'
KEY = 'synthetic-delete-key'
SECRET = 'PRIVATE_SOURCE_MUST_NOT_LEAK'
OPS = ('visibility', 'delete')


class Reply:
    def __init__(self, status, body):
        self.status_code, self.body = status, body

    def json(self):
        if isinstance(self.body, Exception):
            raise self.body
        return self.body


@pytest.fixture
def harness(monkeypatch):
    state = SimpleNamespace(calls=[], auth_calls=[], reply=None, error=None,
                            auth_value=OWNER, auth_error=None)

    async def verify(value):
        state.auth_calls.append(value)
        if state.auth_error is not None:
            raise state.auth_error
        return state.auth_value

    async def rpc(name, args, *, timeout):
        state.calls.append((name, dict(args), timeout))
        if state.error is not None:
            raise state.error
        if state.reply is not None:
            return state.reply
        if name == 'piece_set_visibility_v2':
            return Reply(200, {'piece_id': PID, 'visibility_scope': args['p_visibility_scope'],
                               'row_version': 8})
        if name == 'piece_delete_v2':
            return Reply(200, {'piece_id': PID, 'receipt_id': RID, 'outcome': 'succeeded',
                               'idempotency_replayed': False})
        if name == 'piece_cancel_preview_v2':
            return Reply(200, {'preview_id': PID, 'preview_revision': 7,
                'row_version': 8, 'lifecycle_status': 'cancelled', 'idempotency_replayed': False})
        raise AssertionError('Unexpected RPC')

    monkeypatch.setattr(api, '_verify_bearer', verify)
    monkeypatch.setitem(sys.modules, 'supabase_client', SimpleNamespace(sb_post_rpc=rpc))
    app = FastAPI()
    app.include_router(api.router)
    from piece_v2_runtime_control import PIECE_FEATURE_NAMES
    app.state.piece_v2_runtime = {
        'requested': dict.fromkeys(PIECE_FEATURE_NAMES, True),
        'ready': dict.fromkeys(PIECE_FEATURE_NAMES, True)}
    state.app = app

    async def send(op, *, body=None, headers=None, path_id=PID, query='', raw=None):
        method = 'PATCH' if op == 'visibility' else 'DELETE'
        suffix = '/visibility' if op == 'visibility' else ''
        url = '/emotion/piece/' + path_id + suffix + query
        if headers is None:
            headers = {'Authorization': 'Bearer synthetic', 'Idempotency-Key': KEY}
        if body is None:
            body = {'expected_row_version': 7}
            if op == 'visibility':
                body['visibility_scope'] = 'public'
        data = raw if raw is not None else json.dumps(body)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                     base_url='http://piece-test') as client:
            return await client.request(method, url, headers=headers, content=data)
    state.send = send
    return state


def request(harness, op, **kwargs):
    return asyncio.run(harness.send(op, **kwargs))


def assert_error(response, status, code):
    assert response.status_code == status, response.text
    assert response.json() == {'code': code}
    assert response.headers['cache-control'] == 'no-store'
    assert SECRET not in response.text
    if status == 401:
        assert response.headers['www-authenticate'] == 'Bearer'


@pytest.mark.parametrize('scope', ['public', 'private'])
def test_visibility_uses_existing_terminal_and_authenticated_owner(harness, scope):
    response = request(harness, 'visibility', body={'expected_row_version': 7, 'visibility_scope': scope})
    assert response.status_code == 200
    assert response.json() == {'piece_id': PID, 'visibility_scope': scope, 'row_version': 8}
    assert response.headers['cache-control'] == 'no-store'
    assert harness.calls == [('piece_set_visibility_v2', {'p_owner_user_id': OWNER,
        'p_piece_id': PID, 'p_expected_row_version': 7, 'p_visibility_scope': scope}, 8.0)]
    assert len(harness.auth_calls) == 1


def test_delete_uses_same_key_hash_and_closed_receipt(harness):
    response = request(harness, 'delete')
    assert response.status_code == 200
    assert response.json() == {'piece_id': PID, 'receipt_id': RID, 'outcome': 'succeeded',
                               'idempotency_replayed': False}
    assert harness.calls == [('piece_delete_v2', {'p_owner_user_id': OWNER, 'p_piece_id': PID,
        'p_expected_row_version': 7, 'p_idempotency_key_hash': hashlib.sha256(KEY.encode()).hexdigest()}, 8.0)]
    assert KEY not in str(harness.calls)
    assert response.headers['cache-control'] == 'no-store'


@pytest.mark.parametrize('op', OPS)
def test_piece_prefixed_identity_matches_existing_owner_detail(harness, op):
    response = request(harness, op, path_id='piece:' + PID)
    assert response.status_code == 200
    assert harness.calls[0][1]['p_piece_id'] == PID


@pytest.mark.parametrize('op', OPS)
@pytest.mark.parametrize('headers', [[], [('authorization', 'Bearer')],
    [('authorization', 'Basic synthetic')], [('authorization', 'Bearer a b')],
    [('authorization', 'Bearer a'), ('authorization', 'Bearer b')]])
def test_invalid_auth_is_rejected_before_body_and_rpc(harness, op, headers):
    response = request(harness, op, headers=headers, raw='{bad ' + SECRET)
    assert_error(response, 401, 'PIECE_AUTH_REQUIRED')
    assert harness.calls == []
    assert harness.auth_calls == []


@pytest.mark.parametrize('op', OPS)
@pytest.mark.parametrize('value', [None, 42, '', 'not-a-uuid', '00000000-0000-0000-0000-000000000000'])
def test_non_owner_verifier_result_never_reaches_store(harness, op, value):
    harness.auth_value = value
    assert_error(request(harness, op), 401, 'PIECE_AUTH_REQUIRED')
    assert harness.calls == []


@pytest.mark.parametrize('op', OPS)
@pytest.mark.parametrize('status,expected', [(401, 401), (403, 401), (500, 503)])
def test_auth_lookup_failure_does_not_expose_provider_detail(harness, op, status, expected):
    harness.auth_error = HTTPException(status_code=status, detail=SECRET)
    assert_error(request(harness, op), expected,
                 'PIECE_AUTH_REQUIRED' if expected == 401 else 'PIECE_TEMPORARILY_UNAVAILABLE')
    assert harness.calls == []


@pytest.mark.parametrize('op', OPS)
@pytest.mark.parametrize('version', [None, False, True, 0, -1, 1.0, '7', 9223372036854775808])
def test_invalid_row_versions_do_not_reach_rpc(harness, op, version):
    body = {'expected_row_version': version}
    if op == 'visibility': body['visibility_scope'] = 'public'
    assert_error(request(harness, op, body=body), 400, 'PIECE_REQUEST_INVALID')
    assert harness.calls == []


@pytest.mark.parametrize('op', OPS)
@pytest.mark.parametrize('extra', ['user_id', 'owner_user_id', 'piece_text', 'visual_recipe',
                                   'safety_state', 'subscription_tier', 'idempotency_key'])
def test_client_cannot_supply_identity_body_safety_or_entitlement(harness, op, extra):
    body = {'expected_row_version': 7, extra: SECRET}
    if op == 'visibility': body['visibility_scope'] = 'public'
    assert_error(request(harness, op, body=body), 400, 'PIECE_REQUEST_INVALID')
    assert harness.calls == []


@pytest.mark.parametrize('scope', [None, '', 'friends', 'PRIVATE', 1, True, {}, []])
def test_visibility_cannot_default_or_admit_an_unknown_scope(harness, scope):
    assert_error(request(harness, 'visibility', body={'expected_row_version': 7,
                 'visibility_scope': scope}), 400, 'PIECE_REQUEST_INVALID')
    assert harness.calls == []


@pytest.mark.parametrize('op', OPS)
@pytest.mark.parametrize('body', [{}, [], 'private-input'])
def test_missing_or_wrong_body_shape(harness, op, body):
    assert_error(request(harness, op, body=body), 400, 'PIECE_REQUEST_INVALID')
    assert harness.calls == []


@pytest.mark.parametrize('op', OPS)
@pytest.mark.parametrize('raw', ['', '{bad', '\ud800'])
def test_invalid_json_is_not_reflected(harness, op, raw):
    raw = raw.encode('utf-8', errors='surrogatepass')
    assert_error(request(harness, op, raw=raw), 400, 'PIECE_REQUEST_INVALID')
    assert harness.calls == []


@pytest.mark.parametrize('op', OPS)
@pytest.mark.parametrize('path_id', ['not-a-uuid', 'piece:broken', '00000000-0000-0000-0000-000000000000'])
def test_invalid_id_does_not_reach_rpc(harness, op, path_id):
    assert_error(request(harness, op, path_id=path_id), 400, 'PIECE_REQUEST_INVALID')
    assert harness.calls == []


@pytest.mark.parametrize('op', OPS)
def test_query_fields_are_not_an_alternate_write_channel(harness, op):
    assert_error(request(harness, op, query='?owner_user_id=' + OTHER), 400, 'PIECE_REQUEST_INVALID')
    assert harness.calls == []


@pytest.mark.parametrize('keys', [[], [''], ['   '], ['a', 'b']])
def test_delete_requires_one_nonempty_idempotency_key(harness, keys):
    headers = [('Authorization', 'Bearer synthetic')] + [('Idempotency-Key', k) for k in keys]
    assert_error(request(harness, 'delete', headers=headers), 400, 'PIECE_REQUEST_INVALID')
    assert harness.calls == []


@pytest.mark.parametrize('op', OPS)
@pytest.mark.parametrize('code,status', [('PIECE_REQUEST_INVALID', 400), ('PIECE_AUTH_REQUIRED', 401),
    ('PIECE_NOT_FOUND', 404), ('PIECE_CONFLICT', 409), ('PIECE_TEMPORARILY_UNAVAILABLE', 503)])
def test_only_exact_known_sql_raise_is_mapped(harness, op, code, status):
    harness.reply = Reply(400, {'code': 'P0001', 'message': code, 'details': SECRET, 'hint': SECRET})
    assert_error(request(harness, op), status, code)
    assert len(harness.calls) == 1


@pytest.mark.parametrize('op', OPS)
@pytest.mark.parametrize('status,body', [
    (404, {'code': 'P0001', 'message': 'PIECE_NOT_FOUND'}),
    (401, {'code': 'P0001', 'message': 'PIECE_AUTH_REQUIRED'}),
    (400, {'code': '42501', 'message': 'PIECE_NOT_FOUND'}),
    (400, {'code': 'P0001', 'message': 'PIECE_NOT_FOUND ' + SECRET}),
    (400, {'code': 'P0001', 'message': 'PIECE_QUOTA_EXHAUSTED'}),
    (400, {'code': 'P0001', 'message': ['PIECE_NOT_FOUND']}),
    (200, []), (200, None), (200, ValueError(SECRET)), (502, SECRET),
])
def test_transport_failure_is_not_record_absence_or_success(harness, op, status, body):
    harness.reply = Reply(status, body)
    assert_error(request(harness, op), 503, 'PIECE_TEMPORARILY_UNAVAILABLE')
    assert len(harness.calls) == 1


@pytest.mark.parametrize('op', OPS)
@pytest.mark.parametrize('kind', ['wrong-id', 'extra-body', 'missing', 'wrong-type'])
def test_malformed_ack_cannot_be_returned_as_success(harness, op, kind):
    value = ({'piece_id': PID, 'visibility_scope': 'public', 'row_version': 8}
             if op == 'visibility' else
             {'piece_id': PID, 'receipt_id': RID, 'outcome': 'succeeded', 'idempotency_replayed': False})
    if kind == 'wrong-id': value['piece_id'] = OTHER
    elif kind == 'extra-body': value['piece_text'] = SECRET
    elif kind == 'missing': value.pop('piece_id')
    elif op == 'visibility': value['row_version'] = True
    else: value['idempotency_replayed'] = 'true'
    harness.reply = Reply(200, value)
    assert_error(request(harness, op), 503, 'PIECE_TEMPORARILY_UNAVAILABLE')
    assert len(harness.calls) == 1


def test_visibility_ack_cannot_say_another_scope_was_saved(harness):
    harness.reply = Reply(200, {'piece_id': PID, 'visibility_scope': 'private', 'row_version': 8})
    assert_error(request(harness, 'visibility'), 503, 'PIECE_TEMPORARILY_UNAVAILABLE')
    assert len(harness.calls) == 1


@pytest.mark.parametrize('op', OPS)
def test_timeout_is_not_retried_or_reclassified(harness, op):
    harness.error = TimeoutError(SECRET)
    assert_error(request(harness, op), 503, 'PIECE_TEMPORARILY_UNAVAILABLE')
    assert len(harness.calls) == 1


def test_explicit_same_key_delete_replay_keeps_receipt_and_authenticates_again(harness):
    first = request(harness, 'delete')
    harness.reply = Reply(200, {'piece_id': PID, 'receipt_id': RID, 'outcome': 'succeeded',
                               'idempotency_replayed': True})
    second = request(harness, 'delete')
    assert first.status_code == second.status_code == 200
    assert first.json()['receipt_id'] == second.json()['receipt_id'] == RID
    assert second.json()['idempotency_replayed'] is True
    assert len(harness.auth_calls) == len(harness.calls) == 2
    assert harness.calls[0] == harness.calls[1]


@pytest.mark.parametrize('op', OPS)
def test_each_request_forwards_its_fresh_owner_without_owner_pre_read(harness, op):
    assert request(harness, op).status_code == 200
    harness.auth_value = OTHER
    harness.reply = Reply(400, {'code': 'P0001', 'message': 'PIECE_NOT_FOUND'})
    assert_error(request(harness, op), 404, 'PIECE_NOT_FOUND')
    assert len(harness.auth_calls) == len(harness.calls) == 2
    assert harness.calls[-1][1]['p_owner_user_id'] == OTHER


@pytest.mark.parametrize('op', OPS)
def test_task_cancellation_is_not_swallowed(harness, op):
    harness.error = asyncio.CancelledError()
    with pytest.raises(asyncio.CancelledError):
        request(harness, op)
    assert len(harness.calls) == 1


def test_existing_preview_cancel_still_uses_its_original_operation(harness):
    response = request(harness, 'delete', path_id='preview/' + PID,
                       body={'expected_preview_revision': 7})
    assert response.status_code == 200
    assert response.json()['lifecycle_status'] == 'cancelled'
    assert harness.calls == [('piece_cancel_preview_v2', {'p_owner_user_id': OWNER,
                             'p_preview_id': PID, 'p_expected_preview_revision': 7}, 8.0)]


@pytest.mark.parametrize('scope', ['public', 'private'])
@pytest.mark.parametrize('padding', [' ', '\t', '\n', '\u3000'])
def test_visibility_compares_ack_to_existing_contract_normalization(harness, scope, padding):
    response = request(harness, 'visibility', body={
        'expected_row_version': 7, 'visibility_scope': padding + scope + padding})
    assert response.status_code == 200
    assert response.json() == {'piece_id': PID, 'visibility_scope': scope, 'row_version': 8}
    assert response.headers['cache-control'] == 'no-store'
    assert len(harness.calls) == 1
    assert harness.calls[0][1]['p_visibility_scope'] == scope


@pytest.mark.parametrize('scope', ['public', 'private'])
@pytest.mark.parametrize('padding', ['', ' '])
def test_visibility_normalization_does_not_admit_wrong_scope_ack(harness, scope, padding):
    opposite = 'private' if scope == 'public' else 'public'
    harness.reply = Reply(200, {'piece_id': PID, 'visibility_scope': opposite, 'row_version': 8})
    response = request(harness, 'visibility', body={
        'expected_row_version': 7, 'visibility_scope': padding + scope + padding})
    assert_error(response, 503, 'PIECE_TEMPORARILY_UNAVAILABLE')
    assert len(harness.calls) == 1


@pytest.mark.parametrize('op', OPS)
def test_mutation_missing_flags_precedes_schema_and_rpc(harness, op):
    harness.app.state.piece_v2_runtime = None
    assert_error(request(harness, op, raw='{'+SECRET), 503, 'PIECE_FEATURE_DISABLED')
    assert harness.calls == []
    assert_error(request(harness, op, headers=[]), 401, 'PIECE_AUTH_REQUIRED')


@pytest.mark.parametrize('scope', ['public', ' public '])
def test_public_mutation_off_still_allows_private_target(harness, scope):
    harness.app.state.piece_v2_runtime['requested']['piece_v2_public_write_enabled'] = False
    assert_error(request(harness, 'visibility', body={'expected_row_version': 7,
        'visibility_scope': scope}), 503, 'PIECE_FEATURE_DISABLED')
    assert harness.calls == []
    assert request(harness, 'visibility', body={'expected_row_version': 7,
        'visibility_scope': 'private'}).status_code == 200
    assert len(harness.calls) == 1


@pytest.mark.parametrize('flag', ['piece_v2_owner_read_enabled', 'piece_v2_public_read_enabled',
                                'piece_v2_visibility_toggle_enabled'])
def test_visibility_dependency_cannot_be_bypassed(harness, flag):
    harness.app.state.piece_v2_runtime['ready'][flag] = False
    assert_error(request(harness, 'visibility', body={'expected_row_version': 7,
        'visibility_scope': 'private'}), 503, 'PIECE_FEATURE_DISABLED')
    assert harness.calls == []


def test_owner_recovery_delete_does_not_need_generation_or_public_flags(harness):
    requested = harness.app.state.piece_v2_runtime['requested']
    requested.update(dict.fromkeys(requested, False))
    requested.update(piece_v2_owner_read_enabled=True, piece_v2_delete_enabled=True)
    assert request(harness, 'delete').status_code == 200
    assert len(harness.calls) == 1


@pytest.mark.parametrize('flag', ['piece_v2_owner_read_enabled', 'piece_v2_delete_enabled'])
def test_delete_stop_and_dependency(harness, flag):
    harness.app.state.piece_v2_runtime['ready'][flag] = False
    assert_error(request(harness, 'delete'), 503, 'PIECE_FEATURE_DISABLED')
    assert harness.calls == []


@pytest.mark.parametrize('op', OPS)
def test_mutation_stop_after_dispatch_never_retries(harness, monkeypatch, op):
    original = api._owner_mutation_rpc
    async def stop(name, args):
        result = await original(name, args)
        harness.app.state.piece_v2_runtime = None
        return result
    monkeypatch.setattr(api, '_owner_mutation_rpc', stop)
    assert_error(request(harness, op), 503, 'PIECE_FEATURE_DISABLED')
    assert len(harness.calls) == 1


def test_observed_stop_stays_latched_if_service_reenables(harness, monkeypatch):
    import piece_v2_store
    async def service(**kwargs):
        harness.app.state.piece_v2_runtime['requested']['piece_v2_delete_enabled'] = False
        try:
            await kwargs['rpc']('piece_delete_v2', {})
        except api.PieceContractError:
            pass
        harness.app.state.piece_v2_runtime['requested']['piece_v2_delete_enabled'] = True
        return {'unexpected': 'must not be returned'}
    monkeypatch.setattr(piece_v2_store, 'delete_piece', service)
    assert_error(request(harness, 'delete'), 503, 'PIECE_FEATURE_DISABLED')
    assert harness.calls == []


def test_preview_cancel_remains_available_with_all_flags_off(harness):
    harness.app.state.piece_v2_runtime = None
    response = request(harness, 'delete', path_id='preview/'+PID,
        body={'expected_preview_revision': 7})
    assert response.status_code == 200
    assert harness.calls[0][0] == 'piece_cancel_preview_v2'
