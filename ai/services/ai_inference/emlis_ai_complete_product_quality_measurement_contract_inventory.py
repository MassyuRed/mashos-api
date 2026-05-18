# -*- coding: utf-8 -*-
"""Step 0 contract inventory for Emlis Product Gate measurement.

This module fixes the implementation boundary for the ProductGate Measurement
connection work.  It is intentionally meta-only: it does not touch runtime
response shape, DB physical names, RN display conditions, or EmlisAI gates.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

PRODUCT_GATE_MEASUREMENT_CONTRACT_INVENTORY_VERSION = (
    "emlis.complete_product_quality_measurement_contract_inventory.v1"
)

_FORBIDDEN_TEXT_PAYLOAD_KEYS = {
    "raw_input", "rawInput", "input", "input_text", "inputText",
    "memo", "memo_text", "memoText", "current_input", "currentInput",
    "comment_text", "commentText", "input_feedback_comment", "inputFeedbackComment",
    "public_comment_text", "candidate_comment_text", "reply_text", "text",
}

_ALLOWED_TOUCH_FILES = (
    "ai/services/ai_inference/emlis_ai_complete_product_quality_measurement_contract_inventory.py",
    "ai/services/ai_inference/emlis_ai_observation_diagnostic_compare.py",
    "ai/services/ai_inference/emlis_ai_observation_diagnostic_branching.py",
    "ai/services/ai_inference/emlis_ai_complete_product_quality_measurement_connection.py",
    "ai/services/ai_inference/emlis_ai_complete_product_quality_scorecard_service.py",
    "ai/services/ai_inference/emlis_ai_complete_release_ladder_service.py",
    "ai/tools/emlis_observation_product_quality_measurement.py",
    "ai/tests/test_emlis_ai_observation_diagnostic_compare_step7.py",
    "ai/tests/test_emlis_ai_observation_diagnostic_branching_step8.py",
    "ai/tests/test_emlis_ai_complete_product_quality_measurement_contract_inventory_step0.py",
    "ai/tests/test_emlis_ai_complete_product_quality_measurement_connection.py",
    "ai/tests/test_emlis_ai_complete_product_quality_scorecard.py",
    "ai/tests/test_emlis_ai_complete_product_quality_scorecard_blind_qa.py",
    "ai/tests/test_emlis_observation_product_quality_measurement_tool_step8.py",
    "ai/tests/test_emlis_ai_complete_product_quality_measurement_regression_step9.py",
    "ai/tests/test_emlis_ai_complete_product_quality_measurement_exit_gate_step10.py",
    "ai/tests/contract/test_emlis_ai_contracts.py",
    "ai/tests/contract/test_rn_surface_guards.py",
)

_CONTRACT_LOCKS = (
    {
        "contract_id": "emotion_submit_route_stable",
        "owner": "backend_public_api",
        "must_keep": "POST /emotion/submit",
        "change_allowed": False,
    },
    {
        "contract_id": "input_feedback_comment_public_key_stable",
        "owner": "backend_public_response",
        "must_keep": "input_feedback.comment_text",
        "change_allowed": False,
    },
    {
        "contract_id": "input_feedback_emlis_ai_status_stable",
        "owner": "backend_public_response_and_rn_reader",
        "must_keep": "input_feedback.emlis_ai.observation_status",
        "change_allowed": False,
    },
    {
        "contract_id": "rn_passed_only_modal_contract",
        "owner": "Cocolon RN",
        "must_keep": "public observation_status=passed and public comment presence are both required",
        "change_allowed": False,
    },
    {
        "contract_id": "db_physical_name_boundary",
        "owner": "storage_boundary",
        "must_keep": "no DB physical rename/drop/write-path change in measurement steps",
        "change_allowed": False,
    },
    {
        "contract_id": "gate_fail_closed_boundary",
        "owner": "EmlisAI backend gates",
        "must_keep": "Reader/Grounding/Template/Display gates are not relaxed by measurement",
        "change_allowed": False,
    },
    {
        "contract_id": "meta_only_diagnostic_boundary",
        "owner": "backend_and_frontend_diagnostic",
        "must_keep": "raw input body and public comment body stay out of logs/reports",
        "change_allowed": False,
    },
    {
        "contract_id": "blind_qa_read_feeling_boundary",
        "owner": "ProductQualityScorecard",
        "must_keep": "read_feeling_score is populated only from Blind QA ratings, never from machine metrics",
        "change_allowed": False,
    },
    {
        "contract_id": "next_action_routing_before_repair_boundary",
        "owner": "ProductGateMeasurement Step7",
        "must_keep": "top rejection reasons / release blockers / classification decide the next branch before cause repair",
        "change_allowed": False,
    },
    {
        "contract_id": "local_tool_output_meta_only_boundary",
        "owner": "ProductGateMeasurement Step8",
        "must_keep": "local JSON/Markdown reports are generated from one-line diagnostics without raw input or public comment bodies",
        "change_allowed": False,
    },
    {
        "contract_id": "step9_regression_public_contract_boundary",
        "owner": "ProductGateMeasurement Step9",
        "must_keep": "regression tests cover diagnostic, scorecard, release, local tool, and RN public contract expectations without runtime changes",
        "change_allowed": False,
    },
    {
        "contract_id": "step9_regression_counting_semantics_boundary",
        "owner": "ProductGateMeasurement Step9",
        "must_keep": "backend passed is not counted as display unless display_confirmed is true",
        "change_allowed": False,
    },
    {
        "contract_id": "step10_exit_gate_measurement_only_boundary",
        "owner": "ProductGateMeasurement Step10",
        "must_keep": "Exit Gate completes measurement connection only; it does not declare Product Gate achievement or apply public release",
        "change_allowed": False,
    },
    {
        "contract_id": "step10_exit_gate_fact_based_next_action_boundary",
        "owner": "ProductGateMeasurement Step10",
        "must_keep": "next action is decidable from capture/classification/display_confirmed/scorecard_event/release_ladder facts",
        "change_allowed": False,
    },
    {
        "contract_id": "step10_exit_gate_not_product_gate_boundary",
        "owner": "ProductGateMeasurement Step10",
        "must_keep": "Exit Gate completes measurement connection only; Product Gate achievement and public release stay false",
        "change_allowed": False,
    },
    {
        "contract_id": "step10_exit_gate_fixture_coverage_boundary",
        "owner": "ProductGateMeasurement Step10",
        "must_keep": "diagnostic missing, backend rejected, passed hidden, and display confirmed fixtures are covered by regression",
        "change_allowed": False,
    },
    {
        "contract_id": "step10_exit_gate_measurement_connection_boundary",
        "owner": "ProductGateMeasurement Step10",
        "must_keep": "capture/classification/display_confirmed/scorecard_event are present per submit before next implementation planning",
        "change_allowed": False,
    },
)

_NON_TARGETS = (
    "RN display condition relaxation",
    "API response key rename",
    "DB physical name rename/drop/write-path change",
    "Reader/Grounding/Template/Display Gate relaxation",
    "fixed fallback observation sentence addition",
    "external AI/runtime service addition",
    "Product Gate achieved/public release declaration",
    "machine-inferred read_feeling_score",
    "cause repair before next_action_branch classification is fixed",
    "raw input or public comment body in local tool output",
    "regression tests as public release or Product Gate achievement declaration",
    "Step10 Exit Gate as Product Gate achievement/public release declaration",
)

_MEASUREMENT_STEPS_IN_SCOPE = (
    "Step0: contract inventory",
    "Step1: diagnostic capture status",
    "Step2: backend/frontend join semantics",
    "Step3: joined row -> scorecard event adapter",
    "Step4: measurement run builder",
    "Step5: coverage group aggregation",
    "Step6: Blind QA separation",
    "Step7: next action routing",
    "Step8: local tool output",
    "Step9: regression tests",
    "Step10: Exit Gate",
)

_REGRESSION_TEST_TARGETS = (
    "diagnostic_compare_capture_and_join_semantics",
    "measurement_connection_scorecard_and_release_ladder",
    "local_tool_json_markdown_meta_only_output",
    "rn_passed_only_contract_expectations_no_runtime_change",
    "public_route_response_db_gate_contract_locks",
    "measurement_exit_gate_connection_not_product_gate_release",
    "exit_gate_four_fixture_semantics",
    "exit_gate_summary_report_contract",
)


def _clean(value: Any) -> str:
    if value is None or isinstance(value, (Mapping, list, tuple, set)):
        return ""
    return str(value).strip()


def _contains_forbidden_text_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if _clean(key) in _FORBIDDEN_TEXT_PAYLOAD_KEYS:
                return True
            if _contains_forbidden_text_payload_key(nested):
                return True
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_forbidden_text_payload_key(item) for item in value)
    return False


def assert_product_gate_measurement_contract_inventory_meta_only(
    value: Mapping[str, Any],
    *,
    source: str = "contract_inventory",
) -> None:
    if _contains_forbidden_text_payload_key(value):
        raise ValueError(f"{source} contains a forbidden text payload key")
    if value.get("raw_input_included") is True or value.get("comment_text_included") is True:
        raise ValueError(f"{source} marks raw input or comment text as included")


def build_product_gate_measurement_contract_inventory() -> dict[str, Any]:
    """Return the Step0 inventory used to keep ProductGate measurement bounded.

    The inventory is a read-only, meta-only contract list.  It is not a release
    flag and it does not alter any public API/RN/DB contract.
    """

    inventory: dict[str, Any] = {
        "version": PRODUCT_GATE_MEASUREMENT_CONTRACT_INVENTORY_VERSION,
        "source": "emlis_product_gate_measurement_step0_contract_inventory",
        "scope": "Complete Composer ProductGate Measurement Step0-10",
        "status": "fixed",
        "measurement_connection_only": True,
        "product_gate_achieved": False,
        "public_release_applied": False,
        "steps_in_scope": list(_MEASUREMENT_STEPS_IN_SCOPE),
        "allowed_touch_files": list(_ALLOWED_TOUCH_FILES),
        "contract_locks": [dict(item) for item in _CONTRACT_LOCKS],
        "non_targets": list(_NON_TARGETS),
        "regression_tests_ready": True,
        "exit_gate_ready": True,
        "exit_gate_required": True,
        "exit_gate_ready_requires_measurement_connection": True,
        "exit_gate_is_product_gate_achievement": False,
        "step10_exit_gate_required": True,
        "step10_exit_gate_contract_ready": True,
        "step10_exit_gate_is_product_gate_achievement": False,
        "step10_exit_gate_public_release_applied": False,
        "step10_exit_gate_is_public_release": False,
        "step10_fixture_regression_required": True,
        "step10_required_fixture_classes": [
            "diagnostic_missing",
            "backend_rejected",
            "passed_hidden",
            "display_confirmed",
        ],
        "measurement_connection_completion_not_product_gate_release": True,
        "measurement_connection_complete_definition": "submit rows -> scorecard events -> scorecard -> release ladder -> next action branch, with public release closed",
        "exit_gate_required_fixture_classes": [
            "diagnostic_missing",
            "backend_rejected",
            "passed_backend_frontend_hidden",
            "display_confirmed",
        ],
        "exit_gate_minimum_fixture_classes": [
            "diagnostic_missing",
            "backend_rejected",
            "passed_backend_frontend_hidden",
            "display_confirmed",
        ],
        "step9_regression_tests_required": True,
        "step9_regression_tests_are_public_release": False,
        "regression_public_contract_checks_required": True,
        "regression_meta_only_checks_required": True,
        "regression_display_counting_checks_required": True,
        "regression_rn_contract_checks_required": True,
        "rn_runtime_files_modified_by_measurement": False,
        "regression_test_targets": list(_REGRESSION_TEST_TARGETS),
        "rn_visible_contract_change_allowed": False,
        "api_response_key_change_allowed": False,
        "db_physical_rename_allowed": False,
        "gate_relaxation_allowed": False,
        "blind_qa_required": True,
        "read_feeling_requires_blind_qa": True,
        "machine_metrics_used_for_read_feeling": False,
        "raw_input_included": False,
        "comment_text_included": False,
    }
    assert_product_gate_measurement_contract_inventory_meta_only(inventory)
    return inventory


def dump_product_gate_measurement_contract_inventory(inventory: Mapping[str, Any] | None = None) -> str:
    data = dict(inventory or build_product_gate_measurement_contract_inventory())
    data["raw_input_included"] = False
    data["comment_text_included"] = False
    assert_product_gate_measurement_contract_inventory_meta_only(data)
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "PRODUCT_GATE_MEASUREMENT_CONTRACT_INVENTORY_VERSION",
    "assert_product_gate_measurement_contract_inventory_meta_only",
    "build_product_gate_measurement_contract_inventory",
    "dump_product_gate_measurement_contract_inventory",
]
