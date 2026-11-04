"""Exclusive saved self-insight mode, not a synthetic feeling proposition.

The unit cases exercise the selected-field boundary with immutable JSON and
synthetic node/evidence records. The integration cases use the real CMEE entry
and source validator; they must not be reported as run by a unit-only harness.
No existing tests, runtime switches, public routes or databases are modified.
"""
import copy
from dataclasses import replace
import hashlib
import json
from types import SimpleNamespace

import pytest

from cocolon_meaning_experience_engine.piece_source import _selected_feeling_bindings
from piece_v2_contract import PieceContractError, canonical_json_bytes
from test_b05a_piece_saved_original_generation import auth, generated, outcome, row as saved_state, source

MODE = '自己理解'
THOUGHT = '私は読書を大切にしたい。'
RESERVATION = 'まだ、毎日続けるかは決めていません。'


def record():
    return {
        'id': '50000000-0000-4000-8000-000000000001',
        'created_at': '2026-09-26T00:00:00',
        'memo': THOUGHT, 'memo_action': RESERVATION, 'category': ['生活'],
        'emotions': [MODE],
        'emotion_details': [{'type': MODE, 'strength': 'medium'}],
    }


def selection_variant(row, variant):
    if variant == 'tags_only':
        row['emotion_details'] = []
    elif variant == 'tags_null_details':
        row['emotion_details'] = None
    elif variant == 'details_only':
        row['emotions'] = []
    elif variant == 'details_null_tags':
        row['emotions'] = None
    elif variant == 'missing_strength':
        row['emotion_details'][0].pop('strength')
    elif variant == 'empty_strength':
        row['emotion_details'][0]['strength'] = ''
    return row


VARIANTS = ['ui_medium', 'tags_only', 'tags_null_details', 'details_only',
            'details_null_tags', 'missing_strength', 'empty_strength']


@pytest.mark.parametrize('reservation', (
    'まだ、決めていません。', 'まだ，決めていない！',
    'まだ,決めていませんでした!', 'まだ、決めていなかった。',
))
@pytest.mark.parametrize('separate_fields', (False, True))
def test_literal_account_keeps_a_paused_finite_decision_reservation(reservation, separate_fields):
    from piece_v2_content_policy import validate_source_meaning_preservation
    account = '私は本を読みたい！'
    value = saved_state(account, reservation) if separate_fields else saved_state(account + reservation, None)
    value['original']['emotions'] = [MODE]
    result = outcome(source(value))
    assert result.status.value == 'GENERATED', result.reason_codes
    blocks = (account, reservation) if separate_fields else (account + reservation,)
    assert result.artifact.body_blocks == blocks
    assert result.artifact.piece_text == '\n\n'.join(blocks)
    assert result.artifact.piece_text_hash == hashlib.sha256(result.artifact.piece_text.encode()).hexdigest()
    assert result.artifact.eligible_formats == ('short_essay',)
    assert not result.artifact_plan.declaration_eligible
    assert all(d.operation == 'KEEP_COMPLETE_SOURCE_CONTEXT' for d in result.artifact_plan.duties)
    meaning = result.source_meaning
    assert meaning.saved_snapshot.saved_original_json == canonical_json_bytes(value['original'])
    assert meaning.selected_feelings == ()
    for node, evidence in zip(meaning.graph.nodes, meaning.evidence, strict=True):
        field = value['original'][evidence.field_path]
        assert field[evidence.scalar_start:evidence.scalar_end] == node.value
        assert meaning.envelope.raw_utf8[evidence.utf8_start:evidence.utf8_end] == node.value.encode()
    validate_source_meaning_preservation(meaning, result.artifact_plan, result.artifact)


@pytest.mark.parametrize('reservation', (
    'まだ、決めています。', 'まだ、決めました。', 'まだ、やめていません。',
    'まだ、何を決めていません。', 'まだ、どんな本を読むかは決めていません。',
    'まだ、余裕があるなら決めていません。', 'まだ、読む日は決めていませんと言われた。',
    'まだ、決めていません？', 'まだ、読む日は決めていません',
    'まだ、決めていないわけではありません。',
    'まだ、読む日は決めていません。', 'まだ，読む日は決めていない！',
    'まだ, 読む日は決めていませんでした!', 'まだ、\u3000読む日は決めていなかった。',
    'まだ、余裕があるので私は決めていません。',
    'まだ、遠いけれど私は決めていません。',
    'まだ、は決めていません。', 'まだ、 は決めていません。',
))
def test_paused_decision_does_not_supply_an_unknown_predicate_or_relax_scope_guards(reservation):
    value = saved_state('私は本を読みたい！' + reservation, None)
    value['original']['emotions'] = [MODE]
    result = outcome(source(value))
    assert result.status.value == 'UNAVAILABLE'
    assert result.artifact is None


@pytest.mark.parametrize('variant', VARIANTS)
def test_unit_mode_is_retained_without_a_feeling_or_text_invention(variant):
    row = selection_variant(record(), variant)
    before = copy.deepcopy(row)
    raw = canonical_json_bytes(row)
    source = SimpleNamespace(saved_original_json=raw)
    # A selection is not a license to synthesize a node/evidence or an emotion.
    assert _selected_feeling_bindings(source, (), ()) == ((), (), ())
    assert source.saved_original_json is raw
    assert json.loads(raw) == before == row
    assert row['memo'] == THOUGHT and row['memo_action'] == RESERVATION


@pytest.mark.parametrize('strength', [
    'weak', 'strong', '弱', '強', '中', 'mid', 'middle', 'normal',
    'MEDIUM', ' medium ', 'unknown', '0', 0, 2, False, None, [], {},
])
def test_unit_mode_does_not_reinterpret_an_unproved_strength(strength):
    row = record()
    row['emotion_details'][0]['strength'] = strength
    assert_unavailable(row)


def assert_unavailable(row):
    raw = canonical_json_bytes(row)
    source = SimpleNamespace(saved_original_json=raw)
    with pytest.raises(PieceContractError) as exc:
        _selected_feeling_bindings(source, (), ())
    assert exc.value.code == 'PIECE_CONTENT_UNAVAILABLE'
    assert exc.value.detail == 'saved_emotion_meaning_not_yet_supported'
    assert source.saved_original_json is raw


@pytest.mark.parametrize('variant', [
    'mixed_tags', 'mixed_details', 'tag_alias_mismatch', 'detail_alias_mismatch',
    'duplicate_tags', 'duplicate_details', 'extra_detail_key', 'empty_detail',
    'null_detail', 'string_detail', 'array_detail', 'unknown_mode_alias',
])
def test_unit_invalid_or_ambiguous_mode_stays_unavailable(variant):
    row = record()
    if variant == 'mixed_tags': row['emotions'].append('不安')
    elif variant == 'mixed_details': row['emotion_details'].append({'type': '不安'})
    elif variant == 'tag_alias_mismatch': row['emotions'] = ['不安']
    elif variant == 'detail_alias_mismatch': row['emotion_details'] = [{'type': '不安'}]
    elif variant == 'duplicate_tags': row['emotions'].append(MODE)
    elif variant == 'duplicate_details': row['emotion_details'].append(copy.deepcopy(row['emotion_details'][0]))
    elif variant == 'extra_detail_key': row['emotion_details'][0]['inferred'] = True
    elif variant == 'empty_detail': row['emotion_details'] = [{}]
    elif variant == 'null_detail': row['emotion_details'] = [None]
    elif variant == 'string_detail': row['emotion_details'] = [MODE]
    elif variant == 'array_detail': row['emotion_details'] = [[MODE]]
    elif variant == 'unknown_mode_alias':
        row['emotions'] = ['SelfInsight']
        row['emotion_details'] = [{'type': 'SelfInsight', 'strength': 'medium'}]
    assert_unavailable(row)


def feeling_record(label='不安', strength='strong', degree='強い'):
    row = record()
    row['memo'] = f'私は{degree}{label}を感じています。'
    row['emotions'] = [label]
    row['emotion_details'] = [{'type': label, 'strength': strength}]
    node = SimpleNamespace(node_id='n1', value=row['memo'], evidence_ids=('e1',))
    ev = SimpleNamespace(evidence_id='e1', field_path='memo',
                         scalar_start=0, scalar_end=len(row['memo']))
    return row, node, ev


@pytest.mark.parametrize('label', ['喜び', '悲しみ', '怒り', '不安', '平穏'])
@pytest.mark.parametrize('strength,degree', [('weak', '弱い'), ('medium', '中程度の'), ('strong', '強い')])
def test_unit_ordinary_feelings_keep_exact_existing_proposition_coverage(label, strength, degree):
    row, node, ev = feeling_record(label, strength, degree)
    source = SimpleNamespace(saved_original_json=canonical_json_bytes(row))
    result = _selected_feeling_bindings(source, (node,), (ev,))[0]
    assert [(b.selection_field, b.label, b.strength, b.node_id, b.evidence_id)
            for b in result] == [('emotions', label, '', 'n1', 'e1'),
                                ('emotion_details', label, strength, 'n1', 'e1')]


@pytest.mark.parametrize('strength', ['strong', '強', 'high', 'STRONG'])
def test_unit_existing_feeling_strength_aliases_are_unchanged(strength):
    row, node, ev = feeling_record(strength=strength)
    source = SimpleNamespace(saved_original_json=canonical_json_bytes(row))
    assert _selected_feeling_bindings(source, (node,), (ev,))[0][-1].strength == 'strong'


def test_unit_different_written_strength_keeps_separate_selection_evidence():
    row, node, ev = feeling_record()
    row['emotion_details'][0]['strength'] = 'weak'
    source = SimpleNamespace(saved_original_json=canonical_json_bytes(row))
    bindings, evidence, contexts = _selected_feeling_bindings(source, (node,), (ev,))
    context, = contexts
    assert {b.node_id for b in bindings} == {context.node_id}
    assert context.node_id != node.node_id
    assert tuple(e.evidence_id for e in evidence) == context.evidence_ids
    assert json.loads(context.value)['strength'] == 'weak'


@pytest.mark.parametrize('mutation', ['mixed_mode', 'wrong_evidence'])
def test_unit_invalid_feeling_evidence_is_rejected(mutation):
    row, node, ev = feeling_record()
    if mutation == 'mixed_mode': row['emotion_details'].append({'type': MODE, 'strength': 'medium'})
    if mutation == 'wrong_evidence': ev.field_path = 'category'
    source = SimpleNamespace(saved_original_json=canonical_json_bytes(row))
    with pytest.raises(PieceContractError) as exc:
        _selected_feeling_bindings(source, (node,), (ev,))
    assert exc.value.detail == 'saved_emotion_meaning_not_yet_supported'


def test_unit_non_saved_source_is_unchanged():
    assert _selected_feeling_bindings(SimpleNamespace(saved_original_json=None), (), ()) == ((), (), ())


@pytest.mark.parametrize('variant', VARIANTS)
def test_integration_mode_keeps_the_real_source_and_existing_canonical_body(variant):
    from cocolon_meaning_experience_engine.contracts import EngineStatus
    from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
    from cocolon_meaning_experience_engine.piece_source import validate_piece_saved_fields
    from cocolon_meaning_experience_engine.piece_v1c import PieceGenerationRequest
    from piece_v2_generation import PieceSourceSnapshot

    owner = '40000000-0000-4000-8000-000000000001'
    row = selection_variant(record(), variant)
    text = row['memo'] + '\n\n' + row['memo_action']
    source = PieceSourceSnapshot(owner, row['id'], 'emlis.current_input_bundle.v1',
                                 text, saved_original_json=canonical_json_bytes(row))
    engine = MeaningExperienceEngine()
    result = engine.generate(PieceGenerationRequest(
        'self-insight-original', source, owner, row['id'], source.source_version))
    assert result.status == EngineStatus.GENERATED, result.reason_codes
    meaning = result.source_meaning
    assert meaning.saved_snapshot.saved_original_json == source.saved_original_json
    assert meaning.selected_feelings == ()
    assert [node.value for node in meaning.graph.nodes] == [THOUGHT, RESERVATION]
    assert [ev.field_path for ev in meaning.evidence] == ['memo', 'memo_action']
    validate_piece_saved_fields(meaning)

    # A mode may change the immutable identity, never the authored body.
    without_mode = copy.deepcopy(row)
    without_mode['emotions'], without_mode['emotion_details'] = [], []
    other_source = replace(source, saved_original_json=canonical_json_bytes(without_mode))
    other = engine.generate(PieceGenerationRequest(
        'same-written-meaning', other_source, owner, row['id'], source.source_version))
    assert other.status == EngineStatus.GENERATED, other.reason_codes
    assert result.artifact.piece_text == other.artifact.piece_text
    assert meaning.envelope.envelope_id != other.source_meaning.envelope.envelope_id
    with pytest.raises(PieceContractError):
        validate_piece_saved_fields(replace(meaning, saved_snapshot=other_source))


@pytest.mark.parametrize('variant', VARIANTS)
def test_valid_saved_mode_allows_only_the_written_completed_actions(variant):
    from piece_v2_content_policy import validate_source_meaning_preservation

    row = selection_variant(record(), variant)
    row['memo'] = '昨日は予定を確認しました。'
    row['memo_action'] = '今朝は資料を整理しませんでした'
    result = generated({**saved_state(), 'original': row})
    assert result.artifact.piece_text == row['memo'] + '\n\n' + row['memo_action']
    assert result.source_meaning.saved_snapshot.saved_original_json == canonical_json_bytes(row)
    assert result.source_meaning.selected_feelings == ()
    assert result.source_meaning.selection_contexts == ()
    assert [node.value for node in result.source_meaning.graph.nodes] == [row['memo'], row['memo_action']]
    assert {d.operation for d in result.artifact_plan.duties} == {'KEEP_COMPLETE_SOURCE_CONTEXT'}
    assert 'declaration' not in result.artifact.eligible_formats
    validate_source_meaning_preservation(result.source_meaning, result.artifact_plan, result.artifact)


@pytest.mark.parametrize('variant', VARIANTS)
@pytest.mark.parametrize('memo,action', [
    ('昨日は資料を送りました。', '今朝は書類を読みました。'),
    ('昨日は資料を送りました。', '今朝は書類を読みました'),
    ('昨日は予定を確認しました。', '今朝は窓を開けました。'),
    ('昨日は窓を開けました。', '今朝は下書きを終えませんでした'),
    ('約束した資料を昨日は送りました。', '今日は片付けを始めませんでした'),
    ('今日は片付けを始めませんでした。', '約束した資料を昨日は送りました。'),
    ('玄関の鍵を閉めました。', '封筒を受け取りませんでした'),
    ('封筒を受け取りました。', '窓を閉めませんでした。'),
])
def test_saved_self_insight_lexical_action_preserves_each_written_stop(variant, memo, action):
    from hashlib import sha256
    from piece_v2_content_policy import validate_source_meaning_preservation

    row = selection_variant(record(), variant)
    row['memo'], row['memo_action'] = memo, action
    result = generated({**saved_state(), 'original': row})
    expected = (memo + '\n\n' + action).encode()
    assert result.artifact.piece_text.encode() == expected
    assert result.artifact.piece_text_hash == sha256(expected).hexdigest()
    assert result.artifact.body_blocks == (memo, action)
    assert result.source_meaning.saved_snapshot.saved_original_json == canonical_json_bytes(row)
    assert result.source_meaning.selected_feelings == result.source_meaning.selection_contexts == ()
    assert {d.operation for d in result.artifact_plan.duties} == {'KEEP_COMPLETE_SOURCE_CONTEXT'}
    assert 'declaration' not in result.artifact.eligible_formats
    validate_source_meaning_preservation(result.source_meaning, result.artifact_plan, result.artifact)


@pytest.mark.parametrize('selection,memo,action,reason', [
    ('none', '資料を確認しました。', None, 'expression_meaning_not_admitted'),
    ('mixed', '資料を確認しました。', None, 'saved_emotion_meaning_not_yet_supported'),
    ('wrong_strength', '資料を確認しました。', None, 'saved_emotion_meaning_not_yet_supported'),
    ('mode', '資料を確認しました。', '明日のこと。', 'expression_meaning_not_admitted'),
    ('mode', '資料を確認しましたか。', None, 'expression_meaning_not_admitted'),
    ('mode', 'どの資料を確認しました。', None, 'expression_meaning_not_admitted'),
    ('mode', '誰が資料を確認しました。', None, 'expression_meaning_not_admitted'),
    ('mode', '誰の資料を確認しました', None, 'source_line_mid_sentence'),
    ('mode', '資料を確認しましたが。', None, 'expression_meaning_not_admitted'),
    ('mode', 'もし資料を確認しました。', None, 'expression_meaning_not_admitted'),
    ('mode', 'もし資料を確認しました', None, 'source_line_mid_sentence'),
    ('mode', 'その資料を確認しました。', None, 'unresolved_reference'),
    ('mode', '資料を送りました', '書類を読みました。', 'source_line_mid_sentence'),
    ('mode', '資料を送りました。', 'どこで書類を読みました。', 'expression_meaning_not_admitted'),
    ('mode', '資料を送りました。', 'どこで書類を読みました', 'source_line_mid_sentence'),
    ('mode', '窓を開けました。', 'もし書類を読みました。', 'expression_meaning_not_admitted'),
    ('mode', '窓を開けました。', 'もし書類を読みました', 'source_line_mid_sentence'),
    ('mode', '資料を送りました。', '書類を駅ました。', 'expression_meaning_not_admitted'),
    ('mode', '資料を送りました。', '書類を駅ました', 'source_line_mid_sentence'),
    ('mode', '資料を送りました。', 'その書類を読みました。', 'unresolved_reference'),
    ('mixed', '資料を送りました。', '書類を読みました。', 'saved_emotion_meaning_not_yet_supported'),
    ('mode', '資料を昨日は送りました', '今日は片付けを始めませんでした。', 'source_line_mid_sentence'),
    ('mode', '資料を昨日は送りました。', '何の作業を今朝は始めました。', 'expression_meaning_not_admitted'),
    ('mode', '資料を昨日は送りました。', 'もし作業を今朝は始めました。', 'expression_meaning_not_admitted'),
    ('mode', '窓を閉めました。', '都合が合えば荷物を受け取りました。', 'expression_meaning_not_admitted'),
    ('mode', '契約書を受け取りました。', 'どの窓を閉めました。', 'expression_meaning_not_admitted'),
])
def test_completed_action_path_requires_verified_mode_and_complete_source(selection, memo, action, reason):
    row = record()
    row['memo'], row['memo_action'] = memo, action
    if selection == 'none':
        row['emotions'], row['emotion_details'] = [], []
    elif selection == 'mixed':
        row['emotions'].append('平穏')
    elif selection == 'wrong_strength':
        row['emotion_details'][0]['strength'] = 'strong'
    result = outcome(source({**saved_state(), 'original': row}))
    assert result.reason_codes == (reason,)
    assert result.artifact is None


def test_completed_action_mode_cannot_be_claimed_by_raw_source():
    row = record()
    row['memo'], row['memo_action'] = '資料を確認しました。', None
    snapshot = source({**saved_state(), 'original': row})
    result = outcome(replace(snapshot, saved_original_json=None))
    assert result.reason_codes == ('expression_meaning_not_admitted',)
    assert result.artifact is None
