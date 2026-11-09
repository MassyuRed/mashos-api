"""Source-bound authoring conditions through the configured Piece owner.

Provider IO/Auth are synthetic and saved cases use disposable PostgreSQL.
These tests exercise routing and non-generation after save, not model quality.
"""
import asyncio
from dataclasses import replace
import json

import httpx
import pytest

import piece_model_source as model
import piece_v2_preview_service as preview
from cocolon_meaning_experience_engine.piece_semantic_admission import prepare_piece_model_request
from emlis_ai_current_input_bundle import normalize_emlis_current_input
from emlis_ai_nls_v3_artifact_contract import artifact_sha256
from piece_v2_contract import canonical_json_bytes, canonical_sha256_hex
from test_b05b_piece_visual_change import Adapter, request as preview_request
from test_cmee_piece_finite_request_reuse import source
from test_cmee_piece_request_saved_pipeline import saved_piece_db, _run_saved_request
from test_piece_model_finite_scope import request


ORIGINAL = '僕にとって重要なのは、一人で予定を考える時間です。'
BODY = '僕にとって、一人で予定を考える時間が重要だ。'


def configured(monkeypatch, handler):
    for key, value in dict(PIECE_MODEL_SOURCE=model.SELECTOR,
        EMLIS_NATURAL_REPLY_ENDPOINT='https://synthetic-piece.invalid/v1/chat/completions',
        EMLIS_NATURAL_REPLY_MODEL='synthetic-piece-authoring-4b',
        EMLIS_NATURAL_REPLY_API_KEY='synthetic-existing-piece-key-32').items():
        monkeypatch.setenv(key, value)
    real_type = model.Shared4BPieceModelSource
    monkeypatch.setattr(model, 'Shared4BPieceModelSource',
        lambda **kwargs: real_type(**kwargs, transport=httpx.MockTransport(handler)))
    return model.application_piece_model_source()


def response_for(request, seen):
    payload = json.loads(request.content)
    assert payload['messages'][0]['content'] == model.SYSTEM_MESSAGE
    material = json.loads(payload['messages'][1]['content'])
    assert material['sources'][0]['original']['memo'] == ORIGINAL
    conditions = material['control']['authoring_constraints']['field_slots']
    frame = conditions['memo_0']['required_evaluations'][0]
    assert frame['narrator_literal'] == '僕' and frame['predicate_literal'] == '重要な'
    assert frame['target_literal'] == '一人で予定を考える時間'
    seen.append(material)
    return httpx.Response(200, json=dict(model=payload['model'], candidate_format='piece.field_slots.v1',
        choices=[dict(finish_reason='stop', message=dict(role='assistant', content=json.dumps(
            dict(field_blocks=dict(memo_0=BODY)), ensure_ascii=False)))]))


def adapter_for_evaluation():
    adapter = Adapter('free')
    original = adapter.handoff.original
    record = original.original_payload()
    record['memo'] = ORIGINAL
    bundle = normalize_emlis_current_input(record)
    original = replace(original, _original_json=canonical_json_bytes(record),
        _bundle_json=canonical_json_bytes(bundle),
        input_bundle_commitment='sha256:' + artifact_sha256(bundle),
        record_commitment='sha256:' + canonical_sha256_hex(record))
    lineage = adapter.handoff.lineage_payload()
    lineage['source_input']['source_input_bundle_commitment'] = original.input_bundle_commitment
    adapter.handoff = replace(adapter.handoff, original=original,
                              _lineage_json=canonical_json_bytes(lineage))
    return adapter


def test_direct_preview_passes_the_exact_server_source_to_configured_author(monkeypatch):
    seen = []
    configured(monkeypatch, lambda r: response_for(r, seen))
    adapter = adapter_for_evaluation()
    value = preview_request(adapter.handoff)
    before = adapter.handoff.original._original_json, json.loads(json.dumps(value))
    prepared = asyncio.run(preview.PiecePreviewService(source_adapter=adapter).prepare_original(None, value))
    assert prepared.artifact_payload()['piece_text'] == BODY
    assert len(seen) == 1 and adapter.handoff.original._original_json == before[0]
    assert value == before[1]


def test_dispatch_keeps_custom_callbacks_single_argument_and_selector_off(monkeypatch):
    seen = []
    async def custom(prepared):
        seen.append(prepared)
        return 'custom-receipt'
    prepared = object()
    assert asyncio.run(model.call_piece_model_source(custom, prepared,
        source_request=object())) == 'custom-receipt'
    assert seen == [prepared]
    monkeypatch.setenv('PIECE_MODEL_SOURCE', 'off')
    assert model.application_piece_model_source() is None


def test_configured_source_rejects_a_mismatched_source_before_http(monkeypatch):
    seen = []
    configured_source = configured(monkeypatch, lambda r: response_for(r, seen))
    req = request(source(ORIGINAL, field='memo'))
    prepared = prepare_piece_model_request(req)
    wrong = request(source('僕は司書に展示の予定を相談しました。', field='memo'))
    with pytest.raises(ValueError, match='piece_model_prepared_invalid'):
        asyncio.run(model.call_piece_model_source(configured_source, prepared, source_request=wrong))
    assert seen == []


def test_same_key_shares_one_configured_conditioned_request_without_callback_wrapping(monkeypatch):
    async def exercise():
        seen = []
        entered, release = asyncio.Event(), asyncio.Event()
        async def handler(value):
            entered.set()
            await release.wait()
            return response_for(value, seen)
        selected = configured(monkeypatch, handler)
        req = request(source(ORIGINAL, field='memo'))
        prepared = prepare_piece_model_request(req)
        assert not preview._MODEL_INFLIGHT
        first = asyncio.create_task(preview._shared_model_receipt('owner', 'key', 'same', selected,
            prepared, source_request=req))
        await asyncio.wait_for(entered.wait(), 1)
        second = asyncio.create_task(preview._shared_model_receipt('owner', 'key', 'same', selected,
            prepared, source_request=req))
        await asyncio.sleep(0)
        release.set()
        one, two = await asyncio.gather(first, second)
        assert one is two and one.status == 'CANDIDATE_UNREVIEWED'
        assert len(seen) == 1 and not preview._MODEL_INFLIGHT
    asyncio.run(exercise())


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
def test_configured_author_conditions_reach_saved_body_and_never_regenerate_on_replay(
        saved_piece_db, monkeypatch, tier):
    seen = []
    configured(monkeypatch, lambda r: response_for(r, seen))
    record = dict(id='configured-source-authoring',
        created_at=saved_piece_db.query('SELECT now()::text AS stamp')['rows'][0]['stamp'],
        memo=ORIGINAL, memo_action=None, category=['生活', '価値観'], emotions=['自己理解'],
        emotion_details=[dict(type='自己理解', strength='medium')])
    result = _run_saved_request(saved_piece_db, monkeypatch, record, tier=tier)
    assert result['detail']['piece_text'] == BODY != ORIGINAL
    assert result['quota_consumptions'] == 1 and result['source_unchanged'] and result['emlis_unchanged']
    assert len(seen) == 1
