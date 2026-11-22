"""The mixed unknown witness is earned by the complete original source.

These synthetic cases exercise source qualification directly, without body
generation. Five required source nuclei select only the pair and the unknown
for the initial Reception; the received experience stays in Observation.
"""

from dataclasses import replace

import pytest

from emlis_ai_current_input_bundle import build_emlis_current_input_bundle
import emlis_ai_grounded_observation_plan as observation
from cocolon_meaning_experience_engine.contracts import GenerationRequest
from cocolon_meaning_experience_engine.emlis_question import original_meaning_plan, question_candidate
from cocolon_meaning_experience_engine.emlis_thread_contracts import (
    EmlisQuestionControlV1,
    EmlisThreadInputV1,
    SupplementalAnswerSource,
)
from cocolon_meaning_experience_engine.emlis_thread_source import (
    admit_emlis_thread,
    freeze_supplemental_answer,
)
from cocolon_meaning_experience_engine.source_kernel import freeze_text_source


BASE = '友達からの誘いを断って、一人で休めたことにほっとした。でも、もう誘ってもらえなくなるかもしれないと思うと寂しい。'
RECEIVED = '褒められたのに、嬉しくなかった。'
UNKNOWN = '何が不安なのか、私にもまだわからない。'
MEMO = BASE + RECEIVED + UNKNOWN
WITNESS = 'source_mixed_relief_unknown_retention:v1'


def _request(memo):
    raw = dict(id='mixed-unknown-source', created_at='2026-10-18T00:00:00Z',
        memo=memo, memo_action='', category=['仕事'], emotions=['不安'],
        emotion_details=[dict(type='不安', strength='medium')], is_secret=False)
    request = GenerationRequest('mixed-unknown-source',
        build_emlis_current_input_bundle(raw), 'mixed-unknown-source')
    source = freeze_text_source(request)
    return replace(request, emlis_thread=EmlisThreadInputV1(
        'mixed-unknown-thread', source.envelope.envelope_id,
        capability_snapshot='Q3_PREMIUM',
        question_control_context=EmlisQuestionControlV1(question_limit=3)))


def _original(memo):
    thread = admit_emlis_thread(_request(memo))
    return thread, original_meaning_plan(thread)


def _qualify(thread, plan, *, nuclei=None, relations=None, spans=None,
             normalized=None, require_witness=True):
    return observation._source_mixed_relief_unknown_group(
        plan.nuclei if nuclei is None else nuclei,
        plan.relations if relations is None else relations,
        thread.original.evidence_spans if spans is None else spans,
        thread.original.normalized_current_input if normalized is None else normalized,
        require_witness=require_witness)


@pytest.fixture(scope='module')
def qualified_source():
    thread, plan = _original(MEMO)
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


def test_original_source_qualifies_without_selecting_received_reception(qualified_source):
    thread, plan, group = qualified_source
    unknown, left, right, event, reaction, contrast, received_edge = group
    assert observation._source_mixed_relief_unknown_from_resolver(
        plan.nuclei, plan.relations, thread.resolver()) == group
    assert observation._source_relief_cognition_unknown_from_resolver(
        plan.nuclei, plan.relations, thread.resolver()) == group[:3]
    assert all(n.retention == 'required' for n in group[:5])
    assert {contrast.from_nucleus_id, contrast.to_nucleus_id} == {
        left.nucleus_id, right.nucleus_id}
    assert (received_edge.from_nucleus_id, received_edge.to_nucleus_id) == (
        event.nucleus_id, reaction.nucleus_id)
    moves = plan.response_plan.human_reception_plan.moves
    selected = {ref for move in moves
                for ref in (*move.target_nucleus_ids, *move.support_nucleus_ids)}
    assert len(moves) == 2
    assert selected == {unknown.nucleus_id, left.nucleus_id, right.nucleus_id}
    assert selected.isdisjoint({event.nucleus_id, reaction.nucleus_id})


@pytest.mark.parametrize('mutation', [
    'unknown_actor', 'unknown_time', 'unknown_anchor', 'unknown_retention',
    'unknown_raw_span', 'received_scalar', 'received_link', 'received_type',
    'received_polarity', 'received_raw_span', 'unknown_optional_link',
    'unknown_required_link', 'pair_received_cross_edge', 'witness_missing',
    'witness_version', 'received_source_reinterpreted',
])
def test_typed_or_source_mutation_cannot_keep_mixed_qualification(qualified_source, mutation):
    thread, plan, group = qualified_source
    unknown, left, right, event, reaction, contrast, received_edge = group
    nuclei, relations = plan.nuclei, plan.relations
    spans = thread.original.evidence_spans
    normalized = thread.original.normalized_current_input
    old = changed = None
    if mutation == 'unknown_actor':
        old, changed = unknown, replace(unknown, semantic_frame=replace(
            unknown.semantic_frame, actor='other_person'))
    elif mutation == 'unknown_time':
        old, changed = unknown, replace(unknown, semantic_frame=replace(
            unknown.semantic_frame, time_scope='past'))
    elif mutation == 'unknown_anchor':
        old, changed = unknown, replace(unknown, semantic_frame=replace(
            unknown.semantic_frame, target_anchor_ids=event.source_span_ids))
    elif mutation == 'unknown_retention':
        old, changed = unknown, replace(unknown, retention='optional')
    elif mutation in {'unknown_raw_span', 'received_raw_span'}:
        span_id = (unknown if mutation == 'unknown_raw_span' else event).source_span_ids[0]
        span = next(s for s in spans if s.span_id == span_id)
        replacement = span.raw_text.replace('不安', '不満') if mutation == 'unknown_raw_span' else span.raw_text.replace('嬉', '悲')
        spans = _replace_member(spans, span, replace(span, raw_text=replacement))
    elif mutation == 'received_scalar':
        old, changed = event, _attributes(event, 'source_fragment_scalar_range:',
            ('source_fragment_scalar_range:1:5',))
    elif mutation == 'received_link':
        old, changed = reaction, _attributes(reaction, 'source_received_event_link:',
            ('source_received_event_link:node',))
    elif mutation == 'received_type':
        old, changed = event, replace(event, kind='action')
    elif mutation == 'received_polarity':
        old, changed = reaction, replace(reaction, semantic_frame=replace(
            reaction.semantic_frame, polarity='positive'))
    elif mutation in {'unknown_optional_link', 'unknown_required_link', 'pair_received_cross_edge'}:
        origin = left if mutation == 'pair_received_cross_edge' else unknown
        edge = replace(received_edge, relation_id='relation:injected',
            type='uncertain_connection', from_nucleus_id=origin.nucleus_id,
            to_nucleus_id=event.nucleus_id,
            source_span_ids=origin.source_span_ids + event.source_span_ids,
            grounding_kind='bounded_structural_inference',
            retention='optional' if mutation == 'unknown_optional_link' else 'required')
        relations = (*relations, edge)
    elif mutation in {'witness_missing', 'witness_version'}:
        replacement = () if mutation == 'witness_missing' else (
            'source_mixed_relief_unknown_retention:v2',)
        old, changed = unknown, _attributes(unknown,
            'source_mixed_relief_unknown_retention:', replacement)
    elif mutation == 'received_source_reinterpreted':
        # Keep the raw text/span alignment valid while changing the received
        # event's time and modality. Existing typed labels cannot supply proof.
        span = next(s for s in spans if s.span_id == event.source_span_ids[0])
        replacement = span.raw_text.replace('褒められた', '褒められる')
        assert len(replacement) == len(span.raw_text)
        spans = _replace_member(spans, span, replace(span, raw_text=replacement))
        normalized = dict(normalized, memo=normalized['memo'].replace(span.raw_text, replacement))
    else:
        raise AssertionError(mutation)
    if old is not None:
        nuclei = _replace_member(nuclei, old, changed)
    assert (nuclei, relations, spans, normalized) != (
        plan.nuclei, plan.relations, thread.original.evidence_spans,
        thread.original.normalized_current_input)
    assert _qualify(thread, plan, nuclei=nuclei, relations=relations,
        spans=spans, normalized=normalized) == ()


@pytest.mark.parametrize('memo', [
    BASE + RECEIVED + 'なぜ不安なのか、私にもまだわからない。',
    BASE + RECEIVED + UNKNOWN.replace('わからない', 'わからなかった'),
    UNKNOWN + BASE + RECEIVED,
    BASE + RECEIVED + UNKNOWN.replace('私にも', '友達にも'),
    BASE + RECEIVED + '誘われたのに、悲しかった。' + UNKNOWN,
    BASE + '私に褒められたのに、嬉しくなかった。' + UNKNOWN,
], ids=['cause', 'past', 'preposed', 'third_party', 'additional_received', 'self_giver'])
def test_source_outside_approved_order_and_scope_cannot_earn_witness(memo):
    thread, plan = _original(memo)
    assert not any(WITNESS in n.semantic_frame.attribute_codes for n in plan.nuclei)
    assert _qualify(thread, plan, require_witness=False) == ()


def test_witness_injection_alone_cannot_turn_the_old_pair_unknown_into_mixed_source():
    thread, plan = _original(BASE + UNKNOWN)
    unknowns = tuple(n for n in plan.nuclei if n.kind == 'uncertainty')
    assert len(unknowns) == 1
    unknown, = unknowns
    assert WITNESS not in unknown.semantic_frame.attribute_codes
    forged = replace(unknown, semantic_frame=replace(unknown.semantic_frame,
        attribute_codes=(*unknown.semantic_frame.attribute_codes, WITNESS)))
    assert _qualify(thread, plan,
        nuclei=_replace_member(plan.nuclei, unknown, forged)) == ()


def test_legacy_original_keeps_pair_reception_without_new_unknown_witness(qualified_source):
    thread, _, group = qualified_source
    legacy = original_meaning_plan(thread, _legacy_mixed_relief_unknown=True)
    assert not any(WITNESS in n.semantic_frame.attribute_codes for n in legacy.nuclei)
    assert _qualify(thread, legacy) == ()
    assert len(_qualify(thread, legacy, require_witness=False)) == 7
    moves = legacy.response_plan.human_reception_plan.moves
    assert len(moves) == 1
    assert {ref for move in moves for ref in (
        *move.target_nucleus_ids, *move.support_nucleus_ids)} == {
            group[1].nucleus_id, group[2].nucleus_id}


@pytest.fixture(scope='module')
def prepared_one_answer():
    from cocolon_meaning_experience_engine.emlis_answer_update import (
        prepare_emlis_meaning, build_updated_grounded_plan,
        _retained_unchanged_relief_cognition_duties,
    )
    request = _request(MEMO)
    thread = admit_emlis_thread(request)
    decision, question = question_candidate(thread, original_meaning_plan(thread),
        parent_request_id=request.request_id)
    assert question is not None
    answer = SupplementalAnswerSource('mixed-unknown-answer-1',
        thread.control.thread_id, question.question_id, 1,
        thread.control.original_source_ref, '今は嬉しい。', '2026-10-18T01:00:00Z')
    control = replace(thread.control.question_control_context, pending_question=question,
        asked_target_refs=(decision.target_ref,), issued_count=1, issued_questions=(question,))
    request = replace(request, emlis_thread=replace(thread.control, answers=(answer,),
        current_round=1, question_control_context=control))
    prepared = prepare_emlis_meaning(request)
    plan = build_updated_grounded_plan(prepared)
    assert len(_retained_unchanged_relief_cognition_duties(
        prepared, plan.nuclei, plan.relations)) == 3
    assert len(observation._source_retained_mixed_unknown_from_resolver(
        plan.nuclei, plan.relations, prepared.thread.resolver())) == 3
    return prepared, plan


@pytest.mark.parametrize('owner', ['admitted', 'control', 'both'])
def test_extra_answer_cannot_reuse_the_one_update_qualification(prepared_one_answer, owner):
    from cocolon_meaning_experience_engine.emlis_answer_update import (
        _unchanged_relief_cognition_update_source, _retained_unchanged_relief_cognition_duties,
    )
    from cocolon_meaning_experience_engine.emlis_thread_projection import (
        _retained_updated_relief_cognition_eligibility,
    )
    prepared, plan = prepared_one_answer
    thread = prepared.thread
    # Inject a second answer at the immutable admitted/prepared boundary.
    # Its source bytes are valid, but no second question is invented or issued.
    extra = replace(thread.answers[0].source, answer_id='mixed-unknown-extra-answer',
        round_index=2, answer_text_private='その時は重かった。', recorded_at='2026-10-18T02:00:00Z')
    if owner in {'admitted', 'both'}:
        thread = replace(thread, answers=(*thread.answers, freeze_supplemental_answer(extra)))
    if owner in {'control', 'both'}:
        thread = replace(thread, control=replace(thread.control,
            answers=(*thread.control.answers, extra), current_round=2))
    assert thread.control.question_control_context == prepared.thread.control.question_control_context
    forged = replace(prepared, thread=thread)
    resolver = thread.resolver()
    assert _unchanged_relief_cognition_update_source(forged) is None
    assert _retained_unchanged_relief_cognition_duties(forged, plan.nuclei, plan.relations) == ()
    assert _retained_updated_relief_cognition_eligibility(forged, plan, resolver) is None
    if owner in {'admitted', 'both'}:
        assert observation._source_retained_mixed_unknown_from_resolver(
            plan.nuclei, plan.relations, resolver) == ()
