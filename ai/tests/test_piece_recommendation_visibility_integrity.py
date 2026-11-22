"""Recommendation choices remain authoritative when the settings read fails."""
import asyncio

import pytest

import api_nexus as nexus
import api_piece_runtime as runtime


class Response:
    def __init__(self, rows=None, status=200, invalid_json=False):
        self.rows, self.status_code, self.invalid_json = rows, status, invalid_json

    def json(self):
        if self.invalid_json:
            raise ValueError('invalid transport JSON')
        return self.rows


def test_success_preserves_order_and_missing_row_public_default(monkeypatch):
    async def fetch(*args, **kwargs):
        return Response([{'user_id': 'disabled', 'is_recommendation_enabled': False},
                         {'user_id': 'enabled', 'is_recommendation_enabled': True}])
    monkeypatch.setattr(runtime, '_sb_get', fetch)
    assert asyncio.run(runtime._filter_recommendation_enabled(['missing', 'disabled', 'enabled'])) == ['missing', 'enabled']


@pytest.mark.parametrize('response', [
    Response([], status=500), Response([], status=403), Response(invalid_json=True),
    Response(None), Response({}), Response([None]), Response([{'user_id': 'disabled'}]),
    Response([{'user_id': 'disabled', 'is_recommendation_enabled': 'false'}]),
    Response([{'user_id': 'disabled', 'is_recommendation_enabled': 0}]),
    Response([{'user_id': 'disabled', 'is_recommendation_enabled': None}]),
    Response([{'user_id': 'outside', 'is_recommendation_enabled': False}]),
    Response([{'user_id': 'disabled', 'is_recommendation_enabled': True},
              {'user_id': 'disabled', 'is_recommendation_enabled': False}]),
])
def test_unverified_choices_are_never_recommended(monkeypatch, response):
    async def fetch(*args, **kwargs):
        return response
    monkeypatch.setattr(runtime, '_sb_get', fetch)
    assert asyncio.run(runtime._filter_recommendation_enabled(['disabled'])) == []


def test_transport_exception_is_not_a_public_default(monkeypatch):
    async def fetch(*args, **kwargs):
        raise ConnectionError('offline fake transport')
    monkeypatch.setattr(runtime, '_sb_get', fetch)
    assert asyncio.run(runtime._filter_recommendation_enabled(['disabled'])) == []


def test_failed_chunk_does_not_discard_verified_other_chunk(monkeypatch):
    ids = [f'user-{i}' for i in range(201)]
    calls = []
    async def fetch(*args, **kwargs):
        calls.append(kwargs['params']['user_id'])
        return Response([], status=500) if len(calls) == 1 else Response([])
    monkeypatch.setattr(runtime, '_sb_get', fetch)
    assert asyncio.run(runtime._filter_recommendation_enabled(ids)) == ['user-200']
    assert len(calls) == 2


def test_nexus_active_recommendation_path_never_loads_unverified_profiles(monkeypatch):
    requested_profiles = []
    async def active(**kwargs): return {'viewer', 'disabled'}
    async def followed(**kwargs): return set()
    async def fetch(*args, **kwargs): return Response([], status=500)
    async def profiles(ids):
        requested_profiles.extend(ids)
        return {'disabled': {'display_name': 'must not be recommended', 'friend_code': 'hidden-code'}}
    monkeypatch.setattr(nexus, '_fetch_active_user_ids', active)
    monkeypatch.setattr(nexus, '_fetch_followed_owner_ids', followed)
    monkeypatch.setattr(nexus, '_fetch_profiles_by_ids', profiles)
    monkeypatch.setattr(runtime, '_sb_get', fetch)
    result = asyncio.run(nexus._build_nexus_recommend_users_payload(viewer_user_id='viewer', limit=8))
    assert result['users'] == []
    assert requested_profiles == []
