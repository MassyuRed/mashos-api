"""Piece publication across the shared ASGI routes with synthetic Auth and PostgREST."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
import socket
import sys

import httpx
import pytest
from fastapi import HTTPException

_AI_ROOT = Path(__file__).resolve().parents[2]
for _path in (_AI_ROOT, _AI_ROOT / 'services', _AI_ROOT / 'services' / 'ai_inference'):
    sys.path.insert(0, str(_path))

import api_nexus as nexus
import api_piece_v2 as piece
import app as shared
import middleware_active_user_touch as active_touch
import piece_public_read_service as service
import supabase_client as database

OWNER = '20b0483e-5729-4f8e-94ad-f43ae9d6e638'
FOLLOWER = '6edd38b6-0f3f-40ee-9d44-42df9a0206b1'
STRANGER = '460edee1-0636-44de-8abe-3fedc2bf3741'
PIECE = 'f1fcf08d-4baf-422e-8faa-fab45f23e54e'
PIECE_ID = 'piece:' + PIECE
MUTATION = '/emotion/piece/' + PIECE_ID + '/visibility'
FEED = '/nexus/pieces?include_piece_v2=true'
PUBLISHED_AT = '2026-11-21T03:45:56+00:00'
BODY = 'この作品を通して、自分の気持ちをゆっくり言葉にできました。'
PRIVATE = 'SYNTHETIC_PRIVATE_SOURCE'
AUTH = {'owner': OWNER, 'follower': FOLLOWER, 'stranger': STRANGER}


@pytest.fixture
def application(monkeypatch):
    settings = dict(
        preview_requested=True, preview_ready=True,
        preview_runtime={'ttl_seconds': 600, 'renderer_version': 'synthetic-renderer.v1'},
        save_requested=True, save_ready=True,
        owner_read_requested=True, owner_read_ready=True,
        public_read_requested=True, public_read_ready=True,
        public_write_requested=True, public_write_ready=True,
        visibility_toggle_requested=True, visibility_toggle_ready=True,
    )
    app = shared.create_application(piece_preview_configuration=settings)
    state = {'visibility_scope': 'private', 'row_version': 2, 'secret': False}
    rpc_calls = []

    def block_network(*args, **kwargs):
        raise AssertionError('Only synthetic PostgREST requests may leave the ASGI app')

    async def require_user(token):
        if token not in AUTH:
            raise HTTPException(401, PRIVATE)
        return AUTH[token]

    async def verify_bearer(authorization):
        return await require_user(authorization.removeprefix('Bearer '))

    async def no_active_user(_token):
        return None

    async def followed_owners(*, viewer_user_id, limit):
        return {OWNER} if viewer_user_id == FOLLOWER else set()

    async def no_legacy_rows(*args, **kwargs):
        return []

    async def read_profiles(user_ids):
        return {owner: {'display_name': 'あるユーザー', 'friend_code': PRIVATE} for owner in user_ids}

    def sql_error(message):
        return httpx.Response(400, json={'code': 'P0001', 'message': message, 'details': PRIVATE})

    def upstream(request):
        assert request.headers['authorization'] == 'Bearer synthetic-service-only'
        assert request.method == 'POST'
        path = request.url.path.removeprefix('/rest/v1/rpc/')
        args = json.loads(request.content)
        rpc_calls.append((path, args))
        if path == 'piece_set_visibility_v2':
            if args['p_owner_user_id'] != OWNER or args['p_piece_id'] != PIECE:
                return sql_error('PIECE_NOT_FOUND')
            if args['p_expected_row_version'] != state['row_version']:
                return sql_error('PIECE_CONFLICT')
            if args['p_visibility_scope'] == 'public' and state['secret']:
                return sql_error('PIECE_PUBLICATION_NOT_ALLOWED')
            if state['visibility_scope'] != args['p_visibility_scope']:
                state['visibility_scope'] = args['p_visibility_scope']
                state['row_version'] += 1
            return httpx.Response(200, json={
                'piece_id': PIECE,
                'visibility_scope': state['visibility_scope'],
                'row_version': state['row_version'],
            })
        assert path == 'piece_read_public_feed_v2'
        assert args['p_target_owner_user_id'] is None
        eligible = (args['p_viewer_user_id'] == FOLLOWER or
                    (args['p_viewer_user_id'] == OWNER and not args['p_following_only']))
        if not eligible or state['visibility_scope'] != 'public':
            return httpx.Response(200, json=[])
        item = {'public_id': PIECE_ID, 'owner_user_id': OWNER, 'body': BODY, 'published_at': PUBLISHED_AT}
        if state.get('malformed'):
            item['source_input_id'] = PRIVATE
        return httpx.Response(200, json=[item])

    monkeypatch.setattr(socket.socket, 'connect', block_network)
    monkeypatch.setattr(nexus, '_resolve_user_id_from_token', require_user)
    monkeypatch.setattr(piece, '_verify_bearer', verify_bearer)
    monkeypatch.setattr(active_touch, 'resolve_user_id_verified_cached', no_active_user)
    monkeypatch.setattr(service, 'fetch_followed_owner_ids', followed_owners)
    monkeypatch.setattr(service, 'fetch_active_emotion_generated_reflections_for_owner', no_legacy_rows)
    monkeypatch.setattr(service, 'fetch_profiles_by_ids', read_profiles)
    monkeypatch.setattr(database, 'SUPABASE_URL', 'https://piece.invalid')
    monkeypatch.setattr(database, 'SUPABASE_SERVICE_ROLE_KEY', 'synthetic-service-only')

    def send(method, path, *, token='owner', **kwargs):
        headers = {'X-Piece-Publication': '1', **kwargs.pop('headers', {})}
        if token is not None:
            headers['Authorization'] = 'Bearer ' + token

        async def run():
            async with httpx.AsyncClient(transport=httpx.MockTransport(upstream)) as backend:
                async def get_backend():
                    return backend
                monkeypatch.setattr(database, 'get_async_client', get_backend)
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                             base_url='https://test.invalid') as http:
                    return await http.request(method, path, headers=headers, **kwargs)

        return asyncio.run(run())

    return send, state, rpc_calls


def test_publication_followers_and_withdrawal_use_one_saved_piece(application):
    send, _, calls = application
    assert send('GET', FEED, token='follower').json()['items'] == []

    published = send('PATCH', MUTATION, json={'expected_row_version': 2, 'visibility_scope': 'public'})
    assert published.status_code == 200
    assert published.headers['x-cocolon-contract-id'] == 'emotion.piece.visibility.v2'
    assert published.json() == {'piece_id': PIECE, 'visibility_scope': 'public', 'row_version': 3}

    call_count = len(calls)
    assert send('GET', '/nexus/pieces', token='follower').json()['items'] == []
    assert len(calls) == call_count
    follower = send('GET', FEED + '&sort=oldest&limit=7', token='follower')
    assert follower.status_code == 200
    assert 'no-store' in follower.headers['cache-control']
    assert calls[-1] == ('piece_read_public_feed_v2', {
        'p_viewer_user_id': FOLLOWER, 'p_target_owner_user_id': None, 'p_following_only': True,
        'p_sort': 'oldest', 'p_limit': 8,
    })
    items = [{
        'source_type': 'piece_v2', 'q_instance_id': PIECE_ID, 'body': BODY, 'created_at': PUBLISHED_AT,
        'owner': {'user_id': OWNER, 'display_name': 'あるユーザー'},
    }]
    assert follower.json()['items'] == items
    assert send('GET', FEED + '&following_only=false').json()['items'] == items
    assert send('GET', FEED, token='stranger').json()['items'] == []
    assert send('GET', FEED, token=None).status_code == 401

    withdrawn = send('PATCH', MUTATION, json={'expected_row_version': 3, 'visibility_scope': 'private'})
    assert withdrawn.status_code == 200
    assert withdrawn.json() == {'piece_id': PIECE, 'visibility_scope': 'private', 'row_version': 4}
    assert send('GET', FEED, token='follower').json()['items'] == []


def test_native_posts_and_legacy_display_share_sorting_only_for_opted_in_clients(application, monkeypatch):
    send, state, _ = application
    state['visibility_scope'] = 'public'
    legacy = {
        'source_type': 'emotion_generated', 'q_instance_id': 'reflection:legacy',
        'owner': {'user_id': OWNER, 'display_name': 'あるユーザー', 'friend_code': None},
        'question': {'q_key': 'legacy', 'title': '過去のタイトル'},
        'body': '過去の投稿本文', 'created_at': '2026-11-20T01:00:00+00:00',
        'metrics': {'views': 7, 'resonances': 2},
        'viewer_state': {'is_new': True, 'is_resonated': False, 'can_resonate': True},
    }

    async def legacy_items(*, viewer_user_id, rows):
        assert viewer_user_id == FOLLOWER
        return [legacy]

    monkeypatch.setattr(service, '_build_public_piece_items', legacy_items)
    current = send('GET', FEED, token='follower').json()
    assert current['items'][0]['q_instance_id'] == PIECE_ID
    assert current['items'][1] == legacy
    old = send('GET', '/nexus/pieces?include_piece_v2=false', token='follower').json()
    assert old['items'] == [legacy]
    alias = send('GET', '/nexus/reflections?include_piece_v2=true', token='follower')
    assert alias.status_code == 200 and alias.json()['items'] == [legacy]
    limited = send('GET', FEED + '&sort=oldest&limit=1', token='follower').json()
    assert limited['items'] == [legacy]
    assert limited['has_more'] is True


def test_ineligible_or_non_owner_publication_keeps_private_state(application):
    send, state, _ = application
    body = {'expected_row_version': 2, 'visibility_scope': 'public'}
    rejected = send('PATCH', MUTATION, token='follower', json=body)
    assert rejected.status_code == 404 and rejected.json() == {'code': 'PIECE_NOT_FOUND'}
    state['secret'] = True
    rejected = send('PATCH', MUTATION, json=body)
    assert rejected.status_code == 422 and rejected.json() == {'code': 'PIECE_PUBLICATION_NOT_ALLOWED'}
    assert PRIVATE not in rejected.text
    assert state['visibility_scope'] == 'private' and state['row_version'] == 2


def test_malformed_native_projection_does_not_expose_source_metadata(application):
    send, state, _ = application
    state.update(visibility_scope='public', malformed=True)
    response = send('GET', FEED, token='follower')
    assert response.status_code == 503
    assert response.json() == {'detail': 'Piece publication unavailable'}
    assert 'no-store' in response.headers['cache-control']
    assert PRIVATE not in response.text and BODY not in response.text


def test_initial_save_rejects_public_visibility_even_if_publication_is_enabled(application):
    send, state, calls = application
    response = send('POST', '/emotion/piece/save', headers={'Idempotency-Key': 'synthetic-save'}, json={
        'preview_id': PIECE,
        'expected_preview_revision': 1,
        'piece_text_hash': 'a' * 64,
        'content_payload_hash': 'b' * 64,
        'visual_recipe_hash': 'c' * 64,
        'visibility_scope': 'public',
    })
    assert response.status_code == 400
    assert response.json() == {'code': 'PIECE_REQUEST_INVALID'}
    assert calls == [] and state['visibility_scope'] == 'private'
