from __future__ import annotations

"""Source/version adapter to the existing sole Human Reception author."""

from dataclasses import fields, replace
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
    relations = hr.source_grounded_reception_move_relations(move, plan)
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


def _retained_shared_target_received_relations(prepared, plan, resolver):
    """An expired joint reading may leave its original contrast unchanged."""
    from emlis_ai_grounded_observation_plan import source_owned_shared_target_appraisal_contrast
    if not prepared.thread.answers:
        return frozenset()
    original = prepared.original_plan
    group = source_owned_shared_target_appraisal_contrast(original.nuclei, original.relations, resolver)
    if (not group or source_owned_shared_target_appraisal_contrast(plan.nuclei, plan.relations, resolver)
        or group['received_relation'] not in plan.relations):
        return frozenset()
    index = {n.nucleus_id: n for n in plan.nuclei}
    for key in ('received_event', 'reaction'):
        node = group[key]
        retained = replace(node, semantic_frame=replace(node.semantic_frame,
            attribute_codes=tuple(code for code in node.semantic_frame.attribute_codes
                if code != 'semantic_dependency:shared_target_appraisal_contrast_v1'
                and not code.startswith('source_shared_target_'))))
        if index.get(node.nucleus_id) != retained:
            return frozenset()
    return frozenset((group['received_relation'].relation_id,))


def _current_single_received_contrast_relations(prepared, plan):
    """Keep one unchanged original contrast time-neutral on the current route.

    Explicitly marked legacy routes retain their original surface grammar.
    This changes neither recognition nor the selected Reception content.
    """
    from emlis_ai_grounded_observation_plan import (
        _received_contrast_group_targets, _source_relief_received_group,
        source_owned_result_appraisal_context)
    if (prepared.checkpoint.assessment_status == 'PARTIAL'
        or prepared.legacy_appraisal_retention or prepared.legacy_repeated_appraisal_context
        or prepared.legacy_received_appraisal_context or prepared.legacy_appraisal_reason
        or prepared.legacy_result_appraisal or prepared.legacy_appraisal_correction
        or prepared.legacy_duplicate_appraisal_source or prepared.legacy_shared_target_contrast):
        return frozenset()
    contrasts = tuple(r for r in prepared.original_plan.relations if r.type == 'contrast')
    if len(contrasts) == 2 and not any(
            getattr(prepared, f.name) for f in fields(prepared) if f.name.startswith('legacy_')):
        # Prove the complete original P/R/(U) source, excluding supplemental
        # answer spans. A separate contrast must not imply simultaneous times.
        original, source = prepared.original_plan, prepared.thread.original
        group = _source_relief_received_group(original.nuclei, original.relations,
            source.evidence_spans, source.normalized_current_input)
        if group:
            contrasts = (group[-1],)
    if len(contrasts) != 1:
        # The initial unfinished appraisal owns its own contrast. It must
        # not force the separate, unchanged received pair into simultaneity.
        original = prepared.original_plan
        groups = tuple((r, context) for r in original.relations
            if (context := source_owned_result_appraisal_context(r, original.nuclei, original.relations)) is not None)
        if (prepared.thread.answers or len(contrasts) != 2 or len(groups) != 1
            or len(tuple(n for n in original.nuclei if n.source_fields in {('memo',), ('memo_action',)})) != 5
            or len(original.relations) != 3
            or plan.nuclei != original.nuclei or plan.relations != original.relations):
            return frozenset()
        appraisal, context = groups[0]
        contrasts = tuple(r for r in contrasts if (r.from_nucleus_id, r.to_nucleus_id)
                         != (context.nucleus_id, appraisal.to_nucleus_id))
        if len(contrasts) != 1:
            return frozenset()
    relation = contrasts[0]
    if relation.grounding_kind != 'user_stated_relation' or relation not in plan.relations:
        return frozenset()
    original = {n.nucleus_id: n for n in prepared.original_plan.nuclei}
    current = {n.nucleus_id: n for n in plan.nuclei}
    nodes = tuple(original.get(nid) for nid in (relation.from_nucleus_id, relation.to_nucleus_id))
    if (any(n is None or n.grounding_kind != 'explicit'
            or n.source_fields not in {('memo',), ('memo_action',)}
            or current.get(n.nucleus_id) != n for n in nodes)
        or not _received_contrast_group_targets(nodes, contrasts)):
        return frozenset()
    return frozenset((relation.relation_id,))


def _retained_unfinished_appraisal_relations(prepared, plan):
    """Join an unchanged appraisal after the separate received reaction is revised.

    This is a surface choice only. It never selects a new Reception reading
    or treats the replaced received contrast as a current relation.
    """
    from dataclasses import fields
    from emlis_ai_grounded_observation_plan import (
        source_owned_result_appraisal_context, _received_contrast_group_targets)
    thread, original, checkpoint = prepared.thread, prepared.original_plan, prepared.checkpoint
    update = checkpoint.answer_update
    if (any(getattr(prepared, f.name) for f in fields(prepared) if f.name.startswith('legacy_'))
        or len(thread.answers) != 1 or len(thread.control.answers) != 1 or thread.control.current_round != 1
        or checkpoint.assessment_status != 'RESOLVED' or checkpoint.unresolved_parts
        or update is None or update.disposition != 'MATERIAL_UPDATE'
        or update.unresolved_parts or len(update.updates) != 1):
        return frozenset()
    groups = tuple((r, context) for r in original.relations
        if (context := source_owned_result_appraisal_context(r, original.nuclei, original.relations)) is not None)
    required = tuple(n for n in original.nuclei if n.retention == 'required')
    if len(groups) != 1 or len(required) != 5 or len(original.relations) != 3:
        return frozenset()
    appraisal, context = groups[0]
    owned = {context.nucleus_id, appraisal.from_nucleus_id, appraisal.to_nucleus_id}
    rest = tuple(n for n in required if n.nucleus_id not in owned)
    edges = tuple(r for r in original.relations if owned & {r.from_nucleus_id, r.to_nucleus_id})
    received = tuple(r for r in original.relations if r not in edges)
    if (len(edges) != 2 or len(rest) != 2 or len(received) != 1
        or not _received_contrast_group_targets(rest, received)):
        return frozenset()
    old = received[0]
    item = update.updates[0]
    if (item.operation != 'REVISE' or item.binding_kind != 'EXPLICIT_CORRECTION'
        or item.target_meaning_refs != (old.to_nucleus_id,)
        or item.superseded_claim_refs != (old.to_nucleus_id,)
        or item.affected_dependency_refs != (old.relation_id,)
        or item.temporal_binding.about_time != 'ORIGINAL_OCCASION'
        or item.temporal_binding.anchor_source_ref != thread.original.envelope.envelope_id
        or checkpoint.accepted_update_refs != (item.update_ref,)
        or checkpoint.inactive_claim_refs != (old.to_nucleus_id, old.relation_id)
        or len(item.changed_claim_refs) != 1):
        return frozenset()
    current = {n.nucleus_id: n for n in plan.nuclei}
    answer_id, = item.changed_claim_refs
    answer = current.get(answer_id)
    remaining = tuple(r for r in plan.relations if r not in edges)
    if (any(current.get(n.nucleus_id) != n for n in original.nuclei if n.nucleus_id != old.to_nucleus_id)
        or set(current) != ({n.nucleus_id for n in original.nuclei} - {old.to_nucleus_id}) | {answer_id}
        or not set(edges).issubset(plan.relations) or len(remaining) != 1
        or answer is None or answer.source_fields != ('answer_text_private',)
        or answer.grounding_kind != 'explicit' or answer.retention != 'required'
        or answer.semantic_frame.actor != 'current_user'
        or answer.semantic_frame.time_scope != 'past'
        or {c for c in answer.semantic_frame.attribute_codes if c.startswith('thread_time:')}
            != {'thread_time:original_occasion'}):
        return frozenset()
    relation = remaining[0]
    if (relation.type != 'evaluation_about_event'
        or (relation.from_nucleus_id, relation.to_nucleus_id) != (old.from_nucleus_id, answer_id)
        or relation.grounding_kind != 'user_stated_relation'
        or relation.source_relation_ids != (item.update_ref,)
        or set(plan.coverage_requirements.required_nucleus_ids) != owned | {old.from_nucleus_id, answer_id}
        or set(plan.coverage_requirements.required_relation_ids) != {r.relation_id for r in plan.relations}):
        return frozenset()
    return frozenset((appraisal.relation_id,))


def _snapshot_binding_traces(plan, projection, resolver, observation, reception_text):
    from .emlis_semantic_admission import SnapshotEvidenceSpanResolverV2
    if type(resolver) is not SnapshotEvidenceSpanResolverV2:
        return (), ()
    import re
    from .contracts import SnapshotBindingConsumptionV2
    from emlis_ai_grounded_observation_plan import source_snapshot_v2_group
    from emlis_ai_grounded_observation_gate import read_snapshot_observation_clause, read_source_owned_discourse
    result = {"OBSERVATION":[], "RECEPTION":[]}
    for kind, ids, lexical in source_snapshot_v2_group(plan.nuclei,plan.relations,resolver):
        moves = tuple(m for m in plan.response_plan.human_reception_plan.moves
            if set((*m.target_nucleus_ids,*m.support_nucleus_ids)) == set(ids))
        if len(moves) != 1: raise ValueError("snapshot_v2_trace_move_unbound")
        spans = {}
        for section,text in (("OBSERVATION",observation),("RECEPTION",reception_text)):
            rows = tuple(m for m in re.finditer(r"[^。\n]+。",text)
                if (read_snapshot_observation_clause(m.group().strip(),kind,lexical) if section == "OBSERVATION" else
                    read_source_owned_discourse(m.group().strip(),moves[0],plan,resolver,projection.selected_reception,
                        preceding_observation=observation) is not None))
            if len(rows) != 1: raise ValueError("snapshot_v2_trace_visible_binding_unbound")
            spans[section] = rows[0].span()
        edges = tuple(e for e in plan.relations if (e.from_nucleus_id,e.to_nucleus_id) == ids)
        graph_edges = tuple(_edge_ref(projection.binding.relation_to_edge[e.relation_id]) for e in edges)
        rows = [("SOURCE_SLICE",s.slice_ref,(s.nucleus_ref,),(s.slice_ref,))
            for s in resolver.source_slices if s.nucleus_ref in ids]
        rows += [("WRITTEN_CASE",a.argument_ref,(a.owning_nucleus_ref,),a.source_slice_refs)
            for a in resolver.case_arguments if a.owning_nucleus_ref in ids]
        rows += [("PERSON_STATED_UNKNOWN",u.unknown_ref,(u.statement_nucleus_ref,*u.target_nucleus_refs),u.evidence_slice_refs)
            for u in resolver.person_stated_unknowns if u.statement_nucleus_ref in ids]
        rows += [("WRITTEN_LINK",w.relation_ref,(w.from_nucleus_ref,w.to_nucleus_ref),w.marker_slice_refs)
            for w in resolver.written_links if (w.from_nucleus_ref,w.to_nucleus_ref) == ids]
        for section in result:
            for family,ref,nuclei,slices in rows:
                result[section].append(SnapshotBindingConsumptionV2(resolver.snapshot_ref,family,ref,nuclei,
                    tuple(_node_ref(projection.binding.nucleus_to_node[n]) for n in nuclei),graph_edges,slices,
                    section,*spans[section]))
    return tuple(result["OBSERVATION"]),tuple(result["RECEPTION"])


def realize_emlis_thread_body(prepared) -> EmlisThreadBodyOutcomeV1:
    plan = build_updated_grounded_plan(prepared)
    projection = project_thread_meaning(prepared, plan)
    from .emlis_semantic_admission import snapshot_resolver
    resolver = snapshot_resolver(prepared)
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
    joined_ids = _retained_unfinished_appraisal_relations(prepared, plan)
    neutral_ids = (_retained_shared_target_received_relations(prepared, plan, resolver)
        | _current_single_received_contrast_relations(prepared, plan))
    preceding_observation = surface_owner.realize_grounded_observation_text(
        sentence_plan, plan, resolver, selected_subjective_input=selected,
        joined_unfinished_appraisal_ids=joined_ids, neutral_received_contrast_ids=neutral_ids)
    human_surface = hr.realize_source_grounded_human_reception(reception, expressions,
        {n.nucleus_id: n for n in plan.nuclei}, resolver, plan=plan, recovery_stage="full",
        clause_plans=clauses, selected_subjective_input=selected, preceding_observation=preceding_observation)
    surface, _placements = surface_owner.realize_grounded_sentence_plan_with_human_reception(
        sentence_plan, plan, resolver, human_reception_surface=human_surface,
        selected_subjective_input=selected, preceding_observation=preceding_observation,
        joined_unfinished_appraisal_ids=joined_ids, neutral_received_contrast_ids=neutral_ids)
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
    status = EngineStatus.LIMITED if (projection.premeaning.material_unknown_refs
        or plan.input_profile.material_quality in {"limited_grounding", "labels_only_limited"}) else EngineStatus.GENERATED
    snapshot_meaning_trace, snapshot_reception_trace = _snapshot_binding_traces(
        plan, projection, resolver, observation, reception_text)
    artifact = EmlisThreadBodyArtifactV1(identity("emlis-artifact", checkpoint.checkpoint_id, surface.text),
        observation, reception_text, checkpoint.source_prefix_ref, checkpoint.checkpoint_id,
        resolver.qualified_refs, (*projection.meaning_plan.meaning_visible_causal_trace_rows, *snapshot_meaning_trace),
        (*projection.meaning_plan.reception_visible_causal_trace_rows, *snapshot_reception_trace), status)
    if prepared.thread.control.admitted_history:
        from .emlis_thread_history import history_line_plan, derive_interpretive_frames
        from emlis_ai_grounded_observation_gate import evaluate_emlis_history_line_inverse
        try:
            line_plan = history_line_plan(prepared, plan)
            line = surface_owner.realize_emlis_history_line(line_plan) if line_plan else None
            if line and not evaluate_emlis_history_line_inverse(line, line_plan, prepared=prepared):
                raise ValueError("emlis_history_line_inverse_failed")
            frames = tuple(frame for frame in derive_interpretive_frames(prepared.thread)
                           if frame.frame_key not in prepared.thread.control.rejected_frame_keys)
            artifact = replace(artifact, history_line=line, history_line_plan=line_plan, interpretive_frames=frames)
        except ValueError:
            # Optional context must not erase independently valid current
            # Observation/Reception. No history line or frame is emitted.
            pass
    return EmlisThreadBodyOutcomeV1(status, artifact, projection.graph, ("emlis_thread_body_generated",))
