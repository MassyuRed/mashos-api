"""Opt-in self-hosted Analysis transport; original material stays Analysis-owned.

No Emlis reply, alternate provider, prompt rewrite, or model selection.
The normal application remains finite unless its own server setting opts in.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from functools import lru_cache
import hashlib
import json
import logging
from math import ceil
import os
from urllib.parse import urlsplit

import httpx

from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import (
    SEMANTIC_MAP_MAX_PROMPT_BYTES as SEMANTIC_MAX_PROMPT_BYTES,
    SEMANTIC_HISTORY_MERGE_MAX_PROMPT_BYTES as SEMANTIC_MERGE_MAX_PROMPT_BYTES,
)

logger = logging.getLogger(__name__)

SELECTOR = 'self_hosted.v1'
SEMANTIC_SELECTOR = 'self_hosted.semantic.v1'
SEMANTIC_EVENT_PLAN_MODEL = 'cocolon-qwen3.5-4b-analysis-event-plan-v1'
SEMANTIC_EVENT_PLAN_V2_MODEL = 'cocolon-qwen3.5-4b-analysis-event-plan-v2'
SEMANTIC_EVENT_PLAN_V2_BASE_MODEL = 'cocolon-qwen3.5-4b-analysis-event-plan-v2-base-851bf6e'
SEMANTIC_NODE_LOCAL_V3_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v3'
SEMANTIC_NODE_LOCAL_V3_BASE_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v3-base-851bf6e'
SEMANTIC_NODE_LOCAL_V4_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4'
SEMANTIC_NODE_LOCAL_V4_BOUND_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-bound-roots'
SEMANTIC_OCCURRENCE_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-occurrence-v1'
SEMANTIC_OCCURRENCE_V2_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-occurrence-v2'
SEMANTIC_OCCURRENCE_V3_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-occurrence-v3'
SEMANTIC_OCCURRENCE_V4_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-occurrence-v4'
SEMANTIC_OCCURRENCE_V5_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-occurrence-v5'
SEMANTIC_OCCURRENCE_V6_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-occurrence-v6'
SEMANTIC_OCCURRENCE_V7_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-occurrence-v7'
SEMANTIC_OCCURRENCE_V8_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-occurrence-v8'
SEMANTIC_OCCURRENCE_V9_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-occurrence-v9'
SEMANTIC_OCCURRENCE_V10_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-occurrence-v10'
SEMANTIC_OCCURRENCE_V11_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-occurrence-v11'
SEMANTIC_OCCURRENCE_V12_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-occurrence-v12'
SEMANTIC_OCCURRENCE_V13_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-occurrence-v13'
SEMANTIC_OCCURRENCE_V14_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-occurrence-v14'
SEMANTIC_OCCURRENCE_V15_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-occurrence-v15'
SEMANTIC_OCCURRENCE_V16_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-occurrence-v16'
SEMANTIC_OCCURRENCE_V17_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-occurrence-v17'
SEMANTIC_OCCURRENCE_V18_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-occurrence-v18'
SEMANTIC_OCCURRENCE_V19_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-occurrence-v19'
SEMANTIC_OCCURRENCE_V20_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-occurrence-v20'
SEMANTIC_OCCURRENCE_V21_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-occurrence-v21'
SEMANTIC_OCCURRENCE_V22_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-occurrence-v22'
SEMANTIC_OCCURRENCE_V23_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-occurrence-v23'
SEMANTIC_OCCURRENCE_V24_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-occurrence-v24'
SEMANTIC_OCCURRENCE_V24_9B_MODEL = 'cocolon-qwen3.5-9b-analysis-node-local-v4-occurrence-v24'
SEMANTIC_ANALYSIS_9B_MODEL = 'cocolon-qwen3.5-9b-analysis'
SEMANTIC_NODE_LOCAL_V4_BOUND_V2_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-bound-roots-v2'
SEMANTIC_EVENT_PLAN_BASE_MODEL = 'cocolon-qwen3.5-4b-analysis-semantic-120u'
MAX_RESPONSE_BYTES = 262144
DEFAULT_PROMPT_VERSION = 'selected_material.v4'
EXPLICIT_PROMPT_VERSIONS = frozenset({DEFAULT_PROMPT_VERSION, 'selected_material.v7'})

# These transport byte limits are separate from the native tokenizer/context limit.
SEMANTIC_LEAF_MAX_PROMPT_BYTES = 16384
SEMANTIC_MAX_REQUEST_BYTES = 262144
SEMANTIC_HISTORY_MAX_LEAVES = 16
# Leave response/serialization time after the native 210s generation limit
# and the bridge's 215s upstream limit. These are independent of output quality.
SEMANTIC_HTTP_TIMEOUT_SECONDS = 220.0
SEMANTIC_V4_RESPONSE_RESERVE_SECONDS = 5.0
SEMANTIC_REQUEST_TIMEOUT_SECONDS = 225.0
# The shared deadline for all profiles except multi-stage v24 history.
# Long v24 histories bound source operations and each of at most 51 native phases.
SEMANTIC_PIPELINE_TIMEOUT_SECONDS = 840.0


class AnalysisDirectHistoryPromptTooLarge(RuntimeError):
    """A whole-history v24 request grew beyond its bound after PLAN was admitted."""


class AnalysisModelRateLimited(RuntimeError):
    """The analysis provider has temporarily exhausted its capacity."""

    def __init__(self, retry_after):
        super().__init__('analysis_model_rate_limited')
        self.retry_after = 0
        if retry_after:
            retry_after = retry_after.strip()
            try:
                if retry_after.isascii() and retry_after.isdecimal() and len(retry_after) <= 9:
                    self.retry_after = int(retry_after)
                else:
                    deadline = parsedate_to_datetime(retry_after)
                    if deadline.tzinfo is not None:
                        seconds = (deadline - datetime.now(timezone.utc)).total_seconds()
                        self.retry_after = max(0, ceil(seconds))
            except (ValueError, OverflowError):
                pass


def _semantic_message_bytes(prepared):
    return len(json.dumps(prepared.messages(), ensure_ascii=False,
        separators=(',', ':'), allow_nan=False).encode('utf-8'))


def semantic_analysis_input_fits(prepared):
    """Message-byte admission; the serving owner still checks actual tokens."""
    maximum = (SEMANTIC_MERGE_MAX_PROMPT_BYTES if getattr(prepared, 'kind', None) == 'MERGE'
        else SEMANTIC_MAX_PROMPT_BYTES)
    if getattr(prepared, 'kind', None) == 'MERGE':
        from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
        if core.semantic_node_local_v4_uses_compact_merge(prepared):
            messages = core.semantic_node_local_v4_wire_messages(prepared)
            return len(core.semantic_map_canonical(messages).encode()) <= maximum
    return _semantic_message_bytes(prepared) <= maximum


def semantic_history_leaf_target_fits(prepared):
    """Packing target only; an indivisible cohort keeps the transport limit."""
    return _semantic_message_bytes(prepared) <= SEMANTIC_LEAF_MAX_PROMPT_BYTES


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
                    if response.status_code == 429:
                        raise AnalysisModelRateLimited(response.headers.get('Retry-After'))
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
        except AnalysisModelRateLimited:
            raise
        except (httpx.HTTPError, httpx.InvalidURL, ValueError, TypeError, KeyError, UnicodeError, RuntimeError):
            raise RuntimeError('analysis_model_source_unavailable') from None


class SelfHostedSemanticAnalysisModelSource(SelfHostedAnalysisModelSource):
    """One source-bound acquisition, including admitted cumulative stages.

    Uses the same private self-hosted endpoint, without the old quotation-only
    parser. An invalid or interrupted synthesis never becomes a finite map.
    """
    def __init__(self, *, endpoint, model, api_key, transport=None,
            semantic_prompt_version='semantic_map.v1'):
        from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import (
            SEMANTIC_MAP_PROFILE, SEMANTIC_MAP_SOURCE_DUTIES_PROFILE, SEMANTIC_MAP_EVENT_PLAN_PROFILE,
            SEMANTIC_MAP_EVENT_PLAN_V2_PROFILE, SEMANTIC_MAP_NODE_LOCAL_V3_PROFILE,
            SEMANTIC_MAP_NODE_LOCAL_V4_PROFILES, SEMANTIC_MAP_OCCURRENCE_V24_PROFILE)
        if type(semantic_prompt_version) is not str or semantic_prompt_version not in {
                SEMANTIC_MAP_PROFILE, SEMANTIC_MAP_SOURCE_DUTIES_PROFILE, SEMANTIC_MAP_EVENT_PLAN_PROFILE,
                SEMANTIC_MAP_EVENT_PLAN_V2_PROFILE, SEMANTIC_MAP_NODE_LOCAL_V3_PROFILE,
                *SEMANTIC_MAP_NODE_LOCAL_V4_PROFILES}:
            raise ValueError('analysis_model_configuration_invalid')
        if model == SEMANTIC_OCCURRENCE_V24_9B_MODEL and semantic_prompt_version != SEMANTIC_MAP_OCCURRENCE_V24_PROFILE:
            raise ValueError('analysis_model_configuration_invalid')
        super().__init__(endpoint=endpoint, model=model, api_key=api_key, transport=transport)
        self._prompt_version = semantic_prompt_version

    async def _node_local_v4(self, prepared, *, pipeline_deadline=None, per_phase=False):
        """Exactly three acquisitions, with a bounded deadline for every HTTP call.

        All unmodified raw/finish/message hashes survive in the final private
        artifact. This is structural assembly, not one sequence or a repair.
        Failure/cancellation never starts a later phase, retry or fallback.
        """
        from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
        core.require(semantic_analysis_input_fits(prepared), 'analysis_semantic_history_capacity_exceeded')
        loop = asyncio.get_running_loop()
        receipts, plan, nodes = [], None, None
        compact_merge = core.semantic_node_local_v4_uses_compact_merge(prepared)
        # Legacy callers may pass the remaining history clock to a compact merge.
        # Long v24 histories instead start a finite stream clock at each admitted phase.
        if per_phase:
            core.require(prepared.prompt_version == core.SEMANTIC_MAP_OCCURRENCE_V24_PROFILE
                and getattr(prepared, 'kind', None) in ('LEAF', 'MERGE') and pipeline_deadline is None,
                'analysis_semantic_phase_scope_invalid')
        end = None if per_phase else loop.time() + SEMANTIC_HTTP_TIMEOUT_SECONDS
        if compact_merge:
            from analysis_merge_wire import VERSION, legacy_messages, response_codec
            from analysis_plan_source_choices import uses_attributed_context, uses_speaker_context
            if pipeline_deadline is not None:
                end = min(pipeline_deadline, loop.time() +
                    len(core.SEMANTIC_MAP_NODE_LOCAL_V4_PHASES) * SEMANTIC_HTTP_TIMEOUT_SECONDS)
        remaining_tokens = core.SEMANTIC_MAP_NODE_LOCAL_V4_TOKEN_BUDGET
        maximum = SEMANTIC_MERGE_MAX_PROMPT_BYTES if getattr(prepared, 'kind', None) == 'MERGE' else SEMANTIC_MAX_PROMPT_BYTES
        phase, stage, status = 'PLAN', 'prepare', None
        prompt_bytes = request_bytes = None
        try:
            async with asyncio.timeout_at(end), httpx.AsyncClient(transport=self._transport, follow_redirects=False,
                    trust_env=False) as client:
                for phase in core.SEMANTIC_MAP_NODE_LOCAL_V4_PHASES:
                    stage, status = 'token_budget', None
                    prompt_bytes = request_bytes = None
                    if per_phase:
                        if asyncio.current_task().cancelling():
                            raise asyncio.CancelledError
                        phase_end = loop.time() + SEMANTIC_HTTP_TIMEOUT_SECONDS
                    if remaining_tokens <= 0:
                        raise RuntimeError('analysis_model_source_token_budget_exhausted')
                    tokens = remaining_tokens
                    stage = 'prompt_build'
                    messages = core.semantic_node_local_v4_wire_messages(prepared, phase, plan=plan, nodes=nodes)
                    stage = 'prompt_bytes'
                    prompt_bytes = len(core.semantic_map_canonical(messages).encode())
                    if prompt_bytes > maximum:
                        if (phase != 'PLAN' and type(prepared) is core.AnalysisSemanticMapInput
                                and prepared.prompt_version == core.SEMANTIC_MAP_OCCURRENCE_V24_PROFILE
                                and len(prepared.frozen.members) >= 2):
                            raise AnalysisDirectHistoryPromptTooLarge('analysis_model_source_unavailable')
                        raise core.AnalysisSemanticError('analysis_semantic_history_capacity_exceeded')
                    stage = 'deadline'
                    if not per_phase:
                        phase_end = min(end, loop.time() + SEMANTIC_HTTP_TIMEOUT_SECONDS)
                    remaining = phase_end - loop.time()
                    if remaining <= SEMANTIC_V4_RESPONSE_RESERVE_SECONDS:
                        raise TimeoutError('analysis_model_source_timeout')
                    body = dict(model=self.model, messages=messages, temperature=0, max_tokens=tokens,
                        stream=False, chat_template_kwargs={'enable_thinking': False},
                        generation_seconds=min(210.0, remaining - SEMANTIC_V4_RESPONSE_RESERVE_SECONDS))
                    stage = 'request_bytes'
                    request_bytes = len(core.semantic_map_canonical(body).encode())
                    core.require(request_bytes <= SEMANTIC_MAX_REQUEST_BYTES,
                        'analysis_semantic_history_capacity_exceeded')
                    stage = 'transport'
                    async with asyncio.timeout_at(phase_end), client.stream('POST', self.endpoint,
                            headers={'Authorization': 'Bearer ' + self._api_key}, json=body,
                            timeout=httpx.Timeout(remaining, connect=min(15.0, remaining))) as response:
                        stage, status = 'http_status', response.status_code
                        if status == 429:
                            raise AnalysisModelRateLimited(response.headers.get('Retry-After'))
                        if status != 200:
                            raise RuntimeError('analysis_model_source_unavailable')
                        stage = 'response_read'
                        payload = bytearray()
                        async for chunk in response.aiter_bytes(chunk_size=16384):
                            payload.extend(chunk)
                            if len(payload) > MAX_RESPONSE_BYTES:
                                raise ValueError('phase_response_too_large')
                    if loop.time() >= phase_end:
                        raise TimeoutError('analysis_model_source_timeout')
                    stage = 'response_json'
                    data = json.loads(payload)
                    # A heartbeat commits HTTP 200 before the native result.
                    if data == {'error': 'analysis_bridge_unavailable', 'status': 503}:
                        stage = 'bridge_unavailable'
                        raise ValueError('phase_bridge_unavailable')
                    stage = 'response_model'
                    if type(data) is not dict or data.get('model') != self.model:
                        raise ValueError('phase_model_changed')
                    stage = 'response_choices'
                    choices = data.get('choices')
                    if type(choices) is not list or len(choices) != 1 or type(choices[0]) is not dict:
                        raise ValueError('phase_choice_invalid')
                    choice, message = choices[0], choices[0].get('message')
                    finish_reason = choice.get('finish_reason')
                    if finish_reason != 'stop':
                        stage = 'generation_length' if finish_reason == 'length' else 'generation_finish'
                        raise ValueError('phase_not_complete')
                    stage = 'response_message'
                    if (type(message) is not dict or message.get('role') != 'assistant' or message.get('tool_calls')
                            or message.get('function_call') or message.get('reasoning_content')):
                        raise ValueError('phase_not_complete')
                    stage = 'response_content'
                    if type(message.get('content')) is not str or not message['content'].strip():
                        raise ValueError('phase_not_complete')
                    raw = message['content']
                    stage = 'response_usage'
                    usage = data.get('usage')
                    completion = usage.get('completion_tokens') if type(usage) is dict else None
                    if type(completion) is not int or not 1 <= completion <= tokens:
                        raise ValueError('phase_usage_invalid')
                    remaining_tokens -= completion
                    receipts.append(dict(phase=phase, messages_sha256=core.semantic_map_hash(messages),
                        raw=raw, raw_sha256=hashlib.sha256(raw.encode()).hexdigest(),
                        finish_reason='stop', completion_tokens=completion))
                    if compact_merge:
                        receipts[-1]['logical_messages_sha256'] = core.semantic_map_hash(legacy_messages(messages))
                    stage = 'phase_json'
                    value = core._load(raw)
                    if compact_merge:
                        stage = 'phase_wire'
                        codec = response_codec(messages)
                        if codec is not None:
                            value = codec.decode(value)
                    stage = 'phase_admission'
                    if phase == 'PLAN':
                        plan = core.admit_semantic_node_local_v4_plan_response(prepared, value,
                            merge_anchors=compact_merge, merge_action_sources=compact_merge, context_sources=compact_merge,
                            distinct_context_sources=compact_merge, speaker_context_sources=compact_merge and uses_speaker_context(VERSION),
                            attributed_context_sources=compact_merge and uses_attributed_context(VERSION))
                    elif phase == 'NODES':
                        from analysis_plan_source_choices import single_original_leaf
                        fresh_leaf = (prepared.prompt_version == core.SEMANTIC_MAP_OCCURRENCE_V24_PROFILE
                                      and getattr(prepared, 'kind', None) == 'LEAF'
                                      and single_original_leaf(json.loads(prepared.material_json)))
                        nodes = core.admit_semantic_node_local_v4_nodes_response(
                            prepared, plan, value, bound_titles=compact_merge or fresh_leaf, ordered_titles=compact_merge)
                    else:
                        core.semantic_node_local_v4_relations(prepared, plan, nodes, value, ordered_titles=compact_merge)
                    if per_phase:
                        stage = 'checkpoint'
                        if loop.time() >= phase_end:
                            raise TimeoutError('analysis_model_source_timeout')
                        from analysis_job_progress import checkpoint_v24_phase
                        async with asyncio.timeout(SEMANTIC_REQUEST_TIMEOUT_SECONDS):
                            await checkpoint_v24_phase()
            phase, stage, status = 'ASSEMBLE', 'artifact', None
            artifact = dict(schema_version=core.semantic_node_local_v4_artifact_schema(prepared), phases=receipts)
            if compact_merge:
                artifact['merge_wire_version'] = VERSION
            if per_phase:
                async with asyncio.timeout(SEMANTIC_REQUEST_TIMEOUT_SECONDS):
                    await asyncio.to_thread(core.assemble_semantic_node_local_v4, prepared, artifact)
            else:
                core.assemble_semantic_node_local_v4(prepared, artifact)
            if end is not None and loop.time() >= end:
                raise TimeoutError('analysis_model_source_timeout')
            raw = core.semantic_map_canonical(artifact)
            if len(raw.encode()) > MAX_RESPONSE_BYTES:
                raise ValueError('artifact_too_large')
            result = core.AnalysisModelQuotedParentUnitsResponse(prepared.request_ref,
                core.semantic_map_hash(prepared.messages()), hashlib.sha256(raw.encode()).hexdigest(), 'stop', raw)
            if end is not None and loop.time() >= end:
                raise TimeoutError('analysis_model_source_timeout')
            return result
        except (httpx.TimeoutException, TimeoutError):
            logger.warning('analysis_model_acquisition_failed phase=%s stage=%s http_status=%s timeout=true',
                phase, stage, status)
            raise TimeoutError('analysis_model_source_timeout') from None
        except (httpx.HTTPError, ValueError, TypeError, KeyError, UnicodeError, RuntimeError) as exc:
            # Only the semantic validator's fixed codes are safe to include.
            reason = str(exc) if isinstance(exc, core.AnalysisSemanticMapError) else None
            logger.warning('analysis_model_acquisition_failed phase=%s stage=%s http_status=%s reason=%s '
                'remaining_tokens=%s prompt_bytes=%s prompt_limit=%s request_bytes=%s request_limit=%s',
                phase, stage, status, reason, remaining_tokens, prompt_bytes, maximum,
                request_bytes, SEMANTIC_MAX_REQUEST_BYTES)
            if isinstance(exc, (AnalysisDirectHistoryPromptTooLarge, AnalysisModelRateLimited)):
                raise
            raise RuntimeError('analysis_model_source_unavailable') from None

    async def __call__(self, prepared, *, pipeline_deadline=None, per_phase=False):
        from analysis_semantic_map import SemanticMapInput
        from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import (
            AnalysisModelQuotedParentUnitsResponse, AnalysisSemanticMapStageInput,
            SEMANTIC_MAP_NODE_LOCAL_V4_PROFILES, SEMANTIC_MAP_OCCURRENCE_V24_PROFILE, digest, require)
        if per_phase:
            require(self.prompt_version == SEMANTIC_MAP_OCCURRENCE_V24_PROFILE,
                'analysis_semantic_phase_scope_invalid')
        require(type(prepared) in {SemanticMapInput, AnalysisSemanticMapStageInput}
            and prepared.prompt_version == self.prompt_version,
            'analysis_semantic_input_invalid')
        if self.prompt_version in SEMANTIC_MAP_NODE_LOCAL_V4_PROFILES:
            return await self._node_local_v4(prepared, pipeline_deadline=pipeline_deadline, per_phase=per_phase)
        messages = prepared.messages()
        require(semantic_analysis_input_fits(prepared), 'analysis_semantic_history_capacity_exceeded')
        body = dict(model=self.model, messages=messages, temperature=0,
            max_tokens=4096, stream=False,
            chat_template_kwargs={'enable_thinking': False})
        require(len(json.dumps(body, ensure_ascii=False, separators=(',', ':'),
            allow_nan=False).encode('utf-8')) <= SEMANTIC_MAX_REQUEST_BYTES,
            'analysis_semantic_history_capacity_exceeded')
        try:
            async with httpx.AsyncClient(transport=self._transport, follow_redirects=False,
                    trust_env=False, timeout=httpx.Timeout(SEMANTIC_HTTP_TIMEOUT_SECONDS, connect=15.0)) as client:
                async with client.stream('POST', self.endpoint,
                        headers={'Authorization': 'Bearer ' + self._api_key},
                        json=body) as response:
                    if response.status_code == 429:
                        raise AnalysisModelRateLimited(response.headers.get('Retry-After'))
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
        except AnalysisModelRateLimited:
            raise
        except (httpx.HTTPError, ValueError, TypeError, KeyError, UnicodeError, RuntimeError):
            raise RuntimeError('analysis_model_source_unavailable') from None


def _configured_semantic_prompt_version(model):
    """Only the exact candidate identity opts the application into its contract.

    This does not activate a model or change settings. Existing/default model
    identities retain the legacy profile, including otherwise unknown aliases.
    """
    from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import (
        SEMANTIC_MAP_PROFILE, SEMANTIC_MAP_EVENT_PLAN_PROFILE, SEMANTIC_MAP_EVENT_PLAN_V2_PROFILE,
        SEMANTIC_MAP_NODE_LOCAL_V3_PROFILE, SEMANTIC_MAP_NODE_LOCAL_V4_PROFILE,
        SEMANTIC_MAP_NODE_LOCAL_V4_BOUND_PROFILE, SEMANTIC_MAP_NODE_LOCAL_V4_BOUND_V2_PROFILE,
        SEMANTIC_MAP_OCCURRENCE_PROFILE, SEMANTIC_MAP_OCCURRENCE_V2_PROFILE, SEMANTIC_MAP_OCCURRENCE_V3_PROFILE,
        SEMANTIC_MAP_OCCURRENCE_V4_PROFILE, SEMANTIC_MAP_OCCURRENCE_V5_PROFILE, SEMANTIC_MAP_OCCURRENCE_V6_PROFILE,
        SEMANTIC_MAP_OCCURRENCE_V7_PROFILE, SEMANTIC_MAP_OCCURRENCE_V8_PROFILE, SEMANTIC_MAP_OCCURRENCE_V9_PROFILE,
        SEMANTIC_MAP_OCCURRENCE_V10_PROFILE, SEMANTIC_MAP_OCCURRENCE_V11_PROFILE, SEMANTIC_MAP_OCCURRENCE_V12_PROFILE, SEMANTIC_MAP_OCCURRENCE_V13_PROFILE, SEMANTIC_MAP_OCCURRENCE_V14_PROFILE, SEMANTIC_MAP_OCCURRENCE_V15_PROFILE, SEMANTIC_MAP_OCCURRENCE_V16_PROFILE, SEMANTIC_MAP_OCCURRENCE_V17_PROFILE, SEMANTIC_MAP_OCCURRENCE_V18_PROFILE, SEMANTIC_MAP_OCCURRENCE_V19_PROFILE, SEMANTIC_MAP_OCCURRENCE_V20_PROFILE, SEMANTIC_MAP_OCCURRENCE_V21_PROFILE, SEMANTIC_MAP_OCCURRENCE_V22_PROFILE, SEMANTIC_MAP_OCCURRENCE_V23_PROFILE, SEMANTIC_MAP_OCCURRENCE_V24_PROFILE)
    if model in (SEMANTIC_OCCURRENCE_V24_MODEL, SEMANTIC_OCCURRENCE_V24_9B_MODEL):
        return SEMANTIC_MAP_OCCURRENCE_V24_PROFILE
    if model == SEMANTIC_OCCURRENCE_V23_MODEL:
        return SEMANTIC_MAP_OCCURRENCE_V23_PROFILE
    if model == SEMANTIC_OCCURRENCE_V22_MODEL:
        return SEMANTIC_MAP_OCCURRENCE_V22_PROFILE
    if model == SEMANTIC_OCCURRENCE_V21_MODEL:
        return SEMANTIC_MAP_OCCURRENCE_V21_PROFILE
    if model == SEMANTIC_OCCURRENCE_V20_MODEL:
        return SEMANTIC_MAP_OCCURRENCE_V20_PROFILE
    if model == SEMANTIC_OCCURRENCE_V19_MODEL:
        return SEMANTIC_MAP_OCCURRENCE_V19_PROFILE
    if model == SEMANTIC_OCCURRENCE_V18_MODEL:
        return SEMANTIC_MAP_OCCURRENCE_V18_PROFILE
    if model == SEMANTIC_OCCURRENCE_V17_MODEL:
        return SEMANTIC_MAP_OCCURRENCE_V17_PROFILE
    if model == SEMANTIC_OCCURRENCE_V16_MODEL:
        return SEMANTIC_MAP_OCCURRENCE_V16_PROFILE
    if model == SEMANTIC_OCCURRENCE_V15_MODEL:
        return SEMANTIC_MAP_OCCURRENCE_V15_PROFILE
    if model == SEMANTIC_OCCURRENCE_V14_MODEL:
        return SEMANTIC_MAP_OCCURRENCE_V14_PROFILE
    if model == SEMANTIC_OCCURRENCE_V13_MODEL:
        return SEMANTIC_MAP_OCCURRENCE_V13_PROFILE
    if model == SEMANTIC_OCCURRENCE_V12_MODEL:
        return SEMANTIC_MAP_OCCURRENCE_V12_PROFILE
    if model == SEMANTIC_OCCURRENCE_V11_MODEL:
        return SEMANTIC_MAP_OCCURRENCE_V11_PROFILE
    if model == SEMANTIC_OCCURRENCE_V10_MODEL:
        return SEMANTIC_MAP_OCCURRENCE_V10_PROFILE
    if model == SEMANTIC_OCCURRENCE_V9_MODEL:
        return SEMANTIC_MAP_OCCURRENCE_V9_PROFILE
    if model == SEMANTIC_OCCURRENCE_V8_MODEL:
        return SEMANTIC_MAP_OCCURRENCE_V8_PROFILE
    if model == SEMANTIC_OCCURRENCE_V7_MODEL:
        return SEMANTIC_MAP_OCCURRENCE_V7_PROFILE
    if model == SEMANTIC_OCCURRENCE_V6_MODEL:
        return SEMANTIC_MAP_OCCURRENCE_V6_PROFILE
    if model == SEMANTIC_OCCURRENCE_V5_MODEL:
        return SEMANTIC_MAP_OCCURRENCE_V5_PROFILE
    if model == SEMANTIC_OCCURRENCE_V4_MODEL:
        return SEMANTIC_MAP_OCCURRENCE_V4_PROFILE
    if model == SEMANTIC_OCCURRENCE_V3_MODEL:
        return SEMANTIC_MAP_OCCURRENCE_V3_PROFILE
    if model == SEMANTIC_OCCURRENCE_V2_MODEL:
        return SEMANTIC_MAP_OCCURRENCE_V2_PROFILE
    if model == SEMANTIC_OCCURRENCE_MODEL:
        return SEMANTIC_MAP_OCCURRENCE_PROFILE
    if model == SEMANTIC_NODE_LOCAL_V4_BOUND_V2_MODEL:
        return SEMANTIC_MAP_NODE_LOCAL_V4_BOUND_V2_PROFILE
    if model == SEMANTIC_NODE_LOCAL_V4_BOUND_MODEL:
        return SEMANTIC_MAP_NODE_LOCAL_V4_BOUND_PROFILE
    if model == SEMANTIC_NODE_LOCAL_V4_MODEL:
        return SEMANTIC_MAP_NODE_LOCAL_V4_PROFILE
    if model in {SEMANTIC_NODE_LOCAL_V3_MODEL, SEMANTIC_NODE_LOCAL_V3_BASE_MODEL}:
        return SEMANTIC_MAP_NODE_LOCAL_V3_PROFILE
    if model in {SEMANTIC_EVENT_PLAN_V2_MODEL, SEMANTIC_EVENT_PLAN_V2_BASE_MODEL}:
        return SEMANTIC_MAP_EVENT_PLAN_V2_PROFILE
    return SEMANTIC_MAP_EVENT_PLAN_PROFILE if model == SEMANTIC_EVENT_PLAN_MODEL else SEMANTIC_MAP_PROFILE


def analysis_primary_structure_reading_mode():
    if os.getenv('COCOLON_ANALYSIS_PLAN_READ_ROLLOUT') == 'free_plus.v1':
        return 'free_plus.v1'
    if os.getenv('COCOLON_ANALYSIS_PRIMARY_STRUCTURE_READING') == 'karen.v3':
        return 'karen.v3'
    return None


def analysis_premium_structure_relations_enabled():
    return (analysis_primary_structure_reading_mode() == 'free_plus.v1'
            and os.getenv('COCOLON_ANALYSIS_PREMIUM_RELATION_ROLLOUT') == 'grounded.v1')


def analysis_model_primary_structure_reading(source):
    if analysis_primary_structure_reading_mode() is None:
        return False
    if type(source) is _ApplicationSemanticAnalysisSource:
        model = source._settings[2]
    elif type(source) is SelfHostedSemanticAnalysisModelSource:
        model = source.model
    else:
        return False
    # Only the rehearsed 9B Map identity can request the extra response field.
    return 'karen.v3' if model == SEMANTIC_OCCURRENCE_V24_9B_MODEL else False


def analysis_model_prompt_version(source):
    """Only an explicitly constructed transport opts in; callbacks stay v4.

    Avoid generic attribute lookup: AsyncMock and other callback objects may
    synthesize attributes that are not a declared transport configuration.
    Quotation-only application sources stay v4. Semantic application sources
    use the exact configured model identity; their four-setting identity is unchanged.
    """
    if is_semantic_analysis_model_source(source):
        return source.prompt_version
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
        if selector != SELECTOR or model == SEMANTIC_OCCURRENCE_V24_9B_MODEL:
            raise RuntimeError('analysis_model_configuration_invalid')
        try:
            source = SelfHostedAnalysisModelSource(endpoint=endpoint, model=model, api_key=api_key)
        except ValueError:
            raise RuntimeError('analysis_model_configuration_invalid') from None
        response = await source(prepared)
        self.require_current()
        return response


class _ApplicationSemanticAnalysisSource(_ApplicationAnalysisSource):
    @property
    def prompt_version(self):
        return _configured_semantic_prompt_version(self._settings[2])

    async def __call__(self, prepared, *, pipeline_deadline=None, per_phase=False):
        self.require_current()
        selector, endpoint, model, api_key = self._settings
        if selector != SEMANTIC_SELECTOR:
            raise RuntimeError('analysis_model_configuration_invalid')
        try:
            source = SelfHostedSemanticAnalysisModelSource(endpoint=endpoint, model=model, api_key=api_key,
                semantic_prompt_version=self.prompt_version)
        except ValueError:
            raise RuntimeError('analysis_model_configuration_invalid') from None
        response = await source(prepared, pipeline_deadline=pipeline_deadline, per_phase=per_phase)
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

