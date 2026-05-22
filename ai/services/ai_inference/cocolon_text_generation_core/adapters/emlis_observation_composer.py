# -*- coding: utf-8 -*-
from __future__ import annotations

"""EmlisObservationComposer adapter for the common text generation core.

The adapter is intentionally additive.  It evaluates the candidate text that
EmlisAI has already produced, and it never invents user-facing text.  When the
common core rejects the candidate, callers must keep EmlisAI's existing
fail-closed display boundary.
"""

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from cocolon_text_generation_core.adapters.emlis_evidence_adapter import convert_emlis_evidence_spans
from cocolon_text_generation_core.composer import CORE_TEXT_COMPOSER_NAME, CoreTextComposer
from cocolon_text_generation_core.policies import CORE_ID_EMLIS, DEFAULT_COVERAGE_SCOPE, STATUS_GENERATED
from cocolon_text_generation_core.result import CoreTextCandidate
from cocolon_text_generation_core.stabilization import (
    build_core_stabilization_report,
    emlis_observation_output_contract,
)
from cocolon_text_generation_core.types import CoreTextPayload, PhraseUnit, SentenceBinding, SentencePlan, TextGenerationResult

ADAPTER_NAME = "emlis_observation_composer_adapter.v1"
EMLIS_OBSERVATION_CORE_MODEL = "cocolon_text_generation_core.emlis_observation.v1"
REJECTION_CORE_GATE_REJECTED = "emlis_observation_core_rejected"
REJECTION_CORE_GATE_UNAVAILABLE = "emlis_observation_core_unavailable"
STEP7_GATE_BINDING_REFLECTION_VERSION = "emlis.common_core_gate_binding_reflection.v1"


def _core_guard_meta(result: TextGenerationResult, marker: str) -> Mapping[str, Any]:
    result_meta = result.meta if isinstance(result.meta, Mapping) else {}
    for item in result_meta.get("guard_results") or ():
        if not isinstance(item, Mapping):
            continue
        guard_name = _clean(item.get("guard_name"))
        if marker in guard_name:
            meta = item.get("meta")
            return meta if isinstance(meta, Mapping) else {}
    return {}


def _step7_core_binding_reflection_meta(payload: CoreTextPayload, result: TextGenerationResult) -> dict[str, Any]:
    grounding_meta = _core_guard_meta(result, "grounding")
    binding_count = len(tuple(payload.sentence_bindings or ()))
    binding_used = bool(grounding_meta.get("binding_used"))
    return {
        "version": STEP7_GATE_BINDING_REFLECTION_VERSION,
        "target_step": "7_Gate_binding_reflection",
        "adapter_name": ADAPTER_NAME,
        "core_id": payload.core_id,
        "binding_present": bool(binding_count),
        "binding_available": bool(binding_count),
        "binding_used": binding_used,
        "binding_count": binding_count,
        "binding_supported_sentence_count": int(grounding_meta.get("binding_supported_sentence_count") or 0),
        "relation_types": list(grounding_meta.get("relation_types") or []),
        "reader_trace_binding_used": False,
        "grounding_trace_binding_used": binding_used,
        "template_trace_binding_used": False,
        "display_trace_binding_used": binding_used,
        "gate_threshold_relaxed": False,
        "display_contract_relaxed": False,
        "raw_text_included": False,
        "raw_input_required_for_debug": False,
    }


def _mapping_get(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        return value.get(key, default)
    return getattr(value, key, default)


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


def _tokens(values: Iterable[Any] | Any | None) -> tuple[str, ...]:
    out: list[str] = []
    for value in _as_list(values):
        token = _clean(value)
        if token and token not in out:
            out.append(token)
    return tuple(out)


def _payload_source_id(payload: Mapping[str, Any] | None) -> str:
    if not isinstance(payload, Mapping):
        return "emlis_current_input"
    for key in ("current_input_id", "input_id", "emotion_id", "trace_id"):
        token = _clean(payload.get(key))
        if token:
            return token
    return "emlis_current_input"


def _composition_contract(payload: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if not isinstance(payload, Mapping):
        return {}
    value = payload.get("composition_contract")
    return value if isinstance(value, Mapping) else {}


def _forbidden_surfaces(payload: Mapping[str, Any] | None) -> tuple[str, ...]:
    contract = _composition_contract(payload)
    return _tokens(contract.get("forbidden_output_surfaces") or ())


def _unit_id(unit: Any) -> str:
    return _clean(_mapping_get(unit, "phrase_unit_id", ""))


def _unit_evidence_id(unit: Any) -> str:
    return _clean(_mapping_get(unit, "evidence_span_id", ""))


def _unit_text(unit: Any) -> str:
    return _clean(_mapping_get(unit, "compressed_text", "") or _mapping_get(unit, "text", "") or _mapping_get(unit, "raw_text", ""))


def _unit_role(unit: Any) -> str:
    return _clean(_mapping_get(unit, "role", ""))


def _unit_quality_flags(unit: Any) -> tuple[str, ...]:
    return _tokens(_mapping_get(unit, "quality_flags", ()))


def _unit_must_keep(unit: Any) -> bool:
    return bool(_mapping_get(unit, "must_keep", False))


def _unit_meta(unit: Any) -> dict[str, Any]:
    return {
        "source_adapter": ADAPTER_NAME,
        "source_kind": "emlis_phrase_unit",
        "polarity": _clean(_mapping_get(unit, "polarity", "")),
        "raw_text": _clean(_mapping_get(unit, "raw_text", "")),
    }


def convert_emlis_phrase_unit(unit: Any, *, force_must_keep: bool | None = None) -> PhraseUnit | None:
    unit_id = _unit_id(unit)
    evidence_span_id = _unit_evidence_id(unit)
    text = _unit_text(unit)
    if not unit_id or not evidence_span_id or not text:
        return None
    return PhraseUnit(
        phrase_unit_id=unit_id,
        evidence_span_id=evidence_span_id,
        text=text,
        role=_unit_role(unit),
        quality_flags=_unit_quality_flags(unit),
        must_keep=_unit_must_keep(unit) if force_must_keep is None else bool(force_must_keep),
        meta=_unit_meta(unit),
    )


def _selected_emlis_units(
    phrase_units: Iterable[Any] | None,
    *,
    used_evidence_span_ids: Sequence[str],
    used_phrase_unit_ids: Sequence[str] | None,
) -> list[Any]:
    units = list(phrase_units or [])
    used_ids = set(_tokens(used_phrase_unit_ids))
    used_evidence = set(_tokens(used_evidence_span_ids))
    selected: list[Any] = []
    for unit in units:
        unit_id = _unit_id(unit)
        evidence_id = _unit_evidence_id(unit)
        if used_ids and unit_id in used_ids:
            selected.append(unit)
        elif not used_ids and evidence_id in used_evidence:
            selected.append(unit)
    return selected


def convert_emlis_phrase_units(
    phrase_units: Iterable[Any] | None,
    *,
    used_evidence_span_ids: Sequence[str],
    used_phrase_unit_ids: Sequence[str] | None = None,
    required_roles: Sequence[str] | None = None,
) -> tuple[PhraseUnit, ...]:
    required = set(_tokens(required_roles))
    selected = _selected_emlis_units(
        phrase_units,
        used_evidence_span_ids=used_evidence_span_ids,
        used_phrase_unit_ids=used_phrase_unit_ids,
    )
    converted: list[PhraseUnit] = []
    for unit in selected:
        must_keep = _unit_role(unit) in required or _unit_must_keep(unit)
        common = convert_emlis_phrase_unit(unit, force_must_keep=must_keep)
        if common is not None and common.phrase_unit_id not in {item.phrase_unit_id for item in converted}:
            converted.append(common)
    return tuple(converted)


def _plan_ids(plan: Any) -> tuple[str, ...]:
    return _tokens(_mapping_get(plan, "phrase_unit_ids", ()))


def _plan_id(plan: Any, index: int) -> str:
    return _clean(_mapping_get(plan, "sentence_plan_id", "") or _mapping_get(plan, "plan_id", "") or _mapping_get(plan, "line_role", "")) or f"emlis-plan-{index}"


def convert_emlis_sentence_plan(plan: Any, *, index: int, available_phrase_unit_ids: set[str]) -> SentencePlan | None:
    ids = tuple(unit_id for unit_id in _plan_ids(plan) if unit_id in available_phrase_unit_ids)
    if not ids:
        return None
    return SentencePlan(
        sentence_plan_id=_plan_id(plan, index),
        phrase_unit_ids=ids,
        relation_type=_clean(_mapping_get(plan, "relation_type", "")),
        line_role=_clean(_mapping_get(plan, "line_role", "")),
        max_chars=int(_mapping_get(plan, "max_chars", 120) or 120),
        must_include=bool(_mapping_get(plan, "must_include", True)),
        meta={"source_adapter": ADAPTER_NAME, "source_kind": "emlis_sentence_plan"},
    )



def _binding_items_from_meta(composer_meta: Mapping[str, Any] | None) -> list[Mapping[str, Any]]:
    meta = composer_meta if isinstance(composer_meta, Mapping) else {}
    candidates: list[Any] = []
    bundle = meta.get("sentence_binding_bundle") or meta.get("binding_bundle") or meta.get("binding")
    if isinstance(bundle, Mapping):
        candidates.extend(_as_list(bundle.get("bindings") or bundle.get("sentence_bindings") or bundle.get("items")))
    for key in ("sentence_bindings", "sentence_binding", "bindings"):
        value = meta.get(key)
        if isinstance(value, Mapping):
            candidates.extend(_as_list(value.get("bindings") or value.get("sentence_bindings") or value.get("items")))
        else:
            candidates.extend(_as_list(value))
    out: list[Mapping[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(candidates, start=1):
        if not isinstance(item, Mapping):
            continue
        sentence_id = _clean(item.get("sentence_id") or item.get("id") or f"s{index}")
        if not sentence_id or sentence_id in seen:
            continue
        seen.add(sentence_id)
        out.append(item)
    return out


def convert_emlis_sentence_binding(
    item: Mapping[str, Any],
    *,
    available_phrase_unit_ids: set[str],
    available_evidence_span_ids: set[str],
) -> SentenceBinding | None:
    phrase_ids = tuple(unit_id for unit_id in _tokens(item.get("used_phrase_unit_ids") or item.get("phrase_unit_ids")) if unit_id in available_phrase_unit_ids)
    evidence_ids = tuple(span_id for span_id in _tokens(item.get("used_evidence_span_ids") or item.get("evidence_span_ids")) if span_id in available_evidence_span_ids)
    sentence_id = _clean(item.get("sentence_id") or item.get("id"))
    if not sentence_id or not phrase_ids or not evidence_ids:
        return None
    return SentenceBinding(
        sentence_id=sentence_id,
        text=_clean(item.get("text")),
        used_evidence_span_ids=evidence_ids,
        used_phrase_unit_ids=phrase_ids,
        relation_type=_clean(item.get("relation_type") or item.get("relation")),
        line_role=_clean(item.get("line_role") or item.get("role")),
        coverage_scope=_clean(item.get("coverage_scope")),
        must_include=bool(item.get("must_include", True)),
        meta={"source_adapter": ADAPTER_NAME, "source_kind": "emlis_sentence_binding"},
    )


def convert_emlis_sentence_bindings(
    composer_meta: Mapping[str, Any] | None,
    *,
    phrase_units: Sequence[PhraseUnit],
    evidence_span_ids: Sequence[str],
) -> tuple[SentenceBinding, ...]:
    available_phrase_unit_ids = {unit.phrase_unit_id for unit in phrase_units if unit.phrase_unit_id}
    available_evidence_span_ids = set(_tokens(evidence_span_ids))
    converted: list[SentenceBinding] = []
    for item in _binding_items_from_meta(composer_meta):
        common = convert_emlis_sentence_binding(
            item,
            available_phrase_unit_ids=available_phrase_unit_ids,
            available_evidence_span_ids=available_evidence_span_ids,
        )
        if common is not None and common.sentence_id not in {binding.sentence_id for binding in converted}:
            converted.append(common)
    return tuple(converted)

def convert_emlis_sentence_plans(
    sentence_plans: Iterable[Any] | None,
    *,
    phrase_units: Sequence[PhraseUnit],
    used_phrase_unit_ids: Sequence[str] | None = None,
) -> tuple[SentencePlan, ...]:
    available_ids = {unit.phrase_unit_id for unit in phrase_units if unit.phrase_unit_id}
    converted: list[SentencePlan] = []
    for index, plan in enumerate(sentence_plans or (), start=1):
        common = convert_emlis_sentence_plan(plan, index=index, available_phrase_unit_ids=available_ids)
        if common is not None:
            converted.append(common)
    if converted:
        return tuple(converted)

    # The shallow current-input path does not own Emlis SentencePlan objects.
    # It still needs a common plan so the core can validate the already-built
    # candidate without generating new text.
    ordered_ids = tuple(unit_id for unit_id in _tokens(used_phrase_unit_ids) if unit_id in available_ids) or tuple(
        unit.phrase_unit_id for unit in phrase_units
    )
    return tuple(
        SentencePlan(
            sentence_plan_id=f"emlis-used-unit-{index}",
            phrase_unit_ids=(unit_id,),
            relation_type="candidate_used_phrase_unit",
            line_role="candidate_line",
            must_include=True,
            meta={"source_adapter": ADAPTER_NAME, "source_kind": "emlis_candidate_used_unit"},
        )
        for index, unit_id in enumerate(ordered_ids, start=1)
    )


def _candidate_meta(response: Mapping[str, Any] | None, composer_meta: Mapping[str, Any] | None) -> dict[str, Any]:
    meta = dict(composer_meta or {}) if isinstance(composer_meta, Mapping) else {}
    if isinstance(response, Mapping):
        meta.update(
            {
                "adapter_name": ADAPTER_NAME,
                "composer_source": _clean(response.get("composer_source")),
                "generation_method": _clean(response.get("generation_method")),
                "generation_scope": _clean(response.get("generation_scope")),
                "fixed_string_renderer_used": bool(response.get("fixed_string_renderer_used")),
            }
        )
    else:
        meta["adapter_name"] = ADAPTER_NAME
    return meta



def _common_candidate(
    *,
    comment_text: str,
    used_evidence_span_ids: Sequence[str],
    used_phrase_unit_ids: Sequence[str] | None,
    coverage_scope: str,
    composer_model: str,
    response: Mapping[str, Any] | None,
    composer_meta: Mapping[str, Any] | None,
) -> CoreTextCandidate:
    return CoreTextCandidate(
        text=comment_text,
        used_evidence_span_ids=used_evidence_span_ids,
        used_phrase_unit_ids=used_phrase_unit_ids or (),
        coverage_scope=coverage_scope or DEFAULT_COVERAGE_SCOPE,
        composer_model=composer_model or EMLIS_OBSERVATION_CORE_MODEL,
        meta=_candidate_meta(response, composer_meta),
    )


def required_roles_from_meta(composer_meta: Mapping[str, Any] | None) -> tuple[str, ...]:
    if not isinstance(composer_meta, Mapping):
        return tuple()
    covered = _tokens(composer_meta.get("covered_roles") or ())
    if covered:
        return covered
    return _tokens(composer_meta.get("required_roles") or ())


def build_emlis_observation_core_payload(
    *,
    composer_payload: Mapping[str, Any] | None,
    evidence_items: Iterable[Any] | None,
    phrase_units: Iterable[Any] | None,
    sentence_plans: Iterable[Any] | None,
    comment_text: str,
    used_evidence_span_ids: Sequence[str],
    used_phrase_unit_ids: Sequence[str] | None = None,
    coverage_scope: str = "",
    composer_model: str = "",
    composer_meta: Mapping[str, Any] | None = None,
    response: Mapping[str, Any] | None = None,
) -> tuple[CoreTextPayload, CoreTextCandidate]:
    required_roles = required_roles_from_meta(composer_meta)
    evidence_result = convert_emlis_evidence_spans(evidence_items, source_id=_payload_source_id(composer_payload))
    used_ids = set(_tokens(used_evidence_span_ids))
    common_evidence = tuple(
        span for span in evidence_result.evidence_spans if not used_ids or span.span_id in used_ids
    )
    common_phrases = convert_emlis_phrase_units(
        phrase_units,
        used_evidence_span_ids=tuple(used_ids),
        used_phrase_unit_ids=used_phrase_unit_ids,
        required_roles=required_roles,
    )
    common_used_phrase_ids = tuple(
        unit_id for unit_id in _tokens(used_phrase_unit_ids) if unit_id in {unit.phrase_unit_id for unit in common_phrases}
    ) or tuple(unit.phrase_unit_id for unit in common_phrases)
    common_plans = convert_emlis_sentence_plans(
        sentence_plans,
        phrase_units=common_phrases,
        used_phrase_unit_ids=common_used_phrase_ids,
    )
    common_bindings = convert_emlis_sentence_bindings(
        composer_meta,
        phrase_units=common_phrases,
        evidence_span_ids=tuple(used_ids),
    )
    relation_taxonomy = composer_meta.get("step5_relation_taxonomy") if isinstance(composer_meta, Mapping) else None
    if not isinstance(relation_taxonomy, Mapping) and isinstance(composer_meta, Mapping):
        relation_taxonomy = composer_meta.get("relation_taxonomy")
    if not isinstance(relation_taxonomy, Mapping):
        relation_taxonomy = {}
    structure_material = composer_meta.get("observation_structure_material") if isinstance(composer_meta, Mapping) else None
    if not isinstance(structure_material, Mapping) and isinstance(composer_payload, Mapping):
        structure_material = composer_payload.get("observation_structure_material")
    if not isinstance(structure_material, Mapping):
        structure_material = {}
    candidate = _common_candidate(
        comment_text=comment_text,
        used_evidence_span_ids=tuple(used_ids),
        used_phrase_unit_ids=common_used_phrase_ids,
        coverage_scope=coverage_scope,
        composer_model=composer_model,
        response=response,
        composer_meta=composer_meta,
    )
    payload = CoreTextPayload(
        core_id=CORE_ID_EMLIS,
        source_anchors=evidence_result.source_anchors,
        evidence_spans=common_evidence,
        phrase_units=common_phrases,
        sentence_plans=common_plans,
        sentence_bindings=common_bindings,
        tone_policy={"core_id": CORE_ID_EMLIS, "voice_distance": "emlis_observation"},
        safety_policy={"core_id": CORE_ID_EMLIS, "strictness": "emlis_observation"},
        must_keep_roles=required_roles,
        forbidden_surface_patterns=_forbidden_surfaces(composer_payload),
        composer_model=composer_model or EMLIS_OBSERVATION_CORE_MODEL,
        meta={
            "adapter_name": ADAPTER_NAME,
            "source_core": CORE_ID_EMLIS,
            "coverage_scope": coverage_scope,
            "evidence_adapter": evidence_result.as_meta(),
            "candidate": candidate.as_meta(),
            "sentence_binding_count": len(common_bindings),
            "sentence_bindings": [binding.as_meta(include_text=False) for binding in common_bindings],
            "relation_taxonomy": dict(relation_taxonomy),
            "step5_relation_taxonomy": dict(relation_taxonomy),
            "observation_structure_material": dict(structure_material),
            "observation_structure_dictionary_connected": bool(structure_material),
            "dictionary_is_observation_material_only": True,
            "dictionary_returns_completed_reply": False,
        },
    )
    return payload, candidate


@dataclass(frozen=True)
class EmlisObservationCoreEvaluation:
    adapter_name: str
    payload: CoreTextPayload
    candidate: CoreTextCandidate
    result: TextGenerationResult

    @property
    def passed(self) -> bool:
        return bool(self.result.status == STATUS_GENERATED and self.result.text)

    def as_meta(self) -> dict[str, Any]:
        stabilization_report = build_core_stabilization_report(
            payload=self.payload,
            result=self.result,
            expected_core_id=CORE_ID_EMLIS,
            output_contract=emlis_observation_output_contract(
                coverage_scope=self.result.coverage_scope or self.candidate.coverage_scope
            ),
            meta={"adapter_name": self.adapter_name, "core_composer": CORE_TEXT_COMPOSER_NAME},
        ).as_meta()
        step19_meta = {}
        if isinstance(self.candidate.meta, Mapping):
            raw_step19 = (
                self.candidate.meta.get("step19_a_plan_equivalent_composer")
                or self.candidate.meta.get("step19_a_plan_equivalent")
                or self.candidate.meta.get("a1_composer_introduction")
            )
            if isinstance(raw_step19, Mapping):
                step19_meta = dict(raw_step19)
        step7_binding_reflection = _step7_core_binding_reflection_meta(self.payload, self.result)
        meta = {
            "adapter_name": self.adapter_name,
            "core_composer": CORE_TEXT_COMPOSER_NAME,
            "core_id": self.payload.core_id,
            "status": self.result.status,
            "passed": self.passed,
            "text_length": len(self.result.text or self.candidate.text or ""),
            "used_evidence_span_ids": list(self.result.used_evidence_span_ids or self.candidate.used_evidence_span_ids),
            "used_phrase_unit_ids": list(self.candidate.used_phrase_unit_ids),
            "coverage_scope": self.result.coverage_scope or self.candidate.coverage_scope,
            "quality_flags": list(self.result.quality_flags),
            "rejection_reasons": list(self.result.rejection_reasons),
            "composer_model": self.result.composer_model,
            "payload": {
                "evidence_span_count": len(self.payload.evidence_spans),
                "phrase_unit_count": len(self.payload.phrase_units),
                "sentence_plan_count": len(self.payload.sentence_plans),
                "sentence_binding_count": len(self.payload.sentence_bindings),
                "must_keep_roles": list(self.payload.must_keep_roles),
            },
            "sentence_bindings": [binding.as_meta(include_text=False) for binding in self.payload.sentence_bindings],
            "step7_gate_binding_reflection": step7_binding_reflection,
            "gate_binding_reflection": step7_binding_reflection,
            "step15_common_core_stabilization": stabilization_report,
            "common_core_stabilization": stabilization_report,
            "result": self.result.as_meta(),
        }
        relation_taxonomy = self.payload.meta.get("step5_relation_taxonomy") or self.payload.meta.get("relation_taxonomy")
        if isinstance(relation_taxonomy, Mapping):
            meta["relation_taxonomy"] = dict(relation_taxonomy)
            meta["step5_relation_taxonomy"] = dict(relation_taxonomy)
        if step19_meta:
            meta["step19_a_plan_equivalent_composer"] = step19_meta
            meta["a1_composer_introduction"] = step19_meta
        return meta


def evaluate_emlis_observation_candidate(
    *,
    composer_payload: Mapping[str, Any] | None,
    evidence_items: Iterable[Any] | None,
    phrase_units: Iterable[Any] | None,
    sentence_plans: Iterable[Any] | None,
    comment_text: str,
    used_evidence_span_ids: Sequence[str],
    used_phrase_unit_ids: Sequence[str] | None = None,
    coverage_scope: str = "",
    composer_model: str = "",
    composer_meta: Mapping[str, Any] | None = None,
    response: Mapping[str, Any] | None = None,
    core_composer: CoreTextComposer | None = None,
) -> EmlisObservationCoreEvaluation:
    payload, candidate = build_emlis_observation_core_payload(
        composer_payload=composer_payload,
        evidence_items=evidence_items,
        phrase_units=phrase_units,
        sentence_plans=sentence_plans,
        comment_text=comment_text,
        used_evidence_span_ids=used_evidence_span_ids,
        used_phrase_unit_ids=used_phrase_unit_ids,
        coverage_scope=coverage_scope,
        composer_model=composer_model or EMLIS_OBSERVATION_CORE_MODEL,
        composer_meta=composer_meta,
        response=response,
    )
    result = (core_composer or CoreTextComposer(composer_model=EMLIS_OBSERVATION_CORE_MODEL)).generate(payload, candidate)
    return EmlisObservationCoreEvaluation(adapter_name=ADAPTER_NAME, payload=payload, candidate=candidate, result=result)


def attach_core_evaluation_meta(response: Mapping[str, Any], evaluation: EmlisObservationCoreEvaluation) -> dict[str, Any]:
    out = dict(response or {})
    meta = dict(out.get("composer_meta") or {}) if isinstance(out.get("composer_meta"), Mapping) else {}
    core_meta = evaluation.as_meta()
    meta["text_generation_core"] = core_meta
    meta["core_text_generation"] = core_meta
    out["composer_meta"] = meta
    return out


def core_rejection_reason(evaluation: EmlisObservationCoreEvaluation) -> str:
    if evaluation.result.status == "unavailable":
        return REJECTION_CORE_GATE_UNAVAILABLE
    return REJECTION_CORE_GATE_REJECTED


__all__ = [
    "ADAPTER_NAME",
    "EMLIS_OBSERVATION_CORE_MODEL",
    "EmlisObservationCoreEvaluation",
    "REJECTION_CORE_GATE_REJECTED",
    "REJECTION_CORE_GATE_UNAVAILABLE",
    "attach_core_evaluation_meta",
    "build_emlis_observation_core_payload",
    "convert_emlis_phrase_unit",
    "convert_emlis_phrase_units",
    "convert_emlis_sentence_binding",
    "convert_emlis_sentence_bindings",
    "convert_emlis_sentence_plan",
    "convert_emlis_sentence_plans",
    "core_rejection_reason",
    "evaluate_emlis_observation_candidate",
    "required_roles_from_meta",
]
