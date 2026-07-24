# -*- coding: utf-8 -*-
from __future__ import annotations

"""Standalone Recovery Epoch 001 Step 9 successor graph.

The historical Step 9 modules and policies remain immutable.  This module
reuses their frozen semantic functions while replacing only the superseded
historical dependency-manifest validator with the canonical-current owner.
Both Step 9 verification and the dormant Step 10 adapter import this graph.
"""

import hashlib
import json
from pathlib import Path
from types import FunctionType
from typing import Any, Iterable, Mapping, Sequence

import emlis_ai_bounded_recovery_v3 as bounded_recovery_module
import emlis_ai_lexicographic_selector_v3 as lexicographic_selector_module
import emlis_ai_semantic_hard_gate_v3 as semantic_hard_gate_module
import emlis_ai_step9_artifact_contract_v3 as step9_artifact_contract_module
from emlis_ai_recovery_epoch001_canonical_current_closure_v3 import (
    RECOVERY_EPOCH001_CANDIDATE_VERSION_ID,
    RECOVERY_EPOCH001_CANONICAL_CURRENT_CLOSURE_SCHEMA,
    fresh_recovery_epoch001_canonical_current_closure,
    validate_recovery_epoch001_canonical_current_closure_shape,
)
from emlis_ai_bounded_recovery_v3 import BoundedRecoveryError
from emlis_ai_lexicographic_selector_v3 import LexicographicSelectorError
from emlis_ai_semantic_hard_gate_v3 import (
    SemanticHardGateError,
    build_semantic_candidate,
)
from emlis_ai_step9_artifact_contract_v3 import (
    BoundedRecoveryResult,
    SemanticCandidate,
    SemanticSelectionResult,
    validate_hard_gate_result_structure,
    validate_recovery_trace_structure,
    validate_selector_decision_structure,
)


def _canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _clone_policy_function(
    function: Any,
    replacements: Mapping[str, Any],
) -> Any:
    if type(function) is not FunctionType:
        raise RuntimeError("recovery_epoch001_successor_function_invalid")
    function_globals = dict(function.__globals__)
    function_globals.update(replacements)
    clone = FunctionType(
        function.__code__,
        function_globals,
        function.__name__,
        function.__defaults__,
        function.__closure__,
    )
    clone.__kwdefaults__ = function.__kwdefaults__
    clone.__annotations__ = dict(function.__annotations__)
    clone.__module__ = __name__
    return clone


_REPO_ROOT = Path(__file__).resolve().parents[3]
_CURRENT_CLOSURE_SNAPSHOT = (
    fresh_recovery_epoch001_canonical_current_closure()
)
_CURRENT_CLOSURE_ROOT = (
    _CURRENT_CLOSURE_SNAPSHOT["canonical_current_closure_sha256"]
)
_CURRENT_CLOSURE_ISSUES = (
    validate_recovery_epoch001_canonical_current_closure_shape(
        _CURRENT_CLOSURE_SNAPSHOT
    )
)


def _validate_current_closure_snapshot() -> tuple[str, ...]:
    return _CURRENT_CLOSURE_ISSUES


def _canonical_current_source_file_matches(filename: str) -> bool:
    if type(filename) is not str or Path(filename).name != filename:
        return False
    matches = [
        row
        for row in _CURRENT_CLOSURE_SNAPSHOT["files"]
        if Path(row["path"]).name == filename
    ]
    if len(matches) != 1:
        return False
    path = _REPO_ROOT / matches[0]["path"]
    return (
        path.is_file()
        and hashlib.sha256(path.read_bytes()).hexdigest()
        == matches[0]["sha256"]
    )


_CURRENT_STEP9_POLICY_VALIDATOR = _clone_policy_function(
    step9_artifact_contract_module.validate_step9_policies,
    {
        "validate_step9_dependency_manifest": (
            _validate_current_closure_snapshot
        ),
    },
)
_CURRENT_HARD_GATE_EVALUATE = _clone_policy_function(
    semantic_hard_gate_module._evaluate,
    {
        "validate_step9_policies": _CURRENT_STEP9_POLICY_VALIDATOR,
        "validate_step9_dependency_manifest": (
            _validate_current_closure_snapshot
        ),
        "dependency_source_file_matches": (
            _canonical_current_source_file_matches
        ),
        "FROZEN_STEP9_DEPENDENCY_MANIFEST_SHA256": _CURRENT_CLOSURE_ROOT,
    },
)


def evaluate_semantic_hard_gate(
    candidate: SemanticCandidate,
    *,
    inventory_result: Any,
    content_plan: Mapping[str, Any],
    lexical_authority: Any,
    match_authority: Any,
) -> Any:
    result = _CURRENT_HARD_GATE_EVALUATE(
        candidate,
        inventory_result=inventory_result,
        content_plan=content_plan,
        lexical_authority=lexical_authority,
        match_authority=match_authority,
    )
    if validate_hard_gate_result_structure(result):
        raise SemanticHardGateError("HARD_GATE_RESULT_CONTRACT_REJECTED")
    return result


def validate_semantic_hard_gate_result(
    value: Any,
    *,
    candidate: SemanticCandidate,
    inventory_result: Any,
    content_plan: Mapping[str, Any],
    lexical_authority: Any,
    match_authority: Any,
) -> tuple[str, ...]:
    try:
        structural = validate_hard_gate_result_structure(value)
        expected = _CURRENT_HARD_GATE_EVALUATE(
            candidate,
            inventory_result=inventory_result,
            content_plan=content_plan,
            lexical_authority=lexical_authority,
            match_authority=match_authority,
        )
    except (
        AttributeError,
        KeyError,
        SemanticHardGateError,
        TypeError,
        ValueError,
        UnicodeError,
        RecursionError,
    ):
        return ("HARD_GATE_REVALIDATION_FAILED",)
    issues = set(structural)
    if value != expected:
        issues.add("HARD_GATE_RESULT_RECOMPUTATION_MISMATCH")
    return tuple(sorted(issues))


_CURRENT_LEXICOGRAPHIC_SELECT = _clone_policy_function(
    lexicographic_selector_module._select,
    {
        "validate_step9_policies": _CURRENT_STEP9_POLICY_VALIDATOR,
        "evaluate_semantic_hard_gate": evaluate_semantic_hard_gate,
    },
)


def select_semantic_candidate_lexicographically(
    candidates: Sequence[SemanticCandidate],
    *,
    inventory_result: Any,
    content_plan: Mapping[str, Any],
    lexical_authority: Any,
    match_authority: Any,
) -> SemanticSelectionResult:
    result = _CURRENT_LEXICOGRAPHIC_SELECT(
        candidates,
        inventory_result=inventory_result,
        content_plan=content_plan,
        lexical_authority=lexical_authority,
        match_authority=match_authority,
    )
    if validate_selector_decision_structure(result.decision):
        raise LexicographicSelectorError(
            "SELECTOR_DECISION_CONTRACT_REJECTED"
        )
    return result


def validate_semantic_selection_result(
    value: Any,
    *,
    candidates: Sequence[SemanticCandidate],
    inventory_result: Any,
    content_plan: Mapping[str, Any],
    lexical_authority: Any,
    match_authority: Any,
) -> tuple[str, ...]:
    try:
        expected = _CURRENT_LEXICOGRAPHIC_SELECT(
            candidates,
            inventory_result=inventory_result,
            content_plan=content_plan,
            lexical_authority=lexical_authority,
            match_authority=match_authority,
        )
    except (
        AttributeError,
        KeyError,
        LexicographicSelectorError,
        TypeError,
        ValueError,
        UnicodeError,
        RecursionError,
    ):
        return ("SELECTOR_REVALIDATION_FAILED",)
    if type(value) is not SemanticSelectionResult:
        return ("SELECTOR_RESULT_TYPE_INVALID",)
    issues = set(validate_selector_decision_structure(value.decision))
    if value.decision != expected.decision:
        issues.add("SELECTOR_DECISION_RECOMPUTATION_MISMATCH")
    if value.gate_results != expected.gate_results:
        issues.add("SELECTOR_GATE_RESULTS_RECOMPUTATION_MISMATCH")
    if value.selected_candidate is not expected.selected_candidate:
        issues.add("SELECTOR_SELECTED_CANDIDATE_MISMATCH")
    return tuple(sorted(issues))


_CURRENT_BOUNDED_RECOVER = _clone_policy_function(
    bounded_recovery_module._recover,
    {
        "validate_step9_policies": _CURRENT_STEP9_POLICY_VALIDATOR,
        "select_semantic_candidates": (
            select_semantic_candidate_lexicographically
        ),
    },
)


def apply_bounded_recovery(
    initial_candidates: Sequence[SemanticCandidate],
    *,
    inventory_result: Any,
    content_plan: Mapping[str, Any],
    lexical_authority: Any,
    match_authority: Any,
) -> BoundedRecoveryResult:
    result = _CURRENT_BOUNDED_RECOVER(
        initial_candidates,
        inventory_result=inventory_result,
        content_plan=content_plan,
        lexical_authority=lexical_authority,
        match_authority=match_authority,
    )
    if validate_recovery_trace_structure(result.trace):
        raise BoundedRecoveryError("RECOVERY_TRACE_CONTRACT_REJECTED")
    return result


def validate_bounded_recovery_result(
    value: Any,
    *,
    initial_candidates: Sequence[SemanticCandidate],
    inventory_result: Any,
    content_plan: Mapping[str, Any],
    lexical_authority: Any,
    match_authority: Any,
) -> tuple[str, ...]:
    try:
        expected = _CURRENT_BOUNDED_RECOVER(
            initial_candidates,
            inventory_result=inventory_result,
            content_plan=content_plan,
            lexical_authority=lexical_authority,
            match_authority=match_authority,
        )
    except (
        AttributeError,
        BoundedRecoveryError,
        KeyError,
        TypeError,
        ValueError,
        UnicodeError,
        RecursionError,
    ):
        return ("RECOVERY_REVALIDATION_FAILED",)
    if type(value) is not BoundedRecoveryResult:
        return ("RECOVERY_RESULT_TYPE_INVALID",)
    if type(value.selection) is not SemanticSelectionResult:
        return ("RECOVERY_RESULT_TYPE_INVALID",)
    issues = set(validate_recovery_trace_structure(value.trace))
    if value.trace != expected.trace:
        issues.add("RECOVERY_TRACE_RECOMPUTATION_MISMATCH")
    if value.selection.decision != expected.selection.decision:
        issues.add("RECOVERY_SELECTION_RECOMPUTATION_MISMATCH")
    if value.selection.gate_results != expected.selection.gate_results:
        issues.add("RECOVERY_GATE_RESULTS_RECOMPUTATION_MISMATCH")
    if value.selection.selected_candidate != expected.selection.selected_candidate:
        issues.add("RECOVERY_SELECTED_CANDIDATE_MISMATCH")
    return tuple(sorted(issues))


def build_semantic_candidate_set(
    discourse_plans: Iterable[Mapping[str, Any]],
    *,
    inventory_result: Any,
    content_plan: Mapping[str, Any],
    lexical_authority: Any,
    match_authority: Any,
) -> tuple[Any, ...]:
    """Build the ordered candidate tuple consumed by this successor graph."""

    return tuple(
        build_semantic_candidate(
            plan,
            inventory_result=inventory_result,
            content_plan=content_plan,
            lexical_authority=lexical_authority,
            match_authority=match_authority,
        )
        for plan in discourse_plans
    )


RECOVERY_EPOCH001_STEP9_SUCCESSOR_GRAPH = {
    "schema_version": (
        "cocolon.emlis.nls_v3.recovery_epoch001.step9_successor_graph.v1"
    ),
    "candidate_version_id": RECOVERY_EPOCH001_CANDIDATE_VERSION_ID,
    "canonical_current_closure_schema": (
        RECOVERY_EPOCH001_CANONICAL_CURRENT_CLOSURE_SCHEMA
    ),
    "canonical_current_closure_sha256": _CURRENT_CLOSURE_ROOT,
    "historical_policy_disposition": (
        "IMMUTABLE_SEMANTIC_POLICY_REUSED_DEPENDENCY_OWNER_SUPERSEDED"
    ),
    "callable_chain": (
        "build_semantic_candidate_set",
        "evaluate_semantic_hard_gate",
        "validate_semantic_hard_gate_result",
        "select_semantic_candidate_lexicographically",
        "validate_semantic_selection_result",
        "apply_bounded_recovery",
        "validate_bounded_recovery_result",
    ),
    "body_free": True,
}
RECOVERY_EPOCH001_STEP9_SUCCESSOR_GRAPH_ID = _canonical_sha256(
    RECOVERY_EPOCH001_STEP9_SUCCESSOR_GRAPH
)


__all__ = [
    "RECOVERY_EPOCH001_STEP9_SUCCESSOR_GRAPH",
    "RECOVERY_EPOCH001_STEP9_SUCCESSOR_GRAPH_ID",
    "build_semantic_candidate_set",
    "evaluate_semantic_hard_gate",
    "validate_semantic_hard_gate_result",
    "select_semantic_candidate_lexicographically",
    "validate_semantic_selection_result",
    "apply_bounded_recovery",
    "validate_bounded_recovery_result",
]
