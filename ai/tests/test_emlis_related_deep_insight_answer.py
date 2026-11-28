"""Admit only earlier DeepInsight answers bound to an Emlis history source."""

import asyncio
import json
from uuid import uuid4

import httpx
import pytest

import emlis_thread_store
import kokoro_weather_service as weather
from cocolon_meaning_experience_engine.natural_reply import build_natural_reply_messages
from test_analysis_deep_insight_handoff import RECEIVED_MAP_MIGRATIONS
from test_analysis_interpretation_correction_sources import sql_script
from test_emlis_natural_reply_application import natural_case
from test_emlis_q2_application import run
from test_emlis_q3_application import qdb


TOPIC = '会議の資料を読み直した'
QUESTION = '資料を確認するときに何を重視しますか？'
ANSWER = '次に読む人が迷わない順番を大切にします。'
MIGRATION = '20261128054343_emlis_related_deep_insight_answer.sql'


@pytest.fixture(scope='module')
def deep_db(qdb):
    for migration in (*RECEIVED_MAP_MIGRATIONS, '20261121134000_deep_insight_grounded_questions.sql', MIGRATION):
        sql_script(qdb, migration)
    assert 'code' not in qdb.query('alter table public.emotions add column is_secret boolean not null default false')
    return qdb


@pytest.fixture
def answered_history(natural_case, deep_db, monkeypatch):
    owner, entry, service, calls = natural_case
    earlier, answer_id = str(uuid4()), str(uuid4())
    assert 'code' not in deep_db.query("update public.profiles set subscription_tier='premium' where id=$1", [owner])
    assert 'code' not in deep_db.query("""insert into public.emotions(id,user_id,created_at,memo,memo_action,category,emotions,emotion_details)
        values($1,$2,(now()-interval '3 days') at time zone 'UTC',$3,'',array['仕事'],array['平穏'],$4)""",
        [earlier, owner, TOPIC + '。', json.dumps([{'type': '平穏', 'strength': 'medium'}])])
    assert 'code' not in deep_db.query("""insert into public.deep_insight_questions
        (id,user_id,lane,question_text,issued_on,issued_at,question_key,text_key,answer_text,answered_at,grounding_receipt)
        select $1,e.user_id,'records',$3,(current_date-2),(now()-interval '2 days'),'question','text',$4,
          (now()-interval '1 day'),jsonb_build_object('policy_version','deep-insight.v2','lane','records',
          'source_id',e.id,'source_version',encode(sha256(convert_to(public.emlis_parent_source(e)::text,'UTF8')),'hex'),
          'field','thought','start',0,'end',char_length($5::text),'literal_sha256',encode(sha256(convert_to($5::text,'UTF8')),'hex'))
        from public.emotions e where e.id=$2""", [answer_id, earlier, QUESTION, ANSWER, TOPIC])

    async def sql_rpc(name, payload, **kwargs):
        if name != 'emlis_related_deep_insight_answer':
            return await deep_db.rpc(name, payload, **kwargs)
        args = [payload['p_user_id'], payload['p_input_id'], json.dumps(payload['p_context_guards'])]
        result = await asyncio.to_thread(deep_db.query,
            'select public.emlis_related_deep_insight_answer($1,$2,$3) as value', args, 'service_role')
        assert 'code' not in result, result
        return httpx.Response(200, json=result['rows'][0]['value'])

    async def unavailable(*_args):
        return None

    monkeypatch.setattr(emlis_thread_store, 'sb_post_rpc', sql_rpc)
    monkeypatch.setattr(service.store, 'prior_map_context', unavailable)
    monkeypatch.setattr(weather, 'build_prior_kokoro_observation', unavailable)
    service.premium_context_enabled = True
    service.natural_questions_enabled = False
    return owner, entry, earlier, answer_id, service, calls


def test_normal_premium_writer_and_saved_reply_use_the_exact_record_answer(answered_history, deep_db):
    owner, entry, earlier, _, service, calls = answered_history
    result = run(service.start(owner, entry))
    assert result['current_observation'] and len(calls) == 1
    messages = build_natural_reply_messages(calls[0])
    writer = json.loads(messages[-1]['content'])
    answer = writer['prior_premium_context']['deep_insight_answer']
    assert answer['answer'] == ANSWER and answer['ai_question_context'] == QUESTION
    assert answer['recorded_at'] < answer['answered_at']
    assert earlier not in messages[-1]['content']
    assert 'AIの問いを本人の発言や起きた事実に数えません' in messages[0]['content']
    assert run(service.get(owner, entry))['current_observation'] == result['current_observation']
    assert 'premium_context_guard' not in result
    assert 'code' not in deep_db.query('update public.emotions set is_secret=true where id=$1', [earlier])
    changed = run(service.get(owner, entry))
    assert changed['body_state'] == 'CONTEXT_CHANGED' and changed['current_observation'] is None
    assert len(calls) == 1


@pytest.mark.parametrize('invalid', ['owner', 'tier', 'theme', 'past-topic', 'future-answer', 'changed-proof'])
def test_normal_writer_omits_an_ineligible_answer(answered_history, deep_db, invalid):
    owner, entry, _, answer_id, service, calls = answered_history
    if invalid == 'owner':
        other = str(uuid4())
        assert 'code' not in deep_db.query('insert into auth.users values($1)', [other])
        assert 'code' not in deep_db.query('update public.deep_insight_questions set user_id=$2 where id=$1',
            [answer_id, other])
    elif invalid == 'tier':
        assert 'code' not in deep_db.query("update public.profiles set subscription_tier='plus' where id=$1", [owner])
    elif invalid == 'theme':
        assert 'code' not in deep_db.query("update public.deep_insight_questions set lane='theme',theme='人間関係' where id=$1", [answer_id])
    elif invalid == 'past-topic':
        assert 'code' not in deep_db.query("update public.emotions set memo='会議の資料を棚にしまった。' where id=$1", [entry])
    elif invalid == 'future-answer':
        assert 'code' not in deep_db.query('update public.deep_insight_questions set answered_at=now() where id=$1', [answer_id])
    elif invalid == 'changed-proof':
        assert 'code' not in deep_db.query("update public.deep_insight_questions set grounding_receipt=grounding_receipt-'literal_sha256' where id=$1", [answer_id])
    assert run(service.start(owner, entry))['current_observation']
    assert ANSWER not in build_natural_reply_messages(calls[0])[-1]['content']


def test_context_rpc_is_service_role_only(deep_db):
    sql = "select has_function_privilege($1,'public.emlis_related_deep_insight_answer(uuid,uuid,jsonb)','execute') as eligible"
    for role in ('anon', 'authenticated', 'service_role'):
        assert deep_db.query(sql, [role])['rows'][0]['eligible'] == (role == 'service_role')
