"""Explicit CMEE realization of admitted model prose, without inference.

The recorded rows are fictional November 14 raw, not mock outputs invented
for this implementation. Re-review under a new private profile does not claim
a new model response, the original request's admission, or human acceptance.
"""
import asyncio
from dataclasses import replace
import hashlib
import json
from pathlib import Path

import httpx
import pytest

import piece_model_source as model
from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.piece_semantic_admission import (
    PieceModelInputV1, PIECE_FIELD_SLOTS_FORMAT, prepare_piece_model_request,
    receive_piece_model_candidate,
)
from cocolon_meaning_experience_engine.piece_v1c import MODEL_REALIZATION_PROFILE
from piece_v2_contract import canonical_json_bytes
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
from test_cmee_piece_finite_request_reuse import source
from test_piece_model_finite_scope import request
from test_cmee_piece_request_saved_pipeline import saved_piece_db, _run_saved_request


RECORDED = json.loads((Path(__file__).parent / 'fixtures/piece_cmee_realization_recorded.json').read_text())


def fixed_input(monkeypatch, saved, raw, *, new, tier='free', fmt=None):
    monkeypatch.setenv('PIECE_MODEL_SOURCE', model.CMEE_SELECTOR if new else model.SELECTOR)
    req = replace(request(saved), tier=tier, requested_format=fmt)
    prepared = prepare_piece_model_request(req)
    receipt = receive_piece_model_candidate(prepared, raw_output=raw, finish_reason='stop',
        candidate_format=PIECE_FIELD_SLOTS_FORMAT,
        realization_profile=MODEL_REALIZATION_PROFILE if new else None)
    return req, PieceModelInputV1(prepared, receipt)


def recorded_source(row):
    rec = row['original']
    return PieceSourceSnapshot('recorded-fictional-owner', rec['id'], 'emlis.current_input_bundle.v1',
        '\n\n'.join(rec[k] for k in ('memo', 'memo_action') if rec[k]),
        saved_original_json=canonical_json_bytes(rec))


@pytest.mark.parametrize('row', RECORDED['rows'], ids=lambda row: row['case_id'])
def test_recorded_whole_outputs_change_without_mutating_raw_or_source(monkeypatch, row):
    assert RECORDED['all_fictional'] is True
    raw = row['raw_output']
    assert hashlib.sha256(raw.encode()).hexdigest() == row['raw_sha256']
    saved = recorded_source(row)
    original = saved.saved_original_json
    old_req, old_input = fixed_input(monkeypatch, saved, raw, new=False)
    old = MeaningExperienceEngine().generate(old_req, semantic_input=old_input)
    new_req, new_input = fixed_input(monkeypatch, saved, raw, new=True)
    new = MeaningExperienceEngine().generate(new_req, semantic_input=new_input)
    assert old.artifact is not None, old.reason_codes
    assert new.artifact is not None, new.reason_codes
    assert new.artifact.model_body_blocks == old.artifact.body_blocks
    assert old_input.receipt.raw_output == new_input.receipt.raw_output == raw
    assert saved.saved_original_json == original
    assert new.artifact.piece_text != old.artifact.piece_text
    assert new.artifact.realization_profile == MODEL_REALIZATION_PROFILE
    if row['case_id'] == 'COHERENT-PARAGRAPH':
        assert new.artifact.piece_text == old.artifact.piece_text.replace(
            '私は、返事をする前にメモを見返したい。', '返事をする前にメモを見返したい。')
        # Unproved narrator links stay explicit. This is not general editing.
        assert new.artifact.piece_text.count('私は、') == 4
    else:
        assert new.artifact.piece_text == old.artifact.piece_text.replace(
            'おれは、同僚となら', '同僚となら').replace(
            '僕は、相手に合わせるために', '相手に合わせるために')
        assert new.artifact.body_blocks[0].startswith('おれは、')
        assert new.artifact.body_blocks[1].startswith('僕は、')
        assert '気がする。まだ、次に行く日は決めていない。' in new.artifact.body_blocks[0]
    candidate = generate_piece_candidate(saved, authenticated_owner_id=saved.owner_id,
        model_candidate=new_input)
    assert candidate['piece_text'] == new.artifact.piece_text
    assert new.artifact.realization_edits


@pytest.mark.parametrize('text,body', [
    ('私は司書から資料の確認を頼まれませんでした。', '私は司書から資料の確認を頼まなかった。'),
    ('僕は農作業が好きでした。', '僕は農作業が好きだ。'),
])
def test_failed_model_meaning_is_never_replaced_by_native_author(monkeypatch, text, body):
    raw = json.dumps({'field_blocks': {'memo_0': body}}, ensure_ascii=False)
    req, value = fixed_input(monkeypatch, source(text, field='memo'), raw, new=True)
    out = MeaningExperienceEngine().generate(req, semantic_input=value)
    assert out.artifact is None
    assert value.receipt.raw_output == raw


def test_duplicate_occurrences_and_quote_boundaries_are_not_guessed(monkeypatch):
    text = '私は、静かな時間を大切にしたい。私は、静かな時間を大切にしたい。'
    raw = json.dumps({'field_blocks': {'memo_0': text}}, ensure_ascii=False)
    req, value = fixed_input(monkeypatch, source(text, field='memo'), raw, new=True)
    out = MeaningExperienceEngine().generate(req, semantic_input=value)
    assert out.artifact is not None, out.reason_codes
    assert out.artifact.piece_text == text and out.artifact.realization_edits == ()


@pytest.mark.parametrize('text,expected', [
    ('僕にとって重要なのは、一人で予定を考える時間です。',
     '僕にとって、一人で予定を考える時間が重要です。'),
    ('疲れているなら、私が選びたいのは、音楽を聴く時間です。まだ、出かける日は決めていません。',
     '疲れているなら、私は音楽を聴く時間を選びたい。まだ、出かける日は決めていません。'),
])
def test_existing_evaluation_and_scoped_expression_are_realized_not_only_topic_elision(
        monkeypatch, text, expected):
    raw = json.dumps({'field_blocks': {'memo_0': text}}, ensure_ascii=False)
    req, value = fixed_input(monkeypatch, source(text, field='memo'), raw, new=True)
    out = MeaningExperienceEngine().generate(req, semantic_input=value)
    assert out.artifact is not None, out.reason_codes
    assert out.artifact.piece_text == expected
    assert value.receipt.raw_output == raw


def test_quoted_discourse_keeps_all_model_words_and_does_not_gain_a_narrator(monkeypatch):
    text = '友人が「よかった！！また会おう」と言ってくれた。私は一緒に過ごせたことが嬉しかった。'
    raw = json.dumps({'field_blocks': {'memo_0': text}}, ensure_ascii=False)
    req, value = fixed_input(monkeypatch, source(text, field='memo', emotions=['喜び'],
        details=[dict(type='喜び', strength='strong')]), raw, new=True)
    out = MeaningExperienceEngine().generate(req, semantic_input=value)
    assert out.artifact is not None, out.reason_codes
    assert out.artifact.piece_text == text and out.artifact.realization_edits == ()


@pytest.mark.parametrize('fmt', ['short_essay', 'quote', 'declaration'])
def test_three_formats_use_existing_source_eligibility(monkeypatch, fmt):
    text = '私が大切にしたいのは、自分で納得して選ぶ時間です。'
    raw = json.dumps({'field_blocks': {'memo_0': text}}, ensure_ascii=False)
    req, value = fixed_input(monkeypatch, source(text, field='memo'), raw,
        new=True, tier='premium', fmt=fmt)
    out = MeaningExperienceEngine().generate(req, semantic_input=value)
    assert out.artifact is not None, out.reason_codes
    assert out.artifact.format_type == fmt
    assert out.artifact.piece_text == '私は、自分で納得して選ぶ時間を大切にしたい。'
    assert value.receipt.raw_output == raw
    assert generate_piece_candidate(req.source, authenticated_owner_id=req.source.owner_id,
        tier='premium', requested_format=fmt, model_candidate=value)['format_type'] == fmt


def test_model_cannot_award_declaration_to_uncertain_or_multisentence_source(monkeypatch):
    text = '私は、陶芸を選びたい。まだ決めていない。'
    raw = json.dumps({'field_blocks': {'memo_0': text}}, ensure_ascii=False)
    req, value = fixed_input(monkeypatch, source(text, field='memo'), raw,
        new=True, tier='premium', fmt='declaration')
    assert MeaningExperienceEngine().generate(req, semantic_input=value).artifact is None
    req = replace(req, tier='free', requested_format='quote')
    assert MeaningExperienceEngine().generate(req, semantic_input=value).artifact is None


def test_profile_is_frozen_in_preparation_receipt_and_configured_transport(monkeypatch):
    text = '私は、静かな時間を大切にしたい。私は、自分で確かめたい。'
    raw = json.dumps({'field_blocks': {'memo_0': text}}, ensure_ascii=False)
    req, value = fixed_input(monkeypatch, source(text, field='memo'), raw, new=True)
    for key, val in dict(EMLIS_NATURAL_REPLY_ENDPOINT='https://synthetic-piece.invalid/v1/chat/completions',
                        EMLIS_NATURAL_REPLY_MODEL='synthetic-existing-model',
                        EMLIS_NATURAL_REPLY_API_KEY='synthetic-existing-piece-key-32').items():
        monkeypatch.setenv(key, val)
    seen = []
    def handler(http_request):
        payload = json.loads(http_request.content)
        material = json.loads(payload['messages'][1]['content'])
        assert material['control']['realization_profile'] == MODEL_REALIZATION_PROFILE
        seen.append(payload)
        return httpx.Response(200, json=dict(model=payload['model'], candidate_format=PIECE_FIELD_SLOTS_FORMAT,
            choices=[dict(finish_reason='stop', message=dict(role='assistant', content=raw))]))
    real = model.Shared4BPieceModelSource
    monkeypatch.setattr(model, 'Shared4BPieceModelSource',
        lambda **kwargs: real(**kwargs, transport=httpx.MockTransport(handler)))
    configured = model.application_piece_model_source()
    receipt = asyncio.run(model.call_piece_model_source(configured, value.prepared, source_request=req))
    assert len(seen) == 1 and receipt.raw_output == raw
    assert json.loads(receipt.metadata_json)['realization_profile'] == MODEL_REALIZATION_PROFILE
    assert MeaningExperienceEngine().generate(req,
        semantic_input=PieceModelInputV1(value.prepared, receipt)).artifact is not None
    monkeypatch.setenv('PIECE_MODEL_SOURCE', model.SELECTOR)
    with pytest.raises(RuntimeError, match='configuration_changed'):
        configured.require_current()


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
def test_configured_realization_is_saved_and_reread_without_model_reacquisition(
        saved_piece_db, monkeypatch, tier):
    text = ('私は、静かに考える時間を大切にしたい。'
            '私は、返事の前にメモを見返したい。')
    expected = text.replace('私は、返事の前に', '返事の前に')
    raw = json.dumps({'field_blocks': {'memo_0': text}}, ensure_ascii=False)
    for key, val in dict(PIECE_MODEL_SOURCE=model.CMEE_SELECTOR,
                        EMLIS_NATURAL_REPLY_ENDPOINT='https://synthetic-piece.invalid/v1/chat/completions',
                        EMLIS_NATURAL_REPLY_MODEL='synthetic-existing-model',
                        EMLIS_NATURAL_REPLY_API_KEY='synthetic-existing-piece-key-32').items():
        monkeypatch.setenv(key, val)
    seen = []
    def handler(http_request):
        payload = json.loads(http_request.content)
        seen.append(payload)
        return httpx.Response(200, json=dict(model=payload['model'], candidate_format=PIECE_FIELD_SLOTS_FORMAT,
            choices=[dict(finish_reason='stop', message=dict(role='assistant', content=raw))]))
    real = model.Shared4BPieceModelSource
    monkeypatch.setattr(model, 'Shared4BPieceModelSource',
        lambda **kwargs: real(**kwargs, transport=httpx.MockTransport(handler)))
    record = dict(id='fictional-private-realization-save',
        created_at=saved_piece_db.query('SELECT now()::text AS stamp')['rows'][0]['stamp'],
        memo=text, memo_action=None, category=['生活'], emotions=['自己理解'],
        emotion_details=[dict(type='自己理解', strength='medium')])
    result = _run_saved_request(saved_piece_db, monkeypatch, record, tier=tier)
    assert result['detail']['piece_text'] == expected
    assert result['quota_consumptions'] == 1
    assert result['source_unchanged'] and result['emlis_unchanged']
    assert len(seen) == 1
