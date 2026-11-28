"""Same-owner, as-of contextual sources for the normal Emlis reply writer."""

import json
from uuid import uuid4

import httpx
import pytest

import kokoro_weather_service as weather
from cocolon_meaning_experience_engine.natural_reply import (
    INITIAL_OBSERVATION_FOLLOW_CONTEXT_VERSION, NaturalReply, QWEN_9B_NATURAL_ALIAS,
    build_natural_reply_messages,
)
from test_analysis_cumulative import OWNER
from test_analysis_cumulative_model_source import sql_source
from test_analysis_interpretation_correction_sources import sql_script
from test_analysis_premium_structure_relations import COEXISTENCE, _artifact, saved_map_source
from test_emlis_natural_question_application import THREE, natural_questions
from test_emlis_natural_reply_application import _active_application_owner, insert_past, natural_case
from test_emlis_q2_application import answer, run
from test_emlis_q3_application import qdb


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
@pytest.mark.parametrize('initial_follow', [False, True])
def test_prior_map_and_chart_reach_only_premium_writer_and_invalidate_saved_reply(
        natural_case, qdb, monkeypatch, tier, initial_follow):
    user, parent, service, calls = natural_case
    qdb.query('update public.profiles set subscription_tier=$2 where id=$1', [user, tier])
    service.premium_context_enabled = True
    service.natural_questions_enabled = False
    if initial_follow:
        memo = '見本帳にあった青い縞が大好きでした。'
        qdb.query('update public.emotions set memo=$2 where id=$1', [parent, memo])
        service.initial_observation_follow_enabled = True

        async def follow_source(material):
            calls.append(material)
            return NaturalReply(f'「{memo}」\n\nどの模様に惹かれていたのか、Emlisも聞けてうれしいです。',
                                QWEN_9B_NATURAL_ALIAS, material.source_prefix_ref)

        follow_source.model = QWEN_9B_NATURAL_ALIAS
        service.natural_reply_source = follow_source
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
    if initial_follow:
        writer = json.loads(calls[0].writer_material_json)
        assert writer['source_context_version'] == INITIAL_OBSERVATION_FOLLOW_CONTEXT_VERSION
        assert material['本人の気持ちの言葉'] == '大好き'
        assert material['本人が書いた好みの時制'] == '過去'
        assert '今聞いたEmlis' in messages[0]['content']
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


@pytest.mark.parametrize('tier,related_history', [
    ('free', True), ('plus', True), ('premium', True), ('premium', False),
])
def test_entitled_context_in_active_thread_phases(natural_questions, qdb, monkeypatch, tier, related_history):
    from cocolon_meaning_experience_engine.natural_reply import (
        ISSUED_ANSWER_RECEPTION_VERSION, QWEN_9B_NATURAL_ALIAS, SelfHostedNaturalReplySource)

    user, parent, _, _ = natural_questions(tier=tier, memo=THREE)
    past_memo = '友人に褒められたのに、あの時は嬉しくなかった。'
    insert_past(qdb, user, '昨日は白い鳥を見に行った。')
    past = insert_past(qdb, user, past_memo) if related_history else None
    map_facts = {'ref': {'id': str(uuid4())}, 'generated_at': '2026-01-01T00:00:00Z',
        'structures': [{'title': '自分で選ぶ', 'description': '選べるときの方が安心して任せられます。'}]}
    chart = {'as_of_jst': '2026-11-28T14:00:00+09:00', 'recorded_days': [
        {'jst_date': '2026-11-27', 'record_count': 1, 'recorded_emotion_weights': {'不安': 2}}]}
    messages, read_attempts = [], []

    async def prior_map(owner, input_id):
        assert owner == user and input_id == parent
        read_attempts.append('map')
        return map_facts

    async def prior_chart(owner, cutoff):
        assert owner == user and cutoff.tzinfo is not None
        read_attempts.append('chart')
        return chart, 'chart-sources'

    async def no_deep_insight(owner, input_id, guarded_history):
        assert owner == user and input_id == parent
        assert all(row[0] == past for row in guarded_history)

    def transport(request):
        messages.append(json.loads(request.content)['messages'])
        reply = ('言葉を受け取ったときの気持ちは、単純ではなかったのですね。' if len(messages) == 1 else
                 '褒められた言葉の重さも、ここで聞かせてくださったのですね。')
        return httpx.Response(200, json={'model': QWEN_9B_NATURAL_ALIAS, 'choices': [
            {'finish_reason': 'stop', 'message': {'role': 'assistant', 'content': reply}},
        ]})

    provider = SelfHostedNaturalReplySource(endpoint='https://model.invalid/v1/chat/completions',
        model=QWEN_9B_NATURAL_ALIAS, api_key='synthetic-only', transport=httpx.MockTransport(transport))
    monkeypatch.setenv('COCOLON_EMLIS_PREMIUM_CONTEXT', 'true')
    service = _active_application_owner(monkeypatch, provider, 'paid')
    monkeypatch.setattr(service.store, 'prior_map_context', prior_map)
    monkeypatch.setattr(service.store, 'related_deep_insight_answer', no_deep_insight)
    monkeypatch.setattr(weather, 'build_prior_kokoro_observation', prior_chart)
    initial = run(service.start(user, parent))
    refined = run(answer(service, user, initial, 'その時は重かった。'))
    continued = run(service.action(user, initial['thread_id'], action='continue',
        expected_revision=refined['revision'], idempotency_key='advance-one'))
    skipped = run(service.action(user, initial['thread_id'], action='skip',
        question_id=continued['pending_question']['question_id'], expected_revision=continued['revision'],
        idempotency_key='skip-after-answer'))
    assert skipped['state'] == 'COMPLETED' and skipped['answer_saved']
    assert run(service.get(user, parent)) == skipped
    assert len(messages) == 3
    materials = [json.loads(row[-1]['content']) for row in messages]
    assert (past_memo in messages[0][-1]['content']) is (tier != 'free' and related_history)
    if tier != 'premium':
        assert not read_attempts and all('prior_premium_context' not in row for row in materials)
        return
    assert read_attempts
    assert all(row['prior_premium_context']['kokoro_graph'] == chart and
               row['prior_premium_context']['watashi_map']['structures'] == map_facts['structures']
               for row in materials)
    assert all('その時は重かった。' in row[-1]['content'] for row in messages[1:])
    assert all('昨日は白い鳥を見に行った。' not in row[-1]['content'] for row in messages)
    if not related_history:
        saved = run(service.store.read(user, input_id=parent))
        receipts = [e['payload'] for e in saved['events'] if e['payload'].get('stage') == 'NATURAL_REPLY_RECEIVED']
        assert [e['writer_context_version'] for e in receipts[1:]] == [ISSUED_ANSWER_RECEPTION_VERSION] * 2
        assert all(material['本人の補足'] == 'その時は重かった。' for material in materials[1:])


def test_paid_narrowed_answer_uses_premium_context_without_reintroducing_independent_action(
        natural_case, qdb, monkeypatch):
    from cocolon_meaning_experience_engine.natural_reply import PAID_RECEIVED_ANSWER_CONTEXT_VERSION, NaturalReply

    user, parent, service, _ = natural_case
    qdb.query("update public.profiles set subscription_tier='premium' where id=$1", [user])
    memo, action = '褒められたのに、嬉しくなかった。', '会議で発表した。'
    qdb.query('update public.emotions set memo=$2,memo_action=$3 where id=$1', [parent, memo, action])
    insert_past(qdb, user, memo)
    reply = '褒められた時に嬉しくなかったんですね。その時は怖さを感じていたことも伝わってきました。'
    prompt_materials = []

    async def provider(material):
        prompt_materials.append(material)
        return NaturalReply(reply, 'synthetic-provider', material.source_prefix_ref)

    async def unavailable(*_args):
        return None

    async def graph(*_args):
        return {'recorded_days': [{'jst_date': '2026-11-27', 'record_count': 1}]}, 'graph-ref'

    service = _active_application_owner(monkeypatch, provider, 'paid')
    service.premium_context_enabled = True
    monkeypatch.setattr(service.store, 'prior_map_context', unavailable)
    monkeypatch.setattr(service.store, 'related_deep_insight_answer', unavailable)
    monkeypatch.setattr(weather, 'build_prior_kokoro_observation', graph)
    initial = run(service.start(user, parent))
    refined = run(answer(service, user, initial, 'その時は怖かった。'))
    assert refined['body_state'] == 'REFINED' and run(service.get(user, parent)) == refined
    writer = json.loads(prompt_materials[1].writer_material_json)
    assert writer['source_context_version'] == PAID_RECEIVED_ANSWER_CONTEXT_VERSION
    system, wire = build_natural_reply_messages(prompt_materials[1])
    supplied = json.loads(wire['content'])
    assert supplied['今回の場面']['補足'] == 'その時は怖かった。'
    assert supplied['prior_premium_context'] == writer['prior_premium_context']
    assert len(supplied['past_user_records']) == 1 and supplied['past_user_records'][0]['scope'] == 'PAST_RECORD'
    assert action not in wire['content'] and initial['pending_question']['text'] not in wire['content']
    assert '今回の返事は本人が答えた場面に沿います' in system['content']


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
