# -*- coding: utf-8 -*-
from __future__ import annotations

"""Independent matcher coverage for the rc0026 semantic source repair."""

from dataclasses import replace
from types import SimpleNamespace
from typing import Any

import pytest

from emlis_ai_types import EvidenceSpan
import emlis_ai_step11_natural_surface_matcher_v3 as matcher
import emlis_ai_step11_natural_surface_v3 as surface
import emlis_ai_step11_planning_frontier_v3 as frontier_module
import emlis_ai_step11_runtime_adapter_v3 as runtime


_GENERIC_INPUT: dict[str, Any] = {
    "thought_text": (
        "前の準備に助けられた。"
        "今日は自分のペースを守りたいと思っている。"
    ),
    "action_text": (
        "確認した項目だけを紙に書いた。"
        "残りはまだ触れていない。"
    ),
    "emotions": [{"type": "平穏", "strength": "medium"}],
    "categories": ["生活"],
}


@pytest.fixture(scope="module")
def generic_execution():
    return runtime.execute_step11_offline_v3(
        _GENERIC_INPUT,
        candidate_version_id=surface.STEP11_CANDIDATE_VERSION_ID,
        source_dependency_closure_sha256="8" * 64,
    )


def test_matcher_accepts_the_independently_recomputed_semantic_contract(
    generic_execution,
) -> None:
    assert generic_execution.status == "selected"
    candidate = generic_execution.selected_candidate
    assert candidate is not None
    witness = matcher.parse_step11_natural_surface(
        candidate.rendered_surface.utf8_bytes
    )
    binding = matcher.match_step11_natural_surface(
        witness,
        inventory_result=generic_execution.inventory_result,
        content_plan=generic_execution.content_plan,
        discourse_plan=candidate.discourse_plan,
        current_input=generic_execution.projected_current_input,
    )

    assert binding.verified is True
    assert binding.issue_codes == ()


def test_matcher_recomputes_transition_and_thought_wish_roles(
    generic_execution,
) -> None:
    snapshot = generic_execution.inventory_result.source_snapshot
    transition = next(
        row
        for row in snapshot.relations
        if "source_field_transition:memo_to_memo_action"
        in row.source_relation_ids
        and row.source_relation_kind == "action_supports_change"
    )
    assert matcher._independent_generic_transition_requires_neutral_copresence(
        transition,
        source_slots=("thought",),
        target_slots=("action",),
    )
    forged = replace(
        transition,
        source_relation_ids=(
            *transition.source_relation_ids,
            "evidence_relation_marker:s999",
        ),
    )
    assert not (
        matcher._independent_generic_transition_requires_neutral_copresence(
            forged,
            source_slots=("thought",),
            target_slots=("action",),
        )
    )
    thought_wish = SimpleNamespace(
        source_fields=("memo",),
        kind="wish",
        source_predicate_kind="wish",
        modality="intended",
    )
    assert matcher._independent_endpoint_role(thought_wish) == "proposition"


def test_matcher_rejects_a_missing_source_boundary_companion(
    generic_execution,
) -> None:
    candidate = generic_execution.selected_candidate
    assert candidate is not None
    frontier = frontier_module.build_step11_planning_frontier(
        generic_execution.inventory_result,
        generic_execution.content_plan,
        candidate.discourse_plan,
    )
    companions = tuple(
        row
        for row in frontier.integrations
        if row.reason_code == "source_boundary_clause_companion_integration"
    )
    assert companions
    by_id = {
        row["obligation_id"]: row
        for row in generic_execution.inventory_result.ledger["obligations"]
    }
    arguments = {
        "snapshot": generic_execution.inventory_result.source_snapshot,
        "by_id": by_id,
        "content_plan": generic_execution.content_plan,
        "discourse_plan": candidate.discourse_plan,
    }
    assert matcher._independent_source_boundary_companion_contract(
        planning_frontier=frontier,
        **arguments,
    ) == ()

    forged = replace(
        frontier,
        integrations=tuple(
            row
            for row in frontier.integrations
            if row.reason_code
            != "source_boundary_clause_companion_integration"
        ),
    )
    assert (
        "S11_MATCH_BOUNDARY_COMPANION_CONTRACT_MISMATCH"
        in matcher._independent_source_boundary_companion_contract(
            planning_frontier=forged,
            **arguments,
        )
    )


def test_matcher_trims_only_an_active_contiguous_relation_residue() -> None:
    marker = EvidenceSpan(
        span_id="s1",
        raw_text="一方",
        start_index=0,
        end_index=2,
        detected_type="relation_marker",
        source_field="memo",
    )
    dependent = EvidenceSpan(
        span_id="s2",
        raw_text="で、別の側面も残っている",
        start_index=2,
        end_index=14,
        detected_type="event",
        source_field="memo",
    )
    relation = SimpleNamespace(
        source_id="r1",
        from_nucleus_id="n1",
        to_nucleus_id="n2",
        source_relation_ids=(
            "evidence_relation_marker:s1",
            "whole_input_source_order",
        ),
    )

    assert matcher._independent_dependent_relation_residue_end(
        nucleus_id="n2",
        span=dependent,
        spans=(marker, dependent),
        relations=(relation,),
        active_relation_ids=frozenset({"r1"}),
    ) == (2, ())
    assert matcher._independent_dependent_relation_residue_end(
        nucleus_id="n2",
        span=dependent,
        spans=(marker, dependent),
        relations=(relation,),
        active_relation_ids=frozenset(),
    ) == (0, ())
    noncontiguous = SimpleNamespace(**vars(marker))
    noncontiguous.end_index = 1
    assert matcher._independent_dependent_relation_residue_end(
        nucleus_id="n2",
        span=dependent,
        spans=(noncontiguous, dependent),
        relations=(relation,),
        active_relation_ids=frozenset({"r1"}),
    ) == (0, ())
