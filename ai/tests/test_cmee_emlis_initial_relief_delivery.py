"""Initial short Reception, immutable completed records and meaning-first retry."""
import asyncio
from unittest.mock import patch

import pytest
import emlis_ai_grounded_sentence_surface as surface
from test_cmee_emlis_initial_relief_layout import ROWS
from test_cmee_emlis_loneliness_delivery import export_dto, reopen
from test_emlis_q3_application import qdb, qcase
from test_emlis_q2_application import run, answer


def assert_short(dto):
    obs,follow=dto['current_observation']['text'].split('Emlisから：',1)
    assert 'かもしれない' in obs and 'かもしれない' not in follow
    assert '私も少し安心しましたが、その寂しさにも、今、耳を傾けていたいです。' in follow


@pytest.mark.parametrize('case',['mixed','unknown','ambiguous'])
@pytest.mark.parametrize('historical',[False,True],ids=['current','u346_completed'])
def test_initial_saved_complete_body_reopens_without_generation(qcase,qdb,case,historical):
    user,parent,service=qcase
    qdb.query('update public.emotions set memo=$2 where id=$1',[parent,ROWS[case]['memo']])
    if historical:
        with patch.object(surface,'_retained_relief_observation_pair',return_value=frozenset()):
            saved=run(service.start(user,parent))
        old=ROWS[case]['q3']['artifact']
        assert saved['current_observation']['text']==f"見えたこと：\n{old['observation']}\n\nEmlisから：\n{old['reception']}"
    else:
        saved=run(service.start(user,parent))
        if case!='ambiguous':assert_short(saved)
        else:assert saved['current_observation']['text'].split('Emlisから：',1)[1].strip()==ROWS[case]['q3']['artifact']['reception']
    assert saved['state']=='AWAITING_ANSWER' and saved['body_state']=='PRE_QUESTION'
    assert saved['original']['memo']==ROWS[case]['memo']
    assert len([e for e in saved['timeline'] if e['kind']=='QUESTION'])==1
    assert len([e for e in saved['timeline'] if e['kind']=='ANSWER'])==0
    reopen(user,parent,saved)
    export_dto(f'initial-{historical}-{case}',saved)


@pytest.mark.parametrize('case,text',[('add','今は嬉しい。'),
    ('revise','「嬉しくなかった」ではなく「悲しかった」です。'),('withdraw','「褒められた」は誤りです。')])
def test_short_initial_and_one_actual_answer_keep_history(qcase,qdb,case,text):
    user,parent,service=qcase
    qdb.query('update public.emotions set memo=$2 where id=$1',[parent,ROWS['unknown']['memo']])
    first=run(service.start(user,parent));assert_short(first)
    saved=run(answer(service,user,first,text,'u347-'+case))
    assert saved['state']=='COMPLETED' and saved['body_state']=='REFINED'
    assert_short(saved)
    observations=[e['text'] for e in saved['timeline'] if e['kind']=='OBSERVATION']
    assert observations==[first['current_observation']['text'],saved['current_observation']['text']]
    assert len([e for e in saved['timeline'] if e['kind']=='ANSWER'])==1
    assert saved['original']==first['original']
    reopen(user,parent,saved)
    export_dto('initial-answer-'+case,saved)


@pytest.mark.parametrize('after_checkpoint',[False,True])
def test_interrupted_initial_uses_saved_meaning_without_duplicate_event(qcase,qdb,monkeypatch,after_checkpoint):
    user,parent,service=qcase
    qdb.query('update public.emotions set memo=$2 where id=$1',[parent,ROWS['unknown']['memo']])
    prepare,generate=service.engine.prepare_emlis_update,service.engine.generate
    def interrupted(*_):raise asyncio.CancelledError()
    monkeypatch.setattr(service.engine,'generate',interrupted)
    if not after_checkpoint:monkeypatch.setattr(service.engine,'prepare_emlis_update',interrupted)
    with pytest.raises(asyncio.CancelledError):run(service.start(user,parent))
    pending=run(service.get(user,parent))
    before=run(service.store.read(user,input_id=parent))
    meanings=[e for e in before['events'] if e['kind']=='MEANING_UPDATE']
    assert len(meanings)==int(after_checkpoint) and pending['can_retry']
    monkeypatch.setattr(service.engine,'generate',generate)
    monkeypatch.setattr(service.engine,'prepare_emlis_update',
        (lambda *_:pytest.fail('saved meaning must be reused')) if after_checkpoint else prepare)
    saved=run(service.action(user,pending['thread_id'],action='retry_response',
        expected_revision=pending['revision'],idempotency_key='u347-retry',operation_id=pending['operation_id']))
    after=run(service.store.read(user,input_id=parent))
    current=[e for e in after['events'] if e['kind']=='MEANING_UPDATE']
    assert len(current)==1 and saved['operation_id']==pending['operation_id']
    if after_checkpoint:assert current==meanings
    assert len([e for e in after['events'] if e['kind']=='OBSERVATION'])==1
    assert len([e for e in after['events'] if e['kind']=='QUESTION'])==1
    assert_short(saved)
    reopen(user,parent,saved)
    export_dto('initial-retry-'+str(after_checkpoint),saved)
