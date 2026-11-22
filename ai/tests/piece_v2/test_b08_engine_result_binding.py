"""Actual CMEE results must stay bound to the B8 request before B5 consumes them.

All records and names are synthetic. Fault injection replaces only the engine's
returned outcome, after real generation. It does not replace the source builder,
plan compiler or author, and establishes no public safety or device acceptance.
"""
from dataclasses import replace
import hashlib
import json

import pytest

from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.piece_v1c import PieceGenerationRequest
from piece_v2_contract import (
    PieceContractError, canonical_json_bytes, canonical_sha256_hex,
    validate_piece_text_binding,
)
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
from piece_v2_visual import build_visual_recipe


_MEMO = '私は友人の佐藤さんの上司の田中さんと話したい。'
_ACTION = '田中さんとはまだ会っていない。'
_EXPECTED_MEMO = '私は、友人の上司と話したい。'
_EXPECTED_ACTION = '友人の上司とはまだ会っていない。'


def _source(*, saved=False):
    input_id = 'synthetic-result-binding-input'
    record = {
        'id': input_id, 'created_at': '2026-10-07T00:00:00Z',
        'memo': _MEMO, 'memo_action': _ACTION,
        'category': ['対人関係'], 'emotions': ['自己理解'],
        'emotion_details': [{'type': '自己理解', 'strength': 'medium'}],
    }
    return PieceSourceSnapshot(
        'synthetic-result-binding-owner', input_id,
        'emlis.current_input_bundle.v1' if saved else 'v1',
        _MEMO + ('\n\n' if saved else '') + _ACTION,
        saved_original_json=canonical_json_bytes(record) if saved else None,
    )


def _actual(source, *, tier='free'):
    result = MeaningExperienceEngine().generate(PieceGenerationRequest(
        'synthetic-result-binding-request', source, source.owner_id,
        source.saved_input_id, source.source_version, tier=tier,
    ))
    assert result.status == EngineStatus.GENERATED, result.as_body_free()
    assert result.artifact is not None
    return result


def _return_outcome(monkeypatch, result):
    monkeypatch.setattr(MeaningExperienceEngine, 'generate', lambda self, request: result)


def _unavailable(source, reason):
    with pytest.raises(PieceContractError) as error:
        generate_piece_candidate(source, authenticated_owner_id=source.owner_id)
    assert error.value.code == 'PIECE_CONTENT_UNAVAILABLE'
    assert error.value.detail == reason


@pytest.mark.parametrize('change', [
    {'owner_id': 'synthetic-other-owner'},
    {'saved_input_id': 'synthetic-other-input'},
    {'source_version': 'v2'},
    {'source_stage': 'pre_question_observation'},
    {'original_text': _MEMO.replace('佐藤さん', '鈴木さん') + _ACTION},
], ids=['owner', 'record', 'version', 'stage', 'same_public_body_other_name'])
def test_another_actual_source_result_is_not_returned_for_this_request(monkeypatch, change):
    source = _source()
    cached = _actual(replace(source, **change))
    # Several wrong sources have exactly the same visible text. Comparing just
    # that text, its hash, or a constant node ID cannot bind this request.
    assert cached.artifact.piece_text == _EXPECTED_MEMO + _EXPECTED_ACTION
    _return_outcome(monkeypatch, cached)
    _unavailable(source, 'piece_engine_source_binding')


@pytest.mark.parametrize('field,value', [
    ('created_at', '2026-10-06T00:00:00Z'),
    ('category', ['別の場面']),
])
def test_complete_saved_record_not_just_projected_text_is_bound(monkeypatch, field, value):
    source = _source(saved=True)
    record = json.loads(source.saved_original_json)
    record[field] = value
    cached = _actual(replace(source, saved_original_json=canonical_json_bytes(record)))
    assert cached.artifact.piece_text == _EXPECTED_MEMO + '\n\n' + _EXPECTED_ACTION
    _return_outcome(monkeypatch, cached)
    _unavailable(source, 'piece_engine_source_binding')


@pytest.mark.parametrize('mutation', [
    'omitted_qualification', 'negation_inverted', 'added_claim',
    'changed_relationship', 'identity_reintroduced',
])
def test_self_consistent_but_source_unfaithful_body_is_not_returned(monkeypatch, mutation):
    source = _source()
    actual = _actual(source)
    text = actual.artifact.piece_text
    if mutation == 'omitted_qualification':
        text = _EXPECTED_MEMO
    elif mutation == 'negation_inverted':
        text = text.replace('まだ会っていない', 'もう会った')
    elif mutation == 'added_claim':
        text += '私は新しい約束をした。'
    elif mutation == 'changed_relationship':
        text = text.replace('友人の上司', '同僚')
    else:
        text = text.replace('友人の上司', '田中さん')
    artifact = replace(actual.artifact, body_blocks=(text,), piece_text=text,
                       piece_text_hash=hashlib.sha256(text.encode('utf-8')).hexdigest())
    assert artifact.piece_text != actual.artifact.piece_text
    # This is not merely a bad hash or a broken payload. The changed body has
    # internally consistent content bytes, so it also needs source-plan binding.
    assert validate_piece_text_binding(artifact.content_payload(), text,
                                       artifact.piece_text_hash) == text
    _return_outcome(monkeypatch, replace(actual, artifact=artifact))
    _unavailable(source, 'piece_engine_artifact_binding')


@pytest.mark.parametrize('mutation', ['graph', 'source_version', 'missing_duty'])
def test_result_plan_must_be_the_plan_of_this_complete_source(monkeypatch, mutation):
    source = _source()
    actual = _actual(source)
    plan = actual.artifact_plan
    if mutation == 'graph':
        plan = replace(plan, graph_id='synthetic-other-graph')
    elif mutation == 'source_version':
        plan = replace(plan, source_version='v2')
    else:
        plan = replace(plan, duties=plan.duties[:-1])
    _return_outcome(monkeypatch, replace(actual, artifact_plan=plan))
    _unavailable(source, 'piece_engine_plan_binding')


@pytest.mark.parametrize('saved', [False, True], ids=['original_text', 'complete_saved_record'])
@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
def test_real_result_keeps_source_body_recipe_and_offline_boundary(saved, tier):
    source = _source(saved=saved)
    before = source.original_text, source.saved_original_json
    actual = _actual(source, tier=tier)
    candidate = generate_piece_candidate(source, authenticated_owner_id=source.owner_id, tier=tier)
    expected = _EXPECTED_MEMO + ('\n\n' if saved else '') + _EXPECTED_ACTION
    assert candidate['piece_text'] == expected
    assert candidate == actual.artifact.as_candidate()
    assert validate_piece_text_binding(candidate['content_payload'], expected,
                                       candidate['piece_text_hash']) == expected
    recipe = build_visual_recipe(candidate['format_type'], tier=tier, aspect_ratio='4:5')
    original_recipe = build_visual_recipe(actual.artifact.format_type, tier=tier, aspect_ratio='4:5')
    assert recipe == original_recipe
    assert canonical_sha256_hex(recipe) == canonical_sha256_hex(original_recipe)
    assert (source.original_text, source.saved_original_json) == before
    assert candidate['candidate_state'] == 'OFFLINE_NOT_ACCEPTED'
    assert candidate['production_enabled'] is False
    assert candidate['record_effect'] == candidate['quota_effect'] == 0
    assert 'content_status' not in candidate
