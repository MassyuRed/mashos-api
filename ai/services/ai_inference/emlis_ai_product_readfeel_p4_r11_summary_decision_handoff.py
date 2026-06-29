# -*- coding: utf-8 -*-
from __future__ import annotations

"""P4-R11 R11-8 body-free summary / decision handoff helpers.

R11-8 consumes the R11-7 verdict / repair-candidate classification payload and
materializes only body-free decision material for the next Cocolon step.  It does
not create R54/P5 actual review evidence, does not create question observation
rows, does not start P6/P8, and does not change runtime/API/DB/RN contracts.
"""

from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any, Final

import emlis_ai_product_readfeel_p4_r11_residual_family_surface_audit as base
import emlis_ai_product_readfeel_p4_r11_surface_specificity_role_verdict_audit as r6r7

PRODUCT_READFEEL_P4_R11_SUMMARY_DECISION_HANDOFF_VERSION_20260624: Final[str] = (
    "cocolon.emlis.product_readfeel.p4_r11.summary_decision_handoff.v1"
)
PRODUCT_READFEEL_P4_R11_DECISION_HANDOFF_VERSION_20260624: Final[str] = (
    "cocolon.emlis.product_readfeel.p4_r11.decision_handoff.v1"
)
PRODUCT_READFEEL_P4_R11_PUBLIC_DECISION_SUMMARY_VERSION_20260624: Final[str] = (
    "cocolon.emlis.product_readfeel.p4_r11.public_decision_summary.20260624.v1"
)

P4_R11_R8_IMPLEMENTED_STEPS_20260624: Final[tuple[str, ...]] = (
    base.P4_R11_R0_STEP_REF_20260624,
    base.P4_R11_R1_STEP_REF_20260624,
    base.P4_R11_R2_STEP_REF_20260624,
    base.P4_R11_R3_STEP_REF_20260624,
    base.P4_R11_R4_STEP_REF_20260624,
    base.P4_R11_R5_STEP_REF_20260624,
    base.P4_R11_R6_STEP_REF_20260624,
    base.P4_R11_R7_STEP_REF_20260624,
    base.P4_R11_R8_STEP_REF_20260624,
)
P4_R11_R8_REQUIRED_PRIOR_STEPS_20260624: Final[tuple[str, ...]] = (
    base.P4_R11_R0_STEP_REF_20260624,
    base.P4_R11_R1_STEP_REF_20260624,
    base.P4_R11_R2_STEP_REF_20260624,
    base.P4_R11_R3_STEP_REF_20260624,
    base.P4_R11_R4_STEP_REF_20260624,
    base.P4_R11_R5_STEP_REF_20260624,
    base.P4_R11_R6_STEP_REF_20260624,
    base.P4_R11_R7_STEP_REF_20260624,
)
P4_R11_R8_NOT_YET_IMPLEMENTED_STEPS_20260624: Final[tuple[str, ...]] = (
    base.P4_R11_R9_STEP_REF_20260624,
    base.P4_R11_R10_STEP_REF_20260624,
    base.P4_R11_R11_STEP_REF_20260624,
    base.P4_R11_R12_STEP_REF_20260624,
    base.P4_R11_R13_STEP_REF_20260624,
    base.P4_R11_R14_STEP_REF_20260624,
    base.P4_R11_R15_STEP_REF_20260624,
)

P4_R11_R9_TARGETED_TEST_FILE_REFS_20260624: Final[tuple[str, ...]] = (
    "tests/test_emlis_ai_product_readfeel_p4_r11_scope_matrix_20260624.py",
    "tests/test_emlis_ai_product_readfeel_p4_r11_body_free_schema_20260624.py",
    "tests/test_emlis_ai_product_readfeel_p4_r11_case_ref_selection_coverage_20260624.py",
    "tests/test_emlis_ai_product_readfeel_p4_r11_material_route_audit_20260624.py",
    "tests/test_emlis_ai_product_readfeel_p4_r11_surface_path_audit_20260624.py",
    "tests/test_emlis_ai_product_readfeel_p4_r11_surface_specificity_role_audit_20260624.py",
    "tests/test_emlis_ai_product_readfeel_p4_r11_verdict_repair_candidate_classification_20260624.py",
    "tests/test_emlis_ai_product_readfeel_p4_r11_summary_decision_handoff_20260624.py",
    "tests/test_emlis_ai_product_readfeel_p4_r11_decision_handoff_20260624.py",
    "tests/test_emlis_ai_product_readfeel_p4_r11_targeted_tests_20260624.py",
)

PRODUCT_READFEEL_P4_R11_TARGETED_TESTS_MANIFEST_VERSION_20260624: Final[str] = (
    "cocolon.emlis.product_readfeel.p4_r11.targeted_tests_manifest.v1"
)
P4_R11_R9_IMPLEMENTED_STEPS_20260624: Final[tuple[str, ...]] = (
    *P4_R11_R8_IMPLEMENTED_STEPS_20260624,
    base.P4_R11_R9_STEP_REF_20260624,
)
P4_R11_R9_NOT_YET_IMPLEMENTED_STEPS_20260624: Final[tuple[str, ...]] = (
    base.P4_R11_R10_STEP_REF_20260624,
    base.P4_R11_R11_STEP_REF_20260624,
    base.P4_R11_R12_STEP_REF_20260624,
    base.P4_R11_R13_STEP_REF_20260624,
    base.P4_R11_R14_STEP_REF_20260624,
    base.P4_R11_R15_STEP_REF_20260624,
)
P4_R11_TARGETED_TEST_FILE_REFS_20260624: Final[tuple[str, ...]] = (
    "tests/test_emlis_ai_product_readfeel_p4_r11_scope_matrix_20260624.py",
    "tests/test_emlis_ai_product_readfeel_p4_r11_body_free_schema_20260624.py",
    "tests/test_emlis_ai_product_readfeel_p4_r11_case_ref_selection_coverage_20260624.py",
    "tests/test_emlis_ai_product_readfeel_p4_r11_material_route_audit_20260624.py",
    "tests/test_emlis_ai_product_readfeel_p4_r11_surface_path_audit_20260624.py",
    "tests/test_emlis_ai_product_readfeel_p4_r11_surface_specificity_role_audit_20260624.py",
    "tests/test_emlis_ai_product_readfeel_p4_r11_verdict_repair_candidate_classification_20260624.py",
    "tests/test_emlis_ai_product_readfeel_p4_r11_summary_decision_handoff_20260624.py",
    "tests/test_emlis_ai_product_readfeel_p4_r11_decision_handoff_20260624.py",
    "tests/test_emlis_ai_product_readfeel_p4_r11_targeted_tests_20260624.py",
)

P4_R11_DECISION_RETURN_TO_R54_ACTUAL_REVIEW_CANDIDATE_20260624: Final[str] = (
    "P4_R11_RETURN_TO_R54_ACTUAL_REVIEW_CANDIDATE"
)
P4_R11_DECISION_TARGETED_REPAIR_REQUIRED_BEFORE_R54_20260624: Final[str] = (
    "P4_R11_TARGETED_REPAIR_REQUIRED_BEFORE_R54"
)
P4_R11_DECISION_INSUFFICIENT_COVERAGE_EXPAND_AUDIT_20260624: Final[str] = (
    "P4_R11_INSUFFICIENT_COVERAGE_EXPAND_AUDIT"
)

P4_R11_NEXT_STEP_R54_ACTUAL_REVIEW_20260624: Final[str] = (
    base.P4_R11_R55_NEXT_REQUIRED_STEP_REF_20260624
)
P4_R11_NEXT_STEP_P4_R12_TARGETED_REPAIR_20260624: Final[str] = (
    "P4_R12_targeted_current_only_surface_repair"
)
P4_R11_NEXT_STEP_P4_R11_COVERAGE_EXPANSION_20260624: Final[str] = (
    "P4_R11_case_coverage_expansion"
)
# Aliases keep the design wording stable for R11-8/R11-9 targeted tests.
P4_R11_NEXT_STEP_R54_ACTUAL_LOCAL_ONLY_HUMAN_REVIEW_20260624: Final[str] = (
    P4_R11_NEXT_STEP_R54_ACTUAL_REVIEW_20260624
)
P4_R11_NEXT_STEP_P4_R11_CASE_COVERAGE_EXPANSION_20260624: Final[str] = (
    P4_R11_NEXT_STEP_P4_R11_COVERAGE_EXPANSION_20260624
)

_R8_STATUS_SUMMARIZED: Final[str] = "ready_r11_8"
_COVERAGE_COMPLETE: Final[str] = "complete"
_COVERAGE_INSUFFICIENT: Final[str] = "insufficient_public_safe_case_refs"


def _clean(value: Any) -> str:
    return base._clean(value)  # type: ignore[attr-defined]


def _safe_identifier(value: Any, *, default: str = "") -> str:
    return base._safe_identifier(value, default=default)  # type: ignore[attr-defined]


def _dedupe(values: Any) -> list[str]:
    return base._dedupe(values)  # type: ignore[attr-defined]


def _boundary_flags() -> dict[str, Any]:
    return base._all_boundary_flags()  # type: ignore[attr-defined]


def _counter_dict(counter: Counter[str]) -> dict[str, int]:
    return {key: int(counter[key]) for key in sorted(counter) if key}


def _source_rows(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = source.get("audit_rows")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes, bytearray)):
        raise ValueError("p4_r11.r8 requires R11-7 audit_rows")
    result: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise ValueError(f"p4_r11.r8 audit_rows[{index}] must be a mapping")
        if row.get("verdict_classification_performed_here") is not True:
            raise ValueError("p4_r11.r8 requires R11-7 verdict classification before decision handoff")
        if not _clean(row.get("verdict")):
            raise ValueError("p4_r11.r8 requires every R11-7 row to have a verdict")
        result.append(dict(row))
    return result


def _coverage_complete(*, summary: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]) -> bool:
    coverage_status = _clean(summary.get("coverage_status"))
    audited_row_count = int(summary.get("audited_row_count") or len(rows))
    selected_ref_row_count = int(summary.get("selected_ref_row_count") or audited_row_count)
    unique_case_ref_count = len({_safe_identifier(row.get("case_ref_id"), default="") for row in rows})
    selected_unique_case_ref_count = int(summary.get("selected_unique_case_ref_count") or unique_case_ref_count)
    surface_probe_unavailable_count = int(summary.get("surface_probe_unavailable_count") or 0)
    return (
        coverage_status == _COVERAGE_COMPLETE
        and audited_row_count >= base.P4_R11_TARGET_ROW_COUNT_20260624
        and selected_ref_row_count >= base.P4_R11_TARGET_ROW_COUNT_20260624
        and selected_unique_case_ref_count >= base.P4_R11_TARGET_ROW_COUNT_20260624
        and surface_probe_unavailable_count == 0
    )


def _decision_from_summary(*, summary: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]) -> tuple[str, str, bool]:
    complete = _coverage_complete(summary=summary, rows=rows)
    if not complete:
        return (
            P4_R11_DECISION_INSUFFICIENT_COVERAGE_EXPAND_AUDIT_20260624,
            P4_R11_NEXT_STEP_P4_R11_COVERAGE_EXPANSION_20260624,
            False,
        )
    blocker_count = int(summary.get("current_only_blocker_count") or 0)
    repair_required_count = int(summary.get("repair_required_count") or 0)
    red_count = int(summary.get("red_count") or 0)
    if blocker_count > 0 or repair_required_count > 0 or red_count > 0:
        return (
            P4_R11_DECISION_TARGETED_REPAIR_REQUIRED_BEFORE_R54_20260624,
            P4_R11_NEXT_STEP_P4_R12_TARGETED_REPAIR_20260624,
            False,
        )
    return (
        P4_R11_DECISION_RETURN_TO_R54_ACTUAL_REVIEW_CANDIDATE_20260624,
        P4_R11_NEXT_STEP_R54_ACTUAL_REVIEW_20260624,
        True,
    )


def _row_decision_status(row: Mapping[str, Any]) -> dict[str, Any]:
    verdict = _clean(row.get("verdict"))
    if verdict in {r6r7.P4_R11_VERDICT_REPAIR_REQUIRED_20260624, r6r7.P4_R11_VERDICT_RED_20260624}:
        row_handoff = "p4_targeted_repair_candidate_row"
    elif verdict == r6r7.P4_R11_VERDICT_YELLOW_20260624:
        row_handoff = "human_readfeel_review_note_only_row"
    elif verdict == r6r7.P4_R11_VERDICT_PASS_20260624:
        row_handoff = "r54_return_candidate_row"
    else:
        row_handoff = "unknown_verdict_row"
    return {
        "decision_handoff_status": _R8_STATUS_SUMMARIZED,
        "row_decision_handoff_kind": row_handoff,
        "summary_decision_handoff_performed_here": True,
        "decision_handoff_performed_here": True,
        "p5_human_review_evidence_created_here": False,
        "question_observation_rows_created_here": False,
        "p6_start_allowed": False,
        "p8_start_allowed": False,
        "release_allowed": False,
    }


def _build_decision_handoff(
    *,
    decision_ref: str,
    next_required_step: str,
    r54_return_candidate_after_r11: bool,
    current_only_blocker_count: int,
    coverage_status: str,
) -> dict[str, Any]:
    handoff = {
        "schema_version": PRODUCT_READFEEL_P4_R11_DECISION_HANDOFF_VERSION_20260624,
        "version": PRODUCT_READFEEL_P4_R11_DECISION_HANDOFF_VERSION_20260624,
        "source": base.PRODUCT_READFEEL_P4_R11_SOURCE_20260624,
        "source_phase": base.PRODUCT_READFEEL_P4_R11_PHASE_20260624,
        "source_step": base.P4_R11_R8_STEP_REF_20260624,
        "decision_handoff_status": _R8_STATUS_SUMMARIZED,
        "decision_ref": decision_ref,
        "next_required_step": next_required_step,
        "r55_decision_ref": base.P4_R11_R55_DECISION_REF_20260624,
        "r55_decision_preserved": True,
        "r55_next_required_step_preserved": base.P4_R11_R55_NEXT_REQUIRED_STEP_REF_20260624,
        "coverage_status": coverage_status or "unknown",
        "current_only_blocker_count": int(current_only_blocker_count),
        "r54_return_candidate_after_r11": r54_return_candidate_after_r11,
        "r54_actual_review_still_required": True,
        "p4_targeted_repair_required_before_r54": (
            decision_ref == P4_R11_DECISION_TARGETED_REPAIR_REQUIRED_BEFORE_R54_20260624
        ),
        "case_coverage_expansion_required": (
            decision_ref == P4_R11_DECISION_INSUFFICIENT_COVERAGE_EXPAND_AUDIT_20260624
        ),
        "p5_human_review_evidence_created_here": False,
        "question_observation_rows_created_here": False,
        "p5_human_blind_qa_confirmed": False,
        "p6_start_allowed": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "summary_decision_handoff_performed_here": True,
        "decision_handoff_performed_here": True,
        "not_release_decision": True,
        **_boundary_flags(),
    }
    base.assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(
        handoff,
        source="p4_r11.r8.decision_handoff",
    )
    return handoff


def build_product_readfeel_p4_r11_summary_decision_handoff_20260624(
    *,
    verdict_repair_classification_payload: Mapping[str, Any] | None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Summarize R11-7 verdicts into the R11-8 body-free decision handoff."""

    if not isinstance(verdict_repair_classification_payload, Mapping):
        raise ValueError("p4_r11.r8 requires the R11-7 verdict repair classification payload")
    source = dict(verdict_repair_classification_payload)
    base.assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(
        source,
        source="p4_r11.r8.verdict_source",
    )
    if source.get("schema_version") != r6r7.PRODUCT_READFEEL_P4_R11_VERDICT_REPAIR_CLASSIFICATION_VERSION_20260624:
        raise ValueError("p4_r11.r8 requires R11-7 verdict repair classification schema")
    if source.get("verdict_classification_performed_here") is not True:
        raise ValueError("p4_r11.r8 requires R11-7 verdict classification before decision handoff")

    source_summary = source.get("summary") if isinstance(source.get("summary"), Mapping) else {}
    rows = _source_rows(source)
    run_id_value = _safe_identifier(run_id, default="p4_r11_r8_summary_decision_handoff")

    family_counts: Counter[str] = Counter()
    verdict_counts: Counter[str] = Counter()
    next_action_counts: Counter[str] = Counter()
    repair_layer_counts: Counter[str] = Counter()
    p5_forbidden_count = 0
    p8_forbidden_count = 0
    current_only_repair_before_history_or_question_count = 0
    current_only_blocker_count = 0
    blocker_family_ids: set[str] = set()
    repair_candidate_layer_ids: set[str] = set()
    handoff_rows: list[dict[str, Any]] = []

    for source_row in rows:
        row = dict(source_row)
        family_counts[_clean(row.get("residual_family_id"))] += 1
        verdict = _clean(row.get("verdict"))
        verdict_counts[verdict] += 1
        next_action_counts[_clean(row.get("next_action"))] += 1
        for layer_id in _dedupe(row.get("repair_candidate_layer_ids")):
            repair_layer_counts[layer_id] += 1
            repair_candidate_layer_ids.add(layer_id)
        p5_p8 = row.get("p5_p8_escape_boundary") if isinstance(row.get("p5_p8_escape_boundary"), Mapping) else {}
        if p5_p8.get("p5_masking_forbidden") is True:
            p5_forbidden_count += 1
        if p5_p8.get("p8_question_escape_forbidden") is True:
            p8_forbidden_count += 1
        if p5_p8.get("current_only_repair_required_before_history_or_question") is True:
            current_only_repair_before_history_or_question_count += 1
        if row.get("current_only_blocker") is True or verdict in {
            r6r7.P4_R11_VERDICT_REPAIR_REQUIRED_20260624,
            r6r7.P4_R11_VERDICT_RED_20260624,
        }:
            current_only_blocker_count += 1
            blocker_family = _clean(row.get("residual_family_id"))
            if blocker_family:
                blocker_family_ids.add(blocker_family)
        row.update(
            {
                "schema_version": PRODUCT_READFEEL_P4_R11_SUMMARY_DECISION_HANDOFF_VERSION_20260624,
                "source_step": base.P4_R11_R8_STEP_REF_20260624,
                "run_id": run_id_value,
                "implemented_steps": P4_R11_R8_IMPLEMENTED_STEPS_20260624,
                "not_yet_implemented_steps": P4_R11_R8_NOT_YET_IMPLEMENTED_STEPS_20260624,
                "next_implementation_step": base.P4_R11_R9_STEP_REF_20260624,
                **_row_decision_status(row),
                **_boundary_flags(),
            }
        )
        base.assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(
            row,
            source=f"p4_r11.r8.row.{_safe_identifier(row.get('case_ref_id'), default='unknown')}",
        )
        handoff_rows.append(row)

    coverage_status = _clean(source_summary.get("coverage_status")) or "unknown"
    decision_ref, next_required_step, r54_return_candidate = _decision_from_summary(
        summary={**dict(source_summary), "current_only_blocker_count": current_only_blocker_count},
        rows=handoff_rows,
    )
    selected_unique_case_ref_count = len({_safe_identifier(row.get("case_ref_id"), default="") for row in handoff_rows})
    audited_row_count = len(handoff_rows)
    yellow_count = int(verdict_counts[r6r7.P4_R11_VERDICT_YELLOW_20260624])
    repair_required_count = int(verdict_counts[r6r7.P4_R11_VERDICT_REPAIR_REQUIRED_20260624])
    red_count = int(verdict_counts[r6r7.P4_R11_VERDICT_RED_20260624])
    pass_count = int(verdict_counts[r6r7.P4_R11_VERDICT_PASS_20260624])
    coverage_or_probe_gap_present = not _coverage_complete(summary={**dict(source_summary), "current_only_blocker_count": current_only_blocker_count}, rows=handoff_rows)

    decision_handoff = _build_decision_handoff(
        decision_ref=decision_ref,
        next_required_step=next_required_step,
        r54_return_candidate_after_r11=r54_return_candidate,
        current_only_blocker_count=current_only_blocker_count,
        coverage_status=coverage_status,
    )

    summary = dict(source_summary)
    summary.update(
        {
            "schema_version": PRODUCT_READFEEL_P4_R11_SUMMARY_DECISION_HANDOFF_VERSION_20260624,
            "version": PRODUCT_READFEEL_P4_R11_SUMMARY_DECISION_HANDOFF_VERSION_20260624,
            "source": base.PRODUCT_READFEEL_P4_R11_SOURCE_20260624,
            "source_phase": base.PRODUCT_READFEEL_P4_R11_PHASE_20260624,
            "source_step": base.P4_R11_R8_STEP_REF_20260624,
            "audit_profile": base.PRODUCT_READFEEL_P4_R11_AUDIT_PROFILE_20260624,
            "run_id": run_id_value,
            "target_row_count": base.P4_R11_TARGET_ROW_COUNT_20260624,
            "audited_row_count": audited_row_count,
            "selected_ref_row_count": audited_row_count,
            "selected_unique_case_ref_count": selected_unique_case_ref_count,
            "coverage_status": coverage_status,
            "family_counts": _counter_dict(family_counts),
            "verdict_counts": _counter_dict(verdict_counts),
            "next_action_counts": _counter_dict(next_action_counts),
            "repair_candidate_layer_counts": _counter_dict(repair_layer_counts),
            "pass_count": pass_count,
            "yellow_count": yellow_count,
            "repair_required_count": repair_required_count,
            "red_count": red_count,
            "current_only_blocker_count": current_only_blocker_count,
            "p5_masking_forbidden_row_count": p5_forbidden_count,
            "p8_question_escape_forbidden_row_count": p8_forbidden_count,
            "current_only_repair_required_before_history_or_question_row_count": (
                current_only_repair_before_history_or_question_count
            ),
            "yellow_human_readfeel_review_note_only_count": yellow_count,
            "p4_targeted_repair_required": (
                decision_ref == P4_R11_DECISION_TARGETED_REPAIR_REQUIRED_BEFORE_R54_20260624
            ),
            "r54_return_candidate_after_r11": r54_return_candidate,
            "case_coverage_expansion_required": (
                decision_ref == P4_R11_DECISION_INSUFFICIENT_COVERAGE_EXPAND_AUDIT_20260624
            ),
            "p4_r11_case_coverage_expansion_required": (
                decision_ref == P4_R11_DECISION_INSUFFICIENT_COVERAGE_EXPAND_AUDIT_20260624
            ),
            "insufficient_coverage_expand_audit_required": (
                decision_ref == P4_R11_DECISION_INSUFFICIENT_COVERAGE_EXPAND_AUDIT_20260624
            ),
            "coverage_or_probe_gap_present": coverage_or_probe_gap_present,
            "blocker_family_ids": sorted(blocker_family_ids),
            "repair_candidate_layer_ids": sorted(repair_candidate_layer_ids),
            "decision_ref": decision_ref,
            "next_required_step": next_required_step,
            "r55_decision_preserved": True,
            "r54_actual_review_still_required": True,
            "p5_human_review_evidence_created_here": False,
            "question_observation_rows_created_here": False,
            "actual_rating_rows_materialized_here": False,
            "actual_question_need_observation_rows_materialized_here": False,
            "p6_start_allowed": False,
            "p8_start_allowed": False,
            "release_allowed": False,
            "decision_handoff_status": _R8_STATUS_SUMMARIZED,
            "summary_decision_handoff_performed_here": True,
            "decision_handoff_performed_here": True,
            "implemented_steps": list(P4_R11_R8_IMPLEMENTED_STEPS_20260624),
            "not_yet_implemented_steps": list(P4_R11_R8_NOT_YET_IMPLEMENTED_STEPS_20260624),
            "next_implementation_step": base.P4_R11_R9_STEP_REF_20260624,
            **_boundary_flags(),
        }
    )
    base.assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(
        summary,
        source="p4_r11.r8.summary",
    )

    payload = {
        "schema_version": PRODUCT_READFEEL_P4_R11_SUMMARY_DECISION_HANDOFF_VERSION_20260624,
        "version": PRODUCT_READFEEL_P4_R11_SUMMARY_DECISION_HANDOFF_VERSION_20260624,
        "source": base.PRODUCT_READFEEL_P4_R11_SOURCE_20260624,
        "source_phase": base.PRODUCT_READFEEL_P4_R11_PHASE_20260624,
        "source_step": base.P4_R11_R8_STEP_REF_20260624,
        "run_id": run_id_value,
        "audit_profile": base.PRODUCT_READFEEL_P4_R11_AUDIT_PROFILE_20260624,
        "implemented_steps": list(P4_R11_R8_IMPLEMENTED_STEPS_20260624),
        "required_prior_steps": list(P4_R11_R8_REQUIRED_PRIOR_STEPS_20260624),
        "not_yet_implemented_steps": list(P4_R11_R8_NOT_YET_IMPLEMENTED_STEPS_20260624),
        "next_implementation_step": base.P4_R11_R9_STEP_REF_20260624,
        "r11_9_targeted_test_file_refs": list(P4_R11_R9_TARGETED_TEST_FILE_REFS_20260624),
        "verdict_repair_classification_ref": _safe_identifier(
            source.get("run_id"), default="p4_r11_r7_verdict_repair_candidate_classification"
        ),
        "summary": summary,
        "decision_handoff": decision_handoff,
        "audit_rows": handoff_rows,
        "selected_case_ref_rows": handoff_rows,
        "selected_ref_row_count": audited_row_count,
        "selected_unique_case_ref_count": selected_unique_case_ref_count,
        "case_ref_selection_performed_here": True,
        "material_route_audit_performed_here": True,
        "surface_path_audit_performed_here": True,
        "surface_specificity_role_audit_performed_here": True,
        "verdict_classification_performed_here": True,
        "summary_decision_handoff_performed_here": True,
        "decision_handoff_performed_here": True,
        "targeted_tests_performed_here": False,
        "actual_audit_rows_created_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "p5_human_review_evidence_created_here": False,
        "question_observation_rows_created_here": False,
        "json_schema_file_materialized": False,
        **_boundary_flags(),
    }
    base.assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(
        payload,
        source="p4_r11.r8.summary_decision_handoff",
    )
    return payload


def build_product_readfeel_p4_r11_public_decision_summary_20260624(
    *,
    summary_decision_handoff_payload: Mapping[str, Any],
    run_id: str | None = None,
) -> dict[str, Any]:
    """Build a compact body-free R11-8 decision summary.

    The summary is intended for local result material and tests.  It carries only
    counts, ids, decision refs, and false contract/hold flags; it does not add a
    public response key and does not materialize a JSON/schema file.
    """

    if not isinstance(summary_decision_handoff_payload, Mapping):
        raise ValueError("p4_r11.r8 public summary requires R11-8 summary decision handoff payload")
    source = dict(summary_decision_handoff_payload)
    base.assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(
        source,
        source="p4_r11.r8.public_decision_summary_source",
    )
    if source.get("schema_version") != PRODUCT_READFEEL_P4_R11_SUMMARY_DECISION_HANDOFF_VERSION_20260624:
        raise ValueError("p4_r11.r8 public summary requires R11-8 summary decision handoff schema")
    summary = source.get("summary") if isinstance(source.get("summary"), Mapping) else {}
    decision = source.get("decision_handoff") if isinstance(source.get("decision_handoff"), Mapping) else {}
    result = {
        "schema_version": PRODUCT_READFEEL_P4_R11_PUBLIC_DECISION_SUMMARY_VERSION_20260624,
        "version": PRODUCT_READFEEL_P4_R11_PUBLIC_DECISION_SUMMARY_VERSION_20260624,
        "source": base.PRODUCT_READFEEL_P4_R11_SOURCE_20260624,
        "source_phase": base.PRODUCT_READFEEL_P4_R11_PHASE_20260624,
        "source_step": base.P4_R11_R8_STEP_REF_20260624,
        "run_id": _safe_identifier(run_id, default="p4_r11_r8_public_decision_summary"),
        "audit_profile": base.PRODUCT_READFEEL_P4_R11_AUDIT_PROFILE_20260624,
        "audited_row_count": int(summary.get("audited_row_count") or 0),
        "target_row_count": int(summary.get("target_row_count") or base.P4_R11_TARGET_ROW_COUNT_20260624),
        "coverage_status": _clean(summary.get("coverage_status")),
        "family_counts": dict(summary.get("family_counts") or {}),
        "verdict_counts": dict(summary.get("verdict_counts") or {}),
        "current_only_blocker_count": int(summary.get("current_only_blocker_count") or 0),
        "p5_masking_forbidden_row_count": int(summary.get("p5_masking_forbidden_row_count") or 0),
        "p8_question_escape_forbidden_row_count": int(summary.get("p8_question_escape_forbidden_row_count") or 0),
        "decision_ref": _clean(decision.get("decision_ref") or summary.get("decision_ref")),
        "next_required_step": _clean(decision.get("next_required_step") or summary.get("next_required_step")),
        "r55_decision_ref": base.P4_R11_R55_DECISION_REF_20260624,
        "r55_decision_preserved": decision.get("r55_decision_preserved") is True,
        "r54_actual_review_still_required": decision.get("r54_actual_review_still_required") is True,
        "p5_human_review_evidence_created_here": False,
        "question_observation_rows_created_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "p6_start_allowed": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "summary_decision_handoff_performed_here": True,
        "decision_handoff_performed_here": True,
        "targeted_tests_performed_here": False,
        "r11_9_targeted_test_file_refs": list(P4_R11_R9_TARGETED_TEST_FILE_REFS_20260624),
        **_boundary_flags(),
    }
    base.assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(
        result,
        source="p4_r11.r8.public_decision_summary",
    )
    return result


def build_product_readfeel_p4_r11_targeted_tests_manifest_20260624(
    *,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Freeze the R11-9 target-test file set without claiming execution results."""

    manifest = {
        "schema_version": PRODUCT_READFEEL_P4_R11_TARGETED_TESTS_MANIFEST_VERSION_20260624,
        "version": PRODUCT_READFEEL_P4_R11_TARGETED_TESTS_MANIFEST_VERSION_20260624,
        "source": base.PRODUCT_READFEEL_P4_R11_SOURCE_20260624,
        "source_phase": base.PRODUCT_READFEEL_P4_R11_PHASE_20260624,
        "source_step": base.P4_R11_R9_STEP_REF_20260624,
        "run_id": _safe_identifier(run_id, default="p4_r11_r9_targeted_tests_manifest"),
        "implemented_steps": list(P4_R11_R9_IMPLEMENTED_STEPS_20260624),
        "not_yet_implemented_steps": list(P4_R11_R9_NOT_YET_IMPLEMENTED_STEPS_20260624),
        "next_implementation_step": base.P4_R11_R10_STEP_REF_20260624,
        "targeted_test_file_refs": list(P4_R11_TARGETED_TEST_FILE_REFS_20260624),
        "targeted_test_file_count": len(P4_R11_TARGETED_TEST_FILE_REFS_20260624),
        "covers_r11_0_contract_freeze": True,
        "covers_r11_1_scope_matrix": True,
        "covers_r11_2_body_free_guard": True,
        "covers_r11_3_case_ref_selection": True,
        "covers_r11_4_material_route_audit": True,
        "covers_r11_5_surface_path_audit": True,
        "covers_r11_6_surface_specificity_role_audit": True,
        "covers_r11_7_verdict_repair_classification": True,
        "covers_r11_8_summary_decision_handoff": True,
        "targeted_test_manifest_only": True,
        "targeted_test_green_claim_created_here": False,
        "p5_human_review_evidence_created_here": False,
        "question_observation_rows_created_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_audit_rows_created_here": False,
        "p6_start_allowed": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "runtime_changed_here": False,
        "json_schema_file_materialized": False,
        **_boundary_flags(),
    }
    base.assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(
        manifest,
        source="p4_r11.r9.targeted_tests_manifest",
    )
    return manifest


__all__ = [
    "PRODUCT_READFEEL_P4_R11_SUMMARY_DECISION_HANDOFF_VERSION_20260624",
    "PRODUCT_READFEEL_P4_R11_DECISION_HANDOFF_VERSION_20260624",
    "PRODUCT_READFEEL_P4_R11_PUBLIC_DECISION_SUMMARY_VERSION_20260624",
    "P4_R11_R8_IMPLEMENTED_STEPS_20260624",
    "P4_R11_R8_REQUIRED_PRIOR_STEPS_20260624",
    "P4_R11_R8_NOT_YET_IMPLEMENTED_STEPS_20260624",
    "P4_R11_R9_TARGETED_TEST_FILE_REFS_20260624",
    "P4_R11_DECISION_RETURN_TO_R54_ACTUAL_REVIEW_CANDIDATE_20260624",
    "P4_R11_DECISION_TARGETED_REPAIR_REQUIRED_BEFORE_R54_20260624",
    "P4_R11_DECISION_INSUFFICIENT_COVERAGE_EXPAND_AUDIT_20260624",
    "P4_R11_NEXT_STEP_R54_ACTUAL_REVIEW_20260624",
    "P4_R11_NEXT_STEP_R54_ACTUAL_LOCAL_ONLY_HUMAN_REVIEW_20260624",
    "P4_R11_NEXT_STEP_P4_R12_TARGETED_REPAIR_20260624",
    "P4_R11_NEXT_STEP_P4_R11_COVERAGE_EXPANSION_20260624",
    "P4_R11_NEXT_STEP_P4_R11_CASE_COVERAGE_EXPANSION_20260624",
    "build_product_readfeel_p4_r11_summary_decision_handoff_20260624",
    "build_product_readfeel_p4_r11_public_decision_summary_20260624",
    "PRODUCT_READFEEL_P4_R11_TARGETED_TESTS_MANIFEST_VERSION_20260624",
    "P4_R11_R9_IMPLEMENTED_STEPS_20260624",
    "P4_R11_R9_NOT_YET_IMPLEMENTED_STEPS_20260624",
    "P4_R11_TARGETED_TEST_FILE_REFS_20260624",
    "build_product_readfeel_p4_r11_targeted_tests_manifest_20260624",
]
