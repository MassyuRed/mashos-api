"""Direct owner corrections through Emlis, v24 and DeepInsight storage."""
import json
from uuid import uuid4

import httpx
import pytest

import analysis_cumulative_service as cumulative
from test_analysis_interpretation_correction_sources import MIGRATION, sql_script, sql_snapshot
from test_emlis_natural_reply_application import natural_case
from test_emlis_q2_application import run
from test_emlis_q3_application import qdb


@pytest.fixture(scope='module')
def direct_correction_migrations(qdb):
    for name in ('20261003134440_analysis_observed_artifacts.sql', '20261004041627_analysis_period_comparison.sql',
                 '20261101080144_cumulative_watashi_map.sql', MIGRATION, '20261114123000_analysis_emlis_material_handoff.sql',
                 '20261121132000_deep_insight_questions.sql', '20261121134000_deep_insight_grounded_questions.sql',
                 '20261121195000_deep_insight_skipped_emlis_questions.sql',
                 '20261122142000_deep_insight_effective_emlis_answers.sql',
                 '20261122145000_deep_insight_effective_emlis_corrections.sql'):
        sql_script(qdb, name)


@pytest.mark.usefixtures('direct_correction_migrations')
@pytest.mark.parametrize('legacy, writer_mode', [
    (False, 'disabled'), (True, 'disabled'), (False, 'compact'), (False, 'compact_history'), (False, 'saved_v1'),
])
def test_no_answer_direct_feeling_correction_uses_saved_policy_on_retry(natural_case, qdb, monkeypatch,
        legacy, writer_mode):
    import emlis_thread_service as threads
    import emlis_thread_store
    from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as admission
    from cocolon_meaning_experience_engine.deep_insight_question import generate_question, prepare_question_material
    from cocolon_meaning_experience_engine.emlis_thread_contracts import DIRECT_FEELING_CORRECTION_POLICY
    from cocolon_meaning_experience_engine import natural_reply
    from cocolon_meaning_experience_engine.natural_reply import NaturalReply
    from test_emlis_interpretation_correction import correct

    user, parent, service, calls = natural_case
    original, replacement = 'つらかったんです', '私は不安だった'
    explanation = f'「{original}」ではなく「{replacement}」です。'
    service.natural_context_update_enabled = writer_mode != 'disabled'
    memo = original + '。' if service.natural_context_update_enabled else original
    qdb.query("update public.profiles set subscription_tier='premium' where id=$1", [user])
    qdb.query("update public.emotions set memo=$2,memo_action='',emotions=array['悲しみ'],"
        "emotion_details=$3,receive_emlis_questions=false where id=$1",
        [parent, memo, json.dumps([dict(type='悲しみ', strength='medium')], ensure_ascii=False)])
    if writer_mode == 'compact_history':
        for index in range(4):
            past_id = str(uuid4())
            qdb.query("insert into public.emotions(id,user_id,created_at,memo,memo_action,category,emotions,emotion_details)"
                " values ($1,$2,(now()-interval '1 day') at time zone 'UTC',$3,'',array['仕事'],array['悲しみ'],$4)",
                [past_id, user, f'過去の場面{index}はつらかった。', json.dumps([dict(type='悲しみ', strength='medium')])])
        qdb.query("insert into public.emlis_frame_feedback(user_id,source_emotion_id,frame_key,frame_ref,status)"
                  " values ($1,$2,'past-frame','past-frame-reference','REJECTED')", [user, past_id])

    async def synthetic_reply(material):
        text = (replacement + 'と伝えてくださったんですね。' if calls
                else original + '、と書いてくださったんですね。')
        calls.append(material)
        return NaturalReply(text, 'isolated-direct-feeling', material.source_prefix_ref)

    service.natural_reply_source = synthetic_reply
    before = run(service.start(user, parent))
    assert (before['state'], before['body_state'], before['revision'], before['issued_count']) == (
        'COMPLETED', 'FINAL', 4, 0)
    if legacy:
        old_event = threads._event

        def legacy_event(kind, payload, thread, **kwargs):
            payload = {key: value for key, value in payload.items() if key != 'analysis_correction_policy'}
            return old_event(kind, payload, thread, **kwargs)

        monkeypatch.setattr(threads, '_event', legacy_event)

    failed = False

    async def fail_first_observation(name, payload, **kwargs):
        nonlocal failed
        if not failed and any(event['kind'] == 'OBSERVATION' for event in payload.get('p_events', [])):
            failed = True
            return httpx.Response(503, json={'code': '57P03'})
        return await qdb.rpc(name, payload, **kwargs)

    monkeypatch.setattr(emlis_thread_store, 'sb_post_rpc', fail_first_observation)
    with monkeypatch.context() as before_rollout:
        if writer_mode == 'saved_v1':
            prepare = natural_reply.prepare_natural_reply

            def legacy_writer(*args, **kwargs):
                if 'include_direct_feeling_correction' in kwargs:
                    kwargs['include_direct_feeling_correction'] = False
                return prepare(*args, **kwargs)

            before_rollout.setattr(natural_reply, 'prepare_natural_reply', legacy_writer)
        pending = run(correct(service, user, before, text=original, explanation=explanation))
    assert failed and pending['can_retry'] and len(calls) == 2
    written_material = json.loads(calls[-1].analysis_material_json)
    frozen = run(service.store.read(user, input_id=parent))
    operation, = [e for e in frozen['events'] if e['payload'].get('stage') == 'INTERPRETATION_CORRECTION']
    assert operation['payload'].get('analysis_correction_policy') == (None if legacy else DIRECT_FEELING_CORRECTION_POLICY)
    assert 'analysis_correction_policy' not in operation['payload']['source']
    receipt = [e for e in frozen['events'] if e['payload'].get('stage') == 'NATURAL_REPLY_RECEIVED'][-1]
    messages = natural_reply.build_natural_reply_messages(calls[-1])
    if writer_mode in {'compact', 'compact_history'}:
        assert receipt['payload']['writer_context_version'] == natural_reply.DIRECT_FEELING_CORRECTION_CONTEXT_VERSION
        assert [m['role'] for m in messages] == ['system', 'user']
        body = json.loads(messages[-1]['content'])
        assert body.pop('本人が訂正した気持ち') == replacement
        if writer_mode == 'compact_history':
            writer = json.loads(calls[-1].writer_material_json)
            current, *past = body['records']
            assert current == {'scope': 'CURRENT_INPUT', 'metadata': writer['records'][0]['metadata']}
            assert len(past) == 4 and all(row['scope'] == 'PAST_RECORD' for row in past)
            assert past == writer['records'][1:]
            assert body['user_frame_feedback'] == writer['user_frame_feedback']
            feedback, = body['user_frame_feedback']
            record = body['records'][feedback['record'] - 1]
            assert record['active_fields'][0]['text'] == '過去の場面3はつらかった。'
            assert feedback['status'] == 'REJECTED'
            assert '過去の気持ちや本人判断を今回の気持ちに足さず' in messages[0]['content']
        else:
            assert body == {}
        assert '質問、助言、箇条書きは入れず' in messages[0]['content']
        assert original not in json.dumps(messages, ensure_ascii=False)
    elif writer_mode == 'saved_v1':
        assert receipt['payload']['writer_context_version'] == natural_reply.SOURCE_CONTEXT_VERSION
        assert 'この初回の受口' in messages[0]['content']
        assert json.loads(messages[-1]['content'])['records'][0]['source_updates'][0]['target_text'] == original
    restarted = threads.EmlisThreadService(runtime_profile=threads.Q3_PROFILE,
        natural_reply_source=synthetic_reply, natural_context_update_enabled=False)
    final = run(restarted.action(user, pending['thread_id'], action='retry_response',
        expected_revision=pending['revision'], idempotency_key='resume-direct-interpretation',
        operation_id=pending['operation_id']))
    assert len(calls) == 2 and final['state'] == 'COMPLETED' and final['body_state'] == 'FINAL'
    assert final['issued_count'] == 0 and final['answer_saved'] is False
    assert run(restarted.get(user, parent))['current_observation'] == final['current_observation']
    saved = run(restarted.store.read(user, input_id=parent))
    assert next(e for e in saved['events'] if e['id'] == receipt['id']) == receipt
    observation = [e for e in saved['events'] if e['kind'] == 'OBSERVATION'][-1]['payload']['artifact']
    assert observation['writer_messages_sha256'] == receipt['payload']['writer_messages_sha256']
    assert observation['analysis_material'] == saved['thread']['data']['analysis_material'] == written_material
    saved['context'] = run(restarted.store.related_context(user, parent,
        context_guards=saved['thread']['data']['context_guards']))
    assert admission.admit_saved_emlis_analysis_material(saved, owner_scope=user, tier='premium',
        as_of=saved['now']) == written_material
    if writer_mode == 'compact_history':
        return

    phase = sql_snapshot(qdb, user)
    request = cumulative._cumulative_model_request(user, phase)

    def prepare_map():
        return admission.prepare_analysis_semantic_map(request, phase,
            prompt_version=admission.SEMANTIC_MAP_OCCURRENCE_V24_PROFILE)

    def question_context():
        return qdb.query('select public.deep_insight_candidate_context($1) as value',
                        [user], 'service_role')['rows'][0]['value']

    context = question_context()
    if legacy:
        assert written_material['reason_codes'] == ['analysis_correction_target_unresolved']
        assert written_material['coverage']['active_state'] == 'PENDING'
        with pytest.raises(admission.AnalysisSemanticMapNoMaterial) as excluded:
            prepare_map()
        assert excluded.value.coverage['exclusion_reasons'] == {'analysis_correction_target_unresolved': 1}
        assert not context['material']['records']
        return

    assert written_material['coverage']['active_state'] == 'RESOLVED'
    assert written_material['original_record']['memo'] == memo
    start, end = explanation.index(replacement), explanation.index(replacement) + len(replacement)
    map_input = prepare_map()
    (_, map_text, map_record, map_ref), = map_input.fields
    assert (map_text, map_record, map_ref.scalar_start, map_ref.scalar_end) == (replacement, parent, start, end)
    map_wire = json.loads(map_input.material_json)
    assert original not in json.dumps(map_wire, ensure_ascii=False)
    assert not map_wire.get('answered_feeling_circumstances')
    assert map_wire['fields'][0]['source_role'] == 'USER_INTERPRETATION_CORRECTION'
    record, = context['material']['records']
    correction, = record['emlis_corrections']
    assert record['id'] == parent and record['thought'] is None and not record['emlis_answered_questions']
    assert (correction['id'], correction['text'], correction['scalar_start']) == (operation['id'], replacement, start)
    prepared, sources = prepare_question_material(context['material'], lane='records', theme=None)
    key, = sources
    assert sources[key].text == replacement and sources[key].field == 'correction'

    plan = dict(focus='REASON', source=key, quote=replacement, condition='')
    responses = iter((dict(plan, decision='ask', ask='訂正で述べた不安の理由'),
        dict(question='不安だったのは、どんな理由からですか？'),
        dict(plan, verdict='accept', premise_supported=True, new_information=True)))

    async def synthetic_question_stage(system, payload):
        assert original not in json.dumps(payload, ensure_ascii=False)
        return json.dumps(next(responses), ensure_ascii=False)

    candidate = run(generate_question(prepared, sources, material=context['material'],
        generate=synthetic_question_stage)).candidate
    assert candidate and candidate.receipt['field'] == 'correction'
    assert (candidate.receipt['start'], candidate.receipt['end']) == (start, end)
    issued = qdb.query("select public.deep_insight_issue_grounded($1,"
        "(public.deep_insight_state($1)->>'day')::date,'records',null,$2,$3,$4,$5,$6::jsonb) as value",
        [user, candidate.text, candidate.question_key, candidate.text_key, context['guard'],
         json.dumps(candidate.receipt)], 'service_role')
    question = issued['rows'][0]['value']['question']
    assert question['question_text'] == candidate.text
    answer_text = '急に予定が変わり、準備が間に合うか心配でした。'
    answered = qdb.query('select public.deep_insight_answer($1,$2,$3) as value',
        [user, question['id'], answer_text], 'service_role')
    assert 'code' not in answered, answered
    reloaded, = [row for row in question_context()['material']['prior'] if row['id'] == question['id']]
    assert reloaded['answer_text'] == answer_text and reloaded['grounding_receipt'] == candidate.receipt


@pytest.mark.parametrize('memo, selected, quoted, replacement', [
    ('私は仕事を続けたい', '私は仕事を続けたい', '私は仕事を続けたい', '私は家族を守りたい'),
    ('つらかったんです。つらかったんです。', 'つらかったんです', 'つらかったんです', '私は不安だった'),
    ('つらかったんです', 'つらかったんですね', 'つらかったんです', '私は不安だった'),
    ('つらかったんです', 'つらかったんです', 'とてもつらかった', '私は不安だった'),
])
def test_direct_feeling_policy_only_marks_exact_whole_short_feeling(natural_case, qdb,
        memo, selected, quoted, replacement):
    from cocolon_meaning_experience_engine.natural_reply import NaturalReply
    from test_emlis_interpretation_correction import correct

    user, parent, service, calls = natural_case
    service.natural_questions_enabled = False
    service.natural_context_update_enabled = False
    qdb.query("update public.emotions set memo=$2,memo_action='' where id=$1", [parent, memo])

    async def synthetic_reply(material):
        text = (replacement if calls else selected) + '、と書いてくださったんですね。'
        calls.append(material)
        return NaturalReply(text, 'isolated-direct-feeling', material.source_prefix_ref)

    service.natural_reply_source = synthetic_reply
    first = run(service.start(user, parent))
    result = run(correct(service, user, first, text=selected,
        explanation=f'「{quoted}」ではなく「{replacement}」です。'))
    assert result['correction_saved'] is True and len(calls) == 2
    stored = run(service.store.read(user, input_id=parent))
    operation, = [e for e in stored['events'] if e['payload'].get('stage') == 'INTERPRETATION_CORRECTION']
    assert 'analysis_correction_policy' not in operation['payload']
