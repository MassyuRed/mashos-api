"""Recipient reply over the actual Q3 SQL/RPC; provider calls are synthetic.

These checks prove storage/lifecycle behavior, never real-model quality.
"""
import asyncio
from dataclasses import replace
from hashlib import sha256
import json
import re
import time
from uuid import uuid4

import httpx
import pytest

from test_emlis_q2_application import run
from test_emlis_q3_application import qdb
import emlis_thread_store
from emlis_thread_service import EmlisThreadService, Q3_PROFILE
from emlis_thread_store import ThreadStoreError
from cocolon_meaning_experience_engine.natural_reply import (
    NaturalReply, NaturalReplyError, NaturalReplyInput, SelfHostedNaturalReplySource)

BODY = "会議を終えて、少し安心できたのですね。\n\n資料を読み直したことも、今日の記録に残っています。"


def _active_application_owner(monkeypatch, provider, context_mode, *, initial_follow=False):
    from emlis_thread_factory import application_thread_service

    monkeypatch.setenv("COCOLON_EMLIS_THREAD_MODE", "active")
    monkeypatch.setenv("COCOLON_EMLIS_THREAD_RELEASE_APPROVED", "true")
    monkeypatch.setenv("EMLIS_AI_RESPONSE_PROFILE", "natural_reply.v1")
    monkeypatch.setenv("COCOLON_EMLIS_INITIAL_OBSERVATION_FOLLOW", "true" if initial_follow else "")
    if context_mode is None:
        monkeypatch.delenv("COCOLON_EMLIS_CONTEXT_UPDATE", raising=False)
    else:
        monkeypatch.setenv("COCOLON_EMLIS_CONTEXT_UPDATE", context_mode)
    owner = application_thread_service()
    owner.natural_reply_source = provider
    return owner


def test_finite_source_is_compared_without_changing_normal_prompt_and_review_stays_private(natural_case, qdb, monkeypatch):
    user, parent, service, calls = natural_case
    qdb.query("update public.emotions set memo=$2,memo_action='' where id=$1",
              [parent, "私は友人に頼まれた。"])

    async def reply(material):
        calls.append(material)
        assert 'source_meaning_support' not in json.loads(material.material_json)
        return NaturalReply("あなたは友人に頼まれたのですね。", "synthetic-4b", material.source_prefix_ref)

    service.natural_reply_source = reply
    dto = run(service.start(user, parent))
    snapshot = run(service.store.read(user, input_id=parent))
    event = next(e for e in snapshot['events'] if e['kind'] == 'OBSERVATION')
    report = event['payload']['artifact']['meaning_comparison']
    assert report['verdict'] == 'NO_CONFLICT_IN_CHECKED_SCOPE'
    assert report['checked_reply_count'] == 1 and not report['full_reply_semantic_coverage']
    assert snapshot['thread']['data']['analysis_state'] == 'NOT_GENERATED'
    assert event['payload']['artifact']['analysis_state'] == 'NOT_GENERATED'
    assert len(calls) == 1
    public = json.dumps(dto, ensure_ascii=False)
    assert 'meaning_comparison' not in public and 'source_meaning_support' not in public
    from cocolon_meaning_experience_engine.natural_reply import prepare_natural_reply
    from emlis_thread_service import _request
    research, safety = prepare_natural_reply(_request(snapshot), use_meaning_support=True)
    assert safety.normal_observation_allowed
    assert research.source_prefix_ref == calls[0].source_prefix_ref
    # Generic v1 hints regressed actual responses and stay withdrawn even in
    # the explicit research path; their independent comparison still works.
    assert json.loads(research.material_json) == json.loads(calls[0].material_json)

    def never_read_again(*args):
        raise AssertionError('saved GET never reruns the meaning reader')

    import cocolon_meaning_experience_engine.natural_reply_meaning as meaning
    monkeypatch.setattr(meaning, 'compare_reply_meaning', never_read_again)
    for _ in range(2):
        assert run(service.get(user, parent))['current_observation'] == dto['current_observation']
    assert len(calls) == 1


def test_explicit_focus_research_hint_uses_the_same_saved_source_without_public_report(natural_case, qdb):
    user, parent, service, calls = natural_case
    qdb.query("update public.emotions set memo=$2,memo_action='' where id=$1",
              [parent, "姉が呼び止めたのは先生だった。"])

    async def reply(material):
        calls.append(material)
        assert 'source_meaning_support' not in json.loads(material.material_json)
        return NaturalReply("姉は先生を呼び止めたのですね。", "synthetic-4b", material.source_prefix_ref)

    service.natural_reply_source = reply
    dto = run(service.start(user, parent))
    snapshot = run(service.store.read(user, input_id=parent))
    report = next(e for e in snapshot['events'] if e['kind']=='OBSERVATION')['payload']['artifact']['meaning_comparison']
    assert report['verdict']=='NO_CONFLICT_IN_CHECKED_SCOPE' and report['checked_reply_count']==1
    from cocolon_meaning_experience_engine.natural_reply import prepare_natural_reply
    from emlis_thread_service import _request
    research, safety = prepare_natural_reply(_request(snapshot), use_meaning_support=True)
    assert safety.normal_observation_allowed and research.source_prefix_ref==calls[0].source_prefix_ref
    candidate = json.loads(research.material_json)
    hint = candidate.pop('source_meaning_support')['witnesses'][0]
    assert hint['行為者']=='原文の人物表記：姉'
    assert hint['明記された格']==[{'格':'を','原文':'先生'}]
    assert candidate==json.loads(calls[0].material_json)
    assert len(calls)==1 and 'meaning_comparison' not in json.dumps(dto)


def test_initial_scoped_conflict_report_does_not_rewrite_or_retry_provider(natural_case, qdb):
    user, parent, service, calls = natural_case
    qdb.query("update public.emotions set memo=$2,memo_action='' where id=$1",
              [parent, "私は友人に頼まれた。"])

    async def reversed_reply(material):
        calls.append(material)
        return NaturalReply("あなたは友人に頼んだのですね。", "synthetic-4b", material.source_prefix_ref)

    service.natural_reply_source = reversed_reply
    dto = run(service.start(user, parent))
    snapshot = run(service.store.read(user, input_id=parent))
    event = next(e for e in snapshot['events'] if e['kind'] == 'OBSERVATION')
    assert event['payload']['artifact']['meaning_comparison']['verdict'] == 'CONFLICT'
    assert dto['current_observation']['text'] == "あなたは友人に頼んだのですね。"
    assert len(calls) == 1


def test_reader_bug_is_private_unassessed_and_not_source_error(natural_case, monkeypatch):
    user, parent, service, calls = natural_case
    import cocolon_meaning_experience_engine.natural_reply_meaning as meaning

    def broken(*args):
        raise RuntimeError('never expose internal prose from a reader error')

    monkeypatch.setattr(meaning, 'compare_reply_meaning', broken)
    dto = run(service.start(user, parent))
    snapshot = run(service.store.read(user, input_id=parent))
    event = next(e for e in snapshot['events'] if e['kind'] == 'OBSERVATION')
    report = event['payload']['artifact']['meaning_comparison']
    assert report['verdict'] == 'UNASSESSED' and report['reason_codes'] == ['CHECKER_ERROR']
    import hashlib
    assert report['material_sha256'] == hashlib.sha256(calls[0].material_json.encode('utf-8')).hexdigest()
    assert report['reply_sha256'] == hashlib.sha256(dto['current_observation']['text'].encode('utf-8')).hexdigest()
    assert not report['full_reply_semantic_coverage']
    assert 'never expose' not in json.dumps(snapshot)
    assert dto['body_state'] == 'FINAL' and len(calls) == 1


def test_source_integrity_failure_is_not_swallowed_as_reader_unknown(natural_case, monkeypatch):
    user, parent, service, calls = natural_case
    import cocolon_meaning_experience_engine.natural_reply_meaning as meaning

    def invalid(*args):
        raise ValueError('natural_meaning_material_invalid')

    monkeypatch.setattr(meaning, 'compare_reply_meaning', invalid)
    dto = run(service.start(user, parent))
    snapshot = run(service.store.read(user, input_id=parent))
    assert dto['state'] == 'RESPONSE_FAILED'
    assert not any(e['kind'] == 'OBSERVATION' for e in snapshot['events'])
    assert len(calls) == 1


def _natural_failure_diagnostics(service, owner, parent, dto, calls, phases, *, phase, case_id, tier, rounds, stopped, snapshot=None):
    """Body-free failure context; a successful helper performs no extra read."""
    diagnostic = dict(phase=phase, case_id=case_id, tier=tier, rounds=rounds, stopped=stopped,
        provider_calls=len(calls), natural_phases=phases,
        dto={key: dto.get(key) for key in ('state', 'body_state', 'failure_code', 'issued_count',
            'revision', 'answer_assessment', 'meaning_updated', 'processing_deadline_at')})
    try:
        if snapshot is None:
            snapshot = run(service.store.read(owner, input_id=parent))
        thread = snapshot.get('thread') or {}
        data = thread.get('data') or {}
        diagnostic['snapshot_now'] = snapshot.get('now')
        diagnostic['source_clock'] = dict(created_at=snapshot.get('original', {}).get('created_at'),
            natural_meaning_as_of=data.get('natural_meaning_as_of'), snapshot_now=snapshot.get('now'))
        diagnostic['saved_thread'] = dict(state=thread.get('state'), revision=thread.get('revision'),
            issued_count=thread.get('issued_count'), processing_deadline_at=thread.get('processing_deadline_at'),
            active_attempt=bool(thread.get('active_attempt_id')), active_operation=bool(thread.get('active_operation_id')),
            body_state=data.get('body_state'), failure_code=data.get('failure_code'),
            response_profile=data.get('response_profile'), response_stage=data.get('natural_response_stage'))
        diagnostic['event_phases'] = [dict(kind=event.get('kind'), round_index=event.get('round_index'),
            **{key: event.get('payload', {}).get(key) for key in ('stage', 'status', 'failure_code')
               if key in event.get('payload', {})}) for event in snapshot.get('events', [])]
    except Exception as exc:
        diagnostic['diagnostic_read_error'] = type(exc).__name__
    return diagnostic



def _observe_initial_natural_failures(service, monkeypatch, calls):
    """Observe a fictional fixture without changing acquisition or clock behavior."""
    phases = []
    process_natural, start = service._process_natural, service.start
    count = calls if callable(calls) else lambda: len(calls)

    async def observed_natural(user_id, snapshot):
        began = time.monotonic()
        phases.append(dict(phase='_process_natural', event='ENTER',
            created_at=snapshot['original']['created_at'], snapshot_now=snapshot['now'],
            natural_meaning_as_of=snapshot['thread']['data'].get('natural_meaning_as_of')))
        try:
            dto = await process_natural(user_id, snapshot)
        except asyncio.CancelledError:
            phases.append(dict(phase='_process_natural', event='CANCELLED',
                elapsed_seconds=time.monotonic()-began, exception_type='CancelledError', code=None))
            raise
        except Exception as exc:
            code = getattr(exc, 'code', None) or str(exc)
            if not isinstance(code, str) or not re.fullmatch(
                    r'(?:natural_|thread_|analysis_|emlis_|semantic_|source_|safe_state_|separate_safety_|meaning_)[a-z0-9_]{1,120}', code):
                code = None
            phases.append(dict(phase='_process_natural', event='EXCEPTION',
                elapsed_seconds=time.monotonic()-began, exception_type=type(exc).__name__, code=code))
            raise
        phases.append(dict(phase='_process_natural', event='RETURN', elapsed_seconds=time.monotonic()-began,
            state=dto.get('state'), failure_code=dto.get('failure_code')))
        return dto

    async def observed_start(user_id, input_id):
        owner, parent = user_id, input_id
        began, first_phase, before_calls = time.monotonic(), len(phases), count()
        dto = await start(owner, parent)
        if dto.get('state') == 'RESPONSE_FAILED':
            try:
                snapshot = await service.store.read(owner, input_id=parent)
                diagnostic = _natural_failure_diagnostics(service, owner, parent, dto,
                    [None] * count(), phases[first_phase:], phase='initial_start',
                    case_id='saved-natural-fixture', tier=snapshot.get('tier'), rounds=1,
                    stopped=False, snapshot=snapshot)
                diagnostic.update(elapsed_seconds=time.monotonic()-began,
                    provider_calls_this_start=count()-before_calls)
            except Exception as exc:
                diagnostic = dict(phase='initial_start', state=dto.get('state'),
                    failure_code=dto.get('failure_code'), diagnostic_read_error=type(exc).__name__)
            print('SAVED_NATURAL_INITIAL_FAILURE ' + json.dumps(diagnostic, ensure_ascii=False))
        return dto

    monkeypatch.setattr(service, '_process_natural', observed_natural)
    monkeypatch.setattr(service, 'start', observed_start)
    return phases


@pytest.fixture
def natural_case(qdb, monkeypatch):
    user, parent = str(uuid4()), str(uuid4())
    qdb.query("insert into auth.users values ($1)", [user])
    qdb.query("insert into public.profiles values ($1,'free')", [user])
    qdb.query("insert into public.emotions values ($1,$2,(now()-interval '5 seconds') at time zone 'UTC',$3,'',array['仕事'],array['平穏'],$4)",
        [parent, user, "会議の資料を読み直した。終わって少し安心した。",
         json.dumps([dict(type="平穏", strength="medium")], ensure_ascii=False)])
    monkeypatch.setattr(emlis_thread_store, "sb_post_rpc", qdb.rpc)
    calls = []

    async def source(material):
        snapshot = await service.store.read(user, input_id=parent)
        assert any(e["payload"].get("stage") == "NATURAL_REPLY_CALL_STARTED" for e in snapshot["events"])
        calls.append(material)
        return NaturalReply(BODY, "self-hosted-test-4b", material.source_prefix_ref)

    service = EmlisThreadService(runtime_profile=Q3_PROFILE, natural_reply_source=source)
    _observe_initial_natural_failures(service, monkeypatch, calls)
    return user, parent, service, calls


def test_saved_reply_reopens_without_provider_or_meaning_generation(natural_case):
    user, parent, service, calls = natural_case
    dto = run(service.start(user, parent))
    assert dto["state"] == "COMPLETED" and dto["body_state"] == "FINAL", dto
    assert dto["current_observation"]["text"] == BODY
    assert dto["pending_question"] is None and not dto["meaning_updated"]
    snapshot = run(service.store.read(user, input_id=parent))
    assert snapshot["thread"]["data"]["analysis_state"] == "NOT_GENERATED"
    assert snapshot["thread"]["current_meaning_event_id"] is None
    assert not any(e["kind"] == "MEANING_UPDATE" for e in snapshot["events"])
    restarted = EmlisThreadService(runtime_profile=Q3_PROFILE)
    for _ in range(2):
        read = run(restarted.get(user, parent))
        assert read["current_observation"] == dto["current_observation"]
        assert read["can_write"] is False
    assert len(calls) == 1
    public = json.dumps(dto, ensure_ascii=False)
    assert all(x not in public for x in ("source_prefix_ref", "material_json", "NATURAL_REPLY", "self-hosted-test-4b"))


def _piece_adapter(user, service, monkeypatch):
    import piece_v2_source_adapter as piece
    async def verified(_authorization):
        return user
    monkeypatch.setattr(piece, '_require_user_id', verified)
    return piece.PieceSavedSourceAdapter(store=service.store)


@pytest.mark.parametrize('tier,days', [('free', 1), ('plus', 200), ('premium', 4000)])
def test_piece_uses_original_after_natural_final_with_saved_context(natural_case, qdb, monkeypatch, tier, days):
    from piece_v2_source_adapter import project_saved_original_source
    user, parent, service, calls = natural_case
    qdb.query('update public.profiles set subscription_tier=$2 where id=$1', [user, tier])
    past = str(uuid4())
    qdb.query("insert into public.emotions values ($1,$2,(now()-($3||' days')::interval) at time zone 'UTC',$4,'',array['仕事'],array['平穏'],$5)",
        [past, user, str(days), '会議の資料を読み直した。', json.dumps([dict(type='平穏', strength='medium')])])
    dto = run(service.start(user, parent))
    adapter = _piece_adapter(user, service, monkeypatch)
    handoff = run(adapter.resolve_original_handoff('Bearer synthetic', parent))
    ref = run(adapter.resolve_original_source_ref('Bearer synthetic', parent))
    assert ref['emlis_observation_result_identity'] == dto['current_observation']['event_id']
    assert ref['emlis_observation_stage'] == 'normal_observation'
    assert len(ref) == 7 and ref['supplemental_answer_identity'] is None
    source = project_saved_original_source(handoff.original, source_stage='normal_observation')
    assert BODY not in repr(source) and BODY not in handoff._lineage_json.decode()
    assert source.original_text == handoff.original.original_payload()['memo']
    saved = run(service.store.read(user, input_id=parent))
    assert saved['thread']['current_meaning_event_id'] is None
    assert saved['thread']['data']['analysis_state'] == 'NOT_GENERATED'
    guards = saved['thread']['data']['context_guards']
    assert bool(guards) == (tier != 'free')
    if guards:
        # A new unrelated/coinciding record never substitutes the saved cohort.
        qdb.query("insert into public.emotions values ($1,$2,(now()-interval '1 hour') at time zone 'UTC',$3,'',array['仕事'],array['平穏'],$4)",
            [str(uuid4()), user, '会議の資料を読み直した。', json.dumps([dict(type='平穏', strength='medium')])])
        assert run(adapter.resolve_original_handoff('Bearer synthetic', parent)) == handoff
        qdb.query("update public.emotions set memo='編集済み' where id=$1", [past])
        with pytest.raises(ValueError, match='PIECE_SOURCE_NOT_ELIGIBLE'):
            run(adapter.resolve_original_source_ref('Bearer synthetic', parent))
    assert len(calls) == 1


@pytest.mark.parametrize('corruption', ['receipt', 'start', 'finish', 'artifact', 'context', 'active', 'meaning'])
def test_piece_rejects_incomplete_or_mismatched_natural_control(natural_case, monkeypatch, corruption):
    import copy
    user, parent, service, _ = natural_case
    run(service.start(user, parent))
    value = run(service.store.read(user, input_id=parent))
    value = copy.deepcopy(value)
    t = value['thread']
    obs = next(e for e in value['events'] if e['kind'] == 'OBSERVATION')
    if corruption == 'receipt':
        next(e for e in value['events'] if e['payload'].get('stage') == 'NATURAL_REPLY_RECEIVED')['payload']['reply']['text'] = 'different'
    elif corruption == 'start':
        value['events'] = [e for e in value['events'] if e['payload'].get('stage') != 'NATURAL_REPLY_CALL_STARTED']
    elif corruption == 'finish':
        value['events'][-1]['attempt_id'] = str(uuid4())
    elif corruption == 'artifact':
        obs['payload']['artifact']['schema_version'] = 'invalid'
    elif corruption == 'context':
        obs['payload']['context_ref'] = 'different-context'
    elif corruption == 'active':
        t['active_attempt_id'] = str(uuid4())
    else:
        t['current_meaning_event_id'] = str(uuid4())
    class ReadOnly:
        async def read(self, *_args, **_kwargs): return copy.deepcopy(value)
        async def related_context(self, *_args, **_kwargs): return {'history': [], 'feedback': []}
    adapter = _piece_adapter(user, service, monkeypatch)
    adapter._store = ReadOnly()
    with pytest.raises(ValueError, match='PIECE_SOURCE_NOT_ELIGIBLE'):
        run(adapter.resolve_original_handoff('Bearer synthetic', parent))


def test_parallel_initial_starts_admit_one_provider_call(natural_case):
    user, parent, service, calls = natural_case

    async def both():
        await asyncio.gather(service.start(user, parent), service.start(user, parent))
        return await service.get(user, parent)
    result = run(both())
    assert result["current_observation"]["text"] == BODY
    assert len(calls) == 1
    snapshot = run(service.store.read(user, input_id=parent))
    assert sum(e["kind"] == "OBSERVATION" for e in snapshot["events"]) == 1


def test_unknown_receipt_ack_reads_and_saves_same_reply_without_new_call(natural_case, monkeypatch, qdb):
    user, parent, service, calls = natural_case
    lost = False

    async def rpc(name, payload, **kwargs):
        nonlocal lost
        result = await qdb.rpc(name, payload, **kwargs)
        if not lost and any(e["payload"].get("stage") == "NATURAL_REPLY_RECEIVED" for e in payload.get("p_events", [])):
            lost = True
            raise httpx.ReadTimeout("must not enter public output")
        return result
    monkeypatch.setattr(emlis_thread_store, "sb_post_rpc", rpc)
    result = run(service.start(user, parent))
    assert result["current_observation"]["text"] == BODY and len(calls) == 1
    assert run(service.get(user, parent))["current_observation"] == result["current_observation"]


def test_rolled_back_body_save_reuses_durable_receipt_on_explicit_retry(natural_case, monkeypatch, qdb):
    user, parent, service, calls = natural_case
    failed = False

    async def rpc(name, payload, **kwargs):
        nonlocal failed
        if not failed and any(e["kind"] == "OBSERVATION" for e in payload.get("p_events", [])):
            failed = True
            return httpx.Response(503, json={"code": "57P03"})
        return await qdb.rpc(name, payload, **kwargs)
    monkeypatch.setattr(emlis_thread_store, "sb_post_rpc", rpc)
    failed_dto = run(service.start(user, parent))
    assert failed_dto["can_retry"] and failed_dto["current_observation"] is None
    result = run(service.action(user, failed_dto["thread_id"], action="retry_response",
        expected_revision=failed_dto["revision"], idempotency_key="save-received-reply",
        operation_id=failed_dto["operation_id"]))
    assert result["current_observation"]["text"] == BODY
    assert len(calls) == 1
    # The valid receipt belongs to the first attempt; Piece binds the retried
    # observation to its own successful finish without reacquiring the model.
    adapter = _piece_adapter(user, service, monkeypatch)
    ref = run(adapter.resolve_original_source_ref('Bearer synthetic', parent))
    assert ref['emlis_observation_result_identity'] == result['current_observation']['event_id']


def test_provider_failure_keeps_input_and_does_not_offer_regeneration(natural_case):
    user, parent, service, calls = natural_case

    async def fail(material):
        calls.append(material)
        raise httpx.ReadTimeout("private provider error")
    service.natural_reply_source = fail
    result = run(service.start(user, parent))
    assert result["state"] == "RESPONSE_FAILED" and not result["can_retry"]
    assert result["current_observation"] is None
    assert run(service.store.read(user, input_id=parent))["original"]["id"] == parent
    assert run(service.start(user, parent))["state"] == "RESPONSE_FAILED"
    assert len(calls) == 1
    assert "private provider error" not in json.dumps(result)


def test_cancelled_request_is_not_restarted_by_get_or_start(natural_case):
    user, parent, service, calls = natural_case

    async def scenario():
        started = asyncio.Event()

        async def blocked(material):
            calls.append(material)
            started.set()
            await asyncio.Future()
        service.natural_reply_source = blocked
        task = asyncio.create_task(service.start(user, parent))
        await started.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        dto = await service.get(user, parent)
        assert dto["state"] == "RESPONSE_FAILED" and not dto["can_retry"]
        await service.start(user, parent)
    run(scenario())
    assert len(calls) == 1


@pytest.mark.parametrize("field,value", [
    ("memo", "訂正した記録"),
    ("category", ["仕事", "学習"]),
    ("emotion_details", json.dumps([dict(type="平穏", strength="strong")])),
])
def test_source_edit_before_save_rejects_old_reply(natural_case, qdb, field, value):
    user, parent, service, calls = natural_case
    original = service.natural_reply_source

    async def edited(material):
        result = await original(material)
        qdb.query(f"update public.emotions set {field}=$2 where id=$1", [parent, value])
        return result
    service.natural_reply_source = edited
    with pytest.raises(ThreadStoreError):
        run(service.start(user, parent))
    assert qdb.query("select count(*) as n from public.emlis_thread_events where kind='OBSERVATION' and thread_id in (select id from public.emlis_input_threads where original_emotion_id=$1)", [parent])["rows"][0]["n"] == 0
    assert len(calls) == 1


@pytest.mark.parametrize("tier", ["free", "plus", "premium"])
def test_complete_current_and_owned_history_input_fields_reach_recipient_source(natural_case, qdb, tier):
    user, parent, service, calls = natural_case
    categories = ["人生", "価値観", "学習", "健康", "恋愛", "人間関係", "趣味", "仕事", "生活"]
    details = [dict(type="喜び", strength="weak"), dict(type="不安", strength="strong"),
               dict(type="平穏", strength="medium"), dict(type="悲しみ", strength="strong"),
               dict(type="怒り", strength="weak")]
    memo = "会議に向けて、不安もあるけれど少し楽しみだ。"
    action = "会議の資料を読み直した。"
    qdb.query("update public.profiles set subscription_tier=$2 where id=$1", [user, tier])
    qdb.query("update public.emotions set memo=$2,memo_action=$3,category=$4,emotions=$5,emotion_details=$6 where id=$1",
        [parent, memo, action, categories, [d["type"] for d in details], json.dumps(details, ensure_ascii=False)])
    past = str(uuid4())
    past_categories = ["学習", "仕事"]
    past_details = [dict(type="不安", strength="weak"), dict(type="平穏", strength="strong")]
    qdb.query("insert into public.emotions values ($1,$2,(now()-interval '1 day') at time zone 'UTC',$3,$4,$5,$6,$7)",
        [past, user, "会議の前には迷っていた。", action, past_categories,
         [d["type"] for d in past_details], json.dumps(past_details, ensure_ascii=False)])

    saved = run(service.start(user, parent))
    material = json.loads(calls[0].material_json)
    current = material["current"]
    assert current["memo"] == memo and current["memo_action"] == action
    assert current["category"] == categories
    assert current["emotion_details"] == details
    assert current["emotions"] == [d["type"] for d in details]
    history = material["past_user_records"]
    assert [record["input_id"] for record in history] == ([] if tier == "free" else [past])
    if history:
        assert history[0]["original"]["category"] == past_categories
        assert history[0]["original"]["emotion_details"] == past_details
        assert history[0]["original"]["memo_action"] == action
    assert run(service.get(user, parent))["current_observation"] == saved["current_observation"]
    assert len(calls) == 1


def test_self_insight_keeps_its_distinct_selection_and_fixed_storage_strength(natural_case, qdb):
    user, parent, service, calls = natural_case
    details = [dict(type="自己理解", strength="medium")]
    qdb.query("update public.emotions set emotions=$2,emotion_details=$3 where id=$1",
        [parent, ["自己理解"], json.dumps(details, ensure_ascii=False)])
    run(service.start(user, parent))
    current = json.loads(calls[0].material_json)["current"]
    assert current["emotions"] == ["自己理解"] and current["emotion_details"] == details
    assert current["category"] == ["仕事"]


def test_another_owner_cannot_read_reply(natural_case):
    user, parent, service, _ = natural_case
    run(service.start(user, parent))
    with pytest.raises(ThreadStoreError, match="thread_unavailable"):
        run(service.get(str(uuid4()), parent))


@pytest.mark.parametrize("memo,reason", [
    ("自分なんていないほうがいい。", "safe_state_answer_owner_required"),
    ("今すぐ自分を傷つけたい。", "separate_safety_owner_required"),
])
def test_existing_safety_owner_prevents_ordinary_provider(natural_case, qdb, memo, reason):
    user, parent, service, calls = natural_case
    qdb.query("update public.emotions set memo=$2 where id=$1", [parent, memo])
    dto = run(service.start(user, parent))
    assert dto["failure_code"] == reason, dto
    assert not calls and dto["current_observation"] is None


def test_provider_configuration_loss_reads_saved_reply_but_cannot_write(natural_case, monkeypatch):
    user, parent, service, _ = natural_case
    done = run(service.start(user, parent))
    from emlis_thread_factory import application_thread_service
    monkeypatch.setenv("EMLIS_AI_RESPONSE_PROFILE", "natural_reply.v1")
    monkeypatch.delenv("EMLIS_NATURAL_REPLY_ENDPOINT", raising=False)
    reader = application_thread_service()
    dto = run(reader.get(user, parent))
    assert dto["current_observation"] == done["current_observation"] and dto["can_write"] is False


def test_emlis_observation_provider_can_be_selected_without_changing_other_consumers(monkeypatch):
    from emlis_thread_config import natural_reply_provider_settings
    from emlis_thread_factory import application_thread_service
    from piece_model_source import CMEE_SELECTOR, application_piece_model_source

    monkeypatch.setenv("EMLIS_AI_RESPONSE_PROFILE", "natural_reply.v1")
    monkeypatch.setenv("EMLIS_NATURAL_REPLY_ENDPOINT", "https://shared.invalid/chat/completions")
    monkeypatch.setenv("EMLIS_NATURAL_REPLY_MODEL", "shared-4b")
    monkeypatch.setenv("EMLIS_NATURAL_REPLY_API_KEY", "shared-test-key")
    monkeypatch.setenv("PIECE_MODEL_SOURCE", CMEE_SELECTOR)
    monkeypatch.delenv("COCOLON_EMLIS_CONTEXT_UPDATE", raising=False)
    monkeypatch.delenv("EMLIS_OBSERVATION_MODEL_ENDPOINT", raising=False)
    monkeypatch.delenv("EMLIS_OBSERVATION_MODEL", raising=False)
    monkeypatch.delenv("EMLIS_OBSERVATION_MODEL_API_KEY", raising=False)

    shared = natural_reply_provider_settings()
    piece_source = application_piece_model_source()
    service = application_thread_service()
    assert service.natural_reply_source.model == "shared-4b"
    assert not service.natural_context_update_enabled

    monkeypatch.setenv("EMLIS_OBSERVATION_MODEL", "observation-4b")
    assert application_thread_service().natural_reply_source is None

    monkeypatch.setenv("EMLIS_OBSERVATION_MODEL_ENDPOINT", "https://observation.invalid/chat/completions")
    monkeypatch.setenv("EMLIS_OBSERVATION_MODEL_API_KEY", "observation-test-key")
    assert application_thread_service().natural_reply_source.model == "observation-4b"
    assert natural_reply_provider_settings() == shared
    assert application_piece_model_source() is piece_source
    monkeypatch.setenv("COCOLON_EMLIS_CONTEXT_UPDATE", "true")
    assert application_thread_service().natural_context_update_enabled


@pytest.mark.parametrize("tier", ["free", "plus", "premium"])
def test_existing_history_boundary_passes_user_originals_only(natural_case, qdb, tier):
    user, parent, service, calls = natural_case
    qdb.query("update public.profiles set subscription_tier=$2 where id=$1", [user, tier])
    past = str(uuid4())
    qdb.query("insert into public.emotions values ($1,$2,(now()-interval '1 day') at time zone 'UTC',$3,'',array['仕事'],array['不安'],$4)",
        [past, user, "昨日の会議では資料を忘れて困った。", json.dumps([dict(type="不安", strength="medium")])])
    qdb.query("insert into public.emotions values ($1,$2,(now()-interval '2 days') at time zone 'UTC',$3,'',array['仕事'],array['不安'],$4)",
        [str(uuid4()), user, "自分には価値がない。", json.dumps([dict(type="不安", strength="medium")])])
    dto = run(service.start(user, parent))
    assert dto["current_observation"]["text"] == BODY
    material = json.loads(calls[0].material_json)
    history = material["past_user_records"]
    assert len(history) == (0 if tier == "free" else 1)
    assert "自分には価値がない" not in calls[0].material_json
    if history:
        assert history[0]["original"]["memo"] == "昨日の会議では資料を忘れて困った。"
        assert "thread" not in history[0] and "artifact" not in history[0]


def insert_past(qdb, user, memo, days=1):
    identity = str(uuid4())
    qdb.query("insert into public.emotions values ($1,$2,(now()-($4::int*interval '1 day')) at time zone 'UTC',$3,'',array['仕事'],array['平穏'],$5)",
        [identity,user,memo,days,json.dumps([dict(type='平穏',strength='medium')])])
    return identity


@pytest.mark.parametrize('tier,days,included',[('free',30,False),('plus',30,True),('plus',400,False),('premium',4000,True)])
def test_related_search_precedes_context_limit_and_respects_plan_access(natural_case,qdb,tier,days,included):
    user,parent,service,calls=natural_case
    qdb.query('update public.profiles set subscription_tier=$2 where id=$1',[user,tier])
    older=insert_past(qdb,user,'会議の資料を読み直した。',days)
    for i in range(1,8): insert_past(qdb,user,'バナナ。',i)
    result=run(service.start(user,parent))
    assert result['current_observation']['text']==BODY
    records=json.loads(calls[0].material_json)['past_user_records']
    assert [r['input_id'] for r in records]==([older] if included else [])
    assert len(calls)==1


def test_saved_reply_keeps_selected_cohort_when_another_related_record_is_added(natural_case,qdb):
    user,parent,service,calls=natural_case
    qdb.query("update public.profiles set subscription_tier='plus' where id=$1",[user])
    insert_past(qdb,user,'会議の資料を読み直した。',30)
    saved=run(service.start(user,parent))
    for i in range(1,6): insert_past(qdb,user,'会議の資料を読み直した。',i)
    assert run(service.get(user,parent))['current_observation']==saved['current_observation']
    assert len(calls)==1


@pytest.mark.parametrize('mutation',['edit','delete','tier','answer_revision'])
def test_selected_source_change_during_natural_generation_rejects_save(natural_case,qdb,mutation):
    user,parent,service,calls=natural_case
    qdb.query("update public.profiles set subscription_tier='plus' where id=$1",[user])
    past=insert_past(qdb,user,'会議の資料を読み直した。',10)
    if mutation=='answer_revision':
        run(EmlisThreadService(runtime_profile=Q3_PROFILE).start(user,past))
    original=service.natural_reply_source
    async def changed(material):
        result=await original(material)
        if mutation=='edit': qdb.query("update public.emotions set memo='changed' where id=$1",[past])
        elif mutation=='delete': qdb.query('delete from public.emotions where id=$1',[past])
        elif mutation=='tier': qdb.query("update public.profiles set subscription_tier='free' where id=$1",[user])
        else: qdb.query('update public.emlis_input_threads set revision=revision+1 where original_emotion_id=$1',[past])
        return result
    service.natural_reply_source=changed
    with pytest.raises(ThreadStoreError): run(service.start(user,parent))
    assert len(calls)==1
    dto=run(service.get(user,parent))
    assert dto['current_observation'] is None
    assert BODY not in json.dumps(dto,ensure_ascii=False)


def test_natural_configured_reader_preserves_legacy_paid_thread_and_context_rpc(natural_case,qdb,monkeypatch):
    from test_emlis_q2_application import answer
    user,parent,_,_=natural_case
    qdb.query("update public.profiles set subscription_tier='premium' where id=$1",[user])
    qdb.query('update public.emotions set memo=$2 where id=$1',[parent,'褒められたのに、嬉しくなかった。'])
    old=EmlisThreadService(runtime_profile=Q3_PROFILE)
    saved=run(old.start(user,parent))
    saved=run(answer(old,user,saved,'その時は重かった。'))
    calls=[]
    async def rpc(name,payload,**kw):
        calls.append(name)
        return await qdb.rpc(name,payload,**kw)
    monkeypatch.setattr(emlis_thread_store,'sb_post_rpc',rpc)
    async def no_provider(_): raise AssertionError('GET generated a reply')
    reader=EmlisThreadService(runtime_profile=Q3_PROFILE,natural_reply_source=no_provider)
    assert run(reader.get(user,parent))==saved
    assert 'emlis_thread_context' in calls
    assert 'emlis_thread_related_context' not in calls


def completed_answered_past(qdb,user):
    from test_emlis_q2_application import answer
    from test_emlis_q3_application import cont
    memo='褒められたのに、嬉しくなかった。誘われたのに、悲しかった。頼まれたのに、寂しかった。'
    past=insert_past(qdb,user,memo)
    old=EmlisThreadService(runtime_profile=Q3_PROFILE)
    dto=run(old.start(user,past))
    texts=('その時は重かった。','その時は怖かった。','その時は苦しかった。')
    for i,text in enumerate(texts):
        dto=run(answer(old,user,dto,text,'past-answer-'+str(i)))
        if i<2: dto=run(cont(old,user,dto,'past-continue-'+str(i)))
    assert dto['state']=='COMPLETED'
    return past,memo,texts,dto


def test_history_preserves_three_user_answers_and_correction_as_separate_sources(natural_case,qdb):
    from datetime import timedelta
    from astor_material_snapshots import _analysis_saved_member
    from cocolon_meaning_experience_engine.cores.analysis.source_adapter import _time
    from emlis_thread_service import _request
    from cocolon_meaning_experience_engine.natural_reply import prepare_natural_reply
    user,parent,service,calls=natural_case
    qdb.query("update public.profiles set subscription_tier='premium' where id=$1",[user])
    past,memo,texts,old=completed_answered_past(qdb,user)
    saved_snapshot=run(service.store.read(user,input_id=past))
    stamp=_time(saved_snapshot['original']['created_at'],saved_utc=True)
    member,_=_analysis_saved_member(saved_snapshot,owner=user,input_id=past,tier='premium',
        start=stamp-timedelta(seconds=1),end=stamp+timedelta(seconds=1))
    assert [a.text for a in member.supplements]==list(texts)
    qdb.query('update public.emotions set memo=$2 where id=$1',[parent,memo])
    qdb.query("insert into public.emlis_frame_feedback(user_id,source_emotion_id,frame_key,frame_ref,status,correction_text) values ($1,$2,'synthetic-frame','synthetic-ref','REVISED',$3)",
        [user,past,'期待ではなく、結果だけで判断されたことが気になった。'])
    result=run(service.start(user,parent))
    assert result['current_observation']['text']==BODY
    material=json.loads(calls[0].material_json)
    record=next(r for r in material['past_user_records'] if r['input_id']==past)
    assert record['original']['memo']==memo
    assert [a['text'] for a in record['answers']]==list(texts)
    assert [a['round_index'] for a in record['answers']]==[1,2,3]
    assert all(a['source_role']=='SUPPLEMENTAL_ANSWER' and a['ai_question_context'] for a in record['answers'])
    assert material['user_frame_feedback'][0]['input_id']==past
    assert material['user_frame_feedback'][0]['source_role']=='USER_FRAME_FEEDBACK'
    assert old['current_observation']['text'] not in calls[0].material_json
    # The same admitted answers also work when they are the current record.
    request=_request(run(service.store.read(user,input_id=past)))
    prepared,safety=prepare_natural_reply(request)
    assert safety.normal_observation_allowed
    assert [a['text'] for a in json.loads(prepared.material_json)['current_answers']]==list(texts)


def test_unsafe_supplement_excludes_whole_past_record_and_blocks_current_material(natural_case,qdb):
    from dataclasses import replace
    from emlis_thread_service import _request
    from cocolon_meaning_experience_engine.natural_reply import prepare_natural_reply
    user,parent,service,calls=natural_case
    qdb.query("update public.profiles set subscription_tier='premium' where id=$1",[user])
    past,memo,_,_=completed_answered_past(qdb,user)
    request=_request(run(service.store.read(user,input_id=past)))
    first=replace(request.emlis_thread.answers[0],answer_text_private='自分には価値がない。')
    request=replace(request,emlis_thread=replace(request.emlis_thread,answers=(first,*request.emlis_thread.answers[1:])))
    _,safety=prepare_natural_reply(request)
    assert not safety.normal_observation_allowed
    qdb.query('update public.emotions set memo=$2 where id=$1',[parent,memo])
    original=service.natural_reply_source
    async def inspect_material(material):
        value=json.loads(material.material_json)
        assert value['past_user_records']==[]
        assert value['user_frame_feedback']==[]
        return await original(material)
    service.natural_reply_source=inspect_material
    qdb.query("update public.emlis_thread_events set payload=jsonb_set(payload,'{source,answer_text_private}',to_jsonb($2::text)) where thread_id=(select id from public.emlis_input_threads where original_emotion_id=$1) and kind='ANSWER' and round_index=1",
        [past,'自分には価値がない。'])
    # The fixture keeps the stored thread binding but updates its raw source;
    # admission and Safety still inspect the complete answer, not AI prose.
    assert run(service.start(user,parent))['current_observation']['text']==BODY
    assert len(calls)==1


def test_related_context_rpc_is_service_only_and_rejects_another_owner(natural_case,qdb):
    user,parent,_,_=natural_case
    for role in ['anon','authenticated']:
        assert qdb.query('select public.emlis_thread_related_context($1,$2)',[user,parent],role)['code']=='42501'
    other=str(uuid4())
    assert qdb.query('select public.emlis_thread_related_context($1,$2)',[other,parent],'service_role')['code']=='P0002'


def test_edited_past_thread_is_excluded_without_attaching_stale_answers(natural_case,qdb):
    user,parent,service,calls=natural_case
    qdb.query("update public.profiles set subscription_tier='premium' where id=$1",[user])
    past,memo,_,_=completed_answered_past(qdb,user)
    qdb.query('update public.emotions set memo=$2 where id=$1',[past,'会議の資料を読み直した。'])
    assert run(service.start(user,parent))['current_observation']['text']==BODY
    assert json.loads(calls[0].material_json)['past_user_records']==[]


def test_pause_during_provider_keeps_input_and_does_not_save_or_repeat_reply(natural_case, monkeypatch):
    user, parent, service, calls = natural_case
    service.enforce_application_policy = True
    enabled = True
    monkeypatch.setattr("emlis_thread_service.writes_enabled", lambda: enabled)
    original = service.natural_reply_source

    async def pause(material):
        nonlocal enabled
        result = await original(material)
        enabled = False
        return result
    service.natural_reply_source = pause
    dto = run(service.start(user, parent))
    assert not dto["can_write"] and dto["current_observation"] is None
    assert dto["state"] == "RESPONSE_FAILED" and not dto["can_retry"]
    enabled = True
    assert run(service.start(user, parent))["current_observation"] is None
    assert len(calls) == 1


def test_background_admission_survives_submit_caller_and_deduplicates():
    from emlis_thread_factory import _initial_tasks, schedule_initial_reply

    async def scenario():
        release = asyncio.Event()
        calls = []

        class Owner:
            async def start(self, user, parent):
                calls.append((user, parent))
                await release.wait()
        owner = Owner()
        schedule_initial_reply(owner, "user", "parent")
        schedule_initial_reply(owner, "user", "parent")
        await asyncio.sleep(0)
        assert calls == [("user", "parent")] and len(_initial_tasks) == 1
        release.set()
        await asyncio.gather(*list(_initial_tasks.values()))
        await asyncio.sleep(0)
        assert not _initial_tasks
    run(scenario())


def test_normal_reply_entry_returns_pending_before_model_and_meta_survives_sanitizer(natural_case, monkeypatch):
    from emlis_ai_reply_service import render_emlis_ai_reply
    from emlis_ai_public_feedback_meta import build_public_emlis_input_feedback_meta
    from emlis_thread_factory import _initial_tasks
    user, parent, service, calls = natural_case
    monkeypatch.setenv("COCOLON_ENV", "development")
    monkeypatch.setenv("COCOLON_EMLIS_THREAD_DEVELOPMENT", "true")
    monkeypatch.setattr("emlis_thread_factory.application_thread_service", lambda: service)

    async def scenario():
        reply = await render_emlis_ai_reply(user_id=user, subscription_tier="free", current_input={"id": parent})
        assert not calls and reply.comment_text == ""
        public = build_public_emlis_input_feedback_meta(reply.meta, comment_text_present=False, subscription_tier="free")
        assert "thread_reply_pending" in public["rejection_reasons"]
        await asyncio.gather(*list(_initial_tasks.values()))
        assert (await service.get(user, parent))["current_observation"]["text"] == BODY
    run(scenario())
    assert len(calls) == 1


def test_self_absence_denial_does_not_match_its_explicit_negation_or_location():
    from emlis_ai_safety_triage import classify_emlis_safety_triage_text
    assert classify_emlis_safety_triage_text("自分なんていない方が良い。").safe_state_answer_allowed
    assert classify_emlis_safety_triage_text("自分なんていないほうがいいとは思わない。").normal_observation_allowed
    assert classify_emlis_safety_triage_text("机の前に自分がいないほうが作業を進めやすい。").normal_observation_allowed


def test_unconnected_frame_correction_is_not_silently_omitted(natural_case):
    from emlis_thread_service import _request
    from cocolon_meaning_experience_engine.emlis_thread_history import FrameFeedbackSourceV1
    from cocolon_meaning_experience_engine.natural_reply import prepare_natural_reply
    user, parent, service, calls = natural_case
    run(service.start(user, parent))
    snapshot = run(service.store.read(user, input_id=parent))
    request = _request(snapshot)
    feedback = FrameFeedbackSourceV1("frame", "ref", "past", "REVISED", "本人の訂正", 1, snapshot["now"])
    request = replace(request, emlis_thread=replace(request.emlis_thread,
        capability_snapshot="Q3_PREMIUM", frame_feedback_sources=(feedback,)))
    with pytest.raises(NaturalReplyError, match="natural_reply_frame_feedback_not_connected"):
        prepare_natural_reply(request)
    assert len(calls) == 1


@pytest.mark.parametrize("change", [
    {"finish_reason": "length"}, {"model": "unexpected-model"},
    {"text": "もう一度教えてください？"},
    {"text": "今はどんな気持ちでしょうか。"},
    {"text": "今も同じ気持ちですか。"},
    {"text": "まだ待っていますか\n気になっています。"},
    {"text": "今はどんな気持ちでしょうか"},
    {"text": "今も同じ気持ちですか  。"},
    {"text": "「今も同じ気持ちですか。"},
    {"text": "「お知らせ」今はどんな気持ちでしょうか。"},
])
def test_http_provider_rejects_partial_wrong_model_or_question_without_retry(change):
    calls = []

    def transport(request):
        calls.append(request)
        return httpx.Response(200, json={"model": change.get("model", "chosen-4b"), "choices": [{
            "finish_reason": change.get("finish_reason", "stop"),
            "message": {"role": "assistant", "content": change.get("text", BODY)}}]})
    source = SelfHostedNaturalReplySource(endpoint="https://model.invalid/v1/chat/completions",
        model="chosen-4b", api_key="synthetic-only", transport=httpx.MockTransport(transport))
    with pytest.raises(NaturalReplyError):
        run(source(NaturalReplyInput("source", '{"current":{"memo":"合成入力"}}')))
    assert len(calls) == 1


def test_http_provider_failure_log_uses_fixed_fields(caplog):
    def transport(request):
        return httpx.Response(200, json={"model": "chosen-4b", "choices": [{
            "finish_reason": "PRIVATE_FINISH", "message": {"content": "PRIVATE_REPLY"}}]})

    source = SelfHostedNaturalReplySource(endpoint="https://model.invalid/v1/chat/completions",
        model="chosen-4b", api_key="PRIVATE_KEY", transport=httpx.MockTransport(transport))
    with pytest.raises(NaturalReplyError, match="natural_reply_provider_contract"):
        run(source(NaturalReplyInput("source", '{"current":{"memo":"PRIVATE_INPUT"}}')))
    assert "emlis_reply_acquisition_failed stage=generation_finish http_status=200" in caplog.text
    assert "PRIVATE_" not in caplog.text
    assert "model.invalid" not in caplog.text


@pytest.mark.parametrize("body, reason", [
    ("  \n", "empty_reply"),
    ("PRIVATE_REPLY" * 1300, "reply_length"),
    ("<think>PRIVATE_REPLY</think>", "internal_format"),
    ("```PRIVATE_REPLY```", "internal_format"),
    ("PRIVATE_REPLY？", "question_marker"),
    ("PRIVATE_REPLY?", "question_marker"),
    ("PRIVATE_REPLY どのようなお気持ちでしたか。", "question_ending"),
    ("PRIVATE_REPLY\x00", "control_character"),
])
def test_http_provider_reply_validation_logs_only_a_fixed_reason(caplog, body, reason):
    calls = []

    def transport(request):
        calls.append(request)
        return httpx.Response(200, json={"model": "chosen-4b", "choices": [{
            "finish_reason": "stop", "message": {"role": "assistant", "content": body}}]})

    source = SelfHostedNaturalReplySource(endpoint="https://model.invalid/v1/chat/completions",
        model="chosen-4b", api_key="PRIVATE_KEY", transport=httpx.MockTransport(transport))
    with pytest.raises(NaturalReplyError, match="^natural_reply_invalid$"):
        run(source(NaturalReplyInput("PRIVATE_SOURCE", '{"current":{"memo":"PRIVATE_INPUT"}}')))
    assert len(calls) == 1
    assert f"emlis_reply_acquisition_failed stage=reply_validation http_status=200 reason={reason}" in caplog.text
    assert "PRIVATE_" not in caplog.text
    assert "model.invalid" not in caplog.text


@pytest.mark.parametrize("text", [
    "『明日でしょうか。』という言葉が気になったのですね。",
    "「いま話せますか。」と声をかけたのですね。",
    "「『明日ですか。』と聞いた」と書いてくださったのですね。",
    "今は言葉にできないのですね。",
    "その理由は分からないのですね。",
    "あたたかな気持ちを感じたのですね。",
])
def test_http_provider_keeps_reported_questions_and_declarative_replies(text):
    calls = []

    def transport(request):
        calls.append(request)
        return httpx.Response(200, json={"model": "chosen-4b", "choices": [{
            "finish_reason": "stop", "message": {"role": "assistant", "content": text}}]})

    source = SelfHostedNaturalReplySource(endpoint="https://model.invalid/v1/chat/completions",
        model="chosen-4b", api_key="synthetic-only", transport=httpx.MockTransport(transport))
    reply = run(source(NaturalReplyInput("source", '{"current":{"memo":"合成入力"}}')))
    assert reply.text == text and len(calls) == 1


def test_http_provider_sends_only_admitted_material_and_preserves_reply():
    def transport(request):
        payload = json.loads(request.content)
        instructions = payload["messages"][0]["content"]
        for contract_text in ("memoは「考えたこと・感じたこと」", "memo_actionは「出来事・行動」",
                              "categoryは本人が複数選べる記録の文脈", "weakは弱、mediumは中、strongは強",
                              "自己理解はこの五つの感情とは別の本人選択", "created_atは記録した時点"):
            assert contract_text in instructions
        assert payload["messages"][1]["content"] == '{"current":{"memo":"合成入力"}}'
        assert payload["chat_template_kwargs"] == {"enable_thinking": False}
        assert request.headers["Authorization"] == "Bearer synthetic-only"
        return httpx.Response(200, json={"model": "chosen-4b", "choices": [{"finish_reason": "stop",
            "message": {"role": "assistant", "content": BODY}}]})
    source = SelfHostedNaturalReplySource(endpoint="https://model.invalid/v1/chat/completions",
        model="chosen-4b", api_key="synthetic-only", transport=httpx.MockTransport(transport))
    reply = run(source(NaturalReplyInput("source", '{"current":{"memo":"合成入力"}}')))
    assert reply.text == BODY and reply.source_prefix_ref == "source"


@pytest.mark.parametrize("thought,action,focus,feeling", [
    ("見本帳にあった青い縞が好きでした。", "本を棚へ戻しました。",
     {"好きだと書いた箇所": "見本帳にあった青い縞", "本人が書いた好みの時制": "過去"}, "好き"),
    ("見本帳にあった青い縞が大好きです。", "本を棚へ戻しました。",
     {"好きだと書いた箇所": "見本帳にあった青い縞", "本人が書いた好みの時制": "現在"}, "大好き"),
    ("友人が「寂しかった」と話していました。私はほっとしました。", "楽譜を返しました。", {}, "ほっとしました"),
    ("楽譜を今日中に返せたので、私はほっとしました。", "受付を早く閉めると聞きました。", {"本人が明記した理由": "楽譜を今日中に返せた"}, "ほっとしました"),
    ("私は帰り道に思い返すと寂しかったです。", "花に水をやりました。", {"本人が書いた場面": "帰り道に思い返す"}, "寂しかったです"),
])
def test_9b_initial_follow_uses_bound_focus_and_persists_literal(natural_case, qdb, monkeypatch,
                                                              thought, action, focus, feeling):
    from cocolon_meaning_experience_engine.natural_reply import (
        INITIAL_OBSERVATION_FOLLOW_CONTEXT_VERSION, QWEN_9B_NATURAL_ALIAS)

    user, parent, _, _ = natural_case
    qdb.query("update public.emotions set memo=$2, memo_action=$3 where id=$1",
              [parent, thought, action])
    sent = []
    literal = thought.split('。')[-2] + '。'
    follow = "お話をここに残してくださったことを、Emlisは大事に受け取りました。"

    def infer(request):
        body = json.loads(request.content)
        sent.append(body)
        assert body["model"] == QWEN_9B_NATURAL_ALIAS
        assert json.loads(body["messages"][-1]["content"]) == {
            "本人の気持ちの言葉": feeling, **focus}
        assert "架空の別人の例" in body["messages"][0]["content"]
        return httpx.Response(200, json={"model": QWEN_9B_NATURAL_ALIAS, "choices": [
            {"finish_reason": "stop", "message": {"role": "assistant", "content": follow}}]})

    source = SelfHostedNaturalReplySource(endpoint="https://model.invalid/v1/chat/completions",
        model=QWEN_9B_NATURAL_ALIAS, api_key="synthetic-only", transport=httpx.MockTransport(infer))
    service = _active_application_owner(monkeypatch, source, None, initial_follow=True)
    dto = run(service.start(user, parent))
    assert dto["state"] == "COMPLETED"
    assert dto["current_observation"]["text"] == f"「{literal}」\n\n{follow}"
    assert run(service.get(user, parent))["current_observation"] == dto["current_observation"]
    saved = run(service.store.read(user, input_id=parent))
    assert saved["original"]["memo"] == thought
    assert saved["original"]["memo_action"] == action
    receipt = next(event["payload"] for event in saved["events"]
                   if event["payload"].get("stage") == "NATURAL_REPLY_RECEIVED")
    assert receipt["writer_context_version"] == INITIAL_OBSERVATION_FOLLOW_CONTEXT_VERSION
    assert receipt["reply"]["model"] == QWEN_9B_NATURAL_ALIAS
    assert len(sent) == 1


@pytest.mark.parametrize("thought,action", [
    ("妹は青い縞が大好きでした。", "本を棚へ戻しました。"),
    ("青い縞が好きでした。私は悲しかったです。", ""),
    ("寂しかったけれど青い縞が好きでした。", ""),
    ("私は寂しかったです。", "晴れてほっとしました。"),
    ("友人が「私は寂しかったです。」と言っていました。", ""),
    ("青い縞が好きな自分に気づきました。", ""),
])
def test_9b_initial_follow_does_not_project_uncertain_or_multiple_feelings(natural_case, qdb, monkeypatch,
                                                                          thought, action):
    from cocolon_meaning_experience_engine.natural_reply import QWEN_9B_NATURAL_ALIAS

    user, parent, _, _ = natural_case
    qdb.query("update public.emotions set memo=$2, memo_action=$3 where id=$1",
              [parent, thought, action])

    def infer(request):
        body = json.loads(request.content)
        material = json.loads(body["messages"][-1]["content"])
        assert "本人の原文" not in material
        assert material["records"][0]["active_fields"][0]["text"] == thought
        return httpx.Response(200, json={"model": QWEN_9B_NATURAL_ALIAS, "choices": [
            {"finish_reason": "stop", "message": {"role": "assistant", "content": BODY}}]})

    source = SelfHostedNaturalReplySource(endpoint="https://model.invalid/v1/chat/completions",
        model=QWEN_9B_NATURAL_ALIAS, api_key="synthetic-only", transport=httpx.MockTransport(infer))
    service = _active_application_owner(monkeypatch, source, None, initial_follow=True)
    dto = run(service.start(user, parent))
    assert dto["current_observation"]["text"] == BODY


@pytest.mark.parametrize("follow", [
    "Emlisは見本帳にあった青い縞を見ました。",
    "私も見本帳にあった青い縞が好きでした。",
    "見本帳にあった青い縞が好きでした。",
    "どんな色合いでしたか。",
    "あの青い縞が、今も私の記憶に鮮明に残っています。",
    "Emlisもその模様を想像するだけで心が和みます。",
    "その模様が愛おしいものか、Emlis はよく存じております。",
    "これからも一緒にその景色を眺めていけたらと思います。",
])
def test_9b_initial_follow_rejects_fabricated_witness_or_unbound_voice(natural_case, qdb, monkeypatch, follow):
    from cocolon_meaning_experience_engine.natural_reply import QWEN_9B_NATURAL_ALIAS

    user, parent, _, _ = natural_case
    qdb.query("update public.emotions set memo=$2 where id=$1",
              [parent, "見本帳にあった青い縞が好きでした。"])
    source = SelfHostedNaturalReplySource(endpoint="https://model.invalid/v1/chat/completions",
        model=QWEN_9B_NATURAL_ALIAS, api_key="synthetic-only",
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json={
            "model": QWEN_9B_NATURAL_ALIAS, "choices": [
                {"finish_reason": "stop", "message": {"role": "assistant", "content": follow}}]})))
    service = _active_application_owner(monkeypatch, source, None, initial_follow=True)
    dto = run(service.start(user, parent))
    assert dto["state"] == "RESPONSE_FAILED"
    assert dto["current_observation"] is None


def test_initial_follow_legacy_writer_retains_its_saved_message_shape():
    from cocolon_meaning_experience_engine.natural_reply import (
        ACTIVE_MEANING_PROFILE, LEGACY_INITIAL_OBSERVATION_FOLLOW_CONTEXT_VERSION,
        build_natural_reply_messages)

    literal = "見本帳にあった青い縞が好きでした。"
    material = NaturalReplyInput("source", "{}", ACTIVE_MEANING_PROFILE, json.dumps({
        "source_context_version": LEGACY_INITIAL_OBSERVATION_FOLLOW_CONTEXT_VERSION,
        "initial_observation_follow": {
            "kind": "対象", "excerpt": literal, "feeling": "好き", "anchor": "見本帳にあった青い縞",
        },
    }))
    messages = build_natural_reply_messages(material)
    assert json.loads(messages[1]["content"]) == {
        "本人の原文": literal, "本人の気持ちの言葉": "好き", "好きだと書いた箇所": "見本帳にあった青い縞",
    }
    assert messages[0]["content"].startswith("文章の話し手はEmlis")


def test_initial_follow_example_writer_preserves_archived_requests_and_separates_examples():
    from cocolon_meaning_experience_engine.natural_reply import (
        ACTIVE_MEANING_PROFILE, CONTEXTUAL_INITIAL_OBSERVATION_FOLLOW_CONTEXT_VERSION,
        GROUNDED_INITIAL_OBSERVATION_FOLLOW_CONTEXT_VERSION,
        INITIAL_OBSERVATION_FOLLOW_CONTEXT_VERSION, READER_INITIAL_OBSERVATION_FOLLOW_CONTEXT_VERSION,
        build_natural_reply_messages)

    focus = {
        "kind": "理由", "excerpt": "明日の展示には参加できないと今日分かったので、私は悲しかったです。",
        "feeling": "悲しかったです", "anchor": "明日の展示には参加できないと今日分かった",
    }

    def messages(version):
        return build_natural_reply_messages(NaturalReplyInput("source", "{}", ACTIVE_MEANING_PROFILE,
            json.dumps({"source_context_version": version, "initial_observation_follow": focus})))

    archived_versions = {
        GROUNDED_INITIAL_OBSERVATION_FOLLOW_CONTEXT_VERSION:
            "83b008c6956ccbbd879c420437be0c035f8b3e914a0d8c43b97e27ddced47554",
        CONTEXTUAL_INITIAL_OBSERVATION_FOLLOW_CONTEXT_VERSION:
            "f601ae648a9cb34fa78302e54341bdb7b5a2b163c4dfc5915972ea4167116b23",
        READER_INITIAL_OBSERVATION_FOLLOW_CONTEXT_VERSION:
            "5278700b041eab9bf89f2b1601899aba9a00b0b6567277529c9c68cd80f954d5",
    }
    for version, expected in archived_versions.items():
        encoded = json.dumps(messages(version), ensure_ascii=False, separators=(",", ":")).encode()
        assert sha256(encoded).hexdigest() == expected
    candidate = messages(INITIAL_OBSERVATION_FOLLOW_CONTEXT_VERSION)
    assert candidate[1] == messages(CONTEXTUAL_INITIAL_OBSERVATION_FOLLOW_CONTEXT_VERSION)[1]
    assert json.loads(candidate[1]["content"])["知った内容"] == "明日の展示には参加できない"
    assert "稽古に出られない" in candidate[0]["content"]
    assert "稽古に出られる" in candidate[0]["content"]
    assert "稽古" not in candidate[1]["content"]


@pytest.mark.parametrize("thought,cues,follow,accepted", [
    ("貸した定規を返してもらえたので、私はほっとしました。",
     {"原文での貸し借りと返却": "貸していたものが戻った"},
     "貸していただいた定規が無事でしたね。ほっとできてよかったです。", False),
    ("貸した定規を返してもらえたので、私はほっとしました。",
     {"原文での貸し借りと返却": "貸していたものが戻った"},
     "貸した定規が戻って、ほっとできたと聞けてよかったです。", True),
    ("貸した定規を返してもらえたので、私はほっとしました。",
     {"原文での貸し借りと返却": "貸していたものが戻った"},
     "相手が借りた定規が戻って、ほっとできてよかったです。", True),
    ("貸したはさみを返してもらえたので、私はほっとしました。",
     {"原文での貸し借りと返却": "貸していたものが戻った"},
     "はさみを貸していただいたときに、ほっとされたのですね。", False),
    ("借りた上着を返せたので、私はほっとしました。",
     {"原文での貸し借りと返却": "借りていたものを返した"},
     "貸した上着が戻ったのですね。ほっとできてよかったです。", False),
    ("借りた上着を返せたので、私はほっとしました。",
     {"原文での貸し借りと返却": "借りていたものを返した"},
     "相手があなたに貸した上着を返せて、ほっとされたのですね。", True),
    ("借りた上着を返せたので、私はほっとしました。",
     {"原文での貸し借りと返却": "借りていたものを返した"},
     "上着を返し終えて、ひと息つけたと聞けてよかったです。", True),
    ("明日の講習には参加できないと今日分かったので、私は悲しかったです。",
     {"知った内容": "明日の講習には参加できない", "知った時点": "今日"},
     "明日の講習に参加できなくなったのは、おつらかったですね。", False),
    ("明日の講習には参加できないと今日分かったので、私は悲しかったです。",
     {"知った内容": "明日の講習には参加できない", "知った時点": "今日"},
     "明日の講習に参加できないと今日分かったときのこと、ここでお聞きしました。", True),
    ("明日の展示には参加できないと今日分かったので、私は悲しかったです。",
     {"知った内容": "明日の展示には参加できない", "知った時点": "今日"},
     "明日の展示参加が今日分かったことで、悲しみを覚えたその気持ちを、Emlis は受け止めました。", False),
    ("明日の展示には参加できないと今日分かったので、私は悲しかったです。",
     {"知った内容": "明日の展示には参加できない", "知った時点": "今日"},
     "明日の展示に参加できると分かったときのお気持ち、ここでお聞きしました。", False),
    ("毎週届く手紙が今月で終わると知ったので、私は寂しかったです。",
     {"知った内容": "毎週届く手紙が今月で終わる"},
     "毎週届く手紙が今月で終わると知った寂しさを、Emlis は今も感じています。", False),
    ("毎週届く手紙が今月で終わると知ったので、私は寂しかったです。",
     {"知った内容": "毎週届く手紙が今月で終わる"},
     "毎週届いていた手紙のこと、終わると知った日の寂しさもここで聞かせてくださいましたね。", True),
    ("丸い取っ手が好きでした。", {"本人が書いた好みの時制": "過去"},
     "丸い取っ手のことが、今でも心に残っているのですね。", False),
    ("丸い取っ手が好きでした。", {"本人が書いた好みの時制": "過去"},
     "丸い取っ手がお好きだったお話を、今聞けて嬉しいです。", True),
    ("丸い取っ手が好きです。", {"本人が書いた好みの時制": "現在"},
     "丸い取っ手を今もお好きなんですね。ここで聞けて嬉しいです。", True),
])
def test_initial_follow_checks_explicit_participants_and_time_before_saving(
        natural_case, qdb, monkeypatch, thought, cues, follow, accepted):
    from cocolon_meaning_experience_engine.natural_reply import QWEN_9B_NATURAL_ALIAS

    user, parent, _, _ = natural_case
    qdb.query("update public.emotions set memo=$2, memo_action='' where id=$1", [parent, thought])
    calls = []

    def infer(request):
        calls.append(request)
        material = json.loads(json.loads(request.content)["messages"][-1]["content"])
        assert {key: material[key] for key in cues} == cues
        return httpx.Response(200, json={"model": QWEN_9B_NATURAL_ALIAS, "choices": [
            {"finish_reason": "stop", "message": {"role": "assistant", "content": follow}}]})

    source = SelfHostedNaturalReplySource(endpoint="https://model.invalid/v1/chat/completions",
        model=QWEN_9B_NATURAL_ALIAS, api_key="synthetic-only", transport=httpx.MockTransport(infer))
    service = _active_application_owner(monkeypatch, source, None, initial_follow=True)
    dto = run(service.start(user, parent))
    if accepted:
        assert dto["current_observation"]["text"] == f"「{thought}」\n\n{follow}"
    else:
        assert dto["state"] == "RESPONSE_FAILED"
        assert dto["current_observation"] is None
    assert run(service.get(user, parent))["current_observation"] == dto["current_observation"]
    assert len(calls) == 1


def test_9b_initial_follow_is_not_selected_by_model_alias_alone(natural_case, qdb, monkeypatch):
    from cocolon_meaning_experience_engine.natural_reply import QWEN_9B_NATURAL_ALIAS

    user, parent, _, _ = natural_case
    thought = "丸い取っ手が好きでした。"
    qdb.query("update public.emotions set memo=$2, memo_action='' where id=$1", [parent, thought])
    calls = []

    def infer(request):
        messages = json.loads(request.content)["messages"]
        calls.append(messages)
        material = json.loads(messages[-1]["content"])
        assert material["records"][0]["active_fields"][0]["text"] == thought
        return httpx.Response(200, json={"model": QWEN_9B_NATURAL_ALIAS, "choices": [
            {"finish_reason": "stop", "message": {"role": "assistant", "content": BODY}}]})

    source = SelfHostedNaturalReplySource(endpoint="https://model.invalid/v1/chat/completions",
        model=QWEN_9B_NATURAL_ALIAS, api_key="synthetic-only", transport=httpx.MockTransport(infer))
    service = _active_application_owner(monkeypatch, source, None)
    dto = run(service.start(user, parent))
    assert dto["current_observation"]["text"] == BODY
    assert len(calls) == 1


@pytest.mark.parametrize("variant", ["listener", "unknown_passage", "strength", "fabricated_voice"])
def test_grounded_9b_uses_an_exact_current_passage_and_separate_listener_reply(
        natural_case, qdb, monkeypatch, variant):
    from cocolon_meaning_experience_engine.grounded_observation_reply import CONTEXT_VERSION
    from cocolon_meaning_experience_engine.natural_reply import QWEN_9B_NATURAL_ALIAS

    user, parent, _, _ = natural_case
    memo = "紙の見本帳にあった細い青い縞が好きでした。"
    action = "受付で見本帳を返しました。"
    qdb.query("update public.emotions set memo=$2, memo_action=$3 where id=$1",
              [parent, memo, action])
    follow = "青い縞に目を留めたお話を分けてくださって、Emlisは嬉しいです。"
    responses = {
        "listener": (None, follow),
        "unknown_passage": ("P0", follow),
        "strength": (None, "あの青い縞が大好きだというお気持ちを受け取りました。"),
        "fabricated_voice": (None, "Emlisはあの青い縞を見ました。"),
    }
    calls = []

    def infer(request):
        body = json.loads(request.content)
        calls.append(body)
        material = json.loads(body["messages"][-1]["content"])
        assert material["stage"] == "FINAL"
        assert material["history"] == []
        assert {item["text"] for item in material["passages"]} == {memo, action}
        assert {item["field"] for item in material["passages"]} == {"memo", "memo_action"}
        bound = next(item["id"] for item in material["passages"] if item["text"] == memo)
        passage, text = responses[variant]
        content = json.dumps({"passages": [passage or bound], "follow": text}, ensure_ascii=False)
        return httpx.Response(200, json={"model": QWEN_9B_NATURAL_ALIAS, "choices": [
            {"finish_reason": "stop", "message": {"role": "assistant", "content": content}}]})

    monkeypatch.setenv("COCOLON_EMLIS_GROUNDED_OBSERVATION", "true")
    source = SelfHostedNaturalReplySource(endpoint="https://model.invalid/v1/chat/completions",
        model=QWEN_9B_NATURAL_ALIAS, api_key="synthetic-only", transport=httpx.MockTransport(infer))
    service = _active_application_owner(monkeypatch, source, None)
    dto = run(service.start(user, parent))
    saved = run(service.store.read(user, input_id=parent))
    started = next(event["payload"] for event in saved["events"]
                   if event["payload"].get("stage") == "NATURAL_REPLY_CALL_STARTED")
    assert started["writer_context_version"] == CONTEXT_VERSION
    if variant == "listener":
        assert dto["state"] == "COMPLETED"
        assert dto["current_observation"]["text"] == f"「{memo}」\n\n{follow}"
        monkeypatch.delenv("COCOLON_EMLIS_GROUNDED_OBSERVATION")
        rebuilt = _active_application_owner(monkeypatch, source, None)
        reread = run(rebuilt.get(user, parent))
        assert reread["revision"] == dto["revision"]
        assert reread["current_observation"] == dto["current_observation"]
    else:
        assert dto["state"] == "RESPONSE_FAILED"
        assert dto["current_observation"] is None
        assert not any(event["payload"].get("stage") == "NATURAL_REPLY_RECEIVED"
                       for event in saved["events"])
    assert len(calls) == 1
