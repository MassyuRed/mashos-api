"""Synthetic DB responses through real saved-source, CMEE and ASTOR code.

No live account/input is read, no table/route is activated, no write is mocked
as successful. Only the existing auth, entitlement and HTTP/RPC I/O are faked.
"""
import copy
from dataclasses import asdict
from datetime import datetime, timezone
import json
import sys
import types
import unittest
from unittest.mock import AsyncMock, patch
from uuid import UUID

import httpx
from fastapi import HTTPException
import astor_material_snapshots as material
from astor_self_structure_report import prepare_saved_analysis_observed_map
from cocolon_meaning_experience_engine.contracts import GenerationRequest
from cocolon_meaning_experience_engine.source_kernel import freeze_text_source
from cocolon_meaning_experience_engine.emlis_thread_contracts import (
    EmlisClarificationV1, EmlisQuestionDecisionV1, SupplementalAnswerSource,
)
from cocolon_meaning_experience_engine.cores.analysis.source_adapter import (
    commitment, freeze_analysis_sources,
)
from emlis_ai_current_input_bundle import build_emlis_current_input_bundle
from emlis_thread_store import ThreadStoreError
from subscription import SubscriptionTier

OWNER = str(UUID(int=1))
OTHER = str(UUID(int=2))
START, END = '2026-10-01T00:00:00Z', '2026-10-03T00:00:00Z'
NOW = '2026-10-03T12:00:00+00:00'
TEXT = '私は考えをノートに書いた。私は仕事を続けたい。'


class Clock(datetime):
    @classmethod
    def now(cls, tz=None):
        return datetime.fromisoformat(NOW).astimezone(tz or timezone.utc)


def original(number=1):
    return {'id': str(UUID(int=100 + number)), 'created_at': f'2026-10-0{number}T01:00:00',
            'memo': TEXT, 'memo_action': '', 'category': ['仕事'], 'emotions': ['平穏'],
            'emotion_details': [{'type': '平穏', 'strength': 'medium'}]}


def snapshot(number=1):
    return {'original': original(number), 'tier': 'plus', 'now': NOW, 'thread': None, 'events': []}


def with_answer(saved, text='「私は考えをノートに書いた」ではなく「私は考えをノートに書かなかった」です。'):
    saved = copy.deepcopy(saved)
    source = dict(saved['original'])
    source['created_at'] = source['created_at'] + '+00:00'
    tid, qid, aid = str(UUID(int=201)), 'synthetic-question', str(UUID(int=203))
    request = GenerationRequest('synthetic-emlis', build_emlis_current_input_bundle(source), source['id'])
    ref = freeze_text_source(request).envelope.envelope_id
    question = EmlisClarificationV1(qid, request.request_id, tid, ref,
        EmlisQuestionDecisionV1('ASK', target_ref='synthetic-target'), 'QUESTION_IS_NOT_ANALYSIS_SOURCE')
    answer = SupplementalAnswerSource(aid, tid, qid, 1, ref, text, NOW)
    saved['thread'] = {'id': tid, 'user_id': OWNER, 'original_emotion_id': source['id'],
        'source_snapshot': copy.deepcopy(saved['original']), 'revision': 3, 'issued_count': 1,
        'data': {'runtime_profile': 'q2.free.one_round.v1', 'original_source_ref': ref}}
    saved['events'] = [
        {'id': str(UUID(int=202)), 'thread_id': tid, 'kind': 'QUESTION', 'question_id': qid,
         'round_index': 1, 'payload': asdict(question)},
        {'id': aid, 'thread_id': tid, 'kind': 'ANSWER', 'question_id': qid,
         'round_index': 1, 'payload': {'source': asdict(answer)}},
        {'id': str(UUID(int=204)), 'thread_id': tid, 'kind': 'OBSERVATION',
         'payload': {'text': 'GENERATED_BODY_IS_NOT_SOURCE'}},
    ]
    return saved


class SavedPeriodTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.rows = {s['original']['id']: s for s in [snapshot(1), snapshot(2)]}
        self.ids = list(self.rows)
        self.tier = SubscriptionTier.PLUS
        self.scans = 0
        self.on_scan = None
        self.range_override = None
        self.read_calls = []
        self.period_ids = None
        self.auth = AsyncMock(return_value=OWNER)
        async def tier(user_id, **kwargs):
            self.assertEqual(user_id, OWNER)
            return self.tier
        auth_module = types.ModuleType('api_account_visibility')
        auth_module._require_user_id = self.auth
        tier_module = types.ModuleType('subscription_store')
        tier_module.get_subscription_tier_for_user = tier
        self.enterContext(patch.dict(sys.modules, {
            'api_account_visibility': auth_module, 'subscription_store': tier_module,
        }))
        self.enterContext(patch.object(material, 'datetime', Clock))
        self.enterContext(patch('supabase_client.sb_get', side_effect=self.get_ids))
        self.enterContext(patch('emlis_thread_store.EmlisThreadStore.read', side_effect=self.read))

    async def get_ids(self, path, *, params, prefer, timeout):
        self.assertEqual(path, '/rest/v1/emotions')
        self.assertEqual(params['select'], 'id')
        self.assertEqual(params['user_id'], 'eq.' + OWNER)
        self.assertEqual(params['order'], 'created_at.asc,id.asc')
        self.assertEqual(params['limit'], '101')
        if self.period_ids is None:
            self.assertEqual(params['and'], '(created_at.gte.2026-10-01T00:00:00+00:00,created_at.lt.2026-10-03T00:00:00+00:00)')
        else:
            self.assertIn(params['and'], self.period_ids)
        self.assertEqual(prefer, 'count=exact')
        self.scans += 1
        if self.on_scan:
            self.on_scan(self.scans)
        ids = self.ids if self.period_ids is None else self.period_ids[params['and']]
        count = len(ids)
        return httpx.Response(200, json=[{'id': i} for i in ids], headers={
            'content-range': self.range_override if self.range_override is not None else f'0-{max(0, count-1)}/{count}',
        })

    async def read(self, owner, *, input_id):
        self.assertEqual(owner, OWNER)
        self.read_calls.append(input_id)
        if input_id not in self.rows:
            raise ThreadStoreError('thread_unavailable', 404)
        return copy.deepcopy(self.rows[input_id])

    async def load(self, **kwargs):
        args = dict(period_start=START, period_end=END, report_mode='standard')
        args.update(kwargs)
        return await material.load_analysis_saved_period('Bearer synthetic', **args)

    async def generate(self, **kwargs):
        args = dict(period_start=START, period_end=END, report_mode='standard')
        args.update(kwargs)
        return await prepare_saved_analysis_observed_map('Bearer synthetic', **args)

    async def test_saved_timestamp_and_exact_raw_commitment_are_preserved(self):
        saved = await self.load()
        self.assertEqual(saved.request.members[0].original_json, json.dumps(original(), ensure_ascii=False, sort_keys=True, separators=(',', ':')))
        self.assertEqual(saved.request.members[0].saved_record_version, commitment(original()))
        frozen = freeze_analysis_sources(saved.request)
        self.assertEqual(len(frozen.sources), 2)
        self.assertEqual(frozen.period, ('2026-10-01T00:00:00+00:00', '2026-10-03T00:00:00+00:00'))
        self.assertNotIn(TEXT, repr(saved))

    async def test_saved_records_generate_matching_safe_map_and_text(self):
        result = await self.generate()
        self.assertEqual(result['status'], 'GENERATED')
        self.assertEqual(result['meta']['wire_kind'], 'watashi.map.v2')
        self.assertEqual([n['evidence_badge_count'] for n in result['meta']['nodes']], [2, 2])
        self.assertEqual(result['meta']['edges'][0]['edge_kind'], 'REPEATED_COOCCURRENCE')
        for node in result['meta']['nodes']:
            self.assertIn(node['visible_label'], result['content_text'])
        body = json.dumps(result, ensure_ascii=False)
        for private in [TEXT, OWNER, *self.ids, 'source_guards', 'source_set_ref', 'evidence_refs']:
            self.assertNotIn(private, body)
        self.assertEqual(self.scans, 2)
        self.assertEqual(self.auth.await_count, 2)

    def setup_previous_period(self):
        before = snapshot(3)
        before['original']['created_at'] = '2026-09-30T01:00:00'
        before['original']['memo'] = '私は家族を守りたい。'
        old_id = before['original']['id']
        self.rows[old_id] = before
        self.period_ids = {
            '(created_at.gte.2026-10-01T00:00:00+00:00,created_at.lt.2026-10-03T00:00:00+00:00)': self.ids,
            '(created_at.gte.2026-09-29T00:00:00+00:00,created_at.lt.2026-10-01T00:00:00+00:00)': [old_id],
        }
        return old_id, dict(previous_period_start='2026-09-29T00:00:00Z', previous_period_end=START)

    async def test_comparison_preview_loads_and_rechecks_both_authenticated_periods(self):
        old_id, bounds = self.setup_previous_period()
        result = await self.generate(**bounds)
        self.assertEqual(result['status'], 'GENERATED', result)
        self.assertEqual(result['meta']['period_comparison']['state'], 'COMPARABLE')
        self.assertIn('期間比較：', result['content_text'])
        self.assertEqual((self.scans, self.auth.await_count), (4, 4))
        self.assertEqual(self.read_calls.count(old_id), 2)
        self.assertEqual(set(self.read_calls), set(self.rows))
        public = json.dumps(result, ensure_ascii=False)
        for private in (old_id, OWNER, 'source_set_ref', 'previous_artifact', 'comparison_id', 'evidence_refs'):
            self.assertNotIn(private, public)

    async def test_comparison_preview_rejects_changed_previous_source_and_access(self):
        for mutation in ('edited', 'deleted', 'added', 'answer', 'tier', 'current_edited'):
            with self.subTest(mutation=mutation):
                self.rows = {s['original']['id']: s for s in (snapshot(1), snapshot(2))}
                self.ids = list(self.rows)
                self.scans, self.tier = 0, SubscriptionTier.PLUS
                old_id, bounds = self.setup_previous_period()
                def change(scan):
                    if mutation == 'current_edited':
                        if scan == 3: self.rows[self.ids[0]]['original']['memo'] = '私は生活を守りたい。'
                        return
                    if scan != 4: return
                    previous_ids = list(self.period_ids.values())[1]
                    if mutation == 'edited': self.rows[old_id]['original']['memo'] = '私は生活を守りたい。'
                    if mutation == 'deleted': previous_ids.clear()
                    if mutation == 'added': previous_ids.append(str(UUID(int=999)))
                    if mutation == 'answer': self.rows[old_id] = with_answer(self.rows[old_id], '私は生活を守りたい。')
                    if mutation == 'tier':
                        self.tier = SubscriptionTier.FREE
                        for row in self.rows.values(): row['tier'] = 'free'
                self.on_scan = change
                result = await self.generate(**bounds)
                self.assertEqual(result['status'], 'UNAVAILABLE', result)
                self.assertNotIn('meta', result)
                self.assertNotIn('content_text', result)
        self.on_scan = None

    async def test_comparison_preview_requires_complete_bounds_and_previous_access(self):
        self.assertEqual((await self.generate(previous_period_start=START))['reason_codes'],
                         ['analysis_comparison_period_incomplete'])
        self.assertEqual(self.scans, 0)
        _, bounds = self.setup_previous_period()
        bounds['previous_period_start'] = '2024-01-01T00:00:00Z'
        self.assertEqual((await self.generate(**bounds))['reason_codes'], ['analysis_period_not_retained'])

    async def test_saved_answer_updates_meaning_without_question_or_generated_body(self):
        self.rows[self.ids[0]] = with_answer(self.rows[self.ids[0]])
        result = await self.generate()
        self.assertEqual(result['status'], 'GENERATED', result)
        body = json.dumps(result, ensure_ascii=False)
        self.assertIn('考えをノートに書く（行わなかった）', body)
        self.assertNotIn('QUESTION_IS_NOT_ANALYSIS_SOURCE', body)
        self.assertNotIn('GENERATED_BODY_IS_NOT_SOURCE', body)

    async def test_old_answer_cannot_survive_parent_edit(self):
        saved = with_answer(self.rows[self.ids[0]])
        saved['original']['memo'] = '私は資料を調べた。'
        self.rows[self.ids[0]] = saved
        self.assertEqual((await self.generate())['status'], 'UNAVAILABLE')

    async def test_auth_failure_never_reads_a_period(self):
        self.auth.side_effect = HTTPException(401, 'private token detail')
        result = await self.generate()
        self.assertEqual(result, {'status': 'UNAVAILABLE', 'reason_codes': ['analysis_auth_unavailable']})
        self.assertEqual(self.scans, 0)

    async def test_plan_and_requested_mode_are_enforced_before_read(self):
        for tier, mode in [(SubscriptionTier.FREE, 'standard'), (SubscriptionTier.PLUS, 'deep'), (SubscriptionTier.PLUS, 'unknown')]:
            self.tier = tier
            result = await self.generate(report_mode=mode)
            self.assertEqual(result['reason_codes'], ['analysis_report_mode_unavailable'])
        self.assertEqual(self.scans, 0)
        self.tier = SubscriptionTier.FREE
        for row in self.rows.values(): row['tier'] = 'free'
        self.assertEqual((await self.generate(report_mode='light'))['status'], 'GENERATED')

    async def test_invalid_future_or_unretained_interval_is_not_silently_clipped(self):
        for start, end in [(END, START), ('2026-10-01T00:00:00', END), (START, '2027-01-01T00:00:00Z'), ('2024-01-01T00:00:00Z', END)]:
            self.assertEqual((await self.generate(period_start=start, period_end=end))['status'], 'UNAVAILABLE')
        self.assertEqual(self.scans, 0)

    async def test_period_limit_incomplete_count_and_duplicate_ids_are_rejected(self):
        for content_range in ['0-1/101', '0-1/3', '0-1/*', '']:
            self.range_override = content_range
            self.assertEqual((await self.generate())['status'], 'UNAVAILABLE')
        self.range_override = None
        self.ids.append(self.ids[0])
        self.assertEqual((await self.generate())['status'], 'UNAVAILABLE')
        self.assertEqual(self.read_calls, [])

    async def test_missing_record_wrong_owner_or_wrong_identity_are_rejected(self):
        old = copy.deepcopy(self.rows)
        del self.rows[self.ids[0]]
        self.assertEqual((await self.generate())['status'], 'UNAVAILABLE')
        self.rows = copy.deepcopy(old)
        self.rows[self.ids[0]] = with_answer(self.rows[self.ids[0]])
        self.rows[self.ids[0]]['thread']['user_id'] = OTHER
        self.assertEqual((await self.generate())['status'], 'UNAVAILABLE')
        self.rows = copy.deepcopy(old)
        self.rows[self.ids[0]]['original']['id'] = OTHER
        self.assertEqual((await self.generate())['status'], 'UNAVAILABLE')

    async def test_answer_binding_and_multiple_answers_fail_closed(self):
        for change in ['answer_id', 'question_id', 'round_index', 'multiple']:
            saved = with_answer(snapshot())
            answer = saved['events'][1]
            if change == 'multiple': saved['events'].append(copy.deepcopy(answer))
            elif change == 'round_index': answer['payload']['source'][change] = 2
            else: answer['payload']['source'][change] = 'other-binding'
            self.rows[self.ids[0]] = saved
            self.assertEqual((await self.generate())['status'], 'UNAVAILABLE')

    async def test_unsupported_semantics_do_not_fall_back_to_old_report(self):
        self.rows[self.ids[0]] = with_answer(snapshot(), 'それは大切です。')
        with patch('astor_self_structure_report.build_myprofile_monthly_report', side_effect=AssertionError('V1 fallback')):
            result = await self.generate()
        self.assertEqual(result['status'], 'UNAVAILABLE')
        self.assertNotIn('content_text', result)

    async def test_question_payload_must_bind_to_the_saved_question_row(self):
        for field, value in [('question_id', 'other-question'), ('thread_id', OTHER), ('round_index', 2)]:
            with self.subTest(field=field):
                saved = with_answer(snapshot())
                saved['events'][0][field] = value
                self.rows[self.ids[0]] = saved
                self.assertEqual((await self.generate())['status'], 'UNAVAILABLE')

    async def test_generation_rechecks_cohort_record_answer_metadata_and_tier(self):
        for mutation in ['added', 'deleted', 'edited', 'revision', 'answer_time', 'tier']:
            with self.subTest(mutation=mutation):
                self.rows = {s['original']['id']: s for s in [with_answer(snapshot()), snapshot(2)]}
                self.ids = list(self.rows)
                self.tier, self.scans = SubscriptionTier.PLUS, 0
                def change(scan):
                    if scan != 2: return
                    row = self.rows[self.ids[0]]
                    if mutation == 'added': self.ids.append(str(UUID(int=999)))
                    if mutation == 'deleted': self.ids.pop()
                    if mutation == 'edited': row['original']['memo'] = '私は資料を調べた。'
                    if mutation == 'revision': row['thread']['revision'] += 1
                    if mutation == 'answer_time': row['events'][1]['payload']['source']['recorded_at'] = '2026-10-03T11:00:00+00:00'
                    if mutation == 'tier':
                        self.tier = SubscriptionTier.FREE
                        for snapshot_row in self.rows.values(): snapshot_row['tier'] = 'free'
                self.on_scan = change
                result = await self.generate()
                self.assertEqual(result['status'], 'UNAVAILABLE')
                self.assertNotIn('meta', result)
        self.on_scan = None


if __name__ == '__main__':
    unittest.main()
