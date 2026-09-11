"""Q4: actual persisted application mode, pause and legacy delivery."""
from dataclasses import replace
import pytest
from test_emlis_q3_application import qdb, qcase, cont
from test_emlis_q2_application import run, answer
from emlis_thread_service import EmlisThreadService, Q3_PROFILE, _request
from emlis_thread_store import ThreadStoreError

def active(monkeypatch):
    monkeypatch.setenv('COCOLON_EMLIS_THREAD_MODE','active')
    monkeypatch.setenv('COCOLON_EMLIS_THREAD_RELEASE_APPROVED','true')
    return EmlisThreadService(runtime_profile=Q3_PROFILE,enforce_application_policy=True)

@pytest.mark.parametrize('mode,read,write',[('legacy',False,False),('active',True,True),('read_only',True,False),('invalid',True,False)])
def test_policy_bootstrap(monkeypatch,mode,read,write):
    from emlis_thread_config import read_enabled,writes_enabled
    from api_app_bootstrap import _feature_flags
    monkeypatch.setenv('COCOLON_EMLIS_THREAD_MODE',mode)
    monkeypatch.setenv('COCOLON_EMLIS_THREAD_RELEASE_APPROVED','true')
    assert read_enabled() is read and writes_enabled() is write
    assert _feature_flags()['emlis_threads_enabled'] is read

def test_application_mode_never_admits_single_request(qcase,monkeypatch):
    from cocolon_meaning_experience_engine.contracts import EngineStatus
    user,parent,_=qcase;s=active(monkeypatch);run(s.start(user,parent))
    req=_request(run(s._hydrate(user,run(s.store.read(user,input_id=parent)))))
    assert req.execution_mode=='EMLIS_APPLICATION'
    assert s.engine.generate(replace(req,emlis_thread=None)).status is EngineStatus.REJECTED
    with pytest.raises(ValueError):s.engine.prepare_emlis_update(replace(req,emlis_thread=None))

def test_old_client_gets_only_saved_current_body(qcase,monkeypatch):
    from emlis_ai_reply_service import render_emlis_ai_reply
    user,parent,_=qcase;s=active(monkeypatch)
    monkeypatch.setattr('emlis_ai_reply_service._step10_dormant_v3_public_hook',lambda **_:pytest.fail('second author'))
    def reply():return run(render_emlis_ai_reply(user_id=user,subscription_tier='premium',current_input={'id':parent}))
    before=reply();dto=run(s.get(user,parent))
    assert before.comment_text==dto['current_observation']['text'] and before.meta['observation_status']=='passed'
    assert dto['pending_question']['text'] not in before.comment_text and 'QUESTION_PENDING' not in str(before.meta)
    done=run(answer(s,user,dto,'はい。'));assert done['current_observation'] is None
    monkeypatch.setenv('COCOLON_EMLIS_THREAD_MODE','read_only');after=reply()
    assert after.comment_text=='' and after.meta['observation_status']=='unavailable'

@pytest.mark.parametrize('profile',['q2.free.one_round.v1',Q3_PROFILE])
def test_saved_profile_pause_read_resume(qcase,qdb,monkeypatch,profile):
    user,parent,_=qcase;s=active(monkeypatch);old=EmlisThreadService(runtime_profile=profile)
    if profile!=Q3_PROFILE:qdb.query("update public.emotions set memo=$2 where id=$1",[parent,"褒められたのに、嬉しくなかった。"])
    before=run(old.start(user,parent))
    if profile==Q3_PROFILE:before=run(answer(old,user,before,'その時は重かった。'))
    stored=run(s.store.read(user,input_id=parent))['thread']
    monkeypatch.setenv('COCOLON_EMLIS_THREAD_MODE','read_only');paused=run(s.get(user,parent))
    assert paused['timeline']==before['timeline'] and not paused['can_write'] and not paused['can_continue']
    with pytest.raises(ThreadStoreError,match='application_paused'):
        run(cont(s,user,paused,'next')) if profile==Q3_PROFILE else run(answer(s,user,paused,'その時は怖かった。'))
    assert run(s.store.read(user,input_id=parent))['thread']==stored
    monkeypatch.setenv('COCOLON_EMLIS_THREAD_MODE','active');restored=run(s.get(user,parent));assert restored==before
    after=run(cont(s,user,restored,'next')) if profile==Q3_PROFILE else run(answer(s,user,restored,'その時は怖かった。'))
    assert after['issued_count']==(2 if profile==Q3_PROFILE else 1)
    assert run(s.store.read(user,input_id=parent))['thread']['data']['runtime_profile']==profile

@pytest.mark.parametrize('stage',['meaning','body'])
def test_pause_during_attempt_can_resume_same_answer(qcase,monkeypatch,stage):
    user,parent,_=qcase;s=active(monkeypatch);dto=run(s.start(user,parent))
    method='prepare_emlis_update' if stage=='meaning' else 'generate';original=getattr(s.engine,method)
    def pause(req):
        result=original(req);monkeypatch.setenv('COCOLON_EMLIS_THREAD_MODE','read_only');return result
    monkeypatch.setattr(s.engine,method,pause);failed=run(answer(s,user,dto,'その時は重かった。'))
    assert failed['state']=='RESPONSE_FAILED' and failed['failure_code']=='worker_interrupted'
    assert failed['answer_saved'] and not failed['can_write'] and not failed['can_retry'] and failed['current_observation'] is None
    saved=run(s.store.read(user,input_id=parent));cp=saved['thread']['current_meaning_event_id']
    assert not saved['thread']['active_attempt_id'] and failed['issued_count']==1
    monkeypatch.setattr(s.engine,method,original);monkeypatch.setenv('COCOLON_EMLIS_THREAD_MODE','active')
    fresh=run(s.get(user,parent));assert fresh['can_retry']
    if stage=='body':monkeypatch.setattr(s.engine,'prepare_emlis_update',lambda *_:pytest.fail('saved checkpoint recomputed'))
    recovered=run(s.action(user,fresh['thread_id'],action='retry_response',expected_revision=fresh['revision'],idempotency_key='resume',operation_id=fresh['operation_id']))
    assert recovered['body_state']=='REFINED' and recovered['operation_id']==failed['operation_id']
    after=run(s.store.read(user,input_id=parent));assert len([e for e in after['events'] if e['kind']=='ANSWER'])==1
    if stage=='body':assert after['thread']['current_meaning_event_id']==cp

def test_next_question_failure_preserves_valid_body(qcase,monkeypatch):
    user,parent,s=qcase;dto=run(s.start(user,parent))
    def fail(*a,**k):raise ValueError('question unavailable')
    monkeypatch.setattr('cocolon_meaning_experience_engine.emlis_thread_engine.question_candidate',fail)
    result=run(answer(s,user,dto,'その時は重かった。'))
    assert result['state']=='COMPLETED' and result['body_state']=='REFINED' and result['current_observation']
    assert result['meaning_updated'] and result['issued_count']==1 and not result['can_continue']

def test_positive_answer_is_feeling_not_burden_or_completed_change():
    from test_cmee_emlis_q1_thread import render
    result=render('今は嬉しい。')
    assert '嬉しい' in result.artifact.reception
    assert '嬉しいことを小さくせず' not in result.artifact.reception and 'その変化' not in result.artifact.reception
    from test_cmee_emlis_q1_thread import answered
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning,build_updated_grounded_plan
    plan=build_updated_grounded_plan(prepare_emlis_meaning(answered('今は嬉しい。')))
    moves=plan.response_plan.human_reception_plan.moves
    answer_moves=[m for m in moves if any(n.startswith('answer:') for n in m.target_nucleus_ids)]
    assert answer_moves and all(m.reception_act=='recognize_lived_change' for m in answer_moves)
