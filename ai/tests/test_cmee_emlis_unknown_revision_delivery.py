"""Current time correction and immutable u350 saved bodies reach actual SQL DTOs."""
from unittest.mock import patch

import pytest
from cocolon_meaning_experience_engine import emlis_answer_update as update
from test_cmee_emlis_unknown_revision_time import ROWS
from test_cmee_emlis_loneliness_delivery import export_dto, reopen
from test_cmee_emlis_relief_received_delivery import record_operation_times
from test_emlis_q3_application import qdb, qcase
from test_emlis_q2_application import run, answer


@pytest.mark.parametrize('tier', ['free', 'premium'])
@pytest.mark.parametrize('historical', [False, True], ids=['current', 'u350_saved'])
def test_current_revision_and_completed_old_body_survive_saved_reads(qcase, qdb, tier, historical):
    user, parent, service = qcase
    row = ROWS['mixed_unknown_now', 'q3']
    qdb.query('update public.emotions set memo=$2 where id=$1', [parent, row['memo']])
    qdb.query('update public.profiles set subscription_tier=$2 where id=$1', [user, tier])
    first = run(service.start(user, parent))
    assert first['state'] == 'AWAITING_ANSWER', first
    assert '私も少し安心しましたが' in first['current_observation']['text']
    original = update._prepare_emlis_meaning_from_plan_version

    def previous(*args, **kwargs):
        kwargs['legacy_unknown_replacement_time'] = True
        return original(*args, **kwargs)

    if historical:
        # Reproduce the independent u350 fixture through real service storage.
        # This hook is removed before all saved reads and restart checks.
        with patch.object(update, '_prepare_emlis_meaning_from_plan_version', previous):
            saved = run(answer(service, user, first, row['answer']))
    else:
        saved = run(answer(service, user, first, row['answer']))
    assert saved['body_state'] == 'REFINED', saved
    assert saved['answer_saved'] and saved['meaning_updated']
    assert saved['original'] == first['original']
    assert saved['pending_question'] is None and not saved['can_continue']
    body = saved['current_observation']['text']
    if historical:
        assert body == ('見えたこと：\n' + row['artifact_body']['observation']
                        + '\n\nEmlisから：\n' + row['artifact_body']['reception'])
    else:
        assert '回答した時点で嬉しいという気持ちを受け止めています。' in body
        assert 'その時に今は嬉しい' not in body
    reopen(user, parent, saved)
    assert run(service.get(user, parent)) == saved
    stored = run(service.store.read(user, input_id=parent))
    record_operation_times(stored, f'{tier}-{historical}')
    name = f'unknown-current-{tier}-{historical}'
    export_dto(name + '-initial', first)
    export_dto(name + '-saved', saved)
