"""Existing Premium frames over current natural replies and real isolated SQL.

The reply provider is synthetic. Frames are derived from actual saved user
sources by the existing owner; this does not assess real-model prose quality.
"""
import json
import os
from pathlib import Path
from uuid import uuid4

import pytest

from cocolon_meaning_experience_engine.natural_reply import NaturalReply
from emlis_thread_service import EmlisThreadService, Q3_PROFILE
from test_emlis_natural_reply_application import natural_case
from test_emlis_q2_application import answer, run
from test_emlis_q3_application import qdb

MEMO = '褒められたのに、嬉しくなかった。'
BODY = '褒められても嬉しくなかったのですね。'
REVISION = '結果だけで判断されたことが気になった。'


def _past(qdb, user, *, text='その時は重かった。', natural=False):
    past = str(uuid4())
    qdb.query("insert into public.emotions values ($1,$2,(now()-interval '1 day') at time zone 'UTC',$3,'',array['仕事'],array['不安'],$4)",
        [past, user, MEMO, json.dumps([dict(type='不安', strength='medium')])])
    async def provider(material):
        return NaturalReply(BODY, 'synthetic-natural-frame', material.source_prefix_ref)
    service = (EmlisThreadService(runtime_profile=Q3_PROFILE, natural_reply_source=provider)
               if natural else EmlisThreadService())
    started = run(service.start(user, past))
    completed = run(answer(service, user, started, text))
    return past, service, completed


def _case(natural_case, qdb, *, tier='premium', history=True):
    user, parent, service, calls = natural_case
    qdb.query('update public.profiles set subscription_tier=$2 where id=$1', [user, tier])
    qdb.query('update public.emotions set memo=$2 where id=$1', [parent, MEMO])
    async def provider(material):
        calls.append(material)
        return NaturalReply(BODY, 'synthetic-natural-frame', material.source_prefix_ref)
    service.natural_reply_source = provider
    past, old, dto = _past(qdb, user) if history else (None, None, None)
    return user, parent, service, calls, past, dto


def _evidence(name, **data):
    destination = os.environ.get('NATURAL_FRAME_EVIDENCE_DIR')
    if destination:
        folder = Path(destination)
        folder.mkdir(parents=True, exist_ok=True)
        (folder/(name+'.private.json')).write_text(json.dumps(dict(
            provider='synthetic; no GPU', database='isolated PGlite; not live Auth/PostgREST',
            **data), ensure_ascii=False, indent=2)+'\n')


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
def test_natural_saved_reply_exposes_only_existing_premium_frames(natural_case, qdb, tier):
    user, parent, service, calls, past, old = _case(natural_case, qdb, tier=tier)
    before = qdb.query('select * from public.emotions where id in ($1,$2) order by id', [parent, past])
    dto = run(service.start(user, parent))
    assert dto['state'] == 'AWAITING_ANSWER' and dto['current_observation']['text'] == BODY
    assert bool(dto['interpretive_frames']) == (tier == 'premium')
    snapshot = run(service.store.read(user, input_id=parent))
    artifact = next(e['payload']['artifact'] for e in snapshot['events'] if e['kind'] == 'OBSERVATION')
    if tier == 'premium':
        frame, = dto['interpretive_frames']
        assert frame['input_id'] == past and frame['status'] == 'TENTATIVE'
        assert frame['trigger'] == '褒められた' and frame['received_meaning'] == '重かった'
        private, = artifact['interpretive_frames']
        assert private['evidence_refs'] and private['frame_ref'] == frame['frame_ref']
    else:
        assert 'interpretive_frames' not in artifact
    material = json.loads(calls[0].material_json)
    assert 'interpretive_frames' not in material
    assert old['current_observation']['text'] not in calls[0].material_json
    assert before == qdb.query('select * from public.emotions where id in ($1,$2) order by id', [parent, past])
    assert len(calls) == 1
    _evidence('natural-frame-'+tier, dto=dto, snapshot=snapshot, author_material=material,
        provider_calls=len(calls))


@pytest.mark.parametrize('status,text', [('CONFIRMED', None), ('REJECTED', None), ('REVISED', REVISION)])
def test_person_controls_saved_frame_and_next_natural_reply_uses_feedback(natural_case, qdb, status, text):
    user, parent, service, calls, past, _ = _case(natural_case, qdb)
    dto = run(service.start(user, parent))
    frame, = dto['interpretive_frames']
    changed = run(service.frame_feedback(user, dto['thread_id'], frame_ref=frame['frame_ref'],
        status=status, correction_text=text, expected_revision=dto['revision'], idempotency_key='frame-'+status))
    assert changed['interpretive_frames'][0]['status'] == status
    assert changed['current_observation'] is None and changed['body_state'] == 'CONTEXT_CHANGED'
    assert len(calls) == 1, 'feedback saves without generating another reply'
    repeated = run(service.frame_feedback(user, dto['thread_id'], frame_ref=frame['frame_ref'],
        status=status, correction_text=text, expected_revision=dto['revision'], idempotency_key='frame-'+status))
    assert repeated['requested_operation']['idempotency_key'] == 'frame-'+status
    assert {k: v for k, v in repeated.items() if k != 'requested_operation'} == changed
    after = run(answer(service, user, changed, '今は、私は嬉しい。'))
    assert after['current_observation']['text'] == BODY and after['body_state'] == 'REFINED'
    assert len(calls) == 2
    feedback, = json.loads(calls[-1].material_json)['user_frame_feedback']
    assert feedback['source_role'] == 'USER_FRAME_FEEDBACK' and feedback['input_id'] == past
    assert feedback['status'] == status and feedback['correction_text'] == text
    if status == 'REJECTED':
        assert after['interpretive_frames'] == []
    else:
        active, = after['interpretive_frames']
        assert active['status'] == status
        assert active['received_meaning'] == (text if text else frame['received_meaning'])
    assert len(qdb.query('select * from public.emlis_frame_feedback where user_id=$1', [user])['rows']) == 1
    _evidence('natural-frame-'+status.lower(), initial=dto, feedback=changed, after=after,
        author_material=json.loads(calls[-1].material_json), provider_calls=len(calls))


def test_saved_read_never_derives_frames_or_calls_provider_again(natural_case, qdb, monkeypatch):
    user, parent, service, calls, _, _ = _case(natural_case, qdb)
    dto = run(service.start(user, parent))
    assert dto['interpretive_frames']
    import cocolon_meaning_experience_engine.emlis_thread_history as owner
    def forbidden(*args, **kwargs):
        raise AssertionError('GET cannot rebuild frames')
    monkeypatch.setattr(owner, 'derive_interpretive_frames', forbidden)
    reopened = EmlisThreadService(runtime_profile=Q3_PROFILE)
    for _ in range(2):
        read = run(reopened.get(user, parent))
        assert read['interpretive_frames'] == dto['interpretive_frames']
        assert read['current_observation'] == dto['current_observation']
        assert read['can_write'] is False
    assert len(calls) == 1


@pytest.mark.parametrize('change', ['edit', 'delete'])
def test_changed_history_hides_old_frame_without_regenerating(natural_case, qdb, change):
    user, parent, service, calls, past, _ = _case(natural_case, qdb)
    dto = run(service.start(user, parent))
    assert dto['interpretive_frames']
    if change == 'edit':
        qdb.query('update public.emotions set memo=$2 where id=$1', [past, '別の記録です。'])
    else:
        qdb.query('delete from public.emotions where id=$1', [past])
    reread = run(service.get(user, parent))
    assert reread['interpretive_frames'] == [] and reread['current_observation'] is None
    assert len(calls) == 1


def test_downgrade_hides_premium_frames_without_regenerating(natural_case, qdb):
    user, parent, service, calls, _, _ = _case(natural_case, qdb)
    dto = run(service.start(user, parent))
    assert dto['interpretive_frames']
    qdb.query("update public.profiles set subscription_tier='plus' where id=$1", [user])
    assert run(service.get(user, parent))['interpretive_frames'] == []
    assert len(calls) == 1


@pytest.mark.parametrize('explanation', ['違う', '嬉しくないのではなく、ほめ方が気になりました。'])
def test_current_interpretation_correction_does_not_republish_old_frames(natural_case, qdb, explanation):
    user, parent, service, calls, _, _ = _case(natural_case, qdb)
    dto = run(service.start(user, parent))
    # Complete the current question before correcting this saved reply.
    dto = run(service.action(user, dto['thread_id'], action='skip',
        question_id=dto['pending_question']['question_id'], expected_revision=dto['revision'],
        idempotency_key='finish-before-correction'))
    assert dto['interpretive_frames'] and dto['can_correct']
    changed = run(service.correct_interpretation(user, dto['thread_id'],
        target_event_id=dto['current_observation']['event_id'], target_text='嬉しくなかった',
        explanation=explanation, expected_revision=dto['revision'], idempotency_key='correction'))
    assert changed['correction_saved'] and changed['interpretive_frames'] == []
    assert run(service.get(user, parent))['interpretive_frames'] == []


def test_corrected_history_is_not_promoted_to_a_frame(natural_case, qdb):
    user, parent, service, calls, _, _ = _case(natural_case, qdb, history=False)
    past, old, dto = _past(qdb, user, natural=True)
    corrected = run(old.correct_interpretation(user, dto['thread_id'],
        target_event_id=dto['current_observation']['event_id'], target_text='嬉しくなかった',
        explanation='嬉しくないのではなく、ほめ方が気になりました。',
        expected_revision=dto['revision'], idempotency_key='past-correction'))
    assert corrected['correction_saved']
    current = run(service.start(user, parent))
    assert current['interpretive_frames'] == []
    record, = json.loads(calls[0].material_json)['past_user_records']
    assert record['input_id'] == past and record['interpretation_corrections']


@pytest.mark.parametrize('text', ['まだ分かりません。', '自分には価値がない。'])
def test_unresolved_or_safety_excluded_history_never_becomes_a_frame(natural_case, qdb, text):
    user, parent, service, calls, _, _ = _case(natural_case, qdb, history=False)
    _past(qdb, user, text=text)
    current = run(service.start(user, parent))
    assert current['current_observation']['text'] == BODY
    assert current['interpretive_frames'] == [] and len(calls) == 1
    if text == '自分には価値がない。':
        assert json.loads(calls[0].material_json)['past_user_records'] == []


def test_optional_frame_derivation_failure_preserves_valid_saved_natural_reply(natural_case, qdb, monkeypatch):
    user, parent, service, calls, _, _ = _case(natural_case, qdb)
    import cocolon_meaning_experience_engine.emlis_thread_history as owner
    def unsupported(*args, **kwargs):
        raise ValueError('optional history cannot be interpreted')
    monkeypatch.setattr(owner, 'derive_interpretive_frames', unsupported)
    current = run(service.start(user, parent))
    assert current['current_observation']['text'] == BODY
    assert current['interpretive_frames'] == [] and len(calls) == 1
