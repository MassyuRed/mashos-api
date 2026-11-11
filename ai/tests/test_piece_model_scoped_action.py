"""Whole S7 owns a written reason/concession and its completed action.

The six public fictional CPU cases are fixed preparation inputs, not model
outputs or teachers. No provider, GPU or saved-record service is called.
"""
from copy import deepcopy
from dataclasses import replace
import hashlib
import json

import pytest

from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.piece_semantic_admission import (
    piece_model_source_plan, prepare_piece_model_request,
)
from cocolon_meaning_experience_engine.piece_source import (
    _scoped_finite_self_person_action, piece_source_text,
    validate_piece_expression_scopes,
)
from cocolon_meaning_experience_engine.piece_v1c import PieceArtifact
from piece_model_source import SYSTEM_MESSAGE, build_piece_model_messages
from piece_v2_content_policy import (
    _piece_model_read_block, validate_piece_model_preservation,
    validate_source_meaning_preservation,
)
from piece_v2_contract import PieceContractError
from test_cmee_piece_finite_request_reuse import source
from test_cmee_piece_refined_sources import source as refined_source
from test_piece_model_finite_scope import request
from test_piece_model_narrator_voice import evaluate


# Copied unchanged from scoped-action-trial/cases.py. Keep this test independent
# of scratch preparation assets when it runs in the repository's CI.
CASES = [
    ('ACTION-REASON-CONSULT', '予定が重なっているので、僕は友人に予定を相談しました。',
     '予定が重なっているので、僕は友人に予定を相談した。'),
    ('ACTION-CONCESSION-NEG-CONSULT', '会議が終わったけれど、私は上司に予定を相談しませんでした。',
     '会議が終わったけれど、私は上司に予定を相談しなかった。'),
    ('ACTION-REASON-REQUEST', '朝の作業が終わったので、わたしは同僚に資料の確認を頼みました。',
     '朝の作業が終わったので、わたしは同僚に資料の確認を頼んだ。'),
    ('ACTION-CONCESSION-TELL', '雨が続いているけれども、俺は受付係に集合の時刻を伝えました。',
     '雨が続いているけれども、俺は受付係に集合の時刻を伝えた。'),
    ('ACTION-REASON-NEG-REQUEST', '手順が変わったので、ぼくは先生に道具の準備を頼みませんでした。',
     '手順が変わったので、ぼくは先生に道具の準備を頼まなかった。'),
    ('ACTION-CONCESSION-NEG-TELL', '連絡が届いたけれど、おれは友人に荷物の到着を伝えませんでした。',
     '連絡が届いたけれど、おれは友人に荷物の到着を伝えなかった。'),
]
MODES = ('自己理解', '平穏')
BASELINE_SYSTEM_SHA256 = 'cc896e3e38f9bd241243beeaa5df15c32ac9648c14f84f385be5a2fe1bfe85f0'


def saved(text, *, mode='自己理解', other=None):
    return source(text, field='memo', other=other, emotions=[mode],
                  details=[dict(type=mode, strength='medium')])


def material(snapshot, *, opt_in=True):
    req = request(snapshot)
    prepared = prepare_piece_model_request(req)
    before = deepcopy(prepared.payload()), prepared.private_json, prepared.request_id
    messages = build_piece_model_messages(prepared,
        include_authoring_constraints=opt_in, source_request=req)
    assert (prepared.payload(), prepared.private_json, prepared.request_id) == before
    assert messages[0] == dict(role='system', content=SYSTEM_MESSAGE)
    return json.loads(messages[1]['content']), prepared


def action_hints(payload):
    return payload['control'].get('authoring_constraints', {}).get('field_slots', {})


def all_actions(payload):
    return [action for slot in action_hints(payload).values()
            for action in slot.get('required_actions', [])]


def assert_local_action_ranges(payload, key):
    slot = action_hints(payload)[key]
    source_part = next(part for part in payload['sources']
                       if part['source_id'] == slot['source_id'])
    field = source_part['text_fields'][slot['field_path']]
    wire_slot = payload['control']['field_slots'][key]
    assert wire_slot['literal'] == field[slot['scalar_start']:slot['scalar_end']]
    assert slot['source_role'] == wire_slot['source_role']
    for action in slot['required_actions']:
        scope = action['source_scope']
        whole = field[scope['scalar_start']:scope['scalar_end']]
        inner = field[action['scalar_start']:action['scalar_end']]
        assert whole == scope['literal']
        assert inner == action['source_literal']
        assert action['scalar_start'] == scope['expression_scalar_start']
        assert action['scalar_end'] == scope['expression_scalar_end']
        assert (whole == scope['prefix_literal'] + inner
                and action['scalar_start'] == scope['scalar_start'] + len(scope['prefix_literal']))
        assert scope['marker'] in ('ので', 'けれど', 'けれども')
        assert scope['relation'] == ('SOURCE_EXPLICIT_REASON' if scope['marker'] == 'ので'
                                     else 'SOURCE_EXPLICIT_CONCESSION')
        assert action['semantic_roles']['subject'] == 'SELF'
        assert action['voice'] == 'active' and action['modality'] == 'fact'
        assert action['temporal_scope'] == 'past'


@pytest.mark.parametrize('mode', MODES)
@pytest.mark.parametrize('case_id,before,after', CASES, ids=[c[0] for c in CASES])
def test_fixed_six_modes_keep_native_source_and_adopt_only_received_register(
        mode, case_id, before, after):
    snapshot = saved(before, mode=mode)
    frozen = snapshot, snapshot.saved_original_json
    req = request(snapshot)
    prepared = prepare_piece_model_request(req)
    prepared_before = deepcopy(prepared.payload()), prepared.private_json, prepared.request_id

    native = MeaningExperienceEngine().generate(req)
    assert native.status == EngineStatus.GENERATED, (case_id, mode, native.reason_codes)
    assert native.artifact.body_blocks == (before,)
    assert not native.artifact_plan.declaration_eligible
    assert native.artifact.eligible_formats == ('short_essay',)
    assert [d.operation for d in native.artifact_plan.duties] == ['KEEP_COMPLETE_SOURCE_CONTEXT']
    validate_source_meaning_preservation(native.source_meaning, native.artifact_plan, native.artifact)

    meaning, plan = piece_model_source_plan(req)
    assert len(meaning.expression_scopes) == 1
    scope = meaning.expression_scopes[0]
    comma = before.index('、')
    assert scope.scope_scalar_span == (0, comma)
    assert scope.expression_scalar_span == (comma + 1, len(before))
    assert scope.scope_utf8_span == (0, len(before[:comma].encode()))
    assert scope.expression_utf8_span == (len(before[:comma + 1].encode()), len(before.encode()))
    assert meaning.graph.nodes[0].node_kind == (
        'PIECE_SOURCE_REASON_SCOPED_EXPRESSION' if scope.marker == 'ので'
        else 'PIECE_SOURCE_CONCESSION_SCOPED_EXPRESSION')
    assert [d.operation for d in plan.duties] == ['KEEP_COMPLETE_SOURCE_CONTEXT']
    validate_piece_expression_scopes(meaning)
    # The whole clause is never a flat event-key source. S7 owns the prefix;
    # only the complete main-clause finite key has register equivalence.
    assert _piece_model_read_block(before) is None
    assert _piece_model_read_block(before[comma + 1:]) == _piece_model_read_block(after[comma + 1:])
    out = evaluate(snapshot, [after])
    assert out.status == EngineStatus.GENERATED, (case_id, mode, out.reason_codes)
    assert out.artifact.body_blocks == (after,)
    assert (snapshot, snapshot.saved_original_json) == frozen
    assert (prepared.payload(), prepared.private_json, prepared.request_id) == prepared_before
    # Native S7 remains literal; only the explicit model comparison changes
    # the finite register, without rewriting the candidate or calling an author.
    with pytest.raises(PieceContractError):
        validate_source_meaning_preservation(meaning, plan, out.artifact)
    validate_source_meaning_preservation(meaning, plan, out.artifact, _model_register=True)
    payload, _ = material(snapshot)
    assert len(all_actions(payload)) == 1
    assert_local_action_ranges(payload, 'memo_0')


MUTATIONS = [
    ('predicate', '予定が重なっているので、僕は友人に予定を頼んだ。'),
    ('negative', '予定が重なっているので、僕は友人に予定を相談しなかった。'),
    ('nonpast', '予定が重なっているので、僕は友人に予定を相談する。'),
    ('modality', '予定が重なっているので、僕は友人に予定を相談したかもしれない。'),
    ('voice', '予定が重なっているので、僕は友人に予定を相談された。'),
    ('self', '予定が重なっているので、私は友人に予定を相談した。'),
    ('self_omitted', '予定が重なっているので、友人に予定を相談した。'),
    ('counterpart', '予定が重なっているので、僕は同僚に予定を相談した。'),
    ('object', '予定が重なっているので、僕は友人に旅程を相談した。'),
    ('written_case', '予定が重なっているので、僕は友人から予定を相談した。'),
    ('honorific', '予定が重なっているので、僕は友人さんに予定を相談した。'),
    ('argument_order', '予定が重なっているので、僕は予定を友人に相談した。'),
    ('extra_subject_pause', '予定が重なっているので、僕は、友人に予定を相談した。'),
    ('premise_dropped', '僕は友人に予定を相談した。'),
    ('premise_polarity', '予定が重なっていないので、僕は友人に予定を相談した。'),
    ('reason_to_concession', '予定が重なっているけれど、僕は友人に予定を相談した。'),
    ('reason_to_condition', '予定が重なっているなら、僕は友人に予定を相談した。'),
    ('ambiguous_from', '予定が重なっているから、僕は友人に予定を相談した。'),
    ('ambiguous_noni', '予定が重なっているのに、僕は友人に予定を相談した。'),
    ('fronted_self', '僕は予定が重なっているので、友人に予定を相談した。'),
    ('new_result', '予定が重なっているので、僕は友人に予定を相談した。問題は解決した。'),
    ('repeat', '予定が重なっているので、僕は友人に予定を相談した。僕は友人に予定を相談した。'),
]


@pytest.mark.parametrize('axis,body', MUTATIONS, ids=[m[0] for m in MUTATIONS])
def test_full_outer_context_inner_surface_and_each_event_axis_must_remain(axis, body):
    assert evaluate(saved(CASES[0][1]), [body]).artifact is None, axis


def test_equal_event_key_cannot_license_an_argument_reorder():
    inner = '僕は友人に予定を相談した。'
    reordered = '僕は予定を友人に相談した。'
    assert _piece_model_read_block(inner) == _piece_model_read_block(reordered)
    assert evaluate(saved(CASES[0][1]), ['予定が重なっているので、' + reordered]).artifact is None


EXCLUDED = [
    ('condition', '余裕があるなら、僕は友人に予定を相談しました。'),
    ('ambiguous_kara', '予定が重なっているから、僕は友人に予定を相談しました。'),
    ('ambiguous_noni', '予定が重なっているのに、僕は友人に予定を相談しました。'),
    ('time_topic', '今は、僕は友人に予定を相談しました。'),
    ('inner_day', '予定が重なっているので、昨日は僕は友人に予定を相談しました。'),
    ('quotation', '友人が「私は帰りたい」と言ったので、僕は友人に予定を相談しました。'),
    ('quoted_operator', '友人が「忙しいので帰りたい」と言ったけれど、僕は友人に予定を相談しました。'),
    ('named_person', '予定が重なっているので、僕は友人の山田さんに予定を相談しました。'),
    ('outer_self', '私は忙しいので、僕は友人に予定を相談しました。'),
    ('same_outer_self', '僕は忙しいので、僕は友人に予定を相談しました。'),
    ('passive', '予定が重なっているので、僕は友人から予定を相談されました。'),
    ('multiple_operator', '雨が降っているので予定は変わったけれど、僕は友人に予定を相談しました。'),
    ('multiple_premise', '雨が降っているので、予定は変わったけれど、僕は友人に予定を相談しました。'),
    ('missing_self', '予定が重なっているので、友人に予定を相談しました。'),
    ('nonpast_action', '予定が重なっているので、僕は友人に予定を相談します。'),
    ('reported_action', '予定が重なっているので、僕は友人に予定を相談したと聞きました。'),
    ('two_actions', '予定が重なっているので、僕は友人に予定を相談し、先生に時刻を伝えました。'),
]


@pytest.mark.parametrize('case_id,text', EXCLUDED, ids=[c[0] for c in EXCLUDED])
def test_excluded_sources_get_no_new_action_scope_or_partial_action_hints(case_id, text):
    snapshot = saved(text, mode='平穏')
    assert _scoped_finite_self_person_action(text) is None
    try:
        meaning, _ = piece_model_source_plan(request(snapshot))
    except PieceContractError:
        # Existing refusal remains refusal; preparation never supplies a new
        # source admission or a partial action merely from a matching suffix.
        pass
    else:
        assert meaning.expression_scopes == (), case_id
    payload, _ = material(snapshot)
    assert not all_actions(payload)
    assert 'scoped_action_instruction' not in payload['control'].get('authoring_constraints', {})


def test_exclusion_does_not_revoke_an_existing_literal_keep_or_scoped_wish():
    conditional = EXCLUDED[0][1]
    out = evaluate(saved(conditional, mode='平穏'), [conditional])
    assert out.artifact and out.artifact.body_blocks == (conditional,)
    wish = '予定が重なっているので、僕は友人と話したい。'
    snapshot = saved(wish, mode='平穏')
    meaning, plan = piece_model_source_plan(request(snapshot))
    assert _scoped_finite_self_person_action(wish) is None
    assert len(meaning.expression_scopes) == 1
    assert [d.operation for d in plan.duties] == ['SOURCE_SCOPED_EXPRESSION_TO_FIRST_PERSON']
    payload, _ = material(snapshot)
    assert not all_actions(payload)


def test_multiple_sentences_and_fields_keep_source_and_hint_coordinates_separate():
    first, second, third = CASES[0], CASES[1], CASES[2]
    memo = first[1] + second[1]
    snapshot = saved(memo, other=third[1])
    payload, _ = material(snapshot)
    slots = action_hints(payload)
    assert set(slots) == {'memo_0', 'memo_action_1'}
    assert len(slots['memo_0']['required_actions']) == 2
    assert len(slots['memo_action_1']['required_actions']) == 1
    for key in slots:
        assert_local_action_ranges(payload, key)
    memo_actions = slots['memo_0']['required_actions']
    assert memo_actions[0]['source_scope']['scalar_start'] == 0
    assert memo_actions[1]['source_scope']['scalar_start'] == len(first[1])
    assert memo_actions[1]['scalar_start'] == len(first[1]) + second[1].index('、') + 1
    assert slots['memo_action_1']['required_actions'][0]['source_scope']['scalar_start'] == 0
    assert slots['memo_action_1']['required_actions'][0]['scalar_start'] == third[1].index('、') + 1

    meaning, _ = piece_model_source_plan(request(snapshot))
    view = piece_source_text(meaning)
    third_scope = meaning.expression_scopes[2]
    offset = len(memo) + 2
    assert third_scope.scope_scalar_span == (offset, offset + third[1].index('、'))
    assert third_scope.scope_utf8_span == (
        len(view[:offset].encode()), len(view[:offset + third[1].index('、')].encode()))
    good = [first[2] + second[2], third[2]]
    assert evaluate(snapshot, good).artifact
    for damaged in ([good[1], good[0]],
                    [first[2], second[2] + third[2]],
                    [good[0], third[2].replace('わたしは', '')]):
        assert evaluate(snapshot, damaged).artifact is None


def test_refined_original_action_and_supplement_keep_their_own_source_and_narrator():
    snapshot = refined_source(original=CASES[0][1], answer='今は、私は嬉しいです。')
    frozen = snapshot, snapshot.original.saved_original_json
    payload, _ = material(snapshot)
    original, supplemental = payload['sources']
    slot = action_hints(payload)['memo_0']
    assert slot['source_id'] == original['source_id'] != supplemental['source_id']
    assert slot['source_role'] == 'ORIGINAL_INPUT'
    assert_local_action_ranges(payload, 'memo_0')
    assert all(action['narrator_literal'] == '僕' for action in all_actions(payload))
    assert not any(row.get('required_actions') for row in action_hints(payload).values()
                   if row['source_id'] == supplemental['source_id'])
    good = [CASES[0][2], '今は、私は嬉しい。']
    assert evaluate(snapshot, good).artifact
    for damaged in ([CASES[0][2].replace('僕は', '私は'), good[1]],
                    [good[0], good[1].replace('私は', '僕は')],
                    [good[1], good[0]]):
        assert evaluate(snapshot, damaged).artifact is None
    assert (snapshot, snapshot.original.saved_original_json) == frozen


def test_an_unrepresented_clause_prevents_partial_action_conditions():
    snapshot = saved(CASES[0][1] + '返事はまだ分からない。', mode='平穏')
    payload, _ = material(snapshot)
    assert not all_actions(payload)
    assert payload['control']['field_slots']['memo_0']['literal'] == snapshot.original_text
    assert 'scoped_action_instruction' not in payload['control'].get('authoring_constraints', {})
    # An independently invalid source cannot obtain a valid fragment's hints.
    invalid = saved(CASES[0][1] + '誰に頼みましたか。', mode='平穏')
    payload, _ = material(invalid)
    assert 'authoring_constraints' not in payload['control']


@pytest.mark.parametrize('tail', [
    'まだ、決めていません。',
    '私は静かに休みたい。',
    '資料を読みました。',
    '作業をする。',
    '予定が重なるなら、僕は友人に予定を相談しました。',
])
def test_new_action_does_not_supply_legacy_reservation_or_literal_account_qualification(tail):
    # These complete mixtures were refused by the actual preimage. The new
    # scoped action is not an extra legacy action for qualifying their tails.
    # Use the REQUEST preimage: the older lexical/suru account can already
    # qualify some CONSULT mixtures, whose admission this change must retain.
    snapshot = saved(CASES[2][1] + tail)
    with pytest.raises(PieceContractError) as exc:
        piece_model_source_plan(request(snapshot))
    assert exc.value.detail == 'expression_meaning_not_admitted'
    payload, _ = material(snapshot)
    assert 'authoring_constraints' not in payload['control']


def test_new_account_can_share_a_field_with_an_existing_complete_person_action():
    other = '僕は先生に時刻を伝えました。'
    snapshot = saved(CASES[0][1] + other)
    after = CASES[0][2] + '僕は先生に時刻を伝えた。'
    out = evaluate(snapshot, [after])
    assert out.artifact and out.artifact.body_blocks == (after,)
    payload, _ = material(snapshot)
    actions = action_hints(payload)['memo_0']['required_actions']
    assert len(actions) == 2 and 'source_scope' in actions[0]
    assert 'source_scope' not in actions[1]


@pytest.mark.parametrize('name', ('あいさん', '田中さん', 'Aliceさん'))
def test_named_premise_cannot_bypass_existing_public_role_abstraction(name):
    prefix = '友人の' + name + 'が戻ったので、'
    text = prefix + '僕は友人に予定を相談しました。'
    snapshot = saved(text, mode='平穏')
    assert _scoped_finite_self_person_action(text) is None
    meaning, _ = piece_model_source_plan(request(snapshot))
    assert meaning.role_bindings and not meaning.expression_scopes
    payload, _ = material(snapshot)
    assert not all_actions(payload)
    assert action_hints(payload)['memo_0']['named_people'][0]['public_role'] == '友人'
    # Existing name abstraction remains available with its unchanged finite
    # surface, but neither raw-name retention nor a new register exception is.
    public = text.replace('友人の' + name, '友人')
    assert evaluate(snapshot, [public]).artifact
    for changed in (text, text.replace('相談しました', '相談した'),
                    public.replace('相談しました', '相談した')):
        assert evaluate(snapshot, [changed]).artifact is None


@pytest.mark.parametrize('part', ('scope', 'expression'))
def test_forged_scoped_action_ranges_cannot_rebind_source_meaning(part):
    meaning, _ = piece_model_source_plan(request(saved(CASES[0][1])))
    scope = meaning.expression_scopes[0]
    key = 'scope_scalar_span' if part == 'scope' else 'expression_scalar_span'
    a, b = getattr(scope, key)
    changed = replace(meaning, expression_scopes=(replace(scope, **{key: (a + 1, b)}),))
    with pytest.raises(PieceContractError):
        validate_piece_expression_scopes(changed)


@pytest.mark.parametrize('body', [
    CASES[0][1], CASES[0][2],
    '僕は予定が重なっているので、友人に予定を相談しました。',
])
def test_forged_scoped_duty_cannot_enter_generic_scoped_author_comparison(body):
    meaning, plan = piece_model_source_plan(request(saved(CASES[0][1])))
    forged = replace(plan, duties=(replace(plan.duties[0],
        operation='SOURCE_SCOPED_EXPRESSION_TO_FIRST_PERSON'),))
    artifact = PieceArtifact((body,), body, hashlib.sha256(body.encode()).hexdigest(),
                             'short_essay', ('short_essay',))
    for model_register in (False, True):
        with pytest.raises(PieceContractError):
            validate_source_meaning_preservation(meaning, forged, artifact,
                                               _model_register=model_register)
    with pytest.raises(PieceContractError):
        validate_piece_model_preservation(meaning, forged, artifact)


def test_new_constraints_leave_the_baseline_system_and_default_transport_unchanged():
    assert hashlib.sha256(SYSTEM_MESSAGE.encode()).hexdigest() == BASELINE_SYSTEM_SHA256
    snapshot = saved(CASES[0][1])
    ordinary, prepared = material(snapshot, opt_in=False)
    explicit, _ = material(snapshot)
    assert 'authoring_constraints' not in ordinary['control']
    assert ordinary['sources'] == explicit['sources']
    assert ordinary['control']['field_slots'] == explicit['control']['field_slots']
    assert prepared.payload()['sources'] == ordinary['sources']
    assert not {'expected_body', 'assistant_target', 'target_field_blocks', 'body_blocks'} & set(
        explicit['control']['authoring_constraints'])
