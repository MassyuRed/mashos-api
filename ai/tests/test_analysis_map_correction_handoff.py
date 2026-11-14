"""Person map correction -> real Analysis evidence/current -> old month.

Provider responses are synthetic. These checks establish source and lifecycle
behavior, not a real model's interpretation quality.
"""
import copy
import json
from unittest.mock import AsyncMock
from uuid import uuid4

import httpx
import pytest

import analysis_cumulative_service as cumulative
import analysis_map_correction_service as corrections
import analysis_model_source as sources
import analysis_observed_service as observed
import analysis_semantic_map as semantic
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as admission
from cocolon_meaning_experience_engine.cores.analysis.map_interpretation_correction import qualify_map_correction
from test_analysis_cumulative import OWNER, source_snapshot
from test_analysis_cumulative_model_source import sql_source
from test_analysis_interpretation_correction_sources import sql_script
from test_analysis_semantic_map import response
from test_emlis_q2_application import run

EXPLANATION = ('その推定は違います。会議が終わっていなかったので、その時だけ返事を待ちました。'
               '普段から発言を避けているわけではありません。')
OLD = '二つの記録から、普段から発言を避ける傾向があると読みました。'


def old_packet():
    return dict(schema_version=semantic.MODEL_SCHEMA,
        overview=dict(title='記録の読み取り', summary='二つの記録の読みを並べています。'),
        nodes=[dict(node_id='n1', node_kind='SELF_POSITION', title='発言を避ける傾向',
            summary='発言を避けているように読めます。', explanation=OLD,
            perspective='SELF', unknowns=[], evidence=[
                dict(field=1, quote='私は意見を言わなかった'), dict(field=2, quote='私は資料を調べた')])], edges=[])


def changed_packet(field):
    return dict(schema_version=semantic.MODEL_SCHEMA,
        overview=dict(title='本人の説明から読み直したこと', summary='本人が説明した、その場の事情を分けて読みます。'),
        nodes=[dict(node_id='n1', node_kind='STATE_CONTEXT', title='会議の進行を待っていた場面',
            summary='本人の説明では、その時だけ返事を待っていました。',
            explanation='普段の特徴と決めず、その場の進行に関する本人の説明から読み直します。',
            perspective='SELF', unknowns=[], evidence=[dict(field=field, quote=EXPLANATION)])], edges=[])


@pytest.fixture
def map_case(sql_source, monkeypatch):
    db, rpc = sql_source
    monkeypatch.setenv('COCOLON_ANALYSIS_OBSERVED_MODE', 'development')
    monkeypatch.setattr(observed, '_rpc', rpc)
    for name in ('20261107071033_analysis_semantic_map_wire.sql',
                 '20261114032520_analysis_interpretation_correction_sources.sql',
                 '20261114120000_analysis_if_route_artifacts.sql',
                 '20261114123000_analysis_emlis_material_handoff.sql',
                 '20261114132000_analysis_map_interpretation_corrections.sql'):
        sql_script(db, name)
    db.query('insert into auth.users values ($1)', [OWNER])
    db.query("insert into public.profiles values ($1,'premium')", [OWNER])
    for i, row in enumerate(source_snapshot(2)['members']):
        original = row['original']
        original.update(memo='私は意見を言わなかった。' if i == 0 else '私は資料を調べた。',
            emotion_details=[dict(type='平穏', strength='medium')])
        result = db.query('insert into public.emotions values ($1,$2,$3,$4,$5,$6,$7,$8)',
            [original['id'], OWNER, original['created_at'], original['memo'], '',
             original['category'], original['emotions'], json.dumps(original['emotion_details'])])
        assert 'code' not in result, result
    return db, rpc


def snapshot(rpc):
    return run(rpc('analysis_cumulative_source_snapshot', dict(p_user_id=OWNER)))


def save_old(rpc, snap):
    prepared = semantic.prepare_semantic_map(OWNER, snap,
        prompt_version=admission.SEMANTIC_MAP_SOURCE_DUTIES_PROFILE)
    artifact, coverage = semantic.build_semantic_map(prepared, response(prepared, old_packet()))
    private = artifact.private_evidence(); private['coverage'] = coverage
    private['source_record_refs'] = [r['original']['id'] for r in snap['members']]
    identity = run(rpc('analysis_cumulative_commit', dict(p_user_id=OWNER, p_guard=snap['guard'],
        p_artifact_id=artifact.artifact_id, p_private_evidence=private,
        p_projection=artifact.safe_projection(authenticated_owner_scope=OWNER),
        p_text=artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'],
        p_start=snap['period_start'], p_end=snap['period_end'])))
    return artifact, identity, prepared


def command(artifact):
    return dict(artifact_ref=artifact.reference, kind='node', ref='n1', field='explanation',
        target_text=OLD, explanation=EXPLANATION, idempotency_key='person-corrects-map')


def test_real_submit_person_explanation_is_actual_evidence_in_new_current_and_old_month_is_fixed(map_case, monkeypatch):
    db, rpc = map_case
    before = snapshot(rpc)
    artifact, old_id, old_prepared = save_old(rpc, before)
    monthly = run(cumulative.ensure_map(OWNER, monthly=True))
    sql_script(db, '20261114133000_analysis_map_correction_handoff.sql')
    no_metadata = snapshot(rpc)
    assert no_metadata['members'] == before['members'] and no_metadata['guard'] == before['guard']
    no_metadata.update(now=before['now'], period_start=before['period_start'], period_end=before['period_end'])
    unchanged = semantic.prepare_semantic_map(OWNER, no_metadata,
        prompt_version=admission.SEMANTIC_MAP_SOURCE_DUTIES_PROFILE)
    assert unchanged == old_prepared
    old_private = artifact.private_evidence()
    assert 'map_correction_sources' not in old_private['graph']
    receipt = run(corrections.submit_map_correction(OWNER, command(artifact)))
    assert receipt['source_state'] == 'ACTIVE'
    fresh = snapshot(rpc)
    assert fresh['guard'] != before['guard'] and fresh['members'] == before['members']
    prepared = semantic.prepare_semantic_map(OWNER, fresh,
        prompt_version=admission.SEMANTIC_MAP_SOURCE_DUTIES_PROFILE)
    material = json.loads(prepared.material_json)
    field = next(f for f in material['fields'] if f['source_role'] == 'USER_ANALYSIS_MAP_CORRECTION')
    assert field['record'] is None and field['record_refs'] == [1, 2]
    assert field['text'] == EXPLANATION
    source = qualify_map_correction(OWNER, fresh['map_corrections'][0])
    assert source.envelope.raw_utf8 == EXPLANATION.encode()
    assert OLD.encode() not in source.envelope.raw_utf8
    acquired = []
    def handler(request):
        actual = json.loads(json.loads(request.content)['messages'][1]['content'])
        acquired.append(actual)
        actual_field = next(f for f in actual['fields'] if f['source_role'] == 'USER_ANALYSIS_MAP_CORRECTION')
        return httpx.Response(200, json=dict(model='synthetic-map-model', choices=[dict(finish_reason='stop',
            message=dict(role='assistant', content=json.dumps(changed_packet(actual_field['field']), ensure_ascii=False)))]))
    provider = sources.SelfHostedSemanticAnalysisModelSource(endpoint='https://synthetic-map.invalid/v1/chat/completions',
        model='synthetic-map-model', api_key='synthetic-private-key', transport=httpx.MockTransport(handler),
        semantic_prompt_version=admission.SEMANTIC_MAP_SOURCE_DUTIES_PROFILE)
    current = run(cumulative.ensure_map(OWNER, force=True, model_source=provider))
    assert len(acquired) == 1 and current['report_id'] != old_id
    assert 'その時だけ' in current['content_text'] and OLD not in current['content_text']
    stored = db.query('select private_evidence from public.analysis_observed_artifacts where id=$1',
        [current['report_id']])['rows'][0]['private_evidence']
    assert stored['source_members'] == old_private['source_members']
    node, = stored['graph']['nodes']
    assert set(node['record_refs']) == {r['original']['id'] for r in before['members']}
    assert node['evidence_badge_count'] == 1
    assert all(r['field_path'] == 'explanation' and r['source_envelope_id'] == source.envelope.envelope_id
               for r in node['evidence_refs'])
    evidence = run(cumulative.map_evidence(OWNER, current['report_id'], 'n1'))['items']
    assert len(evidence) == 2
    assert all(row['evidence_scope'] == 'MAP_CORRECTION_CONTEXT' and row['answers'] == [] for row in evidence)
    assert all(row['map_corrections'][0]['text'] == EXPLANATION for row in evidence)
    assert all(row['map_corrections'][0]['version_state'] == 'CURRENT' for row in evidence)
    monkeypatch.setattr(admission, 'prepare_analysis_semantic_map', lambda *a, **kw:
        (_ for _ in ()).throw(AssertionError('saved reader must not generate')))
    assert run(cumulative.ensure_map(OWNER, monthly=True))['meta'] == monthly['meta']
    assert artifact.private_evidence() == old_private


def test_unused_truncated_and_unchanged_target_corrections_are_not_adopted(map_case):
    db, rpc = map_case
    old, _, _ = save_old(rpc, snapshot(rpc))
    sql_script(db, '20261114133000_analysis_map_correction_handoff.sql')
    run(corrections.submit_map_correction(OWNER, command(old)))
    prepared = semantic.prepare_semantic_map(OWNER, snapshot(rpc),
        prompt_version=admission.SEMANTIC_MAP_SOURCE_DUTIES_PROFILE)
    field = next(f for f in json.loads(prepared.material_json)['fields'] if f['source_role'] == 'USER_ANALYSIS_MAP_CORRECTION')
    for defect in ('unused', 'truncated', 'unchanged'):
        packet = changed_packet(field['field'])
        if defect == 'unused':
            packet['nodes'][0]['evidence'] = [dict(field=1, quote='私は意見を言わなかった')]
        elif defect == 'truncated':
            packet['nodes'][0]['evidence'][0]['quote'] = '普段から発言を避けている'
        else:
            packet['nodes'][0]['explanation'] = OLD
        with pytest.raises(ValueError):
            semantic.build_semantic_map(prepared, response(prepared, packet))


def test_saved_if_keeps_its_pinned_correction_prefix_but_raw_edit_invalidates(map_case, monkeypatch):
    from fastapi import HTTPException
    import analysis_if_route_service as if_service
    import analysis_if_route_store as if_store
    from test_analysis_if_routes import response as if_response
    db, rpc = map_case
    old, _, _ = save_old(rpc, snapshot(rpc))
    sql_script(db, '20261114133000_analysis_map_correction_handoff.sql')
    monkeypatch.setattr(if_store, '_rpc', rpc)
    def body(base_ref, key):
        return dict(base_observed_map_ref=base_ref, branch_point_id='n1',
            branch_intent_text='次は意見を伝えてみたい。', constraint_texts=['相手の話を遮りたくない。'],
            constraints_confirmed=True, requested_candidate_count=1, idempotency_key=key)
    provider = AsyncMock(side_effect=lambda prepared: if_response(prepared))
    hypothetical = run(if_service.create_scenario_set(OWNER, body(old.reference, 'before-map-correction'),
        model_source=provider))
    saved = run(if_service.save_intent(OWNER, dict(source_scenario_set_ref=hypothetical['scenario_set_ref'],
        selected_scenario_ref=hypothetical['projection']['scenarios'][0]['scenario_ref'],
        user_note='この方向を考えておきたいです。', idempotency_key='saved-before-map-correction')))
    run(corrections.submit_map_correction(OWNER, command(old)))
    assert run(if_service.get_artifact(OWNER, 'saved_intent', saved['id']))['projection'] == saved['projection']
    assert run(if_service.get_artifact(OWNER, 'scenario_set', hypothetical['id']))['projection'] == hypothetical['projection']
    # An unrelated new source is outside the old IF/Saved cohort.
    added = str(uuid4())
    db.query("insert into public.emotions values ($1,$2,now() at time zone 'UTC','私は日程を決めた。','',"
        "array['仕事'],array['平穏'],$3)", [added, OWNER, json.dumps([dict(type='平穏', strength='medium')])])
    assert run(if_service.get_artifact(OWNER, 'saved_intent', saved['id']))['projection'] == saved['projection']
    fresh = snapshot(rpc)
    prepared = semantic.prepare_semantic_map(OWNER, fresh,
        prompt_version=admission.SEMANTIC_MAP_SOURCE_DUTIES_PROFILE)
    field = next(f for f in json.loads(prepared.material_json)['fields'] if f['source_role'] == 'USER_ANALYSIS_MAP_CORRECTION')
    artifact, coverage = semantic.build_semantic_map(prepared, response(prepared, changed_packet(field['field'])))
    private = artifact.private_evidence(); private['coverage'] = coverage
    private['source_record_refs'] = [r['original']['id'] for r in fresh['members']]
    run(rpc('analysis_cumulative_commit', dict(p_user_id=OWNER, p_guard=fresh['guard'],
        p_artifact_id=artifact.artifact_id, p_private_evidence=private,
        p_projection=artifact.safe_projection(authenticated_owner_scope=OWNER),
        p_text=artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'],
        p_start=fresh['period_start'], p_end=fresh['period_end'], p_force=True)))
    newer = run(if_service.create_scenario_set(OWNER, body(artifact.reference, 'after-map-correction'),
        model_source=provider))
    second = dict(command(artifact), field='summary',
        target_text=artifact.safe_projection(authenticated_owner_scope=OWNER)['nodes'][0]['summary'],
        explanation='この場面では、終了を待つというより、発言する順番を待っていました。',
        idempotency_key='second-map-correction')
    run(corrections.submit_map_correction(OWNER, second))
    # Neither the empty nor one-correction historical prefix is retrofitted.
    assert run(if_service.get_artifact(OWNER, 'saved_intent', saved['id']))['projection'] == saved['projection']
    assert run(if_service.get_artifact(OWNER, 'scenario_set', newer['id']))['projection'] == newer['projection']
    assert provider.await_count == 2
    original_id = fresh['members'][0]['original']['id']
    db.query("update public.emotions set memo=memo||'私は日程を決めた。' where id=$1", [original_id])
    with pytest.raises(HTTPException) as rejected:
        run(if_service.get_artifact(OWNER, 'saved_intent', saved['id']))
    assert rejected.value.status_code == 404
    with pytest.raises(HTTPException):
        run(if_service.get_artifact(OWNER, 'scenario_set', newer['id']))


def test_same_words_in_an_unrelated_record_are_not_a_blanket_ban(map_case):
    db, rpc = map_case
    snap = snapshot(rpc)
    other = snap['members'][1]['original']['id']
    db.query('update public.emotions set memo=$2 where id=$1', [other, OLD])
    snap = snapshot(rpc)
    prepared = semantic.prepare_semantic_map(OWNER, snap,
        prompt_version=admission.SEMANTIC_MAP_SOURCE_DUTIES_PROFILE)
    first = old_packet()
    first['nodes'][0].update(summary=OLD, evidence=[dict(field=1, quote='私は意見を言わなかった')])
    artifact, coverage = semantic.build_semantic_map(prepared, response(prepared, first))
    private = artifact.private_evidence(); private['coverage'] = coverage
    private['source_record_refs'] = [r['original']['id'] for r in snap['members']]
    run(rpc('analysis_cumulative_commit', dict(p_user_id=OWNER, p_guard=snap['guard'],
        p_artifact_id=artifact.artifact_id, p_private_evidence=private,
        p_projection=artifact.safe_projection(authenticated_owner_scope=OWNER),
        p_text=artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'],
        p_start=snap['period_start'], p_end=snap['period_end'])))
    sql_script(db, '20261114133000_analysis_map_correction_handoff.sql')
    run(corrections.submit_map_correction(OWNER, dict(command(artifact), field='summary')))
    fresh = semantic.prepare_semantic_map(OWNER, snapshot(rpc),
        prompt_version=admission.SEMANTIC_MAP_SOURCE_DUTIES_PROFILE)
    field = next(f for f in json.loads(fresh.material_json)['fields'] if f['source_role'] == 'USER_ANALYSIS_MAP_CORRECTION')
    packet = changed_packet(field['field'])
    packet['nodes'].append(dict(node_id='n2', node_kind='TARGET_MEANING', title='別記録に本人が残した文',
        summary=OLD, explanation='別の記録に本人が残した文として表示しています。', perspective='SELF',
        unknowns=[], evidence=[dict(field=2, quote=OLD)]))
    updated, _ = semantic.build_semantic_map(fresh, response(fresh, packet))
    assert updated.safe_projection(authenticated_owner_scope=OWNER)['nodes'][1]['summary'] == OLD
