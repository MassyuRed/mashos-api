"""Real Emlis admission -> saved Analysis source -> active meaning material.

No model response is supplied: these tests exercise the shared source/update
owners and prove the private material's actual provenance and unread boundary.
"""
import copy
from dataclasses import replace
import hashlib
import json

import pytest

from emlis_thread_service import _request
from test_analysis_active_update_material import saved_update, REVISE, WITHDRAW
from test_analysis_saved_period import OWNER, NOW
from cocolon_meaning_experience_engine.emlis_thread_contracts import (
    EmlisClarificationV1, EmlisQuestionControlV1, EmlisQuestionDecisionV1,
    SupplementalAnswerSource)
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as admission
from cocolon_meaning_experience_engine.cores.analysis.source_adapter import (
    AnalysisSourceError, commitment, emlis_analysis_source_request, freeze_analysis_sources)


def prepare(saved, *, request=None, owner=OWNER, as_of=NOW):
    request = request or _request(saved, include_context=False, analysis_source_only=True)
    return admission.prepare_emlis_analysis_material(request, owner_scope=owner,
        original_record=saved['original'], as_of=as_of)


def uncorrected(memo, action=''):
    saved = saved_update(memo=memo, action=action)
    saved['events'] = []
    return saved


def answer_request(saved, texts):
    request = _request(saved, include_context=False, analysis_source_only=True)
    thread = request.emlis_thread
    questions = tuple(EmlisClarificationV1('q' + str(i), request.request_id,
        thread.thread_id, thread.original_source_ref,
        EmlisQuestionDecisionV1('ASK', target_ref='target' + str(i)),
        'AI_QUESTION_IS_NOT_SOURCE') for i in range(1, len(texts) + 1))
    answers = tuple(SupplementalAnswerSource('a' + str(i), thread.thread_id,
        questions[i - 1].question_id, i, thread.original_source_ref, text, NOW)
        for i, text in enumerate(texts, 1))
    control = EmlisQuestionControlV1(questions[-1],
        tuple(q.decision.target_ref for q in questions), len(questions),
        issued_questions=questions, question_limit=3)
    return replace(request, emlis_thread=replace(thread, answers=answers,
        current_round=len(answers), question_control_context=control))


@pytest.mark.parametrize('explanation', [REVISE, WITHDRAW])
def test_both_original_fields_and_separate_surviving_occurrences_reach_shared_material(explanation):
    saved = saved_update(explanation)
    before = copy.deepcopy(saved)
    material = prepare(saved)
    assert material['state'] == 'GENERATED'
    assert material['record_version'] == commitment(before['original'])
    assert material['original_record'] == before['original']
    assert material['as_of'] == NOW
    assert material['coverage']['active_state'] == 'RESOLVED'
    assert material['coverage']['source_update_count'] == 1
    texts = [f['text'] for f in material['active_fields']]
    assert texts[:3] == ['私は考えをノートに書いた。', '私は資料を読んだ。', '私は日程を決めた。']
    assert all('私は仕事を続けたい' not in text for text in texts)
    if explanation == REVISE:
        assert texts[-1] == '私は家族を守りたい'
        field = material['active_fields'][-1]
        assert field['source_role'] == 'USER_INTERPRETATION_CORRECTION'
        assert field['scalar_start'] == REVISE.index('私は家族を守りたい') > 0
    # Exact source coordinates and hashes remain valid after JSON storage.
    request = _request(saved, include_context=False, analysis_source_only=True)
    _, projected = emlis_analysis_source_request(request, owner_scope=OWNER,
        original_record=saved['original'], as_of=NOW)
    frozen = freeze_analysis_sources(projected)
    for field in json.loads(json.dumps(material))['active_fields']:
        e = field['evidence']
        source = next(s for s in frozen.sources if
            s.envelope.envelope_id == field['source_envelope_id'])
        raw = source.envelope.raw_utf8
        original = raw[e['field_utf8_start']:e['field_utf8_end']].decode()
        assert raw[e['utf8_start']:e['utf8_end']].decode() == field['text']
        assert original[field['scalar_start']:field['scalar_end']] == field['text']
        assert e['literal_sha256'] == hashlib.sha256(field['text'].encode()).hexdigest()
    assert saved == before
    assert material == prepare(saved)
    payload = dict(material); ref = payload.pop('material_ref')
    assert ref == 'emlis-analysis-material:' + admission.digest(payload)


def test_raw_seven_fields_and_unknown_text_survive_without_a_generated_claim():
    saved = uncorrected('🐢🪷ZQZX。', '🦉QKZ。')
    saved['original'].update(category=['仕事', '人間関係'], emotions=['平穏', '喜び'],
        emotion_details=[{'type': '平穏', 'strength': 'medium'},
                         {'type': '喜び', 'strength': 'strong'}])
    material = prepare(saved)
    assert material['state'] == 'NOT_GENERATED'
    assert material['coverage']['active_state'] == 'RESOLVED'
    assert [f['text'] for f in material['active_fields']] == ['🐢🪷ZQZX。', '🦉QKZ。']
    assert material['original_record'] == saved['original']
    assert material['source_duties']['claims'] == []
    assert material['coverage']['active_text_status'] == 'PARTIAL'
    assert {r['field'] for r in material['coverage']['unassessed_source_ranges']} == {1, 2}
    assert not material['coverage']['full_source_semantic_coverage']


def test_whole_withdrawal_is_generated_update_with_no_remaining_active_text():
    material = prepare(saved_update(WITHDRAW, memo='私は仕事を続けたい。', action=''))
    assert material['state'] == 'GENERATED'
    assert material['active_fields'] == []
    assert material['source_duties']['claims'] == []
    assert material['coverage']['active_text_status'] == 'NO_ACTIVE_TEXT'
    assert [u['operation'] for u in material['graph']['source_updates']] == ['WITHDRAW']
    assert material['sources'][0]['fields']['memo'] == '私は仕事を続けたい。'


def test_pending_person_explanation_preserves_all_sources_without_resurrecting_old_claim():
    saved = saved_update('今はまだ決められません。')
    material = prepare(saved)
    assert material['state'] == 'NOT_GENERATED'
    assert material['active_fields'] == [] and material['graph'] is None
    assert material['coverage']['active_state'] == 'PENDING'
    assert material['reason_codes'] == ['analysis_interpretation_correction_pending']
    assert len(material['coverage']['pending_source_ranges']) == 3
    assert material['sources'][0]['fields']['memo'] == saved['original']['memo']
    assert material['sources'][-1]['fields']['memo'] == '今はまだ決められません。'
    assert 'AI_TARGET_NOT_USER_EVIDENCE' not in json.dumps(material, ensure_ascii=False)


def test_three_admitted_answers_use_existing_add_revise_withdraw_owners_and_not_questions():
    saved = uncorrected('私は仕事を続けたい。', '私は考えをノートに書いた。')
    request = answer_request(saved, ['私は日程を決めた。', REVISE,
        '「私は考えをノートに書いた」は取り消します。'])
    material = prepare(saved, request=request)
    assert material['state'] == 'GENERATED'
    assert [f['text'] for f in material['active_fields']] == ['私は日程を決めた。', '私は家族を守りたい']
    assert {f['source_role'] for f in material['active_fields']} == {'SUPPLEMENTAL_ANSWER'}
    assert [u['operation'] for u in material['graph']['source_updates']] == ['REVISE', 'WITHDRAW']
    assert len(material['sources']) == 4
    assert 'AI_QUESTION_IS_NOT_SOURCE' not in json.dumps(material)


@pytest.mark.parametrize('text', ['友人は考えをノートに書いた。',
    'もし私は仕事を続けたいなら、明日は休むかもしれない。',
    '友人は「私は仕事を続けたい」と言った。'])
def test_other_actor_condition_and_quote_are_unread_instead_of_self_facts(text):
    material = prepare(uncorrected(text))
    assert material['active_fields'][0]['text'] == text
    assert material['state'] == 'NOT_GENERATED'
    assert material['source_duties']['claims'] == []
    assert material['source_duties']['unassessed_source_ranges']


def test_negative_and_temporal_proposition_remain_qualified_analysis_interpretation():
    material = prepare(uncorrected('私はノートに書かなかった。'))
    claim = material['source_duties']['claims'][0]
    assert material['graph_scope'] == 'ANALYSIS_SOURCE_GROUNDED_INTERPRETATION'
    assert claim['proposition']['actor'] == 'SELF'
    assert claim['proposition']['polarity'] == 'negative'
    assert claim['proposition']['modality'] == 'fact'
    assert claim['proposition']['temporal_scope'] == 'past'
    assert material['coverage']['interpretation_status'] == 'UNASSESSED'
    assert 'RECORD_ORDER_TO_EVENT_ORDER' in material['source_duties']['forbidden_promotions']


def test_source_transplant_and_future_clock_do_not_get_material_identity():
    saved = saved_update()
    request = _request(saved, include_context=False, analysis_source_only=True)
    stale = copy.deepcopy(saved)
    stale['original']['memo'] += '私は日程を決めた。'
    with pytest.raises(AnalysisSourceError, match='emlis_analysis_source_binding_invalid'):
        prepare(stale, request=request)
    with pytest.raises(AnalysisSourceError, match='emlis_analysis_as_of_not_after_source'):
        prepare(saved, as_of=saved['original']['created_at'] + '+00:00')
    with pytest.raises(AnalysisSourceError, match='emlis_analysis_future_source'):
        prepare(saved, as_of='2026-10-03T11:59:59+00:00')


def test_owner_clock_and_source_prefix_are_committed_without_using_generated_body():
    saved = saved_update()
    first = prepare(saved)
    changed_output = copy.deepcopy(saved)
    changed_output['events'][0]['payload']['text'] = 'DIFFERENT_GENERATED_OBSERVATION'
    assert prepare(changed_output) == first
    assert prepare(saved, owner='different-authenticated-owner')['material_ref'] != first['material_ref']
    assert prepare(saved, as_of='2026-10-03T12:00:01+00:00')['material_ref'] != first['material_ref']
    uncorrected_saved = copy.deepcopy(saved); uncorrected_saved['events'] = []
    other = prepare(uncorrected_saved)
    assert other['source_prefix_ref'] != first['source_prefix_ref']
    assert other['record_version'] == first['record_version']
