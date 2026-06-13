# -*- coding: utf-8 -*-
"""P7-6 ratings-only Blind QA material export.

This module turns P7ScorecardRowV1 rows into Blind QA candidate material without
copying raw input, comment_text bodies, candidate bodies, surface bodies, or
reviewer free text.  Machine metrics are never used to fill read_feeling: scores
are reflected only when a ratings-only review supplies dimension scores.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any, Final

from emlis_ai_p7_contracts import (
    P7_INITIAL_HOLD_IDS,
    P7_PHASE,
    assert_false_markers,
    assert_p7_no_body_payload_or_contract_mutation,
    body_free_flags,
    clean_identifier,
    dedupe_identifiers,
    public_contract_flags,
    safe_mapping,
)
from emlis_ai_p7_event_bridge import (
    P7_RATING_REQUIRED_DIMENSIONS,
    P7_SCORECARD_ROW_SCHEMA_VERSION,
    assert_p7_scorecard_row_contract,
)
from emlis_ai_p7_evaluation_matrix import P7_VERDICTS

P7_BLIND_QA_MATERIAL_SCHEMA_VERSION: Final = "cocolon.emlis.p7.blind_qa_material.v1"
P7_BLIND_QA_CANDIDATE_SCHEMA_VERSION: Final = "cocolon.emlis.p7.blind_qa_candidate.v1"
P7_BLIND_QA_REVIEW_SCHEMA_VERSION: Final = "cocolon.emlis.p7.blind_qa_review.v1"
P7_BLIND_QA_MATERIAL_STEP: Final = "P7-6_RatingsOnlyBlindQAMaterialExport_20260612"
P7_BLIND_QA_MATERIAL_SCOPE: Final = "P7_ratings_only_blind_qa_material_export"
P7_BLIND_QA_DIMENSIONS: Final[tuple[str, ...]] = P7_RATING_REQUIRED_DIMENSIONS
P7_HUMAN_QA_MATERIAL_INDEX_SCHEMA_VERSION: Final = "cocolon.emlis.p7.human_qa_material_index.v1"
P7_HUMAN_QA_REVIEW_SUMMARY_SCHEMA_VERSION: Final = "cocolon.emlis.p7.human_qa_review_summary.v1"
P7_HUMAN_QA_SCOPE: Final = "p5_history_line_readfeel"
P7_HUMAN_QA_DIMENSIONS: Final[tuple[str, ...]] = (
    "history_connection_naturalness",
    "creepy_absence",
    "wants_more_input_or_accumulation",
    "overclaim_absence",
    "self_blame_non_amplification",
    "non_shallow_repeat",
)
P7_HUMAN_QA_SOURCE_DIMENSION_ALIASES: Final[dict[str, str]] = {
    "non_shallow_repeat": "non_template",
}
P7_HUMAN_QA_FAMILIES: Final[tuple[str, ...]] = (
    "history_line_eligible",
    "long_meaning_arc",
    "relationship_gratitude_recovery",
)

_ALLOWED_REVIEW_STATUSES: Final[frozenset[str]] = frozenset(
    {"rating_required", "review_missing", "review_partial", "review_completed"}
)
_ALLOWED_VERDICTS: Final[frozenset[str]] = frozenset(P7_VERDICTS)


def _float_score(value: Any) -> float | None:
    try:
        if value is None or value == "" or isinstance(value, bool):
            return None
        score = float(value)
    except (TypeError, ValueError):
        return None
    if 0 <= score <= 1:
        return round(score, 6)
    return None


def _dimension_verdict(score: float | None) -> str:
    if score is None:
        return "YELLOW"
    if score < 0.5:
        return "RED"
    if score < 0.75:
        return "REPAIR_REQUIRED"
    if score >= 0.9:
        return "PRODUCT_PASS"
    return "PASS"


def _overall_verdict(dimension_scores: Mapping[str, float], missing_dimensions: Sequence[str]) -> str:
    if missing_dimensions:
        return "YELLOW"
    if not dimension_scores:
        return "YELLOW"
    dimension_verdicts = [_dimension_verdict(score) for score in dimension_scores.values()]
    if "RED" in dimension_verdicts:
        return "RED"
    if "REPAIR_REQUIRED" in dimension_verdicts:
        return "REPAIR_REQUIRED"
    average = sum(float(score) for score in dimension_scores.values()) / len(dimension_scores)
    if average >= 0.9:
        return "PRODUCT_PASS"
    if average >= 0.75:
        return "PASS"
    return "REPAIR_REQUIRED"


def _candidate_id(row: Mapping[str, Any], *, candidate_index: int) -> str:
    sequence = safe_mapping(row.get("sequence"))
    parts = [
        "p7_blind_qa",
        clean_identifier(row.get("run_id"), default="run", max_length=80),
        clean_identifier(row.get("row_id"), default=f"row_{candidate_index}", max_length=80),
        clean_identifier(row.get("family"), default="unknown", max_length=80),
        clean_identifier(sequence.get("sequence_id"), default="sequence_1", max_length=80),
        str(candidate_index),
    ]
    return ":".join(parts)


def _rating_status(ratings: Mapping[str, Any]) -> str:
    missing = dedupe_identifiers(ratings.get("missing_dimensions"), limit=80)
    scores = safe_mapping(ratings.get("dimension_scores"))
    if ratings.get("blind_qa_completed") is True and not missing:
        return "review_completed"
    if scores:
        return "review_partial"
    if ratings.get("rating_required") is True or missing:
        return "review_missing"
    return "rating_required"


def _review_scores_from_source(source: Mapping[str, Any]) -> dict[str, float]:
    raw_dimensions = safe_mapping(source.get("dimensions"))
    raw_scores = safe_mapping(source.get("dimension_scores"))
    scores: dict[str, float] = {}
    for dimension in P7_BLIND_QA_DIMENSIONS:
        value: Any = raw_scores.get(dimension)
        dimension_payload = safe_mapping(raw_dimensions.get(dimension))
        if value is None and dimension_payload:
            value = dimension_payload.get("score")
        score = _float_score(value)
        if score is not None:
            scores[dimension] = score
    return scores


def _reason_codes_for_dimension(source: Mapping[str, Any], dimension: str) -> list[str]:
    raw_dimensions = safe_mapping(source.get("dimensions"))
    dimension_payload = safe_mapping(raw_dimensions.get(dimension))
    return dedupe_identifiers(dimension_payload.get("reason_codes"), limit=12, max_length=80)


def _human_qa_source_dimension(dimension: str) -> str:
    return P7_HUMAN_QA_SOURCE_DIMENSION_ALIASES.get(dimension, dimension)


def _human_qa_candidate_dimension_scores(candidate: Mapping[str, Any]) -> dict[str, float]:
    scores = safe_mapping(candidate.get("dimension_scores"))
    out: dict[str, float] = {}
    for dimension in P7_HUMAN_QA_DIMENSIONS:
        source_dimension = _human_qa_source_dimension(dimension)
        score = _float_score(scores.get(dimension))
        if score is None:
            score = _float_score(scores.get(source_dimension))
        if score is not None:
            out[dimension] = score
    return out


def _human_qa_candidate_rows(blind_qa_material: Mapping[str, Any]) -> list[dict[str, Any]]:
    candidates = blind_qa_material.get("candidates")
    if not isinstance(candidates, list):
        return []
    rows: list[dict[str, Any]] = []
    for raw in candidates:
        candidate = safe_mapping(raw)
        family = clean_identifier(candidate.get("family"), default="unknown", max_length=120)
        p5_flags = safe_mapping(candidate.get("p5_flags"))
        sequence = safe_mapping(candidate.get("sequence"))
        if (
            family in P7_HUMAN_QA_FAMILIES
            or p5_flags.get("eligible") is True
            or p5_flags.get("visible_applied") is True
            or sequence.get("history_line_eligible") is True
        ):
            rows.append(candidate)
    return rows


def _human_qa_index_from_blind_material(
    blind_qa_material: Mapping[str, Any],
    *,
    material_id: Any = "p7_human_qa_material_index",
) -> dict[str, Any]:
    assert_p7_no_body_payload_or_contract_mutation(blind_qa_material, source="p7_human_qa_material_index.source_blind_qa_material")
    candidates = _human_qa_candidate_rows(blind_qa_material)
    families = dedupe_identifiers((candidate.get("family") for candidate in candidates), limit=20, max_length=120)
    completed_count = 0
    missing_counter: Counter[str] = Counter()
    candidate_statuses: list[str] = []
    for candidate in candidates:
        scores = _human_qa_candidate_dimension_scores(candidate)
        missing = [dimension for dimension in P7_HUMAN_QA_DIMENSIONS if dimension not in scores]
        for dimension in missing:
            missing_counter[dimension] += 1
        status = clean_identifier(candidate.get("review_status"), default="review_missing", max_length=80)
        if not missing and status == "review_completed":
            completed_count += 1
            candidate_statuses.append("review_completed")
        elif scores:
            candidate_statuses.append("review_partial")
        else:
            candidate_statuses.append("review_missing")
    candidate_count = len(candidates)
    p5_human_qa_completed = bool(candidate_count > 0 and completed_count == candidate_count)
    unresolved_hold_refs = [] if p5_human_qa_completed else ["P7-HOLD-001"]
    index = {
        "schema_version": P7_HUMAN_QA_MATERIAL_INDEX_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": "R8_P5HumanQAMaterialBoundary_20260613",
        "material_id": clean_identifier(material_id, default="p7_human_qa_material_index", max_length=160),
        "qa_scope": P7_HUMAN_QA_SCOPE,
        "candidate_count": candidate_count,
        "review_completed_count": completed_count,
        "review_missing_count": max(0, candidate_count - completed_count),
        "families": families,
        "dimensions_required": list(P7_HUMAN_QA_DIMENSIONS),
        "dimension_source_aliases": dict(P7_HUMAN_QA_SOURCE_DIMENSION_ALIASES),
        "missing_dimension_counts": {dimension: missing_counter.get(dimension, 0) for dimension in P7_HUMAN_QA_DIMENSIONS},
        "candidate_review_statuses": candidate_statuses,
        "p5_human_qa_completed": p5_human_qa_completed,
        "human_qa_review_status": "review_completed" if p5_human_qa_completed else "review_required",
        "local_body_review_packet_exists": candidate_count > 0,
        "local_body_review_packet_release_material": False,
        "scorecard_body_free": True,
        "release_material_body_free": True,
        "raw_input_included_in_scorecard": False,
        "comment_text_body_included_in_scorecard": False,
        "reviewer_free_text_included_in_scorecard": False,
        "reviewer_free_text_included": False,
        "raw_input_included": False,
        "comment_text_body_included": False,
        "release_allowed": False,
        "unresolved_hold_refs": unresolved_hold_refs,
        "hold_refs": unresolved_hold_refs,
        "public_contract": public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True),
        "body_free": True,
    }
    assert_p7_human_qa_material_index_contract(index)
    return index


def build_p7_human_qa_material_index(
    scorecard_rows: Sequence[Mapping[str, Any]] | None = None,
    *,
    blind_qa_material: Mapping[str, Any] | None = None,
    material_id: Any = "p7_human_qa_material_index",
) -> dict[str, Any]:
    """Build the R8 body-free P5 human QA material boundary index.

    The local body review packet is represented only by existence and boundary
    flags.  No raw input, comment body, candidate body, surface body, or reviewer
    free text is copied into P7 scorecard or release material.
    """

    if blind_qa_material is None:
        rows = list(scorecard_rows or [])
        for index, row in enumerate(rows, start=1):
            assert_p7_scorecard_row_contract(row)
            assert_p7_no_body_payload_or_contract_mutation(row, source=f"p7_human_qa_material_index.scorecard_rows[{index}]")
        candidates = [build_p7_blind_qa_candidate(row, candidate_index=index) for index, row in enumerate(rows, start=1)]
        blind_qa_material = {
            "schema_version": P7_BLIND_QA_MATERIAL_SCHEMA_VERSION,
            "candidates": candidates,
            "body_free": True,
            "release_allowed": False,
        }
    return _human_qa_index_from_blind_material(safe_mapping(blind_qa_material), material_id=material_id)


def build_p7_human_qa_review_summary(review: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize one ratings-only human QA review summary for release material.

    This summary is ratings/codes only.  It may map the existing P7
    ``non_template`` score into the R8 ``non_shallow_repeat`` dimension, but it
    never accepts or serializes reviewer free text.
    """

    normalized = normalize_p7_blind_qa_review(review) if review.get("schema_version") != P7_BLIND_QA_REVIEW_SCHEMA_VERSION else dict(review)
    assert_p7_blind_qa_review_contract(normalized)
    scores = safe_mapping(normalized.get("dimension_scores"))
    dimensions = safe_mapping(normalized.get("dimensions"))
    human_scores: dict[str, float] = {}
    reason_codes: list[str] = []
    missing: list[str] = []
    for dimension in P7_HUMAN_QA_DIMENSIONS:
        source_dimension = _human_qa_source_dimension(dimension)
        score = _float_score(scores.get(dimension))
        if score is None:
            score = _float_score(scores.get(source_dimension))
        if score is None:
            missing.append(dimension)
        else:
            human_scores[dimension] = score
        reason_codes.extend(_reason_codes_for_dimension({"dimensions": dimensions}, source_dimension))
    status = "review_completed" if not missing else ("review_partial" if human_scores else "review_missing")
    summary = {
        "schema_version": P7_HUMAN_QA_REVIEW_SUMMARY_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": "R8_P5HumanQAReviewSummary_20260613",
        "candidate_id": clean_identifier(normalized.get("candidate_id"), default="candidate", max_length=180),
        "review_status": status,
        "dimension_scores": human_scores,
        "missing_dimensions": missing,
        "reason_codes": dedupe_identifiers([*normalized.get("reason_codes", []), *reason_codes], limit=40, max_length=100),
        "reviewer_free_text_included": False,
        "raw_input_included": False,
        "comment_text_body_included": False,
        "release_allowed": False,
        "public_contract": public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True),
        "body_free": True,
    }
    assert_p7_human_qa_review_summary_contract(summary)
    return summary


def build_p7_blind_qa_candidate(row: Mapping[str, Any], *, candidate_index: int = 1) -> dict[str, Any]:
    """Build one body-free review candidate from a P7 scorecard row."""

    assert_p7_scorecard_row_contract(row)
    assert_p7_no_body_payload_or_contract_mutation(row, source="p7_blind_qa_candidate.source_row")
    sequence = safe_mapping(row.get("sequence"))
    source = safe_mapping(row.get("source"))
    display = safe_mapping(row.get("display_contract"))
    p5 = safe_mapping(row.get("p5"))
    p6 = safe_mapping(row.get("p6"))
    ratings = safe_mapping(row.get("ratings"))
    quality_flags = safe_mapping(row.get("quality_flags"))
    missing_dimensions = dedupe_identifiers(
        ratings.get("missing_dimensions") or [dimension for dimension in P7_BLIND_QA_DIMENSIONS if dimension not in safe_mapping(ratings.get("dimension_scores"))],
        limit=80,
    )
    review_status = _rating_status(ratings)
    dimension_scores = {
        dimension: float(score)
        for dimension, score in safe_mapping(ratings.get("dimension_scores")).items()
        if dimension in P7_BLIND_QA_DIMENSIONS and _float_score(score) is not None
    }
    candidate = {
        "schema_version": P7_BLIND_QA_CANDIDATE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_BLIND_QA_MATERIAL_STEP,
        "candidate_kind": "ratings_only_blind_qa_candidate",
        "candidate_id": _candidate_id(row, candidate_index=candidate_index),
        "candidate_index": int(candidate_index),
        "source_scorecard_schema_version": clean_identifier(row.get("schema_version"), default=P7_SCORECARD_ROW_SCHEMA_VERSION, max_length=120),
        "source_scorecard_row_id": clean_identifier(row.get("row_id"), default="row", max_length=96),
        "run_id": clean_identifier(row.get("run_id"), default="run", max_length=96),
        "source_case_id": clean_identifier(source.get("source_case_id"), default="manual_case", max_length=96),
        "family": clean_identifier(row.get("family"), default="unknown", max_length=120),
        "sequence": {
            "sequence_id": clean_identifier(sequence.get("sequence_id"), default="sequence_1", max_length=96),
            "sequence_index": int(sequence.get("sequence_index") or 1),
            "sequence_length": int(sequence.get("sequence_length") or 1),
            "history_line_eligible": sequence.get("history_line_eligible") is True,
            "row_kind": clean_identifier(sequence.get("row_kind"), default="single_input", max_length=40),
        },
        "display_contract": {
            "observation_status": clean_identifier(display.get("observation_status"), default="unknown", max_length=40),
            "public_reached": display.get("public_reached") is True,
            "rn_visible": display.get("rn_visible") is True,
            "product_surface_valid": display.get("product_surface_valid") is True,
            "comment_text_present": display.get("comment_text_present") is True,
            "comment_text_length": int(display.get("comment_text_length") or 0),
        },
        "p5_flags": {
            "eligible": p5.get("eligible") is True,
            "visible_applied": p5.get("visible_applied") is True,
            "human_qa_completed": p5.get("human_qa_completed") is True,
            "status": clean_identifier(p5.get("status"), default="review_required", max_length=80),
        },
        "p6_flags": {
            "eligible": p6.get("eligible") is True,
            "visible_applied": p6.get("visible_applied") is True,
            "visible_family": clean_identifier(p6.get("visible_family"), default="none", max_length=80),
            "status": clean_identifier(p6.get("status"), default="review_required", max_length=80),
        },
        "quality_flag_ids": [key for key, value in sorted(quality_flags.items()) if value is True],
        "red_refs": dedupe_identifiers(row.get("red_refs"), limit=80),
        "hold_refs": dedupe_identifiers(row.get("hold_refs"), limit=80),
        "blocker_refs": dedupe_identifiers(row.get("blocker_refs"), limit=80),
        "dimensions_required": list(P7_BLIND_QA_DIMENSIONS),
        "missing_dimensions": missing_dimensions,
        "review_status": review_status,
        "rating_required": review_status != "review_completed",
        "reviewer_payload_body_externalized": True,
        "reviewer_free_text_included": False,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "read_feeling_auto_estimation_allowed": False,
        "public_contract": public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True),
        "body_free": True,
        "release_allowed": False,
    }
    if dimension_scores:
        candidate["dimension_scores"] = dimension_scores
    assert_p7_blind_qa_candidate_contract(candidate)
    return candidate


def normalize_p7_blind_qa_review(review: Mapping[str, Any] | None) -> dict[str, Any]:
    """Normalize a ratings-only Blind QA review.

    Free-form reviewer prose is intentionally rejected by the shared P7 contract;
    only scores, verdicts, and reason codes are retained.
    """

    data = safe_mapping(review)
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_blind_qa_review.input")
    scores = _review_scores_from_source(data)
    missing = [dimension for dimension in P7_BLIND_QA_DIMENSIONS if dimension not in scores]
    dimensions: dict[str, dict[str, Any]] = {}
    for dimension in P7_BLIND_QA_DIMENSIONS:
        score = scores.get(dimension)
        dimensions[dimension] = {
            "score": score,
            "verdict": _dimension_verdict(score),
            "reason_codes": _reason_codes_for_dimension(data, dimension),
        }
    verdict = _overall_verdict(scores, missing)
    normalized = {
        "schema_version": P7_BLIND_QA_REVIEW_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_BLIND_QA_MATERIAL_STEP,
        "review_kind": "ratings_only_blind_qa_review",
        "review_id": clean_identifier(data.get("review_id") or data.get("id"), default="review", max_length=96),
        "candidate_id": clean_identifier(data.get("candidate_id"), default="candidate", max_length=180),
        "reviewer_id_hash": clean_identifier(data.get("reviewer_id_hash"), default="reviewer_hash_required", max_length=120),
        "dimensions": dimensions,
        "dimension_scores": scores,
        "missing_dimensions": dedupe_identifiers(missing, limit=80),
        "verdict": verdict,
        "reason_codes": dedupe_identifiers(data.get("reason_codes"), limit=20, max_length=80),
        "ratings_only_payload": True,
        "reviewer_free_text_included": False,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "read_feeling_auto_estimation_allowed": False,
        "public_contract": public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True),
        "body_free": True,
        "release_allowed": False,
    }
    assert_p7_blind_qa_review_contract(normalized)
    return normalized


def apply_p7_blind_qa_review_to_scorecard_row(row: Mapping[str, Any], review: Mapping[str, Any]) -> dict[str, Any]:
    """Return a scorecard row copy with ratings reflected from a normalized review."""

    assert_p7_scorecard_row_contract(row)
    normalized = normalize_p7_blind_qa_review(review) if review.get("schema_version") != P7_BLIND_QA_REVIEW_SCHEMA_VERSION else dict(review)
    assert_p7_blind_qa_review_contract(normalized)
    updated = dict(row)
    missing = dedupe_identifiers(normalized.get("missing_dimensions"), limit=80)
    scores = safe_mapping(normalized.get("dimension_scores"))
    updated["ratings"] = {
        "blind_qa_required": True,
        "blind_qa_completed": bool(not missing and set(scores) == set(P7_BLIND_QA_DIMENSIONS)),
        "rating_required": bool(missing),
        "dimension_scores": {dimension: float(scores[dimension]) for dimension in P7_BLIND_QA_DIMENSIONS if dimension in scores},
        "missing_dimensions": missing,
        "rating_required_dimensions": list(P7_BLIND_QA_DIMENSIONS),
        "review_id": clean_identifier(normalized.get("review_id"), default="review", max_length=96),
        "review_verdict": clean_identifier(normalized.get("verdict"), default="YELLOW", max_length=40),
    }
    updated["release_allowed"] = False
    assert_p7_scorecard_row_contract(updated)
    return updated


def build_p7_blind_qa_material(
    scorecard_rows: Sequence[Mapping[str, Any]] | None = None,
    *,
    reviews: Sequence[Mapping[str, Any]] | None = None,
    material_id: Any = "p7_blind_qa_material",
) -> dict[str, Any]:
    """Build P7-6 material export from P7 scorecard rows and optional reviews."""

    rows = list(scorecard_rows or [])
    for index, row in enumerate(rows, start=1):
        assert_p7_scorecard_row_contract(row)
        assert_p7_no_body_payload_or_contract_mutation(row, source=f"p7_blind_qa_material.scorecard_rows[{index}]")
    candidates = [build_p7_blind_qa_candidate(row, candidate_index=index) for index, row in enumerate(rows, start=1)]
    normalized_reviews = [normalize_p7_blind_qa_review(review) for review in list(reviews or [])]
    review_by_candidate = {review["candidate_id"]: review for review in normalized_reviews}

    missing_counter: Counter[str] = Counter()
    review_missing_count = 0
    review_completed_count = 0
    candidate_rows: list[dict[str, Any]] = []
    for candidate in candidates:
        candidate_row = dict(candidate)
        review = review_by_candidate.get(candidate["candidate_id"])
        if review is not None:
            review_missing = dedupe_identifiers(review.get("missing_dimensions"), limit=80)
            review_scores = safe_mapping(review.get("dimension_scores"))
            candidate_row["dimension_scores"] = {
                dimension: float(review_scores[dimension])
                for dimension in P7_BLIND_QA_DIMENSIONS
                if dimension in review_scores and _float_score(review_scores.get(dimension)) is not None
            }
            candidate_row["missing_dimensions"] = review_missing
            candidate_row["review_id"] = clean_identifier(review.get("review_id"), default="review", max_length=96)
            candidate_row["review_verdict"] = clean_identifier(review.get("verdict"), default="YELLOW", max_length=40)
            candidate_row["review_reason_codes"] = dedupe_identifiers(review.get("reason_codes"), limit=20, max_length=80)
            if not review_missing:
                candidate_row["review_status"] = "review_completed"
                candidate_row["rating_required"] = False
                review_completed_count += 1
            else:
                candidate_row["review_status"] = "review_partial"
                candidate_row["rating_required"] = True
                review_missing_count += 1
        else:
            if candidate.get("review_status") == "review_completed":
                review_completed_count += 1
            else:
                review_missing_count += 1
        for dimension in candidate_row.get("missing_dimensions", []):
            missing_counter[clean_identifier(dimension, max_length=80)] += 1
        candidate_rows.append(candidate_row)

    hold_seed = [ref for candidate in candidate_rows for ref in candidate.get("hold_refs", [])]
    if review_missing_count:
        hold_seed.extend(P7_INITIAL_HOLD_IDS[:1])
    unresolved_hold_refs = dedupe_identifiers(hold_seed, limit=120)
    unresolved_red_refs = dedupe_identifiers(
        [ref for candidate in candidate_rows for ref in candidate.get("red_refs", [])], limit=120
    )
    blind_qa_completed = bool(candidate_rows and review_missing_count == 0 and review_completed_count == len(candidate_rows))
    summary = {
        "blind_qa_required": True,
        "blind_qa_completed": blind_qa_completed,
        "candidate_count": len(candidate_rows),
        "reviewed_candidate_count": review_completed_count + max(0, len(normalized_reviews) - review_completed_count),
        "review_completed_count": review_completed_count,
        "missing_review_candidate_count": review_missing_count,
        "rating_required": not blind_qa_completed,
        "review_missing": (not blind_qa_completed),
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "release_allowed": False,
    }
    material = {
        "schema_version": P7_BLIND_QA_MATERIAL_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_BLIND_QA_MATERIAL_STEP,
        "scope": P7_BLIND_QA_MATERIAL_SCOPE,
        "material_id": clean_identifier(material_id, default="p7_blind_qa_material", max_length=120),
        "source_scorecard_schema_version": P7_SCORECARD_ROW_SCHEMA_VERSION,
        "candidate_schema_version": P7_BLIND_QA_CANDIDATE_SCHEMA_VERSION,
        "review_schema_version": P7_BLIND_QA_REVIEW_SCHEMA_VERSION,
        "dimensions": list(P7_BLIND_QA_DIMENSIONS),
        "candidate_count": len(candidate_rows),
        "review_count": len(normalized_reviews),
        "review_completed_count": review_completed_count,
        "review_missing_count": review_missing_count,
        "summary": summary,
        "missing_dimension_counts": {dimension: missing_counter.get(dimension, 0) for dimension in P7_BLIND_QA_DIMENSIONS},
        "human_qa_hold_refs": [ref for ref in unresolved_hold_refs if ref.startswith("P7-HOLD-")],
        "unresolved_red_refs": unresolved_red_refs,
        "unresolved_hold_refs": unresolved_hold_refs,
        "candidates": candidate_rows,
        "reviews": normalized_reviews,
        "rating_unreviewed_dimensions_status": "review_missing" if review_missing_count else "review_completed",
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "read_feeling_auto_estimation_allowed": False,
        "reviewer_free_text_included": False,
        "public_contract": public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True),
        "body_free": True,
        "release_allowed": False,
    }
    material["human_qa_material_index"] = _human_qa_index_from_blind_material(
        material,
        material_id=f"{material['material_id']}:p5_human_qa",
    )
    assert_p7_blind_qa_material_contract(material)
    return material


def assert_p7_human_qa_material_index_contract(index: Mapping[str, Any]) -> bool:
    data = safe_mapping(index)
    if data.get("schema_version") != P7_HUMAN_QA_MATERIAL_INDEX_SCHEMA_VERSION:
        raise ValueError("unexpected P7 human QA material index schema_version")
    if data.get("phase") != P7_PHASE:
        raise ValueError("unexpected P7 human QA material index phase")
    if data.get("qa_scope") != P7_HUMAN_QA_SCOPE:
        raise ValueError("P7 human QA material index scope changed")
    if list(data.get("dimensions_required") or []) != list(P7_HUMAN_QA_DIMENSIONS):
        raise ValueError("P7 human QA material index dimension set changed")
    if data.get("release_allowed") is not False or data.get("body_free") is not True:
        raise ValueError("P7 human QA material index must be body-free and release-closed")
    for key in (
        "local_body_review_packet_release_material",
        "raw_input_included_in_scorecard",
        "comment_text_body_included_in_scorecard",
        "reviewer_free_text_included_in_scorecard",
        "reviewer_free_text_included",
        "raw_input_included",
        "comment_text_body_included",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7 human QA material index must keep {key}=False")
    for key in ("scorecard_body_free", "release_material_body_free"):
        if data.get(key) is not True:
            raise ValueError(f"P7 human QA material index must keep {key}=True")
    unresolved = dedupe_identifiers(data.get("unresolved_hold_refs"), limit=20, max_length=80)
    if data.get("p5_human_qa_completed") is not True and "P7-HOLD-001" not in unresolved:
        raise ValueError("P7-HOLD-001 must remain when P5 human QA is not complete")
    if data.get("p5_human_qa_completed") is True and unresolved:
        raise ValueError("P5 human QA completed index must not keep unresolved hold refs")
    assert_false_markers(safe_mapping(data.get("public_contract")), source="p7_human_qa_material_index.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_human_qa_material_index.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_human_qa_material_index")
    return True


def assert_p7_human_qa_review_summary_contract(summary: Mapping[str, Any]) -> bool:
    data = safe_mapping(summary)
    if data.get("schema_version") != P7_HUMAN_QA_REVIEW_SUMMARY_SCHEMA_VERSION:
        raise ValueError("unexpected P7 human QA review summary schema_version")
    if data.get("phase") != P7_PHASE:
        raise ValueError("unexpected P7 human QA review summary phase")
    if data.get("release_allowed") is not False or data.get("body_free") is not True:
        raise ValueError("P7 human QA review summary must be body-free and release-closed")
    if data.get("review_status") not in _ALLOWED_REVIEW_STATUSES:
        raise ValueError("P7 human QA review summary status changed")
    scores = safe_mapping(data.get("dimension_scores"))
    if not set(scores).issubset(set(P7_HUMAN_QA_DIMENSIONS)):
        raise ValueError("P7 human QA review summary has unsupported dimensions")
    for value in scores.values():
        if not isinstance(value, (int, float)) or value < 0 or value > 1:
            raise ValueError("P7 human QA review summary scores must be 0..1 numbers")
    if data.get("reviewer_free_text_included") is not False:
        raise ValueError("P7 human QA review summary must not include reviewer free text")
    if data.get("raw_input_included") is not False or data.get("comment_text_body_included") is not False:
        raise ValueError("P7 human QA review summary must not include source bodies")
    assert_false_markers(safe_mapping(data.get("public_contract")), source="p7_human_qa_review_summary.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_human_qa_review_summary.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_human_qa_review_summary")
    return True


def assert_p7_blind_qa_candidate_contract(candidate: Mapping[str, Any]) -> bool:
    data = safe_mapping(candidate)
    if data.get("schema_version") != P7_BLIND_QA_CANDIDATE_SCHEMA_VERSION:
        raise ValueError("unexpected P7 Blind QA candidate schema_version")
    if data.get("phase") != P7_PHASE or data.get("step") != P7_BLIND_QA_MATERIAL_STEP:
        raise ValueError("unexpected P7 Blind QA candidate phase/step")
    if data.get("release_allowed") is not False or data.get("body_free") is not True:
        raise ValueError("P7 Blind QA candidate must be body-free and release-closed")
    if data.get("source_scorecard_schema_version") != P7_SCORECARD_ROW_SCHEMA_VERSION:
        raise ValueError("P7 Blind QA candidate must come from P7ScorecardRowV1")
    if data.get("review_status") not in _ALLOWED_REVIEW_STATUSES:
        raise ValueError("P7 Blind QA candidate review_status changed")
    if data.get("reviewer_free_text_included") is not False:
        raise ValueError("P7 Blind QA candidate must not include reviewer free text")
    if data.get("machine_metrics_used_for_read_feeling") is not False:
        raise ValueError("P7 Blind QA candidate must not use machine metrics for read_feeling")
    if data.get("read_feeling_auto_filled_from_machine_metrics") is not False:
        raise ValueError("P7 Blind QA candidate must not auto-fill read_feeling")
    if list(data.get("dimensions_required") or []) != list(P7_BLIND_QA_DIMENSIONS):
        raise ValueError("P7 Blind QA candidate dimension set changed")
    assert_false_markers(safe_mapping(data.get("public_contract")), source="p7_blind_qa_candidate.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_blind_qa_candidate.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_blind_qa_candidate")
    return True


def assert_p7_blind_qa_review_contract(review: Mapping[str, Any]) -> bool:
    data = safe_mapping(review)
    if data.get("schema_version") != P7_BLIND_QA_REVIEW_SCHEMA_VERSION:
        raise ValueError("unexpected P7 Blind QA review schema_version")
    if data.get("phase") != P7_PHASE or data.get("step") != P7_BLIND_QA_MATERIAL_STEP:
        raise ValueError("unexpected P7 Blind QA review phase/step")
    if data.get("release_allowed") is not False or data.get("body_free") is not True:
        raise ValueError("P7 Blind QA review must be body-free and release-closed")
    if data.get("reviewer_free_text_included") is not False:
        raise ValueError("P7 Blind QA review must not include reviewer free text")
    if data.get("machine_metrics_used_for_read_feeling") is not False:
        raise ValueError("P7 Blind QA review must not use machine metrics for read_feeling")
    if clean_identifier(data.get("verdict"), default="") not in _ALLOWED_VERDICTS:
        raise ValueError("P7 Blind QA review verdict changed")
    dimensions = safe_mapping(data.get("dimensions"))
    if set(dimensions) != set(P7_BLIND_QA_DIMENSIONS):
        raise ValueError("P7 Blind QA review dimension set changed")
    for dimension, payload in dimensions.items():
        item = safe_mapping(payload)
        if clean_identifier(dimension) not in P7_BLIND_QA_DIMENSIONS:
            raise ValueError("unsupported P7 Blind QA dimension")
        score = item.get("score")
        if score is not None and (not isinstance(score, (int, float)) or score < 0 or score > 1):
            raise ValueError("P7 Blind QA review score must be None or a 0..1 number")
        if clean_identifier(item.get("verdict"), default="") not in _ALLOWED_VERDICTS:
            raise ValueError("P7 Blind QA dimension verdict changed")
        if not isinstance(item.get("reason_codes"), list):
            raise ValueError("P7 Blind QA review reason_codes must be list-only")
    assert_false_markers(safe_mapping(data.get("public_contract")), source="p7_blind_qa_review.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_blind_qa_review.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_blind_qa_review")
    return True


def assert_p7_blind_qa_material_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    if data.get("schema_version") != P7_BLIND_QA_MATERIAL_SCHEMA_VERSION:
        raise ValueError("unexpected P7 Blind QA material schema_version")
    if data.get("phase") != P7_PHASE or data.get("scope") != P7_BLIND_QA_MATERIAL_SCOPE:
        raise ValueError("unexpected P7 Blind QA material phase/scope")
    if data.get("release_allowed") is not False or data.get("body_free") is not True:
        raise ValueError("P7 Blind QA material must be body-free and release-closed")
    if data.get("source_scorecard_schema_version") != P7_SCORECARD_ROW_SCHEMA_VERSION:
        raise ValueError("P7 Blind QA material must source P7ScorecardRowV1")
    if list(data.get("dimensions") or []) != list(P7_BLIND_QA_DIMENSIONS):
        raise ValueError("P7 Blind QA material dimension set changed")
    if data.get("machine_metrics_used_for_read_feeling") is not False:
        raise ValueError("P7 Blind QA material must not use machine metrics for read_feeling")
    if data.get("read_feeling_auto_filled_from_machine_metrics") is not False:
        raise ValueError("P7 Blind QA material must not auto-fill read_feeling")
    if data.get("reviewer_free_text_included") is not False:
        raise ValueError("P7 Blind QA material must not include reviewer free text")
    assert_false_markers(safe_mapping(data.get("public_contract")), source="p7_blind_qa_material.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_blind_qa_material.body_free_markers")
    candidates = data.get("candidates")
    if not isinstance(candidates, list):
        raise ValueError("P7 Blind QA material candidates must be a list")
    for candidate in candidates:
        assert_p7_blind_qa_candidate_contract(safe_mapping(candidate))
    reviews = data.get("reviews")
    if not isinstance(reviews, list):
        raise ValueError("P7 Blind QA material reviews must be a list")
    for review in reviews:
        assert_p7_blind_qa_review_contract(safe_mapping(review))
    if "human_qa_material_index" in data:
        assert_p7_human_qa_material_index_contract(safe_mapping(data.get("human_qa_material_index")))
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_blind_qa_material")
    return True


__all__ = [
    "P7_BLIND_QA_CANDIDATE_SCHEMA_VERSION",
    "P7_BLIND_QA_DIMENSIONS",
    "P7_BLIND_QA_MATERIAL_SCHEMA_VERSION",
    "P7_BLIND_QA_MATERIAL_STEP",
    "P7_BLIND_QA_REVIEW_SCHEMA_VERSION",
    "P7_HUMAN_QA_DIMENSIONS",
    "P7_HUMAN_QA_MATERIAL_INDEX_SCHEMA_VERSION",
    "P7_HUMAN_QA_REVIEW_SUMMARY_SCHEMA_VERSION",
    "apply_p7_blind_qa_review_to_scorecard_row",
    "assert_p7_blind_qa_candidate_contract",
    "assert_p7_blind_qa_material_contract",
    "assert_p7_blind_qa_review_contract",
    "assert_p7_human_qa_material_index_contract",
    "assert_p7_human_qa_review_summary_contract",
    "build_p7_blind_qa_candidate",
    "build_p7_blind_qa_material",
    "build_p7_human_qa_material_index",
    "build_p7_human_qa_review_summary",
    "normalize_p7_blind_qa_review",
]
