# -*- coding: utf-8 -*-
from __future__ import annotations

"""Request-bound lexical authority and canonical Step 7 renderer."""

from dataclasses import dataclass
import hashlib
import unicodedata
from typing import Any, Mapping
import weakref

from emlis_ai_content_selection_v3 import validate_content_selection_policy
from emlis_ai_discourse_graph_planner_v3 import build_discourse_graph_plans
from emlis_ai_evidence_ledger_service import EvidenceSpanResolver
from emlis_ai_grounded_observation_plan import GroundedObservationPlan
from emlis_ai_nls_v3_artifact_contract import (
    TrustedFutureStageAuthority,
    artifact_sha256,
    canonical_json_bytes,
    load_canonical_json_bytes,
    validate_discourse_plan,
    validate_surface_ast,
)
from emlis_ai_semantic_obligation_inventory_v3 import (
    GroundedSourceSnapshot,
    SemanticObligationInventoryResult,
    build_grounded_source_snapshot,
    build_semantic_obligation_inventory,
    validate_semantic_obligation_inventory,
)
from emlis_ai_surface_grammar_catalog_v3 import (
    FROZEN_SURFACE_GRAMMAR_CATALOG_SHA256,
    SURFACE_GRAMMAR_CATALOG,
    catalog_token,
    validate_surface_grammar_catalog,
)
from emlis_ai_typed_surface_ast_v3 import validate_typed_surface_ast


class CanonicalSurfaceRenderError(ValueError):
    """Fail-closed error whose message is always one machine code."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, repr=False)
class RequestLexicalAuthority:
    authority_id: str
    source_snapshot_sha256: str
    obligation_ledger_sha256: str
    observation_stage: str
    grammar_catalog_sha256: str
    body_free: bool = True


@dataclass(frozen=True, repr=False)
class CanonicalRenderedSurface:
    utf8_bytes: bytes
    sha256: str
    surface_ast_sha256: str
    grammar_catalog_sha256: str
    raw_anchor_count: int
    anchor_reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True, repr=False)
class _SourceAnchor:
    obligation_id: str
    text: str


@dataclass(frozen=True, slots=True, repr=False)
class _LexicalOrigin:
    grounded_plan: GroundedObservationPlan
    evidence_spans: tuple[Any, ...]
    observation_stage_context_bytes: bytes
    original_input_bundle_bytes: bytes
    trusted_future_authority: TrustedFutureStageAuthority | None
    supplemental_answer_bundle_bytes: bytes

    def rebuild(self) -> tuple[GroundedSourceSnapshot, SemanticObligationInventoryResult]:
        resolver = EvidenceSpanResolver(self.evidence_spans)
        snapshot = build_grounded_source_snapshot(
            self.grounded_plan,
            resolver,
            observation_stage_context=load_canonical_json_bytes(
                self.observation_stage_context_bytes
            ),
            original_input_bundle=load_canonical_json_bytes(
                self.original_input_bundle_bytes
            ),
            trusted_future_authority=self.trusted_future_authority,
            supplemental_answer_bundle=load_canonical_json_bytes(
                self.supplemental_answer_bundle_bytes
            ),
        )
        return snapshot, build_semantic_obligation_inventory(snapshot)


def _authority_store():
    registry: dict[
        int,
        tuple[weakref.ReferenceType[RequestLexicalAuthority], _LexicalOrigin],
    ] = {}

    def register(handle: RequestLexicalAuthority, origin: _LexicalOrigin) -> None:
        if type(handle) is not RequestLexicalAuthority or type(origin) is not _LexicalOrigin:
            raise CanonicalSurfaceRenderError("LEXICAL_AUTHORITY_REGISTRATION_INVALID")
        key = id(handle)

        def remove(
            reference: weakref.ReferenceType[RequestLexicalAuthority],
            *, registry_key: int = key,
        ) -> None:
            current = registry.get(registry_key)
            if current is not None and current[0] is reference:
                registry.pop(registry_key, None)

        reference = weakref.ref(handle, remove)
        registry[key] = (reference, origin)

    def resolve(handle: Any) -> _LexicalOrigin:
        if type(handle) is not RequestLexicalAuthority:
            raise CanonicalSurfaceRenderError("LEXICAL_AUTHORITY_REQUIRED")
        current = registry.get(id(handle))
        if current is None or current[0]() is not handle:
            raise CanonicalSurfaceRenderError("LEXICAL_AUTHORITY_REQUIRED")
        return current[1]

    return register, resolve


_register_authority, _resolve_authority = _authority_store()


def _inventory_matches(
    left: SemanticObligationInventoryResult,
    right: SemanticObligationInventoryResult,
) -> bool:
    return bool(
        left.ledger == right.ledger
        and left.source_snapshot == right.source_snapshot
        and left.resource_counts == right.resource_counts
        and left.inventory_upper_bound == right.inventory_upper_bound
    )


def _source_snapshot_authority_sha256(
    snapshot: GroundedSourceSnapshot,
) -> str:
    return artifact_sha256(
        {
            "source_observation_plan_sha256": snapshot.source_observation_plan_sha256,
            "source_observation_stage_context_sha256": (
                snapshot.source_observation_stage_context_sha256
            ),
            "source_policy_sha256": snapshot.source_policy_sha256,
            "source_semantic_restatement_witness_sha256": (
                snapshot.source_semantic_restatement_witness_sha256
            ),
        }
    )


def _lexical_authority_id(
    *, snapshot_hash: str, ledger_hash: str, observation_stage: str
) -> str:
    return "lexauth_" + artifact_sha256(
        {
            "source_snapshot_sha256": snapshot_hash,
            "obligation_ledger_sha256": ledger_hash,
            "observation_stage": observation_stage,
            "grammar_catalog_sha256": FROZEN_SURFACE_GRAMMAR_CATALOG_SHA256,
        }
    )[:24]


def open_request_lexical_authority(
    inventory_result: SemanticObligationInventoryResult,
    *,
    grounded_plan: GroundedObservationPlan,
    resolver: EvidenceSpanResolver,
    observation_stage_context: Mapping[str, Any],
    original_input_bundle: Any,
    trusted_future_authority: TrustedFutureStageAuthority | None = None,
    supplemental_answer_bundle: Any | None = None,
) -> RequestLexicalAuthority:
    """Issue an opaque capability only after an independent source replay."""

    if type(inventory_result) is not SemanticObligationInventoryResult:
        raise CanonicalSurfaceRenderError("LEXICAL_INVENTORY_RESULT_INVALID")
    if (
        validate_surface_grammar_catalog()
        or validate_surface_grammar_catalog(SURFACE_GRAMMAR_CATALOG)
    ):
        raise CanonicalSurfaceRenderError("LEXICAL_CATALOG_DRIFT")
    if validate_semantic_obligation_inventory(
        inventory_result.ledger,
        source_snapshot=inventory_result.source_snapshot,
    ):
        raise CanonicalSurfaceRenderError("LEXICAL_INVENTORY_REVALIDATION_FAILED")
    try:
        spans = tuple(resolver.resolve(item) for item in resolver.span_ids)
        origin = _LexicalOrigin(
            grounded_plan=grounded_plan,
            evidence_spans=spans,
            observation_stage_context_bytes=(
                canonical_json_bytes(dict(observation_stage_context)) + b"\n"
            ),
            original_input_bundle_bytes=(
                canonical_json_bytes(original_input_bundle) + b"\n"
            ),
            trusted_future_authority=trusted_future_authority,
            supplemental_answer_bundle_bytes=(
                canonical_json_bytes(supplemental_answer_bundle) + b"\n"
            ),
        )
        replay_snapshot, replay_inventory = origin.rebuild()
    except (AttributeError, KeyError, TypeError, ValueError, UnicodeError):
        raise CanonicalSurfaceRenderError(
            "LEXICAL_AUTHORITY_REVALIDATION_FAILED"
        ) from None
    if (
        replay_snapshot != inventory_result.source_snapshot
        or not _inventory_matches(replay_inventory, inventory_result)
    ):
        raise CanonicalSurfaceRenderError("LEXICAL_SOURCE_SNAPSHOT_MISMATCH")
    snapshot_hash = _source_snapshot_authority_sha256(replay_snapshot)
    ledger_hash = artifact_sha256(replay_inventory.ledger)
    authority_id = _lexical_authority_id(
        snapshot_hash=snapshot_hash,
        ledger_hash=ledger_hash,
        observation_stage=replay_snapshot.observation_stage,
    )
    handle = RequestLexicalAuthority(
        authority_id=authority_id,
        source_snapshot_sha256=snapshot_hash,
        obligation_ledger_sha256=ledger_hash,
        observation_stage=replay_snapshot.observation_stage,
        grammar_catalog_sha256=FROZEN_SURFACE_GRAMMAR_CATALOG_SHA256,
        body_free=True,
    )
    _register_authority(handle, origin)
    return handle


def _dimension_group(dimension: str) -> str:
    lowered = dimension.lower()
    if "cause" in lowered or "reason" in lowered:
        return "cause"
    if "choice" in lowered or "decision" in lowered or "alternative" in lowered:
        return "choice"
    if "referent" in lowered or "target" in lowered:
        return "referent"
    if "relation" in lowered or "connection" in lowered:
        return "relation"
    if "outcome" in lowered or "future" in lowered:
        return "outcome"
    return "other"


_SOURCE_ANCHOR_MAX_SCALARS = 16
_SOURCE_ANCHOR_FORBIDDEN = frozenset(
    "\r\n。.!！?？:：\"'`｀＂＇「」『』〔〕【】〈〉《》"
)
_SOURCE_ANCHOR_RESERVED_TOKENS = (
    "見えたこと：",
    "Emlisから：",
)


def _select_source_anchor(
    *,
    ledger: Mapping[str, Any],
    content_plan: Mapping[str, Any],
    snapshot: GroundedSourceSnapshot,
    origin: _LexicalOrigin,
) -> _SourceAnchor | None:
    """Choose one bounded, exact request-local anchor without fixture cues."""

    obligation_by_id = {
        row["obligation_id"]: row
        for row in ledger["obligations"]
    }
    active_ids = {
        row["obligation_id"]
        for row in content_plan["decisions"]
        if row["status"] in {"selected", "integrated_into"}
    }
    stance_targets = [
        target
        for row in ledger["obligations"]
        if row["obligation_id"] in active_ids
        and row["kind"] == "bound_emlis_reception"
        for target in row["target_obligation_ids"]
        if target in active_ids
    ]
    required_nonstance = [
        row["obligation_id"]
        for row in ledger["obligations"]
        if row["obligation_id"] in active_ids
        and row["kind"] != "bound_emlis_reception"
        and row["required"] is True
    ]
    candidate_obligations = tuple(
        dict.fromkeys((*stance_targets, *required_nonstance))
    )
    alias_to_actual = {
        row.alias_source_id: row.actual_source_id
        for row in snapshot.source_id_alias_bindings
        if row.source_kind == "evidence"
    }
    span_by_id = {
        str(span.span_id): span for span in origin.evidence_spans
    }
    for obligation_id in candidate_obligations:
        obligation = obligation_by_id.get(obligation_id)
        if obligation is None:
            continue
        for evidence_id in obligation["evidence_ids"]:
            actual_id = alias_to_actual.get(evidence_id)
            span = span_by_id.get(str(actual_id))
            if span is None:
                continue
            raw_text = unicodedata.normalize(
                "NFC", str(getattr(span, "raw_text", "")).strip()
            )
            text = raw_text[:_SOURCE_ANCHOR_MAX_SCALARS]
            if len(text) < 2 or any(char in _SOURCE_ANCHOR_FORBIDDEN for char in text):
                continue
            if any(token in text for token in _SOURCE_ANCHOR_RESERVED_TOKENS):
                continue
            if any(unicodedata.category(char).startswith("C") for char in text):
                continue
            return _SourceAnchor(obligation_id=obligation_id, text=text)
    return None


def _graph_role(discourse_node_id: str, discourse_plan: Mapping[str, Any]) -> str:
    incoming = [
        edge["type"]
        for edge in discourse_plan["edges"]
        if edge["to"] == discourse_node_id
    ]
    outgoing = [
        edge["type"]
        for edge in discourse_plan["edges"]
        if edge["from"] == discourse_node_id
    ]
    if "precedes" in outgoing:
        return "順序の前側にある"
    if "precedes" in incoming:
        return "順序の後側にある"
    if set(outgoing) & {"coexists_with", "contrasts_with"}:
        return "関係の一方にある"
    if set(incoming) & {"coexists_with", "contrasts_with"}:
        return "関係のもう一方にある"
    if "preserves_unknown_before" in incoming:
        return "分からなさが関わる"
    return ""


def _nucleus_phrase(source: Any) -> str:
    fields = tuple(source.source_fields)
    field_key = fields[0] if len(fields) == 1 and fields[0] in (
        SURFACE_GRAMMAR_CATALOG["source_field"]
    ) else "mixed"
    role = "none"
    for code in source.source_attribute_codes:
        if code == "unit_role:antecedent":
            role = "antecedent"
        elif code == "unit_role:consequent":
            role = "consequent"
    semantic_qualifier = ""
    source_role_priority = (
        "concrete_action_evidence",
        "concrete_action",
        "contrast_before",
        "contrast_after",
        "embedded_turn",
        "initial_condition",
        "retained_intention",
    )
    attribute_codes = set(source.source_attribute_codes)
    for source_role in source_role_priority:
        if f"semantic_role:{source_role}" in attribute_codes:
            semantic_qualifier = catalog_token(
                "source_semantic_role", source_role
            )
            break
    if not semantic_qualifier:
        for operator in ("constraint", "continuation", "shift", "action", "wish"):
            if f"operator:{operator}" in attribute_codes:
                semantic_qualifier = catalog_token("source_operator", operator)
                break
    if not semantic_qualifier:
        for block_key in source.source_meaning_block_keys:
            block_kind = str(block_key).rsplit(":", 1)[-1]
            if block_kind in SURFACE_GRAMMAR_CATALOG["meaning_block_kind"]:
                semantic_qualifier = catalog_token(
                    "meaning_block_kind", block_kind
                )
                break
    return "".join(
        part
        for part in (
            catalog_token("source_field", field_key),
            catalog_token("temporal_scope", source.temporal_scope),
            catalog_token("semantic_role", role),
            catalog_token("polarity", source.polarity),
            semantic_qualifier,
            catalog_token("nucleus_kind", source.kind),
        )
        if part
    )


def _referent_phrase(
    obligation: Mapping[str, Any],
    *,
    discourse_node_id: str,
    discourse_plan: Mapping[str, Any],
    snapshot: GroundedSourceSnapshot,
    source_anchor: _SourceAnchor | None,
) -> str:
    nuclei = {row.source_id: row for row in snapshot.nuclei}
    relation_by_id = {row.source_id: row for row in snapshot.relations}
    ordered_ids = list(obligation.get("nucleus_ids") or [])
    relation_ids = list(obligation.get("relation_ids") or [])
    if len(relation_ids) == 1 and relation_ids[0] in relation_by_id:
        relation = relation_by_id[relation_ids[0]]
        ordered_ids = [relation.from_nucleus_id, relation.to_nucleus_id]
    parts = [_nucleus_phrase(nuclei[item]) for item in ordered_ids if item in nuclei]
    if not parts:
        parts = [
            "".join(
                (
                    catalog_token("source_field", "mixed"),
                    catalog_token("temporal_scope", obligation.get("temporal_scope")),
                    catalog_token("referent_scope", obligation.get("referent_scope")),
                )
            )
        ]
    graph_role = _graph_role(discourse_node_id, discourse_plan)
    phrase = "と".join(parts)
    if graph_role:
        phrase = f"{graph_role}{phrase}"
    if source_anchor is not None:
        anchor_catalog = SURFACE_GRAMMAR_CATALOG["source_anchor"]
        phrase = (
            anchor_catalog["open"]
            + source_anchor.text
            + anchor_catalog["close"]
            + anchor_catalog["binding"]
            + phrase
        )
    return phrase


def _render_clause(
    clause: Mapping[str, Any],
    *,
    discourse_plan: Mapping[str, Any],
    obligation: Mapping[str, Any],
    obligation_by_id: Mapping[str, Mapping[str, Any]],
    snapshot: GroundedSourceSnapshot,
    source_anchor: _SourceAnchor | None,
) -> str:
    nodes = clause["nodes"]
    node_types = [row["node_type"] for row in nodes]
    expected_sequence = SURFACE_GRAMMAR_CATALOG[
        "production_node_sequences"
    ][obligation["kind"]]
    semantic_sequence = [item for item in node_types if item != "connector"]
    if semantic_sequence != expected_sequence:
        raise CanonicalSurfaceRenderError("LEXICAL_PRODUCTION_AMBIGUOUS")
    connectors = "".join(
        catalog_token("connector", row["edge_type"])
        for row in nodes
        if row["node_type"] == "connector"
    )
    modality_node = next(row for row in nodes if row["node_type"] == "modality")
    modality = catalog_token("modality", modality_node["modality"])
    referent_node = next(
        row for row in nodes if row["node_type"] == "grounded_referent"
    )
    if referent_node["form"] == "unique_antecedent":
        targets = obligation.get("target_obligation_ids") or []
        if len(targets) != 1 or targets[0] not in obligation_by_id:
            raise CanonicalSurfaceRenderError("LEXICAL_ANTECEDENT_AMBIGUOUS")
        target_kind = obligation_by_id[targets[0]].get("kind")
        referent = catalog_token("antecedent_referent", target_kind)
    else:
        referent = _referent_phrase(
            obligation,
            discourse_node_id=clause["discourse_node_id"],
            discourse_plan=discourse_plan,
            snapshot=snapshot,
            source_anchor=(
                source_anchor
                if source_anchor is not None
                and source_anchor.obligation_id == obligation["obligation_id"]
                else None
            ),
        )
    kind = obligation["kind"]
    if kind in {
        "grounded_nucleus_notice",
        "significance_or_shift",
        "intention_or_next_action",
        "bounded_counterposition",
    }:
        semantic_node = next(
            row for row in nodes if row["node_type"] == "observation_predicate"
        )
        core = referent + catalog_token("predicate", semantic_node["form"])
    elif kind == "grounded_relation_preservation":
        relation_node = next(
            row
            for row in nodes
            if row["node_type"] == "grounded_relation"
        )
        relation_id = relation_node["relation_id"]
        relation = next(
            row for row in snapshot.relations if row.source_id == relation_id
        )
        nuclei = {row.source_id: row for row in snapshot.nuclei}
        source_id = relation.from_nucleus_id
        target_id = relation.to_nucleus_id
        direction = relation_node["direction"]
        if direction == "target_to_source":
            source_id, target_id = target_id, source_id
        if source_id not in nuclei or target_id not in nuclei:
            raise CanonicalSurfaceRenderError("LEXICAL_RELATION_ENDPOINT_UNRESOLVED")
        source_phrase = _nucleus_phrase(nuclei[source_id])
        target_phrase = _nucleus_phrase(nuclei[target_id])
        if (
            source_anchor is not None
            and source_anchor.obligation_id == obligation["obligation_id"]
        ):
            anchor_catalog = SURFACE_GRAMMAR_CATALOG["source_anchor"]
            source_phrase = (
                anchor_catalog["open"]
                + source_anchor.text
                + anchor_catalog["close"]
                + anchor_catalog["binding"]
                + source_phrase
            )
        if direction == "bidirectional":
            core = (
                source_phrase
                + "と"
                + target_phrase
                + "には"
                + catalog_token("relation", relation.relation_type)
            )
        else:
            relation_joiner = SURFACE_GRAMMAR_CATALOG[
                "directed_relation_joiner"
            ].get(relation.relation_type)
            if (
                type(relation_joiner) is not dict
                or type(relation_joiner.get("left")) is not str
                or type(relation_joiner.get("right")) is not str
            ):
                raise CanonicalSurfaceRenderError(
                    "LEXICAL_RELATION_PRODUCTION_UNRESOLVED"
                )
            core = (
                source_phrase
                + relation_joiner["left"]
                + target_phrase
                + relation_joiner["right"]
            )
    elif kind == "unknown_boundary_preservation":
        unknown_node = next(
            row for row in nodes if row["node_type"] == "unknown_boundary"
        )
        dimensions = [
            row.source_dimension
            for row in snapshot.unknowns
            if row.source_id in unknown_node["unknown_boundary_ids"]
        ]
        dimension_groups = tuple(
            dict.fromkeys(
                _dimension_group(item) for item in dimensions
            )
        ) or ("other",)
        dimension = SURFACE_GRAMMAR_CATALOG["unknown_dimension_joiner"].join(
            catalog_token("unknown_dimension", item)
            for item in dimension_groups
        )
        core = dimension + "に関わる" + referent + catalog_token(
            "unknown", unknown_node["form"]
        )
    elif kind == "self_denial_boundary":
        boundary = next(
            row for row in nodes if row["node_type"] == "self_denial_boundary"
        )
        core = referent + catalog_token("self_denial", boundary["form"])
    elif kind == "bound_emlis_reception":
        stance = next(row for row in nodes if row["node_type"] == "emlis_stance")
        core = referent + "を" + catalog_token("stance", stance["form"])
    else:
        raise CanonicalSurfaceRenderError("LEXICAL_UNSUPPORTED_SEMANTIC_SIGNATURE")
    return connectors + modality + core


def render_canonical_surface(
    surface_ast: Mapping[str, Any],
    *,
    discourse_plan: Mapping[str, Any],
    content_plan: Mapping[str, Any],
    inventory_result: SemanticObligationInventoryResult,
    lexical_authority: RequestLexicalAuthority,
) -> CanonicalRenderedSurface:
    """Render NFC/LF UTF-8 bytes with no post-render text mutation hook."""

    origin = _resolve_authority(lexical_authority)
    if (
        validate_surface_grammar_catalog()
        or validate_surface_grammar_catalog(SURFACE_GRAMMAR_CATALOG)
    ):
        raise CanonicalSurfaceRenderError("LEXICAL_CATALOG_DRIFT")
    try:
        replay_snapshot, replay_inventory = origin.rebuild()
    except (AttributeError, KeyError, TypeError, ValueError, UnicodeError):
        raise CanonicalSurfaceRenderError(
            "LEXICAL_AUTHORITY_REVALIDATION_FAILED"
        ) from None
    expected_snapshot_hash = _source_snapshot_authority_sha256(replay_snapshot)
    expected_ledger_hash = artifact_sha256(replay_inventory.ledger)
    expected_authority_id = _lexical_authority_id(
        snapshot_hash=expected_snapshot_hash,
        ledger_hash=expected_ledger_hash,
        observation_stage=replay_snapshot.observation_stage,
    )
    if (
        type(inventory_result) is not SemanticObligationInventoryResult
        or not _inventory_matches(replay_inventory, inventory_result)
        or replay_snapshot != inventory_result.source_snapshot
        or lexical_authority.authority_id != expected_authority_id
        or lexical_authority.source_snapshot_sha256 != expected_snapshot_hash
        or lexical_authority.obligation_ledger_sha256
        != expected_ledger_hash
        or lexical_authority.observation_stage != replay_snapshot.observation_stage
        or lexical_authority.grammar_catalog_sha256
        != FROZEN_SURFACE_GRAMMAR_CATALOG_SHA256
        or lexical_authority.body_free is not True
    ):
        raise CanonicalSurfaceRenderError("LEXICAL_PARENT_CHAIN_MISMATCH")
    ledger = inventory_result.ledger
    if validate_semantic_obligation_inventory(
        ledger, source_snapshot=replay_snapshot
    ) or validate_content_selection_policy(
        content_plan, inventory_result=inventory_result
    ):
        raise CanonicalSurfaceRenderError("LEXICAL_PARENT_CHAIN_MISMATCH")
    if validate_discourse_plan(
        discourse_plan,
        content_plan=content_plan,
        obligation_ledger=ledger,
    ) or discourse_plan not in build_discourse_graph_plans(
        inventory_result, content_plan
    ).plans:
        raise CanonicalSurfaceRenderError("LEXICAL_PARENT_CHAIN_MISMATCH")
    if validate_surface_ast(
        surface_ast,
        discourse_plan=discourse_plan,
        obligation_ledger=ledger,
    ) or validate_typed_surface_ast(
        surface_ast,
        discourse_plan=discourse_plan,
        inventory_result=inventory_result,
        content_plan=content_plan,
    ):
        raise CanonicalSurfaceRenderError("LEXICAL_PARENT_CHAIN_MISMATCH")
    obligation_by_id = {
        row["obligation_id"]: row for row in ledger["obligations"]
    }
    source_anchor = _select_source_anchor(
        ledger=ledger,
        content_plan=content_plan,
        snapshot=replay_snapshot,
        origin=origin,
    )
    section_text: dict[str, list[str]] = {"observation": [], "reception": []}
    same_kind_cores: dict[tuple[str, str], str] = {}
    for section in surface_ast["sections"]:
        for sentence in section["sentences"]:
            clause_texts: list[str] = []
            for clause in sentence["clauses"]:
                obligation = obligation_by_id[clause["obligation_id"]]
                rendered = _render_clause(
                    clause,
                    discourse_plan=discourse_plan,
                    obligation=obligation,
                    obligation_by_id=obligation_by_id,
                    snapshot=replay_snapshot,
                    source_anchor=source_anchor,
                )
                key = (obligation["kind"], rendered)
                previous = same_kind_cores.get(key)
                if previous is not None and previous != obligation["obligation_id"]:
                    raise CanonicalSurfaceRenderError("LEXICAL_REFERENT_AMBIGUOUS")
                same_kind_cores[key] = obligation["obligation_id"]
                clause_texts.append(rendered)
            sentence_text = SURFACE_GRAMMAR_CATALOG["clause_joiner"].join(
                clause_texts
            ) + SURFACE_GRAMMAR_CATALOG["document"]["terminal"]
            section_text[section["role"]].append(sentence_text)
    document = SURFACE_GRAMMAR_CATALOG["document"]
    text = (
        document["observation_label"]
        + "\n"
        + document["sentence_separator"].join(section_text["observation"])
        + document["section_separator"]
        + document["reception_label"]
        + "\n"
        + document["sentence_separator"].join(section_text["reception"])
    )
    text = unicodedata.normalize("NFC", text)
    if (
        text.count(document["observation_label"]) != 1
        or text.count(document["reception_label"]) != 1
    ):
        raise CanonicalSurfaceRenderError("SECTION_LABEL_CONTRACT_VIOLATION")
    if "\r" in text or text.endswith("\n"):
        raise CanonicalSurfaceRenderError("POST_RENDER_MUTATION_FORBIDDEN")
    payload = text.encode("utf-8", errors="strict")
    return CanonicalRenderedSurface(
        utf8_bytes=payload,
        sha256=hashlib.sha256(payload).hexdigest(),
        surface_ast_sha256=artifact_sha256(surface_ast),
        grammar_catalog_sha256=FROZEN_SURFACE_GRAMMAR_CATALOG_SHA256,
        raw_anchor_count=1 if source_anchor is not None else 0,
        anchor_reason_codes=(
            ("INPUT_SPECIFIC_BINDING_REQUIRED",)
            if source_anchor is not None
            else ("SEMANTIC_PHRASE_SAFE_FALLBACK",)
        ),
    )


__all__ = [
    "CanonicalRenderedSurface",
    "CanonicalSurfaceRenderError",
    "RequestLexicalAuthority",
    "open_request_lexical_authority",
    "render_canonical_surface",
]
