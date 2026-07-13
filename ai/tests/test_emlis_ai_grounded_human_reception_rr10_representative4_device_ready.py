# -*- coding: utf-8 -*-
from __future__ import annotations

"""RR10 representative4 actual-device execution boundary.

The current artifact is readiness evidence, not an actual-device PASS.  The
tests bind the four device candidates to the live RR8/RR9 source and reject a
claimed PASS unless raw-backend hashes, UI evidence and Mash read-feel fields
are all present.  P5/P6/P8 progression remains closed even after a synthetic
RR10 4/4 contract pass; only RR11 evidence collection becomes eligible.
"""

import asyncio
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping

import pytest

from helpers.emlis_ai_grounded_human_reception_rr8_qa import (
    assert_body_free_metadata,
)
from emlis_ai_grounded_observation_gate import RECEPTION_GATE_REPORT_FIELDS
from emlis_ai_grounded_sentence_surface import split_two_stage_surface
from emlis_ai_reply_service import render_emlis_ai_reply
from tools.emlis_grounded_human_reception_rr10_verify_device_evidence import (
    validate_rr10_device_evidence_bundle,
)


_TEST_ROOT = Path(__file__).resolve().parent
_REPO_ROOT = _TEST_ROOT.parents[1]
_EXACT8 = _TEST_ROOT / "fixtures" / "grounded_human_reception_exact8_v2_20260712.json"
_RR8_RECEIPT = _TEST_ROOT / "fixtures" / "grounded_human_reception_rr8_local_qa_receipt_20260713.json"
_RR9_PACKET = _TEST_ROOT / "local_only" / "grounded_human_reception_rr9_visible_packet_20260713.json"
_RR9_RECEIPT = _TEST_ROOT / "fixtures" / "grounded_human_reception_rr9_karen_review_receipt_20260713.json"
_EXPECTED_PACKET = _TEST_ROOT / "local_only" / "grounded_human_reception_rr10_representative4_expected_packet_20260713.json"
_EVIDENCE_TEMPLATE = _TEST_ROOT / "local_only" / "grounded_human_reception_rr10_actual_device_evidence_template_20260713.json"
_READINESS = _TEST_ROOT / "fixtures" / "grounded_human_reception_rr10_representative4_device_readiness_20260713.json"
_EVIDENCE_VERIFIER = _REPO_ROOT / "ai" / "tools" / "emlis_grounded_human_reception_rr10_verify_device_evidence.py"

_REPRESENTATIVE4 = ("A", "B", "I6-L03", "I6-D02")
_SELECTION_ORDER = {
    "A": {
        "emotions": [
            {"label": "悲しみ", "intensity": "中"},
            {"label": "不安", "intensity": "中"},
        ],
        "categories": ["生活"],
    },
    "B": {
        "emotions": [{"label": "自己理解", "intensity": None}],
        "categories": ["学習"],
    },
    "I6-L03": {
        "emotions": [
            {"label": "喜び", "intensity": "中"},
            {"label": "不安", "intensity": "中"},
        ],
        "categories": ["趣味"],
    },
    "I6-D02": {
        "emotions": [{"label": "悲しみ", "intensity": "中"}],
        "categories": ["人生", "価値観"],
    },
}
_RUNTIME_GUARDS = (
    "runtime_visible_contract_guard",
    "runtime_reception_contract_guard",
    "runtime_gate_meta_body_free_guard",
    "runtime_final_contract_guard",
)
_MASH_AXES = (
    "not_bland",
    "sufficient_stay_with_long_input",
    "non_enumerative",
    "non_repetitive_language_and_skeleton",
    "natural_as_emlis_response",
    "short_input_not_water_filled",
)
_SOURCE_OWNER_PATHS = (
    "ai/services/ai_inference/emlis_ai_grounded_observation_plan.py",
    "ai/services/ai_inference/emlis_ai_grounded_human_reception.py",
    "ai/services/ai_inference/emlis_ai_grounded_sentence_surface.py",
    "ai/services/ai_inference/emlis_ai_grounded_observation_gate.py",
    "ai/services/ai_inference/emlis_ai_reply_service.py",
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_PASS_FIELDS = (
    "backend_gate_contract",
    "two_stage_display",
    "observation_regression",
    "depth_target",
    "clipping",
    "overlap",
    "scroll",
    "safety_boundary",
)
_EVIDENCE_CASE_KEYS = frozenset(
    {
        "case_id",
        "status",
        "failure_stage",
        "executed_at_jst",
        "exact_current_input_identity",
        "observed_selection_order",
        "selection_screenshot_ref",
        "selection_screenshot_sha256",
        "request_payload_ref",
        "request_payload_sha256",
        "observed_current_input_sha256",
        "request_trace_sha256",
        "backend_response_ref",
        "backend_response_sha256",
        "raw_comment_text_ref",
        "raw_comment_text_sha256",
        "hash_source",
        "observed_visible_surface_sha256",
        "observed_observation_section_sha256",
        "observed_reception_section_sha256",
        "backend_gate_meta_ref",
        "backend_gate_meta_sha256",
        "backend_gate_contract",
        "observed_depth_level",
        "observed_opportunity_count",
        "observed_planned_move_count",
        "observed_realized_move_count",
        "observed_sentence_count",
        "screenshot_evidence",
        "two_stage_display",
        "observation_regression",
        "depth_target",
        "clipping",
        "overlap",
        "scroll",
        "safety_boundary",
        "mash_product_readfeel_axes",
        "mash_product_readfeel",
        "mash_result_was_derived_from_automatic_gate",
        "mismatch_codes",
    }
)


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_json(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return _sha256_text(payload)


def _source_snapshot() -> tuple[list[dict[str, str]], str]:
    manifest = [
        {"path": path, "sha256": _sha256_file(_REPO_ROOT / path)}
        for path in _SOURCE_OWNER_PATHS
    ]
    return manifest, _sha256_json(manifest)


def _nonempty_ref(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _all_mapping_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        keys = {str(key) for key in value}
        for nested in value.values():
            keys.update(_all_mapping_keys(nested))
        return keys
    if isinstance(value, list):
        keys: set[str] = set()
        for nested in value:
            keys.update(_all_mapping_keys(nested))
        return keys
    return set()


def _validate_not_run_case(row: Mapping[str, Any]) -> list[str]:
    issues: list[str] = []
    if row.get("status") != "not_run":
        return issues
    null_fields = (
        "executed_at_jst",
        "failure_stage",
        "observed_selection_order",
        "selection_screenshot_ref",
        "selection_screenshot_sha256",
        "request_payload_ref",
        "request_payload_sha256",
        "observed_current_input_sha256",
        "request_trace_sha256",
        "backend_response_ref",
        "backend_response_sha256",
        "raw_comment_text_ref",
        "raw_comment_text_sha256",
        "hash_source",
        "observed_visible_surface_sha256",
        "observed_observation_section_sha256",
        "observed_reception_section_sha256",
        "backend_gate_meta_ref",
        "backend_gate_meta_sha256",
        "observed_depth_level",
        "observed_opportunity_count",
        "observed_planned_move_count",
        "observed_realized_move_count",
        "observed_sentence_count",
    )
    if any(row.get(field) is not None for field in null_fields):
        issues.append("rr10_not_run_case_preclaims_device_evidence")
    if row.get("exact_current_input_identity") != "not_evaluated":
        issues.append("rr10_not_run_case_preclaims_input_identity")
    if row.get("screenshot_evidence") != []:
        issues.append("rr10_not_run_case_preclaims_screenshot")
    if any(row.get(field) != "not_evaluated" for field in _PASS_FIELDS):
        issues.append("rr10_not_run_case_preclaims_device_judgment")
    axes = row.get("mash_product_readfeel_axes")
    if not isinstance(axes, dict) or set(axes) != set(_MASH_AXES):
        issues.append("rr10_mash_axes_schema_mismatch")
    elif set(axes.values()) != {"not_evaluated"}:
        issues.append("rr10_not_run_case_preclaims_mash_axes")
    if row.get("mash_product_readfeel") != "not_evaluated":
        issues.append("rr10_not_run_case_preclaims_mash_result")
    if row.get("mismatch_codes") != []:
        issues.append("rr10_not_run_case_preclaims_mismatch")
    return issues


def _validate_passed_case(
    row: Mapping[str, Any], expected: Mapping[str, Any]
) -> list[str]:
    issues: list[str] = []
    required_refs = (
        "executed_at_jst",
        "selection_screenshot_ref",
        "request_payload_ref",
        "backend_response_ref",
        "raw_comment_text_ref",
        "backend_gate_meta_ref",
    )
    if any(not _nonempty_ref(row.get(field)) for field in required_refs):
        issues.append("rr10_passed_case_missing_device_reference")
    if row.get("exact_current_input_identity") != "matched":
        issues.append("rr10_passed_case_input_identity_not_matched")
    if row.get("failure_stage") is not None:
        issues.append("rr10_passed_case_failure_stage_must_be_none")
    if row.get("observed_selection_order") != expected.get("selection_order"):
        issues.append("rr10_passed_case_selection_order_mismatch")
    trace_sha = row.get("request_trace_sha256")
    if not isinstance(trace_sha, str) or not _SHA256_RE.fullmatch(trace_sha):
        issues.append("rr10_passed_case_request_trace_invalid")
    request_sha = row.get("request_payload_sha256")
    if not isinstance(request_sha, str) or not _SHA256_RE.fullmatch(request_sha):
        issues.append("rr10_passed_case_request_payload_hash_invalid")
    for field in ("selection_screenshot_sha256", "backend_response_sha256"):
        value = row.get(field)
        if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
            issues.append(f"rr10_passed_case_{field}_invalid")
    gate_sha = row.get("backend_gate_meta_sha256")
    if not isinstance(gate_sha, str) or not _SHA256_RE.fullmatch(gate_sha):
        issues.append("rr10_passed_case_gate_meta_hash_invalid")
    if row.get("hash_source") != "backend_input_feedback_comment_text_utf8":
        issues.append("rr10_passed_case_hash_source_invalid")

    hash_bindings = (
        ("observed_current_input_sha256", "current_input_sha256"),
        ("raw_comment_text_sha256", "expected_visible_surface_sha256"),
        ("observed_visible_surface_sha256", "expected_visible_surface_sha256"),
        ("observed_observation_section_sha256", "expected_observation_section_sha256"),
        ("observed_reception_section_sha256", "expected_reception_section_sha256"),
        ("observed_depth_level", "expected_depth_level"),
        ("observed_opportunity_count", "expected_opportunity_count"),
        ("observed_planned_move_count", "expected_planned_move_count"),
        ("observed_realized_move_count", "expected_realized_move_count"),
        ("observed_sentence_count", "expected_sentence_count"),
    )
    for actual_field, expected_field in hash_bindings:
        if row.get(actual_field) != expected.get(expected_field):
            issues.append(f"rr10_passed_case_{actual_field}_mismatch")

    screenshots = row.get("screenshot_evidence")
    if not isinstance(screenshots, list) or not screenshots:
        issues.append("rr10_passed_case_screenshot_missing")
        screenshots = []
    roles: set[str] = set()
    allowed_roles = {"modal_full", "modal_top", "modal_middle", "modal_bottom"}
    for item in screenshots:
        if not isinstance(item, dict) or set(item) != {"capture_role", "ref", "sha256"}:
            issues.append("rr10_passed_case_screenshot_schema_mismatch")
            continue
        roles.add(str(item.get("capture_role") or ""))
        if item.get("capture_role") not in allowed_roles:
            issues.append("rr10_passed_case_screenshot_role_invalid")
        if not _nonempty_ref(item.get("ref")):
            issues.append("rr10_passed_case_screenshot_ref_missing")
        if not isinstance(item.get("sha256"), str) or not _SHA256_RE.fullmatch(item["sha256"]):
            issues.append("rr10_passed_case_screenshot_hash_invalid")
    if row.get("case_id") in {"B", "I6-L03"} and not {
        "modal_top",
        "modal_bottom",
    }.issubset(roles):
        issues.append("rr10_long_case_modal_coverage_missing")
    if row.get("case_id") in {"A", "I6-D02"} and "modal_full" not in roles:
        issues.append("rr10_short_or_safety_case_modal_full_missing")
    if any(row.get(field) != "pass" for field in _PASS_FIELDS):
        issues.append("rr10_passed_case_device_axis_not_passed")
    axes = row.get("mash_product_readfeel_axes")
    if not isinstance(axes, dict) or set(axes) != set(_MASH_AXES):
        issues.append("rr10_mash_axes_schema_mismatch")
    elif set(axes.values()) != {"pass"}:
        issues.append("rr10_passed_case_mash_axis_not_passed")
    if row.get("mash_product_readfeel") != "pass":
        issues.append("rr10_passed_case_mash_result_not_passed")
    if row.get("mash_result_was_derived_from_automatic_gate") is not False:
        issues.append("rr10_mash_result_automatic_derivation_forbidden")
    if row.get("mismatch_codes") != []:
        issues.append("rr10_passed_case_has_mismatch")
    return issues


def _validate_failed_case(
    row: Mapping[str, Any], expected: Mapping[str, Any]
) -> list[str]:
    issues: list[str] = []
    required_refs = (
        "executed_at_jst",
        "selection_screenshot_ref",
        "request_payload_ref",
        "backend_response_ref",
        "raw_comment_text_ref",
        "backend_gate_meta_ref",
    )
    if any(not _nonempty_ref(row.get(field)) for field in required_refs):
        issues.append("rr10_failed_case_missing_device_reference")
    if row.get("exact_current_input_identity") not in {"matched", "mismatch"}:
        issues.append("rr10_failed_case_input_identity_invalid")
    if row.get("failure_stage") not in {
        "input_identity",
        "backend_contract",
        "visible_surface",
        "display",
        "product_readfeel",
    }:
        issues.append("rr10_failed_case_failure_stage_invalid")
    for field in (
        "request_trace_sha256",
        "selection_screenshot_sha256",
        "request_payload_sha256",
        "observed_current_input_sha256",
        "backend_response_sha256",
        "raw_comment_text_sha256",
        "observed_visible_surface_sha256",
        "observed_observation_section_sha256",
        "observed_reception_section_sha256",
        "backend_gate_meta_sha256",
    ):
        value = row.get(field)
        if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
            issues.append(f"rr10_failed_case_{field}_invalid")
    if row.get("hash_source") != "backend_input_feedback_comment_text_utf8":
        issues.append("rr10_failed_case_hash_source_invalid")

    screenshots = row.get("screenshot_evidence")
    if not isinstance(screenshots, list) or not screenshots:
        issues.append("rr10_failed_case_screenshot_missing")
        screenshots = []
    roles: set[str] = set()
    allowed_roles = {"modal_full", "modal_top", "modal_middle", "modal_bottom"}
    for item in screenshots:
        if not isinstance(item, dict) or set(item) != {"capture_role", "ref", "sha256"}:
            issues.append("rr10_failed_case_screenshot_schema_mismatch")
            continue
        roles.add(str(item.get("capture_role") or ""))
        if item.get("capture_role") not in allowed_roles:
            issues.append("rr10_failed_case_screenshot_role_invalid")
        if not _nonempty_ref(item.get("ref")):
            issues.append("rr10_failed_case_screenshot_ref_missing")
        if not isinstance(item.get("sha256"), str) or not _SHA256_RE.fullmatch(item["sha256"]):
            issues.append("rr10_failed_case_screenshot_hash_invalid")
    if row.get("case_id") in {"B", "I6-L03"} and not {
        "modal_top",
        "modal_bottom",
    }.issubset(roles):
        issues.append("rr10_failed_long_case_modal_coverage_missing")
    if row.get("case_id") in {"A", "I6-D02"} and "modal_full" not in roles:
        issues.append("rr10_failed_short_or_safety_case_modal_full_missing")

    if any(row.get(field) not in {"pass", "fail"} for field in _PASS_FIELDS):
        issues.append("rr10_failed_case_device_axis_not_evaluated")
    axes = row.get("mash_product_readfeel_axes")
    if not isinstance(axes, dict) or set(axes) != set(_MASH_AXES):
        issues.append("rr10_mash_axes_schema_mismatch")
        axes = {}
    elif any(value not in {"pass", "fail"} for value in axes.values()):
        issues.append("rr10_failed_case_mash_axis_not_evaluated")
    if row.get("mash_product_readfeel") not in {"pass", "fail"}:
        issues.append("rr10_failed_case_mash_result_not_evaluated")
    if row.get("mash_result_was_derived_from_automatic_gate") is not False:
        issues.append("rr10_mash_result_automatic_derivation_forbidden")
    mismatch_codes = row.get("mismatch_codes")
    if not isinstance(mismatch_codes, list) or not mismatch_codes:
        issues.append("rr10_failed_case_mismatch_code_missing")

    hash_mismatch = any(
        row.get(actual_field) != expected.get(expected_field)
        for actual_field, expected_field in (
            ("raw_comment_text_sha256", "expected_visible_surface_sha256"),
            ("observed_visible_surface_sha256", "expected_visible_surface_sha256"),
            ("observed_observation_section_sha256", "expected_observation_section_sha256"),
            ("observed_reception_section_sha256", "expected_reception_section_sha256"),
        )
    )
    axis_failure = any(row.get(field) == "fail" for field in _PASS_FIELDS)
    mash_failure = (
        any(value == "fail" for value in axes.values())
        or row.get("mash_product_readfeel") == "fail"
    )
    input_mismatch = row.get("exact_current_input_identity") == "mismatch"
    if not (hash_mismatch or axis_failure or mash_failure or input_mismatch):
        issues.append("rr10_failed_case_has_no_recorded_failure")
    return issues


def _validate_blocked_case(
    row: Mapping[str, Any], expected: Mapping[str, Any]
) -> list[str]:
    issues: list[str] = []
    if row.get("failure_stage") not in {
        "input_identity",
        "submission",
        "backend_response_unavailable",
    }:
        issues.append("rr10_blocked_case_failure_stage_invalid")
    for field in (
        "executed_at_jst",
        "selection_screenshot_ref",
        "request_payload_ref",
    ):
        if not _nonempty_ref(row.get(field)):
            issues.append("rr10_blocked_case_required_reference_missing")
            break
    for field in (
        "selection_screenshot_sha256",
        "request_payload_sha256",
        "observed_current_input_sha256",
        "request_trace_sha256",
    ):
        value = row.get(field)
        if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
            issues.append(f"rr10_blocked_case_{field}_invalid")
    if row.get("observed_selection_order") != expected.get("selection_order"):
        issues.append("rr10_blocked_case_selection_order_mismatch")
    downstream_null_fields = (
        "backend_response_ref",
        "backend_response_sha256",
        "raw_comment_text_ref",
        "raw_comment_text_sha256",
        "hash_source",
        "observed_visible_surface_sha256",
        "observed_observation_section_sha256",
        "observed_reception_section_sha256",
        "backend_gate_meta_ref",
        "backend_gate_meta_sha256",
        "observed_depth_level",
        "observed_opportunity_count",
        "observed_planned_move_count",
        "observed_realized_move_count",
        "observed_sentence_count",
    )
    if any(row.get(field) is not None for field in downstream_null_fields):
        issues.append("rr10_blocked_case_preclaims_unavailable_downstream_evidence")
    if row.get("screenshot_evidence") != []:
        issues.append("rr10_blocked_case_preclaims_modal_evidence")
    if any(row.get(field) != "not_evaluated" for field in _PASS_FIELDS):
        issues.append("rr10_blocked_case_preclaims_device_axis")
    axes = row.get("mash_product_readfeel_axes")
    if not isinstance(axes, dict) or set(axes) != set(_MASH_AXES) or set(
        axes.values()
    ) != {"not_evaluated"}:
        issues.append("rr10_blocked_case_preclaims_mash_axes")
    if row.get("mash_product_readfeel") != "not_evaluated":
        issues.append("rr10_blocked_case_preclaims_mash_result")
    if not isinstance(row.get("mismatch_codes"), list) or not row.get(
        "mismatch_codes"
    ):
        issues.append("rr10_blocked_case_mismatch_code_missing")
    return issues


def _validate_device_evidence(
    evidence: Mapping[str, Any], expected_packet: Mapping[str, Any]
) -> tuple[str, ...]:
    issues: list[str] = []
    if evidence.get("schema_version") != (
        "cocolon.emlis.grounded_human_reception."
        "rr10_actual_device_evidence.local_only.v1"
    ):
        issues.append("rr10_evidence_schema_version_mismatch")
    if evidence.get("local_only") is not True:
        issues.append("rr10_evidence_local_only_missing")
    if evidence.get("expected_packet_sha256") != _sha256_file(_EXPECTED_PACKET):
        issues.append("rr10_evidence_expected_packet_hash_mismatch")
    if evidence.get("representative_case_order") != list(_REPRESENTATIVE4):
        issues.append("rr10_evidence_case_order_mismatch")

    expected_by_id = {
        row.get("case_id"): row
        for row in expected_packet.get("cases", [])
        if isinstance(row, dict) and row.get("case_id")
    }
    rows = evidence.get("cases")
    if not isinstance(rows, list) or len(rows) != 4:
        issues.append("rr10_evidence_case_count_mismatch")
        rows = []
    case_ids = [row.get("case_id") for row in rows if isinstance(row, dict)]
    if case_ids != list(_REPRESENTATIVE4):
        issues.append("rr10_evidence_case_identity_or_order_mismatch")
    if len(set(case_ids)) != len(case_ids):
        issues.append("rr10_evidence_case_duplicate")

    traces: list[str] = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != _EVIDENCE_CASE_KEYS:
            issues.append("rr10_evidence_case_schema_mismatch")
            continue
        status = row.get("status")
        expected_row = expected_by_id.get(row.get("case_id"))
        if expected_row is None:
            issues.append("rr10_evidence_unknown_case_id")
            continue
        if status == "not_run":
            issues.extend(_validate_not_run_case(row))
        elif status == "passed":
            issues.extend(_validate_passed_case(row, expected_row))
            traces.append(str(row.get("request_trace_sha256") or ""))
        elif status == "failed":
            issues.extend(_validate_failed_case(row, expected_row))
            traces.append(str(row.get("request_trace_sha256") or ""))
        elif status == "blocked":
            issues.extend(_validate_blocked_case(row, expected_row))
            traces.append(str(row.get("request_trace_sha256") or ""))
        else:
            issues.append("rr10_evidence_case_status_invalid")
    if len(traces) != len(set(traces)):
        issues.append("rr10_evidence_request_trace_reused")

    summary = evidence.get("execution_summary")
    if not isinstance(summary, dict):
        issues.append("rr10_evidence_summary_missing")
        summary = {}
    if summary.get("progression_authority") != "none":
        issues.append("rr10_progression_authority_must_remain_none")
    for field in (
        "p5_formal_24_start_allowed",
        "p6_start_allowed",
        "p8_start_allowed",
        "valid_for_progression",
    ):
        if summary.get(field) is not False:
            issues.append(f"rr10_{field}_must_remain_false")

    statuses = [
        row.get("status") if isinstance(row, dict) else "invalid"
        for row in rows
    ]
    passed_count = statuses.count("passed")
    failed_count = statuses.count("failed")
    blocked_count = statuses.count("blocked")
    not_run_count = statuses.count("not_run")
    if passed_count == 0 and not_run_count == 4:
        if summary.get("actual_device_execution_status") != "not_run":
            issues.append("rr10_not_run_summary_status_invalid")
        if summary.get("passed_case_count") != 0 or summary.get("failed_case_count") != 0:
            issues.append("rr10_not_run_summary_counts_invalid")
        if summary.get("first_failed_case_id") is not None:
            issues.append("rr10_not_run_summary_failure_preclaimed")
        if summary.get("rr11_exact8_actual_device_allowed") is not False:
            issues.append("rr10_rr11_must_remain_closed_before_execution")
    elif passed_count == 4:
        environment = evidence.get("execution_environment")
        required_environment = (
            "executed_at_jst",
            "app_build_identity",
            "deployment_identity",
            "device_model",
            "os_version",
            "app_version",
        )
        if not isinstance(environment, dict) or any(
            not _nonempty_ref(environment.get(field)) for field in required_environment
        ):
            issues.append("rr10_passed_environment_incomplete")
        elif environment.get("deployed_source_snapshot_sha256") != expected_packet.get(
            "source_snapshot_sha256"
        ):
            issues.append("rr10_deployed_source_snapshot_mismatch")
        if summary.get("actual_device_execution_status") != "passed":
            issues.append("rr10_passed_summary_status_invalid")
        if summary.get("passed_case_count") != 4 or summary.get("failed_case_count") != 0:
            issues.append("rr10_passed_summary_counts_invalid")
        if summary.get("first_failed_case_id") is not None:
            issues.append("rr10_passed_summary_failure_invalid")
        if summary.get("rr11_exact8_actual_device_allowed") is not True:
            issues.append("rr10_rr11_evidence_collection_not_opened_after_4of4")
    elif failed_count == 1:
        failed_index = statuses.index("failed")
        expected_statuses = ["passed"] * failed_index + ["failed"] + [
            "not_run"
        ] * (3 - failed_index)
        if statuses != expected_statuses:
            issues.append("rr10_failure_did_not_stop_later_cases")
        environment = evidence.get("execution_environment")
        required_environment = (
            "executed_at_jst",
            "app_build_identity",
            "deployment_identity",
            "device_model",
            "os_version",
            "app_version",
        )
        if not isinstance(environment, dict) or any(
            not _nonempty_ref(environment.get(field)) for field in required_environment
        ):
            issues.append("rr10_failed_environment_incomplete")
        if summary.get("actual_device_execution_status") != "failed":
            issues.append("rr10_failed_summary_status_invalid")
        if summary.get("passed_case_count") != failed_index or summary.get(
            "failed_case_count"
        ) != 1:
            issues.append("rr10_failed_summary_counts_invalid")
        if summary.get("first_failed_case_id") != _REPRESENTATIVE4[failed_index]:
            issues.append("rr10_failed_summary_case_invalid")
        if summary.get("rr11_exact8_actual_device_allowed") is not False:
            issues.append("rr10_rr11_opened_after_failure")
    elif blocked_count == 1:
        blocked_index = statuses.index("blocked")
        expected_statuses = ["passed"] * blocked_index + ["blocked"] + [
            "not_run"
        ] * (3 - blocked_index)
        if statuses != expected_statuses:
            issues.append("rr10_block_did_not_stop_later_cases")
        if summary.get("actual_device_execution_status") != "blocked":
            issues.append("rr10_blocked_summary_status_invalid")
        if summary.get("passed_case_count") != blocked_index or summary.get(
            "failed_case_count"
        ) != 1:
            issues.append("rr10_blocked_summary_counts_invalid")
        if summary.get("first_failed_case_id") != _REPRESENTATIVE4[blocked_index]:
            issues.append("rr10_blocked_summary_case_invalid")
        if summary.get("rr11_exact8_actual_device_allowed") is not False:
            issues.append("rr10_rr11_opened_after_block")
    else:
        issues.append("rr10_partial_or_failed_execution_requires_new_evidence_receipt")
        if summary.get("rr11_exact8_actual_device_allowed") is not False:
            issues.append("rr10_rr11_opened_without_4of4")
    return tuple(dict.fromkeys(issues))


def _synthetic_complete_pass() -> dict[str, Any]:
    evidence = deepcopy(_load(_EVIDENCE_TEMPLATE))
    expected = _load(_EXPECTED_PACKET)
    evidence["execution_environment"] = {
        "executed_at_jst": "2026-07-13T12:00:00+09:00",
        "app_build_identity": "synthetic-contract-build",
        "deployment_identity": "synthetic-contract-deploy",
        "deployed_source_snapshot_sha256": expected["source_snapshot_sha256"],
        "device_model": "synthetic-contract-device",
        "os_version": "synthetic-contract-os",
        "app_version": "synthetic-contract-app",
    }
    expected_by_id = {row["case_id"]: row for row in expected["cases"]}
    for index, row in enumerate(evidence["cases"], start=1):
        expected_row = expected_by_id[row["case_id"]]
        trace = hashlib.sha256(f"rr10-trace-{index}".encode()).hexdigest()
        gate_sha = hashlib.sha256(f"rr10-gates-{index}".encode()).hexdigest()
        roles = ["modal_full"]
        if row["case_id"] in {"B", "I6-L03"}:
            roles = ["modal_top", "modal_bottom"]
        row.update(
            {
                "status": "passed",
                "failure_stage": None,
                "executed_at_jst": f"2026-07-13T12:0{index}:00+09:00",
                "exact_current_input_identity": "matched",
                "observed_selection_order": expected_row["selection_order"],
                "selection_screenshot_ref": f"synthetic/selection/{row['case_id']}.png",
                "selection_screenshot_sha256": "2" * 64,
                "request_payload_ref": f"synthetic/requests/{row['case_id']}.json",
                "request_payload_sha256": "1" * 64,
                "observed_current_input_sha256": expected_row["current_input_sha256"],
                "request_trace_sha256": trace,
                "backend_response_ref": f"synthetic/responses/{row['case_id']}.json",
                "backend_response_sha256": "3" * 64,
                "raw_comment_text_ref": f"synthetic/raw/{row['case_id']}.txt",
                "raw_comment_text_sha256": expected_row["expected_visible_surface_sha256"],
                "hash_source": "backend_input_feedback_comment_text_utf8",
                "observed_visible_surface_sha256": expected_row["expected_visible_surface_sha256"],
                "observed_observation_section_sha256": expected_row["expected_observation_section_sha256"],
                "observed_reception_section_sha256": expected_row["expected_reception_section_sha256"],
                "backend_gate_meta_ref": f"synthetic/gates/{row['case_id']}.json",
                "backend_gate_meta_sha256": gate_sha,
                "backend_gate_contract": "pass",
                "observed_depth_level": expected_row["expected_depth_level"],
                "observed_opportunity_count": expected_row["expected_opportunity_count"],
                "observed_planned_move_count": expected_row["expected_planned_move_count"],
                "observed_realized_move_count": expected_row["expected_realized_move_count"],
                "observed_sentence_count": expected_row["expected_sentence_count"],
                "screenshot_evidence": [
                    {
                        "capture_role": role,
                        "ref": f"synthetic/screens/{row['case_id']}-{role}.png",
                        "sha256": hashlib.sha256(
                            f"rr10-screen-{row['case_id']}-{role}".encode()
                        ).hexdigest(),
                    }
                    for role in roles
                ],
                "two_stage_display": "pass",
                "observation_regression": "pass",
                "depth_target": "pass",
                "clipping": "pass",
                "overlap": "pass",
                "scroll": "pass",
                "safety_boundary": "pass",
                "mash_product_readfeel_axes": {axis: "pass" for axis in _MASH_AXES},
                "mash_product_readfeel": "pass",
                "mash_result_was_derived_from_automatic_gate": False,
                "mismatch_codes": [],
            }
        )
    evidence["execution_summary"].update(
        {
            "actual_device_execution_status": "passed",
            "passed_case_count": 4,
            "failed_case_count": 0,
            "first_failed_case_id": None,
            "rr11_exact8_actual_device_allowed": True,
        }
    )
    return evidence


def _materialize_contract_bundle(
    bundle_root: Path, evidence: dict[str, Any]
) -> None:
    exact_by_id = {row["case_id"]: row for row in _load(_EXACT8)["cases"]}
    rr9_by_id = {row["case_id"]: row for row in _load(_RR9_PACKET)["cases"]}

    for row in evidence["cases"]:
        case_id = row["case_id"]
        current_input = exact_by_id[case_id]["exact_current_input"]
        request_bytes = json.dumps(
            current_input,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        request_path = bundle_root / row["request_payload_ref"]
        request_path.parent.mkdir(parents=True, exist_ok=True)
        request_path.write_bytes(request_bytes)
        row["request_payload_sha256"] = hashlib.sha256(request_bytes).hexdigest()

        selection_bytes = (
            f"synthetic-contract-selection:{case_id}"
        ).encode("utf-8")
        selection_path = bundle_root / row["selection_screenshot_ref"]
        selection_path.parent.mkdir(parents=True, exist_ok=True)
        selection_path.write_bytes(selection_bytes)
        row["selection_screenshot_sha256"] = hashlib.sha256(
            selection_bytes
        ).hexdigest()

        comment_bytes = rr9_by_id[case_id]["visible_surface"].encode("utf-8")
        comment_path = bundle_root / row["raw_comment_text_ref"]
        comment_path.parent.mkdir(parents=True, exist_ok=True)
        comment_path.write_bytes(comment_bytes)
        row["raw_comment_text_sha256"] = hashlib.sha256(comment_bytes).hexdigest()

        response_payload = {
            "input_feedback": {
                "comment_text": rr9_by_id[case_id]["visible_surface"],
                "emlis_ai": {"observation_status": "passed"},
            }
        }
        response_bytes = json.dumps(
            response_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        response_path = bundle_root / row["backend_response_ref"]
        response_path.parent.mkdir(parents=True, exist_ok=True)
        response_path.write_bytes(response_bytes)
        row["backend_response_sha256"] = hashlib.sha256(response_bytes).hexdigest()

        reply = asyncio.run(
            render_emlis_ai_reply(
                user_id=f"rr10-bundle-{case_id}",
                subscription_tier="free",
                current_input=current_input,
            )
        )
        gate_meta = reply.meta["grounded_observation"]
        gate_bytes = json.dumps(
            gate_meta,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        gate_path = bundle_root / row["backend_gate_meta_ref"]
        gate_path.parent.mkdir(parents=True, exist_ok=True)
        gate_path.write_bytes(gate_bytes)
        row["backend_gate_meta_sha256"] = hashlib.sha256(gate_bytes).hexdigest()

        for item in row["screenshot_evidence"]:
            screen_bytes = (
                f"synthetic-contract-screen:{case_id}:{item['capture_role']}"
            ).encode("utf-8")
            screen_path = bundle_root / item["ref"]
            screen_path.parent.mkdir(parents=True, exist_ok=True)
            screen_path.write_bytes(screen_bytes)
            item["sha256"] = hashlib.sha256(screen_bytes).hexdigest()


def test_rr10_expected_packet_is_bound_to_rr8_rr9_and_current_source() -> None:
    packet = _load(_EXPECTED_PACKET)
    rr8_receipt = _load(_RR8_RECEIPT)
    rr9_packet = _load(_RR9_PACKET)
    rr9_receipt = _load(_RR9_RECEIPT)
    source_manifest, source_snapshot_sha256 = _source_snapshot()

    assert packet["schema_version"].endswith("expected_packet.local_only.v1")
    assert packet["representative_case_order"] == list(_REPRESENTATIVE4)
    assert packet["app_validated_input_source_sha256"] == (
        "1edd057a6fc246ab24ec1f886eaf1b22292b658cd09bf92a53665bf55bb02c86"
    )
    assert {
        row["case_id"]: row["selection_order"] for row in packet["cases"]
    } == _SELECTION_ORDER
    assert packet["exact8_fixture_sha256"] == _sha256_file(_EXACT8)
    assert packet["rr8_local_qa_receipt_sha256"] == _sha256_file(_RR8_RECEIPT)
    assert packet["rr9_visible_packet_sha256"] == _sha256_file(_RR9_PACKET)
    assert packet["rr9_karen_review_receipt_sha256"] == _sha256_file(_RR9_RECEIPT)
    assert packet["source_snapshot_sha256"] == source_snapshot_sha256
    assert rr8_receipt["source_snapshot_files"] == source_manifest
    assert rr8_receipt["source_snapshot_sha256"] == source_snapshot_sha256
    assert rr8_receipt["technical_acceptance"] == "passed"
    assert rr9_packet["source_snapshot_files"] == source_manifest
    assert rr9_receipt["source_snapshot_sha256"] == source_snapshot_sha256
    assert rr9_receipt["product_readfeel_status"] == "human_pass"
    assert packet["legacy_r7_device_packet_reused"] is False
    assert packet["legacy_actual_device_evidence_reused"] is False
    assert packet["actual_device_execution_status"] == "not_run"
    assert packet["progression_authority"] == "none"
    assert packet["valid_for_progression"] is False


def test_rr10_representative4_live_runtime_matches_rr9_hash_depth_and_gates() -> None:
    exact_by_id = {row["case_id"]: row for row in _load(_EXACT8)["cases"]}
    rr9_by_id = {row["case_id"]: row for row in _load(_RR9_PACKET)["cases"]}
    packet = _load(_EXPECTED_PACKET)

    for expected in packet["cases"]:
        case_id = expected["case_id"]
        current_input = exact_by_id[case_id]["exact_current_input"]
        assert expected["current_input_sha256"] == _sha256_json(current_input)
        reply = asyncio.run(
            render_emlis_ai_reply(
                user_id=f"rr10-representative4-{case_id}",
                subscription_tier="free",
                current_input=current_input,
            )
        )
        observation, reception, issues = split_two_stage_surface(reply.comment_text)
        assert issues == ()
        rr9_row = rr9_by_id[case_id]
        assert reply.comment_text == rr9_row["visible_surface"]
        assert _sha256_text(reply.comment_text) == expected["expected_visible_surface_sha256"]
        assert _sha256_text(observation.strip()) == expected["expected_observation_section_sha256"]
        assert _sha256_text(reception.strip()) == expected["expected_reception_section_sha256"]

        meta = reply.meta["grounded_observation"]
        assert meta["reception_depth_level"] == expected["expected_depth_level"]
        assert meta["reception_opportunity_count"] == expected["expected_opportunity_count"]
        assert meta["reception_planned_move_count"] == expected["expected_planned_move_count"]
        assert meta["reception_realized_move_count"] == expected["expected_realized_move_count"]
        assert meta["reception_sentence_count"] == expected["expected_sentence_count"]
        assert all(meta[field] == "passed" for field in RECEPTION_GATE_REPORT_FIELDS)
        assert all(meta[field] == "passed" for field in _RUNTIME_GUARDS)
        assert meta["reception_all_gates_passed"] is True
        assert meta["raw_character_count_used"] is False
        assert reply.meta["public_contract_changed"] is False
        assert reply.meta["api_route_changed"] is False
        assert reply.meta["db_physical_name_changed"] is False
        assert reply.meta["rn_visible_contract_changed"] is False


def test_rr10_unexecuted_template_is_strictly_not_run_and_progression_closed() -> None:
    packet = _load(_EXPECTED_PACKET)
    evidence = _load(_EVIDENCE_TEMPLATE)

    assert _validate_device_evidence(evidence, packet) == ()
    assert evidence["execution_summary"] == {
        "actual_device_execution_status": "not_run",
        "passed_case_count": 0,
        "failed_case_count": 0,
        "first_failed_case_id": None,
        "rr11_exact8_actual_device_allowed": False,
        "p5_formal_24_start_allowed": False,
        "p6_start_allowed": False,
        "p8_start_allowed": False,
        "progression_authority": "none",
        "valid_for_progression": False,
    }


def test_rr10_validator_accepts_complete_4of4_only_for_rr11_evidence_collection() -> None:
    packet = _load(_EXPECTED_PACKET)
    synthetic = _synthetic_complete_pass()

    assert _validate_device_evidence(synthetic, packet) == ()
    summary = synthetic["execution_summary"]
    assert summary["rr11_exact8_actual_device_allowed"] is True
    assert summary["p5_formal_24_start_allowed"] is False
    assert summary["p6_start_allowed"] is False
    assert summary["p8_start_allowed"] is False
    assert summary["progression_authority"] == "none"
    assert summary["valid_for_progression"] is False


def test_rr10_bundle_verifier_recomputes_input_body_sections_gates_and_files(
    tmp_path: Path,
) -> None:
    packet = _load(_EXPECTED_PACKET)
    evidence = _synthetic_complete_pass()
    _materialize_contract_bundle(tmp_path, evidence)

    assert _validate_device_evidence(evidence, packet) == ()
    assert validate_rr10_device_evidence_bundle(
        expected_packet=packet,
        evidence=evidence,
        bundle_root=tmp_path,
        expected_packet_sha256=_sha256_file(_EXPECTED_PACKET),
    ) == ()


@pytest.mark.parametrize(
    ("tamper_kind", "expected_issue_suffix"),
    [
        ("raw_comment", "raw_comment_file_hash_mismatch"),
        ("request_payload", "observed_input_hash_not_reproducible"),
        ("gate_meta", "gate_contract_not_reproducible"),
    ],
)
def test_rr10_bundle_verifier_rejects_tampered_evidence_bytes(
    tmp_path: Path,
    tamper_kind: str,
    expected_issue_suffix: str,
) -> None:
    packet = _load(_EXPECTED_PACKET)
    evidence = _synthetic_complete_pass()
    _materialize_contract_bundle(tmp_path, evidence)
    row = evidence["cases"][0]

    if tamper_kind == "raw_comment":
        (tmp_path / row["raw_comment_text_ref"]).write_bytes(b"tampered")
    elif tamper_kind == "request_payload":
        path = tmp_path / row["request_payload_ref"]
        payload = json.dumps(
            {"memo": "different"},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        path.write_bytes(payload)
        row["request_payload_sha256"] = hashlib.sha256(payload).hexdigest()
    else:
        path = tmp_path / row["backend_gate_meta_ref"]
        meta = json.loads(path.read_text(encoding="utf-8"))
        meta["reception_plan_gate"] = "failed"
        payload = json.dumps(
            meta,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        path.write_bytes(payload)
        row["backend_gate_meta_sha256"] = hashlib.sha256(payload).hexdigest()

    issues = validate_rr10_device_evidence_bundle(
        expected_packet=packet,
        evidence=evidence,
        bundle_root=tmp_path,
        expected_packet_sha256=_sha256_file(_EXPECTED_PACKET),
    )
    assert any(issue.endswith(expected_issue_suffix) for issue in issues)


def test_rr10_validator_accepts_first_failure_and_keeps_rr11_closed() -> None:
    packet = _load(_EXPECTED_PACKET)
    evidence = _synthetic_complete_pass()
    failed = evidence["cases"][1]
    failed.update(
        {
            "status": "failed",
            "failure_stage": "visible_surface",
            "observed_visible_surface_sha256": "0" * 64,
            "mismatch_codes": ["visible_surface_sha256_mismatch"],
        }
    )
    for row in evidence["cases"][2:]:
        template = next(
            item
            for item in _load(_EVIDENCE_TEMPLATE)["cases"]
            if item["case_id"] == row["case_id"]
        )
        row.clear()
        row.update(template)
    evidence["execution_summary"].update(
        {
            "actual_device_execution_status": "failed",
            "passed_case_count": 1,
            "failed_case_count": 1,
            "first_failed_case_id": "B",
            "rr11_exact8_actual_device_allowed": False,
        }
    )

    assert _validate_device_evidence(evidence, packet) == ()


def test_rr10_validator_accepts_early_submission_block_without_downstream_body(
    tmp_path: Path,
) -> None:
    packet = _load(_EXPECTED_PACKET)
    evidence = deepcopy(_load(_EVIDENCE_TEMPLATE))
    expected = packet["cases"][0]
    current_input = _load(_EXACT8)["cases"][0]["exact_current_input"]
    request_bytes = json.dumps(
        current_input,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    request_ref = "blocked/request.json"
    request_path = tmp_path / request_ref
    request_path.parent.mkdir(parents=True, exist_ok=True)
    request_path.write_bytes(request_bytes)
    selection_bytes = b"blocked-selection-screen"
    selection_ref = "blocked/selection.png"
    (tmp_path / selection_ref).write_bytes(selection_bytes)
    evidence["execution_environment"] = {
        "executed_at_jst": "2026-07-13T12:00:00+09:00",
        "app_build_identity": "blocked-contract-build",
        "deployment_identity": "blocked-contract-deploy",
        "deployed_source_snapshot_sha256": packet["source_snapshot_sha256"],
        "device_model": "blocked-contract-device",
        "os_version": "blocked-contract-os",
        "app_version": "blocked-contract-app",
    }
    evidence["cases"][0].update(
        {
            "status": "blocked",
            "failure_stage": "submission",
            "executed_at_jst": "2026-07-13T12:01:00+09:00",
            "exact_current_input_identity": "matched",
            "observed_selection_order": expected["selection_order"],
            "selection_screenshot_ref": selection_ref,
            "selection_screenshot_sha256": hashlib.sha256(selection_bytes).hexdigest(),
            "request_payload_ref": request_ref,
            "request_payload_sha256": hashlib.sha256(request_bytes).hexdigest(),
            "observed_current_input_sha256": expected["current_input_sha256"],
            "request_trace_sha256": hashlib.sha256(b"blocked-trace").hexdigest(),
            "mismatch_codes": ["submission_failed_before_backend_response"],
        }
    )
    evidence["execution_summary"].update(
        {
            "actual_device_execution_status": "blocked",
            "passed_case_count": 0,
            "failed_case_count": 1,
            "first_failed_case_id": "A",
            "rr11_exact8_actual_device_allowed": False,
        }
    )

    assert _validate_device_evidence(evidence, packet) == ()
    assert validate_rr10_device_evidence_bundle(
        expected_packet=packet,
        evidence=evidence,
        bundle_root=tmp_path,
        expected_packet_sha256=_sha256_file(_EXPECTED_PACKET),
    ) == ()


@pytest.mark.parametrize("malformation", ("non_mapping_row", "unknown_case"))
def test_rr10_validator_fails_closed_for_malformed_case_rows(
    malformation: str,
) -> None:
    packet = _load(_EXPECTED_PACKET)
    evidence = deepcopy(_load(_EVIDENCE_TEMPLATE))
    if malformation == "non_mapping_row":
        evidence["cases"][0] = None
        expected_issue = "rr10_evidence_case_schema_mismatch"
    else:
        evidence["cases"][0]["case_id"] = "UNKNOWN"
        expected_issue = "rr10_evidence_unknown_case_id"

    assert expected_issue in _validate_device_evidence(evidence, packet)


@pytest.mark.parametrize(
    ("mutation", "expected_issue"),
    [
        (
            lambda data: data["cases"][1].update(
                {"observed_visible_surface_sha256": "0" * 64}
            ),
            "rr10_passed_case_observed_visible_surface_sha256_mismatch",
        ),
        (
            lambda data: data["cases"][0].update({"hash_source": "screenshot_ocr"}),
            "rr10_passed_case_hash_source_invalid",
        ),
        (
            lambda data: data["cases"][2].update({"screenshot_evidence": []}),
            "rr10_passed_case_screenshot_missing",
        ),
        (
            lambda data: data["cases"][1].update(
                {
                    "screenshot_evidence": [
                        data["cases"][1]["screenshot_evidence"][0]
                    ]
                }
            ),
            "rr10_long_case_modal_coverage_missing",
        ),
        (
            lambda data: data["cases"][0]["mash_product_readfeel_axes"].update(
                {"not_bland": "fail"}
            ),
            "rr10_passed_case_mash_axis_not_passed",
        ),
        (
            lambda data: data["cases"][0].update(
                {"mash_result_was_derived_from_automatic_gate": True}
            ),
            "rr10_mash_result_automatic_derivation_forbidden",
        ),
        (
            lambda data: data["cases"][1].update(
                {"request_trace_sha256": data["cases"][0]["request_trace_sha256"]}
            ),
            "rr10_evidence_request_trace_reused",
        ),
        (
            lambda data: data["execution_environment"].update(
                {"deployed_source_snapshot_sha256": "0" * 64}
            ),
            "rr10_deployed_source_snapshot_mismatch",
        ),
        (
            lambda data: data["execution_summary"].update(
                {"progression_authority": "granted"}
            ),
            "rr10_progression_authority_must_remain_none",
        ),
        (
            lambda data: data["execution_summary"].update(
                {"rr11_exact8_actual_device_allowed": False}
            ),
            "rr10_rr11_evidence_collection_not_opened_after_4of4",
        ),
    ],
)
def test_rr10_validator_rejects_fabricated_or_incomplete_actual_device_pass(
    mutation,
    expected_issue: str,
) -> None:
    packet = _load(_EXPECTED_PACKET)
    synthetic = _synthetic_complete_pass()
    mutation(synthetic)

    assert expected_issue in _validate_device_evidence(synthetic, packet)


def test_rr10_readiness_receipt_is_body_free_hash_bound_and_not_progression() -> None:
    readiness = _load(_READINESS)
    packet = _load(_EXPECTED_PACKET)

    assert readiness["schema_version"] == (
        "cocolon.emlis.grounded_human_reception."
        "rr10_representative4_device_readiness.v1"
    )
    assert readiness["expected_packet_sha256"] == _sha256_file(_EXPECTED_PACKET)
    assert readiness["evidence_template_sha256"] == _sha256_file(_EVIDENCE_TEMPLATE)
    assert readiness["evidence_verifier_sha256"] == _sha256_file(_EVIDENCE_VERIFIER)
    assert readiness["source_snapshot_sha256"] == packet["source_snapshot_sha256"]
    assert readiness["representative_case_order"] == list(_REPRESENTATIVE4)
    assert readiness["rr8_technical_acceptance"] == "passed"
    assert readiness["rr9_karen_local_product_readfeel"] == "human_pass"
    assert readiness["actual_device_status"] == "not_run"
    assert readiness["actual_device_result_included"] is False
    assert readiness["next_required_owner"] == "mash_actual_device_operator"
    assert readiness["exact8_actual_device_allowed"] is False
    assert readiness["progression_authority"] == "none"
    assert readiness["valid_for_progression"] is False
    assert_body_free_metadata(readiness)
    keys = _all_mapping_keys(readiness)
    assert "visible_surface" not in keys
    assert "comment_text" not in keys
    assert "raw_input" not in keys
