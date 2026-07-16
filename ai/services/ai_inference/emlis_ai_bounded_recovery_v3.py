# -*- coding: utf-8 -*-
from __future__ import annotations

"""Bounded Step 9 recovery without post-render string repair."""

from typing import Any, Mapping, Sequence

from emlis_ai_canonical_renderer_v3 import RequestLexicalAuthority
from emlis_ai_discourse_graph_planner_v3 import (
    DiscourseGraphPlannerError,
    build_discourse_graph_plans,
)
from emlis_ai_independent_semantic_matcher_v3 import IndependentMatchSourceAuthority
from emlis_ai_lexicographic_selector_v3 import (
    LexicographicSelectorError,
    select_semantic_candidates,
)
from emlis_ai_nls_v3_artifact_contract import artifact_sha256
from emlis_ai_semantic_hard_gate_v3 import (
    SemanticHardGateError,
    build_semantic_candidate,
    derive_semantic_candidate_id,
    hard_gate_failure_codes,
)
from emlis_ai_semantic_obligation_inventory_v3 import (
    SemanticObligationInventoryResult,
)
from emlis_ai_step9_artifact_contract_v3 import (
    BoundedRecoveryResult,
    FROZEN_RECOVERY_POLICY_SHA256,
    RECOVERY_POLICY,
    RECOVERY_TRACE_SCHEMA,
    RecoveryAttempt,
    RecoveryTrace,
    SemanticCandidate,
    validate_recovery_trace_structure,
    validate_step9_policies,
)


class BoundedRecoveryError(ValueError):
    """Fail-closed recovery error containing no candidate or input body."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _topology_key(plan: Mapping[str, Any]) -> str | None:
    try:
        return artifact_sha256(
            {
                "nodes": plan.get("nodes"),
                "edges": plan.get("edges"),
            }
        )
    except (
        AttributeError,
        KeyError,
        RecursionError,
        TypeError,
        ValueError,
        UnicodeError,
    ):
        return None


def _safe_plan_hash(plan: Any) -> str | None:
    try:
        return artifact_sha256(plan)
    except (
        AttributeError,
        KeyError,
        RecursionError,
        TypeError,
        ValueError,
        UnicodeError,
    ):
        return None


def _dict_rows(value: Any) -> list[dict[str, Any]]:
    if type(value) is not list:
        return []
    return [row for row in value if type(row) is dict]


def _string_set(value: Any) -> set[str]:
    if type(value) is not list:
        return set()
    return {item for item in value if type(item) is str}


def _flattened_node_order(plan: Mapping[str, Any]) -> tuple[str, ...]:
    if type(plan) is not dict:
        return ()
    result: list[str] = []
    for group in _dict_rows(plan.get("sentence_groups")):
        node_ids = group.get("node_ids")
        if type(node_ids) is list:
            result.extend(item for item in node_ids if type(item) is str)
    return tuple(result)


def _group_count(plan: Mapping[str, Any]) -> int:
    if type(plan) is not dict:
        return 0
    groups = plan.get("sentence_groups", [])
    return len(groups) if type(groups) is list else 0


def _max_group_width(plan: Mapping[str, Any]) -> int:
    if type(plan) is not dict:
        return 0
    groups = plan.get("sentence_groups", [])
    if type(groups) is not list or not groups:
        return 0
    return max(
        len(group.get("node_ids", []))
        if type(group) is dict and type(group.get("node_ids")) is list
        else 0
        for group in groups
    )


def _plan_order_key(plan: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        _max_group_width(plan),
        -_group_count(plan),
        str(plan.get("structural_signature", "")).encode("ascii", errors="ignore"),
        artifact_sha256(plan).encode("ascii"),
    )


def _required_complete(
    plan: Mapping[str, Any],
    *,
    required: set[str],
) -> bool:
    if type(plan) is not dict:
        return False
    obligation_ids = {
        row.get("obligation_id")
        for row in _dict_rows(plan.get("nodes"))
        if type(row.get("obligation_id")) is str
    }
    return obligation_ids == required


def _recover(
    initial_candidates: Sequence[SemanticCandidate],
    *,
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
    lexical_authority: RequestLexicalAuthority,
    match_authority: IndependentMatchSourceAuthority,
) -> BoundedRecoveryResult:
    if type(initial_candidates) not in {list, tuple}:
        raise BoundedRecoveryError("RECOVERY_CANDIDATE_SEQUENCE_REQUIRED")
    if validate_step9_policies():
        raise BoundedRecoveryError("RECOVERY_POLICY_DRIFT")
    if len(initial_candidates) > RECOVERY_POLICY[
        "candidate_total_limit_including_initial"
    ]:
        raise BoundedRecoveryError("RECOVERY_INITIAL_LIMIT_EXCEEDED")
    if any(type(candidate) is not SemanticCandidate for candidate in initial_candidates):
        raise BoundedRecoveryError("RECOVERY_CANDIDATE_TYPE_INVALID")

    try:
        initial_selection = select_semantic_candidates(
            initial_candidates,
            inventory_result=inventory_result,
            content_plan=content_plan,
            lexical_authority=lexical_authority,
            match_authority=match_authority,
        )
    except (LexicographicSelectorError, SemanticHardGateError) as exc:
        raise BoundedRecoveryError("RECOVERY_INITIAL_SELECTION_REJECTED") from exc

    initial_ids = tuple(
        sorted(
            derive_semantic_candidate_id(
                candidate,
                inventory_result=inventory_result,
            )
            for candidate in initial_candidates
        )
    )
    if initial_selection.decision.status == "selected":
        trace = RecoveryTrace(
            schema_version=RECOVERY_TRACE_SCHEMA,
            recovery_policy_sha256=FROZEN_RECOVERY_POLICY_SHA256,
            initial_candidate_ids=initial_ids,
            attempts=(),
            total_candidate_count=len(initial_candidates),
            planner_rebuild_count=0,
            final_status="selected",
            selected_candidate_id=initial_selection.decision.selected_candidate_id,
            v3_success=True,
            v1_fallback_used=False,
            v1_fallback_counts_as_v3_success=False,
            body_free=True,
        )
        return BoundedRecoveryResult(selection=initial_selection, trace=trace)

    planner_rebuild_count = 0
    try:
        plan_set = build_discourse_graph_plans(inventory_result, content_plan)
        planner_rebuild_count = 1
    except (DiscourseGraphPlannerError, AttributeError, KeyError, TypeError, ValueError):
        plan_set = None

    candidates = list(initial_candidates)
    seen = set(initial_ids)
    raw_attempts: list[RecoveryAttempt] = []
    limit = RECOVERY_POLICY["candidate_total_limit_including_initial"]

    def add_plan(
        plan: Mapping[str, Any],
        *,
        lane: str,
        source_candidate_id: str | None,
    ) -> bool:
        if len(candidates) >= limit:
            raw_attempts.append(
                RecoveryAttempt(
                    lane=lane,
                    candidate_id=None,
                    source_candidate_id=source_candidate_id,
                    status="unavailable",
                    failure_codes=("RECOVERY_BUDGET_EXHAUSTED",),
                )
            )
            return False
        try:
            rebuilt = build_semantic_candidate(
                plan,
                inventory_result=inventory_result,
                content_plan=content_plan,
                lexical_authority=lexical_authority,
                match_authority=match_authority,
            )
            candidate_id = derive_semantic_candidate_id(
                rebuilt,
                inventory_result=inventory_result,
            )
        except (
            AttributeError,
            KeyError,
            SemanticHardGateError,
            TypeError,
            ValueError,
            UnicodeError,
        ):
            raw_attempts.append(
                RecoveryAttempt(
                    lane=lane,
                    candidate_id=None,
                    source_candidate_id=source_candidate_id,
                    status="unavailable",
                    failure_codes=("RECOVERY_CANONICAL_REBUILD_FAILED",),
                )
            )
            return False
        if candidate_id in seen:
            raw_attempts.append(
                RecoveryAttempt(
                    lane=lane,
                    candidate_id=None,
                    source_candidate_id=source_candidate_id,
                    status="unavailable",
                    failure_codes=("RECOVERY_DUPLICATE_CANDIDATE_SKIPPED",),
                )
            )
            return False
        candidates.append(rebuilt)
        seen.add(candidate_id)
        raw_attempts.append(
            RecoveryAttempt(
                lane=lane,
                candidate_id=candidate_id,
                source_candidate_id=source_candidate_id,
                status="candidate_built",
                failure_codes=(),
            )
        )
        return True

    def current_selection():
        return select_semantic_candidates(
            candidates,
            inventory_result=inventory_result,
            content_plan=content_plan,
            lexical_authority=lexical_authority,
            match_authority=match_authority,
        )

    final_selection = initial_selection
    plans = tuple(plan_set.plans) if plan_set is not None else ()
    plan_hashes = {artifact_sha256(plan): plan for plan in plans}

    # Lane 1: rollback each failed private bundle to the frozen canonical chain.
    topology_limit = RECOVERY_POLICY[
        "same_semantic_topology_recovery_limit"
    ]
    topology_attempts = 0
    initial_keyed = sorted(
        (
            derive_semantic_candidate_id(
                candidate,
                inventory_result=inventory_result,
            ),
            candidate,
        )
        for candidate in initial_candidates
    )
    for source_id, source in initial_keyed:
        if topology_attempts >= topology_limit or len(candidates) >= limit:
            break
        topology_attempts += 1
        trusted_plan = plan_hashes.get(_safe_plan_hash(source.discourse_plan))
        if trusted_plan is None:
            raw_attempts.append(
                RecoveryAttempt(
                    lane="same_semantic_topology_safer_layout",
                    candidate_id=None,
                    source_candidate_id=source_id,
                    status="unavailable",
                    failure_codes=("RECOVERY_SOURCE_PLAN_NOT_TRUSTED",),
                )
            )
            continue
        add_plan(
            trusted_plan,
            lane="same_semantic_topology_safer_layout",
            source_candidate_id=source_id,
        )
    if len(candidates) > len(initial_candidates):
        final_selection = current_selection()

    # Lane 2: same topology/order, with a strictly safer sentence split.
    if final_selection.decision.status != "selected" and len(candidates) < limit:
        split_plans: dict[str, Mapping[str, Any]] = {}
        for _source_id, source in initial_keyed:
            source_topology = _topology_key(source.discourse_plan)
            source_order = _flattened_node_order(source.discourse_plan)
            source_groups = _group_count(source.discourse_plan)
            for plan in plans:
                if (
                    _topology_key(plan) == source_topology
                    and _flattened_node_order(plan) == source_order
                    and _group_count(plan) > source_groups
                ):
                    split_plans[artifact_sha256(plan)] = plan
        for plan in sorted(split_plans.values(), key=_plan_order_key):
            if len(candidates) >= limit:
                break
            add_plan(
                plan,
                lane="safe_split",
                source_candidate_id=None,
            )
        if any(attempt.lane == "safe_split" for attempt in raw_attempts):
            final_selection = current_selection()
        elif plans:
            raw_attempts.append(
                RecoveryAttempt(
                    lane="safe_split",
                    candidate_id=None,
                    source_candidate_id=None,
                    status="unavailable",
                    failure_codes=("NO_SAFE_SPLIT_ALTERNATIVE",),
                )
            )

    # Lane 3: current Step 5 has already deferred every optional obligation.
    if final_selection.decision.status != "selected" and len(candidates) < limit:
        ledger = (
            inventory_result.ledger
            if type(inventory_result) is SemanticObligationInventoryResult
            and type(inventory_result.ledger) is dict
            else {}
        )
        required = _string_set(ledger.get("required_obligation_ids"))
        safe_content_plan = content_plan if type(content_plan) is dict else {}
        active = {
            row.get("obligation_id")
            for row in _dict_rows(safe_content_plan.get("decisions"))
            if type(row.get("obligation_id")) is str
            and row.get("status") in ("selected", "integrated_into")
        }
        minimal = [
            plan
            for plan in plans
            if active == required and _required_complete(plan, required=required)
        ]
        minimal.sort(
            key=lambda plan: (
                _group_count(plan),
                _max_group_width(plan),
                str(plan.get("structural_signature", "")),
            )
        )
        built = False
        for plan in minimal:
            if len(candidates) >= limit:
                break
            if add_plan(
                plan,
                lane="minimal_required_complete",
                source_candidate_id=None,
            ):
                built = True
                break
        if built:
            final_selection = current_selection()
        else:
            raw_attempts.append(
                RecoveryAttempt(
                    lane="minimal_required_complete",
                    candidate_id=None,
                    source_candidate_id=None,
                    status="unavailable",
                    failure_codes=(
                        "MINIMAL_REQUIRED_COMPLETE_CANDIDATE_UNAVAILABLE",
                    ),
                )
            )

    gate_by_id = {
        row.candidate_id: row for row in final_selection.gate_results
    }
    attempts: list[RecoveryAttempt] = []
    for attempt in raw_attempts:
        gate = gate_by_id.get(attempt.candidate_id)
        if attempt.candidate_id is None or gate is None:
            attempts.append(attempt)
        elif gate.hard_pass:
            attempts.append(attempt)
        else:
            attempts.append(
                RecoveryAttempt(
                    lane=attempt.lane,
                    candidate_id=attempt.candidate_id,
                    source_candidate_id=attempt.source_candidate_id,
                    status="rejected",
                    failure_codes=hard_gate_failure_codes(gate),
                )
            )
    status = final_selection.decision.status
    trace = RecoveryTrace(
        schema_version=RECOVERY_TRACE_SCHEMA,
        recovery_policy_sha256=FROZEN_RECOVERY_POLICY_SHA256,
        initial_candidate_ids=initial_ids,
        attempts=tuple(attempts),
        total_candidate_count=len(candidates),
        planner_rebuild_count=planner_rebuild_count,
        final_status=status,
        selected_candidate_id=final_selection.decision.selected_candidate_id,
        v3_success=status == "selected",
        v1_fallback_used=False,
        v1_fallback_counts_as_v3_success=False,
        body_free=True,
    )
    return BoundedRecoveryResult(selection=final_selection, trace=trace)


def select_with_bounded_recovery(
    initial_candidates: Sequence[SemanticCandidate],
    *,
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
    lexical_authority: RequestLexicalAuthority,
    match_authority: IndependentMatchSourceAuthority,
) -> BoundedRecoveryResult:
    result = _recover(
        initial_candidates,
        inventory_result=inventory_result,
        content_plan=content_plan,
        lexical_authority=lexical_authority,
        match_authority=match_authority,
    )
    issues = validate_recovery_trace_structure(result.trace)
    if issues:
        raise BoundedRecoveryError("RECOVERY_TRACE_CONTRACT_REJECTED")
    return result


def validate_bounded_recovery_result(
    value: Any,
    *,
    initial_candidates: Sequence[SemanticCandidate],
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
    lexical_authority: RequestLexicalAuthority,
    match_authority: IndependentMatchSourceAuthority,
) -> tuple[str, ...]:
    try:
        expected = _recover(
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


__all__ = [
    "BoundedRecoveryError",
    "select_with_bounded_recovery",
    "validate_bounded_recovery_result",
]
