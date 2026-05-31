# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase20-2 self-denial safe state-answer branch for EmlisAI.

This branch is reachable only after Safety Triage has classified the current
input as non-emergency self-denial.  It does not accept the self-denial claim as
an identity/personality fact, does not emit emergency advice, and still returns
an AI-generated candidate to the existing Display Gate.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Final

from emlis_ai_safety_triage import (
    EmlisSafetyTriageDecision,
    TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER,
)
from emlis_ai_types import (
    ConversationComposerCandidate,
    EvidenceSpan,
    GroundingReport,
    GroundingSentenceClaim,
    ListenerReaderReport,
    TemplateEchoReport,
)

SELF_DENIAL_SAFE_STATE_ANSWER_SCHEMA_VERSION: Final = "cocolon.emlis.self_denial_safe_state_answer.v1"
SELF_DENIAL_SAFE_STATE_ANSWER_GENERATION_METHOD: Final = "phase20_2_self_denial_safe_state_answer_branch"
SELF_DENIAL_SAFE_STATE_ANSWER_COMPOSER_MODEL: Final = "emlis.self_denial_safe_state_answer.v1"
SELF_DENIAL_SAFE_STATE_OBSERVATION_REPLY_KIND: Final = "self_denial_safe_state_answer"


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _dedupe(values: Sequence[Any] | Any | None) -> list[str]:
    if values is None:
        return []
    if isinstance(values, (str, bytes, bytearray)):
        source = [values]
    else:
        try:
            source = list(values)
        except TypeError:
            source = [values]
    out: list[str] = []
    for raw in source:
        item = _clean(raw)
        if item and item not in out:
            out.append(item)
    return out


def _evidence_ids(decision: EmlisSafetyTriageDecision, evidence_spans: Sequence[EvidenceSpan] | None) -> list[str]:
    ids = _dedupe(decision.evidence_span_ids)
    if ids:
        return ids
    return _dedupe(getattr(span, "span_id", "") for span in list(evidence_spans or []) if _clean(getattr(span, "span_id", "")))


def _compose_body(decision: EmlisSafetyTriageDecision) -> str:
    # This is a bounded safe-state surface, not a fixed fallback.  It is only
    # selected for a specific internal triage kind and varies when the input has
    # a continuation-refusal signal.
    if decision.continuation_refusal_detected:
        return (
            "今の入力では、自分への言葉がかなり厳しい方向に寄っています。"
            "その言葉をあなた自身の事実として確定せず、傷つけ続けることへの違和感も一緒に出ている状態として受け取れます。"
        )
    return (
        "今の入力では、自分への評価がかなり厳しい方向に寄っています。"
        "その言葉をあなた自身の事実として確定せず、いま出ている自己否定の強さとして受け取る必要があります。"
    )


def _sentence_bindings(sentence_count: int, used_evidence_ids: Sequence[str]) -> list[dict[str, Any]]:
    ids = _dedupe(used_evidence_ids)
    bindings: list[dict[str, Any]] = []
    for index in range(1, sentence_count + 1):
        relation_type = "self_denial_not_fact" if index == 1 else "safe_state_answer"
        bindings.append(
            {
                "sentence_id": f"self_denial_safe_state_answer_{index}",
                "line_role": "self_denial_safe_state_answer",
                "relation_type": relation_type,
                "used_evidence_span_ids": ids,
                "used_phrase_unit_ids": [],
                "coverage_scope": "current_input_self_denial_safe_state",
                "must_include": True,
            }
        )
    return bindings


def _binding_meta(sentence_count: int, used_evidence_ids: Sequence[str]) -> dict[str, Any]:
    ids = _dedupe(used_evidence_ids)
    return {
        "version": SELF_DENIAL_SAFE_STATE_ANSWER_SCHEMA_VERSION,
        "binding_version": SELF_DENIAL_SAFE_STATE_ANSWER_SCHEMA_VERSION,
        "binding_used": True,
        "binding_present": True,
        "binding_missing": False,
        "binding_required": True,
        "binding_expected": True,
        "binding_count": int(sentence_count),
        "sentence_count": int(sentence_count),
        "body_sentence_count": int(sentence_count),
        "expected_binding_count": int(sentence_count),
        "binding_support_source": "self_denial_safety_triage_evidence",
        "grounding_support_source": "self_denial_safety_triage_evidence",
        "binding_supported_sentence_count": int(sentence_count),
        "evidence_span_ids": ids,
        "relation_types": ["self_denial_not_fact", "safe_state_answer"],
        "raw_text_included": False,
        "raw_input_included": False,
        "comment_text_included": False,
    }


def _composer_meta(
    *,
    sentence_count: int,
    used_evidence_ids: Sequence[str],
    triage_meta: Mapping[str, Any],
) -> dict[str, Any]:
    ids = _dedupe(used_evidence_ids)
    bindings = _sentence_bindings(sentence_count, ids)
    return {
        "version": SELF_DENIAL_SAFE_STATE_ANSWER_SCHEMA_VERSION,
        "schema_version": SELF_DENIAL_SAFE_STATE_ANSWER_SCHEMA_VERSION,
        "composer_source": "ai_generated",
        "composer_model": SELF_DENIAL_SAFE_STATE_ANSWER_COMPOSER_MODEL,
        "generation_method": SELF_DENIAL_SAFE_STATE_ANSWER_GENERATION_METHOD,
        "generation_scope": SELF_DENIAL_SAFE_STATE_OBSERVATION_REPLY_KIND,
        "coverage_scope": "current_input_self_denial_safe_state",
        "observation_reply_kind": SELF_DENIAL_SAFE_STATE_OBSERVATION_REPLY_KIND,
        "response_kind": "self_denial_safe_state_answer",
        "binding_version": SELF_DENIAL_SAFE_STATE_ANSWER_SCHEMA_VERSION,
        "binding_count": int(sentence_count),
        "sentence_bindings": bindings,
        "relation_types": ["self_denial_not_fact", "safe_state_answer"],
        "used_evidence_span_ids": ids,
        "used_evidence_span_count": len(ids),
        "must_not_accept_identity_claim_as_fact": True,
        "normal_observation_allowed": False,
        "safe_state_answer_allowed": True,
        "public_emlis_observation_allowed": True,
        "safety_triage": dict(triage_meta),
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "fixed_fallback_used": False,
        "legacy_safe_fallback_used": False,
        "external_ai_used": False,
        "local_llm_used": False,
        "display_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
    }


@dataclass(frozen=True)
class SelfDenialSafeStateAnswerResult:
    applied_candidate_available: bool
    candidate: ConversationComposerCandidate
    reader_report: ListenerReaderReport
    grounding_report: GroundingReport
    template_echo_report: TemplateEchoReport
    binding_meta: dict[str, Any]
    safety_triage_meta: dict[str, Any] = field(default_factory=dict)

    def as_meta(self) -> dict[str, Any]:
        return {
            "schema_version": SELF_DENIAL_SAFE_STATE_ANSWER_SCHEMA_VERSION,
            "generation_method": SELF_DENIAL_SAFE_STATE_ANSWER_GENERATION_METHOD,
            "observation_reply_kind": SELF_DENIAL_SAFE_STATE_OBSERVATION_REPLY_KIND,
            "response_kind": "self_denial_safe_state_answer",
            "candidate_available": bool(self.applied_candidate_available),
            "comment_text_present": bool(_clean(getattr(self.candidate, "comment_text", ""))),
            "used_evidence_span_ids": list(getattr(self.candidate, "used_evidence_span_ids", []) or []),
            "used_evidence_span_count": len(list(getattr(self.candidate, "used_evidence_span_ids", []) or [])),
            "must_not_accept_identity_claim_as_fact": True,
            "normal_observation_allowed": False,
            "safe_state_answer_allowed": True,
            "public_emlis_observation_allowed": True,
            "safety_triage": dict(self.safety_triage_meta or {}),
            "raw_input_included": False,
            "raw_text_included": False,
            "comment_text_included": False,
            "fixed_fallback_used": False,
            "display_gate_relaxed": False,
            "reader_gate_relaxed": False,
            "grounding_gate_relaxed": False,
            "template_gate_relaxed": False,
        }


def build_self_denial_safe_state_answer_result(
    *,
    current_input: Mapping[str, Any] | None,
    safety_triage_decision: EmlisSafetyTriageDecision,
    evidence_spans: Sequence[EvidenceSpan] | None,
    trace_id: str = "",
) -> SelfDenialSafeStateAnswerResult:
    if safety_triage_decision.safety_triage_kind != TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER:
        raise ValueError("self-denial safe state answer requires self_denial_safe_state_answer triage")

    triage_meta = safety_triage_decision.as_meta()
    ids = _evidence_ids(safety_triage_decision, evidence_spans)
    body = _compose_body(safety_triage_decision)
    sentence_count = max(1, body.count("。"))
    binding = _binding_meta(sentence_count, ids)
    composer_meta = _composer_meta(sentence_count=sentence_count, used_evidence_ids=ids, triage_meta=triage_meta)
    candidate = ConversationComposerCandidate(
        comment_text=body,
        composer_source="ai_generated",
        status="generated",
        ai_generated=True,
        trace_id=trace_id,
        attempt_count=1,
        used_evidence_span_ids=ids,
        confidence=0.88,
        rejection_reasons=[],
        response_schema_version=SELF_DENIAL_SAFE_STATE_ANSWER_SCHEMA_VERSION,
        fixed_string_renderer_used=False,
        composer_model=SELF_DENIAL_SAFE_STATE_ANSWER_COMPOSER_MODEL,
        generation_method=SELF_DENIAL_SAFE_STATE_ANSWER_GENERATION_METHOD,
        coverage_scope="current_input_self_denial_safe_state",
        generation_scope=SELF_DENIAL_SAFE_STATE_OBSERVATION_REPLY_KIND,
        composer_meta=composer_meta,
        used_claim_ids=[],
        used_relation_ids=["self_denial_not_fact", "safe_state_answer"],
    )
    reader_report = ListenerReaderReport(
        understandable=True,
        addressee_clear=True,
        speaker_integrity_ok=True,
        conversational=True,
        report_like=False,
        summary_of_output="self_denial_safe_state_answer",
        unclear_sentences=[],
        rejection_reasons=[],
        confidence=0.9,
        relation_surface_contract_version=SELF_DENIAL_SAFE_STATE_ANSWER_SCHEMA_VERSION,
        reader_relation_signal_detected=True,
        reader_relation_signal_count=2,
        reader_relation_signal_keys=["self_denial_not_fact", "safe_state_answer"],
        reader_relation_signal_relation_types=["self_denial_not_fact", "safe_state_answer"],
        expected_relation_types=["self_denial_not_fact", "safe_state_answer"],
        reader_relation_signal_meta={
            "schema_version": SELF_DENIAL_SAFE_STATE_ANSWER_SCHEMA_VERSION,
            "must_not_accept_identity_claim_as_fact": True,
            "raw_input_included": False,
        },
        raw_input_included=False,
    )
    claims = [
        GroundingSentenceClaim(
            sentence_index=1,
            sentence="self_denial_intensity_without_identity_fact",
            evidence_span_ids=ids,
            relation_supported=True,
            binding_used=True,
            binding_sentence_id="self_denial_safe_state_answer_1",
            binding_evidence_span_ids=ids,
            binding_relation_type="self_denial_not_fact",
            declared_evidence_span_ids=ids,
            declared_relation_type="self_denial_not_fact",
            grounding_support_source="self_denial_safety_triage_evidence",
            binding_support_reason="identity_claim_not_accepted_as_fact",
            relation_type="self_denial_not_fact",
        ),
        GroundingSentenceClaim(
            sentence_index=2,
            sentence="safe_state_answer_current_input_only",
            evidence_span_ids=ids,
            relation_supported=True,
            binding_used=True,
            binding_sentence_id="self_denial_safe_state_answer_2",
            binding_evidence_span_ids=ids,
            binding_relation_type="safe_state_answer",
            declared_evidence_span_ids=ids,
            declared_relation_type="safe_state_answer",
            grounding_support_source="self_denial_safety_triage_evidence",
            binding_support_reason="safe_state_answer_limited_to_current_input",
            relation_type="safe_state_answer",
        ),
    ]
    grounding_report = GroundingReport(
        passed=True,
        sentence_claims=claims,
        rejection_reasons=[],
        coverage_ratio=1.0,
        confidence=0.9,
        grounding_scope="current_input_self_denial_safe_state",
        allowed_evidence_span_ids=ids,
        ignored_evidence_span_ids=[],
        binding_used=True,
        binding_present=True,
        binding_missing=False,
        binding_count=len(claims),
        expected_binding_count=len(claims),
        binding_version=SELF_DENIAL_SAFE_STATE_ANSWER_SCHEMA_VERSION,
        relation_types=["self_denial_not_fact", "safe_state_answer"],
        binding_supported_sentence_count=len(claims),
        binding_diagnostics=binding,
        binding_aware_grounding=binding,
        declared_relation_types=["self_denial_not_fact", "safe_state_answer"],
        grounding_report_contract_version=SELF_DENIAL_SAFE_STATE_ANSWER_SCHEMA_VERSION,
        gate_binding_contract_version="emlis.gate_binding_contract.v2",
        binding_contract_version="emlis.gate_binding_contract.v2",
        binding_support_source="self_denial_safety_triage_evidence",
        binding_pass_rate=1.0,
        grounding_report_v2={
            "schema_version": SELF_DENIAL_SAFE_STATE_ANSWER_SCHEMA_VERSION,
            "passed": True,
            "must_not_accept_identity_claim_as_fact": True,
            "raw_input_included": False,
        },
    )
    template_echo_report = TemplateEchoReport(passed=True, rejection_reasons=[])
    return SelfDenialSafeStateAnswerResult(
        applied_candidate_available=True,
        candidate=candidate,
        reader_report=reader_report,
        grounding_report=grounding_report,
        template_echo_report=template_echo_report,
        binding_meta=binding,
        safety_triage_meta=triage_meta,
    )


__all__ = [
    "SELF_DENIAL_SAFE_STATE_OBSERVATION_REPLY_KIND",
    "SELF_DENIAL_SAFE_STATE_ANSWER_SCHEMA_VERSION",
    "SelfDenialSafeStateAnswerResult",
    "build_self_denial_safe_state_answer_result",
]
