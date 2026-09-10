from __future__ import annotations

"""Source/version adapter to the existing sole Human Reception author."""

import emlis_ai_grounded_human_reception as hr
import emlis_ai_grounded_sentence_surface as surface_owner
from emlis_ai_grounded_observation_gate import evaluate_grounded_surface_body_inverse, evaluate_grounded_observation_gate

from .contracts import EngineStatus
from .emlis_answer_update import build_updated_grounded_plan
from .emlis_thread_contracts import THREAD_SCHEMA, EmlisThreadBodyArtifactV1, EmlisThreadBodyOutcomeV1
from .emlis_thread_projection import project_thread_meaning
from .emlis_thread_source import identity
from .emlis_stage1_response import _node_ref, _edge_ref, _evidence_ref


def _unique(values):
    return tuple(dict.fromkeys(values))


def _bind_expression(plan, resolver, projection, move, clause_form):
    reception = plan.response_plan.human_reception_plan
    decisions = hr.validate_selected_subjective_reception_input(projection.selected_reception, reception, plan, resolver)
    decision = decisions[move.move_id]
    index = {n.nucleus_id: n for n in plan.nuclei}
    targets = set(move.target_nucleus_ids)
    relations = tuple(row for row in plan.relations
        if row.relation_id in plan.coverage_requirements.required_relation_ids
        and targets.intersection((row.from_nucleus_id, row.to_nucleus_id)))
    context = _unique(n for row in relations for n in (row.from_nucleus_id, row.to_nucleus_id)
                      if n not in targets and n not in move.support_nucleus_ids)
    nucleus_ids = (*move.target_nucleus_ids, *move.support_nucleus_ids, *context)
    refs = tuple(_node_ref(projection.binding.nucleus_to_node[n]) for n in nucleus_ids)
    edge_refs = tuple(_edge_ref(projection.binding.relation_to_edge[row.relation_id]) for row in relations)
    ir = hr._project_source_grounded_reception_move_realization(reception, move, index, resolver,
        plan=plan, recovery_stage="full", clause_form=clause_form)
    arguments = []
    for arg in ir.arguments:
        ref = refs[arg.semantic_slot]
        relation_ref = edge_refs[arg.relation_slot] if arg.relation_slot is not None else None
        endpoint = hr._source_grounded_relation_endpoint_ref(relation_ref, ref, arg.semantic_role) if relation_ref else None
        direction = hr._source_grounded_direction_ref(relation_ref, ref, arg.semantic_role, arg.direction_side) if arg.direction_side else None
        arguments.append(hr.RealizableReceptionArgumentV1(
            ref, tuple(_evidence_ref(resolver.qualified_ref(s).evidence.evidence_id, THREAD_SCHEMA)
                       for s in index[nucleus_ids[arg.semantic_slot]].source_span_ids),
            arg.semantic_role, arg.lexical_form, "REQUIRED", "FORBIDDEN",
            ("shared-subject:current-user",) if arg.realization == "ZERO" else (), (),
            arg.case_marker, direction, endpoint, arg.realization))
    arguments = tuple(arguments)
    evidence = _unique(e for arg in arguments for e in arg.source_evidence_refs)
    expression = hr.SourceGroundedRealizableReceptionExpressionV1(
        schema_version=hr.SOURCE_GROUNDED_RECEPTION_EXPRESSION_SCHEMA_VERSION,
        expression_ref="", meaning_outcome_ref=decision.meaning_outcome_ref,
        reception_binding_ref=decision.reception_binding_ref, move_id=move.move_id,
        selected_subjective_decision_ref=decision.decision_ref, source_evidence_refs=evidence,
        actor_refs=tuple(refs[s] for s in ir.actor_slots), subject_refs=tuple(refs[s] for s in ir.subject_slots),
        experiencer_refs=tuple(refs[s] for s in ir.experiencer_slots),
        predicate_kind=ir.predicate_kind, lexical_head=ir.predicate_head, arguments=arguments,
        polarity=ir.polarity, modality=ir.modality, time_scope=ir.time_scope,
        aspect=ir.aspect, degree=ir.degree, quantity=ir.quantity, scope=ir.scope,
        qualifier_refs=tuple(q.source_qualifier_binding_ref for q in decision.qualifier_rows),
        relation_refs=edge_refs, relation_endpoint_refs=_unique(a.relation_endpoint_ref for a in arguments if a.relation_endpoint_ref),
        direction_refs=_unique(a.direction_ref for a in arguments if a.direction_ref),
        reference_mode=ir.reference_mode, antecedent_refs=tuple(refs[s] for s in ir.antecedent_slots),
        antecedent_condition=ir.antecedent_condition,
        particle_plan=tuple(f"particle:{a.semantic_role}:{a.case_marker or 'ZERO'}" for a in arguments),
        inflection_plan=(f"predicate:{ir.predicate_kind}", f"polarity:{ir.polarity}", f"modality:{ir.modality}",
            f"time:{ir.time_scope}", f"aspect:{ir.aspect}", f"degree:{ir.degree}", f"quantity:{ir.quantity}",
            f"scope:{ir.scope}", f"focus-kind:{'+'.join(ir.focus_kinds)}", "head-class:source-grounded-proposition",
            "politeness:polite", "reception-form:full", f"clause-form:{clause_form}"),
        nominalization_plan=ir.nominalization_plan,
        clause_link_plan=tuple(f"relation-kind:{row.relation_kind}" for row in ir.relations) or ("clause-link:none",),
        provenance_refs=_unique((decision.meaning_outcome_ref, decision.reception_binding_ref,
            decision.projected_claim_ref, *decision.selected_contribution_refs, *evidence, *edge_refs)))
    expression = hr.identify_source_grounded_reception_expression(expression)
    hr.validate_source_grounded_reception_expression(expression)
    return expression


def realize_emlis_thread_body(prepared) -> EmlisThreadBodyOutcomeV1:
    plan = build_updated_grounded_plan(prepared)
    projection = project_thread_meaning(prepared, plan)
    resolver = prepared.thread.resolver()
    selected = projection.selected_reception
    sentence_plan = surface_owner.build_grounded_sentence_plan(plan, resolver, recovery_stage="full")
    clauses = tuple(row.reception_clause_plans for row in sentence_plan.lines if row.binding.line_role == "human_follow")
    if len(clauses) != 1:
        raise ValueError("emlis_thread_human_follow_exact_one_required")
    clauses = clauses[0]
    forms = {move_id: "FINITE" if i == len(clause.move_ids)-1 else "CONTINUATIVE"
             for clause in clauses for i, move_id in enumerate(clause.move_ids)}
    reception = plan.response_plan.human_reception_plan
    expressions = tuple(_bind_expression(plan, resolver, projection, move, forms[move.move_id]) for move in reception.moves)
    human_surface = hr.realize_source_grounded_human_reception(reception, expressions,
        {n.nucleus_id: n for n in plan.nuclei}, resolver, plan=plan, recovery_stage="full",
        clause_plans=clauses, selected_subjective_input=selected)
    surface, _placements = surface_owner.realize_grounded_sentence_plan_with_human_reception(
        sentence_plan, plan, resolver, human_reception_surface=human_surface,
        selected_subjective_input=selected)
    issues = surface_owner.validate_grounded_surface_result(surface, sentence_plan, plan, resolver,
                                                             selected_subjective_input=selected)
    inverse = evaluate_grounded_surface_body_inverse(body=surface.text.encode(), plan=plan,
        sentence_plan=sentence_plan, resolver=resolver, selected_subjective_input=selected)
    gate = evaluate_grounded_observation_gate(plan=plan, sentence_plan=sentence_plan,
        surface_result=surface, resolver=resolver, require_body_inverse=True, selected_subjective_input=selected)
    if issues or not inverse.passed or gate.public_observation_status != "passed":
        raise ValueError("emlis_thread_body_independent_validation_failed")
    observation, reception_text, split_issues = surface_owner.split_two_stage_surface(surface.text)
    if split_issues or not observation or not reception_text:
        raise ValueError("emlis_thread_two_layer_body_invalid")
    checkpoint = prepared.checkpoint
    status = EngineStatus.LIMITED if checkpoint.assessment_status == "PARTIAL" else EngineStatus.GENERATED
    artifact = EmlisThreadBodyArtifactV1(identity("emlis-artifact", checkpoint.checkpoint_id, surface.text),
        observation, reception_text, checkpoint.source_prefix_ref, checkpoint.checkpoint_id,
        resolver.qualified_refs, projection.meaning_plan.meaning_visible_causal_trace_rows,
        projection.meaning_plan.reception_visible_causal_trace_rows, status)
    return EmlisThreadBodyOutcomeV1(status, artifact, projection.graph, ("emlis_thread_body_generated",))
