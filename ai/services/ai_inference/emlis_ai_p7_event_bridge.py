# -*- coding: utf-8 -*-
"""P7-4 ProductQualityEventV1 bridge and body-free scorecard row.

This bridge reuses the existing ProductQualityEventV1 without replacing it.  It
normalizes the existing event together with the P7 handoff summary and P7 red
ledger into a P7ScorecardRowV1 material row.  The row is intentionally
body-free, ratings-required, and release-closed: it carries identifiers, display
booleans, counts, flags, red/HOLD/blocker ids, and never carries raw input,
comment_text body, candidate body, surface body, reviewer free text, or public
contract mutations.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final

from emlis_ai_p7_contracts import (
    P7_INITIAL_HOLD_IDS,
    P7_INITIAL_RED_IDS,
    P7_PHASE,
    assert_false_markers,
    assert_p7_no_body_payload_or_contract_mutation,
    body_free_flags,
    clean_identifier,
    dedupe_identifiers,
    public_contract_flags,
    safe_mapping,
)
from emlis_ai_p7_handoff_normalizer import (
    assert_p7_handoff_summary_contract,
    build_p7_handoff_summary,
)
from emlis_ai_p7_red_ledger import assert_p7_red_ledger_contract, build_p7_red_ledger
from emlis_ai_product_quality_measurement_event import (
    PRODUCT_QUALITY_EVENT_SCHEMA_VERSION,
    assert_product_quality_measurement_event_meta_only,
    product_quality_event_to_scorecard_row,
)

P7_EVENT_BRIDGE_STEP: Final = "P7-4_ProductQualityEventBridgeScorecardRow_20260612"
P7_SCORECARD_ROW_SCHEMA_VERSION: Final = "cocolon.emlis.p7.body_free_scorecard_row.v1"
P7_SCORECARD_ROW_SOURCE: Final = "ProductQualityEventV1_P7HandoffSummaryV1_P7RedLedgerV1"

P7_ALLOWED_SCORECARD_OBSERVATION_STATUSES: Final[frozenset[str]] = frozenset(
    {"passed", "rejected", "unavailable", "unknown"}
)
P7_ALLOWED_SOURCE_TYPES: Final[frozenset[str]] = frozenset(
    {"fixture_case", "local_runner_case", "manual_internal_case", "sequence_case"}
)
P7_ALLOWED_P5_STATUSES: Final[frozenset[str]] = frozenset(
    {"not_eligible", "applied_hold", "blocked", "review_required"}
)
P7_ALLOWED_P6_STATUSES: Final[frozenset[str]] = frozenset(
    {"not_eligible", "limited_surface_applied_hold", "meta_only", "blocked", "review_required"}
)
P7_ALLOWED_VISIBLE_FAMILIES: Final[frozenset[str]] = frozenset({"structure_question", "none"})
P7_P6_VISIBLE_BOUNDARY_SCHEMA_VERSION: Final = "cocolon.emlis.p7.p6_family_boundary.v1"
P7_P6_VISIBLE_ALLOWED_FAMILIES: Final[tuple[str, ...]] = ("structure_question",)
P7_P6_META_ONLY_FAMILIES: Final[tuple[str, ...]] = (
    "long_meaning_arc",
    "self_understanding_follow",
)
P7_P6_NO_CONNECT_FAMILIES: Final[tuple[str, ...]] = (
    "daily_unpleasant",
    "daily_positive",
    "positive_only",
    "low_information_short",
    "low_information",
    "low_info",
    "safety_triage_required",
    "safety_adjacent",
    "self_denial",
    "anger_or_boundary",
    "limited_grounding",
)

P7_RATING_REQUIRED_DIMENSIONS: Final[tuple[str, ...]] = (
    "read_feeling",
    "naturalness",
    "non_template",
    "follow_depth",
    "history_connection_naturalness",
    "creepy_absence",
    "wants_more_input_or_accumulation",
    "structure_insight_candidate_quality",
    "overclaim_absence",
    "self_blame_non_amplification",
    "mirror_only_absence",
)

P7_SCORECARD_REQUIRED_TOP_LEVEL_KEYS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "row_id",
    "run_id",
    "source",
    "family",
    "sequence",
    "display_contract",
    "p5",
    "p6",
    "quality_flags",
    "ratings",
    "red_refs",
    "hold_refs",
    "blocker_refs",
    "blocker_ids",
    "public_contract",
    "body_free_markers",
    "source_event_schema_version",
    "handoff_schema_version",
    "red_ledger_schema_version",
    "body_free",
    "release_allowed",
)

_P7_FAMILY_ALIASES: Final[dict[str, str]] = {
    "low_information": "low_information_short",
    "low_info": "low_information_short",
    "low_info_short": "low_information_short",
    "daily_negative": "daily_unpleasant",
    "daily_unpleasantness": "daily_unpleasant",
    "daily_good": "daily_positive",
    "positive_only": "daily_positive",
    "positive": "daily_positive",
    "self_deny": "self_denial",
    "uncertainty": "uncertainty_support",
    "mixed_emotion": "limited_grounding",
    "relationship_boundary": "anger_or_boundary",
    "relationship_boundary_issue": "anger_or_boundary",
    "recovery": "relationship_gratitude_recovery",
    "relationship_recovery": "relationship_gratitude_recovery",
    "future_intention": "change_future_intention",
    "source_unavailable": "source_unavailable_high_information",
    "self_understanding_follow": "long_meaning_arc",
    "input_self_report_only_failure": "limited_grounding",
    "structure": "structure_question",
    "structure_insight": "structure_question",
}

P7_SCORECARD_FAMILIES: Final[tuple[str, ...]] = (
    "low_information_short",
    "limited_grounding",
    "daily_unpleasant",
    "daily_positive",
    "self_denial",
    "anger_or_boundary",
    "uncertainty_support",
    "standard_state_answer",
    "structure_question",
    "long_meaning_arc",
    "relationship_gratitude_recovery",
    "change_future_intention",
    "source_unavailable_high_information",
    "history_line_eligible",
    "unknown",
)


def normalize_p7_scorecard_family(value: Any) -> str:
    text = clean_identifier(value, default="unknown", max_length=120).lower().replace("-", "_").replace(" ", "_")
    normalized = _P7_FAMILY_ALIASES.get(text, text)
    return normalized if normalized in P7_SCORECARD_FAMILIES else "unknown"


def _scorecard_source_type(value: Any) -> str:
    text = clean_identifier(value, default="manual_internal_case", max_length=80)
    aliases = {
        "fixture_family": "fixture_case",
        "regression_fixture": "fixture_case",
        "local_jsonl": "local_runner_case",
        "local_runner": "local_runner_case",
        "manual_case": "manual_internal_case",
    }
    normalized = aliases.get(text, text)
    return normalized if normalized in P7_ALLOWED_SOURCE_TYPES else "manual_internal_case"


def _scorecard_observation_status(value: Any) -> str:
    text = clean_identifier(value, default="unknown", max_length=40)
    if text == "safety_blocked":
        return "rejected"
    return text if text in P7_ALLOWED_SCORECARD_OBSERVATION_STATUSES else "unknown"


def _p6_family_boundary_raw_family(value: Any) -> str:
    return clean_identifier(value, default="unknown", max_length=120).lower().replace("-", "_").replace(" ", "_")


def p7_p6_family_boundary_for_family(
    family: Any,
    *,
    runtime_evaluated: bool = False,
    visible_applied: bool = False,
) -> dict[str, Any]:
    """Return the R9 family boundary for P6 visible expansion validation.

    The policy is body-free: it contains family codes, booleans, HOLD refs, and
    schema/version markers only.  P7 does not expand visible Structure Insight
    beyond ``structure_question`` here.
    """

    raw_family = _p6_family_boundary_raw_family(family)
    normalized_family = normalize_p7_scorecard_family(raw_family)
    visible_allowed = normalized_family in P7_P6_VISIBLE_ALLOWED_FAMILIES
    meta_only = raw_family in P7_P6_META_ONLY_FAMILIES or normalized_family in {"long_meaning_arc"}
    no_connect = raw_family in P7_P6_NO_CONNECT_FAMILIES or normalized_family in {
        "daily_unpleasant",
        "daily_positive",
        "low_information_short",
        "self_denial",
        "anger_or_boundary",
        "limited_grounding",
    }
    visible_applied_allowed = bool(visible_applied and visible_allowed)
    violation = bool(visible_applied and not visible_allowed)
    if visible_applied_allowed:
        family_status = "visible_allowed"
        p6_row_status = "limited_surface_applied_hold"
        visible_family = "structure_question"
    elif meta_only:
        family_status = "meta_only"
        p6_row_status = "meta_only" if runtime_evaluated else "not_eligible"
        visible_family = "none"
    elif no_connect:
        family_status = "no_connect"
        p6_row_status = "meta_only" if runtime_evaluated else "not_eligible"
        visible_family = "none"
    else:
        family_status = "not_eligible"
        p6_row_status = "not_eligible"
        visible_family = "none"
    policy = {
        "schema_version": P7_P6_VISIBLE_BOUNDARY_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": "R9_P6VisibleExpansionBoundaryValidation_20260613",
        "family": raw_family,
        "normalized_family": normalized_family,
        "family_status": family_status,
        "p6_row_status": p6_row_status,
        "visible_allowed": visible_allowed,
        "visible_applied_allowed": visible_applied_allowed,
        "visible_applied_violation": violation,
        "visible_family": visible_family,
        "meta_only_family": meta_only,
        "no_connect_family": no_connect,
        "visible_allowed_families": list(P7_P6_VISIBLE_ALLOWED_FAMILIES),
        "meta_only_families": list(P7_P6_META_ONLY_FAMILIES),
        "no_connect_families": list(P7_P6_NO_CONNECT_FAMILIES),
        "visible_expansion_allowed": False,
        "visible_expansion_requires_future_design": True,
        "p7_holds": ["P7-HOLD-002"],
        "hold_refs": ["P7-HOLD-002"],
        "release_allowed": False,
        "public_contract": public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True),
        "raw_input_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "reviewer_free_text_included": False,
        "body_free": True,
    }
    assert_p7_p6_family_boundary_contract(policy)
    return policy


def _to_int(value: Any, *, default: int = 0, minimum: int = 0, maximum: int = 800) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return min(max(number, minimum), maximum)


def _to_float_score(value: Any) -> float | None:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return None
    if score < 0 or score > 1:
        return None
    return round(score, 6)


def _source_from_product_quality_event(event: Mapping[str, Any], *, source_override: Mapping[str, Any] | None = None) -> dict[str, Any]:
    source = safe_mapping(event.get("source"))
    if source_override is not None:
        source.update(safe_mapping(source_override))
    return {
        "source_type": _scorecard_source_type(source.get("source_type")),
        "source_case_id": clean_identifier(source.get("source_case_id"), default="manual_case", max_length=96),
        "source_revision": clean_identifier(source.get("source_revision"), default="", max_length=96),
    }


def normalize_p7_sequence(value: Mapping[str, Any] | None = None, *, family: str = "unknown") -> dict[str, Any]:
    source = safe_mapping(value)
    sequence_length = _to_int(source.get("sequence_length"), default=1, minimum=1, maximum=30)
    sequence_index = _to_int(source.get("sequence_index"), default=1, minimum=1, maximum=sequence_length)
    sequence_id = clean_identifier(
        source.get("sequence_id"),
        default=("sequence_1" if sequence_length == 1 else f"sequence_{sequence_length}"),
        max_length=96,
    )
    history_line_eligible = bool(
        source.get("history_line_eligible") is True
        or (sequence_length > 1 and family in {"history_line_eligible", "long_meaning_arc", "relationship_gratitude_recovery", "change_future_intention"})
    )
    return {
        "sequence_id": sequence_id,
        "sequence_index": sequence_index,
        "sequence_length": sequence_length,
        "history_line_eligible": history_line_eligible,
        "row_kind": "single_input" if sequence_length == 1 else "sequence",
    }


def _ledger_refs(red_ledger: Mapping[str, Any], *, status: str) -> list[str]:
    entries = red_ledger.get("entries", [])
    refs: list[str] = []
    if isinstance(entries, Sequence) and not isinstance(entries, (str, bytes, bytearray)):
        for entry in entries:
            item = safe_mapping(entry)
            if clean_identifier(item.get("status"), max_length=32) == status:
                refs.append(clean_identifier(item.get("id"), max_length=40))
    return dedupe_identifiers(refs, limit=40)


def _blocker_refs(product_scorecard_row: Mapping[str, Any], red_ledger: Mapping[str, Any]) -> list[str]:
    entries = red_ledger.get("entries", [])
    ledger_blockers: list[str] = []
    if isinstance(entries, Sequence) and not isinstance(entries, (str, bytes, bytearray)):
        for entry in entries:
            item = safe_mapping(entry)
            if item.get("release_blocker") is True:
                ledger_blockers.append(clean_identifier(item.get("id"), max_length=40))
    return dedupe_identifiers(
        [*dedupe_identifiers(product_scorecard_row.get("blockers"), limit=40), *ledger_blockers],
        limit=80,
        max_length=160,
    )


def _p5_section(handoff_summary: Mapping[str, Any]) -> dict[str, Any]:
    p5 = safe_mapping(handoff_summary.get("p5"))
    status = clean_identifier(p5.get("status"), max_length=80)
    if p5.get("visible_applied") is True:
        row_status = "applied_hold" if p5.get("human_qa_completed") is not True else "review_required"
    elif status == "blocked":
        row_status = "blocked"
    elif p5.get("runtime_evaluated") is True:
        row_status = "review_required"
    else:
        row_status = "not_eligible"
    return {
        "eligible": bool(p5.get("runtime_evaluated")),
        "visible_applied": bool(p5.get("visible_applied")),
        "human_qa_completed": bool(p5.get("human_qa_completed")),
        "status": row_status,
    }


def _p6_section(handoff_summary: Mapping[str, Any], *, family: str) -> dict[str, Any]:
    p6 = safe_mapping(handoff_summary.get("p6"))
    runtime_evaluated = p6.get("runtime_evaluated") is True
    requested_visible = p6.get("visible_applied") is True
    boundary = p7_p6_family_boundary_for_family(
        family,
        runtime_evaluated=runtime_evaluated,
        visible_applied=requested_visible,
    )
    if clean_identifier(p6.get("status"), max_length=80) == "blocked" and not boundary.get("visible_applied_allowed"):
        row_status = "blocked"
    else:
        row_status = clean_identifier(boundary.get("p6_row_status"), default="not_eligible", max_length=80)
    visible_applied = bool(boundary.get("visible_applied_allowed"))
    return {
        "eligible": bool(runtime_evaluated and boundary.get("visible_allowed") is True),
        "visible_applied": visible_applied,
        "visible_family": clean_identifier(boundary.get("visible_family"), default="none", max_length=80),
        "status": row_status,
        "family_boundary_status": clean_identifier(boundary.get("family_status"), default="not_eligible", max_length=80),
        "visible_expansion_allowed": False,
        "visible_expansion_requires_future_design": True,
        "meta_only_family": boundary.get("meta_only_family") is True,
        "no_connect_family": boundary.get("no_connect_family") is True,
        "visible_applied_violation": False,
        "visible_request_suppressed": bool(requested_visible and not boundary.get("visible_allowed")),
        "p7_hold_refs": ["P7-HOLD-002"],
    }


def _quality_flags(product_scorecard_row: Mapping[str, Any], *, overrides: Mapping[str, Any] | None = None) -> dict[str, bool]:
    override = safe_mapping(overrides)
    blockers = set(dedupe_identifiers(product_scorecard_row.get("blockers"), limit=80))

    def flag(name: str, default: bool) -> bool:
        return bool(override.get(name)) if name in override else bool(default)

    template_major = _to_int(product_scorecard_row.get("template_major_count"), default=0) > 0
    unsafe_claim = bool(product_scorecard_row.get("unsafe_insight_surface_detected")) or _to_int(
        product_scorecard_row.get("safety_major_count"), default=0
    ) > 0
    return {
        "mirror_only_detected": flag("mirror_only_detected", "mirror_only_detected" in blockers),
        "template_major_detected": flag("template_major_detected", template_major or "template_major_detected" in blockers),
        "unsafe_claim_detected": flag("unsafe_claim_detected", unsafe_claim or "unsafe_insight_surface_detected" in blockers),
        "overclaim_risk_detected": flag("overclaim_risk_detected", "overclaim_risk_detected" in blockers),
        "creepy_risk_detected": flag("creepy_risk_detected", "creepy_risk_detected" in blockers),
    }


def normalize_p7_ratings(value: Mapping[str, Any] | None = None) -> dict[str, Any]:
    source = safe_mapping(value)
    scores_source = safe_mapping(source.get("dimension_scores"))
    dimension_scores: dict[str, float] = {}
    for dimension in P7_RATING_REQUIRED_DIMENSIONS:
        score = _to_float_score(scores_source.get(dimension))
        if score is not None:
            dimension_scores[dimension] = score
    explicit_missing = dedupe_identifiers(source.get("missing_dimensions"), limit=40)
    missing = explicit_missing or [dimension for dimension in P7_RATING_REQUIRED_DIMENSIONS if dimension not in dimension_scores]
    blind_completed = bool(source.get("blind_qa_completed") is True and not missing)
    return {
        "blind_qa_required": source.get("blind_qa_required") is not False,
        "blind_qa_completed": blind_completed,
        "rating_required": not blind_completed,
        "dimension_scores": dimension_scores,
        "missing_dimensions": dedupe_identifiers(missing, limit=40),
        "rating_required_dimensions": list(P7_RATING_REQUIRED_DIMENSIONS),
    }


def build_p7_scorecard_row(
    *,
    product_quality_event: Mapping[str, Any],
    p7_handoff_summary: Mapping[str, Any] | None = None,
    p7_red_ledger: Mapping[str, Any] | None = None,
    sequence: Mapping[str, Any] | None = None,
    source: Mapping[str, Any] | None = None,
    ratings: Mapping[str, Any] | None = None,
    quality_flag_overrides: Mapping[str, Any] | None = None,
    row_id: Any | None = None,
    run_id: Any | None = None,
) -> dict[str, Any]:
    """Build a P7ScorecardRowV1 from an existing ProductQualityEventV1.

    ``product_quality_event`` must already satisfy ProductQualityEventV1.  This
    bridge does not rewrite that event; it creates P7's scorecard row material on
    top of it.
    """

    assert_product_quality_measurement_event_meta_only(product_quality_event)
    assert_p7_no_body_payload_or_contract_mutation(product_quality_event, source="p7_product_quality_event_bridge.event")
    for optional_name, optional_value in (
        ("sequence", sequence),
        ("source", source),
        ("ratings", ratings),
        ("quality_flag_overrides", quality_flag_overrides),
    ):
        if optional_value is not None:
            assert_p7_no_body_payload_or_contract_mutation(
                optional_value, source=f"p7_product_quality_event_bridge.{optional_name}"
            )
    handoff = safe_mapping(p7_handoff_summary) if p7_handoff_summary is not None else build_p7_handoff_summary()
    assert_p7_handoff_summary_contract(handoff)
    ledger = safe_mapping(p7_red_ledger) if p7_red_ledger is not None else build_p7_red_ledger()
    assert_p7_red_ledger_contract(ledger)

    product_row = product_quality_event_to_scorecard_row(product_quality_event)
    assert_p7_no_body_payload_or_contract_mutation(product_row, source="p7_product_quality_event_bridge.product_row")

    family = normalize_p7_scorecard_family(product_quality_event.get("family") or product_row.get("family"))
    if family == "unknown" and safe_mapping(sequence).get("history_line_eligible") is True:
        family = "history_line_eligible"
    sequence_row = normalize_p7_sequence(sequence, family=family)
    source_row = _source_from_product_quality_event(product_quality_event, source_override=source)
    display_status = _scorecard_observation_status(product_quality_event.get("observation_status"))
    public_reached = bool(product_quality_event.get("public_display_reached") or product_row.get("public_display_reached"))
    comment_present = bool(product_quality_event.get("comment_text_present") or product_row.get("comment_text_present"))
    product_surface_valid = bool(product_row.get("product_surface_valid"))
    blocker_refs = _blocker_refs(product_row, ledger)

    row = {
        "schema_version": P7_SCORECARD_ROW_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_EVENT_BRIDGE_STEP,
        "row_id": clean_identifier(row_id if row_id is not None else product_quality_event.get("row_id"), default="row", max_length=96),
        "run_id": clean_identifier(run_id if run_id is not None else product_quality_event.get("run_id"), default="product_quality_run", max_length=96),
        "source": source_row,
        "family": family,
        "sequence": sequence_row,
        "display_contract": {
            "observation_status": display_status,
            "public_reached": public_reached,
            "rn_visible": bool(public_reached and display_status == "passed" and comment_present),
            "product_surface_valid": product_surface_valid,
            "comment_text_present": comment_present,
            "comment_text_length": _to_int(product_quality_event.get("comment_text_length"), default=0, minimum=0, maximum=800),
        },
        "p5": _p5_section(handoff),
        "p6": _p6_section(handoff, family=family),
        "quality_flags": _quality_flags(product_row, overrides=quality_flag_overrides),
        "ratings": normalize_p7_ratings(ratings),
        "red_refs": dedupe_identifiers([*_ledger_refs(ledger, status="RED"), *dedupe_identifiers(handoff.get("red_refs"), limit=40)] or P7_INITIAL_RED_IDS, limit=40),
        "hold_refs": dedupe_identifiers([*_ledger_refs(ledger, status="HOLD"), *dedupe_identifiers(handoff.get("hold_refs"), limit=40)] or P7_INITIAL_HOLD_IDS, limit=40),
        "blocker_refs": blocker_refs,
        "blocker_ids": blocker_refs,
        "public_contract": public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True),
        "source_event_schema_version": clean_identifier(product_quality_event.get("schema_version"), default=PRODUCT_QUALITY_EVENT_SCHEMA_VERSION, max_length=128),
        "handoff_schema_version": clean_identifier(handoff.get("schema_version"), max_length=128),
        "red_ledger_schema_version": clean_identifier(ledger.get("schema_version"), max_length=128),
        "bridge_source": P7_SCORECARD_ROW_SOURCE,
        "body_free": True,
        "release_allowed": False,
    }
    assert_p7_scorecard_row_contract(row)
    return row


def build_p7_scorecard_row_from_product_quality_event(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Compatibility alias for P7-4 bridge callers."""

    return build_p7_scorecard_row(*args, **kwargs)


def build_p7_p6_visible_expansion_boundary_validation(
    scorecard_rows: Sequence[Mapping[str, Any]] | None = None,
    *,
    matrix_id: Any = "p7_p6_visible_expansion_boundary:20260613",
) -> dict[str, Any]:
    """Build the R9 body-free validation material for P6 visible boundaries."""

    rows = list(scorecard_rows or [])
    violations: list[dict[str, Any]] = []
    observed_families: list[str] = []
    family_status_counts: dict[str, int] = {
        "visible_allowed": 0,
        "meta_only": 0,
        "no_connect": 0,
        "not_eligible": 0,
    }
    for index, row in enumerate(rows, start=1):
        assert_p7_scorecard_row_contract(row)
        assert_p7_no_body_payload_or_contract_mutation(row, source=f"p7_p6_boundary_validation.scorecard_rows[{index}]")
        family = clean_identifier(row.get("family"), default="unknown", max_length=120)
        p6 = safe_mapping(row.get("p6"))
        boundary = p7_p6_family_boundary_for_family(
            family,
            runtime_evaluated=p6.get("status") not in {"not_eligible", "blocked"},
            visible_applied=p6.get("visible_applied") is True,
        )
        observed_families.append(clean_identifier(boundary.get("normalized_family"), default="unknown", max_length=120))
        status = clean_identifier(boundary.get("family_status"), default="not_eligible", max_length=80)
        family_status_counts[status] = family_status_counts.get(status, 0) + 1
        if boundary.get("visible_applied_violation") is True or (family != "structure_question" and p6.get("visible_applied") is True):
            violations.append(
                {
                    "row_id": clean_identifier(row.get("row_id"), default=f"row_{index}", max_length=96),
                    "family": family,
                    "normalized_family": clean_identifier(boundary.get("normalized_family"), default="unknown", max_length=120),
                    "reason_code": "p6_visible_expansion_outside_structure_question",
                    "body_free": True,
                }
            )
    validation_status = "passed" if not violations else "blocked"
    material = {
        "schema_version": P7_P6_VISIBLE_BOUNDARY_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": "R9_P6VisibleExpansionBoundaryValidation_20260613",
        "matrix_id": clean_identifier(matrix_id, default="p7_p6_visible_expansion_boundary", max_length=160),
        "source_scorecard_schema_version": P7_SCORECARD_ROW_SCHEMA_VERSION,
        "row_count": len(rows),
        "observed_families": dedupe_identifiers(observed_families, limit=80, max_length=120),
        "family_status_counts": family_status_counts,
        "validation_status": validation_status,
        "observed_status": "PASS" if validation_status == "passed" else "BLOCKED",
        "violation_count": len(violations),
        "violations": violations,
        "visible_allowed_families": list(P7_P6_VISIBLE_ALLOWED_FAMILIES),
        "meta_only_families": list(P7_P6_META_ONLY_FAMILIES),
        "no_connect_families": list(P7_P6_NO_CONNECT_FAMILIES),
        "visible_expansion_allowed": False,
        "visible_expansion_requires_future_design": True,
        "p7_holds": ["P7-HOLD-002"],
        "hold_refs": ["P7-HOLD-002"],
        "release_allowed": False,
        "release_blocker": True,
        "public_contract": public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True),
        "raw_input_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "reviewer_free_text_included": False,
        "body_free": True,
    }
    assert_p7_p6_visible_expansion_boundary_contract(material)
    return material


def assert_p7_p6_family_boundary_contract(policy: Mapping[str, Any]) -> bool:
    data = safe_mapping(policy)
    if data.get("schema_version") != P7_P6_VISIBLE_BOUNDARY_SCHEMA_VERSION:
        raise ValueError("unexpected P7 P6 family boundary schema_version")
    if data.get("phase") != P7_PHASE:
        raise ValueError("unexpected P7 P6 family boundary phase")
    if data.get("release_allowed") is not False or data.get("body_free") is not True:
        raise ValueError("P7 P6 family boundary must be body-free and release-closed")
    if data.get("visible_expansion_allowed") is not False or data.get("visible_expansion_requires_future_design") is not True:
        raise ValueError("P7 P6 visible expansion must remain disabled in R9")
    if list(data.get("visible_allowed_families") or []) != list(P7_P6_VISIBLE_ALLOWED_FAMILIES):
        raise ValueError("P7 P6 visible allowed families changed")
    if "P7-HOLD-002" not in dedupe_identifiers(data.get("p7_holds") or data.get("hold_refs"), limit=20):
        raise ValueError("P7-HOLD-002 must remain on P6 visible boundary material")
    if data.get("visible_applied_allowed") is True and data.get("normalized_family") != "structure_question":
        raise ValueError("P6 visible application must stay structure_question-only")
    for key in (
        "raw_input_included",
        "comment_text_body_included",
        "candidate_body_included",
        "surface_body_included",
        "reviewer_free_text_included",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7 P6 boundary must keep {key}=False")
    assert_false_markers(safe_mapping(data.get("public_contract")), source="p7_p6_family_boundary.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_p6_family_boundary.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_p6_family_boundary")
    return True


def assert_p7_p6_visible_expansion_boundary_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    if data.get("schema_version") != P7_P6_VISIBLE_BOUNDARY_SCHEMA_VERSION:
        raise ValueError("unexpected P7 P6 visible boundary validation schema_version")
    if data.get("phase") != P7_PHASE:
        raise ValueError("unexpected P7 P6 visible boundary validation phase")
    if data.get("release_allowed") is not False or data.get("body_free") is not True:
        raise ValueError("P7 P6 visible boundary validation must be body-free and release-closed")
    if data.get("visible_expansion_allowed") is not False or data.get("visible_expansion_requires_future_design") is not True:
        raise ValueError("P6 visible expansion cannot be enabled by P7 validation")
    if list(data.get("visible_allowed_families") or []) != list(P7_P6_VISIBLE_ALLOWED_FAMILIES):
        raise ValueError("P6 visible allowed family list changed")
    if "P7-HOLD-002" not in dedupe_identifiers(data.get("p7_holds") or data.get("hold_refs"), limit=20):
        raise ValueError("P7-HOLD-002 must remain on P6 visible boundary validation")
    if data.get("violation_count") != len(data.get("violations") or []):
        raise ValueError("P6 visible boundary violation_count mismatch")
    if data.get("validation_status") == "passed" and data.get("violation_count") != 0:
        raise ValueError("P6 visible boundary cannot pass with violations")
    for violation in data.get("violations") or []:
        item = safe_mapping(violation)
        if item.get("body_free") is not True:
            raise ValueError("P6 visible boundary violation items must be body-free")
    for key in (
        "raw_input_included",
        "comment_text_body_included",
        "candidate_body_included",
        "surface_body_included",
        "reviewer_free_text_included",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7 P6 visible validation must keep {key}=False")
    assert_false_markers(safe_mapping(data.get("public_contract")), source="p7_p6_visible_boundary.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_p6_visible_boundary.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_p6_visible_boundary")
    return True


def assert_p7_scorecard_row_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    missing = [key for key in P7_SCORECARD_REQUIRED_TOP_LEVEL_KEYS if key not in data]
    if missing:
        raise ValueError(f"P7 scorecard row is missing required keys: {missing}")
    if data.get("schema_version") != P7_SCORECARD_ROW_SCHEMA_VERSION:
        raise ValueError("unexpected P7 scorecard row schema_version")
    if data.get("phase") != P7_PHASE:
        raise ValueError("unexpected P7 scorecard row phase")
    if data.get("step") != P7_EVENT_BRIDGE_STEP:
        raise ValueError("unexpected P7 scorecard row step")
    if data.get("release_allowed") is not False:
        raise ValueError("P7 scorecard row must not allow release")
    if data.get("body_free") is not True:
        raise ValueError("P7 scorecard row must be body-free")
    if data.get("source_event_schema_version") != PRODUCT_QUALITY_EVENT_SCHEMA_VERSION:
        raise ValueError("P7 scorecard row must preserve ProductQualityEventV1 as source")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_scorecard_row")

    source = safe_mapping(data.get("source"))
    if source.get("source_type") not in P7_ALLOWED_SOURCE_TYPES:
        raise ValueError("P7 scorecard row has invalid source.source_type")
    if not clean_identifier(source.get("source_case_id"), max_length=96):
        raise ValueError("P7 scorecard row requires source.source_case_id")

    family = clean_identifier(data.get("family"), max_length=120)
    if family not in P7_SCORECARD_FAMILIES:
        raise ValueError("P7 scorecard row has unsupported family")

    sequence = safe_mapping(data.get("sequence"))
    if _to_int(sequence.get("sequence_length"), minimum=1, maximum=30) < 1:
        raise ValueError("P7 scorecard row sequence length must be positive")
    if sequence.get("row_kind") not in {"single_input", "sequence"}:
        raise ValueError("P7 scorecard row sequence row_kind changed")
    if sequence.get("row_kind") == "single_input" and sequence.get("sequence_length") != 1:
        raise ValueError("single_input rows must have sequence_length 1")

    display = safe_mapping(data.get("display_contract"))
    if display.get("observation_status") not in P7_ALLOWED_SCORECARD_OBSERVATION_STATUSES:
        raise ValueError("P7 scorecard row display observation status changed")
    for key in ("public_reached", "rn_visible", "product_surface_valid", "comment_text_present"):
        if not isinstance(display.get(key), bool):
            raise ValueError(f"P7 scorecard row display_contract.{key} must be boolean")
    if not isinstance(display.get("comment_text_length"), int) or display.get("comment_text_length") < 0:
        raise ValueError("P7 scorecard row display_contract.comment_text_length must be a non-negative integer")

    p5 = safe_mapping(data.get("p5"))
    if p5.get("status") not in P7_ALLOWED_P5_STATUSES:
        raise ValueError("P7 scorecard row p5.status changed")
    for key in ("eligible", "visible_applied", "human_qa_completed"):
        if not isinstance(p5.get(key), bool):
            raise ValueError(f"P7 scorecard row p5.{key} must be boolean")

    p6 = safe_mapping(data.get("p6"))
    if p6.get("status") not in P7_ALLOWED_P6_STATUSES:
        raise ValueError("P7 scorecard row p6.status changed")
    if p6.get("visible_family") not in P7_ALLOWED_VISIBLE_FAMILIES:
        raise ValueError("P7 scorecard row p6.visible_family changed")
    if family != "structure_question" and p6.get("visible_applied") is True:
        raise ValueError("P6 visible surface must stay structure_question-only in P7 scorecard rows")
    for key in ("eligible", "visible_applied"):
        if not isinstance(p6.get(key), bool):
            raise ValueError(f"P7 scorecard row p6.{key} must be boolean")
    if p6.get("visible_expansion_allowed") is not False:
        raise ValueError("P7 scorecard row must keep P6 visible expansion disabled")
    if p6.get("visible_expansion_requires_future_design") is not True:
        raise ValueError("P7 scorecard row must keep P6 visible expansion future-design gated")
    if p6.get("visible_applied_violation") is True:
        raise ValueError("P7 scorecard row cannot carry P6 visible violation")
    if p6.get("p7_hold_refs") is not None and "P7-HOLD-002" not in dedupe_identifiers(p6.get("p7_hold_refs"), limit=20):
        raise ValueError("P7 scorecard row p6 must preserve P7-HOLD-002 boundary ref")

    flags = safe_mapping(data.get("quality_flags"))
    expected_flag_keys = {
        "mirror_only_detected",
        "template_major_detected",
        "unsafe_claim_detected",
        "overclaim_risk_detected",
        "creepy_risk_detected",
    }
    if set(flags) != expected_flag_keys:
        raise ValueError("P7 scorecard row quality_flags key set changed")
    if any(not isinstance(flags.get(key), bool) for key in expected_flag_keys):
        raise ValueError("P7 scorecard row quality_flags must be boolean-only")

    ratings = safe_mapping(data.get("ratings"))
    if ratings.get("blind_qa_required") is not True:
        raise ValueError("P7 scorecard row must keep Blind QA required")
    if ratings.get("rating_required") is False and ratings.get("blind_qa_completed") is not True:
        raise ValueError("P7 scorecard row cannot clear rating_required before Blind QA is complete")
    scores = safe_mapping(ratings.get("dimension_scores"))
    for key, value in scores.items():
        if clean_identifier(key) not in P7_RATING_REQUIRED_DIMENSIONS:
            raise ValueError("P7 scorecard row has unsupported rating dimension")
        if not isinstance(value, (int, float)) or value < 0 or value > 1:
            raise ValueError("P7 scorecard row rating scores must be 0..1 numbers")
    if not isinstance(ratings.get("missing_dimensions"), list):
        raise ValueError("P7 scorecard row ratings.missing_dimensions must be a list")
    if ratings.get("blind_qa_completed") is True and ratings.get("missing_dimensions"):
        raise ValueError("P7 scorecard row cannot complete Blind QA with missing dimensions")

    for key in ("red_refs", "hold_refs", "blocker_refs", "blocker_ids"):
        if not isinstance(data.get(key), list):
            raise ValueError(f"P7 scorecard row {key} must be a list")
    assert_false_markers(safe_mapping(data.get("public_contract")), source="p7_scorecard_row.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_scorecard_row.body_free_markers")
    return True


__all__ = [
    "P7_EVENT_BRIDGE_STEP",
    "P7_P6_VISIBLE_ALLOWED_FAMILIES",
    "P7_P6_VISIBLE_BOUNDARY_SCHEMA_VERSION",
    "P7_RATING_REQUIRED_DIMENSIONS",
    "P7_SCORECARD_FAMILIES",
    "P7_SCORECARD_ROW_SCHEMA_VERSION",
    "assert_p7_p6_family_boundary_contract",
    "assert_p7_p6_visible_expansion_boundary_contract",
    "assert_p7_scorecard_row_contract",
    "build_p7_p6_visible_expansion_boundary_validation",
    "build_p7_scorecard_row",
    "p7_p6_family_boundary_for_family",
    "build_p7_scorecard_row_from_product_quality_event",
    "normalize_p7_ratings",
    "normalize_p7_scorecard_family",
    "normalize_p7_sequence",
]
