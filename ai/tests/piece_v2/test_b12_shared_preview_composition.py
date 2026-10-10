"""Shared API cutover preparation; no listener, live Auth/DB or RN device.

Exercise the real shared composition, submit handler, middleware and existing
preview handlers. Reuse B14's synthetic bearer/source/service/RPC/projection;
keep the real v2 request validator so old input DTOs cannot pass this seam.
"""
import asyncio
from collections import Counter
import copy
from pathlib import Path
import socket
import sys
from types import SimpleNamespace

import httpx
import pytest
from fastapi.routing import APIRoute, iter_route_contexts

_AI_ROOT = Path(__file__).resolve().parents[2]
for _path in (_AI_ROOT, _AI_ROOT / 'services', _AI_ROOT / 'services' / 'ai_inference'):
    sys.path.insert(0, str(_path))

import app as shared
import api_app_bootstrap as bootstrap
import api_emotion_submit as submit
import api_piece_v2 as preview_api
import middleware_active_user_touch as active_touch
import piece_v2_preview_service as real_preview_service
import piece_v2_runtime_control as runtime
import piece_v2_source_ref_http as source_api
from api_contract_registry import get_contract_entry, iter_public_api_contracts
from piece_v2_contract import PieceContractError
from test_b14a_piece_v2_runtime_control import (
    AUTH, DISABLED, FLAGS, INPUT, OWNER, PREVIEW, PREVIEW_PATH, SOURCE_PATH,
    preview_request, refs, wire,
)

_REAL_REQUEST_SNAPSHOT = real_preview_service._request_snapshot
_REAL_VISUAL_SNAPSHOT = real_preview_service._visual_mutation_snapshot
_REAL_PREVIEW_LOAD = real_preview_service._load_owned_preview_for_replay
_RUNTIME = {'ttl_seconds': 600, 'renderer_version': 'synthetic-renderer.v1'}
VISUAL_ROUTE = '/emotion/piece/preview/{preview_id}'
VISUAL_PATH = PREVIEW_PATH + '/' + INPUT


def candidate(**changes):
    settings = {'preview_requested': True, 'preview_ready': True,
                'preview_runtime': copy.deepcopy(_RUNTIME)}
    settings.update(changes)
    return shared.create_application(piece_preview_configuration=settings)


def routes(app):
    return [(method, context.path, context.original_route)
            for context in iter_route_contexts(app.router.routes)
            if isinstance(context.original_route, APIRoute)
            for method in context.original_route.methods]


def send(app, method, path, **kwargs):
    async def run():
        headers = kwargs.pop('headers', {'Authorization': AUTH,
                                        'Idempotency-Key': 'same-synthetic-key'})
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                    base_url='http://shared-test.invalid') as client:
            return await client.request(method, path, headers=headers, **kwargs)
    return asyncio.run(run())


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    attempts = []
    def denied(*args, **kwargs):
        attempts.append(True)
        raise AssertionError('This composition test must not make network connections')
    monkeypatch.setattr(socket.socket, 'connect', denied)
    yield
    assert attempts == []


@pytest.fixture
def shared_env(monkeypatch, wire):
    # Keep shared middleware installed; replace only its external auth lookup.
    async def no_active_user(_token):
        return None
    monkeypatch.setattr(active_touch, 'resolve_user_id_verified_cached', no_active_user)
    wire['submit'] = 0
    async def verified(_token):
        return OWNER
    async def execute(name, **options):
        assert name == 'emotion.submit' and options['user_id'] == OWNER
        assert options['source'] == 'emotion.submit.route'
        wire['submit'] += 1
        return SimpleNamespace(result=SimpleNamespace(data={
            'inserted': {'id': INPUT}, 'created_at': '2026-10-10T00:00:00+00:00'}))
    monkeypatch.setattr(submit, '_resolve_user_id_from_token', verified)
    monkeypatch.setattr(submit, 'execute_home_command', execute)
    monkeypatch.setattr(bootstrap, '_resolve_user_id_from_token', verified)
    monkeypatch.setattr(sys.modules['piece_v2_preview_service'],
                        '_request_snapshot', _REAL_REQUEST_SNAPSHOT)
    monkeypatch.setattr(sys.modules['piece_v2_preview_service'],
                        '_visual_mutation_snapshot', _REAL_VISUAL_SNAPSHOT, raising=False)
    monkeypatch.setattr(sys.modules['piece_v2_preview_service'],
                        '_load_owned_preview_for_replay', _REAL_PREVIEW_LOAD, raising=False)
    return wire


def test_candidate_reuses_factory_without_changing_default_routes_or_registry(shared_env):
    default_routes = [(m, p, r.endpoint) for m, p, r in routes(shared.app)]
    registry = iter_public_api_contracts()
    app = candidate()
    counts = Counter((m, p) for m, p, _ in routes(app))
    for key in [('POST', '/emotion/submit'), ('GET', '/app/bootstrap'),
                ('GET', '/app/startup'), ('GET', '/emotion/piece/source-ref/{saved_input_id}'),
                ('POST', PREVIEW_PATH), ('PATCH', VISUAL_ROUTE)]:
        assert counts[key] == 1
    assert next(r.endpoint for m, p, r in routes(app) if (m, p) == ('POST', PREVIEW_PATH)) is preview_api.create_preview
    assert next(r.endpoint for m, p, r in routes(app) if (m, p) == ('PATCH', VISUAL_ROUTE)) is preview_api.mutate_preview_visual
    assert next(r.endpoint for m, p, r in routes(app) if 'source-ref/' in p) is source_api.read_original_source_ref
    # Every shared route except the incompatible old preview alias is retained.
    before = Counter((m, p) for m, p, _ in routes(shared.app))
    expected = before.copy()
    del expected[('POST', '/emotion/reflection/preview')]
    expected[('GET', '/emotion/piece/source-ref/{saved_input_id}')] = 1
    expected[('PATCH', VISUAL_ROUTE)] = 1
    assert counts == expected
    assert [(m, p, r.endpoint) for m, p, r in routes(shared.app)] == default_routes
    assert iter_public_api_contracts() is registry
    assert app.router.on_shutdown == shared.app.router.on_shutdown
    assert [m.cls for m in app.user_middleware] == [m.cls for m in shared.app.user_middleware]
    assert not any(runtime.piece_feature_flags_for_app(shared.app).values())


def test_same_api_base_serves_submit_bootstrap_source_then_explicit_preview(shared_env):
    app = candidate()
    saved = send(app, 'POST', '/emotion/submit', json={'emotions': ['Calm']})
    assert saved.status_code == 200 and saved.json()['id'] == INPUT
    assert saved.headers['x-cocolon-contract-id'] == 'emotion.submit.v1'
    flags = send(app, 'GET', '/app/bootstrap')
    assert flags.status_code == 200
    assert flags.headers['x-cocolon-contract-id'] == 'app.bootstrap.v1'
    assert {k: flags.json()['feature_flags'][k] for k in FLAGS} == {k: k == PREVIEW for k in FLAGS}
    reference = send(app, 'GET', '/emotion/piece/source-ref/' + saved.json()['id'])
    assert reference.status_code == 200 and reference.json() == refs()
    assert reference.headers['x-cocolon-contract-id'] == 'emotion.piece.source_ref.v2'
    assert shared_env['source'] == 1 and shared_env['service'] == shared_env['rpc'] == 0
    value = preview_request()
    value['source_ref'] = reference.json()
    result = send(app, 'POST', PREVIEW_PATH, json=value)
    assert result.status_code == 200 and result.json() == shared_env['preview']
    assert result.headers['x-cocolon-contract-id'] == 'emotion.piece.preview.v2'
    assert result.headers['cache-control'] == reference.headers['cache-control'] == 'no-store'
    assert shared_env['submit'] == shared_env['service'] == shared_env['rpc'] == 1


def test_contract_selection_is_per_app_even_when_runtime_is_switched_off(shared_env):
    app = candidate()
    for selected, version in [(shared.app, 'v1'), (app, 'v2'),
                              (shared.create_application(), 'v1')]:
        result = send(selected, 'POST', PREVIEW_PATH, headers={}, json={})
        assert result.status_code in (401, 422)
        assert result.headers['x-cocolon-contract-id'] == 'emotion.piece.preview.' + version
    app.state.piece_v2_runtime = {}
    stopped = send(app, 'POST', PREVIEW_PATH, json=preview_request())
    assert stopped.json() == DISABLED
    assert stopped.headers['x-cocolon-contract-id'] == 'emotion.piece.preview.v2'
    assert get_contract_entry(method='POST', path=PREVIEW_PATH).contract_id == 'emotion.piece.preview.v1'


def test_candidate_does_not_delegate_old_preview_alias_to_new_dto(shared_env):
    app = candidate()
    old = {'emotions': ['Calm'], 'memo': 'synthetic old input'}
    result = send(app, 'POST', '/emotion/reflection/preview', json=old)
    assert result.status_code == 404
    assert 'x-cocolon-contract-id' not in result.headers
    assert shared_env['auth'] == shared_env['source'] == shared_env['service'] == shared_env['rpc'] == 0
    assert get_contract_entry(method='POST', path='/emotion/reflection/preview') is not None
    assert get_contract_entry(method='POST', path='/emotion/reflection/preview', piece_preview=True) is None
    assert any((m, p) == ('POST', '/emotion/reflection/preview') for m, p, _ in routes(shared.app))


def test_new_handler_rejects_old_raw_input_without_legacy_fallback(shared_env):
    result = send(candidate(), 'POST', PREVIEW_PATH,
                  json={'emotions': ['Calm'], 'memo': 'synthetic old input'})
    assert result.status_code == 400 and result.json() == {'code': 'PIECE_REQUEST_INVALID'}
    assert 'synthetic old input' not in result.text
    assert shared_env['source'] == shared_env['service'] == shared_env['rpc'] == 0


@pytest.mark.parametrize('method,path', [('GET', SOURCE_PATH), ('POST', PREVIEW_PATH), ('PATCH', VISUAL_PATH)])
def test_explicit_empty_candidate_is_off_and_does_not_parse_private_body(shared_env, method, path):
    app = shared.create_application(piece_preview_configuration={})
    result = send(app, method, path, content=b'SYNTHETIC INVALID PRIVATE BODY')
    assert result.status_code == 503 and result.json() == DISABLED
    assert result.headers['cache-control'] == 'no-store'
    assert not any(runtime.piece_feature_flags_for_app(app).values())
    assert shared_env['source'] == shared_env['service'] == shared_env['rpc'] == 0


@pytest.mark.parametrize('method,path', [('GET', SOURCE_PATH), ('POST', PREVIEW_PATH), ('PATCH', VISUAL_PATH)])
def test_shared_candidate_preserves_auth_before_feature_checks(shared_env, method, path):
    result = send(candidate(preview_ready=False), method, path, headers={}, json={})
    assert result.status_code == 401 and result.json() == {'code': 'PIECE_AUTH_REQUIRED'}
    assert result.headers['www-authenticate'] == 'Bearer'
    assert shared_env['source'] == shared_env['service'] == shared_env['rpc'] == 0


@pytest.mark.parametrize('runtime_value', [None, {},
    {'ttl_seconds': 0, 'renderer_version': 'v1'},
    {'ttl_seconds': 600, 'renderer_version': 'bad/name'}])
def test_bad_enabled_configuration_stops_before_shared_route_registration(shared_env, monkeypatch, runtime_value):
    def no_registration(_app):
        raise AssertionError('Invalid candidate must fail before registering shared routes')
    monkeypatch.setattr(shared, 'register_emotion_submit_routes', no_registration)
    with pytest.raises(PieceContractError) as exc:
        candidate(preview_runtime=runtime_value)
    assert exc.value.code == 'PIECE_TEMPORARILY_UNAVAILABLE'
    assert shared_env['source'] == shared_env['service'] == shared_env['rpc'] == 0


def test_candidate_configuration_and_flags_do_not_leak_between_apps(shared_env):
    first = candidate()
    second = shared.create_application(piece_preview_configuration={})
    first.state.piece_v2_runtime['ready'][PREVIEW] = False
    first.state.piece_preview_runtime['ttl_seconds'] = 1
    assert not any(runtime.piece_feature_flags_for_app(second).values())
    assert not hasattr(second.state, 'piece_preview_runtime')
    third = candidate()
    assert runtime.piece_feature_flags_for_app(third)[PREVIEW] is True
    assert third.state.piece_preview_runtime == _RUNTIME
    assert not hasattr(shared.app.state, 'piece_preview_runtime')


def test_candidate_registry_matches_actual_routes_without_duplicate_ids(shared_env):
    app = candidate()
    keys = Counter((m, p) for m, p, _ in routes(app))
    entries = iter_public_api_contracts(piece_preview=True)
    assert len(entries) == len({e.contract_id for e in entries})
    assert len(entries) == len({(e.method, e.path) for e in entries})
    assert all(keys[(e.method, e.path)] == 1 for e in entries)


def test_shared_local_endpoints_remain_directly_registered(shared_env):
    for app in (shared.app, candidate()):
        assert send(app, 'GET', '/healthz', headers={}).status_code == 200
        assert any(getattr(r, 'path', None) == '/mymodel/infer' for r in app.router.routes)
        assert app.router.on_shutdown == [shared._close_shared_supabase_client]


def test_visual_contract_is_selected_only_by_explicit_candidate(shared_env):
    for app in (shared.app, shared.create_application()):
        result = send(app, 'PATCH', VISUAL_PATH, headers={})
        assert result.status_code == 404
        assert 'x-cocolon-contract-id' not in result.headers
    assert get_contract_entry(method='PATCH', path=VISUAL_ROUTE) is None
    entry = get_contract_entry(method='PATCH', path=VISUAL_ROUTE, piece_preview=True)
    assert entry.contract_id == 'emotion.piece.preview.visual.v2'
    app = candidate(preview_ready=False)
    for headers, status, code in [({}, 401, 'PIECE_AUTH_REQUIRED'),
            ({'Authorization': AUTH}, 503, 'PIECE_FEATURE_DISABLED')]:
        result = send(app, 'PATCH', VISUAL_PATH, headers=headers,
                      content=b'SYNTHETIC INVALID PRIVATE BODY')
        assert result.status_code == status and result.json() == {'code': code}
        assert result.headers['x-cocolon-contract-id'] == entry.contract_id
        assert result.headers['cache-control'] == 'no-store'
    assert shared_env['quota_calls'] == shared_env['source'] == shared_env['service'] == shared_env['rpc'] == 0
