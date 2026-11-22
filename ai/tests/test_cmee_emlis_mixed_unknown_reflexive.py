"""Existing reflexive SELF grammar inside the complete five-owner source."""
from dataclasses import replace
from functools import lru_cache
import json
from pathlib import Path

import pytest

import emlis_ai_grounded_observation_plan as observation
from cocolon_meaning_experience_engine import MeaningExperienceEngine, contracts
from cocolon_meaning_experience_engine import emlis_answer_update as update
from cocolon_meaning_experience_engine.emlis_question import original_meaning_plan
from cocolon_meaning_experience_engine.emlis_thread_contracts import SupplementalAnswerSource
from cocolon_meaning_experience_engine.emlis_thread_projection import project_thread_meaning
from test_cmee_emlis_mixed_unknown import checkpoint, full_snapshot
from test_cmee_emlis_q1_thread import initial
from test_cmee_emlis_q3_thread import begin


BASELINE = json.loads((Path(__file__).parent /
    'fixtures/cmee_emlis_u347_mixed_unknown_reflexive_v1.json').read_text())
MEMO = BASELINE['memo']
UNKNOWN = '何が不安なのか、自分でもまだわからない'
WITNESS = 'source_mixed_relief_unknown_retention:v1'
PAIR_OBSERVATION = ('「友達からの誘いを断って、一人で休めたことにほっとした」の一方で'
    '「もう誘ってもらえなくなるかもしれないと思うと寂しい」とあります。')
PAIR_RECEPTION = ('ほっとしたと聞いて、私も少し安心しましたが、'
    'その寂しさにも、今、耳を傾けていたいです。')
UNKNOWN_RECEPTION = '何が不安なのか、ご自身でもまだわからないのですね。'
QUESTION = '「褒められた」は、あなたにはどんな意味として届きましたか。'


@lru_cache(None)
def current(profile, stage):
    engine = MeaningExperienceEngine()
    if stage == 'initial':
        request = (initial if profile == 'q1' else begin)(MEMO)
    else:
        previous, _, _, first = current(profile, 'initial')
        assert first.artifact is not None and first.question is not None
        question, thread = first.question, previous.emlis_thread
        answer = SupplementalAnswerSource('answer-1', thread.thread_id,
            question.question_id, 1, thread.original_source_ref,
            '今は嬉しい。', '2026-09-11T01:00:00Z')
        control = replace(thread.question_control_context, pending_question=question,
            asked_target_refs=(question.decision.target_ref,), issued_count=1,
            issued_questions=(question,))
        request = replace(previous, emlis_thread=replace(thread, answers=(answer,),
            current_round=1, question_control_context=control,
            prepared_meaning_checkpoint_ref=None))
        request = checkpoint(request, engine.prepare_emlis_update(request).checkpoint_id)
    prepared = update.prepare_emlis_meaning(request)
    plan = update.build_updated_grounded_plan(prepared)
    return request, prepared, plan, engine.generate(request)


@pytest.mark.parametrize('profile', ['q1', 'q3'])
@pytest.mark.parametrize('stage', ['initial', 'add'])
def test_actual_reflexive_body_keeps_each_selected_duty(profile, stage):
    _, prepared, plan, out = current(profile, stage)
    assert out.artifact is not None, out.reason_codes
    received_observation = ('「褒められた」と「嬉しくなかった」が、異なる向きのまま同時にあります。'
        if stage == 'initial' else
        '「褒められた」のに「嬉しくなかった」、回答した時点では「嬉しい」とあります。')
    expected_observation = '\n'.join((PAIR_OBSERVATION, received_observation,
        '今回の中心には、「' + UNKNOWN + '」があります。'))
    answer_reception = ('' if stage == 'initial' else
        '褒められたことについて、回答した時点では嬉しいのですね。')
    expected_reception = PAIR_RECEPTION + answer_reception + UNKNOWN_RECEPTION
    assert out.artifact.text == ('見えたこと：\n' + expected_observation
        + '\n\nEmlisから：\n' + expected_reception)
    assert 'かもしれない' not in out.artifact.reception
    original = prepared.original_plan
    group = observation._source_mixed_relief_unknown_group(
        original.nuclei, original.relations, prepared.thread.original.evidence_spans,
        prepared.thread.original.normalized_current_input)
    assert len(group) == 7
    unknown, left, right, event, reaction, *_ = group
    assert next(n for n in plan.nuclei if n.nucleus_id == unknown.nucleus_id) == unknown
    moves = plan.response_plan.human_reception_plan.moves
    selected = project_thread_meaning(prepared, plan).selected_reception
    assert len(moves) == len(selected.decisions) == (2 if stage == 'initial' else 3)
    duties = [{*m.target_nucleus_ids, *m.support_nucleus_ids} for m in moves]
    assert {left.nucleus_id, right.nucleus_id} in duties
    assert {unknown.nucleus_id} in duties
    pair = selected.decisions[0]
    assert len(pair.subjective_proposition.response_object_refs) == (3 if stage == 'initial' else 4)
    if stage == 'initial':
        assert set.union(*duties).isdisjoint({event.nucleus_id, reaction.nucleus_id})
        assert out.question.prompt_private == QUESTION
        assert out.body_state == 'PRE_QUESTION'
        assert type(pair.retained_relief_cognition) is contracts.RetainedReliefCognitionContentV1
    else:
        assert out.question is None and out.body_state == 'REFINED'
        assert observation._source_retained_mixed_unknown_from_resolver(
            plan.nuclei, plan.relations, prepared.thread.resolver()) == group[:3]
        assert prepared.thread.control.question_control_context.issued_count == 1
        assert len(update._retained_unchanged_relief_cognition_duties(
            prepared, plan.nuclei, plan.relations)) == 3
        assert type(pair.retained_relief_cognition) is contracts.RetainedUpdatedReliefCognitionContentV2
        refs = [set(d.selected_contribution_refs) for d in selected.decisions]
        assert all(refs[i].isdisjoint(refs[j]) for i in range(3) for j in range(i + 1, 3))
        assert set.union(*refs) == set(pair.subjective_proposition.target_contribution_refs)


@pytest.mark.parametrize('profile', ['q1', 'q3'])
def test_independently_frozen_u347_checkpoint_keeps_its_unavailable_state(profile):
    assert BASELINE['source_commit'] == 'e53e8af8513bd567e1df9bca1b09dad4977e230c'
    old = BASELINE['initial'][profile]
    request = (initial if profile == 'q1' else begin)(MEMO)
    prepared, out = full_snapshot(checkpoint(request, old['checkpoint_id']), old)
    assert out.artifact is None and out.question is None
    assert out.reason_codes == ('emlis_q3_initial_body_unavailable',)
    assert not any(WITNESS in n.semantic_frame.attribute_codes for n in prepared.original_plan.nuclei)


@pytest.fixture(scope='module')
def legacy_source():
    prepared = update.prepare_emlis_meaning(begin(MEMO))
    plan = original_meaning_plan(prepared.thread, _legacy_mixed_relief_unknown=True)
    source = prepared.thread.original
    span = next(s for s in source.evidence_spans if s.raw_text == UNKNOWN)
    unknown = next(n for n in plan.nuclei if n.source_span_ids == (span.span_id,))
    return plan, source, span, unknown


def test_reflexive_correction_changes_only_the_two_existing_type_fields(legacy_source):
    plan, source, _, unknown = legacy_source
    assert (unknown.kind, unknown.semantic_frame.predicate_kind) == ('reaction', 'feeling')
    corrected = observation._final_source_mixed_relief_unknown(plan.nuclei, plan.relations,
        source.evidence_spans, source.normalized_current_input)
    expected = replace(unknown, kind='uncertainty', semantic_frame=replace(
        unknown.semantic_frame, predicate_kind='uncertainty'))
    assert corrected == tuple(expected if n == unknown else n for n in plan.nuclei)
    assert len(observation._source_mixed_relief_unknown_group(corrected, plan.relations,
        source.evidence_spans, source.normalized_current_input, require_witness=False)) == 7


@pytest.mark.parametrize('mutation', [
    'bare', 'cause', 'past_raw', 'foreign_owner', 'actor', 'past_type',
    'modality', 'self_evaluation', 'unknown_relation',
])
def test_reflexive_fallback_cannot_reclassify_unqualified_source(legacy_source, mutation):
    plan, source, span, unknown = legacy_source
    nuclei, relations, spans = plan.nuclei, plan.relations, source.evidence_spans
    normalized = source.normalized_current_input
    fragments = dict(bare='まだわからない', cause='なぜ不安なのか、自分でもまだわからない',
        past_raw='何が不安なのか、自分でもまだわからなかった',
        foreign_owner='何が不安なのか、友人でもまだわからない')
    if mutation in fragments:
        raw = fragments[mutation]
        spans = tuple(replace(s, raw_text=raw, end_index=s.start_index + len(raw))
            if s == span else s for s in spans)
        normalized = dict(normalized, memo=normalized['memo'][:span.start_index] + raw + '。')
    elif mutation == 'unknown_relation':
        pair = next(n for n in nuclei if 'source_relief_cognition_slot:relief' in n.semantic_frame.attribute_codes)
        edge = replace(relations[0], relation_id='relation:injected', type='wish_and_constraint',
            from_nucleus_id=pair.nucleus_id, to_nucleus_id=unknown.nucleus_id,
            source_span_ids=pair.source_span_ids + unknown.source_span_ids,
            source_relation_ids=('conflict.e999',), source_meaning_arc_keys=(),
            grounding_kind='user_stated_relation', retention='required')
        relations = (*relations, edge)
    else:
        frame = unknown.semantic_frame
        frame = (replace(frame, actor='other_person') if mutation == 'actor' else
            replace(frame, time_scope='past') if mutation == 'past_type' else
            replace(frame, modality='fact') if mutation == 'modality' else
            replace(frame, attribute_codes=(*frame.attribute_codes, 'operator:self_evaluation')))
        changed = replace(unknown, semantic_frame=frame)
        nuclei = tuple(changed if n == unknown else n for n in nuclei)
    assert (nuclei, relations, spans, normalized) != (plan.nuclei, plan.relations,
        source.evidence_spans, source.normalized_current_input)
    assert observation._final_source_mixed_relief_unknown(
        nuclei, relations, spans, normalized) == nuclei
