"""Actual saved one-answer retention and historical checkpoint delivery."""
import asyncio

import pytest
from cocolon_meaning_experience_engine.emlis_answer_update import _prepare_emlis_meaning_from_plan
from cocolon_meaning_experience_engine.emlis_question import original_meaning_plan
from cocolon_meaning_experience_engine.emlis_thread_source import admit_emlis_thread
from test_cmee_emlis_relief_cognition import BASE, LEFT
from test_cmee_emlis_loneliness_delivery import KANA, export_dto, reopen
from test_emlis_q3_application import qdb, qcase
from test_emlis_q2_application import run, answer

MEMO = BASE + '褒められたのに、嬉しくなかった。'


def old_prepare(req):
    thread = admit_emlis_thread(req)
    return _prepare_emlis_meaning_from_plan(req, thread, original_meaning_plan(thread),
        legacy_relief_cognition_update_retention=True).checkpoint


def assert_pair_and_answer(body, text):
    assert '私も少し安心しました' in body and '今、耳を傾けていたいです' in body
    assert '友達からの誘いを断って' in body and 'かもしれないと思うと' in body
    assert '褒められた' in body
    if text == '今は嬉しい。':
        assert '回答した時点' in body and '嬉しい' in body
    elif text == '今は悲しい。':
        assert '回答した時点' in body and ('悲しい' in body or '悲しさ' in body)
    else:
        assert '悲しかった' in body


@pytest.mark.parametrize('text', ['今は嬉しい。', '今は悲しい。'])
@pytest.mark.parametrize('historical', [False, True], ids=['current', 'u343'])
def test_saved_answer_retains_pair_or_exact_prior_delivery(qcase, qdb, monkeypatch, text, historical):
    user, parent, service = qcase
    qdb.query('update public.emotions set memo=$2 where id=$1', [parent, MEMO])
    first = run(service.start(user, parent))
    assert first['pending_question']
    if historical:
        monkeypatch.setattr(service.engine, 'prepare_emlis_update', old_prepare)
    saved = run(answer(service, user, first, text, 'u344-answer'))
    if historical and text == '今は悲しい。':
        assert saved['state'] == 'RESPONSE_FAILED' and saved['failure_code'] == 'body_not_validated'
        assert saved['current_observation'] is None
        observations = [e for e in saved['timeline'] if e['kind'] == 'OBSERVATION']
        assert len(observations) == 1 and observations[0]['text'] == first['current_observation']['text']
    else:
        assert saved['state'] == 'COMPLETED' and saved['body_state'] == 'REFINED'
        body = saved['current_observation']['text']
        if historical:
            reception = body.split('Emlisから：', 1)[1]
            assert '私も少し安心しました' not in reception
            assert '回答した時点では嬉しい' in reception
        else:
            assert_pair_and_answer(body, text)
    assert saved['original'] == first['original']
    assert len([e for e in saved['timeline'] if e['kind'] == 'ANSWER']) == 1
    reopen(user, parent, saved)
    export_dto(f'update-{historical}-' + ('positive' if '嬉' in text else 'negative'), saved)


@pytest.mark.parametrize('memo,text', [
    (KANA + '褒められたのに、嬉しくなかった。', '今は嬉しい。'),
    ('私は' + BASE.replace('寂しい', '少し寂しい') + '褒められたのに、嬉しくなかった。',
        '「嬉しくなかった」ではなく「悲しかった」です。'),
])
def test_saved_source_variant_keeps_pair_and_updated_separate_experience(qcase, qdb, memo, text):
    user, parent, service = qcase
    qdb.query('update public.emotions set memo=$2 where id=$1', [parent, memo])
    first = run(service.start(user, parent))
    saved = run(answer(service, user, first, text, 'u344-variant'))
    assert saved['state'] == 'COMPLETED' and saved['body_state'] == 'REFINED'
    assert_pair_and_answer(saved['current_observation']['text'], text)
    reopen(user, parent, saved)
    export_dto('update-variant-' + ('kana' if 'さびしい' in memo else 'self'), saved)


def test_saved_pair_withdrawal_does_not_retain_invalid_reaction(qcase, qdb):
    user, parent, service = qcase
    qdb.query('update public.emotions set memo=$2 where id=$1', [parent, MEMO])
    first = run(service.start(user, parent))
    saved = run(answer(service, user, first, f'「{LEFT}」は誤りです。', 'u344-withdraw'))
    assert saved['state'] == 'COMPLETED' and saved['body_state'] == 'REFINED'
    body = saved['current_observation']['text']
    assert '私も少し安心しました' not in body and '耳を傾けていたい' not in body
    assert 'かもしれないと思うと寂しい' in body and '褒められた' in body
    reopen(user, parent, saved)
    export_dto('update-pair-withdraw', saved)


@pytest.mark.parametrize('after_checkpoint', [False, True], ids=['before_meaning', 'after_old_meaning'])
def test_confirmed_answer_interruption_preserves_meaning_version(qcase, qdb, monkeypatch, after_checkpoint):
    user, parent, service = qcase
    qdb.query('update public.emotions set memo=$2 where id=$1', [parent, MEMO])
    first = run(service.start(user, parent))
    prepare, generate = service.engine.prepare_emlis_update, service.engine.generate

    def interrupted(*_):
        raise asyncio.CancelledError()

    monkeypatch.setattr(service.engine, 'prepare_emlis_update', old_prepare if after_checkpoint else interrupted)
    monkeypatch.setattr(service.engine, 'generate', interrupted)
    with pytest.raises(asyncio.CancelledError):
        run(answer(service, user, first, '今は嬉しい。', 'u344-interruption'))
    pending = run(service.get(user, parent))
    assert pending['failure_code'] == 'worker_interrupted' and pending['can_retry']
    before = run(service.store.read(user, input_id=parent))
    meanings = [e for e in before['events'] if e['kind'] == 'MEANING_UPDATE']
    assert len(meanings) == 1 + int(after_checkpoint)
    monkeypatch.setattr(service.engine, 'generate', generate)
    monkeypatch.setattr(service.engine, 'prepare_emlis_update',
        (lambda *_: pytest.fail('saved meaning must be reused')) if after_checkpoint else prepare)
    saved = run(service.action(user, pending['thread_id'], action='retry_response',
        expected_revision=pending['revision'], idempotency_key='u344-update-retry',
        operation_id=pending['operation_id']))
    after = run(service.store.read(user, input_id=parent))
    current = [e for e in after['events'] if e['kind'] == 'MEANING_UPDATE']
    assert len(current) == 2 and saved['operation_id'] == pending['operation_id']
    assert saved['state'] == 'COMPLETED' and saved['body_state'] == 'REFINED'
    body = saved['current_observation']['text']
    if after_checkpoint:
        assert current == meanings
        assert '私も少し安心しました' not in body.split('Emlisから：', 1)[1]
    else:
        assert_pair_and_answer(body, '今は嬉しい。')
    assert len([e for e in after['events'] if e['kind'] == 'ANSWER']) == 1
    reopen(user, parent, saved)
    export_dto(f'update-retry-{after_checkpoint}', saved)
