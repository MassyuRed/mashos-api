"""Q3 synthetic workflow over actual Q2 + additive Q3 migration."""
import asyncio, json, os
from pathlib import Path
from uuid import uuid4
import httpx, pytest
from test_emlis_q2_application import Database, run, answer
from emlis_thread_service import EmlisThreadService, Q3_PROFILE
import emlis_thread_store

class Q3Database(Database):
    def migrate(self):
        sql=(Path(__file__).parents[2]/'supabase/migrations/20260911041749_emlis_q3_plan_rounds.sql').read_text()
        self.proc.stdin.write(json.dumps(dict(sql=sql,script=True))+'\n'); self.proc.stdin.flush()
        result=json.loads(self.proc.stdout.readline()); assert 'code' not in result,result
    async def rpc(self,name,payload,**kwargs):
        assert name in {'emlis_thread_read','emlis_thread_commit','emlis_thread_context'}
        args=','.join(f'{k} => ${i}' for i,k in enumerate(payload,1))
        params=[json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for v in payload.values()]
        result=await asyncio.to_thread(self.query,f'select public.{name}({args}) as value',params,'service_role')
        return httpx.Response(400 if 'code' in result else 200,headers={'content-type':'application/json'},
          content=json.dumps(result if 'code' in result else result['rows'][0]['value'],ensure_ascii=False))

@pytest.fixture(scope='module')
def qdb():
    if not os.environ.get('Q2_PGLITE_MODULE'): pytest.skip('PostgreSQL WASM dependency not configured')
    db=Q3Database();db.migrate();yield db;db.proc.stdin.close();db.proc.wait(timeout=10)

@pytest.fixture
def qcase(qdb,monkeypatch):
    user,parent=str(uuid4()),str(uuid4())
    qdb.query('insert into auth.users values ($1)',[user]);qdb.query("insert into public.profiles values ($1,'premium')",[user])
    memo='褒められたのに、嬉しくなかった。誘われたのに、悲しかった。頼まれたのに、寂しかった。'
    qdb.query("insert into public.emotions values ($1,$2,now() at time zone 'UTC',$3,'',array['仕事'],array['不安'],$4)",[parent,user,memo,json.dumps([dict(type='不安',strength='medium')])])
    monkeypatch.setattr(emlis_thread_store,'sb_post_rpc',qdb.rpc)
    return user,parent,EmlisThreadService(runtime_profile=Q3_PROFILE)

def cont(service,user,dto,key):
    return service.action(user,dto['thread_id'],action='continue',expected_revision=dto['revision'],idempotency_key=key)

def test_three_saved_rounds_require_personal_continue(qcase,qdb):
    user,parent,s=qcase;dto=run(s.start(user,parent));assert dto['state']=='AWAITING_ANSWER',dto
    for n,text in enumerate(('その時は重かった。','その時は怖かった。','その時は苦しかった。'),1):
        assert dto['issued_count']==n
        dto=run(answer(s,user,dto,text,f'answer-{n}'))
        assert dto['body_state']=='REFINED',dto
        assert text[4:-1] in dto['current_observation']['text']
        fetched=run(s.get(user,parent));assert fetched==dto
        if n<3:
            assert dto['state']=='AWAITING_CONTINUE' and dto['pending_question'] is None
            dto=run(cont(s,user,dto,f'continue-{n}'))
        else: assert dto['state']=='COMPLETED' and not dto['can_continue']
    assert [x['round_index'] for x in dto['timeline'] if x['kind']=='QUESTION']==[1,2,3]
    assert len([x for x in dto['timeline'] if x['kind']=='OBSERVATION'])==4

def past_record(qdb,user,monkeypatch,*,text='その時は重かった。'):
    past=str(uuid4())
    qdb.query("insert into public.emotions values ($1,$2,(now()-interval '1 day') at time zone 'UTC',$3,'',array['仕事'],array['不安'],$4)",
      [past,user,'褒められたのに、嬉しくなかった。',json.dumps([dict(type='不安',strength='medium')])])
    legacy=EmlisThreadService();dto=run(legacy.start(user,past));dto=run(answer(legacy,user,dto,text))
    assert dto['body_state']=='REFINED',dto
    return past,dto

@pytest.mark.parametrize('tier',['free','plus','premium'])
def test_plan_sources_real_output_and_frame_boundary(qcase,qdb,monkeypatch,tier):
    user,parent,s=qcase;past_record(qdb,user,monkeypatch)
    qdb.query('update public.profiles set subscription_tier=$2 where id=$1',[user,tier])
    dto=run(s.start(user,parent));assert dto['state']=='AWAITING_ANSWER',dto
    assert bool(dto['interpretive_frames'])==(tier=='premium')
    dto=run(answer(s,user,dto,'その時は重かった。'))
    assert dto['body_state']=='REFINED',dto
    assert ('これまでの記録から' in dto['current_observation']['text'])==(tier!='free')
    assert dto['issued_count']==1 and dto['question_limit']==(3 if tier=='premium' else 1)

@pytest.mark.parametrize('status,text',[('CONFIRMED',None),('REJECTED',None),('REVISED','結果だけで、そこまでの苦労は見てもらえていないと思った。')])
def test_frame_feedback_is_owned_persisted_and_changes_next_observation(qcase,qdb,monkeypatch,status,text):
    user,parent,s=qcase;past_record(qdb,user,monkeypatch)
    dto=run(s.start(user,parent));frame=dto['interpretive_frames'][0]
    changed=run(s.frame_feedback(user,dto['thread_id'],frame_ref=frame['frame_ref'],status=status,
      correction_text=text,expected_revision=dto['revision'],idempotency_key='frame-edit'))
    assert changed['interpretive_frames'][0]['status']==status
    assert changed['issued_count']==1
    assert changed['current_observation'] is None and changed['body_state']=='CONTEXT_CHANGED'
    after=run(answer(s,user,changed,'その時は怖かった。'))
    assert after['body_state']=='REFINED',after
    if status=='REJECTED': assert after['interpretive_frames']==[]
    elif status=='REVISED': assert after['interpretive_frames'][0]['received_meaning']==text


def test_downgrade_answers_issued_round_but_never_issues_another(qcase,qdb):
    user,parent,s=qcase;one=run(s.start(user,parent));one=run(answer(s,user,one,'その時は重かった。'))
    two=run(cont(s,user,one,'continue-one'));qdb.query("update public.profiles set subscription_tier='free' where id=$1",[user])
    downgraded=run(s.get(user,parent));assert downgraded['pending_question']['question_id']==two['pending_question']['question_id']
    finished=run(answer(s,user,downgraded,'その時は怖かった。','answer-two'))
    assert finished['body_state']=='REFINED' and finished['state']=='COMPLETED',finished
    assert finished['issued_count']==2 and not finished['can_continue']


def test_upgrade_does_not_increase_started_budget(qcase,qdb):
    user,parent,s=qcase;qdb.query("update public.profiles set subscription_tier='free' where id=$1",[user])
    dto=run(s.start(user,parent));qdb.query("update public.profiles set subscription_tier='premium' where id=$1",[user])
    dto=run(answer(s,user,dto,'その時は重かった。'))
    assert dto['question_limit']==1 and dto['state']=='COMPLETED'


def test_unchanged_round_two_reuses_correct_body_and_old_replay_has_receipt(qcase):
    user,parent,s=qcase;initial=run(s.start(user,parent));one=run(answer(s,user,initial,'その時は重かった。'))
    two=run(cont(s,user,one,'continue-one'));done=run(answer(s,user,two,'分からない。','answer-two'))
    assert done['body_state']=='UNCHANGED' and not done['meaning_updated'],done
    assert done['current_observation']==one['current_observation']
    replay=run(answer(s,user,initial,'その時は重かった。'))
    assert replay['requested_operation']['question_id']==initial['pending_question']['question_id']
    assert replay['requested_operation']['attempt_id']!=done['attempt_id']
    assert len([e for e in done['timeline'] if e['kind']=='OBSERVATION'])==2


def test_deleted_history_removes_current_interpretation_and_does_not_block_stop(qcase,qdb,monkeypatch):
    user,parent,s=qcase;past,_=past_record(qdb,user,monkeypatch)
    dto=run(s.start(user,parent));dto=run(answer(s,user,dto,'その時は重かった。'))
    assert 'これまでの記録から' in dto['current_observation']['text']
    qdb.query('delete from public.emotions where id=$1',[past])
    dto=run(s.get(user,parent));assert dto['current_observation'] is None and not dto['can_continue']
    assert all('これまでの記録から' not in e['text'] for e in dto['timeline'])
    end=run(s.action(user,dto['thread_id'],action='stop',expected_revision=dto['revision'],idempotency_key='stop'))
    assert end['state']=='COMPLETED'

def test_actual_development_entry_selects_q3(qcase,monkeypatch):
    from emlis_ai_reply_service import render_emlis_ai_reply
    user,parent,s=qcase
    monkeypatch.setenv('COCOLON_ENV','development');monkeypatch.setenv('COCOLON_EMLIS_THREAD_DEVELOPMENT','true')
    reply=run(render_emlis_ai_reply(user_id=user,subscription_tier='free',current_input={'id':parent}))
    assert reply.comment_text==''
    dto=run(s.get(user,parent));assert dto['question_limit']==3 and dto['state']=='AWAITING_ANSWER'


def test_old_q2_saved_rows_survive_additive_migration(monkeypatch):
    db=Q3Database()
    try:
        user,parent=str(uuid4()),str(uuid4());db.query('insert into auth.users values ($1)',[user]);db.query("insert into public.profiles values ($1,'premium')",[user])
        db.query("insert into public.emotions values ($1,$2,now() at time zone 'UTC',$3,'',array['仕事'],array['不安'],$4)",[parent,user,'褒められたのに、嬉しくなかった。',json.dumps([dict(type='不安',strength='medium')])])
        monkeypatch.setattr(emlis_thread_store,'sb_post_rpc',db.rpc)
        old=EmlisThreadService();before=run(old.start(user,parent));before=run(answer(old,user,before,'その時は重かった。'))
        db.migrate();after=run(EmlisThreadService(runtime_profile=Q3_PROFILE).get(user,parent))
        assert after==before
        row=db.query('select data,started_question_limit from public.emlis_input_threads where original_emotion_id=$1',[parent])['rows'][0]
        assert row['data']['runtime_profile']=='q2.free.one_round.v1' and row['started_question_limit']==1
    finally:
        db.proc.stdin.close();db.proc.wait(timeout=10)


def test_pending_or_unresolved_history_never_falls_back_to_original(qcase,qdb,monkeypatch):
    user,parent,s=qcase;past=str(uuid4())
    qdb.query("insert into public.emotions values ($1,$2,(now()-interval '1 day') at time zone 'UTC',$3,'',array['仕事'],array['不安'],$4)",[past,user,'褒められたのに、嬉しくなかった。',json.dumps([dict(type='不安',strength='medium')])])
    old=EmlisThreadService();dto=run(old.start(user,past));failed=run(answer(old,user,dto,'はい。'));assert failed['body_state']=='ANSWER_UNREFLECTED'
    dto=run(s.start(user,parent));dto=run(answer(s,user,dto,'その時は重かった。'))
    assert dto['interpretive_frames']==[] and 'これまでの記録から' not in dto['current_observation']['text']


def test_history_change_during_generation_rejects_final_body(qcase,qdb,monkeypatch):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    from emlis_thread_store import ThreadStoreError
    user,parent,s=qcase;past,_=past_record(qdb,user,monkeypatch);dto=run(s.start(user,parent))
    class ChangedSource(MeaningExperienceEngine):
        def generate(self,request):
            result=super().generate(request)
            qdb.query('delete from public.emotions where id=$1',[past])
            return result
    s.engine=ChangedSource()
    with pytest.raises(ThreadStoreError) as raised:run(answer(s,user,dto,'その時は重かった。'))
    assert raised.value.status==409
    fresh=run(s.get(user,parent));assert fresh['answer_saved'] and fresh['current_observation'] is None
    assert len([e for e in fresh['timeline'] if e['kind']=='OBSERVATION'])==1


def test_frame_api_allowlist_and_foreign_owner(qcase,qdb,monkeypatch):
    from api_emlis_thread import ThreadResponse,ThreadFrameFeedbackBody
    from emlis_thread_store import ThreadStoreError
    from pydantic import ValidationError
    user,parent,s=qcase;past_record(qdb,user,monkeypatch);dto=run(s.start(user,parent));ThreadResponse.model_validate(dto)
    frame=dto['interpretive_frames'][0]
    with pytest.raises(ValidationError):
        ThreadFrameFeedbackBody(expected_revision=dto['revision'],idempotency_key='x',frame_ref=frame['frame_ref'],status='CONFIRMED',user_id=user)
    with pytest.raises(ThreadStoreError):
        run(s.frame_feedback(str(uuid4()),dto['thread_id'],frame_ref=frame['frame_ref'],status='REJECTED',correction_text=None,expected_revision=dto['revision'],idempotency_key='foreign'))


def test_database_rejects_wrong_round_and_duplicate_question_identity(qcase,qdb):
    import copy
    user,parent,s=qcase;dto=run(s.start(user,parent));snapshot=run(s.store.read(user,thread_id=dto['thread_id']))
    original=next(e for e in snapshot['events'] if e['kind']=='QUESTION')
    for round_index,question_id in [(3,'new-question'),(2,original['question_id'])]:
        event=copy.deepcopy(original);event.update(id=str(uuid4()),round_index=round_index,question_id=question_id)
        t=copy.deepcopy(snapshot['thread']);t['issued_count']=2
        response=run(qdb.rpc('emlis_thread_commit',dict(p_user_id=user,p_input_id=parent,p_thread_id=t['id'],p_expected_revision=t['revision'],p_source_snapshot=snapshot['original'],p_access_tier=snapshot['tier'],p_next=t,p_events=[event],p_finishing_attempt=None)))
        assert response.status_code==400 and response.json()['code'] in {'23514','23505'}
    assert run(s.get(user,parent))['issued_count']==1

def test_history_deletion_after_no_change_checkpoint_cannot_restore_old_body(qcase,qdb,monkeypatch):
    from emlis_thread_store import ThreadStoreError
    user,parent,s=qcase;past,_=past_record(qdb,user,monkeypatch);dto=run(s.start(user,parent));dto=run(answer(s,user,dto,'その時は重かった。'));dto=run(cont(s,user,dto,'continue'))
    commit=s.store.commit
    async def changed(*args,**kwargs):
        saved=await commit(*args,**kwargs)
        if any(e['kind']=='MEANING_UPDATE' and (e['payload'].get('answer_update') or {}).get('disposition')=='NO_MATERIAL_UPDATE' for e in args[3]):
            qdb.query('delete from public.emotions where id=$1',[past])
        return saved
    monkeypatch.setattr(s.store,'commit',changed)
    with pytest.raises(ThreadStoreError) as raised:run(answer(s,user,dto,'分からない。','answer-2'))
    assert raised.value.status==409
    fresh=run(s.get(user,parent));assert fresh['current_observation'] is None
    assert len([e for e in fresh['timeline'] if e['kind']=='ANSWER'])==2


def test_frame_source_change_between_reads_is_rejected(qcase,qdb,monkeypatch):
    from emlis_thread_store import ThreadStoreError
    user,parent,s=qcase;past,_=past_record(qdb,user,monkeypatch);dto=run(s.start(user,parent));frame=dto['interpretive_frames'][0]
    read=s.store.context;count=0
    async def changed(*args,**kwargs):
        nonlocal count
        count+=1
        if count==2:qdb.query('delete from public.emotions where id=$1',[past])
        return await read(*args,**kwargs)
    monkeypatch.setattr(s.store,'context',changed)
    with pytest.raises(ThreadStoreError) as raised:
        run(s.frame_feedback(user,dto['thread_id'],frame_ref=frame['frame_ref'],status='CONFIRMED',correction_text=None,expected_revision=dto['revision'],idempotency_key='confirm'))
    assert raised.value.status==409
    assert qdb.query('select * from public.emlis_frame_feedback where user_id=$1',[user])['rows']==[]


def test_history_line_inverse_resolves_both_owned_sources(qcase,qdb,monkeypatch):
    from dataclasses import replace
    from emlis_thread_service import _request
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning,build_updated_grounded_plan
    from cocolon_meaning_experience_engine.emlis_thread_history import history_line_plan
    from emlis_ai_grounded_sentence_surface import realize_emlis_history_line
    from emlis_ai_grounded_observation_gate import evaluate_emlis_history_line_inverse
    user,parent,s=qcase;past_record(qdb,user,monkeypatch);dto=run(s.start(user,parent));dto=run(answer(s,user,dto,'その時は重かった。'))
    snapshot=run(s._hydrate(user,run(s.store.read(user,input_id=parent))))
    p=prepare_emlis_meaning(_request(snapshot));line=history_line_plan(p,build_updated_grounded_plan(p));text=realize_emlis_history_line(line)
    assert evaluate_emlis_history_line_inverse(text,line,prepared=p)
    assert not evaluate_emlis_history_line_inverse(text,replace(line,past_evidence_refs=('foreign',)),prepared=p)
    assert not evaluate_emlis_history_line_inverse(text,replace(line,current_evidence_refs=line.past_evidence_refs),prepared=p)


def test_paid_failure_response_keeps_retry_available_without_extra_get(qcase,qdb,monkeypatch):
    user,parent,s=qcase;past_record(qdb,user,monkeypatch)
    dto=run(s.start(user,parent));failed=False
    async def fail_body_once(name,payload,**kwargs):
        nonlocal failed
        if not failed and payload.get('p_next',{}).get('latest_answer_event_id') and any(e['kind']=='OBSERVATION' for e in payload.get('p_events',[])):
            failed=True;return httpx.Response(503,json={'code':'57P03'})
        return await qdb.rpc(name,payload,**kwargs)
    monkeypatch.setattr(emlis_thread_store,'sb_post_rpc',fail_body_once)
    failed_dto=run(answer(s,user,dto,'その時は重かった。'))
    assert failed_dto['can_retry'] and failed_dto['state']=='RESPONSE_FAILED'
    assert failed_dto==run(s.get(user,parent))
    recovered=run(s.action(user,dto['thread_id'],action='retry_response',expected_revision=failed_dto['revision'],idempotency_key='retry-paid',operation_id=failed_dto['operation_id']))
    assert recovered['body_state']=='REFINED' and 'これまでの記録から' in recovered['current_observation']['text']


def test_start_conflict_returns_paid_current_view(qcase,qdb,monkeypatch):
    from emlis_thread_store import ThreadStoreError
    user,parent,s=qcase;past_record(qdb,user,monkeypatch)
    original_commit=s.store.commit
    expected=None
    async def other_start(user_id,snapshot,next_state,events,**kwargs):
        nonlocal expected
        monkeypatch.setattr(s.store,'commit',original_commit)
        expected=await EmlisThreadService(runtime_profile=Q3_PROFILE).start(user,parent)
        raise ThreadStoreError('revision_conflict',409)
    monkeypatch.setattr(s.store,'commit',other_start)
    actual=run(s.start(user,parent));assert actual==expected
    assert actual['interpretive_frames'] and actual['current_observation']
