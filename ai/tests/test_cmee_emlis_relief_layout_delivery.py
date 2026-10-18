"""Complete old delivery is immutable; a saved current meaning can finish safely."""
import asyncio
from unittest.mock import patch

import pytest
import emlis_ai_grounded_sentence_surface as surface
from test_cmee_emlis_relief_cognition import BASE
from test_cmee_emlis_loneliness_delivery import export_dto, reopen
from test_emlis_q3_application import qdb, qcase
from test_emlis_q2_application import run, answer

MEMO = BASE + '褒められたのに、嬉しくなかった。'
ANSWERS = [
    ('add', '今は嬉しい。'),
    ('revise', '「嬉しくなかった」ではなく「悲しかった」です。'),
    ('withdraw', '「褒められた」は誤りです。'),
]


def assert_short(body):
    observation, reception = body.split('Emlisから：', 1)
    assert 'かもしれない' in observation and 'かもしれない' not in reception
    assert 'その寂しさにも、今、耳を傾けていたいです。' in reception
    assert '私も少し安心しましたが' in reception


@pytest.mark.parametrize('name,text', ANSWERS)
@pytest.mark.parametrize('historical', [False, True], ids=['current', 'u344_completed'])
def test_saved_old_and_current_surface_reopen_exactly(qcase, qdb, name, text, historical):
    user, parent, service = qcase
    qdb.query('update public.emotions set memo=$2 where id=$1', [parent, MEMO])
    first = run(service.start(user, parent))
    if historical:
        # Disable both u345 layout decisions: this is exactly the prior owner
        # behavior, also compared with the untouched u344 frozen public route.
        with patch.object(surface, '_retained_relief_observation_pair', return_value=frozenset()):
            saved = run(answer(service, user, first, text, 'u345-old-body'))
    else:
        saved = run(answer(service, user, first, text, 'u345-current-body'))
    assert saved['state'] == 'COMPLETED' and saved['body_state'] == 'REFINED'
    body = saved['current_observation']['text']
    if historical:
        assert 'かもしれないと思うと寂しいという気持ちにも' in body.split('Emlisから：', 1)[1]
    else:
        assert_short(body)
    assert saved['original'] == first['original']
    observations = [e for e in saved['timeline'] if e['kind'] == 'OBSERVATION']
    assert len(observations) == 2
    assert observations[0]['text'] == first['current_observation']['text']
    assert observations[1]['text'] == body
    assert len([e for e in saved['timeline'] if e['kind'] == 'ANSWER']) == 1
    reopen(user, parent, saved)  # a fresh engine forbids all generation
    export_dto(f'layout-{historical}-{name}', saved)


def test_retry_reuses_saved_current_meaning_and_keeps_one_answer(qcase, qdb, monkeypatch):
    user, parent, service = qcase
    qdb.query('update public.emotions set memo=$2 where id=$1', [parent, MEMO])
    first = run(service.start(user, parent))
    generate = service.engine.generate
    def interrupted(*_):
        raise asyncio.CancelledError()
    monkeypatch.setattr(service.engine, 'generate', interrupted)
    with pytest.raises(asyncio.CancelledError):
        run(answer(service, user, first, '今は嬉しい。', 'u345-interrupted'))
    pending = run(service.get(user, parent))
    before = run(service.store.read(user, input_id=parent))
    meanings = [e for e in before['events'] if e['kind'] == 'MEANING_UPDATE']
    assert len(meanings) == 2 and pending['can_retry']
    monkeypatch.setattr(service.engine, 'generate', generate)
    monkeypatch.setattr(service.engine, 'prepare_emlis_update',
        lambda *_: pytest.fail('saved meaning must be reused'))
    saved = run(service.action(user, pending['thread_id'], action='retry_response',
        expected_revision=pending['revision'], idempotency_key='u345-retry',
        operation_id=pending['operation_id']))
    after = run(service.store.read(user, input_id=parent))
    assert [e for e in after['events'] if e['kind'] == 'MEANING_UPDATE'] == meanings
    assert len([e for e in after['events'] if e['kind'] == 'ANSWER']) == 1
    assert saved['operation_id'] == pending['operation_id']
    assert saved['state'] == 'COMPLETED' and saved['body_state'] == 'REFINED'
    assert_short(saved['current_observation']['text'])
    reopen(user, parent, saved)
    export_dto('layout-retry', saved)
