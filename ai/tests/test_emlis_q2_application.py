"""Synthetic end-to-end application tests against the actual migration/RPC SQL.

Run with Q2_PGLITE_MODULE=/path/to/@electric-sql/pglite (0.5.8).
This exercises PostgreSQL transactions, not a dictionary replacement for storage.
"""
import asyncio
import copy
import json
import os
from pathlib import Path
import subprocess
import threading
from uuid import uuid4

import httpx
import pytest
from emlis_thread_service import EmlisThreadService
from emlis_thread_store import EmlisThreadStore, ThreadStoreError
import emlis_thread_store

ORIGINAL = '褒められたのに、嬉しくなかった。'
ANSWER = '次も同じ成果を求められるようで、重かった。'
CORRECTION = '相手が嫌なのではなく、自分ではまだ納得していなかった。'

class Database:
    def __init__(self):
        self.lock = threading.Lock()
        self.proc = subprocess.Popen(['node', str(Path(__file__).parent / 'helpers/emlis_q2_postgres.cjs')],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        assert json.loads(self.proc.stdout.readline()) == {'ready': True}

    def query(self, sql, params=(), role=None):
        with self.lock:
            self.proc.stdin.write(json.dumps(dict(sql=sql, params=params, role=role)) + '\n')
            self.proc.stdin.flush()
            return json.loads(self.proc.stdout.readline())

    async def rpc(self, name, payload, **kwargs):
        assert name in {'emlis_thread_read', 'emlis_thread_commit'}
        args = ','.join(f'{k} => ${i}' for i, k in enumerate(payload, 1))
        params = [json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v for v in payload.values()]
        result = await asyncio.to_thread(self.query, f'select public.{name}({args}) as value', params, 'service_role')
        return httpx.Response(400 if 'code' in result else 200,
            json=result if 'code' in result else result['rows'][0]['value'])

@pytest.fixture(scope='module')
def db():
    if not os.environ.get('Q2_PGLITE_MODULE'):
        pytest.skip('Q2 PostgreSQL WASM test dependency is not configured')
    value = Database()
    yield value
    value.proc.stdin.close()
    value.proc.wait(timeout=10)

@pytest.fixture
def case(db, monkeypatch):
    user, input_id = str(uuid4()), str(uuid4())
    assert 'code' not in db.query('insert into auth.users values ($1)', [user])
    db.query("insert into public.profiles values ($1,'free')", [user])
    db.query("insert into public.emotions values ($1,$2,now() at time zone 'UTC',$3,'',array['仕事'],array['不安'],$4)",
        [input_id, user, ORIGINAL, json.dumps([dict(type='不安', strength='medium')], ensure_ascii=False)])
    monkeypatch.setattr(emlis_thread_store, 'sb_post_rpc', db.rpc)
    return user, input_id, EmlisThreadService()

def run(awaitable):
    return asyncio.run(awaitable)

def answer(service, user, dto, text=ANSWER, key='answer-1'):
    return service.answer(user, dto['thread_id'], question_id=dto['pending_question']['question_id'],
        expected_revision=dto['revision'], idempotency_key=key, answer_text=text,
        authored_at='2026-09-11T00:00:00+00:00')

def test_persisted_round_and_restart_get_do_not_generate(case):
    user, parent, service = case
    initial = run(service.start(user, parent))
    assert initial['state'] == 'AWAITING_ANSWER', initial
    completed = run(answer(service, user, initial))
    assert completed['body_state'] == 'REFINED', completed
    assert completed['answer_saved'] and completed['meaning_updated']
    assert ANSWER.rstrip('。') in completed['current_observation']['text']
    assert completed['issued_count'] == 1 and completed['pending_question'] is None
    assert [e['kind'] for e in completed['timeline']] == ['OBSERVATION','QUESTION','ANSWER','OBSERVATION']
    class NoAuthor:
        def __getattr__(self, name):
            raise AssertionError('GET or replay attempted generation')
    restarted = EmlisThreadService(engine=NoAuthor())
    assert run(restarted.get(user, parent)) == completed
    replay = run(answer(restarted, user, initial))
    assert replay['attempt_id'] == completed['attempt_id']
    assert len(replay['timeline']) == 4
    public = json.dumps(completed)
    assert all(x not in public for x in ('source_prefix_ref','meaning_graph','artifact','checkpoint_id','raw_utf8'))
