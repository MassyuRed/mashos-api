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
from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.cores.analysis import observed_route_realizer as realizer
from cocolon_meaning_experience_engine.cores.analysis.source_adapter import (
    AnalysisObservedMapRequest, AnalysisSavedRecord, AnalysisSourceError, canonical_bytes, commitment,
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


async def comparison_fixture(*, previous_memo='私は考えをノートに書かなかった。', empty=False, eligible=True):
    """Real save service/engine, synthetic DB transport; also consumed by SQL tests."""
    fx = fixture()
    previous = dict(fx['original'], id=str(UUID(int=99)), created_at='2026-09-30T01:00:00', memo=previous_memo)
    previous_start = '2026-09-29T00:00:00+00:00'
    writes = []
    async def rpc(name, payload):
        if name == 'analysis_observed_comparison_snapshot':
            def snapshot(originals):
                return {'guard': GUARD, 'tier': 'plus', 'now': END, 'members': [
                    {'original': s, 'thread': None, 'events': []} for s in originals]}
            if not eligible:
                return {'comparison_eligible': False, 'current': snapshot([fx['original']]),
                        'guard': GUARD, 'tier': 'plus'}
            return {'guard': 'analysis-db-compare-v1:' + 'b' * 64, 'tier': 'plus', 'comparison_eligible': True,
                'current': snapshot([fx['original']]), 'previous': snapshot([] if empty else [previous]),
                'previous_start': previous_start, 'previous_end': START}
        if name == 'analysis_observed_commit':
            writes.append(payload)
            fx['row'].update(id=str(UUID(payload['p_artifact_id'][9:])), content_text=payload['p_text'])
            fx['row']['content_json']['watashiMap'] = payload['p_projection']
            return fx['row']['id']
        if name == 'analysis_observed_read':
            return result([fx['row']], matched=True)
        raise AssertionError(name)
    with patch.dict(os.environ, COCOLON_ANALYSIS_PERIOD_COMPARISON_MODE='development'), \
            patch.object(service, '_rpc', side_effect=rpc):
        await service.generate_saved(OWNER, start=START, end=END, report_mode='standard', report_type='latest')
    fx.update(private=writes[0]['p_private_evidence'], previous_original=None if empty else previous)
    return fx


async def storage_sql_fixture():
    fx = fixture()
    fx['comparison'] = await comparison_fixture()
    fx['empty_comparison'] = await comparison_fixture(empty=True)
    fx['unchanged_comparison'] = await comparison_fixture(previous_memo=fx['original']['memo'])
    return fx


class SavedAnalysisTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.fx = fixture()
        self.row = self.fx['row']

    async def test_generation_failure_logs_current_reason_without_saving(self):
        for members in ([{'original': dict(self.fx['original'], memo=memo),
                          'thread': None, 'events': []}] for memo in ('未対応の合成記録です。', '')):
            snapshot = {'guard': GUARD, 'tier': 'plus', 'now': END, 'members': members}
            with self.subTest(memo=members[0]['original']['memo']), \
                    patch.dict(os.environ, COCOLON_ANALYSIS_PERIOD_COMPARISON_MODE='off'), \
                    patch.object(service, '_rpc', AsyncMock(return_value=snapshot)) as rpc, \
                    self.assertLogs(realizer.logger, level='WARNING') as logs:
                with self.assertRaises(HTTPException) as caught:
                    await service.generate_saved(OWNER, start=START, end=END,
                        report_mode='standard', report_type='latest')
            self.assertEqual((caught.exception.status_code, caught.exception.detail),
                             (422, 'analysis_observed_map_unavailable'))
            self.assertEqual([call.args[0] for call in rpc.await_args_list],
                             ['analysis_observed_source_snapshot'])
            self.assertEqual([r.getMessage() for r in logs.records], [
                'analysis_observed_generation_unavailable stage=current '
                'reason=analysis_observed_route_not_established'])

    async def test_empty_current_period_skips_engine_and_storage(self):
        empty = {'guard': GUARD, 'tier': 'plus', 'now': END, 'members': []}
        previous = dict(empty, members=[{'original': dict(self.fx['original'],
            id=str(UUID(int=99)), created_at='2026-09-30T01:00:00', memo='未対応の合成記録です。'),
            'thread': None, 'events': []}])
        snapshots = [
            ('off', empty),
            ('development', {'guard': GUARD, 'tier': 'plus', 'comparison_eligible': False,
                             'current': empty}),
        ]
        for previous_source in (empty, previous):
            snapshots.append(('development', {'guard': 'analysis-db-compare-v1:' + 'b' * 64,
                'tier': 'plus', 'comparison_eligible': True, 'current': empty, 'previous': previous_source,
                'previous_start': '2026-09-29T00:00:00+00:00', 'previous_end': START}))
        for mode, snapshot in snapshots:
            with self.subTest(mode=mode, eligible=snapshot.get('comparison_eligible')), \
                    patch.dict(os.environ, COCOLON_ANALYSIS_PERIOD_COMPARISON_MODE=mode), \
                    patch.object(service, '_rpc', AsyncMock(return_value=snapshot)) as rpc, \
                    patch.object(MeaningExperienceEngine, 'generate') as engine, \
                    patch('response_microcache.invalidate_prefix', AsyncMock()) as invalidate, \
                    self.assertNoLogs(realizer.logger, level='WARNING'):
                row = await service.generate_saved(OWNER, start=START, end=END,
                    report_mode='standard', report_type='latest')
            self.assertIsNone(row)
            engine.assert_not_called()
            invalidate.assert_not_awaited()
            self.assertEqual([call.args[0] for call in rpc.await_args_list], [
                'analysis_observed_source_snapshot' if mode == 'off' else 'analysis_observed_comparison_snapshot'])

    async def test_empty_current_does_not_hide_invalid_snapshot_or_period(self):
        empty = {'guard': GUARD, 'tier': 'plus', 'now': END, 'members': []}
        comparison = {'guard': 'analysis-db-compare-v1:' + 'b' * 64, 'tier': 'plus',
            'comparison_eligible': True, 'current': empty, 'previous': empty,
            'previous_start': '2026-09-29T00:00:00+00:00', 'previous_end': START}
        cases = [('off', empty, 'invalid', END), ('off', empty, END, START),
                 ('off', empty, START, START), ('off', dict(empty, guard='invalid'), START, END),
                 ('off', dict(empty, members=None), START, END),
                 ('development', dict(comparison, previous_end=END), START, END),
                 ('development', dict(comparison, previous=dict(empty, tier='free')), START, END),
                 ('development', dict(comparison, previous=dict(empty, members=None)), START, END)]
        for mode, snapshot, start, end in cases:
            with self.subTest(mode=mode, start=start, end=end, snapshot=snapshot), \
                    patch.dict(os.environ, COCOLON_ANALYSIS_PERIOD_COMPARISON_MODE=mode), \
                    patch.object(service, '_rpc', AsyncMock(return_value=snapshot)) as rpc, \
                    patch.object(MeaningExperienceEngine, 'generate') as engine:
                with self.assertRaises(HTTPException) as caught:
                    await service.generate_saved(OWNER, start=start, end=end,
                        report_mode='standard', report_type='latest')
            self.assertEqual((caught.exception.status_code, caught.exception.detail),
                             (422, 'analysis_saved_source_unavailable'))
            engine.assert_not_called()
            self.assertEqual(rpc.await_count, 1)

    async def test_generation_failure_logs_previous_reason_once(self):
        with self.assertLogs(realizer.logger, level='WARNING') as logs:
            with self.assertRaises(HTTPException) as caught:
                await comparison_fixture(previous_memo='未対応の合成記録です。')
        self.assertEqual((caught.exception.status_code, caught.exception.detail),
                         (422, 'analysis_observed_map_unavailable'))
        self.assertEqual([r.getMessage() for r in logs.records], [
            'analysis_observed_generation_unavailable stage=previous '
            'reason=analysis_observed_route_not_established'])

    async def test_comparison_failure_logs_detail_but_keeps_generic_outcome(self):
        original_generate = realizer.generate_observed_map
        outcomes = []
        def generate(request):
            outcome = original_generate(request)
            outcomes.append(outcome)
            return outcome
        for exception, reason in (
                (AnalysisSourceError('analysis_comparison_evidence_unavailable'),
                 'analysis_comparison_evidence_unavailable'),
                (AnalysisSourceError('合成秘密本文\n' + OWNER), 'analysis_generation_reason_unclassified'),
                (ValueError('合成秘密本文\n' + OWNER), 'analysis_comparison_unavailable')):
            with self.subTest(reason=reason), \
                    patch.object(realizer, 'compare_period_meaning', side_effect=exception), \
                    patch('cocolon_meaning_experience_engine.engine.generate_observed_map', side_effect=generate), \
                    self.assertLogs(realizer.logger, level='WARNING') as logs:
                with self.assertRaises(HTTPException) as caught:
                    await comparison_fixture()
            self.assertEqual((caught.exception.status_code, caught.exception.detail),
                             (422, 'analysis_observed_map_unavailable'))
            self.assertEqual(outcomes[-1].reason_codes, ('analysis_comparison_unavailable',))
            self.assertIsNone(outcomes[-1].artifact)
            self.assertEqual([r.getMessage() for r in logs.records], [
                'analysis_observed_generation_unavailable stage=comparison reason=' + reason])
            self.assertTrue(all(r.exc_info is None and r.stack_info is None for r in logs.records))

    async def test_generation_failure_log_rejects_unclassified_values(self):
        class PrivateValue:
            def __str__(self):
                raise AssertionError('must not stringify diagnostic data')
        for value in ('合成秘密本文\n' + OWNER, 'analysis_source_invalid\n' + OWNER,
                      '', [], {}, PrivateValue()):
            with self.subTest(value_type=type(value).__name__), \
                    self.assertLogs(realizer.logger, level='WARNING') as logs:
                realizer._failed_outcome(EngineStatus.UNAVAILABLE, 'analysis_source_invalid',
                    stage=value, diagnostic_reason=value)
            self.assertEqual([r.getMessage() for r in logs.records], [
                'analysis_observed_generation_unavailable stage=unclassified '
                'reason=analysis_generation_reason_unclassified'])
            self.assertTrue(all(r.exc_info is None and r.stack_info is None for r in logs.records))
        with patch.object(realizer, 'compile_observed_graph',
                          side_effect=RuntimeError('合成秘密本文\n' + OWNER)), \
                self.assertLogs(realizer.logger, level='WARNING') as logs:
            outcome = MeaningExperienceEngine().generate(AnalysisObservedMapRequest(
                'synthetic-log-request', OWNER, START, END, ()))
        self.assertEqual(outcome.reason_codes, ('analysis_semantic_generation_unavailable',))
        self.assertEqual([r.getMessage() for r in logs.records], [
            'analysis_observed_generation_unavailable stage=current '
            'reason=analysis_semantic_generation_unavailable'])

    async def test_successful_generation_emits_no_failure_log(self):
        with self.assertNoLogs(realizer.logger, level='WARNING'):
            for options in ({}, {'empty': True}, {'eligible': False}):
                fx = await comparison_fixture(**options)
                self.assertTrue(fx['row']['content_json']['watashiMap']['nodes'])

    async def test_comparison_requires_matching_saved_text(self):
        for state, kinds, reasons in (('COMPARABLE', ['ROUTE_EVIDENCE_CHANGED'], []),
                ('NOT_COMPARABLE', [], ['PERIOD_OVERLAP'])):
            with self.subTest(state=state):
                row = copy.deepcopy(self.row)
                row['content_json']['watashiMap']['period_comparison'] = {
                    'state': state, 'safe_change_kinds': kinds, 'reason_codes': reasons}
                with patch.object(service, '_rpc', AsyncMock(return_value=result([row]))):
                    with self.assertRaises(HTTPException) as caught:
                        await service.read_saved(OWNER)
                self.assertEqual(caught.exception.status_code, 503)

    async def test_comparison_save_read_preserves_both_private_artifacts_and_public_identity(self):
        fx = await comparison_fixture()
        row, private = fx['row'], fx['private']
        self.assertEqual(row['content_json']['watashiMap']['period_comparison']['state'], 'COMPARABLE')
        self.assertIn('読み取れた内容・つながり', row['content_text'])
        self.assertEqual(private['schema_version'], 'analysis.private-evidence.v2')
        c, previous = private['period_comparison'], private['previous_evidence']
        self.assertEqual(c['current_artifact_ref'], private['projection_of'])
        self.assertEqual(c['previous_artifact_ref'], previous['projection_of'])
        self.assertEqual(c['previous_source_set_ref'], previous['source_set_ref'])
        for claim in c['change_claims']:
            self.assertTrue(claim['evidence_refs'])
        for raw in ('visible_label', 'predicate_lemma', 'original_json', '私は', 'ノート'):
            self.assertNotIn(raw, json.dumps(private, ensure_ascii=False))
        for secret in ('previous_evidence', 'comparison_dependency', 'evidence_refs', c['previous_artifact_ref']):
            self.assertNotIn(secret, json.dumps(row, ensure_ascii=False))
        with patch.object(service, '_rpc', AsyncMock(return_value=result([row], matched=True))), \
                patch.object(MeaningExperienceEngine, 'generate', side_effect=AssertionError('read regenerated')):
            reread = await service.read_saved(OWNER, report_id=row['id'])
        self.assertEqual(reread['items'][0], row)

    async def test_empty_previous_is_dependency_but_unreadable_previous_is_not_first_use(self):
        fx = await comparison_fixture(empty=True)
        self.assertEqual(fx['row']['content_json']['watashiMap']['period_comparison']['state'], 'NO_PREVIOUS')
        self.assertIsNone(fx['private']['previous_evidence'])
        self.assertIsNone(fx['private']['period_comparison'])
        self.assertEqual(fx['private']['comparison_dependency']['policy'], 'adjacent-equal-v1')
        with self.assertRaises(HTTPException) as caught:
            await comparison_fixture(previous_memo='この文は未対応の合成記録です。')
        self.assertEqual(caught.exception.status_code, 422)

    async def test_comparison_flag_defaults_off_and_requires_exact_development_value(self):
        for value in ('', 'off', 'true', 'enabled', 'invalid'):
            with patch.dict(os.environ, COCOLON_ANALYSIS_PERIOD_COMPARISON_MODE=value):
                self.assertFalse(service.period_comparison_enabled())
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(service.period_comparison_enabled())

    async def test_previous_outside_retention_keeps_current_single_period_available(self):
        fx = await comparison_fixture(eligible=False)
        self.assertEqual(fx['private']['schema_version'], 'analysis.private-evidence.v1')
        self.assertNotIn('comparison_dependency', fx['private'])
        self.assertEqual(fx['row']['content_json']['watashiMap']['period_comparison']['state'], 'NO_PREVIOUS')

    async def test_comparison_storage_errors_never_fall_back_to_single_period(self):
        for status in (403, 404, 409, 422, 503):
            with patch.dict(os.environ, COCOLON_ANALYSIS_PERIOD_COMPARISON_MODE='development'), \
                    patch.object(service, '_rpc', AsyncMock(side_effect=HTTPException(status, 'unavailable'))) as rpc:
                with self.assertRaises(HTTPException) as caught:
                    await service.generate_saved(OWNER, start=START, end=END, report_mode='standard', report_type='latest')
                self.assertEqual(caught.exception.status_code, status)
                self.assertEqual(rpc.await_count, 1)

    async def test_saved_comparison_rejects_private_unknown_duplicate_and_inconsistent_fields(self):
        fx = await comparison_fixture()
        for mutation in ('private', 'kind', 'duplicate', 'reasons', 'state', 'not_comparable', 'not_list'):
            with self.subTest(mutation=mutation):
                row = copy.deepcopy(fx['row'])
                c = row['content_json']['watashiMap']['period_comparison']
                if mutation == 'private': c['previous_artifact_ref'] = 'private'
                if mutation == 'kind': c['safe_change_kinds'] = ['IMPROVED']
                if mutation == 'duplicate': c['safe_change_kinds'] *= 2
                if mutation == 'reasons': c['reason_codes'] = ['PERIOD_OVERLAP']
                if mutation == 'state': c['state'] = 'NO_PREVIOUS'
                if mutation == 'not_comparable': c.update(state='NOT_COMPARABLE', reason_codes=[])
                if mutation == 'not_list': c['safe_change_kinds'] = {}
                with patch.object(service, '_rpc', AsyncMock(return_value=result([row]))):
                    with self.assertRaises(HTTPException): await service.read_saved(OWNER)

    async def test_protective_intention_survives_save_read_with_private_evidence_separate(self):
        for memo in ('私は家族を守りたい。私は仕事を続けたいけれど、私はつらい。',
                     '私は、家族を守りたい。私は仕事を続けたいけれど、私はつらい。',
                     '僕は，　家族を守りたいです。私は仕事を続けたいけれど、私はつらい。'):
            with self.subTest(memo=memo):
                self.fx = fixture(memo)
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
                    with patch.object(MeaningExperienceEngine, 'generate', side_effect=AssertionError('regenerated')):
                        reread = await service.read_saved(OWNER, report_id=saved['id'], report_mode='standard')
                self.assertEqual(saved, reread['items'][0])
                projection = saved['content_json']['watashiMap']
                self.assertEqual(projection, writes[0]['p_projection'])
                self.assertEqual(saved['content_text'], writes[0]['p_text'])
                self.assertEqual([a['kind'] for a in projection['annotation_badges']], ['PROTECTIVE', 'BURDEN'])
                private = writes[0]['p_private_evidence']
                self.assertEqual(private['graph']['annotations'][0]['evidence_refs'],
                                 private['graph']['nodes'][0]['evidence_refs'])
                for key in ('source_labels', 'predicate_lemma', 'visible_label', 'original_json', '家族', '守りたい'):
                    self.assertNotIn(key, json.dumps(private, ensure_ascii=False))
                for key in ('evidence_refs', 'source_envelope_id', 'literal_sha256', 'annotation_state'):
                    self.assertNotIn(key, json.dumps(saved, ensure_ascii=False))

    async def test_saved_protective_rejects_other_target_and_false_outcome(self):
        base = fixture('私は仕事を続けたい。私は記録を残した。私は家族を守りたい。')['row']
        for mutation in ('wish', 'action', 'unknown', 'kind', 'outcome', 'private', 'duplicate', 'text', 'target_label'):
            with self.subTest(mutation=mutation):
                row = copy.deepcopy(base)
                projection = row['content_json']['watashiMap']
                badge = projection['annotation_badges'][0]
                if mutation == 'wish': badge['target_ref'] = 'n1'
                if mutation == 'action': badge['target_ref'] = 'n2'
                if mutation == 'unknown': badge['target_ref'] = 'n999'
                if mutation == 'kind': badge['kind'] = 'BURDEN'
                if mutation == 'outcome': badge['visible_label'] = '家族を守れています。'
                if mutation == 'private': badge['source_labels'] = ['私は家族を守りたい']
                if mutation == 'duplicate': projection['annotation_badges'].append(dict(badge, annotation_ref='a2'))
                if mutation == 'text': row['content_text'] = row['content_text'].split('注記')[0]
                if mutation == 'target_label': projection['nodes'][2]['visible_label'] = '家族を守ることを望まない'
                with patch.object(service, '_rpc', AsyncMock(return_value=result([row]))):
                    with self.assertRaises(HTTPException) as raised:
                        await service.read_saved(OWNER)
                self.assertEqual(raised.exception.status_code, 503)

    async def test_repeated_period_saves_compact_gaps_and_keeps_all_private_sources(self):
        self.fx = fixture('私は仕事を続けたいけれど、私はつらい。')
        self.row = self.fx['row']
        second = dict(self.fx['original'], id=str(UUID(int=102)),
            created_at='2026-10-02T01:00:00', memo='僕は仕事を続けたいけれど、僕はつらいです。')
        writes = []
        async def rpc(name, payload):
            if name == 'analysis_observed_source_snapshot':
                return {'guard': GUARD, 'tier': 'plus', 'now': END, 'members': [
                    {'original': original, 'thread': None, 'events': []}
                    for original in (self.fx['original'], second)]}
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
            with patch.object(MeaningExperienceEngine, 'generate', side_effect=AssertionError('regenerated')):
                reread = await service.read_saved(OWNER, report_id=saved['id'], report_mode='standard')
        self.assertEqual(saved, reread['items'][0])
        projection = saved['content_json']['watashiMap']
        self.assertEqual(projection, writes[0]['p_projection'])
        self.assertEqual(saved['content_text'], writes[0]['p_text'])
        self.assertEqual(len(projection['unknown_gaps']), 4)
        self.assertEqual(saved['content_text'].count('未確定（'), 4)
        private = writes[0]['p_private_evidence']
        self.assertEqual(len(private['source_members']), 2)
        self.assertEqual(len(private['graph']['unknown_gaps']), 8)
        self.assertEqual(len(private['graph']['nodes'][0]['evidence_refs']), 2)
        self.assertEqual(len(private['graph']['annotations'][0]['evidence_refs']), 6)
        for key in ('reason_code', 'missing_scope', 'evidence_refs', 'source_members'):
            self.assertNotIn(json.dumps(key) + ':', json.dumps(saved, ensure_ascii=False))

    async def test_previous_saved_duplicate_gaps_keep_their_original_text_and_identity(self):
        row = fixture('私は仕事を続けたいけれど、私はつらい。')['row']
        projection = row['content_json']['watashiMap']
        old_gaps = copy.deepcopy(projection['unknown_gaps'])
        projection['unknown_gaps'].extend(dict(g, gap_ref='g' + str(i))
                                         for i, g in enumerate(old_gaps, 5))
        lines = row['content_text'].splitlines()
        # Historical wire text: node, both sets of gaps, then the annotation.
        row['content_text'] = '\n'.join(lines[:-1] + lines[1:-1] + lines[-1:])
        before = copy.deepcopy(row)
        with patch.object(service, '_rpc', AsyncMock(return_value=result([row]))), \
                patch.object(MeaningExperienceEngine, 'generate', side_effect=AssertionError('regenerated')):
            saved = await service.read_saved(OWNER, report_id=row['id'], report_mode='standard')
        self.assertEqual(saved['items'][0], before)
        self.assertEqual(saved['items'][0]['content_text'].count('未確定（'), 8)
        self.assertEqual(row, before)

    async def test_burden_annotation_survives_save_and_read_without_regeneration(self):
        self.fx = fixture('私は仕事を続けたいけれど、私はつらい。')
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
            with patch.object(MeaningExperienceEngine, 'generate', side_effect=AssertionError('regenerated')):
                reread = await service.read_saved(OWNER, report_id=saved['id'], report_mode='standard')
        self.assertEqual(saved, reread['items'][0])
        self.assertEqual(saved['content_text'], writes[0]['p_text'])
        projection = saved['content_json']['watashiMap']
        self.assertEqual(projection, writes[0]['p_projection'])
        self.assertEqual(len(projection['annotation_badges']), 1)
        private = writes[0]['p_private_evidence']
        claim = private['graph']['annotations'][0]
        self.assertEqual(claim['target_ref'], projection['annotation_badges'][0]['target_ref'])
        self.assertEqual(claim['annotation_state'], 'SOURCE_EXPLICIT_ANNOTATION')
        self.assertEqual(len(claim['evidence_refs']), 3)
        for key in ('visible_label', 'source_labels', 'predicate_lemma', 'original_json', '私は', 'つらい', '仕事'):
            self.assertNotIn(key, json.dumps(private, ensure_ascii=False))
        for key in ('evidence_refs', 'source_envelope_id', 'literal_sha256', 'forbidden_promotions', 'annotation_state'):
            self.assertNotIn(key, json.dumps(saved, ensure_ascii=False))
        self.assertIn('注記（仕事を続けることへの希望）', saved['content_text'])

    async def test_saved_burden_rejects_invalid_shape_target_label_and_text(self):
        base = fixture('私は記録を残した。私は仕事を続けたいけれど、私はつらい。')['row']
        for mutation in ('unknown', 'action', 'edge', 'duplicate', 'kind', 'private', 'label', 'non_list', 'id', 'missing_text'):
            with self.subTest(mutation=mutation):
                row = copy.deepcopy(base)
                projection = row['content_json']['watashiMap']
                badge = projection['annotation_badges'][0]
                if mutation == 'unknown': badge['target_ref'] = 'n999'
                if mutation == 'action': badge['target_ref'] = 'n1'
                if mutation == 'edge': badge['target_ref'] = 'e1'
                if mutation == 'duplicate': projection['annotation_badges'].append(dict(badge, annotation_ref='a2'))
                if mutation == 'kind': badge['kind'] = 'PROTECTIVE'
                if mutation == 'private': badge['evidence_refs'] = ['private']
                if mutation == 'label': badge['visible_label'] = '仕事が原因でつらくなっています。'
                if mutation == 'non_list': projection['annotation_badges'] = {}
                if mutation == 'id': badge['annotation_ref'] = 'a0'
                if mutation == 'missing_text': row['content_text'] = row['content_text'].split('注記')[0]
                with patch.object(service, '_rpc', AsyncMock(return_value=result([row]))):
                    with self.assertRaises(HTTPException) as raised:
                        await service.read_saved(OWNER)
                self.assertEqual(raised.exception.status_code, 503)

    async def test_generate_commits_and_rereads_exact_identity(self):
        self.fx = fixture('私は、考えをノートに書いた。僕は，仕事を続けたい。')
        self.row = self.fx['row']
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
            with patch.object(MeaningExperienceEngine, 'generate', side_effect=AssertionError('regenerated')):
                reread = await service.read_saved(OWNER, report_id=saved['id'], report_mode='standard')
        self.assertEqual(reread['items'][0], saved)
        self.assertEqual(saved['content_json']['watashiMap'], writes[0]['p_projection'])
        self.assertEqual(saved['content_text'], writes[0]['p_text'])
        self.assertEqual([n['visible_label'] for n in saved['content_json']['watashiMap']['nodes']],
            ['考えをノートに書く（実行済み）', '仕事を続けることへの希望'])
        encoded = json.dumps(writes[0]['p_private_evidence'], ensure_ascii=False)
        self.assertNotIn('私は', encoded)
        self.assertNotIn('visible_label', encoded)
        self.assertNotIn('original_json', encoded)
        self.assertIn('evidence_refs', encoded)
        self.assertEqual(writes[0]['p_guard'], GUARD)

    async def test_saved_event_topic_commas_keep_scene_role_and_text_without_regeneration(self):
        fx = fixture('私は、職場にいた。僕は，今日、会議を担当しませんでした。')
        row = fx['row']
        with patch.object(service, '_rpc', AsyncMock(return_value=result([row]))), \
                patch.object(MeaningExperienceEngine, 'generate', side_effect=AssertionError('regenerated')):
            reread = await service.read_saved(OWNER)
        saved, = reread['items']
        self.assertEqual(saved['content_text'], row['content_text'])
        self.assertEqual(saved['content_json']['watashiMap'], row['content_json']['watashiMap'])
        self.assertEqual([n['visible_label'] for n in saved['content_json']['watashiMap']['nodes']],
            ['職場にいた（記録された場面）', 'この記述時点の今日：会議を担当しなかった（記録された担当）'])
        self.assertNotIn('私は', json.dumps(fx['private'], ensure_ascii=False))

    async def test_mixed_script_arguments_survive_save_and_read_without_regeneration(self):
        original = dict(self.fx['original'], memo=
            '私は、昨日、会議室ロビーにいた。その後、私は仕事メモをメモ帳に書かなかった。')
        writes = []
        async def rpc(name, payload):
            if name == 'analysis_observed_source_snapshot':
                return {'guard': GUARD, 'tier': 'plus', 'now': END, 'members': [
                    {'original': original, 'thread': None, 'events': []}]}
            if name == 'analysis_observed_commit':
                writes.append(payload)
                self.row.update(id=str(UUID(payload['p_artifact_id'][9:])), content_text=payload['p_text'])
                self.row['content_json']['watashiMap'] = payload['p_projection']
                return self.row['id']
            if name == 'analysis_observed_read':
                return result([self.row], matched=True)
            raise AssertionError(name)
        with patch.dict(os.environ, COCOLON_ANALYSIS_PERIOD_COMPARISON_MODE='off'), \
                patch.object(service, '_rpc', side_effect=rpc):
            saved = await service.generate_saved(OWNER, start=START, end=END,
                report_mode='standard', report_type='latest')
            with patch.object(MeaningExperienceEngine, 'generate', side_effect=AssertionError('regenerated')):
                reread = await service.read_saved(OWNER, report_id=saved['id'], report_mode='standard')
        self.assertEqual(len(writes), 1)
        self.assertEqual(reread['items'][0], saved)
        projection = saved['content_json']['watashiMap']
        self.assertEqual(projection, writes[0]['p_projection'])
        self.assertEqual(saved['content_text'], writes[0]['p_text'])
        self.assertEqual([n['visible_label'] for n in projection['nodes']], [
            'この記述時点の昨日：会議室ロビーにいた（記録された場面）',
            'その後：仕事メモをメモ帳に書く（行わなかった）'])
        self.assertEqual(len(projection['edges']), 1)
        self.assertNotIn('私は', json.dumps(writes[0]['p_private_evidence'], ensure_ascii=False))

    async def test_attributive_arguments_survive_save_and_read_without_regeneration(self):
        original = dict(self.fx['original'], memo=
            '私は、昨日、新しい会議室にいた。その後、私は詳しい仕事メモを古いノートに書かなかった。')
        writes = []
        async def rpc(name, payload):
            if name == 'analysis_observed_source_snapshot':
                return {'guard': GUARD, 'tier': 'plus', 'now': END, 'members': [
                    {'original': original, 'thread': None, 'events': []}]}
            if name == 'analysis_observed_commit':
                writes.append(payload)
                self.row.update(id=str(UUID(payload['p_artifact_id'][9:])), content_text=payload['p_text'])
                self.row['content_json']['watashiMap'] = payload['p_projection']
                return self.row['id']
            if name == 'analysis_observed_read':
                return result([self.row], matched=True)
            raise AssertionError(name)
        with patch.dict(os.environ, COCOLON_ANALYSIS_PERIOD_COMPARISON_MODE='off'), \
                patch.object(service, '_rpc', side_effect=rpc):
            saved = await service.generate_saved(OWNER, start=START, end=END,
                report_mode='standard', report_type='latest')
            with patch.object(MeaningExperienceEngine, 'generate', side_effect=AssertionError('regenerated')):
                reread = await service.read_saved(OWNER, report_id=saved['id'], report_mode='standard')
        self.assertEqual(len(writes), 1)
        self.assertEqual(reread['items'][0], saved)
        projection = saved['content_json']['watashiMap']
        self.assertEqual(projection, writes[0]['p_projection'])
        self.assertEqual(saved['content_text'], writes[0]['p_text'])
        self.assertEqual([n['visible_label'] for n in projection['nodes']], [
            'この記述時点の昨日：新しい会議室にいた（記録された場面）',
            'その後：詳しい仕事メモを古いノートに書く（行わなかった）'])
        self.assertEqual(len(projection['edges']), 1)
        self.assertNotIn('私は', json.dumps(writes[0]['p_private_evidence'], ensure_ascii=False))

    async def test_kana_compound_arguments_survive_save_and_read_without_regeneration(self):
        original = dict(self.fx['original'], memo=
            '私は、昨日、新しい会議室にいた。その後、私は新しい振り返りメモを古い学びノートに書かなかった。')
        writes = []
        async def rpc(name, payload):
            if name == 'analysis_observed_source_snapshot':
                return {'guard': GUARD, 'tier': 'plus', 'now': END, 'members': [
                    {'original': original, 'thread': None, 'events': []}]}
            if name == 'analysis_observed_commit':
                writes.append(payload)
                self.row.update(id=str(UUID(payload['p_artifact_id'][9:])), content_text=payload['p_text'])
                self.row['content_json']['watashiMap'] = payload['p_projection']
                return self.row['id']
            if name == 'analysis_observed_read':
                return result([self.row], matched=True)
            raise AssertionError(name)
        with patch.dict(os.environ, COCOLON_ANALYSIS_PERIOD_COMPARISON_MODE='off'), \
                patch.object(service, '_rpc', side_effect=rpc):
            saved = await service.generate_saved(OWNER, start=START, end=END,
                report_mode='standard', report_type='latest')
            with patch.object(MeaningExperienceEngine, 'generate', side_effect=AssertionError('regenerated')):
                reread = await service.read_saved(OWNER, report_id=saved['id'], report_mode='standard')
        self.assertEqual(len(writes), 1)
        self.assertEqual(reread['items'][0], saved)
        projection = saved['content_json']['watashiMap']
        self.assertEqual(projection, writes[0]['p_projection'])
        self.assertEqual(saved['content_text'], writes[0]['p_text'])
        self.assertEqual([n['visible_label'] for n in projection['nodes']], [
            'この記述時点の昨日：新しい会議室にいた（記録された場面）',
            'その後：新しい振り返りメモを古い学びノートに書く（行わなかった）'])
        self.assertEqual(len(projection['edges']), 1)
        self.assertNotIn('私は', json.dumps(writes[0]['p_private_evidence'], ensure_ascii=False))

    async def test_feeling_word_changes_survive_save_and_read_without_regeneration(self):
        original = dict(self.fx['original'], memo=
            '私は資料を調べた後、不安が減った。私は記録を残してから、気持ちメモが増えた。'
            '私は振り返りメモを残した後、取り組み方が変わりました。')
        writes = []
        async def rpc(name, payload):
            if name == 'analysis_observed_source_snapshot':
                return {'guard': GUARD, 'tier': 'plus', 'now': END, 'members': [
                    {'original': original, 'thread': None, 'events': []}]}
            if name == 'analysis_observed_commit':
                writes.append(payload)
                self.row.update(id=str(UUID(payload['p_artifact_id'][9:])), content_text=payload['p_text'])
                self.row['content_json']['watashiMap'] = payload['p_projection']
                return self.row['id']
            if name == 'analysis_observed_read':
                return result([self.row], matched=True)
            raise AssertionError(name)
        with patch.dict(os.environ, COCOLON_ANALYSIS_PERIOD_COMPARISON_MODE='off'), \
                patch.object(service, '_rpc', side_effect=rpc):
            saved = await service.generate_saved(OWNER, start=START, end=END,
                report_mode='standard', report_type='latest')
            with patch.object(MeaningExperienceEngine, 'generate', side_effect=AssertionError('regenerated')):
                reread = await service.read_saved(OWNER, report_id=saved['id'], report_mode='standard')
        self.assertEqual(len(writes), 1)
        self.assertEqual(reread['items'][0], saved)
        projection = saved['content_json']['watashiMap']
        self.assertEqual(projection, writes[0]['p_projection'])
        self.assertEqual(saved['content_text'], writes[0]['p_text'])
        self.assertEqual([n['visible_label'] for n in projection['nodes']], [
            '資料を調べる（実行済み）', '不安が減った（記録された変化）',
            '記録を残す（実行済み）', '気持ちメモが増えた（記録された変化）',
            '振り返りメモを残す（実行済み）', '取り組み方が変わった（記録された変化）'])
        self.assertEqual([e['edge_kind'] for e in projection['edges']],
            ['OBSERVED_ORDER', 'OBSERVED_ORDER', 'OBSERVED_ORDER'])
        self.assertNotIn('私は', json.dumps(writes[0]['p_private_evidence'], ensure_ascii=False))

    async def test_partial_map_with_unparsed_original_is_saved_and_read_without_regeneration(self):
        original = dict(self.fx['original'], memo='私は資料を明日ノートに書いた。私は記録を残した。')
        writes = []
        async def rpc(name, payload):
            if name == 'analysis_observed_source_snapshot':
                return {'guard': GUARD, 'tier': 'plus', 'now': END, 'members': [
                    {'original': original, 'thread': None, 'events': []}]}
            if name == 'analysis_observed_commit':
                writes.append(payload)
                self.row.update(id=str(UUID(payload['p_artifact_id'][9:])), content_text=payload['p_text'])
                self.row['content_json']['watashiMap'] = payload['p_projection']
                return self.row['id']
            if name == 'analysis_observed_read':
                return result([self.row], matched=True)
            raise AssertionError(name)
        with patch.dict(os.environ, COCOLON_ANALYSIS_PERIOD_COMPARISON_MODE='off'), \
                patch.object(service, '_rpc', side_effect=rpc):
            saved = await service.generate_saved(OWNER, start=START, end=END,
                report_mode='standard', report_type='latest')
            with patch.object(MeaningExperienceEngine, 'generate', side_effect=AssertionError('regenerated')):
                reread = await service.read_saved(OWNER, report_id=saved['id'], report_mode='standard')
        self.assertEqual(len(writes), 1)
        self.assertEqual(reread['items'][0], saved)
        projection = saved['content_json']['watashiMap']
        self.assertEqual([n['visible_label'] for n in projection['nodes']], ['記録を残す（実行済み）'])
        self.assertTrue(any('まだ読み取れていない内容' in g['visible_label']
                            for g in projection['unknown_gaps']))
        self.assertEqual(saved['content_text'], writes[0]['p_text'])
        self.assertNotIn('明日ノート', json.dumps(saved, ensure_ascii=False))
        self.assertNotIn('私は', json.dumps(writes[0]['p_private_evidence'], ensure_ascii=False))

    async def test_opposed_claims_survive_save_read_with_private_evidence_only(self):
        self.fx = fixture('私は資料を調べた。私は資料を調べなかった。')
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
            with patch.object(MeaningExperienceEngine, 'generate', side_effect=AssertionError('regenerated')):
                reread = await service.read_saved(OWNER, report_id=saved['id'], report_mode='standard')
        self.assertEqual(saved, reread['items'][0])
        self.assertEqual(saved['content_text'], writes[0]['p_text'])
        projection = saved['content_json']['watashiMap']
        self.assertEqual(projection, writes[0]['p_projection'])
        self.assertEqual(len(projection['conflict_badges']), 1)
        private = writes[0]['p_private_evidence']
        conflict = private['graph']['conflicts'][0]
        self.assertEqual(conflict['target_refs'], tuple(projection['conflict_badges'][0]['target_refs']))
        self.assertEqual(len(conflict['evidence_refs']), 2)
        encoded_private = json.dumps(private, ensure_ascii=False)
        encoded_safe = json.dumps(saved, ensure_ascii=False)
        for key in ('visible_label', 'original_json', '私は', '資料', 'proposition'):
            self.assertNotIn(key, encoded_private)
        for key in ('evidence_refs', 'source_envelope_id', 'literal_sha256', 'OPPOSING_POLARITY'):
            self.assertNotIn(key, encoded_safe)
        self.assertIn('同じ機会のことかは確定していません', saved['content_text'])

    async def test_saved_conflict_rejects_invalid_targets_shape_and_text(self):
        base = fixture('私は資料を調べた。私は資料を調べなかった。')['row']
        for mutation in ('unknown', 'same', 'duplicate', 'private', 'label', 'non_list', 'missing_text'):
            with self.subTest(mutation=mutation):
                row = copy.deepcopy(base)
                projection = row['content_json']['watashiMap']
                badge = projection['conflict_badges'][0]
                if mutation == 'unknown': badge['target_refs'][1] = 'n999'
                if mutation == 'same': badge['target_refs'][1] = badge['target_refs'][0]
                if mutation == 'duplicate':
                    projection['conflict_badges'].append(dict(badge, conflict_ref='c2'))
                if mutation == 'private': badge['evidence_refs'] = ['private']
                if mutation == 'label': badge['visible_label'] = 'どちらかの記述は誤りです。'
                if mutation == 'non_list': projection['conflict_badges'] = {}
                if mutation == 'missing_text': row['content_text'] = row['content_text'].split('一致していない記録')[0]
                with patch.object(service, '_rpc', AsyncMock(return_value=result([row]))):
                    with self.assertRaises(HTTPException) as raised:
                        await service.read_saved(OWNER)
                self.assertEqual(raised.exception.status_code, 503)

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

    async def test_saved_cognition_keeps_uncertainty_without_private_content(self):
        for topic in ('私は', '私は、', '僕は,'):
            with self.subTest(topic=topic):
                fx = fixture('私は記録を残した。' + topic + '資料を調べなかったかもしれないと思っている。')
                row = fx['row']
                writes = []
                async def rpc(name, payload):
                    if name == 'analysis_observed_source_snapshot':
                        return {'guard': GUARD, 'tier': 'plus', 'now': END, 'members': [
                            {'original': fx['original'], 'thread': None, 'events': []}]}
                    if name == 'analysis_observed_commit':
                        writes.append(payload)
                        row['id'] = str(UUID(payload['p_artifact_id'][9:]))
                        row['content_text'] = payload['p_text']
                        row['content_json']['watashiMap'] = payload['p_projection']
                        return row['id']
                    if name == 'analysis_observed_read':
                        return result([row], matched=True)
                    raise AssertionError(name)
                with patch.dict(os.environ, COCOLON_ANALYSIS_PERIOD_COMPARISON_MODE='off'), \
                     patch.object(service, '_rpc', side_effect=rpc):
                    saved = await service.generate_saved(OWNER, start=START, end=END,
                        report_mode='standard', report_type='latest')
                    with patch.object(MeaningExperienceEngine, 'generate', side_effect=AssertionError('read regenerated')):
                        value = await service.read_saved(OWNER)
                self.assertEqual(value['items'][0], saved)
                self.assertEqual(saved, row)
                self.assertEqual(len(writes), 1)
                projection = saved['content_json']['watashiMap']
                self.assertEqual(projection, writes[0]['p_projection'])
                self.assertEqual(saved['content_text'], writes[0]['p_text'])
                thought = next(n for n in projection['nodes'] if n['node_kind'] == 'ATTENTION_OR_THOUGHT')
                self.assertEqual(thought['visible_label'], '資料を調べなかったかもしれないと思っている（この記述時点の考え）')
                self.assertIn(thought['visible_label'], saved['content_text'])
                self.assertFalse(projection['edges'])
                for value in (fx['private'], writes[0]['p_private_evidence'], projection):
                    encoded = json.dumps(value, ensure_ascii=False)
                    for private in ('possible_content', 'source_parts', 'UNSPECIFIED', '私は', '僕は'):
                        self.assertNotIn(private, encoded)

    async def test_unfinished_result_survives_commit_and_read_without_regeneration(self):
        self.fx = fixture('私は資料を調べた。まだ方法が見つかっていない。')
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
            with patch.object(MeaningExperienceEngine, 'generate', side_effect=AssertionError('read regenerated')):
                reread = await service.read_saved(OWNER)
        self.assertEqual(reread['items'][0], saved)
        projection = saved['content_json']['watashiMap']
        self.assertEqual(projection, writes[0]['p_projection'])
        self.assertEqual(saved['content_text'], writes[0]['p_text'])
        result_node = next(n for n in projection['nodes'] if n['node_kind'] == 'IMMEDIATE_RESULT_OR_AFTERMATH')
        self.assertEqual(result_node['visible_label'], 'まだ方法が見つかっていない（この記述時点）')
        self.assertIn(result_node['visible_label'], saved['content_text'])
        self.assertFalse(projection['edges'])
        for encoded in (json.dumps(writes[0]['p_private_evidence'], ensure_ascii=False),
                        json.dumps(projection, ensure_ascii=False)):
            for private in ('result_state', 'NOT_YET', 'UNSPECIFIED', 'source_parts'):
                self.assertNotIn(private, encoded)

    async def test_action_change_order_survives_commit_and_read_without_regeneration(self):
        await self._assert_action_change_saved('私は資料を調べた後、疑問が減った。')

    async def test_te_after_change_survives_commit_and_read_without_regeneration(self):
        for memo in ('私は資料を調べてから、疑問が減った。',
                     '私は、資料を調べてから、疑問が減った。'):
            with self.subTest(memo=memo):
                await self._assert_action_change_saved(memo)

    async def test_polite_decrease_increase_return_survive_save_and_read(self):
        for clause, plain in (('不安が減りました', '不安が減った'),
                              ('気持ちメモが増えました', '気持ちメモが増えた'),
                              ('資料が戻りました', '資料が戻った')):
            with self.subTest(clause=clause):
                for action in ('私は資料を調べた後、', '私は、資料を調べた後、',
                               '僕は，　資料を調べてから、'):
                    with self.subTest(action=action):
                        await self._assert_action_change_saved(action + clause + '。',
                            plain + '（記録された変化）')

    async def test_past_feeling_survives_commit_and_read_without_regeneration(self):
        for memo, label in (('私は資料を調べた後、安心した。', '安心した（記録された気持ち）'),
                ('私は資料を調べてから、落ち着いた。', '落ち着いた（記録された気持ち）'),
                ('私は、資料を調べてから、安心した。', '安心した（記録された気持ち）'),
                ('私は資料を調べた後、私は、安心しました。', '安心した（記録された気持ち）'),
                ('私は、資料を調べてから、僕は， 落ち着いた。', '落ち着いた（記録された気持ち）'),
                ('私は記録を残した後、わたしは、　嬉しかった。', '嬉しかった（記録された気持ち）')):
            with self.subTest(memo=memo):
                await self._assert_action_change_saved(memo, label)

    async def _assert_action_change_saved(self, memo, expected_label='疑問が減った（記録された変化）'):
        self.fx = fixture(memo)
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
            with patch.object(MeaningExperienceEngine, 'generate', side_effect=AssertionError('read regenerated')):
                reread = await service.read_saved(OWNER)
        self.assertEqual(reread['items'][0], saved)
        projection = saved['content_json']['watashiMap']
        self.assertEqual(projection, writes[0]['p_projection'])
        self.assertEqual(saved['content_text'], writes[0]['p_text'])
        action, change = projection['nodes']
        edge, = projection['edges']
        self.assertEqual((edge['edge_kind'], edge['from_ref'], edge['to_ref']),
                         ('OBSERVED_ORDER', action['node_ref'], change['node_ref']))
        self.assertEqual(change['visible_label'], expected_label)
        self.assertIn(change['visible_label'], saved['content_text'])
        for encoded in (json.dumps(writes[0]['p_private_evidence'], ensure_ascii=False),
                        json.dumps(projection, ensure_ascii=False)):
            for private in ('result_state', 'BOUNDED_CHANGE', 'PAST_FEELING', 'source_parts', '私は',
                            'action_supports_change', 'dependent_form', 'TE_BEFORE_PAST_CHANGE'):
                self.assertNotIn(private, encoded)

    async def test_scene_and_role_polarity_and_action_order_survive_save_and_read(self):
        for clause, kind, label in (
                ('私は職場にいました', 'SCENE', '職場にいた（記録された場面）'),
                ('私は職場にいませんでした', 'SCENE', '職場にいなかった（記録された場面）'),
                ('私は会議の司会を担当しました', 'ROLE', '会議の司会を担当した（記録された担当）'),
                ('私は会議の司会を担当しませんでした', 'ROLE', '会議の司会を担当しなかった（記録された担当）'),
                ('今日私は職場にいました', 'SCENE', 'この記述時点の今日：職場にいた（記録された場面）'),
                ('昨日私は職場にいませんでした', 'SCENE', 'この記述時点の昨日：職場にいなかった（記録された場面）'),
                ('その後私は会議の司会を担当しました', 'ROLE', 'その後：会議の司会を担当した（記録された担当）'),
                ('それから私は会議の司会を担当しませんでした', 'ROLE', 'それから：会議の司会を担当しなかった（記録された担当）')):
            with self.subTest(clause=clause):
                self.fx = fixture(clause + '。その後、私は資料を調べた。')
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
                    with patch.object(MeaningExperienceEngine, 'generate', side_effect=AssertionError('read regenerated')):
                        reread = await service.read_saved(OWNER)
                self.assertEqual(reread['items'][0], saved)
                projection = saved['content_json']['watashiMap']
                self.assertEqual((projection, saved['content_text']), (writes[0]['p_projection'], writes[0]['p_text']))
                context_node, action = projection['nodes']
                self.assertEqual((context_node['node_kind'], context_node['visible_label']), (kind, label))
                self.assertIn(label, saved['content_text'])
                edge, = projection['edges']
                self.assertEqual((edge['edge_kind'], edge['from_ref'], edge['to_ref']),
                    ('OBSERVED_ORDER', context_node['node_ref'], action['node_ref']))
                for encoded in (json.dumps(writes[0]['p_private_evidence'], ensure_ascii=False),
                                json.dumps(projection, ensure_ascii=False)):
                    for private in ('scene_state', 'PAST_PRESENCE', 'role_state', 'PAST_RESPONSIBILITY', 'source_parts', '私は'):
                        self.assertNotIn(private, encoded)

    async def test_saved_scene_role_action_chain_is_read_without_reinterpretation(self):
        fx = fixture('今日私は職場にいた。その後私は会議の司会を担当した。'
                     'それから私は資料を調べた。')
        with patch.object(service, '_rpc', AsyncMock(return_value=result([fx['row']]))), \
             patch.object(MeaningExperienceEngine, 'generate', side_effect=AssertionError('read regenerated')):
            value = await service.read_saved(OWNER)
        self.assertEqual(value['items'][0], fx['row'])
        p = value['items'][0]['content_json']['watashiMap']
        self.assertEqual([n['node_kind'] for n in p['nodes']], ['SCENE', 'ROLE', 'ACTION_OR_NONACTION'])
        self.assertEqual([(e['from_ref'], e['to_ref']) for e in p['edges']], [('n1', 'n2'), ('n2', 'n3')])
        for n in p['nodes']:
            self.assertIn(n['visible_label'], value['items'][0]['content_text'])

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
