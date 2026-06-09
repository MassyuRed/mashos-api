# -*- coding: utf-8 -*-
from __future__ import annotations

"""P3-8 Regression confirmation for EmlisAI Product Read Feel baseline.

P3-8 does not repair runtime output.  It freezes the regression boundary that
must stay green before the P3-7 first repair design can move into a runtime
change.  The output is body-free: safe ids, command groups, suite results,
contract flags, and next-step decisions only.
"""

from collections.abc import Iterable, Mapping, Sequence
import json
from typing import Any, Final

from emlis_ai_product_quality_contract_freeze import (
    assert_emlis_ai_product_quality_contract_freeze_meta_only,
)
from emlis_ai_product_readfeel_p3_first_repair_design import (
    PRODUCT_READFEEL_P3_FIRST_REPAIR_DESIGN_VERSION_20260609,
    assert_product_readfeel_p3_first_repair_design_meta_only_20260609,
)
from emlis_ai_product_readfeel_rubric import assert_product_readfeel_rubric_meta_only

PRODUCT_READFEEL_P3_REGRESSION_VERSION_20260609: Final = (
    "cocolon.emlis.product_readfeel.p3.regression.20260609.v1"
)
PRODUCT_READFEEL_P3_REGRESSION_SUITE_VERSION_20260609: Final = (
    "cocolon.emlis.product_readfeel.p3.regression_suite.20260609.v1"
)
PRODUCT_READFEEL_P3_REGRESSION_RESULT_VERSION_20260609: Final = (
    "cocolon.emlis.product_readfeel.p3.regression_result.20260609.v1"
)
PRODUCT_READFEEL_P3_REGRESSION_SUMMARY_VERSION_20260609: Final = (
    "cocolon.emlis.product_readfeel.p3.regression_summary.20260609.v1"
)
PRODUCT_READFEEL_P3_REGRESSION_STEP_20260609: Final = "P3-8_Regression"
PRODUCT_READFEEL_P3_REGRESSION_SOURCE_20260609: Final = (
    "Cocolon_EmlisAI_P3_ProductReadFeel_Regression_20260609"
)
PRODUCT_READFEEL_P3_REGRESSION_PROFILE_20260609: Final = (
    "local_product_readfeel_p3_regression"
)

STATUS_PASSED: Final = "passed"
STATUS_FAILED: Final = "failed"
STATUS_TIMEOUT: Final = "timeout"
STATUS_NOT_RUN: Final = "not_run"
STATUS_SKIPPED: Final = "skipped"
STATUS_EXPECTED_YELLOW_TIMEOUT: Final = "expected_yellow_timeout"

DECISION_READY_FOR_FIRST_REPAIR: Final = "regression_green_ready_for_first_repair_implementation"
DECISION_YELLOW_TIMEOUT: Final = "regression_yellow_local_timeout_requires_split_confirmation"
DECISION_BLOCKED_REQUIRED_FAILURE: Final = "regression_blocked_by_required_failure"
DECISION_BLOCKED_NOT_EXECUTED: Final = "regression_blocked_until_required_suites_execute"
DECISION_BLOCKED_P2_RED: Final = "regression_blocked_by_p2_red_before_p3_repair"
DECISION_BLOCKED_P1_DISPLAY: Final = "regression_blocked_by_p1_display_repair_before_p3_repair"
DECISION_NO_RUNTIME_TARGET: Final = "regression_green_but_no_p3_runtime_repair_target"

FORBIDDEN_BODY_KEYS_20260609: Final[frozenset[str]] = frozenset(
    {
        "raw_input",
        "rawInput",
        "raw_text",
        "rawText",
        "source_text",
        "sourceText",
        "input",
        "input_text",
        "inputText",
        "user_input",
        "userInput",
        "current_input",
        "currentInput",
        "history_context",
        "historyContext",
        "history_records",
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
        "reply_text",
        "replyText",
        "surface_text",
        "surfaceText",
        "display_text",
        "displayText",
        "reviewer_note",
        "reviewer_notes",
        "review_notes",
        "free_text_note",
        "stdout",
        "stderr",
        "raw_test_output",
        "test_output",
        "traceback_body",
        "body",
        "text",
    }
)
FORBIDDEN_TRUE_FLAGS_20260609: Final[frozenset[str]] = frozenset(
    {
        "api_route_changed",
        "request_key_changed",
        "response_shape_changed",
        "public_response_key_added",
        "public_response_key_change",
        "db_physical_name_changed",
        "rn_visible_contract_changed",
        "rn_visible_title_changed",
        "display_gate_relaxed",
        "grounding_gate_relaxed",
        "reader_gate_relaxed",
        "template_gate_relaxed",
        "gate_relaxed",
        "raw_input_included",
        "raw_text_included",
        "input_text_included",
        "comment_text_included",
        "comment_text_body_included",
        "candidate_body_included",
        "surface_body_included",
        "raw_test_output_included",
        "product_gate_ready",
        "product_gate_reached",
        "product_gate_public_release_applied",
        "public_release_applied",
        "product_quality_released",
        "machine_metrics_used_for_read_feeling",
        "read_feeling_auto_filled_from_machine_metrics",
        "read_feeling_auto_estimation_allowed",
        "exact_comment_text_locked",
        "exact_comment_text_required",
        "case_specific_runtime_branch",
        "case_specific_runtime_condition_allowed",
        "runtime_branching_uses_fixture_strings",
        "fixture_text_used_for_runtime_branching",
        "fixed_sentence_template_added",
        "fixed_sentence_template_used",
        "input_specific_template_added",
        "runtime_repair_applied",
        "implementation_change_applied",
        "external_ai_used",
        "local_llm_used",
    }
)

BASELINE_REGRESSION_REQUIRED_SUITE_IDS_20260609: Final[tuple[str, ...]] = (
    "rn_contract",
    "backend_contract_display_split",
    "product_readfeel_existing",
    "user_label_connection_existing",
    "public_recovery_limited_grounding_source_unavailable",
    "p2_p3_guard_subset",
    "p3_added_chain",
    "py_compile_p3_added_files",
)
OPTIONAL_REGRESSION_SUITE_IDS_20260609: Final[tuple[str, ...]] = (
    "p3_grouped_chain_timeout_probe",
    "full_backend_suite_manual",
    "real_device_submit_manual",
)

REGRESSION_SUITES_20260609: Final[tuple[dict[str, Any], ...]] = (
    {
        "schema_version": PRODUCT_READFEEL_P3_REGRESSION_SUITE_VERSION_20260609,
        "suite_id": "rn_contract",
        "suite_profile": "RN display contract",
        "scope": "Cocolon RN production visible boundary",
        "required_for_p3_8": True,
        "local_executable": True,
        "allow_yellow_timeout": False,
        "expected_signal": "36 passed; RN still displays only passed + non-empty comment_text as Emlis observation",
        "command": "cd Cocolon && npm run test:rn-screens --silent",
        "test_paths": ["Cocolon/tests/rn-screen-contracts.test.js"],
        "guards": [
            "rn_visible_contract_unchanged",
            "observation_status_passed_and_comment_text_non_empty_contract",
        ],
    },
    {
        "schema_version": PRODUCT_READFEEL_P3_REGRESSION_SUITE_VERSION_20260609,
        "suite_id": "backend_contract_display_split",
        "suite_profile": "backend display contract split",
        "scope": "/emotion/submit public input_feedback arrival contract",
        "required_for_p3_8": True,
        "local_executable": True,
        "allow_yellow_timeout": False,
        "expected_signal": "contract/display/e2e split suites pass without changing public response keys",
        "command": "PYTHONPATH=services/ai_inference pytest -q tests/contract/test_emlis_ai_contracts.py tests/test_emlis_ai_display_contract.py tests/test_emotion_submit_two_stage_reception_e2e.py",
        "test_paths": [
            "tests/contract/test_emlis_ai_contracts.py",
            "tests/test_emlis_ai_display_contract.py",
            "tests/test_emotion_submit_two_stage_reception_e2e.py",
        ],
        "guards": ["public_response_shape_unchanged", "comment_text_public_arrival_contract"],
    },
    {
        "schema_version": PRODUCT_READFEEL_P3_REGRESSION_SUITE_VERSION_20260609,
        "suite_id": "product_readfeel_existing",
        "suite_profile": "existing Product Read Feel measurement",
        "scope": "rubric / scorecard / inventory / surface guard",
        "required_for_p3_8": True,
        "local_executable": True,
        "allow_yellow_timeout": False,
        "expected_signal": "existing Product Read Feel measuring instruments remain green",
        "command": "PYTHONPATH=services/ai_inference pytest -q tests/test_emlis_ai_product_readfeel_current_output_inventory_phase1.py tests/test_emlis_ai_product_readfeel_fixture_families.py tests/test_emlis_ai_product_readfeel_rubric.py tests/test_emlis_ai_product_readfeel_scorecard.py tests/test_emlis_ai_product_readfeel_surface_v1_phase5.py tests/test_emlis_ai_mirror_only_surface_detector.py tests/test_emlis_ai_product_surface_question_dominance_guard_p6.py",
        "test_paths": [
            "tests/test_emlis_ai_product_readfeel_current_output_inventory_phase1.py",
            "tests/test_emlis_ai_product_readfeel_fixture_families.py",
            "tests/test_emlis_ai_product_readfeel_rubric.py",
            "tests/test_emlis_ai_product_readfeel_scorecard.py",
            "tests/test_emlis_ai_product_readfeel_surface_v1_phase5.py",
            "tests/test_emlis_ai_mirror_only_surface_detector.py",
            "tests/test_emlis_ai_product_surface_question_dominance_guard_p6.py",
        ],
        "guards": ["meta_only_scorecard", "mirror_only_guard", "question_dominance_guard"],
    },
    {
        "schema_version": PRODUCT_READFEEL_P3_REGRESSION_SUITE_VERSION_20260609,
        "suite_id": "user_label_connection_existing",
        "suite_profile": "User Label Connection regression",
        "scope": "P5 not accidentally strengthened while P3 current-input readfeel is evaluated",
        "required_for_p3_8": True,
        "local_executable": True,
        "allow_yellow_timeout": False,
        "expected_signal": "User Label Connection boundary remains green; no history line masks current-input gap",
        "command": "PYTHONPATH=services/ai_inference pytest -q tests/test_emlis_ai_user_label_connection_material.py tests/test_emlis_ai_user_label_connection_candidate.py tests/test_emlis_ai_user_label_connection_gate.py tests/test_emlis_ai_user_label_connection_surface.py tests/test_emlis_ai_user_label_connection_public_boundary.py tests/test_emlis_ai_user_label_connection_e2e_contract.py",
        "test_paths": [
            "tests/test_emlis_ai_user_label_connection_material.py",
            "tests/test_emlis_ai_user_label_connection_candidate.py",
            "tests/test_emlis_ai_user_label_connection_gate.py",
            "tests/test_emlis_ai_user_label_connection_surface.py",
            "tests/test_emlis_ai_user_label_connection_public_boundary.py",
            "tests/test_emlis_ai_user_label_connection_e2e_contract.py",
        ],
        "guards": ["free_plus_premium_boundary", "no_raw_history_text_meta", "p5_not_p3_mask"],
    },
    {
        "schema_version": PRODUCT_READFEEL_P3_REGRESSION_SUITE_VERSION_20260609,
        "suite_id": "public_recovery_limited_grounding_source_unavailable",
        "suite_profile": "public recovery and limited grounding",
        "scope": "normal observation recovery / source unavailable / limited grounding",
        "required_for_p3_8": True,
        "local_executable": True,
        "allow_yellow_timeout": False,
        "expected_signal": "safe recovery still reaches public boundary without read-it-fake normal rebuild",
        "command": "PYTHONPATH=services/ai_inference pytest -q tests/test_emlis_ai_public_observation_recovery_acceptance_p0.py tests/test_emlis_ai_public_surface_requirement_p1.py tests/test_emlis_ai_product_surface_validation_p3.py tests/test_emlis_ai_limited_grounding_reception_surface_p4.py tests/test_emlis_ai_d_source_unavailable_normal_observation_recovery.py tests/test_emlis_ai_complete_initial_surface_recomposition_p5.py tests/test_emlis_ai_complete_initial_surface_recomposition_existing_gate_chain_p8.py",
        "test_paths": [
            "tests/test_emlis_ai_public_observation_recovery_acceptance_p0.py",
            "tests/test_emlis_ai_public_surface_requirement_p1.py",
            "tests/test_emlis_ai_product_surface_validation_p3.py",
            "tests/test_emlis_ai_limited_grounding_reception_surface_p4.py",
            "tests/test_emlis_ai_d_source_unavailable_normal_observation_recovery.py",
            "tests/test_emlis_ai_complete_initial_surface_recomposition_p5.py",
            "tests/test_emlis_ai_complete_initial_surface_recomposition_existing_gate_chain_p8.py",
        ],
        "guards": ["source_unavailable_not_normal_rebuild_fake", "limited_grounding_not_question_only"],
    },
    {
        "schema_version": PRODUCT_READFEEL_P3_REGRESSION_SUITE_VERSION_20260609,
        "suite_id": "p2_p3_guard_subset",
        "suite_profile": "P2/P3 guard subset",
        "scope": "surface safety / quality gate / visible acceptance / P3 measurement guards",
        "required_for_p3_8": True,
        "local_executable": True,
        "allow_yellow_timeout": False,
        "expected_signal": "P2/P3 guards remain green before any runtime repair",
        "command": "PYTHONPATH=services/ai_inference pytest -q tests/test_emlis_ai_malformed_nominalization_phrase_unit_guard.py tests/test_emlis_ai_phrase_grammar_guard.py tests/test_emlis_ai_quality_gate_pre_return.py tests/test_emlis_ai_visible_surface_acceptance_gate.py tests/test_emlis_ai_visible_surface_acceptance_inventory_step0.py tests/test_emlis_ai_mirror_only_surface_detector.py tests/test_emlis_ai_product_readfeel_current_output_inventory_phase1.py tests/test_emlis_ai_product_readfeel_fixture_families.py tests/test_emlis_ai_product_readfeel_surface_v1_phase5.py tests/test_emlis_ai_product_quality_blind_qa_integration.py tests/test_emlis_ai_product_surface_question_dominance_guard_p6.py",
        "test_paths": [
            "tests/test_emlis_ai_malformed_nominalization_phrase_unit_guard.py",
            "tests/test_emlis_ai_phrase_grammar_guard.py",
            "tests/test_emlis_ai_quality_gate_pre_return.py",
            "tests/test_emlis_ai_visible_surface_acceptance_gate.py",
            "tests/test_emlis_ai_visible_surface_acceptance_inventory_step0.py",
            "tests/test_emlis_ai_mirror_only_surface_detector.py",
            "tests/test_emlis_ai_product_readfeel_current_output_inventory_phase1.py",
            "tests/test_emlis_ai_product_readfeel_fixture_families.py",
            "tests/test_emlis_ai_product_readfeel_surface_v1_phase5.py",
            "tests/test_emlis_ai_product_quality_blind_qa_integration.py",
            "tests/test_emlis_ai_product_surface_question_dominance_guard_p6.py",
        ],
        "guards": ["p2_red_not_silenced", "visible_surface_acceptance_strict"],
    },
    {
        "schema_version": PRODUCT_READFEEL_P3_REGRESSION_SUITE_VERSION_20260609,
        "suite_id": "p3_added_chain",
        "suite_profile": "P3-0 to P3-8 added chain",
        "scope": "new P3 baseline / capture / inventory / split / QA / ledger / design / regression tests",
        "required_for_p3_8": True,
        "local_executable": True,
        "allow_yellow_timeout": False,
        "expected_signal": "all added P3 layer tests pass in split execution",
        "command": "PYTHONPATH=services/ai_inference pytest -q tests/test_emlis_ai_product_readfeel_p3_contract_freeze_20260609.py tests/test_emlis_ai_product_readfeel_baseline_case_matrix_20260609.py tests/test_emlis_ai_product_readfeel_p3_local_output_capture_20260609.py tests/test_emlis_ai_product_readfeel_p3_inventory_connection_20260609.py tests/test_emlis_ai_product_readfeel_p3_verdict_split_20260609.py tests/test_emlis_ai_product_readfeel_p3_blind_qa_ratings_review_20260609.py tests/test_emlis_ai_product_readfeel_p3_repair_priority_ledger_20260609.py tests/test_emlis_ai_product_readfeel_p3_first_repair_design_20260609.py tests/test_emlis_ai_product_readfeel_p3_regression_20260609.py",
        "test_paths": [
            "tests/test_emlis_ai_product_readfeel_p3_contract_freeze_20260609.py",
            "tests/test_emlis_ai_product_readfeel_baseline_case_matrix_20260609.py",
            "tests/test_emlis_ai_product_readfeel_p3_local_output_capture_20260609.py",
            "tests/test_emlis_ai_product_readfeel_p3_inventory_connection_20260609.py",
            "tests/test_emlis_ai_product_readfeel_p3_verdict_split_20260609.py",
            "tests/test_emlis_ai_product_readfeel_p3_blind_qa_ratings_review_20260609.py",
            "tests/test_emlis_ai_product_readfeel_p3_repair_priority_ledger_20260609.py",
            "tests/test_emlis_ai_product_readfeel_p3_first_repair_design_20260609.py",
            "tests/test_emlis_ai_product_readfeel_p3_regression_20260609.py",
        ],
        "guards": ["p3_chain_meta_only", "p3_8_plan_and_result_shape"],
    },
    {
        "schema_version": PRODUCT_READFEEL_P3_REGRESSION_SUITE_VERSION_20260609,
        "suite_id": "py_compile_p3_added_files",
        "suite_profile": "P3 added file syntax",
        "scope": "syntax/import stability for newly added P3 modules and fixtures",
        "required_for_p3_8": True,
        "local_executable": True,
        "allow_yellow_timeout": False,
        "expected_signal": "python files compile without syntax errors",
        "command": "python -m py_compile services/ai_inference/emlis_ai_product_readfeel_p3_verdict_split.py services/ai_inference/emlis_ai_product_readfeel_p3_blind_qa_ratings_review.py services/ai_inference/emlis_ai_product_readfeel_p3_repair_priority_ledger.py services/ai_inference/emlis_ai_product_readfeel_p3_first_repair_design.py services/ai_inference/emlis_ai_product_readfeel_p3_regression.py tests/fixtures/emlis_ai_product_readfeel_p3_regression_20260609.py tests/test_emlis_ai_product_readfeel_p3_regression_20260609.py",
        "test_paths": [
            "services/ai_inference/emlis_ai_product_readfeel_p3_regression.py",
            "tests/fixtures/emlis_ai_product_readfeel_p3_regression_20260609.py",
            "tests/test_emlis_ai_product_readfeel_p3_regression_20260609.py",
        ],
        "guards": ["syntax_stability"],
    },
    {
        "schema_version": PRODUCT_READFEEL_P3_REGRESSION_SUITE_VERSION_20260609,
        "suite_id": "p3_grouped_chain_timeout_probe",
        "suite_profile": "P3 grouped timeout probe",
        "scope": "known grouped command timeout observation; split green is source of truth for P3-8",
        "required_for_p3_8": False,
        "local_executable": True,
        "allow_yellow_timeout": True,
        "expected_signal": "optional grouped timeout is YELLOW only when all required split suites pass",
        "command": "PYTHONPATH=services/ai_inference pytest -q <P3-0_to_P3-8_added_chain_grouped>",
        "test_paths": ["P3 added chain grouped command"],
        "guards": ["grouped_timeout_not_assertion_failure"],
    },
    {
        "schema_version": PRODUCT_READFEEL_P3_REGRESSION_SUITE_VERSION_20260609,
        "suite_id": "full_backend_suite_manual",
        "suite_profile": "full backend suite manual",
        "scope": "all backend tests outside P3 focused subset",
        "required_for_p3_8": False,
        "local_executable": False,
        "allow_yellow_timeout": True,
        "expected_signal": "manual/full-suite evidence before later release gate, not required for P3-8 diff",
        "command": "PYTHONPATH=services/ai_inference pytest -q",
        "test_paths": ["all backend tests"],
        "guards": ["full_suite_not_required_for_p3_8_diff"],
    },
    {
        "schema_version": PRODUCT_READFEEL_P3_REGRESSION_SUITE_VERSION_20260609,
        "suite_id": "real_device_submit_manual",
        "suite_profile": "real device submit manual",
        "scope": "actual device /emotion/submit display arrival",
        "required_for_p3_8": False,
        "local_executable": False,
        "allow_yellow_timeout": False,
        "expected_signal": "manual evidence before release, not required for local P3-8 regression boundary",
        "command": "manual real device submit check",
        "test_paths": ["real device manual check"],
        "guards": ["manual_release_evidence_not_faked"],
    },
)


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _safe_identifier(value: Any, *, default: str = "", max_length: int = 96) -> str:
    text = _clean(value)
    if not text:
        text = default
    allowed = []
    for ch in text[:max_length]:
        allowed.append(ch if ch.isalnum() or ch in {"-", "_", ".", ":"} else "-")
    return "".join(allowed).strip("-") or default


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if isinstance(value, bool):
            return int(value)
        return int(value)
    except (TypeError, ValueError):
        return default


def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
    if values is None:
        return []
    if isinstance(values, (str, bytes)):
        iterable: Iterable[Any] = [values]
    else:
        try:
            iterable = list(values)  # type: ignore[arg-type]
        except TypeError:
            iterable = [values]
    seen: set[str] = set()
    out: list[str] = []
    for value in iterable:
        text = _clean(value)
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out


def _contains_forbidden_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in FORBIDDEN_BODY_KEYS_20260609:
                return True
            if _contains_forbidden_key(child):
                return True
    elif isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_key(item) for item in value)
    return False


def _forbidden_true_flag_path(value: Any, *, path: str = "payload") -> str | None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            current_path = f"{path}.{key_text}"
            if key_text in FORBIDDEN_TRUE_FLAGS_20260609 and child is True:
                return current_path
            nested = _forbidden_true_flag_path(child, path=current_path)
            if nested:
                return nested
    elif isinstance(value, (list, tuple, set)):
        for index, child in enumerate(value):
            nested = _forbidden_true_flag_path(child, path=f"{path}[{index}]")
            if nested:
                return nested
    return None


def assert_product_readfeel_p3_regression_meta_only_20260609(
    payload: Mapping[str, Any],
    *,
    source: str = "p3_8_regression",
) -> None:
    """Reject body-bearing or contract-breaking P3-8 regression payloads."""
    if not isinstance(payload, Mapping):
        raise TypeError(f"{source} must be a mapping")
    if _contains_forbidden_key(payload):
        raise ValueError(f"{source} must not contain local review, input, output, or raw test body keys")
    flag_path = _forbidden_true_flag_path(payload)
    if flag_path:
        raise ValueError(f"{source} contains forbidden true flag: {flag_path}")
    assert_product_readfeel_rubric_meta_only(payload, source=f"{source}.rubric")
    assert_emlis_ai_product_quality_contract_freeze_meta_only(payload, source=f"{source}.contract_freeze")


def _suite_by_id() -> dict[str, dict[str, Any]]:
    return {str(suite["suite_id"]): dict(suite) for suite in REGRESSION_SUITES_20260609}


def _design_summary(first_repair_design: Mapping[str, Any] | None) -> dict[str, Any]:
    if isinstance(first_repair_design, Mapping):
        assert_product_readfeel_p3_first_repair_design_meta_only_20260609(first_repair_design)
        if first_repair_design.get("schema_version") == PRODUCT_READFEEL_P3_FIRST_REPAIR_DESIGN_VERSION_20260609:
            return dict(first_repair_design.get("summary") or first_repair_design.get("public_summary") or {})
        return dict(first_repair_design.get("summary") or first_repair_design.get("public_summary") or first_repair_design)
    return {}


def _design_items(first_repair_design: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(first_repair_design, Mapping):
        return []
    raw_items = first_repair_design.get("design_items") or first_repair_design.get("first_repair_design_items") or []
    items: list[dict[str, Any]] = []
    if isinstance(raw_items, Sequence) and not isinstance(raw_items, (str, bytes)):
        for item in raw_items:
            if isinstance(item, Mapping):
                assert_product_readfeel_p3_first_repair_design_meta_only_20260609(item)
                items.append(dict(item))
    return items


def _normalize_suite(suite: Mapping[str, Any]) -> dict[str, Any]:
    normalized = {
        "schema_version": PRODUCT_READFEEL_P3_REGRESSION_SUITE_VERSION_20260609,
        "version": PRODUCT_READFEEL_P3_REGRESSION_SUITE_VERSION_20260609,
        "source": PRODUCT_READFEEL_P3_REGRESSION_SOURCE_20260609,
        "source_step": PRODUCT_READFEEL_P3_REGRESSION_STEP_20260609,
        "suite_id": _safe_identifier(suite.get("suite_id"), default="unknown_suite"),
        "suite_profile": _clean(suite.get("suite_profile")),
        "scope": _clean(suite.get("scope")),
        "required_for_p3_8": suite.get("required_for_p3_8") is True,
        "local_executable": suite.get("local_executable") is True,
        "allow_yellow_timeout": suite.get("allow_yellow_timeout") is True,
        "expected_signal": _clean(suite.get("expected_signal")),
        "command": _clean(suite.get("command")),
        "test_paths": _dedupe(suite.get("test_paths")),
        "guards": _dedupe(suite.get("guards")),
        "comment_text_body_included": False,
        "raw_input_included": False,
        "candidate_body_included": False,
        "raw_test_output_included": False,
        "gate_relaxed": False,
        "product_gate_ready": False,
        "public_release_applied": False,
    }
    assert_product_readfeel_p3_regression_meta_only_20260609(normalized, source="p3_8.suite")
    return normalized


def _plan_summary(
    *,
    suites: Sequence[Mapping[str, Any]],
    first_repair_design: Mapping[str, Any] | None,
    run_id: str,
) -> dict[str, Any]:
    source_summary = _design_summary(first_repair_design)
    items = _design_items(first_repair_design)
    required = [suite for suite in suites if suite.get("required_for_p3_8") is True]
    optional = [suite for suite in suites if suite.get("required_for_p3_8") is not True]
    selected_runtime_items = [item for item in items if item.get("selected_for_first_runtime_repair") is True]
    summary = {
        "schema_version": PRODUCT_READFEEL_P3_REGRESSION_SUMMARY_VERSION_20260609,
        "version": PRODUCT_READFEEL_P3_REGRESSION_SUMMARY_VERSION_20260609,
        "source": PRODUCT_READFEEL_P3_REGRESSION_SOURCE_20260609,
        "source_step": PRODUCT_READFEEL_P3_REGRESSION_STEP_20260609,
        "run_id": run_id,
        "run_profile": PRODUCT_READFEEL_P3_REGRESSION_PROFILE_20260609,
        "source_p3_7_decision": _clean(source_summary.get("decision")),
        "source_p3_7_design_item_count": _to_int(source_summary.get("design_item_count"), len(items)),
        "source_p3_7_runtime_repair_design_count": _to_int(
            source_summary.get("runtime_repair_design_count"), len(selected_runtime_items)
        ),
        "source_p3_7_first_runtime_repair_blocker_ids": _dedupe(
            source_summary.get("first_runtime_repair_blocker_ids")
        ) or _dedupe(item.get("source_blocker_id") for item in selected_runtime_items),
        "source_p3_7_families": _dedupe(source_summary.get("families")) or _dedupe(
            family for item in items for family in item.get("families") or []
        ),
        "suite_count": len(suites),
        "required_suite_count": len(required),
        "optional_suite_count": len(optional),
        "required_suite_ids": _dedupe(suite.get("suite_id") for suite in required),
        "optional_suite_ids": _dedupe(suite.get("suite_id") for suite in optional),
        "p2_red_present": bool(source_summary.get("p2_red_present")),
        "p2_red_blocks_p3_repair": bool(source_summary.get("p2_red_blocks_p3_repair")),
        "p1_display_repair_present": bool(source_summary.get("p1_display_repair_present")),
        "p3_runtime_repair_can_start_from_design": bool(source_summary.get("p3_runtime_repair_can_start")),
        "p3_0_contract_freeze_respected": True,
        "p3_1_baseline_case_matrix_used": bool(source_summary.get("p3_1_baseline_case_matrix_used")),
        "p3_2_local_output_capture_used": bool(source_summary.get("p3_2_local_output_capture_used")),
        "p3_3_inventory_connection_used": bool(source_summary.get("p3_3_inventory_connection_used")),
        "p3_4_verdict_split_used": bool(source_summary.get("p3_4_verdict_split_used")),
        "p3_5_blind_qa_ratings_only_review_used": bool(source_summary.get("p3_5_blind_qa_ratings_only_review_used")),
        "p3_6_repair_priority_ledger_used": bool(source_summary.get("p3_6_repair_priority_ledger_used")),
        "p3_7_first_repair_design_applied": True if first_repair_design else False,
        "p3_8_regression_plan_created": True,
        "regression_must_precede_runtime_repair": True,
        "body_free_case_references_only": True,
        "local_review_packet_retained": False,
        "local_review_packet_body_retained": False,
        "comment_text_body_included": False,
        "comment_text_included": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "raw_test_output_included": False,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "read_feeling_auto_estimation_allowed": False,
        "exact_comment_text_required": False,
        "case_specific_runtime_branch": False,
        "runtime_branching_uses_fixture_strings": False,
        "fixture_text_used_for_runtime_branching": False,
        "fixed_sentence_template_added": False,
        "input_specific_template_added": False,
        "runtime_repair_applied": False,
        "implementation_change_applied": False,
        "public_response_key_added": False,
        "public_response_key_change": False,
        "response_shape_changed": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "gate_relaxed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "template_gate_relaxed": False,
        "product_gate_ready": False,
        "product_gate_reached": False,
        "public_release_applied": False,
        "product_quality_released": False,
    }
    assert_product_readfeel_p3_regression_meta_only_20260609(summary, source="p3_8.plan_summary")
    return summary


def build_product_readfeel_p3_regression_plan_20260609(
    *,
    first_repair_design: Mapping[str, Any] | None = None,
    run_id: str | None = None,
    include_optional_suites: bool = True,
) -> dict[str, Any]:
    run_id_value = _safe_identifier(
        run_id or (_design_summary(first_repair_design).get("run_id") if isinstance(first_repair_design, Mapping) else None),
        default="p3_8_regression",
    )
    suites = [
        _normalize_suite(suite)
        for suite in REGRESSION_SUITES_20260609
        if include_optional_suites or suite.get("required_for_p3_8") is True
    ]
    summary = _plan_summary(suites=suites, first_repair_design=first_repair_design, run_id=run_id_value)
    payload = {
        "schema_version": PRODUCT_READFEEL_P3_REGRESSION_VERSION_20260609,
        "version": PRODUCT_READFEEL_P3_REGRESSION_VERSION_20260609,
        "source": PRODUCT_READFEEL_P3_REGRESSION_SOURCE_20260609,
        "source_step": PRODUCT_READFEEL_P3_REGRESSION_STEP_20260609,
        "run_id": run_id_value,
        "run_profile": PRODUCT_READFEEL_P3_REGRESSION_PROFILE_20260609,
        "summary": summary,
        "regression_suites": suites,
        "required_suite_ids": list(BASELINE_REGRESSION_REQUIRED_SUITE_IDS_20260609),
        "optional_suite_ids": list(OPTIONAL_REGRESSION_SUITE_IDS_20260609),
        "p3_8_regression_plan_created": True,
        "p3_8_regression_results_attached": False,
        "body_free_case_references_only": True,
        "local_review_packet_retained": False,
        "local_review_packet_body_retained": False,
        "comment_text_body_included": False,
        "comment_text_included": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "raw_test_output_included": False,
        "runtime_repair_applied": False,
        "implementation_change_applied": False,
        "gate_relaxed": False,
        "product_gate_ready": False,
        "public_release_applied": False,
        "public_summary": {},
    }
    payload["public_summary"] = build_product_readfeel_p3_regression_public_summary_20260609(payload)
    assert_product_readfeel_p3_regression_meta_only_20260609(payload)
    return payload


def _normalize_result_row(row: Mapping[str, Any], *, plan_suite_ids: set[str]) -> dict[str, Any]:
    suite_id = _safe_identifier(row.get("suite_id"), default="unknown_suite")
    if suite_id not in plan_suite_ids:
        raise ValueError(f"unknown P3-8 regression suite_id: {suite_id}")
    status = _clean(row.get("status")).lower() or STATUS_NOT_RUN
    if status not in {STATUS_PASSED, STATUS_FAILED, STATUS_TIMEOUT, STATUS_NOT_RUN, STATUS_SKIPPED, STATUS_EXPECTED_YELLOW_TIMEOUT}:
        raise ValueError(f"unsupported P3-8 regression status: {status}")
    normalized = {
        "schema_version": PRODUCT_READFEEL_P3_REGRESSION_RESULT_VERSION_20260609,
        "version": PRODUCT_READFEEL_P3_REGRESSION_RESULT_VERSION_20260609,
        "source": PRODUCT_READFEEL_P3_REGRESSION_SOURCE_20260609,
        "source_step": PRODUCT_READFEEL_P3_REGRESSION_STEP_20260609,
        "suite_id": suite_id,
        "status": status,
        "passed_count": _to_int(row.get("passed_count"), 0),
        "failed_count": _to_int(row.get("failed_count"), 0),
        "warning_count": _to_int(row.get("warning_count"), 0),
        "timeout_observed": bool(row.get("timeout_observed")) or status in {STATUS_TIMEOUT, STATUS_EXPECTED_YELLOW_TIMEOUT},
        "failure_codes": _dedupe(row.get("failure_codes")),
        "yellow_codes": _dedupe(row.get("yellow_codes")),
        "split_execution_used": row.get("split_execution_used") is True,
        "raw_test_output_included": False,
        "comment_text_body_included": False,
        "raw_input_included": False,
        "candidate_body_included": False,
        "gate_relaxed": False,
        "product_gate_ready": False,
        "public_release_applied": False,
    }
    assert_product_readfeel_p3_regression_meta_only_20260609(normalized, source="p3_8.result_row")
    return normalized


def _result_summary(
    *,
    plan: Mapping[str, Any],
    result_rows: Sequence[Mapping[str, Any]],
    run_id: str,
) -> dict[str, Any]:
    suites = [dict(suite) for suite in plan.get("regression_suites") or [] if isinstance(suite, Mapping)]
    suite_by_id = {str(suite.get("suite_id")): suite for suite in suites}
    required_ids = [str(suite.get("suite_id")) for suite in suites if suite.get("required_for_p3_8") is True]
    optional_ids = [str(suite.get("suite_id")) for suite in suites if suite.get("required_for_p3_8") is not True]
    rows_by_id = {str(row.get("suite_id")): dict(row) for row in result_rows}

    missing_required = [suite_id for suite_id in required_ids if suite_id not in rows_by_id]
    required_failed = [
        suite_id
        for suite_id in required_ids
        if rows_by_id.get(suite_id, {}).get("status") == STATUS_FAILED or _to_int(rows_by_id.get(suite_id, {}).get("failed_count"), 0) > 0
    ]
    required_timeout = [
        suite_id
        for suite_id in required_ids
        if rows_by_id.get(suite_id, {}).get("status") in {STATUS_TIMEOUT, STATUS_EXPECTED_YELLOW_TIMEOUT}
    ]
    required_not_green = [
        suite_id
        for suite_id in required_ids
        if suite_id not in rows_by_id
        or rows_by_id.get(suite_id, {}).get("status") not in {STATUS_PASSED}
        or _to_int(rows_by_id.get(suite_id, {}).get("failed_count"), 0) > 0
    ]
    optional_yellow_timeout = [
        suite_id
        for suite_id in optional_ids
        if rows_by_id.get(suite_id, {}).get("status") in {STATUS_TIMEOUT, STATUS_EXPECTED_YELLOW_TIMEOUT}
        and bool(suite_by_id.get(suite_id, {}).get("allow_yellow_timeout"))
    ]
    optional_failed = [
        suite_id
        for suite_id in optional_ids
        if rows_by_id.get(suite_id, {}).get("status") == STATUS_FAILED
        or _to_int(rows_by_id.get(suite_id, {}).get("failed_count"), 0) > 0
    ]
    p2_red = bool((plan.get("summary") or {}).get("p2_red_present") or (plan.get("summary") or {}).get("p2_red_blocks_p3_repair"))
    p1_display = bool((plan.get("summary") or {}).get("p1_display_repair_present"))
    runtime_design_count = _to_int((plan.get("summary") or {}).get("source_p3_7_runtime_repair_design_count"), 0)

    if p2_red:
        decision = DECISION_BLOCKED_P2_RED
        can_start = False
    elif p1_display:
        decision = DECISION_BLOCKED_P1_DISPLAY
        can_start = False
    elif required_failed or required_timeout:
        decision = DECISION_BLOCKED_REQUIRED_FAILURE
        can_start = False
    elif missing_required or required_not_green:
        decision = DECISION_BLOCKED_NOT_EXECUTED
        can_start = False
    elif runtime_design_count <= 0:
        decision = DECISION_NO_RUNTIME_TARGET
        can_start = False
    elif optional_yellow_timeout or optional_failed:
        decision = DECISION_YELLOW_TIMEOUT if optional_yellow_timeout and not optional_failed else DECISION_BLOCKED_REQUIRED_FAILURE
        can_start = not optional_failed
    else:
        decision = DECISION_READY_FOR_FIRST_REPAIR
        can_start = True

    passed_count = sum(1 for row in result_rows if row.get("status") == STATUS_PASSED)
    failed_count = len(required_failed) + len(optional_failed)
    timeout_count = sum(1 for row in result_rows if row.get("status") in {STATUS_TIMEOUT, STATUS_EXPECTED_YELLOW_TIMEOUT})
    summary = {
        "schema_version": PRODUCT_READFEEL_P3_REGRESSION_SUMMARY_VERSION_20260609,
        "version": PRODUCT_READFEEL_P3_REGRESSION_SUMMARY_VERSION_20260609,
        "source": PRODUCT_READFEEL_P3_REGRESSION_SOURCE_20260609,
        "source_step": PRODUCT_READFEEL_P3_REGRESSION_STEP_20260609,
        "run_id": run_id,
        "run_profile": PRODUCT_READFEEL_P3_REGRESSION_PROFILE_20260609,
        "suite_count": len(suites),
        "result_row_count": len(result_rows),
        "required_suite_count": len(required_ids),
        "required_passed_count": sum(1 for suite_id in required_ids if rows_by_id.get(suite_id, {}).get("status") == STATUS_PASSED),
        "optional_suite_count": len(optional_ids),
        "passed_result_count": passed_count,
        "failed_result_count": failed_count,
        "timeout_result_count": timeout_count,
        "missing_required_suite_ids": missing_required,
        "required_failed_suite_ids": required_failed,
        "required_timeout_suite_ids": required_timeout,
        "optional_yellow_timeout_suite_ids": optional_yellow_timeout,
        "optional_failed_suite_ids": optional_failed,
        "required_regression_green": not missing_required and not required_not_green,
        "optional_timeout_yellow_present": bool(optional_yellow_timeout),
        "p2_red_present": p2_red,
        "p2_red_blocks_p3_repair": p2_red,
        "p1_display_repair_present": p1_display,
        "source_p3_7_runtime_repair_design_count": runtime_design_count,
        "p3_runtime_repair_can_start_after_regression": can_start,
        "decision": decision,
        "p3_8_regression_plan_created": True,
        "p3_8_regression_results_attached": True,
        "p3_8_existing_contracts_checked": True,
        "p3_added_tests_checked": True,
        "body_free_case_references_only": True,
        "local_review_packet_retained": False,
        "local_review_packet_body_retained": False,
        "comment_text_body_included": False,
        "comment_text_included": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "raw_test_output_included": False,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "read_feeling_auto_estimation_allowed": False,
        "exact_comment_text_required": False,
        "case_specific_runtime_branch": False,
        "runtime_branching_uses_fixture_strings": False,
        "fixture_text_used_for_runtime_branching": False,
        "fixed_sentence_template_added": False,
        "input_specific_template_added": False,
        "runtime_repair_applied": False,
        "implementation_change_applied": False,
        "public_response_key_added": False,
        "public_response_key_change": False,
        "response_shape_changed": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "gate_relaxed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "template_gate_relaxed": False,
        "product_gate_ready": False,
        "product_gate_reached": False,
        "public_release_applied": False,
        "product_quality_released": False,
    }
    assert_product_readfeel_p3_regression_meta_only_20260609(summary, source="p3_8.result_summary")
    return summary


def build_product_readfeel_p3_regression_result_20260609(
    *,
    first_repair_design: Mapping[str, Any] | None = None,
    regression_plan: Mapping[str, Any] | None = None,
    command_results: Sequence[Mapping[str, Any]] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    plan = dict(
        regression_plan
        or build_product_readfeel_p3_regression_plan_20260609(
            first_repair_design=first_repair_design,
            run_id=run_id,
            include_optional_suites=True,
        )
    )
    assert_product_readfeel_p3_regression_meta_only_20260609(plan, source="p3_8.plan_for_result")
    run_id_value = _safe_identifier(run_id or plan.get("run_id"), default="p3_8_regression_result")
    suites = [dict(suite) for suite in plan.get("regression_suites") or [] if isinstance(suite, Mapping)]
    plan_suite_ids = {str(suite.get("suite_id")) for suite in suites}
    result_rows = [
        _normalize_result_row(row, plan_suite_ids=plan_suite_ids)
        for row in list(command_results or [])
        if isinstance(row, Mapping)
    ]
    summary = _result_summary(plan=plan, result_rows=result_rows, run_id=run_id_value)
    payload = {
        "schema_version": PRODUCT_READFEEL_P3_REGRESSION_VERSION_20260609,
        "version": PRODUCT_READFEEL_P3_REGRESSION_VERSION_20260609,
        "source": PRODUCT_READFEEL_P3_REGRESSION_SOURCE_20260609,
        "source_step": PRODUCT_READFEEL_P3_REGRESSION_STEP_20260609,
        "run_id": run_id_value,
        "run_profile": PRODUCT_READFEEL_P3_REGRESSION_PROFILE_20260609,
        "summary": summary,
        "regression_suites": suites,
        "regression_result_rows": result_rows,
        "public_summary": {},
        "p3_8_regression_plan_created": True,
        "p3_8_regression_results_attached": True,
        "body_free_case_references_only": True,
        "local_review_packet_retained": False,
        "local_review_packet_body_retained": False,
        "comment_text_body_included": False,
        "comment_text_included": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "raw_test_output_included": False,
        "runtime_repair_applied": False,
        "implementation_change_applied": False,
        "gate_relaxed": False,
        "product_gate_ready": False,
        "public_release_applied": False,
    }
    payload["public_summary"] = build_product_readfeel_p3_regression_public_summary_20260609(payload)
    assert_product_readfeel_p3_regression_meta_only_20260609(payload, source="p3_8.result")
    return payload


def build_product_readfeel_p3_regression_public_summary_20260609(
    regression_or_plan: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload = dict(regression_or_plan or {})
    if not payload:
        payload = build_product_readfeel_p3_regression_plan_20260609()
    summary = dict(payload.get("summary") or {})
    suites = [dict(suite) for suite in payload.get("regression_suites") or [] if isinstance(suite, Mapping)]
    result_rows = [dict(row) for row in payload.get("regression_result_rows") or [] if isinstance(row, Mapping)]
    public_summary = dict(summary)
    public_summary["schema_version"] = PRODUCT_READFEEL_P3_REGRESSION_SUMMARY_VERSION_20260609
    public_summary["version"] = PRODUCT_READFEEL_P3_REGRESSION_SUMMARY_VERSION_20260609
    public_summary["source"] = PRODUCT_READFEEL_P3_REGRESSION_SOURCE_20260609
    public_summary["source_step"] = PRODUCT_READFEEL_P3_REGRESSION_STEP_20260609
    public_summary["regression_suites"] = [
        {
            "suite_id": _clean(suite.get("suite_id")),
            "suite_profile": _clean(suite.get("suite_profile")),
            "required_for_p3_8": suite.get("required_for_p3_8") is True,
            "local_executable": suite.get("local_executable") is True,
            "allow_yellow_timeout": suite.get("allow_yellow_timeout") is True,
            "test_paths": _dedupe(suite.get("test_paths")),
            "guards": _dedupe(suite.get("guards")),
        }
        for suite in suites
    ]
    if result_rows:
        public_summary["regression_result_summary"] = [
            {
                "suite_id": _clean(row.get("suite_id")),
                "status": _clean(row.get("status")),
                "passed_count": _to_int(row.get("passed_count"), 0),
                "failed_count": _to_int(row.get("failed_count"), 0),
                "timeout_observed": row.get("timeout_observed") is True,
                "failure_codes": _dedupe(row.get("failure_codes")),
                "yellow_codes": _dedupe(row.get("yellow_codes")),
            }
            for row in result_rows
        ]
    public_summary["comment_text_body_included"] = False
    public_summary["raw_input_included"] = False
    public_summary["candidate_body_included"] = False
    public_summary["raw_test_output_included"] = False
    public_summary["runtime_repair_applied"] = False
    public_summary["implementation_change_applied"] = False
    public_summary["gate_relaxed"] = False
    public_summary["product_gate_ready"] = False
    public_summary["public_release_applied"] = False
    assert_product_readfeel_p3_regression_meta_only_20260609(public_summary, source="p3_8.public_summary")
    return public_summary


def dump_product_readfeel_p3_regression_public_summary_20260609(
    regression_or_plan: Mapping[str, Any] | None = None,
) -> str:
    summary = build_product_readfeel_p3_regression_public_summary_20260609(regression_or_plan)
    return json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def build_product_readfeel_p3_regression_green_fixture_results_20260609(
    *,
    include_optional_timeout: bool = False,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = [
        {
            "suite_id": suite_id,
            "status": STATUS_PASSED,
            "passed_count": 1,
            "failed_count": 0,
            "warning_count": 0,
            "split_execution_used": True,
        }
        for suite_id in BASELINE_REGRESSION_REQUIRED_SUITE_IDS_20260609
    ]
    if include_optional_timeout:
        rows.append(
            {
                "suite_id": "p3_grouped_chain_timeout_probe",
                "status": STATUS_EXPECTED_YELLOW_TIMEOUT,
                "passed_count": 0,
                "failed_count": 0,
                "warning_count": 0,
                "timeout_observed": True,
                "yellow_codes": ["grouped_timeout_probe_yellow_split_green_required"],
                "split_execution_used": False,
            }
        )
    return rows


__all__ = [
    "PRODUCT_READFEEL_P3_REGRESSION_VERSION_20260609",
    "PRODUCT_READFEEL_P3_REGRESSION_SUITE_VERSION_20260609",
    "PRODUCT_READFEEL_P3_REGRESSION_RESULT_VERSION_20260609",
    "PRODUCT_READFEEL_P3_REGRESSION_SUMMARY_VERSION_20260609",
    "PRODUCT_READFEEL_P3_REGRESSION_STEP_20260609",
    "STATUS_PASSED",
    "STATUS_FAILED",
    "STATUS_TIMEOUT",
    "STATUS_NOT_RUN",
    "STATUS_SKIPPED",
    "STATUS_EXPECTED_YELLOW_TIMEOUT",
    "DECISION_READY_FOR_FIRST_REPAIR",
    "DECISION_YELLOW_TIMEOUT",
    "DECISION_BLOCKED_REQUIRED_FAILURE",
    "DECISION_BLOCKED_NOT_EXECUTED",
    "DECISION_BLOCKED_P2_RED",
    "DECISION_BLOCKED_P1_DISPLAY",
    "DECISION_NO_RUNTIME_TARGET",
    "BASELINE_REGRESSION_REQUIRED_SUITE_IDS_20260609",
    "OPTIONAL_REGRESSION_SUITE_IDS_20260609",
    "REGRESSION_SUITES_20260609",
    "assert_product_readfeel_p3_regression_meta_only_20260609",
    "build_product_readfeel_p3_regression_plan_20260609",
    "build_product_readfeel_p3_regression_result_20260609",
    "build_product_readfeel_p3_regression_public_summary_20260609",
    "dump_product_readfeel_p3_regression_public_summary_20260609",
    "build_product_readfeel_p3_regression_green_fixture_results_20260609",
]
