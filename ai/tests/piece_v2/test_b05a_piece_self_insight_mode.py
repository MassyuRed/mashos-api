"""Exclusive saved self-insight mode, not a synthetic feeling proposition.

The unit cases exercise the selected-field boundary with immutable JSON and
synthetic node/evidence records. The integration cases use the real CMEE entry
and source validator; they must not be reported as run by a unit-only harness.
No existing tests, runtime switches, public routes or databases are modified.
"""
import copy
from dataclasses import replace
import json
from types import SimpleNamespace

import pytest

from cocolon_meaning_experience_engine.piece_source import _selected_feeling_bindings
from piece_v2_contract import PieceContractError, canonical_json_bytes

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


@pytest.mark.parametrize('variant', VARIANTS)
def test_unit_mode_is_retained_without_a_feeling_or_text_invention(variant):
    row = selection_variant(record(), variant)
    before = copy.deepcopy(row)
    raw = canonical_json_bytes(row)
    source = SimpleNamespace(saved_original_json=raw)
    # A selection is not a license to synthesize a node/evidence or an emotion.
    assert _selected_feeling_bindings(source, (), ()) == ()
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
    result = _selected_feeling_bindings(source, (node,), (ev,))
    assert [(b.selection_field, b.label, b.strength, b.node_id, b.evidence_id)
            for b in result] == [('emotions', label, '', 'n1', 'e1'),
                                ('emotion_details', label, strength, 'n1', 'e1')]


@pytest.mark.parametrize('strength', ['strong', '強', 'high', 'STRONG'])
def test_unit_existing_feeling_strength_aliases_are_unchanged(strength):
    row, node, ev = feeling_record(strength=strength)
    source = SimpleNamespace(saved_original_json=canonical_json_bytes(row))
    assert _selected_feeling_bindings(source, (node,), (ev,))[-1].strength == 'strong'


@pytest.mark.parametrize('mutation', ['missing_text', 'mismatched_strength', 'mixed_mode', 'wrong_evidence'])
def test_unit_ordinary_feeling_is_not_silently_dropped(mutation):
    row, node, ev = feeling_record()
    if mutation == 'missing_text': nodes = ()
    else: nodes = (node,)
    if mutation == 'mismatched_strength': row['emotion_details'][0]['strength'] = 'weak'
    if mutation == 'mixed_mode': row['emotion_details'].append({'type': MODE, 'strength': 'medium'})
    if mutation == 'wrong_evidence': ev.field_path = 'category'
    source = SimpleNamespace(saved_original_json=canonical_json_bytes(row))
    with pytest.raises(PieceContractError) as exc:
        _selected_feeling_bindings(source, nodes, (ev,))
    assert exc.value.detail == 'saved_emotion_meaning_not_yet_supported'


def test_unit_non_saved_source_is_unchanged():
    assert _selected_feeling_bindings(SimpleNamespace(saved_original_json=None), (), ()) == ()


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
