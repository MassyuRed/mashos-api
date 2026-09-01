# -*- coding: utf-8 -*-
from __future__ import annotations

"""V2-final bounded exclusive-focus lexical-role inheritance."""

import json
from dataclasses import replace
from pathlib import Path
from typing import Any, Mapping
import unittest

from emlis_ai_current_input_bundle import build_emlis_current_input_bundle
from emlis_ai_grounded_observation_plan import (
    FINAL_STAGE1_GROUNDED_PROJECTION_VERSION,
    build_final_stage1_grounded_observation_plan,
)
from cocolon_meaning_experience_engine.contracts import (
    CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1,
    CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2,
    GenerationRequest,
)
import cocolon_meaning_experience_engine.emlis_v1a as vertical
from cocolon_meaning_experience_engine.emlis_v1a import (
    CMEEVerticalError,
    _build_graph,
    _cmee_assert_current_first_person_scope_supported,
    _cmee_bounded_exclusive_focus_role,
    _cmee_frozen_lexical_role_surface,
    _ordered,
    _planned_visible_source_ids,
)
from cocolon_meaning_experience_engine.source_kernel import freeze_text_source


_AI_ROOT = Path(__file__).resolve().parents[1]
_BATCH_PATH = (
    _AI_ROOT
    / "tests"
    / "fixtures"
    / "emlis_nls_v3"
    / "generated"
    / "batch_001.jsonl"
)
_MANIFEST_PATH = _BATCH_PATH.with_name("batch_001_manifest.json")
_SELECTED_AT = "2026-09-01T00:00:00Z"
_TARGET_CASE_ID = "nls3s_b001_0060"
_EXPECTED_ROLE = "疲れから離れられる安心しか見えていなかった"


def _request_from_row(row: Mapping[str, Any]) -> GenerationRequest:
    input_row = row["input"]
    emotions = input_row["emotions"]
    case_id = str(row["case_id"])
    return GenerationRequest(
        request_id=f"req-exclusive-focus-{case_id}",
        current_input_bundle=build_emlis_current_input_bundle(
            {
                "id": case_id,
                "created_at": _SELECTED_AT,
                "memo": input_row["thought_text"],
                "memo_action": input_row["action_text"],
                "category": input_row["categories"],
                "emotion_details": emotions,
                "emotions": [str(item["type"]) for item in emotions],
                "is_secret": False,
            }
        ),
        expected_source_record_id=case_id,
    )


class CMEEV2ExclusiveFocusLexicalRoleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        rows = tuple(
            json.loads(line)
            for line in _BATCH_PATH.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
        manifest = json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))
        if len(rows) != 100 or manifest["case_count"] != 100:
            raise AssertionError("canonical_batch001_exact100_required")
        cls.row = next(
            row for row in rows if str(row["case_id"]) == _TARGET_CASE_ID
        )
        cls.source = freeze_text_source(_request_from_row(cls.row))
        cls.plan = build_final_stage1_grounded_observation_plan(
            cls.source.normalized_current_input,
            evidence_spans=cls.source.evidence_spans,
        )
        cls.focus_nucleus = next(
            nucleus
            for nucleus in cls.plan.nuclei
            if _EXPECTED_ROLE
            in "".join(
                span.raw_text
                for span in cls.source.evidence_spans
                if span.span_id in nucleus.source_span_ids
            )
        )
        cls.focus_source = "".join(
            span.raw_text
            for span in cls.source.evidence_spans
            if span.span_id in cls.focus_nucleus.source_span_ids
        )

    def test_01_canonical_final_graph_freezes_exact_contiguous_role(self) -> None:
        self.assertIn(
            FINAL_STAGE1_GROUNDED_PROJECTION_VERSION,
            self.plan.source_contracts,
        )
        required_nuclei, required_relations, reception_targets = (
            _planned_visible_source_ids(self.plan)
        )
        graph = _build_graph(
            self.source,
            self.plan,
            _ordered((*required_nuclei, *reception_targets)),
            required_relations,
        )
        focus_nodes = tuple(
            node for node in graph.nodes if "しか" in node.value
        )
        self.assertEqual(len(focus_nodes), 1)
        self.assertEqual(focus_nodes[0].value, _EXPECTED_ROLE)
        self.assertIn(focus_nodes[0].value, self.focus_source)
        self.assertEqual(self.focus_source.count(focus_nodes[0].value), 1)
        self.assertLessEqual(
            len(focus_nodes[0].value),
            vertical.CMEE_FROZEN_ROLE_MAX,
        )

    def test_02_finite_negative_carrier_family_is_body_free(self) -> None:
        admitted = (
            "安心しか見えていない",
            "疲れから離れられる安心しか見えていなかった",
            "不安しか感じていません",
            "不安しか感じていませんでした",
        )
        for source_role in admitted:
            with self.subTest(source_role=source_role):
                self.assertEqual(
                    _cmee_bounded_exclusive_focus_role(source_role),
                    source_role,
                )

    def test_03_ambiguous_or_unbounded_focus_fails_closed(self) -> None:
        rejected = (
            "不安しかないわけではない",
            "不安しかなく安心しか見えていない",
            "疲れから離れる安心しか見えていない。不安ではない",
            "「不安しか感じていない」",
            "（不安しか感じていない）",
            "例文として不安しか感じていない",
            "例文として、不安しか感じていない",
            "友人は不安しか感じていない",
            "友人によると、不安しか感じていない",
            "田中は不安しか感じていない",
            "不安 しか感じていない",
            "安心しか見えている",
            "あ" * 33 + "しか見えていない",
        )
        for source_role in rejected:
            with self.subTest(source_role=source_role):
                self.assertEqual(
                    _cmee_bounded_exclusive_focus_role(source_role),
                    "",
                )

    def test_04_final_contract_and_v2_schema_are_both_required(self) -> None:
        self.assertEqual(
            _cmee_frozen_lexical_role_surface(
                self.focus_nucleus,
                self.focus_source,
                allow_final_exclusive_focus=True,
            ),
            _EXPECTED_ROLE,
        )
        with self.assertRaisesRegex(
            CMEEVerticalError,
            "lexical_role_negation_unrepresentable",
        ):
            _cmee_frozen_lexical_role_surface(
                self.focus_nucleus,
                self.focus_source,
            )

        nonfinal_plan = replace(
            self.plan,
            source_contracts=tuple(
                contract
                for contract in self.plan.source_contracts
                if contract != FINAL_STAGE1_GROUNDED_PROJECTION_VERSION
            ),
        )
        required_nuclei, required_relations, reception_targets = (
            _planned_visible_source_ids(nonfinal_plan)
        )
        with self.assertRaisesRegex(
            CMEEVerticalError,
            "lexical_role_negation_unrepresentable",
        ):
            _build_graph(
                self.source,
                nonfinal_plan,
                _ordered((*required_nuclei, *reception_targets)),
                required_relations,
            )

        source_text = "。".join(
            str(self.source.normalized_current_input.get(field, "") or "")
            for field in ("memo", "memo_action")
        )
        _cmee_assert_current_first_person_scope_supported(
            source_text,
            self.plan,
            stage1_response_schema_version=(
                CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2
            ),
        )
        with self.assertRaises(CMEEVerticalError):
            _cmee_assert_current_first_person_scope_supported(
                source_text,
                self.plan,
                stage1_response_schema_version=(
                    CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1
                ),
            )

    def test_05_whole_negation_and_negated_desire_remain_rejected(self) -> None:
        whole_negations = (
            "不安ではない",
            "不安ではなかった",
            "不安ではありません",
            "不安ではありませんでした",
            "疲れもない",
            "疲れもなかった",
            "疲れもありません",
            "疲れもありませんでした",
            "つらくはない",
            "つらくはなかった",
            "つらくはありません",
            "つらくはありませんでした",
            "疲れていない",
            "疲れていなかった",
            "疲れていません",
            "疲れていませんでした",
        )
        for source_role in whole_negations:
            with self.subTest(source_role=source_role):
                self.assertEqual(
                    _cmee_bounded_exclusive_focus_role(source_role),
                    "",
                )
                with self.assertRaises(CMEEVerticalError):
                    _cmee_frozen_lexical_role_surface(
                        self.focus_nucleus,
                        source_role,
                        allow_final_exclusive_focus=True,
                    )

        attributes = tuple(
            dict.fromkeys(
                (
                    *self.focus_nucleus.semantic_frame.attribute_codes,
                    "semantic_role:retained_intention",
                )
            )
        )
        wish_nucleus = replace(
            self.focus_nucleus,
            kind="wish",
            semantic_frame=replace(
                self.focus_nucleus.semantic_frame,
                predicate_kind="desire",
                modality="wish",
                attribute_codes=attributes,
            ),
        )
        with self.assertRaisesRegex(
            CMEEVerticalError,
            "lexical_role_negated_desire_conflict",
        ):
            _cmee_frozen_lexical_role_surface(
                wish_nucleus,
                "帰りたいわけではない",
                allow_final_exclusive_focus=True,
            )

    def test_06_production_owner_contains_no_fixture_branch(self) -> None:
        production = Path(vertical.__file__).read_text(encoding="utf-8")
        self.assertNotIn(_TARGET_CASE_ID, production)
        self.assertNotIn(str(self.row["input"]["thought_text"]), production)


if __name__ == "__main__":
    unittest.main()
