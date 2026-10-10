"""B14-A resolver/preview integration. Auth, source/service IO are doubles.

Real FastAPI/Starlette routes and closed HTTP replies are exercised. This is
not DB atomicity, real CMEE generation, live readiness, or device evidence.
"""
import asyncio
import copy
import importlib
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import httpx
import pytest
from fastapi import FastAPI, HTTPException

import api_piece_v2 as api
import piece_v2_source_ref_http as source_api
from piece_v2_contract import PieceContractError

FLAGS = tuple('piece_v2_' + name + '_enabled' for name in (
    'preview', 'save', 'owner_read', 'public_write', 'public_read',
    'visibility_toggle', 'export', 'delete'))
PREVIEW = FLAGS[0]
OWNER = '10000000-0000-4000-8000-000000000001'
INPUT = '20000000-0000-4000-8000-000000000002'
AUTH = 'Bearer synthetic-session'
SOURCE_PATH = '/emotion/piece/source-ref/' + INPUT
PREVIEW_PATH = '/emotion/piece/preview'
DISABLED = {'code': 'PIECE_FEATURE_DISABLED'}


def control():
    assert importlib.util.find_spec('piece_v2_runtime_control') is not None, 'B14-A resolver owner is not implemented'
    return importlib.import_module('piece_v2_runtime_control')


def config(*names):
    return {'requested': {name: True for name in names},
            'ready': {name: True for name in names}}


def refs():
    return {'source_input_id': INPUT, 'source_input_version': 'emlis.current_input_bundle.v1',
            'source_input_bundle_commitment': 'sha256:' + 'a' * 64,
            'emlis_observation_stage': 'normal_observation',
            'emlis_observation_result_identity': 'synthetic-observation',
            'question_need_decision_identity': None, 'supplemental_answer_identity': None}


def preview_request():
    return {'source_ref': refs(), 'requested_format': None,
            'visual_selection': {'theme_id': None, 'aspect_ratio': None, 'branding_mode': None}}


@pytest.mark.parametrize('value', [None, {}, True, 'true', [], {'requested': {}},
                                  {'ready': {}}, {'requested': {}, 'ready': {}, 'extra': True}])
def test_missing_or_malformed_config_is_exact_eight_false(value):
    assert control().resolve_piece_feature_flags(value) == dict.fromkeys(FLAGS, False)


@pytest.mark.parametrize('side', ['requested', 'ready'])
@pytest.mark.parametrize('value', [None, False, 1, 'true', [], {}])
def test_no_truthy_value_can_enable_a_feature(side, value):
    state = config(*FLAGS)
    state[side][PREVIEW] = value
    flags = control().resolve_piece_feature_flags(state)
    assert flags[PREVIEW] is False and flags[FLAGS[1]] is False and flags[FLAGS[3]] is False
    assert all(type(v) is bool for v in flags.values())


def test_ready_is_not_inferred_from_requested_or_ttl():
    state = config(PREVIEW)
    state['ready'] = {}
    assert not any(control().resolve_piece_feature_flags(state).values())
    state['ready'] = {'ttl_seconds': 600, 'renderer_version': 'synthetic-renderer.v1'}
    assert not any(control().resolve_piece_feature_flags(state).values())


@pytest.mark.parametrize('dependency,disabled', [
    ('preview', ['preview', 'save', 'public_write']),
    ('save', ['save', 'public_write']),
    ('owner_read', ['owner_read', 'visibility_toggle', 'export', 'delete']),
    ('public_read', ['public_read', 'public_write', 'visibility_toggle']),
])
def test_pce7_dependencies_do_not_disable_unrelated_owner_recovery(dependency, disabled):
    state = config(*FLAGS)
    state['requested']['piece_v2_' + dependency + '_enabled'] = False
    expected = {name: name.removeprefix('piece_v2_').removesuffix('_enabled') not in disabled for name in FLAGS}
    assert control().resolve_piece_feature_flags(state) == expected


def test_exact_flags_full_state_and_copied_projection():
    state = config(*FLAGS)
    state['requested']['piece_v2_future_enabled'] = True
    state['ready']['piece_v2_future_enabled'] = True
    before = copy.deepcopy(state)
    result = control().resolve_piece_feature_flags(state)
    assert result == dict.fromkeys(FLAGS, True) and state == before
    result[PREVIEW] = False
    assert control().resolve_piece_feature_flags(state)[PREVIEW] is True


def test_application_state_is_not_global_or_client_owned():
    one, two = FastAPI(), FastAPI()
    one.state.piece_v2_runtime = config(PREVIEW)
    assert control().piece_feature_flags_for_app(one)[PREVIEW] is True
    assert control().piece_feature_flags_for_app(two) == dict.fromkeys(FLAGS, False)
    with pytest.raises(PieceContractError) as exc:
        control().require_piece_feature_enabled(one, 'piece_v2_future_enabled')
    assert exc.value.code == 'PIECE_FEATURE_DISABLED'


@pytest.fixture
def wire(monkeypatch):
    state = {'auth': 0, 'source': 0, 'service': 0, 'rpc': 0,
             'source_error': None, 'service_error': None,
             'before_source_return': None, 'before_rpc': None, 'after_rpc': None,
             'verified': OWNER, 'preview': {'piece_text': 'Synthetic gate-only preview.'}}
    import supabase_client
    from datetime import datetime, timezone
    from piece_v2_quota import project_piece_quota, project_piece_plan_capabilities
    state['quota_calls'] = 0
    state['preview'].update(quota=project_piece_quota(server_tier='free', saved_count=0,
        server_now=datetime(2026, 10, 10, tzinfo=timezone.utc)),
        plan_capabilities=project_piece_plan_capabilities(server_tier='free'))
    async def quota_rpc(name, args, *, timeout):
        assert name == 'piece_read_quota_v2' and args == {'p_owner_user_id': OWNER}
        assert timeout == 8.0
        state['quota_calls'] += 1
        return httpx.Response(200, json={'subscription_tier': 'free', 'saved_count': 0,
            'server_now': '2026-10-10T00:00:00+00:00'})
    monkeypatch.setattr(supabase_client, 'sb_post_rpc', quota_rpc)
    app = FastAPI()
    app.state.piece_preview_runtime = {'ttl_seconds': 600, 'renderer_version': 'synthetic-renderer.v1'}

    async def verify(_authorization):
        state['auth'] += 1
        if isinstance(state['verified'], BaseException):
            raise state['verified']
        return state['verified']

    class Source:
        async def resolve_original_source_ref(self, authorization, saved_input_id):
            assert authorization == AUTH and saved_input_id == INPUT
            state['source'] += 1
            if state['source_error']:
                raise state['source_error']
            if state['before_source_return']:
                state['before_source_return']()
            return refs()

    async def rpc(name, args):
        assert name == 'piece_issue_preview_v2' and args == {'synthetic': True}
        state['rpc'] += 1
        if state['after_rpc']:
            state['after_rpc']()
        return copy.deepcopy(state['preview'])

    class Preview:
        async def issue_original(self, authorization, value, **options):
            assert authorization == AUTH and value == preview_request()
            assert options['idempotency_key'] == 'same-synthetic-key'
            assert options['ttl_seconds'] == 600 and options['renderer_version'] == 'synthetic-renderer.v1'
            assert options['expected_subscription_tier'] == 'free'
            state['service'] += 1
            if state['service_error']:
                raise state['service_error']
            if state['before_rpc']:
                state['before_rpc']()
            try:
                return await options['rpc']('piece_issue_preview_v2', {'synthetic': True})
            except PieceContractError:
                # The existing B5 service closes unknown codes. The HTTP owner
                # must retain its own observed stop even through this mapping.
                if state.get('reenable_on_error'):
                    app.state.piece_v2_runtime = config(PREVIEW)
                raise PieceContractError('PIECE_TEMPORARILY_UNAVAILABLE') from None

    adapter = ModuleType('piece_v2_source_adapter')
    adapter.PieceSavedSourceAdapter = Source
    service = ModuleType('piece_v2_preview_service')
    service.PiecePreviewService = Preview
    service._request_snapshot = lambda value: copy.deepcopy(value)
    monkeypatch.setitem(sys.modules, 'piece_v2_source_adapter', adapter)
    monkeypatch.setitem(sys.modules, 'piece_v2_preview_service', service)
    monkeypatch.setattr(api, '_verify_bearer', verify)
    monkeypatch.setattr(api, '_preview_rpc', rpc)
    # Gating tests deliberately isolate artifact projection; the pre-existing
    # native B5 suite owns real store/CMEE/hash projection, unchanged below.
    monkeypatch.setattr(api, '_preview_public_response', lambda result: copy.deepcopy(result))
    app.include_router(source_api.source_ref_router)
    app.include_router(api.router)

    async def send(method, path, **kwargs):
        headers = kwargs.pop('headers', {'Authorization': AUTH, 'Idempotency-Key': 'same-synthetic-key'})
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
            return await client.request(method, path, headers=headers, **kwargs)

    state.update(app=app, send=lambda *a, **kw: asyncio.run(send(*a, **kw)))
    return state


@pytest.mark.parametrize('path,method', [(SOURCE_PATH, 'GET'), (PREVIEW_PATH, 'POST')])
def test_default_off_denies_before_source_service_and_body_parse(wire, path, method):
    response = wire['send'](method, path, content=b'PRIVATE INVALID JSON')
    assert response.status_code == 503 and response.json() == DISABLED
    assert response.headers['cache-control'] == 'no-store'
    assert wire['auth'] == 1 and wire['source'] == wire['service'] == wire['rpc'] == 0


@pytest.mark.parametrize('path,method', [(SOURCE_PATH, 'GET'), (PREVIEW_PATH, 'POST')])
def test_authentication_precedes_disabled_feature(wire, path, method):
    response = wire['send'](method, path, headers={})
    assert response.status_code == 401 and response.json() == {'code': 'PIECE_AUTH_REQUIRED'}
    assert response.headers['www-authenticate'] == 'Bearer'
    assert wire['source'] == wire['service'] == wire['rpc'] == 0


@pytest.mark.parametrize('path,method', [(SOURCE_PATH, 'GET'), (PREVIEW_PATH, 'POST')])
def test_client_flag_header_cannot_enable_missing_server_state(wire, path, method):
    response = wire['send'](method, path, headers={'Authorization': AUTH,
        'Idempotency-Key': 'same-synthetic-key', 'piece_v2_preview_enabled': 'true'},
        params={'piece_v2_preview_enabled': 'true'})
    assert response.status_code == 503 and response.json() == DISABLED
    assert wire['source'] == wire['service'] == wire['rpc'] == 0


def test_enabled_source_uses_original_seven_field_response(wire):
    wire['app'].state.piece_v2_runtime = config(PREVIEW)
    response = wire['send']('GET', SOURCE_PATH)
    assert response.status_code == 200 and response.json() == refs()
    assert wire['source'] == 1 and wire['service'] == wire['rpc'] == 0


def test_source_disabled_during_read_never_returns_stale_references(wire):
    wire['app'].state.piece_v2_runtime = config(PREVIEW)
    wire['before_source_return'] = lambda: setattr(wire['app'].state, 'piece_v2_runtime', {})
    response = wire['send']('GET', SOURCE_PATH)
    assert response.status_code == 503 and response.json() == DISABLED and wire['source'] == 1


def test_enabled_preview_keeps_original_request_key_and_response(wire):
    wire['app'].state.piece_v2_runtime = config(PREVIEW)
    response = wire['send']('POST', PREVIEW_PATH, json=preview_request())
    assert response.status_code == 200 and response.json() == wire['preview']
    assert wire['service'] == wire['rpc'] == 1


@pytest.mark.parametrize('reenable', [False, True])
def test_stop_after_generation_before_rpc_does_not_write_or_lose_stop_code(wire, reenable):
    wire['app'].state.piece_v2_runtime = config(PREVIEW)
    wire['before_rpc'] = lambda: setattr(wire['app'].state, 'piece_v2_runtime', {})
    wire['reenable_on_error'] = reenable
    response = wire['send']('POST', PREVIEW_PATH, json=preview_request())
    assert response.status_code == 503 and response.json() == DISABLED
    assert wire['service'] == 1 and wire['rpc'] == 0


def test_stop_while_rpc_in_flight_conceals_reply_without_claiming_rollback(wire):
    wire['app'].state.piece_v2_runtime = config(PREVIEW)
    wire['after_rpc'] = lambda: setattr(wire['app'].state, 'piece_v2_runtime', {})
    response = wire['send']('POST', PREVIEW_PATH, json=preview_request())
    assert response.status_code == 503 and response.json() == DISABLED
    assert wire['rpc'] == 1  # Already-dispatched effect is not cancelled/undone.


@pytest.mark.parametrize('method,path,field', [('GET', SOURCE_PATH, 'source_error'),
                                              ('POST', PREVIEW_PATH, 'service_error')])
def test_task_cancellation_propagates_without_retry(wire, method, path, field):
    wire['app'].state.piece_v2_runtime = config(PREVIEW)
    wire[field] = asyncio.CancelledError()
    with pytest.raises(asyncio.CancelledError):
        wire['send'](method, path, **({'json': preview_request()} if method == 'POST' else {}))
    assert wire['rpc'] == 0


def test_enabled_preview_still_requires_existing_ttl_and_renderer(wire):
    wire['app'].state.piece_v2_runtime = config(PREVIEW)
    del wire['app'].state.piece_preview_runtime
    response = wire['send']('POST', PREVIEW_PATH, json=preview_request())
    assert response.status_code == 503 and response.json() == {'code': 'PIECE_TEMPORARILY_UNAVAILABLE'}
    assert wire['service'] == wire['rpc'] == 0


@pytest.fixture
def bootstrap(monkeypatch, wire):
    submit = ModuleType('api_emotion_submit')
    submit._extract_bearer_token = lambda value: 'synthetic' if value == AUTH else None
    async def user(_token):
        return OWNER
    submit._resolve_user_id_from_token = user
    compat = ModuleType('client_compat')
    compat.extract_client_meta = lambda headers: {'app_version': headers.get('X-App-Version')}
    threads = ModuleType('emlis_thread_config')
    threads.read_enabled = lambda: False
    startup = ModuleType('startup_snapshot_store')
    async def snapshot(*_args, **_kwargs):
        if wire.get('startup_failure'):
            raise RuntimeError('synthetic startup failure')
        return {'synthetic': True}
    startup.get_startup_snapshot = snapshot
    for module in [submit, compat, threads, startup]:
        monkeypatch.setitem(sys.modules, module.__name__, module)
    source = Path(api.__file__).with_name('api_app_bootstrap.py')
    spec = importlib.util.spec_from_file_location('_piece_b14_bootstrap', source)
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)
    module.register_app_bootstrap_routes(wire['app'])
    return module


@pytest.mark.parametrize('path', ['/app/bootstrap', '/app/startup'])
def test_both_bootstrap_routes_use_same_application_flags(wire, bootstrap, path):
    wire['app'].state.piece_v2_runtime = config(PREVIEW)
    first = wire['send']('GET', path)
    assert first.status_code == 200 and first.json()['feature_flags'][PREVIEW] is True
    wire['app'].state.piece_v2_runtime = {}
    second = wire['send']('GET', path)
    assert second.status_code == 200
    assert {k: second.json()['feature_flags'][k] for k in FLAGS} == dict.fromkeys(FLAGS, False)


def test_bootstrap_without_application_has_no_piece_authority(bootstrap):
    value = bootstrap._bootstrap_payload(client_meta={'app_version': 'test'})
    assert {k: value['feature_flags'][k] for k in FLAGS} == dict.fromkeys(FLAGS, False)
    assert value['client_meta'] == {'app_version': 'test'}
    assert value['feature_flags']['today_question_enabled'] is True


def test_bootstrap_projection_keeps_other_metadata_and_hides_requested_ready(wire, bootstrap, monkeypatch):
    monkeypatch.setenv('APP_MINIMUM_SUPPORTED_VERSION', ' 1.2.3 ')
    monkeypatch.setenv('COCOLON_SUBSCRIPTION_SALES_ENABLED', 'false')
    wire['app'].state.piece_v2_runtime = config(*FLAGS)
    response = wire['send']('GET', '/app/bootstrap')
    value = response.json()
    assert value['minimum_supported_version'] == '1.2.3'
    assert value['feature_flags']['subscription_sales_enabled'] is False
    assert value['feature_flags']['account_delete_enabled'] is True
    assert set(value) == {'minimum_supported_version', 'recommended_version',
                          'maintenance_message', 'feature_flags', 'client_meta'}
    assert 'requested' not in response.text and 'ready' not in response.text


def test_startup_fallback_still_carries_current_piece_flags(wire, bootstrap):
    wire['startup_failure'] = True
    wire['app'].state.piece_v2_runtime = config(PREVIEW)
    response = wire['send']('GET', '/app/startup')
    assert response.status_code == 200 and response.json()['feature_flags'][PREVIEW] is True
    assert response.json()['startup']['errors'] == {'startup': 'snapshot_unavailable'}


@pytest.mark.parametrize('path,method', [(SOURCE_PATH, 'GET'), (PREVIEW_PATH, 'POST')])
def test_stop_while_request_body_is_received_prevents_service_entry(wire, monkeypatch, path, method):
    from starlette.requests import Request
    original_body = Request.body
    wire['app'].state.piece_v2_runtime = config(PREVIEW)

    async def body_then_stop(request):
        value = await original_body(request)
        request.app.state.piece_v2_runtime = {}
        return value

    monkeypatch.setattr(Request, 'body', body_then_stop)
    kwargs = {'json': preview_request()} if method == 'POST' else {}
    response = wire['send'](method, path, **kwargs)
    assert response.status_code == 503 and response.json() == DISABLED
    assert wire['source'] == wire['service'] == wire['rpc'] == 0


@pytest.mark.parametrize('failure', [False, True])
def test_preview_stop_during_quota_read_is_latched_before_service(wire, monkeypatch, failure):
    import supabase_client
    app = wire['app']; app.state.piece_v2_runtime = config(PREVIEW)
    async def stopped(*args, **kwargs):
        wire['quota_calls'] += 1
        app.state.piece_v2_runtime = {}
        if failure:
            raise TimeoutError('synthetic private quota error')
        return httpx.Response(200, json={'subscription_tier': 'free', 'saved_count': 0,
            'server_now': '2026-10-10T00:00:00+00:00'})
    monkeypatch.setattr(supabase_client, 'sb_post_rpc', stopped)
    response = wire['send']('POST', PREVIEW_PATH, json=preview_request())
    assert response.status_code == 503 and response.json() == DISABLED
    assert wire['quota_calls'] == 1 and wire['service'] == wire['rpc'] == 0
