# -*- coding: utf-8 -*-
from __future__ import annotations

"""Disconnected runtime composition for the rc0029 Step 11 experiment.

This module is intentionally absent from every shared-runtime and public-route
import graph.  Existing owners are imported only inside the experiment entry
point.  Body-bearing input, candidates, parsed witnesses, bindings, and final
bytes remain local to that call; the returned value is a closed body-free
receipt suitable for the bounded experiment tool.
"""

from dataclasses import dataclass
import re
from typing import Any, Mapping


STEP11_RC0029_EXPERIMENT_RUNTIME_RESULT_SCHEMA = (
    "cocolon.emlis.nls_v3.step11.rc0029_experiment_runtime_result.v1"
)
STEP11_RC0029_EXPERIMENT_PRIVATE_EXECUTION_SCHEMA = (
    "cocolon.emlis.nls_v3.step11.rc0029_experiment_private_execution.v1"
)
STEP11_RC0029_EXPERIMENT_RUNTIME_ADAPTER_VERSION = (
    "cocolon.emlis.nls_v3.runtime_adapter.step11.rc0029.experiment."
    "20260719.v1"
)
STEP11_RC0029_EXPERIMENT_EXECUTION_SCOPE = "offline_bounded_experiment"
STEP11_RC0029_BASE_CANDIDATE_VERSION_ID = "nls_v3_rc_0027"
STEP11_RC0029_EXPERIMENT_CANDIDATE_VERSION_ID = (
    "nls_v3_rc_0029_experiment"
)
STEP11_RC0029_MAX_CANDIDATES = 12
STEP11_RC0029_MAX_REPLANS = 1

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_CASE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,95}$")
_CLOSED_CODE_RE = re.compile(r"^STEP11_RC0029_[A-Z0-9_]{2,79}$")
_SHAREABLE_FAILURE_CODE_RE = re.compile(
    r"^(?:STEP11_RC0029_[A-Z0-9_]{2,79}|S11_GATE[A-Z0-9_]{0,120})$"
)
_DISPOSITIONS = frozenset({"selected", "no_valid_candidate", "fail_close"})


class Step11Rc0029ExperimentRuntimeError(ValueError):
    """Caller-contract error containing one closed rc0029 code."""

    def __init__(self, code: str) -> None:
        if type(code) is not str or _CLOSED_CODE_RE.fullmatch(code) is None:
            code = "STEP11_RC0029_RUNTIME_ERROR_CODE_INVALID"
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class Step11Rc0029ExperimentBodyFreeResult:
    """Shareable structural receipt; it owns no source or output body."""

    schema_version: str
    adapter_version: str
    execution_scope: str
    case_id: str
    source_case_commitment: str
    source_dependency_closure_sha256: str
    base_candidate_version_id: str
    experiment_candidate_version_id: str
    base_disposition: str
    disposition: str
    closed_failure_codes: tuple[str, ...]
    gate_failure_code_counts: tuple[tuple[str, int], ...]
    bounded_candidate_limit: int
    bounded_replan_limit: int
    base_candidate_count: int
    experiment_candidate_count: int
    evaluated_candidate_count: int
    hard_gate_pass_count: int
    rejected_candidate_count: int
    replan_count: int
    selected_candidate_present: bool
    successor_snapshot_sha256: str | None
    successor_authority_sha256: str | None
    successor_witness_sha256: str | None
    lexical_atom_specs_sha256: str | None
    surface_catalog_sha256: str | None
    owner_binding_count: int
    construction_atom_count: int
    relation_endpoint_atom_count: int
    semantic_link_atom_count: int
    explicit_unknown_atom_count: int
    semantic_coverage_authority: str
    result_sha256: str
    experimental_only: bool = True
    body_free: bool = True
    runtime_connected: bool = False


# Descriptive compatibility name for callers that treat this as the runtime
# result while still receiving the exact same body-free dataclass type.
Step11Rc0029ExperimentRuntimeResult = (
    Step11Rc0029ExperimentBodyFreeResult
)


@dataclass(frozen=True, slots=True, repr=False)
class Step11Rc0029ExperimentPrivateExecution:
    """Request-local body-full execution; never a shareable response value."""

    schema_version: str
    adapter_version: str
    case_id: str
    source_case_commitment: str
    source_dependency_closure_sha256: str
    base_execution: Any | None
    successor_snapshot: Any | None
    lexical_atom_specs: Any | None
    experiment_candidates: tuple[Any, ...]
    parsed_witnesses: tuple[Any, ...]
    verified_bindings: tuple[Any, ...]
    gate_results: tuple[Any, ...]
    selection_result: Any | None
    selected_final_utf8_bytes: bytes | None
    selected_parsed_witness: Any | None
    selected_verified_binding: Any | None
    body_free_result: Step11Rc0029ExperimentBodyFreeResult
    private_body_full: bool = True
    shareable: bool = False
    experimental_only: bool = True
    runtime_connected: bool = False


def _valid_sha256(value: Any) -> bool:
    return (
        type(value) is str
        and _SHA256_RE.fullmatch(value) is not None
        and value != "0" * 64
    )


def _closed_pipeline_code(error: BaseException) -> str:
    code = getattr(error, "code", None)
    if type(code) is str and _CLOSED_CODE_RE.fullmatch(code) is not None:
        return code
    if type(code) is str and code.startswith("STEP11_RUNTIME_"):
        return "STEP11_RC0029_BASE_RUNTIME_FAIL_CLOSE"
    return "STEP11_RC0029_PIPELINE_FAIL_CLOSE"


def _result_payload(
    value: Step11Rc0029ExperimentBodyFreeResult,
) -> dict[str, Any]:
    return {
        "schema_version": value.schema_version,
        "adapter_version": value.adapter_version,
        "execution_scope": value.execution_scope,
        "case_id": value.case_id,
        "source_case_commitment": value.source_case_commitment,
        "source_dependency_closure_sha256": (
            value.source_dependency_closure_sha256
        ),
        "base_candidate_version_id": value.base_candidate_version_id,
        "experiment_candidate_version_id": (
            value.experiment_candidate_version_id
        ),
        "base_disposition": value.base_disposition,
        "disposition": value.disposition,
        "closed_failure_codes": list(value.closed_failure_codes),
        "gate_failure_code_counts": [
            {"code": code, "count": count}
            for code, count in value.gate_failure_code_counts
        ],
        "bounded_candidate_limit": value.bounded_candidate_limit,
        "bounded_replan_limit": value.bounded_replan_limit,
        "base_candidate_count": value.base_candidate_count,
        "experiment_candidate_count": value.experiment_candidate_count,
        "evaluated_candidate_count": value.evaluated_candidate_count,
        "hard_gate_pass_count": value.hard_gate_pass_count,
        "rejected_candidate_count": value.rejected_candidate_count,
        "replan_count": value.replan_count,
        "selected_candidate_present": value.selected_candidate_present,
        "successor_snapshot_sha256": value.successor_snapshot_sha256,
        "successor_authority_sha256": value.successor_authority_sha256,
        "successor_witness_sha256": value.successor_witness_sha256,
        "lexical_atom_specs_sha256": value.lexical_atom_specs_sha256,
        "surface_catalog_sha256": value.surface_catalog_sha256,
        "owner_binding_count": value.owner_binding_count,
        "construction_atom_count": value.construction_atom_count,
        "relation_endpoint_atom_count": value.relation_endpoint_atom_count,
        "semantic_link_atom_count": value.semantic_link_atom_count,
        "explicit_unknown_atom_count": value.explicit_unknown_atom_count,
        "semantic_coverage_authority": value.semantic_coverage_authority,
        "experimental_only": value.experimental_only,
        "body_free": value.body_free,
        "runtime_connected": value.runtime_connected,
    }


def _payload_sha256(value: Mapping[str, Any]) -> str:
    # Local import keeps this experiment adapter absent from the default graph.
    from emlis_ai_nls_v3_artifact_contract import artifact_sha256

    return artifact_sha256(dict(value))


def _make_result(
    *,
    case_id: str,
    source_case_commitment: str,
    source_dependency_closure_sha256: str,
    base_disposition: str,
    disposition: str,
    closed_failure_codes: tuple[str, ...] = (),
    gate_failure_code_counts: tuple[tuple[str, int], ...] = (),
    bounded_candidate_limit: int,
    bounded_replan_limit: int,
    base_candidate_count: int = 0,
    experiment_candidate_count: int = 0,
    evaluated_candidate_count: int = 0,
    hard_gate_pass_count: int = 0,
    rejected_candidate_count: int = 0,
    replan_count: int = 0,
    selected_candidate_present: bool = False,
    successor_snapshot_sha256: str | None = None,
    successor_authority_sha256: str | None = None,
    successor_witness_sha256: str | None = None,
    lexical_atom_specs_sha256: str | None = None,
    surface_catalog_sha256: str | None = None,
    owner_binding_count: int = 0,
    construction_atom_count: int = 0,
    relation_endpoint_atom_count: int = 0,
    semantic_link_atom_count: int = 0,
    explicit_unknown_atom_count: int = 0,
) -> Step11Rc0029ExperimentBodyFreeResult:
    provisional = Step11Rc0029ExperimentBodyFreeResult(
        schema_version=STEP11_RC0029_EXPERIMENT_RUNTIME_RESULT_SCHEMA,
        adapter_version=STEP11_RC0029_EXPERIMENT_RUNTIME_ADAPTER_VERSION,
        execution_scope=STEP11_RC0029_EXPERIMENT_EXECUTION_SCOPE,
        case_id=case_id,
        source_case_commitment=source_case_commitment,
        source_dependency_closure_sha256=(
            source_dependency_closure_sha256
        ),
        base_candidate_version_id=STEP11_RC0029_BASE_CANDIDATE_VERSION_ID,
        experiment_candidate_version_id=(
            STEP11_RC0029_EXPERIMENT_CANDIDATE_VERSION_ID
        ),
        base_disposition=base_disposition,
        disposition=disposition,
        closed_failure_codes=tuple(sorted(set(closed_failure_codes))),
        gate_failure_code_counts=tuple(sorted(gate_failure_code_counts)),
        bounded_candidate_limit=bounded_candidate_limit,
        bounded_replan_limit=bounded_replan_limit,
        base_candidate_count=base_candidate_count,
        experiment_candidate_count=experiment_candidate_count,
        evaluated_candidate_count=evaluated_candidate_count,
        hard_gate_pass_count=hard_gate_pass_count,
        rejected_candidate_count=rejected_candidate_count,
        replan_count=replan_count,
        selected_candidate_present=selected_candidate_present,
        successor_snapshot_sha256=successor_snapshot_sha256,
        successor_authority_sha256=successor_authority_sha256,
        successor_witness_sha256=successor_witness_sha256,
        lexical_atom_specs_sha256=lexical_atom_specs_sha256,
        surface_catalog_sha256=surface_catalog_sha256,
        owner_binding_count=owner_binding_count,
        construction_atom_count=construction_atom_count,
        relation_endpoint_atom_count=relation_endpoint_atom_count,
        semantic_link_atom_count=semantic_link_atom_count,
        explicit_unknown_atom_count=explicit_unknown_atom_count,
        semantic_coverage_authority="none",
        result_sha256="0" * 64,
    )
    result = Step11Rc0029ExperimentBodyFreeResult(
        **{
            **_result_payload(provisional),
            "closed_failure_codes": provisional.closed_failure_codes,
            "gate_failure_code_counts": provisional.gate_failure_code_counts,
            "result_sha256": _payload_sha256(_result_payload(provisional)),
        }
    )
    issues = validate_step11_rc0029_experiment_result(result)
    if issues:
        raise Step11Rc0029ExperimentRuntimeError(issues[0])
    return result


def _gate_failure_counts(gate_results: tuple[Any, ...]) -> tuple[tuple[str, int], ...]:
    counts: dict[str, int] = {}
    for gate in gate_results:
        codes = getattr(gate, "failure_codes", None)
        if type(codes) not in {tuple, list}:
            raise Step11Rc0029ExperimentRuntimeError(
                "STEP11_RC0029_GATE_RESULT_INVALID"
            )
        for code in codes:
            if (
                type(code) is not str
                or _SHAREABLE_FAILURE_CODE_RE.fullmatch(code) is None
            ):
                raise Step11Rc0029ExperimentRuntimeError(
                    "STEP11_RC0029_GATE_FAILURE_CODE_INVALID"
                )
            counts[code] = counts.get(code, 0) + 1
    return tuple(sorted(counts.items()))


def _private_execution(
    *,
    body_free_result: Step11Rc0029ExperimentBodyFreeResult,
    base_execution: Any | None,
    successor_snapshot: Any | None,
    lexical_atom_specs: Any | None,
    experiment_candidates: tuple[Any, ...],
    parsed_witnesses: tuple[Any, ...],
    verified_bindings: tuple[Any, ...],
    gate_results: tuple[Any, ...],
    selection_result: Any | None,
    selected_final_utf8_bytes: bytes | None,
    selected_parsed_witness: Any | None,
    selected_verified_binding: Any | None,
) -> Step11Rc0029ExperimentPrivateExecution:
    return Step11Rc0029ExperimentPrivateExecution(
        schema_version=STEP11_RC0029_EXPERIMENT_PRIVATE_EXECUTION_SCHEMA,
        adapter_version=STEP11_RC0029_EXPERIMENT_RUNTIME_ADAPTER_VERSION,
        case_id=body_free_result.case_id,
        source_case_commitment=body_free_result.source_case_commitment,
        source_dependency_closure_sha256=(
            body_free_result.source_dependency_closure_sha256
        ),
        base_execution=base_execution,
        successor_snapshot=successor_snapshot,
        lexical_atom_specs=lexical_atom_specs,
        experiment_candidates=experiment_candidates,
        parsed_witnesses=parsed_witnesses,
        verified_bindings=verified_bindings,
        gate_results=gate_results,
        selection_result=selection_result,
        selected_final_utf8_bytes=selected_final_utf8_bytes,
        selected_parsed_witness=selected_parsed_witness,
        selected_verified_binding=selected_verified_binding,
        body_free_result=body_free_result,
    )


def _execute_step11_rc0029_experiment_internal(
    current_input: Mapping[str, Any],
    *,
    case_id: str,
    source_case_commitment: str,
    source_dependency_closure_sha256: str,
    candidate_limit: int = STEP11_RC0029_MAX_CANDIDATES,
    replan_limit: int = STEP11_RC0029_MAX_REPLANS,
) -> Step11Rc0029ExperimentPrivateExecution:
    """Synchronously build one private execution and its public projection."""

    if type(current_input) is not dict:
        raise Step11Rc0029ExperimentRuntimeError(
            "STEP11_RC0029_INPUT_MAPPING_REQUIRED"
        )
    if type(case_id) is not str or _CASE_ID_RE.fullmatch(case_id) is None:
        raise Step11Rc0029ExperimentRuntimeError(
            "STEP11_RC0029_CASE_ID_INVALID"
        )
    if not _valid_sha256(source_case_commitment):
        raise Step11Rc0029ExperimentRuntimeError(
            "STEP11_RC0029_SOURCE_CASE_COMMITMENT_INVALID"
        )
    if not _valid_sha256(source_dependency_closure_sha256):
        raise Step11Rc0029ExperimentRuntimeError(
            "STEP11_RC0029_SOURCE_DEPENDENCY_CLOSURE_INVALID"
        )
    if (
        type(candidate_limit) is not int
        or type(candidate_limit) is bool
        or not 1 <= candidate_limit <= STEP11_RC0029_MAX_CANDIDATES
    ):
        raise Step11Rc0029ExperimentRuntimeError(
            "STEP11_RC0029_CANDIDATE_BOUND_EXCEEDED"
        )
    if (
        type(replan_limit) is not int
        or type(replan_limit) is bool
        or not 0 <= replan_limit <= STEP11_RC0029_MAX_REPLANS
    ):
        raise Step11Rc0029ExperimentRuntimeError(
            "STEP11_RC0029_REPLAN_BOUND_EXCEEDED"
        )

    base_disposition = "fail_close"
    base_candidate_count = 0
    experiment_candidate_count = 0
    successor_snapshot_sha256: str | None = None
    successor_authority_sha256: str | None = None
    successor_witness_sha256: str | None = None
    lexical_atom_specs_sha256: str | None = None
    surface_catalog_sha256: str | None = None
    owner_binding_count = 0
    construction_atom_count = 0
    relation_endpoint_atom_count = 0
    semantic_link_atom_count = 0
    explicit_unknown_atom_count = 0
    baseline: Any | None = None
    successor: Any | None = None
    lexical_specs: Any | None = None
    experiment_candidates: tuple[Any, ...] = ()
    parsed_witnesses: list[Any] = []
    verified_bindings: list[Any] = []
    selection: Any | None = None

    try:
        # Every project import is local: importing this adapter cannot alter
        # rc0027 default imports or connect a public route to the experiment.
        from emlis_ai_evidence_ledger_service import (
            build_evidence_ledger,
            build_evidence_span_resolver,
        )
        successor_owner = __import__(
            "emlis_ai_grounded_lexical_role_experiment_snapshot_successor_v3",
            fromlist=(
                "build_grounded_lexical_role_experiment_snapshot_successor",
                "validate_grounded_lexical_role_experiment_snapshot_successor",
            ),
        )
        build_grounded_lexical_role_experiment_snapshot_successor = (
            successor_owner.build_grounded_lexical_role_experiment_snapshot_successor
        )
        validate_grounded_lexical_role_experiment_snapshot_successor = (
            successor_owner.validate_grounded_lexical_role_experiment_snapshot_successor
        )
        from emlis_ai_step11_grounded_lexicalization_v3 import (
            build_step11_rc0028_experiment_lexical_atom_specs,
            validate_step11_rc0028_experiment_lexical_atom_specs,
        )
        from emlis_ai_step11_hard_gate_v3 import (
            evaluate_step11_rc0029_experiment_candidate,
            select_step11_rc0029_experiment_candidate,
        )
        from emlis_ai_step11_natural_surface_matcher_v3 import (
            match_step11_rc0029_experiment_surface,
            parse_step11_rc0029_experiment_surface,
        )
        from emlis_ai_step11_natural_surface_v3 import (
            STEP11_RC0029_EXPERIMENT_CANDIDATE_VERSION_ID as surface_version,
            build_step11_rc0029_experiment_surface_candidates,
            validate_step11_rc0029_experiment_surface_candidate,
        )
        from emlis_ai_step11_rc0029_experiment_surface_catalog_v3 import (
            STEP11_RC0029_EXPERIMENT_SURFACE_CATALOG_SHA256,
        )
        from emlis_ai_step11_runtime_adapter_v3 import (
            execute_step11_offline_v3,
            validate_step11_runtime_execution,
        )

        if surface_version != STEP11_RC0029_EXPERIMENT_CANDIDATE_VERSION_ID:
            raise Step11Rc0029ExperimentRuntimeError(
                "STEP11_RC0029_CANDIDATE_VERSION_MISMATCH"
            )
        baseline = execute_step11_offline_v3(
            dict(current_input),
            candidate_version_id=STEP11_RC0029_BASE_CANDIDATE_VERSION_ID,
            source_dependency_closure_sha256=(
                source_dependency_closure_sha256
            ),
        )
        if validate_step11_runtime_execution(baseline):
            raise Step11Rc0029ExperimentRuntimeError(
                "STEP11_RC0029_BASE_RUNTIME_VALIDATION_FAILED"
            )
        if baseline.status == "selected":
            base_disposition = "selected"
        elif baseline.status == "v3_no_valid_candidate":
            base_disposition = "no_valid_candidate"
        else:
            raise Step11Rc0029ExperimentRuntimeError(
                "STEP11_RC0029_BASE_RUNTIME_STATUS_INVALID"
            )
        base_candidates = tuple(baseline.natural_candidates)
        base_candidate_count = len(base_candidates)
        if base_candidate_count > candidate_limit:
            raise Step11Rc0029ExperimentRuntimeError(
                "STEP11_RC0029_CANDIDATE_BOUND_EXCEEDED"
            )
        if not base_candidates:
            body_free_result = _make_result(
                case_id=case_id,
                source_case_commitment=source_case_commitment,
                source_dependency_closure_sha256=(
                    source_dependency_closure_sha256
                ),
                base_disposition=base_disposition,
                disposition="no_valid_candidate",
                closed_failure_codes=(
                    "STEP11_RC0029_BASE_CANDIDATE_SET_EMPTY",
                ),
                bounded_candidate_limit=candidate_limit,
                bounded_replan_limit=replan_limit,
            )
            return _private_execution(
                body_free_result=body_free_result,
                base_execution=baseline,
                successor_snapshot=None,
                lexical_atom_specs=None,
                experiment_candidates=(),
                parsed_witnesses=(),
                verified_bindings=(),
                gate_results=(),
                selection_result=None,
                selected_final_utf8_bytes=None,
                selected_parsed_witness=None,
                selected_verified_binding=None,
            )

        evidence_spans = tuple(build_evidence_ledger(baseline.normalized_input))
        resolver = build_evidence_span_resolver(
            evidence_spans,
            current_input=baseline.normalized_input,
        )
        successor = (
            build_grounded_lexical_role_experiment_snapshot_successor(
                baseline.grounded_plan,
                resolver,
                observation_stage_context=(
                    baseline.observation_stage_context
                ),
                original_input_bundle=baseline.normalized_input,
            )
        )
        if validate_grounded_lexical_role_experiment_snapshot_successor(
            successor
        ):
            raise Step11Rc0029ExperimentRuntimeError(
                "STEP11_RC0029_SUCCESSOR_SNAPSHOT_INVALID"
            )
        if (
            successor.semantic_coverage_authorized is not False
            or successor.lexical_role_witness.semantic_coverage_authority
            != "none"
        ):
            raise Step11Rc0029ExperimentRuntimeError(
                "STEP11_RC0029_SEMANTIC_COVERAGE_SELF_CLAIM"
            )
        successor_snapshot_sha256 = successor.experiment_snapshot_sha256
        successor_authority_sha256 = (
            successor.relation_construction_authority.authority_sha256
        )
        successor_witness_sha256 = successor.lexical_role_witness.witness_sha256
        surface_catalog_sha256 = (
            STEP11_RC0029_EXPERIMENT_SURFACE_CATALOG_SHA256
        )

        # rc0029 is a downstream Surface repair.  The typed lexical atoms
        # remain the immutable E1b/rc0028 authority; per-candidate natural
        # handle specs are derived inside the rc0029 Surface builder from
        # these atoms plus each validated rc0027 base candidate.
        lexical_specs = build_step11_rc0028_experiment_lexical_atom_specs(
            successor
        )
        if validate_step11_rc0028_experiment_lexical_atom_specs(
            lexical_specs,
            successor_snapshot=successor,
        ):
            raise Step11Rc0029ExperimentRuntimeError(
                "STEP11_RC0029_LEXICAL_ATOM_SPECS_INVALID"
            )
        if lexical_specs.semantic_coverage_authority != "none":
            raise Step11Rc0029ExperimentRuntimeError(
                "STEP11_RC0029_SEMANTIC_COVERAGE_SELF_CLAIM"
            )
        lexical_atom_specs_sha256 = lexical_specs.specs_sha256
        owner_binding_count = len(lexical_specs.owner_bindings)
        construction_atom_count = len(lexical_specs.construction_atoms)
        relation_endpoint_atom_count = len(
            lexical_specs.relation_endpoint_atoms
        )
        semantic_link_atom_count = len(lexical_specs.semantic_link_atoms)
        explicit_unknown_atom_count = len(
            lexical_specs.explicit_unknown_atoms
        )

        experiment_candidates = (
            build_step11_rc0029_experiment_surface_candidates(
                base_candidates,
                successor_snapshot=successor,
                lexical_atom_specs=lexical_specs,
            )
        )
        experiment_candidate_count = len(experiment_candidates)
        if (
            experiment_candidate_count != base_candidate_count
            or experiment_candidate_count > candidate_limit
        ):
            raise Step11Rc0029ExperimentRuntimeError(
                "STEP11_RC0029_CANDIDATE_BOUND_EXCEEDED"
            )

        preflight_gates: list[Any] = []
        for candidate in experiment_candidates:
            if validate_step11_rc0029_experiment_surface_candidate(
                candidate,
                successor_snapshot=successor,
                lexical_atom_specs=lexical_specs,
            ):
                raise Step11Rc0029ExperimentRuntimeError(
                    "STEP11_RC0029_CANDIDATE_REVALIDATION_FAILED"
                )
            parsed = parse_step11_rc0029_experiment_surface(
                candidate.final_utf8_bytes
            )
            binding = match_step11_rc0029_experiment_surface(
                parsed,
                successor_snapshot=successor,
            )
            parsed_witnesses.append(parsed)
            verified_bindings.append(binding)
            preflight_gates.append(
                evaluate_step11_rc0029_experiment_candidate(
                    candidate,
                    successor_snapshot=successor,
                    lexical_atom_specs=lexical_specs,
                    inventory_result=baseline.inventory_result,
                    content_plan=baseline.content_plan,
                    current_input=baseline.projected_current_input,
                )
            )

        selector_kwargs = {
            "successor_snapshot": successor,
            "lexical_atom_specs": lexical_specs,
            "inventory_result": baseline.inventory_result,
            "content_plan": baseline.content_plan,
            "current_input": baseline.projected_current_input,
            "candidate_limit": candidate_limit,
            "replan_limit": replan_limit,
        }
        selection = select_step11_rc0029_experiment_candidate(
            experiment_candidates,
            **selector_kwargs,
        )
        repeated_selection = select_step11_rc0029_experiment_candidate(
            experiment_candidates,
            **selector_kwargs,
        )
        if selection != repeated_selection:
            raise Step11Rc0029ExperimentRuntimeError(
                "STEP11_RC0029_SELECTION_NONDETERMINISTIC"
            )

        candidate_ids = tuple(row.candidate_id for row in experiment_candidates)
        evaluated_candidate_ids = tuple(sorted(candidate_ids))
        gate_by_id = {
            row.candidate_id: row for row in tuple(selection.gate_results)
        }
        preflight_by_id = {
            row.candidate_id: row for row in tuple(preflight_gates)
        }
        if (
            len(gate_by_id) != len(experiment_candidates)
            or gate_by_id != preflight_by_id
            or tuple(selection.evaluated_candidate_ids)
            != evaluated_candidate_ids
            or selection.bounded_candidate_limit != candidate_limit
            or selection.bounded_replan_limit != replan_limit
            or selection.experimental_only is not True
            or selection.runtime_connected is not False
        ):
            raise Step11Rc0029ExperimentRuntimeError(
                "STEP11_RC0029_SELECTION_COMMITMENT_MISMATCH"
            )
        gate_results = tuple(selection.gate_results)
        gate_failure_code_counts = _gate_failure_counts(gate_results)
        hard_pass_count = sum(row.hard_pass is True for row in gate_results)
        rejected_count = len(gate_results) - hard_pass_count
        replan_count = int(selection.recovery_attempted is True)
        inverse_by_id = {
            candidate.candidate_id: (parsed, binding)
            for candidate, parsed, binding in zip(
                experiment_candidates,
                parsed_witnesses,
                verified_bindings,
            )
        }
        if replan_count > replan_limit:
            raise Step11Rc0029ExperimentRuntimeError(
                "STEP11_RC0029_REPLAN_BOUND_EXCEEDED"
            )

        if selection.status == "selected":
            selected = selection.selected_candidate
            matching_gate = gate_by_id.get(selection.selected_candidate_id)
            if (
                selected not in experiment_candidates
                or selection.selected_candidate_id
                != getattr(selected, "candidate_id", None)
                or matching_gate is None
                or matching_gate.hard_pass is not True
                or type(selected.final_utf8_bytes) is not bytes
                or not selected.final_utf8_bytes
            ):
                raise Step11Rc0029ExperimentRuntimeError(
                    "STEP11_RC0029_SELECTED_CANDIDATE_INVALID"
                )
            disposition = "selected"
            closed_failure_codes: tuple[str, ...] = ()
            selected_present = True
            selected_final_utf8_bytes = selected.final_utf8_bytes
            selected_parsed_witness, selected_verified_binding = (
                inverse_by_id[selected.candidate_id]
            )
        elif selection.status == "rc0029_experiment_no_valid_candidate":
            if (
                selection.selected_candidate is not None
                or selection.selected_candidate_id is not None
                or hard_pass_count != 0
            ):
                raise Step11Rc0029ExperimentRuntimeError(
                    "STEP11_RC0029_NO_VALID_SELECTION_INVALID"
                )
            disposition = "no_valid_candidate"
            closed_failure_codes = tuple(
                code for code, _count in gate_failure_code_counts
            ) or ("STEP11_RC0029_NO_VALID_CANDIDATE",)
            selected_present = False
            selected_final_utf8_bytes = None
            selected_parsed_witness = None
            selected_verified_binding = None
        else:
            raise Step11Rc0029ExperimentRuntimeError(
                "STEP11_RC0029_SELECTION_STATUS_INVALID"
            )

        body_free_result = _make_result(
            case_id=case_id,
            source_case_commitment=source_case_commitment,
            source_dependency_closure_sha256=(
                source_dependency_closure_sha256
            ),
            base_disposition=base_disposition,
            disposition=disposition,
            closed_failure_codes=closed_failure_codes,
            gate_failure_code_counts=gate_failure_code_counts,
            bounded_candidate_limit=candidate_limit,
            bounded_replan_limit=replan_limit,
            base_candidate_count=base_candidate_count,
            experiment_candidate_count=experiment_candidate_count,
            evaluated_candidate_count=len(gate_results),
            hard_gate_pass_count=hard_pass_count,
            rejected_candidate_count=rejected_count,
            replan_count=replan_count,
            selected_candidate_present=selected_present,
            successor_snapshot_sha256=successor_snapshot_sha256,
            successor_authority_sha256=successor_authority_sha256,
            successor_witness_sha256=successor_witness_sha256,
            lexical_atom_specs_sha256=lexical_atom_specs_sha256,
            surface_catalog_sha256=surface_catalog_sha256,
            owner_binding_count=owner_binding_count,
            construction_atom_count=construction_atom_count,
            relation_endpoint_atom_count=relation_endpoint_atom_count,
            semantic_link_atom_count=semantic_link_atom_count,
            explicit_unknown_atom_count=explicit_unknown_atom_count,
        )
        return _private_execution(
            body_free_result=body_free_result,
            base_execution=baseline,
            successor_snapshot=successor,
            lexical_atom_specs=lexical_specs,
            experiment_candidates=tuple(experiment_candidates),
            parsed_witnesses=tuple(parsed_witnesses),
            verified_bindings=tuple(verified_bindings),
            gate_results=gate_results,
            selection_result=selection,
            selected_final_utf8_bytes=selected_final_utf8_bytes,
            selected_parsed_witness=selected_parsed_witness,
            selected_verified_binding=selected_verified_binding,
        )
    except Exception as error:
        body_free_result = _make_result(
            case_id=case_id,
            source_case_commitment=source_case_commitment,
            source_dependency_closure_sha256=(
                source_dependency_closure_sha256
            ),
            base_disposition=base_disposition,
            disposition="fail_close",
            closed_failure_codes=(_closed_pipeline_code(error),),
            bounded_candidate_limit=candidate_limit,
            bounded_replan_limit=replan_limit,
            base_candidate_count=base_candidate_count,
            experiment_candidate_count=experiment_candidate_count,
            successor_snapshot_sha256=successor_snapshot_sha256,
            successor_authority_sha256=successor_authority_sha256,
            successor_witness_sha256=successor_witness_sha256,
            lexical_atom_specs_sha256=lexical_atom_specs_sha256,
            surface_catalog_sha256=surface_catalog_sha256,
            owner_binding_count=owner_binding_count,
            construction_atom_count=construction_atom_count,
            relation_endpoint_atom_count=relation_endpoint_atom_count,
            semantic_link_atom_count=semantic_link_atom_count,
            explicit_unknown_atom_count=explicit_unknown_atom_count,
        )
        return _private_execution(
            body_free_result=body_free_result,
            base_execution=baseline,
            successor_snapshot=successor,
            lexical_atom_specs=lexical_specs,
            experiment_candidates=tuple(experiment_candidates),
            parsed_witnesses=tuple(parsed_witnesses),
            verified_bindings=tuple(verified_bindings),
            gate_results=(
                tuple(getattr(selection, "gate_results", ()))
                if selection is not None
                else ()
            ),
            selection_result=selection,
            selected_final_utf8_bytes=None,
            selected_parsed_witness=None,
            selected_verified_binding=None,
        )


def execute_step11_rc0029_experiment_private(
    current_input: Mapping[str, Any],
    *,
    case_id: str,
    source_case_commitment: str,
    source_dependency_closure_sha256: str,
    candidate_limit: int = STEP11_RC0029_MAX_CANDIDATES,
    replan_limit: int = STEP11_RC0029_MAX_REPLANS,
) -> Step11Rc0029ExperimentPrivateExecution:
    """Return the request-local body-full diagnostic execution."""

    return _execute_step11_rc0029_experiment_internal(
        current_input,
        case_id=case_id,
        source_case_commitment=source_case_commitment,
        source_dependency_closure_sha256=(
            source_dependency_closure_sha256
        ),
        candidate_limit=candidate_limit,
        replan_limit=replan_limit,
    )


def run_step11_rc0029_experiment(
    current_input: Mapping[str, Any],
    *,
    case_id: str,
    source_case_commitment: str,
    source_dependency_closure_sha256: str,
    candidate_limit: int = STEP11_RC0029_MAX_CANDIDATES,
    replan_limit: int = STEP11_RC0029_MAX_REPLANS,
) -> Step11Rc0029ExperimentBodyFreeResult:
    """Return only the body-free projection of the shared internal run."""

    return _execute_step11_rc0029_experiment_internal(
        current_input,
        case_id=case_id,
        source_case_commitment=source_case_commitment,
        source_dependency_closure_sha256=(
            source_dependency_closure_sha256
        ),
        candidate_limit=candidate_limit,
        replan_limit=replan_limit,
    ).body_free_result


def validate_step11_rc0029_experiment_result(value: Any) -> tuple[str, ...]:
    """Validate the exact closed body-free receipt and its commitment."""

    if type(value) is not Step11Rc0029ExperimentBodyFreeResult:
        return ("STEP11_RC0029_RESULT_TYPE_INVALID",)
    issues: set[str] = set()
    if (
        value.schema_version
        != STEP11_RC0029_EXPERIMENT_RUNTIME_RESULT_SCHEMA
        or value.adapter_version
        != STEP11_RC0029_EXPERIMENT_RUNTIME_ADAPTER_VERSION
        or value.execution_scope
        != STEP11_RC0029_EXPERIMENT_EXECUTION_SCOPE
        or value.base_candidate_version_id
        != STEP11_RC0029_BASE_CANDIDATE_VERSION_ID
        or value.experiment_candidate_version_id
        != STEP11_RC0029_EXPERIMENT_CANDIDATE_VERSION_ID
        or value.experimental_only is not True
        or value.body_free is not True
        or value.runtime_connected is not False
        or value.semantic_coverage_authority != "none"
    ):
        issues.add("STEP11_RC0029_RESULT_CONTRACT_MISMATCH")
    if (
        type(value.case_id) is not str
        or _CASE_ID_RE.fullmatch(value.case_id) is None
        or not _valid_sha256(value.source_case_commitment)
        or not _valid_sha256(value.source_dependency_closure_sha256)
    ):
        issues.add("STEP11_RC0029_SOURCE_COMMITMENT_MISMATCH")
    if (
        value.base_disposition not in _DISPOSITIONS
        or value.disposition not in _DISPOSITIONS
    ):
        issues.add("STEP11_RC0029_DISPOSITION_INVALID")
    if (
        tuple(sorted(set(value.closed_failure_codes)))
        != value.closed_failure_codes
        or any(
            type(code) is not str
            or _SHAREABLE_FAILURE_CODE_RE.fullmatch(code) is None
            for code in value.closed_failure_codes
        )
    ):
        issues.add("STEP11_RC0029_FAILURE_CODE_INVALID")
    if (
        tuple(sorted(value.gate_failure_code_counts))
        != value.gate_failure_code_counts
        or len({code for code, _count in value.gate_failure_code_counts})
        != len(value.gate_failure_code_counts)
        or any(
            type(code) is not str
            or _SHAREABLE_FAILURE_CODE_RE.fullmatch(code) is None
            or type(count) is not int
            or type(count) is bool
            or count < 1
            for code, count in value.gate_failure_code_counts
        )
    ):
        issues.add("STEP11_RC0029_GATE_FAILURE_COUNTS_INVALID")
    numeric_values = (
        value.base_candidate_count,
        value.experiment_candidate_count,
        value.evaluated_candidate_count,
        value.hard_gate_pass_count,
        value.rejected_candidate_count,
        value.replan_count,
        value.owner_binding_count,
        value.construction_atom_count,
        value.relation_endpoint_atom_count,
        value.semantic_link_atom_count,
        value.explicit_unknown_atom_count,
    )
    if any(
        type(item) is not int or type(item) is bool or item < 0
        for item in numeric_values
    ):
        issues.add("STEP11_RC0029_RESULT_COUNT_INVALID")
    if (
        type(value.bounded_candidate_limit) is not int
        or type(value.bounded_candidate_limit) is bool
        or not 1
        <= value.bounded_candidate_limit
        <= STEP11_RC0029_MAX_CANDIDATES
        or type(value.bounded_replan_limit) is not int
        or type(value.bounded_replan_limit) is bool
        or not 0 <= value.bounded_replan_limit <= STEP11_RC0029_MAX_REPLANS
        or (
            value.disposition != "fail_close"
            and value.base_candidate_count > value.bounded_candidate_limit
        )
        or (
            value.disposition != "fail_close"
            and value.experiment_candidate_count
            > value.bounded_candidate_limit
        )
        or value.evaluated_candidate_count > value.experiment_candidate_count
        or value.hard_gate_pass_count + value.rejected_candidate_count
        != value.evaluated_candidate_count
        or value.replan_count > value.bounded_replan_limit
    ):
        issues.add("STEP11_RC0029_RESOURCE_BOUND_EXCEEDED")
    if value.disposition == "selected":
        if (
            value.selected_candidate_present is not True
            or value.hard_gate_pass_count < 1
            or value.closed_failure_codes
        ):
            issues.add("STEP11_RC0029_SELECTED_DISPOSITION_INVALID")
    elif value.disposition == "no_valid_candidate":
        if (
            value.selected_candidate_present is not False
            or value.hard_gate_pass_count != 0
            or not value.closed_failure_codes
        ):
            issues.add("STEP11_RC0029_NO_VALID_DISPOSITION_INVALID")
    elif value.disposition == "fail_close":
        if (
            value.selected_candidate_present is not False
            or value.hard_gate_pass_count != 0
            or not value.closed_failure_codes
        ):
            issues.add("STEP11_RC0029_FAIL_CLOSE_DISPOSITION_INVALID")
    commitments = (
        value.successor_snapshot_sha256,
        value.successor_authority_sha256,
        value.successor_witness_sha256,
        value.lexical_atom_specs_sha256,
        value.surface_catalog_sha256,
    )
    if value.disposition != "fail_close" and any(
        not _valid_sha256(item) for item in commitments
    ):
        issues.add("STEP11_RC0029_ARTIFACT_COMMITMENT_MISMATCH")
    if any(item is not None and not _valid_sha256(item) for item in commitments):
        issues.add("STEP11_RC0029_ARTIFACT_COMMITMENT_MISMATCH")
    try:
        expected_sha256 = _payload_sha256(_result_payload(value))
    except (TypeError, ValueError):
        expected_sha256 = ""
    if value.result_sha256 != expected_sha256 or not _valid_sha256(
        value.result_sha256
    ):
        issues.add("STEP11_RC0029_RESULT_HASH_MISMATCH")
    return tuple(sorted(issues))


def validate_step11_rc0029_experiment_private_execution(
    value: Any,
) -> tuple[str, ...]:
    """Validate request-local linkage without projecting private material."""

    if type(value) is not Step11Rc0029ExperimentPrivateExecution:
        return ("STEP11_RC0029_PRIVATE_EXECUTION_TYPE_INVALID",)
    issues: set[str] = set()
    if (
        value.schema_version
        != STEP11_RC0029_EXPERIMENT_PRIVATE_EXECUTION_SCHEMA
        or value.adapter_version
        != STEP11_RC0029_EXPERIMENT_RUNTIME_ADAPTER_VERSION
        or value.private_body_full is not True
        or value.shareable is not False
        or value.experimental_only is not True
        or value.runtime_connected is not False
    ):
        issues.add("STEP11_RC0029_PRIVATE_EXECUTION_CONTRACT_MISMATCH")
    body_free_issues = validate_step11_rc0029_experiment_result(
        value.body_free_result
    )
    if body_free_issues:
        issues.add("STEP11_RC0029_PRIVATE_BODY_FREE_RESULT_INVALID")
        return tuple(sorted(issues))
    result = value.body_free_result
    if (
        value.case_id != result.case_id
        or value.source_case_commitment != result.source_case_commitment
        or value.source_dependency_closure_sha256
        != result.source_dependency_closure_sha256
        or len(value.experiment_candidates)
        != result.experiment_candidate_count
        or len(value.gate_results) != result.evaluated_candidate_count
    ):
        issues.add("STEP11_RC0029_PRIVATE_SOURCE_LINKAGE_MISMATCH")
    if value.selection_result is not None and tuple(
        getattr(value.selection_result, "gate_results", ())
    ) != value.gate_results:
        issues.add("STEP11_RC0029_PRIVATE_SELECTION_LINKAGE_MISMATCH")

    if result.disposition != "fail_close" and (
        len(value.parsed_witnesses) != len(value.experiment_candidates)
        or len(value.verified_bindings) != len(value.experiment_candidates)
    ):
        issues.add("STEP11_RC0029_PRIVATE_INVERSE_CARDINALITY_MISMATCH")
    if result.disposition == "selected":
        selected = getattr(value.selection_result, "selected_candidate", None)
        selected_id = getattr(
            value.selection_result, "selected_candidate_id", None
        )
        matching_gates = tuple(
            row
            for row in value.gate_results
            if getattr(row, "candidate_id", None) == selected_id
        )
        try:
            import hashlib

            selected_body_sha256 = hashlib.sha256(
                value.selected_final_utf8_bytes
            ).hexdigest()
        except (TypeError, ValueError):
            selected_body_sha256 = ""
        if (
            selected not in value.experiment_candidates
            or selected_id != getattr(selected, "candidate_id", None)
            or type(value.selected_final_utf8_bytes) is not bytes
            or not value.selected_final_utf8_bytes
            or value.selected_final_utf8_bytes
            != getattr(selected, "final_utf8_bytes", None)
            or value.selected_parsed_witness not in value.parsed_witnesses
            or getattr(value.selected_parsed_witness, "body_sha256", None)
            != selected_body_sha256
            or value.selected_verified_binding not in value.verified_bindings
            or getattr(value.selected_verified_binding, "hard_verified", None)
            is not True
            or getattr(value.selected_verified_binding, "issue_codes", None)
            != ()
            or len(matching_gates) != 1
            or matching_gates[0].hard_pass is not True
        ):
            issues.add("STEP11_RC0029_PRIVATE_SELECTED_LINKAGE_MISMATCH")
    elif any(
        item is not None
        for item in (
            value.selected_final_utf8_bytes,
            value.selected_parsed_witness,
            value.selected_verified_binding,
        )
    ):
        issues.add("STEP11_RC0029_PRIVATE_UNSELECTED_BODY_FORBIDDEN")
    return tuple(sorted(issues))


def step11_rc0029_experiment_result_material(
    value: Step11Rc0029ExperimentBodyFreeResult,
) -> dict[str, Any]:
    """Return the validated shareable receipt without any body-bearing value."""

    issues = validate_step11_rc0029_experiment_result(value)
    if issues:
        raise Step11Rc0029ExperimentRuntimeError(issues[0])
    return {**_result_payload(value), "result_sha256": value.result_sha256}


validate_step11_rc0029_experiment_runtime_result = (
    validate_step11_rc0029_experiment_result
)
step11_rc0029_experiment_runtime_result_material = (
    step11_rc0029_experiment_result_material
)


__all__ = [
    "STEP11_RC0029_BASE_CANDIDATE_VERSION_ID",
    "STEP11_RC0029_EXPERIMENT_CANDIDATE_VERSION_ID",
    "STEP11_RC0029_EXPERIMENT_EXECUTION_SCOPE",
    "STEP11_RC0029_EXPERIMENT_PRIVATE_EXECUTION_SCHEMA",
    "STEP11_RC0029_EXPERIMENT_RUNTIME_ADAPTER_VERSION",
    "STEP11_RC0029_EXPERIMENT_RUNTIME_RESULT_SCHEMA",
    "STEP11_RC0029_MAX_CANDIDATES",
    "STEP11_RC0029_MAX_REPLANS",
    "Step11Rc0029ExperimentBodyFreeResult",
    "Step11Rc0029ExperimentPrivateExecution",
    "Step11Rc0029ExperimentRuntimeResult",
    "Step11Rc0029ExperimentRuntimeError",
    "execute_step11_rc0029_experiment_private",
    "run_step11_rc0029_experiment",
    "step11_rc0029_experiment_result_material",
    "step11_rc0029_experiment_runtime_result_material",
    "validate_step11_rc0029_experiment_result",
    "validate_step11_rc0029_experiment_private_execution",
    "validate_step11_rc0029_experiment_runtime_result",
]
