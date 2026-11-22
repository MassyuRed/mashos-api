"""Public ASGI responses must not disclose a profile after visibility failure."""
import asyncio
from types import SimpleNamespace

import httpx
import pytest
from fastapi import FastAPI

import api_public_profile as api


def read_profile(monkeypatch, visibility_status, visibility):
    actual_client = httpx.AsyncClient
    reads = []
    def upstream(request):
        reads.append(request.url.path)
        if request.url.path.endswith('/profiles'):
            return httpx.Response(200, json=[dict(id='synthetic-owner', display_name='PRIVATE_NAME',
                friend_code='synthetic-share', myprofile_code='PRIVATE_CONNECT')])
        assert request.url.path.endswith('/account_visibility_settings')
        return httpx.Response(visibility_status, json=visibility)
    monkeypatch.setattr(api, 'SUPABASE_URL', 'https://supabase.invalid')
    monkeypatch.setattr(api, 'SUPABASE_SERVICE_ROLE_KEY', 'synthetic-only')
    monkeypatch.setattr(api, 'httpx', SimpleNamespace(AsyncClient=lambda **kw:
        actual_client(transport=httpx.MockTransport(upstream), **kw)))
    app = FastAPI()
    api.register_public_profile_routes(app)
    async def run():
        async with actual_client(transport=httpx.ASGITransport(app=app), base_url='https://test.invalid') as client:
            return await client.get('/public/profile/by-share-code', params={'code': 'synthetic-share'})
    return asyncio.run(run()), reads


@pytest.mark.parametrize('status', [300, 401, 403, 404, 429, 500, 503])
def test_failed_visibility_lookup_does_not_return_public_defaults(monkeypatch, status):
    response, reads = read_profile(monkeypatch, status, {'message': 'PRIVATE_UPSTREAM'})
    assert response.status_code == 502
    assert 'PRIVATE_' not in response.text
    assert len(reads) == 2


@pytest.mark.parametrize('settings,expected', [
    ([], {'display_name': 'PRIVATE_NAME', 'is_private_account': False}),
    ([{'is_private_account': True, 'is_friend_code_public': True}],
     {'display_name': None, 'connect_code': None, 'is_private_account': True}),
])
def test_successful_missing_or_private_settings_preserve_existing_policy(monkeypatch, settings, expected):
    response, _ = read_profile(monkeypatch, 200, settings)
    assert response.status_code == 200
    for key, value in expected.items():
        assert response.json()[key] == value


def test_disabled_public_share_code_remains_not_found(monkeypatch):
    response, _ = read_profile(monkeypatch, 200, [{'is_friend_code_public': False}])
    assert response.status_code == 404
    assert 'PRIVATE_' not in response.text
