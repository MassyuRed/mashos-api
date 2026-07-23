# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step 10 dormant runtime, batch runner, and evidence boundary tests.

These tests intentionally stop at Step 10.  They prove that the future v3
runtime can be exercised offline while production ownership remains v1; they
do not claim the formal batch-001 initial run, review, lock, or acceptance that
belongs to Step 11.
"""

import asyncio
from copy import deepcopy
from dataclasses import replace
from functools import lru_cache
import hashlib
import inspect
import json
from pathlib import Path
import sys
import tempfile
from types import ModuleType
from typing import Any, Callable

import emlis_ai_dormant_runtime_adapter_v3 as runtime_module
import emlis_ai_reply_service as reply_service_module
import emlis_ai_step10_evidence_v3 as evidence_module
import emlis_ai_step10_dependency_manifest_v3 as step10_manifest_module
import emlis_ai_step9_dependency_manifest_v3 as step9_manifest_module
from emlis_ai_dormant_runtime_adapter_v3 import (
    DEFAULT_RUNTIME_STATE,
    DormantRuntimeAdapterError,
    DormantRuntimeDelivery,
    DormantRuntimeExecution,
    RuntimeOwnerState,
    RuntimeTransitionAuthority,
    TesterExecutionAuthority,
    issue_tester_execution_authority,
    map_verified_v3_bytes_to_reply_envelope,
    resolve_dormant_runtime_delivery,
    rollback_runtime_owner_state,
    transition_runtime_owner_state,
    tester_allowlist_policy_sha256 as _tester_allowlist_policy_sha256,
    runtime_delivery_body_free_summary,
    validate_dormant_runtime_delivery,
    validate_dormant_runtime_execution,
    validate_runtime_owner_state,
)
from emlis_ai_nls_v3_artifact_contract import artifact_sha256
from emlis_ai_reply_service import render_emlis_ai_reply
from emlis_ai_public_feedback_meta import (
    build_public_emlis_input_feedback_meta,
    should_include_public_input_feedback,
)
from emlis_ai_step10_dependency_manifest_v3 import (
    FROZEN_STEP10_CANDIDATE_VERSION_ID,
    FROZEN_STEP10_DEPENDENCY_CLOSURE_SHA256,
    FROZEN_STEP10_MANIFEST_SOURCE_NORMALIZED_SHA256,
    FROZEN_STEP10_MANIFEST_SHA256,
    FROZEN_V1_DEFAULT_OUTPUT_SET_SHA256,
    STEP10_DEPENDENCY_MANIFEST,
    current_step10_source_hashes,
    fresh_step10_source_closure_sha256,
    normalized_step10_manifest_source_sha256,
    step10_source_file_sha256,
    validate_step10_dependency_manifest,
)
from emlis_ai_step10_app_reachable_contract_v3 import (
    FROZEN_APP_REACHABLE_INPUT_POLICY_SHA256,
    project_app_reachable_input,
    validate_app_reachable_input as validate_runtime_app_reachable_input,
    validate_app_reachable_input_policy,
)
from emlis_ai_step10_evidence_v3 import (
    COMMITMENT_POLICY_SHA256,
    HARD_GATE_FAILURE_CODES,
    LOCAL_REVIEW_AXES,
    LOCAL_REVIEW_FAILURE_CODES,
    LOCAL_REVIEW_PASS_CODES,
    STEP10_RECEIPT_SCHEMA,
    Step10EvidenceError,
    assert_body_free,
    build_batch_evidence,
    build_case_evidence,
    build_change_ledger_row,
    build_cumulative_run_manifest,
    build_output_diff,
    build_local_product_review,
    commitment_key_id,
    validate_batch_run_summary,
    validate_historical_batch_run_summary,
    validate_step10_case_evidence_receipt,
    verify_batch_evidence,
)
from emlis_ai_step9_dependency_manifest_v3 import (
    FROZEN_STEP9_DEPENDENCY_MANIFEST_SHA256,
    STEP9_DEPENDENCY_MANIFEST,
    STEP9_DEPENDENCY_MANIFEST_SHA256,
    validate_step9_dependency_manifest,
)
from emlis_nls_v3_s2_sample_registry import (
    VALIDATOR_POLICY_SHA256 as STEP2_VALIDATOR_POLICY_SHA256,
    rn_contract_binding_issues,
    validate_app_reachable_input as validate_step2_app_reachable_input,
)
from helpers.emlis_nls_v3_s0_s1_baseline import load_baseline_cases


_HERE = Path(__file__).resolve().parent
_AI_ROOT = _HERE.parent
_REPO_ROOT = _AI_ROOT.parent
_INFERENCE_ROOT = _AI_ROOT / "services" / "ai_inference"
_BATCH_PATH = (
    _HERE / "fixtures" / "emlis_nls_v3" / "generated" / "batch_001.jsonl"
)
_STEP0_BOUNDARY_PATH = _HERE / "fixtures" / "emlis_nls_v3_s0_boundary_20260714.json"
_CASE_ID = "nls3s_b001_0001"
_CANDIDATE_VERSION = "nls_v3_rc_0010"
_RUN_ID = "nls3run_0123456789abcdef"
_COMMITMENT_KEY = bytes(range(32))
_RUNNER_SHA256_PATH = "ai/tools/emlis_nls_v3_batch_run.py"


def _raises_code(
    expected_type: type[BaseException],
    expected_code: str,
    call: Callable[[], Any],
) -> None:
    try:
        call()
    except expected_type as exc:
        assert getattr(exc, "code", str(exc)) == expected_code
    else:
        raise AssertionError(f"{expected_code} was not raised")


def _contains_exact_string(value: Any, target: str) -> bool:
    if type(value) is str:
        return value == target
    if type(value) is dict:
        return any(
            _contains_exact_string(key, target)
            or _contains_exact_string(child, target)
            for key, child in value.items()
        )
    if type(value) in {list, tuple}:
        return any(_contains_exact_string(child, target) for child in value)
    return False


@lru_cache(maxsize=1)
def _samples() -> tuple[dict[str, Any], ...]:
    return tuple(
        json.loads(line)
        for line in _BATCH_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )


def _sample(case_id: str = _CASE_ID) -> dict[str, Any]:
    return next(row for row in _samples() if row["case_id"] == case_id)


@lru_cache(maxsize=1)
def _v1_body_utf8() -> bytes:
    reply = asyncio.run(
        render_emlis_ai_reply(
            user_id="nls-v3-step10-v1-pair",
            subscription_tier="free",
            current_input=dict(_sample()["input"]),
        )
    )
    assert reply.comment_text
    return reply.comment_text.encode("utf-8")


@lru_cache(maxsize=1)
def _v1_default_output_set_sha256() -> str:
    async def capture() -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for case in load_baseline_cases():
            reply = await render_emlis_ai_reply(
                user_id=f"nls-v3-step10-v1-diff-{case.cohort}-{case.case_id}",
                subscription_tier="free",
                current_input=dict(case.current_input),
            )
            rows.append(
                {
                    "cohort": case.cohort,
                    "case_id": case.case_id,
                    "comment_text": reply.comment_text,
                    "observation_status": reply.meta.get("observation_status"),
                    "generation_path": reply.meta.get("generation_path"),
                    "fallback_used": reply.fallback_used,
                    "used_memory_layers": list(reply.used_memory_layers),
                }
            )
        return rows

    return artifact_sha256(asyncio.run(capture()))


@lru_cache(maxsize=1)
def _execution() -> DormantRuntimeExecution:
    # Exercise the real one-way reply-service bridge, not an alternate test
    # composition of the Step 4--9 modules.
    result = reply_service_module._render_emlis_ai_reply_v3_dormant(
        current_input=dict(_sample()["input"]),
        candidate_version_id=_CANDIDATE_VERSION,
    )
    assert type(result) is DormantRuntimeExecution
    return result


@lru_cache(maxsize=1)
def _case_bundle():
    return build_case_evidence(
        _execution(),
        sample_case=_sample(),
        v1_body_utf8=_v1_body_utf8(),
        commitment_key=_COMMITMENT_KEY,
        run_id=_RUN_ID,
        runner_sha256=step10_source_file_sha256(_RUNNER_SHA256_PATH),
    )


def _evidence_pair(*, expected_case_count: int = 1):
    return build_batch_evidence(
        [_case_bundle()],
        batch_id="nls3_batch_001",
        run_id=_RUN_ID,
        candidate_version_id=_CANDIDATE_VERSION,
        batch_manifest_sha256="a" * 64,
        expected_case_count=expected_case_count,
        commitment_key=_COMMITMENT_KEY,
    )


def _retag_batch_run(summary: dict[str, Any], run_id: str) -> dict[str, Any]:
    retagged = deepcopy(summary)
    retagged["run_id"] = run_id
    for row in retagged["case_rows"]:
        if type(row.get("receipt")) is dict:
            row["receipt"]["run_id"] = run_id
    return retagged


def test_s10_public_contract_is_unchanged_and_default_owner_is_disabled_v1() -> None:
    signature = inspect.signature(render_emlis_ai_reply)
    assert list(signature.parameters) == [
        "user_id",
        "subscription_tier",
        "current_input",
        "display_name",
        "timezone_name",
        "composer_client",
    ]
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )
    assert reply_service_module.__all__ == ["render_emlis_ai_reply"]
    assert reply_service_module._NLS_V3_STEP10_PUBLIC_ROUTING_STATE == "disabled"
    assert (
        reply_service_module._step10_dormant_v3_public_hook(
            user_id="step10-default-owner-check",
            current_input=dict(_sample()["input"]),
        )
        is None
    )

    assert DEFAULT_RUNTIME_STATE.state == "disabled"
    assert DEFAULT_RUNTIME_STATE.public_owner == "grounded_sentence_surface_canonical_v1"
    assert DEFAULT_RUNTIME_STATE.rollback_owner == "grounded_sentence_surface_canonical_v1"
    assert DEFAULT_RUNTIME_STATE.v3_general_account_visible is False
    assert validate_runtime_owner_state(DEFAULT_RUNTIME_STATE) == ()
    boundary = STEP10_DEPENDENCY_MANIFEST["runtime_boundary"]
    assert FROZEN_STEP10_CANDIDATE_VERSION_ID == _CANDIDATE_VERSION
    assert boundary["frozen_candidate_version_id"] == _CANDIDATE_VERSION
    assert boundary["default_public_routing_state"] == "disabled"
    assert boundary["production_owner"] == "grounded_sentence_surface_canonical_v1"
    assert boundary["owner_activation_permitted_in_step10"] is False
    assert boundary["v3_general_account_visible"] is False
    assert _v1_default_output_set_sha256() == FROZEN_V1_DEFAULT_OUTPUT_SET_SHA256
    assert STEP10_DEPENDENCY_MANIFEST["baseline_boundary"] == {
        "known_v1_case_count": 28,
        "v1_default_output_set_sha256": FROZEN_V1_DEFAULT_OUTPUT_SET_SHA256,
        "default_production_output_diff_count": 0,
    }

    # Even a local default-path call remains the existing v1 generation path.
    public_reply = asyncio.run(
        render_emlis_ai_reply(
            user_id="step10-default-owner-check",
            subscription_tier="free",
            current_input=dict(_sample()["input"]),
        )
    )
    assert public_reply.comment_text
    assert public_reply.meta["generation_path"] != "grounded_natural_language_surface_v3"
    assert "nls_v3_runtime" not in public_reply.meta


def test_s10_state_machine_is_fail_closed_and_tester_authority_is_opaque() -> None:
    base_authority = RuntimeTransitionAuthority(
        candidate_version_id=_CANDIDATE_VERSION,
        source_dependency_closure_sha256=FROZEN_STEP10_DEPENDENCY_CLOSURE_SHA256,
    )
    _raises_code(
        DormantRuntimeAdapterError,
        "STEP10_OWNER_ACTIVATION_FORBIDDEN",
        lambda: transition_runtime_owner_state(
            DEFAULT_RUNTIME_STATE,
            "owner",
            authority=base_authority,
        ),
    )
    offline = transition_runtime_owner_state(
        DEFAULT_RUNTIME_STATE,
        "offline",
        authority=base_authority,
    )
    assert offline.state == "offline"
    assert offline.public_owner == "grounded_sentence_surface_canonical_v1"

    _raises_code(
        DormantRuntimeAdapterError,
        "RUNTIME_TRANSITION_FORBIDDEN",
        lambda: transition_runtime_owner_state(
            offline,
            "tester_only_preview",
            authority=RuntimeTransitionAuthority(
                candidate_version_id=_CANDIDATE_VERSION,
                source_dependency_closure_sha256=FROZEN_STEP10_DEPENDENCY_CLOSURE_SHA256,
                tester_allowlist_policy_sha256="b" * 64,
            ),
        ),
    )
    _raises_code(
        DormantRuntimeAdapterError,
        "RUNTIME_TRANSITION_AUTHORITY_INVALID",
        lambda: transition_runtime_owner_state(
            offline,
            "shadow",
            authority=RuntimeTransitionAuthority(
                candidate_version_id="nls_v3_rc_0011",
                source_dependency_closure_sha256=FROZEN_STEP10_DEPENDENCY_CLOSURE_SHA256,
                saturation_gate_sha256="d" * 64,
            ),
        ),
    )
    _raises_code(
        DormantRuntimeAdapterError,
        "SHADOW_SATURATION_AUTHORITY_REQUIRED",
        lambda: transition_runtime_owner_state(
            offline,
            "shadow",
            authority=RuntimeTransitionAuthority(
                candidate_version_id=_CANDIDATE_VERSION,
                source_dependency_closure_sha256=(
                    FROZEN_STEP10_DEPENDENCY_CLOSURE_SHA256
                ),
                saturation_gate_sha256="0" * 64,
            ),
        ),
    )

    shadow = transition_runtime_owner_state(
        offline,
        "shadow",
        authority=RuntimeTransitionAuthority(
            candidate_version_id=_CANDIDATE_VERSION,
            source_dependency_closure_sha256=FROZEN_STEP10_DEPENDENCY_CLOSURE_SHA256,
            saturation_gate_sha256="d" * 64,
        ),
    )
    account_commitment = "c" * 64
    allowlist_policy = _tester_allowlist_policy_sha256(
        allowed_account_commitments=(account_commitment,),
        candidate_version_id=_CANDIDATE_VERSION,
    )
    tester_state = transition_runtime_owner_state(
        shadow,
        "tester_only_preview",
        authority=RuntimeTransitionAuthority(
            candidate_version_id=_CANDIDATE_VERSION,
            source_dependency_closure_sha256=FROZEN_STEP10_DEPENDENCY_CLOSURE_SHA256,
            tester_allowlist_policy_sha256=allowlist_policy,
        ),
    )
    forged = TesterExecutionAuthority(
        account_identity_commitment=account_commitment,
        allowlist_policy_sha256=allowlist_policy,
        candidate_version_id=_CANDIDATE_VERSION,
        source_dependency_closure_sha256=FROZEN_STEP10_DEPENDENCY_CLOSURE_SHA256,
    )
    assert runtime_module._execution_allowed(
        tester_state,
        scope="tester_only_preview",
        tester_authority=forged,
        account_identity_commitment=account_commitment,
    ) is False
    assert runtime_module._execution_allowed(
        tester_state,
        scope="tester_only_preview",
        tester_authority=True,
        account_identity_commitment=account_commitment,
    ) is False
    _raises_code(
        DormantRuntimeAdapterError,
        "RUNTIME_EXECUTION_NOT_AUTHORIZED",
        lambda: runtime_module.execute_dormant_v3(
            dict(_sample()["input"]),
            candidate_version_id=_CANDIDATE_VERSION,
            runtime_state=tester_state,
            execution_scope="tester_only_preview",
            tester_authority=forged,
            account_identity_commitment=account_commitment,
        ),
    )
    _raises_code(
        DormantRuntimeAdapterError,
        "TESTER_ALLOWLIST_POLICY_MISMATCH",
        lambda: issue_tester_execution_authority(
            account_identity_commitment=account_commitment,
            allowed_account_commitments=(account_commitment,),
            allowlist_policy_sha256="b" * 64,
            candidate_version_id=_CANDIDATE_VERSION,
        ),
    )
    issued = issue_tester_execution_authority(
        account_identity_commitment=account_commitment,
        allowed_account_commitments=(account_commitment,),
        allowlist_policy_sha256=allowlist_policy,
        candidate_version_id=_CANDIDATE_VERSION,
    )
    assert runtime_module._execution_allowed(
        tester_state,
        scope="tester_only_preview",
        tester_authority=issued,
        account_identity_commitment=account_commitment,
    ) is True
    assert runtime_module._execution_allowed(
        tester_state,
        scope="tester_only_preview",
        tester_authority=issued,
        account_identity_commitment="e" * 64,
    ) is False

    visible_mutation = replace(offline, v3_general_account_visible=True)
    assert "STEP10_GENERAL_ACCOUNT_VISIBILITY_FORBIDDEN" in (
        validate_runtime_owner_state(visible_mutation)
    )
    shadow_execution = replace(
        _execution(),
        runtime_state=shadow,
        execution_scope="shadow",
    )
    _raises_code(
        DormantRuntimeAdapterError,
        "SHADOW_BODY_VISIBILITY_FORBIDDEN",
        lambda: map_verified_v3_bytes_to_reply_envelope(shadow_execution),
    )

    stopped = rollback_runtime_owner_state(
        offline,
        reason_code="LOCAL_GATE_FAILED",
    )
    assert stopped.state == "stopped"
    assert stopped.candidate_version_id == _CANDIDATE_VERSION
    _raises_code(
        DormantRuntimeAdapterError,
        "STOPPED_SAME_RC_REPROMOTION_FORBIDDEN",
        lambda: transition_runtime_owner_state(
            stopped,
            "offline",
            authority=RuntimeTransitionAuthority(
                candidate_version_id=_CANDIDATE_VERSION,
                source_dependency_closure_sha256=FROZEN_STEP10_DEPENDENCY_CLOSURE_SHA256,
                new_release_candidate_after_stop=True,
            ),
        ),
    )
    historical_stopped = replace(
        stopped,
        candidate_version_id="nls_v3_rc_0009",
    )
    assert validate_runtime_owner_state(historical_stopped) == ()
    _raises_code(
        DormantRuntimeAdapterError,
        "STOPPED_RC_REUSE_FORBIDDEN",
        lambda: transition_runtime_owner_state(
            historical_stopped,
            "offline",
            authority=RuntimeTransitionAuthority(
                candidate_version_id=_CANDIDATE_VERSION,
                source_dependency_closure_sha256=FROZEN_STEP10_DEPENDENCY_CLOSURE_SHA256,
            ),
        ),
    )
    replacement = transition_runtime_owner_state(
        historical_stopped,
        "offline",
        authority=RuntimeTransitionAuthority(
            candidate_version_id=_CANDIDATE_VERSION,
            source_dependency_closure_sha256=FROZEN_STEP10_DEPENDENCY_CLOSURE_SHA256,
            new_release_candidate_after_stop=True,
        ),
    )
    assert replacement.state == "offline"
    assert replacement.candidate_version_id == _CANDIDATE_VERSION


def test_s10_reply_bridge_preserves_selected_canonical_utf8_bytes_exactly() -> None:
    execution = _execution()
    assert execution.execution_scope == "offline_batch"
    assert execution.runtime_state.state == "disabled"
    assert execution.status == "selected"
    assert execution.v3_success is True
    assert execution.v1_fallback_used is False
    assert execution.v1_fallback_counts_as_v3_success is False
    assert execution.final_utf8_bytes
    assert (
        execution.final_utf8_bytes
        == execution.selected_candidate.rendered_surface.utf8_bytes
    )

    envelope = map_verified_v3_bytes_to_reply_envelope(execution)
    assert envelope.comment_text.encode("utf-8") == execution.final_utf8_bytes
    assert envelope.comment_text == envelope.comment_text.strip()
    assert envelope.meta["nls_v3_runtime"]["status"] == "selected"
    assert envelope.meta["nls_v3_runtime"]["public_owner"] == (
        "grounded_sentence_surface_canonical_v1"
    )
    assert envelope.meta["public_contract_changed"] is False
    assert envelope.meta["api_route_changed"] is False
    assert envelope.meta["db_physical_name_changed"] is False
    assert envelope.meta["rn_visible_contract_changed"] is False
    public_runtime = envelope.meta["nls_v3_runtime"]
    assert "selected_candidate_id" not in public_runtime
    assert "source_dependency_closure_sha256" not in public_runtime
    public_meta = build_public_emlis_input_feedback_meta(
        envelope.meta,
        comment_text_present=True,
        subscription_tier="free",
    )
    assert public_meta["observation_status"] == "passed"
    assert should_include_public_input_feedback(envelope.comment_text, public_meta)
    assert envelope.comment_text.strip().encode("utf-8") == execution.final_utf8_bytes
    public_serialized = json.dumps(public_meta, ensure_ascii=False, sort_keys=True)
    assert envelope.comment_text not in public_serialized
    assert "nls_v3_runtime" not in public_meta

    forged_bytes = "検証済みでない本文です。".encode("utf-8")
    forged_render = replace(
        execution.selected_candidate.rendered_surface,
        utf8_bytes=forged_bytes,
        sha256=hashlib.sha256(forged_bytes).hexdigest(),
    )
    forged_candidate = replace(
        execution.selected_candidate,
        rendered_surface=forged_render,
    )
    forged_selection = replace(
        execution.recovery_result.selection,
        selected_candidate=forged_candidate,
    )
    forged_recovery = replace(
        execution.recovery_result,
        selection=forged_selection,
    )
    forged_execution = replace(
        execution,
        recovery_result=forged_recovery,
        final_utf8_bytes=forged_bytes,
    )
    forged_issues = validate_dormant_runtime_execution(forged_execution)
    assert "RUNTIME_SELECTED_CANDIDATE_ID_MISMATCH" in forged_issues
    assert "RUNTIME_SELECTED_TEXT_HASH_MISMATCH" in forged_issues
    _raises_code(
        DormantRuntimeAdapterError,
        "RUNTIME_EXECUTION_SOURCE_LINEAGE_MISMATCH",
        lambda: map_verified_v3_bytes_to_reply_envelope(forged_execution),
    )


def test_s10_runtime_execution_recomputes_the_full_parent_chain_and_frozen_rc() -> None:
    execution = _execution()
    assert validate_dormant_runtime_execution(execution) == ()

    content_forge = replace(execution, content_plan={"evil": True})
    assert "RUNTIME_EXECUTION_SOURCE_LINEAGE_MISMATCH" in (
        validate_dormant_runtime_execution(content_forge)
    )

    source_swap = replace(
        execution,
        normalized_input=dict(_sample("nls3s_b001_0002")["input"]),
    )
    assert any(
        code.startswith("RUNTIME_EXECUTION_SOURCE_LINEAGE_")
        for code in validate_dormant_runtime_execution(source_swap)
    )

    rc_retag = replace(execution, candidate_version_id="nls_v3_rc_9999")
    assert "RUNTIME_EXECUTION_CANDIDATE_INVALID" in (
        validate_dormant_runtime_execution(rc_retag)
    )
    _raises_code(
        DormantRuntimeAdapterError,
        "RUNTIME_CANDIDATE_VERSION_INVALID",
        lambda: runtime_module.execute_dormant_v3(
            dict(_sample()["input"]),
            candidate_version_id="nls_v3_rc_9999",
        ),
    )


def test_s10_delivery_keeps_v3_success_and_v1_fallback_boundaries_separate() -> None:
    selected = resolve_dormant_runtime_delivery(_execution())
    selected_summary = runtime_delivery_body_free_summary(selected)
    assert selected_summary["status"] == "v3_selected"
    assert selected_summary["v3_success"] is True
    assert selected_summary["v1_fallback_used"] is False
    assert selected.delivered_utf8_bytes == _execution().final_utf8_bytes

    v1_envelope = asyncio.run(
        render_emlis_ai_reply(
            user_id="nls-v3-step10-fallback",
            subscription_tier="free",
            current_input=dict(_sample()["input"]),
        )
    )
    fallback = resolve_dormant_runtime_delivery(
        None,
        v1_fallback=v1_envelope,
        v3_failure_code="STEP10_CASE_EXECUTION_REJECTED",
    )
    fallback_summary = runtime_delivery_body_free_summary(fallback)
    assert fallback_summary["status"] == "v1_fallback"
    assert fallback_summary["v3_status"] == "exception"
    assert fallback_summary["v3_success"] is False
    assert fallback_summary["v1_fallback_used"] is True
    assert fallback_summary["v1_fallback_counts_as_v3_success"] is False
    assert fallback.delivered_utf8_bytes == v1_envelope.comment_text.encode("utf-8")

    owner_forge = replace(selected, schema_version="evil", delivery_owner="evil")
    owner_issues = validate_dormant_runtime_delivery(owner_forge)
    assert "RUNTIME_DELIVERY_SCHEMA_INVALID" in owner_issues
    assert "RUNTIME_DELIVERY_SELECTED_CONTRACT_INVALID" in owner_issues
    empty_selected = replace(selected, delivered_utf8_bytes=b"")
    assert validate_dormant_runtime_delivery(empty_selected)
    envelope_flag_forge = replace(
        selected,
        reply_envelope=replace(selected.reply_envelope, fallback_used=True),
    )
    assert "RUNTIME_DELIVERY_SELECTED_CONTRACT_INVALID" in (
        validate_dormant_runtime_delivery(envelope_flag_forge)
    )


def test_s10_batch_runner_aborts_infrastructure_and_lineage_failures() -> None:
    tools_path = str(_AI_ROOT / "tools")
    if tools_path not in sys.path:
        sys.path.insert(0, tools_path)
    import emlis_nls_v3_batch_run as runner

    samples = [_sample(), _sample("nls3s_b001_0002")]
    manifest = {"batch_id": "nls3_batch_001", "case_count": 2}
    original_v1 = runner._v1_body
    original_v3 = runner._render_emlis_ai_reply_v3_dormant
    original_evidence = runner.build_case_evidence

    async def v1_ok(_current_input: dict[str, Any], _case_id: str) -> bytes:
        return b"v1"

    calls = 0

    def infrastructure_failure(**_kwargs: Any):
        nonlocal calls
        calls += 1
        raise OSError("simulated infrastructure failure")

    try:
        runner._v1_body = v1_ok
        runner._render_emlis_ai_reply_v3_dormant = infrastructure_failure
        try:
            runner.run_batch(
                samples,
                manifest,
                candidate_version_id=_CANDIDATE_VERSION,
                run_id="nls3run_5123456789abcdef",
                commitment_key=_COMMITMENT_KEY,
            )
        except OSError:
            pass
        else:
            raise AssertionError("infrastructure failure was downgraded")
        assert calls == 1

        runner._render_emlis_ai_reply_v3_dormant = lambda **_kwargs: _execution()

        def lineage_failure(*_args: Any, **_kwargs: Any):
            raise Step10EvidenceError(
                "RUNTIME_EXECUTION_SOURCE_LINEAGE_MISMATCH"
            )

        runner.build_case_evidence = lineage_failure
        _raises_code(
            Step10EvidenceError,
            "RUNTIME_EXECUTION_SOURCE_LINEAGE_MISMATCH",
            lambda: runner.run_batch(
                samples,
                manifest,
                candidate_version_id=_CANDIDATE_VERSION,
                run_id="nls3run_6123456789abcdef",
                commitment_key=_COMMITMENT_KEY,
            ),
        )

        async def v1_infrastructure_failure(
            _current_input: dict[str, Any],
            _case_id: str,
        ) -> bytes:
            raise OSError("simulated v1 infrastructure failure")

        runner._v1_body = v1_infrastructure_failure
        runner.build_case_evidence = original_evidence
        try:
            runner.run_batch(
                samples,
                manifest,
                candidate_version_id=_CANDIDATE_VERSION,
                run_id="nls3run_7123456789abcdef",
                commitment_key=_COMMITMENT_KEY,
            )
        except OSError:
            pass
        else:
            raise AssertionError("v1 infrastructure failure was downgraded")
    finally:
        runner._v1_body = original_v1
        runner._render_emlis_ai_reply_v3_dormant = original_v3
        runner.build_case_evidence = original_evidence


def test_s10_private_io_rejects_ancestor_symlinks() -> None:
    tools_path = str(_AI_ROOT / "tools")
    if tools_path not in sys.path:
        sys.path.insert(0, tools_path)
    import emlis_nls_v3_batch_run as runner

    with tempfile.TemporaryDirectory(prefix="emlis-nls-v3-step10-") as root:
        root_path = Path(root)
        real_parent = root_path / "real"
        real_parent.mkdir()
        key_path = real_parent / "commitment.key"
        key_path.write_bytes(_COMMITMENT_KEY)
        key_path.chmod(0o600)
        assert runner._read_key(key_path) == _COMMITMENT_KEY

        linked_parent = root_path / "linked"
        linked_parent.symlink_to(real_parent, target_is_directory=True)
        _raises_code(
            ValueError,
            "commitment_key_file_open_rejected",
            lambda: runner._read_key(linked_parent / "commitment.key"),
        )
        try:
            runner._write_json(
                linked_parent / "private.json",
                {"body": "private"},
                private=True,
            )
        except OSError:
            pass
        else:
            raise AssertionError("ancestor symlink was followed for private output")
        assert not (real_parent / "private.json").exists()

        output = root_path / "fresh" / "private.json"
        runner._write_json(output, {"status": "ok"}, private=True)
        assert json.loads(output.read_text(encoding="utf-8")) == {
            "status": "ok"
        }
        assert output.stat().st_mode & 0o777 == 0o600


def test_s10_runtime_app_reachable_adapter_matches_frozen_step2_policy() -> None:
    assert validate_app_reachable_input_policy() == ()
    assert FROZEN_APP_REACHABLE_INPUT_POLICY_SHA256 == (
        STEP2_VALIDATOR_POLICY_SHA256
    )
    valid = deepcopy(_sample()["input"])
    cases = [
        valid,
        {**valid, "thought_text": "\u0085", "action_text": "\u001c"},
        {**valid, "thought_text": "\u3000", "action_text": "\ufeff"},
        {**valid, "emotions": [valid["emotions"][0]] * 2},
        {
            **valid,
            "emotions": [{"type": "自己理解", "strength": "strong"}],
        },
        {**valid, "categories": [valid["categories"][0]] * 2},
        {**valid, "unexpected": True},
    ]
    for current_input in cases:
        assert validate_runtime_app_reachable_input(current_input) == (
            validate_step2_app_reachable_input(current_input)
        )
    assert project_app_reachable_input(valid) == valid


def test_s10_private_body_full_and_body_free_hmac_evidence_are_separate() -> None:
    private_packet, summary = _evidence_pair()
    assert validate_batch_run_summary(summary) == ()
    assert verify_batch_evidence(private_packet, summary) == ()
    assert_body_free(summary)
    assert summary["body_free"] is True
    assert private_packet["body_full"] is True
    assert private_packet["storage_scope"] == "private_local_only"
    assert private_packet["hmac_key_hex"] == _COMMITMENT_KEY.hex()
    assert private_packet["commitment_key_id"] == commitment_key_id(
        _COMMITMENT_KEY
    ) == summary["commitment_key_id"]
    assert "hmac_key_hex" not in summary

    execution = _execution()
    body_text = execution.final_utf8_bytes.decode("utf-8")
    assert not _contains_exact_string(summary, body_text)
    v1_body = _v1_body_utf8().decode("utf-8")
    assert not _contains_exact_string(summary, v1_body)
    assert private_packet["cases"][0]["v3_body"] == body_text
    assert private_packet["cases"][0]["v1_body"] == v1_body
    assert summary["aggregate"]["latency_sample_count"] == 1
    assert summary["aggregate"]["latency_total_ns"] > 0
    assert summary["aggregate"]["required_obligation_count"] > 0
    assert summary["aggregate"]["bound_obligation_count"] >= summary[
        "aggregate"
    ]["required_obligation_count"]
    surface_profile = summary["case_rows"][0]["surface_profile"]
    assert surface_profile["opening_family"]
    assert surface_profile["ending_family"]
    assert surface_profile["near_duplicate_skeleton_commitment"]
    distributions = summary["aggregate"]["surface_distributions"]
    assert sum(distributions["opening_family_counts"].values()) == 1
    assert sum(distributions["ending_family_counts"].values()) == 1
    receipt = summary["case_rows"][0]["receipt"]
    assert receipt["commitment_policy"]["scheme"] == "hmac_sha256_v1"
    assert receipt["commitment_policy"]["key_or_nonce_stored_in_receipt"] is False
    assert receipt["selected_candidate_body_commitment"] != hashlib.sha256(
        execution.final_utf8_bytes
    ).hexdigest()
    assert "selected_candidate_id" not in receipt["selector_decision"]
    assert receipt["selector_decision"][
        "selected_candidate_identity_commitment"
    ]

    tampered_private = deepcopy(private_packet)
    tampered_private["cases"][0]["v3_body"] += "改変"
    assert "PRIVATE_PACKET_COMMITMENT_MISMATCH" in verify_batch_evidence(
        tampered_private,
        summary,
    )
    tampered_summary = deepcopy(summary)
    tampered_summary["aggregate"]["selected_count"] = 0
    summary_issues = verify_batch_evidence(private_packet, tampered_summary)
    assert "BATCH_RUN_MANUAL_AGGREGATE_REJECTED" in summary_issues
    assert "PRIVATE_PACKET_SUMMARY_HASH_MISMATCH" in summary_issues
    tampered_profile = deepcopy(summary)
    tampered_profile["case_rows"][0]["surface_profile"][
        "near_duplicate_skeleton_commitment"
    ] = "e" * 64
    profile_issues = verify_batch_evidence(private_packet, tampered_profile)
    assert "PRIVATE_PACKET_SURFACE_PROFILE_MISMATCH" in profile_issues
    tampered_selector = deepcopy(summary)
    tampered_selector["case_rows"][0]["receipt"]["selector_decision"][
        "selected_candidate_identity_commitment"
    ] = "e" * 64
    assert "PRIVATE_PACKET_SELECTOR_COMMITMENT_MISMATCH" in (
        verify_batch_evidence(private_packet, tampered_selector)
    )
    leaked_summary = deepcopy(summary)
    leaked_summary["raw_input"] = dict(_sample()["input"])
    leak_issues = verify_batch_evidence(private_packet, leaked_summary)
    assert "BATCH_RUN_KEYSET_INVALID" in leak_issues
    _raises_code(
        Step10EvidenceError,
        "BODY_FREE_ARTIFACT_CONTAINS_PRIVATE_BODY",
        lambda: assert_body_free(leaked_summary),
    )


def test_s10_receipt_v3_schema_and_step11_evidence_builders_are_closed() -> None:
    bundle = _case_bundle()
    receipt = bundle.receipt
    assert validate_step10_case_evidence_receipt(
        receipt,
        authority=bundle.authority,
    ) == ()
    original_policy = dict(evidence_module.COMMITMENT_POLICY)
    original_policy_hash = evidence_module.COMMITMENT_POLICY_SHA256
    historical_probe_commitment = evidence_module.hmac_commit_bytes(
        _COMMITMENT_KEY,
        "historical_policy_probe",
        b"frozen-v3-packet",
    )
    try:
        evidence_module.COMMITMENT_POLICY["domain_prefix"] = (
            "cocolon.emlis.nls_v3.future"
        )
        evidence_module.COMMITMENT_POLICY_SHA256 = artifact_sha256(
            evidence_module.COMMITMENT_POLICY
        )
        assert evidence_module.validate_historical_step10_case_evidence_receipt(
            receipt,
            authority=bundle.authority,
        ) == ()
        assert "STEP10_RECEIPT_V3_CATALOG_VERSION_BUMP_REQUIRED" in (
            validate_step10_case_evidence_receipt(
                receipt,
                authority=bundle.authority,
            )
        )
        assert evidence_module.hmac_commit_bytes(
            _COMMITMENT_KEY,
            "historical_policy_probe",
            b"frozen-v3-packet",
        ) == historical_probe_commitment
    finally:
        evidence_module.COMMITMENT_POLICY.clear()
        evidence_module.COMMITMENT_POLICY.update(original_policy)
        evidence_module.COMMITMENT_POLICY_SHA256 = original_policy_hash
    schema_path = (
        _HERE / "schemas" / "emlis_nls_v3_case_evidence_receipt_v3.schema.json"
    )
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    assert schema["$id"] == STEP10_RECEIPT_SCHEMA
    assert set(schema["required"]) == set(receipt)
    assert schema["properties"]["commitment_policy"]["properties"][
        "policy_sha256"
    ]["const"] == COMMITMENT_POLICY_SHA256
    assert set(schema["$defs"]["hardGateCode"]["enum"]) == (
        set(HARD_GATE_FAILURE_CODES) | {"NO_VALID_CANDIDATE"}
    )
    assert set(schema["$defs"]["localReviewPassCode"]["enum"]) == set(
        LOCAL_REVIEW_PASS_CODES
    )
    assert set(schema["$defs"]["localReviewFailureCode"]["enum"]) == set(
        LOCAL_REVIEW_FAILURE_CODES
    )
    assert len(schema["allOf"]) == 3
    assert len(schema["properties"]["hard_gate"]["allOf"]) == 2
    review_conditions = schema["properties"]["local_product_review"]["allOf"]
    assert len(review_conditions) == 3
    assert review_conditions[1]["then"]["properties"]["reason_codes"][
        "items"
    ]["$ref"] == "#/$defs/localReviewPassCode"
    assert review_conditions[2]["then"]["properties"]["reason_codes"][
        "items"
    ]["$ref"] == "#/$defs/localReviewFailureCode"
    assert len(schema["properties"]["previous_output"]["oneOf"]) == 2

    salted_scheme = deepcopy(receipt)
    salted_scheme["commitment_policy"]["scheme"] = "salted_sha256_v1"
    assert "STEP10_RECEIPT_COMMITMENT_POLICY_INVALID" in (
        validate_step10_case_evidence_receipt(
            salted_scheme,
            authority=bundle.authority,
        )
    )
    zero_identity = deepcopy(receipt)
    zero_identity["case_identity_commitment"] = "0" * 64
    assert "STEP10_RECEIPT_CASE_IDENTITY_INVALID" in (
        validate_step10_case_evidence_receipt(
            zero_identity,
            authority=bundle.authority,
        )
    )
    unknown_gate_code = deepcopy(receipt)
    unknown_gate_code["hard_gate"] = {
        "status": "failed",
        "failed_codes": ["UNREGISTERED_GATE_CODE"],
    }
    unknown_gate_code["selector_decision"] = {
        "status": "no_valid_candidate",
        "selected_candidate_identity_commitment": None,
        "selection_attributes_commitment": receipt["selector_decision"][
            "selection_attributes_commitment"
        ],
    }
    assert "STEP10_RECEIPT_HARD_GATE_CODE_INVALID" in (
        validate_step10_case_evidence_receipt(
            unknown_gate_code,
            authority=bundle.authority,
        )
    )

    empty_v1 = build_case_evidence(
        _execution(),
        sample_case=_sample(),
        v1_body_utf8=b"",
        commitment_key=_COMMITMENT_KEY,
        run_id="nls3run_3123456789abcdef",
        runner_sha256=step10_source_file_sha256(_RUNNER_SHA256_PATH),
    )
    assert empty_v1.receipt["v1_baseline_body_commitment"] != hashlib.sha256(
        b""
    ).hexdigest()

    passed_review = build_local_product_review(
        case_identity_commitment=receipt["case_identity_commitment"],
        run_id=_RUN_ID,
        selected_candidate_body_commitment=receipt[
            "selected_candidate_body_commitment"
        ],
        status="passed",
        axis_results={axis: "passed" for axis in LOCAL_REVIEW_AXES},
        reason_codes=(
            "INPUT_SPECIFIC",
            "BOUND_EMLIS_RECEPTION",
            "NATURAL_ENOUGH",
        ),
    )
    assert passed_review["case_identity_commitment"] == receipt[
        "case_identity_commitment"
    ]
    assert passed_review["selected_candidate_body_commitment"] == receipt[
        "selected_candidate_body_commitment"
    ]
    _raises_code(
        Step10EvidenceError,
        "LOCAL_REVIEW_FAILED_STATE_INVALID",
        lambda: build_local_product_review(
            case_identity_commitment=receipt["case_identity_commitment"],
            run_id=_RUN_ID,
            selected_candidate_body_commitment=receipt[
                "selected_candidate_body_commitment"
            ],
            status="failed",
            axis_results={
                **{axis: "passed" for axis in LOCAL_REVIEW_AXES},
                LOCAL_REVIEW_AXES[0]: "failed",
                LOCAL_REVIEW_AXES[1]: "not_reviewed",
            },
            reason_codes=("REQUIRED_MEANING_MISSING",),
            severity="BLOCKER",
        ),
    )
    ledger = build_change_ledger_row(
        before_source_closure_sha256="1" * 64,
        failure_case_commitment="2" * 64,
        failure_layer="evidence",
        severity="BLOCKER",
        failure_code="RAW_BODY_LEAK",
        shared_structural_hypothesis_sha256="3" * 64,
        changed_file_hashes=(
            {"path": "ai/example.py", "sha256": "4" * 64},
        ),
        case_specific_workaround_check_sha256="5" * 64,
        after_source_closure_sha256="6" * 64,
        cumulative_rerun_receipt_sha256="7" * 64,
        new_batch_first_run_receipt_sha256="8" * 64,
        decision="accepted",
    )
    assert ledger["case_specific_workaround_forbidden_check"] == {
        "status": "passed",
        "evidence_sha256": "5" * 64,
    }
    assert ledger["new_batch_first_run_receipt_sha256"] == "8" * 64

    no_valid_rows = [
        {
            "status": "v3_no_valid_candidate",
            "runtime_summary": {},
            "receipt": {"selected_candidate_body_commitment": "f" * 64},
            "surface_profile": {
                "opening_family": None,
                "ending_family": None,
                "predicate_families": [],
                "reception_act_families": [],
                "near_duplicate_skeleton_commitment": None,
            },
        },
        {
            "status": "v3_no_valid_candidate",
            "runtime_summary": {},
            "receipt": {"selected_candidate_body_commitment": "f" * 64},
            "surface_profile": {
                "opening_family": None,
                "ending_family": None,
                "predicate_families": [],
                "reception_act_families": [],
                "near_duplicate_skeleton_commitment": None,
            },
        },
    ]
    no_valid_aggregate = evidence_module._aggregate(no_valid_rows)
    assert no_valid_aggregate["output_duplicate_cluster_count"] == 0
    assert no_valid_aggregate["near_duplicate_cluster_count"] == 0


def test_s10_partial_batch_cannot_claim_formal_completion_or_acceptance() -> None:
    _private, partial = _evidence_pair(expected_case_count=2)
    assert validate_batch_run_summary(partial) == ()
    assert partial["executed_case_count"] == 1
    assert partial["all_expected_cases_executed"] is False
    assert partial["machine_status"] == "incomplete"
    assert partial["step10_smoke_only"] is True
    assert partial["formal_batch001_initial_run_locked"] is False
    assert partial["batch_accepted"] is False
    assert partial["next_step_authority"] == "step11_cycle001_initial_run_only"

    forged = deepcopy(partial)
    forged["all_expected_cases_executed"] = True
    forged["machine_status"] = "clean"
    forged["formal_batch001_initial_run_locked"] = True
    forged["batch_accepted"] = True
    issues = validate_batch_run_summary(forged)
    assert "BATCH_RUN_COMPLETENESS_MISMATCH" in issues
    assert "BATCH_RUN_STATUS_MISMATCH" in issues
    assert "BATCH_RUN_STEP_BOUNDARY_INVALID" in issues


def test_s10_cumulative_uses_fresh_closure_and_rejects_missing_or_duplicate_cases() -> None:
    _private, complete = _evidence_pair(expected_case_count=1)
    assert fresh_step10_source_closure_sha256() == (
        FROZEN_STEP10_DEPENDENCY_CLOSURE_SHA256
    )
    expected = {"nls3_batch_001": [_CASE_ID]}
    cumulative = build_cumulative_run_manifest(
        [complete],
        expected_case_ids_by_batch=expected,
        expected_batch_manifest_sha256_by_batch={"nls3_batch_001": "a" * 64},
        cumulative_run_id="nls3cum_0123456789abcdef",
    )
    assert cumulative["source_closure_start_sha256"] == (
        FROZEN_STEP10_DEPENDENCY_CLOSURE_SHA256
    )
    assert cumulative["source_closure_end_sha256"] == (
        FROZEN_STEP10_DEPENDENCY_CLOSURE_SHA256
    )
    assert cumulative["source_closure_stable"] is True
    assert cumulative["formal_status"] == "step10_ready_for_step11"
    assert cumulative["batch_acceptance_claimed"] is False
    assert cumulative["next_step_authority"] == "step11_cycle001_initial_run_only"

    missing = build_cumulative_run_manifest(
        [complete],
        expected_case_ids_by_batch={
            "nls3_batch_001": [_CASE_ID, "nls3s_b001_0002"]
        },
        expected_batch_manifest_sha256_by_batch={"nls3_batch_001": "a" * 64},
        cumulative_run_id="nls3cum_1123456789abcdef",
    )
    assert missing["all_expected_cases_executed"] is False
    assert missing["formal_status"] == "incomplete_or_failed"

    duplicate = deepcopy(complete)
    duplicate["case_rows"].append(deepcopy(duplicate["case_rows"][0]))
    duplicate["executed_case_count"] = 2
    duplicate["expected_case_count"] = 2
    duplicate["aggregate"]["case_count"] = 2
    duplicate["aggregate"]["selected_count"] = 2
    duplicate["all_expected_cases_executed"] = True
    assert "BATCH_RUN_CASE_ORDER_OR_ID_INVALID" in (
        validate_batch_run_summary(duplicate)
    )
    _raises_code(
        Step10EvidenceError,
        "CUMULATIVE_BATCH_SUMMARY_INVALID",
        lambda: build_cumulative_run_manifest(
            [duplicate],
            expected_case_ids_by_batch={
                "nls3_batch_001": [_CASE_ID, _CASE_ID]
            },
            expected_batch_manifest_sha256_by_batch={"nls3_batch_001": "a" * 64},
            cumulative_run_id="nls3cum_2123456789abcdef",
        ),
    )
    _raises_code(
        Step10EvidenceError,
        "CUMULATIVE_BATCH_ID_DUPLICATE",
        lambda: build_cumulative_run_manifest(
            [complete, deepcopy(complete)],
            expected_case_ids_by_batch=expected,
            expected_batch_manifest_sha256_by_batch={
                "nls3_batch_001": "a" * 64
            },
            cumulative_run_id="nls3cum_3123456789abcdef",
        ),
    )


def test_s10_output_diff_is_body_free_and_commitment_based() -> None:
    _private, previous = _evidence_pair(expected_case_count=1)
    current = _retag_batch_run(previous, "nls3run_1123456789abcdef")
    unchanged = build_output_diff(previous, current)
    assert unchanged["aggregate"] == {
        "case_count": 1,
        "changed_count": 0,
        "unchanged_count": 1,
    }
    assert_body_free(unchanged)

    changed_parent = _retag_batch_run(
        current,
        "nls3run_2123456789abcdef",
    )
    changed_parent["case_rows"][0]["receipt"][
        "selected_candidate_body_commitment"
    ] = "f" * 64
    changed = build_output_diff(current, changed_parent)
    assert changed["aggregate"]["changed_count"] == 1
    assert changed["case_rows"][0]["changed"] is True
    serialized = json.dumps(changed, ensure_ascii=False, sort_keys=True)
    assert _execution().final_utf8_bytes.decode("utf-8") not in serialized

    later_rc = _retag_batch_run(
        current,
        "nls3run_4123456789abcdef",
    )
    later_rc["candidate_version_id"] = "nls_v3_rc_0011"
    later_rc["source_dependency_closure_sha256"] = "e" * 64
    later_rc["source_closure_start_sha256"] = "e" * 64
    later_rc["source_closure_end_sha256"] = "e" * 64
    for row in later_rc["case_rows"]:
        row["runtime_summary"]["candidate_version_id"] = "nls_v3_rc_0011"
        row["runtime_summary"]["source_dependency_closure_sha256"] = "e" * 64
        row["receipt"]["candidate_version_id"] = "nls_v3_rc_0011"
        row["receipt"]["source_dependency_closure_sha256"] = "e" * 64
    assert validate_historical_batch_run_summary(later_rc) == ()
    cross_rc = build_output_diff(current, later_rc)
    assert cross_rc["previous_candidate_version_id"] == _CANDIDATE_VERSION
    assert cross_rc["current_candidate_version_id"] == "nls_v3_rc_0011"
    assert cross_rc["previous_source_dependency_closure_sha256"] != (
        cross_rc["current_source_dependency_closure_sha256"]
    )


def test_s10_rn_api_db_and_step9_historical_boundaries_remain_frozen() -> None:
    assert rn_contract_binding_issues() == ()
    boundary = json.loads(_STEP0_BOUNDARY_PATH.read_text(encoding="utf-8"))[
        "unchanged_contracts"
    ]
    assert boundary["route"] == "POST /emotion/submit"
    assert boundary["db_physical_names_changed"] is False
    assert boundary["db_write_paths_changed"] is False
    assert boundary["rn_production_changed"] is False
    assert boundary["public_response_keys_changed"] is False

    current_hashes = current_step10_source_hashes()
    for path in (
        "ai/services/ai_inference/api_contract_registry.py",
        "ai/services/ai_inference/emlis_ai_public_feedback_meta.py",
        "ai/services/ai_inference/emotion_submit_service.py",
    ):
        assert current_hashes[path] == STEP10_DEPENDENCY_MANIFEST[
            "unchanged_contract_files"
        ][path]
    for path in STEP10_DEPENDENCY_MANIFEST["local_e2e_integration_files"]:
        assert current_hashes[path] == STEP10_DEPENDENCY_MANIFEST[
            "local_e2e_integration_files"
        ][path]
    receipt_schema_path = (
        "ai/tests/schemas/emlis_nls_v3_case_evidence_receipt_v3.schema.json"
    )
    assert current_hashes[receipt_schema_path] == STEP10_DEPENDENCY_MANIFEST[
        "step10_contract_files"
    ][receipt_schema_path]

    historical_hash = (
        "9ac49f3ee8978f48ff402afdd9fb15f16063595546898e514b09b9bdaf58e880"
    )
    historical_reply_hash = (
        "a8b494ff6d14df771e3f1c17d7d516c8457daf17a9431a118f3b44088aff90b6"
    )
    assert FROZEN_STEP9_DEPENDENCY_MANIFEST_SHA256 == historical_hash
    assert STEP9_DEPENDENCY_MANIFEST_SHA256 == historical_hash
    assert artifact_sha256(STEP9_DEPENDENCY_MANIFEST) == historical_hash
    assert STEP9_DEPENDENCY_MANIFEST["source_files"][
        "emlis_ai_reply_service.py"
    ] == historical_reply_hash
    current_reply_hash = hashlib.sha256(
        (_INFERENCE_ROOT / "emlis_ai_reply_service.py").read_bytes()
    ).hexdigest()
    assert current_reply_hash != historical_reply_hash
    assert step9_manifest_module.AUTHORIZED_STEP10_REPLY_SERVICE_SHA256 == (
        current_reply_hash
    )
    assert validate_step9_dependency_manifest() == ()

    assert FROZEN_STEP10_MANIFEST_SHA256 == artifact_sha256(
        STEP10_DEPENDENCY_MANIFEST
    )
    assert step10_manifest_module.STEP10_DEPENDENCY_MANIFEST_SHA256 == (
        FROZEN_STEP10_MANIFEST_SHA256
    )
    assert normalized_step10_manifest_source_sha256() == (
        FROZEN_STEP10_MANIFEST_SOURCE_NORMALIZED_SHA256
    )
    assert validate_step10_dependency_manifest() == ()


def test_s10_local_emotion_submit_e2e_preserves_db_and_public_contract() -> None:
    missing = object()
    module_names = (
        "emotion_submit_service",
        "fastapi",
        "api_emotion_submit",
        "response_microcache",
        "subscription_store",
    )
    saved_modules = {
        name: sys.modules.get(name, missing) for name in module_names
    }

    fastapi_stub = ModuleType("fastapi")

    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str) -> None:
            self.status_code = status_code
            self.detail = detail
            super().__init__(detail)

    fastapi_stub.HTTPException = HTTPException
    api_stub = ModuleType("api_emotion_submit")

    class EmotionItem:
        def __init__(self, *, type: str, strength: str) -> None:
            self.type = type
            self.strength = strength

    def normalize_emotions(raw: Any):
        rows = [
            {
                "type": str(getattr(item, "type", item)).strip(),
                "strength": str(getattr(item, "strength", "medium")),
            }
            for item in raw
        ]
        rows = [row for row in rows if row["type"]]
        scores = {"weak": 1.0, "medium": 2.0, "strong": 3.0}
        return (
            [row["type"] for row in rows],
            rows,
            sum(scores.get(row["strength"], 2.0) for row in rows) / len(rows)
            if rows
            else None,
        )

    async def unavailable_async(**_kwargs: Any):
        raise AssertionError("production dependency escaped Step10 DB mock")

    api_stub.ALLOW_LEGACY_USER_ID = False
    api_stub.EmotionItem = EmotionItem
    api_stub._extract_bearer_token = lambda value: value
    api_stub._global_summary_activity_date_from_created_at = (
        lambda _value: "2026-07-16"
    )
    api_stub._insert_emotion_row = unavailable_async
    api_stub._normalize_categories = lambda value: list(dict.fromkeys(value or []))
    api_stub._normalize_emotions = normalize_emotions
    api_stub._resolve_user_id_from_token = unavailable_async
    api_stub._start_post_submit_background_tasks = lambda **_kwargs: None
    microcache_stub = ModuleType("response_microcache")
    microcache_stub.invalidate_prefix = unavailable_async
    subscription_store_stub = ModuleType("subscription_store")
    subscription_store_stub.get_subscription_tier_for_user = unavailable_async
    sys.modules["fastapi"] = fastapi_stub
    sys.modules["api_emotion_submit"] = api_stub
    sys.modules["response_microcache"] = microcache_stub
    sys.modules["subscription_store"] = subscription_store_stub
    sys.modules.pop("emotion_submit_service", None)

    captured: dict[str, Any] = {}

    async def fake_insert_emotion_row(**kwargs: Any) -> dict[str, Any]:
        captured["db_write"] = dict(kwargs)
        return {
            "id": "nls-v3-step10-db-mock-1",
            "created_at": "2026-07-16T00:00:00+00:00",
        }

    async def fake_invalidate_prefix(_prefix: str) -> None:
        return None

    async def fake_subscription_tier_for_user(
        *_args: Any,
        **_kwargs: Any,
    ) -> str:
        return "free"

    async def fake_render_reply(**kwargs: Any):
        execution = reply_service_module._render_emlis_ai_reply_v3_dormant(
            current_input=kwargs["current_input"],
            candidate_version_id=_CANDIDATE_VERSION,
        )
        captured["execution"] = execution
        return map_verified_v3_bytes_to_reply_envelope(execution)

    try:
        import emotion_submit_service as submit_service
    except Exception:
        for name, previous in saved_modules.items():
            if previous is missing:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = previous
        raise

    replacements = {
        "_insert_emotion_row": fake_insert_emotion_row,
        "invalidate_prefix": fake_invalidate_prefix,
        "_global_summary_activity_date_from_created_at": (
            lambda _created_at: "2026-07-16"
        ),
        "_start_post_submit_background_tasks": lambda **_kwargs: None,
        "get_subscription_tier_for_user": fake_subscription_tier_for_user,
        "render_emlis_ai_reply": fake_render_reply,
        "_build_phase14_reception_mode_timing_probe": lambda _value: {
            "probe_succeeded": True,
            "probe_elapsed_ms": 0,
            "shared_evidence_elapsed_ms": 0,
            "reception_mode_elapsed_ms": 0,
            "reception_mode_id": "",
            "reception_mode_family": "",
            "daily_reception_branch": False,
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
        "_log_emlis_ai_observation_result": lambda **_kwargs: None,
        "_log_emlis_ai_observation_diagnostic_lockdown": (
            lambda **_kwargs: None
        ),
    }
    for name, replacement in replacements.items():
        setattr(submit_service, name, replacement)
    sample_input = _sample()["input"]
    try:
        result = asyncio.run(
            submit_service.persist_emotion_submission(
                user_id="nls-v3-step10-e2e-user",
                emotions=[
                    submit_service.EmotionItem(
                        type=row["type"],
                        strength=row["strength"],
                    )
                    for row in sample_input["emotions"]
                ],
                memo=sample_input["thought_text"],
                memo_action=sample_input["action_text"],
                category=sample_input["categories"],
                created_at="2026-07-16T00:00:00+00:00",
            )
        )
    finally:
        for name, previous in saved_modules.items():
            if previous is missing:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = previous

    execution = captured["execution"]
    assert type(execution) is DormantRuntimeExecution
    assert execution.status == "selected"
    assert result["input_feedback_comment"].encode("utf-8") == (
        execution.final_utf8_bytes
    )
    assert result["input_feedback_meta"]["observation_status"] == "passed"
    assert should_include_public_input_feedback(
        result["input_feedback_comment"],
        result["input_feedback_meta"],
    )
    assert execution.final_utf8_bytes.decode("utf-8") not in json.dumps(
        result["input_feedback_meta"],
        ensure_ascii=False,
        sort_keys=True,
    )
    db_write = captured["db_write"]
    assert set(db_write) == {
        "user_id",
        "emotions",
        "emotion_details",
        "emotion_strength_avg",
        "memo",
        "memo_action",
        "category",
        "created_at",
        "is_secret",
    }
    assert db_write["memo"] == sample_input["thought_text"]
    assert db_write["memo_action"] == sample_input["action_text"]
    assert db_write["category"] == sample_input["categories"]
    assert "input_feedback" not in db_write
