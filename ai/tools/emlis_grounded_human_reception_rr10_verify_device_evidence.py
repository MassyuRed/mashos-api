#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""Verify RR10 evidence files against the immutable expected packet.

This verifier does not operate a device and cannot establish provenance by
itself.  It verifies the supplied bundle bytes: exact request payload, raw
backend comment text, body-free grounded-observation Gate meta and screenshots.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any, Mapping


_AI_ROOT = Path(__file__).resolve().parents[1]
_SERVICE_ROOT = _AI_ROOT / "services" / "ai_inference"
if str(_SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(_SERVICE_ROOT))

from emlis_ai_grounded_sentence_surface import (  # noqa: E402
    split_two_stage_surface,
)


_SHA_FIELDS = (
    "selection_screenshot_sha256",
    "request_payload_sha256",
    "backend_response_sha256",
    "raw_comment_text_sha256",
    "backend_gate_meta_sha256",
)
_OBSERVED_GATE_FIELDS = {
    "observed_depth_level": "reception_depth_level",
    "observed_opportunity_count": "reception_opportunity_count",
    "observed_planned_move_count": "reception_planned_move_count",
    "observed_realized_move_count": "reception_realized_move_count",
    "observed_sentence_count": "reception_sentence_count",
}
_EXPECTED_OBSERVED_FIELDS = {
    "observed_current_input_sha256": "current_input_sha256",
    "observed_visible_surface_sha256": "expected_visible_surface_sha256",
    "observed_observation_section_sha256": "expected_observation_section_sha256",
    "observed_reception_section_sha256": "expected_reception_section_sha256",
    "observed_depth_level": "expected_depth_level",
    "observed_opportunity_count": "expected_opportunity_count",
    "observed_planned_move_count": "expected_planned_move_count",
    "observed_realized_move_count": "expected_realized_move_count",
    "observed_sentence_count": "expected_sentence_count",
}
_ALLOWED_SCREENSHOT_ROLES = frozenset(
    {"modal_full", "modal_top", "modal_middle", "modal_bottom"}
)
_DEVICE_PASS_FIELDS = (
    "backend_gate_contract",
    "two_stage_display",
    "observation_regression",
    "depth_target",
    "clipping",
    "overlap",
    "scroll",
    "safety_boundary",
)
_MASH_AXES = (
    "not_bland",
    "sufficient_stay_with_long_input",
    "non_enumerative",
    "non_repetitive_language_and_skeleton",
    "natural_as_emlis_response",
    "short_input_not_water_filled",
)
_BODY_FREE_CODE_RE = re.compile(r"^[A-Za-z0-9_.:/-]*$")
_FORBIDDEN_BODY_KEYS = frozenset(
    {
        "raw_input",
        "raw_text",
        "source_text",
        "comment_text",
        "surface_text",
        "candidate_body",
        "visible_surface",
        "observation_text",
        "reception_text",
        "anchor_text",
        "sentence_text",
    }
)


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return _sha256_bytes(value.encode("utf-8"))


def _sha256_json(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return _sha256_text(payload)


def _resolve_bundle_ref(bundle_root: Path, value: Any) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    relative = Path(value)
    if relative.is_absolute():
        return None
    root = bundle_root.resolve()
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return candidate


def _gate_meta_is_body_free(value: Any) -> bool:
    if isinstance(value, dict):
        for raw_key, nested in value.items():
            key = str(raw_key or "")
            if not _BODY_FREE_CODE_RE.fullmatch(key):
                return False
            if key in _FORBIDDEN_BODY_KEYS:
                return False
            if key.endswith("_included") and nested is not False:
                return False
            if not _gate_meta_is_body_free(nested):
                return False
        return True
    if isinstance(value, list):
        return all(_gate_meta_is_body_free(item) for item in value)
    if isinstance(value, str):
        return bool(_BODY_FREE_CODE_RE.fullmatch(value))
    return value is None or isinstance(value, (bool, int, float))


def _read_evidence_file(
    *,
    bundle_root: Path,
    ref: Any,
    issue_prefix: str,
    issues: list[str],
) -> tuple[Path | None, bytes | None]:
    path = _resolve_bundle_ref(bundle_root, ref)
    if path is None:
        issues.append(f"{issue_prefix}_ref_unsafe_or_missing")
        return None, None
    if not path.is_file():
        issues.append(f"{issue_prefix}_file_missing")
        return path, None
    return path, path.read_bytes()


def validate_rr10_device_evidence_bundle(
    *,
    expected_packet: Mapping[str, Any],
    evidence: Mapping[str, Any],
    bundle_root: Path,
    expected_packet_sha256: str | None = None,
) -> tuple[str, ...]:
    """Return body-free issue codes for referenced evidence bytes."""

    issues: list[str] = []
    if evidence.get("schema_version") != (
        "cocolon.emlis.grounded_human_reception."
        "rr10_actual_device_evidence.local_only.v1"
    ):
        issues.append("rr10_bundle_evidence_schema_version_mismatch")
    if evidence.get("local_only") is not True:
        issues.append("rr10_bundle_evidence_local_only_missing")
    if expected_packet_sha256 is not None and evidence.get(
        "expected_packet_sha256"
    ) != expected_packet_sha256:
        issues.append("rr10_bundle_expected_packet_hash_mismatch")
    expected_order = list(expected_packet.get("representative_case_order", ()))
    if evidence.get("representative_case_order") != expected_order:
        issues.append("rr10_bundle_case_order_mismatch")
    expected_by_id = {
        row.get("case_id"): row
        for row in expected_packet.get("cases", [])
        if isinstance(row, dict) and row.get("case_id")
    }
    required_gates = tuple(expected_packet.get("required_reception_gate_fields", ()))
    required_guards = tuple(expected_packet.get("required_runtime_guard_fields", ()))
    rows = evidence.get("cases")
    if not isinstance(rows, list):
        return tuple(dict.fromkeys((*issues, "rr10_bundle_cases_missing")))
    executed_rows = [
        row
        for row in rows
        if isinstance(row, dict)
        and row.get("status") in {"passed", "failed", "blocked"}
    ]
    if not executed_rows:
        return ("rr10_actual_device_not_executed",)

    statuses = [
        row.get("status") if isinstance(row, dict) else "invalid" for row in rows
    ]
    if len(rows) != 4 or [
        row.get("case_id") if isinstance(row, dict) else None for row in rows
    ] != expected_order:
        issues.append("rr10_bundle_case_identity_or_count_mismatch")

    summary = evidence.get("execution_summary")
    if not isinstance(summary, dict):
        issues.append("rr10_bundle_summary_missing")
        summary = {}
    if summary.get("progression_authority") != "none":
        issues.append("rr10_bundle_progression_authority_invalid")
    for field in (
        "p5_formal_24_start_allowed",
        "p6_start_allowed",
        "p8_start_allowed",
        "valid_for_progression",
    ):
        if summary.get(field) is not False:
            issues.append(f"rr10_bundle_{field}_must_remain_false")
    if statuses == ["passed"] * 4:
        if summary.get("actual_device_execution_status") != "passed":
            issues.append("rr10_bundle_passed_summary_status_invalid")
        if summary.get("passed_case_count") != 4 or summary.get(
            "failed_case_count"
        ) != 0:
            issues.append("rr10_bundle_passed_summary_count_invalid")
        if summary.get("rr11_exact8_actual_device_allowed") is not True:
            issues.append("rr10_bundle_rr11_not_opened_after_4of4")
    elif statuses.count("failed") == 1:
        failed_index = statuses.index("failed")
        expected_statuses = ["passed"] * failed_index + ["failed"] + [
            "not_run"
        ] * (3 - failed_index)
        if statuses != expected_statuses:
            issues.append("rr10_bundle_execution_continued_after_failure")
        if summary.get("actual_device_execution_status") != "failed":
            issues.append("rr10_bundle_failed_summary_status_invalid")
        if summary.get("passed_case_count") != failed_index or summary.get(
            "failed_case_count"
        ) != 1:
            issues.append("rr10_bundle_failed_summary_count_invalid")
        if summary.get("first_failed_case_id") != expected_order[failed_index]:
            issues.append("rr10_bundle_first_failed_case_invalid")
        if summary.get("rr11_exact8_actual_device_allowed") is not False:
            issues.append("rr10_bundle_rr11_opened_after_failure")
    elif statuses.count("blocked") == 1:
        blocked_index = statuses.index("blocked")
        expected_statuses = ["passed"] * blocked_index + ["blocked"] + [
            "not_run"
        ] * (3 - blocked_index)
        if statuses != expected_statuses:
            issues.append("rr10_bundle_execution_continued_after_block")
        if summary.get("actual_device_execution_status") != "blocked":
            issues.append("rr10_bundle_blocked_summary_status_invalid")
        if summary.get("passed_case_count") != blocked_index or summary.get(
            "failed_case_count"
        ) != 1:
            issues.append("rr10_bundle_blocked_summary_count_invalid")
        if summary.get("first_failed_case_id") != expected_order[blocked_index]:
            issues.append("rr10_bundle_first_blocked_case_invalid")
        if summary.get("rr11_exact8_actual_device_allowed") is not False:
            issues.append("rr10_bundle_rr11_opened_after_block")
    else:
        issues.append("rr10_bundle_execution_status_pattern_invalid")

    environment = evidence.get("execution_environment")
    required_environment_fields = (
        "executed_at_jst",
        "app_build_identity",
        "deployment_identity",
        "device_model",
        "os_version",
        "app_version",
    )
    if not isinstance(environment, dict) or any(
        not isinstance(environment.get(field), str)
        or not str(environment.get(field)).strip()
        for field in required_environment_fields
    ):
        issues.append("rr10_bundle_execution_environment_incomplete")
    elif environment.get("deployed_source_snapshot_sha256") != expected_packet.get(
        "source_snapshot_sha256"
    ):
        issues.append("rr10_bundle_deployed_source_snapshot_mismatch")

    traces = [
        row.get("request_trace_sha256")
        for row in executed_rows
        if isinstance(row, dict)
    ]
    if any(
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
        for value in traces
    ):
        issues.append("rr10_bundle_request_trace_invalid")
    if len(traces) != len(set(traces)):
        issues.append("rr10_bundle_request_trace_reused")

    for row in executed_rows:
        case_id = row.get("case_id")
        expected = expected_by_id.get(case_id)
        prefix = f"rr10_{case_id or 'unknown'}"
        if expected is None:
            issues.append("rr10_bundle_unknown_case_id")
            continue
        if row.get("status") in {"passed", "failed"} and row.get(
            "hash_source"
        ) != "backend_input_feedback_comment_text_utf8":
            issues.append(f"{prefix}_hash_source_invalid")
        if row.get("mash_result_was_derived_from_automatic_gate") is not False:
            issues.append(f"{prefix}_mash_result_automatic_derivation_forbidden")
        if row.get("status") == "passed":
            if row.get("exact_current_input_identity") != "matched":
                issues.append(f"{prefix}_input_identity_not_matched")
            if any(row.get(field) != "pass" for field in _DEVICE_PASS_FIELDS):
                issues.append(f"{prefix}_device_axis_not_passed")
            axes = row.get("mash_product_readfeel_axes")
            if not isinstance(axes, dict) or set(axes) != set(_MASH_AXES) or set(
                axes.values()
            ) != {"pass"}:
                issues.append(f"{prefix}_mash_axes_not_passed")
            if row.get("mash_product_readfeel") != "pass":
                issues.append(f"{prefix}_mash_result_not_passed")
            if row.get("mismatch_codes") != []:
                issues.append(f"{prefix}_passed_case_has_mismatch")
            if row.get("failure_stage") is not None:
                issues.append(f"{prefix}_passed_case_failure_stage_invalid")
            if row.get("observed_selection_order") != expected.get(
                "selection_order"
            ):
                issues.append(f"{prefix}_selection_order_mismatch")
        elif row.get("status") == "failed":
            if not isinstance(row.get("mismatch_codes"), list) or not row.get(
                "mismatch_codes"
            ):
                issues.append(f"{prefix}_failed_case_mismatch_code_missing")
            if row.get("failure_stage") not in {
                "input_identity",
                "backend_contract",
                "visible_surface",
                "display",
                "product_readfeel",
            }:
                issues.append(f"{prefix}_failed_case_failure_stage_invalid")
            if any(
                row.get(field) not in {"pass", "fail"}
                for field in _DEVICE_PASS_FIELDS
            ):
                issues.append(f"{prefix}_failed_case_device_axis_not_evaluated")
            axes = row.get("mash_product_readfeel_axes")
            if (
                not isinstance(axes, dict)
                or set(axes) != set(_MASH_AXES)
                or any(value not in {"pass", "fail"} for value in axes.values())
            ):
                issues.append(f"{prefix}_failed_case_mash_axes_not_evaluated")
            if row.get("mash_product_readfeel") not in {"pass", "fail"}:
                issues.append(f"{prefix}_failed_case_mash_result_not_evaluated")
            failure_recorded = (
                row.get("exact_current_input_identity") == "mismatch"
                or any(row.get(field) == "fail" for field in _DEVICE_PASS_FIELDS)
                or isinstance(axes, dict)
                and any(value == "fail" for value in axes.values())
                or row.get("mash_product_readfeel") == "fail"
                or any(
                    row.get(actual_field) != expected.get(expected_field)
                    for actual_field, expected_field in _EXPECTED_OBSERVED_FIELDS.items()
                )
            )
            if not failure_recorded:
                issues.append(f"{prefix}_failed_case_has_no_recorded_failure")
        elif row.get("status") == "blocked":
            if row.get("failure_stage") not in {
                "input_identity",
                "submission",
                "backend_response_unavailable",
            }:
                issues.append(f"{prefix}_blocked_case_failure_stage_invalid")
            if not isinstance(row.get("mismatch_codes"), list) or not row.get(
                "mismatch_codes"
            ):
                issues.append(f"{prefix}_blocked_case_mismatch_code_missing")
            if row.get("observed_selection_order") != expected.get(
                "selection_order"
            ):
                issues.append(f"{prefix}_blocked_selection_order_mismatch")

        required_sha_fields = (
            ("selection_screenshot_sha256", "request_payload_sha256")
            if row.get("status") == "blocked"
            else _SHA_FIELDS
        )
        for field in required_sha_fields:
            value = row.get(field)
            if not isinstance(value, str) or len(value) != 64:
                issues.append(f"{prefix}_{field}_invalid")

        _selection_path, selection_bytes = _read_evidence_file(
            bundle_root=bundle_root,
            ref=row.get("selection_screenshot_ref"),
            issue_prefix=f"{prefix}_selection_screenshot",
            issues=issues,
        )
        if selection_bytes is not None and _sha256_bytes(
            selection_bytes
        ) != row.get("selection_screenshot_sha256"):
            issues.append(f"{prefix}_selection_screenshot_file_hash_mismatch")

        _request_path, request_bytes = _read_evidence_file(
            bundle_root=bundle_root,
            ref=row.get("request_payload_ref"),
            issue_prefix=f"{prefix}_request_payload",
            issues=issues,
        )
        if request_bytes is not None:
            request_file_sha = _sha256_bytes(request_bytes)
            if request_file_sha != row.get("request_payload_sha256"):
                issues.append(f"{prefix}_request_payload_file_hash_mismatch")
            try:
                request_payload = json.loads(request_bytes.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                issues.append(f"{prefix}_request_payload_json_invalid")
            else:
                observed_input_sha = _sha256_json(request_payload)
                if observed_input_sha != row.get("observed_current_input_sha256"):
                    issues.append(f"{prefix}_observed_input_hash_not_reproducible")
                if row.get("status") == "passed" and observed_input_sha != expected.get(
                    "current_input_sha256"
                ):
                    issues.append(f"{prefix}_expected_input_hash_mismatch")

        if row.get("status") == "blocked":
            continue

        comment_text_value: str | None = None
        _comment_path, comment_bytes = _read_evidence_file(
            bundle_root=bundle_root,
            ref=row.get("raw_comment_text_ref"),
            issue_prefix=f"{prefix}_raw_comment",
            issues=issues,
        )
        if comment_bytes is not None:
            comment_sha = _sha256_bytes(comment_bytes)
            if comment_sha != row.get("raw_comment_text_sha256"):
                issues.append(f"{prefix}_raw_comment_file_hash_mismatch")
            if comment_sha != row.get("observed_visible_surface_sha256"):
                issues.append(f"{prefix}_visible_hash_not_raw_body_hash")
            try:
                comment_text = comment_bytes.decode("utf-8")
            except UnicodeDecodeError:
                issues.append(f"{prefix}_raw_comment_not_utf8")
            else:
                comment_text_value = comment_text
                observation, reception, split_issues = split_two_stage_surface(
                    comment_text
                )
                if split_issues and row.get("status") == "passed":
                    issues.append(f"{prefix}_two_stage_split_invalid")
                if _sha256_text(observation.strip()) != row.get(
                    "observed_observation_section_sha256"
                ):
                    issues.append(f"{prefix}_observation_hash_not_reproducible")
                if _sha256_text(reception.strip()) != row.get(
                    "observed_reception_section_sha256"
                ):
                    issues.append(f"{prefix}_reception_hash_not_reproducible")

        _response_path, response_bytes = _read_evidence_file(
            bundle_root=bundle_root,
            ref=row.get("backend_response_ref"),
            issue_prefix=f"{prefix}_backend_response",
            issues=issues,
        )
        if response_bytes is not None:
            if _sha256_bytes(response_bytes) != row.get("backend_response_sha256"):
                issues.append(f"{prefix}_backend_response_file_hash_mismatch")
            try:
                response = json.loads(response_bytes.decode("utf-8"))
                feedback = response["input_feedback"]
                response_comment = feedback["comment_text"]
                response_status = feedback["emlis_ai"]["observation_status"]
            except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError):
                issues.append(f"{prefix}_backend_response_contract_invalid")
            else:
                if response_status != "passed" and row.get("status") == "passed":
                    issues.append(f"{prefix}_backend_observation_status_not_passed")
                if comment_text_value is None or response_comment != comment_text_value:
                    issues.append(f"{prefix}_raw_comment_not_bound_to_backend_response")

        _gate_path, gate_bytes = _read_evidence_file(
            bundle_root=bundle_root,
            ref=row.get("backend_gate_meta_ref"),
            issue_prefix=f"{prefix}_gate_meta",
            issues=issues,
        )
        if gate_bytes is not None:
            if _sha256_bytes(gate_bytes) != row.get("backend_gate_meta_sha256"):
                issues.append(f"{prefix}_gate_meta_file_hash_mismatch")
            try:
                gate_meta = json.loads(gate_bytes.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                issues.append(f"{prefix}_gate_meta_json_invalid")
            else:
                if not isinstance(gate_meta, dict):
                    issues.append(f"{prefix}_gate_meta_not_object")
                else:
                    if not _gate_meta_is_body_free(gate_meta):
                        issues.append(f"{prefix}_gate_meta_body_leak")
                    all_required_passed = all(
                        gate_meta.get(field) == "passed"
                        for field in (*required_gates, *required_guards)
                    )
                    computed_contract = "pass" if all_required_passed else "fail"
                    if row.get("backend_gate_contract") != computed_contract:
                        issues.append(f"{prefix}_gate_contract_not_reproducible")
                    for evidence_field, gate_field in _OBSERVED_GATE_FIELDS.items():
                        if row.get(evidence_field) != gate_meta.get(gate_field):
                            issues.append(f"{prefix}_{evidence_field}_not_gate_bound")

        screenshots = row.get("screenshot_evidence")
        if isinstance(screenshots, list):
            roles: list[str] = []
            for index, item in enumerate(screenshots):
                if not isinstance(item, dict):
                    issues.append(f"{prefix}_screenshot_{index}_schema_invalid")
                    continue
                role = str(item.get("capture_role") or "")
                roles.append(role)
                if role not in _ALLOWED_SCREENSHOT_ROLES:
                    issues.append(f"{prefix}_screenshot_role_invalid")
                _screen_path, screen_bytes = _read_evidence_file(
                    bundle_root=bundle_root,
                    ref=item.get("ref"),
                    issue_prefix=f"{prefix}_screenshot_{index}",
                    issues=issues,
                )
                if screen_bytes is not None and _sha256_bytes(screen_bytes) != item.get(
                    "sha256"
                ):
                    issues.append(f"{prefix}_screenshot_{index}_file_hash_mismatch")
            if len(roles) != len(set(roles)):
                issues.append(f"{prefix}_screenshot_role_duplicate")
            required_roles = (
                {"modal_top", "modal_bottom"}
                if case_id in {"B", "I6-L03"}
                else {"modal_full"}
            )
            if not required_roles.issubset(set(roles)):
                issues.append(f"{prefix}_required_screenshot_roles_missing")

        if row.get("status") == "passed":
            for actual_field, expected_field in _EXPECTED_OBSERVED_FIELDS.items():
                if row.get(actual_field) != expected.get(expected_field):
                    issues.append(f"{prefix}_{actual_field}_expected_mismatch")

    return tuple(dict.fromkeys(issues))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify RR10 representative4 evidence bundle bytes."
    )
    parser.add_argument("expected_packet", type=Path)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("bundle_root", type=Path)
    args = parser.parse_args()

    issues = validate_rr10_device_evidence_bundle(
        expected_packet=_load(args.expected_packet),
        evidence=_load(args.evidence),
        bundle_root=args.bundle_root,
        expected_packet_sha256=_sha256_bytes(args.expected_packet.read_bytes()),
    )
    print(
        json.dumps(
            {"status": "passed" if not issues else "failed", "issues": issues},
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
