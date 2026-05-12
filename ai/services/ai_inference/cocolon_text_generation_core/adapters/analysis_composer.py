# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 12 AnalysisComposer adapter.

AnalysisComposer connects existing Analysis report text to the common
CoreTextComposer Guard layer. It validates caller-supplied report text as a
non-diagnostic observation report without changing public routes, DB names,
``content_json``, ``standardReport``, or ``contentText`` payload contracts.
"""

from dataclasses import dataclass, field, replace
import re
from typing import Any, Iterable, Mapping

from cocolon_text_generation_core.composer import CORE_TEXT_COMPOSER_NAME, CoreTextComposer
from cocolon_text_generation_core.guards import GuardResult, combine_guard_results, guard_japanese_coherence, guard_overclaim_diagnosis
from cocolon_text_generation_core.policies import CORE_ID_ANALYSIS, PASSING_STATUSES, compact_tokens
from cocolon_text_generation_core.result import CoreTextCandidate, json_safe_mapping
from cocolon_text_generation_core.sentence_plan import build_sentence_plan
from cocolon_text_generation_core.types import CoreTextPayload, PhraseUnit, TextGenerationResult

from .analysis_composer_input_contract import (
    ANALYSIS_CONTENT_PAYLOAD_KEYS_UNCHANGED,
    ANALYSIS_DOMAIN_EMOTION,
    ANALYSIS_DOMAIN_SELF_STRUCTURE,
    ANALYSIS_FORBIDDEN_SURFACE_PATTERNS,
    ANALYSIS_INPUT_CONTRACT_META_KEY,
    COVERAGE_SCOPE_EMOTION_STRUCTURE,
    COVERAGE_SCOPE_SELF_STRUCTURE,
    TEXT_GENERATION_META_KEY,
    AnalysisComposerInputContract,
    build_analysis_composer_input_contract,
    normalize_analysis_material_domain,
)

ADAPTER_NAME = "analysis_composer.v1"
ANALYSIS_COMPOSER_MODEL = "cocolon_text_generation_core.analysis_composer.v1"
PHASE_LABEL = "phase12_analysis_composer_runtime_connected"
ANALYSIS_COMPOSER_META_KEY = "analysis_composer"
ANALYSIS_TEXT_GENERATION_META_KEY = "analysis_text_generation"
TEXT_GENERATION_ANALYSIS_COMPOSER_META_KEY = ANALYSIS_COMPOSER_META_KEY
ANALYSIS_COMPOSER_CONNECTED = True
ANALYSIS_RUNTIME_CONNECTED = True
ANALYSIS_VALIDITY_GATE_CONNECTED = True
ANALYSIS_TEXT_SAFETY_GUARD_NAME = "cocolon_text_generation_core.analysis_text_safety.v1"
COVERAGE_SCOPE_ANALYSIS_RUNTIME = "analysis_observation_report"
COVERAGE_SCOPE_ANALYSIS_REPORT = COVERAGE_SCOPE_ANALYSIS_RUNTIME

REJECTION_ANALYSIS_COMMON_CORE_REJECTED = "analysis_common_core_rejected"
REJECTION_ANALYSIS_COMMON_TEXT_SAFETY_REJECTED = "analysis_common_text_safety_rejected"
REJECTION_ANALYSIS_COMPOSER_NOT_CONNECTED = "analysis_composer_not_connected"
REJECTION_ANALYSIS_OBSERVATION_SURFACE_MISSING = "analysis_observation_surface_missing"
REJECTION_ANALYSIS_RUNTIME_TEXT_MISSING = REJECTION_ANALYSIS_OBSERVATION_SURFACE_MISSING

_EXTRA_FORBIDDEN_SURFACE_PATTERNS = (
    "Emlisです",
    "Emlisの観測",
    "Pieceの問い",
    "Pieceの答え",
    "あなたはこういう人",
    "あなたの本質",
    "性格診断",
    "心理診断",
    "医療診断",
    "診断できます",
    "本当の願い",
    "必ず",
    "絶対に",
    "完全に",
)
_SPACE_RE = re.compile(r"\s+")
_SENTENCE_RE = re.compile(r"[^。！？!?\n]+[。！？!?]?")
_TRIM = " \t\r\n　、,。.!！?？『』「」\"'"


def _clean(value: Any, *, limit: int = 0) -> str:
    text = _SPACE_RE.sub(" ", str(value or "").replace("\r", " ").replace("\n", " ")).strip(_TRIM)
    if limit > 0 and len(text) > limit:
        text = text[:limit].rstrip(_TRIM)
    return text


def _sentences(text: Any) -> tuple[str, ...]:
    source = str(text or "").strip()
    if not source:
        return tuple()
    out: list[str] = []
    for raw_line in re.split(r"[\r\n]+", source):
        line = raw_line.strip()
        if not line:
            continue
        for match in _SENTENCE_RE.finditer(line):
            sentence = _clean(match.group(0), limit=260)
            if sentence and sentence not in out:
                out.append(sentence)
    if not out:
        one = _clean(source, limit=260)
        if one:
            out.append(one)
    return tuple(out)


def _coverage_scope(domain: str) -> str:
    return COVERAGE_SCOPE_SELF_STRUCTURE if domain == ANALYSIS_DOMAIN_SELF_STRUCTURE else COVERAGE_SCOPE_EMOTION_STRUCTURE


def _analysis_safety_policy(domain: Any, *, material_fields: Iterable[Any] | None = None, target_period: Any = "") -> dict[str, Any]:
    return {
        "core_id": CORE_ID_ANALYSIS,
        "analysis_domain": normalize_analysis_material_domain(domain) or ANALYSIS_DOMAIN_EMOTION,
        "target_period": _clean(target_period),
        "strict": True,
        "analysis_strict": True,
        "strictness": "analysis",
        "cross_core_enabled": False,
        "diagnosis_allowed": False,
        "overclaim_allowed": False,
        "personality_assertion_allowed": False,
        "second_person_assertion_allowed": False,
        "medical_psychological_diagnosis_allowed": False,
        "emotion_self_structure_material_mixing_allowed": False,
        "period_material_distribution_change_observation_only": True,
        "material_fields": list(compact_tokens(material_fields or ())),
    }


def evaluate_analysis_report_text_safety(
    text: Any,
    *,
    domain: Any = ANALYSIS_DOMAIN_EMOTION,
    material_fields: Iterable[Any] | None = None,
    target_period: Any = "",
    forbidden_surface_patterns: Iterable[Any] | None = None,
) -> GuardResult:
    """Run the Analysis non-diagnostic subset of the common Guards.

    The validity gate can call this when it only knows report text and material
    fields. Full candidate/evidence evaluation is done by AnalysisComposer when
    source materials are available.
    """

    normalized_domain = normalize_analysis_material_domain(domain) or ANALYSIS_DOMAIN_EMOTION
    forbidden = tuple(
        dict.fromkeys(
            tuple(ANALYSIS_FORBIDDEN_SURFACE_PATTERNS)
            + tuple(_EXTRA_FORBIDDEN_SURFACE_PATTERNS)
            + tuple(forbidden_surface_patterns or ())
        )
    )
    policy = _analysis_safety_policy(normalized_domain, material_fields=material_fields, target_period=target_period)
    checks = (
        guard_japanese_coherence(text, forbidden_surface_patterns=forbidden),
        guard_overclaim_diagnosis(text, core_id=CORE_ID_ANALYSIS, policy=policy),
    )
    combined = combine_guard_results(checks)
    return GuardResult(
        guard_name=ANALYSIS_TEXT_SAFETY_GUARD_NAME,
        passed=combined.passed,
        quality_flags=combined.quality_flags,
        rejection_reasons=combined.rejection_reasons,
        matched_texts=combined.matched_texts,
        coverage_ratio=combined.coverage_ratio,
        used_evidence_span_ids=combined.used_evidence_span_ids,
        meta={
            "adapter_name": ADAPTER_NAME,
            "phase": PHASE_LABEL,
            "core_id": CORE_ID_ANALYSIS,
            "analysis_domain": normalized_domain,
            "analysis_composer_connected": True,
            "validity_gate_connected": True,
            "runtime_connected": True,
            "cross_core_enabled": False,
            "guard_results": [item.as_meta() for item in checks],
        },
    )


def _candidate_text_from_kwargs(
    *,
    report_text: Any = "",
    output_text: Any = None,
    content_text: Any = None,
    content_json: Mapping[str, Any] | None = None,
    output_payload: Mapping[str, Any] | None = None,
) -> str:
    for value in (report_text, output_text, content_text):
        text = _clean(value, limit=0)
        if text:
            return text
    for payload in (content_json, output_payload):
        if not isinstance(payload, Mapping):
            continue
        standard = payload.get("standardReport")
        if isinstance(standard, Mapping):
            text = _clean(standard.get("contentText"), limit=0)
            if text:
                return text
        text = _clean(payload.get("contentText") or payload.get("content_text"), limit=0)
        if text:
            return text
    return ""


def _add_runtime_meta_to_payload(
    payload: CoreTextPayload,
    *,
    contract: AnalysisComposerInputContract,
    candidate_text: str,
    runtime_meta: Mapping[str, Any] | None = None,
) -> CoreTextPayload:
    original_units = tuple(payload.phrase_units or ())
    spans = tuple(payload.evidence_spans or ())
    derived_units: list[PhraseUnit] = []
    if spans and candidate_text:
        base_span_id = spans[0].span_id
        for index, sentence in enumerate(_sentences(candidate_text), start=len(original_units) + 1):
            derived_units.append(
                PhraseUnit(
                    phrase_unit_id=f"analysis-{contract.domain}-candidate-sentence-{index}",
                    evidence_span_id=base_span_id,
                    text=sentence,
                    role="analysis_report_observation_sentence",
                    must_keep=False,
                    meta={
                        "source_adapter": ADAPTER_NAME,
                        "phase": PHASE_LABEL,
                        "analysis_domain": contract.domain,
                        "derived_from": "analysis_candidate_sentence_validation",
                        "user_facing_text_generated_here": False,
                    },
                )
            )
    runtime_units = tuple([*original_units, *derived_units])
    runtime_plans = tuple(payload.sentence_plans or ())
    if derived_units:
        runtime_plan = build_sentence_plan(
            sentence_plan_id=f"analysis-{contract.domain}-candidate-runtime-plan-1",
            phrase_unit_ids=[unit.phrase_unit_id for unit in derived_units],
            relation_type="period_material_distribution_change_observation",
            line_role="analysis_observation_report",
            max_chars=260,
            must_include=True,
            meta={"source_adapter": ADAPTER_NAME, "phase": PHASE_LABEL, "analysis_domain": contract.domain},
        )
        if runtime_plan is not None:
            runtime_plans = runtime_plans + (runtime_plan,)

    meta = dict(payload.meta or {})
    meta.update(
        {
            "adapter_name": ADAPTER_NAME,
            "phase": PHASE_LABEL,
            "core_id": CORE_ID_ANALYSIS,
            "analysis_domain": contract.domain,
            "analysis_composer_connected": True,
            "runtime_connected": True,
            "validity_gate_connected": True,
            "cross_core_enabled": False,
            "emotion_self_structure_material_mixing_allowed": False,
            "content_json_shape_changed": False,
            "content_json_contract_touched": False,
            "standardReport_contract_untouched": True,
            "contentText_contract_untouched": True,
            "content_payload_keys_unchanged": list(ANALYSIS_CONTENT_PAYLOAD_KEYS_UNCHANGED),
            "observation_report_style": "period_material_distribution_change_observation",
            "input_contract": contract.as_meta(),
            "runtime_meta": json_safe_mapping(runtime_meta),
        }
    )
    tone_policy = dict(payload.tone_policy or {})
    tone_policy.update(
        {
            "core_id": CORE_ID_ANALYSIS,
            "analysis_domain": contract.domain,
            "voice_distance": "distant_observation_report",
            "report_style": "period_material_distribution_change_observation",
            "direct_address_allowed": False,
            "emlis_observation_voice_allowed": False,
            "piece_public_qna_voice_allowed": False,
            "analysis_composer_connected": True,
        }
    )
    safety_policy = dict(payload.safety_policy or {})
    safety_policy.update(_analysis_safety_policy(contract.domain, material_fields=_contract_material_fields(contract), target_period=contract.meta.get("target_period", "")))
    safety_policy.update(
        {
            "analysis_composer_connected": True,
            "runtime_connected": True,
            "content_json_mutation_allowed": False,
        }
    )
    forbidden = tuple(
        dict.fromkeys(
            tuple(payload.forbidden_surface_patterns or ())
            + tuple(ANALYSIS_FORBIDDEN_SURFACE_PATTERNS)
            + tuple(_EXTRA_FORBIDDEN_SURFACE_PATTERNS)
        )
    )
    return replace(
        payload,
        phrase_units=runtime_units,
        sentence_plans=runtime_plans,
        tone_policy=tone_policy,
        safety_policy=safety_policy,
        forbidden_surface_patterns=forbidden,
        composer_model=ANALYSIS_COMPOSER_MODEL,
        meta=meta,
    )


def _contract_material_fields(contract: AnalysisComposerInputContract) -> tuple[str, ...]:
    meta = contract.meta if isinstance(contract.meta, Mapping) else {}
    return compact_tokens(meta.get("material_fields") or contract.payload.safety_policy.get("material_fields") or ())


def _runtime_candidate(*, text: str, payload: CoreTextPayload, contract: AnalysisComposerInputContract) -> CoreTextCandidate:
    reasons = list(contract.rejection_reasons)
    if not _sentences(text):
        reasons.append(REJECTION_ANALYSIS_OBSERVATION_SURFACE_MISSING)
    return CoreTextCandidate(
        text=text,
        used_evidence_span_ids=[span.span_id for span in payload.evidence_spans],
        used_phrase_unit_ids=[unit.phrase_unit_id for unit in payload.phrase_units],
        coverage_scope=COVERAGE_SCOPE_ANALYSIS_RUNTIME or _coverage_scope(contract.domain),
        rejection_reasons=tuple(dict.fromkeys(reasons)),
        composer_model=ANALYSIS_COMPOSER_MODEL,
        meta={
            "adapter_name": ADAPTER_NAME,
            "phase": PHASE_LABEL,
            "core_id": CORE_ID_ANALYSIS,
            "analysis_domain": contract.domain,
            "composer_source": "analysis_composer",
            "fixed_string_renderer_used": False,
            "analysis_composer_connected": True,
            "runtime_connected": True,
            "cross_core_enabled": False,
            "diagnosis_allowed": False,
            "overclaim_allowed": False,
            "content_json_shape_changed": False,
            "content_json_contract_touched": False,
            "standardReport_contract_untouched": True,
            "contentText_contract_untouched": True,
            "observation_report_style": "period_material_distribution_change_observation",
        },
    )


@dataclass(frozen=True)
class AnalysisComposerEvaluation:
    contract: AnalysisComposerInputContract
    result: TextGenerationResult
    candidate: CoreTextCandidate
    text_safety: GuardResult
    adapter_name: str = ADAPTER_NAME
    phase: str = PHASE_LABEL
    meta: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "meta", json_safe_mapping(self.meta))

    @property
    def passed(self) -> bool:
        return bool(self.result.status in PASSING_STATUSES and self.result.text and self.text_safety.passed)

    @property
    def text(self) -> str:
        return self.result.text if self.passed else ""

    @property
    def domain(self) -> str:
        return self.contract.domain

    @property
    def save_allowed(self) -> bool:
        return self.passed

    @property
    def rejection_reasons(self) -> tuple[str, ...]:
        reasons: list[str] = []
        reasons.extend(self.contract.rejection_reasons)
        if not self.text_safety.passed:
            reasons.append(REJECTION_ANALYSIS_COMMON_TEXT_SAFETY_REJECTED)
            reasons.extend(self.text_safety.rejection_reasons)
        if not self.result.status in PASSING_STATUSES or not self.result.text:
            reasons.append(REJECTION_ANALYSIS_COMMON_CORE_REJECTED)
            reasons.extend(self.result.rejection_reasons)
        return compact_tokens(reasons)

    def as_meta(self) -> dict[str, Any]:
        return {
            "adapter_name": self.adapter_name,
            "phase": self.phase,
            "core_composer": CORE_TEXT_COMPOSER_NAME,
            "core_id": CORE_ID_ANALYSIS,
            "analysis_domain": self.domain,
            "status": "generated" if self.passed else "rejected",
            "passed": self.passed,
            "save_allowed": self.save_allowed,
            "analysis_composer_connected": True,
            "runtime_connected": True,
            "validity_gate_connected": True,
            "cross_core_enabled": False,
            "non_diagnostic_gate_required": True,
            "non_diagnostic_gate_passed": self.text_safety.passed,
            "observation_report_only": True,
            "period_material_distribution_change_only": True,
            "material_domain_separated": self.contract.as_meta().get("domain_separated"),
            "emotion_self_structure_material_mixing_allowed": False,
            "content_json_shape_changed": False,
            "content_json_contract_touched": False,
            "standardReport_contract_untouched": True,
            "contentText_contract_untouched": True,
            "content_payload_keys_unchanged": list(ANALYSIS_CONTENT_PAYLOAD_KEYS_UNCHANGED),
            "composer_model": ANALYSIS_COMPOSER_MODEL,
            "used_evidence_span_ids": list(self.result.used_evidence_span_ids or self.candidate.used_evidence_span_ids),
            "used_phrase_unit_ids": list(self.candidate.used_phrase_unit_ids),
            "quality_flags": list(dict.fromkeys([*self.result.quality_flags, *self.text_safety.quality_flags])),
            "rejection_reasons": list(self.rejection_reasons),
            "text_generation_result": self.result.as_meta(),
            "text_safety": self.text_safety.as_meta(),
            "candidate": self.candidate.as_meta(),
            "input_contract": self.contract.as_meta(),
            "meta": dict(self.meta),
        }


class AnalysisComposer:
    adapter_name = ADAPTER_NAME
    composer_model = ANALYSIS_COMPOSER_MODEL

    def __init__(self, *, core_composer: CoreTextComposer | None = None) -> None:
        self.core_composer = core_composer or CoreTextComposer(composer_model=ANALYSIS_COMPOSER_MODEL)

    def compose(
        self,
        *,
        domain: Any = ANALYSIS_DOMAIN_EMOTION,
        materials: Any = None,
        material_sources: Any = None,
        report_text: Any = "",
        output_text: Any = None,
        content_text: Any = None,
        content_json: Mapping[str, Any] | None = None,
        output_payload: Mapping[str, Any] | None = None,
        material_fields: Iterable[Any] | None = None,
        target_period: Any = None,
        source_id: Any = "",
        cross_core_enabled: bool = False,
        meta: Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> AnalysisComposerEvaluation:
        normalized_domain = normalize_analysis_material_domain(domain) or ANALYSIS_DOMAIN_EMOTION
        candidate_text = _candidate_text_from_kwargs(
            report_text=report_text,
            output_text=output_text,
            content_text=content_text,
            content_json=content_json,
            output_payload=output_payload,
        )
        contract = build_analysis_composer_input_contract(
            domain=normalized_domain,
            materials=materials,
            material_sources=material_sources,
            report_text=candidate_text,
            content_json=content_json,
            output_payload=output_payload,
            material_fields=material_fields,
            target_period=target_period,
            source_id=source_id,
            cross_core_enabled=cross_core_enabled,
            **kwargs,
        )
        text_safety = evaluate_analysis_report_text_safety(
            candidate_text,
            domain=normalized_domain,
            material_fields=material_fields,
            target_period=target_period,
        )
        payload = _add_runtime_meta_to_payload(contract.payload, contract=contract, candidate_text=candidate_text, runtime_meta=meta)
        candidate = _runtime_candidate(text=candidate_text, payload=payload, contract=contract)
        result = self.core_composer.generate(payload, candidate)
        return AnalysisComposerEvaluation(
            contract=contract,
            result=result,
            candidate=candidate,
            text_safety=text_safety,
            meta={"runtime_meta": dict(meta or {}), "contract_rejection_reasons": list(contract.rejection_reasons)},
        )

    def __call__(self, **kwargs: Any) -> AnalysisComposerEvaluation:
        return self.compose(**kwargs)


def evaluate_analysis_composer(*, core_composer: CoreTextComposer | None = None, **kwargs: Any) -> AnalysisComposerEvaluation:
    return AnalysisComposer(core_composer=core_composer).compose(**kwargs)


def compose_analysis_report(**kwargs: Any) -> AnalysisComposerEvaluation:
    return evaluate_analysis_composer(**kwargs)


def compose_analysis_text_generation(**kwargs: Any) -> AnalysisComposerEvaluation:
    return evaluate_analysis_composer(**kwargs)


def compose_analysis_report_text(**kwargs: Any) -> AnalysisComposerEvaluation:
    return evaluate_analysis_composer(**kwargs)


def adapt_analysis_composer(**kwargs: Any) -> AnalysisComposerEvaluation:
    return evaluate_analysis_composer(**kwargs)


def attach_analysis_composer_meta(content_json: Mapping[str, Any] | None, evaluation: AnalysisComposerEvaluation) -> dict[str, Any]:
    base = dict(content_json or {})
    core_meta = dict(base.get(TEXT_GENERATION_META_KEY) or {}) if isinstance(base.get(TEXT_GENERATION_META_KEY), Mapping) else {}
    evaluation_meta = evaluation.as_meta()
    core_meta[ANALYSIS_COMPOSER_META_KEY] = evaluation_meta
    core_meta[ANALYSIS_TEXT_GENERATION_META_KEY] = evaluation_meta
    core_meta.setdefault(ANALYSIS_INPUT_CONTRACT_META_KEY, evaluation.contract.as_meta())
    core_meta["phase"] = PHASE_LABEL
    core_meta["analysis_composer_connected"] = True
    core_meta["runtime_connected"] = True
    core_meta["cross_core_enabled"] = False
    base[TEXT_GENERATION_META_KEY] = core_meta
    return base


AnalysisComposerCoreEvaluation = AnalysisComposerEvaluation
AnalysisComposerRuntimeResult = AnalysisComposerEvaluation
build_analysis_composer_evaluation = evaluate_analysis_composer

__all__ = [
    "ADAPTER_NAME",
    "ANALYSIS_COMPOSER_CONNECTED",
    "ANALYSIS_COMPOSER_META_KEY",
    "ANALYSIS_COMPOSER_MODEL",
    "ANALYSIS_RUNTIME_CONNECTED",
    "ANALYSIS_TEXT_GENERATION_META_KEY",
    "ANALYSIS_TEXT_SAFETY_GUARD_NAME",
    "ANALYSIS_VALIDITY_GATE_CONNECTED",
    "COVERAGE_SCOPE_ANALYSIS_REPORT",
    "COVERAGE_SCOPE_ANALYSIS_RUNTIME",
    "PHASE_LABEL",
    "REJECTION_ANALYSIS_COMMON_CORE_REJECTED",
    "REJECTION_ANALYSIS_COMMON_TEXT_SAFETY_REJECTED",
    "REJECTION_ANALYSIS_COMPOSER_NOT_CONNECTED",
    "REJECTION_ANALYSIS_OBSERVATION_SURFACE_MISSING",
    "REJECTION_ANALYSIS_RUNTIME_TEXT_MISSING",
    "TEXT_GENERATION_ANALYSIS_COMPOSER_META_KEY",
    "AnalysisComposer",
    "AnalysisComposerCoreEvaluation",
    "AnalysisComposerEvaluation",
    "AnalysisComposerRuntimeResult",
    "adapt_analysis_composer",
    "attach_analysis_composer_meta",
    "build_analysis_composer_evaluation",
    "compose_analysis_report",
    "compose_analysis_report_text",
    "compose_analysis_text_generation",
    "evaluate_analysis_composer",
    "evaluate_analysis_report_text_safety",
]
