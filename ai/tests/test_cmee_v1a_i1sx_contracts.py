# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import hashlib
import io
import inspect
import json
import os
import re
import tempfile
import unittest
from collections import Counter
from dataclasses import fields, replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from emlis_ai_current_input_bundle import build_emlis_current_input_bundle
from emlis_ai_evidence_ledger_service import build_evidence_span_resolver
from emlis_ai_grounded_observation_plan import (
    build_final_stage1_grounded_observation_plan,
    build_grounded_observation_plan,
    validate_grounded_observation_plan,
)
from cocolon_meaning_experience_engine import EngineStatus, GenerationRequest, MeaningExperienceEngine
from cocolon_meaning_experience_engine.contracts import (
    AffectCategory,
    AffectIntensity,
    AppraisalDimension,
    AppraisalOperation,
    ArgumentBinding,
    ArgumentRole,
    AttachmentAdmission,
    CMEE_GROUNDED_GRAPH_SCHEMA_VERSION,
    CMEE_STAGE1_ANTI_TEMPLATE_FORBIDDEN_REGISTRY_FIELDS,
    CMEE_STAGE1_ANTI_TEMPLATE_FORBIDDEN_SELECTOR_INPUTS,
    CMEE_STAGE1_EMLIS_OWNER_REF,
    CMEE_STAGE1_FINAL_LOGICAL_ID_REGISTRY,
    CMEE_STAGE1_MICROGRAMMAR_POLICY_REF,
    CMEE_STAGE1_RECEPTION_ACT_MAPPING_EXACT7,
    CMEE_STAGE1_RECEPTION_ASSET_MAPPING_DOCS_BYTES,
    CMEE_STAGE1_RECEPTION_ASSET_MAPPING_DOCS_SHA256,
    CMEE_STAGE1_RECEPTION_ASSET_MAPPING_DOCS_TUPLE,
    CMEE_STAGE1_RECEPTION_ASSET_MAPPING_VERSION,
    CMEE_STAGE1_RECEPTION_STANCE_MAPPING_EXACT5,
    CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
    CMEE_STAGE1_SUBJECTIVE_FORBIDDEN_PROMOTIONS,
    CMEE_STAGE1_TRACE_EXTENSION_SCHEMA_VERSION,
    CMEE_STAGE1_VALUE_POLICY_REF,
    CMEEStage1ContractError,
    ClauseFrame,
    EmlisAffectContent,
    EmlisAppraisalContent,
    EmlisInterpretationCandidate,
    EmlisMeaningField,
    EmlisRelationalPosition,
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
    MaterialRisk,
    MaterialValueContent,
    ObservationContributionKind,
    ObservationDepthClass,
    OwnerClass,
    PolicyBasisBinding,
    PolicyBasisOwnerKind,
    PolicyBasisRole,
    PlannedObservationContribution,
    ResolverResolution,
    RealizationCandidateSet,
    RealizedSemanticBinding,
    RealizedSentenceUnit,
    RelationOperator,
    RelationalClosure,
    RelationalCommitment,
    RelationalPositionKind,
    SourceOwnerDisposition,
    SourceOwnerResolution,
    SemanticOperator,
    SourceQualifierBinding,
    StanceOperator,
    SubjectiveAssertionModality,
    SubjectiveBasisBinding,
    SubjectiveBasisRole,
    SubjectiveContentKind,
    SubjectiveDepthClass,
    SubjectiveMode,
    SubjectiveOperator,
    SubjectiveProposition,
    SubjectivePropositionV2,
    SurfaceDerivation,
    SurfaceDerivationKind,
    TemperatureClass,
    VisibleAuthority,
    VisibleUnitTrace,
    ValueApplication,
    project_stage1_policy_basis_binding_ref,
    project_stage1_projection_preimage_ref,
    project_stage1_source_qualifier_binding_ref,
    project_stage1_subjective_basis_binding_ref,
    recompute_stage1_identity,
    stage1_canonical_json_bytes,
    stage1_projection_artifact_ref,
    stage1_subjective_forbidden_promotions,
    stage1_subjective_semantic_key,
    stage1_value_principle_ref,
    validate_stage1_anti_template_registry_invariant,
    validate_stage1_final_logical_id_registry,
    validate_stage1_identity,
    validate_stage1_local_ref_dag,
    validate_stage1_projection,
    validate_stage1_sentence_unit,
    validate_stage1_trace_spine,
    validate_subjective_proposition_v2,
    validate_surface_derivation,
    validate_version_qualified_ref,
)
import cocolon_meaning_experience_engine.emlis_stage1_response as stage1_response_module
import cocolon_meaning_experience_engine.emlis_stage1_composition as stage1_composition_module
import cocolon_meaning_experience_engine.emlis_v1a as emlis_v1a_module
import cocolon_meaning_experience_engine.contracts as contracts_module
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
PUBLIC_NONSECRET_EARLY_STANDIN_EXACT4 = (
    (
        "tension",
        "休みたい気持ちと、もう少し進めたい気持ちが同時にある。",
        "生活",
        "不安",
        "medium",
    ),
    (
        "temporal_change",
        "音楽を聴いたら、少し落ち着いた。ただ、いつもそうなるとは思っていない。",
        "生活",
        "不安",
        "medium",
    ),
    (
        "help_seeking",
        "少し話を聞いてほしいが、今声をかけてよいか迷っている。",
        "生活",
        "不安",
        "medium",
    ),
    (
        "unfinished",
        "予定の話はした。でも、まだ迷いが残っていて、どうしたいかは分からない。",
        "仕事",
        "自己理解",
        "medium",
    ),
)


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


def _final_stage1_composition_inputs(request: GenerationRequest):
    """Build the disabled final Phase-A/Phase-B seam from frozen real inputs."""

    source = freeze_text_source(request)
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
    phase_a = stage1_response_module.build_subjective_planning_inputs(
        source=source,
        grounded_graph=graph,
        parent_plan=parent_plan,
        grounded_plan=grounded_plan,
    )
    subjective_plan = stage1_composition_module.project_subjective_meaning_plan(
        phase_a
    )
    final_projection = stage1_response_module.seal_stage1_projection(
        phase_a,
        subjective_plan,
    )
    phase_b = stage1_response_module.build_surface_composition_inputs(
        phase_a,
        final_projection,
    )
    return (
        source,
        grounded_plan,
        graph,
        parent_plan,
        final_projection,
        phase_a,
        subjective_plan,
        phase_b,
    )


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
            SourceOwnerDisposition.SOURCE_EXPLICIT_VISIBLE,
            SourceOwnerDisposition.SUPPLEMENTAL_USER_VISIBLE,
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
                    if row.source_owner_disposition in positive_dispositions
                )
                expected_unresolved_owner_ids = tuple(
                    row.meaning_owner_id
                    for row in graph.owner_dispositions
                    if row.source_owner_disposition not in positive_dispositions
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
                        == (
                            row.source_owner_disposition
                            in positive_dispositions
                        )
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
                    emotion_disposition.source_owner_disposition,
                    SourceOwnerDisposition.SOURCE_EXPLICIT_VISIBLE,
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
                source_owner_disposition=(
                    SourceOwnerDisposition.NOT_VISIBLE_UNRESOLVED
                ),
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
            SourceOwnerDisposition.SOURCE_EXPLICIT_VISIBLE,
            SourceOwnerDisposition.SUPPLEMENTAL_USER_VISIBLE,
        }
        coordinated_parent_plan = replace(
            parent_plan,
            visible_owner_ids=tuple(
                row.meaning_owner_id
                for row in downgraded_dispositions
                if row.source_owner_disposition in positive_dispositions
            ),
            unresolved_owner_ids=tuple(
                row.meaning_owner_id
                for row in downgraded_dispositions
                if row.source_owner_disposition not in positive_dispositions
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
            and row.source_owner_disposition in positive_dispositions
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
            and row.source_owner_disposition in positive_dispositions
            and set(row.visible_claim_refs).intersection(runtime_used_claim_ids)
        )
        self.assertEqual(len(runtime_owner_ids), 1)
        runtime_owner_id = runtime_owner_ids[0]
        runtime_dispositions = tuple(
            replace(
                row,
                visible_authority=VisibleAuthority.NONE,
                source_owner_disposition=(
                    SourceOwnerDisposition.NOT_VISIBLE_UNRESOLVED
                ),
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
                if row.source_owner_disposition in positive_dispositions
            ),
            unresolved_owner_ids=tuple(
                row.meaning_owner_id
                for row in runtime_dispositions
                if row.source_owner_disposition not in positive_dispositions
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

    def test_step6_runner_rejects_noncanonical_source_owner_row_fields(self) -> None:
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
            if row.source_owner_disposition
            is SourceOwnerDisposition.SOURCE_EXPLICIT_VISIBLE
        )
        positive_mutations = (
            replace(positive, visible_authority=VisibleAuthority.NONE),
            replace(positive, resolver_resolution=ResolverResolution.UNRESOLVED),
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
            if row.source_owner_disposition
            is SourceOwnerDisposition.NOT_VISIBLE_UNRESOLVED
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
        self.assertFalse(report["source_owner_contract_complete"])
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

    def test_source_owner_disposition_contract_is_exact_six(self) -> None:
        self.assertEqual(
            {row.value for row in SourceOwnerDisposition},
            {
                "SOURCE_EXPLICIT_VISIBLE",
                "SUPPLEMENTAL_USER_VISIBLE",
                "UNKNOWN_PRESERVED_LIMITED",
                "CLARIFICATION_TARGET",
                "NOT_VISIBLE_UNRESOLVED",
                "SEPARATE_SAFETY",
            },
        )

    def test_source_owner_resolution_has_the_complete_approved_shape(self) -> None:
        self.assertEqual(
            tuple(row.name for row in fields(SourceOwnerResolution)),
            (
                "meaning_owner_id",
                "owner_class",
                "resolver_resolution",
                "attachment_admission",
                "visible_authority",
                "source_owner_disposition",
                "visible_claim_refs",
                "evidence_refs",
                "target_unknown_ref",
                "reason_codes",
            ),
        )
        self.assertEqual({row.value for row in OwnerClass}, {"REQUIRED", "ACTIVE_OPTIONAL"})
        self.assertEqual(
            {row.value for row in ResolverResolution},
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
        binding = stage1_response_module._bind_grounded_plan(
            source,
            contrast_graph,
            grounded_plan,
        )
        endpoint_node_ids = tuple(
            stage1_response_module._local_ref(row.semantic_ref)
            for row in contrast.argument_bindings
        )
        self.assertEqual(
            tuple(binding.source_order[node_id] for node_id in endpoint_node_ids),
            tuple(
                sorted(
                    binding.source_order[node_id]
                    for node_id in endpoint_node_ids
                )
            ),
        )
        graph_node_order = {
            row.node_id: index for index, row in enumerate(contrast_graph.nodes)
        }
        self.assertEqual(
            tuple(graph_node_order[node_id] for node_id in endpoint_node_ids),
            tuple(
                sorted(graph_node_order[node_id] for node_id in endpoint_node_ids)
            ),
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
        direction_shape = stage1_response_module._relation_shape(
            direction_edge,
            {row.node_id: row for row in contrast_graph.nodes},
            binding,
        )
        self.assertEqual(
            direction_shape,
            stage1_response_module._relation_shape(
                replace(
                    direction_edge,
                    source_node_id=direction_edge.target_node_id,
                    target_node_id=direction_edge.source_node_id,
                ),
                {row.node_id: row for row in contrast_graph.nodes},
                binding,
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

    def test_plain_symmetric_relation_source_order_is_case_id_invariant(
        self,
    ) -> None:
        request_tokens = (
            "early-known-02",
            "second-review-known-02",
            "official-known-02",
            "x",
        )
        temporal_memo = (
            "散歩に出たら、少し落ち着いた。"
            "ただ、いつもそうなるとは思っていない。"
        )
        semantic_shapes = []
        endpoint_shapes = []
        qualifier_shapes = []
        arc_shapes = []
        artifact_shapes = []
        lexical_orientations = []
        official_fixture = None

        for request_token in request_tokens:
            with self.subTest(request_token=request_token):
                (
                    source,
                    grounded_plan,
                    graph,
                    parent_plan,
                    projection,
                    phase_a,
                    _subjective_plan,
                    phase_b,
                ) = _final_stage1_composition_inputs(
                    _request(record_id=request_token, memo=temporal_memo)
                )
                binding = stage1_response_module._bind_grounded_plan(
                    source,
                    graph,
                    grounded_plan,
                )
                node_graph_order = {
                    row.node_id: index for index, row in enumerate(graph.nodes)
                }

                def source_order(semantic_ref: str) -> int:
                    return binding.source_order[
                        stage1_response_module._local_ref(semantic_ref)
                    ]

                relation_candidates = tuple(
                    row
                    for row in projection.interpretation_candidates
                    if row.relation_operator
                    is not RelationOperator.NO_RELATION_CLAIM
                )
                tension = tuple(
                    row
                    for row in relation_candidates
                    if row.candidate_kind is InterpretationKind.TENSION
                )
                action_change = tuple(
                    row
                    for row in relation_candidates
                    if row.candidate_kind
                    is InterpretationKind.ACTION_THEN_CHANGE_ONCE
                )
                self.assertEqual(len(tension), 1)
                self.assertEqual(len(action_change), 1)
                tension_row = tension[0]
                action_change_row = action_change[0]
                self.assertEqual(
                    tuple(row.role for row in tension_row.argument_bindings),
                    (ArgumentRole.LEFT, ArgumentRole.RIGHT),
                )
                self.assertEqual(
                    tuple(
                        source_order(row.semantic_ref)
                        for row in tension_row.argument_bindings
                    ),
                    (1, 3),
                )
                self.assertEqual(
                    tuple(row.role for row in action_change_row.argument_bindings),
                    (ArgumentRole.ACTION, ArgumentRole.CHANGE),
                )
                self.assertEqual(
                    tuple(
                        source_order(row.semantic_ref)
                        for row in action_change_row.argument_bindings
                    ),
                    (0, 1),
                )
                self.assertEqual(
                    tuple(
                        node_graph_order[
                            stage1_response_module._local_ref(row.semantic_ref)
                        ]
                        for row in tension_row.argument_bindings
                    ),
                    tuple(
                        source_order(row.semantic_ref)
                        for row in tension_row.argument_bindings
                    ),
                )
                lexical_orientations.append(
                    tuple(
                        row.semantic_ref for row in tension_row.argument_bindings
                    )
                    == tuple(sorted(tension_row.semantic_refs))
                )

                candidate_index = {
                    row.candidate_id: index
                    for index, row in enumerate(
                        projection.interpretation_candidates
                    )
                }
                semantic_shapes.append(
                    tuple(
                        (
                            row.candidate_kind.value,
                            row.semantic_operator.value,
                            row.relation_operator.value,
                            tuple(
                                (
                                    argument.role.value,
                                    source_order(argument.semantic_ref),
                                )
                                for argument in row.argument_bindings
                            ),
                            tuple(source_order(ref) for ref in row.semantic_refs),
                            row.derivation_rule_id,
                            row.required_qualifiers,
                            row.forbidden_promotions,
                        )
                        for row in projection.interpretation_candidates
                    )
                )
                endpoint_shapes.append(
                    tuple(
                        (
                            candidate_index[row.relation_candidate_ref],
                            row.source_argument_role.value,
                            source_order(row.source_semantic_ref),
                            candidate_index[row.endpoint_grounded_candidate_ref],
                        )
                        for row in phase_a.relation_endpoint_grounded_candidate_ref_by_binding_key
                    )
                )
                qualifier_shapes.append(
                    tuple(
                        (
                            candidate_index[row.candidate_ref],
                            row.qualifier_scope.value,
                            (
                                None
                                if row.source_argument_role is None
                                else row.source_argument_role.value
                            ),
                            (
                                None
                                if row.source_semantic_ref is None
                                else source_order(row.source_semantic_ref)
                            ),
                            row.axis.value,
                            row.value,
                        )
                        for row in phase_a.qualifier_value_by_candidate_scope_axis_key
                    )
                )

                contribution_by_relation_ref = {
                    row.relation_basis_refs[0]: row
                    for row in projection.observation_contributions
                    if row.relation_operator
                    is not RelationOperator.NO_RELATION_CLAIM
                }
                arc = stage1_composition_module.project_stage1_discourse_arc(
                    phase_b
                )
                admitted_directions = tuple(
                    row
                    for row in arc.dependency_rows
                    if row.dependency_kind
                    is stage1_composition_module.ArcDependencyKind.ADMITTED_RELATION_DIRECTION
                )
                arc_shape = tuple(
                    (
                        contribution_by_relation_ref[
                            row.source_relation_ref
                        ].relation_operator.value,
                        source_order(row.predecessor_owner_ref),
                        source_order(row.successor_owner_ref),
                    )
                    for row in admitted_directions
                )
                self.assertEqual(
                    arc_shape,
                    (
                        (RelationOperator.TENSION_WITH.value, 1, 3),
                        (RelationOperator.ACTION_PRECEDES_CHANGE.value, 0, 1),
                    ),
                )
                arc_shapes.append(arc_shape)

                result = stage1_composition_module.compose_stage1_from_projection(
                    phase_b
                )
                ranked_shapes = []
                for ranked in result.ranked_candidates:
                    artifact = ranked.normalized_artifact
                    clause_shapes = []
                    for plan in artifact.clause_plan_rows:
                        constraint_index = {
                            row.clause_scalar_constraint_ref: index
                            for index, row in enumerate(plan.scalar_constraint_rows)
                        }
                        scalar_rows = tuple(
                            (
                                row.clause_argument_role.value
                                if row.clause_argument_role is not None
                                else None,
                                (
                                    source_order(row.owner_ref)
                                    if row.owner_ref.startswith("node:")
                                    else "NON_NODE_OWNER"
                                ),
                                row.polarity,
                                row.modality,
                                row.time_scope,
                            )
                            for row in plan.scalar_constraint_rows
                        )
                        realization_rows = tuple(
                            (
                                constraint_index[
                                    row.clause_scalar_constraint_ref
                                ],
                                row.scalar_axis.value,
                                row.realization_mode.value,
                                row.registered_realization_rule_ref,
                                row.target_clause_slot_ref,
                            )
                            for row in plan.scalar_surface_realization_rows
                        )
                        clause_shapes.append(
                            (
                                plan.semantic_clause_kind.value,
                                plan.predicate_valency.value,
                                plan.grammatical_role_assignment_rule.value,
                                plan.syntactic_orientation.value,
                                scalar_rows,
                                realization_rows,
                            )
                        )
                    profile = ranked.discourse_preference_profile
                    profile_shape = tuple(
                        getattr(profile, field.name).value
                        for field in fields(profile)[:-1]
                    )
                    ranked_shapes.append(
                        (
                            ranked.rank,
                            ranked.shared_variant_id,
                            tuple(
                                (unit.layer, unit.text)
                                for unit in ranked.sentence_units
                            ),
                            tuple(clause_shapes),
                            tuple(
                                row.defect_kind.value
                                for row in artifact.correctable_defect_rows
                            ),
                            artifact.normal_form_version,
                            artifact.normal_form_applied,
                            tuple(
                                row.value for row in artifact.normalization_phase_trace
                            ),
                            profile_shape,
                        )
                    )
                    self.assertTrue(
                        all(
                            unit.surface_text_sha256
                            == hashlib.sha256(unit.text.encode("utf-8")).hexdigest()
                            for unit in ranked.sentence_units
                        )
                    )
                artifact_shapes.append(
                    (
                        result.internal_candidate_count,
                        tuple(ranked_shapes),
                    )
                )
                if request_token == "official-known-02":
                    official_fixture = (
                        source,
                        grounded_plan,
                        graph,
                        parent_plan,
                        binding,
                        tension_row,
                    )

        self.assertEqual(lexical_orientations, [True, True, False, True])
        for rows in (
            semantic_shapes,
            endpoint_shapes,
            qualifier_shapes,
            arc_shapes,
            artifact_shapes,
        ):
            self.assertEqual(len(set(rows)), 1)

        self.assertIsNotNone(official_fixture)
        assert official_fixture is not None
        (
            source,
            grounded_plan,
            graph,
            parent_plan,
            binding,
            tension_row,
        ) = official_fixture
        edge_id = stage1_response_module._local_ref(
            tension_row.relation_basis_refs[0]
        )
        edge = next(row for row in graph.edges if row.edge_id == edge_id)
        node_by_id = {row.node_id: row for row in graph.nodes}
        canonical_shape = stage1_response_module._relation_shape(
            edge,
            node_by_id,
            binding,
        )
        self.assertEqual(
            canonical_shape,
            stage1_response_module._relation_shape(
                replace(
                    edge,
                    source_node_id=edge.target_node_id,
                    target_node_id=edge.source_node_id,
                ),
                dict(reversed(tuple(node_by_id.items()))),
                binding,
            ),
        )
        action_edge = next(
            row for row in graph.edges if row.relation == "action_supports_change"
        )
        self.assertIsNotNone(
            stage1_response_module._relation_shape(
                action_edge,
                node_by_id,
                binding,
            )
        )
        self.assertIsNone(
            stage1_response_module._relation_shape(
                replace(
                    action_edge,
                    source_node_id=action_edge.target_node_id,
                    target_node_id=action_edge.source_node_id,
                ),
                node_by_id,
                binding,
            )
        )

        old_left, old_right = sorted(
            (
                stage1_response_module._node_ref(edge.source_node_id),
                stage1_response_module._node_ref(edge.target_node_id),
            )
        )
        old_shape = (
            tension_row.candidate_kind,
            tension_row.semantic_operator,
            tension_row.relation_operator,
            (
                ArgumentBinding(ArgumentRole.LEFT, old_left),
                ArgumentBinding(ArgumentRole.RIGHT, old_right),
            ),
        )
        old_candidate = stage1_response_module._candidate_from_relation(
            graph,
            edge,
            binding,
            old_shape,
        )
        self.assertNotEqual(old_candidate, tension_row)
        candidate_pool = build_interpretation_candidate_pool(
            graph,
            parent_plan,
            source=source,
            grounded_plan=grounded_plan,
        )
        canonical_pool_tension = next(
            row
            for row in candidate_pool
            if row.candidate_kind is InterpretationKind.TENSION
        )
        tampered_pool = tuple(
            old_candidate
            if row.candidate_id == canonical_pool_tension.candidate_id
            else row
            for row in candidate_pool
        )
        with self.assertRaisesRegex(
            CMEEStage1ContractError,
            "stage1_candidate_pool_noncanonical",
        ):
            stage1_response_module.validate_interpretation_candidate_pool(
                tampered_pool,
                grounded_graph=graph,
                parent_plan=parent_plan,
                source=source,
                grounded_plan=grounded_plan,
            )
        node_source_order = {
            row.node_id: index for index, row in enumerate(graph.nodes)
        }
        contracts_module._validate_stage1_relation_binding(
            canonical_pool_tension,
            edge_by_id={row.edge_id: row for row in graph.edges},
            node_by_id=node_by_id,
            node_source_order=node_source_order,
            direct_shapes_by_node_ref={},
        )
        with self.assertRaisesRegex(
            CMEEStage1ContractError,
            "stage1_candidate_relation_binding_invalid",
        ):
            contracts_module._validate_stage1_relation_binding(
                old_candidate,
                edge_by_id={row.edge_id: row for row in graph.edges},
                node_by_id=node_by_id,
                node_source_order=node_source_order,
                direct_shapes_by_node_ref={},
            )

        missing_source_order = dict(binding.source_order)
        missing_source_order.pop(edge.target_node_id)
        duplicate_source_order = dict(binding.source_order)
        duplicate_source_order[edge.target_node_id] = duplicate_source_order[
            edge.source_node_id
        ]
        for source_order_map in (missing_source_order, duplicate_source_order):
            with self.assertRaisesRegex(
                CMEEStage1ContractError,
                "stage1_relation_direction_invalid",
            ):
                stage1_response_module._relation_shape(
                    edge,
                    node_by_id,
                    replace(binding, source_order=source_order_map),
                )

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


class CMEEStage1AdditionalCorrectionStep1ContractsTest(unittest.TestCase):
    def _surface_rule_registry(
        self,
    ) -> dict[tuple[SurfaceDerivationKind, str | None], tuple[str, ...]]:
        rows: dict[
            tuple[SurfaceDerivationKind, str | None],
            tuple[str, ...],
        ] = {}
        for kind in SurfaceDerivationKind:
            if kind is SurfaceDerivationKind.PROJECTED_RESPONSE_OBJECT:
                for mode in ("EXPLICIT", "COMPOSITE", "ANAPHORIC"):
                    rows[(kind, mode)] = (
                        f"rule:{kind.value.lower()}-{mode.lower()}"
                        "@cocolon.cmee.surface.v1",
                    )
            else:
                rows[(kind, None)] = (
                    f"rule:{kind.value.lower()}@cocolon.cmee.surface.v1",
                )
        return rows

    def _valid_subjective_v2(
        self,
        content_kind: SubjectiveContentKind,
        *,
        bounded_counterposition: bool = False,
        material_unknown: bool = False,
    ) -> tuple[SubjectivePropositionV2, dict[str, object]]:
        projection_preimage_ref = project_stage1_projection_preimage_ref(
            grounded_graph_ref="graph-1",
            parent_observation_duty_ref="observation-duty-1",
            parent_reception_duty_ref="reception-duty-1",
            interpretation_candidate_ids=("candidate-1",),
            meaning_field_id="meaning-field-1",
            observation_contribution_ids=("contribution-1", "contribution-2"),
            retained_reception_act_ids=("reception-act-1",),
            observation_depth_class=ObservationDepthClass.FOCUSED,
            temperature_class=TemperatureClass.STANDARD,
            reception_style_policy_ref="policy:style@cocolon.style.v1",
            emlis_value_policy_ref=CMEE_STAGE1_VALUE_POLICY_REF,
        )
        roles = {
            SubjectiveContentKind.AFFECT: SubjectiveBasisRole.ELICITOR,
            SubjectiveContentKind.APPRAISAL: SubjectiveBasisRole.APPRAISED_OBJECT,
            SubjectiveContentKind.MATERIAL_VALUE: SubjectiveBasisRole.APPRAISED_OBJECT,
            SubjectiveContentKind.RELATIONAL_POSITION: SubjectiveBasisRole.CHOICE_TARGET,
        }
        basis_specs = [
            ("contribution-1", "semantic-1", roles[content_kind]),
        ]
        if bounded_counterposition:
            basis_specs.append(
                (
                    "contribution-2",
                    "semantic-2",
                    SubjectiveBasisRole.APPRAISED_OBJECT,
                )
            )
        basis_rows = tuple(
            SubjectiveBasisBinding(
                projection_preimage_ref=projection_preimage_ref,
                binding_ref=project_stage1_subjective_basis_binding_ref(
                    projection_preimage_ref=projection_preimage_ref,
                    contribution_ref=contribution_ref,
                    semantic_ref=semantic_ref,
                    role=role,
                ),
                contribution_ref=contribution_ref,
                semantic_ref=semantic_ref,
                role=role,
            )
            for contribution_ref, semantic_ref, role in basis_specs
        )
        qualifier_codes = (
            "polarity:POSITIVE",
            "modality:ACTUAL",
            "time_scope:CURRENT",
        )
        qualifier_rows = tuple(
            SourceQualifierBinding(
                projection_preimage_ref=projection_preimage_ref,
                source_qualifier_binding_ref=(
                    project_stage1_source_qualifier_binding_ref(
                        projection_preimage_ref=projection_preimage_ref,
                        basis_binding_ref=row.binding_ref,
                        source_candidate_ref="candidate-1",
                        source_argument_role=None,
                        canonical_qualifier_codes=qualifier_codes,
                        polarity="POSITIVE",
                        modality="ACTUAL",
                        time_scope="CURRENT",
                    )
                ),
                basis_binding_ref=row.binding_ref,
                source_candidate_ref="candidate-1",
                source_argument_role=None,
                canonical_qualifier_codes=qualifier_codes,
                polarity="POSITIVE",
                modality="ACTUAL",
                time_scope="CURRENT",
            )
            for row in basis_rows
        )

        policy_basis_rows: list[PolicyBasisBinding] = []
        if content_kind is SubjectiveContentKind.MATERIAL_VALUE:
            policy_basis_rows.append(
                PolicyBasisBinding(
                    projection_preimage_ref=projection_preimage_ref,
                    binding_ref=project_stage1_policy_basis_binding_ref(
                        projection_preimage_ref=projection_preimage_ref,
                        owner_kind=PolicyBasisOwnerKind.CONTRIBUTION,
                        owner_ref="contribution-1",
                        role=PolicyBasisRole.BURDEN_OR_RESIDUE,
                    ),
                    owner_kind=PolicyBasisOwnerKind.CONTRIBUTION,
                    owner_ref="contribution-1",
                    role=PolicyBasisRole.BURDEN_OR_RESIDUE,
                )
            )
        material_unknown_refs: tuple[str, ...] = ()
        if material_unknown:
            material_unknown_refs = ("unknown-1",)
            policy_basis_rows.append(
                PolicyBasisBinding(
                    projection_preimage_ref=projection_preimage_ref,
                    binding_ref=project_stage1_policy_basis_binding_ref(
                        projection_preimage_ref=projection_preimage_ref,
                        owner_kind=PolicyBasisOwnerKind.MATERIAL_UNKNOWN,
                        owner_ref="unknown-1",
                        role=PolicyBasisRole.MATERIAL_UNKNOWN,
                    ),
                    owner_kind=PolicyBasisOwnerKind.MATERIAL_UNKNOWN,
                    owner_ref="unknown-1",
                    role=PolicyBasisRole.MATERIAL_UNKNOWN,
                )
            )

        primary_bindings = (basis_rows[0].binding_ref,)
        boundary_bindings = (
            (basis_rows[1].binding_ref,)
            if bounded_counterposition
            else ()
        )
        affect_content = None
        appraisal_content = None
        material_value_content = None
        relational_position = None
        focal_relation_ref = None
        if content_kind is SubjectiveContentKind.AFFECT:
            affect_content = EmlisAffectContent(
                category=AffectCategory.CONCERN,
                intensity=AffectIntensity.QUIET,
                elicitor_bindings=primary_bindings,
            )
            subjective_mode = SubjectiveMode.AFFECTIVE_RESPONSE
            subjective_operator = SubjectiveOperator.FEEL_TOWARD
            assertion_modality = SubjectiveAssertionModality.EMLIS_FEELING
        elif content_kind is SubjectiveContentKind.APPRAISAL:
            appraisal_content = EmlisAppraisalContent(
                dimension=AppraisalDimension.MATERIAL_WEIGHT,
                operation=AppraisalOperation.RECEIVE_AS_MATERIAL,
                appraised_bindings=primary_bindings,
                focal_relation_ref=None,
                protected_bindings=(),
                basis_contribution_refs=("contribution-1",),
            )
            subjective_mode = SubjectiveMode.PERSONAL_APPRAISAL
            subjective_operator = SubjectiveOperator.APPRAISE_AS_MATERIAL
            assertion_modality = SubjectiveAssertionModality.EMLIS_APPRAISAL
        elif content_kind is SubjectiveContentKind.MATERIAL_VALUE:
            material_value_content = MaterialValueContent(
                value_applications=(
                    ValueApplication(
                        principle_ref=stage1_value_principle_ref("V1"),
                        material_risk=MaterialRisk.MINIMIZATION,
                        policy_application_row_refs=("policy-application-row-1",),
                        policy_basis_binding_refs=(policy_basis_rows[0].binding_ref,),
                        protected_subjective_binding_refs=primary_bindings,
                    ),
                ),
                target_bindings=primary_bindings,
                boundary_bindings=(),
            )
            subjective_mode = SubjectiveMode.VALUE_POSITION
            subjective_operator = SubjectiveOperator.PROTECT_VALUE_BOUNDARY
            assertion_modality = SubjectiveAssertionModality.EMLIS_VALUE_POSITION
        else:
            position_kind = (
                RelationalPositionKind.BOUNDED_COUNTERPOSITION
                if bounded_counterposition
                else RelationalPositionKind.STANCE
            )
            commitment = (
                RelationalCommitment.DECLINE_PROMOTION
                if bounded_counterposition
                else RelationalCommitment.STAY_WITH
            )
            relational_position = EmlisRelationalPosition(
                relational_position_kind=position_kind,
                stance_operator=StanceOperator.PROTECT_USER_AGENCY,
                target_bindings=primary_bindings,
                boundary_bindings=boundary_bindings,
                commitment=commitment,
                closure=(
                    RelationalClosure.BOUNDED
                    if bounded_counterposition
                    else RelationalClosure.NONE
                ),
            )
            if bounded_counterposition:
                focal_relation_ref = "relation-1"
                subjective_mode = SubjectiveMode.BOUNDED_COUNTERPOSITION
                subjective_operator = SubjectiveOperator.COUNTER_SPECIFIC_PROMOTION
                assertion_modality = (
                    SubjectiveAssertionModality.EMLIS_BOUNDED_REFUSAL
                )
            else:
                subjective_mode = SubjectiveMode.RELATIONAL_STANCE
                subjective_operator = SubjectiveOperator.TAKE_RELATIONAL_STANCE
                assertion_modality = (
                    SubjectiveAssertionModality.EMLIS_RELATIONAL_INTENTION
                )

        all_bindings = (*primary_bindings, *boundary_bindings)
        proposition = SubjectivePropositionV2(
            schema_version=dict(CMEE_STAGE1_FINAL_LOGICAL_ID_REGISTRY)[
                "CMEE_STAGE1_SUBJECTIVE_PROPOSITION_SCHEMA_VERSION"
            ],
            content_kind=content_kind,
            subjective_mode=subjective_mode,
            subjective_operator=subjective_operator,
            target_contribution_refs=tuple(
                row.contribution_ref for row in basis_rows
            ),
            primary_target_refs=(basis_rows[0].semantic_ref,),
            boundary_target_refs=tuple(
                row.semantic_ref for row in basis_rows[1:]
            ),
            response_object_refs=tuple(row.semantic_ref for row in basis_rows),
            basis_binding_refs=all_bindings,
            source_qualifier_binding_refs=tuple(
                row.source_qualifier_binding_ref for row in qualifier_rows
            ),
            focal_relation_ref=focal_relation_ref,
            affect_content=affect_content,
            appraisal_content=appraisal_content,
            material_value_content=material_value_content,
            relational_position=relational_position,
            referenced_actor_refs=("actor-user",),
            referenced_experiencer_refs=("experiencer-user",),
            addressee_role="USER",
            assertion_modality=assertion_modality,
            epistemic_scope="REQUEST_LOCAL_EMLIS_SUBJECTIVITY",
        )
        expected_forbidden_promotions = (
            *CMEE_STAGE1_SUBJECTIVE_FORBIDDEN_PROMOTIONS,
            *(("value-policy-suppression:V9",) if material_unknown else ()),
        )
        kwargs: dict[str, object] = {
            "projection_preimage_ref": projection_preimage_ref,
            "basis_rows": basis_rows,
            "qualifier_rows": qualifier_rows,
            "expected_basis_rows": basis_rows,
            "expected_qualifier_rows": qualifier_rows,
            "policy_basis_rows": tuple(policy_basis_rows),
            "expected_policy_basis_rows": tuple(policy_basis_rows),
            "allowed_contribution_refs": (
                "contribution-1",
                "contribution-2",
            ),
            "allowed_semantic_refs": ("semantic-1", "semantic-2"),
            "allowed_source_candidate_refs": ("candidate-1",),
            "allowed_policy_application_row_refs": (
                ("policy-application-row-1",)
                if content_kind is SubjectiveContentKind.MATERIAL_VALUE
                else ()
            ),
            "admitted_relation_refs": (
                ("relation-1",) if bounded_counterposition else ()
            ),
            "material_unknown_refs": material_unknown_refs,
            "expected_actor_refs": ("actor-user",),
            "expected_experiencer_refs": ("experiencer-user",),
            "expected_focal_relation_ref": focal_relation_ref,
            "owner_ref": dict(CMEE_STAGE1_FINAL_LOGICAL_ID_REGISTRY)[
                "CMEE_STAGE1_EMLIS_OWNER_REF"
            ],
            "speaker_owner": "EMLIS",
            "user_fact_effect": 0,
            "forbidden_promotions": expected_forbidden_promotions,
            "expected_forbidden_promotions": expected_forbidden_promotions,
        }
        return proposition, kwargs

    def test_step1_final_logical_ids_are_exact_and_disabled(self) -> None:
        expected = (
            ("CMEE_STAGE1_RESPONSE_SCHEMA_VERSION", "cocolon.cmee.v1a.emlis_stage1_response.v2"),
            ("CMEE_STAGE1_SUBJECTIVE_PROPOSITION_SCHEMA_VERSION", "cocolon.cmee.v1a.emlis_subjective_proposition.v2"),
            ("CMEE_STAGE1_COMPOSITION_POLICY_VERSION", "cocolon.emlis.stage1.discourse_composition.v1"),
            ("CMEE_STAGE1_NORMAL_FORM_VERSION", "cocolon.cmee.v1a.emlis_stage1_normal_form.v1"),
            ("CMEE_STAGE1_CONSTRUCTION_GRAMMAR_POLICY_VERSION", "cocolon.emlis.stage1.grounded_construction_grammar.v1"),
            ("CMEE_STAGE1_PROJECTION_PREIMAGE_REF_VERSION", "cocolon.cmee.v1a.emlis_stage1_projection_preimage_ref.v1"),
            ("CMEE_STAGE1_SUBJECTIVE_BASIS_BINDING_REF_VERSION", "cocolon.cmee.v1a.emlis_subjective_basis_binding_ref.v1"),
            ("CMEE_STAGE1_SOURCE_QUALIFIER_BINDING_REF_VERSION", "cocolon.cmee.v1a.emlis_source_qualifier_binding_ref.v1"),
            ("CMEE_STAGE1_POLICY_BASIS_BINDING_REF_VERSION", "cocolon.cmee.v1a.emlis_policy_basis_binding_ref.v1"),
            ("CMEE_STAGE1_POLICY_TARGET_KEY_VERSION", "cocolon.cmee.v1a.emlis_policy_target_key.v1"),
            ("CMEE_STAGE1_POLICY_APPLICATION_ROW_ID_VERSION", "cocolon.cmee.v1a.emlis_policy_application_row_id.v1"),
            ("CMEE_STAGE1_SUBJECTIVE_RESPONSIBILITY_REF_VERSION", "cocolon.cmee.v1a.emlis_subjective_responsibility_ref.v1"),
            ("CMEE_STAGE1_SUBJECTIVE_OPPORTUNITY_KEY_VERSION", "cocolon.cmee.v1a.emlis_subjective_opportunity_key.v1"),
            ("CMEE_STAGE1_ARC_DEPENDENCY_REF_VERSION", "cocolon.cmee.v1a.emlis_arc_dependency_ref.v1"),
            ("CMEE_STAGE1_DISCOURSE_ARC_REF_VERSION", "cocolon.cmee.v1a.emlis_stage1_discourse_arc_ref.v1"),
            ("CMEE_STAGE1_COMPOSITION_DUTY_REF_VERSION", "cocolon.cmee.v1a.emlis_composition_duty_ref.v1"),
            ("CMEE_STAGE1_REFERENCE_STATE_REF_VERSION", "cocolon.cmee.v1a.emlis_discourse_reference_state_ref.v2"),
            ("CMEE_STAGE1_CLAUSE_SCALAR_CONSTRAINT_REF_VERSION", "cocolon.cmee.v1a.emlis_clause_scalar_constraint_ref.v1"),
            ("CMEE_STAGE1_CLAUSE_INTENT_ID_VERSION", "cocolon.cmee.v1a.emlis_clause_intent_id.v1"),
            ("CMEE_STAGE1_CLAUSE_PLAN_ID_VERSION", "cocolon.cmee.v1a.emlis_clause_plan_id.v1"),
            ("CMEE_STAGE1_RESPONSE_OBJECT_EXPRESSION_ID_VERSION", "cocolon.cmee.v1a.emlis_response_object_expression_id.v1"),
            ("CMEE_STAGE1_PROFILE_EVIDENCE_REF_VERSION", "cocolon.cmee.v1a.emlis_profile_evidence_ref.v1"),
            ("CMEE_STAGE1_SEALED_UNIT_PLAN_ROW_ID_VERSION", "cocolon.cmee.v1a.emlis_sealed_unit_plan_row_id.v1"),
            ("CMEE_STAGE1_COMPOSITION_LAYOUT_ID_VERSION", "cocolon.cmee.v1a.emlis_composition_layout_id.v1"),
            ("CMEE_STAGE1_ARTIFACT_COMPOSITION_CANDIDATE_ID_VERSION", "cocolon.cmee.v1a.emlis_artifact_composition_candidate_id.v1"),
            ("CMEE_STAGE1_SELECTED_ARTIFACT_ID_VERSION", "cocolon.cmee.v1a.emlis_selected_stage1_artifact_id.v1"),
            ("CMEE_STAGE1_TRACE_EXTENSION_SCHEMA_VERSION", "cocolon.cmee.v1a.emlis_stage1_positive_trace_extension.v2"),
            ("CMEE_STAGE1_EMLIS_OWNER_REF", "owner:emlis@cocolon.cmee.v1a.emlis_stage1_response.v2"),
        )
        self.assertEqual(CMEE_STAGE1_FINAL_LOGICAL_ID_REGISTRY, expected)
        validate_stage1_final_logical_id_registry()
        self.assertEqual(
            CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
            "cocolon.cmee.v1a.emlis_stage1_response.v1",
        )
        self.assertEqual(
            CMEE_STAGE1_TRACE_EXTENSION_SCHEMA_VERSION,
            "cocolon.cmee.v1a.emlis_stage1_positive_trace_extension.v1",
        )
        self.assertEqual(
            CMEE_STAGE1_EMLIS_OWNER_REF,
            "owner:emlis@cocolon.cmee.v1a.emlis_stage1_response.v1",
        )
        self.assertTrue(
            set(value for _name, value in expected).isdisjoint(
                emlis_v1a_module.REALIZER_CONTRACT_IDS
            )
        )
        self.assertNotIn(
            dict(expected)["CMEE_STAGE1_TRACE_EXTENSION_SCHEMA_VERSION"],
            emlis_v1a_module.TRUST_POLICY_IDS,
        )

    def test_step1_minimum_lineage_id_preimages_are_field_sensitive(self) -> None:
        projection_inputs: dict[str, object] = {
            "grounded_graph_ref": "graph-1",
            "parent_observation_duty_ref": "observation-duty-1",
            "parent_reception_duty_ref": "reception-duty-1",
            "interpretation_candidate_ids": ("candidate-1",),
            "meaning_field_id": "meaning-field-1",
            "observation_contribution_ids": ("contribution-1",),
            "retained_reception_act_ids": ("act-1",),
            "observation_depth_class": ObservationDepthClass.FOCUSED,
            "temperature_class": TemperatureClass.STANDARD,
            "reception_style_policy_ref": "policy:style@cocolon.style.v1",
            "emlis_value_policy_ref": CMEE_STAGE1_VALUE_POLICY_REF,
        }
        projection_mutations = (
            {"grounded_graph_ref": "graph-2"},
            {"parent_observation_duty_ref": "observation-duty-2"},
            {"parent_reception_duty_ref": "reception-duty-2"},
            {"interpretation_candidate_ids": ("candidate-2",)},
            {"meaning_field_id": "meaning-field-2"},
            {"observation_contribution_ids": ("contribution-2",)},
            {"retained_reception_act_ids": ("act-2",)},
            {"observation_depth_class": ObservationDepthClass.LAYERED},
            {"temperature_class": TemperatureClass.ELEVATED_NON_SAFETY},
            {"reception_style_policy_ref": "policy:other@cocolon.style.v1"},
            {
                "emlis_value_policy_ref": (
                    "policy:other@cocolon.emlis.stage1.value_policy.v1"
                )
            },
        )
        projection_refs = (
            project_stage1_projection_preimage_ref(**projection_inputs),
            *(
                project_stage1_projection_preimage_ref(
                    **{**projection_inputs, **mutation}
                )
                for mutation in projection_mutations
            ),
        )
        self.assertEqual(len(projection_refs), len(set(projection_refs)))

        projection_ref = projection_refs[0]
        basis_inputs = {
            "projection_preimage_ref": projection_ref,
            "contribution_ref": "contribution-1",
            "semantic_ref": "semantic-1",
            "role": SubjectiveBasisRole.ELICITOR,
        }
        basis_refs = (
            project_stage1_subjective_basis_binding_ref(**basis_inputs),
            project_stage1_subjective_basis_binding_ref(
                **{**basis_inputs, "projection_preimage_ref": projection_refs[1]}
            ),
            project_stage1_subjective_basis_binding_ref(
                **{**basis_inputs, "contribution_ref": "contribution-2"}
            ),
            project_stage1_subjective_basis_binding_ref(
                **{**basis_inputs, "semantic_ref": "semantic-2"}
            ),
            project_stage1_subjective_basis_binding_ref(
                **{**basis_inputs, "role": SubjectiveBasisRole.APPRAISED_OBJECT}
            ),
        )
        self.assertEqual(len(basis_refs), len(set(basis_refs)))

        qualifier_inputs = {
            "projection_preimage_ref": projection_ref,
            "basis_binding_ref": basis_refs[0],
            "source_candidate_ref": "candidate-1",
            "source_argument_role": None,
            "canonical_qualifier_codes": (
                "polarity:POSITIVE", "modality:ACTUAL",
                "time_scope:CURRENT",
            ),
            "polarity": "POSITIVE",
            "modality": "ACTUAL",
            "time_scope": "CURRENT",
        }
        qualifier_mutations = (
            {"projection_preimage_ref": projection_refs[1]},
            {"basis_binding_ref": basis_refs[1]},
            {"source_candidate_ref": "candidate-2"},
            {
                "source_argument_role": ArgumentRole.LEFT,
                "canonical_qualifier_codes": (
                    "left_polarity:POSITIVE", "left_modality:ACTUAL",
                    "left_time_scope:CURRENT",
                ),
            },
            {
                "canonical_qualifier_codes": (
                    "polarity:NEGATIVE", "modality:ACTUAL",
                    "time_scope:CURRENT",
                ),
                "polarity": "NEGATIVE",
            },
            {
                "canonical_qualifier_codes": (
                    "polarity:POSITIVE", "modality:POSSIBLE",
                    "time_scope:CURRENT",
                ),
                "modality": "POSSIBLE",
            },
            {
                "canonical_qualifier_codes": (
                    "polarity:POSITIVE", "modality:ACTUAL",
                    "time_scope:PAST",
                ),
                "time_scope": "PAST",
            },
        )
        qualifier_refs = (
            project_stage1_source_qualifier_binding_ref(**qualifier_inputs),
            *(
                project_stage1_source_qualifier_binding_ref(
                    **{**qualifier_inputs, **mutation}
                )
                for mutation in qualifier_mutations
            ),
        )
        self.assertEqual(len(qualifier_refs), len(set(qualifier_refs)))
        with self.assertRaisesRegex(
            CMEEStage1ContractError, "source_qualifier_binding_invalid"
        ):
            project_stage1_source_qualifier_binding_ref(
                **{
                    **qualifier_inputs,
                    "canonical_qualifier_codes": (
                        "polarity:POSITIVE", "polarity:POSITIVE",
                        "time_scope:CURRENT",
                    ),
                }
            )

        policy_inputs = {
            "projection_preimage_ref": projection_ref,
            "owner_kind": PolicyBasisOwnerKind.CONTRIBUTION,
            "owner_ref": "contribution-1",
            "role": PolicyBasisRole.BURDEN_OR_RESIDUE,
        }
        policy_refs = (
            project_stage1_policy_basis_binding_ref(**policy_inputs),
            project_stage1_policy_basis_binding_ref(
                **{**policy_inputs, "projection_preimage_ref": projection_refs[1]}
            ),
            project_stage1_policy_basis_binding_ref(
                **{
                    **policy_inputs,
                    "owner_kind": PolicyBasisOwnerKind.MATERIAL_UNKNOWN,
                }
            ),
            project_stage1_policy_basis_binding_ref(
                **{**policy_inputs, "owner_ref": "contribution-2"}
            ),
            project_stage1_policy_basis_binding_ref(
                **{**policy_inputs, "role": PolicyBasisRole.DIRECTION}
            ),
        )
        self.assertEqual(len(policy_refs), len(set(policy_refs)))

    def test_step1_subjective_v2_fields_are_exact_and_not_aliased(self) -> None:
        self.assertEqual(
            tuple(row.name for row in fields(SubjectivePropositionV2)),
            (
                "schema_version", "content_kind", "subjective_mode",
                "subjective_operator", "target_contribution_refs",
                "primary_target_refs", "boundary_target_refs",
                "response_object_refs", "basis_binding_refs",
                "source_qualifier_binding_refs", "focal_relation_ref",
                "affect_content", "appraisal_content", "material_value_content",
                "relational_position", "referenced_actor_refs",
                "referenced_experiencer_refs", "addressee_role",
                "assertion_modality", "epistemic_scope",
            ),
        )
        self.assertIsNot(SubjectiveProposition, SubjectivePropositionV2)
        contracts_source = inspect.getsource(contracts_module)
        for forbidden_declaration in (
            "class SubjectiveMeaningArtifact",
            "class ClauseFrameV2",
            "class EmlisStage1PositiveTraceExtensionV2",
            "SubjectiveProposition = SubjectivePropositionV2",
        ):
            self.assertNotIn(forbidden_declaration, contracts_source)
        for active_callable in (
            build_stage1_semantic_projection,
            stage1_response_module.compile_stage1_response,
        ):
            with self.subTest(active_callable=active_callable.__name__):
                self.assertNotIn(
                    "SubjectivePropositionV2",
                    inspect.getsource(active_callable),
                )
        self.assertNotIn("SubjectivePropositionV2", inspect.getsource(emlis_v1a_module))

    def test_step1_supporting_types_and_enums_are_literal_exact(self) -> None:
        expected_fields = {
            SubjectiveBasisBinding: (
                "projection_preimage_ref", "binding_ref", "contribution_ref",
                "semantic_ref", "role",
            ),
            SourceQualifierBinding: (
                "projection_preimage_ref", "source_qualifier_binding_ref",
                "basis_binding_ref", "source_candidate_ref",
                "source_argument_role", "canonical_qualifier_codes",
                "polarity", "modality", "time_scope",
            ),
            PolicyBasisBinding: (
                "projection_preimage_ref", "binding_ref", "owner_kind",
                "owner_ref", "role",
            ),
            EmlisAffectContent: (
                "category", "intensity", "elicitor_bindings",
            ),
            EmlisAppraisalContent: (
                "dimension", "operation", "appraised_bindings",
                "focal_relation_ref", "protected_bindings",
                "basis_contribution_refs",
            ),
            ValueApplication: (
                "principle_ref", "material_risk",
                "policy_application_row_refs", "policy_basis_binding_refs",
                "protected_subjective_binding_refs",
            ),
            MaterialValueContent: (
                "value_applications", "target_bindings", "boundary_bindings",
            ),
            EmlisRelationalPosition: (
                "relational_position_kind", "stance_operator",
                "target_bindings", "boundary_bindings", "commitment",
                "closure",
            ),
            SurfaceDerivation: (
                "derivation_kind", "source_or_claim_refs", "emlis_owner_ref",
                "relation_or_clause_plan_refs", "qualifier_refs",
                "response_object_expression_ref", "antecedent_unit_ref",
                "participant_role_ref", "evidence_refs", "rule_ref",
                "input_scalar_ranges",
            ),
        }
        for contract_type, exact_fields in expected_fields.items():
            with self.subTest(contract=contract_type.__name__):
                self.assertEqual(
                    tuple(row.name for row in fields(contract_type)),
                    exact_fields,
                )
                self.assertTrue(contract_type.__dataclass_params__.frozen)
                self.assertEqual(contract_type.__slots__, exact_fields)

        expected_enum_values = {
            SubjectiveContentKind: (
                "AFFECT", "APPRAISAL", "MATERIAL_VALUE",
                "RELATIONAL_POSITION",
            ),
            SubjectiveAssertionModality: (
                "EMLIS_FEELING", "EMLIS_APPRAISAL", "EMLIS_VALUE_POSITION",
                "EMLIS_RELATIONAL_INTENTION", "EMLIS_BOUNDED_REFUSAL",
            ),
            SubjectiveBasisRole: (
                "ELICITOR", "APPRAISED_OBJECT", "RELATION_LEFT",
                "RELATION_RIGHT", "ACTION", "CHANGE", "BEFORE", "AFTER",
                "RESIDUE", "UNFINISHED", "CHOICE_TARGET",
            ),
            PolicyBasisOwnerKind: ("CONTRIBUTION", "MATERIAL_UNKNOWN"),
            PolicyBasisRole: (
                "BURDEN_OR_RESIDUE", "DIRECTION",
                "CHANGE_OR_ACTUAL_OUTPUT", "COEXISTENCE_OR_TENSION",
                "UNFINISHED", "VISIBILITY_ACT_BASIS", "MATERIAL_UNKNOWN",
            ),
            AppraisalDimension: (
                "MATERIAL_WEIGHT", "RELATIONAL_NONCOLLAPSE", "BOUNDED_CHANGE",
                "UNFINISHED_OPENNESS", "AGENCY_BOUNDARY",
            ),
            AppraisalOperation: (
                "RECEIVE_AS_MATERIAL", "PRESERVE_BOTH_ENDPOINTS",
                "RECOGNIZE_AS_BOUNDED", "LEAVE_UNFINISHED",
                "RESPECT_CHOICE",
            ),
            MaterialRisk: (
                "MINIMIZATION", "WISH_TO_OBLIGATION", "NO_RESULT_TO_NO_VALUE",
                "SINGLE_EVENT_TO_IDENTITY",
                "BOUNDED_CHANGE_TO_UNIVERSAL_SOLUTION",
                "ONE_SIDE_TO_TRUE_SELF", "POSSIBILITY_TO_FACT",
                "REMOVE_USER_AGENCY", "UNKNOWN_TO_FALSE_UNDERSTANDING",
            ),
            RelationalPositionKind: ("STANCE", "BOUNDED_COUNTERPOSITION"),
            RelationalCommitment: (
                "AFFIRM_SOURCE_BOUND_DIRECTION", "STAY_WITH", "HOLD_OPEN",
                "WELCOME_BOUNDED_CHANGE", "PROTECT_AGENCY",
                "DECLINE_PROMOTION",
            ),
            RelationalClosure: ("NONE", "BOUNDED", "OPEN"),
            SurfaceDerivationKind: (
                "LITERAL_SUBSPAN", "NORMALIZED_INFLECTION",
                "COMPOSITIONAL_JOIN", "REGISTERED_EMLIS_LEXEME",
                "REGISTERED_PARTICIPANT_LEXEME",
                "REGISTERED_STRUCTURAL_ASSET", "PROJECTED_RESPONSE_OBJECT",
                "PROJECTED_FUNCTIONAL_ASSET",
            ),
        }
        for enum_type, exact_values in expected_enum_values.items():
            with self.subTest(enum=enum_type.__name__):
                self.assertEqual(tuple(enum_type.__members__), exact_values)
                self.assertEqual(
                    tuple(member.value for member in enum_type),
                    exact_values,
                )
                self.assertEqual(len(enum_type.__members__), len(enum_type))

    def test_step1_subjective_v2_exact_derivation_matrix_accepts(self) -> None:
        cases = (
            (SubjectiveContentKind.AFFECT, False),
            (SubjectiveContentKind.APPRAISAL, False),
            (SubjectiveContentKind.MATERIAL_VALUE, False),
            (SubjectiveContentKind.RELATIONAL_POSITION, False),
            (SubjectiveContentKind.RELATIONAL_POSITION, True),
        )
        for kind, counterposition in cases:
            with self.subTest(kind=kind, counterposition=counterposition):
                proposition, kwargs = self._valid_subjective_v2(
                    kind,
                    bounded_counterposition=counterposition,
                )
                validate_subjective_proposition_v2(proposition, **kwargs)

    def test_step1_subjective_v2_rejects_union_and_derived_tamper(self) -> None:
        proposition, kwargs = self._valid_subjective_v2(SubjectiveContentKind.AFFECT)
        with self.assertRaisesRegex(
            CMEEStage1ContractError, "subjective_v2_schema_invalid"
        ):
            validate_subjective_proposition_v2(
                replace(proposition, schema_version=CMEE_STAGE1_RESPONSE_SCHEMA_VERSION),
                **kwargs,
            )
        with self.assertRaisesRegex(
            CMEEStage1ContractError, "content_discriminant_invalid"
        ):
            validate_subjective_proposition_v2(
                replace(proposition, affect_content=None),
                **kwargs,
            )
        with self.assertRaisesRegex(
            CMEEStage1ContractError, "content_discriminant_invalid"
        ):
            validate_subjective_proposition_v2(
                replace(
                    proposition,
                    content_kind=SubjectiveContentKind.APPRAISAL,
                ),
                **kwargs,
            )
        with self.assertRaisesRegex(
            CMEEStage1ContractError, "content_discriminant_invalid"
        ):
            validate_subjective_proposition_v2(
                replace(
                    proposition,
                    appraisal_content=EmlisAppraisalContent(
                        dimension=AppraisalDimension.MATERIAL_WEIGHT,
                        operation=AppraisalOperation.RECEIVE_AS_MATERIAL,
                        appraised_bindings=proposition.basis_binding_refs,
                        focal_relation_ref=None,
                        protected_bindings=(),
                        basis_contribution_refs=proposition.target_contribution_refs,
                    ),
                ),
                **kwargs,
            )
        for field_name, value in (
            ("subjective_mode", SubjectiveMode.ATTENTION),
            ("subjective_operator", SubjectiveOperator.ATTEND_TO),
            (
                "assertion_modality",
                SubjectiveAssertionModality.EMLIS_APPRAISAL,
            ),
        ):
            with self.subTest(field=field_name), self.assertRaisesRegex(
                CMEEStage1ContractError, "derived_field_invalid"
            ):
                validate_subjective_proposition_v2(
                    replace(proposition, **{field_name: value}),
                    **kwargs,
                )

        counter, counter_kwargs = self._valid_subjective_v2(
            SubjectiveContentKind.RELATIONAL_POSITION,
            bounded_counterposition=True,
        )
        assert counter.relational_position is not None
        for relational_mutation in (
            replace(
                counter.relational_position,
                commitment=RelationalCommitment.STAY_WITH,
            ),
            replace(
                counter.relational_position,
                relational_position_kind=RelationalPositionKind.STANCE,
            ),
        ):
            with self.subTest(
                relational_mutation=relational_mutation
            ), self.assertRaisesRegex(
                CMEEStage1ContractError, "derived_field_invalid"
            ):
                validate_subjective_proposition_v2(
                    replace(counter, relational_position=relational_mutation),
                    **counter_kwargs,
                )

    def test_step1_subjective_v2_rejects_generic_content(self) -> None:
        proposition, kwargs = self._valid_subjective_v2(SubjectiveContentKind.AFFECT)
        assert proposition.affect_content is not None
        with self.assertRaisesRegex(
            CMEEStage1ContractError, "GENERIC_SUBJECTIVE_CONTENT_STOP"
        ):
            validate_subjective_proposition_v2(
                replace(
                    proposition,
                    affect_content=replace(
                        proposition.affect_content,
                        elicitor_bindings=(),
                    ),
                ),
                **kwargs,
            )
        appraisal, appraisal_kwargs = self._valid_subjective_v2(
            SubjectiveContentKind.APPRAISAL
        )
        material, material_kwargs = self._valid_subjective_v2(
            SubjectiveContentKind.MATERIAL_VALUE
        )
        relational, relational_kwargs = self._valid_subjective_v2(
            SubjectiveContentKind.RELATIONAL_POSITION
        )
        assert appraisal.appraisal_content is not None
        assert material.material_value_content is not None
        assert relational.relational_position is not None
        generic_rows = (
            (
                replace(
                    appraisal,
                    appraisal_content=replace(
                        appraisal.appraisal_content,
                        appraised_bindings=(),
                    ),
                ),
                appraisal_kwargs,
            ),
            (
                replace(
                    material,
                    material_value_content=replace(
                        material.material_value_content,
                        value_applications=(),
                    ),
                ),
                material_kwargs,
            ),
            (
                replace(
                    relational,
                    relational_position=replace(
                        relational.relational_position,
                        target_bindings=(),
                    ),
                ),
                relational_kwargs,
            ),
        )
        for generic_proposition, generic_kwargs in generic_rows:
            with self.subTest(kind=generic_proposition.content_kind), self.assertRaisesRegex(
                CMEEStage1ContractError, "GENERIC_SUBJECTIVE_CONTENT_STOP"
            ):
                validate_subjective_proposition_v2(
                    generic_proposition,
                    **generic_kwargs,
                )

    def test_step1_subjective_v2_basis_and_qualifier_are_exact_cover(self) -> None:
        proposition, kwargs = self._valid_subjective_v2(SubjectiveContentKind.AFFECT)
        with self.assertRaisesRegex(
            CMEEStage1ContractError, "qualifier_exact_cover_invalid"
        ):
            validate_subjective_proposition_v2(
                proposition,
                **{**kwargs, "qualifier_rows": ()},
            )
        qualifier = kwargs["qualifier_rows"][0]
        with self.assertRaisesRegex(
            CMEEStage1ContractError, "qualifier_exact_cover_invalid"
        ):
            validate_subjective_proposition_v2(
                proposition,
                **{
                    **kwargs,
                    "qualifier_rows": (replace(qualifier, modality="POSSIBLE"),),
                },
            )

        rehashed_codes = (
            "polarity:POSITIVE",
            "modality:POSSIBLE",
            "time_scope:CURRENT",
        )
        rehashed_qualifier = replace(
            qualifier,
            modality="POSSIBLE",
            canonical_qualifier_codes=rehashed_codes,
            source_qualifier_binding_ref=(
                project_stage1_source_qualifier_binding_ref(
                    projection_preimage_ref=qualifier.projection_preimage_ref,
                    basis_binding_ref=qualifier.basis_binding_ref,
                    source_candidate_ref=qualifier.source_candidate_ref,
                    source_argument_role=qualifier.source_argument_role,
                    canonical_qualifier_codes=rehashed_codes,
                    polarity=qualifier.polarity,
                    modality="POSSIBLE",
                    time_scope=qualifier.time_scope,
                )
            ),
        )
        with self.assertRaisesRegex(
            CMEEStage1ContractError, "qualifier_exact_cover_invalid"
        ):
            validate_subjective_proposition_v2(
                replace(
                    proposition,
                    source_qualifier_binding_refs=(
                        rehashed_qualifier.source_qualifier_binding_ref,
                    ),
                ),
                **{**kwargs, "qualifier_rows": (rehashed_qualifier,)},
            )

        basis = kwargs["basis_rows"][0]
        cross_bound_basis = replace(
            basis,
            semantic_ref="semantic-2",
            binding_ref=project_stage1_subjective_basis_binding_ref(
                projection_preimage_ref=basis.projection_preimage_ref,
                contribution_ref=basis.contribution_ref,
                semantic_ref="semantic-2",
                role=basis.role,
            ),
        )
        cross_bound_qualifier = replace(
            qualifier,
            basis_binding_ref=cross_bound_basis.binding_ref,
            source_qualifier_binding_ref=(
                project_stage1_source_qualifier_binding_ref(
                    projection_preimage_ref=qualifier.projection_preimage_ref,
                    basis_binding_ref=cross_bound_basis.binding_ref,
                    source_candidate_ref=qualifier.source_candidate_ref,
                    source_argument_role=qualifier.source_argument_role,
                    canonical_qualifier_codes=qualifier.canonical_qualifier_codes,
                    polarity=qualifier.polarity,
                    modality=qualifier.modality,
                    time_scope=qualifier.time_scope,
                )
            ),
        )
        assert proposition.affect_content is not None
        with self.assertRaisesRegex(
            CMEEStage1ContractError, "basis_exact_cover_invalid"
        ):
            validate_subjective_proposition_v2(
                replace(
                    proposition,
                    primary_target_refs=("semantic-2",),
                    response_object_refs=("semantic-2",),
                    basis_binding_refs=(cross_bound_basis.binding_ref,),
                    source_qualifier_binding_refs=(
                        cross_bound_qualifier.source_qualifier_binding_ref,
                    ),
                    affect_content=replace(
                        proposition.affect_content,
                        elicitor_bindings=(cross_bound_basis.binding_ref,),
                    ),
                ),
                **{
                    **kwargs,
                    "basis_rows": (cross_bound_basis,),
                    "qualifier_rows": (cross_bound_qualifier,),
                },
            )

    def test_step1_subjective_v2_relation_qualifier_roles_are_exact(self) -> None:
        proposition, kwargs = self._valid_subjective_v2(
            SubjectiveContentKind.RELATIONAL_POSITION,
            bounded_counterposition=True,
        )
        roles = (ArgumentRole.LEFT, ArgumentRole.RIGHT)
        def relation_qualifier(
            row: SourceQualifierBinding,
            role: ArgumentRole,
        ) -> SourceQualifierBinding:
            qualifier_codes = (
                f"{role.value.lower()}_polarity:{row.polarity}",
                f"{role.value.lower()}_modality:{row.modality}",
                f"{role.value.lower()}_time_scope:{row.time_scope}",
            )
            return replace(
                row,
                source_argument_role=role,
                canonical_qualifier_codes=qualifier_codes,
                source_qualifier_binding_ref=(
                    project_stage1_source_qualifier_binding_ref(
                        projection_preimage_ref=row.projection_preimage_ref,
                        basis_binding_ref=row.basis_binding_ref,
                        source_candidate_ref=row.source_candidate_ref,
                        source_argument_role=role,
                        canonical_qualifier_codes=qualifier_codes,
                        polarity=row.polarity,
                        modality=row.modality,
                        time_scope=row.time_scope,
                    )
                ),
            )
        relation_qualifiers = tuple(
            relation_qualifier(row, role)
            for row, role in zip(kwargs["qualifier_rows"], roles, strict=True)
        )
        relation_proposition = replace(
            proposition,
            source_qualifier_binding_refs=tuple(
                row.source_qualifier_binding_ref for row in relation_qualifiers
            ),
        )
        validate_subjective_proposition_v2(
            relation_proposition,
            **{
                **kwargs,
                "qualifier_rows": relation_qualifiers,
                "expected_qualifier_rows": relation_qualifiers,
            },
        )
        first = relation_qualifiers[0]
        swapped_codes = (
            f"right_polarity:{first.polarity}",
            f"right_modality:{first.modality}",
            f"right_time_scope:{first.time_scope}",
        )
        swapped = replace(
            first,
            source_argument_role=ArgumentRole.RIGHT,
            canonical_qualifier_codes=swapped_codes,
            source_qualifier_binding_ref=project_stage1_source_qualifier_binding_ref(
                projection_preimage_ref=first.projection_preimage_ref,
                basis_binding_ref=first.basis_binding_ref,
                source_candidate_ref=first.source_candidate_ref,
                source_argument_role=ArgumentRole.RIGHT,
                canonical_qualifier_codes=swapped_codes,
                polarity=first.polarity,
                modality=first.modality,
                time_scope=first.time_scope,
            ),
        )
        with self.assertRaisesRegex(
            CMEEStage1ContractError, "qualifier_exact_cover_invalid"
        ):
            validate_subjective_proposition_v2(
                replace(
                    relation_proposition,
                    source_qualifier_binding_refs=(
                        swapped.source_qualifier_binding_ref,
                        relation_qualifiers[1].source_qualifier_binding_ref,
                    ),
                ),
                **{
                    **kwargs,
                    "qualifier_rows": (swapped, relation_qualifiers[1]),
                    "expected_qualifier_rows": relation_qualifiers,
                },
            )

    def test_step1_subjective_v2_target_projection_is_exact(self) -> None:
        proposition, kwargs = self._valid_subjective_v2(SubjectiveContentKind.AFFECT)
        mutations = (
            replace(proposition, target_contribution_refs=("contribution-2",)),
            replace(proposition, primary_target_refs=("semantic-2",)),
            replace(proposition, boundary_target_refs=("semantic-2",)),
            replace(proposition, response_object_refs=("semantic-2",)),
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation), self.assertRaisesRegex(
                CMEEStage1ContractError, "target_projection_invalid"
            ):
                validate_subjective_proposition_v2(mutation, **kwargs)

        relation, relation_kwargs = self._valid_subjective_v2(
            SubjectiveContentKind.RELATIONAL_POSITION,
            bounded_counterposition=True,
        )
        relation_basis = relation_kwargs["basis_rows"]
        relation_qualifiers = relation_kwargs["qualifier_rows"]
        duplicate_semantic_basis = replace(
            relation_basis[1],
            semantic_ref=relation_basis[0].semantic_ref,
            binding_ref=project_stage1_subjective_basis_binding_ref(
                projection_preimage_ref=relation_basis[1].projection_preimage_ref,
                contribution_ref=relation_basis[1].contribution_ref,
                semantic_ref=relation_basis[0].semantic_ref,
                role=relation_basis[1].role,
            ),
        )
        duplicate_semantic_qualifier = replace(
            relation_qualifiers[1],
            basis_binding_ref=duplicate_semantic_basis.binding_ref,
            source_qualifier_binding_ref=project_stage1_source_qualifier_binding_ref(
                projection_preimage_ref=relation_qualifiers[1].projection_preimage_ref,
                basis_binding_ref=duplicate_semantic_basis.binding_ref,
                source_candidate_ref=relation_qualifiers[1].source_candidate_ref,
                source_argument_role=relation_qualifiers[1].source_argument_role,
                canonical_qualifier_codes=relation_qualifiers[1].canonical_qualifier_codes,
                polarity=relation_qualifiers[1].polarity,
                modality=relation_qualifiers[1].modality,
                time_scope=relation_qualifiers[1].time_scope,
            ),
        )
        duplicate_basis_rows = (relation_basis[0], duplicate_semantic_basis)
        duplicate_qualifier_rows = (
            relation_qualifiers[0], duplicate_semantic_qualifier,
        )
        assert relation.relational_position is not None
        with self.assertRaisesRegex(
            CMEEStage1ContractError, "target_projection_invalid"
        ):
            validate_subjective_proposition_v2(
                replace(
                    relation,
                    boundary_target_refs=(relation_basis[0].semantic_ref,),
                    response_object_refs=(
                        relation_basis[0].semantic_ref,
                        relation_basis[0].semantic_ref,
                    ),
                    basis_binding_refs=(
                        relation_basis[0].binding_ref,
                        duplicate_semantic_basis.binding_ref,
                    ),
                    source_qualifier_binding_refs=(
                        relation_qualifiers[0].source_qualifier_binding_ref,
                        duplicate_semantic_qualifier.source_qualifier_binding_ref,
                    ),
                    relational_position=replace(
                        relation.relational_position,
                        boundary_bindings=(duplicate_semantic_basis.binding_ref,),
                    ),
                ),
                **{
                    **relation_kwargs,
                    "basis_rows": duplicate_basis_rows,
                    "expected_basis_rows": duplicate_basis_rows,
                    "qualifier_rows": duplicate_qualifier_rows,
                    "expected_qualifier_rows": duplicate_qualifier_rows,
                },
            )

    def test_step1_subjective_v2_owner_and_safety_are_fail_closed(self) -> None:
        proposition, kwargs = self._valid_subjective_v2(SubjectiveContentKind.AFFECT)
        for patch_kwargs in (
            {"owner_ref": CMEE_STAGE1_EMLIS_OWNER_REF},
            {"speaker_owner": "USER"},
            {"user_fact_effect": 1},
            {"forbidden_promotions": ("generic-subjective-claim",)},
            {
                "forbidden_promotions": tuple(
                    reversed(CMEE_STAGE1_SUBJECTIVE_FORBIDDEN_PROMOTIONS)
                )
            },
            {
                "forbidden_promotions": (
                    *CMEE_STAGE1_SUBJECTIVE_FORBIDDEN_PROMOTIONS,
                    "value-policy-suppression:V9",
                )
            },
            {
                "forbidden_promotions": (
                    *CMEE_STAGE1_SUBJECTIVE_FORBIDDEN_PROMOTIONS,
                    "value-policy-suppression:V10",
                )
            },
        ):
            with self.subTest(patch=patch_kwargs), self.assertRaisesRegex(
                CMEEStage1ContractError, "cross_owner_invalid"
            ):
                validate_subjective_proposition_v2(
                    proposition,
                    **{**kwargs, **patch_kwargs},
                )
        for proposition_patch in (
            {"referenced_actor_refs": ("foreign-actor",)},
            {"referenced_experiencer_refs": ("foreign-experiencer",)},
            {"addressee_role": "OTHER"},
            {"epistemic_scope": "USER_FACT"},
        ):
            with self.subTest(patch=proposition_patch), self.assertRaisesRegex(
                CMEEStage1ContractError, "cross_owner_invalid"
            ):
                validate_subjective_proposition_v2(
                    replace(proposition, **proposition_patch),
                    **kwargs,
                )

    def test_step1_material_unknown_is_policy_only(self) -> None:
        proposition, kwargs = self._valid_subjective_v2(
            SubjectiveContentKind.AFFECT,
            material_unknown=True,
        )
        validate_subjective_proposition_v2(proposition, **kwargs)
        with self.assertRaisesRegex(
            CMEEStage1ContractError, "cross_owner_invalid"
        ):
            validate_subjective_proposition_v2(
                proposition,
                **{
                    **kwargs,
                    "forbidden_promotions": (
                        CMEE_STAGE1_SUBJECTIVE_FORBIDDEN_PROMOTIONS
                    ),
                },
            )
        validate_subjective_proposition_v2(
            proposition,
            **{
                **kwargs,
                "policy_basis_rows": (),
                "expected_policy_basis_rows": (),
            },
        )
        basis = kwargs["basis_rows"][0]
        promoted_ref = project_stage1_subjective_basis_binding_ref(
            projection_preimage_ref=basis.projection_preimage_ref,
            contribution_ref="unknown-1",
            semantic_ref=basis.semantic_ref,
            role=basis.role,
        )
        promoted_basis = replace(
            basis,
            binding_ref=promoted_ref,
            contribution_ref="unknown-1",
        )
        with self.assertRaisesRegex(
            CMEEStage1ContractError, "material_unknown_promotion_invalid"
        ):
            validate_subjective_proposition_v2(
                proposition,
                **{
                    **kwargs,
                    "basis_rows": (promoted_basis,),
                    "expected_basis_rows": (promoted_basis,),
                    "allowed_contribution_refs": ("contribution-1", "unknown-1"),
                },
            )

    def test_step1_material_value_and_focal_relation_are_bound(self) -> None:
        proposition, kwargs = self._valid_subjective_v2(
            SubjectiveContentKind.MATERIAL_VALUE
        )
        validate_subjective_proposition_v2(proposition, **kwargs)
        assert proposition.material_value_content is not None
        application = proposition.material_value_content.value_applications[0]
        original_policy_basis = kwargs["policy_basis_rows"][0]
        rehashed_policy_basis = replace(
            original_policy_basis,
            role=PolicyBasisRole.DIRECTION,
            binding_ref=project_stage1_policy_basis_binding_ref(
                projection_preimage_ref=original_policy_basis.projection_preimage_ref,
                owner_kind=original_policy_basis.owner_kind,
                owner_ref=original_policy_basis.owner_ref,
                role=PolicyBasisRole.DIRECTION,
            ),
        )
        with self.assertRaisesRegex(
            CMEEStage1ContractError, "policy_basis_binding_invalid"
        ):
            validate_subjective_proposition_v2(
                replace(
                    proposition,
                    material_value_content=replace(
                        proposition.material_value_content,
                        value_applications=(
                            replace(
                                application,
                                policy_basis_binding_refs=(
                                    rehashed_policy_basis.binding_ref,
                                ),
                            ),
                        ),
                    ),
                ),
                **{**kwargs, "policy_basis_rows": (rehashed_policy_basis,)},
            )
        with self.assertRaisesRegex(
            CMEEStage1ContractError, "cross_owner_invalid"
        ):
            validate_subjective_proposition_v2(
                replace(
                    proposition,
                    material_value_content=replace(
                        proposition.material_value_content,
                        value_applications=(
                            replace(
                                application,
                                policy_basis_binding_refs=("foreign-policy-basis",),
                            ),
                        ),
                    ),
                ),
                **kwargs,
            )
        with self.assertRaisesRegex(
            CMEEStage1ContractError, "cross_owner_invalid"
        ):
            validate_subjective_proposition_v2(
                replace(
                    proposition,
                    material_value_content=replace(
                        proposition.material_value_content,
                        value_applications=(
                            replace(
                                application,
                                principle_ref=stage1_value_principle_ref("V9"),
                                material_risk=MaterialRisk.UNKNOWN_TO_FALSE_UNDERSTANDING,
                            ),
                        ),
                    ),
                ),
                **kwargs,
            )
        shared_row_application = replace(
            application,
            principle_ref=stage1_value_principle_ref("V2"),
            material_risk=MaterialRisk.WISH_TO_OBLIGATION,
        )
        with self.assertRaisesRegex(
            CMEEStage1ContractError, "cross_owner_invalid"
        ):
            validate_subjective_proposition_v2(
                replace(
                    proposition,
                    material_value_content=replace(
                        proposition.material_value_content,
                        value_applications=(application, shared_row_application),
                    ),
                ),
                **kwargs,
            )

        unknown_proposition, unknown_kwargs = self._valid_subjective_v2(
            SubjectiveContentKind.MATERIAL_VALUE,
            material_unknown=True,
        )
        assert unknown_proposition.material_value_content is not None
        unknown_application = (
            unknown_proposition.material_value_content.value_applications[0]
        )
        unknown_policy_basis = unknown_kwargs["policy_basis_rows"][1]
        with self.assertRaisesRegex(
            CMEEStage1ContractError, "cross_owner_invalid"
        ):
            validate_subjective_proposition_v2(
                replace(
                    unknown_proposition,
                    material_value_content=replace(
                        unknown_proposition.material_value_content,
                        value_applications=(
                            replace(
                                unknown_application,
                                policy_basis_binding_refs=(
                                    unknown_policy_basis.binding_ref,
                                ),
                            ),
                        ),
                    ),
                ),
                **unknown_kwargs,
            )
        with self.assertRaisesRegex(
            CMEEStage1ContractError, "cross_owner_invalid"
        ):
            validate_subjective_proposition_v2(
                replace(
                    proposition,
                    material_value_content=replace(
                        proposition.material_value_content,
                        value_applications=(
                            replace(
                                application,
                                policy_application_row_refs=("arbitrary-row",),
                            ),
                        ),
                    ),
                ),
                **kwargs,
            )
        with self.assertRaisesRegex(
            CMEEStage1ContractError, "cross_owner_invalid"
        ):
            validate_subjective_proposition_v2(
                replace(
                    proposition,
                    material_value_content=replace(
                        proposition.material_value_content,
                        value_applications=(
                            replace(
                                application,
                                material_risk=(
                                    MaterialRisk.UNKNOWN_TO_FALSE_UNDERSTANDING
                                ),
                            ),
                        ),
                    ),
                ),
                **kwargs,
            )
        appraisal, appraisal_kwargs = self._valid_subjective_v2(
            SubjectiveContentKind.APPRAISAL
        )
        assert appraisal.appraisal_content is not None
        with self.assertRaisesRegex(
            CMEEStage1ContractError, "focal_relation_invalid"
        ):
            validate_subjective_proposition_v2(
                replace(
                    appraisal,
                    appraisal_content=replace(
                        appraisal.appraisal_content,
                        dimension=AppraisalDimension.RELATIONAL_NONCOLLAPSE,
                        operation=AppraisalOperation.PRESERVE_BOTH_ENDPOINTS,
                    ),
                ),
                **appraisal_kwargs,
            )
        counter, counter_kwargs = self._valid_subjective_v2(
            SubjectiveContentKind.RELATIONAL_POSITION,
            bounded_counterposition=True,
        )
        with self.assertRaisesRegex(
            CMEEStage1ContractError, "focal_relation_invalid"
        ):
            validate_subjective_proposition_v2(
                replace(counter, focal_relation_ref=None),
                **{**counter_kwargs, "expected_focal_relation_ref": None},
            )

    def test_step1_anti_template_registry_invariant(self) -> None:
        self.assertEqual(
            CMEE_STAGE1_ANTI_TEMPLATE_FORBIDDEN_REGISTRY_FIELDS,
            (
                "case_id", "case_family", "fixture_id", "exact8_id",
                "raw_text", "raw_pattern", "source_regex",
                "semantic_keyword", "expected_text", "finished_surface",
                "finished_clause", "finished_sentence",
            ),
        )
        self.assertEqual(
            CMEE_STAGE1_ANTI_TEMPLATE_FORBIDDEN_SELECTOR_INPUTS,
            (
                "raw_source", "raw_text", "normalized_input",
                "evidence_text", "resolver", "regex_result", "case_id",
                "fixture_id", "fixture", "exact8_id",
                "source_phrase_family", "semantic_domain_keyword",
                "input_hash",
            ),
        )
        safe_registry_fields = (
            "construction_id",
            "argument_slots",
            "role_order",
            "valency",
            "particle_rules",
            "auxiliary_rules",
            "relation_combinators",
            "inflection_order",
        )
        safe_selector_inputs = (
            "grammatical_shape_key",
            "predicate_valency",
            "syntactic_orientation",
        )
        validate_stage1_anti_template_registry_invariant(
            safe_registry_fields,
            safe_selector_inputs,
        )
        malformed_exact_shapes = (
            ((), ()),
            (safe_registry_fields[:-1], safe_selector_inputs),
            (
                (safe_registry_fields[0], *safe_registry_fields[:-1]),
                safe_selector_inputs,
            ),
            (tuple(reversed(safe_registry_fields)), safe_selector_inputs),
            (
                (
                    "constructionId", "argumentSlots", "roleOrder",
                    "valency", "particleRules", "auxiliaryRules",
                    "relationCombinators", "inflectionOrder",
                ),
                safe_selector_inputs,
            ),
            (safe_registry_fields, safe_selector_inputs[:-1]),
            (
                safe_registry_fields,
                (safe_selector_inputs[0], *safe_selector_inputs[:-1]),
            ),
            (safe_registry_fields, tuple(reversed(safe_selector_inputs))),
            (
                safe_registry_fields,
                (
                    "grammaticalShapeKey", "predicateValency",
                    "syntacticOrientation",
                ),
            ),
        )
        for registry_fields, selector_inputs in malformed_exact_shapes:
            with self.subTest(
                registry_fields=registry_fields,
                selector_inputs=selector_inputs,
            ), self.assertRaisesRegex(
                CMEEStage1ContractError, "anti_template_registry_invalid"
            ):
                validate_stage1_anti_template_registry_invariant(
                    registry_fields,
                    selector_inputs,
                )
        for unknown_registry, unknown_selector in (
            ("opaque_payload", None),
            (None, "opaque_selector_payload"),
            ("reference_rule_id", None),
            ("functional_rule_id", None),
            (None, "artifact_composition_candidate_id"),
            (None, "shared_variant_id"),
        ):
            with self.subTest(
                unknown_registry=unknown_registry,
                unknown_selector=unknown_selector,
            ), self.assertRaisesRegex(
                CMEEStage1ContractError, "anti_template_registry_invalid"
            ):
                validate_stage1_anti_template_registry_invariant(
                    (
                        (unknown_registry, *safe_registry_fields[1:])
                        if unknown_registry
                        else safe_registry_fields
                    ),
                    (
                        (unknown_selector, *safe_selector_inputs[1:])
                        if unknown_selector
                        else safe_selector_inputs
                    ),
                )
        for field_name in CMEE_STAGE1_ANTI_TEMPLATE_FORBIDDEN_REGISTRY_FIELDS:
            with self.subTest(field=field_name), self.assertRaisesRegex(
                CMEEStage1ContractError, "anti_template_registry_invalid"
            ):
                validate_stage1_anti_template_registry_invariant(
                    (field_name, *safe_registry_fields[1:]),
                    safe_selector_inputs,
                )
        for parameter_name in CMEE_STAGE1_ANTI_TEMPLATE_FORBIDDEN_SELECTOR_INPUTS:
            with self.subTest(parameter=parameter_name), self.assertRaisesRegex(
                CMEEStage1ContractError, "anti_template_registry_invalid"
            ):
                validate_stage1_anti_template_registry_invariant(
                    safe_registry_fields,
                    (parameter_name, *safe_selector_inputs[1:]),
                )
        for alias in (
            "finishedSentenceTemplate",
            "fixtureSelector",
            "rawTextDigest",
            "request_raw_source",
            "source_evidence_text",
            "semantic_resolver",
            "test_case_id",
            "normalized_source_input",
            "opening",
            "terminal",
            "finished_connective_chain",
            "sentence_body",
            "source_domain_noun",
            "case_specific_phrase",
        ):
            with self.subTest(alias=alias), self.assertRaisesRegex(
                CMEEStage1ContractError, "anti_template_registry_invalid"
            ):
                validate_stage1_anti_template_registry_invariant(
                    (alias, *safe_registry_fields[1:]),
                    safe_selector_inputs,
                )
        for alias in (
            "source_resolver",
            "source_regex",
            "raw_pattern",
            "semantic_keyword",
            "expected_text",
            "finished_sentence",
            "source_text",
            "rawContent",
            "normalized_text",
            "source_string",
            "input_digest",
            "request_text",
            "source_bytes",
            "utterance",
            "input_bytes",
            "prompt",
            "content",
        ):
            with self.subTest(selector_alias=alias), self.assertRaisesRegex(
                CMEEStage1ContractError, "anti_template_registry_invalid"
            ):
                validate_stage1_anti_template_registry_invariant(
                    safe_registry_fields,
                    (alias, *safe_selector_inputs[1:]),
                )

    def test_step1_surface_derivation_exact8_accepts(self) -> None:
        rule_registry = self._surface_rule_registry()
        owner_ref = dict(CMEE_STAGE1_FINAL_LOGICAL_ID_REGISTRY)[
            "CMEE_STAGE1_EMLIS_OWNER_REF"
        ]
        empty = {
            "source_or_claim_refs": (),
            "emlis_owner_ref": None,
            "relation_or_clause_plan_refs": (),
            "qualifier_refs": (),
            "response_object_expression_ref": None,
            "antecedent_unit_ref": None,
            "participant_role_ref": None,
            "evidence_refs": (),
            "rule_ref": "rule:surface@cocolon.cmee.surface.v1",
            "input_scalar_ranges": (),
        }
        cases = (
            (SurfaceDerivationKind.LITERAL_SUBSPAN, {"source_or_claim_refs": ("source-1",), "evidence_refs": ("evidence-1",), "input_scalar_ranges": ((0, 2),)}, None),
            (SurfaceDerivationKind.NORMALIZED_INFLECTION, {"source_or_claim_refs": ("source-1",), "evidence_refs": ("evidence-1",), "input_scalar_ranges": ((0, 2),)}, None),
            (SurfaceDerivationKind.COMPOSITIONAL_JOIN, {"source_or_claim_refs": ("source-1", "source-2"), "evidence_refs": ("evidence-1",), "input_scalar_ranges": ((0, 2), (3, 5))}, None),
            (SurfaceDerivationKind.REGISTERED_EMLIS_LEXEME, {"emlis_owner_ref": owner_ref}, None),
            (SurfaceDerivationKind.REGISTERED_PARTICIPANT_LEXEME, {"participant_role_ref": "CURRENT_USER_ADDRESSEE"}, None),
            (SurfaceDerivationKind.REGISTERED_STRUCTURAL_ASSET, {}, None),
            (SurfaceDerivationKind.PROJECTED_RESPONSE_OBJECT, {"source_or_claim_refs": ("source-1",), "response_object_expression_ref": "response-object-1", "evidence_refs": ("evidence-1",), "input_scalar_ranges": ((0, 2),)}, "EXPLICIT"),
            (SurfaceDerivationKind.PROJECTED_FUNCTIONAL_ASSET, {"relation_or_clause_plan_refs": ("relation-1",)}, None),
        )
        for kind, delta, response_mode in cases:
            with self.subTest(kind=kind):
                derivation = SurfaceDerivation(
                    derivation_kind=kind,
                    **{
                        **empty,
                        "rule_ref": rule_registry[
                            (
                                kind,
                                response_mode
                                if kind
                                is SurfaceDerivationKind.PROJECTED_RESPONSE_OBJECT
                                else None,
                            )
                        ][0],
                        **delta,
                    },
                )
                validate_surface_derivation(
                    derivation,
                    registered_rule_refs_by_kind=rule_registry,
                    response_object_mode=response_mode,
                )
        additional_rows = (
            (
                SurfaceDerivation(
                    derivation_kind=SurfaceDerivationKind.REGISTERED_EMLIS_LEXEME,
                    **{
                        **empty,
                        "rule_ref": rule_registry[
                            (SurfaceDerivationKind.REGISTERED_EMLIS_LEXEME, None)
                        ][0],
                        "source_or_claim_refs": ("subjective-claim-1",),
                    },
                ),
                None,
            ),
            (
                SurfaceDerivation(
                    derivation_kind=SurfaceDerivationKind.PROJECTED_FUNCTIONAL_ASSET,
                    **{
                        **empty,
                        "rule_ref": rule_registry[
                            (SurfaceDerivationKind.PROJECTED_FUNCTIONAL_ASSET, None)
                        ][0],
                        "qualifier_refs": ("qualifier-1",),
                    },
                ),
                None,
            ),
            (
                SurfaceDerivation(
                    derivation_kind=SurfaceDerivationKind.PROJECTED_RESPONSE_OBJECT,
                    **{
                        **empty,
                        "rule_ref": rule_registry[
                            (
                                SurfaceDerivationKind.PROJECTED_RESPONSE_OBJECT,
                                "COMPOSITE",
                            )
                        ][0],
                        "source_or_claim_refs": ("source-1", "source-2"),
                        "relation_or_clause_plan_refs": ("relation-1",),
                        "response_object_expression_ref": "response-object-2",
                        "evidence_refs": ("evidence-1",),
                        "input_scalar_ranges": ((0, 2), (3, 5)),
                    },
                ),
                "COMPOSITE",
            ),
            (
                SurfaceDerivation(
                    derivation_kind=SurfaceDerivationKind.PROJECTED_RESPONSE_OBJECT,
                    **{
                        **empty,
                        "rule_ref": rule_registry[
                            (
                                SurfaceDerivationKind.PROJECTED_RESPONSE_OBJECT,
                                "ANAPHORIC",
                            )
                        ][0],
                        "source_or_claim_refs": ("source-1",),
                        "response_object_expression_ref": "response-object-3",
                        "antecedent_unit_ref": "unit-1",
                    },
                ),
                "ANAPHORIC",
            ),
        )
        for derivation, response_mode in additional_rows:
            validate_surface_derivation(
                derivation,
                registered_rule_refs_by_kind=rule_registry,
                response_object_mode=response_mode,
            )

    def test_step1_surface_derivation_rejects_owner_range_and_rule_tamper(self) -> None:
        rule_registry = self._surface_rule_registry()
        base = SurfaceDerivation(
            derivation_kind=SurfaceDerivationKind.LITERAL_SUBSPAN,
            source_or_claim_refs=("source-1",),
            emlis_owner_ref=None,
            relation_or_clause_plan_refs=(),
            qualifier_refs=(),
            response_object_expression_ref=None,
            antecedent_unit_ref=None,
            participant_role_ref=None,
            evidence_refs=("evidence-1",),
            rule_ref=rule_registry[
                (SurfaceDerivationKind.LITERAL_SUBSPAN, None)
            ][0],
            input_scalar_ranges=((0, 2),),
        )
        for mutated, code in (
            (replace(base, emlis_owner_ref="owner:other@v1"), "owner_invalid"),
            (replace(base, input_scalar_ranges=((2, 2),)), "range_invalid"),
            (
                replace(
                    base,
                    source_or_claim_refs=("source-1", "source-2"),
                    input_scalar_ranges=((0, 3), (2, 5)),
                    derivation_kind=SurfaceDerivationKind.COMPOSITIONAL_JOIN,
                    rule_ref=rule_registry[
                        (SurfaceDerivationKind.COMPOSITIONAL_JOIN, None)
                    ][0],
                ),
                "range_invalid",
            ),
            (replace(base, rule_ref="unqualified-rule"), "rule_invalid"),
            (replace(base, rule_ref="rule:evil@evil.v1"), "rule_invalid"),
            (
                replace(
                    base,
                    rule_ref=rule_registry[
                        (SurfaceDerivationKind.REGISTERED_EMLIS_LEXEME, None)
                    ][0],
                ),
                "rule_invalid",
            ),
            (
                replace(
                    base,
                    derivation_kind=SurfaceDerivationKind.PROJECTED_RESPONSE_OBJECT,
                    response_object_expression_ref="",
                ),
                "owner_invalid",
            ),
        ):
            with self.subTest(code=code), self.assertRaisesRegex(
                CMEEStage1ContractError, code
            ):
                validate_surface_derivation(
                    mutated,
                    registered_rule_refs_by_kind=rule_registry,
                )

        owner_ref = dict(CMEE_STAGE1_FINAL_LOGICAL_ID_REGISTRY)[
            "CMEE_STAGE1_EMLIS_OWNER_REF"
        ]
        emlis = replace(
            base,
            derivation_kind=SurfaceDerivationKind.REGISTERED_EMLIS_LEXEME,
            source_or_claim_refs=(),
            emlis_owner_ref=owner_ref,
            evidence_refs=(),
            input_scalar_ranges=(),
            rule_ref=rule_registry[
                (SurfaceDerivationKind.REGISTERED_EMLIS_LEXEME, None)
            ][0],
        )
        participant = replace(
            base,
            derivation_kind=SurfaceDerivationKind.REGISTERED_PARTICIPANT_LEXEME,
            source_or_claim_refs=(),
            participant_role_ref="CURRENT_USER_ADDRESSEE",
            evidence_refs=(),
            input_scalar_ranges=(),
            rule_ref=rule_registry[
                (SurfaceDerivationKind.REGISTERED_PARTICIPANT_LEXEME, None)
            ][0],
        )
        structural = replace(
            base,
            derivation_kind=SurfaceDerivationKind.REGISTERED_STRUCTURAL_ASSET,
            source_or_claim_refs=(),
            evidence_refs=(),
            input_scalar_ranges=(),
            rule_ref=rule_registry[
                (SurfaceDerivationKind.REGISTERED_STRUCTURAL_ASSET, None)
            ][0],
        )
        explicit_response = replace(
            base,
            derivation_kind=SurfaceDerivationKind.PROJECTED_RESPONSE_OBJECT,
            response_object_expression_ref="response-object-1",
            rule_ref=rule_registry[
                (SurfaceDerivationKind.PROJECTED_RESPONSE_OBJECT, "EXPLICIT")
            ][0],
        )
        anaphoric_response = replace(
            explicit_response,
            antecedent_unit_ref="unit-1",
            evidence_refs=(),
            input_scalar_ranges=(),
            rule_ref=rule_registry[
                (SurfaceDerivationKind.PROJECTED_RESPONSE_OBJECT, "ANAPHORIC")
            ][0],
        )
        functional = replace(
            base,
            derivation_kind=SurfaceDerivationKind.PROJECTED_FUNCTIONAL_ASSET,
            source_or_claim_refs=(),
            relation_or_clause_plan_refs=("relation-1",),
            evidence_refs=(),
            input_scalar_ranges=(),
            rule_ref=rule_registry[
                (SurfaceDerivationKind.PROJECTED_FUNCTIONAL_ASSET, None)
            ][0],
        )
        exact_matrix_tamper = (
            (replace(base, evidence_refs=()), None, "owner_invalid"),
            (replace(base, input_scalar_ranges=()), None, "owner_invalid"),
            (
                replace(
                    base,
                    derivation_kind=SurfaceDerivationKind.NORMALIZED_INFLECTION,
                    evidence_refs=(),
                    rule_ref=rule_registry[
                        (SurfaceDerivationKind.NORMALIZED_INFLECTION, None)
                    ][0],
                ),
                None,
                "owner_invalid",
            ),
            (
                replace(
                    base,
                    derivation_kind=SurfaceDerivationKind.COMPOSITIONAL_JOIN,
                    source_or_claim_refs=("source-1", "source-2"),
                    input_scalar_ranges=((0, 2),),
                    rule_ref=rule_registry[
                        (SurfaceDerivationKind.COMPOSITIONAL_JOIN, None)
                    ][0],
                ),
                None,
                "owner_invalid",
            ),
            (
                replace(emlis, source_or_claim_refs=("claim-1",)),
                None,
                "owner_invalid",
            ),
            (replace(emlis, emlis_owner_ref=None), None, "owner_invalid"),
            (
                replace(participant, source_or_claim_refs=("source-1",)),
                None,
                "owner_invalid",
            ),
            (
                replace(structural, source_or_claim_refs=("source-1",)),
                None,
                "owner_invalid",
            ),
            (
                replace(explicit_response, response_object_expression_ref=None),
                "EXPLICIT",
                "owner_invalid",
            ),
            (
                replace(explicit_response, antecedent_unit_ref="unit-1"),
                "EXPLICIT",
                "owner_invalid",
            ),
            (
                replace(explicit_response, evidence_refs=()),
                "EXPLICIT",
                "owner_invalid",
            ),
            (
                replace(
                    explicit_response,
                    rule_ref=rule_registry[
                        (
                            SurfaceDerivationKind.PROJECTED_RESPONSE_OBJECT,
                            "COMPOSITE",
                        )
                    ][0],
                ),
                "COMPOSITE",
                "owner_invalid",
            ),
            (
                replace(anaphoric_response, antecedent_unit_ref=None),
                "ANAPHORIC",
                "owner_invalid",
            ),
            (
                replace(
                    anaphoric_response,
                    evidence_refs=("evidence-1",),
                    input_scalar_ranges=((0, 2),),
                ),
                "ANAPHORIC",
                "owner_invalid",
            ),
            (explicit_response, "COMPOSITE", "rule_invalid"),
            (
                replace(functional, qualifier_refs=("qualifier-1",)),
                None,
                "owner_invalid",
            ),
        )
        for mutated, response_mode, code in exact_matrix_tamper:
            with self.subTest(
                kind=mutated.derivation_kind,
                response_mode=response_mode,
                code=code,
            ), self.assertRaisesRegex(CMEEStage1ContractError, code):
                validate_surface_derivation(
                    mutated,
                    registered_rule_refs_by_kind=rule_registry,
                    response_object_mode=response_mode,
                )


class CMEEStage1AdditionalCorrectionStep2CompositionTest(unittest.TestCase):
    _KNOWN_EXACT4 = (
        (
            "tension",
            "続けたい気持ちはある。でも、もうかなり無理をしている気もする。",
            "continuation_or_refusal",
            ObservationContributionKind.OBSERVE_TENSION,
            SemanticOperator.SYNTHESIZE_RELATION,
            RelationOperator.TENSION_WITH,
        ),
        (
            "temporal_change",
            "散歩に出たら、少し落ち着いた。ただ、いつもそうなるとは思っていない。",
            "action_supports_change",
            ObservationContributionKind.OBSERVE_ACTION_THEN_CHANGE,
            SemanticOperator.PRESENT_CHANGE,
            RelationOperator.ACTION_PRECEDES_CHANGE,
        ),
        (
            "help_seeking",
            "相談したい。でも、迷惑かもしれないと思うと切り出せない。",
            "wish_and_constraint",
            ObservationContributionKind.OBSERVE_COEXISTENCE,
            SemanticOperator.SYNTHESIZE_RELATION,
            RelationOperator.COEXISTS_WITH,
        ),
        (
            "unfinished",
            "仕事の話はした。でも、まだ気持ちが残っていて、どうしたいかは分からない。",
            "temporal_before_after",
            ObservationContributionKind.PRESERVE_RESIDUE,
            SemanticOperator.PRESENT_RESIDUE,
            RelationOperator.TEMPORALLY_PRECEDES,
        ),
    )

    def _known_inputs(self, index: int):
        label, memo, *_expected = self._KNOWN_EXACT4[index]
        return _final_stage1_composition_inputs(
            _request(record_id=f"stage2-final-{label}", memo=memo)
        )

    def test_final_job_topology_and_anti_template_registry_are_closed(self) -> None:
        source_path = Path(inspect.getsourcefile(stage1_composition_module) or "")
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        function_names = {
            row.name
            for row in tree.body
            if isinstance(row, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        self.assertTrue(
            {
                "project_subjective_meaning_plan",
                "project_stage1_discourse_arc",
                "compose_stage1_from_projection",
                "normalize_to_normal_form",
                "derive_discourse_preference_profile",
            }.issubset(function_names)
        )
        self.assertTrue(
            {
                "plan_subjective_meaning",
                "plan_stage1_discourse",
                "compose_stage1_draft",
                "rank_stage1_drafts",
            }.isdisjoint(function_names)
        )
        self.assertEqual(
            tuple(
                inspect.signature(
                    stage1_response_module.build_subjective_planning_inputs
                ).parameters
            ),
            ("source", "grounded_graph", "parent_plan", "grounded_plan"),
        )
        self.assertEqual(
            tuple(
                inspect.signature(
                    stage1_response_module.seal_stage1_projection
                ).parameters
            ),
            ("phase_A", "meaning_plan"),
        )
        self.assertEqual(
            tuple(
                inspect.signature(
                    stage1_response_module.build_surface_composition_inputs
                ).parameters
            ),
            ("phase_A", "final_projection"),
        )
        local_imports = {
            row.module
            for row in tree.body
            if isinstance(row, ast.ImportFrom) and row.level
        }
        self.assertEqual(local_imports, {"contracts"})
        self.assertFalse(
            any(
                isinstance(row, ast.Import)
                and any(alias.name == "random" for alias in row.names)
                for row in tree.body
            )
        )
        self.assertTrue(
            all(
                token not in name.lower()
                for name in function_names
                for token in ("retry", "legacy", "fallback", "case_id")
            )
        )
        module_source = source_path.read_text(encoding="utf-8")
        self.assertTrue(
            all(memo not in module_source for _label, memo, *_ in self._KNOWN_EXACT4)
        )

        construction_fields = tuple(
            row.name for row in fields(stage1_composition_module.ConstructionSpec)
        )
        self.assertEqual(len(construction_fields), 8)
        self.assertTrue(
            set(construction_fields).isdisjoint(
                CMEE_STAGE1_ANTI_TEMPLATE_FORBIDDEN_REGISTRY_FIELDS
            )
        )
        self.assertEqual(
            len(
                {
                    row.construction_id
                    for row in stage1_composition_module.CONSTRUCTION_REGISTRY
                }
            ),
            len(stage1_composition_module.CONSTRUCTION_REGISTRY),
        )
        self.assertEqual(
            tuple(inspect.signature(
                stage1_composition_module.select_eligible_constructions
            ).parameters),
            (
                "grammatical_shape_key",
                "predicate_valency",
                "syntactic_orientation",
            ),
        )
        validate_stage1_anti_template_registry_invariant(
            construction_fields,
            tuple(
                inspect.signature(
                    stage1_composition_module.select_eligible_constructions
                ).parameters
            ),
        )
        stage1_composition_module.validate_language_core_registry_invariant()
        self.assertEqual(
            {
                row.relation_operator
                for row in stage1_composition_module.RELATION_MORPHOLOGY_ASSET_REGISTRY
            },
            set(RelationOperator) - {RelationOperator.NO_RELATION_CLAIM},
        )
        self.assertEqual(
            {
                row.scalar_axis
                for row in stage1_composition_module.SCALAR_MORPHOLOGY_ASSET_REGISTRY
            },
            set(stage1_composition_module.ClauseScalarAxis),
        )
        self.assertTrue(
            all(
                "。" not in token
                for row in stage1_composition_module.EXPRESSION_ASSET_REGISTRY
                for token in row.predicate_lexemes
            )
        )
        exact_enum_counts = {
            stage1_composition_module.SentenceJob: 8,
            stage1_composition_module.DutySuppressionReason: 3,
            stage1_composition_module.SubjectiveFacetSuppressionReason: 3,
            stage1_composition_module.CorrectableDefectKind: 8,
            stage1_composition_module.ResponseObjectExpressionMode: 3,
            stage1_composition_module.ArcDependencyKind: 5,
            stage1_composition_module.SubjectiveResponsibilityKind: 4,
            stage1_composition_module.SubjectiveSpecificity: 3,
            stage1_composition_module.ProfileEvidenceField: 8,
            stage1_composition_module.ProfileEvidenceRuleKind: 8,
            stage1_composition_module.PredicateValency: 4,
            stage1_composition_module.ClauseArgumentRole: 11,
            stage1_composition_module.ClauseScalarAxis: 3,
            stage1_composition_module.NormalFormPhase: 6,
        }
        for enum_type, expected_count in exact_enum_counts.items():
            with self.subTest(enum=enum_type.__name__):
                self.assertEqual(len(enum_type), expected_count)

    def test_known_exact4_upstream_typed_semantics_reach_projection(self) -> None:
        for index, (
            label,
            _memo,
            upstream_relation,
            contribution_kind,
            semantic_operator,
            relation_operator,
        ) in enumerate(self._KNOWN_EXACT4):
            with self.subTest(known_structure=label):
                (
                    _source,
                    grounded_plan,
                    _graph,
                    _parent_plan,
                    projection,
                    _phase_a,
                    _subjective_plan,
                    _phase_b,
                ) = self._known_inputs(index)
                resolver = build_evidence_span_resolver(
                    _source.evidence_spans,
                    current_input=_source.normalized_current_input,
                )
                self.assertEqual(
                    validate_grounded_observation_plan(
                        grounded_plan,
                        resolver,
                    ),
                    (),
                )
                relation_rows = tuple(
                    row
                    for row in grounded_plan.relations
                    if row.type == upstream_relation
                )
                self.assertEqual(len(relation_rows), 1)
                contribution_rows = tuple(
                    row
                    for row in projection.observation_contributions
                    if row.contribution_kind is contribution_kind
                    and row.semantic_operator is semantic_operator
                    and row.relation_operator is relation_operator
                )
                self.assertEqual(len(contribution_rows), 1)
                self.assertEqual(contribution_rows[0].retention, "REQUIRED")

                if label in {"tension", "help_seeking"}:
                    self.assertTrue(
                        any(row.kind == "wish" for row in grounded_plan.nuclei)
                    )
                    self.assertTrue(
                        any(
                            row.kind == "constraint"
                            for row in grounded_plan.nuclei
                        )
                    )
                    self.assertEqual(
                        tuple(
                            binding.role
                            for binding in contribution_rows[0].argument_bindings
                        ),
                        (ArgumentRole.LEFT, ArgumentRole.RIGHT),
                    )
                elif label == "temporal_change":
                    action = next(
                        row for row in grounded_plan.nuclei if row.kind == "action"
                    )
                    change = next(
                        row for row in grounded_plan.nuclei if row.kind == "change"
                    )
                    self.assertEqual(action.source_span_ids, change.source_span_ids)
                    self.assertEqual(
                        tuple(
                            binding.role
                            for binding in contribution_rows[0].argument_bindings
                        ),
                        (ArgumentRole.ACTION, ArgumentRole.CHANGE),
                    )
                else:
                    residue = next(
                        row
                        for row in grounded_plan.nuclei
                        if row.semantic_frame.predicate_kind == "residue"
                    )
                    unfinished = next(
                        row
                        for row in grounded_plan.nuclei
                        if row.semantic_frame.predicate_kind == "unfinished"
                    )
                    self.assertEqual(
                        residue.source_span_ids,
                        unfinished.source_span_ids,
                    )
                    relation = relation_rows[0]
                    self.assertEqual(relation.to_nucleus_id, residue.nucleus_id)
                    self.assertNotIn(
                        unfinished.nucleus_id,
                        (relation.from_nucleus_id, relation.to_nucleus_id),
                    )
                    unfinished_contributions = tuple(
                        row
                        for row in projection.observation_contributions
                        if row.contribution_kind
                        is ObservationContributionKind.PRESERVE_UNFINISHED
                        and row.semantic_operator
                        is SemanticOperator.PRESENT_UNFINISHED
                        and row.relation_operator
                        is RelationOperator.NO_RELATION_CLAIM
                    )
                    self.assertEqual(len(unfinished_contributions), 1)
                    self.assertEqual(
                        unfinished_contributions[0].retention,
                        "REQUIRED",
                    )

    def test_generic_affect_is_absorbed_by_same_target_specific_opportunity(
        self,
    ) -> None:
        module = stage1_composition_module
        known_rows = tuple(
            (label, memo, "生活", "不安", "medium")
            for label, memo, *_expected in self._KNOWN_EXACT4
        )
        grouped_rows = (
            ("known", known_rows),
            ("public_standin", PUBLIC_NONSECRET_EARLY_STANDIN_EXACT4),
        )
        affect_sentence_counts: dict[str, int] = {}
        appraisal_claim_counts: dict[str, int] = {}
        position_claim_counts: dict[str, int] = {}

        for group, rows in grouped_rows:
            affect_sentence_count = 0
            appraisal_claim_count = 0
            position_claim_count = 0
            self.assertEqual(len(rows), 4)
            for index, (label, memo, category, emotion, strength) in enumerate(
                rows
            ):
                with self.subTest(group=group, structural_family=label):
                    (
                        _source,
                        _grounded_plan,
                        _graph,
                        _parent_plan,
                        projection,
                        phase_a,
                        meaning_plan,
                        phase_b,
                    ) = _final_stage1_composition_inputs(
                        _request(
                            record_id=(
                                "cmee-i1sx-early-"
                                + (
                                    "known"
                                    if group == "known"
                                    else "withheld"
                                )
                                + f"-{index + 1:02d}"
                            ),
                            memo=memo,
                            category=category,
                            emotion=emotion,
                            strength=strength,
                        )
                    )
                    responsibilities = {
                        row.responsibility_ref: row
                        for row in meaning_plan.subjective_responsibility_rows
                    }
                    opportunities = {
                        row.opportunity_key: row
                        for row in meaning_plan.subjective_opportunity_rows
                    }
                    claims = tuple(meaning_plan.subjective_claim_rows)
                    selected_keys = {
                        row.selected_subjective_opportunity_key
                        for row in claims
                    }
                    suppressions = tuple(
                        meaning_plan.subjective_facet_suppression_rows
                    )
                    suppressed_keys = {
                        row.suppressed_opportunity_key
                        for row in suppressions
                    }
                    self.assertTrue(claims)
                    self.assertEqual(
                        selected_keys | suppressed_keys,
                        set(opportunities),
                    )
                    self.assertTrue(selected_keys.isdisjoint(suppressed_keys))

                    affect_opportunities = tuple(
                        row
                        for row in opportunities.values()
                        if row.content_kind is SubjectiveContentKind.AFFECT
                    )
                    affect_claims = tuple(
                        row
                        for row in claims
                        if row.asserted_subjective_proposition.content_kind
                        is SubjectiveContentKind.AFFECT
                    )
                    self.assertEqual(len(affect_opportunities), 1)
                    self.assertEqual(affect_claims, ())
                    affect_opportunity = affect_opportunities[0]
                    self.assertEqual(
                        len(affect_opportunity.responsibility_refs),
                        1,
                    )
                    affect_responsibility = responsibilities[
                        affect_opportunity.responsibility_refs[0]
                    ]
                    self.assertIs(
                        affect_responsibility.responsibility_kind,
                        module.SubjectiveResponsibilityKind.AFFECTIVE_RESPONSE,
                    )
                    matching_suppressions = tuple(
                        row
                        for row in suppressions
                        if row.suppressed_opportunity_key
                        == affect_opportunity.opportunity_key
                    )
                    self.assertEqual(len(matching_suppressions), 1)
                    suppression = matching_suppressions[0]
                    self.assertIs(
                        suppression.reason,
                        module.SubjectiveFacetSuppressionReason.ABSORBED_ATTENTION,
                    )
                    self.assertIn(
                        suppression.absorbed_by_selected_opportunity_key,
                        selected_keys,
                    )
                    absorber = opportunities[
                        suppression.absorbed_by_selected_opportunity_key
                    ]
                    self.assertIn(
                        absorber.content_kind,
                        {
                            SubjectiveContentKind.APPRAISAL,
                            SubjectiveContentKind.RELATIONAL_POSITION,
                        },
                    )
                    absorber_claims = tuple(
                        row
                        for row in claims
                        if row.selected_subjective_opportunity_key
                        == absorber.opportunity_key
                    )
                    self.assertEqual(len(absorber_claims), 1)
                    absorber_owner_refs = tuple(
                        dict.fromkeys(
                            owner_ref
                            for responsibility_ref
                            in absorber.responsibility_refs
                            for owner_ref in responsibilities[
                                responsibility_ref
                            ].owner_component_refs
                        )
                    )
                    self.assertEqual(
                        absorber_owner_refs,
                        affect_responsibility.owner_component_refs,
                    )

                    coverage_by_ref = {
                        row.responsibility_ref: row
                        for row in meaning_plan.responsibility_coverage_rows
                    }
                    self.assertEqual(
                        set(coverage_by_ref),
                        set(responsibilities),
                    )
                    self.assertEqual(
                        coverage_by_ref[
                            affect_responsibility.responsibility_ref
                        ].covered_by_claim_refs,
                        (),
                    )
                    self.assertEqual(
                        coverage_by_ref[
                            affect_responsibility.responsibility_ref
                        ].reception_act_refs,
                        affect_responsibility.retained_reception_act_refs,
                    )
                    for responsibility in responsibilities.values():
                        expected_claim_refs = tuple(
                            claim.subjective_claim_id
                            for claim in claims
                            if responsibility.responsibility_ref
                            in claim.subjective_responsibility_refs
                        )
                        self.assertEqual(
                            coverage_by_ref[
                                responsibility.responsibility_ref
                            ].covered_by_claim_refs,
                            expected_claim_refs,
                        )

                    appraisal_claims = tuple(
                        row
                        for row in claims
                        if row.asserted_subjective_proposition.content_kind
                        is SubjectiveContentKind.APPRAISAL
                    )
                    position_claims = tuple(
                        row
                        for row in claims
                        if row.asserted_subjective_proposition.content_kind
                        is SubjectiveContentKind.RELATIONAL_POSITION
                    )
                    self.assertEqual(len(appraisal_claims), 1)
                    appraisal_claim_count += len(appraisal_claims)
                    position_claim_count += len(position_claims)
                    position_opportunities = tuple(
                        row
                        for row in opportunities.values()
                        if row.content_kind
                        is SubjectiveContentKind.RELATIONAL_POSITION
                    )
                    self.assertEqual(
                        {row.opportunity_key for row in position_opportunities},
                        {
                            row.selected_subjective_opportunity_key
                            for row in position_claims
                        },
                    )

                    qualifier_by_ref = {
                        row.source_qualifier_binding_ref: row
                        for row in meaning_plan.source_qualifier_binding_rows
                    }
                    contribution_refs = {
                        row.contribution_id
                        for row in projection.observation_contributions
                    }
                    self.assertEqual(
                        phase_a.material_unknown_refs,
                        projection.meaning_field.material_unknown_refs,
                    )
                    for claim in claims:
                        proposition = claim.asserted_subjective_proposition
                        self.assertEqual(
                            claim.speaker_owner,
                            module.CMEE_STAGE1_EMLIS_OWNER_REF,
                        )
                        self.assertEqual(proposition.addressee_role, "USER")
                        self.assertEqual(proposition.referenced_actor_refs, ())
                        self.assertEqual(
                            proposition.referenced_experiencer_refs,
                            (),
                        )
                        self.assertTrue(
                            set(claim.basis_observation_contribution_refs)
                            <= contribution_refs
                        )
                        self.assertTrue(
                            proposition.source_qualifier_binding_refs
                        )
                        for qualifier_ref in (
                            proposition.source_qualifier_binding_refs
                        ):
                            qualifier = qualifier_by_ref[qualifier_ref]
                            self.assertTrue(qualifier.polarity)
                            self.assertTrue(qualifier.modality)
                            self.assertTrue(qualifier.time_scope)
                        self.assertEqual(claim.user_fact_effect, 0)
                        self.assertTrue(claim.forbidden_promotions)

                    arc = module.project_stage1_discourse_arc(phase_b)
                    duties = module._project_duties(phase_b, arc)
                    case_affect_duties = sum(
                        row.sentence_job is module.SentenceJob.FEEL_TOWARD_OBJECT
                        for row in duties
                    )
                    self.assertEqual(case_affect_duties, 0)
                    affect_sentence_count += case_affect_duties
                    result = module.compose_stage1_from_projection(phase_b)
                    self.assertTrue(
                        1 <= len(result.ranked_candidates) <= 2
                    )
                    self.assertEqual(
                        tuple(row.rank for row in result.ranked_candidates),
                        tuple(range(1, len(result.ranked_candidates) + 1)),
                    )
                    self.assertGreaterEqual(
                        result.internal_candidate_count,
                        len(result.ranked_candidates),
                    )
                    for candidate in result.ranked_candidates:
                        normalized = candidate.normalized_artifact
                        repeated = module.normalize_to_normal_form(
                            normalized,
                            normalized.layout_preference_seed,
                            phase_b,
                        )
                        self.assertEqual(
                            module.canonical_normalized_bytes(normalized),
                            module.canonical_normalized_bytes(repeated),
                        )
                        self.assertEqual(
                            normalized.correctable_defect_rows,
                            (),
                        )
                        realized_duties = tuple(
                            duty_ref
                            for unit in normalized.sentence_units
                            for duty_ref in unit.duty_refs
                        )
                        self.assertEqual(
                            set(realized_duties),
                            set(normalized.required_duty_refs),
                        )
                        self.assertEqual(
                            len(realized_duties),
                            len(set(realized_duties)),
                        )

            affect_sentence_counts[group] = affect_sentence_count
            appraisal_claim_counts[group] = appraisal_claim_count
            position_claim_counts[group] = position_claim_count

        self.assertEqual(affect_sentence_counts, {"known": 0, "public_standin": 0})
        self.assertEqual(appraisal_claim_counts, {"known": 4, "public_standin": 4})
        self.assertTrue(
            all(count >= 1 for count in position_claim_counts.values())
        )

    def test_subjective_opportunity_partition_rejects_coordinated_tamper(
        self,
    ) -> None:
        module = stage1_composition_module
        *_, meaning_plan, _phase_b = self._known_inputs(3)
        responsibilities = meaning_plan.subjective_responsibility_rows
        opportunities = meaning_plan.subjective_opportunity_rows
        claims = meaning_plan.subjective_claim_rows
        coverage = meaning_plan.responsibility_coverage_rows
        suppressions = meaning_plan.subjective_facet_suppression_rows
        self.assertEqual(len(suppressions), 1)
        suppression = suppressions[0]
        opportunity_by_key = {
            row.opportunity_key: row for row in opportunities
        }
        affect_opportunity = opportunity_by_key[
            suppression.suppressed_opportunity_key
        ]
        absorber = opportunity_by_key[
            suppression.absorbed_by_selected_opportunity_key
        ]
        appraisal_opportunity = next(
            row
            for row in opportunities
            if row.content_kind is SubjectiveContentKind.APPRAISAL
        )
        absorber_claim = next(
            row
            for row in claims
            if row.selected_subjective_opportunity_key
            == absorber.opportunity_key
        )
        affect_responsibility_ref = affect_opportunity.responsibility_refs[0]
        affect_responsibility = next(
            row
            for row in responsibilities
            if row.responsibility_ref == affect_responsibility_ref
        )
        affect_coverage = next(
            row
            for row in coverage
            if row.responsibility_ref == affect_responsibility_ref
        )
        module._validate_subjective_opportunity_partition(
            responsibilities=responsibilities,
            opportunities=opportunities,
            claims=claims,
            coverage=coverage,
            suppressions=suppressions,
        )

        coordinated_opportunities = tuple(
            replace(
                row,
                responsibility_refs=(
                    *row.responsibility_refs,
                    affect_responsibility_ref,
                ),
            )
            if row.opportunity_key == absorber.opportunity_key
            else row
            for row in opportunities
        )
        coordinated_claims = tuple(
            replace(
                row,
                subjective_responsibility_refs=(
                    *row.subjective_responsibility_refs,
                    affect_responsibility_ref,
                ),
            )
            if row.subjective_claim_id == absorber_claim.subjective_claim_id
            else row
            for row in claims
        )
        coordinated_coverage = tuple(
            replace(
                row,
                covered_by_claim_refs=(absorber_claim.subjective_claim_id,),
            )
            if row.responsibility_ref == affect_responsibility_ref
            else row
            for row in coverage
        )
        affect_target_refs = affect_responsibility.owner_component_refs
        affect_basis_rows = tuple(
            row
            for row in meaning_plan.subjective_basis_binding_rows
            if row.contribution_ref in set(affect_target_refs)
        )
        affect_basis_refs = tuple(row.binding_ref for row in affect_basis_rows)
        affect_primary_refs = tuple(
            dict.fromkeys(row.semantic_ref for row in affect_basis_rows)
        )
        affect_qualifier_refs = tuple(
            row.source_qualifier_binding_ref
            for row in meaning_plan.source_qualifier_binding_rows
            if row.basis_binding_ref in set(affect_basis_refs)
        )
        selected_affect_proposition = SubjectivePropositionV2(
            absorber_claim.asserted_subjective_proposition.schema_version,
            SubjectiveContentKind.AFFECT,
            SubjectiveMode.AFFECTIVE_RESPONSE,
            SubjectiveOperator.FEEL_TOWARD,
            affect_target_refs,
            affect_primary_refs,
            (),
            affect_primary_refs,
            affect_basis_refs,
            affect_qualifier_refs,
            None,
            affect_opportunity.content,
            None,
            None,
            None,
            (),
            (),
            "USER",
            SubjectiveAssertionModality.EMLIS_FEELING,
            "REQUEST_LOCAL_EMLIS_SUBJECTIVITY",
        )
        selected_affect_claim = replace(
            absorber_claim,
            subjective_claim_id="subjective-claim:coordinated-affect",
            subjective_responsibility_refs=(affect_responsibility_ref,),
            selected_subjective_opportunity_key=(
                affect_opportunity.opportunity_key
            ),
            asserted_subjective_proposition=selected_affect_proposition,
            basis_observation_contribution_refs=affect_target_refs,
            basis_semantic_refs=affect_primary_refs,
            value_principle_refs=(),
        )
        selected_affect_coverage = tuple(
            replace(
                row,
                covered_by_claim_refs=(
                    selected_affect_claim.subjective_claim_id,
                ),
            )
            if row.responsibility_ref == affect_responsibility_ref
            else row
            for row in coverage
        )
        orphan_ref = "subjective-responsibility:orphan"
        orphan_responsibility = replace(
            affect_responsibility,
            responsibility_ref=orphan_ref,
        )
        orphan_coverage = replace(
            affect_coverage,
            responsibility_ref=orphan_ref,
        )
        invalid_partitions = (
            (
                "lower_precedence_absorber",
                {
                    "suppressions": (
                        replace(
                            suppression,
                            absorbed_by_selected_opportunity_key=(
                                appraisal_opportunity.opportunity_key
                            ),
                        ),
                    )
                },
            ),
            (
                "selected_content_mismatch",
                {
                    "opportunities": tuple(
                        replace(row, content=affect_opportunity.content)
                        if row.opportunity_key == absorber.opportunity_key
                        else row
                        for row in opportunities
                    )
                },
            ),
            (
                "suppressed_claim_zero_to_one",
                {
                    "opportunities": coordinated_opportunities,
                    "claims": coordinated_claims,
                    "coverage": coordinated_coverage,
                },
            ),
            (
                "generic_affect_selected_instead_of_suppressed",
                {
                    "claims": (*claims, selected_affect_claim),
                    "coverage": selected_affect_coverage,
                    "suppressions": (),
                },
            ),
            (
                "orphan_responsibility",
                {
                    "responsibilities": (
                        *responsibilities,
                        orphan_responsibility,
                    ),
                    "coverage": (*coverage, orphan_coverage),
                },
            ),
            (
                "empty_responsibility_refs",
                {
                    "opportunities": tuple(
                        replace(row, responsibility_refs=())
                        if row.opportunity_key
                        == affect_opportunity.opportunity_key
                        else row
                        for row in opportunities
                    )
                },
            ),
            (
                "duplicate_responsibility_refs",
                {
                    "opportunities": tuple(
                        replace(
                            row,
                            responsibility_refs=(
                                affect_responsibility_ref,
                                affect_responsibility_ref,
                            ),
                        )
                        if row.opportunity_key
                        == affect_opportunity.opportunity_key
                        else row
                        for row in opportunities
                    )
                },
            ),
            (
                "wrong_reason",
                {
                    "suppressions": (
                        replace(
                            suppression,
                            reason=(
                                module.SubjectiveFacetSuppressionReason.DUPLICATE
                            ),
                        ),
                    )
                },
            ),
            (
                "missing_absorber",
                {
                    "suppressions": (
                        replace(
                            suppression,
                            absorbed_by_selected_opportunity_key=None,
                        ),
                    )
                },
            ),
            (
                "foreign_absorber",
                {
                    "suppressions": (
                        replace(
                            suppression,
                            absorbed_by_selected_opportunity_key=(
                                "subjective-opportunity:foreign"
                            ),
                        ),
                    )
                },
            ),
            (
                "suppressed_key_as_absorber",
                {
                    "suppressions": (
                        replace(
                            suppression,
                            absorbed_by_selected_opportunity_key=(
                                affect_opportunity.opportunity_key
                            ),
                        ),
                    )
                },
            ),
            ("missing_suppression", {"suppressions": ()}),
            (
                "duplicate_suppression",
                {"suppressions": (suppression, suppression)},
            ),
        )
        base = {
            "responsibilities": responsibilities,
            "opportunities": opportunities,
            "claims": claims,
            "coverage": coverage,
            "suppressions": suppressions,
        }
        for label, changes in invalid_partitions:
            with self.subTest(tamper=label), self.assertRaisesRegex(
                module.Stage1CompositionError,
                "SUBJECTIVE_OPPORTUNITY_PARTITION_STOP",
            ):
                module._validate_subjective_opportunity_partition(
                    **{**base, **changes}
                )

    def test_bounded_change_and_unfinished_open_claims_keep_typed_targets(self) -> None:
        (
            _b_source,
            _b_grounded_plan,
            _b_graph,
            _b_parent_plan,
            b_projection,
            _b_phase_a,
            b_subjective_plan,
            _b_phase_b,
        ) = self._known_inputs(1)
        action_change = next(
            row
            for row in b_projection.observation_contributions
            if row.contribution_kind
            is ObservationContributionKind.OBSERVE_ACTION_THEN_CHANGE
            and row.semantic_operator is SemanticOperator.PRESENT_CHANGE
            and row.relation_operator is RelationOperator.ACTION_PRECEDES_CHANGE
        )
        caveat_tension = next(
            row
            for row in b_projection.observation_contributions
            if row.contribution_kind is ObservationContributionKind.OBSERVE_TENSION
            and row.relation_operator is RelationOperator.TENSION_WITH
        )
        action_change_ref_by_role = {
            binding.role: binding.semantic_ref
            for binding in action_change.argument_bindings
        }
        action_change_refs = tuple(
            action_change_ref_by_role[role]
            for role in (ArgumentRole.ACTION, ArgumentRole.CHANGE)
        )
        bounded_change_claims = tuple(
            row
            for row in b_subjective_plan.subjective_claim_rows
            if row.asserted_subjective_proposition.content_kind
            is SubjectiveContentKind.APPRAISAL
            and row.asserted_subjective_proposition.appraisal_content is not None
            and row.asserted_subjective_proposition.appraisal_content.dimension
            is AppraisalDimension.BOUNDED_CHANGE
        )
        self.assertEqual(len(bounded_change_claims), 1)
        bounded_change_claim = bounded_change_claims[0]
        bounded_change_proposition = (
            bounded_change_claim.asserted_subjective_proposition
        )
        self.assertEqual(action_change.semantic_refs, action_change_refs)
        self.assertEqual(
            bounded_change_proposition.target_contribution_refs,
            (action_change.contribution_id,),
        )
        self.assertEqual(
            bounded_change_claim.basis_observation_contribution_refs,
            (action_change.contribution_id,),
        )
        self.assertEqual(
            bounded_change_proposition.response_object_refs,
            action_change_refs,
        )
        self.assertEqual(
            bounded_change_proposition.focal_relation_ref,
            action_change.relation_basis_refs[0],
        )
        self.assertNotEqual(
            bounded_change_proposition.response_object_refs,
            caveat_tension.semantic_refs,
        )
        self.assertNotIn(
            caveat_tension.contribution_id,
            bounded_change_proposition.target_contribution_refs,
        )
        self.assertNotEqual(
            bounded_change_proposition.focal_relation_ref,
            caveat_tension.relation_basis_refs[0],
        )

        (
            _d_source,
            _d_grounded_plan,
            _d_graph,
            _d_parent_plan,
            d_projection,
            _d_phase_a,
            d_subjective_plan,
            d_phase_b,
        ) = self._known_inputs(3)
        unfinished_contributions = tuple(
            row
            for row in d_projection.observation_contributions
            if row.contribution_kind
            is ObservationContributionKind.PRESERVE_UNFINISHED
            and row.semantic_operator is SemanticOperator.PRESENT_UNFINISHED
            and row.relation_operator is RelationOperator.NO_RELATION_CLAIM
        )
        self.assertEqual(len(unfinished_contributions), 1)
        unfinished = unfinished_contributions[0]
        self.assertEqual(unfinished.relation_basis_refs, ())
        self.assertEqual(len(unfinished.semantic_refs), 1)
        unfinished_ref = unfinished.semantic_refs[0]

        unfinished_appraisals = tuple(
            row
            for row in d_subjective_plan.subjective_claim_rows
            if row.asserted_subjective_proposition.content_kind
            is SubjectiveContentKind.APPRAISAL
            and row.asserted_subjective_proposition.appraisal_content is not None
            and row.asserted_subjective_proposition.appraisal_content.dimension
            is AppraisalDimension.UNFINISHED_OPENNESS
        )
        open_positions = tuple(
            row
            for row in d_subjective_plan.subjective_claim_rows
            if row.asserted_subjective_proposition.content_kind
            is SubjectiveContentKind.RELATIONAL_POSITION
            and row.asserted_subjective_proposition.relational_position is not None
            and row.asserted_subjective_proposition.relational_position.closure
            is RelationalClosure.OPEN
        )
        self.assertEqual(len(unfinished_appraisals), 1)
        self.assertEqual(len(open_positions), 1)
        unfinished_appraisal = unfinished_appraisals[0]
        open_position = open_positions[0]
        for claim in (unfinished_appraisal, open_position):
            proposition = claim.asserted_subjective_proposition
            with self.subTest(content_kind=proposition.content_kind.value):
                self.assertEqual(
                    proposition.target_contribution_refs,
                    (unfinished.contribution_id,),
                )
                self.assertEqual(
                    claim.basis_observation_contribution_refs,
                    (unfinished.contribution_id,),
                )
                self.assertEqual(proposition.primary_target_refs, (unfinished_ref,))
                self.assertEqual(proposition.response_object_refs, (unfinished_ref,))
        open_position_content = (
            open_position.asserted_subjective_proposition.relational_position
        )
        self.assertIsNotNone(open_position_content)
        self.assertIs(
            open_position_content.commitment,
            RelationalCommitment.HOLD_OPEN,
        )
        self.assertIs(open_position_content.closure, RelationalClosure.OPEN)

        arc = stage1_composition_module.project_stage1_discourse_arc(d_phase_b)
        self.assertIn(unfinished.contribution_id, arc.unresolved_or_residue_refs)
        self.assertEqual(
            arc.terminal_owner_refs,
            (open_position.subjective_claim_id,),
        )
        self.assertEqual(arc.layer2_response_target_refs, (unfinished_ref,))

    def test_known_exact4_relation_direction_and_relation_basis_are_exact(self) -> None:
        module = stage1_composition_module
        for index, (label, _memo, *_expected) in enumerate(self._KNOWN_EXACT4):
            with self.subTest(known_structure=label):
                *_, phase_b = self._known_inputs(index)
                relation_contributions = tuple(
                    row
                    for row in phase_b.projection.observation_contributions
                    if row.relation_operator
                    is not RelationOperator.NO_RELATION_CLAIM
                )
                self.assertTrue(relation_contributions)
                arc = module.project_stage1_discourse_arc(phase_b)
                direction_rows = tuple(
                    row
                    for row in arc.dependency_rows
                    if row.dependency_kind
                    is module.ArcDependencyKind.ADMITTED_RELATION_DIRECTION
                )
                self.assertEqual(
                    len(direction_rows),
                    len(relation_contributions),
                )
                self.assertTrue(
                    all(
                        (row.source_relation_ref is not None)
                        == (
                            row.dependency_kind
                            is module.ArcDependencyKind.ADMITTED_RELATION_DIRECTION
                        )
                        for row in arc.dependency_rows
                    )
                )

                for contribution in relation_contributions:
                    with self.subTest(
                        known_structure=label,
                        relation_operator=contribution.relation_operator.value,
                    ):
                        self.assertEqual(len(contribution.relation_basis_refs), 1)
                        relation_ref = contribution.relation_basis_refs[0]
                        matching_directions = tuple(
                            row
                            for row in direction_rows
                            if row.source_relation_ref == relation_ref
                        )
                        self.assertEqual(len(matching_directions), 1)
                        direction = matching_directions[0]
                        expected_roles = module._ORDERED_RELATION_ARGUMENT_ROLES[
                            contribution.relation_operator
                        ]
                        self.assertEqual(
                            tuple(
                                binding.role
                                for binding in contribution.argument_bindings
                            ),
                            expected_roles,
                        )
                        expected_endpoints = tuple(
                            binding.semantic_ref
                            for binding in contribution.argument_bindings
                        )
                        self.assertEqual(
                            module._ordered_relation_endpoint_refs(contribution),
                            expected_endpoints,
                        )
                        self.assertEqual(
                            (
                                direction.predecessor_owner_ref,
                                direction.successor_owner_ref,
                            ),
                            expected_endpoints,
                        )
                        self.assertEqual(direction.source_relation_ref, relation_ref)

                        truncated = replace(
                            contribution,
                            relation_basis_refs=(
                                contribution.relation_basis_refs[:-1]
                            ),
                        )
                        with self.assertRaisesRegex(
                            module.Stage1CompositionError,
                            "STAGE1_RELATION_CARDINALITY_STOP",
                        ):
                            module._ordered_relation_endpoint_refs(truncated)

    def test_known_exact4_final_api_generates_source_bound_actual_japanese(self) -> None:
        visible_bodies = []
        for index, (label, _memo, *_expected) in enumerate(self._KNOWN_EXACT4):
            with self.subTest(known_structure=label):
                (
                    _source,
                    _grounded_plan,
                    graph,
                    _parent_plan,
                    _projection,
                    _phase_a,
                    subjective_plan,
                    phase_b,
                ) = self._known_inputs(index)
                self.assertTrue(subjective_plan.subjective_claim_rows)
                result = stage1_composition_module.compose_stage1_from_projection(
                    phase_b
                )
                units = result.selected_candidate.sentence_units
                layer1 = tuple(row for row in units if row.layer == "LAYER_1")
                layer2 = tuple(row for row in units if row.layer == "LAYER_2")
                self.assertTrue(1 <= len(layer1) <= 5)
                self.assertTrue(1 <= len(layer2) <= 4)
                self.assertTrue(2 <= len(units) <= 9)
                self.assertTrue(all(row.text.endswith("。") for row in units))
                self.assertTrue(
                    all(re.search(r"[ぁ-んァ-ヶ一-龯]", row.text) for row in units)
                )
                clause_plan_by_ref = {
                    row.clause_plan_ref: row
                    for row in result.selected_candidate.normalized_artifact.clause_plan_rows
                }
                layer2_plans = tuple(
                    clause_plan_by_ref[ref]
                    for unit in layer2
                    for ref in unit.clause_plan_refs
                )
                self.assertTrue(layer2_plans)
                self.assertTrue(
                    all(
                        row.syntactic_orientation
                        is stage1_composition_module.SyntacticOrientation.EMLIS_SUBJECT
                        and row.speaker_requirement
                        in {
                            stage1_composition_module.SpeakerRequirement.EMLIS_EXPLICIT_REQUIRED,
                            stage1_composition_module.SpeakerRequirement.EMLIS_ZERO_ALLOWED,
                        }
                        for row in layer2_plans
                    )
                )
                self.assertTrue(any("Emlis" in row.text for row in layer2))
                graph_node_ids = {row.node_id for row in graph.nodes}
                self.assertTrue(all(unit.basis_anchor_refs for unit in units))
                self.assertTrue(
                    all(
                        ref.split(":", 1)[1].split("@", 1)[0]
                        in graph_node_ids
                        for unit in units
                        for ref in unit.basis_anchor_refs
                    )
                )
                compact_source = re.sub(
                    r"\s+",
                    "",
                    str(_source.normalized_current_input.get("memo", "")),
                )
                quoted_source_fragments = tuple(
                    re.sub(r"\s+", "", value)
                    for unit in layer1
                    for value in re.findall(r"「([^」]+)」", unit.text)
                )
                def source_bound_or_registered_finite_form(value: str) -> bool:
                    if value in compact_source:
                        return True
                    return any(
                        value.endswith(finite_terminal)
                        and (
                            value[: -len(finite_terminal)] + source_terminal
                        ) in compact_source
                        for asset in stage1_composition_module.SOURCE_SCALAR_MORPHOLOGY_ASSET_REGISTRY
                        for source_terminal, finite_terminal in asset.terminal_rewrites
                    )

                self.assertGreaterEqual(
                    len(quoted_source_fragments),
                    len(layer1),
                )
                self.assertTrue(
                    all(
                        source_bound_or_registered_finite_form(value)
                        for value in quoted_source_fragments
                    )
                )
                if label == "temporal_change":
                    self.assertIn("散歩に出た", quoted_source_fragments)
                    self.assertNotIn("散歩に出", quoted_source_fragments)
                elif label == "unfinished":
                    self.assertIn(
                        "まだ気持ちが残っている",
                        quoted_source_fragments,
                    )
                    self.assertNotIn(
                        "まだ気持ちが残っていて",
                        quoted_source_fragments,
                    )
                normalized = result.selected_candidate.normalized_artifact
                realized_duties = tuple(
                    ref for unit in units for ref in unit.duty_refs
                )
                self.assertEqual(len(realized_duties), len(set(realized_duties)))
                self.assertEqual(
                    set(realized_duties),
                    set(normalized.required_duty_refs),
                )
                relation_duties = {
                    row.duty_ref
                    for row in normalized.composition_duty_rows
                    if row.relation_refs and row.retention == "REQUIRED"
                }
                self.assertTrue(relation_duties.issubset(set(realized_duties)))
                visible_bodies.append(tuple(row.text for row in units))
        self.assertEqual(len(visible_bodies), 4)
        self.assertEqual(len(set(visible_bodies)), 4)

    def test_scalar_surface_slots_bound_known_and_public_layer1_seams(self) -> None:
        module = stage1_composition_module
        grouped_rows = (
            (
                "known",
                tuple(
                    (label, memo, "生活", "不安", "medium")
                    for label, memo, *_expected in self._KNOWN_EXACT4
                ),
            ),
            ("public_standin", PUBLIC_NONSECRET_EARLY_STANDIN_EXACT4),
        )
        scalar_morphemes = {
            morpheme
            for asset in module.SCALAR_MORPHOLOGY_ASSET_REGISTRY
            for morpheme in asset.morphemes
        }
        fused_plan = None
        fused_row_index = None
        fused_normalized = None

        for group, rows in grouped_rows:
            self.assertEqual(len(rows), 4)
            for index, (label, memo, category, emotion, strength) in enumerate(
                rows
            ):
                with self.subTest(group=group, structural_family=label):
                    *_, phase_b = _final_stage1_composition_inputs(
                        _request(
                            record_id=(
                                "cmee-i1sx-early-"
                                + ("known" if group == "known" else "withheld")
                                + f"-{index + 1:02d}"
                            ),
                            memo=memo,
                            category=category,
                            emotion=emotion,
                            strength=strength,
                        )
                    )
                    selected = module.compose_stage1_from_projection(
                        phase_b
                    ).selected_candidate
                    normalized = selected.normalized_artifact
                    duty_by_ref = {
                        row.duty_ref: row
                        for row in normalized.composition_duty_rows
                    }
                    expression_by_plan_ref = {
                        row.clause_plan_ref: row
                        for row in normalized.response_object_expression_rows
                    }
                    layer1_plans = tuple(
                        row
                        for row in normalized.clause_plan_rows
                        if duty_by_ref[row.duty_ref].layer == "LAYER_1"
                    )
                    self.assertTrue(layer1_plans)
                    case_max_scalar_segment_run = 0
                    for plan in layer1_plans:
                        self.assertEqual(
                            plan.scalar_surface_realization_rows,
                            module.project_scalar_surface_realization_rows(
                                plan.clause_plan_ref,
                                plan.scalar_constraint_rows,
                            ),
                        )
                        duty = duty_by_ref[plan.duty_ref]
                        expression = expression_by_plan_ref[
                            plan.clause_plan_ref
                        ]
                        surface = module._surface_for_plan(
                            duty,
                            plan,
                            expression,
                            phase_b,
                        )
                        overt, fused = module._functional_surface_lexemes(plan)
                        owner, _refs = module._duty_semantics(duty, phase_b)
                        predicate_asset = module._expression_asset(
                            duty,
                            plan,
                            owner,
                        )
                        self.assertTrue(
                            all(
                                carrier in surface
                                for carrier in (
                                    *overt,
                                    *fused,
                                    *predicate_asset.predicate_lexemes,
                                )
                            )
                        )
                        if (
                            plan.semantic_clause_kind
                            is module.SemanticClauseKind.ADMITTED_RELATION
                        ):
                            role_local_carriers = (
                                module._functional_surface_lexemes_by_role(plan)
                            )
                            endpoint_roles = module._unique(
                                row.clause_argument_role
                                for row in plan.scalar_constraint_rows
                            )
                            self.assertEqual(
                                tuple(
                                    role
                                    for role, _overt, _fused
                                    in role_local_carriers
                                ),
                                endpoint_roles,
                            )
                            endpoint_surfaces = tuple(
                                module._source_expression(
                                    ref,
                                    phase_b,
                                    module._frame_for_semantic_ref(
                                        owner,
                                        ref,
                                        phase_b,
                                    ),
                                )
                                for ref in expression.basis_semantic_refs
                            )
                            left_endpoint_index = surface.index(
                                endpoint_surfaces[0]
                            )
                            right_endpoint_index = surface.index(
                                endpoint_surfaces[1],
                                left_endpoint_index + len(endpoint_surfaces[0]),
                            )
                            for endpoint_index, (
                                _role,
                                role_overt,
                                role_fused,
                            ) in zip(
                                (left_endpoint_index, right_endpoint_index),
                                role_local_carriers,
                            ):
                                carrier = module._structural_lexeme(
                                    "structural:comma.v1"
                                ).join((*role_overt, *role_fused))
                                if not carrier:
                                    continue
                                carrier_index = surface.index(
                                    carrier,
                                    endpoint_index,
                                )
                                self.assertGreater(carrier_index, endpoint_index)
                                if endpoint_index == left_endpoint_index:
                                    self.assertLess(
                                        carrier_index,
                                        right_endpoint_index,
                                    )
                                else:
                                    self.assertGreater(
                                        carrier_index,
                                        right_endpoint_index,
                                    )
                        if (
                            plan.semantic_clause_kind
                            is not module.SemanticClauseKind.ADMITTED_RELATION
                        ):
                            construction = next(
                                row
                                for row in module.CONSTRUCTION_REGISTRY
                                if row.construction_id == plan.construction_id
                            )
                            particles = dict(construction.particle_rules)
                            if (
                                plan.semantic_clause_kind
                                is module.SemanticClauseKind.SUBJECTIVE_PREDICATE
                            ):
                                subject_carrier = module._participant_lexeme(
                                    module.CMEE_STAGE1_EMLIS_OWNER_REF
                                )
                            else:
                                subject_carrier = module._response_object_surface(
                                    expression,
                                    owner,
                                    phase_b,
                                )[0]
                            self.assertIn(
                                subject_carrier
                                + particles[module.ClauseArgumentRole.SUBJECT],
                                surface,
                            )
                        current_run = 0
                        for segment in surface.removesuffix("。").split("、"):
                            if segment in scalar_morphemes:
                                current_run += 1
                                case_max_scalar_segment_run = max(
                                    case_max_scalar_segment_run,
                                    current_run,
                                )
                            else:
                                current_run = 0
                        if (overt or fused) and fused_plan is None:
                            fused_plan = plan
                            fused_normalized = normalized
                            fused_row_index = next(
                                row_index
                                for row_index, realization in enumerate(
                                    plan.scalar_surface_realization_rows
                                )
                                if realization.realization_mode
                                in {
                                    module.ScalarSurfaceRealizationMode.OVERT_FUNCTIONAL_PART,
                                    module.ScalarSurfaceRealizationMode.FUSED_IN_REGISTERED_PART,
                                }
                            )
                    self.assertLessEqual(case_max_scalar_segment_run, 1)

        self.assertIsNotNone(fused_plan)
        self.assertIsNotNone(fused_row_index)
        self.assertIsNotNone(fused_normalized)
        assert fused_plan is not None
        assert fused_row_index is not None
        assert fused_normalized is not None
        tampered_rows = list(fused_plan.scalar_surface_realization_rows)
        original_mode = tampered_rows[fused_row_index].realization_mode
        tampered_rows[fused_row_index] = replace(
            tampered_rows[fused_row_index],
            target_clause_slot_ref=(
                module.RegisteredFunctionalSlotRef.QUALIFIER.value
                if original_mode
                is module.ScalarSurfaceRealizationMode.FUSED_IN_REGISTERED_PART
                else module.RegisteredFunctionalSlotRef.PREDICATE_HEAD.value
            ),
        )
        with self.assertRaisesRegex(
            module.Stage1CompositionError,
            "STAGE1_SCALAR_MORPHOLOGY_NONUNIQUE_STOP",
        ):
            module._functional_surface_lexemes(
                replace(
                    fused_plan,
                    scalar_surface_realization_rows=tuple(tampered_rows),
                )
            )

        original_rows = fused_plan.scalar_surface_realization_rows
        alternate_index = None
        alternate_asset = None
        for row_index, realization in enumerate(original_rows):
            candidates = tuple(
                asset
                for asset in module.SCALAR_MORPHOLOGY_ASSET_REGISTRY
                if asset.scalar_axis is realization.scalar_axis
                and asset.realization_mode is realization.realization_mode
                and asset.realization_target_slot_ref
                == realization.target_clause_slot_ref
                and asset.morphology_asset_id
                != realization.registered_realization_rule_ref
            )
            if candidates:
                alternate_index = row_index
                alternate_asset = candidates[0]
                break
        self.assertIsNotNone(alternate_index)
        self.assertIsNotNone(alternate_asset)
        assert alternate_index is not None
        assert alternate_asset is not None
        alternate_rows = list(original_rows)
        alternate_rows[alternate_index] = replace(
            alternate_rows[alternate_index],
            registered_realization_rule_ref=alternate_asset.morphology_asset_id,
        )
        scalar_row_mutations = (
            ("missing", original_rows[:fused_row_index] + original_rows[fused_row_index + 1 :]),
            ("duplicate", (*original_rows, original_rows[fused_row_index])),
            ("reversed", tuple(reversed(original_rows))),
            ("same_axis_mode_slot_different_asset", tuple(alternate_rows)),
        )

        base_unit_index = next(
            index
            for index, unit in enumerate(fused_normalized.sentence_units)
            if fused_plan.clause_plan_ref in unit.clause_plan_refs
        )
        base_unit = fused_normalized.sentence_units[base_unit_index]
        co_tampered_text = base_unit.text.removesuffix("。") + "、。"
        co_tampered_unit = replace(
            base_unit,
            text=co_tampered_text,
            surface_text_sha256=hashlib.sha256(
                co_tampered_text.encode("utf-8")
            ).hexdigest(),
        )
        for mutation_name, mutated_rows in scalar_row_mutations:
            with self.subTest(scalar_row_mutation=mutation_name):
                mutated_plan = replace(
                    fused_plan,
                    scalar_surface_realization_rows=mutated_rows,
                )
                with self.assertRaisesRegex(
                    module.Stage1CompositionError,
                    "STAGE1_SCALAR_MORPHOLOGY_NONUNIQUE_STOP",
                ):
                    module._functional_surface_lexemes(mutated_plan)
                mutated_plans = tuple(
                    mutated_plan
                    if row.clause_plan_ref == fused_plan.clause_plan_ref
                    else row
                    for row in fused_normalized.clause_plan_rows
                )
                mutated_units = tuple(
                    co_tampered_unit if index == base_unit_index else unit
                    for index, unit in enumerate(fused_normalized.sentence_units)
                )
                defects = module._project_post_normalization_defect_rows(
                    arc=fused_normalized.discourse_arc,
                    seed=fused_normalized.layout_preference_seed,
                    duties=fused_normalized.composition_duty_rows,
                    required_duty_refs=fused_normalized.required_duty_refs,
                    suppressed_duty_rows=fused_normalized.suppressed_duty_rows,
                    clause_plans=mutated_plans,
                    expressions=fused_normalized.response_object_expression_rows,
                    units=mutated_units,
                )
                self.assertTrue(
                    any(
                        row.defect_kind
                        is module.CorrectableDefectKind.RELATION_OR_CONNECTIVE_FIT
                        and fused_plan.clause_plan_ref in row.defect_owner_refs
                        for row in defects
                    )
                )
                with self.assertRaisesRegex(
                    module.Stage1CompositionError,
                    "RECOMPOSITION_NORMAL_FORM_UNPROVEN_STOP",
                ):
                    module.canonical_normalized_bytes(
                        replace(
                            fused_normalized,
                            clause_plan_rows=mutated_plans,
                            sentence_units=mutated_units,
                        )
                    )

    def test_subjective_layer_transition_reestablishes_relation_objects_and_bounds_anaphora(
        self,
    ) -> None:
        module = stage1_composition_module
        singular_anaphora = 0
        plural_anaphora = 0
        for case_index in range(len(self._KNOWN_EXACT4)):
            with self.subTest(case_index=case_index):
                *_, phase_b = self._known_inputs(case_index)
                normalized = module.compose_stage1_from_projection(
                    phase_b
                ).selected_candidate.normalized_artifact
                unit_by_ref = {
                    row.unit_ref: row for row in normalized.sentence_units
                }
                unit_index = {
                    row.unit_ref: index
                    for index, row in enumerate(normalized.sentence_units)
                }
                layer1_refs = {
                    row.basis_semantic_refs
                    for row in normalized.response_object_expression_rows
                    if unit_by_ref[row.unit_ref].layer == "LAYER_1"
                }
                seen_layer2_refs: set[tuple[str, ...]] = set()
                for expression in normalized.response_object_expression_rows:
                    unit = unit_by_ref[expression.unit_ref]
                    if unit.layer == "LAYER_2":
                        if (
                            expression.basis_semantic_refs in layer1_refs
                            and expression.basis_semantic_refs
                            not in seen_layer2_refs
                        ):
                            self.assertIsNot(
                                expression.expression_mode,
                                module.ResponseObjectExpressionMode.ANAPHORIC,
                            )
                        seen_layer2_refs.add(expression.basis_semantic_refs)
                    if (
                        expression.expression_mode
                        is module.ResponseObjectExpressionMode.ANAPHORIC
                    ):
                        antecedent = unit_by_ref[
                            expression.antecedent_unit_ref
                        ]
                        self.assertEqual(antecedent.layer, unit.layer)
                        self.assertLess(
                            unit_index[antecedent.unit_ref],
                            unit_index[unit.unit_ref],
                        )
                        if len(expression.basis_semantic_refs) == 1:
                            singular_anaphora += 1
                            self.assertIn("そのこと", unit.text)
                            self.assertEqual(
                                unit_index[antecedent.unit_ref] + 1,
                                unit_index[unit.unit_ref],
                            )
                        else:
                            plural_anaphora += 1
                            self.assertIn("その両方", unit.text)
                            self.assertNotIn("そのことを", unit.text)
        self.assertGreaterEqual(singular_anaphora, 1)
        self.assertGreaterEqual(plural_anaphora, 1)

    def test_source_scalar_uses_exact_normalized_raw_text_and_typed_finite_morphology(self) -> None:
        def source_expression_by_predicate_kind(
            phase_b: object,
            predicate_kind: str,
        ) -> tuple[str, object, str]:
            candidate_by_ref = {
                row.candidate_id: row
                for row in phase_b.projection.interpretation_candidates
            }
            frame_rows = tuple(
                row
                for row in phase_b.resolved_grounded_frame_by_candidate_ref
                if row.grounded_frame.predicate_kind == predicate_kind
                and any(
                    code.startswith("surface_scalar_range:")
                    for code in row.grounded_frame.attribute_codes
                )
            )
            self.assertEqual(len(frame_rows), 1)
            frame_row = frame_rows[0]
            candidate = candidate_by_ref[frame_row.candidate_ref]
            primary_refs = tuple(
                binding.semantic_ref
                for binding in candidate.argument_bindings
                if binding.role is ArgumentRole.PRIMARY
            )
            self.assertEqual(len(primary_refs), 1)
            return (
                stage1_composition_module._source_expression(
                    primary_refs[0],
                    phase_b,
                    frame_row.grounded_frame,
                ),
                frame_row,
                primary_refs[0],
            )

        *_, b_phase_b = self._known_inputs(1)
        b_action, b_action_row, b_action_ref = source_expression_by_predicate_kind(
            b_phase_b,
            "action",
        )
        self.assertEqual(b_action, "「散歩に出た」ということ")

        *_, d_phase_b = self._known_inputs(3)
        d_residue, _d_residue_row, _d_residue_ref = (
            source_expression_by_predicate_kind(d_phase_b, "residue")
        )
        self.assertEqual(d_residue, "「まだ気持ちが残っている」ということ")
        self.assertNotIn("残っていて", d_residue)

        *_, spaced_phase_b = _final_stage1_composition_inputs(
            _request(
                record_id="stage2-source-scalar-whitespace",
                memo=(
                    "椅子に\u3000  座ったら、少し落ち着いた。"
                    "ただ、いつもそうなるとは思っていない。"
                ),
            )
        )
        spaced_action, _spaced_row, _spaced_ref = (
            source_expression_by_predicate_kind(spaced_phase_b, "action")
        )
        self.assertEqual(spaced_action, "「椅子に 座った」ということ")

        source_marker = "surface_scalar_source:normalized_raw_text"
        invalid_marker_sets = (
            (),
            ("surface_scalar_source:graph_node_value",),
            (source_marker, source_marker),
        )
        original_codes = tuple(b_action_row.grounded_frame.attribute_codes)
        codes_without_source_marker = tuple(
            code
            for code in original_codes
            if not code.startswith("surface_scalar_source:")
        )
        for source_markers in invalid_marker_sets:
            with self.subTest(source_markers=source_markers):
                tampered_frame = replace(
                    b_action_row.grounded_frame,
                    attribute_codes=(*codes_without_source_marker, *source_markers),
                )
                tampered_phase_b = replace(
                    b_phase_b,
                    resolved_grounded_frame_by_candidate_ref=tuple(
                        replace(row, grounded_frame=tampered_frame)
                        if row.candidate_ref == b_action_row.candidate_ref
                        else row
                        for row in b_phase_b.resolved_grounded_frame_by_candidate_ref
                    ),
                )
                with self.assertRaisesRegex(
                    stage1_composition_module.Stage1CompositionError,
                    "STAGE1_SOURCE_SCALAR_RANGE_STOP",
                ):
                    stage1_composition_module._source_expression(
                        b_action_ref,
                        tampered_phase_b,
                        tampered_frame,
                    )

        self.assertEqual(
            {
                row.predicate_kind
                for row in stage1_composition_module.SOURCE_SCALAR_MORPHOLOGY_ASSET_REGISTRY
            },
            {"action", "change", "residue", "unfinished"},
        )
        stage1_composition_module.validate_language_core_registry_invariant()

    def test_exact6_normalizer_is_single_pass_idempotent_and_defect_free(self) -> None:
        *_, phase_b = self._known_inputs(3)
        original_normalizer = stage1_composition_module.normalize_to_normal_form
        with patch.object(
            stage1_composition_module,
            "normalize_to_normal_form",
            wraps=original_normalizer,
        ) as normalizer:
            result = stage1_composition_module.compose_stage1_from_projection(
                phase_b
            )
        self.assertEqual(normalizer.call_count, result.internal_candidate_count)
        representative = result.ranked_candidates[0].normalized_artifact
        with self.assertRaisesRegex(
            stage1_composition_module.Stage1CompositionError,
            "RECOMPOSITION_NORMAL_FORM_INPUT_STOP",
        ):
            original_normalizer(
                SimpleNamespace(
                    projection_ref=representative.projection_ref,
                    layout_preference_seed=representative.layout_preference_seed,
                ),
                representative.layout_preference_seed,
                phase_b,
            )
        for candidate in result.ranked_candidates:
            with self.subTest(rank=candidate.rank):
                first = candidate.normalized_artifact
                second = original_normalizer(
                    first,
                    first.layout_preference_seed,
                    phase_b,
                )
                self.assertEqual(
                    stage1_composition_module.canonical_normalized_bytes(first),
                    stage1_composition_module.canonical_normalized_bytes(second),
                )
                self.assertEqual(
                    first.normalization_phase_trace,
                    tuple(stage1_composition_module.NormalFormPhase),
                )
                self.assertEqual(len(first.normalization_phase_trace), 6)
                self.assertEqual(first.correctable_defect_rows, ())
                self.assertEqual(second.correctable_defect_rows, ())
                self.assertEqual(first.full_duty_refs, second.full_duty_refs)
                self.assertEqual(first.required_duty_refs, second.required_duty_refs)
                self.assertEqual(
                    first.suppressed_duty_rows,
                    second.suppressed_duty_rows,
                )
                self.assertEqual(first.sentence_units, second.sentence_units)
                self.assertTrue(
                    all(
                        row.surface_text_sha256
                        == hashlib.sha256(row.text.encode("utf-8")).hexdigest()
                        for row in first.sentence_units
                    )
                )
                self.assertEqual(
                    first.response_object_expression_rows,
                    second.response_object_expression_rows,
                )

    def test_normalized_tamper_is_rejected_with_corresponding_typed_defect(self) -> None:
        module = stage1_composition_module
        *_, phase_b = self._known_inputs(3)
        normalized = module.compose_stage1_from_projection(
            phase_b
        ).selected_candidate.normalized_artifact

        def project_defects(artifact: object):
            return module._project_post_normalization_defect_rows(
                arc=artifact.discourse_arc,
                seed=artifact.layout_preference_seed,
                duties=artifact.composition_duty_rows,
                required_duty_refs=artifact.required_duty_refs,
                suppressed_duty_rows=artifact.suppressed_duty_rows,
                clause_plans=artifact.clause_plan_rows,
                expressions=artifact.response_object_expression_rows,
                units=artifact.sentence_units,
            )

        self.assertEqual(project_defects(normalized), ())
        first_duty_ref = normalized.sentence_units[0].duty_refs[0]
        self.assertNotEqual(
            first_duty_ref,
            normalized.layout_preference_seed.terminal_duty_ref,
        )
        terminal_tamper = replace(
            normalized,
            layout_preference_seed=replace(
                normalized.layout_preference_seed,
                terminal_duty_ref=first_duty_ref,
            ),
        )
        required_duty_tamper = replace(
            normalized,
            required_duty_refs=normalized.required_duty_refs[:-1],
        )

        anaphoric_index = next(
            index
            for index, row in enumerate(
                normalized.response_object_expression_rows
            )
            if row.expression_mode
            is module.ResponseObjectExpressionMode.ANAPHORIC
        )
        anaphoric = normalized.response_object_expression_rows[anaphoric_index]
        antecedent_tamper = replace(
            normalized,
            response_object_expression_rows=tuple(
                replace(row, antecedent_unit_ref=row.unit_ref)
                if index == anaphoric_index
                else row
                for index, row in enumerate(
                    normalized.response_object_expression_rows
                )
            ),
        )
        grounded_dependency_index = next(
            index
            for index, row in enumerate(normalized.discourse_arc.dependency_rows)
            if row.dependency_kind
            is module.ArcDependencyKind.GROUNDED_BEFORE_SUBJECTIVE
            and row.successor_owner_ref
            not in normalized.discourse_arc.terminal_owner_refs
        )
        grounded_dependency = normalized.discourse_arc.dependency_rows[
            grounded_dependency_index
        ]
        terminal_owner_ref = normalized.discourse_arc.terminal_owner_refs[0]
        self.assertNotEqual(
            grounded_dependency.predecessor_owner_ref,
            terminal_owner_ref,
        )
        dependency_tamper = replace(
            normalized,
            discourse_arc=replace(
                normalized.discourse_arc,
                dependency_rows=tuple(
                    replace(row, predecessor_owner_ref=terminal_owner_ref)
                    if index == grounded_dependency_index
                    else row
                    for index, row in enumerate(
                        normalized.discourse_arc.dependency_rows
                    )
                ),
            ),
        )
        surface_tamper = replace(
            normalized,
            sentence_units=(
                replace(normalized.sentence_units[0], text="改ざん。"),
                *normalized.sentence_units[1:],
            ),
        )

        cases = (
            (
                "terminal",
                terminal_tamper,
                module.CorrectableDefectKind.TERMINAL_FIT,
            ),
            (
                "required-duty",
                required_duty_tamper,
                module.CorrectableDefectKind.NONMATERIAL_OR_DUPLICATE_DUTY,
            ),
            (
                "antecedent",
                antecedent_tamper,
                module.CorrectableDefectKind.UNRESOLVED_OR_DISTANT_REFERENT,
            ),
            (
                "dependency",
                dependency_tamper,
                module.CorrectableDefectKind.DEPENDENCY_OR_INFORMATION_ORDER,
            ),
            (
                "surface-seal",
                surface_tamper,
                module.CorrectableDefectKind.TERMINAL_FIT,
            ),
        )
        for label, tampered, expected_kind in cases:
            with self.subTest(tamper=label):
                defects = project_defects(tampered)
                matching = tuple(
                    row for row in defects if row.defect_kind is expected_kind
                )
                self.assertEqual(len(matching), 1)
                self.assertTrue(matching[0].defect_owner_refs)
                with self.assertRaisesRegex(
                    module.Stage1CompositionError,
                    "RECOMPOSITION_NORMAL_FORM_UNPROVEN_STOP",
                ):
                    module.canonical_normalized_bytes(tampered)
                with self.assertRaisesRegex(
                    module.Stage1CompositionError,
                    "STAGE1_PROFILE_INPUT_STOP",
                ):
                    module.derive_discourse_preference_profile(tampered)

        reordered_units = replace(
            normalized,
            sentence_units=tuple(reversed(normalized.sentence_units)),
        )
        with self.assertRaisesRegex(
            module.Stage1CompositionError,
            "STAGE1_PROFILE_INPUT_STOP",
        ):
            module.derive_discourse_preference_profile(reordered_units)

    def test_material_alternate_runs_final_profile_and_global_rank_path(self) -> None:
        *_, phase_b = self._known_inputs(1)
        arc = stage1_composition_module.project_stage1_discourse_arc(phase_b)
        duties = stage1_composition_module._project_duties(phase_b, arc)
        seeds = stage1_composition_module._layout_seeds(duties, arc)
        self.assertTrue(2 <= len(seeds) <= 32)
        exact5_dimension_values = tuple(
            {
                stage1_canonical_json_bytes(getattr(seed, field_name))
                for seed in seeds
            }
            for field_name in (
                "opening_duty_ref",
                "layer1_group_rows",
                "layer2_group_rows",
                "subjective_progression_duty_refs",
                "terminal_duty_ref",
            )
        )
        exact5_dimension_counts = tuple(
            len(values) for values in exact5_dimension_values
        )
        self.assertTrue(
            all(1 <= count <= 2 for count in exact5_dimension_counts)
        )
        self.assertIn(2, exact5_dimension_counts)
        original_normalizer = stage1_composition_module.normalize_to_normal_form
        original_profile_projector = (
            stage1_composition_module._derive_discourse_preference_profile_with_frozen_applicability
        )
        original_applicability_projector = (
            stage1_composition_module._derive_profile_applicability_mask
        )
        with patch.object(
            stage1_composition_module,
            "normalize_to_normal_form",
            wraps=original_normalizer,
        ) as normalizer, patch.object(
            stage1_composition_module,
            "_derive_discourse_preference_profile_with_frozen_applicability",
            wraps=original_profile_projector,
        ) as profile_projector:
            with patch.object(
                stage1_composition_module,
                "_derive_profile_applicability_mask",
                wraps=original_applicability_projector,
            ) as applicability_projector:
                result = (
                    stage1_composition_module.compose_stage1_from_projection(
                        phase_b
                    )
                )
        self.assertGreaterEqual(result.internal_candidate_count, 2)
        self.assertEqual(normalizer.call_count, result.internal_candidate_count)
        self.assertGreaterEqual(normalizer.call_count, 2)
        self.assertGreaterEqual(profile_projector.call_count, 2)
        self.assertEqual(applicability_projector.call_count, 1)
        self.assertEqual(
            tuple(
                inspect.signature(
                    stage1_composition_module.derive_discourse_preference_profile
                ).parameters
            ),
            ("normalized_artifact",),
        )
        with self.assertRaises(TypeError):
            stage1_composition_module.derive_discourse_preference_profile(
                result.ranked_candidates[0].normalized_artifact,
                applicability_mask=(True, False, *(True for _ in range(6))),
            )
        self.assertEqual(len(result.ranked_candidates), 2)
        self.assertEqual(
            tuple(row.rank for row in result.ranked_candidates),
            (1, 2),
        )
        self.assertEqual(result.selected_candidate, result.ranked_candidates[0])
        self.assertEqual(result.selected_candidate.rank, 1)
        self.assertEqual(
            len({row.composition_signature for row in result.ranked_candidates}),
            len(result.ranked_candidates),
        )
        visible_keys = tuple(
            stage1_composition_module._visible_key(row.normalized_artifact)
            for row in result.ranked_candidates
        )
        self.assertEqual(len(visible_keys), 2)
        self.assertEqual(len(set(visible_keys)), 2)
        preserved_seed_partitions = []
        for candidate in result.ranked_candidates:
            normalized = candidate.normalized_artifact
            seed = normalized.layout_preference_seed
            normalized_groups = tuple(
                stage1_composition_module.DutyGroupRow(unit.duty_refs)
                for unit in normalized.sentence_units
            )
            expected_groups = (
                *seed.layer1_group_rows,
                *seed.layer2_group_rows,
            )
            self.assertEqual(normalized_groups, expected_groups)
            self.assertEqual(
                tuple(
                    ref
                    for unit in normalized.sentence_units
                    if unit.layer == "LAYER_2"
                    for ref in unit.duty_refs
                ),
                seed.subjective_progression_duty_refs,
            )
            preserved_seed_partitions.append(
                tuple(group.ordered_duty_refs for group in expected_groups)
            )
        self.assertEqual(len(set(preserved_seed_partitions)), 2)
        self.assertTrue(
            all(
                len(row.discourse_preference_profile.profile_evidence_rows) == 8
                and row.normalized_artifact.correctable_defect_rows == ()
                for row in result.ranked_candidates
            )
        )

        profile_field_names = stage1_composition_module.PROFILE_RULE_REGISTRY
        not_applicable_masks = tuple(
            tuple(
                getattr(candidate.discourse_preference_profile, field_name)
                is stage1_composition_module.ProfileFit.NOT_APPLICABLE
                for field_name in profile_field_names
            )
            for candidate in result.ranked_candidates
        )
        self.assertEqual(len(set(not_applicable_masks)), 1)
        self.assertFalse(any(not_applicable_masks[0]))
        invalid_na_profile = replace(
            result.ranked_candidates[0].discourse_preference_profile,
            subjective_sequence_fit=(
                stage1_composition_module.ProfileFit.NOT_APPLICABLE
            ),
        )
        with self.assertRaisesRegex(
            stage1_composition_module.Stage1CompositionError,
            "STAGE1_PROFILE_APPLICABILITY_STOP",
        ):
            stage1_composition_module._profile_key(invalid_na_profile)

        sentence_load_evidence = tuple(
            next(
                row
                for row in candidate.discourse_preference_profile.profile_evidence_rows
                if row.profile_field
                is stage1_composition_module.ProfileEvidenceField.SENTENCE_LOAD
            )
            for candidate in result.ranked_candidates
        )
        self.assertEqual(
            {row.result for row in sentence_load_evidence},
            {
                stage1_composition_module.ProfileFit.ARC_ALIGNED,
                stage1_composition_module.ProfileFit.PERMITTED,
            },
        )
        self.assertEqual(
            len(
                {
                    stage1_canonical_json_bytes(row)
                    for row in sentence_load_evidence
                }
            ),
            2,
        )

        fit_rank = {
            stage1_composition_module.ProfileFit.ARC_ALIGNED: 0,
            stage1_composition_module.ProfileFit.PERMITTED: 1,
        }
        for candidate, not_applicable_mask in zip(
            result.ranked_candidates,
            not_applicable_masks,
            strict=True,
        ):
            profile = candidate.discourse_preference_profile
            expected_profile_key = tuple(
                fit_rank[getattr(profile, field_name)]
                for field_name, excluded in zip(
                    profile_field_names,
                    not_applicable_mask,
                    strict=True,
                )
                if not excluded
            )
            self.assertEqual(
                stage1_composition_module._profile_key(profile),
                expected_profile_key,
            )
            self.assertEqual(
                len(expected_profile_key),
                len(profile_field_names) - sum(not_applicable_mask),
            )
        profile_fields = stage1_composition_module.PROFILE_RULE_REGISTRY
        rank_keys = tuple(
            (
                tuple(
                    fit_rank[getattr(row.discourse_preference_profile, field)]
                    for field in profile_fields
                    if getattr(row.discourse_preference_profile, field)
                    is not stage1_composition_module.ProfileFit.NOT_APPLICABLE
                ),
                row.composition_signature,
            )
            for row in result.ranked_candidates
        )
        self.assertEqual(rank_keys, tuple(sorted(rank_keys)))

    def test_language_core_identity_is_independent_exact16_framed_digest(self) -> None:
        module = stage1_composition_module
        repository_root = Path(__file__).resolve().parents[2]
        exact16_names = (
            "ai/services/ai_inference/cocolon_meaning_experience_engine/emlis_stage1_composition.py",
            "ai/services/ai_inference/cocolon_meaning_experience_engine/contracts.py",
            "ai/services/ai_inference/cocolon_meaning_experience_engine/emlis_stage1_response.py",
            "ai/services/ai_inference/cocolon_meaning_experience_engine/emlis_v1a.py",
            "ai/services/ai_inference/emlis_ai_grounded_observation_plan.py",
            "ai/services/ai_inference/cocolon_text_generation_core/composer.py",
            "ai/services/ai_inference/cocolon_text_generation_core/adapters/emlis_observation_composer.py",
            "language_core_contract_manifest",
            "construction_registry",
            "emlis_expression_assets",
            "response_object_reference_assets",
            "functional_surface_assets",
            "participant_lexeme_assets",
            "structural_surface_assets",
            "policy_and_enum_manifest",
            "normal_form_and_profile_manifest",
        )
        payloads = module.language_core_identity_payloads(repository_root)
        self.assertEqual(tuple(name for name, _payload in payloads), exact16_names)
        self.assertEqual(len({name for name, _payload in payloads}), 16)
        for path, payload in payloads[:7]:
            self.assertEqual(payload, (repository_root / path).read_bytes())

        expected_contract_names = (
            "EmlisSubjectiveClaim", "SubjectiveBasisBinding",
            "SourceQualifierBinding", "PolicyBasisBinding",
            "EmlisAffectContent", "EmlisAppraisalContent",
            "EmlisRelationalPosition", "RowRefFreeValueApplication",
            "RowRefFreeMaterialValueContent", "RowRefFreeSubjectivePropositionV2",
            "SubjectiveClaimDraft", "MaterialValueContent", "ValueApplication",
            "Stage1PolicyFeatureVector", "PolicyApplicationSeed",
            "PolicyApplicationRow", "SubjectivePropositionV2",
            "EmlisStage1Projection", "Stage1SubjectivePlanningInputs",
            "Stage1SurfaceCompositionInputs", "EmlisSubjectiveMeaningPlan",
            "SubjectiveResponsibilityRow", "SubjectiveOpportunityRow",
            "SubjectiveFacetSuppressionRow", "Stage1DiscourseArcView",
            "ArcDependencyRow", "CompositionDutyView", "DutySuppressionRow",
            "ClaimSuppressionRow", "DiscourseReferenceStateRow", "ClauseIntent",
            "ClauseSourceBindingCoverage", "ClauseScalarConstraintRow",
            "ScalarSurfaceCoverageKey", "ScalarSurfaceRealizationRow",
            "ClauseSubjectBinding", "ClauseArgumentSlotBinding", "ClausePlan",
            "ResponseObjectExpression", "SurfacePartPlan",
            "SurfaceProjectionContext", "ClauseFrame", "RealizedSentenceUnit",
            "LayoutPreferenceSeed", "DutyGroupRow", "EmlisCompositionLayout",
            "CorrectableDefectRow", "DraftArtifact", "NormalizedDraftArtifact",
            "SealedCompositionPlan", "SealedUnitPlanRow",
            "RankableNormalizedMember", "ArtifactCompositionCandidate",
            "DiscoursePreferenceProfile", "ProfileEvidenceRow",
            "GrammaticalShapeKey", "SurfaceDerivation",
            "RealizedSurfaceBindingV2", "EmlisStage1PositiveTraceExtensionV2",
        )
        contract_manifest = dict(module._contract_manifest())
        descriptors = contract_manifest["logical_contract_descriptors"]
        self.assertEqual(contract_manifest["logical_contract_count"], 59)
        self.assertEqual(
            tuple(dict(row)["type_name"] for row in descriptors),
            expected_contract_names,
        )
        expected_descriptor_keys = (
            "type_name", "logical_version", "serialization_boundary", "fields",
            "conditional_constraints", "derivation",
        )
        expected_field_keys = (
            "field_name", "logical_type", "cardinality", "default",
            "conditional_constraints", "derivation",
        )
        for descriptor in descriptors:
            descriptor_map = dict(descriptor)
            self.assertEqual(tuple(descriptor_map), expected_descriptor_keys)
            self.assertTrue(descriptor_map["fields"])
            field_names = []
            for field_descriptor in descriptor_map["fields"]:
                field_map = dict(field_descriptor)
                self.assertEqual(tuple(field_map), expected_field_keys)
                self.assertEqual(field_map["default"], "NO_IMPLICIT_DEFAULT")
                self.assertTrue(field_map["cardinality"])
                field_names.append(field_map["field_name"])
            self.assertEqual(len(field_names), len(set(field_names)))
        self.assertEqual(len(module.LANGUAGE_CORE_CONTENT_DERIVATION_ROWS), 5)
        expected_concrete_descriptors = (
            ("ProjectedSubjectiveClaim", ("schema_version", "subjective_claim_id", "parent_duty_ref", "speaker_owner", "claim_domain", "subjective_responsibility_refs", "selected_subjective_opportunity_key", "asserted_subjective_proposition", "basis_observation_contribution_refs", "basis_semantic_refs", "source_reception_act_refs", "value_principle_refs", "user_fact_effect", "forbidden_promotions")),
            ("CandidateFrameRow", ("candidate_ref", "grounded_frame")),
            ("RelationEndpointCandidateRow", ("relation_candidate_ref", "source_argument_role", "source_semantic_ref", "endpoint_grounded_candidate_ref")),
            ("QualifierValueRow", ("candidate_ref", "qualifier_scope", "source_argument_role", "source_semantic_ref", "axis", "value")),
            ("RetainedReceptionActRow", ("act_ref", "reception_act", "basis_contribution_refs")),
            ("ComposedSentenceUnit", ("unit_ref", "layer", "duty_refs", "sentence_job_refs", "basis_anchor_refs", "clause_plan_refs", "text", "surface_text_sha256")),
            ("Stage1CompositionResult", ("language_core_identity", "discourse_arc", "internal_candidate_count", "ranked_candidates", "selected_candidate")),
            ("SourceScalarMorphologyAssetSpec", ("morphology_asset_id", "predicate_kind", "required_attribute_codes", "terminal_rewrites", "preserved_finite_terminals")),
        )
        self.assertEqual(
            module.LANGUAGE_CORE_CONCRETE_BINDING_DESCRIPTORS,
            expected_concrete_descriptors,
        )
        for type_name, expected_field_names in expected_concrete_descriptors:
            self.assertEqual(
                tuple(field.name for field in fields(getattr(module, type_name))),
                expected_field_names,
            )
        module._validate_concrete_binding_descriptors()
        self.assertEqual(
            module.FUNCTIONAL_ASSET_REGISTRY[-1],
            module.SOURCE_SCALAR_MORPHOLOGY_ASSET_REGISTRY,
        )

        expected_enum_name_counts = (
            ("SubjectiveResponsibilityKind", 4), ("SubjectiveSpecificity", 3),
            ("SubjectiveFacetSuppressionReason", 3), ("ArcDependencyKind", 5),
            ("SentenceJob", 8), ("DutySuppressionReason", 3),
            ("ResponseObjectExpressionMode", 3), ("GroundedPredicateKind", 14),
            ("RelationOperator", 6), ("ArgumentRole", 10),
            ("ClauseArgumentRole", 11), ("QualifierLookupScope", 2),
            ("SemanticClauseKind", 3), ("SubjectivePredicationKind", 5),
            ("PredicateValency", 4), ("ClauseScalarConstraintOwnerKind", 2),
            ("ClauseScalarAxis", 3), ("ScalarSurfaceRealizationMode", 4),
            ("GrammaticalRoleAssignmentRule", 4), ("SyntacticOrientation", 5),
            ("SpeakerRequirement", 3), ("SubjectOriginKind", 3),
            ("SubjectRealizationMode", 2), ("ActiveReferentEstablishmentKind", 4),
            ("SpeakerResolutionStatus", 2), ("SurfaceDerivationKind", 8),
            ("SurfaceBindingKind", 8), ("CorrectableDefectKind", 8),
            ("NormalFormPhase", 6), ("ProfileFit", 3),
            ("ProfileEvidenceField", 8), ("ProfileEvidenceRuleKind", 8),
            ("RegisteredFunctionalSlotRef", 2), ("SubjectiveContentKind", 4),
            ("SubjectiveMode", 6), ("SubjectiveOperator", 6),
            ("SubjectiveAssertionModality", 5), ("SubjectiveBasisRole", 11),
            ("PolicyBasisOwnerKind", 2), ("PolicyBasisRole", 7),
            ("MaterialRisk", 9), ("RelationalPositionKind", 2),
            ("RelationalCommitment", 6), ("RelationalClosure", 3),
        )
        self.assertEqual(
            tuple((name, len(values)) for name, values in module.LANGUAGE_CORE_CLOSED_ENUM_MANIFEST),
            expected_enum_name_counts,
        )
        self.assertEqual(
            tuple(name for name, _fields in module.LANGUAGE_CORE_REF_PREIMAGE_MANIFEST),
            (
                "projection_preimage_ref", "subjective_basis_binding_ref",
                "source_qualifier_binding_ref", "policy_basis_binding_ref",
                "subjective_responsibility_ref", "subjective_opportunity_key",
                "arc_dependency_ref", "stage1_discourse_arc_ref",
                "composition_duty_ref", "reference_state_ref",
                "affected_claim_policy_target_key", "policy_application_row_ref",
                "clause_scalar_constraint_ref", "clause_intent_ref",
                "clause_plan_ref", "response_object_expression_ref",
                "profile_evidence_ref", "unit_ref", "composition_layout_id",
                "candidate_id", "selected_stage1_artifact_ref",
            ),
        )
        self.assertEqual(len(module.LANGUAGE_CORE_LAYOUT_SEED_EXACT5_RULES), 5)
        self.assertEqual(len(module.LANGUAGE_CORE_NORMAL_FORM_EXACT6_RULES), 6)
        self.assertEqual(
            tuple(
                (row[0], row[1], row[3])
                for row in module.LANGUAGE_CORE_PROFILE_EXACT8_RULES
            ),
            (
                ("INFORMATION_FLOW", "ARC_DEPENDENCY", "REQUIRED_APPLICABLE"),
                ("CONCRETE_BEFORE_ABSTRACT", "CONCRETE_INTRODUCTION", "POOL_GLOBAL_OPTIONAL"),
                ("SENTENCE_LOAD", "PREDICATION_LOAD", "REQUIRED_APPLICABLE"),
                ("TOPIC_TRANSITION", "TOPIC_STATE", "REQUIRED_APPLICABLE"),
                ("REFERENT_CONTINUITY", "REFERENT_STATE", "REQUIRED_APPLICABLE"),
                ("RELATION_REALIZATION", "RELATION_REALIZATION", "REQUIRED_APPLICABLE"),
                ("SUBJECTIVE_SEQUENCE", "SUBJECTIVE_DEPENDENCY", "REQUIRED_APPLICABLE"),
                ("TERMINAL", "TERMINAL_DUTY", "REQUIRED_APPLICABLE"),
            ),
        )
        self.assertEqual(
            Counter(row[3] for row in module.LANGUAGE_CORE_PROFILE_EXACT8_RULES),
            Counter({"REQUIRED_APPLICABLE": 7, "POOL_GLOBAL_OPTIONAL": 1}),
        )
        self.assertEqual(len(module.LANGUAGE_CORE_STAGE_A_B_RULES), 3)

        suppression_features = (
            "PRESENT_BURDEN", "PRESENT_RESIDUE", "OBSERVE_BURDEN",
            "PRESERVE_RESIDUE", "PRESENT_DIRECTION", "PRESENT_CHANGE",
            "PRESENT_ACTUAL_OUTPUT", "COEXISTS_WITH", "TENSION_WITH",
            "PRESENT_UNFINISHED", "PRESERVE_UNFINISHED", "material_unknown",
            "actual_output_retention_required",
        )
        visibility_features = (*suppression_features[:11], suppression_features[12])
        acts = (
            "stay_with_current_burden", "honor_concrete_effort",
            "protect_retained_intention", "recognize_lived_change",
            "hold_help_seeking", "bounded_counter_self_denial",
            "respect_words_placed",
        )
        principle_refs = tuple(
            (code, f"policy:{code}@cocolon.emlis.stage1.value_policy.v1")
            for code in ("V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8", "V9")
        )

        def vectors(width: int) -> tuple[tuple[bool, ...], ...]:
            return tuple(
                tuple(
                    bool((integer >> (width - position - 1)) & 1)
                    for position in range(width)
                )
                for integer in range(1 << width)
            )

        def suppression_codes(bits: tuple[bool, ...]) -> tuple[str, ...]:
            selected = set()
            if any(bits[index] for index in (0, 1, 2, 3)):
                selected.add("V1")
            if bits[4]:
                selected.update(("V2", "V8"))
            if bits[5] or bits[6]:
                selected.update(("V4", "V5"))
            if bits[7] or bits[8]:
                selected.add("V6")
            if bits[9] or bits[10]:
                selected.update(("V3", "V7", "V9"))
            if bits[11]:
                selected.add("V9")
            return tuple(code for code, _ref in principle_refs if code in selected)

        def visible_refs(bits: tuple[bool, ...], act: str) -> tuple[str, ...]:
            if act == "bounded_counter_self_denial":
                codes = {"V1", "V8"}
            elif act == "protect_retained_intention" and bits[4] and (
                bits[0] or bits[7] or bits[8]
            ):
                codes = {"V2", "V8"}
            elif act == "hold_help_seeking" and bits[6] and bits[11]:
                codes = {"V8"}
            else:
                codes = set()
            return tuple(ref for code, ref in principle_refs if code in codes)

        suppression_rows = tuple(
            (bits, suppression_codes(bits)) for bits in vectors(13)
        )
        visibility_rows = tuple(
            (bits, act, visible_refs(bits, act))
            for bits in vectors(12)
            for act in acts
        )
        self.assertEqual(len(suppression_rows), 8192)
        self.assertEqual(len(visibility_rows), 28672)
        independent_policy_payload = (
            (
                ("schema_version", "cocolon.cmee.v1a.stage1_policy_behavior_matrix.v1"),
                ("suppression_feature_fields", suppression_features),
                ("visibility_feature_fields", visibility_features),
                ("boolean_iteration_order", ("FALSE", "TRUE")),
                ("reception_act_order", acts),
            ),
            ("suppression_rows", suppression_rows),
            ("visibility_rows", visibility_rows),
        )
        independent_policy_digest = hashlib.sha256(
            stage1_canonical_json_bytes(independent_policy_payload)
        ).hexdigest()
        self.assertEqual(
            independent_policy_digest,
            "3cd429305e05f41e13fed60c14f24e7060c25c011da20dbf9ef159c05c751327",
        )
        self.assertEqual(independent_policy_digest, module.POLICY_BEHAVIOR_DIGEST)
        self.assertEqual(independent_policy_digest, module.recompute_policy_behavior_digest())
        self.assertEqual(
            module.recompute_policy_behavior_digest(),
            module.recompute_policy_behavior_digest(),
        )
        with patch.object(module, "POLICY_BEHAVIOR_DIGEST", "0" * 64):
            with self.assertRaisesRegex(
                module.Stage1CompositionError,
                "LANGUAGE_CORE_POLICY_BEHAVIOR_DIGEST_STOP",
            ):
                module.language_core_identity_payloads(repository_root)

        expected_owner_paths = exact16_names[:7]
        self.assertEqual(
            tuple(path for path, _names in module.LANGUAGE_CORE_PRODUCT_CAUSAL_OWNER_MANIFEST),
            expected_owner_paths,
        )
        for path, callable_names in module.LANGUAGE_CORE_PRODUCT_CAUSAL_OWNER_MANIFEST:
            tree = ast.parse((repository_root / path).read_text(encoding="utf-8"))
            top_level_functions = {
                node.name
                for node in tree.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
            self.assertTrue(set(callable_names).issubset(top_level_functions))

        framed = bytearray(b"COCOLON_CMEE_STAGE1_LANGUAGE_CORE_IDENTITY_V1\x00")
        for name, payload in payloads:
            name_bytes = name.encode("utf-8")
            framed.extend(len(name_bytes).to_bytes(8, "big"))
            framed.extend(name_bytes)
            framed.extend(len(payload).to_bytes(8, "big"))
            framed.extend(payload)
        independent_identity = hashlib.sha256(framed).hexdigest()
        self.assertEqual(independent_identity, module.LANGUAGE_CORE_IDENTITY)
        self.assertEqual(
            independent_identity,
            module.compute_language_core_identity(repository_root),
        )
        self.assertRegex(module.LANGUAGE_CORE_IDENTITY, r"^[0-9a-f]{64}$")


class CMEEStage1AdditionalCorrectionStep3EarlyHarnessTest(unittest.TestCase):
    _RUNTIME_HEAD = "a" * 40
    _DESIGN_HEAD = "b" * 40
    # Public, non-identifying synthetic stand-ins. These are contract inputs,
    # not withheld fixtures and not expected-output examples.
    _PUBLIC_NONSECRET_STANDIN_EXACT4 = PUBLIC_NONSECRET_EARLY_STANDIN_EXACT4

    @staticmethod
    def _withheld_payload() -> dict[str, object]:
        return {
            "schema_version": (
                candidate_run_module.EARLY_WITHHELD_INPUT_SCHEMA_VERSION
            ),
            "selection_frozen_before_first_after": True,
            "synthetic_non_identifying": True,
            "cases": [
                {
                    "structural_family": family,
                    "memo": memo,
                    "category": category,
                    "emotion": emotion,
                    "strength": strength,
                }
                for family, memo, category, emotion, strength
                in (
                    CMEEStage1AdditionalCorrectionStep3EarlyHarnessTest
                    ._PUBLIC_NONSECRET_STANDIN_EXACT4
                )
            ],
        }

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        (
            cls.body_free_packet,
            cls.known_visible_packet,
            cls.private_packet,
        ) = candidate_run_module.run_early_actual(
            withheld_private_payload=cls._withheld_payload(),
            runtime_repo_head=cls._RUNTIME_HEAD,
            design_repo_head=cls._DESIGN_HEAD,
        )

    def _pro_human_result(
        self,
        result: str = "CLEAR",
    ) -> dict[str, object]:
        defect_class = None
        cause_component = None
        if result == "COMMON_DEFECT":
            defect_class = "SURFACE_SEAM"
            cause_component = "GROUNDED_JAPANESE_COMPOSER"
        return {
            "schema_version": (
                candidate_run_module.EARLY_HUMAN_READ_RESULT_SCHEMA_VERSION
            ),
            "packet_id": candidate_run_module.WITHHELD_EARLY_PACKET_ID,
            "bounded_unit_id": candidate_run_module.EARLY_BOUNDED_UNIT_ID,
            "runtime_repo_head": self._RUNTIME_HEAD,
            "design_repo_head": self._DESIGN_HEAD,
            "language_core_identity": (
                candidate_run_module.STEP2_FROZEN_LANGUAGE_CORE_IDENTITY
            ),
            "withheld_set_digest": self.body_free_packet[
                "withheld_exact4_body_free"
            ]["withheld_set_digest"],
            "reviewed_known_count": 4,
            "reviewed_withheld_count": 4,
            "body_payload_present": False,
            "early_human_read_result": result,
            "defect_class": defect_class,
            "cause_component": cause_component,
            "ceiling_reason": None,
        }

    def _ultra_known_result(
        self,
        result: str = "CLEAR",
    ) -> dict[str, object]:
        return {
            "schema_version": (
                candidate_run_module
                .EARLY_ULTRA_KNOWN_TECHNICAL_RESULT_SCHEMA_VERSION
            ),
            "packet_id": candidate_run_module.WITHHELD_EARLY_PACKET_ID,
            "bounded_unit_id": candidate_run_module.EARLY_BOUNDED_UNIT_ID,
            "runtime_repo_head": self._RUNTIME_HEAD,
            "design_repo_head": self._DESIGN_HEAD,
            "language_core_identity": (
                candidate_run_module.STEP2_FROZEN_LANGUAGE_CORE_IDENTITY
            ),
            "known_visible_packet_sha256": (
                candidate_run_module._canonical_sha256(
                    self.known_visible_packet
                )
            ),
            "body_free_machine_packet_sha256": (
                candidate_run_module._canonical_sha256(
                    self.body_free_packet
                )
            ),
            "reviewed_known_count": 4,
            "body_payload_present": False,
            "ultra_known_technical_invariant": result,
        }

    def test_early_exact8_is_body_isolated_identity_bound_and_machine_clear(
        self,
    ) -> None:
        body_free = self.body_free_packet
        known = body_free["known_exact4_body_free"]
        withheld = body_free["withheld_exact4_body_free"]
        self.assertEqual(
            body_free["schema_version"],
            candidate_run_module.EARLY_BODY_FREE_PACKET_SCHEMA_VERSION,
        )
        self.assertEqual(
            body_free["language_core_identity"],
            candidate_run_module.STEP2_FROZEN_LANGUAGE_CORE_IDENTITY,
        )
        self.assertEqual(
            stage1_composition_module.compute_language_core_identity(),
            candidate_run_module.STEP2_FROZEN_LANGUAGE_CORE_IDENTITY,
        )
        for result in (known, withheld):
            self.assertEqual(result["machine_invariant_result"], "CLEAR")
            self.assertEqual(result["machine_invariant_clear_count"], 4)
            self.assertEqual(result["actual_japanese_reached_count"], 4)
            self.assertGreaterEqual(result["material_alternate_case_count"], 1)
        self.assertEqual(withheld["normal_form_phase_exact6_count"], 4)
        self.assertEqual(withheld["normal_form_defect_free_count"], 4)
        self.assertEqual(withheld["normalization_idempotent_count"], 4)
        self.assertEqual(withheld["required_duty_coverage_exact_count"], 4)
        self.assertFalse(body_free["body_payload_present"])
        self.assertFalse(body_free["private_text_published"])
        self.assertEqual(body_free["early_human_read_result"], "NOT_RUN")
        self.assertEqual(body_free["early_actual_status"], "NOT_RUN")

        serialized = json.dumps(body_free, ensure_ascii=False, sort_keys=True)
        forbidden_keys: list[str] = []

        def collect_keys(value: object) -> None:
            if type(value) is dict:
                for key, child in value.items():
                    forbidden_keys.append(str(key))
                    collect_keys(child)
            elif type(value) in {list, tuple}:
                for child in value:
                    collect_keys(child)

        collect_keys(body_free)
        self.assertTrue(
            {
                "memo",
                "synthetic_input",
                "synthetic_input_private",
                "actual_japanese",
                "candidate_private",
                "private_slot_id",
                "private_packet_binding",
            }.isdisjoint(forbidden_keys)
        )
        self.assertEqual(
            tuple(key for key in forbidden_keys if key.endswith("_digest")),
            ("withheld_set_digest",),
        )
        self.assertTrue(all("locator" not in key.lower() for key in forbidden_keys))

        private_values = [
            str(row[key])
            for row in self._withheld_payload()["cases"]
            for key in ("memo", "category", "emotion", "strength")
        ]
        private_values.extend(
            row["candidate_private"]
            for row in self.private_packet["withheld_cases"]
            if row["candidate_private"]
        )
        known_values = [
            row["actual_japanese"]
            for row in self.known_visible_packet["cases"]
            if row["actual_japanese"]
        ]
        self.assertTrue(
            all(value not in serialized for value in (*private_values, *known_values))
        )
        self.assertEqual(len(self.known_visible_packet["cases"]), 4)
        self.assertTrue(all(known_values))
        self.assertEqual(len(self.private_packet["withheld_cases"]), 4)

    def test_early_exact8_calls_only_the_final_step2_production_chain(self) -> None:
        original_phase_a = stage1_response_module.build_subjective_planning_inputs
        original_compose = stage1_composition_module.compose_stage1_from_projection
        with (
            patch.object(
                candidate_run_module.MeaningExperienceEngine,
                "generate",
                side_effect=AssertionError("active engine called by early harness"),
            ) as active_engine,
            patch.object(
                stage1_response_module,
                "compile_stage1_response",
                side_effect=AssertionError("active v1 compiler called by early harness"),
            ) as active_compiler,
            patch.object(
                stage1_response_module,
                "build_stage1_semantic_projection",
                side_effect=AssertionError("legacy projection called by early harness"),
            ) as legacy_projection,
            patch.object(
                stage1_response_module,
                "build_stage1_realization_candidate_set",
                side_effect=AssertionError("legacy realization called by early harness"),
            ) as legacy_realization,
            patch.object(
                stage1_response_module,
                "build_subjective_planning_inputs",
                wraps=original_phase_a,
            ) as phase_a_builder,
            patch.object(
                stage1_composition_module,
                "compose_stage1_from_projection",
                wraps=original_compose,
            ) as final_composer,
        ):
            body_free, _known_visible, _private = (
                candidate_run_module.run_early_actual(
                    withheld_private_payload=self._withheld_payload(),
                    runtime_repo_head=self._RUNTIME_HEAD,
                    design_repo_head=self._DESIGN_HEAD,
                )
            )
        active_engine.assert_not_called()
        active_compiler.assert_not_called()
        legacy_projection.assert_not_called()
        legacy_realization.assert_not_called()
        self.assertEqual(phase_a_builder.call_count, 8)
        self.assertEqual(final_composer.call_count, 8)
        self.assertEqual(
            body_free["known_exact4_body_free"]["machine_invariant_result"],
            "CLEAR",
        )
        self.assertEqual(
            body_free["withheld_exact4_body_free"]["machine_invariant_result"],
            "CLEAR",
        )

    def test_early_exact8_renormalizes_every_ranked_candidate(self) -> None:
        original_normalize = (
            stage1_composition_module.normalize_to_normal_form
        )
        with patch.object(
            stage1_composition_module,
            "normalize_to_normal_form",
            wraps=original_normalize,
        ) as normalizer:
            _body_free, known_visible, private_packet = (
                candidate_run_module.run_early_actual(
                    withheld_private_payload=self._withheld_payload(),
                    runtime_repo_head=self._RUNTIME_HEAD,
                    design_repo_head=self._DESIGN_HEAD,
                )
            )

        expected_rechecks = sum(
            row["machine_invariant"]["ranked_candidate_count"]
            for row in known_visible["cases"]
        ) + sum(
            row["machine_invariant_body_free"]["ranked_candidate_count"]
            for row in private_packet["withheld_cases"]
        )
        normalized_rechecks = tuple(
            call
            for call in normalizer.call_args_list
            if type(call.args[0]).__name__ == "NormalizedDraftArtifact"
        )
        self.assertEqual(len(normalized_rechecks), expected_rechecks)
        self.assertGreaterEqual(expected_rechecks, 8)

    def test_withheld_exact4_private_schema_is_closed_and_identity_free(self) -> None:
        valid = self._withheld_payload()

        def copied() -> dict[str, object]:
            return json.loads(json.dumps(valid, ensure_ascii=False))

        invalid_rows: list[dict[str, object]] = []
        extra_root = copied()
        extra_root["profile"] = "forbidden"
        invalid_rows.append(extra_root)
        missing_attestation = copied()
        del missing_attestation["synthetic_non_identifying"]
        invalid_rows.append(missing_attestation)
        reordered = copied()
        reordered["cases"] = list(reversed(reordered["cases"]))
        invalid_rows.append(reordered)
        identifying = copied()
        identifying["cases"][0]["user_id"] = "forbidden"
        invalid_rows.append(identifying)
        expected_text = copied()
        expected_text["cases"][0]["expected_text"] = "forbidden"
        invalid_rows.append(expected_text)
        duplicate_known = copied()
        duplicate_known["cases"][0]["memo"] = (
            candidate_run_module.EARLY_KNOWN_EXACT4[0][1]
        )
        invalid_rows.append(duplicate_known)
        whitespace_normalized_known = copied()
        whitespace_normalized_known["cases"][0]["memo"] = (
            " \t"
            + candidate_run_module.EARLY_KNOWN_EXACT4[0][1]
            + "\n "
        )
        invalid_rows.append(whitespace_normalized_known)
        invalid_strength = copied()
        invalid_strength["cases"][0]["strength"] = "extreme"
        invalid_rows.append(invalid_strength)
        nonlist = copied()
        nonlist["cases"] = tuple(nonlist["cases"])
        invalid_rows.append(nonlist)
        for invalid in invalid_rows:
            with self.subTest(keys=tuple(invalid)), self.assertRaisesRegex(
                ValueError,
                "withheld early private input invalid",
            ):
                candidate_run_module._validate_withheld_early_payload(invalid)

        canonical_whitespace = lambda value: " ".join(value.split())
        canonical_known = {
            canonical_whitespace(row[1])
            for row in candidate_run_module.EARLY_KNOWN_EXACT4
        }
        canonical_standins = {
            canonical_whitespace(row["memo"])
            for row in valid["cases"]
        }
        self.assertEqual(len(canonical_standins), 4)
        self.assertTrue(canonical_known.isdisjoint(canonical_standins))

        with self.assertRaisesRegex(
            ValueError,
            "early private packet repo head binding invalid",
        ):
            candidate_run_module.run_early_actual(
                withheld_private_payload=valid,
                runtime_repo_head="not-a-head",
                design_repo_head=self._DESIGN_HEAD,
            )

    def test_pro_body_free_human_result_is_exact_and_machine_bound(self) -> None:
        withheld = self.body_free_packet["withheld_exact4_body_free"]
        base = {
            "schema_version": (
                candidate_run_module.EARLY_HUMAN_READ_RESULT_SCHEMA_VERSION
            ),
            "packet_id": candidate_run_module.WITHHELD_EARLY_PACKET_ID,
            "bounded_unit_id": candidate_run_module.EARLY_BOUNDED_UNIT_ID,
            "runtime_repo_head": self._RUNTIME_HEAD,
            "design_repo_head": self._DESIGN_HEAD,
            "language_core_identity": (
                candidate_run_module.STEP2_FROZEN_LANGUAGE_CORE_IDENTITY
            ),
            "withheld_set_digest": withheld["withheld_set_digest"],
            "reviewed_known_count": 4,
            "reviewed_withheld_count": 4,
            "body_payload_present": False,
            "early_human_read_result": "CLEAR",
            "defect_class": None,
            "cause_component": None,
            "ceiling_reason": None,
        }
        validated = candidate_run_module.validate_early_human_read_result(
            base,
            body_free_machine_packet=self.body_free_packet,
        )
        self.assertEqual(validated, base)

        for defect_class in candidate_run_module.EARLY_COMMON_DEFECT_CLASSES:
            common = {
                **base,
                "early_human_read_result": "COMMON_DEFECT",
                "defect_class": defect_class,
                "cause_component": (
                    candidate_run_module.EARLY_COMMON_DEFECT_CAUSE_COMPONENTS[0]
                ),
            }
            self.assertEqual(
                candidate_run_module.validate_early_human_read_result(
                    common,
                    body_free_machine_packet=self.body_free_packet,
                ),
                common,
            )
        for reason in candidate_run_module.EARLY_ROUTE_LEVEL_CEILING_REASONS:
            ceiling = {
                **base,
                "early_human_read_result": "ROUTE_LEVEL_CEILING",
                "ceiling_reason": reason,
            }
            self.assertEqual(
                candidate_run_module.validate_early_human_read_result(
                    ceiling,
                    body_free_machine_packet=self.body_free_packet,
                ),
                ceiling,
            )

        invalid_rows = (
            {**base, "runtime_repo_head": "c" * 40},
            {**base, "withheld_set_digest": "0" * 64},
            {**base, "reviewed_withheld_count": 3},
            {**base, "body_payload_present": True},
            {**base, "review_note": "free text is forbidden"},
            {**base, "early_human_read_result": "PASS"},
            {**base, "defect_class": "SURFACE_SEAM"},
            {
                **base,
                "early_human_read_result": "COMMON_DEFECT",
                "defect_class": "SURFACE_SEAM",
                "cause_component": "CASE_PATCH",
            },
            {
                **base,
                "early_human_read_result": "ROUTE_LEVEL_CEILING",
                "ceiling_reason": "NEW_SENTENCE",
            },
        )
        for invalid in invalid_rows:
            with self.subTest(result=invalid.get("early_human_read_result")):
                with self.assertRaisesRegex(
                    ValueError,
                    "early human read result invalid",
                ):
                    candidate_run_module.validate_early_human_read_result(
                        invalid,
                        body_free_machine_packet=self.body_free_packet,
                    )

    def test_ultra_known_technical_result_is_exact_and_machine_bound(
        self,
    ) -> None:
        for result in candidate_run_module.EARLY_ULTRA_KNOWN_TECHNICAL_RESULTS:
            payload = self._ultra_known_result(result)
            self.assertEqual(
                candidate_run_module.validate_ultra_known_technical_result(
                    payload,
                    body_free_machine_packet=self.body_free_packet,
                ),
                payload,
            )

        valid = self._ultra_known_result()
        invalid_rows = (
            {**valid, "runtime_repo_head": "c" * 40},
            {**valid, "known_visible_packet_sha256": "not-a-digest"},
            {**valid, "known_visible_packet_sha256": "0" * 64},
            {**valid, "body_free_machine_packet_sha256": "0" * 64},
            {**valid, "reviewed_known_count": 3},
            {**valid, "body_payload_present": True},
            {**valid, "ultra_known_technical_invariant": "PASS"},
            {**valid, "technical_note": "free text is forbidden"},
        )
        for index, invalid in enumerate(invalid_rows):
            with self.subTest(index=index), self.assertRaisesRegex(
                ValueError,
                "early Ultra known technical result invalid",
            ):
                candidate_run_module.validate_ultra_known_technical_result(
                    invalid,
                    body_free_machine_packet=self.body_free_packet,
                )

    def test_exact3_body_free_finalizer_observes_only_all_clear(self) -> None:
        machine_before = json.loads(
            json.dumps(self.body_free_packet, ensure_ascii=False)
        )
        pro_clear = self._pro_human_result()
        ultra_clear = self._ultra_known_result()
        receipt = candidate_run_module.finalize_early_actual_body_free(
            body_free_machine_packet=self.body_free_packet,
            pro_human_read_result=pro_clear,
            ultra_known_technical_result=ultra_clear,
        )

        self.assertEqual(
            receipt["schema_version"],
            candidate_run_module.EARLY_ACTUAL_FINAL_BODY_FREE_SCHEMA_VERSION,
        )
        self.assertEqual(
            receipt["early_actual_status"],
            "LANGUAGE_VIABILITY_OBSERVED",
        )
        self.assertTrue(receipt["all_three_clear"])
        self.assertEqual(
            receipt["pro_body_free_early_human_read_result"], "CLEAR"
        )
        self.assertEqual(
            receipt["ultra_known_technical_invariant"], "CLEAR"
        )
        self.assertEqual(
            receipt["withheld_body_free_machine_invariant"], "CLEAR"
        )
        self.assertEqual(
            receipt["known_visible_packet_sha256"],
            ultra_clear["known_visible_packet_sha256"],
        )
        self.assertEqual(
            receipt["body_free_machine_packet_sha256"],
            candidate_run_module._canonical_sha256(self.body_free_packet),
        )
        self.assertEqual(
            receipt["pro_human_read_result_sha256"],
            candidate_run_module._canonical_sha256(pro_clear),
        )
        self.assertEqual(
            receipt["ultra_known_technical_result_sha256"],
            candidate_run_module._canonical_sha256(ultra_clear),
        )
        self.assertFalse(receipt["body_payload_present"])
        self.assertFalse(receipt["private_text_published"])
        self.assertEqual(receipt["formal_exact8"], "NOT_RUN")
        self.assertFalse(receipt["product_read_evaluated"])
        self.assertEqual(receipt["product_credit"], 0)
        self.assertFalse(receipt["candidate_ready"])
        self.assertEqual(receipt["production_effect"], 0)
        self.assertFalse(receipt["automatic_progression"])
        self.assertEqual(self.body_free_packet, machine_before)

        for pro, ultra in (
            (self._pro_human_result("COMMON_DEFECT"), ultra_clear),
            (pro_clear, self._ultra_known_result("NOT_CLEAR")),
        ):
            with self.subTest(
                pro=pro["early_human_read_result"],
                ultra=ultra["ultra_known_technical_invariant"],
            ):
                nonclear = (
                    candidate_run_module.finalize_early_actual_body_free(
                        body_free_machine_packet=self.body_free_packet,
                        pro_human_read_result=pro,
                        ultra_known_technical_result=ultra,
                    )
                )
                self.assertFalse(nonclear["all_three_clear"])
                self.assertEqual(nonclear["early_actual_status"], "NOT_RUN")

        tampered_machine = json.loads(
            json.dumps(self.body_free_packet, ensure_ascii=False)
        )
        tampered_machine["known_exact4_body_free"][
            "known_visible_packet_sha256"
        ] = "0" * 64
        with self.assertRaisesRegex(
            ValueError,
            "early Ultra known technical result invalid",
        ):
            candidate_run_module.finalize_early_actual_body_free(
                body_free_machine_packet=tampered_machine,
                pro_human_read_result=pro_clear,
                ultra_known_technical_result=ultra_clear,
            )

    def test_exact3_finalizer_cli_clear_nonclear_and_invalid_drift(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            machine_path = root / "machine.json"
            pro_path = root / "pro.json"
            ultra_path = root / "ultra.json"
            machine_path.write_text(
                json.dumps(self.body_free_packet, ensure_ascii=False),
                encoding="utf-8",
            )

            def invoke(
                pro: dict[str, object],
                ultra: dict[str, object],
            ) -> tuple[int, str]:
                pro_path.write_text(
                    json.dumps(pro, ensure_ascii=False), encoding="utf-8"
                )
                ultra_path.write_text(
                    json.dumps(ultra, ensure_ascii=False), encoding="utf-8"
                )
                stdout = io.StringIO()
                with (
                    patch.object(
                        candidate_run_module.sys,
                        "argv",
                        (
                            "cmee-v1a-candidate-run",
                            "--finalize-early-actual",
                            "--early-machine-body-free-input",
                            str(machine_path),
                            "--early-pro-body-free-input",
                            str(pro_path),
                            "--early-ultra-body-free-input",
                            str(ultra_path),
                        ),
                    ),
                    patch.object(candidate_run_module.sys, "stdout", stdout),
                ):
                    result = candidate_run_module.main()
                return result, stdout.getvalue()

            clear_code, clear_stdout = invoke(
                self._pro_human_result(), self._ultra_known_result()
            )
            self.assertEqual(clear_code, 0)
            self.assertEqual(
                json.loads(clear_stdout)["early_actual_status"],
                "LANGUAGE_VIABILITY_OBSERVED",
            )

            nonclear_code, nonclear_stdout = invoke(
                self._pro_human_result("COMMON_DEFECT"),
                self._ultra_known_result(),
            )
            self.assertEqual(nonclear_code, 1)
            self.assertEqual(
                json.loads(nonclear_stdout)["early_actual_status"],
                "NOT_RUN",
            )

            invalid_ultra = {
                **self._ultra_known_result(),
                "body_free_machine_packet_sha256": "0" * 64,
            }
            pro_path.write_text(
                json.dumps(self._pro_human_result(), ensure_ascii=False),
                encoding="utf-8",
            )
            ultra_path.write_text(
                json.dumps(invalid_ultra, ensure_ascii=False),
                encoding="utf-8",
            )
            stdout = io.StringIO()
            stderr = io.StringIO()
            with (
                patch.object(
                    candidate_run_module.sys,
                    "argv",
                    (
                        "cmee-v1a-candidate-run",
                        "--finalize-early-actual",
                        "--early-machine-body-free-input",
                        str(machine_path),
                        "--early-pro-body-free-input",
                        str(pro_path),
                        "--early-ultra-body-free-input",
                        str(ultra_path),
                    ),
                ),
                patch.object(candidate_run_module.sys, "stdout", stdout),
                patch.object(candidate_run_module.sys, "stderr", stderr),
            ):
                with self.assertRaises(SystemExit) as raised:
                    candidate_run_module.main()
            self.assertEqual(raised.exception.code, 2)
            self.assertEqual(stdout.getvalue(), "")
            self.assertIn(
                "early finalization binding invalid", stderr.getvalue()
            )

    def test_human_transition_rejects_fabricated_machine_packets(self) -> None:
        withheld = self.body_free_packet["withheld_exact4_body_free"]
        human_result = {
            "schema_version": (
                candidate_run_module.EARLY_HUMAN_READ_RESULT_SCHEMA_VERSION
            ),
            "packet_id": candidate_run_module.WITHHELD_EARLY_PACKET_ID,
            "bounded_unit_id": candidate_run_module.EARLY_BOUNDED_UNIT_ID,
            "runtime_repo_head": self._RUNTIME_HEAD,
            "design_repo_head": self._DESIGN_HEAD,
            "language_core_identity": (
                candidate_run_module.STEP2_FROZEN_LANGUAGE_CORE_IDENTITY
            ),
            "withheld_set_digest": withheld["withheld_set_digest"],
            "reviewed_known_count": 4,
            "reviewed_withheld_count": 4,
            "body_payload_present": False,
            "early_human_read_result": "CLEAR",
            "defect_class": None,
            "cause_component": None,
            "ceiling_reason": None,
        }

        def mutated(path: tuple[str, ...], value: object) -> dict[str, object]:
            packet = json.loads(
                json.dumps(self.body_free_packet, ensure_ascii=False)
            )
            cursor = packet
            for key in path[:-1]:
                cursor = cursor[key]
            cursor[path[-1]] = value
            return packet

        invalid_packets = [
            mutated(("unexpected",), False),
            mutated(("known_exact4_body_free", "unexpected"), False),
            mutated(("withheld_exact4_body_free", "unexpected"), False),
            mutated(("schema_version",), "fabricated.schema"),
            mutated(("packet_id",), "FABRICATED_PACKET"),
            mutated(("bounded_unit_id",), "fabricated.unit"),
            mutated(("runtime_repo_head",), "not-a-head"),
            mutated(("design_repo_head",), "A" * 40),
            mutated(("language_core_identity",), "0" * 64),
            mutated(("early_human_read_result",), "CLEAR"),
            mutated(("early_actual_status",), "LANGUAGE_VIABILITY_OBSERVED"),
            mutated(("body_payload_present",), True),
            mutated(("private_text_published",), True),
            mutated(("known_exact4_body_free", "case_count"), 3),
            mutated(
                (
                    "known_exact4_body_free",
                    "structural_family_counts",
                    "tension",
                ),
                True,
            ),
            mutated(
                ("known_exact4_body_free", "material_alternate_case_count"),
                0,
            ),
            mutated(("known_exact4_body_free", "body_payload_present"), True),
            mutated(
                (
                    "known_exact4_body_free",
                    "known_visible_packet_sha256",
                ),
                "not-a-digest",
            ),
            mutated(
                ("withheld_exact4_body_free", "schema_version"),
                "fabricated.schema",
            ),
            mutated(
                ("withheld_exact4_body_free", "withheld_set_digest"),
                "not-a-digest",
            ),
            mutated(
                (
                    "withheld_exact4_body_free",
                    "structural_family_counts",
                    "unfinished",
                ),
                2,
            ),
            mutated(
                (
                    "withheld_exact4_body_free",
                    "material_alternate_case_count",
                ),
                0,
            ),
            mutated(
                ("withheld_exact4_body_free", "machine_failure_classes"),
                ["FabricatedFailure"],
            ),
            mutated(
                ("withheld_exact4_body_free", "body_payload_present"),
                True,
            ),
            mutated(
                ("withheld_exact4_body_free", "private_text_published"),
                True,
            ),
            mutated(
                ("withheld_exact4_body_free", "ultra_withheld_body_access"),
                1,
            ),
            mutated(
                ("withheld_exact4_body_free", "candidate_ready"),
                True,
            ),
        ]
        for field in (
            "actual_japanese_reached_count",
            "machine_invariant_clear_count",
        ):
            invalid_packets.append(
                mutated(("known_exact4_body_free", field), 3)
            )
        for field in (
            "withheld_set_count",
            "actual_japanese_reached_count",
            "machine_invariant_clear_count",
            "normal_form_phase_exact6_count",
            "normal_form_defect_free_count",
            "normalization_idempotent_count",
            "required_duty_coverage_exact_count",
        ):
            invalid_packets.append(
                mutated(("withheld_exact4_body_free", field), 3)
            )

        for index, invalid_packet in enumerate(invalid_packets):
            with self.subTest(index=index), self.assertRaisesRegex(
                ValueError,
                "early human read machine binding invalid",
            ):
                candidate_run_module.validate_early_human_read_result(
                    human_result,
                    body_free_machine_packet=invalid_packet,
                )

    def test_early_cli_stdout_is_body_free_and_known_body_is_explicit_output(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            private_root = (Path(temporary_directory) / "private-root").resolve()
            private_root.mkdir(mode=0o700)
            private_root.chmod(0o700)
            input_path = private_root / "input.json"
            input_path.write_text(
                json.dumps(self._withheld_payload(), ensure_ascii=False),
                encoding="utf-8",
            )
            input_path.chmod(0o600)
            known_output = private_root / "known.json"
            private_output = private_root / "private.json"
            stdout = io.StringIO()
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
                        "--early-actual",
                        "--withheld-input",
                        str(input_path),
                        "--known-visible-output",
                        str(known_output),
                        "--body-full-output",
                        str(private_output),
                        "--runtime-repo-head",
                        self._RUNTIME_HEAD,
                        "--design-repo-head",
                        self._DESIGN_HEAD,
                    ),
                ),
                patch.object(candidate_run_module.sys, "stdout", stdout),
            ):
                self.assertEqual(candidate_run_module.main(), 0)

            body_free = json.loads(stdout.getvalue())
            known = json.loads(known_output.read_text(encoding="utf-8"))
            private = json.loads(private_output.read_text(encoding="utf-8"))
            self.assertEqual(
                body_free["known_exact4_body_free"]["machine_invariant_result"],
                "CLEAR",
            )
            serialized = json.dumps(body_free, ensure_ascii=False, sort_keys=True)
            for case in known["cases"]:
                self.assertNotIn(case["synthetic_input"]["memo"], serialized)
                self.assertNotIn(case["actual_japanese"], serialized)
            for case in private["withheld_cases"]:
                self.assertNotIn(case["synthetic_input_private"]["memo"], serialized)
                self.assertNotIn(case["candidate_private"], serialized)
            self.assertEqual(known_output.stat().st_mode & 0o777, 0o600)
            self.assertEqual(private_output.stat().st_mode & 0o777, 0o600)
            self.assertNotIn(str(known_output), serialized)
            self.assertNotIn(str(private_output), serialized)

    def test_early_private_input_rejects_final_symlink_and_non_owner_mode(
        self,
    ) -> None:
        body_sentinel = "PRIVATE_BODY_SENTINEL_DO_NOT_PRINT"
        with tempfile.TemporaryDirectory() as temporary_directory:
            private_root = (Path(temporary_directory) / "private-root").resolve()
            private_root.mkdir(mode=0o700)
            private_root.chmod(0o700)
            valid_target = private_root / "valid-target.json"
            valid_target.write_text(
                json.dumps({"memo": body_sentinel}),
                encoding="utf-8",
            )
            valid_target.chmod(0o600)
            final_symlink = private_root / "final-symlink.json"
            final_symlink.symlink_to(valid_target)
            non_owner_mode = private_root / "non-owner-mode.json"
            non_owner_mode.write_text(
                json.dumps({"memo": body_sentinel}),
                encoding="utf-8",
            )
            non_owner_mode.chmod(0o640)

            for scenario, input_path in (
                ("final_symlink", final_symlink),
                ("mode_not_0600", non_owner_mode),
            ):
                with self.subTest(scenario=scenario):
                    stdout = io.StringIO()
                    stderr = io.StringIO()
                    known_output = private_root / f"{scenario}-known.json"
                    private_output = private_root / f"{scenario}-private.json"
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
                                "--early-actual",
                                "--withheld-input",
                                str(input_path),
                                "--known-visible-output",
                                str(known_output),
                                "--body-full-output",
                                str(private_output),
                                "--runtime-repo-head",
                                self._RUNTIME_HEAD,
                                "--design-repo-head",
                                self._DESIGN_HEAD,
                            ),
                        ),
                        patch.object(candidate_run_module.sys, "stdout", stdout),
                        patch.object(candidate_run_module.sys, "stderr", stderr),
                        patch.object(
                            candidate_run_module,
                            "run_early_actual",
                            side_effect=AssertionError(
                                "early runner must not read an invalid input"
                            ),
                        ) as runner,
                    ):
                        with self.assertRaises(SystemExit) as raised:
                            candidate_run_module.main()

                    self.assertEqual(raised.exception.code, 2)
                    runner.assert_not_called()
                    self.assertEqual(stdout.getvalue(), "")
                    error_text = stderr.getvalue()
                    self.assertNotIn(body_sentinel, error_text)
                    self.assertNotIn(str(input_path), error_text)
                    self.assertNotIn(str(known_output), error_text)
                    self.assertNotIn(str(private_output), error_text)
                    self.assertFalse(known_output.exists())
                    self.assertFalse(private_output.exists())

    def test_private_input_dirfd_walk_rejects_symlink_and_bad_root_mode(
        self,
    ) -> None:
        parser = candidate_run_module.argparse.ArgumentParser(add_help=False)
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory).resolve()
            private_root = base / "private-root"
            private_root.mkdir(mode=0o700)
            private_root.chmod(0o700)
            outside = base / "outside"
            outside.mkdir(mode=0o700)
            outside.chmod(0o700)
            outside_input = outside / "input.json"
            outside_input.write_text(
                json.dumps(self._withheld_payload(), ensure_ascii=False),
                encoding="utf-8",
            )
            outside_input.chmod(0o600)
            (private_root / "intermediate").symlink_to(
                outside,
                target_is_directory=True,
            )
            lexical_target = private_root / "intermediate" / "input.json"
            with patch.object(
                candidate_run_module,
                "PRIVATE_OUTPUT_ROOT",
                private_root,
            ):
                target = candidate_run_module._private_input_target(
                    parser,
                    lexical_target,
                )
                with self.assertRaisesRegex(
                    ValueError,
                    "withheld early private input invalid",
                ):
                    candidate_run_module._read_private_json(target)

            private_root.chmod(0o750)
            root_input = private_root / "root-mode-input.json"
            root_input.write_text(
                json.dumps(self._withheld_payload(), ensure_ascii=False),
                encoding="utf-8",
            )
            root_input.chmod(0o600)
            with patch.object(
                candidate_run_module,
                "PRIVATE_OUTPUT_ROOT",
                private_root,
            ):
                with self.assertRaisesRegex(
                    ValueError,
                    "withheld early private input invalid",
                ):
                    candidate_run_module._read_private_json(root_input)

    def test_private_input_single_fd_rejects_foreign_uid_and_hardlink(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            private_root = (Path(temporary_directory) / "private-root").resolve()
            private_root.mkdir(mode=0o700)
            private_root.chmod(0o700)
            input_path = private_root / "input.json"
            input_path.write_text(
                json.dumps(self._withheld_payload(), ensure_ascii=False),
                encoding="utf-8",
            )
            input_path.chmod(0o600)
            original_fstat = candidate_run_module.os.fstat

            def foreign_file_owner(file_descriptor: int) -> object:
                file_stat = original_fstat(file_descriptor)
                if candidate_run_module.stat.S_ISREG(file_stat.st_mode):
                    return SimpleNamespace(
                        st_mode=file_stat.st_mode,
                        st_uid=file_stat.st_uid + 1,
                        st_nlink=file_stat.st_nlink,
                        st_size=file_stat.st_size,
                    )
                return file_stat

            with (
                patch.object(
                    candidate_run_module,
                    "PRIVATE_OUTPUT_ROOT",
                    private_root,
                ),
                patch.object(
                    candidate_run_module.os,
                    "fstat",
                    side_effect=foreign_file_owner,
                ),
            ):
                with self.assertRaisesRegex(
                    ValueError,
                    "withheld early private input invalid",
                ):
                    candidate_run_module._read_private_json(input_path)

            hardlink_path = private_root / "hardlink.json"
            os.link(input_path, hardlink_path)
            with patch.object(
                candidate_run_module,
                "PRIVATE_OUTPUT_ROOT",
                private_root,
            ):
                with self.assertRaisesRegex(
                    ValueError,
                    "withheld early private input invalid",
                ):
                    candidate_run_module._read_private_json(input_path)

    def test_private_input_single_fd_is_stable_across_path_inode_swap(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            private_root = (Path(temporary_directory) / "private-root").resolve()
            private_root.mkdir(mode=0o700)
            private_root.chmod(0o700)
            original_payload = self._withheld_payload()
            replacement_payload = {"replacement": "PUBLIC_SWAP_SENTINEL"}
            input_path = private_root / "input.json"
            replacement_path = private_root / "replacement.json"
            input_path.write_text(
                json.dumps(original_payload, ensure_ascii=False),
                encoding="utf-8",
            )
            replacement_path.write_text(
                json.dumps(replacement_payload, ensure_ascii=False),
                encoding="utf-8",
            )
            input_path.chmod(0o600)
            replacement_path.chmod(0o600)
            original_fstat = candidate_run_module.os.fstat
            swap_complete = False

            def swap_path_after_final_open(file_descriptor: int) -> object:
                nonlocal swap_complete
                file_stat = original_fstat(file_descriptor)
                if (
                    candidate_run_module.stat.S_ISREG(file_stat.st_mode)
                    and not swap_complete
                ):
                    os.replace(replacement_path, input_path)
                    swap_complete = True
                return file_stat

            with (
                patch.object(
                    candidate_run_module,
                    "PRIVATE_OUTPUT_ROOT",
                    private_root,
                ),
                patch.object(
                    candidate_run_module.os,
                    "fstat",
                    side_effect=swap_path_after_final_open,
                ),
            ):
                loaded = candidate_run_module._read_private_json(input_path)

            self.assertTrue(swap_complete)
            self.assertEqual(loaded, original_payload)
            self.assertEqual(
                json.loads(input_path.read_text(encoding="utf-8")),
                replacement_payload,
            )

    def test_early_existing_outputs_are_rejected_before_body_execution(
        self,
    ) -> None:
        body_sentinel = "PRIVATE_BODY_SENTINEL_DO_NOT_PRINT"
        output_sentinel = "EXISTING_OUTPUT_MUST_REMAIN_UNCHANGED"
        with tempfile.TemporaryDirectory() as temporary_directory:
            private_root = (Path(temporary_directory) / "private-root").resolve()
            private_root.mkdir(mode=0o700)
            private_root.chmod(0o700)
            input_path = private_root / "input.json"
            input_path.write_text(
                json.dumps({"memo": body_sentinel}),
                encoding="utf-8",
            )
            input_path.chmod(0o600)

            for existing_kind in ("known", "private"):
                with self.subTest(existing_kind=existing_kind):
                    known_output = private_root / f"{existing_kind}-known.json"
                    private_output = private_root / f"{existing_kind}-private.json"
                    existing_output = (
                        known_output
                        if existing_kind == "known"
                        else private_output
                    )
                    existing_output.write_text(output_sentinel, encoding="utf-8")
                    existing_output.chmod(0o600)
                    stdout = io.StringIO()
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
                                "--early-actual",
                                "--withheld-input",
                                str(input_path),
                                "--known-visible-output",
                                str(known_output),
                                "--body-full-output",
                                str(private_output),
                                "--runtime-repo-head",
                                self._RUNTIME_HEAD,
                                "--design-repo-head",
                                self._DESIGN_HEAD,
                            ),
                        ),
                        patch.object(candidate_run_module.sys, "stdout", stdout),
                        patch.object(candidate_run_module.sys, "stderr", stderr),
                        patch.object(
                            candidate_run_module,
                            "run_early_actual",
                            side_effect=AssertionError(
                                "early runner must not execute for an existing output"
                            ),
                        ) as runner,
                    ):
                        with self.assertRaises(SystemExit) as raised:
                            candidate_run_module.main()

                    self.assertEqual(raised.exception.code, 2)
                    runner.assert_not_called()
                    self.assertEqual(stdout.getvalue(), "")
                    self.assertEqual(
                        existing_output.read_text(encoding="utf-8"),
                        output_sentinel,
                    )
                    other_output = (
                        private_output
                        if existing_kind == "known"
                        else known_output
                    )
                    self.assertFalse(other_output.exists())
                    error_text = stderr.getvalue()
                    self.assertNotIn(body_sentinel, error_text)
                    self.assertNotIn(output_sentinel, error_text)
                    self.assertNotIn(str(input_path), error_text)
                    self.assertNotIn(str(known_output), error_text)
                    self.assertNotIn(str(private_output), error_text)

    def test_early_output_writer_keeps_o_excl_for_both_packet_classes(
        self,
    ) -> None:
        output_sentinel = "EXISTING_OUTPUT_MUST_REMAIN_UNCHANGED"
        body_sentinel = "PRIVATE_BODY_SENTINEL_DO_NOT_PRINT"
        with tempfile.TemporaryDirectory() as temporary_directory:
            private_root = (Path(temporary_directory) / "private-root").resolve()
            private_root.mkdir(mode=0o700)
            private_root.chmod(0o700)
            parser = candidate_run_module.argparse.ArgumentParser(add_help=False)
            for packet_class in ("known", "private"):
                with self.subTest(packet_class=packet_class):
                    target = private_root / f"{packet_class}.json"
                    target.write_text(output_sentinel, encoding="utf-8")
                    target.chmod(0o600)
                    stdout = io.StringIO()
                    with (
                        patch.object(
                            candidate_run_module,
                            "PRIVATE_OUTPUT_ROOT",
                            private_root,
                        ),
                        patch.object(candidate_run_module.sys, "stdout", stdout),
                    ):
                        with self.assertRaises(FileExistsError):
                            candidate_run_module._write_private_json_exclusive(
                                parser,
                                target,
                                {"body": body_sentinel},
                            )
                    self.assertEqual(stdout.getvalue(), "")
                    self.assertEqual(
                        target.read_text(encoding="utf-8"),
                        output_sentinel,
                    )

    def test_default_runner_body_free_shape_and_hash_remain_frozen(self) -> None:
        body_free, _private_packet = candidate_run_module.run()
        canonical = json.dumps(
            body_free,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        self.assertEqual(
            hashlib.sha256(canonical).hexdigest(),
            "bc671ab7edfcc49616bc90647ae1637ebd29ac855e2bd61fd45df203321b6139",
        )
        self.assertEqual(
            sorted(body_free),
            [
                "artifact_count",
                "automatic_progression",
                "candidate_ready",
                "candidate_state",
                "case_count",
                "cases",
                "cycle001_credit",
                "exact8_acceptance_complete",
                "finite_mutation_set_body_free",
                "full_i1_credit",
                "generated_count",
                "implementation_state",
                "l3i_credit",
                "limited_count",
                "material_unknown_case_count",
                "observation_plus_bound_reception_trace_count",
                "p0_credit",
                "packet_id",
                "private_text_published",
                "product_read_eligible",
                "product_read_evaluated",
                "production_effect",
                "source_owner_contract_complete",
                "structural_trace_valid_count",
            ],
        )


if __name__ == "__main__":
    unittest.main()
