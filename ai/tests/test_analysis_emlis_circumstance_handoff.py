"""Canonical Emlis source proof through isolated SQL into v24 and DeepInsight."""
import json
from dataclasses import replace
from uuid import uuid4

import pytest

import analysis_cumulative_service as cumulative
from cocolon_meaning_experience_engine.cores.analysis.source_adapter import (
    AnalysisSourceError, freeze_analysis_sources,
)
from test_analysis_interpretation_correction_sources import MIGRATION, sql_script, sql_snapshot
from test_emlis_natural_reply_application import natural_case
from test_emlis_q2_application import run
from test_emlis_q3_application import qdb


def test_saved_circumstance_retains_both_original_ranges_for_v24(natural_case, qdb):
    from analysis_plan_source_choices import restore_view
    from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as admission
    from test_emlis_interpretation_correction import correct
    from test_emlis_q2_application import answer

    user, parent, service, _ = natural_case
    original, circumstance = 'つらかったんです', '会議がうまくできませんでした'
    qdb.query("update public.emotions set memo=$2,memo_action='',emotions=array['悲しみ'],emotion_details=$3 where id=$1",
              [parent, original, json.dumps([dict(type='悲しみ', strength='medium')], ensure_ascii=False)])
    for name in ('20261003134440_analysis_observed_artifacts.sql', '20261004041627_analysis_period_comparison.sql',
                 '20261101080144_cumulative_watashi_map.sql', MIGRATION,
                 '20261114123000_analysis_emlis_material_handoff.sql'):
        sql_script(qdb, name)

    def prepare(phase):
        request = cumulative._cumulative_model_request(user, phase)
        return admission.prepare_analysis_semantic_map(request, phase,
            prompt_version=admission.SEMANTIC_MAP_OCCURRENCE_V24_PROFILE)

    initial = run(service.start(user, parent))
    before = json.loads(prepare(sql_snapshot(qdb, user)).material_json)
    assert [f['text'] for f in before['fields']] == [original]
    final = run(answer(service, user, initial, circumstance))
    assert final['body_state'] == 'REFINED' and final['meaning_updated']
    snapshot_value = sql_snapshot(qdb, user)
    ready = prepare(snapshot_value)
    material, _, _ = restore_view(json.loads(ready.messages()[1]['content']))
    fields = {field['field']: field for field in material['fields']}
    assert [f['text'] for f in fields.values()] == [original, circumstance]
    relation, = material['answered_feeling_circumstances']
    for name, role, expected in (('feeling', 'ORIGINAL_INPUT', original),
                                  ('circumstance', 'SUPPLEMENTAL_ANSWER', circumstance)):
        endpoint = relation[name]
        field = fields[endpoint['field']]
        start, end = endpoint['scalar_range']
        assert field['record'] == relation['record'] and field['source_role'] == role
        assert field['text'][start:end] == expected
    assert initial['pending_question']['text'] not in json.dumps(material, ensure_ascii=False)
    assert json.loads(admission.prepare_semantic_leaf(ready, (parent,)).material_json)[
        'answered_feeling_circumstances'] == [relation]

    request = cumulative._cumulative_model_request(user, snapshot_value)
    member, = request.members
    supplement, = member.supplements
    control = supplement.circumstance_control
    transplanted = replace(supplement, circumstance_control=replace(control,
        answer=replace(control.answer, question_id='a-different-question')))
    with pytest.raises(AnalysisSourceError, match='analysis_supplement_binding_invalid'):
        freeze_analysis_sources(replace(request, members=(replace(member, supplements=(transplanted,)),)))

    second = str(uuid4())
    qdb.query('insert into public.emotions (id,user_id,created_at,memo,memo_action,category,emotions,emotion_details) '
              'select $2,user_id,created_at,$3,\'\',category,emotions,emotion_details from public.emotions where id=$1',
              [parent, second, '悲しかったです。'])
    initial_second = run(service.start(user, second))
    answered_unknown = run(answer(service, user, initial_second, '分かりません。'))
    assert answered_unknown['answer_assessment'] == 'RESOLVED' and not answered_unknown['meaning_updated']
    both_ready = prepare(sql_snapshot(qdb, user))
    second_leaf = json.loads(admission.prepare_semantic_leaf(both_ready, (second,)).material_json)
    assert [field['text'] for field in second_leaf['fields']] == ['悲しかったです。']
    assert not second_leaf.get('answered_feeling_circumstances')

    replacement = '私は不安だった'
    explanation = f'「{original}」ではなく「{replacement}」です。'
    revised = run(correct(service, user, final, text=final['current_observation']['text'],
        explanation=explanation))
    assert revised['body_state'] == 'FINAL'
    corrected = prepare(sql_snapshot(qdb, user))
    corrected_leaf = json.loads(admission.prepare_semantic_leaf(corrected, (parent,)).material_json)
    assert [(field['source_role'], field['text']) for field in corrected_leaf['fields']] == [
        ('SUPPLEMENTAL_ANSWER', circumstance), ('USER_INTERPRETATION_CORRECTION', replacement),
    ]
    assert not corrected_leaf.get('answered_feeling_circumstances')
    corrected_wire, _, _ = restore_view(json.loads(corrected.messages()[1]['content']))
    assert original not in json.dumps(corrected_wire, ensure_ascii=False)

    from cocolon_meaning_experience_engine.deep_insight_question import generate_question, prepare_question_material

    def question_context(owner=user):
        stored = qdb.query('select public.deep_insight_candidate_context($1) as value', [owner], 'service_role')
        assert 'code' not in stored, stored
        return stored['rows'][0]['value']

    def deep_insight_record():
        return next(r for r in question_context()['material']['records'] if r['id'] == parent)

    for name in ('20261121132000_deep_insight_questions.sql',
                 '20261121134000_deep_insight_grounded_questions.sql',
                 '20261121195000_deep_insight_skipped_emlis_questions.sql'):
        sql_script(qdb, name)
    legacy_record = deep_insight_record()
    assert legacy_record['thought'] == original and not legacy_record['emlis_answered_questions']
    sql_script(qdb, '20261122142000_deep_insight_effective_emlis_answers.sql')
    old_context = question_context()
    old_record = deep_insight_record()
    current_answer, = old_record['emlis_answered_questions']
    assert old_record['thought'] is None and 'emlis_corrections' not in old_record
    assert current_answer['id'] == supplement.source_id and current_answer['answer'] == circumstance
    assert current_answer['question_id'] == initial['pending_question']['question_id']
    assert current_answer['question'] is None

    sql_script(qdb, '20261122145000_deep_insight_effective_emlis_corrections.sql')
    context = question_context()
    current_record = deep_insight_record()
    current_correction, = current_record['emlis_corrections']
    assert {k: v for k, v in current_record.items() if k != 'emlis_corrections'} == old_record
    map_correction, = [source for source in corrected.frozen.sources
        if source.envelope.source_role == 'USER_INTERPRETATION_CORRECTION']
    assert current_correction['id'] == map_correction.envelope.source_record_id
    assert current_correction['text'] == replacement
    assert current_correction['scalar_start'] == explanation.index(replacement)
    unaffected = next(r for r in old_context['material']['records'] if r['id'] == second)
    assert next(r for r in context['material']['records'] if r['id'] == second) == unaffected

    material = context['material']
    prepared, sources = prepare_question_material(material, lane='records', theme=None)
    correction_key, = [key for key, source in sources.items() if source.field == 'correction']
    before_prepared, before_sources = prepare_question_material(old_context['material'], lane='records', theme=None)
    assert {key: source for key, source in sources.items() if key != correction_key} == before_sources
    assert circumstance in {source.text for source in before_sources.values()}
    assert prepared['sources'][correction_key]['source_role'] == 'USER_INTERPRETATION_CORRECTION'
    assert {key: value for key, value in prepared['sources'].items()
        if key != correction_key} == before_prepared['sources']
    sent = json.dumps(prepared, ensure_ascii=False)
    assert initial['pending_question']['text'] not in sent and original not in sent

    model_calls = []

    async def generate(system, payload):
        model_calls.append(system)
        assert original not in json.dumps(payload, ensure_ascii=False)
        if len(model_calls) == 1:
            return json.dumps(dict(decision='ask', focus='CONDITION', source=correction_key,
                quote=replacement, condition='', ask='不安を感じやすい場面'), ensure_ascii=False)
        if len(model_calls) == 2:
            return json.dumps(dict(question='どんなときにその不安を感じやすいですか？'), ensure_ascii=False)
        return json.dumps(dict(verdict='accept', focus='CONDITION', source=correction_key, quote=replacement,
            condition='', premise_supported=True, new_information=True), ensure_ascii=False)

    candidate = run(generate_question(prepared, sources, material=material, generate=generate)).candidate
    assert candidate and len(model_calls) == 3
    assert candidate.receipt['field'] == 'correction'
    assert explanation[candidate.receipt['start']:candidate.receipt['end']] == replacement

    def issue(owner, guard, receipt, *, role='service_role'):
        return qdb.query("select public.deep_insight_issue_grounded($1,"
            "(public.deep_insight_state($1)->>'day')::date,'records',null,$2,$3,$4,$5,$6::jsonb) as value",
            [owner, candidate.text, candidate.question_key, candidate.text_key, guard,
             json.dumps(receipt)], role)

    other = str(uuid4())
    assert 'code' not in qdb.query('insert into auth.users values ($1)', [other])
    assert 'code' not in qdb.query("insert into public.profiles values ($1,'free')", [other])
    assert question_context(other)['material']['records'] == []
    assert issue(other, question_context(other)['guard'], candidate.receipt)['code'] == '22023'
    assert issue(user, context['guard'], candidate.receipt, role='authenticated')['code'] == '42501'
    assert issue(user, old_context['guard'], candidate.receipt)['rows'][0]['value']['status'] == 'no_question'
    for change in (dict(start=0, end=len(replacement)), dict(source_version='0' * 64), dict(field='answer')):
        assert issue(user, context['guard'], {**candidate.receipt, **change})['code'] == '22023'

    issued = issue(user, context['guard'], candidate.receipt)
    assert 'code' not in issued, issued
    question = issued['rows'][0]['value']['question']
    assert question['question_text'] == candidate.text
    answer_text = '周りに相談できないときに不安になります。'
    answered = qdb.query('select public.deep_insight_answer($1,$2,$3) as value',
        [user, question['id'], answer_text], 'service_role')
    assert 'code' not in answered, answered

    # Only the latest resolved source projection can ground a new question.
    # An already issued question and its answer retain their saved identity.
    assert 'code' not in qdb.query("update public.emlis_input_threads set data=data-'analysis_material' "
        'where id=$1', [revised['thread_id']])
    reloaded = next(row for row in question_context()['material']['prior'] if row['id'] == question['id'])
    assert reloaded['answer_text'] == answer_text and reloaded['grounding_receipt'] == candidate.receipt
    assert all(row['id'] != parent for row in question_context()['material']['records'])
