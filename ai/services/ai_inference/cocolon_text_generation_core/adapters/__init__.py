# -*- coding: utf-8 -*-
from __future__ import annotations

"""Core-specific evidence, composer, and input-contract adapters.

Runtime composer modules are exposed lazily to avoid import cycles while the
package-level ``cocolon_text_generation_core`` namespace is initialising.
"""

from .analysis_evidence_adapter import adapt_analysis_evidence_sources, convert_analysis_evidence_spans

from .analysis_composer import (
    ADAPTER_NAME as ANALYSIS_COMPOSER_ADAPTER_NAME,
    ANALYSIS_COMPOSER_CONNECTED,
    ANALYSIS_COMPOSER_META_KEY,
    ANALYSIS_COMPOSER_MODEL,
    ANALYSIS_RUNTIME_CONNECTED,
    ANALYSIS_TEXT_SAFETY_GUARD_NAME,
    ANALYSIS_VALIDITY_GATE_CONNECTED,
    COVERAGE_SCOPE_ANALYSIS_RUNTIME,
    PHASE_LABEL as ANALYSIS_COMPOSER_PHASE_LABEL,
    AnalysisComposer,
    AnalysisComposerCoreEvaluation,
    AnalysisComposerEvaluation,
    AnalysisComposerRuntimeResult,
    REJECTION_ANALYSIS_COMMON_CORE_REJECTED,
    REJECTION_ANALYSIS_COMMON_TEXT_SAFETY_REJECTED,
    REJECTION_ANALYSIS_COMPOSER_NOT_CONNECTED,
    REJECTION_ANALYSIS_OBSERVATION_SURFACE_MISSING,
    adapt_analysis_composer,
    attach_analysis_composer_meta,
    build_analysis_composer_evaluation,
    compose_analysis_report,
    compose_analysis_report_text,
    compose_analysis_text_generation,
    evaluate_analysis_composer,
    evaluate_analysis_report_text_safety,
)
from .analysis_composer_input_contract import (
    ADAPTER_NAME as ANALYSIS_COMPOSER_INPUT_CONTRACT_ADAPTER_NAME,
    ANALYSIS_CONTENT_PAYLOAD_KEYS_UNCHANGED,
    ANALYSIS_DOMAIN_EMOTION,
    ANALYSIS_DOMAIN_SELF_STRUCTURE,
    ANALYSIS_FORBIDDEN_SURFACE_PATTERNS,
    ANALYSIS_INPUT_CONTRACT_META_KEY,
    ANALYSIS_INPUT_CONTRACT_MODEL,
    COVERAGE_SCOPE_ANALYSIS,
    PAYLOAD_KIND_ANALYSIS_REPORT,
    PHASE_LABEL as ANALYSIS_COMPOSER_INPUT_CONTRACT_PHASE_LABEL,
    AnalysisComposerInputContract,
    adapt_analysis_composer_input_contract,
    adapt_analysis_report_input_contract,
    attach_analysis_input_contract_meta,
    build_analysis_composer_input_contract,
    build_analysis_core_text_payload,
    build_analysis_core_text_payloads,
    build_analysis_domain_input_contracts,
    empty_analysis_composer_input_contract,
    infer_analysis_material_fields,
    normalize_analysis_material_domain,
)
from .emlis_evidence_adapter import (
    adapt_emlis_evidence_span,
    adapt_emlis_evidence_spans,
    convert_emlis_evidence_span,
    convert_emlis_evidence_spans,
)
from .emlis_observation_composer import (
    ADAPTER_NAME as EMLIS_OBSERVATION_COMPOSER_ADAPTER_NAME,
    EMLIS_OBSERVATION_CORE_MODEL,
    EmlisObservationCoreEvaluation,
    attach_core_evaluation_meta,
    build_emlis_observation_core_payload,
    convert_emlis_phrase_unit,
    convert_emlis_phrase_units,
    convert_emlis_sentence_plan,
    convert_emlis_sentence_plans,
    core_rejection_reason,
    evaluate_emlis_observation_candidate,
)
from .piece_evidence_adapter import adapt_piece_evidence_sources, convert_piece_evidence_spans
from .piece_composer import (
    ADAPTER_NAME as PIECE_COMPOSER_ADAPTER_NAME,
    PHASE_LABEL as PIECE_COMPOSER_PHASE_LABEL,
    PIECE_COMPOSER_MODEL,
    PieceComposer,
    PieceComposerEvaluation,
    adapt_piece_composer,
    build_piece_composer_evaluation,
    build_runtime_piece_plan,
    compose_piece_answer,
    compose_piece_text_generation,
    evaluate_piece_composer,
)
from .piece_composer_input_contract import (
    ADAPTER_NAME as PIECE_COMPOSER_INPUT_CONTRACT_ADAPTER_NAME,
    LEGACY_BOUNDARY_NAMES as PIECE_LEGACY_BOUNDARY_NAMES,
    PAYLOAD_KIND_ANSWER as PIECE_PAYLOAD_KIND_ANSWER,
    PAYLOAD_KIND_QUESTION as PIECE_PAYLOAD_KIND_QUESTION,
    PIECE_FORBIDDEN_SURFACE_PATTERNS,
    PIECE_INPUT_CONTRACT_MODEL,
    PieceComposerInputContract,
    adapt_piece_composer_input_contract,
    adapt_piece_core_question_answer_plan,
    build_piece_composer_input_contract,
    build_piece_core_text_payloads,
    empty_piece_composer_input_contract,
)

_ANALYSIS_COMPOSER_EXPORTS = {
    "ANALYSIS_COMPOSER_ADAPTER_NAME": ("ADAPTER_NAME", "alias"),
    "ANALYSIS_COMPOSER_MODEL": ("ANALYSIS_COMPOSER_MODEL", "direct"),
    "COVERAGE_SCOPE_ANALYSIS_REPORT": ("COVERAGE_SCOPE_ANALYSIS_REPORT", "direct"),
    "PHASE_LABEL_ANALYSIS_COMPOSER": ("PHASE_LABEL", "alias"),
    "ANALYSIS_COMPOSER_PHASE_LABEL": ("PHASE_LABEL", "alias"),
    "TEXT_GENERATION_ANALYSIS_COMPOSER_META_KEY": ("TEXT_GENERATION_ANALYSIS_COMPOSER_META_KEY", "direct"),
    "AnalysisComposer": ("AnalysisComposer", "direct"),
    "AnalysisComposerCoreEvaluation": ("AnalysisComposerCoreEvaluation", "direct"),
    "AnalysisComposerEvaluation": ("AnalysisComposerEvaluation", "direct"),
    "AnalysisComposerRuntimeResult": ("AnalysisComposerRuntimeResult", "direct"),
    "REJECTION_ANALYSIS_COMMON_CORE_REJECTED": ("REJECTION_ANALYSIS_COMMON_CORE_REJECTED", "direct"),
    "REJECTION_ANALYSIS_COMPOSER_NOT_CONNECTED": ("REJECTION_ANALYSIS_COMPOSER_NOT_CONNECTED", "direct"),
    "REJECTION_ANALYSIS_RUNTIME_TEXT_MISSING": ("REJECTION_ANALYSIS_RUNTIME_TEXT_MISSING", "direct"),
    "adapt_analysis_composer": ("adapt_analysis_composer", "direct"),
    "attach_analysis_composer_meta": ("attach_analysis_composer_meta", "direct"),
    "build_analysis_composer_evaluation": ("build_analysis_composer_evaluation", "direct"),
    "compose_analysis_report_text": ("compose_analysis_report_text", "direct"),
    "compose_analysis_text_generation": ("compose_analysis_text_generation", "direct"),
    "evaluate_analysis_composer": ("evaluate_analysis_composer", "direct"),
}


def __getattr__(name: str):
    target = _ANALYSIS_COMPOSER_EXPORTS.get(name)
    if target is None:
        raise AttributeError(name)
    attr_name, _kind = target
    from . import analysis_composer as _analysis_composer

    value = getattr(_analysis_composer, attr_name)
    globals()[name] = value
    return value


__all__ = [
    "adapt_analysis_evidence_sources",
    "convert_analysis_evidence_spans",
    "ANALYSIS_COMPOSER_INPUT_CONTRACT_ADAPTER_NAME",
    "ANALYSIS_COMPOSER_INPUT_CONTRACT_PHASE_LABEL",
    "ANALYSIS_CONTENT_PAYLOAD_KEYS_UNCHANGED",
    "ANALYSIS_DOMAIN_EMOTION",
    "ANALYSIS_DOMAIN_SELF_STRUCTURE",
    "ANALYSIS_FORBIDDEN_SURFACE_PATTERNS",
    "ANALYSIS_INPUT_CONTRACT_META_KEY",
    "ANALYSIS_INPUT_CONTRACT_MODEL",
    "COVERAGE_SCOPE_ANALYSIS",
    "PAYLOAD_KIND_ANALYSIS_REPORT",
    "AnalysisComposerInputContract",
    "adapt_analysis_composer_input_contract",
    "adapt_analysis_report_input_contract",
    "attach_analysis_input_contract_meta",
    "build_analysis_composer_input_contract",
    "build_analysis_core_text_payload",
    "build_analysis_core_text_payloads",
    "build_analysis_domain_input_contracts",
    "empty_analysis_composer_input_contract",
    "infer_analysis_material_fields",
    "normalize_analysis_material_domain",
    "adapt_emlis_evidence_span",
    "adapt_emlis_evidence_spans",
    "convert_emlis_evidence_span",
    "convert_emlis_evidence_spans",
    "adapt_piece_evidence_sources",
    "convert_piece_evidence_spans",
    "EMLIS_OBSERVATION_COMPOSER_ADAPTER_NAME",
    "EMLIS_OBSERVATION_CORE_MODEL",
    "EmlisObservationCoreEvaluation",
    "attach_core_evaluation_meta",
    "build_emlis_observation_core_payload",
    "convert_emlis_phrase_unit",
    "convert_emlis_phrase_units",
    "convert_emlis_sentence_plan",
    "convert_emlis_sentence_plans",
    "core_rejection_reason",
    "evaluate_emlis_observation_candidate",
    "PIECE_COMPOSER_ADAPTER_NAME",
    "PIECE_COMPOSER_PHASE_LABEL",
    "PIECE_COMPOSER_MODEL",
    "PieceComposer",
    "PieceComposerEvaluation",
    "adapt_piece_composer",
    "build_piece_composer_evaluation",
    "build_runtime_piece_plan",
    "compose_piece_answer",
    "compose_piece_text_generation",
    "evaluate_piece_composer",
    "PIECE_COMPOSER_INPUT_CONTRACT_ADAPTER_NAME",
    "PIECE_INPUT_CONTRACT_MODEL",
    "PIECE_PAYLOAD_KIND_ANSWER",
    "PIECE_PAYLOAD_KIND_QUESTION",
    "PIECE_FORBIDDEN_SURFACE_PATTERNS",
    "PIECE_LEGACY_BOUNDARY_NAMES",
    "PieceComposerInputContract",
    "adapt_piece_composer_input_contract",
    "adapt_piece_core_question_answer_plan",
    "build_piece_composer_input_contract",
    "build_piece_core_text_payloads",
    "empty_piece_composer_input_contract",
    *_ANALYSIS_COMPOSER_EXPORTS.keys(),
]
