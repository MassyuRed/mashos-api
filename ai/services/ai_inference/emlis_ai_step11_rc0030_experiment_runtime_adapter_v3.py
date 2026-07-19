# -*- coding: utf-8 -*-
"""Disconnected composition root for the rc0030 Step 11 experiment.

All project imports are request-local.  Base and final body witnesses remain
inside :class:`Step11Rc0030ExperimentPrivateExecution`; callers of the public
entry point receive only a closed, body-free commitment receipt.  Nothing in
this module is imported by the shared Step 11 runtime or a public route.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping


STEP11_RC0030_EXPERIMENT_RUNTIME_RESULT_SCHEMA = (
    "cocolon.emlis.nls_v3.step11.rc0030_experiment_runtime_result.v1"
)
STEP11_RC0030_EXPERIMENT_PRIVATE_EXECUTION_SCHEMA = (
    "cocolon.emlis.nls_v3.step11.rc0030_experiment_private_execution.v1"
)
STEP11_RC0030_EXPERIMENT_RUNTIME_ADAPTER_VERSION = (
    "cocolon.emlis.nls_v3.runtime_adapter.step11.rc0030.experiment."
    "20260719.v1"
)
STEP11_RC0030_EXPERIMENT_EXECUTION_SCOPE = "offline_bounded_experiment"
STEP11_RC0030_BASE_CANDIDATE_VERSION_ID = "nls_v3_rc_0027"
STEP11_RC0030_EXPERIMENT_CANDIDATE_VERSION_ID = "nls_v3_rc_0030_experiment"
STEP11_RC0030_MAX_CANDIDATES = 12
STEP11_RC0030_MAX_REPLANS = 1
STEP11_RC0030_MAX_PARSER_INVOCATIONS_PER_CANDIDATE = 2
STEP11_RC0030_MAX_MATCHER_INVOCATIONS_PER_CANDIDATE = 2
STEP11_RC0030_MAX_PARSER_INVOCATIONS = 24
STEP11_RC0030_MAX_MATCHER_INVOCATIONS = 24
STEP11_RC0030_MAX_BODY_BYTE_INSPECTIONS = 48_000_000

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_CASE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,95}$")
_CLOSED_CODE_RE = re.compile(r"^STEP11_RC0030_[A-Z0-9_]{2,111}$")
_SHAREABLE_FAILURE_CODE_RE = re.compile(
    r"^(?:STEP11_RC0030_[A-Z0-9_]{2,111}|S11_GATE[A-Z0-9_]{0,120})$"
)
_DISPOSITIONS = frozenset({"selected", "no_valid_candidate", "fail_close"})


class Step11Rc0030ExperimentRuntimeError(ValueError):
    """Caller-visible error carrying one body-free closed code."""

    def __init__(self, code: str) -> None:
        if type(code) is not str or _CLOSED_CODE_RE.fullmatch(code) is None:
            code = "STEP11_RC0030_RUNTIME_ERROR_CODE_INVALID"
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class Step11Rc0030ExperimentBodyFreeResult:
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
    base_inverse_failure_code_counts: tuple[tuple[str, int], ...]
    forward_failure_code_counts: tuple[tuple[str, int], ...]
    gate_failure_code_counts: tuple[tuple[str, int], ...]
    bounded_candidate_limit: int
    bounded_replan_limit: int
    base_candidate_count: int
    base_inverse_prepass_count: int
    experiment_candidate_count: int
    base_inverse_rejected_candidate_count: int
    forward_rejected_base_candidate_count: int
    evaluated_candidate_count: int
    base_body_parse_count: int
    base_reuse_match_count: int
    final_body_parse_count: int
    final_surface_match_count: int
    body_byte_inspection_count: int
    hard_gate_pass_count: int
    rejected_candidate_count: int
    replan_count: int
    selected_candidate_present: bool
    successor_snapshot_sha256: str | None
    successor_authority_sha256: str | None
    successor_witness_sha256: str | None
    lexical_atom_specs_sha256: str | None
    surface_catalog_sha256: str | None
    base_inverse_contexts_sha256: str | None
    owner_binding_count: int
    construction_atom_count: int
    relation_endpoint_atom_count: int
    semantic_link_atom_count: int
    explicit_unknown_atom_count: int
    verified_base_reuse_binding_count: int
    semantic_coverage_authority: str
    result_sha256: str
    experimental_only: bool = True
    body_free: bool = True
    runtime_connected: bool = False

    @property
    def final_surface_parse_count(self) -> int:
        """Precisely named alias for the final-body parser attempt count."""

        return self.final_body_parse_count


Step11Rc0030ExperimentRuntimeResult = Step11Rc0030ExperimentBodyFreeResult


@dataclass(frozen=True, slots=True, repr=False)
class Step11Rc0030ExperimentPrivateExecution:
    """Request-local body-bearing execution; never a shareable result."""

    schema_version: str
    adapter_version: str
    case_id: str
    source_case_commitment: str
    source_dependency_closure_sha256: str
    base_execution: Any | None
    successor_snapshot: Any | None
    lexical_atom_specs: Any | None
    experiment_candidates: tuple[Any, ...]
    base_inverse_evaluations: tuple[Any, ...]
    attempted_base_inverse_contexts: tuple[Any, ...]
    base_inverse_contexts: tuple[Any, ...]
    gate_results: tuple[Any, ...]
    selection_result: Any | None
    selected_final_utf8_bytes: bytes | None
    selected_parsed_witness: Any | None
    selected_verified_binding: Any | None
    selected_base_inverse_context: Any | None
    body_free_result: Step11Rc0030ExperimentBodyFreeResult
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
        return "STEP11_RC0030_BASE_RUNTIME_FAIL_CLOSE"
    return "STEP11_RC0030_PIPELINE_FAIL_CLOSE"


def _closed_forward_code(error: BaseException) -> str:
    code = getattr(error, "code", None)
    if (
        type(code) is str
        and _SHAREABLE_FAILURE_CODE_RE.fullmatch(code) is not None
    ):
        return code
    return "STEP11_RC0030_FORWARD_CANDIDATE_REJECTED"


def _result_payload(value: Step11Rc0030ExperimentBodyFreeResult) -> dict[str, Any]:
    return {
        "schema_version": value.schema_version,
        "adapter_version": value.adapter_version,
        "execution_scope": value.execution_scope,
        "case_id": value.case_id,
        "source_case_commitment": value.source_case_commitment,
        "source_dependency_closure_sha256": value.source_dependency_closure_sha256,
        "base_candidate_version_id": value.base_candidate_version_id,
        "experiment_candidate_version_id": value.experiment_candidate_version_id,
        "base_disposition": value.base_disposition,
        "disposition": value.disposition,
        "closed_failure_codes": list(value.closed_failure_codes),
        "base_inverse_failure_code_counts": [
            {"code": code, "count": count}
            for code, count in value.base_inverse_failure_code_counts
        ],
        "forward_failure_code_counts": [
            {"code": code, "count": count}
            for code, count in value.forward_failure_code_counts
        ],
        "gate_failure_code_counts": [
            {"code": code, "count": count}
            for code, count in value.gate_failure_code_counts
        ],
        "bounded_candidate_limit": value.bounded_candidate_limit,
        "bounded_replan_limit": value.bounded_replan_limit,
        "base_candidate_count": value.base_candidate_count,
        "base_inverse_prepass_count": value.base_inverse_prepass_count,
        "experiment_candidate_count": value.experiment_candidate_count,
        "base_inverse_rejected_candidate_count": (
            value.base_inverse_rejected_candidate_count
        ),
        "forward_rejected_base_candidate_count": (
            value.forward_rejected_base_candidate_count
        ),
        "evaluated_candidate_count": value.evaluated_candidate_count,
        "base_body_parse_count": value.base_body_parse_count,
        "base_reuse_match_count": value.base_reuse_match_count,
        "final_body_parse_count": value.final_body_parse_count,
        "final_surface_match_count": value.final_surface_match_count,
        "body_byte_inspection_count": value.body_byte_inspection_count,
        "hard_gate_pass_count": value.hard_gate_pass_count,
        "rejected_candidate_count": value.rejected_candidate_count,
        "replan_count": value.replan_count,
        "selected_candidate_present": value.selected_candidate_present,
        "successor_snapshot_sha256": value.successor_snapshot_sha256,
        "successor_authority_sha256": value.successor_authority_sha256,
        "successor_witness_sha256": value.successor_witness_sha256,
        "lexical_atom_specs_sha256": value.lexical_atom_specs_sha256,
        "surface_catalog_sha256": value.surface_catalog_sha256,
        "base_inverse_contexts_sha256": value.base_inverse_contexts_sha256,
        "owner_binding_count": value.owner_binding_count,
        "construction_atom_count": value.construction_atom_count,
        "relation_endpoint_atom_count": value.relation_endpoint_atom_count,
        "semantic_link_atom_count": value.semantic_link_atom_count,
        "explicit_unknown_atom_count": value.explicit_unknown_atom_count,
        "verified_base_reuse_binding_count": value.verified_base_reuse_binding_count,
        "semantic_coverage_authority": value.semantic_coverage_authority,
        "experimental_only": value.experimental_only,
        "body_free": value.body_free,
        "runtime_connected": value.runtime_connected,
    }


def _payload_sha256(value: Mapping[str, Any]) -> str:
    from emlis_ai_nls_v3_artifact_contract import artifact_sha256

    return artifact_sha256(dict(value))


def _make_result(
    *,
    case_id: str,
    source_case_commitment: str,
    source_dependency_closure_sha256: str,
    base_disposition: str,
    disposition: str,
    bounded_candidate_limit: int,
    bounded_replan_limit: int,
    closed_failure_codes: tuple[str, ...] = (),
    base_inverse_failure_code_counts: tuple[tuple[str, int], ...] = (),
    forward_failure_code_counts: tuple[tuple[str, int], ...] = (),
    gate_failure_code_counts: tuple[tuple[str, int], ...] = (),
    base_candidate_count: int = 0,
    base_inverse_prepass_count: int = 0,
    experiment_candidate_count: int = 0,
    base_inverse_rejected_candidate_count: int = 0,
    forward_rejected_base_candidate_count: int = 0,
    evaluated_candidate_count: int = 0,
    base_body_parse_count: int = 0,
    base_reuse_match_count: int = 0,
    final_body_parse_count: int = 0,
    final_surface_match_count: int = 0,
    body_byte_inspection_count: int = 0,
    hard_gate_pass_count: int = 0,
    rejected_candidate_count: int = 0,
    replan_count: int = 0,
    selected_candidate_present: bool = False,
    successor_snapshot_sha256: str | None = None,
    successor_authority_sha256: str | None = None,
    successor_witness_sha256: str | None = None,
    lexical_atom_specs_sha256: str | None = None,
    surface_catalog_sha256: str | None = None,
    base_inverse_contexts_sha256: str | None = None,
    owner_binding_count: int = 0,
    construction_atom_count: int = 0,
    relation_endpoint_atom_count: int = 0,
    semantic_link_atom_count: int = 0,
    explicit_unknown_atom_count: int = 0,
    verified_base_reuse_binding_count: int = 0,
) -> Step11Rc0030ExperimentBodyFreeResult:
    provisional = Step11Rc0030ExperimentBodyFreeResult(
        schema_version=STEP11_RC0030_EXPERIMENT_RUNTIME_RESULT_SCHEMA,
        adapter_version=STEP11_RC0030_EXPERIMENT_RUNTIME_ADAPTER_VERSION,
        execution_scope=STEP11_RC0030_EXPERIMENT_EXECUTION_SCOPE,
        case_id=case_id,
        source_case_commitment=source_case_commitment,
        source_dependency_closure_sha256=source_dependency_closure_sha256,
        base_candidate_version_id=STEP11_RC0030_BASE_CANDIDATE_VERSION_ID,
        experiment_candidate_version_id=STEP11_RC0030_EXPERIMENT_CANDIDATE_VERSION_ID,
        base_disposition=base_disposition,
        disposition=disposition,
        closed_failure_codes=tuple(sorted(set(closed_failure_codes))),
        base_inverse_failure_code_counts=tuple(
            sorted(base_inverse_failure_code_counts)
        ),
        forward_failure_code_counts=tuple(sorted(forward_failure_code_counts)),
        gate_failure_code_counts=tuple(sorted(gate_failure_code_counts)),
        bounded_candidate_limit=bounded_candidate_limit,
        bounded_replan_limit=bounded_replan_limit,
        base_candidate_count=base_candidate_count,
        base_inverse_prepass_count=base_inverse_prepass_count,
        experiment_candidate_count=experiment_candidate_count,
        base_inverse_rejected_candidate_count=(
            base_inverse_rejected_candidate_count
        ),
        forward_rejected_base_candidate_count=(
            forward_rejected_base_candidate_count
        ),
        evaluated_candidate_count=evaluated_candidate_count,
        base_body_parse_count=base_body_parse_count,
        base_reuse_match_count=base_reuse_match_count,
        final_body_parse_count=final_body_parse_count,
        final_surface_match_count=final_surface_match_count,
        body_byte_inspection_count=body_byte_inspection_count,
        hard_gate_pass_count=hard_gate_pass_count,
        rejected_candidate_count=rejected_candidate_count,
        replan_count=replan_count,
        selected_candidate_present=selected_candidate_present,
        successor_snapshot_sha256=successor_snapshot_sha256,
        successor_authority_sha256=successor_authority_sha256,
        successor_witness_sha256=successor_witness_sha256,
        lexical_atom_specs_sha256=lexical_atom_specs_sha256,
        surface_catalog_sha256=surface_catalog_sha256,
        base_inverse_contexts_sha256=base_inverse_contexts_sha256,
        owner_binding_count=owner_binding_count,
        construction_atom_count=construction_atom_count,
        relation_endpoint_atom_count=relation_endpoint_atom_count,
        semantic_link_atom_count=semantic_link_atom_count,
        explicit_unknown_atom_count=explicit_unknown_atom_count,
        verified_base_reuse_binding_count=verified_base_reuse_binding_count,
        semantic_coverage_authority="none",
        result_sha256="0" * 64,
    )
    result = Step11Rc0030ExperimentBodyFreeResult(
        **{
            **_result_payload(provisional),
            "closed_failure_codes": provisional.closed_failure_codes,
            "base_inverse_failure_code_counts": (
                provisional.base_inverse_failure_code_counts
            ),
            "forward_failure_code_counts": (
                provisional.forward_failure_code_counts
            ),
            "gate_failure_code_counts": provisional.gate_failure_code_counts,
            "result_sha256": _payload_sha256(_result_payload(provisional)),
        }
    )
    issues = validate_step11_rc0030_experiment_result(result)
    if issues:
        raise Step11Rc0030ExperimentRuntimeError(issues[0])
    return result


def _gate_failure_counts(gate_results: tuple[Any, ...]) -> tuple[tuple[str, int], ...]:
    counts: dict[str, int] = {}
    for gate in gate_results:
        codes = getattr(gate, "failure_codes", None)
        if type(codes) not in {tuple, list}:
            raise Step11Rc0030ExperimentRuntimeError(
                "STEP11_RC0030_GATE_RESULT_INVALID"
            )
        for code in codes:
            if (
                type(code) is not str
                or _SHAREABLE_FAILURE_CODE_RE.fullmatch(code) is None
            ):
                raise Step11Rc0030ExperimentRuntimeError(
                    "STEP11_RC0030_GATE_FAILURE_CODE_INVALID"
                )
            counts[code] = counts.get(code, 0) + 1
    return tuple(sorted(counts.items()))


def _private_execution(
    *,
    body_free_result: Step11Rc0030ExperimentBodyFreeResult,
    base_execution: Any | None,
    successor_snapshot: Any | None,
    lexical_atom_specs: Any | None,
    experiment_candidates: tuple[Any, ...],
    base_inverse_evaluations: tuple[Any, ...],
    attempted_base_inverse_contexts: tuple[Any, ...],
    base_inverse_contexts: tuple[Any, ...],
    gate_results: tuple[Any, ...],
    selection_result: Any | None,
    selected_final_utf8_bytes: bytes | None,
    selected_parsed_witness: Any | None,
    selected_verified_binding: Any | None,
    selected_base_inverse_context: Any | None,
) -> Step11Rc0030ExperimentPrivateExecution:
    return Step11Rc0030ExperimentPrivateExecution(
        schema_version=STEP11_RC0030_EXPERIMENT_PRIVATE_EXECUTION_SCHEMA,
        adapter_version=STEP11_RC0030_EXPERIMENT_RUNTIME_ADAPTER_VERSION,
        case_id=body_free_result.case_id,
        source_case_commitment=body_free_result.source_case_commitment,
        source_dependency_closure_sha256=(
            body_free_result.source_dependency_closure_sha256
        ),
        base_execution=base_execution,
        successor_snapshot=successor_snapshot,
        lexical_atom_specs=lexical_atom_specs,
        experiment_candidates=experiment_candidates,
        base_inverse_evaluations=base_inverse_evaluations,
        attempted_base_inverse_contexts=attempted_base_inverse_contexts,
        base_inverse_contexts=base_inverse_contexts,
        gate_results=gate_results,
        selection_result=selection_result,
        selected_final_utf8_bytes=selected_final_utf8_bytes,
        selected_parsed_witness=selected_parsed_witness,
        selected_verified_binding=selected_verified_binding,
        selected_base_inverse_context=selected_base_inverse_context,
        body_free_result=body_free_result,
    )


def _execute_step11_rc0030_experiment_internal(
    current_input: Mapping[str, Any],
    *,
    case_id: str,
    source_case_commitment: str,
    source_dependency_closure_sha256: str,
    candidate_limit: int = STEP11_RC0030_MAX_CANDIDATES,
    replan_limit: int = STEP11_RC0030_MAX_REPLANS,
) -> Step11Rc0030ExperimentPrivateExecution:
    if type(current_input) is not dict:
        raise Step11Rc0030ExperimentRuntimeError(
            "STEP11_RC0030_INPUT_MAPPING_REQUIRED"
        )
    if type(case_id) is not str or _CASE_ID_RE.fullmatch(case_id) is None:
        raise Step11Rc0030ExperimentRuntimeError("STEP11_RC0030_CASE_ID_INVALID")
    if not _valid_sha256(source_case_commitment):
        raise Step11Rc0030ExperimentRuntimeError(
            "STEP11_RC0030_SOURCE_CASE_COMMITMENT_INVALID"
        )
    if not _valid_sha256(source_dependency_closure_sha256):
        raise Step11Rc0030ExperimentRuntimeError(
            "STEP11_RC0030_SOURCE_DEPENDENCY_CLOSURE_INVALID"
        )
    if (
        type(candidate_limit) is not int
        or type(candidate_limit) is bool
        or not 1 <= candidate_limit <= STEP11_RC0030_MAX_CANDIDATES
    ):
        raise Step11Rc0030ExperimentRuntimeError(
            "STEP11_RC0030_CANDIDATE_BOUND_EXCEEDED"
        )
    if (
        type(replan_limit) is not int
        or type(replan_limit) is bool
        or not 0 <= replan_limit <= STEP11_RC0030_MAX_REPLANS
    ):
        raise Step11Rc0030ExperimentRuntimeError(
            "STEP11_RC0030_REPLAN_BOUND_EXCEEDED"
        )

    state: dict[str, Any] = {
        "base_disposition": "fail_close",
        "base_candidate_count": 0,
        "base_inverse_prepass_count": 0,
        "experiment_candidate_count": 0,
        "base_body_parse_count": 0,
        "base_reuse_match_count": 0,
        "base_body_byte_inspection_count": 0,
        "selector_base_body_parse_count": 0,
        "selector_base_reuse_match_count": 0,
        "selector_base_body_byte_inspection_count": 0,
        "base_inverse_failure_code_counts": {},
        "forward_failure_code_counts": {},
        "successor_snapshot_sha256": None,
        "successor_authority_sha256": None,
        "successor_witness_sha256": None,
        "lexical_atom_specs_sha256": None,
        "surface_catalog_sha256": None,
        "base_inverse_contexts_sha256": None,
        "owner_binding_count": 0,
        "construction_atom_count": 0,
        "relation_endpoint_atom_count": 0,
        "semantic_link_atom_count": 0,
        "explicit_unknown_atom_count": 0,
        "verified_base_reuse_binding_count": 0,
    }
    baseline: Any | None = None
    successor: Any | None = None
    lexical_specs: Any | None = None
    candidates: list[Any] = []
    base_inverse_evaluations: list[Any] = []
    attempted_contexts: list[Any] = []
    contexts: list[Any] = []
    context_material: list[dict[str, Any]] = []
    selection: Any | None = None

    def finish(
        *,
        disposition: str,
        closed_codes: tuple[str, ...],
        gate_results: tuple[Any, ...] = (),
        selected_bytes: bytes | None = None,
        selected_parsed_witness: Any | None = None,
        selected_verified_binding: Any | None = None,
        selected_context: Any | None = None,
    ) -> Step11Rc0030ExperimentPrivateExecution:
        gate_counts = _gate_failure_counts(gate_results) if gate_results else ()
        hard_pass = sum(getattr(row, "hard_pass", None) is True for row in gate_results)
        context_by_candidate_id = {
            candidate.candidate_id: context
            for candidate, context in zip(candidates, contexts, strict=True)
        }
        gate_candidate_ids = tuple(
            getattr(row, "candidate_id", None) for row in gate_results
        )
        if (
            len(set(gate_candidate_ids)) != len(gate_candidate_ids)
            or any(row not in context_by_candidate_id for row in gate_candidate_ids)
        ):
            raise Step11Rc0030ExperimentRuntimeError(
                "STEP11_RC0030_GATE_RESULT_INVALID"
            )
        gate_contexts = tuple(
            context_by_candidate_id[row] for row in gate_candidate_ids
        )
        gate_parser_count = sum(
            getattr(row, "parser_invocation_count", -1)
            for row in gate_results
        )
        gate_matcher_count = sum(
            getattr(row, "matcher_invocation_count", -1)
            for row in gate_results
        )
        gate_body_byte_inspection_count = sum(
            getattr(row, "body_byte_inspection_count", -1)
            for row in gate_results
        )
        final_parser_count = (
            gate_parser_count
            - sum(row.parser_invocation_count for row in gate_contexts)
        )
        final_matcher_count = (
            gate_matcher_count
            - sum(row.matcher_invocation_count for row in gate_contexts)
        )
        final_body_byte_inspection_count = (
            gate_body_byte_inspection_count
            - sum(row.body_byte_inspection_count for row in gate_contexts)
        )
        body_byte_inspection_count = (
            state["base_body_byte_inspection_count"]
            + final_body_byte_inspection_count
        )
        inverse_counts = tuple(
            sorted(state["base_inverse_failure_code_counts"].items())
        )
        forward_counts = tuple(
            sorted(state["forward_failure_code_counts"].items())
        )
        result = _make_result(
            case_id=case_id,
            source_case_commitment=source_case_commitment,
            source_dependency_closure_sha256=source_dependency_closure_sha256,
            base_disposition=state["base_disposition"],
            disposition=disposition,
            closed_failure_codes=closed_codes,
            base_inverse_failure_code_counts=inverse_counts,
            forward_failure_code_counts=forward_counts,
            gate_failure_code_counts=gate_counts,
            bounded_candidate_limit=candidate_limit,
            bounded_replan_limit=replan_limit,
            base_candidate_count=state["base_candidate_count"],
            base_inverse_prepass_count=state["base_inverse_prepass_count"],
            experiment_candidate_count=len(candidates),
            base_inverse_rejected_candidate_count=sum(
                count for _code, count in inverse_counts
            ),
            forward_rejected_base_candidate_count=sum(
                count for _code, count in forward_counts
            ),
            evaluated_candidate_count=len(gate_results),
            base_body_parse_count=state["base_body_parse_count"],
            base_reuse_match_count=state["base_reuse_match_count"],
            final_body_parse_count=final_parser_count,
            final_surface_match_count=final_matcher_count,
            body_byte_inspection_count=body_byte_inspection_count,
            hard_gate_pass_count=hard_pass,
            rejected_candidate_count=len(gate_results) - hard_pass,
            replan_count=int(getattr(selection, "recovery_attempted", False) is True),
            selected_candidate_present=selected_bytes is not None,
            successor_snapshot_sha256=state["successor_snapshot_sha256"],
            successor_authority_sha256=state["successor_authority_sha256"],
            successor_witness_sha256=state["successor_witness_sha256"],
            lexical_atom_specs_sha256=state["lexical_atom_specs_sha256"],
            surface_catalog_sha256=state["surface_catalog_sha256"],
            base_inverse_contexts_sha256=state["base_inverse_contexts_sha256"],
            owner_binding_count=state["owner_binding_count"],
            construction_atom_count=state["construction_atom_count"],
            relation_endpoint_atom_count=state["relation_endpoint_atom_count"],
            semantic_link_atom_count=state["semantic_link_atom_count"],
            explicit_unknown_atom_count=state["explicit_unknown_atom_count"],
            verified_base_reuse_binding_count=(
                state["verified_base_reuse_binding_count"]
            ),
        )
        return _private_execution(
            body_free_result=result,
            base_execution=baseline,
            successor_snapshot=successor,
            lexical_atom_specs=lexical_specs,
            experiment_candidates=tuple(candidates),
            base_inverse_evaluations=tuple(base_inverse_evaluations),
            attempted_base_inverse_contexts=tuple(attempted_contexts),
            base_inverse_contexts=tuple(contexts),
            gate_results=gate_results,
            selection_result=selection,
            selected_final_utf8_bytes=selected_bytes,
            selected_parsed_witness=selected_parsed_witness,
            selected_verified_binding=selected_verified_binding,
            selected_base_inverse_context=selected_context,
        )

    try:
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
        from emlis_ai_step11_grounded_lexicalization_v3 import (
            Step11GroundedLexicalizationError,
            build_step11_rc0028_experiment_lexical_atom_specs,
            validate_step11_rc0028_experiment_lexical_atom_specs,
        )
        from emlis_ai_step11_hard_gate_v3 import (
            evaluate_step11_rc0030_experiment_base_inverse,
            select_step11_rc0030_experiment_candidate,
            step11_rc0030_experiment_base_inverse_evaluation_material,
        )
        from emlis_ai_step11_natural_surface_v3 import (
            STEP11_RC0030_EXPERIMENT_CANDIDATE_VERSION_ID as surface_version,
            Step11Rc0030BaseBodyExactReuseBinding,
            Step11NaturalSurfaceError,
            build_step11_rc0030_experiment_surface_candidate,
            validate_step11_rc0030_experiment_surface_candidate,
        )
        from emlis_ai_step11_rc0030_experiment_surface_catalog_v3 import (
            STEP11_RC0030_EXPERIMENT_SURFACE_CATALOG_SHA256,
        )
        from emlis_ai_step11_runtime_adapter_v3 import (
            execute_step11_offline_v3,
            validate_step11_runtime_execution,
        )
        from emlis_ai_nls_v3_artifact_contract import artifact_sha256

        if surface_version != STEP11_RC0030_EXPERIMENT_CANDIDATE_VERSION_ID:
            raise Step11Rc0030ExperimentRuntimeError(
                "STEP11_RC0030_CANDIDATE_VERSION_MISMATCH"
            )
        baseline = execute_step11_offline_v3(
            dict(current_input),
            candidate_version_id=STEP11_RC0030_BASE_CANDIDATE_VERSION_ID,
            source_dependency_closure_sha256=source_dependency_closure_sha256,
        )
        if validate_step11_runtime_execution(baseline):
            raise Step11Rc0030ExperimentRuntimeError(
                "STEP11_RC0030_BASE_RUNTIME_VALIDATION_FAILED"
            )
        if baseline.status == "selected":
            state["base_disposition"] = "selected"
        elif baseline.status == "v3_no_valid_candidate":
            state["base_disposition"] = "no_valid_candidate"
        else:
            raise Step11Rc0030ExperimentRuntimeError(
                "STEP11_RC0030_BASE_RUNTIME_STATUS_INVALID"
            )
        base_candidates = tuple(baseline.natural_candidates)
        state["base_candidate_count"] = len(base_candidates)
        if len(base_candidates) > candidate_limit:
            raise Step11Rc0030ExperimentRuntimeError(
                "STEP11_RC0030_CANDIDATE_BOUND_EXCEEDED"
            )
        if not base_candidates:
            return finish(
                disposition="no_valid_candidate",
                closed_codes=("STEP11_RC0030_BASE_CANDIDATE_SET_EMPTY",),
            )

        evidence_spans = tuple(build_evidence_ledger(baseline.normalized_input))
        resolver = build_evidence_span_resolver(
            evidence_spans,
            current_input=baseline.normalized_input,
        )
        successor = successor_owner.build_grounded_lexical_role_experiment_snapshot_successor(
            baseline.grounded_plan,
            resolver,
            observation_stage_context=baseline.observation_stage_context,
            original_input_bundle=baseline.normalized_input,
        )
        if successor_owner.validate_grounded_lexical_role_experiment_snapshot_successor(
            successor
        ):
            raise Step11Rc0030ExperimentRuntimeError(
                "STEP11_RC0030_SUCCESSOR_SNAPSHOT_INVALID"
            )
        if (
            successor.semantic_coverage_authorized is not False
            or successor.lexical_role_witness.semantic_coverage_authority != "none"
        ):
            raise Step11Rc0030ExperimentRuntimeError(
                "STEP11_RC0030_SEMANTIC_COVERAGE_SELF_CLAIM"
            )
        state["successor_snapshot_sha256"] = successor.experiment_snapshot_sha256
        state["successor_authority_sha256"] = (
            successor.relation_construction_authority.authority_sha256
        )
        state["successor_witness_sha256"] = (
            successor.lexical_role_witness.witness_sha256
        )
        state["surface_catalog_sha256"] = (
            STEP11_RC0030_EXPERIMENT_SURFACE_CATALOG_SHA256
        )

        lexical_specs = build_step11_rc0028_experiment_lexical_atom_specs(successor)
        if validate_step11_rc0028_experiment_lexical_atom_specs(
            lexical_specs,
            successor_snapshot=successor,
        ):
            raise Step11Rc0030ExperimentRuntimeError(
                "STEP11_RC0030_LEXICAL_ATOM_SPECS_INVALID"
            )
        if lexical_specs.semantic_coverage_authority != "none":
            raise Step11Rc0030ExperimentRuntimeError(
                "STEP11_RC0030_SEMANTIC_COVERAGE_SELF_CLAIM"
            )
        state["lexical_atom_specs_sha256"] = lexical_specs.specs_sha256
        state["owner_binding_count"] = len(lexical_specs.owner_bindings)
        state["construction_atom_count"] = len(lexical_specs.construction_atoms)
        state["relation_endpoint_atom_count"] = len(
            lexical_specs.relation_endpoint_atoms
        )
        state["semantic_link_atom_count"] = len(lexical_specs.semantic_link_atoms)
        state["explicit_unknown_atom_count"] = len(
            lexical_specs.explicit_unknown_atoms
        )

        for base_candidate in base_candidates:
            evaluation = evaluate_step11_rc0030_experiment_base_inverse(
                base_candidate,
                successor_snapshot=successor,
                inventory_result=baseline.inventory_result,
                content_plan=baseline.content_plan,
                current_input=baseline.projected_current_input,
            )
            base_inverse_evaluations.append(evaluation)
            state["base_inverse_prepass_count"] += 1
            state["base_body_parse_count"] += (
                evaluation.parser_invocation_count
            )
            state["base_reuse_match_count"] += (
                evaluation.matcher_invocation_count
            )
            state["base_body_byte_inspection_count"] += (
                evaluation.body_byte_inspection_count
            )
            context_material.append(
                step11_rc0030_experiment_base_inverse_evaluation_material(
                    evaluation
                )
            )
            state["base_inverse_contexts_sha256"] = artifact_sha256(
                context_material
            )
            if evaluation.hard_pass is not True:
                if (
                    evaluation.base_inverse_context is not None
                    or type(evaluation.failure_codes) is not tuple
                    or len(evaluation.failure_codes) != 1
                    or evaluation.failure_code != evaluation.failure_codes[0]
                ):
                    raise Step11Rc0030ExperimentRuntimeError(
                        "STEP11_RC0030_BASE_INVERSE_EVALUATION_INVALID"
                    )
                code = evaluation.failure_codes[0]
                counts = state["base_inverse_failure_code_counts"]
                counts[code] = counts.get(code, 0) + 1
                if evaluation.parser_invocation_count == 0:
                    raise Step11Rc0030ExperimentRuntimeError(code)
                continue
            context = evaluation.base_inverse_context
            if (
                context is None
                or evaluation.failure_code is not None
                or evaluation.failure_codes
            ):
                raise Step11Rc0030ExperimentRuntimeError(
                    "STEP11_RC0030_BASE_INVERSE_EVALUATION_INVALID"
                )
            verified_reuse = tuple(context.verified_base_reuse_bindings)
            attempted_contexts.append(context)
            state["verified_base_reuse_binding_count"] += len(verified_reuse)
            forward_reuse = tuple(
                Step11Rc0030BaseBodyExactReuseBinding(
                    source_atom_id=row.source_atom_id,
                    semantic_family=row.semantic_family,
                    base_parsed_atom_id=row.base_parsed_atom_id,
                    base_obligation_id=row.base_obligation_id,
                    match_basis=row.match_basis,
                    base_surface_sha256=row.base_surface_sha256,
                    source_authority_sha256=row.source_authority_sha256,
                    independent_binding_sha256=row.independent_binding_sha256,
                )
                for row in verified_reuse
            )
            try:
                candidate = build_step11_rc0030_experiment_surface_candidate(
                    base_candidate,
                    successor_snapshot=successor,
                    lexical_atom_specs=lexical_specs,
                    base_body_exact_reuse_bindings=forward_reuse,
                )
            except (
                Step11GroundedLexicalizationError,
                Step11NaturalSurfaceError,
            ) as error:
                code = _closed_forward_code(error)
                counts = state["forward_failure_code_counts"]
                counts[code] = counts.get(code, 0) + 1
                continue
            if validate_step11_rc0030_experiment_surface_candidate(
                candidate,
                successor_snapshot=successor,
                lexical_atom_specs=lexical_specs,
            ):
                raise Step11Rc0030ExperimentRuntimeError(
                    "STEP11_RC0030_CANDIDATE_REVALIDATION_FAILED"
                )
            candidates.append(candidate)
            contexts.append(context)
            state["selector_base_body_parse_count"] += (
                context.parser_invocation_count
            )
            state["selector_base_reuse_match_count"] += (
                context.matcher_invocation_count
            )
            state["selector_base_body_byte_inspection_count"] += (
                context.body_byte_inspection_count
            )

        if not candidates:
            inverse_codes = tuple(
                sorted(state["base_inverse_failure_code_counts"])
            )
            forward_codes = tuple(
                sorted(state["forward_failure_code_counts"])
            )
            return finish(
                disposition="no_valid_candidate",
                closed_codes=tuple(sorted(set(inverse_codes + forward_codes)))
                or ("STEP11_RC0030_NO_VALID_FORWARD_CANDIDATE",),
            )
        if len(candidates) > candidate_limit or len(contexts) != len(candidates):
            raise Step11Rc0030ExperimentRuntimeError(
                "STEP11_RC0030_CANDIDATE_BOUND_EXCEEDED"
            )
        state["base_inverse_contexts_sha256"] = artifact_sha256(context_material)

        selection = select_step11_rc0030_experiment_candidate(
            tuple(candidates),
            base_inverse_contexts=tuple(contexts),
            successor_snapshot=successor,
            lexical_atom_specs=lexical_specs,
            inventory_result=baseline.inventory_result,
            content_plan=baseline.content_plan,
            current_input=baseline.projected_current_input,
            candidate_limit=candidate_limit,
            replan_limit=replan_limit,
        )
        gate_results = tuple(selection.gate_results)
        ordered_ids = tuple(sorted(row.candidate_id for row in candidates))
        gate_by_id = {row.candidate_id: row for row in gate_results}
        final_parser_count = (
            selection.parser_invocation_count
            - state["selector_base_body_parse_count"]
        )
        final_matcher_count = (
            selection.matcher_invocation_count
            - state["selector_base_reuse_match_count"]
        )
        if (
            len(gate_by_id) != len(candidates)
            or len(tuple(selection.gate_evaluations)) != len(gate_results)
            or tuple(selection.evaluated_candidate_ids) != ordered_ids
            or selection.bounded_candidate_limit != candidate_limit
            or selection.bounded_replan_limit != replan_limit
            or selection.experimental_only is not True
            or selection.runtime_connected is not False
            or getattr(selection, "soft_rescue_used", None) is not False
            or selection.parser_invocation_count
            != sum(row.parser_invocation_count for row in gate_results)
            or selection.matcher_invocation_count
            != sum(row.matcher_invocation_count for row in gate_results)
            or selection.body_byte_inspection_count
            != sum(row.body_byte_inspection_count for row in gate_results)
            or not 0
            <= final_matcher_count
            <= final_parser_count
            <= len(gate_results)
            or selection.body_byte_inspection_count
            < state["selector_base_body_byte_inspection_count"]
            or (
                state["base_body_byte_inspection_count"]
                + selection.body_byte_inspection_count
                - state["selector_base_body_byte_inspection_count"]
            )
            > STEP11_RC0030_MAX_BODY_BYTE_INSPECTIONS
            or any(
                row.parser_invocation_count
                > STEP11_RC0030_MAX_PARSER_INVOCATIONS_PER_CANDIDATE
                or row.matcher_invocation_count
                > STEP11_RC0030_MAX_MATCHER_INVOCATIONS_PER_CANDIDATE
                or row.matcher_invocation_count > row.parser_invocation_count
                for row in gate_results
            )
        ):
            raise Step11Rc0030ExperimentRuntimeError(
                "STEP11_RC0030_SELECTION_COMMITMENT_MISMATCH"
            )
        if getattr(selection, "recovery_attempted", None) is True:
            if replan_limit < 1:
                raise Step11Rc0030ExperimentRuntimeError(
                    "STEP11_RC0030_REPLAN_BOUND_EXCEEDED"
                )
        context_by_id = {
            candidate.candidate_id: context
            for candidate, context in zip(candidates, contexts, strict=True)
        }
        if selection.status == "selected":
            selected = selection.selected_candidate
            gate = gate_by_id.get(selection.selected_candidate_id)
            if (
                selected not in candidates
                or selection.selected_candidate_id
                != getattr(selected, "candidate_id", None)
                or gate is None
                or gate.hard_pass is not True
                or type(selected.final_utf8_bytes) is not bytes
                or not selected.final_utf8_bytes
                or selection.selected_candidate_id not in context_by_id
            ):
                raise Step11Rc0030ExperimentRuntimeError(
                    "STEP11_RC0030_SELECTED_CANDIDATE_INVALID"
                )
            return finish(
                disposition="selected",
                closed_codes=(),
                gate_results=gate_results,
                selected_bytes=selected.final_utf8_bytes,
                selected_parsed_witness=selection.selected_parsed_witness,
                selected_verified_binding=selection.selected_verified_binding,
                selected_context=context_by_id[selection.selected_candidate_id],
            )
        if selection.status == "rc0030_experiment_no_valid_candidate":
            if (
                selection.selected_candidate is not None
                or selection.selected_candidate_id is not None
                or any(row.hard_pass is True for row in gate_results)
            ):
                raise Step11Rc0030ExperimentRuntimeError(
                    "STEP11_RC0030_NO_VALID_SELECTION_INVALID"
                )
            codes = tuple(code for code, _count in _gate_failure_counts(gate_results))
            return finish(
                disposition="no_valid_candidate",
                closed_codes=codes or ("STEP11_RC0030_NO_VALID_CANDIDATE",),
                gate_results=gate_results,
            )
        raise Step11Rc0030ExperimentRuntimeError(
            "STEP11_RC0030_SELECTION_STATUS_INVALID"
        )
    except Exception as error:
        gates = (
            tuple(getattr(selection, "gate_results", ()))
            if selection is not None
            else ()
        )
        closed_code = _closed_pipeline_code(error)
        try:
            return finish(
                disposition="fail_close",
                closed_codes=(closed_code,),
                gate_results=gates,
            )
        except Exception:
            selection = None
            return finish(
                disposition="fail_close",
                closed_codes=(closed_code,),
            )


def execute_step11_rc0030_experiment_private(
    current_input: Mapping[str, Any],
    *,
    case_id: str,
    source_case_commitment: str,
    source_dependency_closure_sha256: str,
    candidate_limit: int = STEP11_RC0030_MAX_CANDIDATES,
    replan_limit: int = STEP11_RC0030_MAX_REPLANS,
) -> Step11Rc0030ExperimentPrivateExecution:
    return _execute_step11_rc0030_experiment_internal(
        current_input,
        case_id=case_id,
        source_case_commitment=source_case_commitment,
        source_dependency_closure_sha256=source_dependency_closure_sha256,
        candidate_limit=candidate_limit,
        replan_limit=replan_limit,
    )


def run_step11_rc0030_experiment(
    current_input: Mapping[str, Any],
    *,
    case_id: str,
    source_case_commitment: str,
    source_dependency_closure_sha256: str,
    candidate_limit: int = STEP11_RC0030_MAX_CANDIDATES,
    replan_limit: int = STEP11_RC0030_MAX_REPLANS,
) -> Step11Rc0030ExperimentBodyFreeResult:
    return _execute_step11_rc0030_experiment_internal(
        current_input,
        case_id=case_id,
        source_case_commitment=source_case_commitment,
        source_dependency_closure_sha256=source_dependency_closure_sha256,
        candidate_limit=candidate_limit,
        replan_limit=replan_limit,
    ).body_free_result


def validate_step11_rc0030_experiment_result(value: Any) -> tuple[str, ...]:
    if type(value) is not Step11Rc0030ExperimentBodyFreeResult:
        return ("STEP11_RC0030_RESULT_TYPE_INVALID",)
    issues: set[str] = set()
    if (
        value.schema_version != STEP11_RC0030_EXPERIMENT_RUNTIME_RESULT_SCHEMA
        or value.adapter_version != STEP11_RC0030_EXPERIMENT_RUNTIME_ADAPTER_VERSION
        or value.execution_scope != STEP11_RC0030_EXPERIMENT_EXECUTION_SCOPE
        or value.base_candidate_version_id != STEP11_RC0030_BASE_CANDIDATE_VERSION_ID
        or value.experiment_candidate_version_id
        != STEP11_RC0030_EXPERIMENT_CANDIDATE_VERSION_ID
        or value.experimental_only is not True
        or value.body_free is not True
        or value.runtime_connected is not False
        or value.semantic_coverage_authority != "none"
    ):
        issues.add("STEP11_RC0030_RESULT_CONTRACT_MISMATCH")
    if (
        type(value.case_id) is not str
        or _CASE_ID_RE.fullmatch(value.case_id) is None
        or not _valid_sha256(value.source_case_commitment)
        or not _valid_sha256(value.source_dependency_closure_sha256)
    ):
        issues.add("STEP11_RC0030_SOURCE_COMMITMENT_MISMATCH")
    if value.base_disposition not in _DISPOSITIONS or value.disposition not in _DISPOSITIONS:
        issues.add("STEP11_RC0030_DISPOSITION_INVALID")
    if (
        tuple(sorted(set(value.closed_failure_codes))) != value.closed_failure_codes
        or any(
            type(code) is not str
            or _SHAREABLE_FAILURE_CODE_RE.fullmatch(code) is None
            for code in value.closed_failure_codes
        )
    ):
        issues.add("STEP11_RC0030_FAILURE_CODE_INVALID")
    if (
        tuple(sorted(value.base_inverse_failure_code_counts))
        != value.base_inverse_failure_code_counts
        or len(
            {code for code, _count in value.base_inverse_failure_code_counts}
        )
        != len(value.base_inverse_failure_code_counts)
        or any(
            type(code) is not str
            or _SHAREABLE_FAILURE_CODE_RE.fullmatch(code) is None
            or type(count) is not int
            or type(count) is bool
            or count < 1
            for code, count in value.base_inverse_failure_code_counts
        )
        or sum(
            count for _code, count in value.base_inverse_failure_code_counts
        )
        != value.base_inverse_rejected_candidate_count
    ):
        issues.add("STEP11_RC0030_BASE_INVERSE_FAILURE_COUNTS_INVALID")
    if (
        tuple(sorted(value.forward_failure_code_counts))
        != value.forward_failure_code_counts
        or len({code for code, _count in value.forward_failure_code_counts})
        != len(value.forward_failure_code_counts)
        or any(
            type(code) is not str
            or _SHAREABLE_FAILURE_CODE_RE.fullmatch(code) is None
            or type(count) is not int
            or type(count) is bool
            or count < 1
            for code, count in value.forward_failure_code_counts
        )
        or sum(count for _code, count in value.forward_failure_code_counts)
        != value.forward_rejected_base_candidate_count
    ):
        issues.add("STEP11_RC0030_FORWARD_FAILURE_COUNTS_INVALID")
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
        issues.add("STEP11_RC0030_GATE_FAILURE_COUNTS_INVALID")
    count_fields = (
        value.base_candidate_count,
        value.base_inverse_prepass_count,
        value.experiment_candidate_count,
        value.base_inverse_rejected_candidate_count,
        value.forward_rejected_base_candidate_count,
        value.evaluated_candidate_count,
        value.base_body_parse_count,
        value.base_reuse_match_count,
        value.final_body_parse_count,
        value.final_surface_match_count,
        value.body_byte_inspection_count,
        value.hard_gate_pass_count,
        value.rejected_candidate_count,
        value.replan_count,
        value.owner_binding_count,
        value.construction_atom_count,
        value.relation_endpoint_atom_count,
        value.semantic_link_atom_count,
        value.explicit_unknown_atom_count,
        value.verified_base_reuse_binding_count,
    )
    if any(type(item) is not int or type(item) is bool or item < 0 for item in count_fields):
        issues.add("STEP11_RC0030_RESULT_COUNT_INVALID")
    if (
        type(value.bounded_candidate_limit) is not int
        or type(value.bounded_candidate_limit) is bool
        or not 1 <= value.bounded_candidate_limit <= STEP11_RC0030_MAX_CANDIDATES
        or type(value.bounded_replan_limit) is not int
        or type(value.bounded_replan_limit) is bool
        or not 0 <= value.bounded_replan_limit <= STEP11_RC0030_MAX_REPLANS
        or value.base_candidate_count > value.bounded_candidate_limit
        or value.experiment_candidate_count > value.bounded_candidate_limit
        or value.base_inverse_prepass_count > value.base_candidate_count
        or value.experiment_candidate_count > value.base_inverse_prepass_count
        or value.experiment_candidate_count
        + value.base_inverse_rejected_candidate_count
        + value.forward_rejected_base_candidate_count
        > value.base_inverse_prepass_count
        or value.disposition != "fail_close"
        and value.base_inverse_prepass_count != value.base_candidate_count
        or value.disposition != "fail_close"
        and value.experiment_candidate_count
        + value.base_inverse_rejected_candidate_count
        + value.forward_rejected_base_candidate_count
        != value.base_inverse_prepass_count
        or value.evaluated_candidate_count > value.experiment_candidate_count
        or value.base_body_parse_count > value.base_inverse_prepass_count
        or value.base_reuse_match_count > value.base_body_parse_count
        or value.disposition != "fail_close"
        and value.base_body_parse_count != value.base_inverse_prepass_count
        or value.final_surface_match_count > value.final_body_parse_count
        or value.final_body_parse_count > value.evaluated_candidate_count
        or value.base_body_parse_count + value.final_body_parse_count
        > STEP11_RC0030_MAX_PARSER_INVOCATIONS
        or value.base_reuse_match_count + value.final_surface_match_count
        > STEP11_RC0030_MAX_MATCHER_INVOCATIONS
        or value.body_byte_inspection_count
        > STEP11_RC0030_MAX_BODY_BYTE_INSPECTIONS
        or value.hard_gate_pass_count + value.rejected_candidate_count
        != value.evaluated_candidate_count
        or value.replan_count > value.bounded_replan_limit
    ):
        issues.add("STEP11_RC0030_RESOURCE_BOUND_EXCEEDED")
    if value.disposition == "selected":
        if (
            value.selected_candidate_present is not True
            or value.hard_gate_pass_count < 1
            or value.closed_failure_codes
        ):
            issues.add("STEP11_RC0030_SELECTED_DISPOSITION_INVALID")
    elif value.disposition == "no_valid_candidate":
        if (
            value.selected_candidate_present is not False
            or value.hard_gate_pass_count != 0
            or not value.closed_failure_codes
        ):
            issues.add("STEP11_RC0030_NO_VALID_DISPOSITION_INVALID")
    elif value.disposition == "fail_close":
        if (
            value.selected_candidate_present is not False
            or not value.closed_failure_codes
        ):
            issues.add("STEP11_RC0030_FAIL_CLOSE_DISPOSITION_INVALID")
    commitments = (
        value.successor_snapshot_sha256,
        value.successor_authority_sha256,
        value.successor_witness_sha256,
        value.lexical_atom_specs_sha256,
        value.surface_catalog_sha256,
        value.base_inverse_contexts_sha256,
    )
    if (
        value.disposition != "fail_close"
        and value.base_candidate_count > 0
        and any(not _valid_sha256(item) for item in commitments)
    ):
        issues.add("STEP11_RC0030_ARTIFACT_COMMITMENT_MISMATCH")
    if (
        value.disposition != "fail_close"
        and value.base_candidate_count == 0
        and any(item is not None for item in commitments)
    ):
        issues.add("STEP11_RC0030_ARTIFACT_COMMITMENT_MISMATCH")
    if any(item is not None and not _valid_sha256(item) for item in commitments):
        issues.add("STEP11_RC0030_ARTIFACT_COMMITMENT_MISMATCH")
    try:
        expected_sha256 = _payload_sha256(_result_payload(value))
    except (TypeError, ValueError):
        expected_sha256 = ""
    if value.result_sha256 != expected_sha256 or not _valid_sha256(value.result_sha256):
        issues.add("STEP11_RC0030_RESULT_HASH_MISMATCH")
    return tuple(sorted(issues))


def validate_step11_rc0030_experiment_private_execution(value: Any) -> tuple[str, ...]:
    if type(value) is not Step11Rc0030ExperimentPrivateExecution:
        return ("STEP11_RC0030_PRIVATE_EXECUTION_TYPE_INVALID",)
    issues: set[str] = set()
    if (
        value.schema_version != STEP11_RC0030_EXPERIMENT_PRIVATE_EXECUTION_SCHEMA
        or value.adapter_version != STEP11_RC0030_EXPERIMENT_RUNTIME_ADAPTER_VERSION
        or value.private_body_full is not True
        or value.shareable is not False
        or value.experimental_only is not True
        or value.runtime_connected is not False
    ):
        issues.add("STEP11_RC0030_PRIVATE_EXECUTION_CONTRACT_MISMATCH")
    if validate_step11_rc0030_experiment_result(value.body_free_result):
        issues.add("STEP11_RC0030_PRIVATE_BODY_FREE_RESULT_INVALID")
        return tuple(sorted(issues))
    result = value.body_free_result
    if (
        value.case_id != result.case_id
        or value.source_case_commitment != result.source_case_commitment
        or value.source_dependency_closure_sha256
        != result.source_dependency_closure_sha256
        or len(value.experiment_candidates) != result.experiment_candidate_count
        or len(value.base_inverse_evaluations)
        != result.base_inverse_prepass_count
        or len(value.attempted_base_inverse_contexts)
        + result.base_inverse_rejected_candidate_count
        != result.base_inverse_prepass_count
        or len(value.base_inverse_contexts)
        != result.experiment_candidate_count
        or len(value.gate_results) != result.evaluated_candidate_count
    ):
        issues.add("STEP11_RC0030_PRIVATE_SOURCE_LINKAGE_MISMATCH")
    if value.selection_result is not None and tuple(
        getattr(value.selection_result, "gate_results", ())
    ) != value.gate_results:
        issues.add("STEP11_RC0030_PRIVATE_SELECTION_LINKAGE_MISMATCH")
    try:
        evaluation_parser_count = sum(
            row.parser_invocation_count
            for row in value.base_inverse_evaluations
        )
        evaluation_matcher_count = sum(
            row.matcher_invocation_count
            for row in value.base_inverse_evaluations
        )
        evaluation_byte_count = sum(
            row.body_byte_inspection_count
            for row in value.base_inverse_evaluations
        )
        evaluation_failure_counts: dict[str, int] = {}
        evaluation_contexts: list[Any] = []
        for row in value.base_inverse_evaluations:
            if row.hard_pass is True:
                evaluation_contexts.append(row.base_inverse_context)
            else:
                for code in row.failure_codes:
                    evaluation_failure_counts[code] = (
                        evaluation_failure_counts.get(code, 0) + 1
                    )
    except (AttributeError, TypeError):
        evaluation_parser_count = -1
        evaluation_matcher_count = -1
        evaluation_byte_count = -1
        evaluation_failure_counts = {"invalid": 1}
        evaluation_contexts = []
    if (
        evaluation_parser_count != result.base_body_parse_count
        or evaluation_matcher_count != result.base_reuse_match_count
        or any(
            getattr(row, "charged_body_scan_pass_count", None)
            != 2 * getattr(row, "parser_invocation_count", -1)
            or getattr(row, "body_byte_inspection_count", None)
            != getattr(row, "base_body_byte_count", -1)
            * getattr(row, "charged_body_scan_pass_count", -1)
            for row in value.base_inverse_evaluations
        )
        or tuple(sorted(evaluation_failure_counts.items()))
        != result.base_inverse_failure_code_counts
        or len(evaluation_contexts)
        != len(value.attempted_base_inverse_contexts)
        or any(
            not any(context is attempted for attempted in evaluation_contexts)
            for context in value.attempted_base_inverse_contexts
        )
    ):
        issues.add("STEP11_RC0030_PRIVATE_BASE_INVERSE_ACCOUNTING_MISMATCH")
    try:
        private_context_by_candidate_id = {
            candidate.candidate_id: context
            for candidate, context in zip(
                value.experiment_candidates,
                value.base_inverse_contexts,
                strict=True,
            )
        }
        retained_gate_byte_count = sum(
            row.body_byte_inspection_count for row in value.gate_results
        )
        retained_gate_base_byte_count = sum(
            private_context_by_candidate_id[row.candidate_id].body_byte_inspection_count
            for row in value.gate_results
        )
    except (AttributeError, KeyError, TypeError, ValueError):
        retained_gate_byte_count = -1
        retained_gate_base_byte_count = -1
    if result.body_byte_inspection_count != (
        evaluation_byte_count
        + retained_gate_byte_count
        - retained_gate_base_byte_count
    ):
        issues.add("STEP11_RC0030_PRIVATE_BODY_BYTE_ACCOUNTING_MISMATCH")
    try:
        candidate_base_ids = {
            row.base_candidate.candidate_id
            for row in value.experiment_candidates
        }
        context_base_ids = {
            row.source_base_candidate_id
            for row in value.base_inverse_contexts
        }
        attempted_base_ids = {
            row.source_base_candidate_id
            for row in value.attempted_base_inverse_contexts
        }
    except (AttributeError, TypeError):
        candidate_base_ids = set()
        context_base_ids = {"invalid"}
        attempted_base_ids = {"invalid"}
    if (
        candidate_base_ids != context_base_ids
        or len(candidate_base_ids) != len(value.experiment_candidates)
        or not context_base_ids <= attempted_base_ids
        or len(attempted_base_ids)
        != len(value.attempted_base_inverse_contexts)
        or any(
            not any(context is attempted for attempted in value.attempted_base_inverse_contexts)
            for context in value.base_inverse_contexts
        )
    ):
        issues.add("STEP11_RC0030_PRIVATE_BASE_CONTEXT_LINKAGE_MISMATCH")
    if result.disposition == "selected":
        selected = getattr(value.selection_result, "selected_candidate", None)
        selected_id = getattr(value.selection_result, "selected_candidate_id", None)
        if (
            selected not in value.experiment_candidates
            or selected_id != getattr(selected, "candidate_id", None)
            or type(value.selected_final_utf8_bytes) is not bytes
            or not value.selected_final_utf8_bytes
            or value.selected_final_utf8_bytes != getattr(selected, "final_utf8_bytes", None)
            or value.selected_parsed_witness
            is not getattr(value.selection_result, "selected_parsed_witness", None)
            or value.selected_verified_binding
            is not getattr(value.selection_result, "selected_verified_binding", None)
            or getattr(value.selected_verified_binding, "hard_verified", None)
            is not True
            or getattr(value.selected_verified_binding, "issue_codes", None) != ()
            or value.selected_base_inverse_context
            not in value.base_inverse_contexts
            or getattr(
                value.selected_base_inverse_context,
                "source_base_candidate_id",
                None,
            )
            != getattr(getattr(selected, "base_candidate", None), "candidate_id", None)
            or sum(
                getattr(row, "candidate_id", None) == selected_id
                and getattr(row, "hard_pass", None) is True
                for row in value.gate_results
            )
            != 1
        ):
            issues.add("STEP11_RC0030_PRIVATE_SELECTED_LINKAGE_MISMATCH")
    elif any(
        item is not None
        for item in (
            value.selected_final_utf8_bytes,
            value.selected_parsed_witness,
            value.selected_verified_binding,
            value.selected_base_inverse_context,
        )
    ):
        issues.add("STEP11_RC0030_PRIVATE_UNSELECTED_BODY_FORBIDDEN")
    return tuple(sorted(issues))


def step11_rc0030_experiment_result_material(
    value: Step11Rc0030ExperimentBodyFreeResult,
) -> dict[str, Any]:
    issues = validate_step11_rc0030_experiment_result(value)
    if issues:
        raise Step11Rc0030ExperimentRuntimeError(issues[0])
    return {**_result_payload(value), "result_sha256": value.result_sha256}


validate_step11_rc0030_experiment_runtime_result = (
    validate_step11_rc0030_experiment_result
)
step11_rc0030_experiment_runtime_result_material = (
    step11_rc0030_experiment_result_material
)


__all__ = [
    "STEP11_RC0030_BASE_CANDIDATE_VERSION_ID",
    "STEP11_RC0030_EXPERIMENT_CANDIDATE_VERSION_ID",
    "STEP11_RC0030_EXPERIMENT_EXECUTION_SCOPE",
    "STEP11_RC0030_EXPERIMENT_PRIVATE_EXECUTION_SCHEMA",
    "STEP11_RC0030_EXPERIMENT_RUNTIME_ADAPTER_VERSION",
    "STEP11_RC0030_EXPERIMENT_RUNTIME_RESULT_SCHEMA",
    "STEP11_RC0030_MAX_BODY_BYTE_INSPECTIONS",
    "STEP11_RC0030_MAX_CANDIDATES",
    "STEP11_RC0030_MAX_MATCHER_INVOCATIONS",
    "STEP11_RC0030_MAX_MATCHER_INVOCATIONS_PER_CANDIDATE",
    "STEP11_RC0030_MAX_PARSER_INVOCATIONS",
    "STEP11_RC0030_MAX_PARSER_INVOCATIONS_PER_CANDIDATE",
    "STEP11_RC0030_MAX_REPLANS",
    "Step11Rc0030ExperimentBodyFreeResult",
    "Step11Rc0030ExperimentPrivateExecution",
    "Step11Rc0030ExperimentRuntimeError",
    "Step11Rc0030ExperimentRuntimeResult",
    "execute_step11_rc0030_experiment_private",
    "run_step11_rc0030_experiment",
    "step11_rc0030_experiment_result_material",
    "step11_rc0030_experiment_runtime_result_material",
    "validate_step11_rc0030_experiment_private_execution",
    "validate_step11_rc0030_experiment_result",
    "validate_step11_rc0030_experiment_runtime_result",
]
