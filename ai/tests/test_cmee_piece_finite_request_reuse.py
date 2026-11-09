"""Source-role grammar qualifies literal Piece accounts, not new prose."""
from dataclasses import replace
import hashlib,json
from unittest.mock import patch
import pytest
from piece_v2_contract import canonical_json_bytes,PieceContractError
from piece_v2_generation import PieceSourceSnapshot,generate_piece_candidate
from piece_v2_content_policy import validate_source_meaning_preservation
from cocolon_meaning_experience_engine.piece_source import build_piece_source_meaning,piece_text_nodes,_finite_self_person_action_account
from cocolon_meaning_experience_engine.piece_v1c import compile_piece_artifact_plan,realize_piece_artifact

def source(text,*,field='memo_action',other=None,emotions=None,details=None):
    record=dict(id='ar04-synthetic-record',created_at='2026-11-09T00:00:00Z',
        memo=text if field=='memo'else other,memo_action=text if field=='memo_action'else other,
        category=['仕事','人間関係'],emotions=['自己理解']if emotions is None else emotions,
        emotion_details=[dict(type='自己理解',strength='medium')]if details is None else details)
    return PieceSourceSnapshot('ar04-synthetic-owner',record['id'],'emlis.current_input_bundle.v1',
        '\n\n'.join(record[k]for k in ('memo','memo_action')if record[k]),saved_original_json=canonical_json_bytes(record))

def produce(saved):
    meaning=build_piece_source_meaning(saved,expected_owner_id=saved.owner_id,expected_saved_input_id=saved.saved_input_id,expected_source_version=saved.source_version)
    plan=compile_piece_artifact_plan(meaning)
    artifact=realize_piece_artifact(meaning,plan,tier='free',requested_format=None)
    validate_source_meaning_preservation(meaning,plan,artifact)
    return meaning,plan,artifact

@pytest.mark.parametrize('role',['同僚','司書','配達員'])
@pytest.mark.parametrize('predicate',[
    '頼んだ','頼まなかった','頼みました','頼みませんでした','頼まれた','頼まれなかった','頼まれました','頼まれませんでした',
    '相談した','相談しなかった','相談しました','相談しませんでした','相談された','相談されなかった','相談されました','相談されませんでした',
    '伝えた','伝えなかった','伝えました','伝えませんでした','伝えられた','伝えられなかった','伝えられました','伝えられませんでした'])
@pytest.mark.parametrize('field',['memo','memo_action'])
def test_voice_negation_register_and_field_reach_actual_author(role,predicate,field):
    case = 'から' if predicate.startswith('伝えられ') else 'に'
    text=f'私は{role}{case}資料の確認を{predicate}。';saved=source(text,field=field);frozen=saved.saved_original_json
    meaning,plan,artifact=produce(saved)
    assert artifact.piece_text==text and artifact.body_blocks==(text,)
    assert [d.operation for d in plan.duties]==['KEEP_COMPLETE_SOURCE_CONTEXT']
    assert not plan.declaration_eligible and'declaration'not in artifact.eligible_formats
    assert piece_text_nodes(meaning)[0].value==text
    assert meaning.evidence[0].field_path==field and meaning.evidence[0].scalar_start==0 and meaning.evidence[0].scalar_end==len(text)
    assert saved.saved_original_json==frozen
    assert generate_piece_candidate(saved,authenticated_owner_id=saved.owner_id)['piece_text']==text

@pytest.mark.parametrize('subject',['私','わたし','僕','ぼく','俺','おれ'])
@pytest.mark.parametrize('case',['に','から'])
def test_written_self_and_passive_agent_case_remain_source_words(subject,case):
    text=f'{subject}は司書{case}展示の設営を頼まれた。'
    assert produce(source(text))[2].piece_text==text

@pytest.mark.parametrize('text',[
    '同僚に資料の確認を頼まれた。','同僚は司書に資料の確認を頼まれた。',
    '私は私に資料の確認を頼んだ。','私はあなたに資料の確認を頼んだ。',
    '私は彼に資料の確認を頼んだ。','私は本人に資料の確認を頼んだ。',
    '私はあなた様に資料の確認を頼んだ。','私は本人さんに資料の確認を頼んだ。',
    '私は私様に資料の確認を頼んだ。','私は僕さんに資料の確認を頼んだ。',
    '私はおれ氏に資料の確認を頼んだ。',
    '私は彼氏に資料の確認を頼んだ。',
    '私は誰に資料の確認を頼んだ。','私はどなたに資料の確認を頼んだ。',
    '私は田中さんに資料の確認を頼んだ。','私は友人の田中さんに資料の確認を頼んだ。',
    '私は同僚から資料の確認を頼んだ。','私は同僚に頼んだ。','私は資料の確認を頼んだ。',
    '私は同僚に先輩から資料の確認を頼まれた。','私は同僚に資料の確認を頼む。',
    '私は同僚に資料の確認を頼まない。','私は同僚に資料の確認を頼みたい。',
    '私は同僚に資料の確認を頼んだかもしれない。','もし私は同僚に資料の確認を頼んだなら。',
    '私は同僚に資料の確認を頼んだと聞いた。','「私は同僚に資料の確認を頼んだ」。',
    '私は同僚に資料の確認を頼んだ、。','私は同僚に資料の確認を頼んだ',
    '私は同僚に資料の確認を頼んだ！','私は同僚に資料の確認を頼んだ？',
    '私は同僚に資料の確認を頼った。'])
def test_new_scope_does_not_guess_roles_or_broaden_unread_grammar(text):
    assert not _finite_self_person_action_account(text)
    if text == '私は同僚に資料の確認を頼みたい。':
        # This wish was already an eligible literal self account. The new
        # past-event reader must not take ownership or revoke it.
        assert produce(source(text))[2].piece_text == text
        return
    with pytest.raises(PieceContractError):generate_piece_candidate(source(text),authenticated_owner_id='ar04-synthetic-owner')

@pytest.mark.parametrize('verb', ['相談した', '伝えた'])
@pytest.mark.parametrize('template', [
    '同僚に変更の内容を{verb}。', '私は私に変更の内容を{verb}。',
    '私はあなた様に変更の内容を{verb}。', '私は誰に変更の内容を{verb}。',
    '私は田中さんに変更の内容を{verb}。', '私は同僚から変更の内容を{verb}。',
    '私は同僚に変更の内容を{verb}かもしれない。',
    '私は同僚に変更の内容を{verb}と聞いた。',
    '私は同僚に変更の内容を{verb}なら。',
    '「私は同僚に変更の内容を{verb}」。',
    '私は同僚に変更の内容を{verb}？', '私は同僚に変更の内容を{verb}！',
])
def test_communication_does_not_bypass_unwritten_people_scope_or_questions(verb, template):
    text = template.format(verb=verb)
    assert not _finite_self_person_action_account(text)
    with pytest.raises(PieceContractError):
        generate_piece_candidate(source(text), authenticated_owner_id='ar04-synthetic-owner')

@pytest.mark.parametrize('ending', ['伝えられた', '伝えられなかった', '伝えられました', '伝えられませんでした'])
def test_ambiguous_ni_passive_is_not_reinterpreted_as_a_proven_event(ending):
    text = f'私は同僚に変更の内容を{ending}。'
    assert not _finite_self_person_action_account(text)
    with pytest.raises(PieceContractError):
        generate_piece_candidate(source(text), authenticated_owner_id='ar04-synthetic-owner')

@pytest.mark.parametrize('before',[True,False])
@pytest.mark.parametrize('field',['memo','memo_action'])
def test_reservation_keeps_order_field_and_unknown(before,field):
    event='私は同僚に資料の確認を頼まれた。';reservation='まだ、決めていません。'
    text=reservation+event if before else event+reservation
    meaning,plan,artifact=produce(source(text,field=field))
    assert artifact.piece_text==text and artifact.eligible_formats==('short_essay',)
    assert all(d.operation=='KEEP_COMPLETE_SOURCE_CONTEXT'for d in plan.duties)
    assert [e.field_path for e in meaning.evidence]==[field,field]

def test_fields_and_linebreaks_preserve_full_propositions():
    memo='まだ、決めていません。';action='私は司書から展示の設営を頼まれた。\n私は同僚に資料の確認を頼まなかった。'
    saved=source(action,other=memo);meaning,plan,artifact=produce(saved)
    assert artifact.body_blocks==(memo,*action.split('\n'))
    assert artifact.piece_text=='\n\n'.join(artifact.body_blocks)
    assert [e.field_path for e in meaning.evidence]==['memo','memo_action','memo_action']
    assert json.loads(saved.saved_original_json)['memo_action']==action
    assert '不安'not in artifact.piece_text and'引き受け'not in artifact.piece_text

def test_request_cannot_license_an_unread_other_sentence():
    for text in ['私は同僚に資料の確認を頼んだ。断片','私は同僚に資料の確認を頼んだ。私はたい。']:
        with pytest.raises(PieceContractError):generate_piece_candidate(source(text),authenticated_owner_id='ar04-synthetic-owner')

def test_existing_short_reservation_context_is_retained_without_certainty_or_excerpt():
    text='私は同僚に資料の確認を頼んだ。かもしれない。'
    _,plan,artifact=produce(source(text))
    assert artifact.piece_text==text and artifact.eligible_formats==('short_essay',)
    assert not plan.declaration_eligible

@pytest.mark.parametrize('emotion,strength',[('喜び','weak'),('悲しみ','medium'),('怒り','strong'),('不安','weak'),('平穏','medium')])
def test_selected_feelings_stay_private_without_explanation(emotion,strength):
    text='私は司書に展示の設営を頼まれた。'
    meaning,_,artifact=produce(source(text,emotions=[emotion],details=[dict(type=emotion,strength=strength)]))
    assert artifact.piece_text==text and meaning.selected_feelings and emotion not in artifact.piece_text

def test_no_selected_mode_or_unsaved_source_gets_new_admission():
    text='私は同僚に資料の確認を頼んだ。'
    for saved in [source(text,emotions=[],details=[]),replace(source(text),saved_original_json=None)]:
        with pytest.raises(PieceContractError):generate_piece_candidate(saved,authenticated_owner_id=saved.owner_id)

@pytest.mark.parametrize('mutation',['role','voice','negation','drop','extra'])
def test_existing_author_free_keep_check_rejects_rehashed_changes(mutation):
    text='私は同僚に資料の確認を頼まれなかった。まだ、決めていません。'
    meaning,plan,artifact=produce(source(text))
    changed={'role':text.replace('同僚','司書'),'voice':text.replace('頼まれなかった','頼まなかった'),
        'negation':text.replace('頼まれなかった','頼まれた'),'drop':text.split('。')[0]+'。','extra':text+'私は引き受けた。'}[mutation]
    damaged=replace(artifact,piece_text=changed,body_blocks=(changed,),piece_text_hash=hashlib.sha256(changed.encode()).hexdigest())
    with patch('cocolon_meaning_experience_engine.piece_v1c.compile_piece_artifact_plan',side_effect=AssertionError('compiler')), \
         patch('cocolon_meaning_experience_engine.piece_v1c.realize_piece_artifact',side_effect=AssertionError('author')):
        validate_source_meaning_preservation(meaning,plan,artifact)
        with pytest.raises(PieceContractError):validate_source_meaning_preservation(meaning,plan,damaged)

@pytest.mark.parametrize('tier',['free','plus','premium'])
def test_tiers_do_not_make_past_requests_declarations(tier):
    saved=source('私は同僚に資料の確認を頼んだ。')
    assert generate_piece_candidate(saved,authenticated_owner_id=saved.owner_id,tier=tier)['piece_text']==saved.original_text
    with pytest.raises(PieceContractError):generate_piece_candidate(saved,authenticated_owner_id=saved.owner_id,tier=tier,requested_format='declaration')

@pytest.mark.parametrize('text',['私は司書から展示の設営を頼まれた。','僕は同僚に資料の確認を頼まなかった。'])
def test_saved_original_sql_read_reaches_new_keep_without_writes(monkeypatch,text):
    import asyncio
    import api_account_visibility
    import emlis_thread_store
    from test_emlis_q2_application import Database
    from piece_v2_source_adapter import PieceSavedSourceAdapter
    owner='40000000-0000-4000-8000-000000000001'
    record_id='50000000-0000-4000-8000-000000000001'
    async def verify(token):
        assert token=='ar04-synthetic-session'
        return owner
    monkeypatch.setattr(api_account_visibility,'_resolve_user_id_from_token',verify)
    db=Database()
    try:
        assert 'code'not in db.query('insert into auth.users values ($1)',[owner])
        assert 'code'not in db.query("insert into public.profiles values ($1,'free')",[owner])
        assert 'code'not in db.query("insert into public.emotions values ($1,$2,now() at time zone 'UTC',null,$3,array['仕事'],array['自己理解'],$4::jsonb)",
            [record_id,owner,text,json.dumps([dict(type='自己理解',strength='medium')],ensure_ascii=False)])
        before=db.query('select * from public.emotions')
        monkeypatch.setattr(emlis_thread_store,'sb_post_rpc',db.rpc)
        candidate=asyncio.run(PieceSavedSourceAdapter().generate_original_candidate_for_development(
            'Bearer ar04-synthetic-session',record_id,source_stage='normal_observation'))
        assert candidate['piece_text']==text and candidate['production_enabled']is False
        assert candidate['record_effect']==candidate['quota_effect']==0
        assert db.query('select * from public.emotions')==before
        for table in ('emlis_input_threads','emlis_thread_events'):
            assert db.query('select count(*)::int as n from public.'+table)['rows'][0]['n']==0
    finally:
        db.proc.stdin.close();db.proc.wait(timeout=10)

