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
    def test_separate_selected_performed_action_keeps_source_and_replay(self):
        action = "作業台を片づけた"
        structural_moves = []
        build_moves = observation_plan_owner._build_reception_depth_policy_and_moves

        def capture_moves(*args, **kwargs):
            result = build_moves(*args, **kwargs)
            structural_moves.append(result[1])
            return result

        with patch.object(
            observation_plan_owner, "_build_reception_depth_policy_and_moves",
            side_effect=capture_moves,
        ):
            a = _full_surface_artifacts({
                "case_id": "public-separate-performed-action-reference",
                "input": {
                    "thought_text": "模型が完成してうれしかった。でも、説明書どおりに作れたのかは分からない。",
                    "action_text": action + "。", "categories": ["趣味"],
                    "emotions": [{"type": "平穏", "strength": "medium"}],
                },
            })
        self.assertTrue(a.gate.passed, a.gate.rejection_reasons)
        self.assertTrue(a.inverse.passed, a.inverse.failure_codes)
        self.assertEqual(a.sentence_plan.recovery_stage, "full")
        reception = a.plan.response_plan.human_reception_plan
        first, effort = reception.moves
        self.assertEqual(effort.reception_act, "honor_concrete_effort")
        self.assertEqual(effort.move_role, "felt_response")
        self.assertEqual(effort.reference_mode, "short_anchor_if_ambiguous")
        self.assertIn((first, replace(effort, reference_mode="anaphoric_first")), structural_moves)
        self.assertEqual(effort.support_nucleus_ids, ())
        self.assertTrue(all(move.required for move in reception.moves))
        follow = _reception_text(a.surface.text)
        self.assertEqual(follow.count(action + "こと"), 1)
        self.assertNotIn("実際の行動", follow)
        self.assertLess(follow.index("分からない"), follow.index(action))
        for old, new in (
            (action, ""), (action, "別のものを片づけた"),
            (action, "作業台を片づけるつもり"),
            (action, "作業台を片づけなかった"),
            (action, "「" + action + "」"),
            (action, action + "ことと" + action),
            ("大切に思っています", "小さなことだと考えています"),
        ):
            with self.subTest(replacement=new):
                changed = _tamper_reception(a.surface.text, old, new)
                self.assertFalse(evaluate_grounded_surface_body_inverse(
                    body=changed.encode("utf-8"), plan=a.plan,
                    sentence_plan=a.sentence_plan, resolver=a.resolver,
                    selected_subjective_input=a.selected_subjective_input,
                ).passed)
                self.assertFalse(evaluate_grounded_observation_gate(
                    plan=a.plan, sentence_plan=a.sentence_plan,
                    surface_result=replace(a.surface, text=changed),
                    resolver=a.resolver, require_body_inverse=True,
                    selected_subjective_input=a.selected_subjective_input,
                ).passed)
        for stage in ("integrated", "hedged", "minimal_grounded"):
            self.assertEqual(reception_owner.reception_effective_move_reference_mode(
                reception, effort, stage,
            ), "anaphoric_first")

    def test_separate_action_reference_requires_performance_and_independent_context(self):
        plan = build_final_stage1_grounded_observation_plan({
            "memo": "模型が完成してうれしかった。でも、説明書どおりに作れたのかは分からない。",
            "memo_action": "作業台を片づけた。",
        })
        response = plan.response_plan
        kwargs = dict(
            required=True, human_follow_target_ids=response.human_follow_target_ids,
            primary_nucleus_ids=response.primary_nucleus_ids,
            supporting_nucleus_ids=response.supporting_nucleus_ids,
            required_nucleus_ids=response.required_nucleus_ids,
            fact_boundary_nucleus_ids=response.fact_boundary_nucleus_ids,
            nuclei=plan.nuclei, relations=plan.relations,
            safety_kind=plan.safety_policy.safety_kind,
            material_quality="limited_grounding",
            semantic_complexity=plan.input_profile.semantic_complexity,
            final_source_fidelity=True,
        )
        build = observation_plan_owner.build_grounded_human_reception_plan
        reception = build(**kwargs)
        first, effort = reception.moves
        self.assertEqual(effort.reference_mode, "short_anchor_if_ambiguous")
        target = next(n for n in plan.nuclei if n.nucleus_id == effort.target_nucleus_ids[0])
        other = next(n for n in plan.nuclei if n.nucleus_id == first.target_nucleus_ids[0])
        original_moves = (first, replace(effort, reference_mode="anaphoric_first"))

        def with_target(changed):
            return tuple(changed if n.nucleus_id == target.nucleus_id else n for n in plan.nuclei)

        relation = replace(plan.relations[0], from_nucleus_id=other.nucleus_id,
                           to_nucleus_id=target.nucleus_id, retention="required")
        variants = (
            {"final_source_fidelity": False},
            {"material_quality": "short_state_sufficient"},
            {"semantic_complexity": "single"},
            {"nuclei": with_target(replace(target, retention="should"))},
            {"nuclei": with_target(replace(target, semantic_frame=replace(
                target.semantic_frame, actor="other_person")))},
            {"nuclei": with_target(replace(target, semantic_frame=replace(
                target.semantic_frame, modality="wish", time_scope="future")))},
            {"nuclei": with_target(replace(target, semantic_frame=replace(
                target.semantic_frame, attribute_codes=tuple(c for c in
                    target.semantic_frame.attribute_codes if c != "operator:performed_action"))))},
            {"nuclei": with_target(replace(target, source_span_ids=other.source_span_ids))},
            {"relations": (*plan.relations, relation)},
        )
        # Hold the already selected duties fixed to test the reference policy,
        # without allowing another selection to hide a missing proof.
        for changes in variants:
            with self.subTest(changes=changes), patch.object(
                observation_plan_owner, "_build_reception_depth_policy_and_moves",
                return_value=(reception.depth_policy, original_moves),
            ):
                rebuilt = build(**(kwargs | changes))
                self.assertEqual(rebuilt.moves[1], original_moves[1])
        for changed_effort in (
            replace(original_moves[1], required=False),
            replace(original_moves[1], support_nucleus_ids=first.target_nucleus_ids),
        ):
            with self.subTest(move=changed_effort), patch.object(
                observation_plan_owner, "_build_reception_depth_policy_and_moves",
                return_value=(reception.depth_policy, (first, changed_effort)),
            ):
                self.assertEqual(build(**kwargs).moves[1], changed_effort)

    def test_independent_selected_relation_keeps_both_concrete_endpoints(self):
        left = "覚えたい気持ちはある"
        right = "手順が分からなくなった"
        structural_moves = []
        build_moves = observation_plan_owner._build_reception_depth_policy_and_moves

        def capture_moves(*args, **kwargs):
            result = build_moves(*args, **kwargs)
            structural_moves.append(result[1])
            return result

        with patch.object(
            observation_plan_owner, "_build_reception_depth_policy_and_moves",
            side_effect=capture_moves,
        ):
            a = _full_surface_artifacts({
                "case_id": "public-independent-learning-relation",
                "input": {
                    "thought_text": f"{left}。でも{right}。",
                    "action_text": "説明書を棚に戻した。",
                    "categories": ["学習"],
                    "emotions": [{"type": "不安", "strength": "medium"}],
                },
            })
        self.assertTrue(a.gate.passed, a.gate.rejection_reasons)
        self.assertTrue(a.inverse.passed, a.inverse.failure_codes)
        self.assertEqual(a.sentence_plan.recovery_stage, "full")
        reception = a.plan.response_plan.human_reception_plan
        self.assertEqual(len(reception.moves), 2)
        self.assertTrue(all(move.required for move in reception.moves))
        self.assertEqual(reception.moves[1].reference_mode, "short_anchor_if_ambiguous")
        old_reference_moves = tuple(
            replace(move, reference_mode="anaphoric_first") if index else move
            for index, move in enumerate(reception.moves)
        )
        self.assertIn(old_reference_moves, structural_moves)
        follow = _reception_text(a.surface.text)
        for source in (left, right, "説明書を棚に戻した"):
            self.assertEqual(follow.count(source), 1)
        self.assertIn(left + "ということと" + right + "ことを見過ごさず、その違いも含めて", follow)
        self.assertNotIn("との違いに目が留まり", follow)
        self.assertNotIn("もう一方の向き", follow)
        for source, replacement in ((left, ""), (right, "別のこと"), ("その違いも含めて", "同じものとして")):
            with self.subTest(source=source):
                changed = _tamper_reception(a.surface.text, source, replacement)
                self.assertFalse(evaluate_grounded_surface_body_inverse(
                    body=changed.encode("utf-8"), plan=a.plan,
                    sentence_plan=a.sentence_plan, resolver=a.resolver,
                    selected_subjective_input=a.selected_subjective_input,
                ).passed)
        for stage in ("integrated", "hedged", "minimal_grounded"):
            self.assertEqual(reception_owner.reception_effective_move_reference_mode(
                reception, reception.moves[1], stage,
            ), "anaphoric_first")

    def test_retained_wish_nominal_keeps_existence_context_and_protection(self):
        source = "繰り返したい気持ちはある"
        context = "手順が分からなくなった"
        row = {
            "case_id": "public-retained-wish-carrier",
            "input": {
                "thought_text": f"{source}。でも{context}。",
                "action_text": "説明書を棚に戻した。",
                "categories": ["学習"],
                "emotions": [{"type": "不安", "strength": "medium"}],
            },
        }
        a = _full_surface_artifacts(row)
        self.assertTrue(a.gate.passed, a.gate.rejection_reasons)
        self.assertTrue(a.inverse.passed, a.inverse.failure_codes)
        self.assertEqual(a.sentence_plan.recovery_stage, "full")
        follow = _reception_text(a.surface.text)
        nominal = source + "ということ"
        self.assertEqual(follow.count(nominal), 1)
        self.assertNotIn("に表れた願い", follow)
        self.assertNotIn("今も、", follow)
        self.assertIn(nominal + "と" + context + "ことを見過ごさず、その重なりも含めて", follow)
        self.assertIn("見失わずに、大切に受け止めています", follow)
        for old, new in (
            (nominal, source + "こと"),
            (nominal, source.removesuffix("はある")),
            (nominal, source.replace("はある", "がある") + "ということ"),
            (nominal, source.replace("はある", "はあった") + "ということ"),
            (nominal, source.replace("はある", "はない") + "ということ"),
            (nominal, "別の気持ちはあるということ"),
            (nominal, "「" + nominal + "」"), (nominal, nominal + "と" + nominal),
            (nominal, "『" + nominal + "』"),
            (context, "別のこと"), ("その重なりも含めて", "同じものとして"),
            ("その重なりも含めて", ""), ("を見過ごさず、", "に目が留まり、"),
            ("見失わずに、大切に受け止めています", "小さなことだと考えています"),
            (nominal, "今も、" + nominal),
        ):
            with self.subTest(replacement=new):
                inverse = evaluate_grounded_surface_body_inverse(
                    body=_tamper_reception(a.surface.text, old, new).encode("utf-8"),
                    plan=a.plan, sentence_plan=a.sentence_plan, resolver=a.resolver,
                    selected_subjective_input=a.selected_subjective_input,
                )
                self.assertFalse(inverse.passed)
                self.assertFalse(evaluate_grounded_observation_gate(
                    plan=a.plan, sentence_plan=a.sentence_plan,
                    surface_result=replace(a.surface, text=_tamper_reception(a.surface.text, old, new)),
                    resolver=a.resolver, require_body_inverse=True,
                    selected_subjective_input=a.selected_subjective_input,
                ).passed)
        reception = a.plan.response_plan.human_reception_plan
        move = next(m for m in reception.moves if m.reception_act == "protect_retained_intention")
        index = {n.nucleus_id: n for n in a.plan.nuclei}
        target = index[move.target_nucleus_ids[0]]
        derive = reception_owner.source_grounded_retained_wish_nominal
        self.assertEqual(target.semantic_frame.time_scope, "current_input")
        self.assertIn("operator:continuation", target.semantic_frame.attribute_codes)
        frozen = freeze_text_source(_request_from_row(row))
        span = next(s for s in frozen.evidence_spans if s.span_id == target.source_span_ids[0])
        before = replace(target, semantic_frame=replace(
            target.semantic_frame, time_scope="continuing", attribute_codes=tuple(
                c for c in target.semantic_frame.attribute_codes if not c.startswith("time_scope:")
            ) + ("time_scope:continuing",),
        ))
        align = observation_plan_owner._final_stage1_align_action_status
        after, = align((before,), (span,), normalized_input=frozen.normalized_current_input)
        self.assertEqual(after, target)
        self.assertEqual(align((before,), (span,)), (before,))
        for prefix, suffix in (
            ("", "？"), ("", "、と説明していた。"), ("友人の話では、", "。"),
            ("（", "）。"), ("", "とは言い切れない。"),
        ):
            field = prefix + source + suffix
            clipped = replace(span, start_index=len(prefix), end_index=len(prefix) + len(source))
            with self.subTest(prefix=prefix, suffix=suffix):
                self.assertEqual(align(
                    (before,), (clipped,), normalized_input={span.source_field: field},
                ), (before,))
        self.assertEqual(derive(move, a.plan, index, a.resolver), nominal)
        self.assertEqual(derive(move, None, index, a.resolver), "")
        self.assertEqual(derive(move, replace(a.plan, source_contracts=()), index, a.resolver), "")
        for changes in (
            {"actor": "other"}, {"actor": "unknown"}, {"modality": "uncertain"},
            {"modality": "fact"}, {"time_scope": "past"}, {"time_scope": "future"},
            {"polarity": "negative"}, {"predicate_kind": "action"},
            {"attribute_codes": (*target.semantic_frame.attribute_codes, "quantity:multiple")},
            {"attribute_codes": (*target.semantic_frame.attribute_codes, "operator:performed_action")},
            {"time_scope": "continuing"},
        ):
            changed = replace(target, semantic_frame=replace(target.semantic_frame, **changes))
            plan = replace(a.plan, nuclei=tuple(changed if n == target else n for n in a.plan.nuclei))
            with self.subTest(changes=changes):
                self.assertEqual(derive(move, plan, {**index, target.nucleus_id: changed}, a.resolver), "")
        for value in (
            "覚えたい思いはある", "覚えたい気持ちはあった", "覚えたい気持ちはまだある",
            "覚えたい気持ちはない", "覚えたい気持ちはあるかもしれない", "覚えたい気持ちはあります",
            "覚えたい気持ちはある？", "覚えたい気持ちはある…", "「覚えたい気持ちはある」",
        ):
            with self.subTest(value=value), patch.object(
                reception_owner, "_source_grounded_clause_candidate", return_value=value,
            ):
                self.assertEqual(derive(move, a.plan, index, a.resolver), "")
        kwargs = dict(reception_plan=reception, move=move, nucleus_index=index,
                      resolver=a.resolver, allow_short_anchor=False, plan=a.plan)
        self.assertNotEqual(reception_owner.resolve_grounded_reception_move_referent(**kwargs).text, nominal)
        self.assertNotEqual(reception_owner.resolve_grounded_reception_move_referent(
            **kwargs, final_source_fidelity=True, recovery_stage="integrated",
        ).text, nominal)
        desired = observation_plan_owner._final_stage1_continuation_is_desired
        for value in (source, "模型を作り続けたい気持ちはある", "同じ確認を繰り返したい願いがある"):
            self.assertFalse(desired(value))
            self.assertTrue(desired(value, allow_nominal_carrier=True))
        for value in (
            "ずっと模型を作り続けたい気持ちはある", "模型を作り続けたい気持ちはあった",
            "模型を作り続けたい気持ちはまだある", "模型を作り続けたい気持ちはない",
            "模型を作り続けたい気持ちはあると思う", "模型を作り続けたい気持ちはある？",
            "「模型を作り続けたい気持ちはある」", "模型を作り続けたい気持ちはある…",
        ):
            with self.subTest(value=value):
                self.assertFalse(desired(value, allow_nominal_carrier=True))

    def test_retained_wish_quotative_keeps_case_and_bounded_body_witness(self):
        source = "繰り返したい気持ちがある"
        a = _full_surface_artifacts({"case_id": "public-retained-wish-case", "input": {
            "thought_text": source + "。でも手順が分からなくなった。",
            "action_text": "説明書を棚に戻した。", "categories": ["学習"],
            "emotions": [{"type": "不安", "strength": "medium"}],
        }})
        nominal = source + "ということ"
        self.assertTrue(a.gate.passed, a.gate.rejection_reasons)
        self.assertTrue(a.inverse.passed, a.inverse.failure_codes)
        self.assertEqual(_reception_text(a.surface.text).count(nominal), 1)
        encoded = a.surface.text.encode("utf-8")
        start = encoded.index(nominal.encode("utf-8"))
        end = start + len(nominal.encode("utf-8"))
        self.assertTrue(any(
            m.section == "reception" and m.marker_kind == "semantic"
            and m.marker_code == "finite_clause_nominal"
            and start <= m.utf8_byte_start and m.utf8_byte_end == end
            for m in surface_owner.parse_grounded_surface_body_bytes(encoded).markers
        ))
        for replacement in (source + "こと", source.replace("がある", "はある") + "ということ"):
            with self.subTest(replacement=replacement):
                self.assertFalse(evaluate_grounded_surface_body_inverse(
                    body=_tamper_reception(a.surface.text, nominal, replacement).encode("utf-8"),
                    plan=a.plan, sentence_plan=a.sentence_plan, resolver=a.resolver,
                    selected_subjective_input=a.selected_subjective_input,
                ).passed)
        for fragment in ("物を買うということ", "箱があるということ", "気持ちはあるということ",
                         "繰り返したい気持ちはないということ", "繰り返したい気持ちはあったということ"):
            body = (surface_owner.OBSERVATION_SECTION_LABEL + "\n記録があります。\n"
                    + surface_owner.RECEPTION_SECTION_LABEL + "\n" + fragment + "を大切に思っています。")
            with self.subTest(fragment=fragment):
                self.assertFalse(any(m.marker_code == "finite_clause_nominal"
                                     for m in surface_owner.parse_grounded_surface_body_bytes(body.encode()).markers))

    def test_changing_wish_nominal_preserves_degree_context_and_protection(self):
        context = "今の暮らしを変える怖さもあって、急いで決めたくない"
        for degree in ("強", "弱"):
            source = f"新しい分野を学びたい気持ちが{degree}くなっている"
            with self.subTest(degree=degree):
                a = _full_surface_artifacts({"case_id": "public-changing-wish", "input": {
                    "thought_text": source + "。でも" + context + "。",
                    "action_text": "本を棚に戻した。", "categories": ["学習"],
                    "emotions": [{"type": "不安", "strength": "medium"}],
                }})
                self.assertTrue(a.gate.passed, a.gate.rejection_reasons)
                self.assertTrue(a.inverse.passed, a.inverse.failure_codes)
                self.assertEqual(a.sentence_plan.recovery_stage, "full")
                nominal = source + "こと"
                follow = _reception_text(a.surface.text)
                self.assertEqual(follow.count(nominal), 1)
                self.assertEqual(follow.count(context), 1)
                self.assertNotIn("に表れた願い", follow)
                self.assertIn("その違いも含めて見失わずに、大切に受け止めています", follow)
                for old, new in (
                    (nominal, source.replace(degree, "弱" if degree == "強" else "強") + "こと"),
                    (nominal, source.removesuffix(f"が{degree}くなっている")),
                    (nominal, source.replace("気持ちが", "気持ちは") + "こと"),
                    (nominal, source.replace("なっている", "なっていた") + "こと"),
                    (nominal, source.replace("なっている", "なっていない") + "こと"),
                    (nominal, source.replace("学びたい", "遊びたい") + "こと"),
                    (nominal, nominal + "と" + nominal), (nominal, "「" + nominal + "」"),
                    (nominal, source + "ということ"), (context, "別のこと"),
                    ("その違いも含めて", "同じものとして"),
                    ("見失わずに、大切に受け止めています", "小さなことだと考えています"),
                ):
                    with self.subTest(replacement=new):
                        changed = _tamper_reception(a.surface.text, old, new)
                        self.assertFalse(evaluate_grounded_surface_body_inverse(
                            body=changed.encode("utf-8"), plan=a.plan,
                            sentence_plan=a.sentence_plan, resolver=a.resolver,
                            selected_subjective_input=a.selected_subjective_input,
                        ).passed)
                        self.assertFalse(evaluate_grounded_observation_gate(
                            plan=a.plan, sentence_plan=a.sentence_plan,
                            surface_result=replace(a.surface, text=changed), resolver=a.resolver,
                            require_body_inverse=True, selected_subjective_input=a.selected_subjective_input,
                        ).passed)

    def test_changing_wish_nominal_requires_existing_selected_source_proof(self):
        source = "学びたい気持ちが強くなっている"
        a = _full_surface_artifacts({"case_id": "public-changing-wish-proof", "input": {
            "thought_text": source + "。でも手順が分からなくなった。",
            "action_text": "本を棚に戻した。", "categories": ["学習"],
            "emotions": [{"type": "不安", "strength": "medium"}],
        }})
        move = next(m for m in a.plan.response_plan.human_reception_plan.moves
                    if m.reception_act == "protect_retained_intention")
        index = {n.nucleus_id: n for n in a.plan.nuclei}
        target = index[move.target_nucleus_ids[0]]
        derive = reception_owner.source_grounded_retained_wish_nominal
        self.assertEqual(derive(move, a.plan, index, a.resolver), source + "こと")
        proof = "lexical:source_declarative_wish_change"
        self.assertIn(proof, target.semantic_frame.attribute_codes)
        for changes in (
            {"actor": "other"}, {"actor": "unknown"}, {"modality": "uncertain"},
            {"modality": "fact"}, {"time_scope": "past"}, {"time_scope": "future"},
            {"polarity": "negative"}, {"predicate_kind": "action"},
            {"attribute_codes": (*target.semantic_frame.attribute_codes, "quantity:multiple")},
            {"attribute_codes": (*target.semantic_frame.attribute_codes, "operator:performed_action")},
            {"attribute_codes": tuple(c for c in target.semantic_frame.attribute_codes if c != proof)},
        ):
            changed = replace(target, semantic_frame=replace(target.semantic_frame, **changes))
            plan = replace(a.plan, nuclei=tuple(changed if n == target else n for n in a.plan.nuclei))
            with self.subTest(changes=changes):
                self.assertEqual(derive(move, plan, {**index, target.nucleus_id: changed}, a.resolver), "")
        for value in (
            source.replace("気持ちが", "気持ちは"), source.replace("気持ちが", "気持ちも"),
            source.replace("なっている", "なっていた"), source.replace("なっている", "なっています"),
            source.replace("なっている", "なっていない"), source + "かもしれない",
            source + "と聞いた", source + "なら", source + "？", source + "…",
            "「" + source + "」", "友人が" + source, source.replace("強くなっている", "強まっている"),
        ):
            with self.subTest(value=value), patch.object(
                reception_owner, "_source_grounded_clause_candidate", return_value=value,
            ):
                self.assertEqual(derive(move, a.plan, index, a.resolver), "")
        with patch.object(reception_owner, "_bounded_bare_wish_nominal", return_value=False):
            self.assertEqual(derive(move, a.plan, index, a.resolver), "")
        self.assertEqual(derive(move, None, index, a.resolver), "")
        self.assertEqual(derive(move, replace(a.plan, source_contracts=()), index, a.resolver), "")

        # Exercise original-field boundaries before ledger punctuation handling.
        for field in (source + "？", source + "…", "「" + source + "」", source + "と聞いた。"):
            with self.subTest(original_field=field):
                inputs = _compile_inputs({"case_id": "public-changing-wish-boundary", "input": {
                    "thought_text": field, "action_text": "本を棚に戻した。", "categories": ["学習"],
                    "emotions": [{"type": "不安", "strength": "medium"}],
                }})
                resolver = build_evidence_span_resolver(
                    inputs.source.evidence_spans, current_input=inputs.source.normalized_current_input,
                )
                plan = inputs.grounded_plan
                nuclei = {n.nucleus_id: n for n in plan.nuclei}
                self.assertTrue(all(derive(m, plan, nuclei, resolver) == ""
                                    for m in plan.response_plan.human_reception_plan.moves))

    def test_contrast_target_nominal_keeps_both_endpoints_and_source_argument(self):
        left = "説明書の細かな記号が分かるようになった"
        right = "それでも小さな部品を一つずつ机に並べて確かめながら組み立てる時間はまだ難しく感じている"
        row = {
            "case_id": "public-contrast-target-nominal",
            "input": {
                "thought_text": f"新しい模型に取りかかり、{left}けれど、{right}。",
                "action_text": "道具を箱に戻した。",
                "categories": ["趣味"],
                "emotions": [{"type": "不安", "strength": "medium"}],
            },
        }
        a = _full_surface_artifacts(row)
        self.assertTrue(a.gate.passed)
        self.assertTrue(a.inverse.passed)
        follow = _reception_text(a.surface.text)
        self.assertEqual(follow.count(left + "という変化"), 1)
        self.assertEqual(follow.count(right), 1)
        self.assertIn("ことを見過ごさず、その違いも含めて受け止めています", follow)
        self.assertNotIn("との違いに目が留まり", follow)
        self.assertNotIn("けれどということ", follow)
        self.assertTrue(any(span.raw_text == left + "けれど"
                            for span in a.resolver.resolve_many(a.resolver.span_ids)))
        args, kwargs = a.author_arguments[0]
        ir = reception_owner._source_grounded_plan_clause_realizations(
            args[0], args[2], args[3], plan=kwargs["plan"],
            recovery_stage=kwargs["recovery_stage"], clause_plans=kwargs["clause_plans"],
        )
        self.assertTrue(any(left + "けれど" in move.semantic_fragments
                            for clause in ir for move in clause.moves))
        for source, replacement in ((left, ""), (right, ""), ("その違いも含めて", "同じものとして")):
            changed = _tamper_reception(a.surface.text, source, replacement)
            inverse = evaluate_grounded_surface_body_inverse(
                body=changed.encode("utf-8"), plan=a.plan,
                sentence_plan=a.sentence_plan, resolver=a.resolver,
                selected_subjective_input=a.selected_subjective_input,
            )
            self.assertFalse(inverse.passed)

    def test_contrast_nominal_keeps_ellipsis_and_a_quoted_source_field(self):
        left = "説明書の細かな記号が分かるようになった"
        right = "それでも小さな部品を一つずつ机に並べて確かめながら組み立てる時間はまだ難しく感じている"
        for prefix, ending in (("見出しは「模型」です。", "けれど"), ("", "…けれど")):
            with self.subTest(prefix=prefix, ending=ending):
                row = {
                    "case_id": "public-contrast-nominal-boundary",
                    "input": {
                        "thought_text": f"{prefix}新しい模型に取りかかり、{left}{ending}、{right}。",
                        "action_text": "道具を箱に戻した。",
                        "categories": ["趣味"],
                        "emotions": [{"type": "不安", "strength": "medium"}],
                    },
                }
                a = _full_surface_artifacts(row)
                self.assertTrue(a.gate.passed)
                self.assertTrue(a.inverse.passed)
                follow = _reception_text(a.surface.text)
                self.assertIn(left + ending + "ということ", follow)
                self.assertEqual(follow.count(right), 1)
                self.assertIn("見過ごさず、その違いも含めて受け止めています", follow)
                self.assertNotIn(left + "という変化", follow)
                changed = _tamper_reception(a.surface.text, left + ending, left)
                self.assertFalse(evaluate_grounded_surface_body_inverse(
                    body=changed.encode(), plan=a.plan, sentence_plan=a.sentence_plan,
                    resolver=a.resolver, selected_subjective_input=a.selected_subjective_input,
                ).passed)

    def test_polite_contrast_context_uses_a_quotative_nominal(self):
        row = {
            "case_id": "public-polite-contrast-context",
            "input": {
                "thought_text": "この役割を続けたい。でも、今は困っています。",
                "action_text": "",
                "categories": ["趣味"],
                "emotions": [{"type": "不安", "strength": "medium"}],
            },
        }
        a = _full_surface_artifacts(row)
        self.assertTrue(a.gate.passed)
        self.assertTrue(a.inverse.passed)
        follow = _reception_text(a.surface.text)
        self.assertEqual(follow.count("今は困っていますということ"), 1)
        self.assertIn("この役割を続けたいという願いと", follow)
        self.assertIn("との違いを見失わず", follow)
        self.assertNotIn("困っていますこと", follow)
        changed = _tamper_reception(a.surface.text, "今は困っています", "困っていました")
        inverse = evaluate_grounded_surface_body_inverse(
            body=changed.encode("utf-8"), plan=a.plan,
            sentence_plan=a.sentence_plan, resolver=a.resolver,
            selected_subjective_input=a.selected_subjective_input,
        )
        self.assertFalse(inverse.passed)

    def test_attention_resumes_its_object_before_the_reception_predicate(self):
        row = {
            "case_id": "public-attention-governed-change",
            "input": {
                "thought_text": "休憩したら、頭の切り替えができた感じ。",
                "action_text": "机の上を片づけた。",
                "categories": ["生活"],
                "emotions": [{"type": "平穏", "strength": "medium"}],
            },
        }
        a = _full_surface_artifacts(row)
        self.assertTrue(a.gate.passed)
        self.assertTrue(a.inverse.passed)
        moves = a.plan.response_plan.human_reception_plan.moves
        self.assertEqual(
            tuple((m.reception_act, m.move_role) for m in moves),
            (("recognize_lived_change", "attention"),
             ("honor_concrete_effort", "felt_response")),
        )
        follow = _reception_text(a.surface.text)
        self.assertEqual(follow.count("頭の切り替えができた感じ"), 1)
        self.assertIn("に目が留まり、それを感じています", follow)
        self.assertEqual(follow.count("机の上を片づけたことを大切に思っています"), 1)
        self.assertNotIn("実際の行動をそれを", follow)
        for authored in a.authored:
            with self.subTest(stage=authored.recovery_stage):
                self.assertIn("に目が留まり、それを", authored.text)
        for changed_object in ("", "別のことを"):
            changed = _tamper_reception(
                a.surface.text, "に目が留まり、それを",
                "に目が留まり、" + changed_object,
            )
            self.assertNotEqual(changed, a.surface.text)
            inverse = evaluate_grounded_surface_body_inverse(
                body=changed.encode("utf-8"), plan=a.plan,
                sentence_plan=a.sentence_plan, resolver=a.resolver,
                selected_subjective_input=a.selected_subjective_input,
            )
            self.assertFalse(inverse.passed)
            self.assertTrue(any("reception_replay_mismatch" in code
                                for code in inverse.failure_codes))

    def test_attention_object_resumption_preserves_a_source_anaphor(self):
        row = {
            "case_id": "public-attention-source-anaphor",
            "input": {
                "thought_text": "少し前に書いたものを読み返した。",
                "action_text": "それをノートに書いた。",
                "categories": ["生活"],
                "emotions": [{"type": "不安", "strength": "medium"}],
            },
        }
        a = _full_surface_artifacts(row)
        self.assertTrue(a.gate.passed)
        self.assertTrue(a.inverse.passed)
        follow = _reception_text(a.surface.text)
        self.assertEqual(follow.count("それをノートに書いた"), 1)
        self.assertIn(
            "それをノートに書いたことを見過ごさず、"
            "大切に受け止めています", follow,
        )
        self.assertNotIn("大切にそれを", follow)
        for authored in a.authored:
            with self.subTest(stage=authored.recovery_stage):
                self.assertIn("を見過ごさず、大切に受け止めています" if authored.recovery_stage == "full"
                              else "に目が留まり、それを大切に思っています", authored.text)

    def test_anaphoric_context_stays_visible_without_repeating_its_relation(self):
        rows, _ = load_validated_batch(_BATCH_PATH, _MANIFEST_PATH)
        exercised = 0
        for row in rows:
            if row["case_id"] not in _TYPED_RELATION_CLOSURE_CASE_IDS:
                continue
            artifacts = _full_surface_artifacts(row)
            self.assertTrue(artifacts.inverse.passed)
            self.assertTrue(artifacts.gate.passed)
            # Independent full references are now concrete. Exercise the same
            # anaphoric context duty in its existing integrated recovery route.
            sentence_plan = surface_owner.build_reception_recovery_sentence_plan(
                artifacts.sentence_plan, artifacts.plan, artifacts.resolver,
                recovery_stage="integrated",
            )
            surface = _recovery_surface(artifacts, sentence_plan)
            follow = _reception_text(surface.text)
            if "が重なる中での" not in follow:
                continue
            exercised += 1
            self.assertTrue(evaluate_grounded_surface_body_inverse(
                body=surface.text.encode("utf-8"), plan=artifacts.plan,
                sentence_plan=sentence_plan, resolver=artifacts.resolver,
                selected_subjective_input=artifacts.selected_subjective_input,
            ).passed)
            self.assertTrue(evaluate_grounded_observation_gate(
                plan=artifacts.plan, sentence_plan=sentence_plan,
                surface_result=surface, resolver=artifacts.resolver,
                product_readfeel_status="not_evaluated", require_body_inverse=True,
                selected_subjective_input=artifacts.selected_subjective_input,
            ).passed)
            self.assertNotIn("が重なる中で、", follow)
            changed = _tamper_reception(
                surface.text, "が重なる中での", "と",
            )
            inverse = evaluate_grounded_surface_body_inverse(
                body=changed.encode("utf-8"), plan=artifacts.plan,
                sentence_plan=sentence_plan, resolver=artifacts.resolver,
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


class CMEEUnresolvedQuestionSourceTest(unittest.TestCase):
    def _source_plan(self, text):
        source = freeze_text_source(_request_from_row({
            "case_id": "unresolved-question-source-unit",
            "input": {"thought_text": text, "action_text": "",
                      "categories": ["生活"],
                      "emotions": [{"type": "不安", "strength": "weak"}]},
        }))
        plan = build_grounded_observation_plan(
            source.normalized_current_input, evidence_spans=source.evidence_spans,
        )
        return source, plan

    def test_finite_cognitive_unknown_preserves_same_nucleus_and_source(self):
        for text in ("まだよく分からない。", "今もはっきりわからない。"):
            with self.subTest(text=text):
                source, before = self._source_plan(text)
                target = next(n for n in before.nuclei if "memo" in n.source_fields)
                self.assertEqual((target.kind, target.semantic_frame.predicate_kind), ("state", "state"))
                nuclei, dependencies = observation_plan_owner._final_stage1_typed_nuclei(
                    before, source.evidence_spans,
                    normalized_input=source.normalized_current_input,
                )
                self.assertEqual(dependencies, ())
                self.assertEqual(nuclei, tuple(
                    replace(n, kind="uncertainty", semantic_frame=replace(
                        n.semantic_frame, predicate_kind="uncertainty",
                    )) if n.nucleus_id == target.nucleus_id else n
                    for n in before.nuclei
                ))
                for normalized in (None, {**source.normalized_current_input, "memo": "別の文"}):
                    untouched, _ = observation_plan_owner._final_stage1_typed_nuclei(
                        before, source.evidence_spans, normalized_input=normalized,
                    )
                    self.assertEqual(untouched, before.nuclei)

    def test_cognitive_unknown_does_not_inherit_omitted_owner_or_host(self):
        source, before = self._source_plan("まだよく分からない。")
        raw = source.normalized_current_input["memo"].rstrip("。")
        for left, right in (("弟は、", "。"), ("「", "」と聞いた。"),
                            ("", "と思った。"), ("", "なら待つ。"),
                            ("", "とは言えない。"), ("", "？")):
            with self.subTest(left=left, right=right):
                spans = tuple(replace(s, start_index=s.start_index + len(left),
                                      end_index=s.end_index + len(left))
                              if s.source_field == "memo" else s
                              for s in source.evidence_spans)
                untouched, _ = observation_plan_owner._final_stage1_typed_nuclei(
                    before, spans, normalized_input={
                        **source.normalized_current_input, "memo": left + raw + right,
                    },
                )
                self.assertEqual(untouched, before.nuclei)
        for text in ("まだ弟は分からない。", "まだ体が動かない。",
                     "まだ分からなかった。", "まだ分からないとは言えない。",
                     "まだよく分からない？"):
            with self.subTest(text=text):
                candidate_source, plan = self._source_plan(text)
                nuclei, _ = observation_plan_owner._final_stage1_typed_nuclei(
                    plan, candidate_source.evidence_spans,
                    normalized_input=candidate_source.normalized_current_input,
                )
                self.assertFalse(any(n.kind == "uncertainty" for n in nuclei))

    def test_cognitive_unknown_selected_openness_reaches_body_and_inverse(self):
        artifacts = _full_surface_artifacts({
            "case_id": "finite-cognitive-unknown-expression-unit",
            "input": {"thought_text": "まだよく分からない。", "action_text": "",
                      "categories": ["生活"],
                      "emotions": [{"type": "不安", "strength": "weak"}]},
        })
        self.assertTrue(artifacts.gate.passed)
        self.assertTrue(artifacts.inverse.passed)
        self.assertEqual(len(artifacts.selected_subjective_input.decisions), 1)
        decision = artifacts.selected_subjective_input.decisions[0]
        self.assertEqual(decision.subjective_proposition.appraisal_content.operation, "LEAVE_UNFINISHED")
        follow = _reception_text(artifacts.surface.text)
        self.assertTrue(follow.lstrip().startswith("結論を急がずに、"))
        altered = _tamper_reception(artifacts.surface.text, "結論を急がずに、", "")
        inverse = evaluate_grounded_surface_body_inverse(
            body=altered.encode("utf-8"), plan=artifacts.plan,
            sentence_plan=artifacts.sentence_plan, resolver=artifacts.resolver,
            selected_subjective_input=artifacts.selected_subjective_input,
        )
        self.assertFalse(inverse.passed)

    def test_why_question_preserves_owner_and_source_before_meaning_selection(self):
        for prefix in ("どうして", "なぜ", "何故"):
            with self.subTest(prefix=prefix):
                source, before = self._source_plan(
                    prefix + "決めた後に迷う気がするんだろう。"
                )
                nuclei, dependencies = observation_plan_owner._final_stage1_typed_nuclei(
                    before, source.evidence_spans,
                    normalized_input=source.normalized_current_input,
                )
                target = next(n for n in before.nuclei if "memo" in n.source_fields)
                self.assertEqual(target.kind, "action")
                self.assertEqual(dependencies, ())
                self.assertEqual(nuclei, tuple(
                    replace(n, kind="uncertainty", semantic_frame=replace(
                        n.semantic_frame, predicate_kind="uncertainty",
                    )) if n.nucleus_id == target.nucleus_id else n
                    for n in before.nuclei
                ))
                unproven, _ = observation_plan_owner._final_stage1_typed_nuclei(
                    before, source.evidence_spans,
                )
                self.assertEqual(unproven, before.nuclei)
                mismatch, _ = observation_plan_owner._final_stage1_typed_nuclei(
                    before, source.evidence_spans,
                    normalized_input={**source.normalized_current_input, "memo": "別の文"},
                )
                self.assertEqual(mismatch, before.nuclei)
                # The same visible fragment cannot discard a subject,
                # quotation, or reporting host outside its Ledger span.
                original = source.normalized_current_input["memo"]
                for left, right in (("同僚は、", ""), ("「", "」と聞いた。"),
                                    ("", "と思った。")):
                    raw = original.rstrip("。")
                    spans = tuple(
                        replace(s, start_index=s.start_index + len(left),
                                end_index=s.end_index + len(left))
                        if s.source_field == "memo" else s
                        for s in source.evidence_spans
                    )
                    bounded, _ = observation_plan_owner._final_stage1_typed_nuclei(
                        before, spans, normalized_input={
                            **source.normalized_current_input,
                            "memo": left + raw + right,
                        },
                    )
                    self.assertEqual(bounded, before.nuclei)

    def test_postposed_why_question_preserves_same_nucleus_and_source(self):
        for reason in ("なぜ", "何故", "どうして"):
            for text, source_kind in (
                (f"昨日より楽になったのは{reason}だろう。", "change"),
                (f"片付いたのに、気分が重くなったのは{reason}だろうか。", "change"),
                (f"記録したのは{reason}だろう。", "action"),
            ):
                with self.subTest(text=text):
                    source, before = self._source_plan(text)
                    target = next(n for n in before.nuclei if "memo" in n.source_fields)
                    self.assertEqual(target.kind, source_kind)
                    nuclei, dependencies = observation_plan_owner._final_stage1_typed_nuclei(
                        before, source.evidence_spans,
                        normalized_input=source.normalized_current_input,
                    )
                    self.assertEqual(dependencies, ())
                    self.assertEqual(nuclei, tuple(
                        replace(n, kind="uncertainty", semantic_frame=replace(
                            n.semantic_frame, predicate_kind="uncertainty",
                            modality="uncertain",
                            attribute_codes=tuple(dict.fromkeys((
                                *n.semantic_frame.attribute_codes, "operator:uncertainty",
                            ))),
                        )) if n.nucleus_id == target.nucleus_id else n
                        for n in before.nuclei
                    ))
                    for normalized in (None, {
                        **source.normalized_current_input, "memo": "原文と異なる文",
                    }):
                        untouched, _ = observation_plan_owner._final_stage1_typed_nuclei(
                            before, source.evidence_spans, normalized_input=normalized,
                        )
                        self.assertEqual(untouched, before.nuclei)

    def test_postposed_why_rejects_report_quote_fragment_and_parallel_assertion(self):
        for text in (
            "昨日より楽になった。",
            "昨日より楽になったのはなぜだろうと思った。",
            "「昨日より楽になったのはなぜだろう」と聞いた。",
            "昨日より楽になったのはなぜだろうかと尋ねた。",
            "記録した、寝るのはなぜだろう。",
            "記録した,寝るのはなぜだろう。",
        ):
            with self.subTest(text=text):
                source, before = self._source_plan(text)
                nuclei, _ = observation_plan_owner._final_stage1_typed_nuclei(
                    before, source.evidence_spans,
                    normalized_input=source.normalized_current_input,
                )
                self.assertFalse(any(n.kind == "uncertainty" for n in nuclei))
        source, before = self._source_plan("昨日より楽になったのはなぜだろう。")
        raw = source.normalized_current_input["memo"].rstrip("。")
        for left, right in (("同僚は、", "。"), ("「", "」と聞いた。"),
                            ("", "と思った。")):
            spans = tuple(
                replace(s, start_index=s.start_index + len(left),
                        end_index=s.end_index + len(left))
                if s.source_field == "memo" else s for s in source.evidence_spans
            )
            nuclei, _ = observation_plan_owner._final_stage1_typed_nuclei(
                before, spans, normalized_input={
                    **source.normalized_current_input, "memo": left + raw + right,
                },
            )
            self.assertEqual(nuclei, before.nuclei)

    def test_postposed_question_selected_openness_reaches_body_and_inverse(self):
        artifacts = _full_surface_artifacts({
            "case_id": "postposed-question-expression-unit",
            "input": {"thought_text": "昨日より楽になったのはなぜだろう。",
                      "action_text": "", "categories": ["生活"],
                      "emotions": [{"type": "喜び", "strength": "weak"}]},
        })
        self.assertTrue(artifacts.gate.passed)
        self.assertTrue(artifacts.inverse.passed)
        self.assertIn("まだ分からない範囲", artifacts.surface.text)
        self.assertTrue(any(
            d.subjective_proposition.appraisal_content is not None
            and d.subjective_proposition.appraisal_content.operation == "LEAVE_UNFINISHED"
            for d in artifacts.selected_subjective_input.decisions
        ))
        self.assertTrue(_reception_text(artifacts.surface.text).lstrip().startswith("結論を急がずに、"))
        self.assertNotIn("を、結論を", _reception_text(artifacts.surface.text))
        changed = _tamper_reception(artifacts.surface.text, "結論を急がずに、", "")
        inverse = evaluate_grounded_surface_body_inverse(
            body=changed.encode("utf-8"), plan=artifacts.plan,
            sentence_plan=artifacts.sentence_plan, resolver=artifacts.resolver,
            selected_subjective_input=artifacts.selected_subjective_input,
        )
        self.assertFalse(inverse.passed)

    def test_report_quote_and_nonquestion_do_not_acquire_question_kind(self):
        for text in (
            "決めた後に迷う気がする。",
            "なぜ決めた後に迷う気がするんだろうと思った。",
            "「なぜ決めた後に迷う気がするんだろう」と聞いた。",
            "なぜ決めた後に迷う気がするんだろうかと尋ねた。",
        ):
            with self.subTest(text=text):
                source, plan = self._source_plan(text)
                nuclei, _ = observation_plan_owner._final_stage1_typed_nuclei(
                    plan, source.evidence_spans,
                    normalized_input=source.normalized_current_input,
                )
                self.assertFalse(any(n.kind == "uncertainty" for n in nuclei))

    def test_selected_unfinished_appraisal_reaches_body_and_inverse(self):
        artifacts = _full_surface_artifacts({
            "case_id": "unresolved-question-expression-unit",
            "input": {"thought_text": "なぜ決めた後に迷う気がするんだろう。",
                      "action_text": "", "categories": ["生活"],
                      "emotions": [{"type": "不安", "strength": "weak"}]},
        })
        self.assertTrue(artifacts.gate.passed)
        self.assertTrue(artifacts.inverse.passed)
        self.assertNotIn("確かめきれない行動", artifacts.surface.text)
        self.assertTrue(any(
            d.subjective_proposition.appraisal_content is not None
            and d.subjective_proposition.appraisal_content.operation == "LEAVE_UNFINISHED"
            for d in artifacts.selected_subjective_input.decisions
        ))
        follow = _reception_text(artifacts.surface.text)
        self.assertTrue(follow.lstrip().startswith("結論を急がずに、"))
        self.assertNotIn("を結論を", follow)
        changed = _tamper_reception(artifacts.surface.text, "結論を急がずに、", "")
        inverse = evaluate_grounded_surface_body_inverse(
            body=changed.encode("utf-8"), plan=artifacts.plan,
            sentence_plan=artifacts.sentence_plan, resolver=artifacts.resolver,
            selected_subjective_input=artifacts.selected_subjective_input,
        )
        self.assertFalse(inverse.passed)

    def test_openness_scope_preserves_object_act_and_clause_inflection(self):
        calls = []
        author = reception_owner._source_grounded_response_predicate_surface

        def capture(*args, **kwargs):
            calls.append((args, kwargs))
            return author(*args, **kwargs)

        with patch.object(reception_owner, "_source_grounded_response_predicate_surface",
                          side_effect=capture):
            artifacts = _full_surface_artifacts({
                "case_id": "openness-clause-scope-unit",
                "input": {"thought_text": "なぜ決めた後に迷う気がするんだろう。",
                          "action_text": "", "categories": ["生活"],
                          "emotions": [{"type": "不安", "strength": "weak"}]},
            })
        self.assertTrue(artifacts.inverse.passed)
        self.assertTrue(calls)
        args, kwargs = next((args, kwargs) for args, kwargs in calls
                            if kwargs["recovery_stage"] == "full")
        for role, connection in (("attention", "に目が留まり、"),
                                 ("significance", "を見失わず、"),
                                 ("felt_response", "を")):
            for form, ending in (("FINITE", "受け止めています"),
                                 ("CONTINUATIVE", "受け止めていて")):
                with self.subTest(role=role, form=form):
                    text = author(args[0], role, **{**kwargs, "clause_form": form})
                    self.assertTrue(text.startswith("結論を急がずに、" + kwargs["object_core"] + connection))
                    self.assertEqual(text.count("結論を急がずに、"), 1)
                    self.assertTrue(text.endswith("小さくせずに" + ending))


class CMEEFinalSinglePerformedActionReferenceTest(unittest.TestCase):
    @staticmethod
    def _row(text):
        return {"case_id": "public-single-performed-action", "input": {
            "thought_text": "", "action_text": text, "categories": ["生活"],
            "emotions": [{"type": "不安", "strength": "weak"}],
        }}

    @classmethod
    def setUpClass(cls):
        cls.artifacts = tuple((text, _full_surface_artifacts(cls._row(text))) for text in (
            "資料を整理した。", "資料を整理している。",
            "会議で受け取った資料を種類ごとに整理した。",
        ))

    def test_complete_selected_action_reaches_reception_without_a_quote(self):
        for text, a in self.artifacts:
            with self.subTest(text=text):
                self.assertTrue(a.gate.passed, a.gate.rejection_reasons)
                self.assertTrue(a.inverse.passed, a.inverse.failure_codes)
                self.assertEqual(a.sentence_plan.recovery_stage, "full")
                rp = a.plan.response_plan.human_reception_plan
                move, = rp.moves
                self.assertTrue(move.required)
                self.assertEqual(move.reception_act, "honor_concrete_effort")
                self.assertEqual(move.target_nucleus_ids, a.plan.response_plan.primary_nucleus_ids)
                self.assertEqual(move.support_nucleus_ids, ())
                self.assertEqual(move.reference_mode, "short_anchor_if_ambiguous")
                self.assertEqual(rp.reference_mode, move.reference_mode)
                # Preserve the registered reference-policy mapping, including
                # the quote budget. The final author still emits no quotes.
                self.assertEqual((rp.quote_policy.max_anchor_count,
                                  rp.quote_policy.max_anchor_visible_chars), (1, 16))
                follow = _reception_text(a.surface.text)
                self.assertEqual(follow.count(text.rstrip("。") + "こと"), 1)
                self.assertNotIn("実際の行動", follow)
                self.assertNotIn("「", follow)
                self.assertNotIn("『", follow)
                for stage in ("integrated", "hedged", "minimal_grounded"):
                    self.assertEqual(reception_owner.reception_effective_move_reference_mode(
                        rp, move, stage), "anaphoric_first")

    def test_inverse_rejects_changed_action_time_owner_and_quoted_or_repeated_target(self):
        text, a = self.artifacts[0]
        nominal = text.rstrip("。") + "こと"
        for wrong in ("実際の行動", "資料を整理すること", "資料を整理しなかったこと",
                      "別の資料を整理したこと", "同僚が資料を整理したこと",
                      "「" + nominal + "」", nominal + "と" + nominal):
            with self.subTest(wrong=wrong):
                body = _tamper_reception(a.surface.text, nominal, wrong)
                self.assertFalse(evaluate_grounded_surface_body_inverse(
                    body=body.encode("utf-8"), plan=a.plan, sentence_plan=a.sentence_plan,
                    resolver=a.resolver, selected_subjective_input=a.selected_subjective_input,
                ).passed)
                self.assertFalse(evaluate_grounded_observation_gate(
                    plan=a.plan, sentence_plan=a.sentence_plan,
                    surface_result=replace(a.surface, text=body), resolver=a.resolver,
                    require_body_inverse=True, selected_subjective_input=a.selected_subjective_input,
                ).passed)

    def test_legacy_and_unproven_performance_keep_their_reference_policy(self):
        text, _a = self.artifacts[0]
        inputs = _compile_inputs(self._row(text))
        base = build_grounded_observation_plan(
            inputs.source.normalized_current_input, evidence_spans=inputs.source.evidence_spans,
        )
        self.assertEqual(base.response_plan.human_reception_plan.reference_mode, "anaphoric_first")
        for text in ("明日、資料を整理する。", "資料を整理した？", "資料を整理しなかった。"):
            with self.subTest(text=text):
                p = _compile_inputs(self._row(text)).grounded_plan
                rp = p.response_plan.human_reception_plan
                self.assertEqual(rp.reference_mode, "anaphoric_first")
                self.assertEqual(rp.quote_policy.max_anchor_count, 0)


class CMEEFinalContinuingWordsReferenceTest(unittest.TestCase):
    @staticmethod
    def _row(text):
        return {"case_id": "public-continuing-words-reference", "input": {
            "thought_text": text, "action_text": "", "categories": ["生活"],
            "emotions": [{"type": "不安", "strength": "weak"}],
        }}

    @classmethod
    def setUpClass(cls):
        cls.artifacts = tuple((text, _full_surface_artifacts(cls._row(text))) for text in (
            "書類が増えて、ずっと落ち着かない。", "ずっと落ち着かない。",
        ))

    def test_complete_continuing_words_survive_final_reference_rebuild(self):
        for text, a in self.artifacts:
            with self.subTest(text=text):
                self.assertTrue(a.gate.passed, a.gate.rejection_reasons)
                self.assertTrue(a.inverse.passed, a.inverse.failure_codes)
                self.assertEqual(a.sentence_plan.recovery_stage, "full")
                rp = a.plan.response_plan.human_reception_plan
                move, = rp.moves
                self.assertTrue(move.required)
                self.assertEqual(move.reception_act, "stay_with_current_burden")
                self.assertEqual(move.target_nucleus_ids, a.plan.response_plan.primary_nucleus_ids)
                self.assertEqual(move.support_nucleus_ids, ())
                self.assertEqual((rp.reference_mode, move.reference_mode),
                                 ("short_anchor_if_ambiguous",) * 2)
                self.assertEqual((rp.quote_policy.max_anchor_count,
                                  rp.quote_policy.max_anchor_visible_chars), (1, 16))
                follow = _reception_text(a.surface.text)
                self.assertEqual(follow.count(text.rstrip("。") + "という言葉"), 1)
                self.assertNotIn("今ここに置かれた言葉", follow)
                self.assertNotIn("「", follow)
                self.assertTrue(all(kw["selected_subjective_input"] is a.selected_subjective_input
                                    for _args, kw in a.author_arguments))

    def test_source_continuation_is_received_once_without_extra_present_adjunct(self):
        for text, a in self.artifacts:
            with self.subTest(text=text):
                follow = _reception_text(a.surface.text)
                self.assertIn(text.rstrip("。"), follow)
                self.assertNotIn("今も、", follow)
                self.assertEqual(follow.count("ずっと"), 1)
                self.assertTrue(a.gate.passed, a.gate.rejection_reasons)
                self.assertTrue(a.inverse.passed, a.inverse.failure_codes)
                for authored in a.authored:
                    sentence_plan = a.sentence_plan if authored.recovery_stage == "full" else (
                        surface_owner.build_reception_recovery_sentence_plan(
                            a.sentence_plan, a.plan, a.resolver, recovery_stage=authored.recovery_stage,
                        )
                    )
                    surface = _recovery_surface(a, sentence_plan)
                    inverse = evaluate_grounded_surface_body_inverse(
                        body=surface.text.encode("utf-8"), plan=a.plan,
                        sentence_plan=sentence_plan, resolver=a.resolver,
                        selected_subjective_input=a.selected_subjective_input,
                    )
                    self.assertTrue(inverse.passed, inverse.failure_codes)

    def test_body_inverse_rejects_added_time_or_removed_continuation(self):
        for text, a in self.artifacts:
            follow = _reception_text(a.surface.text)
            for wrong in ("今も、" + follow, follow.replace("ずっと", "")):
                with self.subTest(text=text, wrong=wrong):
                    body = _tamper_reception(a.surface.text, follow, wrong)
                    self.assertFalse(evaluate_grounded_surface_body_inverse(
                        body=body.encode("utf-8"), plan=a.plan, sentence_plan=a.sentence_plan,
                        resolver=a.resolver, selected_subjective_input=a.selected_subjective_input,
                    ).passed)

    def test_continuation_marker_cannot_borrow_another_time_clause_or_quotation(self):
        realization = SimpleNamespace(time_scope="continuing", aspect="unknown", reference_mode="EXPLICIT")
        for source in (
            "ずっと前は落ち着かなかった", "ずっと先が怖い", "ずっと少ない",
            "ずっと落ち着かなかった", "ずっと落ち着かないと思う",
            "ずっと落ち着かないと友人は言う", "ずっと落ち着かない？",
            "「ずっと落ち着かない」", "ずっと待って、落ち着かない",
            "昨日より、ずっとつらい", "前の方法より、ずっと分かりやすい",
            "前の方法と比べると、ずっと良い",
        ):
            with self.subTest(source=source):
                time, _aspect, adjunct, _aspect_adjunct = reception_owner._source_grounded_temporal_aspect_realization(
                    realization, source,
                )
                self.assertEqual((time, adjunct), ("ADJUNCT", "今も、"))
        for mode in ("past", "future", "present_to_future"):
            other = SimpleNamespace(time_scope=mode, aspect="unknown", reference_mode="EXPLICIT")
            before = reception_owner._source_grounded_temporal_aspect_realization(other, "落ち着かない")
            after = reception_owner._source_grounded_temporal_aspect_realization(other, "ずっと落ち着かない")
            self.assertEqual(after, before)

    def test_inverse_rejects_lost_background_continuation_and_changed_attribution(self):
        text, a = self.artifacts[0]
        nominal = text.rstrip("。") + "という言葉"
        for wrong in (
            "ずっと落ち着かないという言葉", "書類が増えて、落ち着かないという言葉",
            "書類が増えて、ずっと落ち着いているという言葉",
            "友人は書類が増えて、ずっと落ち着かないという言葉",
            "書類が増えて、ずっと落ち着かないこと", "今ここに置かれた言葉",
            nominal + "と" + nominal, "「" + nominal + "」",
        ):
            with self.subTest(wrong=wrong):
                body = _tamper_reception(a.surface.text, nominal, wrong)
                self.assertFalse(evaluate_grounded_surface_body_inverse(
                    body=body.encode("utf-8"), plan=a.plan, sentence_plan=a.sentence_plan,
                    resolver=a.resolver, selected_subjective_input=a.selected_subjective_input,
                ).passed)
                self.assertFalse(evaluate_grounded_observation_gate(
                    plan=a.plan, sentence_plan=a.sentence_plan,
                    surface_result=replace(a.surface, text=body), resolver=a.resolver,
                    require_body_inverse=True, selected_subjective_input=a.selected_subjective_input,
                ).passed)

    def test_existing_nominals_and_legacy_scope_remain_and_attributed_words_stay_whole(self):
        for text, expected in (("なんとなく落ち着かない。", "なんとなくの落ち着かなさ"),
                               ("ずっと不安が残っている。", "ずっと残っている不安")):
            with self.subTest(text=text):
                a = _full_surface_artifacts(self._row(text))
                self.assertEqual(a.plan.response_plan.human_reception_plan.reference_mode,
                                 "anaphoric_first")
                self.assertIn(expected, _reception_text(a.surface.text))
                self.assertTrue(a.inverse.passed, a.inverse.failure_codes)
        for text in ("昨日はずっと落ち着かなかった。", "ずっと落ち着かないかもしれない。",
                     "明日もずっと落ち着かない気がする。", "ずっと胸がざわつく。"):
            with self.subTest(text=text):
                plan = _compile_inputs(self._row(text)).grounded_plan
                self.assertEqual(plan.response_plan.human_reception_plan.reference_mode,
                                 "anaphoric_first")
        text, _a = self.artifacts[0]
        inputs = _compile_inputs(self._row(text))
        legacy = build_grounded_observation_plan(
            inputs.source.normalized_current_input, evidence_spans=inputs.source.evidence_spans)
        self.assertEqual(legacy.response_plan.human_reception_plan.reference_mode, "anaphoric_first")
        # This reference policy does not repair or endorse the upstream actor
        # default. Refer to every attributed word without making it SELF's feeling.
        text = "友人はずっと落ち着かない。"
        a = _full_surface_artifacts(self._row(text))
        self.assertIn(text.rstrip("。") + "という言葉", _reception_text(a.surface.text))
        self.assertTrue(a.inverse.passed, a.inverse.failure_codes)
        body = _tamper_reception(a.surface.text, "友人はずっと", "ずっと")
        self.assertFalse(evaluate_grounded_surface_body_inverse(
            body=body.encode("utf-8"), plan=a.plan, sentence_plan=a.sentence_plan,
            resolver=a.resolver, selected_subjective_input=a.selected_subjective_input,
        ).passed)

    def test_recovery_keeps_same_required_duty_and_source_observation(self):
        for text, a in self.artifacts:
            rp = a.plan.response_plan.human_reception_plan
            move, = rp.moves
            for stage in ("optional_removed", "integrated", "hedged"):
                with self.subTest(text=text, stage=stage):
                    sentence_plan = surface_owner.build_reception_recovery_sentence_plan(
                        a.sentence_plan, a.plan, a.resolver, recovery_stage=stage)
                    surface = _recovery_surface(a, sentence_plan)
                    self.assertEqual(reception_owner.reception_active_moves(rp, stage), (move,))
                    self.assertIn(text.rstrip("。"), surface.text.partition(
                        surface_owner.RECEPTION_SECTION_LABEL)[0])
                    self.assertTrue(evaluate_grounded_surface_body_inverse(
                        body=surface.text.encode("utf-8"), plan=a.plan, sentence_plan=sentence_plan,
                        resolver=a.resolver, selected_subjective_input=a.selected_subjective_input,
                    ).passed)
                    if stage in {"integrated", "hedged"}:
                        self.assertEqual(reception_owner.reception_effective_move_reference_mode(
                            rp, move, stage), "anaphoric_first")


class CMEECompoundPastReportedWishTest(unittest.TestCase):
    @staticmethod
    def _row(text):
        return {"case_id": "public-compound-past-wish", "input": {
            "thought_text": text, "action_text": "", "categories": ["生活"],
            "emotions": [{"type": "不安", "strength": "weak"}],
        }}

    def test_first_reported_wish_reaches_relation_body_and_past_qualifier(self):
        for prefix, link in (("", "が"), ("", "けれど"), ("私は", "が")):
            with self.subTest(prefix=prefix, link=link):
                report = prefix + "生活を変えたいと思った"
                a = _full_surface_artifacts(self._row(report + link + "、難しい。"))
                self.assertTrue(a.gate.passed, a.gate.rejection_reasons)
                self.assertTrue(a.inverse.passed, a.inverse.failure_codes)
                self.assertEqual(a.sentence_plan.recovery_stage, "full")
                left, right = a.plan.nuclei[:2]
                self.assertEqual((left.kind, left.semantic_frame.modality,
                                  left.semantic_frame.time_scope), ("wish", "wish", "past"))
                self.assertEqual(right.kind, "constraint")
                relation, = a.plan.relations
                self.assertEqual((relation.type, relation.from_nucleus_id, relation.to_nucleus_id),
                                 ("wish_and_constraint", left.nucleus_id, right.nucleus_id))
                self.assertEqual(_reception_text(a.surface.text).strip(),
                                 report + "ことと難しいことの両方を見失わず、大切に受け止めています。")
                self.assertTrue(any(q.time_scope == "past"
                                    for d in a.selected_subjective_input.decisions for q in d.qualifier_rows))
                self.assertTrue(all(kw["selected_subjective_input"] is a.selected_subjective_input
                                    for _args, kw in a.author_arguments))

    def test_inverse_rejects_present_desire_and_performed_action_substitution(self):
        a = _full_surface_artifacts(self._row("生活を変えたいと思ったが、難しい。"))
        for replacement in ("生活を変えたいと思っていること", "今も残る願い", "生活を変えたこと"):
            with self.subTest(replacement=replacement):
                body = _tamper_reception(a.surface.text, "生活を変えたいと思ったこと", replacement)
                self.assertFalse(evaluate_grounded_surface_body_inverse(
                    body=body.encode("utf-8"), plan=a.plan, sentence_plan=a.sentence_plan,
                    resolver=a.resolver, selected_subjective_input=a.selected_subjective_input,
                ).passed)

    def test_new_past_license_requires_unique_first_report_and_original_field(self):
        # These forms retain their existing paths; this test does not call
        # those paths a product pass or endorse their remaining wish labels.
        for text in (
            "生活を変えたいと思ったが、難しい？",
            "生活を変えたいと思ったが、今は難しい。",
            "難しいが、生活を変えたいと思った。",
            "生活を変えたいと思ったが、生活を変えたいと思った。",
            "友人は生活を変えたいと思ったが、難しい。",
            "「生活を変えたいと思った」が、難しい。",
            "生活を変えたいと思ったかもしれないが、難しい。",
            "生活を変えたいと思わなかったが、難しい。",
            "生活を変えたいと思ったが、難しい。と友人が話した。",
            "生活を変えたいと思ったが、難しい…",
        ):
            with self.subTest(text=text):
                plan = _compile_inputs(self._row(text)).grounded_plan
                self.assertFalse(any(n.kind == "wish" and n.semantic_frame.time_scope == "past"
                                     for n in plan.nuclei))
        inputs = _compile_inputs(self._row("生活を変えたいと思ったが、難しい。"))
        span = inputs.source.evidence_spans[0]
        frame = inputs.grounded_plan.nuclei[0].semantic_frame
        for normalized in (None, {"memo": "生活を変えたいと思ったが、難しい？"},
                           {"memo": "生活を変えたいと思ったが、難しい。と聞いた。"}):
            projections = observation_plan_owner._typed_nucleus_projections_for_span(
                span, base_frame=frame, normalized_input=normalized,
            )
            self.assertTrue(projections)
            self.assertEqual(projections[0].kind, "uncertainty")

    def test_cancelled_constraint_keeps_neutral_split_and_complete_body(self):
        for link in ("が", "けれど"):
            with self.subTest(link=link):
                # Ledger retains the fullwidth dot; the relation owner
                # trims it. Cancellation must use that same finite range.
                for ending in ("。", "．"):
                    plan = _compile_inputs(self._row(
                        "生活を変えたいと思った" + link + "、難しくない" + ending,
                    )).grounded_plan
                    self.assertEqual(tuple(n.kind for n in plan.nuclei[:2]), ("uncertainty", "state"))
                    self.assertEqual(tuple(r.type for r in plan.relations), ("contrast",))
                a = _full_surface_artifacts(self._row("生活を変えたいと思った" + link + "、難しくない。"))
                self.assertEqual(tuple(n.kind for n in a.plan.nuclei[:2]), ("uncertainty", "state"))
                self.assertEqual(tuple(r.type for r in a.plan.relations), ("contrast",))
                self.assertTrue(a.gate.passed, a.gate.rejection_reasons)
                self.assertTrue(a.inverse.passed, a.inverse.failure_codes)
                self.assertIn("難しくないこと", _reception_text(a.surface.text))


class CMEEFinalNegatedPastWishReportTest(unittest.TestCase):
    @staticmethod
    def _row(text):
        return {"case_id": "public-negated-past-report", "input": {
            "thought_text": text, "action_text": "", "categories": ["生活"],
            "emotions": [{"type": "不安", "strength": "weak"}],
        }}

    @classmethod
    def setUpClass(cls):
        cls.artifacts = tuple((report, _full_surface_artifacts(cls._row(report + "が、難しい。")))
                              for report in (
            "生活を変えたいと思わなかった", "生活を変えたいとは思わなかった",
            "生活を変えたいと思いませんでした", "生活を変えたいと思っていなかった",
            "生活を変えたいと思ってなかった", "生活を変えたいと思っていませんでした",
            "私は生活を変えたいと思わなかった",
        ))

    def test_denied_report_keeps_past_negative_state_and_complete_contrast(self):
        for report, a in self.artifacts:
            with self.subTest(report=report):
                left, right = a.plan.nuclei[:2]
                self.assertEqual((left.kind, left.semantic_frame.predicate_kind,
                                  left.semantic_frame.polarity, left.semantic_frame.modality,
                                  left.semantic_frame.time_scope),
                                 ("state", "state", "negative", "fact", "past"))
                self.assertNotIn("operator:wish", left.semantic_frame.attribute_codes)
                self.assertEqual(right.kind, "constraint")
                self.assertEqual(tuple(r.type for r in a.plan.relations), ("contrast",))
                self.assertTrue(a.gate.passed, a.gate.rejection_reasons)
                self.assertTrue(a.inverse.passed, a.inverse.failure_codes)
                self.assertEqual(a.sentence_plan.recovery_stage, "full")
                follow = _reception_text(a.surface.text)
                self.assertIn(report + "こと", follow)
                self.assertIn("難しい", follow)
                self.assertNotIn("願い", follow)
                self.assertEqual({s.recovery_stage for s in a.authored},
                                 {"full", "optional_removed", "integrated", "hedged"})

    def test_inverse_rejects_negation_loss_current_wish_and_performed_action(self):
        report, a = self.artifacts[0]
        for replacement in ("生活を変えたいと思った", "生活を変えたいと思っている",
                            "生活を変えたいという願い", "生活を変えた"):
            with self.subTest(replacement=replacement):
                body = _tamper_reception(a.surface.text, report, replacement)
                self.assertFalse(evaluate_grounded_surface_body_inverse(
                    body=body.encode("utf-8"), plan=a.plan, sentence_plan=a.sentence_plan,
                    resolver=a.resolver, selected_subjective_input=a.selected_subjective_input,
                ).passed)

    def test_report_proof_requires_first_unique_self_clause_and_original_field(self):
        # Excluded forms keep their prior paths; this does not endorse their
        # existing labels or claim product acceptance for those paths.
        for text in (
            "生活を変えたいと思わなかったが、難しい？",
            "生活を変えたいと思わなかったが、今は難しい。",
            "難しいが、生活を変えたいと思わなかった。",
            "生活を変えたいと思わなかったが、生活を変えたいと思わなかった。",
            "友人は生活を変えたいと思わなかったが、難しい。",
            "「生活を変えたいと思わなかった」が、難しい。",
            "私は多分生活を変えたいと思わなかったが、難しい。",
            "生活を変えたいと思ったので出かけたいと思わなかったが、難しい。",
            "生活を変えたいと思わなかったかもしれないが、難しい。",
            "生活を変えたいと思わなかったが、難しい。と友人が話した。",
            "生活を変えたいと思わなかったが、難しい…",
        ):
            with self.subTest(text=text):
                plan = _compile_inputs(self._row(text)).grounded_plan
                self.assertFalse(any(n.kind == "state" and n.semantic_frame.polarity == "negative"
                                     and n.semantic_frame.time_scope == "past" for n in plan.nuclei))
        # A standalone report now resolves in the same-nucleus final status
        # owner. It must still never manufacture a singleton compound split.
        standalone = _compile_inputs(self._row("生活を変えたいと思わなかった。"))
        self.assertEqual(observation_plan_owner._typed_nucleus_projections_for_span(
            standalone.source.evidence_spans[0],
            base_frame=standalone.grounded_plan.nuclei[0].semantic_frame,
            normalized_input=standalone.source.normalized_current_input,
        ), ())
        inputs = _compile_inputs(self._row("生活を変えたいと思わなかったが、難しい。"))
        span = inputs.source.evidence_spans[0]
        for normalized in (None, {"memo": "生活を変えたいと思わなかったが、難しい？"},
                           {"memo": "生活を変えたいと思わなかったが、難しい。と聞いた。"}):
            projections = observation_plan_owner._typed_nucleus_projections_for_span(
                span, base_frame=inputs.grounded_plan.nuclei[0].semantic_frame,
                normalized_input=normalized,
            )
            self.assertFalse(any(p.kind == "state" and p.time_scope == "past" for p in projections))
        for ending in ("。", "．"):
            a = _full_surface_artifacts(self._row("生活を変えたいと思わなかったが、難しくない" + ending))
            self.assertEqual(tuple(n.kind for n in a.plan.nuclei[:2]), ("state", "state"))
            self.assertTrue(a.gate.passed, a.gate.rejection_reasons)
            self.assertTrue(a.inverse.passed, a.inverse.failure_codes)
            self.assertIn("難しくないこと", _reception_text(a.surface.text))

    def test_minimal_admission_preserves_required_support_and_single_source_contract(self):
        _report, a = self.artifacts[0]
        rp = a.plan.response_plan.human_reception_plan
        move, = rp.moves
        self.assertTrue(move.required)
        self.assertTrue(move.support_nucleus_ids)
        with self.assertRaisesRegex(surface_owner.GroundedSentenceSurfaceError,
                                    "human_reception_minimal_grounded_not_allowed"):
            surface_owner.build_reception_recovery_sentence_plan(
                a.sentence_plan, a.plan, a.resolver, recovery_stage="minimal_grounded")
        for stage in ("full", "optional_removed", "integrated", "hedged"):
            self.assertEqual(reception_owner.reception_active_moves(rp, stage), (move,))
        single = replace(move, support_nucleus_ids=())
        single_plan = replace(rp, moves=(single,))
        self.assertEqual(reception_owner.reception_active_moves(single_plan, "minimal_grounded"), (single,))
        for evidence in ((), (*single.source_evidence_span_ids, "other-span")):
            with self.assertRaisesRegex(reception_owner.GroundedHumanReceptionSurfaceError,
                                        "human_reception_minimal_grounded_not_allowed"):
                reception_owner.reception_active_moves(
                    replace(single_plan, moves=(replace(single, source_evidence_span_ids=evidence),)),
                    "minimal_grounded")


class CMEEFinalStandaloneDeniedPastReportTest(unittest.TestCase):
    _row = staticmethod(CMEEFinalNegatedPastWishReportTest._row)

    @classmethod
    def setUpClass(cls):
        cls.artifacts = tuple((text, _full_surface_artifacts(cls._row(text))) for text in (
            "生活を変えたいと思わなかった。", "生活を変えたいとは思わなかった。",
            "生活を変えたいと思いませんでした。", "生活を変えたいと思っていなかった。",
            "生活を変えたいと思ってなかった。", "生活を変えたいと思っていませんでした。",
            "私は生活を変えたいと思わなかった。", "相談したいと思わなかった。",
            "安心したいと思わなかった。",
        ))

    def test_same_source_denial_reaches_completed_body_and_shared_input(self):
        for text, a in self.artifacts:
            with self.subTest(text=text):
                source = freeze_text_source(_request_from_row(self._row(text)))
                base = build_grounded_observation_plan(
                    source.normalized_current_input, evidence_spans=source.evidence_spans)
                before, = (n for n in base.nuclei if n.source_span_ids == (source.evidence_spans[0].span_id,))
                after, = (n for n in a.plan.nuclei if n.nucleus_id == before.nucleus_id)
                self.assertEqual(after, replace(before, kind="state", semantic_frame=after.semantic_frame))
                self.assertEqual((after.semantic_frame.predicate_kind, after.semantic_frame.polarity,
                                  after.semantic_frame.modality, after.semantic_frame.time_scope),
                                 ("state", "negative", "fact", "past"))
                self.assertEqual({c for c in after.semantic_frame.attribute_codes if c.startswith("operator:")},
                                 {"operator:negation"})
                self.assertEqual(tuple(c for c in after.semantic_frame.attribute_codes if c.startswith("lexical:")),
                                 (*tuple(c for c in before.semantic_frame.attribute_codes if c.startswith("lexical:")),
                                  "lexical:source_denied_past_thought_report"))
                self.assertFalse(any(c.startswith(("semantic_role:", "arc_role:"))
                                     for c in after.semantic_frame.attribute_codes))
                self.assertIn(text.rstrip("。．") + "という言葉", _reception_text(a.surface.text))
                self.assertNotIn("願い", _reception_text(a.surface.text))
                self.assertTrue(a.gate.passed, a.gate.rejection_reasons)
                self.assertTrue(a.inverse.passed, a.inverse.failure_codes)
                self.assertTrue(all(kw["selected_subjective_input"] is a.selected_subjective_input
                                    for _args, kw in a.author_arguments))

    def test_completed_body_inverse_rejects_denial_loss_and_performed_action(self):
        text, a = self.artifacts[0]
        report = text.rstrip("。")
        for replacement in ("生活を変えたいと思った", "生活を変えたいと思っている",
                            "生活を変えたいという願い", "生活を変えた"):
            with self.subTest(replacement=replacement):
                body = _tamper_reception(a.surface.text, report, replacement)
                self.assertNotEqual(body, a.surface.text)
                self.assertFalse(evaluate_grounded_surface_body_inverse(
                    body=body.encode("utf-8"), plan=a.plan, sentence_plan=a.sentence_plan,
                    resolver=a.resolver, selected_subjective_input=a.selected_subjective_input,
                ).passed)

        # Layer 2 retaining the full report cannot discharge Layer 1's own
        # negation/host obligation, even if a shorter quote is a substring.
        observation, separator, reception = a.surface.text.partition(surface_owner.RECEPTION_SECTION_LABEL)
        for replacement in ("生活を変えたい", "生活を変えたいと思った", "生活を変えた"):
            with self.subTest(observation_replacement=replacement):
                body = observation.replace(report, replacement) + separator + reception
                self.assertNotEqual(body, a.surface.text)
                inverse = evaluate_grounded_surface_body_inverse(
                    body=body.encode("utf-8"), plan=a.plan, sentence_plan=a.sentence_plan,
                    resolver=a.resolver, selected_subjective_input=a.selected_subjective_input,
                )
                self.assertFalse(inverse.passed)
                self.assertTrue(any(code.startswith("body_inverse_observation_source_anchor_incomplete:")
                                    for code in inverse.failure_codes))
                self.assertFalse(evaluate_grounded_observation_gate(
                    plan=a.plan, sentence_plan=a.sentence_plan, surface_result=replace(a.surface, text=body),
                    resolver=a.resolver, require_body_inverse=True,
                    selected_subjective_input=a.selected_subjective_input,
                ).passed)

    def test_source_owner_and_report_boundaries_remain_unadmitted(self):
        for text in (
            "友人は生活を変えたいと思わなかった。", "弟が生活を変えたいと思わなかった。",
            "友人曰く生活を変えたいと思わなかった。", "友人によると生活を変えたいと思わなかった。",
            "私は友人が生活を変えたいと思わなかった。", "弟の生活を変えたいと思わなかった。",
            "「生活を変えたいと思わなかった」。", "生活を変えたいと思わなかった？",
            "私は多分生活を変えたいと思わなかった。", "生活を変えたいと思わなかったかもしれない。",
            "生活を変えたいとは思わない。", "昨日は生活を変えたいと思わなかった。",
            "生活を変えたいと思いたいと思わなかった。", "生活を変えたいと思わなかった。と友人が話した。",
            "生活を変えたいと思わなかったので、記録した。",
        ):
            with self.subTest(text=text):
                source = freeze_text_source(_request_from_row(self._row(text)))
                base = build_grounded_observation_plan(
                    source.normalized_current_input, evidence_spans=source.evidence_spans)
                # Compare this final owner directly, without endorsing labels
                # or other compound projections already present upstream.
                self.assertEqual(observation_plan_owner._final_stage1_align_action_status(
                    base.nuclei, source.evidence_spans, normalized_input=source.normalized_current_input),
                    base.nuclei)

    def test_original_field_proof_is_required_before_status_alignment(self):
        text, _a = self.artifacts[0]
        source = freeze_text_source(_request_from_row(self._row(text)))
        base = build_grounded_observation_plan(
            source.normalized_current_input, evidence_spans=source.evidence_spans)
        for normalized in (None, {"memo": text + "と聞いた。"}, {"memo": text[:-1] + "？"},
                           {"memo": "友人は" + text}):
            with self.subTest(normalized=normalized):
                self.assertEqual(observation_plan_owner._final_stage1_align_action_status(
                    base.nuclei, source.evidence_spans, normalized_input=normalized), base.nuclei)
        # The original fullwidth ending remains in Ledger. The observation
        # quote must preserve it independently of this finite status proof.
        fullwidth = _compile_inputs(self._row("生活を変えたいと思わなかった．"))
        nucleus = fullwidth.grounded_plan.nuclei[0]
        self.assertEqual((nucleus.kind, nucleus.semantic_frame.polarity,
                          nucleus.semantic_frame.modality, nucleus.semantic_frame.time_scope),
                         ("state", "negative", "fact", "past"))

    def test_fullwidth_report_quotes_keep_the_original_period_and_complete_body(self):
        for standard_text, standard in self.artifacts:
            with self.subTest(standard_text=standard_text):
                report = standard_text.rstrip("。")
                text = report + "．"
                source = freeze_text_source(_request_from_row(self._row(text)))
                a = _full_surface_artifacts(self._row(text))
                self.assertEqual(a.surface.text, standard.surface.text.replace(
                    "「" + report + "」", "「" + text + "」", 1))
                self.assertEqual(a.resolver.resolve("s1"), source.evidence_spans[0])
                self.assertEqual(a.resolver.resolve("s1").raw_text, text)
                self.assertEqual(a.resolver.resolve("s1").end_index, len(text))
                self.assertEqual(tuple(n.semantic_frame for n in a.plan.nuclei),
                                 tuple(n.semantic_frame for n in standard.plan.nuclei))
                self.assertIn(report + "という言葉", _reception_text(a.surface.text))
                self.assertNotIn("願い", _reception_text(a.surface.text))
                self.assertTrue(a.gate.passed, a.gate.rejection_reasons)
                self.assertTrue(a.inverse.passed, a.inverse.failure_codes)

    def test_fullwidth_report_keeps_strict_observation_and_reception_source_checks(self):
        report = "生活を変えたいと思わなかった"
        a = _full_surface_artifacts(self._row(report + "．"))
        observation, separator, reception = a.surface.text.partition(surface_owner.RECEPTION_SECTION_LABEL)
        for body in (
            observation.replace(report, "生活を変えたいと思った") + separator + reception,
            observation.replace("．", "") + separator + reception,
            _tamper_reception(a.surface.text, report, "生活を変えたいと思った"),
        ):
            with self.subTest(body=body):
                self.assertNotEqual(body, a.surface.text)
                self.assertFalse(evaluate_grounded_surface_body_inverse(
                    body=body.encode("utf-8"), plan=a.plan, sentence_plan=a.sentence_plan,
                    resolver=a.resolver, selected_subjective_input=a.selected_subjective_input,
                ).passed)
                self.assertFalse(evaluate_grounded_observation_gate(
                    plan=a.plan, sentence_plan=a.sentence_plan, surface_result=replace(a.surface, text=body),
                    resolver=a.resolver, require_body_inverse=True,
                    selected_subjective_input=a.selected_subjective_input,
                ).passed)

    def test_fullwidth_quote_preservation_requires_the_existing_proof_and_single_ending(self):
        for text in (
            "友人は生活を変えたいと思わなかった．", "「生活を変えたいと思わなかった」．",
            "生活を変えたいと思わなかったかもしれない．", "昨日は生活を変えたいと思わなかった．",
            "生活を変えたいと思わなかった．．", "生活を変えたいと思わなかった．？",
        ):
            with self.subTest(text=text):
                inputs = _compile_inputs(self._row(text))
                nucleus = inputs.grounded_plan.nuclei[0]
                resolver = build_evidence_span_resolver(inputs.source.evidence_spans)
                quotes = surface_owner._quotes_for_nuclei((nucleus.nucleus_id,),
                                                        {nucleus.nucleus_id: nucleus}, resolver)
                self.assertEqual(quotes, (surface_owner._quote(resolver.resolve("s1").raw_text),))
        inputs = _compile_inputs(self._row("生活を変えたいと思わなかった．"))
        resolver = build_evidence_span_resolver(inputs.source.evidence_spans)
        nucleus = inputs.grounded_plan.nuclei[0]
        unproven = replace(nucleus, semantic_frame=replace(nucleus.semantic_frame,
            attribute_codes=tuple(c for c in nucleus.semantic_frame.attribute_codes
                                  if c != "lexical:source_denied_past_thought_report")))
        self.assertEqual(surface_owner._quotes_for_nuclei((unproven.nucleus_id,),
            {unproven.nucleus_id: unproven}, resolver), ("「生活を変えたいと思わなかった」",))
        # A second typed nucleus can share the span; only the original full
        # source quote may preserve this ending, never its partial slice.
        raw = resolver.resolve("s1").raw_text
        fragment = replace(unproven, nucleus_id=unproven.nucleus_id + ":fragment",
            semantic_frame=replace(unproven.semantic_frame, attribute_codes=(
                "semantic_role:generic_relation_fragment",
                "source_fragment_scalar_source:normalized_raw_text",
                f"source_fragment_scalar_range:1:{len(raw)}",
            )))
        self.assertEqual(surface_owner._quotes_for_nuclei(
            (nucleus.nucleus_id, fragment.nucleus_id),
            {nucleus.nucleus_id: nucleus, fragment.nucleus_id: fragment}, resolver),
            ("「" + raw + "」", surface_owner._quote(raw[1:])))


class CMEEPastReportedWishTest(unittest.TestCase):
    def _wish(self, text):
        source, nucleus = CMEESameNucleusActionStatusTest()._action(text)
        return source, replace(nucleus, kind="wish", semantic_frame=replace(
            nucleus.semantic_frame, predicate_kind="wish", modality="wish",
            attribute_codes=("operator:wish", "time_scope:current_input"),
        ))

    def test_finite_past_report_preserves_host_and_same_wish_owner(self):
        for text in ("休みたいと言った。", "休みたいと言いました。",
                     "休みたいと思った。", "休みたいと思いました。",
                     "休みたいと思っていた。", "休みたいと思っていました。",
                     "休みたいと伝えた。", "休みたいと伝えました。"):
            with self.subTest(text=text):
                source, before = self._wish(text)
                after, = observation_plan_owner._final_stage1_align_action_status(
                    (before,), source.evidence_spans,
                    normalized_input=source.normalized_current_input,
                )
                self.assertEqual(after, replace(before, semantic_frame=replace(
                    before.semantic_frame, time_scope="past",
                    attribute_codes=("operator:wish", "time_scope:past"),
                )))
                unproven, = observation_plan_owner._final_stage1_align_action_status(
                    (before,), source.evidence_spans,
                )
                self.assertEqual(unproven, before)

    def test_report_scope_does_not_override_question_quote_or_current_wish(self):
        for text in (
            "休みたいと言った？", "休みたいと言った！？  ",
            "休みたいと言った ?", "休みたいと言ったら考える。",
            "休みたいと言ったかもしれない。", "休みたいとは言わなかった。",
            "休みたいと思っている。", "休みたい。",
            "同僚が休みたいと言った。", "同僚は休みたいと言った。",
            "たぶん休みたいと言った。", "「休みたいと言った」と聞いた。",
            "休みたいと思った？", "休みたいと思いました！？",
            "休みたいと思ったら考える。", "休みたいと思ったかもしれない。",
            "休みたいとは思わなかった。", "休みたいと思ったので、連絡した。",
            "同僚が休みたいと思った。", "同僚は休みたいと思いました。",
            "たぶん休みたいと思った。", "「休みたいと思った」と聞いた。",
            # Existing lexical future scope is outside this default-time fix.
            "静かに過ごしていきたいと思った。",
        ):
            with self.subTest(text=text):
                source, before = self._wish(text)
                after, = observation_plan_owner._final_stage1_align_action_status(
                    (before,), source.evidence_spans,
                    normalized_input=source.normalized_current_input,
                )
                self.assertEqual(after, before)
        source, before = self._wish("休みたいと言った。")
        past, = observation_plan_owner._final_stage1_align_action_status(
            (before,), source.evidence_spans,
            normalized_input=source.normalized_current_input,
        )
        resolver = build_evidence_span_resolver(source.evidence_spans)
        current = replace(past, semantic_frame=replace(past.semantic_frame, time_scope="current_input"))
        self.assertTrue(reception_owner._past_wish_target((past,), resolver))
        self.assertFalse(reception_owner._past_wish_target((past, current), resolver))
        self.assertFalse(reception_owner._past_wish_target((), resolver))
        self.assertFalse(reception_owner._past_wish_target((None,), resolver))
        for original in (
            "「はい。休みたいと言った。」と聞いた。",
            "同僚がいくつもの事情を詳しく説明したあと、休みたいと言った。",
        ):
            pos = original.index("休みたいと言った")
            span = replace(resolver.resolve(before.source_span_ids[0]),
                           start_index=pos, end_index=pos + len("休みたいと言った"))
            after, = observation_plan_owner._final_stage1_align_action_status(
                (before,), (span,), normalized_input={
                    **source.normalized_current_input, span.source_field: original,
                },
            )
            self.assertEqual(after, before)
        # A past calendar phrase inside the desired object is not a past
        # desire. Legacy time classification alone cannot label its reference.
        source, before = self._wish("昨日の打合せで考えたことを短い文にまとめて明確に伝えたい。")
        legacy_past = replace(before, semantic_frame=replace(before.semantic_frame, time_scope="past"))
        self.assertFalse(reception_owner._past_wish_target(
            (legacy_past,), build_evidence_span_resolver(source.evidence_spans),
        ))
        for text in ("昨日、休みたいと言った？", "昨日、休みたいと言った。",
                     "以前、休みたいと思っていた。"):
            source, before = self._wish(text)
            legacy_past = replace(before, semantic_frame=replace(before.semantic_frame, time_scope="past"))
            self.assertFalse(reception_owner._past_wish_target(
                (legacy_past,), build_evidence_span_resolver(source.evidence_spans),
            ))
        self.assertFalse(observation_plan_owner.past_reported_wish_finite(
            "休みたいと言った", span_text="昨日、話したあと休みたいと言った",
        ))

    def test_selected_past_wish_body_keeps_time_in_independent_inverse(self):
        rows, _ = load_validated_batch(_BATCH_PATH, _MANIFEST_PATH)
        checked = 0
        for row in rows:
            inputs = _compile_inputs(row)
            nuclei = {n.nucleus_id: n for n in inputs.grounded_plan.nuclei}
            resolver = build_evidence_span_resolver(inputs.source.evidence_spans)
            moves = inputs.grounded_plan.response_plan.human_reception_plan.moves
            if not any(m.reception_act == "protect_retained_intention"
                       and reception_owner._past_wish_target(tuple(nuclei[nid] for nid in m.target_nucleus_ids), resolver)
                       for m in moves):
                continue
            a = _full_surface_artifacts(row)
            checked += 1
            self.assertTrue(a.gate.passed)
            self.assertTrue(a.inverse.passed)
            self.assertEqual(a.sentence_plan.recovery_stage, "full")
            follow = _reception_text(a.surface.text)
            index = {n.nucleus_id: n for n in a.plan.nuclei}
            nominals = tuple(filter(None, (
                reception_owner.source_grounded_retained_wish_nominal(
                    move, a.plan, index, a.resolver,
                ) for move in a.plan.response_plan.human_reception_plan.moves
                if reception_owner.reception_effective_move_reference_mode(
                    a.plan.response_plan.human_reception_plan, move, "full",
                ) != "anaphoric_first"
            )))
            witnesses = nominals or ("当時の願い",)
            for witness in witnesses:
                self.assertEqual(follow.count(witness), 1)
            for move in a.plan.response_plan.human_reception_plan.moves:
                for nid in move.target_nucleus_ids:
                    target = next(n for n in a.plan.nuclei if n.nucleus_id == nid)
                    if not reception_owner._past_wish_target((target,), a.resolver):
                        continue
                    self.assertEqual(reception_owner.final_reception_anaphoric_context(
                        move=move, context_nucleus_ids=(nid,), plan=a.plan,
                        nucleus_index={n.nucleus_id: n for n in a.plan.nuclei},
                        resolver=a.resolver,
                    ), "当時の願い")
            for witness in witnesses:
                for wrong in ("今も残る願い", "これからの行動"):
                    changed = _tamper_reception(a.surface.text, witness, wrong)
                    inverse = evaluate_grounded_surface_body_inverse(
                        body=changed.encode("utf-8"), plan=a.plan, sentence_plan=a.sentence_plan,
                        resolver=a.resolver, selected_subjective_input=a.selected_subjective_input,
                    )
                    self.assertFalse(inverse.passed)
                    self.assertTrue(any("replay_mismatch" in code for code in inverse.failure_codes))
        self.assertGreater(checked, 0)

    def test_simple_past_report_reaches_the_selected_wish_and_body_inverse(self):
        for text in ("生活を変えたいと思った。", "生活を変えたいと思いました。"):
            with self.subTest(text=text):
                a = _full_surface_artifacts({"case_id": "public-simple-past-wish", "input": {
                    "thought_text": text, "action_text": "", "categories": ["生活"],
                    "emotions": [{"type": "不安", "strength": "weak"}],
                }})
                self.assertTrue(a.gate.passed, a.gate.rejection_reasons)
                self.assertTrue(a.inverse.passed, a.inverse.failure_codes)
                move, = a.plan.response_plan.human_reception_plan.moves
                target = next(n for n in a.plan.nuclei if n.nucleus_id == move.target_nucleus_ids[0])
                self.assertEqual((target.kind, target.semantic_frame.modality,
                                  target.semantic_frame.time_scope), ("wish", "wish", "past"))
                self.assertEqual(move.reception_act, "protect_retained_intention")
                self.assertIn("当時の願い", _reception_text(a.surface.text))
                for wrong in ("今も残る願い", "これからの行動"):
                    body = _tamper_reception(a.surface.text, "当時の願い", wrong)
                    self.assertFalse(evaluate_grounded_surface_body_inverse(
                        body=body.encode("utf-8"), plan=a.plan, sentence_plan=a.sentence_plan,
                        resolver=a.resolver, selected_subjective_input=a.selected_subjective_input,
                    ).passed)

    def test_past_wish_nominal_preserves_report_context_and_protection(self):
        # Use an actually selected explicit target from the unchanged loader.
        # A short synthetic input can leave this wish target unselected.
        rows, _ = load_validated_batch(_BATCH_PATH, _MANIFEST_PATH)
        a = None
        for row in rows:
            inputs = _compile_inputs(row)
            plan = inputs.grounded_plan
            index = {n.nucleus_id: n for n in plan.nuclei}
            resolver = build_evidence_span_resolver(inputs.source.evidence_spans)
            reception = plan.response_plan.human_reception_plan
            if any(
                reception_owner._past_wish_target(tuple(index[nid] for nid in move.target_nucleus_ids), resolver)
                and reception_owner.reception_effective_move_reference_mode(reception, move, "full") != "anaphoric_first"
                for move in reception.moves
            ):
                a = _full_surface_artifacts(row)
                break
        self.assertIsNotNone(a)
        self.assertTrue(a.gate.passed, a.gate.rejection_reasons)
        self.assertTrue(a.inverse.passed, a.inverse.failure_codes)
        self.assertEqual(a.sentence_plan.recovery_stage, "full")
        follow = _reception_text(a.surface.text)
        reception = a.plan.response_plan.human_reception_plan
        move = next(m for m in reception.moves if m.reception_act == "protect_retained_intention")
        index = {n.nucleus_id: n for n in a.plan.nuclei}
        target = index[move.target_nucleus_ids[0]]
        derive = reception_owner.source_grounded_retained_wish_nominal
        report = reception_owner._source_grounded_clause_candidate(target, a.resolver)
        nominal = report + "こと"
        self.assertEqual(follow.count(nominal), 1)
        self.assertNotIn("ことに表れた当時の願い", follow)
        self.assertIn("見失わずに、大切に受け止めています", follow)
        self.assertEqual(target.semantic_frame.time_scope, "past")
        self.assertEqual(derive(move, a.plan, index, a.resolver), nominal)
        for old, new in (
            (nominal, report.removesuffix("た") + "ていること"),
            (nominal, report.removesuffix("た") + "ていないこと"),
            (nominal, "別のことを望んだこと"),
            (nominal, "今の願い"), (nominal, "当時の願い"),
            (nominal, "「" + nominal + "」"), (nominal, nominal + "と" + nominal),
            ("その重なりも含めて", ""), ("見失わずに、", ""),
        ):
            with self.subTest(replacement=new):
                body = _tamper_reception(a.surface.text, old, new)
                self.assertFalse(evaluate_grounded_surface_body_inverse(
                    body=body.encode("utf-8"), plan=a.plan, sentence_plan=a.sentence_plan,
                    resolver=a.resolver, selected_subjective_input=a.selected_subjective_input,
                ).passed)
                self.assertFalse(evaluate_grounded_observation_gate(
                    plan=a.plan, sentence_plan=a.sentence_plan,
                    surface_result=replace(a.surface, text=body), resolver=a.resolver,
                    require_body_inverse=True, selected_subjective_input=a.selected_subjective_input,
                ).passed)
        for changes in (
            {"actor": "other"}, {"actor": "unknown"}, {"modality": "uncertain"},
            {"time_scope": "current_input"}, {"time_scope": "future"},
            {"polarity": "negative"}, {"predicate_kind": "action"},
            {"attribute_codes": (*target.semantic_frame.attribute_codes, "operator:performed_action")},
            {"attribute_codes": (*target.semantic_frame.attribute_codes, "quantity:multiple")},
        ):
            changed = replace(target, semantic_frame=replace(target.semantic_frame, **changes))
            plan = replace(a.plan, nuclei=tuple(changed if n == target else n for n in a.plan.nuclei))
            with self.subTest(changes=changes):
                self.assertEqual(derive(move, plan, {**index, target.nucleus_id: changed}, a.resolver), "")
        for text in ("休みたいと言いました", "休みたいと思っている", "休みたいと言った？",
                     "昨日、休みたいと言った", "休みたい気持ちで待っていた"):
            with self.subTest(text=text), patch.object(
                reception_owner, "_source_grounded_clause_candidate", return_value=text,
            ):
                self.assertEqual(derive(move, a.plan, index, a.resolver), "")
        kwargs = dict(reception_plan=reception, move=move, nucleus_index=index,
                      resolver=a.resolver, allow_short_anchor=False, plan=a.plan)
        self.assertNotEqual(reception_owner.resolve_grounded_reception_move_referent(**kwargs).text, nominal)
        with patch.object(reception_owner, "reception_effective_move_reference_mode", return_value="anaphoric_first"):
            self.assertEqual(reception_owner.resolve_grounded_reception_move_referent(
                **kwargs, final_source_fidelity=True,
            ).text, "当時の願い")


class CMEEPositiveFeelingProjectionTest(unittest.TestCase):
    def test_independent_selected_feeling_keeps_its_referent_after_effort(self):
        a = _full_surface_artifacts({
            "case_id": "public-independent-feeling-after-effort",
            "input": {
                "thought_text": "道具が使えてうれしかった。休憩したら、気持ちが楽になった。",
                "action_text": "作業台を片づけた。",
                "categories": ["仕事"],
                "emotions": [{"type": "喜び", "strength": "medium"}],
            },
        })
        self.assertTrue(a.gate.passed)
        self.assertTrue(a.inverse.passed)
        self.assertEqual(a.sentence_plan.recovery_stage, "full")
        response = a.plan.response_plan
        reception = response.human_reception_plan
        first, feeling = reception.moves
        self.assertEqual(
            (first.reception_act, feeling.reception_act),
            ("honor_concrete_effort", "recognize_lived_change"),
        )
        self.assertEqual(first.target_nucleus_ids, response.human_follow_target_ids)
        self.assertTrue(set(feeling.target_nucleus_ids) <= set(response.primary_nucleus_ids))
        self.assertTrue(all(move.required for move in reception.moves))
        self.assertEqual(feeling.reference_mode, "short_anchor_if_ambiguous")
        body = _reception_text(a.surface.text)
        self.assertIn("作業台を片づけた", body)
        self.assertIn("道具が使えてうれしかった", body)
        self.assertLess(body.index("道具が使えてうれしかった"), body.index("作業台を片づけた"))
        active = reception_owner.reception_active_moves(reception, "full")
        self.assertEqual(active[0].target_nucleus_ids, feeling.target_nucleus_ids)
        self.assertEqual(active[1].target_nucleus_ids, first.target_nucleus_ids)
        self.assertNotIn("その気持ち", body)
        changed = _tamper_reception(
            a.surface.text, "道具が使えてうれしかった", "別のことがうれしかった",
        )
        self.assertFalse(evaluate_grounded_surface_body_inverse(
            body=changed.encode("utf-8"), plan=a.plan,
            sentence_plan=a.sentence_plan, resolver=a.resolver,
            selected_subjective_input=a.selected_subjective_input,
        ).passed)
        for stage in ("integrated", "hedged", "minimal_grounded"):
            self.assertEqual(reception_owner.reception_effective_move_reference_mode(
                reception, feeling, stage,
            ), "anaphoric_first")

    def test_linked_coprimary_feeling_precedes_supplemental_action(self):
        for memo, boundary in (
            ("模型が完成してうれしかった。でも、説明書どおりに作れたのかは分からない。", "分からない"),
            ("作ったものを見てもらえてうれしかった。でも、手伝ってもらった部分もあり、自分だけの成果としてよいのか迷っている。", "迷っている"),
        ):
            with self.subTest(memo=memo):
                action = "作業台を片づけた。"
                row = {
                    "case_id": "public-linked-coprimary-and-action",
                    "input": {
                        "thought_text": memo, "action_text": action,
                        "categories": ["趣味"],
                        "emotions": [{"type": "平穏", "strength": "medium"}],
                    },
                }
                a = _full_surface_artifacts(row)
                self.assertTrue(a.gate.passed)
                self.assertTrue(a.inverse.passed)
                response = a.plan.response_plan
                self.assertEqual(len(response.primary_nucleus_ids), 2)
                self.assertEqual(len(response.human_follow_target_ids), 1)
                target_id = response.human_follow_target_ids[0]
                self.assertIn(target_id, response.primary_nucleus_ids)
                self.assertTrue(any(
                    relation.retention == "required"
                    and relation.type != "uncertain_connection"
                    and target_id in {relation.from_nucleus_id, relation.to_nucleus_id}
                    and {relation.from_nucleus_id, relation.to_nucleus_id}
                    <= set(response.primary_nucleus_ids)
                    for relation in a.plan.relations
                ))
                moves = response.human_reception_plan.moves
                self.assertEqual(
                    tuple(move.reception_act for move in moves),
                    ("recognize_lived_change", "honor_concrete_effort"),
                )
                self.assertTrue(all(move.required for move in moves))
                self.assertEqual(moves[0].target_nucleus_ids, (target_id,))
                self.assertEqual(moves[0].move_role, "attention")
                authored = next(s for s in a.authored if s.recovery_stage == "full")
                self.assertEqual(authored.realized_move_ids, ("rm1", "rm2"))
                follow = _reception_text(a.surface.text)
                self.assertIn(memo.split("。")[0], follow)
                self.assertIn(boundary, follow)
                self.assertEqual(follow.count(action.removesuffix("。") + "こと"), 1)
                self.assertLess(follow.index("気持ち"), follow.index(action.removesuffix("。")))
                changed = _tamper_reception(a.surface.text, boundary, "確定した")
                self.assertFalse(evaluate_grounded_surface_body_inverse(
                    body=changed.encode("utf-8"), plan=a.plan,
                    sentence_plan=a.sentence_plan, resolver=a.resolver,
                    selected_subjective_input=a.selected_subjective_input,
                ).passed)
                active = build_grounded_observation_plan({"memo": memo, "memo_action": action})
                active_nuclei = {n.nucleus_id: n for n in active.nuclei}
                self.assertEqual(
                    active_nuclei[active.response_plan.human_follow_target_ids[0]].source_fields,
                    ("memo_action",),
                )

    def test_independent_or_multiple_change_primaries_do_not_demote_action(self):
        for memo, eligible_count in (
            ("道具が使えるようになってうれしかった。全部覚えたわけではないけれど、練習を続けたことで少し安心した。", 1),
            ("道具が使えてうれしかった。休憩したら、気持ちが楽になった。", 2),
        ):
            with self.subTest(memo=memo):
                plan = build_final_stage1_grounded_observation_plan({
                    "memo": memo, "memo_action": "作業台を片づけた。",
                })
                nuclei = {n.nucleus_id: n for n in plan.nuclei}
                response = plan.response_plan
                self.assertGreater(len(response.primary_nucleus_ids), 1)
                eligible_ids = {
                    nucleus_id for nucleus_id in response.primary_nucleus_ids
                    if observation_plan_owner._reception_opportunity_families_for_nucleus(
                        nuclei[nucleus_id], safety_kind=plan.safety_policy.safety_kind,
                        final_source_fidelity=True,
                    ) == ("lived_change",)
                }
                self.assertEqual(len(eligible_ids), eligible_count)
                if eligible_count == 1:
                    self.assertFalse(any(
                        relation.retention == "required"
                        and relation.type != "uncertain_connection"
                        and {relation.from_nucleus_id, relation.to_nucleus_id}
                        <= set(response.primary_nucleus_ids)
                        and {relation.from_nucleus_id, relation.to_nucleus_id} & eligible_ids
                        for relation in plan.relations
                    ))
                self.assertEqual(
                    nuclei[response.human_follow_target_ids[0]].source_fields,
                    ("memo_action",),
                )
                self.assertEqual(
                    tuple(move.reception_act for move in response.human_reception_plan.moves),
                    ("honor_concrete_effort", "recognize_lived_change"),
                )

    def test_scored_memo_change_keeps_its_focus_beside_supplemental_action(self):
        for memo in (
            "少し歩いたら、気持ちが楽になった。",
            "休憩したら、頭の切り替えができた感じ。",
        ):
            with self.subTest(memo=memo):
                row = {
                    "case_id": "public-memo-change-and-action",
                    "input": {
                        "thought_text": memo,
                        "action_text": "机の上を片づけた。",
                        "categories": ["生活"],
                        "emotions": [{"type": "平穏", "strength": "medium"}],
                    },
                }
                a = _full_surface_artifacts(row)
                self.assertTrue(a.gate.passed)
                self.assertTrue(a.inverse.passed)
                plan = a.plan
                nuclei = {n.nucleus_id: n for n in plan.nuclei}
                follow_ids = plan.response_plan.human_follow_target_ids
                self.assertEqual(follow_ids, plan.response_plan.primary_nucleus_ids)
                self.assertEqual(nuclei[follow_ids[0]].source_fields, ("memo",))
                moves = plan.response_plan.human_reception_plan.moves
                self.assertEqual(len(moves), 2)
                self.assertTrue(all(move.required for move in moves))
                self.assertEqual(
                    {(move.reception_act, nuclei[move.target_nucleus_ids[0]].source_fields)
                     for move in moves},
                    {("recognize_lived_change", ("memo",)),
                     ("honor_concrete_effort", ("memo_action",))},
                )
                self.assertIn(memo.rstrip("。"), _reception_text(a.surface.text))
                self.assertEqual(moves[0].move_role, "attention")
                self.assertEqual(moves[0].reception_act, "recognize_lived_change")
                authored = next(s for s in a.authored if s.recovery_stage == "full")
                self.assertEqual(authored.realized_move_ids, ("rm1", "rm2"))
                active = build_grounded_observation_plan({
                    "memo": memo, "memo_action": row["input"]["action_text"],
                })
                active_nuclei = {n.nucleus_id: n for n in active.nuclei}
                self.assertEqual(
                    active_nuclei[active.response_plan.human_follow_target_ids[0]].source_fields,
                    ("memo_action",),
                )

    def test_unsettled_memo_is_not_promoted_by_change_labels_alone(self):
        for memo in (
            "前より楽な気はするけど、まだ重さが残っている。",
            "少し気になっている。",
        ):
            with self.subTest(memo=memo):
                plan = build_final_stage1_grounded_observation_plan({
                    "memo": memo, "memo_action": "机の上を片づけた。",
                })
                nuclei = {n.nucleus_id: n for n in plan.nuclei}
                follow = nuclei[plan.response_plan.human_follow_target_ids[0]]
                self.assertEqual(follow.source_fields, ("memo_action",))
                self.assertEqual(len(plan.response_plan.human_reception_plan.moves), 1)

    def test_typed_feeling_does_not_override_change_result_or_unknown(self):
        plan = build_final_stage1_grounded_observation_plan({"memo": "嬉しい。"})
        target = next(n for n in plan.nuclei if "memo" in n.source_fields)
        self.assertTrue(observation_plan_owner.is_grounded_positive_feeling(target))
        self.assertEqual(reception_owner._source_grounded_direct_predicate(target), "present_state")
        for code in ("operator:change", "operator:result",
                     "semantic_role:explicit_result",
                     "semantic_dependency:action_before_change"):
            changed = replace(target, semantic_frame=replace(
                target.semantic_frame,
                attribute_codes=(*target.semantic_frame.attribute_codes, code),
            ))
            self.assertFalse(observation_plan_owner.is_grounded_positive_feeling(changed))
            self.assertEqual(reception_owner._source_grounded_direct_predicate(changed), "present_change")
            self.assertFalse(reception_owner._positive_feeling_target((target, changed)))
        for field, value in (("predicate_kind", "change"), ("modality", "uncertain"),
                             ("polarity", "negative"), ("polarity", "mixed")):
            changed = replace(target, semantic_frame=replace(target.semantic_frame, **{field: value}))
            self.assertFalse(observation_plan_owner.is_grounded_positive_feeling(changed))
        missing = replace(target, semantic_frame=replace(
            target.semantic_frame, attribute_codes=tuple(
                code for code in target.semantic_frame.attribute_codes if code != "operator:feeling"
            ),
        ))
        self.assertFalse(observation_plan_owner.is_grounded_positive_feeling(missing))
        self.assertFalse(reception_owner._positive_feeling_target(()))
        self.assertFalse(reception_owner._positive_feeling_target((target, None)))
        self.assertFalse(observation_plan_owner.is_grounded_positive_feeling(
            replace(target, source_fields=("emotions",)),
        ))
        for text in ("今日は少し落ち着いた。", "少し落ち着いてきた。"):
            final = build_final_stage1_grounded_observation_plan({"memo": text})
            changed = next(n for n in final.nuclei if "memo" in n.source_fields)
            self.assertFalse(observation_plan_owner.is_grounded_positive_feeling(changed))
            self.assertIn("operator:change", changed.semantic_frame.attribute_codes)
            self.assertEqual(reception_owner._source_grounded_direct_predicate(changed), "present_change")
            base = build_grounded_observation_plan({"memo": text})
            base_target = next(n for n in base.nuclei if "memo" in n.source_fields)
            self.assertNotIn("operator:change", base_target.semantic_frame.attribute_codes)
        for text in ("落ち着いたら嬉しい。", "落ち着いたかもしれない。",
                     "落ち着いた？", "落ち着いた！？  ", "落ち着いた ?",
                     "「落ち着いた」と言った。"):
            final = build_final_stage1_grounded_observation_plan({"memo": text})
            for n in final.nuclei:
                self.assertNotIn("operator:change", n.semantic_frame.attribute_codes)

    def test_selected_feeling_body_requires_same_target_in_independent_inverse(self):
        rows, _ = load_validated_batch(_BATCH_PATH, _MANIFEST_PATH)
        checked = 0
        for row in rows:
            inputs = _compile_inputs(row)
            nuclei = {n.nucleus_id: n for n in inputs.grounded_plan.nuclei}
            reception_plan = inputs.grounded_plan.response_plan.human_reception_plan
            if not any(m.reception_act == "recognize_lived_change"
                       and reception_owner._positive_feeling_target(tuple(
                           nuclei[nid] for nid in m.target_nucleus_ids
                       )) for m in reception_plan.moves):
                continue
            a = _full_surface_artifacts(row)
            checked += 1
            self.assertTrue(a.gate.passed)
            self.assertTrue(a.inverse.passed)
            self.assertEqual(a.sentence_plan.recovery_stage, "full")
            follow = _reception_text(a.surface.text)
            self.assertIn("気持ち", follow)
            authored = next(s for s in a.authored if s.recovery_stage == "full")
            self.assertFalse(reception_owner.validate_grounded_human_reception_surface(
                authored, a.plan.response_plan.human_reception_plan, a.resolver, plan=a.plan,
                selected_subjective_input=a.selected_subjective_input,
            ))
            self.assertIn("human_reception_act_responsibility_missing:recognize_lived_change",
                          reception_owner.validate_grounded_human_reception_surface(
                              authored, a.plan.response_plan.human_reception_plan, a.resolver,
                          ))
            for wrong in ("変化", "その言葉"):
                changed = _tamper_reception(a.surface.text, "気持ち", wrong)
                inverse = evaluate_grounded_surface_body_inverse(
                    body=changed.encode("utf-8"), plan=a.plan, sentence_plan=a.sentence_plan,
                    resolver=a.resolver, selected_subjective_input=a.selected_subjective_input,
                )
                self.assertFalse(inverse.passed)
                self.assertTrue(any("replay_mismatch" in code for code in inverse.failure_codes))
                self.assertTrue(any("target_duty_missing" in code for code in inverse.failure_codes))
        self.assertGreater(checked, 0)

    def test_result_body_cannot_discharge_change_duty_with_feeling(self):
        rows, _ = load_validated_batch(_BATCH_PATH, _MANIFEST_PATH)
        for row in rows:
            inputs = _compile_inputs(row)
            nuclei = {n.nucleus_id: n for n in inputs.grounded_plan.nuclei}
            moves = inputs.grounded_plan.response_plan.human_reception_plan.moves
            if not any(m.reception_act == "recognize_lived_change" and any(
                "operator:result" in nuclei[nid].semantic_frame.attribute_codes
                and nuclei[nid].semantic_frame.predicate_kind == "feeling"
                for nid in m.target_nucleus_ids
            ) for m in moves):
                continue
            a = _full_surface_artifacts(row)
            self.assertTrue(a.gate.passed)
            self.assertTrue(a.inverse.passed)
            self.assertIn("変化", _reception_text(a.surface.text))
            changed = _tamper_reception(a.surface.text, "変化", "気持ち")
            inverse = evaluate_grounded_surface_body_inverse(
                body=changed.encode("utf-8"), plan=a.plan, sentence_plan=a.sentence_plan,
                resolver=a.resolver, selected_subjective_input=a.selected_subjective_input,
            )
            self.assertFalse(inverse.passed)
            self.assertTrue(any("target_duty_missing" in code for code in inverse.failure_codes))
            self.assertTrue(any("replay_mismatch" in code for code in inverse.failure_codes))
            break
        else:
            self.fail("source-bound result representative missing")


class CMEESameNucleusActionStatusTest(unittest.TestCase):
    def test_original_question_punctuation_cannot_prove_action_status(self):
        for text in ("資料を読んだ？", "資料を読みました ?",
                     "資料を読んでいる！？", "資料を読むつもり？"):
            with self.subTest(text=text):
                source, before = self._action(text)
                after, = observation_plan_owner._final_stage1_align_action_status(
                    (before,), source.evidence_spans,
                    normalized_input=source.normalized_current_input,
                )
                self.assertEqual(after, before)

    def test_finite_plan_preserves_embedded_desire_and_negation(self):
        for text in (
            "資料を読むつもり",
            "荷物を届ける予定です",
            "手順を確認するつもりだ",
            "来週も変更しない枠を残し、確かめたい点を短く記録するつもり",
        ):
            with self.subTest(text=text):
                source, action = self._action(text)
                before = replace(action, semantic_frame=replace(
                    action.semantic_frame, predicate_kind="wish", modality="wish",
                    polarity="negative", attribute_codes=(
                        "operator:action", "operator:wish", "operator:negation",
                    ),
                ))
                after, = observation_plan_owner._final_stage1_align_action_status(
                    (before,), source.evidence_spans,
                )
                self.assertEqual(after, replace(before, semantic_frame=replace(
                    before.semantic_frame, modality="intention", time_scope="future",
                    attribute_codes=(
                        *before.semantic_frame.attribute_codes,
                        "time_scope:future", "semantic_role:next_intention",
                        "semantic_role:concrete_action",
                    ),
                )))
                # Correct source status within the existing intention
                # family; do not add a concrete-effort opportunity.
                self.assertFalse(observation_plan_owner._is_explicit_action_nucleus(
                    after, final_source_fidelity=True,
                ))
                self.assertFalse(observation_plan_owner._is_explicit_action_nucleus(after))
                self.assertFalse(reception_owner.reception_action_is_performed(
                    after, final_source_fidelity=True,
                ))
                self.assertTrue(reception_owner.reception_action_is_future_intention(
                    after, final_source_fidelity=True,
                ))

    def test_finite_plan_does_not_promote_uncertain_negative_or_other_subject(self):
        for text, modality in (
            ("資料を読みたい", "wish"),
            ("資料を読むつもりだった", "wish"),
            ("資料を読む予定でした", "wish"),
            ("資料を読むつもりと思う", "wish"),
            ("資料を読む予定らしい", "wish"),
            ("資料を読む予定かもしれない", "wish"),
            ("資料を読むつもりかな", "wish"),
            ("資料を読む予定ではない", "wish"),
            ("資料を読まないつもり", "wish"),
            ("たぶん資料を読むつもり", "wish"),
            ("資料を読む予定", "uncertain"),
            ("弟が資料を読むつもり", "wish"),
            ("妹は資料を読む予定", "wish"),
            ("同僚も資料を読むつもり", "wish"),
            ("明日は同僚が資料を読むつもり", "wish"),
            ("資料は明日に読むつもり", "wish"),
            ("「資料を読むつもり」と聞いた", "wish"),
        ):
            with self.subTest(text=text, modality=modality):
                source, action = self._action(text)
                before = replace(action, semantic_frame=replace(
                    action.semantic_frame, modality=modality,
                    attribute_codes=("operator:action", "operator:wish"),
                ))
                after, = observation_plan_owner._final_stage1_align_action_status(
                    (before,), source.evidence_spans,
                )
                self.assertEqual(replace(after, semantic_frame=before.semantic_frame), before)
                self.assertNotEqual(after.semantic_frame.modality, "intention")
                self.assertNotIn("semantic_role:concrete_action", after.semantic_frame.attribute_codes)
                self.assertFalse(observation_plan_owner._is_explicit_action_nucleus(
                    after, final_source_fidelity=True,
                ))

    def test_finite_plan_reaches_selected_body_and_independent_inverse(self):
        rows, _ = load_validated_batch(_BATCH_PATH, _MANIFEST_PATH)
        checked = 0
        for row in rows:
            action = row["input"]["action_text"].rstrip("。 ")
            if not action.endswith(("つもり", "予定", "つもりです", "予定です")):
                continue
            artifacts = _full_surface_artifacts(row)
            targets = {n.nucleus_id for n in artifacts.plan.nuclei
                       if "memo_action" in n.source_fields
                       and n.semantic_frame.modality == "intention"}
            selected = any(d.reception_act == "protect_retained_intention"
                           and targets.intersection(d.target_nucleus_ids)
                           for d in artifacts.selected_subjective_input.decisions)
            follow = _reception_text(artifacts.surface.text)
            # Short inputs and nonprimary Moves may legitimately use an
            # anaphor. Exercise a real selected explicit prospective body.
            if not selected or action not in follow:
                continue
            checked += 1
            self.assertEqual(artifacts.sentence_plan.recovery_stage, "full")
            self.assertTrue(artifacts.gate.passed)
            self.assertTrue(artifacts.inverse.passed)
            self.assertIn("これからの行動", follow)
            self.assertNotIn("願い", follow)
            self.assertNotIn("実際の行動", follow)
            authored = next(surface for surface in artifacts.authored
                            if surface.recovery_stage == "full")
            reception_plan = artifacts.plan.response_plan.human_reception_plan
            self.assertFalse(reception_owner.validate_grounded_human_reception_surface(
                authored, reception_plan, artifacts.resolver, plan=artifacts.plan,
            ))
            self.assertIn(
                "human_reception_act_responsibility_missing:protect_retained_intention",
                reception_owner.validate_grounded_human_reception_surface(
                    authored, reception_plan, artifacts.resolver,
                ),
            )
            for wrong in ("実際の行動", "その願い"):
                changed = _tamper_reception(
                    artifacts.surface.text, "これからの行動", wrong,
                )
                inverse = evaluate_grounded_surface_body_inverse(
                    body=changed.encode("utf-8"), plan=artifacts.plan,
                    sentence_plan=artifacts.sentence_plan, resolver=artifacts.resolver,
                    selected_subjective_input=artifacts.selected_subjective_input,
                )
                self.assertFalse(inverse.passed)
                self.assertTrue(any("replay_mismatch" in code for code in inverse.failure_codes))
        self.assertGreater(checked, 0)

    def test_continuation_inside_desired_object_keeps_source_scope(self):
        for text, resolved in (
            ("待ち続ける時間を短くしたい", True),
            ("働き続ける周期を長くしたいです", True),
            ("待ち続けた時間を短くしたい", False),
            ("待ち続けていた期間を短くしたい", False),
            ("待ち続ける時間を短くしたかった", False),
            ("待ち続ける時間を短くしたいと思っていた", False),
            ("待ち続ける時間を短くしたいと言った", False),
            ("待ち続ける時間を短くしたいかもしれない", False),
            ("待ち続ける時間を短くしたいわけではない", False),
            ("ずっと待ち続ける時間を短くしたい", False),
            ("待ち続ける時間を短くしたいと思い続けている", False),
            ("「待ち続ける時間を短くしたい」と聞いた", False),
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
                expected_frame = replace(
                    before.semantic_frame, time_scope="current_input",
                    attribute_codes=(
                        "operator:wish", "operator:continuation", "time_scope:current_input",
                    ),
                ) if resolved else before.semantic_frame
                self.assertEqual(after, replace(before, semantic_frame=expected_frame))
        # Desire uncertainty has its own earlier correction; it is not an
        # affirmative current desire admitted by the continuation grammar.
        self.assertFalse(observation_plan_owner._final_stage1_continuation_is_desired(
            "待ち続ける時間を短くしたいのか分からない",
        ))

    def test_desired_object_time_correction_reaches_full_body_and_inverse(self):
        rows, _ = load_validated_batch(_BATCH_PATH, _MANIFEST_PATH)
        checked = 0
        for row in rows:
            memo = next((part for part in row["input"]["thought_text"].split("。")
                         if observation_plan_owner._final_stage1_continuation_is_desired(part)
                         and not part.endswith(("続けたい", "続けたいです", "繰り返したい"))), "")
            if not memo:
                continue
            checked += 1
            artifacts = _full_surface_artifacts(row)
            self.assertEqual(artifacts.sentence_plan.recovery_stage, "full")
            self.assertTrue(artifacts.gate.passed)
            self.assertTrue(artifacts.inverse.passed)
            follow = _reception_text(artifacts.surface.text)
            self.assertIn(memo, follow)
            self.assertNotIn("今も、", follow)
            changed = _tamper_reception(
                artifacts.surface.text, follow.strip(), "今も、" + follow.strip(),
            )
            inverse = evaluate_grounded_surface_body_inverse(
                body=changed.encode("utf-8"), plan=artifacts.plan,
                sentence_plan=artifacts.sentence_plan, resolver=artifacts.resolver,
                selected_subjective_input=artifacts.selected_subjective_input,
            )
            self.assertFalse(inverse.passed)
            self.assertTrue(any("replay_mismatch" in code for code in inverse.failure_codes))
        self.assertGreater(checked, 0)

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

    def test_received_performance_does_not_prove_self_execution(self):
        for predicate in (
            "整理してもらった", "書いてもらった", "見てくれた",
            "片づけてもらった", "片づけてもらいました", "片づけてもらっている",
            "片づけてもらっていた", "片づけてもらっています", "片づけてもらっていました",
            "片づけてくれた", "片づけてくれました", "片づけてくれている",
            "片づけてくれていた", "片づけてくれています", "片づけてくれていました",
            "片づけていただいた", "片づけていただきました", "片づけていただいている",
            "片づけていただいていた", "片づけていただいています", "片づけていただいていました",
        ):
            with self.subTest(predicate=predicate):
                source, before = self._action(f"荷物を{predicate}。")
                after, = observation_plan_owner._final_stage1_align_action_status(
                    (before,), source.evidence_spans,
                )
                self.assertEqual(replace(after, semantic_frame=before.semantic_frame), before)
                self.assertEqual(after.semantic_frame.actor, before.semantic_frame.actor)
                self.assertEqual(after.semantic_frame.polarity, before.semantic_frame.polarity)
                self.assertEqual(after.semantic_frame.modality, "fact")
                self.assertIn(after.semantic_frame.time_scope, ("past", "continuing"))
                self.assertFalse(observation_plan_owner.source_proven_performed_action_status(after))
                self.assertFalse(reception_owner.reception_action_is_performed(
                    after, final_source_fidelity=True,
                ))

    def test_embedded_received_performance_keeps_later_self_execution(self):
        for text in (
            "荷物を運んだ。",
            "荷物を運んでもらったことを記録した。",
            "荷物を運んでくれたことを記録した。",
            "荷物を運んでいただいたことを記録した。",
            "本をもらった。",
            "本を店でもらった。",
            "資料を窓口でもらった。",
            "資料を全てもらった。",
            "小遣いを手伝いでもらった。",
            "本を皆さんでもらった。",
        ):
            with self.subTest(text=text):
                source, before = self._action(text)
                after, = observation_plan_owner._final_stage1_align_action_status(
                    (before,), source.evidence_spans,
                )
                self.assertTrue(observation_plan_owner.source_proven_performed_action_status(after))
                self.assertTrue(reception_owner.reception_action_is_performed(
                    after, final_source_fidelity=True,
                ))

    def test_received_and_self_performed_clauses_keep_distinct_body_proof(self):
        artifacts = _full_surface_artifacts({
            "case_id": "received-performance-expression-unit",
            "input": {
                "thought_text": "",
                "action_text": "荷物を片づけてもらった。届いたことを記録した。",
                "categories": ["生活"],
                "emotions": [{"type": "平穏", "strength": "weak"}],
            },
        })
        self.assertTrue(artifacts.gate.passed)
        self.assertTrue(artifacts.inverse.passed)
        self.assertEqual(artifacts.sentence_plan.recovery_stage, "full")
        self.assertIn("荷物を片づけてもらった", artifacts.surface.text)
        self.assertNotIn("荷物を片づけてもらった」という行動", artifacts.surface.text)
        self.assertIn("届いたことを記録した」という行動", artifacts.surface.text)
        actions = [n for n in artifacts.plan.nuclei if n.kind == "action"]
        self.assertEqual(len(actions), 2)
        self.assertEqual([
            observation_plan_owner.source_proven_performed_action_status(n)
            for n in actions
        ], [False, True])

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

    def test_uncertain_wish_pair_keeps_source_modality_and_same_selected_targets(self):
        reached = 0
        target = reception_owner._source_grounded_target_np
        predicate = reception_owner._source_grounded_response_predicate_surface
        for row in self.rows_by_id.values():
            inputs = _compile_inputs(row)
            uncertain = {n.nucleus_id for n in inputs.grounded_plan.nuclei
                         if n.kind == "wish" and n.semantic_frame.modality == "uncertain"}
            if not any(r.type == "wish_and_constraint"
                       and uncertain.intersection((r.from_nucleus_id, r.to_nucleus_id))
                       for r in inputs.grounded_plan.relations):
                continue
            cores, predicates = [], []
            def capture_target(move, realization, **kwargs):
                core = target(move, realization, **kwargs)
                if (kwargs["referent_kind"] == "retained_wish" and core.pending_relation_slots
                    and realization.semantic_profiles[kwargs["target_owner_slot"]].modality == "uncertain"):
                    cores.append((core, realization, kwargs))
                return core
            def capture_predicate(reception_act, move_role, **kwargs):
                result = predicate(reception_act, move_role, **kwargs)
                if kwargs.get("pending_relation_slots") and kwargs["semantic_profile"].modality == "uncertain":
                    predicates.append({"reception_act": reception_act, "move_role": move_role, **kwargs})
                return result
            with patch.object(reception_owner, "_source_grounded_target_np", side_effect=capture_target), patch.object(
                    reception_owner, "_source_grounded_response_predicate_surface", side_effect=capture_predicate):
                a = _full_surface_artifacts(row)
            if not cores:
                continue
            reached += 1
            self.assertTrue(a.gate.passed, a.gate.rejection_reasons)
            self.assertTrue(a.inverse.passed, a.inverse.failure_codes)
            self.assertTrue(predicates)
            core, realization, kw = cores[0]
            self.assertEqual(core.pending_relation_slots, (0,))
            self.assertEqual(core.semantic_slots, (0, 1))
            relation, = realization.relations
            self.assertEqual(relation.relation_kind, "wish_and_constraint")
            self.assertEqual(relation.endpoint_roles, ("LEFT", "RIGHT"))
            self.assertEqual(kw["referent_text"], "まだ確かではない願い")
            profile = realization.semantic_profiles[kw["target_owner_slot"]]
            self.assertEqual((profile.nucleus_kind, profile.predicate_kind, profile.modality), ("wish", "wish", "uncertain"))
            decision = predicates[0]["selected_subjective_decision"]
            prop = decision.subjective_proposition
            self.assertTrue(reception_owner._selected_material_appraisal(decision))
            self.assertIsNone(prop.focal_relation_ref)
            self.assertIsNone(prop.appraisal_content.focal_relation_ref)
            semantic_map = dict(a.selected_subjective_input.semantic_nucleus_pairs)
            appraised = {semantic_map[b.semantic_ref] for b in decision.basis_rows
                         if b.contribution_ref in decision.selected_contribution_refs
                         and b.binding_ref in prop.appraisal_content.appraised_bindings
                         and b.semantic_ref in prop.primary_target_refs}
            self.assertTrue(uncertain.intersection(appraised))
            selected_relation = next(r for r in a.plan.relations if r.type == "wish_and_constraint")
            self.assertLessEqual({selected_relation.from_nucleus_id, selected_relation.to_nucleus_id}, appraised)
            follow = _reception_text(a.surface.text)
            for fragment in realization.semantic_fragments:
                self.assertEqual(core.text.count(fragment), 1)
            self.assertIn(core.text, follow)
            self.assertIn(kw["meaning_fragment"] + "というまだ確かではない願い", core.text)
            self.assertIn("見過ごさず、その重なりも含めて", follow)
            self.assertNotIn("がともにあること", core.text)
            for old, new in (
                (kw["meaning_fragment"], "別の内容"),
                ("まだ確かではない願い", "確かに定まった願い"),
                ("その重なりも含めて", ""), ("を見過ごさず、", "に目が留まり、"),
                ("受け止めています", "受け止めていました"),
                ("見失わずに、大切に", "大切に"),
                (core.text, "「" + core.text + "」"),
            ):
                body = _tamper_reception(a.surface.text, old, new)
                self.assertNotEqual(body, a.surface.text)
                self.assertFalse(evaluate_grounded_surface_body_inverse(
                    body=body.encode(), plan=a.plan, sentence_plan=a.sentence_plan,
                    resolver=a.resolver, selected_subjective_input=a.selected_subjective_input).passed)
                self.assertFalse(evaluate_grounded_observation_gate(
                    plan=a.plan, sentence_plan=a.sentence_plan, surface_result=replace(a.surface, text=body),
                    resolver=a.resolver, require_body_inverse=True,
                    selected_subjective_input=a.selected_subjective_input).passed)
            for kind in ("contrast", "attempt_and_block", "coexistence", "uncertain_connection"):
                with self.assertRaises(reception_owner.GroundedHumanReceptionSurfaceError):
                    predicate(**{**predicates[0], "pending_relation_kind": kind})
        self.assertGreater(reached, 0)

    def test_finite_wish_clause_preserves_the_same_whole_source(self):
        reached = 0
        target = reception_owner._source_grounded_target_np
        for a in self.artifacts.values():
            cores = []
            def capture(move, realization, **kwargs):
                core = target(move, realization, **kwargs)
                if (kwargs["referent_kind"] == "retained_wish" and kwargs["referent_text"] == "願い"
                    and realization.reference_mode != "ANAPHORIC" and not realization.relations
                    and not kwargs["meaning_fragment"].endswith(("たい", "ほしい", "欲しい"))):
                    cores.append((core, realization, kwargs))
                return core
            args, kwargs = a.author_arguments[0]
            with patch.object(reception_owner, "_source_grounded_target_np", side_effect=capture):
                replay = reception_owner.realize_source_grounded_human_reception(*args, **kwargs)
            for core, realization, kw in cores:
                if realization.semantic_profiles[kw["target_owner_slot"]].future_action:
                    continue
                reached += 1
                self.assertEqual(core.text, kw["meaning_fragment"] + "という願い")
                self.assertIn(core.text, replay.text)
                self.assertIn(core.text, _reception_text(a.surface.text))
                body = _tamper_reception(a.surface.text, core.text, kw["meaning_fragment"] + "ことに表れた願い")
                self.assertFalse(evaluate_grounded_surface_body_inverse(
                    body=body.encode(), plan=a.plan, sentence_plan=a.sentence_plan,
                    resolver=a.resolver, selected_subjective_input=a.selected_subjective_input).passed)
        self.assertGreater(reached, 0)

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

    def test_material_related_objects_keeps_both_targets_and_completes_the_same_relation(self):
        seen_roles, seen_kinds = set(), set()
        for a in (self.artifacts[key] for key in _TYPED_RELATION_CLOSURE_CASE_IDS):
            if "その重なりも含めて" not in _reception_text(a.surface.text):
                continue
            cores, predicates = [], []
            target = reception_owner._source_grounded_target_np
            predicate = reception_owner._source_grounded_response_predicate_surface
            def trace_target(move, realization, **kwargs):
                core = target(move, realization, **kwargs)
                if core.pending_relation_slots:
                    cores.append((move, core, realization, kwargs))
                return core
            def trace_predicate(reception_act, move_role, **kwargs):
                value = predicate(reception_act, move_role, **kwargs)
                if kwargs.get("pending_relation_slots"):
                    predicates.append({"reception_act": reception_act, "move_role": move_role, **kwargs})
                return value
            reception = a.plan.response_plan.human_reception_plan
            line = next(line for line in a.sentence_plan.lines if line.binding.line_role == "human_follow")
            with patch.object(reception_owner, "_source_grounded_target_np", side_effect=trace_target), patch.object(
                    reception_owner, "_source_grounded_response_predicate_surface", side_effect=trace_predicate):
                replay = reception_owner.replay_source_grounded_human_reception_from_plan(
                    reception, {n.nucleus_id: n for n in a.plan.nuclei}, a.resolver,
                    plan=a.plan, recovery_stage=a.sentence_plan.recovery_stage,
                    clause_plans=line.reception_clause_plans,
                    selected_subjective_input=a.selected_subjective_input)
            self.assertEqual(replay.text, _reception_text(a.surface.text).strip())
            self.assertTrue(a.gate.passed and a.inverse.passed)
            self.assertTrue(cores and predicates)
            for (move, core, realization, target_kw), kw in zip(cores, predicates, strict=True):
                if kw["pending_relation_kind"] not in {"wish_and_constraint", "attempt_and_block"}:
                    continue
                seen_roles.add(kw["move_role"])
                seen_kinds.add(kw["pending_relation_kind"])
                self.assertEqual((core.relation_count, core.pending_relation_slots, core.semantic_slots),
                                 (0, (0,), (0, 1)))
                self.assertTrue(target_kw["material_pair_object"])
                relation = realization.relations[0]
                self.assertEqual(relation.relation_kind, kw["pending_relation_kind"])
                self.assertEqual(relation.endpoint_roles, ("LEFT", "RIGHT"))
                decision = kw["selected_subjective_decision"]
                prop = decision.subjective_proposition
                self.assertTrue(reception_owner._selected_material_appraisal(decision))
                self.assertIsNone(prop.focal_relation_ref)
                self.assertIsNone(prop.appraisal_content.focal_relation_ref)
                semantic_map = dict(a.selected_subjective_input.semantic_nucleus_pairs)
                selected = {semantic_map[b.semantic_ref] for b in decision.basis_rows
                            if b.contribution_ref in decision.selected_contribution_refs
                            and b.binding_ref in prop.appraisal_content.appraised_bindings
                            and b.semantic_ref in prop.primary_target_refs}
                owned = [r for r in a.plan.relations if r.type == relation.relation_kind
                         and set(move.target_nucleus_ids).intersection({r.from_nucleus_id, r.to_nucleus_id})
                         and {r.from_nucleus_id, r.to_nucleus_id} <= selected]
                self.assertEqual(len(owned), 1)
                ending = ("を、" if kw["move_role"] != "attention" else
                          "を見過ごさず、" if kw["recovery_stage"] == "full" else
                          "に目が留まり、それらを、")
                self.assertIn(core.text + ending + "その重なりも含めて", replay.text)
                for old, new in (
                    ("その重なりも含めて", ""), ("その重なりも含めて", "その違いも含めて"),
                    (core.text, "別の出来事"), (core.text, "「" + core.text + "」"),
                    *((fragment, "別の内容") for fragment in realization.semantic_fragments),
                    ("受け止めています", "受け止めていました"),
                ):
                    body = _tamper_reception(a.surface.text, old, new)
                    self.assertFalse(evaluate_grounded_surface_body_inverse(
                        body=body.encode(), plan=a.plan, sentence_plan=a.sentence_plan,
                        resolver=a.resolver, selected_subjective_input=a.selected_subjective_input).passed)
                    self.assertFalse(evaluate_grounded_observation_gate(
                        plan=a.plan, sentence_plan=a.sentence_plan, surface_result=replace(a.surface, text=body),
                        resolver=a.resolver, require_body_inverse=True,
                        selected_subjective_input=a.selected_subjective_input).passed)
                for updates in (
                    {"pending_relation_kind": None}, {"pending_relation_kind": "user_stated_cause"},
                    {"pending_relation_kind": "coexistence"},
                    {"pending_relation_slots": (False,)}, {"pending_relation_slots": (1,)},
                    {"pending_relation_slots": ()}, {"distributive_object": True},
                    {"unfinished_pair": True}, {"move_role": "significance"},
                ):
                    with self.assertRaises(reception_owner.GroundedHumanReceptionSurfaceError):
                        predicate(**{**kw, **updates})
        self.assertEqual(seen_roles, {"attention", "felt_response"})
        self.assertEqual(seen_kinds, {"wish_and_constraint", "attempt_and_block"})

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
        missing_change_duty = multi_reception.replace("変化", "内容", 1)
        self.assertNotEqual(missing_change_duty, multi_reception)
        with self.assertRaisesRegex(
            reception_owner.GroundedHumanReceptionSurfaceError,
            "reception_actual_surface_contract_failed",
        ):
            self._bind_reception_text(
                multi_case,
                missing_change_duty,
            )

        accountability_case = "nls3s_b001_0066"
        accountability_reception = _reception_text(
            self.artifacts[accountability_case].surface.text
        )
        accountability = self._bind_reception_text(
            accountability_case,
            accountability_reception,
        )
        # The selected duties stay intact while discourse receives the feeling first.
        planned = self.artifacts[accountability_case].plan.response_plan.human_reception_plan
        self.assertEqual(
            tuple((move.move_id, move.reception_act) for move in planned.moves),
            (("rm1", "honor_concrete_effort"), ("rm2", "recognize_lived_change")),
        )
        self.assertTrue(all(move.required for move in planned.moves))
        self.assertEqual(accountability.realized_move_ids, ("rm2", "rm1"))
        self.assertEqual(
            accountability.realized_reception_acts,
            ("recognize_lived_change", "honor_concrete_effort"),
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
            "たこと",
            "たという内容",
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
            "見過ごさず、",
            "",
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
            "受け止めています",
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
            "まだ分からないこと",
            f"まだ分からないこと（{target}）",
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


class CMEEConcreteActionNominalTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifacts = {}
        cls.predicates = {}
        for name, action in (
            ("qualified", "昨日、その資料を三ページだけ整理した"),
            ("demonstrative", "その資料を整理した"),
            ("embedded_negative", "今は引き受けられないと担当者に伝えた"),
            ("ongoing", "資料を整理している"),
        ):
            row = {"case_id": "public-concrete-action-" + name, "input": {
                "action_text": action + "。", "thought_text": "まだ先の見通しは分からない。",
                "categories": ["仕事"], "emotions": [{"type": "不安", "strength": "medium"}],
            }}
            captured = []
            original = reception_owner._source_grounded_response_predicate_surface
            def capture(reception_act, move_role, **kwargs):
                result = original(reception_act, move_role, **kwargs)
                captured.append({"reception_act": reception_act, "move_role": move_role, **kwargs})
                return result
            with patch.object(reception_owner, "_source_grounded_response_predicate_surface", side_effect=capture):
                cls.artifacts[name] = (action, _full_surface_artifacts(row))
            cls.predicates[name] = tuple(captured)

    def test_concrete_action_keeps_complete_source_and_selected_replay(self):
        for name, (action, a) in self.artifacts.items():
            with self.subTest(name=name):
                follow = _reception_text(a.surface.text)
                self.assertTrue(a.inverse.passed, a.inverse.failure_codes)
                self.assertTrue(a.gate.passed, a.gate.rejection_reasons)
                self.assertEqual(a.sentence_plan.recovery_stage, "full")
                self.assertEqual(follow.count(action + "こと"), 1)
                self.assertNotIn("実際の行動", follow)
                self.assertIn("大切に受け止めています", follow)
                self.assertTrue(reception_owner._performed_action_nominal_responsibility(follow, action + "こと"))
                self.assertFalse(reception_owner._performed_action_nominal_responsibility(
                    follow.replace("大切に受け止めています", "大切ではありません"), action + "こと",
                ))
                line = next(line for line in a.sentence_plan.lines
                            if line.binding.line_role == "human_follow")
                replay = reception_owner.replay_source_grounded_human_reception_from_plan(
                    a.plan.response_plan.human_reception_plan,
                    {n.nucleus_id: n for n in a.plan.nuclei}, a.resolver,
                    plan=a.plan, recovery_stage=a.sentence_plan.recovery_stage,
                    clause_plans=line.reception_clause_plans,
                    selected_subjective_input=a.selected_subjective_input,
                )
                self.assertEqual(replay.text, follow.strip())
                self.assertTrue(all(kwargs["selected_subjective_input"] is a.selected_subjective_input
                                    for _args, kwargs in a.author_arguments))

    def test_concrete_action_rejects_source_and_responsibility_tampering(self):
        mutations = (
            ("qualified", "昨日", "明日"),
            ("qualified", "その資料", "別の資料"),
            ("qualified", "三ページだけ", "全ページ"),
            ("qualified", "整理したこと", "整理しなかったこと"),
            ("embedded_negative", "引き受けられない", "引き受けられる"),
            ("embedded_negative", "担当者に", "家族に"),
            ("ongoing", "整理していること", "整理する予定のこと"),
            ("demonstrative", "大切に受け止めています", "大切ではありません"),
        )
        for name, old, new in mutations:
            with self.subTest(name=name, old=old):
                _action, a = self.artifacts[name]
                body = _tamper_reception(a.surface.text, old, new)
                inverse = evaluate_grounded_surface_body_inverse(
                    body=body.encode("utf-8"), plan=a.plan, sentence_plan=a.sentence_plan,
                    resolver=a.resolver, selected_subjective_input=a.selected_subjective_input,
                )
                self.assertFalse(inverse.passed)
                gate = evaluate_grounded_observation_gate(
                    plan=a.plan, sentence_plan=a.sentence_plan,
                    surface_result=replace(a.surface, text=body), resolver=a.resolver,
                    require_body_inverse=True, selected_subjective_input=a.selected_subjective_input,
                )
                self.assertFalse(gate.passed)

    def test_body_nominal_marker_is_structural_and_reception_scoped(self):
        action, a = self.artifacts["qualified"]
        body = a.surface.text.encode("utf-8")
        witness = surface_owner.parse_grounded_surface_body_bytes(body)
        markers = [m for m in witness.markers if m.marker_code == "finite_clause_nominal"]
        self.assertTrue(markers)
        nominal = (action + "こと").encode("utf-8")
        end = body.index(nominal) + len(nominal)
        self.assertTrue(any(m.utf8_byte_end == end for m in markers))
        self.assertTrue(all(m.section == "reception" and m.marker_kind == "semantic" for m in markers))
        self.assertTrue(all("target_effort" not in s.reception_marker_codes
                            for s in witness.sentences if s.section == "reception"))
        # The suffix alone cannot establish the Move's concrete target.
        for replacement in ("別の資料を整理したこと", "別の資料を整理したという実際の行動"):
            changed = _tamper_reception(a.surface.text, action + "こと", replacement)
            inverse = evaluate_grounded_surface_body_inverse(
                body=changed.encode("utf-8"), plan=a.plan, sentence_plan=a.sentence_plan,
                resolver=a.resolver, selected_subjective_input=a.selected_subjective_input,
            )
            self.assertFalse(inverse.passed)
            self.assertTrue(any("target_duty_missing" in code for code in inverse.failure_codes))

    def test_nominal_requires_same_target_actor_status_and_quantity_proof(self):
        action, a = self.artifacts["demonstrative"]
        move = a.plan.response_plan.human_reception_plan.moves[0]
        index = {n.nucleus_id: n for n in a.plan.nuclei}
        target = index[move.target_nucleus_ids[0]]
        self.assertEqual(reception_owner.source_grounded_performed_action_nominal(move, index, a.resolver), action + "こと")
        for changes in (
            {"actor": "other"}, {"actor": "unknown"}, {"modality": "uncertain"},
            {"time_scope": "future"},
            {"attribute_codes": tuple(c for c in target.semantic_frame.attribute_codes
                                      if c != "operator:performed_action")},
            {"attribute_codes": (*target.semantic_frame.attribute_codes, "quantity:multiple")},
        ):
            with self.subTest(changes=changes):
                changed = replace(target, semantic_frame=replace(target.semantic_frame, **changes))
                self.assertEqual(reception_owner.source_grounded_performed_action_nominal(
                    move, {**index, target.nucleus_id: changed}, a.resolver,
                ), "")

    def test_legacy_referent_does_not_acquire_final_nominal_grammar(self):
        action, a = self.artifacts["demonstrative"]
        plan = a.plan.response_plan.human_reception_plan
        index = {n.nucleus_id: n for n in a.plan.nuclei}
        kwargs = dict(reception_plan=plan, move=plan.moves[0], nucleus_index=index,
                      resolver=a.resolver, allow_short_anchor=False, allow_anaphoric_topic=True)
        final = reception_owner.resolve_grounded_reception_move_referent(**kwargs, final_source_fidelity=True)
        legacy = reception_owner.resolve_grounded_reception_move_referent(**kwargs)
        self.assertEqual(final.text, action + "こと")
        self.assertNotEqual(legacy.text, final.text)
        self.assertEqual(final.kind, "self_started_effort")


    def test_selected_material_attention_receives_one_complete_action_object(self):
        action, a = self.artifacts["qualified"]
        follow = _reception_text(a.surface.text)
        self.assertEqual(follow.strip(), action + "ことを見過ごさず、大切に受け止めています。")
        decision = a.selected_subjective_input.decisions[0]
        self.assertTrue(reception_owner._selected_material_appraisal(decision))
        self.assertEqual((decision.reception_act, len(decision.target_nucleus_ids), decision.support_nucleus_ids),
                         ("honor_concrete_effort", 1, ()))
        self.assertEqual(a.plan.response_plan.human_reception_plan.moves[0].move_role, "attention")
        self.assertLessEqual({"full", "hedged"}, {row.recovery_stage for row in a.authored})
        for authored in a.authored:
            if authored.recovery_stage != "full":
                self.assertIn("に目が留まり、それを大切に思っています", authored.text)
                self.assertNotIn("受け止めたいです", authored.text)
        for old, new in (
            ("見過ごさず、", ""), ("見過ごさず、", "見過ごして、"),
            ("大切に", ""), ("受け止めています", "思っています"),
            ("受け止めています", "受け止めていません"),
            (action + "こと", action + "ことと" + action + "こと"),
            (action + "ことを", "別の行動を"),
        ):
            with self.subTest(new=new):
                body = _tamper_reception(a.surface.text, old, new)
                self.assertNotEqual(body, a.surface.text)
                self.assertFalse(evaluate_grounded_surface_body_inverse(
                    body=body.encode(), plan=a.plan, sentence_plan=a.sentence_plan,
                    resolver=a.resolver, selected_subjective_input=a.selected_subjective_input).passed)
                self.assertFalse(evaluate_grounded_observation_gate(
                    plan=a.plan, sentence_plan=a.sentence_plan,
                    surface_result=replace(a.surface, text=body), resolver=a.resolver,
                    require_body_inverse=True, selected_subjective_input=a.selected_subjective_input).passed)

    def test_material_attention_preserves_other_roles_profiles_and_selected_operations(self):
        kw = next(k for k in self.predicates["qualified"] if k["recovery_stage"] == "full")
        render = reception_owner._source_grounded_response_predicate_surface
        profile = kw["semantic_profile"]
        decision = kw["selected_subjective_decision"]
        prop = decision.subjective_proposition
        self.assertEqual(profile.modality, "fact")
        self.assertIn("を見過ごさず、大切に受け止めています", render(**kw))
        other_appraisal = replace(decision, subjective_proposition=replace(prop,
            appraisal_content=replace(prop.appraisal_content,
                dimension=contracts_owner.AppraisalDimension.RELATIONAL_NONCOLLAPSE,
                operation=contracts_owner.AppraisalOperation.PRESERVE_BOTH_ENDPOINTS)))
        variants = [
            {"single_target_object": False}, {"move_role": "felt_response"},
            {"move_role": "significance"},
            {"semantic_profile": replace(profile, quoted_boundary=True)},
            {"semantic_profile": replace(profile, modality="uncertain")},
            {"selected_subjective_decision": other_appraisal},
            {"future_action": True, "voice": "FUTURE_INTENTION",
             "referent_kind": "future_action_intention", "target_predicate_kind": "present_direction",
             "semantic_profile": replace(profile, performed_action=False, future_action=True, modality="intention")},
        ]
        for update in variants:
            with self.subTest(update=update):
                try:
                    text = render(**{**kw, **update})
                except reception_owner.GroundedHumanReceptionSurfaceError:
                    continue
                self.assertNotIn("見過ごさず、大切に受け止め", text)
                self.assertIn("大切に思っています", text)


class CMEENegativeContextNominalTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifacts = {}
        for name, context in (("verb", "今は長く話せなくて"),
                              ("adjective", "今は体調がよくなくて")):
            row = cls._row("この役割を続けたい。でも、" + context + "。")
            cls.artifacts[name] = (context, _full_surface_artifacts(row))

    @staticmethod
    def _row(text):
        return {"case_id": "public-negative-context-grammar", "input": {
            "thought_text": text, "action_text": "", "categories": ["趣味"],
            "emotions": [{"type": "不安", "strength": "medium"}],
        }}

    def test_context_is_inflected_without_losing_its_complete_source_or_relation(self):
        for source, a in self.artifacts.values():
            with self.subTest(source=source):
                nominal = source[:-3] + "ないこと"
                self.assertTrue(a.gate.passed)
                self.assertTrue(a.inverse.passed)
                self.assertEqual(a.sentence_plan.recovery_stage, "full")
                follow = _reception_text(a.surface.text)
                self.assertEqual(follow.count(nominal), 1)
                self.assertIn("この役割を続けたいという願いと", follow)
                self.assertIn("との違いを見失わず", follow)
                self.assertNotIn("なくてということ", follow)
                args, kwargs = a.author_arguments[0]
                self.assertIs(kwargs["selected_subjective_input"], a.selected_subjective_input)
                expressions = args[1]
                self.assertTrue(any(source == arg.lexical_form
                                    for e in expressions for arg in e.arguments))
                self.assertTrue(any("context-slot:1:NEGATIVE_CONTINUATIVE" in e.nominalization_plan
                                    for e in expressions))
                replay = reception_owner.replay_source_grounded_human_reception_from_plan(
                    args[0], args[2], args[3], plan=kwargs["plan"],
                    recovery_stage=kwargs["recovery_stage"], clause_plans=kwargs["clause_plans"],
                    selected_subjective_input=a.selected_subjective_input,
                )
                self.assertEqual(replay.text, a.authored[0].text)

    def test_full_context_witness_rejects_lexical_polarity_time_and_duplicate_tampering(self):
        source, a = self.artifacts["verb"]
        nominal = source[:-3] + "ないこと"
        for replacement in ("話せないこと", "今は長く話せること", "昔は長く話せないこと",
                            "今は短く話せないこと", "今は長く書けないこと",
                            source + "ということ", nominal + "と" + nominal,
                            "「" + nominal + "」", "『" + nominal + "』"):
            with self.subTest(replacement=replacement):
                body = _tamper_reception(a.surface.text, nominal, replacement)
                self.assertNotEqual(body, a.surface.text)
                inverse = evaluate_grounded_surface_body_inverse(
                    body=body.encode("utf-8"), plan=a.plan, sentence_plan=a.sentence_plan,
                    resolver=a.resolver, selected_subjective_input=a.selected_subjective_input,
                )
                self.assertFalse(inverse.passed)
                self.assertTrue(any("context_anchor_missing" in c for c in inverse.failure_codes))
                self.assertTrue(any("why_duty_missing" in c for c in inverse.failure_codes))
                gate = evaluate_grounded_observation_gate(
                    plan=a.plan, sentence_plan=a.sentence_plan,
                    surface_result=replace(a.surface, text=body), resolver=a.resolver,
                    require_body_inverse=True, selected_subjective_input=a.selected_subjective_input,
                )
                self.assertFalse(gate.passed)

    def test_context_grammar_stays_bound_to_its_sealed_slot_and_source_permission(self):
        source, a = self.artifacts["verb"]
        args, kwargs = a.author_arguments[0]
        ir = reception_owner._source_grounded_plan_clause_realizations(
            args[0], args[2], args[3], plan=kwargs["plan"],
            recovery_stage=kwargs["recovery_stage"], clause_plans=kwargs["clause_plans"],
        )[0].moves[0]
        for grammar in ((ir.nominalization_plan[0], "context-slot:0:NEGATIVE_CONTINUATIVE"),
                        (ir.nominalization_plan[0], "context-slot:8:NEGATIVE_CONTINUATIVE"),
                        (ir.nominalization_plan[0], "context-slot:01:NEGATIVE_CONTINUATIVE"),
                        (ir.nominalization_plan[0], "context-slot:" + "1" * 5000 + ":NEGATIVE_CONTINUATIVE"),
                        (*ir.nominalization_plan, ir.nominalization_plan[1])):
            with self.subTest(grammar=grammar):
                with self.assertRaises(reception_owner.GroundedHumanReceptionSurfaceError):
                    reception_owner._validate_source_grounded_move_ir(replace(ir, nominalization_plan=grammar))
        move = args[0].moves[0]
        index = {n.nucleus_id: n for n in a.plan.nuclei}
        context_id = reception_owner.final_reception_context_nucleus_ids(move=move, plan=a.plan)[0]
        nucleus = index[context_id]
        for changes in ({"actor": "other"}, {"modality": "uncertain"}, {"modality": "wish"}):
            altered = replace(nucleus, semantic_frame=replace(nucleus.semantic_frame, **changes))
            self.assertIsNone(reception_owner.source_grounded_negative_context_nominal(
                move, a.plan, {**index, context_id: altered}, a.resolver))
        legacy_plan = replace(a.plan, source_contracts=())
        self.assertIsNone(reception_owner.source_grounded_negative_context_nominal(move, legacy_plan, index, a.resolver))
        self.assertEqual(reception_owner.derive_source_grounded_nominalization_plan(
            tuple(index[nid] for nid in (*move.target_nucleus_ids, context_id)),
            ir.semantic_fragments, "COMPOSITE"), (ir.nominalization_plan[0],))

    def test_alias_uses_existing_source_form_and_invalid_context_fails_closed(self):
        a = _full_surface_artifacts(self._row("話せないことを伝えたい。でも、話せなくて。"))
        self.assertTrue(a.gate.passed)
        self.assertTrue(a.inverse.passed)
        self.assertEqual(a.sentence_plan.recovery_stage, "full")
        self.assertIn("話せなくてということ", _reception_text(a.surface.text))
        self.assertFalse(any(p.startswith("context-slot:") for args, _kwargs in a.author_arguments
                             for e in args[1] for p in e.nominalization_plan))
        source, a = self.artifacts["verb"]
        move = a.plan.response_plan.human_reception_plan.moves[0]
        context_id = reception_owner.final_reception_context_nucleus_ids(move=move, plan=a.plan)[0]
        invalid = replace(a.plan, nuclei=tuple(replace(n, source_span_ids=("s99999",))
                          if n.nucleus_id == context_id else n for n in a.plan.nuclei))
        inverse = evaluate_grounded_surface_body_inverse(
            body=a.surface.text.encode("utf-8"), plan=invalid, sentence_plan=a.sentence_plan,
            resolver=a.resolver, selected_subjective_input=a.selected_subjective_input,
        )
        self.assertFalse(inverse.passed)
        self.assertTrue(any("context_anchor_missing" in c for c in inverse.failure_codes))
        self.assertTrue(any("why_duty_missing" in c for c in inverse.failure_codes))

    def test_visible_quote_ellipsis_and_past_context_keep_their_existing_forms(self):
        for prefix, context in (("見出しは「休憩」です。", "今は長く話せなくて"),
                                ("", "今は長く話せなくて…"),
                                ("", "今は長く話せなかった")):
            with self.subTest(prefix=prefix, context=context):
                a = _full_surface_artifacts(self._row(prefix + "この役割を続けたい。でも、" + context + "。"))
                self.assertTrue(a.inverse.passed)
                self.assertTrue(a.gate.passed)
                self.assertIn(context, _reception_text(a.surface.text))
                self.assertNotIn("今は長く話せないこと", _reception_text(a.surface.text))
                self.assertFalse(any(p.startswith("context-slot:")
                                     for args, _kwargs in a.author_arguments
                                     for e in args[1] for p in e.nominalization_plan))


class CMEENegativeFeelingReferentTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifacts = tuple((source, nominal, _full_surface_artifacts({
            "case_id": "public-negative-feeling-referent", "input": {
                "thought_text": source + "。", "action_text": "", "categories": ["生活"],
                "emotions": [{"type": "不安", "strength": "weak"}],
            },
        })) for source, nominal in (
            ("どことなく、落ち着かない", "どことなくの落ち着かなさ"),
            ("なんとなく感じない", "なんとなくの感じなさ"),
            ("漠然と、焦らない", "漠然とした焦らなさ"),
        ))

    def test_existing_nominal_is_one_target_and_replays_same_selected_input(self):
        for source, nominal, a in self.artifacts:
            with self.subTest(source=source):
                follow = _reception_text(a.surface.text)
                self.assertTrue(a.gate.passed, a.gate.rejection_reasons)
                self.assertTrue(a.inverse.passed, a.inverse.failure_codes)
                self.assertEqual(follow.count(nominal), 1)
                self.assertNotIn("今ここに置かれた言葉", follow)
                self.assertNotIn("について", follow)
                self.assertIn(nominal + "を小さくせずに受け止めています", follow)
                plan = a.plan.response_plan.human_reception_plan
                line = next(line for line in a.sentence_plan.lines if line.binding.line_role == "human_follow")
                replay = reception_owner.replay_source_grounded_human_reception_from_plan(
                    plan, {n.nucleus_id: n for n in a.plan.nuclei}, a.resolver,
                    plan=a.plan, recovery_stage=a.sentence_plan.recovery_stage,
                    clause_plans=line.reception_clause_plans,
                    selected_subjective_input=a.selected_subjective_input,
                )
                self.assertEqual(replay.text, follow.strip())
                self.assertTrue(all(kw["selected_subjective_input"] is a.selected_subjective_input
                                    for _args, kw in a.author_arguments))
                self.assertTrue(all(e.nominalization_plan[1].startswith("nominal-slot:0:NEGATIVE_FEELING_CARRIER:")
                                    for args, _kw in a.author_arguments for e in args[1]))

    def test_inverse_binds_whole_nominal_and_rejects_changed_responsibility(self):
        source, nominal, a = self.artifacts[0]
        for replacement in (
            "落ち着かなさ", "どことなくの落ち着き", "なんとなくの落ち着かなさ",
            "別の感じなさ", "今ここに置かれた言葉", "別の感じなさについて、今ここに置かれた言葉", source,
            "「" + nominal + "」", "『" + nominal + "』", nominal + "と" + nominal,
        ):
            with self.subTest(replacement=replacement):
                body = _tamper_reception(a.surface.text, nominal, replacement)
                inverse = evaluate_grounded_surface_body_inverse(
                    body=body.encode("utf-8"), plan=a.plan, sentence_plan=a.sentence_plan,
                    resolver=a.resolver, selected_subjective_input=a.selected_subjective_input,
                )
                self.assertFalse(inverse.passed)
                self.assertTrue(any("target_duty_missing" in c for c in inverse.failure_codes))
        body = _tamper_reception(a.surface.text, "小さくせずに受け止めています", "小さなことだと考えています")
        self.assertFalse(reception_owner._source_grounded_burden_nominal_responsibility(body, nominal))
        self.assertFalse(evaluate_grounded_surface_body_inverse(
            body=body.encode("utf-8"), plan=a.plan, sentence_plan=a.sentence_plan,
            resolver=a.resolver, selected_subjective_input=a.selected_subjective_input,
        ).passed)
        body = _tamper_reception(a.surface.text, nominal, source + "、" + nominal)
        inverse = evaluate_grounded_surface_body_inverse(
            body=body.encode("utf-8"), plan=a.plan, sentence_plan=a.sentence_plan,
            resolver=a.resolver, selected_subjective_input=a.selected_subjective_input,
        )
        self.assertFalse(inverse.passed)
        self.assertTrue(any("anaphoric_target_replayed" in c for c in inverse.failure_codes))

    def test_suffix_witness_is_reception_scoped_without_burden_classification(self):
        _source, nominal, a = self.artifacts[0]
        body = a.surface.text.encode("utf-8")
        witness = surface_owner.parse_grounded_surface_body_bytes(body)
        markers = [m for m in witness.markers if m.marker_code == "negative_carrier_nominal"]
        end = body.index(nominal.encode("utf-8")) + len(nominal.encode("utf-8"))
        self.assertTrue(any(m.utf8_byte_end == end for m in markers))
        self.assertTrue(all(m.section == "reception" and m.marker_kind == "semantic" for m in markers))
        self.assertTrue(all(not {"target_burden", "target_words"}.intersection(s.reception_marker_codes)
                            for s in witness.sentences if s.section == "reception"))

    def test_nominal_requires_final_same_plan_self_and_no_extra_context(self):
        _source, nominal, a = self.artifacts[0]
        reception = a.plan.response_plan.human_reception_plan
        move = reception.moves[0]
        index = {n.nucleus_id: n for n in a.plan.nuclei}
        target = index[move.target_nucleus_ids[0]]
        derive = reception_owner.source_grounded_feeling_target_nominal
        self.assertEqual(derive(move, a.plan, index, a.resolver), nominal)
        self.assertEqual(derive(move, None, index, a.resolver), "")
        self.assertEqual(derive(move, replace(a.plan, source_contracts=()), index, a.resolver), "")
        for changes in ({"actor": "other"}, {"modality": "uncertain"},
                        {"attribute_codes": (*target.semantic_frame.attribute_codes, "quantity:multiple")}):
            changed = replace(target, semantic_frame=replace(target.semantic_frame, **changes))
            plan = replace(a.plan, nuclei=tuple(changed if n == target else n for n in a.plan.nuclei))
            self.assertEqual(derive(move, plan, {**index, target.nucleus_id: changed}, a.resolver), "")
        supported = replace(move, support_nucleus_ids=(a.plan.nuclei[1].nucleus_id,))
        plan = replace(a.plan, response_plan=replace(a.plan.response_plan,
            human_reception_plan=replace(reception, moves=(supported,))))
        self.assertEqual(derive(supported, plan, index, a.resolver), "")
        relation = observation_plan_owner.GroundedSemanticRelation(
            relation_id="public-required-context", type="contrast", from_nucleus_id=target.nucleus_id,
            to_nucleus_id=a.plan.nuclei[1].nucleus_id, source_span_ids=target.source_span_ids,
            grounding_kind="explicit", certainty=1.0, retention="required",
        )
        plan = replace(a.plan, relations=(relation,), coverage_requirements=replace(a.plan.coverage_requirements,
            required_relation_ids=(relation.relation_id,)))
        self.assertEqual(derive(move, plan, index, a.resolver), "")
        kwargs = dict(reception_plan=reception, move=move, nucleus_index=index,
                      resolver=a.resolver, allow_short_anchor=False, allow_anaphoric_topic=True)
        legacy = reception_owner.resolve_grounded_reception_move_referent(**kwargs)
        unbound = reception_owner.resolve_grounded_reception_move_referent(**kwargs, final_source_fidelity=True)
        final = reception_owner.resolve_grounded_reception_move_referent(**kwargs, final_source_fidelity=True, plan=a.plan)
        self.assertEqual(final.kind, "current_expression")
        self.assertEqual(final.text, nominal)
        self.assertNotEqual(legacy.text, nominal)
        self.assertNotEqual(unbound.text, nominal)


if __name__ == "__main__":
    unittest.main()


class CMEEFutureActionNominalTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifacts = {}
        for name, action in (
            ("calendar", "明日の朝は充電器を机から離れた棚へ移す"),
            ("qualified", "明日は会議で使う資料を三ページだけ記録する"),
            ("embedded_negative", "明日は返事を急がずに予定の確認から始める"),
        ):
            row = {"case_id": "public-future-action-nominal-" + name, "input": {
                "action_text": action + "。", "thought_text": "まだ先の見通しは分からない。",
                "categories": ["仕事"], "emotions": [{"type": "不安", "strength": "medium"}],
            }}
            cls.artifacts[name] = (action, _full_surface_artifacts(row))

    def test_future_clause_reaches_body_with_same_status_and_replay(self):
        for name, (action, a) in self.artifacts.items():
            with self.subTest(name=name):
                follow = _reception_text(a.surface.text)
                self.assertTrue(a.gate.passed, a.gate.rejection_reasons)
                self.assertTrue(a.inverse.passed, a.inverse.failure_codes)
                self.assertEqual(a.sentence_plan.recovery_stage, "full")
                self.assertEqual(follow.count(action + "こと"), 1)
                self.assertNotIn("これからの行動", follow)
                self.assertNotIn("実際の行動", follow)
                self.assertIn("目が留まり", follow)
                self.assertIn("大切に思っています", follow)
                plan = a.plan.response_plan.human_reception_plan
                index = {n.nucleus_id: n for n in a.plan.nuclei}
                move = plan.moves[0]
                ref = reception_owner.resolve_grounded_reception_move_referent(
                    plan, move, index, a.resolver, allow_short_anchor=False,
                    final_source_fidelity=True, plan=a.plan,
                )
                self.assertEqual(ref.kind, "future_action_intention")
                self.assertEqual(ref.text, action + "こと")
                target = index[move.target_nucleus_ids[0]]
                self.assertEqual(target.semantic_frame.modality, "intention")
                self.assertEqual(target.semantic_frame.time_scope, "future")
                self.assertNotIn("operator:performed_action", target.semantic_frame.attribute_codes)
                line = next(line for line in a.sentence_plan.lines
                            if line.binding.line_role == "human_follow")
                replay = reception_owner.replay_source_grounded_human_reception_from_plan(
                    plan, index, a.resolver, plan=a.plan,
                    recovery_stage=a.sentence_plan.recovery_stage,
                    clause_plans=line.reception_clause_plans,
                    selected_subjective_input=a.selected_subjective_input,
                )
                self.assertEqual(replay.text, follow.strip())
                self.assertTrue(all(kwargs["selected_subjective_input"] is a.selected_subjective_input
                                    for _args, kwargs in a.author_arguments))

    def test_future_nominal_rejects_target_time_status_and_response_mutations(self):
        mutations = (
            ("calendar", "明日の朝", "昨日の朝"),
            ("calendar", "充電器", "別の道具"),
            ("calendar", "移すこと", "移したこと"),
            ("calendar", "移すこと", "移さないこと"),
            ("qualified", "三ページだけ", "全ページ"),
            ("embedded_negative", "急がずに", "急いで"),
            ("calendar", "目が留まり", "目に入りませんが"),
            ("calendar", "大切に思っています", "大切ではありません"),
        )
        for name, old, new in mutations:
            with self.subTest(name=name, old=old):
                _action, a = self.artifacts[name]
                body = _tamper_reception(a.surface.text, old, new)
                inverse = evaluate_grounded_surface_body_inverse(
                    body=body.encode("utf-8"), plan=a.plan, sentence_plan=a.sentence_plan,
                    resolver=a.resolver, selected_subjective_input=a.selected_subjective_input,
                )
                self.assertFalse(inverse.passed)
                gate = evaluate_grounded_observation_gate(
                    plan=a.plan, sentence_plan=a.sentence_plan,
                    surface_result=replace(a.surface, text=body), resolver=a.resolver,
                    require_body_inverse=True, selected_subjective_input=a.selected_subjective_input,
                )
                self.assertFalse(gate.passed)

    def test_future_nominal_requires_whole_unquoted_exact_once_target(self):
        action, a = self.artifacts["calendar"]
        nominal = action + "こと"
        for replacement in (
            "別の棚へ移すこと", "これからの行動", "実際の行動",
            "「" + nominal + "」", "『" + nominal + "』", nominal + "と" + nominal,
        ):
            with self.subTest(replacement=replacement):
                changed = _tamper_reception(a.surface.text, nominal, replacement)
                inverse = evaluate_grounded_surface_body_inverse(
                    body=changed.encode("utf-8"), plan=a.plan, sentence_plan=a.sentence_plan,
                    resolver=a.resolver, selected_subjective_input=a.selected_subjective_input,
                )
                self.assertFalse(inverse.passed)
                self.assertTrue(any("target_duty_missing" in code for code in inverse.failure_codes))

    def test_future_nominal_keeps_source_proof_and_grammar_boundaries(self):
        action, a = self.artifacts["calendar"]
        plan = a.plan.response_plan.human_reception_plan
        move = plan.moves[0]
        index = {n.nucleus_id: n for n in a.plan.nuclei}
        target = index[move.target_nucleus_ids[0]]
        derive = reception_owner.source_grounded_future_action_nominal
        self.assertEqual(derive(move, index, a.resolver), action + "こと")
        for changes in (
            {"actor": "other"}, {"actor": "unknown"}, {"modality": "uncertain"},
            {"modality": "wish"}, {"modality": "fact"}, {"time_scope": "past"},
            {"attribute_codes": tuple(c for c in target.semantic_frame.attribute_codes
                                      if c != "semantic_role:next_intention")},
            {"attribute_codes": (*target.semantic_frame.attribute_codes, "operator:performed_action")},
            {"attribute_codes": (*target.semantic_frame.attribute_codes, "quantity:multiple")},
        ):
            with self.subTest(changes=changes):
                changed = replace(target, semantic_frame=replace(target.semantic_frame, **changes))
                self.assertEqual(derive(move, {**index, target.nucleus_id: changed}, a.resolver), "")
        for ending in ("読もう", "します", "です", "する予定", "するつもり", "することにした",
                       "するかな", "する、それだけ", "する…", "する？"):
            with self.subTest(ending=ending), patch.object(
                reception_owner, "_source_grounded_clause_candidate", return_value="明日は資料を" + ending,
            ):
                self.assertEqual(derive(move, index, a.resolver), "")
        # Embedded polarity is retained; it cannot cancel the existing outer intention proof.
        changed = replace(target, semantic_frame=replace(target.semantic_frame, polarity="negative"))
        self.assertEqual(derive(move, {**index, target.nucleus_id: changed}, a.resolver), action + "こと")
        self.assertEqual(derive(replace(move, reception_act="protect_retained_intention"), index, a.resolver), "")
        self.assertEqual(derive(replace(move, target_nucleus_ids=(*move.target_nucleus_ids, "foreign")), index, a.resolver), "")
        spans = tuple(a.resolver.resolve_many(a.resolver.span_ids))
        for boundary in ("？", "?", "…", "『引用』", "「引用」"):
            altered = tuple(replace(span, raw_text=span.raw_text + boundary)
                            if span.source_field == "memo_action" else span for span in spans)
            with self.subTest(boundary=boundary), patch.object(
                type(a.resolver), "resolve_many", return_value=altered,
            ):
                self.assertEqual(derive(move, index, a.resolver), "")

    def test_future_nominal_is_not_used_by_legacy_or_anaphoric_references(self):
        action, a = self.artifacts["calendar"]
        plan = a.plan.response_plan.human_reception_plan
        move = plan.moves[0]
        index = {n.nucleus_id: n for n in a.plan.nuclei}
        kwargs = dict(reception_plan=plan, move=move, nucleus_index=index,
                      resolver=a.resolver, allow_short_anchor=False)
        legacy = reception_owner.resolve_grounded_reception_move_referent(**kwargs)
        self.assertNotEqual(legacy.text, action + "こと")
        with patch.object(reception_owner, "reception_effective_move_reference_mode", return_value="anaphoric_first"):
            anaphoric = reception_owner.resolve_grounded_reception_move_referent(**kwargs, final_source_fidelity=True)
        self.assertEqual(anaphoric.kind, "future_action_intention")
        self.assertNotEqual(anaphoric.text, action + "こと")


class CMEEFinalUnfinishedChangeReceptionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifacts = {}
        for name, thought in (
            ("open", "昨日より楽になったのはなぜだろう。"),
            ("mixed", "片付いたのに、気分が重くなったのはなぜだろうか。"),
            ("settled", "昨日より楽になった。"),
        ):
            row = {"case_id": "public-unfinished-change-" + name, "input": {
                "thought_text": thought, "action_text": "", "categories": ["生活"],
                "emotions": [{"type": "喜び", "strength": "weak"}],
            }}
            cls.artifacts[name] = _full_surface_artifacts(row)

    def test_existing_change_act_receives_its_unfinished_scope(self):
        for name in ("open", "mixed"):
            a = self.artifacts[name]
            with self.subTest(name=name):
                self.assertTrue(a.gate.passed)
                self.assertTrue(a.inverse.passed)
                self.assertEqual(_reception_text(a.surface.text).strip(),
                                 "結論を急がずに、その変化についてまだ分からないことを受け止めています。")
                moves = a.plan.response_plan.human_reception_plan.moves
                self.assertEqual(len(moves), 1)
                self.assertEqual(moves[0].reception_act, "recognize_lived_change")
                target = next(n for n in a.plan.nuclei if n.nucleus_id == moves[0].target_nucleus_ids[0])
                self.assertEqual(target.semantic_frame.polarity, "positive")
                self.assertEqual(target.semantic_frame.modality, "uncertain")
        settled = self.artifacts["settled"]
        self.assertTrue(settled.gate.passed and settled.inverse.passed)
        self.assertIn("その変化を感じています", _reception_text(settled.surface.text))
        self.assertNotIn("まだ分からない", _reception_text(settled.surface.text))

    def test_whole_unknown_target_and_selected_openness_are_required(self):
        a = self.artifacts["open"]
        target = "その変化についてまだ分からないこと"
        for old, new in (
            (target, "その変化"), (target, "まだ分からないこと"),
            (target, target.replace("分からない", "分かった")),
            (target, "「" + target + "」"), (target, target + "と" + target),
            ("受け止めています", "感じています"),
            ("結論を急がずに、", "結論を出して、"),
        ):
            with self.subTest(old=old, new=new):
                body = _tamper_reception(a.surface.text, old, new)
                inverse = evaluate_grounded_surface_body_inverse(
                    body=body.encode("utf-8"), plan=a.plan, sentence_plan=a.sentence_plan,
                    resolver=a.resolver, selected_subjective_input=a.selected_subjective_input,
                )
                gate = evaluate_grounded_observation_gate(
                    plan=a.plan, sentence_plan=a.sentence_plan, surface_result=replace(a.surface, text=body),
                    resolver=a.resolver, require_body_inverse=True,
                    selected_subjective_input=a.selected_subjective_input,
                )
                self.assertFalse(inverse.passed)
                self.assertFalse(gate.passed)

    def test_grammar_requires_same_single_unquoted_uncertainty_source(self):
        a = self.artifacts["open"]
        rp = a.plan.response_plan.human_reception_plan
        move = rp.moves[0]
        index = {n.nucleus_id: n for n in a.plan.nuclei}
        target = index[move.target_nucleus_ids[0]]
        derive = reception_owner.source_grounded_unfinished_referent
        self.assertEqual(derive(move, a.plan, index, a.resolver), "その変化についてまだ分からないこと")
        for changes in (
            {"actor": "other"}, {"actor": "unknown"}, {"modality": "fact"},
            {"predicate_kind": "change"},
            {"attribute_codes": tuple(c for c in target.semantic_frame.attribute_codes if c != "operator:uncertainty")},
            {"attribute_codes": tuple(c for c in target.semantic_frame.attribute_codes if c != "operator:positive_change")},
            {"attribute_codes": tuple(c for c in target.semantic_frame.attribute_codes if c != "operator:change")},
            {"attribute_codes": (*target.semantic_frame.attribute_codes, "quantity:multiple")},
        ):
            changed = replace(target, semantic_frame=replace(target.semantic_frame, **changes))
            plan = replace(a.plan, nuclei=tuple(changed if n == target else n for n in a.plan.nuclei))
            with self.subTest(changes=changes):
                self.assertEqual(derive(move, plan, {**index, target.nucleus_id: changed}, a.resolver), "")
        for changed_move in (
            replace(move, target_nucleus_ids=(*move.target_nucleus_ids, "foreign")),
            replace(move, support_nucleus_ids=("foreign",)),
            replace(move, reception_act="stay_with_current_burden"),
        ):
            plan = replace(a.plan, response_plan=replace(a.plan.response_plan,
                human_reception_plan=replace(rp, moves=(changed_move,))))
            self.assertEqual(derive(changed_move, plan, index, a.resolver), "")
        spans = tuple(a.resolver.resolve_many(a.resolver.span_ids))
        for boundary in ("『引用』", "「引用」", "…"):
            altered = tuple(replace(span, raw_text=span.raw_text + boundary)
                            if span.source_field == "memo" else span for span in spans)
            with self.subTest(boundary=boundary), patch.object(type(a.resolver), "resolve_many", return_value=altered):
                self.assertEqual(derive(move, a.plan, index, a.resolver), "")
        kwargs = dict(reception_plan=rp, move=move, nucleus_index=index,
                      resolver=a.resolver, allow_short_anchor=False, plan=a.plan)
        legacy = reception_owner.resolve_grounded_reception_move_referent(**kwargs)
        self.assertNotIn("まだ分からない", legacy.text)
        with patch.object(reception_owner, "reception_effective_move_reference_mode", return_value="short_anchor_if_ambiguous"):
            explicit = reception_owner.resolve_grounded_reception_move_referent(**kwargs, final_source_fidelity=True)
        self.assertNotIn("まだ分からない", explicit.text)

    def test_unfinished_predicate_cannot_replace_another_selected_operation(self):
        a = self.artifacts["open"]
        rp = a.plan.response_plan.human_reception_plan
        move = rp.moves[0]
        decision = reception_owner.validate_selected_subjective_reception_input(
            a.selected_subjective_input, rp, a.plan, a.resolver,
        )[move.move_id]
        target = next(n for n in a.plan.nuclei if n.nucleus_id == move.target_nucleus_ids[0])
        profile = reception_owner._source_grounded_semantic_profile(target, "理由はまだ分からない")
        kwargs = dict(future_action=False, target_predicate_kind="present_change", semantic_profile=profile,
                      referent_kind="lived_change", voice="STATE", unfinished_change=True)
        predicate = reception_owner._source_grounded_response_predicate(
            move.reception_act, move.move_role, **kwargs, selected_subjective_decision=decision,
        )
        self.assertEqual(predicate.predicate_lemma, "受け止める")
        for operation in ("RECEIVE_AS_MATERIAL", "RECOGNIZE_AS_BOUNDED", "PRESERVE_BOTH_ENDPOINTS"):
            changed = replace(decision, subjective_proposition=replace(decision.subjective_proposition,
                appraisal_content=replace(decision.subjective_proposition.appraisal_content, operation=operation)))
            with self.subTest(operation=operation), self.assertRaises(reception_owner.GroundedHumanReceptionSurfaceError):
                reception_owner._source_grounded_response_predicate(
                    move.reception_act, move.move_role, **kwargs, selected_subjective_decision=changed,
                )


class CMEEFinalMixedUnfinishedReceptionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifacts = {}
        for name, thought in (
            ("explanation", "説明が伝わったのはうれしい。ただ、どの部分が役に立ったのかは分からない。"),
            ("preparation", "準備が終わってうれしい。でも、本当にこれで十分なのかは分からない。"),
            ("unknown_action", "説明が伝わったのはうれしい。ただ、どの作業を見ていたのかは分からない。"),
            ("settled", "説明が伝わったのはうれしい。どの部分が役に立ったのかも分かった。"),
        ):
            cls.artifacts[name] = _full_surface_artifacts({
                "case_id": "public-mixed-unfinished-" + name, "input": {
                    "thought_text": thought, "action_text": "", "categories": ["生活"],
                    "emotions": [{"type": "喜び", "strength": "medium"}],
                },
            })

    def test_selected_pair_receives_feeling_and_unknown_without_resolving_either(self):
        for name, feeling, unknown in (
            ("explanation", "説明が伝わったのはうれしい", "どの部分が役に立ったのかは分からない"),
            ("preparation", "準備が終わってうれしい", "本当にこれで十分なのかは分からない"),
            ("unknown_action", "説明が伝わったのはうれしい", "どの作業を見ていたのかは分からない"),
        ):
            a = self.artifacts[name]
            with self.subTest(name=name):
                self.assertTrue(a.gate.passed and a.inverse.passed)
                self.assertEqual(_reception_text(a.surface.text).strip(),
                    feeling + "という気持ちと" + unknown + "ことの両方を受け止めています。")
                moves = a.plan.response_plan.human_reception_plan.moves
                self.assertEqual(len(moves), 1)
                self.assertEqual(moves[0].reception_act, "recognize_lived_change")
                decisions = reception_owner.validate_selected_subjective_reception_input(
                    a.selected_subjective_input, a.plan.response_plan.human_reception_plan, a.plan, a.resolver,
                )
                proposition = decisions[moves[0].move_id].subjective_proposition
                self.assertEqual(proposition.appraisal_content.operation, "PRESERVE_BOTH_ENDPOINTS")
                self.assertIsNotNone(proposition.focal_relation_ref)

        a = self.artifacts["unknown_action"]
        move = a.plan.response_plan.human_reception_plan.moves[0]
        context_id = reception_owner.final_reception_context_nucleus_ids(move=move, plan=a.plan)[0]
        context = next(n for n in a.plan.nuclei if n.nucleus_id == context_id)
        self.assertEqual(context.kind, "action")
        self.assertEqual(context.semantic_frame.predicate_kind, "action")
        self.assertEqual(context.semantic_frame.modality, "uncertain")
        self.assertFalse(reception_owner.reception_action_is_performed(context, final_source_fidelity=True))
        self.assertFalse(reception_owner.reception_action_is_future_intention(context, final_source_fidelity=True))
        index = {n.nucleus_id: n for n in a.plan.nuclei}
        for code in ("operator:uncertainty", "semantic_role:limiting_unknown"):
            changed = replace(context, semantic_frame=replace(context.semantic_frame,
                attribute_codes=tuple(c for c in context.semantic_frame.attribute_codes if c != code)))
            changed_plan = replace(a.plan, nuclei=tuple(changed if n == context else n for n in a.plan.nuclei))
            with self.subTest(missing_code=code):
                self.assertEqual(reception_owner._source_grounded_positive_feeling_unfinished_relation(
                    move, changed_plan, {**index, context_id: changed}, a.resolver,
                ), "")

    def test_whole_pair_unknown_polarity_and_selected_reception_survive_inverse(self):
        a = self.artifacts["explanation"]
        for old, new in (
            ("説明が伝わったのはうれしいという気持ち", "その気持ち"),
            ("どの部分が役に立ったのかは分からないこと", "分からないこと"),
            ("分からない", "分かった"), ("の両方", "の片方"),
            ("の両方", ""), ("受け止めています", "感じています"),
            ("説明が伝わったのはうれしい", "相手には説明が伝わったのがうれしい"),
        ):
            with self.subTest(old=old, new=new):
                body = _tamper_reception(a.surface.text, old, new)
                inverse = evaluate_grounded_surface_body_inverse(
                    body=body.encode("utf-8"), plan=a.plan, sentence_plan=a.sentence_plan,
                    resolver=a.resolver, selected_subjective_input=a.selected_subjective_input,
                )
                gate = evaluate_grounded_observation_gate(
                    plan=a.plan, sentence_plan=a.sentence_plan, surface_result=replace(a.surface, text=body),
                    resolver=a.resolver, require_body_inverse=True,
                    selected_subjective_input=a.selected_subjective_input,
                )
                self.assertFalse(inverse.passed)
                self.assertFalse(gate.passed)

    def test_settled_context_does_not_authorize_unfinished_pair_grammar(self):
        a = self.artifacts["settled"]
        self.assertTrue(a.gate.passed and a.inverse.passed)
        self.assertIn("の両方を感じています", _reception_text(a.surface.text))
        body = _tamper_reception(a.surface.text, "感じています", "受け止めています")
        inverse = evaluate_grounded_surface_body_inverse(
            body=body.encode("utf-8"), plan=a.plan, sentence_plan=a.sentence_plan,
            resolver=a.resolver, selected_subjective_input=a.selected_subjective_input,
        )
        self.assertFalse(inverse.passed)
        self.assertFalse(reception_owner._positive_feeling_responsibility(_reception_text(body)))

    def test_unrelated_or_unproven_context_cannot_authorize_receive_responsibility(self):
        a = self.artifacts["explanation"]
        rp = a.plan.response_plan.human_reception_plan
        move = rp.moves[0]
        index = {n.nucleus_id: n for n in a.plan.nuclei}
        derive = reception_owner._source_grounded_positive_feeling_unfinished_relation
        relation_id = derive(move, a.plan, index, a.resolver)
        self.assertTrue(relation_id)
        relation = next(r for r in a.plan.relations if r.relation_id == relation_id)
        context_id = reception_owner.final_reception_context_nucleus_ids(move=move, plan=a.plan)[0]
        context = index[context_id]
        for nucleus in (index[move.target_nucleus_ids[0]], context):
            for actor in ("other", "unknown"):
                changed = replace(nucleus, semantic_frame=replace(nucleus.semantic_frame, actor=actor))
                changed_plan = replace(a.plan, nuclei=tuple(changed if n == nucleus else n for n in a.plan.nuclei))
                with self.subTest(actor=actor, kind=nucleus.kind):
                    self.assertEqual(derive(move, changed_plan, {**index, nucleus.nucleus_id: changed}, a.resolver), "")
        changed = replace(context, semantic_frame=replace(context.semantic_frame, modality="fact"))
        stale_plan = replace(a.plan, nuclei=tuple(changed if n == context else n for n in a.plan.nuclei))
        self.assertEqual(derive(move, stale_plan, index, a.resolver), "")
        self.assertEqual(derive(move, replace(a.plan, nuclei=tuple(changed if n == context else n for n in a.plan.nuclei)),
                                {**index, context_id: changed}, a.resolver), "")
        for changed_relations in (
            (), (replace(relation, type="contrast"),),
            (replace(relation, to_nucleus_id=move.target_nucleus_ids[0]),),
        ):
            with self.subTest(relations=changed_relations):
                self.assertEqual(derive(move, replace(a.plan, relations=changed_relations), index, a.resolver), "")
        no_required = replace(a.plan, coverage_requirements=replace(a.plan.coverage_requirements, required_relation_ids=()))
        self.assertEqual(derive(move, no_required, index, a.resolver), "")
        unrelated = next(n.nucleus_id for n in a.plan.nuclei
                         if n.nucleus_id not in (context_id, *move.target_nucleus_ids))
        changed_move = replace(move, support_nucleus_ids=(unrelated,))
        changed_plan = replace(a.plan, response_plan=replace(a.plan.response_plan,
            human_reception_plan=replace(rp, moves=(changed_move,))))
        self.assertEqual(derive(changed_move, changed_plan, index, a.resolver), "")
        spans = tuple(a.resolver.resolve_many(a.resolver.span_ids))
        altered = tuple(replace(span, raw_text=span.raw_text + "『引用』")
                        if span.source_field == "memo" else span for span in spans)
        with patch.object(type(a.resolver), "resolve_many", return_value=altered):
            self.assertEqual(derive(move, a.plan, index, a.resolver), "")


class CMEEFinalCurrentMoodSourceTest(unittest.TestCase):
    @staticmethod
    def _row(text, emotion="不安"):
        return {"case_id": "public-current-mood-source", "input": {
            "thought_text": text, "action_text": "", "categories": ["生活"],
            "emotions": [{"type": emotion, "strength": "weak"}],
        }}

    @classmethod
    def setUpClass(cls):
        from cocolon_meaning_experience_engine import emlis_stage1_composition
        cls.composition = emlis_stage1_composition
        cls.appraisal_arguments = []
        derive = cls.composition._normal_reception_appraisal
        def track(**kwargs):
            value = derive(**kwargs)
            cls.appraisal_arguments.append(kwargs)
            return value
        with patch.object(cls.composition, "_normal_reception_appraisal", side_effect=track):
            cls.artifacts = tuple(_full_surface_artifacts(cls._row(text)) for text in (
                "今日は気分が軽い。", "今は私の気分が少し軽いです。",
            ))

    def test_current_mood_reaches_feeling_reception_without_change_claim(self):
        for a in self.artifacts:
            with self.subTest(body=a.surface.text):
                self.assertTrue(a.gate.passed, a.gate.rejection_reasons)
                self.assertTrue(a.inverse.passed, a.inverse.failure_codes)
                target = next(n for n in a.plan.nuclei if n.source_fields == ("memo",))
                self.assertTrue(observation_plan_owner.is_grounded_positive_feeling(target))
                self.assertFalse(set(target.semantic_frame.attribute_codes) & {
                    "operator:change", "operator:result", "semantic_role:current_change",
                })
                follow = _reception_text(a.surface.text)
                self.assertIn("気持ち", follow)
                self.assertIn("受け止めています", follow)
                self.assertNotIn("変化", follow)
                self.assertNotIn("小さくせず", follow)
                self.assertEqual(len(a.selected_subjective_input.decisions), 1)
                self.assertEqual(a.selected_subjective_input.decisions[0].reception_act,
                                 "recognize_lived_change")
                self.assertTrue(all(kw["selected_subjective_input"] is a.selected_subjective_input
                                    for _args, kw in a.author_arguments))

    def test_source_proof_preserves_same_owner_and_leaves_base_unchanged(self):
        source, before = CMEEUnresolvedQuestionSourceTest()._source_plan("今日は気分が軽い。")
        target = next(n for n in before.nuclei if n.source_fields == ("memo",))
        self.assertFalse(observation_plan_owner.is_grounded_positive_feeling(target))
        nuclei, dependencies = observation_plan_owner._final_stage1_typed_nuclei(
            before, source.evidence_spans, normalized_input=source.normalized_current_input)
        self.assertEqual(dependencies, ())
        expected = replace(target, kind="reaction", semantic_frame=replace(
            target.semantic_frame, predicate_kind="feeling", polarity="positive", modality="feeling",
            attribute_codes=tuple(dict.fromkeys((*target.semantic_frame.attribute_codes,
                "operator:feeling", "operator:positive_change", "semantic_role:positive_evaluation"))),
        ))
        self.assertEqual(nuclei, tuple(expected if n == target else n for n in before.nuclei))
        for normalized in (None, {**source.normalized_current_input, "memo": "原文と異なる文"}):
            self.assertEqual(observation_plan_owner._final_stage1_typed_nuclei(
                before, source.evidence_spans, normalized_input=normalized)[0], before.nuclei)
        for changes in ({"actor": "other"}, {"time_scope": "past"},
                        {"modality": "uncertain"}, {"modality": "wish"},
                        {"attribute_codes": (*target.semantic_frame.attribute_codes, "semantic_role:limiting_unknown")},
                        {"attribute_codes": (*target.semantic_frame.attribute_codes, "operator:change")}):
            altered = replace(before, nuclei=tuple(replace(n, semantic_frame=replace(
                n.semantic_frame, **changes)) if n == target else n for n in before.nuclei))
            self.assertEqual(observation_plan_owner._final_stage1_typed_nuclei(
                altered, source.evidence_spans, normalized_input=source.normalized_current_input)[0], altered.nuclei)

    def test_full_source_rejects_lost_subject_report_question_and_compound(self):
        source, before = CMEEUnresolvedQuestionSourceTest()._source_plan("今日は気分が軽い。")
        raw = source.normalized_current_input["memo"].rstrip("。")
        for left, right in (("同僚は、", "。"), ("「", "」と話した。"),
                            ("", "？"), ("", "と思った。"), ("", "なら出かける。"),
                            ("外の空気が気持ちよくて、", "。"), ("", "。でも不安だ。")):
            with self.subTest(left=left, right=right):
                spans = tuple(replace(s, start_index=s.start_index + len(left),
                                      end_index=s.end_index + len(left))
                              if s.source_field == "memo" else s for s in source.evidence_spans)
                result, _ = observation_plan_owner._final_stage1_typed_nuclei(
                    before, spans, normalized_input={**source.normalized_current_input,
                        "memo": left + raw + right})
                self.assertEqual(result, before.nuclei)
        for text in ("昨日は気分が軽かった。", "明日は気分が軽い。", "同僚の気分が軽い。",
                     "今日は気分が軽くない。", "今日は気分が軽いかもしれない。",
                     "今日は鞄が軽い。", "今日は気分が軽い…", "今日は気分が軽い？"):
            source, before = CMEEUnresolvedQuestionSourceTest()._source_plan(text)
            result, _ = observation_plan_owner._final_stage1_typed_nuclei(
                before, source.evidence_spans, normalized_input=source.normalized_current_input)
            self.assertFalse(any(observation_plan_owner.is_grounded_positive_feeling(n) for n in result))

    def test_inverse_keeps_feeling_target_and_rejects_burden_or_change_substitution(self):
        a = self.artifacts[0]
        for old, new in (("気持ち", "変化"), ("気持ち", "今ここに置かれた言葉"),
                         ("受け止めています", "小さくせずに受け止めています"),
                         ("受け止めています", "感じています")):
            with self.subTest(new=new):
                body = _tamper_reception(a.surface.text, old, new)
                self.assertNotEqual(body, a.surface.text)
                result = evaluate_grounded_surface_body_inverse(
                    body=body.encode("utf-8"), plan=a.plan, sentence_plan=a.sentence_plan,
                    resolver=a.resolver, selected_subjective_input=a.selected_subjective_input)
                self.assertFalse(result.passed)

    def test_normal_appraisal_requires_its_own_current_positive_feeling_qualifier(self):
        derive = self.composition._normal_reception_appraisal
        self.assertTrue(self.appraisal_arguments)
        args = self.appraisal_arguments[0]
        qualifier = args["source_qualifiers"][0]
        content = derive(**args)
        self.assertEqual(content.operation.value, "RECEIVE_AS_MATERIAL")
        self.assertEqual(content.dimension.value, "MATERIAL_WEIGHT")
        for qualifiers in ((), (qualifier, qualifier),
                           (replace(qualifier, basis_binding_ref="foreign-basis"),),
                           (replace(qualifier, polarity="negative"),),
                           (replace(qualifier, modality="uncertain"),),
                           (replace(qualifier, modality="fact"),),
                           (replace(qualifier, time_scope="past"),),
                           (replace(qualifier, source_argument_role=contracts_owner.ArgumentRole.LEFT),)):
            with self.subTest(qualifiers=qualifiers):
                with self.assertRaises(self.composition.Stage1CompositionError):
                    derive(**{**args, "source_qualifiers": qualifiers})
        row = args["semantic_contributions"][0]
        for changed in (replace(row, semantic_refs=("foreign-semantic",)),
                        replace(row, argument_bindings=tuple(b for b in row.argument_bindings
                                if b.role is not contracts_owner.ArgumentRole.EXPERIENCER)),
                        replace(row, argument_bindings=tuple(replace(b, semantic_ref="foreign-experiencer")
                                if b.role is contracts_owner.ArgumentRole.EXPERIENCER else b
                                for b in row.argument_bindings)),
                        replace(row, semantic_operator=contracts_owner.SemanticOperator.PRESENT_BURDEN)):
            with self.assertRaises(self.composition.Stage1CompositionError):
                derive(**{**args, "semantic_contributions": (changed,), "contributions": (changed,)})


class CMEEFinalSelectedMaterialFeelingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.predicate_arguments = []
        predicate = reception_owner._source_grounded_response_predicate
        def track(reception_act, move_role, **kwargs):
            result = predicate(reception_act, move_role, **kwargs)
            cls.predicate_arguments.append({**kwargs, "reception_act": reception_act, "move_role": move_role})
            return result
        with patch.object(reception_owner, "_source_grounded_response_predicate", side_effect=track):
            cls.a = _full_surface_artifacts(CMEEFinalCurrentMoodSourceTest._row(
                "今日は気分が軽い。"))
            cls.feeling_source = "友人が隣で一緒に図を確認してくれたことがうれしかった"
            row = CMEEFinalCurrentMoodSourceTest._row(
                "週末に取りかかった模型の細かな部品がどうしても組み合わず、手を止めて説明書を読み直していたとき、"
                + cls.feeling_source + "。", emotion="喜び")
            row["input"]["action_text"] = "作業が終わった後、残った部品を袋に入れて道具を箱に戻した。"
            cls.attention = _full_surface_artifacts(row)

    def test_single_material_feeling_shares_one_object_for_attention_and_reception(self):
        a = self.attention
        self.assertTrue(a.gate.passed, a.gate.rejection_reasons)
        self.assertTrue(a.inverse.passed, a.inverse.failure_codes)
        follow = _reception_text(a.surface.text)
        target = self.feeling_source + "という気持ち"
        self.assertIn(target + "を見過ごさず、受け止めています", follow)
        self.assertEqual(follow.count(target), 1)
        self.assertNotIn("それを受け止めています", follow)
        for authored in a.authored:
            if authored.recovery_stage != "full":
                self.assertIn("に目が留まり、それを", authored.text)
                self.assertNotIn("を見過ごさず、", authored.text)
        for old, new in (
            ("を見過ごさず、", "に目が留まり、それを"),
            ("見過ごさず、", ""), ("見過ごさず、", "見過ごして、"),
            (target, "別の気持ち"), (target, target + "と" + target),
            ("受け止めています", "うれしく受け止めています"),
        ):
            with self.subTest(new=new):
                body = _tamper_reception(a.surface.text, old, new)
                self.assertNotEqual(body, a.surface.text)
                self.assertFalse(evaluate_grounded_surface_body_inverse(
                    body=body.encode(), plan=a.plan, sentence_plan=a.sentence_plan,
                    resolver=a.resolver, selected_subjective_input=a.selected_subjective_input).passed)
                self.assertFalse(evaluate_grounded_observation_gate(
                    plan=a.plan, sentence_plan=a.sentence_plan, surface_result=replace(a.surface, text=body),
                    resolver=a.resolver, require_body_inverse=True,
                    selected_subjective_input=a.selected_subjective_input).passed)

    def test_feeling_attention_integration_requires_single_complete_material_target(self):
        kwargs = next(k for k in self.predicate_arguments
                      if k["referent_kind"] == "positive_feeling"
                      and k["move_role"] == "attention" and k["single_target_object"])
        predicate = reception_owner._source_grounded_response_predicate
        actual = predicate(**kwargs)
        self.assertEqual((actual.object_particle, actual.role_operator, actual.valency_complement),
                         ("を", "見過ごさず、", ""))
        decision = kwargs["selected_subjective_decision"]
        prop = decision.subjective_proposition
        different_appraisal = replace(decision, subjective_proposition=replace(prop,
            appraisal_content=replace(prop.appraisal_content,
                dimension=contracts_owner.AppraisalDimension.RELATIONAL_NONCOLLAPSE,
                operation=contracts_owner.AppraisalOperation.PRESERVE_BOTH_ENDPOINTS)))
        for changes in (
            {"single_target_object": False}, {"move_role": "felt_response"},
            {"move_role": "significance"}, {"selected_subjective_decision": different_appraisal},
        ):
            with self.subTest(changes=changes):
                self.assertNotEqual(predicate(**{**kwargs, **changes}).role_operator, "見過ごさず、")

    def test_material_responsibility_requires_the_same_validated_selection(self):
        a = self.a
        surface = next(s for s in a.authored if s.recovery_stage == "full")
        validate = reception_owner.validate_grounded_human_reception_surface
        rp = a.plan.response_plan.human_reception_plan
        self.assertFalse(validate(surface, rp, a.resolver, plan=a.plan,
                                  selected_subjective_input=a.selected_subjective_input))
        self.assertIn("human_reception_act_responsibility_missing:recognize_lived_change",
                      validate(surface, rp, a.resolver, plan=a.plan))
        stale = replace(a.selected_subjective_input, grounding_ref="foreign-grounding")
        self.assertIn("MEANING_REALIZATION_CAUSAL_TRACE_GAP",
                      validate(surface, rp, a.resolver, plan=a.plan, selected_subjective_input=stale))
        changed = replace(surface, text=surface.text.replace("受け止めています", "感じています"))
        self.assertIn("human_reception_act_responsibility_missing:recognize_lived_change",
                      validate(changed, rp, a.resolver, plan=a.plan,
                               selected_subjective_input=a.selected_subjective_input))

    def test_receive_predicate_requires_personal_feeling_state_proof(self):
        kwargs = self.predicate_arguments[0]
        predicate = reception_owner._source_grounded_response_predicate
        self.assertTrue(reception_owner._selected_material_appraisal(kwargs["selected_subjective_decision"]))
        self.assertEqual(predicate(**kwargs).predicate_lemma, "受け止める")
        decision = kwargs["selected_subjective_decision"]
        proposition = decision.subjective_proposition
        appraisal = proposition.appraisal_content
        for changed in (replace(appraisal, dimension=contracts_owner.AppraisalDimension.BOUNDED_CHANGE),
                        replace(appraisal, operation=contracts_owner.AppraisalOperation.RECOGNIZE_AS_BOUNDED), None):
            altered = replace(decision, subjective_proposition=replace(proposition, appraisal_content=changed))
            self.assertFalse(reception_owner._selected_material_appraisal(altered))
        profile = kwargs["semantic_profile"]
        for changes in ({"actor_kind": "OTHER"}, {"actor_kind": "UNSPECIFIED"},
                        {"nucleus_kind": "change"}, {"predicate_kind": "change"},
                        {"modality": "uncertain"}, {"performed_action": True},
                        {"future_action": True}, {"quoted_boundary": True}):
            with self.subTest(changes=changes), self.assertRaises(reception_owner.GroundedHumanReceptionSurfaceError):
                predicate(**{**kwargs, "semantic_profile": replace(profile, **changes)})

    def test_independent_gate_rejects_feeling_experience_and_burden_substitution(self):
        a = self.a
        for replacement in ("感じています", "小さくせずに受け止めています", "うれしく受け止めています"):
            body = _tamper_reception(a.surface.text, "受け止めています", replacement)
            with self.subTest(replacement=replacement):
                self.assertNotEqual(body, a.surface.text)
                self.assertFalse(evaluate_grounded_surface_body_inverse(
                    body=body.encode("utf-8"), plan=a.plan, sentence_plan=a.sentence_plan,
                    resolver=a.resolver, selected_subjective_input=a.selected_subjective_input).passed)
                self.assertFalse(evaluate_grounded_observation_gate(
                    plan=a.plan, sentence_plan=a.sentence_plan, surface_result=replace(a.surface, text=body),
                    resolver=a.resolver, require_body_inverse=True,
                    selected_subjective_input=a.selected_subjective_input).passed)


class CMEEFinalMaterialContrastObjectsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.row = {"case_id": "public-material-contrast", "input": {
            "thought_text": "今日はうれしかった。でも周りに頼った場面も多く、一人の実績として伝えてよいのか迷っている。",
            "action_text": "道具を揃えて展示の準備をした。", "categories": ["学習"],
            "emotions": [{"type": "喜び", "strength": "medium"}],
        }}
        cls.cores, cls.predicates = [], []
        target = reception_owner._source_grounded_target_np
        predicate = reception_owner._source_grounded_response_predicate_surface
        def track_target(move, realization, **kwargs):
            result = target(move, realization, **kwargs)
            if result.pending_relation_slots:
                cls.cores.append((result, realization, kwargs))
            return result
        def track_predicate(reception_act, move_role, **kwargs):
            result = predicate(reception_act, move_role, **kwargs)
            if kwargs.get("pending_relation_slots"):
                cls.predicates.append({"reception_act": reception_act, "move_role": move_role, **kwargs})
            return result
        with patch.object(reception_owner, "_source_grounded_target_np", side_effect=track_target), patch.object(
                reception_owner, "_source_grounded_response_predicate_surface", side_effect=track_predicate):
            cls.a = _full_surface_artifacts(cls.row)

    def test_complete_ordered_objects_and_selected_contrast_are_received_together(self):
        a = self.a
        self.assertTrue(a.gate.passed, a.gate.rejection_reasons)
        self.assertTrue(a.inverse.passed, a.inverse.failure_codes)
        self.assertTrue(self.cores)
        core, realization, kwargs = self.cores[0]
        self.assertEqual(core.relation_count, 0)
        self.assertEqual(core.pending_relation_slots, (0,))
        self.assertEqual(core.semantic_slots, (0, 1))
        self.assertEqual(realization.relations[0].relation_kind, "contrast")
        follow = _reception_text(a.surface.text)
        self.assertIn(core.text + "を見過ごさず、その違いも含めて受け止めています", follow)
        self.assertNotIn("との違いに目が留まり", follow)
        for fragment in realization.semantic_fragments:
            self.assertEqual(core.text.count(fragment), 1)
        self.assertEqual(a.plan.nuclei, _compile_inputs(self.row).grounded_plan.nuclei)
        decision = self.predicates[0]["selected_subjective_decision"]
        self.assertTrue(reception_owner._selected_material_appraisal(decision))
        semantic_map = dict(a.selected_subjective_input.semantic_nucleus_pairs)
        primary = {semantic_map[ref] for ref in decision.subjective_proposition.primary_target_refs}
        appraised = {semantic_map[b.semantic_ref] for b in decision.basis_rows
                     if b.binding_ref in decision.subjective_proposition.appraisal_content.appraised_bindings
                     and b.contribution_ref in decision.selected_contribution_refs}
        relation = next(r for r in a.plan.relations if r.type == "contrast")
        self.assertLessEqual({relation.from_nucleus_id, relation.to_nucleus_id}, primary & appraised)

    def test_independent_replay_rejects_endpoint_contrast_and_reception_loss(self):
        a = self.a
        core, realization, _kwargs = self.cores[0]
        left, right = realization.semantic_fragments
        for old, new in (
            (left, "別の気持ち"), (right, "別のこと"),
            (core.text, core.text.replace(left, "TEMP").replace(right, left).replace("TEMP", right)),
            ("を見過ごさず、", "に目が留まり、"), ("その違いも含めて", ""),
            ("その違いも含めて", "同じものとして"),
            ("受け止めています", "感じています"),
            (core.text + "を見過ごさず、その違いも含めて",
             core.text + "との違いに目が留まり、それを"),
        ):
            with self.subTest(new=new):
                body = _tamper_reception(a.surface.text, old, new)
                self.assertNotEqual(body, a.surface.text)
                self.assertFalse(evaluate_grounded_surface_body_inverse(
                    body=body.encode("utf-8"), plan=a.plan, sentence_plan=a.sentence_plan,
                    resolver=a.resolver, selected_subjective_input=a.selected_subjective_input).passed)
                self.assertFalse(evaluate_grounded_observation_gate(
                    plan=a.plan, sentence_plan=a.sentence_plan, surface_result=replace(a.surface, text=body),
                    resolver=a.resolver, require_body_inverse=True,
                    selected_subjective_input=a.selected_subjective_input).passed)

    def test_pair_attention_uses_one_object_case_only_in_full_recovery(self):
        kw = self.predicates[0]
        core = self.cores[0][0]
        render = reception_owner._source_grounded_response_predicate_surface
        self.assertEqual(kw["recovery_stage"], "full")
        full = render(**kw)
        self.assertEqual(full, core.text + "を見過ごさず、その違いも含めて受け止めています")
        self.assertNotIn("それらを", full)
        self.assertEqual(kw["pending_relation_slots"], (0,))
        for stage in reception_owner._RECOVERY_STAGES:
            if stage == "full":
                continue
            with self.subTest(stage=stage):
                other = render(**{**kw, "recovery_stage": stage})
                self.assertIn(core.text + "に目が留まり、それらを、その違いも含めて", other)
                self.assertNotIn("見過ごさず", other)
        # The pre-body selected input and both appraised endpoints are the
        # same objects consumed by every actual forward/replay recovery.
        self.assertTrue({"full", "hedged"} <= {
            arguments[1]["recovery_stage"] for arguments in self.a.author_arguments
        })
        for _args, kwargs in self.a.author_arguments:
            self.assertIs(kwargs["selected_subjective_input"], self.a.selected_subjective_input)

    def test_pair_attention_loss_and_wrong_object_case_are_rejected(self):
        a = self.a
        for old, new, attention_missing in (
            ("見過ごさず、", "", True),
            ("見過ごさず", "見過ごして", False),
            ("を見過ごさず、", "に目が留まり、", False),
            ("を見過ごさず、", "を見過ごさず、それらを、", False),
        ):
            with self.subTest(new=new):
                body = _tamper_reception(a.surface.text, old, new)
                inverse = evaluate_grounded_surface_body_inverse(
                    body=body.encode(), plan=a.plan, sentence_plan=a.sentence_plan,
                    resolver=a.resolver, selected_subjective_input=a.selected_subjective_input)
                self.assertFalse(inverse.passed)
                if attention_missing:
                    self.assertIn("body_inverse_reception_attention_duty_missing:rm1", inverse.failure_codes)
                self.assertFalse(evaluate_grounded_observation_gate(
                    plan=a.plan, sentence_plan=a.sentence_plan,
                    surface_result=replace(a.surface, text=body), resolver=a.resolver,
                    require_body_inverse=True, selected_subjective_input=a.selected_subjective_input).passed)

    def test_pending_relation_requires_exact_local_completion_and_same_appraisal(self):
        core, realization, target_kwargs = self.cores[0]
        validate = reception_owner._validate_source_grounded_clause_core
        for pending in ((), (False,), [0], (0, 0), (1,)):
            with self.subTest(pending=pending), self.assertRaises(reception_owner.GroundedHumanReceptionSurfaceError):
                validate(replace(core, pending_relation_slots=pending), realization=realization,
                         target_owner_slot=target_kwargs["target_owner_slot"])
        with self.assertRaises(reception_owner.GroundedHumanReceptionSurfaceError):
            validate(replace(core, relation_count=1), realization=realization,
                     target_owner_slot=target_kwargs["target_owner_slot"])
        move = self.a.plan.response_plan.human_reception_plan.moves[0]
        with self.assertRaises(reception_owner.GroundedHumanReceptionSurfaceError):
            reception_owner._source_grounded_reception_fragment(
                replace(move, move_role="bounded_counterposition"), realization,
                context_prefix="", target_core=core, referent_kind="positive_feeling",
                target_owner_slot=target_kwargs["target_owner_slot"], recovery_stage="full",
                selected_subjective_decision=self.predicates[0]["selected_subjective_decision"])
        kwargs = self.predicates[0]
        render = reception_owner._source_grounded_response_predicate_surface
        original = reception_owner._source_grounded_response_predicate
        for completed in ((), (False,), [0], (0, 0), (1,)):
            def wrong_completion(reception_act, move_role, **arguments):
                return replace(original(reception_act, move_role, **arguments), completed_relation_slots=completed)
            with self.subTest(completed=completed), patch.object(
                    reception_owner, "_source_grounded_response_predicate", side_effect=wrong_completion):
                with self.assertRaises(reception_owner.GroundedHumanReceptionSurfaceError):
                    render(**kwargs)
        decision = kwargs["selected_subjective_decision"]
        prop = decision.subjective_proposition
        changed = replace(decision, subjective_proposition=replace(prop, appraisal_content=replace(
            prop.appraisal_content, operation=contracts_owner.AppraisalOperation.PRESERVE_BOTH_ENDPOINTS)))
        for updates in ({"pending_relation_slots": (False,)}, {"pending_relation_slots": (0, 0)},
                        {"selected_subjective_decision": changed}, {"move_role": "felt_response"}):
            with self.subTest(updates=updates), self.assertRaises(reception_owner.GroundedHumanReceptionSurfaceError):
                render(**{**kwargs, **updates})


class CMEEFinalMaterialChangeReceptionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.left = "説明書の細かな記号が分かるようになった"
        cls.right = "それでも小さな部品を一つずつ机に並べて確かめながら組み立てる時間はまだ難しく感じている"
        cls.cases = {}
        for name, thought in (
            ("contrast", "新しい模型に取りかかり、" + cls.left + "けれど、" + cls.right + "。"),
            ("single", cls.left + "。"),
            ("feeling", "小さな文字が読みにくくて不安になったけれど、それでも道具を持ち替えて作業する時間は楽しかった。"),
        ):
            cores, predicates = [], []
            target = reception_owner._source_grounded_target_np
            predicate = reception_owner._source_grounded_response_predicate_surface
            def track_target(move, realization, **kwargs):
                result = target(move, realization, **kwargs)
                if move.reception_act == "recognize_lived_change":
                    cores.append((result, realization))
                return result
            def track_predicate(reception_act, move_role, **kwargs):
                result = predicate(reception_act, move_role, **kwargs)
                if reception_act == "recognize_lived_change":
                    predicates.append({"reception_act": reception_act, "move_role": move_role, **kwargs})
                return result
            with patch.object(reception_owner, "_source_grounded_target_np", side_effect=track_target), patch.object(
                    reception_owner, "_source_grounded_response_predicate_surface", side_effect=track_predicate):
                a = _full_surface_artifacts({"case_id": "public-material-change-" + name, "input": {
                    "thought_text": thought, "action_text": "道具を箱に戻した。", "categories": ["趣味"],
                    "emotions": [{"type": "不安", "strength": "medium"}],
                }})
            cls.cases[name] = (a, cores, predicates)

    def test_appraised_change_and_context_are_received_with_their_contrast(self):
        a, cores, predicates = self.cases["contrast"]
        self.assertTrue(a.gate.passed and a.inverse.passed)
        core, realization = cores[0]
        self.assertEqual(core.text, self.left + "という変化と" + self.right + "こと")
        self.assertEqual((core.semantic_slots, core.relation_count, core.pending_relation_slots), ((0, 1), 0, (0,)))
        self.assertEqual(realization.relations[0].relation_kind, "contrast")
        follow = _reception_text(a.surface.text)
        self.assertIn(core.text + "を見過ごさず、その違いも含めて受け止めています", follow)
        self.assertEqual(follow.count("変化"), 1)
        self.assertNotIn("との違いに目が留まり", follow)
        decision = predicates[0]["selected_subjective_decision"]
        self.assertTrue(reception_owner._selected_material_appraisal(decision))
        sm = dict(a.selected_subjective_input.semantic_nucleus_pairs)
        prop = decision.subjective_proposition
        bound = {sm[b.semantic_ref] for b in decision.basis_rows
                 if b.contribution_ref in decision.selected_contribution_refs
                 and b.semantic_ref in prop.primary_target_refs
                 and b.binding_ref in prop.appraisal_content.appraised_bindings}
        relation = next(r for r in a.plan.relations if r.type == "contrast")
        self.assertLessEqual({relation.from_nucleus_id, relation.to_nucleus_id}, bound)
        for old, new in (
            (self.left, "別の出来事"), (self.right, "別の状況"),
            (self.right, self.right.replace("難しく感じている", "簡単に感じている")),
            (core.text, self.right + "ことと" + self.left + "という変化"),
            ("という変化", "ということ"), ("を見過ごさず、", "に目が留まり、"),
            ("その違いも含めて", ""), ("その違いも含めて", "同じものとして"),
            ("受け止めています", "感じています"), ("受け止めています", "受け止めていました"),
            ("受け止めています", "受け止めていません"),
            (core.text, "「" + core.text + "」"), (core.text, core.text + "と" + core.text),
        ):
            with self.subTest(new=new):
                body = _tamper_reception(a.surface.text, old, new)
                self.assertFalse(evaluate_grounded_surface_body_inverse(
                    body=body.encode(), plan=a.plan, sentence_plan=a.sentence_plan, resolver=a.resolver,
                    selected_subjective_input=a.selected_subjective_input).passed)
                self.assertFalse(evaluate_grounded_observation_gate(
                    plan=a.plan, sentence_plan=a.sentence_plan, surface_result=replace(a.surface, text=body),
                    resolver=a.resolver, require_body_inverse=True,
                    selected_subjective_input=a.selected_subjective_input).passed)

    def test_material_receive_keeps_change_profile_and_bounded_recognition_distinct(self):
        render = reception_owner._source_grounded_response_predicate_surface
        for name, expected_profile in (("single", ("change", "fact")), ("feeling", ("feeling", "feeling"))):
            a, _cores, predicates = self.cases[name]
            with self.subTest(name=name):
                self.assertTrue(a.gate.passed and a.inverse.passed)
                self.assertIn("を見過ごさず、受け止めています", _reception_text(a.surface.text))
                kw = predicates[0]
                profile = kw["semantic_profile"]
                self.assertEqual((profile.predicate_kind, profile.modality), expected_profile)
                decision = kw["selected_subjective_decision"]
                prop = decision.subjective_proposition
                bounded = replace(decision, subjective_proposition=replace(prop, appraisal_content=replace(
                    prop.appraisal_content, dimension=contracts_owner.AppraisalDimension.BOUNDED_CHANGE,
                    operation=contracts_owner.AppraisalOperation.RECOGNIZE_AS_BOUNDED)))
                self.assertIn("それを感じています", render(**{**kw, "selected_subjective_decision": bounded}))
                body = _tamper_reception(a.surface.text, "受け止めています", "感じています")
                self.assertFalse(evaluate_grounded_surface_body_inverse(
                    body=body.encode(), plan=a.plan, sentence_plan=a.sentence_plan, resolver=a.resolver,
                    selected_subjective_input=a.selected_subjective_input).passed)
        kw = self.cases["contrast"][2][0]
        profile = kw["semantic_profile"]
        decision = kw["selected_subjective_decision"]
        prop = decision.subjective_proposition
        bounded = replace(decision, subjective_proposition=replace(prop, appraisal_content=replace(
            prop.appraisal_content, dimension=contracts_owner.AppraisalDimension.BOUNDED_CHANGE,
            operation=contracts_owner.AppraisalOperation.RECOGNIZE_AS_BOUNDED)))
        updates = [{"selected_subjective_decision": bounded}, {"move_role": "felt_response"},
                   {"pending_relation_slots": (False,)}, {"pending_relation_slots": (1,)},
                   {"distributive_object": True}, {"unfinished_change": True}, {"unfinished_pair": True}]
        updates.extend({"semantic_profile": replace(profile, **change)} for change in (
            {"nucleus_kind": "reaction"}, {"predicate_kind": "uncertainty"}, {"modality": "uncertain"},
            {"actor_kind": "OTHER"}, {"quoted_boundary": True}, {"performed_action": True}, {"future_action": True},
        ))
        for update in updates:
            with self.subTest(update=update), self.assertRaises(reception_owner.GroundedHumanReceptionSurfaceError):
                render(**{**kw, **update})


    def test_single_material_change_keeps_the_whole_source_as_one_change(self):
        for name in ("single", "feeling"):
            a, cores, _predicates = self.cases[name]
            core, realization = cores[0]
            with self.subTest(name=name):
                self.assertEqual(len(realization.semantic_fragments), 1)
                source = realization.semantic_fragments[0]
                self.assertEqual(core.text, source + "という変化")
                self.assertEqual((core.relation_count, core.pending_relation_slots), (0, ()))
                follow = _reception_text(a.surface.text)
                self.assertEqual(follow.count(source), 1)
                self.assertEqual(follow.count("変化"), 1)
                self.assertNotIn("ことに表れた変化", follow)
                self.assertIn(core.text + "を見過ごさず、受け止めています", follow)
                self.assertNotIn("それを受け止めています", follow)
                for replacement in (
                    source + "ことに表れた変化", source + "ということ",
                    source + "という願い", "別の出来事という変化",
                    "「" + source + "」という変化",
                ):
                    body = _tamper_reception(a.surface.text, core.text, replacement)
                    self.assertNotEqual(body, a.surface.text)
                    self.assertFalse(evaluate_grounded_surface_body_inverse(
                        body=body.encode(), plan=a.plan, sentence_plan=a.sentence_plan,
                        resolver=a.resolver, selected_subjective_input=a.selected_subjective_input).passed)
                    self.assertFalse(evaluate_grounded_observation_gate(
                        plan=a.plan, sentence_plan=a.sentence_plan,
                        surface_result=replace(a.surface, text=body), resolver=a.resolver,
                        require_body_inverse=True, selected_subjective_input=a.selected_subjective_input).passed)

    def test_single_material_change_keeps_attention_duty_and_recovery_boundary(self):
        render = reception_owner._source_grounded_response_predicate_surface
        for name in ("single", "feeling"):
            a, cores, predicates = self.cases[name]
            kw = next(k for k in predicates if k["recovery_stage"] == "full")
            for changes in ({"single_target_object": False}, {"move_role": "felt_response"},
                            {"move_role": "significance"}, {"recovery_stage": "hedged", "single_target_object": False}):
                with self.subTest(name=name, changes=changes):
                    self.assertNotIn("を見過ごさず、", render(**{**kw, **changes}))
            for authored in a.authored:
                if authored.recovery_stage != "full":
                    self.assertIn("に目が留まり、それを", authored.text)
                    self.assertNotIn("を見過ごさず、", authored.text)
            for replacement in ("に目が留まり、それを", "を", "を見過ごして、"):
                with self.subTest(name=name, replacement=replacement):
                    body = _tamper_reception(a.surface.text, "を見過ごさず、", replacement)
                    self.assertNotEqual(body, a.surface.text)
                    self.assertFalse(evaluate_grounded_surface_body_inverse(
                        body=body.encode(), plan=a.plan, sentence_plan=a.sentence_plan,
                        resolver=a.resolver, selected_subjective_input=a.selected_subjective_input).passed)
                    self.assertFalse(evaluate_grounded_observation_gate(
                        plan=a.plan, sentence_plan=a.sentence_plan, surface_result=replace(a.surface, text=body),
                        resolver=a.resolver, require_body_inverse=True,
                        selected_subjective_input=a.selected_subjective_input).passed)


class CMEEFinalMaterialWishContrastTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.row = {"case_id": "public-material-wish-contrast", "input": {
            "thought_text": "この役割を続けたい。でも、今は困っています。",
            "action_text": "道具を箱に戻した。", "categories": ["趣味"],
            "emotions": [{"type": "不安", "strength": "medium"}],
        }}
        cls.cores, cls.predicates = [], []
        target = reception_owner._source_grounded_target_np
        predicate = reception_owner._source_grounded_response_predicate_surface
        def track_target(move, realization, **kwargs):
            result = target(move, realization, **kwargs)
            if result.pending_relation_slots:
                cls.cores.append((result, realization, kwargs))
            return result
        def track_predicate(reception_act, move_role, **kwargs):
            result = predicate(reception_act, move_role, **kwargs)
            if kwargs.get("pending_relation_slots"):
                cls.predicates.append({"reception_act": reception_act, "move_role": move_role, **kwargs})
            return result
        with patch.object(reception_owner, "_source_grounded_target_np", side_effect=track_target), patch.object(
                reception_owner, "_source_grounded_response_predicate_surface", side_effect=track_predicate):
            cls.a = _full_surface_artifacts(cls.row)

    def test_complete_wish_and_context_keep_their_contrast_and_protection_duty(self):
        a = self.a
        self.assertTrue(a.gate.passed, a.gate.rejection_reasons)
        self.assertTrue(a.inverse.passed, a.inverse.failure_codes)
        self.assertTrue(self.cores)
        core, realization, _kwargs = self.cores[0]
        self.assertEqual(core.semantic_slots, (0, 1))
        self.assertEqual(core.relation_count, 0)
        self.assertEqual(core.pending_relation_slots, (0,))
        self.assertEqual(realization.relations[0].relation_kind, "contrast")
        follow = _reception_text(a.surface.text)
        self.assertIn(core.text + "を見過ごさず、その違いも含めて見失わずに、大切に受け止めています", follow)
        self.assertNotIn("との違いに目が留まり", follow)
        left, right = realization.semantic_fragments
        for fragment in (left, right):
            self.assertEqual(core.text.count(fragment), 1)
        decision = self.predicates[0]["selected_subjective_decision"]
        self.assertTrue(reception_owner._selected_material_appraisal(decision))
        semantic_map = dict(a.selected_subjective_input.semantic_nucleus_pairs)
        primary = {semantic_map[ref] for ref in decision.subjective_proposition.primary_target_refs}
        appraised = {semantic_map[b.semantic_ref] for b in decision.basis_rows
                     if b.binding_ref in decision.subjective_proposition.appraisal_content.appraised_bindings
                     and b.contribution_ref in decision.selected_contribution_refs}
        relation = next(r for r in a.plan.relations if r.type == "contrast")
        self.assertLessEqual({relation.from_nucleus_id, relation.to_nucleus_id}, primary & appraised)
        for old, new in (
            (left, "別の願い"), (right, "別の状況"),
            (core.text, core.text.replace(left, "TEMP").replace(right, left).replace("TEMP", right)),
            ("を見過ごさず、", "に目が留まり、"), ("その違いも含めて", ""),
            ("その違いも含めて", "同じものとして"),
            ("見失わずに、大切に", ""), ("見失わずに、大切に", "大切に"),
            ("受け止めています", "受け止めていました"),
            ("受け止めています", "受け止めていません"),
            (core.text + "を見過ごさず、その違いも含めて",
             core.text + "との違いに目が留まり、それを"),
        ):
            with self.subTest(new=new):
                body = _tamper_reception(a.surface.text, old, new)
                self.assertNotEqual(body, a.surface.text)
                self.assertFalse(evaluate_grounded_surface_body_inverse(
                    body=body.encode("utf-8"), plan=a.plan, sentence_plan=a.sentence_plan,
                    resolver=a.resolver, selected_subjective_input=a.selected_subjective_input).passed)
                self.assertFalse(evaluate_grounded_observation_gate(
                    plan=a.plan, sentence_plan=a.sentence_plan, surface_result=replace(a.surface, text=body),
                    resolver=a.resolver, require_body_inverse=True,
                    selected_subjective_input=a.selected_subjective_input).passed)

    def test_pending_contrast_is_limited_to_the_same_selected_self_wish(self):
        kwargs = self.predicates[0]
        render = reception_owner._source_grounded_response_predicate_surface
        self.assertEqual(kwargs["reception_act"], "protect_retained_intention")
        self.assertEqual(kwargs["referent_kind"], "retained_wish")
        decision = kwargs["selected_subjective_decision"]
        prop = decision.subjective_proposition
        changed = replace(decision, subjective_proposition=replace(prop, appraisal_content=replace(
            prop.appraisal_content, operation=contracts_owner.AppraisalOperation.PRESERVE_BOTH_ENDPOINTS)))
        profile = kwargs["semantic_profile"]
        updates = [
            {"selected_subjective_decision": changed}, {"move_role": "felt_response"},
            {"distributive_object": True}, {"unfinished_change": True}, {"unfinished_pair": True},
            {"pending_relation_slots": (False,)}, {"pending_relation_slots": (0, 0)},
            {"pending_relation_slots": (1,)}, {"voice": "FUTURE_INTENTION"},
        ]
        updates.extend({"semantic_profile": replace(profile, **field)} for field in (
            {"nucleus_kind": "reaction"}, {"modality": "uncertain"}, {"actor_kind": "OTHER"},
            {"performed_action": True}, {"future_action": True}, {"quoted_boundary": True},
        ))
        for update in updates:
            with self.subTest(update=update), self.assertRaises(reception_owner.GroundedHumanReceptionSurfaceError):
                render(**{**kwargs, **update})
        original = reception_owner._source_grounded_response_predicate
        for completed in ((), (False,), [0], (0, 0), (1,)):
            def wrong_completion(reception_act, move_role, **arguments):
                return replace(original(reception_act, move_role, **arguments), completed_relation_slots=completed)
            with self.subTest(completed=completed), patch.object(
                    reception_owner, "_source_grounded_response_predicate", side_effect=wrong_completion):
                with self.assertRaises(reception_owner.GroundedHumanReceptionSurfaceError):
                    render(**kwargs)


class CMEEFinalCurrentExpressionNominalTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = "何を変えたいのかはまだ分からない"
        cls.context = "以前より楽にはなった"
        cls.row = {"case_id": "public-quotative-expression", "input": {
            "thought_text": cls.context + "。でも" + cls.source + "。",
            "action_text": "", "categories": ["学習"],
            "emotions": [{"type": "不安", "strength": "medium"}],
        }}
        cls.cores, cls.predicates = [], []
        target = reception_owner._source_grounded_target_np
        predicate = reception_owner._source_grounded_response_predicate_surface
        def track_target(move, realization, **kwargs):
            result = target(move, realization, **kwargs)
            if result.pending_relation_slots:
                cls.cores.append((result, realization, kwargs))
            return result
        def track_predicate(reception_act, move_role, **kwargs):
            result = predicate(reception_act, move_role, **kwargs)
            if kwargs.get("pending_relation_slots"):
                cls.predicates.append({"reception_act": reception_act, "move_role": move_role, **kwargs})
            return result
        with patch.object(reception_owner, "_source_grounded_target_np", side_effect=track_target), patch.object(
                reception_owner, "_source_grounded_response_predicate_surface", side_effect=track_predicate):
            cls.a = _full_surface_artifacts(cls.row)

    def test_complete_expression_and_selected_relation_reach_same_reception(self):
        a = self.a
        self.assertTrue(a.gate.passed, a.gate.rejection_reasons)
        self.assertTrue(a.inverse.passed, a.inverse.failure_codes)
        self.assertEqual(a.sentence_plan.recovery_stage, "full")
        nominal = self.source + "という言葉"
        follow = _reception_text(a.surface.text)
        self.assertEqual(follow.count(nominal), 1)
        self.assertNotIn("置かれた言葉", follow)
        self.assertIn(self.context + "ことと" + nominal + "の両方", follow)
        self.assertIn("の両方を、その違いも含めて小さくせずに受け止めています", follow)
        self.assertNotIn("との違いを", follow)
        plan = a.plan.response_plan.human_reception_plan
        self.assertEqual(len(plan.moves), 1)
        move = plan.moves[0]
        self.assertEqual(move.reception_act, "stay_with_current_burden")
        self.assertEqual(move.reference_mode, "short_anchor_if_ambiguous")
        index = {n.nucleus_id: n for n in a.plan.nuclei}
        ref = reception_owner.resolve_grounded_reception_move_referent(
            plan, move, index, a.resolver, allow_short_anchor=False,
            final_source_fidelity=True, plan=a.plan,
        )
        self.assertEqual((ref.kind, ref.text, ref.source_anchor_used),
                         ("current_expression", nominal, False))
        self.assertEqual(reception_owner._source_grounded_referent_predicate_kind(ref.kind), "source_bounded")
        self.assertEqual(a.plan.nuclei, _compile_inputs(self.row).grounded_plan.nuclei)

    def test_expression_suffix_context_and_reception_duties_survive_inverse(self):
        a = self.a
        nominal = self.source + "という言葉"
        for old, new in (
            (nominal, self.source + "こと"),
            (nominal, self.source + "ということ"),
            (nominal, "その言葉"),
            (nominal, "分かったという言葉"),
            (nominal, self.source.replace("分からない", "分からなかった") + "という言葉"),
            (nominal, "別のことという言葉"),
            (nominal, "「" + nominal + "」"), (nominal, "『" + nominal + "』"),
            (nominal, nominal + "と" + nominal),
            (self.context + "こと", "別のこと"),
            ("その違いも含めて", "同じこととして"),
            ("その違いも含めて", ""), ("の両方", "の片方"),
            ("の両方を、その違いも含めて", "との違いをどちらの側も残したまま、"),
            (self.context + "ことと" + nominal, nominal + "と" + self.context + "こと"),
            ("小さくせずに", "小さく扱って"),
            ("受け止めています", "感じています"),
        ):
            with self.subTest(replacement=new):
                body = _tamper_reception(a.surface.text, old, new)
                self.assertNotEqual(body, a.surface.text)
                inverse = evaluate_grounded_surface_body_inverse(
                    body=body.encode("utf-8"), plan=a.plan, sentence_plan=a.sentence_plan,
                    resolver=a.resolver, selected_subjective_input=a.selected_subjective_input,
                )
                self.assertFalse(inverse.passed)
                self.assertFalse(evaluate_grounded_observation_gate(
                    plan=a.plan, sentence_plan=a.sentence_plan, surface_result=replace(a.surface, text=body),
                    resolver=a.resolver, require_body_inverse=True,
                    selected_subjective_input=a.selected_subjective_input).passed)
        witness = surface_owner.parse_grounded_surface_body_bytes(a.surface.text.encode("utf-8"))
        encoded = a.surface.text.encode("utf-8")
        self.assertTrue(any(m.marker_kind == "reception" and m.marker_code == "target_words"
                            and encoded[m.utf8_byte_start:m.utf8_byte_end].decode() == "という言葉"
                            for m in witness.markers))
        body = (surface_owner.OBSERVATION_SECTION_LABEL + "\n記録があります。\n"
                + surface_owner.RECEPTION_SECTION_LABEL + "\n物を買うということを大切に思っています。")
        self.assertFalse(any(m.marker_code == "finite_clause_nominal"
                             for m in surface_owner.parse_grounded_surface_body_bytes(body.encode()).markers))

    def test_preserved_objects_are_both_selected_primary_with_the_same_focal_contrast(self):
        a = self.a
        self.assertTrue(self.cores)
        core, realization, kwargs = self.cores[0]
        self.assertEqual((core.relation_count, core.pending_relation_slots, core.semantic_slots), (0, (0,), (0, 1)))
        self.assertEqual(kwargs["distributive_relation_slot"], 0)
        self.assertEqual(realization.relations[0].relation_kind, "contrast")
        self.assertEqual(core.text, self.context + "ことと" + self.source + "という言葉の両方")
        decision = self.predicates[0]["selected_subjective_decision"]
        self.assertTrue(reception_owner._selected_noncollapse_appraisal(decision))
        prop = decision.subjective_proposition
        semantic_map = dict(a.selected_subjective_input.semantic_nucleus_pairs)
        relation_map = dict(a.selected_subjective_input.relation_pairs)
        relation = next(r for r in a.plan.relations if r.relation_id == relation_map[prop.focal_relation_ref])
        selected = {semantic_map[b.semantic_ref] for b in decision.basis_rows
                    if b.contribution_ref in decision.selected_contribution_refs}
        primary = {semantic_map[b.semantic_ref] for b in decision.basis_rows
                   if b.binding_ref in prop.appraisal_content.appraised_bindings
                   and b.semantic_ref in prop.primary_target_refs}
        self.assertLessEqual({relation.from_nucleus_id, relation.to_nucleus_id}, selected & primary)
        self.assertEqual(self.predicates[0]["move_role"], "felt_response")
        self.assertTrue(self.predicates[0]["distributive_object"])
        expected_moves = tuple(m.move_id for m in a.plan.response_plan.human_reception_plan.moves if m.required)
        for authored in a.authored:
            self.assertEqual(tuple(m for binding in authored.visible_segment_bindings for m in binding.move_ids),
                             expected_moves)

    def test_preserved_contrast_requires_local_completion_and_exact_selected_operation(self):
        kwargs = self.predicates[0]
        render = reception_owner._source_grounded_response_predicate_surface
        original = reception_owner._source_grounded_response_predicate
        decision = kwargs["selected_subjective_decision"]
        prop = decision.subjective_proposition
        appraisal = prop.appraisal_content
        changed_decisions = tuple(replace(decision, subjective_proposition=replace(prop, appraisal_content=replace(
            appraisal, **changes))) for changes in (
                {"dimension": contracts_owner.AppraisalDimension.MATERIAL_WEIGHT},
                {"operation": contracts_owner.AppraisalOperation.RECEIVE_AS_MATERIAL},
                {"focal_relation_ref": None}, {"focal_relation_ref": "foreign-relation"}))
        for updates in (
            {"pending_relation_slots": (False,)}, {"pending_relation_slots": [0]},
            {"pending_relation_slots": (0, 0)}, {"pending_relation_slots": (1,)},
            {"distributive_object": False}, {"move_role": "attention"}, {"move_role": "significance"},
            {"reception_act": "protect_retained_intention"}, {"unfinished_pair": True},
            *({"selected_subjective_decision": changed} for changed in changed_decisions),
        ):
            with self.subTest(updates=updates), self.assertRaises(reception_owner.GroundedHumanReceptionSurfaceError):
                render(**{**kwargs, **updates})
        for completed in ((), (False,), [0], (0, 0), (1,)):
            def wrong_completion(reception_act, move_role, **arguments):
                return replace(original(reception_act, move_role, **arguments), completed_relation_slots=completed)
            with self.subTest(completed=completed), patch.object(
                    reception_owner, "_source_grounded_response_predicate", side_effect=wrong_completion):
                with self.assertRaises(reception_owner.GroundedHumanReceptionSurfaceError):
                    render(**kwargs)
        core, realization, target_kwargs = self.cores[0]
        move = self.a.plan.response_plan.human_reception_plan.moves[0]
        with self.assertRaises(reception_owner.GroundedHumanReceptionSurfaceError):
            reception_owner._source_grounded_reception_fragment(
                replace(move, move_role="bounded_counterposition"), realization, context_prefix="",
                target_core=core, referent_kind="current_expression",
                target_owner_slot=target_kwargs["target_owner_slot"], recovery_stage="full",
                selected_subjective_decision=decision, distributive_object=True)

    def test_expression_grammar_requires_whole_same_source_and_keeps_legacy(self):
        a = self.a
        rp = a.plan.response_plan.human_reception_plan
        move = rp.moves[0]
        index = {n.nucleus_id: n for n in a.plan.nuclei}
        target = index[move.target_nucleus_ids[0]]
        derive = reception_owner.source_grounded_current_expression_nominal
        nominal = self.source + "という言葉"
        self.assertEqual(derive(move, a.plan, index, a.resolver), nominal)
        self.assertEqual(derive(move, None, index, a.resolver), "")
        self.assertEqual(derive(move, replace(a.plan, source_contracts=()), index, a.resolver), "")
        self.assertEqual(derive(replace(move, move_id="foreign"), a.plan, index, a.resolver), "")
        for changes in (
            {"actor": "other"}, {"actor": "unknown"}, {"modality": "wish"},
            {"modality": "intention"},
            {"attribute_codes": (*target.semantic_frame.attribute_codes, "quantity:multiple")},
            {"attribute_codes": (*target.semantic_frame.attribute_codes, "operator:performed_action")},
        ):
            changed = replace(target, semantic_frame=replace(target.semantic_frame, **changes))
            plan = replace(a.plan, nuclei=tuple(changed if n == target else n for n in a.plan.nuclei))
            with self.subTest(changes=changes):
                self.assertEqual(derive(move, plan, {**index, target.nucleus_id: changed}, a.resolver), "")
        spans = tuple(a.resolver.resolve_many(a.resolver.span_ids))
        # Ledger drops terminal punctuation. Identical spans do not prove
        # a declarative source field, so this grammar must remain words-only.
        for punctuation in ("？", "！"):
            row = {**self.row, "input": {**self.row["input"],
                   "thought_text": self.row["input"]["thought_text"][:-1] + punctuation}}
            source = freeze_text_source(_request_from_row(row))
            self.assertEqual(source.evidence_spans, spans)
            resolver = build_evidence_span_resolver(
                source.evidence_spans, current_input=source.normalized_current_input,
            )
            self.assertEqual(derive(move, a.plan, index, resolver), nominal)
            self.assertNotEqual(nominal, self.source + "ということ")
        for suffix in ("？", "！", "…", "‥", "けど", "と", "。別の文"):
            altered = tuple(replace(s, raw_text=s.raw_text + suffix)
                            if s.span_id == target.source_span_ids[0] else s for s in spans)
            with self.subTest(suffix=suffix):
                resolver = build_evidence_span_resolver(altered)
                if suffix == "。別の文":
                    with self.assertRaises(reception_owner.GroundedHumanReceptionSurfaceError):
                        derive(move, a.plan, index, resolver)
                else:
                    self.assertEqual(derive(move, a.plan, index, resolver), "")
        with patch.object(reception_owner, "_source_grounded_clause_candidate", return_value="分からない"):
            self.assertEqual(derive(move, a.plan, index, a.resolver), "")
        for final, stage in ((False, "full"), (True, "integrated")):
            ref = reception_owner.resolve_grounded_reception_move_referent(
                rp, move, index, a.resolver, allow_short_anchor=False,
                final_source_fidelity=final, recovery_stage=stage, plan=a.plan,
            )
            self.assertNotEqual(ref.text, nominal)


class CMEEFinalUnfinishedStateReferentTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifacts = tuple(_full_surface_artifacts(CMEEFinalCurrentMoodSourceTest._row(text))
                              for text in ("今もはっきり分からない。", "まだわからない。", "まだ分からない。"))

    def test_selected_unknown_reaches_the_same_single_move(self):
        for a in self.artifacts[:2]:
            with self.subTest(body=a.surface.text):
                self.assertTrue(a.gate.passed, a.gate.rejection_reasons)
                self.assertTrue(a.inverse.passed, a.inverse.failure_codes)
                rp = a.plan.response_plan.human_reception_plan
                self.assertEqual(len(rp.moves), 1)
                self.assertEqual(rp.moves[0].reception_act, "stay_with_current_burden")
                self.assertIn("まだ分からないことを小さくせずに受け止めています", _reception_text(a.surface.text))
                self.assertIn("結論を急がずに", _reception_text(a.surface.text))
                self.assertNotIn("今ここに置かれた言葉", _reception_text(a.surface.text))
                target = next(n for n in a.plan.nuclei if n.nucleus_id == rp.moves[0].target_nucleus_ids[0])
                self.assertEqual(target.kind, "uncertainty")
                self.assertEqual(target.semantic_frame.modality, "uncertain")
                self.assertNotIn("operator:change", target.semantic_frame.attribute_codes)

    def test_body_inverse_rejects_resolution_target_loss_and_quoted_nominal(self):
        a = self.artifacts[0]
        for old, new in (("まだ分からないこと", "今ここに置かれた言葉"),
                         ("まだ分からないこと", "分かったこと"),
                         ("まだ分からないこと", "その変化についてまだ分からないこと"),
                         ("まだ分からないこと", "「まだ分からないこと」"),
                         ("結論を急がずに、", ""), ("受け止めています", "感じています")):
            with self.subTest(new=new):
                body = _tamper_reception(a.surface.text, old, new)
                self.assertNotEqual(body, a.surface.text)
                self.assertFalse(evaluate_grounded_surface_body_inverse(
                    body=body.encode("utf-8"), plan=a.plan, sentence_plan=a.sentence_plan,
                    resolver=a.resolver, selected_subjective_input=a.selected_subjective_input).passed)

    def test_unknown_referent_requires_source_proof_not_burden_family(self):
        a = self.artifacts[0]
        rp = a.plan.response_plan.human_reception_plan
        move = rp.moves[0]
        index = {n.nucleus_id: n for n in a.plan.nuclei}
        target = index[move.target_nucleus_ids[0]]
        derive = reception_owner.source_grounded_unfinished_referent
        self.assertEqual(derive(move, a.plan, index, a.resolver), "まだ分からないこと")
        attrs = target.semantic_frame.attribute_codes
        for changes in ({"actor": "other"}, {"actor": "unknown"}, {"time_scope": "past"},
                        {"modality": "fact"}, {"predicate_kind": "state"}, {"polarity": "positive"},
                        *({"attribute_codes": tuple(c for c in attrs if c != code)} for code in (
                            "operator:uncertainty", "lexical:preserve_source_predicate", "lexical:no_new_sensation_family")),
                        *({"attribute_codes": (*attrs, code)} for code in (
                            "operator:change", "operator:positive_change", "operator:result", "quantity:multiple"))):
            changed = replace(target, semantic_frame=replace(target.semantic_frame, **changes))
            plan = replace(a.plan, nuclei=tuple(changed if n == target else n for n in a.plan.nuclei))
            with self.subTest(changes=changes):
                self.assertEqual(derive(move, plan, {**index, target.nucleus_id: changed}, a.resolver), "")
        self.assertEqual(derive(move, None, index, a.resolver), "")
        self.assertEqual(derive(move, a.plan, {**index, target.nucleus_id: replace(target, kind="state")}, a.resolver), "")

    def test_reference_boundary_and_legacy_path_are_preserved(self):
        a = self.artifacts[0]
        rp = a.plan.response_plan.human_reception_plan
        move = rp.moves[0]
        index = {n.nucleus_id: n for n in a.plan.nuclei}
        derive = reception_owner.source_grounded_unfinished_referent
        for changed in (replace(move, support_nucleus_ids=("foreign",)),
                        replace(move, target_nucleus_ids=(*move.target_nucleus_ids, "foreign")),
                        replace(move, reception_act="recognize_lived_change")):
            plan = replace(a.plan, response_plan=replace(a.plan.response_plan,
                human_reception_plan=replace(rp, moves=(changed,))))
            self.assertEqual(derive(changed, plan, index, a.resolver), "")
        kwargs = dict(reception_plan=rp, move=move, nucleus_index=index,
                      resolver=a.resolver, allow_short_anchor=False, plan=a.plan)
        self.assertEqual("その苦しさ", reception_owner.resolve_grounded_reception_move_referent(**kwargs).text)
        short = self.artifacts[2]
        self.assertTrue(short.gate.passed and short.inverse.passed)
        self.assertIn("置かれた言葉", _reception_text(short.surface.text))
        spans = tuple(a.resolver.resolve_many(a.resolver.span_ids))
        for boundary in ("『引用』", "「引用」", "…"):
            altered = tuple(replace(s, raw_text=s.raw_text + boundary)
                            if s.source_field == "memo" else s for s in spans)
            with patch.object(type(a.resolver), "resolve_many", return_value=altered):
                self.assertEqual(derive(move, a.plan, index, a.resolver), "")


class CMEEFinalSceneMoodSourceTest(unittest.TestCase):
    @staticmethod
    def _project(text):
        source, base = CMEEUnresolvedQuestionSourceTest()._source_plan(text)
        nuclei, dependencies = observation_plan_owner._final_stage1_typed_nuclei(
            base, source.evidence_spans, normalized_input=source.normalized_current_input)
        return source, base, nuclei, dependencies

    def test_finite_scene_preserves_whole_source_and_same_nucleus(self):
        for text in (
            "外の空気が気持ちよくて、今日は気分が軽い。",
            "日差しが窓から差し込んできて、今は気分が軽い。",
            "風が室内に入ってきて、今日は私の気分が軽いです。",
            "部屋の空気が心地よくて、気分も少し軽い。",
        ):
            with self.subTest(text=text):
                source, base, nuclei, dependencies = self._project(text)
                before = next(n for n in base.nuclei if n.source_fields == ("memo",))
                after = next(n for n in nuclei if n.source_fields == ("memo",))
                self.assertFalse(observation_plan_owner.is_grounded_positive_feeling(before))
                self.assertTrue(observation_plan_owner.is_grounded_positive_feeling(after))
                self.assertEqual(len(nuclei), len(base.nuclei))
                self.assertEqual(dependencies, ())
                self.assertEqual(replace(after, kind=before.kind, semantic_frame=before.semantic_frame), before)
                self.assertEqual(after.semantic_frame.actor, before.semantic_frame.actor)
                self.assertEqual(after.semantic_frame.time_scope, before.semantic_frame.time_scope)
                self.assertFalse(any(c.startswith(("surface_scalar_", "source_fragment_scalar_"))
                                     for c in after.semantic_frame.attribute_codes))
                self.assertFalse(set(after.semantic_frame.attribute_codes) & {
                    "operator:change", "operator:result", "operator:action", "operator:performed_action",
                    "semantic_role:current_change", "semantic_role:explicit_result"})
                spans = [s for s in source.evidence_spans if s.source_field == "memo"]
                self.assertEqual(len(spans), 1)
                self.assertEqual(spans[0].raw_text.rstrip("。"), text.rstrip("。"))

    def test_scene_cannot_borrow_other_person_or_noncurrent_mood(self):
        for text in (
            "同僚が入ってきて、今日は気分が軽い。",
            "同僚は外の空気が気持ちよくて、今日は気分が軽い。",
            "同僚の部屋の空気が気持ちよくて、今日は気分が軽い。",
            "外の空気が気持ちよくて、同僚の気分が軽い。",
            "外の空気が気持ちよくて、昨日は気分が軽かった。",
            "外の空気が気持ちよくて、明日は気分が軽い。",
            "外の空気が気持ちよくて、今日は気分が軽くない。",
            "外の空気が気持ちよくて、今日は気分が軽いかもしれない。",
            "外の空気が気持ちよくて、今日は気分が軽い？",
            "外の空気が気持ちよくて、今日は気分が軽い…",
            "外の空気が気持ちよくて、今日は気分が軽いと思った。",
            "外の空気が気持ちよくて、今日は気分が軽いなら出かける。",
            "『外の空気が気持ちよくて、今日は気分が軽い』と聞いた。",
            "昨日の光が部屋に入ってきて、今日は気分が軽い。",
            "光が部屋に入ってこなくて、今日は気分が軽い。",
        ):
            with self.subTest(text=text):
                _source, _base, nuclei, _dependencies = self._project(text)
                self.assertFalse(any(observation_plan_owner.is_grounded_positive_feeling(n)
                                     for n in nuclei if n.source_fields == ("memo",)))

    def test_compound_proof_requires_complete_matching_source(self):
        text = "外の空気が気持ちよくて、今日は気分が軽い。"
        source, base, _nuclei, _dependencies = self._project(text)
        target = next(n for n in base.nuclei if n.source_fields == ("memo",))
        for normalized in (None, {**source.normalized_current_input, "memo": "今日は気分が軽い。"}):
            self.assertEqual(observation_plan_owner._final_stage1_typed_nuclei(
                base, source.evidence_spans, normalized_input=normalized)[0], base.nuclei)
        for changes in ({"actor": "other"}, {"actor": "unknown"}, {"time_scope": "past"},
                        {"modality": "uncertain"}, {"modality": "wish"},
                        {"attribute_codes": (*target.semantic_frame.attribute_codes, "operator:change")},
                        {"attribute_codes": (*target.semantic_frame.attribute_codes, "semantic_role:limiting_unknown")}):
            altered = replace(base, nuclei=tuple(replace(n, semantic_frame=replace(n.semantic_frame, **changes))
                                                if n == target else n for n in base.nuclei))
            self.assertEqual(observation_plan_owner._final_stage1_typed_nuclei(
                altered, source.evidence_spans, normalized_input=source.normalized_current_input)[0], altered.nuclei)
        for span_changes in ({"start_index": 1}, {"end_index": 2}, {"raw_text": "今日は気分が軽い"}):
            spans = tuple(replace(s, **span_changes) if s.source_field == "memo" else s
                          for s in source.evidence_spans)
            self.assertEqual(observation_plan_owner._final_stage1_typed_nuclei(
                base, spans, normalized_input=source.normalized_current_input)[0], base.nuclei)

    def test_whole_scene_reaches_reception_and_inverse_rejects_context_loss(self):
        text = "風が室内に入ってきて、今日は私の気分が軽いです。"
        a = _full_surface_artifacts(CMEEFinalCurrentMoodSourceTest._row(text))
        self.assertTrue(a.gate.passed, a.gate.rejection_reasons)
        self.assertTrue(a.inverse.passed, a.inverse.failure_codes)
        self.assertEqual(len(a.selected_subjective_input.decisions), 1)
        self.assertEqual(a.selected_subjective_input.decisions[0].reception_act, "recognize_lived_change")
        follow = _reception_text(a.surface.text)
        self.assertIn("気持ち", follow)
        self.assertNotIn("今ここに置かれた言葉", follow)
        for old, new in (("気持ち", "変化"), ("受け止めています", "小さくせずに受け止めています")):
            body = _tamper_reception(a.surface.text, old, new)
            self.assertNotEqual(body, a.surface.text)
            self.assertFalse(evaluate_grounded_surface_body_inverse(
                body=body.encode("utf-8"), plan=a.plan, sentence_plan=a.sentence_plan,
                resolver=a.resolver, selected_subjective_input=a.selected_subjective_input).passed)
        # The complete event is still asserted in Layer 1. It cannot be
        # discarded just because Layer 2 now receives the focal feeling.
        for old, new in (("風が室内に入ってきて、", ""), ("風", "同僚"), ("今日", "明日")):
            body = a.surface.text.replace(old, new)
            self.assertNotEqual(body, a.surface.text)
            self.assertFalse(evaluate_grounded_surface_body_inverse(
                body=body.encode("utf-8"), plan=a.plan, sentence_plan=a.sentence_plan,
                resolver=a.resolver, selected_subjective_input=a.selected_subjective_input).passed)


class CMEEFinalFeelingSubjectReferentTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifacts = tuple((source, nominal, _full_surface_artifacts({
            "case_id": "public-feeling-subject-referent", "input": {
                "thought_text": source + "。", "action_text": "", "categories": ["生活"],
                "emotions": [{"type": "不安", "strength": "weak"}],
            },
        })) for source, nominal in (
            ("今も不安が残っている", "今も残っている不安"),
            ("不安が少し残っている", "少し残っている不安"),
            ("もやもやがずっと続いている", "ずっと続いているもやもや"),
            ("気持ちが少し残っている", "少し残っている気持ち"),
        ))

    def test_selected_feeling_host_and_modifiers_reach_same_move_and_replay(self):
        for source, nominal, a in self.artifacts:
            with self.subTest(source=source):
                follow = _reception_text(a.surface.text).strip()
                self.assertTrue(a.gate.passed, a.gate.rejection_reasons)
                self.assertTrue(a.inverse.passed, a.inverse.failure_codes)
                self.assertEqual(follow, nominal + "を小さくせずに受け止めています。")
                self.assertNotIn(source, follow)
                reception = a.plan.response_plan.human_reception_plan
                self.assertEqual(len(reception.moves), 1)
                move = reception.moves[0]
                self.assertTrue(move.required)
                self.assertEqual(move.reception_act, "stay_with_current_burden")
                self.assertEqual(move.support_nucleus_ids, ())
                index = {n.nucleus_id: n for n in a.plan.nuclei}
                ref = reception_owner.resolve_grounded_reception_move_referent(
                    reception, move, index, a.resolver, allow_short_anchor=False,
                    final_source_fidelity=True, plan=a.plan,
                )
                self.assertEqual((ref.kind, ref.text), ("current_expression", nominal))
                line = next(line for line in a.sentence_plan.lines if line.binding.line_role == "human_follow")
                replay = reception_owner.replay_source_grounded_human_reception_from_plan(
                    reception, index, a.resolver, plan=a.plan,
                    recovery_stage=a.sentence_plan.recovery_stage,
                    clause_plans=line.reception_clause_plans,
                    selected_subjective_input=a.selected_subjective_input,
                )
                self.assertEqual(replay.text, follow)
                self.assertTrue(all(kw["selected_subjective_input"] is a.selected_subjective_input
                                    for _args, kw in a.author_arguments))
                self.assertTrue(all(e.nominalization_plan == reception_owner._SOURCE_GROUNDED_NOMINALIZATION_BASE
                                    for args, _kw in a.author_arguments for e in args[1]))

    def test_inverse_requires_complete_source_nominal_once_and_responsibility(self):
        source, nominal, a = self.artifacts[1]
        for replacement in (
            "残っている不安", "強く残っている不安", "少し続いている不安", "少し残っていた不安",
            "少し残っている喜び", "今ここに置かれた言葉", source,
            "「" + nominal + "」", "『" + nominal + "』", nominal + "と" + nominal,
        ):
            with self.subTest(replacement=replacement):
                body = _tamper_reception(a.surface.text, nominal, replacement)
                inverse = evaluate_grounded_surface_body_inverse(
                    body=body.encode("utf-8"), plan=a.plan, sentence_plan=a.sentence_plan,
                    resolver=a.resolver, selected_subjective_input=a.selected_subjective_input,
                )
                self.assertFalse(inverse.passed)
                self.assertTrue(any("target_duty_missing" in c for c in inverse.failure_codes))
        for original, replacement, reason in (
            (nominal, source + "、" + nominal, "anaphoric_target_replayed"),
            ("小さくせずに受け止めています", "小さなことだと考えています", "why_duty_missing"),
        ):
            body = _tamper_reception(a.surface.text, original, replacement)
            inverse = evaluate_grounded_surface_body_inverse(
                body=body.encode("utf-8"), plan=a.plan, sentence_plan=a.sentence_plan,
                resolver=a.resolver, selected_subjective_input=a.selected_subjective_input,
            )
            self.assertFalse(inverse.passed)
            self.assertTrue(any(reason in c for c in inverse.failure_codes), inverse.failure_codes)

    def test_subject_transposition_requires_registered_current_host_and_bound_source(self):
        derive = reception_owner._source_grounded_feeling_nominal
        for source in (
            "気持ちが悪い", "気持ちがない", "気持ちがせわしない", "不安は残っている",
            "不安も残っている", "弟の不安が残っている", "私は不安が残っている",
            "不安の記録が残っている", "不安が残っていた", "不安が残っています",
            "不安が残っていると思う", "不安が残っているなら休む", "不安が残っている人だ",
            "不安が残っている？", "「不安が残っている」", "不安が残っている…",
            "不安が私こそ感じている",
        ):
            with self.subTest(source=source):
                self.assertIsNone(derive(source))
        _source, nominal, a = self.artifacts[0]
        reception = a.plan.response_plan.human_reception_plan
        move = reception.moves[0]
        index = {n.nucleus_id: n for n in a.plan.nuclei}
        target = index[move.target_nucleus_ids[0]]
        resolve = reception_owner.source_grounded_feeling_target_nominal
        self.assertEqual(resolve(move, a.plan, index, a.resolver), nominal)
        self.assertEqual(resolve(move, None, index, a.resolver), "")
        self.assertEqual(resolve(move, replace(a.plan, source_contracts=()), index, a.resolver), "")
        for changes in (
            {"actor": "other"}, {"modality": "uncertain"}, {"predicate_kind": "event"},
            {"time_scope": "future"}, {"time_scope": "past"}, {"polarity": "positive"},
            {"attribute_codes": (*target.semantic_frame.attribute_codes, "quantity:multiple")},
        ):
            changed = replace(target, semantic_frame=replace(target.semantic_frame, **changes))
            plan = replace(a.plan, nuclei=tuple(changed if n == target else n for n in a.plan.nuclei))
            self.assertEqual(resolve(move, plan, {**index, target.nucleus_id: changed}, a.resolver), "")
        supported = replace(move, support_nucleus_ids=(a.plan.nuclei[1].nucleus_id,))
        plan = replace(a.plan, response_plan=replace(a.plan.response_plan,
            human_reception_plan=replace(reception, moves=(supported,))))
        self.assertEqual(resolve(supported, plan, index, a.resolver), "")
        relation = observation_plan_owner.GroundedSemanticRelation(
            relation_id="public-feeling-required-context", type="contrast", from_nucleus_id=target.nucleus_id,
            to_nucleus_id=a.plan.nuclei[1].nucleus_id, source_span_ids=target.source_span_ids,
            grounding_kind="explicit", certainty=1.0, retention="required",
        )
        plan = replace(a.plan, relations=(relation,), coverage_requirements=replace(a.plan.coverage_requirements,
            required_relation_ids=(relation.relation_id,)))
        self.assertEqual(resolve(move, plan, index, a.resolver), "")
        legacy = reception_owner.resolve_grounded_reception_move_referent(
            reception, move, index, a.resolver, allow_short_anchor=False,
        )
        self.assertNotEqual(legacy.text, nominal)

    def test_adnominal_witness_is_structural_and_bound_at_whole_target_end(self):
        for _source, nominal, a in self.artifacts:
            body = a.surface.text.encode("utf-8")
            witness = surface_owner.parse_grounded_surface_body_bytes(body)
            markers = [m for m in witness.markers if m.marker_code == "adnominal_subject"]
            end = body.index(nominal.encode("utf-8")) + len(nominal.encode("utf-8"))
            self.assertTrue(any(m.utf8_byte_end == end for m in markers))
            self.assertTrue(all(m.section == "reception" and m.marker_kind == "semantic" for m in markers))
            self.assertTrue(all(not {"target_burden", "target_words"}.intersection(s.reception_marker_codes)
                                for s in witness.sentences if s.section == "reception"))


    def test_original_field_proof_survives_ledger_punctuation_and_owner_splitting(self):
        marker = "lexical:source_declarative_feeling_subject"
        for source in (
            "不安が残っている？", "不安が残っている！", "「不安が残っている」",
            "不安が残っている…", "不安が残っている...", "不安が残っている。。",
            "弟は。今も不安が残っている。",
            "不安が残っている。と弟が話した。",
        ):
            with self.subTest(source=source):
                inputs = _compile_inputs({"case_id": "public-feeling-original-boundary", "input": {
                    "thought_text": source, "action_text": "", "categories": ["生活"],
                    "emotions": [{"type": "不安", "strength": "weak"}],
                }})
                plan = inputs.grounded_plan
                self.assertTrue(all(marker not in n.semantic_frame.attribute_codes for n in plan.nuclei))
                resolver = build_evidence_span_resolver(inputs.source.evidence_spans,
                                                        current_input=inputs.source.normalized_current_input)
                for move in plan.response_plan.human_reception_plan.moves:
                    self.assertEqual(reception_owner.source_grounded_feeling_target_nominal(
                        move, plan, {n.nucleus_id: n for n in plan.nuclei}, resolver,
                    ), "")
        _source, _nominal, a = self.artifacts[0]
        move = a.plan.response_plan.human_reception_plan.moves[0]
        index = {n.nucleus_id: n for n in a.plan.nuclei}
        target = index[move.target_nucleus_ids[0]]
        self.assertIn(marker, target.semantic_frame.attribute_codes)
        changed = replace(target, semantic_frame=replace(target.semantic_frame,
            attribute_codes=tuple(c for c in target.semantic_frame.attribute_codes if c != marker)))
        plan = replace(a.plan, nuclei=tuple(changed if n == target else n for n in a.plan.nuclei))
        self.assertEqual(reception_owner.source_grounded_feeling_target_nominal(
            move, plan, {**index, target.nucleus_id: changed}, a.resolver,
        ), "")


class CMEEFinalIndependentFeelingSelectionTest(unittest.TestCase):
    """The selected response owes both a proven feeling and the old action."""

    @staticmethod
    def row(thought="今も不安が残っている。", action="作業台を片づけた。"):
        return {"case_id": "public-independent-feeling-selection", "input": {
            "thought_text": thought, "action_text": action, "categories": ["生活"],
            "emotions": [{"type": "不安", "strength": "weak"}],
        }}

    @classmethod
    def setUpClass(cls):
        cls.a = _full_surface_artifacts(cls.row())

    def test_both_source_targets_reach_sealed_input_author_recovery_and_body(self):
        a = self.a
        self.assertTrue(a.gate.passed, a.gate.rejection_reasons)
        self.assertTrue(a.inverse.passed, a.inverse.failure_codes)
        moves = a.plan.response_plan.human_reception_plan.moves
        self.assertEqual(tuple(m.reception_act for m in moves),
                         ("stay_with_current_burden", "honor_concrete_effort"))
        self.assertEqual(tuple(m.move_role for m in moves), ("felt_response", "felt_response"))
        index = {n.nucleus_id: n for n in a.plan.nuclei}
        self.assertEqual(tuple(index[m.target_nucleus_ids[0]].source_fields for m in moves),
                         (("memo",), ("memo_action",)))
        self.assertTrue(all(m.required and not m.support_nucleus_ids for m in moves))
        decisions = a.selected_subjective_input.decisions
        self.assertEqual(tuple((d.move_id, d.reception_act, d.target_nucleus_ids, d.support_nucleus_ids)
                               for d in decisions),
                         tuple((m.move_id, m.reception_act, m.target_nucleus_ids, m.support_nucleus_ids)
                               for m in moves))
        # The structural source-order link is still uncertain. It is not
        # promoted to a shared appraisal merely to add the feeling duty.
        self.assertTrue(all(r.retention != "required" and r.type == "uncertain_connection"
                            for r in a.plan.relations))
        self.assertTrue(set(decisions[0].selected_contribution_refs).isdisjoint(
            decisions[1].selected_contribution_refs))
        follow = _reception_text(a.surface.text)
        self.assertLess(follow.index("不安"), follow.index("作業台"))
        self.assertIn("今も不安が残っている", follow)
        self.assertIn("作業台を片づけた", follow)
        required = {m.move_id for m in moves}
        for args, kwargs in a.author_arguments:
            self.assertIs(kwargs["selected_subjective_input"], a.selected_subjective_input)
            self.assertEqual({m.move_id for m in args[0].moves if m.required}, required)
        for authored in a.authored:
            self.assertEqual(set(authored.realized_move_ids), required)
        inputs = _compile_inputs(self.row())
        resolver = build_evidence_span_resolver(inputs.source.evidence_spans,
                                                current_input=inputs.source.normalized_current_input)
        for quality in ("grounded", "limited_grounding"):
            semantic = _cmee_semantic_reception_plan(inputs.grounded_plan, resolver, material_quality=quality)
            self.assertEqual(semantic.moves, moves)

    def test_removing_either_new_feeling_or_existing_action_fails_body_inverse(self):
        a = self.a
        for original in ("今も不安が残っている", "作業台を片づけた"):
            with self.subTest(original=original):
                body = _tamper_reception(a.surface.text, original, "")
                inverse = evaluate_grounded_surface_body_inverse(
                    body=body.encode("utf-8"), plan=a.plan, sentence_plan=a.sentence_plan,
                    resolver=a.resolver, selected_subjective_input=a.selected_subjective_input,
                )
                self.assertFalse(inverse.passed)
                self.assertTrue(any("target_duty_missing" in code for code in inverse.failure_codes),
                                inverse.failure_codes)

    def test_unproved_owner_host_and_unperformed_action_do_not_add_feeling(self):
        cases = [(thought, "作業台を片づけた。") for thought in (
            "", "不安が残っている？", "「不安が残っている」", "弟の不安が残っている。",
            "弟は。今も不安が残っている。", "不安が残っている。と弟が話した。",
            "不安が残っていた。", "不安が残っていると思う。",
            "不安が残っているなら休む。", "今も不安が残っている。別の記録も読んだ。",
        )]
        cases += [("今も不安が残っている。", action) for action in (
            "作業台を片づけるつもり。", "作業台を片づけてもらった。", "作業台を片づけなかった。",
        )]
        for thought, action in cases:
            with self.subTest(thought=thought, action=action):
                inputs = _compile_inputs(self.row(thought, action))
                plan = inputs.grounded_plan
                resolver = build_evidence_span_resolver(inputs.source.evidence_spans,
                                                        current_input=inputs.source.normalized_current_input)
                semantic = _cmee_semantic_reception_plan(plan, resolver)
                self.assertNotEqual(tuple(m.reception_act for m in semantic.moves),
                                    ("stay_with_current_burden", "honor_concrete_effort"))

    def test_source_stated_relation_and_optional_feeling_keep_existing_selection(self):
        from emlis_ai_safety_triage import build_emlis_safety_triage_decision
        inputs = _compile_inputs(self.row())
        plan = inputs.grounded_plan
        feeling = next(n for n in plan.nuclei if n.source_fields == ("memo",))
        action = next(n for n in plan.nuclei if n.source_fields == ("memo_action",))
        relation = replace(plan.relations[0], type="contrast", retention="required",
                           grounding_kind="user_stated_relation")
        variants = (
            (plan.nuclei, (relation,)),
            (tuple(replace(n, retention="optional") if n == feeling else n for n in plan.nuclei), plan.relations),
        )
        for nuclei, relations in variants:
            response, _coverage, _surface, _safety = observation_plan_owner._build_response_and_policies(
                nuclei=nuclei, relations=relations,
                safety_decision=build_emlis_safety_triage_decision(current_input=inputs.source.normalized_current_input),
                complexity=plan.input_profile.semantic_complexity,
                material_quality=plan.input_profile.material_quality,
                include_reception_relation_support=True, final_source_fidelity=True,
            )
            self.assertEqual(response.human_follow_target_ids, (action.nucleus_id,))
        legacy = build_grounded_observation_plan(inputs.source.normalized_current_input,
                                                evidence_spans=inputs.source.evidence_spans)
        self.assertEqual(legacy.response_plan.human_follow_target_ids, (action.nucleus_id,))


class CMEEFinalVerbalBackgroundFeelingSelectionTest(unittest.TestCase):
    """A current residual feeling retains its background and the old action."""

    marker = "lexical:source_current_feeling_with_verbal_background"
    sources = (
        "発言を途中で止められて、悲しさと不安が残っている。",
        "提案を急に退けられて、怒りが残っています。",
        "意見を否定されて、悔しさと寂しさが残っている。",
    )

    @classmethod
    def setUpClass(cls):
        cls.artifacts = tuple(_full_surface_artifacts(
            CMEEFinalIndependentFeelingSelectionTest.row(source),
        ) for source in cls.sources)

    def test_source_type_both_duties_and_selected_input_survive_all_recoveries(self):
        for source, a in zip(self.sources, self.artifacts):
            with self.subTest(source=source):
                self.assertTrue(a.gate.passed, a.gate.rejection_reasons)
                self.assertTrue(a.inverse.passed, a.inverse.failure_codes)
                moves = a.plan.response_plan.human_reception_plan.moves
                self.assertEqual(tuple(m.reception_act for m in moves),
                                 ("stay_with_current_burden", "honor_concrete_effort"))
                index = {n.nucleus_id: n for n in a.plan.nuclei}
                feeling = index[moves[0].target_nucleus_ids[0]]
                self.assertIn(self.marker, feeling.semantic_frame.attribute_codes)
                self.assertNotIn("lexical:source_declarative_feeling_subject",
                                 feeling.semantic_frame.attribute_codes)
                self.assertEqual(tuple(index[m.target_nucleus_ids[0]].source_fields for m in moves),
                                 (("memo",), ("memo_action",)))
                self.assertTrue(all(m.required and not m.support_nucleus_ids for m in moves))
                self.assertTrue(all(r.retention != "required" and r.type == "uncertain_connection"
                                    for r in a.plan.relations))
                self.assertEqual(tuple((d.reception_act, d.target_nucleus_ids, d.support_nucleus_ids)
                                       for d in a.selected_subjective_input.decisions),
                                 tuple((m.reception_act, m.target_nucleus_ids, m.support_nucleus_ids)
                                       for m in moves))
                self.assertTrue(set(a.selected_subjective_input.decisions[0].selected_contribution_refs).isdisjoint(
                    a.selected_subjective_input.decisions[1].selected_contribution_refs))
                inputs = _compile_inputs(CMEEFinalIndependentFeelingSelectionTest.row(source))
                resolver = build_evidence_span_resolver(inputs.source.evidence_spans,
                                                        current_input=inputs.source.normalized_current_input)
                legacy = build_grounded_observation_plan(inputs.source.normalized_current_input,
                                                        evidence_spans=inputs.source.evidence_spans)
                old_feeling = next(n for n in legacy.nuclei if n.source_fields == ("memo",))
                self.assertEqual(feeling.kind, old_feeling.kind)
                self.assertEqual(feeling.semantic_frame.predicate_kind, old_feeling.semantic_frame.predicate_kind)
                self.assertEqual(feeling.semantic_frame.modality, old_feeling.semantic_frame.modality)
                for quality in ("grounded", "limited_grounding"):
                    self.assertEqual(_cmee_semantic_reception_plan(
                        inputs.grounded_plan, resolver, material_quality=quality,
                    ).moves, moves)
                follow = _reception_text(a.surface.text)
                self.assertIn(source.rstrip("。"), follow)
                self.assertIn("作業台を片づけた", follow)
                for args, kwargs in a.author_arguments:
                    self.assertIs(kwargs["selected_subjective_input"], a.selected_subjective_input)
                for authored in a.authored:
                    self.assertEqual(set(authored.realized_move_ids), {m.move_id for m in moves})
                    sentence_plan = a.sentence_plan if authored.recovery_stage == "full" else (
                        surface_owner.build_reception_recovery_sentence_plan(
                            a.sentence_plan, a.plan, a.resolver, recovery_stage=authored.recovery_stage,
                        )
                    )
                    surface = _recovery_surface(a, sentence_plan)
                    self.assertIn(source.rstrip("。"), surface.text)
                    self.assertIn("作業台を片づけた", surface.text)
                    inverse = evaluate_grounded_surface_body_inverse(
                        body=surface.text.encode("utf-8"), plan=a.plan,
                        sentence_plan=sentence_plan, resolver=a.resolver,
                        selected_subjective_input=a.selected_subjective_input,
                    )
                    self.assertTrue(inverse.passed, inverse.failure_codes)

    def test_inverse_rejects_losing_background_either_feeling_or_old_action(self):
        source, a = self.sources[0].rstrip("。"), self.artifacts[0]
        for original in (source, "作業台を片づけた", source.split("、")[0] + "、",
                         "悲しさと", "と不安"):
            with self.subTest(original=original):
                inverse = evaluate_grounded_surface_body_inverse(
                    body=_tamper_reception(a.surface.text, original, "").encode("utf-8"),
                    plan=a.plan, sentence_plan=a.sentence_plan, resolver=a.resolver,
                    selected_subjective_input=a.selected_subjective_input,
                )
                self.assertFalse(inverse.passed, inverse.failure_codes)

    def test_unproved_owner_time_host_and_incomplete_field_never_gain_witness(self):
        base = self.sources[0]
        sources = (
            "不安", "", "弟は" + base, "弟が" + base, "弟の" + base,
            base.replace("悲しさと不安", "弟の不安"),
            base.replace("悲しさと不安", "悲しさと弟の不安"),
            base.replace("悲しさと不安", "不安と悲しさと怒り"),
            base.replace("悲しさと不安", "喜び"),
            base.replace("残っている", "残っていた"),
            base.replace("残っている", "残っていない"),
            base.replace("残っている", "残っているかもしれない"),
            base.replace("残っている", "残っていると思う"),
            base.replace("残っている", "残っているなら休む"),
            base.replace("止められて", "止められなくて"),
            base.replace("止められて", "止めてもらって"),
            base.replace("止められて", "止められると聞いて"),
            base.rstrip("。") + "？", base.rstrip("。") + "！",
            "「" + base.rstrip("。") + "」", base + "と弟が話した。",
            "弟は。" + base, base + "別の記録も読んだ。",
            "明日は" + base, "以前は" + base,
        )
        for source in sources:
            with self.subTest(source=source):
                frozen = freeze_text_source(_request_from_row(
                    CMEEFinalIndependentFeelingSelectionTest.row(source),
                ))
                plan = build_final_stage1_grounded_observation_plan(
                    frozen.normalized_current_input, evidence_spans=frozen.evidence_spans,
                )
                self.assertTrue(all(self.marker not in n.semantic_frame.attribute_codes for n in plan.nuclei))

    def test_shared_relation_optional_third_theme_and_nonperformance_keep_boundary(self):
        from emlis_ai_safety_triage import build_emlis_safety_triage_decision
        inputs = _compile_inputs(CMEEFinalIndependentFeelingSelectionTest.row(self.sources[1]))
        plan = inputs.grounded_plan
        feeling = next(n for n in plan.nuclei if n.source_fields == ("memo",))
        action = next(n for n in plan.nuclei if n.source_fields == ("memo_action",))
        relation = plan.relations[0]
        variants = (
            (plan.nuclei, (replace(relation, type="contrast", retention="required",
                                   grounding_kind="user_stated_relation"),)),
            (plan.nuclei, (replace(relation, type="contrast", retention="should"),)),
            ((*plan.nuclei, replace(feeling, nucleus_id="public-third-theme", retention="optional")), plan.relations),
            (tuple(replace(n, retention="optional") if n == feeling else n for n in plan.nuclei), plan.relations),
        )
        for nuclei, relations in variants:
            response, _coverage, _surface, _safety = observation_plan_owner._build_response_and_policies(
                nuclei=nuclei, relations=relations,
                safety_decision=build_emlis_safety_triage_decision(current_input=inputs.source.normalized_current_input),
                complexity=plan.input_profile.semantic_complexity,
                material_quality=plan.input_profile.material_quality,
                include_reception_relation_support=True, final_source_fidelity=True,
            )
            self.assertEqual(response.human_follow_target_ids, (action.nucleus_id,))
        for action_text in ("作業台を片づけるつもり。", "作業台を片づけてもらった。", "作業台を片づけなかった。"):
            other = _compile_inputs(CMEEFinalIndependentFeelingSelectionTest.row(self.sources[1], action_text))
            self.assertNotEqual(tuple(m.reception_act for m in other.grounded_plan.response_plan.human_reception_plan.moves),
                                ("stay_with_current_burden", "honor_concrete_effort"))
        legacy = build_grounded_observation_plan(inputs.source.normalized_current_input,
                                                evidence_spans=inputs.source.evidence_spans)
        self.assertEqual(legacy.response_plan.human_follow_target_ids, (action.nucleus_id,))


class CMEEFinalPastNegativeFeelingSelectionTest(unittest.TestCase):
    """A finite past feeling retains its background and the separate action."""

    marker = "lexical:source_past_negative_feeling"
    sources = (
        "資料を置き忘れて、少しがっかりした。",
        "楽しみにしていた講座を欠席して、落胆した。",
        "昨日は残念だった。",
    )

    @classmethod
    def setUpClass(cls):
        cls.artifacts = tuple(_full_surface_artifacts(
            CMEEFinalIndependentFeelingSelectionTest.row(source),
        ) for source in cls.sources)

    def test_past_feeling_background_and_action_reach_selected_input_and_all_recoveries(self):
        for source, a in zip(self.sources, self.artifacts):
            with self.subTest(source=source):
                self.assertTrue(a.gate.passed, a.gate.rejection_reasons)
                self.assertTrue(a.inverse.passed, a.inverse.failure_codes)
                moves = a.plan.response_plan.human_reception_plan.moves
                self.assertEqual(tuple(m.reception_act for m in moves),
                                 ("stay_with_current_burden", "honor_concrete_effort"))
                self.assertEqual(tuple(m.move_role for m in moves), ("felt_response", "felt_response"))
                index = {n.nucleus_id: n for n in a.plan.nuclei}
                feeling = index[moves[0].target_nucleus_ids[0]]
                self.assertIn(self.marker, feeling.semantic_frame.attribute_codes)
                self.assertEqual((feeling.kind, feeling.semantic_frame.predicate_kind,
                                  feeling.semantic_frame.polarity, feeling.semantic_frame.modality,
                                  feeling.semantic_frame.time_scope),
                                 ("reaction", "feeling", "negative", "feeling", "past"))
                self.assertEqual(tuple(index[m.target_nucleus_ids[0]].source_fields for m in moves),
                                 (("memo",), ("memo_action",)))
                self.assertTrue(all(m.required and not m.support_nucleus_ids for m in moves))
                self.assertTrue(all(r.retention != "required" and r.type == "uncertain_connection"
                                    for r in a.plan.relations))
                self.assertEqual(tuple((d.reception_act, d.target_nucleus_ids, d.support_nucleus_ids)
                                       for d in a.selected_subjective_input.decisions),
                                 tuple((m.reception_act, m.target_nucleus_ids, m.support_nucleus_ids)
                                       for m in moves))
                follow = _reception_text(a.surface.text)
                self.assertIn(source.rstrip("。"), follow)
                self.assertLess(follow.index(source.rstrip("。")), follow.index("作業台を片づけた"))
                for args, kwargs in a.author_arguments:
                    self.assertIs(kwargs["selected_subjective_input"], a.selected_subjective_input)
                for authored in a.authored:
                    self.assertEqual(set(authored.realized_move_ids), {m.move_id for m in moves})
                    sentence_plan = a.sentence_plan if authored.recovery_stage == "full" else (
                        surface_owner.build_reception_recovery_sentence_plan(
                            a.sentence_plan, a.plan, a.resolver, recovery_stage=authored.recovery_stage,
                        )
                    )
                    surface = _recovery_surface(a, sentence_plan)
                    self.assertIn(source.rstrip("。"), surface.text)
                    self.assertIn("作業台を片づけた", surface.text)
                    inverse = evaluate_grounded_surface_body_inverse(
                        body=surface.text.encode("utf-8"), plan=a.plan,
                        sentence_plan=sentence_plan, resolver=a.resolver,
                        selected_subjective_input=a.selected_subjective_input,
                    )
                    self.assertTrue(inverse.passed, inverse.failure_codes)
                inputs = _compile_inputs(CMEEFinalIndependentFeelingSelectionTest.row(source))
                resolver = build_evidence_span_resolver(inputs.source.evidence_spans,
                                                        current_input=inputs.source.normalized_current_input)
                for quality in ("grounded", "limited_grounding"):
                    semantic = _cmee_semantic_reception_plan(inputs.grounded_plan, resolver,
                                                            material_quality=quality)
                    self.assertEqual(semantic.moves, moves)

    def test_inverse_rejects_missing_feeling_action_or_its_source_background(self):
        a = self.artifacts[0]
        for original in (self.sources[0].rstrip("。"), "作業台を片づけた", "資料を置き忘れて、"):
            with self.subTest(original=original):
                inverse = evaluate_grounded_surface_body_inverse(
                    body=_tamper_reception(a.surface.text, original, "").encode("utf-8"),
                    plan=a.plan, sentence_plan=a.sentence_plan, resolver=a.resolver,
                    selected_subjective_input=a.selected_subjective_input,
                )
                self.assertFalse(inverse.passed, inverse.failure_codes)

    def test_original_field_owner_finite_head_and_modality_are_required(self):
        base = self.sources[0]
        sources = (
            "友人が" + base, "私の友人が" + base, "友人の" + base,
            base.replace("少し", "友人は少し"),
            base.replace("置き忘れて", "置き忘れたと聞いて"),
            base.replace("置き忘れて", "置き忘れたと友人が話して"),
            base.replace("がっかりした", "がっかりしなかった"),
            base.replace("がっかりした", "がっかりしたかもしれない"),
            base.replace("がっかりした", "がっかりしたと思う"),
            base.replace("がっかりした", "がっかりしたなら休む"),
            base.replace("がっかりした", "がっかりしたくない"),
            base.rstrip("。") + "？", base.rstrip("。") + "！",
            "「" + base.rstrip("。") + "」", base + "と友人が話した。",
            "友人は。" + base, base + "別の記録も読んだ。",
            "弟にとって、残念だった。", "友人には、残念だった。",
            "明日は残念だった。", "不安が残っていた。", "昨日は嬉しかった。",
            "板を叩いて、へこんだ。", "穴に落ちこんだ。",
        )
        for source in sources:
            with self.subTest(source=source):
                frozen = freeze_text_source(_request_from_row(
                    CMEEFinalIndependentFeelingSelectionTest.row(source),
                ))
                plan = build_final_stage1_grounded_observation_plan(
                    frozen.normalized_current_input, evidence_spans=frozen.evidence_spans,
                )
                self.assertTrue(all(self.marker not in n.semantic_frame.attribute_codes for n in plan.nuclei))

    def test_existing_relation_action_and_public_route_boundaries_remain(self):
        from emlis_ai_safety_triage import build_emlis_safety_triage_decision
        inputs = _compile_inputs(CMEEFinalIndependentFeelingSelectionTest.row(self.sources[0]))
        plan = inputs.grounded_plan
        feeling = next(n for n in plan.nuclei if n.source_fields == ("memo",))
        action = next(n for n in plan.nuclei if n.source_fields == ("memo_action",))
        relation = replace(plan.relations[0], type="contrast", retention="required",
                           grounding_kind="user_stated_relation")
        for nuclei, relations in (
            (plan.nuclei, (relation,)),
            ((*plan.nuclei, replace(feeling, nucleus_id="public-third-theme", retention="optional")), plan.relations),
            (tuple(replace(n, retention="optional") if n == feeling else n for n in plan.nuclei), plan.relations),
        ):
            response, _coverage, _surface, _safety = observation_plan_owner._build_response_and_policies(
                nuclei=nuclei, relations=relations,
                safety_decision=build_emlis_safety_triage_decision(current_input=inputs.source.normalized_current_input),
                complexity=plan.input_profile.semantic_complexity,
                material_quality=plan.input_profile.material_quality,
                include_reception_relation_support=True, final_source_fidelity=True,
            )
            self.assertEqual(response.human_follow_target_ids, (action.nucleus_id,))
        for action_text in ("作業台を片づけるつもり。", "作業台を片づけてもらった。", "作業台を片づけなかった。"):
            other = _compile_inputs(CMEEFinalIndependentFeelingSelectionTest.row(self.sources[0], action_text))
            self.assertNotEqual(tuple(m.reception_act for m in other.grounded_plan.response_plan.human_reception_plan.moves),
                                ("stay_with_current_burden", "honor_concrete_effort"))
        legacy = build_grounded_observation_plan(inputs.source.normalized_current_input,
                                                evidence_spans=inputs.source.evidence_spans)
        self.assertEqual(legacy.response_plan.human_follow_target_ids, (action.nucleus_id,))


class CMEEFinalScalarBackgroundMaterialTest(unittest.TestCase):
    """An explicit scalar background remains material without a new feeling claim."""

    marker = "lexical:source_scalar_background_expression"
    sources = (
        "荷物を運ぶのが遅れてしまい、少しへこんだ。",
        "仕上がりが予想より重くて、ちょっと落ちこんだ。",
        "外した部品が想像より柔らかくて、少しへこんだ。",
    )

    @classmethod
    def setUpClass(cls):
        cls.artifacts = tuple(_full_surface_artifacts(
            CMEEFinalIndependentFeelingSelectionTest.row(source),
        ) for source in cls.sources)

    def test_whole_material_and_action_reach_selected_input_and_all_recoveries(self):
        for source, a in zip(self.sources, self.artifacts):
            with self.subTest(source=source):
                self.assertTrue(a.gate.passed, a.gate.rejection_reasons)
                self.assertTrue(a.inverse.passed, a.inverse.failure_codes)
                moves = a.plan.response_plan.human_reception_plan.moves
                self.assertEqual(tuple(m.reception_act for m in moves),
                                 ("stay_with_current_burden", "honor_concrete_effort"))
                self.assertEqual(tuple(m.move_role for m in moves), ("felt_response", "felt_response"))
                index = {n.nucleus_id: n for n in a.plan.nuclei}
                feeling = index[moves[0].target_nucleus_ids[0]]
                self.assertIn(self.marker, feeling.semantic_frame.attribute_codes)
                self.assertEqual((feeling.kind, feeling.semantic_frame.predicate_kind,
                                  feeling.semantic_frame.polarity, feeling.semantic_frame.modality,
                                  feeling.semantic_frame.time_scope),
                                 ("event", "event", "neutral", "fact", "current_input"))
                self.assertFalse(set(feeling.semantic_frame.attribute_codes).intersection({
                    "operator:feeling", "operator:positive_change", "semantic_role:explicit_evaluation",
                    "semantic_role:positive_evaluation", "lexical:source_past_negative_feeling",
                }))
                self.assertEqual(tuple(index[m.target_nucleus_ids[0]].source_fields for m in moves),
                                 (("memo",), ("memo_action",)))
                self.assertTrue(all(m.required and not m.support_nucleus_ids for m in moves))
                self.assertTrue(all(r.retention != "required" and r.type == "uncertain_connection"
                                    for r in a.plan.relations))
                self.assertEqual(tuple((d.reception_act, d.target_nucleus_ids, d.support_nucleus_ids)
                                       for d in a.selected_subjective_input.decisions),
                                 tuple((m.reception_act, m.target_nucleus_ids, m.support_nucleus_ids)
                                       for m in moves))
                follow = _reception_text(a.surface.text)
                self.assertIn(source.rstrip("。"), follow)
                self.assertLess(follow.index(source.rstrip("。")), follow.index("作業台を片づけた"))
                for args, kwargs in a.author_arguments:
                    self.assertIs(kwargs["selected_subjective_input"], a.selected_subjective_input)
                for authored in a.authored:
                    self.assertEqual(set(authored.realized_move_ids), {m.move_id for m in moves})
                    sentence_plan = a.sentence_plan if authored.recovery_stage == "full" else (
                        surface_owner.build_reception_recovery_sentence_plan(
                            a.sentence_plan, a.plan, a.resolver, recovery_stage=authored.recovery_stage,
                        )
                    )
                    surface = _recovery_surface(a, sentence_plan)
                    self.assertIn(source.rstrip("。"), surface.text)
                    self.assertIn("作業台を片づけた", surface.text)
                    inverse = evaluate_grounded_surface_body_inverse(
                        body=surface.text.encode("utf-8"), plan=a.plan,
                        sentence_plan=sentence_plan, resolver=a.resolver,
                        selected_subjective_input=a.selected_subjective_input,
                    )
                    self.assertTrue(inverse.passed, inverse.failure_codes)
                inputs = _compile_inputs(CMEEFinalIndependentFeelingSelectionTest.row(source))
                resolver = build_evidence_span_resolver(inputs.source.evidence_spans,
                                                        current_input=inputs.source.normalized_current_input)
                for quality in ("grounded", "limited_grounding"):
                    semantic = _cmee_semantic_reception_plan(inputs.grounded_plan, resolver,
                                                            material_quality=quality)
                    self.assertEqual(semantic.moves, moves)

    def test_inverse_rejects_missing_material_action_or_scalar_background(self):
        a = self.artifacts[0]
        for original in (self.sources[0].rstrip("。"), "作業台を片づけた", "荷物を運ぶのが遅れてしまい、"):
            with self.subTest(original=original):
                inverse = evaluate_grounded_surface_body_inverse(
                    body=_tamper_reception(a.surface.text, original, "").encode("utf-8"),
                    plan=a.plan, sentence_plan=a.sentence_plan, resolver=a.resolver,
                    selected_subjective_input=a.selected_subjective_input,
                )
                self.assertFalse(inverse.passed, inverse.failure_codes)

    def test_witness_requires_the_whole_finite_source_without_report_or_future(self):
        base = self.sources[0]
        sources = (
            base.replace("遅れてしまい", "遅れてしまいそうで"),
            base.replace("遅れてしまい", "遅れなかったので"),
            base.replace("へこんだ", "へこんだと聞いた"),
            base.replace("へこんだ", "へこんだって聞いた"),
            base.replace("へこんだ", "へこんだと思った"),
            base.replace("へこんだ", "へこまなかった"),
            base.replace("へこんだ", "へこんだかもしれない"),
            base.replace("へこんだ", "へこんだなら休む"),
            base.replace("少しへこんだ", "また"),
            base.replace("少しへこんだ", "あなた"),
            base.replace("少しへこんだ", "はんだ"),
            "明日は" + base, base.rstrip("。") + "？", base.rstrip("。") + "！",
            "「" + base.rstrip("。") + "」", base + "と友人が話した。",
            "友人は。" + base, base + "別の記録も読んだ。",
            "仕上がりが重くて、少しへこんだ。",
            "仕上がりが予想より重いらしくて、少しへこんだ。",
            "仕上がりが予想より丸いらしくて、少しへこんだ。",
        )
        for source in sources:
            with self.subTest(source=source):
                frozen = freeze_text_source(_request_from_row(
                    CMEEFinalIndependentFeelingSelectionTest.row(source),
                ))
                plan = build_final_stage1_grounded_observation_plan(
                    frozen.normalized_current_input, evidence_spans=frozen.evidence_spans,
                )
                self.assertTrue(all(self.marker not in n.semantic_frame.attribute_codes
                                    for n in plan.nuclei), source)

    def test_existing_relation_action_and_public_route_boundaries_remain(self):
        from emlis_ai_safety_triage import build_emlis_safety_triage_decision
        inputs = _compile_inputs(CMEEFinalIndependentFeelingSelectionTest.row(self.sources[0]))
        plan = inputs.grounded_plan
        feeling = next(n for n in plan.nuclei if n.source_fields == ("memo",))
        action = next(n for n in plan.nuclei if n.source_fields == ("memo_action",))
        relation = replace(plan.relations[0], type="contrast", retention="required",
                           grounding_kind="user_stated_relation")
        for nuclei, relations in (
            (plan.nuclei, (relation,)),
            ((*plan.nuclei, replace(feeling, nucleus_id="public-third-theme", retention="optional")), plan.relations),
            (tuple(replace(n, retention="optional") if n == feeling else n for n in plan.nuclei), plan.relations),
        ):
            response, _coverage, _surface, _safety = observation_plan_owner._build_response_and_policies(
                nuclei=nuclei, relations=relations,
                safety_decision=build_emlis_safety_triage_decision(current_input=inputs.source.normalized_current_input),
                complexity=plan.input_profile.semantic_complexity,
                material_quality=plan.input_profile.material_quality,
                include_reception_relation_support=True, final_source_fidelity=True,
            )
            self.assertEqual(response.human_follow_target_ids, (action.nucleus_id,))
        for action_text in ("作業台を片づけるつもり。", "作業台を片づけてもらった。", "作業台を片づけなかった。"):
            other = _compile_inputs(CMEEFinalIndependentFeelingSelectionTest.row(self.sources[0], action_text))
            self.assertNotEqual(tuple(m.reception_act for m in other.grounded_plan.response_plan.human_reception_plan.moves),
                                ("stay_with_current_burden", "honor_concrete_effort"))
        for source in ("部長が思ったより固くて、少しへこんだ。",
                       "作業を始めるのが遅れて、かえって助かった。"):
            frozen = freeze_text_source(_request_from_row(
                CMEEFinalIndependentFeelingSelectionTest.row(source),
            ))
            old = build_grounded_observation_plan(frozen.normalized_current_input,
                                                 evidence_spans=frozen.evidence_spans)
            new = build_final_stage1_grounded_observation_plan(frozen.normalized_current_input,
                                                              evidence_spans=frozen.evidence_spans)
            before = next(n for n in old.nuclei if n.source_fields == ("memo",))
            after = next(n for n in new.nuclei if n.source_fields == ("memo",))
            self.assertIn(self.marker, after.semantic_frame.attribute_codes)
            without_witness = replace(after, semantic_frame=replace(after.semantic_frame,
                attribute_codes=tuple(c for c in after.semantic_frame.attribute_codes if c != self.marker)))
            self.assertEqual(without_witness, before)
        legacy = build_grounded_observation_plan(inputs.source.normalized_current_input,
                                                evidence_spans=inputs.source.evidence_spans)
        self.assertEqual(legacy.response_plan.human_follow_target_ids, (action.nucleus_id,))


class CMEEFinalBackgroundFeelingSelectionTest(unittest.TestCase):
    """A complete cognitive background stays with the independently felt target."""

    marker = "lexical:source_current_feeling_with_cognitive_background"
    sources = (
        "何度も読み返したのに説明が理解できなくて、今は不安です。",
        "丁寧に聞いたのに手順がつかめなくて、少し悲しい。",
        "繰り返し確認したのに要点がのみ込めなくて、焦っている。",
    )

    @classmethod
    def setUpClass(cls):
        cls.artifacts = tuple(_full_surface_artifacts(
            CMEEFinalIndependentFeelingSelectionTest.row(source),
        ) for source in cls.sources)

    def test_whole_source_and_old_action_survive_selection_author_and_recovery(self):
        for source, a in zip(self.sources, self.artifacts):
            with self.subTest(source=source):
                self.assertTrue(a.gate.passed, a.gate.rejection_reasons)
                self.assertTrue(a.inverse.passed, a.inverse.failure_codes)
                moves = a.plan.response_plan.human_reception_plan.moves
                self.assertEqual(tuple(m.reception_act for m in moves),
                                 ("stay_with_current_burden", "honor_concrete_effort"))
                index = {n.nucleus_id: n for n in a.plan.nuclei}
                feeling = index[moves[0].target_nucleus_ids[0]]
                self.assertIn(self.marker, feeling.semantic_frame.attribute_codes)
                self.assertNotIn("lexical:source_declarative_feeling_subject",
                                 feeling.semantic_frame.attribute_codes)
                self.assertEqual(tuple(index[m.target_nucleus_ids[0]].source_fields for m in moves),
                                 (("memo",), ("memo_action",)))
                self.assertTrue(all(m.required and not m.support_nucleus_ids for m in moves))
                self.assertTrue(all(r.retention != "required" and r.type == "uncertain_connection"
                                    for r in a.plan.relations))
                self.assertEqual(tuple((d.reception_act, d.target_nucleus_ids, d.support_nucleus_ids)
                                       for d in a.selected_subjective_input.decisions),
                                 tuple((m.reception_act, m.target_nucleus_ids, m.support_nucleus_ids)
                                       for m in moves))
                for authored in a.authored:
                    self.assertEqual(set(authored.realized_move_ids), {m.move_id for m in moves})
                    sentence_plan = a.sentence_plan if authored.recovery_stage == "full" else (
                        surface_owner.build_reception_recovery_sentence_plan(
                            a.sentence_plan, a.plan, a.resolver, recovery_stage=authored.recovery_stage,
                        )
                    )
                    surface = _recovery_surface(a, sentence_plan)
                    # Anaphoric recovery keeps both selected duties while
                    # the observation still supplies their complete source.
                    self.assertIn(source.rstrip("。"), surface.text)
                    self.assertIn("作業台を片づけた", surface.text)
                    inverse = evaluate_grounded_surface_body_inverse(
                        body=surface.text.encode("utf-8"), plan=a.plan,
                        sentence_plan=sentence_plan, resolver=a.resolver,
                        selected_subjective_input=a.selected_subjective_input,
                    )
                    self.assertTrue(inverse.passed, inverse.failure_codes)
                self.assertIn(source.rstrip("。"), _reception_text(a.surface.text))
                for args, kwargs in a.author_arguments:
                    self.assertIs(kwargs["selected_subjective_input"], a.selected_subjective_input)
                inputs = _compile_inputs(CMEEFinalIndependentFeelingSelectionTest.row(source))
                resolver = build_evidence_span_resolver(inputs.source.evidence_spans,
                                                        current_input=inputs.source.normalized_current_input)
                for quality in ("grounded", "limited_grounding"):
                    semantic = _cmee_semantic_reception_plan(inputs.grounded_plan, resolver,
                                                            material_quality=quality)
                    self.assertEqual(semantic.moves, moves)

    def test_inverse_rejects_missing_feeling_action_or_only_its_background(self):
        source, a = self.sources[0].rstrip("。"), self.artifacts[0]
        for original in (source, "作業台を片づけた", source.split("、")[0] + "、"):
            with self.subTest(original=original):
                inverse = evaluate_grounded_surface_body_inverse(
                    body=_tamper_reception(a.surface.text, original, "").encode("utf-8"),
                    plan=a.plan, sentence_plan=a.sentence_plan, resolver=a.resolver,
                    selected_subjective_input=a.selected_subjective_input,
                )
                self.assertFalse(inverse.passed, inverse.failure_codes)

    def test_source_witness_rejects_foreign_owner_noncurrent_and_incomplete_field(self):
        base = self.sources[0]
        sources = (
            "友人が" + base, "私の友人が" + base,
            base.replace("説明が", "友人が"), base.replace("説明が", "友人の説明が"),
            base.replace("今は不安です", "友人は不安です"),
            base.replace("今は不安です", "不安だった"),
            base.replace("今は不安です", "不安ではない"),
            base.replace("今は不安です", "嬉しい"),
            base.replace("今は不安です", "不安かもしれない"),
            base.replace("今は不安です", "不安ですと聞いた"),
            base.replace("今は不安です", "不安なら休む"),
            base.replace("読み返したのに", "読み返すのに"),
            base.replace("読み返したのに", "読み返してもらったのに"),
            base.replace("読み返したのに", "読み返さなかったのに"),
            base.rstrip("。") + "？", base.rstrip("。") + "！",
            "「" + base.rstrip("。") + "」", base + "と友人が話した。",
            "友人は。" + base, base + "別の記録も読んだ。",
        )
        for source in sources:
            with self.subTest(source=source):
                frozen = freeze_text_source(_request_from_row(
                    CMEEFinalIndependentFeelingSelectionTest.row(source),
                ))
                plan = build_final_stage1_grounded_observation_plan(
                    frozen.normalized_current_input, evidence_spans=frozen.evidence_spans,
                )
                self.assertTrue(all(self.marker not in n.semantic_frame.attribute_codes for n in plan.nuclei))

    def test_required_relation_other_text_and_unperformed_action_keep_old_boundary(self):
        from emlis_ai_safety_triage import build_emlis_safety_triage_decision
        inputs = _compile_inputs(CMEEFinalIndependentFeelingSelectionTest.row(self.sources[0]))
        plan = inputs.grounded_plan
        feeling = next(n for n in plan.nuclei if n.source_fields == ("memo",))
        action = next(n for n in plan.nuclei if n.source_fields == ("memo_action",))
        required_relation = replace(plan.relations[0], type="contrast", retention="required",
                                    grounding_kind="user_stated_relation")
        variants = (
            (plan.nuclei, (required_relation,)),
            ((*plan.nuclei, replace(feeling, nucleus_id="public-third-theme", retention="optional")), plan.relations),
            (tuple(replace(n, retention="optional") if n == feeling else n for n in plan.nuclei), plan.relations),
        )
        for nuclei, relations in variants:
            response, _coverage, _surface, _safety = observation_plan_owner._build_response_and_policies(
                nuclei=nuclei, relations=relations,
                safety_decision=build_emlis_safety_triage_decision(current_input=inputs.source.normalized_current_input),
                complexity=plan.input_profile.semantic_complexity,
                material_quality=plan.input_profile.material_quality,
                include_reception_relation_support=True, final_source_fidelity=True,
            )
            self.assertEqual(response.human_follow_target_ids, (action.nucleus_id,))
        for action_text in ("作業台を片づけるつもり。", "作業台を片づけてもらった。", "作業台を片づけなかった。"):
            other = _compile_inputs(CMEEFinalIndependentFeelingSelectionTest.row(self.sources[0], action_text))
            self.assertNotEqual(tuple(m.reception_act for m in other.grounded_plan.response_plan.human_reception_plan.moves),
                                ("stay_with_current_burden", "honor_concrete_effort"))
        legacy = build_grounded_observation_plan(inputs.source.normalized_current_input,
                                                evidence_spans=inputs.source.evidence_spans)
        self.assertEqual(legacy.response_plan.human_follow_target_ids, (action.nucleus_id,))
