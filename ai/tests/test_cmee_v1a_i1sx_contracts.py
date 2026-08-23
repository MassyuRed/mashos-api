# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import inspect
import json
import unittest
from collections import Counter
from dataclasses import fields, replace
from unittest.mock import patch

from emlis_ai_current_input_bundle import build_emlis_current_input_bundle
from emlis_ai_grounded_observation_plan import build_grounded_observation_plan
from cocolon_meaning_experience_engine import EngineStatus, GenerationRequest, MeaningExperienceEngine
from cocolon_meaning_experience_engine.contracts import (
    ArgumentBinding,
    ArgumentRole,
    AttachmentAdmission,
    CMEE_GROUNDED_GRAPH_SCHEMA_VERSION,
    CMEE_STAGE1_EMLIS_OWNER_REF,
    CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
    CMEE_STAGE1_TRACE_EXTENSION_SCHEMA_VERSION,
    CMEEStage1ContractError,
    ClauseFrame,
    EmlisInterpretationCandidate,
    EmlisMeaningField,
    EmlisStage1PositiveTraceExtension,
    EmlisStage1Projection,
    EmlisSubjectiveClaim,
    EmlisTraceClaimDomain,
    EpistemicState,
    ExperiencePlan,
    GroundedMeaningGraph,
    InterpretationEpistemicState,
    InterpretationKind,
    MeaningFieldEntry,
    MeaningFieldSlot,
    MeaningEdge,
    MeaningNode,
    ObservationContributionKind,
    ObservationDepthClass,
    OwnerClass,
    PlannedObservationContribution,
    ProviderResolution,
    RealizedSemanticBinding,
    RealizedSentenceUnit,
    RelationOperator,
    RouteBDisposition,
    RouteBOwnerDisposition,
    SemanticOperator,
    SubjectiveDepthClass,
    SubjectiveMode,
    SubjectiveOperator,
    SubjectiveProposition,
    TemperatureClass,
    VisibleAuthority,
    VisibleUnitTrace,
    recompute_stage1_identity,
    stage1_canonical_json_bytes,
    validate_stage1_identity,
    validate_stage1_local_ref_dag,
    validate_stage1_projection,
    validate_stage1_sentence_unit,
    validate_stage1_trace_spine,
    validate_version_qualified_ref,
)
import cocolon_meaning_experience_engine.emlis_stage1_response as stage1_response_module
from cocolon_meaning_experience_engine.emlis_stage1_response import (
    INTERPRETATION_CANDIDATE_KIND_CAP,
    INTERPRETATION_CANDIDATE_POOL_CAP,
    INTERPRETATION_MATRIX_EXACT13,
    build_emlis_meaning_field,
    build_interpretation_candidate_pool,
    build_layer1_semantics,
    classify_observation_depth,
    validate_emlis_meaning_field,
    validate_layer1_observation_plan,
)
from cocolon_meaning_experience_engine.emlis_v1a import (
    _build_experience_plan,
    _build_graph,
    _ordered,
    _planned_visible_source_ids,
)
from cocolon_meaning_experience_engine.source_kernel import (
    SourceAdmissionError,
    _evidence_id,
    _source_envelope_id,
    build_source_owner_universe,
    freeze_text_source,
    normalize_evidence_literal,
)
from tools.cmee_v1a_i1sx_candidate_run import EXACT8


SAMPLE_MEMO = "仕事が続いて疲れていて、朝から何も手につかない。"


def _with_recomputed_evidence_id(row: object) -> object:
    return replace(
        row,
        evidence_id=_evidence_id(
            envelope_id=row.source_envelope_id,
            source_span_id=row.source_span_id,
            field_path=row.field_path,
            element_index=row.element_index,
            field_utf8_start=row.field_utf8_start,
            field_utf8_end=row.field_utf8_end,
            scalar_start=row.scalar_start,
            scalar_end=row.scalar_end,
            utf8_start=row.utf8_start,
            utf8_end=row.utf8_end,
            field_sha256=row.field_sha256,
            literal_sha256=row.literal_sha256,
        ),
    )


def _request(
    *,
    record_id: str = "cmee-contract-1",
    memo: str = SAMPLE_MEMO,
    action: str = "",
    category: str = "生活",
    emotion: str = "不安",
    strength: str = "medium",
    **request_overrides: object,
) -> GenerationRequest:
    raw = {
        "id": record_id,
        "created_at": "2026-08-15T00:00:00Z",
        "memo": memo,
        "memo_action": action,
        "category": [category],
        "emotion_details": [{"type": emotion, "strength": strength}],
        "emotions": [emotion],
        "is_secret": False,
    }
    values: dict[str, object] = {
        "request_id": f"req-{record_id}",
        "current_input_bundle": build_emlis_current_input_bundle(raw),
        "expected_source_record_id": record_id,
    }
    values.update(request_overrides)
    return GenerationRequest(**values)


def _stage2_inputs(request: GenerationRequest):
    source = freeze_text_source(request)
    grounded_plan = build_grounded_observation_plan(
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
    return source, grounded_plan, graph, parent_plan


def _identified(value: object, identity_field: str) -> object:
    return replace(value, **{identity_field: recompute_stage1_identity(value)})


def _stage1_grounded_graph_fixture() -> GroundedMeaningGraph:
    return GroundedMeaningGraph(
        graph_id="grounded-1",
        source_envelope_id="source-1",
        nodes=(
            MeaningNode(
                node_id="state-1",
                owner_id="owner-state-1",
                node_kind="STATE",
                grounding_kind="explicit",
                value="状態",
                epistemic_state=EpistemicState.SOURCE_EXPLICIT,
                evidence_ids=("memo-1",),
            ),
            MeaningNode(
                node_id="context-1",
                owner_id="owner-context-1",
                node_kind="state",
                grounding_kind="explicit",
                value="文脈",
                epistemic_state=EpistemicState.SOURCE_EXPLICIT,
                evidence_ids=("memo-1",),
            ),
            MeaningNode(
                node_id="other-1",
                owner_id="owner-other-1",
                node_kind="OTHER",
                grounding_kind="explicit",
                value="別対象",
                epistemic_state=EpistemicState.SOURCE_EXPLICIT,
                evidence_ids=("memo-1",),
            ),
        ),
        edges=(),
        owner_dispositions=(),
        required_owner_refs=(),
        active_optional_owner_refs=(),
        source_version="source.v1",
        obligation_version="obligation.v1",
        owner_universe_digest="digest",
    )


def _stage1_projection_fixture() -> EmlisStage1Projection:
    schema = CMEE_STAGE1_RESPONSE_SCHEMA_VERSION
    graph_ref = f"grounded:grounded-1@{CMEE_GROUNDED_GRAPH_SCHEMA_VERSION}"
    observation_duty_ref = "observation-duty-1"
    reception_duty_ref = "reception-duty-1"
    semantic_refs = (
        f"node:state-1@{CMEE_GROUNDED_GRAPH_SCHEMA_VERSION}",
        f"node:context-1@{CMEE_GROUNDED_GRAPH_SCHEMA_VERSION}",
    )
    evidence_refs = ("evidence:memo-1@source.v1",)
    candidate_1 = _identified(
        EmlisInterpretationCandidate(
            schema_version=schema,
            candidate_id="",
            candidate_kind=InterpretationKind.DIRECT_STATE,
            claim_domain=EmlisTraceClaimDomain.INTERPRETIVE_OBSERVATION.value,
            semantic_operator=SemanticOperator.PRESENT_STATE,
            argument_bindings=(
                ArgumentBinding(ArgumentRole.PRIMARY, semantic_refs[0]),
            ),
            relation_operator=RelationOperator.NO_RELATION_CLAIM,
            relation_basis_refs=(),
            derivation_rule_id=(
                "cocolon.cmee.v1a.stage1.direct.direct_state.v1"
            ),
            semantic_refs=(semantic_refs[0],),
            evidence_refs=evidence_refs,
            basis_candidate_refs=(),
            epistemic_state=(
                InterpretationEpistemicState.PROVISIONAL_INTERPRETATION
            ),
            required_qualifiers=("epistemic:provisional_interpretation",),
            forbidden_promotions=stage1_response_module._FORBIDDEN_PROMOTIONS,
        ),
        "candidate_id",
    )
    candidate_2 = _identified(
        EmlisInterpretationCandidate(
            schema_version=schema,
            candidate_id="",
            candidate_kind=InterpretationKind.DIRECT_STATE,
            claim_domain=EmlisTraceClaimDomain.INTERPRETIVE_OBSERVATION.value,
            semantic_operator=SemanticOperator.PRESENT_BURDEN,
            argument_bindings=(
                ArgumentBinding(ArgumentRole.PRIMARY, semantic_refs[1]),
            ),
            relation_operator=RelationOperator.NO_RELATION_CLAIM,
            relation_basis_refs=(),
            derivation_rule_id=(
                "cocolon.cmee.v1a.stage1.direct.direct_state.v1"
            ),
            semantic_refs=(semantic_refs[1],),
            evidence_refs=evidence_refs,
            basis_candidate_refs=(candidate_1.candidate_id,),
            epistemic_state=(
                InterpretationEpistemicState.PROVISIONAL_INTERPRETATION
            ),
            required_qualifiers=("epistemic:provisional_interpretation",),
            forbidden_promotions=stage1_response_module._FORBIDDEN_PROMOTIONS,
        ),
        "candidate_id",
    )
    meaning_field = _identified(
        EmlisMeaningField(
            schema_version=schema,
            meaning_field_id="",
            grounded_graph_ref=graph_ref,
            center_candidate_ref=candidate_1.candidate_id,
            entries=(
                MeaningFieldEntry(
                    slot=MeaningFieldSlot.CENTER,
                    interpretation_candidate_refs=(candidate_1.candidate_id,),
                    semantic_refs=(semantic_refs[0],),
                    evidence_refs=evidence_refs,
                ),
                MeaningFieldEntry(
                    slot=MeaningFieldSlot.BURDEN,
                    interpretation_candidate_refs=(candidate_2.candidate_id,),
                    semantic_refs=(semantic_refs[1],),
                    evidence_refs=evidence_refs,
                ),
            ),
            required_candidate_refs=(candidate_1.candidate_id,),
            material_unknown_refs=(),
        ),
        "meaning_field_id",
    )
    contribution = _identified(
        PlannedObservationContribution(
            schema_version=schema,
            contribution_id="",
            parent_duty_ref=observation_duty_ref,
            contribution_kind=ObservationContributionKind.OBSERVE_CENTER,
            interpretation_candidate_refs=(candidate_1.candidate_id,),
            semantic_operator=SemanticOperator.PRESENT_STATE,
            argument_bindings=(
                ArgumentBinding(ArgumentRole.PRIMARY, semantic_refs[0]),
            ),
            relation_operator=RelationOperator.NO_RELATION_CLAIM,
            relation_basis_refs=(),
            derivation_rule_id=(
                "cocolon.cmee.v1a.stage1.layer1.observe_center.v1"
            ),
            semantic_refs=(semantic_refs[0],),
            evidence_refs=evidence_refs,
            retention="REQUIRED",
            semantic_key_version=(
                stage1_response_module.OBSERVATION_SEMANTIC_KEY_VERSION
            ),
            canonical_semantic_key=stage1_response_module._semantic_key(
                candidate_1
            ),
            prerequisite_contribution_refs=(),
            forbidden_operations=(
                stage1_response_module._FORBIDDEN_OBSERVATION_OPERATIONS
            ),
        ),
        "contribution_id",
    )
    proposition = SubjectiveProposition(
        subjective_operator=SubjectiveOperator.ATTEND_TO,
        target_contribution_refs=(contribution.contribution_id,),
        response_object_refs=(contribution.contribution_id,),
        affect_category=None,
        affect_intensity=None,
        stance_operator=None,
        counterposition_target_ref=None,
        referenced_actor_refs=(),
        referenced_experiencer_refs=(),
        addressee_role="NONE",
        polarity="neutral",
        modality="feeling",
    )
    claim = _identified(
        EmlisSubjectiveClaim(
            schema_version=schema,
            subjective_claim_id="",
            parent_duty_ref=reception_duty_ref,
            speaker_owner="EMLIS",
            claim_domain=EmlisTraceClaimDomain.SUBJECTIVE_RESPONSE.value,
            subjective_mode=SubjectiveMode.ATTENTION,
            asserted_subjective_proposition=proposition,
            basis_observation_contribution_refs=(contribution.contribution_id,),
            basis_semantic_refs=semantic_refs,
            source_reception_act_refs=("ATTEND_CURRENT_MATERIAL",),
            value_principle_refs=(),
            user_fact_effect=0,
            forbidden_promotions=("user-feeling-attribution",),
        ),
        "subjective_claim_id",
    )
    return _identified(
        EmlisStage1Projection(
            schema_version=schema,
            projection_id="",
            grounded_graph_ref=graph_ref,
            parent_observation_duty_ref=observation_duty_ref,
            parent_reception_duty_ref=reception_duty_ref,
            interpretation_candidates=(candidate_1, candidate_2),
            meaning_field=meaning_field,
            observation_contributions=(contribution,),
            subjective_claims=(claim,),
            ordered_observation_refs=(contribution.contribution_id,),
            ordered_subjective_refs=(claim.subjective_claim_id,),
            retained_reception_act_ids=("ATTEND_CURRENT_MATERIAL",),
            observation_depth_class=ObservationDepthClass.FOCUSED,
            subjective_depth_class=SubjectiveDepthClass.FOCUSED,
            temperature_class=TemperatureClass.STANDARD,
            reception_style_policy_ref="policy:reception-style@policy.v1",
            emlis_value_policy_ref="policy:emlis-value@policy.v1",
            emlis_microgrammar_policy_ref="policy:emlis-microgrammar@policy.v1",
        ),
        "projection_id",
    )


def _stage1_parent_plan_fixture(
    projection: EmlisStage1Projection,
) -> ExperiencePlan:
    return ExperiencePlan(
        plan_id="plan-1",
        source_envelope_id="source-1",
        source_version="source.v1",
        obligation_version="obligation.v1",
        owner_universe_digest="digest",
        source_plan_version="plan.v1",
        observation_duty_id=projection.parent_observation_duty_ref,
        unknown_duty_id="unknown-duty-1",
        reception_duty_id=projection.parent_reception_duty_ref,
        reception_plan_digest="reception-digest",
        allowed_reception_act_ids=projection.retained_reception_act_ids,
        required_observation_owner_ids=(),
        reception_target_owner_ids=(),
        visible_owner_ids=(),
        unresolved_owner_ids=(),
        visible_unknown_owner_ids=(),
        required_unknown_owner_ids=(),
        visible_line_ids=(),
    )


def _stage1_sentence_unit_fixture(
    projection: EmlisStage1Projection,
) -> RealizedSentenceUnit:
    text = "見えた"
    binding = RealizedSemanticBinding(
        semantic_ref=f"node:state-1@{CMEE_GROUNDED_GRAPH_SCHEMA_VERSION}",
        clause_slot="predicate",
        surface_scalar_start=0,
        surface_scalar_end=len(text),
        surface_span_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
    )
    unit = RealizedSentenceUnit(
        unit_id="",
        projection_ref=projection.projection_id,
        layer="LAYER_1",
        move_ref="move:observe@microgrammar.v1",
        clause_frames=(
            ClauseFrame(
                move_ref="move:observe@microgrammar.v1",
                discourse_relation="OPEN",
                topic_ref=f"node:state-1@{CMEE_GROUNDED_GRAPH_SCHEMA_VERSION}",
                predicate_operator=SemanticOperator.PRESENT_STATE.value,
                object_ref=None,
                argument_bindings=(
                    ArgumentBinding(
                        ArgumentRole.PRIMARY,
                        f"node:state-1@{CMEE_GROUNDED_GRAPH_SCHEMA_VERSION}",
                    ),
                ),
                qualifier_refs=(),
                polarity="neutral",
                modality="fact",
                time_scope="present",
                actor_refs=(),
                experiencer_refs=(),
                addressee_role="NONE",
                epistemic_marker="provisional",
                speaker_marker=None,
                connective_requirement=None,
                reception_style_policy_ref="policy:reception-style@policy.v1",
                terminal_style="declarative",
            ),
        ),
        text=text,
        basis_anchor_refs=(
            projection.observation_contributions[0].contribution_id,
        ),
        realized_semantic_bindings=(binding,),
        discourse_link_to_prior_sentence=None,
        composition_variant_id="primary.v1",
    )
    return _identified(unit, "unit_id")


class CMEEV1AI1SXContractsTest(unittest.TestCase):
    def test_body_free_projection_never_contains_private_body_digest_or_locator(self) -> None:
        outcome = MeaningExperienceEngine().generate(_request())

        self.assertEqual(outcome.status.value, "GENERATED", outcome.reason_codes)
        report = outcome.as_body_free()
        serialized = json.dumps(report, ensure_ascii=False, sort_keys=True)
        for forbidden in (
            "疲れている",
            "生活",
            "自己理解",
            "cmee-contract-1",
            "raw_sha256",
            "literal_sha256",
            "scalar_start",
            "scalar_end",
            "envelope_id",
            "graph_id",
            "artifact_id",
        ):
            self.assertNotIn(forbidden, serialized)
        self.assertNotIn("observation", report)
        self.assertNotIn("reception", report)
        self.assertEqual(report["status"], "GENERATED")
        self.assertTrue(report["artifact_present"])
        self.assertGreaterEqual(report["observation_unit_count"], 1)
        self.assertEqual(report["unknown_unit_count"], 0)
        self.assertEqual(report["unknown_trace_count"], 0)
        self.assertEqual(report["reception_unit_count"], 1)
        self.assertFalse(report["product_read_evaluated"])
        self.assertEqual(report["implementation_state"], "DRAFT_WIP_DISABLED")
        self.assertFalse(report["route_b_contract_complete"])
        self.assertFalse(report["candidate_ready"])
        self.assertFalse(report["product_read_eligible"])
        self.assertFalse(report["exact8_acceptance_complete"])
        self.assertEqual(report["production_effect"], 0)
        self.assertFalse(report["automatic_progression"])

    def test_source_envelope_locators_are_exact_and_bound_to_one_envelope(self) -> None:
        source = freeze_text_source(_request())
        self.assertEqual(
            source.envelope.source_contract_version,
            "cocolon.cmee.emlis.current_input.text_grounded.v2",
        )
        self.assertGreaterEqual(len(source.evidence_refs), 4)
        self.assertEqual(len({row.evidence_id for row in source.evidence_refs}), len(source.evidence_refs))
        for ref in source.evidence_refs:
            selected = source.envelope.raw_utf8[ref.utf8_start : ref.utf8_end]
            self.assertEqual(hashlib.sha256(selected).hexdigest(), ref.literal_sha256)
            field = source.envelope.raw_utf8[ref.field_utf8_start : ref.field_utf8_end]
            self.assertEqual(hashlib.sha256(field).hexdigest(), ref.field_sha256)
            field_text = field.decode("utf-8")
            self.assertEqual(
                field_text[ref.scalar_start : ref.scalar_end].encode("utf-8"),
                selected,
            )
            self.assertEqual(
                ref.utf8_start,
                ref.field_utf8_start
                + len(field_text[: ref.scalar_start].encode("utf-8")),
            )
            self.assertEqual(
                ref.utf8_end,
                ref.field_utf8_start
                + len(field_text[: ref.scalar_end].encode("utf-8")),
            )
            self.assertLessEqual(ref.field_utf8_start, ref.utf8_start)
            self.assertLessEqual(ref.utf8_end, ref.field_utf8_end)
            self.assertEqual(ref.source_envelope_id, source.envelope.envelope_id)
        memo_ref = next(row for row in source.evidence_refs if row.field_path == "memo")
        self.assertEqual(memo_ref.element_index, -1)
        strength_ref = next(
            row for row in source.evidence_refs if row.source_span_id == "structured:emotion_strength"
        )
        self.assertEqual(strength_ref.field_path, "emotion_details.0.strength")
        self.assertEqual(strength_ref.element_index, 0)

    def test_owner_universe_recompute_rejects_forged_evidence_digests(self) -> None:
        source = freeze_text_source(_request())
        category_index = next(
            index
            for index, row in enumerate(source.evidence_refs)
            if row.field_path == "category.0"
        )
        forged_refs = list(source.evidence_refs)
        forged_refs[category_index] = replace(
            forged_refs[category_index],
            evidence_id="ev-000000000000000000000000",
            literal_sha256="0" * 64,
            field_sha256="0" * 64,
        )

        with self.assertRaisesRegex(SourceAdmissionError, "evidence_digest_invalid"):
            build_source_owner_universe(source.envelope, tuple(forged_refs))

    def test_scalar_and_utf8_ranges_identify_the_same_repeated_occurrence(self) -> None:
        source = freeze_text_source(
            _request(record_id="cmee-scalar-occurrence", memo="🙂同じ。🙂同じ。")
        )
        memo_rows = tuple(row for row in source.evidence_refs if row.field_path == "memo")
        self.assertEqual(len(memo_rows), 2)
        first, second = memo_rows
        self.assertEqual(
            source.envelope.raw_utf8[first.utf8_start : first.utf8_end],
            source.envelope.raw_utf8[second.utf8_start : second.utf8_end],
        )
        self.assertNotEqual(
            (first.scalar_start, first.scalar_end),
            (second.scalar_start, second.scalar_end),
        )
        self.assertNotEqual(
            (first.utf8_start, first.utf8_end),
            (second.utf8_start, second.utf8_end),
        )

        forged = _with_recomputed_evidence_id(
            replace(
                first,
                scalar_start=second.scalar_start,
                scalar_end=second.scalar_end,
            )
        )
        forged_refs = tuple(forged if row is first else row for row in source.evidence_refs)
        with self.assertRaisesRegex(SourceAdmissionError, "canonical_binding_invalid"):
            build_source_owner_universe(source.envelope, forged_refs)

        bool_forged = _with_recomputed_evidence_id(replace(first, scalar_start=True))
        bool_refs = tuple(
            bool_forged if row is first else row for row in source.evidence_refs
        )
        with self.assertRaisesRegex(SourceAdmissionError, "canonical_binding_invalid"):
            build_source_owner_universe(source.envelope, bool_refs)

    def test_whitespace_mapping_preserves_raw_bytes_and_engine_validation(self) -> None:
        memo = "  仕事が  続いて\t疲れていて、\u3000\u3000朝から何も手につかない。  "
        request = _request(record_id="cmee-whitespace", memo=memo)
        source = freeze_text_source(request)
        memo_rows = tuple(row for row in source.evidence_refs if row.field_path == "memo")

        self.assertEqual(len(memo_rows), 1)
        row = memo_rows[0]
        field_text = source.envelope.raw_utf8[
            row.field_utf8_start : row.field_utf8_end
        ].decode("utf-8")
        literal = source.envelope.raw_utf8[row.utf8_start : row.utf8_end].decode(
            "utf-8"
        )
        self.assertEqual(field_text, memo)
        self.assertEqual(
            literal,
            "仕事が  続いて\t疲れていて、\u3000\u3000朝から何も手につかない",
        )
        self.assertEqual(field_text[row.scalar_start : row.scalar_end], literal)
        span = next(
            span
            for span in source.evidence_spans
            if str(getattr(span, "span_id", "")) == row.source_span_id
        )
        self.assertEqual(
            normalize_evidence_literal(literal),
            str(getattr(span, "raw_text", "")),
        )

        outcome = MeaningExperienceEngine().generate(request)
        self.assertEqual(outcome.status, EngineStatus.GENERATED, outcome.reason_codes)
        self.assertIsNotNone(outcome.artifact)

    def test_canonical_field_binding_rejects_coordinated_other_field_redirect(self) -> None:
        source = freeze_text_source(_request(record_id="cmee-field-redirect"))
        category_index = next(
            index
            for index, row in enumerate(source.evidence_refs)
            if row.field_path == "category.0"
        )
        category = source.evidence_refs[category_index]
        memo = next(row for row in source.evidence_refs if row.field_path == "memo")
        redirected = _with_recomputed_evidence_id(
            replace(
                category,
                field_utf8_start=memo.field_utf8_start,
                field_utf8_end=memo.field_utf8_end,
                scalar_start=memo.scalar_start,
                scalar_end=memo.scalar_end,
                utf8_start=memo.utf8_start,
                utf8_end=memo.utf8_end,
                field_sha256=memo.field_sha256,
                literal_sha256=memo.literal_sha256,
            )
        )
        forged_refs = list(source.evidence_refs)
        forged_refs[category_index] = redirected

        with self.assertRaisesRegex(SourceAdmissionError, "canonical_binding_invalid"):
            build_source_owner_universe(source.envelope, tuple(forged_refs))

    def test_canonical_source_span_binding_rejects_equal_literal_swap(self) -> None:
        source = freeze_text_source(_request(record_id="cmee-span-swap"))
        detail_index = next(
            index
            for index, row in enumerate(source.evidence_refs)
            if row.field_path == "emotion_details.0.type"
        )
        simple_index = next(
            index
            for index, row in enumerate(source.evidence_refs)
            if row.field_path == "emotions.0"
        )
        detail = source.evidence_refs[detail_index]
        simple = source.evidence_refs[simple_index]
        self.assertEqual(detail.literal_sha256, simple.literal_sha256)
        forged_refs = list(source.evidence_refs)
        forged_refs[detail_index] = _with_recomputed_evidence_id(
            replace(detail, source_span_id=simple.source_span_id)
        )
        forged_refs[simple_index] = _with_recomputed_evidence_id(
            replace(simple, source_span_id=detail.source_span_id)
        )

        with self.assertRaisesRegex(SourceAdmissionError, "canonical_binding_invalid"):
            build_source_owner_universe(source.envelope, tuple(forged_refs))

    def test_source_envelope_metadata_is_independently_reconstructed(self) -> None:
        source = freeze_text_source(_request(record_id="cmee-envelope-identity"))
        mutations = {
            "source_record_id": "different-record",
            "source_schema_version": "emlis.current_input_bundle.v999",
            "label_contract_id": "cocolon.input_options.forged",
            "label_contract_digest": "0" * 64,
        }
        for field_name, value in mutations.items():
            with self.subTest(field_name=field_name):
                tampered = replace(source.envelope, **{field_name: value})
                with self.assertRaisesRegex(SourceAdmissionError, "source_envelope"):
                    build_source_owner_universe(tampered, source.evidence_refs)

        changed_record = "coordinated-different-record"
        coordinated_id = _source_envelope_id(
            source_record_id=changed_record,
            source_role=source.envelope.source_role,
            source_schema_version=source.envelope.source_schema_version,
            source_contract_version=source.envelope.source_contract_version,
            source_encoding=source.envelope.source_encoding,
            label_contract_id=source.envelope.label_contract_id,
            label_contract_digest=source.envelope.label_contract_digest,
            raw_sha256=source.envelope.raw_sha256,
        )
        coordinated_envelope = replace(
            source.envelope,
            source_record_id=changed_record,
            envelope_id=coordinated_id,
        )
        coordinated_refs = tuple(
            _with_recomputed_evidence_id(
                replace(row, source_envelope_id=coordinated_id)
            )
            for row in source.evidence_refs
        )
        with self.assertRaisesRegex(SourceAdmissionError, "source_envelope_identity"):
            build_source_owner_universe(coordinated_envelope, coordinated_refs)

    def test_route_b_disposition_contract_is_exact_six(self) -> None:
        self.assertEqual(
            {row.value for row in RouteBDisposition},
            {
                "SOURCE_EXPLICIT_VISIBLE",
                "SUPPLEMENTAL_USER_VISIBLE",
                "UNKNOWN_PRESERVED_LIMITED",
                "CLARIFICATION_TARGET",
                "NOT_VISIBLE_UNRESOLVED",
                "SEPARATE_SAFETY",
            },
        )

    def test_route_b_owner_disposition_has_the_complete_approved_shape(self) -> None:
        self.assertEqual(
            tuple(row.name for row in fields(RouteBOwnerDisposition)),
            (
                "meaning_owner_id",
                "owner_class",
                "provider_resolution",
                "attachment_admission",
                "visible_authority",
                "route_b_disposition",
                "visible_claim_refs",
                "evidence_refs",
                "target_unknown_ref",
                "reason_codes",
            ),
        )
        self.assertEqual({row.value for row in OwnerClass}, {"REQUIRED", "ACTIVE_OPTIONAL"})
        self.assertEqual(
            {row.value for row in ProviderResolution},
            {"UNIQUE", "AMBIGUOUS", "UNRESOLVED", "MISSING_OR_INVALID"},
        )
        self.assertEqual(
            {row.value for row in AttachmentAdmission},
            {"PROVISIONAL_ONLY", "UNRESOLVED", "UNAVAILABLE"},
        )
        self.assertEqual(
            {row.value for row in VisibleAuthority},
            {"SOURCE_EXPLICIT", "SUPPLEMENTAL_USER", "NONE"},
        )

    def test_owner_universe_is_frozen_from_source_before_the_legacy_plan(self) -> None:
        with patch(
            "cocolon_meaning_experience_engine.emlis_v1a.build_grounded_observation_plan",
            side_effect=AssertionError("legacy plan must not define U"),
        ):
            source = freeze_text_source(_request())

        universe = source.owner_universe
        source_obligations = tuple(
            row
            for row in universe.obligations
            if row.obligation_kind != "STRUCTURED_CONTEXT_ATTACHMENT"
        )
        self.assertEqual(
            {evidence_id for row in source_obligations for evidence_id in row.evidence_refs},
            {row.evidence_id for row in source.evidence_refs},
        )
        self.assertEqual(
            sum(len(row.evidence_refs) for row in source_obligations),
            len(source.evidence_refs),
        )
        self.assertEqual(
            tuple(row.meaning_owner_id for row in universe.obligations),
            universe.required_owner_refs + universe.active_optional_owner_refs,
        )
        self.assertEqual(len(universe.credit_only_owner_refs), 1)
        emotion_owner = next(
            row for row in universe.obligations if row.obligation_kind == "EMOTION_CONTEXT"
        )
        self.assertEqual(len(emotion_owner.evidence_refs), 2)
        attachment_owner = next(
            row
            for row in universe.obligations
            if row.obligation_kind == "STRUCTURED_CONTEXT_ATTACHMENT"
        )
        self.assertEqual(attachment_owner.owner_class, OwnerClass.ACTIVE_OPTIONAL)
        self.assertTrue(attachment_owner.evidence_refs)
        self.assertEqual(
            freeze_text_source(_request()).owner_universe,
            universe,
        )

        other = freeze_text_source(_request(record_id="cmee-contract-2"))
        self.assertNotEqual(
            other.owner_universe.owner_universe_digest,
            universe.owner_universe_digest,
        )
        self.assertTrue(
            set(other.owner_universe.required_owner_refs).isdisjoint(
                universe.required_owner_refs
            )
        )
        with_action = freeze_text_source(
            _request(
                record_id="cmee-contract-action",
                action="今日は早く休んだ。",
            )
        )
        self.assertEqual(len(with_action.owner_universe.required_owner_refs), 2)
        self.assertEqual(with_action.owner_universe.credit_only_owner_refs, ())

    def test_engine_status_contract_is_exact_six(self) -> None:
        self.assertEqual(
            {row.value for row in EngineStatus},
            {
                "GENERATED",
                "LIMITED",
                "QUESTION_PENDING",
                "UNAVAILABLE",
                "SEPARATE_SAFETY",
                "REJECTED",
            },
        )

    def test_original_field_locators_preserve_whitespace_and_repeated_spans(self) -> None:
        request = _request(memo="　同じ。同じ。  ")
        source = freeze_text_source(request)
        memo_refs = tuple(row for row in source.evidence_refs if row.field_path == "memo")

        self.assertEqual(len(memo_refs), 2)
        self.assertNotEqual(memo_refs[0].utf8_start, memo_refs[1].utf8_start)
        field_bodies = {
            source.envelope.raw_utf8[row.field_utf8_start : row.field_utf8_end]
            for row in memo_refs
        }
        self.assertEqual(field_bodies, {"　同じ。同じ。  ".encode("utf-8")})
        self.assertEqual(
            [
                source.envelope.raw_utf8[row.utf8_start : row.utf8_end].decode("utf-8")
                for row in memo_refs
            ],
            ["同じ", "同じ"],
        )
        self.assertTrue(all(row.element_index == -1 for row in memo_refs))

    def test_wrong_core_job_and_mode_are_rejected_without_source_admission(self) -> None:
        engine = MeaningExperienceEngine()
        cases = (
            _request(core_id="piece"),
            _request(product_job="GENERATE_PIECE"),
            _request(execution_mode="PRODUCTION"),
        )
        for request in cases:
            with self.subTest(request=request):
                outcome = engine.generate(request)
                self.assertEqual(outcome.status.value, "REJECTED")
                self.assertIsNone(outcome.artifact)
                self.assertIsNone(outcome.source_envelope)
                self.assertFalse(outcome.automatic_progression)

    def test_source_lineage_violation_is_rejected_but_thin_input_is_unavailable(self) -> None:
        mismatch = MeaningExperienceEngine().generate(
            _request(expected_source_record_id="different-record")
        )
        labels_only = MeaningExperienceEngine().generate(_request(memo=""))

        self.assertEqual(mismatch.status.value, "REJECTED")
        self.assertEqual(mismatch.reason_codes, ("source_record_binding_mismatch",))
        self.assertIsNone(mismatch.artifact)
        self.assertEqual(labels_only.status.value, "UNAVAILABLE")
        self.assertEqual(labels_only.reason_codes, ("text_grounded_material_required",))
        self.assertIsNone(labels_only.artifact)


class CMEEStage1SpineContractsTest(unittest.TestCase):
    def test_exact_six_identities_recompute_and_reject_stale_tamper(self) -> None:
        projection = _stage1_projection_fixture()
        grounded_graph = _stage1_grounded_graph_fixture()
        parent_plan = _stage1_parent_plan_fixture(projection)
        unit = _stage1_sentence_unit_fixture(projection)
        exact_six = (
            projection.interpretation_candidates[0],
            projection.meaning_field,
            projection.observation_contributions[0],
            projection.subjective_claims[0],
            projection,
            unit,
        )

        prefixes = set()
        for value in exact_six:
            validate_stage1_identity(value)
            identity = recompute_stage1_identity(value)
            self.assertRegex(identity, r"^[a-z-]+-[0-9a-f]{64}$")
            prefixes.add(identity.rsplit("-", 1)[0])
        self.assertEqual(
            prefixes,
            {
                "candidate",
                "meaning-field",
                "contribution",
                "subjective-claim",
                "projection",
                "unit",
            },
        )

        candidate = projection.interpretation_candidates[0]
        stale = replace(candidate, semantic_operator=SemanticOperator.PRESENT_CHANGE)
        with self.assertRaisesRegex(CMEEStage1ContractError, "identity_mismatch"):
            validate_stage1_identity(stale)
        stale_projection = replace(
            projection,
            interpretation_candidates=(
                stale,
                projection.interpretation_candidates[1],
            ),
        )
        with self.assertRaisesRegex(CMEEStage1ContractError, "identity_mismatch"):
            validate_stage1_projection(
                stale_projection,
                grounded_graph=grounded_graph,
                parent_plan=parent_plan,
            )

    def test_canonical_json_key_order_is_invariant_but_semantic_order_changes_id(self) -> None:
        left = {"日本語": "見えた", "nested": {"b": 2, "a": 1}}
        right = {"nested": {"a": 1, "b": 2}, "日本語": "見えた"}
        self.assertEqual(
            stage1_canonical_json_bytes(left),
            stage1_canonical_json_bytes(right),
        )

        projection = _stage1_projection_fixture()
        candidate = projection.interpretation_candidates[0]
        meaning_field = projection.meaning_field
        self.assertNotEqual(
            recompute_stage1_identity(meaning_field),
            recompute_stage1_identity(
                replace(
                    meaning_field,
                    entries=tuple(reversed(meaning_field.entries)),
                )
            ),
        )
        qualifier_ordered = replace(
            candidate,
            required_qualifiers=("qualifier:a", "qualifier:b"),
        )
        self.assertNotEqual(
            recompute_stage1_identity(qualifier_ordered),
            recompute_stage1_identity(
                replace(
                    qualifier_ordered,
                    required_qualifiers=tuple(
                        reversed(qualifier_ordered.required_qualifiers)
                    ),
                )
            ),
        )
        for tampered in (
            replace(
                projection,
                observation_depth_class=ObservationDepthClass.LAYERED,
            ),
            replace(projection, temperature_class=TemperatureClass.ELEVATED_NON_SAFETY),
            replace(
                projection,
                emlis_value_policy_ref="policy:other-value@policy.v1",
            ),
            replace(
                projection,
                interpretation_candidates=tuple(
                    reversed(projection.interpretation_candidates)
                ),
            ),
        ):
            self.assertNotEqual(
                recompute_stage1_identity(projection),
                recompute_stage1_identity(tampered),
            )
        unit = _stage1_sentence_unit_fixture(projection)
        self.assertNotEqual(
            recompute_stage1_identity(unit),
            recompute_stage1_identity(replace(unit, text="見えました")),
        )

    def test_local_ref_dag_rejects_missing_forward_self_cycle_foreign_and_non_string(
        self,
    ) -> None:
        validate_stage1_local_ref_dag(
            ("a", "b", "c"), {"a": (), "b": ("a",), "c": ("b",)}
        )
        cases = (
            (("a", "b"), {"a": (), "b": ("missing",)}, "missing"),
            (("a", "b"), {"a": ("b",), "b": ()}, "forward"),
            (("a",), {"a": ("a",)}, "self"),
            (("a", "b"), {"a": ("b",), "b": ("a",)}, "cycle"),
            (
                ("a", "b"),
                {"a": (), "b": ("candidate:a@projection.v1",)},
                "foreign",
            ),
            (("a", "b"), {"a": (), "b": (1,)}, "identity_invalid"),
        )
        for ids, dependencies, code in cases:
            with self.subTest(code=code):
                with self.assertRaisesRegex(CMEEStage1ContractError, code):
                    validate_stage1_local_ref_dag(ids, dependencies)

    def test_external_refs_are_version_qualified_and_namespace_bound(self) -> None:
        validate_version_qualified_ref(
            "policy:emlis-value@policy.v1", expected_types=("policy",)
        )
        for value, code in (
            ("bare-local-id", "not_version_qualified"),
            ("policy:missing-version", "not_version_qualified"),
            ("node:value@graph.v1", "kind_invalid"),
        ):
            with self.subTest(value=value):
                with self.assertRaisesRegex(CMEEStage1ContractError, code):
                    validate_version_qualified_ref(
                        value, expected_types=("policy",)
                    )

    def test_projection_validates_depth_order_parent_and_single_plan_owner(self) -> None:
        projection = _stage1_projection_fixture()
        grounded_graph = _stage1_grounded_graph_fixture()
        parent = _stage1_parent_plan_fixture(projection)
        validate_stage1_projection(
            projection, grounded_graph=grounded_graph, parent_plan=parent
        )
        self.assertNotIn("core_projection_ref", {row.name for row in fields(ExperiencePlan)})
        for field_name, value in (
            ("source_envelope_id", "foreign-source"),
            ("source_version", "foreign-source.v9"),
            ("obligation_version", "foreign-obligation.v9"),
            ("owner_universe_digest", "foreign-digest"),
        ):
            with self.subTest(parent_lineage_field=field_name):
                with self.assertRaisesRegex(
                    CMEEStage1ContractError, "parent_plan_lineage_mismatch"
                ):
                    validate_stage1_projection(
                        projection,
                        grounded_graph=grounded_graph,
                        parent_plan=replace(parent, **{field_name: value}),
                    )

        invalid_rows = (
            (
                replace(
                    projection,
                    grounded_graph_ref="graph:grounded-1@graph.v1",
                ),
                "kind_invalid",
            ),
            (
                replace(
                    projection,
                    observation_depth_class=ObservationDepthClass.LAYERED,
                ),
                "observation_depth_mismatch",
            ),
            (
                replace(projection, subjective_depth_class="FOCUSED"),
                "subjective_depth_class_invalid",
            ),
            (
                replace(projection, temperature_class="STANDARD"),
                "temperature_class_invalid",
            ),
            (
                replace(projection, ordered_observation_refs=("foreign",)),
                "observation_order_not_exact_cover",
            ),
            (
                replace(projection, retained_reception_act_ids="X"),
                "array_not_tuple",
            ),
        )
        for tampered, code in invalid_rows:
            with self.subTest(code=code):
                with self.assertRaisesRegex(CMEEStage1ContractError, code):
                    validate_stage1_projection(
                        tampered, grounded_graph=grounded_graph, parent_plan=parent
                    )

    def test_subjective_refs_reject_policy_promotion_after_coordinated_rehash(
        self,
    ) -> None:
        projection = _stage1_projection_fixture()
        grounded_graph = _stage1_grounded_graph_fixture()
        parent_plan = _stage1_parent_plan_fixture(projection)
        claim = projection.subjective_claims[0]
        forged_claim = _identified(
            replace(
                claim,
                subjective_claim_id="",
                asserted_subjective_proposition=replace(
                    claim.asserted_subjective_proposition,
                    response_object_refs=("policy:evil@policy.v1",),
                ),
            ),
            "subjective_claim_id",
        )
        forged_projection = _identified(
            replace(
                projection,
                projection_id="",
                subjective_claims=(forged_claim,),
                ordered_subjective_refs=(forged_claim.subjective_claim_id,),
            ),
            "projection_id",
        )
        with self.assertRaisesRegex(CMEEStage1ContractError, "kind_invalid"):
            validate_stage1_projection(
                forged_projection,
                grounded_graph=grounded_graph,
                parent_plan=parent_plan,
            )

    def test_projection_resolves_semantic_refs_against_the_frozen_graph(self) -> None:
        projection = _stage1_projection_fixture()
        grounded_graph = _stage1_grounded_graph_fixture()
        parent_plan = _stage1_parent_plan_fixture(projection)
        meaning_field = projection.meaning_field
        forged_entry = replace(
            meaning_field.entries[0],
            semantic_refs=(
                f"node:foreign@{CMEE_GROUNDED_GRAPH_SCHEMA_VERSION}",
            ),
        )
        forged_field = _identified(
            replace(
                meaning_field,
                meaning_field_id="",
                entries=(forged_entry, *meaning_field.entries[1:]),
            ),
            "meaning_field_id",
        )
        forged_projection = _identified(
            replace(
                projection,
                projection_id="",
                meaning_field=forged_field,
            ),
            "projection_id",
        )
        with self.assertRaisesRegex(CMEEStage1ContractError, "semantic_ref_missing"):
            validate_stage1_projection(
                forged_projection,
                grounded_graph=grounded_graph,
                parent_plan=parent_plan,
            )

    def test_projection_rejects_coordinated_relation_endpoint_kind_forgery(
        self,
    ) -> None:
        projection = _stage1_projection_fixture()
        grounded_graph = _stage1_grounded_graph_fixture()
        parent_plan = _stage1_parent_plan_fixture(projection)
        state_ref = f"node:state-1@{CMEE_GROUNDED_GRAPH_SCHEMA_VERSION}"
        context_ref = f"node:context-1@{CMEE_GROUNDED_GRAPH_SCHEMA_VERSION}"
        edge = MeaningEdge(
            edge_id="forged-wish-constraint",
            owner_id="owner-context-1",
            relation="wish_and_constraint",
            source_node_id="state-1",
            target_node_id="context-1",
            grounding_kind="user_stated_relation",
            epistemic_state=EpistemicState.SOURCE_EXPLICIT,
            evidence_ids=("memo-1",),
        )
        forged_graph = replace(grounded_graph, edges=(edge,))
        first, second = projection.interpretation_candidates
        forged_second = _identified(
            replace(
                second,
                candidate_id="",
                candidate_kind=InterpretationKind.DIRECTION_UNDER_BURDEN,
                semantic_operator=SemanticOperator.SYNTHESIZE_RELATION,
                argument_bindings=(
                    ArgumentBinding(ArgumentRole.LEFT, state_ref),
                    ArgumentBinding(ArgumentRole.RIGHT, context_ref),
                ),
                relation_operator=RelationOperator.COEXISTS_WITH,
                relation_basis_refs=(
                    f"edge:{edge.edge_id}@{CMEE_GROUNDED_GRAPH_SCHEMA_VERSION}",
                ),
                derivation_rule_id=(
                    "cocolon.cmee.v1a.stage1.relation."
                    "wish_and_constraint.v1"
                ),
                semantic_refs=(state_ref, context_ref),
            ),
            "candidate_id",
        )
        forged_relation_entry = MeaningFieldEntry(
            slot=MeaningFieldSlot.COEXISTENCE,
            interpretation_candidate_refs=(forged_second.candidate_id,),
            semantic_refs=(state_ref, context_ref),
            evidence_refs=("evidence:memo-1@source.v1",),
        )
        forged_field = _identified(
            replace(
                projection.meaning_field,
                meaning_field_id="",
                entries=(
                    projection.meaning_field.entries[0],
                    forged_relation_entry,
                ),
            ),
            "meaning_field_id",
        )
        forged_projection = _identified(
            replace(
                projection,
                projection_id="",
                interpretation_candidates=(first, forged_second),
                meaning_field=forged_field,
            ),
            "projection_id",
        )
        with self.assertRaisesRegex(
            CMEEStage1ContractError,
            "stage1_candidate_relation_binding_invalid",
        ):
            validate_stage1_projection(
                forged_projection,
                grounded_graph=forged_graph,
                parent_plan=parent_plan,
            )

    def test_projection_accepts_canonical_capped_relation_endpoint(
        self,
    ) -> None:
        source, grounded_plan, grounded_graph, parent_plan = _stage2_inputs(
            _request(
                record_id="stage2-capped-relation-endpoint",
                memo="困っている。前は動いた。今は不安が残っている。",
            )
        )
        candidates, meaning_field, contributions, ordered_refs, depth = (
            build_layer1_semantics(
                source=source,
                grounded_graph=grounded_graph,
                parent_plan=parent_plan,
                grounded_plan=grounded_plan,
            )
        )
        residue = next(
            row
            for row in candidates
            if row.candidate_kind is InterpretationKind.RESIDUE_AFTER_EVENT
        )
        after_ref = residue.argument_bindings[1].semantic_ref
        self.assertFalse(
            any(
                row.relation_operator is RelationOperator.NO_RELATION_CLAIM
                and after_ref in row.semantic_refs
                for row in candidates
            )
        )

        base = _stage1_projection_fixture()
        base_claim = base.subjective_claims[0]
        proposition = replace(
            base_claim.asserted_subjective_proposition,
            target_contribution_refs=(contributions[0].contribution_id,),
            response_object_refs=(contributions[0].contribution_id,),
        )
        claim = _identified(
            replace(
                base_claim,
                subjective_claim_id="",
                parent_duty_ref=parent_plan.reception_duty_id,
                asserted_subjective_proposition=proposition,
                basis_observation_contribution_refs=(
                    contributions[0].contribution_id,
                ),
                basis_semantic_refs=contributions[0].semantic_refs,
                source_reception_act_refs=(
                    parent_plan.allowed_reception_act_ids
                ),
            ),
            "subjective_claim_id",
        )
        projection = _identified(
            replace(
                base,
                projection_id="",
                grounded_graph_ref=meaning_field.grounded_graph_ref,
                parent_observation_duty_ref=parent_plan.observation_duty_id,
                parent_reception_duty_ref=parent_plan.reception_duty_id,
                interpretation_candidates=candidates,
                meaning_field=meaning_field,
                observation_contributions=contributions,
                subjective_claims=(claim,),
                ordered_observation_refs=ordered_refs,
                ordered_subjective_refs=(claim.subjective_claim_id,),
                retained_reception_act_ids=(
                    parent_plan.allowed_reception_act_ids
                ),
                observation_depth_class=depth,
            ),
            "projection_id",
        )
        validate_stage1_projection(
            projection,
            grounded_graph=grounded_graph,
            parent_plan=parent_plan,
        )

    def test_sentence_unit_binds_projection_utf8_text_and_surface_digest(self) -> None:
        projection = _stage1_projection_fixture()
        grounded_graph = _stage1_grounded_graph_fixture()
        parent_plan = _stage1_parent_plan_fixture(projection)
        unit = _stage1_sentence_unit_fixture(projection)
        validate_stage1_sentence_unit(
            unit,
            projection,
            grounded_graph=grounded_graph,
            parent_plan=parent_plan,
        )

        for tampered, code in (
            (replace(unit, projection_ref="projection-foreign"), "foreign_projection"),
            (replace(unit, text="改竄後"), "surface_digest_invalid"),
            (
                replace(
                    unit,
                    realized_semantic_bindings=(
                        replace(
                            unit.realized_semantic_bindings[0],
                            semantic_ref="policy:wrong@policy.v1",
                        ),
                    ),
                ),
                "kind_invalid",
            ),
            (
                replace(unit, clause_frames=("not-a-frame",)),
                "clause_frame_type_invalid",
            ),
            (
                replace(
                    unit,
                    discourse_link_to_prior_sentence="unit:foreign@unit.v1",
                ),
                "prior_ref_invalid",
            ),
            (
                replace(
                    unit,
                    realized_semantic_bindings=(
                        replace(
                            unit.realized_semantic_bindings[0],
                            semantic_ref=(
                                f"node:other-1@{CMEE_GROUNDED_GRAPH_SCHEMA_VERSION}"
                            ),
                        ),
                    ),
                ),
                "semantic_ref_unreachable",
            ),
            (
                replace(unit, layer="LAYER_2"),
                "basis_anchor_invalid",
            ),
        ):
            with self.subTest(code=code):
                with self.assertRaisesRegex(CMEEStage1ContractError, code):
                    validate_stage1_sentence_unit(
                        tampered,
                        projection,
                        grounded_graph=grounded_graph,
                        parent_plan=parent_plan,
                    )

    def test_trace_spine_enforces_role_owner_reachability_and_exact_coverage(self) -> None:
        projection = _stage1_projection_fixture()
        grounded_graph = _stage1_grounded_graph_fixture()
        parent_plan = _stage1_parent_plan_fixture(projection)
        candidate = projection.interpretation_candidates[0]
        contribution = projection.observation_contributions[0]
        claim = projection.subjective_claims[0]
        observation = VisibleUnitTrace(
            visible_unit_id="cmee:observation:1",
            source_sentence_id="source:1",
            source_envelope_id="source-1",
            source_version="source.v1",
            obligation_version="obligation.v1",
            owner_universe_digest="digest",
            artifact_common_guard_proof_ref="proof-1",
            role="OBSERVATION",
            operation="SEMANTIC_REALIZATION",
            text_sha256="0" * 64,
            duty_id=projection.parent_observation_duty_ref,
            meaning_node_ids=("state-1",),
            meaning_edge_ids=(),
            evidence_ids=("memo-1",),
            emlis_stage1_extension=EmlisStage1PositiveTraceExtension(
                schema_version=CMEE_STAGE1_TRACE_EXTENSION_SCHEMA_VERSION,
                claim_domain=EmlisTraceClaimDomain.INTERPRETIVE_OBSERVATION,
                owner_ref=CMEE_STAGE1_EMLIS_OWNER_REF,
                contribution_refs=(contribution.contribution_id,),
                basis_trace_refs=(),
                interpretation_candidate_refs=(candidate.candidate_id,),
                subjective_claim_ref=None,
                basis_observation_contribution_refs=(),
                value_principle_refs=(),
                speaker_owner=None,
                user_fact_effect=0,
                composition_variant_id="primary.v1",
            ),
        )
        unknown = VisibleUnitTrace(
            visible_unit_id="cmee:unknown:1",
            source_sentence_id="source:2",
            source_envelope_id="source-1",
            source_version="source.v1",
            obligation_version="obligation.v1",
            owner_universe_digest="digest",
            artifact_common_guard_proof_ref="proof-1",
            role="UNKNOWN",
            operation="UNKNOWN_DISCLOSURE",
            text_sha256="1" * 64,
            duty_id="unknown-duty-1",
            meaning_node_ids=(),
            meaning_edge_ids=(),
            evidence_ids=("evidence-1",),
            constrained_by_owner_ids=("owner-1",),
        )
        reception = VisibleUnitTrace(
            visible_unit_id="cmee:reception:1",
            source_sentence_id="source:3",
            source_envelope_id="source-1",
            source_version="source.v1",
            obligation_version="obligation.v1",
            owner_universe_digest="digest",
            artifact_common_guard_proof_ref="proof-1",
            role="RECEPTION",
            operation="RECEPTION",
            text_sha256="2" * 64,
            duty_id=projection.parent_reception_duty_ref,
            meaning_node_ids=("state-1", "context-1"),
            meaning_edge_ids=(),
            evidence_ids=("memo-1",),
            emlis_stage1_extension=EmlisStage1PositiveTraceExtension(
                schema_version=CMEE_STAGE1_TRACE_EXTENSION_SCHEMA_VERSION,
                claim_domain=EmlisTraceClaimDomain.SUBJECTIVE_RESPONSE,
                owner_ref=CMEE_STAGE1_EMLIS_OWNER_REF,
                contribution_refs=(),
                basis_trace_refs=(observation.visible_unit_id,),
                interpretation_candidate_refs=(),
                subjective_claim_ref=claim.subjective_claim_id,
                basis_observation_contribution_refs=(contribution.contribution_id,),
                value_principle_refs=claim.value_principle_refs,
                speaker_owner="EMLIS",
                user_fact_effect=0,
                composition_variant_id="primary.v1",
            ),
        )
        rows = (observation, unknown, reception)
        validate_stage1_trace_spine(
            rows,
            projection,
            grounded_graph=grounded_graph,
            parent_plan=parent_plan,
        )

        invalid_rows = (
            (
                (
                    replace(
                        observation,
                        emlis_stage1_extension=replace(
                            observation.emlis_stage1_extension,
                            owner_ref="owner:other@core.v1",
                        ),
                    ),
                    unknown,
                    reception,
                ),
                "owner_invalid",
            ),
            (
                (
                    observation,
                    unknown,
                    replace(
                        reception,
                        emlis_stage1_extension=replace(
                            reception.emlis_stage1_extension,
                            value_principle_refs=("policy:forged@policy.v1",),
                        ),
                    ),
                ),
                "claim_mismatch",
            ),
            (
                (
                    replace(observation, meaning_node_ids=("foreign-node",)),
                    unknown,
                    reception,
                ),
                "lineage_unreachable",
            ),
            (
                (
                    replace(observation, duty_id="other-duty"),
                    unknown,
                    reception,
                ),
                "duty_mismatch",
            ),
            (
                (
                    replace(observation, source_version="foreign-source.v9"),
                    unknown,
                    reception,
                ),
                "lineage_metadata_mismatch",
            ),
            (
                (
                    replace(
                        observation,
                        meaning_node_ids=(),
                        meaning_edge_ids=("state-1",),
                    ),
                    unknown,
                    reception,
                ),
                "lineage_unreachable",
            ),
            (
                (
                    replace(
                        observation,
                        emlis_stage1_extension=replace(
                            observation.emlis_stage1_extension,
                            composition_variant_id=1,
                        ),
                    ),
                    unknown,
                    reception,
                ),
                "variant_missing",
            ),
            ((reception, unknown, observation), "ref_forward"),
            ((observation, unknown), "reception_trace_coverage_invalid"),
            (
                (
                    observation,
                    unknown,
                    reception,
                    replace(reception, visible_unit_id="cmee:reception:2"),
                ),
                "reception_trace_coverage_invalid",
            ),
        )
        for tampered, code in invalid_rows:
            with self.subTest(code=code):
                with self.assertRaisesRegex(CMEEStage1ContractError, code):
                    validate_stage1_trace_spine(
                        tampered,
                        projection,
                        grounded_graph=grounded_graph,
                        parent_plan=parent_plan,
                    )

    def test_stage2_interpretation_matrix_is_canonical_exact13(self) -> None:
        expected = (
            (InterpretationKind.DIRECT_STATE, SemanticOperator.PRESENT_STATE, RelationOperator.NO_RELATION_CLAIM, (ArgumentRole.PRIMARY,)),
            (InterpretationKind.DIRECT_STATE, SemanticOperator.PRESENT_BURDEN, RelationOperator.NO_RELATION_CLAIM, (ArgumentRole.PRIMARY,)),
            (InterpretationKind.DIRECT_STATE, SemanticOperator.PRESENT_CHANGE, RelationOperator.NO_RELATION_CLAIM, (ArgumentRole.PRIMARY,)),
            (InterpretationKind.DIRECT_STATE, SemanticOperator.PRESENT_ACTUAL_OUTPUT, RelationOperator.NO_RELATION_CLAIM, (ArgumentRole.PRIMARY,)),
            (InterpretationKind.DIRECT_DIRECTION, SemanticOperator.PRESENT_DIRECTION, RelationOperator.NO_RELATION_CLAIM, (ArgumentRole.PRIMARY,)),
            (InterpretationKind.COEXISTENCE, SemanticOperator.SYNTHESIZE_RELATION, RelationOperator.COEXISTS_WITH, (ArgumentRole.LEFT, ArgumentRole.RIGHT)),
            (InterpretationKind.TENSION, SemanticOperator.SYNTHESIZE_RELATION, RelationOperator.TENSION_WITH, (ArgumentRole.LEFT, ArgumentRole.RIGHT)),
            (InterpretationKind.DIRECTION_UNDER_BURDEN, SemanticOperator.SYNTHESIZE_RELATION, RelationOperator.COEXISTS_WITH, (ArgumentRole.LEFT, ArgumentRole.RIGHT)),
            (InterpretationKind.DIRECTION_UNDER_BURDEN, SemanticOperator.SYNTHESIZE_RELATION, RelationOperator.TENSION_WITH, (ArgumentRole.LEFT, ArgumentRole.RIGHT)),
            (InterpretationKind.ACTION_THEN_CHANGE_ONCE, SemanticOperator.PRESENT_CHANGE, RelationOperator.ACTION_PRECEDES_CHANGE, (ArgumentRole.ACTION, ArgumentRole.CHANGE)),
            (InterpretationKind.RESIDUE_AFTER_EVENT, SemanticOperator.PRESENT_RESIDUE, RelationOperator.TEMPORALLY_PRECEDES, (ArgumentRole.BEFORE, ArgumentRole.AFTER)),
            (InterpretationKind.SOURCE_STATED_CAUSE, SemanticOperator.SYNTHESIZE_RELATION, RelationOperator.SOURCE_EXPLICIT_CAUSE, (ArgumentRole.CAUSE, ArgumentRole.EFFECT)),
            (InterpretationKind.UNFINISHED, SemanticOperator.PRESENT_UNFINISHED, RelationOperator.NO_RELATION_CLAIM, (ArgumentRole.PRIMARY,)),
        )
        self.assertEqual(INTERPRETATION_MATRIX_EXACT13, expected)
        self.assertEqual(len(INTERPRETATION_MATRIX_EXACT13), 13)
        self.assertEqual(
            {row[0] for row in INTERPRETATION_MATRIX_EXACT13},
            set(InterpretationKind),
        )

    def test_stage2_exact8_is_deterministic_reachable_and_layered(self) -> None:
        for case_id, memo, category, emotion, strength in EXACT8:
            with self.subTest(case_id=case_id):
                source, grounded_plan, graph, parent_plan = _stage2_inputs(
                    _request(
                        record_id=f"stage2-{case_id.lower()}",
                        memo=memo,
                        category=category,
                        emotion=emotion,
                        strength=strength,
                    )
                )
                first = build_layer1_semantics(
                    source=source,
                    grounded_graph=graph,
                    parent_plan=parent_plan,
                    grounded_plan=grounded_plan,
                )
                second = build_layer1_semantics(
                    source=source,
                    grounded_graph=graph,
                    parent_plan=parent_plan,
                    grounded_plan=grounded_plan,
                )
                self.assertEqual(first, second)
                candidates, meaning_field, contributions, ordered_refs, depth = first
                self.assertLessEqual(
                    len(candidates), INTERPRETATION_CANDIDATE_POOL_CAP
                )
                self.assertTrue(candidates)
                self.assertTrue(
                    all(
                        count <= INTERPRETATION_CANDIDATE_KIND_CAP
                        for count in Counter(
                            row.candidate_kind for row in candidates
                        ).values()
                    )
                )
                node_ids = {row.node_id for row in graph.nodes}
                edge_ids = {row.edge_id for row in graph.edges}
                evidence_ids = {row.evidence_id for row in source.evidence_refs}
                for candidate in candidates:
                    validate_stage1_identity(candidate)
                    for ref in candidate.semantic_refs:
                        self.assertIn(
                            ref.split(":", 1)[1].rsplit("@", 1)[0], node_ids
                        )
                    for ref in candidate.relation_basis_refs:
                        self.assertIn(
                            ref.split(":", 1)[1].rsplit("@", 1)[0], edge_ids
                        )
                    for ref in candidate.evidence_refs:
                        self.assertIn(
                            ref.split(":", 1)[1].rsplit("@", 1)[0],
                            evidence_ids,
                        )
                    roles = tuple(row.role for row in candidate.argument_bindings)
                    self.assertTrue(
                        any(
                            row[:3]
                            == (
                                candidate.candidate_kind,
                                candidate.semantic_operator,
                                candidate.relation_operator,
                            )
                            and roles
                            in {
                                row[3],
                                (*row[3], ArgumentRole.EXPERIENCER),
                            }
                            for row in INTERPRETATION_MATRIX_EXACT13
                        )
                    )
                entry_refs = tuple(
                    ref
                    for entry in meaning_field.entries
                    for ref in entry.interpretation_candidate_refs
                )
                self.assertEqual(len(entry_refs), len(set(entry_refs)))
                self.assertEqual(set(entry_refs), {row.candidate_id for row in candidates})
                self.assertIn(
                    meaning_field.center_candidate_ref,
                    {row.candidate_id for row in candidates},
                )
                self.assertTrue(
                    set(meaning_field.required_candidate_refs).issubset(
                        set(entry_refs)
                    )
                )
                self.assertEqual(len(contributions), 2)
                self.assertEqual(
                    ordered_refs,
                    tuple(row.contribution_id for row in contributions),
                )
                self.assertEqual(
                    len({row.canonical_semantic_key for row in contributions}),
                    len(contributions),
                )
                self.assertIs(depth, ObservationDepthClass.LAYERED)

    def test_stage2_source_evidence_and_unknown_boundaries_fail_closed(self) -> None:
        case_id, memo, category, emotion, strength = EXACT8[0]
        source, grounded_plan, graph, parent_plan = _stage2_inputs(
            _request(
                record_id=f"stage2-reach-{case_id.lower()}",
                memo=memo,
                category=category,
                emotion=emotion,
                strength=strength,
            )
        )
        candidates = build_interpretation_candidate_pool(
            graph,
            parent_plan,
            source=source,
            grounded_plan=grounded_plan,
        )
        self.assertTrue(candidates)

        admitted = next(
            row
            for row in graph.nodes
            if row.epistemic_state is EpistemicState.SOURCE_EXPLICIT
            and row.grounding_kind in {"explicit", "user_stated_relation"}
        )
        invalid_nodes = (
            replace(admitted, evidence_ids=()),
            replace(admitted, epistemic_state=EpistemicState.UNKNOWN),
        )
        for node in invalid_nodes:
            with self.subTest(node_epistemic=node.epistemic_state.value):
                with self.assertRaisesRegex(
                    CMEEStage1ContractError, "stage1_grounded_graph_noncanonical"
                ):
                    build_interpretation_candidate_pool(
                        replace(
                            graph,
                            nodes=tuple(
                                node if row.node_id == admitted.node_id else row
                                for row in graph.nodes
                            ),
                        ),
                        parent_plan,
                        source=source,
                        grounded_plan=grounded_plan,
                    )

        rename_target = next(
            row
            for row in graph.nodes
            if row.epistemic_state is EpistemicState.SOURCE_EXPLICIT
            and row.grounding_kind in {"explicit", "user_stated_relation"}
            and row.owner_id not in set(parent_plan.visible_owner_ids)
        )
        renamed_node = replace(rename_target, node_id="attacker-node-id")
        renamed_graph = replace(
            graph,
            nodes=tuple(
                renamed_node if row.node_id == rename_target.node_id else row
                for row in graph.nodes
            ),
            edges=tuple(
                replace(
                    row,
                    source_node_id=(
                        renamed_node.node_id
                        if row.source_node_id == rename_target.node_id
                        else row.source_node_id
                    ),
                    target_node_id=(
                        renamed_node.node_id
                        if row.target_node_id == rename_target.node_id
                        else row.target_node_id
                    ),
                )
                for row in graph.edges
            ),
        )
        with self.assertRaisesRegex(
            CMEEStage1ContractError, "stage1_grounded_graph_noncanonical"
        ):
            build_interpretation_candidate_pool(
                renamed_graph,
                parent_plan,
                source=source,
                grounded_plan=grounded_plan,
            )

        with self.assertRaisesRegex(
            CMEEStage1ContractError, "stage1_admitted_text_source_required"
        ):
            build_interpretation_candidate_pool(
                graph,
                parent_plan,
                source=object(),
                grounded_plan=grounded_plan,
            )
        with self.assertRaisesRegex(
            CMEEStage1ContractError,
            "stage1_grounded_observation_plan_required",
        ):
            build_interpretation_candidate_pool(
                graph,
                parent_plan,
                source=source,
                grounded_plan=object(),
            )

        source_a = freeze_text_source(
            _request(record_id="stage2-coordinated-source", memo="疲れた。")
        )
        source_b = freeze_text_source(
            _request(
                record_id="stage2-coordinated-source",
                memo="不安はあるけれど進みたい。",
            )
        )
        forged_source = replace(
            source_a,
            normalized_current_input=source_b.normalized_current_input,
            evidence_spans=source_b.evidence_spans,
        )
        forged_grounded_plan = build_grounded_observation_plan(
            forged_source.normalized_current_input,
            evidence_spans=forged_source.evidence_spans,
        )
        forged_required_nuclei, forged_required_relations, forged_targets = (
            _planned_visible_source_ids(forged_grounded_plan)
        )
        forged_graph = _build_graph(
            forged_source,
            forged_grounded_plan,
            _ordered((*forged_required_nuclei, *forged_targets)),
            forged_required_relations,
        )
        forged_parent = _build_experience_plan(
            forged_source,
            forged_graph,
            forged_grounded_plan,
            forged_required_nuclei,
            forged_required_relations,
            forged_targets,
        )
        with self.assertRaisesRegex(
            CMEEStage1ContractError, "stage1_source_evidence_unreachable"
        ):
            build_layer1_semantics(
                source=forged_source,
                grounded_graph=forged_graph,
                parent_plan=forged_parent,
                grounded_plan=forged_grounded_plan,
            )

        relation_case = EXACT8[6]
        relation_source, relation_grounded_plan, relation_graph, relation_plan = (
            _stage2_inputs(
                _request(
                    record_id="stage2-relation-endpoint",
                    memo=relation_case[1],
                    category=relation_case[2],
                    emotion=relation_case[3],
                    strength=relation_case[4],
                )
            )
        )
        relation_edge = next(
            row
            for row in relation_graph.edges
            if row.epistemic_state is EpistemicState.SOURCE_EXPLICIT
        )
        with self.assertRaisesRegex(
            CMEEStage1ContractError, "stage1_relation_endpoint_missing"
        ):
            build_interpretation_candidate_pool(
                replace(
                    relation_graph,
                    edges=tuple(
                        replace(row, target_node_id="missing-node")
                        if row.edge_id == relation_edge.edge_id
                        else row
                        for row in relation_graph.edges
                    ),
                ),
                relation_plan,
                source=relation_source,
                grounded_plan=relation_grounded_plan,
            )

        bounded_source, bounded_grounded_plan, bounded_graph, bounded_plan = (
            _stage2_inputs(
                _request(
                    record_id="stage2-material-unknown",
                    memo="疲れた。",
                )
            )
        )
        excluded_node_ids = {
            row.node_id
            for row in bounded_graph.nodes
            if row.epistemic_state is EpistemicState.UNKNOWN
            or row.grounding_kind == "source_explicit_not_realized"
        }
        self.assertTrue(excluded_node_ids)
        unknown_owner = bounded_plan.visible_unknown_owner_ids[0]
        disposition = next(
            row
            for row in bounded_graph.owner_dispositions
            if row.meaning_owner_id == unknown_owner
        )
        material_unknown_refs = stage1_response_module._material_unknown_refs(
            bounded_graph,
            bounded_plan,
            bounded_source,
        )
        self.assertEqual(len(material_unknown_refs), 1)
        self.assertIn(
            str(disposition.target_unknown_ref),
            material_unknown_refs[0],
        )

        forged_unknown_plan = replace(
            bounded_plan,
            visible_unknown_owner_ids=("bogus-owner",),
            unresolved_owner_ids=(*bounded_plan.unresolved_owner_ids, "bogus-owner"),
        )
        with self.assertRaisesRegex(
            CMEEStage1ContractError, "stage1_material_unknown_unreachable"
        ):
            stage1_response_module._material_unknown_refs(
                bounded_graph,
                forged_unknown_plan,
                bounded_source,
            )

    def test_stage2_relations_preserve_symmetric_order_and_direction(self) -> None:
        case_id, memo, category, emotion, strength = EXACT8[6]
        source, grounded_plan, contrast_graph, contrast_plan = _stage2_inputs(
            _request(
                record_id=f"stage2-relations-{case_id.lower()}",
                memo=memo,
                category=category,
                emotion=emotion,
                strength=strength,
            )
        )
        candidates = build_interpretation_candidate_pool(
            contrast_graph,
            contrast_plan,
            source=source,
            grounded_plan=grounded_plan,
        )
        contrast = next(
            row
            for row in candidates
            if row.candidate_kind is InterpretationKind.TENSION
        )
        self.assertEqual(
            tuple(row.semantic_ref for row in contrast.argument_bindings),
            tuple(sorted(contrast.semantic_refs)),
        )
        direction = next(
            row
            for row in candidates
            if row.candidate_kind is InterpretationKind.DIRECTION_UNDER_BURDEN
        )
        direction_edge = next(
            row for row in contrast_graph.edges if row.relation == "wish_and_constraint"
        )
        self.assertEqual(
            tuple(row.role for row in direction.argument_bindings),
            (ArgumentRole.LEFT, ArgumentRole.RIGHT),
        )
        self.assertEqual(
            tuple(
                row.semantic_ref.split(":", 1)[1].rsplit("@", 1)[0]
                for row in direction.argument_bindings
            ),
            (
                direction_edge.source_node_id,
                direction_edge.target_node_id,
            ),
        )
        reversed_graph = replace(
            contrast_graph,
            edges=tuple(
                replace(
                    row,
                    source_node_id=row.target_node_id,
                    target_node_id=row.source_node_id,
                )
                if row.edge_id == direction_edge.edge_id
                else row
                for row in contrast_graph.edges
            ),
        )
        with self.assertRaisesRegex(
            CMEEStage1ContractError, "stage1_grounded_graph_noncanonical"
        ):
            build_interpretation_candidate_pool(
                reversed_graph,
                contrast_plan,
                source=source,
                grounded_plan=grounded_plan,
            )

        _candidates, _field, contributions, _refs, depth = build_layer1_semantics(
            source=source,
            grounded_graph=contrast_graph,
            parent_plan=contrast_plan,
            grounded_plan=grounded_plan,
        )
        self.assertEqual(len(contributions), 2)
        self.assertIs(depth, ObservationDepthClass.LAYERED)

    def test_stage2_only_source_explicit_cause_can_be_promoted(self) -> None:
        source, grounded_plan, graph, parent_plan = _stage2_inputs(
            _request(
                record_id="stage2-source-stated-cause",
                memo="仕事が続いた。そのため、疲れている。",
            )
        )
        cause = next(
            row
            for row in build_interpretation_candidate_pool(
                graph,
                parent_plan,
                source=source,
                grounded_plan=grounded_plan,
            )
            if row.candidate_kind is InterpretationKind.SOURCE_STATED_CAUSE
        )
        self.assertIs(
            cause.relation_operator, RelationOperator.SOURCE_EXPLICIT_CAUSE
        )
        self.assertEqual(
            tuple(row.role for row in cause.argument_bindings),
            (ArgumentRole.CAUSE, ArgumentRole.EFFECT),
        )
        result_source, result_grounded_plan, result_graph, result_parent_plan = (
            _stage2_inputs(
                _request(
                    record_id="stage2-source-stated-result",
                    memo="雨が降った。だから、外出をやめた。",
                )
            )
        )
        with self.assertRaisesRegex(
            CMEEStage1ContractError, "stage1_unsupported_cause"
        ):
            build_interpretation_candidate_pool(
                result_graph,
                result_parent_plan,
                source=result_source,
                grounded_plan=result_grounded_plan,
            )

    def test_stage2_pool_bounds_suppress_optional_tail_and_reject_required_overflow(
        self,
    ) -> None:
        for case_id, memo, category, emotion, strength in EXACT8:
            with self.subTest(case_id=case_id):
                source, grounded_plan, graph, parent_plan = _stage2_inputs(
                    _request(
                        record_id=f"stage2-bounds-{case_id.lower()}",
                        memo=memo,
                        category=category,
                        emotion=emotion,
                        strength=strength,
                    )
                )
                first = build_interpretation_candidate_pool(
                    graph,
                    parent_plan,
                    source=source,
                    grounded_plan=grounded_plan,
                )
                second = build_interpretation_candidate_pool(
                    graph,
                    parent_plan,
                    source=source,
                    grounded_plan=grounded_plan,
                )
                self.assertEqual(first, second)
                self.assertLessEqual(
                    len(first), INTERPRETATION_CANDIDATE_POOL_CAP
                )
                self.assertTrue(
                    all(
                        count <= INTERPRETATION_CANDIDATE_KIND_CAP
                        for count in Counter(
                            row.candidate_kind for row in first
                        ).values()
                    )
                )

        source, grounded_plan, short_graph, short_parent = _stage2_inputs(
            _request(record_id="stage2-required-overflow", memo="疲れた。")
        )
        with self.assertRaisesRegex(
            CMEEStage1ContractError, "stage1_required_candidate_overflow"
        ):
            build_layer1_semantics(
                source=source,
                grounded_graph=short_graph,
                parent_plan=short_parent,
                grounded_plan=grounded_plan,
            )

    def test_stage2_meaning_field_exact_cover_and_tamper_rejection(self) -> None:
        case_id, memo, category, emotion, strength = EXACT8[6]
        source, grounded_plan, graph, parent_plan = _stage2_inputs(
            _request(
                record_id=f"stage2-field-{case_id.lower()}",
                memo=memo,
                category=category,
                emotion=emotion,
                strength=strength,
            )
        )
        candidates = build_interpretation_candidate_pool(
            graph,
            parent_plan,
            source=source,
            grounded_plan=grounded_plan,
        )
        meaning_field = build_emlis_meaning_field(
            graph,
            parent_plan,
            candidates,
            source=source,
            grounded_plan=grounded_plan,
        )
        validate_emlis_meaning_field(
            meaning_field,
            candidates=candidates,
            grounded_graph=graph,
            parent_plan=parent_plan,
            source=source,
            grounded_plan=grounded_plan,
        )
        entry_refs = tuple(
            ref
            for entry in meaning_field.entries
            for ref in entry.interpretation_candidate_refs
        )
        self.assertEqual(len(entry_refs), len(set(entry_refs)))
        self.assertEqual(set(entry_refs), {row.candidate_id for row in candidates})
        self.assertTrue(
            all(entry_refs.count(ref) == 1 for ref in meaning_field.required_candidate_refs)
        )
        first_entry = meaning_field.entries[0]
        forged_entry = replace(
            first_entry,
            interpretation_candidate_refs=first_entry.interpretation_candidate_refs[1:],
        )
        forged_field = replace(
            meaning_field,
            meaning_field_id="",
            entries=(forged_entry, *meaning_field.entries[1:]),
        )
        forged_field = replace(
            forged_field,
            meaning_field_id=recompute_stage1_identity(forged_field),
        )
        with self.assertRaisesRegex(
            CMEEStage1ContractError,
            "stage1_meaning_field_required_not_exact_cover",
        ):
            validate_emlis_meaning_field(
                forged_field,
                candidates=candidates,
                grounded_graph=graph,
                parent_plan=parent_plan,
                source=source,
                grounded_plan=grounded_plan,
            )

    def test_stage2_layer1_slot_binding_and_semantic_key_are_canonical(self) -> None:
        case_id, memo, category, emotion, strength = EXACT8[7]
        source, grounded_plan, graph, parent_plan = _stage2_inputs(
            _request(
                record_id=f"stage2-layer1-{case_id.lower()}",
                memo=memo,
                category=category,
                emotion=emotion,
                strength=strength,
            )
        )
        candidates, meaning_field, contributions, _ordered_refs, _depth = (
            build_layer1_semantics(
                source=source,
                grounded_graph=graph,
                parent_plan=parent_plan,
                grounded_plan=grounded_plan,
            )
        )
        candidate_by_id = {row.candidate_id: row for row in candidates}
        for contribution in contributions:
            candidate = candidate_by_id[
                contribution.interpretation_candidate_refs[0]
            ]
            self.assertEqual(contribution.semantic_operator, candidate.semantic_operator)
            self.assertEqual(contribution.argument_bindings, candidate.argument_bindings)
            self.assertEqual(contribution.relation_operator, candidate.relation_operator)
            self.assertEqual(contribution.relation_basis_refs, candidate.relation_basis_refs)
            self.assertEqual(contribution.semantic_refs, candidate.semantic_refs)
            self.assertEqual(contribution.evidence_refs, candidate.evidence_refs)
        self.assertTrue(
            any(
                row.semantic_operator is SemanticOperator.PRESENT_CHANGE
                for row in candidates
            )
        )
        validate_layer1_observation_plan(
            contributions,
            candidates=candidates,
            meaning_field=meaning_field,
            grounded_graph=graph,
            parent_plan=parent_plan,
            source=source,
            grounded_plan=grounded_plan,
        )
        forged = replace(
            contributions[0],
            canonical_semantic_key="observation-key-forged",
        )
        with self.assertRaisesRegex(
            CMEEStage1ContractError, "stage1_observation_semantic_key_mismatch"
        ):
            validate_layer1_observation_plan(
                (forged, *contributions[1:]),
                candidates=candidates,
                meaning_field=meaning_field,
                grounded_graph=graph,
                parent_plan=parent_plan,
                source=source,
                grounded_plan=grounded_plan,
            )

    def test_stage2_observation_depth_uses_distinct_contributions_only(self) -> None:
        projection = _stage1_projection_fixture()
        base = projection.observation_contributions[0]
        rows = tuple(
            replace(
                base,
                contribution_id=f"depth-contribution-{index}",
                canonical_semantic_key=f"depth-key-{index}",
            )
            for index in range(1, 7)
        )
        expected = {
            1: ObservationDepthClass.FOCUSED,
            2: ObservationDepthClass.LAYERED,
            3: ObservationDepthClass.LAYERED,
            4: ObservationDepthClass.DENSE,
            5: ObservationDepthClass.DENSE,
        }
        for count, depth in expected.items():
            with self.subTest(count=count):
                self.assertIs(classify_observation_depth(rows[:count]), depth)
        for invalid in ((), rows):
            with self.assertRaisesRegex(
                CMEEStage1ContractError, "stage1_observation_depth_unrealizable"
            ):
                classify_observation_depth(invalid)
        with self.assertRaisesRegex(
            CMEEStage1ContractError, "stage1_duplicate_observation_contribution"
        ):
            classify_observation_depth(
                (rows[0], replace(rows[1], canonical_semantic_key=rows[0].canonical_semantic_key))
            )

    def test_stage2_has_no_case_fixture_or_strength_branch(self) -> None:
        source_code = inspect.getsource(stage1_response_module)
        for forbidden in ("case_id", "expected_text", "EXACT8", "SX-"):
            self.assertNotIn(forbidden, source_code)

        memo = EXACT8[3][1]

        def semantic_shape(record_id: str, strength: str):
            source, grounded_plan, graph, parent_plan = _stage2_inputs(
                _request(
                    record_id=record_id,
                    memo=memo,
                    category=EXACT8[3][2],
                    emotion=EXACT8[3][3],
                    strength=strength,
                )
            )
            candidates, meaning_field, contributions, _refs, depth = (
                build_layer1_semantics(
                    source=source,
                    grounded_graph=graph,
                    parent_plan=parent_plan,
                    grounded_plan=grounded_plan,
                )
            )
            return (
                tuple(
                    (
                        row.candidate_kind,
                        row.semantic_operator,
                        row.relation_operator,
                        tuple(binding.role for binding in row.argument_bindings),
                    )
                    for row in candidates
                ),
                tuple(entry.slot for entry in meaning_field.entries),
                tuple(row.contribution_kind for row in contributions),
                depth,
            )

        baseline = semantic_shape("stage2-generalization-a", "strong")
        self.assertEqual(
            baseline,
            semantic_shape("stage2-generalization-b", "strong"),
        )
        self.assertEqual(
            baseline,
            semantic_shape("stage2-generalization-c", "medium"),
        )


if __name__ == "__main__":
    unittest.main()
