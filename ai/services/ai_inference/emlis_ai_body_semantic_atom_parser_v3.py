# -*- coding: utf-8 -*-
from __future__ import annotations

"""Body-only inverse parser for the controlled NLS v3 surface grammar.

The public entry point accepts final UTF-8 bytes only.  It never receives a
Surface AST, discourse/content plan, obligation ledger, case id, expected text,
generator span map, coverage declaration, or renderer helper.  The sole shared
language authority is the frozen declarative grammar catalog.
"""

from dataclasses import dataclass
import hashlib
import unicodedata
from typing import Any, Iterable

from emlis_ai_nls_v3_artifact_contract import artifact_sha256
from emlis_ai_step8_artifact_contract_v3 import (
    FROZEN_PARSER_RULEBOOK_SHA256,
    WITNESS_V2_SCHEMA,
    validate_parsed_surface_witness_v2,
)
from emlis_ai_surface_grammar_catalog_v3_step8 import (
    FROZEN_STEP8_SURFACE_GRAMMAR_CATALOG_SHA256 as FROZEN_SURFACE_GRAMMAR_CATALOG_SHA256,
    STEP8_SURFACE_GRAMMAR_CATALOG as SURFACE_GRAMMAR_CATALOG,
    validate_step8_surface_grammar_catalog as validate_surface_grammar_catalog,
)


_PARSER_RULEBOOK = {
    "version": "cocolon.emlis.nls_v3.body_atom_parser.20260715.v1",
    "grammar_catalog_sha256": FROZEN_SURFACE_GRAMMAR_CATALOG_SHA256,
    "document": "two_labeled_sections_exact_lf_nfc",
    "clause_split": "catalog_joiner_outside_opaque_source_anchor",
    "referent_components": [
        "source_anchor_optional",
        "graph_role_optional",
        "source_field",
        "source_role",
        "temporal_scope",
        "semantic_role_optional",
        "polarity",
        "semantic_qualifier_optional",
        "nucleus_kind",
    ],
    "ambiguous_seen_predicate": "change_or_value_means_significance_else_nucleus",
    "stance_antecedent": "final_compatible_observation_atom",
    "span": "clause_utf8_half_open_without_joiner_or_terminal",
    "source_ids": "forbidden",
    "body_free_export_allowed": False,
}
PARSER_RULEBOOK_SHA256 = artifact_sha256(_PARSER_RULEBOOK)

_GRAPH_ROLE_TOKENS = tuple(
    sorted(
        (
            (value, key)
            for key, value in SURFACE_GRAMMAR_CATALOG["graph_role"].items()
            if value
        ),
        key=lambda row: (-len(row[0]), row[1]),
    )
)
_QUALIFIER_TOKENS = tuple(
    sorted(
        (
            (value, f"{group}:{key}")
            for group in (
                "source_semantic_role",
                "source_operator",
                "meaning_block_kind",
            )
            for key, value in SURFACE_GRAMMAR_CATALOG[group].items()
            if value
        ),
        key=lambda row: (-len(row[0]), row[1]),
    )
)


class BodySemanticAtomParseError(ValueError):
    """Fail-closed parser/configuration error with a body-free machine code."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class _ParseFailure(Exception):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class _NucleusLexeme:
    source_field: str
    source_role: str
    temporal_scope: str
    semantic_role: str
    polarity: str
    semantic_qualifier: str
    nucleus_kind: str
    fingerprint: str


@dataclass(frozen=True, slots=True)
class _ReferentLexeme:
    nuclei: tuple[_NucleusLexeme, ...]
    anchor_sha256: str | None
    anchor_scalar_count: int
    graph_role: str
    end: int


def _dependencies_valid() -> bool:
    return bool(
        not validate_surface_grammar_catalog()
        and not validate_surface_grammar_catalog(SURFACE_GRAMMAR_CATALOG)
        and artifact_sha256(_PARSER_RULEBOOK) == FROZEN_PARSER_RULEBOOK_SHA256
        and PARSER_RULEBOOK_SHA256 == FROZEN_PARSER_RULEBOOK_SHA256
        and _PARSER_RULEBOOK.get("grammar_catalog_sha256")
        == FROZEN_SURFACE_GRAMMAR_CATALOG_SHA256
    )


def _inverse_group(group: str) -> tuple[tuple[str, str], ...]:
    value = SURFACE_GRAMMAR_CATALOG.get(group)
    if type(value) is not dict:
        raise BodySemanticAtomParseError("PARSER_CATALOG_GROUP_INVALID")
    rows = [(token, key) for key, token in value.items() if type(token) is str and token]
    return tuple(sorted(rows, key=lambda row: (-len(row[0]), row[1])))


def _consume_required_group(text: str, start: int, group: str) -> tuple[str, int]:
    for token, key in _inverse_group(group):
        if text.startswith(token, start):
            return key, start + len(token)
    raise _ParseFailure("UNPARSABLE_CONTROLLED_SURFACE")


def _consume_optional_group(
    text: str,
    start: int,
    group: str,
    *,
    empty_key: str,
) -> tuple[str, int]:
    for token, key in _inverse_group(group):
        if text.startswith(token, start):
            return key, start + len(token)
    value = SURFACE_GRAMMAR_CATALOG.get(group, {}).get(empty_key)
    if value != "":
        raise BodySemanticAtomParseError("PARSER_CATALOG_EMPTY_DEFAULT_INVALID")
    return empty_key, start


def _nucleus_fingerprint(features: dict[str, str]) -> str:
    return "semantic_ref_" + artifact_sha256(
        {"nucleus_surface_semantics": features}
    )[:16]


def _parse_nucleus(text: str, start: int) -> tuple[_NucleusLexeme, int]:
    source_field, offset = _consume_required_group(text, start, "source_field")
    source_role, offset = _consume_optional_group(
        text, offset, "source_role", empty_key="original_input"
    )
    temporal_scope, offset = _consume_required_group(text, offset, "temporal_scope")
    semantic_role, offset = _consume_optional_group(
        text, offset, "semantic_role", empty_key="none"
    )
    polarity, offset = _consume_required_group(text, offset, "polarity")
    qualifier = "none"
    for token, code in _QUALIFIER_TOKENS:
        if text.startswith(token, offset):
            qualifier = code
            offset += len(token)
            break
    nucleus_kind, offset = _consume_required_group(text, offset, "nucleus_kind")
    features = {
        "source_field": source_field,
        "source_role": source_role,
        "temporal_scope": temporal_scope,
        "semantic_role": semantic_role,
        "polarity": polarity,
        "semantic_qualifier": qualifier,
        "nucleus_kind": nucleus_kind,
    }
    return (
        _NucleusLexeme(
            source_field=source_field,
            source_role=source_role,
            temporal_scope=temporal_scope,
            semantic_role=semantic_role,
            polarity=polarity,
            semantic_qualifier=qualifier,
            nucleus_kind=nucleus_kind,
            fingerprint=_nucleus_fingerprint(features),
        ),
        offset,
    )


def _parse_anchor(text: str, start: int) -> tuple[str | None, int, int]:
    anchor = SURFACE_GRAMMAR_CATALOG["source_anchor"]
    opening = anchor["open"]
    closing = anchor["close"] + anchor["binding"]
    if not text.startswith(opening, start):
        return None, 0, start
    close_at = text.find(closing, start + len(opening))
    if close_at < 0:
        raise _ParseFailure("SOURCE_ANCHOR_UNCLOSED")
    raw = text[start + len(opening) : close_at]
    if not 2 <= len(raw) <= 16:
        raise _ParseFailure("SOURCE_ANCHOR_LENGTH_INVALID")
    return (
        hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        len(raw),
        close_at + len(closing),
    )


def _parse_referent(text: str, start: int) -> _ReferentLexeme:
    anchor_sha, anchor_count, offset = _parse_anchor(text, start)
    graph_role = "none"
    for token, key in _GRAPH_ROLE_TOKENS:
        if text.startswith(token, offset):
            graph_role = key
            offset += len(token)
            break
    first, offset = _parse_nucleus(text, offset)
    nuclei = [first]
    joiner = SURFACE_GRAMMAR_CATALOG["morphology"]["referent_joiner"]
    while text.startswith(joiner, offset):
        try:
            item, candidate_end = _parse_nucleus(text, offset + len(joiner))
        except _ParseFailure:
            break
        nuclei.append(item)
        offset = candidate_end
    return _ReferentLexeme(
        nuclei=tuple(nuclei),
        anchor_sha256=anchor_sha,
        anchor_scalar_count=anchor_count,
        graph_role=graph_role,
        end=offset,
    )


def _referent_fingerprint(referent: _ReferentLexeme) -> str:
    return "semantic_ref_" + artifact_sha256(
        {
            "ordered_endpoint_fingerprints": [
                row.fingerprint for row in referent.nuclei
            ],
            "source_anchor_sha256": referent.anchor_sha256,
        }
    )[:16]


def _topic_fingerprints(nuclei: Iterable[_NucleusLexeme]) -> list[str]:
    return sorted(
        {
            "topic_"
            + artifact_sha256(
                {"surface_referent_fingerprint": row.fingerprint}
            )[:16]
            for row in nuclei
        }
    )


def _referent_scope(kind: str) -> str:
    if kind == "action":
        return "action"
    if kind in {"event", "change"}:
        return "event"
    return "state"


def _combined(values: Iterable[str], default: str) -> str:
    unique = tuple(dict.fromkeys(value for value in values if value))
    return unique[0] if len(unique) == 1 else default


def _semantic_signature(atom: dict[str, Any]) -> str:
    excluded = {
        "atom_id",
        "semantic_signature_sha256",
        "utf8_byte_start",
        "utf8_byte_end",
        "span_sha256",
    }
    return artifact_sha256(
        {key: value for key, value in atom.items() if key not in excluded}
    )


def _atom_id(
    *,
    candidate_sha256: str,
    section_role: str,
    start: int,
    end: int,
    kind: str,
) -> str:
    return "atom_" + artifact_sha256(
        {
            "candidate_text_sha256": candidate_sha256,
            "section_role": section_role,
            "utf8_byte_start": start,
            "utf8_byte_end": end,
            "kind": kind,
        }
    )[:16]


def _prefix(text: str) -> tuple[int, str]:
    offset = 0
    connector_tokens = [
        token
        for token in SURFACE_GRAMMAR_CATALOG["connector"].values()
        if token
    ]
    connector_tokens.sort(key=lambda token: -len(token))
    while True:
        matched = next(
            (token for token in connector_tokens if text.startswith(token, offset)),
            None,
        )
        if matched is None:
            break
        offset += len(matched)
    modality, offset = _consume_optional_group(
        text, offset, "modality", empty_key="observed"
    )
    return offset, modality


def _unknown_dimensions(text: str, start: int) -> tuple[list[str], int]:
    accepted = set(
        SURFACE_GRAMMAR_CATALOG["inverse_kind_rule"][
            "accepted_unknown_dimension_codes"
        ]
    )
    inverse = tuple(
        (token, key)
        for token, key in _inverse_group("unknown_dimension")
        if key in accepted
    )
    first: tuple[str, int] | None = None
    for token, key in inverse:
        if text.startswith(token, start):
            first = (key, start + len(token))
            break
    if first is None:
        raise _ParseFailure("UNPARSABLE_CONTROLLED_SURFACE")
    dimensions = [first[0]]
    offset = first[1]
    joiner = SURFACE_GRAMMAR_CATALOG["unknown_dimension_joiner"]
    while text.startswith(joiner, offset):
        candidate = offset + len(joiner)
        matched = next(
            (
                (key, candidate + len(token))
                for token, key in inverse
                if text.startswith(token, candidate)
            ),
            None,
        )
        if matched is None:
            break
        dimensions.append(matched[0])
        offset = matched[1]
    return sorted(set(dimensions)), offset


def _base_nonstance(
    *,
    kind: str,
    referent: _ReferentLexeme,
    modality: str,
    polarity: str,
    temporal_scope: str,
    referent_scope: str,
) -> dict[str, Any]:
    return {
        "kind": kind,
        "section_role": "observation",
        "graph_role": referent.graph_role,
        "referent_fingerprint": _referent_fingerprint(referent),
        "semantic_signature_sha256": "0" * 64,
        "source_anchor_sha256": referent.anchor_sha256,
        "source_anchor_scalar_count": referent.anchor_scalar_count,
        "polarity": polarity,
        "modality": modality,
        "temporal_scope": temporal_scope,
        "topic_fingerprints": _topic_fingerprints(referent.nuclei),
        "referent_scope": referent_scope,
    }


def _try_unknown(text: str, start: int, modality: str) -> dict[str, Any] | None:
    try:
        dimensions, offset = _unknown_dimensions(text, start)
        binding = SURFACE_GRAMMAR_CATALOG["morphology"]["unknown_binding"]
        if not text.startswith(binding, offset):
            return None
        referent = _parse_referent(text, offset + len(binding))
        form = next(
            (
                key
                for token, key in _inverse_group("unknown")
                if text.startswith(token, referent.end)
                and referent.end + len(token) == len(text)
            ),
            None,
        )
        if form is None:
            return None
        atom = _base_nonstance(
            kind="unknown_boundary",
            referent=referent,
            modality=modality,
            polarity="unknown",
            temporal_scope="unknown",
            referent_scope="unknown",
        )
        atom["unknown_dimension_codes"] = dimensions
        atom["semantic_signature_sha256"] = _semantic_signature(atom)
        return atom
    except _ParseFailure:
        return None


def _relation_referent(
    first: _NucleusLexeme,
    second: _NucleusLexeme,
    *,
    anchor_sha256: str | None,
    anchor_scalar_count: int,
) -> _ReferentLexeme:
    return _ReferentLexeme(
        nuclei=(first, second),
        anchor_sha256=anchor_sha256,
        anchor_scalar_count=anchor_scalar_count,
        graph_role="none",
        end=0,
    )


def _try_relation(text: str, start: int, modality: str) -> dict[str, Any] | None:
    offset = start
    try:
        anchor_sha, anchor_count, offset = _parse_anchor(text, offset)
        first, first_end = _parse_nucleus(text, offset)
    except _ParseFailure:
        return None
    joiner = SURFACE_GRAMMAR_CATALOG["morphology"]["referent_joiner"]
    bidirectional_binding = SURFACE_GRAMMAR_CATALOG["morphology"][
        "bidirectional_binding"
    ]
    if text.startswith(joiner, first_end):
        try:
            second, second_end = _parse_nucleus(text, first_end + len(joiner))
        except _ParseFailure:
            second = None
            second_end = -1
        if second is not None and text.startswith(bidirectional_binding, second_end):
            relation_at = second_end + len(bidirectional_binding)
            relation_type = next(
                (
                    key
                    for token, key in _inverse_group("relation")
                    if text.startswith(token, relation_at)
                    and relation_at + len(token) == len(text)
                ),
                None,
            )
            if relation_type is not None:
                referent = _relation_referent(
                    first,
                    second,
                    anchor_sha256=anchor_sha,
                    anchor_scalar_count=anchor_count,
                )
                atom = _base_nonstance(
                    kind="grounded_relation",
                    referent=referent,
                    modality=modality,
                    polarity=_combined((first.polarity, second.polarity), "mixed"),
                    temporal_scope=_combined(
                        (first.temporal_scope, second.temporal_scope), "unknown"
                    ),
                    referent_scope="relation",
                )
                atom.update(
                    {
                        "relation_type": relation_type,
                        "surface_direction": "bidirectional",
                        "ordered_endpoint_fingerprints": [
                            first.fingerprint,
                            second.fingerprint,
                        ],
                    }
                )
                atom["semantic_signature_sha256"] = _semantic_signature(atom)
                return atom

    for relation_type, joiner_value in sorted(
        SURFACE_GRAMMAR_CATALOG["directed_relation_joiner"].items()
    ):
        left = joiner_value["left"]
        right = joiner_value["right"]
        if not text.startswith(left, first_end):
            continue
        try:
            second, second_end = _parse_nucleus(text, first_end + len(left))
        except _ParseFailure:
            continue
        if not text.startswith(right, second_end) or second_end + len(right) != len(text):
            continue
        referent = _relation_referent(
            first,
            second,
            anchor_sha256=anchor_sha,
            anchor_scalar_count=anchor_count,
        )
        polarity = _combined((first.polarity, second.polarity), "mixed")
        if (
            relation_type in {"contrasts_with", "coexists_with"}
            and first.polarity != second.polarity
        ):
            polarity = "mixed"
        atom = _base_nonstance(
            kind="grounded_relation",
            referent=referent,
            modality=modality,
            polarity=polarity,
            temporal_scope=_combined(
                (first.temporal_scope, second.temporal_scope), "unknown"
            ),
            referent_scope="relation",
        )
        atom.update(
            {
                "relation_type": relation_type,
                "surface_direction": "left_to_right",
                "ordered_endpoint_fingerprints": [first.fingerprint, second.fingerprint],
            }
        )
        atom["semantic_signature_sha256"] = _semantic_signature(atom)
        return atom
    return None


def _try_predicate_or_boundary(
    text: str,
    start: int,
    modality: str,
) -> dict[str, Any] | None:
    try:
        referent = _parse_referent(text, start)
    except _ParseFailure:
        return None
    suffix = text[referent.end :]
    boundary = SURFACE_GRAMMAR_CATALOG["self_denial"]
    for form, token in boundary.items():
        if suffix == token:
            atom = _base_nonstance(
                kind="self_denial_boundary",
                referent=referent,
                modality=modality,
                polarity=referent.nuclei[0].polarity,
                temporal_scope=referent.nuclei[0].temporal_scope,
                referent_scope=_referent_scope(referent.nuclei[0].nucleus_kind),
            )
            atom["predicate_code"] = form.upper()
            atom["semantic_signature_sha256"] = _semantic_signature(atom)
            return atom
    accepted_forms = set(
        SURFACE_GRAMMAR_CATALOG["inverse_kind_rule"][
            "accepted_predicate_forms"
        ]
    )
    predicate_matches = [
        (form, token)
        for form, token in SURFACE_GRAMMAR_CATALOG["predicate"].items()
        if form in accepted_forms and suffix == token
    ]
    if not predicate_matches:
        return None
    forms = {form for form, _token in predicate_matches}
    nucleus_kind = referent.nuclei[0].nucleus_kind
    special = set(
        SURFACE_GRAMMAR_CATALOG["inverse_kind_rule"][
            "shared_seen_predicate_special_nucleus_kinds"
        ]
    )
    if "action_intended" in forms:
        kind = "intention_or_next_action"
        predicate_code = "ACTION_INTENDED"
    elif "bounded_counterposition_observed" in forms:
        kind = "bounded_counterposition"
        predicate_code = "BOUNDED_COUNTERPOSITION_OBSERVED"
    elif nucleus_kind in special:
        kind = "significance_or_shift"
        predicate_code = "SHIFT_OBSERVED"
    else:
        kind = "grounded_nucleus"
        predicate_code = "NUCLEUS_OBSERVED"
    atom = _base_nonstance(
        kind=kind,
        referent=referent,
        modality=modality,
        polarity=referent.nuclei[0].polarity,
        temporal_scope=referent.nuclei[0].temporal_scope,
        referent_scope=_referent_scope(nucleus_kind),
    )
    atom["predicate_code"] = predicate_code
    atom["semantic_signature_sha256"] = _semantic_signature(atom)
    return atom


_ANTECEDENT_KIND = {
    "grounded_nucleus_notice": "grounded_nucleus",
    "grounded_relation_preservation": "grounded_relation",
    "unknown_boundary_preservation": "unknown_boundary",
    "significance_or_shift": "significance_or_shift",
    "intention_or_next_action": "intention_or_next_action",
    "self_denial_boundary": "self_denial_boundary",
    "bounded_counterposition": "bounded_counterposition",
}


def _try_reception(
    text: str,
    start: int,
    modality: str,
    prior_observation_atoms: list[dict[str, Any]],
) -> dict[str, Any] | None:
    antecedent = next(
        (
            (key, token)
            for token, key in _inverse_group("antecedent_referent")
            if text.startswith(token, start)
        ),
        None,
    )
    if antecedent is None:
        return None
    obligation_kind, token = antecedent
    offset = start + len(token)
    particle = SURFACE_GRAMMAR_CATALOG["morphology"]["reception_object_particle"]
    if not text.startswith(particle, offset):
        return None
    offset += len(particle)
    act = next(
        (
            key
            for stance_token, key in _inverse_group("stance")
            if text.startswith(stance_token, offset)
            and offset + len(stance_token) == len(text)
        ),
        None,
    )
    if act is None or not prior_observation_atoms:
        return None
    target = prior_observation_atoms[-1]
    if target.get("kind") != _ANTECEDENT_KIND.get(obligation_kind):
        return None
    atom = {
        "kind": "bound_emlis_reception",
        "section_role": "reception",
        "target_atom_ids": [target["atom_id"]],
        "reception_act": act,
        "semantic_signature_sha256": "0" * 64,
        "polarity": target["polarity"],
        "modality": modality,
        "temporal_scope": target["temporal_scope"],
        "topic_fingerprints": list(target["topic_fingerprints"]),
        "referent_scope": target["referent_scope"],
    }
    atom["semantic_signature_sha256"] = _semantic_signature(atom)
    return atom


def _parse_clause(
    clause: str,
    *,
    section_role: str,
    prior_observation_atoms: list[dict[str, Any]],
) -> dict[str, Any]:
    core_start, modality = _prefix(clause)
    if section_role == "reception":
        atom = _try_reception(
            clause, core_start, modality, prior_observation_atoms
        )
    else:
        atom = (
            _try_unknown(clause, core_start, modality)
            or _try_relation(clause, core_start, modality)
            or _try_predicate_or_boundary(clause, core_start, modality)
        )
    if atom is None:
        raise _ParseFailure("UNPARSABLE_CONTROLLED_SURFACE")
    return atom


def _split_clauses(sentence: str) -> list[tuple[str, int, int]]:
    delimiter = SURFACE_GRAMMAR_CATALOG["clause_joiner"]
    opening = SURFACE_GRAMMAR_CATALOG["source_anchor"]["open"]
    closing = SURFACE_GRAMMAR_CATALOG["source_anchor"]["close"]
    result: list[tuple[str, int, int]] = []
    start = 0
    offset = 0
    in_anchor = False
    while offset < len(sentence):
        if sentence.startswith(opening, offset):
            if in_anchor:
                raise _ParseFailure("SOURCE_ANCHOR_NESTED")
            in_anchor = True
            offset += len(opening)
            continue
        if sentence.startswith(closing, offset):
            if not in_anchor:
                raise _ParseFailure("SOURCE_ANCHOR_CLOSE_WITHOUT_OPEN")
            in_anchor = False
            offset += len(closing)
            continue
        if not in_anchor and sentence.startswith(delimiter, offset):
            if offset <= start:
                raise _ParseFailure("EMPTY_CONTROLLED_CLAUSE")
            result.append((sentence[start:offset], start, offset))
            offset += len(delimiter)
            start = offset
            continue
        offset += 1
    if in_anchor:
        raise _ParseFailure("SOURCE_ANCHOR_UNCLOSED")
    if start >= len(sentence):
        raise _ParseFailure("EMPTY_CONTROLLED_CLAUSE")
    result.append((sentence[start:], start, len(sentence)))
    return result


def _char_to_byte_offsets(text: str) -> list[int]:
    offsets = [0]
    total = 0
    for character in text:
        total += len(character.encode("utf-8"))
        offsets.append(total)
    return offsets


def _document_parts(text: str) -> tuple[str, int, str, int]:
    document = SURFACE_GRAMMAR_CATALOG["document"]
    observation_prefix = (
        document["observation_label"] + document["label_body_separator"]
    )
    separator = (
        document["section_separator"]
        + document["reception_label"]
        + document["label_body_separator"]
    )
    if not text.startswith(observation_prefix):
        raise _ParseFailure("LABEL_ORDER_INVALID")
    if text.count(document["observation_label"]) != 1 or text.count(
        document["reception_label"]
    ) != 1:
        raise _ParseFailure("LABEL_COUNT_INVALID")
    split_at = text.find(separator, len(observation_prefix))
    if split_at < 0:
        raise _ParseFailure("SECTION_SEPARATOR_INVALID")
    observation = text[len(observation_prefix) : split_at]
    reception_start = split_at + len(separator)
    reception = text[reception_start:]
    if not observation or not reception:
        raise _ParseFailure("EMPTY_CONTROLLED_SECTION")
    return observation, len(observation_prefix), reception, reception_start


def _unparseable(candidate_sha256: str, code: str) -> dict[str, Any]:
    return {
        "schema_version": WITNESS_V2_SCHEMA,
        "candidate_text_sha256": candidate_sha256,
        "grammar_catalog_sha256": FROZEN_SURFACE_GRAMMAR_CATALOG_SHA256,
        "parser_rulebook_sha256": FROZEN_PARSER_RULEBOOK_SHA256,
        "compatible_observation_stages": list(
            SURFACE_GRAMMAR_CATALOG["parser_compatibility"]["observation_stages"]
        ),
        "compatible_source_roles": list(
            SURFACE_GRAMMAR_CATALOG["parser_compatibility"]["source_roles"]
        ),
        "parse_status": "unparseable",
        "parse_failure_codes": [code],
        "semantic_atoms": [],
        "body_free_export_allowed": False,
    }


def parse_body_semantic_atoms(candidate_text_bytes: bytes) -> dict[str, Any]:
    """Parse only final bytes into a private, source-ID-free v2 witness."""

    if type(candidate_text_bytes) is not bytes:
        raise BodySemanticAtomParseError("CANDIDATE_BYTES_REQUIRED")
    if not _dependencies_valid():
        raise BodySemanticAtomParseError("PARSER_DEPENDENCY_DRIFT")
    candidate_sha = hashlib.sha256(candidate_text_bytes).hexdigest()
    try:
        text = candidate_text_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        raise BodySemanticAtomParseError("CANDIDATE_UTF8_REQUIRED") from None
    if unicodedata.normalize("NFC", text) != text or "\r" in text or text.endswith("\n"):
        witness = _unparseable(candidate_sha, "NON_CANONICAL_CONTROLLED_SURFACE")
        return witness
    try:
        observation, observation_start, reception, reception_start = _document_parts(
            text
        )
        char_to_byte = _char_to_byte_offsets(text)
        atoms: list[dict[str, Any]] = []
        observation_atoms: list[dict[str, Any]] = []
        document = SURFACE_GRAMMAR_CATALOG["document"]
        for section_role, section_text, base_start in (
            ("observation", observation, observation_start),
            ("reception", reception, reception_start),
        ):
            sentence_offset = 0
            sentences = section_text.split(document["sentence_separator"])
            if any(not sentence for sentence in sentences):
                raise _ParseFailure("EMPTY_CONTROLLED_SENTENCE")
            for sentence in sentences:
                terminal = document["terminal"]
                if not sentence.endswith(terminal) or sentence == terminal:
                    raise _ParseFailure("TERMINAL_CONTRACT_INVALID")
                sentence_body = sentence[: -len(terminal)]
                for clause, relative_start, relative_end in _split_clauses(
                    sentence_body
                ):
                    atom = _parse_clause(
                        clause,
                        section_role=section_role,
                        prior_observation_atoms=observation_atoms,
                    )
                    start_char = base_start + sentence_offset + relative_start
                    end_char = base_start + sentence_offset + relative_end
                    start_byte = char_to_byte[start_char]
                    end_byte = char_to_byte[end_char]
                    atom["atom_id"] = _atom_id(
                        candidate_sha256=candidate_sha,
                        section_role=section_role,
                        start=start_byte,
                        end=end_byte,
                        kind=atom["kind"],
                    )
                    atom["utf8_byte_start"] = start_byte
                    atom["utf8_byte_end"] = end_byte
                    atom["span_sha256"] = hashlib.sha256(
                        candidate_text_bytes[start_byte:end_byte]
                    ).hexdigest()
                    # The stance signature includes the final target atom id, so it
                    # is finalized only after that id exists.
                    atom["semantic_signature_sha256"] = _semantic_signature(atom)
                    atoms.append(atom)
                    if section_role == "observation":
                        observation_atoms.append(atom)
                sentence_offset += len(sentence) + len(
                    document["sentence_separator"]
                )
        if sum(
            1
            for atom in atoms
            if atom.get("source_anchor_sha256") is not None
        ) > 1:
            raise _ParseFailure("MULTIPLE_SOURCE_ANCHORS_FORBIDDEN")
        witness = {
            "schema_version": WITNESS_V2_SCHEMA,
            "candidate_text_sha256": candidate_sha,
            "grammar_catalog_sha256": FROZEN_SURFACE_GRAMMAR_CATALOG_SHA256,
            "parser_rulebook_sha256": FROZEN_PARSER_RULEBOOK_SHA256,
            "compatible_observation_stages": list(
                SURFACE_GRAMMAR_CATALOG["parser_compatibility"][
                    "observation_stages"
                ]
            ),
            "compatible_source_roles": list(
                SURFACE_GRAMMAR_CATALOG["parser_compatibility"]["source_roles"]
            ),
            "parse_status": "parsed",
            "parse_failure_codes": [],
            "semantic_atoms": atoms,
            "body_free_export_allowed": False,
        }
    except _ParseFailure as exc:
        witness = _unparseable(candidate_sha, exc.code)
    issues = validate_parsed_surface_witness_v2(
        witness, candidate_text_bytes=candidate_text_bytes
    )
    if issues:
        raise BodySemanticAtomParseError("PARSER_ARTIFACT_CONTRACT_REJECTED")
    return witness


__all__ = [
    "BodySemanticAtomParseError",
    "FROZEN_PARSER_RULEBOOK_SHA256",
    "PARSER_RULEBOOK_SHA256",
    "parse_body_semantic_atoms",
]
