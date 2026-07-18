# -*- coding: utf-8 -*-
from __future__ import annotations

"""rc0024 planning frontier over the frozen Step 4--9 parents.

Step 9 freezes the bytes of the original obligation, content-selection, and
discourse owners.  Step 11 therefore does not rewrite those parents.  This
body-free successor contract records the small set of source-backed optional
obligations that must participate as ``integrated_into`` semantic units before
the surface overlay, AST, renderer, parser, or matcher runs.

The rule is structural: authoritative ``emotion_details`` nuclei of both
valences participate in one mixed-emotion unit.  Parallel legacy ``emotions``
nuclei are never promoted, and no corpus/sample oracle is observable here.
"""

from dataclasses import dataclass
from itertools import product
from typing import Any, Mapping

from emlis_ai_content_selection_v3 import validate_content_selection_policy
from emlis_ai_discourse_graph_planner_v3 import (
    MAX_DISCOURSE_CANDIDATES,
    DiscourseGraphPlannerError,
    DiscourseGraphPlanSet,
    _base_nodes,
    _build_plan,
    _capability,
    _edge_variants,
    _partition_valid,
    _partitions,
    _rhetorical_adjacency_valid,
    _select_candidate_subset,
    _topological_orders,
)
from emlis_ai_nls_v3_artifact_contract import (
    STANCE_KIND,
    artifact_sha256,
    validate_discourse_plan,
)
from emlis_ai_semantic_obligation_inventory_v3 import (
    SemanticObligationInventoryResult,
    validate_semantic_obligation_inventory,
)


STEP11_HISTORICAL_RC0021_PLANNING_FRONTIER_SCHEMA = (
    "cocolon.emlis.nls_v3.step11_planning_frontier.rc0021.v1"
)
STEP11_HISTORICAL_RC0021_PLANNING_FRONTIER_VERSION = "nls_v3_rc_0021"
STEP11_HISTORICAL_RC0022_PLANNING_FRONTIER_VERSION = "nls_v3_rc_0022"
STEP11_HISTORICAL_RC0023_PLANNING_FRONTIER_VERSION = "nls_v3_rc_0023"
STEP11_PLANNING_FRONTIER_SCHEMA = (
    "cocolon.emlis.nls_v3.step11_planning_frontier.rc0024.v1"
)
STEP11_PLANNING_FRONTIER_VERSION = "nls_v3_rc_0024"
_ACTIVE_STATUSES = frozenset({"selected", "integrated_into"})


class Step11PlanningFrontierError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class Step11PlanningIntegration:
    obligation_id: str
    integrated_into_obligation_id: str
    target_sentence_group_id: str
    nucleus_ids: tuple[str, ...]
    reason_code: str = "mixed_emotion_source_backed_integration"


@dataclass(frozen=True, slots=True, repr=False)
class Step11PlanningFrontier:
    schema_version: str
    candidate_version_id: str
    frontier_id: str
    source_obligation_ledger_sha256: str
    source_content_plan_sha256: str
    source_discourse_plan_sha256: str
    base_active_obligation_ids: tuple[str, ...]
    integrated_obligation_ids: tuple[str, ...]
    participating_obligation_ids: tuple[str, ...]
    active_nucleus_ids: tuple[str, ...]
    active_relation_ids: tuple[str, ...]
    active_unknown_ids: tuple[str, ...]
    mixed_emotion_nucleus_ids: tuple[str, ...]
    integrations: tuple[Step11PlanningIntegration, ...]
    body_free: bool = True


def _integration_material(value: Step11PlanningIntegration) -> dict[str, Any]:
    return {
        "obligation_id": value.obligation_id,
        "integrated_into_obligation_id": value.integrated_into_obligation_id,
        "target_sentence_group_id": value.target_sentence_group_id,
        "nucleus_ids": list(value.nucleus_ids),
        "reason_code": value.reason_code,
    }


def step11_planning_frontier_material(
    value: Step11PlanningFrontier,
    *,
    include_id: bool = True,
) -> dict[str, Any]:
    if type(value) is not Step11PlanningFrontier:
        raise Step11PlanningFrontierError(
            "STEP11_PLANNING_FRONTIER_TYPE_INVALID"
        )
    result: dict[str, Any] = {
        "schema_version": value.schema_version,
        "candidate_version_id": value.candidate_version_id,
        "frontier_id": value.frontier_id,
        "source_obligation_ledger_sha256": (
            value.source_obligation_ledger_sha256
        ),
        "source_content_plan_sha256": value.source_content_plan_sha256,
        "source_discourse_plan_sha256": value.source_discourse_plan_sha256,
        "base_active_obligation_ids": list(
            value.base_active_obligation_ids
        ),
        "integrated_obligation_ids": list(value.integrated_obligation_ids),
        "participating_obligation_ids": list(
            value.participating_obligation_ids
        ),
        "active_nucleus_ids": list(value.active_nucleus_ids),
        "active_relation_ids": list(value.active_relation_ids),
        "active_unknown_ids": list(value.active_unknown_ids),
        "mixed_emotion_nucleus_ids": list(
            value.mixed_emotion_nucleus_ids
        ),
        "integrations": [
            _integration_material(row) for row in value.integrations
        ],
        "body_free": value.body_free,
    }
    if not include_id:
        result.pop("frontier_id")
    return result


def _trusted_parent_rows(
    inventory_result: Any,
    content_plan: Any,
    discourse_plan: Any,
) -> tuple[
    dict[str, Any],
    dict[str, dict[str, Any]],
    frozenset[str],
    dict[str, str],
    dict[str, str],
]:
    if type(inventory_result) is not SemanticObligationInventoryResult:
        raise Step11PlanningFrontierError(
            "STEP11_PLANNING_INVENTORY_REQUIRED"
        )
    ledger = inventory_result.ledger
    try:
        if validate_semantic_obligation_inventory(
            ledger, source_snapshot=inventory_result.source_snapshot
        ):
            raise Step11PlanningFrontierError(
                "STEP11_PLANNING_INVENTORY_REVALIDATION_FAILED"
            )
        if validate_content_selection_policy(
            content_plan, inventory_result=inventory_result
        ):
            raise Step11PlanningFrontierError(
                "STEP11_PLANNING_CONTENT_REVALIDATION_FAILED"
            )
        if validate_discourse_plan(
            discourse_plan,
            content_plan=content_plan,
            obligation_ledger=ledger,
        ):
            raise Step11PlanningFrontierError(
                "STEP11_PLANNING_DISCOURSE_REVALIDATION_FAILED"
            )
    except Step11PlanningFrontierError:
        raise
    except (AttributeError, KeyError, TypeError, UnicodeError, ValueError) as exc:
        raise Step11PlanningFrontierError(
            "STEP11_PLANNING_PARENT_REVALIDATION_FAILED"
        ) from exc

    rows = ledger.get("obligations")
    decisions = content_plan.get("decisions")
    nodes = discourse_plan.get("nodes")
    groups = discourse_plan.get("sentence_groups")
    if any(type(value) is not list for value in (rows, decisions, nodes, groups)):
        raise Step11PlanningFrontierError(
            "STEP11_PLANNING_PARENT_ROWS_INVALID"
        )
    by_id = {
        row.get("obligation_id"): row
        for row in rows
        if type(row) is dict and type(row.get("obligation_id")) is str
    }
    if len(by_id) != len(rows):
        raise Step11PlanningFrontierError(
            "STEP11_PLANNING_LEDGER_IDENTITY_INVALID"
        )
    base_active = frozenset(
        row.get("obligation_id")
        for row in decisions
        if type(row) is dict and row.get("status") in _ACTIVE_STATUSES
    )
    node_by_obligation = {
        row.get("obligation_id"): row.get("node_id")
        for row in nodes
        if type(row) is dict
        and type(row.get("obligation_id")) is str
        and type(row.get("node_id")) is str
    }
    if set(node_by_obligation) != set(base_active):
        raise Step11PlanningFrontierError(
            "STEP11_PLANNING_ACTIVE_NODE_MISMATCH"
        )
    group_by_node: dict[str, str] = {}
    for group in groups:
        if type(group) is not dict:
            raise Step11PlanningFrontierError(
                "STEP11_PLANNING_GROUP_ROW_INVALID"
            )
        group_id = group.get("sentence_group_id")
        node_ids = group.get("node_ids")
        if type(group_id) is not str or type(node_ids) is not list:
            raise Step11PlanningFrontierError(
                "STEP11_PLANNING_GROUP_ROW_INVALID"
            )
        for node_id in node_ids:
            if type(node_id) is not str or node_id in group_by_node:
                raise Step11PlanningFrontierError(
                    "STEP11_PLANNING_GROUP_NODE_INVALID"
                )
            group_by_node[node_id] = group_id
    if set(group_by_node) != set(node_by_obligation.values()):
        raise Step11PlanningFrontierError(
            "STEP11_PLANNING_GROUP_COVERAGE_INVALID"
        )
    return ledger, by_id, base_active, node_by_obligation, group_by_node


def build_step11_planning_frontier(
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
    discourse_plan: Mapping[str, Any],
    *,
    _trusted_rows: tuple[
        dict[str, Any],
        dict[str, dict[str, Any]],
        frozenset[str],
        dict[str, str],
        dict[str, str],
    ]
    | None = None,
) -> Step11PlanningFrontier:
    """Build the source-only successor frontier before surface planning."""

    (
        ledger,
        by_id,
        base_active,
        node_by_obligation,
        group_by_node,
    ) = (
        _trusted_parent_rows(inventory_result, content_plan, discourse_plan)
        if _trusted_rows is None
        else _trusted_rows
    )

    authoritative_emotions = tuple(
        row
        for row in inventory_result.source_snapshot.nuclei
        if "emotion_details" in row.source_fields
        and row.allowed_claim_scope == "selected_label_only"
        and row.polarity in {"positive", "negative"}
    )
    has_mixed_valence = {
        row.polarity for row in authoritative_emotions
    } == {"positive", "negative"}
    mixed_nucleus_ids = (
        tuple(sorted(row.source_id for row in authoritative_emotions))
        if has_mixed_valence
        else ()
    )
    obligation_by_single_nucleus = {
        tuple(row.get("nucleus_ids", []))[0]: obligation_id
        for obligation_id, row in by_id.items()
        if row.get("kind") == "grounded_nucleus_notice"
        and len(row.get("nucleus_ids", [])) == 1
        and not row.get("relation_ids")
        and not row.get("unknown_boundary_ids")
    }
    mixed_obligation_ids = tuple(
        sorted(
            obligation_by_single_nucleus[nucleus_id]
            for nucleus_id in mixed_nucleus_ids
            if nucleus_id in obligation_by_single_nucleus
        )
    )
    if mixed_nucleus_ids and len(mixed_obligation_ids) != len(
        mixed_nucleus_ids
    ):
        raise Step11PlanningFrontierError(
            "STEP11_PLANNING_MIXED_EMOTION_OBLIGATION_UNRESOLVED"
        )

    target_candidates = tuple(
        obligation_id
        for obligation_id in sorted(base_active)
        if by_id[obligation_id].get("kind")
        == "grounded_relation_preservation"
    ) or tuple(
        obligation_id
        for obligation_id in sorted(base_active)
        if by_id[obligation_id].get("kind") != STANCE_KIND
    )
    deferred_mixed_ids = tuple(
        obligation_id
        for obligation_id in mixed_obligation_ids
        if obligation_id not in base_active
    )
    if deferred_mixed_ids and not target_candidates:
        raise Step11PlanningFrontierError(
            "STEP11_PLANNING_INTEGRATION_TARGET_UNRESOLVED"
        )
    target_obligation_id = target_candidates[0] if target_candidates else None
    target_group_id = (
        group_by_node[node_by_obligation[target_obligation_id]]
        if target_obligation_id is not None
        else None
    )
    integrations = tuple(
        Step11PlanningIntegration(
            obligation_id=obligation_id,
            integrated_into_obligation_id=str(target_obligation_id),
            target_sentence_group_id=str(target_group_id),
            nucleus_ids=tuple(by_id[obligation_id]["nucleus_ids"]),
        )
        for obligation_id in deferred_mixed_ids
    )
    participating = tuple(sorted((*base_active, *deferred_mixed_ids)))
    active_nuclei = tuple(
        sorted(
            {
                nucleus_id
                for obligation_id in participating
                for nucleus_id in by_id[obligation_id].get("nucleus_ids", [])
            }
        )
    )
    active_relations = tuple(
        sorted(
            {
                relation_id
                for obligation_id in participating
                for relation_id in by_id[obligation_id].get("relation_ids", [])
            }
        )
    )
    active_unknowns = tuple(
        sorted(
            {
                unknown_id
                for obligation_id in participating
                for unknown_id in by_id[obligation_id].get(
                    "unknown_boundary_ids", []
                )
            }
        )
    )

    provisional = Step11PlanningFrontier(
        schema_version=STEP11_PLANNING_FRONTIER_SCHEMA,
        candidate_version_id=STEP11_PLANNING_FRONTIER_VERSION,
        frontier_id="nls3s11front_00000000000000000000",
        source_obligation_ledger_sha256=artifact_sha256(ledger),
        source_content_plan_sha256=artifact_sha256(content_plan),
        source_discourse_plan_sha256=artifact_sha256(discourse_plan),
        base_active_obligation_ids=tuple(sorted(base_active)),
        integrated_obligation_ids=deferred_mixed_ids,
        participating_obligation_ids=participating,
        active_nucleus_ids=active_nuclei,
        active_relation_ids=active_relations,
        active_unknown_ids=active_unknowns,
        mixed_emotion_nucleus_ids=mixed_nucleus_ids,
        integrations=integrations,
        body_free=True,
    )
    frontier_id = "nls3s11front_" + artifact_sha256(
        step11_planning_frontier_material(provisional, include_id=False)
    )[:20]
    return Step11PlanningFrontier(
        schema_version=provisional.schema_version,
        candidate_version_id=provisional.candidate_version_id,
        frontier_id=frontier_id,
        source_obligation_ledger_sha256=(
            provisional.source_obligation_ledger_sha256
        ),
        source_content_plan_sha256=provisional.source_content_plan_sha256,
        source_discourse_plan_sha256=provisional.source_discourse_plan_sha256,
        base_active_obligation_ids=provisional.base_active_obligation_ids,
        integrated_obligation_ids=provisional.integrated_obligation_ids,
        participating_obligation_ids=(
            provisional.participating_obligation_ids
        ),
        active_nucleus_ids=provisional.active_nucleus_ids,
        active_relation_ids=provisional.active_relation_ids,
        active_unknown_ids=provisional.active_unknown_ids,
        mixed_emotion_nucleus_ids=provisional.mixed_emotion_nucleus_ids,
        integrations=provisional.integrations,
        body_free=True,
    )


def build_step11_terminal_pair_discourse_plans(
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
) -> DiscourseGraphPlanSet:
    """Build a successor plan when the frozen target-last rule deadlocks.

    The frozen planner can require a reception-targeted self-denial node to
    be the final group while also requiring its grounded counterposition to
    follow it.  rc0020 keeps both parents immutable and treats that exact
    semantic unit as two terminal groups: boundary, then counterposition.
    """

    if type(inventory_result) is not SemanticObligationInventoryResult:
        raise Step11PlanningFrontierError(
            "STEP11_TERMINAL_PAIR_INVENTORY_REQUIRED"
        )
    ledger = inventory_result.ledger
    try:
        if validate_semantic_obligation_inventory(
            ledger, source_snapshot=inventory_result.source_snapshot
        ) or validate_content_selection_policy(
            content_plan, inventory_result=inventory_result
        ):
            raise Step11PlanningFrontierError(
                "STEP11_TERMINAL_PAIR_PARENT_REVALIDATION_FAILED"
            )
    except Step11PlanningFrontierError:
        raise
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise Step11PlanningFrontierError(
            "STEP11_TERMINAL_PAIR_PARENT_REVALIDATION_FAILED"
        ) from exc

    rows = ledger.get("obligations")
    decisions = content_plan.get("decisions")
    budget = content_plan.get("section_budget")
    if (
        type(rows) is not list
        or type(decisions) is not list
        or type(budget) is not dict
    ):
        raise Step11PlanningFrontierError(
            "STEP11_TERMINAL_PAIR_PARENT_ROWS_INVALID"
        )
    by_id = {
        row.get("obligation_id"): row
        for row in rows
        if type(row) is dict and type(row.get("obligation_id")) is str
    }
    active = frozenset(
        row.get("obligation_id")
        for row in decisions
        if type(row) is dict and row.get("status") in _ACTIVE_STATUSES
    )
    if len(by_id) != len(rows) or not active or not active <= set(by_id):
        raise Step11PlanningFrontierError(
            "STEP11_TERMINAL_PAIR_ACTIVE_SET_INVALID"
        )

    targeted_self_ids = {
        str(target_id)
        for obligation_id in active
        if by_id[obligation_id].get("kind") == STANCE_KIND
        for target_id in by_id[obligation_id].get(
            "target_obligation_ids", []
        )
        if target_id in active
        and by_id[str(target_id)].get("kind") == "self_denial_boundary"
    }
    obligation_pairs: list[tuple[str, str]] = []
    consumed_counters: set[str] = set()
    for self_id in sorted(targeted_self_ids):
        self_row = by_id[self_id]
        nuclei = frozenset(self_row.get("nucleus_ids", []))
        counters = tuple(
            obligation_id
            for obligation_id in active
            if by_id[obligation_id].get("kind")
            == "bounded_counterposition"
            and nuclei
            and frozenset(by_id[obligation_id].get("nucleus_ids", []))
            == nuclei
            and obligation_id
            in set(self_row.get("must_not_merge_with", []))
            and self_id
            in set(by_id[obligation_id].get("must_not_merge_with", []))
        )
        if len(counters) != 1 or counters[0] in consumed_counters:
            raise Step11PlanningFrontierError(
                "STEP11_TERMINAL_PAIR_CONTRACT_INVALID"
            )
        consumed_counters.add(counters[0])
        obligation_pairs.append((self_id, counters[0]))
    if not obligation_pairs:
        raise Step11PlanningFrontierError(
            "STEP11_TERMINAL_PAIR_NOT_APPLICABLE"
        )

    nodes, node_for_obligation = _base_nodes(
        by_id=by_id,
        active=active,
    )
    node_by_id = {row["node_id"]: row for row in nodes}
    observation_nodes = tuple(
        row["node_id"]
        for row in nodes
        if row["section_role"] == "observation"
    )
    reception_nodes = tuple(
        row["node_id"]
        for row in nodes
        if row["section_role"] == "reception"
    )
    node_pairs = tuple(
        (node_for_obligation[left], node_for_obligation[right])
        for left, right in obligation_pairs
    )
    target_nodes = frozenset(
        node_for_obligation[str(target_id)]
        for obligation_id in active
        if by_id[obligation_id].get("kind") == STANCE_KIND
        for target_id in by_id[obligation_id].get(
            "target_obligation_ids", []
        )
        if target_id in active
    )
    terminal_boundary_nodes = frozenset(left for left, _ in node_pairs)
    if target_nodes != terminal_boundary_nodes:
        raise Step11PlanningFrontierError(
            "STEP11_TERMINAL_PAIR_TARGET_SET_INVALID"
        )

    observation_rows = [
        by_id[obligation_id]
        for obligation_id in active
        if by_id[obligation_id].get("kind") != STANCE_KIND
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
            other_row = next(
                row for row in observation_rows if row is not unknown_row
            )
            if set(unknown_row.get("nucleus_ids", [])) & set(
                other_row.get("nucleus_ids", [])
            ):
                required_colocations.add(
                    (
                        node_for_obligation[
                            str(unknown_row["obligation_id"])
                        ],
                        node_for_obligation[
                            str(other_row["obligation_id"])
                        ],
                    )
                )

    def terminal_pair_layout_valid(
        groups: tuple[tuple[str, ...], ...],
    ) -> bool:
        if len(groups) < 2 * len(node_pairs):
            return False
        suffix = groups[-(2 * len(node_pairs)) :]
        remaining = list(node_pairs)
        for index in range(0, len(suffix), 2):
            matches = [
                (pair_index, pair)
                for pair_index, pair in enumerate(remaining)
                if suffix[index]
                and suffix[index][-1] == pair[0]
                and suffix[index + 1] == (pair[1],)
            ]
            if len(matches) != 1:
                return False
            remaining.pop(matches[0][0])
        return not remaining

    active_rows = [by_id[item] for item in sorted(active)]
    edge_variants = _edge_variants(
        inventory_result=inventory_result,
        active_rows=active_rows,
        active=active,
        node_for_obligation=node_for_obligation,
    )
    plans: list[dict[str, Any]] = []
    signatures: set[str] = set()
    terminal_nodes = frozenset(
        node_id for pair in node_pairs for node_id in pair
    )
    for edges in edge_variants:
        dependencies = [(source, target) for source, target, _ in edges]
        dependencies.extend(
            (antecedent, row["node_id"])
            for row in nodes
            for antecedent in row["antecedent_node_ids"]
        )
        try:
            observation_orders = _topological_orders(
                observation_nodes,
                [
                    (source, target)
                    for source, target in dependencies
                    if source in observation_nodes
                    and target in observation_nodes
                ],
                limit=MAX_DISCOURSE_CANDIDATES,
                prefer_last=terminal_nodes,
            )
            reception_orders = _topological_orders(
                reception_nodes,
                [
                    (source, target)
                    for source, target in dependencies
                    if source in reception_nodes
                    and target in reception_nodes
                ],
                limit=4,
            )
        except DiscourseGraphPlannerError as exc:
            if exc.code == "DISCOURSE_DEPENDENCY_CYCLE":
                continue
            raise Step11PlanningFrontierError(
                "STEP11_TERMINAL_PAIR_DEPENDENCY_INVALID"
            ) from exc
        for observation_order, reception_order in product(
            observation_orders, reception_orders
        ):
            for observation_groups in _partitions(
                observation_order,
                int(budget["observation_sentence_min"]),
                int(budget["observation_sentence_max"]),
            ):
                if (
                    not _partition_valid(
                        observation_groups,
                        node_by_id=node_by_id,
                        required_colocations=frozenset(
                            required_colocations
                        ),
                    )
                    or not _rhetorical_adjacency_valid(
                        observation_groups, edges
                    )
                    or not terminal_pair_layout_valid(observation_groups)
                ):
                    continue
                for reception_groups in _partitions(
                    reception_order,
                    int(budget["reception_sentence_min"]),
                    int(budget["reception_sentence_max"]),
                ):
                    if (
                        len(observation_groups) + len(reception_groups)
                        > int(budget["total_sentence_max"])
                        or not _partition_valid(
                            reception_groups,
                            node_by_id=node_by_id,
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
                    if (
                        plan["structural_signature"] in signatures
                        or validate_discourse_plan(
                            plan,
                            content_plan=content_plan,
                            obligation_ledger=ledger,
                        )
                    ):
                        continue
                    signatures.add(plan["structural_signature"])
                    plans.append(plan)
    if not plans:
        raise Step11PlanningFrontierError(
            "STEP11_TERMINAL_PAIR_NO_SAFE_STRUCTURE"
        )
    selected = _select_candidate_subset(plans)[
        :MAX_DISCOURSE_CANDIDATES
    ]
    return DiscourseGraphPlanSet(
        plans=selected,
        capability=_capability(selected),
    )


def validate_step11_planning_frontier(
    value: Any,
    *,
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
    discourse_plan: Mapping[str, Any],
) -> tuple[str, ...]:
    if type(value) is not Step11PlanningFrontier:
        return ("STEP11_PLANNING_FRONTIER_TYPE_INVALID",)
    try:
        expected = build_step11_planning_frontier(
            inventory_result, content_plan, discourse_plan
        )
    except (Step11PlanningFrontierError, TypeError, ValueError):
        return ("STEP11_PLANNING_FRONTIER_PARENT_REVALIDATION_FAILED",)
    return () if value == expected else ("STEP11_PLANNING_FRONTIER_MISMATCH",)


__all__ = [
    "STEP11_HISTORICAL_RC0021_PLANNING_FRONTIER_SCHEMA",
    "STEP11_HISTORICAL_RC0021_PLANNING_FRONTIER_VERSION",
    "STEP11_HISTORICAL_RC0022_PLANNING_FRONTIER_VERSION",
    "STEP11_HISTORICAL_RC0023_PLANNING_FRONTIER_VERSION",
    "STEP11_PLANNING_FRONTIER_SCHEMA",
    "STEP11_PLANNING_FRONTIER_VERSION",
    "Step11PlanningFrontier",
    "Step11PlanningFrontierError",
    "Step11PlanningIntegration",
    "build_step11_planning_frontier",
    "build_step11_terminal_pair_discourse_plans",
    "step11_planning_frontier_material",
    "validate_step11_planning_frontier",
]
