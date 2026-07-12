# -*- coding: utf-8 -*-
from __future__ import annotations

"""Body-free Gate 0 decision and fail-closed exact-8 packet boundary."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any, Final

from helpers.emlis_ai_grounded_observation_i7_readfeel import (
    I7KarenLocalReview,
    I7LocalReadFeelAssessment,
    validate_i7_karen_local_reviews,
)


GATE0_LOCAL_PASS_DEVICE_PACKET_READY_STOPPED: Final = (
    "GATE0_LOCAL_PASS_DEVICE_PACKET_READY_STOPPED"
)
GATE0_REPAIR_RETURN_STOPPED: Final = "GATE0_REPAIR_RETURN_STOPPED"
GATE0_TEST_OR_CONTRACT_BLOCKED_STOPPED: Final = (
    "GATE0_TEST_OR_CONTRACT_BLOCKED_STOPPED"
)
GATE0_VALIDATION_EVIDENCE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.gate0.validation.bodyfree.v2"
)
GATE0_LOCAL_DECISION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.gate0.local_decision.bodyfree.v2"
)
GATE0_EXACT8_CASE_IDS: Final[tuple[str, ...]] = (
    "A",
    "B",
    "C",
    "D",
    "I6-S03",
    "I6-L03",
    "I6-C01",
    "I6-D02",
)
GATE0_DEVICE_REQUIRED_META_FIELDS: Final[tuple[str, ...]] = (
    "generation_path",
    "composer_source",
    "semantic_quality_gate",
    "public_reply_path_connected",
)
_SHA256_RE: Final = re.compile(r"^[0-9a-f]{64}$")


class Gate0DevicePacketBlocked(ValueError):
    """Raised when exact-8 generation is attempted before a binary Gate 0 pass."""


@dataclass(frozen=True)
class Gate0ValidationEvidence:
    schema_version: str
    source_snapshot_fingerprint: str
    targeted_suites_green: bool
    targeted_result_ref: str
    safety_public_contract_green: bool
    safety_public_result_ref: str
    rn_contract_green: bool
    rn_result_ref: str
    full_collect_success: bool
    full_collect_return_code: int
    collected_test_count: int
    collection_error_refs: tuple[str, ...]
    full_backend_green: bool
    full_backend_return_code: int
    full_backend_result_ref: str
    unclassified_failure_refs: tuple[str, ...]

    def as_body_free_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "source_snapshot_fingerprint": self.source_snapshot_fingerprint,
            "targeted_suites_green": self.targeted_suites_green,
            "targeted_result_ref": self.targeted_result_ref,
            "safety_public_contract_green": self.safety_public_contract_green,
            "safety_public_result_ref": self.safety_public_result_ref,
            "rn_contract_green": self.rn_contract_green,
            "rn_result_ref": self.rn_result_ref,
            "full_collect_success": self.full_collect_success,
            "full_collect_return_code": self.full_collect_return_code,
            "collected_test_count": self.collected_test_count,
            "collection_error_count": len(self.collection_error_refs),
            "collection_error_refs": list(self.collection_error_refs),
            "full_backend_green": self.full_backend_green,
            "full_backend_return_code": self.full_backend_return_code,
            "full_backend_result_ref": self.full_backend_result_ref,
            "unclassified_failure_refs": list(self.unclassified_failure_refs),
            "raw_input_included": False,
            "returned_surface_included": False,
            "comment_text_included": False,
        }

    @classmethod
    def from_body_free_mapping(
        cls,
        value: Mapping[str, Any],
    ) -> "Gate0ValidationEvidence":
        steps = dict(value.get("steps") or {})
        targeted = dict(steps.get("targeted") or {})
        safety = dict(steps.get("safety_public_contract") or {})
        rn = dict(steps.get("rn_contract") or {})
        collect = dict(steps.get("full_collect") or {})
        backend = dict(steps.get("full_backend") or {})
        return cls(
            schema_version=str(value.get("schema_version") or ""),
            source_snapshot_fingerprint=str(
                value.get("source_snapshot_fingerprint") or ""
            ),
            targeted_suites_green=targeted.get("passed") is True,
            targeted_result_ref=str(targeted.get("command_ref") or ""),
            safety_public_contract_green=safety.get("passed") is True,
            safety_public_result_ref=str(safety.get("command_ref") or ""),
            rn_contract_green=rn.get("passed") is True,
            rn_result_ref=str(rn.get("command_ref") or ""),
            full_collect_success=collect.get("passed") is True,
            full_collect_return_code=int(collect.get("return_code", -1)),
            collected_test_count=int(collect.get("collected_test_count", 0)),
            collection_error_refs=tuple(
                str(item) for item in collect.get("collection_error_refs") or ()
            ),
            full_backend_green=backend.get("passed") is True,
            full_backend_return_code=int(backend.get("return_code", -1)),
            full_backend_result_ref=str(backend.get("command_ref") or ""),
            unclassified_failure_refs=tuple(
                str(item) for item in value.get("unclassified_failure_refs") or ()
            ),
        )


def validate_gate0_validation_evidence(
    evidence: Gate0ValidationEvidence,
    *,
    expected_source_snapshot_fingerprint: str,
) -> tuple[str, ...]:
    issues: list[str] = []
    if evidence.schema_version != GATE0_VALIDATION_EVIDENCE_SCHEMA_VERSION:
        issues.append("validation_schema_version_mismatch")
    if not _SHA256_RE.fullmatch(evidence.source_snapshot_fingerprint):
        issues.append("validation_source_snapshot_invalid")
    if evidence.source_snapshot_fingerprint != expected_source_snapshot_fingerprint:
        issues.append("validation_source_snapshot_mismatch")
    for name, value in (
        ("targeted_result_ref", evidence.targeted_result_ref),
        ("safety_public_result_ref", evidence.safety_public_result_ref),
        ("rn_result_ref", evidence.rn_result_ref),
        ("full_backend_result_ref", evidence.full_backend_result_ref),
    ):
        if not value:
            issues.append(f"{name}_missing")
    collect_consistent = bool(
        evidence.full_collect_return_code == 0
        and evidence.collected_test_count > 0
        and not evidence.collection_error_refs
    )
    if evidence.full_collect_success != collect_consistent:
        issues.append("full_collect_evidence_inconsistent")
    if evidence.full_backend_green and evidence.full_backend_return_code != 0:
        issues.append("full_backend_evidence_inconsistent")
    return tuple(dict.fromkeys(issues))


def _validation_pass(
    evidence: Gate0ValidationEvidence,
    *,
    expected_source_snapshot_fingerprint: str,
) -> tuple[bool, tuple[str, ...]]:
    integrity_issues = validate_gate0_validation_evidence(
        evidence,
        expected_source_snapshot_fingerprint=expected_source_snapshot_fingerprint,
    )
    blocker_refs = [*integrity_issues]
    if not evidence.targeted_suites_green:
        blocker_refs.append("targeted_suites_not_green")
    if not evidence.safety_public_contract_green:
        blocker_refs.append("safety_public_contract_not_green")
    if not evidence.rn_contract_green:
        blocker_refs.append("rn_contract_not_green")
    if not evidence.full_collect_success:
        blocker_refs.append("full_collect_not_successful")
    blocker_refs.extend(evidence.collection_error_refs)
    if not evidence.full_backend_green:
        blocker_refs.append("full_backend_not_green")
    blocker_refs.extend(evidence.unclassified_failure_refs)
    blockers = tuple(dict.fromkeys(str(item) for item in blocker_refs if item))
    return not blockers, blockers


def _sha256_json(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def build_gate0_local_decision(
    *,
    local_assessments: Sequence[I7LocalReadFeelAssessment],
    actual_local_reviews: Sequence[I7KarenLocalReview],
    validation_evidence: Gate0ValidationEvidence,
    expected_source_snapshot_fingerprint: str,
) -> dict[str, Any]:
    expected_case_ids = tuple(item.case_id for item in local_assessments)
    review_reasons = validate_i7_karen_local_reviews(
        actual_local_reviews,
        expected_case_ids=expected_case_ids,
    )
    automated_pass = bool(
        len(local_assessments) == 16
        and all(item.candidate_status == "candidate_pass" for item in local_assessments)
    )
    local_human_pass_count = sum(item.verdict == "local_human_pass" for item in actual_local_reviews)
    repair_required_count = sum(item.verdict == "repair_required" for item in actual_local_reviews)
    hard_fatal_count = sum(item.verdict == "hard_fatal" for item in actual_local_reviews)
    local_human_pass = bool(
        not review_reasons
        and len(actual_local_reviews) == 16
        and local_human_pass_count == 16
        and repair_required_count == 0
        and hard_fatal_count == 0
    )
    review_snapshots = tuple(
        dict.fromkeys(
            str(item.snapshot_fingerprint)
            for item in actual_local_reviews
            if str(item.snapshot_fingerprint)
        )
    )
    review_snapshot = review_snapshots[0] if len(review_snapshots) == 1 else ""
    validation_pass, validation_blockers = _validation_pass(
        validation_evidence,
        expected_source_snapshot_fingerprint=expected_source_snapshot_fingerprint,
    )
    snapshot_match = bool(
        review_snapshot
        and review_snapshot == validation_evidence.source_snapshot_fingerprint
        == expected_source_snapshot_fingerprint
    )
    blockers = list(validation_blockers)
    if not snapshot_match:
        blockers.append("review_validation_source_snapshot_mismatch")
    if not automated_pass:
        blockers.append("automated_candidate_not_passed")
    blockers = list(dict.fromkeys(blockers))
    validation_pass = bool(validation_pass and snapshot_match and automated_pass)
    passed = bool(
        automated_pass
        and local_human_pass
        and validation_pass
    )
    if passed:
        decision_code = GATE0_LOCAL_PASS_DEVICE_PACKET_READY_STOPPED
    elif not local_human_pass:
        decision_code = GATE0_REPAIR_RETURN_STOPPED
    else:
        decision_code = GATE0_TEST_OR_CONTRACT_BLOCKED_STOPPED
    evidence_mapping = validation_evidence.as_body_free_dict()
    return {
        "schema_version": GATE0_LOCAL_DECISION_SCHEMA_VERSION,
        "source_snapshot_fingerprint": expected_source_snapshot_fingerprint,
        "review_snapshot_fingerprint": review_snapshot,
        "validation_snapshot_fingerprint": validation_evidence.source_snapshot_fingerprint,
        "validation_evidence_sha256": _sha256_json(evidence_mapping),
        "decision_code": decision_code,
        "gate0_local_pass": passed,
        "automated_candidate_pass": automated_pass,
        "actual_local_review_count": len(actual_local_reviews),
        "local_human_pass_count": local_human_pass_count,
        "repair_required_count": repair_required_count,
        "hard_fatal_count": hard_fatal_count,
        "validation": {
            "targeted_suites_green": validation_evidence.targeted_suites_green,
            "safety_public_contract_green": validation_evidence.safety_public_contract_green,
            "rn_contract_green": validation_evidence.rn_contract_green,
            "full_collect_success": validation_evidence.full_collect_success,
            "full_collect_return_code": validation_evidence.full_collect_return_code,
            "collected_test_count": validation_evidence.collected_test_count,
            "collection_error_count": len(validation_evidence.collection_error_refs),
            "full_backend_green": validation_evidence.full_backend_green,
            "full_backend_return_code": validation_evidence.full_backend_return_code,
            "unclassified_failure_count": len(
                validation_evidence.unclassified_failure_refs
            ),
            "source_snapshot_match": snapshot_match,
        },
        "blocker_refs": blockers,
        "review_validation_reason_refs": list(review_reasons),
        "exact8_packet_generation_allowed": passed,
        "exact8_packet_generated": False,
        "device_evidence_status": "not_started",
        "p5_formal_24_start_allowed": False,
        "p6_start_allowed": False,
        "p8_start_allowed": False,
        "raw_input_included": False,
        "returned_surface_included": False,
        "comment_text_included": False,
    }


def build_exact8_device_packet(
    *,
    gate0_decision: Mapping[str, Any],
    cases: Sequence[Any],
    local_comment_sha256_by_case: Mapping[str, str],
) -> dict[str, Any]:
    """Build exact-8 from frozen helpers only after a real Gate 0 pass."""

    if (
        gate0_decision.get("schema_version")
        != GATE0_LOCAL_DECISION_SCHEMA_VERSION
        or gate0_decision.get("decision_code")
        != GATE0_LOCAL_PASS_DEVICE_PACKET_READY_STOPPED
        or gate0_decision.get("gate0_local_pass") is not True
        or gate0_decision.get("exact8_packet_generation_allowed") is not True
    ):
        raise Gate0DevicePacketBlocked("gate0_local_pass_required")
    validation = dict(gate0_decision.get("validation") or {})
    source_snapshot = str(gate0_decision.get("source_snapshot_fingerprint") or "")
    if (
        validation.get("targeted_suites_green") is not True
        or validation.get("safety_public_contract_green") is not True
        or validation.get("rn_contract_green") is not True
        or validation.get("full_collect_success") is not True
        or int(validation.get("collection_error_count", -1)) != 0
        or validation.get("full_backend_green") is not True
        or int(validation.get("unclassified_failure_count", -1)) != 0
        or validation.get("source_snapshot_match") is not True
        or not _SHA256_RE.fullmatch(source_snapshot)
        or source_snapshot
        != str(gate0_decision.get("review_snapshot_fingerprint") or "")
        or source_snapshot
        != str(gate0_decision.get("validation_snapshot_fingerprint") or "")
    ):
        raise Gate0DevicePacketBlocked("gate0_validation_v2_pass_required")
    case_index = {str(case.case_id): case for case in cases}
    if not set(GATE0_EXACT8_CASE_IDS) <= set(case_index):
        raise Gate0DevicePacketBlocked("exact8_frozen_case_missing")
    packet_cases = []
    for case_id in GATE0_EXACT8_CASE_IDS:
        current_input = case_index[case_id].as_current_input()
        local_hash = str(local_comment_sha256_by_case.get(case_id) or "")
        if len(local_hash) != 64:
            raise Gate0DevicePacketBlocked("exact8_local_comparison_hash_missing")
        packet_cases.append(
            {
                "case_id": case_id,
                "exact_current_input": current_input,
                "current_input_sha256": _sha256_json(current_input),
                "local_comment_sha256": local_hash,
            }
        )
    return {
        "schema_version": "cocolon.emlis.gate0.exact8_device_packet.v2",
        "source_snapshot_fingerprint": source_snapshot,
        "packet_status": "ready_waiting_for_device_evidence",
        "case_order": list(GATE0_EXACT8_CASE_IDS),
        "required_meta_fields": list(GATE0_DEVICE_REQUIRED_META_FIELDS),
        "instructions": [
            "use_each_exact_current_input_without_editing",
            "capture_visible_emlis_body",
            "capture_modal_screenshot_local_only",
            "record_required_body_free_meta",
            "record_clipping_pressure_or_layout_breakage",
        ],
        "arbitrary_input_allowed": False,
        "screenshot_local_only": True,
        "cases": packet_cases,
        "p5_formal_24_started_here": False,
        "p8_started_here": False,
    }


__all__ = [
    "GATE0_LOCAL_PASS_DEVICE_PACKET_READY_STOPPED",
    "GATE0_REPAIR_RETURN_STOPPED",
    "GATE0_TEST_OR_CONTRACT_BLOCKED_STOPPED",
    "GATE0_VALIDATION_EVIDENCE_SCHEMA_VERSION",
    "GATE0_LOCAL_DECISION_SCHEMA_VERSION",
    "GATE0_EXACT8_CASE_IDS",
    "GATE0_DEVICE_REQUIRED_META_FIELDS",
    "Gate0DevicePacketBlocked",
    "Gate0ValidationEvidence",
    "validate_gate0_validation_evidence",
    "build_gate0_local_decision",
    "build_exact8_device_packet",
]
