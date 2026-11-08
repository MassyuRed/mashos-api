"""Only candidate GETs retry transient transport failures; no send replay."""
import asyncio
from unittest.mock import AsyncMock

import httpx
import pytest
import supabase_client as sb
from today_question_store import TodayQuestionStore
from report_distribution_push_store import ReportDistributionPushStore


@pytest.mark.parametrize('kind', ['today', 'report'])
@pytest.mark.parametrize('failure', ['recover', 'timeout', 'forbidden', 'json'])
def test_candidate_read_retry_boundary(monkeypatch, kind, failure):
    calls = []
    async def transport(request):
        calls.append(request.method)
        if failure == 'timeout' or (failure == 'recover' and len(calls) < 3):
            raise httpx.ReadTimeout('synthetic timeout', request=request)
        if failure == 'forbidden':
            return httpx.Response(403, json={'message': 'forbidden'})
        if failure == 'json':
            return httpx.Response(200, text='invalid-json')
        return httpx.Response(200, json=[])
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
            monkeypatch.setattr(sb, 'get_async_client', AsyncMock(return_value=client))
            monkeypatch.setattr(sb, 'SUPABASE_URL', 'https://synthetic.supabase.test')
            monkeypatch.setattr(sb, 'ensure_supabase_config', lambda: None)
            monkeypatch.setattr(sb, 'sb_service_role_headers_json', lambda: {})
            monkeypatch.setattr(sb.asyncio, 'sleep', AsyncMock())
            import today_question_store as today
            import report_distribution_push_store as report
            monkeypatch.setattr(today, 'ensure_supabase_config', lambda: None)
            monkeypatch.setattr(report, 'ensure_supabase_config', lambda: None)
            fetch = TodayQuestionStore()._fetch_profiles_for_push_scan(10) if kind == 'today' else ReportDistributionPushStore().list_pending_candidates(limit=10)
            if failure == 'recover':
                assert await fetch == []
            else:
                with pytest.raises(Exception):
                    await fetch
    asyncio.run(run())
    assert calls == ['GET'] * (3 if failure in ('recover', 'timeout') else 1)


@pytest.mark.parametrize('method', ['POST', 'PATCH'])
def test_write_transport_failure_never_retries_even_with_read_override(monkeypatch, method):
    calls = []
    async def transport(request):
        calls.append(request.method)
        raise httpx.ReadTimeout('synthetic timeout', request=request)
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
            monkeypatch.setattr(sb, 'get_async_client', AsyncMock(return_value=client))
            monkeypatch.setattr(sb, 'SUPABASE_URL', 'https://synthetic.supabase.test')
            monkeypatch.setattr(sb, 'ensure_supabase_config', lambda: None)
            monkeypatch.setattr(sb, 'sb_service_role_headers_json', lambda: {})
            with pytest.raises(httpx.ReadTimeout):
                await sb.sb_request(method, '/rest/v1/synthetic', read_retry_count=2)
    asyncio.run(run())
    assert calls == [method]
