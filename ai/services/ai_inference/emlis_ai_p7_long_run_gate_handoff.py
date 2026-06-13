# -*- coding: utf-8 -*-
"""P7-7 Long-run Product Gate candidate material.

P7-7 converts P7 scorecard rows and ratings-only Blind QA material into a
body-free candidate for the existing Long-run Product Gate layer.  The candidate
can say that long-run *material* is ready, but P7 still keeps red/HOLD/release
judgment separate and never applies release or public Product Gate state.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from typing import Any, Final

from emlis_ai_p7_blind_qa_material import (
    P7_BLIND_QA_MATERIAL_SCHEMA_VERSION,
    P7_HUMAN_QA_MATERIAL_INDEX_SCHEMA_VERSION,
    assert_p7_blind_qa_material_contract,
    assert_p7_human_qa_material_index_contract,
    build_p7_blind_qa_material,
    build_p7_human_qa_material_index,
)
from emlis_ai_p7_contracts import (
    P7_PHASE,
    assert_false_markers,
    assert_p7_no_body_payload_or_contract_mutation,
    body_free_flags,
    clean_identifier,
    dedupe_identifiers,
    public_contract_flags,
    safe_mapping,
)
from emlis_ai_p7_evaluation_matrix import (
    P7_EVALUATION_MATRIX_SCHEMA_VERSION,
    P7_VERDICTS,
    aggregate_p7_scorecard_rows_by_family_sequence,
)
from emlis_ai_p7_event_bridge import P7_SCORECARD_ROW_SCHEMA_VERSION, assert_p7_scorecard_row_contract
from emlis_ai_product_readfeel_long_run_product_gate import (
    PRODUCT_READFEEL_LONG_RUN_PRODUCT_GATE_STEP,
    PRODUCT_READFEEL_LONG_RUN_PRODUCT_GATE_VERSION,
)

P7_LONG_RUN_GATE_HANDOFF_SCHEMA_VERSION: Final = "cocolon.emlis.p7.long_run_gate_handoff.v1"
P7_LONG_RUN_GATE_HANDOFF_STEP: Final = "P7-7_LongRunProductGateCandidateMaterial_20260612"
P7_LONG_RUN_GATE_HANDOFF_SCOPE: Final = "P7_long_run_product_gate_candidate_material"

_ALLOWED_STATUSES: Final[frozenset[str]] = frozenset({"blocked", "review_required", "candidate_material_ready"})
_HISTORY_LINE_FAMILIES: Final[frozenset[str]] = frozenset(
    {"history_line_eligible", "long_meaning_arc", "relationship_gratitude_recovery", "change_future_intention"}
)


def _as_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "" or isinstance(value, bool):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _quality_flags(row: Mapping[str, Any]) -> dict[str, bool]:
    flags = safe_mapping(row.get("quality_flags"))
    return {str(key): bool(value) for key, value in flags.items()}


def _sequence(row: Mapping[str, Any]) -> dict[str, Any]:
    return safe_mapping(row.get("sequence"))


def _sequence_length(row: Mapping[str, Any]) -> int:
    return max(1, _as_int(_sequence(row).get("sequence_length"), 1))


def _sequence_id(row: Mapping[str, Any]) -> str:
    return clean_identifier(_sequence(row).get("sequence_id"), default=f"sequence_{_sequence_length(row)}", max_length=96)


def _family(row: Mapping[str, Any]) -> str:
    return clean_identifier(row.get("family"), default="unknown", max_length=120)


def _row_id(row: Mapping[str, Any]) -> str:
    return clean_identifier(row.get("row_id"), default="row", max_length=120)


def _signature_key(row: Mapping[str, Any]) -> str:
    """Return a body-free surface signature key.

    P7 accepts an explicit signature id when a lower layer already produced one;
    otherwise it uses non-body identifiers and counters.  This avoids treating a
    sequence as repetitive merely because several rows share the same family.
    """

    explicit = clean_identifier(row.get("surface_signature_key") or row.get("surface_signature_id"), default="", max_length=160)
    if explicit:
        return explicit
    display = safe_mapping(row.get("display_contract"))
    flags = _quality_flags(row)
    flag_ids = "+".join(sorted(key for key, value in flags.items() if value)) or "no_flags"
    length = _as_int(display.get("comment_text_length"), 0)
    length_bucket = "len_0" if length <= 0 else ("len_1_80" if length <= 80 else ("len_81_160" if length <= 160 else "len_161_plus"))
    return ":".join([_family(row), _sequence_id(row), _row_id(row), length_bucket, flag_ids])


def _sequence_coverage(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    sequence_counter: Counter[str] = Counter(_sequence_id(row) for row in rows)
    sequence_lengths = sorted({_sequence_length(row) for row in rows})
    return {
        "sequence_ids": sorted(sequence_counter),
        "sequence_counts": {key: value for key, value in sorted(sequence_counter.items())},
        "sequence_lengths": sequence_lengths,
        "sequence_1_present": bool(sequence_counter.get("sequence_1")),
        "sequence_3_present": bool(sequence_counter.get("sequence_3")),
        "sequence_7_present": bool(sequence_counter.get("sequence_7")),
        "max_sequence_length": max(sequence_lengths) if sequence_lengths else 0,
    }


def _row_average_score(row: Mapping[str, Any], blind_scores_by_row_id: Mapping[str, float] | None = None) -> float | None:
    row_id = _row_id(row)
    blind_scores = safe_mapping(blind_scores_by_row_id)
    if row_id in blind_scores and isinstance(blind_scores[row_id], (int, float)):
        return float(blind_scores[row_id])
    ratings = safe_mapping(row.get("ratings"))
    scores = [float(value) for value in safe_mapping(ratings.get("dimension_scores")).values() if isinstance(value, (int, float))]
    if not scores:
        return None
    return round(sum(scores) / len(scores), 6)


def _blind_average_scores_by_row_id(blind_qa_material: Mapping[str, Any]) -> dict[str, float]:
    scores_by_row: dict[str, float] = {}
    for candidate in blind_qa_material.get("candidates", []) if isinstance(blind_qa_material.get("candidates"), list) else []:
        item = safe_mapping(candidate)
        row_id = clean_identifier(item.get("source_scorecard_row_id"), default="", max_length=120)
        scores = [float(value) for value in safe_mapping(item.get("dimension_scores")).values() if isinstance(value, (int, float))]
        if row_id and scores:
            scores_by_row[row_id] = round(sum(scores) / len(scores), 6)
    return scores_by_row


def _history_line_value_report(rows: Sequence[Mapping[str, Any]], blind_scores_by_row_id: Mapping[str, float] | None = None) -> dict[str, Any]:
    by_length: dict[int, list[float]] = defaultdict(list)
    eligible_count = 0
    for row in rows:
        sequence = _sequence(row)
        if sequence.get("history_line_eligible") is True or _family(row) in _HISTORY_LINE_FAMILIES:
            eligible_count += 1
            score = _row_average_score(row, blind_scores_by_row_id)
            if score is not None:
                by_length[_sequence_length(row)].append(score)
    avg_by_length = {
        length: round(sum(scores) / len(scores), 6)
        for length, scores in by_length.items()
        if scores
    }
    score_1 = avg_by_length.get(1)
    score_3 = avg_by_length.get(3)
    score_7 = avg_by_length.get(7)
    value_1_to_3 = bool(score_1 is not None and score_3 is not None and score_3 > score_1)
    value_3_to_7 = bool(score_3 is not None and score_7 is not None and score_7 >= score_3)
    risk_rows = 0
    for row in rows:
        if _sequence(row).get("history_line_eligible") is True or _family(row) in _HISTORY_LINE_FAMILIES:
            flags = _quality_flags(row)
            if flags.get("creepy_risk_detected") or flags.get("overclaim_risk_detected"):
                risk_rows += 1
    long_sequence_scores = [
        score
        for row in rows
        if (_sequence(row).get("history_line_eligible") is True or _family(row) in _HISTORY_LINE_FAMILIES)
        and _sequence_length(row) >= 7
        for score in [_row_average_score(row, blind_scores_by_row_id)]
        if score is not None
    ]
    long_sequence_candidate_observed = bool(len(long_sequence_scores) >= 3 and sum(long_sequence_scores) / len(long_sequence_scores) >= 0.8)
    observed = bool(((value_1_to_3 and value_3_to_7) or long_sequence_candidate_observed) and risk_rows == 0)
    return {
        "history_line_eligible_row_count": eligible_count,
        "sequence_history_line_eligible_row_count": sum(
            1 for row in rows if (_sequence(row).get("history_line_eligible") is True or _family(row) in _HISTORY_LINE_FAMILIES) and _sequence_length(row) >= 3
        ),
        "average_score_by_sequence_length": {str(length): score for length, score in sorted(avg_by_length.items())},
        "value_increase_1_to_3_observed": value_1_to_3,
        "value_increase_3_to_7_observed": value_3_to_7,
        "long_sequence_candidate_observed": long_sequence_candidate_observed,
        "history_line_value_increase_observed": observed,
        "history_line_risk_row_count": risk_rows,
    }


def _surface_repetition_report(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    signatures = [_signature_key(row) for row in rows]
    counts = Counter(signatures)
    repeated = sorted(key for key, value in counts.items() if value > 1)
    repeat_count = sum(max(0, value - 1) for value in counts.values())
    return {
        "surface_signature_count": len(signatures),
        "unique_surface_signature_count": len(counts),
        "repeat_count": repeat_count,
        "repetition_detected": repeat_count > 0,
        "surface_signature_repeat_rate": round(repeat_count / len(signatures), 6) if signatures else 0.0,
        "repeated_signature_ids": repeated,
    }


def _risk_report(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    mirror = creepy = overclaim = unsafe = template = p6_violation = 0
    for row in rows:
        flags = _quality_flags(row)
        mirror += int(flags.get("mirror_only_detected") is True)
        creepy += int(flags.get("creepy_risk_detected") is True)
        overclaim += int(flags.get("overclaim_risk_detected") is True)
        unsafe += int(flags.get("unsafe_claim_detected") is True)
        template += int(flags.get("template_major_detected") is True)
        p6 = safe_mapping(row.get("p6"))
        if _family(row) != "structure_question" and p6.get("visible_applied") is True:
            p6_violation += 1
    return {
        "mirror_only_detected_count": mirror,
        "creepy_risk_detected_count": creepy,
        "overclaim_risk_detected_count": overclaim,
        "unsafe_claim_detected_count": unsafe,
        "template_major_detected_count": template,
        "p6_visible_expansion_violation_count": p6_violation,
        "p6_overclaim_or_creepy_risk_present": bool(creepy or overclaim or unsafe),
    }


def _required_followup_fixes(
    *,
    red_refs: Sequence[str],
    hold_refs: Sequence[str],
    blind_qa: Mapping[str, Any],
    sequence_coverage: Mapping[str, Any],
    history_line: Mapping[str, Any],
    repetition: Mapping[str, Any],
    risks: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
    human_qa_index: Mapping[str, Any] | None = None,
) -> list[str]:
    fixes: list[str] = []
    if not rows:
        fixes.append("scorecard_rows_missing")
    if red_refs:
        fixes.append("unresolved_red_refs_present")
    if hold_refs:
        fixes.append("unresolved_hold_refs_present")
    if _as_int(blind_qa.get("review_missing_count"), 0) > 0:
        fixes.append("blind_qa_review_missing")
    if safe_mapping(human_qa_index).get("p5_human_qa_completed") is not True:
        fixes.append("p5_human_qa_review_required")
    if sequence_coverage.get("sequence_7_present") is not True:
        fixes.append("sequence_7_long_run_not_observed")
    if history_line.get("history_line_value_increase_observed") is not True:
        fixes.append("p5_history_line_value_increase_not_observed")
        fixes.append("p5_history_line_sequence_value_not_increased")
        if history_line.get("value_increase_1_to_3_observed") is not True:
            fixes.append("history_line_value_not_higher_at_sequence_3")
        if history_line.get("value_increase_3_to_7_observed") is not True:
            fixes.append("history_line_value_not_maintained_at_sequence_7")
    if repetition.get("repetition_detected") is True:
        fixes.append("surface_signature_repetition_detected")
    if _as_int(risks.get("mirror_only_detected_count"), 0) > 0:
        fixes.append("mirror_only_detected")
    if _as_int(risks.get("creepy_risk_detected_count"), 0) > 0:
        fixes.append("creepy_risk_detected")
    if _as_int(risks.get("overclaim_risk_detected_count"), 0) > 0:
        fixes.append("p6_overclaim_risk_detected")
    if _as_int(risks.get("unsafe_claim_detected_count"), 0) > 0:
        fixes.append("p6_unsafe_claim_risk_detected")
    if _as_int(risks.get("template_major_detected_count"), 0) > 0:
        fixes.append("template_major_detected")
    if _as_int(risks.get("p6_visible_expansion_violation_count"), 0) > 0:
        fixes.append("p6_visible_expansion_violation")
    return dedupe_identifiers(fixes, limit=60, max_length=120)


def _followup_targets(fixes: Sequence[str]) -> list[str]:
    targets: list[str] = []
    fix_set = set(fixes)
    if {"p5_history_line_value_increase_not_observed", "p5_history_line_sequence_value_not_increased", "history_line_value_not_higher_at_sequence_3", "creepy_risk_detected"} & fix_set:
        targets.append("P5_User_Label_Connection")
    if {"p6_overclaim_risk_detected", "p6_unsafe_claim_risk_detected", "p6_visible_expansion_violation"} & fix_set:
        targets.append("P6_Structure_Insight")
    if {"blind_qa_review_missing", "p5_human_qa_review_required", "unresolved_hold_refs_present"} & fix_set:
        targets.append("P7_RatingsOnly_Blind_QA")
    if {"surface_signature_repetition_detected", "mirror_only_detected", "template_major_detected"} & fix_set:
        targets.append("P7_ProductQualityRunner_LongRunGate")
    if "unresolved_red_refs_present" in fix_set:
        targets.append("P7_Red_Ledger")
    return dedupe_identifiers(targets, limit=16, max_length=120)


def _candidate_status(*, red_refs: Sequence[str], fixes: Sequence[str]) -> str:
    hard_fixes = {
        "unresolved_red_refs_present",
        "surface_signature_repetition_detected",
        "mirror_only_detected",
        "creepy_risk_detected",
        "p6_overclaim_risk_detected",
        "p6_unsafe_claim_risk_detected",
        "template_major_detected",
        "p6_visible_expansion_violation",
    }
    if red_refs or (set(fixes) & hard_fixes):
        return "blocked"
    if fixes:
        return "review_required"
    return "candidate_material_ready"


def build_p7_long_run_gate_handoff(
    scorecard_rows: Sequence[Mapping[str, Any]] | None = None,
    *,
    blind_qa_material: Mapping[str, Any] | None = None,
    human_qa_material_index: Mapping[str, Any] | None = None,
    material_id: Any = "p7_long_run_gate_handoff",
) -> dict[str, Any]:
    """Build body-free P7 Long-run Product Gate candidate handoff material."""

    rows = list(scorecard_rows or [])
    for index, row in enumerate(rows, start=1):
        assert_p7_scorecard_row_contract(row)
        assert_p7_no_body_payload_or_contract_mutation(row, source=f"p7_long_run_gate_handoff.scorecard_rows[{index}]")
    blind = safe_mapping(blind_qa_material) if blind_qa_material is not None else build_p7_blind_qa_material(rows)
    assert_p7_blind_qa_material_contract(blind)
    human_qa_index = (
        safe_mapping(human_qa_material_index)
        if human_qa_material_index is not None
        else safe_mapping(blind.get("human_qa_material_index"))
    )
    if not human_qa_index:
        human_qa_index = build_p7_human_qa_material_index(blind_qa_material=blind)
    assert_p7_human_qa_material_index_contract(human_qa_index)

    aggregation = aggregate_p7_scorecard_rows_by_family_sequence(rows)
    verdict_counts = safe_mapping(aggregation.get("overall_verdict_counts"))
    row_red_refs = [ref for row in rows for ref in row.get("red_refs", [])]
    red_refs = dedupe_identifiers(row_red_refs, limit=120)
    hold_refs = dedupe_identifiers([ref for row in rows for ref in row.get("hold_refs", [])], limit=120)
    blocker_refs = dedupe_identifiers([ref for row in rows for ref in row.get("blocker_refs", [])], limit=120)
    sequence_coverage = _sequence_coverage(rows)
    history_line = _history_line_value_report(rows, _blind_average_scores_by_row_id(blind))
    repetition = _surface_repetition_report(rows)
    risks = _risk_report(rows)
    fixes = _required_followup_fixes(
        red_refs=red_refs,
        hold_refs=hold_refs,
        blind_qa=blind,
        sequence_coverage=sequence_coverage,
        history_line=history_line,
        repetition=repetition,
        risks=risks,
        rows=rows,
        human_qa_index=human_qa_index,
    )
    material_ready = bool(
        rows
        and sequence_coverage.get("sequence_7_present") is True
        and _as_int(blind.get("review_missing_count"), 0) == 0
        and human_qa_index.get("p5_human_qa_completed") is True
        and history_line.get("history_line_value_increase_observed") is True
        and repetition.get("repetition_detected") is not True
        and not risks.get("p6_overclaim_or_creepy_risk_present")
        and _as_int(risks.get("mirror_only_detected_count"), 0) == 0
        and _as_int(risks.get("template_major_detected_count"), 0) == 0
        and _as_int(risks.get("p6_visible_expansion_violation_count"), 0) == 0
    )
    status = _candidate_status(red_refs=red_refs, fixes=fixes)
    long_run_ready = bool(material_ready and status == "candidate_material_ready" and not red_refs and not hold_refs)
    candidate = {
        "candidate_schema_version": "cocolon.emlis.p7.long_run_gate_candidate.v1",
        "candidate_id": clean_identifier(material_id, default="p7_long_run_gate_handoff", max_length=120),
        "candidate_status": status,
        "candidate_material_ready": material_ready,
        "long_run_candidate_ready": long_run_ready,
        "long_run_candidate_is_release_ready": False,
        "product_pass_is_release_ready": False,
        "row_count": len(rows),
        "red_refs": red_refs,
        "hold_refs": hold_refs,
        "blocker_refs": blocker_refs,
        "review_missing_count": _as_int(blind.get("review_missing_count"), 0),
        "review_completed_count": _as_int(blind.get("review_completed_count"), 0),
        "p5_human_qa_completed": human_qa_index.get("p5_human_qa_completed") is True,
        "p5_human_qa_review_status": clean_identifier(human_qa_index.get("human_qa_review_status"), default="review_required", max_length=80),
        "p5_human_qa_hold_refs": dedupe_identifiers(human_qa_index.get("unresolved_hold_refs"), limit=20, max_length=80),
        "sequence_coverage": sequence_coverage,
        "history_line_value_report": history_line,
        "surface_repetition_report": repetition,
        "risk_report": risks,
        "required_followup_fixes": fixes,
        "required_followup_targets": _followup_targets(fixes),
        "release_allowed": False,
        "product_gate_ready": False,
        "public_release_applied": False,
        "body_free": True,
    }
    handoff = {
        "schema_version": P7_LONG_RUN_GATE_HANDOFF_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_LONG_RUN_GATE_HANDOFF_STEP,
        "scope": P7_LONG_RUN_GATE_HANDOFF_SCOPE,
        "material_id": clean_identifier(material_id, default="p7_long_run_gate_handoff", max_length=120),
        "source_scorecard_schema_version": P7_SCORECARD_ROW_SCHEMA_VERSION,
        "source_evaluation_matrix_schema_version": P7_EVALUATION_MATRIX_SCHEMA_VERSION,
        "source_blind_qa_material_schema_version": P7_BLIND_QA_MATERIAL_SCHEMA_VERSION,
        "source_human_qa_material_index_schema_version": P7_HUMAN_QA_MATERIAL_INDEX_SCHEMA_VERSION,
        "handoff_target_module": "emlis_ai_product_readfeel_long_run_product_gate",
        "handoff_target_schema_version": PRODUCT_READFEEL_LONG_RUN_PRODUCT_GATE_VERSION,
        "handoff_target_step": PRODUCT_READFEEL_LONG_RUN_PRODUCT_GATE_STEP,
        "row_count": len(rows),
        "verdict_counts": {verdict: _as_int(verdict_counts.get(verdict), 0) for verdict in P7_VERDICTS},
        "sequence_coverage": sequence_coverage,
        "history_line_metrics": history_line,
        "risk_metrics": {
            "surface_signature_repeat_count": repetition["repeat_count"],
            "surface_signature_repetition_detected": repetition["repetition_detected"],
            **risks,
        },
        "blind_qa_summary": {
            "candidate_count": _as_int(blind.get("candidate_count"), 0),
            "review_count": _as_int(blind.get("review_count"), 0),
            "review_completed_count": _as_int(blind.get("review_completed_count"), 0),
            "review_missing_count": _as_int(blind.get("review_missing_count"), 0),
            "rating_unreviewed_dimensions_status": clean_identifier(blind.get("rating_unreviewed_dimensions_status"), default="review_missing", max_length=80),
            "p5_human_qa_completed": human_qa_index.get("p5_human_qa_completed") is True,
            "p5_human_qa_review_status": clean_identifier(human_qa_index.get("human_qa_review_status"), default="review_required", max_length=80),
            "p5_human_qa_hold_refs": dedupe_identifiers(human_qa_index.get("unresolved_hold_refs"), limit=20, max_length=80),
            "p5_human_qa_local_body_review_packet_release_material": human_qa_index.get("local_body_review_packet_release_material") is True,
            "p5_human_qa_scorecard_body_free": human_qa_index.get("scorecard_body_free") is True,
            "p5_human_qa_release_material_body_free": human_qa_index.get("release_material_body_free") is True,
        },
        "unresolved_red_refs": red_refs,
        "unresolved_hold_refs": hold_refs,
        "blocker_refs": blocker_refs,
        "candidate": candidate,
        "candidate_status": status,
        "product_gate_candidate_material_ready": material_ready,
        "long_run_candidate_ready": long_run_ready,
        "long_run_candidate_is_release_ready": False,
        "product_pass_is_release_ready": False,
        "release_decision_separated": True,
        "release_decision_input_ready": long_run_ready,
        "release_allowed": False,
        "product_gate_ready": False,
        "public_release_applied": False,
        "candidate_blocked_or_review_required_reason_codes": fixes,
        "required_followup_targets": _followup_targets(fixes),
        "p5_history_line_value_increase_body_free": history_line.get("history_line_value_increase_observed") is True,
        "p6_insight_overclaim_absence_body_free": not risks.get("p6_overclaim_or_creepy_risk_present"),
        "public_contract": public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True),
        "body_free": True,
    }
    assert_p7_long_run_gate_handoff_contract(handoff)
    return handoff


def build_p7_long_run_gate_candidate_material(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Compatibility alias for P7-7 naming."""

    return build_p7_long_run_gate_handoff(*args, **kwargs)


def assert_p7_long_run_gate_handoff_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    if data.get("schema_version") != P7_LONG_RUN_GATE_HANDOFF_SCHEMA_VERSION:
        raise ValueError("unexpected P7 Long-run Gate handoff schema_version")
    if data.get("phase") != P7_PHASE or data.get("scope") != P7_LONG_RUN_GATE_HANDOFF_SCOPE:
        raise ValueError("unexpected P7 Long-run Gate handoff phase/scope")
    if data.get("source_scorecard_schema_version") != P7_SCORECARD_ROW_SCHEMA_VERSION:
        raise ValueError("P7 Long-run Gate handoff must source P7ScorecardRowV1")
    if data.get("source_blind_qa_material_schema_version") != P7_BLIND_QA_MATERIAL_SCHEMA_VERSION:
        raise ValueError("P7 Long-run Gate handoff must source P7 Blind QA material")
    if data.get("source_human_qa_material_index_schema_version") != P7_HUMAN_QA_MATERIAL_INDEX_SCHEMA_VERSION:
        raise ValueError("P7 Long-run Gate handoff must source P5 human QA material index")
    if data.get("handoff_target_schema_version") != PRODUCT_READFEEL_LONG_RUN_PRODUCT_GATE_VERSION:
        raise ValueError("P7 Long-run Gate handoff target schema changed")
    if data.get("release_allowed") is not False:
        raise ValueError("P7 Long-run Gate handoff must not allow release")
    if data.get("product_gate_ready") is not False or data.get("public_release_applied") is not False:
        raise ValueError("P7 Long-run Gate handoff must not apply Product Gate or public release")
    if data.get("long_run_candidate_is_release_ready") is not False:
        raise ValueError("P7 long_run_candidate_ready must not mean release ready")
    if data.get("product_pass_is_release_ready") is not False:
        raise ValueError("P7 Long-run Gate handoff must not promote Product Pass to Release Ready")
    if data.get("release_decision_separated") is not True:
        raise ValueError("P7 Long-run Gate handoff must keep release decision separated")
    if data.get("body_free") is not True:
        raise ValueError("P7 Long-run Gate handoff must be body-free")
    candidate = safe_mapping(data.get("candidate"))
    if not candidate:
        raise ValueError("P7 Long-run Gate handoff must include candidate material")
    status = clean_identifier(candidate.get("candidate_status") or data.get("candidate_status"), default="")
    if status not in _ALLOWED_STATUSES:
        raise ValueError("P7 Long-run Gate candidate status changed")
    if candidate.get("release_allowed") is not False or candidate.get("product_gate_ready") is not False:
        raise ValueError("P7 Long-run Gate candidate must remain release-closed")
    if candidate.get("long_run_candidate_is_release_ready") is not False or candidate.get("product_pass_is_release_ready") is not False:
        raise ValueError("P7 Long-run Gate candidate must not become release ready")
    if data.get("long_run_candidate_ready") is True and status != "candidate_material_ready":
        raise ValueError("P7 long_run_candidate_ready requires candidate_material_ready status")
    if data.get("long_run_candidate_ready") is True and (
        data.get("unresolved_red_refs") or data.get("unresolved_hold_refs") or data.get("candidate_blocked_or_review_required_reason_codes")
    ):
        raise ValueError("P7 Long-run Gate candidate cannot be ready with unresolved red/hold/reason codes")
    blind_summary = safe_mapping(data.get("blind_qa_summary"))
    if blind_summary.get("p5_human_qa_local_body_review_packet_release_material") is not False:
        raise ValueError("P7 Long-run Gate handoff must not turn local body QA packet into release material")
    if blind_summary.get("p5_human_qa_scorecard_body_free") is not True or blind_summary.get("p5_human_qa_release_material_body_free") is not True:
        raise ValueError("P7 Long-run Gate handoff must preserve P5 human QA body-free boundaries")
    if blind_summary.get("p5_human_qa_completed") is not True and "p5_human_qa_review_required" not in data.get("candidate_blocked_or_review_required_reason_codes", []):
        raise ValueError("P7 Long-run Gate handoff must keep review_required while P5 human QA is incomplete")
    assert_false_markers(safe_mapping(data.get("public_contract")), source="p7_long_run_gate_handoff.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_long_run_gate_handoff.body_free_markers")
    if set(safe_mapping(data.get("verdict_counts"))) != set(P7_VERDICTS):
        raise ValueError("P7 Long-run Gate verdict count set changed")
    risks = safe_mapping(data.get("risk_metrics"))
    required_risk_keys = {
        "surface_signature_repeat_count",
        "surface_signature_repetition_detected",
        "mirror_only_detected_count",
        "creepy_risk_detected_count",
        "overclaim_risk_detected_count",
        "unsafe_claim_detected_count",
        "p6_visible_expansion_violation_count",
    }
    if not required_risk_keys.issubset(risks):
        raise ValueError("P7 Long-run Gate risk metrics missing required keys")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_long_run_gate_handoff")
    return True


__all__ = [
    "P7_LONG_RUN_GATE_HANDOFF_SCHEMA_VERSION",
    "P7_LONG_RUN_GATE_HANDOFF_SCOPE",
    "P7_LONG_RUN_GATE_HANDOFF_STEP",
    "assert_p7_long_run_gate_handoff_contract",
    "build_p7_long_run_gate_candidate_material",
    "build_p7_long_run_gate_handoff",
]
