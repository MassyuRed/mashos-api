# -*- coding: utf-8 -*-
from __future__ import annotations

"""Strict private artifact contracts introduced by NLS v3 Step 8.

Step 3 froze ``parsed_surface_witness.v1`` before the surface grammar exposed
the closed ``choice`` and ``other`` unknown dimensions.  Step 8 therefore adds
v2 artifacts alongside, rather than changing any frozen v1 byte.  These
validators are deliberately builders of nothing: they only validate closed
JSON-shaped artifacts against final bytes and their source ledger.
"""

import hashlib
import re
import unicodedata
from functools import wraps
from typing import Any, Iterable, Mapping

from emlis_ai_nls_v3_artifact_contract import (
    LEDGER_SCHEMA,
    ContractIssue,
    LedgerSourceAuthority,
    artifact_sha256,
    validate_semantic_obligation_ledger,
)
from emlis_ai_surface_grammar_catalog_v3_step8 import (
    FROZEN_STEP8_SURFACE_GRAMMAR_CATALOG_SHA256 as FROZEN_SURFACE_GRAMMAR_CATALOG_SHA256,
)


WITNESS_V2_SCHEMA = "cocolon.emlis.nls_v3.parsed_surface_witness.v2"
BINDING_V2_SCHEMA = "cocolon.emlis.nls_v3.verified_surface_binding.v2"
FROZEN_PARSER_RULEBOOK_SHA256 = (
    "b0d218399eb19453479619a429d74d77e356813af49e3e446ffb707979b33d0d"
)
FROZEN_MATCHER_RULEBOOK_SHA256 = (
    "def32a4051acc24ed166a8a2c9dfd21dcf728cd70007d3133090f7a3ae762943"
)

_SHA_RE = re.compile(r"^[0-9a-f]{64}$")
_ATOM_ID_RE = re.compile(r"^atom_[0-9a-z_]{1,32}$")
_OBLIGATION_ID_RE = re.compile(r"^obl_[0-9a-f]{16}$")
_MACHINE_ID_RE = re.compile(r"^[a-z][a-z0-9_]{1,63}$")
_MACHINE_CODE_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,63}$")
_SEMANTIC_REF_RE = re.compile(r"^semantic_ref_[0-9a-f]{16}$")
_TOPIC_REF_RE = re.compile(r"^topic_[0-9a-f]{16}$")

_SECTIONS = frozenset({"observation", "reception"})
_GRAPH_ROLES = frozenset(
    {
        "none",
        "precedes_source",
        "precedes_target",
        "relation_source",
        "relation_target",
        "unknown_related",
    }
)
_SOURCE_ROLES = frozenset(
    {"original_input", "question_need_decision", "supplemental_answer"}
)
_POLARITIES = frozenset({"positive", "negative", "mixed", "neutral", "unknown"})
_MODALITIES = frozenset({"observed", "reported", "intended", "possible", "unknown"})
_TEMPORAL_SCOPES = frozenset(
    {"current_input", "reported_past", "intended_future", "atemporal", "unknown"}
)
_REFERENT_SCOPES = frozenset(
    {"self", "other", "event", "action", "state", "relation", "unknown"}
)
_UNKNOWN_SCOPES = frozenset(
    {"cause", "choice", "referent", "relation", "outcome", "other"}
)
_RELATION_TYPES = frozenset(
    {"precedes", "contrasts_with", "coexists_with", "qualifies", "supports_without_guarantee"}
)
_RELATION_DIRECTIONS = frozenset(
    {"source_to_target", "target_to_source", "bidirectional"}
)
_SURFACE_DIRECTIONS = frozenset({"left_to_right", "bidirectional"})
_RECEPTION_ACTS = frozenset(
    {
        "hold_in_attention",
        "do_not_dismiss",
        "receive_without_deciding",
        "honor_concrete_action",
        "stay_with_mixed_meaning",
    }
)
_PARSE_FAILURE_CODES = frozenset(
    {
        "EMPTY_CONTROLLED_CLAUSE",
        "EMPTY_CONTROLLED_SECTION",
        "EMPTY_CONTROLLED_SENTENCE",
        "LABEL_COUNT_INVALID",
        "LABEL_ORDER_INVALID",
        "MULTIPLE_SOURCE_ANCHORS_FORBIDDEN",
        "NON_CANONICAL_CONTROLLED_SURFACE",
        "SECTION_SEPARATOR_INVALID",
        "SOURCE_ANCHOR_CLOSE_WITHOUT_OPEN",
        "SOURCE_ANCHOR_LENGTH_INVALID",
        "SOURCE_ANCHOR_NESTED",
        "SOURCE_ANCHOR_UNCLOSED",
        "TERMINAL_CONTRACT_INVALID",
        "UNPARSABLE_CONTROLLED_SURFACE",
    }
)
_BINDING_FAILURES_BY_STATUS = {
    "no_semantic_binding": frozenset(
        {"NO_SEMANTIC_BINDING", "PARSED_WITNESS_REPLAY_MISMATCH"}
    ),
    "ambiguous_semantic_binding": frozenset(
        {"AMBIGUOUS_SEMANTIC_BINDING"}
    ),
    "source_context_mismatch": frozenset(
        {"SOURCE_CONTEXT_NOT_BODY_RECOVERABLE"}
    ),
    "unparseable_surface": frozenset({"UNPARSABLE_CONTROLLED_SURFACE"}),
}

_NONSTANCE_COMMON = {
    "atom_id",
    "kind",
    "section_role",
    "graph_role",
    "referent_fingerprint",
    "semantic_signature_sha256",
    "source_anchor_sha256",
    "source_anchor_scalar_count",
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
    "grounded_nucleus": _NONSTANCE_COMMON | {"predicate_code"},
    "grounded_relation": _NONSTANCE_COMMON
    | {"relation_type", "surface_direction", "ordered_endpoint_fingerprints"},
    "unknown_boundary": _NONSTANCE_COMMON | {"unknown_dimension_codes"},
    "significance_or_shift": _NONSTANCE_COMMON | {"predicate_code"},
    "intention_or_next_action": _NONSTANCE_COMMON | {"predicate_code"},
    "self_denial_boundary": _NONSTANCE_COMMON | {"predicate_code"},
    "bounded_counterposition": _NONSTANCE_COMMON | {"predicate_code"},
    "bound_emlis_reception": {
        "atom_id",
        "kind",
        "section_role",
        "target_atom_ids",
        "reception_act",
        "semantic_signature_sha256",
        "polarity",
        "modality",
        "temporal_scope",
        "topic_fingerprints",
        "referent_scope",
        "utf8_byte_start",
        "utf8_byte_end",
        "span_sha256",
    },
}
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
_MATCH_BASIS = {
    "grounded_nucleus": "UNIQUE_NUCLEUS_POLARITY_MATCH",
    "grounded_relation": "UNIQUE_REFERENT_RELATION_POLARITY_MATCH",
    "unknown_boundary": "UNIQUE_UNKNOWN_SCOPE_MATCH",
    "significance_or_shift": "UNIQUE_SIGNIFICANCE_MATCH",
    "intention_or_next_action": "UNIQUE_INTENTION_MODALITY_MATCH",
    "self_denial_boundary": "UNIQUE_SELF_DENIAL_BOUNDARY_MATCH",
    "bounded_counterposition": "UNIQUE_COUNTERPOSITION_MATCH",
    "bound_emlis_reception": "UNIQUE_BOUND_RECEPTION_TARGET_MATCH",
}
_PREDICATE_BY_ATOM_KIND = {
    "grounded_nucleus": "NUCLEUS_OBSERVED",
    "significance_or_shift": "SHIFT_OBSERVED",
    "intention_or_next_action": "ACTION_INTENDED",
    "self_denial_boundary": "SEPARATE_CLAIM_FROM_OBSERVATION",
    "bounded_counterposition": "BOUNDED_COUNTERPOSITION_OBSERVED",
}


def _add(issues: list[ContractIssue], code: str, path: str) -> None:
    issues.append(ContractIssue(code, path))


def _final(issues: Iterable[ContractIssue]) -> tuple[ContractIssue, ...]:
    return tuple(sorted(set(issues)))


def _parent_artifact_sha256(
    value: Any,
    path: str,
    issues: list[ContractIssue],
) -> str | None:
    """Hash an untrusted parent without leaking canonical-JSON exceptions."""

    try:
        return artifact_sha256(value)
    except (RecursionError, TypeError, ValueError):
        _add(issues, "PARENT_NON_CANONICAL", path)
        return None


def _exact_object(
    value: Any,
    keys: set[str],
    path: str,
    issues: list[ContractIssue],
) -> dict[str, Any] | None:
    if type(value) is not dict:
        _add(issues, "OBJECT_REQUIRED", path)
        return None
    actual = set(value)
    for key in actual:
        if type(key) is not str:
            _add(issues, "STRING_OBJECT_KEY_REQUIRED", path)
    for key in sorted(keys - actual):
        _add(issues, "REQUIRED_FIELD_MISSING", f"{path}.{key}")
    for key in sorted(actual - keys, key=str):
        _add(issues, "UNKNOWN_FIELD", f"{path}.{key}")
    return value


def _string(
    value: Any,
    path: str,
    issues: list[ContractIssue],
    *,
    pattern: re.Pattern[str] | None = None,
    allowed: frozenset[str] | None = None,
) -> str | None:
    if type(value) is not str or not value:
        _add(issues, "STRING_REQUIRED", path)
        return None
    if unicodedata.normalize("NFC", value) != value or "\r" in value:
        _add(issues, "NON_CANONICAL_STRING", path)
    if pattern is not None and pattern.fullmatch(value) is None:
        _add(issues, "STRING_PATTERN_MISMATCH", path)
    if allowed is not None and value not in allowed:
        _add(issues, "ENUM_VALUE_INVALID", path)
    return value


def _string_list(
    value: Any,
    path: str,
    issues: list[ContractIssue],
    *,
    minimum: int = 0,
    pattern: re.Pattern[str] | None = None,
    allowed: frozenset[str] | None = None,
    require_sorted: bool = False,
) -> list[str] | None:
    if type(value) is not list:
        _add(issues, "ARRAY_REQUIRED", path)
        return None
    result: list[str] = []
    for index, item in enumerate(value):
        parsed = _string(
            item,
            f"{path}[{index}]",
            issues,
            pattern=pattern,
            allowed=allowed,
        )
        if parsed is not None:
            result.append(parsed)
    if len(value) < minimum:
        _add(issues, "ARRAY_TOO_SHORT", path)
    if len(result) != len(set(result)):
        _add(issues, "DUPLICATE_VALUE", path)
    if require_sorted and result != sorted(result):
        _add(issues, "NON_CANONICAL_ORDER", path)
    return result


def _sha(value: Any, path: str, issues: list[ContractIssue]) -> str | None:
    return _string(value, path, issues, pattern=_SHA_RE)


def _int(
    value: Any,
    path: str,
    issues: list[ContractIssue],
    *,
    minimum: int,
    maximum: int | None = None,
) -> int | None:
    if type(value) is not int:
        _add(issues, "INTEGER_REQUIRED", path)
        return None
    if value < minimum or (maximum is not None and value > maximum):
        _add(issues, "INTEGER_OUT_OF_RANGE", path)
    return value


def _bool(value: Any, path: str, issues: list[ContractIssue]) -> bool | None:
    if type(value) is not bool:
        _add(issues, "BOOLEAN_REQUIRED", path)
        return None
    return value


def _utf8_boundaries(text: str) -> set[int]:
    result = {0}
    offset = 0
    for character in text:
        offset += len(character.encode("utf-8"))
        result.add(offset)
    return result


def validate_parsed_surface_witness_v2(
    value: Any,
    *,
    candidate_text_bytes: bytes,
) -> tuple[ContractIssue, ...]:
    """Validate the closed v2 body-derived witness and its exact byte spans."""

    issues: list[ContractIssue] = []
    keys = {
        "schema_version",
        "candidate_text_sha256",
        "grammar_catalog_sha256",
        "parser_rulebook_sha256",
        "compatible_observation_stages",
        "compatible_source_roles",
        "parse_status",
        "parse_failure_codes",
        "semantic_atoms",
        "body_free_export_allowed",
    }
    obj = _exact_object(value, keys, "$", issues)
    if obj is None:
        return _final(issues)
    _string(obj.get("schema_version"), "$.schema_version", issues)
    if obj.get("schema_version") != WITNESS_V2_SCHEMA:
        _add(issues, "SCHEMA_VERSION_MISMATCH", "$.schema_version")
    if type(candidate_text_bytes) is not bytes:
        _add(issues, "CANDIDATE_BYTES_REQUIRED", "$.candidate_text_sha256")
        candidate_text_bytes = b""
    try:
        candidate_text = candidate_text_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        candidate_text = ""
        _add(issues, "CANDIDATE_UTF8_REQUIRED", "$.candidate_text_sha256")
    expected_sha = hashlib.sha256(candidate_text_bytes).hexdigest()
    candidate_sha = _sha(
        obj.get("candidate_text_sha256"),
        "$.candidate_text_sha256",
        issues,
    )
    if candidate_sha != expected_sha:
        _add(issues, "PARENT_HASH_MISMATCH", "$.candidate_text_sha256")
    if _sha(
        obj.get("grammar_catalog_sha256"),
        "$.grammar_catalog_sha256",
        issues,
    ) != FROZEN_SURFACE_GRAMMAR_CATALOG_SHA256:
        _add(issues, "GRAMMAR_CATALOG_HASH_MISMATCH", "$.grammar_catalog_sha256")
    if _sha(
        obj.get("parser_rulebook_sha256"),
        "$.parser_rulebook_sha256",
        issues,
    ) != FROZEN_PARSER_RULEBOOK_SHA256:
        _add(issues, "PARSER_RULEBOOK_HASH_MISMATCH", "$.parser_rulebook_sha256")
    compatible_stages = _string_list(
        obj.get("compatible_observation_stages"),
        "$.compatible_observation_stages",
        issues,
        minimum=1,
        allowed=frozenset({"normal_observation"}),
        require_sorted=True,
    )
    if compatible_stages != ["normal_observation"]:
        _add(issues, "PARSER_STAGE_COMPATIBILITY_INVALID", "$.compatible_observation_stages")
    compatible_roles = _string_list(
        obj.get("compatible_source_roles"),
        "$.compatible_source_roles",
        issues,
        minimum=1,
        allowed=_SOURCE_ROLES,
        require_sorted=True,
    )
    if compatible_roles != ["original_input"]:
        _add(issues, "PARSER_SOURCE_ROLE_COMPATIBILITY_INVALID", "$.compatible_source_roles")
    status = _string(
        obj.get("parse_status"),
        "$.parse_status",
        issues,
        allowed=frozenset({"parsed", "unparseable"}),
    )
    failures = _string_list(
        obj.get("parse_failure_codes"),
        "$.parse_failure_codes",
        issues,
        allowed=_PARSE_FAILURE_CODES,
        require_sorted=True,
    )
    if _bool(
        obj.get("body_free_export_allowed"),
        "$.body_free_export_allowed",
        issues,
    ) is not False:
        _add(issues, "PRIVATE_ARTIFACT_EXPORT_FORBIDDEN", "$.body_free_export_allowed")
    atoms_value = obj.get("semantic_atoms")
    if type(atoms_value) is not list:
        _add(issues, "ARRAY_REQUIRED", "$.semantic_atoms")
        atoms_value = []
    if status == "parsed":
        if not atoms_value:
            _add(issues, "PARSED_ATOM_REQUIRED", "$.semantic_atoms")
        if failures:
            _add(issues, "PARSED_FAILURE_CODE_FORBIDDEN", "$.parse_failure_codes")
    elif status == "unparseable":
        if atoms_value:
            _add(issues, "UNPARSEABLE_ATOM_FORBIDDEN", "$.semantic_atoms")
        if failures == []:
            _add(issues, "UNPARSEABLE_FAILURE_CODE_REQUIRED", "$.parse_failure_codes")
        if failures is not None and len(failures) != 1:
            _add(
                issues,
                "PARSE_FAILURE_CARDINALITY_INVALID",
                "$.parse_failure_codes",
            )

    boundaries = _utf8_boundaries(candidate_text)
    parsed_atoms: list[dict[str, Any]] = []
    atom_ids: list[str] = []
    previous_end = -1
    for index, row in enumerate(atoms_value):
        path = f"$.semantic_atoms[{index}]"
        if type(row) is not dict:
            _add(issues, "OBJECT_REQUIRED", path)
            continue
        kind = row.get("kind")
        if kind not in _ATOM_KEYS:
            _add(issues, "ENUM_VALUE_INVALID", f"{path}.kind")
            _exact_object(row, {"atom_id", "kind"}, path, issues)
            continue
        item = _exact_object(row, _ATOM_KEYS[kind], path, issues)
        if item is None:
            continue
        parsed_atoms.append(item)
        atom_id = _string(item.get("atom_id"), f"{path}.atom_id", issues, pattern=_ATOM_ID_RE)
        if atom_id is not None:
            atom_ids.append(atom_id)
        section_role = _string(
            item.get("section_role"), f"{path}.section_role", issues, allowed=_SECTIONS
        )
        if kind == "bound_emlis_reception" and section_role != "reception":
            _add(issues, "STANCE_SECTION_MISMATCH", f"{path}.section_role")
        if kind != "bound_emlis_reception" and section_role != "observation":
            _add(issues, "OBSERVATION_SECTION_MISMATCH", f"{path}.section_role")
        if kind != "bound_emlis_reception":
            _string(
                item.get("graph_role"),
                f"{path}.graph_role",
                issues,
                allowed=_GRAPH_ROLES,
            )
        semantic_signature = _sha(
            item.get("semantic_signature_sha256"),
            f"{path}.semantic_signature_sha256",
            issues,
        )
        _string(item.get("polarity"), f"{path}.polarity", issues, allowed=_POLARITIES)
        _string(item.get("modality"), f"{path}.modality", issues, allowed=_MODALITIES)
        _string(
            item.get("temporal_scope"),
            f"{path}.temporal_scope",
            issues,
            allowed=_TEMPORAL_SCOPES,
        )
        _string(
            item.get("referent_scope"),
            f"{path}.referent_scope",
            issues,
            allowed=_REFERENT_SCOPES,
        )
        _string_list(
            item.get("topic_fingerprints"),
            f"{path}.topic_fingerprints",
            issues,
            minimum=1,
            pattern=_TOPIC_REF_RE,
            require_sorted=True,
        )
        start = _int(
            item.get("utf8_byte_start"), f"{path}.utf8_byte_start", issues, minimum=0
        )
        end = _int(
            item.get("utf8_byte_end"),
            f"{path}.utf8_byte_end",
            issues,
            minimum=1,
            maximum=len(candidate_text_bytes),
        )
        span_sha = _sha(item.get("span_sha256"), f"{path}.span_sha256", issues)
        if start is not None and end is not None:
            if start >= end:
                _add(issues, "SPAN_RANGE_INVALID", path)
            if start not in boundaries or end not in boundaries:
                _add(issues, "SPAN_NOT_UTF8_SCALAR_BOUNDARY", path)
            if start < previous_end:
                _add(issues, "SPAN_ORDER_OR_OVERLAP_INVALID", path)
            previous_end = max(previous_end, end)
            if 0 <= start < end <= len(candidate_text_bytes):
                if span_sha != hashlib.sha256(candidate_text_bytes[start:end]).hexdigest():
                    _add(issues, "SPAN_HASH_MISMATCH", f"{path}.span_sha256")
            if atom_id is not None and candidate_sha is not None:
                expected_atom_id = "atom_" + artifact_sha256(
                    {
                        "candidate_text_sha256": candidate_sha,
                        "section_role": section_role,
                        "utf8_byte_start": start,
                        "utf8_byte_end": end,
                        "kind": kind,
                    }
                )[:16]
                if atom_id != expected_atom_id:
                    _add(issues, "ATOM_ID_DERIVATION_MISMATCH", f"{path}.atom_id")

        if kind == "bound_emlis_reception":
            _string_list(
                item.get("target_atom_ids"),
                f"{path}.target_atom_ids",
                issues,
                minimum=1,
                pattern=_ATOM_ID_RE,
            )
            _string(
                item.get("reception_act"),
                f"{path}.reception_act",
                issues,
                allowed=_RECEPTION_ACTS,
            )
        else:
            _string(
                item.get("referent_fingerprint"),
                f"{path}.referent_fingerprint",
                issues,
                pattern=_SEMANTIC_REF_RE,
            )
            anchor = item.get("source_anchor_sha256")
            if anchor is not None:
                _sha(anchor, f"{path}.source_anchor_sha256", issues)
            anchor_count = _int(
                item.get("source_anchor_scalar_count"),
                f"{path}.source_anchor_scalar_count",
                issues,
                minimum=0,
                maximum=16,
            )
            if (anchor is None and anchor_count != 0) or (
                anchor is not None and (anchor_count is None or anchor_count < 2)
            ):
                _add(issues, "SOURCE_ANCHOR_CONTRACT_INVALID", f"{path}.source_anchor_sha256")
            if kind == "grounded_relation":
                _string(
                    item.get("relation_type"),
                    f"{path}.relation_type",
                    issues,
                    allowed=_RELATION_TYPES,
                )
                _string(
                    item.get("surface_direction"),
                    f"{path}.surface_direction",
                    issues,
                    allowed=_SURFACE_DIRECTIONS,
                )
                endpoints = _string_list(
                    item.get("ordered_endpoint_fingerprints"),
                    f"{path}.ordered_endpoint_fingerprints",
                    issues,
                    minimum=2,
                    pattern=_SEMANTIC_REF_RE,
                )
                if endpoints is not None and len(endpoints) != 2:
                    _add(
                        issues,
                        "RELATION_ENDPOINT_COUNT_INVALID",
                        f"{path}.ordered_endpoint_fingerprints",
                    )
            elif kind == "unknown_boundary":
                _string_list(
                    item.get("unknown_dimension_codes"),
                    f"{path}.unknown_dimension_codes",
                    issues,
                    minimum=1,
                    allowed=_UNKNOWN_SCOPES,
                    require_sorted=True,
                )
            else:
                predicate_code = _string(
                    item.get("predicate_code"),
                    f"{path}.predicate_code",
                    issues,
                    pattern=_MACHINE_CODE_RE,
                )
                if predicate_code != _PREDICATE_BY_ATOM_KIND.get(kind):
                    _add(
                        issues,
                        "PREDICATE_CODE_MISMATCH",
                        f"{path}.predicate_code",
                    )
        signature_fields = {
            key: child
            for key, child in item.items()
            if key
            not in {
                "atom_id",
                "semantic_signature_sha256",
                "utf8_byte_start",
                "utf8_byte_end",
                "span_sha256",
            }
        }
        if (
            semantic_signature is not None
            and semantic_signature != artifact_sha256(signature_fields)
        ):
            _add(
                issues,
                "SEMANTIC_SIGNATURE_MISMATCH",
                f"{path}.semantic_signature_sha256",
            )

    if len(atom_ids) != len(set(atom_ids)):
        _add(issues, "DUPLICATE_ID", "$.semantic_atoms")
    atom_by_id = {
        row.get("atom_id"): row
        for row in parsed_atoms
        if type(row.get("atom_id")) is str
    }
    for index, row in enumerate(parsed_atoms):
        if row.get("kind") != "bound_emlis_reception":
            continue
        path = f"$.semantic_atoms[{index}].target_atom_ids"
        for target in row.get("target_atom_ids", []):
            target_row = atom_by_id.get(target)
            if target_row is None:
                _add(issues, "UNRESOLVED_ATOM_REFERENCE", path)
            elif target_row.get("kind") == "bound_emlis_reception":
                _add(issues, "RECEPTION_TARGET_MUST_BE_NONSTANCE", path)
            elif target_row.get("utf8_byte_end", 0) > row.get("utf8_byte_start", -1):
                _add(issues, "RECEPTION_TARGET_MUST_PRECEDE_STANCE", path)
    return _final(issues)


def validate_verified_surface_binding_v2(
    value: Any,
    *,
    parsed_surface_witness: Any,
    candidate_text_bytes: bytes,
    obligation_ledger: Any,
    ledger_authority: LedgerSourceAuthority,
    source_snapshot_sha256: str,
    observation_stage: str,
) -> tuple[ContractIssue, ...]:
    """Validate a v2 binding without performing semantic candidate search."""

    issues: list[ContractIssue] = list(
        validate_parsed_surface_witness_v2(
            parsed_surface_witness,
            candidate_text_bytes=candidate_text_bytes,
        )
    )
    witness_parent = (
        parsed_surface_witness
        if type(parsed_surface_witness) is dict
        else {}
    )
    ledger_parent = obligation_ledger if type(obligation_ledger) is dict else {}
    if type(ledger_authority) is not LedgerSourceAuthority:
        _add(issues, "LEDGER_AUTHORITY_REQUIRED", "$.source_obligation_ledger_sha256")
    else:
        try:
            issues.extend(
                validate_semantic_obligation_ledger(
                    obligation_ledger,
                    authority=ledger_authority,
                )
            )
        except (RecursionError, TypeError, ValueError):
            _add(
                issues,
                "PARENT_NON_CANONICAL",
                "$.source_obligation_ledger_sha256",
            )
    if witness_parent.get("schema_version") != WITNESS_V2_SCHEMA:
        _add(issues, "PARENT_SCHEMA_MISMATCH", "$.parsed_surface_witness_sha256")
    if ledger_parent.get("schema_version") != LEDGER_SCHEMA:
        _add(issues, "PARENT_SCHEMA_MISMATCH", "$.source_obligation_ledger_sha256")
    keys = {
        "schema_version",
        "parsed_surface_witness_sha256",
        "source_obligation_ledger_sha256",
        "source_snapshot_sha256",
        "matcher_rulebook_sha256",
        "observation_stage",
        "bindings",
        "binding_status",
        "failure_codes",
        "body_free_export_allowed",
    }
    obj = _exact_object(value, keys, "$", issues)
    if obj is None:
        return _final(issues)
    if obj.get("schema_version") != BINDING_V2_SCHEMA:
        _add(issues, "SCHEMA_VERSION_MISMATCH", "$.schema_version")
    else:
        _string(obj.get("schema_version"), "$.schema_version", issues)
    witness_parent_sha = _parent_artifact_sha256(
        parsed_surface_witness,
        "$.parsed_surface_witness_sha256",
        issues,
    )
    if witness_parent_sha is not None and _sha(
        obj.get("parsed_surface_witness_sha256"),
        "$.parsed_surface_witness_sha256",
        issues,
    ) != witness_parent_sha:
        _add(issues, "PARENT_HASH_MISMATCH", "$.parsed_surface_witness_sha256")
    ledger_parent_sha = _parent_artifact_sha256(
        obligation_ledger,
        "$.source_obligation_ledger_sha256",
        issues,
    )
    if ledger_parent_sha is not None and _sha(
        obj.get("source_obligation_ledger_sha256"),
        "$.source_obligation_ledger_sha256",
        issues,
    ) != ledger_parent_sha:
        _add(issues, "PARENT_HASH_MISMATCH", "$.source_obligation_ledger_sha256")
    if _sha(
        obj.get("source_snapshot_sha256"),
        "$.source_snapshot_sha256",
        issues,
    ) != source_snapshot_sha256:
        _add(issues, "PARENT_HASH_MISMATCH", "$.source_snapshot_sha256")
    if _sha(
        obj.get("matcher_rulebook_sha256"),
        "$.matcher_rulebook_sha256",
        issues,
    ) != FROZEN_MATCHER_RULEBOOK_SHA256:
        _add(issues, "MATCHER_RULEBOOK_HASH_MISMATCH", "$.matcher_rulebook_sha256")
    if obj.get("observation_stage") != observation_stage:
        _add(issues, "OBSERVATION_STAGE_MISMATCH", "$.observation_stage")
    _string(
        obj.get("observation_stage"),
        "$.observation_stage",
        issues,
        allowed=frozenset(
            {"normal_observation", "pre_question_observation", "refined_observation"}
        ),
    )
    status = _string(
        obj.get("binding_status"),
        "$.binding_status",
        issues,
        allowed=frozenset(
            {
                "matched",
                "no_semantic_binding",
                "ambiguous_semantic_binding",
                "source_context_mismatch",
                "unparseable_surface",
            }
        ),
    )
    failures = _string_list(
        obj.get("failure_codes"),
        "$.failure_codes",
        issues,
        allowed=frozenset().union(*_BINDING_FAILURES_BY_STATUS.values()),
        require_sorted=True,
    )
    if _bool(
        obj.get("body_free_export_allowed"),
        "$.body_free_export_allowed",
        issues,
    ) is not False:
        _add(issues, "PRIVATE_ARTIFACT_EXPORT_FORBIDDEN", "$.body_free_export_allowed")
    rows_value = obj.get("bindings")
    if type(rows_value) is not list:
        _add(issues, "ARRAY_REQUIRED", "$.bindings")
        rows_value = []
    if status == "matched":
        if not rows_value:
            _add(issues, "MATCHED_BINDING_REQUIRED", "$.bindings")
        if failures:
            _add(issues, "MATCHED_FAILURE_CODE_FORBIDDEN", "$.failure_codes")
    elif status is not None:
        if rows_value:
            _add(issues, "FAILED_BINDING_MUST_BE_EMPTY", "$.bindings")
        if failures == []:
            _add(issues, "FAILED_BINDING_CODE_REQUIRED", "$.failure_codes")
        expected_failures = _BINDING_FAILURES_BY_STATUS.get(status)
        if (
            expected_failures is not None
            and failures is not None
            and (len(failures) != 1 or failures[0] not in expected_failures)
        ):
            _add(
                issues,
                "BINDING_FAILURE_STATUS_MISMATCH",
                "$.failure_codes",
            )

    witness_status = witness_parent.get("parse_status")
    if (
        status == "unparseable_surface"
        and witness_status != "unparseable"
    ) or (
        status not in {None, "unparseable_surface"}
        and witness_status != "parsed"
    ):
        _add(issues, "BINDING_WITNESS_STATUS_MISMATCH", "$.binding_status")

    compatible_stages = witness_parent.get("compatible_observation_stages", [])
    stage_is_compatible = (
        type(compatible_stages) is list
        and observation_stage in compatible_stages
    )
    if stage_is_compatible and status == "source_context_mismatch":
        _add(issues, "BINDING_STAGE_STATUS_MISMATCH", "$.binding_status")
    elif not stage_is_compatible and status not in {
        None,
        "source_context_mismatch",
        "unparseable_surface",
    }:
        _add(issues, "BINDING_STAGE_STATUS_MISMATCH", "$.binding_status")

    witness_atoms = {
        row.get("atom_id"): row
        for row in witness_parent.get("semantic_atoms", [])
        if type(row) is dict and type(row.get("atom_id")) is str
    }
    obligations = {
        row.get("obligation_id"): row
        for row in ledger_parent.get("obligations", [])
        if type(row) is dict and type(row.get("obligation_id")) is str
    }
    parsed_rows: list[dict[str, Any]] = []
    atom_ids: list[str] = []
    obligation_ids: list[str] = []
    binding_keys = {
        "atom_id",
        "obligation_id",
        "evidence_ids",
        "nucleus_ids",
        "relation_id",
        "relation_direction",
        "unknown_boundary_ids",
        "target_obligation_ids",
        "topic_scope_ids",
        "source_roles",
        "match_basis",
        "match_candidate_count",
    }
    for index, row in enumerate(rows_value):
        path = f"$.bindings[{index}]"
        item = _exact_object(row, binding_keys, path, issues)
        if item is None:
            continue
        parsed_rows.append(item)
        atom_id = _string(item.get("atom_id"), f"{path}.atom_id", issues, pattern=_ATOM_ID_RE)
        obligation_id = _string(
            item.get("obligation_id"),
            f"{path}.obligation_id",
            issues,
            pattern=_OBLIGATION_ID_RE,
        )
        if atom_id is not None:
            atom_ids.append(atom_id)
        if obligation_id is not None:
            obligation_ids.append(obligation_id)
        evidence = _string_list(
            item.get("evidence_ids"),
            f"{path}.evidence_ids",
            issues,
            minimum=1,
            pattern=_MACHINE_ID_RE,
        )
        nuclei = _string_list(
            item.get("nucleus_ids"), f"{path}.nucleus_ids", issues, pattern=_MACHINE_ID_RE
        )
        unknowns = _string_list(
            item.get("unknown_boundary_ids"),
            f"{path}.unknown_boundary_ids",
            issues,
            pattern=_MACHINE_ID_RE,
        )
        targets = _string_list(
            item.get("target_obligation_ids"),
            f"{path}.target_obligation_ids",
            issues,
            pattern=_OBLIGATION_ID_RE,
        )
        topics = _string_list(
            item.get("topic_scope_ids"),
            f"{path}.topic_scope_ids",
            issues,
            minimum=1,
            pattern=_MACHINE_ID_RE,
        )
        source_roles = _string_list(
            item.get("source_roles"),
            f"{path}.source_roles",
            issues,
            minimum=1,
            allowed=_SOURCE_ROLES,
            require_sorted=True,
        )
        relation_id = item.get("relation_id")
        if relation_id is not None:
            _string(relation_id, f"{path}.relation_id", issues, pattern=_MACHINE_ID_RE)
        relation_direction = item.get("relation_direction")
        if relation_direction is not None:
            _string(
                relation_direction,
                f"{path}.relation_direction",
                issues,
                allowed=_RELATION_DIRECTIONS,
            )
        count = _int(
            item.get("match_candidate_count"),
            f"{path}.match_candidate_count",
            issues,
            minimum=1,
            maximum=1,
        )
        if count != 1:
            _add(issues, "UNIQUE_MATCH_REQUIRED", f"{path}.match_candidate_count")

        atom = witness_atoms.get(atom_id)
        obligation = obligations.get(obligation_id)
        if atom is None:
            _add(issues, "UNRESOLVED_ATOM_REFERENCE", f"{path}.atom_id")
        if obligation is None:
            _add(issues, "UNRESOLVED_OBLIGATION_REFERENCE", f"{path}.obligation_id")
        if atom is None or obligation is None:
            continue
        if _ATOM_TO_OBLIGATION_KIND.get(atom.get("kind")) != obligation.get("kind"):
            _add(issues, "ATOM_OBLIGATION_KIND_MISMATCH", path)
        for field in ("polarity", "modality", "temporal_scope", "referent_scope"):
            if atom.get(field) != obligation.get(field):
                _add(issues, "ATOM_OBLIGATION_FEATURE_MISMATCH", f"{path}.{field}")
        expected_roles = sorted(
            {
                ref.get("source_role")
                for ref in obligation.get("source_refs", [])
                if type(ref) is dict and type(ref.get("source_role")) is str
            }
        )
        if source_roles != expected_roles:
            _add(issues, "SOURCE_ROLE_BINDING_MISMATCH", f"{path}.source_roles")
        compatible_roles = parsed_surface_witness.get("compatible_source_roles", [])
        if source_roles is not None and not set(source_roles) <= set(compatible_roles):
            _add(issues, "SOURCE_ROLE_NOT_BODY_COMPATIBLE", f"{path}.source_roles")
        exact_fields = (
            (evidence, obligation.get("evidence_ids", []), "evidence_ids"),
            (nuclei, obligation.get("nucleus_ids", []), "nucleus_ids"),
            (unknowns, obligation.get("unknown_boundary_ids", []), "unknown_boundary_ids"),
            (targets, obligation.get("target_obligation_ids", []), "target_obligation_ids"),
            (topics, obligation.get("topic_scope_ids", []), "topic_scope_ids"),
        )
        for actual, expected, field in exact_fields:
            if actual != expected:
                _add(issues, "SOURCE_BINDING_MISMATCH", f"{path}.{field}")
        expected_basis = _MATCH_BASIS.get(atom.get("kind"))
        if item.get("match_basis") != expected_basis:
            _add(issues, "MATCH_BASIS_MISMATCH", f"{path}.match_basis")
        if atom.get("kind") == "grounded_relation":
            relation_ids = obligation.get("relation_ids", [])
            if len(relation_ids) != 1 or relation_id != relation_ids[0]:
                _add(issues, "RELATION_BINDING_MISMATCH", f"{path}.relation_id")
            descriptor = next(
                (
                    value
                    for value in obligation.get("relation_directions", [])
                    if type(value) is dict and value.get("relation_id") == relation_id
                ),
                None,
            )
            if (
                descriptor is None
                or atom.get("relation_type") != descriptor.get("relation_type")
                or relation_direction != descriptor.get("direction")
            ):
                _add(issues, "RELATION_DESCRIPTOR_MISMATCH", path)
        elif relation_id is not None or relation_direction is not None:
            _add(issues, "RELATION_BINDING_FORBIDDEN", f"{path}.relation_id")
        if atom.get("kind") == "bound_emlis_reception":
            if atom.get("reception_act") not in obligation.get("allowed_response_acts", []):
                _add(issues, "RECEPTION_ACT_MISMATCH", f"{path}.match_basis")

    if len(atom_ids) != len(set(atom_ids)):
        _add(issues, "DUPLICATE_ID", "$.bindings")
    if len(obligation_ids) != len(set(obligation_ids)):
        _add(issues, "DUPLICATE_OBLIGATION_BINDING", "$.bindings")
    if status == "matched" and set(atom_ids) != set(witness_atoms):
        _add(issues, "WITNESS_BINDING_COVERAGE_MISMATCH", "$.bindings")
    required = set(ledger_parent.get("required_obligation_ids", []))
    if status == "matched" and not required <= set(obligation_ids):
        _add(issues, "REQUIRED_BINDING_COVERAGE_MISSING", "$.bindings")
    binding_by_atom = {row.get("atom_id"): row for row in parsed_rows}
    for index, row in enumerate(parsed_rows):
        atom = witness_atoms.get(row.get("atom_id"), {})
        if atom.get("kind") != "bound_emlis_reception":
            continue
        resolved_targets = [
            binding_by_atom.get(target, {}).get("obligation_id")
            for target in atom.get("target_atom_ids", [])
        ]
        if resolved_targets != row.get("target_obligation_ids"):
            _add(
                issues,
                "STANCE_ATOM_TARGET_BINDING_MISMATCH",
                f"$.bindings[{index}].target_obligation_ids",
            )
    return _final(issues)


def _fail_closed_validator(function: Any) -> Any:
    """Convert adversarial non-JSON shapes into deterministic contract RED."""

    @wraps(function)
    def guarded(*args: Any, **kwargs: Any) -> tuple[ContractIssue, ...]:
        try:
            return function(*args, **kwargs)
        except (
            AttributeError,
            KeyError,
            TypeError,
            ValueError,
            UnicodeError,
            RecursionError,
        ):
            return (ContractIssue("MALFORMED_ARTIFACT", "$"),)

    return guarded


validate_parsed_surface_witness_v2 = _fail_closed_validator(
    validate_parsed_surface_witness_v2
)
validate_verified_surface_binding_v2 = _fail_closed_validator(
    validate_verified_surface_binding_v2
)


__all__ = [
    "BINDING_V2_SCHEMA",
    "FROZEN_MATCHER_RULEBOOK_SHA256",
    "FROZEN_PARSER_RULEBOOK_SHA256",
    "WITNESS_V2_SCHEMA",
    "validate_parsed_surface_witness_v2",
    "validate_verified_surface_binding_v2",
]
