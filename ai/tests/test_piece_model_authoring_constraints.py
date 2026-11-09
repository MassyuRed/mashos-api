"""Opt-in source constraints aid the sole author without writing its body.

Fictional CPU materials only. The ordinary transport and candidate validators
stay unchanged; no model is called and no product-quality claim is made here.
"""
from contextlib import ExitStack
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from unittest.mock import patch

import pytest

from cocolon_meaning_experience_engine.preparation import PreparedRequest
from cocolon_meaning_experience_engine.piece_semantic_admission import prepare_piece_model_request
from piece_model_source import SYSTEM_MESSAGE, build_piece_model_messages
from test_cmee_piece_finite_request_reuse import source
from test_cmee_piece_refined_sources import source as refined_source
from test_piece_model_finite_scope import request


EVALUATION = '僕にとって重要なのは、一人で予定を考える時間です。僕は読書が好きではありませんでした。'
NAMED = 'おれが選びたいのは、同僚の森さんと展示を見る時間です。おれはその時間が好きです。まだ、参加する日は決めていません。'


def messages(saved, *, opt_in=True):
    req = request(saved)
    prepared = prepare_piece_model_request(req)
    before = deepcopy(prepared.payload()), prepared.private_json, prepared.request_id
    with ExitStack() as stack:
        for owner in ('piece_v1c.realize_piece_artifact', 'piece_v1c._publicize_source_sentence',
                      'piece_v1c._evaluation_sentence', 'piece_refined.realize_refined_piece_artifact'):
            stack.enter_context(patch('cocolon_meaning_experience_engine.' + owner,
                                     side_effect=AssertionError('no author/prose target')))
        result = build_piece_model_messages(prepared,
            include_authoring_constraints=opt_in, source_request=req)
    assert (prepared.payload(), prepared.private_json, prepared.request_id) == before
    assert result[0] == dict(role='system', content=SYSTEM_MESSAGE)
    return json.loads(result[1]['content']), prepared


def field_constraints(material):
    return material['control']['authoring_constraints']['field_slots']


def test_default_messages_are_byte_identical_and_do_not_admit_or_author():
    req = request(source(EVALUATION, field='memo'))
    prepared = prepare_piece_model_request(req)
    baseline = build_piece_model_messages(prepared)
    with patch('cocolon_meaning_experience_engine.piece_semantic_admission.piece_model_source_plan',
               side_effect=AssertionError('ordinary calls do not derive constraints')):
        assert build_piece_model_messages(prepared, source_request=req) == baseline
        assert build_piece_model_messages(prepared, include_authoring_constraints=False) == baseline
    material = json.loads(baseline[1]['content'])
    assert 'authoring_constraints' not in material['control']


def test_written_evaluation_viewpoint_predicate_and_operators_are_source_parts():
    material, _ = messages(source(EVALUATION, field='memo'))
    slot = field_constraints(material)['memo_0']
    frames = slot['required_evaluations']
    assert [row['narrator_literal'] for row in frames] == ['僕', '僕']
    assert [row['predicate_literal'] for row in frames] == ['重要な', '好きではありませんでした']
    assert [row['target_literal'] for row in frames] == ['一人で予定を考える時間', '読書']
    assert [(row['polarity'], row['temporal_scope'], row['commitment']) for row in frames] == [
        ('AFFIRMATIVE', 'NONPAST', 'ASSERTED'), ('NEGATIVE', 'PAST', 'ASSERTED')]
    assert [row['construction'] for row in frames] == ['にとって', 'は']
    for frame in frames:
        assert [EVALUATION[a:b] for a, b in frame['scalar_parts']] == [
            frame[key] for key in ('narrator_literal', 'predicate_literal', 'target_literal')]
    assert slot['named_people'] == []
    assert 'expected_body' not in str(material['control']['authoring_constraints'])


def test_public_name_alias_comes_from_admitted_written_role_without_target_prose():
    material, _ = messages(source(NAMED, field='memo'))
    slot = field_constraints(material)['memo_0']
    names = slot['named_people']
    assert len(names) == 1
    assert {key: names[0][key] for key in ('written_name', 'source_phrase', 'public_role')} == dict(
        written_name='森さん', source_phrase='同僚の森さん', public_role='同僚')
    assert NAMED[names[0]['scalar_start']:names[0]['scalar_end']] == names[0]['source_phrase']
    assert material['control']['field_slots']['memo_0']['literal'] == NAMED
    assert material['sources'][0]['original']['memo'] == NAMED


def test_two_fields_keep_their_own_axes_and_local_scalar_coordinates():
    material, _ = messages(source(NAMED, field='memo', other=EVALUATION))
    slots = field_constraints(material)
    assert set(slots) == {'memo_0', 'memo_action_1'}
    assert slots['memo_0']['named_people'][0]['public_role'] == '同僚'
    assert slots['memo_action_1']['named_people'] == []
    assert [row['narrator_literal'] for row in slots['memo_action_1']['required_evaluations']] == ['僕', '僕']
    for key, slot in slots.items():
        text = material['sources'][0]['text_fields'][slot['field_path']]
        assert slot['field_path'] == key.rsplit('_', 1)[0]
        for frame in slot['required_evaluations']:
            assert [text[a:b] for a, b in frame['scalar_parts']] == [
                frame[name] for name in ('narrator_literal', 'predicate_literal', 'target_literal')]


def test_refined_answer_cannot_borrow_the_originals_name_or_narrator():
    answer = 'わたしにとって休む時間が必要かもしれません。'
    material, _ = messages(refined_source(original=NAMED, answer=answer))
    slots = field_constraints(material)
    assert slots['memo_0']['named_people'][0]['written_name'] == '森さん'
    original, supplemental = material['sources']
    slot = slots['answer_text_private_1']
    assert slot['source_id'] == supplemental['source_id'] != original['source_id']
    assert slot['source_role'] == 'SUPPLEMENTAL_ANSWER' and slot['named_people'] == []
    assert slot['required_evaluations'][0]['narrator_literal'] == 'わたし'
    assert slot['required_evaluations'][0]['commitment'] == 'POSSIBLE'
    assert '森さん' not in str(slot) and 'おれ' not in str(slot)


@pytest.mark.parametrize('text', [
    '僕は司書に展示の予定を相談しました。',
    '私が選びたいのは、同僚の西さんと同僚の東さんと展示を見る時間です。',
    '私が選びたいのは、西さんと展示を見る時間です。',
    '私にとって、その時間が重要です。',
])
def test_absent_or_unestablished_finite_axes_do_not_gain_constraints(text):
    material, _ = messages(source(text, field='memo'))
    assert 'authoring_constraints' not in material['control']


def test_constraints_require_the_exact_source_request_not_only_matching_text():
    saved = source(EVALUATION, field='memo')
    req = request(saved)
    prepared = prepare_piece_model_request(req)
    changes = [None, request(source(NAMED, field='memo')), replace(req, expected_owner_id='another-owner')]
    for altered in changes:
        with pytest.raises(ValueError, match='piece_model_prepared_invalid'):
            build_piece_model_messages(prepared, include_authoring_constraints=True, source_request=altered)


@pytest.mark.parametrize('change', [
    lambda p: p['control']['block_partition'][0].update(field_path='memo_action'),
    lambda p: p['control']['block_partition'][0].update(source_id='other-source'),
    lambda p: p['sources'][0]['original'].update(memo='私は読書が好きです。'),
    lambda p: p['sources'][0]['text_fields'].update(memo='私は読書が好きです。'),
])
def test_resealed_transport_mutations_cannot_supply_authoring_constraints(change):
    req = request(source(EVALUATION, field='memo'))
    prepared = prepare_piece_model_request(req)
    material = prepared.payload()
    change(material)
    encoded = json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)
    forged = replace(prepared, private_json=encoded,
                     request_id='prep-' + hashlib.sha256(encoded.encode()).hexdigest())
    assert type(forged) is PreparedRequest
    with pytest.raises(ValueError, match='piece_model_prepared_invalid'):
        build_piece_model_messages(forged, include_authoring_constraints=True, source_request=req)


def test_opt_in_flag_has_to_be_a_boolean():
    req = request(source(EVALUATION, field='memo'))
    with pytest.raises(ValueError, match='piece_model_prepared_invalid'):
        build_piece_model_messages(prepare_piece_model_request(req),
            include_authoring_constraints=1, source_request=req)
