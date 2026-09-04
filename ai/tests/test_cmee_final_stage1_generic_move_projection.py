# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import re
from types import SimpleNamespace
from typing import Any, Mapping
import unittest
from unittest.mock import patch

from emlis_ai_current_input_bundle import build_emlis_current_input_bundle
from emlis_ai_evidence_ledger_service import build_evidence_span_resolver
from emlis_ai_grounded_observation_gate import (
    evaluate_grounded_observation_gate,
    evaluate_grounded_surface_body_inverse,
)
import emlis_ai_grounded_observation_gate as gate_owner
import emlis_ai_grounded_observation_plan as observation_plan_owner
from emlis_ai_grounded_observation_plan import (
    build_final_stage1_grounded_observation_plan,
    build_grounded_observation_plan,
)
import emlis_ai_grounded_human_reception as reception_owner
import emlis_ai_grounded_sentence_surface as surface_owner
from cocolon_meaning_experience_engine.contracts import (
    GenerationRequest,
    InterpretationKind,
)
from cocolon_meaning_experience_engine.emlis_v1a import (
    _build_experience_plan,
    _build_graph,
    _cmee_semantic_reception_plan,
    _ordered,
    _planned_visible_source_ids,
)
import cocolon_meaning_experience_engine.emlis_stage1_response as response_owner
from cocolon_meaning_experience_engine.source_kernel import freeze_text_source
from tools.emlis_nls_v3_batch_run import load_validated_batch


_AI_ROOT = Path(__file__).resolve().parents[1]
_GENERATED_ROOT = _AI_ROOT / "tests" / "fixtures" / "emlis_nls_v3" / "generated"
_BATCH_PATH = _GENERATED_ROOT / "batch_001.jsonl"
_MANIFEST_PATH = _GENERATED_ROOT / "batch_001_manifest.json"
_SELECTED_AT = "2026-09-01T00:00:00Z"
_REPRESENTATIVE_CASE_IDS = (
    "nls3s_b001_0007",
    "nls3s_b001_0024",
    "nls3s_b001_0029",
    "nls3s_b001_0054",
    "nls3s_b001_0065",
    "nls3s_b001_0076",
    "nls3s_b001_0081",
)
_SURFACE_EDGE_CASE_IDS = (
    "nls3s_b001_0080",
    "nls3s_b001_0090",
)
_TYPED_RELATION_CLOSURE_CASE_IDS = (
    "nls3s_b001_0027",
    "nls3s_b001_0041",
    "nls3s_b001_0057",
    "nls3s_b001_0060",
    "nls3s_b001_0091",
)


def _request_from_row(row: Mapping[str, Any]) -> GenerationRequest:
    input_row = row["input"]
    if not isinstance(input_row, Mapping):
        raise TypeError("canonical_input_mapping_required")
    emotions = input_row["emotions"]
    if not isinstance(emotions, list) or any(
        not isinstance(item, Mapping) for item in emotions
    ):
        raise TypeError("canonical_emotions_list_required")
    case_id = str(row["case_id"])
    return GenerationRequest(
        request_id=f"req-final-generic-{case_id}",
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


def _full_surface_artifacts(row: Mapping[str, Any]) -> SimpleNamespace:
    source = freeze_text_source(_request_from_row(row))
    grounded_plan = build_final_stage1_grounded_observation_plan(
        source.normalized_current_input,
        evidence_spans=source.evidence_spans,
    )
    resolver = build_evidence_span_resolver(
        source.evidence_spans,
        current_input=source.normalized_current_input,
    )
    reception_plan = _cmee_semantic_reception_plan(
        grounded_plan,
        resolver,
    )
    selected_plan = replace(
        grounded_plan,
        input_profile=replace(
            grounded_plan.input_profile,
            material_quality="limited_grounding",
        ),
        response_plan=replace(
            grounded_plan.response_plan,
            response_kind="limited_grounding_observation",
            human_reception_plan=reception_plan,
        ),
        surface_policy=replace(
            grounded_plan.surface_policy,
            hedge_policy="limited_single_input_scope",
        ),
    )
    sentence_plan = surface_owner.build_grounded_sentence_plan(
        selected_plan,
        resolver,
        recovery_stage="full",
    )
    surface = surface_owner.realize_grounded_sentence_plan(
        sentence_plan,
        selected_plan,
        resolver,
    )
    inverse = evaluate_grounded_surface_body_inverse(
        body=surface.text.encode("utf-8"),
        plan=selected_plan,
        sentence_plan=sentence_plan,
        resolver=resolver,
    )
    gate = evaluate_grounded_observation_gate(
        plan=selected_plan,
        sentence_plan=sentence_plan,
        surface_result=surface,
        resolver=resolver,
        product_readfeel_status="not_evaluated",
        require_body_inverse=True,
    )
    return SimpleNamespace(
        plan=selected_plan,
        sentence_plan=sentence_plan,
        surface=surface,
        resolver=resolver,
        inverse=inverse,
        gate=gate,
    )


def _compile_inputs(row: Mapping[str, Any]) -> SimpleNamespace:
    source = freeze_text_source(_request_from_row(row))
    grounded_plan = build_final_stage1_grounded_observation_plan(
        source.normalized_current_input,
        evidence_spans=source.evidence_spans,
    )
    required_nuclei, required_relations, reception_targets = (
        _planned_visible_source_ids(grounded_plan)
    )
    graph = _build_graph(
        source,
        grounded_plan,
        _ordered((*required_nuclei, *reception_targets)),
        required_relations,
    )
    parent_plan = _build_experience_plan(
        source,
        graph,
        grounded_plan,
        required_nuclei,
        required_relations,
        reception_targets,
    )
    return SimpleNamespace(
        source=source,
        grounded_plan=grounded_plan,
        graph=graph,
        parent_plan=parent_plan,
    )


def _reception_text(body: str) -> str:
    _observation, separator, reception = body.partition(
        surface_owner.RECEPTION_SECTION_LABEL
    )
    if not separator:
        raise AssertionError("reception_section_missing")
    return reception


def _tamper_reception(body: str, source: str, replacement: str) -> str:
    observation, separator, reception = body.partition(
        surface_owner.RECEPTION_SECTION_LABEL
    )
    if not separator or source not in reception:
        raise AssertionError(f"reception_tamper_source_missing:{source}")
    return observation + separator + reception.replace(source, replacement, 1)


def _symbolic_cross_move_borrow_artifacts() -> SimpleNamespace:
    raw = {
        "id": "symbolic-cross-move-borrow",
        "created_at": _SELECTED_AT,
        "memo": (
            "毎日練習した。前よりできるようになった。嬉しい。"
            "それでもまだ不安がある。次も続けたい。"
        ),
        "memo_action": "",
        "category": ["仕事"],
        "emotion_details": [{"type": "不安", "strength": "medium"}],
        "emotions": ["不安"],
        "is_secret": False,
    }
    source = freeze_text_source(
        GenerationRequest(
            request_id="req-symbolic-cross-move-borrow",
            current_input_bundle=build_emlis_current_input_bundle(raw),
            expected_source_record_id=str(raw["id"]),
        )
    )
    grounded_plan = build_final_stage1_grounded_observation_plan(
        source.normalized_current_input,
        evidence_spans=source.evidence_spans,
    )
    resolver = build_evidence_span_resolver(
        source.evidence_spans,
        current_input=source.normalized_current_input,
    )
    base_reception_plan = _cmee_semantic_reception_plan(
        grounded_plan,
        resolver,
    )
    if len(base_reception_plan.moves) != 2:
        raise AssertionError("symbolic_two_move_plan_required")
    base_reception_plan = replace(
        base_reception_plan,
        moves=(
            base_reception_plan.moves[0],
            replace(
                base_reception_plan.moves[1],
                move_role="felt_response",
            ),
        ),
    )
    third_opportunity = replace(
        base_reception_plan.opportunities[-1],
        opportunity_id="ro-symbolic-cross-move-borrow",
    )
    third_move = replace(
        base_reception_plan.moves[-1],
        move_id="rm-symbolic-cross-move-borrow",
        distinct_from_move_ids=tuple(
            move.move_id for move in base_reception_plan.moves
        ),
    )
    reception_plan = replace(
        base_reception_plan,
        opportunities=(
            *base_reception_plan.opportunities,
            third_opportunity,
        ),
        depth_policy=replace(
            base_reception_plan.depth_policy,
            opportunity_count=3,
            selected_move_count=3,
            min_sentences=2,
            max_sentences=3,
            min_realized_moves=3,
            max_moves_per_sentence=2,
        ),
        moves=(*base_reception_plan.moves, third_move),
    )
    grounded_plan = replace(
        grounded_plan,
        response_plan=replace(
            grounded_plan.response_plan,
            human_reception_plan=reception_plan,
        ),
    )
    clause_plans = reception_owner.build_grounded_reception_clause_plans(
        reception_plan,
        "integrated",
    )
    if not any(len(clause.move_ids) > 1 for clause in clause_plans):
        raise AssertionError("symbolic_shared_clause_required")
    nucleus_index = {
        nucleus.nucleus_id: nucleus for nucleus in grounded_plan.nuclei
    }
    surface = reception_owner.replay_source_grounded_human_reception_from_plan(
        reception_plan,
        nucleus_index,
        resolver,
        plan=grounded_plan,
        recovery_stage="integrated",
        clause_plans=clause_plans,
    )
    return SimpleNamespace(
        plan=grounded_plan,
        reception_plan=reception_plan,
        clause_plans=clause_plans,
        resolver=resolver,
        surface=surface,
    )


class CMEEReceptionCrossMoveBorrowContractTest(unittest.TestCase):
    def test_body_inverse_join_boundary_requires_one_canonical_owner_cut(
        self,
    ) -> None:
        left_referent = "先の対象"
        right_referent = "次の対象"
        context_with_marker = "受け止めたいことを背景に、"

        def _markers_for(
            text: str,
            *tokens: str,
        ) -> tuple[SimpleNamespace, ...]:
            rows = []
            for token in tokens:
                for match in re.finditer(re.escape(token), text):
                    rows.append(
                        SimpleNamespace(
                            section="reception",
                            marker_kind="reception",
                            utf8_byte_start=len(
                                text[: match.start()].encode("utf-8")
                            ),
                            utf8_byte_end=len(
                                text[: match.end()].encode("utf-8")
                            ),
                        )
                    )
            return tuple(rows)

        canonical_response = "を受け止めていて"
        canonical_prefix = left_referent + canonical_response + "、"
        canonical_text = (
            canonical_prefix + context_with_marker + right_referent
        )
        canonical_boundary = len(canonical_prefix.encode("utf-8"))
        prior_referent_end = len(left_referent.encode("utf-8"))
        owned_referent_start = len(
            (canonical_prefix + context_with_marker).encode("utf-8")
        )
        self.assertEqual(
            gate_owner._body_inverse_reception_join_boundary(
                canonical_text.encode("utf-8"),
                prior_referent_byte_end=prior_referent_end,
                owned_referent_byte_start=owned_referent_start,
                markers=_markers_for(canonical_text, "受け止め"),
            ),
            canonical_boundary,
        )

        missing_join_text = canonical_text.replace(
            canonical_response + "、",
            canonical_response + "と",
            1,
        )
        self.assertIsNone(
            gate_owner._body_inverse_reception_join_boundary(
                missing_join_text.encode("utf-8"),
                prior_referent_byte_end=prior_referent_end,
                owned_referent_byte_start=len(
                    (
                        left_referent
                        + canonical_response
                        + "と"
                        + context_with_marker
                    ).encode("utf-8")
                ),
                markers=_markers_for(
                    missing_join_text,
                    "受け止め",
                ),
            )
        )

        ambiguous_response = "を受け止めていて、見守っていて、"
        ambiguous_text = (
            left_referent
            + ambiguous_response
            + context_with_marker
            + right_referent
        )
        self.assertIsNone(
            gate_owner._body_inverse_reception_join_boundary(
                ambiguous_text.encode("utf-8"),
                prior_referent_byte_end=prior_referent_end,
                owned_referent_byte_start=len(
                    (
                        left_referent
                        + ambiguous_response
                        + context_with_marker
                    ).encode("utf-8")
                ),
                markers=_markers_for(
                    ambiguous_text,
                    "受け止め",
                    "見守",
                ),
            )
        )

    def test_multi_move_responsibility_cannot_borrow_next_context_tail(
        self,
    ) -> None:
        artifacts = _symbolic_cross_move_borrow_artifacts()
        grounded_plan = artifacts.plan
        reception_plan = artifacts.reception_plan
        clause_plans = artifacts.clause_plans
        recovery_stage = "integrated"
        active_moves = reception_owner.reception_active_moves(
            reception_plan,
            recovery_stage,
        )
        move_index = {move.move_id: move for move in active_moves}
        nucleus_index = {
            nucleus.nucleus_id: nucleus for nucleus in grounded_plan.nuclei
        }
        referent_by_move = {}
        anchor_used = False
        for clause_plan in clause_plans:
            for move_id in clause_plan.move_ids:
                move = move_index[move_id]
                referent = (
                    reception_owner.resolve_grounded_reception_move_referent(
                        reception_plan,
                        move,
                        nucleus_index,
                        artifacts.resolver,
                        allow_short_anchor=bool(
                            clause_plan.quote_budget and not anchor_used
                        ),
                        recovery_stage=recovery_stage,
                        allow_anaphoric_topic=True,
                    )
                )
                anchor_used = anchor_used or referent.source_anchor_used
                referent_by_move[move_id] = referent

        actual_text = artifacts.surface.text
        actual_clauses = tuple(
            part.strip()
            for part in reception_owner._SENTENCE_END_RE.split(actual_text)
            if part.strip()
        )
        mutation = None
        for clause_plan, clause_text in zip(
            clause_plans,
            actual_clauses,
            strict=True,
        ):
            for left_id, right_id in zip(
                clause_plan.move_ids,
                clause_plan.move_ids[1:],
            ):
                left_move = move_index[left_id]
                left_visible = referent_by_move[left_id].text.replace(
                    "「", ""
                ).replace("」", "")
                right_visible = referent_by_move[right_id].text.replace(
                    "「", ""
                ).replace("」", "")
                left_start = clause_text.find(left_visible)
                right_start = clause_text.find(
                    right_visible,
                    left_start + len(left_visible),
                )
                if left_start < 0 or right_start < 0:
                    continue
                responsibility = (
                    reception_owner._ACT_OWNED_RESPONSIBILITY_RE[
                        left_move.reception_act
                    ]
                )
                match = responsibility.search(
                    clause_text,
                    left_start,
                    right_start,
                )
                if match is None:
                    continue
                join_end = clause_text.find("、", match.end(), right_start)
                if join_end < 0:
                    continue
                matched_text = match.group(0)
                borrowed_tail = next(
                    (
                        matched_text[offset:]
                        for offset in range(
                            len(matched_text) - 1,
                            -1,
                            -1,
                        )
                        if responsibility.search(
                            left_visible + matched_text[offset:]
                        )
                    ),
                    "",
                )
                if not borrowed_tail:
                    continue
                left_end = left_start + len(left_visible)
                mutated_clause = (
                    clause_text[:left_end]
                    + clause_text[join_end : join_end + 1]
                    + borrowed_tail
                    + clause_text[join_end + 1 :]
                )
                if (
                    responsibility.search(
                        mutated_clause[left_start:left_end]
                    )
                    is None
                    and responsibility.search(mutated_clause) is not None
                ):
                    mutation = (clause_text, mutated_clause, left_move)
                    break
            if mutation is not None:
                break
        self.assertIsNotNone(mutation)
        assert mutation is not None
        clause_text, mutated_clause, left_move = mutation
        clause_start = actual_text.find(clause_text)
        self.assertGreaterEqual(clause_start, 0)
        tampered_text = (
            actual_text[:clause_start]
            + mutated_clause
            + actual_text[clause_start + len(clause_text) :]
        )
        self.assertNotEqual(tampered_text, actual_text)

        context_map = {
            move.move_id: reception_owner.final_reception_context_nucleus_ids(
                move=move,
                plan=grounded_plan,
            )
            for move in active_moves
        }
        with self.assertRaisesRegex(
            reception_owner.GroundedHumanReceptionSurfaceError,
            "human_reception_act_responsibility_missing:"
            f"{left_move.reception_act}",
        ):
            reception_owner.bind_and_validate_grounded_human_reception_surface(
                reception_plan,
                nucleus_index,
                artifacts.resolver,
                actual_text=tampered_text,
                recovery_stage=recovery_stage,
                clause_plans=clause_plans,
                context_nucleus_ids_by_move=context_map,
                allow_anaphoric_topic=True,
            )


class CMEEAnaphoricTopicOwnerTest(unittest.TestCase):
    def test_short_grammatical_topic_is_bounded_and_question_free(self) -> None:
        self.assertEqual(
            reception_owner._short_anaphoric_topic("環境を変えたい"),
            "環境",
        )
        self.assertEqual(
            reception_owner._short_anaphoric_topic(
                "続けられる形は探したい"
            ),
            "続けられる形",
        )
        self.assertEqual(
            reception_owner._short_anaphoric_topic("納得したい気持ち"),
            "納得",
        )
        self.assertEqual(
            reception_owner._short_anaphoric_topic("変えたい"),
            "",
        )
        self.assertEqual(
            reception_owner._short_anaphoric_topic("環境を変えたい？"),
            "",
        )
        self.assertEqual(
            reception_owner._short_anaphoric_topic(
                "非常に長い対象名をそのまま再生してしまう範囲を変えたい"
            ),
            "",
        )


class CMEEFinalStage1GenericMoveProjectionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        rows, _manifest = load_validated_batch(_BATCH_PATH, _MANIFEST_PATH)
        rows_by_id = {str(row["case_id"]): row for row in rows}
        required_ids = (
            *_REPRESENTATIVE_CASE_IDS,
            *_SURFACE_EDGE_CASE_IDS,
            *_TYPED_RELATION_CLOSURE_CASE_IDS,
            "nls3s_b001_0051",
            "nls3s_b001_0020",
            "nls3s_b001_0058",
            "nls3s_b001_0066",
        )
        cls.rows_by_id = rows_by_id
        cls.artifacts = {
            case_id: _full_surface_artifacts(rows_by_id[case_id])
            for case_id in required_ids
        }

    def _inverse_for_tamper(self, case_id: str, body: str):
        artifacts = self.artifacts[case_id]
        return evaluate_grounded_surface_body_inverse(
            body=body.encode("utf-8"),
            plan=artifacts.plan,
            sentence_plan=artifacts.sentence_plan,
            resolver=artifacts.resolver,
        )

    def _bind_reception_text(
        self,
        case_id: str,
        text: str,
        *,
        sentence_plan=None,
    ):
        artifacts = self.artifacts[case_id]
        selected_sentence_plan = sentence_plan or artifacts.sentence_plan
        reception_plan = artifacts.plan.response_plan.human_reception_plan
        line = next(
            row
            for row in selected_sentence_plan.lines
            if row.binding.line_role == "human_follow"
        )
        context_map = {
            move.move_id: reception_owner.final_reception_context_nucleus_ids(
                move=move,
                plan=artifacts.plan,
            )
            for move in reception_owner.reception_active_moves(
                reception_plan,
                selected_sentence_plan.recovery_stage,
            )
        }
        return reception_owner.bind_and_validate_grounded_human_reception_surface(
            reception_plan,
            {
                nucleus.nucleus_id: nucleus
                for nucleus in artifacts.plan.nuclei
            },
            artifacts.resolver,
            actual_text=text.strip(),
            recovery_stage=selected_sentence_plan.recovery_stage,
            clause_plans=line.reception_clause_plans,
            context_nucleus_ids_by_move=context_map,
            allow_anaphoric_topic=True,
        )

    def _gate_for_tampered_body(
        self,
        case_id: str,
        body: str,
        *,
        sentence_plan=None,
        base_surface=None,
    ):
        artifacts = self.artifacts[case_id]
        selected_sentence_plan = sentence_plan or artifacts.sentence_plan
        selected_surface = base_surface or artifacts.surface
        reception = _reception_text(body).strip()
        tampered_surface = replace(
            selected_surface,
            text=body,
            lines=tuple(
                replace(line, text=reception)
                if line.binding.line_role == "human_follow"
                else line
                for line in selected_surface.lines
            ),
        )
        return evaluate_grounded_observation_gate(
            plan=artifacts.plan,
            sentence_plan=selected_sentence_plan,
            surface_result=tampered_surface,
            resolver=artifacts.resolver,
            product_readfeel_status="not_evaluated",
            require_body_inverse=True,
        )

    def test_representative_moves_all_reach_one_hard_valid_surface(self) -> None:
        for case_id in (*_REPRESENTATIVE_CASE_IDS, *_SURFACE_EDGE_CASE_IDS):
            with self.subTest(case_id=case_id):
                artifacts = self.artifacts[case_id]
                self.assertTrue(
                    artifacts.inverse.passed,
                    artifacts.inverse.failure_codes,
                )
                self.assertTrue(
                    artifacts.gate.passed,
                    artifacts.gate.rejection_reasons,
                )

    def test_typed_relation_endpoints_keep_required_body_markers(self) -> None:
        seen_relation_types: set[str] = set()
        seen_semantic_duties: set[str] = set()
        for case_id in _TYPED_RELATION_CLOSURE_CASE_IDS:
            with self.subTest(case_id=case_id):
                artifacts = self.artifacts[case_id]
                witness = surface_owner.parse_grounded_surface_body_bytes(
                    artifacts.surface.text.encode("utf-8")
                )
                observation = next(
                    row
                    for row in witness.lines
                    if row.section == "observation"
                )
                relation_index = {
                    relation.relation_id: relation
                    for relation in artifacts.plan.relations
                }
                required_relation_ids = (
                    artifacts.plan.coverage_requirements.required_relation_ids
                )
                required_relations = tuple(
                    relation_index[relation_id]
                    for relation_id in required_relation_ids
                )
                endpoint_ids = {
                    nucleus_id
                    for relation in required_relations
                    for nucleus_id in (
                        relation.from_nucleus_id,
                        relation.to_nucleus_id,
                    )
                }
                required_nucleus_ids = set(
                    artifacts.plan.coverage_requirements.required_nucleus_ids
                )
                endpoint_nuclei = tuple(
                    nucleus
                    for nucleus in artifacts.plan.nuclei
                    if nucleus.nucleus_id in endpoint_ids
                    and nucleus.nucleus_id in required_nucleus_ids
                )

                for relation in required_relations:
                    seen_relation_types.add(relation.type)
                    allowed = gate_owner._BODY_INVERSE_RELATION_MARKERS_BY_TYPE[
                        relation.type
                    ]
                    self.assertTrue(
                        set(observation.relation_marker_codes).intersection(
                            allowed
                        ),
                        (relation.type, observation.relation_marker_codes),
                    )
                for nucleus in endpoint_nuclei:
                    attributes = set(nucleus.semantic_frame.attribute_codes)
                    if (
                        nucleus.kind == "wish"
                        and nucleus.semantic_frame.modality
                        in {"wish", "intention"}
                    ):
                        seen_semantic_duties.add("intention")
                        self.assertIn(
                            "intention",
                            observation.semantic_marker_codes,
                        )
                    if nucleus.kind == "constraint":
                        seen_semantic_duties.add("constraint")
                        self.assertIn(
                            "constraint",
                            observation.semantic_marker_codes,
                        )
                    if (
                        nucleus.kind == "uncertainty"
                        or "semantic_role:limiting_unknown" in attributes
                    ):
                        seen_semantic_duties.add("unknown")
                        self.assertTrue(
                            "unknown" in observation.semantic_marker_codes
                            or bool(observation.uncertainty_marker_codes)
                        )
                self.assertTrue(
                    artifacts.inverse.passed,
                    artifacts.inverse.failure_codes,
                )
                self.assertTrue(
                    artifacts.gate.passed,
                    artifacts.gate.rejection_reasons,
                )

        self.assertTrue(
            {"attempt_and_block", "wish_and_constraint", "contrast"}
            <= seen_relation_types
        )
        self.assertEqual(
            seen_semantic_duties,
            {"intention", "constraint", "unknown"},
        )

    def test_attempt_and_block_marker_deletion_and_wrong_family_fail_closed(
        self,
    ) -> None:
        artifacts = next(
            self.artifacts[case_id]
            for case_id in _TYPED_RELATION_CLOSURE_CASE_IDS
            if any(
                relation.type == "attempt_and_block"
                and relation.relation_id
                in set(
                    self.artifacts[
                        case_id
                    ].plan.coverage_requirements.required_relation_ids
                )
                for relation in self.artifacts[case_id].plan.relations
            )
        )
        deleted = artifacts.surface.text.replace("一方で、", "、", 1)
        deleted_inverse = evaluate_grounded_surface_body_inverse(
            body=deleted.encode("utf-8"),
            plan=artifacts.plan,
            sentence_plan=artifacts.sentence_plan,
            resolver=artifacts.resolver,
        )
        self.assertFalse(deleted_inverse.passed)
        self.assertIn(
            "body_inverse_relation_type_marker_mismatch:1",
            deleted_inverse.failure_codes,
        )

        wrong_family = artifacts.surface.text.replace(
            "一方で、",
            "つながり、",
            1,
        )
        wrong_inverse = evaluate_grounded_surface_body_inverse(
            body=wrong_family.encode("utf-8"),
            plan=artifacts.plan,
            sentence_plan=artifacts.sentence_plan,
            resolver=artifacts.resolver,
        )
        self.assertFalse(wrong_inverse.passed)
        self.assertIn(
            "body_inverse_relation_type_marker_mismatch:1",
            wrong_inverse.failure_codes,
        )

    def test_typed_relation_closure_cases_compile_through_hard_gate(self) -> None:
        for case_id in _TYPED_RELATION_CLOSURE_CASE_IDS:
            with self.subTest(case_id=case_id):
                inputs = _compile_inputs(self.rows_by_id[case_id])
                _projection, units = response_owner.compile_stage1_response(
                    source=inputs.source,
                    grounded_graph=inputs.graph,
                    parent_plan=inputs.parent_plan,
                    grounded_plan=inputs.grounded_plan,
                )
                artifacts = self.artifacts[case_id]
                self.assertEqual(
                    tuple(unit.text for unit in units),
                    tuple(line.text for line in artifacts.surface.lines),
                )
                self.assertTrue(
                    artifacts.inverse.passed,
                    artifacts.inverse.failure_codes,
                )
                self.assertTrue(
                    artifacts.gate.passed,
                    artifacts.gate.rejection_reasons,
                )

    def test_base_final_surface_delegates_to_human_reception_replay(self) -> None:
        artifacts = self.artifacts["nls3s_b001_0024"]
        actual_replay = (
            surface_owner.replay_source_grounded_human_reception_from_plan
        )
        with patch.object(
            surface_owner,
            "replay_source_grounded_human_reception_from_plan",
            wraps=actual_replay,
        ) as human_reception_replay:
            result = surface_owner.realize_grounded_sentence_plan(
                artifacts.sentence_plan,
                artifacts.plan,
                artifacts.resolver,
            )

        self.assertEqual(result.text, artifacts.surface.text)
        self.assertGreaterEqual(human_reception_replay.call_count, 1)
        for replay_call in human_reception_replay.call_args_list:
            self.assertEqual(len(replay_call.args), 3)
            self.assertTrue(
                {
                    "plan",
                    "recovery_stage",
                    "clause_plans",
                }
                <= set(replay_call.kwargs)
            )
            self.assertTrue(
                {
                    "expressions",
                    "human_reception_surface",
                    "reception_placements",
                }.isdisjoint(replay_call.kwargs)
            )

    def test_unbound_quote_is_rejected_by_actual_rr4_contract(self) -> None:
        case_id = "nls3s_b001_0024"
        artifacts = self.artifacts[case_id]
        reception_plan = artifacts.plan.response_plan.human_reception_plan
        move = reception_plan.moves[0]
        referent = reception_owner.resolve_grounded_reception_move_referent(
            reception_plan,
            move,
            {nucleus.nucleus_id: nucleus for nucleus in artifacts.plan.nuclei},
            artifacts.resolver,
            allow_short_anchor=False,
            recovery_stage=artifacts.sentence_plan.recovery_stage,
            allow_anaphoric_topic=True,
        )
        visible_referent = referent.text.replace("「", "").replace("」", "")
        baseline = _reception_text(artifacts.surface.text)
        self.assertEqual(baseline.count(visible_referent), 1)
        reception = baseline.replace(
            visible_referent,
            "「無関係」",
            1,
        )
        self.assertNotEqual(reception, baseline)
        self.assertEqual(reception.count(visible_referent), 0)
        with self.assertRaisesRegex(
            reception_owner.GroundedHumanReceptionSurfaceError,
            "human_reception_source_anchor_unbound",
        ):
            self._bind_reception_text(case_id, reception)

    def test_multi_move_surfaces_retain_each_rr4_duty(self) -> None:
        multi_case = "nls3s_b001_0020"
        multi_reception = _reception_text(
            self.artifacts[multi_case].surface.text
        )
        bound = self._bind_reception_text(multi_case, multi_reception)
        self.assertEqual(bound.realized_move_ids, ("rm1", "rm2"))
        with self.assertRaisesRegex(
            reception_owner.GroundedHumanReceptionSurfaceError,
            "human_reception_move_target_missing:rm2",
        ):
            self._bind_reception_text(
                multi_case,
                multi_reception.replace("その変化", "その内容", 1),
            )

        accountability_case = "nls3s_b001_0066"
        accountability_reception = _reception_text(
            self.artifacts[accountability_case].surface.text
        )
        accountability = self._bind_reception_text(
            accountability_case,
            accountability_reception,
        )
        self.assertEqual(
            accountability.realized_reception_acts,
            ("honor_concrete_effort", "recognize_lived_change"),
        )
        self.assertNotIn(
            "bounded_counter_self_denial",
            accountability.realized_reception_acts,
        )

    def _fixture_backed_multi_move_responsibility_borrow_witness(
        self,
    ) -> None:
        selected = None
        for artifacts in self.artifacts.values():
            base_reception_plan = (
                artifacts.plan.response_plan.human_reception_plan
            )
            if (
                base_reception_plan is None
                or len(base_reception_plan.moves) != 2
                or base_reception_plan.moves[0].move_role
                in {"attention", "bounded_counterposition"}
                or base_reception_plan.moves[1].move_role
                == "bounded_counterposition"
            ):
                continue
            base_reception_plan = replace(
                base_reception_plan,
                moves=(
                    base_reception_plan.moves[0],
                    replace(
                        base_reception_plan.moves[1],
                        move_role="felt_response",
                    ),
                ),
            )
            third_opportunity = replace(
                base_reception_plan.opportunities[-1],
                opportunity_id="ro-borrow-witness",
            )
            third_move = replace(
                base_reception_plan.moves[-1],
                move_id="rm-borrow-witness",
                distinct_from_move_ids=tuple(
                    move.move_id for move in base_reception_plan.moves
                ),
            )
            reception_plan = replace(
                base_reception_plan,
                opportunities=(
                    *base_reception_plan.opportunities,
                    third_opportunity,
                ),
                depth_policy=replace(
                    base_reception_plan.depth_policy,
                    opportunity_count=3,
                    selected_move_count=3,
                    min_sentences=2,
                    max_sentences=3,
                    min_realized_moves=3,
                    max_moves_per_sentence=2,
                ),
                moves=(*base_reception_plan.moves, third_move),
            )
            grounded_plan = replace(
                artifacts.plan,
                response_plan=replace(
                    artifacts.plan.response_plan,
                    human_reception_plan=reception_plan,
                ),
            )
            clause_plans = (
                reception_owner.build_grounded_reception_clause_plans(
                    reception_plan,
                    "integrated",
                )
            )
            if any(
                len(clause.move_ids) > 1
                for clause in clause_plans
            ):
                nucleus_index = {
                    nucleus.nucleus_id: nucleus
                    for nucleus in grounded_plan.nuclei
                }
                surface = (
                    reception_owner.replay_source_grounded_human_reception_from_plan(
                        reception_plan,
                        nucleus_index,
                        artifacts.resolver,
                        plan=grounded_plan,
                        recovery_stage="integrated",
                        clause_plans=clause_plans,
                    )
                )
                selected = (
                    artifacts,
                    grounded_plan,
                    reception_plan,
                    clause_plans,
                    surface,
                )
                break
        self.assertIsNotNone(selected)
        assert selected is not None
        (
            artifacts,
            grounded_plan,
            reception_plan,
            clause_plans,
            surface,
        ) = selected
        recovery_stage = "integrated"
        active_moves = reception_owner.reception_active_moves(
            reception_plan,
            recovery_stage,
        )
        move_index = {move.move_id: move for move in active_moves}
        nucleus_index = {
            nucleus.nucleus_id: nucleus
            for nucleus in grounded_plan.nuclei
        }
        referent_by_move = {}
        anchor_used = False
        for clause_plan in clause_plans:
            for move_id in clause_plan.move_ids:
                move = move_index[move_id]
                referent = (
                    reception_owner.resolve_grounded_reception_move_referent(
                        reception_plan,
                        move,
                        nucleus_index,
                        artifacts.resolver,
                        allow_short_anchor=bool(
                            clause_plan.quote_budget and not anchor_used
                        ),
                        recovery_stage=recovery_stage,
                        allow_anaphoric_topic=True,
                    )
                )
                anchor_used = anchor_used or referent.source_anchor_used
                referent_by_move[move_id] = referent

        actual_text = surface.text
        actual_clauses = tuple(
            part.strip()
            for part in reception_owner._SENTENCE_END_RE.split(actual_text)
            if part.strip()
        )
        mutation = None
        for clause_plan, clause_text in zip(
            clause_plans,
            actual_clauses,
            strict=True,
        ):
            for left_id, right_id in zip(
                clause_plan.move_ids,
                clause_plan.move_ids[1:],
            ):
                left_move = move_index[left_id]
                left_referent = referent_by_move[left_id]
                right_referent = referent_by_move[right_id]
                left_visible = left_referent.text.replace(
                    "「", ""
                ).replace("」", "")
                right_visible = right_referent.text.replace(
                    "「", ""
                ).replace("」", "")
                left_start = clause_text.find(left_visible)
                right_start = clause_text.find(
                    right_visible,
                    left_start + len(left_visible),
                )
                if left_start < 0 or right_start < 0:
                    continue
                responsibility = (
                    reception_owner._ACT_OWNED_RESPONSIBILITY_RE[
                        left_move.reception_act
                    ]
                )
                match = responsibility.search(
                    clause_text,
                    left_start,
                    right_start,
                )
                if match is None:
                    continue
                join_end = clause_text.find(
                    "、",
                    match.end(),
                    right_start,
                )
                if join_end < 0:
                    continue
                matched_text = match.group(0)
                borrowed_tail = next(
                    (
                        matched_text[offset:]
                        for offset in range(
                            len(matched_text) - 1,
                            -1,
                            -1,
                        )
                        if responsibility.search(
                            left_visible + matched_text[offset:]
                        )
                    ),
                    "",
                )
                if not borrowed_tail:
                    continue
                left_end = left_start + len(left_visible)
                mutated_clause = (
                    clause_text[:left_end]
                    + clause_text[join_end : join_end + 1]
                    + borrowed_tail
                    + clause_text[join_end + 1 :]
                )
                local_owned_text = mutated_clause[left_start:left_end]
                if (
                    responsibility.search(local_owned_text) is None
                    and responsibility.search(mutated_clause) is not None
                ):
                    mutation = (
                        clause_text,
                        mutated_clause,
                        left_move,
                    )
                    break
            if mutation is not None:
                break
        self.assertIsNotNone(mutation)
        assert mutation is not None
        clause_text, mutated_clause, left_move = mutation
        clause_start = actual_text.find(clause_text)
        self.assertGreaterEqual(clause_start, 0)
        tampered_text = (
            actual_text[:clause_start]
            + mutated_clause
            + actual_text[clause_start + len(clause_text) :]
        )
        self.assertNotEqual(tampered_text, actual_text)

        context_map = {
            move.move_id: reception_owner.final_reception_context_nucleus_ids(
                move=move,
                plan=grounded_plan,
            )
            for move in active_moves
        }
        with self.assertRaisesRegex(
            reception_owner.GroundedHumanReceptionSurfaceError,
            "human_reception_act_responsibility_missing:"
            f"{left_move.reception_act}",
        ):
            reception_owner.bind_and_validate_grounded_human_reception_surface(
                reception_plan,
                nucleus_index,
                artifacts.resolver,
                actual_text=tampered_text,
                recovery_stage=recovery_stage,
                clause_plans=clause_plans,
                context_nucleus_ids_by_move=context_map,
                allow_anaphoric_topic=True,
            )

    def test_long_target_uses_referent_without_full_source_replay(
        self,
    ) -> None:
        long_anchor_artifacts = self.artifacts["nls3s_b001_0080"]
        move = (
            long_anchor_artifacts.plan.response_plan.human_reception_plan.moves[0]
        )
        nucleus_index = {
            nucleus.nucleus_id: nucleus
            for nucleus in long_anchor_artifacts.plan.nuclei
        }
        target = reception_owner.final_reception_source_anchor_text(
            move.target_nucleus_ids[0],
            nucleus_index,
            long_anchor_artifacts.resolver,
        )
        reception = _reception_text(long_anchor_artifacts.surface.text)
        referent = reception_owner.resolve_grounded_reception_move_referent(
            long_anchor_artifacts.plan.response_plan.human_reception_plan,
            move,
            nucleus_index,
            long_anchor_artifacts.resolver,
            allow_short_anchor=False,
            recovery_stage=long_anchor_artifacts.sentence_plan.recovery_stage,
            allow_anaphoric_topic=True,
        )
        visible_referent = referent.text.replace("「", "").replace("」", "")
        self.assertTrue(visible_referent)
        self.assertNotIn(target, reception)
        self.assertNotIn(f"「{target}」", reception)
        self.assertEqual(reception.count(visible_referent), 1)
        replayed = reception.replace(
            visible_referent,
            f"{visible_referent}（{target}）",
            1,
        )
        self.assertNotEqual(replayed, reception)
        self.assertEqual(replayed.count(target), 1)
        with self.assertRaisesRegex(
            reception_owner.GroundedHumanReceptionSurfaceError,
            "human_reception_long_target_replayed:rm1",
        ):
            self._bind_reception_text(
                "nls3s_b001_0080",
                replayed,
            )

        relation_artifacts = self.artifacts["nls3s_b001_0090"]
        witness = surface_owner.parse_grounded_surface_body_bytes(
            relation_artifacts.surface.text.encode("utf-8")
        )
        observation = next(
            row for row in witness.lines if row.section == "observation"
        )
        self.assertNotIn("intention", observation.semantic_marker_codes)
        self.assertIn("effort", observation.semantic_marker_codes)

    def test_action_before_after_compile_selects_one_hard_valid_surface(
        self,
    ) -> None:
        inputs = _compile_inputs(self.rows_by_id["nls3s_b001_0090"])
        realized_surfaces = []
        inverse_by_body: dict[bytes, list[object]] = {}
        gates_by_body: dict[bytes, list[object]] = {}
        actual_realize = (
            response_owner.realize_grounded_sentence_plan_with_human_reception
        )
        actual_inverse = response_owner.evaluate_grounded_surface_body_inverse
        actual_gate = response_owner.evaluate_grounded_observation_gate

        def track_realize(*args, **kwargs):
            result = actual_realize(*args, **kwargs)
            surface, _placements = result
            realized_surfaces.append(surface)
            return result

        def track_inverse(*args, **kwargs):
            result = actual_inverse(*args, **kwargs)
            body = kwargs.get("body", args[0] if args else None)
            if type(body) is bytes:
                inverse_by_body.setdefault(body, []).append(result)
            return result

        def track_gate(*args, **kwargs):
            result = actual_gate(*args, **kwargs)
            surface = kwargs.get("surface_result")
            if surface is not None:
                gates_by_body.setdefault(
                    surface.text.encode("utf-8"),
                    [],
                ).append(result)
            return result

        with (
            patch.object(
                response_owner,
                "realize_grounded_sentence_plan_with_human_reception",
                side_effect=track_realize,
            ),
            patch.object(
                response_owner,
                "evaluate_grounded_surface_body_inverse",
                side_effect=track_inverse,
            ),
            patch.object(
                response_owner,
                "evaluate_grounded_observation_gate",
                side_effect=track_gate,
            ),
        ):
            projection, units = response_owner.compile_stage1_response(
                source=inputs.source,
                grounded_graph=inputs.graph,
                parent_plan=inputs.parent_plan,
                grounded_plan=inputs.grounded_plan,
            )

        self.assertTrue(units)
        self.assertEqual(
            sum(
                candidate.candidate_kind
                is InterpretationKind.ACTION_BEFORE_AFTER
                for candidate in projection.interpretation_candidates
            ),
            1,
        )
        selected_texts = tuple(unit.text for unit in units)
        selected_surface = next(
            surface
            for surface in realized_surfaces
            if tuple(line.text for line in surface.lines) == selected_texts
        )
        selected_body = selected_surface.text.encode("utf-8")
        self.assertTrue(
            any(report.passed for report in inverse_by_body[selected_body])
        )
        self.assertTrue(
            any(report.passed for report in gates_by_body[selected_body])
        )

    def test_sx08_layered_move_referents_do_not_reenter_plan_budget(
        self,
    ) -> None:
        from tools import cmee_v1a_i1sx_candidate_run as candidate_run

        case_id, memo, category, emotion, strength = candidate_run.EXACT8[-1]
        private_case, _body_free_case = (
            candidate_run._materialize_im07_formal_case(
                case_id=case_id,
                memo=memo,
                category=category,
                emotion=emotion,
                strength=strength,
            )
        )
        self.assertEqual(case_id, "SX-08")
        self.assertTrue(private_case["formal_trace_valid"])
        self.assertTrue(private_case["machine_invariant_clear"])

    def test_0058_action_change_uses_final_typed_fragments_and_compiles_two_units(
        self,
    ) -> None:
        row = self.rows_by_id["nls3s_b001_0058"]
        inputs = _compile_inputs(row)
        with patch.object(
            observation_plan_owner,
            "_final_stage1_action_change_source_fragment_projections",
            side_effect=AssertionError("final_owner_reached_from_active_builder"),
        ):
            active_plan = build_grounded_observation_plan(
                inputs.source.normalized_current_input,
                evidence_spans=inputs.source.evidence_spans,
            )

        def action_change_endpoints(plan):
            relations = tuple(
                relation
                for relation in plan.relations
                if relation.type == "action_supports_change"
                and relation.source_relation_ids
                == (
                    "typed_projection:"
                    "perfective_action_before_bounded_change",
                )
            )
            self.assertEqual(len(relations), 1)
            relation = relations[0]
            nucleus_index = {
                nucleus.nucleus_id: nucleus for nucleus in plan.nuclei
            }
            return (
                nucleus_index[relation.from_nucleus_id],
                nucleus_index[relation.to_nucleus_id],
            )

        final_endpoints = action_change_endpoints(inputs.grounded_plan)
        self.assertFalse(
            any(
                "semantic_role:final_stage1_compound_meaning"
                in nucleus.semantic_frame.attribute_codes
                for nucleus in active_plan.nuclei
            )
        )
        for nucleus in final_endpoints:
            attributes = tuple(nucleus.semantic_frame.attribute_codes)
            self.assertEqual(
                sum(
                    code.startswith("source_fragment_scalar_range:")
                    for code in attributes
                ),
                1,
            )
            self.assertEqual(
                attributes.count(
                    "source_fragment_scalar_source:normalized_raw_text"
                ),
                1,
            )
            self.assertEqual(
                attributes.count(
                    "semantic_role:generic_relation_fragment"
                ),
                1,
            )
            self.assertFalse(
                any(
                    code.startswith(
                        ("surface_scalar_range:", "surface_scalar_source:")
                    )
                    for code in attributes
                )
            )

        _projection, units = response_owner.compile_stage1_response(
            source=inputs.source,
            grounded_graph=inputs.graph,
            parent_plan=inputs.parent_plan,
            grounded_plan=inputs.grounded_plan,
        )
        self.assertEqual(len(units), 2)
        artifacts = self.artifacts["nls3s_b001_0058"]
        self.assertEqual(
            tuple(unit.text for unit in units),
            tuple(line.text for line in artifacts.surface.lines),
        )
        self.assertTrue(artifacts.inverse.passed, artifacts.inverse.failure_codes)
        self.assertTrue(artifacts.gate.passed, artifacts.gate.rejection_reasons)

        nucleus_index = {
            nucleus.nucleus_id: nucleus for nucleus in artifacts.plan.nuclei
        }
        action_nucleus = nucleus_index[final_endpoints[0].nucleus_id]
        change_nucleus = nucleus_index[final_endpoints[1].nucleus_id]
        raw_text = artifacts.resolver.resolve(
            action_nucleus.source_span_ids[0]
        ).raw_text
        action_fragment = reception_owner._typed_reception_source_fragment(
            action_nucleus,
            raw_text,
        )
        change_fragment = reception_owner._typed_reception_source_fragment(
            change_nucleus,
            raw_text,
        )
        self.assertEqual(
            action_fragment,
            "体調を整えようと思って早く寝る日を増やした",
        )
        self.assertEqual(
            change_fragment,
            "朝に余白ができて気分は落ち着いた",
        )
        self.assertNotEqual(action_fragment, change_fragment)
        reception_text = _reception_text(artifacts.surface.text)

        reception_plan = artifacts.plan.response_plan.human_reception_plan
        move = reception_plan.moves[0]
        reception_line = next(
            line
            for line in artifacts.sentence_plan.lines
            if line.binding.line_role == "human_follow"
        )
        clause_plan = reception_line.reception_clause_plans[0]
        move_ir = reception_owner._source_grounded_plan_clause_realizations(
            reception_plan,
            nucleus_index,
            artifacts.resolver,
            plan=artifacts.plan,
            recovery_stage=artifacts.sentence_plan.recovery_stage,
            clause_plans=tuple(reception_line.reception_clause_plans),
        )[0].moves[0]
        self.assertEqual(
            move_ir.semantic_fragments,
            (action_fragment, change_fragment),
        )
        self.assertEqual(
            move_ir.semantic_heads,
            tuple(
                reception_owner._source_grounded_predicate_head(fragment)
                for fragment in move_ir.semantic_fragments
            ),
        )
        self.assertTrue(all(move_ir.semantic_heads))
        self.assertTrue(
            all(
                head in fragment and len(head) <= 24
                for head, fragment in zip(
                    move_ir.semantic_heads,
                    move_ir.semantic_fragments,
                    strict=True,
                )
            )
        )
        self.assertEqual(len(move_ir.relations), 1)
        relation_ir = move_ir.relations[0]
        self.assertEqual(relation_ir.relation_kind, "action_supports_change")
        self.assertEqual(relation_ir.endpoint_roles, ("ACTION", "CHANGE"))
        relation_arguments = tuple(
            argument
            for argument in move_ir.arguments
            if argument.relation_slot == 0
        )
        self.assertEqual(
            tuple(argument.semantic_role for argument in relation_arguments),
            relation_ir.endpoint_roles,
        )
        self.assertEqual(
            tuple(argument.case_marker for argument in relation_arguments),
            tuple(
                reception_owner.source_grounded_case_marker_for_role(
                    role,
                    relation_ir.relation_kind,
                )
                for role in relation_ir.endpoint_roles
            ),
        )
        self.assertEqual(
            tuple(argument.direction_side for argument in relation_arguments),
            ("FROM", "TO"),
        )
        self.assertEqual(move_ir.relation_predicate_kinds, ("present_change",))
        self.assertEqual(move_ir.governing_relation_slots, (0,))
        self.assertEqual(move_ir.predicate_kind, "present_change")
        self.assertNotIn(raw_text, reception_text)
        referent = reception_owner.resolve_grounded_reception_move_referent(
            reception_plan,
            move,
            nucleus_index,
            artifacts.resolver,
            allow_short_anchor=bool(clause_plan.quote_budget),
            recovery_stage=artifacts.sentence_plan.recovery_stage,
            allow_anaphoric_topic=True,
        )
        self.assertFalse(referent.source_anchor_used)
        visible_referent = referent.text.replace("「", "").replace("」", "")
        self.assertEqual(reception_text.count(visible_referent), 1)

    def test_0058_typed_fragments_reject_whole_span_and_wrong_source(
        self,
    ) -> None:
        case_id = "nls3s_b001_0058"
        artifacts = self.artifacts[case_id]
        reception_plan = artifacts.plan.response_plan.human_reception_plan
        move = reception_plan.moves[0]
        nucleus_index = {
            nucleus.nucleus_id: nucleus for nucleus in artifacts.plan.nuclei
        }
        action_nucleus = nucleus_index[move.target_nucleus_ids[0]]
        raw_text = artifacts.resolver.resolve(
            action_nucleus.source_span_ids[0]
        ).raw_text
        action_fragment = reception_owner._typed_reception_source_fragment(
            action_nucleus,
            raw_text,
        )
        self.assertIsNotNone(action_fragment)

        reception_line = next(
            line
            for line in artifacts.sentence_plan.lines
            if line.binding.line_role == "human_follow"
        )
        clause_plan = reception_line.reception_clause_plans[0]
        referent = reception_owner.resolve_grounded_reception_move_referent(
            reception_plan,
            move,
            nucleus_index,
            artifacts.resolver,
            allow_short_anchor=bool(clause_plan.quote_budget),
            recovery_stage=artifacts.sentence_plan.recovery_stage,
            allow_anaphoric_topic=True,
        )
        self.assertFalse(referent.source_anchor_used)
        visible_referent = referent.text.replace("「", "").replace("」", "")
        self.assertTrue(visible_referent)
        baseline_reception = _reception_text(artifacts.surface.text)
        self.assertEqual(baseline_reception.count(visible_referent), 1)
        whole_span_referent = f"「{raw_text}」"
        self.assertNotEqual(visible_referent, raw_text)
        whole_span_body = _tamper_reception(
            artifacts.surface.text,
            visible_referent,
            whole_span_referent,
        )
        self.assertNotEqual(whole_span_body, artifacts.surface.text)
        self.assertEqual(
            _reception_text(whole_span_body).count(visible_referent),
            0,
        )
        with self.assertRaises(
            reception_owner.GroundedHumanReceptionSurfaceError
        ) as raised:
            self._bind_reception_text(
                case_id,
                _reception_text(whole_span_body),
            )
        self.assertIn(
            "human_reception_source_anchor_unbound",
            str(raised.exception),
        )
        self.assertIn(
            "human_reception_move_target_missing:rm1",
            str(raised.exception),
        )
        whole_span_inverse = self._inverse_for_tamper(
            case_id,
            whole_span_body,
        )
        self.assertIn(
            "body_inverse_reception_target_referent_missing:rm1",
            whole_span_inverse.failure_codes,
        )
        whole_span_gate = self._gate_for_tampered_body(
            case_id,
            whole_span_body,
        )
        self.assertFalse(whole_span_gate.passed)
        self.assertIn(
            "reception_actual_surface_contract_failed",
            whole_span_gate.rejection_reasons,
        )

        context_ids = reception_owner.final_reception_context_nucleus_ids(
            move=move,
            plan=artifacts.plan,
        )
        self.assertEqual(len(context_ids), 1)
        context_fragment = reception_owner._typed_reception_source_fragment(
            nucleus_index[context_ids[0]],
            raw_text,
        )
        self.assertTrue(context_fragment)
        assert context_fragment is not None
        baseline_reception = _reception_text(artifacts.surface.text)
        self.assertEqual(baseline_reception.count(context_fragment), 1)
        missing_context_replacement = "文脈を欠いたもの"
        self.assertNotIn(missing_context_replacement, baseline_reception)
        self.assertNotIn(context_fragment, missing_context_replacement)
        missing_context_body = _tamper_reception(
            artifacts.surface.text,
            context_fragment,
            missing_context_replacement,
        )
        self.assertNotEqual(missing_context_body, artifacts.surface.text)
        self.assertEqual(
            _reception_text(missing_context_body).count(context_fragment),
            0,
        )
        with self.assertRaisesRegex(
            reception_owner.GroundedHumanReceptionSurfaceError,
            "human_reception_move_context_missing:rm1",
        ):
            self._bind_reception_text(
                case_id,
                _reception_text(missing_context_body),
            )
        missing_context_inverse = self._inverse_for_tamper(
            case_id,
            missing_context_body,
        )
        self.assertIn(
            "body_inverse_reception_context_anchor_missing:rm1",
            missing_context_inverse.failure_codes,
        )
        self.assertIn(
            "body_inverse_reception_why_duty_missing:rm1",
            missing_context_inverse.failure_codes,
        )
        missing_context_gate = self._gate_for_tampered_body(
            case_id,
            missing_context_body,
        )
        self.assertFalse(missing_context_gate.passed)
        self.assertIn(
            "reception_actual_surface_contract_failed",
            missing_context_gate.rejection_reasons,
        )

        context_nucleus = nucleus_index[context_ids[0]]
        context_attributes = tuple(
            context_nucleus.semantic_frame.attribute_codes
        )
        self.assertIn(
            "semantic_role:generic_relation_fragment",
            context_attributes,
        )
        self.assertTrue(
            any(
                code.startswith(
                    (
                        "source_fragment_scalar_range:",
                        "source_fragment_scalar_source:",
                    )
                )
                for code in context_attributes
            )
        )
        markerless_context_nucleus = replace(
            context_nucleus,
            semantic_frame=replace(
                context_nucleus.semantic_frame,
                attribute_codes=tuple(
                    code
                    for code in context_attributes
                    if code != "semantic_role:generic_relation_fragment"
                ),
            ),
        )
        markerless_plan = replace(
            artifacts.plan,
            nuclei=tuple(
                markerless_context_nucleus
                if nucleus.nucleus_id == context_nucleus.nucleus_id
                else nucleus
                for nucleus in artifacts.plan.nuclei
            ),
        )
        markerless_inverse = evaluate_grounded_surface_body_inverse(
            body=artifacts.surface.text.encode("utf-8"),
            plan=markerless_plan,
            sentence_plan=artifacts.sentence_plan,
            resolver=artifacts.resolver,
        )
        self.assertFalse(markerless_inverse.passed)
        self.assertIn(
            "body_inverse_reception_context_anchor_missing:rm1",
            markerless_inverse.failure_codes,
        )
        self.assertIn(
            "body_inverse_reception_why_duty_missing:rm1",
            markerless_inverse.failure_codes,
        )
        with self.assertRaisesRegex(
            reception_owner.GroundedHumanReceptionSurfaceError,
            "typed_reception_source_fragment_contract_invalid",
        ):
            reception_owner.bind_and_validate_grounded_human_reception_surface(
                reception_plan,
                {
                    nucleus.nucleus_id: nucleus
                    for nucleus in markerless_plan.nuclei
                },
                artifacts.resolver,
                actual_text=baseline_reception.strip(),
                recovery_stage=artifacts.sentence_plan.recovery_stage,
                clause_plans=tuple(reception_line.reception_clause_plans),
                context_nucleus_ids_by_move={
                    active_move.move_id:
                    reception_owner.final_reception_context_nucleus_ids(
                        move=active_move,
                        plan=markerless_plan,
                    )
                    for active_move in reception_owner.reception_active_moves(
                        reception_plan,
                        artifacts.sentence_plan.recovery_stage,
                    )
                },
                allow_anaphoric_topic=True,
            )

        for invalid_support_ids, mutation_kind in (
            (
                (context_ids[0], context_ids[0]),
                "duplicate_context_owner",
            ),
            (
                (move.target_nucleus_ids[0],),
                "target_context_overlap",
            ),
        ):
            with self.subTest(context_owner_mutation=mutation_kind):
                invalid_move = replace(
                    move,
                    support_nucleus_ids=invalid_support_ids,
                )
                invalid_reception_plan = replace(
                    reception_plan,
                    moves=tuple(
                        invalid_move
                        if candidate.move_id == move.move_id
                        else candidate
                        for candidate in reception_plan.moves
                    ),
                )
                invalid_owner_plan = replace(
                    artifacts.plan,
                    response_plan=replace(
                        artifacts.plan.response_plan,
                        human_reception_plan=invalid_reception_plan,
                    ),
                )
                with self.assertRaisesRegex(
                    ValueError,
                    "context_owner_ambiguous",
                ):
                    gate_owner._body_inverse_reception_context_expectation(
                        invalid_move,
                        invalid_owner_plan,
                        artifacts.resolver,
                    )
                invalid_owner_inverse = (
                    evaluate_grounded_surface_body_inverse(
                        body=artifacts.surface.text.encode("utf-8"),
                        plan=invalid_owner_plan,
                        sentence_plan=artifacts.sentence_plan,
                        resolver=artifacts.resolver,
                    )
                )
                self.assertFalse(invalid_owner_inverse.passed)
                self.assertIn(
                    "body_inverse_reception_context_anchor_missing:rm1",
                    invalid_owner_inverse.failure_codes,
                )
                self.assertIn(
                    "body_inverse_reception_why_duty_missing:rm1",
                    invalid_owner_inverse.failure_codes,
                )

        wrong_source_nucleus = replace(
            action_nucleus,
            semantic_frame=replace(
                action_nucleus.semantic_frame,
                attribute_codes=tuple(
                    "source_fragment_scalar_source:surface_text"
                    if code
                    == "source_fragment_scalar_source:normalized_raw_text"
                    else code
                    for code in action_nucleus.semantic_frame.attribute_codes
                ),
            ),
        )
        with self.assertRaisesRegex(
            reception_owner.GroundedHumanReceptionSurfaceError,
            "typed_reception_source_fragment_contract_invalid",
        ):
            reception_owner._typed_reception_source_fragment(
                wrong_source_nucleus,
                raw_text,
            )
        with self.assertRaisesRegex(
            surface_owner.GroundedSentenceSurfaceError,
            "typed_source_fragment_contract_invalid",
        ):
            surface_owner._typed_source_fragment_for_nucleus(
                wrong_source_nucleus,
                raw_text,
            )
        wrong_source_plan = replace(
            artifacts.plan,
            nuclei=tuple(
                wrong_source_nucleus
                if nucleus.nucleus_id == wrong_source_nucleus.nucleus_id
                else nucleus
                for nucleus in artifacts.plan.nuclei
            ),
        )
        wrong_source_inverse = evaluate_grounded_surface_body_inverse(
            body=artifacts.surface.text.encode("utf-8"),
            plan=wrong_source_plan,
            sentence_plan=artifacts.sentence_plan,
            resolver=artifacts.resolver,
        )
        self.assertFalse(wrong_source_inverse.passed)
        self.assertIn(
            "body_inverse_relation_endpoint_missing:1",
            wrong_source_inverse.failure_codes,
        )
        wrong_source_gate = evaluate_grounded_observation_gate(
            plan=wrong_source_plan,
            sentence_plan=artifacts.sentence_plan,
            surface_result=artifacts.surface,
            resolver=artifacts.resolver,
            product_readfeel_status="not_evaluated",
            require_body_inverse=True,
        )
        self.assertFalse(wrong_source_gate.passed)

    def test_typed_time_precedes_intention_modality_in_body_inverse(
        self,
    ) -> None:
        completed_negative = self.artifacts["nls3s_b001_0007"]
        self.assertNotIn(
            "これからの行動",
            completed_negative.surface.text,
        )
        negated_action = next(
            nucleus
            for nucleus in completed_negative.plan.nuclei
            if nucleus.kind == "action"
        )
        self.assertFalse(
            reception_owner.reception_action_is_future_intention(
                negated_action
            )
        )

        artifacts = self.artifacts["nls3s_b001_0090"]
        past = next(
            nucleus
            for nucleus in artifacts.plan.nuclei
            if nucleus.kind == "action"
            and nucleus.semantic_frame.time_scope == "past"
        )
        self.assertFalse(surface_owner._final_action_is_future_intention(past))
        self.assertFalse(gate_owner._body_inverse_action_is_future_intention(past))

        base_attributes = tuple(
            code
            for code in past.semantic_frame.attribute_codes
            if not code.startswith("time_scope:")
        )
        completed = replace(
            past,
            semantic_frame=replace(
                past.semantic_frame,
                time_scope="present",
                attribute_codes=(*base_attributes, "aspect:completed"),
            ),
        )
        future = replace(
            past,
            semantic_frame=replace(
                past.semantic_frame,
                time_scope="future",
                attribute_codes=(*base_attributes, "time_scope:future"),
            ),
        )
        self.assertFalse(
            surface_owner._final_action_is_future_intention(completed)
        )
        self.assertFalse(
            gate_owner._body_inverse_action_is_future_intention(completed)
        )
        self.assertTrue(surface_owner._final_action_is_future_intention(future))
        self.assertTrue(gate_owner._body_inverse_action_is_future_intention(future))

        def plan_with(replacement_nucleus):
            return replace(
                artifacts.plan,
                nuclei=tuple(
                    replacement_nucleus
                    if nucleus.nucleus_id == past.nucleus_id
                    else nucleus
                    for nucleus in artifacts.plan.nuclei
                ),
            )

        completed_inverse = evaluate_grounded_surface_body_inverse(
            body=artifacts.surface.text.encode("utf-8"),
            plan=plan_with(completed),
            sentence_plan=artifacts.sentence_plan,
            resolver=artifacts.resolver,
        )
        self.assertNotIn(
            "body_inverse_required_intention_missing:1",
            completed_inverse.failure_codes,
        )
        future_inverse = evaluate_grounded_surface_body_inverse(
            body=artifacts.surface.text.encode("utf-8"),
            plan=plan_with(future),
            sentence_plan=artifacts.sentence_plan,
            resolver=artifacts.resolver,
        )
        self.assertIn(
            "body_inverse_required_intention_missing:1",
            future_inverse.failure_codes,
        )

    def test_target_marker_deletion_is_rejected(self) -> None:
        case_id = "nls3s_b001_0024"
        artifacts = self.artifacts[case_id]
        reception_plan = artifacts.plan.response_plan.human_reception_plan
        move = reception_plan.moves[0]
        referent = reception_owner.resolve_grounded_reception_move_referent(
            reception_plan,
            move,
            {nucleus.nucleus_id: nucleus for nucleus in artifacts.plan.nuclei},
            artifacts.resolver,
            allow_short_anchor=False,
            recovery_stage=artifacts.sentence_plan.recovery_stage,
            allow_anaphoric_topic=True,
        )
        visible_referent = referent.text.replace("「", "").replace("」", "")
        baseline_reception = _reception_text(artifacts.surface.text)
        self.assertEqual(baseline_reception.count(visible_referent), 1)
        body = _tamper_reception(
            artifacts.surface.text,
            visible_referent,
            "対象",
        )
        self.assertNotEqual(body, artifacts.surface.text)
        self.assertEqual(_reception_text(body).count(visible_referent), 0)
        inverse = self._inverse_for_tamper(case_id, body)
        self.assertIn(
            "body_inverse_reception_target_referent_missing:rm1",
            inverse.failure_codes,
        )

    def test_required_target_referent_deletion_is_rejected(self) -> None:
        case_id = "nls3s_b001_0029"
        artifacts = self.artifacts[case_id]
        reception_plan = artifacts.plan.response_plan.human_reception_plan
        self.assertIsNotNone(reception_plan)
        assert reception_plan is not None
        move = next(
            row
            for row in reception_plan.moves
            if row.move_id == "rm1"
        )
        reception_line_plan = next(
            row
            for row in artifacts.sentence_plan.lines
            if row.binding.line_role == "human_follow"
        )
        clause_plan = next(
            row
            for row in reception_line_plan.reception_clause_plans
            if move.move_id in row.move_ids
        )
        referent = reception_owner.resolve_grounded_reception_move_referent(
            reception_plan,
            move,
            {
                nucleus.nucleus_id: nucleus
                for nucleus in artifacts.plan.nuclei
            },
            artifacts.resolver,
            allow_short_anchor=bool(clause_plan.quote_budget),
            recovery_stage=artifacts.sentence_plan.recovery_stage,
            allow_anaphoric_topic=True,
        )
        visible_referent = referent.text.replace("「", "").replace("」", "")
        self.assertTrue(visible_referent)
        baseline_reception = _reception_text(artifacts.surface.text)
        self.assertEqual(baseline_reception.count(visible_referent), 1)
        baseline_witness = surface_owner.parse_grounded_surface_body_bytes(
            artifacts.surface.text.encode("utf-8")
        )
        target_markers = tuple(
            marker
            for marker in baseline_witness.markers
            if marker.section == "reception"
            and marker.marker_kind == "reception"
            and marker.marker_code == "target_intention"
        )
        self.assertEqual(len(target_markers), 1)
        bound = self._bind_reception_text(case_id, baseline_reception)
        self.assertEqual(bound.text.count(visible_referent), 1)

        body = _tamper_reception(
            artifacts.surface.text,
            visible_referent,
            "対象",
        )
        self.assertNotEqual(body, artifacts.surface.text)
        inverse = self._inverse_for_tamper(case_id, body)
        self.assertFalse(inverse.passed)
        self.assertIn(
            "body_inverse_reception_target_referent_missing:rm1",
            inverse.failure_codes,
        )
        with self.assertRaisesRegex(
            reception_owner.GroundedHumanReceptionSurfaceError,
            "human_reception_move_target_missing:rm1",
        ):
            self._bind_reception_text(
                case_id,
                _reception_text(body),
            )

        duplicate_body = _tamper_reception(
            artifacts.surface.text,
            visible_referent,
            f"{visible_referent}{visible_referent}",
        )
        self.assertNotEqual(duplicate_body, artifacts.surface.text)
        duplicate_witness = surface_owner.parse_grounded_surface_body_bytes(
            duplicate_body.encode("utf-8")
        )
        duplicate_target_markers = tuple(
            marker
            for marker in duplicate_witness.markers
            if marker.section == "reception"
            and marker.marker_kind == "reception"
            and marker.marker_code == "target_intention"
        )
        self.assertEqual(len(duplicate_target_markers), 2)
        with self.assertRaisesRegex(
            reception_owner.GroundedHumanReceptionSurfaceError,
            "human_reception_move_target_duplicate:rm1",
        ):
            self._bind_reception_text(
                case_id,
                _reception_text(duplicate_body),
            )

    def test_explicit_target_cannot_be_replaced_by_a_generic_marker(
        self,
    ) -> None:
        case_id = "nls3s_b001_0024"
        artifacts = self.artifacts[case_id]
        reception_plan = artifacts.plan.response_plan.human_reception_plan
        move = reception_plan.moves[0]
        referent = reception_owner.resolve_grounded_reception_move_referent(
            reception_plan,
            move,
            {nucleus.nucleus_id: nucleus for nucleus in artifacts.plan.nuclei},
            artifacts.resolver,
            allow_short_anchor=False,
            recovery_stage=artifacts.sentence_plan.recovery_stage,
            allow_anaphoric_topic=True,
        )
        visible_referent = referent.text.replace("「", "").replace("」", "")
        baseline_reception = _reception_text(artifacts.surface.text)
        self.assertEqual(baseline_reception.count(visible_referent), 1)
        body = _tamper_reception(
            artifacts.surface.text,
            visible_referent,
            "一般的な対象",
        )
        self.assertNotEqual(body, artifacts.surface.text)
        self.assertEqual(_reception_text(body).count(visible_referent), 0)
        inverse = self._inverse_for_tamper(case_id, body)
        self.assertIn(
            "body_inverse_reception_target_referent_missing:rm1",
            inverse.failure_codes,
        )
        gate = self._gate_for_tampered_body(case_id, body)
        self.assertFalse(gate.passed)
        self.assertIn(
            "reception_actual_surface_contract_failed",
            gate.rejection_reasons,
        )

    def test_attention_deletion_is_rejected(self) -> None:
        case_id = "nls3s_b001_0024"
        body = _tamper_reception(
            self.artifacts[case_id].surface.text,
            "目が留まり",
            "心に触れ",
        )
        inverse = self._inverse_for_tamper(case_id, body)
        self.assertIn(
            "body_inverse_reception_attention_duty_missing:rm1",
            inverse.failure_codes,
        )
        with self.assertRaisesRegex(
            reception_owner.GroundedHumanReceptionSurfaceError,
            "human_reception_move_attention_missing:rm1",
        ):
            self._bind_reception_text(
                case_id,
                _reception_text(body),
            )

    def test_relation_context_deletion_is_rejected(self) -> None:
        case_id = "nls3s_b001_0076"
        artifacts = self.artifacts[case_id]
        reception_plan = artifacts.plan.response_plan.human_reception_plan
        move = reception_plan.moves[0]
        nucleus_index = {
            nucleus.nucleus_id: nucleus for nucleus in artifacts.plan.nuclei
        }
        context_id = reception_owner.final_reception_context_nucleus_id(
            move=move,
            plan=artifacts.plan,
        )
        raw_context = reception_owner.final_reception_source_anchor_text(
            context_id,
            nucleus_index,
            artifacts.resolver,
        )
        reception_line = next(
            line
            for line in artifacts.sentence_plan.lines
            if line.binding.line_role == "human_follow"
        )
        move_ir = reception_owner._source_grounded_plan_clause_realizations(
            reception_plan,
            nucleus_index,
            artifacts.resolver,
            plan=artifacts.plan,
            recovery_stage=artifacts.sentence_plan.recovery_stage,
            clause_plans=tuple(reception_line.reception_clause_plans),
        )[0].moves[0]
        context_adjunct = reception_owner._source_grounded_context_adjunct(
            move_ir
        )
        baseline_reception = _reception_text(artifacts.surface.text)
        self.assertTrue(raw_context)
        self.assertTrue(context_adjunct)
        self.assertNotEqual(context_adjunct, raw_context)
        self.assertEqual(baseline_reception.count(context_adjunct), 1)
        punctuation_offset = max(1, len(context_adjunct) // 2)
        punctuated_context_adjunct = (
            context_adjunct[:punctuation_offset]
            + "、"
            + context_adjunct[punctuation_offset:]
        )
        ellipsis_context_adjunct = (
            context_adjunct[:punctuation_offset]
            + "…"
            + context_adjunct[punctuation_offset:]
        )
        zero_width_raw_context = "\u200b".join(raw_context)
        body = _tamper_reception(
            artifacts.surface.text,
            context_adjunct,
            "その状況を背景に、",
        )
        inverse = self._inverse_for_tamper(case_id, body)
        self.assertIn(
            "body_inverse_reception_context_anchor_missing:rm1",
            inverse.failure_codes,
        )
        self.assertIn(
            "body_inverse_reception_why_duty_missing:rm1",
            inverse.failure_codes,
        )
        with self.assertRaisesRegex(
            reception_owner.GroundedHumanReceptionSurfaceError,
            "human_reception_move_context_missing:rm1",
        ):
            self._bind_reception_text(
                case_id,
                _reception_text(body),
            )

        for replacement, mutation_kind in (
            (
                raw_context,
                "raw_whole_clause",
            ),
            (
                f"「{raw_context}」",
                "quoted_whole_clause",
            ),
            (
                context_adjunct + context_adjunct,
                "duplicate_adjunct",
            ),
            (
                punctuated_context_adjunct,
                "internal_punctuation",
            ),
            (
                context_adjunct + punctuated_context_adjunct,
                "punctuation_obfuscated_duplicate",
            ),
            (
                context_adjunct + ellipsis_context_adjunct,
                "ellipsis_obfuscated_duplicate",
            ),
            (
                f'"{context_adjunct}"',
                "ascii_quoted_adjunct",
            ),
            (
                f"“{context_adjunct}”",
                "curly_quoted_adjunct",
            ),
            (
                ("prefix" * 16) + context_adjunct,
                "long_arbitrary_prefix",
            ),
            (
                "、" + context_adjunct,
                "extra_leading_delimiter",
            ),
            (
                raw_context + context_adjunct,
                "raw_and_derived_adjunct",
            ),
            (
                context_adjunct + f"“{raw_context}”",
                "curly_quoted_raw_after_adjunct",
            ),
            (
                context_adjunct + zero_width_raw_context,
                "zero_width_raw_after_adjunct",
            ),
        ):
            with self.subTest(context_mutation=mutation_kind):
                mutated_body = _tamper_reception(
                    artifacts.surface.text,
                    context_adjunct,
                    replacement,
                )
                mutated_inverse = self._inverse_for_tamper(
                    case_id,
                    mutated_body,
                )
                self.assertFalse(mutated_inverse.passed)
                self.assertIn(
                    "body_inverse_reception_context_anchor_missing:rm1",
                    mutated_inverse.failure_codes,
                )
                self.assertIn(
                    "body_inverse_reception_why_duty_missing:rm1",
                    mutated_inverse.failure_codes,
                )
                with self.assertRaisesRegex(
                    reception_owner.GroundedHumanReceptionSurfaceError,
                    "human_reception_move_context_missing:rm1",
                ):
                    self._bind_reception_text(
                        case_id,
                        _reception_text(mutated_body),
                    )

        terminal_index = baseline_reception.rfind("。")
        self.assertGreaterEqual(terminal_index, 0)
        trailing_duplicate_reception = (
            baseline_reception[:terminal_index]
            + context_adjunct
            + baseline_reception[terminal_index:]
        )
        trailing_duplicate_body = _tamper_reception(
            artifacts.surface.text,
            baseline_reception,
            trailing_duplicate_reception,
        )
        trailing_duplicate_inverse = self._inverse_for_tamper(
            case_id,
            trailing_duplicate_body,
        )
        self.assertFalse(trailing_duplicate_inverse.passed)
        self.assertIn(
            "body_inverse_reception_context_anchor_missing:rm1",
            trailing_duplicate_inverse.failure_codes,
        )
        self.assertIn(
            "body_inverse_reception_why_duty_missing:rm1",
            trailing_duplicate_inverse.failure_codes,
        )
        with self.assertRaisesRegex(
            reception_owner.GroundedHumanReceptionSurfaceError,
            "human_reception_move_context_missing:rm1",
        ):
            self._bind_reception_text(
                case_id,
                trailing_duplicate_reception,
            )

    def test_importance_predicate_deletion_is_rejected(self) -> None:
        case_id = "nls3s_b001_0054"
        body = self.artifacts[case_id].surface.text.encode("utf-8")
        witness = surface_owner.parse_grounded_surface_body_bytes(body)
        importance_spans = tuple(
            marker
            for marker in witness.markers
            if marker.section == "reception"
            and marker.marker_kind == "reception"
            and marker.marker_code in {"receive", "felt_response"}
        )
        self.assertTrue(importance_spans)
        merged_ranges: list[tuple[int, int]] = []
        for marker in sorted(
            importance_spans,
            key=lambda row: row.utf8_byte_start,
        ):
            if (
                merged_ranges
                and marker.utf8_byte_start <= merged_ranges[-1][1]
            ):
                merged_ranges[-1] = (
                    merged_ranges[-1][0],
                    max(merged_ranges[-1][1], marker.utf8_byte_end),
                )
            else:
                merged_ranges.append(
                    (marker.utf8_byte_start, marker.utf8_byte_end)
                )
        tampered = body
        for start, end in reversed(merged_ranges):
            tampered = (
                tampered[:start]
                + "そこにあります".encode("utf-8")
                + tampered[end:]
            )
        self.assertNotEqual(tampered, body)
        tampered_witness = surface_owner.parse_grounded_surface_body_bytes(
            tampered
        )
        tampered_reception = next(
            row
            for row in tampered_witness.lines
            if row.section == "reception"
        )
        self.assertTrue(
            {"receive", "felt_response"}.isdisjoint(
                tampered_reception.reception_marker_codes
            )
        )
        tampered_text = tampered.decode("utf-8")
        inverse = self._inverse_for_tamper(case_id, tampered_text)
        self.assertFalse(inverse.passed)
        self.assertIn(
            "body_inverse_reception_why_duty_missing:rm1",
            inverse.failure_codes,
        )
        with self.assertRaisesRegex(
            reception_owner.GroundedHumanReceptionSurfaceError,
            "human_reception_act_responsibility_missing",
        ):
            self._bind_reception_text(
                case_id,
                _reception_text(tampered_text),
            )

    def test_required_change_marker_deletion_is_rejected(self) -> None:
        case_id = "nls3s_b001_0081"
        body = self.artifacts[case_id].surface.text
        observation, separator, reception = body.partition(
            surface_owner.RECEPTION_SECTION_LABEL
        )
        self.assertIn("変化", observation)
        tampered = (
            observation.replace("変化", "状態")
            + separator
            + reception
        )
        inverse = self._inverse_for_tamper(case_id, tampered)
        self.assertIn(
            "body_inverse_required_change_missing:1",
            inverse.failure_codes,
        )

    def test_anaphoric_target_does_not_require_source_anchor(self) -> None:
        case_id = "nls3s_b001_0051"
        artifacts = self.artifacts[case_id]
        reception_plan = artifacts.plan.response_plan.human_reception_plan
        move = reception_plan.moves[0]
        self.assertEqual(move.reference_mode, "anaphoric_first")
        self.assertTrue(artifacts.inverse.passed, artifacts.inverse.failure_codes)
        nucleus_index = {
            nucleus.nucleus_id: nucleus for nucleus in artifacts.plan.nuclei
        }
        target = reception_owner.final_reception_nucleus_text(
            move.target_nucleus_ids[0],
            nucleus_index,
            artifacts.resolver,
        )
        self.assertNotIn(target, _reception_text(artifacts.surface.text))
        replayed_body = _tamper_reception(
            artifacts.surface.text,
            "そのつらさ",
            f"そのつらさ（{target}）",
        )
        replayed_inverse = self._inverse_for_tamper(
            case_id,
            replayed_body,
        )
        self.assertIn(
            "body_inverse_reception_anaphoric_target_replayed:rm1",
            replayed_inverse.failure_codes,
        )
        replayed_gate = self._gate_for_tampered_body(
            case_id,
            replayed_body,
        )
        self.assertFalse(replayed_gate.passed)
        self.assertIn(
            "reception_actual_surface_contract_failed",
            replayed_gate.rejection_reasons,
        )

    def test_recovery_anaphoric_context_is_required_without_exact_replay(
        self,
    ) -> None:
        case_id = "nls3s_b001_0076"
        artifacts = self.artifacts[case_id]
        recovered_plan = surface_owner.build_reception_recovery_sentence_plan(
            artifacts.sentence_plan,
            artifacts.plan,
            artifacts.resolver,
            recovery_stage="integrated",
        )
        recovered_surface = surface_owner.realize_grounded_sentence_plan(
            recovered_plan,
            artifacts.plan,
            artifacts.resolver,
        )
        reception = _reception_text(recovered_surface.text)
        move = artifacts.plan.response_plan.human_reception_plan.moves[0]
        context_id = reception_owner.final_reception_context_nucleus_ids(
            move=move,
            plan=artifacts.plan,
        )[0]
        nucleus_index = {
            nucleus.nucleus_id: nucleus for nucleus in artifacts.plan.nuclei
        }
        typed_context = reception_owner.final_reception_anaphoric_context(
            move=move,
            context_nucleus_ids=(context_id,),
            plan=artifacts.plan,
            nucleus_index=nucleus_index,
            resolver=artifacts.resolver,
        )
        context_anaphor = f"{typed_context}が重なる中で、"
        anaphoric_prefix = context_anaphor
        self.assertTrue(reception.strip().startswith(anaphoric_prefix))

        missing_body = _tamper_reception(
            recovered_surface.text,
            anaphoric_prefix,
            "",
        )
        missing_inverse = evaluate_grounded_surface_body_inverse(
            body=missing_body.encode("utf-8"),
            plan=artifacts.plan,
            sentence_plan=recovered_plan,
            resolver=artifacts.resolver,
        )
        self.assertIn(
            "body_inverse_reception_context_anchor_missing:rm1",
            missing_inverse.failure_codes,
        )
        missing_gate = self._gate_for_tampered_body(
            case_id,
            missing_body,
            sentence_plan=recovered_plan,
            base_surface=recovered_surface,
        )
        self.assertFalse(missing_gate.passed)
        self.assertIn(
            "reception_actual_surface_contract_failed",
            missing_gate.rejection_reasons,
        )

        exact_context = reception_owner.final_reception_source_anchor_text(
            context_id,
            nucleus_index,
            artifacts.resolver,
        )
        replayed_body = _tamper_reception(
            recovered_surface.text,
            context_anaphor,
            f"{exact_context}という言葉が重なる中で、",
        )
        replayed_inverse = evaluate_grounded_surface_body_inverse(
            body=replayed_body.encode("utf-8"),
            plan=artifacts.plan,
            sentence_plan=recovered_plan,
            resolver=artifacts.resolver,
        )
        self.assertIn(
            "body_inverse_reception_anaphoric_context_replayed:rm1",
            replayed_inverse.failure_codes,
        )
        replayed_gate = self._gate_for_tampered_body(
            case_id,
            replayed_body,
            sentence_plan=recovered_plan,
            base_surface=recovered_surface,
        )
        self.assertFalse(replayed_gate.passed)
        self.assertIn(
            "reception_actual_surface_contract_failed",
            replayed_gate.rejection_reasons,
        )

    def test_quote_zero_recovery_uses_effective_anaphoric_reference(
        self,
    ) -> None:
        case_id = "nls3s_b001_0029"
        artifacts = self.artifacts[case_id]
        recovered_plan = surface_owner.build_reception_recovery_sentence_plan(
            artifacts.sentence_plan,
            artifacts.plan,
            artifacts.resolver,
            recovery_stage="integrated",
        )
        clause = next(
            line.reception_clause_plans[0]
            for line in recovered_plan.lines
            if line.binding.line_role == "human_follow"
        )
        self.assertEqual(clause.quote_budget, 0)
        recovered_surface = surface_owner.realize_grounded_sentence_plan(
            recovered_plan,
            artifacts.plan,
            artifacts.resolver,
        )
        move = artifacts.plan.response_plan.human_reception_plan.moves[0]
        self.assertEqual(
            reception_owner.reception_effective_move_reference_mode(
                artifacts.plan.response_plan.human_reception_plan,
                move,
                recovered_plan.recovery_stage,
            ),
            "anaphoric_first",
        )
        nucleus_index = {
            nucleus.nucleus_id: nucleus for nucleus in artifacts.plan.nuclei
        }
        target = reception_owner.final_reception_nucleus_text(
            move.target_nucleus_ids[0],
            nucleus_index,
            artifacts.resolver,
        )
        reception = _reception_text(recovered_surface.text)
        self.assertNotIn(target, reception)
        self.assertNotIn(f"「{target}」", reception)
        self.assertIn("その願い", reception)
        self._bind_reception_text(
            case_id,
            reception,
            sentence_plan=recovered_plan,
        )
        inverse = evaluate_grounded_surface_body_inverse(
            body=recovered_surface.text.encode("utf-8"),
            plan=artifacts.plan,
            sentence_plan=recovered_plan,
            resolver=artifacts.resolver,
        )
        self.assertTrue(inverse.passed, inverse.failure_codes)
        gate = evaluate_grounded_observation_gate(
            plan=artifacts.plan,
            sentence_plan=recovered_plan,
            surface_result=recovered_surface,
            resolver=artifacts.resolver,
            product_readfeel_status="not_evaluated",
            require_body_inverse=True,
        )
        self.assertTrue(gate.passed, gate.rejection_reasons)


if __name__ == "__main__":
    unittest.main()
