"""Natural acknowledgement/question/answer over the actual existing SQL owners.

The single configured provider is synthetic. These tests establish lifecycle,
source/update binding and persisted reread, not actual 4B response quality.
"""
import asyncio
import json
from uuid import uuid4

import httpx
import pytest

from test_emlis_q2_application import run, answer
from test_emlis_q3_application import qdb
from cocolon_meaning_experience_engine.natural_reply import NaturalReply
from emlis_thread_service import EmlisThreadService, Q3_PROFILE
from emlis_thread_store import ThreadStoreError
import emlis_thread_store


ONE = '褒められたのに、嬉しくなかった。'
THREE = ONE + '誘われたのに、悲しかった。頼まれたのに、寂しかった。'
ACK = '言葉を受け取ったときの気持ちは、単純ではなかったのですね。'
FINAL = 'まだはっきりしない部分も、そのままにしておけます。'


@pytest.fixture
def natural_questions(qdb, monkeypatch):
    def create(*, tier='free', memo=ONE, enabled=True):
        user, parent = str(uuid4()), str(uuid4())
        qdb.query('insert into auth.users values ($1)', [user])
        qdb.query('insert into public.profiles values ($1,$2)', [user, tier])
        qdb.query("insert into public.emotions values ($1,$2,now() at time zone 'UTC',$3,'',"
                  "array['仕事'],array['不安'],$4)",
                  [parent, user, memo, json.dumps([dict(type='不安', strength='medium')])])
        calls = []

        async def provider(material):
            data = json.loads(material.material_json)
            calls.append(data)
            stage = data.get('response_purpose', {}).get('stage', 'FINAL')
            answered = {
                'その時は重かった。': 'その時は重かったのですね。',
                'その時は怖かった。': 'その時は怖かったのですね。',
                'その時は苦しかった。': 'その時は苦しかったのですね。',
                'はい。': 'どんな意味として届いたのかは、今の言葉だけではまだ確かめきれていません。',
                '「嬉しくなかった」は誤りです。': '元の受け取り方について、訂正を伝えてくださったのですね。',
            }
            text = (ACK if stage == 'PRE_QUESTION' else
                    answered[data['current_answers'][-1]['text']] if stage == 'REFINED' else FINAL)
            return NaturalReply(text, 'synthetic-single-provider', material.source_prefix_ref)

        service = EmlisThreadService(runtime_profile=Q3_PROFILE,
            natural_reply_source=provider, natural_questions_enabled=enabled)
        return user, parent, service, calls

    monkeypatch.setattr(emlis_thread_store, 'sb_post_rpc', qdb.rpc)
    return create


def test_one_real_bound_question_answer_update_and_saved_natural_reread(natural_questions):
    user, parent, service, calls = natural_questions()
    initial = run(service.start(user, parent))
    assert initial['state'] == 'AWAITING_ANSWER', initial
    assert initial['body_state'] == 'PRE_QUESTION'
    assert initial['current_observation']['text'] == ACK
    assert initial['pending_question']['text'].endswith('どんな意味として届きましたか。')
    assert calls[0]['current_answers'] == []
    assert calls[0]['response_purpose'] == {'stage': 'PRE_QUESTION'}
    completed = run(answer(service, user, initial, 'その時は重かった。'))
    assert completed['state'] == 'COMPLETED', completed
    assert completed['body_state'] == 'REFINED' and completed['meaning_updated']
    assert completed['answer_assessment'] == 'RESOLVED'
    assert completed['current_observation']['text'] == 'その時は重かったのですね。'
    assert len(calls) == 2 and calls[1]['response_purpose'] == {'stage': 'REFINED'}
    assert calls[1]['current_answers'][0]['text'] == 'その時は重かった。'
    assert calls[1]['current_answers'][0]['ai_question_context'] == initial['pending_question']['text']
    meaning = calls[1]['answer_meaning']
    assert meaning['assessment'] == 'RESOLVED' and meaning['disposition'] == 'MATERIAL_UPDATE'
    assert any(fragment['source_role'] == 'SUPPLEMENTAL_ANSWER'
        and fragment['text'] == 'その時は重かった'
        for claim in meaning['active_claims'] for fragment in claim['source_fragments'])
    assert any('重かった' in claim['claim_anchor'] for claim in meaning['active_claims'])
    _assert_answer_projection_uses_actual_source_spans(calls[1])
    assert 'answer_meaning' not in json.dumps(completed)
    saved = run(service.store.read(user, input_id=parent))
    assert saved['original']['memo'] == ONE
    updates = [e for e in saved['events'] if e['kind'] == 'MEANING_UPDATE']
    assert len(updates) == 1
    assert updates[0]['payload']['source_prefix_ref'] == saved['thread']['source_prefix_ref']
    assert updates[0]['payload']['answer_update']['updates']

    class NoGeneration:
        def __getattr__(self, name):
            raise AssertionError('saved reread entered a generator/update owner')

    restarted = EmlisThreadService(runtime_profile=Q3_PROFILE, engine=NoGeneration())
    for _ in range(2):
        assert run(restarted.get(user, parent))['current_observation'] == completed['current_observation']
    replay = run(answer(service, user, initial, 'その時は重かった。'))
    assert replay['current_observation'] == completed['current_observation']
    assert len(calls) == 2


@pytest.mark.parametrize('tier', ('free', 'plus', 'premium'))
def test_each_plan_reuses_three_rounds_and_explicit_continue_without_extra_generation(natural_questions, tier):
    user, parent, service, calls = natural_questions(tier=tier, memo=THREE)
    dto = run(service.start(user, parent))
    assert dto['question_limit'] == 3
    questions = []
    for index, text in enumerate(('その時は重かった。', 'その時は怖かった。', 'その時は苦しかった。'), 1):
        assert dto['state'] == 'AWAITING_ANSWER', dto
        questions.append(dto['pending_question']['question_id'])
        dto = run(answer(service, user, dto, text, f'answer-{index}'))
        assert len(calls) == index + 1
        assert dto['answer_saved'] and dto['meaning_updated']
        assert text[4:-1] in dto['current_observation']['text']
        assert dto['issued_count'] == index
        if index < 3:
            assert dto['state'] == 'AWAITING_CONTINUE' and dto['can_continue'], dto
            dto = run(service.action(user, dto['thread_id'], action='continue',
                expected_revision=dto['revision'], idempotency_key=f'continue-{index}'))
            assert len(calls) == index + 1
        else:
            assert dto['state'] == 'COMPLETED' and not dto['can_continue']
    assert len(set(questions)) == 3
    saved = run(service.store.read(user, input_id=parent))
    assert len([e for e in saved['events'] if e['kind'] == 'MEANING_UPDATE']) == 3
    assert len([e for e in saved['events'] if e['kind'] == 'QUESTION']) == 3
    assert len([e for e in saved['events'] if e['kind'] == 'ANSWER']) == 3
    assert saved['original']['memo'] == THREE
    assert run(service.get(user, parent))['current_observation'] == dto['current_observation']
    assert len(calls) == 4


def test_off_setting_is_persisted_and_ordinary_no_question_still_uses_final(natural_questions):
    user, parent, service, calls = natural_questions(enabled=False)
    dto = run(service.start(user, parent))
    assert dto['state'] == 'COMPLETED' and dto['pending_question'] is None
    assert dto['current_observation']['text'] == FINAL
    assert 'response_purpose' not in calls[0]
    saved = run(service.store.read(user, input_id=parent))
    assert saved['thread']['data']['natural_questions_enabled'] is False
    assert not any(e['kind'] in {'QUESTION', 'MEANING_UPDATE'} for e in saved['events'])
    assert run(EmlisThreadService(runtime_profile=Q3_PROFILE).get(user, parent))['current_observation'] == dto['current_observation']
    assert len(calls) == 1


def test_ordinary_source_needs_no_finite_checkpoint_or_question(natural_questions):
    user, parent, service, calls = natural_questions(memo='会議の資料を読み直した。終わって少し安心した。')
    dto = run(service.start(user, parent))
    assert dto['state'] == 'COMPLETED' and dto['pending_question'] is None
    assert 'response_purpose' not in calls[0]
    saved = run(service.store.read(user, input_id=parent))
    assert saved['thread']['current_meaning_event_id'] is None
    assert not any(e['kind'] in {'QUESTION', 'MEANING_UPDATE'} for e in saved['events'])


def test_already_written_personal_explanation_is_not_asked_again(natural_questions):
    memo = ONE + '期待されているように感じて、重かった。'
    user, parent, service, calls = natural_questions(memo=memo)
    dto = run(service.start(user, parent))
    assert dto['state'] == 'COMPLETED' and dto['pending_question'] is None
    assert calls[0]['current']['memo'] == memo
    assert 'response_purpose' not in calls[0] and len(calls) == 1


def test_two_resolved_targets_end_after_two_questions(natural_questions):
    user, parent, service, calls = natural_questions(memo=ONE + '誘われたのに、悲しかった。')
    dto = run(service.start(user, parent))
    dto = run(answer(service, user, dto, 'その時は重かった。', 'first'))
    assert dto['state'] == 'AWAITING_CONTINUE'
    dto = run(service.action(user, dto['thread_id'], action='continue',
        expected_revision=dto['revision'], idempotency_key='continue-second'))
    dto = run(answer(service, user, dto, 'その時は怖かった。', 'second'))
    assert dto['state'] == 'COMPLETED' and dto['issued_count'] == 2
    assert not dto['can_continue'] and len(calls) == 3


def test_old_q2_natural_constructor_keeps_its_saved_single_reply_contract(natural_questions):
    user, parent, service, calls = natural_questions()
    legacy = EmlisThreadService(natural_reply_source=service.natural_reply_source)
    dto = run(legacy.start(user, parent))
    assert dto['state'] == 'COMPLETED' and dto['question_limit'] == 1
    saved = run(legacy.store.read(user, input_id=parent))
    assert 'natural_question_policy' not in saved['thread']['data']
    assert 'response_purpose' not in calls[0] and len(calls) == 1


def test_skip_finishes_with_new_final_reply_and_replay_never_reacquires(natural_questions):
    user, parent, service, calls = natural_questions()
    initial = run(service.start(user, parent))
    done = run(service.action(user, initial['thread_id'], action='skip',
        question_id=initial['pending_question']['question_id'],
        expected_revision=initial['revision'], idempotency_key='skip'))
    assert done['state'] == 'COMPLETED' and done['body_state'] == 'FINAL', done
    assert done['current_observation']['text'] == FINAL
    assert done['current_observation']['event_id'] != initial['current_observation']['event_id']
    assert len(calls) == 2 and 'response_purpose' not in calls[-1]
    assert not calls[-1]['current_answers']
    replay = run(service.action(user, initial['thread_id'], action='skip',
        question_id=initial['pending_question']['question_id'],
        expected_revision=initial['revision'], idempotency_key='skip'))
    assert replay['current_observation'] == done['current_observation'] and len(calls) == 2
    saved = run(service.store.read(user, input_id=parent))
    assert not any(e['kind'] == 'ANSWER' for e in saved['events'])
    assert saved['thread']['data']['natural_question_stop'] == 'skip'


def test_stop_after_answer_preserves_current_complete_reply_without_extra_generation(natural_questions):
    user, parent, service, calls = natural_questions(memo=THREE)
    initial = run(service.start(user, parent))
    answered = run(answer(service, user, initial, 'その時は重かった。'))
    assert answered['state'] == 'AWAITING_CONTINUE'
    done = run(service.action(user, answered['thread_id'], action='stop',
        expected_revision=answered['revision'], idempotency_key='stop'))
    assert done['state'] == 'COMPLETED' and done['body_state'] == 'REFINED'
    assert done['current_observation'] == answered['current_observation']
    assert calls[-1]['current_answers'][0]['text'] == 'その時は重かった。'
    assert calls[-1]['response_purpose'] == {'stage': 'REFINED'}
    assert len(calls) == 2 and done['issued_count'] == 1 and not done['can_continue']
    saved = run(service.store.read(user, input_id=parent))
    assert saved['thread']['data']['natural_question_stop'] == 'stop'
    assert 'continuation_question' not in saved['thread']['data']
    terminals = [e for e in saved['events'] if e['kind'] == 'TERMINAL']
    assert terminals[-1]['payload']['reason'] == 'stop'
    assert len([e for e in saved['events'] if e['kind'] == 'OBSERVATION']) == 2
    replay = run(service.action(user, answered['thread_id'], action='stop',
        expected_revision=answered['revision'], idempotency_key='stop'))
    assert replay['current_observation'] == done['current_observation'] and len(calls) == 2
    assert run(service.get(user, parent))['current_observation'] == done['current_observation']


def test_stop_after_answer_refreshes_deleted_history_and_acquires_current_final(natural_questions, qdb):
    user, parent, service, calls = natural_questions(tier='plus', memo=THREE)
    past = str(uuid4())
    qdb.query("insert into public.emotions values ($1,$2,(now()-interval '1 day') at time zone 'UTC',$3,'',"
              "array['仕事'],array['不安'],$4)",
              [past, user, '褒められた。会議の感想を考えた。',
               json.dumps([dict(type='不安', strength='medium')])])
    initial = run(service.start(user, parent))
    answered = run(answer(service, user, initial, 'その時は重かった。'))
    assert answered['state'] == 'AWAITING_CONTINUE' and len(calls) == 2
    assert len(calls[-1]['past_user_records']) == 1
    qdb.query('delete from public.emotions where id=$1', [past])
    done = run(service.action(user, answered['thread_id'], action='stop',
        expected_revision=answered['revision'], idempotency_key='stop-deleted-history'))
    assert done['state'] == 'COMPLETED' and done['current_observation']['text'] == FINAL
    assert done['current_observation']['event_id'] != answered['current_observation']['event_id']
    assert calls[-1]['current_answers'][0]['text'] == 'その時は重かった。'
    assert calls[-1]['past_user_records'] == [] and 'response_purpose' not in calls[-1]
    assert len(calls) == 3 and done['issued_count'] == 1


@pytest.mark.parametrize('history_change', ('delete', 'edit'))
def test_stop_reuse_checks_history_again_at_sql_commit(natural_questions, qdb, monkeypatch, history_change):
    user, parent, service, calls = natural_questions(tier='plus', memo=THREE)
    past = str(uuid4())
    qdb.query("insert into public.emotions values ($1,$2,(now()-interval '1 day') at time zone 'UTC',$3,'',"
              "array['仕事'],array['不安'],$4)",
              [past, user, '褒められた。会議の感想を考えた。',
               json.dumps([dict(type='不安', strength='medium')])])
    initial = run(service.start(user, parent))
    answered = run(answer(service, user, initial, 'その時は重かった。'))
    assert answered['state'] == 'AWAITING_CONTINUE' and answered['current_observation']
    assert len(calls) == 2 and len(calls[-1]['past_user_records']) == 1
    changed = False

    async def change_history_before_terminal(name, payload, **kwargs):
        nonlocal changed
        if not changed and any(e['kind'] == 'TERMINAL' and e['payload'].get('reason') == 'stop'
                               for e in payload.get('p_events', [])):
            changed = True
            if history_change == 'delete':
                result = qdb.query('delete from public.emotions where id=$1', [past])
            else:
                result = qdb.query('update public.emotions set memo=$2 where id=$1',
                    [past, '褒められた。別の会議の感想を考えた。'])
            assert 'code' not in result, result
        return await qdb.rpc(name, payload, **kwargs)

    monkeypatch.setattr(emlis_thread_store, 'sb_post_rpc', change_history_before_terminal)
    with pytest.raises(ThreadStoreError) as conflict:
        run(service.action(user, answered['thread_id'], action='stop',
            expected_revision=answered['revision'], idempotency_key='stop-history-race'))
    assert conflict.value.status == 409 and changed and len(calls) == 2
    current = run(service.get(user, parent))
    assert current['current_observation'] is None
    saved = run(service.store.read(user, input_id=parent))
    assert not any(e.get('idempotency_key') == 'stop-history-race' for e in saved['events'])
    done = run(service.action(user, current['thread_id'], action='stop',
        expected_revision=current['revision'], idempotency_key='stop-history-race'))
    assert done['state'] == 'COMPLETED' and done['current_observation']['text'] == FINAL
    assert done['current_observation']['event_id'] != answered['current_observation']['event_id']
    assert len(calls) == 3 and calls[-1]['current_answers'][0]['text'] == 'その時は重かった。'
    if history_change == 'delete':
        assert calls[-1]['past_user_records'] == []
    else:
        assert '別の会議の感想' in json.dumps(calls[-1]['past_user_records'], ensure_ascii=False)


def test_skip_refreshes_revoked_paid_history_before_final_response(natural_questions, qdb):
    user, parent, service, calls = natural_questions(tier='plus')
    past = str(uuid4())
    qdb.query("insert into public.emotions values ($1,$2,(now()-interval '1 day') at time zone 'UTC',$3,'',"
              "array['仕事'],array['不安'],$4)",
              [past, user, '褒められた。会議の感想を考えた。',
               json.dumps([dict(type='不安', strength='medium')])])
    initial = run(service.start(user, parent))
    assert initial['state'] == 'AWAITING_ANSWER'
    assert len(calls[0]['past_user_records']) == 1
    qdb.query('delete from public.emotions where id=$1', [past])
    changed = run(service.get(user, parent))
    assert changed['current_observation'] is None
    done = run(service.action(user, initial['thread_id'], action='skip',
        question_id=initial['pending_question']['question_id'],
        expected_revision=changed['revision'], idempotency_key='skip-deleted-history'))
    assert done['state'] == 'COMPLETED' and done['current_observation']['text'] == FINAL, done
    assert calls[-1]['past_user_records'] == []
    assert len(calls) == 2


def test_unresolved_answer_remains_unresolved_and_is_not_reasked(natural_questions):
    user, parent, service, calls = natural_questions()
    initial = run(service.start(user, parent))
    done = run(answer(service, user, initial, 'はい。'))
    assert done['state'] == 'COMPLETED'
    assert done['answer_assessment'] == 'UNRESOLVED' and not done['meaning_updated']
    assert done['pending_question'] is None and done['issued_count'] == 1
    assert 'まだ確かめきれていません' in done['current_observation']['text']
    assert calls[-1]['current_answers'][0]['text'] == 'はい。'
    meaning = calls[-1]['answer_meaning']
    assert meaning['assessment'] == 'UNRESOLVED' and meaning['disposition'] == 'UNRESOLVED'
    assert meaning['unresolved_parts']
    assert not any(fragment['source_role'] == 'SUPPLEMENTAL_ANSWER'
        for claim in meaning['active_claims'] for fragment in claim['source_fragments'])
    assert len(calls) == 2


def _assert_answer_projection_uses_actual_source_spans(material):
    answers = {answer['answer_id']: answer['text'] for answer in material['current_answers']}
    meaning = material['answer_meaning']
    for row in (*meaning['active_claims'], *meaning['inactive_claims'], *meaning['inactive_relations']):
        for fragment in row['source_fragments']:
            if fragment['source_role'] == 'SUPPLEMENTAL_ANSWER':
                raw = answers[fragment['answer_id']]
            else:
                raw = material['current']
                for key in fragment['field'].split('.'):
                    raw = raw[int(key)] if isinstance(raw, list) else raw[key]
            assert isinstance(raw, str)
            assert raw[fragment['scalar_start']:fragment['scalar_end']] == fragment['text']


def test_withdrawn_original_claim_is_marked_inactive_for_the_sole_natural_provider(natural_questions):
    user, parent, service, calls = natural_questions()
    initial = run(service.start(user, parent))
    done = run(answer(service, user, initial, '「嬉しくなかった」は誤りです。'))
    assert done['state'] == 'COMPLETED' and done['meaning_updated'], done
    meaning = calls[-1]['answer_meaning']
    assert meaning['assessment'] == 'RESOLVED' and meaning['inactive_claims']
    assert any(row['kind'] == 'reaction' and any('嬉しくなかった' in fragment['text']
        for fragment in row['source_fragments']) for row in meaning['inactive_claims'])
    assert any(row['kind'] == 'reaction' and '嬉しくなかった' in row['claim_anchor']
        for row in meaning['inactive_claims'])
    assert any(row['kind'] == 'event' and '褒められた' in row['claim_anchor']
        for row in meaning['active_claims'])
    assert not any(row['kind'] == 'reaction' for row in meaning['active_claims'])
    assert all('嬉しくなかった' not in row['claim_anchor'] for row in meaning['active_claims'])
    assert all(fragment['field'] in {'memo', 'memo_action', 'answer_text_private'}
        for row in (*meaning['active_claims'], *meaning['inactive_claims'])
        for fragment in row['source_fragments'])
    _assert_answer_projection_uses_actual_source_spans(calls[-1])
    saved = run(service.store.read(user, input_id=parent))
    assert saved['original']['memo'] == ONE
    assert len(calls) == 2 and 'answer_meaning' not in json.dumps(done)


@pytest.mark.parametrize('tier', ('free', 'plus', 'premium'))
@pytest.mark.parametrize('answer_text,assessment', (
    ('「嬉しくなかった」は誤りです。', 'RESOLVED'),
    ('その時は重かった。', 'RESOLVED'),
    ('はい。', 'UNASSESSED'),
))
def test_research_history_uses_latest_owned_answer_meaning_without_changing_normal_sources(
        natural_questions, qdb, monkeypatch, tier, answer_text, assessment):
    from emlis_thread_service import _request
    from cocolon_meaning_experience_engine.natural_reply import prepare_natural_reply, system_message_for
    user, past, service, calls = natural_questions(tier='premium')
    qdb.query("update public.emotions set created_at=(now()-interval '1 day') at time zone 'UTC' where id=$1", [past])
    initial = run(service.start(user, past))
    completed = run(answer(service, user, initial, answer_text))
    assert completed['state'] == 'COMPLETED'
    past_snapshot = run(service.store.read(user, input_id=past))
    parent = str(uuid4())
    qdb.query('update public.profiles set subscription_tier=$2 where id=$1', [user, tier])
    qdb.query("insert into public.emotions values ($1,$2,now() at time zone 'UTC',$3,'',"
              "array['仕事'],array['不安'],$4)",
              [parent, user, ONE, json.dumps([dict(type='不安', strength='medium')])])
    current = run(service.start(user, parent))
    snapshot = run(service._hydrate(user, run(service.store.read(user, input_id=parent))))
    request = _request(snapshot)
    ordinary, safety = prepare_natural_reply(request)
    research, research_safety = prepare_natural_reply(request, use_meaning_support=True)
    assert safety == research_safety and safety.normal_observation_allowed
    assert research.source_prefix_ref == ordinary.source_prefix_ref
    before, after = json.loads(ordinary.material_json), json.loads(research.material_json)
    if tier == 'free':
        assert before['past_user_records'] == after['past_user_records'] == []
        assert ordinary == research
    else:
        assert len(after['past_user_records']) == 1
        record = after['past_user_records'][0]
        assert record['input_id'] == past and record['original']['memo'] == ONE
        assert record['answers'][0]['text'] == answer_text
        assert record['answers'][0]['ai_question_context'] == initial['pending_question']['text']
        meaning = record.pop('answer_meaning')
        assert meaning['assessment'] == assessment
        assert after == before  # Every admitted raw source remains exact.
        assert 'inactive_claims' not in before['past_user_records'][0]
        assert 'past_user_recordsのanswer_meaning' in system_message_for(research)
        messages = [{'role': 'system', 'content': system_message_for(research)},
                    {'role': 'user', 'content': research.material_json}]
        assert len(json.dumps(messages, ensure_ascii=False, separators=(',', ':')).encode()) <= 5800
        if assessment == 'UNASSESSED':
            assert set(meaning) == {'schema_version', 'assessment'}
        elif '誤り' in answer_text:
            assert any('嬉しくなかった' in row['claim_anchor'] for row in meaning['inactive_claims'])
            assert all('嬉しくなかった' not in row['claim_anchor'] for row in meaning['active_claims'])
            assert any('褒められた' in row['claim_anchor'] for row in meaning['active_claims'])
        else:
            assert any('重かった' in row['claim_anchor'] for row in meaning['active_claims'])
        if assessment == 'RESOLVED':
            _assert_answer_projection_uses_actual_source_spans({
                'current': record['original'], 'current_answers': record['answers'], 'answer_meaning': meaning})
        assert completed['current_observation']['text'] not in research.material_json
        import cocolon_meaning_experience_engine.natural_reply as natural
        monkeypatch.setattr(natural, 'MEANING_SUPPORT_MESSAGES_MAX_BYTES', 1)
        fallback, _ = prepare_natural_reply(request, use_meaning_support=True)
        assert fallback == ordinary  # Omit only optional hints, never raw sources.
    reread = run(service.store.read(user, input_id=past))
    assert {k: reread[k] for k in ('original', 'thread', 'events')} == {
        k: past_snapshot[k] for k in ('original', 'thread', 'events')}
    assert 'answer_meaning' not in json.dumps(current, ensure_ascii=False)
    before_calls = len(calls)
    restarted = EmlisThreadService(runtime_profile=Q3_PROFILE)
    assert run(restarted.get(user, parent))['current_observation'] == current['current_observation']
    assert len(calls) == before_calls


def test_receipt_and_meaning_checkpoint_survive_final_save_failure_without_second_provider(natural_questions, qdb, monkeypatch):
    user, parent, service, calls = natural_questions()
    initial = run(service.start(user, parent))
    failed = False

    async def fail_once(name, payload, **kwargs):
        nonlocal failed
        if (not failed and payload.get('p_next', {}).get('latest_answer_event_id')
                and any(e['kind'] == 'OBSERVATION' for e in payload.get('p_events', []))):
            failed = True
            return httpx.Response(503, json={'code': '57P03'})
        return await qdb.rpc(name, payload, **kwargs)

    monkeypatch.setattr(emlis_thread_store, 'sb_post_rpc', fail_once)
    failed_dto = run(answer(service, user, initial, 'その時は重かった。'))
    assert failed_dto['state'] == 'RESPONSE_FAILED' and failed_dto['can_retry'], failed_dto
    saved = run(service.store.read(user, input_id=parent))
    checkpoint_id = saved['thread']['current_meaning_event_id']
    assert checkpoint_id and len(calls) == 2
    resumed = run(service.action(user, failed_dto['thread_id'], action='retry_response',
        expected_revision=failed_dto['revision'], idempotency_key='retry',
        operation_id=failed_dto['operation_id']))
    assert resumed['state'] == 'COMPLETED' and resumed['body_state'] == 'REFINED', resumed
    assert len(calls) == 2
    saved = run(service.store.read(user, input_id=parent))
    assert saved['thread']['current_meaning_event_id'] == checkpoint_id
    assert len([e for e in saved['events'] if e['kind'] == 'MEANING_UPDATE']) == 1


def test_saved_answer_can_resume_when_interrupted_before_provider_acquisition(natural_questions, monkeypatch):
    user, parent, service, calls = natural_questions()
    initial = run(service.start(user, parent))
    prepare = service._prepare_natural_question

    async def interrupt_before_call(*_args):
        raise asyncio.CancelledError

    monkeypatch.setattr(service, '_prepare_natural_question', interrupt_before_call)
    with pytest.raises(asyncio.CancelledError):
        run(answer(service, user, initial, 'その時は重かった。'))
    failed = run(service.get(user, parent))
    assert failed['answer_saved'] and failed['failure_code'] == 'worker_interrupted'
    assert failed['can_retry'] and len(calls) == 1
    saved = run(service.store.read(user, input_id=parent))
    prefix = saved['thread']['source_prefix_ref']
    assert not any(e['payload'].get('stage') == 'NATURAL_REPLY_CALL_STARTED'
        and e['payload'].get('source_prefix_ref') == prefix for e in saved['events'])
    monkeypatch.setattr(service, '_prepare_natural_question', prepare)
    done = run(service.action(user, failed['thread_id'], action='retry_response',
        expected_revision=failed['revision'], idempotency_key='resume-before-call',
        operation_id=failed['operation_id']))
    assert done['state'] == 'COMPLETED' and done['body_state'] == 'REFINED', done
    assert len(calls) == 2
    saved = run(service.store.read(user, input_id=parent))
    assert len([e for e in saved['events'] if e['kind'] == 'ANSWER']) == 1


def test_interrupted_started_provider_has_unknown_result_and_cannot_reacquire(natural_questions):
    user, parent, service, calls = natural_questions()
    initial = run(service.start(user, parent))

    async def interrupted_provider(material):
        calls.append(json.loads(material.material_json))
        raise asyncio.CancelledError

    service.natural_reply_source = interrupted_provider
    with pytest.raises(asyncio.CancelledError):
        run(answer(service, user, initial, 'その時は重かった。'))
    failed = run(service.get(user, parent))
    assert failed['answer_saved'] and failed['failure_code'] == 'worker_interrupted'
    assert not failed['can_retry'] and len(calls) == 2
    with pytest.raises(ThreadStoreError, match='retry_not_available'):
        run(service.action(user, failed['thread_id'], action='retry_response',
            expected_revision=failed['revision'], idempotency_key='unsafe-retry',
            operation_id=failed['operation_id']))
    assert len(calls) == 2
