"""Approved four-topic model-profile connection, synthetic CPU only.

The fixture specifies source roles and expected prose independently of production
recognizers. SQL cases exercise existing isolated PostgreSQL/WASM RPCs. No model,
GPU, real account or production DB is involved; no product-quality acceptance.
"""
import asyncio
import copy
from dataclasses import replace
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from emlis_ai_current_input_bundle import build_emlis_current_input_bundle
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.contracts import GenerationRequest, EngineStatus
from cocolon_meaning_experience_engine.source_kernel import freeze_text_source
from cocolon_meaning_experience_engine.emlis_thread_contracts import EmlisThreadInputV1, EmlisQuestionControlV1, SupplementalAnswerSource
from cocolon_meaning_experience_engine.emlis_semantic_admission import MODEL_PROFILE, MODEL_CANDIDATE_SCHEMA, SemanticInput, SemanticNotAdopted, prepare_model_snapshot, restore_model_snapshot, _model_semantic_ref
from cocolon_meaning_experience_engine.preparation import prepare_emlis, receive_candidate, QUOTE_CANDIDATE_SCHEMA
from cocolon_meaning_experience_engine.model_candidate_source import build_model_messages
from emlis_ai_grounded_observation_gate import evaluate_emlis_model_surface_inverse
from emlis_thread_service import EmlisThreadService
from test_emlis_q2_application import case, db, run, answer

FIXTURE = json.loads((Path(__file__).parent/'fixtures/cmee_emlis_sixrow_v3.json').read_text())['topics']
STATES = [('book',False),('book',True),('shop',False),('shop',True),('repot',False),('knit',False)]


def canonical(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))


def request(topic):
    raw=copy.deepcopy(FIXTURE[topic]['original'])
    req=GenerationRequest('sixrow-'+topic,build_emlis_current_input_bundle(raw),raw['id'])
    source=freeze_text_source(req)
    return replace(req,emlis_thread=EmlisThreadInputV1('sixrow-thread-'+topic,source.envelope.envelope_id))


def fixture_packet(req, topic, prior=None):
    """Rebind hand-authored fixture quotes; no production grammar/parser calls."""
    item=FIXTURE[topic]; after=bool(req.emlis_thread.answers)
    stages=[item['initial']] + ([item['after']] if after else [])
    raw=req.current_input_bundle.raw_current_input
    sid=prepare_emlis(req).payload()['sources'][0]['source_id']
    aid=req.emlis_thread.answers[0].answer_id if after else None
    fields={sid:raw}
    if after: fields[aid]={'answer_text_private':req.emlis_thread.answers[0].answer_text_private}
    ev=[]
    def index(spec, quote=None):
        source=aid if spec['field']=='answer_text_private' else sid
        text=fields[source][spec['field']]; q=quote or spec['quote']; start=text.index(q)
        e=dict(source_id=source,field_path=spec['field'],start=start,end=start+len(q),quote=q)
        if e not in ev: ev.append(e)
        return ev.index(e)
    roles=[r for s in stages for r in s['roles']]; links=[r for s in stages for r in s['links']]
    # Keep the original evidence prefix, so unchanged adopted rows retain their indexes too.
    for stage in stages:
        for r in stage['roles']:
            index(r)
            if r['polarity_quote']: index(r,r['polarity_quote'])
            if r['time_quote']: index(r,r['time_quote'])
        for r in stage['links']: index(r)
    claims=[]
    for r in roles:
        i=index(r); n=r['name']
        claims.append(dict(claim_id=n,kind=r['kind'],text=r['quote'],
            subject=dict(binding='OMITTED',source_entity=None,evidence_indexes=[]),
            predicate=dict(surface=r['quote'],arguments=[]),
            polarity=dict(value=r['polarity'],scope_refs=[n],evidence_indexes=[index(r,r['polarity_quote'])]),
            modality=dict(value=r['modality'],evidence_indexes=[i]),
            about_time=dict(kind=r['about'],expression=r['time_quote'],anchor_source_id=ev[i]['source_id'],evidence_indexes=[index(r,r['time_quote'])]),
            qualifiers=[],evidence_indexes=[i]))
    relations=[dict(relation_id=r['name'],type=r['kind'],from_claim_id=r['left'],to_claim_id=r['right'],polarity='AFFIRMED',scope_refs=[r['name']],qualifiers=[],evidence_indexes=[index(r)]) for r in links]
    byname={r['name']:r for r in roles}; target=item['target']; unknowns=[]; updates=[]; q=None
    if target and not after:
        unknowns=[dict(unknown_id='missing_explanation',kind='NOT_STATED',target_claim_refs=[target],description=item['gap_description'],evidence_indexes=[index(byname[target])])]
        q=dict(text=item['question'],target_unknown_ref='missing_explanation',focus=item['focus'],claim_refs=[target])
    if topic=='knit':
        unknowns=[dict(unknown_id='unknown_connection',kind='PERSON_STATED',target_claim_refs=['burden','sadness'],description=byname['stated_unknown']['quote'],evidence_indexes=[index(byname[n]) for n in ('stated_unknown','burden','sadness')])]
    if after:
        for r in item['after']['roles']:
            attached=[l for l in item['after']['links'] if l['right']==r['name']]
            updates.append(dict(operation='ADD',target_kind='UNKNOWN',target_ref='missing_explanation',replacement_refs=[r['name']]+[l['name'] for l in attached],evidence_indexes=list(dict.fromkeys([index(r)]+[index(l) for l in attached])),prior_snapshot_ref=prior.checkpoint.snapshot_ref))
        explained=next(l for l in item['after']['links'] if l['name']=='answer_explains_target')
        updates.append(dict(operation='INVALIDATE_GAP',target_kind='UNKNOWN',target_ref='missing_explanation',replacement_refs=[],evidence_indexes=[index(explained)],prior_snapshot_ref=prior.checkpoint.snapshot_ref))
    stage=stages[-1]; surface={k:stage['surface'][k] for k in ('observation','reception','update_note')}
    surface['bindings']=copy.deepcopy(stage['bindings'])
    if after: surface['bindings'][-1]['update_refs']=list(range(len(updates)))
    return dict(candidate=dict(schema_version=MODEL_CANDIDATE_SCHEMA,core='emlis',claims=claims,relations=relations,unknowns=unknowns,conflicts=[],updates=updates,surface_proposal=surface,question_proposal=q),evidence=ev)


def wire(packet):
    return dict(schema_version=QUOTE_CANDIDATE_SCHEMA,candidate=copy.deepcopy(packet['candidate']),evidence_quotes=[{k:e[k] for k in ('source_id','field_path','quote')} for e in packet['evidence']])


def semantic(req,packet,prior=None):
    material=prepare_emlis(req)
    receipt=receive_candidate(material,request_id=material.request_id,raw_output=canonical(wire(packet)),finish_reason='stop',provider='independent-synthetic-fixture',model='synthetic-not-4B')
    assert receipt.status=='CANDIDATE_UNREVIEWED',receipt.status
    assert json.loads(receipt.candidate_json)==packet
    return SemanticInput('FRESH_CANDIDATE',receipt,prior_snapshot_json=prior.semantic_snapshot if prior else None,semantic_profile=MODEL_PROFILE)


def outcome(req,prepared):
    resumed=replace(req,emlis_thread=replace(req.emlis_thread,prepared_meaning_checkpoint_ref=prepared.checkpoint.checkpoint_id))
    return MeaningExperienceEngine().generate(resumed,semantic_input=SemanticInput('RESUME_ADOPTED',snapshot_json=prepared.semantic_snapshot,semantic_profile=MODEL_PROFILE))


def state(topic,after=False):
    req=request(topic); p=prepare_model_snapshot(req,semantic(req,fixture_packet(req,topic))); out=outcome(req,p)
    if not after: return req,p,out,None
    assert out.question is not None,out.reason_codes
    q=out.question
    a=SupplementalAnswerSource('sixrow-answer-'+topic,req.emlis_thread.thread_id,q.question_id,1,req.emlis_thread.original_source_ref,FIXTURE[topic]['after']['answer'],'2026-10-26T01:00:00Z')
    req=replace(req,emlis_thread=replace(req.emlis_thread,answers=(a,),current_round=1,prepared_meaning_checkpoint_ref=None,question_control_context=EmlisQuestionControlV1(q,(q.decision.target_ref,),1)))
    prepared=prepare_model_snapshot(req,semantic(req,fixture_packet(req,topic,p),p))
    return req,prepared,outcome(req,prepared),p


@pytest.mark.parametrize('topic,after',STATES)
def test_six_states_actual_quote_meaning_body_question_and_canonical_replay(topic,after):
    req,p,out,prior=state(topic,after); item=FIXTURE[topic]; stage=item['after' if after else 'initial']; snap=json.loads(p.semantic_snapshot)
    assert snap['admission_version']==snap['adapter_version']=='3'
    assert snap['native_bindings']['family']==item['family']
    assert len(snap['packet']['candidate']['claims'])==len(item['initial']['roles'])+(len(stage['roles']) if after else 0)
    assert snap['native_bindings']['preserved_selections']=={k:item['original'].get(k) for k in ('category','emotions','emotion_details','is_secret')}
    assert out.artifact is not None,out.reason_codes
    for key in ('observation','reception','update_note'): assert getattr(out.artifact,key)==stage['surface'][key]
    assert out.body_state==('REFINED' if after else 'PRE_QUESTION' if item['target'] else 'FINAL')
    assert out.status==(EngineStatus.QUESTION_PENDING if item['target'] and not after else EngineStatus.GENERATED)
    assert (out.question.prompt_private if out.question else None)==(item['question'] if not after else None)
    assert restore_model_snapshot(req,p.semantic_snapshot)==p
    resumed=replace(req,emlis_thread=replace(req.emlis_thread,prepared_meaning_checkpoint_ref=p.checkpoint.checkpoint_id))
    assert outcome(resumed,p)==out
    if after:
        old=json.loads(prior.meaning_json)['candidate']; current=json.loads(p.meaning_json)['candidate']
        assert current['claims'][:len(old['claims'])]==old['claims']
        assert current['relations'][:len(old['relations'])]==old['relations']
        assert p.checkpoint.inactive_claim_refs==('missing_explanation',)
        assert all(not u.superseded_claim_refs for u in p.checkpoint.answer_update.updates[:-1])
        assert [u.operation for u in p.checkpoint.answer_update.updates]==['ADD']*len(stage['roles'])+['INVALIDATE_GAP']
        assert len(p.checkpoint.answer_update.updates)==len(stage['roles'])+1
    if topic=='repot':
        assert [(x['text'],x['written_role']) for x in snap['native_bindings']['case_arguments']]==[('植え替えの手順','を'),('叔父','に')]
    if topic=='knit':
        u=json.loads(p.meaning_json)['candidate']['unknowns'][0]
        assert u['kind']=='PERSON_STATED' and u['target_claim_refs']==['burden','sadness']
        assert not snap['native_bindings']['written_links']


@pytest.mark.parametrize('topic', ['book','shop'])
def test_explanations_keep_per_claim_time_polarity_and_perception(topic):
    req,p,_,_=state(topic,True); c={r['claim_id']:r for r in json.loads(p.meaning_json)['candidate']['claims']}
    if topic=='book':
        assert c['self_statement']['kind']=='REPORTED_STATEMENT'
        assert c['no_contact']['polarity']['value']=='NEGATED'
        assert c['returned']['polarity']['value']=='AFFIRMED'
        assert c['counterfactual']['modality']['value']=='COUNTERFACTUAL_APPRAISAL'
        assert [c[n]['about_time']['kind'] for n in ('remaining_concern','counterfactual','continuing_concern')]==['WRITTEN_PRESENT','ANSWER_TIME','ANSWER_TIME']
    else:
        assert c['no_joint_preparation']['polarity']['value']==c['no_promise']['polarity']['value']=='NEGATED'
        assert c['no_joint_preparation']['polarity']['evidence_indexes']==c['no_promise']['polarity']['evidence_indexes']
        assert c['perceived_realization']['modality']['value']==c['felt_distance']['modality']['value']=='PERSON_PERCEPTION'
        assert c['answer_joy']['about_time']['kind']=='WRITTEN_PRESENT_IN_PAST_CONTEXT'
    for update,role in zip(p.checkpoint.answer_update.updates,FIXTURE[topic]['after']['roles']):
        assert update.temporal_binding.about_time==role['about']


@pytest.mark.parametrize('topic,after',STATES)
def test_messages_are_stage_specific_preserve_full_fields_and_correct_unknown_shape(topic,after):
    req,p,_,prior=state(topic,after)
    messages=build_model_messages(req,prior.semantic_snapshot if prior else None,candidate_format=QUOTE_CANDIDATE_SCHEMA)
    payload=json.loads(messages[1]['content']); spec=payload['output_spec']; shape=spec['shape']['candidate']
    fields=payload['material']['sources'][0]['text_fields']; raw=req.current_input_bundle.raw_current_input
    assert fields['memo']==raw['memo'] and fields['memo_action']==raw['memo_action']
    assert spec['role_order']==[r['name'] for r in FIXTURE[topic]['initial']['roles']]+([r['name'] for r in FIXTURE[topic]['after']['roles']] if after else [])
    assert '$object' not in canonical(shape['unknowns']) and '$joy' not in canonical(shape['unknowns'])
    if topic=='knit': assert shape['unknowns'][0]['kind']=='PERSON_STATED' and len(shape['unknowns'][0]['evidence_indexes'])==3
    elif not after and FIXTURE[topic]['target']:
        assert len(shape['unknowns'][0]['target_claim_refs'])==1
        assert shape['question_proposal']['focus']==FIXTURE[topic]['focus']
    else: assert shape['unknowns']==[] and shape['question_proposal'] is None


@pytest.mark.parametrize('topic,after',STATES)
@pytest.mark.parametrize('axis', ['subject','polarity','time','modality','predicate','claim_drop','foreign_quote'])
def test_valid_quotes_do_not_license_changed_semantic_axes(topic,after,axis):
    req,p,_,prior=state(topic,after); packet=fixture_packet(req,topic,prior)
    claim=packet['candidate']['claims'][-1]
    if axis=='subject': claim['subject']['binding']='SELF'
    elif axis=='polarity': claim['polarity']['value']='NEGATED' if claim['polarity']['value']=='AFFIRMED' else 'AFFIRMED'
    elif axis=='time': claim['about_time']['kind']='ORIGINAL_OCCASION'
    elif axis=='modality': claim['modality']['value']='OBJECTIVE_REALITY'
    elif axis=='predicate': claim['predicate']['surface']='別の意味'
    elif axis=='claim_drop': packet['candidate']['claims'].pop()
    else: packet['evidence'][0]['source_id']='foreign'
    if axis=='foreign_quote':
        material=prepare_emlis(req); receipt=receive_candidate(material,request_id=material.request_id,raw_output=canonical(wire(packet)),finish_reason='stop')
        assert receipt.status=='INVALID_EVIDENCE'
    else:
        with pytest.raises(SemanticNotAdopted): prepare_model_snapshot(req,semantic(req,packet,prior))


@pytest.mark.parametrize('topic,after', [x for x in STATES if x[0]!='knit'])
@pytest.mark.parametrize('mutation',['reverse','cause','drop'])
def test_written_relation_direction_and_noncausal_scope(topic,after,mutation):
    req,p,_,prior=state(topic,after); packet=fixture_packet(req,topic,prior); row=packet['candidate']['relations'][-1]
    if mutation=='reverse': row['from_claim_id'],row['to_claim_id']=row['to_claim_id'],row['from_claim_id']
    elif mutation=='cause': row['type']='OBJECTIVE_CAUSE'
    else: packet['candidate']['relations'].pop()
    with pytest.raises(SemanticNotAdopted): prepare_model_snapshot(req,semantic(req,packet,prior))


@pytest.mark.parametrize('topic,after',STATES)
def test_full_source_extra_text_and_forged_version_cannot_select_a_parser(topic,after):
    req,p,_,prior=state(topic,after)
    snap=json.loads(p.semantic_snapshot);snap['admission_version']=snap['adapter_version']='1';snap['snapshot_ref']=_model_semantic_ref(snap)
    with pytest.raises(SemanticNotAdopted,match='snapshot_binding_invalid'): restore_model_snapshot(req,canonical(snap))
    if after:
        a=replace(req.emlis_thread.answers[0],answer_text_private=req.emlis_thread.answers[0].answer_text_private+'本当は別の意味です。')
        changed=replace(req,emlis_thread=replace(req.emlis_thread,answers=(a,)))
    else:
        raw=dict(req.current_input_bundle.raw_current_input); raw['memo']+='本当は別の意味です。'
        changed=replace(req,current_input_bundle=build_emlis_current_input_bundle(raw),emlis_thread=None)
        original=freeze_text_source(changed)
        changed=replace(changed,emlis_thread=EmlisThreadInputV1(req.emlis_thread.thread_id,original.envelope.envelope_id))
    with pytest.raises(SemanticNotAdopted): prepare_model_snapshot(changed,semantic(changed,fixture_packet(changed,topic,prior),prior))


@pytest.mark.parametrize('topic,after,section,text',[
    ('book',False,'observation','本を返すのが遅れて友人に謝り、「大丈夫」と言われても、まだ気がかりが残っているのですね。'),
    ('book',False,'observation','友人が本の返却に遅れて、あなたに謝ったのですね。'),
    ('book',True,'observation','遅くなると分かった時に連絡したので、今は気にならないのですね。'),
    ('book',True,'reception','あの時に連絡したことが、今も気になっていたのですね。'),
    ('shop',False,'observation','友人に実際に置いていかれたのですね。'),
    ('shop',True,'observation','二人で話していた未来が、あなたの方で現実になっていたのですね。'),
    ('shop',True,'reception','一緒に準備して約束したのに、友人に裏切られたのですね。'),
    ('shop',True,'observation','あの頃から友人があなたと離れたので、寂しいのですね。'),
    ('repot',False,'observation','叔父に植え替えの手順を説明して、最後まで聞いてもらったのですね。'),
    ('repot',False,'reception','最後まで説明を聞いた後で、安心したのですね。'),
    ('knit',False,'reception','うまく結び付けられなくても、気にしなくていいのですね。'),
    ('knit',False,'observation','ほどくのが面倒だったから、さみしくなったのですね。'),
    ('knit',False,'reception','二つのつながりが分かって、安心したのですね。'),
])
def test_independent_reader_rejects_changed_actual_words_with_unchanged_valid_refs(topic,after,section,text):
    req,p,_,prior=state(topic,after); packet=fixture_packet(req,topic,prior);packet['candidate']['surface_proposal'][section]=text
    p=prepare_model_snapshot(req,semantic(req,packet,prior))
    with pytest.raises(ValueError,match='model_surface_v3_'): evaluate_emlis_model_surface_inverse(proposal=json.loads(p.surface_proposal_json),meaning_packet=json.loads(p.meaning_json),native_bindings=json.loads(p.native_bindings_json))
    out=outcome(req,p); assert out.artifact is None and out.meaning_checkpoint==p.checkpoint


@pytest.mark.parametrize('topic,after',STATES)
def test_independent_reader_requires_complete_section_binding(topic,after):
    _,p,_,_=state(topic,after); surface=json.loads(p.surface_proposal_json);surface['bindings'][0]['claim_refs'].pop()
    with pytest.raises(ValueError,match='binding_or_coverage'): evaluate_emlis_model_surface_inverse(proposal=surface,meaning_packet=json.loads(p.meaning_json),native_bindings=json.loads(p.native_bindings_json))


@pytest.mark.parametrize('topic', ['book','shop'])
@pytest.mark.parametrize('mutation',['revise','old_claim','wrong_gap','wrong_pending','old_time'])
def test_explanations_cannot_forge_correction_or_target_or_pending(topic,mutation):
    req,p,_,prior=state(topic,True); packet=fixture_packet(req,topic,prior)
    if mutation=='revise': packet['candidate']['updates'][0]['operation']='REVISE'
    elif mutation=='old_claim': packet['candidate']['updates'][-1].update(target_kind='CLAIM',target_ref=FIXTURE[topic]['target'])
    elif mutation=='wrong_gap': packet['candidate']['updates'][0]['target_ref']='another_gap'
    elif mutation=='wrong_pending':
        control=req.emlis_thread.question_control_context; q=replace(control.pending_question,question_id='foreign-question')
        a=replace(req.emlis_thread.answers[0],question_id=q.question_id)
        req=replace(req,emlis_thread=replace(req.emlis_thread,answers=(a,),question_control_context=replace(control,pending_question=q)))
    else: packet['candidate']['claims'][-1]['about_time']['kind']='ORIGINAL_OCCASION'
    with pytest.raises(SemanticNotAdopted): prepare_model_snapshot(req,semantic(req,packet,prior))


@pytest.mark.parametrize('topic,after',STATES)
def test_real_sql_six_states_interrupt_after_meaning_retry_same_snapshot_and_saved_non_generating_reads(case,db,monkeypatch,topic,after):
    user,parent,_=case; item=FIXTURE[topic]; raw=item['original']
    result=db.query('update public.emotions set memo=$1,memo_action=$2,category=$3,emotions=$4,emotion_details=$5 where id=$6',[raw['memo'],raw['memo_action'],raw['category'],raw['emotions'],json.dumps(raw['emotion_details'],ensure_ascii=False),parent])
    assert 'code' not in result,result
    calls=[]
    def source(req,prior):
        calls.append((req.request_id,bool(req.emlis_thread.answers)))
        p=SimpleNamespace(checkpoint=SimpleNamespace(snapshot_ref=json.loads(prior)['snapshot_ref'])) if prior else None
        material=prepare_emlis(req)
        return receive_candidate(material,request_id=material.request_id,raw_output=canonical(wire(fixture_packet(req,topic,p))),finish_reason='stop',provider='independent-synthetic-test',model='synthetic-not-4B')
    service=EmlisThreadService(semantic_profile=MODEL_PROFILE,offline_candidate_source=source,offline_model_attempt_seconds=180)
    initial=run(service.start(user,parent)) if after else None
    if initial: assert initial['state']=='AWAITING_ANSWER',initial
    generate=service.engine.generate
    def interrupted(*args,**kwargs): raise asyncio.CancelledError()
    monkeypatch.setattr(service.engine,'generate',interrupted)
    with pytest.raises(asyncio.CancelledError):
        run(answer(service,user,initial,item['after']['answer'])) if after else run(service.start(user,parent))
    failed=run(service.get(user,parent))
    assert failed['can_retry'] and failed['current_observation'] is None,failed
    if after: assert failed['answer_saved'] and failed['meaning_updated']
    before=run(service.store.read(user,input_id=parent)); call_count=len(calls)
    monkeypatch.setattr(service.engine,'generate',generate)
    done=run(service.action(user,failed['thread_id'],action='retry_response',expected_revision=failed['revision'],idempotency_key='sixrow-explicit-retry',operation_id=failed['operation_id']))
    assert len(calls)==call_count
    assert done['body_state']==('REFINED' if after else 'PRE_QUESTION' if item['target'] else 'FINAL'),done
    assert done['state']==('AWAITING_ANSWER' if item['target'] and not after else 'COMPLETED'),done
    assert done['issued_count']==(1 if item['target'] else 0)
    if done['pending_question']: assert done['pending_question']['text']==item['question']
    saved=run(service.store.read(user,input_id=parent))
    assert before['thread']['current_meaning_event_id']==saved['thread']['current_meaning_event_id']
    for kind,n in [('MEANING_UPDATE',2 if after else 1),('ANSWER',1 if after else 0),('OBSERVATION',2 if after else 1)]:
        assert len([e for e in saved['events'] if e['kind']==kind])==n,(kind,saved)
    class NoGeneration:
        def __getattr__(self,name): raise AssertionError('saved sixrow read requested '+name)
    reader=EmlisThreadService(engine=NoGeneration())
    assert run(reader.get(user,parent))=={**done,'can_write':False}
    assert run(reader.start(user,parent))=={**done,'can_write':False}
    reread=run(service.store.read(user,input_id=parent))
    assert {k:v for k,v in saved.items() if k!='now'}=={k:v for k,v in reread.items() if k!='now'}
    assert len(calls)==call_count
