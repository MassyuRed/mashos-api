"""Same-owner, as-of contextual sources for the normal Emlis reply writer."""

import json
from uuid import uuid4

import httpx
import pytest

import kokoro_weather_service as weather
from cocolon_meaning_experience_engine.natural_reply import build_natural_reply_messages
from test_analysis_cumulative import OWNER
from test_analysis_cumulative_model_source import sql_source
from test_analysis_interpretation_correction_sources import sql_script
from test_analysis_premium_structure_relations import COEXISTENCE, _artifact, saved_map_source
from test_emlis_natural_reply_application import natural_case
from test_emlis_q2_application import run
from test_emlis_q3_application import qdb


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
def test_prior_map_and_chart_reach_only_premium_writer_and_invalidate_saved_reply(
        natural_case, qdb, monkeypatch, tier):
    user, parent, service, calls = natural_case
    qdb.query('update public.profiles set subscription_tier=$2 where id=$1', [user, tier])
    service.premium_context_enabled = True
    service.natural_questions_enabled = False
    map_ref = {'id': str(uuid4()), 'version': 1, 'guard': 'bound-map-sources', 'visibility': 'same',
               'period_end': '2026-01-01T00:00:00Z'}
    structures = [{'title': '期限を守る余地', 'description': '提出と助け合いを両立できる時間を見ています。'}]
    exact_map = {'ref': map_ref, 'generated_at': '2026-01-01T00:00:00Z', 'structures': structures}
    exact_graph = {'as_of_jst': '2026-11-28T14:00:00+09:00', 'recorded_days': [
        {'jst_date': '2026-11-27', 'record_count': 1, 'recorded_emotion_weights': {'不安': 2}}]}
    source_calls = []
    map_cached = True

    async def prior_map(owner, entry):
        assert owner == user and entry == parent
        source_calls.append('map')
        return exact_map if map_cached else None

    async def current_prior_map(owner, entry, binding):
        assert owner == user and entry == parent
        return binding == map_ref

    async def prior_graph(owner, before):
        assert owner == user and before.tzinfo is not None
        source_calls.append('chart')
        return exact_graph, 'source-version'

    monkeypatch.setattr(service.store, 'prior_map_context', prior_map)
    monkeypatch.setattr(service.store, 'prior_map_is_current', current_prior_map)
    monkeypatch.setattr(weather, 'build_prior_kokoro_observation', prior_graph)
    result = run(service.start(user, parent))
    assert result['current_observation'] and len(calls) == 1
    messages = build_natural_reply_messages(calls[0])
    material = json.loads(messages[-1]['content'])
    assert 'prior_premium_context' not in json.loads(calls[0].material_json)
    assert run(service.get(user, parent))['current_observation'] == result['current_observation']
    if tier != 'premium':
        assert not source_calls and 'prior_premium_context' not in material
        return

    assert material['prior_premium_context']['kokoro_graph'] == exact_graph
    assert material['prior_premium_context']['watashi_map']['structures'] == structures
    snapshot = run(service.store.read(user, input_id=parent))
    stored = next(e['payload'] for e in snapshot['events'] if e['kind'] == 'OBSERVATION')
    assert stored['premium_context_guard'] == {'watashi_map': map_ref, 'kokoro_graph': 'source-version'}
    assert 'premium_context_guard' not in json.dumps(result)
    assert '今の理由、改善や悪化を示しません' in messages[0]['content']

    map_cached = False
    assert run(service.get(user, parent)) == result
    map_ref['visibility'] = 'record-made-secret'
    changed = run(service.get(user, parent))
    assert changed['current_observation'] is None and changed['body_state'] == 'CONTEXT_CHANGED'
    assert all(e['kind'] != 'OBSERVATION' for e in changed['timeline'])
    map_ref['visibility'] = 'same'
    qdb.query("update public.profiles set subscription_tier='plus' where id=$1", [user])
    assert run(service.get(user, parent))['current_observation'] is None
    assert len(calls) == 1


def test_graph_uses_only_prior_dated_non_secret_emotion_records(monkeypatch):
    from datetime import datetime, timezone

    cutoff = datetime(2026, 11, 28, 15, 0, tzinfo=timezone.utc)

    def row(offset, date, emotion, *, secret=False, strength='medium'):
        return dict(id=str(offset), user_id=OWNER, created_at=date,
            emotion_details=[{'type': emotion, 'strength': strength}], is_secret=secret)

    rows = [
        row(1, '2026-11-27T14:59:56Z', '自己理解'),
        row(2, '2026-11-27T14:59:57Z', '不安'),
        row(3, '2026-11-27T15:00:00Z', '平穏', strength='weak'),
        row(4, '2026-11-28T14:30:00Z', '怒り', secret=True),
        row(5, '2026-11-28T15:00:00Z', '喜び'),
        row(6, '2026-11-28T15:30:00Z', '喜び'),
    ]

    async def get(path, *, params, **_kwargs):
        assert path == '/rest/v1/emotions'
        assert params['user_id'] == 'eq.' + OWNER
        assert 'is_secret.eq.false' in params['and']
        assert 'created_at.lt.2026-11-28T15:00:00Z' in params['and']
        return httpx.Response(200, json=[] if 'or(created_at' in params['and'] else rows)

    monkeypatch.setattr(weather, 'sb_get', get)
    first, guard = run(weather.build_prior_kokoro_observation(OWNER, cutoff))
    assert first['recorded_days'] == [
        dict(jst_date='2026-11-27', record_count=1, recorded_emotion_weights={'不安': 2}),
        dict(jst_date='2026-11-28', record_count=1, recorded_emotion_weights={'平穏': 1}),
    ]
    rows[3]['emotion_details'][0]['strength'] = 'weak'
    assert run(weather.build_prior_kokoro_observation(OWNER, cutoff)) == (first, guard)
    rows[2]['emotion_details'][0]['strength'] = 'strong'
    assert run(weather.build_prior_kokoro_observation(OWNER, cutoff))[1] != guard
    rows[2]['is_secret'] = True
    assert len(run(weather.build_prior_kokoro_observation(OWNER, cutoff))[0]['recorded_days']) == 1


def test_prior_map_read_revalidates_its_saved_cohort_with_existing_sql(saved_map_source):
    db, rpc, other, originals, snapshot = saved_map_source
    assert 'code' not in db.query('alter table public.emotions add column is_secret boolean not null default false')
    for migration in ('20261125205000_analysis_premium_structure_relations.sql',
                      '20261127080000_analysis_withhold_unaccepted_map.sql',
                      '20261128053622_emlis_prior_map_context.sql'):
        sql_script(db, migration)
    assert 'code' not in db.query("update public.profiles set subscription_tier='premium' where id in ($1,$2)", [OWNER, other])
    artifact, coverage, _ = _artifact(COEXISTENCE, snapshot)
    evidence = dict(artifact.private_evidence(), coverage=coverage, source_record_refs=[row['id'] for row in originals])
    graph = artifact.safe_projection(authenticated_owner_scope=OWNER)
    report_id = run(rpc('analysis_cumulative_commit', dict(p_user_id=OWNER, p_guard=snapshot['guard'],
        p_artifact_id=artifact.artifact_id, p_private_evidence=evidence, p_projection=graph,
        p_text='比較した条件', p_start=snapshot['period_start'], p_end=snapshot['period_end'])))
    entry = str(uuid4())
    assert 'code' not in db.query("insert into public.emotions values "
        "($1,$2,clock_timestamp() at time zone 'UTC','今日は提出した。','',array['仕事'],array['平穏'],'[]'::jsonb,true)",
        [entry, OWNER])

    def read(owner, input_id):
        args = [owner, input_id]
        return db.query('select public.emlis_thread_prior_map_context($1,$2) as result', args,
                        'service_role')['rows'][0]['result']

    previous = read(OWNER, entry)
    assert previous['ref']['id'] == report_id
    assert previous['structures'] and read(other, entry) is None
    assert read(OWNER, originals[0]['id']) is None
    acl = db.query("select has_function_privilege('anon','public.emlis_thread_prior_map_context(uuid,uuid)','execute') a, "
                   "has_function_privilege('authenticated','public.emlis_thread_prior_map_context(uuid,uuid)','execute') b")
    assert acl['rows'] == [{'a': False, 'b': False}]

    def reauthorize(owner=OWNER):
        ref = previous['ref']
        return db.query('select public.emlis_thread_prior_map_is_current($1,$2,$3,$4,$5,$6) as result',
            [owner, entry, report_id, ref['period_end'], ref['guard'], ref['visibility']],
            'service_role')['rows'][0]['result']

    assert reauthorize() is True and reauthorize(other) is False
    assert 'code' not in db.query('delete from public.analysis_observed_artifacts where id=$1', [report_id])
    assert read(OWNER, entry) is None and reauthorize() is True
    assert 'code' not in db.query('update public.emotions set is_secret=true where id=$1', [originals[0]['id']])
    assert reauthorize() is False
    assert 'code' not in db.query('update public.emotions set is_secret=false where id=$1', [originals[0]['id']])
    assert 'code' not in db.query('update public.emotions set memo=$2 where id=$1', [originals[0]['id'], '判断を見直した。'])
    assert reauthorize() is False
