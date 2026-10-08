"""Unregistered source-ref transport; no live Auth/DB/CMEE claim.

These tests exercise FastAPI/Starlette routing and the actual HTTP handler.
The remote bearer verifier and saved-adapter result boundary are doubles.
The adapter's semantic/retention checks belong to its separate tests.
"""
import asyncio
import copy
import sys
from types import ModuleType

import httpx
import pytest
from fastapi import FastAPI, HTTPException

import api_piece_v2
import piece_v2_source_ref_http as mod
from piece_v2_contract import PieceContractError

OWNER = '10000000-0000-4000-8000-000000000001'
INPUT = '20000000-0000-4000-8000-000000000002'
AUTH = 'Bearer synthetic-session'
PATH = '/emotion/piece/source-ref/' + INPUT


def source_ref(pre=False):
    return {
        'source_input_id': INPUT,
        'source_input_version': 'emlis.current_input_bundle.v1',
        'source_input_bundle_commitment': 'sha256:' + 'a' * 64,
        'emlis_observation_stage': 'pre_question_observation' if pre else 'normal_observation',
        'emlis_observation_result_identity': 'synthetic-observation',
        'question_need_decision_identity': 'synthetic-question' if pre else None,
        'supplemental_answer_identity': None,
    }


@pytest.fixture
def setup(monkeypatch):
    state = {'calls': [], 'result': source_ref(), 'error': None, 'verified': OWNER}
    async def verify(authorization):
        assert authorization == AUTH
        if isinstance(state['verified'], BaseException):
            raise state['verified']
        return state['verified']
    monkeypatch.setattr(api_piece_v2, '_verify_bearer', verify)
    adapter_module = ModuleType('piece_v2_source_adapter')
    class Adapter:
        async def resolve_original_source_ref(self, authorization, saved_input_id):
            state['calls'].append((authorization, saved_input_id))
            if state['error'] is not None:
                raise state['error']
            return copy.deepcopy(state['result'])
    adapter_module.PieceSavedSourceAdapter = Adapter
    monkeypatch.setitem(sys.modules, 'piece_v2_source_adapter', adapter_module)
    app = FastAPI()
    app.include_router(mod.source_ref_router)
    async def send(path=PATH, *, headers=None, content=b'', method='GET'):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
            return await client.request(method, path, headers={'Authorization': AUTH} if headers is None else headers, content=content)
    state['send'] = lambda **kw: asyncio.run(send(**kw))
    state['send_async'] = send
    return state


@pytest.mark.parametrize('pre', [False, True])
def test_exact_seven_fields_current_input_and_no_store(setup, pre):
    setup['result'] = source_ref(pre)
    response = setup['send']()
    assert response.status_code == 200
    assert response.json() == source_ref(pre)
    assert len(response.json()) == 7
    assert response.headers['cache-control'] == 'no-store'
    assert setup['calls'] == [(AUTH, INPUT)]
    assert OWNER not in response.text and 'synthetic-session' not in response.text


@pytest.mark.parametrize('headers', [{}, {'Authorization': 'Basic private'},
    {'Authorization': 'Bearer'}, [('Authorization', AUTH), ('Authorization', AUTH)]])
def test_missing_invalid_or_duplicate_auth_does_not_resolve(setup, headers):
    response = setup['send'](headers=headers)
    assert response.status_code == 401
    assert response.json() == {'code': 'PIECE_AUTH_REQUIRED'}
    assert response.headers['www-authenticate'] == 'Bearer'
    assert response.headers['cache-control'] == 'no-store'
    assert setup['calls'] == []


@pytest.mark.parametrize('verified,code,status', [
    (HTTPException(401, 'PRIVATE'), 'PIECE_AUTH_REQUIRED', 401),
    (HTTPException(503, 'PRIVATE'), 'PIECE_TEMPORARILY_UNAVAILABLE', 503),
    ('not-a-uuid', 'PIECE_AUTH_REQUIRED', 401),
    ('00000000-0000-0000-0000-000000000000', 'PIECE_AUTH_REQUIRED', 401),
    (None, 'PIECE_AUTH_REQUIRED', 401),
])
def test_shared_bearer_owner_failure_is_closed(setup, verified, code, status):
    setup['verified'] = verified
    response = setup['send']()
    assert response.status_code == status
    assert response.json() == {'code': code}
    assert setup['calls'] == []


@pytest.mark.parametrize('path,content', [
    (PATH + '?eligible=true', b''), (PATH, b'{"memo":"PRIVATE"}'),
    ('/emotion/piece/source-ref/not-a-uuid', b''),
    ('/emotion/piece/source-ref/00000000-0000-0000-0000-000000000000', b''),
    ('/emotion/piece/source-ref/20000000000040008000000000000002', b''),
])
def test_no_raw_body_query_or_invalid_source_identity(setup, path, content):
    response = setup['send'](path=path, content=content)
    assert response.status_code == 400
    assert response.json() == {'code': 'PIECE_REQUEST_INVALID'}
    assert setup['calls'] == []


@pytest.mark.parametrize('field,value', [
    ('source_input_id', OWNER), ('source_input_version', 'future'),
    ('source_input_bundle_commitment', 'PRIVATE'),
    ('emlis_observation_result_identity', ''),
    ('emlis_observation_result_identity', '\ud800'),
    ('emlis_observation_stage', 'refined_observation'),
    ('supplemental_answer_identity', 'answer'),
    ('question_need_decision_identity', 'unexpected-question'),
    ('memo', 'PRIVATE RAW INPUT'), ('owner_user_id', OWNER),
])
def test_malformed_or_private_result_is_not_partially_projected(setup, field, value):
    setup['result'][field] = value
    response = setup['send']()
    assert response.status_code == 503
    assert response.json() == {'code': 'PIECE_TEMPORARILY_UNAVAILABLE'}


@pytest.mark.parametrize('code,status', list(mod._SOURCE_REF_STATUS.items()))
def test_closed_adapter_failures_keep_code_and_status(setup, code, status):
    setup['error'] = PieceContractError(code, 'PRIVATE INPUT AND TOKEN')
    response = setup['send']()
    assert response.status_code == status
    assert response.json() == {'code': code}
    assert response.headers['cache-control'] == 'no-store'


@pytest.mark.parametrize('error', [RuntimeError('PRIVATE'), PieceContractError('PRIVATE_INTERNAL')])
def test_unexpected_failure_never_echoes_backend_detail(setup, error):
    setup['error'] = error
    response = setup['send']()
    assert response.status_code == 503
    assert response.json() == {'code': 'PIECE_TEMPORARILY_UNAVAILABLE'}


def test_cancellation_does_not_become_a_success_or_retry(setup):
    setup['error'] = asyncio.CancelledError()
    with pytest.raises(asyncio.CancelledError):
        setup['send']()
    assert len(setup['calls']) == 1


def test_candidate_is_not_added_to_existing_router():
    assert mod.source_ref_router is not api_piece_v2.router
    assert not any(r.path == '/emotion/piece/source-ref/{saved_input_id}' for r in api_piece_v2.router.routes)
