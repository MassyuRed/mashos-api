# -*- coding: utf-8 -*-
from __future__ import annotations

"""Closed Step 9 policies and body-free decision artifacts.

Step 0--8 artifacts are frozen.  Step 9 therefore owns its policies and
decision schemas in this side-by-side module instead of extending the frozen
v1 contract or changing the Step 8 v2 witness/binding contracts.
"""

from dataclasses import dataclass
import re
from typing import Any, Iterable, Mapping

from emlis_ai_nls_v3_artifact_contract import artifact_sha256
from emlis_ai_step9_dependency_manifest_v3 import (
    FROZEN_STEP9_DEPENDENCY_MANIFEST_SHA256,
    validate_step9_dependency_manifest,
)


HARD_GATE_DECISION_SCHEMA = "cocolon.emlis.nls_v3.hard_gate_candidate_decision.v1"
SELECTOR_DECISION_SCHEMA = "cocolon.emlis.nls_v3.selector_decision.v1"
RECOVERY_TRACE_SCHEMA = "cocolon.emlis.nls_v3.bounded_recovery_trace.v1"

_SHA_RE = re.compile(r"^[0-9a-f]{64}$")
_CANDIDATE_ID_RE = re.compile(r"^nls3cand_[0-9a-f]{64}$")
_MACHINE_CODE_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,95}$")


HARD_GATE_POLICY: dict[str, Any] = {
    "schema_version": "cocolon.emlis.nls_v3.semantic_hard_gate_policy.v1",
    "evaluation_mode": "all_rows_no_short_circuit",
    "runtime_scope": "offline_step9_runtime_disconnected",
    "gates": [
        {
            "ordinal": 1,
            "gate_id": "artifact_schema_parent_hash",
            "failure_codes": ["INVALID_SCHEMA", "PARENT_HASH_MISMATCH"],
        },
        {
            "ordinal": 2,
            "gate_id": "version_dependency_closure",
            "failure_codes": ["DEPENDENCY_DRIFT"],
        },
        {
            "ordinal": 3,
            "gate_id": "canonical_render_equality",
            "failure_codes": ["RENDER_TEXT_MISMATCH"],
        },
        {
            "ordinal": 4,
            "gate_id": "body_parseability",
            "failure_codes": ["UNPARSABLE_CONTROLLED_SURFACE"],
        },
        {
            "ordinal": 5,
            "gate_id": "evidence_resolution",
            "failure_codes": [
                "UNKNOWN_EVIDENCE_REF",
                "AMBIGUOUS_SEMANTIC_BINDING",
                "NO_SEMANTIC_BINDING",
                "SOURCE_CONTEXT_NOT_BODY_RECOVERABLE",
            ],
        },
        {
            "ordinal": 6,
            "gate_id": "required_obligation_coverage",
            "failure_codes": ["REQUIRED_OBLIGATION_MISSING"],
        },
        {
            "ordinal": 7,
            "gate_id": "bound_emlis_reception",
            "failure_codes": ["UNBOUND_EMLIS_RECEPTION"],
        },
        {
            "ordinal": 8,
            "gate_id": "polarity_modality_time",
            "failure_codes": [
                "POLARITY_INVERSION",
                "MODALITY_OVERCLAIM",
                "TEMPORAL_SCOPE_DRIFT",
            ],
        },
        {
            "ordinal": 9,
            "gate_id": "relation_type_direction",
            "failure_codes": [
                "RELATION_TYPE_MISMATCH",
                "RELATION_DIRECTION_INVERSION",
            ],
        },
        {
            "ordinal": 10,
            "gate_id": "referent_topic_scope",
            "failure_codes": ["AMBIGUOUS_REFERENT", "TOPIC_MIX"],
        },
        {
            "ordinal": 11,
            "gate_id": "unknown_boundary",
            "failure_codes": ["UNKNOWN_BOUNDARY_DROPPED"],
        },
        {
            "ordinal": 12,
            "gate_id": "self_denial_boundary",
            "failure_codes": ["SELF_DENIAL_ADOPTED", "SELF_DENIAL_AMPLIFIED"],
        },
        {
            "ordinal": 13,
            "gate_id": "unsupported_claim",
            "failure_codes": [
                "UNSUPPORTED_CLAIM",
                "INVENTED_CAUSE",
                "PERSONALITY_CLAIM",
                "DIAGNOSIS_CLAIM",
                "FUTURE_GUARANTEE",
            ],
        },
        {
            "ordinal": 14,
            "gate_id": "observation_reception_distinctness",
            "failure_codes": ["SECTION_SEMANTIC_REPLAY"],
        },
        {
            "ordinal": 15,
            "gate_id": "input_enumeration_shallow_mirror",
            "failure_codes": ["INPUT_ENUMERATION", "ANCHOR_REPLAY"],
        },
        {
            "ordinal": 16,
            "gate_id": "contribution_distinctness",
            "failure_codes": ["DISTINCT_OBLIGATIONS_COLLAPSED"],
        },
        {
            "ordinal": 17,
            "gate_id": "depth_proportionality",
            "failure_codes": ["DEPTH_INFLATED", "DEPTH_TRUNCATED"],
        },
        {
            "ordinal": 18,
            "gate_id": "surface_integrity",
            "failure_codes": [
                "BROKEN_GRAMMAR",
                "DUPLICATE_FRAGMENT",
                "LABEL_ORDER_INVALID",
            ],
        },
        {
            "ordinal": 19,
            "gate_id": "naming_address_contract",
            "failure_codes": ["USER_NAME_INVENTED", "ADDRESS_RETARGETED"],
        },
        {
            "ordinal": 20,
            "gate_id": "body_free_public_contract",
            "failure_codes": ["RAW_BODY_LEAK", "PUBLIC_CONTRACT_DIFF"],
        },
    ],
}

SELECTOR_POLICY: dict[str, Any] = {
    "schema_version": "cocolon.emlis.nls_v3.lexicographic_selector_policy.v1",
    "hard_pass_required": True,
    "weighted_score_forbidden": True,
    "attributes": [
        {
            "ordinal": 1,
            "name": "required_binding_count",
            "direction": "max",
            "formula": "cardinality(required_obligation_ids intersect bound_obligation_ids)",
        },
        {
            "ordinal": 2,
            "name": "required_distinctness_group_count",
            "direction": "max",
            "formula": "cardinality(distinctness_group of required bound obligations)",
        },
        {
            "ordinal": 3,
            "name": "bound_reception_target_count",
            "direction": "max",
            "formula": "cardinality(required nonstance targets of bound reception atoms)",
        },
        {
            "ordinal": 4,
            "name": "section_semantic_replay_count",
            "direction": "min",
            "formula": "cross_section exact semantic key replay count",
        },
        {
            "ordinal": 5,
            "name": "generic_referent_count",
            "direction": "min",
            "formula": "unbound or unknown referent atom count",
        },
        {
            "ordinal": 6,
            "name": "unnecessary_source_anchor_count",
            "direction": "min",
            "formula": "renderer source anchors on AST semantic_phrase referents with unique binding",
        },
        {
            "ordinal": 7,
            "name": "redundant_atom_count",
            "direction": "min",
            "formula": "same section duplicate semantic key count after first",
        },
        {
            "ordinal": 8,
            "name": "depth_deviation",
            "direction": "min",
            "formula": "abs(actual sentence groups - target(minimal=2 focused=3 layered=4))",
        },
        {
            "ordinal": 9,
            "name": "anaphora_distance",
            "direction": "min",
            "formula": "sum reception atom ordinal minus target atom ordinal",
        },
        {
            "ordinal": 10,
            "name": "candidate_id",
            "direction": "ascending_bytes",
            "formula": "sha256(ledger structural signature AST final bytes witness binding hashes)",
        },
    ],
}

RECOVERY_POLICY: dict[str, Any] = {
    "schema_version": "cocolon.emlis.nls_v3.bounded_recovery_policy.v1",
    "candidate_total_limit_including_initial": 12,
    "same_semantic_topology_recovery_limit": 2,
    "planner_rebuild_limit": 1,
    "post_render_text_repair_forbidden": True,
    "required_obligation_deletion_forbidden": True,
    "lanes": [
        "same_semantic_topology_safer_layout",
        "safe_split",
        "minimal_required_complete",
    ],
    "terminal_failure_status": "v3_no_valid_candidate",
    "v1_fallback_counts_as_v3_success": False,
}

HARD_GATE_POLICY_SHA256 = artifact_sha256(HARD_GATE_POLICY)
SELECTOR_POLICY_SHA256 = artifact_sha256(SELECTOR_POLICY)
RECOVERY_POLICY_SHA256 = artifact_sha256(RECOVERY_POLICY)

# Patched once from the canonical policy bytes before Step 9 verification.
FROZEN_HARD_GATE_POLICY_SHA256 = (
    "18007a7bbe794ebf77c148558d787d69cab0653b35ea2c2cc776e22161f2e46f"
)
FROZEN_SELECTOR_POLICY_SHA256 = (
    "39855afcaa59fe09d00a8fd1d95afaf99e4ac5d5524526e4e1217ea9f293663f"
)
FROZEN_RECOVERY_POLICY_SHA256 = (
    "867ebcfb171f823f4a675ac544f216039b63d5db1dddced7178a95f6b0427a55"
)


@dataclass(frozen=True, slots=True, repr=False)
class SemanticCandidate:
    """Private candidate bundle; no score or claimed coverage field exists."""

    discourse_plan: dict[str, Any]
    surface_ast: dict[str, Any]
    rendered_surface: Any
    parsed_surface_witness: dict[str, Any]
    verified_surface_binding: dict[str, Any]


@dataclass(frozen=True, slots=True)
class GateOutcome:
    ordinal: int
    gate_id: str
    status: str
    failure_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SelectorAttributes:
    required_binding_count: int
    required_distinctness_group_count: int
    bound_reception_target_count: int
    section_semantic_replay_count: int
    generic_referent_count: int
    unnecessary_source_anchor_count: int
    redundant_atom_count: int
    depth_deviation: int
    anaphora_distance: int
    candidate_id: str


@dataclass(frozen=True, slots=True)
class HardGateResult:
    schema_version: str
    candidate_id: str
    candidate_text_sha256: str
    parent_hashes: tuple[tuple[str, str], ...]
    gate_policy_sha256: str
    outcomes: tuple[GateOutcome, ...]
    hard_pass: bool
    selector_eligible: bool
    selector_attributes: SelectorAttributes | None
    body_free: bool = True


@dataclass(frozen=True, slots=True)
class SelectorDecision:
    schema_version: str
    status: str
    selected_candidate_id: str | None
    evaluated_candidate_ids: tuple[str, ...]
    rejected_candidate_ids: tuple[str, ...]
    selection_policy_sha256: str
    selection_attributes_sha256: str | None
    v3_success: bool
    v1_fallback_used: bool
    v1_fallback_counts_as_v3_success: bool
    body_free: bool = True


@dataclass(frozen=True, slots=True, repr=False)
class SemanticSelectionResult:
    decision: SelectorDecision
    gate_results: tuple[HardGateResult, ...]
    selected_candidate: SemanticCandidate | None


@dataclass(frozen=True, slots=True)
class RecoveryAttempt:
    lane: str
    candidate_id: str | None
    source_candidate_id: str | None
    status: str
    failure_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RecoveryTrace:
    schema_version: str
    recovery_policy_sha256: str
    initial_candidate_ids: tuple[str, ...]
    attempts: tuple[RecoveryAttempt, ...]
    total_candidate_count: int
    planner_rebuild_count: int
    final_status: str
    selected_candidate_id: str | None
    v3_success: bool
    v1_fallback_used: bool
    v1_fallback_counts_as_v3_success: bool
    body_free: bool = True


@dataclass(frozen=True, slots=True, repr=False)
class BoundedRecoveryResult:
    selection: SemanticSelectionResult
    trace: RecoveryTrace


def _unique_codes(codes: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted(set(codes)))


def _valid_sha(value: Any) -> bool:
    return type(value) is str and _SHA_RE.fullmatch(value) is not None


def _valid_candidate_id(value: Any) -> bool:
    return type(value) is str and _CANDIDATE_ID_RE.fullmatch(value) is not None


def _live_policy_sha256(value: Any) -> str | None:
    try:
        return artifact_sha256(value)
    except (RecursionError, TypeError, ValueError, UnicodeError):
        return None


def validate_step9_policies() -> tuple[str, ...]:
    issues: list[str] = []
    issues.extend(validate_step9_dependency_manifest())
    if (
        HARD_GATE_POLICY_SHA256 != FROZEN_HARD_GATE_POLICY_SHA256
        or _live_policy_sha256(HARD_GATE_POLICY)
        != FROZEN_HARD_GATE_POLICY_SHA256
    ):
        issues.append("HARD_GATE_POLICY_HASH_DRIFT")
    if (
        SELECTOR_POLICY_SHA256 != FROZEN_SELECTOR_POLICY_SHA256
        or _live_policy_sha256(SELECTOR_POLICY) != FROZEN_SELECTOR_POLICY_SHA256
    ):
        issues.append("SELECTOR_POLICY_HASH_DRIFT")
    if (
        RECOVERY_POLICY_SHA256 != FROZEN_RECOVERY_POLICY_SHA256
        or _live_policy_sha256(RECOVERY_POLICY) != FROZEN_RECOVERY_POLICY_SHA256
    ):
        issues.append("RECOVERY_POLICY_HASH_DRIFT")
    gates = HARD_GATE_POLICY.get("gates")
    if type(gates) is not list or len(gates) != 20:
        issues.append("HARD_GATE_POLICY_CARDINALITY_INVALID")
    else:
        if [row.get("ordinal") for row in gates if type(row) is dict] != list(
            range(1, 21)
        ):
            issues.append("HARD_GATE_POLICY_ORDER_INVALID")
        gate_ids = [row.get("gate_id") for row in gates if type(row) is dict]
        if (
            len(gate_ids) != 20
            or any(type(item) is not str for item in gate_ids)
            or len(gate_ids) != len(set(gate_ids))
        ):
            issues.append("HARD_GATE_POLICY_ID_INVALID")
        for row in gates:
            if type(row) is not dict or set(row) != {
                "ordinal",
                "gate_id",
                "failure_codes",
            }:
                issues.append("HARD_GATE_POLICY_ROW_INVALID")
                continue
            codes = row.get("failure_codes")
            if (
                type(codes) is not list
                or not codes
                or any(
                    type(code) is not str
                    or _MACHINE_CODE_RE.fullmatch(code) is None
                    for code in codes
                )
                or len(codes) != len(set(codes))
            ):
                issues.append("HARD_GATE_POLICY_FAILURE_CODE_INVALID")
    attributes = SELECTOR_POLICY.get("attributes")
    if type(attributes) is not list or len(attributes) != 10:
        issues.append("SELECTOR_POLICY_CARDINALITY_INVALID")
    else:
        if [row.get("ordinal") for row in attributes if type(row) is dict] != list(
            range(1, 11)
        ):
            issues.append("SELECTOR_POLICY_ORDER_INVALID")
        names = [row.get("name") for row in attributes if type(row) is dict]
        if (
            len(names) != 10
            or any(type(item) is not str for item in names)
            or len(names) != len(set(names))
        ):
            issues.append("SELECTOR_POLICY_ATTRIBUTE_INVALID")
        for row in attributes:
            if type(row) is not dict or set(row) != {
                "ordinal",
                "name",
                "direction",
                "formula",
            }:
                issues.append("SELECTOR_POLICY_ROW_INVALID")
    if RECOVERY_POLICY.get("candidate_total_limit_including_initial") != 12:
        issues.append("RECOVERY_TOTAL_LIMIT_INVALID")
    if RECOVERY_POLICY.get("same_semantic_topology_recovery_limit") != 2:
        issues.append("RECOVERY_TOPOLOGY_LIMIT_INVALID")
    if RECOVERY_POLICY.get("planner_rebuild_limit") != 1:
        issues.append("RECOVERY_REPLAN_LIMIT_INVALID")
    if RECOVERY_POLICY.get("v1_fallback_counts_as_v3_success") is not False:
        issues.append("V1_FALLBACK_SUCCESS_FORBIDDEN")
    return _unique_codes(issues)


def _validate_selector_attributes(value: Any) -> tuple[str, ...]:
    if type(value) is not SelectorAttributes:
        return ("SELECTOR_ATTRIBUTES_TYPE_INVALID",)
    issues: list[str] = []
    for item in (
        value.required_binding_count,
        value.required_distinctness_group_count,
        value.bound_reception_target_count,
        value.section_semantic_replay_count,
        value.generic_referent_count,
        value.unnecessary_source_anchor_count,
        value.redundant_atom_count,
        value.depth_deviation,
        value.anaphora_distance,
    ):
        if type(item) is not int or item < 0:
            issues.append("SELECTOR_ATTRIBUTE_VALUE_INVALID")
    if not _valid_candidate_id(value.candidate_id):
        issues.append("SELECTOR_ATTRIBUTE_CANDIDATE_ID_INVALID")
    return _unique_codes(issues)


def validate_hard_gate_result_structure(value: Any) -> tuple[str, ...]:
    issues: list[str] = []
    if type(value) is not HardGateResult:
        return ("HARD_GATE_RESULT_TYPE_INVALID",)
    if value.schema_version != HARD_GATE_DECISION_SCHEMA:
        issues.append("HARD_GATE_RESULT_SCHEMA_INVALID")
    if not _valid_candidate_id(value.candidate_id):
        issues.append("HARD_GATE_CANDIDATE_ID_INVALID")
    if not _valid_sha(value.candidate_text_sha256):
        issues.append("HARD_GATE_TEXT_HASH_INVALID")
    expected_parent_names = (
        "content_plan",
        "dependency_manifest",
        "discourse_plan",
        "obligation_ledger",
        "parsed_surface_witness",
        "source_snapshot",
        "surface_ast",
        "verified_surface_binding",
    )
    parent_hash_rows_valid = (
        type(value.parent_hashes) is tuple
        and all(
            type(row) is tuple and len(row) == 2
            for row in value.parent_hashes
        )
    )
    if not parent_hash_rows_valid or (
        tuple(row[0] for row in value.parent_hashes) != expected_parent_names
        or any(
            type(row[0]) is not str or not _valid_sha(row[1])
            for row in value.parent_hashes
        )
    ):
        issues.append("HARD_GATE_PARENT_HASHES_INVALID")
    if value.gate_policy_sha256 != FROZEN_HARD_GATE_POLICY_SHA256:
        issues.append("HARD_GATE_POLICY_HASH_MISMATCH")
    expected_rows = HARD_GATE_POLICY["gates"]
    if type(value.outcomes) is not tuple or len(value.outcomes) != 20:
        issues.append("HARD_GATE_OUTCOME_CARDINALITY_INVALID")
    else:
        for expected, outcome in zip(expected_rows, value.outcomes):
            if type(outcome) is not GateOutcome:
                issues.append("HARD_GATE_OUTCOME_TYPE_INVALID")
                continue
            if (
                outcome.ordinal != expected["ordinal"]
                or outcome.gate_id != expected["gate_id"]
            ):
                issues.append("HARD_GATE_OUTCOME_ORDER_INVALID")
            if type(outcome.status) is not str or outcome.status not in (
                "passed",
                "failed",
                "not_evaluated",
            ):
                issues.append("HARD_GATE_OUTCOME_STATUS_INVALID")
            if (
                type(outcome.failure_codes) is not tuple
                or any(
                    type(code) is not str
                    or code not in expected["failure_codes"]
                    for code in outcome.failure_codes
                )
                or tuple(sorted(set(outcome.failure_codes)))
                != outcome.failure_codes
            ):
                issues.append("HARD_GATE_OUTCOME_CODE_INVALID")
            if (outcome.status == "failed") != bool(outcome.failure_codes):
                issues.append("HARD_GATE_OUTCOME_STATUS_CODE_MISMATCH")
            if outcome.status == "not_evaluated" and outcome.failure_codes:
                issues.append("HARD_GATE_NOT_EVALUATED_CODE_FORBIDDEN")
    all_passed = (
        type(value.outcomes) is tuple
        and len(value.outcomes) == 20
        and all(
            type(outcome) is GateOutcome and outcome.status == "passed"
            for outcome in value.outcomes
        )
    )
    if value.hard_pass is not all_passed or value.selector_eligible is not all_passed:
        issues.append("HARD_GATE_PASS_STATUS_MISMATCH")
    if all_passed:
        attribute_issues = _validate_selector_attributes(value.selector_attributes)
        issues.extend(attribute_issues)
        if type(value.selector_attributes) is SelectorAttributes and (
            value.selector_attributes.candidate_id != value.candidate_id
        ):
            issues.append("SELECTOR_ATTRIBUTE_CANDIDATE_ID_MISMATCH")
    elif value.selector_attributes is not None:
        issues.append("FAILED_GATE_SELECTOR_ATTRIBUTES_FORBIDDEN")
    if value.body_free is not True:
        issues.append("HARD_GATE_RESULT_BODY_FREE_REQUIRED")
    return _unique_codes(issues)


def validate_selector_decision_structure(value: Any) -> tuple[str, ...]:
    issues: list[str] = []
    if type(value) is not SelectorDecision:
        return ("SELECTOR_DECISION_TYPE_INVALID",)
    if value.schema_version != SELECTOR_DECISION_SCHEMA:
        issues.append("SELECTOR_DECISION_SCHEMA_INVALID")
    if type(value.status) is not str or value.status not in (
        "selected",
        "v3_no_valid_candidate",
    ):
        issues.append("SELECTOR_STATUS_INVALID")
    if value.selection_policy_sha256 != FROZEN_SELECTOR_POLICY_SHA256:
        issues.append("SELECTOR_POLICY_HASH_MISMATCH")
    id_sets: dict[str, set[str]] = {}
    for field_name, ids, code in (
        (
            "evaluated",
            value.evaluated_candidate_ids,
            "SELECTOR_EVALUATED_IDS_INVALID",
        ),
        (
            "rejected",
            value.rejected_candidate_ids,
            "SELECTOR_REJECTED_IDS_INVALID",
        ),
    ):
        valid = (
            type(ids) is not tuple
            or any(not _valid_candidate_id(item) for item in ids)
        )
        if valid or ids != tuple(sorted(set(ids))):
            issues.append(code)
            id_sets[field_name] = set()
        else:
            id_sets[field_name] = set(ids)
    if not id_sets["rejected"] <= id_sets["evaluated"]:
        issues.append("SELECTOR_REJECTED_IDS_NOT_EVALUATED")
    if value.status == "selected":
        if (
            not _valid_candidate_id(value.selected_candidate_id)
            or value.selected_candidate_id not in id_sets["evaluated"]
            or value.selected_candidate_id in id_sets["rejected"]
            or not _valid_sha(value.selection_attributes_sha256)
            or value.v3_success is not True
        ):
            issues.append("SELECTOR_SELECTED_STATUS_MISMATCH")
    elif (
        value.selected_candidate_id is not None
        or value.selection_attributes_sha256 is not None
        or value.v3_success is not False
    ):
        issues.append("SELECTOR_NO_VALID_STATUS_MISMATCH")
    if value.v1_fallback_used is not False:
        issues.append("STEP9_V1_FALLBACK_USE_FORBIDDEN")
    if value.v1_fallback_counts_as_v3_success is not False:
        issues.append("V1_FALLBACK_SUCCESS_FORBIDDEN")
    if value.body_free is not True:
        issues.append("SELECTOR_DECISION_BODY_FREE_REQUIRED")
    return _unique_codes(issues)


def validate_recovery_trace_structure(value: Any) -> tuple[str, ...]:
    issues: list[str] = []
    if type(value) is not RecoveryTrace:
        return ("RECOVERY_TRACE_TYPE_INVALID",)
    if value.schema_version != RECOVERY_TRACE_SCHEMA:
        issues.append("RECOVERY_TRACE_SCHEMA_INVALID")
    if value.recovery_policy_sha256 != FROZEN_RECOVERY_POLICY_SHA256:
        issues.append("RECOVERY_POLICY_HASH_MISMATCH")
    initial_ids_valid = (
        type(value.initial_candidate_ids) is not tuple
        or any(not _valid_candidate_id(item) for item in value.initial_candidate_ids)
    )
    if initial_ids_valid or value.initial_candidate_ids != tuple(
        sorted(set(value.initial_candidate_ids))
    ):
        issues.append("RECOVERY_INITIAL_IDS_INVALID")
    seen: set[str] = (
        set(value.initial_candidate_ids) if not initial_ids_valid else set()
    )
    if type(value.attempts) is not tuple:
        issues.append("RECOVERY_ATTEMPTS_INVALID")
    else:
        valid_lanes = set(RECOVERY_POLICY["lanes"])
        candidate_attempts = 0
        topology_attempts = 0
        for attempt in value.attempts:
            if type(attempt) is not RecoveryAttempt:
                issues.append("RECOVERY_ATTEMPT_TYPE_INVALID")
                continue
            if type(attempt.lane) is not str or attempt.lane not in valid_lanes:
                issues.append("RECOVERY_LANE_INVALID")
            if type(attempt.status) is not str or attempt.status not in (
                "candidate_built",
                "unavailable",
                "rejected",
            ):
                issues.append("RECOVERY_ATTEMPT_STATUS_INVALID")
            candidate_id_valid = attempt.candidate_id is None or _valid_candidate_id(
                attempt.candidate_id
            )
            if attempt.candidate_id is not None:
                candidate_attempts += 1
                if not candidate_id_valid:
                    issues.append("RECOVERY_CANDIDATE_ID_INVALID")
                elif attempt.candidate_id in seen:
                    issues.append("RECOVERY_DUPLICATE_CANDIDATE_ID")
                if candidate_id_valid:
                    seen.add(attempt.candidate_id)
            if attempt.source_candidate_id is not None and not _valid_candidate_id(
                attempt.source_candidate_id
            ):
                issues.append("RECOVERY_SOURCE_CANDIDATE_ID_INVALID")
            if attempt.lane == "same_semantic_topology_safer_layout":
                topology_attempts += 1
            failure_codes_valid = (
                type(attempt.failure_codes) is tuple
                and all(
                    type(code) is str
                    and _MACHINE_CODE_RE.fullmatch(code) is not None
                    for code in attempt.failure_codes
                )
                and attempt.failure_codes
                == tuple(sorted(set(attempt.failure_codes)))
            )
            if not failure_codes_valid:
                issues.append("RECOVERY_ATTEMPT_CODE_INVALID")
            if attempt.status == "candidate_built" and (
                attempt.candidate_id is None or bool(attempt.failure_codes)
            ):
                issues.append("RECOVERY_ATTEMPT_STATUS_CODE_MISMATCH")
            if attempt.status == "rejected" and (
                attempt.candidate_id is None or not attempt.failure_codes
            ):
                issues.append("RECOVERY_ATTEMPT_STATUS_CODE_MISMATCH")
            if attempt.status == "unavailable" and (
                attempt.candidate_id is not None or not attempt.failure_codes
            ):
                issues.append("RECOVERY_ATTEMPT_STATUS_CODE_MISMATCH")
        if topology_attempts > RECOVERY_POLICY[
            "same_semantic_topology_recovery_limit"
        ]:
            issues.append("RECOVERY_TOPOLOGY_LIMIT_EXCEEDED")
        initial_count = (
            len(value.initial_candidate_ids)
            if type(value.initial_candidate_ids) is tuple
            else 0
        )
        if value.total_candidate_count != initial_count + candidate_attempts:
            issues.append("RECOVERY_TOTAL_COUNT_MISMATCH")
    if (
        type(value.total_candidate_count) is not int
        or not 0
        <= value.total_candidate_count
        <= RECOVERY_POLICY["candidate_total_limit_including_initial"]
    ):
        issues.append("RECOVERY_TOTAL_LIMIT_EXCEEDED")
    if (
        type(value.planner_rebuild_count) is not int
        or not 0
        <= value.planner_rebuild_count
        <= RECOVERY_POLICY["planner_rebuild_limit"]
    ):
        issues.append("RECOVERY_REPLAN_LIMIT_EXCEEDED")
    if type(value.final_status) is not str or value.final_status not in (
        "selected",
        "v3_no_valid_candidate",
    ):
        issues.append("RECOVERY_FINAL_STATUS_INVALID")
    if value.final_status == "selected":
        if (
            not _valid_candidate_id(value.selected_candidate_id)
            or value.selected_candidate_id not in seen
            or value.v3_success is not True
        ):
            issues.append("RECOVERY_SELECTED_STATUS_MISMATCH")
    elif value.selected_candidate_id is not None or value.v3_success is not False:
        issues.append("RECOVERY_NO_VALID_STATUS_MISMATCH")
    if value.v1_fallback_used is not False:
        issues.append("STEP9_V1_FALLBACK_USE_FORBIDDEN")
    if value.v1_fallback_counts_as_v3_success is not False:
        issues.append("V1_FALLBACK_SUCCESS_FORBIDDEN")
    if value.body_free is not True:
        issues.append("RECOVERY_TRACE_BODY_FREE_REQUIRED")
    return _unique_codes(issues)


def selector_attributes_sha256(value: SelectorAttributes) -> str:
    if type(value) is not SelectorAttributes:
        raise ValueError("SELECTOR_ATTRIBUTES_REQUIRED")
    return artifact_sha256(
        {
            "required_binding_count": value.required_binding_count,
            "required_distinctness_group_count": (
                value.required_distinctness_group_count
            ),
            "bound_reception_target_count": value.bound_reception_target_count,
            "section_semantic_replay_count": value.section_semantic_replay_count,
            "generic_referent_count": value.generic_referent_count,
            "unnecessary_source_anchor_count": (
                value.unnecessary_source_anchor_count
            ),
            "redundant_atom_count": value.redundant_atom_count,
            "depth_deviation": value.depth_deviation,
            "anaphora_distance": value.anaphora_distance,
            "candidate_id": value.candidate_id,
        }
    )


def parent_hash_mapping(value: HardGateResult) -> Mapping[str, str]:
    if type(value) is not HardGateResult:
        raise ValueError("HARD_GATE_RESULT_REQUIRED")
    return dict(value.parent_hashes)


__all__ = [
    "BoundedRecoveryResult",
    "FROZEN_HARD_GATE_POLICY_SHA256",
    "FROZEN_RECOVERY_POLICY_SHA256",
    "FROZEN_SELECTOR_POLICY_SHA256",
    "FROZEN_STEP9_DEPENDENCY_MANIFEST_SHA256",
    "HARD_GATE_DECISION_SCHEMA",
    "HARD_GATE_POLICY",
    "HARD_GATE_POLICY_SHA256",
    "HardGateResult",
    "GateOutcome",
    "RECOVERY_POLICY",
    "RECOVERY_POLICY_SHA256",
    "RECOVERY_TRACE_SCHEMA",
    "RecoveryAttempt",
    "RecoveryTrace",
    "SELECTOR_DECISION_SCHEMA",
    "SELECTOR_POLICY",
    "SELECTOR_POLICY_SHA256",
    "SemanticCandidate",
    "SemanticSelectionResult",
    "SelectorAttributes",
    "SelectorDecision",
    "parent_hash_mapping",
    "selector_attributes_sha256",
    "validate_hard_gate_result_structure",
    "validate_recovery_trace_structure",
    "validate_selector_decision_structure",
    "validate_step9_policies",
]
