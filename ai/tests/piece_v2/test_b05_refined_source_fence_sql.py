"""Refined SQL fence over disposable PGlite, without hosted DB or native locks.

Existing Q2/CMEE produces real accepted ADD states. Record content/renderer is
a canonical synthetic SQL fixture; full author/review/service coverage is a
separate suite. Frame-escaping cases deliberately test SQL bytes only and do
not claim semantic admission of their altered answer prose.
"""
import asyncio
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import runpy
from unittest.mock import patch
from uuid import uuid4

import pytest

import api_account_visibility
import emlis_thread_store
from emlis_thread_service import EmlisThreadService
from cocolon_meaning_experience_engine.emlis_thread_contracts import SupplementalAnswerSource
from cocolon_meaning_experience_engine.emlis_thread_source import freeze_supplemental_answer
from piece_v2_contract import canonical_sha256_hex
from piece_v2_source_adapter import PieceSavedSourceAdapter
from piece_v2_visual import build_visual_recipe
from test_cmee_piece_request_saved_pipeline import saved_piece_db, _run_saved_request
from test_emlis_q2_application import answer as answer_question

ROOT=Path(__file__).parents[3]
MIGRATION=ROOT/'supabase/migrations/20261109024943_piece_refined_source_fence.sql'
_PERSISTENCE=runpy.run_path(str(Path(__file__).parent/'db/test_b05_preview_persistence.py'))
_RECORD=_PERSISTENCE['_record']
SIGNATURES=(
    'public.piece_issue_preview_v2(uuid,text,text,jsonb,integer,text,jsonb)',
    'public.piece_save_v2(uuid,uuid,bigint,text,text,text,text,text,text,jsonb,boolean)',
    'public.piece_mutate_preview_visual_v2(uuid,uuid,bigint,jsonb,jsonb,text,text,jsonb)',
)
MUTATION_FIELDS=(
    'id','owner_user_id','piece_contract_version','lifecycle_status','preview_request_hash',
    'preview_revision','row_version','expires_at','visibility_scope','source_lineage','format_type',
    'preview_eligible_formats','content_payload','content_payload_hash','piece_text','piece_text_hash',
    'safety_state','visual_recipe','visual_recipe_hash','renderer_version',
)
run=asyncio.run


def _catalog(db):
    return dict(
        functions=db.query("SELECT p.oid::regprocedure::text AS signature,p.prosecdef,p.proconfig,p.proacl::text FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='public' AND p.proname IN ('piece_issue_preview_v2','piece_save_v2','piece_mutate_preview_visual_v2') ORDER BY 1"),
        tables=db.query("SELECT c.relname,c.relrowsecurity,c.relforcerowsecurity,c.relacl::text FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relname LIKE 'piece%' ORDER BY 1"),
        primitive=db.query("SELECT pg_get_functiondef('public.piece_issue_preview_v2(uuid,text,text,jsonb,integer)'::regprocedure) AS definition"),
    )


@pytest.fixture(scope='module')
def refined_piece_db(saved_piece_db):
    db=saved_piece_db
    db.refined_catalog_before=_catalog(db)
    db.proc.stdin.write(json.dumps(dict(sql=MIGRATION.read_text(),script=True))+'\n');db.proc.stdin.flush()
    applied=json.loads(db.proc.stdout.readline())
    assert 'code' not in applied,applied
    db.refined_catalog_after=_catalog(db)
    # The retained JS bridge RESET ROLE cannot run in an aborted outer
    # transaction. Catch expected RPC errors inside a real SQL subtransaction;
    # this invoker-only temp helper keeps the tested service_role unchanged.
    db.proc.stdin.write(json.dumps(dict(script=True,sql="""
        CREATE FUNCTION pg_temp.refined_try_rpc(statement text) RETURNS jsonb
        LANGUAGE plpgsql SECURITY INVOKER SET search_path=pg_catalog AS $$
        DECLARE result jsonb;
        BEGIN EXECUTE statement INTO result; RETURN result;
        EXCEPTION WHEN OTHERS THEN RETURN jsonb_build_object('code',SQLSTATE,'message',SQLERRM);
        END; $$;
    """))+'\n');db.proc.stdin.flush()
    assert 'code'not in json.loads(db.proc.stdout.readline())
    yield db


def _canonical_lineage(handoff):
    private=handoff.lineage_payload()
    keys=('handoff_contract_version','piece_source_lineage_version','source_input','observation',
          'semantic_source_roles','lineage_control_roles','piece_generation_eligibility','body_free')
    result={k:deepcopy(private[k]) for k in keys}
    result['source_input'].pop('source_input_record_commitment',None)
    result['observation'].pop('source_prefix_ref',None)
    return result


def _case(db,text,*,refined=True):
    owner,parent=str(uuid4()),str(uuid4())
    assert 'code'not in db.query('INSERT INTO auth.users VALUES ($1)',[owner])
    assert 'code'not in db.query("INSERT INTO public.profiles VALUES ($1,'premium')",[owner])
    assert 'code'not in db.query("INSERT INTO public.emotions VALUES ($1,$2,now() at time zone 'UTC',$3,'',array['仕事'],array['不安'],$4::jsonb)",
        [parent,owner,'褒められたのに、嬉しくなかった。',json.dumps([dict(type='不安',strength='medium')],ensure_ascii=False)])
    async def verify(token):
        assert token=='refined-sql-synthetic'
        return owner
    with patch.object(api_account_visibility,'_resolve_user_id_from_token',verify), \
         patch.object(emlis_thread_store,'sb_post_rpc',db.rpc):
        service=EmlisThreadService();initial=run(service.start(owner,parent))
        assert initial['state']=='AWAITING_ANSWER'
        if refined:
            final=run(answer_question(service,owner,initial,text))
            assert final['body_state']=='REFINED' and final['meaning_updated'] is True
        snapshot=run(service.store.read(owner,input_id=parent))
        adapter=PieceSavedSourceAdapter(store=service.store)
        if refined:
            h=run(adapter.resolve_refined_handoff('Bearer refined-sql-synthetic',parent,
                supplemental_answer_identity=snapshot['thread']['latest_answer_event_id'],opted_in=True))
        else:
            h=run(adapter.resolve_original_handoff('Bearer refined-sql-synthetic',parent))
    line=_canonical_lineage(h);record=_RECORD();record['source_lineage']=line
    expected=dict(original=snapshot['original'],thread_id=snapshot['thread']['id'],
        thread_revision=snapshot['thread']['revision'],lineage=line)
    return dict(owner=owner,parent=parent,snapshot=snapshot,handoff=h,record=record,expected=expected)


@pytest.fixture(scope='module')
def refined_sql_cases(refined_piece_db):
    return [_case(refined_piece_db,'私は寂しかった。'),_case(refined_piece_db,'今は、私は嬉しい。')]


def rpc(db,name,args,*,role='service_role'):
    def literal(value):
        if value is None:return 'NULL'
        if type(value)is bool:return 'true'if value else'false'
        if type(value)is int:return str(value)
        js=isinstance(value,(dict,list))
        text=json.dumps(value,ensure_ascii=False)if js else str(value)
        return "E'"+text.replace('\\','\\\\').replace("'","''")+"'"+('::jsonb'if js else'')
    named=','.join(f'{key} => {literal(value)}'for key,value in args.items())
    result=db.query('SELECT pg_temp.refined_try_rpc($1) AS value',[f'SELECT public.{name}({named})'],role,error_message=True)
    return result if 'code'in result else result['rows'][0]['value']


def _issue_args(case):
    return dict(p_owner_user_id=case['owner'],p_idempotency_key_hash=hashlib.sha256(str(uuid4()).encode()).hexdigest(),
        p_request_hash='a'*64,p_record=deepcopy(case['record']),p_ttl_seconds=600,
        p_expected_subscription_tier='premium',p_expected_source_state=deepcopy(case['expected']))


def _saved_args(case,preview):
    return dict(p_owner_user_id=case['owner'],p_preview_id=preview['preview_id'],
        p_expected_preview_revision=preview['preview_revision'],p_piece_text_hash=preview['piece_text_hash'],
        p_content_payload_hash=preview['content_payload_hash'],p_visual_recipe_hash=preview['visual_recipe_hash'],
        p_idempotency_key_hash=hashlib.sha256(str(uuid4()).encode()).hexdigest(),p_visibility_scope='private',
        p_expected_subscription_tier='premium',p_expected_source_state=deepcopy(case['expected']),p_replay_only=False)


def _mutation_args(db,case,preview):
    row=db.query('SELECT to_jsonb(r) AS row FROM public.piece_records r WHERE id=$1',[preview['preview_id']])['rows'][0]['row']
    recipe=build_visual_recipe('short_essay',tier='premium',theme='quiet_night',aspect_ratio='4:5',branding='off')
    return dict(p_owner_user_id=case['owner'],p_preview_id=preview['preview_id'],p_expected_preview_revision=preview['preview_revision'],
        p_expected_record={k:row[k]for k in MUTATION_FIELDS},p_visual_recipe=recipe,p_visual_recipe_hash=canonical_sha256_hex(recipe),
        p_expected_subscription_tier='premium',p_expected_source_state=deepcopy(case['expected']))


def _update(db,sql,params):
    result=db.query(sql,params,error_message=True)
    assert 'code'not in result,result
    return result


def _piece_state(db):
    return {table:db.query('SELECT to_jsonb(r) AS row FROM public.'+table+' r ORDER BY to_jsonb(r)::text')
        for table in ('piece_records','piece_quota_consumptions','piece_quota_month_locks')}


def test_refined_migration_changes_only_existing_function_bodies_and_preserves_privileges(refined_piece_db):
    db=refined_piece_db
    assert db.refined_catalog_before==db.refined_catalog_after
    for signature in SIGNATURES:
        for role,expected in [('anon',False),('authenticated',False),('service_role',True)]:
            actual=db.query('SELECT has_function_privilege($1,$2,\'EXECUTE\') AS allowed',[role,signature])
            assert actual['rows'][0]['allowed']is expected


@pytest.mark.parametrize('which',[0,1])
def test_real_q2_refined_issue_visual_save_replay_consumes_once(refined_piece_db,refined_sql_cases,which):
    db=refined_piece_db;case=refined_sql_cases[which]
    assert 'code'not in db.query('BEGIN')
    try:
        args=_issue_args(case);first=rpc(db,'piece_issue_preview_v2',args);assert 'code'not in first,first
        again=rpc(db,'piece_issue_preview_v2',args);assert again['preview_id']==first['preview_id']and again['idempotency_replayed']
        visual=rpc(db,'piece_mutate_preview_visual_v2',_mutation_args(db,case,first));assert 'code'not in visual,visual
        assert visual['piece_text']==first['piece_text']and visual['content_payload']==first['content_payload']
        assert visual['visual_recipe_hash']!=first['visual_recipe_hash']
        saved_args=_saved_args(case,visual);saved=rpc(db,'piece_save_v2',saved_args);assert 'code'not in saved,saved
        replay=rpc(db,'piece_save_v2',saved_args);assert replay['consumption_id']==saved['consumption_id']and replay['idempotency_replayed']
        assert db.query('SELECT count(*)::int AS n FROM public.piece_quota_consumptions WHERE piece_id=$1',[saved['piece_id']])['rows'][0]['n']==1
        # A saved replay is historical and must not require a still-current input.
        assert 'code'not in db.query('DELETE FROM public.emotions WHERE id=$1',[case['parent']])
        after_delete=rpc(db,'piece_save_v2',saved_args)
        assert after_delete['consumption_id']==saved['consumption_id']and after_delete['idempotency_replayed']
    finally:db.query('ROLLBACK')


@pytest.mark.parametrize('operation',['issue','visual','save'])
@pytest.mark.parametrize('change',[
    'answer_text','answer_time','answer_id','commitment','question','checkpoint_question',
    'checkpoint_answer','checkpoint_partial','checkpoint_replace','checkpoint_superseded',
    'latest_answer','active_attempt','stale_revision','missing_profile','null_profile',
    'finish_failure','checkpoint_attempt','normal_disguise','pre_question_disguise',
])
def test_refined_current_source_mutations_fail_atomically(refined_piece_db,refined_sql_cases,operation,change):
    db=refined_piece_db;case=deepcopy(refined_sql_cases[0]);snapshot=case['snapshot'];t=snapshot['thread']
    answer_event=next(e for e in snapshot['events']if e['kind']=='ANSWER')
    checkpoint=next(e for e in snapshot['events']if e['id']==t['current_meaning_event_id'])
    finish=next(e for e in snapshot['events']if e['kind']=='OPERATION'and e['seq']>next(x['seq']for x in snapshot['events']if x['id']==t['last_observation_event_id']))
    assert 'code'not in db.query('BEGIN')
    try:
        issue_args=_issue_args(case)
        if operation!='issue':
            preview=rpc(db,'piece_issue_preview_v2',issue_args);assert 'code'not in preview,preview
            args=_mutation_args(db,case,preview)if operation=='visual'else _saved_args(case,preview)
        else:args=issue_args
        if change in {'answer_text','answer_time','answer_id'}:
            payload=deepcopy(answer_event['payload']);field={'answer_text':'answer_text_private','answer_time':'authored_at','answer_id':'answer_id'}[change]
            payload['source'][field]=payload['source']['answer_text_private']+'追加'if change=='answer_text'else '2026-11-09T00:00:00+00:00'if change=='answer_time'else str(uuid4())
            _update(db,'UPDATE public.emlis_thread_events SET payload=$2::jsonb WHERE id=$1',[answer_event['id'],json.dumps(payload,ensure_ascii=False)])
        elif change.startswith('checkpoint_'):
            payload=deepcopy(checkpoint['payload']);update=payload['answer_update']
            if change=='checkpoint_question':update['question_ref']='wrong'
            elif change=='checkpoint_answer':update['answer_source_ref']='wrong'
            elif change=='checkpoint_partial':payload['assessment_status']='PARTIAL'
            elif change=='checkpoint_replace':update['updates'][0]['operation']='REVISE'
            elif change=='checkpoint_superseded':update['updates'][0]['superseded_claim_refs']=['old']
            elif change=='checkpoint_attempt':
                _update(db,'UPDATE public.emlis_thread_events SET attempt_id=$2 WHERE id=$1',[checkpoint['id'],str(uuid4())])
            _update(db,'UPDATE public.emlis_thread_events SET payload=$2::jsonb WHERE id=$1',[checkpoint['id'],json.dumps(payload,ensure_ascii=False)])
        elif change=='latest_answer':_update(db,'UPDATE public.emlis_input_threads SET latest_answer_event_id=NULL WHERE id=$1',[t['id']])
        elif change=='active_attempt':
            changed=_update(db,"UPDATE public.emlis_input_threads SET state='REFINING',active_attempt_id=$2,active_operation_id=$3,processing_deadline_at=clock_timestamp()+interval '1 minute' WHERE id=$1",[t['id'],str(uuid4()),str(uuid4())])
            assert 'code'not in changed,changed
        elif change in {'missing_profile','null_profile'}:
            data=deepcopy(t['data']);data.pop('runtime_profile')if change=='missing_profile'else data.update(runtime_profile=None)
            _update(db,'UPDATE public.emlis_input_threads SET data=$2::jsonb WHERE id=$1',[t['id'],json.dumps(data)])
        elif change=='finish_failure':
            payload=deepcopy(finish['payload']);payload['failure_code']='failed'
            _update(db,'UPDATE public.emlis_thread_events SET payload=$2::jsonb WHERE id=$1',[finish['id'],json.dumps(payload)])
        else:
            line=args['p_expected_source_state']['lineage']
            if change=='commitment':line['observation']['supplemental_answer_bundle_commitment']='sha256:'+'f'*64
            elif change=='question':line['observation']['question_need_decision_identity']=str(uuid4())
            elif change=='stale_revision':args['p_expected_source_state']['thread_revision']+=1
            elif change in {'normal_disguise','pre_question_disguise'}:
                line['observation']['emlis_observation_stage']='normal_observation'if change=='normal_disguise'else'pre_question_observation'
            else:raise AssertionError(change)
            if operation=='issue':args['p_record']['source_lineage']=deepcopy(line)
            elif operation=='visual':args['p_expected_record']['source_lineage']=deepcopy(line)
        before=_piece_state(db)
        outcome=rpc(db,{'issue':'piece_issue_preview_v2','visual':'piece_mutate_preview_visual_v2','save':'piece_save_v2'}[operation],args)
        assert 'code'in outcome and outcome['message']in {'PIECE_CONFLICT','PIECE_REQUEST_INVALID'},outcome
        assert _piece_state(db)==before
    finally:db.query('ROLLBACK')


@pytest.mark.parametrize('text',['私は、"引用"\\記号\n漢字🙂e\u0301と\u2028区切りを残した。'])
def test_sql_frame_preserves_quotes_newlines_unicode_and_combining_bytes(refined_piece_db,refined_sql_cases,text):
    db=refined_piece_db;case=deepcopy(refined_sql_cases[0]);snap=case['snapshot'];t=snap['thread']
    event=next(e for e in snap['events']if e['kind']=='ANSWER');cp=next(e for e in snap['events']if e['id']==t['current_meaning_event_id'])
    source=SupplementalAnswerSource(**event['payload']['source']);frozen=freeze_supplemental_answer(replace(source,answer_text_private=text))
    assert 'code'not in db.query('BEGIN')
    try:
        payload=deepcopy(event['payload']);payload['source']['answer_text_private']=text
        _update(db,'UPDATE public.emlis_thread_events SET payload=$2::jsonb WHERE id=$1',[event['id'],json.dumps(payload,ensure_ascii=False)])
        checkpoint=deepcopy(cp['payload']);checkpoint['answer_update']['answer_source_ref']=frozen.envelope.envelope_id
        _update(db,'UPDATE public.emlis_thread_events SET payload=$2::jsonb WHERE id=$1',[cp['id'],json.dumps(checkpoint,ensure_ascii=False)])
        digest='sha256:'+frozen.envelope.raw_sha256
        case['record']['source_lineage']['observation']['supplemental_answer_bundle_commitment']=digest
        case['expected']['lineage']['observation']['supplemental_answer_bundle_commitment']=digest
        outcome=rpc(db,'piece_issue_preview_v2',_issue_args(case))
        assert 'code'not in outcome,outcome
        # Python's hash is checked by the real SQL final fence, without NFC/LF
        # normalization. This changed prose has no Emlis/CMEE meaning credit.
        assert frozen.envelope.raw_utf8.endswith(text.encode())
    finally:db.query('ROLLBACK')


def test_original_pre_question_still_requires_no_answer(refined_piece_db):
    db=refined_piece_db;case=_case(db,None,refined=False)
    assert case['record']['source_lineage']['observation']['emlis_observation_stage']=='pre_question_observation'
    db.query('BEGIN')
    try:
        outcome=rpc(db,'piece_issue_preview_v2',_issue_args(case));assert 'code'not in outcome,outcome
    finally:db.query('ROLLBACK')


@pytest.mark.parametrize('tier',['free','plus','premium'])
def test_normal_natural_after_refined_migration_keeps_existing_saved_pipeline(refined_piece_db,monkeypatch,tier):
    # Reuse the existing service/review/SQL/owner workflow with a prior supported
    # action and separate reservation. The new migration is already applied.
    # Its synthetic preceding natural provider supplies no Piece body material.
    record=dict(id='existing-original-normal-control',created_at='2026-11-09T00:00:00Z',
        memo='まだ、決めていません。',memo_action='私は司書から展示の設営を頼まれた。',
        category=['仕事','人間関係'],emotions=['自己理解'],
        emotion_details=[dict(type='自己理解',strength='medium')])
    _run_saved_request(refined_piece_db,monkeypatch,record,tier=tier)
