"""Visibility failure cannot bypass a private account's approval boundary."""
import asyncio
from types import SimpleNamespace

import httpx
import pytest
from fastapi import FastAPI, HTTPException

import api_follow_graph as graph
import api_self_structure as owner


def follow(monkeypatch, visibility):
    writes = []
    async def user(*args): return 'synthetic-viewer'
    async def existing(*args): return False
    async def read(*args, **kwargs):
        if isinstance(visibility, Exception): raise visibility
        return visibility
    async def link(*args): writes.append(('link', args))
    async def request(*args): writes.append(('request', args)); return True
    async def no_request(*args): return None
    async def cleanup(*args): return None
    monkeypatch.setattr(graph, '_resolve_user_id_from_token', user)
    monkeypatch.setattr(graph, '_is_already_registered', existing)
    monkeypatch.setattr(owner, '_sb_get', read)
    monkeypatch.setattr(graph, '_insert_myprofile_link', link)
    monkeypatch.setattr(graph, '_insert_follow_request', request)
    monkeypatch.setattr(graph, '_find_existing_follow_request_id', no_request)
    monkeypatch.setattr(graph, '_delete_follow_request_pair', cleanup)
    app = FastAPI()
    graph.register_follow_graph_routes(app)
    endpoint = next(r.endpoint for r in app.routes if r.path == '/follow/create')
    body = SimpleNamespace(owner_user_id='synthetic-owner', connect_code=None, myprofile_code=None)
    return endpoint(body, authorization='Bearer synthetic-token'), writes


@pytest.mark.parametrize('failure', [
    httpx.Response(500, text='upstream unavailable'),
    httpx.Response(403, text='denied'),
    ConnectionError('synthetic transport offline'),
])
def test_visibility_failure_has_no_link_or_request_side_effect(monkeypatch, failure):
    work, writes = follow(monkeypatch, failure)
    with pytest.raises((HTTPException, ConnectionError)):
        asyncio.run(work)
    assert writes == []


@pytest.mark.parametrize('rows,kind,result', [
    ([{'is_private_account': True}], 'request', 'requested'),
    ([{'is_private_account': False}], 'link', 'followed'),
    ([], 'link', 'followed'),
])
def test_verified_private_public_and_missing_row_preserve_policy(monkeypatch, rows, kind, result):
    work, writes = follow(monkeypatch, httpx.Response(200, json=rows))
    response = asyncio.run(work)
    assert response.result == result
    assert [write[0] for write in writes] == [kind]
