"""Input integrity across report material identities and emotion aggregation.

Synthetic rows and mocked transport only. These checks do not certify natural
language understanding, live DB contents, or device output.
"""
import asyncio
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

import pytest

import astor_material_snapshots as materials
import kokoro_weather_service as weather


CATEGORIES = ['生活', '仕事', '趣味', '人間関係', '恋愛', '健康', '学習', '価値観', '人生']
EMOTIONS = ['喜び', '悲しみ', '怒り', '不安', '平穏']
ROW = dict(id='00000000-0000-0000-0000-000000000101',
    created_at='2026-11-07T01:00:00Z', is_secret=False,
    memo='私は考えをノートに書いた。私は仕事を続けたい。',
    memo_action='私は資料を確認しなかった。', category=CATEGORIES,
    emotions=EMOTIONS, emotion_details=[dict(type=kind, strength='weak') for kind in EMOTIONS],
    emotion_strength_avg=1.0)


def identities(rows, snapshot_type='internal'):
    return (
        materials.compute_source_hash_from_emotion_meta(user_id='synthetic-owner',
            scope='emotion_daily:2026-11-07', snapshot_type=snapshot_type, meta_rows=rows),
        materials.compute_source_hash_from_material_meta(user_id='synthetic-owner',
            scope='global', snapshot_type=snapshot_type,
            meta_rows=materials._material_meta_rows_from_rows('emotion_input', rows)),
    )


@pytest.mark.parametrize('field,value', [
    ('memo', '私は考えをノートに書かなかった。私は仕事を続けたくない。'),
    ('memo_action', '私は資料を確認した。'),
    ('emotions', ['平穏']),
    ('emotion_details', [dict(type=kind, strength='strong') for kind in EMOTIONS]),
    ('emotion_strength_avg', 3.0),
    ('category', CATEGORIES[:-1]),
    ('id', '00000000-0000-0000-0000-000000000102'),
    ('created_at', '2026-11-07T02:00:00Z'),
])
def test_editing_each_input_dimension_invalidates_period_and_global_materials(field, value):
    before = deepcopy(ROW)
    changed = deepcopy(before)
    changed[field] = deepcopy(value)
    assert all(a != b for a, b in zip(identities([before]), identities([changed])))
    assert before == ROW
    assert all(len(value) == 64 for value in identities([before]))


def test_material_metadata_retains_no_plaintext_and_secret_changes_do_not_affect_public_identity():
    secret = deepcopy(ROW)
    secret['is_secret'] = True
    meta = materials._material_meta_rows_from_rows('emotion_input', [secret])
    assert not any(key in meta[0] for key in ('memo', 'memo_action', 'emotions', 'emotion_details'))
    assert secret['memo'] not in str(meta) and secret['memo_action'] not in str(meta)
    assert identities([secret], 'public') == identities([], 'public')
    assert identities([secret], 'internal') != identities([], 'internal')
    assert identities([secret], 'internal') != identities([ROW], 'internal')


@pytest.mark.parametrize('strength,score', [('weak', 1.0), ('medium', 2.0), ('strong', 3.0)])
def test_storage_payload_preserves_nine_categories_all_emotions_and_distinct_source_fields(monkeypatch, strength, score):
    import api_emotion_submit as submit
    from emotion_submit_service import normalize_submission_payload
    captured = []
    normalized = normalize_submission_payload(
        emotions=[submit.EmotionItem(type=kind, strength=strength) for kind in EMOTIONS],
        memo=ROW['memo'], memo_action=ROW['memo_action'], category=CATEGORIES)

    class Response:
        status_code = 201

        def json(self):
            return [dict(id=ROW['id'], **captured[0])]

    async def post(path, *, json, prefer, timeout):
        assert path == '/rest/v1/emotions' and prefer == 'return=representation'
        captured.append(deepcopy(json))
        return Response()

    monkeypatch.setattr(submit, '_ensure_supabase_config', lambda: None)
    monkeypatch.setattr(submit, '_sb_post_shared', post)
    saved = asyncio.run(submit._insert_emotion_row(user_id='synthetic-owner',
        emotions=normalized['emotions_tags'], emotion_details=normalized['emotion_details'],
        emotion_strength_avg=normalized['emotion_strength_avg'], memo=ROW['memo'],
        memo_action=ROW['memo_action'], category=normalized['category'],
        created_at=ROW['created_at'], is_secret=False))
    assert saved['category'] == CATEGORIES
    assert saved['emotions'] == EMOTIONS
    assert saved['emotion_details'] == [dict(type=kind, strength=strength) for kind in EMOTIONS]
    assert saved['emotion_strength_avg'] == score
    assert saved['memo'] == ROW['memo'] and saved['memo_action'] == ROW['memo_action']
    assert saved['user_id'] == 'synthetic-owner' and saved['created_at'] == ROW['created_at']


def test_self_structure_materials_keep_all_categories_and_thought_action_fields_separate():
    item = materials._emotion_row_to_self_structure_item(deepcopy(ROW))
    assert item['categories'] == CATEGORIES
    assert item['text_primary'] == ROW['memo']
    assert item['text_secondary'] == ROW['memo_action']
    assert item['emotion_signals'] == EMOTIONS


@pytest.mark.parametrize('strength', ['weak', 'medium', 'strong'])
def test_cumulative_saved_source_keeps_full_original_and_independent_text_fields(strength):
    from cocolon_meaning_experience_engine.cores.analysis.source_adapter import (
        ORIGINAL_FIELDS, AnalysisObservedMapRequest, canonical_bytes, commitment,
        freeze_analysis_sources, source_field_text, _time)
    original = {key: deepcopy(ROW[key]) for key in ORIGINAL_FIELDS}
    original['emotion_details'] = [dict(type=kind, strength=strength) for kind in EMOTIONS]
    start, end = '2026-11-07T00:00:00Z', '2026-11-08T00:00:00Z'
    owner = '00000000-0000-0000-0000-000000000001'
    member, guard = materials._analysis_saved_member(dict(original=original,
        thread=None, events=[], tier='free'), owner=owner, input_id=original['id'],
        tier='free', start=_time(start), end=_time(end), cumulative=True)
    assert member.original_json == canonical_bytes(original).decode('utf-8')
    assert guard[1] == commitment(original)
    sources = freeze_analysis_sources(AnalysisObservedMapRequest('synthetic-current',
        owner, start, end, (member,), selected_category_context=True))
    assert len(sources.sources) == 1
    source = sources.sources[0]
    assert source.normalized['category'] == CATEGORIES
    assert source.normalized['emotion_details'] == original['emotion_details']
    assert source_field_text(source, 'memo') == ROW['memo']
    assert source_field_text(source, 'memo_action') == ROW['memo_action']


@pytest.mark.parametrize('kind', EMOTIONS)
def test_legacy_empty_details_use_existing_selected_emotion_fallback(kind):
    row = dict(created_at=ROW['created_at'], emotions=[kind], emotion_details=[])
    result = weather.build_current_kokoro_weather_from_rows([row],
        end_utc=datetime(2026, 11, 7, 6, tzinfo=timezone.utc))
    assert result['status'] == 'ok'
    assert result['dominant_emotion']['label'] == kind
    assert materials._normalize_details(row) == [dict(type=kind, strength='medium')]


@pytest.mark.parametrize('strength,score', [('weak', 1), ('medium', 2), ('strong', 3)])
def test_all_selected_emotions_and_strengths_survive_both_aggregate_paths(strength, score):
    row = dict(created_at=ROW['created_at'], emotions=EMOTIONS,
        emotion_details=[dict(type=kind, strength=strength) for kind in EMOTIONS])
    assert weather._row_emotion_weights(row) == dict.fromkeys(weather.EMOTION_KEYS, score)
    details = materials._normalize_details(row)
    assert details == row['emotion_details']
    assert row['emotion_details'] == [dict(type=kind, strength=strength) for kind in EMOTIONS]


def test_self_understanding_is_excluded_without_creating_an_ordinary_emotion():
    row = dict(created_at=ROW['created_at'], emotions=['自己理解'], emotion_details=[])
    assert weather._row_emotion_weights(row) == dict.fromkeys(weather.EMOTION_KEYS, 0)
    assert materials._normalize_details(row) == []


@pytest.mark.parametrize('strength,score', [(None, 2), ('weak', 1), ('medium', 2), ('strong', 3)])
def test_worker_engine_adapter_keeps_five_emotions_and_empty_details_fallback(monkeypatch, strength, score):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'services'))
    from analysis_engine_adapter import build_emotion_entries_from_rows
    row = deepcopy(ROW)
    row['emotion_details'] = ([dict(type=kind, strength=strength) for kind in EMOTIONS]
        if strength else [])
    entries = build_emotion_entries_from_rows([row])
    assert {e.label for e in entries} == {'joy', 'sadness', 'anger', 'anxiety', 'peace'}
    assert len(entries) == 5 and all(e.intensity == score for e in entries)
    assert all(e.memo == ROW['memo'] and e.timestamp == ROW['created_at'] for e in entries)
    assert build_emotion_entries_from_rows([dict(row, emotions=['自己理解'], emotion_details=[])]) == []


def test_daily_report_materials_change_identity_and_weights_after_strength_edit(monkeypatch):
    state = {'row': deepcopy(ROW), 'saved': []}

    async def get(path, *, params, timeout=8.0):
        assert path == '/rest/v1/emotions'
        filters = list(params)
        # The previous-day probe is deliberately empty.
        if any(k == 'created_at' and str(v).startswith('lte.2026-11-06') for k, v in filters):
            return []
        columns = next(v for k, v in filters if k == 'select').split(',')
        return [{column: deepcopy(state['row'].get(column)) for column in columns}]

    async def store(**kwargs):
        state['saved'].append(deepcopy(kwargs))
        return True

    monkeypatch.setattr(materials, '_sb_get_json', get)
    monkeypatch.setattr(materials, '_insert_snapshot_row', store)
    monkeypatch.setattr(materials, 'enqueue_job', None)
    first = asyncio.run(materials._generate_and_store_emotion_period_snapshots(
        user_id='synthetic-owner', scope='emotion_daily:2026-11-07', trigger='synthetic-test'))
    state['row']['emotion_details'][3]['strength'] = 'strong'
    second = asyncio.run(materials._generate_and_store_emotion_period_snapshots(
        user_id='synthetic-owner', scope='emotion_daily:2026-11-07', trigger='synthetic-test'))
    assert first['internal']['source_hash'] != second['internal']['source_hash']
    assert first['public']['source_hash'] != second['public']['source_hash']
    assert state['saved'][0]['payload']['views']['day']['anxiety'] == 1
    assert state['saved'][2]['payload']['views']['day']['anxiety'] == 3
