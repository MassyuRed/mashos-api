"""Actual Q2 ADD to reviewed refined preview, SQL save and owner reread.

The inputs/auth are synthetic. Existing Emlis finite CMEE and isolated PGlite
execute without a model provider. RPC callbacks are not PostgREST or live DB.
No native bitmap, device, publication or deployed feature is exercised.
"""
import asyncio
from contextlib import ExitStack
import json
import os
from pathlib import Path
import time
from unittest.mock import patch
from uuid import uuid4

import pytest

from test_cmee_piece_request_saved_pipeline import saved_piece_db, _ARTIFACT_FIELDS
from test_emlis_q2_application import answer as answer_question
from piece_v2_contract import PieceContractError, canonical_json_bytes


@pytest.fixture(scope='module')
def refined_pipeline_db(saved_piece_db):
    db = saved_piece_db
    root = Path(__file__).parents[3]
    path = root / 'supabase/migrations/20261109024943_piece_refined_source_fence.sql'
    db.proc.stdin.write(json.dumps(dict(sql=path.read_text(), script=True)) + '\n')
    db.proc.stdin.flush()
    result = json.loads(db.proc.stdout.readline())
    assert 'code' not in result, result
    return db


def _prepare_refined_pipeline(db, monkeypatch, answer_text, case_id, *,
                             original_memo='褒められたのに、嬉しくなかった。', tier='free'):
    """Commit a genuine synthetic Q2 ADD before any Piece acquisition.

    The returned JSON state belongs with the same database checkpoint. It is
    not a fabricated qualified source or permission to rebind recorded raw.
    """
    import api_account_visibility
    import emlis_thread_store
    import piece_v2_preview_service as preview_module
    import piece_v2_safety_review as safety_module
    from emlis_thread_service import EmlisThreadService
    from piece_v2_source_adapter import PieceSavedSourceAdapter
    from piece_v2_preview_service import PiecePreviewService
    from piece_v2_save_service import PieceSaveService
    from piece_v2_owner_service import PieceOwnerService, _COLUMNS

    start = time.monotonic()
    owner, source_id = str(uuid4()), str(uuid4())
    token = 'refined-pipeline-synthetic-owner'
    counts = dict(q2_start=0, q2_answer=0, piece_generation_entry=0, piece_review=0,
                  preview_rpc=0, visual_rpc=0, save_rpc=0, external_model_provider=0)
    assert 'code' not in db.query('INSERT INTO auth.users VALUES ($1)', [owner])
    assert 'code' not in db.query('INSERT INTO public.profiles VALUES ($1,$2)', [owner,tier])
    assert 'code' not in db.query(
        "INSERT INTO public.emotions VALUES ($1,$2,now() at time zone 'UTC',$3,'',array['仕事'],array['不安'],$4::jsonb)",
        [source_id, owner, original_memo,
         json.dumps([dict(type='不安', strength='medium')], ensure_ascii=False)])
    async def verify(value):
        assert value == token
        return owner
    monkeypatch.setattr(api_account_visibility, '_resolve_user_id_from_token', verify)
    monkeypatch.setattr(emlis_thread_store, 'sb_post_rpc', db.rpc)
    emlis = EmlisThreadService()
    started = asyncio.run(emlis.start(owner, source_id)); counts['q2_start'] += 1
    completed = asyncio.run(answer_question(emlis, owner, started, answer_text)); counts['q2_answer'] += 1
    assert completed['body_state'] == 'REFINED' and completed['meaning_updated'] is True
    snapshot_before = asyncio.run(emlis.store.read(owner, input_id=source_id))
    original = snapshot_before['original']
    answer_id = snapshot_before['thread']['latest_answer_event_id']
    cp = next(e['payload'] for e in snapshot_before['events']
              if e['id'] == snapshot_before['thread']['current_meaning_event_id'])
    assert cp['answer_update']['disposition'] == 'MATERIAL_UPDATE'
    assert all(item['operation'] == 'ADD' for item in cp['answer_update']['updates'])
    adapter = PieceSavedSourceAdapter()
    reference = asyncio.run(adapter.resolve_refined_source_ref('Bearer ' + token, source_id,
        supplemental_answer_identity=answer_id, opted_in=True))
    request = dict(source_ref=reference, requested_format=None,
        visual_selection=dict(theme_id=None, aspect_ratio=None, branding_mode=None))

    return json.loads(json.dumps(dict(case_id=case_id, tier=tier, owner=owner,
        source_id=source_id, token=token, answer_text=answer_text, original=original,
        source_ref=reference, request=request, initial_dto=started,
        completed_dto=completed, snapshot_before=snapshot_before, counts=counts),
        ensure_ascii=False))


def _finish_refined_pipeline(db, monkeypatch, state, *, visual_change=False,
                             expected_blocks=None, expected_safety_state='ready'):
    """Resume the same qualified source; never create another Q2 operation."""
    import api_account_visibility
    import emlis_thread_store
    import piece_v2_preview_service as preview_module
    import piece_v2_safety_review as safety_module
    from emlis_thread_service import EmlisThreadService
    from piece_v2_source_adapter import PieceSavedSourceAdapter
    from piece_v2_preview_service import PiecePreviewService
    from piece_v2_save_service import PieceSaveService
    from piece_v2_owner_service import PieceOwnerService, _COLUMNS

    start = time.monotonic()
    state = json.loads(json.dumps(state, ensure_ascii=False))
    owner, source_id, token = (state[key] for key in ('owner', 'source_id', 'token'))
    case_id, tier, answer_text = (state[key] for key in ('case_id', 'tier', 'answer_text'))
    original, snapshot_before = state['original'], state['snapshot_before']
    reference, request, counts = state['source_ref'], state['request'], state['counts']
    started, completed = state['initial_dto'], state['completed_dto']
    answer_id = snapshot_before['thread']['latest_answer_event_id']

    async def verify(value):
        assert value == token
        return owner
    monkeypatch.setattr(api_account_visibility, '_resolve_user_id_from_token', verify)
    monkeypatch.setattr(emlis_thread_store, 'sb_post_rpc', db.rpc)
    emlis = EmlisThreadService()
    current = asyncio.run(emlis.store.read(owner, input_id=source_id))
    assert set(original) == {'id', 'created_at', 'memo', 'memo_action', 'category',
                             'emotions', 'emotion_details'}
    assert current['original'] == original
    for key in ('original', 'thread', 'events'):
        assert current[key] == snapshot_before[key], 'qualified source changed after checkpoint'
    adapter = PieceSavedSourceAdapter()
    assert asyncio.run(adapter.resolve_refined_source_ref('Bearer ' + token, source_id,
        supplemental_answer_identity=answer_id, opted_in=True)) == reference
    assert request['source_ref'] == reference

    async def load_record(who, pid):
        rows = db.query('SELECT to_jsonb(r) AS row FROM public.piece_records r WHERE owner_user_id=$1 AND id=$2',
                        [who, pid], 'service_role')['rows']
        return rows[0]['row'] if rows else None
    async def load_preview(who, pid):
        row = await load_record(who, pid)
        return {key: row[key] for key in preview_module._REPLAY_COLUMNS} if row else None
    async def rpc(name, args):
        assert name in ('piece_issue_preview_v2', 'piece_save_v2', 'piece_mutate_preview_visual_v2')
        counts[{'piece_issue_preview_v2': 'preview_rpc', 'piece_save_v2': 'save_rpc',
                'piece_mutate_preview_visual_v2': 'visual_rpc'}[name]] += 1
        params = [json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v for v in args.values()]
        named = ','.join(f'{k} => ${n}' for n, k in enumerate(args, 1))
        result = db.query(f'SELECT public.{name}({named}) AS value', params, 'service_role', error_message=True)
        if 'code' in result:
            raise PieceContractError(result['message'])
        return result['rows'][0]['value']
    async def load_saved(params):
        assert set(params) == {'select', 'owner_user_id', 'lifecycle_status', 'id', 'limit'}
        assert params['select'] == ','.join(_COLUMNS)
        assert params['owner_user_id'] == 'eq.' + owner and params['lifecycle_status'] == 'eq.saved'
        row = await load_record(owner, params['id'][3:])
        return [{key: row[key] for key in _COLUMNS}] if row and row['lifecycle_status'] == 'saved' else []

    author, reviewer = preview_module.generate_piece_candidate, safety_module.review_prepared_original
    def observed_author(*args, **kwargs):
        counts['piece_generation_entry'] += 1
        return author(*args, **kwargs)
    async def observed_review(*args, **kwargs):
        counts['piece_review'] += 1
        return await reviewer(*args, **kwargs)
    monkeypatch.setattr(preview_module, 'generate_piece_candidate', observed_author)
    monkeypatch.setattr(safety_module, 'review_prepared_original', observed_review)
    issue_args = dict(idempotency_key='refined-pipeline-preview', ttl_seconds=600,
        renderer_version='piece.rn_bitmap_renderer.ios.v2', allowed_renderers=('piece.rn_bitmap_renderer.ios.v2',),
        expected_subscription_tier=tier, load_record=load_preview, rpc=rpc)
    preview = PiecePreviewService(source_adapter=adapter)
    first = asyncio.run(preview.issue_original('Bearer ' + token, request, **issue_args))
    expected_blocks = [original['memo'],answer_text] if expected_blocks is None else expected_blocks
    assert first['piece_text'] == '\n\n'.join(expected_blocks)
    assert first['content_payload']['body_blocks'] == expected_blocks
    # A source-stated role replacing its written name is the existing
    # adjusted state. Preserve exact expectations for every older fixture.
    assert expected_safety_state in ('ready', 'adjusted')
    assert first['safety_state'] == expected_safety_state
    row_after_issue = asyncio.run(load_record(owner, first['preview_id']))
    assert row_after_issue['source_lineage']['observation']['supplemental_answer_identity'] == answer_id
    assert len(row_after_issue['source_lineage']) == 8
    assert counts['piece_generation_entry'] == counts['piece_review'] == counts['preview_rpc'] == 1
    def forbidden(*args, **kw):
        pytest.fail('restart/save/detail must not generate, compile or review')
    selected, visual_mutation = first, None
    if visual_change:
        # The actual mutation service rechecks the source and reviews the
        # stored text; it may parse/compile for review but must never author.
        with patch('piece_v2_preview_service.generate_piece_candidate', side_effect=forbidden), \
             patch('cocolon_meaning_experience_engine.piece_v1c.realize_piece_artifact', side_effect=forbidden), \
             patch('cocolon_meaning_experience_engine.engine.MeaningExperienceEngine.generate', side_effect=forbidden):
            visual_mutation = asyncio.run(preview.mutate_original_visual('Bearer ' + token,
                authenticated_user_id=owner, preview_id=first['preview_id'],
                request=dict(expected_preview_revision=first['preview_revision'],
                    visual_selection=dict(theme_id='quiet_night', aspect_ratio=None, branding_mode=None)),
                expected_subscription_tier=tier, load_record=load_preview, rpc=rpc,
                allowed_renderers=('piece.rn_bitmap_renderer.ios.v2',)))
        assert visual_mutation['preview_revision'] == first['preview_revision'] + 1
        assert visual_mutation['expires_at'] == first['expires_at']
        for key in ('piece_text', 'piece_text_hash', 'content_payload', 'content_payload_hash'):
            assert visual_mutation[key] == first[key]
        assert visual_mutation['visual_recipe']['theme']['theme_id'] == 'quiet_night'
        assert visual_mutation['visual_recipe_hash'] != first['visual_recipe_hash']
        selected = visual_mutation
    row_for_replay = asyncio.run(load_record(owner, first['preview_id']))
    save_request = dict(preview_id=selected['preview_id'], expected_preview_revision=selected['preview_revision'],
        **{key: selected[key] for key in ('piece_text_hash', 'content_payload_hash', 'visual_recipe_hash')})
    with ExitStack() as stack:
        for path in ('piece_v2_preview_service.generate_piece_candidate',
            'piece_v2_safety_review.review_prepared_original',
            'cocolon_meaning_experience_engine.piece_v1c.compile_piece_artifact_plan',
            'cocolon_meaning_experience_engine.piece_v1c.realize_piece_artifact',
            'cocolon_meaning_experience_engine.engine.MeaningExperienceEngine.generate'):
            stack.enter_context(patch(path, side_effect=forbidden))
        replay = asyncio.run(PiecePreviewService().issue_original('Bearer ' + token, request, **issue_args))
        assert replay == dict(selected, idempotency_replayed=True)
        assert asyncio.run(load_record(owner, first['preview_id'])) == row_for_replay
        save_args = dict(authenticated_user_id=owner, request=save_request,
            idempotency_key='refined-pipeline-save', allowed_renderers=('piece.rn_bitmap_renderer.ios.v2',))
        saved = asyncio.run(PieceSaveService(load_record=load_record, rpc=rpc).save('Bearer ' + token, **save_args))
        saved_again = asyncio.run(PieceSaveService(load_record=load_record, rpc=rpc).save('Bearer ' + token, **save_args))
        assert saved_again == dict(saved, idempotency_replayed=True)
        detail = asyncio.run(PieceOwnerService(load_records=load_saved).detail(
            authenticated_user_id=owner, piece_id=saved['piece_id']))
        assert detail == asyncio.run(PieceOwnerService(load_records=load_saved).detail(
            authenticated_user_id=owner, piece_id=saved['piece_id']))
    final_row = asyncio.run(load_record(owner, first['preview_id']))
    snapshot_after = asyncio.run(emlis.store.read(owner, input_id=source_id))
    for key in ('original', 'thread', 'events'):
        assert snapshot_after[key] == snapshot_before[key]
    for key in _ARTIFACT_FIELDS:
        assert final_row[key] == detail[key]
        if key in selected:
            assert selected[key] == detail[key]
    assert final_row['lifecycle_status'] == detail['lifecycle_status'] == 'saved'
    assert db.query('SELECT count(*)::int AS n FROM public.piece_quota_consumptions WHERE owner_user_id=$1',
                    [owner])['rows'][0]['n'] == 1
    assert counts == dict(q2_start=1,
                         q2_answer=sum(e['kind'] == 'ANSWER' for e in snapshot_before['events']),
                         piece_generation_entry=1,
                         piece_review=2 if visual_change else 1,
                         preview_rpc=1, visual_rpc=1 if visual_change else 0,
                         save_rpc=2, external_model_provider=0)
    evidence = dict(case_id=case_id, tier=tier, answer_text=answer_text, initial_dto=started, completed_dto=completed,
        snapshot_before=snapshot_before, snapshot_after=snapshot_after, source_ref=reference,
        preview=first, preview_row=row_after_issue, visual_mutation=visual_mutation,
        selected_preview=selected, current_preview_row=row_for_replay,
        preview_replay=replay, save=saved, save_replay=saved_again,
        detail=detail, persisted_row=final_row, counts=counts, quota_consumptions=1,
        source_unchanged=True, emlis_unchanged=True, seconds=time.monotonic() - start,
        limitations=['synthetic auth and inputs', 'isolated SQL callback, not live PostgREST',
                     'no native bitmap/device/image sharing', 'one candidate entry may author internally more than once'])
    destination = os.environ.get('REFINED_PIPELINE_EVIDENCE_DIR')
    if destination:
        output = Path(destination)
        output.mkdir(parents=True, exist_ok=True)
        (output / (case_id + '.private.json')).write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + '\n')
    return evidence


def _run_refined_pipeline(db, monkeypatch, answer_text, case_id, *, visual_change=False,
                          original_memo='褒められたのに、嬉しくなかった。', tier='free',
                          expected_blocks=None, expected_safety_state='ready'):
    start = time.monotonic()
    state = _prepare_refined_pipeline(db, monkeypatch, answer_text, case_id,
        original_memo=original_memo, tier=tier)
    evidence = _finish_refined_pipeline(db, monkeypatch, state,
        visual_change=visual_change, expected_blocks=expected_blocks,
        expected_safety_state=expected_safety_state)
    evidence['seconds'] = time.monotonic() - start
    return evidence


@pytest.mark.parametrize('case_id,answer_text', [('Q2-A', '私は寂しかった。'), ('Q2-C', '今は、私は嬉しい。')])
def test_actual_q2_refinement_reaches_preview_save_and_fixed_owner_artifact(refined_pipeline_db, monkeypatch, case_id, answer_text):
    evidence = _run_refined_pipeline(refined_pipeline_db, monkeypatch, answer_text, case_id,
                                     visual_change=case_id == 'Q2-C')
    assert evidence['detail']['piece_text'] == '褒められたのに、嬉しくなかった。\n\n' + answer_text
