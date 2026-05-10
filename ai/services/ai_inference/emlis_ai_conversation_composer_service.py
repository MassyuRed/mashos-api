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
from typing import Any, Dict, List, Mapping, Protocol, Sequence, runtime_checkable

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
    limited_observation_scope: object = None,
) -> Dict[str, Any]:
    """Build the structured request sent to the Composer AI.

    The payload contains graph/evidence/constraints only.  It deliberately does
    not include example replies, fixed closing sentences, or surface templates.
    """

    scope_meta: Dict[str, Any] = {}
    if isinstance(limited_observation_scope, Mapping):
        scope_meta = dict(limited_observation_scope)
    else:
        as_meta = getattr(limited_observation_scope, "as_meta", None)
        if callable(as_meta):
            try:
                raw_scope_meta = as_meta()
                scope_meta = dict(raw_scope_meta) if isinstance(raw_scope_meta, Mapping) else {}
            except Exception:
                scope_meta = {}

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
        "limited_observation_scope": scope_meta,
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
            "optional": [
                "response_schema_version",
                "composer_source",
                "composer_model",
                "generation_method",
                "generation_scope",
                "coverage_scope",
                "fixed_string_renderer_used",
                "used_claim_ids",
                "used_relation_ids",
            ],
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
    response_source = ""
    response_schema = ""
    composer_model = ""
    generation_method = ""
    coverage_scope = ""
    generation_scope = ""
    used_claim_ids: List[str] = []
    used_relation_ids: List[str] = []
    fixed_string_renderer_used = False
    composer_meta: Dict[str, Any] = {}
    confidence = 0.0
    if isinstance(response, Mapping):
        response_source = _clean_text(response.get("composer_source") or response.get("source"))
        response_schema = _clean_text(response.get("response_schema_version") or response.get("schema_version"))
        composer_model = _clean_text(response.get("composer_model"))
        generation_method = _clean_text(response.get("generation_method"))
        coverage_scope = _clean_text(response.get("coverage_scope"))
        generation_scope = _clean_text(response.get("generation_scope")) or generation_method
        raw_claim_ids = response.get("used_claim_ids") if isinstance(response.get("used_claim_ids"), (list, tuple, set)) else []
        raw_relation_ids = response.get("used_relation_ids") if isinstance(response.get("used_relation_ids"), (list, tuple, set)) else []
        used_claim_ids = [str(item or "").strip() for item in raw_claim_ids if str(item or "").strip()]
        used_relation_ids = [str(item or "").strip() for item in raw_relation_ids if str(item or "").strip()]
        fixed_string_renderer_used = bool(response.get("fixed_string_renderer_used"))
        raw_meta = response.get("composer_meta") or {}
        composer_meta = dict(raw_meta) if isinstance(raw_meta, Mapping) else {}
        try:
            confidence = float(response.get("confidence") or 0.0)
        except (TypeError, ValueError):
            confidence = 0.0

    text = _extract_text_from_response(response)
    if not text:
        source = response_source or "empty"
        status = "unavailable" if source == "unavailable" else "empty"
        reasons = []
        if isinstance(response, Mapping) and isinstance(response.get("rejection_reasons"), (list, tuple)):
            reasons = [str(item) for item in response.get("rejection_reasons") if str(item)]
        if not reasons:
            reasons = ["composer_returned_empty_text"]
        return ConversationComposerCandidate(
            composer_source=source,
            status=status,
            trace_id=trace_id,
            attempt_count=attempt_count,
            rejection_reasons=reasons,
            request_schema_version=str(payload.get("schema_version") or _REQUEST_SCHEMA_VERSION),
            response_schema_version=response_schema,
            composer_model=composer_model,
            generation_method=generation_method,
            coverage_scope=coverage_scope,
            generation_scope=generation_scope,
            used_claim_ids=used_claim_ids,
            used_relation_ids=used_relation_ids,
            fixed_string_renderer_used=fixed_string_renderer_used,
            composer_meta=composer_meta,
        )

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
            composer_model=composer_model,
            generation_method=generation_method,
            coverage_scope=coverage_scope,
            generation_scope=generation_scope,
            used_claim_ids=used_claim_ids,
            used_relation_ids=used_relation_ids,
            fixed_string_renderer_used=fixed_string_renderer_used,
            composer_meta=composer_meta,
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
        fixed_string_renderer_used=fixed_string_renderer_used,
        composer_model=composer_model,
        generation_method=generation_method,
        coverage_scope=coverage_scope,
        generation_scope=generation_scope,
        used_claim_ids=used_claim_ids,
        used_relation_ids=used_relation_ids,
        composer_meta=composer_meta,
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
    limited_observation_scope: object = None,
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
        limited_observation_scope=limited_observation_scope,
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
    limited_observation_scope: object = None,
) -> str:
    """Backward-compatible text accessor for tests and legacy adapters."""

    candidate = compose_emlis_conversation_candidate(
        graph=graph,
        evidence_spans=evidence_spans,
        display_name=display_name,
        greeting_text=greeting_text,
        composer_client=composer_client,
        trace_id=trace_id,
        limited_observation_scope=limited_observation_scope,
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
    "build_conversation_composer_payload",
    "compose_emlis_conversation",
    "compose_emlis_conversation_candidate",
    "audit_runtime_fixed_string_renderer",
    "phase6_composer_contract_ready",
]
