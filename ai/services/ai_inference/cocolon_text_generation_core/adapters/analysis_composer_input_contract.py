# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 11 AnalysisComposer input contract adapter.

This module is design-only.  It separates Analysis materials into
``emotion_structure`` and ``self_structure`` domains, prepares strict common
``CoreTextPayload`` input for a future AnalysisComposer, and keeps existing
``content_json`` / ``standardReport`` / ``contentText`` payload contracts
untouched.  It does not connect Analysis runtime text generation.
"""

from dataclasses import dataclass, field
import re
from typing import Any, Iterable, Mapping, Sequence

from cocolon_text_generation_core.evidence import make_evidence_span_like, source_anchors_for_evidence
from cocolon_text_generation_core.guards.overclaim_diagnosis import guard_overclaim_diagnosis
from cocolon_text_generation_core.policies import CORE_ID_ANALYSIS, compact_tokens
from cocolon_text_generation_core.result import CoreTextCandidate, json_safe_mapping
from cocolon_text_generation_core.sentence_plan import build_sentence_plan
from cocolon_text_generation_core.types import CoreTextPayload, EvidenceSpanLike, PhraseUnit, SentencePlan

ADAPTER_NAME = "analysis_composer_input_contract.v0"
ANALYSIS_INPUT_CONTRACT_MODEL = "cocolon_text_generation_core.analysis_input_contract.v0"
PHASE_LABEL = "phase11_input_contract_only"

TEXT_GENERATION_META_KEY = "textGenerationCore"
ANALYSIS_INPUT_CONTRACT_META_KEY = "analysis_input_contract"
ANALYSIS_CONTENT_PAYLOAD_KEYS_UNCHANGED = ("content_json", "standardReport", "contentText")

ANALYSIS_DOMAIN_EMOTION = "emotion_structure"
ANALYSIS_DOMAIN_SELF_STRUCTURE = "self_structure"
DOMAIN_EMOTION_STRUCTURE = ANALYSIS_DOMAIN_EMOTION
DOMAIN_SELF_STRUCTURE = ANALYSIS_DOMAIN_SELF_STRUCTURE
ANALYSIS_DOMAINS = (ANALYSIS_DOMAIN_EMOTION, ANALYSIS_DOMAIN_SELF_STRUCTURE)

PAYLOAD_KIND_EMOTION_STRUCTURE = "analysis_emotion_structure_payload"
PAYLOAD_KIND_SELF_STRUCTURE = "analysis_self_structure_payload"
PAYLOAD_KIND_ANALYSIS_REPORT = "analysis_report_payload"
COVERAGE_SCOPE_EMOTION_STRUCTURE = "analysis_emotion_structure_contract"
COVERAGE_SCOPE_SELF_STRUCTURE = "analysis_self_structure_contract"
COVERAGE_SCOPE_ANALYSIS = "analysis_input_contract"

ANALYSIS_COMPOSER_CONNECTED = False
ANALYSIS_RUNTIME_CONNECTED = False
ANALYSIS_CROSS_CORE_ENABLED = False

ANALYSIS_FORBIDDEN_SURFACE_PATTERNS = (
    "Emlisです",
    "Emlisの観測",
    "Emlisには",
    "Emlisは",
    "Emlisの感想",
    "Pieceの問い",
    "Pieceの答え",
    "あなたはこういう人",
    "あなたの本質",
    "性格診断",
    "心理診断",
    "医療診断",
    "診断できます",
    "うつ病",
    "発達障害",
    "ADHD",
    "ASD",
    "PTSD",
    "必ず",
    "絶対に",
    "完全に",
)

REJECTION_ANALYSIS_DOMAIN_UNKNOWN = "analysis_domain_unknown"
REJECTION_ANALYSIS_DOMAIN_INVALID = REJECTION_ANALYSIS_DOMAIN_UNKNOWN
REJECTION_ANALYSIS_MATERIAL_MISSING = "analysis_material_missing"
REJECTION_ANALYSIS_DOMAIN_MIXED = "analysis_material_domain_mixed"
REJECTION_ANALYSIS_MATERIAL_DOMAIN_MIXED = REJECTION_ANALYSIS_DOMAIN_MIXED
REJECTION_ANALYSIS_EMOTION_CONTAINS_SELF_STRUCTURE = "analysis_emotion_domain_contains_self_structure_material"
REJECTION_ANALYSIS_EMOTION_DOMAIN_CONTAINS_SELF_STRUCTURE = REJECTION_ANALYSIS_EMOTION_CONTAINS_SELF_STRUCTURE
REJECTION_ANALYSIS_SELF_CONTAINS_EMOTION = "analysis_self_structure_domain_contains_emotion_material"
REJECTION_ANALYSIS_SELF_STRUCTURE_DOMAIN_CONTAINS_EMOTION = REJECTION_ANALYSIS_SELF_CONTAINS_EMOTION
REJECTION_ANALYSIS_SELF_STRUCTURE_MATERIAL_BOUNDARY_MISSING = "analysis_self_structure_material_boundary_missing"
REJECTION_ANALYSIS_OUTPUT_TEXT_MISSING = "analysis_output_text_missing"
REJECTION_ANALYSIS_OUTPUT_MISSING = REJECTION_ANALYSIS_OUTPUT_TEXT_MISSING
REJECTION_ANALYSIS_TEXT_SAFETY_REJECTED = "analysis_text_safety_rejected"
REJECTION_ANALYSIS_OUTPUT_OVERCLAIM = REJECTION_ANALYSIS_TEXT_SAFETY_REJECTED
REJECTION_ANALYSIS_CROSS_CORE_DISABLED = "analysis_cross_core_not_enabled"
REJECTION_ANALYSIS_PAYLOAD_MINIMUM_NOT_MET = "analysis_payload_minimum_not_met"

_SPACE_RE = re.compile(r"\s+")
_TRIM = " \t\r\n　、,。.!！?？『』「」\"'"

_DOMAIN_ALIASES = {
    "emotion": ANALYSIS_DOMAIN_EMOTION,
    "emotion_structure": ANALYSIS_DOMAIN_EMOTION,
    "myweb": ANALYSIS_DOMAIN_EMOTION,
    "analysis": ANALYSIS_DOMAIN_EMOTION,
    "self": ANALYSIS_DOMAIN_SELF_STRUCTURE,
    "self_structure": ANALYSIS_DOMAIN_SELF_STRUCTURE,
    "myprofile": ANALYSIS_DOMAIN_SELF_STRUCTURE,
}

_COMMON_FIELDS = {"id", "source_id", "timestamp", "created_at", "updated_at", "domain", "material_domain", "analysis_domain", "source_domain"}
_EMOTION_FIELDS = {
    "emotion_details",
    "emotions",
    "emotion_signals",
    "emotion",
    "label",
    "intensity",
    "strength",
    "memo",
    "category",
    "categories",
    "period",
    "summary",
    "motifs",
    "keywords",
    "daily_share",
    "share",
    "counts",
    "transition_edges",
    "time_buckets",
}
_SELF_FIELDS = {
    "target_hint",
    "target",
    "role_hint",
    "role",
    "thinking",
    "thinking_signals",
    "action",
    "action_signals",
    "social_signals",
    "text_primary",
    "text_secondary",
    "memo_action",
    "question_text",
    "answer_text",
    "answer",
    "value_observation_signals",
    "value_observation_signal_keys",
    "value_observation_plan",
    "analysis_tags",
    "source_anchor_text",
}
_EMOTION_EVIDENCE_FIELDS = (
    "memo",
    "summary",
    "emotion_details",
    "emotions",
    "emotion_signals",
    "emotion",
    "label",
    "category",
    "categories",
)
_SELF_EVIDENCE_FIELDS = (
    "text_primary",
    "text_secondary",
    "memo_action",
    "question_text",
    "answer_text",
    "answer",
    "role_hint",
    "target_hint",
    "thinking",
    "action",
    "source_anchor_text",
    "value_observation_signal_keys",
    "value_observation_signals",
    "action_signals",
    "thinking_signals",
    "analysis_tags",
)


def _clean(value: Any, *, limit: int = 0) -> str:
    text = _SPACE_RE.sub(" ", str(value or "").replace("\r", " ").replace("\n", " ")).strip(_TRIM)
    if limit > 0 and len(text) > limit:
        text = text[:limit].rstrip(_TRIM)
    return text


def _get(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        return value.get(key, default)
    return getattr(value, key, default)


def _iter_materials(value: Any) -> tuple[Any, ...]:
    if value is None:
        return tuple()
    if isinstance(value, Mapping):
        for key in ("materials", "material_sources", "rows", "items"):
            nested = value.get(key)
            if isinstance(nested, Sequence) and not isinstance(nested, (str, bytes, bytearray)):
                return tuple(nested)
        return (value,)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return tuple(value)
    return (value,)


def _as_texts(value: Any, *, limit: int = 180) -> tuple[str, ...]:
    if value is None:
        return tuple()
    items = value if isinstance(value, (list, tuple, set)) else (value,)
    out: list[str] = []
    for item in items:
        if isinstance(item, Mapping):
            text = _clean(item.get("text") or item.get("label") or item.get("type") or item.get("key") or item.get("signal_key") or item.get("name"), limit=limit)
        else:
            text = _clean(item, limit=limit)
        if text and text not in out:
            out.append(text)
    return tuple(out)


def normalize_analysis_material_domain(domain: Any) -> str:
    raw = _clean(domain).lower()
    return _DOMAIN_ALIASES.get(raw, raw)


normalize_analysis_contract_domain = normalize_analysis_material_domain


def _explicit_domain(material: Any) -> str:
    return normalize_analysis_material_domain(
        _get(material, "domain", "")
        or _get(material, "material_domain", "")
        or _get(material, "analysis_domain", "")
        or _get(material, "source_domain", "")
    )


def _field_names_for_item(item: Any) -> set[str]:
    if isinstance(item, Mapping):
        pairs = item.items()
    else:
        names = _COMMON_FIELDS | _EMOTION_FIELDS | _SELF_FIELDS
        pairs = ((name, getattr(item, name, None)) for name in names)
    fields: set[str] = set()
    for key, value in pairs:
        if key and value not in (None, "", [], {}):
            fields.add(str(key))
    return fields


def _field_names(materials: Iterable[Any] | None, explicit: Iterable[Any] | None = None) -> set[str]:
    fields = set(compact_tokens(explicit))
    for item in materials or ():
        fields.update(_field_names_for_item(item))
    return fields


def infer_analysis_material_fields(materials: Iterable[Any] | None, explicit: Iterable[Any] | None = None) -> tuple[str, ...]:
    return tuple(sorted(_field_names(materials, explicit=explicit)))


def infer_analysis_material_domain(material: Any, *, default_domain: Any = ANALYSIS_DOMAIN_EMOTION) -> str:
    explicit = _explicit_domain(material)
    if explicit:
        return explicit
    fields = _field_names_for_item(material)
    emotion_specific = fields.intersection(_EMOTION_FIELDS)
    self_specific = fields.intersection(_SELF_FIELDS)
    if emotion_specific and self_specific:
        return "mixed"
    if self_specific and not emotion_specific:
        return ANALYSIS_DOMAIN_SELF_STRUCTURE
    if emotion_specific and not self_specific:
        return ANALYSIS_DOMAIN_EMOTION
    return normalize_analysis_material_domain(default_domain) or ANALYSIS_DOMAIN_EMOTION


def split_analysis_materials_by_domain(materials: Iterable[Any] | None, *, default_domain: Any = ANALYSIS_DOMAIN_EMOTION) -> dict[str, tuple[Any, ...]]:
    buckets: dict[str, list[Any]] = {ANALYSIS_DOMAIN_EMOTION: [], ANALYSIS_DOMAIN_SELF_STRUCTURE: [], "unknown": []}
    for material in materials or ():
        domain = infer_analysis_material_domain(material, default_domain=default_domain)
        if domain in buckets:
            buckets[domain].append(material)
        else:
            buckets["unknown"].append(material)
    return {key: tuple(value) for key, value in buckets.items()}


def _payload_output_text(payload: Any) -> str:
    if not isinstance(payload, Mapping):
        return ""
    for key in ("contentText", "content_text", "text"):
        text = _clean(payload.get(key), limit=0)
        if text:
            return text
    standard = payload.get("standardReport") or payload.get("standard_report")
    if isinstance(standard, Mapping):
        for key in ("contentText", "content_text", "text"):
            text = _clean(standard.get(key), limit=0)
            if text:
                return text
    return ""


def _resolve_output_text(*, report_text: Any = "", output_text: Any = None, content_text: Any = None, content_json: Any = None, output_payload: Any = None) -> str:
    for value in (report_text, output_text, content_text):
        text = _clean(value, limit=0)
        if text:
            return text
    return _payload_output_text(content_json) or _payload_output_text(output_payload)


def _domain_role(domain: str) -> str:
    return "self_structure_material" if domain == ANALYSIS_DOMAIN_SELF_STRUCTURE else "emotion_structure_material"


def _coverage_scope(domain: str) -> str:
    return COVERAGE_SCOPE_SELF_STRUCTURE if domain == ANALYSIS_DOMAIN_SELF_STRUCTURE else COVERAGE_SCOPE_EMOTION_STRUCTURE


def _payload_kind(domain: str) -> str:
    return PAYLOAD_KIND_SELF_STRUCTURE if domain == ANALYSIS_DOMAIN_SELF_STRUCTURE else PAYLOAD_KIND_EMOTION_STRUCTURE


def _field_texts(material: Any, field_name: str) -> tuple[str, ...]:
    value = _get(material, field_name, None)
    if value in (None, "", [], {}):
        return tuple()
    if field_name in {
        "emotion_details",
        "emotions",
        "emotion_signals",
        "categories",
        "value_observation_signal_keys",
        "value_observation_signals",
        "action_signals",
        "thinking_signals",
        "analysis_tags",
    }:
        return _as_texts(value, limit=120)
    text = _clean(value, limit=220)
    return (text,) if text else tuple()


def _build_evidence(materials: Sequence[Any], *, domain: str, source_id_prefix: str = "") -> tuple[EvidenceSpanLike, ...]:
    fields = _SELF_EVIDENCE_FIELDS if domain == ANALYSIS_DOMAIN_SELF_STRUCTURE else _EMOTION_EVIDENCE_FIELDS
    role = _domain_role(domain)
    spans: list[EvidenceSpanLike] = []
    for material_index, material in enumerate(materials, start=1):
        source_id = _clean(_get(material, "source_id", "") or _get(material, "id", "") or source_id_prefix or f"analysis-{domain}-{material_index}")
        for field in fields:
            for raw_text in _field_texts(material, field):
                span = make_evidence_span_like(
                    span_id=f"analysis-{domain}-{material_index}-{len(spans) + 1}",
                    source_id=source_id,
                    field_name=field,
                    raw_text=raw_text,
                    role=role,
                    meta={
                        "source_adapter": ADAPTER_NAME,
                        "phase": PHASE_LABEL,
                        "analysis_domain": domain,
                        "source_field": field,
                        "must_keep": True,
                    },
                )
                if span.usable:
                    spans.append(span)
    return tuple(spans)


def _build_units(spans: Sequence[EvidenceSpanLike]) -> tuple[PhraseUnit, ...]:
    return tuple(
        PhraseUnit(
            phrase_unit_id=f"analysis-pu{index}",
            evidence_span_id=span.span_id,
            text=span.raw_text,
            role=span.role,
            must_keep=True,
            meta={"source_adapter": ADAPTER_NAME, "phase": PHASE_LABEL, "analysis_domain": span.meta.get("analysis_domain", "")},
        )
        for index, span in enumerate(spans, start=1)
        if _clean(span.raw_text)
    )


def _build_plans(domain: str, units: Sequence[PhraseUnit]) -> tuple[SentencePlan, ...]:
    plan = build_sentence_plan(
        sentence_plan_id=f"analysis-{domain}-plan-1",
        phrase_unit_ids=[unit.phrase_unit_id for unit in units],
        relation_type="analysis_material_observation_contract",
        line_role="observation_report",
        max_chars=240,
        must_include=True,
        meta={"source_adapter": ADAPTER_NAME, "phase": PHASE_LABEL, "analysis_domain": domain},
    )
    return (plan,) if plan is not None else tuple()


def _tone_policy(domain: str, target_period: Any = "") -> dict[str, Any]:
    return {
        "core_id": CORE_ID_ANALYSIS,
        "analysis_domain": domain,
        "voice_distance": "distant_observation_report",
        "report_style": "period_material_distribution_change_observation",
        "target_period": _clean(target_period),
        "direct_address_allowed": False,
        "emlis_observation_voice_allowed": False,
        "piece_public_qna_voice_allowed": False,
        "second_person_lock_in_allowed": False,
        "diagnosis_tone_allowed": False,
    }


def _safety_policy(domain: str, *, material_fields: Sequence[str], target_period: Any = "") -> dict[str, Any]:
    return {
        "core_id": CORE_ID_ANALYSIS,
        "analysis_domain": domain,
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
        "emotion_material_in_self_structure_allowed": False,
        "self_structure_material_in_emotion_allowed": False,
        "content_json_mutation_allowed": False,
        "analysis_composer_connected": False,
        "runtime_connected": False,
        "material_fields": list(material_fields),
    }


def _candidate(
    *,
    text: str,
    spans: Sequence[EvidenceSpanLike],
    units: Sequence[PhraseUnit],
    domain: str,
    reasons: Sequence[str],
    safety_policy: Mapping[str, Any],
) -> CoreTextCandidate:
    candidate_reasons = list(reasons)
    if text:
        guard = guard_overclaim_diagnosis(text, core_id=CORE_ID_ANALYSIS, policy=safety_policy)
        if not guard.passed:
            candidate_reasons.append(REJECTION_ANALYSIS_TEXT_SAFETY_REJECTED)
            candidate_reasons.extend(str(reason) for reason in guard.rejection_reasons)
    unique_reasons = tuple(dict.fromkeys(candidate_reasons))
    return CoreTextCandidate(
        text="" if unique_reasons else text,
        used_evidence_span_ids=[span.span_id for span in spans],
        used_phrase_unit_ids=[unit.phrase_unit_id for unit in units],
        coverage_scope=_coverage_scope(domain),
        composer_model=ANALYSIS_INPUT_CONTRACT_MODEL,
        rejection_reasons=unique_reasons,
        meta={
            "adapter_name": ADAPTER_NAME,
            "phase": PHASE_LABEL,
            "analysis_domain": domain,
            "payload_kind": _payload_kind(domain),
            "analysis_composer_connected": False,
            "runtime_connected": False,
            "cross_core_enabled": False,
        },
    )


def _payload(
    *,
    domain: str,
    spans: Sequence[EvidenceSpanLike],
    units: Sequence[PhraseUnit],
    plans: Sequence[SentencePlan],
    candidate: CoreTextCandidate,
    material_fields: Sequence[str],
    target_period: Any,
    source_id: Any,
    meta: Mapping[str, Any],
) -> CoreTextPayload:
    payload_meta = dict(meta)
    payload_meta.update(
        {
            "candidate": candidate.as_meta(),
            "payload_kind": PAYLOAD_KIND_ANALYSIS_REPORT,
            "analysis_domain": domain,
            "phase": PHASE_LABEL,
            "runtime_connected": False,
            "analysis_composer_connected": False,
            "cross_core_enabled": False,
            "content_json_shape_changed": False,
            "content_json_contract_touched": False,
            "standardReport_contract_untouched": True,
            "contentText_contract_untouched": True,
        }
    )
    return CoreTextPayload(
        core_id=CORE_ID_ANALYSIS,
        source_anchors=source_anchors_for_evidence(spans),
        evidence_spans=spans,
        phrase_units=units,
        sentence_plans=plans,
        tone_policy=_tone_policy(domain, target_period),
        safety_policy=_safety_policy(domain, material_fields=material_fields, target_period=target_period),
        must_keep_roles=(_domain_role(domain),),
        forbidden_surface_patterns=ANALYSIS_FORBIDDEN_SURFACE_PATTERNS,
        composer_model=ANALYSIS_INPUT_CONTRACT_MODEL,
        meta=payload_meta,
    )


@dataclass(frozen=True)
class AnalysisComposerInputContract:
    payload: CoreTextPayload
    report_candidate: CoreTextCandidate
    domain: str
    rejection_reasons: Iterable[str] = field(default_factory=tuple)
    adapter_name: str = ADAPTER_NAME
    meta: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "domain", normalize_analysis_material_domain(self.domain))
        object.__setattr__(self, "rejection_reasons", compact_tokens(self.rejection_reasons))
        object.__setattr__(self, "adapter_name", _clean(self.adapter_name) or ADAPTER_NAME)
        object.__setattr__(self, "meta", json_safe_mapping(self.meta))

    @property
    def candidate(self) -> CoreTextCandidate:
        return self.report_candidate

    @property
    def usable(self) -> bool:
        return bool(not self.rejection_reasons and self.payload.valid_minimum and self.report_candidate.usable_text and not self.report_candidate.rejection_reasons)

    @property
    def connected_to_runtime(self) -> bool:
        return False

    @property
    def cross_core_enabled(self) -> bool:
        return False

    @property
    def analysis_composer_connected(self) -> bool:
        return False

    def as_meta(self) -> dict[str, Any]:
        domain_reasons = {
            REJECTION_ANALYSIS_DOMAIN_MIXED,
            REJECTION_ANALYSIS_EMOTION_CONTAINS_SELF_STRUCTURE,
            REJECTION_ANALYSIS_SELF_CONTAINS_EMOTION,
            REJECTION_ANALYSIS_SELF_STRUCTURE_MATERIAL_BOUNDARY_MISSING,
        }
        return {
            "adapter_name": self.adapter_name,
            "phase": PHASE_LABEL,
            "usable": self.usable,
            "rejection_reasons": list(self.rejection_reasons),
            "core_id": CORE_ID_ANALYSIS,
            "analysis_domain": self.domain,
            "domain": self.domain,
            "analysis_composer_connected": False,
            "runtime_connected": False,
            "connected_to_runtime": False,
            "cross_core_enabled": False,
            "domain_separated": not any(reason in domain_reasons for reason in self.rejection_reasons),
            "emlis_piece_independent": True,
            "content_json_shape_changed": False,
            "content_json_contract_touched": False,
            "standardReport_contract_untouched": True,
            "contentText_contract_untouched": True,
            "content_payload_keys_unchanged": list(ANALYSIS_CONTENT_PAYLOAD_KEYS_UNCHANGED),
            "payload": {
                "core_id": self.payload.core_id,
                "valid_minimum": self.payload.valid_minimum,
                "rejection_reasons": list(self.payload.validate_minimum()),
                "evidence_span_count": len(self.payload.evidence_spans),
                "phrase_unit_count": len(self.payload.phrase_units),
                "sentence_plan_count": len(self.payload.sentence_plans),
                "must_keep_roles": list(self.payload.must_keep_roles),
                "tone_policy": dict(self.payload.tone_policy),
                "safety_policy": dict(self.payload.safety_policy),
            },
            "candidate": self.report_candidate.as_meta(),
            "input_contract": dict(self.meta),
        }


def empty_analysis_composer_input_contract(reason: str = REJECTION_ANALYSIS_MATERIAL_MISSING, *, domain: Any = ANALYSIS_DOMAIN_EMOTION) -> AnalysisComposerInputContract:
    normalized_domain = normalize_analysis_material_domain(domain) or ANALYSIS_DOMAIN_EMOTION
    if normalized_domain not in ANALYSIS_DOMAINS:
        normalized_domain = ANALYSIS_DOMAIN_EMOTION
    candidate = CoreTextCandidate(composer_model=ANALYSIS_INPUT_CONTRACT_MODEL, rejection_reasons=(reason,))
    payload = _payload(
        domain=normalized_domain,
        spans=(),
        units=(),
        plans=(),
        candidate=candidate,
        material_fields=(),
        target_period="",
        source_id="",
        meta={"adapter_name": ADAPTER_NAME, "phase": PHASE_LABEL},
    )
    return AnalysisComposerInputContract(payload, candidate, normalized_domain, rejection_reasons=(reason,), meta={"empty_contract": True})


def build_analysis_composer_input_contract(
    *,
    domain: Any = ANALYSIS_DOMAIN_EMOTION,
    materials: Any = None,
    material_sources: Any = None,
    report_text: Any = "",
    content_json: Mapping[str, Any] | None = None,
    output_payload: Mapping[str, Any] | None = None,
    output_text: Any = None,
    content_text: Any = None,
    material_fields: Iterable[Any] | None = None,
    target_period: Any = None,
    source_id: Any = "",
    cross_core_enabled: bool = False,
    **_kwargs: Any,
) -> AnalysisComposerInputContract:
    normalized_domain = normalize_analysis_material_domain(domain)
    domain_invalid = normalized_domain not in ANALYSIS_DOMAINS
    if domain_invalid:
        normalized_domain = ANALYSIS_DOMAIN_EMOTION

    raw_materials = _iter_materials(material_sources if material_sources is not None else materials)
    all_fields = infer_analysis_material_fields(raw_materials, explicit=material_fields)
    matching: list[Any] = []
    excluded_domains: list[str] = []
    for item in raw_materials:
        item_domain = infer_analysis_material_domain(item, default_domain=normalized_domain)
        if item_domain == normalized_domain:
            matching.append(item)
        else:
            excluded_domains.append(item_domain)

    reasons: list[str] = []
    if domain_invalid:
        reasons.append(REJECTION_ANALYSIS_DOMAIN_UNKNOWN)
    if not matching:
        reasons.append(REJECTION_ANALYSIS_MATERIAL_MISSING)
    field_set = set(all_fields)
    if normalized_domain == ANALYSIS_DOMAIN_EMOTION and field_set.intersection(_SELF_FIELDS):
        reasons.append(REJECTION_ANALYSIS_EMOTION_CONTAINS_SELF_STRUCTURE)
    if normalized_domain == ANALYSIS_DOMAIN_SELF_STRUCTURE and field_set.intersection(_EMOTION_FIELDS):
        reasons.append(REJECTION_ANALYSIS_SELF_CONTAINS_EMOTION)
    if excluded_domains:
        reasons.append(REJECTION_ANALYSIS_DOMAIN_MIXED)
        if normalized_domain == ANALYSIS_DOMAIN_EMOTION:
            reasons.append(REJECTION_ANALYSIS_EMOTION_CONTAINS_SELF_STRUCTURE)
        else:
            reasons.append(REJECTION_ANALYSIS_SELF_CONTAINS_EMOTION)
    if normalized_domain == ANALYSIS_DOMAIN_SELF_STRUCTURE and all_fields and not set(all_fields).intersection(_SELF_FIELDS):
        reasons.append(REJECTION_ANALYSIS_SELF_STRUCTURE_MATERIAL_BOUNDARY_MISSING)
    if cross_core_enabled:
        reasons.append(REJECTION_ANALYSIS_CROSS_CORE_DISABLED)

    text = _resolve_output_text(report_text=report_text, output_text=output_text, content_text=content_text, content_json=content_json, output_payload=output_payload)
    if not text:
        reasons.append(REJECTION_ANALYSIS_OUTPUT_TEXT_MISSING)

    spans = _build_evidence(matching, domain=normalized_domain, source_id_prefix=_clean(source_id))
    if not spans:
        reasons.append(REJECTION_ANALYSIS_MATERIAL_MISSING)
    units = _build_units(spans)
    plans = _build_plans(normalized_domain, units)

    unique_reasons = list(dict.fromkeys(reasons))
    safety_policy = _safety_policy(normalized_domain, material_fields=all_fields, target_period=target_period)
    candidate = _candidate(text=text, spans=spans, units=units, domain=normalized_domain, reasons=unique_reasons, safety_policy=safety_policy)
    # Candidate safety reasons are part of the contract-level rejection surface.
    unique_reasons = list(dict.fromkeys([*unique_reasons, *candidate.rejection_reasons]))
    if unique_reasons:
        candidate = CoreTextCandidate(
            text="",
            used_evidence_span_ids=candidate.used_evidence_span_ids,
            used_phrase_unit_ids=candidate.used_phrase_unit_ids,
            coverage_scope=candidate.coverage_scope,
            composer_model=candidate.composer_model,
            rejection_reasons=unique_reasons,
            quality_flags=candidate.quality_flags,
            meta=candidate.meta,
        )

    meta = {
        "adapter_name": ADAPTER_NAME,
        "phase": PHASE_LABEL,
        "source_core": CORE_ID_ANALYSIS,
        "analysis_domain": normalized_domain,
        "target_period": _clean(target_period),
        "source_id": _clean(source_id),
        "material_count": len(raw_materials),
        "matching_material_count": len(matching),
        "excluded_material_domains": list(dict.fromkeys(excluded_domains)),
        "material_fields": list(all_fields),
        "cross_core_enabled_requested": bool(cross_core_enabled),
        "cross_core_enabled": False,
        "analysis_composer_connected": False,
        "runtime_connected": False,
        "content_json_shape_changed": False,
        "content_json_contract_touched": False,
        "standardReport_contract_untouched": True,
        "contentText_contract_untouched": True,
    }
    payload = _payload(
        domain=normalized_domain,
        spans=spans,
        units=units,
        plans=plans,
        candidate=candidate,
        material_fields=all_fields,
        target_period=target_period,
        source_id=source_id,
        meta=meta,
    )
    return AnalysisComposerInputContract(payload, candidate, normalized_domain, rejection_reasons=tuple(unique_reasons), meta=meta)


def adapt_analysis_composer_input_contract(*args: Any, **kwargs: Any) -> AnalysisComposerInputContract:
    return build_analysis_composer_input_contract(*args, **kwargs)


adapt_analysis_report_input_contract = adapt_analysis_composer_input_contract


def build_analysis_core_text_payload(**kwargs: Any) -> CoreTextPayload:
    return build_analysis_composer_input_contract(**kwargs).payload


def build_analysis_core_text_payloads(*args: Any, **kwargs: Any) -> tuple[CoreTextPayload, ...]:
    if args and isinstance(args[0], AnalysisComposerInputContract):
        return (args[0].payload,)
    return (build_analysis_core_text_payload(**kwargs),)


def build_analysis_domain_input_contracts(
    *,
    emotion_materials: Any = None,
    self_structure_materials: Any = None,
    emotion_output_text: Any = "",
    self_structure_output_text: Any = "",
    emotion_output_payload: Any = None,
    self_structure_output_payload: Any = None,
    target_period: Any = "",
) -> dict[str, AnalysisComposerInputContract]:
    return {
        ANALYSIS_DOMAIN_EMOTION: build_analysis_composer_input_contract(
            domain=ANALYSIS_DOMAIN_EMOTION,
            materials=emotion_materials,
            output_text=emotion_output_text,
            output_payload=emotion_output_payload,
            target_period=target_period,
            source_id="analysis-emotion-structure-input",
        ),
        ANALYSIS_DOMAIN_SELF_STRUCTURE: build_analysis_composer_input_contract(
            domain=ANALYSIS_DOMAIN_SELF_STRUCTURE,
            materials=self_structure_materials,
            output_text=self_structure_output_text,
            output_payload=self_structure_output_payload,
            target_period=target_period,
            source_id="analysis-self-structure-input",
        ),
    }


def attach_analysis_input_contract_meta(content_json: Mapping[str, Any] | None, contract: AnalysisComposerInputContract) -> dict[str, Any]:
    base = dict(content_json or {})
    core_meta = dict(base.get(TEXT_GENERATION_META_KEY) or {}) if isinstance(base.get(TEXT_GENERATION_META_KEY), Mapping) else {}
    core_meta[ANALYSIS_INPUT_CONTRACT_META_KEY] = contract.as_meta()
    core_meta["phase"] = PHASE_LABEL
    core_meta["runtime_connected"] = False
    core_meta["analysis_composer_connected"] = False
    base[TEXT_GENERATION_META_KEY] = core_meta
    return base


__all__ = [
    "ADAPTER_NAME",
    "ANALYSIS_COMPOSER_CONNECTED",
    "ANALYSIS_CONTENT_PAYLOAD_KEYS_UNCHANGED",
    "ANALYSIS_CROSS_CORE_ENABLED",
    "ANALYSIS_DOMAIN_EMOTION",
    "ANALYSIS_DOMAIN_SELF_STRUCTURE",
    "ANALYSIS_DOMAINS",
    "ANALYSIS_FORBIDDEN_SURFACE_PATTERNS",
    "ANALYSIS_INPUT_CONTRACT_META_KEY",
    "ANALYSIS_INPUT_CONTRACT_MODEL",
    "ANALYSIS_RUNTIME_CONNECTED",
    "COVERAGE_SCOPE_ANALYSIS",
    "COVERAGE_SCOPE_EMOTION_STRUCTURE",
    "COVERAGE_SCOPE_SELF_STRUCTURE",
    "DOMAIN_EMOTION_STRUCTURE",
    "DOMAIN_SELF_STRUCTURE",
    "PAYLOAD_KIND_ANALYSIS_REPORT",
    "PAYLOAD_KIND_EMOTION_STRUCTURE",
    "PAYLOAD_KIND_SELF_STRUCTURE",
    "PHASE_LABEL",
    "REJECTION_ANALYSIS_CROSS_CORE_DISABLED",
    "REJECTION_ANALYSIS_DOMAIN_INVALID",
    "REJECTION_ANALYSIS_DOMAIN_MIXED",
    "REJECTION_ANALYSIS_DOMAIN_UNKNOWN",
    "REJECTION_ANALYSIS_EMOTION_CONTAINS_SELF_STRUCTURE",
    "REJECTION_ANALYSIS_EMOTION_DOMAIN_CONTAINS_SELF_STRUCTURE",
    "REJECTION_ANALYSIS_MATERIAL_DOMAIN_MIXED",
    "REJECTION_ANALYSIS_MATERIAL_MISSING",
    "REJECTION_ANALYSIS_OUTPUT_MISSING",
    "REJECTION_ANALYSIS_OUTPUT_OVERCLAIM",
    "REJECTION_ANALYSIS_OUTPUT_TEXT_MISSING",
    "REJECTION_ANALYSIS_PAYLOAD_MINIMUM_NOT_MET",
    "REJECTION_ANALYSIS_SELF_CONTAINS_EMOTION",
    "REJECTION_ANALYSIS_SELF_STRUCTURE_DOMAIN_CONTAINS_EMOTION",
    "REJECTION_ANALYSIS_SELF_STRUCTURE_MATERIAL_BOUNDARY_MISSING",
    "REJECTION_ANALYSIS_TEXT_SAFETY_REJECTED",
    "TEXT_GENERATION_META_KEY",
    "AnalysisComposerInputContract",
    "adapt_analysis_composer_input_contract",
    "adapt_analysis_report_input_contract",
    "attach_analysis_input_contract_meta",
    "build_analysis_composer_input_contract",
    "build_analysis_core_text_payload",
    "build_analysis_core_text_payloads",
    "build_analysis_domain_input_contracts",
    "empty_analysis_composer_input_contract",
    "infer_analysis_material_domain",
    "infer_analysis_material_fields",
    "normalize_analysis_contract_domain",
    "normalize_analysis_material_domain",
    "split_analysis_materials_by_domain",
]
