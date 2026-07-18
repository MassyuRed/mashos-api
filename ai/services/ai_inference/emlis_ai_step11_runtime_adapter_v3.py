# -*- coding: utf-8 -*-
from __future__ import annotations

"""Offline-only runtime adapter for the Step 11 rc0023 surface.

The adapter deliberately leaves the frozen Step 0--10 production path alone.
It rebuilds the established Step 4--6 source lineage, hands only the exact
four-field app projection to the rc0023 forward surface, and accepts bytes only
after the independent rc0023 matcher and hard gate select the candidate.

Body-bearing values live only in the private, ``repr=False`` execution result.
The public helper emits a separately validated body-free summary.
"""

from dataclasses import dataclass
import re
import time
from typing import Any, Mapping

from emlis_ai_content_selection_v3 import build_content_selection_plan
from emlis_ai_current_input_bundle import normalize_emlis_current_input
from emlis_ai_discourse_graph_planner_v3 import (
    DiscourseGraphPlannerError,
    DiscourseGraphPlanSet,
    build_discourse_graph_plans,
)
from emlis_ai_evidence_ledger_service import (
    build_evidence_ledger,
    build_evidence_span_resolver,
)
from emlis_ai_grounded_observation_plan import build_grounded_observation_plan
from emlis_ai_observation_integrator_service import integrate_perspective_board
from emlis_ai_observation_stage_context_v3 import build_observation_stage_context
from emlis_ai_perspective_board import build_perspective_board
from emlis_ai_perspective_observers import run_perspective_observers
from emlis_ai_safety_triage import build_emlis_safety_triage_decision
from emlis_ai_semantic_obligation_inventory_v3 import (
    SemanticObligationInventoryResult,
    build_grounded_source_snapshot,
    build_semantic_obligation_inventory,
)
from emlis_ai_step10_app_reachable_contract_v3 import (
    project_app_reachable_input,
)
from emlis_ai_step11_hard_gate_v3 import (
    Step11SelectionResult,
    evaluate_step11_natural_surface_candidate,
    select_step11_natural_surface_candidates,
)
from emlis_ai_step11_natural_surface_matcher_v3 import (
    match_step11_natural_surface,
    parse_step11_natural_surface,
)
from emlis_ai_step11_natural_surface_v3 import (
    STEP11_CANDIDATE_VERSION_ID,
    Step11NaturalSurfaceCandidate,
    build_step11_natural_surface_candidates,
    project_step11_current_input,
    validate_step11_natural_surface_candidate,
)
from emlis_ai_step11_planning_frontier_v3 import (
    build_step11_terminal_pair_discourse_plans,
)


STEP11_RUNTIME_EXECUTION_SCHEMA = (
    "cocolon.emlis.nls_v3.step11_runtime_execution.v2"
)
STEP11_RUNTIME_SUMMARY_SCHEMA = (
    "cocolon.emlis.nls_v3.step11_runtime_execution_summary.v2"
)
STEP11_RUNTIME_ADAPTER_VERSION = (
    "cocolon.emlis.nls_v3.runtime_adapter.step11.rc0023.v1"
)
STEP11_HISTORICAL_RC0022_RUNTIME_ADAPTER_VERSION = (
    "cocolon.emlis.nls_v3.runtime_adapter.step11.rc0022.v1"
)
STEP11_HISTORICAL_RC0021_RUNTIME_ADAPTER_VERSION = (
    "cocolon.emlis.nls_v3.runtime_adapter.step11.rc0021.v1"
)
STEP11_HISTORICAL_RC0020_RUNTIME_ADAPTER_VERSION = (
    "cocolon.emlis.nls_v3.runtime_adapter.step11.rc0020.v1"
)
STEP11_RUNTIME_EXECUTION_SCOPE = "offline_batch"
STEP11_RUNTIME_CANDIDATE_LIMIT = 12

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_MACHINE_CODE_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,95}$")
_APP_PROJECTION_KEYS = frozenset(
    {"thought_text", "action_text", "emotions", "categories"}
)
_BODY_FREE_FORBIDDEN_KEYS = frozenset(
    {
        "action_text",
        "body",
        "candidate_id",
        "categories",
        "current_input",
        "emotions",
        "final_utf8_bytes",
        "normalized_input",
        "rendered_surface",
        "selected_candidate_id",
        "source_fragments",
        "thought_text",
        "utf8_bytes",
    }
)


class Step11RuntimeAdapterError(ValueError):
    """Fail-closed adapter error containing one closed machine code."""

    def __init__(self, code: str) -> None:
        if type(code) is not str or _MACHINE_CODE_RE.fullmatch(code) is None:
            code = "STEP11_RUNTIME_ERROR_CODE_INVALID"
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True, repr=False)
class Step11RuntimeExecution:
    """Private body-full execution bundle; never a public response object."""

    schema_version: str
    adapter_version: str
    candidate_version_id: str
    execution_scope: str
    status: str
    source_dependency_closure_sha256: str
    normalized_input: dict[str, Any]
    projected_current_input: dict[str, Any]
    observation_stage_context: dict[str, Any]
    grounded_plan: Any
    inventory_result: SemanticObligationInventoryResult
    content_plan: dict[str, Any]
    discourse_plan_set: DiscourseGraphPlanSet
    natural_candidates: tuple[Step11NaturalSurfaceCandidate, ...]
    selection_result: Step11SelectionResult
    final_utf8_bytes: bytes | None
    elapsed_ns: int
    v3_success: bool
    v1_fallback_used: bool
    v1_fallback_counts_as_v3_success: bool

    @property
    def selected_candidate(self) -> Step11NaturalSurfaceCandidate | None:
        candidate = self.selection_result.selected_candidate
        return candidate if type(candidate) is Step11NaturalSurfaceCandidate else None


def _valid_nonzero_sha256(value: Any) -> bool:
    return (
        type(value) is str
        and _SHA256_RE.fullmatch(value) is not None
        and value != "0" * 64
    )


def _build_step11_discourse_plan_set(
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
) -> DiscourseGraphPlanSet:
    """Use the frozen planner first, then one fail-closed rc0023 successor."""

    try:
        return build_discourse_graph_plans(inventory_result, content_plan)
    except DiscourseGraphPlannerError as exc:
        if exc.code != "NO_SAFE_DISCOURSE_STRUCTURE":
            raise
        return build_step11_terminal_pair_discourse_plans(
            inventory_result,
            content_plan,
        )


def _closed_exception_code(exc: Exception) -> str:
    code = getattr(exc, "code", None)
    if type(code) is str and _MACHINE_CODE_RE.fullmatch(code) is not None:
        return code
    return "STEP11_RUNTIME_PIPELINE_REJECTED"


def _project_normalized_current_input(
    normalized_input: Mapping[str, Any],
) -> dict[str, Any]:
    """Create and validate the exact app-reachable four-field projection."""

    if type(normalized_input) is not dict:
        raise Step11RuntimeAdapterError("STEP11_RUNTIME_NORMALIZED_INPUT_INVALID")
    projected = {
        "thought_text": normalized_input.get("memo"),
        "action_text": normalized_input.get("memo_action"),
        "emotions": normalized_input.get("emotion_details"),
        "categories": normalized_input.get("category"),
    }
    if set(projected) != _APP_PROJECTION_KEYS:
        raise Step11RuntimeAdapterError("STEP11_RUNTIME_APP_PROJECTION_INVALID")
    try:
        exact = project_app_reachable_input(projected)
        project_step11_current_input(exact)
    except (KeyError, TypeError, UnicodeError, ValueError) as exc:
        raise Step11RuntimeAdapterError(
            "STEP11_RUNTIME_APP_INPUT_INVALID"
        ) from exc
    if type(exact) is not dict or set(exact) != _APP_PROJECTION_KEYS:
        raise Step11RuntimeAdapterError("STEP11_RUNTIME_APP_PROJECTION_INVALID")
    return exact


def _verified_selected_bytes(
    selection: Step11SelectionResult,
    *,
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
    current_input: Mapping[str, Any],
) -> bytes | None:
    """Return only bytes belonging to the independently gated selection."""

    if type(selection) is not Step11SelectionResult:
        raise Step11RuntimeAdapterError("STEP11_RUNTIME_SELECTION_INVALID")
    if selection.status == "v3_no_valid_candidate":
        if (
            selection.selected_candidate is not None
            or selection.selected_candidate_id is not None
            or any(row.hard_pass is True for row in selection.gate_results)
        ):
            raise Step11RuntimeAdapterError(
                "STEP11_RUNTIME_NO_VALID_SELECTION_INVALID"
            )
        return None
    if selection.status != "selected":
        raise Step11RuntimeAdapterError("STEP11_RUNTIME_SELECTOR_STATUS_INVALID")
    selected = selection.selected_candidate
    if type(selected) is not Step11NaturalSurfaceCandidate:
        raise Step11RuntimeAdapterError("STEP11_RUNTIME_SELECTED_CANDIDATE_INVALID")
    if (
        selected.candidate_version_id != STEP11_CANDIDATE_VERSION_ID
        or selection.selected_candidate_id != selected.candidate_id
    ):
        raise Step11RuntimeAdapterError("STEP11_RUNTIME_SELECTED_ID_INVALID")
    matching_gates = tuple(
        row
        for row in selection.gate_results
        if row.candidate_id == selected.candidate_id
    )
    if len(matching_gates) != 1 or matching_gates[0].hard_pass is not True:
        raise Step11RuntimeAdapterError("STEP11_RUNTIME_SELECTED_GATE_INVALID")
    independently_recomputed_gate = evaluate_step11_natural_surface_candidate(
        selected,
        inventory_result=inventory_result,
        content_plan=content_plan,
        current_input=current_input,
    )
    if independently_recomputed_gate != matching_gates[0]:
        raise Step11RuntimeAdapterError("STEP11_RUNTIME_SELECTED_GATE_MISMATCH")
    candidate_bytes = selected.rendered_surface.utf8_bytes
    if type(candidate_bytes) is not bytes or not candidate_bytes:
        raise Step11RuntimeAdapterError("STEP11_RUNTIME_SELECTED_BYTES_INVALID")
    try:
        decoded = candidate_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise Step11RuntimeAdapterError(
            "STEP11_RUNTIME_SELECTED_UTF8_INVALID"
        ) from exc
    if decoded.encode("utf-8", errors="strict") != candidate_bytes:
        raise Step11RuntimeAdapterError("STEP11_RUNTIME_SELECTED_BYTES_CHANGED")
    return candidate_bytes


def execute_step11_offline_v3(
    current_input: Mapping[str, Any],
    *,
    candidate_version_id: str,
    source_dependency_closure_sha256: str,
    execution_scope: str = STEP11_RUNTIME_EXECUTION_SCOPE,
) -> Step11RuntimeExecution:
    """Run raw app input through rc0023 without touching production ownership."""

    if type(current_input) is not dict:
        raise Step11RuntimeAdapterError("STEP11_RUNTIME_INPUT_MAPPING_REQUIRED")
    if candidate_version_id != STEP11_CANDIDATE_VERSION_ID:
        raise Step11RuntimeAdapterError("STEP11_RUNTIME_CANDIDATE_VERSION_INVALID")
    if execution_scope != STEP11_RUNTIME_EXECUTION_SCOPE:
        raise Step11RuntimeAdapterError("STEP11_RUNTIME_OFFLINE_SCOPE_REQUIRED")
    if not _valid_nonzero_sha256(source_dependency_closure_sha256):
        raise Step11RuntimeAdapterError(
            "STEP11_RUNTIME_SOURCE_DEPENDENCY_CLOSURE_INVALID"
        )

    started = time.perf_counter_ns()
    try:
        normalized_input = normalize_emlis_current_input(dict(current_input))
        projected_input = _project_normalized_current_input(normalized_input)

        evidence_spans = tuple(build_evidence_ledger(normalized_input))
        resolver = build_evidence_span_resolver(
            evidence_spans,
            current_input=normalized_input,
        )
        reports = tuple(run_perspective_observers(evidence_spans))
        board = build_perspective_board(
            evidence_spans=evidence_spans,
            reports=reports,
        )
        graph = integrate_perspective_board(board=board)
        safety_decision = build_emlis_safety_triage_decision(
            current_input=normalized_input,
            graph=graph,
            evidence_spans=evidence_spans,
        )
        grounded_plan = build_grounded_observation_plan(
            normalized_input,
            evidence_spans=evidence_spans,
            reports=reports,
            board=board,
            graph=graph,
            safety_decision=safety_decision,
        )
        stage = build_observation_stage_context(
            stage="normal_observation",
            original_input_bundle=normalized_input,
        )
        snapshot = build_grounded_source_snapshot(
            grounded_plan,
            resolver,
            observation_stage_context=stage,
            original_input_bundle=normalized_input,
        )
        inventory = build_semantic_obligation_inventory(snapshot)
        content_plan = build_content_selection_plan(inventory)
        discourse = _build_step11_discourse_plan_set(inventory, content_plan)
        candidates = build_step11_natural_surface_candidates(
            discourse.plans,
            inventory_result=inventory,
            content_plan=content_plan,
            current_input=projected_input,
        )
        selection = select_step11_natural_surface_candidates(
            candidates,
            inventory_result=inventory,
            content_plan=content_plan,
            current_input=projected_input,
            candidate_limit=STEP11_RUNTIME_CANDIDATE_LIMIT,
        )
        final_bytes = _verified_selected_bytes(
            selection,
            inventory_result=inventory,
            content_plan=content_plan,
            current_input=projected_input,
        )
    except Exception as exc:
        raise Step11RuntimeAdapterError(_closed_exception_code(exc)) from exc

    status = selection.status
    return Step11RuntimeExecution(
        schema_version=STEP11_RUNTIME_EXECUTION_SCHEMA,
        adapter_version=STEP11_RUNTIME_ADAPTER_VERSION,
        candidate_version_id=candidate_version_id,
        execution_scope=execution_scope,
        status=status,
        source_dependency_closure_sha256=source_dependency_closure_sha256,
        normalized_input=normalized_input,
        projected_current_input=projected_input,
        observation_stage_context=stage,
        grounded_plan=grounded_plan,
        inventory_result=inventory,
        content_plan=content_plan,
        discourse_plan_set=discourse,
        natural_candidates=candidates,
        selection_result=selection,
        final_utf8_bytes=final_bytes,
        elapsed_ns=time.perf_counter_ns() - started,
        v3_success=status == "selected",
        v1_fallback_used=False,
        v1_fallback_counts_as_v3_success=False,
    )


def validate_step11_runtime_execution(value: Any) -> tuple[str, ...]:
    """Fully and independently recompute the private rc0023 execution."""

    if type(value) is not Step11RuntimeExecution:
        return ("STEP11_RUNTIME_EXECUTION_TYPE_INVALID",)
    issues: set[str] = set()
    if value.schema_version != STEP11_RUNTIME_EXECUTION_SCHEMA:
        issues.add("STEP11_RUNTIME_EXECUTION_SCHEMA_INVALID")
    if value.adapter_version != STEP11_RUNTIME_ADAPTER_VERSION:
        issues.add("STEP11_RUNTIME_ADAPTER_VERSION_INVALID")
    if value.candidate_version_id != STEP11_CANDIDATE_VERSION_ID:
        issues.add("STEP11_RUNTIME_EXECUTION_CANDIDATE_INVALID")
    if value.execution_scope != STEP11_RUNTIME_EXECUTION_SCOPE:
        issues.add("STEP11_RUNTIME_EXECUTION_SCOPE_INVALID")
    if not _valid_nonzero_sha256(value.source_dependency_closure_sha256):
        issues.add("STEP11_RUNTIME_SOURCE_DEPENDENCY_CLOSURE_INVALID")
    if (
        type(value.elapsed_ns) is not int
        or type(value.elapsed_ns) is bool
        or value.elapsed_ns < 0
    ):
        issues.add("STEP11_RUNTIME_EXECUTION_LATENCY_INVALID")
    if (
        type(value.normalized_input) is not dict
        or type(value.projected_current_input) is not dict
        or set(value.projected_current_input) != _APP_PROJECTION_KEYS
        or type(value.observation_stage_context) is not dict
        or type(value.inventory_result) is not SemanticObligationInventoryResult
        or type(value.content_plan) is not dict
        or type(value.discourse_plan_set) is not DiscourseGraphPlanSet
        or type(value.natural_candidates) is not tuple
        or any(
            type(row) is not Step11NaturalSurfaceCandidate
            for row in value.natural_candidates
        )
        or type(value.selection_result) is not Step11SelectionResult
    ):
        issues.add("STEP11_RUNTIME_PRIVATE_MATERIAL_INVALID")
        return tuple(sorted(issues))

    expected_candidates: tuple[Step11NaturalSurfaceCandidate, ...] | None = None
    expected_selection: Step11SelectionResult | None = None
    try:
        renormalized_input = normalize_emlis_current_input(
            dict(value.normalized_input)
        )
        expected_projection = _project_normalized_current_input(
            value.normalized_input
        )

        expected_spans = tuple(build_evidence_ledger(value.normalized_input))
        expected_resolver = build_evidence_span_resolver(
            expected_spans,
            current_input=value.normalized_input,
        )
        expected_reports = tuple(run_perspective_observers(expected_spans))
        expected_board = build_perspective_board(
            evidence_spans=expected_spans,
            reports=expected_reports,
        )
        expected_graph = integrate_perspective_board(board=expected_board)
        expected_safety = build_emlis_safety_triage_decision(
            current_input=value.normalized_input,
            graph=expected_graph,
            evidence_spans=expected_spans,
        )
        expected_grounded_plan = build_grounded_observation_plan(
            value.normalized_input,
            evidence_spans=expected_spans,
            reports=expected_reports,
            board=expected_board,
            graph=expected_graph,
            safety_decision=expected_safety,
        )
        expected_stage = build_observation_stage_context(
            stage="normal_observation",
            original_input_bundle=value.normalized_input,
        )
        expected_snapshot = build_grounded_source_snapshot(
            expected_grounded_plan,
            expected_resolver,
            observation_stage_context=expected_stage,
            original_input_bundle=value.normalized_input,
        )
        expected_inventory = build_semantic_obligation_inventory(
            expected_snapshot
        )
        expected_content_plan = build_content_selection_plan(expected_inventory)
        expected_discourse = _build_step11_discourse_plan_set(
            expected_inventory,
            expected_content_plan,
        )
        expected_candidates = build_step11_natural_surface_candidates(
            expected_discourse.plans,
            inventory_result=expected_inventory,
            content_plan=expected_content_plan,
            current_input=expected_projection,
        )
        for candidate in expected_candidates:
            candidate_issues = validate_step11_natural_surface_candidate(
                candidate,
                inventory_result=expected_inventory,
                content_plan=expected_content_plan,
                current_input=expected_projection,
            )
            if candidate_issues:
                raise Step11RuntimeAdapterError(
                    "STEP11_RUNTIME_CANDIDATE_REVALIDATION_FAILED"
                )
        expected_selection = select_step11_natural_surface_candidates(
            expected_candidates,
            inventory_result=expected_inventory,
            content_plan=expected_content_plan,
            current_input=expected_projection,
            candidate_limit=STEP11_RUNTIME_CANDIDATE_LIMIT,
        )
        expected_final_bytes = _verified_selected_bytes(
            expected_selection,
            inventory_result=expected_inventory,
            content_plan=expected_content_plan,
            current_input=expected_projection,
        )
    except Exception:
        issues.add("STEP11_RUNTIME_SOURCE_LINEAGE_INVALID")
    else:
        if renormalized_input != value.normalized_input:
            issues.add("STEP11_RUNTIME_NORMALIZED_INPUT_MISMATCH")
        if expected_projection != value.projected_current_input:
            issues.add("STEP11_RUNTIME_APP_PROJECTION_MISMATCH")
        if (
            expected_stage != value.observation_stage_context
            or expected_grounded_plan != value.grounded_plan
            or expected_inventory != value.inventory_result
            or expected_content_plan != value.content_plan
            or expected_discourse != value.discourse_plan_set
            or expected_candidates != value.natural_candidates
            or expected_selection != value.selection_result
        ):
            issues.add("STEP11_RUNTIME_SOURCE_LINEAGE_MISMATCH")
        if expected_final_bytes != value.final_utf8_bytes:
            issues.add("STEP11_RUNTIME_VERIFIED_FINAL_BYTES_MISMATCH")

    selection = value.selection_result
    if (
        selection.candidate_version_id != STEP11_CANDIDATE_VERSION_ID
        or selection.bounded_candidate_limit != STEP11_RUNTIME_CANDIDATE_LIMIT
        or selection.recovery_attempted is not False
        or selection.v1_fallback_used is not False
    ):
        issues.add("STEP11_RUNTIME_SELECTION_BOUNDARY_INVALID")
    candidate_ids = tuple(row.candidate_id for row in value.natural_candidates)
    if (
        candidate_ids != tuple(sorted(candidate_ids))
        or len(candidate_ids) != len(set(candidate_ids))
        or selection.evaluated_candidate_ids != candidate_ids
        or tuple(row.candidate_id for row in selection.gate_results)
        != candidate_ids
    ):
        issues.add("STEP11_RUNTIME_CANDIDATE_SET_MISMATCH")

    selected_status = selection.status == "selected"
    if value.status != selection.status:
        issues.add("STEP11_RUNTIME_STATUS_MISMATCH")
    if selected_status:
        selected = selection.selected_candidate
        matching_gates = tuple(
            row
            for row in selection.gate_results
            if row.candidate_id == selection.selected_candidate_id
        )
        if (
            type(selected) is not Step11NaturalSurfaceCandidate
            or selection.selected_candidate_id
            != getattr(selected, "candidate_id", None)
            or len(matching_gates) != 1
            or matching_gates[0].hard_pass is not True
            or value.final_utf8_bytes
            != getattr(getattr(selected, "rendered_surface", None), "utf8_bytes", None)
        ):
            issues.add("STEP11_RUNTIME_SELECTED_GATE_BYTES_MISMATCH")
        elif type(value.final_utf8_bytes) is not bytes or not value.final_utf8_bytes:
            issues.add("STEP11_RUNTIME_SELECTED_BYTES_INVALID")
        else:
            try:
                if (
                    value.final_utf8_bytes.decode("utf-8", errors="strict").encode(
                        "utf-8", errors="strict"
                    )
                    != value.final_utf8_bytes
                ):
                    issues.add("STEP11_RUNTIME_SELECTED_BYTES_CHANGED")
                independent_gate = evaluate_step11_natural_surface_candidate(
                    selected,
                    inventory_result=value.inventory_result,
                    content_plan=value.content_plan,
                    current_input=value.projected_current_input,
                )
                if independent_gate != matching_gates[0]:
                    issues.add("STEP11_RUNTIME_SELECTED_GATE_MISMATCH")
            except Exception:
                issues.add("STEP11_RUNTIME_SELECTED_REVALIDATION_FAILED")
    elif selection.status == "v3_no_valid_candidate":
        if (
            selection.selected_candidate is not None
            or selection.selected_candidate_id is not None
            or value.final_utf8_bytes is not None
            or any(row.hard_pass is True for row in selection.gate_results)
        ):
            issues.add("STEP11_RUNTIME_NO_VALID_SELECTION_INVALID")
    else:
        issues.add("STEP11_RUNTIME_EXECUTION_STATUS_INVALID")

    if (
        value.v3_success is not selected_status
        or value.v1_fallback_used is not False
        or value.v1_fallback_counts_as_v3_success is not False
    ):
        issues.add("STEP11_RUNTIME_SUCCESS_BOUNDARY_INVALID")
    return tuple(sorted(issues))


def _scan_body_free_summary(value: Any, path: str = "$") -> tuple[str, ...]:
    issues: list[str] = []
    if type(value) is dict:
        for key, child in value.items():
            if type(key) is not str:
                issues.append(f"STEP11_BODY_FREE_NON_STRING_KEY:{path}")
                continue
            if key in _BODY_FREE_FORBIDDEN_KEYS:
                issues.append(f"STEP11_BODY_FREE_FORBIDDEN_KEY:{path}.{key}")
            issues.extend(_scan_body_free_summary(child, f"{path}.{key}"))
    elif type(value) is list:
        for index, child in enumerate(value):
            issues.extend(_scan_body_free_summary(child, f"{path}[{index}]"))
    elif type(value) not in {str, int, bool, type(None)}:
        issues.append(f"STEP11_BODY_FREE_VALUE_TYPE_INVALID:{path}")
    return tuple(issues)


def runtime_execution_body_free_summary(
    execution: Step11RuntimeExecution,
) -> dict[str, Any]:
    """Return structural metrics without input, response, IDs, or body hashes."""

    issues = validate_step11_runtime_execution(execution)
    if issues:
        raise Step11RuntimeAdapterError(issues[0])

    selection = execution.selection_result
    selected = execution.selected_candidate
    required_ids = execution.inventory_result.ledger.get(
        "required_obligation_ids", []
    )
    required_count = len(required_ids) if type(required_ids) is list else 0
    semantic_atom_count = 0
    bound_obligation_count = 0
    integrated_relation_count = 0
    integrated_unknown_count = 0
    source_fragment_count = 0
    sentence_count = 0
    section_count = 0
    if selected is not None:
        try:
            witness = parse_step11_natural_surface(
                selected.rendered_surface.utf8_bytes
            )
            binding = match_step11_natural_surface(
                witness,
                inventory_result=execution.inventory_result,
                content_plan=execution.content_plan,
                discourse_plan=selected.discourse_plan,
                current_input=execution.projected_current_input,
            )
        except Exception as exc:
            raise Step11RuntimeAdapterError(
                "STEP11_RUNTIME_SUMMARY_RECOMPUTATION_FAILED"
            ) from exc
        semantic_atom_count = len(witness.atoms)
        bound_obligation_count = len(binding.binding_rows)
        integrated_relation_count = len(binding.integrated_relation_ids)
        integrated_unknown_count = len(binding.integrated_unknown_ids)
        source_fragment_count = binding.source_fragment_count
        sentence_count = len(selected.surface_ast.sentences)
        section_count = len(
            {row.section_role for row in selected.surface_ast.sentences}
        )

    failure_code_counts: dict[str, int] = {}
    for gate in selection.gate_results:
        for code in gate.failure_codes:
            if type(code) is not str or _MACHINE_CODE_RE.fullmatch(code) is None:
                raise Step11RuntimeAdapterError(
                    "STEP11_RUNTIME_GATE_FAILURE_CODE_INVALID"
                )
            failure_code_counts[code] = failure_code_counts.get(code, 0) + 1

    summary = {
        "schema_version": STEP11_RUNTIME_SUMMARY_SCHEMA,
        "adapter_version": execution.adapter_version,
        "candidate_version_id": execution.candidate_version_id,
        "execution_scope": execution.execution_scope,
        "status": execution.status,
        "source_dependency_closure_sha256": (
            execution.source_dependency_closure_sha256
        ),
        "selected_candidate_present": selected is not None,
        "evaluated_candidate_count": len(selection.evaluated_candidate_ids),
        "rejected_candidate_count": sum(
            gate.hard_pass is not True for gate in selection.gate_results
        ),
        "hard_gate_pass_count": sum(
            gate.hard_pass is True for gate in selection.gate_results
        ),
        "hard_gate_failure_code_counts": dict(sorted(failure_code_counts.items())),
        "recovery_attempt_count": 0,
        "latency_ns": execution.elapsed_ns,
        "semantic_metrics": {
            "required_obligation_count": required_count,
            "bound_obligation_count": bound_obligation_count,
            "semantic_atom_count": semantic_atom_count,
            "integrated_relation_count": integrated_relation_count,
            "integrated_unknown_count": integrated_unknown_count,
            "source_fragment_count": source_fragment_count,
            "section_count": section_count,
            "sentence_count": sentence_count,
            "depth": execution.content_plan.get("depth"),
        },
        "v3_success": execution.v3_success,
        "v1_fallback_used": execution.v1_fallback_used,
        "v1_fallback_counts_as_v3_success": (
            execution.v1_fallback_counts_as_v3_success
        ),
        "body_free": True,
    }
    if _scan_body_free_summary(summary):
        raise Step11RuntimeAdapterError(
            "STEP11_RUNTIME_SUMMARY_CONTAINS_PRIVATE_BODY"
        )
    return summary


__all__ = [
    "STEP11_HISTORICAL_RC0020_RUNTIME_ADAPTER_VERSION",
    "STEP11_HISTORICAL_RC0021_RUNTIME_ADAPTER_VERSION",
    "STEP11_HISTORICAL_RC0022_RUNTIME_ADAPTER_VERSION",
    "STEP11_RUNTIME_ADAPTER_VERSION",
    "STEP11_RUNTIME_CANDIDATE_LIMIT",
    "STEP11_RUNTIME_EXECUTION_SCHEMA",
    "STEP11_RUNTIME_EXECUTION_SCOPE",
    "STEP11_RUNTIME_SUMMARY_SCHEMA",
    "Step11RuntimeAdapterError",
    "Step11RuntimeExecution",
    "execute_step11_offline_v3",
    "runtime_execution_body_free_summary",
    "validate_step11_runtime_execution",
]
