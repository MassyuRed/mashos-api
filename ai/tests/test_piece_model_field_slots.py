"""Private format adaptation reuses the existing canonical Piece owners.

Fictional CPU candidates; named slots are not proof of preserved meaning.
"""
from dataclasses import replace
import json

import pytest

from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.piece_semantic_admission import (
    PieceModelInputV1, PIECE_FIELD_SLOTS_FORMAT, prepare_piece_model_request,
    receive_piece_model_candidate,
)
from piece_model_source import build_piece_model_messages
from test_cmee_piece_finite_request_reuse import source
from test_piece_model_finite_scope import request
from test_cmee_piece_refined_sources import source as refined_source, request as refined_request

FIRST = '私にとって読書が必要とは限りません。'
SECOND = '私は司書に展示の予定を相談しました。'


def selected_request():
    return request(source(FIRST, field='memo', other=SECOND))


def receive(req, raw, **kw):
    prepared = prepare_piece_model_request(req)
    receipt = receive_piece_model_candidate(prepared, raw_output=raw, finish_reason='stop',
        candidate_format=PIECE_FIELD_SLOTS_FORMAT, **kw)
    return prepared, receipt


def produce(req, raw):
    prepared, receipt = receive(req, raw)
    return MeaningExperienceEngine().generate(req,
        semantic_input=PieceModelInputV1(prepared, receipt))


def wire(fields):
    return json.dumps({'field_blocks': fields}, ensure_ascii=False)


def test_reversed_wire_keys_are_projected_in_source_order_without_changing_raw():
    req = selected_request()
    raw = wire({'memo_action_1': SECOND, 'memo_0': FIRST}) + '\n'
    prepared, receipt = receive(req, raw)
    assert receipt.raw_output == raw and receipt.adoption_state == 'NOT_ADOPTED'
    assert receipt.status == 'CANDIDATE_UNREVIEWED'
    assert json.loads(receipt.candidate_json) == {'body_blocks': [FIRST, SECOND]}
    assert json.loads(receipt.metadata_json)['candidate_format'] == PIECE_FIELD_SLOTS_FORMAT
    out = produce(req, raw)
    assert out.artifact is not None, out.reason_codes
    assert out.artifact.body_blocks == (FIRST, SECOND)
    assert out.artifact.piece_text == FIRST + '\n\n' + SECOND
    assert prepared == prepare_piece_model_request(req)


@pytest.mark.parametrize('raw', [
    '{"field_blocks":{"memo_0":"a","memo_0":"b","memo_action_1":"c"}}',
    '{"field_blocks":{"memo_0":"a","memo_action_1":"b"},"field_blocks":{}}',
    wire({'memo_0': FIRST}), wire({'memo_0': FIRST, 'memo_action_1': SECOND, 'memo_2': FIRST}),
    wire({'memo_0': FIRST, 'memo_action_0': SECOND}),
    wire({'memo_0': FIRST, 'memo_action_1': ''}),
    wire({'memo_0': FIRST, 'memo_action_1': '　'}),
    wire({'memo_0': FIRST, 'memo_action_1': None}),
    wire({'memo_0': FIRST, 'memo_action_1': [SECOND]}),
    wire({'memo_0': FIRST, 'memo_action_1': SECOND + '\n'}),
    '{"field_blocks":["a","b"]}',
    json.dumps({'body_blocks': [FIRST, SECOND]}, ensure_ascii=False),
    json.dumps({'field_blocks': {'memo_0': FIRST,'memo_action_1': SECOND},'body_blocks': [FIRST,SECOND]}, ensure_ascii=False),
    '{"field_blocks":{"memo_0":"\\ud800","memo_action_1":"b"}}',
])
def test_invalid_slot_wire_is_retained_but_not_repaired_or_accepted(raw):
    _, receipt = receive(selected_request(), raw)
    assert receipt.raw_output == raw and receipt.status == 'INVALID_FORMAT'
    assert receipt.candidate_json is None and receipt.adoption_state == 'NOT_ADOPTED'
    assert produce(selected_request(), raw).artifact is None


@pytest.mark.parametrize('fields', [
    {'memo_0': SECOND, 'memo_action_1': FIRST},
    {'memo_0': FIRST + SECOND, 'memo_action_1': SECOND},
    {'memo_0': FIRST, 'memo_action_1': FIRST},
    {'memo_0': '私にとって読書が必要です。', 'memo_action_1': SECOND},
    {'memo_0': FIRST, 'memo_action_1': '私は司書に展示の予定を相談しませんでした。'},
    {'memo_0': FIRST, 'memo_action_1': SECOND + 'だから安心した。'},
])
def test_complete_named_slots_do_not_certify_swapped_merged_or_changed_meaning(fields):
    req = selected_request(); raw = wire(fields)
    _, receipt = receive(req, raw)
    assert receipt.status == 'CANDIDATE_UNREVIEWED'
    assert produce(req, raw).artifact is None


def test_legacy_default_keeps_its_receipt_bytes_and_never_guesses_new_format():
    req = selected_request(); prepared = prepare_piece_model_request(req)
    raw = json.dumps({'body_blocks': [FIRST, SECOND]}, ensure_ascii=False)
    old = receive_piece_model_candidate(prepared, raw_output=raw, finish_reason='stop')
    explicit = receive_piece_model_candidate(prepared, raw_output=raw, finish_reason='stop', candidate_format=None)
    assert old == explicit
    assert 'candidate_format' not in json.loads(old.metadata_json)
    assert old.metadata_json == '{"elapsed_seconds":null,"evidence_check":"BODY_UNREVIEWED_NOT_SEMANTIC_ADMISSION","finish_reason":"stop","model":null,"provider":null,"revision":null,"usage":null}'
    slots = wire({'memo_0': FIRST, 'memo_action_1': SECOND})
    assert receive_piece_model_candidate(prepared, raw_output=slots, finish_reason='stop').status == 'INVALID_FORMAT'


def test_format_metadata_cannot_be_dropped_or_forged_after_receipt():
    req = selected_request(); prepared, receipt = receive(req, wire({'memo_0': FIRST,'memo_action_1': SECOND}))
    metadata = json.loads(receipt.metadata_json); metadata.pop('candidate_format')
    forged = replace(receipt, metadata_json=json.dumps(metadata,sort_keys=True,separators=(',',':')))
    assert MeaningExperienceEngine().generate(req,semantic_input=PieceModelInputV1(prepared,forged)).artifact is None
    with pytest.raises(ValueError, match='piece_model_candidate_format'):
        receive_piece_model_candidate(prepared,raw_output=receipt.raw_output,finish_reason='stop',candidate_format='other')


def test_transport_slots_keep_exact_scalar_text_full_sources_and_frozen_identity():
    memo = '　私は👩\u200d🚀が好きです。\r\n\r\n私はe\u0301が好きです。　'
    req = request(source(memo,field='memo',other=SECOND))
    prepared = prepare_piece_model_request(req); before = prepared.private_json
    material = json.loads(build_piece_model_messages(prepared)[1]['content'])
    slots = material['control'].pop('field_slots')
    assert list(slots) == ['memo_0','memo_1','memo_action_2']
    assert [s['literal'] for s in slots.values()] == ['　私は👩\u200d🚀が好きです。','私はe\u0301が好きです。　',SECOND]
    assert material == prepared.payload() and prepared.private_json == before
    assert json.loads(build_piece_model_messages(prepared)[1]['content'])['control']['field_slots'] == slots


def test_identical_original_and_answer_are_separate_slots_not_deduplicated():
    text='私は考える時間を大切にしたい。'
    req=refined_request(refined_source(text,text));prepared=prepare_piece_model_request(req)
    slots=json.loads(build_piece_model_messages(prepared)[1]['content'])['control']['field_slots']
    order=['memo_0','answer_text_private_1']
    assert set(slots)==set(order)
    assert [slots[k]['literal'] for k in order]==[text,text]
    assert [slots[k]['source_role'] for k in order]==['ORIGINAL_INPUT','SUPPLEMENTAL_ANSWER']
    assert len({v['source_id'] for v in slots.values()})==2


@pytest.mark.parametrize('change', [{'scalar_start':True},{'scalar_end':True},{'scalar_start':-1},
    {'scalar_end':999},{'scalar_end':0},{'field_path':'created_at'},{'source_id':'other'},{'literal':'override'}])
def test_rehashed_bad_locators_never_become_transport_literals(change):
    import hashlib
    from cocolon_meaning_experience_engine.preparation import PreparedRequest
    prepared=prepare_piece_model_request(selected_request());material=prepared.payload()
    material['control']['block_partition'][0].update(change)
    raw=json.dumps(material,ensure_ascii=False,sort_keys=True,separators=(',',':'))
    forged=PreparedRequest('prep-'+hashlib.sha256(raw.encode()).hexdigest(),raw)
    with pytest.raises(ValueError,match='piece_model_prepared_invalid'):
        build_piece_model_messages(forged)
