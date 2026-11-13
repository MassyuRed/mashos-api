"""User correction, actual isolated SQL/CAS and synthetic recipient provider."""
import json
from uuid import uuid4

import pytest
import httpx
import emlis_thread_store

from test_emlis_q2_application import run
from test_emlis_q3_application import qdb
from test_emlis_natural_reply_application import natural_case, BODY
from emlis_thread_store import ThreadStoreError
from cocolon_meaning_experience_engine.natural_reply import (
    NaturalReply, NaturalReplyError, NaturalReplyInput, SelfHostedNaturalReplySource,
    build_natural_reply_messages, system_message_for,
)

EXPLANATION = "安心したのではなく、終わってもまだ心配が残っています。資料を読み直したことは合っています。"
REPLY = "会議が終わっても心配は残っているのですね。資料を読み直したことと、今の気持ちは分けて受け取りました。"


def _target_context_request():
    def correction(identity, target, explanation):
        return dict(source_role="USER_INTERPRETATION_CORRECTION", correction_id=identity,
            recorded_at="2026-11-13T04:00:00+09:00", target_event_id="event-" + identity,
            target_ai_interpretation=target, user_explanation=explanation, assessment="UNASSESSED")

    target = "先生が姉を呼び止めた"
    material = dict(current_input_id="current-record",
        current=dict(memo='AIには「' + target + '」と書かれたが違った。',
                     memo_action="姉が先生を呼び止めた。"),
        interpretation_corrections=[correction("current-vague", target, "違います。"),
            correction("current-detail", target, '「' + target + '」ではなく、姉が先に声をかけました。')],
        current_answers=[], user_frame_feedback=[],
        past_user_records=[dict(input_id="past-record", original=dict(memo="資料を渡した。"),
            answers=[], interpretation_corrections=[correction("past-correction", "資料を受け取った",
                "受け取ったのではなく、私から渡しました。")])])
    return NaturalReplyInput("unchanged-correction-prefix", json.dumps(material, ensure_ascii=False, indent=2))


def test_target_context_projection_preserves_sources_and_all_current_past_corrections():
    request = _target_context_request()
    original = request.material_json
    source = json.loads(original)
    baseline = build_natural_reply_messages(request)
    projected = build_natural_reply_messages(request, correction_target_context=True)
    assert baseline == [dict(role="system", content=system_message_for(request)),
                        dict(role="user", content=original)]
    assert [row["role"] for row in projected] == ["system", "assistant", "user"]
    assert projected[0] == baseline[0]
    targets = json.loads(projected[1]["content"])["ai_interpretation_targets"]
    person = json.loads(projected[2]["content"])
    assert [row["correction_id"] for row in targets] == ["current-vague", "current-detail", "past-correction"]
    assert [row["parent_input_id"] for row in targets] == ["current-record", "current-record", "past-record"]
    assert [row["correction_source_path"] for row in targets] == [
        "interpretation_corrections[0]", "interpretation_corrections[1]",
        "past_user_records[0].interpretation_corrections[0]"]
    assert all(row["source_role"] == "AI_INTERPRETATION_TARGET" and "recorded_at" not in row
               for row in targets)
    person_rows = person["interpretation_corrections"] + person["past_user_records"][0]["interpretation_corrections"]
    original_rows = source["interpretation_corrections"] + source["past_user_records"][0]["interpretation_corrections"]
    assert len(targets) == len(person_rows) == len(original_rows) == 3
    for index, (row, ai, old) in enumerate(zip(person_rows, targets, original_rows)):
        reference = f"ai_interpretation_targets[{index}]"
        assert row.pop("target_ai_context_ref") == ai["context_ref"] == reference
        assert "target_ai_interpretation" not in row
        assert ai["target_event_id"] == old["target_event_id"]
        assert ai["target_ai_interpretation"] == old["target_ai_interpretation"]
        row["target_ai_interpretation"] = ai["target_ai_interpretation"]
    # This also proves that literal user quotations and all vague/multiple
    # explanations survived: no global text removal or opposite meaning.
    assert person == source
    assert request.material_json == original and request.source_prefix_ref == "unchanged-correction-prefix"


@pytest.mark.parametrize("enabled", [False, True])
def test_target_context_option_reaches_only_the_existing_http_message_owner(enabled):
    request = _target_context_request()
    before = request.material_json
    calls = []

    def handler(sent):
        body = json.loads(sent.content)
        calls.append(body)
        assert body == dict(model="configured-only",
            messages=build_natural_reply_messages(request, correction_target_context=enabled),
            temperature=0, max_tokens=2048, stream=False, chat_template_kwargs={"enable_thinking": False})
        return httpx.Response(200, json={"model": "configured-only", "choices": [{"finish_reason": "stop",
            "message": {"role": "assistant", "content": "本人の説明を受け取る合成の返事です。"}}]})

    options = {"correction_target_context": True} if enabled else {}
    provider = SelfHostedNaturalReplySource(endpoint="https://provider.example/v1/chat/completions",
        model="configured-only", api_key="synthetic", transport=httpx.MockTransport(handler), **options)
    reply = run(provider(request))
    assert reply.source_prefix_ref == request.source_prefix_ref
    assert request.material_json == before and len(calls) == 1
    assert [row["role"] for row in calls[0]["messages"]] == (
        ["system", "assistant", "user"] if enabled else ["system", "user"])


def test_target_context_no_correction_keeps_original_message_bytes_through_http():
    material = '{ "current": {"memo":"普通の記録。"}, "past_user_records": [] }'
    request = NaturalReplyInput("ordinary-prefix", material)
    expected = build_natural_reply_messages(request)
    calls = []

    def handler(sent):
        calls.append(json.loads(sent.content))
        assert calls[0]["messages"] == expected
        assert calls[0]["messages"][1]["content"] == material
        return httpx.Response(200, json={"model": "configured-only", "choices": [{"finish_reason": "stop",
            "message": {"role": "assistant", "content": "普通の合成の返事です。"}}]})

    provider = SelfHostedNaturalReplySource(endpoint="https://provider.example/v1/chat/completions",
        model="configured-only", api_key="synthetic", transport=httpx.MockTransport(handler),
        correction_target_context=True)
    assert run(provider(request)).source_prefix_ref == "ordinary-prefix"
    assert len(calls) == 1 and request.material_json == material


@pytest.mark.parametrize("mutation", ["target", "parent", "reference", "list"])
def test_target_context_malformed_later_record_rejects_before_http_without_partial_projection(mutation):
    original = _target_context_request()
    material = json.loads(original.material_json)
    past = material["past_user_records"][0]
    if mutation == "target":
        past["interpretation_corrections"][0]["target_ai_interpretation"] = None
    elif mutation == "parent":
        past["input_id"] = ""
    elif mutation == "reference":
        past["interpretation_corrections"][0]["target_ai_context_ref"] = "foreign-context"
    else:
        past["interpretation_corrections"] = {}
    request = NaturalReplyInput(original.source_prefix_ref, json.dumps(material, ensure_ascii=False))
    before = request.material_json
    calls = []

    def handler(sent):
        calls.append(sent)
        raise AssertionError("malformed projection must not reach provider")

    provider = SelfHostedNaturalReplySource(endpoint="https://provider.example/v1/chat/completions",
        model="configured-only", api_key="synthetic", transport=httpx.MockTransport(handler),
        correction_target_context=True)
    with pytest.raises(NaturalReplyError, match="natural_reply_correction_context_invalid"):
        run(provider(request))
    assert not calls and request.material_json == before
    assert build_natural_reply_messages(request)[1]["content"] == before


def test_correction_roles_reach_research_author_and_independent_saved_comparison(natural_case):
    user, parent, service, calls = natural_case
    dto = run(service.start(user, parent))
    explanation = "先生から呼び止められたのは妹だった。"

    async def source(material):
        calls.append(material)
        assert 'source_meaning_support' not in json.loads(material.material_json)
        from emlis_thread_service import _request
        from cocolon_meaning_experience_engine.natural_reply import prepare_natural_reply
        snapshot = await service.store.read(user, input_id=parent)
        research, safety = prepare_natural_reply(_request(snapshot), use_meaning_support=True)
        assert safety.normal_observation_allowed and research.source_prefix_ref == material.source_prefix_ref
        data = json.loads(research.material_json)
        hint, = data['source_meaning_support']['witnesses']
        assert hint['source_role'] == 'USER_INTERPRETATION_CORRECTION'
        assert hint['source_path'] == 'interpretation_corrections[0].user_explanation'
        assert hint['行為者'] == '原文の人物表記：先生'
        assert hint['相手'] == '原文の人物表記：妹'
        assert data['interpretation_corrections'][0]['user_explanation'] == explanation
        return NaturalReply('先生が妹を呼び止めたのですね。', 'synthetic-correction', material.source_prefix_ref)

    service.natural_reply_source = source
    after = run(correct(service, user, dto, explanation=explanation))
    saved = run(service.store.read(user, input_id=parent))
    event = [e for e in saved['events'] if e['kind'] == 'OBSERVATION'][-1]
    report = event['payload']['artifact']['meaning_comparison']
    assert report['verdict'] == 'NO_CONFLICT_IN_CHECKED_SCOPE'
    check, = report['checks']
    assert check['source_role'] == 'USER_INTERPRETATION_CORRECTION'
    assert check['parent_input_id'] == parent
    assert not report['full_reply_semantic_coverage']
    assert after['correction_assessment'] == 'UNASSESSED' and not after['meaning_updated']
    assert run(service.get(user, parent))['current_observation'] == after['current_observation']
    assert len(calls) == 2
    assert 'meaning_comparison' not in json.dumps(after)


def correct(service, user, dto, *, text="少し安心できた", explanation=EXPLANATION, key="correction-1", target=None):
    return service.correct_interpretation(user, dto["thread_id"],
        expected_revision=dto["revision"], idempotency_key=key,
        target_event_id=target or (dto.get("current_observation") or dto["correction_target"])["event_id"],
        target_text=text, explanation=explanation)


@pytest.mark.parametrize("tier", ["free", "plus", "premium"])
def test_correction_is_separate_bound_source_saved_and_reread_without_question_or_input(natural_case, qdb, tier):
    user, parent, service, calls = natural_case
    qdb.query("update public.profiles set subscription_tier=$2 where id=$1", [user, tier])
    dto = run(service.start(user, parent))
    old = dto["current_observation"]

    async def source(material):
        calls.append(material)
        data = json.loads(material.material_json)
        correction = data["interpretation_corrections"][0]
        assert correction["target_ai_interpretation"] == "少し安心できた"
        assert correction["user_explanation"] == EXPLANATION
        assert correction["target_event_id"] == old["event_id"]
        assert correction["assessment"] == "UNASSESSED"
        assert data["current"]["memo"] == dto["original"]["memo"]
        assert not data["current_answers"]
        assert "本人が述べた事実でも" in system_message_for(material)
        saved = await service.store.read(user, input_id=parent)
        assert service._dto(saved)["current_observation"] is None
        assert saved["thread"]["current_meaning_event_id"] is None
        return NaturalReply(REPLY, "synthetic-correction", material.source_prefix_ref)

    service.natural_reply_source = source
    changed = run(correct(service, user, dto))
    assert changed["state"] == "COMPLETED" and changed["current_observation"]["text"] == REPLY
    assert changed["current_observation"]["event_id"] != old["event_id"]
    assert changed["correction_saved"] and changed["correction_assessment"] == "UNASSESSED"
    assert changed["issued_count"] == dto["issued_count"] == 0
    assert not changed["answer_saved"] and not changed["meaning_updated"]
    assert next(e for e in changed["timeline"] if e["event_id"] == old["event_id"])["is_disputed"]
    note = next(e for e in changed["timeline"] if e["kind"] == "CORRECTION")
    assert note["text"] == EXPLANATION and note["operation_key"] == "correction-1"
    for _ in range(2):
        assert run(service.get(user, parent))["current_observation"] == changed["current_observation"]
    replay = run(correct(service, user, dto))
    assert replay["current_observation"] == changed["current_observation"]
    assert len(calls) == 2
    rows = qdb.query("select count(*) n from public.emotions where user_id=$1", [user])
    assert rows["rows"][0]["n"] == 1


def test_bare_disagreement_is_saved_but_never_resolved_or_generated(natural_case):
    user, parent, service, calls = natural_case
    dto = run(service.start(user, parent))
    pending = run(correct(service, user, dto, explanation="違います。"))
    assert pending["correction_assessment"] == "NEEDS_DETAIL"
    assert pending["current_observation"] is None and pending["can_correct"]
    assert pending["correction_target"] == dto["current_observation"]
    assert len(calls) == 1
    assert run(service.get(user, parent))["correction_assessment"] == "NEEDS_DETAIL"

    async def source(material):
        calls.append(material)
        assert len(json.loads(material.material_json)["interpretation_corrections"]) == 2
        return NaturalReply(REPLY, "synthetic-correction", material.source_prefix_ref)

    service.natural_reply_source = source
    changed = run(correct(service, user, pending, key="more-detail"))
    assert changed["current_observation"]["text"] == REPLY and len(calls) == 2


@pytest.mark.parametrize("mutation,code", [
    ({"target": str(uuid4())}, "correction_target_changed"),
    ({"text": "原文にない内容"}, "correction_target_must_be_unique_excerpt"),
    ({"text": " "}, "correction_fields_required"),
    ({"explanation": " "}, "correction_fields_required"),
])
def test_invalid_target_or_blank_fields_do_not_admit_or_generate(natural_case, mutation, code):
    user, parent, service, calls = natural_case
    dto = run(service.start(user, parent))
    with pytest.raises(ThreadStoreError, match=code):
        run(correct(service, user, dto, **mutation))
    assert run(service.get(user, parent))["revision"] == dto["revision"] and len(calls) == 1


def test_failed_correction_generation_never_restores_disputed_reply(natural_case):
    user, parent, service, calls = natural_case
    dto = run(service.start(user, parent))
    async def unavailable(material):
        calls.append(material)
        raise RuntimeError("synthetic unavailable")
    service.natural_reply_source = unavailable
    changed = run(correct(service, user, dto))
    assert changed["state"] == "RESPONSE_FAILED" and changed["current_observation"] is None
    assert changed["correction_saved"] and not changed["can_retry"]
    reopened = run(service.get(user, parent))
    assert reopened["current_observation"] is None and len(calls) == 2


def test_correction_is_not_readable_or_writable_by_another_owner(natural_case):
    user, parent, service, calls = natural_case
    dto = run(service.start(user, parent))
    with pytest.raises(ThreadStoreError) as error:
        run(correct(service, str(uuid4()), dto))
    assert error.value.status == 404 and len(calls) == 1


@pytest.mark.parametrize("lost_stage", ["INTERPRETATION_CORRECTION", "NATURAL_REPLY_RECEIVED"])
def test_lost_admission_or_receipt_ack_recovers_saved_command_without_reacquisition(natural_case, qdb, monkeypatch, lost_stage):
    user, parent, service, calls = natural_case
    dto = run(service.start(user, parent))
    lost = False
    async def rpc(name, payload, **kwargs):
        nonlocal lost
        result = await qdb.rpc(name, payload, **kwargs)
        if not lost and any(e["payload"].get("stage") == lost_stage for e in payload.get("p_events", [])):
            lost = True
            raise httpx.ReadTimeout("synthetic ACK loss")
        return result
    async def source(material):
        calls.append(material)
        return NaturalReply(REPLY, "synthetic-correction", material.source_prefix_ref)
    service.natural_reply_source = source
    monkeypatch.setattr(emlis_thread_store, "sb_post_rpc", rpc)
    changed = run(correct(service, user, dto))
    assert lost and changed["current_observation"]["text"] == REPLY and len(calls) == 2
    assert run(correct(service, user, dto))["current_observation"] == changed["current_observation"]
    assert len(calls) == 2


@pytest.mark.parametrize("first_explanation", ["違う", EXPLANATION])
def test_older_correction_replay_cannot_restore_an_older_reply(natural_case, first_explanation):
    user, parent, service, calls = natural_case
    original = run(service.start(user, parent))
    async def source(material):
        calls.append(material)
        text = "心配が残っていますね。" if len(calls) == 2 else "後の説明に沿って受け取り直しました。"
        return NaturalReply(text, "synthetic-correction", material.source_prefix_ref)
    service.natural_reply_source = source
    first = run(correct(service, user, original, explanation=first_explanation))
    second = run(correct(service, user, first, key="correction-2",
        text="少し安心できた" if first_explanation == "違う" else "心配が残っていますね。",
        explanation="心配ではなく、確認したいことが一つ残っているという意味です。"))
    count = len(calls)
    replay = run(correct(service, user, original, explanation=first_explanation))
    assert replay["current_observation"] == second["current_observation"]
    assert replay["revision"] == second["revision"] and len(calls) == count


@pytest.mark.parametrize("tier,included", [("free", False), ("plus", True), ("premium", True)])
def test_later_natural_history_preserves_correction_only_with_existing_entitlement(natural_case, qdb, tier, included):
    user, parent, service, calls = natural_case
    qdb.query("update public.profiles set subscription_tier=$2 where id=$1", [user, tier])
    qdb.query("update public.emotions set created_at=(now()-interval '1 minute') at time zone 'UTC' where id=$1", [parent])
    original = run(service.start(user, parent))
    run(correct(service, user, original, explanation="違う"))
    later = str(uuid4())
    qdb.query("insert into public.emotions values ($1,$2,now() at time zone 'UTC',$3,'',array['仕事'],array['平穏'],$4)",
        [later, user, "会議の資料をもう一度読み直した。", json.dumps([dict(type="平穏", strength="medium")])])
    run(service.start(user, later))
    history = json.loads(calls[-1].material_json)["past_user_records"]
    assert bool(history) is included
    if included:
        assert history[0]["input_id"] == parent
        correction = history[0]["interpretation_corrections"][0]
        assert correction["user_explanation"] == "違う"
        assert correction["assessment"] == "UNASSESSED"
        assert "target_ai_interpretation" in correction
        assert "answer_meaning" not in history[0]


def test_correction_invalidates_a_reply_already_using_that_history(natural_case, qdb):
    user, parent, service, calls = natural_case
    qdb.query("update public.profiles set subscription_tier='plus' where id=$1", [user])
    qdb.query("update public.emotions set created_at=(now()-interval '1 minute') at time zone 'UTC' where id=$1", [parent])
    original = run(service.start(user, parent))
    later = str(uuid4())
    qdb.query("insert into public.emotions values ($1,$2,now() at time zone 'UTC',$3,'',array['仕事'],array['平穏'],$4)",
        [later, user, "会議の資料を読み直した。", json.dumps([dict(type="平穏", strength="medium")])])
    before = run(service.start(user, later))
    assert before["current_observation"]
    run(correct(service, user, original, explanation="違う"))
    after = run(service.get(user, later))
    assert after["current_observation"] is None and after["body_state"] == "CONTEXT_CHANGED"
    assert not any(e["kind"] == "OBSERVATION" for e in after["timeline"])


def test_correction_http_route_uses_owner_and_public_allowlist(natural_case, monkeypatch):
    from fastapi import FastAPI
    import api_emlis_thread as api
    user, parent, service, calls = natural_case
    dto = run(service.start(user, parent))
    async def owner(authorization):
        assert authorization == "Bearer synthetic"
        return user
    async def source(material):
        calls.append(material)
        return NaturalReply(REPLY, "synthetic-correction", material.source_prefix_ref)
    service.natural_reply_source = source
    monkeypatch.setattr(api, "_require_user_id", owner)
    monkeypatch.setattr(api, "read_enabled", lambda: True)
    monkeypatch.setattr(api, "writes_enabled", lambda: True)
    app = FastAPI()
    api.register_emlis_thread_routes(app, service=service)
    async def request():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url="http://synthetic") as client:
            return await client.post(f"/emlis/threads/{dto['thread_id']}/corrections",
                headers={"authorization": "Bearer synthetic"}, json={
                    "expected_revision": dto["revision"], "idempotency_key": "http-correction",
                    "target_event_id": dto["current_observation"]["event_id"],
                    "target_text": "少し安心できた", "explanation": EXPLANATION})
    response = run(request())
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "private, no-store"
    result = response.json()
    assert result["current_observation"]["text"] == REPLY and result["correction_saved"]
    assert next(e for e in result["timeline"] if e["kind"] == "CORRECTION")["text"] == EXPLANATION
    assert all(secret not in response.text for secret in ("source_prefix_ref", "material_json", "request_fingerprint", "synthetic-correction"))


def test_disputed_target_cannot_reexpose_a_reply_after_history_context_changed(natural_case):
    import copy
    from emlis_thread_service import thread_dto
    user, parent, service, calls = natural_case
    dto = run(service.start(user, parent))
    run(correct(service, user, dto, explanation="違う"))
    snapshot = run(service.store.read(user, input_id=parent))
    snapshot = copy.deepcopy(snapshot)
    snapshot["context"] = {"history": [], "feedback": []}
    body = next(e for e in snapshot["events"] if e["kind"] == "OBSERVATION")
    body["payload"]["context_guards"] = [["unavailable-history", "source", 1]]
    body["payload"]["context_ref"] = "old-context"
    value = thread_dto(snapshot)
    assert value["current_observation"] is None
    assert value["correction_target"] is None and not value["can_correct"]
    assert not any(e["kind"] == "OBSERVATION" for e in value["timeline"])
