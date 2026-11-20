"""The final three POSTs can use the remaining history budget without resetting it."""
import asyncio
import json

import httpx
import pytest

import analysis_cumulative_service as service
import analysis_model_source as sources
from test_analysis_merge_response_parser import exchange, planned


@pytest.mark.parametrize('history_seconds, expected_final', [(None, 22), (243, 45), (210, 12)])
def test_history_merge_shares_remaining_time_across_provider_posts(monkeypatch, history_seconds, expected_final):
    stage, _ = planned()
    messages_and_replies = [exchange(phase) for phase in ('PLAN', 'NODES')]
    budgets = []
    model = 'test-model'
    monkeypatch.setenv('COCOLON_ANALYSIS_OBSERVED_MODE', 'development')

    async def scenario():
        clock = asyncio.get_running_loop()
        real_time = clock.time
        elapsed = 0
        monkeypatch.setattr(clock, 'time', lambda: real_time() + elapsed)
        async def handler(request):
            nonlocal elapsed
            body = json.loads(request.content)
            budgets.append(body['generation_seconds'])
            assert request.extensions['timeout']['read'] <= sources.SEMANTIC_HTTP_TIMEOUT_SECONDS
            if len(budgets) == 3:
                raise asyncio.CancelledError
            messages, _, reply, _ = messages_and_replies[len(budgets)-1]
            assert body['messages'] == messages
            # Close to B57's sequential PLAN + NODES time including transport/admission.
            elapsed += (75, 118)[len(budgets)-1]
            return httpx.Response(200, json={'model': model, 'usage': {'completion_tokens': 20},
                'choices': [{'finish_reason': 'stop', 'message': {'role': 'assistant',
                    'content': json.dumps(reply, ensure_ascii=False)}}]})

        transport = sources.SelfHostedSemanticAnalysisModelSource(endpoint='https://test.invalid/chat/completions',
            api_key='test', model=model, semantic_prompt_version=stage.prompt_version,
            transport=httpx.MockTransport(handler))
        end = clock.time() + history_seconds if history_seconds is not None else None
        with pytest.raises(asyncio.CancelledError):
            await service._model_response(transport, stage, merge_deadline=end)

    asyncio.run(scenario())
    assert len(budgets) == 3
    assert budgets[0] <= 210
    assert expected_final - 2 < budgets[2] <= expected_final


def test_late_phase_response_is_rejected_even_when_whole_history_has_time(monkeypatch):
    stage, _ = planned()
    _, _, plan, _ = exchange('PLAN')
    calls = []
    model = 'test-model'
    monkeypatch.setenv('COCOLON_ANALYSIS_OBSERVED_MODE', 'development')

    async def scenario():
        clock = asyncio.get_running_loop()
        real_time = clock.time
        elapsed = 0
        monkeypatch.setattr(clock, 'time', lambda: real_time() + elapsed)

        async def late_reply(request):
            nonlocal elapsed
            calls.append(request)
            # A transport may return before the event loop delivers its cancellation.
            elapsed = sources.SEMANTIC_HTTP_TIMEOUT_SECONDS + 1
            return httpx.Response(200, json={'model': model, 'usage': {'completion_tokens': 20},
                'choices': [{'finish_reason': 'stop', 'message': {'role': 'assistant',
                    'content': json.dumps(plan, ensure_ascii=False)}}]})

        transport = sources.SelfHostedSemanticAnalysisModelSource(endpoint='https://test.invalid/chat/completions',
            api_key='test', model=model, semantic_prompt_version=stage.prompt_version,
            transport=httpx.MockTransport(late_reply))
        with pytest.raises(TimeoutError, match='analysis_model_source_timeout'):
            await transport(stage, pipeline_deadline=clock.time() + 500)

    asyncio.run(scenario())
    assert len(calls) == 1
