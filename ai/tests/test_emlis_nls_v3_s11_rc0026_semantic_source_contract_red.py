# -*- coding: utf-8 -*-
from __future__ import annotations

"""RED/forward tests for the rc0026 Step 11 source-meaning repair.

The fixtures use invented generic text and body-free semantic rows.  They do
not read Cycle case ids, semantic-contract annotations, or expected answers.
Independent matcher and Hard Gate changes are intentionally outside this
staging file set.
"""

from types import SimpleNamespace
from typing import Any

from emlis_ai_nls_v3_artifact_contract import STANCE_KIND
from emlis_ai_types import EvidenceSpan
import emlis_ai_step11_planning_frontier_v3 as frontier_module
import emlis_ai_step11_runtime_adapter_v3 as runtime_module
import emlis_ai_step11_semantic_overlay_v3 as overlay_module


_GENERIC_BOUNDARY_INPUT: dict[str, Any] = {
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


def _nucleus(
    source_id: str,
    actual_source_id: str,
    *,
    field: str,
    kind: str,
    retention: str = "required",
    required: bool = True,
    grounding_kind: str = "explicit",
) -> SimpleNamespace:
    ordinal = actual_source_id.rsplit("s", 1)[-1]
    return SimpleNamespace(
        source_id=source_id,
        actual_source_id=actual_source_id,
        source_fields=(field,),
        surface_anchor_ids=(f"s{ordinal}",),
        grounding_kind=grounding_kind,
        kind=kind,
        source_predicate_kind=kind,
        modality="reported",
        retention=retention,
        required=required,
    )


def _relation(
    *,
    source_relation_ids: tuple[str, ...] = (
        "source_field_transition:memo_to_memo_action",
    ),
    source_id: str = "relation:transition",
    from_nucleus_id: str = "nucleus:thought",
    to_nucleus_id: str = "nucleus:action",
    required: bool = True,
) -> SimpleNamespace:
    return SimpleNamespace(
        source_id=source_id,
        source_relation_kind="action_supports_change",
        grounding_kind="bounded_structural_inference",
        relation_type="supports_without_guarantee",
        relation_direction="source_to_target",
        from_nucleus_id=from_nucleus_id,
        to_nucleus_id=to_nucleus_id,
        source_relation_ids=source_relation_ids,
        retention="required" if required else "should",
        required=required,
    )


def _parents(current_input: dict[str, Any]):
    normalized = runtime_module.normalize_emlis_current_input(
        dict(current_input)
    )
    spans = tuple(runtime_module.build_evidence_ledger(normalized))
    resolver = runtime_module.build_evidence_span_resolver(
        spans, current_input=normalized
    )
    reports = tuple(runtime_module.run_perspective_observers(spans))
    board = runtime_module.build_perspective_board(
        evidence_spans=spans, reports=reports
    )
    graph = runtime_module.integrate_perspective_board(board=board)
    safety = runtime_module.build_emlis_safety_triage_decision(
        current_input=normalized,
        graph=graph,
        evidence_spans=spans,
    )
    grounded_plan = runtime_module.build_grounded_observation_plan(
        normalized,
        evidence_spans=spans,
        reports=reports,
        board=board,
        graph=graph,
        safety_decision=safety,
    )
    stage = runtime_module.build_observation_stage_context(
        stage="normal_observation",
        original_input_bundle=normalized,
    )
    snapshot = runtime_module.build_grounded_source_snapshot(
        grounded_plan,
        resolver,
        observation_stage_context=stage,
        original_input_bundle=normalized,
    )
    inventory = runtime_module.build_semantic_obligation_inventory(snapshot)
    content_plan = runtime_module.build_content_selection_plan(inventory)
    discourse = runtime_module._build_step11_discourse_plan_set(
        inventory, content_plan
    )
    return inventory, content_plan, discourse


def test_thought_slot_wish_endpoint_is_a_proposition() -> None:
    thought_wish = _nucleus(
        "nucleus:wish",
        "nucleus:s1",
        field="memo",
        kind="wish",
    )
    action_wish = _nucleus(
        "nucleus:action-wish",
        "nucleus:s2",
        field="memo_action",
        kind="wish",
    )
    explicit_thought_action = _nucleus(
        "nucleus:thought-action",
        "nucleus:s3",
        field="memo",
        kind="action",
    )

    assert overlay_module._relation_endpoint_role(thought_wish) == (
        "proposition"
    )
    assert overlay_module._relation_endpoint_role(action_wish) == "action"
    assert overlay_module._relation_endpoint_role(
        explicit_thought_action
    ) == "action"


def test_generic_transition_is_visible_only_as_neutral_copresence() -> None:
    thought = _nucleus(
        "nucleus:thought",
        "nucleus:s1",
        field="memo",
        kind="wish",
    )
    action = _nucleus(
        "nucleus:action",
        "nucleus:s2",
        field="memo_action",
        kind="action",
    )
    relation = _relation()
    inventory = SimpleNamespace(
        source_snapshot=SimpleNamespace(
            nuclei=(thought, action), relations=(relation,)
        )
    )

    projected = overlay_module._overlay_relations(
        inventory,
        frozenset({thought.source_id, action.source_id}),
        active_relation_ids=frozenset({relation.source_id}),
        selected_relation_ids=frozenset({relation.source_id}),
        content_depth="focused",
        projection={},
        anchor_ids_by_nucleus={thought.source_id: (), action.source_id: ()},
        label_anchor_ids_by_nucleus={
            thought.source_id: (),
            action.source_id: (),
        },
        anchor_by_id={},
    )

    assert len(projected) == 1
    visible = projected[0]
    assert visible.relation_type == "coexists_with"
    assert visible.relation_direction == "bidirectional"
    assert visible.evidence_grade == "cross_field_copresence_only"
    assert visible.source_relation_id == relation.source_id
    assert visible.source_relation_kind == "action_supports_change"
    assert visible.required is True
    assert visible.from_endpoint_role == "proposition"
    assert visible.to_endpoint_role == "action"


def test_generic_transition_neutralisation_is_narrow() -> None:
    relation = _relation()
    assert overlay_module._generic_transition_requires_neutral_copresence(
        relation,
        source_slots=("thought",),
        target_slots=("action",),
    )
    marker_backed = _relation(
        source_relation_ids=(
            "source_field_transition:memo_to_memo_action",
            "evidence_relation_marker:s2",
        )
    )
    assert not overlay_module._generic_transition_requires_neutral_copresence(
        marker_backed,
        source_slots=("thought",),
        target_slots=("action",),
    )
    assert not overlay_module._generic_transition_requires_neutral_copresence(
        relation,
        source_slots=("action",),
        target_slots=("thought",),
    )


def test_source_boundary_companions_integrate_nuclei_not_relations() -> None:
    inventory, content_plan, discourse = _parents(_GENERIC_BOUNDARY_INPUT)
    plan = discourse.plans[0]
    frontier = frontier_module.build_step11_planning_frontier(
        inventory, content_plan, plan
    )
    companions = tuple(
        row
        for row in frontier.integrations
        if row.reason_code
        == "source_boundary_clause_companion_integration"
    )
    assert len(companions) == 2

    decision_by_id = {
        row["obligation_id"]: row for row in content_plan["decisions"]
    }
    obligation_by_id = {
        row["obligation_id"]: row
        for row in inventory.ledger["obligations"]
    }
    nucleus_by_id = {
        row.source_id: row for row in inventory.source_snapshot.nuclei
    }
    for integration in companions:
        assert (
            decision_by_id[integration.obligation_id]["status"]
            == "deferred_by_budget"
        )
        assert integration.integrated_into_obligation_id in (
            frontier.base_active_obligation_ids
        )
        assert (
            obligation_by_id[
                integration.integrated_into_obligation_id
            ]["kind"]
            != STANCE_KIND
        )
        assert len(integration.nucleus_ids) == 1
        nucleus = nucleus_by_id[integration.nucleus_ids[0]]
        assert nucleus.retention == "should"
        assert nucleus.required is False
        assert integration.nucleus_ids[0] in frontier.active_nucleus_ids

    base_relation_ids = tuple(
        sorted(
            {
                relation_id
                for obligation_id in frontier.base_active_obligation_ids
                for relation_id in obligation_by_id[obligation_id].get(
                    "relation_ids", ()
                )
            }
        )
    )
    assert frontier.active_relation_ids == base_relation_ids


def test_internal_or_extra_authority_clause_is_not_a_companion() -> None:
    first = _nucleus(
        "n1", "nucleus:s1", field="memo", kind="event"
    )
    internal = _nucleus(
        "n2",
        "nucleus:s2",
        field="memo",
        kind="event",
        retention="should",
        required=False,
    )
    last = _nucleus(
        "n3", "nucleus:s3", field="memo", kind="event"
    )
    internal_relation = SimpleNamespace(
        source_id="r1",
        from_nucleus_id="n2",
        to_nucleus_id="n3",
        source_relation_ids=("whole_input_source_order",),
        retention="should",
        required=False,
    )
    inventory = SimpleNamespace(
        source_snapshot=SimpleNamespace(
            nuclei=(first, internal, last), relations=(internal_relation,)
        )
    )
    by_id = {
        "o1": {
            "kind": "grounded_nucleus_notice",
            "nucleus_ids": ["n1"],
            "relation_ids": [],
            "unknown_boundary_ids": [],
        },
        "o2": {
            "kind": "grounded_nucleus_notice",
            "nucleus_ids": ["n2"],
            "relation_ids": [],
            "unknown_boundary_ids": [],
        },
        "o3": {
            "kind": "grounded_nucleus_notice",
            "nucleus_ids": ["n3"],
            "relation_ids": [],
            "unknown_boundary_ids": [],
        },
    }
    decisions = {
        "o1": {"status": "selected"},
        "o2": {"status": "deferred_by_budget"},
        "o3": {"status": "selected"},
    }
    assert frontier_module._source_boundary_companion_specs(
        inventory,
        by_id=by_id,
        decision_by_id=decisions,
        base_active=frozenset({"o1", "o3"}),
    ) == ()

    boundary = _nucleus(
        "n1",
        "nucleus:s1",
        field="memo",
        kind="event",
        retention="should",
        required=False,
    )
    active = _nucleus(
        "n2", "nucleus:s2", field="memo", kind="event"
    )
    extra_authority_relation = SimpleNamespace(
        source_id="r2",
        from_nucleus_id="n1",
        to_nucleus_id="n2",
        source_relation_ids=(
            "whole_input_source_order",
            "evidence_relation_marker:s9",
        ),
        retention="should",
        required=False,
    )
    extra_inventory = SimpleNamespace(
        source_snapshot=SimpleNamespace(
            nuclei=(boundary, active), relations=(extra_authority_relation,)
        )
    )
    assert frontier_module._source_boundary_companion_specs(
        extra_inventory,
        by_id={"o1": by_id["o1"], "o2": by_id["o2"]},
        decision_by_id={
            "o1": {"status": "deferred_by_budget"},
            "o2": {"status": "selected"},
        },
        base_active=frozenset({"o2"}),
    ) == ()


def test_dependent_relation_residue_trim_is_exact_and_fail_closed() -> None:
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

    assert overlay_module._dependent_relation_residue_end(
        nucleus_id="n2",
        span=dependent,
        spans=(marker, dependent),
        relations=(relation,),
        active_relation_ids=frozenset({"r1"}),
    ) == 2
    assert overlay_module._dependent_relation_residue_end(
        nucleus_id="n2",
        span=dependent,
        spans=(marker, dependent),
        relations=(relation,),
        active_relation_ids=frozenset(),
    ) == 0
    noncontiguous = SimpleNamespace(**vars(marker))
    noncontiguous.end_index = 1
    assert overlay_module._dependent_relation_residue_end(
        nucleus_id="n2",
        span=dependent,
        spans=(noncontiguous, dependent),
        relations=(relation,),
        active_relation_ids=frozenset({"r1"}),
    ) == 0
