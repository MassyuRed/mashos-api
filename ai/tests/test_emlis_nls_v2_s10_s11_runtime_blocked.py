# -*- coding: utf-8 -*-
from __future__ import annotations

"""Fail-closed guards for NLS v2 Steps 10/11 after Holdout A STOP."""

import json
from pathlib import Path

from helpers.emlis_nls_v2_s2_development import sha256_file


_TEST_ROOT = Path(__file__).resolve().parent
_AI_ROOT = _TEST_ROOT.parent
_REPO_ROOT = _AI_ROOT.parent
_FIXTURE_ROOT = _TEST_ROOT / "fixtures"
_BLOCKED_PATH = (
    _FIXTURE_ROOT / "emlis_nls_v2_s10_s11_runtime_blocked_20260713.json"
)
_A_RECEIPT_PATH = (
    _FIXTURE_ROOT / "emlis_nls_v2_s8_holdout_a_receipt_20260713.json"
)
_B_RECEIPT_PATH = (
    _FIXTURE_ROOT / "emlis_nls_v2_s9_holdout_b_receipt_20260713.json"
)
_S1_RECEIPT_PATH = _FIXTURE_ROOT / "emlis_nls_v2_s1_receipt_20260713.json"
_RUNTIME_PATHS = (
    _AI_ROOT / "services" / "ai_inference" / "emlis_ai_grounded_sentence_surface.py",
    _AI_ROOT / "services" / "ai_inference" / "emlis_ai_grounded_observation_gate.py",
    _AI_ROOT / "services" / "ai_inference" / "emlis_ai_reply_service.py",
)
_V2_RUNTIME_TOKENS = (
    "emlis_ai_grounded_reception_content_plan_v2",
    "emlis_ai_grounded_reception_candidate_plan_v2",
    "emlis_ai_grounded_human_reception_v2",
    "emlis_ai_grounded_reception_candidate_selector_v2",
    "build_reception_content_plan_v2",
    "build_reception_candidate_plans_v2",
    "generate_reception_surface_candidates_v2",
    "evaluate_and_select_reception_candidate_v2",
)
_FORBIDDEN_BODY_KEYS = frozenset(
    {
        "current_input",
        "memo",
        "memo_action",
        "text",
        "surface_text",
        "candidate_text",
        "selected_text",
        "raw_input",
        "raw_text",
        "source_text",
        "comment_text",
        "expected_text",
    }
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_body_free(value) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            assert key not in _FORBIDDEN_BODY_KEYS
            _assert_body_free(child)
    elif isinstance(value, list):
        for child in value:
            _assert_body_free(child)


def test_step10_step11_are_blocked_by_live_holdout_receipts() -> None:
    blocked = _load(_BLOCKED_PATH)
    a = _load(_A_RECEIPT_PATH)
    b = _load(_B_RECEIPT_PATH)

    assert blocked["schema_version"] == (
        "cocolon.emlis.nls_v2.s10_s11.runtime_blocked.v1"
    )
    assert blocked["decision"] == "blocked_fail_closed"
    assert blocked["prerequisite_evidence"]["both_holdouts_pass"] is False
    assert blocked["prerequisite_evidence"]["runtime_progression_allowed"] is False

    a_meta = blocked["prerequisite_evidence"]["holdout_a"]
    assert sha256_file(_A_RECEIPT_PATH) == a_meta["receipt_sha256"]
    assert a["overall_status"] == a_meta["overall_status"] == "stop"
    paired = a["human_review"]["paired_comparison"]
    assert paired["v2_clearly_better_count"] == a_meta["v2_clearly_better_count"] == 5
    assert paired["same_count"] == a_meta["same_count"] == 3
    assert paired["v1_clearly_better_count"] == a_meta["v1_clearly_better_count"] == 6
    assert paired["pass"] is a_meta["paired_pass"] is False
    assert a["human_review"]["product_metrics"][
        "roadmap_product_target_pass"
    ] is a_meta["roadmap_product_target_pass"] is False
    assert a["automatic_gate"]["distribution_pass"] is a_meta[
        "distribution_pass"
    ] is False

    b_meta = blocked["prerequisite_evidence"]["holdout_b"]
    assert sha256_file(_B_RECEIPT_PATH) == b_meta["receipt_sha256"]
    assert b["overall_status"] == b_meta["overall_status"] == "not_evaluated"
    assert b["evaluation_run_count"] == b_meta["evaluation_run_count"] == 0
    assert b["opened_for_evaluation"] is b_meta["opened_for_evaluation"] is False
    assert b["fixture_parsed"] is b_meta["fixture_parsed"] is False


def test_step10_shadow_remains_not_executed_and_does_not_invent_budgets() -> None:
    blocked = _load(_BLOCKED_PATH)
    step10 = blocked["step10_runtime_preconnection_shadow"]
    assert step10 == {
        "status": "not_executed",
        "shadow_run_count": 0,
        "v1_v2_simultaneous_runtime_generation_enabled": False,
        "v2_runtime_import_added": False,
        "v2_body_written_to_public_meta": False,
        "v2_body_written_to_db": False,
        "public_response_changed": False,
        "latency_measurement_performed": False,
        "latency_budget_ms": None,
        "latency_budget_invented": False,
        "fallback_rate_measurement_performed": False,
        "gate_result_runtime_measurement_performed": False,
        "grounded_sentence_surface_connection_attempted": False,
        "completion_status": "blocked_by_prior_holdout_stop",
    }


def test_step11_runtime_owner_stays_canonical_v1_and_v2_stays_offline() -> None:
    blocked = _load(_BLOCKED_PATH)
    step11 = blocked["step11_runtime_owner_switch"]
    assert step11["status"] == "not_executed"
    assert step11["owner_switch_count"] == 0
    assert step11["owner_before"] == "grounded_sentence_surface_canonical_v1"
    assert step11["owner_after"] == "grounded_sentence_surface_canonical_v1"
    assert step11["v2_internal_switch_added"] is False
    assert step11["v1_fallback_path_changed"] is False
    assert step11["fallback_acceptance_rate"] is None
    assert step11["fallback_acceptance_rate_invented"] is False
    assert step11["final_v2_text_forwarded_to_two_stage_surface"] is False

    runtime = blocked["runtime_boundary"]
    assert runtime["production_owner"] == "v1"
    assert runtime["v2_state"] == "offline_only"
    assert runtime["runtime_source_modified_count"] == 0
    for path in _RUNTIME_PATHS:
        source = path.read_text(encoding="utf-8")
        assert all(token not in source for token in _V2_RUNTIME_TOKENS)
    sentence_source = _RUNTIME_PATHS[0].read_text(encoding="utf-8")
    assert 'GROUND_SURFACE_GENERATION_PATH: Final = "grounded_sentence_surface_canonical_v1"' in sentence_source


def test_step10_step11_preserve_step1_runtime_sources_and_public_contract() -> None:
    blocked = _load(_BLOCKED_PATH)
    runtime = blocked["runtime_boundary"]
    live_rows = [
        {"path": row["path"], "sha256": sha256_file(_REPO_ROOT / row["path"])}
        for row in runtime["runtime_source_files"]
    ]
    assert live_rows == runtime["runtime_source_files"]

    s1 = _load(_S1_RECEIPT_PATH)
    s1_by_path = {row["path"]: row["sha256"] for row in s1["source_snapshot_files"]}
    assert all(s1_by_path[row["path"]] == row["sha256"] for row in live_rows)
    assert runtime["api_contract_changed"] is False
    assert runtime["db_contract_changed"] is False
    assert runtime["rn_contract_changed"] is False
    assert runtime["public_contract_diff_count"] == 0
    assert blocked["production_files_modified"] == []
    assert blocked["holdout_files_modified"] == []
    _assert_body_free(blocked)

