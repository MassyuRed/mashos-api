# -*- coding: utf-8 -*-
from __future__ import annotations

"""Lossless, body-free Content Selection for Cocolon EmlisAI NLS v3.

Step 5 accepts the completed Step 4 result as its only semantic authority.
It never accepts a caller-supplied stage, role, unknown-boundary, safety, or
parent-hash declaration.  Every such value is derived from the independently
validated ``GroundedSourceSnapshot`` owned by Step 4.

The current owner has no recoverability witness and no safety-block authority.
Consequently required obligations are selected directly, integration is never
emitted, and ``blocked_by_safety`` is rejected.  Optional meanings remain in
the plan as explicit deferred decisions instead of being silently discarded.
"""

from typing import Any, Final, Iterable, Mapping, Sequence

from emlis_ai_nls_v3_artifact_contract import (
    CONTENT_SCHEMA,
    LEDGER_SCHEMA,
    STANCE_KIND,
    ContractIssue,
    artifact_sha256,
    derive_content_id,
    validate_content_selection_plan,
)
from emlis_ai_semantic_obligation_inventory_v3 import (
    GroundedSourceSnapshot,
    SemanticObligationInventoryResult,
    validate_semantic_obligation_inventory,
)


_NORMAL_STAGE: Final = "normal_observation"
_PRE_QUESTION_STAGE: Final = "pre_question_observation"
_REFINED_STAGE: Final = "refined_observation"
_SEMANTIC_ROLES_BY_STAGE: Final = {
    _NORMAL_STAGE: frozenset({"original_input"}),
    _PRE_QUESTION_STAGE: frozenset({"original_input"}),
    _REFINED_STAGE: frozenset({"original_input", "supplemental_answer"}),
}

_ACTIVE_STATUSES: Final = frozenset({"selected", "integrated_into"})
_KNOWN_STATUSES: Final = frozenset(
    {
        "selected",
        "integrated_into",
        "deferred_by_budget",
        "omitted_redundant",
        "blocked_by_safety",
        "unrealizable",
    }
)
_REQUIRED_REASON_BY_KIND: Final = {
    "grounded_nucleus_notice": "REQUIRED_GROUNDED_NUCLEUS",
    "grounded_relation_preservation": "REQUIRED_GROUNDED_RELATION",
    "unknown_boundary_preservation": "REQUIRED_UNKNOWN_BOUNDARY",
    "significance_or_shift": "REQUIRED_SIGNIFICANCE_OR_SHIFT",
    "intention_or_next_action": "REQUIRED_INTENTION_OR_NEXT_ACTION",
    "self_denial_boundary": "REQUIRED_SELF_DENIAL_BOUNDARY",
    "bounded_counterposition": "REQUIRED_BOUNDED_COUNTERPOSITION",
    STANCE_KIND: "BOUND_RECEPTION_REQUIRED",
}
_OPTIONAL_ACTIVE_REASON: Final = "OPTIONAL_DISTINCT_MEANING"
_SOURCE_UNAVAILABLE_ACTIVE_REASON: Final = (
    "SOURCE_UNAVAILABLE_BINDABLE_OBSERVATION"
)
_OPTIONAL_DEFERRED_REASON: Final = "OPTIONAL_DEFERRED_BY_BUDGET"

_BUDGET_BY_DEPTH: Final = {
    "minimal": {
        "observation_sentence_min": 1,
        "observation_sentence_max": 1,
        "reception_sentence_min": 1,
        "reception_sentence_max": 1,
        "total_sentence_max": 2,
    },
    "focused": {
        "observation_sentence_min": 1,
        "observation_sentence_max": 2,
        "reception_sentence_min": 1,
        "reception_sentence_max": 2,
        "total_sentence_max": 4,
    },
    "layered": {
        "observation_sentence_min": 2,
        "observation_sentence_max": 3,
        "reception_sentence_min": 1,
        "reception_sentence_max": 2,
        "total_sentence_max": 5,
    },
}
_DEPTH_RANK: Final = {"minimal": 0, "focused": 1, "layered": 2}
_CROSS_ROLE_DEPTH_EFFECT: Final = "CONTENT_DEPTH_ONLY"

_LABEL_SOURCE_FIELDS: Final = frozenset(
    {"category", "emotions", "emotion_details"}
)


class ContentSelectionBuildError(ValueError):
    """Fail-closed build error containing stable codes and no source body."""

    def __init__(
        self,
        code: str,
        *,
        contract_issue_codes: tuple[str, ...] = (),
    ) -> None:
        self.code = code
        self.contract_issue_codes = contract_issue_codes
        detail = (
            f"{code}:{','.join(contract_issue_codes)}"
            if contract_issue_codes
            else code
        )
        super().__init__(detail)


def _add(issues: list[ContractIssue], code: str, path: str) -> None:
    issue = ContractIssue(code, path)
    if issue not in issues:
        issues.append(issue)


def _final(issues: Iterable[ContractIssue]) -> tuple[ContractIssue, ...]:
    return tuple(sorted(set(issues)))


def _string_tuple(value: Any) -> tuple[str, ...]:
    if type(value) is not list:
        return ()
    return tuple(item for item in value if type(item) is str)


def _rows(
    obligation_ledger: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]] | None:
    if type(obligation_ledger) is not dict:
        return None
    value = obligation_ledger.get("obligations")
    if type(value) is not list or not value:
        return None
    rows: list[dict[str, Any]] = []
    by_id: dict[str, dict[str, Any]] = {}
    for row in value:
        if type(row) is not dict:
            return None
        obligation_id = row.get("obligation_id")
        if type(obligation_id) is not str or obligation_id in by_id:
            return None
        rows.append(row)
        by_id[obligation_id] = row
    return rows, by_id


def _obligation_source_roles(row: Mapping[str, Any]) -> frozenset[str]:
    refs = row.get("source_refs")
    if type(refs) is not list:
        return frozenset()
    return frozenset(
        ref.get("source_role")
        for ref in refs
        if type(ref) is dict and type(ref.get("source_role")) is str
    )


def _validated_inventory(
    inventory_result: Any,
    issues: list[ContractIssue],
) -> tuple[
    Mapping[str, Any],
    GroundedSourceSnapshot,
    list[dict[str, Any]],
    dict[str, dict[str, Any]],
] | None:
    """Revalidate Step 4 before trusting a single Step 5 parent field."""

    if type(inventory_result) is not SemanticObligationInventoryResult:
        _add(issues, "SEMANTIC_INVENTORY_RESULT_TYPE_INVALID", "$.inventory_result")
        return None
    ledger = inventory_result.ledger
    snapshot = inventory_result.source_snapshot
    if type(snapshot) is not GroundedSourceSnapshot or type(ledger) is not dict:
        _add(issues, "SEMANTIC_INVENTORY_PARENT_INVALID", "$.inventory_result")
        return None
    parsed = _rows(ledger)
    if parsed is None or ledger.get("schema_version") != LEDGER_SCHEMA:
        _add(
            issues,
            "SEMANTIC_INVENTORY_PARENT_INVALID",
            "$.source_obligation_ledger_sha256",
        )
        return None

    try:
        step4_issues = validate_semantic_obligation_inventory(
            ledger,
            source_snapshot=snapshot,
        )
    except (AttributeError, KeyError, TypeError, ValueError, RecursionError):
        step4_issues = ("MALFORMED_SEMANTIC_INVENTORY_PARENT",)
    if step4_issues:
        _add(
            issues,
            "SEMANTIC_INVENTORY_REVALIDATION_FAILED",
            "$.source_obligation_ledger_sha256",
        )
        return None

    if (
        type(inventory_result.resource_counts) is not dict
        or inventory_result.resource_counts != dict(snapshot.resource_counts)
        or type(inventory_result.inventory_upper_bound) is not int
        or inventory_result.inventory_upper_bound
        != snapshot.obligation_inventory_upper_bound
    ):
        _add(
            issues,
            "SEMANTIC_INVENTORY_RESULT_METADATA_MISMATCH",
            "$.inventory_result",
        )
        return None

    # These commitments are derived from the snapshot.  Checking them again
    # here keeps a re-hashed, shrunk, or re-parented ledger from becoming a
    # valid Step 5 parent even if its own child hash is recomputed.
    lineage_fields = (
        "source_observation_plan_sha256",
        "source_observation_stage_context_sha256",
        "source_reception_opportunity_plan_sha256",
        "response_eligibility_source_sha256",
        "response_eligibility",
        "source_policy_sha256",
    )
    if any(ledger.get(name) != getattr(snapshot, name) for name in lineage_fields):
        _add(
            issues,
            "SEMANTIC_INVENTORY_LINEAGE_MISMATCH",
            "$.source_obligation_ledger_sha256",
        )
        return None

    rows, by_id = parsed
    expected_required = sorted(
        row["obligation_id"] for row in rows if row.get("required") is True
    )
    if ledger.get("required_obligation_ids") != expected_required:
        _add(
            issues,
            "SEMANTIC_INVENTORY_REQUIRED_SET_MISMATCH",
            "$.source_obligation_ledger_sha256",
        )
        return None
    return ledger, snapshot, rows, by_id


def _semantic_restatement_relations(
    snapshot: GroundedSourceSnapshot,
) -> tuple[set[str], tuple[tuple[str, ...], ...]]:
    relation_ids: set[str] = set()
    units: list[tuple[str, ...]] = []
    for relation in snapshot.relations:
        endpoint_semantic_relation = getattr(
            relation,
            "endpoint_semantic_relation",
            "distinct_meanings",
        )
        if endpoint_semantic_relation == "semantic_restatement":
            relation_ids.add(relation.source_id)
            witnessed_unit = tuple(
                getattr(
                    relation,
                    "semantic_restatement_unit_nucleus_ids",
                    (),
                )
            )
            units.append(
                witnessed_unit
                or (relation.from_nucleus_id, relation.to_nucleus_id)
            )
    return relation_ids, tuple(sorted(units))


def _semantic_root_map(
    snapshot: GroundedSourceSnapshot,
) -> tuple[dict[str, str], set[str]]:
    """Collapse only upstream-proven semantic-restatement endpoints."""

    nucleus_ids = {row.source_id for row in snapshot.nuclei}
    parent = {source_id: source_id for source_id in nucleus_ids}

    def find(source_id: str) -> str:
        root = source_id
        while parent[root] != root:
            root = parent[root]
        while parent[source_id] != source_id:
            next_id = parent[source_id]
            parent[source_id] = root
            source_id = next_id
        return root

    relation_ids, units = _semantic_restatement_relations(snapshot)
    for unit in units:
        available = [source_id for source_id in unit if source_id in parent]
        if len(available) < 2:
            continue
        first = available[0]
        for source_id in available[1:]:
            left_root, right_root = find(first), find(source_id)
            if left_root != right_root:
                keep, merge = sorted((left_root, right_root))
                parent[merge] = keep

    return {source_id: find(source_id) for source_id in parent}, relation_ids


def _depth_from_body_free_rows(
    active_rows: Sequence[dict[str, Any]],
    snapshot: GroundedSourceSnapshot,
) -> str:
    """Derive depth from body-free semantic structure, never text metadata."""

    nonstance = [row for row in active_rows if row.get("kind") != STANCE_KIND]
    if not nonstance:
        return "minimal"

    root_by_nucleus, replay_relation_ids = _semantic_root_map(snapshot)
    root_member_count: dict[str, int] = {}
    for root in root_by_nucleus.values():
        root_member_count[root] = root_member_count.get(root, 0) + 1
    nonstance_ids = {
        row.get("obligation_id")
        for row in nonstance
        if type(row.get("obligation_id")) is str
    }
    semantic_units: set[tuple[Any, ...]] = set()
    topic_ids: set[str] = set()
    kinds: set[Any] = set()
    has_relation = False
    has_unknown = False
    has_shift = False
    has_active_must_not_merge = False

    for row in nonstance:
        kind = row.get("kind")
        relation_ids = set(_string_tuple(row.get("relation_ids")))
        is_restatement_relation = (
            kind == "grounded_relation_preservation"
            and bool(relation_ids & replay_relation_ids)
        )
        if is_restatement_relation:
            # Preserve/select the relation, but the typed upstream witness says
            # that its endpoints contribute one meaning rather than two.
            continue
        nuclei = tuple(
            sorted(
                {
                    root_by_nucleus.get(source_id, source_id)
                    for source_id in _string_tuple(row.get("nucleus_ids"))
                }
            )
        )
        replay_roots = {
            root_by_nucleus.get(source_id, source_id)
            for source_id in _string_tuple(row.get("nucleus_ids"))
            if root_member_count.get(
                root_by_nucleus.get(source_id, source_id), 0
            )
            > 1
        }
        unknowns = tuple(sorted(_string_tuple(row.get("unknown_boundary_ids"))))
        relations = tuple(sorted(relation_ids))
        replay_collapsible = bool(replay_roots) and kind in {
            "grounded_nucleus_notice",
            "significance_or_shift",
            "intention_or_next_action",
            "self_denial_boundary",
        }
        if replay_collapsible:
            semantic_units.add(("semantic_restatement", tuple(sorted(replay_roots))))
        else:
            semantic_units.add((kind, nuclei, relations, unknowns))
        if replay_roots:
            # Topic fingerprints are normally source-local.  Two endpoint
            # fingerprints must not re-expand a typed semantic restatement
            # into two topics after the endpoint union above.
            topic_ids.update(f"semantic_replay:{root}" for root in replay_roots)
        else:
            topic_ids.update(_string_tuple(row.get("topic_scope_ids")))
        if not replay_collapsible:
            kinds.add(kind)
        has_relation = has_relation or kind == "grounded_relation_preservation" or bool(relations)
        has_unknown = has_unknown or kind == "unknown_boundary_preservation" or bool(unknowns)
        has_shift = has_shift or (
            kind == "significance_or_shift" and not replay_collapsible
        )
        has_active_must_not_merge = has_active_must_not_merge or bool(
            set(_string_tuple(row.get("must_not_merge_with"))) & nonstance_ids
        )

    nonstance_by_id = {
        row.get("obligation_id"): row
        for row in nonstance
        if type(row.get("obligation_id")) is str
    }

    def normalized_stance_target(target_id: str) -> tuple[Any, ...]:
        target = nonstance_by_id.get(target_id)
        if target is None:
            return ("obligation", target_id)
        roots = tuple(
            sorted(
                {
                    root_by_nucleus.get(source_id, source_id)
                    for source_id in _string_tuple(target.get("nucleus_ids"))
                }
            )
        )
        if roots and any(root_member_count.get(root, 0) > 1 for root in roots):
            return ("semantic_restatement", roots)
        return ("obligation", target_id)

    stance_units = {
        (
            tuple(
                sorted(
                    normalized_stance_target(target_id)
                    for target_id in _string_tuple(
                        row.get("target_obligation_ids")
                    )
                )
            ),
            tuple(sorted(_string_tuple(row.get("allowed_response_acts")))),
        )
        for row in active_rows
        if row.get("kind") == STANCE_KIND
    }
    self_denial_and_action = {
        "self_denial_boundary",
        "intention_or_next_action",
    } <= kinds
    unit_count = len(semantic_units)

    active_nucleus_ids = {
        source_id
        for row in nonstance
        for source_id in _string_tuple(row.get("nucleus_ids"))
    }
    active_sources = [
        row for row in snapshot.nuclei if row.source_id in active_nucleus_ids
    ]
    active_semantic_roots = {
        root_by_nucleus.get(source_id, source_id)
        for source_id in active_nucleus_ids
    }
    active_relation_ids = {
        source_id
        for row in nonstance
        for source_id in _string_tuple(row.get("relation_ids"))
        if source_id not in replay_relation_ids
    }
    active_polarities = {
        source.polarity for source in active_sources if source.polarity != "neutral"
    }
    has_mixed_source = "mixed" in active_polarities
    has_positive_and_negative = {"positive", "negative"} <= active_polarities
    has_positive_change = any(
        source.kind == "change" and source.polarity == "positive"
        for source in active_sources
    )
    has_negative_action = any(
        source.kind == "action" and source.polarity == "negative"
        for source in active_sources
    )
    replay_collapsed_to_one = (
        len(active_semantic_roots) == 1
        and any(
            root_member_count.get(root, 0) > 1
            for root in active_semantic_roots
        )
        and not active_relation_ids
        and not has_unknown
    )
    label_only_sources = bool(active_sources) and all(
        source.allowed_claim_scope == "selected_label_only"
        for source in active_sources
    )

    # ``layered`` is reserved for independently visible separation pressure,
    # not merely two source-local topic fingerprints.  This keeps an ordinary
    # thought/action pair focused while preserving long-arc, polarity-conflict,
    # unknown, safety, and multi-relation structures.
    if (
        has_active_must_not_merge
        or self_denial_and_action
        or len(active_semantic_roots) >= 4
        or len(topic_ids) >= 4
        or len(active_relation_ids) >= 3
        or len(stance_units) >= 2
        # Multiple unknown rows about the same source root/arc do not create
        # independent layers.  They remain explicit obligations, while depth
        # is driven by distinct semantic roots, relations, and separation
        # pressure below.  This prevents a source-explicit cause+referent
        # uncertainty from being inflated merely because it has two typed
        # boundary dimensions.
        or (
            len(active_semantic_roots) >= 3
            and has_mixed_source
        )
        or (
            len(active_semantic_roots) >= 3
            and len(active_relation_ids) >= 2
            and has_positive_and_negative
        )
        or (
            len(active_semantic_roots) >= 3
            and has_positive_change
            and has_negative_action
        )
    ):
        return "layered"
    if replay_collapsed_to_one or label_only_sources:
        return "minimal"
    if unit_count == 1 and kinds == {"intention_or_next_action"}:
        return "minimal"
    if unit_count or has_relation or has_unknown or has_shift:
        return "focused"
    return "minimal"


def _cross_role_depth_rows(
    active_rows: Sequence[dict[str, Any]],
    snapshot: GroundedSourceSnapshot,
) -> tuple[dict[str, Any], ...]:
    """Remove only depth-duplicate supplemental rows proved by Step 4."""

    equivalence = getattr(
        snapshot,
        "cross_role_semantic_depth_equivalence",
        None,
    )
    if (
        equivalence is None
        or equivalence.effect_scope != _CROSS_ROLE_DEPTH_EFFECT
    ):
        return tuple(active_rows)
    bound_supplemental = {
        "nucleus": {
            row.supplemental_source_id
            for row in equivalence.component_bindings
            if row.component_kind == "nucleus"
        },
        "relation": {
            row.supplemental_source_id
            for row in equivalence.component_bindings
            if row.component_kind == "relation"
        },
        "unknown_boundary": {
            row.supplemental_source_id
            for row in equivalence.component_bindings
            if row.component_kind == "unknown_boundary"
        },
    }

    def contributes_distinct_depth(row: Mapping[str, Any]) -> bool:
        if row.get("kind") == STANCE_KIND:
            return True
        if _obligation_source_roles(row) != frozenset(
            {"supplemental_answer"}
        ):
            return True
        refs = row.get("source_refs")
        if type(refs) is not list:
            return True
        saw_component = False
        for ref in refs:
            if (
                type(ref) is not dict
                or ref.get("source_role") != "supplemental_answer"
            ):
                continue
            for field, component_kind in (
                ("nucleus_ids", "nucleus"),
                ("relation_ids", "relation"),
                ("unknown_boundary_ids", "unknown_boundary"),
            ):
                source_ids = _string_tuple(ref.get(field))
                saw_component = saw_component or bool(source_ids)
                if not set(source_ids) <= bound_supplemental[
                    component_kind
                ]:
                    return True
        return not saw_component

    return tuple(
        row for row in active_rows if contributes_distinct_depth(row)
    )


def _depth_from_active_rows(
    active_rows: Sequence[dict[str, Any]],
    snapshot: GroundedSourceSnapshot,
) -> str:
    """Apply cross-role equivalence to depth, never to content decisions."""

    depth_rows = _cross_role_depth_rows(active_rows, snapshot)
    depth = _depth_from_body_free_rows(depth_rows, snapshot)
    equivalence = getattr(
        snapshot,
        "cross_role_semantic_depth_equivalence",
        None,
    )
    if (
        equivalence is None
        or equivalence.effect_scope != _CROSS_ROLE_DEPTH_EFFECT
    ):
        return depth
    original_floor_rows = tuple(
        row
        for row in active_rows
        if row.get("kind") == STANCE_KIND
        or _obligation_source_roles(row) == frozenset({"original_input"})
    )
    original_floor = _depth_from_body_free_rows(
        original_floor_rows,
        snapshot,
    )
    return max((depth, original_floor), key=_DEPTH_RANK.__getitem__)


def derive_content_depth(
    inventory_result: SemanticObligationInventoryResult,
    *,
    active_obligation_ids: Iterable[str],
) -> str:
    """Derive depth from the validated Step 4 body-free semantic structure."""

    issues: list[ContractIssue] = []
    trusted = _validated_inventory(inventory_result, issues)
    if trusted is None or issues:
        raise ContentSelectionBuildError(
            "NLS3_CONTENT_SELECTION_PARENT_INVALID",
            contract_issue_codes=tuple(sorted({item.code for item in issues})),
        )
    _, snapshot, _, by_id = trusted
    try:
        active_ids = tuple(active_obligation_ids)
    except TypeError as exc:
        raise ContentSelectionBuildError(
            "NLS3_CONTENT_SELECTION_ACTIVE_SET_INVALID"
        ) from exc
    if (
        not active_ids
        or any(type(item) is not str for item in active_ids)
        or len(active_ids) != len(set(active_ids))
        or not set(active_ids) <= set(by_id)
    ):
        raise ContentSelectionBuildError(
            "NLS3_CONTENT_SELECTION_ACTIVE_SET_INVALID"
        )
    return _depth_from_active_rows([by_id[item] for item in active_ids], snapshot)


def _required_stance_target_closure(
    rows: Sequence[dict[str, Any]],
) -> frozenset[str]:
    return frozenset(
        target_id
        for row in rows
        if row.get("required") is True and row.get("kind") == STANCE_KIND
        for target_id in _string_tuple(row.get("target_obligation_ids"))
    )


def _cross_role_unmatched_obligation_ids(
    rows: Sequence[dict[str, Any]],
    snapshot: GroundedSourceSnapshot,
) -> frozenset[str]:
    """Keep every unbound role-local component independently selectable."""

    equivalence = getattr(
        snapshot,
        "cross_role_semantic_depth_equivalence",
        None,
    )
    if (
        equivalence is None
        or equivalence.effect_scope != _CROSS_ROLE_DEPTH_EFFECT
    ):
        return frozenset()
    bound = {
        ("original_input", "nucleus"): {
            row.original_source_id
            for row in equivalence.component_bindings
            if row.component_kind == "nucleus"
        },
        ("supplemental_answer", "nucleus"): {
            row.supplemental_source_id
            for row in equivalence.component_bindings
            if row.component_kind == "nucleus"
        },
        ("original_input", "relation"): {
            row.original_source_id
            for row in equivalence.component_bindings
            if row.component_kind == "relation"
        },
        ("supplemental_answer", "relation"): {
            row.supplemental_source_id
            for row in equivalence.component_bindings
            if row.component_kind == "relation"
        },
        ("original_input", "unknown_boundary"): {
            row.original_source_id
            for row in equivalence.component_bindings
            if row.component_kind == "unknown_boundary"
        },
        ("supplemental_answer", "unknown_boundary"): {
            row.supplemental_source_id
            for row in equivalence.component_bindings
            if row.component_kind == "unknown_boundary"
        },
    }
    all_components = {
        ("original_input", "nucleus"): {
            row.source_id
            for row in snapshot.nuclei
            if row.source_role == "original_input"
        },
        ("supplemental_answer", "nucleus"): {
            row.source_id
            for row in snapshot.nuclei
            if row.source_role == "supplemental_answer"
        },
        ("original_input", "relation"): {
            row.source_id
            for row in snapshot.relations
            if row.source_role == "original_input"
        },
        ("supplemental_answer", "relation"): {
            row.source_id
            for row in snapshot.relations
            if row.source_role == "supplemental_answer"
        },
        ("original_input", "unknown_boundary"): {
            row.source_id
            for row in snapshot.unknowns
            if row.source_role == "original_input"
        },
        ("supplemental_answer", "unknown_boundary"): {
            row.source_id
            for row in snapshot.unknowns
            if row.source_role == "supplemental_answer"
        },
    }
    unmatched = {
        key: all_components[key] - bound[key]
        for key in all_components
    }
    selected: set[str] = set()
    for row in rows:
        refs = row.get("source_refs")
        if type(refs) is not list:
            continue
        for ref in refs:
            if type(ref) is not dict:
                continue
            source_role = ref.get("source_role")
            if source_role not in {
                "original_input",
                "supplemental_answer",
            }:
                continue
            if any(
                set(_string_tuple(ref.get(field)))
                & unmatched[(source_role, component_kind)]
                for field, component_kind in (
                    ("nucleus_ids", "nucleus"),
                    ("relation_ids", "relation"),
                    (
                        "unknown_boundary_ids",
                        "unknown_boundary",
                    ),
                )
            ):
                obligation_id = row.get("obligation_id")
                if type(obligation_id) is str:
                    selected.add(obligation_id)
                break
    return frozenset(selected)


def _nucleus_by_id(snapshot: GroundedSourceSnapshot) -> dict[str, Any]:
    return {row.source_id: row for row in snapshot.nuclei}


def _source_unavailable_nucleus_permitted(source: Any) -> bool:
    return (
        source.allowed_claim_scope == "selected_label_only"
        and bool(source.source_fields)
        and set(source.source_fields) <= _LABEL_SOURCE_FIELDS
    ) or (
        source.source_modality == "uncertain"
        and source.source_predicate_kind in {"state", "uncertainty"}
        and "operator:uncertainty" in source.source_attribute_codes
    )


def _source_unavailable_row_permitted(
    row: Mapping[str, Any],
    snapshot: GroundedSourceSnapshot,
) -> bool:
    """Allow only typed labels, explicit absence, or unknown boundaries.

    Explicit uncertainty is recognized only through the upstream typed frame;
    it is never inferred from source wording here.
    """

    if row.get("kind") == "unknown_boundary_preservation":
        return True
    nucleus_ids = _string_tuple(row.get("nucleus_ids"))
    if not nucleus_ids:
        return False
    nuclei = _nucleus_by_id(snapshot)
    sources = [nuclei.get(source_id) for source_id in nucleus_ids]
    if any(source is None for source in sources):
        return False
    return all(_source_unavailable_nucleus_permitted(source) for source in sources)


def _source_unavailable_active_row_permitted(
    row: Mapping[str, Any],
    *,
    ledger_by_id: Mapping[str, dict[str, Any]],
    snapshot: GroundedSourceSnapshot,
) -> bool:
    if row.get("kind") != STANCE_KIND:
        return _source_unavailable_row_permitted(row, snapshot)
    target_ids = _string_tuple(row.get("target_obligation_ids"))
    targets = [ledger_by_id.get(target_id) for target_id in target_ids]
    if not target_ids or any(target is None for target in targets):
        return False
    if not all(
        _source_unavailable_row_permitted(target, snapshot)
        for target in targets
        if target is not None
    ):
        return False
    target_nucleus_ids = {
        source_id
        for target in targets
        if target is not None
        for source_id in _string_tuple(target.get("nucleus_ids"))
    }
    if not set(_string_tuple(row.get("nucleus_ids"))) <= target_nucleus_ids:
        return False
    nuclei = _nucleus_by_id(snapshot)
    opportunity_by_id = {
        opportunity.source_id: opportunity
        for opportunity in snapshot.reception_opportunities
    }
    for opportunity_id in _string_tuple(row.get("reception_opportunity_ids")):
        opportunity = opportunity_by_id.get(opportunity_id)
        if opportunity is None:
            return False
        bound_source_ids = {
            *opportunity.target_nucleus_ids,
            *opportunity.support_nucleus_ids,
        }
        if any(
            source_id not in nuclei
            or not _source_unavailable_nucleus_permitted(nuclei[source_id])
            for source_id in bound_source_ids
        ):
            return False
    return True


def _expected_decision(
    row: Mapping[str, Any],
    *,
    forced_active_ids: frozenset[str],
    response_eligibility: str,
) -> tuple[str, str]:
    kind = row.get("kind")
    obligation_id = row.get("obligation_id")
    if row.get("required") is True:
        reason = _REQUIRED_REASON_BY_KIND.get(kind)
        if reason is None:
            raise ContentSelectionBuildError(
                "NLS3_CONTENT_SELECTION_REQUIRED_KIND_INVALID"
            )
        return "selected", reason
    if obligation_id in forced_active_ids:
        reason = (
            _SOURCE_UNAVAILABLE_ACTIVE_REASON
            if response_eligibility == "source_unavailable"
            else _OPTIONAL_ACTIVE_REASON
        )
        return "selected", reason
    return "deferred_by_budget", _OPTIONAL_DEFERRED_REASON


def validate_content_selection_policy(
    value: Any,
    *,
    inventory_result: SemanticObligationInventoryResult,
) -> tuple[ContractIssue, ...]:
    """Validate Step 5 against a revalidated Step 4 result and snapshot."""

    issues: list[ContractIssue] = []
    try:
        trusted = _validated_inventory(inventory_result, issues)
        if trusted is None:
            return _final(issues)
        ledger, snapshot, ledger_rows, ledger_by_id = trusted
        issues.extend(
            validate_content_selection_plan(value, obligation_ledger=ledger)
        )
        if type(value) is not dict:
            _add(issues, "CONTENT_SELECTION_PLAN_INVALID", "$")
            return _final(issues)

        expected_roles = _SEMANTIC_ROLES_BY_STAGE.get(snapshot.observation_stage)
        if expected_roles is None:
            _add(issues, "CONTENT_SELECTION_STAGE_INVALID", "$.inventory_result")
            return _final(issues)
        if frozenset(snapshot.semantic_source_roles) != expected_roles:
            _add(
                issues,
                "CONTENT_SELECTION_SOURCE_ROLES_MISMATCH",
                "$.inventory_result",
            )
        for index, row in enumerate(ledger_rows):
            roles = _obligation_source_roles(row)
            if not roles or not roles <= expected_roles:
                _add(
                    issues,
                    "STAGE_SEMANTIC_SOURCE_ROLE_FORBIDDEN",
                    f"$.inventory_result.ledger.obligations[{index}].source_refs",
                )

        decisions_value = value.get("decisions")
        decisions = (
            [row for row in decisions_value if type(row) is dict]
            if type(decisions_value) is list
            else []
        )
        decision_by_id = {
            row.get("obligation_id"): row
            for row in decisions
            if type(row.get("obligation_id")) is str
        }
        forced_active_ids = _required_stance_target_closure(ledger_rows)
        if not forced_active_ids <= set(ledger_by_id):
            _add(issues, "STANCE_TARGET_UNRESOLVED", "$.decisions")
        for index, decision in enumerate(decisions):
            path = f"$.decisions[{index}]"
            obligation_id = decision.get("obligation_id")
            row = ledger_by_id.get(obligation_id)
            if row is None:
                continue
            status = decision.get("status")
            reason = decision.get("reason_code")
            if status not in _KNOWN_STATUSES:
                _add(issues, "CONTENT_SELECTION_STATUS_INVALID", f"{path}.status")
                continue
            if status == "integrated_into":
                _add(
                    issues,
                    "INTEGRATION_WITNESS_AUTHORITY_REQUIRED",
                    f"{path}.status",
                )
            if status == "blocked_by_safety":
                _add(issues, "UNAUTHORIZED_SAFETY_BLOCK", f"{path}.status")
            if status == "unrealizable":
                _add(
                    issues,
                    "UNREALIZABLE_AUTHORITY_REQUIRED",
                    f"{path}.status",
                )
            expected_status, expected_reason = _expected_decision(
                row,
                forced_active_ids=forced_active_ids,
                response_eligibility=snapshot.response_eligibility,
            )
            if status != expected_status:
                _add(issues, "CONTENT_SELECTION_STATUS_MISMATCH", f"{path}.status")
            if reason != expected_reason:
                _add(
                    issues,
                    "CONTENT_SELECTION_REASON_MISMATCH",
                    f"{path}.reason_code",
                )

        required_ids = {
            row["obligation_id"]
            for row in ledger_rows
            if row.get("required") is True
        }
        directly_selected_required = {
            obligation_id
            for obligation_id in required_ids
            if decision_by_id.get(obligation_id, {}).get("status") == "selected"
        }
        if directly_selected_required != required_ids:
            _add(
                issues,
                "REQUIRED_COVERAGE_NOT_100_PERCENT",
                "$.required_coverage_obligation_ids",
            )

        active_ids = {
            obligation_id
            for obligation_id, decision in decision_by_id.items()
            if obligation_id in ledger_by_id
            and decision.get("status") in _ACTIVE_STATUSES
        }
        active_rows = [
            row for row in ledger_rows if row["obligation_id"] in active_ids
        ]
        active_nonstance = [
            row for row in active_rows if row.get("kind") != STANCE_KIND
        ]
        if not active_nonstance:
            _add(issues, "OBSERVATION_OBLIGATION_REQUIRED", "$.decisions")

        if snapshot.observation_stage == _PRE_QUESTION_STAGE:
            source_unknown_ids = {row.source_id for row in snapshot.unknowns}
            if snapshot.answered_unknown_boundary_ids:
                _add(
                    issues,
                    "ANSWERED_UNKNOWN_FORBIDDEN_FOR_STAGE",
                    "$.inventory_result.source_snapshot",
                )
            if (
                source_unknown_ids
                and set(snapshot.preserved_unknown_boundary_ids)
                != source_unknown_ids
            ):
                _add(
                    issues,
                    "PRE_QUESTION_ALL_UNKNOWNS_MUST_BE_PRESERVED",
                    "$.inventory_result.source_snapshot",
                )
            active_unknown_ids = {
                source_id
                for row in active_nonstance
                if row.get("kind") == "unknown_boundary_preservation"
                for source_id in _string_tuple(row.get("unknown_boundary_ids"))
            }
            if not source_unknown_ids <= active_unknown_ids:
                _add(issues, "PRESERVED_UNKNOWN_NOT_ACTIVE", "$.decisions")
        elif snapshot.observation_stage == _NORMAL_STAGE and (
            snapshot.preserved_unknown_boundary_ids
            or snapshot.answered_unknown_boundary_ids
        ):
            _add(
                issues,
                "FUTURE_UNKNOWN_AUTHORITY_FORBIDDEN_FOR_NORMAL_STAGE",
                "$.inventory_result.source_snapshot",
            )
        elif snapshot.observation_stage == _REFINED_STAGE:
            active_roles = set().union(
                *(
                    set(_obligation_source_roles(row))
                    for row in active_nonstance
                ),
                set(),
            )
            if not {"original_input", "supplemental_answer"} <= active_roles:
                _add(
                    issues,
                    "REFINED_SOURCE_ROLES_MUST_BOTH_REMAIN_ACTIVE",
                    "$.decisions",
                )

        if snapshot.response_eligibility == "separate_safety_owner":
            _add(
                issues,
                "SEPARATE_SAFETY_OWNER_NOT_CONTENT_SELECTABLE",
                "$.source_obligation_ledger_sha256",
            )
        if snapshot.response_eligibility in {
            "normal_surface",
            "source_unavailable",
        } and not any(row.get("kind") == STANCE_KIND for row in active_rows):
            _add(issues, "ACTIVE_BOUND_RECEPTION_REQUIRED", "$.decisions")

        if snapshot.response_eligibility == "source_unavailable":
            for row in active_rows:
                if not _source_unavailable_active_row_permitted(
                    row,
                    ledger_by_id=ledger_by_id,
                    snapshot=snapshot,
                ):
                    _add(
                        issues,
                        "SOURCE_UNAVAILABLE_SOURCE_SCOPE_FORBIDDEN",
                        "$.decisions",
                    )
                    break
            stance_targets = {
                target_id
                for row in active_rows
                if row.get("kind") == STANCE_KIND
                for target_id in _string_tuple(row.get("target_obligation_ids"))
            }
            if not stance_targets or not stance_targets <= active_ids:
                _add(
                    issues,
                    "SOURCE_UNAVAILABLE_BOUND_TARGET_REQUIRED",
                    "$.decisions",
                )

        expected_depth = _depth_from_active_rows(active_rows, snapshot)
        if value.get("depth") != expected_depth:
            _add(issues, "CONTENT_DEPTH_MISMATCH", "$.depth")
        if value.get("section_budget") != _BUDGET_BY_DEPTH[expected_depth]:
            _add(issues, "CONTENT_DEPTH_BUDGET_MISMATCH", "$.section_budget")
    except (AttributeError, KeyError, TypeError, ValueError, UnicodeError, RecursionError):
        _add(issues, "MALFORMED_CONTENT_SELECTION_POLICY_INPUT", "$")
    return _final(issues)


def build_content_selection_plan(
    inventory_result: SemanticObligationInventoryResult,
) -> dict[str, Any]:
    """Build Step 5 strictly from a revalidated Step 4 result."""

    parent_issues: list[ContractIssue] = []
    trusted = _validated_inventory(inventory_result, parent_issues)
    if trusted is None or parent_issues:
        raise ContentSelectionBuildError(
            "NLS3_CONTENT_SELECTION_PARENT_INVALID",
            contract_issue_codes=tuple(
                sorted({item.code for item in parent_issues})
            ),
        )
    ledger, snapshot, ledger_rows, ledger_by_id = trusted
    if snapshot.response_eligibility == "separate_safety_owner":
        raise ContentSelectionBuildError(
            "NLS3_CONTENT_SELECTION_SEPARATE_SAFETY_OWNER"
        )

    forced_active_ids = _required_stance_target_closure(ledger_rows)
    if not forced_active_ids <= set(ledger_by_id):
        raise ContentSelectionBuildError(
            "NLS3_CONTENT_SELECTION_STANCE_TARGET_INVALID"
        )
    decisions: list[dict[str, Any]] = []
    for row in ledger_rows:
        status, reason = _expected_decision(
            row,
            forced_active_ids=forced_active_ids,
            response_eligibility=snapshot.response_eligibility,
        )
        decisions.append(
            {
                "obligation_id": row["obligation_id"],
                "status": status,
                "reason_code": reason,
                "integrated_into_obligation_id": None,
            }
        )

    active_ids = [
        row["obligation_id"]
        for row in decisions
        if row["status"] in _ACTIVE_STATUSES
    ]
    depth = _depth_from_active_rows(
        [ledger_by_id[obligation_id] for obligation_id in active_ids],
        snapshot,
    )
    required_ids = ledger.get("required_obligation_ids")
    if type(required_ids) is not list:
        raise ContentSelectionBuildError(
            "NLS3_CONTENT_SELECTION_PARENT_INVALID"
        )
    try:
        source_ledger_sha256 = artifact_sha256(ledger)
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise ContentSelectionBuildError(
            "NLS3_CONTENT_SELECTION_PARENT_INVALID"
        ) from exc

    plan: dict[str, Any] = {
        "schema_version": CONTENT_SCHEMA,
        "content_plan_id": "nls3cp_0000000000000000",
        "source_obligation_ledger_sha256": source_ledger_sha256,
        "depth": depth,
        "section_budget": dict(_BUDGET_BY_DEPTH[depth]),
        "decisions": decisions,
        "required_coverage_obligation_ids": list(required_ids),
        "body_free": True,
    }
    try:
        plan["content_plan_id"] = derive_content_id(
            "nls3cp_",
            plan,
            "content_plan_id",
        )
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise ContentSelectionBuildError(
            "NLS3_CONTENT_SELECTION_PARENT_INVALID"
        ) from exc

    issues = validate_content_selection_policy(
        plan,
        inventory_result=inventory_result,
    )
    if issues:
        raise ContentSelectionBuildError(
            "NLS3_CONTENT_SELECTION_CONTRACT_REJECTED",
            contract_issue_codes=tuple(
                sorted({issue.code for issue in issues})
            ),
        )
    return plan


__all__ = [
    "ContentSelectionBuildError",
    "build_content_selection_plan",
    "derive_content_depth",
    "validate_content_selection_policy",
]
