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
def test_later_frame_view_keeps_exact_previously_displayed_person_revision(natural_case, qdb, status, text):
    user, parent, service, calls, _, _ = _case(natural_case, qdb)
    initial = run(service.start(user, parent))
    frame, = initial['interpretive_frames']
    revised = _feedback(service, user, initial, frame, 'REVISED', REVISION)
    view, = revised['interpretive_frames']
    assert view['frame_ref'] != frame['frame_ref']
    changed = _feedback(service, user, revised, view, status, text, 'second-frame-context')
    run(answer(service, user, changed, '今は、私は嬉しい。'))
    feedback, = json.loads(calls[-1].material_json)['user_frame_feedback']
    assert feedback['target_binding'] == 'BOUND'
    target = feedback['target_user_revision']
    assert target['source_role'] == 'USER_FRAME_REVISION_CONTEXT'
    assert 'target_ai_interpretation' not in feedback
    assert target['received_meaning'] == REVISION
    assert target['received_meaning'] != frame['received_meaning']
    assert feedback['status'] == status and feedback['correction_text'] == text and feedback['version'] == 2
    assert len(calls) == 2
    fetched = run(service.get(user, parent))
    assert len(calls) == 2 and 'frame_feedback_target' not in json.dumps(fetched)


@pytest.mark.parametrize('mutation', ['missing', 'version', 'frame_ref', 'input_id', 'guard', 'duplicate'])
def test_uncaptured_or_mismatched_later_target_remains_unresolved(natural_case, qdb, mutation):
    user, parent, service, calls, _, _ = _case(natural_case, qdb)
    initial = run(service.start(user, parent))
    revised = _feedback(service, user, initial, initial['interpretive_frames'][0], 'REVISED', REVISION)
    _feedback(service, user, revised, revised['interpretive_frames'][0], 'REJECTED', key='later-target')
    snapshot = run(service._hydrate(user, run(service.store.read(user, input_id=parent))))
    event = next(e for e in snapshot['events'] if e.get('idempotency_key') == 'later-target')
    context = event['payload']['frame_feedback_target']
    if mutation == 'missing':
        event['payload'].pop('frame_feedback_target')
    elif mutation == 'duplicate':
        snapshot['events'].append(dict(event, id=str(uuid4())))
    elif mutation == 'guard':
        context['source_guard'][1] = 'foreign'
    else:
        context[{'version':'feedback_version'}.get(mutation, mutation)] = 'foreign'
    material, _ = prepare_natural_reply(_request(snapshot))
    feedback, = json.loads(material.material_json)['user_frame_feedback']
    assert feedback['target_binding'] == 'UNRESOLVED' and 'target_ai_interpretation' not in feedback


def test_other_thread_uses_captured_prior_revision(natural_case, qdb):
    user, parent, service, calls, _, _ = _case(natural_case, qdb)
    initial = run(service.start(user, parent))
    revised = _feedback(service, user, initial, initial['interpretive_frames'][0], 'REVISED', REVISION)
    _feedback(service, user, revised, revised['interpretive_frames'][0], 'REJECTED', key='later-target')
    run(service.start(user, _fresh(qdb, user)))
    feedback, = json.loads(calls[-1].material_json)['user_frame_feedback']
    assert feedback['target_binding'] == 'BOUND'
    assert feedback['target_user_revision']['received_meaning'] == REVISION


def _cross_frame(natural_case, qdb, *, second_status='REJECTED', second_text=None):
    user, parent, service, calls, past, _ = _case(natural_case, qdb)
    # B can find A, while C's words match A and not B. B must not consume an
    # extra history slot or become an unrequested source body in C.
    qdb.query('update public.emotions set memo=$2 where id=$1', [parent, '嬉しくない。'])
    initial = run(service.start(user, parent))
    revised = _feedback(service, user, initial, initial['interpretive_frames'][0], 'REVISED', REVISION)
    changed = _feedback(service, user, revised, revised['interpretive_frames'][0], second_status, second_text, key='cross-target')
    current = _fresh(qdb, user)
    qdb.query('update public.emotions set memo=$2 where id=$1', [current, '褒められたのに、悲しかった。'])
    return user, parent, current, past, service, calls, changed


def test_cross_frame_target_reaches_new_saved_reply_and_non_generating_get(natural_case, qdb):
    user, parent, current, past, service, calls, _ = _cross_frame(natural_case, qdb)
    dto = run(service.start(user, current))
    material = json.loads(calls[-1].material_json)
    assert [r['input_id'] for r in material['past_user_records']] == [past]
    feedback, = material['user_frame_feedback']
    assert feedback['target_binding'] == 'BOUND'
    assert feedback['target_user_revision']['received_meaning'] == REVISION
    snapshot = run(service._hydrate(user, run(service.store.read(user, input_id=current))))
    deps, = snapshot['thread']['data']['frame_target_dependencies']
    assert deps[2] == parent and len(deps) == 6
    assert snapshot['thread']['data']['context_guards'][0][0] == past
    for _ in range(2):
        assert run(service.get(user, current)) == dto
    assert len(calls) == 2
    assert 'target_operations' not in json.dumps(dto) and 'frame_target_dependencies' not in json.dumps(dto)


def test_cross_frame_can_be_revised_again_in_the_consuming_record(natural_case, qdb):
    previous='ほめ方への戸惑いでした。'
    user, parent, current, past, service, calls, _ = _cross_frame(natural_case, qdb,
        second_status='REVISED',second_text=previous)
    dto=run(service.start(user,current))
    frame,=dto['interpretive_frames']
    changed=_feedback(service,user,dto,frame,'REVISED','その場の受け取り方を言い直します。',key='third-frame-change')
    assert changed['interpretive_frames'][0]['correction_text']=='その場の受け取り方を言い直します。'
    run(answer(service,user,changed,'今は、私は嬉しい。'))
    assert json.loads(calls[-1].material_json)['user_frame_feedback'][0]['target_user_revision']['received_meaning']==previous
    assert len(calls)==3


@pytest.mark.parametrize('change', ['edited', 'deleted', 'foreign', 'duplicate', 'duplicate_bad_fingerprint', 'version', 'uncaptured'])
def test_cross_frame_invalid_origin_is_not_bound(natural_case, qdb, change):
    user, parent, current, past, service, calls, _ = _cross_frame(natural_case, qdb)
    if change == 'edited':
        qdb.query('update public.emotions set memo=$2 where id=$1', [parent, '書き直した記録。'])
    elif change == 'deleted':
        qdb.query('delete from public.emotions where id=$1', [parent])
    elif change == 'foreign':
        other = str(uuid4()); qdb.query('insert into auth.users values ($1)', [other])
        qdb.query('update public.emlis_input_threads set user_id=$2 where original_emotion_id=$1', [parent, other])
    elif change.startswith('duplicate'):
        qdb.query("insert into public.emlis_thread_events(id,thread_id,seq,kind,round_index,payload) select $1,thread_id,seq+100,kind,round_index,case when $3 then jsonb_set(payload,'{request_fingerprint}','\"invalid\"'::jsonb) else payload end from public.emlis_thread_events where idempotency_key='cross-target' and thread_id=(select id from public.emlis_input_threads where original_emotion_id=$2)", [str(uuid4()), parent, change=='duplicate_bad_fingerprint'])
    elif change == 'version':
        qdb.query('update public.emlis_frame_feedback set version=version+1 where user_id=$1', [user])
    else:
        qdb.query("update public.emlis_thread_events set payload=payload-'frame_feedback_target' where idempotency_key='cross-target' and thread_id=(select id from public.emlis_input_threads where original_emotion_id=$1)", [parent])
    run(service.start(user, current))
    feedback, = json.loads(calls[-1].material_json)['user_frame_feedback']
    assert feedback['target_binding'] == 'UNRESOLVED'
    assert 'target_user_revision' not in feedback and 'target_ai_interpretation' not in feedback


@pytest.mark.parametrize('change', ['edited', 'deleted', 'operation'])
def test_cross_frame_origin_change_hides_saved_reply_without_generation(natural_case, qdb, change):
    user, parent, current, past, service, calls, _ = _cross_frame(natural_case, qdb)
    dto = run(service.start(user, current))
    assert dto['current_observation']
    if change == 'edited':
        qdb.query('update public.emotions set memo=$2 where id=$1', [parent, '書き直した記録。'])
    elif change == 'deleted':
        qdb.query('delete from public.emotions where id=$1', [parent])
    else:
        qdb.query("delete from public.emlis_thread_events where idempotency_key='cross-target' and thread_id=(select id from public.emlis_input_threads where original_emotion_id=$1)", [parent])
    fetched = run(service.get(user, current))
    assert fetched['current_observation'] is None and fetched['body_state'] == 'CONTEXT_CHANGED'
    assert not any(e['kind'] == 'OBSERVATION' for e in fetched['timeline'])
    assert len(calls) == 2


def test_cross_frame_unrelated_origin_operation_preserves_saved_reply(natural_case,qdb):
    user,parent,current,past,service,calls,_=_cross_frame(natural_case,qdb)
    dto=run(service.start(user,current))
    qdb.query('update public.emlis_input_threads set revision=revision+1 where original_emotion_id=$1',[parent])
    assert run(service.get(user,current))==dto and len(calls)==2


def test_cross_frame_origin_change_during_provider_cannot_save_reply(natural_case, qdb):
    user, parent, current, past, service, calls, _ = _cross_frame(natural_case, qdb)
    original_provider = service.natural_reply_source
    async def racing_provider(material):
        reply = await original_provider(material)
        qdb.query('update public.emotions set memo=$2 where id=$1', [parent, '生成中に変更した記録。'])
        return reply
    service.natural_reply_source = racing_provider
    from emlis_thread_store import ThreadStoreError
    with pytest.raises(ThreadStoreError, match='thread_conflict'):
        run(service.start(user, current))
    snapshot = run(service.store.read(user, input_id=current))
    assert not any(e['kind'] == 'OBSERVATION' for e in snapshot['events'])
    assert len(calls) == 2


@pytest.mark.parametrize('downgrade', ['free','plus'])
def test_cross_frame_target_does_not_expand_lower_plan_material(natural_case, qdb, downgrade):
    user, parent, current, past, service, calls, _ = _cross_frame(natural_case, qdb)
    qdb.query('update public.profiles set subscription_tier=$2 where id=$1',[user,downgrade])
    run(service.start(user,current))
    material=json.loads(calls[-1].material_json)
    assert material['user_frame_feedback']==[]
    snapshot=run(service.store.read(user,input_id=current))
    assert snapshot['thread']['data']['frame_target_dependencies']==[]


@pytest.mark.parametrize('changed', [False, True])
def test_cross_frame_received_receipt_restarts_without_acquiring_again(natural_case,qdb,monkeypatch,changed):
    import httpx
    import emlis_thread_store
    user, parent, current, past, service, calls, _ = _cross_frame(natural_case,qdb)
    failed=False
    async def rpc(name,payload,**kwargs):
        nonlocal failed
        if not failed and any(e['kind']=='OBSERVATION' for e in payload.get('p_events',[])):
            failed=True
            return httpx.Response(503,json={'code':'57P03'})
        return await qdb.rpc(name,payload,**kwargs)
    monkeypatch.setattr(emlis_thread_store,'sb_post_rpc',rpc)
    dto=run(service.start(user,current))
    assert dto['can_retry'] and len(calls)==2
    if changed:
        qdb.query('update public.emotions set memo=$2 where id=$1',[parent,'再開前に変更した記録。'])
        fetched=run(service.get(user,current))
        assert not fetched['can_retry'] and fetched['current_observation'] is None
    else:
        result=run(service.action(user,dto['thread_id'],action='retry_response',
            expected_revision=dto['revision'],idempotency_key='cross-receipt-restart',operation_id=dto['operation_id']))
        assert result['current_observation'] and len(calls)==2


def test_new_context_does_not_change_feedback_evidence_identity(natural_case, qdb):
    user, parent, service, calls, _, _, _, _, _ = _after(natural_case, qdb, 'REVISED', REVISION)
    snapshot = run(service._hydrate(user, run(service.store.read(user, input_id=parent))))
    feedback, = _request(snapshot).emlis_thread.frame_feedback_sources
    assert feedback.target_context_json
    assert feedback.evidence_ref == replace(feedback, target_context_json=None).evidence_ref


def test_refined_saved_frame_then_second_revision_keeps_displayed_text(natural_case, qdb):
    user, parent, service, calls, _, _, _, _, final = _after(natural_case, qdb, 'REVISED', REVISION)
    frame, = final['interpretive_frames']
    assert frame['received_meaning'] == frame['correction_text'] == REVISION
    _feedback(service, user, final, frame, 'REVISED', '周りの評価より、自分の納得が大切だった。', key='after-refined')
    snapshot = run(service._hydrate(user, run(service.store.read(user, input_id=parent))))
    material, _ = prepare_natural_reply(_request(snapshot))
    feedback, = json.loads(material.material_json)['user_frame_feedback']
    assert feedback['target_binding'] == 'BOUND'
    assert feedback['target_user_revision']['received_meaning'] == REVISION
    assert feedback['target_user_revision']['source_role'] == 'USER_FRAME_REVISION_CONTEXT'
    assert 'target_ai_interpretation' not in feedback
    assert len(calls) == 2


def test_previous_unsafe_revision_does_not_reenter_as_target_context(natural_case, qdb):
    user, parent, service, calls, _, _ = _case(natural_case, qdb)
    initial = run(service.start(user, parent))
    revised = _feedback(service, user, initial, initial['interpretive_frames'][0], 'REVISED', '自分には価値がない。')
    changed = _feedback(service, user, revised, revised['interpretive_frames'][0], 'REVISED', REVISION, key='safe-revision')
    run(answer(service, user, changed, '今は、私は嬉しい。'))
    feedback, = json.loads(calls[-1].material_json)['user_frame_feedback']
    assert feedback['target_binding'] == 'UNRESOLVED' and 'target_ai_interpretation' not in feedback
    assert feedback['correction_text'] == REVISION


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
