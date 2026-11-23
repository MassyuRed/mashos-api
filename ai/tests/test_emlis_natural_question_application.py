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
from cocolon_meaning_experience_engine.natural_reply import (
    INITIAL_RECIPIENT_CONTEXT_VERSION, OBSERVATION_ANSWER_CONTEXT_VERSION,
    OBSERVATION_CONTEXT_VERSION, OBSERVATION_DELIVERY_CONTEXT_VERSION, NaturalReply,
    build_natural_reply_messages,
)
from emlis_thread_service import EmlisThreadService, Q3_PROFILE
from emlis_thread_store import ThreadStoreError
from test_emlis_natural_reply_application import _active_application_owner, _observe_initial_natural_failures
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
        qdb.query("insert into public.emotions values ($1,$2,(now()-interval '5 seconds') at time zone 'UTC',$3,'',"
                  "array['仕事'],array['不安'],$4)",
                  [parent, user, memo, json.dumps([dict(type='不安', strength='medium')])])
        calls = []

        async def provider(material):
            data = json.loads(material.material_json)
            calls.append(data)
            stage = data.get('response_purpose', {}).get('stage', 'FINAL')
            answered = {
                'その時は重かった。': 'その時は重かったのですね。',
                '今は重いです。': '今は重いと感じているのですね。',
                'その時は怖かった。': 'その時は怖かったのですね。',
                'その時は苦しかった。': 'その時は苦しかったのですね。',
                'はい。': 'どんな意味として届いたのかは、今の言葉だけではまだ確かめきれていません。',
                '「嬉しくなかった」は誤りです。': '元の受け取り方について、訂正を伝えてくださったのですね。',
                '「悲しかった」は誤りです。': '元の受け取り方について、訂正を伝えてくださったのですね。',
            }
            text = (ACK if stage == 'PRE_QUESTION' else
                    answered[data['current_answers'][-1]['text']] if stage == 'REFINED' else FINAL)
            return NaturalReply(text, 'synthetic-single-provider', material.source_prefix_ref)

        service = EmlisThreadService(runtime_profile=Q3_PROFILE,
            natural_reply_source=provider, natural_questions_enabled=enabled)
        _observe_initial_natural_failures(service, monkeypatch, calls)
        return user, parent, service, calls

    monkeypatch.setattr(emlis_thread_store, 'sb_post_rpc', qdb.rpc)
    return create


def test_independent_consulting_action_does_not_block_first_natural_reply(natural_questions, qdb):
    user, parent, service, calls = natural_questions()
    action = '私は友人に旅程を相談しました。'
    assert 'code' not in qdb.query('update public.emotions set memo_action=$2 where id=$1',
        [parent, action])
    initial = run(service.start(user, parent))
    assert initial['current_observation']['text'] in {ACK, FINAL}
    assert len(calls) == 1
    material = run(service.store.read(user, input_id=parent))
    assert material['original']['memo'] == ONE
    assert material['original']['memo_action'] == action
    assert run(service.get(user, parent))['current_observation'] == initial['current_observation']
    assert len(calls) == 1


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


def test_underspecified_feeling_gets_one_bound_question_and_an_event_answer(natural_questions):
    from cocolon_meaning_experience_engine.emlis_answer_update import (
        build_updated_grounded_plan, prepare_emlis_meaning,
    )
    from emlis_thread_service import _request

    user, parent, service, _ = natural_questions(memo='つらかったんです')
    calls = []

    async def provider(material):
        calls.append(material)
        return NaturalReply(ACK if len(calls) == 1 else FINAL,
                            'synthetic-single-provider', material.source_prefix_ref)

    service.natural_reply_source = provider
    initial = run(service.start(user, parent))
    assert initial['state'] == 'AWAITING_ANSWER', initial
    assert initial['pending_question']['text'] == 'なにがつらかったんですか？'
    assert initial['body_state'] == 'PRE_QUESTION'

    final = run(answer(service, user, initial, '会議がうまくできませんでした'))
    assert final['state'] == 'COMPLETED', final
    assert final['body_state'] == 'REFINED' and final['meaning_updated']
    assert final['issued_count'] == 1 and not final['can_continue']
    assert len(calls) == 2
    for call in calls:
        system_message, _ = build_natural_reply_messages(call)
        assert '返事の中で場面が伝わる言葉にしてください' in system_message['content']
    _, user_message = build_natural_reply_messages(calls[1])
    assert json.loads(user_message['content'])['カテゴリ'] == ['仕事']
    material = json.loads(calls[1].material_json)
    assert material['response_purpose'] == {'stage': 'REFINED'}
    assert material['current_answers'][0]['ai_question_context'] == initial['pending_question']['text']
    assert material['current_answers'][0]['text'] == '会議がうまくできませんでした'
    meaning = material['answer_meaning']
    assert meaning['assessment'] == 'RESOLVED'
    saved = run(service.store.read(user, input_id=parent))
    checkpoint, = [event['payload'] for event in saved['events'] if event['kind'] == 'MEANING_UPDATE']
    prepared = prepare_emlis_meaning(_request(saved, checkpoint_ref=checkpoint['checkpoint_id']))
    relation, = [row for row in build_updated_grounded_plan(prepared).relations if row.type == 'user_stated_cause']
    assert relation.from_nucleus_id == prepared.accepted_nuclei[0].nucleus_id
    assert relation.to_nucleus_id == prepared.thread.control.question_control_context.pending_question.decision.affected_meaning_refs[0]
    writer = json.loads(calls[1].writer_material_json)['records'][0]
    rows = writer['unresolved_sources'] if writer['active_state'] == 'PENDING' else writer['active_fields']
    bound, = [field for field in rows if field['source_role'] == 'SUPPLEMENTAL_ANSWER']
    assert (bound.get('text') or bound['fields']['memo']) == material['current_answers'][0]['text']
    assert bound['ai_question_context'] == initial['pending_question']['text']

    reread = run(EmlisThreadService(runtime_profile=Q3_PROFILE).get(user, parent))
    assert reread['current_observation'] == final['current_observation']
    assert len(calls) == 2


@pytest.mark.parametrize(('memo', 'action', 'enabled', 'expected_question'), [
    ('本当にしんどかった。', '', True, 'なにがしんどかったんですか？'),
    ('嬉しかったです。', '', True, 'なにが嬉しかったんですか？'),
    ('仕事が終わらなくてつらかった。', '', True, None),
    ('つらかったんです', '会議で発表した。', True, None),
    ('「つらかった」と友人が言いました。', '', True, None),
    ('つらかったんです', '', False, None),
])
def test_feeling_question_requires_unexplained_self_state_and_enabled_setting(
        natural_questions, qdb, memo, action, enabled, expected_question):
    user, parent, service, _ = natural_questions(memo=memo, enabled=enabled)
    qdb.query('update public.emotions set memo_action=$2 where id=$1', [parent, action])
    dto = run(service.start(user, parent))
    assert (dto['pending_question'] or {}).get('text') == expected_question


@pytest.mark.parametrize(('tier', 'mode', 'enabled'), [
    ('free', 'false', False),
    ('free', 'paid', False),
    ('plus', 'paid', True),
    ('premium', 'paid', True),
    ('free', 'true', True),
    ('plus', None, False),
])
def test_application_context_mode_pins_new_thread_at_plan_boundary(
        natural_questions, qdb, monkeypatch, tier, mode, enabled):
    user, parent, service, calls = natural_questions(tier=tier, memo='つらかったんです')
    owner = _active_application_owner(monkeypatch, service.natural_reply_source, mode)
    dto = run(owner.start(user, parent))
    snapshot = run(owner.store.read(user, input_id=parent))
    assert snapshot['thread']['data']['started_tier'] == tier
    assert snapshot['thread']['data'].get('natural_context_update_enabled') is (True if enabled else None)
    assert (dto['pending_question'] or {}).get('text') == 'なにがつらかったんですか？'
    receipt, = [event for event in snapshot['events'] if event['payload'].get('stage') == 'NATURAL_REPLY_RECEIVED']
    assert receipt['payload']['writer_context_version'] == INITIAL_RECIPIENT_CONTEXT_VERSION
    assert run(owner.get(user, parent))['current_observation'] == dto['current_observation']
    assert len(calls) == 1


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


def test_old_q2_natural_constructor_keeps_its_saved_single_reply_contract(natural_questions, monkeypatch):
    user, parent, service, calls = natural_questions()
    legacy = EmlisThreadService(natural_reply_source=service.natural_reply_source)
    _observe_initial_natural_failures(legacy, monkeypatch, calls)
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


@pytest.mark.parametrize(('tier', 'selected', 'action', 'expected'), [
    ('plus', None, 'skip', INITIAL_RECIPIENT_CONTEXT_VERSION),
    ('plus', OBSERVATION_CONTEXT_VERSION, 'skip', OBSERVATION_CONTEXT_VERSION),
    ('plus', OBSERVATION_ANSWER_CONTEXT_VERSION, 'skip', OBSERVATION_ANSWER_CONTEXT_VERSION),
    ('plus', OBSERVATION_DELIVERY_CONTEXT_VERSION, 'skip', OBSERVATION_DELIVERY_CONTEXT_VERSION),
    ('free', OBSERVATION_DELIVERY_CONTEXT_VERSION, 'stop', OBSERVATION_DELIVERY_CONTEXT_VERSION),
    ('premium', OBSERVATION_DELIVERY_CONTEXT_VERSION, 'skip', INITIAL_RECIPIENT_CONTEXT_VERSION),
])
def test_application_first_skip_keeps_live_paid_history_out_of_the_reply_writer(
        natural_questions, qdb, monkeypatch, tier, selected, action, expected):
    user, parent, _, _ = natural_questions(tier=tier)
    past = str(uuid4())
    qdb.query("insert into public.emotions values ($1,$2,(now()-interval '1 day') at time zone 'UTC',$3,'',"
              "array['仕事'],array['不安'],$4)",
              [past, user, '褒められたのに、嬉しくなかった。昨日のことです。',
               json.dumps([dict(type='不安', strength='medium')])])
    calls = []

    async def provider(material):
        calls.append(material)
        return NaturalReply('褒められても嬉しくなかったんですね。Emlisはその気持ちを大切に受け止めています。',
                            'synthetic-single-provider', material.source_prefix_ref)

    owner = _active_application_owner(monkeypatch, provider, 'paid', observation_version=selected)
    initial = run(owner.start(user, parent))
    assert initial['state'] == 'AWAITING_ANSWER', initial
    done = run(owner.action(user, initial['thread_id'], action=action,
        question_id=initial['pending_question']['question_id'],
        expected_revision=initial['revision'], idempotency_key='first-skip'))
    assert done['state'] == 'COMPLETED' and done['body_state'] == 'FINAL', done
    pre_question, final = calls
    assert 'initial_unanswered_final' not in json.loads(pre_question.writer_material_json)
    assert '書いていない考えや迷い' not in build_natural_reply_messages(pre_question)[0]['content']
    expected_history = [] if tier == 'free' else [past]
    assert [row['input_id'] for row in json.loads(final.material_json)['past_user_records']] == expected_history
    writer = json.loads(final.writer_material_json)
    assert writer['source_context_version'] == expected
    assert 'history_line' not in writer and 'related_past' not in writer and writer['user_frame_feedback'] == []
    system, user_message = build_natural_reply_messages(final)
    if expected == OBSERVATION_DELIVERY_CONTEXT_VERSION:
        assert writer['initial_unanswered_final'] is True
        assert '書いていない考えや迷い' in system['content']
    else:
        assert 'initial_unanswered_final' not in writer
        assert '書いていない考えや迷い' not in system['content']
    assert set(json.loads(user_message['content'])) == {'今回の記録'}
    assert '昨日のことです' not in user_message['content']
    assert initial['pending_question']['text'] not in user_message['content']
    assert run(owner.get(user, parent))['current_observation'] == done['current_observation']


@pytest.mark.parametrize(('tier', 'writer_version'), [
    ('free', OBSERVATION_CONTEXT_VERSION), ('plus', OBSERVATION_CONTEXT_VERSION),
    ('premium', OBSERVATION_CONTEXT_VERSION), ('free', OBSERVATION_DELIVERY_CONTEXT_VERSION),
    ('plus', OBSERVATION_DELIVERY_CONTEXT_VERSION),
])
def test_observation_writer_receives_one_verified_prior_passage_only_for_paid_plans(
        natural_questions, qdb, monkeypatch, tier, writer_version):
    user, parent, _, _ = natural_questions(tier=tier, memo='資料を期限に間に合わせた。今日は肩の力が抜けた。')
    past_memo = '資料を期限に間に合わせた。あの日はほっとした。'
    for memo, days in [(past_memo, 2), ('駅で傘を買った。', 3)]:
        qdb.query("insert into public.emotions values ($1,$2,(now()-$4::integer*interval '1 day') at time zone 'UTC',"
                  "$3,'',array['仕事'],array['平穏'],$5)",
                  [str(uuid4()), user, memo, days, json.dumps([dict(type='平穏', strength='medium')])])
    calls = []
    reply = '間に合って、今日は肩の力が抜けたんですね。Emlisもほっとしました。'

    async def provider(request):
        calls.append(build_natural_reply_messages(request))
        return NaturalReply(reply, 'synthetic-single-provider', request.source_prefix_ref)

    owner = _active_application_owner(monkeypatch, provider, 'paid', observation_version=writer_version)
    initial = run(owner.start(user, parent))
    assert initial['current_observation']['text'] == reply
    assert run(owner.get(user, parent))['current_observation'] == initial['current_observation']
    (system, user_message), = calls
    material = json.loads(user_message['content'])
    assert material.get('以前の本人の言葉') == (None if tier == 'free' else past_memo)
    assert '駅で傘' not in user_message['content']
    assert ('二つを並べて読む' in system['content']) is (tier != 'free')


@pytest.mark.parametrize('writer_version', [OBSERVATION_CONTEXT_VERSION, OBSERVATION_DELIVERY_CONTEXT_VERSION])
def test_self_understanding_projects_the_discovery_and_preserves_the_stored_selection(
        natural_questions, qdb, monkeypatch, writer_version):
    memo = '頼られることが好きだと思っていたけれど、相手によるとわかりました。'
    user, parent, _, _ = natural_questions(memo=memo)
    selection = [dict(type='自己理解', strength='medium')]
    qdb.query("update public.emotions set emotions=array['自己理解'],emotion_details=$2 where id=$1",
              [parent, json.dumps(selection)])
    calls = []

    async def provider(request):
        calls.append(request)
        return NaturalReply('誰に頼られるかで違うんですね。その違いを聞けて、Emlisはうれしいです。',
                            'synthetic-single-provider', request.source_prefix_ref)

    owner = _active_application_owner(monkeypatch, provider, 'paid', observation_version=writer_version)
    initial = run(owner.start(user, parent))
    assert initial['state'] == 'COMPLETED' and initial['pending_question'] is None
    request, = calls
    system, user_message = build_natural_reply_messages(request)
    assert '本人が自分について気づいたこと' in system['content']
    assert 'initial_unanswered_final' not in json.loads(request.writer_material_json)
    assert '書いていない考えや迷い' not in system['content']
    assert '同じ名詞を続けず' not in system['content']
    assert memo in user_message['content'] and 'medium' not in user_message['content']
    assert json.loads(request.material_json)['current']['emotion_details'] == selection
    assert run(owner.get(user, parent))['current_observation'] == initial['current_observation']


@pytest.mark.parametrize(('memo', 'asks'), [
    ('褒められたのに、嬉しくなかった。', False),
    ('褒められたのに、嬉しくなかった。なぜだろう。', True),
    ('褒められたのに、嬉しくなかった。駅で友人に会った。どうしてかな。', False),
])
def test_self_understanding_only_asks_about_an_open_point_in_its_own_passage(
        natural_questions, qdb, monkeypatch, memo, asks):
    user, parent, service, _ = natural_questions(memo=memo)
    qdb.query("update public.emotions set emotions=array['自己理解'],emotion_details=$2 where id=$1",
              [parent, json.dumps([dict(type='自己理解', strength='medium')])])
    owner = _active_application_owner(monkeypatch, service.natural_reply_source, 'paid', observation=True)
    initial = run(owner.start(user, parent))
    assert (initial['pending_question'] is not None) is asks


def test_answer_updates_the_observation_without_treating_the_question_as_the_users_words(
        natural_questions, monkeypatch):
    user, parent, _, _ = natural_questions()
    calls = []

    async def provider(request):
        calls.append(request)
        return NaturalReply('重く感じられたんですね。' if len(calls) == 2 else ACK,
                            'synthetic-single-provider', request.source_prefix_ref)

    owner = _active_application_owner(monkeypatch, provider, 'paid', observation=True)
    initial = run(owner.start(user, parent))
    final = run(answer(owner, user, initial, 'その時は重かった。'))
    assert final['state'] == 'COMPLETED'
    _, refined = calls
    system, user_message = build_natural_reply_messages(refined)
    assert '今日かける言葉を選び直し' in system['content']
    assert 'その時は重かった。' in user_message['content']
    assert initial['pending_question']['text'] in user_message['content']
    assert run(owner.get(user, parent))['current_observation'] == final['current_observation']


@pytest.mark.parametrize(('answer_text', 'interpreted'), [('その時は重かった。', True), ('はい。', False)])
@pytest.mark.parametrize('writer_version', [OBSERVATION_ANSWER_CONTEXT_VERSION, OBSERVATION_DELIVERY_CONTEXT_VERSION])
def test_answer_projection_uses_the_exact_issued_turn_and_can_replay_from_its_receipt(
        natural_questions, monkeypatch, qdb, answer_text, interpreted, writer_version):
    from test_emlis_natural_reply_application import _piece_adapter

    user, parent, _, _ = natural_questions()
    calls = []
    synthetic = '聞かせてくださって、ありがとうございます。'

    async def provider(request):
        calls.append(request)
        return NaturalReply(synthetic, 'single-synthetic-author', request.source_prefix_ref)

    owner = _active_application_owner(monkeypatch, provider, 'paid',
                                      observation_version=writer_version)
    initial = run(owner.start(user, parent))
    issued = initial['pending_question']
    failed = False

    async def rpc(method, payload, **kwargs):
        nonlocal failed
        if not failed and any(e['kind'] == 'OBSERVATION' for e in payload.get('p_events', [])):
            failed = True
            return httpx.Response(503, json={'code': '57P03'})
        return await qdb.rpc(method, payload, **kwargs)

    monkeypatch.setattr(emlis_thread_store, 'sb_post_rpc', rpc)
    partial = run(answer(owner, user, initial, answer_text))
    assert partial['can_retry']
    request = calls[-1]
    material = json.loads(request.material_json)
    audit = json.loads(request.analysis_material_json)
    bound, = material['current_answers']
    assert (bound['question_id'], bound['ai_question_context'], bound['text']) == (
        issued['question_id'], issued['text'], answer_text)
    writer = json.loads(request.writer_material_json)
    assert writer['records'][0]['active_state'] == 'PENDING'
    assert writer['bound_answer_turns']['interpreted'] is interpreted
    assert 'initial_unanswered_final' not in writer
    system, user_message = build_natural_reply_messages(request)
    assert ('同じ名詞を続けず' in system['content']) is (writer_version == OBSERVATION_DELIVERY_CONTEXT_VERSION)
    assert '書いていない考えや迷い' not in system['content']
    message = json.loads(user_message['content'])
    assert list(message)[-1] == 'いま届いたやり取り'
    assert message['いま届いたやり取り'] == {'Emlisが送った問い': issued['text'], '本人の返答': answer_text}
    assert message['今回の記録']['考えたこと・感じたこと'] == ONE
    assert synthetic not in request.material_json and synthetic not in request.analysis_material_json
    assert not any(source.get('source_role') == 'AI_QUESTION' for source in audit['sources'])
    assert 'いま届いたやり取り' not in request.material_json + request.analysis_material_json
    reopened = _active_application_owner(monkeypatch, provider, 'false')
    result = run(reopened.action(user, partial['thread_id'], action='retry_response',
        expected_revision=partial['revision'], idempotency_key='reread-new-answer', operation_id=partial['operation_id']))
    assert result['current_observation']['text'] == synthetic
    assert run(reopened.get(user, parent))['current_observation'] == result['current_observation']
    saved = run(reopened.store.read(user, input_id=parent))
    receipt, = [e for e in saved['events'] if e['payload'].get('stage') == 'NATURAL_REPLY_RECEIVED'
                and e['operation_id'] == partial['operation_id']]
    assert receipt['payload']['writer_context_version'] == writer_version
    assert len(calls) == 2
    assert saved['original']['memo'] == ONE
    if interpreted:
        adapter = _piece_adapter(user, reopened, monkeypatch)
        ref = run(adapter.resolve_refined_source_ref('Bearer synthetic', parent,
            supplemental_answer_identity=saved['thread']['latest_answer_event_id'], opted_in=True))
        assert ref['emlis_observation_result_identity'] == result['current_observation']['event_id']


def test_prior_recipient_version_still_builds_the_original_prompt(natural_questions, monkeypatch):
    from dataclasses import replace
    user, parent, _, _ = natural_questions()
    calls = []

    async def provider(request):
        calls.append(request)
        return NaturalReply(ACK, 'synthetic-single-provider', request.source_prefix_ref)

    owner = _active_application_owner(monkeypatch, provider, 'paid', observation=True)
    run(owner.start(user, parent))
    material, = calls
    writer = json.loads(material.writer_material_json)
    writer['source_context_version'] = INITIAL_RECIPIENT_CONTEXT_VERSION
    writer.pop('self_understanding')
    legacy = replace(material, writer_material_json=json.dumps(writer, ensure_ascii=False))
    system, user_message = build_natural_reply_messages(legacy)
    assert '焼きたてのパン' in system['content']
    assert '今回の記録' in user_message['content']


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
    qdb.query("insert into public.emotions values ($1,$2,(now()-interval '5 seconds') at time zone 'UTC',$3,'',"
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
        assert meaning['schema_version'] == 'natural_history_answer_meaning.v1'
        assert meaning['source_record_id'] == past != parent
        assert after == before  # Every admitted raw source remains exact.
        assert 'inactive_claims' not in before['past_user_records'][0]
        assert 'source_record_idの過去の場面' in system_message_for(research)
        assert 'current_userは記録者' in system_message_for(research)
        messages = [{'role': 'system', 'content': system_message_for(research)},
                    {'role': 'user', 'content': research.material_json}]
        assert len(json.dumps(messages, ensure_ascii=False, separators=(',', ':')).encode()) <= 5800
        if assessment == 'UNASSESSED':
            assert set(meaning) == {'schema_version', 'assessment', 'source_record_id'}
        elif '誤り' in answer_text:
            assert any('嬉しくなかった' in row['claim_anchor'] for row in meaning['inactive_claims'])
            assert all('嬉しくなかった' not in row['claim_anchor'] for row in meaning['active_claims'])
            assert any('褒められた' in row['claim_anchor'] for row in meaning['active_claims'])
        else:
            assert any('重かった' in row['claim_anchor'] for row in meaning['active_claims'])
        if assessment == 'RESOLVED':
            _assert_answer_projection_uses_actual_source_spans({
                'current': record['original'], 'current_answers': record['answers'], 'answer_meaning': meaning})
            from cocolon_meaning_experience_engine.natural_reply import _compact_history_answer_meaning
            compact = _compact_history_answer_meaning(meaning)
            assert _expand_history_locator_view(compact, record) == meaning
            if answer_text == 'その時は重かった。':
                assert any(locator['source_path'] == 'answers.text'
                    and locator['answer_id'] == record['answers'][0]['answer_id']
                    for locator in compact['source_fragments'])
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


def _expand_history_locator_view(meaning, record):
    """Read each locator from its retained original/answer, independently."""
    expanded = {key: value for key, value in meaning.items() if key != 'source_fragments'}
    expanded['schema_version'] = 'natural_history_answer_meaning.v1'
    answers = {answer['answer_id']: answer['text'] for answer in record['answers']}
    fragments = []
    for locator in meaning['source_fragments']:
        start, end = locator['scalar_range']
        if locator['source_path'].startswith('original.'):
            field = locator['source_path'].removeprefix('original.')
            fragment = dict(source_role='CURRENT_INPUT', field=field,
                scalar_start=start, scalar_end=end, text=record['original'][field][start:end])
        else:
            assert locator['source_path'] == 'answers.text'
            fragment = dict(source_role='SUPPLEMENTAL_ANSWER', field='answer_text_private',
                scalar_start=start, scalar_end=end, text=answers[locator['answer_id']][start:end],
                answer_id=locator['answer_id'])
        fragments.append(fragment)
    groups = ('active_claims', 'inactive_claims', 'inactive_relations')
    if 'active_relations' in meaning:
        groups = (*groups, 'active_relations')
    for group in groups:
        expanded[group] = []
        for row in meaning[group]:
            original = {key: value for key, value in row.items() if key != 'source_fragment_refs'}
            original['source_fragments'] = [fragments[index] for index in row['source_fragment_refs']]
            expanded[group].append(original)
    return expanded


@pytest.mark.parametrize('past_memo,past_action,answer_text,current_memo,current_action', (
    ('誘われたのに、悲しかった。', '先週、弟に映画へ誘われた。', '「悲しかった」は誤りです。',
     '誘われたのに、悲しかった。', '今日、知人に食事へ誘われた。'),
    ('頼まれたのに、嬉しくなかった。', '先週、兄に荷物の受取を頼まれた。', '「嬉しくなかった」は誤りです。',
     '今日はサークルの冊子づくりを頼まれたけれど、喜べなかった。', ''),
))
def test_resolved_history_fits_without_dropping_withdrawal_or_raw_sources(
        natural_questions, qdb, monkeypatch, past_memo, past_action, answer_text,
        current_memo, current_action):
    from emlis_thread_service import _request
    from cocolon_meaning_experience_engine import natural_reply as natural
    from cocolon_meaning_experience_engine.emlis_thread_history import admitted_history_plans
    from cocolon_meaning_experience_engine.emlis_thread_source import admit_emlis_thread
    user, past, service, calls = natural_questions(tier='premium', memo=past_memo)
    qdb.query("update public.emotions set memo_action=$2,created_at=(now()-interval '1 day') "
              "at time zone 'UTC' where id=$1", [past, past_action])
    initial = run(service.start(user, past))
    completed = run(answer(service, user, initial, answer_text))
    assert completed['state'] == 'COMPLETED' and completed['meaning_updated']
    saved = run(service.store.read(user, input_id=past))
    parent = str(uuid4())
    qdb.query("insert into public.emotions values ($1,$2,(now()-interval '5 seconds') at time zone 'UTC',$3,$4,"
              "array['趣味','人間関係'],array['悲しみ'],$5)",
              [parent, user, current_memo, current_action,
               json.dumps([dict(type='悲しみ', strength='medium')])])
    run(service.start(user, parent))
    snapshot = run(service._hydrate(user, run(service.store.read(user, input_id=parent))))
    request = _request(snapshot)
    ordinary, safety = natural.prepare_natural_reply(request)
    research, research_safety = natural.prepare_natural_reply(request, use_meaning_support=True)
    before, after = json.loads(ordinary.material_json), json.loads(research.material_json)
    record = after['past_user_records'][0]
    meaning = record.pop('answer_meaning')
    assert meaning['schema_version'] == 'natural_history_answer_meaning.v2'
    assert meaning['source_record_id'] == record['input_id'] == past != parent
    assert after == before and ordinary.source_prefix_ref == research.source_prefix_ref
    assert safety == research_safety and safety.normal_observation_allowed
    source, prepared, _ = admitted_history_plans(admit_emlis_thread(request))[0]
    full = natural._answer_meaning_material(prepared, admit_emlis_thread(source.request))
    full.update(schema_version='natural_history_answer_meaning.v1', source_record_id=past)
    assert _expand_history_locator_view(meaning, record) == full
    assert full['inactive_claims'] and full['inactive_relations']
    assert all(row['claim_anchor'] not in past_action for row in full['inactive_claims'])
    expected_system = natural.SYSTEM_MESSAGE + natural._SCOPED_HISTORY_ANSWER_MEANING_MESSAGE
    assert natural.system_message_for(research) == expected_system
    messages = lambda material: [{'role': 'system', 'content': expected_system},
                                {'role': 'user', 'content': natural._compact_json(material)}]
    full_material = json.loads(research.material_json)
    full_material['past_user_records'][0]['answer_meaning'] = full
    assert len(natural._compact_json(messages(full_material)).encode()) > 5800
    assert len(natural._compact_json(messages(json.loads(research.material_json))).encode()) <= 5800
    monkeypatch.setattr(natural, 'MEANING_SUPPORT_MESSAGES_MAX_BYTES', 1)
    fallback, _ = natural.prepare_natural_reply(request, use_meaning_support=True)
    assert fallback == ordinary
    reread = run(service.store.read(user, input_id=past))
    assert {key: reread[key] for key in ('original', 'thread', 'events')} == {
        key: saved[key] for key in ('original', 'thread', 'events')}


@pytest.mark.parametrize('answer_text,about_time', (
    ('その時は重かった。', 'ORIGINAL_OCCASION'),
    ('今は重いです。', 'ANSWER_TIME'),
))
def test_optin_history_plan_preserves_the_evaluation_target_and_its_owned_time(
        natural_questions, qdb, monkeypatch, answer_text, about_time):
    from emlis_thread_service import _request
    from cocolon_meaning_experience_engine import natural_reply as natural
    from cocolon_meaning_experience_engine.emlis_thread_source import admit_emlis_thread
    from cocolon_meaning_experience_engine.emlis_thread_history import admitted_history_plans
    user, past, service, calls = natural_questions(tier='premium')
    qdb.query("update public.emotions set created_at=(now()-interval '1 day') at time zone 'UTC' where id=$1", [past])
    initial = run(service.start(user, past))
    completed = run(answer(service, user, initial, answer_text))
    assert completed['state'] == 'COMPLETED' and completed['meaning_updated']
    parent = str(uuid4())
    qdb.query("insert into public.emotions values ($1,$2,(now()-interval '5 seconds') at time zone 'UTC',$3,'',"
              "array['仕事'],array['不安'],$4)",
              [parent, user, ONE, json.dumps([dict(type='不安', strength='medium')])])
    run(service.start(user, parent))
    snapshot = run(service._hydrate(user, run(service.store.read(user, input_id=parent))))
    request = _request(snapshot)
    ordinary, safety = natural.prepare_natural_reply(request)
    unused, _ = natural.prepare_natural_reply(request, use_history_answer_plan=True)
    assert unused == ordinary  # The research flag never activates support by itself.
    previous, _ = natural.prepare_natural_reply(request, use_meaning_support=True)
    candidate, candidate_safety = natural.prepare_natural_reply(request,
        use_meaning_support=True, use_history_answer_plan=True)
    before, after = json.loads(previous.material_json), json.loads(candidate.material_json)
    record = after['past_user_records'][0]
    old_meaning = before['past_user_records'][0].pop('answer_meaning')
    meaning = record.pop('answer_meaning')
    assert after == before == json.loads(ordinary.material_json)
    assert candidate.source_prefix_ref == previous.source_prefix_ref == ordinary.source_prefix_ref
    assert candidate_safety == safety
    full = _expand_history_locator_view(meaning, record)
    relation, = full.pop('active_relations')
    assert full == old_meaning  # No existing claim, withdrawal or unknown is replaced.
    assert relation['relation'] == 'evaluation_about_event'
    assert relation['from_claim_anchor'] == '褒められた'
    assert relation['to_claim_anchor'] in {'重かった', '重いです'}
    source, prepared, plan = admitted_history_plans(admit_emlis_thread(request))[0]
    owned_relation, = [r for r in plan.relations if r.type == 'evaluation_about_event']
    binding, = [item.temporal_binding for item in prepared.checkpoint.answer_update.updates
                if item.update_ref in owned_relation.source_relation_ids]
    assert relation['about_time'] == binding.about_time == about_time
    envelopes = {prepared.thread.original.envelope.envelope_id: None,
        **{a.envelope.envelope_id: a.source.answer_id for a in prepared.thread.answers}}
    anchor_answer_id = envelopes[binding.anchor_source_ref]
    if anchor_answer_id is None:
        assert relation['time_anchor'] == 'original'
    else:
        assert relation['time_anchor_answer_id'] == anchor_answer_id
    assert relation.get('relative_relation') == binding.relative_relation
    assert [relation['source_fragments'][i]['text'] for i in relation['time_span_indices']] == [answer_text.rstrip('。')]
    assert natural.system_message_for(candidate) == natural.system_message_for(previous)
    messages = [{'role': 'system', 'content': natural.system_message_for(candidate)},
                {'role': 'user', 'content': candidate.material_json}]
    assert len(natural._compact_json(messages).encode('utf-8')) <= 5800
    monkeypatch.setattr(natural, 'MEANING_SUPPORT_MESSAGES_MAX_BYTES', 1)
    fallback, _ = natural.prepare_natural_reply(request,
        use_meaning_support=True, use_history_answer_plan=True)
    assert fallback == ordinary


def test_scoped_history_never_recovers_earlier_resolved_meaning_after_latest_unknown(natural_questions, qdb):
    from emlis_thread_service import _request
    from cocolon_meaning_experience_engine.natural_reply import prepare_natural_reply
    user, past, service, calls = natural_questions(tier='premium', memo=THREE)
    qdb.query("update public.emotions set created_at=(now()-interval '1 day') at time zone 'UTC' where id=$1", [past])
    dto = run(service.start(user, past))
    dto = run(answer(service, user, dto, 'その時は重かった。', 'history-resolved'))
    assert dto['answer_assessment'] == 'RESOLVED'
    dto = run(service.action(user, dto['thread_id'], action='continue',
        expected_revision=dto['revision'], idempotency_key='history-next'))
    dto = run(answer(service, user, dto, 'はい。', 'history-unknown'))
    assert dto['answer_assessment'] != 'RESOLVED'
    if dto['state'] == 'AWAITING_CONTINUE':
        dto = run(service.action(user, dto['thread_id'], action='stop',
            expected_revision=dto['revision'], idempotency_key='history-stop'))
    assert dto['state'] == 'COMPLETED'
    parent = str(uuid4())
    qdb.query("insert into public.emotions values ($1,$2,(now()-interval '5 seconds') at time zone 'UTC',$3,'',"
              "array['仕事'],array['不安'],$4)",
              [parent, user, ONE, json.dumps([dict(type='不安', strength='medium')])])
    service.natural_questions_enabled = False
    run(service.start(user, parent))
    snapshot = run(service._hydrate(user, run(service.store.read(user, input_id=parent))))
    material, _ = prepare_natural_reply(_request(snapshot), use_meaning_support=True)
    record = json.loads(material.material_json)['past_user_records'][0]
    assert record['input_id'] == past
    assert [a['text'] for a in record['answers']] == ['その時は重かった。', 'はい。']
    assert record['answer_meaning'] == {'schema_version': 'natural_history_answer_meaning.v1',
        'source_record_id': past, 'assessment': 'UNASSESSED'}


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

