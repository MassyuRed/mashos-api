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
    '私が選びたいのは、同僚の西さんと同僚の東さんと展示を見る時間です。',
    '私が選びたいのは、西さんと展示を見る時間です。',
    '私にとって、その時間が重要です。',
])
def test_absent_or_unestablished_finite_axes_do_not_gain_constraints(text):
    material, _ = messages(source(text, field='memo'))
    assert 'authoring_constraints' not in material['control']


@pytest.mark.parametrize('speaker', ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ'))
@pytest.mark.parametrize('ending,predicate,polarity', [
    ('相談しました', '相談する', 'positive'),
    ('伝えませんでした', '伝える', 'negative'),
    ('頼まなかった', '頼む', 'negative'),
])
def test_finite_source_conditions_keep_the_written_narrator_and_each_event(speaker, ending, predicate, polarity):
    text = speaker + 'は司書に展示の予定を' + ending + '。'
    material, _ = messages(source(text, field='memo'))
    slot = field_constraints(material)['memo_0']
    assert slot['required_actions'] == [dict(narrator_literal=speaker,
        predicate_literal=ending, predicate=predicate, polarity=polarity,
        temporal_scope='past', modality='fact', voice='active', relative_day='',
        arguments=[dict(case='に', literal='司書'), dict(case='を', literal='展示の予定')],
        scalar_start=0, scalar_end=len(text))]
    assert slot['named_people'] == [] and slot['required_evaluations'] == []
    assert 'expected_body' not in str(slot)


def test_different_written_narrators_do_not_share_polarity_or_tense():
    first = '僕は司書に展示の予定を相談しました。'
    second = '私は受付係に開場の時刻を伝えませんでした。'
    material, _ = messages(source(first + second, field='memo'))
    actions = field_constraints(material)['memo_0']['required_actions']
    assert [(row['narrator_literal'], row['polarity'], row['temporal_scope']) for row in actions] == [
        ('僕', 'positive', 'past'), ('私', 'negative', 'past')]
    assert [(row['scalar_start'], row['scalar_end']) for row in actions] == [
        (0, len(first)), (len(first), len(first + second))]


@pytest.mark.parametrize('target', ('参加する日は', '毎日続けるかは'))
def test_undecided_target_does_not_add_a_generation_hint(target):
    text = '僕は読書が好きでした。まだ、' + target + '決めていません。'
    material, _ = messages(source(text, field='memo'))
    slot = field_constraints(material)['memo_0']
    assert 'required_undecided_targets' not in slot
    assert 'finite_scope_instruction' not in material['control']['authoring_constraints']
    assert slot['required_evaluations'][0]['temporal_scope'] == 'PAST'
    assert material['control']['field_slots']['memo_0']['literal'] == text


def test_action_conditions_are_local_to_original_fields_and_the_answer():
    original = '僕は司書に展示の予定を相談しました。まだ、参加する日は決めていません。'
    answer = 'わたしは読書が好きでした。'
    material, _ = messages(refined_source(original=original, answer=answer))
    slots = field_constraints(material)
    original_slot, answer_slot = slots['memo_0'], slots['answer_text_private_1']
    assert original_slot['source_role'] == 'ORIGINAL_INPUT'
    assert answer_slot['source_role'] == 'SUPPLEMENTAL_ANSWER'
    assert original_slot['source_id'] != answer_slot['source_id']
    assert original_slot['required_actions'][0]['narrator_literal'] == '僕'
    assert original_slot['required_actions'][0]['polarity'] == 'positive'
    assert original_slot['required_actions'][0]['scalar_start'] == 0
    assert 'required_undecided_targets' not in original_slot
    assert answer_slot['required_evaluations'][0]['narrator_literal'] == 'わたし'
    assert 'required_actions' not in answer_slot and 'required_undecided_targets' not in answer_slot


@pytest.mark.parametrize('text', [
    '司書に展示の予定を相談しました。',
    'あなたは司書に展示の予定を相談しました。',
    '私は司書に展示の予定を相談したかもしれない。',
    '私は司書に展示の予定を相談したと聞いた。',
    '私は司書に展示の予定を相談する。',
    '私は司書に展示の予定を相談したなら。',
    '私は司書に展示の予定を相談しました。まだ、',
    '私は司書に展示の予定を相談しました！',
    '私は司書に展示の予定を相談し、受付係に時刻を伝えました。',
    '私は司書に展示の予定を伝えられました。',
])
def test_source_action_projection_does_not_parse_a_substring_or_infer_a_writer(text):
    from piece_model_source import _source_action_constraint
    assert _source_action_constraint(text) is None


def test_explicit_kara_passive_does_not_receive_action_rewrite_conditions():
    text = '私は司書から展示の予定を伝えられました。'
    material, _ = messages(source(text, field='memo'))
    assert 'authoring_constraints' not in material['control']
    assert material['control']['field_slots']['memo_0']['literal'] == text


@pytest.mark.parametrize('passive_first', [True, False])
def test_passive_and_active_in_one_field_receive_no_action_conditions(passive_first):
    active = '僕は受付係に開場の時刻を伝えませんでした。'
    passive = '私は司書から展示の予定を頼まれました。'
    text = passive + active if passive_first else active + passive
    material, _ = messages(source(text, field='memo'))
    assert 'authoring_constraints' not in material['control']
    assert material['control']['field_slots']['memo_0']['literal'] == text


@pytest.mark.parametrize('passive_field', ('memo', 'memo_action'))
def test_passive_field_does_not_suppress_another_fields_active_conditions(passive_field):
    active = '僕は受付係に開場の時刻を伝えませんでした。'
    passive = '私は司書から展示の予定を頼まれました。'
    material, _ = messages(source(passive, field=passive_field, other=active))
    constraints = field_constraints(material)
    active_field = 'memo_action' if passive_field == 'memo' else 'memo'
    assert len(constraints) == 1
    slot = next(iter(constraints.values()))
    assert slot['field_path'] == active_field
    assert slot['required_actions'][0]['narrator_literal'] == '僕'
    assert slot['required_actions'][0]['polarity'] == 'negative'
    assert slot['required_actions'][0]['scalar_start'] == 0


def test_passive_suppression_preserves_existing_evaluation_conditions_in_its_field():
    text = '私は司書から展示の予定を頼まれました。僕は読書が好きでした。'
    material, _ = messages(source(text, field='memo'))
    slot = field_constraints(material)['memo_0']
    assert 'required_actions' not in slot
    assert slot['required_evaluations'][0]['narrator_literal'] == '僕'
    assert slot['required_evaluations'][0]['temporal_scope'] == 'PAST'


def test_evaluation_only_wire_has_no_new_condition_or_instruction():
    material, _ = messages(source(EVALUATION, field='memo'))
    constraints = material['control']['authoring_constraints']
    assert set(constraints) == {'instruction', 'field_slots'}
    assert set(field_constraints(material)['memo_0']) == {
        'source_id', 'source_role', 'field_path', 'scalar_start', 'scalar_end',
        'named_people', 'required_evaluations'}


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
