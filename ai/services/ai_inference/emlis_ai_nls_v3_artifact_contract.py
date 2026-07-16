# -*- coding: utf-8 -*-
from __future__ import annotations

"""Closed, offline artifact contracts for Cocolon EmlisAI NLS v3 Step 3.

This module deliberately contains validators and a canonical JSON codec only.
It does not build semantic artifacts, render text, parse text, select a
candidate, or connect NLS v3 to the runtime.  Later owners may emit these
artifacts, but they must not be used as the authority for their validation.
"""

from dataclasses import dataclass
import ast
from functools import wraps
import hashlib
import json
from pathlib import Path
import re
import unicodedata
from typing import Any, Iterable, Mapping, Sequence


STAGE_SCHEMA = "cocolon.emlis.nls_v3.observation_stage_context.v1"
LEDGER_SCHEMA = "cocolon.emlis.nls_v3.semantic_obligation_ledger.v1"
CONTENT_SCHEMA = "cocolon.emlis.nls_v3.content_selection_plan.v1"
DISCOURSE_SCHEMA = "cocolon.emlis.nls_v3.discourse_plan.v1"
AST_SCHEMA = "cocolon.emlis.nls_v3.surface_ast.v1"
WITNESS_SCHEMA = "cocolon.emlis.nls_v3.parsed_surface_witness.v1"
BINDING_SCHEMA = "cocolon.emlis.nls_v3.verified_surface_binding.v1"
RECEIPT_SCHEMA = "cocolon.emlis.nls_v3.case_evidence_receipt.v2"

STOPPED_V2_MODULES = frozenset(
    {
        "emlis_ai_grounded_reception_content_plan_v2",
        "emlis_ai_grounded_reception_candidate_plan_v2",
        "emlis_ai_grounded_human_reception_v2",
        "emlis_ai_grounded_reception_candidate_selector_v2",
    }
)
FORBIDDEN_CORE_IMPORTS = STOPPED_V2_MODULES | frozenset({"emlis_ai_reply_service"})

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_MACHINE_ID_RE = re.compile(r"^[a-z][a-z0-9_]{1,63}$")
_MACHINE_CODE_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,63}$")
_ID_PATTERNS = {
    "ledger_id": re.compile(r"^nls3obl_[0-9a-f]{16}$"),
    "obligation_id": re.compile(r"^obl_[0-9a-f]{16}$"),
    "content_plan_id": re.compile(r"^nls3cp_[0-9a-f]{16}$"),
    "discourse_plan_id": re.compile(r"^nls3dp_[0-9a-f]{16}$"),
    "structural_signature": re.compile(r"^nls3sig_[0-9a-f]{16}$"),
    "surface_ast_id": re.compile(r"^nls3ast_[0-9a-f]{16}$"),
    "node_id": re.compile(r"^dn_[0-9a-z_]{1,32}$"),
    "sentence_group_id": re.compile(r"^sg_[0-9a-z_]{1,32}$"),
    "clause_id": re.compile(r"^cl_[0-9a-z_]{1,32}$"),
    "atom_id": re.compile(r"^atom_[0-9a-z_]{1,32}$"),
    "run_id": re.compile(r"^nls3run_[0-9a-f]{16,64}$"),
    "batch_id": re.compile(r"^nls3_batch_[0-9]{3}$"),
    "candidate_version_id": re.compile(r"^nls_v3_rc_[0-9]{4}$"),
}

OBSERVATION_STAGES = frozenset(
    {"normal_observation", "pre_question_observation", "refined_observation"}
)
OBLIGATION_KINDS = frozenset(
    {
        "grounded_nucleus_notice",
        "grounded_relation_preservation",
        "unknown_boundary_preservation",
        "significance_or_shift",
        "intention_or_next_action",
        "self_denial_boundary",
        "bounded_counterposition",
        "bound_emlis_reception",
    }
)
STANCE_KIND = "bound_emlis_reception"
POLARITIES = frozenset({"positive", "negative", "mixed", "neutral", "unknown"})
MODALITIES = frozenset({"observed", "reported", "intended", "possible", "unknown"})
TEMPORAL_SCOPES = frozenset(
    {"current_input", "reported_past", "intended_future", "atemporal", "unknown"}
)
REFERENT_SCOPES = frozenset(
    {"self", "other", "event", "action", "state", "relation", "unknown"}
)
ALLOWED_SOURCE_OWNERS = (
    "nuclei",
    "relations",
    "unknown_boundaries",
    "safety_policy",
    "human_reception_plan.opportunities",
)
SOURCE_AUTHORITY_CODES = frozenset(
    {"nucleus", "relation", "unknown_boundary", "safety_policy", "reception_opportunity"}
)
RESPONSE_ACTS = frozenset(
    {
        "notice",
        "preserve_relation",
        "preserve_unknown",
        "mark_shift",
        "honor_action",
        "separate_self_denial",
        "bounded_counterposition",
        "hold_in_attention",
        "do_not_dismiss",
        "receive_without_deciding",
        "honor_concrete_action",
        "stay_with_mixed_meaning",
    }
)
RECEPTION_ACTS = frozenset(
    {
        "hold_in_attention",
        "do_not_dismiss",
        "receive_without_deciding",
        "honor_concrete_action",
        "stay_with_mixed_meaning",
    }
)


@dataclass(frozen=True, order=True)
class ContractIssue:
    code: str
    path: str


@dataclass(frozen=True)
class TrustedFutureStageAuthority:
    """Resolved authority supplied by the future question-system adapter.

    Merely copying these values into the stage artifact does not create
    authority: validation requires this separate trusted object.
    """

    authority_owner: str
    question_need_decision_sha256: str
    permitted_stages: tuple[str, ...]
    original_input_bundle_sha256: str
    supplemental_answer_bundle_sha256: str | None


@dataclass(frozen=True)
class TrustedSourceSemantic:
    """A source-owner fact resolved independently from an obligation builder."""

    source_id: str
    source_authority_code: str
    source_role: str
    polarity: str
    modality: str
    temporal_scope: str
    topic_scope_ids: tuple[str, ...]
    referent_scope: str
    relation_type: str | None
    relation_direction: str | None


@dataclass(frozen=True)
class LedgerSourceAuthority:
    """Resolved upstream lineage and source-ID index for ledger validation."""

    source_observation_plan_sha256: str
    source_observation_stage_context_sha256: str
    source_reception_opportunity_plan_sha256: str | None
    response_eligibility_source_sha256: str
    response_eligibility: str
    source_policy_sha256: str
    allowed_source_owners: tuple[str, ...]
    evidence_ids: frozenset[str]
    nucleus_ids: frozenset[str]
    relation_ids: frozenset[str]
    unknown_boundary_ids: frozenset[str]
    reception_opportunity_ids: frozenset[str]
    topic_scope_ids: frozenset[str]
    allowed_source_roles: tuple[str, ...]
    source_role_bindings: tuple[tuple[str, str], ...]
    source_semantics: tuple[TrustedSourceSemantic, ...]
    obligation_inventory_max: int


@dataclass(frozen=True)
class ReceiptLineageAuthority:
    """Body-free values resolved independently by the Step 10 runner owner."""

    observation_stage: str
    commitment_policy_sha256: str
    source_dependency_closure_sha256: str
    observation_stage_context_commitment: str
    source_observation_plan_commitment: str
    obligation_ledger_commitment: str
    content_plan_commitment: str
    candidate_set_commitment: str
    selected_discourse_plan_commitment: str
    selected_surface_ast_commitment: str
    selected_candidate_body_commitment: str
    parsed_witness_binding_commitment: str
    v1_baseline_body_commitment: str
    previous_output_commitment: str | None
    previous_output_changed: bool | None
    environment_sha256: str
    runner_sha256: str
    rubric_sha256: str


def _normalise_json(value: Any, path: str = "$") -> Any:
    if value is None or type(value) in {bool, int}:
        return value
    if type(value) is str:
        try:
            value.encode("utf-8", errors="strict")
        except UnicodeEncodeError as exc:
            raise ValueError(f"NON_UTF8_SCALAR:{path}") from exc
        return unicodedata.normalize("NFC", value.replace("\r\n", "\n").replace("\r", "\n"))
    if type(value) is list:
        return [_normalise_json(item, f"{path}[{index}]") for index, item in enumerate(value)]
    if type(value) is dict:
        result: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"NON_STRING_KEY:{path}")
            normalised_key = _normalise_json(key, f"{path}.<key>")
            if normalised_key in result:
                raise ValueError(f"NORMALIZED_KEY_COLLISION:{path}.{normalised_key}")
            result[normalised_key] = _normalise_json(item, f"{path}.{normalised_key}")
        return result
    raise ValueError(f"NON_JSON_TYPE:{path}:{type(value).__name__}")


def canonical_json_bytes(value: Any) -> bytes:
    """Return the sole canonical JSON representation for active NLS v3 artifacts.

    The representation is UTF-8, NFC, LF-normalised, key-sorted and compact.
    It intentionally has no trailing LF; file writers add exactly one LF.
    """

    try:
        normalised = _normalise_json(value)
        return json.dumps(
            normalised,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8", errors="strict")
    except RecursionError as exc:
        raise ValueError("CANONICAL_NESTING_OR_CYCLE_FORBIDDEN") from exc


def load_canonical_json_bytes(payload: bytes) -> Any:
    """Load a canonical JSON file (exactly one trailing LF)."""

    if type(payload) is not bytes:
        raise ValueError("CANONICAL_PAYLOAD_NOT_BYTES")
    if payload.startswith(b"\xef\xbb\xbf"):
        raise ValueError("CANONICAL_BOM_FORBIDDEN")
    if b"\r" in payload:
        raise ValueError("CANONICAL_CR_FORBIDDEN")
    if not payload.endswith(b"\n") or payload.endswith(b"\n\n"):
        raise ValueError("CANONICAL_FINAL_LF_REQUIRED")
    try:
        text = payload[:-1].decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError("CANONICAL_UTF8_REQUIRED") from exc

    def reject_constant(value: str) -> Any:
        raise ValueError(f"CANONICAL_NONFINITE_FORBIDDEN:{value}")

    def closed_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"CANONICAL_DUPLICATE_KEY:{key}")
            result[key] = value
        return result

    try:
        value = json.loads(text, parse_constant=reject_constant, object_pairs_hook=closed_object)
    except json.JSONDecodeError as exc:
        raise ValueError("CANONICAL_JSON_INVALID") from exc
    except RecursionError as exc:
        raise ValueError("CANONICAL_NESTING_OR_CYCLE_FORBIDDEN") from exc
    if canonical_json_bytes(value) + b"\n" != payload:
        raise ValueError("CANONICAL_BYTES_MISMATCH")
    return value


def artifact_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def derive_content_id(prefix: str, value: Mapping[str, Any], id_field: str) -> str:
    if type(value) is not dict:
        raise ValueError("DERIVED_ID_SOURCE_NOT_OBJECT")
    payload = {key: item for key, item in value.items() if key != id_field}
    return prefix + artifact_sha256(payload)[:16]


def derive_obligation_id(value: Mapping[str, Any]) -> str:
    """Derive an obligation ID without a cyclic must-not-merge dependency.

    Cross-obligation separation references are secured by the ledger ID.  The
    obligation's intrinsic ID canonicalises that reference list to empty, so a
    symmetric A<->B separation constraint remains constructible.
    """

    if type(value) is not dict:
        raise ValueError("DERIVED_ID_SOURCE_NOT_OBJECT")
    payload = {key: item for key, item in value.items() if key != "obligation_id"}
    payload["must_not_merge_with"] = []
    return "obl_" + artifact_sha256(payload)[:16]


def issue_codes(issues: Iterable[ContractIssue]) -> tuple[str, ...]:
    return tuple(issue.code for issue in issues)


def _add(issues: list[ContractIssue], code: str, path: str) -> None:
    issue = ContractIssue(code, path)
    if issue not in issues:
        issues.append(issue)


def _object(
    value: Any,
    keys: Iterable[str],
    path: str,
    issues: list[ContractIssue],
) -> dict[str, Any] | None:
    if type(value) is not dict:
        _add(issues, "OBJECT_REQUIRED", path)
        return None
    expected = set(keys)
    actual: set[str] = set()
    for key in value:
        if type(key) is not str:
            _add(issues, "NON_STRING_KEY", path)
        else:
            actual.add(key)
    for key in sorted(actual - expected):
        _add(issues, "UNKNOWN_FIELD", f"{path}.{key}")
    for key in sorted(expected - actual):
        _add(issues, "MISSING_FIELD", f"{path}.{key}")
    return value


def _string(
    value: Any,
    path: str,
    issues: list[ContractIssue],
    *,
    pattern: re.Pattern[str] | None = None,
    allow_empty: bool = False,
) -> str | None:
    if type(value) is not str:
        _add(issues, "STRING_REQUIRED", path)
        return None
    if not allow_empty and not value:
        _add(issues, "EMPTY_STRING_FORBIDDEN", path)
    if value != unicodedata.normalize("NFC", value.replace("\r\n", "\n").replace("\r", "\n")):
        _add(issues, "NON_CANONICAL_STRING", path)
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeEncodeError:
        _add(issues, "NON_UTF8_SCALAR", path)
    if pattern is not None and not pattern.fullmatch(value):
        _add(issues, "PATTERN_MISMATCH", path)
    return value


def _sha(value: Any, path: str, issues: list[ContractIssue], *, nullable: bool = False) -> str | None:
    if nullable and value is None:
        return None
    return _string(value, path, issues, pattern=_SHA256_RE)


def _enum(value: Any, allowed: Iterable[str], path: str, issues: list[ContractIssue]) -> str | None:
    result = _string(value, path, issues)
    if result is not None and result not in set(allowed):
        _add(issues, "ENUM_INVALID", path)
    return result


def _bool(value: Any, path: str, issues: list[ContractIssue]) -> bool | None:
    if type(value) is not bool:
        _add(issues, "STRICT_BOOL_REQUIRED", path)
        return None
    return value


def _int(
    value: Any,
    path: str,
    issues: list[ContractIssue],
    *,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int | None:
    if type(value) is not int:
        _add(issues, "STRICT_INTEGER_REQUIRED", path)
        return None
    if minimum is not None and value < minimum:
        _add(issues, "RANGE_INVALID", path)
    if maximum is not None and value > maximum:
        _add(issues, "RANGE_INVALID", path)
    return value


def _list(value: Any, path: str, issues: list[ContractIssue], *, minimum: int = 0) -> list[Any] | None:
    if type(value) is not list:
        _add(issues, "ARRAY_REQUIRED", path)
        return None
    if len(value) < minimum:
        _add(issues, "ARRAY_TOO_SHORT", path)
    return value


def _string_list(
    value: Any,
    path: str,
    issues: list[ContractIssue],
    *,
    minimum: int = 0,
    allowed: Iterable[str] | None = None,
    pattern: re.Pattern[str] | None = None,
) -> list[str] | None:
    values = _list(value, path, issues, minimum=minimum)
    if values is None:
        return None
    result: list[str] = []
    allowed_set = set(allowed) if allowed is not None else None
    for index, item in enumerate(values):
        item_path = f"{path}[{index}]"
        parsed = _string(item, item_path, issues, pattern=pattern)
        if parsed is None:
            continue
        if allowed_set is not None and parsed not in allowed_set:
            _add(issues, "ENUM_INVALID", item_path)
        result.append(parsed)
    seen: set[str] = set()
    for index, item in enumerate(result):
        if item in seen:
            _add(issues, "DUPLICATE_VALUE", f"{path}[{index}]")
        seen.add(item)
    return result


def _schema(value: Any, expected: str, path: str, issues: list[ContractIssue]) -> None:
    _string(value, path, issues)
    if value != expected:
        _add(issues, "SCHEMA_VERSION_MISMATCH", path)


def _const(value: Any, expected: Any, path: str, issues: list[ContractIssue]) -> None:
    if type(value) is not type(expected) or value != expected:
        _add(issues, "CONST_MISMATCH", path)


def _parent(value: Any, expected: str | None, path: str, issues: list[ContractIssue]) -> None:
    _sha(value, path, issues, nullable=expected is None)
    if value != expected:
        _add(issues, "PARENT_HASH_MISMATCH", path)


def _derived_id(
    value: Mapping[str, Any], id_field: str, prefix: str, path: str, issues: list[ContractIssue]
) -> None:
    actual = value.get(id_field)
    _string(actual, path, issues, pattern=_ID_PATTERNS[id_field])
    try:
        expected = derive_content_id(prefix, value, id_field)
    except ValueError:
        _add(issues, "DERIVED_ID_SOURCE_INVALID", path)
        return
    if actual != expected:
        _add(issues, "DERIVED_ID_MISMATCH", path)


def _final(issues: list[ContractIssue]) -> tuple[ContractIssue, ...]:
    return tuple(sorted(issues))


def validate_observation_stage_context(
    value: Any,
    *,
    original_input_bundle: Any,
    trusted_future_authority: TrustedFutureStageAuthority | None = None,
    supplemental_answer_bundle: Any | None = None,
) -> tuple[ContractIssue, ...]:
    issues: list[ContractIssue] = []
    obj = _object(
        value,
        {
            "schema_version",
            "stage",
            "original_input_bundle_sha256",
            "question_need_decision_sha256",
            "supplemental_answer_bundle_sha256",
            "allowed_source_roles",
            "body_free",
        },
        "$",
        issues,
    )
    if obj is None:
        return _final(issues)
    _schema(obj.get("schema_version"), STAGE_SCHEMA, "$.schema_version", issues)
    stage = _enum(obj.get("stage"), OBSERVATION_STAGES, "$.stage", issues)
    original_hash = artifact_sha256(original_input_bundle)
    _parent(obj.get("original_input_bundle_sha256"), original_hash, "$.original_input_bundle_sha256", issues)
    roles = _string_list(obj.get("allowed_source_roles"), "$.allowed_source_roles", issues, minimum=1)
    body_free = _bool(obj.get("body_free"), "$.body_free", issues)
    if body_free is not True:
        _add(issues, "BODY_FREE_REQUIRED", "$.body_free")

    expected_roles: list[str] | None = None
    if stage == "normal_observation":
        expected_roles = ["original_input"]
        if obj.get("question_need_decision_sha256") is not None:
            _add(issues, "FUTURE_AUTHORITY_FORBIDDEN", "$.question_need_decision_sha256")
        if obj.get("supplemental_answer_bundle_sha256") is not None:
            _add(issues, "SUPPLEMENTAL_SOURCE_FORBIDDEN", "$.supplemental_answer_bundle_sha256")
        _sha(obj.get("question_need_decision_sha256"), "$.question_need_decision_sha256", issues, nullable=True)
        _sha(obj.get("supplemental_answer_bundle_sha256"), "$.supplemental_answer_bundle_sha256", issues, nullable=True)
        if trusted_future_authority is not None or supplemental_answer_bundle is not None:
            _add(issues, "FUTURE_SOURCE_CONTEXT_FORBIDDEN", "$")
    elif stage in {"pre_question_observation", "refined_observation"}:
        expected_roles = (
            ["original_input", "question_need_decision"]
            if stage == "pre_question_observation"
            else ["original_input", "question_need_decision", "supplemental_answer"]
        )
        if trusted_future_authority is None:
            _sha(obj.get("question_need_decision_sha256"), "$.question_need_decision_sha256", issues)
            _add(issues, "FUTURE_STAGE_AUTHORITY_REQUIRED", "$.question_need_decision_sha256")
        else:
            if trusted_future_authority.authority_owner != "question_system_core":
                _add(issues, "FUTURE_STAGE_AUTHORITY_OWNER_INVALID", "$.question_need_decision_sha256")
            permitted = trusted_future_authority.permitted_stages
            if (
                type(permitted) is not tuple
                or len(permitted) != len(set(permitted))
                or not set(permitted) <= {
                    "pre_question_observation",
                    "refined_observation",
                }
            ):
                _add(issues, "FUTURE_STAGE_AUTHORITY_SHAPE_INVALID", "$.question_need_decision_sha256")
                permitted = ()
            if stage not in permitted:
                _add(issues, "FUTURE_STAGE_NOT_AUTHORIZED", "$.stage")
            if not _SHA256_RE.fullmatch(
                trusted_future_authority.question_need_decision_sha256
            ):
                _add(issues, "FUTURE_STAGE_AUTHORITY_SHAPE_INVALID", "$.question_need_decision_sha256")
            if trusted_future_authority.original_input_bundle_sha256 != original_hash:
                _add(issues, "FUTURE_AUTHORITY_SOURCE_MISMATCH", "$.original_input_bundle_sha256")
            _parent(
                obj.get("question_need_decision_sha256"),
                trusted_future_authority.question_need_decision_sha256,
                "$.question_need_decision_sha256",
                issues,
            )
        if stage == "pre_question_observation":
            _sha(obj.get("supplemental_answer_bundle_sha256"), "$.supplemental_answer_bundle_sha256", issues, nullable=True)
            if obj.get("supplemental_answer_bundle_sha256") is not None or supplemental_answer_bundle is not None:
                _add(issues, "SUPPLEMENTAL_SOURCE_FORBIDDEN", "$.supplemental_answer_bundle_sha256")
            if (
                trusted_future_authority is not None
                and trusted_future_authority.supplemental_answer_bundle_sha256
                is not None
            ):
                _add(issues, "FUTURE_STAGE_AUTHORITY_SHAPE_INVALID", "$.supplemental_answer_bundle_sha256")
        else:
            if supplemental_answer_bundle is None:
                _sha(obj.get("supplemental_answer_bundle_sha256"), "$.supplemental_answer_bundle_sha256", issues)
                _add(issues, "SUPPLEMENTAL_SOURCE_REQUIRED", "$.supplemental_answer_bundle_sha256")
            else:
                supplemental_hash = artifact_sha256(supplemental_answer_bundle)
                _parent(
                    obj.get("supplemental_answer_bundle_sha256"),
                    supplemental_hash,
                    "$.supplemental_answer_bundle_sha256",
                    issues,
                )
                if (
                    trusted_future_authority is not None
                    and trusted_future_authority.supplemental_answer_bundle_sha256 != supplemental_hash
                ):
                    _add(issues, "FUTURE_AUTHORITY_SUPPLEMENT_MISMATCH", "$.supplemental_answer_bundle_sha256")
                if supplemental_hash == original_hash:
                    _add(issues, "SOURCE_ROLE_COLLISION", "$.supplemental_answer_bundle_sha256")
    if expected_roles is not None and roles != expected_roles:
        _add(issues, "SOURCE_ROLE_SET_MISMATCH", "$.allowed_source_roles")
    return _final(issues)


_OBLIGATION_KEYS = {
    "obligation_id",
    "kind",
    "required",
    "evidence_ids",
    "nucleus_ids",
    "relation_ids",
    "unknown_boundary_ids",
    "target_obligation_ids",
    "polarity",
    "modality",
    "temporal_scope",
    "topic_scope_ids",
    "referent_scope",
    "distinctness_group",
    "must_not_merge_with",
    "allowed_response_acts",
    "forbidden_claim_codes",
    "source_authority_codes",
    "reception_opportunity_ids",
    "source_refs",
    "relation_directions",
}
_SOURCE_REF_KEYS = {
    "source_role",
    "evidence_ids",
    "nucleus_ids",
    "relation_ids",
    "unknown_boundary_ids",
    "reception_opportunity_ids",
}


def validate_semantic_obligation_ledger(
    value: Any,
    *,
    authority: LedgerSourceAuthority,
) -> tuple[ContractIssue, ...]:
    issues: list[ContractIssue] = []
    obj = _object(
        value,
        {
            "schema_version",
            "ledger_id",
            "source_observation_plan_sha256",
            "source_observation_stage_context_sha256",
            "source_reception_opportunity_plan_sha256",
            "response_eligibility_source_sha256",
            "response_eligibility",
            "source_policy_sha256",
            "allowed_source_owners",
            "obligations",
            "required_obligation_ids",
            "body_free",
        },
        "$",
        issues,
    )
    if obj is None:
        return _final(issues)
    _schema(obj.get("schema_version"), LEDGER_SCHEMA, "$.schema_version", issues)
    _parent(obj.get("source_observation_plan_sha256"), authority.source_observation_plan_sha256, "$.source_observation_plan_sha256", issues)
    _parent(obj.get("source_observation_stage_context_sha256"), authority.source_observation_stage_context_sha256, "$.source_observation_stage_context_sha256", issues)
    _parent(obj.get("source_reception_opportunity_plan_sha256"), authority.source_reception_opportunity_plan_sha256, "$.source_reception_opportunity_plan_sha256", issues)
    _parent(obj.get("response_eligibility_source_sha256"), authority.response_eligibility_source_sha256, "$.response_eligibility_source_sha256", issues)
    eligibility = _enum(obj.get("response_eligibility"), {"normal_surface", "separate_safety_owner", "source_unavailable"}, "$.response_eligibility", issues)
    if eligibility != authority.response_eligibility:
        _add(issues, "UPSTREAM_ELIGIBILITY_MISMATCH", "$.response_eligibility")
    _parent(obj.get("source_policy_sha256"), authority.source_policy_sha256, "$.source_policy_sha256", issues)
    owners = _string_list(obj.get("allowed_source_owners"), "$.allowed_source_owners", issues, minimum=5)
    if owners != list(ALLOWED_SOURCE_OWNERS) or owners != list(authority.allowed_source_owners):
        _add(issues, "SOURCE_OWNER_POLICY_MISMATCH", "$.allowed_source_owners")
    body_free = _bool(obj.get("body_free"), "$.body_free", issues)
    if body_free is not True:
        _add(issues, "BODY_FREE_REQUIRED", "$.body_free")

    if type(authority.allowed_source_roles) is not tuple or not authority.allowed_source_roles:
        _add(issues, "TRUSTED_SOURCE_ROLE_POLICY_INVALID", "$.obligations")
    role_pairs = authority.source_role_bindings
    role_by_id = dict(role_pairs)
    if len(role_by_id) != len(role_pairs):
        _add(issues, "TRUSTED_SOURCE_ROLE_POLICY_INVALID", "$.obligations")
    semantic_by_id = {fact.source_id: fact for fact in authority.source_semantics}
    expected_semantic_ids = (
        authority.nucleus_ids
        | authority.relation_ids
        | authority.unknown_boundary_ids
    )
    if len(semantic_by_id) != len(authority.source_semantics) or set(
        semantic_by_id
    ) != expected_semantic_ids:
        _add(issues, "TRUSTED_SOURCE_SEMANTIC_POLICY_INVALID", "$.obligations")
    expected_role_ids = (
        authority.evidence_ids
        | expected_semantic_ids
        | authority.reception_opportunity_ids
    )
    if set(role_by_id) != expected_role_ids or not set(role_by_id.values()) <= set(
        authority.allowed_source_roles
    ):
        _add(issues, "TRUSTED_SOURCE_ROLE_POLICY_INVALID", "$.obligations")

    rows = _list(obj.get("obligations"), "$.obligations", issues, minimum=1)
    parsed_rows: list[dict[str, Any]] = []
    ids: list[str] = []
    reception_opportunity_used = False
    if rows is not None:
        if type(authority.obligation_inventory_max) is not int or authority.obligation_inventory_max < 1:
            _add(issues, "TRUSTED_RESOURCE_BOUND_INVALID", "$.obligations")
        elif len(rows) > authority.obligation_inventory_max:
            _add(issues, "OBLIGATION_INVENTORY_OVERFLOW", "$.obligations")
        for index, row in enumerate(rows):
            path = f"$.obligations[{index}]"
            item = _object(row, _OBLIGATION_KEYS, path, issues)
            if item is None:
                continue
            parsed_rows.append(item)
            obligation_id = _string(item.get("obligation_id"), f"{path}.obligation_id", issues, pattern=_ID_PATTERNS["obligation_id"])
            if obligation_id is not None:
                ids.append(obligation_id)
            expected_obligation_id = derive_obligation_id(item)
            if item.get("obligation_id") != expected_obligation_id:
                _add(issues, "DERIVED_ID_MISMATCH", f"{path}.obligation_id")
            kind = _enum(item.get("kind"), OBLIGATION_KINDS, f"{path}.kind", issues)
            _bool(item.get("required"), f"{path}.required", issues)
            evidence = _string_list(item.get("evidence_ids"), f"{path}.evidence_ids", issues, pattern=_MACHINE_ID_RE)
            nuclei = _string_list(item.get("nucleus_ids"), f"{path}.nucleus_ids", issues, pattern=_MACHINE_ID_RE)
            relations = _string_list(item.get("relation_ids"), f"{path}.relation_ids", issues, pattern=_MACHINE_ID_RE)
            unknowns = _string_list(item.get("unknown_boundary_ids"), f"{path}.unknown_boundary_ids", issues, pattern=_MACHINE_ID_RE)
            opportunities = _string_list(item.get("reception_opportunity_ids"), f"{path}.reception_opportunity_ids", issues, pattern=_MACHINE_ID_RE)
            _string_list(item.get("target_obligation_ids"), f"{path}.target_obligation_ids", issues, pattern=_ID_PATTERNS["obligation_id"])
            _enum(item.get("polarity"), POLARITIES, f"{path}.polarity", issues)
            _enum(item.get("modality"), MODALITIES, f"{path}.modality", issues)
            _enum(item.get("temporal_scope"), TEMPORAL_SCOPES, f"{path}.temporal_scope", issues)
            topics = _string_list(item.get("topic_scope_ids"), f"{path}.topic_scope_ids", issues, minimum=1, pattern=_MACHINE_ID_RE)
            _enum(item.get("referent_scope"), REFERENT_SCOPES, f"{path}.referent_scope", issues)
            _string(item.get("distinctness_group"), f"{path}.distinctness_group", issues, pattern=_MACHINE_ID_RE)
            _string_list(item.get("must_not_merge_with"), f"{path}.must_not_merge_with", issues, pattern=_ID_PATTERNS["obligation_id"])
            acts = _string_list(item.get("allowed_response_acts"), f"{path}.allowed_response_acts", issues, minimum=1, allowed=RESPONSE_ACTS)
            _string_list(item.get("forbidden_claim_codes"), f"{path}.forbidden_claim_codes", issues, pattern=_MACHINE_CODE_RE)
            sources = _string_list(item.get("source_authority_codes"), f"{path}.source_authority_codes", issues, minimum=1, allowed=SOURCE_AUTHORITY_CODES)
            direction_rows = _list(item.get("relation_directions"), f"{path}.relation_directions", issues)
            direction_by_relation: dict[str, str] = {}
            for direction_index, direction_row in enumerate(direction_rows or []):
                direction_path = f"{path}.relation_directions[{direction_index}]"
                direction_item = _object(direction_row, {"relation_id", "relation_type", "direction"}, direction_path, issues)
                if direction_item is None:
                    continue
                relation_id = _string(direction_item.get("relation_id"), f"{direction_path}.relation_id", issues, pattern=_MACHINE_ID_RE)
                direction = _enum(direction_item.get("direction"), {"source_to_target", "target_to_source", "bidirectional"}, f"{direction_path}.direction", issues)
                relation_type = _enum(direction_item.get("relation_type"), {"precedes", "contrasts_with", "coexists_with", "qualifies", "supports_without_guarantee"}, f"{direction_path}.relation_type", issues)
                if relation_id in direction_by_relation:
                    _add(issues, "DUPLICATE_ID", f"{direction_path}.relation_id")
                elif relation_id is not None and direction is not None and relation_type is not None:
                    direction_by_relation[relation_id] = f"{relation_type}:{direction}"
            if set(direction_by_relation) != set(relations or []):
                _add(issues, "RELATION_DIRECTION_SET_MISMATCH", f"{path}.relation_directions")

            source_ref_rows = _list(item.get("source_refs"), f"{path}.source_refs", issues, minimum=1)
            ref_unions = {
                "evidence_ids": set(),
                "nucleus_ids": set(),
                "relation_ids": set(),
                "unknown_boundary_ids": set(),
                "reception_opportunity_ids": set(),
            }
            seen_source_roles: list[str] = []
            for ref_index, ref_row in enumerate(source_ref_rows or []):
                ref_path = f"{path}.source_refs[{ref_index}]"
                ref_item = _object(ref_row, _SOURCE_REF_KEYS, ref_path, issues)
                if ref_item is None:
                    continue
                source_role = _enum(ref_item.get("source_role"), authority.allowed_source_roles, f"{ref_path}.source_role", issues)
                if source_role is not None:
                    seen_source_roles.append(source_role)
                for ref_field in ref_unions:
                    refs = _string_list(ref_item.get(ref_field), f"{ref_path}.{ref_field}", issues, pattern=_MACHINE_ID_RE)
                    ref_unions[ref_field].update(refs or [])
                    for source_id in refs or []:
                        if role_by_id.get(source_id) != source_role:
                            _add(issues, "SOURCE_ROLE_BINDING_MISMATCH", f"{ref_path}.{ref_field}")
            if len(seen_source_roles) != len(set(seen_source_roles)):
                _add(issues, "DUPLICATE_SOURCE_ROLE", f"{path}.source_refs")
            aggregate_refs = {
                "evidence_ids": set(evidence or []),
                "nucleus_ids": set(nuclei or []),
                "relation_ids": set(relations or []),
                "unknown_boundary_ids": set(unknowns or []),
                "reception_opportunity_ids": set(opportunities or []),
            }
            if ref_unions != aggregate_refs:
                _add(issues, "SOURCE_REF_AGGREGATE_MISMATCH", f"{path}.source_refs")
            if evidence is not None and not set(evidence) <= authority.evidence_ids:
                _add(issues, "UNRESOLVED_EVIDENCE_REFERENCE", f"{path}.evidence_ids")
            if nuclei is not None and not set(nuclei) <= authority.nucleus_ids:
                _add(issues, "UNRESOLVED_NUCLEUS_REFERENCE", f"{path}.nucleus_ids")
            if relations is not None and not set(relations) <= authority.relation_ids:
                _add(issues, "UNRESOLVED_RELATION_REFERENCE", f"{path}.relation_ids")
            if unknowns is not None and not set(unknowns) <= authority.unknown_boundary_ids:
                _add(issues, "UNRESOLVED_UNKNOWN_REFERENCE", f"{path}.unknown_boundary_ids")
            if opportunities is not None and not set(opportunities) <= authority.reception_opportunity_ids:
                _add(issues, "UNRESOLVED_RECEPTION_OPPORTUNITY_REFERENCE", f"{path}.reception_opportunity_ids")
            if topics is not None and not set(topics) <= authority.topic_scope_ids:
                _add(issues, "UNRESOLVED_TOPIC_REFERENCE", f"{path}.topic_scope_ids")
            if kind == "grounded_relation_preservation" and not relations:
                _add(issues, "RELATION_REFERENCE_REQUIRED", f"{path}.relation_ids")
            if kind == "unknown_boundary_preservation" and not unknowns:
                _add(issues, "UNKNOWN_REFERENCE_REQUIRED", f"{path}.unknown_boundary_ids")
            if kind in {
                "grounded_nucleus_notice",
                "significance_or_shift",
                "intention_or_next_action",
                "self_denial_boundary",
                "bounded_counterposition",
            } and not nuclei:
                _add(issues, "NUCLEUS_REFERENCE_REQUIRED", f"{path}.nucleus_ids")
            derived_source_codes = set()
            if nuclei:
                derived_source_codes.add("nucleus")
            if relations:
                derived_source_codes.add("relation")
            if unknowns:
                derived_source_codes.add("unknown_boundary")
            if opportunities:
                derived_source_codes.add("reception_opportunity")
            if sources is not None and (
                not derived_source_codes <= set(sources)
                or not set(sources) <= derived_source_codes | {"safety_policy"}
            ):
                _add(issues, "SOURCE_AUTHORITY_REFERENCE_MISMATCH", f"{path}.source_authority_codes")
            if opportunities:
                reception_opportunity_used = True
            primary_source_ids = (
                relations
                if kind == "grounded_relation_preservation"
                else unknowns
                if kind == "unknown_boundary_preservation"
                else nuclei
            ) or []
            if kind != STANCE_KIND:
                for source_id in primary_source_ids:
                    fact = semantic_by_id.get(source_id)
                    if fact is None:
                        _add(issues, "TRUSTED_SOURCE_SEMANTIC_MISSING", path)
                        continue
                    expected_code = (
                        "relation"
                        if source_id in (relations or [])
                        else "unknown_boundary"
                        if source_id in (unknowns or [])
                        else "nucleus"
                    )
                    if fact.source_authority_code != expected_code or fact.source_role != role_by_id.get(source_id):
                        _add(issues, "TRUSTED_SOURCE_SEMANTIC_MISMATCH", path)
                    for field in (
                        "polarity",
                        "modality",
                        "temporal_scope",
                        "referent_scope",
                    ):
                        if item.get(field) != getattr(fact, field):
                            _add(issues, "SOURCE_SEMANTIC_FEATURE_MISMATCH", f"{path}.{field}")
                    if set(item.get("topic_scope_ids") or []) != set(fact.topic_scope_ids):
                        _add(issues, "SOURCE_SEMANTIC_FEATURE_MISMATCH", f"{path}.topic_scope_ids")
                    if expected_code == "relation" and direction_by_relation.get(source_id) != f"{fact.relation_type}:{fact.relation_direction}":
                        _add(issues, "SOURCE_RELATION_DESCRIPTOR_MISMATCH", f"{path}.relation_directions")
            if kind == STANCE_KIND:
                if not evidence:
                    _add(issues, "BOUND_RECEPTION_EVIDENCE_REQUIRED", f"{path}.evidence_ids")
                targets = item.get("target_obligation_ids")
                if type(targets) is not list or not targets:
                    _add(issues, "BOUND_RECEPTION_TARGET_REQUIRED", f"{path}.target_obligation_ids")
                if acts is not None and not set(acts) & RECEPTION_ACTS:
                    _add(issues, "BOUND_RECEPTION_ACT_REQUIRED", f"{path}.allowed_response_acts")
            elif item.get("target_obligation_ids") != []:
                _add(issues, "NONSTANCE_TARGET_FORBIDDEN", f"{path}.target_obligation_ids")
    for index, obligation_id in enumerate(ids):
        if obligation_id in ids[:index]:
            _add(issues, "DUPLICATE_ID", f"$.obligations[{index}].obligation_id")
    id_set = set(ids)
    by_id = {row.get("obligation_id"): row for row in parsed_rows if type(row.get("obligation_id")) is str}
    for index, row in enumerate(parsed_rows):
        path = f"$.obligations[{index}]"
        if not any(
            row.get(field)
            for field in (
                "evidence_ids",
                "nucleus_ids",
                "relation_ids",
                "unknown_boundary_ids",
            )
        ):
            _add(issues, "SOURCE_REFERENCE_REQUIRED", path)
        for field in ("target_obligation_ids", "must_not_merge_with"):
            refs = row.get(field)
            if type(refs) is list and not set(item for item in refs if type(item) is str) <= id_set:
                _add(issues, "UNRESOLVED_OBLIGATION_REFERENCE", f"{path}.{field}")
        if row.get("obligation_id") in (row.get("must_not_merge_with") or []):
            _add(issues, "SELF_REFERENCE_FORBIDDEN", f"{path}.must_not_merge_with")
        for target in row.get("must_not_merge_with") or []:
            if row.get("obligation_id") not in by_id.get(target, {}).get(
                "must_not_merge_with", []
            ):
                _add(issues, "MUST_NOT_MERGE_ASYMMETRIC", f"{path}.must_not_merge_with")
        if row.get("kind") == STANCE_KIND:
            for target in row.get("target_obligation_ids") or []:
                target_row = by_id.get(target, {})
                if target_row.get("kind") == STANCE_KIND:
                    _add(issues, "STANCE_TARGET_MUST_BE_NONSTANCE", f"{path}.target_obligation_ids")
                if target_row.get("kind") == "grounded_relation_preservation":
                    for field in (
                        "relation_ids",
                        "relation_directions",
                        "polarity",
                        "modality",
                        "temporal_scope",
                        "topic_scope_ids",
                        "referent_scope",
                    ):
                        if row.get(field) != target_row.get(field):
                            _add(issues, "STANCE_RELATION_SCOPE_MISMATCH", f"{path}.{field}")
    required_ids = _string_list(obj.get("required_obligation_ids"), "$.required_obligation_ids", issues, minimum=1)
    expected_required = sorted(
        row["obligation_id"]
        for row in parsed_rows
        if row.get("required") is True and type(row.get("obligation_id")) is str
    )
    if required_ids is not None and sorted(required_ids) != expected_required:
        _add(issues, "REQUIRED_SET_MISMATCH", "$.required_obligation_ids")
    visible = eligibility in {"normal_surface", "source_unavailable"}
    if visible and not any(row.get("kind") == STANCE_KIND for row in parsed_rows):
        _add(issues, "BOUND_RECEPTION_REQUIRED", "$.obligations")
    if reception_opportunity_used != (authority.source_reception_opportunity_plan_sha256 is not None):
        _add(issues, "RECEPTION_PLAN_LINEAGE_MISMATCH", "$.source_reception_opportunity_plan_sha256")
    _derived_id(obj, "ledger_id", "nls3obl_", "$.ledger_id", issues)
    return _final(issues)


def validate_content_selection_plan(
    value: Any,
    *,
    obligation_ledger: Mapping[str, Any],
) -> tuple[ContractIssue, ...]:
    issues: list[ContractIssue] = []
    obj = _object(
        value,
        {
            "schema_version",
            "content_plan_id",
            "source_obligation_ledger_sha256",
            "depth",
            "section_budget",
            "decisions",
            "required_coverage_obligation_ids",
            "body_free",
        },
        "$",
        issues,
    )
    if obj is None:
        return _final(issues)
    _schema(obj.get("schema_version"), CONTENT_SCHEMA, "$.schema_version", issues)
    _parent(obj.get("source_obligation_ledger_sha256"), artifact_sha256(obligation_ledger), "$.source_obligation_ledger_sha256", issues)
    if (
        type(obligation_ledger) is not dict
        or obligation_ledger.get("schema_version") != LEDGER_SCHEMA
        or obligation_ledger.get("body_free") is not True
    ):
        _add(issues, "PARENT_ARTIFACT_INVALID", "$.source_obligation_ledger_sha256")
    _enum(obj.get("depth"), {"minimal", "focused", "layered"}, "$.depth", issues)
    body_free = _bool(obj.get("body_free"), "$.body_free", issues)
    if body_free is not True:
        _add(issues, "BODY_FREE_REQUIRED", "$.body_free")
    budget = _object(
        obj.get("section_budget"),
        {
            "observation_sentence_min",
            "observation_sentence_max",
            "reception_sentence_min",
            "reception_sentence_max",
            "total_sentence_max",
        },
        "$.section_budget",
        issues,
    )
    if budget is not None:
        for key in budget:
            _int(budget[key], f"$.section_budget.{key}", issues, minimum=1, maximum=5)
        if type(budget.get("observation_sentence_min")) is int and type(budget.get("observation_sentence_max")) is int and budget["observation_sentence_min"] > budget["observation_sentence_max"]:
            _add(issues, "BUDGET_RANGE_INVALID", "$.section_budget.observation_sentence_min")
        if type(budget.get("reception_sentence_min")) is int and type(budget.get("reception_sentence_max")) is int and budget["reception_sentence_min"] > budget["reception_sentence_max"]:
            _add(issues, "BUDGET_RANGE_INVALID", "$.section_budget.reception_sentence_min")
        maxima = budget.get("observation_sentence_max"), budget.get("reception_sentence_max")
        if all(type(item) is int for item in maxima) and type(budget.get("total_sentence_max")) is int and budget["total_sentence_max"] > sum(maxima):
            _add(issues, "BUDGET_RANGE_INVALID", "$.section_budget.total_sentence_max")
        minima = budget.get("observation_sentence_min"), budget.get("reception_sentence_min")
        if all(type(item) is int for item in minima) and type(budget.get("total_sentence_max")) is int and budget["total_sentence_max"] < sum(minima):
            _add(issues, "BUDGET_RANGE_INVALID", "$.section_budget.total_sentence_max")

    ledger_rows = obligation_ledger.get("obligations") if type(obligation_ledger) is dict else None
    ledger_by_id = {
        row.get("obligation_id"): row
        for row in ledger_rows or []
        if type(row) is dict and type(row.get("obligation_id")) is str
    }
    if type(ledger_rows) is not list or len(ledger_by_id) != len(ledger_rows):
        _add(issues, "PARENT_ARTIFACT_INVALID", "$.source_obligation_ledger_sha256")
    rows = _list(obj.get("decisions"), "$.decisions", issues, minimum=1)
    decisions: list[dict[str, Any]] = []
    decision_ids: list[str] = []
    statuses = {"selected", "integrated_into", "deferred_by_budget", "omitted_redundant", "blocked_by_safety", "unrealizable"}
    if rows is not None:
        for index, row in enumerate(rows):
            path = f"$.decisions[{index}]"
            item = _object(row, {"obligation_id", "status", "reason_code", "integrated_into_obligation_id"}, path, issues)
            if item is None:
                continue
            decisions.append(item)
            oid = _string(item.get("obligation_id"), f"{path}.obligation_id", issues, pattern=_ID_PATTERNS["obligation_id"])
            if oid is not None:
                decision_ids.append(oid)
            status = _enum(item.get("status"), statuses, f"{path}.status", issues)
            _string(item.get("reason_code"), f"{path}.reason_code", issues, pattern=_MACHINE_CODE_RE)
            target = item.get("integrated_into_obligation_id")
            if status == "integrated_into":
                _string(target, f"{path}.integrated_into_obligation_id", issues, pattern=_ID_PATTERNS["obligation_id"])
                if target == oid:
                    _add(issues, "SELF_REFERENCE_FORBIDDEN", f"{path}.integrated_into_obligation_id")
            elif target is not None:
                _add(issues, "INTEGRATION_TARGET_FORBIDDEN", f"{path}.integrated_into_obligation_id")
            if oid not in ledger_by_id:
                _add(issues, "UNRESOLVED_OBLIGATION_REFERENCE", f"{path}.obligation_id")
            if ledger_by_id.get(oid, {}).get("required") is True and status not in {"selected", "integrated_into"}:
                _add(issues, "REQUIRED_OBLIGATION_NOT_SELECTED", f"{path}.status")
    for index, oid in enumerate(decision_ids):
        if oid in decision_ids[:index]:
            _add(issues, "DUPLICATE_ID", f"$.decisions[{index}].obligation_id")
    if set(decision_ids) != set(ledger_by_id):
        _add(issues, "DECISION_SET_MISMATCH", "$.decisions")
    selected = {row.get("obligation_id") for row in decisions if row.get("status") == "selected"}
    active_obligation_ids = {
        row.get("obligation_id")
        for row in decisions
        if row.get("status") in {"selected", "integrated_into"}
    }
    for index, row in enumerate(decisions):
        if row.get("status") == "integrated_into" and row.get("integrated_into_obligation_id") not in selected:
            _add(issues, "INTEGRATION_TARGET_NOT_SELECTED", f"$.decisions[{index}].integrated_into_obligation_id")
        if row.get("status") == "integrated_into":
            source = ledger_by_id.get(row.get("obligation_id"), {})
            target_id = row.get("integrated_into_obligation_id")
            target = ledger_by_id.get(target_id, {})
            if target_id in source.get("must_not_merge_with", []) or row.get(
                "obligation_id"
            ) in target.get("must_not_merge_with", []):
                _add(issues, "MUST_NOT_MERGE_INTEGRATION_FORBIDDEN", f"$.decisions[{index}].integrated_into_obligation_id")
            if (source.get("kind") == STANCE_KIND) != (
                target.get("kind") == STANCE_KIND
            ):
                _add(issues, "CROSS_SECTION_INTEGRATION_FORBIDDEN", f"$.decisions[{index}].integrated_into_obligation_id")
        obligation = ledger_by_id.get(row.get("obligation_id"), {})
        if (
            obligation.get("kind") == STANCE_KIND
            and row.get("status") in {"selected", "integrated_into"}
            and not set(obligation.get("target_obligation_ids", []))
            <= active_obligation_ids
        ):
            _add(
                issues,
                "BOUND_RECEPTION_TARGET_NOT_SELECTED",
                f"$.decisions[{index}].status",
            )
    required = _string_list(obj.get("required_coverage_obligation_ids"), "$.required_coverage_obligation_ids", issues, minimum=1)
    expected_required = obligation_ledger.get("required_obligation_ids") if type(obligation_ledger) is dict else None
    if required != expected_required:
        _add(issues, "REQUIRED_COVERAGE_SET_MISMATCH", "$.required_coverage_obligation_ids")
    _derived_id(obj, "content_plan_id", "nls3cp_", "$.content_plan_id", issues)
    return _final(issues)


def _acyclic(edges: Iterable[tuple[str, str]]) -> bool:
    adjacency: dict[str, set[str]] = {}
    for source, target in edges:
        adjacency.setdefault(source, set()).add(target)
        adjacency.setdefault(target, set())
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return False
        if node in visited:
            return True
        visiting.add(node)
        for target in adjacency.get(node, ()):
            if not visit(target):
                return False
        visiting.remove(node)
        visited.add(node)
        return True

    return all(visit(node) for node in tuple(adjacency))


def validate_discourse_plan(
    value: Any,
    *,
    content_plan: Mapping[str, Any],
    obligation_ledger: Mapping[str, Any],
) -> tuple[ContractIssue, ...]:
    issues: list[ContractIssue] = []
    obj = _object(
        value,
        {"schema_version", "discourse_plan_id", "source_content_plan_sha256", "structural_signature", "nodes", "edges", "sentence_groups", "body_free"},
        "$",
        issues,
    )
    if obj is None:
        return _final(issues)
    _schema(obj.get("schema_version"), DISCOURSE_SCHEMA, "$.schema_version", issues)
    _parent(obj.get("source_content_plan_sha256"), artifact_sha256(content_plan), "$.source_content_plan_sha256", issues)
    if (
        type(content_plan) is not dict
        or content_plan.get("schema_version") != CONTENT_SCHEMA
        or content_plan.get("body_free") is not True
        or type(obligation_ledger) is not dict
        or obligation_ledger.get("schema_version") != LEDGER_SCHEMA
        or obligation_ledger.get("body_free") is not True
    ):
        _add(issues, "PARENT_ARTIFACT_INVALID", "$.source_content_plan_sha256")
    body_free = _bool(obj.get("body_free"), "$.body_free", issues)
    if body_free is not True:
        _add(issues, "BODY_FREE_REQUIRED", "$.body_free")
    ledger_by_id = {
        row.get("obligation_id"): row
        for row in obligation_ledger.get("obligations", [])
        if type(row) is dict and type(row.get("obligation_id")) is str
    }
    ledger_rows = obligation_ledger.get("obligations", [])
    if type(ledger_rows) is not list or len(ledger_by_id) != len(ledger_rows):
        _add(issues, "PARENT_ARTIFACT_INVALID", "$.source_content_plan_sha256")
    content_decisions = content_plan.get("decisions", [])
    selected_ids = {
        row.get("obligation_id")
        for row in content_decisions
        if type(row) is dict and row.get("status") in {"selected", "integrated_into"}
    }
    content_decision_ids = [
        row.get("obligation_id")
        for row in content_decisions
        if type(row) is dict and type(row.get("obligation_id")) is str
    ]
    if type(content_decisions) is not list or len(content_decision_ids) != len(
        content_decisions
    ) or len(content_decision_ids) != len(set(content_decision_ids)):
        _add(issues, "PARENT_ARTIFACT_INVALID", "$.source_content_plan_sha256")
    if content_plan.get("source_obligation_ledger_sha256") != artifact_sha256(
        obligation_ledger
    ):
        _add(issues, "PARENT_CHAIN_MISMATCH", "$.source_content_plan_sha256")
    nodes_value = _list(obj.get("nodes"), "$.nodes", issues, minimum=1)
    nodes: list[dict[str, Any]] = []
    node_ids: list[str] = []
    if nodes_value is not None:
        for index, row in enumerate(nodes_value):
            path = f"$.nodes[{index}]"
            item = _object(row, {"node_id", "obligation_id", "section_role", "clause_role", "antecedent_node_ids", "merge_eligible", "must_separate_from_node_ids"}, path, issues)
            if item is None:
                continue
            nodes.append(item)
            nid = _string(item.get("node_id"), f"{path}.node_id", issues, pattern=_ID_PATTERNS["node_id"])
            if nid is not None:
                node_ids.append(nid)
            oid = _string(item.get("obligation_id"), f"{path}.obligation_id", issues, pattern=_ID_PATTERNS["obligation_id"])
            section = _enum(item.get("section_role"), {"observation", "reception"}, f"{path}.section_role", issues)
            _enum(item.get("clause_role"), {"nucleus_notice", "relation_notice", "unknown_boundary", "shift_notice", "next_action", "self_denial_boundary", "bounded_counterposition", "bound_reception"}, f"{path}.clause_role", issues)
            _string_list(item.get("antecedent_node_ids"), f"{path}.antecedent_node_ids", issues)
            _bool(item.get("merge_eligible"), f"{path}.merge_eligible", issues)
            _string_list(item.get("must_separate_from_node_ids"), f"{path}.must_separate_from_node_ids", issues)
            if oid not in selected_ids or oid not in ledger_by_id:
                _add(issues, "UNRESOLVED_OBLIGATION_REFERENCE", f"{path}.obligation_id")
            expected_clause_role = {
                "grounded_nucleus_notice": "nucleus_notice",
                "grounded_relation_preservation": "relation_notice",
                "unknown_boundary_preservation": "unknown_boundary",
                "significance_or_shift": "shift_notice",
                "intention_or_next_action": "next_action",
                "self_denial_boundary": "self_denial_boundary",
                "bounded_counterposition": "bounded_counterposition",
                "bound_emlis_reception": "bound_reception",
            }.get(ledger_by_id.get(oid, {}).get("kind"))
            if expected_clause_role is not None and item.get("clause_role") != expected_clause_role:
                _add(issues, "CLAUSE_ROLE_MISMATCH", f"{path}.clause_role")
            expected_section = "reception" if ledger_by_id.get(oid, {}).get("kind") == STANCE_KIND else "observation"
            if section is not None and section != expected_section:
                _add(issues, "SECTION_ROLE_MISMATCH", f"{path}.section_role")
    for index, nid in enumerate(node_ids):
        if nid in node_ids[:index]:
            _add(issues, "DUPLICATE_ID", f"$.nodes[{index}].node_id")
    node_set = set(node_ids)
    node_by_id = {row.get("node_id"): row for row in nodes}
    dependency_edges: list[tuple[str, str]] = []
    for index, row in enumerate(nodes):
        for field in ("antecedent_node_ids", "must_separate_from_node_ids"):
            refs = row.get(field)
            if type(refs) is list and not set(item for item in refs if type(item) is str) <= node_set:
                _add(issues, "UNRESOLVED_NODE_REFERENCE", f"$.nodes[{index}].{field}")
            if row.get("node_id") in (refs or []):
                _add(issues, "SELF_REFERENCE_FORBIDDEN", f"$.nodes[{index}].{field}")
        for antecedent in row.get("antecedent_node_ids") or []:
            dependency_edges.append((antecedent, row.get("node_id")))

    edges_value = _list(obj.get("edges"), "$.edges", issues)
    edge_tuples: list[tuple[str, str, str]] = []
    if edges_value is not None:
        for index, row in enumerate(edges_value):
            path = f"$.edges[{index}]"
            item = _object(row, {"from", "to", "type"}, path, issues)
            if item is None:
                continue
            source = _string(item.get("from"), f"{path}.from", issues, pattern=_ID_PATTERNS["node_id"])
            target = _string(item.get("to"), f"{path}.to", issues, pattern=_ID_PATTERNS["node_id"])
            edge_type = _enum(item.get("type"), {"precedes", "explains_without_causation", "contrasts_with", "coexists_with", "qualifies", "receives", "separates_self_denial_from", "preserves_unknown_before"}, f"{path}.type", issues)
            if source not in node_set or target not in node_set:
                _add(issues, "UNRESOLVED_NODE_REFERENCE", path)
            if source == target:
                _add(issues, "SELF_REFERENCE_FORBIDDEN", path)
            if source and target and edge_type:
                edge_tuples.append((source, target, edge_type))
                dependency_edges.append((source, target))
    if len(edge_tuples) != len(set(edge_tuples)):
        _add(issues, "DUPLICATE_EDGE", "$.edges")
    if not _acyclic(dependency_edges):
        _add(issues, "DISCOURSE_CYCLE", "$.edges")

    groups_value = _list(obj.get("sentence_groups"), "$.sentence_groups", issues, minimum=2)
    group_ids: list[str] = []
    group_roles: list[str] = []
    grouped_nodes: list[str] = []
    node_to_group: dict[str, str] = {}
    node_to_group_index: dict[str, int] = {}
    if groups_value is not None:
        for index, row in enumerate(groups_value):
            path = f"$.sentence_groups[{index}]"
            item = _object(row, {"sentence_group_id", "section_role", "node_ids"}, path, issues)
            if item is None:
                continue
            gid = _string(item.get("sentence_group_id"), f"{path}.sentence_group_id", issues, pattern=_ID_PATTERNS["sentence_group_id"])
            if gid is not None:
                group_ids.append(gid)
            section = _enum(item.get("section_role"), {"observation", "reception"}, f"{path}.section_role", issues)
            if section is not None:
                group_roles.append(section)
            refs = _string_list(item.get("node_ids"), f"{path}.node_ids", issues, minimum=1, pattern=_ID_PATTERNS["node_id"])
            for ref in refs or []:
                grouped_nodes.append(ref)
                node_to_group[ref] = gid or ""
                node_to_group_index[ref] = index
                if ref not in node_set:
                    _add(issues, "UNRESOLVED_NODE_REFERENCE", f"{path}.node_ids")
                elif node_by_id[ref].get("section_role") != section:
                    _add(issues, "SECTION_ROLE_MISMATCH", f"{path}.node_ids")
    if len(group_ids) != len(set(group_ids)):
        _add(issues, "DUPLICATE_ID", "$.sentence_groups")
    if (
        not group_roles
        or group_roles[0] != "observation"
        or group_roles[-1] != "reception"
        or any(
            left == "reception" and right == "observation"
            for left, right in zip(group_roles, group_roles[1:])
        )
    ):
        _add(issues, "SECTION_GROUP_SEQUENCE_MISMATCH", "$.sentence_groups")
    if sorted(grouped_nodes) != sorted(node_ids):
        _add(issues, "SENTENCE_PARTITION_MISMATCH", "$.sentence_groups")
    budget = content_plan.get("section_budget")
    budget_keys = {
        "observation_sentence_min",
        "observation_sentence_max",
        "reception_sentence_min",
        "reception_sentence_max",
        "total_sentence_max",
    }
    if type(budget) is not dict or set(budget) != budget_keys or not all(
        type(budget.get(key)) is int for key in budget_keys
    ):
        _add(issues, "PARENT_ARTIFACT_INVALID", "$.source_content_plan_sha256")
    else:
        observation_count = group_roles.count("observation")
        reception_count = group_roles.count("reception")
        if not (
            budget["observation_sentence_min"]
            <= observation_count
            <= budget["observation_sentence_max"]
        ):
            _add(issues, "CONTENT_BUDGET_MISMATCH", "$.sentence_groups")
        if not (
            budget["reception_sentence_min"]
            <= reception_count
            <= budget["reception_sentence_max"]
        ):
            _add(issues, "CONTENT_BUDGET_MISMATCH", "$.sentence_groups")
        if len(group_roles) > budget["total_sentence_max"]:
            _add(issues, "CONTENT_BUDGET_MISMATCH", "$.sentence_groups")
    represented_obligations = [
        row.get("obligation_id")
        for row in nodes
        if type(row.get("obligation_id")) is str
    ]
    if len(represented_obligations) != len(set(represented_obligations)) or set(
        represented_obligations
    ) != selected_ids:
        _add(issues, "DISCOURSE_OBLIGATION_COVERAGE_MISMATCH", "$.nodes")
    for index, row in enumerate(nodes):
        expected_separate_nodes = sorted(
            node_id
            for obligation_id in ledger_by_id.get(
                row.get("obligation_id"), {}
            ).get("must_not_merge_with", [])
            for node_id, target_node in node_by_id.items()
            if target_node.get("obligation_id") == obligation_id
        )
        if sorted(row.get("must_separate_from_node_ids") or []) != expected_separate_nodes:
            _add(issues, "MUST_SEPARATE_DERIVATION_MISMATCH", f"$.nodes[{index}].must_separate_from_node_ids")
        for target in row.get("must_separate_from_node_ids") or []:
            if node_to_group.get(row.get("node_id")) == node_to_group.get(target):
                _add(issues, "MUST_SEPARATE_VIOLATION", f"$.nodes[{index}].must_separate_from_node_ids")
    for source, target in dependency_edges:
        if node_to_group_index.get(source, -1) > node_to_group_index.get(target, -1):
            _add(issues, "DISCOURSE_ORDER_VIOLATION", "$.sentence_groups")
    node_by_obligation = {
        row.get("obligation_id"): row.get("node_id") for row in nodes
    }
    expected_receives: set[tuple[str, str, str]] = set()
    for row in nodes:
        obligation = ledger_by_id.get(row.get("obligation_id"), {})
        if obligation.get("kind") != STANCE_KIND:
            continue
        stance_node = row.get("node_id")
        for target_obligation_id in obligation.get("target_obligation_ids", []):
            target_node = node_by_obligation.get(target_obligation_id)
            if type(target_node) is str and type(stance_node) is str:
                expected_receives.add((target_node, stance_node, "receives"))
            else:
                _add(
                    issues,
                    "BOUND_RECEPTION_TARGET_NODE_MISSING",
                    "$.nodes",
                )
    actual_receives = {
        edge for edge in edge_tuples if edge[2] == "receives"
    }
    if actual_receives != expected_receives:
        _add(issues, "BOUND_RECEPTION_EDGE_MISMATCH", "$.edges")
    for index, decision in enumerate(content_decisions):
        if decision.get("status") != "integrated_into":
            continue
        source_node = node_by_obligation.get(decision.get("obligation_id"))
        target_node = node_by_obligation.get(
            decision.get("integrated_into_obligation_id")
        )
        if (
            source_node is None
            or target_node is None
            or node_to_group.get(source_node) != node_to_group.get(target_node)
        ):
            _add(issues, "INTEGRATED_DISCOURSE_GROUP_MISMATCH", f"$.nodes")
        elif (
            node_by_id.get(source_node, {}).get("merge_eligible") is not True
            or node_by_id.get(target_node, {}).get("merge_eligible") is not True
        ):
            _add(issues, "INTEGRATED_NODE_NOT_MERGE_ELIGIBLE", "$.nodes")

    structural_payload = {
        "nodes": obj.get("nodes"),
        "edges": obj.get("edges"),
        "sentence_groups": obj.get("sentence_groups"),
    }
    signature = obj.get("structural_signature")
    _string(signature, "$.structural_signature", issues, pattern=_ID_PATTERNS["structural_signature"])
    expected_signature = "nls3sig_" + artifact_sha256(structural_payload)[:16]
    if signature != expected_signature:
        _add(issues, "STRUCTURAL_SIGNATURE_MISMATCH", "$.structural_signature")
    _derived_id(obj, "discourse_plan_id", "nls3dp_", "$.discourse_plan_id", issues)
    return _final(issues)


_AST_NODE_KEYS = {
    "grounded_referent": {"node_type", "evidence_ids", "nucleus_ids", "antecedent_clause_id", "form"},
    "grounded_relation": {"node_type", "relation_id", "direction"},
    "unknown_boundary": {"node_type", "unknown_boundary_ids", "form"},
    "observation_predicate": {"node_type", "form"},
    "emlis_stance": {"node_type", "target_obligation_ids", "form"},
    "self_denial_boundary": {"node_type", "form"},
    "modality": {"node_type", "modality"},
    "connector": {"node_type", "edge_type"},
}


def validate_surface_ast(
    value: Any,
    *,
    discourse_plan: Mapping[str, Any],
    obligation_ledger: Mapping[str, Any],
) -> tuple[ContractIssue, ...]:
    issues: list[ContractIssue] = []
    obj = _object(value, {"schema_version", "surface_ast_id", "source_discourse_plan_sha256", "sections", "body_free"}, "$", issues)
    if obj is None:
        return _final(issues)
    _schema(obj.get("schema_version"), AST_SCHEMA, "$.schema_version", issues)
    _parent(obj.get("source_discourse_plan_sha256"), artifact_sha256(discourse_plan), "$.source_discourse_plan_sha256", issues)
    if (
        type(discourse_plan) is not dict
        or discourse_plan.get("schema_version") != DISCOURSE_SCHEMA
        or discourse_plan.get("body_free") is not True
        or type(obligation_ledger) is not dict
        or obligation_ledger.get("schema_version") != LEDGER_SCHEMA
        or obligation_ledger.get("body_free") is not True
    ):
        _add(issues, "PARENT_ARTIFACT_INVALID", "$.source_discourse_plan_sha256")
    body_free = _bool(obj.get("body_free"), "$.body_free", issues)
    if body_free is not True:
        _add(issues, "BODY_FREE_REQUIRED", "$.body_free")
    discourse_nodes = {
        row.get("node_id"): row
        for row in discourse_plan.get("nodes", [])
        if type(row) is dict and type(row.get("node_id")) is str
    }
    discourse_rows = discourse_plan.get("nodes", [])
    if type(discourse_rows) is not list or len(discourse_nodes) != len(discourse_rows):
        _add(issues, "PARENT_ARTIFACT_INVALID", "$.source_discourse_plan_sha256")
    ledger_by_id = {
        row.get("obligation_id"): row
        for row in obligation_ledger.get("obligations", [])
        if type(row) is dict and type(row.get("obligation_id")) is str
    }
    ledger_rows = obligation_ledger.get("obligations", [])
    if type(ledger_rows) is not list or len(ledger_by_id) != len(ledger_rows):
        _add(issues, "PARENT_ARTIFACT_INVALID", "$.source_discourse_plan_sha256")
    sections_value = _list(obj.get("sections"), "$.sections", issues, minimum=2)
    section_roles: list[str] = []
    clause_ids: list[str] = []
    covered_discourse_nodes: list[str] = []
    clause_order: list[str] = []
    ast_sentence_groups: list[list[str]] = []
    ast_sentence_roles: list[str | None] = []
    if sections_value is not None:
        for section_index, section_row in enumerate(sections_value):
            spath = f"$.sections[{section_index}]"
            section = _object(section_row, {"role", "sentences"}, spath, issues)
            if section is None:
                continue
            role = _enum(section.get("role"), {"observation", "reception"}, f"{spath}.role", issues)
            if role is not None:
                section_roles.append(role)
            sentences = _list(section.get("sentences"), f"{spath}.sentences", issues, minimum=1)
            for sentence_index, sentence_row in enumerate(sentences or []):
                sent_path = f"{spath}.sentences[{sentence_index}]"
                sentence = _object(sentence_row, {"clauses", "terminal"}, sent_path, issues)
                if sentence is None:
                    continue
                _enum(sentence.get("terminal"), {"plain_bounded", "plain_restrained", "plain_unknown", "plain_intended"}, f"{sent_path}.terminal", issues)
                clauses = _list(sentence.get("clauses"), f"{sent_path}.clauses", issues, minimum=1)
                sentence_discourse_nodes: list[str] = []
                for clause_index, clause_row in enumerate(clauses or []):
                    cpath = f"{sent_path}.clauses[{clause_index}]"
                    clause = _object(clause_row, {"clause_id", "discourse_node_id", "obligation_id", "nodes"}, cpath, issues)
                    if clause is None:
                        continue
                    cid = _string(clause.get("clause_id"), f"{cpath}.clause_id", issues, pattern=_ID_PATTERNS["clause_id"])
                    if cid is not None:
                        clause_ids.append(cid)
                        clause_order.append(cid)
                    discourse_id = _string(clause.get("discourse_node_id"), f"{cpath}.discourse_node_id", issues, pattern=_ID_PATTERNS["node_id"])
                    if discourse_id is not None:
                        covered_discourse_nodes.append(discourse_id)
                        sentence_discourse_nodes.append(discourse_id)
                    oid = _string(clause.get("obligation_id"), f"{cpath}.obligation_id", issues, pattern=_ID_PATTERNS["obligation_id"])
                    parent_node = discourse_nodes.get(discourse_id)
                    if parent_node is None:
                        _add(issues, "UNRESOLVED_DISCOURSE_NODE", f"{cpath}.discourse_node_id")
                    else:
                        if parent_node.get("obligation_id") != oid:
                            _add(issues, "DISCOURSE_OBLIGATION_MISMATCH", f"{cpath}.obligation_id")
                        if parent_node.get("section_role") != role:
                            _add(issues, "SECTION_ROLE_MISMATCH", f"{cpath}.discourse_node_id")
                    if oid not in ledger_by_id:
                        _add(issues, "UNRESOLVED_OBLIGATION_REFERENCE", f"{cpath}.obligation_id")
                    nodes = _list(clause.get("nodes"), f"{cpath}.nodes", issues, minimum=1)
                    node_types: list[str] = []
                    for node_index, node_row in enumerate(nodes or []):
                        npath = f"{cpath}.nodes[{node_index}]"
                        if type(node_row) is not dict:
                            _add(issues, "OBJECT_REQUIRED", npath)
                            continue
                        node_type = node_row.get("node_type")
                        _enum(node_type, _AST_NODE_KEYS, f"{npath}.node_type", issues)
                        if node_type not in _AST_NODE_KEYS:
                            _object(node_row, {"node_type"}, npath, issues)
                            continue
                        node = _object(node_row, _AST_NODE_KEYS[node_type], npath, issues)
                        if node is None:
                            continue
                        node_types.append(node_type)
                        if node_type == "grounded_referent":
                            evidence = _string_list(node.get("evidence_ids"), f"{npath}.evidence_ids", issues, pattern=_MACHINE_ID_RE)
                            nuclei = _string_list(node.get("nucleus_ids"), f"{npath}.nucleus_ids", issues, pattern=_MACHINE_ID_RE)
                            form = _enum(node.get("form"), {"semantic_phrase", "unique_antecedent"}, f"{npath}.form", issues)
                            antecedent = node.get("antecedent_clause_id")
                            if form == "semantic_phrase":
                                if not evidence and not nuclei:
                                    _add(issues, "GROUNDED_SOURCE_REQUIRED", npath)
                                if antecedent is not None:
                                    _add(issues, "ANTECEDENT_FORBIDDEN", f"{npath}.antecedent_clause_id")
                            elif form == "unique_antecedent":
                                _string(antecedent, f"{npath}.antecedent_clause_id", issues, pattern=_ID_PATTERNS["clause_id"])
                                if antecedent not in clause_order[:-1]:
                                    _add(issues, "UNRESOLVED_ANTECEDENT", f"{npath}.antecedent_clause_id")
                                if evidence or nuclei:
                                    _add(issues, "ANTECEDENT_SOURCE_COLLISION", npath)
                            obligation = ledger_by_id.get(oid, {})
                            if evidence is not None and not set(evidence) <= set(obligation.get("evidence_ids", [])):
                                _add(issues, "UNRESOLVED_EVIDENCE_REFERENCE", f"{npath}.evidence_ids")
                            if nuclei is not None and not set(nuclei) <= set(obligation.get("nucleus_ids", [])):
                                _add(issues, "UNRESOLVED_NUCLEUS_REFERENCE", f"{npath}.nucleus_ids")
                        elif node_type == "grounded_relation":
                            relation_id = _string(node.get("relation_id"), f"{npath}.relation_id", issues, pattern=_MACHINE_ID_RE)
                            direction = _enum(node.get("direction"), {"source_to_target", "target_to_source", "bidirectional"}, f"{npath}.direction", issues)
                            if relation_id not in ledger_by_id.get(oid, {}).get("relation_ids", []):
                                _add(issues, "UNRESOLVED_RELATION_REFERENCE", f"{npath}.relation_id")
                            expected_direction = {
                                row.get("relation_id"): row.get("direction")
                                for row in ledger_by_id.get(oid, {}).get(
                                    "relation_directions", []
                                )
                                if type(row) is dict
                            }.get(relation_id)
                            if direction != expected_direction:
                                _add(issues, "RELATION_DIRECTION_MISMATCH", f"{npath}.direction")
                        elif node_type == "unknown_boundary":
                            refs = _string_list(node.get("unknown_boundary_ids"), f"{npath}.unknown_boundary_ids", issues, minimum=1, pattern=_MACHINE_ID_RE)
                            _enum(node.get("form"), {"preserve_unknown", "bounded_uncertainty"}, f"{npath}.form", issues)
                            if refs is not None and not set(refs) <= set(ledger_by_id.get(oid, {}).get("unknown_boundary_ids", [])):
                                _add(issues, "UNRESOLVED_UNKNOWN_REFERENCE", f"{npath}.unknown_boundary_ids")
                        elif node_type == "observation_predicate":
                            predicate_form = _enum(node.get("form"), {"nucleus_observed", "coexisting_meanings_observed", "shift_observed", "action_intended", "bounded_counterposition_observed"}, f"{npath}.form", issues)
                            expected_predicate_form = {
                                "grounded_nucleus_notice": "nucleus_observed",
                                "grounded_relation_preservation": "coexisting_meanings_observed",
                                "significance_or_shift": "shift_observed",
                                "intention_or_next_action": "action_intended",
                                "bounded_counterposition": "bounded_counterposition_observed",
                            }.get(ledger_by_id.get(oid, {}).get("kind"))
                            if expected_predicate_form is not None and predicate_form != expected_predicate_form:
                                _add(issues, "PREDICATE_FORM_MISMATCH", f"{npath}.form")
                        elif node_type == "emlis_stance":
                            targets = _string_list(node.get("target_obligation_ids"), f"{npath}.target_obligation_ids", issues, minimum=1, pattern=_ID_PATTERNS["obligation_id"])
                            _enum(node.get("form"), RECEPTION_ACTS, f"{npath}.form", issues)
                            if targets is not None and targets != ledger_by_id.get(oid, {}).get("target_obligation_ids"):
                                _add(issues, "STANCE_TARGET_MISMATCH", f"{npath}.target_obligation_ids")
                            if node.get("form") not in ledger_by_id.get(oid, {}).get(
                                "allowed_response_acts", []
                            ):
                                _add(issues, "STANCE_ACT_MISMATCH", f"{npath}.form")
                        elif node_type == "self_denial_boundary":
                            _enum(node.get("form"), {"separate_claim_from_observation"}, f"{npath}.form", issues)
                        elif node_type == "modality":
                            modality = _enum(node.get("modality"), MODALITIES, f"{npath}.modality", issues)
                            if modality != ledger_by_id.get(oid, {}).get("modality"):
                                _add(issues, "MODALITY_MISMATCH", f"{npath}.modality")
                        elif node_type == "connector":
                            _enum(node.get("edge_type"), {"precedes", "explains_without_causation", "contrasts_with", "coexists_with", "qualifies", "receives", "separates_self_denial_from", "preserves_unknown_before"}, f"{npath}.edge_type", issues)
                    if "grounded_referent" not in node_types:
                        _add(issues, "GROUNDED_REFERENT_REQUIRED", f"{cpath}.nodes")
                    if ledger_by_id.get(oid, {}).get("kind") == STANCE_KIND and "emlis_stance" not in node_types:
                        _add(issues, "EMLIS_STANCE_NODE_REQUIRED", f"{cpath}.nodes")
                    obligation_kind = ledger_by_id.get(oid, {}).get("kind")
                    required_node_type = {
                        "grounded_nucleus_notice": "observation_predicate",
                        "grounded_relation_preservation": "grounded_relation",
                        "unknown_boundary_preservation": "unknown_boundary",
                        "significance_or_shift": "observation_predicate",
                        "intention_or_next_action": "observation_predicate",
                        "self_denial_boundary": "self_denial_boundary",
                        "bounded_counterposition": "observation_predicate",
                        "bound_emlis_reception": "emlis_stance",
                    }.get(obligation_kind)
                    if required_node_type is not None and required_node_type not in node_types:
                        _add(issues, "SEMANTIC_NODE_TYPE_REQUIRED", f"{cpath}.nodes")
                ast_sentence_groups.append(sentence_discourse_nodes)
                ast_sentence_roles.append(role)
    if section_roles != ["observation", "reception"]:
        _add(issues, "SECTION_SEQUENCE_MISMATCH", "$.sections")
    for index, cid in enumerate(clause_ids):
        if cid in clause_ids[:index]:
            _add(issues, "DUPLICATE_ID", "$.sections")
    if sorted(covered_discourse_nodes) != sorted(discourse_nodes):
        _add(issues, "DISCOURSE_COVERAGE_MISMATCH", "$.sections")
    discourse_groups = discourse_plan.get("sentence_groups")
    if type(discourse_groups) is not list or not all(
        type(row) is dict
        and type(row.get("node_ids")) is list
        and type(row.get("section_role")) is str
        for row in discourse_groups
    ):
        _add(issues, "PARENT_ARTIFACT_INVALID", "$.source_discourse_plan_sha256")
    else:
        expected_sentence_groups = [row["node_ids"] for row in discourse_groups]
        expected_sentence_roles = [row["section_role"] for row in discourse_groups]
        if ast_sentence_groups != expected_sentence_groups:
            _add(issues, "DISCOURSE_SENTENCE_PARTITION_MISMATCH", "$.sections")
        if ast_sentence_roles != expected_sentence_roles:
            _add(issues, "DISCOURSE_SENTENCE_ROLE_MISMATCH", "$.sections")
    _derived_id(obj, "surface_ast_id", "nls3ast_", "$.surface_ast_id", issues)
    return _final(issues)


_ATOM_COMMON = {
    "atom_id",
    "kind",
    "referent_fingerprint",
    "polarity",
    "modality",
    "temporal_scope",
    "topic_fingerprints",
    "referent_scope",
    "utf8_byte_start",
    "utf8_byte_end",
    "span_sha256",
}
_ATOM_KEYS = {
    "grounded_nucleus": _ATOM_COMMON | {"predicate_code"},
    "grounded_relation": _ATOM_COMMON | {"relation_type", "direction"},
    "unknown_boundary": _ATOM_COMMON | {"unknown_scope"},
    "significance_or_shift": _ATOM_COMMON | {"predicate_code"},
    "intention_or_next_action": _ATOM_COMMON | {"predicate_code"},
    "self_denial_boundary": _ATOM_COMMON | {"predicate_code"},
    "bounded_counterposition": _ATOM_COMMON | {"predicate_code"},
    "bound_emlis_reception": {
        "atom_id",
        "kind",
        "target_atom_ids",
        "reception_act",
        "temporal_scope",
        "topic_fingerprints",
        "referent_scope",
        "utf8_byte_start",
        "utf8_byte_end",
        "span_sha256",
    },
}


def validate_parsed_surface_witness(
    value: Any,
    *,
    candidate_text_bytes: bytes,
) -> tuple[ContractIssue, ...]:
    issues: list[ContractIssue] = []
    obj = _object(value, {"schema_version", "candidate_text_sha256", "parse_status", "semantic_atoms", "body_free_export_allowed"}, "$", issues)
    if obj is None:
        return _final(issues)
    _schema(obj.get("schema_version"), WITNESS_SCHEMA, "$.schema_version", issues)
    if type(candidate_text_bytes) is not bytes:
        _add(issues, "CANDIDATE_BYTES_REQUIRED", "$.candidate_text_sha256")
        candidate_text_bytes = b""
    try:
        candidate_text = candidate_text_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        candidate_text = ""
        _add(issues, "CANDIDATE_UTF8_REQUIRED", "$.candidate_text_sha256")
    expected_text_sha = hashlib.sha256(candidate_text_bytes).hexdigest()
    _parent(obj.get("candidate_text_sha256"), expected_text_sha, "$.candidate_text_sha256", issues)
    status = _enum(obj.get("parse_status"), {"parsed", "unparseable"}, "$.parse_status", issues)
    allowed = _bool(obj.get("body_free_export_allowed"), "$.body_free_export_allowed", issues)
    if allowed is not False:
        _add(issues, "PRIVATE_ARTIFACT_EXPORT_FORBIDDEN", "$.body_free_export_allowed")
    atoms_value = _list(obj.get("semantic_atoms"), "$.semantic_atoms", issues)
    atoms: list[dict[str, Any]] = []
    atom_ids: list[str] = []
    boundaries = {0}
    offset = 0
    for character in candidate_text:
        offset += len(character.encode("utf-8"))
        boundaries.add(offset)
    if atoms_value is not None:
        if status == "parsed" and not atoms_value:
            _add(issues, "PARSED_ATOM_REQUIRED", "$.semantic_atoms")
        if status == "unparseable" and atoms_value:
            _add(issues, "UNPARSEABLE_ATOM_FORBIDDEN", "$.semantic_atoms")
        for index, row in enumerate(atoms_value):
            path = f"$.semantic_atoms[{index}]"
            if type(row) is not dict:
                _add(issues, "OBJECT_REQUIRED", path)
                continue
            kind = row.get("kind")
            _enum(kind, _ATOM_KEYS, f"{path}.kind", issues)
            if kind not in _ATOM_KEYS:
                _object(row, {"atom_id", "kind"}, path, issues)
                continue
            item = _object(row, _ATOM_KEYS[kind], path, issues)
            if item is None:
                continue
            atoms.append(item)
            atom_id = _string(item.get("atom_id"), f"{path}.atom_id", issues, pattern=_ID_PATTERNS["atom_id"])
            if atom_id is not None:
                atom_ids.append(atom_id)
            _enum(item.get("temporal_scope"), TEMPORAL_SCOPES, f"{path}.temporal_scope", issues)
            _string_list(item.get("topic_fingerprints"), f"{path}.topic_fingerprints", issues, minimum=1, pattern=re.compile(r"^topic_[0-9a-f]{16}$"))
            _enum(item.get("referent_scope"), REFERENT_SCOPES, f"{path}.referent_scope", issues)
            start = _int(item.get("utf8_byte_start"), f"{path}.utf8_byte_start", issues, minimum=0)
            end = _int(item.get("utf8_byte_end"), f"{path}.utf8_byte_end", issues, minimum=1, maximum=len(candidate_text_bytes))
            span_hash = _sha(item.get("span_sha256"), f"{path}.span_sha256", issues)
            if start is not None and end is not None:
                if start >= end:
                    _add(issues, "SPAN_RANGE_INVALID", path)
                if start not in boundaries or end not in boundaries:
                    _add(issues, "SPAN_NOT_UTF8_SCALAR_BOUNDARY", path)
                if 0 <= start < end <= len(candidate_text_bytes):
                    expected_span_hash = hashlib.sha256(candidate_text_bytes[start:end]).hexdigest()
                    if span_hash != expected_span_hash:
                        _add(issues, "SPAN_HASH_MISMATCH", f"{path}.span_sha256")
            if kind == "bound_emlis_reception":
                _string_list(item.get("target_atom_ids"), f"{path}.target_atom_ids", issues, minimum=1, pattern=_ID_PATTERNS["atom_id"])
                _enum(item.get("reception_act"), RECEPTION_ACTS, f"{path}.reception_act", issues)
            else:
                _string(item.get("referent_fingerprint"), f"{path}.referent_fingerprint", issues, pattern=re.compile(r"^semantic_ref_[0-9a-f]{16}$"))
                _enum(item.get("polarity"), POLARITIES, f"{path}.polarity", issues)
                _enum(item.get("modality"), MODALITIES, f"{path}.modality", issues)
                if kind == "grounded_relation":
                    _enum(item.get("relation_type"), {"precedes", "contrasts_with", "coexists_with", "qualifies", "supports_without_guarantee"}, f"{path}.relation_type", issues)
                    _enum(item.get("direction"), {"source_to_target", "target_to_source", "bidirectional"}, f"{path}.direction", issues)
                elif kind == "unknown_boundary":
                    _enum(item.get("unknown_scope"), {"cause", "referent", "outcome", "intention", "relation"}, f"{path}.unknown_scope", issues)
                else:
                    _string(item.get("predicate_code"), f"{path}.predicate_code", issues, pattern=re.compile(r"^[A-Z][A-Z0-9_]{2,63}$"))
    for index, atom_id in enumerate(atom_ids):
        if atom_id in atom_ids[:index]:
            _add(issues, "DUPLICATE_ID", f"$.semantic_atoms[{index}].atom_id")
    atom_by_id = {row.get("atom_id"): row for row in atoms}
    for index, row in enumerate(atoms):
        if row.get("kind") != "bound_emlis_reception":
            continue
        refs = row.get("target_atom_ids") or []
        if not set(refs) <= set(atom_ids):
            _add(issues, "UNRESOLVED_ATOM_REFERENCE", f"$.semantic_atoms[{index}].target_atom_ids")
        for ref in refs:
            if atom_by_id.get(ref, {}).get("kind") == "bound_emlis_reception":
                _add(issues, "RECEPTION_TARGET_MUST_BE_NONSTANCE", f"$.semantic_atoms[{index}].target_atom_ids")
    return _final(issues)


_ATOM_TO_OBLIGATION_KIND = {
    "grounded_nucleus": "grounded_nucleus_notice",
    "grounded_relation": "grounded_relation_preservation",
    "unknown_boundary": "unknown_boundary_preservation",
    "significance_or_shift": "significance_or_shift",
    "intention_or_next_action": "intention_or_next_action",
    "self_denial_boundary": "self_denial_boundary",
    "bounded_counterposition": "bounded_counterposition",
    "bound_emlis_reception": "bound_emlis_reception",
}


def validate_verified_surface_binding(
    value: Any,
    *,
    parsed_surface_witness: Mapping[str, Any],
    obligation_ledger: Mapping[str, Any],
) -> tuple[ContractIssue, ...]:
    issues: list[ContractIssue] = []
    obj = _object(value, {"schema_version", "parsed_surface_witness_sha256", "source_obligation_ledger_sha256", "bindings", "binding_status", "body_free_export_allowed"}, "$", issues)
    if obj is None:
        return _final(issues)
    _schema(obj.get("schema_version"), BINDING_SCHEMA, "$.schema_version", issues)
    _parent(obj.get("parsed_surface_witness_sha256"), artifact_sha256(parsed_surface_witness), "$.parsed_surface_witness_sha256", issues)
    _parent(obj.get("source_obligation_ledger_sha256"), artifact_sha256(obligation_ledger), "$.source_obligation_ledger_sha256", issues)
    if (
        type(parsed_surface_witness) is not dict
        or parsed_surface_witness.get("schema_version") != WITNESS_SCHEMA
        or parsed_surface_witness.get("body_free_export_allowed") is not False
        or parsed_surface_witness.get("parse_status") not in {
            "parsed",
            "unparseable",
        }
        or type(obligation_ledger) is not dict
        or obligation_ledger.get("schema_version") != LEDGER_SCHEMA
        or obligation_ledger.get("body_free") is not True
    ):
        _add(issues, "PARENT_ARTIFACT_INVALID", "$.parsed_surface_witness_sha256")
    status = _enum(obj.get("binding_status"), {"matched", "no_semantic_binding", "ambiguous_semantic_binding"}, "$.binding_status", issues)
    allowed = _bool(obj.get("body_free_export_allowed"), "$.body_free_export_allowed", issues)
    if allowed is not False:
        _add(issues, "PRIVATE_ARTIFACT_EXPORT_FORBIDDEN", "$.body_free_export_allowed")
    witness_atoms = {
        row.get("atom_id"): row
        for row in parsed_surface_witness.get("semantic_atoms", [])
        if type(row) is dict and type(row.get("atom_id")) is str
    }
    witness_rows = parsed_surface_witness.get("semantic_atoms", [])
    if type(witness_rows) is not list or len(witness_atoms) != len(witness_rows):
        _add(issues, "PARENT_ARTIFACT_INVALID", "$.parsed_surface_witness_sha256")
    obligations = {
        row.get("obligation_id"): row
        for row in obligation_ledger.get("obligations", [])
        if type(row) is dict and type(row.get("obligation_id")) is str
    }
    obligation_rows = obligation_ledger.get("obligations", [])
    if type(obligation_rows) is not list or len(obligations) != len(obligation_rows):
        _add(issues, "PARENT_ARTIFACT_INVALID", "$.source_obligation_ledger_sha256")
    rows_value = _list(obj.get("bindings"), "$.bindings", issues)
    rows: list[dict[str, Any]] = []
    atom_ids: list[str] = []
    obligation_ids: list[str] = []
    if rows_value is not None:
        if status == "matched" and not rows_value:
            _add(issues, "MATCHED_BINDING_REQUIRED", "$.bindings")
        if status != "matched" and rows_value:
            _add(issues, "FAILED_BINDING_MUST_BE_EMPTY", "$.bindings")
        for index, row in enumerate(rows_value):
            path = f"$.bindings[{index}]"
            item = _object(row, {"atom_id", "obligation_id", "evidence_ids", "relation_id", "target_obligation_ids", "topic_scope_ids", "match_basis", "match_candidate_count"}, path, issues)
            if item is None:
                continue
            rows.append(item)
            atom_id = _string(item.get("atom_id"), f"{path}.atom_id", issues, pattern=_ID_PATTERNS["atom_id"])
            obligation_id = _string(item.get("obligation_id"), f"{path}.obligation_id", issues, pattern=_ID_PATTERNS["obligation_id"])
            if atom_id is not None:
                atom_ids.append(atom_id)
            if obligation_id is not None:
                obligation_ids.append(obligation_id)
            evidence = _string_list(item.get("evidence_ids"), f"{path}.evidence_ids", issues, pattern=_MACHINE_ID_RE)
            if evidence == []:
                _add(issues, "BINDING_EVIDENCE_REQUIRED", f"{path}.evidence_ids")
            relation = item.get("relation_id")
            if relation is not None:
                _string(relation, f"{path}.relation_id", issues, pattern=_MACHINE_ID_RE)
            targets = _string_list(item.get("target_obligation_ids"), f"{path}.target_obligation_ids", issues, pattern=_ID_PATTERNS["obligation_id"])
            topics = _string_list(item.get("topic_scope_ids"), f"{path}.topic_scope_ids", issues, minimum=1, pattern=_MACHINE_ID_RE)
            _enum(item.get("match_basis"), {"UNIQUE_NUCLEUS_POLARITY_MATCH", "UNIQUE_REFERENT_RELATION_POLARITY_MATCH", "UNIQUE_UNKNOWN_SCOPE_MATCH", "UNIQUE_SIGNIFICANCE_MATCH", "UNIQUE_INTENTION_MODALITY_MATCH", "UNIQUE_SELF_DENIAL_BOUNDARY_MATCH", "UNIQUE_COUNTERPOSITION_MATCH", "UNIQUE_BOUND_RECEPTION_TARGET_MATCH"}, f"{path}.match_basis", issues)
            count = _int(item.get("match_candidate_count"), f"{path}.match_candidate_count", issues, minimum=1, maximum=1)
            if count != 1:
                _add(issues, "UNIQUE_MATCH_REQUIRED", f"{path}.match_candidate_count")
            atom = witness_atoms.get(atom_id)
            obligation = obligations.get(obligation_id)
            if atom is None:
                _add(issues, "UNRESOLVED_ATOM_REFERENCE", f"{path}.atom_id")
            if obligation is None:
                _add(issues, "UNRESOLVED_OBLIGATION_REFERENCE", f"{path}.obligation_id")
            if atom is not None and obligation is not None and _ATOM_TO_OBLIGATION_KIND.get(atom.get("kind")) != obligation.get("kind"):
                _add(issues, "ATOM_OBLIGATION_KIND_MISMATCH", path)
            if atom is not None and obligation is not None:
                for field in ("temporal_scope", "referent_scope"):
                    if atom.get(field) != obligation.get(field):
                        _add(issues, "ATOM_OBLIGATION_FEATURE_MISMATCH", f"{path}.{field}")
                if atom.get("kind") != "bound_emlis_reception":
                    for field in ("polarity", "modality"):
                        if atom.get(field) != obligation.get(field):
                            _add(issues, "ATOM_OBLIGATION_FEATURE_MISMATCH", f"{path}.{field}")
                elif atom.get("reception_act") not in obligation.get(
                    "allowed_response_acts", []
                ):
                    _add(issues, "ATOM_OBLIGATION_FEATURE_MISMATCH", f"{path}.match_basis")
            expected_match_basis = {
                "grounded_nucleus": "UNIQUE_NUCLEUS_POLARITY_MATCH",
                "grounded_relation": "UNIQUE_REFERENT_RELATION_POLARITY_MATCH",
                "unknown_boundary": "UNIQUE_UNKNOWN_SCOPE_MATCH",
                "significance_or_shift": "UNIQUE_SIGNIFICANCE_MATCH",
                "intention_or_next_action": "UNIQUE_INTENTION_MODALITY_MATCH",
                "self_denial_boundary": "UNIQUE_SELF_DENIAL_BOUNDARY_MATCH",
                "bounded_counterposition": "UNIQUE_COUNTERPOSITION_MATCH",
                "bound_emlis_reception": "UNIQUE_BOUND_RECEPTION_TARGET_MATCH",
            }.get(atom.get("kind") if atom is not None else None)
            if expected_match_basis is not None and item.get("match_basis") != expected_match_basis:
                _add(issues, "MATCH_BASIS_MISMATCH", f"{path}.match_basis")
            if obligation is not None:
                if evidence is not None and not set(evidence) <= set(obligation.get("evidence_ids", [])):
                    _add(issues, "UNRESOLVED_EVIDENCE_REFERENCE", f"{path}.evidence_ids")
                if topics is not None and not set(topics) <= set(obligation.get("topic_scope_ids", [])):
                    _add(issues, "UNRESOLVED_TOPIC_REFERENCE", f"{path}.topic_scope_ids")
                if relation is not None and relation not in obligation.get("relation_ids", []):
                    _add(issues, "UNRESOLVED_RELATION_REFERENCE", f"{path}.relation_id")
                if atom is not None and atom.get("kind") == "grounded_relation" and relation is None:
                    _add(issues, "RELATION_BINDING_REQUIRED", f"{path}.relation_id")
                if atom is not None and atom.get("kind") != "grounded_relation" and relation is not None:
                    _add(issues, "RELATION_BINDING_FORBIDDEN", f"{path}.relation_id")
                if atom is not None and atom.get("kind") == "grounded_relation" and relation is not None:
                    descriptor = next(
                        (
                            row
                            for row in obligation.get("relation_directions", [])
                            if type(row) is dict
                            and row.get("relation_id") == relation
                        ),
                        None,
                    )
                    if descriptor is None or atom.get("direction") != descriptor.get(
                        "direction"
                    ) or atom.get("relation_type") != descriptor.get("relation_type"):
                        _add(issues, "RELATION_DESCRIPTOR_MISMATCH", path)
                if obligation.get("kind") == STANCE_KIND:
                    if targets != obligation.get("target_obligation_ids"):
                        _add(issues, "STANCE_TARGET_MISMATCH", f"{path}.target_obligation_ids")
                elif targets != []:
                    _add(issues, "NONSTANCE_TARGET_FORBIDDEN", f"{path}.target_obligation_ids")
    for index, atom_id in enumerate(atom_ids):
        if atom_id in atom_ids[:index]:
            _add(issues, "DUPLICATE_ID", f"$.bindings[{index}].atom_id")
    for index, obligation_id in enumerate(obligation_ids):
        if obligation_id in obligation_ids[:index]:
            _add(issues, "DUPLICATE_ID", f"$.bindings[{index}].obligation_id")
    if status == "matched" and set(atom_ids) != set(witness_atoms):
        _add(issues, "WITNESS_BINDING_COVERAGE_MISMATCH", "$.bindings")
    required_obligation_ids = set(obligation_ledger.get("required_obligation_ids", []))
    if status == "matched" and not required_obligation_ids <= set(obligation_ids):
        _add(issues, "REQUIRED_BINDING_COVERAGE_MISSING", "$.bindings")
    binding_by_atom = {row.get("atom_id"): row for row in rows}
    for index, row in enumerate(rows):
        atom = witness_atoms.get(row.get("atom_id"), {})
        if atom.get("kind") != "bound_emlis_reception":
            continue
        target_obligations = [
            binding_by_atom.get(target_atom, {}).get("obligation_id")
            for target_atom in atom.get("target_atom_ids", [])
        ]
        if target_obligations != row.get("target_obligation_ids"):
            _add(issues, "STANCE_ATOM_TARGET_BINDING_MISMATCH", f"$.bindings[{index}].target_obligation_ids")
    return _final(issues)


_RECEIPT_KEYS = {
    "schema_version",
    "candidate_version_id",
    "run_id",
    "batch_id",
    "sample_source",
    "case_identity_commitment",
    "commitment_policy",
    "app_reachable_validation",
    "observation_stage",
    "observation_stage_context_commitment",
    "source_dependency_closure_sha256",
    "source_observation_plan_commitment",
    "obligation_ledger_commitment",
    "content_plan_commitment",
    "candidate_set_commitment",
    "selected_discourse_plan_commitment",
    "selected_surface_ast_commitment",
    "selected_candidate_body_commitment",
    "parsed_witness_binding_commitment",
    "hard_gate",
    "selector_decision",
    "v1_baseline_body_commitment",
    "local_product_review",
    "previous_output",
    "environment_sha256",
    "runner_sha256",
    "rubric_sha256",
    "body_free",
}
_FORBIDDEN_BODY_KEYS = frozenset(
    {
        "raw_input",
        "input",
        "thought_text",
        "action_text",
        "question_answer",
        "supplemental_answer",
        "comment_text",
        "candidate_text",
        "final_text",
        "visible_body",
        "response_text",
        "local_review_note",
        "free_text",
        "username",
        "honorific",
        "covered_obligation_ids",
        "realized_unit_ids",
    }
)


def _scan_forbidden_body_keys(value: Any, path: str, issues: list[ContractIssue]) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if key in _FORBIDDEN_BODY_KEYS:
                _add(issues, "BODY_CONTENT_FORBIDDEN", f"{path}.{key}")
            _scan_forbidden_body_keys(item, f"{path}.{key}", issues)
    elif type(value) is list:
        for index, item in enumerate(value):
            _scan_forbidden_body_keys(item, f"{path}[{index}]", issues)


def validate_case_evidence_receipt(
    value: Any,
    *,
    authority: ReceiptLineageAuthority,
) -> tuple[ContractIssue, ...]:
    issues: list[ContractIssue] = []
    obj = _object(value, _RECEIPT_KEYS, "$", issues)
    if obj is None:
        return _final(issues)
    _scan_forbidden_body_keys(obj, "$", issues)
    _schema(obj.get("schema_version"), RECEIPT_SCHEMA, "$.schema_version", issues)
    _string(obj.get("candidate_version_id"), "$.candidate_version_id", issues, pattern=_ID_PATTERNS["candidate_version_id"])
    _string(obj.get("run_id"), "$.run_id", issues, pattern=_ID_PATTERNS["run_id"])
    _string(obj.get("batch_id"), "$.batch_id", issues, pattern=_ID_PATTERNS["batch_id"])
    _enum(obj.get("sample_source"), {"karen_generated", "other_ai_generated_reviewed", "real_user_current_valid", "known_regression"}, "$.sample_source", issues)
    _sha(obj.get("case_identity_commitment"), "$.case_identity_commitment", issues)
    body_free = _bool(obj.get("body_free"), "$.body_free", issues)
    if body_free is not True:
        _add(issues, "BODY_FREE_REQUIRED", "$.body_free")
    policy = _object(obj.get("commitment_policy"), {"scheme", "policy_sha256", "key_or_nonce_stored_in_receipt"}, "$.commitment_policy", issues)
    if policy is not None:
        _enum(policy.get("scheme"), {"hmac_sha256_v1", "salted_sha256_v1"}, "$.commitment_policy.scheme", issues)
        _parent(policy.get("policy_sha256"), authority.commitment_policy_sha256, "$.commitment_policy.policy_sha256", issues)
        stored = _bool(policy.get("key_or_nonce_stored_in_receipt"), "$.commitment_policy.key_or_nonce_stored_in_receipt", issues)
        if stored is not False:
            _add(issues, "COMMITMENT_SECRET_FORBIDDEN", "$.commitment_policy.key_or_nonce_stored_in_receipt")
    app = _object(obj.get("app_reachable_validation"), {"status", "contract_version"}, "$.app_reachable_validation", issues)
    if app is not None:
        _const(app.get("status"), "passed", "$.app_reachable_validation.status", issues)
        _const(app.get("contract_version"), "cocolon.input_contract.20260714", "$.app_reachable_validation.contract_version", issues)
    _enum(obj.get("observation_stage"), OBSERVATION_STAGES, "$.observation_stage", issues)
    if obj.get("observation_stage") != authority.observation_stage:
        _add(issues, "UPSTREAM_STAGE_MISMATCH", "$.observation_stage")
    expected_fields = {
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
        "v1_baseline_body_commitment": authority.v1_baseline_body_commitment,
        "environment_sha256": authority.environment_sha256,
        "runner_sha256": authority.runner_sha256,
        "rubric_sha256": authority.rubric_sha256,
    }
    for field, expected in expected_fields.items():
        _parent(obj.get(field), expected, f"$.{field}", issues)
    gate_status: str | None = None
    hard_gate = _object(obj.get("hard_gate"), {"status", "failed_codes"}, "$.hard_gate", issues)
    if hard_gate is not None:
        gate_status = _enum(hard_gate.get("status"), {"passed", "failed"}, "$.hard_gate.status", issues)
        failed = _string_list(hard_gate.get("failed_codes"), "$.hard_gate.failed_codes", issues, pattern=_MACHINE_CODE_RE)
        if (gate_status == "passed" and failed) or (gate_status == "failed" and not failed):
            _add(issues, "GATE_STATUS_CODE_MISMATCH", "$.hard_gate")
    selection_status: str | None = None
    selector = _object(obj.get("selector_decision"), {"status", "selected_candidate_id", "selection_attributes_sha256"}, "$.selector_decision", issues)
    if selector is not None:
        selection_status = _enum(selector.get("status"), {"selected", "no_valid_candidate"}, "$.selector_decision.status", issues)
        if selection_status == "selected":
            _string(selector.get("selected_candidate_id"), "$.selector_decision.selected_candidate_id", issues, pattern=re.compile(r"^nls3cand_[0-9a-f]{16,64}$"))
        elif selector.get("selected_candidate_id") is not None:
            _add(issues, "SELECTED_CANDIDATE_FORBIDDEN", "$.selector_decision.selected_candidate_id")
        _sha(selector.get("selection_attributes_sha256"), "$.selector_decision.selection_attributes_sha256", issues)
    review_status: str | None = None
    review = _object(obj.get("local_product_review"), {"status", "reason_codes"}, "$.local_product_review", issues)
    if review is not None:
        review_status = _enum(review.get("status"), {"passed", "failed", "not_reviewed"}, "$.local_product_review.status", issues)
        reasons = _string_list(review.get("reason_codes"), "$.local_product_review.reason_codes", issues, minimum=0 if review_status == "not_reviewed" else 1, pattern=_MACHINE_CODE_RE)
        if review_status == "not_reviewed" and reasons:
            _add(issues, "REVIEW_STATUS_CODE_MISMATCH", "$.local_product_review")
    if (gate_status == "passed") != (selection_status == "selected"):
        _add(issues, "RECEIPT_GATE_SELECTOR_MISMATCH", "$.selector_decision")
    if review_status == "passed" and gate_status != "passed":
        _add(issues, "RECEIPT_REVIEW_GATE_MISMATCH", "$.local_product_review")
    previous = _object(obj.get("previous_output"), {"commitment", "changed"}, "$.previous_output", issues)
    if previous is not None:
        commitment = previous.get("commitment")
        changed = previous.get("changed")
        _sha(commitment, "$.previous_output.commitment", issues, nullable=True)
        if changed is not None:
            _bool(changed, "$.previous_output.changed", issues)
        if (commitment is None) != (changed is None):
            _add(issues, "PREVIOUS_OUTPUT_STATE_MISMATCH", "$.previous_output")
        if commitment != authority.previous_output_commitment or changed is not authority.previous_output_changed:
            _add(issues, "PREVIOUS_OUTPUT_AUTHORITY_MISMATCH", "$.previous_output")
    return _final(issues)


def forbidden_imports_in_source(source: str) -> tuple[str, ...]:
    """Return forbidden static/dynamic import targets found in Python source."""

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return ("<syntax_error>",)
    found: set[str] = set()
    for node in ast.walk(tree):
        targets: list[str] = []
        if isinstance(node, ast.Import):
            targets.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                targets.append(node.module)
            targets.extend(alias.name for alias in node.names if alias.name != "*")
        elif isinstance(node, ast.Call):
            literal_target: str | None = None
            if (
                node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
            ):
                literal_target = node.args[0].value
            else:
                for keyword in node.keywords:
                    if (
                        keyword.arg == "name"
                        and isinstance(keyword.value, ast.Constant)
                        and isinstance(keyword.value.value, str)
                    ):
                        literal_target = keyword.value.value
            if literal_target is not None:
                if isinstance(node.func, ast.Name) and node.func.id == "__import__":
                    targets.append(literal_target)
                elif isinstance(node.func, ast.Attribute) and node.func.attr == "import_module":
                    targets.append(literal_target)
        for target in targets:
            components = target.split(".")
            for forbidden in FORBIDDEN_CORE_IMPORTS:
                if forbidden in components:
                    found.add(forbidden)
    return tuple(sorted(found))


def forbidden_imports_in_module_tree(paths: Sequence[Path]) -> tuple[tuple[str, str], ...]:
    found: list[tuple[str, str]] = []
    for path in paths:
        source = path.read_text(encoding="utf-8")
        found.extend((str(path), target) for target in forbidden_imports_in_source(source))
    return tuple(sorted(found))


_ARTIFACT_CHAIN_KEYS = {
    "observation_stage_context",
    "semantic_obligation_ledger",
    "content_selection_plan",
    "discourse_plan",
    "surface_ast",
    "parsed_surface_witness",
    "verified_surface_binding",
    "case_evidence_receipt",
}


def validate_artifact_chain(
    value: Any,
    *,
    original_input_bundle: Any,
    ledger_authority: LedgerSourceAuthority,
    candidate_text_bytes: bytes,
    receipt_authority: ReceiptLineageAuthority,
    trusted_future_authority: TrustedFutureStageAuthority | None = None,
    supplemental_answer_bundle: Any | None = None,
) -> tuple[ContractIssue, ...]:
    """Validate every owner before accepting any downstream parent hash.

    A child validator proves that its parent bytes match its stored hash.  This
    chain validator additionally proves that each parent is valid under its own
    independently supplied authority.  Formal Step 3 acceptance therefore uses
    this function, so recomputing a forged parent and all descendant hashes
    cannot turn an invalid upstream artifact into an accepted chain.
    """

    issues: list[ContractIssue] = []
    artifacts = _object(value, _ARTIFACT_CHAIN_KEYS, "$", issues)
    if artifacts is None:
        return _final(issues)

    def add_owner_issues(
        owner: str, owner_issues: tuple[ContractIssue, ...]
    ) -> None:
        for issue in owner_issues:
            suffix = issue.path[1:] if issue.path.startswith("$") else f".{issue.path}"
            issues.append(ContractIssue(issue.code, f"$.{owner}{suffix}"))

    stage = artifacts["observation_stage_context"]
    ledger = artifacts["semantic_obligation_ledger"]
    content = artifacts["content_selection_plan"]
    discourse = artifacts["discourse_plan"]
    surface_ast = artifacts["surface_ast"]
    witness = artifacts["parsed_surface_witness"]
    binding = artifacts["verified_surface_binding"]
    receipt = artifacts["case_evidence_receipt"]

    if (
        type(ledger) is not dict
        or ledger.get("source_observation_stage_context_sha256")
        != artifact_sha256(stage)
    ):
        issues.append(
            ContractIssue(
                "PARENT_CHAIN_MISMATCH",
                "$.semantic_obligation_ledger.source_observation_stage_context_sha256",
            )
        )
    if (
        type(stage) is not dict
        or type(receipt) is not dict
        or receipt.get("observation_stage") != stage.get("stage")
    ):
        issues.append(
            ContractIssue(
                "PARENT_CHAIN_MISMATCH",
                "$.case_evidence_receipt.observation_stage",
            )
        )

    add_owner_issues(
        "observation_stage_context",
        validate_observation_stage_context(
            stage,
            original_input_bundle=original_input_bundle,
            trusted_future_authority=trusted_future_authority,
            supplemental_answer_bundle=supplemental_answer_bundle,
        ),
    )
    add_owner_issues(
        "semantic_obligation_ledger",
        validate_semantic_obligation_ledger(ledger, authority=ledger_authority),
    )
    add_owner_issues(
        "content_selection_plan",
        validate_content_selection_plan(content, obligation_ledger=ledger),
    )
    add_owner_issues(
        "discourse_plan",
        validate_discourse_plan(
            discourse,
            content_plan=content,
            obligation_ledger=ledger,
        ),
    )
    add_owner_issues(
        "surface_ast",
        validate_surface_ast(
            surface_ast,
            discourse_plan=discourse,
            obligation_ledger=ledger,
        ),
    )
    add_owner_issues(
        "parsed_surface_witness",
        validate_parsed_surface_witness(
            witness,
            candidate_text_bytes=candidate_text_bytes,
        ),
    )
    add_owner_issues(
        "verified_surface_binding",
        validate_verified_surface_binding(
            binding,
            parsed_surface_witness=witness,
            obligation_ledger=ledger,
        ),
    )
    add_owner_issues(
        "case_evidence_receipt",
        validate_case_evidence_receipt(receipt, authority=receipt_authority),
    )
    return _final(issues)


def _fail_closed_validator(function: Any) -> Any:
    """Convert malformed raw-Mapping traversal failures into deterministic RED.

    Field-level helpers still return the more specific issue whenever possible.
    This final boundary covers adversarial shapes (for example a list used as an
    ID and then encountered by a cross-reference check) without allowing a
    validator exception to become acceptance or an application crash.
    """

    @wraps(function)
    def guarded(*args: Any, **kwargs: Any) -> tuple[ContractIssue, ...]:
        try:
            return function(*args, **kwargs)
        except (AttributeError, KeyError, TypeError, ValueError, UnicodeError, RecursionError):
            return (ContractIssue("MALFORMED_ARTIFACT", "$"),)

    return guarded


validate_observation_stage_context = _fail_closed_validator(
    validate_observation_stage_context
)
validate_semantic_obligation_ledger = _fail_closed_validator(
    validate_semantic_obligation_ledger
)
validate_content_selection_plan = _fail_closed_validator(
    validate_content_selection_plan
)
validate_discourse_plan = _fail_closed_validator(validate_discourse_plan)
validate_surface_ast = _fail_closed_validator(validate_surface_ast)
validate_parsed_surface_witness = _fail_closed_validator(
    validate_parsed_surface_witness
)
validate_verified_surface_binding = _fail_closed_validator(
    validate_verified_surface_binding
)
validate_case_evidence_receipt = _fail_closed_validator(
    validate_case_evidence_receipt
)
validate_artifact_chain = _fail_closed_validator(validate_artifact_chain)


__all__ = [
    "AST_SCHEMA",
    "BINDING_SCHEMA",
    "CONTENT_SCHEMA",
    "ContractIssue",
    "DISCOURSE_SCHEMA",
    "FORBIDDEN_CORE_IMPORTS",
    "LEDGER_SCHEMA",
    "LedgerSourceAuthority",
    "RECEIPT_SCHEMA",
    "ReceiptLineageAuthority",
    "STAGE_SCHEMA",
    "STOPPED_V2_MODULES",
    "TrustedFutureStageAuthority",
    "TrustedSourceSemantic",
    "WITNESS_SCHEMA",
    "artifact_sha256",
    "canonical_json_bytes",
    "derive_content_id",
    "derive_obligation_id",
    "forbidden_imports_in_module_tree",
    "forbidden_imports_in_source",
    "issue_codes",
    "load_canonical_json_bytes",
    "validate_artifact_chain",
    "validate_case_evidence_receipt",
    "validate_content_selection_plan",
    "validate_discourse_plan",
    "validate_observation_stage_context",
    "validate_parsed_surface_witness",
    "validate_semantic_obligation_ledger",
    "validate_surface_ast",
    "validate_verified_surface_binding",
]
