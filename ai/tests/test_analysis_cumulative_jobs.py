"""Existing input/worker/cron callers must not write the withdrawn period map."""
from datetime import datetime, timezone
import os
import unittest
from unittest.mock import AsyncMock, patch

import analysis_cumulative_service as cumulative
import astor_self_structure_report as refresher
import api_emotion_submit as submit
import api_cron_distribution as cron
import astor_worker as worker

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
