"""The additional received duty is owned by the complete approved source only."""
from dataclasses import replace

import pytest
import emlis_ai_grounded_observation_plan as observation
from cocolon_meaning_experience_engine.emlis_question import original_meaning_plan
from cocolon_meaning_experience_engine.emlis_thread_source import admit_emlis_thread
from test_cmee_emlis_q3_thread import begin

BASE = '友達からの誘いを断って、一人で休めたことにほっとした。でも、もう誘ってもらえなくなるかもしれないと思うと寂しい。'
RECEIVED = '褒められたのに、嬉しくなかった。'
UNKNOWN = '何が不安なのか、私にもまだわからない。'
WITNESS = 'source_relief_received_retention:v1'


def _original(memo):
    thread = admit_emlis_thread(begin(memo))
    return thread, original_meaning_plan(thread)


def _qualify(thread, plan, *, nuclei=None, relations=None, spans=None,
             normalized=None, require_witness=True):
    return observation._source_relief_received_group(
        plan.nuclei if nuclei is None else nuclei,
        plan.relations if relations is None else relations,
        thread.original.evidence_spans if spans is None else spans,
        thread.original.normalized_current_input if normalized is None else normalized,
        require_witness=require_witness)


@pytest.fixture(scope='module', params=[False, True], ids=['without_unknown', 'with_unknown'])
def qualified_source(request):
    thread, plan = _original(BASE + RECEIVED + (UNKNOWN if request.param else ''))
    group = _qualify(thread, plan)
    assert len(group) == 7
    return thread, plan, group


def _replace_member(members, old, new):
    assert old in members and new != old
    return tuple(new if member == old else member for member in members)


def _attributes(nucleus, prefix, replacement):
    frame = nucleus.semantic_frame
    old = tuple(code for code in frame.attribute_codes if code.startswith(prefix))
    assert old and old != replacement
    codes = tuple(code for code in frame.attribute_codes if not code.startswith(prefix))
    return replace(nucleus, semantic_frame=replace(frame, attribute_codes=codes + replacement))


def test_full_original_selects_pair_and_received_as_independent_duties(qualified_source):
    thread, plan, group = qualified_source
    unknown, left, right, event, reaction, contrast, received_edge = group
    assert observation._source_relief_received_from_resolver(
        plan.nuclei, plan.relations, thread.resolver()) == group
    assert {contrast.from_nucleus_id, contrast.to_nucleus_id} == {left.nucleus_id, right.nucleus_id}
    assert (received_edge.from_nucleus_id, received_edge.to_nucleus_id) == (event.nucleus_id, reaction.nucleus_id)
    moves = plan.response_plan.human_reception_plan.moves
    assert len(moves) == 2 + bool(unknown)
    groups = [{ref for ref in (*move.target_nucleus_ids, *move.support_nucleus_ids)}
              for move in moves]
    assert groups[:2] == [{left.nucleus_id, right.nucleus_id}, {event.nucleus_id, reaction.nucleus_id}]
    if unknown:
        assert groups[2] == {unknown.nucleus_id}
        assert moves[2].move_role == 'felt_response'


@pytest.mark.parametrize('mutation', [
    'event_actor', 'event_time', 'reaction_polarity', 'reaction_retention',
    'event_scalar', 'reaction_link', 'event_raw_span', 'source_reinterpreted',
    'received_edge', 'cross_edge', 'extra_span', 'missing_witness', 'wrong_witness',
])
def test_source_and_typed_changes_cannot_keep_received_qualification(qualified_source, mutation):
    thread, plan, group = qualified_source
    unknown, left, right, event, reaction, contrast, received_edge = group
    nuclei, relations = plan.nuclei, plan.relations
    spans = thread.original.evidence_spans
    normalized = thread.original.normalized_current_input
    old = changed = None
    if mutation == 'event_actor':
        old, changed = event, replace(event, semantic_frame=replace(event.semantic_frame, actor='other_person'))
    elif mutation == 'event_time':
        old, changed = event, replace(event, semantic_frame=replace(event.semantic_frame, time_scope='current'))
    elif mutation == 'reaction_polarity':
        old, changed = reaction, replace(reaction, semantic_frame=replace(reaction.semantic_frame, polarity='positive'))
    elif mutation == 'reaction_retention':
        old, changed = reaction, replace(reaction, retention='optional')
    elif mutation == 'event_scalar':
        old, changed = event, _attributes(event, 'source_fragment_scalar_range:', ('source_fragment_scalar_range:1:5',))
    elif mutation == 'reaction_link':
        old, changed = reaction, _attributes(reaction, 'source_received_event_link:', ('source_received_event_link:forged',))
    elif mutation == 'event_raw_span':
        span = next(s for s in spans if s.span_id == event.source_span_ids[0])
        spans = _replace_member(spans, span, replace(span, raw_text=span.raw_text.replace('嬉', '悲')))
    elif mutation == 'source_reinterpreted':
        span = next(s for s in spans if s.span_id == event.source_span_ids[0])
        replacement = span.raw_text.replace('褒められた', '褒められる')
        assert len(replacement) == len(span.raw_text)
        spans = _replace_member(spans, span, replace(span, raw_text=replacement))
        normalized = dict(normalized, memo=normalized['memo'].replace(span.raw_text, replacement))
    elif mutation == 'received_edge':
        relations = _replace_member(relations, received_edge, replace(received_edge,
            from_nucleus_id=reaction.nucleus_id, to_nucleus_id=event.nucleus_id))
    elif mutation == 'cross_edge':
        relations = (*relations, replace(received_edge, relation_id='injected:cross',
            from_nucleus_id=right.nucleus_id, to_nucleus_id=event.nucleus_id,
            source_span_ids=(*right.source_span_ids, *event.source_span_ids)))
    elif mutation == 'extra_span':
        span = next(s for s in spans if s.span_id == event.source_span_ids[0])
        spans = (*spans, replace(span, span_id='forged:unaccounted-source'))
    else:
        old, changed = left, _attributes(left, 'source_relief_received_retention:',
            () if mutation == 'missing_witness' else ('source_relief_received_retention:v2',))
    if old is not None:
        nuclei = _replace_member(nuclei, old, changed)
    assert _qualify(thread, plan, nuclei=nuclei, relations=relations,
        spans=spans, normalized=normalized) == ()


def test_u348_legacy_source_keeps_its_old_selection_without_new_witness(qualified_source):
    thread, _, group = qualified_source
    legacy = original_meaning_plan(thread, _legacy_relief_received_retention=True)
    assert not any(WITNESS in n.semantic_frame.attribute_codes for n in legacy.nuclei)
    assert _qualify(thread, legacy) == ()
    assert len(_qualify(thread, legacy, require_witness=False)) == 7
    unknown, left, right, event, reaction, *_ = group
    moves = legacy.response_plan.human_reception_plan.moves
    assert len(moves) == 1 + bool(unknown)
    selected = {ref for move in moves for ref in (*move.target_nucleus_ids, *move.support_nucleus_ids)}
    assert selected == {left.nucleus_id, right.nucleus_id} | ({unknown.nucleus_id} if unknown else set())
    assert selected.isdisjoint({event.nucleus_id, reaction.nucleus_id})


@pytest.mark.parametrize('memo', [BASE, BASE + UNKNOWN, RECEIVED])
def test_witness_injection_cannot_supply_the_missing_experience(memo):
    thread, plan = _original(memo)
    assert _qualify(thread, plan, require_witness=False) == ()
    first = next(n for n in plan.nuclei if n.retention == 'required' and n.source_fields == ('memo',))
    forged = replace(first, semantic_frame=replace(first.semantic_frame,
        attribute_codes=(*first.semantic_frame.attribute_codes, WITNESS)))
    assert _qualify(thread, plan, nuclei=_replace_member(plan.nuclei, first, forged)) == ()


@pytest.fixture(scope='module', params=['base_unknown', 'withdraw_reaction_unknown'])
def selected_context(request):
    from test_cmee_emlis_relief_received import actual_context
    return actual_context('initial' if request.param == 'base_unknown' else request.param)


@pytest.mark.parametrize('mutation', ['checkpoint', 'operation', 'event',
                                      'received_move', 'unknown',
                                      'borrowed_contributions', 'erase_received'])
def test_resealed_private_content_cannot_change_ownership_or_erase_received_duty(selected_context, mutation):
    import emlis_ai_grounded_human_reception as hr
    from cocolon_meaning_experience_engine import contracts as c
    from cocolon_meaning_experience_engine.emlis_thread_projection import validate_retained_relief_received_source
    _, plan, _, resolver, selected = selected_context
    pair, received, unknown = selected.decisions
    local = pair.retained_relief_received
    eligibility = local.eligibility
    decisions = selected.decisions
    if mutation == 'checkpoint':
        local = replace(local, eligibility=replace(eligibility, checkpoint_ref='forged'))
    elif mutation == 'operation':
        local = replace(local, eligibility=replace(eligibility,
            operation='ADD' if eligibility.operation == 'INITIAL' else 'INITIAL'))
    elif mutation == 'event':
        local = replace(local, eligibility=replace(eligibility,
            received_event_ref=eligibility.relief_nucleus_ref))
    elif mutation == 'received_move':
        local = replace(local, eligibility=replace(eligibility, received_move_ref=unknown.move_id))
    elif mutation == 'unknown':
        local = replace(local, eligibility=replace(eligibility, unknown_nucleus_ref=None))
    elif mutation == 'borrowed_contributions':
        decisions = (pair, replace(received, selected_contribution_refs=pair.selected_contribution_refs), unknown)
    else:
        decisions = (pair, unknown)
    local = replace(local, seal_ref=c.retained_relief_received_seal(local))
    forged = hr.identify_selected_subjective_reception_decision(replace(pair,
        retained_relief_received=local))
    altered = hr.identify_selected_subjective_reception_input(replace(selected,
        decisions=(forged, *decisions[1:])))
    with pytest.raises((ValueError, c.CMEEStage1ContractError)):
        validate_retained_relief_received_source(forged, altered, plan, resolver)


@pytest.mark.parametrize('mutation', ['drop_original_experience', 'drop_original_reaction',
                                      'drop_answer', 'drop_answer_relation'])
def test_three_endpoint_add_cannot_be_resealed_as_an_old_two_endpoint_experience(mutation):
    import emlis_ai_grounded_human_reception as hr
    from cocolon_meaning_experience_engine import contracts as c
    from cocolon_meaning_experience_engine.emlis_thread_projection import validate_retained_relief_received_source
    from test_cmee_emlis_relief_received import actual_context
    _, plan, _, resolver, selected = actual_context('add_unknown')
    pair, received, unknown = selected.decisions
    local = received.retained_relief_received
    assert local.eligibility.operation == 'ADD'
    assert local.event_ref and local.reaction_ref and local.answer_ref
    assert len(local.relation_refs) == 2 and local.original_proposition is not None
    if mutation == 'drop_original_experience':
        local = replace(local, original_proposition=None)
    elif mutation == 'drop_original_reaction':
        local = replace(local, reaction_ref=None)
    elif mutation == 'drop_answer':
        local = replace(local, answer_ref=None)
    else:
        local = replace(local, relation_refs=local.relation_refs[:1])
    local = replace(local, seal_ref=c.retained_relief_received_seal(local))
    forged = hr.identify_selected_subjective_reception_decision(replace(received,
        retained_relief_received=local))
    altered = hr.identify_selected_subjective_reception_input(replace(selected,
        decisions=(pair, forged, unknown)))
    with pytest.raises((ValueError, c.CMEEStage1ContractError)):
        validate_retained_relief_received_source(forged, altered, plan, resolver)
