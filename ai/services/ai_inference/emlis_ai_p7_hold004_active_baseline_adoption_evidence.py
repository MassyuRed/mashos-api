# -*- coding: utf-8 -*-
"""P7-HOLD-004 active-baseline adoption evidence materials.

R30/R35 scope only:
- freeze the local repeated full-backend collect-only evidence as body-free
  material;
- record the source identity decision without promoting the current local
  attachment alias to a runtime source_snapshot_ref;
- classify the received/active item fingerprint mismatch as a stale baseline
  constant only after the R30/R31 evidence is satisfied;
- record the test-semantics boundary as an accepted baseline refresh without
  claiming semantic no-change;
- bundle R30/R33 evidence and connect it to the existing R27 evidence freeze
  without updating the active baseline;
- open the conditional active-baseline adoption gate only through that bundle;
- keep runtime builder refresh, official group_02 capture, HOLD closure,
  release, P7 completion, and P8 start outside this step.

Only identifiers, counts, booleans, enum-like statuses, and SHA-256 hashes are
stored. Raw input, comment_text bodies, candidate/surface bodies, pytest nodeid
lists, terminal output, stdout/stderr, and traceback bodies must not be stored.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any, Final

from emlis_ai_p7_contracts import (
    P7_GIT_CHECKED,
    P7_PHASE,
    P7_SOURCE_MODE,
    assert_false_markers,
    assert_p7_no_body_payload_or_contract_mutation,
    body_free_flags,
    clean_identifier,
    dedupe_identifiers,
    public_contract_flags,
    safe_mapping,
)
from emlis_ai_p7_hold004_backend_suite_split_consistency import (
    P7_HOLD004_BACKEND_COLLECT_FINGERPRINT_ALGORITHM,
    P7_HOLD004_BACKEND_COLLECT_WARNINGS_COUNT,
    P7_HOLD004_BACKEND_COLLECTED_TEST_FILE_COUNT,
    P7_HOLD004_BACKEND_COLLECTED_TEST_ITEM_COUNT,
    P7_HOLD004_BACKEND_SUITE_HOLD_ID,
)
from emlis_ai_p7_hold004_received_snapshot_baseline_fingerprint_reconcile import (
    P7_HOLD004_ACTIVE_BASELINE_ID_AT_RECEIPT,
    P7_HOLD004_ACTIVE_SOURCE_SNAPSHOT_REF_AT_RECEIPT,
    P7_HOLD004_ACTIVE_TEST_FILES_FINGERPRINT_SHA256_AT_RECEIPT,
    P7_HOLD004_ACTIVE_TEST_ITEMS_FINGERPRINT_SHA256_AT_RECEIPT,
    P7_HOLD004_RECEIVED_ADOPTABLE_ROOT_CAUSE_STATUSES,
    P7_HOLD004_RECEIVED_ADOPTION_EVIDENCE_STATUS_SATISFIED_FOR_R27_CONDITIONAL_ADOPTION,
    P7_HOLD004_RECEIVED_ADOPTION_STATUS_ADOPTABLE_AS_RECEIVED_SNAPSHOT_BASELINE_REFRESH,
    P7_HOLD004_RECEIVED_COLLECT_WARNINGS_COUNT,
    P7_HOLD004_RECEIVED_COLLECTED_TEST_FILE_COUNT,
    P7_HOLD004_RECEIVED_COLLECTED_TEST_ITEM_COUNT,
    P7_HOLD004_RECEIVED_ROOT_CAUSE_STATUSES,
    P7_HOLD004_RECEIVED_ROOT_CAUSE_STATUS_UNCLASSIFIED,
    P7_HOLD004_RECEIVED_SNAPSHOT_ADOPTION_EVIDENCE_FREEZE_ID,
    P7_HOLD004_RECEIVED_SNAPSHOT_ADOPTION_EVIDENCE_FREEZE_SCHEMA_VERSION,
    P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_ID,
    P7_HOLD004_RECEIVED_SNAPSHOT_CANDIDATE_NEW_BASELINE_ID,
    P7_HOLD004_RECEIVED_SNAPSHOT_CONDITIONAL_ACTIVE_BASELINE_ADOPTION_ID,
    P7_HOLD004_RECEIVED_SNAPSHOT_CONDITIONAL_ACTIVE_BASELINE_ADOPTION_SCHEMA_VERSION,
    P7_HOLD004_RECEIVED_TEST_FILES_FINGERPRINT_SHA256,
    P7_HOLD004_RECEIVED_TEST_ITEMS_FINGERPRINT_SHA256,
    P7_HOLD004_RECEIVED_TEST_SEMANTICS_REVIEW_OUTCOME_ACCEPTED_AS_BASELINE_REFRESH,
    P7_HOLD004_RECEIVED_TEST_SEMANTICS_REVIEW_OUTCOME_NO_SEMANTIC_CHANGE_DETECTED,
    P7_HOLD004_RECEIVED_TEST_SEMANTICS_REVIEW_OUTCOME_NOT_REVIEWED,
    P7_HOLD004_RECEIVED_TEST_SEMANTICS_REVIEW_OUTCOMES,
    P7_HOLD004_RECEIVED_ZIP_REF,
    assert_p7_hold004_received_snapshot_adoption_evidence_freeze_contract,
    assert_p7_hold004_received_snapshot_baseline_fingerprint_reconcile_contract,
    assert_p7_hold004_received_snapshot_conditional_active_baseline_adoption_contract,
    build_p7_hold004_received_snapshot_adoption_evidence_freeze,
    build_p7_hold004_received_snapshot_baseline_fingerprint_reconcile,
    build_p7_hold004_received_snapshot_conditional_active_baseline_adoption,
)

P7_HOLD004_LOCAL_REPEAT_COLLECT_EVIDENCE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.local_repeat_collect_evidence.v1"
)
P7_HOLD004_SOURCE_IDENTITY_DECISION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.source_identity_decision.v1"
)
P7_HOLD004_ITEM_FINGERPRINT_ROOT_CAUSE_REVIEW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.item_fingerprint_root_cause_review.v1"
)
P7_HOLD004_TEST_SEMANTICS_REVIEW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.test_semantics_review.v1"
)
P7_HOLD004_ACTIVE_BASELINE_ADOPTION_EVIDENCE_BUNDLE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.active_baseline_adoption_evidence_bundle.v1"
)
P7_HOLD004_CONDITIONAL_ACTIVE_BASELINE_ADOPTION_GATE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.conditional_active_baseline_adoption_gate.v1"
)
P7_HOLD004_LOCAL_REPEAT_COLLECT_EVIDENCE_STEP: Final = (
    "P7-HOLD-004_ActiveBaselineAdoptionEvidence_R30_LocalRepeatCollectEvidenceFreeze_20260616"
)
P7_HOLD004_SOURCE_IDENTITY_DECISION_STEP: Final = (
    "P7-HOLD-004_ActiveBaselineAdoptionEvidence_R31_SourceIdentityDecisionBoundary_20260616"
)
P7_HOLD004_ITEM_FINGERPRINT_ROOT_CAUSE_REVIEW_STEP: Final = (
    "P7-HOLD-004_ActiveBaselineAdoptionEvidence_R32_RootCauseReviewMaterial_20260616"
)
P7_HOLD004_TEST_SEMANTICS_REVIEW_STEP: Final = (
    "P7-HOLD-004_ActiveBaselineAdoptionEvidence_R33_TestSemanticsReviewBoundary_20260616"
)
P7_HOLD004_ACTIVE_BASELINE_ADOPTION_EVIDENCE_BUNDLE_STEP: Final = (
    "P7-HOLD-004_ActiveBaselineAdoptionEvidence_R34_AdoptionEvidenceBundle_R27Connection_20260616"
)
P7_HOLD004_CONDITIONAL_ACTIVE_BASELINE_ADOPTION_GATE_STEP: Final = (
    "P7-HOLD-004_ActiveBaselineAdoptionEvidence_R35_ConditionalActiveBaselineAdoptionGate_20260616"
)
P7_HOLD004_LOCAL_REPEAT_COLLECT_EVIDENCE_ID: Final = "p7_hold004_local_repeat_collect_evidence_20260616"
P7_HOLD004_SOURCE_IDENTITY_DECISION_ID: Final = "p7_hold004_source_identity_decision_20260616"
P7_HOLD004_ITEM_FINGERPRINT_ROOT_CAUSE_REVIEW_ID: Final = "p7_hold004_item_fingerprint_root_cause_review_20260616"
P7_HOLD004_TEST_SEMANTICS_REVIEW_ID: Final = "p7_hold004_test_semantics_review_20260616"
P7_HOLD004_ACTIVE_BASELINE_ADOPTION_EVIDENCE_BUNDLE_ID: Final = (
    "p7_hold004_active_baseline_adoption_evidence_bundle_20260616"
)
P7_HOLD004_CONDITIONAL_ACTIVE_BASELINE_ADOPTION_GATE_ID: Final = (
    "p7_hold004_conditional_active_baseline_adoption_gate_20260616"
)
P7_HOLD004_LOCAL_ATTACHMENT_REF_OBSERVED: Final = "mashos-api(151).zip"
P7_HOLD004_FULL_BACKEND_COLLECT_ONLY_SCOPE: Final = "full_backend_collect_only"
P7_HOLD004_LOCAL_REPEAT_COLLECT_SCOPE: Final = P7_HOLD004_FULL_BACKEND_COLLECT_ONLY_SCOPE
P7_HOLD004_MINIMUM_REPEAT_COLLECT_RUN_COUNT: Final = 2
P7_HOLD004_LOCAL_REPEAT_COLLECT_MINIMUM_RUN_COUNT: Final = P7_HOLD004_MINIMUM_REPEAT_COLLECT_RUN_COUNT
P7_HOLD004_ACTIVE_BASELINE_ADOPTION_R30_STEP: Final = P7_HOLD004_LOCAL_REPEAT_COLLECT_EVIDENCE_STEP
P7_HOLD004_ACTIVE_BASELINE_ADOPTION_R31_STEP: Final = P7_HOLD004_SOURCE_IDENTITY_DECISION_STEP
P7_HOLD004_ACTIVE_BASELINE_ADOPTION_R32_STEP: Final = P7_HOLD004_ITEM_FINGERPRINT_ROOT_CAUSE_REVIEW_STEP
P7_HOLD004_ACTIVE_BASELINE_ADOPTION_R33_STEP: Final = P7_HOLD004_TEST_SEMANTICS_REVIEW_STEP
P7_HOLD004_ACTIVE_BASELINE_ADOPTION_R34_STEP: Final = P7_HOLD004_ACTIVE_BASELINE_ADOPTION_EVIDENCE_BUNDLE_STEP
P7_HOLD004_ACTIVE_BASELINE_ADOPTION_R35_STEP: Final = P7_HOLD004_CONDITIONAL_ACTIVE_BASELINE_ADOPTION_GATE_STEP
P7_HOLD004_ROOT_CAUSE_STATUS_BASELINE_CONSTANT_STALE: Final = "BASELINE_CONSTANT_STALE"
P7_HOLD004_SOURCE_IDENTITY_STATUS_RECEIVED_REF_ACCEPTED_ATTACHMENT_ALIAS_NOT_PROMOTED: Final = (
    "RECEIVED_REF_ACCEPTED_AS_CANONICAL_REFRESH_CANDIDATE_ATTACHMENT_ALIAS_NOT_PROMOTED"
)
P7_HOLD004_SOURCE_IDENTITY_STATUS_ACCEPTED: Final = (
    P7_HOLD004_SOURCE_IDENTITY_STATUS_RECEIVED_REF_ACCEPTED_ATTACHMENT_ALIAS_NOT_PROMOTED
)
P7_HOLD004_SOURCE_IDENTITY_STATUS_BLOCKED_LOCAL_ATTACHMENT_PROMOTED: Final = (
    "BLOCKED_LOCAL_ATTACHMENT_ALIAS_PROMOTED_TO_SOURCE_SNAPSHOT_REF"
)
P7_HOLD004_SOURCE_IDENTITY_STATUS_BLOCKED_CANONICAL_REF_MISMATCH: Final = (
    "BLOCKED_CANONICAL_RECEIVED_REF_MISMATCH"
)
P7_HOLD004_SOURCE_IDENTITY_STATUS_BLOCKED_SOURCE_IDENTITY_UNCLEAR: Final = "BLOCKED_SOURCE_IDENTITY_UNCLEAR"
P7_HOLD004_SOURCE_IDENTITY_STATUSES: Final[frozenset[str]] = frozenset(
    {
        P7_HOLD004_SOURCE_IDENTITY_STATUS_RECEIVED_REF_ACCEPTED_ATTACHMENT_ALIAS_NOT_PROMOTED,
        P7_HOLD004_SOURCE_IDENTITY_STATUS_BLOCKED_LOCAL_ATTACHMENT_PROMOTED,
        P7_HOLD004_SOURCE_IDENTITY_STATUS_BLOCKED_CANONICAL_REF_MISMATCH,
        P7_HOLD004_SOURCE_IDENTITY_STATUS_BLOCKED_SOURCE_IDENTITY_UNCLEAR,
    }
)
P7_HOLD004_ITEM_FINGERPRINT_ROOT_CAUSE_REVIEW_ALLOWED_STATUSES: Final[frozenset[str]] = frozenset(
    P7_HOLD004_RECEIVED_ROOT_CAUSE_STATUSES
)
P7_HOLD004_ITEM_FINGERPRINT_ROOT_CAUSE_REVIEW_ADOPTABLE_STATUSES: Final[frozenset[str]] = frozenset(
    P7_HOLD004_RECEIVED_ADOPTABLE_ROOT_CAUSE_STATUSES
)
P7_HOLD004_TEST_SEMANTICS_REVIEW_ALLOWED_OUTCOMES: Final[frozenset[str]] = frozenset(
    P7_HOLD004_RECEIVED_TEST_SEMANTICS_REVIEW_OUTCOMES
)

_SHA256_HEX_LENGTH: Final = 64
_RELEASE_CLOSED_KEYS: Final[tuple[str, ...]] = (
    "full_backend_suite_green_confirmed",
    "full_backend_suite_green_claim_allowed",
    "hold004_close_allowed",
    "p7_complete",
    "p7_complete_claim_allowed",
    "p8_start_allowed",
    "release_allowed",
    "split_green_is_full_backend_suite_green",
    "split_green_can_close_p7_hold004",
)
_CAPTURE_CLOSED_KEYS: Final[tuple[str, ...]] = (
    "active_baseline_update_allowed",
    "active_baseline_update_applied_to_runtime_builders",
    "source_snapshot_ref_updated_in_active_builders",
    "official_group_02_capture_run_allowed",
    "official_group_02_capture_result_recording_allowed",
    "can_claim_group_green",
    "can_claim_full_backend_suite_green",
)
_BODY_RETENTION_KEYS: Final[tuple[str, ...]] = (
    "nodeids_retained",
    "pytest_output_retained",
    "terminal_output_retained",
    "stdout_retained",
    "stderr_retained",
    "raw_traceback_included",
)
_BOUNDARY_FLAG_KEYS: Final[tuple[str, ...]] = (
    "rn_visible_contract_changed",
    "api_route_changed",
    "request_key_changed",
    "api_response_key_added",
    "public_response_key_added",
    "response_shape_changed",
    "db_schema_changed",
    "db_physical_name_changed",
    "public_release_applied",
    "display_gate_relaxed",
    "reader_gate_relaxed",
    "grounding_gate_relaxed",
    "template_gate_relaxed",
    "runtime_surface_gate_relaxed",
    "visible_surface_gate_relaxed",
    "gate_relaxed",
    "fixed_sentence_template_added",
    "runtime_fixture_branch_added",
)
_IMPLEMENTATION_SCOPE_FLAGS: Final[dict[str, bool]] = {
    "r30_local_repeat_collect_evidence_freeze_added": True,
    "r31_source_identity_decision_boundary_added": True,
    "r32_root_cause_review_added": False,
    "r33_test_semantics_review_added": False,
    "r34_adoption_evidence_bundle_added": False,
    "r35_conditional_active_baseline_adoption_gate_added": False,
    "active_baseline_change_allowed": False,
    "runtime_builder_refresh_allowed": False,
    "runtime_behavior_change_allowed": False,
    "rn_change_allowed": False,
    "api_contract_change_allowed": False,
    "db_change_allowed": False,
    "release_decision_change_allowed": False,
    "p8_implementation_allowed": False,
}
_R32_IMPLEMENTATION_SCOPE_FLAGS: Final[dict[str, bool]] = {
    **_IMPLEMENTATION_SCOPE_FLAGS,
    "r32_root_cause_review_added": True,
}
_R33_IMPLEMENTATION_SCOPE_FLAGS: Final[dict[str, bool]] = {
    **_R32_IMPLEMENTATION_SCOPE_FLAGS,
    "r33_test_semantics_review_added": True,
}
_R34_IMPLEMENTATION_SCOPE_FLAGS: Final[dict[str, bool]] = {
    **_R33_IMPLEMENTATION_SCOPE_FLAGS,
    "r34_adoption_evidence_bundle_added": True,
}
_R35_IMPLEMENTATION_SCOPE_FLAGS: Final[dict[str, bool]] = {
    **_R34_IMPLEMENTATION_SCOPE_FLAGS,
    "r35_conditional_active_baseline_adoption_gate_added": True,
    "active_baseline_change_allowed": True,
}
_R30_REQUIRED_FOLLOWUP_FIXES: Final[tuple[str, ...]] = (
    "item_fingerprint_root_cause_review_required",
    "test_semantics_review_required",
    "adoption_evidence_bundle_required_before_active_baseline_update",
    "runtime_builder_refresh_not_applied_by_r30",
    "official_group_02_capture_blocked_until_later_gate",
    "full_backend_suite_green_unconfirmed",
)
_R31_REQUIRED_FOLLOWUP_FIXES: Final[tuple[str, ...]] = (
    "item_fingerprint_root_cause_review_required",
    "test_semantics_review_required",
    "adoption_evidence_bundle_required_before_active_baseline_update",
    "runtime_builder_refresh_not_applied_by_r31",
    "official_group_02_capture_blocked_until_later_gate",
    "full_backend_suite_green_unconfirmed",
)
_R32_REQUIRED_FOLLOWUP_FIXES: Final[tuple[str, ...]] = (
    "test_semantics_review_required",
    "adoption_evidence_bundle_required_before_active_baseline_update",
    "runtime_builder_refresh_not_applied_by_r32",
    "official_group_02_capture_blocked_until_later_gate",
    "full_backend_suite_green_unconfirmed",
)
_R33_REQUIRED_FOLLOWUP_FIXES: Final[tuple[str, ...]] = (
    "adoption_evidence_bundle_required_before_active_baseline_update",
    "runtime_builder_refresh_not_applied_by_r33",
    "official_group_02_capture_blocked_until_later_gate",
    "full_backend_suite_green_unconfirmed",
)
_R34_REQUIRED_FOLLOWUP_FIXES: Final[tuple[str, ...]] = (
    "conditional_active_baseline_adoption_gate_required_after_r34",
    "active_baseline_refresh_not_applied_to_runtime_builders",
    "official_group_02_capture_blocked_until_received_snapshot_adoption",
    "full_backend_suite_green_unconfirmed",
)
_R35_REQUIRED_FOLLOWUP_FIXES: Final[tuple[str, ...]] = (
    "post_adoption_active_baseline_material_required_after_r35",
    "runtime_builder_refresh_required_after_r35",
    "official_group_02_capture_blocked_until_runtime_builder_refresh",
    "full_backend_suite_green_unconfirmed",
)


def _coerce_non_negative_int(value: Any, *, default: int = 0) -> int:
    if value is None or value == "" or isinstance(value, bool):
        return int(default)
    try:
        number = int(float(value))
    except (TypeError, ValueError):
        return int(default)
    return max(0, number)


def _coerce_bool(value: Any) -> bool:
    return value if isinstance(value, bool) else False


def _is_sha256_hex(value: Any) -> bool:
    text = str(value or "").strip()
    return len(text) == _SHA256_HEX_LENGTH and all(ch in "0123456789abcdef" for ch in text)


def _false_boundary_flags() -> dict[str, bool]:
    return {key: False for key in _BOUNDARY_FLAG_KEYS}


def _public_contract_boundary_flags() -> dict[str, bool]:
    flags = public_contract_flags()
    flags.update(_false_boundary_flags())
    return flags


def _body_free_markers() -> dict[str, bool]:
    flags = body_free_flags(include_history=True, include_reviewer=True, include_terminal=True)
    flags.update(
        {
            "pytest_nodeids_included": False,
            "pytest_output_included": False,
            "stdout_included": False,
            "stderr_included": False,
            "traceback_body_included": False,
            "test_body_included": False,
        }
    )
    return flags


def _release_closed_boundary() -> dict[str, bool]:
    return {key: False for key in _RELEASE_CLOSED_KEYS}


def _capture_closed_boundary() -> dict[str, bool]:
    return {key: False for key in _CAPTURE_CLOSED_KEYS}


def _body_retention_flags() -> dict[str, bool]:
    return {key: False for key in _BODY_RETENTION_KEYS}


def _expected_collect_summary() -> dict[str, Any]:
    return {
        "collected_test_file_count": P7_HOLD004_RECEIVED_COLLECTED_TEST_FILE_COUNT,
        "collected_test_item_count": P7_HOLD004_RECEIVED_COLLECTED_TEST_ITEM_COUNT,
        "warnings_count": P7_HOLD004_RECEIVED_COLLECT_WARNINGS_COUNT,
        "test_items_fingerprint_sha256": P7_HOLD004_RECEIVED_TEST_ITEMS_FINGERPRINT_SHA256,
        "test_files_fingerprint_sha256": P7_HOLD004_RECEIVED_TEST_FILES_FINGERPRINT_SHA256,
        "fingerprint_algorithm": P7_HOLD004_BACKEND_COLLECT_FINGERPRINT_ALGORITHM,
    }


def _expected_summary_matches_constants(value: Mapping[str, Any]) -> bool:
    data = safe_mapping(value)
    expected = _expected_collect_summary()
    return all(data.get(key) == expected_value for key, expected_value in expected.items())


def _collect_run_matches_expected(run: Mapping[str, Any]) -> bool:
    return _expected_summary_matches_constants(run)


def _observed_run_material(value: Mapping[str, Any] | None = None, *, index: int) -> dict[str, Any]:
    expected = _expected_collect_summary()
    data = safe_mapping(value)
    run = {
        "run_id": clean_identifier(
            data.get("run_id"),
            default=f"p7_hold004_local_repeat_collect_run_{index}_20260616",
            max_length=120,
        ),
        "collected_test_file_count": _coerce_non_negative_int(
            data.get("collected_test_file_count", expected["collected_test_file_count"])
        ),
        "collected_test_item_count": _coerce_non_negative_int(
            data.get("collected_test_item_count", expected["collected_test_item_count"])
        ),
        "warnings_count": _coerce_non_negative_int(data.get("warnings_count", expected["warnings_count"])),
        "test_items_fingerprint_sha256": clean_identifier(
            data.get("test_items_fingerprint_sha256", expected["test_items_fingerprint_sha256"]),
            default=expected["test_items_fingerprint_sha256"],
            max_length=_SHA256_HEX_LENGTH,
        ),
        "test_files_fingerprint_sha256": clean_identifier(
            data.get("test_files_fingerprint_sha256", expected["test_files_fingerprint_sha256"]),
            default=expected["test_files_fingerprint_sha256"],
            max_length=_SHA256_HEX_LENGTH,
        ),
        "fingerprint_algorithm": clean_identifier(
            data.get("fingerprint_algorithm", expected["fingerprint_algorithm"]),
            default=expected["fingerprint_algorithm"],
            max_length=240,
        ),
        **_body_retention_flags(),
        "body_free": True,
    }
    run["matches_expected"] = _collect_run_matches_expected(run)
    run["matches_expected_collect"] = run["matches_expected"]
    run["match_checks"] = {
        "file_count_match": run["collected_test_file_count"] == expected["collected_test_file_count"],
        "item_count_match": run["collected_test_item_count"] == expected["collected_test_item_count"],
        "warning_count_match": run["warnings_count"] == expected["warnings_count"],
        "test_items_fingerprint_match": run["test_items_fingerprint_sha256"] == expected["test_items_fingerprint_sha256"],
        "test_files_fingerprint_match": run["test_files_fingerprint_sha256"] == expected["test_files_fingerprint_sha256"],
    }
    return run


def _build_observed_runs(
    observed_collect_runs: Iterable[Mapping[str, Any]] | None,
    *,
    collect_run_count: int,
) -> list[dict[str, Any]]:
    if observed_collect_runs is not None:
        return [_observed_run_material(run, index=index) for index, run in enumerate(observed_collect_runs, start=1)]
    return [_observed_run_material(None, index=index) for index in range(1, collect_run_count + 1)]


def _observed_runs_stable(runs: list[Mapping[str, Any]]) -> bool:
    if len(runs) < P7_HOLD004_MINIMUM_REPEAT_COLLECT_RUN_COUNT:
        return False
    first = safe_mapping(runs[0])
    keys = (
        "collected_test_file_count",
        "collected_test_item_count",
        "warnings_count",
        "test_items_fingerprint_sha256",
        "test_files_fingerprint_sha256",
    )
    return all(all(safe_mapping(run).get(key) == first.get(key) for key in keys) for run in runs)


def _assert_common_closed_body_free(material: Mapping[str, Any], *, source: str) -> None:
    data = safe_mapping(material)
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_BACKEND_SUITE_HOLD_ID:
        raise ValueError(f"{source} scope mismatch")
    if data.get("source_mode") != P7_SOURCE_MODE or data.get("git_checked") is not False:
        raise ValueError(f"{source} source mode mismatch")
    for key in (*_RELEASE_CLOSED_KEYS, *_CAPTURE_CLOSED_KEYS):
        if data.get(key) is not False:
            raise ValueError(f"{source} must keep {key}=false")
    for key in _BODY_RETENTION_KEYS:
        if data.get(key) is not False:
            raise ValueError(f"{source} must keep {key}=false")
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must be body_free")
    assert_false_markers(safe_mapping(data.get("public_contract")), source=f"{source}.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source=f"{source}.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source=source)


def _implementation_scope_contract(scope: Mapping[str, Any], *, source: str) -> None:
    data = safe_mapping(scope)
    for key, expected in _IMPLEMENTATION_SCOPE_FLAGS.items():
        if data.get(key) is not expected:
            raise ValueError(f"{source}.implementation_scope.{key} mismatch")


def _implementation_scope_contract_for_step(
    scope: Mapping[str, Any],
    *,
    expected: Mapping[str, bool],
    source: str,
) -> None:
    data = safe_mapping(scope)
    for key, expected_value in expected.items():
        if data.get(key) is not expected_value:
            raise ValueError(f"{source}.implementation_scope.{key} mismatch")


def _normalize_root_cause_status_for_review(value: Any) -> str:
    status = clean_identifier(
        value,
        default=P7_HOLD004_RECEIVED_ROOT_CAUSE_STATUS_UNCLASSIFIED,
        max_length=120,
    ).upper()
    if status not in P7_HOLD004_ITEM_FINGERPRINT_ROOT_CAUSE_REVIEW_ALLOWED_STATUSES:
        return P7_HOLD004_RECEIVED_ROOT_CAUSE_STATUS_UNCLASSIFIED
    return status


def _normalize_test_semantics_review_outcome(value: Any) -> str:
    outcome = clean_identifier(
        value,
        default=P7_HOLD004_RECEIVED_TEST_SEMANTICS_REVIEW_OUTCOME_NOT_REVIEWED,
        max_length=120,
    ).upper()
    if outcome not in P7_HOLD004_TEST_SEMANTICS_REVIEW_ALLOWED_OUTCOMES:
        return P7_HOLD004_RECEIVED_TEST_SEMANTICS_REVIEW_OUTCOME_NOT_REVIEWED
    return outcome


def _root_cause_review_evidence_conditions(
    *,
    local_repeat_collect_evidence: Mapping[str, Any],
    source_identity_decision: Mapping[str, Any],
    parser_mismatch_evidence_present: bool,
    fingerprint_algorithm_mismatch_present: bool,
    environment_cause_claimed: bool,
    implementation_regression_claimed: bool,
    semantic_no_change_claimed: bool,
) -> dict[str, bool]:
    expected = safe_mapping(local_repeat_collect_evidence.get("expected"))
    return {
        "repeat_collect_stable": local_repeat_collect_evidence.get("satisfied") is True,
        "source_identity_accepted": source_identity_decision.get("source_identity_accepted") is True,
        "file_count_match": P7_HOLD004_BACKEND_COLLECTED_TEST_FILE_COUNT == P7_HOLD004_RECEIVED_COLLECTED_TEST_FILE_COUNT,
        "item_count_match": P7_HOLD004_BACKEND_COLLECTED_TEST_ITEM_COUNT == P7_HOLD004_RECEIVED_COLLECTED_TEST_ITEM_COUNT,
        "counts_match": (
            P7_HOLD004_BACKEND_COLLECTED_TEST_FILE_COUNT == P7_HOLD004_RECEIVED_COLLECTED_TEST_FILE_COUNT
            and P7_HOLD004_BACKEND_COLLECTED_TEST_ITEM_COUNT == P7_HOLD004_RECEIVED_COLLECTED_TEST_ITEM_COUNT
        ),
        "warning_count_match": P7_HOLD004_BACKEND_COLLECT_WARNINGS_COUNT == P7_HOLD004_RECEIVED_COLLECT_WARNINGS_COUNT,
        "test_files_fingerprint_match": (
            P7_HOLD004_ACTIVE_TEST_FILES_FINGERPRINT_SHA256_AT_RECEIPT
            == P7_HOLD004_RECEIVED_TEST_FILES_FINGERPRINT_SHA256
        ),
        "test_items_fingerprint_diff_recorded": (
            P7_HOLD004_ACTIVE_TEST_ITEMS_FINGERPRINT_SHA256_AT_RECEIPT
            != P7_HOLD004_RECEIVED_TEST_ITEMS_FINGERPRINT_SHA256
        ),
        "received_item_fingerprint_matches_local_repeat_collect": (
            expected.get("test_items_fingerprint_sha256") == P7_HOLD004_RECEIVED_TEST_ITEMS_FINGERPRINT_SHA256
        ),
        "received_file_fingerprint_matches_local_repeat_collect": (
            expected.get("test_files_fingerprint_sha256") == P7_HOLD004_RECEIVED_TEST_FILES_FINGERPRINT_SHA256
        ),
        "fingerprint_algorithm_match": (
            expected.get("fingerprint_algorithm") == P7_HOLD004_BACKEND_COLLECT_FINGERPRINT_ALGORITHM
            and not fingerprint_algorithm_mismatch_present
        ),
        "parser_mismatch_absent": parser_mismatch_evidence_present is False,
        "environment_cause_not_claimed": environment_cause_claimed is False,
        "implementation_regression_not_claimed": implementation_regression_claimed is False,
        "semantic_no_change_not_claimed_in_r32": semantic_no_change_claimed is False,
        "same_baseline_id_hash_replacement_blocked": True,
        "previous_active_baseline_retained": True,
    }


def build_p7_hold004_local_repeat_collect_evidence(
    *,
    observed_collect_runs: Iterable[Mapping[str, Any]] | None = None,
    collect_run_count: Any = P7_HOLD004_MINIMUM_REPEAT_COLLECT_RUN_COUNT,
    run_1_matches_expected: Any = True,
    run_2_matches_expected: Any = True,
    counts_warnings_fingerprints_stable: Any = True,
    received_collect_matches_recorded_default: Any = True,
    canonical_received_snapshot_ref: Any = P7_HOLD004_RECEIVED_ZIP_REF,
    local_attachment_ref_observed: Any = P7_HOLD004_LOCAL_ATTACHMENT_REF_OBSERVED,
    local_attachment_promoted_to_source_snapshot_ref: Any = False,
) -> dict[str, Any]:
    """Build R30 local repeat collect evidence without retaining pytest bodies."""

    canonical_ref = clean_identifier(canonical_received_snapshot_ref, default=P7_HOLD004_RECEIVED_ZIP_REF, max_length=160)
    local_ref = clean_identifier(local_attachment_ref_observed, default=P7_HOLD004_LOCAL_ATTACHMENT_REF_OBSERVED, max_length=160)
    promoted = _coerce_bool(local_attachment_promoted_to_source_snapshot_ref)
    requested_run_count = _coerce_non_negative_int(collect_run_count)
    observed_runs = _build_observed_runs(observed_collect_runs, collect_run_count=requested_run_count)
    run_count = len(observed_runs) if observed_collect_runs is not None else requested_run_count
    run_1_match = bool(
        _coerce_bool(run_1_matches_expected)
        and len(observed_runs) >= 1
        and observed_runs[0].get("matches_expected") is True
    )
    run_2_match = bool(
        _coerce_bool(run_2_matches_expected)
        and len(observed_runs) >= 2
        and observed_runs[1].get("matches_expected") is True
    )
    stable = bool(_coerce_bool(counts_warnings_fingerprints_stable) and _observed_runs_stable(observed_runs))
    default_match = bool(
        _coerce_bool(received_collect_matches_recorded_default)
        and all(safe_mapping(run).get("matches_expected") is True for run in observed_runs)
    )
    observed = {
        "collect_run_count": run_count,
        "minimum_collect_run_count": P7_HOLD004_MINIMUM_REPEAT_COLLECT_RUN_COUNT,
        "runs": observed_runs,
        "all_runs_match_expected": all(safe_mapping(run).get("matches_expected") is True for run in observed_runs),
        "run_1_matches_expected": run_1_match,
        "run_2_matches_expected": run_2_match,
        "counts_warnings_fingerprints_stable": stable,
        "received_collect_matches_recorded_default": default_match,
    }
    conditions_satisfied = bool(
        run_count >= P7_HOLD004_MINIMUM_REPEAT_COLLECT_RUN_COUNT
        and observed["run_1_matches_expected"]
        and observed["run_2_matches_expected"]
        and observed["counts_warnings_fingerprints_stable"]
        and observed["received_collect_matches_recorded_default"]
        and canonical_ref == P7_HOLD004_RECEIVED_ZIP_REF
        and local_ref == P7_HOLD004_LOCAL_ATTACHMENT_REF_OBSERVED
        and promoted is False
    )
    material = {
        "schema_version": P7_HOLD004_LOCAL_REPEAT_COLLECT_EVIDENCE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_HOLD004_LOCAL_REPEAT_COLLECT_EVIDENCE_STEP,
        "implementation_step": P7_HOLD004_LOCAL_REPEAT_COLLECT_EVIDENCE_STEP,
        "hold_id": P7_HOLD004_BACKEND_SUITE_HOLD_ID,
        "evidence_id": P7_HOLD004_LOCAL_REPEAT_COLLECT_EVIDENCE_ID,
        "source_mode": P7_SOURCE_MODE,
        "git_checked": P7_GIT_CHECKED,
        "canonical_received_snapshot_ref": canonical_ref,
        "local_attachment_ref_observed": local_ref,
        "local_attachment_promoted_to_source_snapshot_ref": promoted,
        "collect_scope": P7_HOLD004_FULL_BACKEND_COLLECT_ONLY_SCOPE,
        "collect_run_count": run_count,
        "repeat_collect_run_count": run_count,
        "minimum_collect_run_count": P7_HOLD004_MINIMUM_REPEAT_COLLECT_RUN_COUNT,
        "expected": _expected_collect_summary(),
        "expected_collect": _expected_collect_summary(),
        "observed": observed,
        "observed_collect_runs": observed_runs,
        "counts_warnings_fingerprints_stable": observed["counts_warnings_fingerprints_stable"],
        "received_collect_matches_recorded_default": observed["received_collect_matches_recorded_default"],
        "satisfied": conditions_satisfied,
        "repeat_collect_evidence_satisfied": conditions_satisfied,
        "collect_only_is_not_execution_green": True,
        "execution_green_confirmed": False,
        **_body_retention_flags(),
        **_capture_closed_boundary(),
        **_release_closed_boundary(),
        "implementation_scope": dict(_IMPLEMENTATION_SCOPE_FLAGS),
        "unresolved_hold_refs": [P7_HOLD004_BACKEND_SUITE_HOLD_ID],
        "required_followup_fixes": list(_R30_REQUIRED_FOLLOWUP_FIXES),
        "public_contract": _public_contract_boundary_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_hold004_local_repeat_collect_evidence_contract(material)
    return material


def assert_p7_hold004_local_repeat_collect_evidence_contract(material: Mapping[str, Any]) -> bool:
    """Validate R30 local repeat collect evidence."""

    data = safe_mapping(material)
    source = "p7_hold004_local_repeat_collect_evidence"
    if data.get("schema_version") != P7_HOLD004_LOCAL_REPEAT_COLLECT_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("P7-HOLD-004 R30 schema_version mismatch")
    if data.get("implementation_step") != P7_HOLD004_LOCAL_REPEAT_COLLECT_EVIDENCE_STEP:
        raise ValueError("P7-HOLD-004 R30 implementation_step mismatch")
    if data.get("evidence_id") != P7_HOLD004_LOCAL_REPEAT_COLLECT_EVIDENCE_ID:
        raise ValueError("P7-HOLD-004 R30 evidence id mismatch")
    _assert_common_closed_body_free(data, source=source)
    _implementation_scope_contract(safe_mapping(data.get("implementation_scope")), source=source)
    if data.get("canonical_received_snapshot_ref") != P7_HOLD004_RECEIVED_ZIP_REF:
        raise ValueError("P7-HOLD-004 R30 canonical received ref mismatch")
    if data.get("local_attachment_ref_observed") != P7_HOLD004_LOCAL_ATTACHMENT_REF_OBSERVED:
        raise ValueError("P7-HOLD-004 R30 local attachment alias mismatch")
    if data.get("local_attachment_promoted_to_source_snapshot_ref") is not False:
        raise ValueError("P7-HOLD-004 R30 must not promote local attachment alias")
    if data.get("collect_scope") != P7_HOLD004_FULL_BACKEND_COLLECT_ONLY_SCOPE:
        raise ValueError("P7-HOLD-004 R30 collect scope mismatch")
    expected = safe_mapping(data.get("expected"))
    if not _expected_summary_matches_constants(expected):
        raise ValueError("P7-HOLD-004 R30 expected collect summary mismatch")
    expected_collect = safe_mapping(data.get("expected_collect"))
    if expected_collect and expected_collect != expected:
        raise ValueError("P7-HOLD-004 R30 expected_collect must mirror expected")
    if not _is_sha256_hex(expected.get("test_items_fingerprint_sha256")):
        raise ValueError("P7-HOLD-004 R30 item fingerprint must be sha256 hex")
    if not _is_sha256_hex(expected.get("test_files_fingerprint_sha256")):
        raise ValueError("P7-HOLD-004 R30 file fingerprint must be sha256 hex")
    observed = safe_mapping(data.get("observed"))
    observed_runs = data.get("observed_collect_runs")
    if not isinstance(observed_runs, list):
        raise ValueError("P7-HOLD-004 R30 observed_collect_runs must be a list")
    if observed.get("runs") != observed_runs:
        raise ValueError("P7-HOLD-004 R30 observed.runs must mirror observed_collect_runs")
    if observed.get("collect_run_count") != data.get("collect_run_count"):
        raise ValueError("P7-HOLD-004 R30 observed collect count mirror mismatch")
    if observed.get("minimum_collect_run_count") != P7_HOLD004_MINIMUM_REPEAT_COLLECT_RUN_COUNT:
        raise ValueError("P7-HOLD-004 R30 observed minimum count mismatch")
    for index, run_value in enumerate(observed_runs, start=1):
        run = safe_mapping(run_value)
        if not run:
            raise ValueError(f"P7-HOLD-004 R30 observed run {index} must be a mapping")
        for key in _BODY_RETENTION_KEYS:
            if run.get(key) is not False:
                raise ValueError(f"P7-HOLD-004 R30 observed run {index} must keep {key}=false")
        if run.get("body_free") is not True:
            raise ValueError(f"P7-HOLD-004 R30 observed run {index} must be body_free")
        matches_expected = _collect_run_matches_expected(run)
        if run.get("matches_expected") is not matches_expected:
            raise ValueError(f"P7-HOLD-004 R30 observed run {index} match flag mismatch")
        if run.get("matches_expected_collect") is not matches_expected:
            raise ValueError(f"P7-HOLD-004 R30 observed run {index} collect match flag mismatch")
    if observed.get("run_1_matches_expected") is not bool(
        len(observed_runs) >= 1 and safe_mapping(observed_runs[0]).get("matches_expected") is True
    ):
        raise ValueError("P7-HOLD-004 R30 run_1 match mirror mismatch")
    if observed.get("run_2_matches_expected") is not bool(
        len(observed_runs) >= 2 and safe_mapping(observed_runs[1]).get("matches_expected") is True
    ):
        raise ValueError("P7-HOLD-004 R30 run_2 match mirror mismatch")
    if observed.get("all_runs_match_expected") is not all(
        safe_mapping(run).get("matches_expected") is True for run in observed_runs
    ):
        raise ValueError("P7-HOLD-004 R30 all-runs match mirror mismatch")
    if observed.get("counts_warnings_fingerprints_stable") is not _observed_runs_stable(
        [safe_mapping(run) for run in observed_runs]
    ):
        raise ValueError("P7-HOLD-004 R30 stable run mirror mismatch")

    conditions_satisfied = bool(
        _coerce_non_negative_int(data.get("collect_run_count")) >= P7_HOLD004_MINIMUM_REPEAT_COLLECT_RUN_COUNT
        and observed.get("run_1_matches_expected") is True
        and observed.get("run_2_matches_expected") is True
        and observed.get("counts_warnings_fingerprints_stable") is True
        and observed.get("received_collect_matches_recorded_default") is True
        and data.get("canonical_received_snapshot_ref") == P7_HOLD004_RECEIVED_ZIP_REF
        and data.get("local_attachment_ref_observed") == P7_HOLD004_LOCAL_ATTACHMENT_REF_OBSERVED
        and data.get("local_attachment_promoted_to_source_snapshot_ref") is False
    )
    if data.get("repeat_collect_run_count") != data.get("collect_run_count"):
        raise ValueError("P7-HOLD-004 R30 repeat collect count mismatch")
    if data.get("repeat_collect_run_count") != data.get("collect_run_count"):
        raise ValueError("P7-HOLD-004 R30 repeat collect count mismatch")
    if data.get("minimum_collect_run_count") != P7_HOLD004_MINIMUM_REPEAT_COLLECT_RUN_COUNT:
        raise ValueError("P7-HOLD-004 R30 minimum run count mismatch")
    if data.get("satisfied") is not conditions_satisfied:
        raise ValueError("P7-HOLD-004 R30 satisfied flag must mirror repeat collect conditions")
    if data.get("repeat_collect_evidence_satisfied") is not conditions_satisfied:
        raise ValueError("P7-HOLD-004 R30 repeat evidence flag must mirror repeat collect conditions")
    if data.get("counts_warnings_fingerprints_stable") is not observed.get("counts_warnings_fingerprints_stable"):
        raise ValueError("P7-HOLD-004 R30 stability mirror mismatch")
    if data.get("received_collect_matches_recorded_default") is not observed.get("received_collect_matches_recorded_default"):
        raise ValueError("P7-HOLD-004 R30 default match mirror mismatch")
    if data.get("collect_only_is_not_execution_green") is not True:
        raise ValueError("P7-HOLD-004 R30 collect-only boundary missing")
    if data.get("execution_green_confirmed") is not False:
        raise ValueError("P7-HOLD-004 R30 must not claim execution green")
    if P7_HOLD004_BACKEND_SUITE_HOLD_ID not in dedupe_identifiers(data.get("unresolved_hold_refs")):
        raise ValueError("P7-HOLD-004 R30 must keep HOLD-004 unresolved")
    return True


def _source_identity_status(
    *,
    active_source_snapshot_ref_at_receipt: str,
    canonical_received_snapshot_ref: str,
    local_attachment_ref_observed: str,
    candidate_source_snapshot_ref: str,
    local_attachment_promoted_to_source_snapshot_ref: bool,
    received_zip_promoted_to_source_snapshot_ref_before_adoption: bool,
) -> str:
    if local_attachment_promoted_to_source_snapshot_ref or candidate_source_snapshot_ref == local_attachment_ref_observed:
        return P7_HOLD004_SOURCE_IDENTITY_STATUS_BLOCKED_LOCAL_ATTACHMENT_PROMOTED
    if canonical_received_snapshot_ref != P7_HOLD004_RECEIVED_ZIP_REF:
        return P7_HOLD004_SOURCE_IDENTITY_STATUS_BLOCKED_CANONICAL_REF_MISMATCH
    if candidate_source_snapshot_ref != P7_HOLD004_RECEIVED_ZIP_REF:
        return P7_HOLD004_SOURCE_IDENTITY_STATUS_BLOCKED_SOURCE_IDENTITY_UNCLEAR
    if active_source_snapshot_ref_at_receipt != P7_HOLD004_ACTIVE_SOURCE_SNAPSHOT_REF_AT_RECEIPT:
        return P7_HOLD004_SOURCE_IDENTITY_STATUS_BLOCKED_SOURCE_IDENTITY_UNCLEAR
    if received_zip_promoted_to_source_snapshot_ref_before_adoption:
        return P7_HOLD004_SOURCE_IDENTITY_STATUS_BLOCKED_SOURCE_IDENTITY_UNCLEAR
    return P7_HOLD004_SOURCE_IDENTITY_STATUS_RECEIVED_REF_ACCEPTED_ATTACHMENT_ALIAS_NOT_PROMOTED


def build_p7_hold004_source_identity_decision(
    *,
    local_repeat_collect_evidence: Mapping[str, Any] | None = None,
    active_source_snapshot_ref_at_receipt: Any = P7_HOLD004_ACTIVE_SOURCE_SNAPSHOT_REF_AT_RECEIPT,
    canonical_received_snapshot_ref: Any = P7_HOLD004_RECEIVED_ZIP_REF,
    local_attachment_ref_observed: Any = P7_HOLD004_LOCAL_ATTACHMENT_REF_OBSERVED,
    candidate_source_snapshot_ref: Any = P7_HOLD004_RECEIVED_ZIP_REF,
    local_attachment_promoted_to_source_snapshot_ref: Any = False,
    received_zip_promoted_to_source_snapshot_ref_before_adoption: Any = False,
) -> dict[str, Any]:
    """Build R31 source identity decision boundary material."""

    evidence = safe_mapping(local_repeat_collect_evidence) if local_repeat_collect_evidence is not None else build_p7_hold004_local_repeat_collect_evidence()
    assert_p7_hold004_local_repeat_collect_evidence_contract(evidence)
    active_ref = clean_identifier(active_source_snapshot_ref_at_receipt, default=P7_HOLD004_ACTIVE_SOURCE_SNAPSHOT_REF_AT_RECEIPT, max_length=160)
    canonical_ref = clean_identifier(canonical_received_snapshot_ref, default=P7_HOLD004_RECEIVED_ZIP_REF, max_length=160)
    local_ref = clean_identifier(local_attachment_ref_observed, default=P7_HOLD004_LOCAL_ATTACHMENT_REF_OBSERVED, max_length=160)
    candidate_ref = clean_identifier(candidate_source_snapshot_ref, default=P7_HOLD004_RECEIVED_ZIP_REF, max_length=160)
    local_promoted = _coerce_bool(local_attachment_promoted_to_source_snapshot_ref)
    received_promoted = _coerce_bool(received_zip_promoted_to_source_snapshot_ref_before_adoption)
    status = _source_identity_status(
        active_source_snapshot_ref_at_receipt=active_ref,
        canonical_received_snapshot_ref=canonical_ref,
        local_attachment_ref_observed=local_ref,
        candidate_source_snapshot_ref=candidate_ref,
        local_attachment_promoted_to_source_snapshot_ref=local_promoted,
        received_zip_promoted_to_source_snapshot_ref_before_adoption=received_promoted,
    )
    accepted = bool(
        status == P7_HOLD004_SOURCE_IDENTITY_STATUS_RECEIVED_REF_ACCEPTED_ATTACHMENT_ALIAS_NOT_PROMOTED
        and evidence.get("satisfied") is True
    )
    material = {
        "schema_version": P7_HOLD004_SOURCE_IDENTITY_DECISION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_HOLD004_SOURCE_IDENTITY_DECISION_STEP,
        "implementation_step": P7_HOLD004_SOURCE_IDENTITY_DECISION_STEP,
        "hold_id": P7_HOLD004_BACKEND_SUITE_HOLD_ID,
        "decision_id": P7_HOLD004_SOURCE_IDENTITY_DECISION_ID,
        "local_repeat_collect_evidence_id": clean_identifier(evidence.get("evidence_id"), default=P7_HOLD004_LOCAL_REPEAT_COLLECT_EVIDENCE_ID, max_length=160),
        "local_repeat_collect_evidence_satisfied": evidence.get("satisfied") is True,
        "received_reconcile_id": P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_ID,
        "source_mode": P7_SOURCE_MODE,
        "git_checked": P7_GIT_CHECKED,
        "active_baseline_id_at_receipt": P7_HOLD004_ACTIVE_BASELINE_ID_AT_RECEIPT,
        "active_source_snapshot_ref_at_receipt": active_ref,
        "canonical_received_snapshot_ref": canonical_ref,
        "received_zip_ref_in_material": P7_HOLD004_RECEIVED_ZIP_REF,
        "local_attachment_ref_observed": local_ref,
        "candidate_source_snapshot_ref": candidate_ref,
        "candidate_active_baseline_id": P7_HOLD004_RECEIVED_SNAPSHOT_CANDIDATE_NEW_BASELINE_ID,
        "source_identity_status": status,
        "source_identity_decision_recorded": True,
        "source_identity_accepted": accepted,
        "active_source_snapshot_ref_is_not_received_ref_at_receipt": active_ref != canonical_ref,
        "local_attachment_promoted_to_source_snapshot_ref": local_promoted,
        "received_zip_promoted_to_source_snapshot_ref_before_adoption": received_promoted,
        "received_zip_promoted_to_source_snapshot_ref": False,
        "source_snapshot_ref_update_allowed_by_identity": accepted,
        "source_snapshot_ref_update_allowed": False,
        "source_snapshot_ref_update_allowed_before_adoption": False,
        "candidate_new_baseline_id": P7_HOLD004_RECEIVED_SNAPSHOT_CANDIDATE_NEW_BASELINE_ID,
        "satisfied": accepted,
        "source_identity_decision_satisfied": accepted,
        "adoption_evidence_bundle_not_built_in_r31": True,
        "same_baseline_id_hash_replacement_allowed": False,
        "previous_active_baseline_retained": True,
        **_body_retention_flags(),
        **_capture_closed_boundary(),
        **_release_closed_boundary(),
        "implementation_scope": dict(_IMPLEMENTATION_SCOPE_FLAGS),
        "unresolved_hold_refs": [P7_HOLD004_BACKEND_SUITE_HOLD_ID],
        "required_followup_fixes": list(_R31_REQUIRED_FOLLOWUP_FIXES),
        "public_contract": _public_contract_boundary_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_hold004_source_identity_decision_contract(material)
    return material


def assert_p7_hold004_source_identity_decision_contract(material: Mapping[str, Any]) -> bool:
    """Validate R31 source identity decision boundary material."""

    data = safe_mapping(material)
    source = "p7_hold004_source_identity_decision"
    if data.get("schema_version") != P7_HOLD004_SOURCE_IDENTITY_DECISION_SCHEMA_VERSION:
        raise ValueError("P7-HOLD-004 R31 schema_version mismatch")
    if data.get("implementation_step") != P7_HOLD004_SOURCE_IDENTITY_DECISION_STEP:
        raise ValueError("P7-HOLD-004 R31 implementation_step mismatch")
    if data.get("decision_id") != P7_HOLD004_SOURCE_IDENTITY_DECISION_ID:
        raise ValueError("P7-HOLD-004 R31 decision id mismatch")
    _assert_common_closed_body_free(data, source=source)
    _implementation_scope_contract(safe_mapping(data.get("implementation_scope")), source=source)
    if data.get("local_repeat_collect_evidence_id") != P7_HOLD004_LOCAL_REPEAT_COLLECT_EVIDENCE_ID:
        raise ValueError("P7-HOLD-004 R31 R30 evidence id mismatch")
    if data.get("local_repeat_collect_evidence_satisfied") is not True:
        raise ValueError("P7-HOLD-004 R31 requires satisfied R30 evidence")
    if data.get("received_reconcile_id") != P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_ID:
        raise ValueError("P7-HOLD-004 R31 received reconcile id mismatch")
    if data.get("active_baseline_id_at_receipt") != P7_HOLD004_ACTIVE_BASELINE_ID_AT_RECEIPT:
        raise ValueError("P7-HOLD-004 R31 active baseline id mismatch")
    if data.get("active_source_snapshot_ref_at_receipt") != P7_HOLD004_ACTIVE_SOURCE_SNAPSHOT_REF_AT_RECEIPT:
        raise ValueError("P7-HOLD-004 R31 active source ref mismatch")
    if data.get("canonical_received_snapshot_ref") != P7_HOLD004_RECEIVED_ZIP_REF:
        raise ValueError("P7-HOLD-004 R31 canonical received ref mismatch")
    if data.get("local_attachment_ref_observed") != P7_HOLD004_LOCAL_ATTACHMENT_REF_OBSERVED:
        raise ValueError("P7-HOLD-004 R31 local attachment alias mismatch")
    if data.get("candidate_source_snapshot_ref") != P7_HOLD004_RECEIVED_ZIP_REF:
        raise ValueError("P7-HOLD-004 R31 candidate source ref must be canonical received ref")
    if data.get("candidate_source_snapshot_ref") == P7_HOLD004_LOCAL_ATTACHMENT_REF_OBSERVED:
        raise ValueError("P7-HOLD-004 R31 must not use local attachment alias as source ref")
    if data.get("candidate_active_baseline_id") != P7_HOLD004_RECEIVED_SNAPSHOT_CANDIDATE_NEW_BASELINE_ID:
        raise ValueError("P7-HOLD-004 R31 candidate baseline id mismatch")
    if data.get("candidate_new_baseline_id") not in {None, P7_HOLD004_RECEIVED_SNAPSHOT_CANDIDATE_NEW_BASELINE_ID}:
        raise ValueError("P7-HOLD-004 R31 candidate new baseline id mismatch")
    status = clean_identifier(data.get("source_identity_status"), max_length=160)
    if status not in P7_HOLD004_SOURCE_IDENTITY_STATUSES:
        raise ValueError("P7-HOLD-004 R31 source identity status unrecognized")
    accepted_conditions = bool(
        status == P7_HOLD004_SOURCE_IDENTITY_STATUS_RECEIVED_REF_ACCEPTED_ATTACHMENT_ALIAS_NOT_PROMOTED
        and data.get("local_repeat_collect_evidence_satisfied") is True
        and data.get("source_identity_decision_recorded") is True
        and data.get("canonical_received_snapshot_ref") == P7_HOLD004_RECEIVED_ZIP_REF
        and data.get("candidate_source_snapshot_ref") == P7_HOLD004_RECEIVED_ZIP_REF
        and data.get("local_attachment_ref_observed") == P7_HOLD004_LOCAL_ATTACHMENT_REF_OBSERVED
        and data.get("active_source_snapshot_ref_at_receipt") == P7_HOLD004_ACTIVE_SOURCE_SNAPSHOT_REF_AT_RECEIPT
        and data.get("local_attachment_promoted_to_source_snapshot_ref") is False
        and data.get("received_zip_promoted_to_source_snapshot_ref_before_adoption") is False
        and data.get("received_zip_promoted_to_source_snapshot_ref") is False
        and data.get("active_source_snapshot_ref_is_not_received_ref_at_receipt") is True
    )
    if data.get("source_identity_accepted") is not accepted_conditions:
        raise ValueError("P7-HOLD-004 R31 source_identity_accepted mirror mismatch")
    if data.get("source_snapshot_ref_update_allowed_by_identity") is not accepted_conditions:
        raise ValueError("P7-HOLD-004 R31 source ref update boundary mirror mismatch")
    if data.get("satisfied") is not accepted_conditions:
        raise ValueError("P7-HOLD-004 R31 satisfied mirror mismatch")
    if data.get("source_identity_decision_satisfied") is not accepted_conditions:
        raise ValueError("P7-HOLD-004 R31 decision satisfied mirror mismatch")
    if data.get("adoption_evidence_bundle_not_built_in_r31") is not True:
        raise ValueError("P7-HOLD-004 R31 must not build adoption bundle")
    for key in (
        "local_attachment_promoted_to_source_snapshot_ref",
        "received_zip_promoted_to_source_snapshot_ref_before_adoption",
        "received_zip_promoted_to_source_snapshot_ref",
        "source_snapshot_ref_update_allowed",
        "source_snapshot_ref_update_allowed_before_adoption",
        "same_baseline_id_hash_replacement_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-HOLD-004 R31 must keep {key}=false")
    if data.get("previous_active_baseline_retained") is not True:
        raise ValueError("P7-HOLD-004 R31 must retain previous active baseline")
    if data.get("active_source_snapshot_ref_at_receipt") == data.get("canonical_received_snapshot_ref"):
        raise ValueError("P7-HOLD-004 R31 active source at receipt must differ from received ref")
    if P7_HOLD004_BACKEND_SUITE_HOLD_ID not in dedupe_identifiers(data.get("unresolved_hold_refs")):
        raise ValueError("P7-HOLD-004 R31 must keep HOLD-004 unresolved")
    return True


def build_p7_hold004_item_fingerprint_root_cause_review(
    *,
    local_repeat_collect_evidence: Mapping[str, Any] | None = None,
    source_identity_decision: Mapping[str, Any] | None = None,
    root_cause_status: Any = P7_HOLD004_ROOT_CAUSE_STATUS_BASELINE_CONSTANT_STALE,
    root_cause_review_recorded: Any = True,
    parser_mismatch_evidence_present: Any = False,
    fingerprint_algorithm_mismatch_present: Any = False,
    environment_cause_claimed: Any = False,
    implementation_regression_claimed: Any = False,
    semantic_no_change_claimed: Any = False,
) -> dict[str, Any]:
    """Build R32 root-cause review material for the received item hash diff."""

    evidence = (
        safe_mapping(local_repeat_collect_evidence)
        if local_repeat_collect_evidence is not None
        else build_p7_hold004_local_repeat_collect_evidence()
    )
    assert_p7_hold004_local_repeat_collect_evidence_contract(evidence)
    source_identity = (
        safe_mapping(source_identity_decision)
        if source_identity_decision is not None
        else build_p7_hold004_source_identity_decision(local_repeat_collect_evidence=evidence)
    )
    assert_p7_hold004_source_identity_decision_contract(source_identity)

    normalized_root_cause = _normalize_root_cause_status_for_review(root_cause_status)
    review_recorded = _coerce_bool(root_cause_review_recorded)
    parser_mismatch_present = _coerce_bool(parser_mismatch_evidence_present)
    algorithm_mismatch_present = _coerce_bool(fingerprint_algorithm_mismatch_present)
    environment_claim = _coerce_bool(environment_cause_claimed)
    regression_claim = _coerce_bool(implementation_regression_claimed)
    no_semantic_claim = _coerce_bool(semantic_no_change_claimed)
    conditions = _root_cause_review_evidence_conditions(
        local_repeat_collect_evidence=evidence,
        source_identity_decision=source_identity,
        parser_mismatch_evidence_present=parser_mismatch_present,
        fingerprint_algorithm_mismatch_present=algorithm_mismatch_present,
        environment_cause_claimed=environment_claim,
        implementation_regression_claimed=regression_claim,
        semantic_no_change_claimed=no_semantic_claim,
    )
    root_cause_supported = bool(
        normalized_root_cause == P7_HOLD004_ROOT_CAUSE_STATUS_BASELINE_CONSTANT_STALE
        and review_recorded
        and all(conditions.values())
    )
    material = {
        "schema_version": P7_HOLD004_ITEM_FINGERPRINT_ROOT_CAUSE_REVIEW_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_HOLD004_ITEM_FINGERPRINT_ROOT_CAUSE_REVIEW_STEP,
        "implementation_step": P7_HOLD004_ITEM_FINGERPRINT_ROOT_CAUSE_REVIEW_STEP,
        "hold_id": P7_HOLD004_BACKEND_SUITE_HOLD_ID,
        "review_id": P7_HOLD004_ITEM_FINGERPRINT_ROOT_CAUSE_REVIEW_ID,
        "local_repeat_collect_evidence_id": clean_identifier(
            evidence.get("evidence_id"), default=P7_HOLD004_LOCAL_REPEAT_COLLECT_EVIDENCE_ID, max_length=160
        ),
        "local_repeat_collect_evidence_satisfied": evidence.get("satisfied") is True,
        "source_identity_decision_id": clean_identifier(
            source_identity.get("decision_id"), default=P7_HOLD004_SOURCE_IDENTITY_DECISION_ID, max_length=160
        ),
        "source_identity_decision_satisfied": source_identity.get("satisfied") is True,
        "source_identity_accepted": source_identity.get("source_identity_accepted") is True,
        "received_reconcile_id": P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_ID,
        "source_mode": P7_SOURCE_MODE,
        "git_checked": P7_GIT_CHECKED,
        "active_baseline_id_at_receipt": P7_HOLD004_ACTIVE_BASELINE_ID_AT_RECEIPT,
        "active_source_snapshot_ref_at_receipt": P7_HOLD004_ACTIVE_SOURCE_SNAPSHOT_REF_AT_RECEIPT,
        "canonical_received_snapshot_ref": P7_HOLD004_RECEIVED_ZIP_REF,
        "candidate_active_baseline_id": P7_HOLD004_RECEIVED_SNAPSHOT_CANDIDATE_NEW_BASELINE_ID,
        "candidate_source_snapshot_ref": P7_HOLD004_RECEIVED_ZIP_REF,
        "active_item_fingerprint_sha256_at_receipt": P7_HOLD004_ACTIVE_TEST_ITEMS_FINGERPRINT_SHA256_AT_RECEIPT,
        "received_item_fingerprint_sha256": P7_HOLD004_RECEIVED_TEST_ITEMS_FINGERPRINT_SHA256,
        "active_test_files_fingerprint_sha256_at_receipt": P7_HOLD004_ACTIVE_TEST_FILES_FINGERPRINT_SHA256_AT_RECEIPT,
        "received_test_files_fingerprint_sha256": P7_HOLD004_RECEIVED_TEST_FILES_FINGERPRINT_SHA256,
        "fingerprint_algorithm": P7_HOLD004_BACKEND_COLLECT_FINGERPRINT_ALGORITHM,
        "review_conditions": conditions,
        "file_fingerprint_match": conditions["test_files_fingerprint_match"],
        "counts_match": conditions["counts_match"],
        "warnings_match": conditions["warning_count_match"],
        "repeat_collect_stable": conditions["repeat_collect_stable"],
        "root_cause_status": normalized_root_cause,
        "root_cause_review_recorded": review_recorded,
        "root_cause_classified": root_cause_supported,
        "root_cause_unclassified": normalized_root_cause == P7_HOLD004_RECEIVED_ROOT_CAUSE_STATUS_UNCLASSIFIED,
        "root_cause_overclaim_absent": bool(
            conditions["parser_mismatch_absent"]
            and conditions["environment_cause_not_claimed"]
            and conditions["implementation_regression_not_claimed"]
            and conditions["semantic_no_change_not_claimed_in_r32"]
        ),
        "parser_mismatch_evidence_present": parser_mismatch_present,
        "fingerprint_algorithm_mismatch_present": algorithm_mismatch_present,
        "environment_cause_claimed": environment_claim,
        "implementation_regression_claimed": regression_claim,
        "semantic_no_change_claimed": no_semantic_claim,
        "same_baseline_id_hash_replacement_allowed": False,
        "previous_active_baseline_retained": True,
        "satisfied": root_cause_supported,
        "root_cause_review_satisfied": root_cause_supported,
        "collect_only_is_not_execution_green": True,
        "execution_green_confirmed": False,
        **_body_retention_flags(),
        **_capture_closed_boundary(),
        **_release_closed_boundary(),
        "implementation_scope": dict(_R32_IMPLEMENTATION_SCOPE_FLAGS),
        "unresolved_hold_refs": [P7_HOLD004_BACKEND_SUITE_HOLD_ID],
        "required_followup_fixes": list(_R32_REQUIRED_FOLLOWUP_FIXES),
        "public_contract": _public_contract_boundary_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_hold004_item_fingerprint_root_cause_review_contract(material)
    return material


def assert_p7_hold004_item_fingerprint_root_cause_review_contract(material: Mapping[str, Any]) -> bool:
    """Validate R32 item-fingerprint root-cause review material."""

    data = safe_mapping(material)
    source = "p7_hold004_item_fingerprint_root_cause_review"
    if data.get("schema_version") != P7_HOLD004_ITEM_FINGERPRINT_ROOT_CAUSE_REVIEW_SCHEMA_VERSION:
        raise ValueError("P7-HOLD-004 R32 schema_version mismatch")
    if data.get("implementation_step") != P7_HOLD004_ITEM_FINGERPRINT_ROOT_CAUSE_REVIEW_STEP:
        raise ValueError("P7-HOLD-004 R32 implementation_step mismatch")
    if data.get("review_id") != P7_HOLD004_ITEM_FINGERPRINT_ROOT_CAUSE_REVIEW_ID:
        raise ValueError("P7-HOLD-004 R32 review id mismatch")
    _assert_common_closed_body_free(data, source=source)
    _implementation_scope_contract_for_step(
        safe_mapping(data.get("implementation_scope")), expected=_R32_IMPLEMENTATION_SCOPE_FLAGS, source=source
    )
    if data.get("local_repeat_collect_evidence_id") != P7_HOLD004_LOCAL_REPEAT_COLLECT_EVIDENCE_ID:
        raise ValueError("P7-HOLD-004 R32 R30 evidence id mismatch")
    if data.get("local_repeat_collect_evidence_satisfied") is not True:
        raise ValueError("P7-HOLD-004 R32 requires satisfied R30 evidence")
    if data.get("source_identity_decision_id") != P7_HOLD004_SOURCE_IDENTITY_DECISION_ID:
        raise ValueError("P7-HOLD-004 R32 R31 decision id mismatch")
    if data.get("source_identity_decision_satisfied") is not True:
        raise ValueError("P7-HOLD-004 R32 requires satisfied R31 decision")
    if data.get("received_reconcile_id") != P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_ID:
        raise ValueError("P7-HOLD-004 R32 received reconcile id mismatch")
    if data.get("active_baseline_id_at_receipt") != P7_HOLD004_ACTIVE_BASELINE_ID_AT_RECEIPT:
        raise ValueError("P7-HOLD-004 R32 active baseline id mismatch")
    if data.get("active_source_snapshot_ref_at_receipt") != P7_HOLD004_ACTIVE_SOURCE_SNAPSHOT_REF_AT_RECEIPT:
        raise ValueError("P7-HOLD-004 R32 active source ref mismatch")
    if data.get("canonical_received_snapshot_ref") != P7_HOLD004_RECEIVED_ZIP_REF:
        raise ValueError("P7-HOLD-004 R32 received ref mismatch")
    if data.get("candidate_active_baseline_id") != P7_HOLD004_RECEIVED_SNAPSHOT_CANDIDATE_NEW_BASELINE_ID:
        raise ValueError("P7-HOLD-004 R32 candidate baseline id mismatch")
    if data.get("candidate_source_snapshot_ref") != P7_HOLD004_RECEIVED_ZIP_REF:
        raise ValueError("P7-HOLD-004 R32 candidate source ref mismatch")
    if data.get("active_item_fingerprint_sha256_at_receipt") != P7_HOLD004_ACTIVE_TEST_ITEMS_FINGERPRINT_SHA256_AT_RECEIPT:
        raise ValueError("P7-HOLD-004 R32 active item fingerprint mismatch")
    if data.get("received_item_fingerprint_sha256") != P7_HOLD004_RECEIVED_TEST_ITEMS_FINGERPRINT_SHA256:
        raise ValueError("P7-HOLD-004 R32 received item fingerprint mismatch")
    if data.get("active_test_files_fingerprint_sha256_at_receipt") != P7_HOLD004_ACTIVE_TEST_FILES_FINGERPRINT_SHA256_AT_RECEIPT:
        raise ValueError("P7-HOLD-004 R32 active file fingerprint mismatch")
    if data.get("received_test_files_fingerprint_sha256") != P7_HOLD004_RECEIVED_TEST_FILES_FINGERPRINT_SHA256:
        raise ValueError("P7-HOLD-004 R32 received file fingerprint mismatch")
    if data.get("fingerprint_algorithm") != P7_HOLD004_BACKEND_COLLECT_FINGERPRINT_ALGORITHM:
        raise ValueError("P7-HOLD-004 R32 fingerprint algorithm mismatch")
    status = _normalize_root_cause_status_for_review(data.get("root_cause_status"))
    if data.get("root_cause_status") != status:
        raise ValueError("P7-HOLD-004 R32 root cause status normalization mismatch")
    conditions = safe_mapping(data.get("review_conditions"))
    expected_conditions = _root_cause_review_evidence_conditions(
        local_repeat_collect_evidence=build_p7_hold004_local_repeat_collect_evidence(),
        source_identity_decision=build_p7_hold004_source_identity_decision(),
        parser_mismatch_evidence_present=data.get("parser_mismatch_evidence_present") is True,
        fingerprint_algorithm_mismatch_present=data.get("fingerprint_algorithm_mismatch_present") is True,
        environment_cause_claimed=data.get("environment_cause_claimed") is True,
        implementation_regression_claimed=data.get("implementation_regression_claimed") is True,
        semantic_no_change_claimed=data.get("semantic_no_change_claimed") is True,
    )
    if conditions != expected_conditions:
        raise ValueError("P7-HOLD-004 R32 review conditions mismatch")
    for key in (
        "parser_mismatch_evidence_present",
        "fingerprint_algorithm_mismatch_present",
        "environment_cause_claimed",
        "implementation_regression_claimed",
        "semantic_no_change_claimed",
        "same_baseline_id_hash_replacement_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-HOLD-004 R32 must keep {key}=false")
    root_supported = bool(
        status == P7_HOLD004_ROOT_CAUSE_STATUS_BASELINE_CONSTANT_STALE
        and data.get("root_cause_review_recorded") is True
        and all(conditions.values())
    )
    if data.get("root_cause_status") == P7_HOLD004_RECEIVED_ROOT_CAUSE_STATUS_UNCLASSIFIED and data.get("satisfied") is True:
        raise ValueError("P7-HOLD-004 R32 cannot satisfy UNCLASSIFIED root cause")
    if data.get("root_cause_status") != P7_HOLD004_ROOT_CAUSE_STATUS_BASELINE_CONSTANT_STALE and data.get("satisfied") is True:
        raise ValueError("P7-HOLD-004 R32 only BASELINE_CONSTANT_STALE is supported by this evidence")
    if data.get("satisfied") is not root_supported:
        raise ValueError("P7-HOLD-004 R32 satisfied mirror mismatch")
    if data.get("root_cause_review_satisfied") is not root_supported:
        raise ValueError("P7-HOLD-004 R32 review satisfied mirror mismatch")
    if data.get("root_cause_classified") is not root_supported:
        raise ValueError("P7-HOLD-004 R32 classified mirror mismatch")
    if data.get("root_cause_unclassified") is not (status == P7_HOLD004_RECEIVED_ROOT_CAUSE_STATUS_UNCLASSIFIED):
        raise ValueError("P7-HOLD-004 R32 unclassified mirror mismatch")
    if data.get("root_cause_overclaim_absent") is not bool(
        conditions.get("parser_mismatch_absent")
        and conditions.get("environment_cause_not_claimed")
        and conditions.get("implementation_regression_not_claimed")
        and conditions.get("semantic_no_change_not_claimed_in_r32")
    ):
        raise ValueError("P7-HOLD-004 R32 overclaim mirror mismatch")
    if data.get("previous_active_baseline_retained") is not True:
        raise ValueError("P7-HOLD-004 R32 must retain previous active baseline")
    if data.get("collect_only_is_not_execution_green") is not True:
        raise ValueError("P7-HOLD-004 R32 collect-only boundary missing")
    if data.get("execution_green_confirmed") is not False:
        raise ValueError("P7-HOLD-004 R32 must not claim execution green")
    if P7_HOLD004_BACKEND_SUITE_HOLD_ID not in dedupe_identifiers(data.get("unresolved_hold_refs")):
        raise ValueError("P7-HOLD-004 R32 must keep HOLD-004 unresolved")
    return True


def build_p7_hold004_test_semantics_review(
    *,
    root_cause_review: Mapping[str, Any] | None = None,
    test_semantics_reviewed: Any = True,
    test_semantics_review_outcome: Any = P7_HOLD004_RECEIVED_TEST_SEMANTICS_REVIEW_OUTCOME_ACCEPTED_AS_BASELINE_REFRESH,
    old_nodeid_list_available: Any = False,
    body_free_nodeid_diff_review_available: Any = False,
    no_semantic_change_claimed: Any = False,
    nodeids_retained: Any = False,
    pytest_output_retained: Any = False,
    test_body_retained: Any = False,
) -> dict[str, Any]:
    """Build R33 test-semantics review boundary material."""

    root_review = (
        safe_mapping(root_cause_review)
        if root_cause_review is not None
        else build_p7_hold004_item_fingerprint_root_cause_review()
    )
    assert_p7_hold004_item_fingerprint_root_cause_review_contract(root_review)

    reviewed = _coerce_bool(test_semantics_reviewed)
    outcome = _normalize_test_semantics_review_outcome(test_semantics_review_outcome)
    old_nodeids_available = _coerce_bool(old_nodeid_list_available)
    diff_review_available = _coerce_bool(body_free_nodeid_diff_review_available)
    no_change_claimed = _coerce_bool(no_semantic_change_claimed) or outcome == P7_HOLD004_RECEIVED_TEST_SEMANTICS_REVIEW_OUTCOME_NO_SEMANTIC_CHANGE_DETECTED
    accepted_as_refresh = outcome == P7_HOLD004_RECEIVED_TEST_SEMANTICS_REVIEW_OUTCOME_ACCEPTED_AS_BASELINE_REFRESH
    retained_nodeids = _coerce_bool(nodeids_retained)
    retained_pytest_output = _coerce_bool(pytest_output_retained)
    retained_test_body = _coerce_bool(test_body_retained)
    no_change_supported = bool(
        outcome == P7_HOLD004_RECEIVED_TEST_SEMANTICS_REVIEW_OUTCOME_NO_SEMANTIC_CHANGE_DETECTED
        and old_nodeids_available
        and diff_review_available
        and no_change_claimed
    )
    accepted_supported = bool(
        accepted_as_refresh
        and no_change_claimed is False
        and old_nodeids_available is False
        and diff_review_available is False
    )
    semantics_satisfied = bool(
        root_review.get("satisfied") is True
        and reviewed
        and not retained_nodeids
        and not retained_pytest_output
        and not retained_test_body
        and (accepted_supported or no_change_supported)
    )
    material = {
        "schema_version": P7_HOLD004_TEST_SEMANTICS_REVIEW_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_HOLD004_TEST_SEMANTICS_REVIEW_STEP,
        "implementation_step": P7_HOLD004_TEST_SEMANTICS_REVIEW_STEP,
        "hold_id": P7_HOLD004_BACKEND_SUITE_HOLD_ID,
        "review_id": P7_HOLD004_TEST_SEMANTICS_REVIEW_ID,
        "root_cause_review_id": clean_identifier(
            root_review.get("review_id"), default=P7_HOLD004_ITEM_FINGERPRINT_ROOT_CAUSE_REVIEW_ID, max_length=160
        ),
        "root_cause_review_satisfied": root_review.get("satisfied") is True,
        "root_cause_status": clean_identifier(
            root_review.get("root_cause_status"), default=P7_HOLD004_ROOT_CAUSE_STATUS_BASELINE_CONSTANT_STALE, max_length=120
        ),
        "local_repeat_collect_evidence_id": P7_HOLD004_LOCAL_REPEAT_COLLECT_EVIDENCE_ID,
        "source_identity_decision_id": P7_HOLD004_SOURCE_IDENTITY_DECISION_ID,
        "received_reconcile_id": P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_ID,
        "source_mode": P7_SOURCE_MODE,
        "git_checked": P7_GIT_CHECKED,
        "active_baseline_id_at_receipt": P7_HOLD004_ACTIVE_BASELINE_ID_AT_RECEIPT,
        "canonical_received_snapshot_ref": P7_HOLD004_RECEIVED_ZIP_REF,
        "candidate_active_baseline_id": P7_HOLD004_RECEIVED_SNAPSHOT_CANDIDATE_NEW_BASELINE_ID,
        "active_item_fingerprint_sha256_at_receipt": P7_HOLD004_ACTIVE_TEST_ITEMS_FINGERPRINT_SHA256_AT_RECEIPT,
        "received_item_fingerprint_sha256": P7_HOLD004_RECEIVED_TEST_ITEMS_FINGERPRINT_SHA256,
        "test_semantics_reviewed": reviewed,
        "test_semantics_review_outcome": outcome,
        "preferred_outcome": P7_HOLD004_RECEIVED_TEST_SEMANTICS_REVIEW_OUTCOME_ACCEPTED_AS_BASELINE_REFRESH,
        "optional_outcome_if_body_free_old_nodeid_review_exists": (
            P7_HOLD004_RECEIVED_TEST_SEMANTICS_REVIEW_OUTCOME_NO_SEMANTIC_CHANGE_DETECTED
        ),
        "old_nodeid_list_available": old_nodeids_available,
        "body_free_nodeid_diff_review_available": diff_review_available,
        "no_semantic_change_claimed": no_change_claimed,
        "accepted_as_baseline_refresh": accepted_as_refresh,
        "no_semantic_change_supported": no_change_supported,
        "accepted_as_baseline_refresh_supported": accepted_supported,
        "review_boundary_reason_codes": [
            "old_active_nodeid_list_not_available_in_body_free_material"
            if not old_nodeids_available
            else "old_active_nodeid_list_body_free_review_available",
            "nodeid_list_not_retained",
            "pytest_output_not_retained",
            "test_body_not_retained",
            "semantic_no_change_not_claimed_without_old_nodeid_review"
            if not no_change_supported
            else "semantic_no_change_supported_by_body_free_old_nodeid_review",
            "item_fingerprint_diff_accepted_as_baseline_refresh_candidate"
            if accepted_supported
            else "item_fingerprint_diff_not_accepted_as_refresh_candidate",
        ],
        "satisfied": semantics_satisfied,
        "test_semantics_review_satisfied": semantics_satisfied,
        "adoption_evidence_bundle_not_built_in_r33": True,
        "collect_only_is_not_execution_green": True,
        "execution_green_confirmed": False,
        "nodeids_retained": retained_nodeids,
        "pytest_output_retained": retained_pytest_output,
        "terminal_output_retained": False,
        "stdout_retained": False,
        "stderr_retained": False,
        "raw_traceback_included": False,
        "test_body_retained": retained_test_body,
        **_capture_closed_boundary(),
        **_release_closed_boundary(),
        "implementation_scope": dict(_R33_IMPLEMENTATION_SCOPE_FLAGS),
        "unresolved_hold_refs": [P7_HOLD004_BACKEND_SUITE_HOLD_ID],
        "required_followup_fixes": list(_R33_REQUIRED_FOLLOWUP_FIXES),
        "public_contract": _public_contract_boundary_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_hold004_test_semantics_review_contract(material)
    return material


def assert_p7_hold004_test_semantics_review_contract(material: Mapping[str, Any]) -> bool:
    """Validate R33 test-semantics review boundary material."""

    data = safe_mapping(material)
    source = "p7_hold004_test_semantics_review"
    if data.get("schema_version") != P7_HOLD004_TEST_SEMANTICS_REVIEW_SCHEMA_VERSION:
        raise ValueError("P7-HOLD-004 R33 schema_version mismatch")
    if data.get("implementation_step") != P7_HOLD004_TEST_SEMANTICS_REVIEW_STEP:
        raise ValueError("P7-HOLD-004 R33 implementation_step mismatch")
    if data.get("review_id") != P7_HOLD004_TEST_SEMANTICS_REVIEW_ID:
        raise ValueError("P7-HOLD-004 R33 review id mismatch")
    _assert_common_closed_body_free(data, source=source)
    _implementation_scope_contract_for_step(
        safe_mapping(data.get("implementation_scope")), expected=_R33_IMPLEMENTATION_SCOPE_FLAGS, source=source
    )
    if data.get("root_cause_review_id") != P7_HOLD004_ITEM_FINGERPRINT_ROOT_CAUSE_REVIEW_ID:
        raise ValueError("P7-HOLD-004 R33 R32 review id mismatch")
    if data.get("root_cause_review_satisfied") is not True:
        raise ValueError("P7-HOLD-004 R33 requires satisfied R32 review")
    if data.get("root_cause_status") != P7_HOLD004_ROOT_CAUSE_STATUS_BASELINE_CONSTANT_STALE:
        raise ValueError("P7-HOLD-004 R33 root cause status mismatch")
    if data.get("local_repeat_collect_evidence_id") != P7_HOLD004_LOCAL_REPEAT_COLLECT_EVIDENCE_ID:
        raise ValueError("P7-HOLD-004 R33 R30 evidence id mismatch")
    if data.get("source_identity_decision_id") != P7_HOLD004_SOURCE_IDENTITY_DECISION_ID:
        raise ValueError("P7-HOLD-004 R33 R31 decision id mismatch")
    if data.get("received_reconcile_id") != P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_ID:
        raise ValueError("P7-HOLD-004 R33 received reconcile id mismatch")
    if data.get("active_baseline_id_at_receipt") != P7_HOLD004_ACTIVE_BASELINE_ID_AT_RECEIPT:
        raise ValueError("P7-HOLD-004 R33 active baseline id mismatch")
    if data.get("canonical_received_snapshot_ref") != P7_HOLD004_RECEIVED_ZIP_REF:
        raise ValueError("P7-HOLD-004 R33 received ref mismatch")
    if data.get("candidate_active_baseline_id") != P7_HOLD004_RECEIVED_SNAPSHOT_CANDIDATE_NEW_BASELINE_ID:
        raise ValueError("P7-HOLD-004 R33 candidate baseline id mismatch")
    if data.get("active_item_fingerprint_sha256_at_receipt") != P7_HOLD004_ACTIVE_TEST_ITEMS_FINGERPRINT_SHA256_AT_RECEIPT:
        raise ValueError("P7-HOLD-004 R33 active item fingerprint mismatch")
    if data.get("received_item_fingerprint_sha256") != P7_HOLD004_RECEIVED_TEST_ITEMS_FINGERPRINT_SHA256:
        raise ValueError("P7-HOLD-004 R33 received item fingerprint mismatch")
    outcome = _normalize_test_semantics_review_outcome(data.get("test_semantics_review_outcome"))
    if data.get("test_semantics_review_outcome") != outcome:
        raise ValueError("P7-HOLD-004 R33 outcome normalization mismatch")
    if outcome not in P7_HOLD004_TEST_SEMANTICS_REVIEW_ALLOWED_OUTCOMES:
        raise ValueError("P7-HOLD-004 R33 outcome unrecognized")
    if data.get("preferred_outcome") != P7_HOLD004_RECEIVED_TEST_SEMANTICS_REVIEW_OUTCOME_ACCEPTED_AS_BASELINE_REFRESH:
        raise ValueError("P7-HOLD-004 R33 preferred outcome mismatch")
    if data.get("optional_outcome_if_body_free_old_nodeid_review_exists") != P7_HOLD004_RECEIVED_TEST_SEMANTICS_REVIEW_OUTCOME_NO_SEMANTIC_CHANGE_DETECTED:
        raise ValueError("P7-HOLD-004 R33 optional outcome mismatch")
    if data.get("nodeids_retained") is not False or data.get("pytest_output_retained") is not False:
        raise ValueError("P7-HOLD-004 R33 must not retain nodeids or pytest output")
    if data.get("test_body_retained") is not False:
        raise ValueError("P7-HOLD-004 R33 must not retain test body")
    if data.get("adoption_evidence_bundle_not_built_in_r33") is not True:
        raise ValueError("P7-HOLD-004 R33 must not build adoption bundle")
    old_nodeids_available = data.get("old_nodeid_list_available") is True
    diff_review_available = data.get("body_free_nodeid_diff_review_available") is True
    no_change_claimed = data.get("no_semantic_change_claimed") is True
    accepted_as_refresh = outcome == P7_HOLD004_RECEIVED_TEST_SEMANTICS_REVIEW_OUTCOME_ACCEPTED_AS_BASELINE_REFRESH
    no_change_supported = bool(
        outcome == P7_HOLD004_RECEIVED_TEST_SEMANTICS_REVIEW_OUTCOME_NO_SEMANTIC_CHANGE_DETECTED
        and old_nodeids_available
        and diff_review_available
        and no_change_claimed
    )
    accepted_supported = bool(
        accepted_as_refresh
        and no_change_claimed is False
        and old_nodeids_available is False
        and diff_review_available is False
    )
    if outcome == P7_HOLD004_RECEIVED_TEST_SEMANTICS_REVIEW_OUTCOME_NOT_REVIEWED and data.get("satisfied") is True:
        raise ValueError("P7-HOLD-004 R33 cannot satisfy NOT_REVIEWED")
    if outcome == P7_HOLD004_RECEIVED_TEST_SEMANTICS_REVIEW_OUTCOME_NO_SEMANTIC_CHANGE_DETECTED and not no_change_supported:
        raise ValueError("P7-HOLD-004 R33 cannot claim no semantic change without body-free old nodeid review")
    if accepted_supported and data.get("accepted_as_baseline_refresh") is not True:
        raise ValueError("P7-HOLD-004 R33 accepted-as-refresh mirror mismatch")
    if not accepted_supported and outcome == P7_HOLD004_RECEIVED_TEST_SEMANTICS_REVIEW_OUTCOME_ACCEPTED_AS_BASELINE_REFRESH:
        raise ValueError("P7-HOLD-004 R33 accepted-as-refresh unsupported")
    if data.get("no_semantic_change_supported") is not no_change_supported:
        raise ValueError("P7-HOLD-004 R33 no-change support mirror mismatch")
    if data.get("accepted_as_baseline_refresh_supported") is not accepted_supported:
        raise ValueError("P7-HOLD-004 R33 accepted support mirror mismatch")
    semantics_supported = bool(
        data.get("root_cause_review_satisfied") is True
        and data.get("test_semantics_reviewed") is True
        and (accepted_supported or no_change_supported)
    )
    if data.get("satisfied") is not semantics_supported:
        raise ValueError("P7-HOLD-004 R33 satisfied mirror mismatch")
    if data.get("test_semantics_review_satisfied") is not semantics_supported:
        raise ValueError("P7-HOLD-004 R33 review satisfied mirror mismatch")
    if not isinstance(data.get("review_boundary_reason_codes"), list) or not data.get("review_boundary_reason_codes"):
        raise ValueError("P7-HOLD-004 R33 reason codes required")
    if data.get("collect_only_is_not_execution_green") is not True:
        raise ValueError("P7-HOLD-004 R33 collect-only boundary missing")
    if data.get("execution_green_confirmed") is not False:
        raise ValueError("P7-HOLD-004 R33 must not claim execution green")
    if P7_HOLD004_BACKEND_SUITE_HOLD_ID not in dedupe_identifiers(data.get("unresolved_hold_refs")):
        raise ValueError("P7-HOLD-004 R33 must keep HOLD-004 unresolved")
    return True


def _previous_active_baseline_material_for_adoption() -> dict[str, Any]:
    return {
        "baseline_id": P7_HOLD004_ACTIVE_BASELINE_ID_AT_RECEIPT,
        "source_snapshot_ref": P7_HOLD004_ACTIVE_SOURCE_SNAPSHOT_REF_AT_RECEIPT,
        "collected_test_file_count": P7_HOLD004_BACKEND_COLLECTED_TEST_FILE_COUNT,
        "collected_test_item_count": P7_HOLD004_BACKEND_COLLECTED_TEST_ITEM_COUNT,
        "warnings_count": P7_HOLD004_BACKEND_COLLECT_WARNINGS_COUNT,
        "test_items_fingerprint_sha256": P7_HOLD004_ACTIVE_TEST_ITEMS_FINGERPRINT_SHA256_AT_RECEIPT,
        "test_files_fingerprint_sha256": P7_HOLD004_ACTIVE_TEST_FILES_FINGERPRINT_SHA256_AT_RECEIPT,
        "fingerprint_algorithm": P7_HOLD004_BACKEND_COLLECT_FINGERPRINT_ALGORITHM,
    }


def _candidate_active_baseline_material_for_adoption() -> dict[str, Any]:
    return {
        "baseline_id": P7_HOLD004_RECEIVED_SNAPSHOT_CANDIDATE_NEW_BASELINE_ID,
        "source_snapshot_ref": P7_HOLD004_RECEIVED_ZIP_REF,
        "collected_test_file_count": P7_HOLD004_RECEIVED_COLLECTED_TEST_FILE_COUNT,
        "collected_test_item_count": P7_HOLD004_RECEIVED_COLLECTED_TEST_ITEM_COUNT,
        "warnings_count": P7_HOLD004_RECEIVED_COLLECT_WARNINGS_COUNT,
        "test_items_fingerprint_sha256": P7_HOLD004_RECEIVED_TEST_ITEMS_FINGERPRINT_SHA256,
        "test_files_fingerprint_sha256": P7_HOLD004_RECEIVED_TEST_FILES_FINGERPRINT_SHA256,
        "fingerprint_algorithm": P7_HOLD004_BACKEND_COLLECT_FINGERPRINT_ALGORITHM,
        "same_baseline_id_hash_replacement_allowed": False,
        "previous_active_baseline_retained": True,
    }


def _assert_r35_body_free_release_and_capture_boundaries(material: Mapping[str, Any], *, source: str) -> None:
    data = safe_mapping(material)
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_BACKEND_SUITE_HOLD_ID:
        raise ValueError(f"{source} scope mismatch")
    if data.get("source_mode") != P7_SOURCE_MODE or data.get("git_checked") is not False:
        raise ValueError(f"{source} source mode mismatch")
    for key in _RELEASE_CLOSED_KEYS:
        if data.get(key) is not False:
            raise ValueError(f"{source} must keep {key}=false")
    for key in _BODY_RETENTION_KEYS:
        if data.get(key) is not False:
            raise ValueError(f"{source} must keep {key}=false")
    for key in _CAPTURE_CLOSED_KEYS:
        if key == "active_baseline_update_allowed":
            continue
        if data.get(key) is not False:
            raise ValueError(f"{source} must keep {key}=false")
    if data.get("source_snapshot_ref_updated_in_active_builders") is not False:
        raise ValueError(f"{source} must not update runtime builders")
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must be body_free")
    assert_false_markers(safe_mapping(data.get("public_contract")), source=f"{source}.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source=f"{source}.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source=source)


def build_p7_hold004_active_baseline_adoption_evidence_bundle(
    *,
    local_repeat_collect_evidence: Mapping[str, Any] | None = None,
    source_identity_decision: Mapping[str, Any] | None = None,
    root_cause_review: Mapping[str, Any] | None = None,
    test_semantics_review: Mapping[str, Any] | None = None,
    received_snapshot_reconcile: Mapping[str, Any] | None = None,
    runtime_builder_update_plan_recorded: Any = True,
    matrix_handoff_update_plan_recorded: Any = True,
) -> dict[str, Any]:
    """Build R34 adoption evidence bundle and R27 evidence-freeze connection.

    R34 intentionally freezes evidence and connects it to the existing R27
    adoption evidence material. It does not make active-baseline changes, does
    not refresh runtime builders, and does not open official group_02 capture.
    """

    local_evidence = (
        safe_mapping(local_repeat_collect_evidence)
        if local_repeat_collect_evidence is not None
        else build_p7_hold004_local_repeat_collect_evidence()
    )
    assert_p7_hold004_local_repeat_collect_evidence_contract(local_evidence)
    source_identity = (
        safe_mapping(source_identity_decision)
        if source_identity_decision is not None
        else build_p7_hold004_source_identity_decision(local_repeat_collect_evidence=local_evidence)
    )
    assert_p7_hold004_source_identity_decision_contract(source_identity)
    root_review = (
        safe_mapping(root_cause_review)
        if root_cause_review is not None
        else build_p7_hold004_item_fingerprint_root_cause_review(
            local_repeat_collect_evidence=local_evidence,
            source_identity_decision=source_identity,
        )
    )
    assert_p7_hold004_item_fingerprint_root_cause_review_contract(root_review)
    semantics_review = (
        safe_mapping(test_semantics_review)
        if test_semantics_review is not None
        else build_p7_hold004_test_semantics_review(root_cause_review=root_review)
    )
    assert_p7_hold004_test_semantics_review_contract(semantics_review)
    reconcile = (
        safe_mapping(received_snapshot_reconcile)
        if received_snapshot_reconcile is not None
        else build_p7_hold004_received_snapshot_baseline_fingerprint_reconcile()
    )
    assert_p7_hold004_received_snapshot_baseline_fingerprint_reconcile_contract(reconcile)

    r27_evidence_freeze = build_p7_hold004_received_snapshot_adoption_evidence_freeze(
        received_snapshot_reconcile=reconcile,
        repeat_collect_run_count=local_evidence.get("repeat_collect_run_count"),
        repeat_collect_counts_warnings_fingerprints_match=local_evidence.get(
            "counts_warnings_fingerprints_stable"
        ),
        root_cause_status=root_review.get("root_cause_status"),
        root_cause_review_recorded=root_review.get("root_cause_review_satisfied") is True,
        source_identity_decision_recorded=source_identity.get("source_identity_decision_recorded") is True,
        source_identity_accepted=source_identity.get("source_identity_accepted") is True,
        test_semantics_reviewed=semantics_review.get("test_semantics_review_satisfied") is True,
        test_semantics_review_outcome=semantics_review.get("test_semantics_review_outcome"),
        baseline_id_or_revision_update_planned=True,
        runtime_builder_update_plan_recorded=runtime_builder_update_plan_recorded,
        matrix_handoff_update_plan_recorded=matrix_handoff_update_plan_recorded,
    )
    assert_p7_hold004_received_snapshot_adoption_evidence_freeze_contract(r27_evidence_freeze)

    can_mark_r27 = r27_evidence_freeze.get("can_mark_r27_conditions_satisfied") is True
    candidate = _candidate_active_baseline_material_for_adoption()
    previous = _previous_active_baseline_material_for_adoption()
    material = {
        "schema_version": P7_HOLD004_ACTIVE_BASELINE_ADOPTION_EVIDENCE_BUNDLE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_HOLD004_ACTIVE_BASELINE_ADOPTION_EVIDENCE_BUNDLE_STEP,
        "implementation_step": P7_HOLD004_ACTIVE_BASELINE_ADOPTION_EVIDENCE_BUNDLE_STEP,
        "hold_id": P7_HOLD004_BACKEND_SUITE_HOLD_ID,
        "bundle_id": P7_HOLD004_ACTIVE_BASELINE_ADOPTION_EVIDENCE_BUNDLE_ID,
        "source_mode": P7_SOURCE_MODE,
        "git_checked": P7_GIT_CHECKED,
        "local_repeat_collect_evidence_id": clean_identifier(
            local_evidence.get("evidence_id"), default=P7_HOLD004_LOCAL_REPEAT_COLLECT_EVIDENCE_ID, max_length=160
        ),
        "source_identity_decision_id": clean_identifier(
            source_identity.get("decision_id"), default=P7_HOLD004_SOURCE_IDENTITY_DECISION_ID, max_length=160
        ),
        "root_cause_review_id": clean_identifier(
            root_review.get("review_id"), default=P7_HOLD004_ITEM_FINGERPRINT_ROOT_CAUSE_REVIEW_ID, max_length=160
        ),
        "test_semantics_review_id": clean_identifier(
            semantics_review.get("review_id"), default=P7_HOLD004_TEST_SEMANTICS_REVIEW_ID, max_length=160
        ),
        "received_reconcile_id": P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_ID,
        "r27_adoption_evidence_freeze_id": clean_identifier(
            r27_evidence_freeze.get("evidence_freeze_id"),
            default=P7_HOLD004_RECEIVED_SNAPSHOT_ADOPTION_EVIDENCE_FREEZE_ID,
            max_length=180,
        ),
        "r27_adoption_evidence_freeze_schema_version": P7_HOLD004_RECEIVED_SNAPSHOT_ADOPTION_EVIDENCE_FREEZE_SCHEMA_VERSION,
        "r27_adoption_evidence_freeze": r27_evidence_freeze,
        "previous_active_baseline": previous,
        "candidate_active_baseline": candidate,
        "previous_active_baseline_retained": True,
        "same_baseline_id_hash_replacement_allowed": False,
        "canonical_received_snapshot_ref": P7_HOLD004_RECEIVED_ZIP_REF,
        "local_attachment_ref_observed": P7_HOLD004_LOCAL_ATTACHMENT_REF_OBSERVED,
        "local_attachment_promoted_to_source_snapshot_ref": False,
        "r30_local_repeat_collect_evidence_satisfied": local_evidence.get("satisfied") is True,
        "r31_source_identity_decision_satisfied": source_identity.get("satisfied") is True,
        "r32_root_cause_review_satisfied": root_review.get("satisfied") is True,
        "r33_test_semantics_review_satisfied": semantics_review.get("satisfied") is True,
        "r27_condition_projection": safe_mapping(r27_evidence_freeze.get("r27_condition_projection")),
        "r27_condition_inputs": safe_mapping(r27_evidence_freeze.get("r27_condition_inputs")),
        "r27_manual_boolean_only_adoption_ready_allowed": False,
        "adoption_evidence_freeze_satisfied": can_mark_r27,
        "can_mark_r27_conditions_satisfied": can_mark_r27,
        "adoption_status_if_applied_to_r27": clean_identifier(
            r27_evidence_freeze.get("adoption_status_if_applied_to_r27"), default="", max_length=180
        ),
        "adoption_evidence_status": clean_identifier(
            r27_evidence_freeze.get("evidence_status"), default="", max_length=180
        ),
        "runtime_builder_update_plan_recorded": _coerce_bool(runtime_builder_update_plan_recorded),
        "matrix_handoff_update_plan_recorded": _coerce_bool(matrix_handoff_update_plan_recorded),
        "active_baseline_update_allowed_by_evidence": False,
        "active_baseline_adoption_ready": False,
        "active_baseline_update_allowed": False,
        "source_snapshot_ref_update_allowed": False,
        "active_baseline_update_applied_to_runtime_builders": False,
        "source_snapshot_ref_updated_in_active_builders": False,
        "conditional_active_baseline_adoption_gate_not_built_in_r34": True,
        "collect_only_is_not_execution_green": True,
        "execution_green_confirmed": False,
        **_body_retention_flags(),
        **_capture_closed_boundary(),
        **_release_closed_boundary(),
        "implementation_scope": dict(_R34_IMPLEMENTATION_SCOPE_FLAGS),
        "unresolved_hold_refs": [P7_HOLD004_BACKEND_SUITE_HOLD_ID],
        "required_followup_fixes": list(_R34_REQUIRED_FOLLOWUP_FIXES),
        "public_contract": _public_contract_boundary_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_hold004_active_baseline_adoption_evidence_bundle_contract(material)
    return material


def assert_p7_hold004_active_baseline_adoption_evidence_bundle_contract(material: Mapping[str, Any]) -> bool:
    """Validate R34 adoption evidence bundle / R27 connection material."""

    data = safe_mapping(material)
    source = "p7_hold004_active_baseline_adoption_evidence_bundle"
    if data.get("schema_version") != P7_HOLD004_ACTIVE_BASELINE_ADOPTION_EVIDENCE_BUNDLE_SCHEMA_VERSION:
        raise ValueError("P7-HOLD-004 R34 schema_version mismatch")
    if data.get("implementation_step") != P7_HOLD004_ACTIVE_BASELINE_ADOPTION_EVIDENCE_BUNDLE_STEP:
        raise ValueError("P7-HOLD-004 R34 implementation_step mismatch")
    if data.get("bundle_id") != P7_HOLD004_ACTIVE_BASELINE_ADOPTION_EVIDENCE_BUNDLE_ID:
        raise ValueError("P7-HOLD-004 R34 bundle id mismatch")
    _assert_common_closed_body_free(data, source=source)
    _implementation_scope_contract_for_step(
        safe_mapping(data.get("implementation_scope")), expected=_R34_IMPLEMENTATION_SCOPE_FLAGS, source=source
    )
    if data.get("local_repeat_collect_evidence_id") != P7_HOLD004_LOCAL_REPEAT_COLLECT_EVIDENCE_ID:
        raise ValueError("P7-HOLD-004 R34 R30 evidence id mismatch")
    if data.get("source_identity_decision_id") != P7_HOLD004_SOURCE_IDENTITY_DECISION_ID:
        raise ValueError("P7-HOLD-004 R34 R31 decision id mismatch")
    if data.get("root_cause_review_id") != P7_HOLD004_ITEM_FINGERPRINT_ROOT_CAUSE_REVIEW_ID:
        raise ValueError("P7-HOLD-004 R34 R32 review id mismatch")
    if data.get("test_semantics_review_id") != P7_HOLD004_TEST_SEMANTICS_REVIEW_ID:
        raise ValueError("P7-HOLD-004 R34 R33 review id mismatch")
    if data.get("received_reconcile_id") != P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_ID:
        raise ValueError("P7-HOLD-004 R34 received reconcile id mismatch")
    freeze = safe_mapping(data.get("r27_adoption_evidence_freeze"))
    assert_p7_hold004_received_snapshot_adoption_evidence_freeze_contract(freeze)
    if data.get("r27_adoption_evidence_freeze_id") != P7_HOLD004_RECEIVED_SNAPSHOT_ADOPTION_EVIDENCE_FREEZE_ID:
        raise ValueError("P7-HOLD-004 R34 R27 evidence freeze id mismatch")
    previous = safe_mapping(data.get("previous_active_baseline"))
    candidate = safe_mapping(data.get("candidate_active_baseline"))
    if previous != _previous_active_baseline_material_for_adoption():
        raise ValueError("P7-HOLD-004 R34 previous active baseline mismatch")
    if candidate != _candidate_active_baseline_material_for_adoption():
        raise ValueError("P7-HOLD-004 R34 candidate active baseline mismatch")
    if candidate.get("baseline_id") == previous.get("baseline_id"):
        raise ValueError("P7-HOLD-004 R34 must not reuse same baseline id")
    if data.get("canonical_received_snapshot_ref") != P7_HOLD004_RECEIVED_ZIP_REF:
        raise ValueError("P7-HOLD-004 R34 canonical received snapshot ref mismatch")
    if data.get("local_attachment_ref_observed") != P7_HOLD004_LOCAL_ATTACHMENT_REF_OBSERVED:
        raise ValueError("P7-HOLD-004 R34 local attachment alias mismatch")
    if data.get("local_attachment_promoted_to_source_snapshot_ref") is not False:
        raise ValueError("P7-HOLD-004 R34 must not promote local attachment")
    for key in (
        "r30_local_repeat_collect_evidence_satisfied",
        "r31_source_identity_decision_satisfied",
        "r32_root_cause_review_satisfied",
        "r33_test_semantics_review_satisfied",
        "runtime_builder_update_plan_recorded",
        "matrix_handoff_update_plan_recorded",
    ):
        if not isinstance(data.get(key), bool):
            raise ValueError(f"P7-HOLD-004 R34 {key} must be bool")
    can_mark = data.get("can_mark_r27_conditions_satisfied") is True
    if data.get("adoption_evidence_freeze_satisfied") is not can_mark:
        raise ValueError("P7-HOLD-004 R34 evidence satisfied mirror mismatch")
    if freeze.get("can_mark_r27_conditions_satisfied") is not can_mark:
        raise ValueError("P7-HOLD-004 R34 R27 freeze satisfied mirror mismatch")
    if data.get("adoption_status_if_applied_to_r27") != freeze.get("adoption_status_if_applied_to_r27"):
        raise ValueError("P7-HOLD-004 R34 R27 adoption status mirror mismatch")
    if data.get("adoption_evidence_status") != freeze.get("evidence_status"):
        raise ValueError("P7-HOLD-004 R34 evidence status mirror mismatch")
    projection = safe_mapping(data.get("r27_condition_projection"))
    if projection != safe_mapping(freeze.get("r27_condition_projection")):
        raise ValueError("P7-HOLD-004 R34 R27 condition projection mismatch")
    if data.get("r27_manual_boolean_only_adoption_ready_allowed") is not False:
        raise ValueError("P7-HOLD-004 R34 must reject manual boolean-only readiness")
    if can_mark:
        if data.get("adoption_evidence_status") != P7_HOLD004_RECEIVED_ADOPTION_EVIDENCE_STATUS_SATISFIED_FOR_R27_CONDITIONAL_ADOPTION:
            raise ValueError("P7-HOLD-004 R34 satisfied evidence status mismatch")
        if data.get("adoption_status_if_applied_to_r27") != P7_HOLD004_RECEIVED_ADOPTION_STATUS_ADOPTABLE_AS_RECEIVED_SNAPSHOT_BASELINE_REFRESH:
            raise ValueError("P7-HOLD-004 R34 satisfied adoption status mismatch")
        for key in (
            "r30_local_repeat_collect_evidence_satisfied",
            "r31_source_identity_decision_satisfied",
            "r32_root_cause_review_satisfied",
            "r33_test_semantics_review_satisfied",
            "runtime_builder_update_plan_recorded",
            "matrix_handoff_update_plan_recorded",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-HOLD-004 R34 cannot satisfy without {key}")
    else:
        if data.get("adoption_status_if_applied_to_r27") == P7_HOLD004_RECEIVED_ADOPTION_STATUS_ADOPTABLE_AS_RECEIVED_SNAPSHOT_BASELINE_REFRESH:
            raise ValueError("P7-HOLD-004 R34 blocked bundle cannot project adoptable")
    if data.get("active_baseline_update_allowed_by_evidence") is not False:
        raise ValueError("P7-HOLD-004 R34 evidence bundle must not allow update by itself")
    if data.get("source_snapshot_ref_update_allowed") is not False:
        raise ValueError("P7-HOLD-004 R34 must not allow source ref update")
    if data.get("conditional_active_baseline_adoption_gate_not_built_in_r34") is not True:
        raise ValueError("P7-HOLD-004 R34 must not build conditional gate")
    if data.get("collect_only_is_not_execution_green") is not True or data.get("execution_green_confirmed") is not False:
        raise ValueError("P7-HOLD-004 R34 collect-only boundary mismatch")
    if P7_HOLD004_BACKEND_SUITE_HOLD_ID not in dedupe_identifiers(data.get("unresolved_hold_refs")):
        raise ValueError("P7-HOLD-004 R34 must keep HOLD-004 unresolved")
    return True


def build_p7_hold004_conditional_active_baseline_adoption_gate(
    *,
    adoption_evidence_bundle: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build R35 conditional active-baseline adoption gate material.

    R35 may mark the adoption gate ready and allow a subsequent active-baseline
    update only when the R34 bundle has satisfied the R27 evidence freeze. It
    still does not apply the update to runtime builders or open official
    group_02 capture.
    """

    bundle = (
        safe_mapping(adoption_evidence_bundle)
        if adoption_evidence_bundle is not None
        else build_p7_hold004_active_baseline_adoption_evidence_bundle()
    )
    assert_p7_hold004_active_baseline_adoption_evidence_bundle_contract(bundle)
    freeze = safe_mapping(bundle.get("r27_adoption_evidence_freeze"))
    assert_p7_hold004_received_snapshot_adoption_evidence_freeze_contract(freeze)
    conditional = build_p7_hold004_received_snapshot_conditional_active_baseline_adoption(
        adoption_evidence_freeze=freeze
    )
    assert_p7_hold004_received_snapshot_conditional_active_baseline_adoption_contract(conditional)

    ready = conditional.get("active_baseline_adoption_ready") is True
    update_allowed = conditional.get("active_baseline_update_allowed") is True
    source_update_allowed = conditional.get("source_snapshot_ref_update_allowed") is True
    material = {
        "schema_version": P7_HOLD004_CONDITIONAL_ACTIVE_BASELINE_ADOPTION_GATE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_HOLD004_CONDITIONAL_ACTIVE_BASELINE_ADOPTION_GATE_STEP,
        "implementation_step": P7_HOLD004_CONDITIONAL_ACTIVE_BASELINE_ADOPTION_GATE_STEP,
        "hold_id": P7_HOLD004_BACKEND_SUITE_HOLD_ID,
        "gate_id": P7_HOLD004_CONDITIONAL_ACTIVE_BASELINE_ADOPTION_GATE_ID,
        "source_mode": P7_SOURCE_MODE,
        "git_checked": P7_GIT_CHECKED,
        "adoption_evidence_bundle_id": clean_identifier(
            bundle.get("bundle_id"), default=P7_HOLD004_ACTIVE_BASELINE_ADOPTION_EVIDENCE_BUNDLE_ID, max_length=180
        ),
        "r27_adoption_evidence_freeze_id": clean_identifier(
            freeze.get("evidence_freeze_id"),
            default=P7_HOLD004_RECEIVED_SNAPSHOT_ADOPTION_EVIDENCE_FREEZE_ID,
            max_length=180,
        ),
        "r27_conditional_adoption_id": clean_identifier(
            conditional.get("adoption_id"),
            default=P7_HOLD004_RECEIVED_SNAPSHOT_CONDITIONAL_ACTIVE_BASELINE_ADOPTION_ID,
            max_length=180,
        ),
        "r27_conditional_adoption_schema_version": P7_HOLD004_RECEIVED_SNAPSHOT_CONDITIONAL_ACTIVE_BASELINE_ADOPTION_SCHEMA_VERSION,
        "conditional_active_baseline_adoption": conditional,
        "previous_active_baseline": safe_mapping(conditional.get("previous_active_baseline")),
        "candidate_active_baseline": safe_mapping(conditional.get("candidate_active_baseline")),
        "adoption_conditions": safe_mapping(conditional.get("adoption_conditions")),
        "adoption_status": clean_identifier(conditional.get("adoption_status"), default="", max_length=180),
        "root_cause_status": clean_identifier(conditional.get("root_cause_status"), default="", max_length=120),
        "adoption_evidence_bundle_satisfied": bundle.get("can_mark_r27_conditions_satisfied") is True,
        "adoption_evidence_freeze_satisfied": conditional.get("adoption_evidence_freeze_satisfied") is True,
        "active_baseline_adoption_ready": ready,
        "active_baseline_update_allowed": update_allowed,
        "source_snapshot_ref_update_allowed": source_update_allowed,
        "same_baseline_id_hash_replacement_allowed": False,
        "received_zip_promoted_to_source_snapshot_ref": False,
        "active_baseline_update_applied_to_runtime_builders": False,
        "source_snapshot_ref_updated_in_active_builders": False,
        "official_group_02_capture_blocked_until_adopted": True,
        "official_group_02_capture_run_allowed": False,
        "official_group_02_capture_result_recording_allowed": False,
        "can_claim_group_green": False,
        "can_claim_full_backend_suite_green": False,
        "full_backend_suite_green_confirmed": False,
        "hold004_close_allowed": False,
        "p7_complete": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "r35_is_gate_only_not_runtime_refresh": True,
        "post_adoption_active_baseline_material_not_built_in_r35": True,
        "runtime_builder_refresh_not_applied_in_r35": True,
        "collect_only_is_not_execution_green": True,
        "execution_green_confirmed": False,
        **_body_retention_flags(),
        **_release_closed_boundary(),
        "implementation_scope": dict(_R35_IMPLEMENTATION_SCOPE_FLAGS),
        "unresolved_hold_refs": [P7_HOLD004_BACKEND_SUITE_HOLD_ID],
        "required_followup_fixes": dedupe_identifiers(
            [
                *list(_R35_REQUIRED_FOLLOWUP_FIXES),
                *dedupe_identifiers(conditional.get("required_followup_fixes"), limit=80, max_length=200),
            ],
            limit=80,
            max_length=200,
        ),
        "public_contract": _public_contract_boundary_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_hold004_conditional_active_baseline_adoption_gate_contract(material)
    return material


def assert_p7_hold004_conditional_active_baseline_adoption_gate_contract(material: Mapping[str, Any]) -> bool:
    """Validate R35 conditional active-baseline adoption gate material."""

    data = safe_mapping(material)
    source = "p7_hold004_conditional_active_baseline_adoption_gate"
    if data.get("schema_version") != P7_HOLD004_CONDITIONAL_ACTIVE_BASELINE_ADOPTION_GATE_SCHEMA_VERSION:
        raise ValueError("P7-HOLD-004 R35 schema_version mismatch")
    if data.get("implementation_step") != P7_HOLD004_CONDITIONAL_ACTIVE_BASELINE_ADOPTION_GATE_STEP:
        raise ValueError("P7-HOLD-004 R35 implementation_step mismatch")
    if data.get("gate_id") != P7_HOLD004_CONDITIONAL_ACTIVE_BASELINE_ADOPTION_GATE_ID:
        raise ValueError("P7-HOLD-004 R35 gate id mismatch")
    _assert_r35_body_free_release_and_capture_boundaries(data, source=source)
    _implementation_scope_contract_for_step(
        safe_mapping(data.get("implementation_scope")), expected=_R35_IMPLEMENTATION_SCOPE_FLAGS, source=source
    )
    if data.get("adoption_evidence_bundle_id") != P7_HOLD004_ACTIVE_BASELINE_ADOPTION_EVIDENCE_BUNDLE_ID:
        raise ValueError("P7-HOLD-004 R35 bundle id mismatch")
    if data.get("r27_adoption_evidence_freeze_id") != P7_HOLD004_RECEIVED_SNAPSHOT_ADOPTION_EVIDENCE_FREEZE_ID:
        raise ValueError("P7-HOLD-004 R35 R27 evidence freeze id mismatch")
    if data.get("r27_conditional_adoption_id") != P7_HOLD004_RECEIVED_SNAPSHOT_CONDITIONAL_ACTIVE_BASELINE_ADOPTION_ID:
        raise ValueError("P7-HOLD-004 R35 R27 conditional adoption id mismatch")
    conditional = safe_mapping(data.get("conditional_active_baseline_adoption"))
    assert_p7_hold004_received_snapshot_conditional_active_baseline_adoption_contract(conditional)
    previous = safe_mapping(data.get("previous_active_baseline"))
    candidate = safe_mapping(data.get("candidate_active_baseline"))
    if previous != safe_mapping(conditional.get("previous_active_baseline")):
        raise ValueError("P7-HOLD-004 R35 previous baseline mirror mismatch")
    if candidate != safe_mapping(conditional.get("candidate_active_baseline")):
        raise ValueError("P7-HOLD-004 R35 candidate baseline mirror mismatch")
    if previous != _previous_active_baseline_material_for_adoption():
        raise ValueError("P7-HOLD-004 R35 previous active baseline mismatch")
    if candidate != _candidate_active_baseline_material_for_adoption():
        raise ValueError("P7-HOLD-004 R35 candidate active baseline mismatch")
    if candidate.get("baseline_id") == previous.get("baseline_id"):
        raise ValueError("P7-HOLD-004 R35 must not reuse same baseline id")
    conditions = safe_mapping(data.get("adoption_conditions"))
    if conditions != safe_mapping(conditional.get("adoption_conditions")):
        raise ValueError("P7-HOLD-004 R35 conditions mirror mismatch")
    ready = data.get("adoption_status") == P7_HOLD004_RECEIVED_ADOPTION_STATUS_ADOPTABLE_AS_RECEIVED_SNAPSHOT_BASELINE_REFRESH
    if data.get("active_baseline_adoption_ready") is not ready:
        raise ValueError("P7-HOLD-004 R35 ready flag mismatch")
    if data.get("active_baseline_update_allowed") is not ready:
        raise ValueError("P7-HOLD-004 R35 update allowed mirror mismatch")
    if data.get("source_snapshot_ref_update_allowed") is not ready:
        raise ValueError("P7-HOLD-004 R35 source update allowed mirror mismatch")
    if conditional.get("active_baseline_adoption_ready") is not ready:
        raise ValueError("P7-HOLD-004 R35 conditional ready mirror mismatch")
    if conditional.get("active_baseline_update_allowed") is not ready:
        raise ValueError("P7-HOLD-004 R35 conditional update mirror mismatch")
    if data.get("adoption_evidence_bundle_satisfied") is not data.get("adoption_evidence_freeze_satisfied"):
        raise ValueError("P7-HOLD-004 R35 evidence satisfaction mirror mismatch")
    if ready:
        if data.get("adoption_evidence_bundle_satisfied") is not True:
            raise ValueError("P7-HOLD-004 R35 ready requires R34 evidence bundle")
        if conditions.get("adoption_evidence_freeze_satisfied") is not True:
            raise ValueError("P7-HOLD-004 R35 ready requires R27 evidence freeze")
        for key in (
            "root_cause_classified",
            "repeated_collect_stable",
            "source_identity_decision_recorded",
            "source_identity_accepted",
            "test_semantics_reviewed",
            "candidate_baseline_id_changes",
            "same_baseline_id_hash_replacement_blocked",
        ):
            if conditions.get(key) is not True:
                raise ValueError(f"P7-HOLD-004 R35 ready requires {key}=true")
    else:
        if data.get("active_baseline_update_allowed") is True:
            raise ValueError("P7-HOLD-004 R35 blocked gate cannot allow update")
    for key in (
        "same_baseline_id_hash_replacement_allowed",
        "received_zip_promoted_to_source_snapshot_ref",
        "active_baseline_update_applied_to_runtime_builders",
        "source_snapshot_ref_updated_in_active_builders",
        "official_group_02_capture_run_allowed",
        "official_group_02_capture_result_recording_allowed",
        "can_claim_group_green",
        "can_claim_full_backend_suite_green",
        "full_backend_suite_green_confirmed",
        "hold004_close_allowed",
        "p7_complete",
        "p8_start_allowed",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-HOLD-004 R35 must keep {key}=false")
    for key in (
        "r35_is_gate_only_not_runtime_refresh",
        "post_adoption_active_baseline_material_not_built_in_r35",
        "runtime_builder_refresh_not_applied_in_r35",
        "collect_only_is_not_execution_green",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-HOLD-004 R35 {key} must be true")
    if data.get("execution_green_confirmed") is not False:
        raise ValueError("P7-HOLD-004 R35 must not claim execution green")
    if P7_HOLD004_BACKEND_SUITE_HOLD_ID not in dedupe_identifiers(data.get("unresolved_hold_refs")):
        raise ValueError("P7-HOLD-004 R35 must keep HOLD-004 unresolved")
    followups = set(dedupe_identifiers(data.get("required_followup_fixes"), limit=80, max_length=200))
    if "runtime_builder_refresh_required_after_r35" not in followups:
        raise ValueError("P7-HOLD-004 R35 must keep runtime builder refresh followup")
    if "full_backend_suite_green_unconfirmed" not in followups:
        raise ValueError("P7-HOLD-004 R35 must keep full backend suite green unconfirmed")
    return True


__all__ = [
    "P7_HOLD004_FULL_BACKEND_COLLECT_ONLY_SCOPE",
    "P7_HOLD004_LOCAL_ATTACHMENT_REF_OBSERVED",
    "P7_HOLD004_LOCAL_REPEAT_COLLECT_EVIDENCE_ID",
    "P7_HOLD004_LOCAL_REPEAT_COLLECT_EVIDENCE_SCHEMA_VERSION",
    "P7_HOLD004_LOCAL_REPEAT_COLLECT_EVIDENCE_STEP",
    "P7_HOLD004_MINIMUM_REPEAT_COLLECT_RUN_COUNT",
    "P7_HOLD004_SOURCE_IDENTITY_DECISION_ID",
    "P7_HOLD004_SOURCE_IDENTITY_DECISION_SCHEMA_VERSION",
    "P7_HOLD004_SOURCE_IDENTITY_DECISION_STEP",
    "P7_HOLD004_SOURCE_IDENTITY_STATUS_ACCEPTED",
    "P7_HOLD004_SOURCE_IDENTITY_STATUS_RECEIVED_REF_ACCEPTED_ATTACHMENT_ALIAS_NOT_PROMOTED",
    "assert_p7_hold004_local_repeat_collect_evidence_contract",
    "assert_p7_hold004_source_identity_decision_contract",
    "build_p7_hold004_local_repeat_collect_evidence",
    "build_p7_hold004_source_identity_decision",
    "P7_HOLD004_ITEM_FINGERPRINT_ROOT_CAUSE_REVIEW_ID",
    "P7_HOLD004_ITEM_FINGERPRINT_ROOT_CAUSE_REVIEW_SCHEMA_VERSION",
    "P7_HOLD004_ITEM_FINGERPRINT_ROOT_CAUSE_REVIEW_STEP",
    "P7_HOLD004_TEST_SEMANTICS_REVIEW_ID",
    "P7_HOLD004_TEST_SEMANTICS_REVIEW_SCHEMA_VERSION",
    "P7_HOLD004_TEST_SEMANTICS_REVIEW_STEP",
    "P7_HOLD004_ROOT_CAUSE_STATUS_BASELINE_CONSTANT_STALE",
    "P7_HOLD004_ACTIVE_BASELINE_ADOPTION_EVIDENCE_BUNDLE_ID",
    "P7_HOLD004_ACTIVE_BASELINE_ADOPTION_EVIDENCE_BUNDLE_SCHEMA_VERSION",
    "P7_HOLD004_ACTIVE_BASELINE_ADOPTION_EVIDENCE_BUNDLE_STEP",
    "P7_HOLD004_CONDITIONAL_ACTIVE_BASELINE_ADOPTION_GATE_ID",
    "P7_HOLD004_CONDITIONAL_ACTIVE_BASELINE_ADOPTION_GATE_SCHEMA_VERSION",
    "P7_HOLD004_CONDITIONAL_ACTIVE_BASELINE_ADOPTION_GATE_STEP",
    "assert_p7_hold004_item_fingerprint_root_cause_review_contract",
    "assert_p7_hold004_test_semantics_review_contract",
    "assert_p7_hold004_active_baseline_adoption_evidence_bundle_contract",
    "assert_p7_hold004_conditional_active_baseline_adoption_gate_contract",
    "build_p7_hold004_item_fingerprint_root_cause_review",
    "build_p7_hold004_test_semantics_review",
    "build_p7_hold004_active_baseline_adoption_evidence_bundle",
    "build_p7_hold004_conditional_active_baseline_adoption_gate",
]
