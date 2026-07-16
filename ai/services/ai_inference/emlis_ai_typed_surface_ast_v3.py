# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step 7 closed Typed Surface AST builder for NLS v3."""

from typing import Any, Mapping, Sequence

from emlis_ai_content_selection_v3 import validate_content_selection_policy
from emlis_ai_discourse_graph_planner_v3 import build_discourse_graph_plans
from emlis_ai_nls_v3_artifact_contract import (
    AST_SCHEMA,
    STANCE_KIND,
    artifact_sha256,
    derive_content_id,
    validate_discourse_plan,
    validate_surface_ast,
)
from emlis_ai_semantic_obligation_inventory_v3 import (
    SemanticObligationInventoryResult,
    validate_semantic_obligation_inventory,
)
from emlis_ai_surface_grammar_catalog_v3 import (
    validate_surface_grammar_catalog,
)


class TypedSurfaceAstError(ValueError):
    """Fail-closed AST error containing no source body."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


_PREDICATE_FORM = {
    "grounded_nucleus_notice": "nucleus_observed",
    "significance_or_shift": "shift_observed",
    "intention_or_next_action": "action_intended",
    "bounded_counterposition": "bounded_counterposition_observed",
}


def _clause_id(discourse_node_id: str, obligation_id: str) -> str:
    return "cl_" + artifact_sha256(
        {
            "discourse_node_id": discourse_node_id,
            "obligation_id": obligation_id,
        }
    )[:20]


def _validated_parents(
    discourse_plan: Any,
    *,
    inventory_result: Any,
    content_plan: Any,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    if type(inventory_result) is not SemanticObligationInventoryResult:
        raise TypedSurfaceAstError("AST_INVENTORY_RESULT_INVALID")
    ledger = inventory_result.ledger
    if validate_semantic_obligation_inventory(
        ledger, source_snapshot=inventory_result.source_snapshot
    ):
        raise TypedSurfaceAstError("AST_INVENTORY_REVALIDATION_FAILED")
    if type(content_plan) is not dict or validate_content_selection_policy(
        content_plan, inventory_result=inventory_result
    ):
        raise TypedSurfaceAstError("AST_CONTENT_REVALIDATION_FAILED")
    if type(discourse_plan) is not dict or validate_discourse_plan(
        discourse_plan,
        content_plan=content_plan,
        obligation_ledger=ledger,
    ):
        raise TypedSurfaceAstError("AST_DISCOURSE_REVALIDATION_FAILED")
    plan_set = build_discourse_graph_plans(inventory_result, content_plan)
    if discourse_plan not in plan_set.plans:
        raise TypedSurfaceAstError("AST_DISCOURSE_POLICY_MISMATCH")
    if validate_surface_grammar_catalog():
        raise TypedSurfaceAstError("AST_GRAMMAR_CATALOG_INVALID")
    rows = ledger.get("obligations")
    if type(rows) is not list:
        raise TypedSurfaceAstError("AST_LEDGER_SHAPE_INVALID")
    by_id = {
        row.get("obligation_id"): row
        for row in rows
        if type(row) is dict and type(row.get("obligation_id")) is str
    }
    return ledger, by_id


def _semantic_nodes(
    obligation: Mapping[str, Any],
    *,
    incoming_edge_types: Sequence[str],
    target_clause_ids: Sequence[str],
) -> list[dict[str, Any]]:
    kind = obligation.get("kind")
    nodes: list[dict[str, Any]] = [
        {"node_type": "connector", "edge_type": edge_type}
        for edge_type in sorted(set(incoming_edge_types))
    ]
    if kind == STANCE_KIND and len(target_clause_ids) == 1:
        nodes.append(
            {
                "node_type": "grounded_referent",
                "evidence_ids": [],
                "nucleus_ids": [],
                "antecedent_clause_id": target_clause_ids[0],
                "form": "unique_antecedent",
            }
        )
    else:
        evidence_ids = list(obligation.get("evidence_ids") or [])
        nucleus_ids = list(obligation.get("nucleus_ids") or [])
        if not evidence_ids and not nucleus_ids:
            raise TypedSurfaceAstError("AST_GROUNDED_REFERENT_UNAVAILABLE")
        nodes.append(
            {
                "node_type": "grounded_referent",
                "evidence_ids": evidence_ids,
                "nucleus_ids": nucleus_ids,
                "antecedent_clause_id": None,
                "form": "semantic_phrase",
            }
        )
    if kind in _PREDICATE_FORM:
        nodes.append(
            {
                "node_type": "observation_predicate",
                "form": _PREDICATE_FORM[kind],
            }
        )
    elif kind == "grounded_relation_preservation":
        relation_ids = obligation.get("relation_ids") or []
        directions = obligation.get("relation_directions") or []
        if len(relation_ids) != 1 or len(directions) != 1:
            raise TypedSurfaceAstError("AST_RELATION_BINDING_AMBIGUOUS")
        direction = directions[0]
        if (
            type(direction) is not dict
            or direction.get("relation_id") != relation_ids[0]
        ):
            raise TypedSurfaceAstError("AST_RELATION_BINDING_INVALID")
        nodes.append(
            {
                "node_type": "grounded_relation",
                "relation_id": relation_ids[0],
                "direction": direction.get("direction"),
            }
        )
    elif kind == "unknown_boundary_preservation":
        unknowns = list(obligation.get("unknown_boundary_ids") or [])
        if not unknowns:
            raise TypedSurfaceAstError("AST_UNKNOWN_BINDING_REQUIRED")
        nodes.append(
            {
                "node_type": "unknown_boundary",
                "unknown_boundary_ids": unknowns,
                "form": "preserve_unknown",
            }
        )
    elif kind == "self_denial_boundary":
        nodes.append(
            {
                "node_type": "self_denial_boundary",
                "form": "separate_claim_from_observation",
            }
        )
    elif kind == STANCE_KIND:
        acts = obligation.get("allowed_response_acts") or []
        targets = obligation.get("target_obligation_ids") or []
        if len(acts) != 1 or not targets:
            raise TypedSurfaceAstError("AST_STANCE_BINDING_INVALID")
        nodes.append(
            {
                "node_type": "emlis_stance",
                "target_obligation_ids": list(targets),
                "form": acts[0],
            }
        )
    else:
        raise TypedSurfaceAstError("AST_OBLIGATION_KIND_UNSUPPORTED")
    nodes.append(
        {
            "node_type": "modality",
            "modality": obligation.get("modality"),
        }
    )
    return nodes


def _terminal(obligations: Sequence[Mapping[str, Any]]) -> str:
    kinds = {row.get("kind") for row in obligations}
    modalities = {row.get("modality") for row in obligations}
    if "unknown_boundary_preservation" in kinds or "unknown" in modalities:
        return "plain_unknown"
    if "intention_or_next_action" in kinds or "intended" in modalities:
        return "plain_intended"
    if kinds & {"self_denial_boundary", "bounded_counterposition", STANCE_KIND}:
        return "plain_restrained"
    return "plain_bounded"


def _build(
    discourse_plan: Mapping[str, Any],
    *,
    by_id: Mapping[str, dict[str, Any]],
) -> dict[str, Any]:
    discourse_nodes = {
        row["node_id"]: row for row in discourse_plan["nodes"]
    }
    clause_by_node = {
        node_id: _clause_id(node_id, row["obligation_id"])
        for node_id, row in discourse_nodes.items()
    }
    incoming_by_node: dict[str, list[str]] = {
        node_id: [] for node_id in discourse_nodes
    }
    for edge in discourse_plan["edges"]:
        incoming_by_node[edge["to"]].append(edge["type"])
    sections: list[dict[str, Any]] = []
    for role in ("observation", "reception"):
        sentences: list[dict[str, Any]] = []
        for group in discourse_plan["sentence_groups"]:
            if group["section_role"] != role:
                continue
            clauses: list[dict[str, Any]] = []
            sentence_obligations: list[dict[str, Any]] = []
            for node_id in group["node_ids"]:
                discourse_node = discourse_nodes[node_id]
                obligation = by_id[discourse_node["obligation_id"]]
                target_clause_ids = [
                    clause_by_node[_node_id]
                    for target in obligation.get("target_obligation_ids", [])
                    for _node_id, target_node in discourse_nodes.items()
                    if target_node["obligation_id"] == target
                ]
                clauses.append(
                    {
                        "clause_id": clause_by_node[node_id],
                        "discourse_node_id": node_id,
                        "obligation_id": obligation["obligation_id"],
                        "nodes": _semantic_nodes(
                            obligation,
                            incoming_edge_types=incoming_by_node[node_id],
                            target_clause_ids=target_clause_ids,
                        ),
                    }
                )
                sentence_obligations.append(obligation)
            sentences.append(
                {
                    "clauses": clauses,
                    "terminal": _terminal(sentence_obligations),
                }
            )
        sections.append({"role": role, "sentences": sentences})
    ast: dict[str, Any] = {
        "schema_version": AST_SCHEMA,
        "surface_ast_id": "nls3ast_0000000000000000",
        "source_discourse_plan_sha256": artifact_sha256(discourse_plan),
        "sections": sections,
        "body_free": True,
    }
    ast["surface_ast_id"] = derive_content_id(
        "nls3ast_", ast, "surface_ast_id"
    )
    return ast


def build_typed_surface_ast(
    discourse_plan: Mapping[str, Any],
    *,
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
) -> dict[str, Any]:
    """Build the sole closed AST for one validated discourse candidate."""

    ledger, by_id = _validated_parents(
        discourse_plan,
        inventory_result=inventory_result,
        content_plan=content_plan,
    )
    ast = _build(discourse_plan, by_id=by_id)
    if validate_surface_ast(
        ast,
        discourse_plan=discourse_plan,
        obligation_ledger=ledger,
    ):
        raise TypedSurfaceAstError("AST_CONTRACT_REJECTED")
    if validate_typed_surface_ast(
        ast,
        discourse_plan=discourse_plan,
        inventory_result=inventory_result,
        content_plan=content_plan,
    ):
        raise TypedSurfaceAstError("AST_POLICY_REJECTED")
    return ast


def validate_typed_surface_ast(
    value: Any,
    *,
    discourse_plan: Mapping[str, Any],
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
) -> tuple[str, ...]:
    """Rebuild and compare every node; arbitrary text nodes cannot enter."""

    try:
        ledger, by_id = _validated_parents(
            discourse_plan,
            inventory_result=inventory_result,
            content_plan=content_plan,
        )
        expected = _build(discourse_plan, by_id=by_id)
    except (TypedSurfaceAstError, KeyError, TypeError, ValueError):
        return ("AST_PARENT_REVALIDATION_FAILED",)
    issues: list[str] = []
    if type(value) is not dict or value != expected:
        issues.append("AST_CONTENT_MISMATCH")
    if type(value) is dict and validate_surface_ast(
        value,
        discourse_plan=discourse_plan,
        obligation_ledger=ledger,
    ):
        issues.append("AST_CONTRACT_REJECTED")
    serialized = str(value)
    for forbidden in (
        "final_text",
        "expected_sentence",
        "case_id",
        "family_id",
        "batch_id",
        "username",
    ):
        if forbidden in serialized:
            issues.append("AST_ARBITRARY_OR_FIXTURE_TEXT_FORBIDDEN")
    return tuple(sorted(set(issues)))


__all__ = [
    "TypedSurfaceAstError",
    "build_typed_surface_ast",
    "validate_typed_surface_ast",
]
