"""Recipient reply over the actual Q3 SQL/RPC; provider calls are synthetic.

These checks prove storage/lifecycle behavior, never real-model quality.
"""
import asyncio
from dataclasses import replace
import json
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


@pytest.fixture
def natural_case(qdb, monkeypatch):
    user, parent = str(uuid4()), str(uuid4())
    qdb.query("insert into auth.users values ($1)", [user])
    qdb.query("insert into public.profiles values ($1,'free')", [user])
    qdb.query("insert into public.emotions values ($1,$2,now() at time zone 'UTC',$3,'',array['仕事'],array['平穏'],$4)",
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
