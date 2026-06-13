# -*- coding: utf-8 -*-
from __future__ import annotations

import json

import pytest

from emlis_ai_p7_evaluation_matrix import (
    P7_EVALUATION_FAMILIES,
    P7_EVALUATION_MATRIX_SCHEMA_VERSION,
    P7_SEQUENCE_DEFINITIONS,
    P7_VERDICTS,
    assert_p7_evaluation_matrix_contract,
    build_p7_evaluation_matrix,
    classify_p7_scorecard_row_verdict,
)
from emlis_ai_p7_event_bridge import P7_RATING_REQUIRED_DIMENSIONS, build_p7_scorecard_row
from test_emlis_ai_p7_event_bridge_20260612 import _event, _handoff

SECRET_COMMENT = "P7-5 secret comment_text body must never be serialized"


def _base_row(*, family: str = "structure_question") -> dict[str, object]:
    return build_p7_scorecard_row(product_quality_event=_event(family=family), p7_handoff_summary=_handoff())


def _cleared_row(row: dict[str, object]) -> dict[str, object]:
    cleared = dict(row)
    cleared["red_refs"] = []
    cleared["hold_refs"] = []
    cleared["blocker_refs"] = []
    cleared["blocker_ids"] = []
    return cleared


def test_p7_5_matrix_defines_initial_families_sequences_and_p6_visible_boundary() -> None:
    matrix = build_p7_evaluation_matrix()
    assert_p7_evaluation_matrix_contract(matrix)

    assert matrix["schema_version"] == P7_EVALUATION_MATRIX_SCHEMA_VERSION
    assert tuple(matrix["families"]) == P7_EVALUATION_FAMILIES
    assert [sequence["sequence_id"] for sequence in matrix["sequences"]] == ["sequence_1", "sequence_3", "sequence_7"]
    assert [sequence["sequence_length"] for sequence in P7_SEQUENCE_DEFINITIONS] == [1, 3, 7]
    assert matrix["family_count"] == 14
    assert matrix["sequence_count"] == 3
    assert matrix["matrix_row_count"] == 42
    assert matrix["p6_visible_allowed_families"] == ["structure_question"]
    assert "long_meaning_arc" in matrix["p6_visible_blocked_families"]
    assert matrix["product_pass_is_release_ready"] is False
    assert matrix["release_allowed"] is False


def test_p7_5_matrix_separates_single_input_sequence_and_history_line_rows() -> None:
    matrix = build_p7_evaluation_matrix()
    rows = matrix["matrix_rows"]

    single_rows = [row for row in rows if row["row_kind"] == "single_input"]
    sequence_rows = [row for row in rows if row["row_kind"] == "sequence"]
    history_rows = [row for row in rows if row["history_line_eligible"] is True]
    non_history_rows = [row for row in rows if row["history_line_eligible"] is False]

    assert len(single_rows) == len(P7_EVALUATION_FAMILIES)
    assert len(sequence_rows) == len(P7_EVALUATION_FAMILIES) * 2
    assert history_rows
    assert non_history_rows
    assert any(row["family"] == "history_line_eligible" and row["sequence_id"] == "sequence_3" for row in history_rows)
    assert any(row["family"] == "daily_positive" and row["sequence_id"] == "sequence_1" for row in non_history_rows)


def test_p7_5_scorecard_aggregation_counts_red_yellow_repair_and_product_pass_candidate_without_release() -> None:
    red_row = _base_row()

    yellow_row = _cleared_row(_base_row())
    # HOLD remains absent here, but Blind QA is still missing, so the row is YELLOW.

    repair_row = _cleared_row(_base_row(family="daily_positive"))
    repair_display = dict(repair_row["display_contract"])
    repair_display["product_surface_valid"] = False
    repair_row["display_contract"] = repair_display

    product_row = _cleared_row(_base_row())
    product_row["ratings"] = {
        "blind_qa_required": True,
        "blind_qa_completed": True,
        "rating_required": False,
        "dimension_scores": {dimension: 0.95 for dimension in P7_RATING_REQUIRED_DIMENSIONS},
        "missing_dimensions": [],
        "rating_required_dimensions": list(P7_RATING_REQUIRED_DIMENSIONS),
    }

    assert classify_p7_scorecard_row_verdict(red_row) == "RED"
    assert classify_p7_scorecard_row_verdict(yellow_row) == "YELLOW"
    assert classify_p7_scorecard_row_verdict(repair_row) == "REPAIR_REQUIRED"
    assert classify_p7_scorecard_row_verdict(product_row) == "PRODUCT_PASS"

    matrix = build_p7_evaluation_matrix([red_row, yellow_row, repair_row, product_row])
    counts = matrix["aggregation"]["overall_verdict_counts"]
    assert counts == {"RED": 1, "REPAIR_REQUIRED": 1, "YELLOW": 1, "PASS": 0, "PRODUCT_PASS": 1}
    assert matrix["aggregation"]["product_pass_is_release_ready"] is False
    assert matrix["aggregation"]["release_allowed"] is False


def test_p7_5_matrix_keeps_scorecard_family_sequence_aggregation_body_free() -> None:
    rows = [
        _base_row(family="structure_question"),
        build_p7_scorecard_row(
            product_quality_event=_event(family="long_meaning_arc"),
            p7_handoff_summary=_handoff(),
            sequence={"sequence_id": "sequence_7", "sequence_index": 7, "sequence_length": 7, "history_line_eligible": True},
        ),
    ]
    matrix = build_p7_evaluation_matrix(rows)
    aggregation = matrix["aggregation"]

    assert aggregation["history_line_counts"]["history_line_eligible_rows"] == 1
    assert aggregation["history_line_counts"]["history_line_non_eligible_rows"] == 1
    assert aggregation["by_sequence"]["sequence_7"]["row_kind"] == "sequence"
    assert aggregation["by_family"]["structure_question"]["p6_visible_allowed"] is True
    assert aggregation["by_family"]["long_meaning_arc"]["p6_visible_allowed"] is False

    dumped = json.dumps(matrix, ensure_ascii=False, sort_keys=True)
    assert SECRET_COMMENT not in dumped
    assert '"comment_text":' not in dumped
    assert '"raw_input":' not in dumped
    assert '"candidate_body":' not in dumped
    assert '"surface_body":' not in dumped
    assert '"release_allowed": true' not in dumped.lower()


def test_p7_5_matrix_contract_rejects_release_promotion_body_payload_and_p6_visible_expansion() -> None:
    matrix = build_p7_evaluation_matrix()

    unsafe_release = dict(matrix)
    unsafe_release["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_evaluation_matrix_contract(unsafe_release)

    unsafe_body = dict(matrix)
    unsafe_body["matrix_rows"] = [dict(row) for row in matrix["matrix_rows"]]
    unsafe_body["matrix_rows"][0]["comment_text"] = SECRET_COMMENT
    with pytest.raises(ValueError):
        assert_p7_evaluation_matrix_contract(unsafe_body)

    unsafe_p6 = dict(matrix)
    unsafe_p6["matrix_rows"] = [dict(row) for row in matrix["matrix_rows"]]
    for row in unsafe_p6["matrix_rows"]:
        if row["family"] == "daily_positive":
            row["p6_visible_allowed"] = True
            break
    with pytest.raises(ValueError):
        assert_p7_evaluation_matrix_contract(unsafe_p6)

    assert set(P7_VERDICTS) == {"RED", "REPAIR_REQUIRED", "YELLOW", "PASS", "PRODUCT_PASS"}
