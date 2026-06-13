# -*- coding: utf-8 -*-
from __future__ import annotations

import json

from emlis_ai_p7_event_bridge import (
    P7_P6_VISIBLE_BOUNDARY_SCHEMA_VERSION,
    assert_p7_p6_family_boundary_contract,
    assert_p7_p6_visible_expansion_boundary_contract,
    build_p7_p6_visible_expansion_boundary_validation,
    build_p7_scorecard_row,
    p7_p6_family_boundary_for_family,
)
from emlis_ai_p7_validation_matrix import build_p7_validation_regression_matrix
from test_emlis_ai_p7_event_bridge_20260612 import _event, _handoff

SECRET_INPUT = "R9 secret raw input must never enter boundary material"
SECRET_COMMENT = "R9 secret comment_text body must never enter boundary material"


def test_r9_p6_family_boundary_keeps_visible_structure_question_only() -> None:
    structure = p7_p6_family_boundary_for_family("structure_question", runtime_evaluated=True, visible_applied=True)
    long_arc = p7_p6_family_boundary_for_family("long_meaning_arc", runtime_evaluated=True, visible_applied=True)
    self_follow = p7_p6_family_boundary_for_family("self_understanding_follow", runtime_evaluated=True, visible_applied=False)
    daily = p7_p6_family_boundary_for_family("daily_positive", runtime_evaluated=True, visible_applied=True)

    for policy in (structure, long_arc, self_follow, daily):
        assert_p7_p6_family_boundary_contract(policy)
        assert policy["schema_version"] == P7_P6_VISIBLE_BOUNDARY_SCHEMA_VERSION
        assert policy["visible_expansion_allowed"] is False
        assert policy["visible_expansion_requires_future_design"] is True
        assert "P7-HOLD-002" in policy["p7_holds"]
        assert policy["release_allowed"] is False

    assert structure["visible_applied_allowed"] is True
    assert structure["visible_family"] == "structure_question"
    assert long_arc["family_status"] == "meta_only"
    assert long_arc["visible_applied_violation"] is True
    assert self_follow["family_status"] == "meta_only"
    assert daily["family_status"] == "no_connect"
    assert daily["visible_applied_violation"] is True


def test_r9_scorecard_rows_suppress_non_structure_visible_and_validation_material_stays_body_free() -> None:
    structure_row = build_p7_scorecard_row(product_quality_event=_event(family="structure_question", row_id="r9_structure"), p7_handoff_summary=_handoff())
    daily_row = build_p7_scorecard_row(product_quality_event=_event(family="daily_positive", row_id="r9_daily"), p7_handoff_summary=_handoff())
    long_row = build_p7_scorecard_row(product_quality_event=_event(family="long_meaning_arc", row_id="r9_long"), p7_handoff_summary=_handoff())

    assert structure_row["p6"]["visible_applied"] is True
    assert daily_row["p6"]["visible_applied"] is False
    assert daily_row["p6"]["visible_family"] == "none"
    assert daily_row["p6"]["family_boundary_status"] == "no_connect"
    assert daily_row["p6"]["visible_request_suppressed"] is True
    assert long_row["p6"]["family_boundary_status"] == "meta_only"

    boundary = build_p7_p6_visible_expansion_boundary_validation([structure_row, daily_row, long_row])
    assert_p7_p6_visible_expansion_boundary_contract(boundary)
    assert boundary["validation_status"] == "passed"
    assert boundary["violation_count"] == 0
    assert boundary["visible_allowed_families"] == ["structure_question"]
    assert "long_meaning_arc" in boundary["meta_only_families"]
    assert "daily_positive" in boundary["no_connect_families"]
    assert boundary["visible_expansion_allowed"] is False
    assert boundary["release_allowed"] is False

    dumped = json.dumps(boundary, ensure_ascii=False, sort_keys=True)
    assert SECRET_INPUT not in dumped
    assert SECRET_COMMENT not in dumped
    assert '"raw_input":' not in dumped
    assert '"comment_text":' not in dumped
    assert '"candidate_body":' not in dumped
    assert '"surface_body":' not in dumped
    assert '"release_allowed": true' not in dumped.lower()


def test_r9_validation_matrix_keeps_p6_hold002_without_calling_p7_complete_or_p8_ready() -> None:
    validation = build_p7_validation_regression_matrix()

    assert validation["summary"]["p6_visible_expansion_blocked"] is True
    assert validation["summary"]["p6_visible_expansion_boundary_validated"] is True
    assert validation["summary"]["p6_visible_expansion_violation_count"] == 0
    assert "P7-HOLD-002" in validation["unresolved_hold_refs"]
    assert validation["summary"]["p8_start_allowed"] is False
    assert validation["release_allowed"] is False
    assert any(row["check_kind"] == "p6_visible_expansion_boundary" for row in validation["matrix_rows"])
