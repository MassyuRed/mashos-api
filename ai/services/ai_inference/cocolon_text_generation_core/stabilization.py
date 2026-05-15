# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step 15 common Core stabilization helpers.

This module is intentionally additive.  It records whether a core-specific
adapter is using the shared text-generation shapes without moving the
core-specific output purpose, tone, public response keys, routes, or DB names
into the common core.
"""

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from cocolon_text_generation_core.policies import (
    CORE_ID_ANALYSIS,
    CORE_ID_EMLIS,
    CORE_ID_PIECE,
    PASSING_STATUSES,
    compact_tokens,
)
from cocolon_text_generation_core.result import json_safe_mapping
from cocolon_text_generation_core.types import CoreTextPayload, TextGenerationResult

STEP15_STABILIZATION_NAME = "cocolon_text_generation_core.step15_stabilization.v1"
STEP15_PHASE_LABEL = "step15_common_core_stabilization"

CORE_SPECIFIC_OUTPUT_PURPOSE = {
    CORE_ID_EMLIS: "emlis_observation",
    CORE_ID_PIECE: "piece_question_answer",
    CORE_ID_ANALYSIS: "analysis_observation_report",
}

CORE_SPECIFIC_PUBLIC_CONTRACTS = {
    CORE_ID_EMLIS: ("input_feedback.comment_text", "observation_status", "Emlisの観測"),
    CORE_ID_PIECE: ("piece_text", "reflection", "mymodel_qna"),
    CORE_ID_ANALYSIS: ("content_json", "standardReport", "contentText"),
}

COMMON_QUALITY_PART_KEYS = (
    "SourceAnchor",
    "EvidenceSpanLike",
    "PhraseUnit",
    "SentencePlan",
    "TextGenerationResult",
    "GuardResult",
    "used_evidence_span_ids",
    "quality_flags",
)

_REQUIRED_COMMON_GUARDS = (
    "japanese_coherence",
    "template_echo",
    "overclaim",
    "grounding",
    "must_keep",
)


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _as_list(value: Iterable[Any] | Any | None) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


def _tokens(value: Iterable[Any] | Any | None) -> tuple[str, ...]:
    return compact_tokens(_as_list(value))


def _guard_results_from_result(result: TextGenerationResult | None) -> tuple[Mapping[str, Any], ...]:
    if result is None or not isinstance(getattr(result, "meta", None), Mapping):
        return tuple()
    raw = result.meta.get("guard_results")
    if not isinstance(raw, (list, tuple)):
        return tuple()
    return tuple(item for item in raw if isinstance(item, Mapping))


def _guard_names(result: TextGenerationResult | None) -> tuple[str, ...]:
    names: list[str] = []
    for item in _guard_results_from_result(result):
        name = _clean(item.get("guard_name"))
        if name and name not in names:
            names.append(name)
    return tuple(names)


def _has_required_guard_family(guard_names: Iterable[str], family: str) -> bool:
    return any(family in name for name in guard_names)


def _payload_evidence_ids(payload: CoreTextPayload | None) -> set[str]:
    if payload is None:
        return set()
    return {_clean(getattr(span, "span_id", "")) for span in tuple(payload.evidence_spans or ()) if _clean(getattr(span, "span_id", ""))}


def _payload_phrase_ids(payload: CoreTextPayload | None) -> set[str]:
    if payload is None:
        return set()
    return {_clean(getattr(unit, "phrase_unit_id", "")) for unit in tuple(payload.phrase_units or ()) if _clean(getattr(unit, "phrase_unit_id", ""))}


def _shared_quality_parts(payload: CoreTextPayload | None, result: TextGenerationResult | None) -> dict[str, bool]:
    guard_names = _guard_names(result)
    return {
        "SourceAnchor": bool(payload and tuple(payload.source_anchors or ())),
        "EvidenceSpanLike": bool(payload and tuple(payload.evidence_spans or ())),
        "PhraseUnit": bool(payload and tuple(payload.phrase_units or ())),
        "SentencePlan": bool(payload and tuple(payload.sentence_plans or ())),
        "TextGenerationResult": isinstance(result, TextGenerationResult),
        "GuardResult": bool(guard_names),
        "used_evidence_span_ids": isinstance(result, TextGenerationResult) and hasattr(result, "used_evidence_span_ids"),
        "quality_flags": isinstance(result, TextGenerationResult) and hasattr(result, "quality_flags"),
    }


def _shape_issues(payload: CoreTextPayload | None, result: TextGenerationResult | None, *, require_guard_results: bool) -> tuple[str, ...]:
    issues: list[str] = []
    if not isinstance(payload, CoreTextPayload):
        issues.append("core_text_payload_missing")
        return tuple(issues)
    if not isinstance(result, TextGenerationResult):
        issues.append("text_generation_result_missing")
        return tuple(issues)

    evidence_ids = _payload_evidence_ids(payload)
    phrase_ids = _payload_phrase_ids(payload)
    if not evidence_ids:
        issues.append("common_evidence_span_missing")
    if not phrase_ids:
        issues.append("common_phrase_unit_missing")
    if not tuple(payload.sentence_plans or ()):  # generated adapters should have a plan even for shallow paths.
        issues.append("common_sentence_plan_missing")

    for unit in tuple(payload.phrase_units or ()):  # pragma: no branch - small loop, intentionally explicit.
        unit_id = _clean(getattr(unit, "phrase_unit_id", ""))
        evidence_span_id = _clean(getattr(unit, "evidence_span_id", ""))
        text = _clean(getattr(unit, "text", ""))
        if not unit_id or not evidence_span_id or not text:
            issues.append("phrase_unit_common_shape_incomplete")
            break
        if evidence_span_id not in evidence_ids:
            issues.append("phrase_unit_evidence_span_not_in_payload")
            break

    for plan in tuple(payload.sentence_plans or ()):  # pragma: no branch - small loop, intentionally explicit.
        ids = _tokens(getattr(plan, "phrase_unit_ids", ()))
        if not ids:
            issues.append("sentence_plan_phrase_units_missing")
            break
        if any(unit_id not in phrase_ids for unit_id in ids):
            issues.append("sentence_plan_phrase_unit_not_in_payload")
            break

    guard_names = _guard_names(result)
    if require_guard_results and not guard_names:
        issues.append("common_guard_results_missing")
    for family in _REQUIRED_COMMON_GUARDS:
        if require_guard_results and not _has_required_guard_family(guard_names, family):
            issues.append(f"common_guard_family_missing:{family}")

    used_ids = set(_tokens(result.used_evidence_span_ids))
    if result.status in PASSING_STATUSES:
        if not result.text:
            issues.append("passing_result_text_missing")
        if not used_ids:
            issues.append("passing_result_used_evidence_missing")
        if any(span_id not in evidence_ids for span_id in used_ids):
            issues.append("passing_result_used_evidence_outside_payload")
    elif result.text:
        issues.append("fail_closed_result_keeps_text")

    return tuple(dict.fromkeys(issues))


def _core_specific_issues(
    payload: CoreTextPayload | None,
    *,
    expected_core_id: str | None,
    output_contract: Mapping[str, Any] | None,
) -> tuple[str, ...]:
    issues: list[str] = []
    if not isinstance(payload, CoreTextPayload):
        return ("core_specific_payload_missing",)

    expected = _clean(expected_core_id) or _clean(payload.core_id)
    if expected and _clean(payload.core_id) != expected:
        issues.append("core_id_mismatch")

    contract = output_contract if isinstance(output_contract, Mapping) else {}
    contract_core = _clean(contract.get("core_id"))
    if contract_core and contract_core != _clean(payload.core_id):
        issues.append("output_contract_core_id_mismatch")

    expected_purpose = CORE_SPECIFIC_OUTPUT_PURPOSE.get(_clean(payload.core_id), "")
    output_purpose = _clean(contract.get("output_purpose")) or _clean(payload.tone_policy.get("output_purpose"))
    if expected_purpose and output_purpose and output_purpose != expected_purpose:
        issues.append("output_purpose_mismatch")

    if contract.get("db_rename_or_drop") is True:
        issues.append("db_rename_or_drop_requested")
    if contract.get("public_api_route_change") is True:
        issues.append("public_api_route_change_requested")
    if contract.get("public_response_key_change") is True:
        issues.append("public_response_key_change_requested")
    if contract.get("emlis_voice_shared_to_other_cores") is True:
        issues.append("emlis_voice_shared_to_other_cores")

    if _clean(payload.core_id) == CORE_ID_EMLIS:
        if contract and _clean(contract.get("comment_text_contract")) != "passed_only":
            issues.append("emlis_comment_text_contract_not_passed_only")
        if contract and contract.get("passed_only_display") is not True:
            issues.append("emlis_passed_only_display_not_confirmed")
        if contract and contract.get("scoped_grounding") is not True:
            issues.append("emlis_scoped_grounding_not_confirmed")

    return tuple(dict.fromkeys(issues))


@dataclass(frozen=True)
class CoreStabilizationReport:
    """JSON-safe Step 15 report for a core-specific adapter evaluation."""

    report_name: str = STEP15_STABILIZATION_NAME
    phase: str = STEP15_PHASE_LABEL
    core_id: str = ""
    passed: bool = False
    shared_quality_parts: Mapping[str, bool] = field(default_factory=dict)
    core_specific_contract: Mapping[str, Any] = field(default_factory=dict)
    guard_names: Iterable[str] = field(default_factory=tuple)
    issue_codes: Iterable[str] = field(default_factory=tuple)
    meta: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "report_name", _clean(self.report_name) or STEP15_STABILIZATION_NAME)
        object.__setattr__(self, "phase", _clean(self.phase) or STEP15_PHASE_LABEL)
        object.__setattr__(self, "core_id", _clean(self.core_id))
        object.__setattr__(self, "shared_quality_parts", {str(k): bool(v) for k, v in dict(self.shared_quality_parts or {}).items()})
        object.__setattr__(self, "core_specific_contract", json_safe_mapping(self.core_specific_contract))
        object.__setattr__(self, "guard_names", _tokens(self.guard_names))
        object.__setattr__(self, "issue_codes", _tokens(self.issue_codes))
        object.__setattr__(self, "passed", bool(self.passed) and not tuple(self.issue_codes))
        object.__setattr__(self, "meta", json_safe_mapping(self.meta))

    def as_meta(self) -> dict[str, Any]:
        return {
            "report_name": self.report_name,
            "phase": self.phase,
            "core_id": self.core_id,
            "passed": self.passed,
            "shared_quality_parts": dict(self.shared_quality_parts),
            "common_shapes_ready": all(bool(self.shared_quality_parts.get(key)) for key in COMMON_QUALITY_PART_KEYS),
            "core_specific_contract": dict(self.core_specific_contract),
            "guard_names": list(self.guard_names),
            "issue_codes": list(self.issue_codes),
            "meta": dict(self.meta),
        }


def emlis_observation_output_contract(
    *,
    coverage_scope: Any = "partial_observation",
    visible_name: str = "Emlisの観測",
) -> dict[str, Any]:
    """Return the Step 15 public-boundary contract for Emlis observations."""

    return {
        "core_id": CORE_ID_EMLIS,
        "output_purpose": CORE_SPECIFIC_OUTPUT_PURPOSE[CORE_ID_EMLIS],
        "core_specific_composer": "EmlisObservationComposer",
        "visible_name": visible_name,
        "public_contract_keys": list(CORE_SPECIFIC_PUBLIC_CONTRACTS[CORE_ID_EMLIS]),
        "comment_text_contract": "passed_only",
        "passed_only_display": True,
        "scoped_grounding": _clean(coverage_scope) != "full_graph",
        "db_rename_or_drop": False,
        "public_api_route_change": False,
        "public_response_key_change": False,
        "emlis_voice_shared_to_other_cores": False,
    }


def build_core_stabilization_report(
    *,
    payload: CoreTextPayload | None,
    result: TextGenerationResult | None,
    expected_core_id: str | None = None,
    output_contract: Mapping[str, Any] | None = None,
    require_guard_results: bool | None = None,
    meta: Mapping[str, Any] | None = None,
) -> CoreStabilizationReport:
    """Build a Step 15 report without generating or altering user-facing text."""

    parts = _shared_quality_parts(payload, result)
    expected = _clean(expected_core_id) or (_clean(payload.core_id) if isinstance(payload, CoreTextPayload) else "")
    require_guards = bool(require_guard_results)
    if require_guard_results is None:
        require_guards = bool(isinstance(result, TextGenerationResult) and result.status in PASSING_STATUSES)
    issues = tuple(
        dict.fromkeys(
            tuple(f"common_part_missing:{key}" for key, ready in parts.items() if not ready and key in COMMON_QUALITY_PART_KEYS)
            + _shape_issues(payload, result, require_guard_results=require_guards)
            + _core_specific_issues(payload, expected_core_id=expected, output_contract=output_contract)
        )
    )
    return CoreStabilizationReport(
        core_id=expected,
        passed=not issues,
        shared_quality_parts=parts,
        core_specific_contract=output_contract or {},
        guard_names=_guard_names(result),
        issue_codes=issues,
        meta=meta or {},
    )


__all__ = [
    "COMMON_QUALITY_PART_KEYS",
    "CORE_SPECIFIC_OUTPUT_PURPOSE",
    "CORE_SPECIFIC_PUBLIC_CONTRACTS",
    "CoreStabilizationReport",
    "STEP15_PHASE_LABEL",
    "STEP15_STABILIZATION_NAME",
    "build_core_stabilization_report",
    "emlis_observation_output_contract",
]
