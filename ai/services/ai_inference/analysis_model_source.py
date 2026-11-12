"""Opt-in self-hosted Analysis transport; original material stays Analysis-owned.

No Emlis reply, provider fallback, retry, prompt rewrite, or model selection.
The normal application remains finite unless its own server setting opts in.
"""
from __future__ import annotations

from functools import lru_cache
import hashlib
import json
import os
from urllib.parse import urlsplit

import httpx

SELECTOR = 'self_hosted.v1'
SEMANTIC_SELECTOR = 'self_hosted.semantic.v1'
MAX_RESPONSE_BYTES = 262144
DEFAULT_PROMPT_VERSION = 'selected_material.v4'
EXPLICIT_PROMPT_VERSIONS = frozenset({DEFAULT_PROMPT_VERSION, 'selected_material.v7'})


class SelfHostedAnalysisModelSource:
    def __init__(self, *, endpoint, model, api_key, transport=None, prompt_version=DEFAULT_PROMPT_VERSION):
        if any(type(v) is not str for v in (endpoint, model, api_key)):
            raise ValueError('analysis_model_configuration_invalid')
        if type(prompt_version) is not str or prompt_version not in EXPLICIT_PROMPT_VERSIONS:
            raise ValueError('analysis_model_configuration_invalid')
        self._prompt_version = prompt_version
        parsed = urlsplit(endpoint)
        if (parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password
                or parsed.query or parsed.fragment or not parsed.path.endswith('/chat/completions')
                or endpoint != endpoint.strip() or not model or model != model.strip()
                or not api_key or not api_key.strip()):
            raise ValueError('analysis_model_configuration_invalid')
        self.endpoint, self.model, self._api_key = endpoint, model, api_key
        self._transport = transport

    @property
    def prompt_version(self):
        return self._prompt_version

    async def __call__(self, prepared):
        from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import (
            AnalysisModelQuotedParentUnitsInput, AnalysisModelQuotedParentUnitsResponse,
            digest, require, require_analysis_model_observed_scope)
        require(type(prepared) is AnalysisModelQuotedParentUnitsInput
            and prepared.response is None and prepared.prompt_version == self.prompt_version,
            'analysis_quoted_parent_units_binding_invalid')
        require_analysis_model_observed_scope(prepared.request)
        messages = prepared.messages()
        messages_hash = digest(messages)
        try:
            async with httpx.AsyncClient(transport=self._transport, follow_redirects=False,
                    trust_env=False, timeout=httpx.Timeout(25.0)) as client:
                async with client.stream('POST', self.endpoint,
                        headers={'Authorization': 'Bearer ' + self._api_key},
                        json=dict(model=self.model, messages=messages, temperature=0,
                            max_tokens=2048, stream=False,
                            chat_template_kwargs={'enable_thinking': False})) as response:
                    if response.status_code != 200:
                        raise RuntimeError('analysis_model_source_unavailable')
                    body = bytearray()
                    async for chunk in response.aiter_bytes(chunk_size=16384):
                        body.extend(chunk)
                        if len(body) > MAX_RESPONSE_BYTES:
                            raise RuntimeError('analysis_model_source_unavailable')
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
            raise TimeoutError('analysis_model_source_timeout') from None
        except (httpx.HTTPError, httpx.InvalidURL, ValueError, TypeError, KeyError, UnicodeError, RuntimeError):
            raise RuntimeError('analysis_model_source_unavailable') from None


class SelfHostedSemanticAnalysisModelSource(SelfHostedAnalysisModelSource):
    """One source-bound synthesis call for the complete semantic map.

    Uses the same private self-hosted endpoint, without the old quotation-only
    parser. An invalid or interrupted synthesis never becomes a finite map.
    """
    def __init__(self, *, endpoint, model, api_key, transport=None,
            semantic_prompt_version='semantic_map.v1'):
        from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import (
            SEMANTIC_MAP_PROFILE, SEMANTIC_MAP_SOURCE_DUTIES_PROFILE)
        if type(semantic_prompt_version) is not str or semantic_prompt_version not in {
                SEMANTIC_MAP_PROFILE, SEMANTIC_MAP_SOURCE_DUTIES_PROFILE}:
            raise ValueError('analysis_model_configuration_invalid')
        super().__init__(endpoint=endpoint, model=model, api_key=api_key, transport=transport)
        self._prompt_version = semantic_prompt_version

    async def __call__(self, prepared):
        from analysis_semantic_map import SemanticMapInput
        from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import (
            AnalysisModelQuotedParentUnitsResponse, digest, require)
        require(type(prepared) is SemanticMapInput and prepared.prompt_version == self.prompt_version,
            'analysis_semantic_input_invalid')
        messages = prepared.messages()
        try:
            async with httpx.AsyncClient(transport=self._transport, follow_redirects=False,
                    trust_env=False, timeout=httpx.Timeout(210.0, connect=15.0)) as client:
                async with client.stream('POST', self.endpoint,
                        headers={'Authorization': 'Bearer ' + self._api_key},
                        json=dict(model=self.model, messages=messages, temperature=0,
                            max_tokens=4096, stream=False,
                            chat_template_kwargs={'enable_thinking': False})) as response:
                    if response.status_code != 200:
                        raise RuntimeError('analysis_model_source_unavailable')
                    body = bytearray()
                    async for chunk in response.aiter_bytes(chunk_size=16384):
                        body.extend(chunk)
                        if len(body) > MAX_RESPONSE_BYTES:
                            raise RuntimeError('analysis_model_source_unavailable')
            data = json.loads(body)
            if type(data) is not dict or data.get('model') != self.model:
                raise ValueError
            choices = data.get('choices')
            if type(choices) is not list or len(choices) != 1 or type(choices[0]) is not dict:
                raise ValueError
            choice, message = choices[0], choices[0].get('message')
            if (choice.get('finish_reason') != 'stop' or type(message) is not dict
                    or message.get('role') != 'assistant' or message.get('tool_calls')
                    or message.get('function_call') or message.get('reasoning_content')
                    or type(message.get('content')) is not str or not message['content'].strip()):
                raise ValueError
            raw = message['content']
            return AnalysisModelQuotedParentUnitsResponse(prepared.request_ref, digest(messages),
                hashlib.sha256(raw.encode('utf-8')).hexdigest(), 'stop', raw)
        except httpx.TimeoutException:
            raise TimeoutError('analysis_model_source_timeout') from None
        except (httpx.HTTPError, ValueError, TypeError, KeyError, UnicodeError, RuntimeError):
            raise RuntimeError('analysis_model_source_unavailable') from None


def analysis_model_prompt_version(source):
    """Only an explicitly constructed transport opts in; callbacks stay v4.

    Avoid generic attribute lookup: AsyncMock and other callback objects may
    synthesize attributes that are not a declared transport configuration.
    The application factory and its environment/settings identity stay v4.
    """
    if is_semantic_analysis_model_source(source):
        return source.prompt_version if type(source) is SelfHostedSemanticAnalysisModelSource else 'semantic_map.v1'
    return source.prompt_version if type(source) is SelfHostedAnalysisModelSource else DEFAULT_PROMPT_VERSION


def _settings():
    return (os.environ.get('COCOLON_ANALYSIS_MODEL_SOURCE', '').strip(),
        os.environ.get('COCOLON_ANALYSIS_MODEL_ENDPOINT', ''),
        os.environ.get('COCOLON_ANALYSIS_MODEL', ''),
        os.environ.get('COCOLON_ANALYSIS_MODEL_API_KEY', ''))


class _ApplicationAnalysisSource:
    def __init__(self, settings):
        self._settings = settings

    def require_current(self):
        if self._settings != _settings():
            raise RuntimeError('analysis_model_configuration_changed')

    async def __call__(self, prepared):
        self.require_current()
        selector, endpoint, model, api_key = self._settings
        if selector != SELECTOR:
            raise RuntimeError('analysis_model_configuration_invalid')
        try:
            source = SelfHostedAnalysisModelSource(endpoint=endpoint, model=model, api_key=api_key)
        except ValueError:
            raise RuntimeError('analysis_model_configuration_invalid') from None
        response = await source(prepared)
        self.require_current()
        return response


class _ApplicationSemanticAnalysisSource(_ApplicationAnalysisSource):
    async def __call__(self, prepared):
        self.require_current()
        selector, endpoint, model, api_key = self._settings
        if selector != SEMANTIC_SELECTOR:
            raise RuntimeError('analysis_model_configuration_invalid')
        try:
            source = SelfHostedSemanticAnalysisModelSource(endpoint=endpoint, model=model, api_key=api_key)
        except ValueError:
            raise RuntimeError('analysis_model_configuration_invalid') from None
        response = await source(prepared)
        self.require_current()
        return response


def is_semantic_analysis_model_source(source):
    return type(source) in {SelfHostedSemanticAnalysisModelSource, _ApplicationSemanticAnalysisSource}


@lru_cache(maxsize=1)
def _configured_source(settings):
    # A stable callable is required by ensure_map's existing in-flight sharing.
    # The one retained settings tuple is private; never log/cache user material.
    return (_ApplicationSemanticAnalysisSource(settings)
        if settings[0] == SEMANTIC_SELECTOR else _ApplicationAnalysisSource(settings))


def application_analysis_model_source():
    settings = _settings()
    if settings[0] in {'', 'off'}:
        return None
    # Defer validation to actual acquisition: saved maps must remain readable
    # even with a missing key, bad URL, or unsupported enabled selector.
    return _configured_source(settings)


def require_current_analysis_model_source(source):
    if type(source) in {_ApplicationAnalysisSource, _ApplicationSemanticAnalysisSource}:
        source.require_current()

