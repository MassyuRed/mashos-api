"""Active transport ranges retain raw provenance without resurrecting old text.

These synthetic private snapshots exercise transport projection only. Saved
thread eligibility and whole-Piece meaning are verified by their owners.
"""
from dataclasses import replace
import hashlib
import json

import pytest

from cocolon_meaning_experience_engine.piece_semantic_admission import prepare_piece_model_request
from piece_model_source import build_piece_model_messages
from test_cmee_piece_refined_sources import source, request


FIRST = '私は考えをノートに書いた。'
OLD = '私は仕事を続けたい。'
LAST = '私は資料を調べた。'
NEW = '私は家族を守りたい。'


def updated(*, operation='REVISE', separator=''):
    memo = FIRST + OLD + separator + LAST
    answer = ('「' + OLD + '」ではなく「' + NEW + '」です。' if operation == 'REVISE'
              else '「' + OLD + '」は取り消します。')
    value = source(memo, answer)
    start = answer.index(NEW) if operation == 'REVISE' else None
    return replace(value, supplemental_update_operation=operation,
        original_active_ranges=(('memo', 0, len(FIRST)),
            ('memo', len(FIRST + OLD + separator), len(memo))),
        supplemental_active_range=(start, start + len(NEW)) if start is not None else None)


@pytest.mark.parametrize('operation', ['REVISE', 'WITHDRAW'])
def test_active_wire_omits_old_and_control_text_but_keeps_private_sources(operation):
    value = updated(operation=operation)
    prepared = prepare_piece_model_request(request(value))
    before = prepared.private_json
    messages = build_piece_model_messages(prepared)
    material = json.loads(messages[1]['content'])
    slots = material['control']['field_slots']
    assert prepared.private_json == before
    assert prepared.payload()['sources'][0]['original']['memo'] == FIRST + OLD + LAST
    assert prepared.payload()['sources'][1]['text_fields']['answer_text_private'] == value.supplemental.answer_text_private
    assert OLD not in messages[1]['content']
    assert value.supplemental.answer_text_private not in messages[1]['content']
    assert material['control']['active_source_update'] == operation
    assert material['sources'][0]['source_commitment'] == value.original_commitment
    assert material['sources'][1]['source_commitment'] == value.supplemental_commitment
    assert len(material['sources']) == 2
    assert all('text_fields' not in item and 'evidence' not in item for item in material['sources'])
    assert 'memo' not in material['sources'][0]['original']
    assert material['sources'][0]['original']['emotions'] == ['平穏']
    assert 'literal' not in slots['memo_0']
    ranges = slots['memo_0']['literal_ranges']
    assert [item['literal'] for item in ranges] == [FIRST, LAST]
    assert slots['memo_0']['field_sha256'] == hashlib.sha256((FIRST + OLD + LAST).encode()).hexdigest()
    assert [(item['scalar_start'], item['scalar_end']) for item in ranges] == [(0, len(FIRST)),
        (len(FIRST + OLD), len(FIRST + OLD + LAST))]
    for item in ranges:
        original = FIRST + OLD + LAST
        assert original[item['scalar_start']:item['scalar_end']] == item['literal']
        assert original.encode()[item['utf8_start']:item['utf8_end']].decode() == item['literal']
    if operation == 'REVISE':
        assert list(slots) == ['answer_text_private_1', 'memo_0']  # Canonical JSON key ordering.
        assert slots['answer_text_private_1']['literal_ranges'][0]['literal'] == NEW
    else:
        assert list(slots) == ['memo_0']
        assert material['sources'][1]['active_text_ranges'] == []


def test_active_ranges_do_not_collapse_written_paragraph_boundaries():
    value = updated(separator='\r\n')
    prepared = prepare_piece_model_request(request(value))
    partitions = prepared.payload()['control']['block_partition']
    assert len(partitions) == 3
    assert partitions[0]['scalar_ranges'] == [[0, len(FIRST)]]
    assert partitions[1]['scalar_ranges'] == [[len(FIRST + OLD + '\r\n'), len(FIRST + OLD + '\r\n' + LAST)]]


@pytest.mark.parametrize('operation', ['REVISE', 'WITHDRAW'])
def test_authoring_conditions_cover_only_active_parts_including_withdrawal_without_answer_body(operation):
    value = updated(operation=operation)
    selected_request = request(value)
    prepared = prepare_piece_model_request(selected_request)
    messages = build_piece_model_messages(prepared, include_authoring_constraints=True,
                                         source_request=selected_request)
    material = json.loads(messages[1]['content'])
    control = material['control']
    assert set(control['content_selection']['field_slots']) == set(control['field_slots'])
    assert OLD not in messages[1]['content']
    assert value.supplemental.answer_text_private not in messages[1]['content']
    assert control['content_selection']['required_source_omission_allowed'] is False
    assert prepared.payload()['sources'][0]['original']['memo'] == FIRST + OLD + LAST


@pytest.mark.parametrize('ranges', [
    (), (('memo', -1, 2),), (('memo', 0, 9999),),
    (('memo', 0, len(FIRST)), ('memo', 1, len(FIRST))),
    (('memo_action', 0, 2),), (('memo', False, 2),),
])
def test_invalid_active_ranges_are_not_repaired(ranges):
    with pytest.raises(ValueError):
        prepare_piece_model_request(request(replace(updated(), original_active_ranges=ranges)))
