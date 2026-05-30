# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase18 diagnostic failure taxonomy for EmlisAI.

This module is meta-only. It converts existing gate / status / reason-code
signals into canonical diagnostic classes and keeps legacy aliases for older
QA contracts.  It does not generate display text, change public response keys,
or relax Reader / Grounding / Template / Display / Visible gates.
"""

from collections.abc import Iterable, Mapping
from typing import Any, Final

DIAGNOSTIC_FAILURE_TAXONOMY_SCHEMA_VERSION: Final = "cocolon.emlis.diagnostic_failure_taxonomy.v1"
DIAGNOSTIC_FAILURE_TAXONOMY_SOURCE_PHASE: Final = "Phase18_product_quality_stabilization"

CANONICAL_CANDIDATE_NOT_GENERATED: Final = "candidate_not_generated"
CANONICAL_CANDIDATE_GENERATED_DISPLAY_PASSED: Final = "candidate_generated_display_passed"
CANONICAL_CANDIDATE_GENERATED_BUT_READER_REJECTED: Final = "candidate_generated_but_reader_rejected"
CANONICAL_CANDIDATE_GENERATED_BUT_GROUNDING_REJECTED: Final = "candidate_generated_but_grounding_rejected"
CANONICAL_CANDIDATE_GENERATED_BUT_TEMPLATE_REJECTED: Final = "candidate_generated_but_template_rejected"
CANONICAL_CANDIDATE_GENERATED_BUT_DISPLAY_REJECTED: Final = "candidate_generated_but_display_rejected"
CANONICAL_CANDIDATE_BLOCKED_SURFACE_GRAMMAR: Final = "candidate_blocked_surface_grammar"
CANONICAL_CANDIDATE_BLOCKED_TWO_STAGE_CONTRACT: Final = "candidate_blocked_two_stage_contract"
CANONICAL_CANDIDATE_BLOCKED_META_BOUNDARY: Final = "candidate_blocked_meta_boundary"
CANONICAL_LOW_INFORMATION_PUBLIC_REPAIR_APPLIED: Final = "low_information_public_repair_applied"
CANONICAL_LOW_INFORMATION_PUBLIC_REPAIR_FAILED: Final = "low_information_public_repair_failed"
CANONICAL_PRE_CONNECTION_BLOCKED_SAFETY: Final = "pre_connection_blocked_safety"
CANONICAL_PRE_CONNECTION_BLOCKED_SCOPE: Final = "pre_connection_blocked_scope"
CANONICAL_PRE_CONNECTION_BLOCKED_AP0: Final = "pre_connection_blocked_ap0"
CANONICAL_PRE_CONNECTION_BLOCKED_ROLLOUT: Final = "pre_connection_blocked_rollout"
CANONICAL_PRE_CONNECTION_BLOCKED_FLAG: Final = "pre_connection_blocked_flag"
CANONICAL_BACKEND_EXCEPTION_OR_TIMEOUT: Final = "backend_exception_or_timeout"
CANONICAL_UNCLASSIFIED_NON_DISPLAY: Final = "unclassified_non_display"

# Phase18-7 compatibility aliases for tests / older call sites that use the
# shorter CLASS_* prefix.  The canonical values above remain the source of truth.
CLASS_CANDIDATE_NOT_GENERATED: Final = CANONICAL_CANDIDATE_NOT_GENERATED
CLASS_CANDIDATE_GENERATED_DISPLAY_PASSED: Final = CANONICAL_CANDIDATE_GENERATED_DISPLAY_PASSED
CLASS_CANDIDATE_GENERATED_BUT_READER_REJECTED: Final = CANONICAL_CANDIDATE_GENERATED_BUT_READER_REJECTED
CLASS_CANDIDATE_GENERATED_BUT_GROUNDING_REJECTED: Final = CANONICAL_CANDIDATE_GENERATED_BUT_GROUNDING_REJECTED
CLASS_CANDIDATE_GENERATED_BUT_TEMPLATE_REJECTED: Final = CANONICAL_CANDIDATE_GENERATED_BUT_TEMPLATE_REJECTED
CLASS_CANDIDATE_GENERATED_BUT_DISPLAY_REJECTED: Final = CANONICAL_CANDIDATE_GENERATED_BUT_DISPLAY_REJECTED
CLASS_CANDIDATE_BLOCKED_SURFACE_GRAMMAR: Final = CANONICAL_CANDIDATE_BLOCKED_SURFACE_GRAMMAR
CLASS_CANDIDATE_BLOCKED_TWO_STAGE_CONTRACT: Final = CANONICAL_CANDIDATE_BLOCKED_TWO_STAGE_CONTRACT
CLASS_CANDIDATE_BLOCKED_META_BOUNDARY: Final = CANONICAL_CANDIDATE_BLOCKED_META_BOUNDARY
CLASS_LOW_INFORMATION_PUBLIC_REPAIR_APPLIED: Final = CANONICAL_LOW_INFORMATION_PUBLIC_REPAIR_APPLIED
CLASS_LOW_INFORMATION_PUBLIC_REPAIR_FAILED: Final = CANONICAL_LOW_INFORMATION_PUBLIC_REPAIR_FAILED
CLASS_PRE_CONNECTION_BLOCKED_SAFETY: Final = CANONICAL_PRE_CONNECTION_BLOCKED_SAFETY
CLASS_PRE_CONNECTION_BLOCKED_SCOPE: Final = CANONICAL_PRE_CONNECTION_BLOCKED_SCOPE
CLASS_PRE_CONNECTION_BLOCKED_AP0: Final = CANONICAL_PRE_CONNECTION_BLOCKED_AP0
CLASS_PRE_CONNECTION_BLOCKED_ROLLOUT: Final = CANONICAL_PRE_CONNECTION_BLOCKED_ROLLOUT
CLASS_PRE_CONNECTION_BLOCKED_FLAG: Final = CANONICAL_PRE_CONNECTION_BLOCKED_FLAG
CLASS_BACKEND_EXCEPTION_OR_TIMEOUT: Final = CANONICAL_BACKEND_EXCEPTION_OR_TIMEOUT
CLASS_UNCLASSIFIED_NON_DISPLAY: Final = CANONICAL_UNCLASSIFIED_NON_DISPLAY

_CANONICAL_CLASSES: Final = (
    CANONICAL_CANDIDATE_NOT_GENERATED,
    CANONICAL_CANDIDATE_GENERATED_DISPLAY_PASSED,
    CANONICAL_CANDIDATE_GENERATED_BUT_READER_REJECTED,
    CANONICAL_CANDIDATE_GENERATED_BUT_GROUNDING_REJECTED,
    CANONICAL_CANDIDATE_GENERATED_BUT_TEMPLATE_REJECTED,
    CANONICAL_CANDIDATE_GENERATED_BUT_DISPLAY_REJECTED,
    CANONICAL_CANDIDATE_BLOCKED_SURFACE_GRAMMAR,
    CANONICAL_CANDIDATE_BLOCKED_TWO_STAGE_CONTRACT,
    CANONICAL_CANDIDATE_BLOCKED_META_BOUNDARY,
    CANONICAL_LOW_INFORMATION_PUBLIC_REPAIR_APPLIED,
    CANONICAL_LOW_INFORMATION_PUBLIC_REPAIR_FAILED,
    CANONICAL_PRE_CONNECTION_BLOCKED_SAFETY,
    CANONICAL_PRE_CONNECTION_BLOCKED_SCOPE,
    CANONICAL_PRE_CONNECTION_BLOCKED_AP0,
    CANONICAL_PRE_CONNECTION_BLOCKED_ROLLOUT,
    CANONICAL_PRE_CONNECTION_BLOCKED_FLAG,
    CANONICAL_BACKEND_EXCEPTION_OR_TIMEOUT,
    CANONICAL_UNCLASSIFIED_NON_DISPLAY,
)

_LEGACY_ALIASES: Final = {
    CANONICAL_CANDIDATE_NOT_GENERATED: ["candidate_missing"],
    CANONICAL_CANDIDATE_GENERATED_DISPLAY_PASSED: ["passed_displayed", "passed_backend_frontend_hidden"],
    CANONICAL_CANDIDATE_GENERATED_BUT_READER_REJECTED: ["candidate_generated_but_reader_rejected"],
    CANONICAL_CANDIDATE_GENERATED_BUT_GROUNDING_REJECTED: ["candidate_generated_but_grounding_rejected"],
    CANONICAL_CANDIDATE_GENERATED_BUT_TEMPLATE_REJECTED: ["candidate_generated_but_template_rejected"],
    CANONICAL_CANDIDATE_GENERATED_BUT_DISPLAY_REJECTED: ["candidate_generated_but_display_rejected"],
    CANONICAL_CANDIDATE_BLOCKED_SURFACE_GRAMMAR: [
        "candidate_generated_but_display_rejected",
        "surface_quality_blocked",
        "candidate_blocked_koto_splice",
        "candidate_blocked_relation_skeleton",
    ],
    CANONICAL_CANDIDATE_BLOCKED_TWO_STAGE_CONTRACT: [
        "candidate_generated_but_display_rejected",
        "surface_quality_blocked",
    ],
    CANONICAL_CANDIDATE_BLOCKED_META_BOUNDARY: ["candidate_generated_but_display_rejected"],
    CANONICAL_LOW_INFORMATION_PUBLIC_REPAIR_APPLIED: ["candidate_unavailable_but_low_information_repaired"],
    CANONICAL_LOW_INFORMATION_PUBLIC_REPAIR_FAILED: ["candidate_unavailable_low_information_repair_failed"],
    CANONICAL_PRE_CONNECTION_BLOCKED_SAFETY: ["pre_connection_stop"],
    CANONICAL_PRE_CONNECTION_BLOCKED_SCOPE: ["pre_connection_stop"],
    CANONICAL_PRE_CONNECTION_BLOCKED_AP0: ["pre_connection_stop"],
    CANONICAL_PRE_CONNECTION_BLOCKED_ROLLOUT: ["pre_connection_stop"],
    CANONICAL_PRE_CONNECTION_BLOCKED_FLAG: ["pre_connection_stop"],
    CANONICAL_BACKEND_EXCEPTION_OR_TIMEOUT: ["backend_exception_or_timeout"],
    CANONICAL_UNCLASSIFIED_NON_DISPLAY: ["unclassified_non_display"],
}

_META_BOUNDARY_REASON_FRAGMENTS: Final = (
    "meta_boundary",
    "public_meta_leak",
    "raw_input_included",
    "raw_text_included",
    "comment_text_body_included",
    "surface_policy_included",
    "forbidden_meta",
)
_TWO_STAGE_REASON_FRAGMENTS: Final = (
    "two_stage_",
    "labelled_two_stage",
    "section_label",
    "labels_missing_or_duplicated",
)
_SURFACE_GRAMMAR_REASON_FRAGMENTS: Final = (
    "runtime_surface_pre_return_gate_failed",
    "surface_template_major",
    "malformed_phrase_unit",
    "malformed_nominalization",
    "koto_splice",
    "surface_relation_skeleton",
    "relation_skeleton",
    "generic_center_phrase",
    "same_connector_run",
    "visible_surface_acceptance_gate_failed",
    "visible_surface_acceptance_gate_classification_red",
    "visible_surface_acceptance_gate_action_block",
)
_PRE_CONNECTION_STAGES: Final = frozenset({"flag", "rollout", "scope", "ap0", "safety", "feature_flag"})
_TEXT_PAYLOAD_KEYS: Final = frozenset(
    {
        "raw_input",
        "raw_text",
        "input_text",
        "current_input",
        "memo",
        "memo_text",
        "comment_text",
        "public_comment_text",
        "candidate_comment_text",
        "observation_text",
        "reception_text",
        "body",
        "text",
        "sentence",
        "sentences",
    }
)
_CONTRACT_TRUE_FLAGS: Final = frozenset(
    {
        "raw_input_included",
        "raw_text_included",
        "comment_text_body_included",
        "generated_candidate_text_included",
        "public_response_key_added",
        "rn_visible_contract_changed",
        "display_gate_relaxed",
        "grounding_gate_relaxed",
        "reader_gate_relaxed",
        "template_gate_relaxed",
    }
)


def _clean(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, Mapping) or isinstance(value, (list, tuple, set)):
        return ""
    return str(value).strip()


def _clean_lower(value: Any) -> str:
    return _clean(value).lower()


def _safe_mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, (tuple, set)):
        return list(value)
    if isinstance(value, (str, bytes, bytearray)):
        return [value] if str(value).strip() else []
    return [value]


def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in _as_list(values):
        text = _clean(value)
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def _gate_passed(gate_results: Mapping[str, Any], *names: str) -> bool | None:
    for name in names:
        gate = _safe_mapping(gate_results.get(name))
        if "passed" in gate:
            return bool(gate.get("passed"))
    return None


def _gate_reasons(gate_results: Mapping[str, Any], *names: str) -> list[str]:
    out: list[str] = []
    for name in names:
        gate = _safe_mapping(gate_results.get(name))
        out.extend(_as_list(gate.get("rejection_reasons")))
        primary = _clean(gate.get("primary_reason"))
        if primary and primary != "passed":
            out.append(primary)
    return _dedupe(out)


def _reason_matches(reasons: Iterable[str], fragments: Iterable[str]) -> bool:
    lowered = [str(reason or "").lower() for reason in reasons]
    return any(fragment in reason for reason in lowered for fragment in fragments)


def _legacy_aliases_for(canonical: str) -> list[str]:
    return list(_LEGACY_ALIASES.get(canonical, []))


def canonicalize_legacy_diagnostic_classification(value: Any) -> str:
    raw = _clean(value)
    if not raw:
        return ""
    if raw in _CANONICAL_CLASSES:
        return raw
    for canonical, aliases in _LEGACY_ALIASES.items():
        if raw in aliases:
            return canonical
    if raw == "surface_quality_blocked":
        return CANONICAL_CANDIDATE_BLOCKED_SURFACE_GRAMMAR
    return raw


def classify_diagnostic_failure(
    *,
    observation_status: Any = "",
    stage: Any = "",
    primary_reason: Any = "",
    secondary_reasons: Any = None,
    rejection_reasons: Any = None,
    display_rejection_reasons: Any = None,
    gate_results: Mapping[str, Any] | None = None,
    runtime_surface: Mapping[str, Any] | None = None,
    display_absence_summary: Mapping[str, Any] | None = None,
    gate_failure_stage: Any = "",
    composer_status: Any = "",
    candidate_generated: Any = None,
    comment_text_allowed: Any = None,
    comment_text_present: Any = None,
    observation_reply_kind: Any = "",
    low_information_public_repair_contract: Mapping[str, Any] | None = None,
    connection_status: Any = "",
) -> str:
    """Return a canonical Phase18 diagnostic class from meta-safe signals."""

    status = _clean(observation_status)
    stage_text = _clean_lower(stage)
    primary = _clean(primary_reason)
    reasons = _dedupe(
        [
            primary,
            *_as_list(secondary_reasons),
            *_as_list(rejection_reasons),
            *_as_list(display_rejection_reasons),
        ]
    )
    gate_results = _safe_mapping(gate_results)
    runtime_surface = _safe_mapping(runtime_surface)
    display_absence_summary = _safe_mapping(display_absence_summary)
    for gate_name in ("reader", "grounding", "template_echo", "template", "display", "visible_surface_acceptance"):
        reasons.extend(_gate_reasons(gate_results, gate_name))
    reasons.extend(_as_list(runtime_surface.get("runtime_surface_pre_return_gate_rejection_reasons")))
    reasons.extend(_as_list(display_absence_summary.get("reason_codes")))
    if _clean(gate_failure_stage):
        reasons.append(_clean(gate_failure_stage))
    reasons = _dedupe(reasons)

    if "emlis_ai_timeout_or_error" in set(reasons) or "emlis_ai_reply_timeout" in set(reasons):
        return CANONICAL_BACKEND_EXCEPTION_OR_TIMEOUT

    low_info_contract = _safe_mapping(low_information_public_repair_contract)
    reply_kind = _clean(observation_reply_kind)
    if reply_kind == "low_information_observation" or low_info_contract:
        final_status = _clean(low_info_contract.get("final_observation_status"))
        applied = bool(low_info_contract.get("repair_route_allowed") and final_status == "passed")
        if status == "passed" or applied:
            return CANONICAL_LOW_INFORMATION_PUBLIC_REPAIR_APPLIED
        return CANONICAL_LOW_INFORMATION_PUBLIC_REPAIR_FAILED

    if status == "passed":
        return CANONICAL_CANDIDATE_GENERATED_DISPLAY_PASSED

    if stage_text in _PRE_CONNECTION_STAGES:
        if stage_text in {"safety"} or status == "safety_blocked" or _reason_matches(reasons, ("safety",)):
            return CANONICAL_PRE_CONNECTION_BLOCKED_SAFETY
        if stage_text == "scope" or _reason_matches(reasons, ("scope", "out_of_scope")):
            return CANONICAL_PRE_CONNECTION_BLOCKED_SCOPE
        if stage_text == "ap0" or _reason_matches(reasons, ("ap0",)):
            return CANONICAL_PRE_CONNECTION_BLOCKED_AP0
        if stage_text == "rollout" or _reason_matches(reasons, ("rollout",)):
            return CANONICAL_PRE_CONNECTION_BLOCKED_ROLLOUT
        return CANONICAL_PRE_CONNECTION_BLOCKED_FLAG

    connection = _clean_lower(connection_status)
    if connection.startswith("blocked_"):
        if "safety" in connection:
            return CANONICAL_PRE_CONNECTION_BLOCKED_SAFETY
        if "scope" in connection:
            return CANONICAL_PRE_CONNECTION_BLOCKED_SCOPE
        if "ap0" in connection:
            return CANONICAL_PRE_CONNECTION_BLOCKED_AP0
        if "rollout" in connection:
            return CANONICAL_PRE_CONNECTION_BLOCKED_ROLLOUT
        return CANONICAL_PRE_CONNECTION_BLOCKED_FLAG

    generated_flag = bool(candidate_generated) if candidate_generated is not None else _clean(composer_status) == "generated"
    if not generated_flag:
        return CANONICAL_CANDIDATE_NOT_GENERATED

    if _gate_passed(gate_results, "reader") is False:
        return CANONICAL_CANDIDATE_GENERATED_BUT_READER_REJECTED
    if _gate_passed(gate_results, "grounding") is False:
        return CANONICAL_CANDIDATE_GENERATED_BUT_GROUNDING_REJECTED
    if _gate_passed(gate_results, "template_echo", "template") is False:
        return CANONICAL_CANDIDATE_GENERATED_BUT_TEMPLATE_REJECTED

    if _reason_matches(reasons, _META_BOUNDARY_REASON_FRAGMENTS):
        return CANONICAL_CANDIDATE_BLOCKED_META_BOUNDARY
    if _reason_matches(reasons, _TWO_STAGE_REASON_FRAGMENTS):
        return CANONICAL_CANDIDATE_BLOCKED_TWO_STAGE_CONTRACT
    if (
        _reason_matches(reasons, _SURFACE_GRAMMAR_REASON_FRAGMENTS)
        or bool(display_absence_summary.get("candidate_blocked_surface_grammar"))
        or bool(display_absence_summary.get("candidate_blocked_koto_splice"))
        or bool(display_absence_summary.get("candidate_blocked_relation_skeleton"))
        or (bool(runtime_surface.get("runtime_surface_pre_return_gate_evaluated")) and not bool(runtime_surface.get("runtime_surface_pre_return_gate_passed")))
    ):
        return CANONICAL_CANDIDATE_BLOCKED_SURFACE_GRAMMAR

    if _gate_passed(gate_results, "display") is False or comment_text_allowed is False or status in {"rejected", "unavailable"}:
        return CANONICAL_CANDIDATE_GENERATED_BUT_DISPLAY_REJECTED

    return CANONICAL_UNCLASSIFIED_NON_DISPLAY


def build_diagnostic_failure_taxonomy_meta(
    *,
    canonical_classification: Any = "",
    classification: Any = "",
    observation_status: Any = "",
    stage: Any = "",
    primary_reason: Any = "",
    secondary_reasons: Any = None,
    rejection_reasons: Any = None,
    display_rejection_reasons: Any = None,
    gate_results: Mapping[str, Any] | None = None,
    gate_failure_stage: Any = "",
    runtime_surface: Mapping[str, Any] | None = None,
    display_absence_summary: Mapping[str, Any] | None = None,
    composer_status: Any = "",
    candidate_generated: Any = None,
    comment_text_allowed: Any = None,
    comment_text_present: Any = None,
    comment_text_length: Any = None,
    observation_reply_kind: Any = "",
    low_information_public_repair_contract: Mapping[str, Any] | None = None,
    connection_status: Any = "",
    **_: Any,
) -> dict[str, Any]:
    runtime = _safe_mapping(runtime_surface)
    display_absence = _safe_mapping(display_absence_summary)
    merged_rejection_reasons = _dedupe(
        [
            *_as_list(rejection_reasons),
            *_as_list(runtime.get("rejection_reasons")),
            *_as_list(runtime.get("runtime_surface_pre_return_gate_rejection_reasons")),
            *_as_list(display_absence.get("reason_codes")),
        ]
    )
    merged_secondary_reasons = _dedupe(
        [
            *_as_list(secondary_reasons),
            *_as_list(display_absence.get("secondary_reasons")),
            _clean(gate_failure_stage),
        ]
    )
    seed = _clean(canonical_classification) or canonicalize_legacy_diagnostic_classification(classification)
    canonical = seed if seed in _CANONICAL_CLASSES else ""
    if not canonical:
        canonical = classify_diagnostic_failure(
            observation_status=observation_status,
            stage=stage,
            primary_reason=primary_reason,
            secondary_reasons=merged_secondary_reasons,
            rejection_reasons=merged_rejection_reasons,
            display_rejection_reasons=display_rejection_reasons,
            gate_results=gate_results,
            composer_status=composer_status,
            candidate_generated=candidate_generated,
            comment_text_allowed=comment_text_allowed,
            comment_text_present=comment_text_present if comment_text_present is not None else bool(int(comment_text_length or 0)),
            observation_reply_kind=observation_reply_kind,
            low_information_public_repair_contract=low_information_public_repair_contract,
            connection_status=connection_status,
        )
    aliases = _legacy_aliases_for(canonical)
    public_contract = {
        "raw_input_included": False,
        "raw_text_included": False,
        "generated_candidate_text_included": False,
        "comment_text_body_included": False,
        "public_response_key_added": False,
        "rn_visible_contract_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "template_gate_relaxed": False,
    }
    meta = {
        "schema_version": DIAGNOSTIC_FAILURE_TAXONOMY_SCHEMA_VERSION,
        "source_phase": DIAGNOSTIC_FAILURE_TAXONOMY_SOURCE_PHASE,
        "canonical_classification": canonical,
        "classification": canonical,
        "legacy_classification_aliases": aliases,
        "legacy_alias_count": len(aliases),
        "public_safe": True,
        **public_contract,
        "public_contract": dict(public_contract),
    }
    assert_diagnostic_failure_taxonomy_meta_only(meta)
    return meta


def attach_diagnostic_failure_taxonomy_meta(summary_meta: Mapping[str, Any] | None) -> dict[str, Any]:
    summary = dict(summary_meta or {})
    gate_results = _safe_mapping(summary.get("gate_results"))
    taxonomy = build_diagnostic_failure_taxonomy_meta(
        observation_status=summary.get("observation_status"),
        stage=summary.get("stage"),
        primary_reason=summary.get("primary_reason"),
        secondary_reasons=summary.get("secondary_reasons"),
        rejection_reasons=summary.get("rejection_reasons") or summary.get("gate_rejection_reasons"),
        display_rejection_reasons=summary.get("display_rejection_reasons"),
        gate_results=gate_results,
        composer_status=summary.get("composer_status"),
        candidate_generated=(
            summary.get("candidate_generated")
            if "candidate_generated" in summary
            else summary.get("complete_candidate_generated")
            if "complete_candidate_generated" in summary
            else summary.get("candidate_generated_before_display_gate")
        ),
        comment_text_allowed=summary.get("comment_text_allowed"),
        comment_text_present=summary.get("public_comment_text_present"),
        observation_reply_kind=summary.get("observation_reply_kind"),
        low_information_public_repair_contract=(
            summary.get("low_information_public_repair_contract")
            if isinstance(summary.get("low_information_public_repair_contract"), Mapping)
            else summary.get("phase18_low_information_public_repair_contract")
            if isinstance(summary.get("phase18_low_information_public_repair_contract"), Mapping)
            else {}
        ),
        connection_status=(
            _safe_mapping(summary.get("registry_resolution")).get("connection_status")
            or _safe_mapping(summary.get("composer_client_resolution")).get("connection_status")
        ),
    )
    summary["diagnostic_failure_taxonomy"] = taxonomy
    summary["diagnostic_failure_taxonomy_schema_version"] = taxonomy["schema_version"]
    summary["diagnostic_classification"] = taxonomy["canonical_classification"]
    summary["canonical_classification"] = taxonomy["canonical_classification"]
    summary["classification"] = taxonomy["canonical_classification"]
    summary["legacy_classification_aliases"] = list(taxonomy["legacy_classification_aliases"])
    summary["diagnostic_taxonomy_public_safe"] = True
    summary["diagnostic_taxonomy_comment_text_body_included"] = False
    summary["diagnostic_taxonomy_raw_input_included"] = False
    return summary


def assert_diagnostic_failure_taxonomy_meta_only(value: Any, *, source: str = "diagnostic_failure_taxonomy") -> None:
    if not isinstance(value, Mapping):
        raise ValueError(f"{source} must be a mapping")
    _assert_no_forbidden_keys(value, source=source)
    _assert_no_true_contract_flags(value, source=source)


def _assert_no_forbidden_keys(value: Any, *, source: str) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if _clean(key) in _TEXT_PAYLOAD_KEYS:
                raise ValueError(f"{source} must not include body/raw key: {key}")
            _assert_no_forbidden_keys(child, source=source)
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            _assert_no_forbidden_keys(item, source=source)


def _assert_no_true_contract_flags(value: Any, *, source: str) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if _clean(key) in _CONTRACT_TRUE_FLAGS and child is True:
                raise ValueError(f"{source} violates public/gate contract: {key}=true")
            _assert_no_true_contract_flags(child, source=source)
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            _assert_no_true_contract_flags(item, source=source)


def assert_diagnostic_failure_taxonomy_meta(value: Any, *, source: str = "diagnostic_failure_taxonomy") -> None:
    assert_diagnostic_failure_taxonomy_meta_only(value, source=source)


__all__ = [
    "DIAGNOSTIC_FAILURE_TAXONOMY_SCHEMA_VERSION",
    "DIAGNOSTIC_FAILURE_TAXONOMY_SOURCE_PHASE",
    "CLASS_CANDIDATE_NOT_GENERATED",
    "CLASS_CANDIDATE_GENERATED_DISPLAY_PASSED",
    "CLASS_CANDIDATE_GENERATED_BUT_READER_REJECTED",
    "CLASS_CANDIDATE_GENERATED_BUT_GROUNDING_REJECTED",
    "CLASS_CANDIDATE_GENERATED_BUT_TEMPLATE_REJECTED",
    "CLASS_CANDIDATE_GENERATED_BUT_DISPLAY_REJECTED",
    "CLASS_CANDIDATE_BLOCKED_SURFACE_GRAMMAR",
    "CLASS_CANDIDATE_BLOCKED_TWO_STAGE_CONTRACT",
    "CLASS_CANDIDATE_BLOCKED_META_BOUNDARY",
    "build_diagnostic_failure_taxonomy_meta",
    "attach_diagnostic_failure_taxonomy_meta",
    "canonicalize_legacy_diagnostic_classification",
    "classify_diagnostic_failure",
    "assert_diagnostic_failure_taxonomy_meta",
    "assert_diagnostic_failure_taxonomy_meta_only",
]
