# -*- coding: utf-8 -*-
"""P7-5 family / sequence / history-line evaluation matrix.

The matrix lets P7 evaluate single-input rows separately from sequence rows and
keeps P6 visible expansion blocked outside ``structure_question``.  It also
summarizes P7ScorecardRowV1 rows by family, sequence, history-line eligibility,
and RED / REPAIR_REQUIRED / YELLOW / PASS / PRODUCT_PASS candidate verdicts.
Product Pass is counted only as candidate material and never as Release Ready.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from typing import Any, Final

from emlis_ai_p7_contracts import (
    P7_PHASE,
    assert_p7_no_body_payload_or_contract_mutation,
    clean_identifier,
    dedupe_identifiers,
    public_contract_flags,
    safe_mapping,
)
from emlis_ai_p7_event_bridge import (
    P7_RATING_REQUIRED_DIMENSIONS,
    P7_SCORECARD_ROW_SCHEMA_VERSION,
    P7_SCORECARD_FAMILIES,
    assert_p7_scorecard_row_contract,
    normalize_p7_scorecard_family,
)

P7_EVALUATION_MATRIX_SCHEMA_VERSION: Final = "cocolon.emlis.p7.evaluation_matrix.v1"
P7_EVALUATION_MATRIX_STEP: Final = "P7-5_FamilySequenceHistoryLineEvaluationMatrix_20260612"
P7_EVALUATION_MATRIX_SCOPE: Final = "P7_family_sequence_history_line_body_free_evaluation_matrix"

P7_EVALUATION_FAMILIES: Final[tuple[str, ...]] = (
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
)

P7_HISTORY_LINE_ELIGIBLE_FAMILIES: Final[frozenset[str]] = frozenset(
    {
        "history_line_eligible",
        "long_meaning_arc",
        "relationship_gratitude_recovery",
        "change_future_intention",
    }
)
P7_P6_VISIBLE_ALLOWED_FAMILIES: Final[frozenset[str]] = frozenset({"structure_question"})
P7_VERDICTS: Final[tuple[str, ...]] = ("RED", "REPAIR_REQUIRED", "YELLOW", "PASS", "PRODUCT_PASS")
P7_SEQUENCE_DEFINITIONS: Final[tuple[dict[str, Any], ...]] = (
    {
        "sequence_id": "sequence_1",
        "sequence_length": 1,
        "row_kind": "single_input",
        "history_line_candidate": False,
        "description_code": "current_only_no_history",
    },
    {
        "sequence_id": "sequence_3",
        "sequence_length": 3,
        "row_kind": "sequence",
        "history_line_candidate": True,
        "description_code": "same_user_three_inputs_history_line_candidate",
    },
    {
        "sequence_id": "sequence_7",
        "sequence_length": 7,
        "row_kind": "sequence",
        "history_line_candidate": True,
        "description_code": "same_user_seven_inputs_long_run_candidate",
    },
)


def _empty_verdict_counts() -> dict[str, int]:
    return {verdict: 0 for verdict in P7_VERDICTS}


def _to_float_scores(value: Mapping[str, Any]) -> list[float]:
    scores = []
    for raw in safe_mapping(value.get("dimension_scores")).values():
        if isinstance(raw, (int, float)):
            score = float(raw)
            if 0 <= score <= 1:
                scores.append(score)
    return scores


def _history_line_eligible_from_row(row: Mapping[str, Any]) -> bool:
    sequence = safe_mapping(row.get("sequence"))
    family = normalize_p7_scorecard_family(row.get("family"))
    return bool(sequence.get("history_line_eligible") is True or family in P7_HISTORY_LINE_ELIGIBLE_FAMILIES)


def classify_p7_scorecard_row_verdict(row: Mapping[str, Any]) -> str:
    """Classify a body-free P7 scorecard row for matrix aggregation.

    This is not a release gate.  ``PRODUCT_PASS`` means candidate material only;
    the source row must still keep ``release_allowed`` false.
    """

    assert_p7_scorecard_row_contract(row)
    if row.get("red_refs"):
        return "RED"
    blocker_refs = dedupe_identifiers(
        [*dedupe_identifiers(row.get("blocker_refs"), limit=80), *dedupe_identifiers(row.get("blocker_ids"), limit=80)],
        limit=120,
    )
    if any(ref.startswith("P7-RED-") for ref in blocker_refs):
        return "RED"
    if blocker_refs:
        return "REPAIR_REQUIRED"

    display = safe_mapping(row.get("display_contract"))
    if (
        display.get("observation_status") != "passed"
        or display.get("public_reached") is not True
        or display.get("rn_visible") is not True
        or display.get("product_surface_valid") is not True
        or display.get("comment_text_present") is not True
    ):
        return "REPAIR_REQUIRED"

    flags = safe_mapping(row.get("quality_flags"))
    if any(flags.get(key) is True for key in flags):
        return "REPAIR_REQUIRED"

    ratings = safe_mapping(row.get("ratings"))
    if row.get("hold_refs") or ratings.get("blind_qa_completed") is not True or ratings.get("missing_dimensions"):
        return "YELLOW"

    scores = _to_float_scores(ratings)
    if not scores:
        return "YELLOW"
    average = sum(scores) / len(scores)
    if average >= 0.9:
        return "PRODUCT_PASS"
    if average >= 0.75:
        return "PASS"
    return "REPAIR_REQUIRED"


def build_p7_family_sequence_matrix_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for family in P7_EVALUATION_FAMILIES:
        family_history_line_eligible = family in P7_HISTORY_LINE_ELIGIBLE_FAMILIES
        p6_visible_allowed = family in P7_P6_VISIBLE_ALLOWED_FAMILIES
        for sequence in P7_SEQUENCE_DEFINITIONS:
            history_line_eligible = bool(sequence["history_line_candidate"] and family_history_line_eligible)
            blocked_reasons: list[str] = []
            if not p6_visible_allowed:
                blocked_reasons.append("p6_visible_family_not_structure_question")
            if family in {"long_meaning_arc", "history_line_eligible"}:
                blocked_reasons.append("p6_long_meaning_arc_visible_hold")
            row = {
                "matrix_row_id": f"{family}:{sequence['sequence_id']}",
                "family": family,
                "sequence_id": sequence["sequence_id"],
                "sequence_length": sequence["sequence_length"],
                "row_kind": sequence["row_kind"],
                "sequence_history_line_candidate": bool(sequence["history_line_candidate"]),
                "family_history_line_eligible": family_history_line_eligible,
                "history_line_eligible": history_line_eligible,
                "p6_visible_allowed": p6_visible_allowed,
                "p6_visible_blocked_reason_codes": dedupe_identifiers(blocked_reasons, limit=8),
                "evaluation_axes": [
                    "display_contract",
                    "product_surface_valid",
                    "p5_history_line",
                    "p6_structure_insight_boundary",
                    "ratings_required",
                    "red_hold_blocker_refs",
                ],
                "allowed_verdicts": list(P7_VERDICTS),
                "initial_verdict": "YELLOW",
                "required_rating_dimensions": list(P7_RATING_REQUIRED_DIMENSIONS),
                "body_free": True,
                "release_allowed": False,
            }
            rows.append(row)
    return rows


def aggregate_p7_scorecard_rows_by_family_sequence(scorecard_rows: Sequence[Mapping[str, Any]] | None = None) -> dict[str, Any]:
    rows = list(scorecard_rows or [])
    by_family: dict[str, dict[str, Any]] = {}
    by_sequence: dict[str, dict[str, Any]] = {}
    overall_counter: Counter[str] = Counter()
    history_line_counter: Counter[str] = Counter()
    sequence_family_seen: dict[str, set[str]] = defaultdict(set)

    for row in rows:
        assert_p7_scorecard_row_contract(row)
        verdict = classify_p7_scorecard_row_verdict(row)
        overall_counter[verdict] += 1
        family = normalize_p7_scorecard_family(row.get("family"))
        sequence = safe_mapping(row.get("sequence"))
        sequence_id = clean_identifier(sequence.get("sequence_id"), default="sequence_1", max_length=96)
        sequence_family_seen[sequence_id].add(family)
        if _history_line_eligible_from_row(row):
            history_line_counter["history_line_eligible_rows"] += 1
        else:
            history_line_counter["history_line_non_eligible_rows"] += 1

        family_bucket = by_family.setdefault(
            family,
            {
                "family": family,
                "verdict_counts": _empty_verdict_counts(),
                "row_count": 0,
                "sequence_ids": [],
                "history_line_eligible_count": 0,
                "p6_visible_allowed": family in P7_P6_VISIBLE_ALLOWED_FAMILIES,
                "release_allowed": False,
            },
        )
        family_bucket["row_count"] += 1
        family_bucket["verdict_counts"][verdict] += 1
        if sequence_id not in family_bucket["sequence_ids"]:
            family_bucket["sequence_ids"].append(sequence_id)
        if _history_line_eligible_from_row(row):
            family_bucket["history_line_eligible_count"] += 1

        sequence_bucket = by_sequence.setdefault(
            sequence_id,
            {
                "sequence_id": sequence_id,
                "sequence_length": int(sequence.get("sequence_length") or 1),
                "row_kind": clean_identifier(sequence.get("row_kind"), default="single_input", max_length=40),
                "verdict_counts": _empty_verdict_counts(),
                "row_count": 0,
                "family_count": 0,
                "release_allowed": False,
            },
        )
        sequence_bucket["row_count"] += 1
        sequence_bucket["verdict_counts"][verdict] += 1

    for sequence_id, families in sequence_family_seen.items():
        if sequence_id in by_sequence:
            by_sequence[sequence_id]["family_count"] = len(families)

    return {
        "schema_version": "cocolon.emlis.p7.evaluation_matrix_aggregation.v1",
        "source_scorecard_schema_version": P7_SCORECARD_ROW_SCHEMA_VERSION,
        "overall_verdict_counts": {verdict: overall_counter.get(verdict, 0) for verdict in P7_VERDICTS},
        "by_family": by_family,
        "by_sequence": by_sequence,
        "history_line_counts": {
            "history_line_eligible_rows": history_line_counter.get("history_line_eligible_rows", 0),
            "history_line_non_eligible_rows": history_line_counter.get("history_line_non_eligible_rows", 0),
        },
        "product_pass_is_release_ready": False,
        "release_allowed": False,
        "body_free": True,
    }


def build_p7_evaluation_matrix(scorecard_rows: Sequence[Mapping[str, Any]] | None = None) -> dict[str, Any]:
    matrix_rows = build_p7_family_sequence_matrix_rows()
    aggregation = aggregate_p7_scorecard_rows_by_family_sequence(scorecard_rows)
    matrix = {
        "schema_version": P7_EVALUATION_MATRIX_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_EVALUATION_MATRIX_STEP,
        "scope": P7_EVALUATION_MATRIX_SCOPE,
        "families": list(P7_EVALUATION_FAMILIES),
        "sequences": [dict(sequence) for sequence in P7_SEQUENCE_DEFINITIONS],
        "matrix_rows": matrix_rows,
        "family_count": len(P7_EVALUATION_FAMILIES),
        "sequence_count": len(P7_SEQUENCE_DEFINITIONS),
        "matrix_row_count": len(matrix_rows),
        "allowed_verdicts": list(P7_VERDICTS),
        "p6_visible_allowed_families": sorted(P7_P6_VISIBLE_ALLOWED_FAMILIES),
        "p6_visible_blocked_families": [family for family in P7_EVALUATION_FAMILIES if family not in P7_P6_VISIBLE_ALLOWED_FAMILIES],
        "history_line_eligible_families": sorted(P7_HISTORY_LINE_ELIGIBLE_FAMILIES),
        "aggregation": aggregation,
        "public_contract": public_contract_flags(),
        "body_free": True,
        "product_pass_is_release_ready": False,
        "release_allowed": False,
    }
    assert_p7_evaluation_matrix_contract(matrix)
    return matrix


def assert_p7_evaluation_matrix_contract(matrix: Mapping[str, Any]) -> bool:
    data = safe_mapping(matrix)
    if data.get("schema_version") != P7_EVALUATION_MATRIX_SCHEMA_VERSION:
        raise ValueError("unexpected P7 evaluation matrix schema_version")
    if data.get("phase") != P7_PHASE:
        raise ValueError("unexpected P7 evaluation matrix phase")
    if data.get("scope") != P7_EVALUATION_MATRIX_SCOPE:
        raise ValueError("unexpected P7 evaluation matrix scope")
    if data.get("release_allowed") is not False:
        raise ValueError("P7 evaluation matrix must not allow release")
    if data.get("product_pass_is_release_ready") is not False:
        raise ValueError("P7 evaluation matrix must not convert Product Pass to Release Ready")
    if data.get("body_free") is not True:
        raise ValueError("P7 evaluation matrix must be body-free")
    public_contract = safe_mapping(data.get("public_contract"))
    if any(value is True for value in public_contract.values()):
        raise ValueError("P7 evaluation matrix must not mutate public contracts")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_evaluation_matrix")

    families = data.get("families")
    sequences = data.get("sequences")
    rows = data.get("matrix_rows")
    if list(families or []) != list(P7_EVALUATION_FAMILIES):
        raise ValueError("P7 evaluation matrix family set changed")
    if not isinstance(sequences, list) or {seq.get("sequence_id") for seq in sequences if isinstance(seq, Mapping)} != {
        "sequence_1",
        "sequence_3",
        "sequence_7",
    }:
        raise ValueError("P7 evaluation matrix must keep sequence_1/3/7")
    if not isinstance(rows, list) or len(rows) != len(P7_EVALUATION_FAMILIES) * len(P7_SEQUENCE_DEFINITIONS):
        raise ValueError("P7 evaluation matrix row count changed")
    seen: set[str] = set()
    row_kinds = {"single_input": 0, "sequence": 0}
    for row in rows:
        item = safe_mapping(row)
        row_id = clean_identifier(item.get("matrix_row_id"), max_length=180)
        if not row_id or row_id in seen:
            raise ValueError("P7 evaluation matrix rows must have unique ids")
        seen.add(row_id)
        family = clean_identifier(item.get("family"), max_length=120)
        if family not in P7_EVALUATION_FAMILIES:
            raise ValueError("P7 evaluation matrix row has unsupported family")
        row_kind = clean_identifier(item.get("row_kind"), max_length=40)
        if row_kind not in row_kinds:
            raise ValueError("P7 evaluation matrix row_kind changed")
        row_kinds[row_kind] += 1
        if item.get("body_free") is not True or item.get("release_allowed") is not False:
            raise ValueError("P7 evaluation matrix rows must be body-free and release-closed")
        if family != "structure_question" and item.get("p6_visible_allowed") is True:
            raise ValueError("P6 visible allowed family must remain structure_question-only")
        if family == "structure_question" and item.get("p6_visible_allowed") is not True:
            raise ValueError("structure_question must remain the only P6 visible allowed family")
        if item.get("allowed_verdicts") != list(P7_VERDICTS):
            raise ValueError("P7 evaluation matrix verdict set changed")
    if row_kinds["single_input"] != len(P7_EVALUATION_FAMILIES):
        raise ValueError("P7 evaluation matrix must include one single-input row per family")
    if row_kinds["sequence"] != len(P7_EVALUATION_FAMILIES) * 2:
        raise ValueError("P7 evaluation matrix must include sequence_3 and sequence_7 rows per family")

    aggregation = safe_mapping(data.get("aggregation"))
    if aggregation.get("release_allowed") is not False:
        raise ValueError("P7 evaluation aggregation must remain release-closed")
    if aggregation.get("product_pass_is_release_ready") is not False:
        raise ValueError("P7 evaluation aggregation must not promote Product Pass")
    counts = safe_mapping(aggregation.get("overall_verdict_counts"))
    if set(counts) != set(P7_VERDICTS):
        raise ValueError("P7 evaluation aggregation verdict counts changed")
    return True


__all__ = [
    "P7_EVALUATION_FAMILIES",
    "P7_EVALUATION_MATRIX_SCHEMA_VERSION",
    "P7_EVALUATION_MATRIX_STEP",
    "P7_SEQUENCE_DEFINITIONS",
    "P7_VERDICTS",
    "aggregate_p7_scorecard_rows_by_family_sequence",
    "assert_p7_evaluation_matrix_contract",
    "build_p7_evaluation_matrix",
    "build_p7_family_sequence_matrix_rows",
    "classify_p7_scorecard_row_verdict",
]
