# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json
import unittest
from dataclasses import fields, replace
from unittest.mock import patch

from emlis_ai_current_input_bundle import build_emlis_current_input_bundle
from cocolon_meaning_experience_engine import EngineStatus, GenerationRequest, MeaningExperienceEngine
from cocolon_meaning_experience_engine.contracts import (
    ArgumentBinding,
    ArgumentRole,
    AttachmentAdmission,
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
    ExperiencePlan,
    InterpretationEpistemicState,
    InterpretationKind,
    MeaningFieldEntry,
    MeaningFieldSlot,
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
from cocolon_meaning_experience_engine.source_kernel import (
    SourceAdmissionError,
    _evidence_id,
    _source_envelope_id,
    build_source_owner_universe,
    freeze_text_source,
    normalize_evidence_literal,
)


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


def _identified(value: object, identity_field: str) -> object:
    return replace(value, **{identity_field: recompute_stage1_identity(value)})


def _stage1_projection_fixture() -> EmlisStage1Projection:
    schema = CMEE_STAGE1_RESPONSE_SCHEMA_VERSION
    graph_ref = "grounded:grounded-1@graph.v1"
    observation_duty_ref = "observation-duty-1"
    reception_duty_ref = "reception-duty-1"
    semantic_refs = ("node:state-1@graph.v1", "node:context-1@graph.v1")
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
            derivation_rule_id="direct-state.v1",
            semantic_refs=semantic_refs,
            evidence_refs=evidence_refs,
            basis_candidate_refs=(),
            epistemic_state=(
                InterpretationEpistemicState.PROVISIONAL_INTERPRETATION
            ),
            required_qualifiers=("provisional",),
            forbidden_promotions=("diagnosis",),
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
            derivation_rule_id="direct-burden.v1",
            semantic_refs=(semantic_refs[1],),
            evidence_refs=evidence_refs,
            basis_candidate_refs=(candidate_1.candidate_id,),
            epistemic_state=(
                InterpretationEpistemicState.PROVISIONAL_INTERPRETATION
            ),
            required_qualifiers=("provisional",),
            forbidden_promotions=("hidden-cause",),
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
                    semantic_refs=semantic_refs,
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
            derivation_rule_id="observe-center.v1",
            semantic_refs=semantic_refs,
            evidence_refs=evidence_refs,
            retention="REQUIRED",
            semantic_key_version="semantic-key.v1",
            canonical_semantic_key="state-1|context-1",
            prerequisite_contribution_refs=(),
            forbidden_operations=("invent-cause",),
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


def _stage1_sentence_unit_fixture(
    projection: EmlisStage1Projection,
) -> RealizedSentenceUnit:
    text = "見えた"
    binding = RealizedSemanticBinding(
        semantic_ref="node:state-1@graph.v1",
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
                topic_ref="node:state-1@graph.v1",
                predicate_operator=SemanticOperator.PRESENT_STATE.value,
                object_ref=None,
                argument_bindings=(
                    ArgumentBinding(
                        ArgumentRole.PRIMARY, "node:state-1@graph.v1"
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
            validate_stage1_projection(stale_projection)

    def test_canonical_json_key_order_is_invariant_but_semantic_order_changes_id(self) -> None:
        left = {"日本語": "見えた", "nested": {"b": 2, "a": 1}}
        right = {"nested": {"a": 1, "b": 2}, "日本語": "見えた"}
        self.assertEqual(
            stage1_canonical_json_bytes(left),
            stage1_canonical_json_bytes(right),
        )

        projection = _stage1_projection_fixture()
        candidate = projection.interpretation_candidates[0]
        self.assertNotEqual(
            recompute_stage1_identity(candidate),
            recompute_stage1_identity(
                replace(candidate, semantic_refs=tuple(reversed(candidate.semantic_refs)))
            ),
        )
        self.assertNotEqual(
            recompute_stage1_identity(candidate),
            recompute_stage1_identity(replace(candidate, schema_version="other.v1")),
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
        parent = ExperiencePlan(
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
        validate_stage1_projection(projection, parent_plan=parent)
        self.assertNotIn("core_projection_ref", {row.name for row in fields(ExperiencePlan)})

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
                    validate_stage1_projection(tampered)

    def test_subjective_refs_reject_policy_promotion_after_coordinated_rehash(
        self,
    ) -> None:
        projection = _stage1_projection_fixture()
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
            validate_stage1_projection(forged_projection)

    def test_sentence_unit_binds_projection_utf8_text_and_surface_digest(self) -> None:
        projection = _stage1_projection_fixture()
        unit = _stage1_sentence_unit_fixture(projection)
        validate_stage1_sentence_unit(unit, projection)

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
        ):
            with self.subTest(code=code):
                with self.assertRaisesRegex(CMEEStage1ContractError, code):
                    validate_stage1_sentence_unit(tampered, projection)

    def test_trace_spine_enforces_role_owner_reachability_and_exact_coverage(self) -> None:
        projection = _stage1_projection_fixture()
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
            meaning_node_ids=("state-1", "context-1"),
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
        validate_stage1_trace_spine(rows, projection)

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
                    validate_stage1_trace_spine(tampered, projection)


if __name__ == "__main__":
    unittest.main()
