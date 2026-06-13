# -*- coding: utf-8 -*-
"""P7-0 body-free P5/P6 handoff intake.

This module receives the existing P5/P6 R9 handoff lock and normalizes it into
P7's first internal material.  It intentionally starts ``p7_readiness.ready`` and
``release_allowed`` as false and carries P5/P6 HOLDs forward instead of treating
runtime connection as product readiness.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Final

from emlis_ai_p5_p6_split_test_matrix import (
    P5_P6_HANDOFF_LOCK_SCHEMA_VERSION,
    build_p5_p6_handoff_lock,
)
from emlis_ai_p7_contracts import (
    P7_HANDOFF_SUMMARY_SCHEMA_VERSION,
    P7_INITIAL_HOLD_IDS,
    P7_INITIAL_RED_IDS,
    assert_false_markers,
    assert_p7_no_body_payload_or_contract_mutation,
    body_free_flags,
    clean_identifier,
    dedupe_identifiers,
    public_contract_flags,
    safe_mapping,
)

P7_HANDOFF_SCOPE: Final = "P5_P6_to_P7_body_free_handoff"

_P7_READINESS_DEFAULT_REASONS: Final[tuple[str, ...]] = (
    "p7_red_ledger_required",
    "positive_recovery_red_open",
    "product_quality_connection_timeout_open",
    "release_decision_not_allowed",
)

_P7_READINESS_ALLOWED_REASONS: Final[frozenset[str]] = frozenset(
    {
        "p7_red_ledger_required",
        "p5_human_qa_hold",
        "p6_limited_surface_hold",
        "positive_recovery_red_open",
        "product_quality_connection_timeout_open",
        "release_decision_not_allowed",
        "source_handoff_not_runtime_evaluated",
    }
)


def _bool(value: Any) -> bool:
    return value is True


def _source_handoff(source_handoff: Mapping[str, Any] | None) -> dict[str, Any]:
    data = safe_mapping(source_handoff)
    if not data:
        return build_p5_p6_handoff_lock()
    return data


def _normalize_visible_family(value: Any) -> str:
    family = clean_identifier(value, default="none")
    return family if family == "structure_question" else "none"


def _p5_status(p5: Mapping[str, Any]) -> str:
    if _bool(p5.get("runtime_evaluated")):
        return "runtime_connected_hold"
    reasons = set(dedupe_identifiers(p5.get("visible_not_applied_reason_codes")))
    if any("blocked" in reason or "block" in reason for reason in reasons):
        return "blocked"
    return "not_connected"


def _p6_status(p6: Mapping[str, Any], *, visible_family: str) -> str:
    if _bool(p6.get("visible_applied")) and visible_family == "structure_question":
        return "limited_surface_connected_hold"
    if _bool(p6.get("runtime_evaluated")):
        return "meta_only"
    reasons = set(dedupe_identifiers(p6.get("visible_not_applied_reason_codes")))
    if any("blocked" in reason or "block" in reason for reason in reasons):
        return "blocked"
    return "unknown"


def _normalize_reason_codes(*, p5: Mapping[str, Any], p6: Mapping[str, Any]) -> list[str]:
    reasons = list(_P7_READINESS_DEFAULT_REASONS)
    if p5.get("human_qa_completed") is not True:
        reasons.append("p5_human_qa_hold")
    reasons.append("p6_limited_surface_hold")
    if p5.get("runtime_evaluated") is not True or p6.get("runtime_evaluated") is not True:
        reasons.append("source_handoff_not_runtime_evaluated")
    deduped = dedupe_identifiers(reasons, limit=12)
    return [reason for reason in deduped if reason in _P7_READINESS_ALLOWED_REASONS]


def build_p7_handoff_summary(
    *,
    source_handoff: Mapping[str, Any] | None = None,
    p5_runtime_bridge_summary: Mapping[str, Any] | None = None,
    p6_runtime_bridge_summary: Mapping[str, Any] | None = None,
    red_refs: list[str] | tuple[str, ...] | None = None,
    hold_refs: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Build P7HandoffSummaryV1 from a P5/P6 handoff lock or runtime summaries."""

    if source_handoff is None and (p5_runtime_bridge_summary is not None or p6_runtime_bridge_summary is not None):
        assert_p7_no_body_payload_or_contract_mutation(
            p5_runtime_bridge_summary or {}, source="p5_runtime_bridge_summary"
        )
        assert_p7_no_body_payload_or_contract_mutation(
            p6_runtime_bridge_summary or {}, source="p6_runtime_bridge_summary"
        )
        source = build_p5_p6_handoff_lock(
            p5_runtime_bridge_summary=p5_runtime_bridge_summary,
            p6_runtime_bridge_summary=p6_runtime_bridge_summary,
        )
    else:
        source = _source_handoff(source_handoff)

    assert_p7_no_body_payload_or_contract_mutation(source, source="p7_source_handoff")

    p5 = safe_mapping(source.get("p5_handoff"))
    p6 = safe_mapping(source.get("p6_handoff"))
    visible_family = _normalize_visible_family(p6.get("visible_family"))

    summary = {
        "schema_version": P7_HANDOFF_SUMMARY_SCHEMA_VERSION,
        "source_handoff_schema_version": clean_identifier(
            source.get("schema_version"), default=P5_P6_HANDOFF_LOCK_SCHEMA_VERSION
        ),
        "scope": P7_HANDOFF_SCOPE,
        "p5": {
            "runtime_evaluated": _bool(p5.get("runtime_evaluated")),
            "visible_applied": _bool(p5.get("visible_applied")),
            "product_quality_confirmed": _bool(p5.get("product_quality_confirmed")),
            "human_qa_completed": _bool(p5.get("human_qa_completed")),
            "history_connection_naturalness_confirmed": _bool(
                p5.get("history_connection_naturalness_confirmed")
            ),
            "creepy_absence_confirmed": _bool(p5.get("creepy_absence_confirmed")),
            "wants_more_input_confirmed": _bool(p5.get("wants_more_input_confirmed")),
            "status": _p5_status(p5),
            "release_allowed": False,
        },
        "p6": {
            "runtime_evaluated": _bool(p6.get("runtime_evaluated")),
            "visible_applied": _bool(p6.get("visible_applied")) and visible_family == "structure_question",
            "visible_family": visible_family,
            "visible_only_for_structure_question": True,
            "long_meaning_arc_visible_allowed": False,
            "self_understanding_follow_visible_allowed": False,
            "product_quality_review_ratings_only": p6.get("product_quality_review_ratings_only") is not False,
            "status": _p6_status(p6, visible_family=visible_family),
            "release_allowed": False,
        },
        "p7_readiness": {
            "ready": False,
            "reason_codes": _normalize_reason_codes(p5=p5, p6=p6),
        },
        "red_refs": dedupe_identifiers(red_refs or P7_INITIAL_RED_IDS, limit=12),
        "hold_refs": dedupe_identifiers(hold_refs or P7_INITIAL_HOLD_IDS, limit=12),
        "public_contract": public_contract_flags(),
        "body_free": body_free_flags(include_history=True),
        "release_allowed": False,
    }
    assert_p7_handoff_summary_contract(summary)
    return summary


def normalize_p7_handoff_summary(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Compatibility alias for callers that name this step as normalization."""

    return build_p7_handoff_summary(*args, **kwargs)


def assert_p7_handoff_summary_contract(summary: Mapping[str, Any]) -> bool:
    data = safe_mapping(summary)
    if data.get("schema_version") != P7_HANDOFF_SUMMARY_SCHEMA_VERSION:
        raise ValueError("unexpected P7 handoff summary schema_version")
    if data.get("scope") != P7_HANDOFF_SCOPE:
        raise ValueError("unexpected P7 handoff summary scope")
    if data.get("release_allowed") is not False:
        raise ValueError("P7 handoff summary must not allow release")
    p7_readiness = safe_mapping(data.get("p7_readiness"))
    if p7_readiness.get("ready") is not False:
        raise ValueError("P7 handoff summary must start with p7_readiness.ready false")
    if "release_decision_not_allowed" not in dedupe_identifiers(p7_readiness.get("reason_codes")):
        raise ValueError("P7 handoff summary must keep release-decision separation as a reason")
    p5 = safe_mapping(data.get("p5"))
    p6 = safe_mapping(data.get("p6"))
    if not p5 or not p6:
        raise ValueError("P7 handoff summary must include P5 and P6 sections")
    if p5.get("release_allowed") is not False or p6.get("release_allowed") is not False:
        raise ValueError("P5/P6 handoff sections must keep release_allowed false")
    if p6.get("visible_family") not in {"structure_question", "none"}:
        raise ValueError("P6 visible family must remain structure_question-only or none")
    if p6.get("long_meaning_arc_visible_allowed") is not False:
        raise ValueError("P7-0 must not open long_meaning_arc visible expansion")
    if p6.get("self_understanding_follow_visible_allowed") is not False:
        raise ValueError("P7-0 must not open self_understanding_follow visible expansion")
    if not set(P7_INITIAL_RED_IDS).issubset(set(dedupe_identifiers(data.get("red_refs")))):
        raise ValueError("P7 handoff summary must carry initial red references")
    if not {"P7-HOLD-001", "P7-HOLD-002"}.issubset(set(dedupe_identifiers(data.get("hold_refs")))):
        raise ValueError("P7 handoff summary must carry P5/P6 HOLD references")
    assert_false_markers(safe_mapping(data.get("public_contract")), source="p7_handoff.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free")), source="p7_handoff.body_free")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_handoff_summary")
    return True
