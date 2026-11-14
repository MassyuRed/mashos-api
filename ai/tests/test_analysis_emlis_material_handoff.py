"""Actual Emlis SQL -> Analysis admission/provider -> immutable saved map.

The HTTP/model replies are synthetic; no model-quality claim follows from
these source, lifecycle and cross-core consumption checks.
"""
import copy
import json
from pathlib import Path
from uuid import uuid4

import httpx
import pytest

import analysis_cumulative_service as cumulative
import analysis_model_source as sources
import analysis_semantic_map as semantic
import emlis_thread_store
from emlis_thread_service import EmlisThreadService, Q3_PROFILE
from cocolon_meaning_experience_engine.natural_reply import NaturalReply
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as admission
from cocolon_meaning_experience_engine.cores.analysis.source_adapter import AnalysisSourceError
from test_analysis_cumulative_model_source import sql_source
from test_analysis_interpretation_correction_sources import sql_script
from test_emlis_interpretation_correction import correct
from test_emlis_natural_reply_application import BODY
from test_emlis_q2_application import run

MIGRATION = '20261114123000_analysis_emlis_material_handoff.sql'


@pytest.fixture
def handoff_case(sql_source, monkeypatch):
    db, rpc = sql_source
    for name in ('20261114032520_analysis_interpretation_correction_sources.sql',
                 '20261107071033_analysis_semantic_map_wire.sql', MIGRATION):
        sql_script(db, name)
    user, parent = str(uuid4()), str(uuid4())
    assert 'code' not in db.query('insert into auth.users values ($1)', [user])
    assert 'code' not in db.query("insert into public.profiles values ($1,'free')", [user])
    assert 'code' not in db.query("insert into public.emotions values ($1,$2,(now()-interval '1 second') at time zone 'UTC',"
        "$3,$4,array['仕事'],array['平穏'],$5)", [parent, user,
        '私は仕事を続けたい。くるくるした余韻が残った。', '私は費用を記録した。',
        json.dumps([dict(type='平穏', strength='medium')])])
    monkeypatch.setattr(emlis_thread_store, 'sb_post_rpc', db.rpc)
    calls = []
    async def source(material):
        calls.append(material)
        return NaturalReply(BODY, 'synthetic-emlis-model', material.source_prefix_ref)
    service = EmlisThreadService(runtime_profile=Q3_PROFILE, natural_reply_source=source)
    return db, rpc, user, parent, service, calls


def prepare(case):
    _, rpc, user, _, _, _ = case
    snapshot = run(rpc('analysis_cumulative_source_snapshot', dict(p_user_id=user)))
    return snapshot, semantic.prepare_semantic_map(user, snapshot,
        prompt_version=admission.SEMANTIC_MAP_SOURCE_DUTIES_PROFILE)


def packet(field, quote):
    return dict(schema_version=semantic.MODEL_SCHEMA,
        overview=dict(title='記録に書いた希望', summary='本人がこの入力に記した希望を読みます。'),
        nodes=[dict(node_id='n1', node_kind='SELF_POSITION', title='家族を守りたい',
            summary='家族を守りたいと書かれています。',
            explanation='この記述を、この入力で本人が示した希望として読みます。',
            perspective='SELF', unknowns=[], evidence=[dict(field=field, quote=quote)])], edges=[])


def test_saved_material_reaches_actual_analysis_provider_and_monthly_reread_without_generation(handoff_case, monkeypatch):
    db, rpc, user, parent, service, emlis_calls = handoff_case
    first = run(service.start(user, parent))
    run(correct(service, user, first,
        explanation='「私は仕事を続けたい」ではなく「私は家族を守りたい」です。'))
    snapshot, prepared = prepare(handoff_case)
    raw, = snapshot['members']
    observation = [e for e in raw['events'] if e['kind'] == 'OBSERVATION'][-1]
    saved = observation['payload']['artifact']['analysis_material']
    assert saved == raw['thread']['data']['analysis_material']
    assert 'text' not in observation['payload']
    assert BODY not in json.dumps(observation['payload'], ensure_ascii=False)
    material = json.loads(prepared.material_json)
    handoff, = material['emlis_source_materials']
    assert handoff['material_ref'] == saved['material_ref']
    assert handoff['graph_scope'] == 'ANALYSIS_SOURCE_GROUNDED_INTERPRETATION'
    assert handoff['source_updates'][0]['operation'] == 'REVISE'
    assert all(a['target_ref'] in {n['source_node_ref'] for n in handoff['source_node_bindings']}
               for a in handoff['annotations'])
    assert handoff['coverage']['unassessed_source_ranges']
    assert '私は仕事を続けたい' not in ''.join(f['text'] for f in material['fields'])
    assert any('くるくるした余韻が残った' in f['text'] for f in material['fields'])
    field = next(f for f in material['fields'] if f['text'] == '私は家族を守りたい')
    assert field['source_role'] == 'USER_INTERPRETATION_CORRECTION'
    assert material['source_duties']['claims']
    # Ordinary generated wording does not become source identity or evidence.
    assert 'code' not in db.query("update public.emlis_thread_events set payload="
        "jsonb_set(payload,'{text}',to_jsonb('ALTERED_GENERATED_TEXT_ONLY'::text)) where id=$1",
        [observation['id']])
    assert run(rpc('analysis_cumulative_source_snapshot', dict(p_user_id=user)))['guard'] == snapshot['guard']
    acquired = []
    def handler(request):
        messages = json.loads(request.content)['messages']
        actual = json.loads(messages[1]['content'])
        acquired.append(actual)
        assert {k:v for k,v in actual.items() if k != 'analysis_as_of'} == {
            k:v for k,v in material.items() if k != 'analysis_as_of'}
        assert '本人が新しく述べた事実' in messages[0]['content']
        assert actual['emlis_source_materials'][0]['material_ref'] == saved['material_ref']
        return httpx.Response(200, json=dict(model='synthetic-analysis-model', choices=[dict(
            finish_reason='stop', message=dict(role='assistant', content=json.dumps(
                packet(field['field'], '私は家族を守りたい'), ensure_ascii=False)))]))
    source = sources.SelfHostedSemanticAnalysisModelSource(
        endpoint='https://synthetic-analysis.invalid/v1/chat/completions',
        model='synthetic-analysis-model', api_key='synthetic-private-key',
        transport=httpx.MockTransport(handler),
        semantic_prompt_version=admission.SEMANTIC_MAP_SOURCE_DUTIES_PROFILE)
    created = run(cumulative.ensure_map(user, model_source=source))
    assert created['has_visible_content'] and len(acquired) == 1
    monthly = run(cumulative.ensure_map(user, monthly=True, model_source=source))
    old_meta = copy.deepcopy(monthly['meta'])
    assert run(cumulative.ensure_map(user, ensure=False, model_source=source))['meta'] == created['meta']
    # A later ordinary source change cannot rewrite an already captured month.
    assert 'code' not in db.query("update public.emotions set memo=memo||'私は日程を決めた。' where id=$1", [parent])
    monkeypatch.setattr(admission, 'prepare_emlis_analysis_material', lambda *a, **kw:
        (_ for _ in ()).throw(AssertionError('saved/monthly read must not derive or generate')))
    assert run(cumulative.ensure_map(user, monthly=True, model_source=source))['meta'] == old_meta
    assert len(acquired) == 1 and len(emlis_calls) == 2


@pytest.mark.parametrize('mutation', ['graph', 'thread_copy', 'clock', 'prefix'])
def test_current_forged_material_never_reaches_analysis_writer(handoff_case, mutation):
    _, _, user, parent, service, _ = handoff_case
    run(service.start(user, parent))
    snapshot, _ = prepare(handoff_case)
    raw = snapshot['members'][0]
    artifact = [e for e in raw['events'] if e['kind'] == 'OBSERVATION'][-1]['payload']['artifact']
    if mutation == 'graph':
        artifact['analysis_material']['graph']['nodes'][0]['visible_label'] = 'INVENTED_PERSON_FACT'
        raw['thread']['data']['analysis_material'] = copy.deepcopy(artifact['analysis_material'])
    elif mutation == 'thread_copy':
        raw['thread']['data']['analysis_material']['material_ref'] = 'forged'
    elif mutation == 'clock':
        raw['thread']['data']['natural_meaning_as_of'] = '2099-01-01T00:00:00+00:00'
    else:
        raw['thread']['source_prefix_ref'] = 'foreign-source-prefix'
    with pytest.raises(AnalysisSourceError, match='analysis_emlis_material_binding_invalid'):
        semantic.prepare_semantic_map(user, snapshot,
            prompt_version=admission.SEMANTIC_MAP_SOURCE_DUTIES_PROFILE)


def test_legacy_snapshot_and_request_identity_stay_exact_without_private_handoff(sql_source, monkeypatch):
    db, rpc = sql_source
    sql_script(db, '20261114032520_analysis_interpretation_correction_sources.sql')
    user, parent = str(uuid4()), str(uuid4())
    db.query('insert into auth.users values ($1)', [user])
    db.query("insert into public.profiles values ($1,'free')", [user])
    db.query("insert into public.emotions values ($1,$2,(now()-interval '1 second') at time zone 'UTC',"
        "'私は仕事を続けたい。','',array['仕事'],array['平穏'],$3)",
        [parent, user, json.dumps([dict(type='平穏', strength='medium')])])
    before = run(rpc('analysis_cumulative_source_snapshot', dict(p_user_id=user)))
    old_request = cumulative._cumulative_model_request(user, before)
    old_prepared = semantic.prepare_semantic_map(user, before)
    sql_script(db, MIGRATION)
    after = run(rpc('analysis_cumulative_source_snapshot', dict(p_user_id=user)))
    assert before['members'] == after['members'] and before['guard'] == after['guard']
    # The real clock naturally advances. Hold the exact original request
    # clock to demonstrate that absent metadata did not alter its identity.
    after.update(now=before['now'], period_start=before['period_start'], period_end=before['period_end'])
    new_request = cumulative._cumulative_model_request(user, after)
    new_prepared = semantic.prepare_semantic_map(user, after)
    assert old_request == new_request
    assert old_prepared.request_ref == new_prepared.request_ref
    assert old_prepared.material_json == new_prepared.material_json


def test_actual_history_bound_prefix_is_rederived_and_changed_context_drops_only_the_derivative(handoff_case):
    db, rpc, user, parent, service, _ = handoff_case
    db.query("update public.profiles set subscription_tier='plus' where id=$1", [user])
    past = str(uuid4())
    db.query("insert into public.emotions values ($1,$2,(now()-interval '1 day') at time zone 'UTC',"
        "'私は仕事を続けたい。','',array['仕事'],array['平穏'],$3)",
        [past, user, json.dumps([dict(type='平穏', strength='medium')])])
    run(service.start(user, parent))
    snapshot, prepared = prepare(handoff_case)
    raw = next(r for r in snapshot['members'] if r['original']['id'] == parent)
    assert raw['thread']['data']['context_guards']
    assert json.loads(prepared.material_json)['emlis_source_materials']
    db.query("update public.emotions set memo=memo||'私は日程を決めた。' where id=$1", [past])
    fresh = run(rpc('analysis_cumulative_source_snapshot', dict(p_user_id=user)))
    current = semantic.prepare_semantic_map(user, fresh,
        prompt_version=admission.SEMANTIC_MAP_SOURCE_DUTIES_PROFILE)
    material = json.loads(current.material_json)
    assert 'emlis_source_materials' not in material
    assert len(material['records']) == 2
    assert any('私は日程を決めた' in f['text'] for f in material['fields'])
