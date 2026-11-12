"""Input choice through the existing submit owner and actual isolated SQL.

Provider bodies are synthetic. No live DB, deployment or model is exercised.
"""
import asyncio
import json
from json import dumps
from uuid import uuid4
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import FastAPI, HTTPException

import api_emotion_submit as submit
import emotion_submit_service as persistence
import emlis_thread_factory as factory
import emlis_thread_store
import home_gateway.command_gateway as gateway
from emlis_thread_service import EmlisThreadService, Q3_PROFILE
from cocolon_meaning_experience_engine.natural_reply import NaturalReply
from test_emlis_q2_application import run
from test_emlis_q3_application import qdb


MEMO = '褒められたのに、嬉しくなかった。'
BODY = '言葉を受け取ったときの気持ちは、単純ではなかったのですね。'


@pytest.fixture
def submitted_input(qdb, monkeypatch):
    user = str(uuid4())
    qdb.query('insert into auth.users values ($1)', [user])
    qdb.query("insert into public.profiles values ($1,'free')", [user])
    captures, calls = [], []

    async def insert(path, *, json, **kwargs):
        assert path == '/rest/v1/emotions'
        row = dict(json, id=str(uuid4()))
        captures.append(row)
        result = qdb.query(
            'insert into public.emotions(id,user_id,created_at,memo,memo_action,category,emotions,emotion_details,receive_emlis_questions) '
            "values ($1,$2,($3::timestamptz) at time zone 'UTC',$4,$5,$6,$7,$8,$9)",
            [row['id'], row['user_id'], row['created_at'], row.get('memo'), row.get('memo_action'),
             row.get('category'), row['emotions'], dumps(row['emotion_details']),
             row['receive_emlis_questions']])
        assert 'code' not in result, result
        return httpx.Response(201, json=[row])

    async def provider(material):
        payload = json.loads(material.material_json)
        calls.append(payload)
        return NaturalReply(BODY, 'synthetic-preference-test', material.source_prefix_ref)

    monkeypatch.setattr(submit, '_ensure_supabase_config', lambda: None)
    monkeypatch.setattr(submit, '_sb_post_shared', insert)
    monkeypatch.setattr(submit, '_resolve_user_id_from_token', AsyncMock(return_value=user))
    monkeypatch.setattr(persistence, '_start_post_submit_background_tasks', lambda **_: None)
    monkeypatch.setattr(persistence, 'invalidate_prefix', AsyncMock())
    monkeypatch.setattr(persistence, 'get_subscription_tier_for_user', AsyncMock(return_value='free'))
    monkeypatch.setattr(gateway, 'execute_cache_invalidation', AsyncMock())
    monkeypatch.setattr(emlis_thread_store, 'sb_post_rpc', qdb.rpc)
    monkeypatch.setenv('COCOLON_ENV', 'development')
    monkeypatch.setenv('COCOLON_EMLIS_THREAD_DEVELOPMENT', 'true')
    monkeypatch.setenv('EMLIS_AI_REPLY_TIMEOUT_SECONDS', '10.0')
    monkeypatch.delenv('COCOLON_EMLIS_THREAD_MODE', raising=False)
    app = FastAPI()
    submit.register_emotion_submit_routes(app)

    async def submit_one(*, enabled='omitted', natural=True):
        owner = EmlisThreadService(runtime_profile=Q3_PROFILE,
            natural_reply_source=provider if natural else None)
        monkeypatch.setattr(factory, 'application_thread_service', lambda: owner)
        payload = {'emotions': [{'type': '不安', 'strength': 'medium'}],
                   'memo': MEMO, 'memo_action': '', 'category': ['仕事'],
                   'send_emotion_notification': False}
        if enabled != 'omitted':
            payload['receive_emlis_questions'] = enabled
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
            response = await client.post('/emotion/submit', headers={'Authorization': 'Bearer synthetic'}, json=payload)
        if response.status_code == 200:
            tasks = list(factory._initial_tasks.values())
            if tasks:
                await asyncio.gather(*tasks)
            dto = await owner.get(user, response.json()['id'])
            return response, dto, owner
        return response, None, owner

    return user, submit_one, captures, calls


@pytest.mark.parametrize('natural', [False, True])
@pytest.mark.parametrize('enabled', ['omitted', True, False])
def test_public_choice_reaches_saved_input_and_background_thread(submitted_input, qdb, natural, enabled):
    user, submit_one, captures, calls = submitted_input
    response, dto, owner = run(submit_one(enabled=enabled, natural=natural))
    assert response.status_code == 200, response.text
    expected = enabled is not False
    assert captures[-1]['receive_emlis_questions'] is expected
    assert captures[-1]['memo'] == MEMO and captures[-1]['category'] == ['仕事']
    saved = run(owner.store.read(user, input_id=response.json()['id']))
    assert saved['receive_emlis_questions'] is expected
    assert saved['thread']['data']['receive_emlis_questions'] is expected
    assert 'receive_emlis_questions' not in saved['original']
    assert 'receive_emlis_questions' not in response.text
    assert 'receive_emlis_questions' not in json.dumps(dto)
    assert dto['current_observation']['text']
    if expected:
        assert dto['state'] == 'AWAITING_ANSWER' and dto['issued_count'] == 1
        assert dto['pending_question']
    else:
        assert dto['state'] == 'COMPLETED' and dto['issued_count'] == 0
        assert dto['pending_question'] is None and not dto['can_continue']
        assert not any(e['kind'] == 'QUESTION' for e in saved['events'])
        assert not saved['thread']['data'].get('continuation_question')
        assert dto['body_state'] == 'FINAL'
    if natural:
        assert len(calls) == 1
        assert calls[0].get('response_purpose', {'stage': 'FINAL'})['stage'] == ('PRE_QUESTION' if expected else 'FINAL')
        assert 'receive_emlis_questions' not in json.dumps(calls)


@pytest.mark.parametrize('value', ['false', 'true', 0, 1, None, [], {}])
def test_non_boolean_public_preference_is_rejected_before_insert(submitted_input, value):
    _, submit_one, captures, calls = submitted_input
    response, dto, _ = run(submit_one(enabled=value))
    assert response.status_code == 422
    assert not captures and not calls and dto is None


@pytest.mark.parametrize('natural', [False, True])
def test_saved_off_survives_submit_process_loss_before_thread_admission(submitted_input, qdb, monkeypatch, natural):
    user, submit_one, captures, calls = submitted_input
    # Simulate the request ending after INSERT, before any thread can start.
    original_render = persistence.render_emlis_ai_reply
    monkeypatch.setattr(persistence, 'render_emlis_ai_reply', AsyncMock(side_effect=asyncio.TimeoutError))
    response, _, owner = run(submit_one(enabled=False, natural=natural))
    assert response.status_code == 200
    parent = response.json()['id']
    assert qdb.query('select count(*)::int as n from public.emlis_input_threads where original_emotion_id=$1', [parent])['rows'][0]['n'] == 0
    monkeypatch.setattr(persistence, 'render_emlis_ai_reply', original_render)
    # A fresh owner has default ON, but this input's durable OFF controls it.
    dto = run(owner.start(user, parent))
    assert dto['state'] == 'COMPLETED' and dto['issued_count'] == 0
    assert dto['pending_question'] is None and dto['current_observation']['text']
    assert len(calls) == (1 if natural else 0)


@pytest.mark.parametrize('enabled', [False, True])
def test_started_choice_and_saved_reread_ignore_later_input_setting_changes(submitted_input, qdb, enabled):
    user, submit_one, _, calls = submitted_input
    response, dto, owner = run(submit_one(enabled=enabled))
    parent = response.json()['id']
    qdb.query('update public.emotions set receive_emlis_questions=$2 where id=$1', [parent, not enabled])
    before_calls = len(calls)
    restarted = EmlisThreadService(runtime_profile=Q3_PROFILE)
    # start() finds the saved thread before examining the newly read preference.
    assert run(restarted.start(user, parent))['state'] == dto['state']
    assert run(restarted.get(user, parent))['current_observation'] == dto['current_observation']
    assert len(calls) == before_calls
    saved = run(owner.store.read(user, input_id=parent))
    assert saved['thread']['data']['receive_emlis_questions'] is enabled


def test_private_rpc_preserves_source_and_owner_acl(submitted_input, qdb):
    user, submit_one, _, _ = submitted_input
    response, _, owner = run(submit_one(enabled=False))
    parent = response.json()['id']
    saved = run(owner.store.read(user, input_id=parent))
    assert set(saved['original']) == {'id','created_at','memo','memo_action','category','emotions','emotion_details'}
    other = str(uuid4())
    result = qdb.query('select public.emlis_thread_read($1,$2,null) as value', [other, parent], 'service_role')
    assert result['rows'][0]['value'] is None
    privileges = qdb.query("select prosecdef, has_function_privilege('anon',oid,'EXECUTE') as anon, "
        "has_function_privilege('authenticated',oid,'EXECUTE') as authenticated, "
        "has_function_privilege('service_role',oid,'EXECUTE') as service "
        "from pg_proc where oid='public.emlis_thread_read(uuid,uuid,uuid)'::regprocedure")['rows'][0]
    assert privileges == {'prosecdef': False, 'anon': False, 'authenticated': False, 'service': True}


@pytest.mark.parametrize('value', [None, 0, 'false'])
def test_internal_submit_cannot_coerce_preference(submitted_input, value):
    user, _, captures, _ = submitted_input
    with pytest.raises(HTTPException) as error:
        run(persistence.persist_emotion_submission(user_id=user, emotions=['不安'], memo=MEMO,
            memo_action=None, category=['仕事'], receive_emlis_questions=value))
    assert error.value.status_code == 400
    assert not captures
