"""Model receipt to existing saved Piece, with isolated SQL and synthetic IO.

The provider HTTP response is fixed CPU material, or an explicitly supplied
private recorded 4B response. Replaying recorded raw is not a new GPU call.
The saved adapter, provider parser, CMEE/B8, Safety, SQL and read owners run.
"""
import json
import os
from pathlib import Path

import httpx
import pytest

from piece_model_source import Shared4BPieceModelSource
from test_cmee_piece_request_saved_pipeline import saved_piece_db, _run_saved_request
from test_b05_refined_preview_saved_pipeline import refined_pipeline_db, _run_refined_pipeline


def _provider(monkeypatch, case_id, default_blocks):
    seen = []
    recorded = os.environ.get('PIECE_MODEL_RECORDED_DIR')
    path = Path(recorded) / (case_id + '.private.json') if recorded else None
    response = json.loads(path.read_text())['response'] if path and path.exists() else {
        'model': 'piece-shared-4b-test', 'candidate_format': 'piece.field_slots.v1', 'choices': [{'finish_reason': 'stop',
            'message': {'role': 'assistant', 'content': json.dumps(
                {'body_blocks': default_blocks}, ensure_ascii=False)}}]}

    def transport(request):
        material = json.loads(request.content)
        assert material['max_tokens'] == 2048
        assert material['chat_template_kwargs'] == {'enable_thinking': False}
        prepared = json.loads(material['messages'][1]['content'])
        assert prepared['task'] == 'PIECE_MODEL_BODY'
        if path is None or not path.exists():
            # CPU prose remains independent fixed material. Only the named
            # private wire format changes; semantic/save expectations do not.
            keys = [item['field_path'] + '_' + str(index) for index, item
                    in enumerate(prepared['control']['block_partition'])]
            response['choices'][0]['message']['content'] = json.dumps(
                {'field_blocks': dict(zip(keys, default_blocks, strict=True))}, ensure_ascii=False)
        seen.append(dict(prepared=prepared, response=response))
        return httpx.Response(200, json=response)

    source = Shared4BPieceModelSource(endpoint='https://piece.example/v1/chat/completions',
        model=response['model'], api_key='synthetic-piece-key-not-a-secret',
        transport=httpx.MockTransport(transport))
    monkeypatch.setattr('piece_model_source.application_piece_model_source', lambda: source)
    return seen


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
@pytest.mark.parametrize('case_id,memo,body', [
    ('canonical-condition', '疲れているなら、私は本を読みたいです。',
     '私は、疲れているなら、本を読みたい。'),
    ('canonical-reason', '雨が続いているので、僕は家で過ごしたいです。',
     '僕は、雨が続いているので、家で過ごしたい。'),
    ('canonical-plain', '時間に余裕があるならば、わたしは休みたい。',
     'わたしは、時間に余裕があるならば、休みたいです。'),
])
def test_canonical_self_fronted_model_register_survives_saved_owner_reread(
        saved_piece_db, monkeypatch, tier, case_id, memo, body):
    from contextlib import ExitStack
    from unittest.mock import patch
    seen = _provider(monkeypatch, case_id, [body])
    record = dict(id=case_id,
        created_at=saved_piece_db.query('SELECT now()::text AS stamp')['rows'][0]['stamp'],
        memo=memo, memo_action='', category=['生活'], emotions=['平穏'],
        emotion_details=[dict(type='平穏', strength='weak')])
    with ExitStack() as stack:
        for owner in ('piece_v1c.realize_piece_artifact', 'piece_v1c._publicize_source_sentence',
                      'piece_v1c._evaluation_sentence', 'piece_refined.realize_refined_piece_artifact'):
            stack.enter_context(patch('cocolon_meaning_experience_engine.' + owner,
                                     side_effect=AssertionError('old author forbidden')))
        result = _run_saved_request(saved_piece_db, monkeypatch, record, tier=tier)
    assert result['detail']['piece_text'] == body
    assert result['source_unchanged'] and result['emlis_unchanged']
    assert result['quota_consumptions'] == 1
    _evidence(case_id + '-' + tier, result, seen)


def _evidence(case_id, result, seen):
    assert len(seen) == 1, 'replay/save/detail must never acquire another model candidate'
    result['piece_model_transport_calls'] = len(seen)
    result['model_material_and_raw'] = seen
    result['limits'] = ['synthetic authenticated IO', 'isolated PGlite, not live PostgREST',
                        'recorded or fixed response, not GPU invocation', 'no native bitmap/device']
    destination = os.environ.get('PIECE_MODEL_PIPELINE_EVIDENCE_DIR')
    if destination:
        folder = Path(destination)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / (case_id + '.private.json')).write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + '\n')


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
def test_model_body_differs_from_old_author_and_remains_fixed_after_sql_save(saved_piece_db, monkeypatch, tier):
    body = '私は同僚に資料の確認を頼んだ。'
    seen = _provider(monkeypatch, 'normal-request', [body])
    record = dict(id='piece-model-normal',
        created_at=saved_piece_db.query('SELECT now()::text AS stamp')['rows'][0]['stamp'],
        memo='', memo_action='私は同僚に資料の確認を頼みました。',
        category=['仕事'], emotions=['自己理解'],
        emotion_details=[dict(type='自己理解', strength='medium')])
    result = _run_saved_request(saved_piece_db, monkeypatch, record, tier=tier)
    assert result['detail']['piece_text'] == body
    assert result['detail']['piece_text'] != record['memo_action']
    assert len(seen[0]['prepared']['sources']) == 1
    _evidence('normal-request-' + tier, result, seen)


@pytest.mark.parametrize('case_id,answer', [('Q2-A', '私は寂しかった。'), ('Q2-C', '今は、私は嬉しい。')])
def test_real_q2_separate_answer_model_receipt_reuses_existing_visual_save_and_restart(
        refined_pipeline_db, monkeypatch, case_id, answer):
    blocks = ['褒められたのに、嬉しくなかった。', answer]
    seen = _provider(monkeypatch, case_id, blocks)
    result = _run_refined_pipeline(refined_pipeline_db, monkeypatch, answer, case_id,
                                  visual_change=True)
    assert result['detail']['piece_text'] == '\n\n'.join(blocks)
    sources = seen[0]['prepared']['sources']
    assert [item['role'] for item in sources] == ['ORIGINAL_INPUT', 'SUPPLEMENTAL_ANSWER']
    assert sources[0]['original']['memo'] == blocks[0]
    assert result['selected_preview']['visual_recipe_hash'] == result['detail']['visual_recipe_hash']
    # The reused helper counts its former finite-only path; record the model
    # call from this actual transport boundary rather than inheriting that zero.
    result['counts']['external_model_provider'] = len(seen)
    _evidence(case_id, result, seen)


@pytest.mark.parametrize('tier', ['free','plus','premium'])
@pytest.mark.parametrize('case_id,answer', [
    ('Q2-INVITE-PAST','その時、私は寂しかった。'),
    ('Q2-INVITE-NOW','今は、私は嬉しい。'),
])
def test_new_eligible_refined_sources_use_real_question_answer_add_and_saved_model_text(
        refined_pipeline_db,monkeypatch,tier,case_id,answer):
    memo='誘われたのに、嬉しくなかった。'
    seen=_provider(monkeypatch,case_id,[memo,answer])
    result=_run_refined_pipeline(refined_pipeline_db,monkeypatch,answer,case_id+'-'+tier,
        original_memo=memo,tier=tier,visual_change=True)
    assert result['initial_dto']['state']=='AWAITING_ANSWER'
    assert result['completed_dto']['body_state']=='REFINED'
    assert result['quota_consumptions']==1 and result['source_unchanged'] and result['emlis_unchanged']
    result['counts']['external_model_provider']=len(seen)
    _evidence(case_id+'-'+tier,result,seen)


@pytest.mark.parametrize('tier', ['free','plus','premium'])
def test_explicit_refined_name_to_role_remains_adjusted_through_visual_save_reload(
        refined_pipeline_db, monkeypatch, tier):
    memo = '上司の長谷川さんに褒められたのに、嬉しくなかった。'
    answer = 'その時、私は少し寂しかった。'
    blocks = ['上司に褒められたのに、嬉しくなかった。', answer]
    seen = _provider(monkeypatch, 'Q2-WRITTEN-ROLE', blocks)
    result = _run_refined_pipeline(refined_pipeline_db, monkeypatch, answer,
        'Q2-WRITTEN-ROLE-' + tier, original_memo=memo, tier=tier,
        expected_blocks=blocks, expected_safety_state='adjusted', visual_change=True)
    assert result['preview']['safety_state'] == 'adjusted'
    assert result['snapshot_before']['original']['memo'] == memo
    assert result['detail']['piece_text'] == '\n\n'.join(blocks)
    assert result['source_unchanged'] and result['emlis_unchanged']
    assert result['quota_consumptions'] == 1 and len(seen) == 1
    result['counts']['external_model_provider'] = len(seen)
    _evidence('Q2-WRITTEN-ROLE-' + tier, result, seen)


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
@pytest.mark.parametrize('case_id,memo', [
    ('QUOTE-STOP', '友人が「ゆっくりでいいよ。待っているよ」と言ってくれた。私は急がなくても一緒に過ごせることが嬉しかった。'),
    ('QUOTE-QUESTION', '友人が「どうする？急がなくてもいいよ」と言ってくれた。私は急がなくても一緒に過ごせることが嬉しかった。'),
    ('QUOTE-RUN', '友人が「よかった！！また会おう」と言ってくれた。私は一緒に過ごせたことが嬉しかった。'),
    ('QUOTE-PARAGRAPH', '友人が「ゆっくりでいいよ。待っているよ」と言ってくれた。\n私は急がなくても一緒に過ごせることが嬉しかった。'),
])
def test_quote_internal_stops_keep_complete_cpu_text_through_sql_save_and_restart(
        saved_piece_db, monkeypatch, tier, case_id, memo):
    # Fixed CPU prose verifies the receipt/save path; no real model is called.
    # The quoted speaker and outer feeling must survive byte for byte.
    blocks = memo.split('\n')
    seen = _provider(monkeypatch, case_id, blocks)
    record = dict(id=case_id, created_at=saved_piece_db.query(
        'SELECT now()::text AS stamp')['rows'][0]['stamp'], memo=memo, memo_action='',
        category=['生活'], emotions=['喜び'],
        emotion_details=[dict(type='喜び', strength='strong')])
    result = _run_saved_request(saved_piece_db, monkeypatch, record, tier=tier)
    assert result['detail']['content_payload']['body_blocks'] == blocks
    assert result['detail']['piece_text'] == '\n\n'.join(blocks)
    assert result['original']['memo'] == memo
    assert result['source_unchanged'] and result['emlis_unchanged']
    assert result['quota_consumptions'] == 1
    _evidence(case_id + '-' + tier, result, seen)


def test_qualified_normal_checkpoint_preserves_source_and_application_messages_before_save(tmp_path, monkeypatch):
    """CPU fixed prose; a new qualified source is frozen before acquisition.

    This is not a recorded GPU result rebound to a different UUID or time.
    Closing the SQL process also proves thread/events are restored, not seeded
    again before the ordinary application provider and save owners execute.
    """
    import asyncio
    from test_emlis_q3_application import Q3Database
    from test_cmee_piece_request_saved_pipeline import (
        _prepare_saved_request, _finish_saved_request, _bind_saved_request_io)
    from piece_v2_source_adapter import PieceSavedSourceAdapter
    from piece_v2_preview_service import _prepare_model_inputs
    from piece_model_source import build_piece_model_messages

    fixture = saved_piece_db.__wrapped__()
    db = next(fixture)
    checkpoint = tmp_path / 'qualified-normal.tgz'
    try:
        record = dict(id='qualified-normal-checkpoint',
            created_at=db.query('SELECT now()::text AS stamp')['rows'][0]['stamp'],
            memo='', memo_action='私は同僚に資料の確認を頼みました。',
            category=['仕事'], emotions=['自己理解'],
            emotion_details=[dict(type='自己理解', strength='medium')])
        with monkeypatch.context() as before:
            state = _prepare_saved_request(db, before, record, tier='free')
            handoff = asyncio.run(PieceSavedSourceAdapter().resolve_original_handoff(
                'Bearer ' + state['token'], state['source_id']))
            source, prepared = _prepare_model_inputs(handoff, state['request'])
            messages = build_piece_model_messages(prepared,
                include_authoring_constraints=True, source_request=source)
            frozen_state = json.dumps(state, ensure_ascii=False, sort_keys=True)
            assert state['counts'] == dict(synthetic_emlis_provider=1,
                piece_author=0, piece_review=0, preview_rpc=0, save_rpc=0)
            assert db.query('SELECT count(*)::int AS n FROM public.piece_records')['rows'][0]['n'] == 0
            dumped = db.dump_checkpoint(checkpoint)
            assert dumped['bytes'] == checkpoint.stat().st_size
    finally:
        fixture.close()

    # The restore path skips initial DDL/migrations: all qualified rows,
    # timestamps and observation identities come from the saved database.
    restored = Q3Database(checkpoint_path=checkpoint)
    try:
        with monkeypatch.context() as after:
            _bind_saved_request_io(restored, after, state['owner'], state['token'])
            handoff_after = asyncio.run(PieceSavedSourceAdapter().resolve_original_handoff(
                'Bearer ' + state['token'], state['source_id']))
            source_after, prepared_after = _prepare_model_inputs(handoff_after, state['request'])
            assert handoff_after == handoff
            assert prepared_after == prepared
            assert build_piece_model_messages(prepared_after,
                include_authoring_constraints=True, source_request=source_after) == messages
            seen = []
            fixed_body = '私は同僚に資料の確認を頼んだ。'

            def transport(request):
                body = json.loads(request.content)
                assert body['messages'] == messages
                material = json.loads(body['messages'][1]['content'])
                # This runs the actual configured Application source, so its
                # trusted source_request must reach the existing author input.
                assert material['control']['authoring_constraints']
                seen.append(body)
                keys = list(material['control']['field_slots'])
                assert len(keys) == 1
                return httpx.Response(200, json=dict(model=body['model'],
                    candidate_format='piece.field_slots.v1', choices=[dict(finish_reason='stop',
                        message=dict(role='assistant', content=json.dumps(
                            {'field_blocks': {keys[0]: fixed_body}}, ensure_ascii=False)))]))

            client = httpx.AsyncClient
            def local_client(*args, **kwargs):
                return client(*args, **dict(kwargs, transport=httpx.MockTransport(transport)))
            after.setattr('piece_model_source.httpx.AsyncClient', local_client)
            after.setenv('PIECE_MODEL_SOURCE', 'shared_4b.v1')
            after.setenv('EMLIS_NATURAL_REPLY_ENDPOINT', 'https://piece.example/v1/chat/completions')
            after.setenv('EMLIS_NATURAL_REPLY_MODEL', 'piece-checkpoint-test')
            after.setenv('EMLIS_NATURAL_REPLY_API_KEY', 'synthetic-checkpoint-key-not-a-secret')

            changed = json.loads(frozen_state)
            changed['original']['memo_action'] += '別の記録。'
            with pytest.raises(AssertionError, match='prepared saved original changed'):
                _finish_saved_request(restored, after, changed)
            changed = json.loads(frozen_state)
            changed['source_ref']['emlis_observation_result_identity'] = 'different-observation'
            with pytest.raises(AssertionError, match='prepared saved source reference changed'):
                _finish_saved_request(restored, after, changed)
            assert not seen, 'source mismatch must stop before provider acquisition'
            result = _finish_saved_request(restored, after, json.loads(frozen_state))
            assert len(seen) == 1
            assert result['original'] == state['original']
            assert result['source_ref'] == state['source_ref']
            assert result['detail']['piece_text'] == fixed_body
            assert result['detail']['piece_text'] != state['original']['memo_action']
            assert result['source_unchanged'] and result['emlis_unchanged']
            assert result['quota_consumptions'] == 1
            assert json.dumps(state, ensure_ascii=False, sort_keys=True) == frozen_state
    finally:
        restored.proc.stdin.close()
        restored.proc.wait(timeout=10)
