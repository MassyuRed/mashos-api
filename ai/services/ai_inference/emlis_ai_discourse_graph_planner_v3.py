# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step 6 body-free discourse graph planner for NLS v3.

The planner consumes only the revalidated Step 4 ledger and Step 5 content
plan.  It plans obligation order, rhetorical dependencies and sentence
partitioning; it never chooses words, punctuation, greetings or endings.
"""

from dataclasses import dataclass
from itertools import combinations, product
from typing import Any, Iterable, Mapping, Sequence

from emlis_ai_content_selection_v3 import validate_content_selection_policy
from emlis_ai_nls_v3_artifact_contract import (
    DISCOURSE_SCHEMA,
    STANCE_KIND,
    artifact_sha256,
    derive_content_id,
    validate_discourse_plan,
)
from emlis_ai_semantic_obligation_inventory_v3 import (
    SemanticObligationInventoryResult,
    validate_semantic_obligation_inventory,
)


MAX_DISCOURSE_CANDIDATES = 12

_CLAUSE_ROLE = {
    "grounded_nucleus_notice": "nucleus_notice",
    "grounded_relation_preservation": "relation_notice",
    "unknown_boundary_preservation": "unknown_boundary",
    "significance_or_shift": "shift_notice",
    "intention_or_next_action": "next_action",
    "self_denial_boundary": "self_denial_boundary",
    "bounded_counterposition": "bounded_counterposition",
    STANCE_KIND: "bound_reception",
}
_RELATION_EDGE = {
    "precedes": "precedes",
    "contrasts_with": "contrasts_with",
    "coexists_with": "coexists_with",
    "qualifies": "qualifies",
    "supports_without_guarantee": "explains_without_causation",
}
_OBSERVATION_KIND_RANK = {
    "grounded_nucleus_notice": 1,
    "significance_or_shift": 2,
    "intention_or_next_action": 3,
    "self_denial_boundary": 4,
    "bounded_counterposition": 5,
}
_SOURCE_ORDER_KIND_RANK = {
    "unknown_boundary_preservation": 0,
    "grounded_nucleus_notice": 1,
    "significance_or_shift": 2,
    "intention_or_next_action": 3,
    "self_denial_boundary": 4,
    "bounded_counterposition": 5,
    "grounded_relation_preservation": 6,
    STANCE_KIND: 7,
}


class DiscourseGraphPlannerError(ValueError):
    """Fail-closed planning error with a body-free machine code."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class StructuralVariationCapability:
    order_variation: bool
    merge_split_variation: bool
    reception_position_variation: bool
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class DiscourseGraphPlanSet:
    plans: tuple[dict[str, Any], ...]
    capability: StructuralVariationCapability
    candidate_limit: int = MAX_DISCOURSE_CANDIDATES
    body_free: bool = True


def _node_id(obligation_id: str) -> str:
    return "dn_" + artifact_sha256({"obligation_id": obligation_id})[:20]


def _group_id(section_role: str, node_ids: Sequence[str], ordinal: int) -> str:
    return "sg_" + artifact_sha256(
        {
            "section_role": section_role,
            "node_ids": list(node_ids),
            "ordinal": ordinal,
        }
    )[:20]


def _validated_parents(
    inventory_result: Any,
    content_plan: Any,
) -> tuple[
    Mapping[str, Any],
    list[dict[str, Any]],
    dict[str, dict[str, Any]],
    frozenset[str],
]:
    if type(inventory_result) is not SemanticObligationInventoryResult:
        raise DiscourseGraphPlannerError("DISCOURSE_INVENTORY_RESULT_INVALID")
    ledger = inventory_result.ledger
    if validate_semantic_obligation_inventory(
        ledger, source_snapshot=inventory_result.source_snapshot
    ):
        raise DiscourseGraphPlannerError("DISCOURSE_INVENTORY_REVALIDATION_FAILED")
    if type(content_plan) is not dict or validate_content_selection_policy(
        content_plan, inventory_result=inventory_result
    ):
        raise DiscourseGraphPlannerError("DISCOURSE_CONTENT_REVALIDATION_FAILED")
    rows_value = ledger.get("obligations")
    decisions = content_plan.get("decisions")
    if type(rows_value) is not list or type(decisions) is not list:
        raise DiscourseGraphPlannerError("DISCOURSE_PARENT_SHAPE_INVALID")
    rows = [row for row in rows_value if type(row) is dict]
    by_id = {
        row.get("obligation_id"): row
        for row in rows
        if type(row.get("obligation_id")) is str
    }
    active = frozenset(
        row.get("obligation_id")
        for row in decisions
        if type(row) is dict
        and row.get("status") in {"selected", "integrated_into"}
        and type(row.get("obligation_id")) is str
    )
    if not active or not active <= set(by_id):
        raise DiscourseGraphPlannerError("DISCOURSE_ACTIVE_SET_INVALID")
    return ledger, rows, by_id, active


def _representative_for_nucleus(
    nucleus_id: str,
    *,
    active_rows: Sequence[dict[str, Any]],
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
            _OBSERVATION_KIND_RANK.get(row.get("kind"), 99),
            row.get("obligation_id", ""),
        )
    )
    return str(candidates[0]["obligation_id"])


def _base_nodes(
    *, by_id: Mapping[str, dict[str, Any]], active: frozenset[str]
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    node_for_obligation = {
        obligation_id: _node_id(obligation_id) for obligation_id in active
    }
    nodes: list[dict[str, Any]] = []
    for obligation_id in sorted(active):
        row = by_id[obligation_id]
        kind = row.get("kind")
        if kind not in _CLAUSE_ROLE:
            raise DiscourseGraphPlannerError("DISCOURSE_OBLIGATION_KIND_INVALID")
        separate = sorted(
            node_for_obligation[item]
            for item in row.get("must_not_merge_with", [])
            if item in node_for_obligation
        )
        antecedents = sorted(
            node_for_obligation[item]
            for item in row.get("target_obligation_ids", [])
            if item in node_for_obligation
        ) if kind == STANCE_KIND else []
        nodes.append(
            {
                "node_id": node_for_obligation[obligation_id],
                "obligation_id": obligation_id,
                "section_role": "reception" if kind == STANCE_KIND else "observation",
                "clause_role": _CLAUSE_ROLE[kind],
                "antecedent_node_ids": antecedents,
                "merge_eligible": not bool(separate),
                "must_separate_from_node_ids": separate,
            }
        )
    return nodes, node_for_obligation


def _edge_variants(
    *,
    inventory_result: SemanticObligationInventoryResult,
    active_rows: Sequence[dict[str, Any]],
    active: frozenset[str],
    node_for_obligation: Mapping[str, str],
) -> tuple[tuple[tuple[str, str, str], ...], ...]:
    fixed: set[tuple[str, str, str]] = set()
    directed_rhetorical: set[tuple[str, str, str]] = set()
    bidirectional_choices: list[
        tuple[tuple[str, str, str], tuple[str, str, str]]
    ] = []
    relation_by_alias = {
        row.source_id: row for row in inventory_result.source_snapshot.relations
    }

    for row in active_rows:
        obligation_id = str(row["obligation_id"])
        kind = row.get("kind")
        if kind == STANCE_KIND:
            for target_id in row.get("target_obligation_ids", []):
                if target_id not in active:
                    raise DiscourseGraphPlannerError("DISCOURSE_STANCE_TARGET_INACTIVE")
                fixed.add(
                    (
                        node_for_obligation[target_id],
                        node_for_obligation[obligation_id],
                        "receives",
                    )
                )
        elif kind == "unknown_boundary_preservation":
            target_ids: set[str] = set()
            for nucleus_id in row.get("nucleus_ids", []):
                target_id = _representative_for_nucleus(
                    nucleus_id, active_rows=active_rows
                )
                if target_id:
                    target_ids.add(target_id)
            if not target_ids:
                raise DiscourseGraphPlannerError(
                    "DISCOURSE_UNKNOWN_TARGET_UNRESOLVED"
                )
            for target_id in sorted(target_ids):
                fixed.add(
                    (
                        node_for_obligation[obligation_id],
                        node_for_obligation[target_id],
                        "preserves_unknown_before",
                    )
                )
        elif kind == "self_denial_boundary":
            counters = [
                candidate
                for candidate in active_rows
                if candidate.get("kind") == "bounded_counterposition"
                and set(candidate.get("nucleus_ids", []))
                & set(row.get("nucleus_ids", []))
            ]
            for counter in counters:
                fixed.add(
                    (
                        node_for_obligation[obligation_id],
                        node_for_obligation[str(counter["obligation_id"])],
                        "separates_self_denial_from",
                    )
                )
        if kind != "grounded_relation_preservation":
            continue
        relation_ids = row.get("relation_ids") or []
        if len(relation_ids) != 1:
            raise DiscourseGraphPlannerError("DISCOURSE_RELATION_BINDING_AMBIGUOUS")
        relation = relation_by_alias.get(relation_ids[0])
        if relation is None:
            raise DiscourseGraphPlannerError("DISCOURSE_RELATION_SOURCE_UNRESOLVED")
        left_id = _representative_for_nucleus(
            relation.from_nucleus_id, active_rows=active_rows
        )
        right_id = _representative_for_nucleus(
            relation.to_nucleus_id, active_rows=active_rows
        )
        if left_id is None or right_id is None or left_id == right_id:
            # A typed semantic-restatement relation can have multiple physical
            # endpoints but only one active semantic representative.  It is
            # preserved as its own obligation and must not create fake order.
            if relation.endpoint_semantic_relation == "semantic_restatement":
                continue
            raise DiscourseGraphPlannerError("DISCOURSE_RELATION_ENDPOINT_UNRESOLVED")
        left_node = node_for_obligation[left_id]
        right_node = node_for_obligation[right_id]
        relation_node = node_for_obligation[obligation_id]
        edge_type = _RELATION_EDGE.get(relation.relation_type)
        if edge_type is None:
            raise DiscourseGraphPlannerError("DISCOURSE_RELATION_TYPE_INVALID")
        fixed.add((left_node, relation_node, "qualifies"))
        fixed.add((right_node, relation_node, "qualifies"))
        if relation.relation_direction == "bidirectional" and edge_type in {
            "coexists_with", "contrasts_with"
        }:
            bidirectional_choices.append(
                (
                    (left_node, right_node, edge_type),
                    (right_node, left_node, edge_type),
                )
            )
        elif relation.relation_direction == "source_to_target":
            directed_rhetorical.add((left_node, right_node, edge_type))
        elif relation.relation_direction == "target_to_source":
            directed_rhetorical.add((right_node, left_node, edge_type))
        else:
            raise DiscourseGraphPlannerError(
                "DISCOURSE_RELATION_DIRECTION_UNSUPPORTED"
            )

    variants: list[tuple[tuple[str, str, str], ...]] = []
    choice_products = product(*bidirectional_choices) if bidirectional_choices else [()]
    for choices in choice_products:
        edges = tuple(sorted({*fixed, *directed_rhetorical, *choices}))
        if edges not in variants:
            variants.append(edges)
        if len(variants) >= 4:
            break
    # A source relation remains losslessly represented by its typed relation
    # obligation and both endpoint-to-relation dependencies.  If rhetorical
    # endpoint orientations collectively form a cycle, this canonical fallback
    # removes only those optional presentation edges; it never removes source
    # semantics or the required reception/unknown/safety edges.
    fallback = tuple(sorted(fixed))
    if fallback not in variants:
        variants.append(fallback)
    return tuple(variants)


def _topological_orders(
    node_ids: Sequence[str],
    dependencies: Iterable[tuple[str, str]],
    *,
    limit: int = 4,
    prefer_last: frozenset[str] = frozenset(),
    priority: Mapping[str, int] | None = None,
) -> tuple[tuple[str, ...], ...]:
    node_set = set(node_ids)
    incoming = {node_id: set() for node_id in node_ids}
    outgoing = {node_id: set() for node_id in node_ids}
    for source, target in dependencies:
        if source == target or source not in node_set or target not in node_set:
            raise DiscourseGraphPlannerError("DISCOURSE_DEPENDENCY_INVALID")
        incoming[target].add(source)
        outgoing[source].add(target)
    results: list[tuple[str, ...]] = []

    def visit(order: list[str], current: dict[str, set[str]]) -> None:
        if len(results) >= limit:
            return
        if len(order) == len(node_ids):
            results.append(tuple(order))
            return
        available = sorted(
            (
                node_id
                for node_id in node_ids
                if node_id not in order and not current[node_id]
            ),
            key=lambda node_id: (
                node_id in prefer_last,
                (priority or {}).get(node_id, 10**9),
                node_id,
            ),
        )
        for node_id in available:
            next_incoming = {key: set(value) for key, value in current.items()}
            for target in outgoing[node_id]:
                next_incoming[target].discard(node_id)
            visit([*order, node_id], next_incoming)

    visit([], incoming)
    if not results:
        raise DiscourseGraphPlannerError("DISCOURSE_DEPENDENCY_CYCLE")
    return tuple(results)


def _partitions(
    order: Sequence[str], minimum: int, maximum: int
) -> Iterable[tuple[tuple[str, ...], ...]]:
    if not order:
        return
    upper = min(maximum, len(order))
    for count in range(minimum, upper + 1):
        for cuts in combinations(range(1, len(order)), count - 1):
            boundaries = (0, *cuts, len(order))
            yield tuple(
                tuple(order[boundaries[index] : boundaries[index + 1]])
                for index in range(count)
            )


def _partition_valid(
    groups: Sequence[Sequence[str]],
    *,
    node_by_id: Mapping[str, Mapping[str, Any]],
    final_target_nodes: frozenset[str] = frozenset(),
    required_colocations: frozenset[tuple[str, str]] = frozenset(),
) -> bool:
    group_index = {
        node_id: index
        for index, group in enumerate(groups)
        for node_id in group
    }
    for node_id, node in node_by_id.items():
        if node_id not in group_index:
            continue
        if any(
            group_index.get(target) == group_index[node_id]
            for target in node.get("must_separate_from_node_ids", [])
        ):
            return False
    if any(
        group_index.get(left) != group_index.get(right)
        for left, right in required_colocations
    ):
        return False
    if final_target_nodes:
        final_group = tuple(groups[-1])
        if len(final_group) < len(final_target_nodes):
            return False
        if set(final_group[-len(final_target_nodes) :]) != set(final_target_nodes):
            return False
    return True


def _rhetorical_adjacency_valid(
    groups: Sequence[Sequence[str]],
    edges: Sequence[tuple[str, str, str]],
) -> bool:
    group_index = {
        node_id: index
        for index, group in enumerate(groups)
        for node_id in group
    }
    for source, target, edge_type in edges:
        if edge_type != "contrasts_with":
            continue
        if source not in group_index or target not in group_index:
            continue
        if abs(group_index[source] - group_index[target]) > 1:
            return False
    return True


def _observation_layout(
    plan: Mapping[str, Any],
) -> tuple[tuple[str, ...], ...]:
    return tuple(
        tuple(group["node_ids"])
        for group in plan["sentence_groups"]
        if group["section_role"] == "observation"
    )


def _reception_layout(
    plan: Mapping[str, Any],
) -> tuple[tuple[str, ...], ...]:
    return tuple(
        tuple(group["node_ids"])
        for group in plan["sentence_groups"]
        if group["section_role"] == "reception"
    )


def _observation_order(plan: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(item for group in _observation_layout(plan) for item in group)


def _edge_signature(
    plan: Mapping[str, Any],
) -> tuple[tuple[str, str, str], ...]:
    return tuple(
        (edge["from"], edge["to"], edge["type"])
        for edge in plan["edges"]
    )


def _select_candidate_subset(
    candidates: Sequence[dict[str, Any]],
) -> tuple[dict[str, Any], ...]:
    """Keep representative structural dimensions before filling the cap."""

    ordered = sorted(candidates, key=lambda row: row["structural_signature"])
    if len(ordered) <= MAX_DISCOURSE_CANDIDATES:
        return tuple(ordered)
    selected: list[dict[str, Any]] = [ordered[0]]
    selected_signatures = {ordered[0]["structural_signature"]}

    def add_first(predicate: Any) -> None:
        if len(selected) >= MAX_DISCOURSE_CANDIDATES:
            return
        for candidate in ordered:
            signature = candidate["structural_signature"]
            if signature not in selected_signatures and predicate(candidate):
                selected.append(candidate)
                selected_signatures.add(signature)
                return

    canonical = ordered[0]
    canonical_order = _observation_order(canonical)
    canonical_partition = _observation_layout(canonical)
    canonical_reception = _reception_layout(canonical)
    canonical_edges = _edge_signature(canonical)
    add_first(
        lambda candidate: _observation_order(candidate) == canonical_order
        and _observation_layout(candidate) != canonical_partition
    )
    add_first(lambda candidate: _observation_order(candidate) != canonical_order)
    add_first(lambda candidate: _reception_layout(candidate) != canonical_reception)
    add_first(lambda candidate: _edge_signature(candidate) != canonical_edges)

    while len(selected) < MAX_DISCOURSE_CANDIDATES:
        seen_orders = {_observation_order(item) for item in selected}
        seen_partitions = {
            (_observation_order(item), _observation_layout(item))
            for item in selected
        }
        seen_receptions = {_reception_layout(item) for item in selected}
        seen_edges = {_edge_signature(item) for item in selected}
        remaining = [
            item
            for item in ordered
            if item["structural_signature"] not in selected_signatures
        ]
        if not remaining:
            break

        def score(candidate: Mapping[str, Any]) -> tuple[int, str]:
            new_dimensions = sum(
                (
                    _observation_order(candidate) not in seen_orders,
                    (
                        _observation_order(candidate),
                        _observation_layout(candidate),
                    )
                    not in seen_partitions,
                    _reception_layout(candidate) not in seen_receptions,
                    _edge_signature(candidate) not in seen_edges,
                )
            )
            return (-new_dimensions, str(candidate["structural_signature"]))

        chosen = min(remaining, key=score)
        selected.append(chosen)
        selected_signatures.add(chosen["structural_signature"])
    return tuple(sorted(selected, key=lambda row: row["structural_signature"]))


def _build_plan(
    *,
    nodes: Sequence[dict[str, Any]],
    edges: Sequence[tuple[str, str, str]],
    observation_groups: Sequence[Sequence[str]],
    reception_groups: Sequence[Sequence[str]],
    content_plan: Mapping[str, Any],
) -> dict[str, Any]:
    groups: list[dict[str, Any]] = []
    for section, section_groups in (
        ("observation", observation_groups),
        ("reception", reception_groups),
    ):
        for ordinal, node_ids in enumerate(section_groups):
            ids = list(node_ids)
            groups.append(
                {
                    "sentence_group_id": _group_id(section, ids, ordinal),
                    "section_role": section,
                    "node_ids": ids,
                }
            )
    plan: dict[str, Any] = {
        "schema_version": DISCOURSE_SCHEMA,
        "discourse_plan_id": "nls3dp_0000000000000000",
        "source_content_plan_sha256": artifact_sha256(content_plan),
        "structural_signature": "nls3sig_0000000000000000",
        "nodes": [dict(row) for row in sorted(nodes, key=lambda row: row["node_id"])],
        "edges": [
            {"from": source, "to": target, "type": edge_type}
            for source, target, edge_type in sorted(edges)
        ],
        "sentence_groups": groups,
        "body_free": True,
    }
    plan["structural_signature"] = "nls3sig_" + artifact_sha256(
        {
            "nodes": plan["nodes"],
            "edges": plan["edges"],
            "sentence_groups": plan["sentence_groups"],
        }
    )[:16]
    plan["discourse_plan_id"] = derive_content_id(
        "nls3dp_", plan, "discourse_plan_id"
    )
    return plan


def _generate(
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
) -> tuple[dict[str, Any], ...]:
    ledger = inventory_result.ledger
    rows = ledger["obligations"]
    by_id = {row["obligation_id"]: row for row in rows}
    active = frozenset(
        row["obligation_id"]
        for row in content_plan["decisions"]
        if row["status"] in {"selected", "integrated_into"}
    )
    active_rows = [by_id[item] for item in sorted(active)]
    nodes, node_for_obligation = _base_nodes(by_id=by_id, active=active)
    node_by_id = {row["node_id"]: row for row in nodes}
    observation_nodes = tuple(
        row["node_id"] for row in nodes if row["section_role"] == "observation"
    )
    reception_nodes = tuple(
        row["node_id"] for row in nodes if row["section_role"] == "reception"
    )
    if not observation_nodes or not reception_nodes:
        raise DiscourseGraphPlannerError("DISCOURSE_SECTION_NODE_REQUIRED")
    budget = content_plan["section_budget"]
    plans: list[dict[str, Any]] = []
    signatures: set[str] = set()
    edge_variants = _edge_variants(
        inventory_result=inventory_result,
        active_rows=active_rows,
        active=active,
        node_for_obligation=node_for_obligation,
    )
    target_nodes = frozenset(
        node_for_obligation[target]
        for row in active_rows
        if row.get("kind") == STANCE_KIND
        for target in row.get("target_obligation_ids", [])
    )
    observation_rows = [
        row for row in active_rows if row.get("kind") != STANCE_KIND
    ]
    required_colocations: set[tuple[str, str]] = set()
    if len(observation_rows) == 2:
        unknown_rows = [
            row
            for row in observation_rows
            if row.get("kind") == "unknown_boundary_preservation"
        ]
        if len(unknown_rows) == 1:
            unknown_row = unknown_rows[0]
            other_row = next(row for row in observation_rows if row is not unknown_row)
            if set(unknown_row.get("nucleus_ids", [])) & set(
                other_row.get("nucleus_ids", [])
            ):
                required_colocations.add(
                    (
                        node_for_obligation[str(unknown_row["obligation_id"])],
                        node_for_obligation[str(other_row["obligation_id"])],
                    )
                )
    nucleus_order = {
        row.source_id: index
        for index, row in enumerate(inventory_result.source_snapshot.nuclei)
    }
    node_priority: dict[str, int] = {}
    for row in active_rows:
        source_positions = [
            nucleus_order[item]
            for item in row.get("nucleus_ids", [])
            if item in nucleus_order
        ]
        source_position = min(source_positions) if source_positions else 10**6
        node_priority[node_for_obligation[str(row["obligation_id"])]] = (
            source_position * 10
            + _SOURCE_ORDER_KIND_RANK.get(str(row.get("kind")), 9)
        )
    minimal_policy = content_plan.get("depth") == "minimal"
    searched_edge_variants = edge_variants
    for edges in searched_edge_variants:
        dependencies = [(source, target) for source, target, _ in edges]
        dependencies.extend(
            (antecedent, row["node_id"])
            for row in nodes
            for antecedent in row["antecedent_node_ids"]
        )
        observation_dependencies = [
            (source, target)
            for source, target in dependencies
            if source in observation_nodes and target in observation_nodes
        ]
        reception_dependencies = [
            (source, target)
            for source, target in dependencies
            if source in reception_nodes and target in reception_nodes
        ]
        try:
            observation_orders = _topological_orders(
                observation_nodes,
                observation_dependencies,
                limit=1 if minimal_policy else 4,
                prefer_last=target_nodes,
                priority=node_priority,
            )
            reception_orders = _topological_orders(
                reception_nodes,
                reception_dependencies,
                limit=1 if minimal_policy else 4,
                priority=node_priority,
            )
        except DiscourseGraphPlannerError as exc:
            if exc.code == "DISCOURSE_DEPENDENCY_CYCLE":
                continue
            raise
        for observation_order, reception_order in product(
            observation_orders, reception_orders
        ):
            topology_plans: list[dict[str, Any]] = []
            topology_observation_layouts: set[
                tuple[tuple[str, ...], ...]
            ] = set()
            topology_reception_layouts: set[
                tuple[tuple[str, ...], ...]
            ] = set()
            topology_observation_counts: set[int] = set()
            topology_reception_counts: set[int] = set()
            for observation_groups in _partitions(
                observation_order,
                budget["observation_sentence_min"],
                budget["observation_sentence_max"],
            ):
                if not _partition_valid(
                    observation_groups,
                    node_by_id=node_by_id,
                    final_target_nodes=target_nodes,
                    required_colocations=frozenset(required_colocations),
                ) or not _rhetorical_adjacency_valid(
                    observation_groups, edges
                ):
                    continue
                for reception_groups in _partitions(
                    reception_order,
                    budget["reception_sentence_min"],
                    budget["reception_sentence_max"],
                ):
                    if (
                        len(observation_groups) + len(reception_groups)
                        > budget["total_sentence_max"]
                        or not _partition_valid(
                            reception_groups, node_by_id=node_by_id
                        )
                    ):
                        continue
                    plan = _build_plan(
                        nodes=nodes,
                        edges=edges,
                        observation_groups=observation_groups,
                        reception_groups=reception_groups,
                        content_plan=content_plan,
                    )
                    signature = plan["structural_signature"]
                    if signature in signatures:
                        continue
                    observation_layout = tuple(
                        tuple(group) for group in observation_groups
                    )
                    reception_layout = tuple(
                        tuple(group) for group in reception_groups
                    )
                    keep = not topology_plans
                    if (
                        observation_layout not in topology_observation_layouts
                        and len(topology_observation_layouts) < 2
                    ):
                        keep = True
                    if len(observation_layout) not in topology_observation_counts:
                        keep = True
                    if (
                        reception_layout not in topology_reception_layouts
                        and len(topology_reception_layouts) < 2
                    ):
                        keep = True
                    if len(reception_layout) not in topology_reception_counts:
                        keep = True
                    if not keep:
                        continue
                    signatures.add(signature)
                    topology_plans.append(plan)
                    topology_observation_layouts.add(observation_layout)
                    topology_reception_layouts.add(reception_layout)
                    topology_observation_counts.add(len(observation_layout))
                    topology_reception_counts.add(len(reception_layout))
            plans.extend(topology_plans)
    if not plans:
        raise DiscourseGraphPlannerError("NO_SAFE_DISCOURSE_STRUCTURE")
    if minimal_policy:
        return (
            sorted(
                plans,
                key=lambda row: (
                    -len(row["edges"]),
                    row["structural_signature"],
                ),
            )[0],
        )
    return _select_candidate_subset(plans)


def _capability(plans: Sequence[Mapping[str, Any]]) -> StructuralVariationCapability:
    orders: set[tuple[str, ...]] = set()
    partitions_by_order: dict[
        tuple[str, ...], set[tuple[tuple[str, ...], ...]]
    ] = {}
    receptions: set[tuple[tuple[str, ...], ...]] = set()
    for plan in plans:
        observation = tuple(
            tuple(group["node_ids"])
            for group in plan["sentence_groups"]
            if group["section_role"] == "observation"
        )
        reception = tuple(
            tuple(group["node_ids"])
            for group in plan["sentence_groups"]
            if group["section_role"] == "reception"
        )
        order = tuple(item for group in observation for item in group)
        orders.add(order)
        partitions_by_order.setdefault(order, set()).add(observation)
        receptions.add(reception)
    order_variation = len(orders) >= 2
    merge_split = any(
        len(partitions) >= 2 for partitions in partitions_by_order.values()
    )
    reception_variation = len(receptions) >= 2
    reasons: list[str] = []
    if not order_variation:
        reasons.append("ALL_SAFE_ORDERS_CONSTRAINED")
        if any(
            node["section_role"] == "reception"
            for plan in plans
            for node in plan["nodes"]
        ):
            reasons.append("BOUND_RECEPTION_TARGET_ORDER_FIXED")
    if not merge_split:
        reasons.append("NO_SAFE_MERGE_SPLIT_ALTERNATIVE")
    if not reception_variation:
        reasons.append("SINGLE_BOUND_RECEPTION_POSITION")
    if len(plans) == 1:
        reasons.append("NO_SAFE_STRUCTURAL_ALTERNATIVE")
    return StructuralVariationCapability(
        order_variation=order_variation,
        merge_split_variation=merge_split,
        reception_position_variation=reception_variation,
        reason_codes=tuple(sorted(reasons)),
    )


def build_discourse_graph_plans(
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
) -> DiscourseGraphPlanSet:
    """Build at most twelve distinct, validator-green structures."""

    ledger, _rows, _by_id, _active = _validated_parents(
        inventory_result, content_plan
    )
    plans = _generate(inventory_result, content_plan)
    for plan in plans:
        if validate_discourse_plan(
            plan,
            content_plan=content_plan,
            obligation_ledger=ledger,
        ):
            raise DiscourseGraphPlannerError("DISCOURSE_CONTRACT_REJECTED")
    result = DiscourseGraphPlanSet(plans=plans, capability=_capability(plans))
    if validate_discourse_graph_plan_set(
        result,
        inventory_result=inventory_result,
        content_plan=content_plan,
    ):
        raise DiscourseGraphPlannerError("DISCOURSE_POLICY_REJECTED")
    return result


def validate_discourse_graph_plan_set(
    value: Any,
    *,
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
) -> tuple[str, ...]:
    """Recompute the complete candidate set; do not trust self-report fields."""

    issues: list[str] = []
    try:
        ledger, _rows, _by_id, _active = _validated_parents(
            inventory_result, content_plan
        )
        expected = _generate(inventory_result, content_plan)
    except (DiscourseGraphPlannerError, KeyError, TypeError, ValueError):
        return ("DISCOURSE_PARENT_REVALIDATION_FAILED",)
    if type(value) is not DiscourseGraphPlanSet:
        return ("DISCOURSE_PLAN_SET_TYPE_INVALID",)
    if value.body_free is not True:
        issues.append("DISCOURSE_PLAN_SET_BODY_FREE_REQUIRED")
    if value.candidate_limit != MAX_DISCOURSE_CANDIDATES:
        issues.append("DISCOURSE_CANDIDATE_LIMIT_MISMATCH")
    if type(value.plans) is not tuple or value.plans != expected:
        issues.append("DISCOURSE_PLAN_SET_MISMATCH")
    if value.capability != _capability(expected):
        issues.append("DISCOURSE_CAPABILITY_MISMATCH")
    signatures: list[str] = []
    for plan in value.plans if type(value.plans) is tuple else ():
        if type(plan) is not dict:
            issues.append("DISCOURSE_PLAN_TYPE_INVALID")
            continue
        signatures.append(str(plan.get("structural_signature", "")))
        contract_issues = validate_discourse_plan(
            plan,
            content_plan=content_plan,
            obligation_ledger=ledger,
        )
        if contract_issues:
            issues.append("DISCOURSE_CONTRACT_REJECTED")
    if len(signatures) != len(set(signatures)) or len(signatures) > MAX_DISCOURSE_CANDIDATES:
        issues.append("DISCOURSE_SIGNATURE_SET_INVALID")
    return tuple(sorted(set(issues)))


__all__ = [
    "DiscourseGraphPlanSet",
    "DiscourseGraphPlannerError",
    "MAX_DISCOURSE_CANDIDATES",
    "StructuralVariationCapability",
    "build_discourse_graph_plans",
    "validate_discourse_graph_plan_set",
]
