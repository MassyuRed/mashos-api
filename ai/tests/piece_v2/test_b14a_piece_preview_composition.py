"""Preview-only development composition, not production activation or DB E2E.

Reuse the existing B14 HTTP fixtures unchanged: real ASGI handlers/resolver,
synthetic bearer/source/preview service/RPC and preview projection. Bootstrap
is the full existing module with its external dependencies replaced by fixtures.
"""
import asyncio
import builtins
import copy
import sys

import httpx
import pytest
from fastapi import HTTPException
from starlette.requests import Request

import api_piece_v2 as api
import piece_v2_runtime_control as runtime
import piece_v2_source_ref_http as source_api
from piece_v2_contract import PieceContractError
from test_b14a_piece_v2_runtime_control import (
    AUTH, DISABLED, FLAGS, INPUT, PREVIEW, PREVIEW_PATH, SOURCE_PATH,
    bootstrap, preview_request, refs, wire,
)

RUNTIME = {'ttl_seconds': 600, 'renderer_version': 'synthetic-renderer.v1'}


@pytest.fixture
def composition_env(monkeypatch, bootstrap, wire):
    # Reuse the actual bootstrap source already loaded by the unchanged fixture.
    monkeypatch.setitem(sys.modules, 'api_app_bootstrap', bootstrap)
    return wire


def make(**kwargs):
    factory = getattr(runtime, 'create_piece_preview_application', None)
    assert callable(factory), 'B14_PREVIEW_COMPOSITION_ABSENT'
    return factory(**kwargs)


def enabled(**kwargs):
    return make(preview_requested=True, preview_ready=True,
                preview_runtime=kwargs.pop('preview_runtime', copy.deepcopy(RUNTIME)), **kwargs)


def send(app, method, path, **kwargs):
    async def run():
        headers = kwargs.pop('headers', {'Authorization': AUTH,
                                        'Idempotency-Key': 'same-synthetic-key'})
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                    base_url='http://test') as client:
            return await client.request(method, path, headers=headers, **kwargs)
    return asyncio.run(run())


def test_default_composition_has_only_existing_preview_and_bootstrap_handlers(composition_env):
    before = tuple(api.router.routes)
    app = make()
    assert {(r.path, tuple(sorted(r.methods))) for r in app.routes} == {
        ('/app/bootstrap', ('GET',)), ('/app/startup', ('GET',)),
        ('/emotion/piece/preview', ('POST',)),
        ('/emotion/piece/source-ref/{saved_input_id}', ('GET',)),
    }
    assert next(r.endpoint for r in app.routes if r.path == PREVIEW_PATH) is api.create_preview
    assert next(r.endpoint for r in app.routes if 'source-ref/' in r.path) is source_api.read_original_source_ref
    assert tuple(api.router.routes) == before
    assert runtime.piece_feature_flags_for_app(app) == dict.fromkeys(FLAGS, False)
    assert not hasattr(app.state, 'piece_preview_runtime')
    assert all(composition_env[key] == 0 for key in ('auth', 'source', 'service', 'rpc'))


@pytest.mark.parametrize('path,method', [(SOURCE_PATH, 'GET'), (PREVIEW_PATH, 'POST')])
def test_composed_default_off_is_closed_without_parsing_private_body(composition_env, path, method):
    app = make()
    response = send(app, method, path, content=b'SYNTHETIC PRIVATE INVALID JSON')
    assert response.status_code == 503 and response.json() == DISABLED
    assert response.headers['cache-control'] == 'no-store'
    assert composition_env['auth'] == 1
    assert composition_env['source'] == composition_env['service'] == composition_env['rpc'] == 0


@pytest.mark.parametrize('path,method', [(SOURCE_PATH, 'GET'), (PREVIEW_PATH, 'POST')])
def test_composed_auth_precedes_flags(composition_env, path, method):
    response = send(make(), method, path, headers={})
    assert response.status_code == 401 and response.json() == {'code': 'PIECE_AUTH_REQUIRED'}
    assert response.headers['www-authenticate'] == 'Bearer'
    assert composition_env['auth'] == composition_env['source'] == composition_env['service'] == 0


@pytest.mark.parametrize('side', ['preview_requested', 'preview_ready'])
@pytest.mark.parametrize('value', [None, False, 1, 'true', [], {}])
def test_truthy_or_missing_permission_is_not_readiness(composition_env, side, value):
    options = {'preview_requested': True, 'preview_ready': True,
               'preview_runtime': copy.deepcopy(RUNTIME), side: value}
    app = make(**options)
    assert runtime.piece_feature_flags_for_app(app) == dict.fromkeys(FLAGS, False)
    response = send(app, 'POST', PREVIEW_PATH, json=preview_request())
    assert response.status_code == 503 and response.json() == DISABLED
    assert composition_env['service'] == composition_env['rpc'] == 0


def test_settings_or_requested_alone_never_establish_readiness(composition_env):
    for options in ({'preview_runtime': RUNTIME},
                    {'preview_requested': True, 'preview_runtime': RUNTIME},
                    {'preview_ready': True, 'preview_runtime': RUNTIME}):
        app = make(**options)
        assert not any(runtime.piece_feature_flags_for_app(app).values())
    assert composition_env['auth'] == composition_env['source'] == composition_env['service'] == 0


BAD_RUNTIME = [None, {}, True, {'ttl_seconds': 600},
    {'ttl_seconds': 600, 'renderer_version': 'v1', 'extra': 'SYNTHETIC_PRIVATE'},
    *({'ttl_seconds': v, 'renderer_version': 'v1'} for v in (0, -1, True, 1.0, '600', 2147483648)),
    *({'ttl_seconds': 600, 'renderer_version': v} for v in ('', 'bad/name', 'bad\nname', 'あ', 'x' * 129, 1)),
]


@pytest.mark.parametrize('value', BAD_RUNTIME)
def test_enabled_composition_rejects_missing_or_invalid_configuration_before_io(composition_env, value):
    with pytest.raises(PieceContractError) as exc:
        enabled(preview_runtime=value)
    assert str(exc.value) == 'PIECE_TEMPORARILY_UNAVAILABLE'
    assert all(composition_env[key] == 0 for key in ('auth', 'source', 'service', 'rpc'))


@pytest.mark.parametrize('ttl,renderer', [(1, 'a'), (2147483647, 'R.v1:build-2_3'), (600, 'x' * 128)])
def test_configuration_keeps_existing_valid_boundaries_without_normalization(composition_env, ttl, renderer):
    app = enabled(preview_runtime={'ttl_seconds': ttl, 'renderer_version': renderer})
    assert api._preview_runtime(Request({'type': 'http', 'app': app})) == (ttl, renderer)


def test_configuration_is_copied_and_each_application_is_independent(composition_env):
    settings = copy.deepcopy(RUNTIME)
    first = enabled(preview_runtime=settings)
    second = make()
    settings['ttl_seconds'] = 0
    settings['renderer_version'] = 'changed'
    assert first.state.piece_preview_runtime == RUNTIME
    assert not hasattr(second.state, 'piece_preview_runtime')
    first.state.piece_v2_runtime['requested'][PREVIEW] = False
    assert not any(runtime.piece_feature_flags_for_app(first).values())
    assert not any(runtime.piece_feature_flags_for_app(second).values())
    third = enabled()
    assert runtime.piece_feature_flags_for_app(third)[PREVIEW] is True
    assert all(runtime.piece_feature_flags_for_app(third)[name] is False for name in FLAGS[1:])


@pytest.mark.parametrize('path', ['/app/bootstrap', '/app/startup'])
def test_same_composition_publishes_only_effective_flags_not_configuration(composition_env, path):
    app = enabled()
    response = send(app, 'GET', path)
    assert response.status_code == 200
    flags = response.json()['feature_flags']
    assert {name: flags[name] for name in FLAGS} == {name: name == PREVIEW for name in FLAGS}
    assert flags['today_question_enabled'] is True
    assert not any(word in response.text for word in ('requested', 'ready', 'ttl_seconds', 'renderer_version'))
    app.state.piece_v2_runtime['ready'][PREVIEW] = False
    response = send(app, 'GET', path)
    assert not any(response.json()['feature_flags'][name] for name in FLAGS)


def test_composed_get_then_explicit_post_keeps_reference_request_key_and_settings(composition_env):
    app = enabled()
    reference = send(app, 'GET', SOURCE_PATH)
    assert reference.status_code == 200 and reference.json() == refs()
    assert composition_env['source'] == 1 and composition_env['service'] == 0
    request = preview_request()
    request['source_ref'] = reference.json()
    response = send(app, 'POST', PREVIEW_PATH, json=request)
    assert response.status_code == 200 and response.json() == composition_env['preview']
    assert response.headers['cache-control'] == 'no-store'
    assert composition_env['service'] == composition_env['rpc'] == 1
    # Fixture checks the exact request, key, TTL and renderer on every call.
    again = send(app, 'POST', PREVIEW_PATH, json=request)
    assert again.json() == response.json()
    assert composition_env['service'] == composition_env['rpc'] == 2
    # This is explicit forwarding, not proof of real DB idempotency.


@pytest.mark.parametrize('method,path', [
    ('POST', '/emotion/piece/save'), ('GET', '/emotion/piece/history'),
    ('GET', '/emotion/piece/' + INPUT), ('DELETE', '/emotion/piece/' + INPUT),
    ('PATCH', '/emotion/piece/' + INPUT + '/visibility'),
    ('DELETE', '/emotion/piece/preview/' + INPUT),
    ('POST', '/emotion/piece/publish'), ('GET', '/emotion/piece/quota'),
    ('POST', '/emotion/reflection/preview'), ('GET', '/nexus'),
])
def test_unfinished_or_legacy_routes_are_not_published_by_preview_composition(composition_env, method, path):
    response = send(enabled(), method, path, content=b'SYNTHETIC PRIVATE BODY')
    assert response.status_code == 404
    assert composition_env['auth'] == composition_env['source'] == composition_env['service'] == composition_env['rpc'] == 0


def test_factory_does_not_import_or_modify_production_or_legacy_application(composition_env, monkeypatch):
    original = builtins.__import__
    forbidden = {'app', 'api_emotion_piece', 'api_piece_runtime', 'api_piece_compat', 'api_nexus'}
    def guarded(name, *args, **kwargs):
        assert name not in forbidden, 'preview composition entered a production/legacy owner'
        return original(name, *args, **kwargs)
    monkeypatch.setattr(builtins, '__import__', guarded)
    app = enabled()
    assert len(app.routes) == 4
    assert app is not composition_env['app']


def test_stop_after_source_get_prevents_the_later_preview(composition_env):
    app = enabled()
    assert send(app, 'GET', SOURCE_PATH).status_code == 200
    app.state.piece_v2_runtime['ready'][PREVIEW] = False
    response = send(app, 'POST', PREVIEW_PATH, json=preview_request())
    assert response.status_code == 503 and response.json() == DISABLED
    assert composition_env['source'] == 1 and composition_env['service'] == composition_env['rpc'] == 0


@pytest.mark.parametrize('hook,rpc_count', [('before_rpc', 0), ('after_rpc', 1)])
def test_composition_keeps_existing_stop_fences_without_inventing_rollback(composition_env, hook, rpc_count):
    app = enabled()
    composition_env[hook] = lambda: setattr(app.state, 'piece_v2_runtime', {})
    response = send(app, 'POST', PREVIEW_PATH, json=preview_request())
    assert response.status_code == 503 and response.json() == DISABLED
    assert composition_env['service'] == 1 and composition_env['rpc'] == rpc_count


def test_runtime_configuration_is_revalidated_by_post_not_only_at_construction(composition_env):
    app = enabled()
    app.state.piece_preview_runtime['ttl_seconds'] = True
    response = send(app, 'POST', PREVIEW_PATH, json=preview_request())
    assert response.status_code == 503 and response.json() == {'code': 'PIECE_TEMPORARILY_UNAVAILABLE'}
    assert composition_env['service'] == composition_env['rpc'] == 0


def test_source_eligibility_denial_and_authentication_error_are_not_configuration_success(composition_env):
    app = enabled()
    composition_env['source_error'] = PieceContractError('PIECE_SOURCE_NOT_ELIGIBLE')
    response = send(app, 'GET', SOURCE_PATH)
    assert response.status_code == 422 and response.json() == {'code': 'PIECE_SOURCE_NOT_ELIGIBLE'}
    composition_env['verified'] = HTTPException(403, 'SYNTHETIC PRIVATE DIAGNOSTIC')
    response = send(app, 'POST', PREVIEW_PATH, json=preview_request())
    assert response.status_code == 401 and response.json() == {'code': 'PIECE_AUTH_REQUIRED'}
    assert composition_env['service'] == composition_env['rpc'] == 0


def test_http_values_cannot_supply_server_readiness(composition_env):
    app = make()
    response = send(app, 'POST', PREVIEW_PATH, params={'preview_ready': 'true'},
                    headers={'Authorization': AUTH, 'piece_v2_preview_enabled': 'true'},
                    json={'ready': True, 'ttl_seconds': 600, 'renderer_version': 'v1'})
    assert response.status_code == 503 and response.json() == DISABLED
    assert composition_env['service'] == composition_env['rpc'] == 0


def test_existing_http_runtime_validation_preserves_all_rejections(composition_env):
    # The refactor must preserve the former HTTP owner's full invalid-value
    # boundary, not merely reject these values once in the new constructor.
    from test_b14a_piece_v2_runtime_control import config
    composition_env['app'].state.piece_v2_runtime = config(PREVIEW)
    for value in BAD_RUNTIME:
        composition_env['app'].state.piece_preview_runtime = copy.deepcopy(value)
        response = composition_env['send']('POST', PREVIEW_PATH, json=preview_request())
        assert response.status_code == 503, value
        assert response.json() == {'code': 'PIECE_TEMPORARILY_UNAVAILABLE'}
    assert composition_env['service'] == composition_env['rpc'] == 0
