# -*- coding: utf-8 -*-
from __future__ import annotations

"""Conversation Composer boundary for EmlisAI.

Phase 6 connects the ObservationGraph to an AI composer boundary without
reintroducing runtime fixed observation sentences.  This module is allowed to
build structured request payloads, validate AI responses, and record trace
metadata.  It must not render user-facing Emlis observation text from Python
strings, role maps, f-strings, or fallback sentences.
"""

from dataclasses import asdict, is_dataclass
import ast
import inspect
import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict, List, Mapping, Optional, Protocol, Sequence, runtime_checkable

from emlis_ai_types import (
    ConversationComposerCandidate,
    EvidenceSpan,
    GraphClaim,
    ObservationGraph,
    RelationEdge,
)

_REQUEST_SCHEMA_VERSION = "emlis.composer.request.v1"
_RESPONSE_SCHEMA_VERSION = "emlis.composer.response.v1"

_FORBIDDEN_OUTPUT_SURFACES = [
    "そこには",
    "もありました",
    "も含まれていました",
    "受け取りました",
    "と思います",
    "として見ています",
    "小さく扱いません",
    "軽く扱いません",
    "今の私は",
    "あなたは",
    "あなたの",
    "あなたが",
    "あなたに",
    "言葉の流れには",
    "外からは見えにくい緊張",
    "まだ決めきれない揺れ",
    "急いで片づけず",
    "一緒に見ます",
]

_RUNTIME_RENDERER_MARKERS = [
    "_line_primary",
    "_line_pressure",
    "_line_limit",
    "_line_closing",
    "closing_template",
    "role_template",
    "static_observation_text",
]


@runtime_checkable
class ConversationComposerClient(Protocol):
    """Synchronous Composer AI client boundary used by tests/adapters."""

    def generate(self, payload: Mapping[str, Any]) -> Mapping[str, Any] | str:
        ...



def _jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(v) for v in value]
    return value



def _clean_text(value: Any) -> str:
    return str(value or "").strip()



def _graph_claim_payload(claim: GraphClaim | None) -> Dict[str, Any]:
    if claim is None:
        return {}
    return {
        "claim_id": claim.claim_id,
        "claim_type": claim.claim_type,
        "text": claim.text,
        "evidence_span_ids": list(claim.evidence_span_ids),
        "confidence": float(claim.confidence or 0.0),
    }



def _relation_payload(edge: RelationEdge) -> Dict[str, Any]:
    return {
        "edge_id": edge.edge_id,
        "from_claim_id": edge.from_claim_id,
        "to_claim_id": edge.to_claim_id,
        "relation_type": edge.relation_type,
        "evidence_span_ids": list(edge.evidence_span_ids),
        "confidence": float(edge.confidence or 0.0),
    }



def _evidence_payload(span: EvidenceSpan) -> Dict[str, Any]:
    return {
        "span_id": span.span_id,
        "raw_text": span.raw_text,
        "detected_type": span.detected_type,
        "confidence": float(span.confidence or 0.0),
        "source_field": span.source_field,
    }



def build_conversation_composer_payload(
    *,
    graph: ObservationGraph,
    evidence_spans: Sequence[EvidenceSpan],
    display_name: object = None,
    greeting_text: object = "",
    trace_id: str = "",
    attempt_count: int = 1,
    rejection_reasons: Sequence[str] | None = None,
) -> Dict[str, Any]:
    """Build the structured request sent to the Composer AI.

    The payload contains graph/evidence/constraints only.  It deliberately does
    not include example replies, fixed closing sentences, or surface templates.
    """

    addressee = graph.addressee_notes
    return {
        "schema_version": _REQUEST_SCHEMA_VERSION,
        "trace_id": str(trace_id or ""),
        "attempt_count": int(attempt_count or 1),
        "task": "conversation_composer_candidate",
        "addressee": {
            "display_name": _clean_text(display_name),
            "display_name_call": _clean_text(addressee.display_name_call),
            "greeting_text": _clean_text(greeting_text),
            "sentence_target": int(addressee.sentence_target or 5),
            "voice_distance": _clean_text(addressee.voice_distance),
            "needs_gentle_pacing": bool(addressee.needs_gentle_pacing),
            "avoid_report_like": bool(addressee.avoid_report_like),
        },
        "observation_graph": {
            "primary_state": _graph_claim_payload(graph.primary_state),
            "core_tensions": [_relation_payload(edge) for edge in graph.core_tensions],
            "pressure_sources": [_graph_claim_payload(claim) for claim in graph.pressure_sources],
            "limit_signals": [_graph_claim_payload(claim) for claim in graph.limit_signals],
            "self_awareness": [_graph_claim_payload(claim) for claim in graph.self_awareness],
            "value_or_strength_signals": [_graph_claim_payload(claim) for claim in graph.value_or_strength_signals],
            "safety_boundaries": list(graph.safety_boundaries),
            "forbidden_claims": list(graph.forbidden_claims),
            "missing_information": list(graph.missing_information),
        },
        "evidence_spans": [_evidence_payload(span) for span in evidence_spans],
        "composition_contract": {
            "produce_user_facing_text": True,
            "composer_source_required": "ai_generated",
            "do_not_use_examples": True,
            "do_not_use_fixed_templates": True,
            "do_not_use_fallback_observation": True,
            "forbidden_output_surfaces": list(_FORBIDDEN_OUTPUT_SURFACES),
            "preserve_speaker": "Emlis",
            "avoid_second_person_pronouns": True,
            "avoid_user_first_person_hijack": True,
            "return_schema_version": _RESPONSE_SCHEMA_VERSION,
            "previous_rejection_reasons": [str(item) for item in list(rejection_reasons or []) if str(item)],
        },
        "expected_response_schema": {
            "schema_version": _RESPONSE_SCHEMA_VERSION,
            "required": ["comment_text", "used_evidence_span_ids", "confidence"],
            "optional": ["response_schema_version", "composer_source"],
        },
    }



def _extract_text_from_response(response: Mapping[str, Any] | str) -> str:
    if isinstance(response, str):
        return response.strip()
    text = _clean_text(response.get("comment_text") or response.get("text"))
    if text:
        return text
    reply_lines = response.get("reply_lines") or response.get("lines")
    if isinstance(reply_lines, (list, tuple)):
        return "\n".join(_clean_text(line) for line in reply_lines if _clean_text(line)).strip()
    return ""



def _extract_used_evidence_ids(response: Mapping[str, Any] | str, allowed: set[str]) -> List[str]:
    if not isinstance(response, Mapping):
        return []
    values = response.get("used_evidence_span_ids") or response.get("used_evidence_ids") or []
    if not isinstance(values, (list, tuple, set)):
        return []
    out: List[str] = []
    for item in values:
        span_id = str(item or "").strip()
        if span_id and span_id in allowed and span_id not in out:
            out.append(span_id)
    return out



def _normalize_ai_response(
    *,
    response: Mapping[str, Any] | str,
    payload: Mapping[str, Any],
    trace_id: str,
    attempt_count: int,
    allowed_evidence_ids: set[str],
) -> ConversationComposerCandidate:
    text = _extract_text_from_response(response)
    if not text:
        return ConversationComposerCandidate(
            composer_source="empty",
            status="empty",
            trace_id=trace_id,
            attempt_count=attempt_count,
            rejection_reasons=["composer_returned_empty_text"],
            request_schema_version=str(payload.get("schema_version") or _REQUEST_SCHEMA_VERSION),
        )

    response_source = ""
    response_schema = ""
    confidence = 0.0
    if isinstance(response, Mapping):
        response_source = _clean_text(response.get("composer_source") or response.get("source"))
        response_schema = _clean_text(response.get("response_schema_version") or response.get("schema_version"))
        try:
            confidence = float(response.get("confidence") or 0.0)
        except (TypeError, ValueError):
            confidence = 0.0

    if response_source and response_source != "ai_generated":
        return ConversationComposerCandidate(
            comment_text="",
            composer_source=response_source,
            status="schema_invalid",
            trace_id=trace_id,
            attempt_count=attempt_count,
            rejection_reasons=["composer_source_not_ai_generated"],
            request_schema_version=str(payload.get("schema_version") or _REQUEST_SCHEMA_VERSION),
            response_schema_version=response_schema,
        )

    return ConversationComposerCandidate(
        comment_text=text,
        composer_source="ai_generated",
        status="generated",
        ai_generated=True,
        trace_id=trace_id,
        attempt_count=attempt_count,
        used_evidence_span_ids=_extract_used_evidence_ids(response, allowed_evidence_ids),
        confidence=confidence,
        request_schema_version=str(payload.get("schema_version") or _REQUEST_SCHEMA_VERSION),
        response_schema_version=response_schema or _RESPONSE_SCHEMA_VERSION,
        fixed_string_renderer_used=False,
    )




_COMPOSER_SYSTEM_PROMPT_JA = """あなたは Cocolon の EmlisAI Conversation Composer です。
ObservationGraph と EvidenceSpan だけを根拠に、ユーザー本人へ届く短い会話文候補を日本語で作成してください。

厳守:
- 返答は JSON object のみ。markdown、説明、コードフェンスは禁止。
- comment_text は3〜5行。最初の行は payload.addressee.greeting_text があればそれを自然に使う。
- 原文にない原因、診断、性格判断、医療判断、行動指示を足さない。
- 「あなたは/あなたの/あなたが/あなたに」を使わない。
- Emlis がユーザー本人の一人称を名乗らない。
- payload.composition_contract.forbidden_output_surfaces に含まれる表面文型を使わない。
- 観測結果の箇条書きではなく、相手に話す会話文にする。
- EvidenceSpan の raw_text を根拠として使い、ただの貼り付けや原文順の復唱にしない。

必ず次の JSON schema で返してください:
{
  "response_schema_version": "emlis.composer.response.v1",
  "composer_source": "ai_generated",
  "comment_text": "...",
  "used_evidence_span_ids": ["s1"],
  "confidence": 0.0
}
"""


def _first_env(*names: str) -> str:
    for name in names:
        value = str(os.getenv(name, "") or "").strip()
        if value:
            return value
    return ""


def _truthy_env(name: str, default: bool = False) -> bool:
    raw = str(os.getenv(name, "") or "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on", "enabled"}


def _float_env(name: str, default: float, *, low: float, high: float) -> float:
    try:
        value = float(str(os.getenv(name, "") or default))
    except Exception:
        value = default
    return max(low, min(high, value))


def _int_env(name: str, default: int, *, low: int, high: int) -> int:
    try:
        value = int(str(os.getenv(name, "") or default))
    except Exception:
        value = default
    return max(low, min(high, value))


def _join_chat_completions_url(base_or_url: str) -> str:
    url = str(base_or_url or "").strip()
    if not url:
        return ""
    if url.rstrip("/").endswith("/chat/completions"):
        return url.rstrip("/")
    return url.rstrip("/") + "/chat/completions"


class OpenAICompatibleConversationComposerClient:
    """OpenAI-compatible HTTP adapter for the Composer AI boundary.

    The adapter only transports the structured ObservationGraph/EvidenceSpan
    payload to an external AI service. It does not own user-facing observation
    sentences and never produces a rule-rendered fallback body.
    """

    def __init__(
        self,
        *,
        endpoint: str,
        api_key: str = "",
        model: str = "",
        timeout_seconds: float = 2.2,
        temperature: float = 0.55,
        max_tokens: int = 520,
        mode: str = "openai_chat",
    ) -> None:
        self.endpoint = str(endpoint or "").strip()
        self.api_key = str(api_key or "").strip()
        self.model = str(model or "").strip()
        self.timeout_seconds = float(timeout_seconds or 2.2)
        self.temperature = float(temperature or 0.55)
        self.max_tokens = int(max_tokens or 520)
        self.mode = str(mode or "openai_chat").strip() or "openai_chat"

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _post_json(self, body: Mapping[str, Any]) -> Mapping[str, Any] | str:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(self.endpoint, data=data, headers=self._headers(), method="POST")
        with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:  # nosec B310 - configured trusted endpoint
            raw = response.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(raw)
        except Exception:
            return raw
        return parsed if isinstance(parsed, Mapping) else raw

    def generate(self, payload: Mapping[str, Any]) -> Mapping[str, Any] | str:
        if not self.endpoint:
            raise RuntimeError("composer_endpoint_not_configured")
        if self.mode == "raw_payload":
            return self._post_json(payload)

        request_body: Dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": _COMPOSER_SYSTEM_PROMPT_JA},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "response_format": {"type": "json_object"},
        }
        response = self._post_json(request_body)
        if not isinstance(response, Mapping):
            return response
        choices = response.get("choices")
        if not isinstance(choices, list) or not choices:
            return response
        first = choices[0] if isinstance(choices[0], Mapping) else {}
        message = first.get("message") if isinstance(first, Mapping) else {}
        content = message.get("content") if isinstance(message, Mapping) else ""
        content_text = str(content or "").strip()
        if not content_text:
            return response
        try:
            parsed_content = json.loads(content_text)
        except Exception:
            return {"comment_text": content_text, "composer_source": "ai_generated"}
        return parsed_content if isinstance(parsed_content, Mapping) else {"comment_text": content_text, "composer_source": "ai_generated"}


def is_default_conversation_composer_configured() -> bool:
    """Return whether production has a Composer AI endpoint/key available."""

    if _truthy_env("EMLIS_AI_COMPOSER_DISABLED", default=False):
        return False
    endpoint = _first_env("EMLIS_AI_COMPOSER_ENDPOINT", "EMLIS_AI_COMPOSER_API_URL")
    api_key = _first_env("EMLIS_AI_COMPOSER_API_KEY", "OPENAI_API_KEY")
    if endpoint:
        return True
    return bool(api_key)


def get_default_conversation_composer_client() -> Optional[ConversationComposerClient]:
    """Resolve the default Composer AI client from environment variables.

    Supported runtime configuration:
    - EMLIS_AI_COMPOSER_ENDPOINT / EMLIS_AI_COMPOSER_API_URL
    - EMLIS_AI_COMPOSER_API_KEY or OPENAI_API_KEY
    - EMLIS_AI_COMPOSER_MODEL or OPENAI_MODEL
    - EMLIS_AI_COMPOSER_MODE=openai_chat|raw_payload
    """

    if not is_default_conversation_composer_configured():
        return None
    mode = _first_env("EMLIS_AI_COMPOSER_MODE") or "openai_chat"
    endpoint = _first_env("EMLIS_AI_COMPOSER_ENDPOINT", "EMLIS_AI_COMPOSER_API_URL")
    api_key = _first_env("EMLIS_AI_COMPOSER_API_KEY", "OPENAI_API_KEY")
    if mode != "raw_payload":
        endpoint = endpoint or _join_chat_completions_url(_first_env("EMLIS_AI_COMPOSER_BASE_URL", "OPENAI_BASE_URL") or "https://api.openai.com/v1")
    model = _first_env("EMLIS_AI_COMPOSER_MODEL", "OPENAI_MODEL") or "gpt-4o-mini"
    return OpenAICompatibleConversationComposerClient(
        endpoint=endpoint,
        api_key=api_key,
        model=model,
        timeout_seconds=_float_env("EMLIS_AI_COMPOSER_TIMEOUT_SECONDS", 2.2, low=0.3, high=8.0),
        temperature=_float_env("EMLIS_AI_COMPOSER_TEMPERATURE", 0.55, low=0.0, high=1.2),
        max_tokens=_int_env("EMLIS_AI_COMPOSER_MAX_TOKENS", 520, low=160, high=1200),
        mode=mode,
    )


def compose_emlis_conversation_candidate(
    *,
    graph: ObservationGraph,
    evidence_spans: Sequence[EvidenceSpan],
    display_name: object = None,
    greeting_text: object = "",
    composer_client: ConversationComposerClient | None = None,
    trace_id: str = "",
    attempt_count: int = 1,
    rejection_reasons: Sequence[str] | None = None,
) -> ConversationComposerCandidate:
    """Ask the Composer AI for a candidate and validate the response shape.

    If no Composer AI client is connected, this returns an unavailable candidate
    with empty text.  It never creates a rule-rendered fallback observation.
    """

    payload = build_conversation_composer_payload(
        graph=graph,
        evidence_spans=evidence_spans,
        display_name=display_name,
        greeting_text=greeting_text,
        trace_id=trace_id,
        attempt_count=attempt_count,
        rejection_reasons=rejection_reasons,
    )
    if composer_client is None:
        return ConversationComposerCandidate(
            composer_source="unavailable",
            status="unavailable",
            trace_id=trace_id,
            attempt_count=attempt_count,
            rejection_reasons=["composer_client_not_connected"],
            request_schema_version=_REQUEST_SCHEMA_VERSION,
        )
    try:
        response = composer_client.generate(payload)
    except Exception:
        return ConversationComposerCandidate(
            composer_source="unavailable",
            status="unavailable",
            trace_id=trace_id,
            attempt_count=attempt_count,
            rejection_reasons=["composer_client_error"],
            request_schema_version=_REQUEST_SCHEMA_VERSION,
        )
    if inspect.isawaitable(response):
        return ConversationComposerCandidate(
            composer_source="unavailable",
            status="unavailable",
            trace_id=trace_id,
            attempt_count=attempt_count,
            rejection_reasons=["composer_client_returned_awaitable_in_sync_path"],
            request_schema_version=_REQUEST_SCHEMA_VERSION,
        )
    return _normalize_ai_response(
        response=response,
        payload=payload,
        trace_id=trace_id,
        attempt_count=attempt_count,
        allowed_evidence_ids={span.span_id for span in evidence_spans},
    )



def compose_emlis_conversation(
    *,
    graph: ObservationGraph,
    evidence_spans: Sequence[EvidenceSpan],
    display_name: object = None,
    greeting_text: object = "",
    composer_client: ConversationComposerClient | None = None,
    trace_id: str = "",
) -> str:
    """Backward-compatible text accessor for tests and legacy adapters."""

    candidate = compose_emlis_conversation_candidate(
        graph=graph,
        evidence_spans=evidence_spans,
        display_name=display_name,
        greeting_text=greeting_text,
        composer_client=composer_client,
        trace_id=trace_id,
    )
    return candidate.comment_text if candidate.composer_source == "ai_generated" else ""



def audit_runtime_fixed_string_renderer() -> List[str]:
    """Return suspicious runtime renderer definitions in this module.

    The marker list itself is not a violation; a violation is a helper/function
    or assignment that could own a role-specific completed observation line.
    """

    source = inspect.getsource(inspect.getmodule(audit_runtime_fixed_string_renderer))
    tree = ast.parse(source)
    markers = set(_RUNTIME_RENDERER_MARKERS)
    findings: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in markers:
            findings.append(node.name)
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in markers:
                    findings.append(target.id)
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id in markers:
            findings.append(node.target.id)
    return sorted(set(findings))



def phase6_composer_contract_ready() -> bool:
    """Phase 6 is structurally ready when no fixed renderer markers remain."""

    return not audit_runtime_fixed_string_renderer()


__all__ = [
    "ConversationComposerClient",
    "OpenAICompatibleConversationComposerClient",
    "get_default_conversation_composer_client",
    "is_default_conversation_composer_configured",
    "build_conversation_composer_payload",
    "compose_emlis_conversation",
    "compose_emlis_conversation_candidate",
    "audit_runtime_fixed_string_renderer",
    "phase6_composer_contract_ready",
]
