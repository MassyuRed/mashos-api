"""Canonical Emlis source proof through isolated SQL into the v24 provider wire."""
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
    from test_emlis_q2_application import answer

    user, parent, service, _ = natural_case
    original, circumstance = 'つらかったんです', '会議がうまくできませんでした'
    qdb.query("update public.emotions set memo=$2,memo_action='' where id=$1", [parent, original])
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
