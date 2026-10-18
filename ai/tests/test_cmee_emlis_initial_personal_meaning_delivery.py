"""Actual isolated SQL stores completed bodies and resumes whole saved meaning."""
import asyncio
from contextlib import contextmanager
from unittest.mock import patch
import pytest
from cocolon_meaning_experience_engine import emlis_question, emlis_answer_update as update
from test_cmee_emlis_initial_personal_meaning import ROWS, UPDATES
from test_cmee_emlis_loneliness_delivery import export_dto, reopen
from test_cmee_emlis_relief_received_delivery import record_operation_times, record_sql_errors
from test_emlis_q3_application import qdb, qcase
from test_emlis_q2_application import run, answer

@contextmanager
def old_initial():
    original=emlis_question._original_source_meaning_plan
    def legacy(source,**kwargs):
        kwargs['_legacy_initial_personal_meaning']=True
        return original(source,**kwargs)
    with patch.object(emlis_question,'_original_source_meaning_plan',legacy):
        yield

@pytest.mark.parametrize('case',['received','pair_received_unknown'])
@pytest.mark.parametrize('tier',['free','premium'])
@pytest.mark.parametrize('historical',[False,True])
def test_completed_initial_new_or_old_body_is_immutable(qcase,qdb,case,tier,historical):
    user,parent,service=qcase
    qdb.query('update public.emotions set memo=$2 where id=$1',[parent,ROWS[case]['memo']])
    qdb.query('update public.profiles set subscription_tier=$2 where id=$1',[user,tier])
    if historical:
        with old_initial(): saved=run(service.start(user,parent))
    else:
        saved=run(service.start(user,parent))
    assert saved['state']=='COMPLETED',saved
    assert saved['pending_question'] is None and not saved['can_continue']
    if historical:
        old=ROWS[case]['q3']['artifact']
        assert saved['current_observation']['text']==f"見えたこと：\n{old['observation']}\n\nEmlisから：\n{old['reception']}"
    else:
        assert '嬉しくなかったし、期待されているように感じて、重かったのですね。' in saved['current_observation']['text']
    assert run(service.get(user,parent))==saved
    reopen(user,parent,saved)
    stored=run(service.store.read(user,input_id=parent))
    record_operation_times(stored,f'initial-{case}-{tier}-{historical}')
    export_dto(f'initial-{case}-{tier}-{historical}',saved)

@pytest.mark.parametrize('tier',['free','premium'])
@pytest.mark.parametrize('historical',[False,True])
def test_actual_unmarked_pending_answer_and_old_stop_survive_saved_reads(qcase,qdb,tier,historical):
    user,parent,service=qcase;row=UPDATES['add_mixed']
    qdb.query('update public.emotions set memo=$2 where id=$1',[parent,row['memo']])
    qdb.query('update public.profiles set subscription_tier=$2 where id=$1',[user,tier])
    first=run(service.start(user,parent));assert first['state']=='AWAITING_ANSWER'
    original=update._prepare_emlis_meaning_from_plan_version
    def legacy(*args,**kwargs):
        kwargs['legacy_relief_cognition_update_retention']=True
        return original(*args,**kwargs)
    if historical:
        with patch.object(update,'_prepare_emlis_meaning_from_plan_version',legacy):
            saved=run(answer(service,user,first,row['answer']))
    else:
        saved=run(answer(service,user,first,row['answer']))
    assert saved['answer_saved'] and saved['meaning_updated']
    assert saved['original']==first['original']
    if historical:
        assert saved['current_observation'] is None
        assert saved['failure_code']=='body_not_validated'
        assert saved['body_state']=='MEANING_UPDATED_BODY_UNAVAILABLE'
        assert [event for event in saved['timeline'] if event['kind']=='OBSERVATION']==[
            dict(event,is_current=False) for event in first['timeline'] if event['kind']=='OBSERVATION']
        assert saved['state']=='RESPONSE_FAILED' and not saved['can_retry']
    else:
        assert saved['state']=='COMPLETED',saved
        body=saved['current_observation']['text']
        assert '重かった' in body and '私も少し安心しましたが' in body and 'わからない' in body
    reopen(user,parent,saved)
    record_operation_times(run(service.store.read(user,input_id=parent)),f'pending-{tier}-{historical}')
    export_dto(f'pending-{tier}-{historical}',saved)

@pytest.mark.parametrize('stage',['before_meaning','current_meaning','old_meaning'])
def test_confirmed_interruption_resumes_whole_checkpoint_without_reprepare(qcase,qdb,monkeypatch,stage):
    user,parent,service=qcase;row=ROWS['pair_received_unknown']
    qdb.query('update public.emotions set memo=$2 where id=$1',[parent,row['memo']])
    prepare,generate=service.engine.prepare_emlis_update,service.engine.generate
    def interrupted(*_): raise asyncio.CancelledError()
    monkeypatch.setattr(service.engine,'generate',interrupted)
    if stage=='before_meaning':monkeypatch.setattr(service.engine,'prepare_emlis_update',interrupted)
    with pytest.raises(asyncio.CancelledError):
        if stage=='old_meaning':
            with old_initial():run(service.start(user,parent))
        else:run(service.start(user,parent))
    pending=run(service.get(user,parent))
    assert pending['failure_code']=='worker_interrupted' and pending['can_retry']
    before=run(service.store.read(user,input_id=parent));meanings=[e for e in before['events'] if e['kind']=='MEANING_UPDATE']
    assert len(meanings)==int(stage!='before_meaning')
    monkeypatch.setattr(service.engine,'generate',generate)
    monkeypatch.setattr(service.engine,'prepare_emlis_update',prepare if stage=='before_meaning' else lambda *_:pytest.fail('saved meaning must be reused'))
    saved=run(service.action(user,pending['thread_id'],action='retry_response',expected_revision=pending['revision'],idempotency_key='u353-retry',operation_id=pending['operation_id']))
    assert saved['state']=='COMPLETED',saved
    after=run(service.store.read(user,input_id=parent));current=[e for e in after['events'] if e['kind']=='MEANING_UPDATE']
    assert len(current)==1
    if stage!='before_meaning':assert current==meanings
    body=saved['current_observation']['text']
    if stage=='old_meaning':
        old=row['q3']['artifact'];assert body==f"見えたこと：\n{old['observation']}\n\nEmlisから：\n{old['reception']}"
    else:assert '嬉しくなかったし、期待されているように感じて、重かったのですね。' in body
    reopen(user,parent,saved)
    export_dto(f'resume-{stage}',saved)
