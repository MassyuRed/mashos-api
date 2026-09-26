"""Saved original -> actual CMEE/B9 candidate; no live auth, RPC or UI claim.

The source stage is explicitly supplied by this offline test caller. This does
not issue terminal eligibility or test a production preview endpoint.
"""
import asyncio
import copy
from dataclasses import replace
import hashlib
import json

from fastapi import HTTPException
import pytest

import api_account_visibility
import piece_v2_source_adapter as adapter_module
from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.piece_source import build_piece_source_meaning
from cocolon_meaning_experience_engine.piece_v1c import (
    PieceGenerationRequest, compile_piece_artifact_plan, realize_piece_artifact,
)
from piece_v2_contract import canonical_json_bytes, canonical_sha256_hex
from piece_v2_layout import TextMeasurement, build_measured_layout
from piece_v2_visual import build_visual_recipe

OWNER = '40000000-0000-4000-8000-000000000001'
INPUT = '50000000-0000-4000-8000-000000000001'
AUTH = 'Bearer synthetic-owner-session'
THOUGHT = '余裕があるなら、私が選びたいのは、陶芸です。'
ACTION = 'まだ、始める日は決めていません。'


def run(value):
    return asyncio.run(value)


def api():
    if not hasattr(adapter_module, 'project_saved_original_source'):
        pytest.fail('saved-original field projection is not implemented', pytrace=False)
    return adapter_module


def row(memo=THOUGHT, action=ACTION):
    return {'original': {'id': INPUT, 'created_at': '2026-09-26T00:00:00',
            'memo': memo, 'memo_action': action, 'category': ['生活'],
            'emotions': [], 'emotion_details': []}, 'tier': 'free',
            'now': '2026-09-26T01:00:00+00:00', 'thread': None, 'events': []}


class Store:
    def __init__(self, value):
        self.value, self.calls = value, []

    async def read(self, user_id, *, input_id=None):
        self.calls.append((user_id, input_id))
        return copy.deepcopy(self.value)

    async def commit(self, *args, **kwargs):
        pytest.fail('candidate generation must not write')


@pytest.fixture(autouse=True)
def auth(monkeypatch):
    async def verify(token):
        if token != 'synthetic-owner-session':
            raise HTTPException(401, 'private diagnostic')
        return OWNER
    monkeypatch.setattr(api_account_visibility, '_resolve_user_id_from_token', verify)


def source(value=None, stage='normal_observation'):
    api()
    saved = run(adapter_module.PieceSavedSourceAdapter(store=Store(value or row()))
                .resolve_original(AUTH, INPUT))
    return adapter_module.project_saved_original_source(saved, source_stage=stage)


def outcome(snapshot):
    return MeaningExperienceEngine().generate(PieceGenerationRequest(
        'synthetic-saved-original', snapshot, OWNER, INPUT, snapshot.source_version))


def generated(value=None):
    result = outcome(source(value))
    assert result.status == EngineStatus.GENERATED, result.reason_codes
    return result


def test_two_saved_fields_reach_the_existing_engine_without_becoming_one_field():
    result = generated()
    assert result.artifact.piece_text == '余裕があるなら、私は陶芸を選びたい。\n\n' + ACTION
    assert [e.field_path for e in result.source_meaning.evidence] == ['memo', 'memo_action']
    assert result.source_meaning.saved_snapshot.saved_original_json == canonical_json_bytes(row()['original'])
    assert result.artifact.as_candidate()['production_enabled'] is False
    assert result.artifact.as_candidate()['record_effect'] == result.artifact.as_candidate()['quota_effect'] == 0


@pytest.mark.parametrize('memo,action', [
    ('🌱を眺めた。\r\n私は読書を大切にしています。', '今朝は一冊を開いた。'),
    ('私は、陶芸を選びたい。', '私は、その時間を望んでいない。'),
    ('以前は、私が望んでいなかったのは、競争です。', '今も同じ気持ちかは、まだ分かりません。'),
    ('  私は読書を大切にしています。  ', '\tまだ、続ける日は決めていません。 '),
])
def test_field_relative_scalar_and_absolute_utf8_offsets_are_exact(memo, action):
    s = source(row(memo, action))
    # The unresolved-reference example must not become generated, but its
    # failure cannot be a cross-field sentence splice or dropped action.
    result = outcome(s)
    if 'その時間' in action:
        assert result.status == EngineStatus.UNAVAILABLE
        return
    assert result.status == EngineStatus.GENERATED, result.reason_codes
    meaning = result.source_meaning
    for ev, node in zip(meaning.evidence, meaning.graph.nodes, strict=True):
        field = row(memo, action)['original'][ev.field_path]
        assert field[ev.scalar_start:ev.scalar_end] == node.value
        assert meaning.envelope.raw_utf8[ev.utf8_start:ev.utf8_end].decode() == node.value
        assert meaning.envelope.raw_utf8[ev.field_utf8_start:ev.field_utf8_end].decode() == field
        assert ev.field_sha256 == hashlib.sha256(field.encode()).hexdigest()
    assert json.loads(meaning.saved_snapshot.saved_original_json) == row(memo, action)['original']


@pytest.mark.parametrize('empty', [None, '', ' \t\r\n'])
@pytest.mark.parametrize('field', ['memo', 'memo_action'])
def test_one_nonempty_written_field_uses_its_actual_field_identity(empty, field):
    value = row('私は読書を大切にしています。まだ、続ける日は決めていません。', None)
    value['original'][field] = value['original']['memo']
    value['original']['memo_action' if field == 'memo' else 'memo'] = empty
    result = generated(value)
    assert {ev.field_path for ev in result.source_meaning.evidence} == {field}
    assert result.artifact.piece_text == '私は、読書を大切にしています。まだ、続ける日は決めていません。'


@pytest.mark.parametrize('memo,action', [
    ('私は読書を大切に', 'しています。まだ、続ける日は決めていません。'),
    (THOUGHT, 'まだ、始める日は'),
    (None, None),
    (THOUGHT, '「続けます」と友人が言った。'),
])
def test_incomplete_or_unadmitted_action_is_not_removed_or_completed(memo, action):
    result = outcome(source(row(memo, action)))
    assert result.status == EngineStatus.UNAVAILABLE and result.artifact is None


@pytest.mark.parametrize('field,value', [
    ('emotions', ['平穏']),
    ('emotion_details', [{'type': '平穏', 'strength': 'medium'}]),
    ('emotions', ['平穏', '不安']),
])
def test_selected_feelings_are_not_silently_discarded_to_generate_text(field, value):
    record = row()
    record['original'][field] = value
    result = outcome(source(record))
    assert result.status == EngineStatus.UNAVAILABLE
    assert result.reason_codes == ('saved_emotion_meaning_not_yet_supported',)
    assert result.artifact is None


def test_same_literal_in_both_fields_keeps_both_propositions():
    text = '私は読書を大切にしています。'
    result = generated(row(text, text))
    assert result.artifact.piece_text == '私は、読書を大切にしています。\n\n私は、読書を大切にしています。'
    assert [e.scalar_start for e in result.source_meaning.evidence] == [0, 0]
    assert len(result.source_meaning.graph.nodes) == 2


def test_action_intent_is_not_fronted_across_the_thought_field():
    result = generated(row('今朝は窓を開けた。まだ、続ける日は決めていません。',
                           '私は読書を大切にしたい。'))
    assert result.artifact.piece_text == ('今朝は窓を開けた。まだ、続ける日は決めていません。'
                                          '\n\n私は、読書を大切にしたい。')


@pytest.mark.parametrize('which', ['field_path', 'field_digest', 'field_range', 'field_scalar', 'record', 'missing_record'])
def test_a_changed_field_or_record_binding_cannot_be_realized(which):
    result = generated()
    meaning, plan = result.source_meaning, result.artifact_plan
    first = meaning.evidence[0]
    if which == 'field_path':
        first = replace(first, field_path='memo_action')
    elif which == 'field_digest':
        first = replace(first, field_sha256='0' * 64)
    elif which == 'field_range':
        first = replace(first, field_utf8_end=first.field_utf8_end - 1)
    elif which == 'field_scalar':
        first = replace(first, scalar_start=1)
    elif which == 'record':
        altered = row()['original']; altered['category'] = ['仕事']
        meaning = replace(meaning, saved_snapshot=replace(meaning.saved_snapshot,
                          saved_original_json=canonical_json_bytes(altered)))
    else:
        meaning = replace(meaning, saved_snapshot=None)
    if which.startswith('field_'):
        meaning = replace(meaning, evidence=(first, *meaning.evidence[1:]))
    with pytest.raises(ValueError):
        realize_piece_artifact(meaning, plan, tier='free', requested_format=None)


def test_projected_text_cannot_drop_the_action():
    snapshot = source()
    result = outcome(replace(snapshot, original_text=THOUGHT))
    assert result.status == EngineStatus.UNAVAILABLE and result.artifact is None


def test_structured_metadata_changes_source_identity_without_becoming_prose():
    a = generated()
    changed = row(); changed['original']['category'] = ['仕事']
    b = generated(changed)
    assert a.source_meaning.envelope.envelope_id != b.source_meaning.envelope.envelope_id
    assert a.source_meaning.graph.graph_id != b.source_meaning.graph.graph_id
    assert a.artifact.piece_text == b.artifact.piece_text
    assert '仕事' not in b.artifact.piece_text
    assert 'original' not in json.dumps(b.as_body_free())


@pytest.mark.parametrize('stage', ['normal_observation', 'pre_question_observation'])
def test_explicit_offline_stage_is_bound_not_issued_as_terminal_eligibility(stage):
    s = source(stage=stage)
    assert s.source_stage == stage
    assert outcome(s).status == EngineStatus.GENERATED
    assert not hasattr(s, 'piece_generation_eligibility')


@pytest.mark.parametrize('stage', ['refined_observation', '', None])
def test_unproved_or_refined_stage_has_no_original_only_success(stage):
    api()
    with pytest.raises(ValueError):
        source(stage=stage)


def test_authenticated_candidate_uses_real_engine_then_revalidates(monkeypatch):
    api()
    store = Store(row())
    result = run(adapter_module.PieceSavedSourceAdapter(store=store)
                 .generate_original_candidate_for_development(AUTH, INPUT,
                    source_stage='normal_observation'))
    assert result['piece_text'] == '余裕があるなら、私は陶芸を選びたい。\n\n' + ACTION
    assert store.calls == [(OWNER, INPUT), (OWNER, INPUT)]
    assert result['production_enabled'] is False


@pytest.mark.parametrize('mutation', ['memo_action', 'category', 'tier', 'deleted'])
def test_source_changed_during_generation_is_not_returned(monkeypatch, mutation):
    api()
    store = Store(row())
    import piece_v2_generation
    original = piece_v2_generation.generate_piece_candidate
    def generate(*args, **kwargs):
        result = original(*args, **kwargs)
        if mutation == 'deleted':
            store.value = None
        elif mutation == 'tier':
            store.value['tier'] = 'plus'
        else:
            store.value['original'][mutation] = '違う行動。' if mutation == 'memo_action' else ['仕事']
        return result
    monkeypatch.setattr(piece_v2_generation, 'generate_piece_candidate', generate)
    with pytest.raises(ValueError):
        run(adapter_module.PieceSavedSourceAdapter(store=store)
            .generate_original_candidate_for_development(AUTH, INPUT,
                 source_stage='normal_observation'))


@pytest.mark.parametrize('ratio', ['4:5', '9:16'])
def test_both_complete_body_blocks_reach_existing_b9(ratio):
    candidate = generated().artifact.as_candidate()
    class Metrics:
        profile_id = 'synthetic-saved-fields-not-native'
        def graphemes(self, text): return list(text)
        def measure(self, text, size):
            width = len(text) * size
            return TextMeasurement(width, 0, -.8 * size, width, .2 * size)
    recipe = build_visual_recipe('short_essay', tier='premium', aspect_ratio=ratio)
    layout = build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    reconstructed = [''.join(row['text'] for row in layout['lines'] if row['block_index'] == index)
                     for index in range(2)]
    assert reconstructed == candidate['content_payload']['body_blocks']
    assert layout['piece_text_hash'] == candidate['piece_text_hash']
    assert layout['native_device_verified'] is False


@pytest.mark.parametrize('memo,action', [
    (THOUGHT, ACTION),
    ('以前は、私が望んでいなかったのは、競争です。', '今も同じ気持ちかは、まだ分かりません。'),
    ('私は読書を大切にしています。', '今日は一冊を開いた。毎日続けるかは、まだ決めていません。'),
    (None, '私は読書を大切にしています。まだ、毎日続けるかは決めていません。'),
])
def test_existing_sql_saved_read_reaches_actual_cmee_and_revalidation(monkeypatch, memo, action):
    api()
    import importlib.util
    import os
    from pathlib import Path
    import emlis_thread_store
    assert os.environ.get('Q2_PGLITE_MODULE'), 'retained SQL runtime required'
    path = Path(__file__).parents[1] / 'test_emlis_q2_application.py'
    spec = importlib.util.spec_from_file_location('piece_saved_generation_sql_fixture', path)
    existing = importlib.util.module_from_spec(spec); spec.loader.exec_module(existing)
    db = existing.Database()
    try:
        assert 'code' not in db.query('insert into auth.users values ($1)', [OWNER])
        assert 'code' not in db.query("insert into public.profiles values ($1,'free')", [OWNER])
        assert 'code' not in db.query(
            "insert into public.emotions values ($1,$2,now() at time zone 'UTC',$3,$4,array['生活'],array[]::text[],'[]'::jsonb)",
            [INPUT, OWNER, memo, action])
        monkeypatch.setattr(emlis_thread_store, 'sb_post_rpc', db.rpc)
        candidate = run(adapter_module.PieceSavedSourceAdapter()
            .generate_original_candidate_for_development(AUTH, INPUT,
                 source_stage='normal_observation'))
        expected = generated(row(memo, action)).artifact.as_candidate()
        assert candidate == expected
        for table in ('emlis_input_threads', 'emlis_thread_events'):
            assert db.query(f'select count(*)::int as n from public.{table}')['rows'][0]['n'] == 0
        assert candidate['production_enabled'] is False
    finally:
        db.proc.stdin.close()
        db.proc.wait(timeout=10)
