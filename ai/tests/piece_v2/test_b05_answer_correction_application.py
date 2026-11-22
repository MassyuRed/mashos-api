"""Real saved ANSWER prefixes plus proper corrections reach the Piece lifecycle.

The bearer identity and Emlis reply provider are synthetic. The application,
source/checkpoint admission, author, independent review and disposable SQL are
real. These tests do not exercise a GPU, a native bitmap or a person's account.
"""
import asyncio
from contextlib import ExitStack
from copy import deepcopy
from dataclasses import replace
import json
from unittest.mock import patch
from uuid import uuid4

import httpx
import pytest
from fastapi import FastAPI

import api_piece_v2
from cocolon_meaning_experience_engine.natural_reply import NaturalReply
from emlis_thread_service import EmlisThreadService, Q3_PROFILE
from piece_v2_contract import PieceContractError
from piece_v2_owner_service import PieceOwnerService, _COLUMNS
from piece_v2_preview_service import PiecePreviewService, _REPLAY_COLUMNS
from piece_v2_save_service import PieceSaveService
from piece_v2_source_adapter import PieceSavedSourceAdapter, project_saved_corrected_source, project_saved_refined_fence
from piece_v2_source_ref_http import source_ref_router
from test_b05_interpretation_correction_application import corrected_db
from test_b05_effective_round_sql_fence import effective_fence_db, _apply
from test_b05_natural_refined_saved_pipeline import _prepare_natural, natural_refined_db, refined_pipeline_db, saved_piece_db
from test_b05_piece_answer_update_saved_pipeline import ANSWERS, prepare_later_update
from test_b05_refined_source_fence_sql import rpc

run = asyncio.run
MIGRATION = '20261115005742_piece_answer_and_interpretation_corrections.sql'
RENDERER = 'piece.rn_bitmap_renderer.ios.v2'
ACTION = '私は資料を調べた。'
LATEST_ADD = '私は嬉しかった。'
EXPLANATIONS = {
    'REVISE': '「私は資料を調べた」ではなく「私は約束を守りたい」です。',
    'WITHDRAW': '「私は資料を調べた」は取り消します。',
}


@pytest.fixture(scope='module')
def answer_correction_db(corrected_db):
    _apply(corrected_db, MIGRATION)
    corrected_db.answer_correction_writer_md5 = corrected_db.query("""
        select p.proname, md5(pg_get_functiondef(p.oid)) as definition_md5
        from pg_proc p where p.oid in (
            'public.piece_issue_preview_v2(uuid,text,text,jsonb,integer,text,jsonb)'::regprocedure,
            'public.piece_mutate_preview_visual_v2(uuid,uuid,bigint,jsonb,jsonb,text,text,jsonb)'::regprocedure,
            'public.piece_save_v2(uuid,uuid,bigint,text,text,text,text,text,text,jsonb,boolean)'::regprocedure)
        order by p.proname
    """)['rows']
    return corrected_db


def answer_correction_case(db, monkeypatch, *, tier='free', rounds=1,
                           operation='REVISE', answer_operation='ADD', issue=True,
                           extra_explanations=(), meeting=False):
    if meeting:
        texts = ['会議がうまくできませんでした']
        state, _, answer_calls = _prepare_natural(db, monkeypatch, tier=tier,
            memo_text='つらかったんです', first_answer=texts[0])
        assert state['initial_dto']['pending_question']['text'] == 'なにがつらかったんですか？'
        explanation = '「つらかったんです」ではなく「私は不安だった」です。'
    else:
        # Earlier opaque, unselected ADDs qualify history without being promoted
        # to Analysis claims or included in the selected Piece body.
        texts = ['私は怖かった。'] * (rounds - 1) + [
            LATEST_ADD if answer_operation == 'ADD' else ANSWERS[answer_operation]]
        state, _, answer_calls = prepare_later_update(db, monkeypatch, rounds,
            answer_operation, tier, action_text=ACTION, answer_texts=texts)
        explanation = EXPLANATIONS[operation]
    owner, parent, token = state['owner'], state['source_id'], state['token']
    correction_calls = []

    async def provider(material):
        correction_calls.append(material)
        return NaturalReply('記録を受け取る合成の返事です。',
            'synthetic-answer-correction-provider', material.source_prefix_ref)

    service = EmlisThreadService(runtime_profile=Q3_PROFILE, natural_reply_source=provider)
    previous = state['completed_dto']
    updated = run(service.correct_interpretation(owner, previous['thread_id'],
        expected_revision=previous['revision'], idempotency_key='mixed-proper-correction',
        target_event_id=previous['current_observation']['event_id'], target_text='記録を受け取る',
        explanation=explanation))
    assert updated['state'] == 'COMPLETED' and updated['body_state'] == 'FINAL'
    assert updated['correction_saved'] and updated['answer_saved']
    assert updated['answer_assessment'] == 'RESOLVED' and updated['meaning_updated'] is False
    for index, explanation in enumerate(extra_explanations, 2):
        updated = run(service.correct_interpretation(owner, updated['thread_id'],
            expected_revision=updated['revision'], idempotency_key='mixed-proper-correction-'+str(index),
            target_event_id=updated['current_observation']['event_id'], target_text='記録を受け取る',
            explanation=explanation))
        assert updated['state'] == 'COMPLETED' and updated['correction_saved']
    snapshot = run(service.store.read(owner, input_id=parent))
    selected = state['snapshot_before']['thread']['latest_answer_event_id']
    adapter = PieceSavedSourceAdapter()
    handoff = run(adapter.resolve_corrected_handoff('Bearer '+token, parent,
        supplemental_answer_identity=selected))
    reference = run(adapter.resolve_refined_source_ref('Bearer '+token, parent,
        supplemental_answer_identity=selected, opted_in=True))
    assert reference['emlis_observation_stage'] == 'corrected_observation'
    assert reference['emlis_observation_result_identity'] == updated['current_observation']['event_id']
    assert reference['supplemental_answer_identity'] == selected
    assert reference['question_need_decision_identity'] == next(e['id'] for e in snapshot['events']
        if e['kind'] == 'QUESTION' and e['round_index'] == rounds)
    request = dict(source_ref=reference, requested_format=None,
        visual_selection=dict(theme_id=None, aspect_ratio=None, branding_mode=None))

    async def load_record(who, pid):
        rows = db.query('select to_jsonb(r) as row from public.piece_records r '
            'where owner_user_id=$1 and id=$2', [who, pid], 'service_role')['rows']
        return rows[0]['row'] if rows else None

    async def load_preview(who, pid):
        row = await load_record(who, pid)
        return {key: row[key] for key in _REPLAY_COLUMNS} if row else None

    async def call(name, args):
        result = rpc(db, name, args)
        if 'code' in result:
            raise PieceContractError(result['message'])
        return result

    preview = (PiecePreviewService(source_adapter=adapter) if meeting
        else PiecePreviewService(source_adapter=adapter, model_source=None))
    issue_args = dict(idempotency_key='mixed-piece-preview', ttl_seconds=600,
        renderer_version=RENDERER, allowed_renderers=(RENDERER,),
        expected_subscription_tier=tier, load_record=load_preview, rpc=call)
    issued = run(preview.issue_original('Bearer '+token, request, **issue_args)) if issue else None
    record = run(load_record(owner, issued['preview_id'])) if issued else None
    expected = dict(original=snapshot['original'], thread_id=handoff.thread_id,
        thread_revision=handoff.thread_revision, lineage=handoff.lineage_payload(),
        **project_saved_refined_fence(handoff))
    return dict(owner=owner, parent=parent, source_id=parent, token=token, service=service,
        adapter=adapter, handoff=handoff, snapshot=snapshot, source_ref=reference,
        request=request, preview=preview, issued=issued, record=record, expected=expected,
        load_record=load_record, load_preview=load_preview, rpc=call, issue_args=issue_args,
        initial=state['initial_dto'], answer_state=state, updated=updated,
        answer_calls=answer_calls, correction_calls=correction_calls,
        answer_texts=texts, selected_answer_id=selected, extra_explanations=extra_explanations)


def _finish_saved_case(case, db, tier):
    owner, token, first = case['owner'], case['token'], case['issued']
    visual = run(case['preview'].mutate_original_visual('Bearer '+token,
        authenticated_user_id=owner, preview_id=first['preview_id'],
        request=dict(expected_preview_revision=first['preview_revision'],
            visual_selection=dict(theme_id='quiet_night', aspect_ratio=None, branding_mode=None)),
        expected_subscription_tier=tier, load_record=case['load_preview'], rpc=case['rpc'],
        allowed_renderers=(RENDERER,)))
    for key in ('piece_text', 'piece_text_hash', 'content_payload', 'content_payload_hash'):
        assert visual[key] == first[key]
    save_request = dict(preview_id=visual['preview_id'], expected_preview_revision=visual['preview_revision'],
        **{key: visual[key] for key in ('piece_text_hash', 'content_payload_hash', 'visual_recipe_hash')})

    def forbidden(*args, **kwargs):
        pytest.fail('saved/replayed mixed Piece must not generate or acquire a model')

    with ExitStack() as stack:
        for name in ('piece_v2_preview_service.generate_piece_candidate',
                     'cocolon_meaning_experience_engine.piece_v1c.realize_piece_artifact',
                     'cocolon_meaning_experience_engine.engine.MeaningExperienceEngine.generate',
                     'piece_model_source.call_piece_model_source'):
            stack.enter_context(patch(name, side_effect=forbidden))
        replay = run(PiecePreviewService(model_source=None).issue_original('Bearer '+token,
            case['request'], **case['issue_args']))
        assert replay['idempotency_replayed'] and replay['piece_text'] == visual['piece_text']
        kwargs = dict(authenticated_user_id=owner, request=save_request,
            idempotency_key='mixed-piece-save', allowed_renderers=(RENDERER,))
        saved = run(PieceSaveService(load_record=case['load_record'], rpc=case['rpc']).save('Bearer '+token, **kwargs))
        again = run(PieceSaveService(load_record=case['load_record'], rpc=case['rpc']).save('Bearer '+token, **kwargs))
        assert again == dict(saved, idempotency_replayed=True)

        async def load_saved(params):
            row = await case['load_record'](owner, params['id'][3:])
            return [{key: row[key] for key in _COLUMNS}] if row and row['lifecycle_status'] == 'saved' else []

        # A new reader has no preview/service memory and uses the stored artifact.
        detail = run(PieceOwnerService(load_records=load_saved).detail(
            authenticated_user_id=owner, piece_id=saved['piece_id']))
        for key in ('piece_text', 'piece_text_hash', 'content_payload', 'content_payload_hash',
                    'visual_recipe_hash', 'renderer_version'):
            assert detail[key] == visual[key]
    after = run(case['service'].store.read(owner, input_id=case['parent']))
    for key in ('original', 'thread', 'events'):
        assert after[key] == case['snapshot'][key]
    assert len(case['answer_calls']) == len(case['answer_texts']) + 1
    assert len(case['correction_calls']) == 1 + len(case['extra_explanations'])
    assert db.query('select count(*)::int as n from public.piece_quota_consumptions '
        'where owner_user_id=$1', [owner])['rows'][0]['n'] == 1
    return visual, detail


@pytest.mark.parametrize('answer_surface', ['会議がうまくできませんでした。',
    '会議がうまくできました。', 'というのも、会議がうまくできませんでした。'])
def test_proved_meeting_circumstance_survives_correction_without_old_feeling_or_relation(
        answer_correction_db, monkeypatch, answer_surface):
    from cocolon_meaning_experience_engine.piece_v1c import MODEL_REALIZATION_PROFILE
    from test_b05_piece_model_saved_pipeline import _provider

    case_id = 'corrected-meeting'
    correction_surface = '私は不安だった。'
    seen = _provider(monkeypatch, case_id, [answer_surface, correction_surface],
        realization_profile=MODEL_REALIZATION_PROFILE)
    case = answer_correction_case(answer_correction_db, monkeypatch, issue=False, meeting=True)
    handoff = case['handoff']
    assert handoff.original_active_ranges == ()
    assert handoff.circumstance_control.answer.answer_id == case['selected_answer_id']
    with pytest.raises(PieceContractError, match='piece_correction_selected_answer_pending'):
        project_saved_corrected_source(replace(handoff, circumstance_control=None))
    unrelated = replace(handoff.circumstance_control,
        question=replace(handoff.circumstance_control.question, prompt_private='別の質問ですか？'))
    with pytest.raises(PieceContractError, match='PIECE_CONFLICT'):
        project_saved_corrected_source(replace(handoff, circumstance_control=unrelated))

    def issue():
        return run(case['preview'].issue_original('Bearer '+case['token'], case['request'], **case['issue_args']))

    if answer_surface != '会議がうまくできませんでした。':
        with pytest.raises(PieceContractError, match='PIECE_SOURCE_NOT_ELIGIBLE'):
            issue()
        assert len(seen) == 1
        return
    case['issued'] = issue()
    assert len(seen) == 1
    wire = seen[0]['messages'][1]['content']
    assert 'つらかった' not in wire and '記録を受け取る' not in wire and 'feeling_circumstance' not in wire
    assert '会議がうまくできませんでした' in wire and '私は不安だった' in wire
    assert case['issued']['piece_text'] == answer_surface + '\n\n' + correction_surface
    _finish_saved_case(case, answer_correction_db, 'free')
    assert len(seen) == 1


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
@pytest.mark.parametrize('rounds', [1, 2, 3])
@pytest.mark.parametrize('operation', ['REVISE', 'WITHDRAW'])
def test_selected_answer_and_proper_correction_reach_saved_non_generating_read(
        answer_correction_db, monkeypatch, tier, rounds, operation, tmp_path):
    case = answer_correction_case(answer_correction_db, monkeypatch,
        tier=tier, rounds=rounds, operation=operation)
    text = case['issued']['piece_text']
    assert LATEST_ADD in text and '私は怖かった。' not in text
    assert '仕事を続けたい' in text
    assert '資料を調べた' not in text and '記録を受け取る' not in text
    assert ('私は約束を守りたい' in text) == (operation == 'REVISE')
    visual, detail = _finish_saved_case(case, answer_correction_db, tier)
    (tmp_path/'mixed_piece_evidence.json').write_text(json.dumps(dict(
        tier=tier, rounds=rounds, operation=operation, original=case['snapshot']['original'],
        selected_answer=LATEST_ADD, explanation=EXPLANATIONS[operation], preview=case['issued'],
        selected=visual, detail=detail, original_and_emlis_unchanged=True,
        writer_definition_md5=answer_correction_db.answer_correction_writer_md5,
        quota_consumptions=1), ensure_ascii=False, indent=2)+'\n')


@pytest.mark.parametrize('answer_operation', ['REVISE', 'WITHDRAW'])
@pytest.mark.parametrize('operation', ['REVISE', 'WITHDRAW'])
def test_distinct_original_answer_update_and_proper_correction_preserve_effective_sources(
        answer_correction_db, monkeypatch, answer_operation, operation):
    case = answer_correction_case(answer_correction_db, monkeypatch,
        answer_operation=answer_operation, operation=operation)
    text = case['issued']['piece_text']
    assert '仕事を続けたい' not in text and '資料を調べた' not in text
    assert ('私は家族を守りたい' in text) == (answer_operation == 'REVISE')
    assert ('私は約束を守りたい' in text) == (operation == 'REVISE')
    _finish_saved_case(case, answer_correction_db, 'free')


@pytest.mark.parametrize('change', ['no_selection', 'old_answer', 'foreign_answer', 'opt_out', 'old_observation'])
def test_mixed_source_requires_explicit_current_answer_and_observation(
        answer_correction_db, monkeypatch, change):
    case = answer_correction_case(answer_correction_db, monkeypatch, rounds=2, issue=False)
    adapter, auth = case['adapter'], 'Bearer '+case['token']
    with patch('piece_v2_preview_service.generate_piece_candidate',
               side_effect=AssertionError('rejected source reached the author')):
        with pytest.raises(PieceContractError):
            if change == 'no_selection':
                run(adapter.resolve_original_source_ref(auth, case['parent']))
            elif change in ('old_answer', 'foreign_answer', 'opt_out'):
                answer = (case['handoff'].answer_sources[0].answer_id if change == 'old_answer' else
                    str(uuid4()) if change == 'foreign_answer' else case['selected_answer_id'])
                run(adapter.resolve_refined_source_ref(auth, case['parent'],
                    supplemental_answer_identity=answer, opted_in=change != 'opt_out'))
            else:
                request = deepcopy(case['request'])
                request['source_ref']['emlis_observation_result_identity'] = (
                    case['answer_state']['completed_dto']['current_observation']['event_id'])
                run(case['preview'].issue_original(auth, request, **case['issue_args']))


def test_new_proper_correction_invalidates_existing_mixed_preview_before_save(
        answer_correction_db, monkeypatch):
    case = answer_correction_case(answer_correction_db, monkeypatch)
    dto = case['updated']
    changed = run(case['service'].correct_interpretation(case['owner'], dto['thread_id'],
        expected_revision=dto['revision'], idempotency_key='mixed-subsequent-explanation',
        target_event_id=dto['current_observation']['event_id'], target_text='記録を受け取る',
        explanation='「私は仕事を続けたい」は取り消します。'))
    assert changed['correction_saved'] and changed['revision'] > dto['revision']
    first = case['issued']
    request = dict(preview_id=first['preview_id'], expected_preview_revision=first['preview_revision'],
        **{key: first[key] for key in ('piece_text_hash', 'content_payload_hash', 'visual_recipe_hash')})
    with pytest.raises(PieceContractError):
        run(PieceSaveService(load_record=case['load_record'], rpc=case['rpc']).save(
            'Bearer '+case['token'], authenticated_user_id=case['owner'], request=request,
            idempotency_key='stale-mixed-save', allowed_renderers=(RENDERER,)))
    assert answer_correction_db.query('select count(*)::int as n from public.piece_quota_consumptions '
        'where owner_user_id=$1', [case['owner']])['rows'][0]['n'] == 0


def test_real_mixed_source_ref_http_keeps_selected_identity_and_seven_public_fields(
        answer_correction_db, monkeypatch):
    case = answer_correction_case(answer_correction_db, monkeypatch, issue=False)
    async def verify(authorization):
        assert authorization == 'Bearer '+case['token']
        return case['owner']
    monkeypatch.setattr(api_piece_v2, '_verify_bearer', verify)
    app = FastAPI()
    app.state.piece_v2_runtime = dict(
        requested={'piece_v2_preview_enabled': True}, ready={'piece_v2_preview_enabled': True})
    app.include_router(source_ref_router)

    async def send():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
            return await client.get('/emotion/piece/source-ref/'+case['parent'],
                params={'supplemental_answer_identity': case['selected_answer_id']},
                headers={'Authorization': 'Bearer '+case['token']})

    response = run(send())
    assert response.status_code == 200, response.json()
    assert response.json() == case['source_ref'] and len(response.json()) == 7
    assert response.headers['cache-control'] == 'no-store'
    assert case['owner'] not in response.text and case['token'] not in response.text
