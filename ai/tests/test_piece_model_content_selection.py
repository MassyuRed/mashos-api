"""Current Piece generation receives source-bound whole-content duties.

The provider responses below are fictional fixed candidates, not new 4B
generations. They verify the actual request/receipt/independent-admission
route, source preservation and budgeting; they make no model-quality claim.
"""
import asyncio
from copy import deepcopy
import json

import httpx
import pytest

import piece_model_source as model
from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.piece_semantic_admission import (
    PieceModelInputV1, prepare_piece_model_request,
)
from test_cmee_piece_finite_request_reuse import source
from test_cmee_piece_refined_sources import source as refined_source
from test_piece_model_authoring_constraints import messages, NAMED
from test_piece_model_finite_scope import request


def selection_for(saved):
    material, prepared = messages(saved)
    return material, material['control']['content_selection'], prepared


def selected_literals(material, selection, key):
    original = material['control']['field_slots'][key]
    return [original['literal'][
        row['scalar_start'] - original['scalar_start']:
        row['scalar_end'] - original['scalar_start']]
        for row in selection['field_slots'][key]['selected']]


def test_whole_field_keeps_expression_reference_and_unresolved_context_together():
    material, selection, _ = selection_for(source(NAMED, field='memo'))
    rows = selection['field_slots']['memo_0']['selected']
    assert ''.join(selected_literals(material, selection, 'memo_0')) == NAMED
    assert len(rows) == 3 and rows[-1]['operation'] == 'KEEP_COMPLETE_SOURCE_CONTEXT'
    assert all(row['required'] and row['status'] == 'selected' for row in rows)
    # The old source-bound reference responsibility closes over the complete
    # earlier proposition. A content plan cannot excerpt the final preference.
    reference = [row for row in selection['relations'] if row['relation'] != 'SOURCE_ORDER']
    assert len(reference) == 1
    assert reference[0]['source_node_id'] == rows[1]['node_id']
    assert reference[0]['target_node_id'] == rows[0]['node_id']
    assert selection['required_source_omission_allowed'] is False
    assert selection['deferred_by_budget'] == []
    assert 'expected_body' not in str(selection) and NAMED not in json.dumps(selection, ensure_ascii=False)


def test_duplicate_required_propositions_are_not_discarded_by_lexical_identity_or_budget():
    sentence = '僕は司書に展示の予定を相談しました。'
    material, selection, _ = selection_for(source(sentence * 6, field='memo'))
    rows = selection['field_slots']['memo_0']['selected']
    assert len(rows) == len({row['node_id'] for row in rows}) == 6
    assert selected_literals(material, selection, 'memo_0') == [sentence] * 6
    assert selection['deferred_by_budget'] == []
    assert len(json.dumps(material, ensure_ascii=False).encode()) < model.MAX_REQUEST_BYTES


def test_each_field_and_written_paragraph_has_its_own_complete_required_inventory():
    first = '僕は司書に展示の予定を相談しました。'
    second = '私は受付係に開場の時刻を伝えませんでした。'
    saved = source(first + '\n' + second, field='memo', other=first)
    material, selection, _ = selection_for(saved)
    assert set(selection['field_slots']) == {'memo_0', 'memo_1', 'memo_action_2'}
    assert [selected_literals(material, selection, key) for key in selection['field_slots']] == [
        [first], [second], [first]]
    for key, slot in selection['field_slots'].items():
        original = material['control']['field_slots'][key]
        assert slot['source_id'] == original['source_id']
        assert slot['field_path'] == original['field_path']
        assert [node for group in slot['reading_groups'] for node in group] == [
            row['node_id'] for row in slot['selected']]
    # SOURCE_ORDER is a written sequence, never a cause or a clock relation.
    assert selection['source_order_implies_cause_or_time'] is False
    assert all(row['relation'] == 'SOURCE_ORDER' for row in selection['relations'])


@pytest.mark.parametrize('text,relation', [
    ('時間が限られているので、私は読書を選びたいです。', 'SOURCE_EXPLICIT_REASON'),
    ('雨が降るなら、私は読書を選びたいです。', 'SOURCE_EXPLICIT_CONDITION'),
    ('時間が限られているけれど、私は読書を選びたいです。', 'SOURCE_EXPLICIT_CONCESSION'),
    ('以前は、私は読書が好きでした。', 'SOURCE_EXPLICIT_TIME_CONTEXT'),
])
def test_whole_scope_and_expression_are_source_coordinates_not_new_assertions(text, relation):
    material, selection, _ = selection_for(source(text, field='memo'))
    scope = next(row for row in selection['relations'] if row['relation'] == relation)
    source_field = material['sources'][0]['text_fields']['memo']
    a, b = scope['scope_scalar_span']
    c, d = scope['expression_scalar_span']
    assert source_field[a:b] and source_field[c:d].startswith('私は')
    assert scope['field_slot'] == 'memo_0'
    assert selected_literals(material, selection, 'memo_0') == [text]
    assert 'scope_literal' not in scope and 'expression_literal' not in scope


def test_original_and_answer_inventories_never_borrow_each_others_sources_or_versions():
    saved = refined_source(original='僕は司書に展示の予定を相談しました。',
        answer='わたしは読書が好きでした。')
    material, selection, _ = selection_for(saved)
    original, answer = material['sources']
    first = selection['field_slots']['memo_0']
    second = selection['field_slots']['answer_text_private_1']
    assert (first['source_id'], first['source_role'], first['source_version']) == (
        original['source_id'], 'ORIGINAL_INPUT', original['source_version'])
    assert (second['source_id'], second['source_role'], second['source_version']) == (
        answer['source_id'], 'SUPPLEMENTAL_ANSWER', answer['source_version'])
    assert first['source_id'] != second['source_id']
    assert selected_literals(material, selection, 'memo_0') == [saved.original.original_text]
    assert selected_literals(material, selection, 'answer_text_private_1') == [saved.supplemental.answer_text_private]
    assert selection['relations'] == []


def test_nonwritten_selected_feeling_remains_context_not_an_added_image_proposition():
    text = '私は司書に展示の予定を相談しました。'
    material, selection, _ = selection_for(source(text, field='memo', emotions=['喜び'],
        details=[dict(type='喜び', strength='strong')]))
    assert selected_literals(material, selection, 'memo_0') == [text]
    assert selection['context_only']
    assert all(row['status'] == 'context_only' for row in selection['context_only'])
    assert '喜び' not in json.dumps(selection, ensure_ascii=False)


def test_default_off_projection_stays_exact_and_does_not_read_a_source_plan():
    saved = source('私は司書に展示の予定を相談しました。', field='memo')
    material, _ = messages(saved, opt_in=False)
    assert 'content_selection' not in material['control']


def test_unread_source_does_not_gain_a_selection_or_a_completed_meaning():
    text = '私は司書に展示の予定を相談しました。まだ、'
    material, _ = messages(source(text, field='memo'))
    assert material['control']['field_slots']['memo_0']['literal'] == text
    assert 'content_selection' not in material['control']
    assert 'authoring_constraints' not in material['control']


@pytest.mark.parametrize('ending,accepted', [('伝えた', True), ('伝えなかった', False)])
def test_current_provider_receives_all_duties_without_forcing_one_output_sentence_per_duty(ending, accepted):
    original = '私は友人に日程を相談しました。私は司書に会場の変更を伝えました。'
    body = '私は友人に日程を相談し、司書に会場の変更を' + ending + '。'
    req = request(source(original, field='memo'))
    prepared = prepare_piece_model_request(req)
    before = deepcopy(prepared.payload()), prepared.private_json, req.source
    seen = []
    def provider(value):
        payload = json.loads(value.content)
        material = json.loads(payload['messages'][1]['content'])
        selection = material['control']['content_selection']
        assert selected_literals(material, selection, 'memo_0') == [
            '私は友人に日程を相談しました。', '私は司書に会場の変更を伝えました。']
        assert len(selection['field_slots']['memo_0']['selected']) == 2
        assert payload['messages'][0]['content'] == model.SYSTEM_MESSAGE
        seen.append(material)
        return httpx.Response(200, json=dict(model=payload['model'],
            candidate_format='piece.field_slots.v1', choices=[dict(finish_reason='stop',
            message=dict(role='assistant', content=json.dumps(dict(field_blocks=dict(memo_0=body)),
                                                          ensure_ascii=False)))]))
    configured = model.Shared4BPieceModelSource(endpoint='https://piece.invalid/v1/chat/completions',
        model='synthetic-author', api_key='synthetic-private-source-key-32',
        transport=httpx.MockTransport(provider))
    receipt = asyncio.run(configured(prepared, source_request=req))
    outcome = MeaningExperienceEngine().generate(req, semantic_input=PieceModelInputV1(prepared, receipt))
    assert (outcome.artifact is not None) is accepted
    if accepted:
        assert outcome.artifact.piece_text == body and body.count('。') == 1
    assert len(seen) == 1 and receipt.raw_output == json.dumps(
        dict(field_blocks=dict(memo_0=body)), ensure_ascii=False)
    assert (prepared.payload(), prepared.private_json, req.source) == before
