"""Explicit present replacements keep their answer time and old saved identity.

The u350 comparison is captured from an independent, unchanged source process.
Only current SELF uncertainty -> already admitted finite feeling is repaired.
"""
from dataclasses import replace
from functools import lru_cache
import json
from pathlib import Path

import pytest
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine import emlis_answer_update as update
from cocolon_meaning_experience_engine.emlis_thread_contracts import SupplementalAnswerSource
from cocolon_meaning_experience_engine.emlis_thread_projection import project_thread_meaning
from test_cmee_emlis_contrast_degree import encoded, digest
from test_cmee_emlis_q1_thread import initial
from test_cmee_emlis_q3_thread import begin
from test_cmee_emlis_relief_received import decode_question
from test_cmee_emlis_received_discourse import actual
from test_cmee_emlis_detached_observation import read_body

BASELINE = json.loads((Path(__file__).parent / 'fixtures' /
    'cmee_emlis_u350_unknown_revision_time_v1.json').read_text())
ROWS = {(r['case'], r['profile']): r for r in BASELINE['cases']}
CHANGED = {'mixed_unknown_now', 'mixed_reflexive_now',
           'mixed_unknown_current_negative', 'mixed_unknown_now_negative'}


@lru_cache(None)
def first(case, profile):
    req = (initial if profile == 'q1' else begin)(ROWS[case, profile]['memo'])
    return req, MeaningExperienceEngine().generate(req)


@lru_cache(None)
def request(case, profile, historical=False):
    row = ROWS[case, profile]
    req, out = first(case, profile)
    assert digest(out.artifact) == row['initial_artifact_sha']
    assert encoded(out.question) == row['initial_question']
    assert encoded(out.question_decision) == row['initial_decision']
    q = decode_question(row['initial_question']) if historical else out.question
    t = req.emlis_thread
    answer = SupplementalAnswerSource('answer-1', t.thread_id, q.question_id, 1,
        t.original_source_ref, row['answer'], '2026-09-11T01:00:00Z')
    control = replace(t.question_control_context, pending_question=q,
        asked_target_refs=(q.decision.target_ref,), issued_count=1, issued_questions=(q,))
    return replace(req, emlis_thread=replace(t, answers=(answer,), current_round=1,
        prepared_meaning_checkpoint_ref=row['checkpoint_id'] if historical else None,
        question_control_context=control))


def checkpoint(req, ref):
    return replace(req, emlis_thread=replace(req.emlis_thread,
        prepared_meaning_checkpoint_ref=ref))


def full_snapshot(req, row):
    prepared = update.prepare_emlis_meaning(req)
    assert digest(prepared.checkpoint) == row['checkpoint_sha']
    assert digest(prepared.original_plan) == row['original_plan_sha']
    assert digest(prepared.accepted_nuclei) == row['accepted_nuclei_sha']
    if 'plan_error' in row:
        with pytest.raises(ValueError) as exc:
            update.build_updated_grounded_plan(prepared)
        assert str(exc.value) == row['plan_error']
    else:
        plan = update.build_updated_grounded_plan(prepared)
        assert digest(plan) == row['plan_sha']
        if 'projection_error' in row:
            with pytest.raises(ValueError) as exc:
                project_thread_meaning(prepared, plan)
            assert str(exc.value) == row['projection_error']
        else:
            assert digest(project_thread_meaning(prepared, plan).selected_reception) == row['selected_sha']
    out = MeaningExperienceEngine().generate(checkpoint(req, prepared.checkpoint.checkpoint_id))
    assert digest(out.artifact) == row['artifact_sha']
    assert encoded(out.question) == row['question']
    assert encoded(out.question_decision) == row['question_decision']
    assert list(out.reason_codes) == row['reasons']
    assert out.status.value == row['status'] and out.body_state == row['body_state']


@pytest.mark.parametrize('case,profile', ROWS)
def test_complete_saved_u350_interpretation_replays(case, profile):
    assert BASELINE['source_commit'] == '2b3a83e2a25445967412e7569332ea308df031ef'
    full_snapshot(request(case, profile, True), ROWS[case, profile])


@pytest.mark.parametrize('case,profile', [key for key in ROWS if key[0] not in CHANGED])
def test_other_targets_times_and_unsupported_replacements_are_unchanged(case, profile):
    full_snapshot(request(case, profile), ROWS[case, profile])


@pytest.mark.parametrize('case,profile', [key for key in ROWS if key[0] in CHANGED])
def test_new_current_unknown_revision_is_bound_to_answer_source(case, profile):
    req = request(case, profile)
    prepared = update.prepare_emlis_meaning(req)
    cp = prepared.checkpoint
    item, = cp.answer_update.updates
    assert item.operation == 'REVISE' and not cp.unresolved_parts
    assert cp.checkpoint_id != ROWS[case, profile]['checkpoint_id']
    binding = item.temporal_binding
    assert binding.about_time == 'ANSWER_TIME'
    assert binding.anchor_source_ref == prepared.thread.answers[0].envelope.envelope_id
    assert binding.time_expression_evidence_refs == item.evidence_refs
    assert binding.time_expression_evidence_refs
    nucleus, = prepared.accepted_nuclei
    assert nucleus.source_fields == ('answer_text_private',)
    assert nucleus.semantic_frame.time_scope == 'present'
    assert nucleus.semantic_frame.polarity == ('negative' if 'negative' in case else 'positive')
    assert 'thread_time:answer_time' in nucleus.semantic_frame.attribute_codes
    fragment, = (v for v in nucleus.semantic_frame.attribute_codes
                 if v.startswith('source_fragment_scalar_range:'))
    start, end = map(int, fragment.split(':')[1:])
    assert ROWS[case, profile]['answer'][start:end] == (
        '嬉しくない' if 'negative' in case else '嬉しい')
    assert digest(prepared.original_plan) == ROWS[case, profile]['original_plan_sha']
    saved = checkpoint(req, cp.checkpoint_id)
    restored = update.prepare_emlis_meaning(saved)
    assert restored.checkpoint == cp
    assert restored.original_plan == prepared.original_plan
    assert restored.accepted_nuclei == prepared.accepted_nuclei
    # The saved request now has a checkpoint ref; compare interpretation,
    # not the request-control object that deliberately changed at save time.
    assert update.build_updated_grounded_plan(restored) == update.build_updated_grounded_plan(prepared)
    out = MeaningExperienceEngine().generate(saved)
    assert not out.automatic_progression
    assert out.question is None
    if 'negative' in case:
        # Existing pair eligibility expires when uncertainty itself is revised.
        # Time correctness is not a claim that its unavailable body is fixed.
        assert out.artifact is None and out.status.value == 'UNAVAILABLE'
        assert 'emlis_refined_body_unavailable' in out.reason_codes
    else:
        assert out.artifact is not None, out.reason_codes
        assert '回答した時点で嬉しいという気持ちを受け止めています。' == out.artifact.reception
        assert '今は嬉しい' not in out.artifact.reception
        assert 'その時に' not in out.artifact.reception
        assert '私も少し安心しました' not in out.artifact.reception


@pytest.fixture(scope='module')
def context():
    return actual(request=request('mixed_unknown_now', 'q3'))


@pytest.mark.parametrize('old,new', [
    ('回答した時点で嬉しい', 'その時に嬉しかった'),
    ('回答した時点で嬉しい', '先の回答時点で嬉しい'),
    ('回答した時点で嬉しい', '嬉しい'),
    ('回答した時点で嬉しい', '回答した時点で嬉しくない'),
])
def test_independent_reader_rejects_reassigned_time_or_polarity(context, old, new):
    body = context[0].artifact.text
    assert read_body(context, body).passed
    changed = body.replace(old, new)
    assert changed != body and not read_body(context, changed).passed


def test_unrelated_checkpoint_cannot_choose_legacy_interpretation():
    req = checkpoint(request('mixed_unknown_now', 'q3'), 'unknown-saved-checkpoint')
    with pytest.raises(ValueError, match='emlis_checkpoint_source_prefix_mismatch'):
        update.prepare_emlis_meaning(req)


@pytest.mark.parametrize('replacement,about,fragment', [
    ('今は、嬉しい', 'ANSWER_TIME', '嬉しい'),
    ('現在は 嬉しい', 'ANSWER_TIME', '嬉しい'),
    ('今も嬉しい', 'ORIGINAL_OCCASION', '今も嬉しい'),
    ('現在も嬉しい', 'ORIGINAL_OCCASION', '現在も嬉しい'),
])
def test_topic_separator_and_excluded_additive_particle_keep_source(replacement, about, fragment):
    req = request('mixed_unknown_now', 'q3')
    old, = req.emlis_thread.answers
    text = old.answer_text_private.replace('今は嬉しい', replacement)
    req = replace(req, emlis_thread=replace(req.emlis_thread,
        answers=(replace(old, answer_text_private=text),)))
    p = update.prepare_emlis_meaning(req)
    item, = p.checkpoint.answer_update.updates
    assert item.operation == 'REVISE' and item.temporal_binding.about_time == about
    nucleus, = p.accepted_nuclei
    span, = (v for v in nucleus.semantic_frame.attribute_codes
             if v.startswith('source_fragment_scalar_range:'))
    start, end = map(int, span.split(':')[1:])
    assert text[start:end] == fragment
    if about == 'ANSWER_TIME':
        out = MeaningExperienceEngine().generate(checkpoint(req, p.checkpoint.checkpoint_id))
        assert out.artifact is not None, out.reason_codes
        assert out.artifact.reception == '回答した時点で嬉しいという気持ちを受け止めています。'
