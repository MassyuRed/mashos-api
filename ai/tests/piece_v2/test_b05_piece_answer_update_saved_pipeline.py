"""Genuine saved one-answer updates reach the existing Piece lifecycle.

Sources/auth/HTTP responses are fictional. SQL and source owners are real;
GPU output is compared separately against the same frozen source.
"""
import asyncio
from copy import deepcopy
import json
import os
from pathlib import Path
from uuid import uuid4

import pytest

from cocolon_meaning_experience_engine.natural_reply import NaturalReply
from emlis_thread_service import EmlisThreadService, Q3_PROFILE
from piece_v2_contract import PieceContractError
from piece_v2_source_adapter import PieceSavedSourceAdapter, project_saved_refined_fence
from test_b05_natural_refined_saved_pipeline import (
    natural_refined_db, refined_pipeline_db, saved_piece_db, _bind,
)
from test_b05_refined_preview_saved_pipeline import _finish_refined_pipeline
from test_b05_piece_model_saved_pipeline import _provider
from test_b05_refined_source_fence_sql import (
    _update, _canonical_lineage, _RECORD, _issue_args, _mutation_args,
    _saved_args, _piece_state, rpc,
)

ROOT = Path(__file__).parents[3]
MEMO = '褒められたのに、嬉しくなかった。私は仕事を続けたい。'
ACTION = '私は資料を調べた。'
RETAINED = '褒められたのに、嬉しくなかった。'
ANSWERS = {
    'REVISE': '「私は仕事を続けたい」ではなく「私は家族を守りたい」です。',
    'WITHDRAW': '「私は仕事を続けたい」は取り消します。',
    'ADD': '今は、私は嬉しい。',
}
run = asyncio.run


@pytest.fixture(scope='module')
def answer_update_db(natural_refined_db):
    db = natural_refined_db
    paths = list((ROOT/'supabase/migrations').glob('*_piece_natural_answer_active_source.sql'))
    assert len(paths) == 1, paths
    db.proc.stdin.write(json.dumps(dict(sql=paths[0].read_text(), script=True))+'\n')
    db.proc.stdin.flush()
    result = json.loads(db.proc.stdout.readline())
    assert 'code' not in result, result
    return db


def prepare_answer_update(db, monkeypatch, operation, *, tier='premium', resolve=True,
                          answer_text=None, case_id=None):
    owner, parent = str(uuid4()), str(uuid4())
    token = 'synthetic-one-answer-piece-update'
    _update(db, 'insert into auth.users values ($1)', [owner])
    _update(db, 'insert into public.profiles values ($1,$2)', [owner,tier])
    _update(db, "insert into public.emotions values ($1,$2,now() at time zone 'UTC',"
        "$3,$4,array['仕事'],array['不安'],$5::jsonb)",
        [parent,owner,MEMO,ACTION,json.dumps([dict(type='不安',strength='medium')])])
    _bind(db,monkeypatch,owner,token)
    replies = []
    async def provider(material):
        replies.append(material.source_prefix_ref)
        return NaturalReply('記録を受け取る合成の返事です。',
            'synthetic-natural-provider',material.source_prefix_ref)
    service = EmlisThreadService(runtime_profile=Q3_PROFILE,natural_reply_source=provider)
    initial = run(service.start(owner,parent))
    assert initial['state'] == 'AWAITING_ANSWER' and initial['issued_count'] == 1
    answer_text = ANSWERS[operation] if answer_text is None else answer_text
    stamp = db.query('select clock_timestamp() as stamp')['rows'][0]['stamp']
    completed = run(service.answer(owner,initial['thread_id'],
        question_id=initial['pending_question']['question_id'],expected_revision=initial['revision'],
        idempotency_key='one-answer-update',answer_text=answer_text,authored_at=stamp))
    snapshot = run(service.store.read(owner,input_id=parent))
    state = dict(case_id=case_id or 'one-answer-'+operation.lower()+'-'+tier,
        tier=tier,owner=owner,source_id=parent,token=token,answer_text=answer_text,
        original=snapshot['original'],initial_dto=initial,completed_dto=completed,
        snapshot_before=snapshot,counts=dict(q2_start=1,q2_answer=1,
            piece_generation_entry=0,piece_review=0,preview_rpc=0,visual_rpc=0,
            save_rpc=0,external_model_provider=0))
    assert len(replies) == 2
    if not resolve:
        return state
    assert completed['state']=='COMPLETED' and completed['body_state']=='REFINED'
    assert completed['answer_assessment']=='RESOLVED' and completed['meaning_updated']
    checkpoint = next(e['payload'] for e in snapshot['events']
        if e['id']==snapshot['thread']['current_meaning_event_id'])
    assert checkpoint['answer_update']['disposition']=='MATERIAL_UPDATE'
    assert [u['operation'] for u in checkpoint['answer_update']['updates']] == [operation]
    reference = run(PieceSavedSourceAdapter().resolve_refined_source_ref('Bearer '+token,parent,
        supplemental_answer_identity=snapshot['thread']['latest_answer_event_id'],opted_in=True))
    assert set(reference) == {'source_input_id','source_input_version',
        'source_input_bundle_commitment','emlis_observation_stage',
        'emlis_observation_result_identity','question_need_decision_identity',
        'supplemental_answer_identity'}
    state['source_ref'] = reference
    state['request'] = dict(source_ref=reference,requested_format=None,
        visual_selection=dict(theme_id=None,aspect_ratio=None,branding_mode=None))
    return state


@pytest.mark.parametrize('tier',['free','plus','premium'])
@pytest.mark.parametrize('operation',['REVISE','WITHDRAW'])
def test_genuine_one_answer_update_reaches_preview_visual_save_and_same_reread(
        answer_update_db,monkeypatch,tier,operation):
    state = prepare_answer_update(answer_update_db,monkeypatch,operation,tier=tier)
    blocks = [RETAINED,ACTION] + (['私は家族を守りたい。'] if operation=='REVISE' else [])
    seen = _provider(monkeypatch,state['case_id'],blocks)
    result = _finish_refined_pipeline(answer_update_db,monkeypatch,state,
        visual_change=tier!='free',expected_blocks=blocks)
    assert len(seen)==1 and result['quota_consumptions']==1
    assert result['source_unchanged'] and result['emlis_unchanged']
    wire = json.dumps(seen[0]['prepared'],ensure_ascii=False)
    assert '仕事を続けたい' not in wire
    assert '取り消します' not in wire and 'ではなく' not in wire
    assert '記録を受け取る合成の返事' not in wire
    assert result['detail']['piece_text'] == '\n\n'.join(blocks)
    result['model_material_and_raw'] = seen
    result['operation'] = operation
    destination = os.environ.get('PIECE_ANSWER_UPDATE_EVIDENCE_DIR')
    if destination:
        folder=Path(destination);folder.mkdir(parents=True,exist_ok=True)
        (folder/(state['case_id']+'.private.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2))


def test_genuine_add_keeps_original_and_answer_after_update_extension(answer_update_db,monkeypatch):
    state = prepare_answer_update(answer_update_db,monkeypatch,'ADD')
    blocks = [MEMO,ACTION,ANSWERS['ADD']]
    seen = _provider(monkeypatch,state['case_id'],blocks)
    result = _finish_refined_pipeline(answer_update_db,monkeypatch,state,
        visual_change=True,expected_blocks=blocks)
    assert len(seen)==1 and result['source_unchanged'] and result['quota_consumptions']==1
    assert seen[0]['prepared']['sources'][0]['original']['memo']==MEMO


@pytest.mark.parametrize('answer',[
    '「私は仕事を続けたい」ではなく「私は家族を守りたい。」です。',
    'それは違います。',
])
def test_unresolved_answer_is_refused_before_piece_acquisition(answer_update_db,monkeypatch,answer):
    state=prepare_answer_update(answer_update_db,monkeypatch,'REVISE',resolve=False,answer_text=answer)
    assert state['completed_dto']['answer_assessment']=='UNRESOLVED'
    with pytest.raises(PieceContractError):
        run(PieceSavedSourceAdapter().resolve_refined_handoff('Bearer '+state['token'],
            state['source_id'],supplemental_answer_identity=state['snapshot_before']['thread']['latest_answer_event_id'],
            opted_in=True))


@pytest.mark.parametrize('operation',['issue','visual','save'])
@pytest.mark.parametrize('change',['checkpoint_target','checkpoint_as_add','answer_text','original_text'])
def test_update_source_fence_rejects_modified_input_without_piece_side_effects(
        answer_update_db,monkeypatch,operation,change):
    db=answer_update_db
    state=prepare_answer_update(db,monkeypatch,'REVISE')
    handoff=run(PieceSavedSourceAdapter().resolve_refined_handoff('Bearer '+state['token'],state['source_id'],
        supplemental_answer_identity=state['snapshot_before']['thread']['latest_answer_event_id'],opted_in=True))
    record=_RECORD();record['source_lineage']=_canonical_lineage(handoff)
    snapshot=state['snapshot_before'];thread=snapshot['thread']
    case=dict(owner=state['owner'],parent=state['source_id'],snapshot=snapshot,token=state['token'],
        handoff=handoff,record=record,expected=dict(original=state['original'],thread_id=thread['id'],
            thread_revision=thread['revision'],lineage=record['source_lineage'],**project_saved_refined_fence(handoff)))
    assert 'code' not in db.query('BEGIN')
    try:
        args=_issue_args(case)
        if operation!='issue':
            preview=rpc(db,'piece_issue_preview_v2',args);assert 'code' not in preview,preview
            args=_mutation_args(db,case,preview) if operation=='visual' else _saved_args(case,preview)
        if change=='original_text':
            _update(db,"update public.emotions set memo=memo||'変更' where id=$1",[state['source_id']])
        else:
            event=next(e for e in snapshot['events'] if e['id']==thread[
                'current_meaning_event_id' if change in {'checkpoint_target','checkpoint_as_add'} else 'latest_answer_event_id'])
            value=deepcopy(event['payload'])
            if change=='checkpoint_target':value['answer_update']['updates'][0]['target_meaning_refs']=['foreign-target']
            elif change=='checkpoint_as_add':
                value['answer_update']['updates'][0].update(operation='ADD',superseded_claim_refs=[],affected_dependency_refs=[])
                value['inactive_claim_refs']=[]
            else:value['source']['answer_text_private']='私は別のことを考えた。'
            _update(db,'update public.emlis_thread_events set payload=$2::jsonb where id=$1',[event['id'],json.dumps(value)])
        with pytest.raises(PieceContractError):
            run(PieceSavedSourceAdapter().resolve_refined_handoff('Bearer '+state['token'],state['source_id'],
                supplemental_answer_identity=thread['latest_answer_event_id'],opted_in=True))
        before=_piece_state(db)
        outcome=rpc(db,{'issue':'piece_issue_preview_v2','visual':'piece_mutate_preview_visual_v2','save':'piece_save_v2'}[operation],args)
        assert 'code' in outcome and outcome['message'] in {'PIECE_CONFLICT','PIECE_REQUEST_INVALID'},outcome
        assert _piece_state(db)==before
    finally:
        db.query('ROLLBACK')
