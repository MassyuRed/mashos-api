from __future__ import annotations

"""Bind admitted Emlis sources to the shared meaning and Reception owners.

This module constructs no prose. Both projections below are the same
post-admission functions used by the single-input Stage-1 compiler.
"""

from dataclasses import dataclass, replace
from types import SimpleNamespace

from . import contracts as c
from . import emlis_stage1_response as r
from . import emlis_stage1_composition as composition
from .emlis_input_specific_meaning import (
    derive_grounded_situation_view, derive_foreground_scope_closed,
    derive_input_specific_meaning_structure, validate_grounded_situation_view,
)
from .emlis_thread_contracts import THREAD_SCHEMA
from .emlis_thread_source import identity
import emlis_ai_grounded_human_reception as hr
from emlis_ai_grounded_observation_plan import (
    source_owned_result_appraisal, source_owned_result_appraisal_context, source_owned_result_appraisal_reason,
    _source_operator_owner_scope_is_bound, _received_contrast_group_targets,
    _thread_retained_reaction_groups,
)


@dataclass(frozen=True, slots=True, repr=False)
class ThreadMeaningProjection:
    graph: c.GroundedMeaningGraph
    parent: c.ExperiencePlan
    premeaning: c.PreMeaningGroundedInputs
    structure: object
    meaning_plan: object
    selected_reception: hr.SelectedSubjectiveReceptionInputV1
    binding: object


def _appraisal_received_components(prepared, plan, resolver):
    """Admit only one already-owned appraisal and one received contrast."""
    links = tuple(e for e in plan.relations if source_owned_result_appraisal(e, plan.nuclei))
    if len(links) != 1:
        return False
    link = links[0]
    index = {n.nucleus_id: n for n in plan.nuclei}
    event, evaluation = (index[nid] for nid in (link.from_nucleus_id, link.to_nucleus_id))
    if source_owned_result_appraisal_context(link, plan.nuclei, plan.relations) is not None:
        return False
    reason = source_owned_result_appraisal_reason(link, plan.nuclei, plan.relations)
    owned = {event.nucleus_id, evaluation.nucleus_id}
    answers = tuple(n for n in plan.nuclei if n.source_fields == ('answer_text_private',))
    if answers:
        # Preserve precisely u279's original-occasion negative correction.
        original = prepared.original_plan
        old_links = tuple(e for e in original.relations
            if source_owned_result_appraisal(e, original.nuclei)
            and e.from_nucleus_id == event.nucleus_id)
        if len(old_links) != 1:
            return False
        old_reason = source_owned_result_appraisal_reason(old_links[0], original.nuclei, original.relations)
        if (old_reason is None or index.get(old_reason.nucleus_id) != old_reason
            or answers != (evaluation,) or reason is not None
            or {v for v in evaluation.semantic_frame.attribute_codes if v.startswith('thread_time:')}
                != {'thread_time:original_occasion'}
            or {v for v in evaluation.semantic_frame.attribute_codes if v.startswith('source_appraisal_')}
                != {'source_appraisal_kind:satisfaction', 'source_appraisal_degree:unmarked'}
            or evaluation.semantic_frame.polarity != 'negative'
            or any(old_reason.nucleus_id in (e.from_nucleus_id, e.to_nucleus_id) for e in plan.relations)):
            return False
        reason = old_reason
    if reason is not None:
        owned.add(reason.nucleus_id)
    required = tuple(n for n in plan.nuclei if n.nucleus_id in plan.coverage_requirements.required_nucleus_ids
                     and set(n.source_fields) & {'memo', 'memo_action', 'answer_text_private'})
    rest = tuple(n for n in required if n.nucleus_id not in owned)
    rest_ids = {n.nucleus_id for n in rest}
    rest_relations = tuple(e for e in plan.relations
        if {e.from_nucleus_id, e.to_nucleus_id} <= rest_ids)
    received = _received_contrast_group_targets(rest, rest_relations)
    if (len(rest) != 2 or len(rest_relations) != 1 or not received or len(received[0]) != 1
        or any({e.from_nucleus_id, e.to_nucleus_id} & rest_ids
               and not {e.from_nucleus_id, e.to_nucleus_id} <= rest_ids for e in plan.relations)
        or len(plan.response_plan.human_reception_plan.moves) != 2):
        return False
    # Equal/nearby occurrences are not an ownership proof for this opt-in.
    for n in (event, *rest):
        if len(n.source_span_ids) != 1:
            return False
        span = resolver.resolve(n.source_span_ids[0])
        if sum(s.source_field == span.source_field and s.raw_text == span.raw_text
               for s in resolver.resolve_many(resolver.span_ids)) != 1:
            return False
    if answers and _thread_retained_reaction_groups(plan.nuclei, plan.relations) != (
            ('current_burden', (evaluation.nucleus_id,), (event.nucleus_id,)),
            ('current_burden', *received)):
        return False
    return True


def _component_reception_rows(structure, bound_moves, contributions):
    domains = c.component_reception_bundle_domains(structure)
    rows = []
    for bound in bound_moves:
        refs = {row.contribution_id for row in bound.basis_contributions}
        owned = tuple(row for row in contributions if row.contribution_id in refs)
        nodes = {ref for row in owned for ref in row.semantic_refs}
        matches = tuple((ref, relations) for ref, (domain, relations) in domains.items() if domain == nodes)
        if len(matches) != 1:
            raise ValueError('emlis_thread_component_move_unbound')
        component, relations = matches[0]
        row = c.ComponentReceptionOpportunityV1('cocolon.cmee.component_reception_opportunity.v1', '',
            bound.move.move_id, bound.move.reception_act, component,
            tuple(row.contribution_id for row in owned), relations)
        rows.append(replace(row, opportunity_ref=c.component_reception_opportunity_ref(
            row, structure.meaning_decision_outcome.reading_id)))
    result = tuple(rows)
    c.validate_component_reception_opportunities(result, structure, contributions)
    return result


def project_thread_meaning(prepared, plan) -> ThreadMeaningProjection:
    from .emlis_answer_update import build_updated_grounded_plan
    if plan != build_updated_grounded_plan(prepared):
        raise ValueError("emlis_thread_plan_checkpoint_mismatch")
    thread, checkpoint = prepared.thread, prepared.checkpoint
    source_version = c.EMLIS_Q3_SOURCE_VERSION if thread.control.capability_snapshot.startswith("Q3_") else THREAD_SCHEMA
    resolver = thread.resolver()
    index = {n.nucleus_id: n for n in plan.nuclei}
    nodes, edges, dispositions = [], [], []
    node_ids, edge_ids = {}, {}
    for n in plan.nuclei:
        ev = tuple(resolver.qualified_ref(s).evidence.evidence_id for s in n.source_span_ids)
        node_id = identity("mn", checkpoint.checkpoint_id, n.nucleus_id, ev)
        owner = identity("owner", node_id)
        node_ids[n.nucleus_id] = node_id
        nodes.append(c.MeaningNode(node_id, owner, n.kind, n.grounding_kind,
            hr.final_reception_source_anchor_text(n.nucleus_id, index, resolver),
            c.EpistemicState.SOURCE_EXPLICIT, ev))
        supplemental = any(resolver.qualified_ref(s).source_envelope_id != thread.original.envelope.envelope_id
                           for s in n.source_span_ids)
        dispositions.append(c.OwnerDisposition(owner, c.OwnerClass.REQUIRED if n.nucleus_id in plan.coverage_requirements.required_nucleus_ids else c.OwnerClass.ACTIVE_OPTIONAL,
            c.ResolverResolution.UNIQUE, c.AttachmentAdmission.PROVISIONAL_ONLY,
            c.VisibleAuthority.SUPPLEMENTAL_USER if supplemental else c.VisibleAuthority.SOURCE_EXPLICIT,
            c.SourceOwnerDisposition.SUPPLEMENTAL_USER_VISIBLE if supplemental else c.SourceOwnerDisposition.SOURCE_EXPLICIT_VISIBLE,
            (node_id,), ev, None, ("versioned_source_bound",)))
    for relation in plan.relations:
        ev = tuple(resolver.qualified_ref(s).evidence.evidence_id for s in relation.source_span_ids)
        edge_id = identity("me", checkpoint.checkpoint_id, relation.relation_id, ev)
        owner = identity("owner", edge_id)
        edge_ids[relation.relation_id] = edge_id
        edges.append(c.MeaningEdge(edge_id, owner, relation.type,
            node_ids[relation.from_nucleus_id], node_ids[relation.to_nucleus_id],
            relation.grounding_kind, c.EpistemicState.SOURCE_EXPLICIT, ev))
        supplemental = any(resolver.qualified_ref(s).source_envelope_id != thread.original.envelope.envelope_id
                           for s in relation.source_span_ids)
        dispositions.append(c.OwnerDisposition(owner, c.OwnerClass.REQUIRED if relation.relation_id in plan.coverage_requirements.required_relation_ids else c.OwnerClass.ACTIVE_OPTIONAL,
            c.ResolverResolution.UNIQUE, c.AttachmentAdmission.PROVISIONAL_ONLY,
            c.VisibleAuthority.SUPPLEMENTAL_USER if supplemental else c.VisibleAuthority.SOURCE_EXPLICIT,
            c.SourceOwnerDisposition.SUPPLEMENTAL_USER_VISIBLE if supplemental else c.SourceOwnerDisposition.SOURCE_EXPLICIT_VISIBLE,
            (edge_id,), ev, None, ("versioned_source_bound",)))
    visible_owners = tuple(x.meaning_owner_id for x in dispositions)
    unknown_owners = []
    epistemic_boundaries = {}
    for unknown in plan.unknown_boundaries:
        # An unreflected answer span constrains what the body may claim to
        # have understood. It is not an unknown inside the accepted reading.
        # Its source-bound disclosure remains a mandatory Sentence/Gate duty.
        if unknown.dimension == "answer_interpretation_unresolved":
            continue
        ev = tuple(resolver.qualified_ref(s).evidence.evidence_id for s in unknown.evidence_span_ids)
        if not ev:
            if unknown.dimension == "source_explicit_epistemic_limit":
                raise ValueError("emlis_thread_epistemic_unknown_source_unbound")
            continue
        node_id = identity("unknown", checkpoint.checkpoint_id, unknown.unknown_id)
        owner = identity("owner", node_id)
        unknown_owners.append(owner)
        if unknown.dimension == "source_explicit_epistemic_limit":
            epistemic_boundaries[node_id] = unknown
        nodes.append(c.MeaningNode(node_id, owner, "unknown", "unknown", unknown.dimension,
                                   c.EpistemicState.UNKNOWN, ev))
        dispositions.append(c.OwnerDisposition(owner, c.OwnerClass.REQUIRED,
            c.ResolverResolution.UNRESOLVED, c.AttachmentAdmission.UNRESOLVED,
            c.VisibleAuthority.NONE, c.SourceOwnerDisposition.UNKNOWN_PRESERVED_LIMITED,
            (node_id,), ev, node_id, ("preserved_original_unknown",)))
    owner_refs = tuple(x.meaning_owner_id for x in dispositions if x.owner_class is c.OwnerClass.REQUIRED)
    optional_owners = tuple(x.meaning_owner_id for x in dispositions if x.owner_class is c.OwnerClass.ACTIVE_OPTIONAL)
    owner_digest = identity("owner-universe", owner_refs)
    graph = c.GroundedMeaningGraph(identity("graph", checkpoint.checkpoint_id),
        thread.source_prefix_ref, tuple(nodes), tuple(edges), tuple(dispositions),
        owner_refs, optional_owners, source_version, "cocolon.cmee.emlis_thread_obligations.v1", owner_digest)
    reception = plan.response_plan.human_reception_plan
    acts = tuple(dict.fromkeys(m.reception_act for m in reception.moves))
    parent = c.ExperiencePlan(identity("plan", checkpoint.checkpoint_id), thread.source_prefix_ref,
        source_version, graph.obligation_version, owner_digest, THREAD_SCHEMA,
        identity("observation-duty", checkpoint.checkpoint_id), identity("unknown-duty", checkpoint.checkpoint_id),
        identity("reception-duty", checkpoint.checkpoint_id), identity("reception-plan", str(reception)),
        acts, tuple(o for o in owner_refs if o in visible_owners), visible_owners, visible_owners,
        tuple(unknown_owners), tuple(unknown_owners), tuple(unknown_owners), ())
    covered = {n for edge in plan.relations if edge.relation_id in plan.coverage_requirements.required_relation_ids
               and edge.type != "evaluation_about_event"
               for n in (edge.from_nucleus_id, edge.to_nucleus_id)}
    # Both initial and updated thread projection keep the direct unfinished
    # witness required by the existing strict unknown-source binding. A
    # relational contribution cannot discharge this separate epistemic duty.
    covered.difference_update(nid for boundary in plan.unknown_boundaries
        if boundary.dimension == "source_explicit_epistemic_limit"
        and boundary.surface_policy == "hedge_only" and len(boundary.affected_nucleus_ids) == 1
        for nid in boundary.affected_nucleus_ids
        if nid in index and index[nid].kind == index[nid].semantic_frame.predicate_kind == "uncertainty"
        and index[nid].grounding_kind == "explicit"
        and "semantic_role:limiting_unknown" in index[nid].semantic_frame.attribute_codes
        and boundary.evidence_span_ids == index[nid].source_span_ids
        and nid in plan.coverage_requirements.required_nucleus_ids)
    binding = r._PlanBinding(
        node_meta={node_ids[n.nucleus_id]: n for n in plan.nuclei},
        edge_meta={edge_ids[e.relation_id]: e for e in plan.relations},
        nucleus_to_node=node_ids, relation_to_edge=edge_ids,
        required_node_ids=frozenset(node_ids[n] for n in plan.coverage_requirements.required_nucleus_ids if n not in covered),
        required_edge_ids=frozenset(edge_ids[e.relation_id] for e in plan.relations
            if e.relation_id in plan.coverage_requirements.required_relation_ids and e.type != "evaluation_about_event"),
        source_order={ref: i for i, ref in enumerate((*node_ids.values(), *edge_ids.values()))})
    rows = r._candidate_rows_from_binding(graph=graph, parent_plan=parent, binding=binding,
        visible_claim_ids=set((*node_ids.values(), *edge_ids.values())),
        obligation_kind_by_owner={owner: "THOUGHT_MEANING" for owner in (*owner_refs, *optional_owners)},
        stage1_response_schema_version=c.CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2)
    candidates = r._interpretation_candidates_from_rows(rows)
    source_refs = SimpleNamespace(evidence_refs=tuple(x.evidence for x in resolver.qualified_refs))
    field = r._build_emlis_meaning_field_from_rows(graph, parent, rows, source=source_refs,
        stage1_response_schema_version=c.CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2)
    contributions = r._plan_layer1_observation_from_rows(parent, rows,
        stage1_response_schema_version=c.CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2)
    depth = r.classify_observation_depth(contributions, contribution_cap=c.observation_contribution_cap(source_version))
    qualifiers = []
    shift_endpoints = c.project_stage1_source_explicit_shift_endpoint_node_ids(graph)
    for node in graph.nodes:
        if node.node_id not in binding.node_meta:
            continue
        frame = binding.node_meta[node.node_id].semantic_frame
        aspects = tuple(v for v in frame.attribute_codes if v.startswith("aspect:"))
        qualifiers.append(c.GroundedSourceQualifierRow(r._node_ref(node.node_id), (
            "epistemic:provisional_interpretation", f"actor:{frame.actor}", "world:unknown",
            aspects[0] if aspects else "aspect:unknown", f"polarity:{frame.polarity}",
            f"modality:{frame.modality}", f"time_scope:{frame.time_scope}",
            *c.project_stage1_source_contract_qualifiers(source_attribute_codes=frame.attribute_codes,
                source_explicit_shift_relation_endpoint=node.node_id in shift_endpoints,
                stage1_response_schema_version=c.CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2))))
    relation_rows = tuple(c.GroundedSourceRelationRow(r._edge_ref(e.edge_id), kind)
        for e in graph.edges if (kind := (c.EmlisThreadScopeRelationKind.ABOUT_TARGET
            if e.relation == "evaluation_about_event" and (any(
                ref in checkpoint.accepted_update_refs for ref in binding.edge_meta[e.edge_id].source_relation_ids)
                or source_owned_result_appraisal(binding.edge_meta[e.edge_id], plan.nuclei))
            else c.EmlisThreadScopeRelationKind.SATISFACTION_REASON
            if e.relation == 'user_stated_cause' and any(
                (reason := source_owned_result_appraisal_reason(about, plan.nuclei, plan.relations)) is not None
                and (binding.edge_meta[e.edge_id].from_nucleus_id, binding.edge_meta[e.edge_id].to_nucleus_id)
                    == (reason.nucleus_id, about.to_nucleus_id) for about in plan.relations)
            else c.project_foreground_scope_relation_kind(e.relation))) is not None)
    pre = c.PreMeaningGroundedInputs("1.0", c.CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2,
        graph, r._graph_ref(graph), parent.observation_duty_id, candidates, field, contributions,
        tuple(x.contribution_id for x in contributions), field.material_unknown_refs, depth,
        tuple(sorted(qualifiers, key=lambda x: x.node_ref)), relation_rows)
    for disposition in dispositions:
        carrier = c.source_explicit_epistemic_unknown_object_ref(pre, disposition)
        if carrier is None:
            continue
        unknown = epistemic_boundaries[disposition.target_unknown_ref]
        affected = tuple(index[nid] for nid in unknown.affected_nucleus_ids if nid in index)
        if (len(unknown.affected_nucleus_ids) != 1 or len(affected) != 1
            or unknown.evidence_span_ids != affected[0].source_span_ids
            or unknown.surface_policy != "hedge_only"
            or carrier != r._node_ref(node_ids[affected[0].nucleus_id])
            or affected[0].source_fields not in {("memo",), ("memo_action",)}
            or "semantic_role:limiting_unknown" not in affected[0].semantic_frame.attribute_codes):
            raise ValueError("emlis_thread_epistemic_unknown_source_unbound")
    # The v1.1 component policy is admitted from the validated source Plan,
    # not a downstream request to turn LIMITED into NORMAL. Its first scope
    # is an original explicit appraisal plus source-owned performed actions.
    appraisals = tuple(e for e in plan.relations if source_owned_result_appraisal(e, plan.nuclei))
    appraisal_endpoints = {nid for e in appraisals for nid in (e.from_nucleus_id, e.to_nucleus_id)}
    # Only a source-proved, connected unfinished fact may accompany this
    # appraisal pair. Other independent required content keeps the performed
    # SELF-action boundary; adjacency cannot activate the component policy.
    appraisal_endpoints.update(context.nucleus_id for e in appraisals
        if (context := source_owned_result_appraisal_context(e, plan.nuclei, plan.relations)) is not None)
    appraisal_endpoints.update(reason.nucleus_id for e in appraisals
        if (reason := source_owned_result_appraisal_reason(e, plan.nuclei, plan.relations)) is not None)
    independent_required = tuple(n for n in plan.nuclei
        if n.nucleus_id in plan.coverage_requirements.required_nucleus_ids
        and n.nucleus_id not in appraisal_endpoints)
    component_reception = _appraisal_received_components(prepared, plan, resolver)
    component_refs = tuple(sorted(r._edge_ref(edge_ids[e.relation_id]) for e in appraisals)) if (component_reception or (
        appraisals and all(n.kind == n.semantic_frame.predicate_kind and n.kind in {'action', 'event'}
            and n.grounding_kind == 'explicit' and n.semantic_frame.actor == 'current_user'
            and n.semantic_frame.modality == 'fact'
            and 'operator:performed_action' in n.semantic_frame.attribute_codes
            and n.source_fields in {('memo',), ('memo_action',)}
            and n.allowed_claim_scope == 'explicit_current_input' and len(n.source_span_ids) == 1
            and (anchor := hr.final_reception_source_anchor_text(n.nucleus_id, index, resolver))
            and _source_operator_owner_scope_is_bound(anchor)
            for n in independent_required))) else ()
    view = derive_grounded_situation_view(pre, appraisal_component_relation_refs=component_refs)
    validate_grounded_situation_view(view, pre, graph, appraisal_component_relation_refs=component_refs)
    scope = derive_foreground_scope_closed(view)
    structure = derive_input_specific_meaning_structure(view, scope)
    c.validate_input_specific_meaning_structure(structure, grounded_view=view, foreground_scope_derivation=scope)
    bound_moves = r._bind_reception_moves(reception, binding=binding, contributions=contributions)
    retained = tuple(composition.RetainedReceptionActRow(act, act,
        tuple(dict.fromkeys(row.contribution_id for move in bound_moves
            if move.move.reception_act == act for row in move.basis_contributions))) for act in acts)
    if component_reception and type(structure.meaning_decision_outcome) is c.SelectedEmlisProvisionalReading:
        retained = _component_reception_rows(structure, bound_moves, contributions)
    retained_refs = tuple(row.act_ref for row in retained)
    contribution_map = tuple((row.contribution_id, r.resolve_candidate_for_contribution(candidates, row).candidate_id)
                             for row in contributions)
    qualifier_values = []
    for candidate in candidates:
        relation = c.stage1_candidate_uses_relation_qualifier_scope(candidate)
        for argument in candidate.argument_bindings if relation else (None,):
            role = argument.role if argument else None
            for axis in composition.ClauseScalarAxis:
                qualifier_values.append(composition.QualifierValueRow(candidate.candidate_id,
                    composition.QualifierLookupScope.RELATION_SOURCE_BINDING if relation else composition.QualifierLookupScope.DIRECT_UNQUALIFIED,
                    role, argument.semantic_ref if argument else None, axis,
                    r.resolve_qualifier_value(candidate, axis.value.lower(), role=role)))
    style = r._style_policy_ref_for_stance(str(reception.stance))
    temperature = r._temperature_for_reception_asset(reception, plan)
    preimage = c.project_stage1_projection_preimage_ref(grounded_graph_ref=r._graph_ref(graph),
        parent_observation_duty_ref=parent.observation_duty_id, parent_reception_duty_ref=parent.reception_duty_id,
        interpretation_candidate_ids=tuple(x.candidate_id for x in candidates), meaning_field_id=field.meaning_field_id,
        observation_contribution_ids=tuple(x.contribution_id for x in contributions), retained_reception_act_ids=retained_refs,
        observation_depth_class=depth, temperature_class=temperature, reception_style_policy_ref=style,
        emlis_value_policy_ref=c.CMEE_STAGE1_VALUE_POLICY_REF)
    records = r.build_stage1_post_selection_reception_records(input_specific_meaning_structure=structure,
        projection_preimage_ref=preimage, retained_reception_act_rows=retained,
        observation_contribution_rows=contributions, interpretation_candidate_rows=candidates,
        contribution_to_candidate_ref_map=contribution_map, qualifier_value_rows=tuple(qualifier_values),
        material_unknown_refs=field.material_unknown_refs, expected_act_refs=retained_refs)
    consequence, sealed, propositions, sets, bounded, bounded_propositions, seal = records
    authority = composition._ProjectionCommonAuthority(view, scope, structure, thread, graph, plan,
        r._graph_ref(graph), parent, c.AllowedReceptionOpportunityEnvelope("1.0", thread.source_prefix_ref,
            parent.reception_duty_id, acts, plan.safety_policy.required_boundary_codes),
        parent.observation_duty_id, preimage, seal, parent.reception_duty_id, field.meaning_field_id,
        depth, temperature, style, c.CMEE_STAGE1_VALUE_POLICY_REF, candidates, contributions,
        retained, field.material_unknown_refs, contribution_map, tuple(qualifier_values))
    outcome = structure.meaning_decision_outcome
    if isinstance(outcome, c.SelectedEmlisProvisionalReading):
        inputs = composition.SelectedReadingProjectionInputs(authority, outcome, consequence, sealed, propositions, sets)
        composition._validate_tagged_projection_semantic_closure(inputs, authority)
        meaning = composition._project_selected_reading_from_admitted_authority(inputs, authority)
    else:
        inputs = composition.LimitedProjectionInputs(authority, outcome, bounded, bounded_propositions)
        composition._validate_tagged_projection_semantic_closure(inputs, authority)
        meaning = composition._project_limited_subjective_from_admitted_authority(inputs, authority)
    selected = _selected_reception(meaning, reception, plan, resolver, binding, retained)
    return ThreadMeaningProjection(graph, parent, pre, structure, meaning, selected, binding)


def _selected_reception(meaning, reception, plan, resolver, binding, retained=()):
    decisions = []
    component_rows = tuple(row for row in retained if type(row) is c.ComponentReceptionOpportunityV1)
    if component_rows and (len(component_rows) != len(reception.moves)
        or {row.move_ref for row in component_rows} != {move.move_id for move in reception.moves}):
        raise ValueError('emlis_thread_component_move_unbound')
    for move in reception.moves:
        owned = tuple(row for row in retained if type(row) is c.ComponentReceptionOpportunityV1
                      and row.move_ref == move.move_id and row.reception_act == move.reception_act)
        ref = owned[0].opportunity_ref if len(owned) == 1 else move.reception_act
        claims = tuple(row for row in meaning.subjective_claim_rows if ref in row.source_reception_act_refs)
        if len(claims) != 1:
            raise ValueError("emlis_thread_selected_reception_ambiguous")
        claim = claims[0]
        proposition = claim.asserted_subjective_proposition
        if component_rows:
            if len(owned) != 1:
                raise ValueError('emlis_thread_component_move_unbound')
            actual_ids = set((*move.target_nucleus_ids, *move.support_nucleus_ids))
            actual_nodes = {r._node_ref(binding.nucleus_to_node[nid]) for nid in actual_ids}
            actual_relations = tuple(sorted(r._edge_ref(binding.relation_to_edge[edge.relation_id])
                for edge in plan.relations if {edge.from_nucleus_id, edge.to_nucleus_id} <= actual_ids))
            if (set(proposition.response_object_refs) != actual_nodes
                or owned[0].bound_relation_refs != actual_relations
                or proposition.target_contribution_refs != owned[0].basis_contribution_refs):
                raise ValueError('emlis_thread_component_move_unbound')
        traces = tuple(row for row in meaning.reception_visible_causal_trace_rows
                       if row.projected_claim_ref == claim.subjective_claim_id)
        if len(traces) != 1:
            raise ValueError("emlis_thread_selected_reception_trace_invalid")
        trace = traces[0]
        by_basis = {row.binding_ref: row for row in meaning.subjective_basis_binding_rows}
        by_qualifier = {row.source_qualifier_binding_ref: row for row in meaning.source_qualifier_binding_rows}
        decisions.append(hr.identify_selected_subjective_reception_decision(hr.SelectedSubjectiveReceptionDecisionV1(
            "", meaning.projection_branch.value, trace.meaning_outcome_ref, trace.reception_record_ref,
            claim.subjective_claim_id, claim.selected_subjective_opportunity_key, move.move_id, move.reception_act,
            move.target_nucleus_ids, move.support_nucleus_ids, trace.layer1_contribution_refs, proposition,
            tuple(by_basis[ref] for ref in proposition.basis_binding_refs),
            tuple(by_qualifier[ref] for ref in proposition.source_qualifier_binding_refs))))
    decisions = r._partition_shared_reception_move_contributions(decisions, reception, binding)
    selected = hr.identify_selected_subjective_reception_input(hr.SelectedSubjectiveReceptionInputV1(
        "", meaning.projection_preimage_ref, meaning.projection_seal_ref,
        hr.selected_subjective_reception_grounding_ref(plan, resolver),
        tuple((r._node_ref(ref), nid) for nid, ref in binding.nucleus_to_node.items()),
        tuple((r._edge_ref(ref), rid) for rid, ref in binding.relation_to_edge.items()), tuple(decisions)))
    hr.validate_selected_subjective_reception_input(selected, reception, plan, resolver)
    return selected
