# -*- coding: utf-8 -*-
from __future__ import annotations

"""R7 representative4 actual-device direction-check readiness contract.

This file deliberately does not claim actual-device completion.  It freezes the
four exact inputs and expected visible surfaces after R0-R6, verifies the
current runtime path, and keeps progression closed until Mash supplies real
screenshots, body-free gate meta and product-readfeel results.
"""

import asyncio
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping

from emlis_ai_grounded_observation_gate import RECEPTION_GATE_REPORT_FIELDS
from emlis_ai_grounded_sentence_surface import split_two_stage_surface
from emlis_ai_reply_service import render_emlis_ai_reply


_TEST_ROOT = Path(__file__).resolve().parent
_BACKEND_ROOT = _TEST_ROOT.parents[1]
_EXACT8_FIXTURE = (
    _TEST_ROOT / "fixtures" / "grounded_human_reception_exact8_v2_20260712.json"
)
_R6_VISIBLE_PACKET = (
    _TEST_ROOT
    / "local_only"
    / "grounded_human_reception_r6_exact8_visible_packet_20260712.json"
)
_R6_KAREN_RECEIPT = (
    _TEST_ROOT
    / "fixtures"
    / "grounded_human_reception_r6_karen_review_receipt_20260712.json"
)
_R6_LOCAL_QA_RECEIPT = (
    _TEST_ROOT
    / "fixtures"
    / "grounded_human_reception_r6_local_qa_receipt_20260712.json"
)
_R7_DEVICE_PACKET = (
    _TEST_ROOT
    / "local_only"
    / "grounded_human_reception_r7_representative4_device_packet_20260712.json"
)
_R7_READINESS_RECEIPT = (
    _TEST_ROOT
    / "fixtures"
    / "grounded_human_reception_r7_representative4_device_readiness_20260712.json"
)
_SOURCE_SNAPSHOT_FILES = (
    "ai/services/ai_inference/emlis_ai_grounded_observation_plan.py",
    "ai/services/ai_inference/emlis_ai_grounded_human_reception.py",
    "ai/services/ai_inference/emlis_ai_grounded_sentence_surface.py",
    "ai/services/ai_inference/emlis_ai_grounded_observation_gate.py",
    "ai/services/ai_inference/emlis_ai_reply_service.py",
)
_REPRESENTATIVE4 = ("A", "B", "I6-S03", "I6-D02")
_RUNTIME_GUARD_FIELDS = (
    "runtime_visible_contract_guard",
    "runtime_reception_contract_guard",
    "runtime_gate_meta_body_free_guard",
    "runtime_final_contract_guard",
)
_READINESS_ALLOWED_KEYS = frozenset(
    {
        "schema_version",
        "created_date",
        "design_stage",
        "readiness_status",
        "actual_device_status",
        "source_snapshot_sha256",
        "source_snapshot_files",
        "exact8_fixture_ref",
        "exact8_fixture_sha256",
        "r6_visible_packet_ref",
        "r6_visible_packet_sha256",
        "r6_karen_review_receipt_ref",
        "r6_karen_review_receipt_sha256",
        "r6_local_qa_receipt_ref",
        "r6_local_qa_receipt_sha256",
        "representative4_device_packet_ref",
        "representative4_device_packet_sha256",
        "r0_through_r6_technical_acceptance",
        "r6_karen_local_product_readfeel",
        "representative_case_order",
        "cases",
        "required_reception_gate_fields",
        "required_runtime_guard_fields",
        "required_actual_device_evidence_fields",
        "actual_device_result_included",
        "raw_input_included",
        "surface_body_included",
        "comment_text_included",
        "anchor_text_included",
        "sentence_text_included",
        "screenshot_included",
        "backend_gate_meta_body_included",
        "next_required_owner",
        "progression_authority",
        "valid_for_progression",
        "exact8_actual_device_allowed",
        "p5_start_allowed",
        "p6_start_allowed",
        "p8_start_allowed",
        "local_execution",
    }
)
_READINESS_CASE_ALLOWED_KEYS = frozenset(
    {
        "case_id",
        "current_input_sha256",
        "expected_visible_surface_sha256",
        "expected_observation_section_sha256",
        "expected_reception_section_sha256",
        "reception_act",
        "reception_stance",
        "reception_reference_mode",
        "reception_terminal_predicate_kind",
        "reception_sentence_count",
    }
)
_FORBIDDEN_BODY_KEYS = frozenset(
    {
        "raw_input",
        "exact_current_input",
        "memo",
        "memo_action",
        "visible_surface",
        "surface_body",
        "comment_text",
        "anchor_text",
        "sentence_text",
        "screenshot",
        "backend_gate_meta",
    }
)
_BODY_FLAGS = frozenset(
    {
        "actual_device_result_included",
        "raw_input_included",
        "surface_body_included",
        "comment_text_included",
        "anchor_text_included",
        "sentence_text_included",
        "screenshot_included",
        "backend_gate_meta_body_included",
    }
)
_BODY_FREE_VALUE_RE = re.compile(r"^[A-Za-z0-9_.:/-]*$")


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()


def _canonical_input_sha256(current_input: Mapping[str, Any]) -> str:
    payload = json.dumps(
        current_input,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return _sha256_text(payload)


def _source_manifest() -> list[dict[str, str]]:
    return [
        {
            "path": relative_path,
            "sha256": _sha256_file(_BACKEND_ROOT / relative_path),
        }
        for relative_path in _SOURCE_SNAPSHOT_FILES
    ]


def _source_snapshot_sha256() -> str:
    payload = json.dumps(
        _source_manifest(),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return _sha256_text(payload)


def _is_body_free(value: Any) -> bool:
    if isinstance(value, dict):
        for raw_key, nested in value.items():
            key = str(raw_key or "")
            if not _BODY_FREE_VALUE_RE.fullmatch(key):
                return False
            if key in _FORBIDDEN_BODY_KEYS:
                return False
            if key in _BODY_FLAGS and nested is not False:
                return False
            if not _is_body_free(nested):
                return False
        return True
    if isinstance(value, (list, tuple)):
        return all(_is_body_free(item) for item in value)
    if isinstance(value, str):
        return bool(_BODY_FREE_VALUE_RE.fullmatch(value))
    return value is None or isinstance(value, (bool, int, float))


def _validate_readiness_receipt(receipt: Mapping[str, Any]) -> tuple[str, ...]:
    issues: list[str] = []
    if set(receipt) != _READINESS_ALLOWED_KEYS:
        issues.append("r7_readiness_top_level_schema_mismatch")
    if receipt.get("schema_version") != (
        "cocolon.emlis.grounded_human_reception."
        "r7_representative4_device_readiness.v1"
    ):
        issues.append("r7_readiness_schema_version_mismatch")
    if receipt.get("readiness_status") != (
        "ready_for_mash_actual_device_execution"
    ):
        issues.append("r7_readiness_status_invalid")
    if receipt.get("actual_device_status") != "not_run":
        issues.append("r7_actual_device_status_must_remain_not_run")
    if receipt.get("progression_authority") != "none":
        issues.append("r7_progression_authority_must_remain_none")
    if receipt.get("valid_for_progression") is not False:
        issues.append("r7_progression_must_remain_closed")
    for field_name in (
        "exact8_actual_device_allowed",
        "p5_start_allowed",
        "p6_start_allowed",
        "p8_start_allowed",
    ):
        if receipt.get(field_name) is not False:
            issues.append(f"r7_{field_name}_must_remain_false")
    if receipt.get("actual_device_result_included") is not False:
        issues.append("r7_actual_device_result_must_not_be_claimed")
    if not _is_body_free(receipt):
        issues.append("r7_readiness_receipt_body_leak")

    cases = receipt.get("cases")
    if not isinstance(cases, list) or len(cases) != len(_REPRESENTATIVE4):
        issues.append("r7_readiness_case_count_mismatch")
        cases = []
    case_ids = [row.get("case_id") for row in cases if isinstance(row, dict)]
    if case_ids != list(_REPRESENTATIVE4):
        issues.append("r7_readiness_case_order_mismatch")
    for row in cases:
        if not isinstance(row, dict) or set(row) != _READINESS_CASE_ALLOWED_KEYS:
            issues.append("r7_readiness_case_schema_mismatch")
            break
    return tuple(dict.fromkeys(issues))


def _validate_unexecuted_device_packet(packet: Mapping[str, Any]) -> tuple[str, ...]:
    issues: list[str] = []
    if packet.get("schema_version") != (
        "cocolon.emlis.grounded_human_reception."
        "r7_representative4_device_packet.local_only.v1"
    ):
        issues.append("r7_device_packet_schema_version_mismatch")
    if packet.get("local_only") is not True:
        issues.append("r7_device_packet_must_remain_local_only")
    if packet.get("actual_device_execution_status") != "not_run":
        issues.append("r7_device_packet_execution_status_invalid")
    if packet.get("progression_authority") != "none":
        issues.append("r7_device_packet_progression_authority_invalid")
    if packet.get("valid_for_progression") is not False:
        issues.append("r7_device_packet_progression_must_remain_closed")
    if packet.get("representative_case_order") != list(_REPRESENTATIVE4):
        issues.append("r7_device_packet_case_order_mismatch")

    cases = packet.get("cases")
    if not isinstance(cases, list) or len(cases) != len(_REPRESENTATIVE4):
        issues.append("r7_device_packet_case_count_mismatch")
        cases = []
    case_ids = [row.get("case_id") for row in cases if isinstance(row, dict)]
    if case_ids != list(_REPRESENTATIVE4):
        issues.append("r7_device_packet_case_id_mismatch")
    for row in cases:
        result = row.get("actual_device_result") if isinstance(row, dict) else None
        if not isinstance(result, dict):
            issues.append("r7_device_result_placeholder_missing")
            continue
        if result.get("status") != "not_run":
            issues.append("r7_device_result_must_remain_not_run")
        if result.get("screenshot_refs") != []:
            issues.append("r7_screenshot_evidence_cannot_be_preclaimed")
        if result.get("backend_gate_meta_ref") is not None:
            issues.append("r7_backend_meta_evidence_cannot_be_preclaimed")
        for field_name in (
            "visible_surface_sha256",
            "observation_section_sha256",
            "reception_section_sha256",
        ):
            if result.get(field_name) is not None:
                issues.append("r7_actual_hash_evidence_cannot_be_preclaimed")
                break
        for field_name in (
            "clipping_or_layout",
            "two_stage_display",
            "observation_regression",
            "reception_role_distinctness",
            "generic_template_readfeel",
            "safety_boundary",
            "mash_product_readfeel",
        ):
            if result.get(field_name) != "not_evaluated":
                issues.append("r7_human_or_device_result_cannot_be_preclaimed")
                break
    return tuple(dict.fromkeys(issues))


def test_r7_r0_through_r6_prerequisites_are_hash_bound_and_passed() -> None:
    readiness = _load(_R7_READINESS_RECEIPT)
    r6_qa = _load(_R6_LOCAL_QA_RECEIPT)
    r6_review = _load(_R6_KAREN_RECEIPT)

    assert r6_qa["technical_acceptance"] == "passed"
    assert set(r6_qa["automated_qa_order_status"].values()) == {"passed"}
    assert r6_qa["representative4_actual_device_status"] == "not_run"
    assert r6_qa["valid_for_progression"] is False
    assert r6_review["product_readfeel_status"] == "human_pass"
    assert r6_review["representative4_actual_device_status"] == "not_run"
    assert r6_review["valid_for_progression"] is False

    assert readiness["r0_through_r6_technical_acceptance"] == "passed"
    assert readiness["r6_karen_local_product_readfeel"] == "human_pass"
    assert readiness["exact8_fixture_sha256"] == _sha256_file(_EXACT8_FIXTURE)
    assert readiness["r6_visible_packet_sha256"] == _sha256_file(
        _R6_VISIBLE_PACKET
    )
    assert readiness["r6_karen_review_receipt_sha256"] == _sha256_file(
        _R6_KAREN_RECEIPT
    )
    assert readiness["r6_local_qa_receipt_sha256"] == _sha256_file(
        _R6_LOCAL_QA_RECEIPT
    )
    assert readiness["representative4_device_packet_sha256"] == _sha256_file(
        _R7_DEVICE_PACKET
    )
    assert readiness["source_snapshot_files"] == _source_manifest()
    assert readiness["source_snapshot_sha256"] == _source_snapshot_sha256()
    assert readiness["local_execution"] == {
        "r0_through_r7_contract_test_count": 72,
        "r0_through_r7_contract_test_file_count": 8,
        "relevant_backend_regression_test_count": 342,
        "relevant_backend_regression_test_file_count": 22,
        "subtest_pass_count": 41,
        "failed_test_count": 0,
        "warning_count": 1,
        "warning_ref": "existing_pydantic_v1_root_validator_deprecation",
    }


def test_r7_representative4_packet_matches_current_canonical_runtime() -> None:
    fixture = _load(_EXACT8_FIXTURE)
    r6_packet = _load(_R6_VISIBLE_PACKET)
    r7_packet = _load(_R7_DEVICE_PACKET)
    readiness = _load(_R7_READINESS_RECEIPT)
    fixture_by_id = {row["case_id"]: row for row in fixture["cases"]}
    r6_by_id = {row["case_id"]: row for row in r6_packet["cases"]}
    readiness_by_id = {row["case_id"]: row for row in readiness["cases"]}

    assert r7_packet["source_snapshot_sha256"] == _source_snapshot_sha256()
    assert r7_packet["source_fixture_sha256"] == _sha256_file(_EXACT8_FIXTURE)
    assert r7_packet["r6_visible_packet_sha256"] == _sha256_file(
        _R6_VISIBLE_PACKET
    )
    assert r7_packet["representative_case_order"] == list(_REPRESENTATIVE4)

    for packet_row in r7_packet["cases"]:
        case_id = packet_row["case_id"]
        source_case = fixture_by_id[case_id]
        current_input = source_case["exact_current_input"]
        expected = packet_row["expected_local_result"]
        reply = asyncio.run(
            render_emlis_ai_reply(
                user_id=f"r7-representative4-{case_id}",
                subscription_tier="free",
                current_input=current_input,
            )
        )
        observation, reception, issues = split_two_stage_surface(
            reply.comment_text
        )
        assert issues == ()

        assert packet_row["exact_current_input"] == current_input
        assert packet_row["current_input_sha256"] == _canonical_input_sha256(
            current_input
        )
        assert expected["visible_surface"] == reply.comment_text
        assert expected["visible_surface"] == r6_by_id[case_id]["visible_surface"]
        assert expected["visible_surface_sha256"] == _sha256_text(
            reply.comment_text
        )
        assert expected["observation_section_sha256"] == _sha256_text(
            observation
        )
        assert expected["reception_section_sha256"] == _sha256_text(reception)

        gate_meta = reply.meta["grounded_observation"]
        common = expected["body_free_gate_expectations"]
        for field_name, expected_value in common.items():
            if field_name == "composer_source":
                assert reply.meta[field_name] == expected_value
            elif field_name == "generation_path":
                assert reply.meta[field_name] == expected_value
            elif field_name == "product_readfeel_status":
                assert gate_meta[field_name] == expected_value
            else:
                assert gate_meta[field_name] == expected_value
        assert gate_meta["reception_act"] == expected["reception_act"]
        assert gate_meta["reception_stance"] == expected["reception_stance"]
        assert gate_meta["reception_reference_mode"] == expected[
            "reception_reference_mode"
        ]
        assert gate_meta["reception_terminal_predicate_kind"] == expected[
            "reception_terminal_predicate_kind"
        ]
        assert gate_meta["reception_sentence_count"] == expected[
            "reception_sentence_count"
        ]
        assert gate_meta["reception_all_gates_passed"] is True
        assert gate_meta["repeated_long_anchor_count"] == 0
        assert reply.meta["public_contract_changed"] is False
        assert reply.meta["api_route_changed"] is False
        assert reply.meta["db_physical_name_changed"] is False
        assert reply.meta["rn_visible_contract_changed"] is False

        receipt_row = readiness_by_id[case_id]
        assert receipt_row["current_input_sha256"] == packet_row[
            "current_input_sha256"
        ]
        assert receipt_row["expected_visible_surface_sha256"] == expected[
            "visible_surface_sha256"
        ]
        assert receipt_row["expected_observation_section_sha256"] == expected[
            "observation_section_sha256"
        ]
        assert receipt_row["expected_reception_section_sha256"] == expected[
            "reception_section_sha256"
        ]


def test_r7_readiness_receipt_is_body_free_and_progression_closed() -> None:
    readiness = _load(_R7_READINESS_RECEIPT)

    assert _validate_readiness_receipt(readiness) == ()
    assert readiness["representative_case_order"] == list(_REPRESENTATIVE4)
    assert readiness["required_reception_gate_fields"] == list(
        RECEPTION_GATE_REPORT_FIELDS
    )
    assert readiness["required_runtime_guard_fields"] == list(
        _RUNTIME_GUARD_FIELDS
    )
    assert readiness["next_required_owner"] == "mash_actual_device_operator"
    assert readiness["actual_device_status"] == "not_run"
    assert readiness["actual_device_result_included"] is False
    assert readiness["progression_authority"] == "none"
    assert readiness["valid_for_progression"] is False
    assert readiness["exact8_actual_device_allowed"] is False
    assert readiness["p5_start_allowed"] is False
    assert readiness["p6_start_allowed"] is False
    assert readiness["p8_start_allowed"] is False


def test_r7_device_packet_does_not_preclaim_real_device_or_human_evidence() -> None:
    packet = _load(_R7_DEVICE_PACKET)

    assert _validate_unexecuted_device_packet(packet) == ()
    assert packet["actual_device_execution_status"] == "not_run"
    assert packet["progression_authority"] == "none"
    assert packet["valid_for_progression"] is False
    assert packet["stop_rule"] == {
        "do_not_start_exact8_actual_device_after_failure": True,
        "do_not_start_p5_p6_p8": True,
        "stop_on_first_failed_case": True,
    }


def test_r7_contract_rejects_fabricated_pass_without_device_evidence() -> None:
    readiness = deepcopy(_load(_R7_READINESS_RECEIPT))
    readiness["actual_device_status"] = "passed"
    readiness["progression_authority"] = "granted"
    readiness["valid_for_progression"] = True

    readiness_issues = _validate_readiness_receipt(readiness)
    assert "r7_actual_device_status_must_remain_not_run" in readiness_issues
    assert "r7_progression_authority_must_remain_none" in readiness_issues
    assert "r7_progression_must_remain_closed" in readiness_issues

    packet = deepcopy(_load(_R7_DEVICE_PACKET))
    packet["actual_device_execution_status"] = "passed"
    packet["valid_for_progression"] = True
    packet["cases"][0]["actual_device_result"]["status"] = "passed"
    packet["cases"][0]["actual_device_result"]["two_stage_display"] = "pass"

    packet_issues = _validate_unexecuted_device_packet(packet)
    assert "r7_device_packet_execution_status_invalid" in packet_issues
    assert "r7_device_packet_progression_must_remain_closed" in packet_issues
    assert "r7_device_result_must_remain_not_run" in packet_issues
    assert "r7_human_or_device_result_cannot_be_preclaimed" in packet_issues
