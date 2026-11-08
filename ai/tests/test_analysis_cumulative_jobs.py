"""Existing input/worker/cron callers must not write the withdrawn period map."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import os
import unittest
from unittest.mock import AsyncMock, patch
from uuid import UUID

import analysis_cumulative_service as cumulative
import astor_self_structure_report as refresher
import api_emotion_submit as submit
import api_cron_distribution as cron
import astor_worker as worker
import astor_job_queue as queue
import fcm_push_queue as push_queue

OWNER = '00000000-0000-0000-0000-000000000001'


def response(visible=True):
    return dict(status='ok', has_visible_content=visible, refreshed=visible,
        report_id='00000000-0000-0000-0000-000000000101' if visible else None,
        generated_at='2026-11-01T00:00:00Z', content_text='PRIVATE_SYNTHETIC_MAP',
        meta={'private_test_marker':'PRIVATE_SYNTHETIC_MAP'}, history_saved=visible)


class CumulativeJobTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.enterContext(patch.dict(os.environ, COCOLON_ANALYSIS_OBSERVED_MODE='development'))

    async def test_existing_latest_refresher_uses_cumulative_and_never_logs_body(self):
        engine = AsyncMock(return_value=response())
        with patch.object(cumulative, 'ensure_map', engine), \
                patch.object(refresher, 'build_myprofile_monthly_report', side_effect=AssertionError('legacy builder')):
            result = await refresher.refresh_myprofile_latest_report(user_id=OWNER)
        self.assertEqual(result['period'], 'all')
        self.assertNotIn('PRIVATE_SYNTHETIC_MAP', str(result))
        engine.assert_awaited_once_with(OWNER, force=False)

    async def test_input_queue_failure_fallback_uses_same_cumulative_owner(self):
        engine = AsyncMock(return_value=response())
        with patch.object(cumulative, 'ensure_map', engine), patch.object(submit, 'MYPROFILE_LATEST_AUTO_REFRESH_ENABLED', True), \
                patch.object(submit, '_fetch_myprofile_latest_generated_at', side_effect=AssertionError('legacy throttle')):
            await submit._auto_refresh_myprofile_latest_report(OWNER)
        engine.assert_awaited_once_with(OWNER)

    async def test_monthly_cron_includes_free_and_skips_old_table_notification_candidates(self):
        engine = AsyncMock(return_value=response())
        with patch.object(cumulative, 'ensure_map', engine), \
                patch.object(cron, '_select_monthly_report_mode', side_effect=AssertionError('old paid gate')), \
                patch.object(cron, '_enqueue_report_distribution_candidate', side_effect=AssertionError('wrong table notification')):
            results, errors = await cron._run_myprofile_monthly_for_users(user_ids=[OWNER],
                now_utc=datetime.now(timezone.utc), force=True, dry_run=False, period='28d', include_secret=True)
        self.assertEqual(errors, [])
        self.assertEqual(results[0]['status'], 'generated')
        self.assertNotIn('PRIVATE_SYNTHETIC_MAP', str(results))
        engine.assert_awaited_once_with(OWNER, monthly=True, ensure=True)

    async def test_monthly_dry_run_never_generates_or_captures(self):
        engine = AsyncMock(return_value=response(False))
        with patch.object(cumulative, 'ensure_map', engine):
            results, errors = await cron._run_myprofile_monthly_for_users(user_ids=[OWNER],
                now_utc=datetime.now(timezone.utc), force=True, dry_run=True, period='28d', include_secret=True)
        engine.assert_awaited_once_with(OWNER, monthly=True, ensure=False)
        self.assertTrue(results[0]['dry_run'])

    async def test_queued_old_standard_and_deep_do_not_restart_old_chain(self):
        for handler in (worker._handle_analyze_self_structure_standard_v1, worker._handle_analyze_self_structure_deep_v1):
            with self.subTest(handler=handler.__name__), \
                    patch.object(worker, 'refresh_myprofile_latest_report', AsyncMock(return_value={'status':'ok'})) as refresh, \
                    patch.object(worker, '_fetch_latest_internal_snapshot_row', side_effect=AssertionError('old source')):
                result = await handler(user_id=OWNER, payload={'scope':'global'})
                self.assertEqual(result['scope'], 'cumulative')
                refresh.assert_awaited_once()

    async def test_shared_monthly_refresher_exposes_saved_identity_not_a_backfill(self):
        with patch.object(cumulative, 'ensure_map', AsyncMock(return_value=response())) as engine, \
                patch.object(refresher, 'build_myprofile_monthly_report', side_effect=AssertionError('legacy builder')):
            result = await refresher.refresh_myprofile_monthly_report(user_id=OWNER, period_override='28d')
        self.assertEqual(result['source_profile'], 'cumulative.v1')
        self.assertTrue(result['history_saved'])
        engine.assert_awaited_once_with(OWNER, monthly=True)


class QueueLifecycleTests(unittest.IsolatedAsyncioTestCase):
    """Exercise coalescing and completion through the existing HTTP boundary."""

    def setUp(self):
        self.row = dict(job_key='myprofile_latest_refresh:' + OWNER,
            job_type='myprofile_latest_refresh_v1', user_id=OWNER,
            payload={}, status='queued', priority=50, attempts=0,
            max_attempts=8, updated_at='2026-11-08T00:00:00Z')
        self.enterContext(patch.object(queue, 'ensure_supabase_config'))
        self.enterContext(patch.object(queue, 'sb_patch', self._patch))
        self.enterContext(patch.object(queue, 'sb_post', self._post))
        class Clock(datetime):
            ticks = 0

            @classmethod
            def now(cls, tz=None):
                cls.ticks += 1
                return datetime(2026, 11, 8, tzinfo=timezone.utc) + timedelta(microseconds=100000 * cls.ticks)
        self.enterContext(patch.object(queue, 'datetime', Clock))

    async def _patch(self, path, *, json, params, **kwargs):
        import httpx
        def matches(key, condition):
            actual = self.row.get(key)
            if condition.startswith('eq.'):
                expected = condition[3:]
                if key == 'updated_at':
                    return queue._parse_iso_z(actual) == queue._parse_iso_z(expected)
                return str(actual) == expected
            if condition.startswith('neq.'):
                return str(actual) != condition[4:]
            if condition.startswith('in.('):
                return str(actual) in [x.strip('"') for x in condition[4:-1].split(',')]
            raise AssertionError('unexpected queue filter: ' + condition)
        matched = all(matches(key, value) for key, value in params.items())
        if matched:
            self.row.update(deepcopy(json))
        return httpx.Response(200, json=[deepcopy(self.row)] if matched else [])

    async def _post(self, *args, **kwargs):
        raise AssertionError('an existing job must be updated, not inserted')

    async def _enqueue(self):
        await queue.enqueue_job(job_key=self.row['job_key'], job_type=self.row['job_type'],
            user_id=OWNER, payload={'requested_at': 'new-input'}, debounce_seconds=20)

    async def test_new_generation_after_done_or_failed_has_a_fresh_retry_budget(self):
        for status in ('done', 'failed'):
            with self.subTest(status=status):
                self.row.update(status=status, attempts=8)
                await self._enqueue()
                self.assertEqual(self.row['status'], 'queued')
                self.assertEqual(self.row['attempts'], 0)
                claimed = await queue.claim_job(job_key=self.row['job_key'], worker_id='synthetic-worker',
                    attempts=self.row['attempts'])
                self.assertEqual(claimed.attempts, 1)

    async def test_coalesced_queued_and_running_jobs_keep_the_current_retry_budget(self):
        self.row['attempts'] = 3
        await self._enqueue()
        self.assertEqual(self.row['attempts'], 3)
        claimed = await queue.claim_job(job_key=self.row['job_key'], worker_id='synthetic-worker', attempts=3)
        await self._enqueue()
        self.assertEqual(self.row['status'], 'running')
        self.assertEqual(self.row['attempts'], 4)
        await queue.requeue(job_key=claimed.job_key, worker_id=claimed.worker_id,
            error='synthetic-temporary-failure', delay_seconds=10)
        self.assertEqual(self.row['attempts'], 4)
        self.assertGreater(queue._parse_iso_z(self.row['run_after']), queue._parse_iso_z(self.row['updated_at']))

    async def test_input_in_the_claim_second_cannot_be_marked_done_as_unchanged(self):
        claimed = await queue.claim_job(job_key=self.row['job_key'], worker_id='synthetic-worker', attempts=0)
        await self._enqueue()
        self.assertEqual(self.row['payload'], {'requested_at': 'new-input'})
        done = await queue.mark_done_if_unchanged(job_key=claimed.job_key,
            worker_id=claimed.worker_id, expected_updated_at=claimed.updated_at)
        self.assertFalse(done)
        self.assertEqual(self.row['status'], 'running')
        self.assertEqual(self.row['attempts'], 1)


class CompletionPushReservationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.rows = {}
        self.enterContext(patch.object(push_queue, 'ensure_supabase_config'))
        self.enterContext(patch.object(push_queue, 'sb_post', self._insert))
        self.normal_enqueue = self.enterContext(patch.object(push_queue, 'enqueue_job', AsyncMock()))

    async def _insert(self, path, *, params, json, prefer, **kwargs):
        import httpx
        self.assertEqual(path, '/rest/v1/' + queue.JOBS_TABLE)
        self.assertEqual(params, {'on_conflict': 'job_key'})
        self.assertEqual(prefer, 'resolution=ignore-duplicates,return=representation')
        key = json['job_key']
        if key in self.rows:
            return httpx.Response(201, json=[])
        self.rows[key] = deepcopy(json)
        return httpx.Response(201, json=[deepcopy(json)])

    async def _reserve(self, **changes):
        options = dict(user_id=OWNER, title='Emlis', body='わたしマップが更新されました',
            data={'type': 'watashi_map_updated', 'report_id': 'synthetic-map'},
            event_type='watashi_map_updated', job_key_prefix='synthetic-map',
            only_if_absent=True)
        options.update(changes)
        return await push_queue.enqueue_single_user_push_notification(**options)

    async def test_new_completion_is_reserved_once_without_device_tokens(self):
        self.assertEqual(await self._reserve(), 1)
        self.assertEqual(await self._reserve(), 0)
        self.assertEqual(len(self.rows), 1)
        payload = next(iter(self.rows.values()))['payload']
        self.assertEqual(payload['recipient_user_ids'], [OWNER])
        self.assertNotIn('tokens', payload)
        self.normal_enqueue.assert_not_awaited()

    async def test_duplicate_completion_preserves_queued_running_and_terminal_jobs(self):
        await self._reserve()
        key = next(iter(self.rows))
        for status in ('queued', 'running', 'done', 'failed'):
            with self.subTest(status=status):
                self.rows[key].update(status=status, attempts=5, last_error='prior-generation')
                before = deepcopy(self.rows[key])
                self.assertEqual(await self._reserve(), 0)
                self.assertEqual(self.rows[key], before)

    async def test_concurrent_completion_reservations_insert_only_one_job(self):
        import asyncio
        self.assertEqual(sorted(await asyncio.gather(self._reserve(), self._reserve())), [0, 1])
        self.assertEqual(len(self.rows), 1)

    async def test_normal_notifications_keep_existing_enqueue_behavior(self):
        self.assertEqual(await self._reserve(only_if_absent=False), 1)
        self.normal_enqueue.assert_awaited_once()
        self.assertEqual(self.rows, {})

    async def test_insert_failure_is_not_reported_as_a_reservation(self):
        import httpx
        with patch.object(push_queue, 'sb_post', AsyncMock(return_value=httpx.Response(503, json={}))):
            with self.assertRaisesRegex(RuntimeError, 'push_once_insert_failed:503'):
                await self._reserve()


class CumulativeCompletionNotificationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        from test_analysis_cumulative import source_snapshot
        self.snapshot = source_snapshot(1)
        self.artifact, self.coverage = cumulative.build_cumulative_map(OWNER, self.snapshot)
        self.rid = str(UUID(self.artifact.artifact_id[9:]))
        self.row = dict(id=self.rid, source_profile='cumulative.v1', report_mode='standard',
            title='わたしマップ', period_start=self.snapshot['period_start'],
            period_end=self.snapshot['period_end'], generated_at=self.snapshot['period_end'],
            snapshot_month=None, captured_at=None,
            content_text=self.artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'],
            content_json=dict(report_mode='standard',
                watashiMap=self.artifact.safe_projection(authenticated_owner_scope=OWNER),
                map_context=self.coverage))
        self.enterContext(patch.object(cumulative, 'observed_mode', return_value='development'))
        self.enterContext(patch.object(cumulative, 'build_cumulative_map', return_value=(self.artifact, self.coverage)))
        self.reserve = self.enterContext(patch.object(push_queue, 'enqueue_single_user_push_notification', AsyncMock(return_value=1)))

    async def _new_map(self, *, rows=None, rpc=None):
        rows = rows if rows is not None else [{'items': []}, {'items': [self.row]}]
        rpc = rpc if rpc is not None else [self.snapshot, self.rid]
        with patch.object(cumulative, 'read_maps', AsyncMock(side_effect=rows)), \
                patch.object(cumulative, '_rpc', AsyncMock(side_effect=rpc)):
            return await cumulative._ensure_map(OWNER)

    async def test_new_saved_map_reserves_fixed_private_owner_notification(self):
        result = await self._new_map()
        self.assertTrue(result['refreshed'])
        self.reserve.assert_awaited_once()
        options = self.reserve.await_args.kwargs
        self.assertEqual(options['user_id'], OWNER)
        self.assertEqual(options['title'], 'Emlis')
        self.assertEqual(options['body'], 'わたしマップが更新されました')
        self.assertEqual(options['event_type'], 'watashi_map_updated')
        self.assertEqual(options['priority'], 60)
        self.assertTrue(options['only_if_absent'])
        self.assertEqual(options['data'], dict(type='watashi_map_updated', target='watashi_map',
            user_id=OWNER, report_id=self.rid,
            version_key=self.row['content_json']['watashiMap']['projection_of']))
        self.assertNotIn(self.row['content_text'], str(options))
        self.assertNotIn(self.snapshot['members'][0]['original']['memo'], str(options))

    async def test_read_and_reused_current_do_not_reserve_another_completion(self):
        result = await self._new_map(rows=[{'items': [self.row]}, {'items': [self.row]}])
        self.assertFalse(result['refreshed'])
        with patch.object(cumulative, 'read_maps', AsyncMock(return_value={'items': [self.row]})):
            result = await cumulative._ensure_map(OWNER, ensure=False)
        self.assertFalse(result['refreshed'])
        self.reserve.assert_not_awaited()

    async def test_commit_failure_and_guard_rejection_never_notify_success(self):
        from fastapi import HTTPException
        for rpc, rows in (([self.snapshot, HTTPException(503, 'synthetic_commit_failure')], [{'items': []}]),
                          ([self.snapshot, self.rid], [{'items': []}, {'items': []}])):
            with self.subTest(rpc=rpc):
                with self.assertRaises(HTTPException):
                    await self._new_map(rpc=rpc, rows=rows)
                self.reserve.assert_not_awaited()

    async def test_concurrent_commit_reuse_does_not_claim_the_other_artifact_is_new(self):
        from uuid import UUID
        other = deepcopy(self.row)
        other['id'] = str(UUID(int=999))
        await self._new_map(rpc=[self.snapshot, other['id']], rows=[{'items': []}, {'items': [other]}])
        self.reserve.assert_not_awaited()

    async def test_no_artifact_does_not_emit_a_completion(self):
        coverage = dict(self.coverage, mapped_count=0, unparsed_count=1)
        with patch.object(cumulative, 'build_cumulative_map', return_value=(None, coverage)):
            result = await self._new_map(rows=[{'items': []}], rpc=[self.snapshot])
        self.assertFalse(result['has_visible_content'])
        self.reserve.assert_not_awaited()

    async def test_push_reservation_outage_keeps_the_successfully_saved_map(self):
        self.reserve.side_effect = RuntimeError('PRIVATE_FAILURE_BODY')
        with self.assertLogs('analysis_cumulative_service', level='WARNING') as logs:
            result = await self._new_map()
        self.assertTrue(result['refreshed'])
        self.assertEqual(result['report_id'], self.rid)
        self.assertNotIn('PRIVATE_FAILURE_BODY', str(logs.output))


class CompletionPushDeliveryTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        from uuid import UUID
        self.rid = str(UUID(int=101))
        self.payload = dict(recipient_mode='user_ids', recipient_user_ids=[OWNER], actor_user_id=OWNER,
            title='Emlis', body='わたしマップが更新されました', event_type='watashi_map_updated',
            data=dict(type='watashi_map_updated', target='watashi_map', user_id=OWNER,
                report_id=self.rid, version_key='artifact:' + UUID(self.rid).hex + '@1'))
        self.read = self.enterContext(patch.object(cumulative, 'read_maps', AsyncMock(return_value={'items': [{'id': self.rid}]})))
        self.tokens = self.enterContext(patch.object(worker, '_fetch_push_tokens_for_users', AsyncMock(return_value={OWNER: 'synthetic-device-token'})))
        self.sender = self.enterContext(patch.object(worker, '_send_fcm_push', AsyncMock(return_value={'status': 'sent'})))

    async def test_current_owned_map_sends_using_the_existing_worker_and_metadata_only(self):
        result = await worker._handle_send_fcm_push_v1(user_id=OWNER, payload=self.payload)
        self.assertEqual(result['status'], 'sent')
        self.read.assert_awaited_once_with(OWNER, limit=1, metadata_only=True)
        self.tokens.assert_awaited_once_with([OWNER])
        self.sender.assert_awaited_once_with(tokens=['synthetic-device-token'], title='Emlis',
            body='わたしマップが更新されました', data=self.payload['data'])

    async def test_foreign_or_malformed_completion_never_reads_or_sends(self):
        from uuid import UUID
        other = str(UUID(int=2))
        cases = [dict(recipient_user_ids=[other]), dict(actor_user_id=other),
            dict(recipient_mode='tokens'), dict(event_type='generic'), dict(title='wrong'),
            dict(data=dict(self.payload['data'], user_id=other)),
            dict(data=dict(self.payload['data'], version_key='wrong')),
            dict(data=dict(self.payload['data'], target='wrong')),
            dict(data=dict(self.payload['data'], report_id='not-a-map'))]
        for change in cases:
            with self.subTest(change=change):
                result = await worker._handle_send_fcm_push_v1(user_id=OWNER, payload=dict(self.payload, **change))
                self.assertEqual(result['status'], 'skipped_invalid_map_notification')
        self.read.assert_not_awaited()
        self.tokens.assert_not_awaited()
        self.sender.assert_not_awaited()

    async def test_deleted_changed_or_superseded_source_does_not_notify(self):
        from uuid import UUID
        for items in ([], [{'id': str(UUID(int=999))}]):
            with self.subTest(items=items):
                self.read.return_value = {'items': items}
                result = await worker._handle_send_fcm_push_v1(user_id=OWNER, payload=self.payload)
                self.assertEqual(result['status'], 'skipped_stale_map_notification')
        self.tokens.assert_not_awaited()
        self.sender.assert_not_awaited()

    async def test_guard_read_failure_is_retryable_without_sending(self):
        from fastapi import HTTPException
        self.read.side_effect = HTTPException(503, 'synthetic_guard_unavailable')
        with self.assertRaises(HTTPException):
            await worker._handle_send_fcm_push_v1(user_id=OWNER, payload=self.payload)
        self.tokens.assert_not_awaited()
        self.sender.assert_not_awaited()

    async def test_current_push_preference_off_is_respected_at_send_time(self):
        import httpx
        # Exercise the real resolver used by the worker, not a hard-coded empty
        # token result: a registered token with push_enabled=False must not send.
        with patch.object(worker, '_fetch_push_tokens_for_users', submit._fetch_push_tokens_for_users), \
                patch.object(submit, '_ensure_supabase_config'), \
                patch.object(submit, '_sb_get_shared', AsyncMock(return_value=httpx.Response(200,
                    json=[dict(id=OWNER, push_token='synthetic-device-token', push_enabled=False)]))):
            result = await worker._handle_send_fcm_push_v1(user_id=OWNER, payload=self.payload)
        self.assertEqual(result['status'], 'skipped_no_token')
        self.sender.assert_not_awaited()
