"""Independent unknown stays saved beside the retained pair and separate answer."""
import asyncio
from contextlib import nullcontext
from unittest.mock import patch

import pytest
from cocolon_meaning_experience_engine import emlis_answer_update as update
from test_cmee_emlis_unknown_pair_retention import ROWS
from test_cmee_emlis_loneliness_delivery import export_dto, reopen
from test_emlis_q3_application import qdb, qcase
from test_emlis_q2_application import run, answer

MEMO = ROWS['now_positive']['memo']
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
@pytest.mark.parametrize('historical', [False, True], ids=['current', 'u345_completed'])
def test_saved_old_and_current_surface_reopen_exactly(qcase, qdb, name, text, historical):
    user, parent, service = qcase
    qdb.query('update public.emotions set memo=$2 where id=$1', [parent, MEMO])
    first = run(service.start(user, parent))
    if historical:
        # The narrow new source proof is the sole added route. Its absence
        # reproduces the frozen u345 checkpoint and prior completed body.
        with patch.object(update, '_independent_unknown_beside_received_pair', return_value=None):
            saved = run(answer(service, user, first, text, 'u346-old-body'))
    else:
        saved = run(answer(service, user, first, text, 'u346-current-body'))
    assert saved['state'] == ('RESPONSE_FAILED' if historical and name!='add' else 'COMPLETED')
    body = (saved['current_observation'] or {}).get('text','')
    if historical:
        assert '私も少し安心しましたが' not in body
        assert saved['body_state']==('REFINED' if name=='add' else 'MEANING_UPDATED_BODY_UNAVAILABLE')
    else:
        assert saved['body_state']=='REFINED'
        assert_short(body)
        assert '何が不安なのか、私にもまだわからない' in body.split('Emlisから：',1)[0]
    assert saved['original'] == first['original']
    observations = [e for e in saved['timeline'] if e['kind'] == 'OBSERVATION']
    assert len(observations) == (1 if historical and name!='add' else 2)
    assert observations[0]['text'] == first['current_observation']['text']
    if len(observations)==2: assert observations[1]['text'] == body
    assert len([e for e in saved['timeline'] if e['kind'] == 'ANSWER']) == 1
    reopen(user, parent, saved)  # a fresh engine forbids all generation
    export_dto(f'unknown-{historical}-{name}', saved)


@pytest.mark.parametrize('historical',[False,True],ids=['current','u345_pending'])
def test_retry_reuses_saved_current_meaning_and_keeps_one_answer(qcase, qdb, monkeypatch,historical):
    user, parent, service = qcase
    qdb.query('update public.emotions set memo=$2 where id=$1', [parent, MEMO])
    first = run(service.start(user, parent))
    generate = service.engine.generate
    def interrupted(*_):
        raise asyncio.CancelledError()
    monkeypatch.setattr(service.engine, 'generate', interrupted)
    with (patch.object(update,'_independent_unknown_beside_received_pair',return_value=None) if historical else nullcontext()):
        with pytest.raises(asyncio.CancelledError):
            run(answer(service, user, first, '今は嬉しい。', 'u346-interrupted'))
    pending = run(service.get(user, parent))
    before = run(service.store.read(user, input_id=parent))
    meanings = [e for e in before['events'] if e['kind'] == 'MEANING_UPDATE']
    assert len(meanings) == 2 and pending['can_retry']
    monkeypatch.setattr(service.engine, 'generate', generate)
    monkeypatch.setattr(service.engine, 'prepare_emlis_update',
        lambda *_: pytest.fail('saved meaning must be reused'))
    saved = run(service.action(user, pending['thread_id'], action='retry_response',
        expected_revision=pending['revision'], idempotency_key='u346-retry',
        operation_id=pending['operation_id']))
    after = run(service.store.read(user, input_id=parent))
    assert [e for e in after['events'] if e['kind'] == 'MEANING_UPDATE'] == meanings
    assert len([e for e in after['events'] if e['kind'] == 'ANSWER']) == 1
    assert saved['operation_id'] == pending['operation_id']
    assert saved['state'] == 'COMPLETED' and saved['body_state'] == 'REFINED'
    if historical: assert '私も少し安心しましたが' not in saved['current_observation']['text']
    else: assert_short(saved['current_observation']['text'])
    assert '何が不安なのか、私にもまだわからない' in saved['current_observation']['text']
    reopen(user, parent, saved)
    export_dto(f'unknown-retry-{historical}', saved)
