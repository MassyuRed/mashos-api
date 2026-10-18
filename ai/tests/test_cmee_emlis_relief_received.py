"""Approved pair + received experience: complete old replay and visible retention.

The u349 fixture was captured in a separate, unchanged source process. It is an
old-version comparison, never an expectation manufactured by the new writer.
"""
from dataclasses import replace
from functools import lru_cache
import json
import os
from pathlib import Path
import re
from unittest.mock import patch

import pytest
import emlis_ai_grounded_human_reception as hr
import emlis_ai_grounded_observation_plan as gp
import emlis_ai_grounded_sentence_surface as surface
from cocolon_meaning_experience_engine import MeaningExperienceEngine, contracts as c
from cocolon_meaning_experience_engine import emlis_answer_update as update
from cocolon_meaning_experience_engine.emlis_thread_projection import project_thread_meaning
from cocolon_meaning_experience_engine.emlis_thread_contracts import (
    EmlisClarificationV1, EmlisQuestionDecisionV1, SupplementalAnswerSource,
)
from test_cmee_emlis_contrast_degree import encoded, digest
from test_cmee_emlis_q1_thread import initial
from test_cmee_emlis_q3_thread import begin
from test_cmee_emlis_received_discourse import actual
from test_cmee_emlis_detached_observation import read_body

BASELINE = json.loads((Path(__file__).parent / 'fixtures' /
    'cmee_emlis_u349_relief_received_v1.json').read_text())
ROWS = {row['case']: row for row in BASELINE['cases']}
UPDATES = {row['case']: row for row in BASELINE['updates']}
QUALIFIED = {name + suffix for name in ('base', 'self', 'degree', 'kana',
    'received_kana', 'received_connective', 'received_owned') for suffix in ('', '_unknown')}
QUALIFIED |= {'reflexive_unknown', 'object_unknown'}
OPERATIONS = {
    name + suffix: operation for name, operation in (
        ('add', 'ADD'), ('add_negative', 'ADD'), ('add_past', 'ADD'),
        ('add_past_negative', 'ADD'), ('revise', 'REVISE'),
        ('withdraw_event', 'WITHDRAW_EVENT'), ('withdraw_reaction', 'WITHDRAW_REACTION'))
    for suffix in ('', '_unknown')}
OPERATIONS.update(degree_add='ADD', reflexive_add='ADD')


def checkpoint(req, ref):
    return replace(req, emlis_thread=replace(req.emlis_thread,
        prepared_meaning_checkpoint_ref=ref))


def decode_question(value):
    q = dict(value)
    d = dict(q.pop('decision'))
    for key in ('supporting_evidence_refs', 'affected_meaning_refs',
                'affected_reception_refs', 'asked_target_refs'):
        d[key] = tuple(d[key])
    return EmlisClarificationV1(decision=EmlisQuestionDecisionV1(**d), **q)


@lru_cache(None)
def request(case, profile='q3', answered=False, historical=False):
    row = (UPDATES if answered else ROWS)[case]
    req = (initial if profile == 'q1' else begin)(row['memo'])
    if not answered:
        return checkpoint(req, row[profile]['checkpoint_id']) if historical else req
    if historical:
        q = decode_question(ROWS[row['original_case']][profile]['question'])
    else:
        # Reuse this actual initial output across independent one-answer cases.
        # Its issued question is never fabricated or inferred from new source.
        original = initial_output(row['original_case'], profile)
        assert original.artifact and original.question, original.reason_codes
        q = original.question
    t = req.emlis_thread
    answer = SupplementalAnswerSource('answer-1', t.thread_id, q.question_id, 1,
        t.original_source_ref, row['answer'], '2026-09-11T01:00:00Z')
    control = replace(t.question_control_context, pending_question=q,
        asked_target_refs=(q.decision.target_ref,), issued_count=1,
        issued_questions=(q,))
    req = replace(req, emlis_thread=replace(t, answers=(answer,), current_round=1,
        prepared_meaning_checkpoint_ref=row[profile]['checkpoint_id'] if historical else None,
        question_control_context=control))
    return req if historical else checkpoint(req, MeaningExperienceEngine().prepare_emlis_update(req).checkpoint_id)


@lru_cache(None)
def initial_output(case, profile='q3'):
    return MeaningExperienceEngine().generate(request(case, profile))


def full_snapshot(req, old):
    prepared = update.prepare_emlis_meaning(req)
    assert digest(prepared.checkpoint) == old['checkpoint_sha']
    assert digest(prepared.original_plan) == old['original_plan_sha']
    if 'plan_error' in old:
        with pytest.raises(ValueError) as exc:
            update.build_updated_grounded_plan(prepared)
        assert str(exc.value) == old['plan_error']
    else:
        plan = update.build_updated_grounded_plan(prepared)
        assert digest(plan) == old['plan_sha']
        assert digest(plan.nuclei) == old['nuclei_sha']
        assert digest(plan.relations) == old['relations_sha']
        if 'projection_error' in old:
            with pytest.raises(ValueError) as exc:
                project_thread_meaning(prepared, plan)
            assert str(exc.value) == old['projection_error']
        else:
            selected = project_thread_meaning(prepared, plan).selected_reception
            assert digest(selected) == old['selected_sha']
    out = MeaningExperienceEngine().generate(req)
    for key in ('artifact', 'question', 'question_decision'):
        assert encoded(getattr(out, key)) == old[key]
    assert list(out.reason_codes) == old['reasons']
    assert out.status.value == old['status'] and out.body_state == old['body_state']
    return prepared, out


def export(name, req, out):
    folder = os.environ.get('CMEE_RELIEF_RECEIVED_BODY_DIR')
    if folder:
        Path(folder).mkdir(parents=True, exist_ok=True)
        Path(folder, name + '.json').write_text(json.dumps(dict(case=name,
            memo=update.prepare_emlis_meaning(req).thread.original.normalized_current_input['memo'],
            body=out.artifact.text if out.artifact else None,
            question=encoded(out.question), reasons=list(out.reason_codes)),
            ensure_ascii=False, indent=2) + '\n')


def _complete_partition(selected, object_count, move_count):
    assert len(selected.decisions) == move_count
    pair = selected.decisions[0]
    assert len(pair.subjective_proposition.response_object_refs) == object_count
    assert all(d.subjective_proposition == pair.subjective_proposition
               for d in selected.decisions)
    refs = [set(d.selected_contribution_refs) for d in selected.decisions]
    assert all(refs[i].isdisjoint(refs[j]) for i in range(len(refs))
               for j in range(i + 1, len(refs)))
    assert set.union(*refs) == set(pair.subjective_proposition.target_contribution_refs)


@pytest.mark.parametrize('profile', ['q1', 'q3'])
@pytest.mark.parametrize('answered,case', [*[(False, k) for k in ROWS],
                                          *[(True, k) for k in UPDATES]])
def test_full_u349_checkpoint_preserves_meaning_selection_body_and_stop(answered, case, profile):
    assert BASELINE['source_commit'] == '9ae2079769a1ee7c1d524fcc9569c8fa172ccbc8'
    assert BASELINE['source_tree'] == 'e4794f3c36fc7bcf14b443f14fe9ca702b99af8f'
    row = (UPDATES if answered else ROWS)[case]
    full_snapshot(request(case, profile, answered, True), row[profile])


@pytest.mark.parametrize('profile', ['q1', 'q3'])
@pytest.mark.parametrize('case', ROWS)
def test_initial_receives_both_experiences_only_with_complete_qualified_source(case, profile):
    req = request(case, profile)
    old = ROWS[case][profile]
    if case not in QUALIFIED:
        full_snapshot(req, old)
        return
    p = update.prepare_emlis_meaning(req)
    plan = update.build_updated_grounded_plan(p)
    group = gp._source_relief_received_group(plan.nuclei, plan.relations,
        p.thread.original.evidence_spans, p.thread.original.normalized_current_input)
    assert group and len(group) == 7
    unknown, left, right, event, reaction, *_ = group
    count = 4 + bool(unknown)
    assert p.checkpoint.checkpoint_id != old['checkpoint_id']
    moves = plan.response_plan.human_reception_plan.moves
    assert len(moves) == 2 + bool(unknown)
    selected_ids = {ref for m in moves for ref in
                    (*m.target_nucleus_ids, *m.support_nucleus_ids)}
    expected_ids = {n.nucleus_id for n in (left, right, event, reaction)}
    if unknown:
        expected_ids.add(unknown.nucleus_id)
    assert selected_ids == expected_ids
    selected = project_thread_meaning(p, plan).selected_reception
    _complete_partition(selected, count, len(moves))
    pair, received = selected.decisions[:2]
    assert type(pair.retained_relief_received) is c.RetainedReliefReceivedPairContentV1
    assert type(received.retained_relief_received) is c.RetainedReliefReceivedExperienceContentV1
    assert pair.retained_relief_received.eligibility.operation == 'INITIAL'
    out = initial_output(case, profile)
    assert out.artifact, out.reason_codes
    follow = out.artifact.reception
    assert ('ほめられた' if case.startswith('received_kana') else '褒められた') in follow
    assert '嬉' in follow and ('なかった' in follow or '伴わない' in follow)
    assert '私も少し安心しましたが' in follow
    if unknown:
        assert ('よくわからないのですね。' if case == 'object_unknown'
                else 'まだわからないのですね。') in follow
    assert 'かもしれない' not in follow
    assert out.artifact.observation == old['artifact']['observation']
    assert encoded(out.question) == old['question']
    assert encoded(out.question_decision) == old['question_decision']
    if case in {'base', 'base_unknown'}:
        assert MeaningExperienceEngine().generate(checkpoint(req, p.checkpoint.checkpoint_id)).artifact == out.artifact
    if profile == 'q3':
        export('initial-' + case, req, out)


@pytest.mark.parametrize('profile', ['q1', 'q3'])
@pytest.mark.parametrize('case', UPDATES)
def test_one_existing_answer_preserves_valid_received_material_and_qualifiers(case, profile):
    req = request(case, profile, True)
    old = UPDATES[case][profile]
    p = update.prepare_emlis_meaning(req)
    assert p.checkpoint.answer_update.disposition == old['answer_disposition']
    if 'plan_error' in old and case not in OPERATIONS:
        with pytest.raises(ValueError) as exc:
            update.build_updated_grounded_plan(p)
        assert str(exc.value) == old['plan_error']
        out = MeaningExperienceEngine().generate(req)
        assert encoded(out.artifact) == old['artifact']
        return
    plan = update.build_updated_grounded_plan(p)
    out = MeaningExperienceEngine().generate(req)
    duties = update._retained_relief_received_duties(p, plan.nuclei, plan.relations)
    if case in OPERATIONS:
        operation = OPERATIONS[case]
        has_unknown = UPDATES[case]['original_case'].endswith('_unknown')
        count = {'ADD': 5, 'REVISE': 4, 'WITHDRAW_EVENT': 3,
                 'WITHDRAW_REACTION': 3}[operation] + has_unknown
        assert len(duties) == 2 + has_unknown
        selected = project_thread_meaning(p, plan).selected_reception
        _complete_partition(selected, count, len(duties))
        pair, received = selected.decisions[:2]
        assert pair.retained_relief_received.eligibility.operation == operation
        assert received.retained_relief_received.eligibility.operation == operation
        assert out.artifact, out.reason_codes
        follow = out.artifact.reception
        assert '私も少し安心しましたが' in follow
        if has_unknown:
            assert ('ご自身でも' if case == 'reflexive_add' else 'あなたにも') in follow
            assert 'まだわからないのですね。' in follow
        if operation == 'ADD':
            assert '褒められた' in follow and '嬉しくなかった' in follow
            if 'past' in case:
                assert 'その時' in follow
                assert ('悲しくなかった' if 'negative' in case else '嬉しかった') in follow
            else:
                assert '回答した時点' in follow
                assert ('嬉しくない' if 'negative' in case else '嬉しい') in follow
        elif operation == 'REVISE':
            assert '嬉しくなかった' not in out.artifact.text
            assert '褒められた' in follow and '悲' in follow
        elif operation == 'WITHDRAW_EVENT':
            assert '褒められた' not in out.artifact.text
            assert '嬉しくなかった' in follow
        else:
            assert '嬉しくなかった' not in out.artifact.text
            assert '褒められた' in follow
            assert not any(term in follow for term in ('嬉', '悲', '嬉しさ', '経験だった'))
        assert encoded(out.question) == old['question']
        assert encoded(out.question_decision) == old['question_decision']
        if case in {'add', 'add_unknown'}:
            assert MeaningExperienceEngine().generate(checkpoint(req, p.checkpoint.checkpoint_id)).artifact == out.artifact
    elif p.checkpoint.answer_update.disposition == 'NO_MATERIAL_UPDATE':
        assert not duties and plan == p.original_plan
        assert out.artifact is None and out.body_state == 'UNCHANGED'
        assert out.reason_codes == ('reuse_saved_observation_required',)
    else:
        assert not duties
        # Changes to the pair or unknown must not resurrect the old complete
        # group. Fresh source versions have new identities; completed old
        # checkpoints are compared in full in the historical test above.
        if old['artifact'] is None:
            assert out.artifact is None
        else:
            current = encoded(out.artifact)
            identities = {'artifact_id', 'meaning_checkpoint_ref', 'meaning_trace', 'reception_trace'}
            expected = dict(old['artifact'])
            if case == 'unknown_revise':
                # u351 fixes only the already admitted explicit current
                # replacement. Historical checkpoint expectations stay intact.
                expected['observation'] = expected['observation'].replace(
                    'その時の気持ちとして、「今は嬉しい」が見えます。',
                    '回答した時点の気持ちとして、「嬉しい」が見えます。')
                expected['reception'] = '回答した時点で嬉しいという気持ちを受け止めています。'
            assert {k: v for k, v in current.items() if k not in identities} == {
                k: v for k, v in expected.items() if k not in identities}
            assert current['meaning_checkpoint_ref'] == p.checkpoint.checkpoint_id
            assert current['meaning_checkpoint_ref'] != old['artifact']['meaning_checkpoint_ref']
            original = gp._source_relief_received_group(p.original_plan.nuclei,
                p.original_plan.relations, p.thread.original.evidence_spans,
                p.thread.original.normalized_current_input)
            assert original and original[0] is not None
            assert original[0].nucleus_id not in {n.nucleus_id for n in plan.nuclei}
            assert not any('source_relief_received_retention:v1' in n.semantic_frame.attribute_codes
                           for n in plan.nuclei)
            assert '何が不安なのか、私にもまだわからない' not in out.artifact.text
        assert encoded(out.question) == old['question']
        assert encoded(out.question_decision) == old['question_decision']
        assert list(out.reason_codes) == old['reasons']
        assert out.status.value == old['status'] and out.body_state == old['body_state']
    if profile == 'q3':
        export('update-' + case, req, out)


@lru_cache(None)
def actual_context(case):
    req = request('base_unknown') if case == 'initial' else request(case, 'q3', True)
    return actual(request=req)


@pytest.fixture(scope='module', params=['initial', 'add_unknown', 'add_past_negative_unknown',
                                        'revise_unknown', 'withdraw_event_unknown',
                                        'withdraw_reaction_unknown'])
def context(request):
    name = request.param
    return name, actual_context(name)


@pytest.mark.parametrize('mutation', ['received_missing', 'pair_missing', 'unknown_missing',
                                      'subject', 'causal'])
def test_each_received_duty_is_required_by_reader_without_calling_author(context, mutation):
    _, ctx = context
    out, *_ = ctx
    follow = out.artifact.reception
    parts = re.findall(r'[^。]+。', follow)
    assert len(parts) == 3
    pair = next(part for part in parts if '私も少し安心しましたが' in part)
    unknown = next(part for part in parts if 'まだわからないのですね' in part)
    received, = (part for part in parts if part not in (pair, unknown))
    if mutation == 'received_missing':
        changed = follow.replace(received, '')
    elif mutation == 'pair_missing':
        changed = follow.replace(pair, '')
    elif mutation == 'unknown_missing':
        changed = follow.replace(unknown, '')
    elif mutation == 'subject':
        changed = follow.replace(received, '友人は、' + received)
    else:
        changed = follow.replace(received, 'だから、' + received)
    assert changed != follow
    body = out.artifact.text.replace(follow, changed)
    with patch.object(surface, '_realize_line', side_effect=AssertionError('no author oracle')):
        assert read_body(ctx, out.artifact.text).passed
        assert not read_body(ctx, body).passed


@pytest.mark.parametrize('case,old,new', [
    ('add_unknown', '回答した時点', 'その時'),
    ('add_unknown', '嬉しくなかった', '嬉しかった'),
    ('add_unknown', '嬉しいのですね', '嬉しくないのですね'),
    ('add_past_negative_unknown', '悲しくなかった', '悲しかった'),
    ('withdraw_event_unknown', 'その時は嬉しくなかった', '回答した時点では嬉しくない'),
    ('withdraw_reaction_unknown', '褒められた', '褒められたので嬉しかった'),
])
def test_reader_rejects_received_time_polarity_change_and_withdrawn_revival(case, old, new):
    ctx = actual_context(case)
    out, *_ = ctx
    follow = out.artifact.reception
    assert old in follow
    changed = out.artifact.text.replace(follow, follow.replace(old, new))
    assert changed != out.artifact.text
    assert not read_body(ctx, changed).passed
