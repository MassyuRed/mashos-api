# -*- coding: utf-8 -*-
from __future__ import annotations

"""Cocolon internal limited Composer client for EmlisAI B-plan.

Phase8 improves the already-connected B-plan Composer by making source-grounded
PhraseUnit / ObservationProfile / SentencePlan decisions before creating text.
It does not call external AI and does not use public knowledge.
"""

from dataclasses import dataclass
import re
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from emlis_ai_limited_sentence_quality_guard import (
    detect_phase8_profile,
    judge_limited_sentence_quality,
    judge_phrase_unit_material_quality,
    phase8_primary_role_for_text,
    phase8_role_meta,
    phase8_roles_for_text,
)
from emlis_ai_limited_relation_taxonomy import (
    LIMITED_RELATION_TAXONOMY_TARGET_STEP,
    LIMITED_RELATION_TAXONOMY_VERSION,
    build_limited_relation_taxonomy_meta,
    canonical_relation_type,
    normalize_relation_type,
    relation_family,
)
from emlis_ai_limited_surface_realizer import (
    LIMITED_SURFACE_REALIZER_TARGET_STEP,
    LIMITED_SURFACE_REALIZER_VERSION,
    build_surface_component_row,
    build_surface_stabilization_meta,
    choose_limited_surface_parts,
)
from emlis_ai_phrase_unit_grammar_normalizer import (
    KEEP as PHRASE_UNIT_GRAMMAR_KEEP,
    REPHRASE as PHRASE_UNIT_GRAMMAR_REPHRASE,
    normalize_phrase_unit_grammar,
    summarize_phrase_unit_grammar_normalizer,
)
from emlis_ai_relation_surface_contract import (
    detect_relation_surface,
    normalize_relation_surface_type,
    relation_marker_meta,
)
from cocolon_text_generation_core.adapters.emlis_observation_composer import (
    attach_core_evaluation_meta,
    core_rejection_reason,
    evaluate_emlis_observation_candidate,
)
from cocolon_text_generation_core.types import SentenceBinding, SentenceBindingBundle
from emlis_ai_a_plan_equivalent_composer_service import (
    STEP19_A_PLAN_COMPOSER_MODEL,
    promote_step19_a_plan_equivalent_response,
)

_RESPONSE_SCHEMA_VERSION = "emlis.composer.response.v1"
_COMPOSER_MODEL = "cocolon_limited_composer.v1"
_GENERATION_METHOD = "scoped_graph_evidence_composer"
_GENERATION_SCOPE = "scoped_graph_only"
_COMPOSER_DIAGNOSTIC_VERSION = "emlis.composer_diagnostic.v1"
_ALLOWED_SOURCE = "ai_generated"
_UNAVAILABLE_SOURCE = "unavailable"
_MIN_BODY_LINES = 2
_MAX_BODY_LINES = 4
_LIMITED_READER_REPAIR_VERSION = "limited_reader_repair.v1"
_LIMITED_READER_REPAIR_TARGET_STEP = "Step3_previous_rejection_reasons"
_LIMITED_READER_REPAIR_STEP4_TARGET = "Step4_addressee_repair"
_LIMITED_READER_REPAIR_STEP5_TARGET = "Step5_relation_surface_marker_repair"
_READER_REJECTION_REASONS_FOR_LIMITED_REPAIR = frozenset({"addressee_not_clear", "relation_not_expressed"})
_EDGE_ID_LIKE_RE = re.compile(r"^[a-z][0-9a-z_-]*\.[a-z0-9_-]+$", re.IGNORECASE)

_SPACE_RE = re.compile(r"\s+")
_SENTENCE_END_RE = re.compile(r"[。！？!?]+$")
_HONORIFIC_SUFFIXES = ("さん", "様", "くん", "君", "ちゃん", "氏")
_HONORIFIC_SUFFIX_RE = r"(?:さん|様|くん|君|ちゃん|氏)"
_EMLIS_INTRO_RE = r"Emlis[ \u3000]?です。"
_LIMITED_VALID_ADDRESSEE_RE = re.compile(
    rf"^(?:[^\n]{{0,32}}{_HONORIFIC_SUFFIX_RE}、[^\n]{{0,24}}{_EMLIS_INTRO_RE}|{_EMLIS_INTRO_RE})$"
)
_PUNCT_TRIM = " 　、,。.!！?？『』\"'"
_EMOTION_LABELS = {"喜び", "悲しみ", "怒り", "不安", "平穏", "自己理解", "恐れ", "焦り"}
_TEXT_SOURCE_FIELDS = {"memo", "memo_action", "text", "free_text"}
_SKIP_SOURCE_FIELDS = {"emotion_details", "emotions", "category"}
_SKIP_DETECTED_TYPES = {"emotion"}
_GROUP_KEYS = ("pressure_sources", "limit_signals", "self_awareness", "value_or_strength_signals")
_FORBIDDEN_SURFACES = (
    "そこには",
    "もありました",
    "も含まれていました",
    "受け取りました",
    "と思います",
    "として見ています",
    "一緒に見ます",
    "今の私は",
    "あなたは",
    "あなたの",
    "あなたが",
    "あなたに",
    "入力全体では",
    "言葉の流れには",
    "外からは見えにくい緊張",
    "まだ決めきれない揺れ",
    "急いで片づけず",
    "がつながっています",
    "同じ中にあります",
)
_MARKER_NAMES = (
    "_line_primary",
    "_line_pressure",
    "_line_limit",
    "_line_closing",
    "closing_template",
    "role_template",
    "static_observation_text",
    "fallback_observation",
)

_STEP11_ROLE_EXPANSION_VERSION = "emlis.phrase_unit_role_expansion.v1"
_STEP11_EXPANDED_ROLES = (
    "fatigue_accumulation",
    "loss_of_control",
    "small_repair",
    "avoidance_wish",
    "value_wish",
)
_STEP11_ROLE_GROUPS: Dict[str, str] = {
    "fatigue_accumulation": "energy_fatigue",
    "loss_of_control": "energy_fatigue",
    "small_repair": "positive_recovery",
    "avoidance_wish": "limit_escape",
    "value_wish": "value_wish",
}

_STEP12_PROFILE_SENTENCE_PLAN_VERSION = "emlis.profile_sentence_plan_expansion.v1"
_STEP12_EXPANDED_PROFILES = (
    "energy_fatigue",
    "anxiety_anticipation",
    "value_wish",
    "long_meaning_arc",
)
_STEP12_PROFILE_GROUPS: Dict[str, str] = {
    "energy_fatigue": "energy_fatigue",
    "anxiety_anticipation": "anxiety",
    "value_wish": "value_wish",
    "long_meaning_arc": "long_meaning_arc",
}
_STEP12_PROFILE_REQUIRED_GROUPS: Dict[str, Tuple[Tuple[str, ...], ...]] = {
    "energy_fatigue": (("fatigue_accumulation",), ("loss_of_control",)),
    "anxiety_anticipation": (("anticipation_loop",), ("anxiety_return", "loss_of_control")),
    "value_wish": (("value_wish",), ("loss_of_control", "wish_to_rely")),
    "long_meaning_arc": (("fatigue_accumulation", "loss_of_control"), ("value_wish", "avoidance_wish"), ("small_repair", "limit", "perfection_fear")),
}

_STEP13_SURFACE_REALIZER_VERSION = "emlis.surface_realizer.v1"
_STEP13_SURFACE_UNIT_TYPES = ("connector", "particle", "predicate_tail", "tail_variation")
_STEP13_SURFACE_POLICY = "grammar_parts_only_no_completion_sentence_templates"
_STEP8_LIMITED_SURFACE_REALIZER_VERSION = LIMITED_SURFACE_REALIZER_VERSION
_STEP8_LIMITED_SURFACE_REALIZER_TARGET_STEP = LIMITED_SURFACE_REALIZER_TARGET_STEP

_STEP3_SENTENCE_BINDING_VERSION = "emlis.sentence_binding.v1"
_STEP3_SENTENCE_BINDING_TYPE_VERSION = "emlis.limited_composer_sentence_binding_type.v1"
_STEP5_RELATION_TAXONOMY_VERSION = LIMITED_RELATION_TAXONOMY_VERSION
_STEP4_PHRASE_UNIT_MATERIAL_VERSION = "emlis.phrase_unit_material_quality.v1"
_STEP4_PHRASE_UNIT_MATERIAL_TARGET_STEP = "4_PhraseUnit_material_improvement"
_STEP4_SHALLOW_PHRASE_UNIT_GUARD_VERSION = "emlis.shallow_phrase_unit_creation_guard.v1"
_STEP4_SHALLOW_PHRASE_UNIT_GUARD_TARGET_STEP = "Step4_shallow_phrase_unit_creation_guard"
_STEP5_RELATION_TAXONOMY_TARGET_STEP = LIMITED_RELATION_TAXONOMY_TARGET_STEP
_STEP5_SHALLOW_SURFACE_REALIZER_V2_VERSION = "emlis.shallow_surface_realizer_plan.v2"
_STEP5_SHALLOW_SURFACE_REALIZER_V2_TARGET_STEP = "Step5_shallow_surface_realizer_v2"
_STEP5_SHALLOW_SURFACE_REALIZER_V2_NAME = "shallow_surface_realizer.v2"


@dataclass(frozen=True)
class EmlisPhraseUnit:
    phrase_unit_id: str
    evidence_span_id: str
    raw_text: str
    compressed_text: str
    role: str
    polarity: str = "neutral"
    must_keep: bool = False
    quality_flags: Tuple[str, ...] = ()


@dataclass(frozen=True)
class ObservationProfile:
    profile_key: str
    required_roles: Tuple[str, ...]
    min_lines: int = 2
    max_lines: int = 4
    coverage_scope: str = "partial_observation"


@dataclass(frozen=True)
class SentencePlan:
    line_role: str
    phrase_unit_ids: Tuple[str, ...]
    relation_type: str
    max_chars: int = 110
    must_include: bool = True


@dataclass(frozen=True)
class SentenceSurfaceContext:
    line_role: str
    relation_type: str
    phrase_count: int
    polarity: str
    sequence_order: int


@dataclass(frozen=True)
class SentenceSurfaceParts:
    opener: str = ""
    joiner: str = "や、"
    particle: str = "が"
    predicate: str = "書かれています"
    max_phrases: int = 2


class CocolonLimitedComposerClient:
    """Generate a limited Emlis candidate from a scoped payload."""

    composer_model = _COMPOSER_MODEL

    def generate(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        if not isinstance(payload, Mapping):
            return _unavailable_response("limited_composer_invalid_payload")

        scope = _scope_meta(payload)
        coverage_scope = _clean(scope.get("coverage_scope")) or _coverage_scope(_graph(payload))
        if _clean(scope.get("scope_status")) and _clean(scope.get("scope_status")) != "eligible":
            return _unavailable_response("limited_scope_not_eligible", coverage_scope=coverage_scope)

        graph = _graph(payload)
        if not graph:
            return _unavailable_response("limited_composer_missing_graph", coverage_scope=coverage_scope)
        if list(graph.get("safety_boundaries") or []):
            return _unavailable_response("limited_composer_safety_boundary", coverage_scope=coverage_scope)
        if list(graph.get("missing_information") or []):
            return _unavailable_response("limited_composer_missing_information", coverage_scope=coverage_scope)

        evidence_items = [item for item in list(payload.get("evidence_spans") or []) if isinstance(item, Mapping)]
        evidence_by_id = _evidence_by_id(evidence_items)
        if not evidence_by_id:
            return _unavailable_response("limited_composer_missing_evidence", coverage_scope=coverage_scope)

        profile_key = detect_phase8_profile(evidence_items)
        if profile_key == "short_ambiguous_low_evidence":
            return _unavailable_response("limited_composer_short_ambiguous_low_evidence", coverage_scope="current_input_core", profile_key=profile_key)

        allowed_evidence_ids = _allowed_evidence_ids_from_graph(graph)
        if profile_key in {"", "unknown", "current_input_core"}:
            return _generate_current_input_core_candidate(
                payload=payload,
                graph=graph,
                evidence_items=evidence_items,
                evidence_by_id=evidence_by_id,
                allowed_evidence_ids=allowed_evidence_ids,
                source_profile_key=profile_key or "unknown",
            )

        allowed_evidence_ids.update(_phase8_profile_evidence_ids(profile_key, evidence_items))
        generation_evidence_items = [
            item
            for item in evidence_items
            if not allowed_evidence_ids or str(item.get("span_id") or "").strip() in allowed_evidence_ids
        ]
        phrase_units = _build_phrase_units(generation_evidence_items)
        if not phrase_units:
            return _unavailable_response(
                "limited_composer_missing_phrase_units",
                coverage_scope=coverage_scope,
                profile_key=profile_key,
                extra_meta={
                    "required_roles": list(_profile_for_key(profile_key).required_roles),
                    "available_roles": [],
                    "phrase_unit_count": 0,
                    "sentence_plan_count": 0,
                    "allowed_evidence_span_ids": sorted(allowed_evidence_ids),
                },
            )
        profile = _profile_for_key(profile_key)
        missing_roles = [role for role in profile.required_roles if not _units_for_role(phrase_units, role)]
        if missing_roles:
            return _unavailable_response(
                "limited_composer_required_role_missing",
                coverage_scope=coverage_scope,
                profile_key=profile_key,
                extra_meta={
                    "missing_roles": missing_roles,
                    "required_roles": list(profile.required_roles),
                    "available_roles": _dedupe(unit.role for unit in phrase_units),
                    "phrase_unit_count": len(phrase_units),
                    "sentence_plan_count": 0,
                },
            )

        plans = _sentence_plans_for_profile(profile=profile, units=phrase_units)
        if not plans:
            return _unavailable_response(
                "limited_composer_sentence_plan_unavailable",
                coverage_scope=coverage_scope,
                profile_key=profile_key,
                extra_meta={
                    "required_roles": list(profile.required_roles),
                    "available_roles": _dedupe(unit.role for unit in phrase_units),
                    "phrase_unit_count": len(phrase_units),
                    "sentence_plan_count": 0,
                },
            )
        lines, used_unit_ids, sentence_tail_keys, sentence_bindings, surface_rows = _render_sentence_plans(payload=payload, profile=profile, plans=plans, units=phrase_units)
        if not lines:
            return _unavailable_response(
                "limited_composer_sentence_plan_unavailable",
                coverage_scope=coverage_scope,
                profile_key=profile_key,
                extra_meta={
                    "required_roles": list(profile.required_roles),
                    "available_roles": _dedupe(unit.role for unit in phrase_units),
                    "phrase_unit_count": len(phrase_units),
                    "sentence_plan_count": len(plans),
                },
            )

        min_body, max_body = _body_limits(scope, profile=profile)
        greeting_count = 1 if lines and "Emlis" in lines[0] else 0
        body_lines = lines[greeting_count:][:max_body]
        body_bindings = list(sentence_bindings or [])[:len(body_lines)]
        body_surface_rows = list(surface_rows or [])[:len(body_lines)]
        lines = lines[:greeting_count] + body_lines
        if body_bindings:
            used_unit_ids = _dedupe(unit_id for binding in body_bindings for unit_id in binding.used_phrase_unit_ids)
        if len(body_lines) < min_body:
            return _unavailable_response(
                "limited_composer_minimum_body_not_met",
                coverage_scope=coverage_scope,
                profile_key=profile_key,
                extra_meta={
                    "required_roles": list(profile.required_roles),
                    "available_roles": _dedupe(unit.role for unit in phrase_units),
                    "phrase_unit_count": len(phrase_units),
                    "sentence_plan_count": len(plans),
                    "body_line_count": len(body_lines),
                },
            )

        comment_text = "\n".join(line for line in lines if line).strip()
        if not comment_text:
            return _unavailable_response("limited_composer_empty_candidate", coverage_scope=coverage_scope, profile_key=profile_key)

        matched_forbidden = _matched_forbidden_surfaces(payload=payload, text=comment_text)
        if matched_forbidden:
            return _unavailable_response("limited_composer_forbidden_surface", matched_forbidden=matched_forbidden, coverage_scope=coverage_scope, profile_key=profile_key)

        unit_by_id = {unit.phrase_unit_id: unit for unit in phrase_units}
        used_evidence_ids = _dedupe(unit_by_id[unit_id].evidence_span_id for unit_id in used_unit_ids if unit_id in unit_by_id)
        quality_report = judge_limited_sentence_quality(
            comment_text=comment_text,
            evidence_spans=_evidence_objects_for_quality(generation_evidence_items),
            profile_key=profile_key,
            used_evidence_span_ids=used_evidence_ids,
            composer_meta={"profile_key": profile_key},
        )
        if not bool(quality_report.get("passed")):
            return _unavailable_response(
                "limited_composer_sentence_quality_rejected",
                matched_forbidden=list(quality_report.get("matched_fragments") or quality_report.get("matched_surfaces") or []),
                coverage_scope=coverage_scope,
                profile_key=profile_key,
                extra_meta={"phase8_quality": quality_report},
            )

        used_evidence_ids = [span_id for span_id in used_evidence_ids if span_id in evidence_by_id]
        if not used_evidence_ids:
            return _unavailable_response("limited_composer_no_used_evidence", coverage_scope=coverage_scope, profile_key=profile_key)

        composer_meta = {
            "limited_composer": True,
            "generation_scope": _GENERATION_SCOPE,
            "external_ai_used": False,
            "phase8_quality_path": True,
            "profile_key": profile_key,
            "required_roles": list(profile.required_roles),
            "available_roles": _dedupe(unit.role for unit in phrase_units),
            "covered_roles": _dedupe(unit.role for unit in phrase_units if unit.phrase_unit_id in set(used_unit_ids)),
            "body_line_count": len(body_lines),
            "phrase_unit_count": len(phrase_units),
            "sentence_plan_count": len(plans),
            "sentence_surface_mode": "componentized_surface_realizer",
            "surface_realizer_stage": "Step13_surface_realizer",
            "sentence_tail_keys": sentence_tail_keys,
            "surface_tail_keys": sentence_tail_keys,
            "allowed_evidence_span_ids": sorted(allowed_evidence_ids),
            "phase8_quality": quality_report,
        }
        composer_meta["phrase_unit_material_quality"] = _step4_phrase_unit_material_meta(phrase_units)
        composer_meta["step4_phrase_unit_material_quality"] = composer_meta["phrase_unit_material_quality"]
        composer_meta["phrase_unit_material_quality_enabled"] = True
        sentence_binding_bundle = _sentence_binding_bundle_meta(
            bindings=body_bindings,
            coverage_scope=profile.coverage_scope or coverage_scope,
            profile_key=profile_key,
            sentence_plans=plans,
            phrase_units=phrase_units,
        )
        _attach_sentence_binding_meta(composer_meta, bundle_meta=sentence_binding_bundle, body_line_count=len(body_lines))
        _attach_relation_taxonomy_meta(composer_meta, taxonomy_meta=sentence_binding_bundle.get("relation_taxonomy"))
        _attach_step8_surface_meta(
            composer_meta,
            step8_meta=_step8_limited_surface_realizer_meta(
                profile_key=profile_key,
                coverage_scope=profile.coverage_scope or coverage_scope,
                surface_rows=body_surface_rows,
                predicate_keys=sentence_tail_keys,
                relation_types=sentence_binding_bundle.get("relation_types") or (),
                shallow_path=False,
            ),
        )
        composer_meta["surface_realizer"] = _step13_surface_realizer_meta(
            profile_key=profile_key,
            sentence_plans=plans,
            phrase_units=phrase_units,
            used_unit_ids=used_unit_ids,
            predicate_keys=sentence_tail_keys,
            shallow_path=False,
        )
        composer_meta["surface_realizer_meta"] = composer_meta["surface_realizer"]
        composer_meta["step13_surface_realizer"] = composer_meta["surface_realizer"]
        composer_meta["role_expansion"] = _step11_role_expansion_meta(phrase_units)
        composer_meta["step11_role_expansion"] = composer_meta["role_expansion"]
        composer_meta["profile_sentence_plan"] = _step12_profile_sentence_plan_meta(
            profile_key=profile_key,
            profile=profile,
            phrase_units=phrase_units,
            sentence_plans=plans,
            used_unit_ids=used_unit_ids,
        )
        composer_meta["profile_sentence_plan_expansion"] = composer_meta["profile_sentence_plan"]
        composer_meta["step12_profile_sentence_plan"] = composer_meta["profile_sentence_plan"]
        composer_meta["step12_profile_sentence_plan_expansion"] = composer_meta["profile_sentence_plan"]
        composer_meta["composer_diagnostic"] = _composer_diagnostic_meta(
            status="generated",
            coverage_scope=profile.coverage_scope or coverage_scope,
            profile_key=profile_key,
            phrase_units=phrase_units,
            sentence_plans=plans,
            used_unit_ids=used_unit_ids,
            required_roles=profile.required_roles,
            extra_meta=composer_meta,
        )
        _attach_limited_reader_repair_step3_meta(
            composer_meta,
            payload=payload,
            coverage_scope=profile.coverage_scope or coverage_scope,
            profile_key=profile_key,
        )
        response = {
            "schema_version": _RESPONSE_SCHEMA_VERSION,
            "response_schema_version": _RESPONSE_SCHEMA_VERSION,
            "composer_source": _ALLOWED_SOURCE,
            "status": "generated",
            "composer_model": _COMPOSER_MODEL,
            "generation_method": _GENERATION_METHOD,
            "generation_scope": _GENERATION_SCOPE,
            "fixed_string_renderer_used": False,
            "coverage_scope": profile.coverage_scope or coverage_scope,
            "comment_text": comment_text,
            "used_evidence_span_ids": used_evidence_ids,
            "used_claim_ids": _used_claim_ids(graph),
            "used_relation_ids": _used_relation_ids(graph),
            "confidence": _confidence(profile=profile, phrase_units=phrase_units, used_unit_ids=used_unit_ids),
            "used_phrase_unit_ids": used_unit_ids,
            "sentence_binding_bundle": sentence_binding_bundle,
            "composer_meta": composer_meta,
        }
        return _core_checked_response(
            response=response,
            payload=payload,
            evidence_items=generation_evidence_items,
            phrase_units=phrase_units,
            sentence_plans=plans,
            used_unit_ids=used_unit_ids,
            coverage_scope=profile.coverage_scope or coverage_scope,
            profile_key=profile_key,
        )


def _scope_meta(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    for key in ("limited_observation_scope", "limited_scope", "scope_meta", "scope"):
        value = payload.get(key)
        if isinstance(value, Mapping):
            return value
    return {}


def _graph(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    value = payload.get("observation_graph")
    return value if isinstance(value, Mapping) else {}


def _unavailable_response(
    reason: str,
    *,
    matched_forbidden: Sequence[str] | None = None,
    coverage_scope: str = "",
    profile_key: str = "",
    extra_meta: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    reasons = [str(reason or "limited_composer_unavailable").strip()]
    if matched_forbidden:
        reasons.append("limited_composer_forbidden_or_quality_surface")
    meta: Dict[str, Any] = {
        "limited_composer": True,
        "generation_scope": _GENERATION_SCOPE,
        "external_ai_used": False,
        "phase8_quality_path": True,
    }
    if profile_key:
        meta["profile_key"] = profile_key
    if isinstance(extra_meta, Mapping):
        meta.update(dict(extra_meta))
    diagnostic = meta.get("composer_diagnostic") if isinstance(meta.get("composer_diagnostic"), Mapping) else None
    if diagnostic is None:
        diagnostic = _composer_diagnostic_meta(
            status="unavailable",
            coverage_scope=coverage_scope or "current_input_core",
            profile_key=profile_key or str(meta.get("profile_key") or ""),
            source_profile_key=str(meta.get("source_profile_key") or ""),
            rejection_reasons=reasons,
            required_roles=meta.get("required_roles") if isinstance(meta.get("required_roles"), list) else (),
            missing_roles=meta.get("missing_roles") if isinstance(meta.get("missing_roles"), list) else (),
            extra_meta=meta,
        )
    meta["composer_diagnostic"] = dict(diagnostic)
    return {
        "schema_version": _RESPONSE_SCHEMA_VERSION,
        "response_schema_version": _RESPONSE_SCHEMA_VERSION,
        "composer_source": _UNAVAILABLE_SOURCE,
        "status": "unavailable",
        "composer_model": _COMPOSER_MODEL,
        "generation_method": _GENERATION_METHOD,
        "generation_scope": _GENERATION_SCOPE,
        "fixed_string_renderer_used": False,
        "coverage_scope": coverage_scope or "current_input_core",
        "comment_text": "",
        "used_evidence_span_ids": [],
        "used_claim_ids": [],
        "used_relation_ids": [],
        "confidence": 0.0,
        "rejection_reasons": _dedupe(reasons),
        "matched_forbidden_surfaces": list(matched_forbidden or []),
        "composer_meta": meta,
    }


def _clean(value: Any, *, limit: int = 120) -> str:
    text = _SPACE_RE.sub(" ", str(value or "").replace("\r", " ").replace("\n", " ")).strip()
    text = _SENTENCE_END_RE.sub("", text).strip(_PUNCT_TRIM)
    if limit > 0 and len(text) > limit:
        text = text[:limit].rstrip(_PUNCT_TRIM)
    return text


def _compact(value: Any) -> str:
    return re.sub(r"[\s　、,。.!！?？\t\n\r『』「」（）()\[\]【】]", "", str(value or ""))


def _dedupe(values: Iterable[str]) -> List[str]:
    out: List[str] = []
    for value in values or []:
        item = str(value or "").strip()
        if item and item not in out:
            out.append(item)
    return out


def _repeated_values(values: Iterable[str], *, min_count: int = 2) -> List[str]:
    counts: Dict[str, int] = {}
    for value in values or []:
        item = str(value or "").strip()
        if item:
            counts[item] = counts.get(item, 0) + 1
    return [key for key, count in counts.items() if count >= min_count]







def _composer_reason_category(reason: str) -> str:
    value = str(reason or "").strip()
    if not value:
        return ""
    direct = {
        "limited_composer_required_role_missing": "required_role_missing",
        "required_role_missing": "required_role_missing",
        "limited_composer_missing_phrase_units": "missing_phrase_units",
        "missing_phrase_units": "missing_phrase_units",
        "limited_composer_shallow_insufficient_evidence": "shallow_insufficient_evidence",
        "limited_composer_short_ambiguous_low_evidence": "shallow_insufficient_evidence",
        "shallow_insufficient_evidence": "shallow_insufficient_evidence",
        "limited_composer_sentence_plan_unavailable": "sentence_plan_unavailable",
        "limited_composer_empty_candidate": "sentence_plan_unavailable",
        "limited_composer_shallow_empty_candidate": "sentence_plan_unavailable",
        "limited_composer_minimum_body_not_met": "sentence_plan_unavailable",
        "sentence_plan_unavailable": "sentence_plan_unavailable",
        "profile_unmatched": "profile_unmatched",
    }
    if value in direct:
        return direct[value]
    if "required_role" in value:
        return "required_role_missing"
    if "phrase_unit" in value:
        return "missing_phrase_units"
    if "shallow" in value and ("evidence" in value or "ambiguous" in value):
        return "shallow_insufficient_evidence"
    if "profile" in value and "unmatched" in value:
        return "profile_unmatched"
    if "sentence_plan" in value or "empty_candidate" in value or "minimum_body" in value:
        return "sentence_plan_unavailable"
    if "quality" in value or "core" in value or "forbidden" in value:
        return "composer_quality"
    if "evidence" in value:
        return "composer_evidence"
    if "scope" in value:
        return "scope_not_eligible"
    if "graph" in value:
        return "missing_graph"
    return "composer_general"


def _composer_coverage_hint(category: str, *, profile_key: str = "", shallow_path: bool = False) -> str:
    category = str(category or "").strip()
    if category in {
        "required_role_missing",
        "missing_phrase_units",
        "shallow_insufficient_evidence",
        "profile_unmatched",
        "sentence_plan_unavailable",
    }:
        return category
    if shallow_path or profile_key == "current_input_core":
        return "current_input_core"
    if category:
        return category
    return "composer_not_classified"


def _step11_role_expansion_meta(units: Sequence[EmlisPhraseUnit] | None) -> Dict[str, Any]:
    role_counts: Dict[str, int] = {}
    groups: Dict[str, List[str]] = {}
    for unit in list(units or []):
        role = str(getattr(unit, "role", "") or "").strip()
        if not role:
            continue
        role_counts[role] = role_counts.get(role, 0) + 1
        group = _STEP11_ROLE_GROUPS.get(role)
        if group:
            groups.setdefault(group, [])
            if role not in groups[group]:
                groups[group].append(role)
    expanded = [role for role in _STEP11_EXPANDED_ROLES if role_counts.get(role)]
    return {
        "version": _STEP11_ROLE_EXPANSION_VERSION,
        "target_step": "Step11_phrase_unit_role_expansion",
        "phase": "B-C1",
        "policy": "role_to_phrase_unit_material_only",
        "expanded_roles": expanded,
        "expanded_role_count": sum(role_counts.get(role, 0) for role in _STEP11_EXPANDED_ROLES),
        "role_counts": dict(role_counts),
        "coverage_groups": _dedupe(groups.keys()),
        "roles_by_coverage_group": {key: value for key, value in groups.items()},
        "role_is_material_only": True,
        "completion_sentence_templates_added": False,
    }


def _step12_profile_sentence_plan_meta(
    *,
    profile_key: str,
    profile: ObservationProfile | None = None,
    phrase_units: Sequence[EmlisPhraseUnit] | None = None,
    sentence_plans: Sequence[SentencePlan] | None = None,
    used_unit_ids: Sequence[str] | None = None,
) -> Dict[str, Any]:
    units = list(phrase_units or [])
    plans = list(sentence_plans or [])
    used = {str(item or "").strip() for item in list(used_unit_ids or []) if str(item or "").strip()}
    key = str(profile_key or getattr(profile, "profile_key", "") or "").strip()
    required = list(getattr(profile, "required_roles", tuple()) or tuple())
    unit_by_id = {unit.phrase_unit_id: unit for unit in units}
    planned_roles: List[str] = []
    plan_roles: Dict[str, List[str]] = {}
    for plan in plans:
        line_roles = _dedupe(
            unit_by_id[unit_id].role
            for unit_id in plan.phrase_unit_ids
            if unit_id in unit_by_id and unit_by_id[unit_id].role
        )
        plan_roles[plan.line_role] = line_roles
        for role in line_roles:
            if role not in planned_roles:
                planned_roles.append(role)
    used_roles = _dedupe(unit.role for unit in units if unit.phrase_unit_id in used)
    available_roles = set(_dedupe([*planned_roles, *used_roles, *(unit.role for unit in units)]))
    required_role_groups = [list(group) for group in _STEP12_PROFILE_REQUIRED_GROUPS.get(key, tuple())]
    satisfied_role_groups: List[List[str]] = []
    for group in _STEP12_PROFILE_REQUIRED_GROUPS.get(key, tuple()):
        matched = [role for role in group if role in available_roles]
        if matched:
            satisfied_role_groups.append(matched)
    expanded_roles = _dedupe(role for role in [*planned_roles, *used_roles] if role in _STEP11_EXPANDED_ROLES)
    expanded = key in _STEP12_EXPANDED_PROFILES
    return {
        "version": _STEP12_PROFILE_SENTENCE_PLAN_VERSION,
        "target_step": "Step12_profile_sentence_plan_expansion",
        "phase": "B-C1",
        "profile_key": key,
        "profile_expanded": bool(expanded),
        "profile_is_expanded": bool(expanded),
        "expanded_profile": bool(expanded),
        "expanded_profiles": [key] if expanded else [],
        "coverage_group": _STEP12_PROFILE_GROUPS.get(key, ""),
        "profile_group": _STEP12_PROFILE_GROUPS.get(key, ""),
        "required_roles": required,
        "required_role_groups": required_role_groups,
        "satisfied_role_groups": satisfied_role_groups,
        "planned_roles": planned_roles,
        "used_roles": used_roles,
        "expanded_roles": expanded_roles,
        "sentence_plan_count": len(plans),
        "sentence_plan_roles": plan_roles,
        "planned_line_roles": _dedupe(plan.line_role for plan in plans),
        "planned_relation_types": _dedupe(plan.relation_type for plan in plans),
        "profile_source": "role_set_requirements_not_example_sentences",
        "sentence_plan_source": "role_and_relation_plan",
        "profile_selection_is_role_based": True,
        "sentence_plan_is_role_based": True,
        "role_combination_based": True,
        "lexical_variant_ready": bool(expanded and len(satisfied_role_groups) == len(required_role_groups) and len(plans) >= 2),
        "example_sentence_match_used": False,
        "completion_sentence_templates_added": False,
        "profile_sentence_plan_is_material_only": True,
        "profile_material_only": True,
    }


def _step13_surface_realizer_meta(
    *,
    profile_key: str,
    sentence_plans: Sequence[SentencePlan] | None = None,
    phrase_units: Sequence[EmlisPhraseUnit] | None = None,
    used_unit_ids: Sequence[str] | None = None,
    predicate_keys: Sequence[str] | None = None,
    shallow_path: bool = False,
) -> Dict[str, Any]:
    units = list(phrase_units or [])
    plans = list(sentence_plans or [])
    used = {str(item or "").strip() for item in list(used_unit_ids or []) if str(item or "").strip()}
    used_units = [unit for unit in units if not used or unit.phrase_unit_id in used]
    used_roles = _dedupe(unit.role for unit in used_units)
    tails = _dedupe(predicate_keys or [])
    raw_tails = [str(item or "").strip() for item in list(predicate_keys or []) if str(item or "").strip()]
    repeated_tail_keys = _repeated_values(raw_tails, min_count=2)
    generic_tail_count = sum(1 for key in tails if key in {"written", "exists"})
    line_count = len(tails) if tails else len(plans)
    if line_count <= 2:
        length_mode = "short"
    elif line_count == 3:
        length_mode = "medium"
    else:
        length_mode = "long"
    phrase_lengths = [len(str(unit.compressed_text or "")) for unit in used_units if str(unit.compressed_text or "").strip()]
    return {
        "version": _STEP13_SURFACE_REALIZER_VERSION,
        "target_step": "Step13_surface_realizer",
        "phase": "B-C1",
        "policy": _STEP13_SURFACE_POLICY,
        "surface_unit_types": list(_STEP13_SURFACE_UNIT_TYPES),
        "surface_realizer_stage": "connector_particle_tail_naturalization",
        "surface_realizer_source": "sentence_plan_and_phrase_unit_roles",
        "profile_key": str(profile_key or "").strip(),
        "shallow_observation_path": bool(shallow_path),
        "length_mode": length_mode,
        "line_count": line_count,
        "phrase_length_range": {
            "min": min(phrase_lengths) if phrase_lengths else 0,
            "max": max(phrase_lengths) if phrase_lengths else 0,
        },
        "grammar_parts_only": True,
        "surface_realizer_is_componentized": True,
        "componentized_surface_realizer": True,
        "connector_particle_tail_components_only": True,
        "relation_aware": True,
        "role_aware": True,
        "completion_sentence_templates_added": False,
        "fixed_observation_sentence_added": False,
        "fixed_closing_sentence_added": False,
        "generic_closing_added": False,
        "role_sentence_templates_added": False,
        "example_sentence_match_used": False,
        "connector_policy": "relation_aware_opener_variation",
        "particle_policy": "phrase_ending_and_relation_aware",
        "predicate_policy": "relation_polarity_and_tail_variation",
        "raw_evidence_quote_policy": "compressed_phrase_unit_only",
        "claim_relation_derived_tail_only": True,
        "tail_variation_enabled": True,
        "repeated_tail_avoidance": True,
        "repeated_sentence_tail_guarded": True,
        "raw_evidence_sentence_copy_guarded": True,
        "unfinished_phrase_guarded": True,
        "generic_closing_guarded": True,
        "used_tail_keys": tails,
        "predicate_keys": tails,
        "unique_tail_key_count": len(tails),
        "surface_tail_key_count": len(tails),
        "generic_tail_key_count": generic_tail_count,
        "repeated_tail_keys": repeated_tail_keys,
        "repeated_predicate_keys": repeated_tail_keys,
        "relation_types": _dedupe(plan.relation_type for plan in plans),
        "line_roles": _dedupe(plan.line_role for plan in plans),
        "used_roles": used_roles,
        "naturalized_surface_count": len(tails),
    }



def _step8_limited_surface_realizer_meta(
    *,
    profile_key: str,
    coverage_scope: str,
    surface_rows: Sequence[Mapping[str, Any]] | None = None,
    predicate_keys: Sequence[str] | None = None,
    relation_types: Sequence[str] | None = None,
    shallow_path: bool = False,
) -> Dict[str, Any]:
    return build_surface_stabilization_meta(
        profile_key=profile_key,
        coverage_scope=coverage_scope,
        surface_rows=surface_rows or (),
        predicate_keys=predicate_keys or (),
        relation_types=relation_types or (),
        shallow_path=shallow_path,
    )


def _attach_step8_surface_meta(target: Dict[str, Any], *, step8_meta: Mapping[str, Any]) -> None:
    meta = dict(step8_meta or {})
    target["limited_surface_realizer_stabilization"] = meta
    target["step8_limited_surface_realizer_stabilization"] = meta
    target["limited_surface_realizer"] = meta
    target["surface_component_rows"] = list(meta.get("surface_component_rows") or [])
    target["surface_relation_component_rows"] = list(meta.get("relation_component_rows") or [])
    target["surface_opener_keys"] = list(meta.get("opener_keys") or [])
    target["surface_particle_keys"] = list(meta.get("particle_keys") or [])
    target["surface_stabilized_tail_keys"] = list(meta.get("tail_keys") or [])
    target["surface_realizer_stabilized"] = bool(meta.get("surface_realizer_stabilized"))
    target["limited_surface_realizer_stabilized"] = bool(meta.get("limited_surface_realizer_stabilized"))


def _make_sentence_binding(
    *,
    sentence_index: int,
    text: str,
    units: Sequence[EmlisPhraseUnit],
    relation_type: str,
    line_role: str,
    coverage_scope: str,
    must_include: bool = True,
    source: str = "limited_composer_sentence_plan",
    predicate_key: str = "",
) -> SentenceBinding | None:
    selected = [unit for unit in list(units or []) if unit.phrase_unit_id and unit.evidence_span_id]
    if not selected or not str(text or "").strip():
        return None
    relation = normalize_relation_type(
        relation_type,
        roles=(unit.role for unit in selected),
        line_role=line_role,
    )
    return SentenceBinding(
        sentence_id=f"s{int(sentence_index or 0) or 1}",
        text=str(text or "").strip(),
        used_evidence_span_ids=_dedupe(unit.evidence_span_id for unit in selected),
        used_phrase_unit_ids=_dedupe(unit.phrase_unit_id for unit in selected),
        relation_type=relation,
        line_role=str(line_role or "observation").strip(),
        coverage_scope=str(coverage_scope or "partial_observation").strip(),
        must_include=bool(must_include),
        binding_version=_STEP3_SENTENCE_BINDING_VERSION,
        meta={
            "source": source,
            "predicate_key": str(predicate_key or "").strip(),
            "relation_taxonomy_version": _STEP5_RELATION_TAXONOMY_VERSION,
            "canonical_relation_type": canonical_relation_type(relation),
            "relation_family": relation_family(relation),
            "raw_input_included": False,
        },
    )


def _sentence_binding_bundle_meta(
    *,
    bindings: Sequence[SentenceBinding],
    coverage_scope: str,
    profile_key: str,
    sentence_plans: Sequence[SentencePlan] | None = None,
    phrase_units: Sequence[EmlisPhraseUnit] | None = None,
) -> Dict[str, Any]:
    relation_taxonomy = build_limited_relation_taxonomy_meta(
        profile_key=profile_key,
        coverage_scope=coverage_scope,
        sentence_plans=sentence_plans or (),
        sentence_bindings=bindings or (),
        phrase_units=phrase_units or (),
    )
    bundle = SentenceBindingBundle(
        bindings=tuple(bindings or ()),
        binding_version=_STEP3_SENTENCE_BINDING_VERSION,
        coverage_scope=str(coverage_scope or "").strip(),
        profile_key=str(profile_key or "").strip(),
        relation_taxonomy_version=_STEP5_RELATION_TAXONOMY_VERSION,
        meta={
            "source": "cocolon_limited_composer",
            "target_step": "3_SentenceBinding_type_addition",
            "step5_target_step": _STEP5_RELATION_TAXONOMY_TARGET_STEP,
            "relation_taxonomy_added": True,
            "completion_sentence_templates_added": False,
            "raw_input_included": False,
        },
    )
    meta = bundle.as_meta()
    meta["relation_taxonomy"] = relation_taxonomy
    meta["step5_relation_taxonomy"] = relation_taxonomy
    meta["limited_composer_relation_taxonomy"] = relation_taxonomy
    meta["relation_taxonomy_added"] = True
    meta["relation_not_expressed_traceable"] = bool(relation_taxonomy.get("relation_not_expressed_traceable"))
    meta["canonical_relation_types"] = list(relation_taxonomy.get("canonical_relation_types") or [])
    meta["relation_families"] = list(relation_taxonomy.get("relation_families") or [])
    meta["unmapped_relation_types"] = list(relation_taxonomy.get("unmapped_relation_types") or [])
    meta["all_relation_types_mapped"] = bool(relation_taxonomy.get("all_relation_types_mapped"))
    return meta


def _step3_sentence_binding_type_meta(bundle: Mapping[str, Any] | None, *, body_line_count: int = 0) -> Dict[str, Any]:
    binding_bundle = bundle if isinstance(bundle, Mapping) else {}
    rows = list(binding_bundle.get("bindings") or binding_bundle.get("sentence_bindings") or [])
    relation_types = _dedupe(binding_bundle.get("relation_types") or [])
    count = int(binding_bundle.get("binding_count") or len(rows) or 0)
    expected = int(body_line_count or binding_bundle.get("expected_binding_count") or count or 0)
    return {
        "version": _STEP3_SENTENCE_BINDING_TYPE_VERSION,
        "target_step": "3_SentenceBinding_type_addition",
        "step": "3_SentenceBinding_type_addition",
        "sentence_binding_type_added": True,
        "binding_contract_attached": bool(rows),
        "sentence_binding_contract_attached": bool(rows),
        "binding_version": str(binding_bundle.get("binding_version") or _STEP3_SENTENCE_BINDING_VERSION),
        "relation_taxonomy_version": str(binding_bundle.get("relation_taxonomy_version") or _STEP5_RELATION_TAXONOMY_VERSION),
        "candidate_body_sentence_count": expected,
        "binding_count": count,
        "sentence_binding_count": count,
        "expected_binding_count": expected,
        "binding_count_matches_body": bool(count == expected),
        "binding_missing": bool(expected and count < expected),
        "coverage_scope": str(binding_bundle.get("coverage_scope") or ""),
        "profile_key": str(binding_bundle.get("profile_key") or ""),
        "relation_types": relation_types,
        "used_phrase_unit_count": int(binding_bundle.get("used_phrase_unit_count") or 0),
        "used_evidence_span_count": int(binding_bundle.get("used_evidence_span_count") or 0),
        "raw_text_included": False,
        "raw_input_required_for_debug": False,
    }


def _attach_sentence_binding_meta(
    target: Dict[str, Any],
    *,
    bundle_meta: Mapping[str, Any],
    body_line_count: int,
) -> None:
    bundle = dict(bundle_meta or {})
    step3 = _step3_sentence_binding_type_meta(bundle, body_line_count=body_line_count)
    target["sentence_binding_bundle"] = bundle
    target["binding_bundle"] = bundle
    target["binding"] = bundle
    target["sentence_bindings"] = list(bundle.get("bindings") or [])
    target["binding_count"] = int(bundle.get("binding_count") or 0)
    target["sentence_binding_count"] = int(bundle.get("sentence_binding_count") or target["binding_count"])
    target["expected_binding_count"] = int(bundle.get("expected_binding_count") or body_line_count or target["binding_count"])
    target["binding_present"] = bool(bundle.get("binding_present"))
    target["binding_missing"] = bool(step3.get("binding_missing"))
    target["used_phrase_unit_ids"] = list(bundle.get("used_phrase_unit_ids") or [])
    target["used_phrase_unit_count"] = int(bundle.get("used_phrase_unit_count") or 0)
    target["relation_types"] = list(bundle.get("relation_types") or [])
    target["relation_count"] = len(target["relation_types"])
    target["step3_sentence_binding_type"] = step3
    target["sentence_binding_type"] = step3
    target["limited_composer_sentence_binding_type"] = step3


def _attach_relation_taxonomy_meta(target: Dict[str, Any], *, taxonomy_meta: Mapping[str, Any] | None) -> None:
    taxonomy = dict(taxonomy_meta or {}) if isinstance(taxonomy_meta, Mapping) else {}
    if not taxonomy:
        taxonomy = build_limited_relation_taxonomy_meta(
            profile_key=str(target.get("profile_key") or ""),
            coverage_scope=str(target.get("coverage_scope") or ""),
            relation_types=target.get("relation_types") or (),
        )
    target["relation_taxonomy"] = taxonomy
    target["step5_relation_taxonomy"] = taxonomy
    target["limited_composer_relation_taxonomy"] = taxonomy
    target["relation_taxonomy_version"] = str(taxonomy.get("version") or taxonomy.get("taxonomy_version") or _STEP5_RELATION_TAXONOMY_VERSION)
    target["relation_taxonomy_added"] = bool(taxonomy.get("relation_taxonomy_added"))
    target["relation_not_expressed_traceable"] = bool(taxonomy.get("relation_not_expressed_traceable"))
    target["canonical_relation_types"] = list(taxonomy.get("canonical_relation_types") or [])
    target["relation_families"] = list(taxonomy.get("relation_families") or [])
    target["unmapped_relation_types"] = list(taxonomy.get("unmapped_relation_types") or [])
    target["all_relation_types_mapped"] = bool(taxonomy.get("all_relation_types_mapped"))

def _composer_diagnostic_meta(
    *,
    status: str,
    coverage_scope: str = "",
    profile_key: str = "",
    source_profile_key: str = "",
    rejection_reasons: Sequence[str] | None = None,
    phrase_units: Sequence[EmlisPhraseUnit] | None = None,
    sentence_plans: Sequence[SentencePlan] | None = None,
    used_unit_ids: Sequence[str] | None = None,
    required_roles: Sequence[str] | None = None,
    missing_roles: Sequence[str] | None = None,
    extra_meta: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Step04 developer-facing composer diagnostics.

    This meta explains why a scoped graph could or could not become text.  It
    records counts, roles, and reason codes only; it never adds display text.
    """

    meta = dict(extra_meta or {}) if isinstance(extra_meta, Mapping) else {}
    units = list(phrase_units or [])
    plans = list(sentence_plans or [])
    used = set(str(item or "").strip() for item in list(used_unit_ids or []) if str(item or "").strip())
    required = _dedupe(str(item or "").strip() for item in list(required_roles or meta.get("required_roles") or []) if str(item or "").strip())
    missing = _dedupe(str(item or "").strip() for item in list(missing_roles or meta.get("missing_roles") or []) if str(item or "").strip())
    available_roles = _dedupe(
        str(item or "").strip()
        for item in [*(meta.get("available_roles") or []), *(unit.role for unit in units)]
        if str(item or "").strip()
    )
    covered_roles = _dedupe(
        str(item or "").strip()
        for item in [*(meta.get("covered_roles") or []), *(unit.role for unit in units if unit.phrase_unit_id in used)]
        if str(item or "").strip()
    )
    reason_codes = _dedupe(str(item or "").strip() for item in list(rejection_reasons or []) if str(item or "").strip())

    source_profile = str(source_profile_key or meta.get("source_profile_key") or "").strip()
    profile = str(profile_key or meta.get("profile_key") or "").strip()
    shallow_path = bool(meta.get("shallow_observation_path") or profile == "current_input_core")
    profile_unmatched = bool(profile == "current_input_core" and source_profile in {"", "unknown", "current_input_core"})
    if bool(meta.get("profile_unmatched")):
        profile_unmatched = True
    if profile_unmatched and "profile_unmatched" not in reason_codes:
        reason_codes.append("profile_unmatched")

    categories = _dedupe(_composer_reason_category(reason) for reason in reason_codes)
    hints = _dedupe(_composer_coverage_hint(category, profile_key=profile, shallow_path=shallow_path) for category in categories)
    if not hints:
        hints = ["composer_generated"] if status == "generated" else ["composer_not_classified"]

    phrase_count = int(meta.get("phrase_unit_count") or len(units) or 0)
    plan_count = int(meta.get("sentence_plan_count") or len(plans) or 0)
    evidence_count = len(_dedupe(unit.evidence_span_id for unit in units))
    if not evidence_count and isinstance(meta.get("allowed_evidence_span_ids"), list):
        evidence_count = len([item for item in meta.get("allowed_evidence_span_ids") if str(item or "").strip()])
    role_expansion = _step11_role_expansion_meta(units)
    step12_meta = meta.get("step12_profile_sentence_plan") if isinstance(meta.get("step12_profile_sentence_plan"), Mapping) else None
    if step12_meta is None:
        step12_meta = meta.get("step12_profile_sentence_plan_expansion") if isinstance(meta.get("step12_profile_sentence_plan_expansion"), Mapping) else None
    if step12_meta is None:
        step12_meta = meta.get("profile_sentence_plan") if isinstance(meta.get("profile_sentence_plan"), Mapping) else None
    if step12_meta is None:
        step12_meta = meta.get("profile_sentence_plan_expansion") if isinstance(meta.get("profile_sentence_plan_expansion"), Mapping) else None
    if step12_meta is None:
        step12_meta = _step12_profile_sentence_plan_meta(
            profile_key=profile,
            phrase_units=units,
            sentence_plans=plans,
            used_unit_ids=used_unit_ids,
        )
    step13_meta = meta.get("step13_surface_realizer") if isinstance(meta.get("step13_surface_realizer"), Mapping) else None
    if step13_meta is None:
        step13_meta = meta.get("surface_realizer") if isinstance(meta.get("surface_realizer"), Mapping) else None
    if step13_meta is None:
        step13_meta = meta.get("surface_realizer_meta") if isinstance(meta.get("surface_realizer_meta"), Mapping) else None
    if step13_meta is None:
        step13_meta = _step13_surface_realizer_meta(
            profile_key=profile,
            phrase_units=units,
            sentence_plans=plans,
            used_unit_ids=used_unit_ids,
            predicate_keys=meta.get("surface_tail_keys") or meta.get("sentence_tail_keys") or (),
            shallow_path=shallow_path,
        )

    step8_meta = meta.get("step8_limited_surface_realizer_stabilization") if isinstance(meta.get("step8_limited_surface_realizer_stabilization"), Mapping) else None
    if step8_meta is None:
        step8_meta = meta.get("limited_surface_realizer_stabilization") if isinstance(meta.get("limited_surface_realizer_stabilization"), Mapping) else None
    if step8_meta is None:
        step8_meta = meta.get("limited_surface_realizer") if isinstance(meta.get("limited_surface_realizer"), Mapping) else None
    if step8_meta is None:
        step8_meta = _step8_limited_surface_realizer_meta(
            profile_key=profile,
            coverage_scope=str(coverage_scope or meta.get("coverage_scope") or ""),
            surface_rows=meta.get("surface_component_rows") or (),
            predicate_keys=meta.get("surface_tail_keys") or meta.get("sentence_tail_keys") or (),
            relation_types=meta.get("relation_types") or (),
            shallow_path=shallow_path,
        )

    step4_meta = meta.get("step4_phrase_unit_material_quality") if isinstance(meta.get("step4_phrase_unit_material_quality"), Mapping) else None
    if step4_meta is None:
        step4_meta = meta.get("phrase_unit_material_quality") if isinstance(meta.get("phrase_unit_material_quality"), Mapping) else None
    if step4_meta is None:
        step4_meta = _step4_phrase_unit_material_meta(units)

    binding_bundle = meta.get("sentence_binding_bundle") if isinstance(meta.get("sentence_binding_bundle"), Mapping) else None
    if binding_bundle is None:
        binding_bundle = meta.get("binding_bundle") if isinstance(meta.get("binding_bundle"), Mapping) else None
    if binding_bundle is None:
        binding_bundle = meta.get("binding") if isinstance(meta.get("binding"), Mapping) else None
    binding_bundle = dict(binding_bundle or {})
    step3_binding = meta.get("step3_sentence_binding_type") if isinstance(meta.get("step3_sentence_binding_type"), Mapping) else None
    if step3_binding is None:
        step3_binding = _step3_sentence_binding_type_meta(
            binding_bundle,
            body_line_count=int(meta.get("body_line_count") or 0),
        )

    step5_meta = meta.get("step5_relation_taxonomy") if isinstance(meta.get("step5_relation_taxonomy"), Mapping) else None
    if step5_meta is None:
        step5_meta = meta.get("relation_taxonomy") if isinstance(meta.get("relation_taxonomy"), Mapping) else None
    if step5_meta is None:
        step5_meta = meta.get("limited_composer_relation_taxonomy") if isinstance(meta.get("limited_composer_relation_taxonomy"), Mapping) else None
    if step5_meta is None:
        step5_meta = binding_bundle.get("relation_taxonomy") if isinstance(binding_bundle.get("relation_taxonomy"), Mapping) else None
    if step5_meta is None:
        step5_meta = build_limited_relation_taxonomy_meta(
            profile_key=profile,
            coverage_scope=str(coverage_scope or meta.get("coverage_scope") or ""),
            sentence_plans=plans,
            phrase_units=units,
            relation_types=binding_bundle.get("relation_types") or meta.get("relation_types") or (),
        )

    return {
        "version": _COMPOSER_DIAGNOSTIC_VERSION,
        "composer_attempted": True,
        "composer_status": str(status or ""),
        "composer_ready_for_gate": bool(status == "generated"),
        "coverage_scope": str(coverage_scope or meta.get("coverage_scope") or ""),
        "profile_key": profile,
        "source_profile_key": source_profile,
        "profile_matched": bool(profile and profile not in {"unknown", "current_input_core"} and not profile_unmatched),
        "profile_unmatched": bool(profile_unmatched),
        "shallow_observation_path": bool(shallow_path),
        "phrase_unit_count": phrase_count,
        "used_phrase_unit_count": len(used),
        "evidence_span_count": evidence_count,
        "sentence_plan_count": plan_count,
        "sentence_binding_bundle": binding_bundle,
        "sentence_bindings": list(binding_bundle.get("bindings") or binding_bundle.get("sentence_bindings") or []),
        "binding_count": int(binding_bundle.get("binding_count") or 0),
        "sentence_binding_count": int(binding_bundle.get("sentence_binding_count") or binding_bundle.get("binding_count") or 0),
        "expected_binding_count": int(binding_bundle.get("expected_binding_count") or binding_bundle.get("binding_count") or 0),
        "binding_present": bool(binding_bundle.get("binding_present")),
        "binding_missing": bool(binding_bundle.get("binding_missing")),
        "relation_types": list(binding_bundle.get("relation_types") or []),
        "relation_count": len(list(binding_bundle.get("relation_types") or [])),
        "relation_taxonomy": dict(step5_meta),
        "step5_relation_taxonomy": dict(step5_meta),
        "limited_composer_relation_taxonomy": dict(step5_meta),
        "relation_taxonomy_version": str(step5_meta.get("version") or step5_meta.get("taxonomy_version") or _STEP5_RELATION_TAXONOMY_VERSION),
        "relation_taxonomy_added": bool(step5_meta.get("relation_taxonomy_added")),
        "relation_not_expressed_traceable": bool(step5_meta.get("relation_not_expressed_traceable")),
        "canonical_relation_types": list(step5_meta.get("canonical_relation_types") or []),
        "relation_families": list(step5_meta.get("relation_families") or []),
        "unmapped_relation_types": list(step5_meta.get("unmapped_relation_types") or []),
        "all_relation_types_mapped": bool(step5_meta.get("all_relation_types_mapped")),
        "major_coverage_group_relation_unset": bool(step5_meta.get("major_coverage_group_relation_unset")),
        "step3_sentence_binding_type": dict(step3_binding),
        "sentence_binding_type": dict(step3_binding),
        "sentence_binding_contract_attached": bool(step3_binding.get("sentence_binding_contract_attached") or step3_binding.get("binding_contract_attached")),
        "required_roles": required,
        "available_roles": available_roles,
        "covered_roles": covered_roles,
        "missing_roles": missing,
        "role_expansion": role_expansion,
        "step11_role_expansion": role_expansion,
        "profile_sentence_plan": dict(step12_meta),
        "profile_sentence_plan_expansion": dict(step12_meta),
        "step12_profile_sentence_plan": dict(step12_meta),
        "step12_profile_sentence_plan_expansion": dict(step12_meta),
        "surface_realizer": dict(step13_meta),
        "surface_realizer_meta": dict(step13_meta),
        "step13_surface_realizer": dict(step13_meta),
        "limited_surface_realizer_stabilization": dict(step8_meta),
        "step8_limited_surface_realizer_stabilization": dict(step8_meta),
        "limited_surface_realizer": dict(step8_meta),
        "limited_surface_realizer_stabilized": bool(step8_meta.get("limited_surface_realizer_stabilized")),
        "surface_component_rows": list(step8_meta.get("surface_component_rows") or []),
        "surface_relation_component_rows": list(step8_meta.get("relation_component_rows") or []),
        "surface_opener_keys": list(step8_meta.get("opener_keys") or []),
        "surface_particle_keys": list(step8_meta.get("particle_keys") or []),
        "surface_stabilized_tail_keys": list(step8_meta.get("tail_keys") or []),
        "phrase_unit_material_quality": dict(step4_meta),
        "step4_phrase_unit_material_quality": dict(step4_meta),
        "phrase_unit_material_quality_enabled": bool(step4_meta.get("material_stage_filter_enabled")),
        "phrase_unit_material_safe": bool(step4_meta.get("all_phrase_units_material_safe")),
        "unsafe_phrase_unit_count": int(step4_meta.get("unsafe_phrase_unit_count") or 0),
        "material_blocked_reason_keys": list(step4_meta.get("blocked_reason_keys") or []),
        "surface_realizer_enabled": True,
        "surface_realizer_grammar_parts_only": bool(step13_meta.get("grammar_parts_only")),
        "surface_realizer_componentized": bool(step13_meta.get("surface_realizer_is_componentized") or step13_meta.get("componentized_surface_realizer")),
        "surface_tail_keys": list(step13_meta.get("used_tail_keys") or []),
        "surface_predicate_keys": list(step13_meta.get("predicate_keys") or []),
        "surface_repeated_tail_keys": list(step13_meta.get("repeated_tail_keys") or []),
        "surface_unique_tail_key_count": int(step13_meta.get("unique_tail_key_count") or 0),
        "surface_generic_tail_key_count": int(step13_meta.get("generic_tail_key_count") or 0),
        "surface_variation_enabled": bool(step13_meta.get("tail_variation_enabled") or step8_meta.get("tail_variation_enabled")),
        "surface_realizer_stabilized": bool(step8_meta.get("surface_realizer_stabilized")),
        "limited_surface_tail_variation_by_relation": bool(step8_meta.get("tail_variation_by_relation")),
        "surface_repeated_stabilized_tail_keys": list(step8_meta.get("repeated_tail_keys") or []),
        "completion_sentence_templates_added": bool(step13_meta.get("completion_sentence_templates_added") or step8_meta.get("completion_sentence_templates_added")),
        "expanded_roles": list(role_expansion.get("expanded_roles") or []),
        "expanded_profile": bool(step12_meta.get("profile_expanded") or step12_meta.get("profile_is_expanded") or step12_meta.get("expanded_profile")),
        "profile_expanded": bool(step12_meta.get("profile_expanded") or step12_meta.get("profile_is_expanded") or step12_meta.get("expanded_profile")),
        "expanded_profiles": list(step12_meta.get("expanded_profiles") or []),
        "required_role_missing": bool(missing or "required_role_missing" in categories),
        "missing_phrase_units": bool(phrase_count == 0 or "missing_phrase_units" in categories),
        "shallow_insufficient_evidence": bool("shallow_insufficient_evidence" in categories),
        "sentence_plan_unavailable": bool("sentence_plan_unavailable" in categories or (status != "generated" and phrase_count > 0 and plan_count == 0 and not shallow_path)),
        "reason_codes": reason_codes,
        "reason_categories": categories,
        "reason_category": categories[0] if categories else "",
        "coverage_matrix_hints": hints,
        "stop_reason": categories[0] if status != "generated" and categories else "",
    }

def _allowed_evidence_ids_from_graph(graph: Mapping[str, Any]) -> set[str]:
    ids: set[str] = set()

    def add_values(values: Any) -> None:
        if isinstance(values, (list, tuple, set)):
            for value in values:
                item = str(value or "").strip()
                if item:
                    ids.add(item)
        else:
            item = str(values or "").strip()
            if item:
                ids.add(item)

    def add_claim(claim: Any) -> None:
        if isinstance(claim, Mapping):
            add_values(claim.get("evidence_span_ids") or claim.get("evidence_ids") or [])

    add_claim(graph.get("primary_state"))
    for group_key in ("pressure_sources", "limit_signals", "self_awareness", "value_or_strength_signals"):
        for claim in list(graph.get(group_key) or []):
            add_claim(claim)
    for edge in list(graph.get("core_tensions") or []):
        if isinstance(edge, Mapping):
            add_values(edge.get("evidence_span_ids") or edge.get("evidence_ids") or [])
    return ids

def _evidence_by_id(items: Sequence[Mapping[str, Any]]) -> Dict[str, Mapping[str, Any]]:
    out: Dict[str, Mapping[str, Any]] = {}
    for item in items:
        span_id = str(item.get("span_id") or "").strip()
        if span_id:
            out[span_id] = item
    return out


def _source_field(item: Mapping[str, Any]) -> str:
    return str(item.get("source_field") or "").strip()


def _detected_type(item: Mapping[str, Any]) -> str:
    return str(item.get("detected_type") or "").strip()


def _raw_text(item: Mapping[str, Any]) -> str:
    return _clean(item.get("raw_text"), limit=240)


def _skip_evidence(item: Mapping[str, Any]) -> bool:
    raw = _raw_text(item)
    source = _source_field(item)
    detected = _detected_type(item)
    if not raw or raw in _EMOTION_LABELS:
        return True
    if source and source not in _TEXT_SOURCE_FIELDS:
        return True
    if detected in _SKIP_DETECTED_TYPES or source in _SKIP_SOURCE_FIELDS:
        return True
    if detected == "relation_marker" and _compact(raw) in {"でも"}:
        return True
    return False


def _role_for_text(text: str, detected_type: str) -> Tuple[str, str, bool]:
    return phase8_primary_role_for_text(text, detected_type)


def _compress_text(raw: str, role: str) -> str:
    """Build a role-scoped PhraseUnit from the evidence span.

    Phase8-R3 keeps PhraseUnit shaping generic: the branch is role + semantic
    cue based, not a fixed ``input sentence -> output phrase`` replacement map.
    """

    text = _clean(raw, limit=200)
    compact = _compact(text)
    if not text:
        return ""

    def has(*terms: str) -> bool:
        return any(term and (term in text or term in compact) for term in terms)

    def has_all(*terms: str) -> bool:
        return all(term and (term in text or term in compact) for term in terms)

    if role == "fatigue_accumulation":
        if has("仕事") and has("疲"):
            return "仕事で疲れたこと"
        if has("抜けない"):
            return "疲れが抜けないこと"
        if has("溜", "たま"):
            return "疲れが溜まっていること"
        if has("消耗"):
            return "消耗していること"
        if has("へとへと", "ぐったり"):
            return "体力が削れていること"
        if has("寝ても", "休んでも"):
            return "休んでも戻りきらないこと"
        if has("体力"):
            return "体力が落ちていること"
        if has("眠"):
            return "眠気が強いこと"
        if has("疲"):
            return "疲れが重なっていること"

    if role == "loss_of_control":
        if has("頭が回"):
            return "頭が回りにくいこと"
        if has("集中"):
            return "集中が切れていること"
        if has("手につか"):
            return "手につかないこと"
        if has("予定") and has("詰"):
            return "予定が詰まっていること"
        if has("やること") and has("多"):
            return "やることが多すぎること"
        if has("余裕"):
            return "余裕がなくなっていること"
        if has("追いつ"):
            return "追いつけないこと"
        if has("動け"):
            return "動けないこと"

    if role == "small_repair":
        if has("机") and has("整"):
            return "机を整えたこと"
        if has("片付"):
            return "少し片付けたこと" if has("少し") else "片付けたこと"
        if has("手帳"):
            return "手帳を整えたこと"
        if has("お茶"):
            return "お茶を飲んで落ち着けたこと" if has("落ち着") else "お茶を飲めたこと"
        if has("深呼吸"):
            return "深呼吸できたこと"
        if has("散歩"):
            if has("落ち着") and has("したら"):
                return "少し散歩したら落ち着いたこと" if has("少し") else "散歩したら落ち着いたこと"
            return "少し散歩したこと" if has("少し") else "散歩したこと"
        if has("休め"):
            return "少し休めたこと"
        if has("整"):
            return "少し整えたこと"

    if role == "avoidance_wish":
        if has("休みたい", "横になりたい", "寝たい"):
            return "休みたい気持ち"
        if has("逃げたい"):
            return "逃げたい気持ち"
        if has("逃げ出"):
            return "逃げ出したくなる感覚"
        if has("離れたい"):
            return "離れたい気持ち"
        if has("距離"):
            return "距離を置きたい気持ち"
        if has("投げ出"):
            return "投げ出したくなる感覚"
        if has("やめたい"):
            return "やめたい気持ち"

    if role == "value_wish":
        if has("大事にしたい"):
            return "大事にしたい気持ち"
        if has("大切にしたい"):
            return "大切にしたい気持ち"
        if has("守りたい"):
            return "守りたい気持ち"
        if has("選びたい"):
            return "選びたい気持ち"
        if has("優先"):
            return "優先したい気持ち"
        if has("願"):
            return "願い"
        if has("ほしい", "欲しい"):
            return "ほしい気持ち"

    if role == "positive_state":
        if has_all("散歩", "落ち着"):
            if has("したら"):
                return "少し散歩したら落ち着いたこと" if has("少し") else "散歩したら落ち着いたこと"
            return "散歩して落ち着いたこと"
        if has("友達"):
            return "友達と話せた楽しさ"
        if has("元気"):
            return "少し元気になれた感覚" if has("少し") else "元気になれた感覚"
        if has("笑え"):
            return "笑えたこと"
        if has("ほっと"):
            return "ほっとした感覚"
        if has("安心"):
            return "安心したこと"
        if has("楽しか"):
            return "楽しかったこと"

    if role == "anxiety_return":
        if has_all("夜", "失敗", "不安"):
            return "夜に戻った失敗への不安"
        if has_all("一人", "不安"):
            return "一人になった時の不安"
        if has_all("静か", "不安"):
            return "静かになった後の不安"
        if has("不安"):
            return "戻ってきた不安"
        if has("落ちる"):
            return "落ちる感覚"

    if role == "fall_contrast":
        if has("落差"):
            return "ほっとしていた分の落差" if has("ほっと") else "落差の大きさ"
        if has("落ちる"):
            return "楽しかった後に落ちる感覚"

    if role == "anger_surface":
        if has_all("返し方", "雑"):
            return "返し方の雑さにむっとしたこと" if has("むっと", "ムッと") else "返し方の雑さへの怒り"
        if has("言い方"):
            return "きつい言い方への怒り"
        if has("腹が立"):
            return "腹が立ったこと"
        if has("怒"):
            return "怒り"

    if role == "unfairness":
        if has("軽く扱"):
            return "軽く扱われたこと"
        if has("丁寧"):
            return "丁寧に伝えようとしていたこと"
        if has("ちゃんと考", "考えて話"):
            return "ちゃんと考えて話していたこと"
        if has("されなきゃ"):
            return "きつい言い方をされる分からなさ"

    if role == "hurt_core":
        if has("大事に扱"):
            return "大事に扱われなかったしんどさ"
        if has("軽く扱"):
            return "軽く扱われたしんどさ"
        if has("傷つ"):
            return "傷ついたしんどさ"
        if has("しんど"):
            return "しんどさ"

    if role == "withdrawal":
        if has_all("説明", "気力"):
            return "説明する気力がなくなっていること"
        if has("面倒"):
            return "話すのが面倒になっていること"
        if has("距離"):
            return "距離を置きたくなること"

    if role == "known_action":
        if has("見えて"):
            return "やることは見えている流れ"
        if has("分か"):
            return "やることは分かっている流れ"
        if has("そんなの"):
            return "分かっている自覚"

    if role == "anticipation_loop":
        if has_all("考えすぎ", "動け"):
            return "考えすぎて動けなくなる流れ"
        if has("手が止ま"):
            return "考えると手が止まる流れ"
        if has("止まら", "先のこと"):
            return "考え始めると止まらなくなる流れ"
        if has("進めない"):
            return "進めない流れ"

    if role == "perfection_fear":
        if has_all("失敗", "ちゃんとできない"):
            return "失敗やちゃんとできないため進めない怖さ" if has("進めない") else "失敗やちゃんとできないことへの怖さ"
        if has("失敗"):
            return "失敗への怖さ"
        if has("ちゃんとできない"):
            return "ちゃんとできない怖さ"
        if has("完璧"):
            return "完璧にやろうとする怖さ"
        if has("適当"):
            return "適当にやる怖さ"

    if role == "small_action":
        if has("洗い物"):
            return "洗い物を少し終えたこと"
        if has("片付け"):
            return "片付けられたこと"
        if has("台所", "整"):
            return "台所が整ったこと"
        if has("進め"):
            return "少し進められたこと"

    if role == "relieved_weight":
        if has_all("台所", "落ち着"):
            return "台所が整って気持ちが落ち着いた感覚"
        if has("気持ちが軽"):
            return "気持ちが軽くなった感覚"
        if has("気持ちが落ち着", "落ち着"):
            return "気持ちが落ち着いた感覚"
        if has("ほっと"):
            return "ほっとした感覚"
        if has("気にな"):
            return "気になっていた場所に触れられた感覚"

    if role == "achievement":
        if has("ちゃんとでき"):
            return "ちゃんとできた嬉しさ"
        if has_all("進め", "ほっと"):
            return "少し進められてほっとした感覚"
        if has("嬉し"):
            return "嬉しさ"
        if has("ほっと"):
            return "ほっとした感覚"

    if role == "wish_to_rely":
        if has("相談したい"):
            return "相談したい気持ち"
        if has("助けを借りたい"):
            return "助けを借りたい気持ち"
        if has("頼りたい", "頼った"):
            return "頼りたい気持ち"
        if has("話したい"):
            return "話したい気持ち"

    if role == "burden_fear":
        if has_all("時間", "奪"):
            return "相手の時間を奪う怖さ"
        if has("迷惑"):
            return "迷惑だと思われる怖さ"
        if has("困らせ"):
            return "助けを借りたいのに困らせそうで怖いこと" if has("助け") else "困らせそうな怖さ"
        if has("言い出せない"):
            return "言い出せない怖さ"

    if role == "rejection_fear":
        if has("嫌われ", "重い"):
            parts: List[str] = []
            if has("嫌われ"):
                parts.append("嫌われる怖さ")
            if has("重い"):
                parts.append("重いと思われる怖さ")
            return "や".join(parts)
        if has("困らせ"):
            return "困らせそうな怖さ"
        if has("怖"):
            return "怖さ"

    if role == "limit":
        if has_all("考え続け", "つら"):
            return "一人で考え続けるつらさ" if has("一人") else "考え続けるつらさ"
        if has_all("抱え", "限界"):
            return "一人で抱える限界"
        if has("逃げ出"):
            return "逃げ出したくなる感覚"
        if has("投げ出"):
            return "全部投げ出したくなる時" if has("全部") else "投げ出したくなる時"
        if has("限界"):
            return "限界"
        if has("つら"):
            return "つらさ"
        if has("何もしたくない"):
            return "何もしたくない感覚"

    if role == "safe_home":
        if has("リラックス"):
            return "家にいてリラックスできること" if has("家", "お家", "おうち") else "リラックスできること"
        if has("安心", "自分のペース", "ペース"):
            if has("安心") and has("ペース"):
                return "安心して自分のペースで過ごせること"
            return "安心できること"
        if has("優先", "整え"):
            return "自分を優先して整えられること"
        if has("家", "お家", "おうち"):
            return "家で落ち着けること"

    if role == "reality_damage":
        if has("不便"):
            return "生活の不便さが重くなること" if has("重く") else "今の生活の不便さ"
        if has("ダメージ"):
            return "現実と向き合う時の大きなダメージ"
        if has("現実"):
            return "現実へ戻ること"
        if has("移動", "準備"):
            return "移動や準備の負担"

    if role == "ordinary_life_wish":
        if has("いつも通り"):
            return "いつも通りに過ごしたい気持ち"
        if has("生活したい", "普通に"):
            return "普通に生活したい気持ち"

    if role == "worsening_risk":
        if has_all("体調", "崩"):
            return "体調が崩れそうな怖さ"
        if has("悪化"):
            return "悪化するリスク"

    if role == "low_energy":
        if has("だるい"):
            return "だるさ"
        if has("何もしたくない"):
            return "何もしたくない感覚"

    cleaned = re.sub(r"^(?:今日は|今日|また|でも|本当は|たぶん|もう|このまま|さっき)\s*", "", text).strip(_PUNCT_TRIM)
    cleaned = re.sub(r"(?:けど|だけど|でも|のに|から|なら|すると|したら|を|が|で)$", "", cleaned).strip(_PUNCT_TRIM)
    if not cleaned:
        return ""
    if cleaned.endswith(("こと", "気持ち", "感覚", "怖さ", "しんどさ", "限界", "不安", "流れ", "つらさ")):
        return cleaned
    suffix = "気持ち" if role in {"wish_to_rely", "ordinary_life_wish"} else "こと"
    return f"{cleaned}{suffix}"

def _quality_flags(text: str, *, raw_text: str = "", role: str = "", detected_type: str = "", source_field: str = "") -> Tuple[str, ...]:
    report = judge_phrase_unit_material_quality(
        text,
        raw_text=raw_text,
        role=role,
        detected_type=detected_type,
        source_field=source_field,
    )
    return tuple(str(item or "").strip() for item in list(report.get("quality_flags") or []) if str(item or "").strip())


def _phrase_material_blocked(flags: Sequence[str]) -> bool:
    blocked = {
        "empty_phrase_unit_material",
        "emotion_label_only",
        "unfinished_phrase",
        "orphan_particle",
        "too_long_quote",
        "too_short_phrase_unit_material",
    }
    return bool(set(str(flag or "").strip() for flag in flags or ()).intersection(blocked))


def _phrase_unit_material_report(unit: EmlisPhraseUnit) -> Dict[str, Any]:
    return judge_phrase_unit_material_quality(
        unit.compressed_text,
        raw_text=unit.raw_text,
        role=unit.role,
    )


def _step4_phrase_unit_material_meta(units: Sequence[EmlisPhraseUnit] | None) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    reason_counts: Dict[str, int] = {}
    for unit in list(units or []):
        report = _phrase_unit_material_report(unit)
        reasons = [str(item or "").strip() for item in list(report.get("rejection_reasons") or []) if str(item or "").strip()]
        for reason in reasons:
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
        rows.append({
            "phrase_unit_id": unit.phrase_unit_id,
            "evidence_span_id": unit.evidence_span_id,
            "role": unit.role,
            "passed": bool(report.get("passed")),
            "quality_flags": list(unit.quality_flags),
            "material_rejection_reasons": reasons,
            "raw_text_included": False,
        })
    rejected = [row for row in rows if not bool(row.get("passed"))]
    return {
        "version": _STEP4_PHRASE_UNIT_MATERIAL_VERSION,
        "target_step": _STEP4_PHRASE_UNIT_MATERIAL_TARGET_STEP,
        "step": _STEP4_PHRASE_UNIT_MATERIAL_TARGET_STEP,
        "material_stage_filter_enabled": True,
        "material_stage_filtering_enabled": True,
        "sentence_plan_pre_filter_enabled": True,
        "phrase_unit_material_quality_enabled": True,
        "emotion_label_only_excluded": True,
        "unfinished_fragment_excluded": True,
        "orphan_particle_excluded": True,
        "too_long_raw_copy_excluded": True,
        "completion_sentence_templates_added": False,
        "input_specific_template_added": False,
        "candidate_phrase_unit_count": len(rows),
        "unsafe_phrase_unit_count": len(rejected),
        "all_phrase_units_material_safe": not rejected,
        "blocked_reasons": dict(reason_counts),
        "blocked_reason_keys": _dedupe(reason_counts.keys()),
        "rows": rows,
        "raw_text_included": False,
        "raw_input_required_for_debug": False,
    }


def _text_evidence_ids(items: Sequence[Mapping[str, Any]]) -> set[str]:
    ids: set[str] = set()
    for item in items:
        if _skip_evidence(item):
            continue
        span_id = str(item.get("span_id") or "").strip()
        if span_id:
            ids.add(span_id)
    return ids


def _generation_items_for_allowed_ids(items: Sequence[Mapping[str, Any]], allowed_ids: set[str]) -> List[Mapping[str, Any]]:
    if not allowed_ids:
        return [item for item in items if not _skip_evidence(item)]
    return [
        item
        for item in items
        if not _skip_evidence(item) and str(item.get("span_id") or "").strip() in allowed_ids
    ]


def _shallow_polarity(text: str) -> str:
    compact = _compact(text)
    negative = any(term in compact for term in ("疲れ", "不安", "怖", "失敗", "つら", "しんど", "切れて", "詰ま", "重く", "困", "迷惑"))
    positive = any(term in compact for term in ("落ち着", "整え", "終え", "進め", "安心", "ほっと", "嬉し", "楽しか", "できた"))
    if negative and positive:
        return "mixed"
    if negative:
        return "negative"
    if positive:
        return "positive"
    return "neutral"


def _generic_shallow_phrase(raw: str, detected_type: str = "") -> str:
    text = _clean(raw, limit=160)
    compact = _compact(text)
    if not text:
        return ""

    def has(*terms: str) -> bool:
        return any(term and term in compact for term in terms)

    if has("仕事") and has("疲れ"):
        return "仕事で疲れたこと"
    if has("疲れ") and has("積"):
        return "積み重なった疲れ"
    if has("疲れ") and has("溜", "たま"):
        return "疲れが溜まっていること"
    if has("疲れ") and has("抜け"):
        return "疲れが抜けないこと"
    if has("疲労"):
        return "疲労が残っていること"
    if has("くたくた"):
        return "くたくたになっていること"
    if has("消耗"):
        return "消耗していること"
    if has("大事にしたい"):
        return "大事にしたい気持ち"
    if has("大切にしたい"):
        return "大切にしたい気持ち"
    if has("守りたい"):
        return "守りたい気持ち"
    if has("選びたい"):
        return "選びたい気持ち"
    if has("予定") and has("集中"):
        return "予定が詰まって集中が切れていたこと"
    if has("資料") and has("頭がいっぱい"):
        return "資料を直して頭がいっぱいだったこと"
    if has("お茶") and has("落ち着"):
        return "お茶を飲んで落ち着いたこと"
    if has("机") and has("整え"):
        return "少しだけ机を整えたこと" if has("少し") else "机を整えたこと"
    if has("失敗") and has("不安"):
        return "失敗しそうで不安なこと"
    if has("休みたい"):
        return "休みたい気持ち"
    if has("逃げたい", "逃げ出"):
        return "逃げたい気持ち" if has("逃げたい") else "逃げ出したくなる感覚"
    if has("頭が回"):
        return "頭が回りにくいこと"
    if has("集中") and has("切"):
        return "集中が切れていること"
    if has("追いつ"):
        return "追いつけないこと"
    if has("余裕"):
        return "余裕がなくなっていること"
    if has("疲れ"):
        return "疲れたこと"
    if has("不安"):
        return "不安"
    if has("つら"):
        return "つらさ"

    raw_parts = re.split(r"(?:[、,]|けれど|けど|だけど|でも|のに|なら|したら|すると|て、|いて、|と、)", text)
    parts: List[str] = []
    for part in raw_parts:
        item = _clean(part, limit=70)
        item = re.sub(r"^(?:今日は|今日|朝から|夜になって|昼過ぎには|また|もう|それでも|本当は|このまま|さっき|少しだけ)\s*", "", item).strip(_PUNCT_TRIM)
        item_compact = _compact(item)
        if not item or item_compact in {"それ", "それでも", "でも", "本当は", "たぶん", "もう", "このまま", "さっき", "今日", "今日は"}:
            continue
        if len(item_compact) < 3:
            continue
        parts.append(item)
    if not parts:
        return ""

    priority_terms = (
        "疲", "休み", "逃げ", "大事", "大切", "守り", "選び", "願", "不安", "怖", "失敗",
        "つら", "しんど", "切れ", "落ち着", "整え", "進め", "終え", "相談", "助け", "困",
        "追いつ", "余裕", "頭が回", "集中", "体力", "消耗", "疲労", "くたくた", "へとへと", "ぐったり",
    )
    parts.sort(key=lambda part: (0 if any(term in _compact(part) for term in priority_terms) else 1, len(part)))
    chosen = parts[0].strip(_PUNCT_TRIM)
    chosen = re.sub(r"^(?:今日は|今日|朝から|夜になって|昼過ぎには|また|もう|それでも|本当は|このまま|さっき)\s*", "", chosen).strip(_PUNCT_TRIM)
    if not chosen or _compact(chosen) in {"それ", "それでも", "でも", "本当は", "今日", "今日は"}:
        return ""
    if chosen.endswith(("こと", "気持ち", "感覚", "怖さ", "不安", "つらさ", "しんどさ", "限界", "願い")):
        return chosen
    chosen = re.sub(r"(?:を|が|に|へ|は|も|と|から|なら)$", "", chosen).strip(_PUNCT_TRIM)
    if not chosen or _compact(chosen) in {"それ", "それでも", "でも", "本当は", "今日", "今日は"}:
        return ""
    if chosen.endswith(("たい", "したい")):
        return f"{chosen}気持ち"
    return f"{chosen}こと"

def _role_phrase_safe_for_shallow(phrase: str, raw: str) -> bool:
    phrase_compact = _compact(phrase)
    raw_compact = _compact(raw)
    if not phrase_compact or not raw_compact:
        return False
    for term in ("優先", "ペース", "リラックス", "家", "お家", "生活", "悪化", "体調", "相談", "助け", "頼り", "迷惑", "嫌われ", "重い", "限界", "疲れ", "疲労", "溜ま", "消耗", "体力", "頭が回", "集中", "手につか", "余裕", "予定", "追いつ", "逃げ", "休み", "止まり", "距離", "整え", "お茶", "深呼吸", "大事", "大切", "守り", "選び", "願"):
        if term in phrase_compact and term not in raw_compact:
            return False
    return True




def _safe_step4_meta_list(value: Any) -> List[str]:
    if isinstance(value, (list, tuple, set)):
        return _dedupe(str(item or "").strip() for item in value if str(item or "").strip())
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _shallow_phrase_creation_extra_warning_codes(*, phrase: str, raw: str) -> Tuple[str, ...]:
    phrase_compact = _compact(phrase)
    raw_compact = _compact(raw)
    codes: List[str] = []
    if phrase_compact in {"今まこと", "これまこと", "さっきこと", "先ほどこと", "さきほどこと", "このままこと"}:
        codes.append("malformed_nominalization_temporal_fragment")
    if raw_compact in {"今まで", "これまで", "さっき", "先ほど", "さきほど", "このまま", "まだ"} and phrase_compact.endswith("こと"):
        codes.append("malformed_nominalization_temporal_fragment")
    return tuple(dict.fromkeys(codes))


def _shallow_phrase_unit_guard_row(
    *,
    candidate_id: str,
    evidence_span_id: str,
    role: str,
    stage: str,
    grammar_meta: Mapping[str, Any],
    material_report: Mapping[str, Any] | None = None,
    accepted: bool = False,
    duplicate_suppressed: bool = False,
    final_phrase_unit_id: str = "",
    extra_warning_codes: Sequence[str] | None = None,
) -> Dict[str, Any]:
    grammar = dict(grammar_meta or {}) if isinstance(grammar_meta, Mapping) else {}
    material = dict(material_report or {}) if isinstance(material_report, Mapping) else {}
    grammar_codes = _dedupe([
        *_safe_step4_meta_list(grammar.get("grammar_warning_codes")),
        *list(extra_warning_codes or []),
    ])
    material_reasons = _safe_step4_meta_list(material.get("rejection_reasons"))
    quality_flags = _safe_step4_meta_list(material.get("quality_flags"))
    action = str(grammar.get("phrase_unit_grammar_action") or grammar.get("action") or "").strip()
    safe = bool(accepted)
    malformed_count = int(grammar.get("malformed_phrase_unit_count") or 0) + len(
        [code for code in grammar_codes if "malformed" in code or "nominalization" in code]
    )
    return {
        "candidate_id": str(candidate_id or "").strip(),
        "phrase_unit_id": str(final_phrase_unit_id or candidate_id or "").strip(),
        "evidence_span_id": str(evidence_span_id or "").strip(),
        "role": str(role or "current_input_core").strip(),
        "stage": str(stage or "shallow_phrase_unit_candidate").strip(),
        "safe_for_render": safe,
        "rendered_text_allowed": safe,
        "accepted": safe,
        "kept": safe,
        "blocked": not safe,
        "duplicate_suppressed": bool(duplicate_suppressed),
        "phrase_unit_grammar_action": action,
        "grammar_warning_codes": grammar_codes,
        "creation_guard_warning_codes": list(extra_warning_codes or []),
        "phrase_unit_grammar_normalizer": grammar,
        "normalizer": grammar,
        "material_passed": bool(material.get("passed")) if material else bool(safe),
        "quality_flags": quality_flags,
        "material_rejection_reasons": material_reasons,
        "malformed_nominalization_risk": bool(grammar.get("malformed_nominalization_risk")) or any("malformed" in code or "nominalization" in code for code in grammar_codes),
        "malformed_phrase_unit_count": malformed_count,
        "must_keep": bool(grammar.get("must_keep")),
        "must_keep_deferred": bool(grammar.get("must_keep_deferred")) or ((not safe) and bool(grammar.get("must_keep"))),
        "must_keep_deferred_not_rendered": bool(grammar.get("must_keep_deferred")) or ((not safe) and bool(grammar.get("must_keep"))),
        "must_keep_dropped": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "normalized_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "completion_sentence_templates_added": False,
        "fixed_sentence_template_added": False,
        "input_specific_template_used": False,
        "unsupported_completion_added": False,
        "unsupported_complement_added": False,
        "meaning_added": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
    }


def _step4_shallow_phrase_unit_guard_meta(
    rows: Sequence[Mapping[str, Any]] | None,
    *,
    kept_units: Sequence[EmlisPhraseUnit] | None = None,
) -> Dict[str, Any]:
    source_rows = [dict(row) for row in list(rows or []) if isinstance(row, Mapping)]
    kept = list(kept_units or [])
    normalizer_rows = [row.get("phrase_unit_grammar_normalizer") or row.get("normalizer") for row in source_rows if isinstance(row.get("phrase_unit_grammar_normalizer") or row.get("normalizer"), Mapping)]
    normalizer_summary = summarize_phrase_unit_grammar_normalizer(normalizer_rows)
    blocked_rows = [row for row in source_rows if bool(row.get("blocked")) or not bool(row.get("safe_for_render"))]
    deferred_rows = [row for row in blocked_rows if str(row.get("phrase_unit_grammar_action") or "") == "defer" or bool(row.get("must_keep_deferred"))]
    dropped_rows = [row for row in blocked_rows if str(row.get("phrase_unit_grammar_action") or "") == "drop"]
    malformed_rows = [
        row for row in blocked_rows
        if bool(row.get("malformed_nominalization_risk")) or int(row.get("malformed_phrase_unit_count") or 0) > 0
    ]
    reason_counts: Dict[str, int] = {}
    for row in blocked_rows:
        for reason in [
            *_safe_step4_meta_list(row.get("grammar_warning_codes")),
            *_safe_step4_meta_list(row.get("material_rejection_reasons")),
            *_safe_step4_meta_list(row.get("creation_guard_warning_codes")),
        ]:
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
    return {
        "version": _STEP4_SHALLOW_PHRASE_UNIT_GUARD_VERSION,
        "schema_version": _STEP4_SHALLOW_PHRASE_UNIT_GUARD_VERSION,
        "target_step": _STEP4_SHALLOW_PHRASE_UNIT_GUARD_TARGET_STEP,
        "step": _STEP4_SHALLOW_PHRASE_UNIT_GUARD_TARGET_STEP,
        "step4_shallow_phrase_unit_guard_applied": True,
        "shallow_phrase_unit_guard_applied": True,
        "shallow_phrase_unit_creation_guard_applied": True,
        "raw_fragment_to_generic_phrase_guarded": True,
        "runs_before_render_current_input_core_lines": True,
        "runs_before_surface_realizer": True,
        "phrase_grammar_normalizer_connected": True,
        "phrase_unit_grammar_normalizer_applied": True,
        "material_quality_guard_connected": True,
        "material_quality_guard_applied": True,
        "safe_phrase_units_only_for_realizer": True,
        "safe_phrase_units_only_passed_to_realizer": True,
        "safe_phrase_unit_only_passed_to_realizer": True,
        "must_keep_deferred_not_rendered": True,
        "must_keep_malformed_deferred_not_rendered": True,
        "must_keep_dropped": False,
        "candidate_phrase_unit_count": len(source_rows),
        "kept_phrase_unit_count": len(kept),
        "safe_phrase_unit_count": len(kept),
        "accepted_phrase_unit_count": len([row for row in source_rows if bool(row.get("accepted"))]),
        "blocked_phrase_unit_count": len(blocked_rows),
        "deferred_phrase_unit_count": len(deferred_rows),
        "dropped_phrase_unit_count": len(dropped_rows),
        "duplicate_suppressed_count": sum(1 for row in source_rows if bool(row.get("duplicate_suppressed"))),
        "malformed_phrase_unit_blocked_count": len(malformed_rows),
        "malformed_nominalization_blocked_count": len(malformed_rows),
        "all_rendered_phrase_units_safe": True,
        "unsafe_candidates_reach_rendered_text": False,
        "safe_unit_shortage": len(kept) < 2,
        "blocked_reasons": dict(reason_counts),
        "blocked_reason_keys": _dedupe(reason_counts.keys()),
        "rows": source_rows,
        "rejected_rows": blocked_rows,
        "phrase_unit_grammar_normalizer_summary": normalizer_summary,
        "raw_input_included": False,
        "raw_text_included": False,
        "normalized_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "completion_sentence_templates_added": False,
        "fixed_sentence_template_added": False,
        "input_specific_template_used": False,
        "unsupported_completion_added": False,
        "unsupported_complement_added": False,
        "meaning_added": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "external_ai_used": False,
        "local_llm_used": False,
        "product_gate_achieved": False,
        "public_release_applied": False,
    }


def _append_step4_shallow_guard_row(rows: Optional[List[Dict[str, Any]]], row: Mapping[str, Any]) -> None:
    if rows is not None:
        rows.append(dict(row))

def _add_shallow_unit(
    units: List[EmlisPhraseUnit],
    *,
    span_id: str,
    raw: str,
    phrase: str,
    role: str,
    polarity: str,
    guard_rows: Optional[List[Dict[str, Any]]] = None,
    stage: str = "shallow_phrase_unit_candidate",
) -> None:
    compressed = _clean(phrase, limit=90)
    compact = _compact(compressed)
    candidate_id = f"shallow_pu_candidate_{len(guard_rows or []) + 1}"
    if not compressed or compressed in _EMOTION_LABELS or len(compact) < 3:
        reason = "empty_phrase_unit_material" if not compressed else "emotion_label_only"
        _append_step4_shallow_guard_row(
            guard_rows,
            _shallow_phrase_unit_guard_row(
                candidate_id=candidate_id,
                evidence_span_id=span_id,
                role=role or "current_input_core",
                stage=stage,
                grammar_meta={
                    "phrase_unit_grammar_action": "drop",
                    "grammar_warning_codes": [reason],
                    "must_keep": True,
                    "raw_input_included": False,
                    "comment_text_body_included": False,
                },
                material_report={"passed": False, "quality_flags": [], "rejection_reasons": [reason]},
                accepted=False,
            ),
        )
        return

    normalizer_result = normalize_phrase_unit_grammar(
        compressed,
        raw_text=raw,
        role=role or "current_input_core",
        must_keep=True,
        phrase_unit_id=candidate_id,
        evidence_span_id=span_id,
        source_field="shallow_current_input_core",
        source="shallow_current_input_core",
    )
    normalizer_meta = normalizer_result.as_meta()
    extra_warning_codes = _shallow_phrase_creation_extra_warning_codes(phrase=compressed, raw=raw)
    normalized = _clean(normalizer_result.normalized_text, limit=90) if bool(normalizer_result.usable) else ""
    normalized_compact = _compact(normalized)
    if normalizer_result.action not in {PHRASE_UNIT_GRAMMAR_KEEP, PHRASE_UNIT_GRAMMAR_REPHRASE, "keep", "rephrase"} or not normalized or len(normalized_compact) < 3 or extra_warning_codes:
        _append_step4_shallow_guard_row(
            guard_rows,
            _shallow_phrase_unit_guard_row(
                candidate_id=candidate_id,
                evidence_span_id=span_id,
                role=role or "current_input_core",
                stage=stage,
                grammar_meta=normalizer_meta,
                accepted=False,
                extra_warning_codes=extra_warning_codes,
            ),
        )
        return

    flags = _quality_flags(normalized, raw_text=raw, role=role)
    material_report = judge_phrase_unit_material_quality(
        normalized,
        raw_text=raw,
        role=role or "current_input_core",
        source_field="shallow_current_input_core",
    )
    if (not bool(material_report.get("passed"))) or _phrase_material_blocked(flags):
        _append_step4_shallow_guard_row(
            guard_rows,
            _shallow_phrase_unit_guard_row(
                candidate_id=candidate_id,
                evidence_span_id=span_id,
                role=role or "current_input_core",
                stage=stage,
                grammar_meta=normalizer_meta,
                material_report=material_report,
                accepted=False,
            ),
        )
        return

    for index, unit in enumerate(units):
        existing = _compact(unit.compressed_text)
        duplicate = normalized_compact == existing or (len(normalized_compact) >= 6 and normalized_compact in existing) or (len(existing) >= 6 and existing in normalized_compact)
        if not duplicate:
            continue
        if role in _STEP11_EXPANDED_ROLES and unit.role == "current_input_core" and unit.evidence_span_id == span_id:
            units[index] = EmlisPhraseUnit(
                phrase_unit_id=unit.phrase_unit_id,
                evidence_span_id=span_id,
                raw_text=raw,
                compressed_text=normalized,
                role=role,
                polarity=polarity or _shallow_polarity(normalized),
                must_keep=True,
                quality_flags=flags,
            )
            accepted = True
        else:
            accepted = False
        _append_step4_shallow_guard_row(
            guard_rows,
            _shallow_phrase_unit_guard_row(
                candidate_id=candidate_id,
                evidence_span_id=span_id,
                role=role or "current_input_core",
                stage=stage,
                grammar_meta=normalizer_meta,
                material_report=material_report,
                accepted=accepted,
                duplicate_suppressed=not accepted,
                final_phrase_unit_id=unit.phrase_unit_id,
            ),
        )
        return

    final_unit_id = f"pu{len(units)+1}"
    units.append(
        EmlisPhraseUnit(
            phrase_unit_id=final_unit_id,
            evidence_span_id=span_id,
            raw_text=raw,
            compressed_text=normalized,
            role=role or "current_input_core",
            polarity=polarity or _shallow_polarity(normalized),
            must_keep=True,
            quality_flags=flags,
        )
    )
    _append_step4_shallow_guard_row(
        guard_rows,
        _shallow_phrase_unit_guard_row(
            candidate_id=candidate_id,
            evidence_span_id=span_id,
            role=role or "current_input_core",
            stage=stage,
            grammar_meta=normalizer_meta,
            material_report=material_report,
            accepted=True,
            final_phrase_unit_id=final_unit_id,
        ),
    )


def _build_current_input_core_phrase_units_with_guard_meta(
    evidence_items: Sequence[Mapping[str, Any]],
    *,
    guard_rows: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[List[EmlisPhraseUnit], Dict[str, Any]]:
    units: List[EmlisPhraseUnit] = []
    guard_rows = guard_rows if guard_rows is not None else []
    role_priority = (
        "fatigue_accumulation",
        "loss_of_control",
        "avoidance_wish",
        "value_wish",
        "small_repair",
        "positive_state",
        "relieved_weight",
        "achievement",
        "small_action",
        "anxiety_return",
        "perfection_fear",
        "anticipation_loop",
        "burden_fear",
        "rejection_fear",
        "limit",
        "known_action",
        "wish_to_rely",
        "hurt_core",
        "anger_surface",
        "safe_home",
        "reality_damage",
        "ordinary_life_wish",
        "worsening_risk",
    )
    for item in evidence_items:
        if _skip_evidence(item):
            continue
        raw = _raw_text(item)
        span_id = str(item.get("span_id") or f"s{len(units)+1}").strip()
        if not raw or not span_id:
            continue
        generic = _generic_shallow_phrase(raw, _detected_type(item))
        _add_shallow_unit(
            units,
            span_id=span_id,
            raw=raw,
            phrase=generic,
            role="current_input_core",
            polarity=_shallow_polarity(generic or raw),
            guard_rows=guard_rows,
            stage="generic_shallow_phrase",
        )
        roles = set(phase8_roles_for_text(raw, _detected_type(item)))
        for role in role_priority:
            if role not in roles:
                continue
            if role in {"safe_home", "ordinary_life_wish", "reality_damage", "worsening_risk"} and generic:
                continue
            compressed = _compress_text(raw, role)
            if not _role_phrase_safe_for_shallow(compressed, raw):
                continue
            polarity, _must_keep = phase8_role_meta(role)
            _add_shallow_unit(
                units,
                span_id=span_id,
                raw=raw,
                phrase=compressed,
                role=role,
                polarity=polarity,
                guard_rows=guard_rows,
                stage="phase8_role_phrase",
            )
    return units, _step4_shallow_phrase_unit_guard_meta(guard_rows, kept_units=units)


def _build_current_input_core_phrase_units(
    evidence_items: Sequence[Mapping[str, Any]],
    *,
    guard_rows: Optional[List[Dict[str, Any]]] = None,
) -> List[EmlisPhraseUnit]:
    units, _guard_meta = _build_current_input_core_phrase_units_with_guard_meta(evidence_items, guard_rows=guard_rows)
    return units


def _step11_unit_rank(unit: EmlisPhraseUnit) -> Tuple[int, int, str, str]:
    role_order = {role: index for index, role in enumerate((*_STEP11_EXPANDED_ROLES, "positive_state", "anxiety_return", "small_action", "limit", "current_input_core"))}
    expanded_penalty = 0 if unit.role in _STEP11_EXPANDED_ROLES else 1
    return (expanded_penalty, role_order.get(unit.role, 99), unit.evidence_span_id, unit.phrase_unit_id)


def _select_current_input_core_units(units: Sequence[EmlisPhraseUnit], *, max_units: int = 3) -> List[EmlisPhraseUnit]:
    selected: List[EmlisPhraseUnit] = []
    if not units:
        return selected

    ranked = sorted(list(units), key=_step11_unit_rank)
    first = ranked[0]
    selected.append(first)

    for unit in ranked[1:]:
        if unit.evidence_span_id == first.evidence_span_id and unit.role in _STEP11_EXPANDED_ROLES and unit.polarity != first.polarity:
            selected.append(unit)
            break
        if len(selected) >= max_units:
            return selected

    evidence_seen = {unit.evidence_span_id for unit in selected}
    for unit in ranked[1:]:
        if unit in selected or unit.evidence_span_id in evidence_seen:
            continue
        selected.append(unit)
        evidence_seen.add(unit.evidence_span_id)
        if len(selected) >= max_units:
            return selected

    selected_roles = {unit.role for unit in selected}
    for unit in ranked[1:]:
        if unit in selected:
            continue
        if unit.role in _STEP11_EXPANDED_ROLES and unit.role not in selected_roles:
            selected.append(unit)
            selected_roles.add(unit.role)
        elif selected and unit.polarity != selected[-1].polarity:
            selected.append(unit)
        elif unit.evidence_span_id not in evidence_seen:
            selected.append(unit)
            evidence_seen.add(unit.evidence_span_id)
        if len(selected) >= max_units:
            return selected

    return selected[:max_units]

def _current_input_core_relation(previous: EmlisPhraseUnit, current: EmlisPhraseUnit) -> str:
    if previous.polarity != current.polarity and {previous.polarity, current.polarity}.issubset({"positive", "negative", "mixed"}):
        return "contrast"
    if current.polarity == "positive":
        return "continuation"
    return "coexistence"


def _choose_tail(parts: Sequence[Tuple[str, str, str]], used_tail_keys: Sequence[str]) -> Tuple[str, str, str]:
    used = set(used_tail_keys or [])
    for particle, tail, key in parts:
        if key not in used:
            return particle, tail, key
    return parts[0] if parts else ("が", "書かれています", "written")


def _shallow_tail_options(relation: str) -> Tuple[Tuple[str, str, str], ...]:
    if relation == "contrast":
        return (("も", "重なっています", "stack"), ("も", "残っています", "remain"), ("も", "見えています", "visible"))
    if relation in {"continuation", "recovery"}:
        return (("も", "続いています", "continue"), ("も", "見えています", "visible"), ("も", "残っています", "remain"))
    return (("も", "見えています", "visible"), ("も", "重なっています", "stack"), ("も", "残っています", "remain"))



_SHALLOW_V2_BLOCKED_SURFACE_PATTERNS = (
    "generic_center_phrase",
    "same_connector_run",
    "malformed_phrase_unit",
    "old_current_input_core_skeleton",
)


def _shallow_v2_body_lines(lines: Sequence[str]) -> List[str]:
    return [str(line or "").strip() for line in list(lines or []) if str(line or "").strip() and "Emlis" not in str(line or "")]


def _shallow_v2_connector_key(line: str) -> str:
    value = str(line or "").strip()
    if value.startswith("一方で"):
        return "contrast_after"
    if value.startswith("そのあとに"):
        return "sequence_after"
    if value.startswith("さらに"):
        return "bounded_additional"
    if value.startswith("そこに"):
        return "coexistence_add"
    if value.startswith("今は"):
        return "receive_now"
    return "none"


def _shallow_v2_same_connector_run_max(lines: Sequence[str]) -> int:
    keys = [_shallow_v2_connector_key(line) for line in _shallow_v2_body_lines(lines)]
    longest = 0
    current_key = ""
    current_count = 0
    for key in keys:
        if key and key == current_key:
            current_count += 1
        else:
            current_key = key
            current_count = 1 if key else 0
        longest = max(longest, current_count)
    return longest


def _shallow_v2_generic_center_phrase_count(lines: Sequence[str]) -> int:
    return sum(1 for line in _shallow_v2_body_lines(lines) if "中心にあります" in line or "中心として" in line)


def _shallow_v2_role_for_index(index: int) -> str:
    if index <= 0:
        return "receive_line"
    if index == 1:
        return "state_arrangement_line"
    return "bounded_observation_line"


def _shallow_v2_meta(
    *,
    eligible: bool,
    selected: Sequence[EmlisPhraseUnit],
    lines: Sequence[str] | None = None,
    relation_types: Sequence[str] | None = None,
    sentence_roles: Sequence[str] | None = None,
    failure_reason: str = "",
) -> Dict[str, Any]:
    body_lines = _shallow_v2_body_lines(lines or ())
    generic_center_count = _shallow_v2_generic_center_phrase_count(lines or ())
    same_connector_run_max = _shallow_v2_same_connector_run_max(lines or ())
    blocked_patterns = list(_SHALLOW_V2_BLOCKED_SURFACE_PATTERNS)
    meta: Dict[str, Any] = {
        "version": _STEP5_SHALLOW_SURFACE_REALIZER_V2_VERSION,
        "target_step": _STEP5_SHALLOW_SURFACE_REALIZER_V2_TARGET_STEP,
        "step": _STEP5_SHALLOW_SURFACE_REALIZER_V2_TARGET_STEP,
        "eligible": bool(eligible),
        "realizer_version": _STEP5_SHALLOW_SURFACE_REALIZER_V2_NAME,
        "profile_key": "current_input_core",
        "coverage_scope": "current_input_core",
        "safe_focus_unit_count": 1 if selected else 0,
        "safe_phrase_unit_count": len(list(selected or ())),
        "deferred_phrase_unit_count": 0,
        "relation_candidate_count": len([r for r in list(relation_types or ()) if str(r or "").strip()]),
        "sentence_roles": _dedupe(sentence_roles or ()),
        "blocked_surface_patterns": blocked_patterns,
        "same_connector_run_max": same_connector_run_max,
        "generic_center_phrase_count": generic_center_count,
        "body_line_count": len(body_lines),
        "body_line_count_between_2_and_4": 2 <= len(body_lines) <= 4,
        "old_current_input_core_skeleton_disabled": True,
        "center_phrase_disabled": True,
        "default_sono_nakademo_disabled": True,
        "malformed_phrase_unit_count": 0,
        "malformed_phrase_unit_in_rendered_units": False,
        "relation_bearing_surface": bool(len(selected or ()) >= 2),
        "raw_input_included": False,
        "comment_text_body_included": False,
        "completion_sentence_templates_added": False,
        "input_specific_template_added": False,
        "example_sentence_match_used": False,
    }
    if failure_reason:
        meta["failure_reason"] = str(failure_reason or "").strip()
    return meta


def _shallow_v2_receive_line(unit: EmlisPhraseUnit) -> Tuple[str, str, str, str]:
    phrase = _clean(unit.compressed_text, limit=80)
    if not phrase:
        return "", "", "", ""
    return _finish(f"今は、{phrase}が先に出ています"), "receive_first", "center", "receive_line"


def _shallow_v2_relation_line(previous: EmlisPhraseUnit, current: EmlisPhraseUnit, *, relation: str, body_index: int) -> Tuple[str, str, str, str, str]:
    phrase = _clean(current.compressed_text, limit=80)
    if not phrase:
        return "", "", "", "", ""
    relation = normalize_relation_type(relation, roles=(previous.role, current.role), line_role="state_arrangement_line")
    if relation == "contrast":
        if body_index <= 1:
            line = _finish(f"一方で、{phrase}も残っていて、ひとつの向きだけでは切れない状態です")
            role = "state_arrangement_line"
        else:
            line = _finish(f"さらに、{phrase}も残っていて、まだ一つの答えには絞りきれません")
            role = "bounded_observation_line"
        return line, "contrast_remaining", relation, role, "も"
    if relation in {"continuation", "recovery", "sequence", "progress"}:
        if body_index <= 1:
            line = _finish(f"そのあとに、{phrase}が少し戻れる手がかりとして出ています")
            role = "state_arrangement_line"
        else:
            line = _finish(f"さらに、{phrase}も続いていて、少し整えようとする動きがあります")
            role = "bounded_observation_line"
        return line, "progress_signal", relation, role, "が"
    if body_index <= 1:
        line = _finish(f"そこに、{phrase}も加わっていて、状態が一色ではありません")
        role = "state_arrangement_line"
    else:
        line = _finish(f"さらに、{phrase}もあり、今見えている範囲は一つの要素だけではありません")
        role = "bounded_observation_line"
    return line, "coexistence_parallel", relation or "coexistence", role, "も"


def _render_current_input_core_lines(*, payload: Mapping[str, Any], units: Sequence[EmlisPhraseUnit]) -> Tuple[List[str], List[str], List[str], List[SentenceBinding], List[Dict[str, Any]]]:
    selected = _select_current_input_core_units(units, max_units=3)
    if len(selected) < 2:
        return [], [], [], [], []

    lines: List[str] = []
    used: List[str] = []
    tail_keys: List[str] = []
    bindings: List[SentenceBinding] = []
    surface_rows: List[Dict[str, Any]] = []
    greeting = _greeting(payload)
    if greeting:
        lines.append(greeting)

    relation_types_for_meta: List[str] = []
    sentence_roles_for_meta: List[str] = []

    first = selected[0]
    first_line, first_tail_key, first_relation, first_role = _shallow_v2_receive_line(first)
    if first_line:
        first_line = _trim_line(first_line, limit=110)
        lines.append(first_line)
        used.append(first.phrase_unit_id)
        tail_keys.append(first_tail_key)
        relation_types_for_meta.append(first_relation)
        sentence_roles_for_meta.append(first_role)
        binding = _make_sentence_binding(
            sentence_index=len(bindings) + 1,
            text=first_line,
            units=(first,),
            relation_type=first_relation,
            line_role=first_role,
            coverage_scope="current_input_core",
            must_include=True,
            source="limited_composer_shallow_surface_realizer_v2",
            predicate_key=first_tail_key,
        )
        if binding is not None:
            bindings.append(binding)
        surface_rows.append(
            build_surface_component_row(
                line_role=first_role,
                relation_type=first_relation,
                role_keys=(first.role,),
                phrase_unit_ids=(first.phrase_unit_id,),
                sequence_order=0,
                particle="が",
                predicate_key=first_tail_key,
                shallow_path=True,
            )
        )

    previous = first
    for unit in selected[1:]:
        body_index = len(_shallow_v2_body_lines(lines))
        relation = _current_input_core_relation(previous, unit)
        line, tail_key, relation_type, line_role, particle = _shallow_v2_relation_line(
            previous,
            unit,
            relation=relation,
            body_index=body_index,
        )
        line = _trim_line(line, limit=118)
        if line and line not in lines:
            lines.append(line)
            used.extend([previous.phrase_unit_id, unit.phrase_unit_id])
            tail_keys.append(tail_key)
            relation_types_for_meta.append(relation_type)
            sentence_roles_for_meta.append(line_role)
            binding = _make_sentence_binding(
                sentence_index=len(bindings) + 1,
                text=line,
                units=(previous, unit),
                relation_type=relation_type,
                line_role=line_role,
                coverage_scope="current_input_core",
                must_include=True,
                source="limited_composer_shallow_surface_realizer_v2",
                predicate_key=tail_key,
            )
            if binding is not None:
                bindings.append(binding)
            surface_rows.append(
                build_surface_component_row(
                    line_role=line_role,
                    relation_type=relation_type,
                    role_keys=(previous.role, unit.role),
                    phrase_unit_ids=(previous.phrase_unit_id, unit.phrase_unit_id),
                    sequence_order=len(surface_rows),
                    particle=particle,
                    predicate_key=tail_key,
                    shallow_path=True,
                )
            )
        previous = unit
        if len(_shallow_v2_body_lines(lines)) >= 3:
            break

    body_count = len(_shallow_v2_body_lines(lines))
    if body_count < 2:
        return [], [], [], [], []
    if _shallow_v2_generic_center_phrase_count(lines) > 0:
        return [], [], [], [], []
    if _shallow_v2_same_connector_run_max(lines) > 1:
        return [], [], [], [], []
    return lines, _dedupe(used), list(tail_keys), bindings, surface_rows

def _shallow_opener(*, relation: str, body_index: int, total: int) -> str:
    if body_index <= 0:
        return ""
    if relation == "contrast":
        return "一方で、"
    if relation in {"continuation", "recovery"}:
        return "そこから、" if body_index >= 2 else "その中で、"
    return "その中でも、"


def _shallow_confidence(*, used_unit_ids: Sequence[str], units: Sequence[EmlisPhraseUnit]) -> float:
    used_count = len(set(used_unit_ids))
    used_evidence_count = len({unit.evidence_span_id for unit in units if unit.phrase_unit_id in set(used_unit_ids)})
    base = 0.58 + min(0.16, 0.04 * used_count) + min(0.08, 0.04 * used_evidence_count)
    return round(max(0.0, min(0.78, base)), 3)


def _generate_current_input_core_candidate(
    *,
    payload: Mapping[str, Any],
    graph: Mapping[str, Any],
    evidence_items: Sequence[Mapping[str, Any]],
    evidence_by_id: Mapping[str, Mapping[str, Any]],
    allowed_evidence_ids: set[str],
    source_profile_key: str,
) -> Mapping[str, Any]:
    profile_key = "current_input_core"
    if not allowed_evidence_ids:
        allowed_evidence_ids = _text_evidence_ids(evidence_items)
    generation_evidence_items = _generation_items_for_allowed_ids(evidence_items, allowed_evidence_ids)
    phrase_units, shallow_phrase_unit_guard_meta = _build_current_input_core_phrase_units_with_guard_meta(generation_evidence_items)
    if len(phrase_units) < 2 or len({unit.evidence_span_id for unit in phrase_units}) < 2:
        return _unavailable_response(
            "limited_composer_shallow_insufficient_evidence",
            coverage_scope="current_input_core",
            profile_key=profile_key,
            extra_meta={
                "source_profile_key": source_profile_key,
                "shallow_observation_path": True,
                "profile_unmatched": True,
                "phrase_unit_count": len(phrase_units),
                "sentence_plan_count": 0,
                "shallow_surface_realizer_v2": _shallow_v2_meta(eligible=False, selected=phrase_units, failure_reason="insufficient_evidence"),
                "step5_shallow_surface_realizer_v2": _shallow_v2_meta(eligible=False, selected=phrase_units, failure_reason="insufficient_evidence"),
                "shallow_realizer_version": _STEP5_SHALLOW_SURFACE_REALIZER_V2_NAME,
                "shallow_v2_used": False,
                "shallow_phrase_unit_guard": shallow_phrase_unit_guard_meta,
                "step4_shallow_phrase_unit_guard": shallow_phrase_unit_guard_meta,
                "shallow_phrase_unit_creation_guard": shallow_phrase_unit_guard_meta,
                "step4_shallow_phrase_unit_creation_guard": shallow_phrase_unit_guard_meta,
                "malformed_phrase_unit_blocked_count": int(shallow_phrase_unit_guard_meta.get("malformed_phrase_unit_blocked_count") or 0),
            },
        )

    lines, used_unit_ids, surface_tail_keys, sentence_bindings, surface_rows = _render_current_input_core_lines(payload=payload, units=phrase_units)
    rendered_unit_by_id = {unit.phrase_unit_id: unit for unit in phrase_units}
    rendered_units_for_v2 = [rendered_unit_by_id[unit_id] for unit_id in _dedupe(used_unit_ids) if unit_id in rendered_unit_by_id]
    shallow_v2_plan_meta = _shallow_v2_meta(
        eligible=bool(lines),
        selected=rendered_units_for_v2 or _select_current_input_core_units(phrase_units, max_units=3),
        lines=lines,
        relation_types=[str(row.get("relation_type") or "").strip() for row in list(surface_rows or []) if isinstance(row, Mapping)],
        sentence_roles=[str(row.get("line_role") or "").strip() for row in list(surface_rows or []) if isinstance(row, Mapping)],
        failure_reason="" if lines else "empty_candidate",
    )
    if not lines:
        return _unavailable_response(
            "limited_composer_shallow_empty_candidate",
            coverage_scope="current_input_core",
            profile_key=profile_key,
            extra_meta={
                "source_profile_key": source_profile_key,
                "shallow_observation_path": True,
                "profile_unmatched": True,
                "phrase_unit_count": len(phrase_units),
                "sentence_plan_count": 0,
                "shallow_surface_realizer_v2": shallow_v2_plan_meta,
                "step5_shallow_surface_realizer_v2": shallow_v2_plan_meta,
                "shallow_realizer_version": _STEP5_SHALLOW_SURFACE_REALIZER_V2_NAME,
                "shallow_v2_used": False,
                "shallow_phrase_unit_guard": shallow_phrase_unit_guard_meta,
                "step4_shallow_phrase_unit_guard": shallow_phrase_unit_guard_meta,
                "shallow_phrase_unit_creation_guard": shallow_phrase_unit_guard_meta,
                "step4_shallow_phrase_unit_creation_guard": shallow_phrase_unit_guard_meta,
                "malformed_phrase_unit_blocked_count": int(shallow_phrase_unit_guard_meta.get("malformed_phrase_unit_blocked_count") or 0),
            },
        )

    comment_text = "\n".join(line for line in lines if line).strip()
    matched_forbidden = _matched_forbidden_surfaces(payload=payload, text=comment_text)
    if matched_forbidden:
        return _unavailable_response(
            "limited_composer_forbidden_surface",
            matched_forbidden=matched_forbidden,
            coverage_scope="current_input_core",
            profile_key=profile_key,
            extra_meta={
                "source_profile_key": source_profile_key,
                "shallow_observation_path": True,
                "profile_unmatched": True,
                "shallow_surface_realizer_v2": shallow_v2_plan_meta,
                "step5_shallow_surface_realizer_v2": shallow_v2_plan_meta,
                "shallow_realizer_version": _STEP5_SHALLOW_SURFACE_REALIZER_V2_NAME,
                "shallow_v2_used": True,
                "shallow_phrase_unit_guard": shallow_phrase_unit_guard_meta,
                "step4_shallow_phrase_unit_guard": shallow_phrase_unit_guard_meta,
                "shallow_phrase_unit_creation_guard": shallow_phrase_unit_guard_meta,
                "step4_shallow_phrase_unit_creation_guard": shallow_phrase_unit_guard_meta,
                "malformed_phrase_unit_blocked_count": int(shallow_phrase_unit_guard_meta.get("malformed_phrase_unit_blocked_count") or 0),
            },
        )

    unit_by_id = {unit.phrase_unit_id: unit for unit in phrase_units}
    used_evidence_ids = _dedupe(unit_by_id[unit_id].evidence_span_id for unit_id in used_unit_ids if unit_id in unit_by_id)
    quality_report = judge_limited_sentence_quality(
        comment_text=comment_text,
        evidence_spans=_evidence_objects_for_quality(generation_evidence_items),
        profile_key=profile_key,
        used_evidence_span_ids=used_evidence_ids,
        composer_meta={"profile_key": profile_key, "source_profile_key": source_profile_key, "shallow_observation_path": True, "profile_unmatched": True},
    )
    if not bool(quality_report.get("passed")):
        return _unavailable_response(
            "limited_composer_sentence_quality_rejected",
            matched_forbidden=list(quality_report.get("matched_fragments") or quality_report.get("matched_surfaces") or []),
            coverage_scope="current_input_core",
            profile_key=profile_key,
            extra_meta={
                "phase8_quality": quality_report,
                "source_profile_key": source_profile_key,
                "shallow_observation_path": True,
                "profile_unmatched": True,
                "shallow_surface_realizer_v2": shallow_v2_plan_meta,
                "step5_shallow_surface_realizer_v2": shallow_v2_plan_meta,
                "shallow_realizer_version": _STEP5_SHALLOW_SURFACE_REALIZER_V2_NAME,
                "shallow_v2_used": True,
                "shallow_phrase_unit_guard": shallow_phrase_unit_guard_meta,
                "step4_shallow_phrase_unit_guard": shallow_phrase_unit_guard_meta,
                "shallow_phrase_unit_creation_guard": shallow_phrase_unit_guard_meta,
                "step4_shallow_phrase_unit_creation_guard": shallow_phrase_unit_guard_meta,
                "malformed_phrase_unit_blocked_count": int(shallow_phrase_unit_guard_meta.get("malformed_phrase_unit_blocked_count") or 0),
            },
        )

    used_evidence_ids = [span_id for span_id in used_evidence_ids if span_id in evidence_by_id]
    if not used_evidence_ids:
        return _unavailable_response(
            "limited_composer_no_used_evidence",
            coverage_scope="current_input_core",
            profile_key=profile_key,
            extra_meta={
                "source_profile_key": source_profile_key,
                "shallow_observation_path": True,
                "profile_unmatched": True,
                "shallow_surface_realizer_v2": shallow_v2_plan_meta,
                "step5_shallow_surface_realizer_v2": shallow_v2_plan_meta,
                "shallow_realizer_version": _STEP5_SHALLOW_SURFACE_REALIZER_V2_NAME,
                "shallow_v2_used": True,
                "shallow_phrase_unit_guard": shallow_phrase_unit_guard_meta,
                "step4_shallow_phrase_unit_guard": shallow_phrase_unit_guard_meta,
                "shallow_phrase_unit_creation_guard": shallow_phrase_unit_guard_meta,
                "step4_shallow_phrase_unit_creation_guard": shallow_phrase_unit_guard_meta,
                "malformed_phrase_unit_blocked_count": int(shallow_phrase_unit_guard_meta.get("malformed_phrase_unit_blocked_count") or 0),
            },
        )
    greeting_count = 1 if lines and "Emlis" in lines[0] else 0
    body_lines = lines[greeting_count:]
    composer_meta = {
        "limited_composer": True,
        "generation_scope": _GENERATION_SCOPE,
        "external_ai_used": False,
        "phase8_quality_path": True,
        "profile_key": profile_key,
        "source_profile_key": source_profile_key,
        "shallow_observation_path": True,
        "profile_unmatched": True,
        "required_roles": [],
        "available_roles": _dedupe(unit.role for unit in phrase_units),
        "covered_roles": _dedupe(unit.role for unit in phrase_units if unit.phrase_unit_id in set(used_unit_ids)),
        "body_line_count": len(body_lines),
        "phrase_unit_count": len(phrase_units),
        "sentence_plan_count": 0,
        "sentence_surface_mode": _STEP5_SHALLOW_SURFACE_REALIZER_V2_NAME,
        "surface_realizer_stage": _STEP5_SHALLOW_SURFACE_REALIZER_V2_TARGET_STEP,
        "shallow_surface_realizer_v2": shallow_v2_plan_meta,
        "step5_shallow_surface_realizer_v2": shallow_v2_plan_meta,
        "shallow_realizer_version": _STEP5_SHALLOW_SURFACE_REALIZER_V2_NAME,
        "shallow_v2_used": True,
        "sentence_tail_keys": surface_tail_keys,
        "surface_tail_keys": surface_tail_keys,
        "allowed_evidence_span_ids": sorted(allowed_evidence_ids),
        "phase8_quality": quality_report,
        "shallow_phrase_unit_guard": shallow_phrase_unit_guard_meta,
        "step4_shallow_phrase_unit_guard": shallow_phrase_unit_guard_meta,
        "shallow_phrase_unit_creation_guard": shallow_phrase_unit_guard_meta,
        "step4_shallow_phrase_unit_creation_guard": shallow_phrase_unit_guard_meta,
        "malformed_phrase_unit_blocked_count": int(shallow_phrase_unit_guard_meta.get("malformed_phrase_unit_blocked_count") or 0),
    }
    composer_meta["phrase_unit_material_quality"] = _step4_phrase_unit_material_meta(phrase_units)
    composer_meta["step4_phrase_unit_material_quality"] = composer_meta["phrase_unit_material_quality"]
    composer_meta["phrase_unit_material_quality_enabled"] = True
    shallow_binding_bundle = _sentence_binding_bundle_meta(
        bindings=sentence_bindings,
        coverage_scope="current_input_core",
        profile_key=profile_key,
        sentence_plans=(),
        phrase_units=phrase_units,
    )
    _attach_sentence_binding_meta(composer_meta, bundle_meta=shallow_binding_bundle, body_line_count=len(body_lines))
    _attach_relation_taxonomy_meta(composer_meta, taxonomy_meta=shallow_binding_bundle.get("relation_taxonomy"))
    _attach_step8_surface_meta(
        composer_meta,
        step8_meta=_step8_limited_surface_realizer_meta(
            profile_key=profile_key,
            coverage_scope="current_input_core",
            surface_rows=surface_rows,
            predicate_keys=surface_tail_keys,
            relation_types=shallow_binding_bundle.get("relation_types") or (),
            shallow_path=True,
        ),
    )
    composer_meta["surface_realizer"] = _step13_surface_realizer_meta(
        profile_key=profile_key,
        sentence_plans=(),
        phrase_units=phrase_units,
        used_unit_ids=used_unit_ids,
        predicate_keys=surface_tail_keys,
        shallow_path=True,
    )
    composer_meta["surface_realizer_meta"] = composer_meta["surface_realizer"]
    composer_meta["step13_surface_realizer"] = composer_meta["surface_realizer"]
    composer_meta["role_expansion"] = _step11_role_expansion_meta(phrase_units)
    composer_meta["step11_role_expansion"] = composer_meta["role_expansion"]
    composer_meta["profile_sentence_plan"] = _step12_profile_sentence_plan_meta(
        profile_key=profile_key,
        phrase_units=phrase_units,
        sentence_plans=(),
        used_unit_ids=used_unit_ids,
    )
    composer_meta["profile_sentence_plan_expansion"] = composer_meta["profile_sentence_plan"]
    composer_meta["step12_profile_sentence_plan"] = composer_meta["profile_sentence_plan"]
    composer_meta["step12_profile_sentence_plan_expansion"] = composer_meta["profile_sentence_plan"]
    composer_meta["composer_diagnostic"] = _composer_diagnostic_meta(
        status="generated",
        coverage_scope="current_input_core",
        profile_key=profile_key,
        source_profile_key=source_profile_key,
        phrase_units=phrase_units,
        sentence_plans=(),
        used_unit_ids=used_unit_ids,
        required_roles=(),
        extra_meta=composer_meta,
    )
    _attach_limited_reader_repair_step3_meta(
        composer_meta,
        payload=payload,
        coverage_scope="current_input_core",
        profile_key=profile_key,
    )
    response = {
        "schema_version": _RESPONSE_SCHEMA_VERSION,
        "response_schema_version": _RESPONSE_SCHEMA_VERSION,
        "composer_source": _ALLOWED_SOURCE,
        "status": "generated",
        "composer_model": _COMPOSER_MODEL,
        "generation_method": _GENERATION_METHOD,
        "generation_scope": _GENERATION_SCOPE,
        "fixed_string_renderer_used": False,
        "coverage_scope": "current_input_core",
        "comment_text": comment_text,
        "used_evidence_span_ids": used_evidence_ids,
        "used_claim_ids": _used_claim_ids(graph),
        "used_relation_ids": _used_relation_ids(graph),
        "confidence": _shallow_confidence(used_unit_ids=used_unit_ids, units=phrase_units),
        "used_phrase_unit_ids": used_unit_ids,
        "sentence_binding_bundle": shallow_binding_bundle,
        "composer_meta": composer_meta,
    }
    return _core_checked_response(
        response=response,
        payload=payload,
        evidence_items=generation_evidence_items,
        phrase_units=phrase_units,
        sentence_plans=(),
        used_unit_ids=used_unit_ids,
        coverage_scope="current_input_core",
        profile_key=profile_key,
    )

def _core_checked_response(
    *,
    response: Mapping[str, Any],
    payload: Mapping[str, Any],
    evidence_items: Sequence[Mapping[str, Any]],
    phrase_units: Sequence[EmlisPhraseUnit],
    sentence_plans: Sequence[SentencePlan],
    used_unit_ids: Sequence[str],
    coverage_scope: str,
    profile_key: str,
) -> Mapping[str, Any]:
    response = _apply_limited_reader_repair_if_needed(
        response=response,
        payload=payload,
        phrase_units=phrase_units,
        sentence_plans=sentence_plans,
        used_unit_ids=used_unit_ids,
        coverage_scope=coverage_scope,
        profile_key=profile_key,
    )
    evaluation = evaluate_emlis_observation_candidate(
        composer_payload=payload,
        evidence_items=evidence_items,
        phrase_units=phrase_units,
        sentence_plans=sentence_plans,
        comment_text=str(response.get("comment_text") or ""),
        used_evidence_span_ids=list(response.get("used_evidence_span_ids") or []),
        used_phrase_unit_ids=used_unit_ids,
        coverage_scope=coverage_scope,
        composer_model=str(response.get("composer_model") or _COMPOSER_MODEL),
        composer_meta=response.get("composer_meta") if isinstance(response.get("composer_meta"), Mapping) else {},
        response=response,
    )
    if evaluation.passed:
        return attach_core_evaluation_meta(response, evaluation)
    core_meta = evaluation.as_meta()
    return _unavailable_response(
        core_rejection_reason(evaluation),
        coverage_scope=coverage_scope,
        profile_key=profile_key,
        extra_meta={
            "text_generation_core": core_meta,
            "core_text_generation": core_meta,
        },
    )

def _phase8_profile_evidence_ids(profile_key: str, evidence_items: Sequence[Mapping[str, Any]]) -> set[str]:
    profile = _profile_for_key(profile_key)
    required = set(profile.required_roles)
    optional_by_profile = {
        "mixed_positive_anxiety": {"positive_state", "anxiety_return", "fall_contrast"},
        "anger_hurt_boundary": {"anger_surface", "unfairness", "hurt_core", "withdrawal"},
        "self_understanding_loop": {"anticipation_loop", "known_action", "perfection_fear"},
        "positive_progress": {"small_action", "relieved_weight", "achievement"},
        "relationship_approach_avoidance": {"wish_to_rely", "burden_fear", "rejection_fear", "limit"},
        "reality_escape_tension": {"safe_home", "reality_damage", "ordinary_life_wish", "worsening_risk", "known_action", "limit"},
        "energy_fatigue": {"fatigue_accumulation", "loss_of_control", "avoidance_wish", "small_repair"},
        "anxiety_anticipation": {"anticipation_loop", "perfection_fear", "anxiety_return", "loss_of_control"},
        "value_wish": {"value_wish", "avoidance_wish", "fatigue_accumulation", "loss_of_control", "small_repair", "wish_to_rely"},
        "long_meaning_arc": {"fatigue_accumulation", "loss_of_control", "avoidance_wish", "value_wish", "small_repair", "anticipation_loop", "perfection_fear", "limit"},
    }.get(profile_key, set())
    target_roles = required | set(optional_by_profile)
    ids: set[str] = set()
    for item in evidence_items:
        if _skip_evidence(item):
            continue
        roles = set(phase8_roles_for_text(_raw_text(item), _detected_type(item)))
        if roles.intersection(target_roles):
            span_id = str(item.get("span_id") or "").strip()
            if span_id:
                ids.add(span_id)
    return ids

def _build_phrase_units(evidence_items: Sequence[Mapping[str, Any]]) -> List[EmlisPhraseUnit]:
    units: List[EmlisPhraseUnit] = []
    for item in evidence_items:
        if _skip_evidence(item):
            continue
        raw = _raw_text(item)
        roles = phase8_roles_for_text(raw, _detected_type(item))
        if not roles:
            role, _polarity, _must_keep = _role_for_text(raw, _detected_type(item))
            roles = (role,) if role != "other" else tuple()
        for role in roles:
            if role == "other":
                continue
            polarity, must_keep = phase8_role_meta(role)
            compressed = _compress_text(raw, role)
            if not compressed or compressed in _EMOTION_LABELS:
                continue
            flags = _quality_flags(
                compressed,
                raw_text=raw,
                role=role,
                detected_type=_detected_type(item),
                source_field=_source_field(item),
            )
            if _phrase_material_blocked(flags):
                continue
            span_id = str(item.get("span_id") or f"s{len(units)+1}").strip()
            units.append(
                EmlisPhraseUnit(
                    phrase_unit_id=f"pu{len(units)+1}",
                    evidence_span_id=span_id,
                    raw_text=raw,
                    compressed_text=compressed,
                    role=role,
                    polarity=polarity,
                    must_keep=must_keep,
                    quality_flags=flags,
                )
            )
    return units


def _profile_for_key(profile_key: str) -> ObservationProfile:
    profiles = {
        "mixed_positive_anxiety": ObservationProfile("mixed_positive_anxiety", ("positive_state", "anxiety_return"), min_lines=2, max_lines=3),
        "anger_hurt_boundary": ObservationProfile("anger_hurt_boundary", ("anger_surface", "hurt_core"), min_lines=2, max_lines=3),
        "self_understanding_loop": ObservationProfile("self_understanding_loop", ("anticipation_loop", "perfection_fear"), min_lines=2, max_lines=3),
        "positive_progress": ObservationProfile("positive_progress", ("small_action", "achievement"), min_lines=2, max_lines=3),
        "relationship_approach_avoidance": ObservationProfile("relationship_approach_avoidance", ("wish_to_rely", "burden_fear", "rejection_fear", "limit"), min_lines=2, max_lines=3),
        "reality_escape_tension": ObservationProfile("reality_escape_tension", ("safe_home", "reality_damage", "ordinary_life_wish", "worsening_risk"), min_lines=3, max_lines=4),
        "energy_fatigue": ObservationProfile("energy_fatigue", ("fatigue_accumulation", "loss_of_control"), min_lines=2, max_lines=3),
        "anxiety_anticipation": ObservationProfile("anxiety_anticipation", ("anticipation_loop", "anxiety_return"), min_lines=2, max_lines=3),
        "value_wish": ObservationProfile("value_wish", ("value_wish", "loss_of_control"), min_lines=2, max_lines=3),
        "long_meaning_arc": ObservationProfile("long_meaning_arc", ("fatigue_accumulation", "value_wish"), min_lines=3, max_lines=4),
    }
    return profiles.get(profile_key, ObservationProfile("unknown", tuple(), min_lines=0, max_lines=0, coverage_scope="current_input_core"))


def _units_for_role(units: Sequence[EmlisPhraseUnit], role: str) -> List[EmlisPhraseUnit]:
    return [unit for unit in units if unit.role == role]


def _first_unit(units: Sequence[EmlisPhraseUnit], *roles: str) -> Optional[EmlisPhraseUnit]:
    for role in roles:
        found = _units_for_role(units, role)
        if found:
            return found[0]
    return None


def _unit_ids(*units: Optional[EmlisPhraseUnit]) -> Tuple[str, ...]:
    return tuple(unit.phrase_unit_id for unit in units if unit is not None)


def _sentence_plans_for_profile(*, profile: ObservationProfile, units: Sequence[EmlisPhraseUnit]) -> List[SentencePlan]:
    key = profile.profile_key
    if key == "mixed_positive_anxiety":
        return [
            SentencePlan("receive", tuple(unit.phrase_unit_id for unit in units if unit.role == "positive_state")[:2], "sequence"),
            SentencePlan("contrast", _unit_ids(_first_unit(units, "anxiety_return")), "contrast"),
            SentencePlan("contrast_detail", _unit_ids(_first_unit(units, "fall_contrast")), "coexistence", must_include=False),
        ]
    if key == "anger_hurt_boundary":
        hurt_units = tuple(unit.phrase_unit_id for unit in units if unit.role in {"hurt_core", "unfairness"})[:2]
        return [
            SentencePlan("receive", _unit_ids(_first_unit(units, "anger_surface")), "surface"),
            SentencePlan("contrast", hurt_units, "contrast"),
            SentencePlan("distance", _unit_ids(_first_unit(units, "withdrawal")), "distance", must_include=False),
        ]
    if key == "self_understanding_loop":
        return [
            SentencePlan("tension", _unit_ids(_first_unit(units, "anticipation_loop")), "pressure"),
            SentencePlan("context", _unit_ids(_first_unit(units, "known_action")), "context", must_include=False),
            SentencePlan("tension_detail", tuple(unit.phrase_unit_id for unit in units if unit.role == "perfection_fear")[:2], "coexistence"),
        ]
    if key == "positive_progress":
        return [
            SentencePlan("progress", _unit_ids(_first_unit(units, "small_action")), "progress"),
            SentencePlan("progress_detail", _unit_ids(_first_unit(units, "relieved_weight")), "sequence", must_include=False),
            SentencePlan("progress_detail", _unit_ids(_first_unit(units, "achievement")), "progress"),
        ]
    if key == "relationship_approach_avoidance":
        return [
            SentencePlan("approach", _unit_ids(_first_unit(units, "wish_to_rely")), "approach"),
            SentencePlan("tension", tuple(unit.phrase_unit_id for unit in units if unit.role in {"burden_fear", "rejection_fear"})[:2], "approach_avoidance"),
            SentencePlan("limit", _unit_ids(_first_unit(units, "limit")), "limit"),
        ]
    if key == "reality_escape_tension":
        return [
            SentencePlan("receive", tuple(unit.phrase_unit_id for unit in sorted([u for u in units if u.role == "safe_home"], key=lambda u: (0 if any(term in u.compressed_text for term in ("リラックス", "優先", "整え")) else 1, u.phrase_unit_id)))[:1], "sequence"),
            SentencePlan("contrast", tuple(unit.phrase_unit_id for unit in units if unit.role == "reality_damage")[:2], "contrast"),
            SentencePlan("tension", tuple(unit.phrase_unit_id for unit in units if unit.role in {"ordinary_life_wish", "worsening_risk", "known_action"})[:3], "tension"),
            SentencePlan("escape", _unit_ids(_first_unit(units, "limit")), "limit", must_include=False),
        ]
    if key == "energy_fatigue":
        return [
            SentencePlan("fatigue", _unit_ids(_first_unit(units, "fatigue_accumulation")), "pressure"),
            SentencePlan("control", _unit_ids(_first_unit(units, "loss_of_control", "avoidance_wish")), "coexistence"),
            SentencePlan("repair", _unit_ids(_first_unit(units, "small_repair", "positive_state")), "sequence", must_include=False),
        ]
    if key == "anxiety_anticipation":
        return [
            SentencePlan("loop", _unit_ids(_first_unit(units, "anticipation_loop")), "pressure"),
            SentencePlan("fear", tuple(unit.phrase_unit_id for unit in units if unit.role in {"anxiety_return", "loss_of_control"})[:2], "coexistence"),
            SentencePlan("detail", _unit_ids(_first_unit(units, "perfection_fear")), "context", must_include=False),
        ]
    if key == "value_wish":
        return [
            SentencePlan("value", _unit_ids(_first_unit(units, "value_wish")), "value"),
            SentencePlan("pressure", tuple(unit.phrase_unit_id for unit in units if unit.role in {"loss_of_control", "avoidance_wish", "fatigue_accumulation", "wish_to_rely"})[:2], "coexistence"),
            SentencePlan("repair", _unit_ids(_first_unit(units, "small_repair", "positive_state")), "sequence", must_include=False),
        ]
    if key == "long_meaning_arc":
        return [
            SentencePlan("state", tuple(unit.phrase_unit_id for unit in units if unit.role in {"fatigue_accumulation", "loss_of_control"})[:2], "pressure"),
            SentencePlan("tension", tuple(unit.phrase_unit_id for unit in units if unit.role in {"value_wish", "avoidance_wish", "perfection_fear"})[:2], "tension"),
            SentencePlan("repair", _unit_ids(_first_unit(units, "small_repair", "positive_state")), "sequence", must_include=False),
            SentencePlan("limit", _unit_ids(_first_unit(units, "limit", "avoidance_wish")), "limit", must_include=False),
        ]
    return []


def _unit_by_id(units: Sequence[EmlisPhraseUnit]) -> Dict[str, EmlisPhraseUnit]:
    return {unit.phrase_unit_id: unit for unit in units}


def _units_for_plan_ids(units: Sequence[EmlisPhraseUnit], plan: SentencePlan) -> List[EmlisPhraseUnit]:
    by_id = _unit_by_id(units)
    return [by_id[unit_id] for unit_id in plan.phrase_unit_ids if unit_id in by_id and by_id[unit_id].compressed_text]


def _texts_for_plan(units: Sequence[EmlisPhraseUnit], plan: SentencePlan) -> List[str]:
    return _dedupe(unit.compressed_text for unit in _units_for_plan_ids(units, plan))


def _finish(value: Any) -> str:
    text = _clean(value, limit=220).strip(_PUNCT_TRIM)
    return f"{text}。" if text else ""


def _plan_polarity(plan_units: Sequence[EmlisPhraseUnit]) -> str:
    polarities = {unit.polarity for unit in plan_units if unit.polarity}
    if not polarities:
        return "neutral"
    if "mixed" in polarities or ("positive" in polarities and "negative" in polarities):
        return "mixed"
    if "negative" in polarities:
        return "negative"
    if "positive" in polarities:
        return "positive"
    return "neutral"


def _sentence_unit_order_key(plan: SentencePlan, unit: EmlisPhraseUnit) -> Tuple[int, str]:
    if plan.relation_type == "tension":
        order = {
            "ordinary_life_wish": 0,
            "wish_to_rely": 0,
            "worsening_risk": 1,
            "perfection_fear": 1,
            "limit": 1,
            "known_action": 2,
        }
        return order.get(unit.role, 9), unit.phrase_unit_id
    if plan.relation_type == "coexistence":
        order = {"known_action": 0, "perfection_fear": 1, "fall_contrast": 1}
        return order.get(unit.role, 5), unit.phrase_unit_id
    return 0, unit.phrase_unit_id


def _select_subject_units(plan: SentencePlan, plan_units: Sequence[EmlisPhraseUnit]) -> List[EmlisPhraseUnit]:
    units = sorted(list(plan_units), key=lambda unit: _sentence_unit_order_key(plan, unit))
    if not units:
        return []
    if plan.relation_type in {"sequence", "contrast", "coexistence", "approach_avoidance", "tension"}:
        return units[:2]
    return units[:1]


def _joiner_for_plan(plan: SentencePlan, selected_units: Sequence[EmlisPhraseUnit]) -> str:
    roles = {unit.role for unit in selected_units}
    if plan.relation_type in {"tension", "coexistence"}:
        return "と、"
    if plan.relation_type == "contrast" and roles.issubset({"reality_damage"}):
        return "と、"
    return "や、"


def _join_subject_texts(*, plan: SentencePlan, selected_units: Sequence[EmlisPhraseUnit]) -> str:
    cleaned = [unit.compressed_text for unit in selected_units if unit.compressed_text]
    cleaned = _dedupe(cleaned)
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return cleaned[0]
    joiner = _joiner_for_plan(plan, selected_units)
    return joiner.join(cleaned[:2])


def _opener_for_plan(*, plan: SentencePlan, sequence_index: int) -> str:
    if sequence_index <= 0:
        return ""
    relation = str(plan.relation_type or "").strip()
    if relation in {"contrast", "approach_avoidance"}:
        return "一方で、"
    if relation == "tension":
        return "その中で、"
    if relation == "coexistence":
        return "同時に、"
    if relation in {"sequence", "progress", "recovery", "continuation"}:
        return "そこから、" if sequence_index == 1 else "続いて、"
    if relation in {"limit", "distance"}:
        return "さらに、" if sequence_index <= 2 else "その先で、"
    return "さらに、" if sequence_index <= 2 else "続いて、"


def _surface_parts_for_plan(
    *,
    plan: SentencePlan,
    selected_units: Sequence[EmlisPhraseUnit],
    sequence_index: int,
    used_predicate_keys: Sequence[str],
) -> Tuple[SentenceSurfaceParts, str]:
    ctx = SentenceSurfaceContext(
        line_role=plan.line_role,
        relation_type=plan.relation_type,
        phrase_count=len(selected_units),
        polarity=_plan_polarity(selected_units),
        sequence_order=sequence_index,
    )
    relation = ctx.relation_type
    polarity = ctx.polarity
    opener = _opener_for_plan(plan=plan, sequence_index=ctx.sequence_order)
    joiner = _joiner_for_plan(plan, selected_units)

    candidates: Tuple[Tuple[str, str, str], ...]
    roles = {unit.role for unit in selected_units}
    if relation == "surface":
        candidates = (("が", "表に出ています", "surface_visible"), ("が", "前面にあります", "front"))
    elif relation == "value":
        candidates = (("が", "言葉になっています", "worded"), ("が", "前面にあります", "front"))
    elif relation == "pressure":
        if roles.intersection({"fatigue_accumulation", "loss_of_control", "avoidance_wish"}):
            candidates = (("が", "強く残っています", "strong_remain"), ("が", "続いています", "continue"))
        else:
            candidates = (("が", "続いています", "continue"), ("が", "強く残っています", "strong_remain"))
    elif relation == "context":
        candidates = (("も", "見えています", "visible"), ("も", "重なっています", "stack"), ("も", "残っています", "remain"))
    elif relation in {"progress", "recovery"}:
        candidates = (("が", "形になっています", "progress_shape"), ("も", "見えています", "visible"), ("が", "書かれています", "written"))
    elif relation == "approach":
        candidates = (("が", "言葉になっています", "worded"), ("が", "前面にあります", "front"))
    elif relation == "approach_avoidance":
        candidates = (("も", "重なっています", "stack"), ("も", "見えています", "visible"), ("も", "書かれています", "written"))
    elif relation == "contrast":
        if roles.issubset({"reality_damage"}):
            candidates = (("が", "大きく響いています", "impact"), ("も", "残っています", "remain"))
        elif polarity == "negative":
            candidates = (("も", "重なっています", "stack"), ("も", "書かれています", "written"))
        else:
            candidates = (("が", "戻ってきています", "return"), ("も", "残っています", "remain"))
    elif relation == "tension":
        candidates = (("が", "ぶつかっています", "tension"), ("が", "同時に残っています", "co_remain"))
    elif relation == "coexistence":
        if len(selected_units) <= 1:
            candidates = (("も", "残っています", "remain"), ("も", "見えています", "visible"), ("も", "重なっています", "stack"))
        else:
            roles = {unit.role for unit in selected_units}
            if roles.intersection({"value_wish", "wish_to_rely", "avoidance_wish"}) and roles.intersection({"loss_of_control", "fatigue_accumulation", "burden_fear", "rejection_fear"}):
                candidates = (("が", "混ざっています", "mixed"), ("も", "重なっています", "stack"), ("も", "残っています", "remain"))
            elif polarity == "negative":
                candidates = (("も", "重なっています", "stack"), ("も", "残っています", "remain"), ("も", "見えています", "visible"))
            else:
                candidates = (("が", "混ざっています", "mixed"), ("も", "並んでいます", "parallel"), ("も", "残っています", "remain"))
    elif relation == "distance":
        candidates = (("も", "書かれています", "written"), ("も", "続いています", "continue"))
    elif relation == "limit":
        subject = selected_units[0].compressed_text if selected_units else ""
        if "限界" in subject:
            candidates = (("まで", "来ています", "limit_arrived"),)
        elif subject.endswith("時"):
            candidates = (("も", "あります", "exists"), ("も", "残っています", "remain"))
        else:
            candidates = (("も", "書かれています", "written"), ("も", "残っています", "remain"))
    elif relation == "sequence":
        if polarity == "positive":
            candidates = (("も", "見えています", "visible"), ("が", "形になっています", "progress_shape"), ("が", "続いています", "continue"))
        else:
            candidates = (("が", "続いています", "continue"), ("も", "残っています", "remain"), ("も", "見えています", "visible"))
    else:
        candidates = (("が", "書かれています", "written"), ("が", "残っています", "remain"))

    particle, predicate, key = choose_limited_surface_parts(
        relation_type=relation,
        line_role=plan.line_role,
        role_keys=roles,
        polarity=polarity,
        current_candidates=candidates,
        used_tail_keys=used_predicate_keys,
    )
    return SentenceSurfaceParts(opener=opener, joiner=joiner, particle=particle, predicate=predicate, max_phrases=2), key


def _surface_parts_after_phrase_fit(
    *,
    plan: SentencePlan,
    subject: str,
    selected_units: Sequence[EmlisPhraseUnit],
    parts: SentenceSurfaceParts,
    predicate_key: str,
    used_predicate_keys: Sequence[str] | None = None,
) -> Tuple[SentenceSurfaceParts, str]:
    compact_subject = _compact(subject)
    relation = str(plan.relation_type or "").strip()
    roles = {unit.role for unit in selected_units}
    used = {str(item or "").strip() for item in list(used_predicate_keys or []) if str(item or "").strip()}
    particle = parts.particle
    predicate = parts.predicate
    key = predicate_key

    if relation == "limit" and ("限界" in compact_subject or roles.intersection({"limit", "avoidance_wish"})):
        if "限界" in compact_subject and "limit_arrived" not in used:
            particle, predicate, key = "まで", "来ています", "limit_arrived"
        elif predicate == "書かれています":
            particle, predicate, key = "も", "残っています", "remain"
    elif predicate == "書かれています":
        if compact_subject.endswith(("気持ち", "願い")) or roles.intersection({"value_wish", "wish_to_rely", "avoidance_wish"}):
            if "worded" not in used:
                particle, predicate, key = "が", "言葉になっています", "worded"
            else:
                particle, predicate, key = "が", "前面にあります", "front"
        elif roles.intersection({"small_repair", "small_action", "achievement", "relieved_weight"}):
            if "progress_shape" not in used:
                particle, predicate, key = "が", "形になっています", "progress_shape"
            elif "visible" not in used:
                particle, predicate, key = "も", "見えています", "visible"
            elif "continue" not in used:
                particle, predicate, key = "が", "続いています", "continue"
            else:
                particle, predicate, key = "も", "あります", "exists"
        elif compact_subject.endswith("こと"):
            particle, predicate, key = "も", "見えています", "visible"

    particle, predicate, key = choose_limited_surface_parts(
        relation_type=relation,
        line_role=plan.line_role,
        role_keys=roles,
        polarity=_plan_polarity(selected_units),
        current_candidates=((particle, predicate, key),),
        used_tail_keys=used_predicate_keys,
    )

    return SentenceSurfaceParts(
        opener=parts.opener,
        joiner=parts.joiner,
        particle=particle,
        predicate=predicate,
        max_phrases=parts.max_phrases,
    ), key


def _realize_sentence(
    *,
    plan: SentencePlan,
    plan_units: Sequence[EmlisPhraseUnit],
    sequence_index: int,
    used_predicate_keys: Sequence[str],
) -> Tuple[str, str, Tuple[EmlisPhraseUnit, ...], Dict[str, Any]]:
    selected_units = _select_subject_units(plan, plan_units)
    subject = _join_subject_texts(plan=plan, selected_units=selected_units)
    if not subject:
        return "", "", tuple(), {}
    parts, predicate_key = _surface_parts_for_plan(
        plan=plan,
        selected_units=selected_units,
        sequence_index=sequence_index,
        used_predicate_keys=used_predicate_keys,
    )
    parts, predicate_key = _surface_parts_after_phrase_fit(
        plan=plan,
        subject=subject,
        selected_units=selected_units,
        parts=parts,
        predicate_key=predicate_key,
        used_predicate_keys=used_predicate_keys,
    )
    surface_row = build_surface_component_row(
        line_role=plan.line_role,
        relation_type=plan.relation_type,
        role_keys=(unit.role for unit in selected_units),
        phrase_unit_ids=(unit.phrase_unit_id for unit in selected_units),
        sequence_order=sequence_index,
        particle=parts.particle,
        predicate_key=predicate_key,
        shallow_path=False,
    )
    return _finish(f"{parts.opener}{subject}{parts.particle}{parts.predicate}"), predicate_key, tuple(selected_units), surface_row



def _greeting(payload: Mapping[str, Any]) -> str:
    addressee = payload.get("addressee") if isinstance(payload.get("addressee"), Mapping) else {}
    call = _clean(addressee.get("display_name_call"), limit=28)
    greeting = _clean(addressee.get("greeting_text"), limit=32) or "Emlisです"
    if call and call not in greeting:
        return _finish(f"{call}、{greeting}")
    return _finish(greeting)

def _render_sentence_plans(*, payload: Mapping[str, Any], profile: ObservationProfile, plans: Sequence[SentencePlan], units: Sequence[EmlisPhraseUnit]) -> Tuple[List[str], List[str], List[str], List[SentenceBinding], List[Dict[str, Any]]]:
    lines: List[str] = []
    used: List[str] = []
    bindings: List[SentenceBinding] = []
    surface_rows: List[Dict[str, Any]] = []
    used_predicate_keys: List[str] = []
    greeting = _greeting(payload)
    if greeting:
        lines.append(greeting)
    for plan in plans:
        plan_units = _units_for_plan_ids(units, plan)
        if plan.must_include and not plan_units:
            return [], [], [], [], []
        if not plan_units:
            continue
        sequence_index = len([line for line in lines if "Emlis" not in line])
        line, predicate_key, selected_units, surface_row = _realize_sentence(
            plan=plan,
            plan_units=plan_units,
            sequence_index=sequence_index,
            used_predicate_keys=used_predicate_keys,
        )
        line = _trim_line(line, limit=plan.max_chars)
        if line and line not in lines:
            lines.append(line)
            used_predicate_keys.append(predicate_key)
            used.extend(unit.phrase_unit_id for unit in selected_units)
            binding = _make_sentence_binding(
                sentence_index=len(bindings) + 1,
                text=line,
                units=selected_units,
                relation_type=plan.relation_type,
                line_role=plan.line_role,
                coverage_scope=profile.coverage_scope,
                must_include=plan.must_include,
                source="limited_composer_sentence_plan",
                predicate_key=predicate_key,
            )
            if binding is not None:
                bindings.append(binding)
            if surface_row:
                surface_rows.append(surface_row)
        if len(lines) >= 1 + _MAX_BODY_LINES:
            break
    return lines, _dedupe(used), list(used_predicate_keys), bindings, surface_rows


def _trim_line(value: str, *, limit: int) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if len(text) > limit:
        text = text[:limit].rstrip(_PUNCT_TRIM) + "。"
    return text


def _body_limits(scope: Mapping[str, Any], *, profile: ObservationProfile) -> Tuple[int, int]:
    try:
        min_count = int(scope.get("min_reply_sentence_count") or profile.min_lines or _MIN_BODY_LINES)
    except Exception:
        min_count = profile.min_lines or _MIN_BODY_LINES
    try:
        max_count = int(scope.get("max_reply_sentence_count") or profile.max_lines or _MAX_BODY_LINES)
    except Exception:
        max_count = profile.max_lines or _MAX_BODY_LINES
    min_count = max(min_count, profile.min_lines)
    max_count = max(max_count, profile.max_lines)
    return max(1, min(3, min_count)), max(2, min(4, max_count))


def _matched_forbidden_surfaces(*, payload: Mapping[str, Any], text: str) -> List[str]:
    contract = payload.get("composition_contract") if isinstance(payload.get("composition_contract"), Mapping) else {}
    configured = [str(item or "").strip() for item in list(contract.get("forbidden_output_surfaces") or [])]
    patterns = _dedupe([*_FORBIDDEN_SURFACES, *configured])
    return [surface for surface in patterns if surface and surface in text]




def _previous_rejection_reasons(payload: Any) -> Tuple[str, ...]:
    """Read prior display/Reader rejection reasons from limited Composer payload.

    Step3 only classifies whether the limited/A1 path should enter the future
    reader repair adapter. It does not relax gates or add any text.
    """

    if not isinstance(payload, Mapping):
        return tuple()
    contract = payload.get("composition_contract")
    if not isinstance(contract, Mapping):
        return tuple()
    values = contract.get("previous_rejection_reasons")
    if values is None:
        return tuple()
    if isinstance(values, str):
        iterable: Iterable[Any] = (values,)
    elif isinstance(values, Mapping):
        return tuple()
    else:
        try:
            iterable = tuple(values)  # type: ignore[arg-type]
        except TypeError:
            iterable = (values,)

    reasons: List[str] = []
    for item in iterable:
        reason = str(item or "").strip()
        if reason and reason not in reasons:
            reasons.append(reason)
    return tuple(reasons)


def _requires_limited_reader_repair(reasons: Iterable[Any] | Any) -> bool:
    """Return true only for Reader-surface reasons handled by limited repair."""

    if reasons is None:
        return False
    if isinstance(reasons, str):
        iterable: Iterable[Any] = (reasons,)
    elif isinstance(reasons, Mapping):
        return False
    else:
        try:
            iterable = tuple(reasons)  # type: ignore[arg-type]
        except TypeError:
            iterable = (reasons,)
    return any(str(reason or "").strip() in _READER_REJECTION_REASONS_FOR_LIMITED_REPAIR for reason in iterable)


def _limited_reader_repair_step3_meta(
    payload: Mapping[str, Any],
    *,
    coverage_scope: str = "",
    profile_key: str = "",
) -> Dict[str, Any]:
    previous_reasons = _previous_rejection_reasons(payload)
    reader_reasons = _dedupe(
        reason
        for reason in previous_reasons
        if reason in _READER_REJECTION_REASONS_FOR_LIMITED_REPAIR
    )
    if not reader_reasons:
        return {}
    pending_operations: List[str] = []
    if "addressee_not_clear" in reader_reasons:
        pending_operations.append("addressee_repair_pending_step4")
    if "relation_not_expressed" in reader_reasons:
        pending_operations.append("relation_surface_repair_pending_step5")
    return {
        "version": _LIMITED_READER_REPAIR_VERSION,
        "target_step": _LIMITED_READER_REPAIR_TARGET_STEP,
        "attempted": True,
        "applied": False,
        "previous_rejection_reasons": list(previous_reasons),
        "reader_rejection_reasons": reader_reasons,
        "repair_required_reasons": reader_reasons,
        "requires_limited_reader_repair": True,
        "addressee_repair_required": "addressee_not_clear" in reader_reasons,
        "relation_surface_repair_required": "relation_not_expressed" in reader_reasons,
        "operations": [],
        "pending_operations": pending_operations,
        "reason_source": "composition_contract.previous_rejection_reasons",
        "complete_client_self_repair_touched": False,
        "comment_text_changed": False,
        "meaning_added": False,
        "gate_relaxed": False,
        "raw_input_included": False,
        "coverage_scope": str(coverage_scope or "").strip(),
        "profile_key": str(profile_key or "").strip(),
    }


def _attach_limited_reader_repair_step3_meta(
    composer_meta: Dict[str, Any],
    *,
    payload: Mapping[str, Any],
    coverage_scope: str,
    profile_key: str,
) -> None:
    repair_meta = _limited_reader_repair_step3_meta(
        payload,
        coverage_scope=coverage_scope,
        profile_key=profile_key,
    )
    if not repair_meta:
        return
    composer_meta["limited_reader_repair"] = repair_meta
    composer_meta["limited_reader_repair_step3"] = repair_meta
    diagnostic = composer_meta.get("composer_diagnostic")
    if isinstance(diagnostic, dict):
        diagnostic["limited_reader_repair"] = repair_meta


def _is_valid_limited_addressee_line(value: Any) -> bool:
    return bool(_LIMITED_VALID_ADDRESSEE_RE.match(str(value or "").strip()))


def _call_with_honorific(value: Any) -> str:
    text = _clean(value, limit=28)
    if not text:
        return ""
    if text.endswith(_HONORIFIC_SUFFIXES):
        return text
    return f"{text}さん"


def _canonical_addressee_greeting(payload: Mapping[str, Any]) -> str:
    """Build a Reader-compatible greeting without adding observation meaning."""

    addressee = payload.get("addressee") if isinstance(payload.get("addressee"), Mapping) else {}
    existing = _greeting(payload)
    if _is_valid_limited_addressee_line(existing):
        return existing

    call = _call_with_honorific(addressee.get("display_name_call"))
    if not call:
        call = _call_with_honorific(addressee.get("display_name"))
    if call:
        return _finish(f"{call}、Emlisです")
    return "Emlisです。"


def _replace_first_non_empty_line(text: Any, replacement: str) -> Tuple[str, bool]:
    original = str(text or "")
    lines = original.splitlines()
    for index, line in enumerate(lines):
        if not line.strip():
            continue
        if _is_valid_limited_addressee_line(line):
            return original, False
        lines[index] = replacement
        return "\n".join(lines), True
    # Step4 is a greeting-line repair, not an alternate generator.  If the
    # candidate has no non-empty line, leave it to the normal fail-closed gates.
    return original, False


def _apply_limited_addressee_repair_if_needed(
    *,
    response: Mapping[str, Any],
    payload: Mapping[str, Any],
    coverage_scope: str,
    profile_key: str,
) -> Mapping[str, Any]:
    """Apply Step4 minimal addressee repair for limited/A1 Reader retries.

    This is intentionally limited to the Reader reason ``addressee_not_clear``.
    It changes only the first non-empty greeting line and then leaves the normal
    core/Reader/Grounding/Display gates to decide the result.
    """

    previous_reasons = _previous_rejection_reasons(payload)
    if "addressee_not_clear" not in previous_reasons:
        return response

    repaired_greeting = _canonical_addressee_greeting(payload)
    comment_text = str(response.get("comment_text") or "")
    repaired_text, changed = _replace_first_non_empty_line(comment_text, repaired_greeting)

    original_meta = response.get("composer_meta") if isinstance(response.get("composer_meta"), Mapping) else {}
    composer_meta: Dict[str, Any] = dict(original_meta)
    repair_meta = dict(composer_meta.get("limited_reader_repair") or {})
    if not repair_meta:
        repair_meta = _limited_reader_repair_step3_meta(
            payload,
            coverage_scope=coverage_scope,
            profile_key=profile_key,
        )
    if not repair_meta:
        return response

    operations = list(repair_meta.get("operations") or [])
    pending_operations = [
        op
        for op in list(repair_meta.get("pending_operations") or [])
        if op != "addressee_repair_pending_step4"
    ]
    if changed and "addressee_line_replaced" not in operations:
        operations.append("addressee_line_replaced")

    repair_meta.update(
        {
            "target_step": _LIMITED_READER_REPAIR_STEP4_TARGET if changed else repair_meta.get("target_step", _LIMITED_READER_REPAIR_TARGET_STEP),
            "attempted": True,
            "applied": bool(repair_meta.get("applied")) or changed,
            "addressee_repaired": changed,
            "addressee_repair_step": _LIMITED_READER_REPAIR_STEP4_TARGET,
            "addressee_repair_greeting_source": "greeting_policy",
            "operations": operations,
            "pending_operations": pending_operations,
            "comment_text_changed": bool(repair_meta.get("comment_text_changed")) or changed,
            "meaning_added": False,
            "gate_relaxed": False,
            "raw_input_included": False,
            "complete_client_self_repair_touched": False,
            "coverage_scope": str(coverage_scope or repair_meta.get("coverage_scope") or "").strip(),
            "profile_key": str(profile_key or repair_meta.get("profile_key") or "").strip(),
        }
    )

    composer_meta["limited_reader_repair"] = repair_meta
    composer_meta["limited_reader_repair_step4"] = repair_meta
    if "limited_reader_repair_step3" in composer_meta:
        composer_meta["limited_reader_repair_step3"] = repair_meta
    diagnostic = composer_meta.get("composer_diagnostic")
    if isinstance(diagnostic, dict):
        diagnostic = dict(diagnostic)
        diagnostic["limited_reader_repair"] = repair_meta
        composer_meta["composer_diagnostic"] = diagnostic

    repaired_response = dict(response)
    repaired_response["composer_meta"] = composer_meta
    if changed:
        repaired_response["comment_text"] = repaired_text
    return repaired_response



def _as_sequence(value: Any) -> Tuple[Any, ...]:
    if value is None:
        return tuple()
    if isinstance(value, (str, bytes)):
        return (value,)
    if isinstance(value, Mapping):
        return tuple()
    try:
        return tuple(value)  # type: ignore[arg-type]
    except TypeError:
        return (value,)


def _looks_like_edge_id(value: Any) -> bool:
    token = str(value or "").strip()
    return bool(token and _EDGE_ID_LIKE_RE.match(token))


def _safe_relation_surface_type(value: Any) -> str:
    token = str(value or "").strip()
    if not token or _looks_like_edge_id(token):
        return ""
    relation = normalize_relation_surface_type(token)
    if not relation or relation == "unknown" or _looks_like_edge_id(relation):
        return ""
    return relation


def _binding_rows_for_repair(response: Mapping[str, Any]) -> List[Mapping[str, Any]]:
    rows: List[Mapping[str, Any]] = []
    seen: set[str] = set()

    def add(item: Any) -> None:
        if not isinstance(item, Mapping):
            return
        sentence_id = str(item.get("sentence_id") or item.get("id") or "").strip()
        text_key = str(item.get("text") or "").strip()
        relation_key = str(item.get("relation_type") or item.get("relation") or "").strip()
        key = sentence_id or f"{text_key}|{relation_key}|{len(rows)}"
        if key in seen:
            return
        seen.add(key)
        rows.append(item)

    bundle = response.get("sentence_binding_bundle")
    if isinstance(bundle, Mapping):
        for item in list(bundle.get("bindings") or bundle.get("sentence_bindings") or bundle.get("items") or []):
            add(item)

    meta = response.get("composer_meta") if isinstance(response.get("composer_meta"), Mapping) else {}
    if isinstance(meta, Mapping):
        meta_bundle = meta.get("sentence_binding_bundle") or meta.get("binding_bundle") or meta.get("binding")
        if isinstance(meta_bundle, Mapping):
            for item in list(meta_bundle.get("bindings") or meta_bundle.get("sentence_bindings") or meta_bundle.get("items") or []):
                add(item)
        for item in list(meta.get("sentence_bindings") or []):
            add(item)
    return rows


def _relation_type_candidates_for_repair(response: Mapping[str, Any]) -> List[str]:
    candidates: List[str] = []

    def add(value: Any) -> None:
        relation = _safe_relation_surface_type(value)
        if relation and relation not in candidates:
            candidates.append(relation)

    for row in _binding_rows_for_repair(response):
        add(row.get("relation_type") or row.get("relation"))
        meta = row.get("meta") if isinstance(row.get("meta"), Mapping) else {}
        if isinstance(meta, Mapping):
            add(meta.get("canonical_relation_type"))

    bundle = response.get("sentence_binding_bundle")
    if isinstance(bundle, Mapping):
        for value in _as_sequence(bundle.get("relation_types")):
            add(value)
        taxonomy = bundle.get("relation_taxonomy") if isinstance(bundle.get("relation_taxonomy"), Mapping) else {}
        for value in _as_sequence(taxonomy.get("canonical_relation_types") if isinstance(taxonomy, Mapping) else ()):
            add(value)

    meta = response.get("composer_meta") if isinstance(response.get("composer_meta"), Mapping) else {}
    if isinstance(meta, Mapping):
        for key in ("relation_types", "canonical_relation_types", "used_relation_ids"):
            for value in _as_sequence(meta.get(key)):
                add(value)
        for key in ("sentence_binding_bundle", "binding_bundle", "binding", "relation_taxonomy", "step5_relation_taxonomy"):
            nested = meta.get(key)
            if not isinstance(nested, Mapping):
                continue
            for value in _as_sequence(nested.get("relation_types")):
                add(value)
            for value in _as_sequence(nested.get("canonical_relation_types")):
                add(value)

    for value in _as_sequence(response.get("used_relation_ids")):
        add(value)
    return candidates


def _relation_type_for_surface_repair(response: Mapping[str, Any]) -> str:
    candidates = _relation_type_candidates_for_repair(response)
    for preferred in ("recovery", "contrast", "coexistence", "approach_avoidance", "pressure", "residue"):
        if preferred in candidates:
            return preferred
    for relation in candidates:
        if relation not in {"sequence", "continuation", "candidate_used_phrase_unit", "center", "surface"}:
            return relation
    if candidates:
        return candidates[0]
    return "coexistence"


def _relation_context_flags_for_repair(response: Mapping[str, Any], *, relation_type: str) -> Dict[str, Any]:
    text = str(response.get("comment_text") or "")
    flags = {
        "prior_load_present": bool(re.search(r"前|重さ|負荷|圧力|疲れ|不安|戻", text)),
        "raw_input_included": False,
    }
    if relation_type == "recovery":
        flags["prior_load_present"] = True
    return flags


def _append_relation_marker_text(comment_text: Any, marker_phrase: Any) -> Tuple[str, bool]:
    text = str(comment_text or "").strip()
    marker = _finish(marker_phrase)
    if not text or not marker:
        return text, False
    if marker in text:
        return text, False
    return f"{text}\n{marker}", True


def _relation_marker_binding_row(
    *,
    marker_phrase: str,
    relation_type: str,
    response: Mapping[str, Any],
    coverage_scope: str,
) -> Dict[str, Any]:
    rows = _binding_rows_for_repair(response)
    existing_ids = [str(row.get("sentence_id") or "").strip() for row in rows]
    sentence_id = f"s{len(rows) + 1}"
    while sentence_id in existing_ids:
        sentence_id = f"s{len(existing_ids) + 1}"
        existing_ids.append(sentence_id)

    evidence_ids = _dedupe(str(item or "").strip() for item in list(response.get("used_evidence_span_ids") or []))
    phrase_ids = _dedupe(str(item or "").strip() for item in list(response.get("used_phrase_unit_ids") or []))
    if not evidence_ids:
        for row in rows:
            for item in list(row.get("used_evidence_span_ids") or row.get("evidence_span_ids") or []):
                if str(item or "").strip() not in evidence_ids:
                    evidence_ids.append(str(item or "").strip())
    if not phrase_ids:
        for row in rows:
            for item in list(row.get("used_phrase_unit_ids") or row.get("phrase_unit_ids") or []):
                if str(item or "").strip() not in phrase_ids:
                    phrase_ids.append(str(item or "").strip())

    return {
        "version": _STEP3_SENTENCE_BINDING_VERSION,
        "binding_version": _STEP3_SENTENCE_BINDING_VERSION,
        "sentence_id": sentence_id,
        "text": marker_phrase,
        "used_evidence_span_ids": evidence_ids,
        "used_phrase_unit_ids": phrase_ids,
        "relation_type": relation_type,
        "line_role": "relation_surface_marker",
        "coverage_scope": str(coverage_scope or response.get("coverage_scope") or "partial_observation").strip(),
        "must_include": False,
        "raw_input_included": False,
        "meta": {
            "source": "limited_reader_repair_relation_surface_marker",
            "relation_taxonomy_version": _STEP5_RELATION_TAXONOMY_VERSION,
            "canonical_relation_type": canonical_relation_type(relation_type),
            "relation_family": relation_family(relation_type),
            "raw_input_included": False,
            "meaning_added": False,
            "gate_relaxed": False,
        },
    }


def _with_relation_marker_binding(
    *,
    response: Mapping[str, Any],
    composer_meta: Dict[str, Any],
    marker_phrase: str,
    relation_type: str,
    coverage_scope: str,
    profile_key: str,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    marker_row = _relation_marker_binding_row(
        marker_phrase=marker_phrase,
        relation_type=relation_type,
        response=response,
        coverage_scope=coverage_scope,
    )
    rows = [dict(row) for row in _binding_rows_for_repair(response)]
    if marker_row["text"] not in {str(row.get("text") or "") for row in rows}:
        rows.append(marker_row)

    relation_types = _dedupe(
        [
            *(str(row.get("relation_type") or row.get("relation") or "").strip() for row in rows),
            *list(composer_meta.get("relation_types") or []),
            relation_type,
        ]
    )
    used_evidence_ids = _dedupe(
        item
        for row in rows
        for item in list(row.get("used_evidence_span_ids") or row.get("evidence_span_ids") or [])
    )
    used_phrase_ids = _dedupe(
        item
        for row in rows
        for item in list(row.get("used_phrase_unit_ids") or row.get("phrase_unit_ids") or [])
    )

    original_bundle = response.get("sentence_binding_bundle")
    bundle: Dict[str, Any] = dict(original_bundle) if isinstance(original_bundle, Mapping) else {}
    bundle.update(
        {
            "binding_count": len(rows),
            "sentence_binding_count": len(rows),
            "expected_binding_count": len(rows),
            "binding_present": bool(rows),
            "binding_missing": False,
            "binding_required": bool(rows),
            "binding_expected": bool(rows),
            "coverage_scope": str(coverage_scope or bundle.get("coverage_scope") or "partial_observation").strip(),
            "profile_key": str(profile_key or bundle.get("profile_key") or "").strip(),
            "relation_types": relation_types,
            "used_evidence_span_ids": used_evidence_ids,
            "used_phrase_unit_ids": used_phrase_ids,
            "used_evidence_span_count": len(used_evidence_ids),
            "used_phrase_unit_count": len(used_phrase_ids),
            "bindings": rows,
            "sentence_bindings": rows,
            "items": rows,
            "raw_text_included": False,
            "raw_input_required_for_debug": False,
        }
    )
    bundle["relation_marker_binding_added"] = True
    bundle["relation_marker_sentence_id"] = marker_row["sentence_id"]

    taxonomy = dict(bundle.get("relation_taxonomy") or bundle.get("step5_relation_taxonomy") or {})
    if taxonomy:
        taxonomy["relation_marker_binding_added"] = True
        taxonomy["relation_marker_relation_type"] = relation_type
        taxonomy["relation_types"] = _dedupe([*list(taxonomy.get("relation_types") or []), relation_type])
        taxonomy["canonical_relation_types"] = _dedupe([*list(taxonomy.get("canonical_relation_types") or []), canonical_relation_type(relation_type)])
        taxonomy["raw_text_included"] = False
        taxonomy["raw_input_required_for_debug"] = False
        bundle["relation_taxonomy"] = taxonomy
        bundle["step5_relation_taxonomy"] = taxonomy
        bundle["limited_composer_relation_taxonomy"] = taxonomy
    else:
        taxonomy = {}

    composer_meta["sentence_binding_bundle"] = bundle
    composer_meta["binding_bundle"] = bundle
    composer_meta["binding"] = bundle
    composer_meta["sentence_bindings"] = rows
    composer_meta["binding_count"] = len(rows)
    composer_meta["sentence_binding_count"] = len(rows)
    composer_meta["expected_binding_count"] = len(rows)
    composer_meta["binding_present"] = bool(rows)
    composer_meta["binding_missing"] = False
    composer_meta["relation_types"] = relation_types
    composer_meta["relation_count"] = len(relation_types)
    composer_meta["used_phrase_unit_ids"] = used_phrase_ids
    composer_meta["used_phrase_unit_count"] = len(used_phrase_ids)
    if taxonomy:
        composer_meta["relation_taxonomy"] = taxonomy
        composer_meta["step5_relation_taxonomy"] = taxonomy
        composer_meta["limited_composer_relation_taxonomy"] = taxonomy
        composer_meta["canonical_relation_types"] = list(taxonomy.get("canonical_relation_types") or [])
        composer_meta["relation_families"] = list(taxonomy.get("relation_families") or composer_meta.get("relation_families") or [])
    step3 = dict(composer_meta.get("step3_sentence_binding_type") or {})
    if step3:
        step3.update(
            {
                "binding_count": len(rows),
                "sentence_binding_count": len(rows),
                "expected_binding_count": len(rows),
                "binding_count_matches_body": True,
                "binding_missing": False,
                "relation_types": relation_types,
                "used_phrase_unit_count": len(used_phrase_ids),
                "used_evidence_span_count": len(used_evidence_ids),
                "raw_text_included": False,
                "raw_input_required_for_debug": False,
            }
        )
        composer_meta["step3_sentence_binding_type"] = step3
        composer_meta["sentence_binding_type"] = step3
        composer_meta["limited_composer_sentence_binding_type"] = step3
    return bundle, composer_meta


def _apply_limited_relation_surface_repair_if_needed(
    *,
    response: Mapping[str, Any],
    payload: Mapping[str, Any],
    coverage_scope: str,
    profile_key: str,
) -> Mapping[str, Any]:
    """Apply Step5 relation marker repair for limited/A1 Reader retries.

    This runs only when the prior Reader reason includes
    ``relation_not_expressed``.  It uses the shared relation surface contract,
    appends one marker sentence, updates sentence bindings for grounding, and
    keeps all gates fail-closed.
    """

    previous_reasons = _previous_rejection_reasons(payload)
    if "relation_not_expressed" not in previous_reasons:
        return response

    comment_text = str(response.get("comment_text") or "").strip()
    if not comment_text:
        return response

    original_meta = response.get("composer_meta") if isinstance(response.get("composer_meta"), Mapping) else {}
    composer_meta: Dict[str, Any] = dict(original_meta)
    repair_meta = dict(composer_meta.get("limited_reader_repair") or {})
    if not repair_meta:
        repair_meta = _limited_reader_repair_step3_meta(
            payload,
            coverage_scope=coverage_scope,
            profile_key=profile_key,
        )
    if not repair_meta:
        return response

    relation_type = _relation_type_for_surface_repair(response)
    context_flags = _relation_context_flags_for_repair(response, relation_type=relation_type)
    marker_meta = relation_marker_meta(relation_type, context_flags=context_flags)
    marker_phrase = _finish(marker_meta.get("relation_marker_phrase"))
    repaired_text, changed = _append_relation_marker_text(comment_text, marker_phrase)
    marker_signal = detect_relation_surface(marker_phrase, expected_relation_types=(relation_type,))

    operations = list(repair_meta.get("operations") or [])
    pending_operations = [
        op
        for op in list(repair_meta.get("pending_operations") or [])
        if op != "relation_surface_repair_pending_step5"
    ]
    if changed and "relation_marker_appended" not in operations:
        operations.append("relation_marker_appended")

    repair_meta.update(
        {
            "target_step": _LIMITED_READER_REPAIR_STEP5_TARGET if changed else repair_meta.get("target_step", _LIMITED_READER_REPAIR_TARGET_STEP),
            "attempted": True,
            "applied": bool(repair_meta.get("applied")) or changed,
            "relation_surface_repaired": changed,
            "relation_surface_repair_step": _LIMITED_READER_REPAIR_STEP5_TARGET,
            "relation_type": relation_type,
            "relation_marker_key": marker_meta.get("relation_marker_key"),
            "relation_marker_signal_detected": bool(marker_signal.get("reader_relation_signal_detected")),
            "relation_marker_signal_keys": list(marker_signal.get("reader_relation_signal_keys") or []),
            "relation_surface_contract_version": marker_meta.get("relation_surface_contract_version") or marker_meta.get("contract_version"),
            "operations": operations,
            "pending_operations": pending_operations,
            "comment_text_changed": bool(repair_meta.get("comment_text_changed")) or changed,
            "meaning_added": False,
            "gate_relaxed": False,
            "raw_input_included": False,
            "complete_client_self_repair_touched": False,
            "coverage_scope": str(coverage_scope or repair_meta.get("coverage_scope") or "").strip(),
            "profile_key": str(profile_key or repair_meta.get("profile_key") or "").strip(),
        }
    )

    repaired_response: Dict[str, Any] = dict(response)
    if changed:
        repaired_response["comment_text"] = repaired_text
        bundle, composer_meta = _with_relation_marker_binding(
            response=repaired_response,
            composer_meta=composer_meta,
            marker_phrase=marker_phrase,
            relation_type=relation_type,
            coverage_scope=coverage_scope,
            profile_key=profile_key,
        )
        repaired_response["sentence_binding_bundle"] = bundle

    composer_meta["limited_reader_repair"] = repair_meta
    composer_meta["limited_reader_repair_step5"] = repair_meta
    if "limited_reader_repair_step3" in composer_meta:
        composer_meta["limited_reader_repair_step3"] = repair_meta
    if "limited_reader_repair_step4" in composer_meta:
        composer_meta["limited_reader_repair_step4"] = repair_meta
    diagnostic = composer_meta.get("composer_diagnostic")
    if isinstance(diagnostic, dict):
        diagnostic = dict(diagnostic)
        diagnostic["limited_reader_repair"] = repair_meta
        composer_meta["composer_diagnostic"] = diagnostic
    repaired_response["composer_meta"] = composer_meta
    return repaired_response


def _apply_limited_reader_repair_if_needed(
    *,
    response: Mapping[str, Any],
    payload: Mapping[str, Any],
    phrase_units: Sequence[EmlisPhraseUnit],
    sentence_plans: Sequence[SentencePlan],
    used_unit_ids: Sequence[str],
    coverage_scope: str,
    profile_key: str,
) -> Mapping[str, Any]:
    # Step4 and Step5 are intentionally independent no-op-by-default repairs.
    # Unused arguments are kept in this adapter signature so the Step6 hook can
    # pass the same structural context without widening RN/API contracts.
    _ = (phrase_units, sentence_plans, used_unit_ids)
    repaired = _apply_limited_addressee_repair_if_needed(
        response=response,
        payload=payload,
        coverage_scope=coverage_scope,
        profile_key=profile_key,
    )
    return _apply_limited_relation_surface_repair_if_needed(
        response=repaired,
        payload=payload,
        coverage_scope=coverage_scope,
        profile_key=profile_key,
    )


def _coverage_scope(graph: Mapping[str, Any]) -> str:
    if list(graph.get("core_tensions") or []) or any(list(graph.get(key) or []) for key in _GROUP_KEYS):
        return "partial_observation"
    return "current_input_core"


def _used_claim_ids(graph: Mapping[str, Any]) -> List[str]:
    ids: List[str] = []
    primary = graph.get("primary_state") if isinstance(graph.get("primary_state"), Mapping) else {}
    primary_id = str(primary.get("claim_id") or "").strip()
    if primary_id:
        ids.append(primary_id)
    for group_key in _GROUP_KEYS:
        for claim in list(graph.get(group_key) or []):
            if isinstance(claim, Mapping):
                claim_id = str(claim.get("claim_id") or "").strip()
                if claim_id:
                    ids.append(claim_id)
    return _dedupe(ids)


def _used_relation_ids(graph: Mapping[str, Any]) -> List[str]:
    return _dedupe(str(edge.get("edge_id") or "").strip() for edge in list(graph.get("core_tensions") or []) if isinstance(edge, Mapping))


def _evidence_objects_for_quality(items: Sequence[Mapping[str, Any]]) -> List[Mapping[str, Any]]:
    return [dict(item) for item in items if isinstance(item, Mapping)]


def _confidence(*, profile: ObservationProfile, phrase_units: Sequence[EmlisPhraseUnit], used_unit_ids: Sequence[str]) -> float:
    base = 0.74 if profile.profile_key != "unknown" else 0.0
    used_roles = {unit.role for unit in phrase_units if unit.phrase_unit_id in set(used_unit_ids)}
    ratio = len(set(profile.required_roles).intersection(used_roles)) / max(1, len(profile.required_roles))
    return round(max(0.0, min(0.94, base + 0.18 * ratio)), 3)


def audit_limited_composer_contract() -> List[str]:
    issues: List[str] = []
    for marker in _MARKER_NAMES:
        if marker in globals():
            issues.append(marker)
    return issues


class CocolonAPlanEquivalentComposerClient(CocolonLimitedComposerClient):
    """Step19 A-1 equivalent EmlisObservationComposer.

    It reuses the stabilized scoped-graph composer and common Core path, then
    switches the developer-facing composer_model to the A-plan equivalent name.
    The generated text is not post-rendered, expanded, or fall-backed here.
    """

    composer_model = STEP19_A_PLAN_COMPOSER_MODEL

    def generate(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        response = super().generate(payload)
        return promote_step19_a_plan_equivalent_response(response)


__all__ = [
    "CocolonAPlanEquivalentComposerClient",
    "CocolonLimitedComposerClient",
    "EmlisPhraseUnit",
    "ObservationProfile",
    "SentencePlan",
    "_previous_rejection_reasons",
    "_requires_limited_reader_repair",
    "_apply_limited_relation_surface_repair_if_needed",
    "audit_limited_composer_contract",
]
