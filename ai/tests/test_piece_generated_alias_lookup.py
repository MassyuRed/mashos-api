"""Actual legacy lookup/owner gate with a UUID-typed synthetic transport."""
import json
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException

import piece_generated_access as access
from test_emlis_q2_application import run


@pytest.mark.parametrize('public_id', ['old-public-text', 'reflection:old-public-text'])
@pytest.mark.parametrize('request_prefix', ['', 'reflection:'])
def test_non_uuid_public_alias_reaches_text_lookup_without_invalid_uuid_query(
        monkeypatch, public_id, request_prefix):
    row = dict(id=str(uuid4()), public_id=public_id, owner_user_id='owner',
               source_type='emotion_generated', is_active=True, status='ready')
    calls = []

    async def read(path, *, params):
        calls.append(dict(params))
        assert params['source_type'] == 'eq.emotion_generated'
        assert params['is_active'] == 'eq.true' and params['status'] == 'in.(ready,published)'
        if 'id' in params:
            # A real UUID column rejects a text public alias here.
            UUID(params['id'][3:])
            return [row] if params['id'][3:] == row['id'] else []
        values = json.loads('[' + params['public_id'][4:-1] + ']')
        return [row] if row['public_id'] in values else []

    monkeypatch.setattr(access, 'sb_get_json', read)
    monkeypatch.setattr(access, 'get_public_generated_reflection_text', lambda row: '保存済み本文です。')
    requested = request_prefix + 'old-public-text'
    assert run(access.fetch_emotion_generated_row_by_instance_id(requested)) == row
    assert len(calls) == 1 and 'id' not in calls[0]


def test_uuid_database_id_still_uses_typed_id_and_existing_public_lookup(monkeypatch):
    row = dict(id=str(uuid4()), public_id='old-text', owner_user_id='owner',
               source_type='emotion_generated')
    calls = []

    async def read(path, *, params):
        calls.append(dict(params))
        if 'id' in params:
            assert UUID(params['id'][3:]) == UUID(row['id'])
            return [row]
        assert 'public_id' in params
        return []

    monkeypatch.setattr(access, 'sb_get_json', read)
    monkeypatch.setattr(access, 'get_public_generated_reflection_text', lambda row: '保存済み本文です。')
    assert run(access.fetch_emotion_generated_row_by_instance_id('reflection:' + row['id'])) == row
    assert len(calls) == 2 and calls[0]['id'] == 'eq.' + row['id']


def test_text_alias_preserves_owner_access_and_unavailable_row_rules(monkeypatch):
    row = dict(id=str(uuid4()), public_id='old-text', owner_user_id='owner',
               source_type='emotion_generated')
    state = {'allowed': False, 'body': '保存済み本文です。', 'found': True}
    calls = []

    async def read(path, *, params):
        assert 'id' not in params
        return [row] if state['found'] else []

    async def linked(**kwargs):
        calls.append(kwargs)
        return state['allowed']

    monkeypatch.setattr(access, 'sb_get_json', read)
    monkeypatch.setattr(access, 'has_myprofile_link', linked)
    monkeypatch.setattr(access, 'get_public_generated_reflection_text', lambda row: state['body'])
    with pytest.raises(HTTPException) as error:
        run(access.resolve_generated_reflection_access(viewer_user_id='viewer', q_instance_id='reflection:old-text'))
    assert error.value.status_code == 403
    assert calls == [dict(viewer_user_id='viewer', owner_user_id='owner')]
    state['allowed'] = True
    assert run(access.resolve_generated_reflection_access(viewer_user_id='viewer',
               q_instance_id='reflection:old-text')) == row
    for changed in ('body', 'found'):
        before = state[changed]
        state[changed] = False
        with pytest.raises(HTTPException) as error:
            run(access.resolve_generated_reflection_access(viewer_user_id='viewer', q_instance_id='reflection:old-text'))
        assert error.value.status_code == 404
        state[changed] = before
