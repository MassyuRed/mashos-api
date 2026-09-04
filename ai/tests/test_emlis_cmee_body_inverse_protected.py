# -*- coding: utf-8 -*-
from __future__ import annotations

"""Protected D21 vectors for the CMEE use of the existing Emlis owner."""

from dataclasses import replace
import inspect
import json
from pathlib import Path
import unittest

from helpers.emlis_ai_grounded_observation_i6_cases import (
    GROUND_OBSERVATION_I6_BLIND_CASES,
)
from emlis_ai_current_input_bundle import normalize_emlis_current_input
from emlis_ai_evidence_ledger_service import (
    build_evidence_ledger,
    build_evidence_span_resolver,
)
from emlis_ai_grounded_observation_gate import (
    evaluate_grounded_observation_gate,
    evaluate_grounded_surface_body_inverse,
    grounded_gate_meta_is_body_free,
)
import emlis_ai_grounded_observation_gate as gate_owner
from emlis_ai_grounded_observation_plan import (
    build_final_stage1_grounded_observation_plan,
    build_grounded_observation_plan,
)
from emlis_ai_grounded_sentence_surface import (
    build_grounded_sentence_plan,
    parse_grounded_surface_body_bytes,
    realize_grounded_sentence_plan,
)
import emlis_ai_grounded_human_reception as reception_owner
import emlis_ai_grounded_sentence_surface as surface_owner
from cocolon_meaning_experience_engine.emlis_v1a import (
    _cmee_semantic_reception_plan,
)
from tools.emlis_nls_v3_batch_run import load_validated_batch


_GENERATED_FIXTURE_ROOT = (
    Path(__file__).resolve().parent / "fixtures" / "emlis_nls_v3" / "generated"
)
_CANONICAL_BATCH001_PATH = _GENERATED_FIXTURE_ROOT / "batch_001.jsonl"
_CANONICAL_BATCH001_MANIFEST_PATH = (
    _GENERATED_FIXTURE_ROOT / "batch_001_manifest.json"
)


def _artifacts(case_id: str):
    case = next(
        row for row in GROUND_OBSERVATION_I6_BLIND_CASES if row.case_id == case_id
    )
    normalized = normalize_emlis_current_input(case.as_current_input())
    spans = tuple(build_evidence_ledger(normalized))
    resolver = build_evidence_span_resolver(spans, current_input=normalized)
    plan = build_grounded_observation_plan(normalized, evidence_spans=spans)
    sentence_plan = build_grounded_sentence_plan(plan, resolver)
    surface = realize_grounded_sentence_plan(sentence_plan, plan, resolver)
    return plan, sentence_plan, surface, resolver


def _final_stage1_artifacts_from_raw(raw: dict[str, object]):
    current_input = normalize_emlis_current_input(raw)
    spans = tuple(build_evidence_ledger(current_input))
    resolver = build_evidence_span_resolver(spans, current_input=current_input)
    plan = build_final_stage1_grounded_observation_plan(
        current_input,
        evidence_spans=spans,
    )
    reception_plan = _cmee_semantic_reception_plan(plan, resolver)
    plan = replace(
        plan,
        input_profile=replace(
            plan.input_profile,
            material_quality="limited_grounding",
        ),
        response_plan=replace(
            plan.response_plan,
            response_kind="limited_grounding_observation",
            human_reception_plan=reception_plan,
        ),
        surface_policy=replace(
            plan.surface_policy,
            hedge_policy="limited_single_input_scope",
        ),
    )
    sentence_plan = build_grounded_sentence_plan(plan, resolver)
    surface = realize_grounded_sentence_plan(sentence_plan, plan, resolver)
    return plan, sentence_plan, surface, resolver


def _final_stage1_artifacts(memo: str, *, memo_action: str = ""):
    return _final_stage1_artifacts_from_raw(
        {
            "record_id": "SX-PROTECTED",
            "memo": memo,
            "memo_action": memo_action,
            "category": ["生活"],
            "emotion_details": [{"type": "自己理解", "strength": "medium"}],
            "emotions": ["自己理解"],
            "is_secret": False,
        }
    )


def _replace_body_markers(body: str, *, section: str, codes: set[str], replacement: str) -> str:
    raw = body.encode("utf-8")
    witness = parse_grounded_surface_body_bytes(raw)
    spans = sorted({(m.utf8_byte_start, m.utf8_byte_end) for m in witness.markers
                    if m.section == section and m.marker_code in codes})
    if not spans:
        raise AssertionError("semantic_mutation_marker_missing")
    merged = []
    for start, end in spans:
        if merged and start < merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    for start, end in reversed(merged):
        raw = raw[:start] + replacement.encode("utf-8") + raw[end:]
    result = raw.decode("utf-8")
    if result == body:
        raise AssertionError("semantic_mutation_noop")
    return result


class GroundedBodyOnlyParserProtectedTest(unittest.TestCase):
    def test_parser_contract_is_exact_bytes_only_and_deterministic(self) -> None:
        _plan, _sentence_plan, surface, _resolver = _artifacts("I6-C01")
        signature = inspect.signature(parse_grounded_surface_body_bytes)
        self.assertEqual(tuple(signature.parameters), ("body",))
        self.assertIn(signature.parameters["body"].annotation, (bytes, "bytes"))

        body = surface.text.encode("utf-8")
        first = parse_grounded_surface_body_bytes(body)
        second = parse_grounded_surface_body_bytes(body)
        self.assertEqual(first, second)
        self.assertTrue(first.utf8_valid)
        self.assertEqual(first.structural_issues, ())
        self.assertEqual(first.section_order, ("observation", "reception"))
        self.assertEqual(first.observation_label_count, 1)
        self.assertEqual(first.reception_label_count, 1)
        self.assertGreaterEqual(first.observation_sentence_count, 2)
        self.assertGreaterEqual(first.reception_sentence_count, 1)
        self.assertTrue(first.quotes)
        self.assertTrue(
            any(row.marker_kind == "relation" for row in first.markers)
        )
        self.assertTrue(
            any(row.marker_kind == "reception" for row in first.markers)
        )
        self.assertNotIn(surface.text, json.dumps(first.as_body_free_meta()))

    def test_parser_has_no_plan_source_or_forward_metadata_parameters(self) -> None:
        source = inspect.getsource(parse_grounded_surface_body_bytes)
        signature_text = str(inspect.signature(parse_grounded_surface_body_bytes))
        for forbidden in (
            "plan",
            "resolver",
            "source_text",
            "surface_result",
            "forward",
        ):
            self.assertNotIn(forbidden, signature_text)
        self.assertNotIn("resolver.resolve", source)
        self.assertNotIn("GroundedObservationPlan", source)
        self.assertNotIn("GroundedSentencePlan", source)

    def test_parser_fails_closed_on_invalid_utf8_and_layout(self) -> None:
        invalid = parse_grounded_surface_body_bytes(b"\xff\xfe")
        self.assertFalse(invalid.utf8_valid)
        self.assertIn("body_utf8_invalid", invalid.structural_issues)
        reversed_sections = parse_grounded_surface_body_bytes(
            "Emlisから：\n受け止めます。\n\n見えたこと：\n「入力」です。".encode(
                "utf-8"
            )
        )
        self.assertIn("body_section_order_invalid", reversed_sections.structural_issues)


class GroundedBodyInverseProtectedTest(unittest.TestCase):
    def _evaluate(self, case_id: str, body: str):
        plan, sentence_plan, _surface, resolver = _artifacts(case_id)
        return evaluate_grounded_surface_body_inverse(
            body=body.encode("utf-8"),
            plan=plan,
            sentence_plan=sentence_plan,
            resolver=resolver,
        )

    def test_unmodified_body_matches_required_semantic_and_reception_duties(self) -> None:
        plan, sentence_plan, surface, resolver = _artifacts("I6-C01")
        evaluation = evaluate_grounded_surface_body_inverse(
            body=surface.text.encode("utf-8"),
            plan=plan,
            sentence_plan=sentence_plan,
            resolver=resolver,
        )
        self.assertTrue(evaluation.passed, evaluation.failure_codes)
        meta = evaluation.as_body_free_meta()
        self.assertFalse(meta["raw_text_included"])
        self.assertFalse(meta["source_text_included"])
        self.assertFalse(meta["surface_text_included"])
        self.assertFalse(meta["candidate_body_included"])
        self.assertNotIn(surface.text, json.dumps(meta, ensure_ascii=False))

    def test_cmee_final_surface_intention_unknown_and_protective_why_are_visible(
        self,
    ) -> None:
        for memo in (
            "疲れているけれど、少し整えたい気持ちもある。",
            "変えたいのに動けなくて疲れた。ずっとこのままなのが不安で、"
            "どうしたらいいのか考えている。",
        ):
            with self.subTest(memo=memo):
                plan, sentence_plan, surface, resolver = _final_stage1_artifacts(
                    memo
                )
                witness = parse_grounded_surface_body_bytes(
                    surface.text.encode("utf-8")
                )
                observation = next(
                    row for row in witness.lines if row.section == "observation"
                )
                reception = next(
                    row for row in witness.lines if row.section == "reception"
                )
                self.assertIn("intention", observation.semantic_marker_codes)
                if "どうしたら" in memo:
                    self.assertIn("unknown", observation.semantic_marker_codes)
                self.assertIn("target_intention", reception.reception_marker_codes)
                self.assertIn("protect", reception.reception_marker_codes)
                evaluation = evaluate_grounded_surface_body_inverse(
                    body=surface.text.encode("utf-8"),
                    plan=plan,
                    sentence_plan=sentence_plan,
                    resolver=resolver,
                )
                self.assertTrue(evaluation.passed, evaluation.failure_codes)
                without_why = _replace_body_markers(
                    surface.text, section="reception", codes={"protect"}, replacement="",
                )
                missing_why = evaluate_grounded_surface_body_inverse(
                    body=without_why.encode("utf-8"),
                    plan=plan,
                    sentence_plan=sentence_plan,
                    resolver=resolver,
                )
                self.assertFalse(missing_why.passed)
                self.assertTrue(
                    any(
                        code.startswith(
                            "body_inverse_reception_why_duty_missing:"
                        )
                        for code in missing_why.failure_codes
                    )
                )

    def test_final_typed_fragments_and_reception_context_are_case_specific(
        self,
    ) -> None:
        memo = "疲れているけれど、少し整えたい気持ちもある。"
        plan, sentence_plan, surface, resolver = _final_stage1_artifacts(memo)
        observation, reception = surface.text.split("Emlisから：\n", 1)
        self.assertNotIn(memo.rstrip("。"), observation)
        self.assertIn("「少し整えたい気持ちもある」", observation)
        self.assertIn("「疲れている」", observation)
        self.assertNotIn("「少し整えたい気持ちもある」", reception)
        self.assertIn("願い", reception)
        self.assertIn("疲れている", reception)
        self.assertTrue(any(marker in reception for marker in ("中で", "中にも", "背景")))
        wrong_target = _replace_body_markers(
            surface.text, section="reception", codes={"target_intention"}, replacement="内容",
        ).split("Emlisから：\n", 1)[1]
        wrong_target_evaluation = evaluate_grounded_surface_body_inverse(
            body=(observation + "Emlisから：\n" + wrong_target).encode("utf-8"),
            plan=plan,
            sentence_plan=sentence_plan,
            resolver=resolver,
        )
        self.assertFalse(wrong_target_evaluation.passed)
        self.assertTrue(
            any(
                code.startswith(
                    "body_inverse_reception_target_duty_missing:"
                )
                for code in wrong_target_evaluation.failure_codes
            )
        )

        tampered_reception = reception.replace("疲れている", "別のこと")
        tampered = observation + "Emlisから：\n" + tampered_reception
        evaluation = evaluate_grounded_surface_body_inverse(
            body=tampered.encode("utf-8"),
            plan=plan,
            sentence_plan=sentence_plan,
            resolver=resolver,
        )
        self.assertFalse(evaluation.passed)
        self.assertIn(
            "body_inverse_reception_context_anchor_missing:rm1",
            evaluation.failure_codes,
        )
        self.assertIn(
            "body_inverse_reception_why_duty_missing:rm1",
            evaluation.failure_codes,
        )

    def test_final_directional_binding_and_body_surface_pass_for_sx07(
        self,
    ) -> None:
        plan, sentence_plan, surface, resolver = _final_stage1_artifacts(
            "この職場でやっていけるか不安。でも、続けられる形は探したい。"
        )
        relation = next(
            row
            for row in plan.relations
            if row.type == "continuation_or_refusal"
        )
        line = next(
            row
            for row in sentence_plan.lines
            if relation.relation_id in row.binding.relation_ids
        )
        self.assertLess(
            line.binding.nucleus_ids.index(relation.from_nucleus_id),
            line.binding.nucleus_ids.index(relation.to_nucleus_id),
        )
        gate = evaluate_grounded_observation_gate(
            plan=plan,
            sentence_plan=sentence_plan,
            surface_result=surface,
            resolver=resolver,
            require_body_inverse=True,
        )
        self.assertTrue(gate.passed, gate.rejection_reasons)

    def test_final_future_action_is_intention_not_performed_effort(self) -> None:
        action = "今日は少し早めに休む。"
        plan, sentence_plan, surface, resolver = _final_stage1_artifacts(
            "",
            memo_action=action,
        )
        witness = parse_grounded_surface_body_bytes(
            surface.text.encode("utf-8")
        )
        observation = next(
            row for row in witness.lines if row.section == "observation"
        )
        reception = next(
            row for row in witness.lines if row.section == "reception"
        )
        self.assertIn("intention", observation.semantic_marker_codes)
        self.assertNotIn("effort", observation.semantic_marker_codes)
        self.assertIn("これからの行動", surface.lines[0].text)
        self.assertIn("target_intention", reception.reception_marker_codes)
        self.assertIn("これからの行動", surface.text)
        self.assertNotIn("target_effort", reception.reception_marker_codes)
        self.assertNotIn("実際の行動", surface.text)
        self.assertNotIn("その手間", surface.text)
        reception_plan = plan.response_plan.human_reception_plan
        self.assertIsNotNone(reception_plan)
        assert reception_plan is not None
        future_move = next(
            move
            for move in reception_plan.moves
            if move.reception_act == "honor_concrete_effort"
        )
        self.assertTrue(future_move.required)
        evaluation = evaluate_grounded_surface_body_inverse(
            body=surface.text.encode("utf-8"),
            plan=plan,
            sentence_plan=sentence_plan,
            resolver=resolver,
        )
        self.assertTrue(evaluation.passed, evaluation.failure_codes)
        completed_tamper = _replace_body_markers(
            surface.text, section="observation", codes={"intention"}, replacement="実際の行動",
        )
        tampered_evaluation = evaluate_grounded_surface_body_inverse(
            body=completed_tamper.encode("utf-8"),
            plan=plan,
            sentence_plan=sentence_plan,
            resolver=resolver,
        )
        self.assertFalse(tampered_evaluation.passed)
        self.assertIn(
            "body_inverse_required_intention_missing:1",
            tampered_evaluation.failure_codes,
        )
        gate = evaluate_grounded_observation_gate(
            plan=plan,
            sentence_plan=sentence_plan,
            surface_result=surface,
            resolver=resolver,
            require_body_inverse=True,
        )
        self.assertTrue(gate.passed, gate.rejection_reasons)

    def test_future_action_classification_precedes_performed_action(self) -> None:
        plan, _sentence_plan, _surface, _resolver = _final_stage1_artifacts(
            "",
            memo_action="今日は少し早めに休む。",
        )
        action = next(
            nucleus
            for nucleus in plan.nuclei
            if nucleus.kind == "action"
            and nucleus.nucleus_id
            in set(plan.coverage_requirements.required_nucleus_ids)
        )
        self.assertEqual(action.semantic_frame.modality, "intention")
        self.assertEqual(action.semantic_frame.time_scope, "present")
        self.assertTrue(
            reception_owner.reception_action_is_future_intention(action)
        )
        self.assertFalse(surface_owner._final_action_is_performed(action))
        self.assertFalse(gate_owner._body_inverse_action_is_performed(action))

        base_attributes = tuple(
            code
            for code in action.semantic_frame.attribute_codes
            if not code.startswith("time_scope:")
            and code not in {"aspect:completed", "aspect:perfective"}
        )
        fact_future = replace(
            action,
            semantic_frame=replace(
                action.semantic_frame,
                modality="fact",
                time_scope="future",
                attribute_codes=(*base_attributes, "time_scope:future"),
            ),
        )
        self.assertTrue(
            reception_owner.reception_action_is_future_intention(fact_future)
        )
        self.assertFalse(
            surface_owner._final_action_is_performed(fact_future)
        )
        self.assertFalse(
            gate_owner._body_inverse_action_is_performed(fact_future)
        )

        completed = replace(
            fact_future,
            semantic_frame=replace(
                fact_future.semantic_frame,
                time_scope="completed",
                attribute_codes=(*base_attributes, "aspect:completed"),
            ),
        )
        self.assertFalse(
            reception_owner.reception_action_is_future_intention(completed)
        )
        self.assertTrue(surface_owner._final_action_is_performed(completed))
        self.assertTrue(gate_owner._body_inverse_action_is_performed(completed))

        negative_fact = replace(
            completed,
            semantic_frame=replace(
                completed.semantic_frame,
                polarity="negative",
            ),
        )
        self.assertFalse(
            reception_owner.reception_action_is_future_intention(negative_fact)
        )
        self.assertFalse(
            surface_owner._final_action_is_performed(negative_fact)
        )
        self.assertFalse(
            gate_owner._body_inverse_action_is_performed(negative_fact)
        )

        negated_fact = replace(
            completed,
            semantic_frame=replace(
                completed.semantic_frame,
                polarity="positive",
                attribute_codes=(*base_attributes, "operator:negation"),
            ),
        )
        self.assertFalse(
            reception_owner.reception_action_is_future_intention(negated_fact)
        )
        self.assertFalse(
            surface_owner._final_action_is_performed(negated_fact)
        )
        self.assertFalse(
            gate_owner._body_inverse_action_is_performed(negated_fact)
        )

        completed_intention = replace(
            completed,
            semantic_frame=replace(
                completed.semantic_frame,
                modality="intention",
            ),
        )
        self.assertFalse(
            reception_owner.reception_action_is_future_intention(
                completed_intention
            )
        )
        self.assertFalse(
            surface_owner._final_action_is_performed(completed_intention)
        )
        self.assertFalse(
            gate_owner._body_inverse_action_is_performed(completed_intention)
        )

    def test_final_performed_action_keeps_visible_effort(self) -> None:
        plan, sentence_plan, surface, resolver = _final_stage1_artifacts(
            "今日は仕事で疲れたけど、帰ってから少し散歩したら落ち着いた。"
        )
        witness = parse_grounded_surface_body_bytes(
            surface.text.encode("utf-8")
        )
        observation = next(
            row for row in witness.lines if row.section == "observation"
        )
        self.assertIn("effort", observation.semantic_marker_codes)
        self.assertIn(
            "「帰ってから少し散歩した」という行動",
            surface.lines[0].text,
        )
        self.assertNotIn("という実際の行動", surface.lines[0].text)
        self.assertIn("実際の行動", surface.text)
        self.assertIn("target_effort", next(row for row in witness.lines if row.section == "reception").reception_marker_codes)
        evaluation = evaluate_grounded_surface_body_inverse(
            body=surface.text.encode("utf-8"),
            plan=plan,
            sentence_plan=sentence_plan,
            resolver=resolver,
        )
        self.assertTrue(evaluation.passed, evaluation.failure_codes)
        future_tamper = _replace_body_markers(
            surface.text, section="observation", codes={"effort"}, replacement="これからの行動",
        )
        tampered_evaluation = evaluate_grounded_surface_body_inverse(
            body=future_tamper.encode("utf-8"),
            plan=plan,
            sentence_plan=sentence_plan,
            resolver=resolver,
        )
        self.assertFalse(tampered_evaluation.passed)
        self.assertIn(
            "body_inverse_required_effort_missing:1",
            tampered_evaluation.failure_codes,
        )
        gate = evaluate_grounded_observation_gate(
            plan=plan,
            sentence_plan=sentence_plan,
            surface_result=surface,
            resolver=resolver,
            require_body_inverse=True,
        )
        self.assertTrue(gate.passed, gate.rejection_reasons)

    def test_final_anaphoric_felt_response_uses_role_duties_without_anchor(
        self,
    ) -> None:
        rows, manifest = load_validated_batch(
            _CANONICAL_BATCH001_PATH,
            _CANONICAL_BATCH001_MANIFEST_PATH,
        )
        self.assertEqual(manifest["case_count"], 100)
        row = next(
            item
            for item in rows
            if item["case_id"] == "nls3s_b001_0051"
        )
        input_row = row["input"]
        emotions = input_row["emotions"]
        plan, sentence_plan, surface, resolver = (
            _final_stage1_artifacts_from_raw(
                {
                    "record_id": row["case_id"],
                    "memo": input_row["thought_text"],
                    "memo_action": input_row["action_text"],
                    "category": input_row["categories"],
                    "emotion_details": emotions,
                    "emotions": [item["type"] for item in emotions],
                    "is_secret": False,
                }
            )
        )
        reception_plan = plan.response_plan.human_reception_plan
        self.assertIsNotNone(reception_plan)
        assert reception_plan is not None
        move = reception_plan.moves[0]
        reception_line_plan = next(
            item
            for item in sentence_plan.lines
            if item.binding.line_role == "human_follow"
        )
        clause = reception_line_plan.reception_clause_plans[0]
        self.assertEqual(move.reception_act, "stay_with_current_burden")
        self.assertEqual(move.move_role, "felt_response")
        self.assertEqual(move.reference_mode, "anaphoric_first")
        self.assertEqual(reception_plan.quote_policy.max_anchor_count, 0)
        self.assertEqual(clause.quote_budget, 0)

        reception_text = surface.text.split("Emlisから：\n", 1)[1]
        self.assertNotIn(
            input_row["thought_text"].rstrip("。"),
            reception_text,
        )
        witness = parse_grounded_surface_body_bytes(
            surface.text.encode("utf-8")
        )
        parsed_reception = next(
            item for item in witness.lines if item.section == "reception"
        )
        self.assertIn(
            "target_words",
            parsed_reception.reception_marker_codes,
        )
        self.assertNotIn("target_burden", parsed_reception.reception_marker_codes)
        self.assertIn("receive", parsed_reception.reception_marker_codes)
        self.assertNotIn("attention", parsed_reception.reception_marker_codes)

        evaluation = evaluate_grounded_surface_body_inverse(
            body=surface.text.encode("utf-8"),
            plan=plan,
            sentence_plan=sentence_plan,
            resolver=resolver,
        )
        self.assertTrue(evaluation.passed, evaluation.failure_codes)
        gate = evaluate_grounded_observation_gate(
            plan=plan,
            sentence_plan=sentence_plan,
            surface_result=surface,
            resolver=resolver,
            require_body_inverse=True,
        )
        self.assertTrue(gate.passed, gate.rejection_reasons)

        target_tamper = surface.text.replace("今ここに置かれた言葉", "そのこと", 1)
        self.assertNotEqual(target_tamper, surface.text)
        target_evaluation = evaluate_grounded_surface_body_inverse(
            body=target_tamper.encode("utf-8"),
            plan=plan,
            sentence_plan=sentence_plan,
            resolver=resolver,
        )
        self.assertFalse(target_evaluation.passed)
        self.assertIn(
            "body_inverse_reception_target_duty_missing:rm1",
            target_evaluation.failure_codes,
        )

        receive_tamper = surface.text.replace(
            "受け止めています",
            "そこにあります",
            1,
        )
        receive_evaluation = evaluate_grounded_surface_body_inverse(
            body=receive_tamper.encode("utf-8"),
            plan=plan,
            sentence_plan=sentence_plan,
            resolver=resolver,
        )
        self.assertFalse(receive_evaluation.passed)
        self.assertIn(
            "body_inverse_reception_why_duty_missing:rm1",
            receive_evaluation.failure_codes,
        )

    def test_d21_delete_vector_is_rejected(self) -> None:
        plan, sentence_plan, surface, resolver = _artifacts("I6-C01")
        relation_line = next(
            row
            for row in surface.lines
            if row.binding.line_role != "human_follow"
            and row.binding.relation_ids
        )
        deleted = surface.text.replace(
            f"{relation_line.text}\n",
            "",
            1,
        )
        evaluation = evaluate_grounded_surface_body_inverse(
            body=deleted.encode("utf-8"),
            plan=plan,
            sentence_plan=sentence_plan,
            resolver=resolver,
        )
        self.assertFalse(evaluation.passed)
        self.assertIn(
            "body_inverse_observation_line_count_mismatch",
            evaluation.failure_codes,
        )

    def test_d21_relation_reverse_vector_is_rejected(self) -> None:
        plan, sentence_plan, surface, resolver = _final_stage1_artifacts(
            "今日は仕事で疲れたけど、帰ってから少し散歩したら落ち着いた。"
        )
        reversed_relation = surface.text.replace(
            "「帰ってから少し散歩した」という行動から"
            "「落ち着いた」という変化へのつながり",
            "「落ち着いた」という変化から"
            "「帰ってから少し散歩した」という行動へのつながり",
            1,
        )
        evaluation = evaluate_grounded_surface_body_inverse(
            body=reversed_relation.encode("utf-8"),
            plan=plan,
            sentence_plan=sentence_plan,
            resolver=resolver,
        )
        self.assertFalse(evaluation.passed)
        self.assertIn(
            "body_inverse_relation_direction_reversed:1",
            evaluation.failure_codes,
        )

    def test_d21_unknown_fill_vector_is_rejected(self) -> None:
        _plan, _sentence_plan, surface, _resolver = _artifacts("I6-L03")
        filled = surface.text.replace(
            "焼成条件はまだ不明だ",
            "焼成条件は温度だけで決まる",
        ).replace(
            "まだ分からない範囲",
            "原因まで確定した範囲",
        )
        evaluation = self._evaluate("I6-L03", filled)
        self.assertFalse(evaluation.passed)
        self.assertIn(
            "body_inverse_unbound_observation_quote:2",
            evaluation.failure_codes,
        )

    def test_d21_relation_tamper_vector_is_rejected(self) -> None:
        plan, sentence_plan, surface, resolver = _final_stage1_artifacts(
            "今日は仕事で疲れたけど、帰ってから少し散歩したら落ち着いた。"
        )
        tampered = surface.text.replace(
            "という変化へのつながり",
            "という変化が並んでいること",
            1,
        )
        evaluation = evaluate_grounded_surface_body_inverse(
            body=tampered.encode("utf-8"),
            plan=plan,
            sentence_plan=sentence_plan,
            resolver=resolver,
        )
        self.assertFalse(evaluation.passed)
        self.assertIn(
            "body_inverse_relation_type_marker_mismatch:1",
            evaluation.failure_codes,
        )

    def test_reception_target_attention_why_duties_are_protected(self) -> None:
        _plan, _sentence_plan, surface, _resolver = _artifacts("I6-C01")
        tampered = surface.text.replace("が特に印象に残り、", "があり、")
        evaluation = self._evaluate("I6-C01", tampered)
        self.assertFalse(evaluation.passed)
        self.assertTrue(
            any(
                code.startswith("body_inverse_reception_attention_duty_missing:")
                for code in evaluation.failure_codes
            )
        )

    def test_existing_production_gate_default_is_unchanged_and_opt_in_is_body_free(
        self,
    ) -> None:
        plan, sentence_plan, surface, resolver = _artifacts("I6-C01")
        existing = evaluate_grounded_observation_gate(
            plan=plan,
            sentence_plan=sentence_plan,
            surface_result=surface,
            resolver=resolver,
        )
        explicit_default = evaluate_grounded_observation_gate(
            plan=plan,
            sentence_plan=sentence_plan,
            surface_result=surface,
            resolver=resolver,
            require_body_inverse=False,
        )
        protected = evaluate_grounded_observation_gate(
            plan=plan,
            sentence_plan=sentence_plan,
            surface_result=surface,
            resolver=resolver,
            require_body_inverse=True,
        )
        self.assertEqual(existing, explicit_default)
        self.assertEqual(existing, protected)
        self.assertTrue(grounded_gate_meta_is_body_free(protected.as_body_free_meta()))
        self.assertNotIn(
            surface.text,
            json.dumps(protected.as_body_free_meta(), ensure_ascii=False),
        )

        if "につながっています" in surface.text:
            tampered_text = surface.text.replace(
                "につながっています",
                "が並んでいます",
                1,
            )
        else:
            self.assertIn("がある一方で", surface.text)
            tampered_text = surface.text.replace(
                "がある一方で",
                "と並び",
                1,
            )
        body_tamper = replace(surface, text=tampered_text)
        legacy_tamper = evaluate_grounded_observation_gate(
            plan=plan,
            sentence_plan=sentence_plan,
            surface_result=body_tamper,
            resolver=resolver,
        )
        protected_tamper = evaluate_grounded_observation_gate(
            plan=plan,
            sentence_plan=sentence_plan,
            surface_result=body_tamper,
            resolver=resolver,
            require_body_inverse=True,
        )
        self.assertFalse(
            any(
                reason.startswith("body_inverse_")
                for reason in legacy_tamper.rejection_reasons
            )
        )
        self.assertTrue(
            any(
                reason.startswith("body_inverse_")
                and "relation" in reason
                for reason in protected_tamper.rejection_reasons
            ),
            protected_tamper.rejection_reasons,
        )
        self.assertFalse(protected_tamper.passed)


if __name__ == "__main__":
    unittest.main()
