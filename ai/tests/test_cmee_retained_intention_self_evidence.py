# -*- coding: utf-8 -*-
from __future__ import annotations

"""Source-exact retained intentions may evidence their own reception Move."""

from dataclasses import replace
import json
from pathlib import Path
import unittest

from emlis_ai_current_input_bundle import build_emlis_current_input_bundle
from emlis_ai_evidence_ledger_service import build_evidence_span_resolver
from emlis_ai_grounded_observation_plan import (
    build_final_stage1_grounded_observation_plan,
    build_grounded_human_reception_plan,
    build_grounded_observation_plan,
)
from cocolon_meaning_experience_engine.contracts import GenerationRequest
import cocolon_meaning_experience_engine.emlis_v1a as vertical
from cocolon_meaning_experience_engine.source_kernel import freeze_text_source
from tools.cmee_v1a_i1sx_candidate_run import EXACT8


_AI_ROOT = Path(__file__).resolve().parents[1]
_BATCH_PATH = (
    _AI_ROOT / "tests" / "fixtures" / "emlis_nls_v3" / "generated"
    / "batch_001.jsonl"
)


def _request(
    *,
    record_id: str,
    thought_text: str,
    action_text: str = "",
    categories: tuple[str, ...] = ("生活",),
    emotions: tuple[dict[str, str], ...] = (
        {"type": "不安", "strength": "medium"},
    ),
) -> GenerationRequest:
    raw = {
        "id": record_id,
        "created_at": "2026-09-01T00:00:00Z",
        "memo": thought_text,
        "memo_action": action_text,
        "category": list(categories),
        "emotion_details": list(emotions),
        "emotions": [row["type"] for row in emotions],
        "is_secret": False,
    }
    return GenerationRequest(
        request_id=f"req-{record_id}",
        current_input_bundle=build_emlis_current_input_bundle(raw),
        expected_source_record_id=record_id,
    )


def _parts(request: GenerationRequest, *, final: bool):
    source = freeze_text_source(request)
    resolver = build_evidence_span_resolver(
        source.evidence_spans,
        current_input=source.normalized_current_input,
    )
    builder = (
        build_final_stage1_grounded_observation_plan
        if final
        else build_grounded_observation_plan
    )
    grounded_plan = builder(
        source.normalized_current_input,
        evidence_spans=source.evidence_spans,
    )
    return source, resolver, grounded_plan


def _raw_reception_plan(grounded_plan):
    response_plan = grounded_plan.response_plan
    return build_grounded_human_reception_plan(
        required=grounded_plan.coverage_requirements.human_follow_required,
        human_follow_target_ids=response_plan.human_follow_target_ids,
        primary_nucleus_ids=response_plan.primary_nucleus_ids,
        supporting_nucleus_ids=response_plan.supporting_nucleus_ids,
        required_nucleus_ids=response_plan.required_nucleus_ids,
        fact_boundary_nucleus_ids=response_plan.fact_boundary_nucleus_ids,
        nuclei=grounded_plan.nuclei,
        relations=grounded_plan.relations,
        safety_kind=grounded_plan.safety_policy.safety_kind,
        material_quality=vertical.CMEE_RECEPTION_MATERIAL_MODE,
        semantic_complexity=grounded_plan.input_profile.semantic_complexity,
    )


def _canonical_explicit_retained_intention_row() -> dict[str, object]:
    with _BATCH_PATH.open(encoding="utf-8") as stream:
        rows = (json.loads(line) for line in stream)
        return next(
            row
            for row in rows
            if "PRESERVE_DESIRE_TO_REDUCE_ACTIVITY_SWING"
            in row["semantic_contract"]["required_meaning_codes"]
        )


class CMEERetainedIntentionSelfEvidenceTest(unittest.TestCase):
    def test_source_explicit_retained_intention_keeps_exact_zero_support(
        self,
    ) -> None:
        row = _canonical_explicit_retained_intention_row()
        current_input = row["input"]
        request = _request(
            record_id=str(row["case_id"]),
            thought_text=str(current_input["thought_text"]),
            action_text=str(current_input["action_text"]),
            categories=tuple(current_input["categories"]),
            emotions=tuple(current_input["emotions"]),
        )
        _source, resolver, grounded_plan = _parts(request, final=True)
        initial_plan = _raw_reception_plan(grounded_plan)
        nucleus_index = {row.nucleus_id: row for row in grounded_plan.nuclei}

        self.assertTrue(
            vertical._cmee_target_self_evidences_retained_intention(
                initial_plan,
                nucleus_index=nucleus_index,
                resolver=resolver,
            )
        )
        reception_plan = vertical._cmee_semantic_reception_plan(
            grounded_plan,
            resolver,
        )
        self.assertEqual(reception_plan.support_nucleus_ids, ())
        self.assertEqual(
            reception_plan.source_evidence_span_ids,
            tuple(
                span_id
                for span_id in resolver.span_ids
                if span_id
                in {
                    evidence_id
                    for target_id in reception_plan.target_nucleus_ids
                    for evidence_id in nucleus_index[target_id].source_span_ids
                }
            ),
        )
        self.assertEqual(
            tuple(move.reception_act for move in reception_plan.moves),
            ("protect_retained_intention",),
        )
        self.assertTrue(
            all(not move.support_nucleus_ids for move in reception_plan.moves)
        )

    def test_kind_modality_or_semantic_role_can_own_the_same_evidence(
        self,
    ) -> None:
        row = _canonical_explicit_retained_intention_row()
        current_input = row["input"]
        request = _request(
            record_id="retained-intention-typed-alternatives",
            thought_text=str(current_input["thought_text"]),
            action_text=str(current_input["action_text"]),
            categories=tuple(current_input["categories"]),
            emotions=tuple(current_input["emotions"]),
        )
        _source, resolver, grounded_plan = _parts(request, final=True)
        reception_plan = _raw_reception_plan(grounded_plan)
        nucleus_index = {row.nucleus_id: row for row in grounded_plan.nuclei}
        target_id = reception_plan.target_nucleus_ids[0]
        target = nucleus_index[target_id]
        attributes_without_role = tuple(
            code
            for code in target.semantic_frame.attribute_codes
            if code != "semantic_role:retained_intention"
        )
        typed_alternatives = (
            replace(
                target,
                kind="wish",
                semantic_frame=replace(
                    target.semantic_frame,
                    modality="fact",
                    attribute_codes=attributes_without_role,
                ),
            ),
            replace(
                target,
                kind="state",
                semantic_frame=replace(
                    target.semantic_frame,
                    modality="intention",
                    attribute_codes=attributes_without_role,
                ),
            ),
            replace(
                target,
                kind="state",
                semantic_frame=replace(
                    target.semantic_frame,
                    modality="fact",
                ),
            ),
        )
        for typed_target in typed_alternatives:
            with self.subTest(
                kind=typed_target.kind,
                modality=typed_target.semantic_frame.modality,
            ):
                self.assertTrue(
                    vertical._cmee_target_self_evidences_retained_intention(
                        reception_plan,
                        nucleus_index={
                            **nucleus_index,
                            target_id: typed_target,
                        },
                        resolver=resolver,
                    )
                )

    def test_deliberation_keeps_separate_desire_support_and_rejects_burden(
        self,
    ) -> None:
        _case_id, memo, category, emotion, strength = EXACT8[5]
        request = _request(
            record_id="retained-intention-open-deliberation",
            thought_text=memo,
            categories=(category,),
            emotions=({"type": emotion, "strength": strength},),
        )
        _source, resolver, grounded_plan = _parts(request, final=False)
        initial_plan = _raw_reception_plan(grounded_plan)
        nucleus_index = {row.nucleus_id: row for row in grounded_plan.nuclei}
        self.assertFalse(
            vertical._cmee_target_self_evidences_retained_intention(
                initial_plan,
                nucleus_index=nucleus_index,
                resolver=resolver,
            )
        )
        reception_plan = vertical._cmee_semantic_reception_plan(
            grounded_plan,
            resolver,
        )
        self.assertEqual(len(reception_plan.support_nucleus_ids), 1)
        support_text = vertical._cmee_source_text(
            nucleus_index[reception_plan.support_nucleus_ids[0]],
            resolver,
        )
        self.assertTrue(vertical._cmee_desire_phrase(support_text))

        unrelated_request = _request(
            record_id="retained-intention-unrelated-burden",
            thought_text=(
                "仕事が忙しい。ずっとこのままなのが不安で、"
                "どうしたらいいのか考えている。"
            ),
        )
        _source, unrelated_resolver, unrelated_plan = _parts(
            unrelated_request,
            final=False,
        )
        with self.assertRaisesRegex(
            vertical.CMEEVerticalError,
            "bound_human_reception_retained_intention_evidence_missing",
        ):
            vertical._cmee_semantic_reception_plan(
                unrelated_plan,
                unrelated_resolver,
            )

    def test_negation_and_inexact_evidence_cannot_self_support(self) -> None:
        negated_request = _request(
            record_id="retained-intention-negated",
            thought_text="散歩したいとは全然思わない。",
        )
        _source, negated_resolver, negated_plan = _parts(
            negated_request,
            final=False,
        )
        negated_reception = _raw_reception_plan(negated_plan)
        negated_index = {row.nucleus_id: row for row in negated_plan.nuclei}
        self.assertFalse(
            vertical._cmee_target_self_evidences_retained_intention(
                negated_reception,
                nucleus_index=negated_index,
                resolver=negated_resolver,
            )
        )

        row = _canonical_explicit_retained_intention_row()
        current_input = row["input"]
        request = _request(
            record_id="retained-intention-inexact-evidence",
            thought_text=str(current_input["thought_text"]),
            action_text=str(current_input["action_text"]),
            categories=tuple(current_input["categories"]),
            emotions=tuple(current_input["emotions"]),
        )
        _source, resolver, grounded_plan = _parts(request, final=True)
        reception_plan = _raw_reception_plan(grounded_plan)
        nucleus_index = {row.nucleus_id: row for row in grounded_plan.nuclei}
        for inexact_plan in (
            replace(reception_plan, source_evidence_span_ids=()),
            replace(
                reception_plan,
                source_evidence_span_ids=tuple(resolver.span_ids),
            ),
        ):
            with self.subTest(evidence=inexact_plan.source_evidence_span_ids):
                self.assertFalse(
                    vertical._cmee_target_self_evidences_retained_intention(
                        inexact_plan,
                        nucleus_index=nucleus_index,
                        resolver=resolver,
                    )
                )

        target_id = reception_plan.target_nucleus_ids[0]
        unresolved_target = replace(
            nucleus_index[target_id],
            source_span_ids=(
                *nucleus_index[target_id].source_span_ids,
                "unresolved-span",
            ),
        )
        self.assertFalse(
            vertical._cmee_target_self_evidences_retained_intention(
                reception_plan,
                nucleus_index={
                    **nucleus_index,
                    target_id: unresolved_target,
                },
                resolver=resolver,
            )
        )
        negative_target = replace(
            nucleus_index[target_id],
            semantic_frame=replace(
                nucleus_index[target_id].semantic_frame,
                polarity="negative",
            ),
        )
        self.assertFalse(
            vertical._cmee_target_self_evidences_retained_intention(
                reception_plan,
                nucleus_index={
                    **nucleus_index,
                    target_id: negative_target,
                },
                resolver=resolver,
            )
        )


if __name__ == "__main__":
    unittest.main()
