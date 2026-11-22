"""Explicit quote wire format: actual raw/replay, old compatibility and SQL.

Synthetic sources only; no model, GPU or production database calls.
"""
import asyncio
import copy
from dataclasses import replace
import json

import pytest

from test_cmee_preparation import emlis_request, original, piece_source
from test_cmee_emlis_model_daily_calm import daily_request, daily_packet, outcome
from test_emlis_q2_application import case, db, run
from cocolon_meaning_experience_engine.preparation import (
    prepare_emlis, prepare_piece, receive_candidate, QUOTE_CANDIDATE_SCHEMA,
)
from cocolon_meaning_experience_engine.model_candidate_source import (
    MODEL, REVISION, ModelCallLimits, ModelCandidateSource, ModelResponse,
    build_model_messages,
)
from cocolon_meaning_experience_engine.emlis_semantic_admission import (
    MODEL_PROFILE, SemanticInput, SemanticNotAdopted, prepare_model_snapshot,
    restore_model_snapshot,
)
from emlis_thread_service import EmlisThreadService


def wire(packet):
    return dict(schema_version=QUOTE_CANDIDATE_SCHEMA, candidate=copy.deepcopy(packet['candidate']),
        evidence_quotes=[{k: e[k] for k in ('source_id', 'field_path', 'quote')} for e in packet['evidence']])


def receive(req, packet, finish='stop'):
    material = prepare_emlis(req)
    text = json.dumps(packet, ensure_ascii=False)
    return receive_candidate(material, request_id=material.request_id, raw_output=text, finish_reason=finish)


def test_quote_compiles_to_exact_native_packet_and_replays_original_raw():
    req = daily_request()
    packet = daily_packet(req)
    quoted = wire(packet)
    receipt = receive(req, quoted)
    assert receipt.status == 'CANDIDATE_UNREVIEWED'
    assert json.loads(receipt.raw_output) == quoted
    assert json.loads(receipt.candidate_json) == packet
    assert receipt.adoption_state == 'NOT_ADOPTED'
    material = prepare_emlis(req)
    metadata = json.loads(receipt.metadata_json)
    metadata.pop('evidence_check')
    assert receive_candidate(material, request_id=receipt.request_id, raw_output=receipt.raw_output, **metadata) == receipt
    prepared = prepare_model_snapshot(req, SemanticInput('FRESH_CANDIDATE', receipt, semantic_profile=MODEL_PROFILE))
    restored = restore_model_snapshot(req, prepared.semantic_snapshot)
    assert restored.semantic_snapshot == prepared.semantic_snapshot
    assert outcome(req, prepared).artifact is not None
    forged = replace(receipt, candidate_json=receipt.candidate_json.replace('うどん', '雑炊'))
    with pytest.raises(SemanticNotAdopted, match='receipt_not_validated'):
        prepare_model_snapshot(req, SemanticInput('FRESH_CANDIDATE', forged, semantic_profile=MODEL_PROFILE))


@pytest.mark.parametrize('text,quote,expected', [
    ('🙂食べた', '食べた', (1, 4)), ('e\u0301を食べた', 'を食べた', (2, 6)),
    ('先に\n食べた', '\n食べた', (2, 6)), ('あああ', 'ああ', None),
    ('食べた、食べた', '食べた', None), ('食べた', '食べた。', None),
    ('食べた', '', None), ('か\u3099', 'が', None),
])
def test_scalar_positions_and_missing_overlapping_or_normalized_quotes(text, quote, expected):
    req = emlis_request(original(memo=text))
    sid = prepare_emlis(req).payload()['sources'][0]['source_id']
    packet = dict(schema_version=QUOTE_CANDIDATE_SCHEMA, candidate=dict(core='emlis'),
        evidence_quotes=[dict(source_id=sid, field_path='memo', quote=quote)])
    receipt = receive(req, packet)
    assert receipt.status == ('CANDIDATE_UNREVIEWED' if expected else 'INVALID_EVIDENCE')
    if expected:
        ref = json.loads(receipt.candidate_json)['evidence'][0]
        assert (ref['start'], ref['end']) == expected


@pytest.mark.parametrize('change', ['version', 'top_extra', 'mixed', 'row_start', 'row_end',
    'source', 'field', 'bool_quote', 'empty_rows', 'duplicate_key', 'nonfinite', 'other_core'])
def test_strict_quote_packet_rejects_mixed_foreign_or_ambiguous_inputs(change):
    req = daily_request()
    packet = wire(daily_packet(req))
    if change == 'version': packet['schema_version'] += '.future'
    if change == 'top_extra': packet['extra'] = True
    if change == 'mixed': packet['evidence'] = []
    if change in ('row_start', 'row_end'): packet['evidence_quotes'][0][change[4:]] = 0
    if change == 'source': packet['evidence_quotes'][0]['source_id'] = 'foreign'
    if change == 'field': packet['evidence_quotes'][0]['field_path'] = 'memo.no_such_field'
    if change == 'bool_quote': packet['evidence_quotes'][0]['quote'] = True
    if change == 'empty_rows': packet['evidence_quotes'] = []
    if change == 'other_core': packet['candidate']['core'] = 'piece'
    material = prepare_emlis(req)
    text = json.dumps(packet, ensure_ascii=False)
    if change == 'duplicate_key': text = text.replace('"schema_version":', '"schema_version":"forged","schema_version":', 1)
    if change == 'nonfinite': text = text.replace('"candidate":', '"candidate":NaN,"unused":', 1)
    receipt = receive_candidate(material, request_id=material.request_id, raw_output=text, finish_reason='stop')
    assert receipt.status in {'INVALID_EVIDENCE', 'INVALID_FORMAT'}
    assert receipt.raw_output == text


def test_quote_parser_does_not_admit_piece_material_or_repair_legacy_offsets():
    req = daily_request()
    packet = daily_packet(req)
    packet['evidence'][0]['start'] += 1
    assert receive(req, packet).status == 'INVALID_EVIDENCE'
    material = prepare_piece(piece_source(), expected_owner_id='synthetic-preparation-owner', tier='free')
    ref = material.payload()['sources'][0]
    field = next(k for k, v in ref['text_fields'].items() if isinstance(v, str) and v)
    quoted = dict(schema_version=QUOTE_CANDIDATE_SCHEMA, candidate=dict(core='piece'),
        evidence_quotes=[dict(source_id=ref['source_id'], field_path=field, quote=ref['text_fields'][field])])
    assert receive_candidate(material, request_id=material.request_id,
        raw_output=json.dumps(quoted), finish_reason='stop').status == 'INVALID_EVIDENCE'


@pytest.mark.parametrize('finish,status', [('length','TOKEN_LIMIT'),('timeout','TIMEOUT'),('error','PROVIDER_ERROR'),('unknown','UNKNOWN_FINISH')])
def test_finish_state_overrides_even_a_located_quote(finish, status):
    req = daily_request()
    assert receive(req, wire(daily_packet(req)), finish).status == status


def test_quote_prompt_is_explicit_and_old_prompt_bytes_are_the_default():
    req = daily_request()
    old = build_model_messages(req)
    assert old == build_model_messages(req, candidate_format='legacy_numeric')
    new = build_model_messages(req, candidate_format=QUOTE_CANDIDATE_SCHEMA)
    body = json.loads(new[1]['content'])
    assert body['model_output_format'] == QUOTE_CANDIDATE_SCHEMA
    assert '[A-Za-z0-9_.-]{1,64}' in body['output_spec']['unknown_id_constraints']
    assert 'prior unknown IDs' in body['output_spec']['unknown_id_constraints']
    assert 'unknown_id_constraints' not in json.loads(old[1]['content'])['output_spec']
    assert set(body['output_spec']['shape']) == {'schema_version','candidate','evidence_quotes'}
    assert 'field_unicode_spans' not in new[1]['content']
    assert 'with exact full-field coordinates' not in new[1]['content']
    assert body['material']['sources'][0]['text_fields'] == json.loads(old[1]['content'])['material']['sources'][0]['text_fields']
    assert '最上位はschema_versionとcandidateとevidence_quotesだけです。' in new[0]['content']
    with pytest.raises(ValueError, match='format_invalid'):
        build_model_messages(req, candidate_format='future')
    with pytest.raises(ValueError, match='explicit_offline'):
        build_model_messages(replace(req, execution_mode='EMLIS_APPLICATION'), candidate_format=QUOTE_CANDIDATE_SCHEMA)


@pytest.mark.parametrize('requested,returned', [(QUOTE_CANDIDATE_SCHEMA,'legacy_numeric'),('legacy_numeric',QUOTE_CANDIDATE_SCHEMA),(QUOTE_CANDIDATE_SCHEMA,QUOTE_CANDIDATE_SCHEMA)])
def test_model_source_preserves_raw_and_never_falls_back(requested, returned):
    req = daily_request()
    packet = daily_packet(req)
    raw = json.dumps(wire(packet) if returned == QUOTE_CANDIDATE_SCHEMA else packet, ensure_ascii=False)
    calls = []
    async def generator(messages, limits):
        calls.append(messages)
        return ModelResponse(raw, 'stop', 'synthetic', MODEL, REVISION)
    source = ModelCandidateSource(generator, lambda _: 50,
        limits=ModelCallLimits(5632,2560,150), candidate_format=requested)
    receipt = asyncio.run(source(req))
    assert receipt.raw_output == raw and len(calls) == 1
    assert receipt.status == ('CANDIDATE_UNREVIEWED' if requested == returned else 'PROVIDER_ERROR')


@pytest.mark.parametrize('variant',[False,True])
@pytest.mark.parametrize('interrupted',[False,True])
def test_real_sql_quote_receipt_is_saved_and_reread_without_generation(case, db, monkeypatch, variant, interrupted):
    user, parent, _ = case
    proto = daily_request('雑炊','温かいもの','を','少し') if variant else daily_request()
    raw = proto.current_input_bundle.raw_current_input
    db.query("update public.emotions set memo=$1,memo_action=$2,category=array['生活'],emotions=array['平穏','喜び'],emotion_details=$3 where id=$4",
        [raw['memo'],raw['memo_action'],json.dumps(raw['emotion_details'],ensure_ascii=False),parent])
    calls = []
    async def generate(messages, limits):
        req = calls[-1]
        return ModelResponse(json.dumps(wire(daily_packet(req)),ensure_ascii=False), 'stop', 'synthetic', MODEL, REVISION)
    source = ModelCandidateSource(generate, lambda _: 50,
        limits=ModelCallLimits(5632,2560,150),candidate_format=QUOTE_CANDIDATE_SCHEMA)
    async def acquire(req, prior):
        calls.append(req)
        return await source(req, prior)
    service = EmlisThreadService(semantic_profile=MODEL_PROFILE,offline_candidate_source=acquire,offline_model_attempt_seconds=180)
    if interrupted:
        original_generate = service.engine.generate
        def interrupt(*args, **kwargs):
            raise asyncio.CancelledError()
        monkeypatch.setattr(service.engine, 'generate', interrupt)
        with pytest.raises(asyncio.CancelledError):
            run(service.start(user,parent))
        failed = run(service.get(user,parent))
        # Initial meaning is saved; meaning_updated describes an answer update.
        assert failed['can_retry'] and not failed['meaning_updated']
        saved_meaning = run(service.store.read(user,input_id=parent))['thread']['current_meaning_event_id']
        assert saved_meaning is not None
        monkeypatch.setattr(service.engine, 'generate', original_generate)
        completed = run(service.action(user,failed['thread_id'],action='retry_response',
            expected_revision=failed['revision'],idempotency_key='quote-resume',operation_id=failed['operation_id']))
        assert run(service.store.read(user,input_id=parent))['thread']['current_meaning_event_id']==saved_meaning
    else:
        completed = run(service.start(user,parent))
    assert completed['state']=='COMPLETED' and completed['body_state']=='FINAL',completed
    before = run(service.store.read(user,input_id=parent))
    assert len([e for e in before['events'] if e['kind']=='MEANING_UPDATE'])==1
    class NoGeneration:
        def __getattr__(self, name): raise AssertionError('saved quote read generated')
    reader = EmlisThreadService(engine=NoGeneration())
    assert run(reader.get(user,parent))=={**completed,'can_write':False}
    assert run(reader.start(user,parent))=={**completed,'can_write':False}
    after=run(service.store.read(user,input_id=parent))
    assert {k:v for k,v in before.items() if k!='now'}=={k:v for k,v in after.items() if k!='now'}
    assert len(calls)==1


def test_quote_prior_hides_native_coordinates_without_mutating_saved_meaning():
    from test_cmee_emlis_model_meaning import (
        initial_model_request, model_answer, model_semantic,
    )
    req = initial_model_request()
    initial = build_model_messages(req, candidate_format=QUOTE_CANDIDATE_SCHEMA)
    prior = prepare_model_snapshot(req, model_semantic(req))
    answer = model_answer(req, prior)
    saved_before = prior.semantic_snapshot
    meaning_before = prior.meaning_json
    legacy = build_model_messages(answer, prior.semantic_snapshot)
    native = json.loads(legacy[1]["content"])["prior_adopted_interpretation"]
    quoted = build_model_messages(answer, prior.semantic_snapshot,
                                  candidate_format=QUOTE_CANDIDATE_SCHEMA)
    visible = json.loads(quoted[1]["content"])["prior_adopted_interpretation"]
    expected = copy.deepcopy(native)
    for item in expected["meaning_packet"]["evidence"]:
        assert "start" in item and "end" in item
        del item["start"], item["end"]
    assert visible == expected
    assert visible["meaning_packet"]["candidate"] == native["meaning_packet"]["candidate"]
    assert prior.semantic_snapshot == saved_before and prior.meaning_json == meaning_before
    assert json.loads(prior.meaning_json) == native["meaning_packet"]
    assert build_model_messages(answer, prior.semantic_snapshot) == legacy
    assert build_model_messages(req, candidate_format=QUOTE_CANDIDATE_SCHEMA) == initial

