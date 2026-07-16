# -*- coding: utf-8 -*-
from __future__ import annotations

"""Deterministic Step 9 selector over independently hard-passed candidates."""

from typing import Any, Mapping, Sequence

from emlis_ai_canonical_renderer_v3 import RequestLexicalAuthority
from emlis_ai_discourse_graph_planner_v3 import MAX_DISCOURSE_CANDIDATES
from emlis_ai_independent_semantic_matcher_v3 import IndependentMatchSourceAuthority
from emlis_ai_nls_v3_artifact_contract import artifact_sha256
from emlis_ai_semantic_hard_gate_v3 import (
    derive_semantic_candidate_id,
    evaluate_semantic_hard_gate,
)
from emlis_ai_semantic_obligation_inventory_v3 import (
    SemanticObligationInventoryResult,
)
from emlis_ai_step9_artifact_contract_v3 import (
    FROZEN_SELECTOR_POLICY_SHA256,
    SELECTOR_DECISION_SCHEMA,
    SemanticCandidate,
    SemanticSelectionResult,
    SelectorAttributes,
    SelectorDecision,
    selector_attributes_sha256,
    validate_selector_decision_structure,
    validate_step9_policies,
)


class LexicographicSelectorError(ValueError):
    """Fail-closed selector error containing no candidate body."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def selector_sort_key(attributes: SelectorAttributes) -> tuple[Any, ...]:
    if type(attributes) is not SelectorAttributes:
        raise LexicographicSelectorError("SELECTOR_ATTRIBUTES_REQUIRED")
    return (
        -attributes.required_binding_count,
        -attributes.required_distinctness_group_count,
        -attributes.bound_reception_target_count,
        attributes.section_semantic_replay_count,
        attributes.generic_referent_count,
        attributes.unnecessary_source_anchor_count,
        attributes.redundant_atom_count,
        attributes.depth_deviation,
        attributes.anaphora_distance,
        attributes.candidate_id.encode("ascii"),
    )


def _selected_candidate_id_from_results(gate_results: Sequence[Any]) -> str | None:
    eligible = [
        result
        for result in gate_results
        if getattr(result, "hard_pass", False) is True
        and getattr(result, "selector_eligible", False) is True
        and type(getattr(result, "selector_attributes", None))
        is SelectorAttributes
    ]
    if not eligible:
        return None
    return min(
        eligible,
        key=lambda result: selector_sort_key(result.selector_attributes),
    ).candidate_id


def _select(
    candidates: Sequence[SemanticCandidate],
    *,
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
    lexical_authority: RequestLexicalAuthority,
    match_authority: IndependentMatchSourceAuthority,
) -> SemanticSelectionResult:
    if type(candidates) not in {list, tuple}:
        raise LexicographicSelectorError("SELECTOR_CANDIDATE_SEQUENCE_REQUIRED")
    if validate_step9_policies():
        raise LexicographicSelectorError("SELECTOR_POLICY_DRIFT")
    if len(candidates) > MAX_DISCOURSE_CANDIDATES:
        raise LexicographicSelectorError("SELECTOR_CANDIDATE_LIMIT_EXCEEDED")
    if any(type(candidate) is not SemanticCandidate for candidate in candidates):
        raise LexicographicSelectorError("SELECTOR_CANDIDATE_TYPE_INVALID")

    keyed = [
        (
            derive_semantic_candidate_id(
                candidate,
                inventory_result=inventory_result,
            ),
            candidate,
        )
        for candidate in candidates
    ]
    keyed.sort(key=lambda item: item[0].encode("ascii"))
    candidate_ids = [item[0] for item in keyed]
    if len(candidate_ids) != len(set(candidate_ids)):
        raise LexicographicSelectorError("SELECTOR_DUPLICATE_CANDIDATE_ID")

    evaluated = [
        (
            candidate_id,
            candidate,
            evaluate_semantic_hard_gate(
                candidate,
                inventory_result=inventory_result,
                content_plan=content_plan,
                lexical_authority=lexical_authority,
                match_authority=match_authority,
            ),
        )
        for candidate_id, candidate in keyed
    ]
    passed = [
        row
        for row in evaluated
        if row[2].hard_pass is True
        and row[2].selector_eligible is True
        and type(row[2].selector_attributes) is SelectorAttributes
    ]
    rejected_ids = tuple(
        candidate_id
        for candidate_id, _candidate, gate_result in evaluated
        if gate_result.hard_pass is not True
    )
    selected_candidate: SemanticCandidate | None = None
    selected_id: str | None = None
    selected_attributes: SelectorAttributes | None = None
    ranked_id = _selected_candidate_id_from_results(
        [row[2] for row in evaluated]
    )
    if ranked_id is not None:
        selected_id, selected_candidate, selected_gate = next(
            row for row in passed if row[0] == ranked_id
        )
        selected_attributes = selected_gate.selector_attributes

    if selected_id is None:
        decision = SelectorDecision(
            schema_version=SELECTOR_DECISION_SCHEMA,
            status="v3_no_valid_candidate",
            selected_candidate_id=None,
            evaluated_candidate_ids=tuple(candidate_ids),
            rejected_candidate_ids=tuple(sorted(rejected_ids)),
            selection_policy_sha256=FROZEN_SELECTOR_POLICY_SHA256,
            selection_attributes_sha256=None,
            v3_success=False,
            v1_fallback_used=False,
            v1_fallback_counts_as_v3_success=False,
            body_free=True,
        )
    else:
        decision = SelectorDecision(
            schema_version=SELECTOR_DECISION_SCHEMA,
            status="selected",
            selected_candidate_id=selected_id,
            evaluated_candidate_ids=tuple(candidate_ids),
            rejected_candidate_ids=tuple(sorted(rejected_ids)),
            selection_policy_sha256=FROZEN_SELECTOR_POLICY_SHA256,
            selection_attributes_sha256=selector_attributes_sha256(
                selected_attributes
            ),
            v3_success=True,
            v1_fallback_used=False,
            v1_fallback_counts_as_v3_success=False,
            body_free=True,
        )
    return SemanticSelectionResult(
        decision=decision,
        gate_results=tuple(row[2] for row in evaluated),
        selected_candidate=selected_candidate,
    )


def select_semantic_candidates(
    candidates: Sequence[SemanticCandidate],
    *,
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
    lexical_authority: RequestLexicalAuthority,
    match_authority: IndependentMatchSourceAuthority,
) -> SemanticSelectionResult:
    result = _select(
        candidates,
        inventory_result=inventory_result,
        content_plan=content_plan,
        lexical_authority=lexical_authority,
        match_authority=match_authority,
    )
    issues = validate_selector_decision_structure(result.decision)
    if issues:
        raise LexicographicSelectorError("SELECTOR_DECISION_CONTRACT_REJECTED")
    return result


def validate_semantic_selection_result(
    value: Any,
    *,
    candidates: Sequence[SemanticCandidate],
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
    lexical_authority: RequestLexicalAuthority,
    match_authority: IndependentMatchSourceAuthority,
) -> tuple[str, ...]:
    try:
        expected = _select(
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
    issues: set[str] = set()
    if type(value) is not SemanticSelectionResult:
        return ("SELECTOR_RESULT_TYPE_INVALID",)
    issues.update(validate_selector_decision_structure(value.decision))
    if value.decision != expected.decision:
        issues.add("SELECTOR_DECISION_RECOMPUTATION_MISMATCH")
    if value.gate_results != expected.gate_results:
        issues.add("SELECTOR_GATE_RESULTS_RECOMPUTATION_MISMATCH")
    if value.selected_candidate is not expected.selected_candidate:
        issues.add("SELECTOR_SELECTED_CANDIDATE_MISMATCH")
    return tuple(sorted(issues))


def selected_candidate_commitment(value: SemanticSelectionResult) -> str | None:
    if type(value) is not SemanticSelectionResult:
        raise LexicographicSelectorError("SELECTOR_RESULT_REQUIRED")
    if value.decision.status != "selected":
        return None
    return artifact_sha256(
        {
            "selected_candidate_id": value.decision.selected_candidate_id,
            "selection_attributes_sha256": (
                value.decision.selection_attributes_sha256
            ),
            "selection_policy_sha256": value.decision.selection_policy_sha256,
        }
    )


__all__ = [
    "LexicographicSelectorError",
    "select_semantic_candidates",
    "selected_candidate_commitment",
    "selector_sort_key",
    "validate_semantic_selection_result",
]
