"""Public synthetic full-engine questions and answer-owned outcome standards.

The tentative reading is control, not source evidence. An explicit answer can
confirm or replace its direction; no personal goal is manufactured from yes/no.
"""
from dataclasses import asdict, replace
import json
from unittest.mock import patch

import pytest
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.emlis_answer_update import (
    prepare_emlis_meaning, build_updated_grounded_plan, _past_desire_source,
)
from cocolon_meaning_experience_engine.emlis_question import question_candidate, original_meaning_plan
from cocolon_meaning_experience_engine.emlis_thread_source import admit_emlis_thread
from test_cmee_emlis_q1_thread import initial, answered, prepared_request
from test_emlis_q2_application import run, answer
from test_emlis_q3_application import qdb, qcase

MATERIAL = '今日は散歩に出て帰っただけ'
APPRAISAL = '何一つできなかった'
MEMO = MATERIAL + '。' + APPRAISAL + '。'


def actual(text, request=None):
    req, checkpoint = prepared_request(answered(text, request or initial(MEMO)))
    result = MeaningExperienceEngine().generate(req)
    assert result.artifact is not None, result.reason_codes
    return req, checkpoint, result


@pytest.mark.parametrize('material', [MATERIAL, '今日は洗濯した', '用事を済ませた', '今日は書店に寄った'])
@pytest.mark.parametrize('appraisal', ['何もできなかった', '何一つできなかった', 'ひとつも出来なかった'])
def test_complete_source_discrepancy_selects_a_tentative_not_factual_standard(material, appraisal):
    request = initial(material + '。' + appraisal + '。')
    before = request
    result = MeaningExperienceEngine().generate(request)
    assert result.question is not None, result.reason_codes
    q = result.question
    assert q.decision.target_kind == 'PERSONAL_OUTCOME_STANDARD'
    assert q.decision.missing_dimension == 'personal_outcome_standard'
    assert appraisal in q.prompt_private and 'ということでしょうか' in q.prompt_private
    assert '違っていたら' in q.prompt_private
    assert q.prompt_private.count('でしょうか') == 1 and q.answer_limit == 1 and q.skip_allowed
    assert request == before and not result.automatic_progression
    prepared = prepare_emlis_meaning(request)
    assert not any(n.kind == 'wish' for n in prepared.original_plan.nuclei)
    assert 'やりたかった' not in json.dumps(asdict(prepared.checkpoint), ensure_ascii=False)
    resolver = prepared.thread.resolver()
    evidence = {r.evidence.evidence_id for r in resolver.qualified_refs
                if resolver.resolve(r.thread_span_id).source_field in {'memo', 'memo_action'}}
    assert set(q.decision.supporting_evidence_refs) == evidence
    # Asking does not overwrite the independently generated original body.
    original = MeaningExperienceEngine().generate(replace(request, emlis_thread=None))
    assert original.artifact.text == result.artifact.text


@pytest.mark.parametrize('memo,action', [
    ('何もできなかった。', ''),
    ('今日は雨だった。何もできなかった。', ''),
    ('今日は晴れだった。何もできなかった。', ''),
    ('今日は寒かった。何もできなかった。', ''),
    (MATERIAL + '。自分が情けない。', ''),
    ('友人は散歩に出て帰っただけ。何もできなかった。', ''),
    ('散歩に出て帰りたかった。何もできなかった。', ''),
    ('散歩に出て帰れなかっただけ。何もできなかった。', ''),
    ('もし散歩に出て帰ったなら。何もできなかった。', ''),
    ('「散歩に出て帰っただけ」と彼は言った。何もできなかった。', ''),
    ('昨日は散歩に出て帰っただけ。今日は何もできなかった。', ''),
    (MATERIAL + '。何もできなかったかもしれない。', ''),
    (MATERIAL + '。何もできなかったわけではない。', ''),
    (MEMO + '制作を進めたかった。', ''),
    (MEMO, '休みたかった。'),
])
def test_no_proposal_from_other_owner_unperformed_uncertainty_or_already_supplied_standard(memo, action):
    thread = admit_emlis_thread(initial(memo, action))
    decision, question = question_candidate(thread, original_meaning_plan(thread), parent_request_id='synthetic')
    assert question is None or decision.target_kind != 'PERSONAL_OUTCOME_STANDARD'


@pytest.mark.parametrize('mode', ['stop', 'budget', 'asked'])
def test_question_controls_still_end_the_new_candidate(mode):
    request = initial(MEMO)
    thread = admit_emlis_thread(request)
    plan = original_meaning_plan(thread)
    _, first = question_candidate(thread, plan, parent_request_id=request.request_id)
    control = thread.control.question_control_context
    if mode == 'stop': control = replace(control, stop=True)
    elif mode == 'budget': control = replace(control, issued_count=1)
    else: control = replace(control, asked_target_refs=(first.decision.target_ref,))
    thread = replace(thread, control=replace(thread.control, question_control_context=control))
    assert question_candidate(thread, plan, parent_request_id=request.request_id)[1] is None


@pytest.mark.parametrize('reply', ['制作を進めたかった', '休みたかった', '本を読みたかった', '手紙を書きたかった', '静かに過ごしたかった'])
@pytest.mark.parametrize('feedback', ['', 'そうです。', '違います。'])
def test_own_answer_not_proposal_supplies_the_wish_and_changes_real_response(reply, feedback):
    req, checkpoint, result = actual(feedback + reply + '。')
    assert checkpoint.assessment_status == 'RESOLVED'
    assert checkpoint.answer_update.disposition == 'MATERIAL_UPDATE'
    assert result.body_state == 'REFINED' and result.question is None
    assert reply in result.artifact.reception
    assert 'やりたかったことには手が届かなかった' not in result.artifact.text
    prepared = prepare_emlis_meaning(req)
    assert len(prepared.accepted_nuclei) == 1
    frame = prepared.accepted_nuclei[0].semantic_frame
    assert (frame.predicate_kind, frame.modality, frame.time_scope) == ('wish', 'wish', 'past')
    assert 'という変化' not in result.artifact.observation
    plan = build_updated_grounded_plan(prepared)
    original_ids = {n.nucleus_id for n in prepared.original_plan.nuclei}
    assert original_ids <= {n.nucleus_id for n in plan.nuclei}
    update = checkpoint.answer_update.updates[0]
    assert not update.superseded_claim_refs and update.operation == 'ADD'
    evidence = {e.evidence.evidence_id: e for e in prepared.thread.resolver().qualified_refs}
    assert all(evidence[e].source_envelope_id != req.emlis_thread.original_source_ref for e in update.evidence_refs)
    assert MATERIAL in result.artifact.observation and APPRAISAL in result.artifact.text


@pytest.mark.parametrize('text', ['はい。', 'そうです。', 'いいえ。', '違います。', '分からない。'])
def test_bare_feedback_never_manufactures_a_goal_or_withdraws_original(text):
    req, checkpoint, result = actual(text)
    assert checkpoint.answer_update.disposition == 'NO_MATERIAL_UPDATE'
    assert not checkpoint.answer_update.updates and not checkpoint.inactive_claim_refs
    assert not prepare_emlis_meaning(req).accepted_nuclei
    assert result.question is None and result.body_state == 'UNCHANGED'


@pytest.mark.parametrize('text', ['冷たかった', '重たかった', '眠たかった', '温かかった',
    '彼は休みたかった', '同僚は休みたかった', '「休みたかった」と言われた',
    '休みたかったかもしれない', '休みたくなかった', '休みたかったなら', '休みたかったと思った'])
def test_adjective_report_negation_and_modality_are_not_affirmative_desires(text):
    assert not _past_desire_source(text)
    req = answered(text+'。', initial(MEMO))
    prepared = prepare_emlis_meaning(req)
    assert not any(n.kind == 'wish' and n.semantic_frame.polarity == 'positive'
                   for n in prepared.accepted_nuclei)


def test_question_tampering_and_borrowed_evidence_cannot_authorize_answer():
    req = answered('休みたかった。', initial(MEMO))
    control = req.emlis_thread.question_control_context
    q = control.pending_question
    variants = [replace(q, prompt_private=q.prompt_private.replace('でしょうか', 'です')),
                replace(q, decision=replace(q.decision, supporting_evidence_refs=q.decision.supporting_evidence_refs[:1])),
                replace(q, decision=replace(q.decision, affected_meaning_refs=tuple(reversed(q.decision.affected_meaning_refs))))]
    for invalid in variants:
        changed = replace(req, emlis_thread=replace(req.emlis_thread,
            question_control_context=replace(control, pending_question=invalid)))
        with pytest.raises(ValueError, match='noncanonical'):
            prepare_emlis_meaning(changed)


def test_body_failure_does_not_erase_the_persons_rejection_and_new_meaning():
    req, checkpoint = prepared_request(answered('違います。休みたかった。', initial(MEMO)))
    with patch('cocolon_meaning_experience_engine.emlis_thread_engine.realize_emlis_thread_body', side_effect=ValueError('synthetic')):
        result = MeaningExperienceEngine().generate(req)
    assert result.artifact is None and result.meaning_checkpoint == checkpoint
    assert result.body_state == 'MEANING_UPDATED_BODY_UNAVAILABLE'
    assert checkpoint.answer_update.disposition == 'MATERIAL_UPDATE'


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
@pytest.mark.parametrize('reply', ['そうです。制作を進めたかった。', '違います。休みたかった。', '違います。'])
def test_question_answer_correction_and_get_work_in_existing_application(qcase,qdb,monkeypatch,tier,reply):
    user,parent,service = qcase
    qdb.query('update public.profiles set subscription_tier=$2 where id=$1', [user,tier])
    qdb.query('update public.emotions set memo=$1 where id=$2', [MEMO,parent])
    first = run(service.start(user,parent))
    assert first['state'] == 'AWAITING_ANSWER' and first['issued_count'] == 1
    current = run(answer(service,user,first,reply))
    assert current['current_observation'] is not None and current['original'] == first['original']
    assert current['question_limit'] == (3 if tier == 'premium' else 1)
    assert current['issued_count'] == 1 and current['pending_question'] is None
    if reply != '違います。':
        assert current['body_state'] == 'REFINED'
        assert reply.split('。')[1] in current['current_observation']['text']
    else:
        assert current['body_state'] == 'UNCHANGED' and not current['meaning_updated']
    monkeypatch.setattr(service.engine,'generate',lambda *_:pytest.fail('GET/start must not regenerate'))
    assert run(service.get(user,parent)) == current
    assert run(service.start(user,parent)) == current
