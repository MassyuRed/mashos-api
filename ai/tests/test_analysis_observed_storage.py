"""Saved Analysis API contracts with synthetic auth/DB I/O and the real engine."""
import copy
from datetime import datetime, timedelta, timezone
import json
import os
import unittest
from unittest.mock import AsyncMock, patch
from uuid import UUID

from fastapi import HTTPException
import httpx
import analysis_observed_service as service
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.cores.analysis.source_adapter import (
    AnalysisObservedMapRequest, AnalysisSavedRecord, canonical_bytes, commitment,
)

OWNER, OTHER = str(UUID(int=1)), str(UUID(int=2))
START, END = '2026-10-01T00:00:00+00:00', '2026-10-03T00:00:00+00:00'
GUARD = 'analysis-db-v1:' + 'a' * 64


def fixture(memo='私は考えをノートに書いた。私は仕事を続けたい。'):
    original = {'id': str(UUID(int=101)), 'created_at': '2026-10-01T01:00:00',
        'memo': memo, 'memo_action': '',
        'category': ['仕事'], 'emotions': ['平穏'], 'emotion_details': []}
    member = AnalysisSavedRecord(OWNER, original['id'], commitment(original), canonical_bytes(original).decode())
    artifact = MeaningExperienceEngine().generate(AnalysisObservedMapRequest(
        'synthetic-storage', OWNER, START, END, (member,))).artifact
    projection = artifact.safe_projection(authenticated_owner_scope=OWNER)
    row = {'id': str(UUID(artifact.artifact_id[9:])), 'report_type': 'latest',
        'report_mode': 'standard', 'title': 'わたしマップ', 'period_start': START, 'period_end': END,
        'generated_at': END, 'updated_at': END,
        'content_text': artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'],
        'content_json': {'report_mode': 'standard', 'watashiMap': projection}}
    return {'original': original, 'private': service.private_storage_evidence(artifact), 'row': row}


def result(rows, tier='plus', matched=False):
    return {'items': rows, 'subscription_tier': tier, 'matched': matched}


class SavedAnalysisTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.fx = fixture()
        self.row = self.fx['row']

    async def test_generate_commits_and_rereads_exact_identity(self):
        writes = []
        async def rpc(name, payload):
            if name == 'analysis_observed_source_snapshot':
                return {'guard': GUARD, 'tier': 'plus', 'now': END, 'members': [
                    {'original': self.fx['original'], 'thread': None, 'events': []}]}
            if name == 'analysis_observed_commit':
                writes.append(payload)
                projection = payload['p_projection']
                self.row['id'] = str(UUID(payload['p_artifact_id'][9:]))
                self.row['content_text'] = payload['p_text']
                self.row['content_json']['watashiMap'] = projection
                return self.row['id']
            return result([self.row], matched=True)
        with patch.object(service, '_rpc', side_effect=rpc):
            saved = await service.generate_saved(OWNER, start=START, end=END,
                report_mode='standard', report_type='latest')
        self.assertEqual(saved['content_json']['watashiMap'], writes[0]['p_projection'])
        self.assertEqual(saved['content_text'], writes[0]['p_text'])
        encoded = json.dumps(writes[0]['p_private_evidence'], ensure_ascii=False)
        self.assertNotIn('私は', encoded)
        self.assertNotIn('visible_label', encoded)
        self.assertNotIn('original_json', encoded)
        self.assertIn('evidence_refs', encoded)
        self.assertEqual(writes[0]['p_guard'], GUARD)

    async def test_sequence_occurrences_survive_save_and_read_without_reinterpretation(self):
        self.fx = fixture('私は資料を調べた。その後私は考えをノートに書いた。'
                          'それから私は資料を調べた。')
        self.row = self.fx['row']
        writes = []
        async def rpc(name, payload):
            if name == 'analysis_observed_source_snapshot':
                return {'guard': GUARD, 'tier': 'plus', 'now': END, 'members': [
                    {'original': self.fx['original'], 'thread': None, 'events': []}]}
            if name == 'analysis_observed_commit':
                writes.append(payload)
                self.row['id'] = str(UUID(payload['p_artifact_id'][9:]))
                self.row['content_text'] = payload['p_text']
                self.row['content_json']['watashiMap'] = payload['p_projection']
                return self.row['id']
            return result([self.row], matched=True)
        with patch.object(service, '_rpc', side_effect=rpc):
            saved = await service.generate_saved(OWNER, start=START, end=END,
                report_mode='standard', report_type='latest')
            with patch.object(MeaningExperienceEngine, 'generate',
                              side_effect=AssertionError('read regenerated')):
                reread = await service.read_saved(OWNER)
        projection = saved['content_json']['watashiMap']
        self.assertEqual(len(projection['nodes']), 3)
        self.assertEqual([(e['from_ref'], e['to_ref']) for e in projection['edges']],
                         [('n1', 'n2'), ('n2', 'n3')])
        self.assertEqual(projection, writes[0]['p_projection'])
        self.assertEqual(saved['content_text'], writes[0]['p_text'])
        self.assertEqual(reread['items'][0], saved)
        encoded = json.dumps(writes[0]['p_private_evidence'], ensure_ascii=False)
        for private in ('私は', 'proposition', 'sequence_marker', 'source_parts', 'visible_label'):
            self.assertNotIn(private, encoded)

    async def test_saved_relative_day_remains_statement_bound_when_read(self):
        fx = fixture('昨日私は資料を調べた。今日私は資料を調べなかった。')
        row = fx['row']
        with patch.object(service, '_rpc', AsyncMock(return_value=result([row]))), \
             patch.object(MeaningExperienceEngine, 'generate', side_effect=AssertionError('read regenerated')):
            value = await service.read_saved(OWNER)
        self.assertEqual(value['items'][0], row)
        projection = value['items'][0]['content_json']['watashiMap']
        self.assertEqual([n['visible_label'] for n in projection['nodes']], [
            'この記述時点の昨日：資料を調べる（実行済み）',
            'この記述時点の今日：資料を調べる（行わなかった）'])
        self.assertFalse(projection['edges'])
        for label in [n['visible_label'] for n in projection['nodes']]:
            self.assertIn(label, value['items'][0]['content_text'])
        encoded = json.dumps(fx['private'], ensure_ascii=False)
        for private in ('relative_day', 'source_parts', 'visible_label', '昨日', '今日'):
            self.assertNotIn(private, encoded)

    async def test_read_never_generates_and_preserves_wire(self):
        with patch.object(service, '_rpc', AsyncMock(return_value=result([self.row]))), \
             patch.object(MeaningExperienceEngine, 'generate', side_effect=AssertionError('read regenerated')):
            value = await service.read_saved(OWNER)
        self.assertEqual(value['items'][0], self.row)

    async def test_corrupt_private_and_mismatched_text_are_rejected(self):
        for kind in ('private', 'text', 'identity', 'edge'):
            row = copy.deepcopy(self.row)
            if kind == 'private': row['content_json']['watashiMap']['raw_body'] = 'PRIVATE'
            if kind == 'text': row['content_text'] = 'PRIVATE old source'
            if kind == 'identity': row['id'] = OTHER
            if kind == 'edge': row['content_json']['watashiMap']['edges'] = [{'source_ref': 'PRIVATE'}]
            with patch.object(service, '_rpc', AsyncMock(return_value=result([row]))):
                with self.assertRaises(HTTPException) as raised: await service.read_saved(OWNER)
                self.assertEqual(raised.exception.status_code, 503)
                self.assertNotIn('PRIVATE', raised.exception.detail)

    async def test_free_history_and_plus_deep_never_return_body(self):
        for tier, mode, history in [('free', 'light', True), ('free', 'standard', False), ('plus', 'deep', False)]:
            row = copy.deepcopy(self.row)
            row['report_mode'] = row['content_json']['report_mode'] = mode
            with patch.object(service, '_rpc', AsyncMock(return_value=result([row], tier))):
                with self.assertRaises(HTTPException): await service.read_saved(OWNER, history=history)

    async def test_lost_ack_not_retried_or_returned_as_saved(self):
        with patch.object(service, 'sb_post_rpc', AsyncMock(side_effect=httpx.ReadTimeout('PRIVATE'))) as io:
            with self.assertRaises(HTTPException) as raised: await service._rpc('analysis_observed_commit', {})
        self.assertEqual(io.await_count, 1)
        self.assertEqual(raised.exception.status_code, 503)
        self.assertNotIn('PRIVATE', raised.exception.detail)

    async def test_conflict_never_falls_back(self):
        with patch.dict(os.environ, COCOLON_ANALYSIS_OBSERVED_MODE='development'), \
             patch.object(service, 'read_saved', AsyncMock(return_value=result([]))), \
             patch.object(service, 'generate_saved', AsyncMock(side_effect=HTTPException(409, 'changed'))):
            with self.assertRaises(HTTPException) as raised:
                await service.ensure_saved(OWNER, period='28d', report_mode='standard')
        self.assertEqual(raised.exception.status_code, 409)

    async def test_read_only_retains_old_valid_saved_map(self):
        row = copy.deepcopy(self.row)
        end = datetime.now(timezone.utc)-timedelta(days=3)
        row.update(period_start=(end-timedelta(days=28)).isoformat(), period_end=end.isoformat())
        with patch.dict(os.environ, COCOLON_ANALYSIS_OBSERVED_MODE='read_only'), \
             patch.object(service, 'read_saved', AsyncMock(return_value=result([row]))), \
             patch.object(service, 'generate_saved', AsyncMock(side_effect=AssertionError('read-only write'))):
            answer = await service.ensure_saved(OWNER, period='28d', report_mode='standard', force=True)
        self.assertTrue(answer['has_visible_content'])
        self.assertFalse(answer['refreshed'])

    async def test_status_selects_same_tier_default_mode(self):
        standard, deep = copy.deepcopy(self.row), copy.deepcopy(self.row)
        deep['report_mode'] = 'deep'
        with patch.object(service, 'read_saved', AsyncMock(side_effect=[result([standard], 'premium'), result([deep], 'premium')])) as read:
            status = await service.saved_status(OWNER)
        self.assertEqual(read.await_args.kwargs['report_mode'], 'deep')
        self.assertEqual(status['version_key'], deep['content_json']['watashiMap']['projection_of'])

    async def test_monthly_exclusive_end_and_no_view_time_regeneration(self):
        with patch.dict(os.environ, COCOLON_ANALYSIS_OBSERVED_MODE='development'), \
             patch.object(service, 'read_saved', AsyncMock(return_value=result([]))), \
             patch.object(service, 'generate_saved', AsyncMock(return_value=self.row)) as generate:
            await service.ensure_saved(OWNER, period='28d', report_mode='standard', monthly=True)
        end = datetime.fromisoformat(generate.await_args.kwargs['end']).astimezone(timezone(timedelta(hours=9)))
        self.assertEqual((end.day, end.hour, end.minute, end.second, end.microsecond), (1, 0, 0, 0, 0))


if __name__ == '__main__':
    unittest.main()
