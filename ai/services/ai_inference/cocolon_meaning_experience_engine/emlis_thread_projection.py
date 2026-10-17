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
    source_owned_shared_target_appraisal_contrast,
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
    context = source_owned_result_appraisal_context(link, plan.nuclei, plan.relations)
    reason = source_owned_result_appraisal_reason(link, plan.nuclei, plan.relations)
    owned = {event.nucleus_id, evaluation.nucleus_id}
    if context is not None:
        from dataclasses import fields
        from .emlis_answer_update import PreparedEmlisMeaning
        # u301 admits only the already-owned initial triple. An answer,
        # historical source restoration or unresolved meaning stays on its
        # existing route, even if a triple survives in the resulting Plan.
        if (type(prepared) is not PreparedEmlisMeaning
            or any(getattr(prepared, field.name) for field in fields(prepared)
                   if field.name.startswith('legacy_'))
            or prepared.thread.answers or prepared.thread.control.answers
            or prepared.thread.control.current_round != 0 or prepared.accepted_nuclei
            or prepared.checkpoint.assessment_status != 'RESOLVED'
            or prepared.checkpoint.answer_update is not None
            or prepared.checkpoint.accepted_update_refs or prepared.checkpoint.inactive_claim_refs
            or prepared.checkpoint.unresolved_parts or reason is not None):
            return False
        owned.add(context.nucleus_id)
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
    if context is not None:
        import re
        import emlis_ai_grounded_observation_plan as gp
        text_nodes = tuple(n for n in plan.nuclei
            if set(n.source_fields) & {'memo', 'memo_action', 'answer_text_private'})
        expected_ids = owned | rest_ids
        moves = plan.response_plan.human_reception_plan.moves
        expected_moves = {
            ('recognize_lived_change', (evaluation.nucleus_id,),
             (context.nucleus_id, event.nucleus_id), event.source_span_ids),
            ('stay_with_current_burden', *received, index[received[0][0]].source_span_ids),
        }
        if (len(expected_ids) != 5 or len(text_nodes) != 5
            or {n.nucleus_id for n in text_nodes} != expected_ids
            or {n.nucleus_id for n in plan.nuclei if n.retention == 'required'} != expected_ids
            or set(plan.coverage_requirements.required_nucleus_ids) != expected_ids
            or len(plan.relations) != 3
            or set(plan.coverage_requirements.required_relation_ids) != {r.relation_id for r in plan.relations}
            or any(r.retention != 'required' or r.grounding_kind != 'user_stated_relation'
                   for r in plan.relations)
            or any(not m.required for m in moves)
            or {(m.reception_act, m.target_nucleus_ids, m.support_nucleus_ids,
                 m.source_evidence_span_ids) for m in moves} != expected_moves
            or any(u.surface_policy != 'do_not_claim' or u.evidence_span_ids
                   or u.dimension == 'source_explicit_epistemic_limit' for u in plan.unknown_boundaries)):
            return False
        spans = tuple(resolver.resolve(sid) for sid in
            dict.fromkeys(sid for n in text_nodes for sid in n.source_span_ids))
        if (len(spans) != 2
            or {s.span_id for s in resolver.resolve_many(resolver.span_ids)
                if s.source_field in {'memo', 'memo_action'}} != {s.span_id for s in spans}
            or any(n.source_fields not in {('memo',), ('memo_action',)}
                or n.surface_anchor_ids != n.source_span_ids
                or n.semantic_frame.target_anchor_ids != n.source_span_ids
                or n.allowed_claim_scope != 'explicit_current_input' for n in text_nodes)
            or any(r.source_span_ids != index[r.from_nucleus_id].source_span_ids
                   or r.source_span_ids != index[r.to_nucleus_id].source_span_ids for r in plan.relations)):
            return False
        if spans[0].source_field == spans[1].source_field:
            a, b = sorted(spans, key=lambda s: s.start_index)
            if not 0 <= a.start_index < a.end_index <= b.start_index < b.end_index:
                return False
        received_text = hr.final_reception_source_anchor_text(received[0][0], index, resolver)
        giver = re.sub(r'^(?:私|自分|わたし)(?:は|が)', '', received_text).rpartition('に')[0]
        if (gp._SELF_REFERENCE_RE.search(giver) is not None
            or 'に' in received_text and not _source_operator_owner_scope_is_bound(received_text)):
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


def _retained_received_experience_source(prepared, plan, resolver):
    """Select the unchanged pair in the one approved separate-field update."""
    import json
    import re
    from dataclasses import asdict, fields
    import emlis_ai_grounded_observation_plan as gp
    from .emlis_answer_update import PreparedEmlisMeaning

    if (type(prepared) is not PreparedEmlisMeaning
        or any(getattr(prepared, f.name) for f in fields(prepared) if f.name.startswith('legacy_'))):
        return None
    thread, original, checkpoint = prepared.thread, prepared.original_plan, prepared.checkpoint
    control = thread.control
    update = checkpoint.answer_update
    if (len(thread.answers) != 1 or len(control.answers) != 1 or control.current_round != 1
        or control.admitted_history or control.rejected_frame_keys or control.frame_feedback_sources
        or checkpoint.assessment_status != 'RESOLVED' or checkpoint.unresolved_parts
        or update is None or update.disposition != 'MATERIAL_UPDATE'
        or update.unresolved_parts or len(update.updates) != 1):
        return None
    links = tuple(edge for edge in original.relations
                  if source_owned_result_appraisal(edge, original.nuclei))
    if len(links) != 1 or not _appraisal_received_components(prepared, original, resolver):
        return None
    link = links[0]
    index = {node.nucleus_id: node for node in original.nuclei}
    event, appraisal = (index[nid] for nid in (link.from_nucleus_id, link.to_nucleus_id))
    reason = source_owned_result_appraisal_reason(link, original.nuclei, original.relations)
    required = tuple(node for node in original.nuclei if node.retention == 'required')
    text = tuple(node for node in original.nuclei
                 if set(node.source_fields) & {'memo', 'memo_action', 'answer_text_private'})
    owned = {event.nucleus_id, appraisal.nucleus_id}
    if reason is not None:
        owned.add(reason.nucleus_id)
    rest = tuple(node for node in required if node.nucleus_id not in owned)
    rest_ids = {node.nucleus_id for node in rest}
    relations = tuple(edge for edge in original.relations
                      if {edge.from_nucleus_id, edge.to_nucleus_id} <= rest_ids)
    received = _received_contrast_group_targets(rest, relations)
    if (len(required) != 4 + int(reason is not None) or text != required
        or set(original.coverage_requirements.required_nucleus_ids) != {n.nucleus_id for n in required}
        or len(original.relations) != 2 + int(reason is not None)
        or len(rest) != 2 or len(relations) != 1 or not received or len(received[0]) != 1
        or (appraisal.semantic_frame.polarity, appraisal.semantic_frame.time_scope) != ('positive', 'past')
        or event.semantic_frame.time_scope != 'past'
        or {code for code in appraisal.semantic_frame.attribute_codes if code.startswith('source_appraisal_')}
            != {'source_appraisal_kind:satisfaction', 'source_appraisal_degree:unmarked'}):
        return None
    received_event, reaction = (index[ids[0]] for ids in received)
    received_relation = relations[0]
    if (event.source_fields == received_event.source_fields
        or received_relation.grounding_kind != 'user_stated_relation'
        or received_relation.source_span_ids != received_event.source_span_ids):
        return None
    for node in required:
        if (node.source_fields not in {('memo',), ('memo_action',)}
            or len(node.source_span_ids) != 1 or node.source_span_ids[0] not in resolver.span_ids
            or node.surface_anchor_ids != node.source_span_ids
            or node.semantic_frame.target_anchor_ids != node.source_span_ids
            or node.grounding_kind != 'explicit' or node.allowed_claim_scope != 'explicit_current_input'
            or node.semantic_frame.actor != 'current_user'):
            return None
    for node in (event, received_event):
        span = resolver.resolve(node.source_span_ids[0])
        source = str(thread.original.normalized_current_input.get(span.source_field) or '')
        if (span.start_index != 0 or span.end_index != len(span.raw_text)
            or re.fullmatch(re.escape(span.raw_text) + r'[。．.]?', source) is None
            or tuple(s.span_id for s in resolver.resolve_many(resolver.span_ids)
                     if s.source_field == span.source_field) != (span.span_id,)):
            return None
    received_text = hr.final_reception_source_anchor_text(received_event.nucleus_id, index, resolver)
    giver = re.sub(r'^(?:私|自分|わたし)(?:は|が)', '', received_text).rpartition('に')[0]
    if (gp._SELF_REFERENCE_RE.search(giver) is not None
        or 'に' in received_text and not _source_operator_owner_scope_is_bound(received_text)):
        return None

    item = update.updates[0]
    dependencies = tuple(edge.relation_id for edge in original.relations
                         if appraisal.nucleus_id in (edge.from_nucleus_id, edge.to_nucleus_id))
    answer_refs = tuple(q.evidence.evidence_id for q in resolver.qualified_refs
                        if q.source_envelope_id == thread.answers[0].envelope.envelope_id)
    if (len(answer_refs) != 1 or item.evidence_refs != answer_refs
        or item.operation not in {'REVISE', 'WITHDRAW'} or item.binding_kind != 'EXPLICIT_CORRECTION'
        or item.target_meaning_refs != (appraisal.nucleus_id,)
        or item.superseded_claim_refs != (appraisal.nucleus_id,)
        or item.affected_dependency_refs != dependencies
        or item.temporal_binding.about_time != 'ORIGINAL_OCCASION'
        or item.temporal_binding.anchor_source_ref != thread.original.envelope.envelope_id
        or checkpoint.accepted_update_refs != (item.update_ref,)
        or checkpoint.inactive_claim_refs != (appraisal.nucleus_id, *dependencies)):
        return None
    current = {node.nucleus_id: node for node in plan.nuclei}
    answers = tuple(node for node in plan.nuclei if node.source_fields == ('answer_text_private',))
    if item.operation == 'REVISE':
        if reason is not None or len(answers) != 1 or len(prepared.accepted_nuclei) != 1:
            return None
        evaluation = answers[0]
        frame = evaluation.semantic_frame
        if (item.changed_claim_refs != (evaluation.nucleus_id,)
            or (evaluation.kind, frame.predicate_kind, frame.modality, frame.polarity,
                frame.time_scope, frame.actor) != ('reaction', 'feeling', 'feeling', 'negative', 'past', 'current_user')
            or evaluation.retention != 'required' or evaluation.grounding_kind != 'explicit'
            or evaluation.allowed_claim_scope != 'explicit_supplemental_answer'
            or {code for code in frame.attribute_codes if code.startswith('thread_time:')}
                != {'thread_time:original_occasion'}
            or {code for code in frame.attribute_codes if code.startswith('source_appraisal_')}
                != {'source_appraisal_kind:satisfaction', 'source_appraisal_degree:unmarked'}):
            return None
    elif item.changed_claim_refs or answers or prepared.accepted_nuclei:
        return None
    if (any(current.get(node.nucleus_id) != node for node in original.nuclei if node != appraisal)
        or appraisal.nucleus_id in current
        or set(current) != ({node.nucleus_id for node in original.nuclei if node != appraisal}
                            | set(item.changed_claim_refs))
        or tuple(edge for edge in plan.relations if edge.relation_id == received_relation.relation_id)
            != (received_relation,)):
        return None
    moves = tuple(move for move in plan.response_plan.human_reception_plan.moves
                  if move.target_nucleus_ids == received[0] and move.support_nucleus_ids == received[1]
                  and move.reception_act == 'stay_with_current_burden' and move.required
                  and move.source_evidence_span_ids == received_event.source_span_ids)
    if len(moves) != 1:
        return None
    return c.RetainedReceivedExperienceEligibilityV1(
        schema_version='cocolon.cmee.retained_received_experience_eligibility.v1',
        source_prefix_ref=thread.source_prefix_ref, checkpoint_ref=checkpoint.checkpoint_id,
        original_source_ref=thread.original.envelope.envelope_id,
        answer_source_ref=thread.answers[0].envelope.envelope_id,
        original_nuclei=tuple(json.dumps(asdict(node), ensure_ascii=False, sort_keys=True,
            separators=(',', ':'), allow_nan=False) for node in required),
        original_relations=tuple(json.dumps(asdict(edge), ensure_ascii=False, sort_keys=True,
            separators=(',', ':'), allow_nan=False) for edge in original.relations),
        update=update, move_ref=moves[0].move_id, thread_control=control)


def _rederive_retained_received_experience_source(control, resolver):
    """Re-admit actual envelopes and replay the existing answer owner only."""
    from dataclasses import fields, is_dataclass
    from emlis_ai_current_input_bundle import build_emlis_current_input_bundle
    from .emlis_thread_contracts import EmlisThreadInputV1
    from .emlis_thread_source import ThreadEvidenceSpanResolver, admit_emlis_thread
    from .source_kernel import _parse_canonical_frame
    from .emlis_question import original_meaning_plan
    from .emlis_answer_update import _prepare_answer, build_updated_grounded_plan

    def immutable(value):
        if value is None or isinstance(value, (str, int, bool)):
            return True
        if type(value) is tuple:
            return all(immutable(child) for child in value)
        return (is_dataclass(value) and value.__dataclass_params__.frozen
                and all(immutable(getattr(value, field.name)) for field in fields(value)))

    failure = 'retained_received_experience_source_invalid'
    if (type(control) is not EmlisThreadInputV1 or not immutable(control)
        or len(control.answers) != 1 or control.current_round != 1
        or control.admitted_history or control.rejected_frame_keys or control.frame_feedback_sources
        or type(resolver) is not ThreadEvidenceSpanResolver or resolver.source_contract != THREAD_SCHEMA):
        raise ValueError(failure)
    envelopes = tuple(resolver._source_envelopes.values())
    original = tuple(row for row in envelopes if row.source_role == 'CURRENT_INPUT')
    if len(envelopes) != 2 or len(original) != 1:
        raise ValueError(failure)
    envelope = original[0]
    snapshot, _ = _parse_canonical_frame(envelope.raw_utf8)
    request = c.GenerationRequest('retained-received-source-replay',
        build_emlis_current_input_bundle(snapshot), envelope.source_record_id, emlis_thread=control)
    thread = admit_emlis_thread(request)
    replay_resolver = thread.resolver()
    if (replay_resolver._source_envelopes != resolver._source_envelopes
        or replay_resolver.span_ids != resolver.span_ids
        or replay_resolver.qualified_refs != resolver.qualified_refs
        or replay_resolver.resolve_many(replay_resolver.span_ids) != resolver.resolve_many(resolver.span_ids)):
        raise ValueError(failure)
    prepared = _prepare_answer(thread, original_meaning_plan(thread))
    return prepared, build_updated_grounded_plan(prepared)


def derive_retained_received_experience_eligibility(prepared, plan, resolver):
    """Return no local qualification for every input outside the approved slice."""
    try:
        eligibility = _retained_received_experience_source(prepared, plan, resolver)
        if eligibility is None:
            return None
        replay, replay_plan = _rederive_retained_received_experience_source(eligibility.thread_control, resolver)
        if replay != prepared or replay_plan != plan:
            return None
        if _retained_received_experience_source(replay, replay_plan, resolver) != eligibility:
            return None
        return eligibility
    except (AttributeError, KeyError, TypeError, ValueError):
        return None


def validate_retained_received_experience_eligibility(eligibility, plan, resolver):
    """Reject re-sealed source claims unless the admitted sources rederive them."""
    failure = 'retained_received_experience_source_invalid'
    try:
        if type(eligibility) is not c.RetainedReceivedExperienceEligibilityV1:
            raise ValueError(failure)
        prepared, replay_plan = _rederive_retained_received_experience_source(eligibility.thread_control, resolver)
        expected = _retained_received_experience_source(prepared, replay_plan, resolver)
        if expected is None or replay_plan != plan or expected != eligibility:
            raise ValueError(failure)
    except (AttributeError, KeyError, TypeError, ValueError):
        raise ValueError(failure) from None


def validate_retained_received_experience_candidate(local, plan, resolver):
    """Rebuild the local relation candidate and contribution from current source.

    This two-node source slice supplies the existing candidate projector only;
    it never replaces the whole graph, meaning outcome or aggregate projection.
    Source/update eligibility is independently validated by the caller.
    """
    failure = 'retained_received_experience_candidate_invalid'
    try:
        if type(local) is not c.RetainedReceivedExperienceContentV1:
            raise ValueError(failure)
        eligibility = local.eligibility
        move, = (move for move in plan.response_plan.human_reception_plan.moves
                 if move.move_id == eligibility.move_ref)
        if len(move.target_nucleus_ids) != 1 or len(move.support_nucleus_ids) != 1:
            raise ValueError(failure)
        endpoints = (*move.target_nucleus_ids, *move.support_nucleus_ids)
        relation, = (edge for edge in plan.relations if edge.type == 'contrast'
                     and (edge.from_nucleus_id, edge.to_nucleus_id) == endpoints)
        index = {node.nucleus_id: node for node in plan.nuclei}
        nodes, node_ids = [], {}
        for nid in endpoints:
            nucleus = index[nid]
            evidence = tuple(resolver.qualified_ref(s).evidence.evidence_id for s in nucleus.source_span_ids)
            node_id = identity('mn', eligibility.checkpoint_ref, nid, evidence)
            node_ids[nid] = node_id
            nodes.append(c.MeaningNode(node_id, identity('owner', node_id), nucleus.kind,
                nucleus.grounding_kind, hr.final_reception_source_anchor_text(nid, index, resolver),
                c.EpistemicState.SOURCE_EXPLICIT, evidence))
        evidence = tuple(resolver.qualified_ref(s).evidence.evidence_id for s in relation.source_span_ids)
        edge_id = identity('me', eligibility.checkpoint_ref, relation.relation_id, evidence)
        edge = c.MeaningEdge(edge_id, identity('owner', edge_id), relation.type,
            node_ids[relation.from_nucleus_id], node_ids[relation.to_nucleus_id],
            relation.grounding_kind, c.EpistemicState.SOURCE_EXPLICIT, evidence)
        source_version = (c.EMLIS_Q3_SOURCE_VERSION
            if eligibility.thread_control.capability_snapshot.startswith('Q3_') else THREAD_SCHEMA)
        owners = tuple(row.owner_id for row in (*nodes, edge))
        dispositions = tuple(c.OwnerDisposition(row.owner_id, c.OwnerClass.REQUIRED,
            c.ResolverResolution.UNIQUE, c.AttachmentAdmission.PROVISIONAL_ONLY,
            c.VisibleAuthority.SOURCE_EXPLICIT, c.SourceOwnerDisposition.SOURCE_EXPLICIT_VISIBLE,
            (row.node_id if type(row) is c.MeaningNode else row.edge_id,), row.evidence_ids,
            None, ('versioned_source_bound',)) for row in (*nodes, edge))
        graph = c.GroundedMeaningGraph(
            identity('retained-received-source-slice', eligibility.checkpoint_ref, endpoints, edge_id),
            eligibility.source_prefix_ref, tuple(nodes), (edge,), dispositions, owners, (),
            source_version, 'cocolon.cmee.emlis_thread_obligations.v1', identity('owner-universe', owners))
        source_order = {node_ids[node.nucleus_id]: i for i, node in enumerate(plan.nuclei)
                        if node.nucleus_id in node_ids}
        source_order[edge_id] = len(plan.nuclei) + plan.relations.index(relation)
        binding = r._PlanBinding({node_ids[nid]: index[nid] for nid in endpoints},
            {edge_id: relation}, node_ids, {relation.relation_id: edge_id},
            frozenset(), frozenset((edge_id,)), source_order)
        schema = c.CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2
        shape = r._relation_shape(edge, {node.node_id: node for node in nodes}, binding,
                                  stage1_response_schema_version=schema)
        if shape is None:
            raise ValueError(failure)
        candidate = r._candidate_from_relation(graph, edge, binding, shape,
                                               stage1_response_schema_version=schema)
        row = r._CandidateRow(candidate, True, True, 'THOUGHT_MEANING',
                              r._retention_rank(relation, required=True), source_order[edge_id])
        # The layer-1 owner consumes only this already-existing duty reference
        # and source version; no new whole parent plan is asserted here.
        duty = SimpleNamespace(source_version=source_version,
            observation_duty_id=identity('observation-duty', eligibility.checkpoint_ref))
        contribution, = r._plan_layer1_observation_from_rows(duty, (row,),
            stage1_response_schema_version=schema)
        if (local.proposition.focal_relation_ref != r._edge_ref(edge_id)
            or local.proposition.response_object_refs != candidate.semantic_refs
            or local.proposition.target_contribution_refs != (contribution.contribution_id,)
            or len(local.basis_rows) != 2 or len(local.qualifier_rows) != 2
            or any(basis.contribution_ref != contribution.contribution_id for basis in local.basis_rows)
            or any(qualifier.source_candidate_ref != candidate.candidate_id for qualifier in local.qualifier_rows)):
            raise ValueError(failure)
    except (AttributeError, KeyError, TypeError, ValueError):
        raise ValueError(failure) from None


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


def _project_thread_meaning_aggregate(prepared, plan) -> ThreadMeaningProjection:
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
    shared_target = source_owned_shared_target_appraisal_contrast(plan.nuclei, plan.relations, resolver)
    if shared_target:
        # The grouped outer edge is not the appraisal itself. Retain its two
        # direct owners so the first Move can receive the person's evaluation
        # without borrowing the received-experience contrast's contribution.
        covered.difference_update(shared_target[key].nucleus_id
                                  for key in ('appraisal_event', 'appraisal'))
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
    eligibility = (derive_retained_received_experience_eligibility(prepared, plan, resolver)
                   if meaning.projection_branch == 'LIMITED' else None)
    if eligibility is not None:
        decision, = (row for row in selected.decisions if row.move_id == eligibility.move_ref)
        local = r.derive_retained_received_experience_content(decision,
            contribution_rows=contributions, candidate_rows=candidates,
            contribution_candidate_map=contribution_map)
        content = composition.project_retained_received_experience_content(
            eligibility, local, decision, selected, meaning)
        carried = hr.SelectedRetainedReceivedExperienceDecisionV1(
            **{name: getattr(decision, name) for name in decision.__dataclass_fields__},
            retained_received_experience=content)
        carried = hr.identify_selected_subjective_reception_decision(carried)
        selected = hr.identify_selected_subjective_reception_input(replace(selected,
            decisions=tuple(carried if row == decision else row for row in selected.decisions)))
        hr.validate_selected_subjective_reception_input(selected, reception, plan, resolver)
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



def _retained_reasoned_add_duties(prepared, plan, resolver):
    """Prove one separate ADD without changing any original source duty."""
    import re
    import emlis_ai_grounded_observation_plan as gp
    original, thread, checkpoint = prepared.original_plan, prepared.thread, prepared.checkpoint
    update = checkpoint.answer_update
    if (len(thread.answers) != 1 or len(thread.control.answers) != 1
        or thread.control.current_round != 1 or checkpoint.assessment_status != 'RESOLVED'
        or checkpoint.unresolved_parts or checkpoint.inactive_claim_refs
        or update is None or update.disposition != 'MATERIAL_UPDATE'
        or update.unresolved_parts or len(update.updates) != 1):
        return ()
    item, = update.updates
    if (item.operation != 'ADD' or item.superseded_claim_refs or item.affected_dependency_refs
        or checkpoint.accepted_update_refs != (item.update_ref,)
        or len(item.changed_claim_refs) != 1):
        return ()
    links = tuple(e for e in original.relations if source_owned_result_appraisal(e, original.nuclei))
    if len(links) != 1:
        return ()
    link, = links
    reason = source_owned_result_appraisal_reason(link, original.nuclei, original.relations)
    index = {n.nucleus_id: n for n in original.nuclei}
    event, evaluation = (index[nid] for nid in (link.from_nucleus_id, link.to_nucleus_id))
    if reason is None:
        return ()
    required = tuple(n for n in original.nuclei if n.retention == 'required')
    required_ids = {n.nucleus_id for n in required}
    owned = {reason.nucleus_id, event.nucleus_id, evaluation.nucleus_id}
    edges = tuple(e for e in original.relations if owned & {e.from_nucleus_id, e.to_nucleus_id})
    rest = tuple(n for n in required if n.nucleus_id not in owned)
    received_edges = tuple(e for e in original.relations if e not in edges)
    received = _received_contrast_group_targets(rest, received_edges)
    if (len(required) != 5 or len(original.relations) != 3 or len(edges) != 2
        or any(not {e.from_nucleus_id, e.to_nucleus_id} <= owned for e in edges)
        or len(rest) != 2 or len(received_edges) != 1 or not received or len(received[0]) != 1
        or {n.nucleus_id for n in original.nuclei if set(n.source_fields)
            & {'memo', 'memo_action', 'answer_text_private'}} != required_ids
        or set(original.coverage_requirements.required_nucleus_ids) != required_ids
        or set(original.coverage_requirements.required_relation_ids)
            != {e.relation_id for e in original.relations}
        or any(n.semantic_frame.actor != 'current_user' or n.grounding_kind != 'explicit'
            or n.source_fields not in {('memo',), ('memo_action',)}
            or len(n.source_span_ids) != 1 or n.source_span_ids[0] not in resolver.span_ids
            or n.surface_anchor_ids != n.source_span_ids
            or n.semantic_frame.target_anchor_ids != n.source_span_ids
            or n.allowed_claim_scope != 'explicit_current_input' for n in required)
        or any(e.retention != 'required' or e.grounding_kind != 'user_stated_relation'
            or e.source_span_ids != index[e.from_nucleus_id].source_span_ids
            or e.source_span_ids != index[e.to_nucleus_id].source_span_ids for e in original.relations)):
        return ()
    spans = tuple(resolver.resolve(sid) for sid in dict.fromkeys(s for n in required for s in n.source_span_ids))
    if (len(spans) != 2 or {s.span_id for s in resolver.resolve_many(resolver.span_ids)
            if s.source_field in {'memo', 'memo_action'}} != {s.span_id for s in spans}
        or any(sum(s.source_field == span.source_field and s.raw_text == span.raw_text
            for s in resolver.resolve_many(resolver.span_ids)) != 1 for span in spans)):
        return ()
    if spans[0].source_field == spans[1].source_field:
        first, last = sorted(spans, key=lambda s: s.start_index)
        if not 0 <= first.start_index < first.end_index <= last.start_index < last.end_index:
            return ()
    received_event = index[received[0][0]]
    received_text = hr.final_reception_source_anchor_text(received_event.nucleus_id, index, resolver)
    giver = re.sub(r'^(?:私|自分|わたし)(?:は|が)', '', received_text).rpartition('に')[0]
    if (gp._SELF_REFERENCE_RE.search(giver) is not None
        or 'に' in received_text and not _source_operator_owner_scope_is_bound(received_text)):
        return ()
    current = {n.nucleus_id: n for n in plan.nuclei}
    answer_id, = item.changed_claim_refs
    answer = current.get(answer_id)
    added_edges = tuple(e for e in plan.relations if e not in original.relations)
    if (len(current) != len(plan.nuclei) or set(current) != set(index) | {answer_id}
        or any(current.get(n.nucleus_id) != n for n in original.nuclei)
        or len(plan.relations) != 4 or len({e.relation_id for e in plan.relations}) != 4
        or not set(original.relations).issubset(plan.relations) or len(added_edges) != 1
        or item.target_meaning_refs != (received_event.nucleus_id,)
        or answer is None or answer.source_fields != ('answer_text_private',)
        or answer.grounding_kind != 'explicit' or answer.retention != 'required'
        or answer.allowed_claim_scope != 'explicit_supplemental_answer'
        or answer.semantic_frame.actor != 'current_user' or len(answer.source_span_ids) != 1
        or answer.surface_anchor_ids != answer.source_span_ids
        or answer.semantic_frame.target_anchor_ids != answer.source_span_ids
        or 'thread_subject:unique_source_clause' not in answer.semantic_frame.attribute_codes
        or {n.nucleus_id for n in plan.nuclei if n.retention == 'required'} != required_ids | {answer_id}
        or set(plan.coverage_requirements.required_nucleus_ids) != required_ids | {answer_id}
        or set(plan.coverage_requirements.required_relation_ids) != {e.relation_id for e in plan.relations}):
        return ()
    frame = answer.semantic_frame
    positive = gp.is_grounded_positive_feeling(answer)
    negative = ((answer.kind, frame.predicate_kind, frame.modality, frame.polarity)
        == ('reaction', 'feeling', 'feeling', 'negative') and not gp.is_grounded_current_answer_uncertainty(answer))
    times = {code for code in frame.attribute_codes if code.startswith('thread_time:')}
    current_time = frame.time_scope == 'present' and times == {'thread_time:answer_time'}
    original_time = frame.time_scope == 'past' and times == {'thread_time:original_occasion'}
    temporal = item.temporal_binding
    evidence = tuple(q.evidence.evidence_id for q in resolver.qualified_refs
        if q.source_envelope_id == thread.answers[0].envelope.envelope_id)
    if (not (positive or negative) or not (current_time or original_time)
        or len(evidence) != 1 or item.evidence_refs != evidence
        or temporal.time_expression_evidence_refs != evidence
        or temporal.anchor_source_ref != thread.original.envelope.envelope_id
        or temporal.resolved_interval is not None or temporal.timezone_basis is not None
        or (item.binding_kind, temporal.about_time, temporal.relative_relation) != (
            ('SAME_OCCASION_CURRENT_STATE', 'ANSWER_TIME', 'answer_deictic_now') if current_time
            else ('QUESTION_FOCUS', 'ORIGINAL_OCCASION', None))):
        return ()
    about, = added_edges
    if (about.type != 'evaluation_about_event' or about.retention != 'required'
        or (about.from_nucleus_id, about.to_nucleus_id) != (received_event.nucleus_id, answer_id)
        or about.grounding_kind != 'user_stated_relation' or about.source_relation_ids != (item.update_ref,)
        or set(about.source_span_ids) != set(received_event.source_span_ids + answer.source_span_ids)):
        return ()
    duties = (('lived_change', (evaluation.nucleus_id,), (reason.nucleus_id, event.nucleus_id)),
              ('current_burden', received[0], received[1] + (() if positive else (answer_id,))))
    if positive:
        duties += (('lived_change', (answer_id,), ()),)
    acts = {'lived_change': 'recognize_lived_change', 'current_burden': 'stay_with_current_burden'}
    expected_moves = tuple((acts[family], targets, supports,
        tuple(dict.fromkeys(s for nid in (*targets, *supports) for s in current[nid].source_span_ids)))
        for family, targets, supports in duties)
    moves = plan.response_plan.human_reception_plan.moves
    if (_thread_retained_reaction_groups(plan.nuclei, plan.relations) != duties
        or any(not m.required for m in moves)
        or tuple((m.reception_act, m.target_nucleus_ids, m.support_nucleus_ids, m.source_evidence_span_ids)
                 for m in moves) != expected_moves):
        return ()
    return duties


def _retained_reasoned_experience_source(prepared, plan, resolver):
    """Qualify the unchanged triple after one separate revision or bounded ADD."""
    import json
    from dataclasses import asdict, fields
    from .emlis_answer_update import PreparedEmlisMeaning, _retained_unfinished_received_duties
    if (type(prepared) is not PreparedEmlisMeaning
        or any(getattr(prepared, f.name) for f in fields(prepared) if f.name.startswith('legacy_'))):
        return None
    thread, original, checkpoint = prepared.thread, prepared.original_plan, prepared.checkpoint
    control = thread.control
    if control.admitted_history or control.rejected_frame_keys or control.frame_feedback_sources:
        return None
    duties = (_retained_unfinished_received_duties(prepared, plan.nuclei, plan.relations)
              or _retained_reasoned_add_duties(prepared, plan, resolver))
    if not duties:
        return None
    links = tuple(edge for edge in original.relations if source_owned_result_appraisal(edge, original.nuclei))
    if len(links) != 1:
        return None
    link, = links
    reason = source_owned_result_appraisal_reason(link, original.nuclei, original.relations)
    index = {n.nucleus_id: n for n in original.nuclei}
    event, evaluation = (index[nid] for nid in (link.from_nucleus_id, link.to_nucleus_id))
    required = tuple(n for n in original.nuclei if n.retention == 'required')
    if (reason is None or len(required) != 5 or len(original.relations) != 3
        or any(n.semantic_frame.actor != 'current_user' or n.grounding_kind != 'explicit' for n in required)):
        return None
    item, = checkpoint.answer_update.updates
    answers = tuple(n for n in plan.nuclei if n.source_fields == ('answer_text_private',))
    evidence = tuple(q.evidence.evidence_id for q in resolver.qualified_refs
                     if q.source_envelope_id == thread.answers[0].envelope.envelope_id)
    if (len(evidence) != 1 or item.evidence_refs != evidence or len(answers) != 1
        or tuple(n.nucleus_id for n in prepared.accepted_nuclei) != item.changed_claim_refs):
        return None
    moves = plan.response_plan.human_reception_plan.moves
    matches = tuple(m for m in moves if m.target_nucleus_ids == (evaluation.nucleus_id,)
                    and m.support_nucleus_ids == (reason.nucleus_id, event.nucleus_id)
                    and m.reception_act == 'recognize_lived_change' and m.required)
    if len(moves) != len(duties) or len(matches) != 1:
        return None
    return c.RetainedReasonedExperienceEligibilityV1(
        'cocolon.cmee.retained_reasoned_experience_eligibility.v1',
        thread.source_prefix_ref, checkpoint.checkpoint_id, thread.original.envelope.envelope_id,
        thread.answers[0].envelope.envelope_id,
        tuple(json.dumps(asdict(n), ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)
              for n in required),
        tuple(json.dumps(asdict(e), ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)
              for e in original.relations), checkpoint.answer_update, matches[0].move_id, control)


def derive_retained_reasoned_experience_eligibility(prepared, plan, resolver):
    try:
        eligibility = _retained_reasoned_experience_source(prepared, plan, resolver)
        if eligibility is None:
            return None
        replay, replay_plan = _rederive_retained_received_experience_source(eligibility.thread_control, resolver)
        if (replay != prepared or replay_plan != plan
            or _retained_reasoned_experience_source(replay, replay_plan, resolver) != eligibility):
            return None
        return eligibility
    except (AttributeError, KeyError, TypeError, ValueError):
        return None


def _carry_retained_reasoned_experience(projection, eligibility):
    selected = projection.selected_reception
    decision, = (d for d in selected.decisions if d.move_id == eligibility.move_ref)
    local = r.derive_retained_reasoned_experience_content(decision, projection.premeaning)
    content = composition.project_retained_reasoned_experience_content(
        eligibility, local, decision, selected, projection.meaning_plan)
    carried = hr.SelectedRetainedReasonedExperienceDecisionV1(
        **{name: getattr(decision, name) for name in hr.SelectedSubjectiveReceptionDecisionV1.__dataclass_fields__},
        retained_reasoned_experience=content)
    carried = hr.identify_selected_subjective_reception_decision(carried)
    return hr.identify_selected_subjective_reception_input(replace(selected,
        decisions=tuple(carried if row == decision else row for row in selected.decisions)))


def validate_retained_reasoned_experience_source(decision, selected, plan, resolver):
    """Rebuild the original source, accepted update and unchanged whole projection.

    The aggregate projector never attaches this new carrier. Comparing the
    entire rebuilt selection also rejects re-sealed foreign Move/aggregate IDs.
    """
    fail = 'retained_reasoned_experience_source_invalid'
    try:
        local = decision.retained_reasoned_experience
        c.validate_retained_reasoned_experience_content(local, decision, selected)
        prepared, replay_plan = _rederive_retained_received_experience_source(local.eligibility.thread_control, resolver)
        expected = _retained_reasoned_experience_source(prepared, replay_plan, resolver)
        if expected is None or replay_plan != plan or expected != local.eligibility:
            raise ValueError(fail)
        projection = _project_thread_meaning_aggregate(prepared, replay_plan)
        if _carry_retained_reasoned_experience(projection, expected) != selected:
            raise ValueError(fail)
    except (AttributeError, KeyError, TypeError, ValueError):
        raise ValueError(fail) from None


def project_thread_meaning(prepared, plan) -> ThreadMeaningProjection:
    projection = _project_thread_meaning_aggregate(prepared, plan)
    if projection.meaning_plan.projection_branch != 'LIMITED':
        return projection
    resolver = prepared.thread.resolver()
    eligibility = derive_retained_reasoned_experience_eligibility(prepared, plan, resolver)
    if eligibility is None:
        return projection
    selected = _carry_retained_reasoned_experience(projection, eligibility)
    hr.validate_selected_subjective_reception_input(selected, plan.response_plan.human_reception_plan, plan, resolver)
    return replace(projection, selected_reception=selected)
