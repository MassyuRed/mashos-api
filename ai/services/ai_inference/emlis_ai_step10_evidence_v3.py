# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step 10 batch, cumulative, diff, and private/body-free evidence owners."""

from dataclasses import asdict, dataclass, is_dataclass
import hashlib
import hmac
from pathlib import Path
import platform
import re
import sys
from typing import Any, Mapping, Sequence

from emlis_ai_dormant_runtime_adapter_v3 import (
    DormantRuntimeExecution,
    runtime_execution_body_free_summary,
    validate_dormant_runtime_execution,
)
from emlis_ai_current_input_bundle import normalize_emlis_current_input
from emlis_ai_nls_v3_artifact_contract import (
    RECEIPT_SCHEMA as HISTORICAL_RECEIPT_SCHEMA_V2,
    ReceiptLineageAuthority,
    artifact_sha256,
    canonical_json_bytes,
    validate_case_evidence_receipt,
)
from emlis_ai_step10_dependency_manifest_v3 import (
    FROZEN_STEP10_CANDIDATE_VERSION_ID,
    FROZEN_STEP10_DEPENDENCY_CLOSURE_SHA256,
    fresh_step10_source_closure_sha256,
    step10_source_file_sha256,
    validate_step10_dependency_manifest,
)
from emlis_ai_step10_app_reachable_contract_v3 import (
    project_app_reachable_input,
    validate_app_reachable_input,
    validate_app_reachable_input_policy,
)
from emlis_ai_step9_artifact_contract_v3 import HARD_GATE_POLICY


PRIVATE_PACKET_SCHEMA = "cocolon.emlis.nls_v3.private_batch_packet.v1"
STEP10_RECEIPT_SCHEMA = "cocolon.emlis.nls_v3.case_evidence_receipt.v3"
BATCH_RUN_SCHEMA = "cocolon.emlis.nls_v3.batch_run_receipt.v1"
CUMULATIVE_RUN_SCHEMA = "cocolon.emlis.nls_v3.cumulative_run_manifest.v1"
OUTPUT_DIFF_SCHEMA = "cocolon.emlis.nls_v3.output_diff.v1"
LOCAL_REVIEW_SCHEMA = "cocolon.emlis.nls_v3.local_product_review.v1"
CHANGE_LEDGER_SCHEMA = "cocolon.emlis.nls_v3.change_ledger_row.v1"

_SHA_RE = re.compile(r"^[0-9a-f]{64}$")
_CASE_RE = re.compile(r"^nls3s_b[0-9]{3}_[0-9]{4}$")
_BATCH_RE = re.compile(r"^nls3_batch_[0-9]{3}$")
_RUN_RE = re.compile(r"^nls3run_[0-9a-f]{16,64}$")
_CUMULATIVE_RUN_RE = re.compile(r"^nls3cum_[0-9a-f]{16,64}$")
_SAMPLE_SOURCE_TO_RECEIPT_SOURCE = {
    "karen_generated": "karen_generated",
    "other_ai_generated_reviewed": "other_ai_generated_reviewed",
    "real_user_anonymized_private": "real_user_current_valid",
}
_SAMPLE_KEYS = frozenset(
    {
        "schema_version",
        "case_id",
        "batch_id",
        "source",
        "input",
        "semantic_contract",
        "coverage",
    }
)

COMMITMENT_POLICY: dict[str, Any] = {
    "schema_version": "cocolon.emlis.nls_v3.commitment_policy.hmac_sha256.v1",
    "scheme": "hmac_sha256_v1",
    "domain_prefix": "cocolon.emlis.nls_v3.step10",
    "key_bits": 256,
    "key_storage": "private_body_full_packet_only",
    "raw_sha256_shareable": False,
    "key_or_nonce_stored_in_body_free_receipt": False,
}
COMMITMENT_POLICY_SHA256 = artifact_sha256(COMMITMENT_POLICY)

LOCAL_REVIEW_AXES = (
    "PRIMARY_MEANING_RETAINED",
    "RELATION_DIRECTION_CORRECT",
    "NO_CAUSE_PERSONALITY_DIAGNOSIS_PROMOTION",
    "UNKNOWN_BOUNDARY_PRESERVED",
    "SELF_DENIAL_NOT_ADOPTED_OR_AMPLIFIED",
    "BOUND_EMLIS_RECEPTION",
    "SECTION_SEMANTIC_DISTINCTNESS",
    "NATURAL_NON_REPETITIVE_SURFACE",
    "DISTRIBUTION_NOT_OVERCONCENTRATED",
    "DEPTH_PROPORTIONAL",
    "NO_FALSE_UNDERSTANDING_COMPLETION",
    "IMMEDIATE_OBSERVATION_FEELS_READ",
)
LOCAL_REVIEW_FAILURE_CODES = frozenset(
    {
        "REQUIRED_MEANING_MISSING",
        "RELATION_DIRECTION_REVERSED",
        "UNSUPPORTED_CAUSE_OR_PERSONALITY_OR_DIAGNOSIS",
        "UNKNOWN_BOUNDARY_FILLED",
        "SELF_DENIAL_ADOPTED_OR_AMPLIFIED",
        "EMLIS_RECEPTION_UNBOUND",
        "SECTIONS_SEMANTICALLY_DUPLICATED",
        "SURFACE_UNNATURAL_OR_REPETITIVE",
        "SURFACE_DISTRIBUTION_OVERCONCENTRATED",
        "DEPTH_MISMATCH",
        "FALSE_UNDERSTANDING_COMPLETION",
        "IMMEDIATE_OBSERVATION_NOT_READ",
    }
)
LOCAL_REVIEW_PASS_CODES = frozenset(
    {
        "BOUND_EMLIS_RECEPTION",
        "INPUT_SPECIFIC",
        "NATURAL_ENOUGH",
    }
)
RUNNER_CASE_FAILURE_CODES = frozenset(
    {
        "STEP10_CASE_EXECUTION_REJECTED",
        "STEP10_EVIDENCE_BUILD_REJECTED",
        "V1_BASELINE_EXECUTION_REJECTED",
    }
)
HARD_GATE_FAILURE_CODES = frozenset(
    code
    for row in HARD_GATE_POLICY["gates"]
    for code in row["failure_codes"]
)
CHANGE_LEDGER_FAILURE_CODES = frozenset(
    set(LOCAL_REVIEW_FAILURE_CODES)
    | set(RUNNER_CASE_FAILURE_CODES)
    | set(HARD_GATE_FAILURE_CODES)
    | {"NO_VALID_CANDIDATE"}
)
FROZEN_RECEIPT_V3_COMMITMENT_POLICY_SHA256 = (
    "913c7051a6f6c88fbfbceb0e39660a97273da1fe462888dd8f497849a8b19405"
)
FROZEN_RECEIPT_V3_DOMAIN_PREFIX = "cocolon.emlis.nls_v3.step10"
FROZEN_RECEIPT_V3_HARD_GATE_FAILURE_CODES = frozenset(
    {
        "ADDRESS_RETARGETED",
        "AMBIGUOUS_REFERENT",
        "AMBIGUOUS_SEMANTIC_BINDING",
        "ANCHOR_REPLAY",
        "BROKEN_GRAMMAR",
        "DEPENDENCY_DRIFT",
        "DEPTH_INFLATED",
        "DEPTH_TRUNCATED",
        "DIAGNOSIS_CLAIM",
        "DISTINCT_OBLIGATIONS_COLLAPSED",
        "DUPLICATE_FRAGMENT",
        "FUTURE_GUARANTEE",
        "INPUT_ENUMERATION",
        "INVALID_SCHEMA",
        "INVENTED_CAUSE",
        "LABEL_ORDER_INVALID",
        "MODALITY_OVERCLAIM",
        "NO_SEMANTIC_BINDING",
        "NO_VALID_CANDIDATE",
        "PARENT_HASH_MISMATCH",
        "PERSONALITY_CLAIM",
        "POLARITY_INVERSION",
        "PUBLIC_CONTRACT_DIFF",
        "RAW_BODY_LEAK",
        "RELATION_DIRECTION_INVERSION",
        "RELATION_TYPE_MISMATCH",
        "RENDER_TEXT_MISMATCH",
        "REQUIRED_OBLIGATION_MISSING",
        "SECTION_SEMANTIC_REPLAY",
        "SELF_DENIAL_ADOPTED",
        "SELF_DENIAL_AMPLIFIED",
        "SOURCE_CONTEXT_NOT_BODY_RECOVERABLE",
        "TEMPORAL_SCOPE_DRIFT",
        "TOPIC_MIX",
        "UNBOUND_EMLIS_RECEPTION",
        "UNKNOWN_BOUNDARY_DROPPED",
        "UNKNOWN_EVIDENCE_REF",
        "UNPARSABLE_CONTROLLED_SURFACE",
        "UNSUPPORTED_CLAIM",
        "USER_NAME_INVENTED",
    }
)
FROZEN_RECEIPT_V3_LOCAL_REVIEW_PASS_CODES = frozenset(
    {"BOUND_EMLIS_RECEPTION", "INPUT_SPECIFIC", "NATURAL_ENOUGH"}
)
FROZEN_RECEIPT_V3_LOCAL_REVIEW_FAILURE_CODES = frozenset(
    {
        "DEPTH_MISMATCH",
        "EMLIS_RECEPTION_UNBOUND",
        "FALSE_UNDERSTANDING_COMPLETION",
        "IMMEDIATE_OBSERVATION_NOT_READ",
        "RELATION_DIRECTION_REVERSED",
        "REQUIRED_MEANING_MISSING",
        "SECTIONS_SEMANTICALLY_DUPLICATED",
        "SELF_DENIAL_ADOPTED_OR_AMPLIFIED",
        "SURFACE_DISTRIBUTION_OVERCONCENTRATED",
        "SURFACE_UNNATURAL_OR_REPETITIVE",
        "UNKNOWN_BOUNDARY_FILLED",
        "UNSUPPORTED_CAUSE_OR_PERSONALITY_OR_DIAGNOSIS",
    }
)
FAILURE_TAXONOMY: dict[str, Any] = {
    "schema_version": "cocolon.emlis.nls_v3.failure_taxonomy.step10.v1",
    "severities": ["BLOCKER", "MAJOR", "MINOR", "NOTE"],
    "acceptance_blocking_severities": ["BLOCKER", "MAJOR"],
    "review_failure_codes": sorted(LOCAL_REVIEW_FAILURE_CODES),
    "machine_failure_source": "hard_gate_and_runner_closed_codes",
    "case_specific_workaround_allowed": False,
    "free_text_in_body_free_artifact": False,
}
FAILURE_TAXONOMY_SHA256 = artifact_sha256(FAILURE_TAXONOMY)

LOCAL_REVIEW_RUBRIC: dict[str, Any] = {
    "schema_version": "cocolon.emlis.nls_v3.local_review_rubric.v1",
    "statuses": ["passed", "failed", "not_reviewed"],
    "axis_codes": list(LOCAL_REVIEW_AXES),
    "axis_statuses": ["passed", "failed", "not_reviewed"],
    "failure_codes": sorted(LOCAL_REVIEW_FAILURE_CODES),
    "pass_reason_codes": sorted(LOCAL_REVIEW_PASS_CODES),
    "failure_taxonomy_sha256": FAILURE_TAXONOMY_SHA256,
    "free_text_in_body_free_artifact": False,
    "step10_default_status": "not_reviewed",
    "step11_owns_batch_acceptance": True,
}
LOCAL_REVIEW_RUBRIC_SHA256 = artifact_sha256(LOCAL_REVIEW_RUBRIC)

RUNTIME_VALIDATION_PROTOCOL: dict[str, Any] = {
    "schema_version": "cocolon.emlis.nls_v3.runtime_validation_protocol.v1",
    "default_public_owner": "grounded_sentence_surface_canonical_v1",
    "default_v3_route": "disabled",
    "offline_runner_requires_runtime_activation": False,
    "verified_renderer_bytes_must_be_preserved": True,
    "v1_fallback_counts_as_v3_success": False,
    "private_body_full_and_body_free_separate": True,
    "aggregate_source": "case_rows_only",
    "partial_cumulative_formal_completion_forbidden": True,
    "step10_formal_batch_acceptance_forbidden": True,
}
RUNTIME_VALIDATION_PROTOCOL_SHA256 = artifact_sha256(RUNTIME_VALIDATION_PROTOCOL)

_FORBIDDEN_BODY_FREE_KEYS = frozenset(
    {
        "raw_input",
        "input",
        "normalized_input",
        "thought_text",
        "action_text",
        "memo",
        "memo_action",
        "question_answer",
        "comment_text",
        "candidate_text",
        "final_text",
        "visible_body",
        "response_text",
        "v1_body",
        "v3_body",
        "parsed_surface_witness",
        "verified_surface_binding",
        "surface_ast",
        "discourse_plan",
        "hmac_key_hex",
        "commitment_key",
        "nonce",
        "local_review_note",
        "free_text",
    }
)


class Step10EvidenceError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True, repr=False)
class CaseEvidenceBundle:
    case_id: str
    receipt: dict[str, Any]
    authority: ReceiptLineageAuthority
    runtime_summary: dict[str, Any]
    surface_profile: dict[str, Any]
    private_row: dict[str, Any]


def _valid_sha(value: Any) -> bool:
    return type(value) is str and _SHA_RE.fullmatch(value) is not None


def _valid_nonzero_sha(value: Any) -> bool:
    return _valid_sha(value) and value != "0" * 64


def _require_key(key: bytes) -> None:
    if type(key) is not bytes or len(key) != 32:
        raise Step10EvidenceError("COMMITMENT_KEY_256_BIT_REQUIRED")


def commitment_key_id(key: bytes) -> str:
    """Return a non-secret, domain-separated identifier for key continuity."""

    _require_key(key)
    return hmac.new(
        key,
        b"cocolon.emlis.nls_v3.step10\0commitment_key_id\0v1",
        hashlib.sha256,
    ).hexdigest()


def _strict_json_material(value: Any, path: str = "$") -> Any:
    """Convert trusted dataclass tuples to closed canonical-JSON material."""

    if is_dataclass(value) and not isinstance(value, type):
        return _strict_json_material(asdict(value), path)
    if type(value) is dict:
        result: dict[str, Any] = {}
        for key, child in value.items():
            if type(key) is not str:
                raise Step10EvidenceError("COMMITMENT_JSON_KEY_INVALID")
            result[key] = _strict_json_material(child, f"{path}.{key}")
        return result
    if type(value) in {list, tuple}:
        return [
            _strict_json_material(child, f"{path}[{index}]")
            for index, child in enumerate(value)
        ]
    if value is None or type(value) in {bool, int, str}:
        return value
    raise Step10EvidenceError("COMMITMENT_JSON_VALUE_INVALID")


def _sample_registry_projection(sample_case: Mapping[str, Any]) -> dict[str, Any]:
    """Re-run the frozen production input adapter before claiming pass.

    The batch runner owns full sample/corpus schema validation.  This evidence
    owner independently checks the identity envelope and only the actual app
    projection, without importing evaluation tooling into production modules.
    """

    sample = dict(sample_case)
    if (
        set(sample) != _SAMPLE_KEYS
        or sample.get("schema_version")
        != "cocolon.emlis.nls_v3.sample_case.v1"
        or _CASE_RE.fullmatch(str(sample.get("case_id") or "")) is None
        or _BATCH_RE.fullmatch(str(sample.get("batch_id") or "")) is None
        or sample.get("source") not in _SAMPLE_SOURCE_TO_RECEIPT_SOURCE
        or type(sample.get("semantic_contract")) is not dict
        or type(sample.get("coverage")) is not dict
    ):
        raise Step10EvidenceError("SAMPLE_CASE_CONTRACT_INVALID")
    case_batch = str(sample["case_id"])[7:10]
    if str(sample["batch_id"])[11:] != case_batch:
        raise Step10EvidenceError("SAMPLE_CASE_CONTRACT_INVALID")
    current_input = sample.get("input")
    if (
        validate_app_reachable_input_policy()
        or type(current_input) is not dict
        or validate_app_reachable_input(current_input)
    ):
        raise Step10EvidenceError("SAMPLE_APP_REACHABLE_INVALID")
    try:
        projected = project_app_reachable_input(current_input)
    except (KeyError, TypeError, ValueError) as exc:
        raise Step10EvidenceError("SAMPLE_GENERATION_PROJECTION_INVALID") from exc
    if type(projected) is not dict:
        raise Step10EvidenceError("SAMPLE_GENERATION_PROJECTION_INVALID")
    return projected


def _domain(domain: str) -> bytes:
    if type(domain) is not str or not re.fullmatch(r"[a-z0-9_]{3,64}", domain):
        raise Step10EvidenceError("COMMITMENT_DOMAIN_INVALID")
    return (
        # A v3 private packet must remain independently verifiable after a
        # later receipt version introduces a different commitment catalog.
        # Current generation fails closed on policy drift above; historical
        # v3 verification therefore always uses the domain frozen by v3.
        FROZEN_RECEIPT_V3_DOMAIN_PREFIX.encode("ascii")
        + b"\0"
        + domain.encode("ascii")
        + b"\0"
    )


def hmac_commit_bytes(key: bytes, domain: str, value: bytes) -> str:
    _require_key(key)
    if type(value) is not bytes:
        raise Step10EvidenceError("COMMITMENT_BYTES_REQUIRED")
    return hmac.new(key, _domain(domain) + value, hashlib.sha256).hexdigest()


def hmac_commit_json(key: bytes, domain: str, value: Any) -> str:
    try:
        payload = canonical_json_bytes(value)
    except (RecursionError, TypeError, ValueError, UnicodeError) as exc:
        raise Step10EvidenceError("COMMITMENT_JSON_INVALID") from exc
    return hmac_commit_bytes(key, domain, payload)


def _selected_candidate_identity_commitment(
    key: bytes,
    selected_candidate_id: str | None,
) -> str | None:
    if selected_candidate_id is None:
        return None
    if type(selected_candidate_id) is not str or re.fullmatch(
        r"nls3cand_[0-9a-f]{16,64}", selected_candidate_id
    ) is None:
        raise Step10EvidenceError("SELECTED_CANDIDATE_ID_INVALID")
    return hmac_commit_bytes(
        key,
        "selected_candidate_id",
        selected_candidate_id.encode("ascii"),
    )


def _validate_step10_case_evidence_receipt(
    value: Any,
    *,
    authority: ReceiptLineageAuthority,
    require_current_catalogs: bool,
) -> tuple[str, ...]:
    """Validate the Step 10 privacy revision without rewriting frozen v2.

    The frozen v2 validator still owns every common lineage field.  This v3
    adapter changes only selector identity fields from deterministic hashes to
    explicit HMAC commitments and projects them into v2 solely for reuse of
    the historical structural checks.
    """

    if type(value) is not dict:
        return ("STEP10_RECEIPT_MAPPING_REQUIRED",)
    issues: set[str] = set()
    if value.get("schema_version") != STEP10_RECEIPT_SCHEMA:
        issues.add("STEP10_RECEIPT_SCHEMA_INVALID")
    if require_current_catalogs and (
        COMMITMENT_POLICY_SHA256
        != FROZEN_RECEIPT_V3_COMMITMENT_POLICY_SHA256
        or HARD_GATE_FAILURE_CODES | {"NO_VALID_CANDIDATE"}
        != FROZEN_RECEIPT_V3_HARD_GATE_FAILURE_CODES
        or LOCAL_REVIEW_PASS_CODES
        != FROZEN_RECEIPT_V3_LOCAL_REVIEW_PASS_CODES
        or LOCAL_REVIEW_FAILURE_CODES
        != FROZEN_RECEIPT_V3_LOCAL_REVIEW_FAILURE_CODES
    ):
        issues.add("STEP10_RECEIPT_V3_CATALOG_VERSION_BUMP_REQUIRED")
    expected_policy_sha256 = (
        COMMITMENT_POLICY_SHA256
        if require_current_catalogs
        else FROZEN_RECEIPT_V3_COMMITMENT_POLICY_SHA256
    )
    policy = value.get("commitment_policy")
    if (
        type(policy) is not dict
        or set(policy)
        != {
            "scheme",
            "policy_sha256",
            "key_or_nonce_stored_in_receipt",
        }
        or policy.get("scheme") != "hmac_sha256_v1"
        or not _valid_nonzero_sha(policy.get("policy_sha256"))
        or policy.get("policy_sha256") != expected_policy_sha256
        or policy.get("key_or_nonce_stored_in_receipt") is not False
    ):
        issues.add("STEP10_RECEIPT_COMMITMENT_POLICY_INVALID")
    if not _valid_nonzero_sha(value.get("case_identity_commitment")):
        issues.add("STEP10_RECEIPT_CASE_IDENTITY_INVALID")
    allowed_hard_gate_codes = (
        HARD_GATE_FAILURE_CODES | {"NO_VALID_CANDIDATE"}
        if require_current_catalogs
        else FROZEN_RECEIPT_V3_HARD_GATE_FAILURE_CODES
    )
    hard_gate = value.get("hard_gate")
    failed_codes = hard_gate.get("failed_codes") if type(hard_gate) is dict else None
    if (
        type(failed_codes) is not list
        or failed_codes != sorted(set(failed_codes))
        or any(
            type(code) is not str
            or re.fullmatch(r"[A-Z][A-Z0-9_]{2,63}", code) is None
            or code not in allowed_hard_gate_codes
            for code in failed_codes
        )
    ):
        issues.add("STEP10_RECEIPT_HARD_GATE_CODE_INVALID")
    review = value.get("local_product_review")
    review_status = review.get("status") if type(review) is dict else None
    review_codes = review.get("reason_codes") if type(review) is dict else None
    pass_review_codes = (
        LOCAL_REVIEW_PASS_CODES
        if require_current_catalogs
        else FROZEN_RECEIPT_V3_LOCAL_REVIEW_PASS_CODES
    )
    failure_review_codes = (
        LOCAL_REVIEW_FAILURE_CODES
        if require_current_catalogs
        else FROZEN_RECEIPT_V3_LOCAL_REVIEW_FAILURE_CODES
    )
    allowed_review_codes = (
        pass_review_codes
        if review_status == "passed"
        else failure_review_codes
        if review_status == "failed"
        else frozenset()
    )
    if (
        review_status not in {"passed", "failed", "not_reviewed"}
        or type(review_codes) is not list
        or review_codes != sorted(set(review_codes))
        or any(
            type(code) is not str
            or re.fullmatch(r"[A-Z][A-Z0-9_]{2,63}", code) is None
            or code not in allowed_review_codes
            for code in review_codes
        )
    ):
        issues.add("STEP10_RECEIPT_LOCAL_REVIEW_CODE_INVALID")
    selector = value.get("selector_decision")
    if type(selector) is not dict or set(selector) != {
        "status",
        "selected_candidate_identity_commitment",
        "selection_attributes_commitment",
    }:
        issues.add("STEP10_RECEIPT_SELECTOR_SHAPE_INVALID")
        return tuple(sorted(issues))
    status = selector.get("status")
    selected_commitment = selector.get(
        "selected_candidate_identity_commitment"
    )
    attributes_commitment = selector.get("selection_attributes_commitment")
    if status not in {"selected", "no_valid_candidate"}:
        issues.add("STEP10_RECEIPT_SELECTOR_STATUS_INVALID")
    if (status == "selected" and not _valid_nonzero_sha(selected_commitment)) or (
        status == "no_valid_candidate" and selected_commitment is not None
    ):
        issues.add("STEP10_RECEIPT_SELECTED_COMMITMENT_INVALID")
    if not _valid_nonzero_sha(attributes_commitment):
        issues.add("STEP10_RECEIPT_ATTRIBUTES_COMMITMENT_INVALID")
    authority_values = asdict(authority)
    required_authority_hashes = (
        "commitment_policy_sha256",
        "source_dependency_closure_sha256",
        "observation_stage_context_commitment",
        "source_observation_plan_commitment",
        "obligation_ledger_commitment",
        "content_plan_commitment",
        "candidate_set_commitment",
        "selected_discourse_plan_commitment",
        "selected_surface_ast_commitment",
        "selected_candidate_body_commitment",
        "parsed_witness_binding_commitment",
        "v1_baseline_body_commitment",
        "environment_sha256",
        "runner_sha256",
        "rubric_sha256",
    )
    if any(
        not _valid_nonzero_sha(authority_values.get(field))
        for field in required_authority_hashes
    ) or (
        authority.previous_output_commitment is not None
        and not _valid_nonzero_sha(authority.previous_output_commitment)
    ):
        issues.add("STEP10_RECEIPT_AUTHORITY_HASH_INVALID")
    projection = dict(value)
    projection["schema_version"] = HISTORICAL_RECEIPT_SCHEMA_V2
    projection["selector_decision"] = {
        "status": status,
        "selected_candidate_id": (
            "nls3cand_" + selected_commitment
            if type(selected_commitment) is str
            else None
        ),
        "selection_attributes_sha256": attributes_commitment,
    }
    if validate_case_evidence_receipt(projection, authority=authority):
        issues.add("STEP10_RECEIPT_COMMON_CONTRACT_INVALID")
    return tuple(sorted(issues))


def validate_step10_case_evidence_receipt(
    value: Any,
    *,
    authority: ReceiptLineageAuthority,
) -> tuple[str, ...]:
    """Validate a receipt against the currently frozen Step 10 catalogs."""

    return _validate_step10_case_evidence_receipt(
        value,
        authority=authority,
        require_current_catalogs=True,
    )


def validate_historical_step10_case_evidence_receipt(
    value: Any,
    *,
    authority: ReceiptLineageAuthority,
) -> tuple[str, ...]:
    """Validate v3 structure/lineage without reinterpreting old catalogs."""

    return _validate_step10_case_evidence_receipt(
        value,
        authority=authority,
        require_current_catalogs=False,
    )


def _environment_artifact() -> dict[str, Any]:
    return {
        "schema_version": "cocolon.emlis.nls_v3.local_environment.v1",
        "python_implementation": platform.python_implementation(),
        "python_version": [
            sys.version_info.major,
            sys.version_info.minor,
            sys.version_info.micro,
        ],
        "platform_system": platform.system().lower(),
        "platform_machine": platform.machine().lower(),
        "hash_algorithm": "sha256",
        "unicode_normalization": "NFC",
        "line_ending": "LF",
    }


def _scan_body_free(value: Any, path: str = "$") -> list[str]:
    issues: list[str] = []
    if type(value) is dict:
        for key, child in value.items():
            if type(key) is not str:
                issues.append(f"BODY_FREE_NON_STRING_KEY:{path}")
                continue
            if key in _FORBIDDEN_BODY_FREE_KEYS:
                issues.append(f"BODY_FREE_FORBIDDEN_KEY:{path}.{key}")
            issues.extend(_scan_body_free(child, f"{path}.{key}"))
    elif type(value) is list:
        for index, child in enumerate(value):
            issues.extend(_scan_body_free(child, f"{path}[{index}]"))
    return issues


def assert_body_free(value: Any) -> None:
    issues = _scan_body_free(value)
    if issues:
        raise Step10EvidenceError("BODY_FREE_ARTIFACT_CONTAINS_PRIVATE_BODY")


def build_local_product_review(
    *,
    case_identity_commitment: str,
    run_id: str,
    selected_candidate_body_commitment: str,
    status: str,
    axis_results: Mapping[str, str],
    reason_codes: Sequence[str] = (),
    severity: str | None = None,
) -> dict[str, Any]:
    if (
        not _valid_nonzero_sha(case_identity_commitment)
        or not _valid_nonzero_sha(selected_candidate_body_commitment)
        or type(run_id) is not str
        or _RUN_RE.fullmatch(run_id) is None
    ):
        raise Step10EvidenceError("LOCAL_REVIEW_PARENT_BINDING_INVALID")
    if status not in {"passed", "failed", "not_reviewed"}:
        raise Step10EvidenceError("LOCAL_REVIEW_STATUS_INVALID")
    if type(axis_results) is not dict or set(axis_results) != set(LOCAL_REVIEW_AXES):
        raise Step10EvidenceError("LOCAL_REVIEW_AXIS_SET_INVALID")
    if any(
        value not in {"passed", "failed", "not_reviewed"}
        for value in axis_results.values()
    ):
        raise Step10EvidenceError("LOCAL_REVIEW_AXIS_STATUS_INVALID")
    if type(reason_codes) not in {list, tuple} or any(
        type(code) is not str
        or code not in LOCAL_REVIEW_FAILURE_CODES | LOCAL_REVIEW_PASS_CODES
        for code in reason_codes
    ):
        raise Step10EvidenceError("LOCAL_REVIEW_REASON_CODE_INVALID")
    normalized = sorted(set(reason_codes))
    statuses = set(axis_results.values())
    if status == "not_reviewed":
        if statuses != {"not_reviewed"} or normalized or severity is not None:
            raise Step10EvidenceError("LOCAL_REVIEW_NOT_REVIEWED_STATE_INVALID")
    elif status == "passed":
        if (
            statuses != {"passed"}
            or not normalized
            or any(code not in LOCAL_REVIEW_PASS_CODES for code in normalized)
            or severity is not None
        ):
            raise Step10EvidenceError("LOCAL_REVIEW_PASSED_STATE_INVALID")
    elif (
        "failed" not in statuses
        or not statuses <= {"passed", "failed"}
        or not normalized
        or any(code not in LOCAL_REVIEW_FAILURE_CODES for code in normalized)
        or severity not in {"BLOCKER", "MAJOR", "MINOR", "NOTE"}
    ):
        raise Step10EvidenceError("LOCAL_REVIEW_FAILED_STATE_INVALID")
    return {
        "schema_version": LOCAL_REVIEW_SCHEMA,
        "case_identity_commitment": case_identity_commitment,
        "run_id": run_id,
        "selected_candidate_body_commitment": (
            selected_candidate_body_commitment
        ),
        "status": status,
        "axis_results": {
            axis: axis_results[axis] for axis in LOCAL_REVIEW_AXES
        },
        "severity": severity,
        "reason_codes": normalized,
        "rubric_sha256": LOCAL_REVIEW_RUBRIC_SHA256,
        "failure_taxonomy_sha256": FAILURE_TAXONOMY_SHA256,
        "body_free": True,
    }


def _candidate_set_material(execution: DormantRuntimeExecution) -> dict[str, Any]:
    selection = execution.recovery_result.selection
    return _strict_json_material({
        "selector_decision": asdict(selection.decision),
        "evaluated_candidate_ids": list(selection.decision.evaluated_candidate_ids),
        "rejected_candidate_ids": list(selection.decision.rejected_candidate_ids),
        "gate_results": [
            {
                "candidate_id": row.candidate_id,
                "candidate_text_sha256": row.candidate_text_sha256,
                "hard_pass": row.hard_pass,
                "outcomes": [asdict(outcome) for outcome in row.outcomes],
                "selector_attributes": (
                    asdict(row.selector_attributes)
                    if row.selector_attributes is not None
                    else None
                ),
            }
            for row in selection.gate_results
        ],
        "recovery_trace": asdict(execution.recovery_result.trace),
    })


def _selected_private_material(execution: DormantRuntimeExecution) -> dict[str, Any]:
    selected = execution.selected_candidate
    if selected is None:
        marker = {"status": "v3_no_valid_candidate"}
        return {
            "discourse_plan": marker,
            "surface_ast": marker,
            "witness_binding": marker,
        }
    return _strict_json_material({
        "discourse_plan": selected.discourse_plan,
        "surface_ast": selected.surface_ast,
        "witness_binding": {
            "parsed_surface_witness": selected.parsed_surface_witness,
            "verified_surface_binding": selected.verified_surface_binding,
        },
    })


def _surface_profile_from_material(
    discourse_plan: Any,
    surface_ast: Any,
    *,
    commitment_key: bytes,
) -> dict[str, Any]:
    """Derive privacy-safe output distribution and near-template material."""

    _require_key(commitment_key)
    if (
        type(discourse_plan) is dict
        and discourse_plan.get("status") == "v3_no_valid_candidate"
        and type(surface_ast) is dict
        and surface_ast.get("status") == "v3_no_valid_candidate"
    ):
        return {
            "opening_family": None,
            "ending_family": None,
            "predicate_families": [],
            "reception_act_families": [],
            "near_duplicate_skeleton_commitment": None,
        }
    if type(discourse_plan) is not dict or type(surface_ast) is not dict:
        raise Step10EvidenceError("SURFACE_PROFILE_PARENT_INVALID")
    discourse_nodes = discourse_plan.get("nodes")
    sections = surface_ast.get("sections")
    if type(discourse_nodes) is not list or type(sections) is not list:
        raise Step10EvidenceError("SURFACE_PROFILE_PARENT_INVALID")
    clause_role_by_node = {
        row.get("node_id"): row.get("clause_role")
        for row in discourse_nodes
        if type(row) is dict
        and type(row.get("node_id")) is str
        and type(row.get("clause_role")) is str
    }
    skeleton_sections: list[dict[str, Any]] = []
    opening_family: str | None = None
    ending_family: str | None = None
    predicate_families: set[str] = set()
    reception_act_families: set[str] = set()
    for section in sections:
        if (
            type(section) is not dict
            or type(section.get("role")) is not str
            or type(section.get("sentences")) is not list
        ):
            raise Step10EvidenceError("SURFACE_PROFILE_PARENT_INVALID")
        skeleton_sentences: list[dict[str, Any]] = []
        for sentence in section["sentences"]:
            if type(sentence) is not dict or type(sentence.get("clauses")) is not list:
                raise Step10EvidenceError("SURFACE_PROFILE_PARENT_INVALID")
            terminal = sentence.get("terminal")
            if type(terminal) is not str:
                raise Step10EvidenceError("SURFACE_PROFILE_PARENT_INVALID")
            ending_family = terminal
            skeleton_clauses: list[dict[str, Any]] = []
            for clause in sentence["clauses"]:
                if type(clause) is not dict or type(clause.get("nodes")) is not list:
                    raise Step10EvidenceError("SURFACE_PROFILE_PARENT_INVALID")
                clause_role = clause_role_by_node.get(clause.get("discourse_node_id"))
                if type(clause_role) is not str:
                    raise Step10EvidenceError("SURFACE_PROFILE_PARENT_INVALID")
                if opening_family is None:
                    opening_family = clause_role
                node_shapes: list[dict[str, Any]] = []
                for node in clause["nodes"]:
                    if type(node) is not dict or type(node.get("node_type")) is not str:
                        raise Step10EvidenceError("SURFACE_PROFILE_PARENT_INVALID")
                    shape: dict[str, Any] = {"node_type": node["node_type"]}
                    for field in ("form", "modality", "edge_type"):
                        if field in node:
                            if type(node[field]) is not str:
                                raise Step10EvidenceError(
                                    "SURFACE_PROFILE_PARENT_INVALID"
                                )
                            shape[field] = node[field]
                    for field in (
                        "evidence_ids",
                        "nucleus_ids",
                        "target_obligation_ids",
                    ):
                        if field in node:
                            if type(node[field]) is not list:
                                raise Step10EvidenceError(
                                    "SURFACE_PROFILE_PARENT_INVALID"
                                )
                            shape[f"{field}_count"] = len(node[field])
                    if node["node_type"] == "observation_predicate":
                        form = node.get("form")
                        if type(form) is str:
                            predicate_families.add(form)
                    if node["node_type"] == "emlis_stance":
                        form = node.get("form")
                        if type(form) is str:
                            reception_act_families.add(form)
                    node_shapes.append(shape)
                skeleton_clauses.append(
                    {"clause_role": clause_role, "nodes": node_shapes}
                )
            skeleton_sentences.append(
                {"terminal": terminal, "clauses": skeleton_clauses}
            )
        skeleton_sections.append(
            {"role": section.get("role"), "sentences": skeleton_sentences}
        )
    if opening_family is None or ending_family is None:
        raise Step10EvidenceError("SURFACE_PROFILE_EMPTY_SELECTED_SURFACE")
    code_values = {
        opening_family,
        ending_family,
        *predicate_families,
        *reception_act_families,
    }
    if any(re.fullmatch(r"[a-z][a-z0-9_]{1,63}", code) is None for code in code_values):
        raise Step10EvidenceError("SURFACE_PROFILE_CODE_INVALID")
    return {
        "opening_family": opening_family,
        "ending_family": ending_family,
        "predicate_families": sorted(predicate_families),
        "reception_act_families": sorted(reception_act_families),
        "near_duplicate_skeleton_commitment": hmac_commit_json(
            commitment_key,
            "surface_skeleton",
            {"sections": skeleton_sections},
        ),
    }


def _failure_codes(execution: DormantRuntimeExecution) -> list[str]:
    if execution.status == "selected":
        return []
    codes = {
        code
        for result in execution.recovery_result.selection.gate_results
        for outcome in result.outcomes
        for code in outcome.failure_codes
    }
    return sorted(codes or {"NO_VALID_CANDIDATE"})


def build_case_evidence(
    execution: DormantRuntimeExecution,
    *,
    sample_case: Mapping[str, Any],
    v1_body_utf8: bytes,
    commitment_key: bytes,
    run_id: str,
    runner_sha256: str,
    previous_receipt: Mapping[str, Any] | None = None,
    previous_commitment_key_id: str | None = None,
) -> CaseEvidenceBundle:
    """Build one strict body-free receipt and its separate private row."""

    if validate_step10_dependency_manifest():
        raise Step10EvidenceError("STEP10_DEPENDENCY_DRIFT")
    if type(execution) is not DormantRuntimeExecution:
        raise Step10EvidenceError("RUNTIME_EXECUTION_REQUIRED")
    try:
        runtime_summary = runtime_execution_body_free_summary(execution)
    except Exception as exc:
        code = getattr(exc, "code", "RUNTIME_EXECUTION_INVALID")
        raise Step10EvidenceError(str(code)) from exc
    if type(sample_case) is not dict or type(sample_case.get("input")) is not dict:
        raise Step10EvidenceError("SAMPLE_CASE_INVALID")
    projected_input = _sample_registry_projection(sample_case)
    try:
        expected_normalized_input = normalize_emlis_current_input(projected_input)
        normalized_input_matches = (
            canonical_json_bytes(expected_normalized_input)
            == canonical_json_bytes(execution.normalized_input)
        )
    except (RecursionError, TypeError, ValueError, UnicodeError) as exc:
        raise Step10EvidenceError("EXECUTION_INPUT_LINEAGE_INVALID") from exc
    if not normalized_input_matches:
        raise Step10EvidenceError("EXECUTION_SAMPLE_INPUT_MISMATCH")
    case_id = sample_case.get("case_id")
    batch_id = sample_case.get("batch_id")
    sample_source = _SAMPLE_SOURCE_TO_RECEIPT_SOURCE.get(
        sample_case.get("source")
    )
    if type(case_id) is not str or _CASE_RE.fullmatch(case_id) is None:
        raise Step10EvidenceError("SAMPLE_CASE_ID_INVALID")
    if type(batch_id) is not str or _BATCH_RE.fullmatch(batch_id) is None:
        raise Step10EvidenceError("SAMPLE_BATCH_ID_INVALID")
    if sample_source is None:
        raise Step10EvidenceError("SAMPLE_SOURCE_INVALID")
    if type(run_id) is not str or _RUN_RE.fullmatch(run_id) is None:
        raise Step10EvidenceError("RUN_ID_INVALID")
    _require_key(commitment_key)
    if type(v1_body_utf8) is not bytes:
        raise Step10EvidenceError("V1_BODY_BYTES_REQUIRED")
    try:
        if v1_body_utf8.decode("utf-8", errors="strict").encode("utf-8") != v1_body_utf8:
            raise Step10EvidenceError("V1_BODY_UTF8_INVALID")
    except UnicodeDecodeError as exc:
        raise Step10EvidenceError("V1_BODY_UTF8_INVALID") from exc
    current_key_id = commitment_key_id(commitment_key)

    selected = _selected_private_material(execution)
    surface_profile = _surface_profile_from_material(
        selected["discourse_plan"],
        selected["surface_ast"],
        commitment_key=commitment_key,
    )
    candidate_set = _candidate_set_material(execution)
    snapshot = execution.inventory_result.source_snapshot
    source_plan_material = {
        "source_observation_plan_sha256": snapshot.source_observation_plan_sha256,
        "source_semantic_restatement_witness_sha256": (
            snapshot.source_semantic_restatement_witness_sha256
        ),
    }
    environment = _environment_artifact()
    expected_runner_sha = step10_source_file_sha256(
        "ai/tools/emlis_nls_v3_batch_run.py"
    )
    if not _valid_sha(runner_sha256) or runner_sha256 != expected_runner_sha:
        raise Step10EvidenceError("RUNNER_OWNER_HASH_UNFROZEN")
    v3_bytes = execution.final_utf8_bytes or b""
    material = _strict_json_material({
        "case_identity": projected_input,
        "observation_stage_context": execution.observation_stage_context,
        "source_observation_plan": source_plan_material,
        "obligation_ledger": execution.inventory_result.ledger,
        "content_plan": execution.content_plan,
        "candidate_set": candidate_set,
        "selected_discourse_plan": selected["discourse_plan"],
        "selected_surface_ast": selected["surface_ast"],
        "parsed_witness_binding": selected["witness_binding"],
    })
    commitments = {
        name: hmac_commit_json(commitment_key, name, value)
        for name, value in material.items()
    }
    commitments["selected_candidate_body"] = hmac_commit_bytes(
        commitment_key, "selected_candidate_body", v3_bytes
    )
    commitments["v1_baseline_body"] = hmac_commit_bytes(
        commitment_key, "v1_baseline_body", v1_body_utf8
    )

    previous_commitment: str | None = None
    previous_changed: bool | None = None
    if previous_receipt is not None:
        if type(previous_receipt) is not dict:
            raise Step10EvidenceError("PREVIOUS_RECEIPT_INVALID")
        policy = previous_receipt.get("commitment_policy")
        previous_commitment = previous_receipt.get(
            "selected_candidate_body_commitment"
        )
        if (
            type(policy) is not dict
            or policy.get("policy_sha256") != COMMITMENT_POLICY_SHA256
            or not _valid_sha(previous_commitment)
        ):
            raise Step10EvidenceError("PREVIOUS_RECEIPT_POLICY_MISMATCH")
        if previous_commitment_key_id != current_key_id:
            raise Step10EvidenceError("PREVIOUS_RECEIPT_KEY_MISMATCH")
        if (
            previous_receipt.get("case_identity_commitment")
            != commitments["case_identity"]
            or previous_receipt.get("batch_id") != batch_id
            or previous_receipt.get("sample_source") != sample_source
        ):
            raise Step10EvidenceError("PREVIOUS_RECEIPT_CASE_LINEAGE_MISMATCH")
        previous_changed = (
            previous_commitment != commitments["selected_candidate_body"]
        )
    elif previous_commitment_key_id is not None:
        raise Step10EvidenceError("PREVIOUS_RECEIPT_KEY_WITHOUT_RECEIPT")

    authority = ReceiptLineageAuthority(
        observation_stage="normal_observation",
        commitment_policy_sha256=COMMITMENT_POLICY_SHA256,
        source_dependency_closure_sha256=(
            FROZEN_STEP10_DEPENDENCY_CLOSURE_SHA256
        ),
        observation_stage_context_commitment=commitments[
            "observation_stage_context"
        ],
        source_observation_plan_commitment=commitments[
            "source_observation_plan"
        ],
        obligation_ledger_commitment=commitments["obligation_ledger"],
        content_plan_commitment=commitments["content_plan"],
        candidate_set_commitment=commitments["candidate_set"],
        selected_discourse_plan_commitment=commitments[
            "selected_discourse_plan"
        ],
        selected_surface_ast_commitment=commitments["selected_surface_ast"],
        selected_candidate_body_commitment=commitments[
            "selected_candidate_body"
        ],
        parsed_witness_binding_commitment=commitments[
            "parsed_witness_binding"
        ],
        v1_baseline_body_commitment=commitments["v1_baseline_body"],
        previous_output_commitment=previous_commitment,
        previous_output_changed=previous_changed,
        environment_sha256=artifact_sha256(environment),
        runner_sha256=runner_sha256,
        rubric_sha256=LOCAL_REVIEW_RUBRIC_SHA256,
    )
    decision = execution.recovery_result.selection.decision
    selected_status = decision.status == "selected"
    selected_candidate_identity_commitment = (
        _selected_candidate_identity_commitment(
            commitment_key,
            decision.selected_candidate_id,
        )
    )
    attributes_sha = hmac_commit_json(
        commitment_key,
        "selection_attributes",
        {
            "status": decision.status,
            "selected_candidate_id": decision.selected_candidate_id,
            "selection_attributes_sha256": decision.selection_attributes_sha256,
        },
    )
    receipt = {
        "schema_version": STEP10_RECEIPT_SCHEMA,
        "candidate_version_id": execution.candidate_version_id,
        "run_id": run_id,
        "batch_id": batch_id,
        "sample_source": sample_source,
        "case_identity_commitment": commitments["case_identity"],
        "commitment_policy": {
            "scheme": "hmac_sha256_v1",
            "policy_sha256": COMMITMENT_POLICY_SHA256,
            "key_or_nonce_stored_in_receipt": False,
        },
        "app_reachable_validation": {
            "status": "passed",
            "contract_version": "cocolon.input_contract.20260714",
        },
        "observation_stage": "normal_observation",
        "observation_stage_context_commitment": authority.observation_stage_context_commitment,
        "source_dependency_closure_sha256": authority.source_dependency_closure_sha256,
        "source_observation_plan_commitment": authority.source_observation_plan_commitment,
        "obligation_ledger_commitment": authority.obligation_ledger_commitment,
        "content_plan_commitment": authority.content_plan_commitment,
        "candidate_set_commitment": authority.candidate_set_commitment,
        "selected_discourse_plan_commitment": authority.selected_discourse_plan_commitment,
        "selected_surface_ast_commitment": authority.selected_surface_ast_commitment,
        "selected_candidate_body_commitment": authority.selected_candidate_body_commitment,
        "parsed_witness_binding_commitment": authority.parsed_witness_binding_commitment,
        "hard_gate": {
            "status": "passed" if selected_status else "failed",
            "failed_codes": _failure_codes(execution),
        },
        "selector_decision": {
            "status": "selected" if selected_status else "no_valid_candidate",
            "selected_candidate_identity_commitment": (
                selected_candidate_identity_commitment
            ),
            "selection_attributes_commitment": attributes_sha,
        },
        "v1_baseline_body_commitment": authority.v1_baseline_body_commitment,
        "local_product_review": {
            "status": "not_reviewed",
            "reason_codes": [],
        },
        "previous_output": {
            "commitment": previous_commitment,
            "changed": previous_changed,
        },
        "environment_sha256": authority.environment_sha256,
        "runner_sha256": authority.runner_sha256,
        "rubric_sha256": authority.rubric_sha256,
        "body_free": True,
    }
    issues = validate_step10_case_evidence_receipt(
        receipt,
        authority=authority,
    )
    if issues:
        raise Step10EvidenceError("CASE_RECEIPT_CONTRACT_REJECTED")
    assert_body_free(receipt)
    private_row = {
        "case_id": case_id,
        "sample_case": dict(sample_case),
        "normalized_input": execution.normalized_input,
        "v1_body": v1_body_utf8.decode("utf-8", errors="strict"),
        "v3_body": (
            execution.final_utf8_bytes.decode("utf-8", errors="strict")
            if execution.final_utf8_bytes is not None
            else None
        ),
        "commitment_material": material,
        "receipt_authority": asdict(authority),
        "runtime_summary": runtime_summary,
    }
    return CaseEvidenceBundle(
        case_id=case_id,
        receipt=receipt,
        authority=authority,
        runtime_summary=runtime_summary,
        surface_profile=surface_profile,
        private_row=private_row,
    )


def _case_row(bundle: CaseEvidenceBundle) -> dict[str, Any]:
    return {
        "case_id": bundle.case_id,
        "case_identity_commitment": bundle.receipt["case_identity_commitment"],
        "v1_baseline_body_commitment": bundle.receipt[
            "v1_baseline_body_commitment"
        ],
        "status": bundle.runtime_summary["status"],
        "failure_code": None,
        "runtime_summary": bundle.runtime_summary,
        "surface_profile": bundle.surface_profile,
        "receipt": bundle.receipt,
    }


def _failure_row(
    value: Mapping[str, Any],
    *,
    commitment_key: bytes,
    batch_id: str,
) -> dict[str, Any]:
    if type(value) is not dict:
        raise Step10EvidenceError("BATCH_FAILURE_ROW_INVALID")
    case_id = value.get("case_id")
    code = value.get("failure_code")
    if (
        type(case_id) is not str
        or _CASE_RE.fullmatch(case_id) is None
        or type(code) is not str
        or code not in RUNNER_CASE_FAILURE_CODES
    ):
        raise Step10EvidenceError("BATCH_FAILURE_ROW_INVALID")
    sample = value.get("sample_case")
    if (
        type(sample) is not dict
        or sample.get("case_id") != case_id
        or sample.get("batch_id") != batch_id
    ):
        raise Step10EvidenceError("BATCH_FAILURE_SAMPLE_LINEAGE_INVALID")
    projected = _sample_registry_projection(sample)
    v1_body_utf8 = value.get("v1_body_utf8")
    if v1_body_utf8 is not None and type(v1_body_utf8) is not bytes:
        raise Step10EvidenceError("BATCH_FAILURE_V1_BODY_INVALID")
    if type(v1_body_utf8) is bytes:
        try:
            v1_body_utf8.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise Step10EvidenceError("BATCH_FAILURE_V1_BODY_INVALID") from exc
    return {
        "case_id": case_id,
        "case_identity_commitment": hmac_commit_json(
            commitment_key,
            "case_identity",
            projected,
        ),
        "v1_baseline_body_commitment": (
            hmac_commit_bytes(
                commitment_key,
                "v1_baseline_body",
                v1_body_utf8,
            )
            if type(v1_body_utf8) is bytes
            else None
        ),
        "status": "exception",
        "failure_code": code,
        "runtime_summary": None,
        "surface_profile": None,
        "receipt": None,
    }


def _count_values(values: Sequence[str]) -> dict[str, int]:
    return {value: values.count(value) for value in sorted(set(values))}


def _aggregate(case_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    runtime_rows = [
        row["runtime_summary"]
        for row in case_rows
        if type(row.get("runtime_summary")) is dict
    ]
    latencies = [
        row["latency_ns"]
        for row in runtime_rows
        if type(row.get("latency_ns")) is int
        and type(row.get("latency_ns")) is not bool
        and row["latency_ns"] >= 0
    ]
    body_commitments = [
        row["receipt"]["selected_candidate_body_commitment"]
        for row in case_rows
        if row.get("status") == "selected"
        and type(row.get("receipt")) is dict
        and _valid_sha(row["receipt"].get("selected_candidate_body_commitment"))
    ]
    commitment_counts = {
        value: body_commitments.count(value) for value in set(body_commitments)
    }
    profiles = [
        row["surface_profile"]
        for row in case_rows
        if row.get("status") == "selected"
        and type(row.get("surface_profile")) is dict
    ]
    openings = [
        profile["opening_family"]
        for profile in profiles
        if type(profile.get("opening_family")) is str
    ]
    endings = [
        profile["ending_family"]
        for profile in profiles
        if type(profile.get("ending_family")) is str
    ]
    predicates = [
        code
        for profile in profiles
        for code in profile.get("predicate_families", [])
        if type(code) is str
    ]
    reception_acts = [
        code
        for profile in profiles
        for code in profile.get("reception_act_families", [])
        if type(code) is str
    ]
    skeletons = [
        profile["near_duplicate_skeleton_commitment"]
        for profile in profiles
        if _valid_nonzero_sha(
            profile.get("near_duplicate_skeleton_commitment")
        )
    ]
    skeleton_counts = _count_values(skeletons)
    return {
        "case_count": len(case_rows),
        "selected_count": sum(row.get("status") == "selected" for row in case_rows),
        "no_valid_candidate_count": sum(
            row.get("status") == "v3_no_valid_candidate" for row in case_rows
        ),
        "exception_count": sum(row.get("status") == "exception" for row in case_rows),
        "v1_fallback_count": sum(
            type(row.get("runtime_summary")) is dict
            and row["runtime_summary"].get("v1_fallback_used") is True
            for row in case_rows
        ),
        "local_reviewed_count": sum(
            type(row.get("receipt")) is dict
            and row["receipt"].get("local_product_review", {}).get("status")
            in {"passed", "failed"}
            for row in case_rows
        ),
        "latency_sample_count": len(latencies),
        "latency_total_ns": sum(latencies),
        "latency_min_ns": min(latencies) if latencies else 0,
        "latency_max_ns": max(latencies) if latencies else 0,
        "required_obligation_count": sum(
            row.get("semantic_metrics", {}).get("required_obligation_count", 0)
            for row in runtime_rows
            if type(row.get("semantic_metrics")) is dict
        ),
        "bound_obligation_count": sum(
            row.get("semantic_metrics", {}).get("bound_obligation_count", 0)
            for row in runtime_rows
            if type(row.get("semantic_metrics")) is dict
        ),
        "output_duplicate_cluster_count": sum(
            count > 1 for count in commitment_counts.values()
        ),
        "output_duplicate_case_count": sum(
            count for count in commitment_counts.values() if count > 1
        ),
        "near_duplicate_cluster_count": sum(
            count > 1 for count in skeleton_counts.values()
        ),
        "near_duplicate_case_count": sum(
            count for count in skeleton_counts.values() if count > 1
        ),
        "surface_distributions": {
            "opening_family_counts": _count_values(openings),
            "ending_family_counts": _count_values(endings),
            "predicate_family_counts": _count_values(predicates),
            "reception_act_family_counts": _count_values(reception_acts),
            "skeleton_commitment_counts": skeleton_counts,
        },
    }


_RUNTIME_SUMMARY_KEYS = frozenset(
    {
        "schema_version",
        "adapter_version",
        "candidate_version_id",
        "runtime_state",
        "public_owner",
        "execution_scope",
        "status",
        "source_dependency_closure_sha256",
        "selected_candidate_present",
        "evaluated_candidate_count",
        "rejected_candidate_count",
        "hard_gate_pass_count",
        "recovery_attempt_count",
        "latency_ns",
        "semantic_metrics",
        "v3_success",
        "v1_fallback_used",
        "v1_fallback_counts_as_v3_success",
        "body_free",
    }
)


def _surface_profile_issues(value: Any, *, selected: bool) -> set[str]:
    keys = {
        "opening_family",
        "ending_family",
        "predicate_families",
        "reception_act_families",
        "near_duplicate_skeleton_commitment",
    }
    if type(value) is not dict or set(value) != keys:
        return {"BATCH_SURFACE_PROFILE_KEYSET_INVALID"}
    if not selected:
        expected = {
            "opening_family": None,
            "ending_family": None,
            "predicate_families": [],
            "reception_act_families": [],
            "near_duplicate_skeleton_commitment": None,
        }
        return set() if value == expected else {"BATCH_SURFACE_PROFILE_INVALID"}
    code_re = re.compile(r"^[a-z][a-z0-9_]{1,63}$")
    if (
        type(value.get("opening_family")) is not str
        or code_re.fullmatch(value["opening_family"]) is None
        or type(value.get("ending_family")) is not str
        or code_re.fullmatch(value["ending_family"]) is None
        or not _valid_nonzero_sha(
            value.get("near_duplicate_skeleton_commitment")
        )
    ):
        return {"BATCH_SURFACE_PROFILE_INVALID"}
    for field in ("predicate_families", "reception_act_families"):
        codes = value.get(field)
        if (
            type(codes) is not list
            or codes != sorted(set(codes))
            or any(type(code) is not str or code_re.fullmatch(code) is None for code in codes)
        ):
            return {"BATCH_SURFACE_PROFILE_INVALID"}
    return set()


def _runtime_summary_issues(
    value: Any,
    *,
    candidate_version_id: str,
    row_status: str,
    source_dependency_closure_sha256: str,
) -> set[str]:
    issues: set[str] = set()
    if type(value) is not dict or set(value) != _RUNTIME_SUMMARY_KEYS:
        return {"BATCH_RUNTIME_SUMMARY_KEYSET_INVALID"}
    if value.get("schema_version") != "cocolon.emlis.nls_v3.runtime_execution_summary.v1":
        issues.add("BATCH_RUNTIME_SUMMARY_SCHEMA_INVALID")
    if value.get("adapter_version") != "cocolon.emlis.nls_v3.runtime_adapter.step10.v1":
        issues.add("BATCH_RUNTIME_ADAPTER_VERSION_INVALID")
    if value.get("candidate_version_id") != candidate_version_id:
        issues.add("BATCH_RUNTIME_CANDIDATE_MISMATCH")
    state = value.get("runtime_state")
    scope = value.get("execution_scope")
    if (state, scope) not in {
        ("disabled", "offline_batch"),
        ("offline", "offline_batch"),
        ("shadow", "shadow"),
        ("tester_only_preview", "tester_only_preview"),
    }:
        issues.add("BATCH_RUNTIME_STATE_SCOPE_INVALID")
    if value.get("public_owner") != "grounded_sentence_surface_canonical_v1":
        issues.add("BATCH_RUNTIME_PUBLIC_OWNER_INVALID")
    if (
        value.get("source_dependency_closure_sha256")
        != source_dependency_closure_sha256
    ):
        issues.add("BATCH_RUNTIME_DEPENDENCY_MISMATCH")
    if value.get("status") != row_status or row_status not in {
        "selected",
        "v3_no_valid_candidate",
    }:
        issues.add("BATCH_RUNTIME_STATUS_INVALID")
    selected = row_status == "selected"
    if value.get("selected_candidate_present") is not selected:
        issues.add("BATCH_RUNTIME_SELECTED_PRESENCE_INVALID")
    for field in (
        "evaluated_candidate_count",
        "rejected_candidate_count",
        "hard_gate_pass_count",
        "recovery_attempt_count",
        "latency_ns",
    ):
        current = value.get(field)
        if type(current) is not int or type(current) is bool or current < 0:
            issues.add("BATCH_RUNTIME_COUNT_INVALID")
    metrics = value.get("semantic_metrics")
    metric_keys = {
        "required_obligation_count",
        "bound_obligation_count",
        "semantic_atom_count",
        "section_count",
        "sentence_count",
        "depth",
    }
    if type(metrics) is not dict or set(metrics) != metric_keys:
        issues.add("BATCH_RUNTIME_SEMANTIC_METRICS_INVALID")
    else:
        for field in metric_keys - {"depth"}:
            current = metrics.get(field)
            if type(current) is not int or type(current) is bool or current < 0:
                issues.add("BATCH_RUNTIME_SEMANTIC_METRICS_INVALID")
        if metrics.get("depth") not in {"minimal", "focused", "layered"}:
            issues.add("BATCH_RUNTIME_DEPTH_INVALID")
        if selected and (
            metrics.get("bound_obligation_count", 0)
            < metrics.get("required_obligation_count", 0)
            or metrics.get("semantic_atom_count", 0) < 1
            or metrics.get("section_count", 0) < 2
            or metrics.get("sentence_count", 0) < 2
        ):
            issues.add("BATCH_RUNTIME_SEMANTIC_COVERAGE_INVALID")
    if (
        value.get("v3_success") is not selected
        or value.get("v1_fallback_used") is not False
        or value.get("v1_fallback_counts_as_v3_success") is not False
        or value.get("body_free") is not True
    ):
        issues.add("BATCH_RUNTIME_OUTCOME_BOUNDARY_INVALID")
    return issues


def _receipt_self_authority(value: Mapping[str, Any]) -> ReceiptLineageAuthority:
    previous = value.get("previous_output")
    policy = value.get("commitment_policy")
    if type(previous) is not dict or type(policy) is not dict:
        raise TypeError("receipt_parent_shape_invalid")
    return ReceiptLineageAuthority(
        observation_stage=value.get("observation_stage"),
        commitment_policy_sha256=policy.get("policy_sha256"),
        source_dependency_closure_sha256=value.get(
            "source_dependency_closure_sha256"
        ),
        observation_stage_context_commitment=value.get(
            "observation_stage_context_commitment"
        ),
        source_observation_plan_commitment=value.get(
            "source_observation_plan_commitment"
        ),
        obligation_ledger_commitment=value.get("obligation_ledger_commitment"),
        content_plan_commitment=value.get("content_plan_commitment"),
        candidate_set_commitment=value.get("candidate_set_commitment"),
        selected_discourse_plan_commitment=value.get(
            "selected_discourse_plan_commitment"
        ),
        selected_surface_ast_commitment=value.get(
            "selected_surface_ast_commitment"
        ),
        selected_candidate_body_commitment=value.get(
            "selected_candidate_body_commitment"
        ),
        parsed_witness_binding_commitment=value.get(
            "parsed_witness_binding_commitment"
        ),
        v1_baseline_body_commitment=value.get("v1_baseline_body_commitment"),
        previous_output_commitment=previous.get("commitment"),
        previous_output_changed=previous.get("changed"),
        environment_sha256=value.get("environment_sha256"),
        runner_sha256=value.get("runner_sha256"),
        rubric_sha256=value.get("rubric_sha256"),
    )


def _receipt_parent_issues(
    value: Any,
    *,
    candidate_version_id: str,
    run_id: str,
    batch_id: str,
    case_id: str,
    row_status: str,
    runtime_summary: Mapping[str, Any],
    source_dependency_closure_sha256: str,
    commitment_policy_sha256: str,
    require_current_authority: bool,
) -> set[str]:
    issues: set[str] = set()
    if type(value) is not dict:
        return {"BATCH_RECEIPT_INVALID"}
    try:
        authority = _receipt_self_authority(value)
    except (TypeError, ValueError):
        return {"BATCH_RECEIPT_AUTHORITY_INVALID"}
    receipt_issues = (
        validate_step10_case_evidence_receipt(value, authority=authority)
        if require_current_authority
        else validate_historical_step10_case_evidence_receipt(
            value,
            authority=authority,
        )
    )
    if receipt_issues:
        issues.add("BATCH_RECEIPT_CONTRACT_INVALID")
    authority_invalid = bool(
        authority.commitment_policy_sha256 != commitment_policy_sha256
        or authority.source_dependency_closure_sha256
        != source_dependency_closure_sha256
        or not _valid_nonzero_sha(authority.environment_sha256)
        or not _valid_nonzero_sha(authority.runner_sha256)
        or not _valid_nonzero_sha(authority.rubric_sha256)
    )
    if require_current_authority and (
        authority.environment_sha256 != artifact_sha256(_environment_artifact())
        or authority.runner_sha256
        != step10_source_file_sha256("ai/tools/emlis_nls_v3_batch_run.py")
        or authority.rubric_sha256 != LOCAL_REVIEW_RUBRIC_SHA256
    ):
        authority_invalid = True
    if authority_invalid:
        issues.add("BATCH_RECEIPT_AUTHORITY_LINEAGE_INVALID")
    if (
        value.get("candidate_version_id") != candidate_version_id
        or value.get("run_id") != run_id
        or value.get("batch_id") != batch_id
    ):
        issues.add("BATCH_RECEIPT_PARENT_MISMATCH")
    if (
        value.get("source_dependency_closure_sha256")
        != source_dependency_closure_sha256
    ):
        issues.add("BATCH_RECEIPT_DEPENDENCY_MISMATCH")
    selector = value.get("selector_decision")
    if type(selector) is not dict:
        issues.add("BATCH_RECEIPT_SELECTOR_INVALID")
    else:
        expected_status = "selected" if row_status == "selected" else "no_valid_candidate"
        if (
            selector.get("status") != expected_status
            or (
                selector.get("selected_candidate_identity_commitment")
                is not None
            )
            is not runtime_summary.get("selected_candidate_present")
        ):
            issues.add("BATCH_RECEIPT_RUNTIME_MISMATCH")
    # The case ID is deliberately not body-derived, but it must be a valid row
    # identity and is cross-checked to the private sample by the pair verifier.
    if _CASE_RE.fullmatch(case_id) is None:
        issues.add("BATCH_RECEIPT_CASE_ID_INVALID")
    return issues


def build_batch_evidence(
    bundles: Sequence[CaseEvidenceBundle],
    *,
    failure_rows: Sequence[Mapping[str, Any]] = (),
    batch_id: str,
    run_id: str,
    candidate_version_id: str,
    batch_manifest_sha256: str,
    expected_case_count: int,
    commitment_key: bytes,
    source_closure_start_sha256: str | None = None,
    source_closure_end_sha256: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if validate_step10_dependency_manifest():
        raise Step10EvidenceError("STEP10_DEPENDENCY_DRIFT")
    _require_key(commitment_key)
    start_closure = (
        fresh_step10_source_closure_sha256()
        if source_closure_start_sha256 is None
        else source_closure_start_sha256
    )
    end_closure = (
        fresh_step10_source_closure_sha256()
        if source_closure_end_sha256 is None
        else source_closure_end_sha256
    )
    if (
        start_closure != end_closure
        or start_closure != FROZEN_STEP10_DEPENDENCY_CLOSURE_SHA256
    ):
        raise Step10EvidenceError("STEP10_SOURCE_CLOSURE_CHANGED_DURING_RUN")
    if type(bundles) not in {list, tuple} or any(
        type(item) is not CaseEvidenceBundle for item in bundles
    ):
        raise Step10EvidenceError("CASE_EVIDENCE_SEQUENCE_INVALID")
    if type(batch_id) is not str or _BATCH_RE.fullmatch(batch_id) is None:
        raise Step10EvidenceError("BATCH_ID_INVALID")
    if type(run_id) is not str or _RUN_RE.fullmatch(run_id) is None:
        raise Step10EvidenceError("RUN_ID_INVALID")
    if candidate_version_id != FROZEN_STEP10_CANDIDATE_VERSION_ID:
        raise Step10EvidenceError("CANDIDATE_VERSION_INVALID")
    if not _valid_nonzero_sha(batch_manifest_sha256):
        raise Step10EvidenceError("BATCH_MANIFEST_HASH_INVALID")
    if type(expected_case_count) is not int or type(expected_case_count) is bool or expected_case_count < 1:
        raise Step10EvidenceError("EXPECTED_CASE_COUNT_INVALID")
    for item in bundles:
        receipt = item.receipt
        runtime_summary = item.runtime_summary
        private_sample = item.private_row.get("sample_case")
        if (
            receipt.get("candidate_version_id") != candidate_version_id
            or receipt.get("run_id") != run_id
            or receipt.get("batch_id") != batch_id
            or runtime_summary.get("candidate_version_id") != candidate_version_id
            or type(private_sample) is not dict
            or private_sample.get("case_id") != item.case_id
            or private_sample.get("batch_id") != batch_id
        ):
            raise Step10EvidenceError("CASE_EVIDENCE_PARENT_MISMATCH")
    rows = [_case_row(item) for item in bundles]
    failure_case_rows = [
        _failure_row(
            item,
            commitment_key=commitment_key,
            batch_id=batch_id,
        )
        for item in failure_rows
    ]
    rows.extend(failure_case_rows)
    rows.sort(key=lambda item: item["case_id"])
    ids = [row["case_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise Step10EvidenceError("BATCH_CASE_ID_DUPLICATE")
    aggregate = _aggregate(rows)
    complete = len(rows) == expected_case_count
    machine_clean = bool(
        complete
        and aggregate["selected_count"] == expected_case_count
        and aggregate["exception_count"] == 0
        and aggregate["no_valid_candidate_count"] == 0
        and aggregate["v1_fallback_count"] == 0
    )
    summary = {
        "schema_version": BATCH_RUN_SCHEMA,
        "candidate_version_id": candidate_version_id,
        "run_id": run_id,
        "batch_id": batch_id,
        "batch_manifest_sha256": batch_manifest_sha256,
        "source_dependency_closure_sha256": FROZEN_STEP10_DEPENDENCY_CLOSURE_SHA256,
        "source_closure_start_sha256": start_closure,
        "source_closure_end_sha256": end_closure,
        "source_closure_stable": True,
        "runtime_validation_protocol_sha256": RUNTIME_VALIDATION_PROTOCOL_SHA256,
        "commitment_policy_sha256": COMMITMENT_POLICY_SHA256,
        "commitment_key_id": commitment_key_id(commitment_key),
        "expected_case_count": expected_case_count,
        "executed_case_count": len(rows),
        "all_expected_cases_executed": complete,
        "case_rows": rows,
        "aggregate": aggregate,
        "aggregate_recomputed_from_case_rows": True,
        "machine_status": "clean" if machine_clean else "failed" if complete else "incomplete",
        "step10_smoke_only": True,
        "formal_batch001_initial_run_locked": False,
        "batch_accepted": False,
        "next_step_authority": "step11_cycle001_initial_run_only",
        "body_free": True,
    }
    issues = validate_batch_run_summary(summary)
    if issues:
        raise Step10EvidenceError(issues[0])
    private_cases = [item.private_row for item in bundles]
    private_cases.extend(
        {
            "case_id": row["case_id"],
            "sample_case": dict(row.get("sample_case") or {}),
            "normalized_input": normalize_emlis_current_input(
                _sample_registry_projection(dict(row.get("sample_case") or {}))
            ),
            "v1_body": (
                row["v1_body_utf8"].decode("utf-8", errors="strict")
                if type(row.get("v1_body_utf8")) is bytes
                else None
            ),
            "v3_body": None,
            "commitment_material": None,
            "receipt_authority": None,
            "runtime_summary": {
                "status": "exception",
                "failure_code": row["failure_code"],
            },
        }
        for row in failure_rows
    )
    private_cases.sort(key=lambda item: item["case_id"])
    private_packet = {
        "schema_version": PRIVATE_PACKET_SCHEMA,
        "storage_scope": "private_local_only",
        "body_full": True,
        "body_free_summary_sha256": artifact_sha256(summary),
        "commitment_key_id": commitment_key_id(commitment_key),
        "hmac_key_hex": commitment_key.hex(),
        "cases": private_cases,
    }
    return private_packet, summary


def _validate_batch_run_summary(
    value: Any,
    *,
    require_current_authority: bool,
) -> tuple[str, ...]:
    issues: set[str] = set()
    if require_current_authority and validate_step10_dependency_manifest():
        issues.add("BATCH_RUN_CURRENT_DEPENDENCY_DRIFT")
    expected_keys = {
        "schema_version", "candidate_version_id", "run_id", "batch_id",
        "batch_manifest_sha256", "source_dependency_closure_sha256",
        "source_closure_start_sha256", "source_closure_end_sha256",
        "source_closure_stable",
        "runtime_validation_protocol_sha256", "commitment_policy_sha256",
        "commitment_key_id",
        "expected_case_count", "executed_case_count",
        "all_expected_cases_executed", "case_rows", "aggregate",
        "aggregate_recomputed_from_case_rows", "machine_status",
        "step10_smoke_only", "formal_batch001_initial_run_locked",
        "batch_accepted", "next_step_authority", "body_free",
    }
    if type(value) is not dict or set(value) != expected_keys:
        return ("BATCH_RUN_KEYSET_INVALID",)
    if _scan_body_free(value):
        issues.add("BATCH_RUN_BODY_FREE_VIOLATION")
    if value.get("schema_version") != BATCH_RUN_SCHEMA:
        issues.add("BATCH_RUN_SCHEMA_INVALID")
    source_closure = value.get("source_dependency_closure_sha256")
    protocol_sha = value.get("runtime_validation_protocol_sha256")
    policy_sha = value.get("commitment_policy_sha256")
    if not _valid_nonzero_sha(source_closure):
        issues.add("BATCH_RUN_DEPENDENCY_HASH_INVALID")
    elif (
        require_current_authority
        and source_closure != FROZEN_STEP10_DEPENDENCY_CLOSURE_SHA256
    ):
        issues.add("BATCH_RUN_DEPENDENCY_MISMATCH")
    if (
        value.get("source_closure_start_sha256") != source_closure
        or value.get("source_closure_end_sha256") != source_closure
        or value.get("source_closure_stable") is not True
    ):
        issues.add("BATCH_RUN_SOURCE_CLOSURE_STABILITY_INVALID")
    if not _valid_nonzero_sha(protocol_sha):
        issues.add("BATCH_RUN_PROTOCOL_HASH_INVALID")
    elif require_current_authority and protocol_sha != RUNTIME_VALIDATION_PROTOCOL_SHA256:
        issues.add("BATCH_RUN_PROTOCOL_MISMATCH")
    if not _valid_nonzero_sha(policy_sha):
        issues.add("BATCH_RUN_COMMITMENT_POLICY_HASH_INVALID")
    elif require_current_authority and policy_sha != COMMITMENT_POLICY_SHA256:
        issues.add("BATCH_RUN_COMMITMENT_POLICY_MISMATCH")
    if not _valid_nonzero_sha(value.get("commitment_key_id")):
        issues.add("BATCH_RUN_COMMITMENT_KEY_ID_INVALID")
    if (
        type(value.get("candidate_version_id")) is not str
        or re.fullmatch(r"nls_v3_rc_[0-9]{4}", value["candidate_version_id"])
        is None
        or (
            require_current_authority
            and value["candidate_version_id"]
            != FROZEN_STEP10_CANDIDATE_VERSION_ID
        )
    ):
        issues.add("BATCH_RUN_CANDIDATE_VERSION_INVALID")
    if type(value.get("run_id")) is not str or _RUN_RE.fullmatch(value["run_id"]) is None:
        issues.add("BATCH_RUN_ID_INVALID")
    if type(value.get("batch_id")) is not str or _BATCH_RE.fullmatch(value["batch_id"]) is None:
        issues.add("BATCH_RUN_BATCH_ID_INVALID")
    if not _valid_nonzero_sha(value.get("batch_manifest_sha256")):
        issues.add("BATCH_RUN_MANIFEST_HASH_INVALID")
    rows = value.get("case_rows")
    if type(rows) is not list:
        issues.add("BATCH_RUN_CASE_ROWS_INVALID")
        rows = []
    ids: list[str] = []
    recorded_authorities: set[tuple[Any, Any, Any]] = set()
    for row in rows:
        if type(row) is not dict or set(row) != {
            "case_id", "case_identity_commitment",
            "v1_baseline_body_commitment", "status", "failure_code",
            "runtime_summary", "surface_profile", "receipt"
        }:
            issues.add("BATCH_RUN_CASE_ROW_INVALID")
            continue
        if not _valid_nonzero_sha(row.get("case_identity_commitment")):
            issues.add("BATCH_RUN_CASE_IDENTITY_COMMITMENT_INVALID")
        case_id = row.get("case_id")
        if type(case_id) is not str or _CASE_RE.fullmatch(case_id) is None:
            issues.add("BATCH_RUN_CASE_ID_INVALID")
        else:
            ids.append(case_id)
        if row.get("status") == "exception":
            if (
                type(row.get("failure_code")) is not str
                or row["failure_code"] not in RUNNER_CASE_FAILURE_CODES
                or row.get("receipt") is not None
                or row.get("runtime_summary") is not None
                or row.get("surface_profile") is not None
                or (
                    row.get("v1_baseline_body_commitment") is not None
                    and not _valid_nonzero_sha(
                        row.get("v1_baseline_body_commitment")
                    )
                )
            ):
                issues.add("BATCH_RUN_EXCEPTION_ROW_INVALID")
        elif row.get("status") in {"selected", "v3_no_valid_candidate"}:
            if (
                row.get("failure_code") is not None
                or type(row.get("receipt")) is not dict
                or type(row.get("runtime_summary")) is not dict
            ):
                issues.add("BATCH_RUN_COMPLETED_ROW_INVALID")
            else:
                recorded_authorities.add(
                    (
                        row["receipt"].get("environment_sha256"),
                        row["receipt"].get("runner_sha256"),
                        row["receipt"].get("rubric_sha256"),
                    )
                )
                if row.get("case_identity_commitment") != row["receipt"].get(
                    "case_identity_commitment"
                ):
                    issues.add("BATCH_RUN_CASE_IDENTITY_LINEAGE_MISMATCH")
                if row.get("v1_baseline_body_commitment") != row[
                    "receipt"
                ].get("v1_baseline_body_commitment"):
                    issues.add("BATCH_RUN_V1_BASELINE_LINEAGE_MISMATCH")
                issues.update(
                    _surface_profile_issues(
                        row["surface_profile"],
                        selected=row["status"] == "selected",
                    )
                )
                issues.update(
                    _runtime_summary_issues(
                        row["runtime_summary"],
                        candidate_version_id=value.get("candidate_version_id"),
                        row_status=row["status"],
                        source_dependency_closure_sha256=source_closure,
                    )
                )
                issues.update(
                    _receipt_parent_issues(
                        row["receipt"],
                        candidate_version_id=value.get("candidate_version_id"),
                        run_id=value.get("run_id"),
                        batch_id=value.get("batch_id"),
                        case_id=case_id,
                        row_status=row["status"],
                        runtime_summary=row["runtime_summary"],
                        source_dependency_closure_sha256=source_closure,
                        commitment_policy_sha256=policy_sha,
                        require_current_authority=require_current_authority,
                    )
                )
        else:
            issues.add("BATCH_RUN_CASE_STATUS_INVALID")
    if len(recorded_authorities) > 1:
        issues.add("BATCH_RUN_AUTHORITY_SET_INCONSISTENT")
    if len(ids) != len(set(ids)) or ids != sorted(ids):
        issues.add("BATCH_RUN_CASE_ORDER_OR_ID_INVALID")
    expected_count = value.get("expected_case_count")
    executed_count = value.get("executed_case_count")
    if (
        type(expected_count) is not int
        or type(expected_count) is bool
        or expected_count < 1
        or type(executed_count) is not int
        or type(executed_count) is bool
        or executed_count != len(rows)
    ):
        issues.add("BATCH_RUN_COUNT_INVALID")
    complete = len(rows) == expected_count
    if value.get("all_expected_cases_executed") is not complete:
        issues.add("BATCH_RUN_COMPLETENESS_MISMATCH")
    aggregate = _aggregate(rows)
    if value.get("aggregate") != aggregate:
        issues.add("BATCH_RUN_MANUAL_AGGREGATE_REJECTED")
    machine_clean = bool(
        complete
        and aggregate["selected_count"] == expected_count
        and aggregate["exception_count"] == 0
        and aggregate["no_valid_candidate_count"] == 0
        and aggregate["v1_fallback_count"] == 0
    )
    expected_status = "clean" if machine_clean else "failed" if complete else "incomplete"
    if value.get("machine_status") != expected_status:
        issues.add("BATCH_RUN_STATUS_MISMATCH")
    if (
        value.get("aggregate_recomputed_from_case_rows") is not True
        or value.get("step10_smoke_only") is not True
        or value.get("formal_batch001_initial_run_locked") is not False
        or value.get("batch_accepted") is not False
        or value.get("next_step_authority") != "step11_cycle001_initial_run_only"
        or value.get("body_free") is not True
    ):
        issues.add("BATCH_RUN_STEP_BOUNDARY_INVALID")
    return tuple(sorted(issues))


def validate_batch_run_summary(value: Any) -> tuple[str, ...]:
    """Validate a summary against the source/runtime authority now loaded."""

    return _validate_batch_run_summary(
        value,
        require_current_authority=True,
    )


def validate_historical_batch_run_summary(value: Any) -> tuple[str, ...]:
    """Validate append-only old evidence by its own closed parent lineage.

    Historical validation deliberately does not reinterpret an old closure,
    environment, runner, rubric, or protocol as current.  It still enforces
    every row/receipt relationship and requires valid recorded hashes.
    """

    return _validate_batch_run_summary(
        value,
        require_current_authority=False,
    )


def verify_batch_evidence(
    private_packet: Any,
    body_free_summary: Any,
) -> tuple[str, ...]:
    issues: set[str] = set(
        validate_historical_batch_run_summary(body_free_summary)
    )
    if type(body_free_summary) is not dict:
        return tuple(sorted(issues | {"BATCH_RUN_SUMMARY_MAPPING_REQUIRED"}))
    if type(private_packet) is not dict or set(private_packet) != {
        "schema_version", "storage_scope", "body_full",
        "body_free_summary_sha256", "commitment_key_id", "hmac_key_hex", "cases",
    }:
        return tuple(sorted(issues | {"PRIVATE_PACKET_KEYSET_INVALID"}))
    if (
        private_packet.get("schema_version") != PRIVATE_PACKET_SCHEMA
        or private_packet.get("storage_scope") != "private_local_only"
        or private_packet.get("body_full") is not True
    ):
        issues.add("PRIVATE_PACKET_BOUNDARY_INVALID")
    if private_packet.get("body_free_summary_sha256") != artifact_sha256(body_free_summary):
        issues.add("PRIVATE_PACKET_SUMMARY_HASH_MISMATCH")
    try:
        key = bytes.fromhex(private_packet.get("hmac_key_hex", ""))
        _require_key(key)
    except (TypeError, ValueError, Step10EvidenceError):
        issues.add("PRIVATE_PACKET_COMMITMENT_KEY_INVALID")
        return tuple(sorted(issues))
    expected_key_id = commitment_key_id(key)
    if (
        private_packet.get("commitment_key_id") != expected_key_id
        or body_free_summary.get("commitment_key_id") != expected_key_id
    ):
        issues.add("PRIVATE_PACKET_COMMITMENT_KEY_ID_MISMATCH")
    private_rows = private_packet.get("cases")
    summary_rows = body_free_summary.get("case_rows", []) if type(body_free_summary) is dict else []
    if type(private_rows) is not list or len(private_rows) != len(summary_rows):
        issues.add("PRIVATE_PACKET_CASE_COUNT_MISMATCH")
        return tuple(sorted(issues))
    by_id = {
        row.get("case_id"): row
        for row in private_rows
        if type(row) is dict and type(row.get("case_id")) is str
    }
    if len(by_id) != len(private_rows):
        issues.add("PRIVATE_PACKET_CASE_ID_INVALID")
        return tuple(sorted(issues))
    private_row_keys = {
        "case_id",
        "sample_case",
        "normalized_input",
        "v1_body",
        "v3_body",
        "commitment_material",
        "receipt_authority",
        "runtime_summary",
    }
    material_keys = {
        "case_identity",
        "observation_stage_context",
        "source_observation_plan",
        "obligation_ledger",
        "content_plan",
        "candidate_set",
        "selected_discourse_plan",
        "selected_surface_ast",
        "parsed_witness_binding",
    }
    for summary_row in summary_rows:
        case_id = summary_row.get("case_id")
        private_row = by_id.get(case_id)
        if private_row is None:
            issues.add("PRIVATE_PACKET_CASE_MISSING")
            continue
        if type(private_row) is not dict or set(private_row) != private_row_keys:
            issues.add("PRIVATE_PACKET_CASE_ROW_KEYSET_INVALID")
            continue
        if summary_row.get("status") == "exception":
            sample = private_row.get("sample_case")
            runtime = private_row.get("runtime_summary")
            v1_body = private_row.get("v1_body")
            try:
                projected = _sample_registry_projection(sample)
                expected_case_identity = hmac_commit_json(
                    key,
                    "case_identity",
                    projected,
                )
                expected_normalized = normalize_emlis_current_input(projected)
                expected_v1_commitment = (
                    hmac_commit_bytes(
                        key,
                        "v1_baseline_body",
                        v1_body.encode("utf-8", errors="strict"),
                    )
                    if type(v1_body) is str
                    else None
                )
            except (TypeError, UnicodeError, ValueError, Step10EvidenceError):
                expected_case_identity = None
                expected_normalized = None
                expected_v1_commitment = None
            if (
                type(sample) is not dict
                or sample.get("case_id") != case_id
                or sample.get("batch_id") != body_free_summary.get("batch_id")
                or summary_row.get("case_identity_commitment")
                != expected_case_identity
                or summary_row.get("v1_baseline_body_commitment")
                != expected_v1_commitment
                or private_row.get("normalized_input") != expected_normalized
                or type(runtime) is not dict
                or runtime.get("status") != "exception"
                or runtime.get("failure_code") != summary_row.get("failure_code")
            ):
                issues.add("PRIVATE_PACKET_EXCEPTION_ROW_MISMATCH")
            continue
        receipt = summary_row.get("receipt")
        material = private_row.get("commitment_material")
        authority_value = private_row.get("receipt_authority")
        if type(receipt) is not dict or type(material) is not dict or type(authority_value) is not dict:
            issues.add("PRIVATE_PACKET_COMPLETED_ROW_INVALID")
            continue
        if set(material) != material_keys:
            issues.add("PRIVATE_PACKET_COMMITMENT_MATERIAL_KEYSET_INVALID")
            continue
        if private_row.get("runtime_summary") != summary_row.get("runtime_summary"):
            issues.add("PRIVATE_PACKET_RUNTIME_SUMMARY_MISMATCH")
        sample = private_row.get("sample_case")
        normalized = private_row.get("normalized_input")
        if type(sample) is not dict:
            issues.add("PRIVATE_PACKET_SAMPLE_INVALID")
            continue
        try:
            projected = _sample_registry_projection(sample)
            expected_normalized = normalize_emlis_current_input(projected)
            lineage_matches = bool(
                sample.get("case_id") == case_id
                and sample.get("batch_id") == body_free_summary.get("batch_id")
                and _SAMPLE_SOURCE_TO_RECEIPT_SOURCE.get(sample.get("source"))
                == receipt.get("sample_source")
                and material.get("case_identity") == projected
                and canonical_json_bytes(normalized)
                == canonical_json_bytes(expected_normalized)
                and receipt.get("candidate_version_id")
                == body_free_summary.get("candidate_version_id")
                and receipt.get("run_id") == body_free_summary.get("run_id")
                and receipt.get("batch_id") == body_free_summary.get("batch_id")
            )
        except (RecursionError, TypeError, ValueError, UnicodeError, Step10EvidenceError):
            lineage_matches = False
        if not lineage_matches:
            issues.add("PRIVATE_PACKET_INPUT_LINEAGE_MISMATCH")
        try:
            authority = ReceiptLineageAuthority(**authority_value)
        except (TypeError, ValueError):
            issues.add("PRIVATE_PACKET_AUTHORITY_INVALID")
            continue
        expected = {
            name: hmac_commit_json(key, name, value)
            for name, value in material.items()
        }
        raw_v3_body = private_row.get("v3_body")
        v3_body = raw_v3_body
        v1_body = private_row.get("v1_body")
        if v3_body is None:
            v3_body = ""
        if type(v3_body) is not str or type(v1_body) is not str:
            issues.add("PRIVATE_PACKET_BODY_INVALID")
            continue
        expected["selected_candidate_body"] = hmac_commit_bytes(
            key, "selected_candidate_body", v3_body.encode("utf-8")
        )
        expected["v1_baseline_body"] = hmac_commit_bytes(
            key, "v1_baseline_body", v1_body.encode("utf-8")
        )
        authority_map = asdict(authority)
        mapping = {
            "observation_stage_context": "observation_stage_context_commitment",
            "source_observation_plan": "source_observation_plan_commitment",
            "obligation_ledger": "obligation_ledger_commitment",
            "content_plan": "content_plan_commitment",
            "candidate_set": "candidate_set_commitment",
            "selected_discourse_plan": "selected_discourse_plan_commitment",
            "selected_surface_ast": "selected_surface_ast_commitment",
            "selected_candidate_body": "selected_candidate_body_commitment",
            "parsed_witness_binding": "parsed_witness_binding_commitment",
            "v1_baseline_body": "v1_baseline_body_commitment",
        }
        if any(authority_map[field] != expected[name] for name, field in mapping.items()):
            issues.add("PRIVATE_PACKET_COMMITMENT_MISMATCH")
        if (
            expected.get("case_identity")
            != receipt.get("case_identity_commitment")
            or expected.get("case_identity")
            != summary_row.get("case_identity_commitment")
        ):
            issues.add("PRIVATE_PACKET_CASE_IDENTITY_COMMITMENT_MISMATCH")
        candidate_set = material.get("candidate_set")
        selector_material = (
            candidate_set.get("selector_decision")
            if type(candidate_set) is dict
            else None
        )
        receipt_selector = receipt.get("selector_decision")
        raw_status = (
            selector_material.get("status")
            if type(selector_material) is dict
            else None
        )
        raw_selected_id = (
            selector_material.get("selected_candidate_id")
            if type(selector_material) is dict
            else None
        )
        raw_attributes_sha = (
            selector_material.get("selection_attributes_sha256")
            if type(selector_material) is dict
            else None
        )
        expected_selector_status = (
            "selected"
            if raw_status == "selected"
            else "no_valid_candidate"
            if raw_status == "v3_no_valid_candidate"
            else None
        )
        try:
            expected_selected_identity = (
                _selected_candidate_identity_commitment(key, raw_selected_id)
            )
            expected_attributes_commitment = hmac_commit_json(
                key,
                "selection_attributes",
                {
                    "status": raw_status,
                    "selected_candidate_id": raw_selected_id,
                    "selection_attributes_sha256": raw_attributes_sha,
                },
            )
        except Step10EvidenceError:
            expected_selected_identity = None
            expected_attributes_commitment = None
        if (
            type(receipt_selector) is not dict
            or receipt_selector.get("status") != expected_selector_status
            or receipt_selector.get(
                "selected_candidate_identity_commitment"
            )
            != expected_selected_identity
            or receipt_selector.get("selection_attributes_commitment")
            != expected_attributes_commitment
        ):
            issues.add("PRIVATE_PACKET_SELECTOR_COMMITMENT_MISMATCH")
        selected_status = expected_selector_status == "selected"
        try:
            expected_surface_profile = _surface_profile_from_material(
                material.get("selected_discourse_plan"),
                material.get("selected_surface_ast"),
                commitment_key=key,
            )
        except Step10EvidenceError:
            expected_surface_profile = None
        if summary_row.get("surface_profile") != expected_surface_profile:
            issues.add("PRIVATE_PACKET_SURFACE_PROFILE_MISMATCH")
        row_runtime_summary = summary_row.get("runtime_summary")
        if (
            summary_row.get("status")
            != ("selected" if selected_status else "v3_no_valid_candidate")
            or type(row_runtime_summary) is not dict
            or row_runtime_summary.get("selected_candidate_present")
            is not selected_status
            or (selected_status and (type(raw_v3_body) is not str or not raw_v3_body))
            or (not selected_status and raw_v3_body is not None)
        ):
            issues.add("PRIVATE_PACKET_RUNTIME_SELECTOR_MISMATCH")
        gate_results = (
            candidate_set.get("gate_results", [])
            if type(candidate_set) is dict
            else []
        )
        if type(gate_results) is not list:
            gate_results = []
            issues.add("PRIVATE_PACKET_GATE_MATERIAL_INVALID")
        failed_codes = sorted({
            code
            for gate in gate_results
            if type(gate) is dict
            for outcome in gate.get("outcomes", [])
            if type(outcome) is dict
            for code in outcome.get("failure_codes", [])
            if type(code) is str
        })
        receipt_gate = receipt.get("hard_gate")
        if (
            type(receipt_gate) is not dict
            or receipt_gate.get("status")
            != ("passed" if selected_status else "failed")
            or receipt_gate.get("failed_codes")
            != ([] if selected_status else failed_codes or ["NO_VALID_CANDIDATE"])
        ):
            issues.add("PRIVATE_PACKET_HARD_GATE_MISMATCH")
        if type(row_runtime_summary) is dict and type(selector_material) is dict:
            evaluated_ids = selector_material.get("evaluated_candidate_ids")
            rejected_ids = selector_material.get("rejected_candidate_ids")
            recovery_trace = candidate_set.get("recovery_trace")
            attempts = (
                recovery_trace.get("attempts")
                if type(recovery_trace) is dict
                else None
            )
            hard_pass_count = sum(
                gate.get("hard_pass") is True
                for gate in gate_results
                if type(gate) is dict
            )
            if (
                type(evaluated_ids) is not list
                or type(rejected_ids) is not list
                or type(attempts) is not list
                or row_runtime_summary.get("evaluated_candidate_count")
                != len(evaluated_ids)
                or row_runtime_summary.get("rejected_candidate_count")
                != len(rejected_ids)
                or row_runtime_summary.get("hard_gate_pass_count")
                != hard_pass_count
                or row_runtime_summary.get("recovery_attempt_count")
                != len(attempts)
            ):
                issues.add("PRIVATE_PACKET_RUNTIME_COUNT_MISMATCH")
            ledger = material.get("obligation_ledger")
            content_plan = material.get("content_plan")
            surface_ast = material.get("selected_surface_ast")
            witness_binding = material.get("parsed_witness_binding")
            parsed_witness = (
                witness_binding.get("parsed_surface_witness")
                if type(witness_binding) is dict
                else None
            )
            verified_binding = (
                witness_binding.get("verified_surface_binding")
                if type(witness_binding) is dict
                else None
            )
            sections = (
                surface_ast.get("sections", [])
                if type(surface_ast) is dict
                else []
            )
            expected_metrics = {
                "required_obligation_count": len(
                    ledger.get("required_obligation_ids", [])
                    if type(ledger) is dict
                    else []
                ),
                "bound_obligation_count": len(
                    verified_binding.get("bindings", [])
                    if type(verified_binding) is dict
                    else []
                ),
                "semantic_atom_count": len(
                    parsed_witness.get("semantic_atoms", [])
                    if type(parsed_witness) is dict
                    else []
                ),
                "section_count": len(sections) if type(sections) is list else -1,
                "sentence_count": sum(
                    len(section.get("sentences", []))
                    for section in sections
                    if type(section) is dict
                    and type(section.get("sentences")) is list
                )
                if type(sections) is list
                else -1,
                "depth": (
                    content_plan.get("depth")
                    if type(content_plan) is dict
                    else None
                ),
            }
            if row_runtime_summary.get("semantic_metrics") != expected_metrics:
                issues.add("PRIVATE_PACKET_SEMANTIC_METRICS_MISMATCH")
        if (
            authority.observation_stage != "normal_observation"
            or authority.commitment_policy_sha256
            != body_free_summary.get("commitment_policy_sha256")
            or authority.source_dependency_closure_sha256
            != body_free_summary.get("source_dependency_closure_sha256")
            or not _valid_nonzero_sha(authority.environment_sha256)
            or not _valid_nonzero_sha(authority.runner_sha256)
            or not _valid_nonzero_sha(authority.rubric_sha256)
        ):
            issues.add("PRIVATE_PACKET_AUTHORITY_LINEAGE_MISMATCH")
        if validate_historical_step10_case_evidence_receipt(
            receipt,
            authority=authority,
        ):
            issues.add("PRIVATE_PACKET_RECEIPT_CONTRACT_INVALID")
    return tuple(sorted(issues))


def build_output_diff(
    previous: Mapping[str, Any],
    current: Mapping[str, Any],
) -> dict[str, Any]:
    if (
        validate_historical_batch_run_summary(previous)
        or validate_historical_batch_run_summary(current)
    ):
        raise Step10EvidenceError("OUTPUT_DIFF_PARENT_INVALID")
    if previous.get("commitment_policy_sha256") != current.get("commitment_policy_sha256"):
        raise Step10EvidenceError("OUTPUT_DIFF_COMMITMENT_POLICY_MISMATCH")
    if previous.get("commitment_key_id") != current.get("commitment_key_id"):
        raise Step10EvidenceError("OUTPUT_DIFF_COMMITMENT_KEY_MISMATCH")
    if previous.get("batch_id") != current.get("batch_id"):
        raise Step10EvidenceError("OUTPUT_DIFF_BATCH_MISMATCH")
    if previous.get("batch_manifest_sha256") != current.get("batch_manifest_sha256"):
        raise Step10EvidenceError("OUTPUT_DIFF_MANIFEST_MISMATCH")
    if previous.get("run_id") == current.get("run_id"):
        raise Step10EvidenceError("OUTPUT_DIFF_RUN_ID_REUSE")
    before = {row["case_id"]: row for row in previous["case_rows"]}
    after = {row["case_id"]: row for row in current["case_rows"]}
    rows: list[dict[str, Any]] = []
    for case_id in sorted(set(before) | set(after)):
        left = before.get(case_id)
        right = after.get(case_id)
        left_commitment = (
            left.get("receipt", {}).get("selected_candidate_body_commitment")
            if type(left) is dict and type(left.get("receipt")) is dict
            else None
        )
        right_commitment = (
            right.get("receipt", {}).get("selected_candidate_body_commitment")
            if type(right) is dict and type(right.get("receipt")) is dict
            else None
        )
        left_identity = (
            left.get("receipt", {}).get("case_identity_commitment")
            if type(left) is dict and type(left.get("receipt")) is dict
            else left.get("case_identity_commitment") if type(left) is dict else None
        )
        right_identity = (
            right.get("receipt", {}).get("case_identity_commitment")
            if type(right) is dict and type(right.get("receipt")) is dict
            else right.get("case_identity_commitment") if type(right) is dict else None
        )
        if left is not None and right is not None and left_identity != right_identity:
            raise Step10EvidenceError("OUTPUT_DIFF_CASE_IDENTITY_MISMATCH")
        rows.append(
            {
                "case_id": case_id,
                "previous_body_commitment": left_commitment,
                "current_body_commitment": right_commitment,
                "previous_status": left.get("status") if left else None,
                "current_status": right.get("status") if right else None,
                "changed": left_commitment != right_commitment,
            }
        )
    result = {
        "schema_version": OUTPUT_DIFF_SCHEMA,
        "previous_run_id": previous["run_id"],
        "current_run_id": current["run_id"],
        "previous_candidate_version_id": previous["candidate_version_id"],
        "current_candidate_version_id": current["candidate_version_id"],
        "previous_batch_summary_sha256": artifact_sha256(previous),
        "current_batch_summary_sha256": artifact_sha256(current),
        "commitment_policy_sha256": current["commitment_policy_sha256"],
        "commitment_key_id": current["commitment_key_id"],
        "batch_id": current["batch_id"],
        "batch_manifest_sha256": current["batch_manifest_sha256"],
        "previous_source_dependency_closure_sha256": previous[
            "source_dependency_closure_sha256"
        ],
        "current_source_dependency_closure_sha256": current[
            "source_dependency_closure_sha256"
        ],
        "case_rows": rows,
        "aggregate": {
            "case_count": len(rows),
            "changed_count": sum(row["changed"] for row in rows),
            "unchanged_count": sum(not row["changed"] for row in rows),
        },
        "body_free": True,
    }
    assert_body_free(result)
    return result


def build_cumulative_run_manifest(
    batch_summaries: Sequence[Mapping[str, Any]],
    *,
    expected_case_ids_by_batch: Mapping[str, Sequence[str]],
    expected_batch_manifest_sha256_by_batch: Mapping[str, str] | None = None,
    cumulative_run_id: str,
) -> dict[str, Any]:
    start_closure = fresh_step10_source_closure_sha256()
    if type(batch_summaries) not in {list, tuple} or not batch_summaries:
        raise Step10EvidenceError("CUMULATIVE_BATCH_SUMMARIES_REQUIRED")
    if type(cumulative_run_id) is not str or _CUMULATIVE_RUN_RE.fullmatch(cumulative_run_id) is None:
        raise Step10EvidenceError("CUMULATIVE_RUN_ID_INVALID")
    if type(expected_case_ids_by_batch) is not dict or not expected_case_ids_by_batch:
        raise Step10EvidenceError("CUMULATIVE_EXPECTED_CASES_REQUIRED")
    if any(type(item) is not dict for item in batch_summaries):
        raise Step10EvidenceError("CUMULATIVE_BATCH_SUMMARY_INVALID")
    summaries = sorted(batch_summaries, key=lambda item: str(item.get("batch_id", "")))
    if any(validate_batch_run_summary(item) for item in summaries):
        raise Step10EvidenceError("CUMULATIVE_BATCH_SUMMARY_INVALID")
    summary_batch_ids = [item["batch_id"] for item in summaries]
    if len(summary_batch_ids) != len(set(summary_batch_ids)):
        raise Step10EvidenceError("CUMULATIVE_BATCH_ID_DUPLICATE")
    candidate_ids = {item["candidate_version_id"] for item in summaries}
    if len(candidate_ids) != 1:
        raise Step10EvidenceError("CUMULATIVE_CANDIDATE_VERSION_MISMATCH")
    commitment_key_ids = {item["commitment_key_id"] for item in summaries}
    if len(commitment_key_ids) != 1:
        raise Step10EvidenceError("CUMULATIVE_COMMITMENT_KEY_MISMATCH")
    actual_by_batch = {
        item["batch_id"]: [row["case_id"] for row in item["case_rows"]]
        for item in summaries
    }
    expected: dict[str, list[str]] = {}
    for batch, ids in sorted(expected_case_ids_by_batch.items()):
        if (
            type(batch) is not str
            or _BATCH_RE.fullmatch(batch) is None
            or type(ids) not in {list, tuple}
            or not ids
            or any(type(case_id) is not str or _CASE_RE.fullmatch(case_id) is None for case_id in ids)
            or len(ids) != len(set(ids))
        ):
            raise Step10EvidenceError("CUMULATIVE_EXPECTED_CASE_SET_INVALID")
        expected[batch] = sorted(ids)
    expected_flat = [case_id for ids in expected.values() for case_id in ids]
    if len(expected_flat) != len(set(expected_flat)):
        raise Step10EvidenceError("CUMULATIVE_EXPECTED_CASE_ID_DUPLICATE")
    all_expected = actual_by_batch == expected
    rows = [row for item in summaries for row in item["case_rows"]]
    actual_flat = [row["case_id"] for row in rows]
    if len(actual_flat) != len(set(actual_flat)):
        raise Step10EvidenceError("CUMULATIVE_ACTUAL_CASE_ID_DUPLICATE")
    manifest_bound = False
    if expected_batch_manifest_sha256_by_batch is not None:
        if (
            type(expected_batch_manifest_sha256_by_batch) is not dict
            or set(expected_batch_manifest_sha256_by_batch) != set(expected)
            or any(
                type(batch) is not str or not _valid_sha(value)
                for batch, value in expected_batch_manifest_sha256_by_batch.items()
            )
        ):
            raise Step10EvidenceError("CUMULATIVE_MANIFEST_BINDING_INVALID")
        manifest_bound = all(
            item["batch_manifest_sha256"]
            == expected_batch_manifest_sha256_by_batch[item["batch_id"]]
            for item in summaries
        )
    aggregate = _aggregate(rows)
    machine_clean = bool(
        all_expected
        and manifest_bound
        and len(rows) == len(expected_flat)
        and all(
            item["machine_status"] == "clean"
            and item["all_expected_cases_executed"] is True
            for item in summaries
        )
        and aggregate["selected_count"] == len(rows)
        and aggregate["exception_count"] == 0
        and aggregate["no_valid_candidate_count"] == 0
        and aggregate["v1_fallback_count"] == 0
    )
    end_closure = fresh_step10_source_closure_sha256()
    closure_stable = bool(
        start_closure == end_closure == FROZEN_STEP10_DEPENDENCY_CLOSURE_SHA256
    )
    result = {
        "schema_version": CUMULATIVE_RUN_SCHEMA,
        "candidate_version_id": next(iter(candidate_ids)),
        "cumulative_run_id": cumulative_run_id,
        "batch_ids": sorted(actual_by_batch),
        "commitment_key_id": next(iter(commitment_key_ids)),
        "batch_summary_sha256s": [
            {"batch_id": item["batch_id"], "sha256": artifact_sha256(item)}
            for item in summaries
        ],
        "expected_case_count": sum(len(ids) for ids in expected.values()),
        "executed_case_count": len(rows),
        "all_expected_cases_executed": all_expected,
        "batch_manifest_bindings_verified": manifest_bound,
        "source_closure_start_sha256": start_closure,
        "source_closure_end_sha256": end_closure,
        "source_closure_stable": closure_stable,
        "aggregate": aggregate,
        "formal_status": (
            "step10_ready_for_step11"
            if machine_clean and closure_stable
            else "incomplete_or_failed"
        ),
        "batch_acceptance_claimed": False,
        "next_step_authority": "step11_cycle001_initial_run_only",
        "body_free": True,
    }
    assert_body_free(result)
    return result


def build_change_ledger_row(
    *,
    before_source_closure_sha256: str,
    failure_case_commitment: str,
    failure_layer: str,
    severity: str,
    failure_code: str,
    shared_structural_hypothesis_sha256: str,
    changed_file_hashes: Sequence[Mapping[str, str]],
    case_specific_workaround_check_sha256: str,
    after_source_closure_sha256: str,
    cumulative_rerun_receipt_sha256: str,
    new_batch_first_run_receipt_sha256: str,
    decision: str,
) -> dict[str, Any]:
    hashes = (
        before_source_closure_sha256,
        failure_case_commitment,
        shared_structural_hypothesis_sha256,
        case_specific_workaround_check_sha256,
        after_source_closure_sha256,
        cumulative_rerun_receipt_sha256,
        new_batch_first_run_receipt_sha256,
    )
    if any(not _valid_nonzero_sha(value) for value in hashes):
        raise Step10EvidenceError("CHANGE_LEDGER_HASH_INVALID")
    if failure_layer not in {
        "source", "obligation", "content", "discourse", "ast", "renderer",
        "parser", "matcher", "hard_gate", "selector", "runtime", "evidence",
    }:
        raise Step10EvidenceError("CHANGE_LEDGER_LAYER_INVALID")
    if severity not in {"BLOCKER", "MAJOR", "MINOR", "NOTE"}:
        raise Step10EvidenceError("CHANGE_LEDGER_SEVERITY_INVALID")
    if failure_code not in CHANGE_LEDGER_FAILURE_CODES:
        raise Step10EvidenceError("CHANGE_LEDGER_FAILURE_CODE_INVALID")
    if decision not in {"accepted", "rejected"}:
        raise Step10EvidenceError("CHANGE_LEDGER_DECISION_INVALID")
    normalized_files = sorted(
        (dict(row) for row in changed_file_hashes), key=lambda row: row.get("path", "")
    )
    if not normalized_files or any(
        set(row) != {"path", "sha256"}
        or type(row["path"]) is not str
        or Path(row["path"]).is_absolute()
        or ".." in Path(row["path"]).parts
        or not _valid_nonzero_sha(row["sha256"])
        for row in normalized_files
    ) or len({row["path"] for row in normalized_files}) != len(normalized_files):
        raise Step10EvidenceError("CHANGE_LEDGER_FILE_HASH_INVALID")
    value = {
        "schema_version": CHANGE_LEDGER_SCHEMA,
        "before_source_closure_sha256": before_source_closure_sha256,
        "failure_case_commitment": failure_case_commitment,
        "failure_layer": failure_layer,
        "severity": severity,
        "failure_code": failure_code,
        "shared_structural_hypothesis_sha256": shared_structural_hypothesis_sha256,
        "changed_file_hashes": normalized_files,
        "case_specific_workaround_forbidden_check": {
            "status": "passed",
            "evidence_sha256": case_specific_workaround_check_sha256,
        },
        "after_source_closure_sha256": after_source_closure_sha256,
        "cumulative_rerun_receipt_sha256": cumulative_rerun_receipt_sha256,
        "new_batch_first_run_receipt_sha256": (
            new_batch_first_run_receipt_sha256
        ),
        "decision": decision,
        "body_free": True,
    }
    assert_body_free(value)
    return value


__all__ = [
    "BATCH_RUN_SCHEMA",
    "CHANGE_LEDGER_SCHEMA",
    "COMMITMENT_POLICY",
    "COMMITMENT_POLICY_SHA256",
    "CUMULATIVE_RUN_SCHEMA",
    "CaseEvidenceBundle",
    "FAILURE_TAXONOMY",
    "FAILURE_TAXONOMY_SHA256",
    "FROZEN_RECEIPT_V3_COMMITMENT_POLICY_SHA256",
    "FROZEN_RECEIPT_V3_DOMAIN_PREFIX",
    "FROZEN_RECEIPT_V3_HARD_GATE_FAILURE_CODES",
    "FROZEN_RECEIPT_V3_LOCAL_REVIEW_FAILURE_CODES",
    "FROZEN_RECEIPT_V3_LOCAL_REVIEW_PASS_CODES",
    "HARD_GATE_FAILURE_CODES",
    "LOCAL_REVIEW_AXES",
    "LOCAL_REVIEW_FAILURE_CODES",
    "LOCAL_REVIEW_PASS_CODES",
    "LOCAL_REVIEW_RUBRIC",
    "LOCAL_REVIEW_RUBRIC_SHA256",
    "LOCAL_REVIEW_SCHEMA",
    "OUTPUT_DIFF_SCHEMA",
    "PRIVATE_PACKET_SCHEMA",
    "RUNTIME_VALIDATION_PROTOCOL",
    "RUNTIME_VALIDATION_PROTOCOL_SHA256",
    "RUNNER_CASE_FAILURE_CODES",
    "STEP10_RECEIPT_SCHEMA",
    "Step10EvidenceError",
    "assert_body_free",
    "build_batch_evidence",
    "build_case_evidence",
    "build_change_ledger_row",
    "build_cumulative_run_manifest",
    "build_local_product_review",
    "build_output_diff",
    "commitment_key_id",
    "hmac_commit_bytes",
    "hmac_commit_json",
    "validate_batch_run_summary",
    "validate_historical_batch_run_summary",
    "validate_historical_step10_case_evidence_receipt",
    "validate_step10_case_evidence_receipt",
    "verify_batch_evidence",
]
