# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from emlis_ai_p5_p6_split_test_matrix import (
    P5_P6_HANDOFF_LOCK_SCHEMA_VERSION,
    P5_P6_R9_REPAIR_STEP,
    P5_P6_SPLIT_TEST_MATRIX_SCHEMA_VERSION,
    assert_p5_p6_handoff_lock_contract,
    assert_p5_p6_split_test_matrix_contract,
    build_p5_p6_handoff_lock,
    build_p5_p6_split_test_matrix,
)
from emlis_ai_public_feedback_meta import build_public_emlis_input_feedback_meta
from emlis_ai_user_label_connection_public_meta import USER_LABEL_CONNECTION_META_ONLY_META_KEY
from test_emlis_ai_user_label_connection_p5_runtime_bridge_20260612 import _install_p5_runtime_history_context

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPLY_SERVICE_PATH = PROJECT_ROOT / "services" / "ai_inference" / "emlis_ai_reply_service.py"
PUBLIC_META_PATH = PROJECT_ROOT / "services" / "ai_inference" / "emlis_ai_public_feedback_meta.py"
R9_MODULE_PATH = PROJECT_ROOT / "services" / "ai_inference" / "emlis_ai_p5_p6_split_test_matrix.py"

R9_REPLY_SERVICE_TOKENS = {
    "R9_P5P6SplitTestMatrixHandoff_20260612",
    "build_p5_p6_handoff_lock",
    "p5_p6_split_test_matrix_handoff",
    "r9_full_backend_suite_green_claim_allowed",
    "r9_combined_pytest_timeout_is_not_green",
    "r9_p7_ready",
    "r9_release_allowed",
}

R9_REQUIRED_GROUPS = {
    "r0_r8_targeted_runtime_repair",
    "p5_focused_runtime_and_boundary",
    "p6_focused_runtime_limited_surface_and_regression",
    "existing_runtime_public_regression",
    "no_connect_safety_low_info_regression",
    "rn_contract_external",
}

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


def _source(path: Path = REPLY_SERVICE_PATH) -> str:
    return path.read_text(encoding="utf-8")


def _missing_tokens(text: str, tokens: set[str]) -> list[str]:
    return sorted(token for token in tokens if token not in text)


def _walk_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            keys.add(str(key))
            keys.update(_walk_keys(child))
    elif isinstance(value, list):
        for item in value:
            keys.update(_walk_keys(item))
    return keys


def _contains_forbidden_body_key(value: Any) -> bool:
    if isinstance(value, dict):
        return any(str(key) in FORBIDDEN_BODY_KEYS or _contains_forbidden_body_key(child) for key, child in value.items())
    if isinstance(value, list):
        return any(_contains_forbidden_body_key(item) for item in value)
    return False


def _sample_p5_summary(**overrides: Any) -> dict[str, Any]:
    value = {
        "schema_version": "cocolon.emlis.user_label_connection.p5_runtime_bridge.v1",
        "runtime_evaluated": True,
        "visible_applied": False,
        "product_quality_confirmed": False,
        "human_qa_completed": False,
        "blocked_reason_codes": ["p5_product_quality_review_missing", "P5-HOLD-001"],
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


def _sample_p6_summary(**overrides: Any) -> dict[str, Any]:
    value = {
        "schema_version": "cocolon.emlis.structure_insight.p6_runtime_bridge.v1",
        "runtime_evaluated": True,
        "visible_applied": False,
        "visible_family": "none",
        "p5_dependency_status": "p5_ready",
        "r8_no_connect_regression": True,
        "no_connect_family_preserved": True,
        "no_connect_family_visible_applied": False,
        "p6_product_quality_review_ratings_only": True,
        "p6_visible_not_applied_reason_codes": ["r7_limited_surface_not_applied"],
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


def test_r9_latest_files_are_present_and_reply_service_is_wired_to_handoff_lock() -> None:
    assert R9_MODULE_PATH.exists()
    reply_source = _source(REPLY_SERVICE_PATH)
    public_meta_source = _source(PUBLIC_META_PATH)

    assert _missing_tokens(reply_source, R9_REPLY_SERVICE_TOKENS) == []
    assert "from emlis_ai_p5_p6_split_test_matrix import build_p5_p6_handoff_lock" in reply_source
    assert "p5_p6_split_test_matrix_handoff" not in public_meta_source
    assert "public_response_key_added\": True" not in reply_source
    assert "rn_visible_contract_changed\": True" not in reply_source
    assert "db_schema_changed\": True" not in reply_source


def test_r9_split_test_matrix_is_fixed_without_full_suite_green_claim() -> None:
    matrix = build_p5_p6_split_test_matrix()
    assert_p5_p6_split_test_matrix_contract(matrix)

    assert matrix["schema_version"] == P5_P6_SPLIT_TEST_MATRIX_SCHEMA_VERSION
    assert matrix["step"] == P5_P6_R9_REPAIR_STEP
    assert matrix["p7_out_of_scope"] is True
    assert matrix["full_backend_suite_green_claim_allowed"] is False
    assert matrix["full_backend_timeout_hang_must_be_ledgered"] is True
    assert matrix["combined_pytest_timeout_is_not_green"] is True
    assert matrix["release_allowed"] is False

    group_ids = {group["group_id"] for group in matrix["groups"]}
    assert R9_REQUIRED_GROUPS.issubset(group_ids)

    by_id = {group["group_id"]: group for group in matrix["groups"]}
    assert "tests/test_emlis_ai_user_label_connection_p5_runtime_bridge_20260612.py" in by_id[
        "p5_focused_runtime_and_boundary"
    ]["test_files"]
    assert "tests/test_emlis_ai_structure_insight_p6_runtime_bridge_20260612.py" in by_id[
        "p6_focused_runtime_limited_surface_and_regression"
    ]["test_files"]
    assert "tests/test_emlis_ai_structure_insight_p6_no_connect_regression_r8_20260612.py" in by_id[
        "p6_focused_runtime_limited_surface_and_regression"
    ]["test_files"]
    assert by_id["rn_contract_external"]["command"] == "npm run test:rn-screens --silent"


def test_r9_handoff_lock_separates_p5_p6_status_from_p7_and_release() -> None:
    handoff = build_p5_p6_handoff_lock(
        p5_runtime_bridge_summary=_sample_p5_summary(),
        p6_runtime_bridge_summary=_sample_p6_summary(),
    )
    assert_p5_p6_handoff_lock_contract(handoff)

    assert handoff["schema_version"] == P5_P6_HANDOFF_LOCK_SCHEMA_VERSION
    assert handoff["step"] == P5_P6_R9_REPAIR_STEP
    assert handoff["p7_out_of_scope"] is True
    assert handoff["p7_ready"] is False
    assert handoff["release_allowed"] is False
    assert handoff["full_backend_suite_green_claim_allowed"] is False
    assert handoff["combined_pytest_timeout_is_not_green"] is True

    assert handoff["p5_handoff"]["runtime_evaluated"] is True
    assert handoff["p5_handoff"]["visible_applied"] is False
    assert handoff["p5_handoff"]["product_quality_confirmed"] is False
    assert handoff["p5_handoff"]["product_quality_unconfirmed_blocks_release"] is True
    assert handoff["p5_handoff"]["release_allowed"] is False

    assert handoff["p6_handoff"]["runtime_evaluated"] is True
    assert handoff["p6_handoff"]["visible_family"] == "none"
    assert handoff["p6_handoff"]["visible_only_for_structure_question"] is True
    assert handoff["p6_handoff"]["no_connect_family_regression_green"] is True
    assert handoff["p6_handoff"]["product_quality_review_ratings_only"] is True
    assert handoff["p6_handoff"]["p7_ready"] is False
    assert handoff["p6_handoff"]["release_allowed"] is False

    assert not _contains_forbidden_body_key(handoff)
    assert not (set(_walk_keys(handoff)) & FORBIDDEN_BODY_KEYS)


def test_r9_public_meta_does_not_add_handoff_as_public_top_level_key() -> None:
    public_meta = build_public_emlis_input_feedback_meta(
        {
            "version": "emlis_ai_v3",
            "kernel_version": "multi_perspective_observation.v1",
            "observation_status": "passed",
            USER_LABEL_CONNECTION_META_ONLY_META_KEY: {
                "schema_version": "cocolon.emlis.user_label_connection.meta_only_integration.v1",
                "meta_only_connected": True,
                "history_connection_applied": False,
                "history_connection_blocked": True,
                "history_connection_edge_family_count": 1,
                "history_connection_evidence_record_count": 2,
                "scope_marker_required": True,
                "soft_marker_required": True,
                "raw_text_included": False,
                "history_raw_text_included": False,
                "comment_text_body_included": False,
                "candidate_body_included": False,
                "surface_body_included": False,
            },
            "p5_p6_split_test_matrix_handoff": build_p5_p6_handoff_lock(
                p5_runtime_bridge_summary=_sample_p5_summary(),
                p6_runtime_bridge_summary=_sample_p6_summary(),
            ),
        },
        comment_text_present=True,
        subscription_tier="plus",
    )

    assert "p5_p6_split_test_matrix_handoff" not in public_meta
    assert "p5_p6_handoff_lock" not in public_meta
    assert public_meta.get("public_response_key_added") is not True
    assert public_meta.get("release_allowed") is not True
    serialized = json.dumps(public_meta, ensure_ascii=False, sort_keys=True)
    assert "P5/P6 split test matrix" not in serialized


def test_r9_reply_service_keeps_internal_handoff_lock_static_contract() -> None:
    source = _source(REPLY_SERVICE_PATH)

    for token in (
        "build_p5_p6_handoff_lock",
        "p5_p6_split_test_matrix_handoff_summary",
        "meta[\"p5_p6_split_test_matrix_handoff\"]",
        "meta[\"p5_p6_handoff_lock\"]",
        "diagnostic_summary",
        "r9_full_backend_suite_green_claim_allowed",
        "r9_combined_pytest_timeout_is_not_green",
        "r9_p7_ready",
        "r9_release_allowed",
    ):
        assert token in source

    assert "r9_public_response_key_added" in source
    assert '"public_response_key_added": True' not in source
    assert '"rn_visible_contract_changed": True' not in source
    assert '"db_schema_changed": True' not in source
