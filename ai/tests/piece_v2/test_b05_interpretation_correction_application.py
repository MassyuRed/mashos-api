"""Two-input correction -> native Piece -> SQL save and non-generating reread.

Only the recipient provider and bearer identity are synthetic. The ordinary
source, author, independent review, preview, visual and persistence run here.
This does not exercise a GPU, native bitmap or a real person's account.
"""
import asyncio
from contextlib import ExitStack
from copy import deepcopy
import json
from unittest.mock import patch
from uuid import uuid4

import pytest
import api_account_visibility
import emlis_thread_store
from emlis_thread_service import EmlisThreadService, Q3_PROFILE
from cocolon_meaning_experience_engine.natural_reply import NaturalReply
from piece_v2_contract import PieceContractError
from piece_v2_preview_service import PiecePreviewService, _REPLAY_COLUMNS
from piece_v2_source_adapter import PieceSavedSourceAdapter, project_saved_refined_fence
from piece_v2_save_service import PieceSaveService
from piece_v2_owner_service import PieceOwnerService, _COLUMNS
from test_cmee_piece_request_saved_pipeline import saved_piece_db
from test_b05_refined_preview_saved_pipeline import refined_pipeline_db
from test_b05_natural_refined_saved_pipeline import natural_refined_db, _bind
from test_b05_effective_round_sql_fence import effective_fence_db, _apply
from test_b05_refined_source_fence_sql import _update, rpc

run = asyncio.run
MIGRATION = '20261114213309_piece_interpretation_correction_source.sql'
HISTORY_MIGRATION = '20261114235041_piece_multiple_interpretation_corrections.sql'
MEMO = '私は本を読みたい。私は仕事を続けたい。'
EXPLANATIONS = {
    'REVISE': '「私は仕事を続けたい」ではなく「私は家族を守りたい」です。',
    'WITHDRAW': '「私は仕事を続けたい」は取り消します。',
}


@pytest.fixture(scope='module')
def corrected_db(effective_fence_db):
    _apply(effective_fence_db, MIGRATION)
    _apply(effective_fence_db, HISTORY_MIGRATION)
    return effective_fence_db


def corrected_case(natural_case, db, monkeypatch, *, operation='REVISE', tier='free', issue=True, memo_action='', memo=MEMO, extra_explanations=()):
    owner, parent, token = str(uuid4()), str(uuid4()), 'synthetic-corrected-piece'
    _update(db, 'insert into auth.users values ($1)', [owner])
    _update(db, 'insert into public.profiles values ($1,$2)', [owner, tier])
    _update(db, "insert into public.emotions values ($1,$2,(now()-interval '5 seconds') at time zone 'UTC',$3,$4,array['仕事'],array['平穏'],$5::jsonb)",
        [parent, owner, memo, memo_action, json.dumps([dict(type='平穏', strength='medium')], ensure_ascii=False)])
    _bind(db, monkeypatch, owner, token)
    calls = []
    async def provider(material):
        calls.append(material)
        return NaturalReply('少し安心できたと受け取りました。', 'synthetic-corrected-provider', material.source_prefix_ref)
    service = EmlisThreadService(runtime_profile=Q3_PROFILE, natural_reply_source=provider)
    initial = run(service.start(owner, parent))
    assert initial['state'] == 'COMPLETED' and initial['issued_count'] == 0, initial
    updated = run(service.correct_interpretation(owner, initial['thread_id'],
        expected_revision=initial['revision'], idempotency_key='corrected-piece-explanation',
        target_event_id=initial['current_observation']['event_id'], target_text='少し安心できた',
        explanation=EXPLANATIONS[operation]))
    assert updated['state'] == 'COMPLETED' and updated['body_state'] == 'FINAL', updated
    assert updated['correction_saved'] and updated['correction_assessment'] == 'UNASSESSED'
    for i, explanation in enumerate(extra_explanations, 2):
        updated = run(service.correct_interpretation(owner, initial['thread_id'],
            expected_revision=updated['revision'], idempotency_key=f'corrected-piece-explanation-{i}',
            target_event_id=updated['current_observation']['event_id'], target_text='少し安心できた',
            explanation=explanation))
        assert updated['correction_saved'] and updated['state'] == 'COMPLETED', updated
    snapshot = run(service.store.read(owner, input_id=parent))
    adapter = PieceSavedSourceAdapter()
    handoff = run(adapter.resolve_corrected_handoff('Bearer '+token, parent))
    reference = run(adapter.resolve_original_source_ref('Bearer '+token, parent))
    assert reference['emlis_observation_stage'] == 'corrected_observation'
    assert reference['emlis_observation_result_identity'] == updated['current_observation']['event_id']
    assert reference['question_need_decision_identity'] is reference['supplemental_answer_identity'] is None
    request = dict(source_ref=reference, requested_format=None,
        visual_selection=dict(theme_id=None, aspect_ratio=None, branding_mode=None))

    async def load_record(who, pid):
        rows = db.query('select to_jsonb(r) as row from public.piece_records r where owner_user_id=$1 and id=$2',
            [who, pid], 'service_role')['rows']
        return rows[0]['row'] if rows else None
    async def load_preview(who, pid):
        row = await load_record(who, pid)
        return {key: row[key] for key in _REPLAY_COLUMNS} if row else None
    async def call(name, args):
        result = rpc(db, name, args)
        if 'code' in result:
            raise PieceContractError(result['message'])
        return result
    preview = PiecePreviewService(source_adapter=adapter, model_source=None)
    issue_args = dict(idempotency_key='corrected-piece-preview', ttl_seconds=600,
        renderer_version='piece.rn_bitmap_renderer.ios.v2', allowed_renderers=('piece.rn_bitmap_renderer.ios.v2',),
        expected_subscription_tier=tier, load_record=load_preview, rpc=call)
    issued = run(preview.issue_original('Bearer '+token, request, **issue_args)) if issue else None
    record = run(load_record(owner, issued['preview_id'])) if issued else None
    expected = dict(original=snapshot['original'], thread_id=handoff.thread_id,
        thread_revision=handoff.thread_revision, lineage=handoff.lineage_payload(),
        **project_saved_refined_fence(handoff))
    return dict(owner=owner, parent=parent, source_id=parent, token=token,
        service=service, adapter=adapter, handoff=handoff, preview=preview,
        issued=issued, source_ref=reference, request=request, record=record,
        expected=expected, snapshot=snapshot, calls=calls, initial=initial, updated=updated,
        issue_args=issue_args, load_record=load_record, load_preview=load_preview, rpc=call)


@pytest.mark.parametrize('tier,operation,memo_action', [
    (tier, operation, '') for tier in ('free', 'plus', 'premium') for operation in ('REVISE', 'WITHDRAW')
] + [('premium', 'REVISE', '私は資料を調べた。')])
def test_correction_explanation_reaches_normal_preview_visual_save_and_reread(corrected_db, monkeypatch, operation, tier, memo_action, tmp_path):
    case = corrected_case(None, corrected_db, monkeypatch, operation=operation, tier=tier, memo_action=memo_action)
    owner, token, first = case['owner'], case['token'], case['issued']
    assert '私は仕事を続けたい' not in first['piece_text']
    assert '私は本を読みたい' in first['piece_text']
    if memo_action:
        assert memo_action in first['piece_text']
    assert ('私は家族を守りたい' in first['piece_text']) == (operation == 'REVISE')
    assert '少し安心できた' not in first['piece_text'] and 'ではなく' not in first['piece_text']
    # The reply remains unassessed; Piece's own source proof does not rewrite
    # Emlis receipt state or turn its prose into a person statement.
    assert case['updated']['meaning_updated'] is False and len(case['calls']) == 2
    visual = run(case['preview'].mutate_original_visual('Bearer '+token,
        authenticated_user_id=owner, preview_id=first['preview_id'],
        request=dict(expected_preview_revision=first['preview_revision'],
            visual_selection=dict(theme_id='quiet_night', aspect_ratio=None, branding_mode=None)),
        expected_subscription_tier=tier, load_record=case['load_preview'], rpc=case['rpc'],
        allowed_renderers=('piece.rn_bitmap_renderer.ios.v2',)))
    for key in ('piece_text', 'piece_text_hash', 'content_payload', 'content_payload_hash'):
        assert visual[key] == first[key]
    save_request = dict(preview_id=visual['preview_id'], expected_preview_revision=visual['preview_revision'],
        **{key: visual[key] for key in ('piece_text_hash', 'content_payload_hash', 'visual_recipe_hash')})
    def forbidden(*args, **kwargs):
        pytest.fail('saved/replay must not invoke an author or model')
    with ExitStack() as stack:
        for path in ('piece_v2_preview_service.generate_piece_candidate',
                     'cocolon_meaning_experience_engine.piece_v1c.realize_piece_artifact',
                     'cocolon_meaning_experience_engine.engine.MeaningExperienceEngine.generate',
                     'piece_model_source.call_piece_model_source'):
            stack.enter_context(patch(path, side_effect=forbidden))
        replay = run(PiecePreviewService(model_source=None).issue_original('Bearer '+token,
            case['request'], **case['issue_args']))
        assert replay['piece_text'] == visual['piece_text'] and replay['idempotency_replayed']
        save_service = PieceSaveService(load_record=case['load_record'], rpc=case['rpc'])
        kwargs = dict(authenticated_user_id=owner, request=save_request,
            idempotency_key='corrected-piece-save', allowed_renderers=('piece.rn_bitmap_renderer.ios.v2',))
        saved = run(save_service.save('Bearer '+token, **kwargs))
        again = run(save_service.save('Bearer '+token, **kwargs))
        assert again == dict(saved, idempotency_replayed=True)
        async def load_saved(params):
            row = await case['load_record'](owner, params['id'][3:])
            return [{key: row[key] for key in _COLUMNS}] if row and row['lifecycle_status'] == 'saved' else []
        detail = run(PieceOwnerService(load_records=load_saved).detail(
            authenticated_user_id=owner, piece_id=saved['piece_id']))
        assert detail['piece_text'] == visual['piece_text']
        assert detail['content_payload_hash'] == visual['content_payload_hash']
        assert detail['visual_recipe_hash'] == visual['visual_recipe_hash']
    after = run(case['service'].store.read(owner, input_id=case['parent']))
    for key in ('original', 'thread', 'events'):
        assert after[key] == case['snapshot'][key]
    assert len(case['calls']) == 2
    assert corrected_db.query('select count(*)::int as n from public.piece_quota_consumptions where owner_user_id=$1',
        [owner])['rows'][0]['n'] == 1
    # Export only this test's fictional product, for whole-output review.
    (tmp_path/'corrected_piece_evidence.json').write_text(json.dumps(dict(
        tier=tier, operation=operation, original=case['snapshot']['original'],
        explanation=EXPLANATIONS[operation], source_lineage=case['handoff'].lineage_payload(),
        preview=first, selected=visual, detail=detail, provider_calls=len(case['calls']),
        original_and_emlis_unchanged=True, quota_consumptions=1), ensure_ascii=False, indent=2)+'\n')


@pytest.mark.parametrize('change', ['edit', 'delete', 'second_correction', 'needs_detail'])
def test_current_source_change_prevents_old_preview_or_save(corrected_db, monkeypatch, change):
    case = corrected_case(None, corrected_db, monkeypatch)
    db, owner = corrected_db, case['owner']
    if change == 'edit':
        _update(db, "update public.emotions set memo=memo||'私は資料を読んだ。' where id=$1", [case['parent']])
    elif change == 'delete':
        _update(db, 'delete from public.emotions where id=$1', [case['parent']])
    else:
        dto = case['updated']
        updated = run(case['service'].correct_interpretation(owner, dto['thread_id'],
            expected_revision=dto['revision'], idempotency_key='second-piece-correction',
            target_event_id=dto['current_observation']['event_id'], target_text='少し安心できた',
            explanation='違います。' if change == 'needs_detail' else '「私は本を読みたい」は取り消します。'))
        assert updated['correction_saved']
    first = case['issued']
    request = dict(preview_id=first['preview_id'], expected_preview_revision=first['preview_revision'],
        **{key: first[key] for key in ('piece_text_hash', 'content_payload_hash', 'visual_recipe_hash')})
    with pytest.raises(PieceContractError):
        run(PieceSaveService(load_record=case['load_record'], rpc=case['rpc']).save('Bearer '+case['token'],
            authenticated_user_id=owner, request=request, idempotency_key='changed-source-save',
            allowed_renderers=('piece.rn_bitmap_renderer.ios.v2',)))
    assert db.query('select count(*)::int as n from public.piece_quota_consumptions where owner_user_id=$1',
        [owner])['rows'][0]['n'] == 0


@pytest.mark.parametrize('change', ['finish_time', 'answer_assessment', 'correction_question'])
def test_impossible_saved_controls_reject_before_piece_author(corrected_db, monkeypatch, change):
    case = corrected_case(None, corrected_db, monkeypatch, issue=False)
    events = case['snapshot']['events']
    correction = next(e for e in events if e['payload'].get('stage') == 'INTERPRETATION_CORRECTION')
    if change == 'finish_time':
        finish = next(e for e in events if e['kind'] == 'OPERATION'
            and e['operation_id'] == correction['operation_id'] and e['payload'].get('status') == 'COMPLETED')
        _update(corrected_db, 'update public.emlis_thread_events set recorded_at=$2 where id=$1',
            [finish['id'], events[0]['recorded_at']])
    elif change == 'answer_assessment':
        data = deepcopy(case['snapshot']['thread']['data']); data['answer_assessment'] = 'RESOLVED'
        _update(corrected_db, 'update public.emlis_input_threads set data=$2::jsonb where id=$1',
            [case['handoff'].thread_id, json.dumps(data)])
    else:
        _update(corrected_db, 'update public.emlis_thread_events set question_id=$2 where id=$1',
            [correction['id'], 'not-a-real-question'])
    with patch('piece_v2_preview_service.generate_piece_candidate', side_effect=AssertionError('author reached')):
        with pytest.raises(PieceContractError, match='PIECE_SOURCE_NOT_ELIGIBLE'):
            run(case['adapter'].resolve_original_source_ref('Bearer '+case['token'], case['parent']))



@pytest.mark.parametrize('tier', ['free','plus','premium'])
@pytest.mark.parametrize('first,second', [(a,b) for a in ('REVISE','WITHDRAW') for b in ('REVISE','WITHDRAW')])
def test_complete_correction_history_reaches_saved_piece(corrected_db, monkeypatch, tier, first, second, tmp_path):
    explanation = ('「私は資料を調べた」ではなく「私は約束を守りたい」です。'
        if second == 'REVISE' else '「私は資料を調べた」は取り消します。')
    case = corrected_case(None, corrected_db, monkeypatch, operation=first, tier=tier,
        memo=MEMO,
        memo_action='私は資料を調べた。', extra_explanations=(explanation,))
    owner, token, preview = case['owner'], case['token'], case['issued']
    text = preview['piece_text']
    assert '私は本を読みたい。' in text
    assert ('私は家族を守りたい' in text) == (first == 'REVISE')
    assert ('私は約束を守りたい' in text) == (second == 'REVISE')
    assert '私は仕事を続けたい' not in text and '私は資料を調べた' not in text
    assert 'ではなく' not in text and '少し安心できた' not in text
    assert len(case['handoff'].prior_corrections) == 1 and len(case['calls']) == 3
    visual = run(case['preview'].mutate_original_visual('Bearer '+token,
        authenticated_user_id=owner, preview_id=preview['preview_id'],
        request=dict(expected_preview_revision=preview['preview_revision'],
            visual_selection=dict(theme_id='quiet_night', aspect_ratio=None, branding_mode=None)),
        expected_subscription_tier=tier, load_record=case['load_preview'], rpc=case['rpc'],
        allowed_renderers=('piece.rn_bitmap_renderer.ios.v2',)))
    assert visual['piece_text'] == text
    request = dict(preview_id=visual['preview_id'], expected_preview_revision=visual['preview_revision'],
        **{k:visual[k] for k in ('piece_text_hash','content_payload_hash','visual_recipe_hash')})
    with patch('piece_v2_preview_service.generate_piece_candidate', side_effect=AssertionError('reread generated')):
        replay = run(PiecePreviewService(model_source=None).issue_original('Bearer '+token,
            case['request'], **case['issue_args']))
        assert replay['piece_text'] == text and replay['idempotency_replayed']
        saver = PieceSaveService(load_record=case['load_record'], rpc=case['rpc'])
        kwargs = dict(authenticated_user_id=owner, request=request, idempotency_key='multi-corrected-save',
            allowed_renderers=('piece.rn_bitmap_renderer.ios.v2',))
        saved = run(saver.save('Bearer '+token, **kwargs))
        assert run(saver.save('Bearer '+token, **kwargs)) == dict(saved,idempotency_replayed=True)
        async def load(params):
            row = await case['load_record'](owner,params['id'][3:])
            return [{k:row[k] for k in _COLUMNS}] if row and row['lifecycle_status']=='saved' else []
        detail = run(PieceOwnerService(load_records=load).detail(authenticated_user_id=owner,piece_id=saved['piece_id']))
        for key in ('piece_text','piece_text_hash','content_payload','content_payload_hash','visual_recipe','visual_recipe_hash','renderer_version'):
            assert detail[key] == visual[key]
    after = run(case['service'].store.read(owner,input_id=case['parent']))
    assert all(after[k] == case['snapshot'][k] for k in ('original','thread','events'))
    assert len(case['calls']) == 3
    assert corrected_db.query('select count(*)::int as n from public.piece_quota_consumptions where owner_user_id=$1',[owner])['rows'][0]['n']==1
    (tmp_path/'multi_corrected_piece.json').write_text(json.dumps(dict(tier=tier,operations=[first,second],
        original=after['original'],explanations=[EXPLANATIONS[first],explanation],preview=preview,selected=visual,
        detail=detail,original_and_emlis_unchanged=True,quota=1,provider_calls=3),ensure_ascii=False,indent=2))
