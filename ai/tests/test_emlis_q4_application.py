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

def test_active_requires_separate_release_approval(monkeypatch):
    from emlis_thread_config import application_mode,writes_enabled
    monkeypatch.setenv('COCOLON_EMLIS_THREAD_MODE','active');monkeypatch.delenv('COCOLON_EMLIS_THREAD_RELEASE_APPROVED',raising=False)
    assert application_mode()=='read_only' and not writes_enabled()


def test_read_only_authenticated_api_exposes_saved_dto_and_rejects_all_writes(qcase,monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from api_emlis_thread import register_emlis_thread_routes
    import api_account_visibility
    user,parent,_=qcase;s=active(monkeypatch);before=run(s.start(user,parent))
    async def resolve(token):return user
    monkeypatch.setattr(api_account_visibility,'_resolve_user_id_from_token',resolve)
    monkeypatch.setenv('COCOLON_EMLIS_THREAD_MODE','read_only')
    app=FastAPI();register_emlis_thread_routes(app)
    with TestClient(app) as client:
        url=f'/emlis/threads/by-input/{parent}';headers={'Authorization':'Bearer synthetic-owner-token'}
        assert client.get(url).status_code==401
        got=client.get(url,headers=headers);assert got.status_code==200
        assert got.json()['timeline']==before['timeline'] and not got.json()['can_write']
        assert got.headers['cache-control']=='private, no-store'
        base=dict(expected_revision=before['revision'],idempotency_key='blocked')
        for suffix,payload in [('answers',dict(question_id=before['pending_question']['question_id'],answer_text='回答')),('actions',dict(action='skip')),('frames',dict(frame_ref='frame',status='REJECTED'))]:
            denied=client.post(f"/emlis/threads/{before['thread_id']}/{suffix}",headers=headers,json={**base,**payload})
            assert denied.status_code==503 and denied.json()['detail']=='application_paused'
        assert client.get(url,headers=headers).json()['revision']==before['revision']


def test_cancel_after_pause_closes_attempt_and_preserves_meaning(qcase,monkeypatch):
    import asyncio
    user,parent,_=qcase;s=active(monkeypatch);dto=run(s.start(user,parent))
    original=s.engine.generate
    def cancel(req):
        monkeypatch.setenv('COCOLON_EMLIS_THREAD_MODE','read_only');raise asyncio.CancelledError()
    monkeypatch.setattr(s.engine,'generate',cancel)
    with pytest.raises(asyncio.CancelledError):run(answer(s,user,dto,'その時は重かった。'))
    failed=run(s.get(user,parent));assert failed['meaning_updated'] and failed['failure_code']=='worker_interrupted'
    assert failed['processing_deadline_at'] is None and not failed['can_retry']
    monkeypatch.setattr(s.engine,'generate',original);monkeypatch.setenv('COCOLON_EMLIS_THREAD_MODE','active')
    assert run(s.get(user,parent))['can_retry']

@pytest.mark.parametrize('memo',['褒められたのに、嬉しくなかった。','誘われたのに、悲しかった。'])
def test_initial_event_nominal_keeps_both_source_endpoints_and_inverse(memo):
    from test_cmee_emlis_q1_thread import initial
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning,build_updated_grounded_plan
    from cocolon_meaning_experience_engine.emlis_thread_surface import realize_emlis_thread_body
    from cocolon_meaning_experience_engine.emlis_thread_projection import project_thread_meaning
    import emlis_ai_grounded_sentence_surface as surface
    from emlis_ai_grounded_observation_gate import evaluate_grounded_surface_body_inverse
    prepared=prepare_emlis_meaning(initial(memo));checkpoint=prepared.checkpoint;plan=build_updated_grounded_plan(prepared)
    result=realize_emlis_thread_body(prepared);assert prepared.checkpoint==checkpoint
    event,reaction=memo.rstrip('。').split('のに、')
    assert f'{event}ことと{reaction}こと' in result.artifact.reception
    assert '今ここに置かれた言葉' not in result.artifact.reception
    resolver=prepared.thread.resolver();projection=project_thread_meaning(prepared,plan)
    sentence=surface.build_grounded_sentence_plan(plan,resolver,recovery_stage='full')
    def inverse(text):return evaluate_grounded_surface_body_inverse(body=text.encode(),plan=plan,sentence_plan=sentence,resolver=resolver,selected_subjective_input=projection.selected_reception).passed
    body=result.artifact.text;assert inverse(body)
    for old,new in [(event+'こと',''),(reaction+'こと',''),('その違いも含めて',''),(event+'こと',f'「{event}」こと')]:
        changed=body.replace(old,new);assert changed!=body and not inverse(changed)


@pytest.mark.parametrize('answer_text,nominal,mutations',[
    ('次も同じ成果を求められるようで、重かった。','次も同じ成果を求められるようだという、その時の重さ',
     [('ようだという','という'),('ようだという','ための'),('重さ','苦しさ'),('次も',''),('同じ','')]),
    ('結果だけで、そこまでの苦労は見てもらえていないと思った。','結果だけで、そこまでの苦労は見てもらえていないという、その時の思い',
     [('見てもらえていない','見てもらえている'),('だけ',''),('そこまでの',''),('思い','事実')]),
    ('その時は重かった。','その時の重さ',[('重さ','軽さ')]),
    ('その時は寂しかった。','その時の寂しさ',[('寂しさ','嬉しさ')]),
])
def test_answer_nominal_preserves_source_and_rejects_semantic_mutations(answer_text,nominal,mutations):
    from test_cmee_emlis_q1_thread import answered
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning,build_updated_grounded_plan
    from cocolon_meaning_experience_engine.emlis_thread_surface import realize_emlis_thread_body
    from cocolon_meaning_experience_engine.emlis_thread_projection import project_thread_meaning
    import emlis_ai_grounded_sentence_surface as surface
    from emlis_ai_grounded_observation_gate import evaluate_grounded_surface_body_inverse, _semantic_subcheck_reasons
    prepared=prepare_emlis_meaning(answered(answer_text));checkpoint=prepared.checkpoint
    plan=build_updated_grounded_plan(prepared);resolver=prepared.thread.resolver()
    result=realize_emlis_thread_body(prepared);assert prepared.checkpoint==checkpoint
    assert nominal in result.artifact.reception
    projection=project_thread_meaning(prepared,plan)
    sentence=surface.build_grounded_sentence_plan(plan,resolver,recovery_stage='full')
    def inverse(text):return evaluate_grounded_surface_body_inverse(body=text.encode(),plan=plan,sentence_plan=sentence,resolver=resolver,selected_subjective_input=projection.selected_reception).passed
    body=result.artifact.text;assert inverse(body)
    variants=[nominal.replace(a,b) for a,b in mutations]
    variants += [nominal.replace('その時の',''),nominal.replace('その時の','今の'),nominal*2,
                 '「'+nominal+'」','『'+nominal+'』']
    for changed in variants:
        assert changed!=nominal and not inverse(body.replace(nominal,changed))
    # Only the one exact source-owned nominal may be re-inflected for
    # sensation checking; an unrelated extra burden remains ungrounded.
    from types import SimpleNamespace
    extra=body+'\n重さもあります。'
    semantic,_,_=_semantic_subcheck_reasons(plan=plan,sentence_plan=sentence,
        surface_result=SimpleNamespace(text=extra,lines=()),resolver=resolver)
    assert 'ungrounded_sensation_family_added' in semantic


@pytest.mark.parametrize('text',['私は重かった','少し重かった','まだ重かった','重くなかった','行きたかった','悪かった'])
def test_answer_nominal_does_not_strip_topic_degree_negation_or_other_predicate(text):
    from test_cmee_emlis_q1_thread import answered
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning,build_updated_grounded_plan
    from emlis_ai_grounded_human_reception import source_grounded_thread_answer_nominal
    prepared=prepare_emlis_meaning(answered(text+'。'));plan=build_updated_grounded_plan(prepared)
    index={n.nucleus_id:n for n in plan.nuclei}
    assert all(source_grounded_thread_answer_nominal(m,plan,index,prepared.thread.resolver()) is None
               for m in plan.response_plan.human_reception_plan.moves)


def test_answer_nominal_requires_original_source_scope_owner_and_time():
    from test_cmee_emlis_q1_thread import answered
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning,build_updated_grounded_plan
    from emlis_ai_grounded_human_reception import source_grounded_thread_answer_nominal
    prepared=prepare_emlis_meaning(answered('その時は重かった。'));plan=build_updated_grounded_plan(prepared)
    move=plan.response_plan.human_reception_plan.moves[0];index={n.nucleus_id:n for n in plan.nuclei};n=index[move.target_nucleus_ids[0]]
    assert source_grounded_thread_answer_nominal(move,plan,index,prepared.thread.resolver()) is not None
    changes=[replace(n,allowed_claim_scope='memo_only'),replace(n,source_fields=('memo',)),
             replace(n,semantic_frame=replace(n.semantic_frame,actor='other_person')),
             replace(n,semantic_frame=replace(n.semantic_frame,polarity='positive'))]
    for code in ['thread_time:unknown','aspect:completed','source_fragment_scalar_range:4:7']:
        prefix=code.split(':',1)[0]+':'
        changes.append(replace(n,semantic_frame=replace(n.semantic_frame,
            attribute_codes=tuple(c for c in n.semantic_frame.attribute_codes if not c.startswith(prefix))+(code,))))
    for changed in changes:
        altered=replace(plan,nuclei=tuple(changed if x.nucleus_id==n.nucleus_id else x for x in plan.nuclei))
        assert source_grounded_thread_answer_nominal(move,altered,{x.nucleus_id:x for x in altered.nuclei},prepared.thread.resolver()) is None


@pytest.mark.parametrize('grammar',['answer-slot:0:PAST_FEELING:answer_time',
                                  'answer-slot:0:PAST_FEELING:prior_answer_time',
                                  'answer-slot:0:BELIEF:original_occasion'])
def test_answer_nominal_ir_cannot_change_answer_time_or_predicate(grammar):
    from test_cmee_emlis_q1_thread import answered
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning,build_updated_grounded_plan
    from cocolon_meaning_experience_engine.emlis_thread_surface import _bind_expression
    from cocolon_meaning_experience_engine.emlis_thread_projection import project_thread_meaning
    import emlis_ai_grounded_human_reception as hr
    import emlis_ai_grounded_sentence_surface as surface
    prepared=prepare_emlis_meaning(answered('その時は重かった。'));plan=build_updated_grounded_plan(prepared)
    projection=project_thread_meaning(prepared,plan);resolver=prepared.thread.resolver()
    reception=plan.response_plan.human_reception_plan;assert len(reception.moves)==1
    expression=_bind_expression(plan,resolver,projection,reception.moves[0],'FINITE')
    changed=hr.identify_source_grounded_reception_expression(replace(expression,
        expression_ref='',nominalization_plan=(expression.nominalization_plan[0],grammar)))
    sentence=surface.build_grounded_sentence_plan(plan,resolver,recovery_stage='full')
    clauses=next(line.reception_clause_plans for line in sentence.lines if line.binding.line_role=='human_follow')
    with pytest.raises(hr.GroundedHumanReceptionSurfaceError):
        hr.realize_source_grounded_human_reception(reception,(changed,),{n.nucleus_id:n for n in plan.nuclei},resolver,
            plan=plan,recovery_stage='full',clause_plans=clauses,selected_subjective_input=projection.selected_reception)


@pytest.mark.parametrize('duplicate',[False,True])
def test_sensation_check_handles_absent_reception_and_duplicate_nominal_ranges(duplicate):
    from types import SimpleNamespace
    from test_cmee_emlis_q1_thread import answered
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning,build_updated_grounded_plan
    from cocolon_meaning_experience_engine.emlis_thread_surface import realize_emlis_thread_body
    from emlis_ai_grounded_observation_gate import _semantic_subcheck_reasons
    import emlis_ai_grounded_sentence_surface as surface
    prepared=prepare_emlis_meaning(answered('その時は重かった。'));plan=build_updated_grounded_plan(prepared)
    body=realize_emlis_thread_body(prepared).artifact.text
    # The extra token immediately follows the one eligible nominal so a
    # second replacement at the original byte range would wrongly erase it.
    body=body.replace('その時の重さ','その時の重さ重さ')
    reception=plan.response_plan.human_reception_plan
    altered=replace(plan,response_plan=replace(plan.response_plan,human_reception_plan=
        replace(reception,moves=reception.moves*2) if duplicate else None))
    reasons,_,_=_semantic_subcheck_reasons(plan=altered,
        sentence_plan=surface.build_grounded_sentence_plan(plan,prepared.thread.resolver(),recovery_stage='full'),
        surface_result=SimpleNamespace(text=body,lines=()),resolver=prepared.thread.resolver())
    assert 'ungrounded_sensation_family_added' in reasons


@pytest.mark.parametrize('answer_text,when', [
    ('次も同じ成果を求められるようで、重かった。', 'その時'),
    ('結果だけで、そこまでの苦労は見てもらえていないと思った。', 'その時'),
    ('今は嬉しい。', '回答した時点'),
])
def test_answer_observation_binds_one_event_without_repetition(answer_text, when):
    from test_cmee_emlis_q1_thread import answered
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning, build_updated_grounded_plan
    from cocolon_meaning_experience_engine.emlis_thread_surface import realize_emlis_thread_body
    from cocolon_meaning_experience_engine.emlis_thread_projection import project_thread_meaning
    import emlis_ai_grounded_sentence_surface as surface
    from emlis_ai_grounded_observation_gate import evaluate_grounded_surface_body_inverse
    prepared = prepare_emlis_meaning(answered(answer_text)); checkpoint = prepared.checkpoint
    plan = build_updated_grounded_plan(prepared); resolver = prepared.thread.resolver()
    result = realize_emlis_thread_body(prepared)
    assert prepared.checkpoint == checkpoint
    body = result.artifact.text
    assert result.artifact.observation.count('「褒められた」') == 1
    assert '「嬉しくなかった」という反応' in result.artifact.observation
    assert f'その出来事に対する{when}の受け止め' in result.artifact.observation
    projection = project_thread_meaning(prepared, plan)
    sentence = surface.build_grounded_sentence_plan(plan, resolver, recovery_stage='full')
    def inverse(text):
        return evaluate_grounded_surface_body_inverse(body=text.encode(), plan=plan,
            sentence_plan=sentence, resolver=resolver, selected_subjective_input=projection.selected_reception).passed
    assert inverse(body)
    for before, after in [
        ('その出来事に対する', 'その反応に対する'),
        ('その出来事に対する', 'その出来事が原因の'),
        ('という反応があり、', 'という反応はなく、'),
        ('という反応があり、', 'という反応があり。'),
        ('「褒められた」', '「誘われた」'),
        ('「嬉しくなかった」', '「嬉しかった」'),
        (f'に対する{when}', 'に対する先の回答時点'),
    ]:
        changed = body.replace(before, after)
        assert changed != body and not inverse(changed)
    crossed = body.replace('「褒められた」', '「TEMP」').replace('「嬉しくなかった」', '「褒められた」').replace('「TEMP」', '「嬉しくなかった」')
    assert not inverse(crossed)


def test_answer_observation_does_not_group_ambiguous_or_hedged_event():
    from test_cmee_emlis_q1_thread import answered
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning, build_updated_grounded_plan
    import emlis_ai_grounded_sentence_surface as surface
    prepared = prepare_emlis_meaning(answered('その時は重かった。'))
    plan = build_updated_grounded_plan(prepared); resolver = prepared.thread.resolver()
    index = {n.nucleus_id:n for n in plan.nuclei}; relations = {r.relation_id:r for r in plan.relations}
    sentence = surface.build_grounded_sentence_plan(plan, resolver, recovery_stage='full')
    binding = next(l.binding for l in sentence.lines if l.binding.relation_ids)
    groups, consumed = surface._thread_contrast_answer_groups(binding,index,relations,resolver)
    assert len(groups) == 1 and len(consumed) == 2
    hedged = replace(binding,functional_atom_ids=(*binding.functional_atom_ids,'scope_hedge'))
    assert surface._thread_contrast_answer_groups(hedged,index,relations,resolver) == ((),frozenset())
    duplicate = replace(index['nucleus:s1:event'],nucleus_id='duplicate-event')
    assert surface._thread_contrast_answer_groups(binding,{**index,duplicate.nucleus_id:duplicate},relations,resolver) == ((),frozenset())
    # Multiple ABOUT_TARGETs require explicit targets, even if one binding
    # could otherwise make the event sound like a unique antecedent.
    about = next(r for r in plan.relations if r.type=='evaluation_about_event')
    other = replace(about,relation_id='duplicate-about')
    altered = replace(binding,relation_ids=(*binding.relation_ids,other.relation_id))
    assert surface._thread_contrast_answer_groups(altered,index,{**relations,other.relation_id:other},resolver) == ((),frozenset())
    assert surface._thread_contrast_answer_groups(binding,index,{**relations,other.relation_id:other},resolver) == ((),frozenset())
