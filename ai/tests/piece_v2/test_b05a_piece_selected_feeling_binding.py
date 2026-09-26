"""Selected feeling meaning in original-only Piece; no live auth/DB/UI claim.

Every admitted selection must already be expressed in a retained whole source
proposition. The SQL case uses the real existing Emlis writer and stored state,
not a caller's invented terminal flag. No existing test expectation is edited.
"""
import asyncio
import copy
from dataclasses import replace
import importlib.util
import json
import os
from pathlib import Path
from uuid import uuid4

import pytest
import api_account_visibility
import emlis_thread_store
from emlis_thread_service import EmlisThreadService
from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.piece_v1c import (
    PieceGenerationRequest, compile_piece_artifact_plan, realize_piece_artifact,
)
from piece_v2_contract import canonical_json_bytes
from piece_v2_generation import PieceSourceSnapshot
from piece_v2_source_adapter import PieceSavedSourceAdapter
from piece_v2_visual import build_visual_recipe

OWNER = '40000000-0000-4000-8000-000000000001'
INPUT = '50000000-0000-4000-8000-000000000001'
INTENT = '私は読書を大切にしたい。'
INTENT_BODY = '私は、読書を大切にしたい。'


def record(feeling='私は強い不安を感じています。', *, label='不安', strength='strong', field='memo'):
    return {'id': INPUT, 'created_at': '2026-09-26T00:00:00',
            'memo': feeling if field == 'memo' else INTENT,
            'memo_action': INTENT if field == 'memo' else feeling,
            'category': ['生活'], 'emotions': [label],
            'emotion_details': [{'type': label, 'strength': strength}]}


def outcome(row):
    text = '\n\n'.join(row[k] for k in ('memo', 'memo_action') if row[k] and row[k].strip())
    source = PieceSourceSnapshot(OWNER, INPUT, 'emlis.current_input_bundle.v1', text,
                                 saved_original_json=canonical_json_bytes(row))
    return MeaningExperienceEngine().generate(PieceGenerationRequest(
        'selected-feeling-original', source, OWNER, INPUT, source.source_version))


def generated(row):
    result = outcome(row)
    assert result.status == EngineStatus.GENERATED, result.reason_codes
    print('SELECTED_FEELING_BODY', json.dumps({'original': row,
        'candidate': result.artifact.as_candidate()}, ensure_ascii=False))
    return result


@pytest.mark.parametrize('label', ['喜び', '悲しみ', '怒り', '不安', '平穏'])
@pytest.mark.parametrize('strength,degree', [('weak', '弱い'), ('medium', '中程度の'), ('strong', '強い')])
def test_selected_meaning_is_bound_to_existing_explicit_words_not_added_prose(label, strength, degree):
    feeling = '私は' + degree + label + 'を感じています。'
    row = record(feeling, label=label, strength=strength)
    result = generated(row)
    assert result.artifact.piece_text == feeling + '\n\n' + INTENT_BODY
    meaning = result.source_meaning
    assert meaning.saved_snapshot.saved_original_json == canonical_json_bytes(row)
    assert [(x.selection_field, x.selection_index, x.label, x.strength)
            for x in meaning.selected_feelings] == [('emotions', 0, label, ''),
                                                    ('emotion_details', 0, label, strength)]
    assert {x.node_id for x in meaning.selected_feelings} == {'piece:s1'}
    assert {x.evidence_id for x in meaning.selected_feelings} == {'piece:e1'}
    assert meaning.graph.nodes[0].value == feeling
    assert result.artifact.as_candidate()['record_effect'] == result.artifact.as_candidate()['quota_effect'] == 0


@pytest.mark.parametrize('speaker', ['私', 'わたし', '僕', 'ぼく', '俺', 'おれ'])
@pytest.mark.parametrize('field', ['memo', 'memo_action'])
def test_real_field_and_written_speaker_are_preserved(speaker, field):
    feeling = speaker + 'は、強い不安を感じています。'
    row = record(feeling, field=field)
    result = generated(row)
    wanted = [feeling, INTENT_BODY] if field == 'memo' else [INTENT_BODY, feeling]
    assert result.artifact.piece_text == '\n\n'.join(wanted)
    bindings = result.source_meaning.selected_feelings
    ev = next(e for e in result.source_meaning.evidence if e.evidence_id == bindings[0].evidence_id)
    assert ev.field_path == field
    assert row[field][ev.scalar_start:ev.scalar_end] == feeling


@pytest.mark.parametrize('strength', ['strong', '強', 'high', 'STRONG'])
def test_existing_strength_alias_does_not_change_raw_record_or_source_words(strength):
    row = record(strength=strength)
    result = generated(row)
    assert result.source_meaning.saved_snapshot.saved_original_json == canonical_json_bytes(row)
    assert result.source_meaning.selected_feelings[-1].strength == 'strong'


@pytest.mark.parametrize('mode', ['tags_only', 'details_only', 'no_strength', 'empty_strength'])
def test_unspecified_strength_is_not_inferred_from_a_label(mode):
    row = record('私は不安を感じています。', strength='')
    if mode == 'tags_only': row['emotion_details'] = []
    elif mode == 'details_only': row['emotions'] = []
    elif mode == 'no_strength': del row['emotion_details'][0]['strength']
    result = generated(row)
    assert result.artifact.piece_text == '私は不安を感じています。\n\n' + INTENT_BODY
    assert all(x.strength == '' for x in result.source_meaning.selected_feelings)


@pytest.mark.parametrize('change', [
    'missing', 'negative', 'past', 'uncertain', 'conditional', 'other_person', 'report',
    'degree_mismatch', 'degree_missing', 'two_matches', 'duplicate_tag', 'duplicate_detail',
    'other_tag', 'unknown_label', 'unknown_strength', 'self_understanding', 'extra_detail_key',
    'nonstring_strength', 'two_different_degrees', 'field_fragment',
])
def test_unrepresented_ambiguous_or_nonasserted_feeling_is_not_silently_discarded(change):
    row = record()
    text_changes = {
        'missing': INTENT, 'negative': '私は強い不安を感じていません。',
        'past': '私は強い不安を感じていました。',
        'uncertain': '私は強い不安を感じているかもしれません。',
        'conditional': '私は強い不安を感じているなら、休みたい。',
        'other_person': '友人は強い不安を感じています。',
        'report': '私は強い不安を感じています、と友人が言った。',
        'degree_mismatch': '私は弱い不安を感じています。',
        'degree_missing': '私は不安を感じています。',
        'two_matches': '私は強い不安を感じています。私は強い不安を感じています。',
        'two_different_degrees': '私は強い不安を感じています。私は弱い不安を感じています。',
        'field_fragment': '私は強い不安を',
    }
    if change in text_changes: row['memo'] = text_changes[change]
    elif change == 'duplicate_tag': row['emotions'].append('不安')
    elif change == 'duplicate_detail': row['emotion_details'].append(copy.deepcopy(row['emotion_details'][0]))
    elif change == 'other_tag': row['emotions'] = ['怒り']
    elif change == 'unknown_label': row['emotions'] = ['謎']; row['emotion_details'][0]['type'] = '謎'
    elif change == 'unknown_strength': row['emotion_details'][0]['strength'] = 'very-high'
    elif change == 'self_understanding': row['emotions'] = ['自己理解']; row['emotion_details'][0]['type'] = '自己理解'
    elif change == 'extra_detail_key': row['emotion_details'][0]['cause'] = '読書'
    elif change == 'nonstring_strength': row['emotion_details'][0]['strength'] = 3
    result = outcome(row)
    assert result.status == EngineStatus.UNAVAILABLE and result.artifact is None


def test_multiple_feelings_remain_separate_without_inventing_a_relation():
    row = record('私は強い不安を感じています。私は弱い喜びを感じています。')
    row['emotions'].append('喜び'); row['emotion_details'].append({'type': '喜び', 'strength': 'weak'})
    result = generated(row)
    assert result.artifact.piece_text == row['memo'] + '\n\n' + INTENT_BODY
    assert [x.node_id for x in result.source_meaning.selected_feelings] == ['piece:s1', 'piece:s2', 'piece:s1', 'piece:s2']
    assert all(e.relation == 'SOURCE_ORDER' for e in result.source_meaning.graph.edges)


@pytest.mark.parametrize('change', ['field', 'index', 'label', 'strength', 'node', 'evidence', 'remove'])
def test_selected_binding_cannot_be_forged_between_meaning_and_realization(change):
    result = generated(record())
    meaning = result.source_meaning
    binding = meaning.selected_feelings[-1]
    changes = {'field': {'selection_field': 'memo'}, 'index': {'selection_index': 99},
        'label': {'label': '喜び'}, 'strength': {'strength': 'weak'},
        'node': {'node_id': 'piece:s2'}, 'evidence': {'evidence_id': 'piece:e2'}}
    bindings = () if change == 'remove' else meaning.selected_feelings[:-1] + (replace(binding, **changes[change]),)
    changed = replace(meaning, selected_feelings=bindings)
    with pytest.raises(ValueError, match='piece_saved_field_binding'):
        compile_piece_artifact_plan(changed)
    with pytest.raises(ValueError, match='piece_saved_field_binding'):
        realize_piece_artifact(changed, result.artifact_plan, tier="free", requested_format=None)


def test_feelings_without_an_explicit_expression_do_not_manufacture_a_will():
    row = record(); row['memo_action'] = ''
    result = outcome(row)
    assert result.status == EngineStatus.UNAVAILABLE and result.artifact is None


@pytest.fixture(scope='module')
def database():
    assert os.environ.get('Q2_PGLITE_MODULE'), 'retained SQL runtime required'
    path = Path(__file__).parents[1] / 'test_emlis_q2_application.py'
    spec = importlib.util.spec_from_file_location('piece_selected_sql_fixture', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    db = module.Database()
    yield db
    db.proc.stdin.close(); db.proc.wait(timeout=10)


@pytest.mark.parametrize('edit_during_generation', [False, True])
def test_actual_sql_saved_emlis_state_reaches_piece_body_and_rechecks_source(database, monkeypatch, edit_during_generation):
    db = database; user, parent = str(uuid4()), str(uuid4()); run = asyncio.run
    memo = '私は強い不安を感じています。' + INTENT
    for sql, params in [
        ('insert into auth.users values ($1)', [user]),
        ("insert into public.profiles values ($1,'free')", [user]),
        ("insert into public.emotions values ($1,$2,now() at time zone 'UTC',$3,'',array['生活'],array['不安'],$4)",
         [parent, user, memo, json.dumps([{'type': '不安', 'strength': 'strong'}])]),
    ]:
        assert 'code' not in db.query(sql, params)
    async def verify(token):
        assert token == 'synthetic-owner'
        return user
    monkeypatch.setattr(api_account_visibility, '_resolve_user_id_from_token', verify)
    monkeypatch.setattr(emlis_thread_store, 'sb_post_rpc', db.rpc)
    service = EmlisThreadService()
    initial = run(service.start(user, parent))
    assert initial['state'] == 'COMPLETED' and initial['current_observation'] is not None
    assert initial['pending_question'] is None
    before = run(service.store.read(user, input_id=parent))
    adapter = PieceSavedSourceAdapter()
    expected = '私は強い不安を感じています。' + INTENT_BODY
    generate = MeaningExperienceEngine.generate
    seen = []
    def piece_only(self, request):
        assert isinstance(request, PieceGenerationRequest), 'Piece must not rerun Emlis'
        out = generate(self, request); seen.append(out)
        if out.status == EngineStatus.GENERATED and edit_during_generation:
            assert 'code' not in db.query("update public.emotions set emotion_details=$1 where id=$2",
                [json.dumps([{'type': '不安', 'strength': 'weak'}]), parent])
        return out
    monkeypatch.setattr(MeaningExperienceEngine, 'generate', piece_only)
    if edit_during_generation:
        with pytest.raises(ValueError, match='PIECE_SOURCE_NOT_ELIGIBLE|PIECE_CONFLICT'):
            run(adapter.generate_original_candidate_from_saved_state('Bearer synthetic-owner', parent))
        assert len(seen) == 1 and seen[0].artifact.piece_text == expected
    else:
        result = run(adapter.generate_original_candidate_from_saved_state('Bearer synthetic-owner', parent))
        assert len(seen) == 1 and result['candidate']['piece_text'] == expected
        assert result['source_lineage']['observation']['emlis_observation_result_identity'] == initial['current_observation']['event_id']
        assert result['source_lineage']['observation']['emlis_observation_stage'] == 'normal_observation'
        assert result['source_lineage']['semantic_source_roles'] == ['original_input']
        assert '補助原則' not in result['candidate']['piece_text']
        recipe = build_visual_recipe('short_essay', tier='free')
        assert recipe['visual_recipe_version'] == 'piece.visual_recipe.v1'
        print('SELECTED_SQL_BODY', json.dumps({'original': before['original'],
            'candidate': result['candidate'], 'source_lineage': result['source_lineage'],
            'visual_recipe': recipe}, ensure_ascii=False))
    after = run(service.store.read(user, input_id=parent))
    assert before['thread'] == after['thread'] and before['events'] == after['events']
