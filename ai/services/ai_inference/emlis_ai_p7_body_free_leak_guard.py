# -*- coding: utf-8 -*-
"""P7 R13 body-free leak guard contract and helper definitions.

R13-0/R13-1 fixed the baseline and defined the body-free boundary without
materializing raw input bodies, comment text bodies, candidate bodies, terminal
output, or public contract mutations.

R13-2 adds the recursive scanner/assertion helper. Raw runtime values may be
supplied for matching, but they must not be copied into returned violations or
exception messages. Product Quality Connection E2E assertion replacement remains
a later R13 step.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Final

from emlis_ai_p7_contracts import (
    P7_FORBIDDEN_BODY_KEYS,
    P7_FORBIDDEN_TRUE_FLAGS,
    P7_PHASE,
    assert_p7_no_body_payload_or_contract_mutation,
    clean_identifier,
    dedupe_identifiers,
    safe_mapping,
)

P7_BODY_FREE_LEAK_GUARD_CONTRACT_SCHEMA_VERSION: Final = "cocolon.emlis.p7.body_free_leak_guard_contract.v1"
P7_BODY_FREE_LEAK_GUARD_CONTRACT_STEP: Final = "P7-R13-1_BodyFreeLeakGuardContract_20260613"
P7_BODY_FREE_LEAK_VIOLATION_SCHEMA_VERSION: Final = "cocolon.emlis.p7.body_free_leak_violation.v1"
P7_BODY_FREE_LEAK_GUARD_SOURCE_MODE: Final = "local_snapshot"
P7_BODY_FREE_LEAK_GUARD_GIT_CHECKED: Final = False

P7_BODY_FREE_SCOPE_PRODUCT_QUALITY_CONNECTION_SCORECARD: Final = "product_quality_connection_scorecard"

P7_BODY_FREE_SAFE_CURRENT_INPUT_RUBRIC_PATH_SUFFIX: Final = (
    "phase2_product_readfeel_rubric.dimensions.evidence_boundary.green"
)
P7_BODY_FREE_SAFE_CURRENT_INPUT_RUBRIC_VALUE: Final = (
    "claims_stay_within_current_input_or_safe_known_user_fact"
)

_ALLOWED_SCOPES: Final[frozenset[str]] = frozenset({P7_BODY_FREE_SCOPE_PRODUCT_QUALITY_CONNECTION_SCORECARD})
_FORBIDDEN_RAW_VALUE_REF_KEYS: Final[frozenset[str]] = frozenset(
    {
        "value",
        "raw_value",
        "literal_value",
        "sample_value",
        "body_value",
        "input_value",
        "comment_text_value",
        "candidate_body_value",
        "surface_body_value",
    }
)
_ALLOWED_RAW_VALUE_REF_KINDS: Final[frozenset[str]] = frozenset(
    {
        "raw_current_input_body",
        "raw_current_input_id",
        "raw_comment_text_body",
        "raw_candidate_body",
        "raw_surface_body",
        "raw_history_body",
    }
)
_REQUIRED_FORBIDDEN_KEYS: Final[frozenset[str]] = frozenset(
    {
        "current_input",
        "raw_input",
        "source_text",
        "memo",
        "memo_action",
        "comment_text",
        "candidate_body",
        "surface_body",
    }
)
_REQUIRED_FORBIDDEN_TRUE_FLAGS: Final[frozenset[str]] = frozenset(
    {
        "raw_input_included",
        "comment_text_body_included",
        "candidate_body_included",
        "surface_body_included",
        "release_allowed",
    }
)
_REQUIRED_FAILURE_POLICY_FALSE_KEYS: Final[tuple[str, str]] = ("include_raw_values", "include_serialized_payload")


class P7BodyFreeLeakGuardContractError(ValueError):
    """Raised when the R13 body-free leak guard contract is malformed."""


class P7BodyFreeLeakGuardError(ValueError):
    """Raised when a body-free leak guard assertion finds compact violations."""


def _sorted_texts(values: Iterable[Any]) -> list[str]:
    return sorted(dedupe_identifiers(values, limit=240, max_length=160))


def _base_forbidden_key_names() -> list[str]:
    return _sorted_texts(P7_FORBIDDEN_BODY_KEYS)


def _base_forbidden_true_flags() -> list[str]:
    return _sorted_texts(P7_FORBIDDEN_TRUE_FLAGS)


def _default_forbidden_raw_value_refs() -> list[dict[str, Any]]:
    return [
        {
            "ref": "current_input.memo",
            "kind": "raw_current_input_body",
            "minimum_length": 1,
            "value_materialized_in_contract": False,
        },
        {
            "ref": "current_input.id",
            "kind": "raw_current_input_id",
            "minimum_length": 1,
            "value_materialized_in_contract": False,
        },
        {
            "ref": "input_feedback.comment_text",
            "kind": "raw_comment_text_body",
            "minimum_length": 1,
            "value_materialized_in_contract": False,
        },
        {
            "ref": "product_quality.candidate_body",
            "kind": "raw_candidate_body",
            "minimum_length": 1,
            "value_materialized_in_contract": False,
        },
    ]


def _default_allowed_string_occurrences() -> list[dict[str, str]]:
    return [
        {
            "token": "current_input",
            "path_suffix": P7_BODY_FREE_SAFE_CURRENT_INPUT_RUBRIC_PATH_SUFFIX,
            "exact_value": P7_BODY_FREE_SAFE_CURRENT_INPUT_RUBRIC_VALUE,
            "reason_code": "safe_rubric_vocabulary_not_raw_payload",
        }
    ]


def _default_failure_output_policy() -> dict[str, Any]:
    return {
        "include_raw_values": False,
        "include_serialized_payload": False,
        "max_reported_violations": 6,
        "max_path_length": 220,
    }


def build_p7_product_quality_connection_scorecard_body_free_contract(
    *,
    scope: Any = P7_BODY_FREE_SCOPE_PRODUCT_QUALITY_CONNECTION_SCORECARD,
    forbidden_raw_value_refs: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build the R13-1 body-free contract for Product Quality scorecards.

    This contract stores only raw-value *refs*.  Runtime raw values are supplied
    to the later scanner/assertion layer and must not be serialized into this
    contract material.
    """

    contract = {
        "schema_version": P7_BODY_FREE_LEAK_GUARD_CONTRACT_SCHEMA_VERSION,
        "implementation_step": P7_BODY_FREE_LEAK_GUARD_CONTRACT_STEP,
        "phase": P7_PHASE,
        "source_mode": P7_BODY_FREE_LEAK_GUARD_SOURCE_MODE,
        "git_checked": P7_BODY_FREE_LEAK_GUARD_GIT_CHECKED,
        "scope": clean_identifier(scope, default=P7_BODY_FREE_SCOPE_PRODUCT_QUALITY_CONNECTION_SCORECARD, max_length=120),
        "contract_kind": "body_free_leak_guard_definition_only",
        "scanner_implemented": False,
        "e2e_assertion_replaced": False,
        "forbidden_key_names": _base_forbidden_key_names(),
        "forbidden_raw_value_refs": [dict(item) for item in (forbidden_raw_value_refs or _default_forbidden_raw_value_refs())],
        "forbidden_true_flags": _base_forbidden_true_flags(),
        "allowed_string_occurrences": _default_allowed_string_occurrences(),
        "failure_output_policy": _default_failure_output_policy(),
        "release_boundary": {
            "p7_complete": False,
            "p8_start_allowed": False,
            "release_allowed": False,
        },
        "body_free": True,
        "raw_input_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "terminal_output_included": False,
    }
    assert_p7_body_free_leak_guard_contract(contract)
    return contract


def assert_p7_body_free_leak_guard_contract(contract: Mapping[str, Any]) -> bool:
    """Validate the R13-1 body-free leak guard contract definition."""

    data = safe_mapping(contract)
    if data.get("schema_version") != P7_BODY_FREE_LEAK_GUARD_CONTRACT_SCHEMA_VERSION:
        raise P7BodyFreeLeakGuardContractError("unexpected P7 body-free leak guard contract schema_version")
    if data.get("implementation_step") != P7_BODY_FREE_LEAK_GUARD_CONTRACT_STEP:
        raise P7BodyFreeLeakGuardContractError("unexpected P7 body-free leak guard implementation_step")
    if data.get("phase") != P7_PHASE:
        raise P7BodyFreeLeakGuardContractError("body-free leak guard contract must stay in P7 phase")
    if data.get("source_mode") != P7_BODY_FREE_LEAK_GUARD_SOURCE_MODE:
        raise P7BodyFreeLeakGuardContractError("body-free leak guard contract must be local_snapshot sourced")
    if data.get("git_checked") is not False:
        raise P7BodyFreeLeakGuardContractError("body-free leak guard contract must keep git_checked=false for local work")
    if clean_identifier(data.get("scope"), max_length=120) not in _ALLOWED_SCOPES:
        raise P7BodyFreeLeakGuardContractError("unsupported body-free leak guard scope")
    if data.get("contract_kind") != "body_free_leak_guard_definition_only":
        raise P7BodyFreeLeakGuardContractError("R13-1 contract must remain definition-only")
    if data.get("scanner_implemented") is not False or data.get("e2e_assertion_replaced") is not False:
        raise P7BodyFreeLeakGuardContractError("R13-1 must not claim scanner implementation or E2E assertion replacement")

    forbidden_keys = set(dedupe_identifiers(data.get("forbidden_key_names"), limit=320, max_length=160))
    if not _REQUIRED_FORBIDDEN_KEYS.issubset(forbidden_keys):
        raise P7BodyFreeLeakGuardContractError("body-free contract misses required forbidden key names")

    forbidden_true_flags = set(dedupe_identifiers(data.get("forbidden_true_flags"), limit=320, max_length=160))
    if not _REQUIRED_FORBIDDEN_TRUE_FLAGS.issubset(forbidden_true_flags):
        raise P7BodyFreeLeakGuardContractError("body-free contract misses required forbidden true flags")

    raw_value_refs = data.get("forbidden_raw_value_refs")
    if not isinstance(raw_value_refs, Sequence) or isinstance(raw_value_refs, (str, bytes, bytearray)) or not raw_value_refs:
        raise P7BodyFreeLeakGuardContractError("body-free contract must list forbidden raw value refs")
    for raw_item in raw_value_refs:
        item = safe_mapping(raw_item)
        if not item:
            raise P7BodyFreeLeakGuardContractError("forbidden raw value ref must be a mapping")
        if _FORBIDDEN_RAW_VALUE_REF_KEYS & set(map(str, item.keys())):
            raise P7BodyFreeLeakGuardContractError("forbidden raw value refs must not materialize raw values")
        ref = clean_identifier(item.get("ref"), max_length=160)
        kind = clean_identifier(item.get("kind"), max_length=120)
        if not ref or kind not in _ALLOWED_RAW_VALUE_REF_KINDS:
            raise P7BodyFreeLeakGuardContractError("forbidden raw value refs need safe ref and known kind")
        if item.get("value_materialized_in_contract") is not False:
            raise P7BodyFreeLeakGuardContractError("forbidden raw values must stay unmaterialized in contract")
        minimum_length = item.get("minimum_length")
        if not isinstance(minimum_length, int) or minimum_length < 1:
            raise P7BodyFreeLeakGuardContractError("forbidden raw value refs need positive minimum_length")

    allowed_occurrences = data.get("allowed_string_occurrences")
    if not isinstance(allowed_occurrences, Sequence) or isinstance(allowed_occurrences, (str, bytes, bytearray)):
        raise P7BodyFreeLeakGuardContractError("allowed string occurrences must be a list")
    safe_occurrence_found = False
    for raw_item in allowed_occurrences:
        item = safe_mapping(raw_item)
        if (
            item.get("token") == "current_input"
            and item.get("path_suffix") == P7_BODY_FREE_SAFE_CURRENT_INPUT_RUBRIC_PATH_SUFFIX
            and item.get("exact_value") == P7_BODY_FREE_SAFE_CURRENT_INPUT_RUBRIC_VALUE
            and item.get("reason_code") == "safe_rubric_vocabulary_not_raw_payload"
        ):
            safe_occurrence_found = True
    if not safe_occurrence_found:
        raise P7BodyFreeLeakGuardContractError("safe current_input rubric vocabulary allowance must be path-limited")

    failure_policy = safe_mapping(data.get("failure_output_policy"))
    for key in _REQUIRED_FAILURE_POLICY_FALSE_KEYS:
        if failure_policy.get(key) is not False:
            raise P7BodyFreeLeakGuardContractError(f"failure output policy must keep {key}=false")
    max_reported = failure_policy.get("max_reported_violations")
    max_path = failure_policy.get("max_path_length")
    if not isinstance(max_reported, int) or not 1 <= max_reported <= 20:
        raise P7BodyFreeLeakGuardContractError("failure output policy max_reported_violations must be bounded")
    if not isinstance(max_path, int) or not 40 <= max_path <= 300:
        raise P7BodyFreeLeakGuardContractError("failure output policy max_path_length must be bounded")

    release_boundary = safe_mapping(data.get("release_boundary"))
    for key in ("p7_complete", "p8_start_allowed", "release_allowed"):
        if release_boundary.get(key) is not False:
            raise P7BodyFreeLeakGuardContractError(f"R13-1 contract must keep {key}=false")

    for key in (
        "body_free",
        "raw_input_included",
        "comment_text_body_included",
        "candidate_body_included",
        "surface_body_included",
        "terminal_output_included",
    ):
        expected = True if key == "body_free" else False
        if data.get(key) is not expected:
            raise P7BodyFreeLeakGuardContractError(f"body-free leak guard contract must keep {key}={expected}")

    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_body_free_leak_guard_contract")
    return True


_SAFE_PATH_CHARS: Final[frozenset[str]] = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_:-"
)
_MAX_FAILURE_MESSAGE_CHARS: Final[int] = 1100


def _path_endswith(path: str, suffix: str) -> bool:
    suffix_text = str(suffix).strip()
    return bool(suffix_text) and (path == suffix_text or path.endswith(f".{suffix_text}"))


def _safe_path_component(value: Any, *, max_length: int = 80) -> str:
    """Return a schema-like path component without leaking arbitrary key text."""

    text = clean_identifier(value, default="<key>", max_length=max_length)
    if not text:
        return "<key>"
    if any(char not in _SAFE_PATH_CHARS for char in text):
        return "<key>"
    return text


def _truncate_path(path: str, *, max_length: int) -> str:
    text = str(path)
    if len(text) <= max_length:
        return text
    if max_length <= 12:
        return text[:max_length]
    return f"...{text[-(max_length - 3):]}"


def _path_child(path: str, key: Any, *, max_path_length: int) -> str:
    return _truncate_path(f"{path}.{_safe_path_component(key)}", max_length=max_path_length)


def _path_index(path: str, index: int, *, max_path_length: int) -> str:
    return _truncate_path(f"{path}[{index}]", max_length=max_path_length)


def _failure_policy_from_contract(contract: Mapping[str, Any] | None) -> dict[str, Any]:
    default_policy = _default_failure_output_policy()
    policy = safe_mapping(safe_mapping(contract).get("failure_output_policy"))
    max_reported = policy.get("max_reported_violations", default_policy["max_reported_violations"])
    max_path = policy.get("max_path_length", default_policy["max_path_length"])
    return {
        "include_raw_values": False,
        "include_serialized_payload": False,
        "max_reported_violations": max_reported if isinstance(max_reported, int) and 1 <= max_reported <= 20 else default_policy["max_reported_violations"],
        "max_path_length": max_path if isinstance(max_path, int) and 40 <= max_path <= 300 else default_policy["max_path_length"],
    }


def _token_kind_for_ref(ref: str, contract: Mapping[str, Any] | None) -> str:
    ref_text = clean_identifier(ref, max_length=160)
    for raw_item in safe_mapping(contract).get("forbidden_raw_value_refs", []) or []:
        item = safe_mapping(raw_item)
        if item.get("ref") == ref_text:
            return clean_identifier(item.get("kind"), default="raw_current_input_body", max_length=120)
    lower_ref = ref_text.lower()
    if lower_ref.endswith(".id") or "input_id" in lower_ref:
        return "raw_current_input_id"
    if "comment_text" in lower_ref or "commenttext" in lower_ref:
        return "raw_comment_text_body"
    if "candidate" in lower_ref:
        return "raw_candidate_body"
    if "surface" in lower_ref:
        return "raw_surface_body"
    if "history" in lower_ref:
        return "raw_history_body"
    return "raw_current_input_body"


def _minimum_length_for_ref(ref: str, contract: Mapping[str, Any] | None) -> int:
    ref_text = clean_identifier(ref, max_length=160)
    for raw_item in safe_mapping(contract).get("forbidden_raw_value_refs", []) or []:
        item = safe_mapping(raw_item)
        if item.get("ref") == ref_text and isinstance(item.get("minimum_length"), int):
            return max(1, int(item["minimum_length"]))
    return 1


def _runtime_raw_value_specs(
    forbidden_raw_values: Mapping[str, Any] | None,
    *,
    contract: Mapping[str, Any] | None,
) -> list[dict[str, str]]:
    specs: list[dict[str, str]] = []
    for raw_ref, raw_spec in safe_mapping(forbidden_raw_values).items():
        ref = clean_identifier(raw_ref, max_length=160)
        if not ref:
            continue
        kind = _token_kind_for_ref(ref, contract)
        minimum_length = _minimum_length_for_ref(ref, contract)
        raw_value: Any = raw_spec
        if isinstance(raw_spec, Mapping):
            raw_map = safe_mapping(raw_spec)
            raw_value = raw_map.get("value")
            kind = clean_identifier(raw_map.get("kind"), default=kind, max_length=120)
            raw_min = raw_map.get("minimum_length")
            if isinstance(raw_min, int):
                minimum_length = max(1, raw_min)
        if raw_value is None:
            continue
        value_text = str(raw_value)
        if len(value_text) < minimum_length:
            continue
        specs.append({"ref": ref, "kind": kind, "value": value_text})
    return specs


def _allowed_occurrence_specs(
    allowed_string_occurrences: Sequence[Mapping[str, Any]] | None,
    *,
    contract: Mapping[str, Any] | None,
) -> list[dict[str, str]]:
    raw_occurrences: Any = allowed_string_occurrences
    if raw_occurrences is None:
        raw_occurrences = safe_mapping(contract).get("allowed_string_occurrences", _default_allowed_string_occurrences())
    if not isinstance(raw_occurrences, Sequence) or isinstance(raw_occurrences, (str, bytes, bytearray)):
        return []
    specs: list[dict[str, str]] = []
    for raw_item in raw_occurrences:
        item = safe_mapping(raw_item)
        token = clean_identifier(item.get("token"), max_length=160)
        path_suffix = clean_identifier(item.get("path_suffix"), max_length=260)
        exact_value = clean_identifier(item.get("exact_value"), max_length=400)
        reason_code = clean_identifier(item.get("reason_code"), default="safe_string_occurrence", max_length=160)
        if token and path_suffix and exact_value:
            specs.append(
                {
                    "token": token,
                    "path_suffix": path_suffix,
                    "exact_value": exact_value,
                    "reason_code": reason_code,
                }
            )
    return specs


def _is_allowed_string_occurrence(*, path: str, value: str, token: str, allowed_specs: Sequence[Mapping[str, str]]) -> bool:
    for item in allowed_specs:
        if (
            item.get("token") == token
            and value == item.get("exact_value")
            and _path_endswith(path, str(item.get("path_suffix", "")))
        ):
            return True
    return False


def _make_violation(
    *,
    violation_kind: str,
    path: str,
    token_ref: str,
    token_kind: str,
    max_path_length: int,
    reason_code: str = "",
) -> dict[str, Any]:
    violation = {
        "schema_version": P7_BODY_FREE_LEAK_VIOLATION_SCHEMA_VERSION,
        "violation_kind": clean_identifier(violation_kind, default="body_free_violation", max_length=120),
        "path": _truncate_path(path, max_length=max_path_length),
        "token_ref": clean_identifier(token_ref, default="body_free_token", max_length=160),
        "token_kind": clean_identifier(token_kind, default="body_free_token", max_length=120),
        "raw_value_included": False,
        "serialized_payload_included": False,
        "body_free": True,
    }
    reason = clean_identifier(reason_code, max_length=160)
    if reason:
        violation["reason_code"] = reason
    return violation


def collect_p7_body_free_leak_violations(
    value: Any,
    *,
    source: str,
    contract: Mapping[str, Any] | None = None,
    forbidden_keys: Iterable[str] | None = None,
    forbidden_raw_values: Mapping[str, Any] | None = None,
    forbidden_true_flags: Iterable[str] | None = None,
    allowed_string_occurrences: Sequence[Mapping[str, Any]] | None = None,
    max_violations: int | None = None,
) -> list[dict[str, Any]]:
    """Return compact body-free leak guard violations.

    Runtime raw values may be passed through ``forbidden_raw_values`` for
    matching, but they are never copied into the returned violations.
    """

    if contract is not None:
        assert_p7_body_free_leak_guard_contract(contract)
    policy = _failure_policy_from_contract(contract)
    max_reported = max_violations if isinstance(max_violations, int) and max_violations > 0 else policy["max_reported_violations"]
    max_reported = max(1, min(int(max_reported), 20))
    max_path_length = int(policy["max_path_length"])
    root_path = clean_identifier(source, default="payload", max_length=120)

    contract_map = safe_mapping(contract)
    forbidden_key_set = set(
        dedupe_identifiers(
            forbidden_keys if forbidden_keys is not None else contract_map.get("forbidden_key_names", _base_forbidden_key_names()),
            limit=320,
            max_length=160,
        )
    )
    forbidden_true_flag_set = set(
        dedupe_identifiers(
            forbidden_true_flags if forbidden_true_flags is not None else contract_map.get("forbidden_true_flags", _base_forbidden_true_flags()),
            limit=320,
            max_length=160,
        )
    )
    raw_specs = _runtime_raw_value_specs(forbidden_raw_values, contract=contract)
    allowed_specs = _allowed_occurrence_specs(allowed_string_occurrences, contract=contract)
    watched_allowed_tokens = sorted({item["token"] for item in allowed_specs if item.get("token")})

    violations: list[dict[str, Any]] = []

    def add_violation(*, violation_kind: str, path: str, token_ref: str, token_kind: str, reason_code: str = "") -> None:
        if len(violations) >= max_reported:
            return
        violations.append(
            _make_violation(
                violation_kind=violation_kind,
                path=path,
                token_ref=token_ref,
                token_kind=token_kind,
                max_path_length=max_path_length,
                reason_code=reason_code,
            )
        )

    def walk(node: Any, path: str) -> None:
        if len(violations) >= max_reported:
            return
        if isinstance(node, Mapping):
            for raw_key, child in node.items():
                key = str(raw_key)
                child_path = _path_child(path, key, max_path_length=max_path_length)
                if key in forbidden_key_set:
                    add_violation(
                        violation_kind="forbidden_key",
                        path=child_path,
                        token_ref=key,
                        token_kind="raw_payload_key",
                    )
                if key in forbidden_true_flag_set and child is True:
                    add_violation(
                        violation_kind="forbidden_true_flag",
                        path=child_path,
                        token_ref=key,
                        token_kind="contract_mutation_flag",
                    )
                walk(child, child_path)
                if len(violations) >= max_reported:
                    return
            return
        if isinstance(node, Sequence) and not isinstance(node, (str, bytes, bytearray)):
            for index, child in enumerate(node):
                walk(child, _path_index(path, index, max_path_length=max_path_length))
                if len(violations) >= max_reported:
                    return
            return
        if isinstance(node, str):
            for item in raw_specs:
                raw_value = item["value"]
                if raw_value and raw_value in node:
                    add_violation(
                        violation_kind="forbidden_raw_value",
                        path=path,
                        token_ref=item["ref"],
                        token_kind=item["kind"],
                    )
                    if len(violations) >= max_reported:
                        return
            for token in watched_allowed_tokens:
                if token in node and not _is_allowed_string_occurrence(
                    path=path,
                    value=node,
                    token=token,
                    allowed_specs=allowed_specs,
                ):
                    add_violation(
                        violation_kind="unsafe_unregistered_string_occurrence",
                        path=path,
                        token_ref=token,
                        token_kind="unregistered_safe_vocabulary",
                        reason_code="safe_vocabulary_path_or_value_not_allowlisted",
                    )
                    if len(violations) >= max_reported:
                        return

    walk(value, root_path)
    return violations


def _format_body_free_violation_message(source: str, violations: Sequence[Mapping[str, Any]]) -> str:
    compact_parts = [
        f"{item['violation_kind']} at {item['path']} token_ref={item['token_ref']} token_kind={item['token_kind']}"
        for item in violations[:6]
    ]
    source_label = clean_identifier(source, default="payload", max_length=120)
    message = f"{source_label} body-free leak guard violations ({len(violations)}): " + "; ".join(compact_parts)
    if len(message) > _MAX_FAILURE_MESSAGE_CHARS:
        return message[: _MAX_FAILURE_MESSAGE_CHARS - 3] + "..."
    return message


def assert_p7_body_free_no_payload_leak(
    value: Any,
    *,
    source: str,
    contract: Mapping[str, Any] | None = None,
    forbidden_keys: Iterable[str] | None = None,
    forbidden_raw_values: Mapping[str, Any] | None = None,
    forbidden_true_flags: Iterable[str] | None = None,
    allowed_string_occurrences: Sequence[Mapping[str, Any]] | None = None,
    max_violations: int | None = None,
) -> None:
    """Assert that ``value`` contains no body payload leak according to R13.

    The raised error contains only compact violation kind/path/token refs and
    never includes raw runtime values or serialized payload dumps.
    """

    violations = collect_p7_body_free_leak_violations(
        value,
        source=source,
        contract=contract,
        forbidden_keys=forbidden_keys,
        forbidden_raw_values=forbidden_raw_values,
        forbidden_true_flags=forbidden_true_flags,
        allowed_string_occurrences=allowed_string_occurrences,
        max_violations=max_violations,
    )
    if not violations:
        return
    raise P7BodyFreeLeakGuardError(_format_body_free_violation_message(source, violations))


__all__ = [
    "P7_BODY_FREE_LEAK_GUARD_CONTRACT_SCHEMA_VERSION",
    "P7_BODY_FREE_LEAK_GUARD_CONTRACT_STEP",
    "P7_BODY_FREE_LEAK_VIOLATION_SCHEMA_VERSION",
    "P7_BODY_FREE_SCOPE_PRODUCT_QUALITY_CONNECTION_SCORECARD",
    "P7_BODY_FREE_SAFE_CURRENT_INPUT_RUBRIC_PATH_SUFFIX",
    "P7_BODY_FREE_SAFE_CURRENT_INPUT_RUBRIC_VALUE",
    "P7BodyFreeLeakGuardContractError",
    "P7BodyFreeLeakGuardError",
    "assert_p7_body_free_leak_guard_contract",
    "assert_p7_body_free_no_payload_leak",
    "build_p7_product_quality_connection_scorecard_body_free_contract",
    "collect_p7_body_free_leak_violations",
]
