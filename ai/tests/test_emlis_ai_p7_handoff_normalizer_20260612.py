# -*- coding: utf-8 -*-
from __future__ import annotations

import json

import pytest

from emlis_ai_p5_p6_split_test_matrix import P5_P6_HANDOFF_LOCK_SCHEMA_VERSION, build_p5_p6_handoff_lock
from emlis_ai_p7_contracts import P7_HANDOFF_SUMMARY_SCHEMA_VERSION, P7_INITIAL_RED_IDS
from emlis_ai_p7_handoff_normalizer import (
    assert_p7_handoff_summary_contract,
    build_p7_handoff_summary,
    normalize_p7_handoff_summary,
)

SECRET_INPUT = "P7-0 secret raw input must never be serialized"
SECRET_COMMENT = "P7-0 secret comment_text body must never be serialized"

FORBIDDEN_BODY_KEYS = {
    "raw_input",
    "rawInput",
    "raw_text",
    "rawText",
    "source_text",
    "sourceText",
    "input_text",
    "inputText",
    "user_input",
    "userInput",
    "current_input",
    "currentInput",
    "history_context",
    "historyContext",
    "history_records",
    "historyRecords",
    "history_raw_text",
    "historyRawText",
    "memo",
    "memo_text",
    "memoText",
    "memo_action",
    "memoAction",
    "comment_text",
    "commentText",
    "comment_text_body",
    "commentTextBody",
    "candidate_body",
    "candidateBody",
    "surface_body",
    "surfaceBody",
    "surface_text",
    "surfaceText",
    "visible_text",
    "visibleText",
    "reply_text",
    "replyText",
    "display_text",
    "displayText",
    "reviewer_free_text",
    "terminal_output",
    "stdout",
    "stderr",
    "traceback",
    "body",
    "text",
}


def _walk_keys(value: object) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            keys.add(str(key))
            keys.update(_walk_keys(child))
    elif isinstance(value, list):
        for child in value:
            keys.update(_walk_keys(child))
    return keys


def _sample_p5_summary(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "schema_version": "cocolon.emlis.user_label_connection.p5_runtime_bridge.v1",
        "runtime_evaluated": True,
        "visible_applied": True,
        "product_quality_confirmed": True,
        "human_qa_completed": False,
        "release_allowed": False,
        "body_free": {
            "raw_input_included": False,
            "comment_text_body_included": False,
            "candidate_body_included": False,
            "surface_body_included": False,
        },
    }
    value.update(overrides)
    return value


def _sample_p6_summary(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "schema_version": "cocolon.emlis.structure_insight.p6_runtime_bridge.v1",
        "runtime_evaluated": True,
        "visible_applied": True,
        "visible_family": "structure_question",
        "product_quality_review_ratings_only": True,
        "release_allowed": False,
        "body_free": {
            "raw_input_included": False,
            "comment_text_body_included": False,
            "candidate_body_included": False,
            "surface_body_included": False,
        },
    }
    value.update(overrides)
    return value


def test_p7_0_handoff_normalizer_keeps_p5_p6_runtime_connection_release_closed_and_body_free() -> None:
    handoff = build_p5_p6_handoff_lock(
        p5_runtime_bridge_summary=_sample_p5_summary(),
        p6_runtime_bridge_summary=_sample_p6_summary(),
    )
    summary = build_p7_handoff_summary(source_handoff=handoff)
    assert_p7_handoff_summary_contract(summary)

    assert summary["schema_version"] == P7_HANDOFF_SUMMARY_SCHEMA_VERSION
    assert summary["source_handoff_schema_version"] == P5_P6_HANDOFF_LOCK_SCHEMA_VERSION
    assert summary["scope"] == "P5_P6_to_P7_body_free_handoff"
    assert summary["release_allowed"] is False
    assert summary["p7_readiness"] == {
        "ready": False,
        "reason_codes": [
            "p7_red_ledger_required",
            "positive_recovery_red_open",
            "product_quality_connection_timeout_open",
            "release_decision_not_allowed",
            "p5_human_qa_hold",
            "p6_limited_surface_hold",
        ],
    }

    assert summary["p5"]["runtime_evaluated"] is True
    assert summary["p5"]["visible_applied"] is True
    assert summary["p5"]["product_quality_confirmed"] is True
    assert summary["p5"]["human_qa_completed"] is False
    assert summary["p5"]["history_connection_naturalness_confirmed"] is False
    assert summary["p5"]["creepy_absence_confirmed"] is False
    assert summary["p5"]["wants_more_input_confirmed"] is False
    assert summary["p5"]["status"] == "runtime_connected_hold"
    assert summary["p5"]["release_allowed"] is False

    assert summary["p6"]["runtime_evaluated"] is True
    assert summary["p6"]["visible_applied"] is True
    assert summary["p6"]["visible_family"] == "structure_question"
    assert summary["p6"]["visible_only_for_structure_question"] is True
    assert summary["p6"]["long_meaning_arc_visible_allowed"] is False
    assert summary["p6"]["self_understanding_follow_visible_allowed"] is False
    assert summary["p6"]["product_quality_review_ratings_only"] is True
    assert summary["p6"]["status"] == "limited_surface_connected_hold"
    assert summary["p6"]["release_allowed"] is False

    assert set(P7_INITIAL_RED_IDS).issubset(set(summary["red_refs"]))
    assert {"P7-HOLD-001", "P7-HOLD-002"}.issubset(set(summary["hold_refs"]))
    assert all(value is False for value in summary["public_contract"].values())
    assert all(value is False for value in summary["body_free"].values())
    assert not (set(_walk_keys(summary)) & FORBIDDEN_BODY_KEYS)

    dumped = json.dumps(summary, ensure_ascii=False, sort_keys=True)
    assert SECRET_INPUT not in dumped
    assert SECRET_COMMENT not in dumped
    assert '"comment_text":' not in dumped
    assert '"raw_input":' not in dumped
    assert '"candidate_body":' not in dumped
    assert '"surface_body":' not in dumped


def test_p7_0_handoff_normalizer_accepts_runtime_summaries_but_never_marks_p7_ready() -> None:
    summary = normalize_p7_handoff_summary(
        p5_runtime_bridge_summary=_sample_p5_summary(visible_applied=True, product_quality_confirmed=True),
        p6_runtime_bridge_summary=_sample_p6_summary(visible_applied=True, visible_family="structure_question"),
    )

    assert_p7_handoff_summary_contract(summary)
    assert summary["p5"]["status"] == "runtime_connected_hold"
    assert summary["p6"]["status"] == "limited_surface_connected_hold"
    assert summary["p7_readiness"]["ready"] is False
    assert "p5_human_qa_hold" in summary["p7_readiness"]["reason_codes"]
    assert "p6_limited_surface_hold" in summary["p7_readiness"]["reason_codes"]
    assert summary["release_allowed"] is False


def test_p7_0_handoff_normalizer_normalizes_p6_visible_family_to_structure_question_or_none() -> None:
    handoff = build_p5_p6_handoff_lock(
        p5_runtime_bridge_summary=_sample_p5_summary(),
        p6_runtime_bridge_summary=_sample_p6_summary(visible_applied=True, visible_family="daily_positive"),
    )
    summary = build_p7_handoff_summary(source_handoff=handoff)

    assert_p7_handoff_summary_contract(summary)
    assert summary["p6"]["visible_family"] == "none"
    assert summary["p6"]["visible_applied"] is False
    assert summary["p6"]["visible_only_for_structure_question"] is True
    assert summary["p6"]["long_meaning_arc_visible_allowed"] is False
    assert summary["p6"]["self_understanding_follow_visible_allowed"] is False


def test_p7_0_handoff_normalizer_rejects_body_payload_keys_before_normalization() -> None:
    unsafe_handoff = build_p5_p6_handoff_lock(
        p5_runtime_bridge_summary=_sample_p5_summary(),
        p6_runtime_bridge_summary=_sample_p6_summary(),
    )
    unsafe_handoff = dict(unsafe_handoff)
    unsafe_handoff["p5_handoff"] = dict(unsafe_handoff["p5_handoff"])
    unsafe_handoff["p5_handoff"]["comment_text"] = SECRET_COMMENT

    with pytest.raises(ValueError):
        build_p7_handoff_summary(source_handoff=unsafe_handoff)

    with pytest.raises(ValueError):
        build_p7_handoff_summary(
            p5_runtime_bridge_summary={"runtime_evaluated": True, "raw_input": SECRET_INPUT},
            p6_runtime_bridge_summary=_sample_p6_summary(),
        )


def test_p7_0_handoff_contract_rejects_public_contract_or_release_promotion() -> None:
    summary = build_p7_handoff_summary(
        p5_runtime_bridge_summary=_sample_p5_summary(),
        p6_runtime_bridge_summary=_sample_p6_summary(),
    )

    unsafe_ready = dict(summary)
    unsafe_ready["p7_readiness"] = dict(summary["p7_readiness"])
    unsafe_ready["p7_readiness"]["ready"] = True
    with pytest.raises(ValueError):
        assert_p7_handoff_summary_contract(unsafe_ready)

    unsafe_release = dict(summary)
    unsafe_release["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_handoff_summary_contract(unsafe_release)

    unsafe_contract = dict(summary)
    unsafe_contract["public_contract"] = dict(summary["public_contract"])
    unsafe_contract["public_contract"]["api_response_key_added"] = True
    with pytest.raises(ValueError):
        assert_p7_handoff_summary_contract(unsafe_contract)
