"""Saved person corrections must not disappear at the Analysis source boundary.

Model responses and auth are synthetic; SQL, source, compiler, artifact save,
monthly reread and evidence reconstruction use their actual owners.
"""
import copy
from dataclasses import asdict, replace
import json
from pathlib import Path
from uuid import UUID

import pytest
from astor_material_snapshots import _analysis_saved_member, AnalysisSavedSourceError
import analysis_cumulative_service as cumulative
from cocolon_meaning_experience_engine.emlis_thread_contracts import InterpretationCorrectionSource
from cocolon_meaning_experience_engine.cores.analysis.source_adapter import (
    _time, AnalysisObservedMapRequest, AnalysisSourceError, freeze_analysis_sources)
from cocolon_meaning_experience_engine.cores.analysis.intent_compiler import compile_observed_graph
from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import prepare_analysis_semantic_map
from emlis_thread_service import _request, NATURAL_REPLY_PROFILE, Q3_PROFILE
from test_analysis_saved_period import snapshot, OWNER, NOW, START, END
from test_emlis_q3_application import qdb
from test_emlis_natural_reply_application import natural_case
from test_emlis_interpretation_correction import correct
from test_emlis_q2_application import run

MIGRATION = '20261114032520_analysis_interpretation_correction_sources.sql'


def corrected(text='「私は仕事を続けたい」は取り消します。'):
    saved = snapshot()
    saved['thread'] = dict(id=str(UUID(int=201)), user_id=OWNER,
        original_emotion_id=saved['original']['id'], source_snapshot=copy.deepcopy(saved['original']),
        revision=2, issued_count=0, started_question_limit=3,
        data=dict(runtime_profile=Q3_PROFILE, response_profile=NATURAL_REPLY_PROFILE))
    request = _request(saved, include_context=False, analysis_source_only=True)
    source = InterpretationCorrectionSource('correction', saved['thread']['id'],
        request.emlis_thread.original_source_ref, 'observation', 'AI_TARGET_NOT_USER_EVIDENCE', text, NOW)
    saved['events'] = [dict(id='observation', thread_id=saved['thread']['id'], kind='OBSERVATION',
        payload=dict(text=source.target_text)),
        dict(id=source.correction_id, thread_id=saved['thread']['id'], kind='OPERATION',
        payload=dict(stage='INTERPRETATION_CORRECTION', source=asdict(source)))]
    return saved


def member(saved):
    return _analysis_saved_member(saved, owner=OWNER, input_id=saved['original']['id'],
        tier='plus', start=_time(START), end=_time(END), cumulative=True)


def frozen(saved):
    record, _ = member(saved)
    return freeze_analysis_sources(AnalysisObservedMapRequest('request', OWNER, START, END, (record,)))


@pytest.mark.parametrize('text,operation,remaining', [
    ('「私は仕事を続けたい」は取り消します。', 'WITHDRAW', '私は考えをノートに書いた'),
    ('「私は仕事を続けたい」ではなく「私は家族を守りたい」です。', 'REVISE', '私は家族を守りたい'),
])
def test_exact_person_explanation_uses_existing_clause_proof_and_keeps_unaffected_meaning(text, operation, remaining):
    saved = corrected(text)
    before = copy.deepcopy(saved)
    record, guard = member(saved)
    sources = frozen(saved)
    assert len(record.interpretation_corrections) == 1 and record.supplements == ()
    source = sources.sources[-1]
    assert source.envelope.source_role == 'USER_INTERPRETATION_CORRECTION'
    assert text.encode() in source.envelope.raw_utf8
    assert b'AI_TARGET_NOT_USER_EVIDENCE' not in source.envelope.raw_utf8
    graph = compile_observed_graph(sources)
    assert [u.operation for u in graph.source_updates] == [operation]
    labels = [n.visible_label for n in graph.nodes]
    assert '私は仕事を続けたい' not in labels and remaining in labels
    assert '私は考えをノートに書いた' in labels
    assert saved == before
    without = copy.deepcopy(saved); without['events'] = []
    assert member(without)[0] != record and member(without)[1] != guard


def test_unknown_explanation_is_preserved_pending_and_never_reuses_original_as_uncorrected():
    saved = corrected('仕事を続けたいのではなく、今はまだ決められません。')
    snap = dict(tier='plus', now=NOW, period_start=START, period_end=END,
        members=[saved, snapshot(2)], guard='analysis-db-cumulative-v1:'+'a'*64)
    artifact, coverage = cumulative.build_cumulative_map(OWNER, snap)
    assert artifact and coverage['processed_count'] == 1
    assert coverage['exclusion_reasons'] == {'analysis_interpretation_correction_pending': 1}
    assert saved['original']['id'] not in {r for n in artifact.graph.nodes for r in n.record_refs}
    request = cumulative._cumulative_model_request(OWNER, snap)
    prepared = prepare_analysis_semantic_map(request, snap)
    assert len(prepared.request.members) == 1
    assert json.loads(prepared.exclusion_reasons_json) == coverage['exclusion_reasons']
    assert 'AI_TARGET_NOT_USER_EVIDENCE' not in prepared.material_json
    assert prepared.source_request.members[0].interpretation_corrections[0].explanation


@pytest.mark.parametrize('mutation', ['foreign_record', 'edited_record', 'foreign_source', 'duplicate_source'])
def test_freeze_rejects_transplanted_or_stale_correction(mutation):
    record, _ = member(corrected())
    correction = record.interpretation_corrections[0]
    if mutation == 'foreign_record':
        other, _ = member(dict(corrected(), original=snapshot(2)['original'], thread=None, events=[]))
        record = replace(other, interpretation_corrections=(correction,))
    elif mutation == 'edited_record':
        original = json.loads(record.original_json); original['memo'] += '私は資料を読んだ。'
        from cocolon_meaning_experience_engine.cores.analysis.source_adapter import canonical_bytes, commitment
        record = replace(record, original_json=canonical_bytes(original).decode(), saved_record_version=commitment(original))
    elif mutation == 'foreign_source':
        record = replace(record, interpretation_corrections=(replace(correction, original_source_ref='foreign'),))
    else:
        record = replace(record, interpretation_corrections=(correction, correction))
    with pytest.raises(AnalysisSourceError, match='analysis_correction_binding_invalid'):
        freeze_analysis_sources(AnalysisObservedMapRequest('request', OWNER, START, END, (record,)))


@pytest.mark.parametrize('mutation', ['missing_target', 'duplicate_target', 'ambiguous_excerpt', 'future_target', 'wrong_id', 'other_owner'])
def test_saved_boundary_rejects_corrupt_target_or_owner(mutation):
    saved = corrected()
    if mutation == 'missing_target': saved['events'] = saved['events'][1:]
    elif mutation == 'duplicate_target': saved['events'].insert(0, copy.deepcopy(saved['events'][0]))
    elif mutation == 'ambiguous_excerpt': saved['events'][0]['payload']['text'] *= 2
    elif mutation == 'future_target': saved['events'].reverse()
    elif mutation == 'wrong_id': saved['events'][1]['id'] = 'different'
    else: saved['thread']['user_id'] = str(UUID(int=2))
    with pytest.raises(AnalysisSavedSourceError): member(saved)


def sql_script(db, name):
    sql = (Path(__file__).parents[2]/'supabase/migrations'/name).read_text()
    db.proc.stdin.write(json.dumps(dict(sql=sql, script=True))+'\n'); db.proc.stdin.flush()
    result = json.loads(db.proc.stdout.readline())
    assert 'code' not in result, result


def sql_snapshot(db, owner):
    result = db.query('select public.analysis_cumulative_source_snapshot($1) as value', [owner], 'service_role')
    assert 'code' not in result, result
    return result['rows'][0]['value']


def test_real_correction_sql_snapshot_save_month_reread_evidence_and_invalidation(natural_case, qdb):
    user, parent, service, calls = natural_case
    qdb.query("update public.emotions set memo='私は考えをノートに書いた。私は仕事を続けたい。' where id=$1", [parent])
    dto = run(service.start(user, parent))
    for name in ('20261003134440_analysis_observed_artifacts.sql', '20261004041627_analysis_period_comparison.sql',
                 '20261101080144_cumulative_watashi_map.sql'):
        sql_script(qdb, name)
    old = sql_snapshot(qdb, user)
    sql_script(qdb, MIGRATION)
    unchanged = sql_snapshot(qdb, user)
    assert unchanged['guard'] == old['guard'] and unchanged['members'] == old['members']
    dto = run(correct(service, user, dto,
        explanation='「私は仕事を続けたい」ではなく「私は家族を守りたい」です。'))
    snap = sql_snapshot(qdb, user)
    assert snap['guard'] != old['guard']
    assert len([e for e in snap['members'][0]['events'] if e['kind']=='OPERATION']) == 1
    assert len([e for e in snap['members'][0]['events'] if e['kind']=='OBSERVATION']) == 1
    artifact, coverage = cumulative.build_cumulative_map(user, snap)
    assert artifact and coverage['mapped_count'] == 1
    from analysis_observed_service import private_storage_evidence
    private = private_storage_evidence(artifact); private['coverage'] = coverage
    private['source_record_refs'] = [parent]
    projection = artifact.safe_projection(authenticated_owner_scope=user)
    text = artifact.safe_text_projection(authenticated_owner_scope=user)['text']
    result = qdb.query('select public.analysis_cumulative_commit($1,$2,$3,$4::jsonb,$5::jsonb,$6,$7,$8) as id',
        [user,snap['guard'],artifact.artifact_id,json.dumps(private),json.dumps(projection),text,
         snap['period_start'],snap['period_end']], 'service_role')
    assert 'code' not in result, result
    rid = result['rows'][0]['id']
    month = qdb.query('select snapshot_month from public.analysis_cumulative_months where artifact_id=$1',
        [rid], 'service_role')['rows'][0]['snapshot_month']
    def read_month():
        value = qdb.query('select public.analysis_cumulative_read($1,$2,false,60,0,$3) as value',
            [user,rid,month], 'service_role')
        assert 'code' not in value, value
        return value['rows'][0]['value']['items']
    monthly_before = read_month()
    assert monthly_before and monthly_before[0]['content_text'] == text
    node = next(n for n in projection['nodes'] if '家族' in n['visible_label'])
    result = qdb.query('select public.analysis_cumulative_evidence($1,$2,$3) as value',
        [user,rid,node['node_ref']], 'service_role')
    assert 'code' not in result, result
    evidence = cumulative._project_evidence(user, result['rows'][0]['value'])
    assert evidence[0]['answers'] == ['「私は仕事を続けたい」ではなく「私は家族を守りたい」です。']
    assert evidence[0]['version_state'] == 'CURRENT'
    count = len(calls)
    for _ in range(2):
        assert sql_snapshot(qdb,user)['guard'] == snap['guard']
        assert run(service.get(user,parent))['current_observation'] == dto['current_observation']
    assert len(calls) == count == 2
    # A later source edit invalidates current reuse, without rewriting the
    # already captured artifact and monthly pointer's original text/version.
    before = qdb.query('select content_text,private_evidence from public.analysis_observed_artifacts where id=$1',[rid],'service_role')['rows']
    qdb.query("update public.emotions set memo=memo || '私は資料を読んだ。' where id=$1",[parent])
    assert sql_snapshot(qdb,user)['guard'] != snap['guard']
    after = qdb.query('select content_text,private_evidence from public.analysis_observed_artifacts where id=$1',[rid],'service_role')['rows']
    assert after == before
    assert read_month() == monthly_before
