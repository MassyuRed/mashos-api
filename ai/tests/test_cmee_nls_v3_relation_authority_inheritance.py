# -*- coding: utf-8 -*-
from __future__ import annotations

"""Cross-field relation authority inherited by the unified CMEE plan."""

from dataclasses import replace
from pathlib import Path
from typing import Any, Mapping
import unittest

from emlis_ai_current_input_bundle import build_emlis_current_input_bundle
from emlis_ai_evidence_ledger_service import build_evidence_span_resolver
from emlis_ai_grounded_observation_plan import (
    build_final_stage1_grounded_observation_plan,
    build_grounded_human_reception_plan,
    validate_grounded_human_reception_plan,
)
from cocolon_meaning_experience_engine import emlis_v1a as vertical_module
from cocolon_meaning_experience_engine.contracts import GenerationRequest
from cocolon_meaning_experience_engine.source_kernel import freeze_text_source
from tools.emlis_nls_v3_batch_run import load_validated_batch


_AI_ROOT = Path(__file__).resolve().parents[1]
_GENERATED_ROOT = _AI_ROOT / "tests" / "fixtures" / "emlis_nls_v3" / "generated"
_BATCH_PATH = _GENERATED_ROOT / "batch_001.jsonl"
_MANIFEST_PATH = _GENERATED_ROOT / "batch_001_manifest.json"
_SELECTED_AT = "2026-09-01T00:00:00Z"


def _request(row: Mapping[str, Any]) -> GenerationRequest:
    case_id = str(row["case_id"])
    input_row = row["input"]
    if not isinstance(input_row, Mapping):
        raise TypeError("canonical_input_mapping_required")
    emotions = input_row["emotions"]
    if not isinstance(emotions, list) or any(
        not isinstance(item, Mapping) for item in emotions
    ):
        raise TypeError("canonical_emotions_list_required")
    raw = {
        "id": case_id,
        "created_at": _SELECTED_AT,
        "memo": input_row["thought_text"],
        "memo_action": input_row["action_text"],
        "category": input_row["categories"],
        "emotion_details": emotions,
        "emotions": [str(item["type"]) for item in emotions],
        "is_secret": False,
    }
    return GenerationRequest(
        request_id=f"req-cmee-relation-{case_id}",
        current_input_bundle=build_emlis_current_input_bundle(raw),
        expected_source_record_id=case_id,
    )


class CMEENLSV3RelationAuthorityInheritanceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        rows, manifest = load_validated_batch(_BATCH_PATH, _MANIFEST_PATH)
        if len(rows) != 100 or manifest["case_count"] != 100:
            raise AssertionError("canonical_batch001_exact100_required")
        cls.rows = {str(row["case_id"]): row for row in rows}

    def _plan(self, case_id: str):
        source = freeze_text_source(_request(self.rows[case_id]))
        plan = build_final_stage1_grounded_observation_plan(
            source.normalized_current_input,
            evidence_spans=source.evidence_spans,
        )
        return source, plan

    def _raw_reception(self, source, plan):
        resolver = build_evidence_span_resolver(
            source.evidence_spans,
            current_input=source.normalized_current_input,
        )
        reception_plan = build_grounded_human_reception_plan(
            required=plan.coverage_requirements.human_follow_required,
            human_follow_target_ids=plan.response_plan.human_follow_target_ids,
            primary_nucleus_ids=plan.response_plan.primary_nucleus_ids,
            supporting_nucleus_ids=plan.response_plan.supporting_nucleus_ids,
            required_nucleus_ids=plan.response_plan.required_nucleus_ids,
            fact_boundary_nucleus_ids=plan.response_plan.fact_boundary_nucleus_ids,
            nuclei=plan.nuclei,
            relations=plan.relations,
            safety_kind=plan.safety_policy.safety_kind,
            material_quality=vertical_module.CMEE_RECEPTION_MATERIAL_MODE,
            semantic_complexity=plan.input_profile.semantic_complexity,
        )
        if reception_plan is None:
            raise AssertionError("canonical_reception_plan_required")
        nucleus_index = {row.nucleus_id: row for row in plan.nuclei}
        return resolver, reception_plan, nucleus_index

    def _assert_bounded_relation_keeps_required_endpoints(
        self,
        source,
        plan,
        relation,
    ) -> None:
        required_nuclei = set(plan.coverage_requirements.required_nucleus_ids)
        self.assertEqual(relation.grounding_kind, "bounded_structural_inference")
        self.assertEqual(relation.retention, "should")
        self.assertNotIn(
            relation.relation_id,
            plan.coverage_requirements.required_relation_ids,
        )
        self.assertTrue(
            {relation.from_nucleus_id, relation.to_nucleus_id}.issubset(
                required_nuclei
            )
        )
        self.assertTrue(relation.source_span_ids)
        self.assertTrue(
            set(relation.source_span_ids).issubset(
                set(plan.referenced_evidence_span_ids)
            )
        )
        owners = tuple(
            dict.fromkeys(
                source.meaning_owner_for_span(span_id)
                for span_id in relation.source_span_ids
            )
        )
        self.assertEqual(len(owners), 2)

    def test_structural_action_support_never_becomes_required_source_fact(self) -> None:
        for case_id in ("nls3s_b001_0056", "nls3s_b001_0087"):
            with self.subTest(case_id=case_id):
                source, plan = self._plan(case_id)
                rows = tuple(
                    relation
                    for relation in plan.relations
                    if "source_field_transition:memo_to_memo_action"
                    in relation.source_relation_ids
                    and relation.type == "action_supports_change"
                )
                self.assertTrue(rows)
                for relation in rows:
                    self._assert_bounded_relation_keeps_required_endpoints(
                        source,
                        plan,
                        relation,
                    )

    def test_cross_field_board_conflict_is_not_reclassified_source_explicit(self) -> None:
        for case_id in ("nls3s_b001_0031", "nls3s_b001_0097"):
            with self.subTest(case_id=case_id):
                source, plan = self._plan(case_id)
                relation = next(
                    row
                    for row in plan.relations
                    if "conflict.e1" in row.source_relation_ids
                )
                self._assert_bounded_relation_keeps_required_endpoints(
                    source,
                    plan,
                    relation,
                )
                self.assertEqual(relation.source_relation_ids, ("conflict.e1",))

    def test_connective_inside_one_field_cannot_authorize_cross_field_edge(self) -> None:
        source, plan = self._plan("nls3s_b001_0076")
        nucleus_by_id = {row.nucleus_id: row for row in plan.nuclei}
        span_by_id = {
            str(getattr(row, "span_id", "")): row
            for row in source.evidence_spans
        }
        self.assertTrue(
            any(
                str(getattr(row, "detected_type", "")) == "relation_marker"
                for row in span_by_id.values()
            )
        )
        rows = tuple(
            relation
            for relation in plan.relations
            if set(
                nucleus_by_id[relation.from_nucleus_id].source_fields
            ).isdisjoint(
                set(nucleus_by_id[relation.to_nucleus_id].source_fields)
            )
            and any(
                source_id.startswith("conflict.")
                for source_id in relation.source_relation_ids
            )
        )
        self.assertTrue(rows)
        for relation in rows:
            self._assert_bounded_relation_keeps_required_endpoints(
                source,
                plan,
                relation,
            )

    def test_single_field_explicit_connective_keeps_user_stated_authority(self) -> None:
        _source, plan = self._plan("nls3s_b001_0041")
        relation = next(
            row
            for row in plan.relations
            if any(
                source_id.startswith("evidence_relation_marker:")
                for source_id in row.source_relation_ids
            )
        )
        nucleus_by_id = {row.nucleus_id: row for row in plan.nuclei}
        fields = {
            *nucleus_by_id[relation.from_nucleus_id].source_fields,
            *nucleus_by_id[relation.to_nucleus_id].source_fields,
        }
        self.assertEqual(fields, {"memo"})
        self.assertEqual(relation.grounding_kind, "user_stated_relation")
        self.assertEqual(relation.retention, "required")
        self.assertIn(
            relation.relation_id,
            plan.coverage_requirements.required_relation_ids,
        )

    def test_rr4_selected_move_aggregate_support_is_inherited_exactly(self) -> None:
        accepted = {}
        for case_id in ("nls3s_b001_0020", "nls3s_b001_0091"):
            with self.subTest(case_id=case_id):
                source, plan = self._plan(case_id)
                resolver, reception_plan, nucleus_index = self._raw_reception(
                    source,
                    plan,
                )
                self.assertEqual(
                    validate_grounded_human_reception_plan(
                        reception_plan,
                        expected_target_ids=(
                            plan.response_plan.human_follow_target_ids
                        ),
                        nucleus_index=nucleus_index,
                        resolver=resolver,
                        safety_kind=plan.safety_policy.safety_kind,
                        material_quality=(
                            vertical_module.CMEE_RECEPTION_MATERIAL_MODE
                        ),
                    ),
                    (),
                )
                move_union = tuple(
                    dict.fromkeys(
                        nucleus_id
                        for move in reception_plan.moves
                        for nucleus_id in (
                            *move.target_nucleus_ids,
                            *move.support_nucleus_ids,
                        )
                    )
                )
                expected_support = tuple(
                    nucleus_id
                    for nucleus_id in move_union
                    if nucleus_id
                    not in set(reception_plan.target_nucleus_ids)
                )
                self.assertEqual(
                    reception_plan.support_nucleus_ids,
                    expected_support,
                )
                self.assertTrue(
                    vertical_module._cmee_rr4_aggregate_support_exact(
                        reception_plan,
                        nucleus_index=nucleus_index,
                    )
                )
                self.assertEqual(
                    vertical_module._cmee_semantic_reception_plan(
                        plan,
                        resolver,
                    ),
                    reception_plan,
                )
                accepted[case_id] = (
                    reception_plan,
                    nucleus_index,
                    resolver,
                    plan,
                )

        multi_support, multi_index, _, _ = accepted["nls3s_b001_0091"]
        reordered = replace(
            multi_support,
            support_nucleus_ids=tuple(
                reversed(multi_support.support_nucleus_ids)
            ),
        )
        self.assertFalse(
            vertical_module._cmee_rr4_aggregate_support_exact(
                reordered,
                nucleus_index=multi_index,
            )
        )

        plan_0020, index_0020, resolver_0020, owner_0020 = accepted[
            "nls3s_b001_0020"
        ]
        corrupted_move = replace(
            plan_0020.moves[0],
            source_evidence_span_ids=plan_0020.moves[1].source_evidence_span_ids,
        )
        owner_invalid = replace(
            plan_0020,
            moves=(corrupted_move, *plan_0020.moves[1:]),
        )
        self.assertTrue(
            validate_grounded_human_reception_plan(
                owner_invalid,
                expected_target_ids=owner_0020.response_plan.human_follow_target_ids,
                nucleus_index=index_0020,
                resolver=resolver_0020,
                safety_kind=owner_0020.safety_policy.safety_kind,
                material_quality=vertical_module.CMEE_RECEPTION_MATERIAL_MODE,
            )
        )


if __name__ == "__main__":
    unittest.main()
