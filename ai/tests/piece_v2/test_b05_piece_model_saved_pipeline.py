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
