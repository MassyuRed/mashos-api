# -*- coding: utf-8 -*-
from __future__ import annotations

"""Process-local Development runner for Natural Language Surface v2 Steps 6/7.

Only the frozen 42-case Development cohort is imported.  Candidate and
selected bodies stay in memory; the receipt helper returns body-free metadata.
"""

from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from helpers.emlis_nls_v2_s2_development import EvaluationCase, load_development_cases
from emlis_ai_evidence_ledger_service import (
    EvidenceSpanResolver,
    build_evidence_ledger,
    build_evidence_span_resolver,
)
from emlis_ai_grounded_human_reception_v2 import (
    ReceptionSurfaceCandidateSetV2,
    ReceptionSurfaceCandidateV2,
    generate_reception_surface_candidates_v2,
)
from emlis_ai_grounded_observation_plan import GroundedObservationPlan, build_grounded_observation_plan
from emlis_ai_grounded_reception_candidate_plan_v2 import (
    ReceptionCandidatePlanSetV2,
    build_reception_candidate_plans_v2,
)
from emlis_ai_grounded_reception_candidate_selector_v2 import (
    ReceptionCandidateSelectionV2,
    evaluate_and_select_reception_candidate_v2,
    resolve_selected_reception_surface_v2,
)
from emlis_ai_grounded_reception_content_plan_v2 import (
    ReceptionContentPlanV2,
    build_reception_content_plan_v2,
)


@dataclass(frozen=True)
class DevelopmentSelectionRow:
    case: EvaluationCase
    observation_plan: GroundedObservationPlan
    content_plan: ReceptionContentPlanV2
    candidate_plan_set: ReceptionCandidatePlanSetV2
    resolver: EvidenceSpanResolver
    surface_candidate_set: ReceptionSurfaceCandidateSetV2
    selection: ReceptionCandidateSelectionV2
    selected_surface: ReceptionSurfaceCandidateV2


@lru_cache(maxsize=1)
def load_development_selection_rows() -> tuple[DevelopmentSelectionRow, ...]:
    rows: list[DevelopmentSelectionRow] = []
    for case in load_development_cases():
        observation_plan = build_grounded_observation_plan(case.current_input)
        content_plan = build_reception_content_plan_v2(observation_plan)
        candidate_plan_set = build_reception_candidate_plans_v2(content_plan)
        resolver = build_evidence_span_resolver(
            tuple(build_evidence_ledger(case.current_input)),
            current_input=case.current_input,
        )
        surface_candidate_set = generate_reception_surface_candidates_v2(
            observation_plan,
            content_plan,
            candidate_plan_set,
            resolver,
        )
        selection = evaluate_and_select_reception_candidate_v2(
            observation_plan,
            content_plan,
            candidate_plan_set,
            surface_candidate_set,
            resolver,
        )
        selected_surface = resolve_selected_reception_surface_v2(
            selection,
            surface_candidate_set,
        )
        rows.append(
            DevelopmentSelectionRow(
                case=case,
                observation_plan=observation_plan,
                content_plan=content_plan,
                candidate_plan_set=candidate_plan_set,
                resolver=resolver,
                surface_candidate_set=surface_candidate_set,
                selection=selection,
                selected_surface=selected_surface,
            )
        )
    return tuple(rows)


def body_free_development_receipt() -> list[dict[str, Any]]:
    return [
        {
            "case_id": row.case.case_id,
            "family": row.case.family,
            "content_plan_id": row.content_plan.plan_id,
            "depth": row.content_plan.depth,
            "candidate_count": len(row.candidate_plan_set.candidates),
            "selection_meta": row.selection.as_body_free_meta(),
        }
        for row in load_development_selection_rows()
    ]


def development_distribution() -> dict[str, Any]:
    rows = load_development_selection_rows()
    strategies: Counter[str] = Counter()
    terminals: Counter[str] = Counter()
    predicates: Counter[str] = Counter()
    skeletons: Counter[str] = Counter()
    depths: Counter[str] = Counter()
    texts: Counter[str] = Counter()
    rich_single_sentence = 0
    short_meaningless_inflation = 0

    for row in rows:
        surface = row.selected_surface
        candidate = next(
            item
            for item in row.candidate_plan_set.candidates
            if item.candidate_id == row.selection.selected_candidate_id
        )
        variation = candidate.variation_signature
        strategies[candidate.strategy_code] += 1
        terminals[variation.terminal_family] += 1
        predicates.update(surface.predicate_families)
        skeletons[
            "|".join(
                (
                    candidate.strategy_code,
                    variation.opening,
                    variation.speaker_presence,
                    variation.connection,
                    variation.terminal_family,
                    str(surface.sentence_count),
                )
            )
        ] += 1
        depths[row.content_plan.depth] += 1
        texts[surface.text] += 1
        rich_single_sentence += bool(
            row.content_plan.depth in {"focused", "layered"}
            and surface.sentence_count == 1
        )
        short_meaningless_inflation += bool(
            row.content_plan.depth == "minimal" and surface.sentence_count > 1
        )

    selected_count = len(rows)
    predicate_total = sum(predicates.values())

    def max_share(counter: Counter[str], denominator: int) -> float:
        return round(max(counter.values(), default=0) / max(1, denominator), 6)

    return {
        "case_count": selected_count,
        "selected_count": sum(row.selection.status == "selected" for row in rows),
        "depth_counts": dict(sorted(depths.items())),
        "exact_duplicate_count": sum(count - 1 for count in texts.values() if count > 1),
        "rich_single_sentence_count": rich_single_sentence,
        "short_meaningless_inflation_count": short_meaningless_inflation,
        "strategy_counts": dict(sorted(strategies.items())),
        "terminal_family_counts": dict(sorted(terminals.items())),
        "predicate_family_counts": dict(sorted(predicates.items())),
        "skeleton_counts": dict(sorted(skeletons.items())),
        "max_strategy_share": max_share(strategies, selected_count),
        "max_terminal_family_share": max_share(terminals, selected_count),
        "max_predicate_family_share": max_share(predicates, predicate_total),
        "max_skeleton_share": max_share(skeletons, selected_count),
    }


__all__ = [
    "DevelopmentSelectionRow",
    "load_development_selection_rows",
    "body_free_development_receipt",
    "development_distribution",
]
