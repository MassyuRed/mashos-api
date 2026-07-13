# -*- coding: utf-8 -*-
from __future__ import annotations

"""Receipt-only validation for NLS v2 Steps 8/9.

These tests never execute the Holdout pipeline and never parse Holdout bodies.
They validate the one-shot, body-free receipts and their frozen lineage.
"""

import hashlib
import json
from pathlib import Path

from helpers.emlis_nls_v2_s2_development import EVALUATION_FAMILIES, sha256_file, sha256_json
from emlis_ai_grounded_reception_candidate_selector_v2 import (
    DISTRIBUTION_THRESHOLD_FREEZE,
    selector_config_as_body_free_meta,
)


_TEST_ROOT = Path(__file__).resolve().parent
_AI_ROOT = _TEST_ROOT.parent
_REPO_ROOT = _AI_ROOT.parent
_FIXTURES = _TEST_ROOT / "fixtures"
_PROTOCOL_PATH = _FIXTURES / "emlis_nls_v2_s8_s9_protocol_freeze_20260713.json"
_A_RECEIPT_PATH = _FIXTURES / "emlis_nls_v2_s8_holdout_a_receipt_20260713.json"
_B_RECEIPT_PATH = _FIXTURES / "emlis_nls_v2_s9_holdout_b_receipt_20260713.json"
_RUNNER_PATH = _TEST_ROOT / "helpers" / "emlis_nls_v2_s8_s9_holdout.py"
_REPLY_SERVICE_PATH = (
    _AI_ROOT / "services" / "ai_inference" / "emlis_ai_reply_service.py"
)
_FORBIDDEN_BODY_KEYS = frozenset(
    {
        "current_input",
        "memo",
        "memo_action",
        "text",
        "v1_text",
        "v2_text",
        "left_text",
        "right_text",
        "surface_text",
        "candidate_text",
        "selected_text",
        "raw_input",
        "raw_text",
        "source_text",
        "comment_text",
        "expected_text",
        "note",
        "reason",
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


def _assert_distribution_pass(distribution: dict) -> None:
    thresholds = DISTRIBUTION_THRESHOLD_FREEZE
    assert distribution["exact_duplicate_count"] <= thresholds["exact_duplicate_max"]
    assert distribution["rich_single_sentence_count"] <= thresholds[
        "rich_single_sentence_max"
    ]
    assert distribution["short_meaningless_inflation_count"] <= thresholds[
        "short_meaningless_inflation_max"
    ]
    assert distribution["max_strategy_share"] <= thresholds["strategy_share_max"]
    assert distribution["max_terminal_family_share"] <= thresholds[
        "terminal_family_share_max"
    ]
    assert distribution["max_predicate_family_share"] <= thresholds[
        "predicate_family_share_max"
    ]
    assert distribution["max_skeleton_share"] <= thresholds["skeleton_share_max"]


def _assert_holdout_pass(receipt: dict, cohort: str) -> None:
    assert receipt["schema_version"] == (
        "cocolon.emlis.nls_v2.holdout_evaluation_receipt.v1"
    )
    assert receipt["cohort"] == cohort
    assert receipt["case_count"] == 14
    assert receipt["evaluation_run_count"] == 1
    assert receipt["overall_status"] == "pass"
    assert receipt["source_or_protocol_change_count"] == 0
    assert receipt["candidate_bodies_included"] is False
    assert receipt["selected_bodies_included"] is False
    assert receipt["raw_input_included"] is False
    assert receipt["raw_text_included"] is False
    assert receipt["expected_text_included"] is False
    assert receipt["runtime_connected"] is False
    assert receipt["public_contract_changed"] is False
    _assert_body_free(receipt)

    automatic = receipt["automatic_gate"]
    assert automatic["case_count"] == 14
    assert automatic["selected_count"] == 14
    assert automatic["v2_no_valid_candidate_count"] == 0
    assert automatic["machine_failure_case_count"] == 0
    assert automatic["v1_fallback_used_count"] == 0
    assert automatic["runtime_connected_count"] == 0
    assert automatic["distribution_pass"] is True
    _assert_distribution_pass(automatic["distribution"])

    human = receipt["human_review"]
    assert human["automatic_gate_separate"] is True
    assert human["case_id_hidden_during_review"] is True
    assert human["variant_identity_hidden_during_review"] is True
    assert human["v1_left_count"] == 7
    assert human["v1_right_count"] == 7
    assert human["absolute_conditions"]["failure_case_count"] == 0
    assert human["absolute_conditions"]["fatal_semantic_failure_count"] == 0
    assert human["absolute_conditions"]["pass"] is True
    product = human["product_metrics"]
    assert product["read_feeling_pass_count"] >= 13
    assert product["naturalness_pass_count"] >= 13
    assert product["non_template_pass_count"] >= 13
    assert product["wants_more_input_or_accumulation_pass_count"] >= 13
    assert product["self_blame_non_amplification_pass_count"] == 14
    assert product["overclaim_absence_pass_count"] == 14
    assert product["wants_more_floor_pass"] is True
    assert product["roadmap_product_target_pass"] is True
    paired = human["paired_comparison"]
    assert paired["v2_clearly_better_count"] >= 10
    assert paired["v1_clearly_better_count"] <= 1
    assert paired["same_count"] <= 3
    assert sum(
        paired[key]
        for key in (
            "v2_clearly_better_count",
            "same_count",
            "v1_clearly_better_count",
        )
    ) == 14
    assert paired["pass"] is True
    assert len(receipt["rows"]) == 14
    assert {row["family"] for row in receipt["rows"]} == set(EVALUATION_FAMILIES)
    assert all(not row["machine_failure_codes"] for row in receipt["rows"])
    assert all(not row["human_absolute_failure_codes"] for row in receipt["rows"])


def test_step8_step9_protocol_freeze_is_live_and_unchanged() -> None:
    protocol = _load(_PROTOCOL_PATH)
    assert protocol["schema_version"] == "cocolon.emlis.nls_v2.s8_s9.protocol_freeze.v1"
    assert protocol["created_before_holdout_a_parse"] is True
    assert protocol["holdout_a_evaluation_run_limit"] == 1
    assert protocol["holdout_b_evaluation_run_limit"] == 1
    assert protocol["holdout_b_requires_holdout_a_pass"] is True
    assert protocol["post_holdout_a_code_fixture_weight_change_allowed"] is False

    dependency_rows = [
        {
            "path": row["path"],
            "sha256": sha256_file(_REPO_ROOT / row["path"]),
        }
        for row in protocol["dependency_closure"]["files"]
    ]
    assert dependency_rows == protocol["dependency_closure"]["files"]
    assert sha256_json(dependency_rows) == protocol["dependency_closure"]["sha256"]
    assert sha256_json(selector_config_as_body_free_meta()) == protocol[
        "step7_freeze"
    ]["selector_config_sha256"]
    assert sha256_file(_RUNNER_PATH) == protocol["evaluation_protocol"]["runner_sha256"]
    assert sha256_file(Path(__file__)) == protocol["evaluation_protocol"][
        "receipt_test_sha256"
    ]
    assert sha256_file(_REPLY_SERVICE_PATH) == protocol["runtime_boundary"][
        "reply_service_sha256"
    ]
    reply_source = _REPLY_SERVICE_PATH.read_text(encoding="utf-8")
    assert "emlis_ai_grounded_reception_candidate_selector_v2" not in reply_source
    assert "evaluate_and_select_reception_candidate_v2" not in reply_source


def test_step8_holdout_a_one_shot_body_free_receipt_passes() -> None:
    protocol = _load(_PROTOCOL_PATH)
    receipt = _load(_A_RECEIPT_PATH)
    _assert_holdout_pass(receipt, "holdout_a")
    assert receipt["protocol_freeze_sha256"] == sha256_file(_PROTOCOL_PATH)
    assert receipt["fixture_sha256"] == protocol["holdout_fixtures"]["holdout_a"][
        "fixture_sha256"
    ]


def test_step9_holdout_b_one_shot_body_free_receipt_passes_without_a_to_b_change() -> None:
    protocol = _load(_PROTOCOL_PATH)
    receipt = _load(_B_RECEIPT_PATH)
    _assert_holdout_pass(receipt, "holdout_b")
    assert receipt["protocol_freeze_sha256"] == sha256_file(_PROTOCOL_PATH)
    assert receipt["fixture_sha256"] == protocol["holdout_fixtures"]["holdout_b"][
        "fixture_sha256"
    ]
    combined = receipt["a_b_combined"]
    assert combined["holdout_a_receipt_sha256"] == sha256_file(_A_RECEIPT_PATH)
    assert combined["holdout_a_status"] == "pass"
    assert combined["holdout_b_status"] == "pass"
    assert combined["family_large_reversal_count"] == 0
    assert combined["family_large_reversal_codes"] == []
    assert combined["a_to_b_source_or_protocol_change_count"] == 0
    assert combined["both_holdouts_pass"] is True


def test_step8_step9_receipts_share_exact_frozen_source_config_runner_and_runtime() -> None:
    protocol = _load(_PROTOCOL_PATH)
    a = _load(_A_RECEIPT_PATH)
    b = _load(_B_RECEIPT_PATH)
    for key in (
        "protocol_freeze_sha256",
        "dependency_closure_sha256",
        "selector_config_sha256",
        "evaluation_runner_sha256",
        "receipt_test_sha256",
        "reply_service_sha256",
    ):
        assert a[key] == b[key]
    assert a["dependency_closure_sha256"] == protocol["dependency_closure"]["sha256"]
    assert a["selector_config_sha256"] == protocol["step7_freeze"][
        "selector_config_sha256"
    ]
    assert a["evaluation_runner_sha256"] == protocol["evaluation_protocol"][
        "runner_sha256"
    ]
    assert a["receipt_test_sha256"] == protocol["evaluation_protocol"][
        "receipt_test_sha256"
    ]
    assert a["reply_service_sha256"] == protocol["runtime_boundary"][
        "reply_service_sha256"
    ]


def test_step8_step9_do_not_reexecute_holdouts_from_tests_or_persist_review_bodies() -> None:
    source = Path(__file__).read_text(encoding="utf-8")
    assert "evaluate_holdout_once(" not in source
    assert "load_holdout_cases_for_one_shot(" not in source
    assert "prepare_blind_review_once(" not in source
    for receipt_path in (_A_RECEIPT_PATH, _B_RECEIPT_PATH):
        payload = _load(receipt_path)
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        assert "left_text" not in encoded
        assert "right_text" not in encoded
        assert "current_input" not in encoded

