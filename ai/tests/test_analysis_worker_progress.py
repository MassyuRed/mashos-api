"""Exercise worker lease changes against a conditional, in-memory PostgREST row."""
import asyncio
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

from analysis_job_progress import (MapJobClaimChanged, MapJobClaimUnavailable,
    check_map_job_owner, checkpoint_v24_phase, map_job_progress)
import astor_job_queue as queue


def response(status, data):
    return SimpleNamespace(status_code=status, json=lambda: deepcopy(data), text='')


class MapProgressTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        old = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        self.row = dict(job_key='myprofile_latest_refresh:synthetic', user_id='synthetic',
            job_type='myprofile_latest_refresh_v1', status='running', worker_id='worker-A',
            started_at=old, updated_at=old, attempts=1, max_attempts=8,
            payload={'trigger': 'map_view'}, run_after=old)
        self.job = queue._row_to_job(deepcopy(self.row))
        self.trigger = False
        self.unknown_ack = False
        self.enterContext(patch.object(queue, 'ensure_supabase_config'))
        self.enterContext(patch.object(queue, 'sb_patch', self.patch_row))

    async def patch_row(self, _path, *, params, json, **kwargs):
        for key, wanted in params.items():
            if key == 'select':
                continue
            value = self.row.get(key)
            if wanted == 'is.null':
                matched = value is None
            elif wanted.startswith('neq.'):
                matched = wanted[4:] != str(value)
            else:
                matched = wanted == 'eq.' + str(value)
            if not matched:
                return response(200, [])
        self.row.update(deepcopy(json))
        if self.trigger:
            self.row['updated_at'] = queue._now_iso_z()
        if self.unknown_ack:
            raise OSError('unavailable')
        return response(200, [self.row])

    async def stale(self, scanned):
        with patch.object(queue, 'sb_get', AsyncMock(return_value=response(200, [scanned]))):
            return await queue.requeue_stale_running_jobs(stale_running_seconds=1800)

    async def test_completed_phases_renew_without_losing_enqueue_revision(self):
        for trigger in (False, True):
            self.trigger = trigger
            started, previous = self.job.started_at, self.job.run_after
            await queue.renew_map_job_progress(self.job)
            self.assertEqual(self.job.started_at, started)
            self.assertNotEqual(self.job.run_after, previous)
            self.assertEqual(self.job.updated_at, self.row['updated_at'])
        await queue.check_map_job_owner(self.job)
        self.assertTrue(await queue.mark_done_if_unchanged(job_key=self.job.job_key,
            claim=self.job, expected_updated_at=self.job.updated_at))
        self.assertEqual(self.row['status'], 'done')

    async def test_new_input_is_preserved_and_old_compute_cannot_commit(self):
        self.row['max_attempts'] = self.job.max_attempts = 1
        self.row.update(updated_at=queue._now_iso_z(), last_error='map_updated_while_running',
                        payload={'trigger': 'new input'})
        with self.assertRaises(MapJobClaimChanged):
            await queue.check_map_job_owner(self.job)
        self.assertFalse(await queue.mark_done_if_unchanged(job_key=self.job.job_key,
            claim=self.job, expected_updated_at=self.job.updated_at))
        await queue.requeue(job_key=self.job.job_key, claim=self.job, error='map_claim_changed')
        self.assertEqual((self.row['status'], self.row['attempts'], self.row['max_attempts']), ('queued', 0, 1))
        self.assertEqual(self.row['payload'], {'trigger': 'new input'})

    async def test_old_claim_cannot_finish_fail_or_requeue_replacement(self):
        # Reused process name and attempt number still have a new lease timestamp.
        self.row.update(started_at=queue._now_iso_z(), updated_at=queue._now_iso_z())
        newer = deepcopy(self.row)
        with self.assertRaises(MapJobClaimChanged):
            await queue.renew_map_job_progress(self.job)
        self.assertFalse(await queue.mark_done_if_unchanged(job_key=self.job.job_key,
            claim=self.job, expected_updated_at=self.job.updated_at))
        await queue.mark_failed(job_key=self.job.job_key, claim=self.job, error='old')
        await queue.requeue(job_key=self.job.job_key, claim=self.job, error='old')
        self.assertEqual(self.row, newer)

    async def test_stale_scan_loses_to_real_progress_and_replacement(self):
        scanned = deepcopy(self.row)
        await queue.renew_map_job_progress(self.job)
        self.assertEqual(await self.stale(scanned), 0)
        self.assertEqual(await self.stale(deepcopy(self.row)), 0)
        self.assertEqual(self.row['status'], 'running')

    async def test_dead_claim_requeues_with_budget_or_fails_last_attempt(self):
        old = deepcopy(self.row)
        self.assertEqual(await self.stale(deepcopy(self.row)), 1)
        self.assertEqual((self.row['status'], self.row['attempts']), ('queued', 1))
        self.row = dict(old, attempts=8)
        self.assertEqual(await self.stale(deepcopy(self.row)), 0)
        self.assertEqual((self.row['status'], self.row['last_error']), ('failed', 'map_progress_stalled'))

    async def test_unknown_heartbeat_ack_aborts_without_overwriting_current_lease(self):
        old = self.job.run_after
        self.unknown_ack = True
        with self.assertRaises(MapJobClaimUnavailable):
            await queue.renew_map_job_progress(self.job)
        self.assertEqual(self.job.run_after, old)
        self.assertNotEqual(self.row['run_after'], old)
        self.unknown_ack = False
        await queue.requeue(job_key=self.job.job_key, claim=self.job, error='old')
        self.assertEqual(self.row['status'], 'running')

    async def test_same_generation_final_retry_and_legacy_exhausted_row_never_claim(self):
        self.row['max_attempts'] = self.job.max_attempts = 1
        await queue.requeue(job_key=self.job.job_key, claim=self.job, error='unavailable')
        self.assertEqual((self.row['status'], self.row['attempts']), ('failed', 1))
        self.row['status'] = 'queued'
        candidate = queue._row_to_job(self.row)
        got = await queue.claim_job(job_key=self.job.job_key, worker_id='B', attempts=1, candidate=candidate)
        self.assertIsNone(got)
        self.assertEqual((self.row['status'], self.row['attempts']), ('failed', 1))

    async def test_old_queued_snapshot_cannot_replace_new_revision_or_reset_attempts(self):
        self.row.update(status='queued', attempts=0, max_attempts=1)
        observed = queue._row_to_job(self.row)
        self.row.update(updated_at=queue._now_iso_z(), attempts=1)
        self.assertIsNone(await queue.claim_job(job_key=self.job.job_key, worker_id='B',
                                                attempts=0, candidate=observed))
        self.assertEqual((self.row['status'], self.row['attempts']), ('queued', 1))

    async def test_stalled_new_request_gets_fresh_budget(self):
        self.row.update(max_attempts=1, last_error='map_updated_while_running', payload={'value': 'new'})
        self.assertEqual(await self.stale(deepcopy(self.row)), 1)
        self.assertEqual((self.row['status'], self.row['attempts'], self.row['payload']), ('queued', 0, {'value': 'new'}))
        fresh = queue._row_to_job(self.row)
        got = await queue.claim_job(job_key=fresh.job_key, worker_id='B', attempts=0, candidate=fresh)
        self.assertEqual((got.status, got.attempts, got.started_at, got.run_after),
                         ('running', 1, self.row['started_at'], self.row['started_at']))

    async def test_first_phase_stall_with_automatic_updated_at_does_not_replenish_budget(self):
        started = queue._parse_iso_z(self.row['started_at'])
        self.row.update(max_attempts=1, run_after=self.row['started_at'],
                        updated_at=(started + timedelta(microseconds=1)).isoformat())
        self.assertEqual(await self.stale(deepcopy(self.row)), 0)
        self.assertEqual((self.row['status'], self.row['attempts']), ('failed', 1))

    async def test_legacy_claim_with_newer_input_before_first_progress_is_preserved(self):
        started = queue._parse_iso_z(self.row['started_at'])
        self.row.update(max_attempts=1, run_after=(started - timedelta(seconds=20)).isoformat(),
                        updated_at=(started + timedelta(seconds=1)).isoformat())
        self.assertEqual(await self.stale(deepcopy(self.row)), 1)
        self.assertEqual((self.row['status'], self.row['attempts']), ('queued', 0))

    async def test_health_retains_actual_runtime_and_uses_progress_for_staleness(self):
        await queue.renew_map_job_progress(self.job)
        with patch.object(queue, 'sb_get', AsyncMock(return_value=response(200, [self.row]))):
            stats = await queue.fetch_queue_stats(stale_running_seconds=1800)
        self.assertEqual(stats['stale_running_count'], 0)
        self.assertGreater(stats['oldest_running_age_seconds'], 3500)

    async def test_callbacks_are_task_scoped_and_reset_on_exit(self):
        progress, check = AsyncMock(), AsyncMock()
        async def checkpoints():
            await checkpoint_v24_phase()
            await check_map_job_owner()
        outside = asyncio.create_task(checkpoints())
        with map_job_progress(progress, check):
            await asyncio.gather(outside, asyncio.create_task(checkpoints()))
        await checkpoints()
        progress.assert_awaited_once()
        check.assert_awaited_once()

    async def test_unaccepted_analysis_settles_the_claim_without_repeating_generation(self):
        import analysis_cumulative_service as cumulative
        import analysis_observed_service as observed
        import astor_worker as worker

        rejected = dict(reason=cumulative.NO_ACCEPTED_MAP_STRUCTURE, has_visible_content=False)
        with patch.object(observed, 'observed_enabled', return_value=True), \
                patch.object(cumulative, 'ensure_map', AsyncMock(return_value=rejected)) as ensure_map, \
                patch.object(worker, '_run_worker_maintenance', AsyncMock()), \
                patch.object(worker, 'fetch_next_queued_job',
                             AsyncMock(side_effect=[self.job, asyncio.CancelledError()])), \
                patch.object(worker, 'claim_job', AsyncMock(return_value=self.job)), \
                patch.object(worker, 'requeue', AsyncMock()) as requeue, \
                patch.object(worker, 'mark_done_if_unchanged', AsyncMock()) as mark_done:
            self.job.user_id = '00000000-0000-4000-8000-000000000001'
            with self.assertRaises(asyncio.CancelledError):
                await worker._worker_loop()
        ensure_map.assert_awaited_once()
        mark_done.assert_not_awaited()
        requeue.assert_not_awaited()
        self.assertEqual((self.row['status'], self.row['last_error']),
                         ('failed', cumulative.NO_ACCEPTED_MAP_STRUCTURE))

    async def test_settlement_retries_transport_loss_without_replacing_another_claim(self):
        attempts = 0

        async def lose_first_ack(*args, **kwargs):
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise OSError('database connection unavailable')
            return await self.patch_row(*args, **kwargs)

        with patch.object(queue, 'sb_patch', lose_first_ack), patch.object(queue.asyncio, 'sleep', AsyncMock()):
            await queue.mark_failed(job_key=self.job.job_key, claim=self.job, error='analysis_model_rate_limited')
        self.assertEqual(attempts, 2)
        self.assertEqual((self.row['status'], self.row['last_error']), ('failed', 'analysis_model_rate_limited'))

    async def test_provider_rate_limit_reschedules_with_retry_after(self):
        from fastapi import HTTPException
        import astor_worker as worker

        limited = HTTPException(429, 'analysis_model_rate_limited', headers={'Retry-After': '180'})
        with patch.object(worker, '_run_map_job', AsyncMock(side_effect=limited)), \
                patch.object(worker, '_run_worker_maintenance', AsyncMock()), \
                patch.object(worker, 'fetch_next_queued_job', AsyncMock(side_effect=[self.job, asyncio.CancelledError()])), \
                patch.object(worker, 'claim_job', AsyncMock(return_value=self.job)), \
                patch.object(worker, 'requeue', AsyncMock()) as requeue:
            with self.assertRaises(asyncio.CancelledError):
                await worker._worker_loop()
        self.assertEqual(requeue.await_args.kwargs['delay_seconds'], 180)
        self.assertEqual(requeue.await_args.kwargs['error'], 'analysis_model_rate_limited')


class WorkerPostgrestPollTests(unittest.IsolatedAsyncioTestCase):
    async def test_queue_fetch_and_claim_surface_only_transient_postgrest_codes(self):
        with patch.object(queue, 'ensure_supabase_config'), \
                patch.object(queue, 'sb_get', AsyncMock(side_effect=[
                    response(503, {'code': 'PGRST002', 'message': 'private response discarded'}),
                    response(503, {'code': 'other'}), response(200, []),
                ])), patch.object(queue, 'sb_patch', AsyncMock(side_effect=[
                    response(504, {'code': 'PGRST003'}), response(200, []),
                ])) as patch_row:
            with self.assertRaisesRegex(queue.AstorQueueTemporarilyUnavailable, '^PGRST002$'):
                await queue.fetch_next_queued_job()
            self.assertIsNone(await queue.fetch_next_queued_job())
            self.assertIsNone(await queue.fetch_next_queued_job())
            with self.assertRaisesRegex(queue.AstorQueueTemporarilyUnavailable, '^PGRST003$'):
                await queue.claim_job(job_key='job', worker_id='worker', attempts=0)
            patch_row.assert_awaited_once()
            self.assertIsNone(await queue.claim_job(job_key='job', worker_id='worker', attempts=0))

    async def test_worker_caps_backoff_and_resumes_ordinary_poll_after_recovery(self):
        import astor_worker as worker

        job = SimpleNamespace(job_key='job', attempts=0)
        fetch_failed = queue.AstorQueueTemporarilyUnavailable('PGRST002')
        claim_failed = queue.AstorQueueTemporarilyUnavailable('PGRST003')
        with patch.dict(worker.os.environ, {'ASTOR_WORKER_POLL_INTERVAL_SECONDS': '1'}), \
                patch.object(worker, '_run_worker_maintenance', AsyncMock()), \
                patch.object(worker, 'fetch_next_queued_job', AsyncMock(side_effect=[
                    fetch_failed, job, job, fetch_failed, fetch_failed, fetch_failed, fetch_failed,
                    None, fetch_failed, asyncio.CancelledError(),
                ])), patch.object(worker, 'claim_job', AsyncMock(side_effect=[claim_failed, claim_failed])), \
                patch.object(worker.asyncio, 'sleep', AsyncMock()) as sleep:
            with self.assertRaises(asyncio.CancelledError):
                await worker._worker_loop()
        self.assertEqual([call.args for call in sleep.await_args_list],
                         [(1.0,), (2.0,), (4.0,), (8.0,), (16.0,), (30.0,), (30.0,), (1.0,), (1.0,)])


if __name__ == '__main__':
    unittest.main()
