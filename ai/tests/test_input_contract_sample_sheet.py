"""The replacement operation sheet through real API normalization and Analysis.

The sheet is fictional. Only external database I/O is doubled in the insert
test; this never authenticates, inserts production rows, or invokes a model.
"""
import asyncio
import copy
import json
from pathlib import Path
from unittest.mock import patch
from uuid import UUID

import httpx
import pytest

import api_emotion_submit as submit
import analysis_cumulative_service as cumulative
from cocolon_meaning_experience_engine.cores.analysis.source_adapter import (
    AnalysisObservedMapRequest, AnalysisSavedRecord, canonical_bytes,
    commitment, freeze_analysis_sources,
)

SHEET_PATH = Path(__file__).parent / 'fixtures/cocolon-input-contract-samples-20261107.json'
SHEET = json.loads(SHEET_PATH.read_text())
OWNER = str(UUID(int=77001))


def normalized_row(sample, index):
    wire = dict(memo=sample['memo'], emotions=sample['emotion_details'],
        category=sample['category'], is_secret=sample['is_secret'],
        send_emotion_notification=sample['send_emotion_notification'],
        created_at=f'2026-11-07T01:{index:02d}:00+00:00')
    if sample['memo_action']:
        wire['memo_action'] = sample['memo_action']
    request = submit.EmotionSubmitRequest(**wire)
    tags, details, average = submit._normalize_emotions(request.emotions)
    row = dict(id=str(UUID(int=77100 + index)), created_at=request.created_at,
        memo=request.memo, memo_action=request.memo_action or '',
        category=submit._normalize_categories(request.category),
        emotions=tags, emotion_details=details)
    return request, row, average


@pytest.mark.parametrize('sample', SHEET['cases'], ids=lambda sample: sample['case_id'])
def test_actual_request_normalization_and_insert_keep_each_sheet_value(sample):
    index = int(sample['case_id'])
    request, row, average = normalized_row(sample, index)
    sent = []

    async def database_post(path, **options):
        assert path == '/rest/v1/emotions'
        sent.append(copy.deepcopy(options['json']))
        return httpx.Response(201, json=[dict(options['json'], id=row['id'])])

    with patch.object(submit, '_ensure_supabase_config'), \
            patch.object(submit, '_sb_post_shared', database_post):
        result = asyncio.run(submit._insert_emotion_row(user_id=OWNER,
            emotions=row['emotions'], emotion_details=row['emotion_details'],
            emotion_strength_avg=average, memo=request.memo,
            memo_action=request.memo_action, category=row['category'],
            created_at=request.created_at, is_secret=request.is_secret))
    assert len(sent) == 1
    assert result['id'] == row['id']
    assert result['memo'] == sample['memo']
    assert result.get('memo_action', '') == sample['memo_action']
    assert result['category'] == sample['category']
    assert result['emotion_details'] == sample['emotion_details']
    assert result['emotions'] == [item['type'] for item in sample['emotion_details']]
    assert result['user_id'] == OWNER
    assert result['is_secret'] is False
    assert request.notify_friends is False
    assert 'send_emotion_notification' not in result


def source_snapshot():
    members = []
    for index, sample in enumerate(SHEET['cases'], 1):
        _, row, _ = normalized_row(sample, index)
        members.append(dict(original=row, thread=None, events=[]))
    return dict(members=members, tier='free', now='2026-11-07T02:00:00+00:00',
        period_start='2026-11-07T00:00:00+00:00',
        period_end='2026-11-07T02:00:00+00:00',
        guard='analysis-db-cumulative-v1:' + 'a' * 64)


def test_every_sheet_source_keeps_both_fields_categories_and_each_strength():
    snapshot = source_snapshot()
    for member, sample in zip(snapshot['members'], SHEET['cases']):
        original = member['original']
        saved = AnalysisSavedRecord(OWNER, original['id'], commitment(original),
            canonical_bytes(original).decode())
        request = AnalysisObservedMapRequest('replacement-sheet-' + sample['case_id'],
            OWNER, snapshot['period_start'], snapshot['period_end'], (saved,),
            selected_category_context=True)
        frozen = freeze_analysis_sources(request)
        source, = frozen.sources
        assert source.normalized['memo'] == sample['memo']
        assert source.normalized['memo_action'] == sample['memo_action']
        assert source.normalized['category'] == sample['category']
        assert source.normalized['emotion_details'] == sample['emotion_details']
        for span in source.evidence:
            assert span.field_path in original
            raw = source.envelope.raw_utf8
            raw[span.utf8_start:span.utf8_end].decode('utf-8')


def test_complete_sheet_uses_the_real_cumulative_compiler_and_discloses_unparsed_input():
    snapshot = source_snapshot()
    before = copy.deepcopy(snapshot)
    artifact, coverage = cumulative.build_cumulative_map(OWNER, snapshot)
    assert snapshot == before
    assert artifact is not None
    assert coverage['source_count'] == len(SHEET['cases']) == 11
    assert coverage['processed_count'] == 11
    assert coverage['excluded_count'] == 0
    # This fixture exercises operations and fidelity, not universal language
    # understanding. Its unsupported natural prose must remain disclosed.
    assert coverage['unparsed_count'] > 0
    assert 0 < coverage['mapped_count'] <= 11
    assert len(artifact.source_members) == 11
    raw_by_id = {item['original']['id']: item['original'] for item in snapshot['members']}
    for node in artifact.graph.nodes:
        assert set(node.record_refs) <= set(raw_by_id)
        for evidence in node.evidence_refs:
            assert evidence.field_path in {'memo', 'memo_action'}
    projection = artifact.safe_projection(authenticated_owner_scope=OWNER)
    text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
    assert projection['nodes']
    assert text
