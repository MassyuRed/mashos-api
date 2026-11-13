"""Bind existing person feedback to an exact original frame, as AI context.

All inputs/provider replies are synthetic; SQL/source admission are real and
isolated. These tests do not assess the prose of a real model.
"""
from dataclasses import replace
import json
import os
from pathlib import Path
from uuid import uuid4

import pytest

from cocolon_meaning_experience_engine.natural_reply import prepare_natural_reply
from emlis_thread_service import _request
from test_emlis_natural_frames_application import _case, _past, MEMO, REVISION
from test_emlis_natural_reply_application import natural_case
from test_emlis_q2_application import answer, run
from test_emlis_q3_application import qdb


def _fresh(qdb, user):
    parent = str(uuid4())
    qdb.query("insert into public.emotions values ($1,$2,now() at time zone 'UTC',$3,'',array['仕事'],array['不安'],$4)",
        [parent, user, MEMO, json.dumps([dict(type='不安', strength='medium')])])
    return parent


def _feedback(service, user, dto, frame, status, text=None, key='frame-context'):
    return run(service.frame_feedback(user, dto['thread_id'], frame_ref=frame['frame_ref'],
        status=status, correction_text=text, expected_revision=dto['revision'], idempotency_key=key))


def _after(natural_case, qdb, status, text=None):
    user, parent, service, calls, past, _ = _case(natural_case, qdb)
    initial = run(service.start(user, parent))
    frame, = initial['interpretive_frames']
    changed = _feedback(service, user, initial, frame, status, text)
    assert len(calls) == 1
    final = run(answer(service, user, changed, '今は、私は嬉しい。'))
    assert len(calls) == 2
    return user, parent, service, calls, past, initial, frame, changed, final


@pytest.mark.parametrize('status', ['CONFIRMED', 'REJECTED', 'REVISED'])
def test_exact_original_frame_context_stays_separate_from_person_feedback(natural_case, qdb, status):
    text = REVISION if status == 'REVISED' else None
    user, parent, service, calls, past, initial, frame, changed, final = _after(natural_case, qdb, status, text)
    material = json.loads(calls[-1].material_json)
    feedback, = material['user_frame_feedback']
    assert feedback['source_role'] == 'USER_FRAME_FEEDBACK'
    assert feedback['input_id'] == past and feedback['status'] == status
    assert feedback['correction_text'] == text
    assert feedback['frame_key'] == frame['frame_key'] and feedback['frame_ref'] == frame['frame_ref']
    assert feedback['target_binding'] == 'BOUND'
    target = feedback['target_ai_interpretation']
    assert target['source_role'] == 'AI_INTERPRETATION_CONTEXT' and target['scope'] == 'PAST_RECORD_FRAME'
    assert target['trigger'] == frame['trigger'] and target['received_meaning'] == frame['received_meaning']
    assert target['evidence_refs'] and target['source_recorded_at'] == frame['recorded_at']
    assert target['received_meaning'] != text
    if status == 'REJECTED':
        assert final['interpretive_frames'] == [], 'target context never reactivates a rejected frame'
    assert all(k not in json.dumps(final) for k in ('target_binding', 'target_ai_interpretation'))
    folder = os.environ.get('FRAME_CONTEXT_EVIDENCE_DIR')
    if folder:
        path = Path(folder); path.mkdir(parents=True, exist_ok=True)
        (path/(status.lower()+'.private.json')).write_text(json.dumps(dict(
            synthetic_provider=True, isolated_sql=True, initial=initial, feedback=changed, final=final,
            material=material, source_prefix_ref=calls[-1].source_prefix_ref), ensure_ascii=False, indent=2)+'\n')


@pytest.mark.parametrize('status,text', [('REJECTED', None), ('REVISED', 'ほめ方への戸惑いでした。')])
def test_later_frame_view_cannot_be_reconstructed_from_original_mapping(natural_case, qdb, status, text):
    user, parent, service, calls, _, _ = _case(natural_case, qdb)
    initial = run(service.start(user, parent))
    frame, = initial['interpretive_frames']
    revised = _feedback(service, user, initial, frame, 'REVISED', REVISION)
    view, = revised['interpretive_frames']
    assert view['frame_ref'] != frame['frame_ref']
    changed = _feedback(service, user, revised, view, status, text, 'second-frame-context')
    run(answer(service, user, changed, '今は、私は嬉しい。'))
    feedback, = json.loads(calls[-1].material_json)['user_frame_feedback']
    assert feedback['target_binding'] == 'UNRESOLVED'
    assert 'target_ai_interpretation' not in feedback
    assert feedback['status'] == status and feedback['correction_text'] == text and feedback['version'] == 2


def test_changed_past_source_does_not_bind_old_frame_version(natural_case, qdb):
    user, parent, service, calls, past, _ = _case(natural_case, qdb)
    initial = run(service.start(user, parent))
    _feedback(service, user, initial, initial['interpretive_frames'][0], 'REJECTED')
    qdb.query('update public.emotions set memo_action=$2 where id=$1', [past, '資料を読み直した。'])
    run(service.start(user, _fresh(qdb, user)))
    rows = json.loads(calls[-1].material_json)['user_frame_feedback']
    assert all(f['target_binding'] == 'UNRESOLVED' and 'target_ai_interpretation' not in f for f in rows)


@pytest.mark.parametrize('tier', ['free', 'plus'])
def test_target_projection_does_not_expand_other_plan_material(natural_case, qdb, tier):
    user, parent, service, calls, _, _ = _case(natural_case, qdb)
    initial = run(service.start(user, parent))
    _feedback(service, user, initial, initial['interpretive_frames'][0], 'REVISED', REVISION)
    qdb.query('update public.profiles set subscription_tier=$2 where id=$1', [user, tier])
    dto = run(service.start(user, _fresh(qdb, user)))
    assert dto['interpretive_frames'] == []
    rows = json.loads(calls[-1].material_json)['user_frame_feedback']
    if tier == 'free':
        assert rows == []
    else:
        assert all(set(r) == {'source_role','input_id','status','correction_text','version','updated_at'} for r in rows)


def test_corrected_history_is_not_recovered_as_old_target(natural_case, qdb):
    user, parent, service, calls, _, _ = _case(natural_case, qdb, history=False)
    past, old, dto = _past(qdb, user, natural=True)
    initial = run(service.start(user, parent))
    old_frame = initial['interpretive_frames'][0]
    run(old.correct_interpretation(user, dto['thread_id'],
        target_event_id=dto['current_observation']['event_id'], target_text='嬉しくなかった',
        explanation='嬉しくないのではなく、ほめ方が気になりました。',
        expected_revision=dto['revision'], idempotency_key='past-context-correction'))
    # A historical stale feedback row must not resurrect the interpretation.
    # The current API cannot newly accept this now-invalid view.
    from emlis_thread_store import ThreadStoreError
    with pytest.raises(ThreadStoreError):
        _feedback(service, user, initial, old_frame, 'REJECTED')
    qdb.query("insert into public.emlis_frame_feedback(user_id,source_emotion_id,frame_key,frame_ref,status) values ($1,$2,$3,$4,'REJECTED')",
        [user,past,old_frame['frame_key'],old_frame['frame_ref']])
    run(service.start(user, _fresh(qdb, user)))
    material = json.loads(calls[-1].material_json)
    assert all(f['target_binding'] == 'UNRESOLVED' and 'target_ai_interpretation' not in f
               for f in material['user_frame_feedback'])
    record = next(r for r in material['past_user_records'] if r['input_id'] == past)
    assert record['interpretation_corrections']


def test_unsafe_history_cannot_reenter_through_target_context(natural_case, qdb):
    user, parent, service, calls, _, _ = _case(natural_case, qdb)
    initial = run(service.start(user, parent))
    changed = _feedback(service, user, initial, initial['interpretive_frames'][0], 'REVISED', '自分には価値がない。')
    run(answer(service, user, changed, '今は、私は嬉しい。'))
    material = json.loads(calls[-1].material_json)
    assert material['past_user_records'] == [] and material['user_frame_feedback'] == []


def test_optional_derivation_failure_preserves_original_person_feedback(natural_case, qdb, monkeypatch):
    user, parent, service, calls, _, _, _, _, _ = _after(natural_case, qdb, 'REVISED', REVISION)
    async def snapshot():
        return await service._hydrate(user, await service.store.read(user, input_id=parent))
    request = _request(run(snapshot()))
    import cocolon_meaning_experience_engine.emlis_thread_history as owner
    def unsupported(*args):
        raise ValueError('optional frame target not available')
    monkeypatch.setattr(owner, 'derive_interpretive_frames', unsupported)
    material, safety = prepare_natural_reply(request)
    assert safety.normal_observation_allowed
    feedback, = json.loads(material.material_json)['user_frame_feedback']
    assert feedback['status'] == 'REVISED' and feedback['correction_text'] == REVISION
    assert feedback['target_binding'] == 'UNRESOLVED' and 'target_ai_interpretation' not in feedback


def test_without_feedback_existing_material_has_no_new_control(natural_case, qdb):
    user, parent, service, calls, _, _ = _case(natural_case, qdb)
    run(service.start(user, parent))
    material = json.loads(calls[0].material_json)
    assert material['user_frame_feedback'] == []
    assert 'target_ai_interpretation' not in calls[0].material_json
