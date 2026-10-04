"""Real FastAPI entrypoints; fake Auth/DB transport, real lifecycle and CMEE."""
import copy
from datetime import datetime, timedelta
import os
import unittest
from unittest.mock import AsyncMock, patch
from uuid import UUID

from fastapi import FastAPI, HTTPException
import httpx
import api_emotion_submit as auth
import api_self_structure as latest
import api_self_structure_reports as reports
import api_report_reads as unread
import analysis_observed_service as service
import report_artifact_read_service as reader
from subscription import SubscriptionTier
from ai.tests.test_analysis_observed_storage import fixture, OWNER, OTHER, GUARD, result


class AnalysisApiTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.fx = fixture()
        self.saved = []
        self.calls = []
        self.tier = 'plus'
        self.legacy = []
        self.patches = [
            patch.dict(os.environ, COCOLON_ANALYSIS_OBSERVED_MODE='development'),
            patch.object(auth, '_ensure_supabase_config'),
            patch.object(auth, 'resolve_user_id_verified_cached', AsyncMock(side_effect=lambda token: OWNER if token=='valid' else None)),
            patch.object(auth, '_sb_auth_headers_shared', return_value={}),
            patch.object(auth, '_sb_get_shared', AsyncMock(return_value=httpx.Response(401,json={}))),
            patch.object(service, '_rpc', side_effect=self.rpc),
            patch.object(reader, 'sb_get', AsyncMock(side_effect=lambda *a, **kw: httpx.Response(200,json=self.legacy))),
            patch('subscription_store.get_subscription_tier_for_user', AsyncMock(return_value=SubscriptionTier.PLUS)),
            patch('access_policy.subscription_context.get_subscription_tier_for_user', AsyncMock(return_value=SubscriptionTier.PLUS)),
        ]
        for p in self.patches: p.start()
        self.app = FastAPI()
        latest.register_self_structure_routes(self.app)
        reports.register_self_structure_report_routes(self.app)
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app),base_url='http://synthetic')

    async def asyncTearDown(self):
        await self.client.aclose()
        for p in reversed(self.patches): p.stop()

    async def rpc(self, name, payload):
        self.calls.append((name,payload))
        self.assertEqual(payload['p_user_id'],OWNER)
        if name == 'analysis_observed_source_snapshot':
            return {'guard':GUARD,'tier':self.tier,'now':payload['p_end'],
                'members':[{'original':self.fx['original'],'thread':None,'events':[]}]}
        if name == 'analysis_observed_comparison_snapshot':
            start, end = datetime.fromisoformat(payload['p_start']), datetime.fromisoformat(payload['p_end'])
            previous_start = start-(end-start)
            current = dict(self.fx['original'], created_at=(end-timedelta(hours=1)).replace(tzinfo=None).isoformat())
            previous = dict(current, id=str(UUID(int=99)), memo='私は考えをノートに書かなかった。',
                created_at=(start-timedelta(hours=1)).replace(tzinfo=None).isoformat())
            def snap(original):
                return {'guard':GUARD,'tier':self.tier,'now':payload['p_end'],
                    'members':[{'original':original,'thread':None,'events':[]}]}
            return {'guard':'analysis-db-compare-v1:'+'b'*64,'tier':self.tier,'comparison_eligible':True,
                'current':snap(current),'previous':snap(previous),
                'previous_start':previous_start.isoformat(),'previous_end':start.isoformat()}
        if name == 'analysis_observed_commit':
            row = copy.deepcopy(self.fx['row'])
            row.update(id=str(UUID(payload['p_artifact_id'][9:])),report_type=payload['p_report_type'],
                report_mode=payload['p_mode'],period_start=payload['p_start'],period_end=payload['p_end'],
                content_text=payload['p_text'],content_json={'report_mode':payload['p_mode'],'watashiMap':payload['p_projection']})
            self.saved = [row]
            return row['id']
        if payload.get('p_history') and self.tier=='free':
            raise HTTPException(403,'analysis_history_unavailable')
        rows = self.saved
        if payload.get('p_id'): rows = [r for r in rows if r['id']==payload['p_id']]
        elif payload.get('p_report_type'): rows = [r for r in rows if r['report_type']==payload['p_report_type']]
        if payload.get('p_mode'): rows = [r for r in rows if r['report_mode']==payload['p_mode']]
        return result(rows,self.tier,matched=any(r['id']==payload.get('p_id') for r in self.saved))

    async def get(self,path,**kwargs):
        return await self.client.get(path,headers={'Authorization':'Bearer valid'},**kwargs)

    async def test_http_save_latest_status_read_and_owner_binding(self):
        response = await self.get('/self-structure/latest?report_mode=standard&user_id='+OTHER)
        self.assertEqual(response.status_code,200,response.text)
        body = response.json()
        self.assertTrue(body['refreshed'])
        ref = body['meta']['projection_of']
        status = await self.get('/self-structure/latest/status')
        self.assertEqual(status.json()['version_key'],ref)
        count = sum(n=='analysis_observed_commit' for n,_ in self.calls)
        again = await self.get('/self-structure/latest?ensure=false')
        self.assertEqual(again.json()['meta'],body['meta'])
        self.assertEqual(again.json()['content_text'],body['content_text'])
        self.assertEqual(sum(n=='analysis_observed_commit' for n,_ in self.calls),count)
        self.assertNotIn('private_evidence',response.text)

    async def test_missing_invalid_auth_never_touches_store(self):
        for headers in ({},{'Authorization':'Bearer invalid'}):
            response=await self.client.get('/self-structure/latest',headers=headers)
            self.assertEqual(response.status_code,401)
            response=await self.client.get('/self-structure/reports/history',headers=headers)
            self.assertEqual(response.status_code,401)
        self.assertEqual(self.calls,[])

    async def test_comparison_http_latest_history_detail_return_same_saved_text_and_graph(self):
        with patch.dict(os.environ, COCOLON_ANALYSIS_PERIOD_COMPARISON_MODE='development'):
            response=await self.get('/self-structure/latest?report_mode=standard&user_id='+OTHER)
            self.assertEqual(response.status_code,200,response.text)
            body=response.json(); row=self.saved[0]
            self.assertEqual(body['meta']['period_comparison']['state'],'COMPARABLE')
            again=await self.get('/self-structure/latest?ensure=false&report_mode=standard')
            detail=await self.get('/self-structure/reports/'+row['id'])
            self.assertEqual(again.json()['content_text'],body['content_text'])
            self.assertEqual(detail.json()['item']['content_json']['watashiMap'],body['meta'])
            self.assertEqual(detail.json()['item']['content_text'],body['content_text'])
            row['report_type']='monthly'
            history=await self.get('/self-structure/reports/history')
            self.assertEqual(history.json()['items'][0]['id'],row['id'])
            self.assertEqual(sum(n=='analysis_observed_commit' for n,_ in self.calls),1)
            for private in ('previous_evidence','comparison_dependency','current_source_set_ref'):
                self.assertNotIn(private,response.text+again.text+detail.text+history.text)

    async def test_plan_and_unsupported_secret_override(self):
        deep=await self.get('/self-structure/latest?report_mode=deep')
        self.assertEqual(deep.status_code,403)
        monthly=await self.client.post('/self-structure/monthly/ensure',headers={'Authorization':'Bearer valid'},
            json={'include_secret':False})
        self.assertEqual(monthly.status_code,400)
        self.tier='free'
        history=await self.get('/self-structure/reports/history')
        self.assertEqual(history.status_code,403)
        self.assertFalse(any(n=='analysis_observed_commit' for n,_ in self.calls))

    async def test_http_history_detail_unread_same_id_and_legacy_mode_guard(self):
        row=copy.deepcopy(self.fx['row']); row['report_type']='monthly'; self.saved=[row]
        legacy=copy.deepcopy(row); legacy.update(id=str(UUID(int=777)),content_text='legacy')
        for shape in ({'reportMode':'deep'},{'meta':{'report_mode':'deep'}},
                      {'report_mode':'standard','meta':{'report_mode':'deep'}}):
            legacy['content_json']=shape; self.legacy=[legacy]
            page=await self.get('/self-structure/reports/history')
            self.assertEqual(page.status_code,200,page.text)
            self.assertEqual([r['id'] for r in page.json()['items']],[row['id']])
        detail=await self.get('/self-structure/reports/'+row['id'])
        self.assertEqual(detail.json()['item']['content_json'],row['content_json'])
        self.assertEqual(await unread._fetch_latest_self_structure_ids(OWNER,tier_str='plus',limit=1),[row['id']])

    async def test_active_failure_does_not_call_legacy_builder(self):
        with patch.object(service,'generate_saved',AsyncMock(side_effect=HTTPException(409,'changed'))), \
             patch.object(latest,'_sb_get',AsyncMock(side_effect=AssertionError('legacy accessed'))):
            response=await self.get('/self-structure/latest')
        self.assertEqual(response.status_code,409)

    async def test_default_off_does_not_touch_observed_storage(self):
        with patch.dict(os.environ,COCOLON_ANALYSIS_OBSERVED_MODE='off'), \
             patch.object(latest,'_sb_get',AsyncMock(return_value=httpx.Response(200,json=[]))):
            response=await self.get('/self-structure/latest/status')
        self.assertEqual(response.status_code,200,response.text)
        self.assertEqual(self.calls,[])


if __name__=='__main__': unittest.main()
