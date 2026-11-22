"""Request-private model sharing and cancellation, without provider or SQL.

The real preview owner runs against existing synthetic saved-control seams.
No test implies a persisted reservation or exactly-once generation across
different server processes, completed acquisitions or database transactions.
"""
import asyncio

import pytest

from piece_v2_contract import PieceContractError
import piece_v2_preview_service as preview


@pytest.fixture(autouse=True)
def no_retained_acquisitions():
    assert not preview._MODEL_INFLIGHT
    yield
    assert not preview._MODEL_INFLIGHT


def test_same_owner_key_fingerprint_and_callable_share_one_pending_acquisition():
    async def run():
        entered, release = asyncio.Event(), asyncio.Event()
        calls, receipt, prepared = [], object(), object()
        async def source(value):
            calls.append(value); entered.set(); await release.wait(); return receipt
        first = asyncio.create_task(preview._shared_model_receipt('owner', 'key', 'same', source, prepared))
        await asyncio.wait_for(entered.wait(), 1)
        second = asyncio.create_task(preview._shared_model_receipt('owner', 'key', 'same', source, prepared))
        await asyncio.sleep(0)
        assert calls == [prepared]
        release.set()
        assert await first is receipt and await second is receipt
        assert not preview._MODEL_INFLIGHT
        # Completion is not a permanent result cache. Persisted replay is
        # handled before this helper by the existing preview record owner.
        assert await preview._shared_model_receipt('owner', 'key', 'same', source, prepared) is receipt
        assert calls == [prepared, prepared]
    asyncio.run(run())


@pytest.mark.parametrize('changed', ['fingerprint', 'callable'])
def test_a_pending_key_cannot_accept_a_different_request_or_model_callable(changed):
    async def run():
        entered, release = asyncio.Event(), asyncio.Event()
        calls = []
        async def source(value):
            calls.append(('first', value)); entered.set(); await release.wait(); return 'first-receipt'
        async def other(value):
            calls.append(('other', value)); return 'other-receipt'
        first = asyncio.create_task(preview._shared_model_receipt('owner', 'key', 'same', source, 'prepared'))
        await asyncio.wait_for(entered.wait(), 1)
        with pytest.raises(PieceContractError) as error:
            await preview._shared_model_receipt('owner', 'key',
                'different' if changed == 'fingerprint' else 'same',
                other if changed == 'callable' else source, 'other-prepared')
        assert error.value.code == 'PIECE_CONFLICT'
        assert calls == [('first', 'prepared')]
        release.set(); assert await first == 'first-receipt'
    asyncio.run(run())


@pytest.mark.parametrize('second_owner,second_key', [('another-owner', 'key'), ('owner', 'another-key')])
def test_different_owners_or_keys_never_share_source_material(second_owner, second_key):
    async def run():
        release = asyncio.Event(); calls = []
        async def source(value):
            calls.append(value); await release.wait(); return value
        first = asyncio.create_task(preview._shared_model_receipt('owner', 'key', 'same', source, 'first-material'))
        second = asyncio.create_task(preview._shared_model_receipt(second_owner, second_key, 'same', source, 'second-material'))
        await asyncio.sleep(0); await asyncio.sleep(0)
        assert sorted(calls) == ['first-material', 'second-material']
        release.set()
        assert await first == 'first-material' and await second == 'second-material'
    asyncio.run(run())


def test_cancelling_one_waiter_keeps_the_other_waiter_and_provider_alive():
    async def run():
        entered, release, cancelled = asyncio.Event(), asyncio.Event(), asyncio.Event()
        calls = []
        async def source(value):
            calls.append(value); entered.set()
            try: await release.wait()
            except asyncio.CancelledError: cancelled.set(); raise
            return 'shared-receipt'
        first = asyncio.create_task(preview._shared_model_receipt('owner', 'key', 'same', source, 'material'))
        await asyncio.wait_for(entered.wait(), 1)
        second = asyncio.create_task(preview._shared_model_receipt('owner', 'key', 'same', source, 'material'))
        await asyncio.sleep(0)
        first.cancel()
        with pytest.raises(asyncio.CancelledError): await first
        assert not cancelled.is_set() and not second.done()
        assert calls == ['material']
        release.set(); assert await second == 'shared-receipt'
    asyncio.run(run())


def test_all_cancelled_waiters_cancel_provider_and_release_the_slot():
    async def run():
        entered, cancelled = asyncio.Event(), asyncio.Event()
        calls = []
        async def source(value):
            calls.append(value); entered.set()
            try: await asyncio.Event().wait()
            except asyncio.CancelledError: cancelled.set(); raise
        first = asyncio.create_task(preview._shared_model_receipt('owner', 'key', 'same', source, 'material'))
        await asyncio.wait_for(entered.wait(), 1)
        second = asyncio.create_task(preview._shared_model_receipt('owner', 'key', 'same', source, 'material'))
        await asyncio.sleep(0)
        first.cancel(); second.cancel()
        results = await asyncio.gather(first, second, return_exceptions=True)
        assert all(isinstance(result, asyncio.CancelledError) for result in results)
        await asyncio.wait_for(cancelled.wait(), 1)
        assert calls == ['material'] and not preview._MODEL_INFLIGHT
    asyncio.run(run())


def test_provider_failure_releases_the_slot_and_is_not_retried_automatically():
    async def run():
        calls = []
        async def source(value):
            calls.append(value); raise RuntimeError('synthetic-provider-failure')
        with pytest.raises(RuntimeError):
            await preview._shared_model_receipt('owner', 'key', 'same', source, 'material')
        assert calls == ['material'] and not preview._MODEL_INFLIGHT
        with pytest.raises(RuntimeError):
            await preview._shared_model_receipt('owner', 'key', 'same', source, 'material')
        assert calls == ['material', 'material']
    asyncio.run(run())


def test_capacity_rejection_does_not_start_another_provider(monkeypatch):
    monkeypatch.setattr(preview, '_MAX_MODEL_INFLIGHT', 1)
    async def run():
        entered, release = asyncio.Event(), asyncio.Event(); calls = []
        async def source(value):
            calls.append(value); entered.set(); await release.wait(); return value
        first = asyncio.create_task(preview._shared_model_receipt('owner', 'key', 'same', source, 'first'))
        await asyncio.wait_for(entered.wait(), 1)
        with pytest.raises(PieceContractError) as error:
            await preview._shared_model_receipt('owner', 'second-key', 'same', source, 'second')
        assert error.value.code == 'PIECE_TEMPORARILY_UNAVAILABLE'
        assert calls == ['first']
        release.set(); assert await first == 'first'
    asyncio.run(run())


@pytest.mark.parametrize('boundary', ['runtime', 'cancel', 'cancel-ignored'])
def test_late_candidate_after_runtime_stop_or_request_cancellation_never_reaches_issuance(monkeypatch, boundary):
    from test_b05b_piece_visual_change import Adapter, request
    adapter = Adapter(tier='free')
    async def run():
        entered, release, cancelled = asyncio.Event(), asyncio.Event(), asyncio.Event()
        enabled = True; calls = {'model': 0, 'prepare': 0, 'rpc': 0}
        async def source(prepared):
            calls['model'] += 1; entered.set()
            try: await release.wait()
            except asyncio.CancelledError:
                cancelled.set()
                if boundary != 'cancel-ignored': raise
            return object()  # No cancelled/stopped result may reach adoption.
        async def load_record(*args): return None
        async def rpc(*args): calls['rpc'] += 1; pytest.fail('late candidate attempted a preview write')
        async def prepare(*args, **kwargs):
            calls['prepare'] += 1; pytest.fail('late candidate entered body adoption')
        def require_current():
            if not enabled: raise PieceContractError('PIECE_FEATURE_DISABLED')
        service = preview.PiecePreviewService(source_adapter=adapter, model_source=source)
        monkeypatch.setattr(service, 'prepare_original', prepare)
        task = asyncio.create_task(service.issue_original(None, request(adapter.handoff),
            idempotency_key='independent-model-boundary', ttl_seconds=600,
            renderer_version='synthetic-renderer.v1', allowed_renderers=('synthetic-renderer.v1',),
            expected_subscription_tier='free', load_record=load_record, rpc=rpc,
            require_current=require_current))
        await asyncio.wait_for(entered.wait(), 1)
        if boundary == 'runtime':
            enabled = False; release.set()
            with pytest.raises(PieceContractError): await task
        else:
            task.cancel()
            with pytest.raises(asyncio.CancelledError): await task
            await asyncio.wait_for(cancelled.wait(), 1)
        await asyncio.sleep(0)
        assert calls == {'model': 1, 'prepare': 0, 'rpc': 0}
        assert not preview._MODEL_INFLIGHT
    asyncio.run(run())


@pytest.mark.parametrize('change,status,code', [
    ('ttl', 409, 'PIECE_CONFLICT'),
    ('renderer', 409, 'PIECE_CONFLICT'),
    ('feature', 503, 'PIECE_FEATURE_DISABLED'),
])
def test_http_runtime_change_while_model_is_pending_prevents_rpc_dispatch(monkeypatch, change, status, code):
    import httpx
    from fastapi import FastAPI
    import api_piece_v2 as api
    import supabase_client
    from test_b05b_piece_visual_change import Adapter, request
    adapter = Adapter(tier='free')
    owner = adapter.handoff.original.authenticated_owner_id
    async def run():
        entered, release = asyncio.Event(), asyncio.Event()
        calls = {'model': 0, 'quota': 0, 'prepare': 0, 'rpc': 0}
        async def source(prepared):
            calls['model'] += 1; entered.set(); await release.wait(); return object()
        async def load_record(*args): return None
        async def verify(authorization):
            assert authorization == 'Bearer independent-http-owner'
            return owner
        async def quota_rpc(name, args, *, timeout):
            assert name == 'piece_read_quota_v2' and args == {'p_owner_user_id': owner}
            calls['quota'] += 1
            return httpx.Response(200, json=dict(subscription_tier='free', saved_count=0,
                server_now='2026-11-09T00:00:00+00:00'))
        async def rpc(*args):
            calls['rpc'] += 1; pytest.fail('runtime-changed HTTP dispatched a preview RPC')
        async def prepare(*args, **kwargs):
            calls['prepare'] += 1; pytest.fail('runtime-changed HTTP adopted a late body')
        service = preview.PiecePreviewService(source_adapter=adapter, model_source=source)
        original_issue = service.issue_original
        async def issue(*args, **kwargs):
            return await original_issue(*args, **kwargs, load_record=load_record)
        monkeypatch.setattr(service, 'issue_original', issue)
        monkeypatch.setattr(service, 'prepare_original', prepare)
        monkeypatch.setattr(preview, 'PiecePreviewService', lambda: service)
        monkeypatch.setattr(api, '_verify_bearer', verify)
        monkeypatch.setattr(api, '_preview_rpc', rpc)
        monkeypatch.setattr(supabase_client, 'sb_post_rpc', quota_rpc)
        app = FastAPI()
        app.state.piece_v2_runtime = dict(requested=dict(piece_v2_preview_enabled=True),
                                        ready=dict(piece_v2_preview_enabled=True))
        app.state.piece_preview_runtime = dict(ttl_seconds=600, renderer_version='synthetic-renderer.v1')
        app.include_router(api.router)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://isolated') as client:
            pending = asyncio.create_task(client.post('/emotion/piece/preview', json=request(adapter.handoff),
                headers={'Authorization': 'Bearer independent-http-owner', 'Idempotency-Key': 'same-http-key'}))
            await asyncio.wait_for(entered.wait(), 1)
            if change == 'ttl': app.state.piece_preview_runtime['ttl_seconds'] = 601
            elif change == 'renderer': app.state.piece_preview_runtime['renderer_version'] = 'another-renderer.v2'
            else: app.state.piece_v2_runtime['requested']['piece_v2_preview_enabled'] = False
            release.set()
            response = await pending
        assert response.status_code == status and response.json() == {'code': code}
        assert response.headers['cache-control'] == 'no-store'
        assert calls == {'model': 1, 'quota': 1, 'prepare': 0, 'rpc': 0}
        assert not preview._MODEL_INFLIGHT
    asyncio.run(run())


def test_completed_acquisition_is_shared_until_the_first_issuance_acknowledgement(monkeypatch):
    """Simulated SQL ACK wait; actual service lifetime, not SQL atomicity."""
    from test_b05b_piece_visual_change import Adapter, request
    adapter = Adapter(tier='free')
    async def run():
        first_rpc, second_rpc, release = asyncio.Event(), asyncio.Event(), asyncio.Event()
        receipt = object(); calls = {'model': 0, 'rpc': 0, 'prepare': 0}
        async def source(prepared): calls['model'] += 1; return receipt
        async def load_record(*args): return None  # No committed row yet.
        async def prepare(authorization, value, *, _model_input):
            calls['prepare'] += 1
            assert _model_input.receipt is receipt
            return preview.PreparedPiecePreview(adapter.handoff, b'{}')
        async def rpc(name, args):
            assert name == 'piece_issue_preview_v2'
            calls['rpc'] += 1
            (first_rpc if calls['rpc'] == 1 else second_rpc).set()
            await release.wait()
            return {'synthetic_ack': True}
        async def issue_prepared(authorization, value, prepared, **options):
            # Preserve the real service's guarded dispatch callback; only the
            # downstream persistence/record projection is replaced here.
            return await options['rpc']('piece_issue_preview_v2', {})
        services = [preview.PiecePreviewService(source_adapter=adapter, model_source=source) for _ in range(2)]
        for service in services:
            monkeypatch.setattr(service, 'prepare_original', prepare)
            monkeypatch.setattr(service, 'issue_prepared_original', issue_prepared)
        options = dict(idempotency_key='same-acquisition-and-issuance', ttl_seconds=600,
            renderer_version='synthetic-renderer.v1', allowed_renderers=('synthetic-renderer.v1',),
            expected_subscription_tier='free', load_record=load_record, rpc=rpc)
        first = asyncio.create_task(services[0].issue_original(None, request(adapter.handoff), **options))
        await asyncio.wait_for(first_rpc.wait(), 1)
        assert calls == {'model': 1, 'rpc': 1, 'prepare': 1}
        second = asyncio.create_task(services[1].issue_original(None, request(adapter.handoff), **options))
        await asyncio.wait_for(second_rpc.wait(), 1)
        assert calls == {'model': 1, 'rpc': 2, 'prepare': 2}
        release.set()
        assert await first == await second == {'synthetic_ack': True}
        assert not preview._MODEL_INFLIGHT
    asyncio.run(run())
