"""Exercise the final HTTP response, including the saved async pending marker."""
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock
import httpx
import pytest
from fastapi import FastAPI
import api_emotion_submit as submit
from emlis_ai_public_feedback_meta import should_include_public_input_feedback


@pytest.mark.parametrize('status,reason,saved,comment,pending', [
    ('unavailable','thread_reply_pending',True,'',True),
    ('unavailable','thread_reply_pending',False,'',False),
    ('unavailable','thread_body_unavailable',True,'',False),
    ('unavailable','thread_reply_paused',True,'',False),
    ('rejected','thread_reply_pending',True,'',False),
    ('unavailable','thread_reply_pending',True,'must not display',False),
])
def test_submit_delivers_only_minimal_saved_pending_meta(monkeypatch,status,reason,saved,comment,pending):
    public_meta={'observation_status':status,'rejection_reasons':[reason], 'internal_raw':'private-must-not-leak'}
    assert not should_include_public_input_feedback('', public_meta)
    persisted={'inserted':{'id':'saved-synthetic'} if saved else {}, 'input_feedback_comment':comment,
               'input_feedback_meta':public_meta,'created_at':'2026-11-08T00:00:00Z'}
    monkeypatch.setattr(submit,'_resolve_user_id_from_token',AsyncMock(return_value='synthetic-owner'))
    monkeypatch.setattr(submit,'execute_home_command',AsyncMock(return_value=SimpleNamespace(result=SimpleNamespace(data=persisted))))
    app=FastAPI();submit.register_emotion_submit_routes(app)
    async def request():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as client:
            return await client.post('/emotion/submit',headers={'Authorization':'Bearer synthetic'},json={
                'emotions':[{'type':'平穏','strength':'medium'}], 'memo':'合成の入力', 'category':['生活']})
    response=asyncio.run(request());assert response.status_code == 200
    feedback=response.json()['input_feedback']
    if pending:
        assert feedback == {'comment_text':'','emlis_ai':{'schema_version':'emlis.public_input_feedback_meta.v1',
            'observation_status':'unavailable','rejection_reasons':['thread_reply_pending']}}
    else:
        assert feedback is None
    assert 'private-must-not-leak' not in response.text
