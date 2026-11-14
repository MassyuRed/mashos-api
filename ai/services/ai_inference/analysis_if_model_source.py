"""One IF proposal call through the existing private Analysis configuration.

No fallback, training, retry or remote request occurs at import/factory time.
The Analysis owner alone prepares/adopts hypothetical meaning; this transport
only returns the same source-bound raw receipt used by the existing model arm.
"""
from __future__ import annotations

import hashlib
import json
import httpx

from analysis_model_source import (SelfHostedAnalysisModelSource, _settings,
    SELECTOR, SEMANTIC_SELECTOR, MAX_RESPONSE_BYTES)


class SelfHostedAnalysisIfModelSource(SelfHostedAnalysisModelSource):
    def __init__(self, *, endpoint, model, api_key, transport=None, settings_snapshot=None):
        super().__init__(endpoint=endpoint, model=model, api_key=api_key, transport=transport)
        self._settings_snapshot = settings_snapshot

    def _current(self):
        if self._settings_snapshot is not None and self._settings_snapshot != _settings():
            raise RuntimeError('analysis_if_model_configuration_changed')

    async def __call__(self, prepared):
        from cocolon_meaning_experience_engine.cores.analysis.if_route_contracts import AnalysisIfModelPrepared
        from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import AnalysisModelQuotedParentUnitsResponse, digest
        if type(prepared) is not AnalysisIfModelPrepared:
            raise ValueError('analysis_if_model_request_invalid')
        self._current()
        messages = prepared.messages()
        messages_hash = digest(messages)
        try:
            async with httpx.AsyncClient(transport=self._transport, follow_redirects=False,
                    trust_env=False, timeout=httpx.Timeout(210.0, connect=15.0)) as client:
                async with client.stream('POST', self.endpoint,
                        headers={'Authorization': 'Bearer ' + self._api_key},
                        json=dict(model=self.model, messages=messages, temperature=0,
                            max_tokens=2048, stream=False,
                            chat_template_kwargs={'enable_thinking': False})) as response:
                    if response.status_code != 200:
                        raise RuntimeError('analysis_if_model_source_unavailable')
                    body = bytearray()
                    async for chunk in response.aiter_bytes(chunk_size=16384):
                        body.extend(chunk)
                        if len(body) > MAX_RESPONSE_BYTES:
                            raise RuntimeError('analysis_if_model_source_unavailable')
            self._current()
            data = json.loads(body)
            if type(data) is not dict or data.get('model') != self.model:
                raise ValueError
            choices = data.get('choices')
            if type(choices) is not list or len(choices) != 1 or type(choices[0]) is not dict:
                raise ValueError
            choice = choices[0]
            message = choice.get('message')
            if (choice.get('finish_reason') != 'stop' or type(message) is not dict
                    or message.get('role') != 'assistant' or message.get('tool_calls')
                    or message.get('function_call') or message.get('reasoning_content')
                    or type(message.get('content')) is not str or not message['content'].strip()):
                raise ValueError
            raw = message['content']
            return AnalysisModelQuotedParentUnitsResponse(prepared.request_ref, messages_hash,
                hashlib.sha256(raw.encode('utf-8')).hexdigest(), 'stop', raw)
        except httpx.TimeoutException:
            raise TimeoutError('analysis_if_model_source_timeout') from None
        except (httpx.HTTPError, ValueError, TypeError, KeyError, UnicodeError, RuntimeError):
            raise RuntimeError('analysis_if_model_source_unavailable') from None


def application_analysis_if_model_source():
    settings = _settings()
    selector, endpoint, model, api_key = settings
    if selector in {'', 'off'}:
        return None
    if selector not in {SELECTOR, SEMANTIC_SELECTOR}:
        raise RuntimeError('analysis_if_model_configuration_invalid')
    return SelfHostedAnalysisIfModelSource(endpoint=endpoint, model=model, api_key=api_key,
        settings_snapshot=settings)
