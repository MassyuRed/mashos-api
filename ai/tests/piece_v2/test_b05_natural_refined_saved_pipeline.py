"""Current natural Q3 answer -> existing refined Piece, over isolated SQL.

The Emlis provider and Piece HTTP response are synthetic; this verifies actual
source/receipt/checkpoint/SQL lifecycle, not GPU prose or native bitmap quality.
"""
import asyncio
from copy import deepcopy
import json
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import pytest
import api_account_visibility
import emlis_thread_store
from cocolon_meaning_experience_engine.natural_reply import NaturalReply
from emlis_thread_service import EmlisThreadService, Q3_PROFILE
from piece_v2_contract import PieceContractError
from piece_v2_source_adapter import PieceSavedSourceAdapter
from test_emlis_q2_application import answer as answer_question
from test_cmee_piece_request_saved_pipeline import saved_piece_db
from test_b05_piece_model_saved_pipeline import _provider
from test_b05_refined_preview_saved_pipeline import (
    refined_pipeline_db, _finish_refined_pipeline, _run_refined_pipeline,
)
from test_b05_refined_source_fence_sql import (
    _catalog, _canonical_lineage, _RECORD, _issue_args, _saved_args,
    _mutation_args, _piece_state, rpc, _update,
)

ROOT = Path(__file__).parents[3]
MIGRATION = ROOT/'supabase/migrations/20261113085044_piece_natural_refined_source_fence.sql'
ONE = '褒められたのに、嬉しくなかった。'
THREE = ONE+'誘われたのに、悲しかった。頼まれたのに、寂しかった。'
ANSWER = '今は、私は嬉しい。'
run = asyncio.run


@pytest.fixture(scope='module')
def natural_refined_db(refined_pipeline_db):
    db = refined_pipeline_db
    before = _catalog(db)
    sql = MIGRATION.read_text()
    if sql.strip():
        db.proc.stdin.write(json.dumps(dict(sql=sql,script=True))+'\n');db.proc.stdin.flush()
        applied = json.loads(db.proc.stdout.readline())
        assert 'code' not in applied, applied
    target_fence = ROOT/'supabase/migrations/20261113120502_piece_frame_target_dependency_fence.sql'
    db.proc.stdin.write(json.dumps(dict(sql=target_fence.read_text(),script=True))+'\n');db.proc.stdin.flush()
    assert 'code' not in json.loads(db.proc.stdout.readline())
    db.natural_refined_catalog = (before, _catalog(db))
    db.proc.stdin.write(json.dumps(dict(script=True,sql="""
        CREATE FUNCTION pg_temp.refined_try_rpc(statement text) RETURNS jsonb
        LANGUAGE plpgsql SECURITY INVOKER SET search_path=pg_catalog AS $$
        DECLARE result jsonb;
        BEGIN EXECUTE statement INTO result; RETURN result;
        EXCEPTION WHEN OTHERS THEN RETURN jsonb_build_object('code',SQLSTATE,'message',SQLERRM);
        END; $$;
    """))+'\n');db.proc.stdin.flush()
    assert 'code' not in json.loads(db.proc.stdout.readline())
    return db


def _bind(db, monkeypatch, owner, token):
    async def verify(value):
        assert value == token
        return owner
    monkeypatch.setattr(api_account_visibility, '_resolve_user_id_from_token', verify)
    monkeypatch.setattr(emlis_thread_store, 'sb_post_rpc', db.rpc)


def _prepare_natural(db, monkeypatch, *, tier='premium', stopped=False, case_id='natural', with_history=False,
                     with_frame_target=False):
    owner, parent = str(uuid4()), str(uuid4())
    token = 'synthetic-natural-refined-owner'
    _update(db, 'insert into auth.users values ($1)', [owner])
    _update(db, 'insert into public.profiles values ($1,$2)', [owner,tier])
    memo = THREE if stopped else ONE
    _update(db, "insert into public.emotions values ($1,$2,now() at time zone 'UTC',$3,'',array['仕事'],array['不安'],$4::jsonb)",
        [parent,owner,memo,json.dumps([dict(type='不安',strength='medium')],ensure_ascii=False)])
    past = str(uuid4()) if with_history else None
    if past:
        _update(db, "insert into public.emotions values ($1,$2,(now()-interval '1 day') at time zone 'UTC',$3,'',array['仕事'],array['不安'],$4::jsonb)",
            [past,owner,ONE,json.dumps([dict(type='不安',strength='medium')],ensure_ascii=False)])
    _bind(db,monkeypatch,owner,token)
    calls = []
    async def provider(material):
        data = json.loads(material.material_json)
        calls.append(data)
        return NaturalReply('記録を受け取る合成の返事です。', 'synthetic-natural-provider', material.source_prefix_ref)
    service = EmlisThreadService(runtime_profile=Q3_PROFILE,natural_reply_source=provider)
    frame_origin = None
    if with_frame_target:
        from test_emlis_frame_feedback_context import _cross_frame
        _, frame_origin, parent, _, service, calls, _ = _cross_frame((owner,parent,service,calls), db)
        calls.clear()
        service.natural_reply_source = provider
    initial = run(service.start(owner,parent))
    assert initial['state']=='AWAITING_ANSWER' and initial['issued_count']==1
    completed = run(answer_question(service,owner,initial,ANSWER))
    if stopped:
        assert completed['state']=='AWAITING_CONTINUE'
        before_stop = completed['current_observation']
        completed = run(service.action(owner,completed['thread_id'],action='stop',
            expected_revision=completed['revision'],idempotency_key='natural-stop'))
        assert completed['current_observation']==before_stop
    assert completed['state']=='COMPLETED' and completed['body_state']=='REFINED'
    assert completed['meaning_updated'] and completed['answer_assessment']=='RESOLVED'
    assert len(calls)==2 and calls[-1]['response_purpose']=={'stage':'REFINED'}
    snapshot = run(service.store.read(owner,input_id=parent))
    if past:
        assert [row['input_id'] for row in calls[0]['past_user_records']]==[past]
        assert [row['input_id'] for row in calls[1]['past_user_records']]==[past]
        # Newer matching inputs cannot replace the cohort consumed by either
        # saved reply. The legacy context() would select these instead.
        for _ in range(7):
            _update(db, "insert into public.emotions values ($1,$2,(now()-interval '1 hour') at time zone 'UTC',$3,'',array['仕事'],array['不安'],$4::jsonb)",
                [str(uuid4()),owner,ONE,json.dumps([dict(type='不安',strength='medium')],ensure_ascii=False)])
        related=run(service.store.related_context(owner,parent,context_guards=snapshot['thread']['data']['context_guards']))
        assert [row['guard'][0] for row in related['history']]==[past]
        assert past not in [row['guard'][0] for row in run(service.store.context(owner,parent))['history']]
    cp = next(e['payload'] for e in snapshot['events'] if e['id']==snapshot['thread']['current_meaning_event_id'])
    assert cp['answer_update']['disposition']=='MATERIAL_UPDATE'
    assert all(x['operation']=='ADD' for x in cp['answer_update']['updates'])
    answer_id = snapshot['thread']['latest_answer_event_id']
    adapter = PieceSavedSourceAdapter()
    handoff = run(adapter.resolve_refined_handoff('Bearer '+token,parent,
        supplemental_answer_identity=answer_id,opted_in=True))
    reference = run(adapter.resolve_refined_source_ref('Bearer '+token,parent,
        supplemental_answer_identity=answer_id,opted_in=True))
    state = dict(case_id=case_id,tier=tier,owner=owner,source_id=parent,token=token,frame_target_origin=frame_origin,
        answer_text=ANSWER,original=snapshot['original'],source_ref=reference,
        request=dict(source_ref=reference,requested_format=None,
            visual_selection=dict(theme_id=None,aspect_ratio=None,branding_mode=None)),
        initial_dto=initial,completed_dto=completed,snapshot_before=snapshot,
        # The retained workflow helper has historical counter names; evidence
        # below explicitly relabels these two real natural lifecycle calls.
        counts=dict(q2_start=1,q2_answer=1,piece_generation_entry=0,piece_review=0,
            preview_rpc=0,visual_rpc=0,save_rpc=0,external_model_provider=0))
    return state,handoff,calls


def test_cross_frame_target_refined_reaches_piece_save_and_same_saved_artifact(natural_refined_db, monkeypatch):
    state, handoff, calls = _prepare_natural(natural_refined_db,monkeypatch,
        case_id='cross-frame-refined-piece',with_frame_target=True)
    assert state['snapshot_before']['thread']['data']['frame_target_dependencies']
    assert state['frame_target_origin'] not in [g[0] for g in state['snapshot_before']['thread']['data']['context_guards']]
    blocks=[state['original']['memo'],ANSWER]
    seen=_provider(monkeypatch,'cross-frame-refined-piece',blocks)
    result=_finish_refined_pipeline(natural_refined_db,monkeypatch,state,
        visual_change=True,expected_blocks=blocks)
    assert len(calls)==2 and len(seen)==1
    assert result['quota_consumptions']==1 and result['source_unchanged'] and result['emlis_unchanged']


@pytest.mark.parametrize('operation',['issue','visual','save'])
@pytest.mark.parametrize('change',['edited','deleted'])
def test_cross_frame_target_piece_sql_rejects_changed_origin(natural_refined_db,monkeypatch,operation,change):
    db=natural_refined_db
    state,handoff,_=_prepare_natural(db,monkeypatch,with_frame_target=True)
    record=_RECORD();record['source_lineage']=_canonical_lineage(handoff)
    case=dict(owner=state['owner'],parent=state['source_id'],snapshot=state['snapshot_before'],
        token=state['token'],handoff=handoff,record=record,
        expected=dict(original=state['original'],thread_id=state['snapshot_before']['thread']['id'],
            thread_revision=state['snapshot_before']['thread']['revision'],lineage=record['source_lineage']))
    args=_issue_args(case)
    if operation!='issue':
        preview=rpc(db,'piece_issue_preview_v2',args); assert 'code' not in preview,preview
        args=_mutation_args(db,case,preview) if operation=='visual' else _saved_args(case,preview)
    if change=='edited':
        _update(db,'update public.emotions set memo=$2 where id=$1',[state['frame_target_origin'],'書き直した記録。'])
    else:
        _update(db,'delete from public.emotions where id=$1',[state['frame_target_origin']])
    before=_piece_state(db)
    result=rpc(db,{'issue':'piece_issue_preview_v2','visual':'piece_mutate_preview_visual_v2','save':'piece_save_v2'}[operation],args)
    assert 'code' in result and result['message']=='PIECE_CONTEXT_CHANGED',result
    assert _piece_state(db)==before


@pytest.mark.parametrize('tier',['free','plus','premium'])
@pytest.mark.parametrize('stopped',[False,True],ids=['direct','stop'])
def test_current_natural_one_answer_reaches_model_preview_visual_save_reread(
        natural_refined_db,monkeypatch,tier,stopped):
    identity='natural-refined-'+tier+('-stop' if stopped else '-direct')
    state,handoff,calls = _prepare_natural(natural_refined_db,monkeypatch,
        tier=tier,stopped=stopped,case_id=identity,with_history=tier!='free')
    blocks = [state['original']['memo'],ANSWER]
    seen = _provider(monkeypatch,identity,blocks)
    result = _finish_refined_pipeline(natural_refined_db,monkeypatch,state,
        visual_change=tier!='free',expected_blocks=blocks)
    assert len(calls)==2 and len(seen)==1
    material=seen[0]['prepared']
    assert [x['role'] for x in material['sources']]==['ORIGINAL_INPUT','SUPPLEMENTAL_ANSWER']
    assert '記録を受け取る合成の返事' not in json.dumps(material,ensure_ascii=False)
    assert result['quota_consumptions']==1 and result['source_unchanged'] and result['emlis_unchanged']
    result['counts']['natural_start']=result['counts'].pop('q2_start')
    result['counts']['natural_answer']=result['counts'].pop('q2_answer')
    result['counts']['external_model_provider']=len(seen)
    result['emlis_profile']='natural_reply.v1'
    result['stopped_after_one_answer']=stopped
    result['model_material_and_raw']=seen
    result['limits']=['synthetic Auth/provider HTTP','isolated SQL','no GPU/live DB/native bitmap']
    import os
    destination=os.environ.get('NATURAL_REFINED_EVIDENCE_DIR')
    if destination:
        folder=Path(destination);folder.mkdir(parents=True,exist_ok=True)
        (folder/(identity+'.private.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')


@pytest.fixture(scope='module')
def natural_sql_case(natural_refined_db):
    with pytest.MonkeyPatch.context() as setup:
        state,handoff,_=_prepare_natural(natural_refined_db,setup,case_id='natural-fence')
    line=_canonical_lineage(handoff)
    record=_RECORD();record['source_lineage']=line
    return dict(owner=state['owner'],parent=state['source_id'],snapshot=state['snapshot_before'],
        token=state['token'],handoff=handoff,record=record,
        expected=dict(original=state['original'],thread_id=state['snapshot_before']['thread']['id'],
            thread_revision=state['snapshot_before']['thread']['revision'],lineage=line))


CHANGES=('refined_received_text','refined_received_model','refined_started_context',
    'initial_received_prefix','initial_context_chain','checkpoint_answer','checkpoint_replace',
    'unknown_profile','wrong_policy','finish_failure','duplicate_receipt','second_question','edited_original')

def _change(db,case,change):
    snap=case['snapshot'];thread=snap['thread'];events=snap['events']
    observation=next(e for e in events if e['id']==thread['last_observation_event_id'])
    checkpoint=next(e for e in events if e['id']==thread['current_meaning_event_id'])
    def receipt(stage,round_index):
        return next(e for e in events if e['kind']=='OPERATION' and e['payload'].get('stage')==stage and e['round_index']==round_index)
    def payload(event,value):
        _update(db,'update public.emlis_thread_events set payload=$2::jsonb where id=$1',[event['id'],json.dumps(value,ensure_ascii=False)])
    if change in {'refined_received_text','refined_received_model'}:
        event=receipt('NATURAL_REPLY_RECEIVED',1);value=deepcopy(event['payload'])
        value['reply']['text' if change.endswith('text') else 'model']='altered'
        payload(event,value)
    elif change in {'refined_started_context','initial_received_prefix'}:
        event=receipt('NATURAL_REPLY_CALL_STARTED',1) if change.startswith('refined') else receipt('NATURAL_REPLY_RECEIVED',0)
        value=deepcopy(event['payload']);value['context_ref' if change.startswith('refined') else 'source_prefix_ref']='foreign'
        payload(event,value)
    elif change=='initial_context_chain':
        for event in events:
            if event['round_index']==0 and (event['kind']=='OBSERVATION' or event['payload'].get('stage') in {'NATURAL_REPLY_CALL_STARTED','NATURAL_REPLY_RECEIVED'}):
                value=deepcopy(event['payload']);value['context_ref']='foreign-consistent-initial-chain';payload(event,value)
    elif change in {'checkpoint_answer','checkpoint_replace'}:
        value=deepcopy(checkpoint['payload'])
        if change.endswith('answer'):value['answer_update']['answer_source_ref']='foreign'
        else:value['answer_update']['updates'][0]['operation']='REVISE'
        payload(checkpoint,value)
    elif change in {'unknown_profile','wrong_policy'}:
        value=deepcopy(thread['data']);value['response_profile' if change=='unknown_profile' else 'natural_question_policy']='unsupported'
        _update(db,'update public.emlis_input_threads set data=$2::jsonb where id=$1',[thread['id'],json.dumps(value)])
    elif change=='finish_failure':
        event=next(e for e in events if e['kind']=='OPERATION' and e['seq']>observation['seq'])
        value=deepcopy(event['payload']);value['failure_code']='failed';payload(event,value)
    elif change in {'duplicate_receipt','second_question'}:
        event=receipt('NATURAL_REPLY_RECEIVED',1) if change=='duplicate_receipt' else next(e for e in events if e['kind']=='QUESTION')
        _update(db,'insert into public.emlis_thread_events(id,thread_id,seq,kind,round_index,question_id,operation_id,attempt_id,payload) values ($1,$2,$3,$4,$5,$6,$7,$8,$9::jsonb)',
            [str(uuid4()),thread['id'],max(e['seq'] for e in events)+1,event['kind'],event['round_index'] if change=='duplicate_receipt' else 2,
             event['question_id'] if change=='duplicate_receipt' else 'additional-question',event['operation_id'],event['attempt_id'],json.dumps(event['payload'])])
    elif change=='edited_original':
        _update(db,"update public.emotions set memo=memo||'変更' where id=$1",[case['parent']])
    else:raise AssertionError(change)


@pytest.mark.parametrize('operation',['issue','visual','save'])
@pytest.mark.parametrize('change',CHANGES)
def test_natural_current_source_fence_rejects_modified_success_atomically(
        natural_refined_db,natural_sql_case,operation,change):
    db=natural_refined_db;case=deepcopy(natural_sql_case)
    assert 'code' not in db.query('BEGIN')
    try:
        args=_issue_args(case)
        if operation!='issue':
            preview=rpc(db,'piece_issue_preview_v2',args);assert 'code' not in preview,preview
            args=_mutation_args(db,case,preview) if operation=='visual' else _saved_args(case,preview)
        _change(db,case,change)
        before=_piece_state(db)
        outcome=rpc(db,{'issue':'piece_issue_preview_v2','visual':'piece_mutate_preview_visual_v2','save':'piece_save_v2'}[operation],args)
        assert 'code' in outcome and outcome['message'] in {'PIECE_CONFLICT','PIECE_REQUEST_INVALID'},outcome
        assert _piece_state(db)==before
    finally:db.query('ROLLBACK')


@pytest.mark.parametrize('change',CHANGES)
def test_natural_adapter_rejects_modified_source_before_piece_generation(
        natural_refined_db,natural_sql_case,monkeypatch,change):
    db=natural_refined_db;case=natural_sql_case
    _bind(db,monkeypatch,case['owner'],case['token'])
    assert 'code' not in db.query('BEGIN')
    try:
        _change(db,case,change)
        with pytest.raises(PieceContractError):
            run(PieceSavedSourceAdapter().resolve_refined_handoff('Bearer '+case['token'],case['parent'],
                supplemental_answer_identity=case['snapshot']['thread']['latest_answer_event_id'],opted_in=True))
    finally:db.query('ROLLBACK')


def test_natural_refined_migration_preserves_existing_acl_tables_and_primitive(natural_refined_db):
    assert natural_refined_db.natural_refined_catalog[0]==natural_refined_db.natural_refined_catalog[1]


@pytest.mark.parametrize('answer',['私は寂しかった。','今は、私は嬉しい。'])
def test_legacy_refined_control_keeps_visual_save_reread_after_new_migration(
        natural_refined_db,monkeypatch,answer):
    seen=_provider(monkeypatch,'legacy-control',[ONE,answer])
    result=_run_refined_pipeline(natural_refined_db,monkeypatch,answer,'legacy-control',
        tier='premium',visual_change=True)
    assert len(seen)==1 and result['quota_consumptions']==1
    assert result['source_unchanged'] and result['emlis_unchanged']


def test_zero_answer_natural_control_still_reaches_same_saved_piece(
        natural_refined_db,monkeypatch):
    from test_cmee_piece_request_saved_pipeline import _run_saved_request
    memo='私は同僚に資料の確認を頼みました。'
    seen=_provider(monkeypatch,'original-control',[memo])
    result=_run_saved_request(natural_refined_db,monkeypatch,dict(id='original-control',
        created_at=natural_refined_db.query('select now()::text as stamp')['rows'][0]['stamp'],
        memo=memo,memo_action='',category=['仕事'],emotions=['自己理解'],
        emotion_details=[dict(type='自己理解',strength='medium')]),tier='premium')
    assert len(seen)==1 and result['quota_consumptions']==1
    assert [x['role'] for x in seen[0]['prepared']['sources']]==['ORIGINAL_INPUT']


@pytest.mark.parametrize('operation',['issue','visual','save'])
def test_stop_reuse_requires_the_actual_stop_terminal(
        natural_refined_db,monkeypatch,operation):
    db=natural_refined_db
    state,handoff,_=_prepare_natural(db,monkeypatch,stopped=True,case_id='stop-fence')
    line=_canonical_lineage(handoff);record=_RECORD();record['source_lineage']=line
    snapshot=state['snapshot_before'];thread=snapshot['thread']
    case=dict(owner=state['owner'],parent=state['source_id'],snapshot=snapshot,
        record=record,expected=dict(original=state['original'],thread_id=thread['id'],
        thread_revision=thread['revision'],lineage=line))
    terminal=next(e for e in snapshot['events'] if e['kind']=='TERMINAL')
    assert 'code' not in db.query('BEGIN')
    try:
        args=_issue_args(case)
        if operation!='issue':
            preview=rpc(db,'piece_issue_preview_v2',args);assert 'code' not in preview,preview
            args=_mutation_args(db,case,preview) if operation=='visual' else _saved_args(case,preview)
        payload=deepcopy(terminal['payload']);payload['reason']='skip'
        _update(db,'update public.emlis_thread_events set payload=$2::jsonb where id=$1',
            [terminal['id'],json.dumps(payload)])
        with pytest.raises(PieceContractError):
            run(PieceSavedSourceAdapter().resolve_refined_handoff('Bearer '+state['token'],state['source_id'],
                supplemental_answer_identity=thread['latest_answer_event_id'],opted_in=True))
        before=_piece_state(db)
        result=rpc(db,{'issue':'piece_issue_preview_v2','visual':'piece_mutate_preview_visual_v2','save':'piece_save_v2'}[operation],args)
        assert result.get('message')=='PIECE_CONFLICT',result
        assert _piece_state(db)==before
    finally:db.query('ROLLBACK')


@pytest.mark.parametrize('operation',['issue','visual','save'])
@pytest.mark.parametrize('change',['edit','delete'])
def test_natural_refined_invalidated_consumed_history_is_rejected(
        natural_refined_db,monkeypatch,operation,change):
    db=natural_refined_db
    state,handoff,_=_prepare_natural(db,monkeypatch,with_history=True,case_id='history-fence')
    snapshot=state['snapshot_before'];thread=snapshot['thread']
    past,=thread['data']['context_guards']
    line=_canonical_lineage(handoff);record=_RECORD();record['source_lineage']=line
    case=dict(owner=state['owner'],parent=state['source_id'],snapshot=snapshot,
        record=record,expected=dict(original=state['original'],thread_id=thread['id'],
        thread_revision=thread['revision'],lineage=line))
    assert 'code' not in db.query('BEGIN')
    try:
        args=_issue_args(case)
        if operation!='issue':
            preview=rpc(db,'piece_issue_preview_v2',args);assert 'code' not in preview,preview
            args=_mutation_args(db,case,preview) if operation=='visual' else _saved_args(case,preview)
        if change=='edit':
            _update(db,"update public.emotions set memo=memo||'変更' where id=$1",[past[0]])
        else:_update(db,'delete from public.emotions where id=$1',[past[0]])
        with pytest.raises(PieceContractError):
            run(PieceSavedSourceAdapter().resolve_refined_handoff('Bearer '+state['token'],state['source_id'],
                supplemental_answer_identity=thread['latest_answer_event_id'],opted_in=True))
        before=_piece_state(db)
        result=rpc(db,{'issue':'piece_issue_preview_v2','visual':'piece_mutate_preview_visual_v2','save':'piece_save_v2'}[operation],args)
        assert result.get('message')=='PIECE_CONFLICT',result
        assert _piece_state(db)==before
    finally:db.query('ROLLBACK')
