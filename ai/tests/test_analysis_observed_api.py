"""Current cumulative FastAPI contract; synthetic transport, real compiler/author.

The withdrawn period/tier API expectations were replaced by Mash's 11/1
cumulative policy. Period compiler/storage regression remains in its own tests.
"""
import copy
from datetime import datetime, timezone, timedelta
import os
import unittest
from unittest.mock import AsyncMock, patch
from uuid import UUID

from fastapi import FastAPI, HTTPException
import httpx
import api_emotion_submit as auth
import api_self_structure as latest
import api_self_structure_reports as reports
import analysis_cumulative_service as service
import report_artifact_read_service as reader
from ai.tests.test_analysis_cumulative import source_snapshot, OWNER

OTHER = str(UUID(int=2))


class AnalysisApiTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.source = source_snapshot(2)
        self.saved = []
        self.months = {}
        self.calls = []
        self.current = True
        self.tier = 'free'
        self.month = datetime.now(timezone(timedelta(hours=9))).date().replace(day=1).isoformat()
        self.patches = [
            patch.dict(os.environ, COCOLON_ANALYSIS_OBSERVED_MODE='development'),
            patch.object(auth, '_ensure_supabase_config'),
            patch.object(auth, 'resolve_user_id_verified_cached', AsyncMock(side_effect=lambda token: OWNER if token == 'valid' else None)),
            patch.object(auth, '_sb_auth_headers_shared', return_value={}),
            patch.object(auth, '_sb_get_shared', AsyncMock(return_value=httpx.Response(401, json={}))),
            patch.object(service, '_rpc', side_effect=self.rpc),
            patch.object(reader, 'sb_get', AsyncMock(side_effect=AssertionError('cumulative must not query legacy history'))),
        ]
        for p in self.patches:
            p.start()
        app = FastAPI()
        latest.register_self_structure_routes(app)
        reports.register_self_structure_report_routes(app)
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://synthetic')

    async def asyncTearDown(self):
        await self.client.aclose()
        for p in reversed(self.patches):
            p.stop()

    async def rpc(self, name, p):
        self.calls.append((name, p))
        self.assertEqual(p['p_user_id'], OWNER)
        if name == 'analysis_cumulative_source_snapshot':
            return dict(copy.deepcopy(self.source), tier=self.tier)
        if name == 'analysis_cumulative_commit':
            if p.get('p_artifact_id'):
                row = dict(id=str(UUID(p['p_artifact_id'][9:])), report_type='latest', report_mode='standard',
                    title='わたしマップ', source_profile='cumulative.v1', snapshot_month=None, captured_at=None,
                    period_start=p['p_start'], period_end=p['p_end'], generated_at=p['p_end'], updated_at=p['p_end'],
                    content_text=p['p_text'], content_json=dict(report_mode='standard', watashiMap=p['p_projection'],
                        map_context=p['p_private_evidence']['coverage']))
                self.saved.append(row)
                self.current = True
            row = self.saved[-1]
            self.months.setdefault(self.month, dict(row, snapshot_month=self.month, report_type='monthly', captured_at=row['generated_at']))
            return row['id']
        if name == 'analysis_cumulative_read':
            if p['p_history'] or p.get('p_month'):
                rows = sorted(self.months.values(), key=lambda r: r['snapshot_month'], reverse=True)
                cap = {'free': 2, 'plus': 12, 'premium': len(rows)}[self.tier]
                rows = rows[:cap]
                if p.get('p_month'):
                    rows = [r for r in rows if r['snapshot_month'] == p['p_month']]
            else:
                rows = self.saved[-1:] if self.current else []
                if p.get('p_id') and not rows:
                    rows = list(self.months.values())[:2]
            if p.get('p_id'):
                rows = [r for r in rows if r['id'] == p['p_id']]
            rows = rows[p['p_offset']:p['p_offset']+p['p_limit']]
            if p.get('p_metadata_only'):
                rows = [{k:v for k,v in row.items() if k not in {'content_json','content_text'}} for row in rows]
            return dict(items=copy.deepcopy(rows), subscription_tier=self.tier,
                matched=any(r['id'] == p.get('p_id') for r in self.saved),
                history_limit={'free': 2, 'plus': 12, 'premium': None}[self.tier])
        raise AssertionError(name)

    async def get(self, path):
        return await self.client.get(path, headers={'Authorization': 'Bearer valid'})

    async def monthly(self, body=None):
        return await self.client.post('/self-structure/monthly/ensure', json=body or {}, headers={'Authorization': 'Bearer valid'})

    async def test_real_generation_status_and_saved_same_text_graph_and_authenticated_owner(self):
        response = await self.get('/self-structure/latest?period=28d&report_mode=deep&user_id='+OTHER)
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertTrue(body['refreshed'])
        self.assertEqual(body['period'], 'all')
        self.assertEqual(body['report_mode'], 'standard')
        self.assertEqual(body['map_context']['source_count'], 2)
        self.assertEqual((await self.get('/self-structure/latest/status')).json()['version_key'], body['meta']['projection_of'])
        again = (await self.get('/self-structure/latest?ensure=false')).json()
        self.assertEqual(again['meta'], body['meta'])
        self.assertEqual(again['content_text'], body['content_text'])
        detail = await self.get('/self-structure/reports/'+body['report_id']+'?month='+self.month)
        self.assertEqual(detail.status_code, 200, detail.text)
        self.assertEqual(detail.json()['item']['content_json']['watashiMap'], body['meta'])
        self.assertEqual(detail.json()['item']['content_text'], body['content_text'])
        self.assertNotIn('private_evidence', response.text+detail.text)
        self.assertEqual(sum(n == 'analysis_cumulative_commit' for n, _ in self.calls), 1)

    async def test_all_plans_use_the_same_current_map_and_free_monthly_is_available(self):
        first = (await self.get('/self-structure/latest')).json()
        for tier in ('free', 'plus', 'premium'):
            self.tier = tier
            row = (await self.get('/self-structure/latest?ensure=false')).json()
            self.assertEqual(row['meta'], first['meta'])
            self.assertEqual(row['content_text'], first['content_text'])
            history = await self.get('/self-structure/reports/history')
            self.assertEqual(history.status_code, 200, history.text)
            self.assertEqual(history.json()['items'][0]['snapshot_month'], self.month)

    async def test_monthly_existing_capture_is_not_regenerated_after_current_becomes_uninterpretable(self):
        first = (await self.monthly()).json()
        self.current = False
        self.source['members'][0]['original']['memo'] = 'まだ言葉にできない。'
        with patch.object(service, 'build_cumulative_map', side_effect=AssertionError('historical regeneration forbidden')):
            again = await self.monthly({'force': True})
        self.assertEqual(again.status_code, 200, again.text)
        for key in ('report_id', 'content_text', 'meta', 'captured_at', 'generated_at'):
            self.assertEqual(again.json()[key], first[key])
        self.assertEqual(sum(n == 'analysis_cumulative_commit' for n, _ in self.calls), 1)

    async def test_no_saved_map_empty_sources_and_unparsed_sources_are_distinct(self):
        read = (await self.get('/self-structure/latest?ensure=false')).json()
        self.assertEqual(read['reason'], 'no_visible_content')
        self.source['members'] = []
        empty = (await self.get('/self-structure/latest')).json()
        self.assertEqual(empty['reason'], 'no_visible_content')
        self.assertEqual(empty['map_context']['source_count'], 0)
        self.source = source_snapshot(1)
        self.source['members'][0]['original']['memo'] = 'まだ言葉を整理しているところです。'
        pending = (await self.get('/self-structure/latest')).json()
        self.assertEqual(pending['reason'], 'insufficient_input')
        self.assertEqual(pending['map_context']['unparsed_count'], 1)
        self.assertIsNone(pending['meta'])
        self.assertEqual(self.saved, [])

    async def test_missing_or_invalid_auth_cannot_touch_source_or_evidence(self):
        for headers in ({}, {'Authorization': 'Bearer invalid'}):
            for url in ('/self-structure/latest', '/self-structure/reports/history',
                        '/self-structure/reports/'+str(UUID(int=99))+'/evidence?node=n1'):
                response = await self.client.get(url, headers=headers)
                self.assertEqual(response.status_code, 401)
        self.assertEqual(self.calls, [])

    async def test_normal_http_uses_opt_in_analysis_provider_and_keeps_saved_reads_on_config_loss(self):
        import analysis_model_source
        from test_analysis_cumulative_model_source import provider_environment, provider_packet, synthetic_response
        from test_analysis_model_observed_roles import material
        self.source = material('pair')
        received = []
        real_client = httpx.AsyncClient
        def handler(request):
            received.append(request)
            prepared = service.prepare_cumulative_category_units(OWNER, self.source, prompt_version='selected_material.v4')
            return httpx.Response(200, json=provider_packet(synthetic_response(prepared).raw))
        with patch.dict(os.environ, provider_environment()), patch.object(analysis_model_source.httpx,
                'AsyncClient', side_effect=lambda **kw: real_client(**{**kw, 'transport':httpx.MockTransport(handler)})):
            first = await self.get('/self-structure/latest')
            self.assertEqual(first.status_code, 200, first.text)
            self.assertTrue(first.json()['refreshed'])
            self.assertIn('受付係', first.json()['content_text'])
            self.assertEqual(len(first.json()['meta']['nodes']), 2)
            self.assertEqual(len(received), 1)
            with patch.dict(os.environ, COCOLON_ANALYSIS_MODEL_API_KEY=''):
                for saved in (await self.get('/self-structure/latest'),
                        await self.get('/self-structure/latest?ensure=false'), await self.monthly({'force':True})):
                    self.assertEqual(saved.status_code, 200, saved.text)
                    self.assertEqual(saved.json()['content_text'], first.json()['content_text'])
                    self.assertEqual(saved.json()['meta'], first.json()['meta'])
                failure = await self.get('/self-structure/latest?force=true')
                self.assertEqual(failure.status_code, 503, failure.text)
                self.assertNotIn('synthetic-analysis-private-key', failure.text)
            self.assertEqual(len(received), 1)
            self.assertEqual(len(self.saved), 1)

    async def test_invalid_auth_does_not_resolve_an_enabled_model_provider(self):
        from test_analysis_cumulative_model_source import provider_environment
        import analysis_model_source
        with patch.dict(os.environ, provider_environment()), patch.object(analysis_model_source,
                'application_analysis_model_source', side_effect=AssertionError('provider before authentication')):
            result = await self.client.get('/self-structure/latest', headers={'Authorization':'Bearer invalid'})
        self.assertEqual(result.status_code, 401)
        self.assertEqual(self.calls, [])

    async def test_storage_failure_and_generation_failure_do_not_become_empty_or_legacy(self):
        with patch.object(service, '_rpc', AsyncMock(side_effect=HTTPException(503, 'analysis_storage_unavailable'))):
            response = await self.get('/self-structure/latest')
        self.assertEqual(response.status_code, 503)
        with patch.object(service, 'build_cumulative_map', side_effect=ValueError('synthetic private error')):
            response = await self.get('/self-structure/latest')
        self.assertEqual(response.status_code, 422)
        self.assertNotIn('synthetic private', response.text)
        self.assertEqual(self.saved, [])

    async def test_unsupported_source_overrides_are_denied_and_legacy_is_not_merged(self):
        self.assertEqual((await self.monthly({'include_secret': False})).status_code, 400)
        self.assertEqual((await self.monthly({'now_iso': '2025-01-01T00:00:00Z'})).status_code, 400)
        self.assertEqual((await self.get('/self-structure/reports/history?report_type=latest')).status_code, 400)
        self.assertEqual((await self.get('/self-structure/reports/history')).json()['items'], [])

    async def test_default_off_does_not_access_cumulative_store(self):
        with patch.dict(os.environ, COCOLON_ANALYSIS_OBSERVED_MODE='off'), \
                patch.object(latest, '_sb_get', AsyncMock(return_value=httpx.Response(200, json=[]))):
            response = await self.get('/self-structure/latest/status')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.calls, [])


if __name__ == '__main__':
    unittest.main()
