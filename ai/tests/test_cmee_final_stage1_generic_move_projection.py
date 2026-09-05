# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from pathlib import Path
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
import cocolon_meaning_experience_engine.contracts as contracts_owner
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
    inputs = _compile_inputs(row)
    resolver = build_evidence_span_resolver(inputs.source.evidence_spans, current_input=inputs.source.normalized_current_input)
    captured = []
    selected_inputs = []
    authored = []
    author_arguments = []
    build_input = response_owner._build_selected_subjective_reception_input
    author = response_owner.realize_source_grounded_human_reception
    adapt = response_owner._adapt_grounded_surface_to_v2_realized_units

    def track_adapter(*args, **kwargs):
        captured.append(kwargs)
        return adapt(*args, **kwargs)

    def track_input(*args, **kwargs):
        value = build_input(*args, **kwargs)
        selected_inputs.append(value)
        return value

    def track_author(*args, **kwargs):
        value = author(*args, **kwargs)
        authored.append(value)
        author_arguments.append((args, kwargs))
        return value

    with (
        patch.object(response_owner, "_build_selected_subjective_reception_input", side_effect=track_input),
        patch.object(response_owner, "realize_source_grounded_human_reception", side_effect=track_author),
        patch.object(response_owner, "_adapt_grounded_surface_to_v2_realized_units", side_effect=track_adapter),
    ):
        response_owner.compile_stage1_response(
            source=inputs.source, grounded_graph=inputs.graph,
            parent_plan=inputs.parent_plan, grounded_plan=inputs.grounded_plan,
        )
    if len(captured) != 1:
        raise AssertionError("selected_surface_adapter_exact1_required")
    if len(selected_inputs) != 1:
        raise AssertionError("selected_subjective_input_exact1_required")
    selected_subjective_input = selected_inputs[0]
    selected_plan = captured[0]["grounded_plan"]
    sentence_plan = captured[0]["sentence_plan"]
    surface = captured[0]["surface_result"]
    inverse = evaluate_grounded_surface_body_inverse(
        body=surface.text.encode("utf-8"),
        plan=selected_plan,
        sentence_plan=sentence_plan,
        resolver=resolver,
        selected_subjective_input=selected_subjective_input,
    )
    gate = evaluate_grounded_observation_gate(
        plan=selected_plan,
        sentence_plan=sentence_plan,
        surface_result=surface,
        resolver=resolver,
        product_readfeel_status="not_evaluated",
        require_body_inverse=True,
        selected_subjective_input=selected_subjective_input,
    )
    return SimpleNamespace(
        plan=selected_plan,
        sentence_plan=sentence_plan,
        surface=surface,
        resolver=resolver,
        inverse=inverse,
        gate=gate,
        selected_subjective_input=selected_subjective_input,
        authored=tuple(authored),
        author_arguments=tuple(author_arguments),
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


def _recovery_surface(artifacts, sentence_plan):
    authored = next(row for row in artifacts.authored
                    if row.recovery_stage == sentence_plan.recovery_stage)
    result, _placements = surface_owner.realize_grounded_sentence_plan_with_human_reception(
        sentence_plan, artifacts.plan, artifacts.resolver,
        human_reception_surface=authored,
        selected_subjective_input=artifacts.selected_subjective_input,
    )
    return result


def _tamper_reception(body: str, source: str, replacement: str) -> str:
    observation, separator, reception = body.partition(
        surface_owner.RECEPTION_SECTION_LABEL
    )
    if not separator or source not in reception:
        raise AssertionError(f"reception_tamper_source_missing:{source}")
    return observation + separator + reception.replace(source, replacement, 1)


class CMEEAnaphoricTopicOwnerTest(unittest.TestCase):
    def test_anaphoric_context_stays_visible_without_repeating_its_relation(self):
        rows, _ = load_validated_batch(_BATCH_PATH, _MANIFEST_PATH)
        exercised = 0
        for row in rows:
            if row["case_id"] not in _TYPED_RELATION_CLOSURE_CASE_IDS:
                continue
            artifacts = _full_surface_artifacts(row)
            follow = _reception_text(artifacts.surface.text)
            if "が重なる中での" not in follow:
                continue
            exercised += 1
            self.assertTrue(artifacts.inverse.passed)
            self.assertTrue(artifacts.gate.passed)
            self.assertNotIn("が重なる中で、", follow)
            changed = _tamper_reception(
                artifacts.surface.text, "が重なる中での", "と",
            )
            inverse = evaluate_grounded_surface_body_inverse(
                body=changed.encode("utf-8"), plan=artifacts.plan,
                sentence_plan=artifacts.sentence_plan, resolver=artifacts.resolver,
                selected_subjective_input=artifacts.selected_subjective_input,
            )
            self.assertFalse(inverse.passed)
            self.assertTrue(any("context_anchor_missing" in code
                                for code in inverse.failure_codes))
        self.assertGreaterEqual(exercised, 2)

    def test_selected_noncollapse_governs_both_visible_objects_once(self):
        rows, _ = load_validated_batch(_BATCH_PATH, _MANIFEST_PATH)
        selected_ids = set(_TYPED_RELATION_CLOSURE_CASE_IDS + _REPRESENTATIVE_CASE_IDS)
        exercised = 0
        for row in rows:
            if row["case_id"] not in selected_ids:
                continue
            artifacts = _full_surface_artifacts(row)
            follow = _reception_text(artifacts.surface.text)
            if "の両方" not in follow:
                continue
            exercised += 1
            self.assertTrue(artifacts.inverse.passed)
            self.assertTrue(artifacts.gate.passed)
            self.assertTrue(any(
                decision.subjective_proposition.appraisal_content is not None
                and decision.subjective_proposition.appraisal_content.operation
                == "PRESERVE_BOTH_ENDPOINTS"
                for decision in artifacts.selected_subjective_input.decisions
            ))
            self.assertNotIn("どちらの側も残したまま", follow)
            self.assertNotIn("がともにあること", follow)
            for replacement in ("の片方", "", "のどちらか"):
                changed = _tamper_reception(
                    artifacts.surface.text, "の両方", replacement,
                )
                inverse = evaluate_grounded_surface_body_inverse(
                    body=changed.encode("utf-8"), plan=artifacts.plan,
                    sentence_plan=artifacts.sentence_plan, resolver=artifacts.resolver,
                    selected_subjective_input=artifacts.selected_subjective_input,
                )
                self.assertFalse(inverse.passed)
        self.assertGreaterEqual(exercised, 2)

    def test_distributive_object_cannot_invent_a_relation_slot(self):
        for invalid_slot in (True, -1, 0, "0"):
            with self.assertRaisesRegex(
                reception_owner.GroundedHumanReceptionSurfaceError,
                "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP",
            ):
                reception_owner._source_grounded_argument_surface(
                    SimpleNamespace(relations=()),
                    distributive_relation_slot=invalid_slot,
                )

    def test_negative_feeling_nominal_uses_existing_finite_classes(self):
        for source, nominal in (
            ("どことなく、落ち着かない", "どことなくの落ち着かなさ"),
            ("なんとなく感じない", "なんとなくの感じなさ"),
            ("漠然と、焦らない", "漠然とした焦らなさ"),
            ("苦しまない", "苦しまなさ"),
            ("苦しくない", "苦しくなさ"),
        ):
            with self.subTest(source=source):
                row = reception_owner._source_grounded_negative_feeling_nominal(source)
                self.assertIsNotNone(row)
                self.assertEqual(row[1], nominal)
        for source in (
            "落ち着かないかもしれない", "落ち着かなかった", "落ち着かないと話した",
            "落ち着かないでほしい", "人が落ち着かない", "感じかない", "焦ない",
            "どことなく、落ち着かないけれど嬉しい",
        ):
            with self.subTest(source=source):
                self.assertIsNone(reception_owner._source_grounded_negative_feeling_nominal(source))

    def test_negative_feeling_body_keeps_manner_and_negation(self):
        artifacts = _full_surface_artifacts({
            "case_id": "negative-feeling-expression-unit",
            "input": {
                "thought_text": "どことなく、落ち着かない。",
                "action_text": "", "categories": ["生活"],
                "emotions": [{"type": "不安", "strength": "weak"}],
            },
        })
        follow = _reception_text(artifacts.surface.text)
        self.assertTrue(artifacts.inverse.passed)
        self.assertIn("どことなくの落ち着かなさ", follow)
        self.assertNotIn("どことなく、落ち着かないという", follow)
        changed = _tamper_reception(
            artifacts.surface.text, "落ち着かなさ", "落ち着き",
        )
        inverse = evaluate_grounded_surface_body_inverse(
            body=changed.encode("utf-8"), plan=artifacts.plan,
            sentence_plan=artifacts.sentence_plan, resolver=artifacts.resolver,
            selected_subjective_input=artifacts.selected_subjective_input,
        )
        self.assertFalse(inverse.passed)

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


class CMEESameNucleusActionStatusTest(unittest.TestCase):
    def test_desired_continuation_keeps_wish_without_ongoing_assertion(self):
        for text, resolved in (
            ("作業を続けたい", True),
            ("練習を続けたいです", True),
            ("同じ確認を繰り返したい", True),
            ("ずっと作業を続けたい", False),
            ("作業を続けたいと思っている", False),
            ("作業を続けていた", False),
            ("作業を続けたかった", False),
            ("「作業を続けたい」と聞いた", False),
            ("作業を続けていて、休みたい", False),
        ):
            with self.subTest(text=text):
                source, action = self._action(text)
                before = replace(action, kind="wish", semantic_frame=replace(
                    action.semantic_frame, predicate_kind="wish", modality="wish",
                    time_scope="continuing", attribute_codes=(
                        "operator:wish", "operator:continuation", "time_scope:continuing",
                    ),
                ))
                after, = observation_plan_owner._final_stage1_align_action_status(
                    (before,), source.evidence_spans,
                )
                self.assertEqual(after.semantic_frame.time_scope,
                                 "current_input" if resolved else "continuing")
                self.assertEqual(after.semantic_frame.modality, "wish")
                self.assertEqual(replace(after, semantic_frame=before.semantic_frame), before)

    def test_visible_wish_and_postposed_focus_do_not_add_time(self):
        rows, _ = load_validated_batch(_BATCH_PATH, _MANIFEST_PATH)
        checked = {"desire": 0, "postposed": 0}
        for row in rows:
            memo = row["input"]["thought_text"].rstrip("。 ")
            action = row["input"]["action_text"].rstrip("。 ")
            kind = (
                "desire" if memo.endswith("続けたい")
                else "postposed" if action.endswith(("、それだけ", "、これだけ", "、あれだけ"))
                else ""
            )
            if not kind:
                continue
            artifacts = _full_surface_artifacts(row)
            follow = _reception_text(artifacts.surface.text)
            forbidden = "今も、" if kind == "desire" else "これまで、"
            self.assertTrue(artifacts.inverse.passed)
            self.assertTrue(artifacts.gate.passed)
            self.assertNotIn(forbidden, follow)
            # Inspect an actual explicit body, including the limiting focus;
            # an anaphoric short input cannot exercise this morphology bug.
            marker = "続けたい" if kind == "desire" else "それだけ" if "それだけ" in action else "これだけ" if "これだけ" in action else "あれだけ"
            if marker not in follow:
                continue
            checked[kind] += 1
            changed = _tamper_reception(artifacts.surface.text, follow.strip(), forbidden + follow.strip())
            inverse = evaluate_grounded_surface_body_inverse(
                body=changed.encode("utf-8"), plan=artifacts.plan,
                sentence_plan=artifacts.sentence_plan, resolver=artifacts.resolver,
                selected_subjective_input=artifacts.selected_subjective_input,
            )
            self.assertFalse(inverse.passed)
        self.assertGreater(checked["desire"], 0)
        self.assertGreater(checked["postposed"], 0)

    def test_unfinished_source_ellipsis_survives_body_and_inverse(self):
        rows, _ = load_validated_batch(_BATCH_PATH, _MANIFEST_PATH)
        checked = 0
        for row in rows:
            memo = row["input"]["thought_text"]
            if not memo.endswith("…"):
                continue
            artifacts = _full_surface_artifacts(row)
            follow = _reception_text(artifacts.surface.text)
            self.assertTrue(artifacts.inverse.passed)
            # Only a source phrase actually exposed by the selected Move
            # supplies the antecedent for this character-preservation test.
            if memo[:-1] not in follow:
                continue
            checked += 1
            self.assertIn(memo, follow)
            changed = _tamper_reception(artifacts.surface.text, memo, memo[:-1])
            inverse = evaluate_grounded_surface_body_inverse(
                body=changed.encode("utf-8"), plan=artifacts.plan,
                sentence_plan=artifacts.sentence_plan, resolver=artifacts.resolver,
                selected_subjective_input=artifacts.selected_subjective_input,
            )
            self.assertFalse(inverse.passed)
        self.assertGreater(checked, 0)

    def test_open_desire_scope_does_not_change_affirmed_desire(self):
        for source, expected in (
            ("何を選びたいのかも決められず、迷っている気がする", True),
            ("進みたいのか、ここに残りたいのかも定まっていない", True),
            ("たぶん続けたい、でもそれでいいのか…", True),
            ("続けたいが、できるかは分からない", False),
            ("何を選びたいのか迷ったが、いまは続けたい", False),
            ("たぶん雨が降るが、続けたいと思っている", False),
            ("「何をしたいのかも分からない」と言われた", False),
        ):
            with self.subTest(source=source):
                self.assertEqual(observation_plan_owner._final_stage1_wish_is_open(source), expected)

    def test_uncertain_desire_keeps_owner_and_completed_body_boundary(self):
        artifacts = _full_surface_artifacts({
            "case_id": "uncertain-desire-expression-unit",
            "input": {
                "thought_text": "何を選びたいのか、ただ話を聞いてほしいのかも定まっていない。",
                "action_text": "候補を紙に記録した。", "categories": ["生活"],
                "emotions": [{"type": "不安", "strength": "weak"}],
            },
        })
        target = next(n for n in artifacts.plan.nuclei if "operator:wish" in n.semantic_frame.attribute_codes)
        self.assertEqual(target.semantic_frame.modality, "uncertain")
        self.assertEqual(target.semantic_frame.time_scope, "current_input")
        self.assertFalse(reception_owner.reception_action_is_performed(target, final_source_fidelity=True))
        self.assertTrue(artifacts.inverse.passed)
        self.assertIn("まだ確かではない願い", _reception_text(artifacts.surface.text))
        changed = _tamper_reception(artifacts.surface.text, "まだ確かではない願い", "確かに定まった願い")
        inverse = evaluate_grounded_surface_body_inverse(
            body=changed.encode("utf-8"), plan=artifacts.plan,
            sentence_plan=artifacts.sentence_plan, resolver=artifacts.resolver,
            selected_subjective_input=artifacts.selected_subjective_input,
        )
        self.assertFalse(inverse.passed)

    def _action(self, text):
        source = freeze_text_source(_request_from_row({
            "case_id": "status-scope-unit",
            "input": {"thought_text": "", "action_text": text,
                      "categories": ["生活"], "emotions": [{"type": "不安", "strength": "weak"}]},
        }))
        plan = build_grounded_observation_plan(
            source.normalized_current_input, evidence_spans=source.evidence_spans,
        )
        action = next(n for n in plan.nuclei if "memo_action" in n.source_fields)
        # Exercise the conservative default that this final-only seam owns.
        action = replace(action, kind="action", semantic_frame=replace(
            action.semantic_frame, modality="intention", polarity="positive",
            time_scope="current_input", attribute_codes=("operator:action",),
        ))
        return source, action

    def test_future_decision_keeps_embedded_negation_without_performance(self):
        source, action = self._action(
            "先に結論を出さず、材料を比べてから選ぶことにした。"
        )
        action = replace(action, semantic_frame=replace(
            action.semantic_frame, polarity="negative",
            attribute_codes=("operator:action", "operator:negation"),
        ))
        aligned, = observation_plan_owner._final_stage1_align_action_status(
            (action,), source.evidence_spans,
        )
        self.assertEqual(aligned.semantic_frame.polarity, "negative")
        self.assertEqual(aligned.semantic_frame.modality, "intention")
        self.assertEqual(aligned.semantic_frame.time_scope, "future")
        self.assertIn("operator:negation", aligned.semantic_frame.attribute_codes)
        self.assertTrue(observation_plan_owner._is_explicit_action_nucleus(
            aligned, final_source_fidelity=True,
        ))
        self.assertFalse(observation_plan_owner.source_proven_performed_action_status(aligned))
        self.assertFalse(reception_owner.reception_action_is_performed(
            aligned, final_source_fidelity=True,
        ))

    def test_future_decision_has_one_visible_time_expression(self):
        artifacts = _full_surface_artifacts({
            "case_id": "future-decision-expression-unit",
            "input": {
                "thought_text": "返事を待っていて、少し気になっている。",
                "action_text": "連絡を急がず、候補を比べてから決めることにした。",
                "categories": ["生活"],
                "emotions": [{"type": "不安", "strength": "weak"}],
            },
        })
        follow = _reception_text(artifacts.surface.text)
        self.assertTrue(artifacts.inverse.passed)
        self.assertEqual(follow.count("これから"), 1)
        self.assertNotIn("実際の行動", follow)

    def test_finite_action_tense_and_aspect_are_separate(self):
        for text, time, aspect in (
            ("資料を郵送した", "past", "unknown"),
            ("資料を読んでいる", "continuing", "progressive"),
            ("資料を読んでいた", "past", "progressive"),
            ("今後の予定を調べた", "past", "unknown"),
            ("整理した、それだけ", "past", "unknown"),
            ("完成させた、これだけ", "past", "unknown"),
            ("話したい内容は二行だけ記録した", "past", "unknown"),
            ("回答を待ってもらうよう頼んだ", "past", "unknown"),
        ):
            with self.subTest(time=time, aspect=aspect):
                source, before = self._action(text)
                after, = observation_plan_owner._final_stage1_align_action_status(
                    (before,), source.evidence_spans,
                )
                self.assertEqual(after.semantic_frame.modality, "fact")
                self.assertEqual(after.semantic_frame.time_scope, time)
                self.assertIn("aspect:" + aspect, after.semantic_frame.attribute_codes)
                self.assertFalse(reception_owner.reception_action_is_future_intention(after))
                self.assertTrue(reception_owner.reception_action_is_performed(after))
                self.assertEqual(replace(after, semantic_frame=before.semantic_frame), before)
                self.assertEqual(after.semantic_frame.actor, before.semantic_frame.actor)
                self.assertEqual(after.semantic_frame.target_anchor_ids, before.semantic_frame.target_anchor_ids)

    def test_nonfactual_predicate_does_not_become_performed(self):
        for text in (
            "資料を読んでいない", "資料を読みたかった",
            "資料を読んだか分からない", "「資料を読んだ」と聞いた",
            "資料を読んだら連絡する", "古びた",
            "資料を読むようにした", "資料を読んだことにした",
            "この部屋は作業に便利だった", "部屋にいた",
            "資料を読もうとした", "資料を読もうとしていた",
            "資料を読む予定だった", "資料を読むつもりだった",
            "何を選んだのだろう", "そうだろうと思う",
        ):
            with self.subTest():
                source, before = self._action(text)
                after, = observation_plan_owner._final_stage1_align_action_status(
                    (before,), source.evidence_spans,
                )
                self.assertEqual(after, before)

    def test_source_future_keeps_embedded_negation_and_tentative_modality(self):
        for text, tentative in (
            ("資料を読む予定", False),
            ("明日は都合のつかない人にも案内を送る", False),
            ("来週は変更しない範囲を決めるつもり", False),
            ("次の段階を決めようかな", True),
            ("今日は少し早めに休む", False),
            ("資料を読むことにした", False),
        ):
            with self.subTest(tentative=tentative):
                source, nucleus = self._action(text)
                before = replace(nucleus, semantic_frame=replace(
                    nucleus.semantic_frame, polarity="negative",
                    attribute_codes=(*nucleus.semantic_frame.attribute_codes, "operator:negation"),
                ))
                after, = observation_plan_owner._final_stage1_align_action_status((before,), source.evidence_spans)
                self.assertEqual(after.semantic_frame.time_scope, "future")
                self.assertEqual(after.semantic_frame.modality, "uncertain" if tentative else "intention")
                self.assertEqual(after.semantic_frame.polarity, "negative")
                self.assertTrue(observation_plan_owner.source_proven_future_action_status(after))
                self.assertTrue(reception_owner.reception_action_is_future_intention(after, final_source_fidelity=True))
                self.assertFalse(reception_owner.reception_action_is_performed(after, final_source_fidelity=True))
                self.assertEqual(replace(after, semantic_frame=before.semantic_frame), before)

    def test_ellipsis_is_not_a_future_plan_and_separate_subject_is_not_effort(self):
        for text in ("手紙に「受け取った」まで", "連絡はまだ", "宛先だけ"):
            with self.subTest():
                source, before = self._action(text)
                after, = observation_plan_owner._final_stage1_align_action_status((before,), source.evidence_spans)
                self.assertEqual(after.semantic_frame.modality, "uncertain")
                self.assertEqual(after.semantic_frame.time_scope, before.semantic_frame.time_scope)
                self.assertFalse(reception_owner.reception_action_is_future_intention(after, final_source_fidelity=True))
                self.assertFalse(reception_owner.reception_action_is_performed(after, final_source_fidelity=True))
                self.assertEqual(replace(after, semantic_frame=before.semantic_frame), before)
        source, before = self._action("窓を開けたまま雨が入ってきた")
        after, = observation_plan_owner._final_stage1_align_action_status((before,), source.evidence_spans)
        self.assertEqual(after.semantic_frame.modality, "fact")
        self.assertEqual(after.semantic_frame.time_scope, "past")
        self.assertFalse(reception_owner.reception_action_is_performed(after, final_source_fidelity=True))
        self.assertEqual(replace(after, semantic_frame=before.semantic_frame), before)

    def test_embedded_operator_keeps_scope_with_factual_outer_action(self):
        for text, polarity, modality, code, aspect in (
            ("参加できないことだけを記録した", "negative", "possibility", "operator:negation", "unknown"),
            ("続けたいと伝えた", "neutral", "wish", "operator:wish", "unknown"),
            ("不安な箇所を記録していた", "neutral", "feeling", "operator:feeling", "progressive"),
        ):
            with self.subTest(operator=code):
                source, nucleus = self._action(text)
                before = replace(nucleus, semantic_frame=replace(
                    nucleus.semantic_frame, polarity=polarity, modality=modality,
                    attribute_codes=(*nucleus.semantic_frame.attribute_codes, code),
                ))
                after, = observation_plan_owner._final_stage1_align_action_status((before,), source.evidence_spans)
                self.assertEqual(after.semantic_frame.modality, "fact")
                self.assertEqual(after.semantic_frame.time_scope, "past")
                self.assertEqual(after.semantic_frame.polarity, polarity)
                self.assertIn(code, after.semantic_frame.attribute_codes)
                self.assertIn("aspect:" + aspect, after.semantic_frame.attribute_codes)
                self.assertEqual(replace(after, semantic_frame=before.semantic_frame), before)
                self.assertTrue(observation_plan_owner._is_explicit_action_nucleus(after))
                self.assertTrue(reception_owner.reception_action_is_performed(after))
                self.assertFalse(reception_owner.reception_action_is_future_intention(after))

    def test_negative_fact_without_outer_action_proof_is_not_effort(self):
        source, nucleus = self._action("何も記録しなかった")
        negative = replace(nucleus, semantic_frame=replace(
            nucleus.semantic_frame, modality="fact", polarity="negative",
            attribute_codes=("operator:negation", "operator:action", "semantic_role:concrete_action_evidence"),
        ))
        after, = observation_plan_owner._final_stage1_align_action_status((negative,), source.evidence_spans)
        self.assertEqual(after, negative)
        self.assertTrue(observation_plan_owner._is_explicit_action_nucleus(after))
        self.assertTrue(observation_plan_owner._is_reception_performed_action_nucleus(after))
        self.assertFalse(observation_plan_owner._is_explicit_action_nucleus(after, final_source_fidelity=True))
        self.assertFalse(observation_plan_owner._is_reception_performed_action_nucleus(after, final_source_fidelity=True))
        self.assertFalse(reception_owner.reception_action_is_performed(after))

    def test_past_action_pair_keeps_source_aspect_and_rejects_wrong_owner(self):
        rows, _ = load_validated_batch(_BATCH_PATH, _MANIFEST_PATH)
        inputs = _compile_inputs(next(row for row in rows if row["case_id"] == "nls3s_b001_0090"))
        projection, units = response_owner.compile_stage1_response(
            source=inputs.source, grounded_graph=inputs.graph,
            parent_plan=inputs.parent_plan, grounded_plan=inputs.grounded_plan,
        )
        actions = [n for n in inputs.grounded_plan.nuclei if n.kind == "action"]
        self.assertEqual(len(actions), 2)
        self.assertTrue(all(n.semantic_frame.time_scope == "past" and n.semantic_frame.modality == "fact" for n in actions))
        self.assertIn("aspect:progressive", actions[0].semantic_frame.attribute_codes)
        self.assertIn("aspect:unknown", actions[1].semantic_frame.attribute_codes)
        self.assertTrue(all(len(row.canonical_qualifier_codes) == 3 for row in projection.source_qualifier_binding_rows))
        aspect_row, = [row for row in projection.meaning_visible_causal_trace_rows
                       if row.source_qualifier_refs and all(ref.startswith("aspect:") for ref in row.source_qualifier_refs)]
        self.assertEqual(set(aspect_row.source_qualifier_refs), {"aspect:progressive", "aspect:unknown"})

        def changed_projection(changed):
            traces = tuple(changed if row is aspect_row else row for row in projection.meaning_visible_causal_trace_rows)
            return replace(projection, meaning_visible_causal_trace_rows=traces,
                           tagged_projection_ref=contracts_owner.project_stage1_tagged_projection_ref(
                               projection_branch=projection.projection_branch,
                               projection_seal_ref=projection.projection_seal_ref,
                               meaning_visible_causal_trace_rows=traces,
                               reception_visible_causal_trace_rows=projection.reception_visible_causal_trace_rows))

        contracts_owner._validate_stage1_projection_causal_trace(projection)
        for refs in (("aspect:perfective",), ("aspect:unknown",), ("aspect:progressive",)):
            with self.subTest(refs=refs), self.assertRaisesRegex(contracts_owner.CMEEStage1ContractError, "MEANING_REALIZATION_CAUSAL_TRACE_GAP"):
                contracts_owner._validate_stage1_projection_causal_trace(changed_projection(replace(aspect_row, source_qualifier_refs=refs)))
        before_ref = next(binding.semantic_ref for candidate in projection.interpretation_candidates
                          if candidate.candidate_kind is InterpretationKind.ACTION_BEFORE_AFTER
                          for binding in candidate.argument_bindings if binding.role is contracts_owner.ArgumentRole.BEFORE)
        before_only = replace(aspect_row, configuration_component_refs=(before_ref,), source_qualifier_refs=("aspect:progressive",))
        contracts_owner._validate_stage1_projection_causal_trace(changed_projection(before_only))
        with self.assertRaisesRegex(contracts_owner.CMEEStage1ContractError, "MEANING_REALIZATION_CAUSAL_TRACE_GAP"):
            contracts_owner._validate_stage1_projection_causal_trace(changed_projection(replace(before_only, source_qualifier_refs=("aspect:unknown",))))
        self.assertEqual(len(units), 2)

    def test_incomplete_fragment_provenance_is_rejected(self):
        source, before = self._action("資料を郵送した")
        for codes in (
            ("source_fragment_scalar_range:0:3",),
            ("source_fragment_scalar_source:normalized_raw_text",),
            ("semantic_role:generic_relation_fragment",),
            ("surface_scalar_range:0:3",),
        ):
            malformed = replace(before, semantic_frame=replace(
                before.semantic_frame, attribute_codes=codes,
            ))
            with self.assertRaises(observation_plan_owner.GroundedObservationPlanError):
                observation_plan_owner._final_stage1_align_action_status(
                    (malformed,), source.evidence_spans,
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
            selected_subjective_input=artifacts.selected_subjective_input,
        )

    def _bind_reception_text(self, case_id: str, text: str, *, sentence_plan=None):
        artifacts = self.artifacts[case_id]
        selected = sentence_plan or artifacts.sentence_plan
        base = (artifacts.surface if selected == artifacts.sentence_plan else
                _recovery_surface(artifacts, selected))
        observation, label, _follow = base.text.partition(surface_owner.RECEPTION_SECTION_LABEL)
        gate = self._gate_for_tampered_body(
            case_id, observation + label + "\n" + text.strip(),
            sentence_plan=selected, base_surface=base,
        )
        if not gate.passed:
            raise reception_owner.GroundedHumanReceptionSurfaceError(
                "reception_actual_surface_contract_failed"
            )
        line = next(row for row in selected.lines if row.binding.line_role == "human_follow")
        return reception_owner.replay_source_grounded_human_reception_from_plan(
            artifacts.plan.response_plan.human_reception_plan,
            {n.nucleus_id: n for n in artifacts.plan.nuclei}, artifacts.resolver,
            plan=artifacts.plan, recovery_stage=selected.recovery_stage,
            clause_plans=line.reception_clause_plans,
            selected_subjective_input=artifacts.selected_subjective_input,
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
            selected_subjective_input=artifacts.selected_subjective_input,
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
            selected_subjective_input=artifacts.selected_subjective_input,
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
            selected_subjective_input=artifacts.selected_subjective_input,
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

    def test_final_generic_actual_text_is_the_rr4_validation_input(self) -> None:
        inputs = _compile_inputs(self.rows_by_id["nls3s_b001_0024"])
        author = response_owner.realize_source_grounded_human_reception
        place = response_owner.realize_grounded_sentence_plan_with_human_reception
        authored = []
        placed = []

        def track_author(*args, **kwargs):
            result = author(*args, **kwargs)
            authored.append(result)
            return result

        def track_place(*args, **kwargs):
            self.assertIn(kwargs["human_reception_surface"], authored)
            result = place(*args, **kwargs)
            follow = next(row for row in result[0].lines if row.binding.line_role == "human_follow")
            self.assertEqual(follow.text, kwargs["human_reception_surface"].text)
            placed.append(result[0])
            return result

        with (
            patch.object(response_owner, "realize_source_grounded_human_reception", side_effect=track_author),
            patch.object(response_owner, "realize_grounded_sentence_plan_with_human_reception", side_effect=track_place),
            patch.object(response_owner, "realize_grounded_sentence_plan", side_effect=AssertionError("legacy final author reached")),
        ):
            _projection, units = response_owner.compile_stage1_response(
                source=inputs.source, grounded_graph=inputs.graph,
                parent_plan=inputs.parent_plan, grounded_plan=inputs.grounded_plan,
            )
        self.assertTrue(authored)
        self.assertEqual(len(authored), len(placed))
        self.assertTrue(any(tuple(line.text for line in surface.lines) == tuple(unit.text for unit in units) for surface in placed))

    def test_unbound_quote_is_rejected_by_actual_rr4_contract(self) -> None:
        case_id = "nls3s_b001_0024"
        reception = _reception_text(
            self.artifacts[case_id].surface.text
        ) + "「無関係」"
        with self.assertRaisesRegex(
            reception_owner.GroundedHumanReceptionSurfaceError,
            "reception_actual_surface_contract_failed",
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
            "reception_actual_surface_contract_failed",
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

    def test_explicit_long_target_keeps_source_bound_fragment(
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
        self.assertEqual(move.reference_mode, "short_anchor_if_ambiguous")
        self.assertIn(target, reception)
        self.assertNotIn(f"「{target}」", reception)
        self.assertIn("願い", reception)
        replayed = reception.replace(
            target,
            "その内容",
            1,
        )
        self.assertNotEqual(replayed, reception)
        with self.assertRaisesRegex(
            reception_owner.GroundedHumanReceptionSurfaceError,
            "reception_actual_surface_contract_failed",
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
        actual_realize = response_owner.realize_grounded_sentence_plan_with_human_reception
        actual_inverse = response_owner.evaluate_grounded_surface_body_inverse
        actual_gate = response_owner.evaluate_grounded_observation_gate

        def track_realize(*args, **kwargs):
            result = actual_realize(*args, **kwargs)
            realized_surfaces.append(result[0])
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
        self.assertIn(change_fragment, reception_text)

        reception_plan = artifacts.plan.response_plan.human_reception_plan
        move = reception_plan.moves[0]
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
            allow_short_anchor=False,
            final_source_fidelity=True,
            recovery_stage=artifacts.sentence_plan.recovery_stage,
            allow_anaphoric_topic=True,
        )
        self.assertFalse(referent.source_anchor_used)
        self.assertIn(action_fragment, reception_text)
        self.assertIn(referent.text, reception_text)

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
            allow_short_anchor=False,
            final_source_fidelity=True,
            recovery_stage=artifacts.sentence_plan.recovery_stage,
            allow_anaphoric_topic=True,
        )
        self.assertFalse(referent.source_anchor_used)
        self.assertNotEqual(action_fragment, raw_text)
        whole_span_body = _tamper_reception(
            artifacts.surface.text, action_fragment, raw_text,
        )
        with self.assertRaises(
            reception_owner.GroundedHumanReceptionSurfaceError
        ) as raised:
            self._bind_reception_text(
                case_id,
                _reception_text(whole_span_body),
            )
        self.assertIn("reception_actual_surface_contract_failed", str(raised.exception))
        whole_span_inverse = self._inverse_for_tamper(
            case_id,
            whole_span_body,
        )
        self.assertIn("body_inverse_reception_replay_mismatch:1", whole_span_inverse.failure_codes)
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
        self.assertIsNotNone(context_fragment)
        missing_context_body = _tamper_reception(
            artifacts.surface.text,
            context_fragment,
            "その変化",
        )
        with self.assertRaisesRegex(
            reception_owner.GroundedHumanReceptionSurfaceError,
            "reception_actual_surface_contract_failed",
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
            selected_subjective_input=artifacts.selected_subjective_input,
        )
        self.assertFalse(wrong_source_inverse.passed)
        self.assertIn(
            "body_inverse_reception_replay_unavailable:1",
            wrong_source_inverse.failure_codes,
        )
        wrong_source_gate = evaluate_grounded_observation_gate(
            plan=wrong_source_plan,
            sentence_plan=artifacts.sentence_plan,
            surface_result=artifacts.surface,
            resolver=artifacts.resolver,
            product_readfeel_status="not_evaluated",
            require_body_inverse=True,
            selected_subjective_input=artifacts.selected_subjective_input,
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
            if not code.startswith(("time_scope:", "aspect:"))
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
                modality="intention",
                attribute_codes=(
                    *(code for code in base_attributes if code != "operator:performed_action"),
                    "time_scope:future",
                ),
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
            selected_subjective_input=artifacts.selected_subjective_input,
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
            selected_subjective_input=artifacts.selected_subjective_input,
        )
        self.assertIn(
            "body_inverse_required_intention_missing:1",
            future_inverse.failure_codes,
        )

    def test_target_marker_deletion_is_rejected(self) -> None:
        case_id = "nls3s_b001_0024"
        body = _tamper_reception(
            self.artifacts[case_id].surface.text,
            "実際の行動",
            "その内容",
        )
        inverse = self._inverse_for_tamper(case_id, body)
        self.assertIn(
            "body_inverse_reception_target_duty_missing:rm1",
            inverse.failure_codes,
        )

    def test_required_target_referent_deletion_is_rejected(self) -> None:
        case_id = "nls3s_b001_0029"
        artifacts = self.artifacts[case_id]
        body = _tamper_reception(
            artifacts.surface.text,
            "願い",
            "内容",
        )
        inverse = self._inverse_for_tamper(case_id, body)
        self.assertIn(
            "body_inverse_reception_target_duty_missing:rm1",
            inverse.failure_codes,
        )
        with self.assertRaisesRegex(
            reception_owner.GroundedHumanReceptionSurfaceError,
            "reception_actual_surface_contract_failed",
        ):
            self._bind_reception_text(
                case_id,
                _reception_text(body),
            )

    def test_explicit_target_cannot_be_replaced_by_a_generic_marker(
        self,
    ) -> None:
        case_id = "nls3s_b001_0024"
        body = _tamper_reception(
            self.artifacts[case_id].surface.text,
            "断った",
            "何かがあった",
        )
        inverse = self._inverse_for_tamper(case_id, body)
        self.assertIn(
            "body_inverse_reception_replay_mismatch:1",
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
            "reception_actual_surface_contract_failed",
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
        context = reception_owner.final_reception_nucleus_text(
            context_id,
            nucleus_index,
            artifacts.resolver,
        )
        body = _tamper_reception(
            artifacts.surface.text,
            context,
            "その状況",
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
            "reception_actual_surface_contract_failed",
        ):
            self._bind_reception_text(
                case_id,
                _reception_text(body),
            )

    def test_importance_predicate_deletion_is_rejected(self) -> None:
        case_id = "nls3s_b001_0054"
        body = _tamper_reception(
            self.artifacts[case_id].surface.text,
            "感じています",
            "ここに置いておきます",
        )
        inverse = self._inverse_for_tamper(case_id, body)
        self.assertIn(
            "body_inverse_reception_why_duty_missing:rm1",
            inverse.failure_codes,
        )
        with self.assertRaisesRegex(
            reception_owner.GroundedHumanReceptionSurfaceError,
            "reception_actual_surface_contract_failed",
        ):
            self._bind_reception_text(
                case_id,
                _reception_text(body),
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
            "今ここに置かれた言葉",
            f"今ここに置かれた言葉（{target}）",
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
        recovered_surface = _recovery_surface(artifacts, recovered_plan)
        reception = _reception_text(recovered_surface.text)
        rendered_context, context_separator, _target_clause = (
            reception.strip().partition("が重なる中で、")
        )
        self.assertTrue(context_separator)

        missing_body = _tamper_reception(
            recovered_surface.text,
            f"{rendered_context}{context_separator}",
            "",
        )
        missing_inverse = evaluate_grounded_surface_body_inverse(
            body=missing_body.encode("utf-8"),
            plan=artifacts.plan,
            sentence_plan=recovered_plan,
            resolver=artifacts.resolver,
            selected_subjective_input=artifacts.selected_subjective_input,
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

        move = artifacts.plan.response_plan.human_reception_plan.moves[0]
        context_id = reception_owner.final_reception_context_nucleus_ids(
            move=move,
            plan=artifacts.plan,
        )[0]
        nucleus_index = {
            nucleus.nucleus_id: nucleus for nucleus in artifacts.plan.nuclei
        }
        exact_context = reception_owner.final_reception_source_anchor_text(
            context_id,
            nucleus_index,
            artifacts.resolver,
        )
        replayed_body = _tamper_reception(
            recovered_surface.text,
            rendered_context,
            f"{exact_context}という言葉",
        )
        replayed_inverse = evaluate_grounded_surface_body_inverse(
            body=replayed_body.encode("utf-8"),
            plan=artifacts.plan,
            sentence_plan=recovered_plan,
            resolver=artifacts.resolver,
            selected_subjective_input=artifacts.selected_subjective_input,
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
        recovered_surface = _recovery_surface(artifacts, recovered_plan)
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
            selected_subjective_input=artifacts.selected_subjective_input,
        )
        self.assertTrue(inverse.passed, inverse.failure_codes)
        gate = evaluate_grounded_observation_gate(
            plan=artifacts.plan,
            sentence_plan=recovered_plan,
            surface_result=recovered_surface,
            resolver=artifacts.resolver,
            product_readfeel_status="not_evaluated",
            require_body_inverse=True,
            selected_subjective_input=artifacts.selected_subjective_input,
        )
        self.assertTrue(gate.passed, gate.rejection_reasons)


    def test_selected_reception_input_is_immutable_and_reused_for_replay(self) -> None:
        branches = set()
        for case_id, artifacts in self.artifacts.items():
            with self.subTest(case_id=case_id):
                selected = artifacts.selected_subjective_input
                branches.update(row.branch for row in selected.decisions)
                with self.assertRaises(FrozenInstanceError):
                    selected.input_ref = "changed"
                with self.assertRaises(FrozenInstanceError):
                    selected.decisions[0].subjective_proposition.epistemic_scope = "changed"
                self.assertTrue(artifacts.author_arguments)
                self.assertTrue(all(
                    kwargs["selected_subjective_input"] is selected
                    for _args, kwargs in artifacts.author_arguments
                ))
                line = next(row for row in artifacts.sentence_plan.lines
                            if row.binding.line_role == "human_follow")
                replay = reception_owner.replay_source_grounded_human_reception_from_plan(
                    artifacts.plan.response_plan.human_reception_plan,
                    {row.nucleus_id: row for row in artifacts.plan.nuclei},
                    artifacts.resolver,
                    plan=artifacts.plan,
                    recovery_stage=artifacts.sentence_plan.recovery_stage,
                    clause_plans=line.reception_clause_plans,
                    selected_subjective_input=selected,
                )
                self.assertEqual(replay.text, _reception_text(artifacts.surface.text).strip())
                self.assertTrue(any(row.text == replay.text for row in artifacts.authored))
                seen = []
                original = gate_owner.replay_source_grounded_human_reception_from_plan

                def track_replay(*args, **kwargs):
                    seen.append(kwargs["selected_subjective_input"])
                    return original(*args, **kwargs)

                with patch.object(gate_owner, "replay_source_grounded_human_reception_from_plan", side_effect=track_replay):
                    evaluation = evaluate_grounded_surface_body_inverse(
                        body=artifacts.surface.text.encode("utf-8"), plan=artifacts.plan,
                        sentence_plan=artifacts.sentence_plan, resolver=artifacts.resolver,
                        selected_subjective_input=selected,
                    )
                self.assertTrue(evaluation.passed, evaluation.failure_codes)
                self.assertTrue(seen)
                self.assertTrue(all(value is selected for value in seen))
        self.assertEqual(branches, {"NORMAL", "LIMITED"})

    def test_selected_reception_input_missing_or_foreign_fails_closed(self) -> None:
        artifacts = self.artifacts["nls3s_b001_0024"]
        foreign = self.artifacts["nls3s_b001_0051"].selected_subjective_input
        line = next(row for row in artifacts.sentence_plan.lines
                    if row.binding.line_role == "human_follow")
        for invalid in (None, foreign):
            with self.subTest(missing=invalid is None):
                evaluation = evaluate_grounded_surface_body_inverse(
                    body=artifacts.surface.text.encode("utf-8"), plan=artifacts.plan,
                    sentence_plan=artifacts.sentence_plan, resolver=artifacts.resolver,
                    selected_subjective_input=invalid,
                )
                self.assertFalse(evaluation.passed)
                self.assertIn("body_inverse_reception_replay_unavailable:1", evaluation.failure_codes)
                gate = evaluate_grounded_observation_gate(
                    plan=artifacts.plan, sentence_plan=artifacts.sentence_plan,
                    surface_result=artifacts.surface, resolver=artifacts.resolver,
                    require_body_inverse=True, selected_subjective_input=invalid,
                )
                self.assertFalse(gate.passed)
                with self.assertRaises(reception_owner.GroundedHumanReceptionSurfaceError):
                    reception_owner.replay_source_grounded_human_reception_from_plan(
                        artifacts.plan.response_plan.human_reception_plan,
                        {row.nucleus_id: row for row in artifacts.plan.nuclei}, artifacts.resolver,
                        plan=artifacts.plan, recovery_stage=artifacts.sentence_plan.recovery_stage,
                        clause_plans=line.reception_clause_plans, selected_subjective_input=invalid,
                    )
                args, kwargs = artifacts.author_arguments[0]
                with self.assertRaises(reception_owner.GroundedHumanReceptionSurfaceError):
                    response_owner.realize_source_grounded_human_reception(
                        *args, **{**kwargs, "selected_subjective_input": invalid},
                    )

    def test_selected_reception_boundary_rejects_resealed_semantic_mutations(self) -> None:
        inputs = _compile_inputs(self.rows_by_id["nls3s_b001_0024"])
        original = response_owner._build_selected_subjective_reception_input

        def change_decision(value, **changes):
            row = reception_owner.identify_selected_subjective_reception_decision(
                replace(value.decisions[0], **changes),
            )
            return replace(value, decisions=(row, *value.decisions[1:]))

        def change_basis(value):
            row = value.decisions[0]
            self.assertTrue(row.basis_rows)
            changed = replace(row.basis_rows[0], contribution_ref="foreign-contribution")
            return change_decision(value, basis_rows=(changed, *row.basis_rows[1:]))

        def change_qualifier(value):
            row = next(row for row in value.decisions if row.qualifier_rows)
            changed = replace(row.qualifier_rows[0], time_scope="foreign-time-scope")
            changed_row = reception_owner.identify_selected_subjective_reception_decision(
                replace(row, qualifier_rows=(changed, *row.qualifier_rows[1:])),
            )
            return replace(value, decisions=tuple(changed_row if item is row else item for item in value.decisions))

        def replace_appraisal(value, row, appraisal, *, focal_relation_ref):
            proposition = replace(row.subjective_proposition,
                                  appraisal_content=appraisal, focal_relation_ref=focal_relation_ref)
            # Use an internally legal existing content shape. The compiler
            # must reject it because it differs from the selected authority.
            contracts_owner._stage1_subjective_v2_content_bindings(proposition)
            changed_row = reception_owner.identify_selected_subjective_reception_decision(
                replace(row, subjective_proposition=proposition),
            )
            return replace(value, decisions=tuple(changed_row if item is row else item for item in value.decisions))

        def change_appraisal_operation(value):
            row = next(row for row in value.decisions if row.subjective_proposition.appraisal_content is not None)
            appraisal = row.subjective_proposition.appraisal_content
            pair = (contracts_owner.AppraisalDimension.UNFINISHED_OPENNESS,
                    contracts_owner.AppraisalOperation.LEAVE_UNFINISHED)
            if (appraisal.dimension, appraisal.operation) == pair:
                pair = (contracts_owner.AppraisalDimension.MATERIAL_WEIGHT,
                        contracts_owner.AppraisalOperation.RECEIVE_AS_MATERIAL)
            return replace_appraisal(value, row, replace(appraisal, dimension=pair[0], operation=pair[1]),
                                     focal_relation_ref=row.subjective_proposition.focal_relation_ref)

        def change_focal_pair(value):
            row = next(row for row in value.decisions if row.subjective_proposition.appraisal_content is not None)
            appraisal = row.subjective_proposition.appraisal_content
            alternate = next(ref for ref, _relation_id in value.relation_pairs
                             if ref != row.subjective_proposition.focal_relation_ref)
            # Both focal fields name the same admitted relation. Neither a
            # mismatched pair nor an unknown relation is the rejection cause.
            return replace_appraisal(value, row, replace(appraisal, focal_relation_ref=alternate),
                                     focal_relation_ref=alternate)

        mutations = {
            "branch": lambda value: change_decision(value, branch="LIMITED" if value.decisions[0].branch == "NORMAL" else "NORMAL"),
            "outcome": lambda value: change_decision(value, meaning_outcome_ref="foreign-outcome"),
            "opportunity": lambda value: change_decision(value, selected_opportunity_ref="foreign-opportunity"),
            "claim": lambda value: change_decision(value, projected_claim_ref="foreign-claim"),
            "proposition": lambda value: change_decision(value, subjective_proposition=replace(value.decisions[0].subjective_proposition, epistemic_scope="FOREIGN_SCOPE")),
            "selected_subset": lambda value: change_decision(value, selected_contribution_refs=("foreign-contribution",)),
            "appraisal_operation": change_appraisal_operation,
            "focal_pair": change_focal_pair,
            "basis": change_basis,
            "qualifier": change_qualifier,
            "preimage": lambda value: replace(value, projection_preimage_ref="foreign-preimage"),
            "seal": lambda value: replace(value, projection_seal_ref="foreign-seal"),
            "nucleus_mapping": lambda value: replace(value, semantic_nucleus_pairs=(("foreign-semantic-ref", value.semantic_nucleus_pairs[0][1]), *value.semantic_nucleus_pairs[1:])),
        }
        for label, mutation in mutations.items():
            with self.subTest(field=label):
                mutation_inputs = (_compile_inputs(self.rows_by_id["nls3s_b001_0081"])
                                   if label == "focal_pair" else inputs)
                def tamper(*args, **kwargs):
                    expected = original(*args, **kwargs)
                    changed = reception_owner.identify_selected_subjective_reception_input(mutation(expected))
                    # Re-identification is deliberate: identity consistency must
                    # not substitute for the original upstream decision.
                    self.assertNotEqual(changed, expected)
                    self.assertEqual(reception_owner.identify_selected_subjective_reception_input(changed), changed)
                    return changed

                with (
                    patch.object(response_owner, "_build_selected_subjective_reception_input", side_effect=tamper),
                    patch.object(response_owner, "realize_source_grounded_human_reception", side_effect=AssertionError("untrusted decision reached author")) as author,
                    self.assertRaisesRegex(contracts_owner.CMEEStage1ContractError, "MEANING_REALIZATION_CAUSAL_TRACE_GAP"),
                ):
                    response_owner.compile_stage1_response(
                        source=mutation_inputs.source, grounded_graph=mutation_inputs.graph,
                        parent_plan=mutation_inputs.parent_plan, grounded_plan=mutation_inputs.grounded_plan,
                    )
                author.assert_not_called()


if __name__ == "__main__":
    unittest.main()
