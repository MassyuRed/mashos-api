# -*- coding: utf-8 -*-
from __future__ import annotations

"""Dormant Step 10 runtime adapter for Natural Language Surface v3.

This module is deliberately reached from the reply service in one direction.
The production callable consults a default-disabled hook, while offline tooling
calls the private bridge explicitly.  Importantly, the disabled hook does not
import this module, so a dormant v3 import failure cannot take down v1.  A
successful execution always returns the exact canonical UTF-8 bytes that passed
the Step 9 selector and never counts a v1 fallback as v3.
"""

from dataclasses import dataclass
import hashlib
import re
import time
from typing import Any, Mapping

from emlis_ai_bounded_recovery_v3 import (
    BoundedRecoveryError,
    select_with_bounded_recovery,
)
from emlis_ai_canonical_renderer_v3 import (
    CanonicalSurfaceRenderError,
    open_request_lexical_authority,
)
from emlis_ai_content_selection_v3 import (
    ContentSelectionBuildError,
    build_content_selection_plan,
)
from emlis_ai_current_input_bundle import normalize_emlis_current_input
from emlis_ai_discourse_graph_planner_v3 import (
    DiscourseGraphPlannerError,
    build_discourse_graph_plans,
)
from emlis_ai_evidence_ledger_service import (
    build_evidence_ledger,
    build_evidence_span_resolver,
)
from emlis_ai_grounded_observation_plan import build_grounded_observation_plan
from emlis_ai_independent_semantic_matcher_v3 import (
    IndependentSemanticMatchError,
    open_independent_match_source_authority,
)
from emlis_ai_nls_v3_artifact_contract import artifact_sha256
from emlis_ai_observation_integrator_service import integrate_perspective_board
from emlis_ai_observation_stage_context_v3 import (
    ObservationStageContextBuildError,
    build_observation_stage_context,
)
from emlis_ai_perspective_board import build_perspective_board
from emlis_ai_perspective_observers import run_perspective_observers
from emlis_ai_safety_triage import build_emlis_safety_triage_decision
from emlis_ai_semantic_hard_gate_v3 import (
    SemanticHardGateError,
    build_semantic_candidate,
    derive_semantic_candidate_id,
)
from emlis_ai_semantic_obligation_inventory_v3 import (
    SemanticObligationInventoryError,
    SemanticObligationInventoryResult,
    build_grounded_source_snapshot,
    build_semantic_obligation_inventory,
)
from emlis_ai_step10_dependency_manifest_v3 import (
    FROZEN_STEP10_CANDIDATE_VERSION_ID,
    FROZEN_STEP10_DEPENDENCY_CLOSURE_SHA256,
    validate_step10_dependency_manifest,
)
from emlis_ai_step9_artifact_contract_v3 import (
    BoundedRecoveryResult,
    SemanticCandidate,
    SemanticSelectionResult,
    SelectorAttributes,
    selector_attributes_sha256,
    validate_hard_gate_result_structure,
    validate_recovery_trace_structure,
    validate_selector_decision_structure,
)
from emlis_ai_types import ReplyEnvelope


RUNTIME_STATE_SCHEMA = "cocolon.emlis.nls_v3.runtime_owner_state.v1"
RUNTIME_EXECUTION_SCHEMA = "cocolon.emlis.nls_v3.dormant_runtime_execution.v1"
RUNTIME_DELIVERY_SCHEMA = "cocolon.emlis.nls_v3.dormant_runtime_delivery.v1"
RUNTIME_ADAPTER_VERSION = "cocolon.emlis.nls_v3.runtime_adapter.step10.v1"
TESTER_ALLOWLIST_POLICY_SCHEMA = (
    "cocolon.emlis.nls_v3.tester_allowlist_policy.step10.v1"
)

RUNTIME_STATES = (
    "disabled",
    "offline",
    "shadow",
    "tester_only_preview",
    "owner",
    "stopped",
)
EXECUTION_SCOPES = ("offline_batch", "shadow", "tester_only_preview")
_SHA_RE = re.compile(r"^[0-9a-f]{64}$")


class DormantRuntimeAdapterError(ValueError):
    """Fail-closed adapter error that never embeds input or candidate text."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class RuntimeTransitionAuthority:
    """Body-free upstream evidence required for gated non-default states."""

    candidate_version_id: str
    source_dependency_closure_sha256: str
    saturation_gate_sha256: str | None = None
    tester_allowlist_policy_sha256: str | None = None
    new_release_candidate_after_stop: bool = False


@dataclass(frozen=True, slots=True)
class RuntimeOwnerState:
    schema_version: str
    state: str
    public_owner: str
    rollback_owner: str
    candidate_version_id: str | None
    tester_allowlist_policy_sha256: str | None
    v3_general_account_visible: bool
    body_free: bool = True


@dataclass(frozen=True, slots=True)
class TesterExecutionAuthority:
    """Opaque process-local proof issued only after allowlist commitment match."""

    account_identity_commitment: str
    allowlist_policy_sha256: str
    candidate_version_id: str
    source_dependency_closure_sha256: str


@dataclass(frozen=True, slots=True, repr=False)
class DormantRuntimeExecution:
    """Private execution bundle.  Body-bearing members are never public meta."""

    schema_version: str
    adapter_version: str
    candidate_version_id: str
    runtime_state: RuntimeOwnerState
    execution_scope: str
    status: str
    dependency_closure_sha256: str
    normalized_input: dict[str, Any]
    observation_stage_context: dict[str, Any]
    grounded_plan: Any
    inventory_result: SemanticObligationInventoryResult
    content_plan: dict[str, Any]
    initial_candidates: tuple[SemanticCandidate, ...]
    recovery_result: BoundedRecoveryResult
    final_utf8_bytes: bytes | None
    elapsed_ns: int
    v3_success: bool
    v1_fallback_used: bool
    v1_fallback_counts_as_v3_success: bool

    @property
    def selected_candidate(self) -> SemanticCandidate | None:
        return self.recovery_result.selection.selected_candidate


@dataclass(frozen=True, slots=True, repr=False)
class DormantRuntimeDelivery:
    """Private exact-body delivery result, distinct from v3 execution success."""

    schema_version: str
    status: str
    v3_status: str
    v3_failure_code: str | None
    delivery_owner: str
    reply_envelope: ReplyEnvelope
    delivered_utf8_bytes: bytes
    v3_success: bool
    v1_fallback_used: bool
    v1_fallback_counts_as_v3_success: bool


DEFAULT_RUNTIME_STATE = RuntimeOwnerState(
    schema_version=RUNTIME_STATE_SCHEMA,
    state="disabled",
    public_owner="grounded_sentence_surface_canonical_v1",
    rollback_owner="grounded_sentence_surface_canonical_v1",
    candidate_version_id=None,
    tester_allowlist_policy_sha256=None,
    v3_general_account_visible=False,
    body_free=True,
)

_TESTER_AUTHORITY_REGISTRY: dict[int, TesterExecutionAuthority] = {}


def _valid_sha(value: Any) -> bool:
    return type(value) is str and _SHA_RE.fullmatch(value) is not None


def _valid_nonzero_sha(value: Any) -> bool:
    return _valid_sha(value) and value != "0" * 64


def validate_runtime_owner_state(value: Any) -> tuple[str, ...]:
    issues: set[str] = set()
    if type(value) is not RuntimeOwnerState:
        return ("RUNTIME_STATE_TYPE_INVALID",)
    if value.schema_version != RUNTIME_STATE_SCHEMA:
        issues.add("RUNTIME_STATE_SCHEMA_INVALID")
    if value.state not in RUNTIME_STATES:
        issues.add("RUNTIME_STATE_VALUE_INVALID")
    if value.public_owner != "grounded_sentence_surface_canonical_v1":
        issues.add("STEP10_PUBLIC_OWNER_MUST_REMAIN_V1")
    if value.rollback_owner != "grounded_sentence_surface_canonical_v1":
        issues.add("STEP10_ROLLBACK_OWNER_MUST_REMAIN_V1")
    if value.state == "disabled" and value.candidate_version_id is not None:
        issues.add("DISABLED_STATE_CANDIDATE_FORBIDDEN")
    if value.state == "stopped":
        if (
            type(value.candidate_version_id) is not str
            or re.fullmatch(
                r"nls_v3_rc_[0-9]{4}", value.candidate_version_id
            ) is None
        ):
            issues.add("RUNTIME_STATE_CANDIDATE_INVALID")
    elif (
        value.state != "disabled"
        and value.candidate_version_id != FROZEN_STEP10_CANDIDATE_VERSION_ID
    ):
        issues.add("RUNTIME_STATE_CANDIDATE_INVALID")
    if value.state == "tester_only_preview":
        if not _valid_nonzero_sha(value.tester_allowlist_policy_sha256):
            issues.add("TESTER_ALLOWLIST_POLICY_INVALID")
    elif value.tester_allowlist_policy_sha256 is not None:
        issues.add("TESTER_ALLOWLIST_POLICY_FORBIDDEN")
    if value.v3_general_account_visible is not False:
        issues.add("STEP10_GENERAL_ACCOUNT_VISIBILITY_FORBIDDEN")
    if value.body_free is not True:
        issues.add("RUNTIME_STATE_BODY_FREE_REQUIRED")
    if value.state == "owner":
        issues.add("STEP10_OWNER_STATE_FORBIDDEN")
    return tuple(sorted(issues))


def transition_runtime_owner_state(
    current: RuntimeOwnerState,
    target_state: str,
    *,
    authority: RuntimeTransitionAuthority,
) -> RuntimeOwnerState:
    """Return a new pure state; Step 10 cannot enter the production owner state."""

    if validate_runtime_owner_state(current):
        raise DormantRuntimeAdapterError("RUNTIME_CURRENT_STATE_INVALID")
    if target_state not in RUNTIME_STATES:
        raise DormantRuntimeAdapterError("RUNTIME_TARGET_STATE_INVALID")
    if target_state == "owner":
        raise DormantRuntimeAdapterError("STEP10_OWNER_ACTIVATION_FORBIDDEN")
    if type(authority) is not RuntimeTransitionAuthority:
        raise DormantRuntimeAdapterError("RUNTIME_TRANSITION_AUTHORITY_REQUIRED")
    if (
        authority.candidate_version_id != FROZEN_STEP10_CANDIDATE_VERSION_ID
        or authority.source_dependency_closure_sha256
        != FROZEN_STEP10_DEPENDENCY_CLOSURE_SHA256
    ):
        raise DormantRuntimeAdapterError("RUNTIME_TRANSITION_AUTHORITY_INVALID")

    allowed = {
        "disabled": {"offline"},
        "offline": {"disabled", "shadow", "stopped"},
        "shadow": {"offline", "tester_only_preview", "stopped"},
        "tester_only_preview": {"shadow", "stopped"},
        "stopped": {"offline"},
    }
    if target_state not in allowed.get(current.state, set()):
        raise DormantRuntimeAdapterError("RUNTIME_TRANSITION_FORBIDDEN")
    if (
        current.state not in {"disabled", "stopped"}
        and current.candidate_version_id != authority.candidate_version_id
    ):
        raise DormantRuntimeAdapterError("RUNTIME_TRANSITION_CANDIDATE_MISMATCH")
    if target_state == "tester_only_preview" and not _valid_nonzero_sha(
        authority.tester_allowlist_policy_sha256
    ):
        raise DormantRuntimeAdapterError("TESTER_ALLOWLIST_AUTHORITY_REQUIRED")
    if target_state == "shadow" and not _valid_nonzero_sha(
        authority.saturation_gate_sha256
    ):
        raise DormantRuntimeAdapterError("SHADOW_SATURATION_AUTHORITY_REQUIRED")
    if current.state == "stopped" and authority.new_release_candidate_after_stop is not True:
        raise DormantRuntimeAdapterError("STOPPED_RC_REUSE_FORBIDDEN")

    candidate_version_id = (
        None if target_state == "disabled" else authority.candidate_version_id
    )
    tester_policy = (
        authority.tester_allowlist_policy_sha256
        if target_state == "tester_only_preview"
        else None
    )
    if (
        current.state == "stopped"
        and current.candidate_version_id == authority.candidate_version_id
    ):
        raise DormantRuntimeAdapterError("STOPPED_SAME_RC_REPROMOTION_FORBIDDEN")
    result = RuntimeOwnerState(
        schema_version=RUNTIME_STATE_SCHEMA,
        state=target_state,
        public_owner="grounded_sentence_surface_canonical_v1",
        rollback_owner="grounded_sentence_surface_canonical_v1",
        candidate_version_id=candidate_version_id,
        tester_allowlist_policy_sha256=tester_policy,
        v3_general_account_visible=False,
        body_free=True,
    )
    issues = validate_runtime_owner_state(result)
    if issues:
        raise DormantRuntimeAdapterError(issues[0])
    return result


def rollback_runtime_owner_state(
    current: RuntimeOwnerState,
    *,
    reason_code: str,
) -> RuntimeOwnerState:
    if validate_runtime_owner_state(current):
        raise DormantRuntimeAdapterError("RUNTIME_CURRENT_STATE_INVALID")
    if type(reason_code) is not str or not re.fullmatch(
        r"[A-Z][A-Z0-9_]{2,95}", reason_code
    ):
        raise DormantRuntimeAdapterError("ROLLBACK_REASON_CODE_INVALID")
    if current.state == "disabled":
        return current
    return RuntimeOwnerState(
        schema_version=RUNTIME_STATE_SCHEMA,
        state="stopped",
        public_owner="grounded_sentence_surface_canonical_v1",
        rollback_owner="grounded_sentence_surface_canonical_v1",
        candidate_version_id=current.candidate_version_id,
        tester_allowlist_policy_sha256=None,
        v3_general_account_visible=False,
        body_free=True,
    )


def _execution_allowed(
    state: RuntimeOwnerState,
    *,
    scope: str,
    tester_authority: TesterExecutionAuthority | None,
    account_identity_commitment: str | None = None,
) -> bool:
    if scope == "offline_batch":
        return state.state in {"disabled", "offline"}
    if scope == "shadow":
        return state.state == "shadow"
    if scope == "tester_only_preview":
        return bool(
            state.state == "tester_only_preview"
            and type(tester_authority) is TesterExecutionAuthority
            and _TESTER_AUTHORITY_REGISTRY.get(id(tester_authority))
            is tester_authority
            and tester_authority.allowlist_policy_sha256
            == state.tester_allowlist_policy_sha256
            and tester_authority.account_identity_commitment
            == account_identity_commitment
            and tester_authority.candidate_version_id
            == state.candidate_version_id
            and tester_authority.source_dependency_closure_sha256
            == FROZEN_STEP10_DEPENDENCY_CLOSURE_SHA256
        )
    return False


def tester_allowlist_policy_sha256(
    *,
    allowed_account_commitments: tuple[str, ...],
    candidate_version_id: str,
) -> str:
    """Commit an exact tester allowlist without putting identities in state."""

    if (
        type(allowed_account_commitments) is not tuple
        or not allowed_account_commitments
        or any(
            not _valid_nonzero_sha(item)
            for item in allowed_account_commitments
        )
        or len(set(allowed_account_commitments)) != len(allowed_account_commitments)
    ):
        raise DormantRuntimeAdapterError("TESTER_ALLOWLIST_INVALID")
    if candidate_version_id != FROZEN_STEP10_CANDIDATE_VERSION_ID:
        raise DormantRuntimeAdapterError("TESTER_CANDIDATE_VERSION_INVALID")
    return artifact_sha256(
        {
            "schema_version": TESTER_ALLOWLIST_POLICY_SCHEMA,
            "candidate_version_id": candidate_version_id,
            "source_dependency_closure_sha256": (
                FROZEN_STEP10_DEPENDENCY_CLOSURE_SHA256
            ),
            "allowed_account_identity_commitments": sorted(
                allowed_account_commitments
            ),
        }
    )


def issue_tester_execution_authority(
    *,
    account_identity_commitment: str,
    allowed_account_commitments: tuple[str, ...],
    allowlist_policy_sha256: str,
    candidate_version_id: str,
) -> TesterExecutionAuthority:
    """Issue an opaque capability from body-free, upstream-verified material."""

    if not _valid_nonzero_sha(account_identity_commitment):
        raise DormantRuntimeAdapterError("TESTER_ACCOUNT_COMMITMENT_INVALID")
    expected_policy_sha256 = tester_allowlist_policy_sha256(
        allowed_account_commitments=allowed_account_commitments,
        candidate_version_id=candidate_version_id,
    )
    if account_identity_commitment not in allowed_account_commitments:
        raise DormantRuntimeAdapterError("TESTER_ACCOUNT_NOT_ALLOWLISTED")
    if allowlist_policy_sha256 != expected_policy_sha256:
        raise DormantRuntimeAdapterError("TESTER_ALLOWLIST_POLICY_MISMATCH")
    authority = TesterExecutionAuthority(
        account_identity_commitment=account_identity_commitment,
        allowlist_policy_sha256=allowlist_policy_sha256,
        candidate_version_id=candidate_version_id,
        source_dependency_closure_sha256=FROZEN_STEP10_DEPENDENCY_CLOSURE_SHA256,
    )
    _TESTER_AUTHORITY_REGISTRY[id(authority)] = authority
    return authority


def execute_dormant_v3(
    current_input: Mapping[str, Any],
    *,
    candidate_version_id: str,
    runtime_state: RuntimeOwnerState = DEFAULT_RUNTIME_STATE,
    execution_scope: str = "offline_batch",
    tester_authority: TesterExecutionAuthority | None = None,
    account_identity_commitment: str | None = None,
) -> DormantRuntimeExecution:
    """Execute the complete Step 4--9 path without changing public ownership."""

    if validate_step10_dependency_manifest():
        raise DormantRuntimeAdapterError("STEP10_DEPENDENCY_DRIFT")
    if validate_runtime_owner_state(runtime_state):
        raise DormantRuntimeAdapterError("RUNTIME_STATE_INVALID")
    if execution_scope not in EXECUTION_SCOPES:
        raise DormantRuntimeAdapterError("RUNTIME_EXECUTION_SCOPE_INVALID")
    if not _execution_allowed(
        runtime_state,
        scope=execution_scope,
        tester_authority=tester_authority,
        account_identity_commitment=account_identity_commitment,
    ):
        raise DormantRuntimeAdapterError("RUNTIME_EXECUTION_NOT_AUTHORIZED")
    if type(current_input) is not dict:
        raise DormantRuntimeAdapterError("RUNTIME_INPUT_MAPPING_REQUIRED")
    if candidate_version_id != FROZEN_STEP10_CANDIDATE_VERSION_ID:
        raise DormantRuntimeAdapterError("RUNTIME_CANDIDATE_VERSION_INVALID")
    if (
        runtime_state.candidate_version_id is not None
        and runtime_state.candidate_version_id != candidate_version_id
    ):
        raise DormantRuntimeAdapterError("RUNTIME_CANDIDATE_VERSION_MISMATCH")

    started = time.perf_counter_ns()
    try:
        normalized_input = normalize_emlis_current_input(dict(current_input))
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
        discourse = build_discourse_graph_plans(inventory, content_plan)
        lexical_authority = open_request_lexical_authority(
            inventory,
            grounded_plan=grounded_plan,
            resolver=resolver,
            observation_stage_context=stage,
            original_input_bundle=normalized_input,
        )
        match_authority = open_independent_match_source_authority(
            inventory,
            grounded_plan=grounded_plan,
            resolver=resolver,
            observation_stage_context=stage,
            original_input_bundle=normalized_input,
        )
        initial_candidates = tuple(
            build_semantic_candidate(
                plan,
                inventory_result=inventory,
                content_plan=content_plan,
                lexical_authority=lexical_authority,
                match_authority=match_authority,
            )
            for plan in discourse.plans
        )
        recovery = select_with_bounded_recovery(
            initial_candidates,
            inventory_result=inventory,
            content_plan=content_plan,
            lexical_authority=lexical_authority,
            match_authority=match_authority,
        )
    except (
        AttributeError,
        BoundedRecoveryError,
        CanonicalSurfaceRenderError,
        ContentSelectionBuildError,
        DiscourseGraphPlannerError,
        IndependentSemanticMatchError,
        KeyError,
        ObservationStageContextBuildError,
        RecursionError,
        SemanticHardGateError,
        SemanticObligationInventoryError,
        TypeError,
        UnicodeError,
        ValueError,
    ) as exc:
        code = getattr(exc, "code", None)
        if type(code) is not str or not re.fullmatch(r"[A-Z0-9_]{3,95}", code):
            code = "DORMANT_RUNTIME_PIPELINE_REJECTED"
        raise DormantRuntimeAdapterError(code) from exc

    selected = recovery.selection.selected_candidate
    final_bytes: bytes | None = None
    status = recovery.selection.decision.status
    if status == "selected":
        rendered = getattr(selected, "rendered_surface", None)
        candidate_bytes = getattr(rendered, "utf8_bytes", None)
        if type(candidate_bytes) is not bytes or not candidate_bytes:
            raise DormantRuntimeAdapterError("SELECTED_CANDIDATE_BYTES_INVALID")
        try:
            decoded = candidate_bytes.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise DormantRuntimeAdapterError("SELECTED_CANDIDATE_UTF8_INVALID") from exc
        if decoded.encode("utf-8", errors="strict") != candidate_bytes:
            raise DormantRuntimeAdapterError("SELECTED_CANDIDATE_BYTES_CHANGED")
        final_bytes = candidate_bytes
    elif status != "v3_no_valid_candidate":
        raise DormantRuntimeAdapterError("RUNTIME_SELECTOR_STATUS_INVALID")

    elapsed = time.perf_counter_ns() - started
    return DormantRuntimeExecution(
        schema_version=RUNTIME_EXECUTION_SCHEMA,
        adapter_version=RUNTIME_ADAPTER_VERSION,
        candidate_version_id=candidate_version_id,
        runtime_state=runtime_state,
        execution_scope=execution_scope,
        status=status,
        dependency_closure_sha256=FROZEN_STEP10_DEPENDENCY_CLOSURE_SHA256,
        normalized_input=normalized_input,
        observation_stage_context=stage,
        grounded_plan=grounded_plan,
        inventory_result=inventory,
        content_plan=content_plan,
        initial_candidates=initial_candidates,
        recovery_result=recovery,
        final_utf8_bytes=final_bytes,
        elapsed_ns=elapsed,
        v3_success=status == "selected",
        v1_fallback_used=False,
        v1_fallback_counts_as_v3_success=False,
    )


def validate_dormant_runtime_execution(value: Any) -> tuple[str, ...]:
    """Independently re-check the private adapter bundle before any mapping."""

    issues: set[str] = set()
    if type(value) is not DormantRuntimeExecution:
        return ("RUNTIME_EXECUTION_TYPE_INVALID",)
    if validate_step10_dependency_manifest():
        issues.add("RUNTIME_EXECUTION_DEPENDENCY_DRIFT")
    if value.schema_version != RUNTIME_EXECUTION_SCHEMA:
        issues.add("RUNTIME_EXECUTION_SCHEMA_INVALID")
    if value.adapter_version != RUNTIME_ADAPTER_VERSION:
        issues.add("RUNTIME_ADAPTER_VERSION_INVALID")
    if value.candidate_version_id != FROZEN_STEP10_CANDIDATE_VERSION_ID:
        issues.add("RUNTIME_EXECUTION_CANDIDATE_INVALID")
    if validate_runtime_owner_state(value.runtime_state):
        issues.add("RUNTIME_EXECUTION_STATE_INVALID")
    if value.dependency_closure_sha256 != FROZEN_STEP10_DEPENDENCY_CLOSURE_SHA256:
        issues.add("RUNTIME_EXECUTION_DEPENDENCY_MISMATCH")
    if (value.runtime_state.state, value.execution_scope) not in {
        ("disabled", "offline_batch"),
        ("offline", "offline_batch"),
        ("shadow", "shadow"),
        ("tester_only_preview", "tester_only_preview"),
    }:
        issues.add("RUNTIME_EXECUTION_STATE_SCOPE_INVALID")
    if (
        value.runtime_state.candidate_version_id is not None
        and value.runtime_state.candidate_version_id != value.candidate_version_id
    ):
        issues.add("RUNTIME_EXECUTION_STATE_CANDIDATE_MISMATCH")
    expected_initial_candidates: tuple[SemanticCandidate, ...] | None = None
    expected_recovery: BoundedRecoveryResult | None = None
    if (
        type(value.normalized_input) is not dict
        or type(value.observation_stage_context) is not dict
        or type(value.inventory_result) is not SemanticObligationInventoryResult
        or type(value.content_plan) is not dict
        or type(value.initial_candidates) is not tuple
    ):
        issues.add("RUNTIME_EXECUTION_SOURCE_LINEAGE_INVALID")
    else:
        try:
            expected_spans = tuple(build_evidence_ledger(value.normalized_input))
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
            expected_resolver = build_evidence_span_resolver(
                expected_spans,
                current_input=value.normalized_input,
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
            expected_content_plan = build_content_selection_plan(
                expected_inventory
            )
            expected_discourse = build_discourse_graph_plans(
                expected_inventory,
                expected_content_plan,
            )
            expected_lexical_authority = open_request_lexical_authority(
                expected_inventory,
                grounded_plan=expected_grounded_plan,
                resolver=expected_resolver,
                observation_stage_context=expected_stage,
                original_input_bundle=value.normalized_input,
            )
            expected_match_authority = open_independent_match_source_authority(
                expected_inventory,
                grounded_plan=expected_grounded_plan,
                resolver=expected_resolver,
                observation_stage_context=expected_stage,
                original_input_bundle=value.normalized_input,
            )
            expected_initial_candidates = tuple(
                build_semantic_candidate(
                    plan,
                    inventory_result=expected_inventory,
                    content_plan=expected_content_plan,
                    lexical_authority=expected_lexical_authority,
                    match_authority=expected_match_authority,
                )
                for plan in expected_discourse.plans
            )
            expected_recovery = select_with_bounded_recovery(
                expected_initial_candidates,
                inventory_result=expected_inventory,
                content_plan=expected_content_plan,
                lexical_authority=expected_lexical_authority,
                match_authority=expected_match_authority,
            )
        except (
            AttributeError,
            BoundedRecoveryError,
            CanonicalSurfaceRenderError,
            ContentSelectionBuildError,
            DiscourseGraphPlannerError,
            IndependentSemanticMatchError,
            KeyError,
            ObservationStageContextBuildError,
            RecursionError,
            SemanticHardGateError,
            SemanticObligationInventoryError,
            TypeError,
            UnicodeError,
            ValueError,
        ):
            issues.add("RUNTIME_EXECUTION_SOURCE_LINEAGE_INVALID")
        else:
            if (
                expected_stage != value.observation_stage_context
                or expected_grounded_plan != value.grounded_plan
                or expected_inventory != value.inventory_result
                or expected_content_plan != value.content_plan
                or expected_initial_candidates != value.initial_candidates
                or expected_recovery != value.recovery_result
            ):
                issues.add("RUNTIME_EXECUTION_SOURCE_LINEAGE_MISMATCH")
    if type(value.recovery_result) is not BoundedRecoveryResult:
        issues.add("RUNTIME_RECOVERY_RESULT_INVALID")
        return tuple(sorted(issues))
    selection = value.recovery_result.selection
    if type(selection) is not SemanticSelectionResult:
        issues.add("RUNTIME_SELECTION_RESULT_INVALID")
        return tuple(sorted(issues))
    decision = selection.decision
    trace = value.recovery_result.trace
    if validate_selector_decision_structure(decision):
        issues.add("RUNTIME_SELECTOR_DECISION_INVALID")
    if validate_recovery_trace_structure(trace):
        issues.add("RUNTIME_RECOVERY_TRACE_INVALID")
    gate_results = selection.gate_results
    gate_rows_valid = (
        type(gate_results) is tuple
        and not any(validate_hard_gate_result_structure(row) for row in gate_results)
    )
    if not gate_rows_valid:
        issues.add("RUNTIME_HARD_GATE_RESULT_INVALID")
        gate_results = ()
    gate_ids = tuple(sorted(row.candidate_id for row in gate_results))
    if gate_ids != getattr(decision, "evaluated_candidate_ids", None):
        issues.add("RUNTIME_GATE_DECISION_CANDIDATE_SET_MISMATCH")
    if (
        value.status != decision.status
        or value.status != trace.final_status
        or decision.selected_candidate_id != trace.selected_candidate_id
    ):
        issues.add("RUNTIME_DECISION_TRACE_MISMATCH")
    selected = selection.selected_candidate
    selected_status = value.status == "selected"
    if selected_status:
        rendered = getattr(selected, "rendered_surface", None)
        verified_bytes = getattr(rendered, "utf8_bytes", None)
        if (
            type(selected) is not SemanticCandidate
            or type(verified_bytes) is not bytes
            or not verified_bytes
            or value.final_utf8_bytes != verified_bytes
        ):
            issues.add("RUNTIME_VERIFIED_FINAL_BYTES_MISMATCH")
        else:
            try:
                if verified_bytes.decode("utf-8", errors="strict").encode("utf-8") != verified_bytes:
                    issues.add("RUNTIME_VERIFIED_FINAL_BYTES_MISMATCH")
            except UnicodeDecodeError:
                issues.add("RUNTIME_VERIFIED_FINAL_BYTES_MISMATCH")
        if type(selected) is SemanticCandidate:
            try:
                derived_selected_id = derive_semantic_candidate_id(
                    selected,
                    inventory_result=value.inventory_result,
                )
            except (AttributeError, KeyError, TypeError, ValueError, UnicodeError):
                issues.add("RUNTIME_SELECTED_CANDIDATE_ID_INVALID")
            else:
                if derived_selected_id != decision.selected_candidate_id:
                    issues.add("RUNTIME_SELECTED_CANDIDATE_ID_MISMATCH")
                matching_gates = tuple(
                    row for row in gate_results
                    if row.candidate_id == decision.selected_candidate_id
                )
                if (
                    len(matching_gates) != 1
                    or matching_gates[0].hard_pass is not True
                    or matching_gates[0].selector_eligible is not True
                    or type(matching_gates[0].selector_attributes)
                    is not SelectorAttributes
                ):
                    issues.add("RUNTIME_SELECTED_HARD_GATE_MISMATCH")
                else:
                    selected_gate = matching_gates[0]
                    if (
                        selector_attributes_sha256(
                            selected_gate.selector_attributes
                        )
                        != decision.selection_attributes_sha256
                    ):
                        issues.add("RUNTIME_SELECTED_ATTRIBUTES_MISMATCH")
                    if (
                        selected_gate.candidate_text_sha256
                        != hashlib.sha256(verified_bytes).hexdigest()
                    ):
                        issues.add("RUNTIME_SELECTED_TEXT_HASH_MISMATCH")
            rendered_sha = getattr(rendered, "sha256", None)
            if (
                type(verified_bytes) is bytes
                and rendered_sha != hashlib.sha256(verified_bytes).hexdigest()
            ):
                issues.add("RUNTIME_RENDERED_SURFACE_HASH_MISMATCH")
    elif value.status == "v3_no_valid_candidate":
        if selected is not None or value.final_utf8_bytes is not None:
            issues.add("RUNTIME_NO_VALID_CANDIDATE_BODY_FORBIDDEN")
        if any(
            row.hard_pass is True or row.selector_eligible is True
            for row in gate_results
        ):
            issues.add("RUNTIME_NO_VALID_CANDIDATE_GATE_MISMATCH")
    else:
        issues.add("RUNTIME_EXECUTION_STATUS_INVALID")
    if (
        value.v3_success is not selected_status
        or decision.v3_success is not selected_status
        or trace.v3_success is not selected_status
        or value.v1_fallback_used is not False
        or value.v1_fallback_counts_as_v3_success is not False
        or decision.v1_fallback_used is not False
        or decision.v1_fallback_counts_as_v3_success is not False
        or trace.v1_fallback_used is not False
        or trace.v1_fallback_counts_as_v3_success is not False
    ):
        issues.add("RUNTIME_EXECUTION_SUCCESS_BOUNDARY_INVALID")
    if (
        type(value.elapsed_ns) is not int
        or type(value.elapsed_ns) is bool
        or value.elapsed_ns < 0
    ):
        issues.add("RUNTIME_EXECUTION_LATENCY_INVALID")
    if (
        type(value.normalized_input) is not dict
        or type(value.observation_stage_context) is not dict
        or type(value.content_plan) is not dict
        or type(value.initial_candidates) is not tuple
        or any(type(item) is not SemanticCandidate for item in value.initial_candidates)
    ):
        issues.add("RUNTIME_EXECUTION_PRIVATE_MATERIAL_INVALID")
    else:
        try:
            initial_ids = tuple(sorted(
                derive_semantic_candidate_id(
                    candidate,
                    inventory_result=value.inventory_result,
                )
                for candidate in value.initial_candidates
            ))
        except (AttributeError, KeyError, TypeError, ValueError, UnicodeError):
            issues.add("RUNTIME_INITIAL_CANDIDATE_SET_INVALID")
        else:
            if initial_ids != getattr(trace, "initial_candidate_ids", None):
                issues.add("RUNTIME_INITIAL_CANDIDATE_SET_MISMATCH")
    return tuple(sorted(issues))


def _runtime_execution_body_free_summary_unchecked(
    execution: DormantRuntimeExecution,
) -> dict[str, Any]:
    decision = execution.recovery_result.selection.decision
    selected = execution.selected_candidate
    ledger = execution.inventory_result.ledger
    required_ids = (
        ledger.get("required_obligation_ids", []) if type(ledger) is dict else []
    )
    binding = selected.verified_surface_binding if selected is not None else {}
    witness = selected.parsed_surface_witness if selected is not None else {}
    surface_ast = selected.surface_ast if selected is not None else {}
    sections = surface_ast.get("sections", []) if type(surface_ast) is dict else []
    sentence_count = sum(
        len(section.get("sentences", []))
        for section in sections
        if type(section) is dict and type(section.get("sentences")) is list
    )
    return {
        "schema_version": "cocolon.emlis.nls_v3.runtime_execution_summary.v1",
        "adapter_version": execution.adapter_version,
        "candidate_version_id": execution.candidate_version_id,
        "runtime_state": execution.runtime_state.state,
        "public_owner": execution.runtime_state.public_owner,
        "execution_scope": execution.execution_scope,
        "status": execution.status,
        "source_dependency_closure_sha256": execution.dependency_closure_sha256,
        "selected_candidate_present": decision.selected_candidate_id is not None,
        "evaluated_candidate_count": len(decision.evaluated_candidate_ids),
        "rejected_candidate_count": len(decision.rejected_candidate_ids),
        "hard_gate_pass_count": sum(
            result.hard_pass
            for result in execution.recovery_result.selection.gate_results
        ),
        "recovery_attempt_count": len(execution.recovery_result.trace.attempts),
        "latency_ns": execution.elapsed_ns,
        "semantic_metrics": {
            "required_obligation_count": len(required_ids),
            "bound_obligation_count": len(
                binding.get("bindings", []) if type(binding) is dict else []
            ),
            "semantic_atom_count": len(
                witness.get("semantic_atoms", []) if type(witness) is dict else []
            ),
            "section_count": len(sections),
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


def runtime_execution_body_free_summary(
    execution: DormantRuntimeExecution,
) -> dict[str, Any]:
    issues = validate_dormant_runtime_execution(execution)
    if issues:
        raise DormantRuntimeAdapterError(issues[0])
    return _runtime_execution_body_free_summary_unchecked(execution)


def map_verified_v3_bytes_to_reply_envelope(
    execution: DormantRuntimeExecution,
) -> ReplyEnvelope:
    """Map selected bytes without normalization; shadow is never visible."""

    issues = validate_dormant_runtime_execution(execution)
    if issues:
        raise DormantRuntimeAdapterError(issues[0])
    if execution.execution_scope == "shadow":
        raise DormantRuntimeAdapterError("SHADOW_BODY_VISIBILITY_FORBIDDEN")
    if execution.status != "selected" or execution.final_utf8_bytes is None:
        raise DormantRuntimeAdapterError("V3_SELECTED_BYTES_REQUIRED")
    text = execution.final_utf8_bytes.decode("utf-8", errors="strict")
    if not text or text.encode("utf-8", errors="strict") != execution.final_utf8_bytes:
        raise DormantRuntimeAdapterError("V3_PUBLIC_ENVELOPE_BYTE_MISMATCH")
    private_summary = _runtime_execution_body_free_summary_unchecked(execution)
    public_runtime_summary = {
        "schema_version": private_summary["schema_version"],
        "adapter_version": private_summary["adapter_version"],
        "runtime_state": private_summary["runtime_state"],
        "public_owner": private_summary["public_owner"],
        "execution_scope": private_summary["execution_scope"],
        "status": private_summary["status"],
        "v3_success": private_summary["v3_success"],
        "v1_fallback_used": private_summary["v1_fallback_used"],
        "v1_fallback_counts_as_v3_success": private_summary[
            "v1_fallback_counts_as_v3_success"
        ],
        "body_free": True,
    }
    meta = {
        "version": "emlis_ai_v3",
        "kernel_version": "grounded_natural_language_surface_v3.step10.dormant",
        "observation_status": "passed",
        "public_observation_status": "passed",
        "public_comment_present": True,
        "observation_reply_kind": "eligible_observation",
        "delivery_status": "passed",
        "generation_path": "grounded_natural_language_surface_v3",
        "generation_method": "model_free_typed_surface_ast",
        "composer_source": "nls_v3_canonical_renderer",
        "used_sources": ["current_input"],
        "used_memory_layers": ["canonical_history"],
        "fallback_used": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "public_contract_changed": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "nls_v3_runtime": public_runtime_summary,
    }
    return ReplyEnvelope(
        comment_text=text,
        meta=meta,
        used_evidence=[],
        evidence_by_line={},
        used_memory_layers=["canonical_history"],
        fallback_used=False,
    )


def resolve_dormant_runtime_delivery(
    execution: DormantRuntimeExecution | None,
    *,
    v1_fallback: ReplyEnvelope | None = None,
    v3_failure_code: str | None = None,
) -> DormantRuntimeDelivery:
    """Resolve exact v3 bytes or an explicitly supplied v1 fallback.

    This helper never changes the public owner or route.  It exists so local
    integration can prove that a no-valid/exception outcome may continue with
    the caller's existing v1 envelope while remaining a v3 failure.
    """

    if execution is not None:
        issues = validate_dormant_runtime_execution(execution)
        if issues:
            raise DormantRuntimeAdapterError(issues[0])
        if execution.status == "selected":
            if v1_fallback is not None or v3_failure_code is not None:
                raise DormantRuntimeAdapterError(
                    "V3_SELECTED_FALLBACK_MATERIAL_FORBIDDEN"
                )
            envelope = map_verified_v3_bytes_to_reply_envelope(execution)
            delivery = DormantRuntimeDelivery(
                schema_version=RUNTIME_DELIVERY_SCHEMA,
                status="v3_selected",
                v3_status="selected",
                v3_failure_code=None,
                delivery_owner="nls_v3_canonical_renderer",
                reply_envelope=envelope,
                delivered_utf8_bytes=execution.final_utf8_bytes or b"",
                v3_success=True,
                v1_fallback_used=False,
                v1_fallback_counts_as_v3_success=False,
            )
            validate_dormant_runtime_delivery(delivery, raise_on_error=True)
            return delivery
        v3_status = "v3_no_valid_candidate"
        if v3_failure_code is not None:
            raise DormantRuntimeAdapterError(
                "NO_VALID_CANDIDATE_FAILURE_CODE_FORBIDDEN"
            )
    else:
        v3_status = "exception"
        if type(v3_failure_code) is not str or re.fullmatch(
            r"[A-Z][A-Z0-9_]{2,95}", v3_failure_code
        ) is None:
            raise DormantRuntimeAdapterError("V3_FAILURE_CODE_REQUIRED")
    if type(v1_fallback) is not ReplyEnvelope:
        raise DormantRuntimeAdapterError("V1_FALLBACK_ENVELOPE_REQUIRED")
    if type(v1_fallback.comment_text) is not str:
        raise DormantRuntimeAdapterError("V1_FALLBACK_BODY_INVALID")
    fallback_bytes = v1_fallback.comment_text.encode("utf-8", errors="strict")
    delivery = DormantRuntimeDelivery(
        schema_version=RUNTIME_DELIVERY_SCHEMA,
        status="v1_fallback",
        v3_status=v3_status,
        v3_failure_code=v3_failure_code,
        delivery_owner="grounded_sentence_surface_canonical_v1",
        reply_envelope=v1_fallback,
        delivered_utf8_bytes=fallback_bytes,
        v3_success=False,
        v1_fallback_used=True,
        v1_fallback_counts_as_v3_success=False,
    )
    validate_dormant_runtime_delivery(delivery, raise_on_error=True)
    return delivery


def validate_dormant_runtime_delivery(
    delivery: Any,
    *,
    raise_on_error: bool = False,
) -> tuple[str, ...]:
    """Validate exact bytes, status, owner, and success/fallback boundaries."""

    issues: set[str] = set()
    if type(delivery) is not DormantRuntimeDelivery:
        issues.add("RUNTIME_DELIVERY_REQUIRED")
    else:
        try:
            exact_bytes = delivery.reply_envelope.comment_text.encode(
                "utf-8",
                errors="strict",
            )
        except (AttributeError, UnicodeError):
            exact_bytes = None
        selected = delivery.status == "v3_selected"
        fallback = delivery.status == "v1_fallback"
        if delivery.schema_version != RUNTIME_DELIVERY_SCHEMA:
            issues.add("RUNTIME_DELIVERY_SCHEMA_INVALID")
        if type(delivery.reply_envelope) is not ReplyEnvelope:
            issues.add("RUNTIME_DELIVERY_ENVELOPE_INVALID")
        if exact_bytes != delivery.delivered_utf8_bytes:
            issues.add("RUNTIME_DELIVERY_BYTES_MISMATCH")
        if not (selected or fallback):
            issues.add("RUNTIME_DELIVERY_STATUS_INVALID")
        if (
            delivery.v3_success is not selected
            or delivery.v1_fallback_used is not fallback
            or delivery.v1_fallback_counts_as_v3_success is not False
        ):
            issues.add("RUNTIME_DELIVERY_SUCCESS_BOUNDARY_INVALID")
        if selected:
            envelope_meta = getattr(delivery.reply_envelope, "meta", None)
            if (
                not delivery.delivered_utf8_bytes
                or delivery.delivery_owner != "nls_v3_canonical_renderer"
                or delivery.v3_status != "selected"
                or delivery.v3_failure_code is not None
                or delivery.reply_envelope.fallback_used is not False
                or type(envelope_meta) is not dict
                or envelope_meta.get("observation_status") != "passed"
                or envelope_meta.get("public_observation_status") != "passed"
            ):
                issues.add("RUNTIME_DELIVERY_SELECTED_CONTRACT_INVALID")
        if fallback:
            if (
                delivery.delivery_owner
                != "grounded_sentence_surface_canonical_v1"
                or delivery.v3_status
                not in {"v3_no_valid_candidate", "exception"}
            ):
                issues.add("RUNTIME_DELIVERY_FALLBACK_CONTRACT_INVALID")
            if delivery.v3_status == "exception":
                if type(delivery.v3_failure_code) is not str or re.fullmatch(
                    r"[A-Z][A-Z0-9_]{2,95}",
                    delivery.v3_failure_code,
                ) is None:
                    issues.add("RUNTIME_DELIVERY_FAILURE_CODE_INVALID")
            elif delivery.v3_failure_code is not None:
                issues.add("RUNTIME_DELIVERY_FAILURE_CODE_FORBIDDEN")
    result = tuple(sorted(issues))
    if result and raise_on_error:
        raise DormantRuntimeAdapterError(result[0])
    return result


def runtime_delivery_body_free_summary(
    delivery: DormantRuntimeDelivery,
) -> dict[str, Any]:
    issues = validate_dormant_runtime_delivery(delivery)
    if issues:
        raise DormantRuntimeAdapterError(issues[0])
    return {
        "schema_version": "cocolon.emlis.nls_v3.runtime_delivery_summary.v1",
        "status": delivery.status,
        "v3_status": delivery.v3_status,
        "v3_failure_code": delivery.v3_failure_code,
        "delivery_owner": delivery.delivery_owner,
        "delivered_body_present": bool(delivery.delivered_utf8_bytes),
        "v3_success": delivery.v3_success,
        "v1_fallback_used": delivery.v1_fallback_used,
        "v1_fallback_counts_as_v3_success": (
            delivery.v1_fallback_counts_as_v3_success
        ),
        "body_free": True,
    }


__all__ = [
    "DEFAULT_RUNTIME_STATE",
    "DormantRuntimeAdapterError",
    "DormantRuntimeDelivery",
    "DormantRuntimeExecution",
    "EXECUTION_SCOPES",
    "RUNTIME_ADAPTER_VERSION",
    "RUNTIME_EXECUTION_SCHEMA",
    "RUNTIME_DELIVERY_SCHEMA",
    "RUNTIME_STATE_SCHEMA",
    "RUNTIME_STATES",
    "TESTER_ALLOWLIST_POLICY_SCHEMA",
    "RuntimeOwnerState",
    "TesterExecutionAuthority",
    "RuntimeTransitionAuthority",
    "execute_dormant_v3",
    "issue_tester_execution_authority",
    "map_verified_v3_bytes_to_reply_envelope",
    "resolve_dormant_runtime_delivery",
    "rollback_runtime_owner_state",
    "runtime_execution_body_free_summary",
    "runtime_delivery_body_free_summary",
    "tester_allowlist_policy_sha256",
    "transition_runtime_owner_state",
    "validate_runtime_owner_state",
    "validate_dormant_runtime_execution",
    "validate_dormant_runtime_delivery",
]
