# -*- coding: utf-8 -*-
from __future__ import annotations

"""Independent source matcher for the Step 8 body-derived witness.

This module does not import the forward renderer, Surface AST, discourse or
content planner, generator span map, fixtures, or case metadata.  A separate
opaque authority replays the original grounded sources
once and retains raw Evidence only in a request-local weakref registry so the
single bounded source anchor can be checked independently.  It also replays
the body-only parser from the supplied final bytes before trusting a witness.
"""

from copy import deepcopy
from dataclasses import asdict, dataclass, is_dataclass
import hashlib
from itertools import product
import re
import unicodedata
from typing import Any, Iterable, Mapping, Sequence
import weakref

from emlis_ai_body_semantic_atom_parser_v3 import (
    PARSER_RULEBOOK_SHA256,
    BodySemanticAtomParseError,
    parse_body_semantic_atoms,
)
from emlis_ai_evidence_ledger_service import (
    EvidenceSpanResolver,
    build_evidence_span_resolver,
)
from emlis_ai_grounded_observation_plan import GroundedObservationPlan
from emlis_ai_nls_v3_artifact_contract import (
    TrustedFutureStageAuthority,
    artifact_sha256,
    canonical_json_bytes,
    load_canonical_json_bytes,
)
from emlis_ai_step8_artifact_contract_v3 import (
    BINDING_V2_SCHEMA,
    FROZEN_MATCHER_RULEBOOK_SHA256,
    FROZEN_PARSER_RULEBOOK_SHA256,
    validate_parsed_surface_witness_v2,
    validate_verified_surface_binding_v2,
)
from emlis_ai_semantic_obligation_inventory_v3 import (
    GroundedSourceSnapshot,
    SemanticObligationInventoryResult,
    build_grounded_source_snapshot,
    build_semantic_obligation_inventory,
    validate_semantic_obligation_inventory,
)
from emlis_ai_surface_grammar_catalog_v3_step8 import (
    FROZEN_STEP8_SURFACE_GRAMMAR_CATALOG_SHA256 as FROZEN_SURFACE_GRAMMAR_CATALOG_SHA256,
    STEP8_SURFACE_GRAMMAR_CATALOG as SURFACE_GRAMMAR_CATALOG,
    validate_step8_surface_grammar_catalog as validate_surface_grammar_catalog,
)


_MATCHER_RULEBOOK = {
    "version": "cocolon.emlis.nls_v3.independent_semantic_matcher.20260715.v1",
    "grammar_catalog_sha256": FROZEN_SURFACE_GRAMMAR_CATALOG_SHA256,
    "source_authority": "independent_replay_detached_validated_weakref",
    "candidate_inputs": ["candidate_text_bytes", "parsed_surface_witness"],
    "parser_rulebook_sha256": FROZEN_PARSER_RULEBOOK_SHA256,
    "witness_authenticity": "exact_body_parser_replay",
    "forward_artifacts": "forbidden",
    "matching": "global_unique_one_to_one_nonstance_then_bound_reception",
    "graph_role_matching": "independent_active_source_edge_variant_topological_reconstruction",
    "anchor": "exact_nfc_evidence_prefix_2_to_16_private",
    "failure_rows": "always_empty",
    "current_stage": "normal_observation_only",
    "body_free_export_allowed": False,
}
MATCHER_RULEBOOK_SHA256 = artifact_sha256(_MATCHER_RULEBOOK)

_ATOM_TO_OBLIGATION = {
    "grounded_nucleus": "grounded_nucleus_notice",
    "grounded_relation": "grounded_relation_preservation",
    "unknown_boundary": "unknown_boundary_preservation",
    "significance_or_shift": "significance_or_shift",
    "intention_or_next_action": "intention_or_next_action",
    "self_denial_boundary": "self_denial_boundary",
    "bounded_counterposition": "bounded_counterposition",
    "bound_emlis_reception": "bound_emlis_reception",
}
_PREDICATE_CODE = {
    "grounded_nucleus_notice": "NUCLEUS_OBSERVED",
    "significance_or_shift": "SHIFT_OBSERVED",
    "intention_or_next_action": "ACTION_INTENDED",
    "self_denial_boundary": "SEPARATE_CLAIM_FROM_OBSERVATION",
    "bounded_counterposition": "BOUNDED_COUNTERPOSITION_OBSERVED",
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
_OBSERVATION_KIND_RANK = {
    "grounded_nucleus_notice": 1,
    "significance_or_shift": 2,
    "intention_or_next_action": 3,
    "self_denial_boundary": 4,
    "bounded_counterposition": 5,
}
_ANCHOR_RE = re.compile(r"「([^」]+)」に表れた")
_ANCHOR_FORBIDDEN = frozenset(
    "\r\n。.!！?？:：\"'`｀＂＇「」『』〔〕【】〈〉《》"
)
_ANCHOR_RESERVED = ("見えたこと：", "Emlisから：")


class IndependentSemanticMatchError(ValueError):
    """Fail-closed caller/source/configuration error with one machine code."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, repr=False)
class IndependentMatchSourceAuthority:
    authority_id: str
    source_snapshot_sha256: str
    obligation_ledger_sha256: str
    observation_stage: str
    grammar_catalog_sha256: str
    matcher_rulebook_sha256: str
    body_free: bool = True


@dataclass(frozen=True, slots=True, repr=False)
class _MatchOrigin:
    source_snapshot: GroundedSourceSnapshot
    obligation_ledger_bytes: bytes
    evidence_spans: tuple[Any, ...]

    def ledger(self) -> dict[str, Any]:
        value = load_canonical_json_bytes(self.obligation_ledger_bytes)
        if type(value) is not dict:
            raise IndependentSemanticMatchError("MATCH_SOURCE_LEDGER_INVALID")
        return value


def _authority_store():
    registry: dict[
        int,
        tuple[
            weakref.ReferenceType[IndependentMatchSourceAuthority],
            _MatchOrigin,
        ],
    ] = {}

    def register(
        handle: IndependentMatchSourceAuthority,
        origin: _MatchOrigin,
    ) -> None:
        if type(handle) is not IndependentMatchSourceAuthority or type(
            origin
        ) is not _MatchOrigin:
            raise IndependentSemanticMatchError(
                "MATCH_SOURCE_AUTHORITY_REGISTRATION_INVALID"
            )
        key = id(handle)

        def remove(
            reference: weakref.ReferenceType[IndependentMatchSourceAuthority],
            *,
            registry_key: int = key,
        ) -> None:
            current = registry.get(registry_key)
            if current is not None and current[0] is reference:
                registry.pop(registry_key, None)

        reference = weakref.ref(handle, remove)
        registry[key] = (reference, origin)

    def resolve(handle: Any) -> _MatchOrigin:
        if type(handle) is not IndependentMatchSourceAuthority:
            raise IndependentSemanticMatchError("MATCH_SOURCE_AUTHORITY_REQUIRED")
        current = registry.get(id(handle))
        if current is None or current[0]() is not handle:
            raise IndependentSemanticMatchError("MATCH_SOURCE_AUTHORITY_REQUIRED")
        return current[1]

    return register, resolve


_register_authority, _resolve_authority = _authority_store()


def _jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if type(value) is dict:
        return {str(key): _jsonable(item) for key, item in value.items()}
    if type(value) in {tuple, list}:
        return [_jsonable(item) for item in value]
    if type(value) in {set, frozenset}:
        return sorted(_jsonable(item) for item in value)
    if value is None or type(value) in {str, int, bool}:
        return value
    raise IndependentSemanticMatchError("MATCH_SOURCE_SNAPSHOT_NON_CANONICAL")


def _source_snapshot_sha256(snapshot: GroundedSourceSnapshot) -> str:
    return artifact_sha256(_jsonable(snapshot))


def _dependencies_valid() -> bool:
    return bool(
        not validate_surface_grammar_catalog()
        and not validate_surface_grammar_catalog(SURFACE_GRAMMAR_CATALOG)
        and artifact_sha256(_MATCHER_RULEBOOK)
        == FROZEN_MATCHER_RULEBOOK_SHA256
        and MATCHER_RULEBOOK_SHA256 == FROZEN_MATCHER_RULEBOOK_SHA256
        and PARSER_RULEBOOK_SHA256 == FROZEN_PARSER_RULEBOOK_SHA256
        and _MATCHER_RULEBOOK.get("grammar_catalog_sha256")
        == FROZEN_SURFACE_GRAMMAR_CATALOG_SHA256
    )


def _authority_id(
    *,
    source_snapshot_sha256: str,
    obligation_ledger_sha256: str,
    observation_stage: str,
) -> str:
    return "matchauth_" + artifact_sha256(
        {
            "source_snapshot_sha256": source_snapshot_sha256,
            "obligation_ledger_sha256": obligation_ledger_sha256,
            "observation_stage": observation_stage,
            "grammar_catalog_sha256": FROZEN_SURFACE_GRAMMAR_CATALOG_SHA256,
            "matcher_rulebook_sha256": FROZEN_MATCHER_RULEBOOK_SHA256,
        }
    )[:24]


def open_independent_match_source_authority(
    inventory_result: SemanticObligationInventoryResult,
    *,
    grounded_plan: GroundedObservationPlan,
    resolver: EvidenceSpanResolver,
    observation_stage_context: Mapping[str, Any],
    original_input_bundle: Any,
    trusted_future_authority: TrustedFutureStageAuthority | None = None,
    supplemental_answer_bundle: Any | None = None,
) -> IndependentMatchSourceAuthority:
    """Replay source owners independently and issue a request-local handle."""

    if not _dependencies_valid():
        raise IndependentSemanticMatchError("MATCHER_DEPENDENCY_DRIFT")
    if type(inventory_result) is not SemanticObligationInventoryResult:
        raise IndependentSemanticMatchError("MATCH_INVENTORY_RESULT_INVALID")
    try:
        evidence_spans = tuple(
            deepcopy(resolver.resolve(span_id)) for span_id in resolver.span_ids
        )
        replay_resolver = build_evidence_span_resolver(
            evidence_spans,
            current_input=original_input_bundle,
        )
        replay_snapshot = build_grounded_source_snapshot(
            grounded_plan,
            replay_resolver,
            observation_stage_context=dict(observation_stage_context),
            original_input_bundle=original_input_bundle,
            trusted_future_authority=trusted_future_authority,
            supplemental_answer_bundle=supplemental_answer_bundle,
        )
        replay_inventory = build_semantic_obligation_inventory(replay_snapshot)
    except (
        AttributeError,
        KeyError,
        TypeError,
        ValueError,
        UnicodeError,
        RecursionError,
    ):
        raise IndependentSemanticMatchError("MATCH_SOURCE_REPLAY_FAILED") from None
    if (
        replay_snapshot != inventory_result.source_snapshot
        or replay_inventory.ledger != inventory_result.ledger
        or replay_inventory.resource_counts != inventory_result.resource_counts
        or replay_inventory.inventory_upper_bound
        != inventory_result.inventory_upper_bound
        or validate_semantic_obligation_inventory(
            inventory_result.ledger,
            source_snapshot=inventory_result.source_snapshot,
        )
    ):
        raise IndependentSemanticMatchError("MATCH_SOURCE_REPLAY_MISMATCH")
    snapshot_sha = _source_snapshot_sha256(replay_snapshot)
    ledger_sha = artifact_sha256(replay_inventory.ledger)
    handle = IndependentMatchSourceAuthority(
        authority_id=_authority_id(
            source_snapshot_sha256=snapshot_sha,
            obligation_ledger_sha256=ledger_sha,
            observation_stage=replay_snapshot.observation_stage,
        ),
        source_snapshot_sha256=snapshot_sha,
        obligation_ledger_sha256=ledger_sha,
        observation_stage=replay_snapshot.observation_stage,
        grammar_catalog_sha256=FROZEN_SURFACE_GRAMMAR_CATALOG_SHA256,
        matcher_rulebook_sha256=FROZEN_MATCHER_RULEBOOK_SHA256,
        body_free=True,
    )
    _register_authority(
        handle,
        _MatchOrigin(
            source_snapshot=replay_snapshot,
            obligation_ledger_bytes=(
                canonical_json_bytes(replay_inventory.ledger) + b"\n"
            ),
            evidence_spans=evidence_spans,
        ),
    )
    return handle


def _source_field(source: Any) -> str:
    values = tuple(source.source_fields)
    if (
        len(values) == 1
        and values[0] in SURFACE_GRAMMAR_CATALOG["source_field"]
    ):
        return values[0]
    return "mixed"


def _semantic_role(source: Any) -> str:
    role = "none"
    for code in source.source_attribute_codes:
        if code == "unit_role:antecedent":
            role = "antecedent"
        elif code == "unit_role:consequent":
            role = "consequent"
    return role


def _semantic_qualifier(source: Any) -> str:
    attribute_codes = set(source.source_attribute_codes)
    for key in (
        "concrete_action_evidence",
        "concrete_action",
        "contrast_before",
        "contrast_after",
        "embedded_turn",
        "initial_condition",
        "retained_intention",
    ):
        if f"semantic_role:{key}" in attribute_codes:
            return f"source_semantic_role:{key}"
    for key in ("constraint", "continuation", "shift", "action", "wish"):
        if f"operator:{key}" in attribute_codes:
            return f"source_operator:{key}"
    for block_key in source.source_meaning_block_keys:
        key = str(block_key).rsplit(":", 1)[-1]
        if key in SURFACE_GRAMMAR_CATALOG["meaning_block_kind"]:
            return f"meaning_block_kind:{key}"
    return "none"


def _nucleus_features(source: Any) -> dict[str, str]:
    return {
        "source_field": _source_field(source),
        "source_role": str(source.source_role),
        "temporal_scope": str(source.temporal_scope),
        "semantic_role": _semantic_role(source),
        "polarity": str(source.polarity),
        "semantic_qualifier": _semantic_qualifier(source),
        "nucleus_kind": str(source.kind),
    }


def _nucleus_fingerprint(source: Any) -> str:
    return "semantic_ref_" + artifact_sha256(
        {"nucleus_surface_semantics": _nucleus_features(source)}
    )[:16]


def _topic_fingerprints(sources: Sequence[Any]) -> list[str]:
    return sorted(
        {
            "topic_"
            + artifact_sha256(
                {"surface_referent_fingerprint": _nucleus_fingerprint(source)}
            )[:16]
            for source in sources
        }
    )


def _referent_fingerprint(
    sources: Sequence[Any],
    *,
    anchor_sha256: str | None,
) -> str:
    return "semantic_ref_" + artifact_sha256(
        {
            "ordered_endpoint_fingerprints": [
                _nucleus_fingerprint(source) for source in sources
            ],
            "source_anchor_sha256": anchor_sha256,
        }
    )[:16]


def _dimension_group(value: str) -> str:
    lowered = value.lower()
    for rule in SURFACE_GRAMMAR_CATALOG["unknown_dimension_classification"]:
        contains = rule["contains"]
        if not contains or any(token in lowered for token in contains):
            return rule["code"]
    raise IndependentSemanticMatchError("MATCH_UNKNOWN_DIMENSION_UNRESOLVED")


def _semantic_signature(atom: Mapping[str, Any]) -> str:
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


def _obligation_sources(
    obligation: Mapping[str, Any],
    snapshot: GroundedSourceSnapshot,
) -> tuple[Any, ...]:
    nucleus_by_id = {row.source_id: row for row in snapshot.nuclei}
    if obligation.get("kind") == "grounded_relation_preservation":
        relation_ids = obligation.get("relation_ids") or []
        if len(relation_ids) != 1:
            return ()
        relation = next(
            (
                row
                for row in snapshot.relations
                if row.source_id == relation_ids[0]
            ),
            None,
        )
        if relation is None:
            return ()
        source_id, target_id = relation.from_nucleus_id, relation.to_nucleus_id
        if relation.relation_direction == "target_to_source":
            source_id, target_id = target_id, source_id
        if source_id not in nucleus_by_id or target_id not in nucleus_by_id:
            return ()
        return (nucleus_by_id[source_id], nucleus_by_id[target_id])
    return tuple(
        nucleus_by_id[item]
        for item in obligation.get("nucleus_ids", [])
        if item in nucleus_by_id
    )


def _source_roles(obligation: Mapping[str, Any]) -> list[str]:
    return sorted(
        {
            row.get("source_role")
            for row in obligation.get("source_refs", [])
            if type(row) is dict and type(row.get("source_role")) is str
        }
    )


def _anchor_text(
    atom: Mapping[str, Any],
    candidate_text_bytes: bytes,
) -> str | None:
    start = atom.get("utf8_byte_start")
    end = atom.get("utf8_byte_end")
    if type(start) is not int or type(end) is not int:
        return None
    try:
        span = candidate_text_bytes[start:end].decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return None
    values = _ANCHOR_RE.findall(span)
    if not values:
        return None
    if len(values) != 1:
        return ""
    return values[0]


def _anchor_belongs_to_obligation(
    atom: Mapping[str, Any],
    obligation: Mapping[str, Any],
    *,
    candidate_text_bytes: bytes,
    snapshot: GroundedSourceSnapshot,
    evidence_spans: Sequence[Any],
) -> bool:
    expected_sha = atom.get("source_anchor_sha256")
    expected_count = atom.get("source_anchor_scalar_count")
    visible = _anchor_text(atom, candidate_text_bytes)
    if expected_sha is None:
        return visible is None and expected_count == 0
    if (
        type(visible) is not str
        or not visible
        or hashlib.sha256(visible.encode("utf-8")).hexdigest() != expected_sha
        or len(visible) != expected_count
        or not 2 <= len(visible) <= 16
        or any(char in _ANCHOR_FORBIDDEN for char in visible)
        or any(token in visible for token in _ANCHOR_RESERVED)
        or any(unicodedata.category(char).startswith("C") for char in visible)
    ):
        return False
    alias_to_actual = {
        row.alias_source_id: row.actual_source_id
        for row in snapshot.source_id_alias_bindings
        if row.source_kind == "evidence"
    }
    span_by_id = {str(row.span_id): row for row in evidence_spans}
    for evidence_id in obligation.get("evidence_ids", []):
        span = span_by_id.get(str(alias_to_actual.get(evidence_id)))
        if span is None:
            continue
        raw = unicodedata.normalize(
            "NFC", str(getattr(span, "raw_text", "")).strip()
        )[:16]
        if raw == visible:
            return True
    return False


def _expected_nonstance_atom(
    atom: Mapping[str, Any],
    obligation: Mapping[str, Any],
    *,
    candidate_text_bytes: bytes,
    snapshot: GroundedSourceSnapshot,
    evidence_spans: Sequence[Any],
) -> bool:
    if _ATOM_TO_OBLIGATION.get(atom.get("kind")) != obligation.get("kind"):
        return False
    if not obligation.get("evidence_ids"):
        return False
    if _source_roles(obligation) != ["original_input"]:
        return False
    for field in ("polarity", "modality", "temporal_scope", "referent_scope"):
        if atom.get(field) != obligation.get(field):
            return False
    sources = _obligation_sources(obligation, snapshot)
    if not sources:
        return False
    anchor_sha = atom.get("source_anchor_sha256")
    if not _anchor_belongs_to_obligation(
        atom,
        obligation,
        candidate_text_bytes=candidate_text_bytes,
        snapshot=snapshot,
        evidence_spans=evidence_spans,
    ):
        return False
    expected = {
        "kind": atom.get("kind"),
        "section_role": "observation",
        "graph_role": atom.get("graph_role"),
        "referent_fingerprint": _referent_fingerprint(
            sources, anchor_sha256=anchor_sha
        ),
        "semantic_signature_sha256": "0" * 64,
        "source_anchor_sha256": anchor_sha,
        "source_anchor_scalar_count": atom.get("source_anchor_scalar_count"),
        "polarity": obligation.get("polarity"),
        "modality": obligation.get("modality"),
        "temporal_scope": obligation.get("temporal_scope"),
        "topic_fingerprints": _topic_fingerprints(sources),
        "referent_scope": obligation.get("referent_scope"),
    }
    if atom.get("kind") == "grounded_relation":
        descriptor = (obligation.get("relation_directions") or [None])[0]
        if type(descriptor) is not dict:
            return False
        expected.update(
            {
                "relation_type": descriptor.get("relation_type"),
                "surface_direction": (
                    "bidirectional"
                    if descriptor.get("direction") == "bidirectional"
                    else "left_to_right"
                ),
                "ordered_endpoint_fingerprints": [
                    _nucleus_fingerprint(source) for source in sources
                ],
            }
        )
    elif atom.get("kind") == "unknown_boundary":
        unknown_by_id = {row.source_id: row for row in snapshot.unknowns}
        dimensions = sorted(
            {
                _dimension_group(unknown_by_id[item].source_dimension)
                for item in obligation.get("unknown_boundary_ids", [])
                if item in unknown_by_id
            }
        )
        if not dimensions:
            return False
        expected["unknown_dimension_codes"] = dimensions
    else:
        expected["predicate_code"] = _PREDICATE_CODE.get(obligation.get("kind"))
    expected["semantic_signature_sha256"] = _semantic_signature(expected)
    return all(atom.get(key) == value for key, value in expected.items())


def _binding_row(
    atom: Mapping[str, Any],
    obligation: Mapping[str, Any],
) -> dict[str, Any]:
    relation_id = None
    relation_direction = None
    if atom.get("kind") == "grounded_relation":
        relation_ids = obligation.get("relation_ids") or []
        descriptor = (obligation.get("relation_directions") or [None])[0]
        relation_id = relation_ids[0] if len(relation_ids) == 1 else None
        relation_direction = (
            descriptor.get("direction") if type(descriptor) is dict else None
        )
    return {
        "atom_id": atom["atom_id"],
        "obligation_id": obligation["obligation_id"],
        "evidence_ids": list(obligation.get("evidence_ids", [])),
        "nucleus_ids": list(obligation.get("nucleus_ids", [])),
        "relation_id": relation_id,
        "relation_direction": relation_direction,
        "unknown_boundary_ids": list(
            obligation.get("unknown_boundary_ids", [])
        ),
        "target_obligation_ids": list(
            obligation.get("target_obligation_ids", [])
        ),
        "topic_scope_ids": list(obligation.get("topic_scope_ids", [])),
        "source_roles": _source_roles(obligation),
        "match_basis": _MATCH_BASIS[atom["kind"]],
        "match_candidate_count": 1,
    }


def _nonstance_assignments(
    atoms: Sequence[Mapping[str, Any]],
    obligations: Sequence[Mapping[str, Any]],
    *,
    candidate_text_bytes: bytes,
    snapshot: GroundedSourceSnapshot,
    evidence_spans: Sequence[Any],
) -> list[dict[str, Mapping[str, Any]]]:
    choices: list[tuple[str, list[Mapping[str, Any]]]] = []
    for atom in atoms:
        candidates = [
            obligation
            for obligation in obligations
            if _expected_nonstance_atom(
                atom,
                obligation,
                candidate_text_bytes=candidate_text_bytes,
                snapshot=snapshot,
                evidence_spans=evidence_spans,
            )
        ]
        if not candidates:
            return []
        choices.append((atom["atom_id"], candidates))
    choices.sort(key=lambda row: (len(row[1]), row[0]))
    results: list[dict[str, Mapping[str, Any]]] = []

    def search(
        index: int,
        used: set[str],
        current: dict[str, Mapping[str, Any]],
    ) -> None:
        if len(results) >= 2:
            return
        if index == len(choices):
            results.append(dict(current))
            return
        atom_id, candidates = choices[index]
        for obligation in candidates:
            obligation_id = obligation["obligation_id"]
            if obligation_id in used:
                continue
            used.add(obligation_id)
            current[atom_id] = obligation
            search(index + 1, used, current)
            current.pop(atom_id, None)
            used.remove(obligation_id)

    search(0, set(), {})
    return results


def _representative_obligation(
    nucleus_id: str,
    active_rows: Sequence[Mapping[str, Any]],
) -> str | None:
    candidates = [
        row
        for row in active_rows
        if row.get("kind") in _OBSERVATION_KIND_RANK
        and nucleus_id in (row.get("nucleus_ids") or [])
    ]
    if not candidates:
        return None
    candidates.sort(
        key=lambda row: (
            0 if len(row.get("nucleus_ids") or []) == 1 else 1,
            _OBSERVATION_KIND_RANK.get(str(row.get("kind")), 99),
            str(row.get("obligation_id", "")),
        )
    )
    return str(candidates[0]["obligation_id"])


def _edges_are_acyclic(
    edges: Iterable[tuple[str, str, str]],
) -> bool:
    pairs = {(source, target) for source, target, _kind in edges}
    nodes = {item for pair in pairs for item in pair}
    outgoing = {
        node: {target for source, target in pairs if source == node}
        for node in nodes
    }
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return False
        if node in visited:
            return True
        visiting.add(node)
        for target in outgoing.get(node, set()):
            if not visit(target):
                return False
        visiting.remove(node)
        visited.add(node)
        return True

    return all(visit(node) for node in sorted(nodes))


def _role_for_obligation(
    obligation_id: str,
    edges: Iterable[tuple[str, str, str]],
) -> str:
    rows = tuple(edges)
    incoming = [kind for source, target, kind in rows if target == obligation_id]
    outgoing = [kind for source, target, kind in rows if source == obligation_id]
    if "precedes" in outgoing:
        return "precedes_source"
    if "precedes" in incoming:
        return "precedes_target"
    if set(outgoing) & {"coexists_with", "contrasts_with"}:
        return "relation_source"
    if set(incoming) & {"coexists_with", "contrasts_with"}:
        return "relation_target"
    if "preserves_unknown_before" in incoming:
        return "unknown_related"
    return "none"


def _graph_roles_match_source(
    atoms: Sequence[Mapping[str, Any]],
    assignment: Mapping[str, Mapping[str, Any]],
    snapshot: GroundedSourceSnapshot,
) -> bool:
    """Reconstruct allowed source edge variants without planner artifacts."""

    active_rows = tuple(assignment.values())
    fixed: set[tuple[str, str, str]] = set()
    directed: set[tuple[str, str, str]] = set()
    choices: list[tuple[tuple[str, str, str], tuple[str, str, str]]] = []
    relation_by_id = {row.source_id: row for row in snapshot.relations}
    for row in active_rows:
        obligation_id = str(row.get("obligation_id", ""))
        if row.get("kind") == "unknown_boundary_preservation":
            for nucleus_id in row.get("nucleus_ids", []):
                target_id = _representative_obligation(
                    str(nucleus_id), active_rows
                )
                if target_id is not None:
                    fixed.add(
                        (
                            obligation_id,
                            target_id,
                            "preserves_unknown_before",
                        )
                    )
        if row.get("kind") != "grounded_relation_preservation":
            continue
        relation_ids = row.get("relation_ids") or []
        if len(relation_ids) != 1:
            return False
        relation = relation_by_id.get(str(relation_ids[0]))
        if relation is None:
            return False
        left_id = _representative_obligation(
            relation.from_nucleus_id, active_rows
        )
        right_id = _representative_obligation(
            relation.to_nucleus_id, active_rows
        )
        if left_id is None or right_id is None or left_id == right_id:
            continue
        edge_type = relation.relation_type
        if edge_type not in {
            "precedes",
            "coexists_with",
            "contrasts_with",
        }:
            continue
        if relation.relation_direction == "bidirectional":
            choices.append(
                (
                    (left_id, right_id, edge_type),
                    (right_id, left_id, edge_type),
                )
            )
        elif relation.relation_direction == "source_to_target":
            directed.add((left_id, right_id, edge_type))
        elif relation.relation_direction == "target_to_source":
            directed.add((right_id, left_id, edge_type))
        else:
            return False

    variants: list[set[tuple[str, str, str]]] = []
    for selected in product(*choices) if choices else [()]:
        variant = {*fixed, *directed, *selected}
        if _edges_are_acyclic(variant) and variant not in variants:
            variants.append(variant)
    if fixed not in variants:
        variants.append(set(fixed))
    atom_by_id = {str(atom.get("atom_id")): atom for atom in atoms}
    atom_index_by_obligation = {
        str(obligation.get("obligation_id", "")): index
        for index, atom in enumerate(atoms)
        for atom_id, obligation in assignment.items()
        if atom_id == atom.get("atom_id")
    }
    for variant in variants:
        if any(
            atom_index_by_obligation.get(source, -1)
            >= atom_index_by_obligation.get(target, -1)
            for source, target, _kind in variant
        ):
            continue
        if all(
            atom_by_id.get(atom_id, {}).get("graph_role")
            == _role_for_obligation(
                str(obligation.get("obligation_id", "")), variant
            )
            for atom_id, obligation in assignment.items()
        ):
            return True
    return False


def _reception_candidates(
    atom: Mapping[str, Any],
    obligations: Sequence[Mapping[str, Any]],
    assignment: Mapping[str, Mapping[str, Any]],
) -> list[Mapping[str, Any]]:
    target_ids = [
        assignment.get(atom_id, {}).get("obligation_id")
        for atom_id in atom.get("target_atom_ids", [])
    ]
    if None in target_ids:
        return []
    results: list[Mapping[str, Any]] = []
    for obligation in obligations:
        if obligation.get("kind") != "bound_emlis_reception":
            continue
        if not obligation.get("evidence_ids"):
            continue
        if _source_roles(obligation) != ["original_input"]:
            continue
        if target_ids != obligation.get("target_obligation_ids"):
            continue
        if atom.get("reception_act") not in obligation.get(
            "allowed_response_acts", []
        ):
            continue
        if any(
            atom.get(field) != obligation.get(field)
            for field in (
                "polarity",
                "modality",
                "temporal_scope",
                "referent_scope",
            )
        ):
            continue
        expected_signature = _semantic_signature(atom)
        if atom.get("semantic_signature_sha256") != expected_signature:
            continue
        results.append(obligation)
    return results


def _failure_binding(
    *,
    witness: Mapping[str, Any],
    ledger: Mapping[str, Any],
    source_snapshot_sha256: str,
    observation_stage: str,
    status: str,
    code: str,
) -> dict[str, Any]:
    return {
        "schema_version": BINDING_V2_SCHEMA,
        "parsed_surface_witness_sha256": artifact_sha256(witness),
        "source_obligation_ledger_sha256": artifact_sha256(ledger),
        "source_snapshot_sha256": source_snapshot_sha256,
        "matcher_rulebook_sha256": FROZEN_MATCHER_RULEBOOK_SHA256,
        "observation_stage": observation_stage,
        "bindings": [],
        "binding_status": status,
        "failure_codes": [code],
        "body_free_export_allowed": False,
    }


def match_parsed_surface_witness(
    parsed_surface_witness: Mapping[str, Any],
    *,
    candidate_text_bytes: bytes,
    inventory_result: SemanticObligationInventoryResult,
    match_authority: IndependentMatchSourceAuthority,
) -> dict[str, Any]:
    """Bind body-derived atoms globally without any forward candidate data."""

    if not _dependencies_valid():
        raise IndependentSemanticMatchError("MATCHER_DEPENDENCY_DRIFT")
    origin = _resolve_authority(match_authority)
    ledger = origin.ledger()
    snapshot = origin.source_snapshot
    snapshot_sha = _source_snapshot_sha256(snapshot)
    ledger_sha = artifact_sha256(ledger)
    expected_authority_id = _authority_id(
        source_snapshot_sha256=snapshot_sha,
        obligation_ledger_sha256=ledger_sha,
        observation_stage=snapshot.observation_stage,
    )
    if (
        type(candidate_text_bytes) is not bytes
        or type(inventory_result) is not SemanticObligationInventoryResult
        or inventory_result.source_snapshot != snapshot
        or inventory_result.ledger != ledger
        or match_authority.authority_id != expected_authority_id
        or match_authority.source_snapshot_sha256 != snapshot_sha
        or match_authority.obligation_ledger_sha256 != ledger_sha
        or match_authority.observation_stage != snapshot.observation_stage
        or match_authority.grammar_catalog_sha256
        != FROZEN_SURFACE_GRAMMAR_CATALOG_SHA256
        or match_authority.matcher_rulebook_sha256
        != FROZEN_MATCHER_RULEBOOK_SHA256
        or match_authority.body_free is not True
    ):
        raise IndependentSemanticMatchError("MATCH_SOURCE_PARENT_MISMATCH")
    witness_issues = validate_parsed_surface_witness_v2(
        parsed_surface_witness,
        candidate_text_bytes=candidate_text_bytes,
    )
    if witness_issues:
        raise IndependentSemanticMatchError("MATCH_WITNESS_CONTRACT_REJECTED")
    try:
        replayed_witness = parse_body_semantic_atoms(candidate_text_bytes)
    except BodySemanticAtomParseError:
        raise IndependentSemanticMatchError("MATCH_BODY_REPLAY_FAILED") from None
    if replayed_witness != parsed_surface_witness:
        result = _failure_binding(
            witness=parsed_surface_witness,
            ledger=ledger,
            source_snapshot_sha256=snapshot_sha,
            observation_stage=snapshot.observation_stage,
            status="no_semantic_binding",
            code="PARSED_WITNESS_REPLAY_MISMATCH",
        )
    elif parsed_surface_witness.get("parse_status") != "parsed":
        result = _failure_binding(
            witness=parsed_surface_witness,
            ledger=ledger,
            source_snapshot_sha256=snapshot_sha,
            observation_stage=snapshot.observation_stage,
            status="unparseable_surface",
            code="UNPARSABLE_CONTROLLED_SURFACE",
        )
    elif (
        snapshot.observation_stage
        not in parsed_surface_witness.get("compatible_observation_stages", [])
        or set(snapshot.semantic_source_roles)
        - set(parsed_surface_witness.get("compatible_source_roles", []))
    ):
        result = _failure_binding(
            witness=parsed_surface_witness,
            ledger=ledger,
            source_snapshot_sha256=snapshot_sha,
            observation_stage=snapshot.observation_stage,
            status="source_context_mismatch",
            code="SOURCE_CONTEXT_NOT_BODY_RECOVERABLE",
        )
    else:
        atoms = parsed_surface_witness["semantic_atoms"]
        nonstance = [
            atom for atom in atoms if atom.get("kind") != "bound_emlis_reception"
        ]
        stances = [
            atom for atom in atoms if atom.get("kind") == "bound_emlis_reception"
        ]
        obligations = list(ledger.get("obligations", []))
        assignments = _nonstance_assignments(
            nonstance,
            obligations,
            candidate_text_bytes=candidate_text_bytes,
            snapshot=snapshot,
            evidence_spans=origin.evidence_spans,
        )
        complete: list[list[dict[str, Any]]] = []
        for assignment in assignments:
            if not _graph_roles_match_source(nonstance, assignment, snapshot):
                continue
            used = {
                obligation["obligation_id"] for obligation in assignment.values()
            }
            rows = [
                _binding_row(atom, assignment[atom["atom_id"]])
                for atom in nonstance
            ]
            valid = True
            for stance in stances:
                candidates = [
                    obligation
                    for obligation in _reception_candidates(
                        stance, obligations, assignment
                    )
                    if obligation["obligation_id"] not in used
                ]
                if len(candidates) != 1:
                    valid = False
                    if len(candidates) > 1:
                        complete.extend([[], []])
                    break
                selected = candidates[0]
                used.add(selected["obligation_id"])
                rows.append(_binding_row(stance, selected))
            required = set(ledger.get("required_obligation_ids", []))
            if valid and required <= used:
                complete.append(rows)
            if len(complete) >= 2:
                break
        if not complete:
            result = _failure_binding(
                witness=parsed_surface_witness,
                ledger=ledger,
                source_snapshot_sha256=snapshot_sha,
                observation_stage=snapshot.observation_stage,
                status="no_semantic_binding",
                code="NO_SEMANTIC_BINDING",
            )
        elif len(complete) > 1:
            result = _failure_binding(
                witness=parsed_surface_witness,
                ledger=ledger,
                source_snapshot_sha256=snapshot_sha,
                observation_stage=snapshot.observation_stage,
                status="ambiguous_semantic_binding",
                code="AMBIGUOUS_SEMANTIC_BINDING",
            )
        else:
            result = {
                "schema_version": BINDING_V2_SCHEMA,
                "parsed_surface_witness_sha256": artifact_sha256(
                    parsed_surface_witness
                ),
                "source_obligation_ledger_sha256": ledger_sha,
                "source_snapshot_sha256": snapshot_sha,
                "matcher_rulebook_sha256": FROZEN_MATCHER_RULEBOOK_SHA256,
                "observation_stage": snapshot.observation_stage,
                "bindings": complete[0],
                "binding_status": "matched",
                "failure_codes": [],
                "body_free_export_allowed": False,
            }
    binding_issues = validate_verified_surface_binding_v2(
        result,
        parsed_surface_witness=parsed_surface_witness,
        candidate_text_bytes=candidate_text_bytes,
        obligation_ledger=ledger,
        ledger_authority=snapshot.ledger_source_authority,
        source_snapshot_sha256=snapshot_sha,
        observation_stage=snapshot.observation_stage,
    )
    if binding_issues:
        raise IndependentSemanticMatchError("MATCH_BINDING_CONTRACT_REJECTED")
    return result


__all__ = [
    "IndependentMatchSourceAuthority",
    "IndependentSemanticMatchError",
    "MATCHER_RULEBOOK_SHA256",
    "match_parsed_surface_witness",
    "open_independent_match_source_authority",
]
