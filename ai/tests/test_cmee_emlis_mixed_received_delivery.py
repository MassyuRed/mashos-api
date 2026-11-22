"""Time-neutral received observation survives actual saved delivery."""
from unittest.mock import patch
import pytest
from cocolon_meaning_experience_engine import emlis_thread_surface as thread_surface
from test_cmee_emlis_negative_revision_delivery import begin_case, events, persisted
from test_cmee_emlis_negative_revision_surface import ROWS
from test_cmee_emlis_loneliness_delivery import export_dto, reopen
from test_cmee_emlis_relief_received_delivery import record_operation_times
from test_emlis_q3_application import qdb, qcase
from test_emlis_q2_application import run, answer

NEUTRAL = '「褒められた」のに「嬉しくなかった」という経験が書かれています。'
OLD = '「褒められた」と「嬉しくなかった」が、異なる向きのまま同時にあります。'


@pytest.mark.parametrize('tier', ['free', 'premium'])
@pytest.mark.parametrize('unknown', [False, True])
def test_initial_and_real_pending_add_keep_complete_saved_body(qcase, qdb, tier, unknown):
    user, parent, service = qcase
    memo = ROWS['mixed_unknown_current_negative', 'q3']['memo']
    if not unknown: memo = memo.split('何が不安なのか')[0]
    assert 'code' not in qdb.query('update public.emotions set memo=$2 where id=$1', [parent, memo])
    assert 'code' not in qdb.query('update public.profiles set subscription_tier=$2 where id=$1', [user, tier])
    first = run(service.start(user, parent))
    assert first['state'] == 'AWAITING_ANSWER' and first['pending_question']
    assert NEUTRAL in first['current_observation']['text']
    assert '同時に' not in first['current_observation']['text']
    reopen(user, parent, first)
    export_dto(f'u355-initial-{tier}-{unknown}', first)
    saved = run(answer(service, user, first, '今は少し嬉しい。'))
    assert saved['body_state'] == 'REFINED' and saved['answer_saved'] and saved['meaning_updated']
    assert saved['original'] == first['original']
    body = saved['current_observation']['text']
    assert '褒められた' in body and '嬉しくなかった' in body and '少し嬉しい' in body
    assert '同時に' not in body
    snapshot = run(service.store.read(user, input_id=parent))
    assert len(events(snapshot,'ANSWER')) == 1 and len(events(snapshot,'MEANING_UPDATE')) == 2
    reopen(user, parent, saved)
    assert persisted(run(service.store.read(user, input_id=parent))) == persisted(snapshot)
    record_operation_times(snapshot, f'u355-add-{tier}-{unknown}')
    export_dto(f'u355-add-{tier}-{unknown}', saved)


@pytest.mark.parametrize('tier', ['free', 'premium'])
def test_completed_old_observation_is_not_regenerated(qcase, qdb, tier):
    # Recreate the old surface only, save it through the actual service, then
    # remove the hook. New GET/start must return that exact persisted artifact.
    with patch.object(thread_surface, '_current_single_received_contrast_relations', return_value=frozenset()):
        user, parent, service, row, first = begin_case(qcase, qdb, 'mixed_unknown_current_negative', tier)
        saved = run(answer(service, user, first, row['answer']))
    assert saved['state'] == 'COMPLETED' and saved['body_state'] == 'REFINED'
    assert OLD in first['current_observation']['text'] and OLD in saved['current_observation']['text']
    snapshot = run(service.store.read(user, input_id=parent))
    reopen(user, parent, saved)
    assert run(service.get(user,parent)) == saved
    assert persisted(run(service.store.read(user, input_id=parent))) == persisted(snapshot)
    export_dto(f'u355-old-completed-{tier}', saved)
