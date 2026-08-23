# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import hashlib
import io
import inspect
import json
import re
import tempfile
import unittest
from collections import Counter
from dataclasses import fields, replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from emlis_ai_current_input_bundle import build_emlis_current_input_bundle
from emlis_ai_grounded_observation_plan import build_grounded_observation_plan
from cocolon_meaning_experience_engine import EngineStatus, GenerationRequest, MeaningExperienceEngine
from cocolon_meaning_experience_engine.contracts import (
    AffectCategory,
    AffectIntensity,
    ArgumentBinding,
    ArgumentRole,
    AttachmentAdmission,
    CMEE_GROUNDED_GRAPH_SCHEMA_VERSION,
    CMEE_STAGE1_EMLIS_OWNER_REF,
    CMEE_STAGE1_MICROGRAMMAR_POLICY_REF,
    CMEE_STAGE1_RECEPTION_ACT_MAPPING_EXACT7,
    CMEE_STAGE1_RECEPTION_ASSET_MAPPING_DOCS_BYTES,
    CMEE_STAGE1_RECEPTION_ASSET_MAPPING_DOCS_SHA256,
    CMEE_STAGE1_RECEPTION_ASSET_MAPPING_DOCS_TUPLE,
    CMEE_STAGE1_RECEPTION_ASSET_MAPPING_VERSION,
    CMEE_STAGE1_RECEPTION_STANCE_MAPPING_EXACT5,
    CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
    CMEE_STAGE1_TRACE_EXTENSION_SCHEMA_VERSION,
    CMEE_STAGE1_VALUE_POLICY_REF,
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
    RealizationCandidateSet,
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
    stage1_projection_artifact_ref,
    stage1_subjective_forbidden_promotions,
    stage1_subjective_semantic_key,
    stage1_value_principle_ref,
    validate_stage1_identity,
    validate_stage1_local_ref_dag,
    validate_stage1_projection,
    validate_stage1_sentence_unit,
    validate_stage1_trace_spine,
    validate_version_qualified_ref,
)
import cocolon_meaning_experience_engine.emlis_stage1_response as stage1_response_module
import cocolon_meaning_experience_engine.emlis_v1a as emlis_v1a_module
from cocolon_meaning_experience_engine.emlis_stage1_response import (
    CMEE_STAGE1_MICROGRAMMAR_INVENTORY_DOCS_BYTES,
    CMEE_STAGE1_MICROGRAMMAR_INVENTORY_DOCS_SHA256,
    CMEE_STAGE1_MICROGRAMMAR_INVENTORY_TUPLE,
    CMEE_STAGE1_MICROGRAMMAR_POLICY_VERSION,
    EmlisUtteranceState,
    INTERPRETATION_CANDIDATE_KIND_CAP,
    INTERPRETATION_CANDIDATE_POOL_CAP,
    INTERPRETATION_MATRIX_EXACT13,
    UtterancePhase,
    build_emlis_meaning_field,
    build_interpretation_candidate_pool,
    build_layer1_semantics,
    build_stage1_realization_candidate_set,
    build_stage1_semantic_projection,
    classify_affect_intensity,
    classify_observation_depth,
    classify_subjective_depth,
    initialize_emlis_utterance_state,
    select_stage1_realization_candidate,
    validate_layer2_subjective_plan,
    validate_reception_asset_mapping,
    validate_emlis_meaning_field,
    validate_layer1_observation_plan,
)
from cocolon_meaning_experience_engine.emlis_v1a import (
    CMEEVerticalError,
    _artifact_id,
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
import tools.cmee_v1a_i1sx_candidate_run as candidate_run_module
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


def _replace_projection_claim(
    projection: EmlisStage1Projection,
    index: int,
    claim: EmlisSubjectiveClaim,
) -> EmlisStage1Projection:
    identified_claim = _identified(
        replace(claim, subjective_claim_id=""),
        "subjective_claim_id",
    )
    claims = tuple(
        identified_claim if row_index == index else row
        for row_index, row in enumerate(projection.subjective_claims)
    )
    return _identified(
        replace(
            projection,
            projection_id="",
            subjective_claims=claims,
            ordered_subjective_refs=tuple(
                row.subjective_claim_id for row in claims
            ),
        ),
        "projection_id",
    )


def _stage1_grounded_graph_fixture() -> GroundedMeaningGraph:
    return GroundedMeaningGraph(
        graph_id="grounded-1",
        source_envelope_id="source-1",
        nodes=(
            MeaningNode(
                node_id="state-1",
                owner_id="owner-state-1",
                node_kind="BURDEN",
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
            semantic_operator=SemanticOperator.PRESENT_BURDEN,
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
            semantic_operator=SemanticOperator.PRESENT_STATE,
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
                    interpretation_candidate_refs=(candidate_2.candidate_id,),
                    semantic_refs=(semantic_refs[1],),
                    evidence_refs=evidence_refs,
                ),
                MeaningFieldEntry(
                    slot=MeaningFieldSlot.BURDEN,
                    interpretation_candidate_refs=(candidate_1.candidate_id,),
                    semantic_refs=(semantic_refs[0],),
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
            contribution_kind=ObservationContributionKind.OBSERVE_BURDEN,
            interpretation_candidate_refs=(candidate_1.candidate_id,),
            semantic_operator=SemanticOperator.PRESENT_BURDEN,
            argument_bindings=(
                ArgumentBinding(ArgumentRole.PRIMARY, semantic_refs[0]),
            ),
            relation_operator=RelationOperator.NO_RELATION_CLAIM,
            relation_basis_refs=(),
            derivation_rule_id=(
                "cocolon.cmee.v1a.stage1.layer1.observe_burden.v1"
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
            basis_semantic_refs=(semantic_refs[0],),
            source_reception_act_refs=("stay_with_current_burden",),
            value_principle_refs=(),
            user_fact_effect=0,
            forbidden_promotions=stage1_subjective_forbidden_promotions(
                (contribution,)
            ),
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
            retained_reception_act_ids=("stay_with_current_burden",),
            observation_depth_class=ObservationDepthClass.FOCUSED,
            subjective_depth_class=SubjectiveDepthClass.FOCUSED,
            temperature_class=TemperatureClass.STANDARD,
            reception_style_policy_ref=next(
                row.distance_policy_ref
                for row in CMEE_STAGE1_RECEPTION_STANCE_MAPPING_EXACT5
                if row.stance == "quiet_presence"
            ),
            emlis_value_policy_ref=CMEE_STAGE1_VALUE_POLICY_REF,
            emlis_microgrammar_policy_ref=CMEE_STAGE1_MICROGRAMMAR_POLICY_REF,
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
        reception_target_owner_ids=("owner-state-1",),
        visible_owner_ids=("owner-state-1",),
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
                predicate_operator=SemanticOperator.PRESENT_BURDEN.value,
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


def _stage4_exact8_fixture(index: int = 0):
    case_id, memo, category, emotion, strength = EXACT8[index]
    source, grounded_plan, graph, parent_plan = _stage2_inputs(
        _request(
            record_id=case_id,
            memo=memo,
            category=category,
            emotion=emotion,
            strength=strength,
        )
    )
    projection = build_stage1_semantic_projection(
        source=source,
        grounded_graph=graph,
        parent_plan=parent_plan,
        grounded_plan=grounded_plan,
    )
    candidate_set = build_stage1_realization_candidate_set(
        projection=projection,
        grounded_graph=graph,
        parent_plan=parent_plan,
    )
    return source, grounded_plan, graph, parent_plan, projection, candidate_set


class CMEEV1AI1SXContractsTest(unittest.TestCase):
    def test_step6_exact8_owner_authority_is_an_exact_positive_unresolved_partition(
        self,
    ) -> None:
        positive_dispositions = {
            RouteBDisposition.SOURCE_EXPLICIT_VISIBLE,
            RouteBDisposition.SUPPLEMENTAL_USER_VISIBLE,
        }
        for case_id, memo, category, emotion, strength in EXACT8:
            with self.subTest(case_id=case_id):
                source, _grounded_plan, graph, parent_plan = _stage2_inputs(
                    _request(
                        record_id=f"step6-authority-{case_id.lower()}",
                        memo=memo,
                        category=category,
                        emotion=emotion,
                        strength=strength,
                    )
                )
                owner_ids = tuple(
                    row.meaning_owner_id for row in graph.owner_dispositions
                )
                expected_owner_ids = (
                    *source.owner_universe.required_owner_refs,
                    *source.owner_universe.active_optional_owner_refs,
                )
                expected_visible_owner_ids = tuple(
                    row.meaning_owner_id
                    for row in graph.owner_dispositions
                    if row.route_b_disposition in positive_dispositions
                )
                expected_unresolved_owner_ids = tuple(
                    row.meaning_owner_id
                    for row in graph.owner_dispositions
                    if row.route_b_disposition not in positive_dispositions
                )

                self.assertEqual(owner_ids, expected_owner_ids)
                self.assertEqual(len(owner_ids), len(set(owner_ids)))
                self.assertEqual(
                    parent_plan.visible_owner_ids,
                    expected_visible_owner_ids,
                )
                self.assertEqual(
                    parent_plan.unresolved_owner_ids,
                    expected_unresolved_owner_ids,
                )
                self.assertTrue(
                    set(parent_plan.visible_owner_ids).isdisjoint(
                        parent_plan.unresolved_owner_ids
                    )
                )
                self.assertEqual(
                    set(parent_plan.visible_owner_ids)
                    | set(parent_plan.unresolved_owner_ids),
                    set(owner_ids),
                )
                self.assertTrue(
                    set(parent_plan.required_observation_owner_ids).issubset(
                        parent_plan.visible_owner_ids
                    )
                )
                self.assertTrue(
                    all(
                        bool(row.visible_claim_refs)
                        == (row.route_b_disposition in positive_dispositions)
                        for row in graph.owner_dispositions
                    )
                )

    def test_step6_exact8_optional_candidates_remain_structured_not_observed(
        self,
    ) -> None:
        structured_candidate_refs: set[str] = set()
        for case_id, memo, category, emotion, strength in EXACT8:
            with self.subTest(case_id=case_id):
                source, grounded_plan, graph, parent_plan = _stage2_inputs(
                    _request(
                        record_id=f"step6-optional-{case_id.lower()}",
                        memo=memo,
                        category=category,
                        emotion=emotion,
                        strength=strength,
                    )
                )
                projection = build_stage1_semantic_projection(
                    source=source,
                    grounded_graph=graph,
                    parent_plan=parent_plan,
                    grounded_plan=grounded_plan,
                )
                emotion_obligation = next(
                    row
                    for row in source.owner_universe.obligations
                    if row.obligation_kind == "EMOTION_CONTEXT"
                )
                emotion_disposition = next(
                    row
                    for row in graph.owner_dispositions
                    if row.meaning_owner_id
                    == emotion_obligation.meaning_owner_id
                )
                self.assertIs(emotion_obligation.owner_class, OwnerClass.ACTIVE_OPTIONAL)
                self.assertIs(emotion_disposition.owner_class, OwnerClass.ACTIVE_OPTIONAL)
                self.assertIs(
                    emotion_disposition.route_b_disposition,
                    RouteBDisposition.SOURCE_EXPLICIT_VISIBLE,
                )
                self.assertIs(
                    emotion_disposition.visible_authority,
                    VisibleAuthority.SOURCE_EXPLICIT,
                )
                self.assertTrue(emotion_disposition.visible_claim_refs)
                self.assertIn(
                    emotion_obligation.meaning_owner_id,
                    parent_plan.visible_owner_ids,
                )
                self.assertNotIn(
                    emotion_obligation.meaning_owner_id,
                    parent_plan.unresolved_owner_ids,
                )
                self.assertNotIn(
                    emotion_obligation.meaning_owner_id,
                    parent_plan.required_observation_owner_ids,
                )

                claim_owner_by_id = {
                    **{row.node_id: row.owner_id for row in graph.nodes},
                    **{row.edge_id: row.owner_id for row in graph.edges},
                }
                structured_context_kinds = {
                    "EMOTION_CONTEXT",
                    "CATEGORY_CONTEXT",
                    "EMOTION_STRENGTH_CONTEXT",
                    "STRUCTURED_CONTEXT_ATTACHMENT",
                }
                structured_owner_ids = {
                    row.meaning_owner_id
                    for row in source.owner_universe.obligations
                    if row.obligation_kind in structured_context_kinds
                    and row.owner_class is OwnerClass.ACTIVE_OPTIONAL
                }
                candidate_refs = {
                    row.candidate_id for row in projection.interpretation_candidates
                }
                required_candidate_refs = set(
                    projection.meaning_field.required_candidate_refs
                )
                optional_candidate_refs = candidate_refs - required_candidate_refs
                field_candidate_refs = {
                    ref
                    for entry in projection.meaning_field.entries
                    for ref in entry.interpretation_candidate_refs
                }
                self.assertTrue(optional_candidate_refs)
                self.assertEqual(field_candidate_refs, candidate_refs)

                for candidate in projection.interpretation_candidates:
                    candidate_owner_ids = {
                        claim_owner_by_id[
                            ref.split(":", 1)[1].rsplit("@", 1)[0]
                        ]
                        for ref in (
                            *candidate.semantic_refs,
                            *candidate.relation_basis_refs,
                        )
                    }
                    if candidate_owner_ids.intersection(structured_owner_ids):
                        structured_candidate_refs.add(candidate.candidate_id)
                        self.assertIn(
                            candidate.candidate_id,
                            optional_candidate_refs,
                        )

                optional_contributions = tuple(
                    row
                    for row in projection.observation_contributions
                    if row.retention == "OPTIONAL"
                )
                self.assertEqual(optional_contributions, ())
                contribution_candidate_refs = {
                    ref
                    for row in projection.observation_contributions
                    for ref in row.interpretation_candidate_refs
                }
                self.assertEqual(
                    contribution_candidate_refs,
                    required_candidate_refs,
                )
                self.assertTrue(
                    optional_candidate_refs.isdisjoint(
                        contribution_candidate_refs
                    )
                )

        self.assertTrue(structured_candidate_refs)

    def test_step6_coordinated_optional_owner_disposition_downgrade_is_rejected(
        self,
    ) -> None:
        case_id, memo, category, emotion, strength = EXACT8[0]
        source, grounded_plan, graph, parent_plan = _stage2_inputs(
            _request(
                record_id=f"step6-downgrade-{case_id.lower()}",
                memo=memo,
                category=category,
                emotion=emotion,
                strength=strength,
            )
        )
        projection = build_stage1_semantic_projection(
            source=source,
            grounded_graph=graph,
            parent_plan=parent_plan,
            grounded_plan=grounded_plan,
        )
        validate_stage1_projection(
            projection,
            grounded_graph=graph,
            parent_plan=parent_plan,
        )
        emotion_owner_id = next(
            row.meaning_owner_id
            for row in source.owner_universe.obligations
            if row.obligation_kind == "EMOTION_CONTEXT"
        )
        downgraded_dispositions = tuple(
            replace(
                row,
                visible_authority=VisibleAuthority.NONE,
                route_b_disposition=RouteBDisposition.NOT_VISIBLE_UNRESOLVED,
                visible_claim_refs=(),
                reason_codes=("ATTACHMENT_UNRESOLVED",),
            )
            if row.meaning_owner_id == emotion_owner_id
            else row
            for row in graph.owner_dispositions
        )
        downgraded_graph = replace(
            graph,
            owner_dispositions=downgraded_dispositions,
        )
        positive_dispositions = {
            RouteBDisposition.SOURCE_EXPLICIT_VISIBLE,
            RouteBDisposition.SUPPLEMENTAL_USER_VISIBLE,
        }
        coordinated_parent_plan = replace(
            parent_plan,
            visible_owner_ids=tuple(
                row.meaning_owner_id
                for row in downgraded_dispositions
                if row.route_b_disposition in positive_dispositions
            ),
            unresolved_owner_ids=tuple(
                row.meaning_owner_id
                for row in downgraded_dispositions
                if row.route_b_disposition not in positive_dispositions
            ),
        )
        self.assertNotIn(
            emotion_owner_id,
            coordinated_parent_plan.visible_owner_ids,
        )
        self.assertIn(
            emotion_owner_id,
            coordinated_parent_plan.unresolved_owner_ids,
        )
        with self.assertRaisesRegex(
            CMEEStage1ContractError,
            "stage1_candidate_visible_owner_disposition_mismatch",
        ):
            validate_stage1_projection(
                projection,
                grounded_graph=downgraded_graph,
                parent_plan=coordinated_parent_plan,
            )

        outcome = MeaningExperienceEngine().generate(
            _request(
                record_id=f"step6-runner-downgrade-{case_id.lower()}",
                memo=memo,
                category=category,
                emotion=emotion,
                strength=strength,
            )
        )
        self.assertEqual(outcome.status.value, "GENERATED", outcome.reason_codes)
        self.assertIsNotNone(outcome.artifact)
        self.assertIsNotNone(outcome.meaning_graph)
        assert outcome.artifact is not None
        assert outcome.meaning_graph is not None
        runtime_used_claim_ids = {
            *(
                claim_id
                for trace in outcome.artifact.trace
                for claim_id in trace.meaning_node_ids
            ),
            *(
                claim_id
                for trace in outcome.artifact.trace
                for claim_id in trace.meaning_edge_ids
            ),
        }
        optional_visible_dispositions = tuple(
            row
            for row in outcome.meaning_graph.owner_dispositions
            if row.owner_class is OwnerClass.ACTIVE_OPTIONAL
            and row.route_b_disposition in positive_dispositions
        )
        self.assertTrue(optional_visible_dispositions)
        self.assertTrue(
            all(
                set(row.visible_claim_refs).isdisjoint(runtime_used_claim_ids)
                for row in optional_visible_dispositions
            )
        )
        runtime_owner_ids = tuple(
            row.meaning_owner_id
            for row in outcome.meaning_graph.owner_dispositions
            if row.owner_class is OwnerClass.REQUIRED
            and row.route_b_disposition in positive_dispositions
            and set(row.visible_claim_refs).intersection(runtime_used_claim_ids)
        )
        self.assertEqual(len(runtime_owner_ids), 1)
        runtime_owner_id = runtime_owner_ids[0]
        runtime_dispositions = tuple(
            replace(
                row,
                visible_authority=VisibleAuthority.NONE,
                route_b_disposition=RouteBDisposition.NOT_VISIBLE_UNRESOLVED,
                visible_claim_refs=(),
                reason_codes=("ATTACHMENT_UNRESOLVED",),
            )
            if row.meaning_owner_id == runtime_owner_id
            else row
            for row in outcome.meaning_graph.owner_dispositions
        )
        runtime_plan = replace(
            outcome.artifact.plan,
            visible_owner_ids=tuple(
                row.meaning_owner_id
                for row in runtime_dispositions
                if row.route_b_disposition in positive_dispositions
            ),
            unresolved_owner_ids=tuple(
                row.meaning_owner_id
                for row in runtime_dispositions
                if row.route_b_disposition not in positive_dispositions
            ),
        )
        self.assertFalse(
            candidate_run_module._structural_trace_valid(
                replace(
                    outcome,
                    meaning_graph=replace(
                        outcome.meaning_graph,
                        owner_dispositions=runtime_dispositions,
                    ),
                    artifact=replace(outcome.artifact, plan=runtime_plan),
                )
            )
        )

    def test_step6_runner_rejects_directional_trace_endpoint_reversal(self) -> None:
        outcome = MeaningExperienceEngine().generate(
            _request(
                record_id="step6-runner-directional-trace",
                memo="前は動いた。今は不安が残っている。",
                category="生活",
                emotion="不安",
                strength="medium",
            )
        )
        self.assertEqual(outcome.status.value, "GENERATED", outcome.reason_codes)
        self.assertIsNotNone(outcome.artifact)
        self.assertIsNotNone(outcome.meaning_graph)
        assert outcome.artifact is not None
        assert outcome.meaning_graph is not None
        self.assertTrue(candidate_run_module._structural_trace_valid(outcome))

        edge_by_id = {
            row.edge_id: row for row in outcome.meaning_graph.edges
        }
        directional_index = next(
            index
            for index, trace in enumerate(outcome.artifact.trace)
            if any(
                edge_by_id[edge_id].relation == "shift_from_to"
                for edge_id in trace.meaning_edge_ids
            )
        )
        directional_trace = outcome.artifact.trace[directional_index]
        self.assertEqual(len(directional_trace.meaning_node_ids), 2)
        reversed_trace = replace(
            directional_trace,
            meaning_node_ids=tuple(reversed(directional_trace.meaning_node_ids)),
        )
        forged_traces = list(outcome.artifact.trace)
        forged_traces[directional_index] = reversed_trace
        self.assertFalse(
            candidate_run_module._structural_trace_valid(
                replace(
                    outcome,
                    artifact=replace(
                        outcome.artifact,
                        trace=tuple(forged_traces),
                    ),
                )
            )
        )

    def test_step6_runner_rejects_noncanonical_route_b_row_fields(self) -> None:
        case_id, memo, category, emotion, strength = EXACT8[0]
        outcome = MeaningExperienceEngine().generate(
            _request(
                record_id=f"step6-runner-owner-shape-{case_id.lower()}",
                memo=memo,
                category=category,
                emotion=emotion,
                strength=strength,
            )
        )
        self.assertEqual(outcome.status.value, "GENERATED", outcome.reason_codes)
        self.assertIsNotNone(outcome.artifact)
        self.assertIsNotNone(outcome.meaning_graph)
        assert outcome.artifact is not None
        assert outcome.meaning_graph is not None
        self.assertTrue(candidate_run_module._structural_trace_valid(outcome))

        positive = next(
            row
            for row in outcome.meaning_graph.owner_dispositions
            if row.route_b_disposition
            is RouteBDisposition.SOURCE_EXPLICIT_VISIBLE
        )
        positive_mutations = (
            replace(positive, visible_authority=VisibleAuthority.NONE),
            replace(positive, provider_resolution=ProviderResolution.UNRESOLVED),
            replace(positive, attachment_admission=AttachmentAdmission.UNRESOLVED),
            replace(positive, reason_codes=("tampered",)),
        )
        for mutated in positive_mutations:
            with self.subTest(field_shape=mutated):
                dispositions = tuple(
                    mutated if row.owner_id == positive.owner_id else row
                    for row in outcome.meaning_graph.owner_dispositions
                )
                self.assertFalse(
                    candidate_run_module._structural_trace_valid(
                        replace(
                            outcome,
                            meaning_graph=replace(
                                outcome.meaning_graph,
                                owner_dispositions=dispositions,
                            ),
                        )
                    )
                )

        nonvisible = next(
            row
            for row in outcome.meaning_graph.owner_dispositions
            if row.route_b_disposition
            is RouteBDisposition.NOT_VISIBLE_UNRESOLVED
        )
        owned_node = next(
            row
            for row in outcome.meaning_graph.nodes
            if row.owner_id == nonvisible.owner_id
        )
        injected = replace(
            nonvisible,
            visible_claim_refs=(owned_node.node_id,),
        )
        injected_dispositions = tuple(
            injected if row.owner_id == nonvisible.owner_id else row
            for row in outcome.meaning_graph.owner_dispositions
        )
        self.assertFalse(
            candidate_run_module._structural_trace_valid(
                replace(
                    outcome,
                    meaning_graph=replace(
                        outcome.meaning_graph,
                        owner_dispositions=injected_dispositions,
                    ),
                )
            )
        )

    def test_step6_private_output_boundary_rejects_before_runner_execution(
        self,
    ) -> None:
        body_sentinel = "疲れている-private-body-sentinel"
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory).resolve()
            isolated_root = (temporary_root / "private-root").resolve()
            checkout_overlap_root = (
                candidate_run_module.CHECKOUT_ROOT / "private-test-root"
            ).resolve()
            invalid_targets = (
                ("root", isolated_root, isolated_root),
                (
                    "outside",
                    isolated_root,
                    temporary_root / "outside" / f"{body_sentinel}.json",
                ),
                (
                    "checkout-descendant",
                    checkout_overlap_root,
                    checkout_overlap_root / f"{body_sentinel}.json",
                ),
                (
                    "checkout-exact",
                    candidate_run_module.CHECKOUT_ROOT,
                    candidate_run_module.CHECKOUT_ROOT
                    / f"{body_sentinel}.json",
                ),
                (
                    "checkout-ancestor",
                    candidate_run_module.CHECKOUT_ROOT.parent,
                    candidate_run_module.CHECKOUT_ROOT.parent
                    / f"{body_sentinel}.json",
                ),
            )
            for scenario, private_root, requested_target in invalid_targets:
                with self.subTest(scenario=scenario):
                    stderr = io.StringIO()
                    with (
                        patch.object(
                            candidate_run_module,
                            "PRIVATE_OUTPUT_ROOT",
                            private_root,
                        ),
                        patch.object(
                            candidate_run_module.sys,
                            "argv",
                            (
                                "cmee-v1a-candidate-run",
                                "--body-full-output",
                                str(requested_target),
                            ),
                        ),
                        patch.object(candidate_run_module.sys, "stderr", stderr),
                        patch.object(
                            candidate_run_module,
                            "run",
                            side_effect=AssertionError(
                                "runner must not execute for an invalid target"
                            ),
                        ) as runner,
                    ):
                        with self.assertRaises(SystemExit) as raised:
                            candidate_run_module.main()

                    self.assertEqual(raised.exception.code, 2)
                    runner.assert_not_called()
                    error_text = stderr.getvalue()
                    self.assertIn("private output", error_text)
                    self.assertNotIn(str(private_root), error_text)
                    self.assertNotIn(str(requested_target), error_text)
                    self.assertNotIn(body_sentinel, error_text)
                    self.assertTrue(
                        all(memo not in error_text for _case_id, memo, *_ in EXACT8)
                    )

    def test_step6_private_output_accepts_only_an_isolated_descendant(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            private_root = (Path(temporary_directory) / "private-root").resolve()
            requested_target = private_root / "nested" / "packet.json"
            parser = candidate_run_module.argparse.ArgumentParser(add_help=False)
            with patch.object(
                candidate_run_module,
                "PRIVATE_OUTPUT_ROOT",
                private_root,
            ):
                self.assertEqual(
                    candidate_run_module._private_output_target(
                        parser,
                        requested_target,
                    ),
                    requested_target.resolve(),
                )

    def test_step6_runner_body_free_tree_has_no_private_body_or_locator(self) -> None:
        runtime_head = "a" * 40
        design_head = "b" * 40
        body_free, private_packet = candidate_run_module.run(
            runtime_repo_head=runtime_head,
            design_repo_head=design_head,
        )

        keys: list[str] = []

        def collect_keys(value: object) -> None:
            if type(value) is dict:
                for key, child in value.items():
                    keys.append(str(key))
                    collect_keys(child)
            elif type(value) in {list, tuple}:
                for child in value:
                    collect_keys(child)

        collect_keys(body_free)
        forbidden_private_keys = {
            "memo",
            "memo_action",
            "synthetic_input_private",
            "candidate_private",
            "private_slot_id",
            "private_body_full",
            "observation",
            "reception",
            "raw_sha256",
            "literal_sha256",
            "envelope_id",
            "graph_id",
            "artifact_id",
        }
        self.assertTrue(forbidden_private_keys.isdisjoint(keys))
        self.assertTrue(
            all(
                "digest" not in key.lower()
                and "locator" not in key.lower()
                and not key.lower().endswith("_sha256")
                and not key.lower().endswith("_private")
                for key in keys
            )
        )
        self.assertFalse(body_free["private_text_published"])
        mutation_registry = body_free["finite_mutation_set_body_free"]
        self.assertFalse(mutation_registry["body_payload_present"])
        self.assertFalse(mutation_registry["runner_executes_source_bodies"])

        binding = private_packet["private_packet_binding"]
        self.assertEqual(
            binding["binding_version"],
            "cocolon.cmee.stage1.private_packet_binding.v1",
        )
        self.assertEqual(binding["packet_id"], private_packet["packet_id"])
        self.assertEqual(binding["runtime_repo_head"], runtime_head)
        self.assertEqual(binding["design_repo_head"], design_head)
        self.assertEqual(
            binding["fixture_identity"]["fixture_order"],
            [row[0] for row in EXACT8],
        )
        for digest in (
            binding["fixture_identity"]["fixture_and_axes_sha256"],
            binding["runner_identity"]["runner_sha256"],
            binding["packet_binding_sha256"],
        ):
            self.assertRegex(digest, r"^[0-9a-f]{64}$")
            self.assertNotIn(digest, json.dumps(body_free, sort_keys=True))
        self.assertEqual(
            binding["runner_identity"]["repo_relative_path"],
            "ai/tools/cmee_v1a_i1sx_candidate_run.py",
        )

        serialized = json.dumps(body_free, ensure_ascii=False, sort_keys=True)
        for _case_id, memo, _category, _emotion, _strength in EXACT8:
            self.assertNotIn(memo, serialized)
        for case in private_packet["cases"]:
            private_input = case["synthetic_input_private"]
            private_values: list[str] = []

            def collect_private_values(value: object) -> None:
                if type(value) is dict:
                    for child in value.values():
                        collect_private_values(child)
                elif type(value) in {list, tuple}:
                    for child in value:
                        collect_private_values(child)
                elif type(value) is str and value:
                    private_values.append(value)

            collect_private_values(private_input)
            candidate_text = case["candidate_private"]
            if candidate_text:
                private_values.append(candidate_text)
            self.assertTrue(
                all(private_value not in serialized for private_value in private_values)
            )

    def test_step5_compiler_facade_owns_projection_s8_and_s9_exactly_once(self) -> None:
        case_id, memo, category, emotion, strength = EXACT8[5]
        source, grounded_plan, graph, parent_plan = _stage2_inputs(
            _request(
                record_id=f"step5-{case_id.lower()}",
                memo=memo,
                category=category,
                emotion=emotion,
                strength=strength,
            )
        )
        with (
            patch.object(
                stage1_response_module,
                "build_stage1_semantic_projection",
                wraps=stage1_response_module.build_stage1_semantic_projection,
            ) as projection_builder,
            patch.object(
                stage1_response_module,
                "build_stage1_realization_candidate_set",
                wraps=stage1_response_module.build_stage1_realization_candidate_set,
            ) as candidate_builder,
            patch.object(
                stage1_response_module,
                "select_stage1_realization_candidate",
                wraps=stage1_response_module.select_stage1_realization_candidate,
            ) as candidate_selector,
        ):
            projection, selected = stage1_response_module.compile_stage1_response(
                source=source,
                grounded_graph=graph,
                parent_plan=parent_plan,
                grounded_plan=grounded_plan,
            )

        self.assertEqual(projection_builder.call_count, 1)
        self.assertEqual(candidate_builder.call_count, 1)
        self.assertEqual(candidate_selector.call_count, 1)
        self.assertEqual(
            tuple(row.layer for row in selected),
            ("LAYER_1", "LAYER_1", "LAYER_2", "LAYER_2", "LAYER_2"),
        )
        self.assertEqual(
            tuple(row.basis_anchor_refs[0] for row in selected),
            (
                *projection.ordered_observation_refs,
                *projection.ordered_subjective_refs,
            ),
        )

    def test_step5_trace_spine_reaches_selected_relation_basis_edges(self) -> None:
        case_id, memo, category, emotion, strength = EXACT8[6]
        source, grounded_plan, graph, parent_plan = _stage2_inputs(
            _request(
                record_id=f"step5-relation-{case_id.lower()}",
                memo=memo,
                category=category,
                emotion=emotion,
                strength=strength,
            )
        )
        projection, selected = stage1_response_module.compile_stage1_response(
            source=source,
            grounded_graph=graph,
            parent_plan=parent_plan,
            grounded_plan=grounded_plan,
        )
        observation_lines, reception_lines = emlis_v1a_module._stage1_visible_lines(
            source,
            graph,
            grounded_plan,
            projection,
            selected,
        )
        safe_lines = (*observation_lines, *reception_lines)
        bound_plan = emlis_v1a_module._bind_plan_to_visible_lines(
            source,
            graph,
            parent_plan,
            safe_lines,
        )
        trace = emlis_v1a_module._trace_for_lines(
            source,
            graph,
            bound_plan,
            safe_lines,
            "proof:step5-relation",
            projection,
            selected,
        )

        relation_rows = tuple(
            row for row in trace if row.role == "OBSERVATION" and row.meaning_edge_ids
        )
        self.assertEqual(len(relation_rows), 2)
        validate_stage1_trace_spine(
            trace,
            projection,
            grounded_graph=graph,
            parent_plan=bound_plan,
        )

        tampered = list(trace)
        first_index = trace.index(relation_rows[0])
        tampered[first_index] = replace(
            relation_rows[0],
            meaning_edge_ids=relation_rows[1].meaning_edge_ids,
        )
        with self.assertRaisesRegex(
            CMEEStage1ContractError,
            "stage1_observation_trace_lineage_unreachable",
        ):
            validate_stage1_trace_spine(
                tuple(tampered),
                projection,
                grounded_graph=graph,
                parent_plan=bound_plan,
            )

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
        self.assertGreaterEqual(report["reception_unit_count"], 1)
        self.assertLessEqual(report["reception_unit_count"], 4)
        assert outcome.artifact is not None
        self.assertEqual(
            report["reception_unit_count"],
            sum(row.role == "RECEPTION" for row in outcome.artifact.trace),
        )
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
                    forged_relation_entry,
                    projection.meaning_field.entries[1],
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

        projection = build_stage1_semantic_projection(
            source=source,
            grounded_graph=grounded_graph,
            parent_plan=parent_plan,
            grounded_plan=grounded_plan,
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
            meaning_node_ids=("state-1",),
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
            ((reception, unknown, observation), "role_order_invalid"),
            ((observation, unknown), "role_order_invalid"),
            (
                (
                    observation,
                    unknown,
                    reception,
                    replace(reception, visible_unit_id="cmee:reception:2"),
                ),
                "role_order_invalid",
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
        expected_shape_by_case = {
            "SX-01": (1, ObservationDepthClass.FOCUSED),
            "SX-02": (1, ObservationDepthClass.FOCUSED),
            "SX-03": (1, ObservationDepthClass.FOCUSED),
            "SX-04": (2, ObservationDepthClass.LAYERED),
            "SX-05": (1, ObservationDepthClass.FOCUSED),
            "SX-06": (2, ObservationDepthClass.LAYERED),
            "SX-07": (2, ObservationDepthClass.LAYERED),
            "SX-08": (1, ObservationDepthClass.FOCUSED),
        }
        observed_shape_by_case: dict[
            str, tuple[int, ObservationDepthClass]
        ] = {}
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
                self.assertTrue(
                    all(row.retention == "REQUIRED" for row in contributions)
                )
                self.assertEqual(
                    tuple(
                        ref
                        for row in contributions
                        for ref in row.interpretation_candidate_refs
                    ),
                    meaning_field.required_candidate_refs,
                )
                self.assertEqual(
                    ordered_refs,
                    tuple(row.contribution_id for row in contributions),
                )
                self.assertEqual(
                    len({row.canonical_semantic_key for row in contributions}),
                    len(contributions),
                )
                observed_shape_by_case[case_id] = (len(contributions), depth)
                self.assertEqual(
                    observed_shape_by_case[case_id],
                    expected_shape_by_case[case_id],
                )

        self.assertEqual(observed_shape_by_case, expected_shape_by_case)

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
            and row.owner_id in set(graph.active_optional_owner_refs)
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
            _request(
                record_id="stage2-required-overflow",
                memo="疲れた。つらい。苦しい。",
            )
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

    def test_stage3_mapping_tuple_and_canonical_docs_bytes_are_exact(self) -> None:
        self.assertEqual(
            CMEE_STAGE1_RECEPTION_ASSET_MAPPING_VERSION,
            "cocolon.emlis.stage1.reception_asset_mapping.v1",
        )
        self.assertEqual(len(CMEE_STAGE1_RECEPTION_ACT_MAPPING_EXACT7), 7)
        self.assertEqual(len(CMEE_STAGE1_RECEPTION_STANCE_MAPPING_EXACT5), 5)
        self.assertEqual(
            CMEE_STAGE1_RECEPTION_ASSET_MAPPING_DOCS_BYTES,
            stage1_canonical_json_bytes(
                CMEE_STAGE1_RECEPTION_ASSET_MAPPING_DOCS_TUPLE
            ),
        )
        self.assertEqual(
            CMEE_STAGE1_RECEPTION_ASSET_MAPPING_DOCS_SHA256,
            "1fca37e4dd4efd06c09e63f14a1977ab31856dde8b147803cbab0d166eec2587",
        )
        self.assertEqual(len(CMEE_STAGE1_RECEPTION_ASSET_MAPPING_DOCS_BYTES), 7336)
        self.assertEqual(
            hashlib.sha256(
                CMEE_STAGE1_RECEPTION_ASSET_MAPPING_DOCS_BYTES
            ).hexdigest(),
            CMEE_STAGE1_RECEPTION_ASSET_MAPPING_DOCS_SHA256,
        )

    def test_stage3_exact8_builds_deterministic_grounded_layer2(self) -> None:
        legacy_depths: set[str] = set()
        for case_id, memo, category, emotion, strength in EXACT8:
            with self.subTest(case_id=case_id):
                source, grounded_plan, graph, parent_plan = _stage2_inputs(
                    _request(
                        record_id=case_id,
                        memo=memo,
                        category=category,
                        emotion=emotion,
                        strength=strength,
                    )
                )
                first = build_stage1_semantic_projection(
                    source=source,
                    grounded_graph=graph,
                    parent_plan=parent_plan,
                    grounded_plan=grounded_plan,
                )
                second = build_stage1_semantic_projection(
                    source=source,
                    grounded_graph=graph,
                    parent_plan=parent_plan,
                    grounded_plan=grounded_plan,
                )
                self.assertEqual(first, second)
                material_value_case = case_id == EXACT8[5][0]
                self.assertEqual(
                    len(first.subjective_claims),
                    3 if material_value_case else 2,
                )
                self.assertIs(
                    first.subjective_depth_class,
                    SubjectiveDepthClass.LAYERED,
                )
                self.assertEqual(
                    {act for claim in first.subjective_claims for act in claim.source_reception_act_refs},
                    set(parent_plan.allowed_reception_act_ids),
                )
                self.assertTrue(
                    all(
                        claim.speaker_owner == "EMLIS"
                        and claim.user_fact_effect == 0
                        and len(claim.source_reception_act_refs) == 1
                        and claim.asserted_subjective_proposition.affect_category
                        is not AffectCategory.DISCOMFORT
                        for claim in first.subjective_claims
                    )
                )
                visible_value_rows = tuple(
                    claim.value_principle_refs
                    for claim in first.subjective_claims
                    if claim.value_principle_refs
                )
                self.assertEqual(
                    visible_value_rows,
                    (
                        (
                            stage1_value_principle_ref("V2"),
                            stage1_value_principle_ref("V8"),
                        ),
                    )
                    if material_value_case
                    else (),
                )
                validate_layer2_subjective_plan(
                    first.subjective_claims,
                    source=source,
                    grounded_graph=graph,
                    parent_plan=parent_plan,
                    grounded_plan=grounded_plan,
                    observation_contributions=first.observation_contributions,
                )
                reception_plan = stage1_response_module._semantic_reception_asset(
                    source=source,
                    grounded_plan=grounded_plan,
                )
                legacy_depths.add(reception_plan.depth_policy.level)
        self.assertEqual(legacy_depths, {"minimal", "focused"})

    def test_stage3_reception_asset_rejects_unregistered_or_relaxed_axes(self) -> None:
        case_id, memo, category, emotion, strength = EXACT8[3]
        source, grounded_plan, _graph, _parent = _stage2_inputs(
            _request(
                record_id=case_id,
                memo=memo,
                category=category,
                emotion=emotion,
                strength=strength,
            )
        )
        plan = stage1_response_module._semantic_reception_asset(
            source=source,
            grounded_plan=grounded_plan,
        )
        move = plan.moves[0]
        invalid_plans = (
            replace(
                plan,
                primary_reception_act="unregistered_act",
                moves=(replace(move, reception_act="unregistered_act"),),
            ),
            replace(plan, stance="unregistered_stance"),
            replace(plan, speaker_presence="unregistered_speaker"),
            replace(plan, reference_mode="unregistered_reference"),
            replace(
                plan,
                moves=(replace(move, surface_strategy="unregistered_strategy"),),
            ),
            replace(
                plan,
                moves=(replace(move, move_role="unregistered_role"),),
            ),
            replace(
                plan,
                quote_policy=replace(
                    plan.quote_policy,
                    max_anchor_visible_chars=20,
                ),
            ),
            replace(
                plan,
                distinctness_policy=replace(
                    plan.distinctness_policy,
                    advice_allowed=True,
                ),
            ),
            replace(
                plan,
                safety_modifier_codes=("unregistered_safety",),
            ),
            replace(
                plan,
                forbidden_surface_codes=(
                    *plan.forbidden_surface_codes,
                    "unregistered_surface_code",
                ),
            ),
            replace(
                plan,
                depth_policy=replace(plan.depth_policy, level="dense"),
            ),
        )
        for invalid in invalid_plans:
            with self.subTest(invalid=invalid):
                with self.assertRaises(CMEEStage1ContractError):
                    validate_reception_asset_mapping(
                        invalid,
                        grounded_plan=grounded_plan,
                    )

    def test_stage3_cross_field_depth_and_semantic_distinctness_fail_closed(self) -> None:
        case_id, memo, category, emotion, strength = EXACT8[3]
        source, grounded_plan, graph, parent_plan = _stage2_inputs(
            _request(
                record_id=case_id,
                memo=memo,
                category=category,
                emotion=emotion,
                strength=strength,
            )
        )
        projection = build_stage1_semantic_projection(
            source=source,
            grounded_graph=graph,
            parent_plan=parent_plan,
            grounded_plan=grounded_plan,
        )
        claim_index = 1
        claim = projection.subjective_claims[claim_index]
        invalid_claims = (
            (
                replace(
                    claim,
                    asserted_subjective_proposition=replace(
                        claim.asserted_subjective_proposition,
                        subjective_operator=SubjectiveOperator.FEEL_TOWARD,
                    ),
                ),
                "stage1_subjective_cross_field_invalid",
            ),
            (
                replace(
                    claim,
                    source_reception_act_refs=(
                        claim.source_reception_act_refs[0],
                        claim.source_reception_act_refs[0],
                    ),
                ),
                "stage1_subjective_reception_act_union_invalid",
            ),
            (
                replace(
                    claim,
                    basis_semantic_refs=(
                        *claim.basis_semantic_refs,
                        projection.observation_contributions[1].semantic_refs[0],
                    ),
                ),
                "stage1_subjective_basis_semantic_projection_mismatch",
            ),
        )
        for invalid_claim, code in invalid_claims:
            with self.subTest(code=code):
                invalid_projection = _replace_projection_claim(
                    projection,
                    claim_index,
                    invalid_claim,
                )
                with self.assertRaisesRegex(CMEEStage1ContractError, code):
                    validate_stage1_projection(
                        invalid_projection,
                        grounded_graph=graph,
                        parent_plan=parent_plan,
                    )

        contribution_by_id = {
            row.contribution_id: row
            for row in projection.observation_contributions
        }
        basis_contributions = tuple(
            contribution_by_id[ref]
            for ref in claim.basis_observation_contribution_refs
        )
        reachable = {
            *claim.basis_observation_contribution_refs,
            *(
                ref
                for row in basis_contributions
                for ref in (*row.semantic_refs, *row.relation_basis_refs)
            ),
        }
        unrelated_refs = tuple(
            f"node:{row.node_id}@{CMEE_GROUNDED_GRAPH_SCHEMA_VERSION}"
            for row in graph.nodes
            if f"node:{row.node_id}@{CMEE_GROUNDED_GRAPH_SCHEMA_VERSION}"
            not in reachable
        )
        self.assertTrue(unrelated_refs)
        unrelated = unrelated_refs[0]
        unreachable_claim = replace(
            claim,
            asserted_subjective_proposition=replace(
                claim.asserted_subjective_proposition,
                response_object_refs=(unrelated,),
            ),
        )
        with self.assertRaisesRegex(
            CMEEStage1ContractError,
            "stage1_subjective_response_object_unreachable",
        ):
            validate_stage1_projection(
                _replace_projection_claim(
                    projection,
                    claim_index,
                    unreachable_claim,
                ),
                grounded_graph=graph,
                parent_plan=parent_plan,
            )

        extra_basis_rows = tuple(
            row
            for row in projection.observation_contributions
            if row.contribution_id
            not in claim.basis_observation_contribution_refs
        )
        self.assertEqual(len(extra_basis_rows), 1)
        extra_basis = extra_basis_rows[0]
        duplicate_basis_refs = (
            *claim.basis_observation_contribution_refs,
            extra_basis.contribution_id,
        )
        duplicate_basis = tuple(
            contribution_by_id[ref] for ref in duplicate_basis_refs
        )
        duplicate = _identified(
            replace(
                claim,
                subjective_claim_id="",
                basis_observation_contribution_refs=duplicate_basis_refs,
                basis_semantic_refs=tuple(
                    dict.fromkeys(
                        ref
                        for row in duplicate_basis
                        for ref in (
                            *row.semantic_refs,
                            *row.relation_basis_refs,
                        )
                    )
                ),
                forbidden_promotions=stage1_subjective_forbidden_promotions(
                    duplicate_basis,
                    material_unknown_refs=(
                        projection.meaning_field.material_unknown_refs
                    ),
                ),
            ),
            "subjective_claim_id",
        )
        claims = (*projection.subjective_claims, duplicate)
        duplicate_projection = _identified(
            replace(
                projection,
                projection_id="",
                subjective_claims=claims,
                ordered_subjective_refs=tuple(
                    row.subjective_claim_id for row in claims
                ),
            ),
            "projection_id",
        )
        with self.assertRaisesRegex(
            CMEEStage1ContractError,
            "stage1_duplicate_subjective_claim",
        ):
            validate_stage1_projection(
                duplicate_projection,
                grounded_graph=graph,
                parent_plan=parent_plan,
            )

    def test_stage3_discomfort_never_targets_user_state_or_personality(self) -> None:
        projection = _stage1_projection_fixture()
        graph = _stage1_grounded_graph_fixture()
        parent_plan = _stage1_parent_plan_fixture(projection)
        claim = projection.subjective_claims[0]
        user_state_ref = (
            f"node:state-1@{CMEE_GROUNDED_GRAPH_SCHEMA_VERSION}"
        )
        discomfort = replace(
            claim,
            subjective_mode=SubjectiveMode.AFFECTIVE_RESPONSE,
            asserted_subjective_proposition=replace(
                claim.asserted_subjective_proposition,
                subjective_operator=SubjectiveOperator.FEEL_TOWARD,
                response_object_refs=(user_state_ref,),
                affect_category=AffectCategory.DISCOMFORT,
                affect_intensity=AffectIntensity.QUIET,
            ),
        )
        with self.assertRaisesRegex(
            CMEEStage1ContractError,
            "stage1_subjective_discomfort_target_invalid",
        ):
            validate_stage1_projection(
                _replace_projection_claim(projection, 0, discomfort),
                grounded_graph=graph,
                parent_plan=parent_plan,
            )

    def test_stage3_intensity_is_decoupled_from_depth_strength_and_temperature(self) -> None:
        case_id, memo, category, emotion, _strength = EXACT8[7]

        def build(strength: str, suffix: str):
            source, grounded_plan, graph, parent_plan = _stage2_inputs(
                _request(
                    record_id=f"{case_id}-{suffix}",
                    memo=memo,
                    category=category,
                    emotion=emotion,
                    strength=strength,
                )
            )
            return build_stage1_semantic_projection(
                source=source,
                grounded_graph=graph,
                parent_plan=parent_plan,
                grounded_plan=grounded_plan,
            )

        weak = build("weak", "weak")
        strong = build("strong", "strong")
        weak_affect = next(
            row
            for row in weak.subjective_claims
            if row.subjective_mode is SubjectiveMode.AFFECTIVE_RESPONSE
        )
        strong_affect = next(
            row
            for row in strong.subjective_claims
            if row.subjective_mode is SubjectiveMode.AFFECTIVE_RESPONSE
        )
        self.assertIs(
            weak_affect.asserted_subjective_proposition.affect_intensity,
            AffectIntensity.MODERATE,
        )
        self.assertEqual(
            weak_affect.asserted_subjective_proposition.affect_intensity,
            strong_affect.asserted_subjective_proposition.affect_intensity,
        )
        self.assertEqual(weak.temperature_class, strong.temperature_class)
        self.assertEqual(weak.subjective_depth_class, strong.subjective_depth_class)

        contribution_by_id = {
            row.contribution_id: row for row in weak.observation_contributions
        }
        targets = tuple(
            contribution_by_id[ref]
            for ref in weak_affect.asserted_subjective_proposition.target_contribution_refs
        )
        self.assertIs(
            classify_affect_intensity(
                AffectCategory.CONCERN,
                targets,
                reception_style_policy_ref=weak.reception_style_policy_ref,
                relationship_care_constraints=(),
            ),
            AffectIntensity.QUIET,
        )
        self.assertIs(
            classify_affect_intensity(
                AffectCategory.JOY,
                (replace(targets[0], retention="OPTIONAL"),),
                reception_style_policy_ref=weak.reception_style_policy_ref,
                relationship_care_constraints=(),
            ),
            AffectIntensity.QUIET,
        )
        quiet_style = next(
            row.distance_policy_ref
            for row in CMEE_STAGE1_RECEPTION_STANCE_MAPPING_EXACT5
            if row.stance == "quiet_presence"
        )
        self.assertIs(
            classify_affect_intensity(
                AffectCategory.JOY,
                targets,
                reception_style_policy_ref=quiet_style,
                relationship_care_constraints=(),
            ),
            AffectIntensity.QUIET,
        )
        self.assertIs(
            classify_affect_intensity(
                AffectCategory.JOY,
                targets,
                reception_style_policy_ref=weak.reception_style_policy_ref,
                relationship_care_constraints=(
                    "felt_state_is_real",
                    "identity_claim_is_not_accepted",
                ),
            ),
            AffectIntensity.QUIET,
        )

    def test_stage3_depth_uses_distinct_claims_not_legacy_reception_depth(self) -> None:
        source, grounded_plan, graph, parent_plan = _stage2_inputs(
            _request(
                record_id="stage3-bounded-depth",
                memo="自分が悪いから、助けを求めてはいけない。",
                category="生活",
                emotion="悲しみ",
                strength="strong",
            )
        )
        projection = build_stage1_semantic_projection(
            source=source,
            grounded_graph=graph,
            parent_plan=parent_plan,
            grounded_plan=grounded_plan,
        )
        self.assertEqual(len(projection.subjective_claims), 4)
        self.assertIs(
            classify_subjective_depth(projection.subjective_claims[:1]),
            SubjectiveDepthClass.FOCUSED,
        )
        self.assertIs(
            classify_subjective_depth(projection.subjective_claims[:2]),
            SubjectiveDepthClass.LAYERED,
        )
        self.assertIs(
            classify_subjective_depth(projection.subjective_claims[:3]),
            SubjectiveDepthClass.LAYERED,
        )
        self.assertIs(
            classify_subjective_depth(projection.subjective_claims),
            SubjectiveDepthClass.DENSE,
        )
        reception_plan = stage1_response_module._semantic_reception_asset(
            source=source,
            grounded_plan=grounded_plan,
        )
        self.assertNotEqual(
            reception_plan.depth_policy.level.upper(),
            projection.subjective_depth_class.value,
        )

    def test_stage3_value_visibility_is_material_and_other_values_stay_suppressed(self) -> None:
        source, grounded_plan, graph, parent_plan = _stage2_inputs(
            _request(
                record_id="stage3-bounded-values",
                memo="自分が悪いから、助けを求めてはいけない。",
                category="生活",
                emotion="悲しみ",
                strength="strong",
            )
        )
        bounded = build_stage1_semantic_projection(
            source=source,
            grounded_graph=graph,
            parent_plan=parent_plan,
            grounded_plan=grounded_plan,
        )
        counter = next(
            row
            for row in bounded.subjective_claims
            if row.subjective_mode is SubjectiveMode.BOUNDED_COUNTERPOSITION
        )
        self.assertEqual(
            counter.value_principle_refs,
            (
                stage1_value_principle_ref("V1"),
                stage1_value_principle_ref("V8"),
            ),
        )
        self.assertTrue(
            all(
                not row.value_principle_refs
                for row in bounded.subjective_claims
                if row is not counter
            )
        )
        counter_index = bounded.subjective_claims.index(counter)
        unpaired_counter = replace(
            counter,
            asserted_subjective_proposition=replace(
                counter.asserted_subjective_proposition,
                counterposition_target_ref=(
                    counter.asserted_subjective_proposition.target_contribution_refs[0]
                ),
            ),
        )
        with self.assertRaisesRegex(
            CMEEStage1ContractError,
            "stage1_subjective_object_contract_invalid",
        ):
            validate_stage1_projection(
                _replace_projection_claim(
                    bounded,
                    counter_index,
                    unpaired_counter,
                ),
                grounded_graph=graph,
                parent_plan=parent_plan,
            )
        base_contribution = bounded.observation_contributions[0]
        suppression_rows = (
            replace(
                base_contribution,
                contribution_kind=ObservationContributionKind.OBSERVE_BURDEN,
                semantic_operator=SemanticOperator.PRESENT_BURDEN,
                relation_operator=RelationOperator.NO_RELATION_CLAIM,
            ),
            replace(
                base_contribution,
                contribution_kind=ObservationContributionKind.OBSERVE_DIRECTION,
                semantic_operator=SemanticOperator.PRESENT_DIRECTION,
                relation_operator=RelationOperator.NO_RELATION_CLAIM,
            ),
            replace(
                base_contribution,
                contribution_kind=ObservationContributionKind.OBSERVE_CHANGE,
                semantic_operator=SemanticOperator.PRESENT_CHANGE,
                relation_operator=RelationOperator.NO_RELATION_CLAIM,
            ),
            replace(
                base_contribution,
                contribution_kind=ObservationContributionKind.OBSERVE_COEXISTENCE,
                semantic_operator=SemanticOperator.SYNTHESIZE_RELATION,
                relation_operator=RelationOperator.COEXISTS_WITH,
            ),
            replace(
                base_contribution,
                contribution_kind=ObservationContributionKind.PRESERVE_UNFINISHED,
                semantic_operator=SemanticOperator.PRESENT_UNFINISHED,
                relation_operator=RelationOperator.NO_RELATION_CLAIM,
            ),
        )
        self.assertEqual(
            tuple(
                row.removeprefix("value-policy-suppression:")
                for row in stage1_subjective_forbidden_promotions(
                    suppression_rows
                )
                if row.startswith("value-policy-suppression:")
            ),
            tuple(f"V{index}" for index in range(1, 10)),
        )
        unknown_suppression = stage1_subjective_forbidden_promotions(
            (base_contribution,),
            material_unknown_refs=(
                "unknown:material-1@cocolon.cmee.obligation.v1",
            ),
        )
        self.assertIn("value-policy-suppression:V9", unknown_suppression)
        self.assertNotIn("value-policy-suppression:V3", unknown_suppression)
        self.assertNotIn("value-policy-suppression:V7", unknown_suppression)

        case_id, memo, category, emotion, strength = EXACT8[7]
        source, grounded_plan, graph, parent_plan = _stage2_inputs(
            _request(
                record_id=case_id,
                memo=memo,
                category=category,
                emotion=emotion,
                strength=strength,
            )
        )
        change = build_stage1_semantic_projection(
            source=source,
            grounded_graph=graph,
            parent_plan=parent_plan,
            grounded_plan=grounded_plan,
        )
        self.assertTrue(
            all(not row.value_principle_refs for row in change.subjective_claims)
        )
        self.assertTrue(
            all(
                {
                    "value-policy-suppression:V4",
                    "value-policy-suppression:V5",
                }.issubset(row.forbidden_promotions)
                for row in change.subjective_claims
            )
        )

        case_id, memo, category, emotion, strength = EXACT8[0]
        source, grounded_plan, graph, parent_plan = _stage2_inputs(
            _request(
                record_id=case_id,
                memo=memo,
                category=category,
                emotion=emotion,
                strength=strength,
            )
        )
        protect = build_stage1_semantic_projection(
            source=source,
            grounded_graph=graph,
            parent_plan=parent_plan,
            grounded_plan=grounded_plan,
        )
        attention = protect.subjective_claims[0]
        nonmaterial = replace(
            attention,
            subjective_mode=SubjectiveMode.VALUE_POSITION,
            asserted_subjective_proposition=replace(
                attention.asserted_subjective_proposition,
                subjective_operator=SubjectiveOperator.PROTECT_VALUE_BOUNDARY,
            ),
            value_principle_refs=(stage1_value_principle_ref("V1"),),
        )
        with self.assertRaisesRegex(
            CMEEStage1ContractError,
            "stage1_nonmaterial_value_visible",
        ):
            validate_stage1_projection(
                _replace_projection_claim(protect, 0, nonmaterial),
                grounded_graph=graph,
                parent_plan=parent_plan,
            )

        case_id, memo, category, emotion, strength = EXACT8[5]
        source, grounded_plan, graph, parent_plan = _stage2_inputs(
            _request(
                record_id=case_id,
                memo=memo,
                category=category,
                emotion=emotion,
                strength=strength,
            )
        )
        material_protect = build_stage1_semantic_projection(
            source=source,
            grounded_graph=graph,
            parent_plan=parent_plan,
            grounded_plan=grounded_plan,
        )
        value_position = next(
            row
            for row in material_protect.subjective_claims
            if row.subjective_mode is SubjectiveMode.VALUE_POSITION
        )
        self.assertEqual(
            value_position.value_principle_refs,
            (
                stage1_value_principle_ref("V2"),
                stage1_value_principle_ref("V8"),
            ),
        )
        burden_contribution = next(
            row
            for row in material_protect.observation_contributions
            if row.semantic_operator is SemanticOperator.PRESENT_BURDEN
        )
        attention = next(
            row
            for row in material_protect.subjective_claims
            if row.subjective_mode is SubjectiveMode.ATTENTION
        )
        redirected = replace(
            attention,
            asserted_subjective_proposition=replace(
                attention.asserted_subjective_proposition,
                target_contribution_refs=(burden_contribution.contribution_id,),
                response_object_refs=(burden_contribution.semantic_refs[0],),
            ),
        )
        with self.assertRaisesRegex(
            CMEEStage1ContractError,
            "stage1_subjective_object_contract_invalid",
        ):
            validate_stage1_projection(
                _replace_projection_claim(material_protect, 0, redirected),
                grounded_graph=graph,
                parent_plan=parent_plan,
            )

    def test_stage3_request_local_self_state_is_exact_four_and_a_b_a_stable(self) -> None:
        def build(index: int):
            case_id, memo, category, emotion, strength = EXACT8[index]
            source, grounded_plan, graph, parent_plan = _stage2_inputs(
                _request(
                    record_id=case_id,
                    memo=memo,
                    category=category,
                    emotion=emotion,
                    strength=strength,
                )
            )
            return build_stage1_semantic_projection(
                source=source,
                grounded_graph=graph,
                parent_plan=parent_plan,
                grounded_plan=grounded_plan,
            )

        first_a = build(1)
        state = stage1_response_module._build_request_local_response_state(
            first_a.observation_contributions,
            relationship_care_constraints=(),
        )
        self.assertEqual(
            tuple(row.name for row in fields(type(state))),
            (
                "speaker_identity",
                "versioned_value_policy",
                "selected_observation_contribution_refs",
                "relationship_care_constraints",
            ),
        )
        self.assertEqual(state.speaker_identity, "EMLIS")
        self.assertEqual(state.versioned_value_policy, CMEE_STAGE1_VALUE_POLICY_REF)
        middle_b = build(7)
        second_a = build(1)
        self.assertNotEqual(first_a.projection_id, middle_b.projection_id)
        self.assertEqual(first_a, second_a)

    def test_stage3_policy_projection_and_artifact_identity_are_bound(self) -> None:
        case_id, memo, category, emotion, strength = EXACT8[1]
        source, grounded_plan, graph, parent_plan = _stage2_inputs(
            _request(
                record_id=case_id,
                memo=memo,
                category=category,
                emotion=emotion,
                strength=strength,
            )
        )
        projection = build_stage1_semantic_projection(
            source=source,
            grounded_graph=graph,
            parent_plan=parent_plan,
            grounded_plan=grounded_plan,
        )
        projection_ref = stage1_projection_artifact_ref(projection)
        args = (
            "source-envelope",
            "graph",
            "plan",
            "proof",
            "observation",
            ("unknown",),
            "reception",
        )
        legacy = _artifact_id(*args)
        self.assertEqual(
            legacy,
            _artifact_id(*args, emlis_stage1_projection_ref=None),
        )
        bound = _artifact_id(
            *args,
            emlis_stage1_projection_ref=projection_ref,
        )
        self.assertNotEqual(legacy, bound)

        altered = _identified(
            replace(
                projection,
                projection_id="",
                emlis_value_policy_ref=(
                    "policy:cocolon.emlis.stage1.value_policy"
                    "@cocolon.emlis.stage1.value_policy.v2"
                ),
            ),
            "projection_id",
        )
        altered_ref = stage1_projection_artifact_ref(altered)
        self.assertNotEqual(projection_ref, altered_ref)
        self.assertNotEqual(
            bound,
            _artifact_id(
                *args,
                emlis_stage1_projection_ref=altered_ref,
            ),
        )
        with self.assertRaisesRegex(
            CMEEStage1ContractError,
            "stage1_value_policy_ref_invalid",
        ):
            validate_stage1_projection(
                altered,
                grounded_graph=graph,
                parent_plan=parent_plan,
            )
        with self.assertRaisesRegex(
            CMEEVerticalError,
            "stage1_projection_artifact_ref_invalid",
        ):
            _artifact_id(
                *args,
                emlis_stage1_projection_ref="projection:not-local@wrong.v1",
            )
        self.assertIsNone(
            inspect.signature(_artifact_id)
            .parameters["emlis_stage1_projection_ref"]
            .default
        )

    def test_stage4_microgrammar_inventory_tuple_and_docs_bytes_are_exact(self) -> None:
        self.assertEqual(
            CMEE_STAGE1_MICROGRAMMAR_POLICY_VERSION,
            "cocolon.emlis.stage1.microgrammar.v2",
        )
        self.assertEqual(
            CMEE_STAGE1_MICROGRAMMAR_INVENTORY_DOCS_BYTES,
            stage1_canonical_json_bytes(
                CMEE_STAGE1_MICROGRAMMAR_INVENTORY_TUPLE
            ),
        )
        self.assertEqual(len(CMEE_STAGE1_MICROGRAMMAR_INVENTORY_DOCS_BYTES), 16695)
        self.assertEqual(
            CMEE_STAGE1_MICROGRAMMAR_INVENTORY_DOCS_SHA256,
            "dc4e1e5ef8026d5577698f375e305db7886f57096c69e6e6a0b99bfe1f26de8a",
        )
        self.assertEqual(
            hashlib.sha256(
                CMEE_STAGE1_MICROGRAMMAR_INVENTORY_DOCS_BYTES
            ).hexdigest(),
            CMEE_STAGE1_MICROGRAMMAR_INVENTORY_DOCS_SHA256,
        )
        sections = dict(CMEE_STAGE1_MICROGRAMMAR_INVENTORY_TUPLE)
        self.assertEqual(len(CMEE_STAGE1_MICROGRAMMAR_INVENTORY_TUPLE), 44)
        self.assertNotIn("shared_relation_endpoint_heads", sections)
        self.assertEqual(sections["policy_ref"], CMEE_STAGE1_MICROGRAMMAR_POLICY_REF)
        self.assertEqual(len(sections["observation_operator_rows"]), 12)
        self.assertEqual(len(sections["subjective_operator_rows"]), 14)
        self.assertEqual(len(sections["connective_families"]), 9)
        self.assertEqual(
            dict(sections["layer2_explicit_nominalizers"])[
                "PRESENT_DIRECTION:*"
            ],
            "という方向",
        )
        self.assertEqual(
            dict(sections["layer2_explicit_nominalizers"])[
                "PRESENT_DIRECTION:wish"
            ],
            "という願い",
        )
        self.assertEqual(
            dict(sections["direction_under_burden_surface"])["predicate"],
            "続いています",
        )
        epistemic_surface = dict(sections["epistemic_burden_surface"])
        self.assertEqual(epistemic_surface, {"question_link": "という"})
        self.assertNotIn("context_link", epistemic_surface)
        self.assertNotIn("における", epistemic_surface.values())
        quote_policy = dict(sections["quote_policy"])
        self.assertEqual(quote_policy["l1_max_per_sentence"], 2)
        self.assertEqual(quote_policy["l2_max_per_sentence"], 1)
        self.assertEqual(quote_policy["l1_max_graphemes"], 16)
        self.assertEqual(quote_policy["l2_max_graphemes"], 16)
        self.assertIs(quote_policy["full_replay"], False)
        self.assertEqual(dict(sections["variant_policy"])["max_candidates"], 2)
        self.assertEqual(dict(sections["variant_policy"])["automatic_retry"], 0)
        self.assertEqual(dict(sections["s9_selection_policy"])["new_generation"], 0)
        self.assertEqual(
            dict(sections["role_anchor_policy"])["over_limit_selection"],
            "semantic_boundary_or_stop",
        )
        attention_rows = dict(sections["attention_surface_rows"])
        attention_predicates = {
            predicate
            for variants in attention_rows.values()
            for _particle, predicate in variants
        }
        concern_row = next(
            row
            for row in sections["subjective_operator_rows"]
            if row[:2] == ("FEEL_TOWARD", "CONCERN")
        )
        concern_predicates = {token for token in concern_row[3:] if token}
        self.assertTrue(attention_predicates)
        self.assertTrue(concern_predicates)
        self.assertTrue(attention_predicates.isdisjoint(concern_predicates))
        self.assertTrue(
            all(
                len(variants) == 2
                and len(set(variants)) == 2
                and all(particle and predicate for particle, predicate in variants)
                for variants in attention_rows.values()
            )
        )
        self.assertEqual(
            dict(sections["structural_tokens"])["topic_particle"],
            "は",
        )
        self.assertEqual(
            dict(sections["structural_tokens"])["separator"],
            "、",
        )
        stage1_response_module._validate_microgrammar_inventory()
        tampered_role_policy = dict(stage1_response_module._ROLE_ANCHOR_POLICY)
        tampered_role_policy["over_limit_selection"] = "rightmost_grapheme_window"
        for attribute, tampered in (
            ("_ROLE_ANCHOR_POLICY", tampered_role_policy),
            ("CMEE_STAGE1_MICROGRAMMAR_INVENTORY_DOCS_SHA256", "0" * 64),
        ):
            with self.subTest(tampered_inventory_owner=attribute):
                with (
                    patch.object(stage1_response_module, attribute, tampered),
                    self.assertRaisesRegex(
                        CMEEStage1ContractError,
                        "stage1_microgrammar_inventory_invalid",
                    ),
                ):
                    stage1_response_module._validate_microgrammar_inventory()

        def recursively_immutable(value: object) -> bool:
            if type(value) is tuple:
                return all(recursively_immutable(row) for row in value)
            return value is None or type(value) in {str, int, bool}

        self.assertTrue(
            recursively_immutable(CMEE_STAGE1_MICROGRAMMAR_INVENTORY_TUPLE)
        )

    def test_stage4_registered_source_shape_parsers_are_exact_and_fail_closed(
        self,
    ) -> None:
        def nucleus(
            *,
            kind: str,
            modality: str,
            attributes: tuple[str, ...] = (),
        ) -> SimpleNamespace:
            return SimpleNamespace(
                kind=kind,
                semantic_frame=SimpleNamespace(
                    modality=modality,
                    attribute_codes=attributes,
                ),
            )

        direction = nucleus(kind="wish", modality="wish")
        burden = nucleus(kind="state", modality="feeling")
        positive_change = nucleus(
            kind="state",
            modality="fact",
            attributes=("operator:positive_change",),
        )
        allow_rows = (
            (
                "direct_contrast",
                lambda value: emlis_v1a_module._cmee_parse_direct_contrast_shape(
                    direction,
                    value,
                ),
                "続けたいけど不安",
                (("続けたい", "direction"), ("不安", "burden")),
            ),
            (
                "context_direction_residue",
                emlis_v1a_module._cmee_parse_context_direction_residue_shape,
                "仕事のあと、続けたい気持ちと不安が残っている",
                ("仕事の", "続けたい", "不安"),
            ),
            (
                "open_question",
                emlis_v1a_module._cmee_parse_open_question_shape,
                "不安で、どうしたらいいのか考えている",
                ("不安", "どうしたらいいのか"),
            ),
            (
                "compound_burden",
                emlis_v1a_module._cmee_parse_compound_burden_shape,
                "仕事が続いて疲れていて、何も手につかない",
                ("仕事", "疲れて", "何も手につかない"),
            ),
            (
                "action_change",
                emlis_v1a_module._cmee_parse_action_change_shape,
                "疲れたけど散歩したら落ち着いた",
                ("疲れた", "散歩した", "落ち着いた"),
            ),
            (
                "simple_positive_change",
                emlis_v1a_module._cmee_parse_simple_change_shape,
                "散歩して気分が軽かった",
                ("散歩し", "散歩した", "気分が軽かった"),
            ),
            (
                "body_adjective",
                stage1_response_module._source_body_burden_parts,
                "体がだるい",
                ("body_adjective", "体", "だるい"),
            ),
            (
                "body_weight",
                stage1_response_module._source_body_burden_parts,
                "体が重く感じる",
                ("body_weight", "体", "重く感じる"),
            ),
            (
                "context_de_epistemic_burden",
                stage1_response_module._source_context_de_epistemic_burden_parts,
                "この職場でやっていけるか不安",
                ("この職場でやっていけるか", "不安"),
            ),
            (
                "bounded_self_denial",
                stage1_response_module._source_bounded_self_denial_parts,
                "自分が悪いから、助けを求めてはいけない",
                ("自分が悪いから", "助けを求めてはいけない"),
            ),
        )
        for name, parser, value, expected in allow_rows:
            with self.subTest(registered_shape=name, disposition="allow"):
                self.assertEqual(parser(value), expected)

        near_miss_rows = (
            (
                "direct_contrast",
                lambda value: emlis_v1a_module._cmee_parse_direct_contrast_shape(
                    direction,
                    value,
                ),
                "続けたいけど晴れている",
            ),
            (
                "context_direction_residue",
                emlis_v1a_module._cmee_parse_context_direction_residue_shape,
                "仕事のあと、続けたい気持ちと不安が消えている",
            ),
            (
                "open_question",
                emlis_v1a_module._cmee_parse_open_question_shape,
                "不安で、どうしたらいいか考えている",
            ),
            (
                "compound_burden",
                emlis_v1a_module._cmee_parse_compound_burden_shape,
                "仕事が続いて笑っていて、元気",
            ),
            (
                "action_change",
                emlis_v1a_module._cmee_parse_action_change_shape,
                "疲れたけど散歩なら落ち着いた",
            ),
            (
                "simple_positive_change",
                emlis_v1a_module._cmee_parse_simple_change_shape,
                "散歩したくて気分が軽かった",
            ),
            (
                "body_burden",
                stage1_response_module._source_body_burden_parts,
                "体がだるかった",
            ),
            (
                "context_de_epistemic_burden",
                stage1_response_module._source_context_de_epistemic_burden_parts,
                "この職場でやっていけるか迷う",
            ),
            (
                "bounded_self_denial",
                stage1_response_module._source_bounded_self_denial_parts,
                "自分が悪いので、助けを求めてはいけない",
            ),
        )
        for name, parser, value in near_miss_rows:
            with self.subTest(registered_shape=name, disposition="near_miss"):
                self.assertIsNone(parser(value))

        malformed_rows = (
            (
                "conditional_nara",
                positive_change,
                "疲れたけど散歩なら落ち着いた",
            ),
            (
                "hypothetical_result",
                positive_change,
                "疲れたけど散歩したら落ち着くかもしれない",
            ),
            (
                "typed_other_missing",
                direction,
                "続けたいけど晴れている",
            ),
            (
                "compound_burden_role_missing",
                burden,
                "仕事が続いて笑っていて、元気",
            ),
            (
                "ambiguous_te_inflection",
                positive_change,
                "散歩したくて気分が軽かった",
            ),
        )
        for name, typed_nucleus, value in malformed_rows:
            with self.subTest(source_shape=name):
                with self.assertRaisesRegex(
                    CMEEVerticalError,
                    "stage1_source_shape_malformed",
                ):
                    emlis_v1a_module._cmee_validate_typed_source_shape(
                        typed_nucleus,
                        value,
                    )

        with self.assertRaisesRegex(
            CMEEVerticalError,
            "stage1_source_shape_ambiguous",
        ):
            emlis_v1a_module._cmee_validate_typed_source_shape(
                positive_change,
                "疲れたけど散歩したら落ち着いて良かった",
            )

        valid_fragment_anchor = "前と後"
        self.assertEqual(
            emlis_v1a_module._cmee_valid_source_fragment_rows(
                valid_fragment_anchor,
                (("前", 0, 1), ("後", 2, 3)),
            ),
            ("前", "後"),
        )
        too_long = "あ" * (emlis_v1a_module._CMEE_SOURCE_FRAGMENT_MAX + 1)
        rejected_fragment_rows = (
            (
                "duplicate",
                "疲れ疲れ",
                (("疲れ", 0, 2), ("疲れ", 2, 4)),
            ),
            (
                "source_order",
                "前と後",
                (("後", 2, 3), ("前", 0, 1)),
            ),
            (
                "over_limit",
                too_long,
                ((too_long, 0, len(too_long)),),
            ),
        )
        for name, anchor, rows in rejected_fragment_rows:
            with self.subTest(source_fragment=name):
                self.assertIsNone(
                    emlis_v1a_module._cmee_valid_source_fragment_rows(
                        anchor,
                        rows,
                    )
                )

    def test_stage4_exact8_candidate_sets_are_deterministic_same_projection_max2(self) -> None:
        for index, (case_id, _memo, _category, _emotion, _strength) in enumerate(
            EXACT8
        ):
            with self.subTest(case_id=case_id):
                _source, _plan, graph, parent, projection, first = (
                    _stage4_exact8_fixture(index)
                )
                second = build_stage1_realization_candidate_set(
                    projection=projection,
                    grounded_graph=graph,
                    parent_plan=parent,
                )
                self.assertEqual(first, second)
                self.assertIs(type(first), RealizationCandidateSet)
                self.assertEqual(first.projection_ref, projection.projection_id)
                self.assertEqual(len(first.candidates), 2)
                self.assertEqual(
                    tuple(candidate[0].composition_variant_id for candidate in first.candidates),
                    ("01-primary.v2", "02-alternate.v2"),
                )
                expected_count = len(projection.ordered_observation_refs) + len(
                    projection.ordered_subjective_refs
                )
                self.assertTrue(
                    all(len(candidate) == expected_count for candidate in first.candidates)
                )
                self.assertTrue(
                    all(
                        unit.projection_ref == projection.projection_id
                        for candidate in first.candidates
                        for unit in candidate
                    )
                )
                selected = select_stage1_realization_candidate(
                    first,
                    projection=projection,
                    grounded_graph=graph,
                    parent_plan=parent,
                )
                self.assertEqual(selected[0].composition_variant_id, "01-primary.v2")
                layer2 = tuple(unit for unit in selected if unit.layer == "LAYER_2")
                self.assertTrue(layer2)
                self.assertIn(
                    "reference_mode:anaphoric_first",
                    layer2[0].clause_frames[0].qualifier_refs,
                )
                for later in layer2[1:]:
                    self.assertIn(
                        "reference_mode:anaphoric_first",
                        later.clause_frames[0].qualifier_refs,
                    )

    def test_stage4_utterance_state_exact14_typed_atomic_transition(self) -> None:
        _source, _plan, _graph, _parent, projection, candidate_set = (
            _stage4_exact8_fixture(0)
        )
        candidate = candidate_set.candidates[0]
        state = initialize_emlis_utterance_state(
            projection,
            composition_variant_id="01-primary.v2",
        )
        self.assertEqual(
            tuple(row.name for row in fields(EmlisUtteranceState)),
            (
                "phase",
                "realized_observation_contribution_refs",
                "remaining_required_observation_refs",
                "suppressed_observation_candidate_refs",
                "realized_subjective_claim_refs",
                "remaining_required_subjective_refs",
                "suppressed_subjective_claim_refs",
                "last_focus_refs",
                "last_move_kind",
                "realized_semantic_keys",
                "normalized_surface_digests",
                "layer_sentence_counts",
                "composition_variant_id",
                "stop_reason",
            ),
        )
        self.assertIs(state.phase, UtterancePhase.L1_ACTIVE)
        self.assertEqual(
            tuple(state.remaining_required_observation_refs),
            projection.ordered_observation_refs,
        )
        initial = replace(
            state,
            realized_observation_contribution_refs=list(
                state.realized_observation_contribution_refs
            ),
            remaining_required_observation_refs=list(
                state.remaining_required_observation_refs
            ),
            suppressed_observation_candidate_refs=list(
                state.suppressed_observation_candidate_refs
            ),
            realized_subjective_claim_refs=list(state.realized_subjective_claim_refs),
            remaining_required_subjective_refs=list(
                state.remaining_required_subjective_refs
            ),
            suppressed_subjective_claim_refs=list(
                state.suppressed_subjective_claim_refs
            ),
            last_focus_refs=list(state.last_focus_refs),
            realized_semantic_keys=list(state.realized_semantic_keys),
            normalized_surface_digests=list(state.normalized_surface_digests),
            layer_sentence_counts=dict(state.layer_sentence_counts),
        )
        first_advanced = stage1_response_module._accept_sentence(
            state, candidate[0], projection
        )
        self.assertEqual(state, initial)
        self.assertIsNot(first_advanced, state)
        self.assertEqual(len(first_advanced.realized_observation_contribution_refs), 1)
        self.assertFalse(first_advanced.realized_subjective_claim_refs)
        snapshot = replace(
            first_advanced,
            realized_observation_contribution_refs=list(
                first_advanced.realized_observation_contribution_refs
            ),
            remaining_required_observation_refs=list(
                first_advanced.remaining_required_observation_refs
            ),
            suppressed_observation_candidate_refs=list(
                first_advanced.suppressed_observation_candidate_refs
            ),
            realized_subjective_claim_refs=list(
                first_advanced.realized_subjective_claim_refs
            ),
            remaining_required_subjective_refs=list(
                first_advanced.remaining_required_subjective_refs
            ),
            suppressed_subjective_claim_refs=list(
                first_advanced.suppressed_subjective_claim_refs
            ),
            last_focus_refs=list(first_advanced.last_focus_refs),
            realized_semantic_keys=list(first_advanced.realized_semantic_keys),
            normalized_surface_digests=list(
                first_advanced.normalized_surface_digests
            ),
            layer_sentence_counts=dict(first_advanced.layer_sentence_counts),
        )
        with self.assertRaises(CMEEStage1ContractError):
            stage1_response_module._accept_sentence(
                first_advanced, candidate[0], projection
            )
        self.assertEqual(first_advanced, snapshot)

        state = first_advanced
        observation_count = len(projection.ordered_observation_refs)
        for unit in candidate[1:observation_count]:
            state = stage1_response_module._accept_sentence(state, unit, projection)
        self.assertIs(state.phase, UtterancePhase.L1_COMPLETE)
        state = stage1_response_module._begin_layer2(state, projection)
        self.assertIs(state.phase, UtterancePhase.L2_ACTIVE)
        for unit in candidate[observation_count:]:
            state = stage1_response_module._accept_sentence(state, unit, projection)
        self.assertIs(state.phase, UtterancePhase.CANDIDATE_COMPLETE)
        state = stage1_response_module._ready_for_s9(state, projection)
        self.assertIs(state.phase, UtterancePhase.READY_FOR_S9)
        self.assertFalse(state.remaining_required_observation_refs)
        self.assertFalse(state.remaining_required_subjective_refs)
        candidate_ids = {row.candidate_id for row in projection.interpretation_candidates}
        contribution_ids = {
            row.contribution_id for row in projection.observation_contributions
        }
        self.assertTrue(
            set(state.suppressed_observation_candidate_refs).issubset(candidate_ids)
        )
        self.assertFalse(
            set(state.suppressed_observation_candidate_refs) & contribution_ids
        )
        self.assertNotIn(
            "state",
            {row.name for row in fields(RealizationCandidateSet)},
        )

    def test_stage4_full_coverage_repetition_and_span_binding_exact8(self) -> None:
        for index, (case_id, _memo, _category, _emotion, _strength) in enumerate(
            EXACT8
        ):
            with self.subTest(case_id=case_id):
                _source, _plan, graph, parent, projection, candidate_set = (
                    _stage4_exact8_fixture(index)
                )
                expected_anchors = (
                    *projection.ordered_observation_refs,
                    *projection.ordered_subjective_refs,
                )
                for candidate in candidate_set.candidates:
                    self.assertEqual(
                        tuple(unit.basis_anchor_refs[0] for unit in candidate),
                        expected_anchors,
                    )
                    normalized = tuple(
                        stage1_response_module._normalized_surface_digest(unit.text)
                        for unit in candidate
                    )
                    self.assertEqual(len(normalized), len(set(normalized)))
                    prior_ids: list[str] = []
                    for unit in candidate:
                        validate_stage1_sentence_unit(
                            unit,
                            projection,
                            grounded_graph=graph,
                            parent_plan=parent,
                            prior_unit_ids=tuple(prior_ids),
                        )
                        for binding in unit.realized_semantic_bindings:
                            span = unit.text[
                                binding.surface_scalar_start : binding.surface_scalar_end
                            ]
                            self.assertEqual(
                                hashlib.sha256(span.encode("utf-8")).hexdigest(),
                                binding.surface_span_sha256,
                            )
                        stage1_response_module._validate_surface_partition(unit)
                        prior_ids.append(unit.unit_id)
                select_stage1_realization_candidate(
                    candidate_set,
                    projection=projection,
                    grounded_graph=graph,
                    parent_plan=parent,
                )

    def test_stage4_s9_selects_existing_alternate_after_bound_span_defect(self) -> None:
        _source, _plan, graph, parent, projection, candidate_set = (
            _stage4_exact8_fixture(0)
        )

        def wrong_span(candidate: tuple[RealizedSentenceUnit, ...]):
            unit = candidate[0]
            original = unit.realized_semantic_bindings[0]
            target = unit.realized_semantic_bindings[-1]
            forged_binding = replace(
                original,
                semantic_ref=target.semantic_ref,
                clause_slot=target.clause_slot,
            )
            forged_unit = _identified(
                replace(
                    unit,
                    unit_id="",
                    realized_semantic_bindings=(
                        forged_binding,
                        *unit.realized_semantic_bindings[1:],
                    ),
                ),
                "unit_id",
            )
            return (forged_unit, *candidate[1:])

        primary_bad = wrong_span(candidate_set.candidates[0])
        one_bad = replace(
            candidate_set,
            candidates=(primary_bad, candidate_set.candidates[1]),
        )
        with patch.object(
            stage1_response_module,
            "_realize_stage1_variant",
            side_effect=AssertionError("S9 must not generate"),
        ) as realizer, patch.object(
            stage1_response_module,
            "_surface_parts",
            side_effect=AssertionError("S9 must not compose"),
        ) as composer, patch.object(
            stage1_response_module,
            "_observation_surface_shape",
            side_effect=AssertionError("S9 must not compose"),
        ) as observation_shape, patch.object(
            stage1_response_module,
            "_subjective_surface_shape",
            side_effect=AssertionError("S9 must not compose"),
        ) as subjective_shape:
            selected = select_stage1_realization_candidate(
                one_bad,
                projection=projection,
                grounded_graph=graph,
                parent_plan=parent,
            )
            self.assertEqual(selected[0].composition_variant_id, "02-alternate.v2")
            self.assertEqual(realizer.call_count, 0)
            self.assertEqual(composer.call_count, 0)
            self.assertEqual(observation_shape.call_count, 0)
            self.assertEqual(subjective_shape.call_count, 0)

            both_bad = replace(
                candidate_set,
                candidates=(primary_bad, wrong_span(candidate_set.candidates[1])),
            )
            with self.assertRaisesRegex(
                CMEEStage1ContractError,
                "stage1_no_hard_valid_realization",
            ):
                select_stage1_realization_candidate(
                    both_bad,
                    projection=projection,
                    grounded_graph=graph,
                    parent_plan=parent,
                )
            self.assertEqual(realizer.call_count, 0)
            self.assertEqual(composer.call_count, 0)
            self.assertEqual(observation_shape.call_count, 0)
            self.assertEqual(subjective_shape.call_count, 0)

    def test_stage4_candidate_set_bounds_projection_and_variant_fail_closed(self) -> None:
        _source, _plan, graph, parent, projection, candidate_set = (
            _stage4_exact8_fixture(1)
        )
        invalid_sets = (
            RealizationCandidateSet(projection.projection_id, ()),
            RealizationCandidateSet(
                projection.projection_id,
                (candidate_set.candidates[0],),
            ),
            RealizationCandidateSet(
                projection.projection_id,
                (
                    *candidate_set.candidates,
                    candidate_set.candidates[0],
                ),
            ),
            replace(candidate_set, projection_ref="projection-foreign"),
            replace(
                candidate_set,
                candidates=tuple(reversed(candidate_set.candidates)),
            ),
            RealizationCandidateSet(
                projection.projection_id,
                (("bad-member",), candidate_set.candidates[1]),
            ),
        )
        for invalid in invalid_sets:
            with self.subTest(invalid=invalid):
                with self.assertRaises(CMEEStage1ContractError):
                    select_stage1_realization_candidate(
                        invalid,
                        projection=projection,
                        grounded_graph=graph,
                        parent_plan=parent,
                    )

        first = candidate_set.candidates[0][0]
        foreign_unit = _identified(
            replace(first, unit_id="", projection_ref="projection-foreign"),
            "unit_id",
        )
        primary_bad = (
            foreign_unit,
            *candidate_set.candidates[0][1:],
        )
        selected = select_stage1_realization_candidate(
            replace(
                candidate_set,
                candidates=(primary_bad, candidate_set.candidates[1]),
            ),
            projection=projection,
            grounded_graph=graph,
            parent_plan=parent,
        )
        self.assertEqual(selected[0].composition_variant_id, "02-alternate.v2")

    def test_stage4_projection_defect_stops_before_any_surface_generation(self) -> None:
        _source, _plan, graph, parent, projection, _candidate_set = (
            _stage4_exact8_fixture(2)
        )
        invalid_projection = replace(
            projection,
            parent_observation_duty_ref="foreign-observation-duty",
        )
        with patch.object(
            stage1_response_module,
            "_realize_stage1_variant",
            side_effect=AssertionError("defect must stop before generation"),
        ) as realizer:
            with self.assertRaises(CMEEStage1ContractError):
                build_stage1_realization_candidate_set(
                    projection=invalid_projection,
                    grounded_graph=graph,
                    parent_plan=parent,
                )
            self.assertEqual(realizer.call_count, 0)

    def test_stage4_state_rejects_normalized_repetition_without_mutation(self) -> None:
        _source, _plan, _graph, _parent, projection, candidate_set = (
            _stage4_exact8_fixture(3)
        )
        candidate = candidate_set.candidates[0]
        state = initialize_emlis_utterance_state(
            projection,
            composition_variant_id="01-primary.v2",
        )
        state = stage1_response_module._accept_sentence(
            state, candidate[0], projection
        )
        repeated = _identified(
            replace(candidate[1], unit_id="", text=candidate[0].text),
            "unit_id",
        )
        snapshot = tuple(state.normalized_surface_digests)
        with self.assertRaisesRegex(
            CMEEStage1ContractError,
            "stage1_realization_surface_repetition",
        ):
            stage1_response_module._accept_sentence(state, repeated, projection)
        self.assertEqual(tuple(state.normalized_surface_digests), snapshot)

    def test_stage4_alternate_changes_exactly_one_predeclared_surface_slot(self) -> None:
        _source, _plan, graph, parent, projection, candidate_set = (
            _stage4_exact8_fixture(6)
        )
        primary, alternate = candidate_set.candidates
        self.assertEqual(
            tuple(unit.basis_anchor_refs for unit in primary),
            tuple(unit.basis_anchor_refs for unit in alternate),
        )
        self.assertEqual(
            tuple(unit.move_ref for unit in primary),
            tuple(unit.move_ref for unit in alternate),
        )
        self.assertEqual(
            sum(left.text != right.text for left, right in zip(primary, alternate)),
            1,
        )
        selected = select_stage1_realization_candidate(
            candidate_set,
            projection=projection,
            grounded_graph=graph,
            parent_plan=parent,
        )
        self.assertIs(selected, primary)
        self.assertEqual(
            min(
                (primary, alternate),
                key=lambda row: row[0].composition_variant_id,
            ),
            primary,
        )

    def test_stage4_s8_attempts_all_predeclared_variants_after_local_defect(self) -> None:
        _source, _plan, graph, parent, projection, candidate_set = (
            _stage4_exact8_fixture(0)
        )
        alternate = candidate_set.candidates[1]
        with patch.object(
            stage1_response_module,
            "_realize_stage1_variant",
            side_effect=(
                CMEEStage1ContractError("stage1_realization_surface_repetition"),
                alternate,
            ),
        ) as realizer:
            rebuilt = build_stage1_realization_candidate_set(
                projection=projection,
                grounded_graph=graph,
                parent_plan=parent,
            )
        self.assertEqual(realizer.call_count, 2)
        self.assertEqual(rebuilt.candidates, ((), alternate))
        selected = select_stage1_realization_candidate(
            rebuilt,
            projection=projection,
            grounded_graph=graph,
            parent_plan=parent,
        )
        self.assertEqual(selected[0].composition_variant_id, "02-alternate.v2")

    def test_stage4_state_phase_foreign_unit_stop_and_suppression_fail_closed(self) -> None:
        _source, _plan, _graph, _parent, projection, candidate_set = (
            _stage4_exact8_fixture(0)
        )
        initial = initialize_emlis_utterance_state(
            projection,
            composition_variant_id="01-primary.v2",
        )
        with self.assertRaisesRegex(
            CMEEStage1ContractError,
            "stage1_utterance_state_phase_invalid",
        ):
            stage1_response_module._validate_utterance_state(
                replace(initial, phase=UtterancePhase.READY_FOR_S9),
                projection,
            )
        stopped = stage1_response_module._mark_no_valid_surface(
            initial,
            projection,
            reason="stage1_surface_binding_unavailable",
        )
        self.assertIs(stopped.phase, UtterancePhase.NO_VALID_SURFACE)
        self.assertEqual(
            stopped.stop_reason,
            "stage1_surface_binding_unavailable",
        )

        first = candidate_set.candidates[0][0]
        foreign = _identified(
            replace(first, unit_id="", projection_ref="projection-foreign"),
            "unit_id",
        )
        with self.assertRaisesRegex(
            CMEEStage1ContractError,
            "stage1_utterance_state_unit_invalid",
        ):
            stage1_response_module._accept_sentence(initial, foreign, projection)
        self.assertFalse(initial.realized_observation_contribution_refs)

        selected_id = projection.observation_contributions[0].interpretation_candidate_refs[0]
        selected_candidate = next(
            row
            for row in projection.interpretation_candidates
            if row.candidate_id == selected_id
        )
        duplicate = replace(
            selected_candidate,
            candidate_id="interpretation-suppressed-local",
        )
        projection_with_duplicate = replace(
            projection,
            interpretation_candidates=(
                *projection.interpretation_candidates,
                duplicate,
            ),
        )
        duplicate_state = initialize_emlis_utterance_state(
            projection_with_duplicate,
            composition_variant_id="01-primary.v2",
        )
        advanced = stage1_response_module._accept_sentence(
            duplicate_state,
            first,
            projection_with_duplicate,
        )
        self.assertEqual(
            advanced.suppressed_observation_candidate_refs,
            ["interpretation-suppressed-local"],
        )

    def test_stage4_bounded_role_anchor_counter_and_connective_collision(self) -> None:
        multipart_fragment_sets: dict[str, set[str]] = {}
        inventory = dict(CMEE_STAGE1_MICROGRAMMAR_INVENTORY_TUPLE)
        quote_policy = dict(inventory["quote_policy"])
        structural_tokens = dict(inventory["structural_tokens"])
        quote_open = structural_tokens["quote_open"]
        quote_close = structural_tokens["quote_close"]
        forgery_seed = None
        for index in range(len(EXACT8)):
            _source, _plan, graph, _parent, _projection, candidate_set = (
                _stage4_exact8_fixture(index)
            )
            node_values = {
                f"node:{row.node_id}@{CMEE_GROUNDED_GRAPH_SCHEMA_VERSION}": row.value
                for row in graph.nodes
            }
            self.assertTrue(
                all(
                    len(row.value) <= 32
                    for row in graph.nodes
                    if row.grounding_kind in {"explicit", "user_stated_relation"}
                )
            )
            for candidate in candidate_set.candidates:
                for unit in candidate:
                    openings = tuple(
                        sorted(
                            (
                                row
                                for row in unit.realized_semantic_bindings
                                if row.clause_slot.endswith(":quote_open")
                            ),
                            key=lambda row: (
                                row.surface_scalar_start,
                                row.surface_scalar_end,
                            ),
                        )
                    )
                    closings = tuple(
                        sorted(
                            (
                                row
                                for row in unit.realized_semantic_bindings
                                if row.clause_slot.endswith(":quote_close")
                            ),
                            key=lambda row: (
                                row.surface_scalar_start,
                                row.surface_scalar_end,
                            ),
                        )
                    )
                    self.assertEqual(len(openings), len(closings))
                    self.assertEqual(unit.text.count(quote_open), len(openings))
                    self.assertEqual(unit.text.count(quote_close), len(closings))
                    layer_key = "l1" if unit.layer == "LAYER_1" else "l2"
                    max_pairs = int(quote_policy[f"{layer_key}_max_per_sentence"])
                    max_graphemes = int(quote_policy[f"{layer_key}_max_graphemes"])
                    self.assertLessEqual(len(openings), max_pairs)
                    previous_close_end = 0
                    for opening, closing in zip(openings, closings, strict=True):
                        self.assertEqual(opening.semantic_ref, closing.semantic_ref)
                        self.assertGreaterEqual(
                            opening.surface_scalar_start,
                            previous_close_end,
                        )
                        self.assertLessEqual(
                            opening.surface_scalar_end,
                            closing.surface_scalar_start,
                        )
                        self.assertEqual(
                            unit.text[
                                opening.surface_scalar_start :
                                opening.surface_scalar_end
                            ],
                            quote_open,
                        )
                        self.assertEqual(
                            unit.text[
                                closing.surface_scalar_start :
                                closing.surface_scalar_end
                            ],
                            quote_close,
                        )
                        anchor = unit.text[
                            opening.surface_scalar_end :
                            closing.surface_scalar_start
                        ]
                        self.assertTrue(anchor)
                        self.assertLessEqual(
                            len(stage1_response_module._grapheme_clusters(anchor)),
                            max_graphemes,
                        )
                        self.assertIn(opening.semantic_ref, node_values)
                        self.assertIn(anchor, node_values[opening.semantic_ref])
                        self.assertTrue(
                            any(
                                row.semantic_ref == opening.semantic_ref
                                and row.surface_scalar_start
                                == opening.surface_scalar_end
                                and row.surface_scalar_end
                                == closing.surface_scalar_start
                                for row in unit.realized_semantic_bindings
                            )
                        )
                        previous_close_end = closing.surface_scalar_end
                    if (
                        forgery_seed is None
                        and unit.layer == "LAYER_1"
                        and openings
                    ):
                        forgery_seed = (unit, graph, openings[0], closings[0])

                    for binding in unit.realized_semantic_bindings:
                        if binding.clause_slot.endswith(
                            (":quote_open", ":quote_close")
                        ) or not (
                            binding.clause_slot.endswith((":object", ":anchor"))
                            or ":argument:" in binding.clause_slot
                        ):
                            continue
                        span = unit.text[
                            binding.surface_scalar_start : binding.surface_scalar_end
                        ]
                        self.assertLessEqual(len(span), 16)
                        source_value = node_values[binding.semantic_ref]
                        self.assertIn(span, source_value)
                        if len(source_value) > 16:
                            multipart_fragment_sets.setdefault(
                                binding.semantic_ref,
                                set(),
                            ).add(span)

        self.assertIsNotNone(forgery_seed)
        assert forgery_seed is not None
        seed_unit, seed_graph, seed_opening, seed_closing = forgery_seed
        seed_anchor = seed_unit.text[
            seed_opening.surface_scalar_end : seed_closing.surface_scalar_start
        ]
        forged_parts = tuple(
            part
            for pair_index in range(3)
            for part in (
                stage1_response_module._part(
                    quote_open,
                    seed_opening.semantic_ref,
                    f"forged:{pair_index}:quote_open",
                ),
                stage1_response_module._part(
                    seed_anchor,
                    seed_opening.semantic_ref,
                    f"forged:{pair_index}:anchor",
                ),
                stage1_response_module._part(
                    quote_close,
                    seed_opening.semantic_ref,
                    f"forged:{pair_index}:quote_close",
                ),
            )
        )
        forged_text, forged_bindings = stage1_response_module._surface_parts(
            forged_parts
        )
        forged_unit = replace(
            seed_unit,
            text=forged_text,
            realized_semantic_bindings=forged_bindings,
        )
        with self.assertRaisesRegex(
            CMEEStage1ContractError,
            "stage1_realization_quote_policy_invalid",
        ):
            stage1_response_module._validate_quote_policy(
                forged_unit,
                seed_graph,
            )

        self.assertTrue(multipart_fragment_sets)
        self.assertTrue(
            all(len(spans) >= 2 for spans in multipart_fragment_sets.values())
        )

        # Quotation is a source citation, not a paraphrase wrapper.  Exercise
        # unrelated typed shapes so this remains a source-bound invariant and
        # not an exact8 expected-text oracle.
        quoted_shape_count = 0
        for index, memo in enumerate(
            (
                "仕事が重く感じる。",
                "体がだるい。",
                "仕事が続いて疲れていて、朝から何も手につかない。",
                "私は散歩したいと言っている。",
                "今日は仕事で疲れたけど、帰ってから少し散歩したら落ち着いた。",
                "環境を変えたいけど変えられなくて疲れた。",
                "不安。でも、続けたい。",
            ),
            start=1,
        ):
            with self.subTest(source_quote_shape=index):
                outcome = MeaningExperienceEngine().generate(
                    _request(
                        record_id=f"stage4-source-quote-{index}",
                        memo=memo,
                    )
                )
                self.assertEqual(
                    outcome.status.value,
                    "GENERATED",
                    outcome.reason_codes,
                )
                assert outcome.artifact is not None
                compact_source = re.sub(r"\s+", "", memo)
                quoted = tuple(
                    re.sub(r"\s+", "", row)
                    for row in re.findall(r"「([^」]+)」", outcome.artifact.text)
                )
                self.assertTrue(quoted)
                quoted_shape_count += len(quoted)
                self.assertTrue(
                    all(row in compact_source for row in quoted),
                    "quoted text must be a contiguous source substring",
                )
        self.assertGreaterEqual(quoted_shape_count, 7)

        # A bounded interrogative burden keeps the complete source predicate,
        # including the proposition before か.  It must not collapse to a
        # terminal noun/right-edge window or introduce a synonym.
        for index, memo in enumerate(
            (
                "うまく進められるか不安。",
                "仕事を続けられるか心配。",
            ),
            start=1,
        ):
            with self.subTest(bounded_epistemic_predicate=index):
                _source, grounded_plan, _graph, _parent = _stage2_inputs(
                    _request(
                        record_id=f"stage4-epistemic-predicate-{index}",
                        memo=memo,
                    )
                )
                nucleus = next(
                    row
                    for row in grounded_plan.nuclei
                    if row.retention == "required"
                    and row.source_fields == ("memo",)
                )
                compact_source = memo.strip("、。！？!?「」『』 ")
                bounded = emlis_v1a_module._cmee_frozen_lexical_role_surface(
                    nucleus,
                    compact_source,
                )
                self.assertEqual(bounded, compact_source)
                self.assertRegex(bounded, r"か(?:不安|心配)$")
                self.assertGreater(len(bounded), len("心配"))

        for label, memo, source_shape in (
            (
                "inability",
                "環境を変えたいけど変えられなくて疲れた。",
                r"(?:られなく|れなく|できなく|動けなく)",
            ),
            (
                "conditional-action-change",
                "仕事で疲れたけど、帰ってから少し散歩したら落ち着いた。",
                r"(?:たら|だら|なら).+",
            ),
        ):
            with self.subTest(common_cause_source_shape=label):
                _source, _grounded_plan, shape_graph, _parent = _stage2_inputs(
                    _request(
                        record_id=f"stage4-source-shape-{label}",
                        memo=memo,
                    )
                )
                compact_source = re.sub(r"\s+", "", memo).strip(
                    "、。！？!?「」『』 "
                )
                admitted_values = tuple(
                    row.value
                    for row in shape_graph.nodes
                    if row.grounding_kind
                    in {"explicit", "user_stated_relation"}
                )
                self.assertTrue(
                    any(
                        value in compact_source
                        and re.search(source_shape, value)
                        for value in admitted_values
                    ),
                    "source shape was lost at the semantic boundary",
                )

        l1_over_limit_node = replace(graph.nodes[0], value="あ" * 17)
        l1_over_limit_graph = replace(
            graph,
            nodes=(l1_over_limit_node, *graph.nodes[1:]),
        )
        l1_over_limit_ref = (
            f"node:{l1_over_limit_node.node_id}@{CMEE_GROUNDED_GRAPH_SCHEMA_VERSION}"
        )
        with self.assertRaisesRegex(
            CMEEStage1ContractError,
            "stage1_surface_binding_unavailable",
        ):
            stage1_response_module._source_bound_role_surface(
                l1_over_limit_ref,
                l1_over_limit_graph,
                layer="LAYER_1",
            )

        over_limit_node = replace(graph.nodes[0], value="あ" * 33)
        over_limit_graph = replace(
            graph,
            nodes=(over_limit_node, *graph.nodes[1:]),
        )
        over_limit_ref = (
            f"node:{over_limit_node.node_id}@{CMEE_GROUNDED_GRAPH_SCHEMA_VERSION}"
        )
        with self.assertRaisesRegex(
            CMEEStage1ContractError,
            "stage1_surface_binding_unavailable",
        ):
            stage1_response_module._source_bound_role_surface(
                over_limit_ref,
                over_limit_graph,
            )

        source, grounded_plan, graph, parent = _stage2_inputs(
            _request(
                record_id="stage4-counter-later",
                memo="自分が悪いから、助けを求めてはいけない。",
                category="生活",
                emotion="不安",
                strength="strong",
            )
        )
        projection = build_stage1_semantic_projection(
            source=source,
            grounded_graph=graph,
            parent_plan=parent,
            grounded_plan=grounded_plan,
        )
        candidate_set = build_stage1_realization_candidate_set(
            projection=projection,
            grounded_graph=graph,
            parent_plan=parent,
        )
        selected = select_stage1_realization_candidate(
            candidate_set,
            projection=projection,
            grounded_graph=graph,
            parent_plan=parent,
        )
        counter_units = tuple(
            unit
            for unit in selected
            if unit.clause_frames[0].predicate_operator
            == SubjectiveOperator.COUNTER_SPECIFIC_PROMOTION.value
        )
        self.assertEqual(len(counter_units), 1)
        self.assertEqual(counter_units[0].clause_frames[0].speaker_marker, "EMLIS")

        # Head and connective selection belongs to the semantic claim role.
        # Scan the denominator by operator/stance/source shape rather than by
        # case ID or expected full sentence.
        inventory = dict(CMEE_STAGE1_MICROGRAMMAR_INVENTORY_TUPLE)
        connective_tokens = dict(inventory["connective_families"])
        operator_connectives = {
            (layer, operator): family
            for layer, operator, family in inventory["operator_connective_rows"]
        }
        basis_connectives = {
            (operator, detail, relation): family
            for operator, detail, relation, family in inventory[
                "subjective_basis_connective_rows"
            ]
        }
        attention_predicates = {
            predicate
            for variants in dict(inventory["attention_surface_rows"]).values()
            for _particle, predicate in variants
        }
        concern_row = next(
            row
            for row in inventory["subjective_operator_rows"]
            if row[:2] == ("FEEL_TOWARD", "CONCERN")
        )
        concern_predicates = {token for token in concern_row[3:] if token}
        special_heads_seen: set[str] = set()
        for fixture_index in range(len(EXACT8)):
            (
                _source,
                _plan,
                fixture_graph,
                _parent,
                fixture_projection,
                fixture_candidates,
            ) = _stage4_exact8_fixture(fixture_index)
            primary_units = fixture_candidates.candidates[0]
            contribution_by_id = {
                row.contribution_id: row
                for row in fixture_projection.observation_contributions
            }
            unit_by_move = {row.move_ref: row for row in primary_units}
            for layer2_index, claim in enumerate(
                fixture_projection.subjective_claims
            ):
                proposition = claim.asserted_subjective_proposition
                operator = proposition.subjective_operator.value
                detail = ""
                if proposition.subjective_operator is SubjectiveOperator.FEEL_TOWARD:
                    assert proposition.affect_category is not None
                    detail = proposition.affect_category.value
                elif (
                    proposition.subjective_operator
                    is SubjectiveOperator.TAKE_RELATIONAL_STANCE
                ):
                    assert proposition.stance_operator is not None
                    detail = proposition.stance_operator.value

                unit = unit_by_move[
                    stage1_response_module._move_ref(claim.subjective_claim_id)
                ]
                frame = unit.clause_frames[0]
                if layer2_index == 0:
                    expected_connective = "NONE"
                else:
                    expected_connective = operator_connectives[
                        ("LAYER_2", operator)
                    ]
                    overrides = {
                        basis_connectives[(operator, detail, contribution.relation_operator.value)]
                        for ref in claim.basis_observation_contribution_refs
                        if (contribution := contribution_by_id[ref])
                        and (
                            operator,
                            detail,
                            contribution.relation_operator.value,
                        )
                        in basis_connectives
                    }
                    self.assertLessEqual(len(overrides), 1)
                    if overrides:
                        expected_connective = next(iter(overrides))
                self.assertEqual(frame.discourse_relation, expected_connective)
                self.assertEqual(
                    frame.connective_requirement,
                    None if expected_connective == "NONE" else expected_connective,
                )
                if expected_connective != "NONE":
                    self.assertTrue(
                        any(
                            unit.text.startswith(f"{token}、")
                            for token in connective_tokens[expected_connective]
                        )
                    )

                # The established explicit-speaker prefix owns `Emlisは、`.
                # Outside that exact prefix, a semantic topic particle and
                # separator must never be realized adjacently.
                semantic_body = unit.text
                if frame.speaker_marker == "EMLIS":
                    self.assertIn("Emlisは、", semantic_body)
                    semantic_body = semantic_body.replace("Emlisは、", "", 1)
                self.assertNotIn("は、", semantic_body)

                object_ref = stage1_response_module._subjective_object_ref(
                    fixture_projection,
                    claim,
                )
                head = stage1_response_module._anaphoric_surface(
                    fixture_projection,
                    object_ref,
                    fixture_graph,
                    claim=claim,
                )
                role_value = stage1_response_module._source_bound_role_surface(
                    object_ref,
                    fixture_graph,
                    layer=None,
                )
                semantic_operator = (
                    stage1_response_module._semantic_operator_for_object(
                        fixture_projection,
                        object_ref,
                    )
                )
                if (
                    semantic_operator == SemanticOperator.PRESENT_DIRECTION.value
                    and stage1_response_module._source_open_question_parts(
                        role_value
                    )
                    is not None
                    and (
                        proposition.subjective_operator
                        is SubjectiveOperator.ATTEND_TO
                        or (
                            proposition.subjective_operator
                            is SubjectiveOperator.TAKE_RELATIONAL_STANCE
                            and proposition.stance_operator is not None
                            and proposition.stance_operator.value
                            == "HOLD_UNFINISHED_OPEN"
                        )
                    )
                ):
                    self.assertEqual(head, "その問い")
                    self.assertIn(head, unit.text)
                    special_heads_seen.add(head)
                contrast = stage1_response_module._source_direct_contrast_roles(
                    role_value
                )
                if (
                    semantic_operator == SemanticOperator.PRESENT_DIRECTION.value
                    and contrast is not None
                    and contrast[1][1] == "hesitation"
                    and proposition.subjective_operator
                    is SubjectiveOperator.FEEL_TOWARD
                    and proposition.affect_category is AffectCategory.CONCERN
                ):
                    self.assertEqual(head, "そのためらい")
                    self.assertIn(head, unit.text)
                    special_heads_seen.add(head)

                if proposition.subjective_operator is SubjectiveOperator.ATTEND_TO:
                    self.assertTrue(
                        any(unit.text.endswith(f"{row}。") for row in attention_predicates)
                    )
                    self.assertFalse(
                        any(unit.text.endswith(f"{row}。") for row in concern_predicates)
                    )
                elif (
                    proposition.subjective_operator is SubjectiveOperator.FEEL_TOWARD
                    and proposition.affect_category is AffectCategory.CONCERN
                ):
                    self.assertTrue(
                        any(unit.text.endswith(f"{row}。") for row in concern_predicates)
                    )
                    self.assertFalse(
                        any(unit.text.endswith(f"{row}。") for row in attention_predicates)
                    )
        self.assertEqual(special_heads_seen, {"その問い", "そのためらい"})

        source, grounded_plan, graph, parent = _stage2_inputs(
            _request(
                record_id="stage4-connective-collision",
                memo="また疲れている。",
                category="生活",
                emotion="不安",
            )
        )
        projection = build_stage1_semantic_projection(
            source=source,
            grounded_graph=graph,
            parent_plan=parent,
            grounded_plan=grounded_plan,
        )
        candidate_set = build_stage1_realization_candidate_set(
            projection=projection,
            grounded_graph=graph,
            parent_plan=parent,
        )
        with patch.object(
            stage1_response_module,
            "_realize_stage1_variant",
            side_effect=AssertionError("S9 must not generate after composition"),
        ) as realizer:
            selected = select_stage1_realization_candidate(
                candidate_set,
                projection=projection,
                grounded_graph=graph,
                parent_plan=parent,
            )
            self.assertEqual(realizer.call_count, 0)
        selected_text = "\n".join(unit.text for unit in selected)
        self.assertNotIn("またまた", selected_text)
        self.assertNotIn("またEmlis", selected_text)
        self.assertIn("「また疲れている」", selected_text)

    def test_stage4_has_no_provider_random_template_or_inventory_bypass(self) -> None:
        source_code = inspect.getsource(stage1_response_module)
        tree = ast.parse(source_code)
        imported_roots = {
            alias.name.split(".", 1)[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        } | {
            str(node.module).split(".", 1)[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        }
        self.assertTrue(
            {"random", "requests", "httpx", "openai"}.isdisjoint(imported_roots)
        )
        for forbidden in (
            "expected_text",
            "EXACT8",
            "case_id",
            "finished_sentence_bank",
            "automatic_retry(",
        ):
            self.assertNotIn(forbidden, source_code)

        inventory_assignment = next(
            node
            for node in tree.body
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name)
                and target.id == "CMEE_STAGE1_MICROGRAMMAR_INVENTORY_TUPLE"
                for target in node.targets
            )
        )

        def contains_japanese(value: str) -> bool:
            return any(
                "\u3040" <= char <= "\u30ff" or "\u3400" <= char <= "\u9fff"
                for char in value
            )

        inventory_literals = {
            node.value
            for node in ast.walk(inventory_assignment.value)
            if isinstance(node, ast.Constant)
            and type(node.value) is str
            and contains_japanese(node.value)
        }
        module_literals = {
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant)
            and type(node.value) is str
            and contains_japanese(node.value)
        }
        self.assertTrue(module_literals.issubset(inventory_literals))

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
