# -*- coding: utf-8 -*-
from __future__ import annotations

"""Final-only CMEE inheritance for the current SX exact8 meaning shapes."""

from dataclasses import asdict
import hashlib
import json
import unittest
from unittest.mock import patch

import emlis_ai_grounded_observation_plan as observation_plan_module
from emlis_ai_current_input_bundle import build_emlis_current_input_bundle
from emlis_ai_evidence_ledger_service import (
    build_evidence_ledger,
    build_evidence_span_resolver,
)
from emlis_ai_grounded_observation_plan import (
    FINAL_STAGE1_GROUNDED_PROJECTION_VERSION,
    build_final_stage1_grounded_observation_plan,
    build_grounded_observation_plan,
    validate_grounded_observation_plan,
)
from tools.cmee_v1a_i1sx_candidate_run import EXACT8 as _EXACT8


def _inputs(row):
    case_id, memo, category, emotion, strength = row
    current_input = build_emlis_current_input_bundle(
        {
            "record_id": case_id,
            "memo": memo,
            "category": [category],
            "emotion_details": [{"type": emotion, "strength": strength}],
            "emotions": [emotion],
            "is_secret": False,
        }
    )
    spans = tuple(build_evidence_ledger(current_input))
    resolver = build_evidence_span_resolver(
        spans,
        current_input=current_input,
    )
    return current_input, spans, resolver


def _plans(row):
    current_input, spans, resolver = _inputs(row)
    active = build_grounded_observation_plan(
        current_input,
        evidence_spans=spans,
    )
    final = build_final_stage1_grounded_observation_plan(
        current_input,
        evidence_spans=spans,
    )
    return active, final, spans, resolver


_EXPECTED_REQUIRED_MEANING = {
    "SX-01": {("reaction", "feeling"), ("wish", "wish")},
    "SX-02": {("wish", "wish"), ("constraint", "constraint")},
    "SX-03": {
        ("event", "event"),
        ("wish", "wish"),
        ("reaction", "residue"),
    },
    "SX-04": {
        ("state", "feeling"),
        ("wish", "wish"),
        ("constraint", "uncertainty"),
    },
    "SX-05": {("wish", "wish"), ("constraint", "constraint")},
    "SX-06": {
        ("wish", "wish"),
        ("constraint", "constraint"),
        ("reaction", "feeling"),
        ("uncertainty", "open_deliberation"),
    },
    "SX-07": {("reaction", "feeling"), ("wish", "wish")},
    "SX-08": {
        ("reaction", "feeling"),
        ("action", "action"),
        ("change", "change"),
    },
}

_EXPECTED_REQUIRED_RELATIONS = {
    "SX-01": {"preserves_despite"},
    "SX-02": {"wish_and_constraint"},
    "SX-03": {"temporal_before_after", "coexistence"},
    "SX-04": {"wish_and_constraint"},
    "SX-05": {"wish_and_constraint"},
    "SX-06": {"wish_and_constraint", "coexistence"},
    "SX-07": {"contrast", "continuation_or_refusal"},
    "SX-08": {"action_supports_change", "contrast"},
}


def _check_final_stage1_exact8_keeps_required_meaning_and_relation_coverage(row) -> None:
    active, final, spans, resolver = _plans(row)
    case_id = row[0]
    text_span_ids = {
        span.span_id
        for span in spans
        if span.source_field in {"memo", "memo_action"}
    }
    required_text_nuclei = tuple(
        nucleus
        for nucleus in final.nuclei
        if nucleus.retention == "required"
        and set(nucleus.source_span_ids) & text_span_ids
        and nucleus.kind != "other_explicit"
    )
    actual_meaning = {
        (nucleus.kind, nucleus.semantic_frame.predicate_kind)
        for nucleus in required_text_nuclei
    }
    required_relations = {
        relation.type
        for relation in final.relations
        if relation.retention == "required"
    }

    assert _EXPECTED_REQUIRED_MEANING[case_id] <= actual_meaning
    assert _EXPECTED_REQUIRED_RELATIONS[case_id] <= required_relations
    assert set(final.coverage_requirements.required_nucleus_ids) == {
        nucleus.nucleus_id
        for nucleus in final.nuclei
        if nucleus.retention == "required"
    }
    assert set(final.coverage_requirements.required_relation_ids) == {
        relation.relation_id
        for relation in final.relations
        if relation.retention == "required"
    }
    assert final.input_profile.material_quality == "grounded"
    assert final.input_profile.semantic_complexity == "multi"
    assert FINAL_STAGE1_GROUNDED_PROJECTION_VERSION in final.source_contracts
    assert FINAL_STAGE1_GROUNDED_PROJECTION_VERSION not in active.source_contracts
    assert validate_grounded_observation_plan(final, resolver) == ()


def _check_final_stage1_compound_children_keep_nonempty_exact_source_fragments(row) -> None:
    _active, final, spans, _resolver = _plans(row)
    span_text = {span.span_id: span.raw_text for span in spans}
    action_change_endpoint_ids = {
        nucleus_id
        for relation in final.relations
        if relation.type == "action_supports_change"
        and relation.source_relation_ids
        == ("typed_projection:perfective_action_before_bounded_change",)
        for nucleus_id in (
            relation.from_nucleus_id,
            relation.to_nucleus_id,
        )
    }
    compound = tuple(
        nucleus
        for nucleus in final.nuclei
        if "semantic_role:final_stage1_compound_meaning"
        in nucleus.semantic_frame.attribute_codes
        or nucleus.nucleus_id in action_change_endpoint_ids
    )
    assert len(compound) >= 2
    for nucleus in compound:
        assert len(nucleus.source_span_ids) == 1
        range_codes = tuple(
            code
            for code in nucleus.semantic_frame.attribute_codes
            if code.startswith("source_fragment_scalar_range:")
        )
        assert len(range_codes) == 1
        assert (
            nucleus.semantic_frame.attribute_codes.count(
                "semantic_role:generic_relation_fragment"
            )
            == 1
        )
        assert (
            nucleus.semantic_frame.attribute_codes.count(
                "semantic_role:final_stage1_compound_meaning"
            )
            == 1
        )
        assert (
            nucleus.semantic_frame.attribute_codes.count(
                "source_fragment_scalar_source:normalized_raw_text"
            )
            == 1
        )
        assert not any(
            code.startswith(("surface_scalar_range:", "surface_scalar_source:"))
            for code in nucleus.semantic_frame.attribute_codes
        )
        _prefix, start_text, end_text = range_codes[0].rsplit(":", 2)
        start = int(start_text)
        end = int(end_text)
        source = span_text[nucleus.source_span_ids[0]]
        assert 0 <= start < end <= len(source)
        assert source[start:end].strip(" 、,。．.!！?？")


def _check_final_stage1_reception_binds_target_attention_and_relation_reason(row) -> None:
    _active, final, _spans, _resolver = _plans(row)
    reception = final.response_plan.human_reception_plan
    assert reception is not None
    assert reception.moves
    relation_endpoints = {
        frozenset((relation.from_nucleus_id, relation.to_nucleus_id))
        for relation in final.relations
        if relation.retention in {"required", "should"}
    }
    for move in reception.moves:
        assert move.target_nucleus_ids
        assert move.support_nucleus_ids
        assert move.source_evidence_span_ids
        assert move.surface_strategy in {
            "emlis_attention_first",
            "referent_significance_first",
            "felt_response_first",
            "quiet_referent_first",
        }
        assert any(
            frozenset((target_id, support_id)) in relation_endpoints
            for target_id in move.target_nucleus_ids
            for support_id in move.support_nucleus_ids
        )


def _check_final_stage1_explicit_unknown_is_source_bound_and_hedged(row) -> None:
    _active, final, _spans, _resolver = _plans(row)
    explicit = tuple(
        boundary
        for boundary in final.unknown_boundaries
        if boundary.dimension == "source_explicit_epistemic_limit"
    )
    assert explicit
    assert all(boundary.surface_policy == "hedge_only" for boundary in explicit)
    assert all(boundary.evidence_span_ids for boundary in explicit)
    unknown_ids = {
        nucleus.nucleus_id
        for nucleus in final.nuclei
        if nucleus.semantic_frame.modality == "uncertain"
    }
    assert unknown_ids == {
        nucleus_id
        for boundary in explicit
        for nucleus_id in boundary.affected_nucleus_ids
    }


def _plan_sha256(plan) -> str:
    payload = json.dumps(
        asdict(plan),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _check_sx04_uncertain_block_keeps_burden_and_unknown_duties() -> None:
    row = next(row for row in _EXACT8 if row[0] == "SX-04")
    current_input, spans, _resolver = _inputs(row)
    active_before = build_grounded_observation_plan(
        current_input,
        evidence_spans=spans,
    )
    final = build_final_stage1_grounded_observation_plan(
        current_input,
        evidence_spans=spans,
    )
    active_after = build_grounded_observation_plan(
        current_input,
        evidence_spans=spans,
    )
    assert _plan_sha256(active_after) == _plan_sha256(active_before)

    relation = next(
        relation
        for relation in final.relations
        if relation.type == "wish_and_constraint"
        and relation.retention == "required"
    )
    nucleus_index = {nucleus.nucleus_id: nucleus for nucleus in final.nuclei}
    direction = nucleus_index[relation.from_nucleus_id]
    burden = nucleus_index[relation.to_nucleus_id]
    burden_codes = set(burden.semantic_frame.attribute_codes)
    assert direction.kind == "wish"
    assert burden.kind == "constraint"
    assert burden.semantic_frame.predicate_kind == "uncertainty"
    assert burden.semantic_frame.modality == "uncertain"
    assert {
        "operator:uncertainty",
        "semantic_role:limiting_unknown",
        "semantic_role:burden",
        "semantic_role:generic_relation_fragment",
    } <= burden_codes
    assert sum(
        code.startswith("source_fragment_scalar_range:")
        for code in burden_codes
    ) == 1
    assert relation.relation_id in (
        final.coverage_requirements.required_relation_ids
    )
    explicit = tuple(
        boundary
        for boundary in final.unknown_boundaries
        if boundary.dimension == "source_explicit_epistemic_limit"
        and burden.nucleus_id in boundary.affected_nucleus_ids
    )
    assert len(explicit) == 1
    assert explicit[0].surface_policy == "hedge_only"
    assert explicit[0].evidence_span_ids == burden.source_span_ids


def _check_active_production_builder_never_enters_final_compound_projection() -> None:
    current_input, spans, _resolver = _inputs(_EXACT8[0])
    baseline = build_grounded_observation_plan(
        current_input,
        evidence_spans=spans,
    )
    with patch.object(
        observation_plan_module,
        "_final_stage1_compound_meaning_projections_for_span",
        side_effect=AssertionError("final projection entered active production"),
    ):
        active = build_grounded_observation_plan(
            current_input,
            evidence_spans=spans,
        )
    assert active == baseline
    assert len(active.nuclei) == len(spans)
    assert not any(
        "semantic_role:final_stage1_compound_meaning"
        in nucleus.semantic_frame.attribute_codes
        for nucleus in active.nuclei
    )


class FinalStage1Exact8MeaningInheritanceTest(unittest.TestCase):
    def test_final_stage1_exact8_keeps_required_meaning_and_relation_coverage(
        self,
    ) -> None:
        for row in _EXACT8:
            with self.subTest(case_id=row[0]):
                _check_final_stage1_exact8_keeps_required_meaning_and_relation_coverage(
                    row
                )

    def test_final_stage1_compound_children_keep_exact_source_fragments(
        self,
    ) -> None:
        for row in (row for row in _EXACT8 if row[0] != "SX-07"):
            with self.subTest(case_id=row[0]):
                _check_final_stage1_compound_children_keep_nonempty_exact_source_fragments(
                    row
                )

    def test_final_stage1_reception_binds_target_attention_and_reason(
        self,
    ) -> None:
        for row in _EXACT8:
            with self.subTest(case_id=row[0]):
                _check_final_stage1_reception_binds_target_attention_and_relation_reason(
                    row
                )

    def test_final_stage1_explicit_unknown_is_source_bound_and_hedged(
        self,
    ) -> None:
        for row in (row for row in _EXACT8 if row[0] in {"SX-04", "SX-06"}):
            with self.subTest(case_id=row[0]):
                _check_final_stage1_explicit_unknown_is_source_bound_and_hedged(
                    row
                )

    def test_sx04_uncertain_block_keeps_burden_and_unknown_duties(
        self,
    ) -> None:
        _check_sx04_uncertain_block_keeps_burden_and_unknown_duties()

    def test_active_production_builder_never_enters_final_projection(
        self,
    ) -> None:
        _check_active_production_builder_never_enters_final_compound_projection()
