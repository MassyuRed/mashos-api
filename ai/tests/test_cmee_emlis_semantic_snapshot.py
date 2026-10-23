"""Synthetic candidate admission and actual existing thread/service boundaries."""
import copy
import json
from dataclasses import asdict, replace
from unittest.mock import patch

import pytest

from test_cmee_emlis_q1_thread import initial
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.emlis_thread_contracts import (
    EmlisQuestionControlV1, SupplementalAnswerSource)
from cocolon_meaning_experience_engine.emlis_semantic_admission import (
    SemanticInput, SemanticNotAdopted, PROFILE, CANDIDATE_SCHEMA,
    CHECKPOINT_SCHEMA, prepare_snapshot_meaning, derive_snapshot_plan)
from cocolon_meaning_experience_engine.preparation import prepare_emlis, receive_candidate
from test_emlis_q2_application import db, case, run, answer
from emlis_thread_service import EmlisThreadService
import emlis_thread_store
import httpx
from test_emlis_q3_application import qdb, qcase, cont
from emlis_thread_service import Q3_PROFILE
import asyncio


def receipt(req, packet, **metadata):
    material = prepare_emlis(req)
    return receive_candidate(material, request_id=material.request_id,
        raw_output=json.dumps(packet, ensure_ascii=False), finish_reason="stop", **metadata)


def claim(cid, kind, text, index, *, negative=False, time="WRITTEN_PAST_UNRESOLVED_OCCASION",
          expression=None, source=None, predicate=None):
    return dict(claim_id=cid, kind=kind, text=text,
        subject=dict(binding="OMITTED", source_entity=None, evidence_indexes=[]),
        predicate=dict(surface=predicate or text, arguments=[]),
        polarity=dict(value="NEGATED" if negative else "AFFIRMED", scope_refs=[cid], evidence_indexes=[index]),
        modality=dict(value="ASSERTED_AS_WRITTEN", evidence_indexes=[index]),
        about_time=dict(kind=time, expression=expression, anchor_source_id=source, evidence_indexes=[index]),
        qualifiers=[], evidence_indexes=[index])


def evidence(source, field, full, quote):
    start = full.index(quote)
    return dict(source_id=source, field_path=field, start=start, end=start+len(quote), quote=quote)


def base_packet(req):
    raw = req.current_input_bundle.raw_current_input
    sid, memo = raw["id"], raw["memo"]
    ev = [evidence(sid, "memo", memo, "褒められた"),
          evidence(sid, "memo", memo, "嬉しくなかった"),
          evidence(sid, "memo", memo, "のに")]
    cs = [claim("event", "EVENT", "褒められた", 0),
          claim("reaction", "STATE", "嬉しくなかった", 1, negative=True)]
    if raw.get("memo_action"):
        text = raw["memo_action"].rstrip("。")
        ev.append(evidence(sid, "memo_action", raw["memo_action"], text))
        cs.append(claim("other", "STATE", text, 3, predicate="苦しかった"))
    rel = dict(relation_id="contrast", type="SOURCE_WRITTEN_CONCESSION",
        from_claim_id="event", to_claim_id="reaction", polarity="AFFIRMED",
        scope_refs=["contrast"], qualifiers=[], evidence_indexes=[2])
    return dict(candidate=dict(schema_version=CANDIDATE_SCHEMA, core="emlis", claims=cs,
        relations=[rel], unknowns=[], conflicts=[], updates=[]), evidence=ev)


def fresh(req, packet=None, prior=None, **metadata):
    return SemanticInput("FRESH_CANDIDATE", receipt(req, packet or base_packet(req), **metadata),
                         prior_snapshot_json=prior)


def generate(req, semantic):
    engine = MeaningExperienceEngine()
    cp = engine.prepare_emlis_update(req, semantic_input=semantic)
    req = replace(req, emlis_thread=replace(req.emlis_thread, prepared_meaning_checkpoint_ref=cp.checkpoint_id))
    outcome = engine.generate(req, semantic_input=SemanticInput("RESUME_ADOPTED", snapshot_json=cp.semantic_snapshot))
    return req, cp, outcome


def answered(req, outcome, text):
    q = outcome.question
    assert q is not None
    answer = SupplementalAnswerSource("snapshot-answer", req.emlis_thread.thread_id, q.question_id,
        1, req.emlis_thread.original_source_ref, text, "2026-09-11T00:00:00Z")
    return replace(req, emlis_thread=replace(req.emlis_thread, answers=(answer,), current_round=1,
        prepared_meaning_checkpoint_ref=None,
        question_control_context=EmlisQuestionControlV1(q, (q.decision.target_ref,), 1)))


def answer_packet(req, prior, *, operation="ADD", withdraw=False):
    p = json.loads(prior)
    packet = copy.deepcopy(p["packet"])
    cs = packet["candidate"]["claims"]
    text = req.emlis_thread.answers[-1].answer_text_private
    sid = req.emlis_thread.answers[-1].answer_id
    past = operation == "REVISE" or withdraw
    quote = ("その時は寂しかった" if withdraw else "あの時も本当は嬉しかった" if past else "今は嬉しい")
    index = len(packet["evidence"])
    packet["evidence"].append(evidence(sid, "answer_text_private", text, quote))
    cs.append(claim("answer", "STATE", quote, index,
        time="ORIGINAL_OCCASION" if past else "ANSWER_TIME",
        expression="その時" if withdraw else "あの時" if past else "今",
        source=sid, predicate="寂しかった" if withdraw else "嬉しかった" if past else "嬉しい"))
    if operation == "REVISE":
        cs[:] = [c for c in cs if c["claim_id"] != "reaction"]
        packet["candidate"]["relations"] = []
    updates = [dict(operation=operation, target_claim_refs=["reaction"], new_claim_refs=["answer"],
        answer_source_id=sid, prior_meaning_ref=p["snapshot_ref"])]
    if withdraw:
        cs[:] = [c for c in cs if c["claim_id"] != "other"]
        updates.append(dict(operation="WITHDRAW", target_claim_refs=["other"], new_claim_refs=[],
            answer_source_id=sid, prior_meaning_ref=p["snapshot_ref"]))
        packet["evidence"].append(evidence(sid, "answer_text_private", text, "帰宅しても苦しかった"))
    packet["candidate"]["updates"] = updates
    return packet


def test_initial_candidate_reaches_real_author_question_and_snapshot_replay():
    req, cp, out = generate(initial(), fresh(initial()))
    assert cp.semantic_schema_version == CHECKPOINT_SCHEMA
    assert out.artifact is not None, out.reason_codes
    assert out.question is not None
    assert "嬉しくなかった" in out.artifact.observation
    assert out.meaning_checkpoint == cp
    with patch("cocolon_meaning_experience_engine.emlis_question.original_meaning_plan", side_effect=AssertionError("legacy meaning parser")):
        again = MeaningExperienceEngine().generate(req, semantic_input=SemanticInput("RESUME_ADOPTED", snapshot_json=cp.semantic_snapshot))
    assert again == out
    assert not out.automatic_progression


@pytest.mark.parametrize("text,operation,withdraw", [
    ("今は嬉しい。", "ADD", False),
    ("あの時も本当は嬉しかった。書き方を間違えた。", "REVISE", False),
    ('その時は寂しかった。「帰宅しても苦しかった」は誤りです。', "ADD", True)])
def test_real_pending_answer_keeps_subject_time_and_unaffected_material(text, operation, withdraw):
    req = initial(memo_action="帰宅しても苦しかった。" if withdraw else "")
    _, original_cp, original = generate(req, fresh(req))
    if withdraw:
        assert "帰宅しても苦しかった" in original.artifact.observation
    req = answered(req, original, text)
    packet = answer_packet(req, original_cp.semantic_snapshot, operation=operation, withdraw=withdraw)
    req, cp, out = generate(req, fresh(req, packet, original_cp.semantic_snapshot))
    assert out.artifact is not None, out.reason_codes
    assert cp.answer_update.updates[0].operation == operation
    assert "褒められた" in out.artifact.observation
    if operation == "REVISE":
        assert "嬉しくなかった" not in out.artifact.text
    else:
        assert "嬉しくなかった" in out.artifact.observation
    if withdraw:
        assert cp.answer_update.updates[-1].operation == "WITHDRAW"
        assert "帰宅しても苦しかった" not in out.artifact.text
    assert cp == MeaningExperienceEngine().prepare_emlis_update(req, semantic_input=SemanticInput("RESUME_ADOPTED", snapshot_json=cp.semantic_snapshot))


def test_metadata_does_not_change_semantic_identity():
    req = initial()
    a = prepare_snapshot_meaning(req, fresh(req, provider="stub", usage={"input":1}, elapsed_seconds=1))
    b = prepare_snapshot_meaning(req, fresh(req, provider="stub2", usage={"input":9}, elapsed_seconds=2))
    assert a.checkpoint.snapshot_ref == b.checkpoint.snapshot_ref
    assert a.semantic_snapshot != b.semantic_snapshot


@pytest.mark.parametrize("occasion", ["original", "answer_now", "answer_original"])
def test_written_predicate_tense_cannot_be_relabelled(occasion):
    if occasion == "original":
        req = initial(memo="嬉しい。")
        sid = req.current_input_bundle.raw_current_input["id"]
        packet = dict(candidate=dict(schema_version=CANDIDATE_SCHEMA, core="emlis",
            claims=[claim("feeling", "STATE", "嬉しい", 0)],
            relations=[], unknowns=[], conflicts=[], updates=[]),
            evidence=[evidence(sid, "memo", "嬉しい。", "嬉しい")])
        prior = None
    else:
        req = initial()
        _, cp, out = generate(req, fresh(req))
        prior = cp.semantic_snapshot
        text = "今は嬉しかった。" if occasion == "answer_now" else "あの時も本当は嬉しい。書き方を間違えた。"
        req = answered(req, out, text)
        good = replace(req, emlis_thread=replace(req.emlis_thread, answers=(replace(
            req.emlis_thread.answers[0], answer_text_private=("今は嬉しい。" if occasion == "answer_now"
                else "あの時も本当は嬉しかった。書き方を間違えた。")),)))
        packet = answer_packet(good, prior, operation="ADD" if occasion == "answer_now" else "REVISE")
        new = packet["candidate"]["claims"][-1]
        new["text"] = "今は嬉しかった" if occasion == "answer_now" else "あの時も本当は嬉しい"
        new["predicate"]["surface"] = "嬉しかった" if occasion == "answer_now" else "嬉しい"
        packet["evidence"][-1] = evidence("snapshot-answer", "answer_text_private", text, new["text"])
    with pytest.raises(SemanticNotAdopted) as exc:
        prepare_snapshot_meaning(req, fresh(req, packet, prior))
    assert exc.value.reason_code == "semantic_predicate_time_not_bound"


def test_source_mismatch_and_unknown_core_are_rejected():
    req = initial()
    packet = base_packet(req)
    packet["candidate"]["core"] = "piece"
    with pytest.raises(SemanticNotAdopted) as exc:
        prepare_snapshot_meaning(req, fresh(req, packet))
    assert exc.value.decision == "REJECT"
    packet = base_packet(req)
    packet["evidence"][0]["source_id"] = "foreign"
    with pytest.raises(SemanticNotAdopted):
        prepare_snapshot_meaning(req, fresh(req, packet))


def test_necessary_qualifier_and_omitted_claim_cannot_be_dropped():
    req = initial()
    packet = base_packet(req)
    packet["candidate"]["claims"][1]["qualifiers"] = [{"kind":"CONDITION", "text":"if"}]
    with pytest.raises(SemanticNotAdopted) as exc:
        prepare_snapshot_meaning(req, fresh(req, packet))
    assert exc.value.decision == "UNSUPPORTED"
    packet = base_packet(req)
    packet["candidate"]["claims"].pop()
    packet["candidate"]["relations"] = []
    with pytest.raises(SemanticNotAdopted):
        prepare_snapshot_meaning(req, fresh(req, packet))


def test_duplicate_source_clause_cannot_multiply_experience():
    req = initial()
    packet = base_packet(req)
    duplicate = copy.deepcopy(packet["candidate"]["claims"][0])
    duplicate["claim_id"] = "event_duplicate"
    duplicate["polarity"]["scope_refs"] = ["event_duplicate"]
    packet["candidate"]["claims"].append(duplicate)
    with pytest.raises(SemanticNotAdopted) as exc:
        prepare_snapshot_meaning(req, fresh(req, packet))
    assert exc.value.reason_code == "semantic_claim_anchor_overlap"


def test_new_profile_never_falls_back_for_missing_or_modified_snapshot():
    req, cp, out = generate(initial(), fresh(initial()))
    with pytest.raises(SemanticNotAdopted):
        prepare_snapshot_meaning(req, SemanticInput("RESUME_ADOPTED"))
    p = json.loads(cp.semantic_snapshot)
    p["packet"]["candidate"]["claims"][1]["text"] = "嬉しかった"
    with pytest.raises(SemanticNotAdopted):
        prepare_snapshot_meaning(req, SemanticInput("RESUME_ADOPTED", snapshot_json=json.dumps(p)))
    with pytest.raises(SemanticNotAdopted):
        prepare_snapshot_meaning(req, fresh(req))


@pytest.mark.parametrize("kind", ["unused_quote", "foreign_subject", "original_time", "revision_event"])
def test_source_and_semantic_mutations_never_become_adopted(kind):
    req = initial()
    packet = base_packet(req)
    prior = None
    if kind in {"unused_quote", "revision_event"}:
        _, cp, out = generate(req, fresh(req))
        text = "今は嬉しい。彼は寂しかった。" if kind == "unused_quote" else "あの時も本当は嬉しかった。書き方を間違えた。"
        req = answered(req, out, text)
        prior = cp.semantic_snapshot
        packet = answer_packet(req, prior, operation="REVISE" if kind == "revision_event" else "ADD")
        if kind == "unused_quote":
            packet["evidence"].append(evidence("snapshot-answer", "answer_text_private", text, "彼は寂しかった"))
        else:
            packet["candidate"]["updates"][0]["target_claim_refs"] = ["event"]
    elif kind == "foreign_subject":
        req = initial(memo="同僚は嬉しかった。")
        sid = req.current_input_bundle.raw_current_input["id"]
        packet = dict(candidate=dict(schema_version=CANDIDATE_SCHEMA, core="emlis",
            claims=[claim("foreign", "STATE", "同僚は嬉しかった", 0, predicate="嬉しかった")],
            relations=[], unknowns=[], conflicts=[], updates=[]),
            evidence=[evidence(sid,"memo","同僚は嬉しかった。","同僚は嬉しかった")])
    else:
        packet["candidate"]["claims"][1]["about_time"]["kind"] = "ANSWER_TIME"
    with pytest.raises(SemanticNotAdopted):
        prepare_snapshot_meaning(req, fresh(req, packet, prior))


def offline_service(case, *, unsupported=False):
    user, parent, old = case
    calls = []
    def source(req, prior):
        calls.append(bool(prior))
        packet = answer_packet(req, prior) if prior else base_packet(req)
        if unsupported and prior:
            packet["candidate"]["claims"][-1]["qualifiers"] = [{"kind":"unprojectable"}]
        return receipt(req, packet)
    return user, parent, EmlisThreadService(store=old.store, semantic_profile=PROFILE,
        offline_candidate_source=source), calls


def test_actual_sql_service_saves_snapshot_then_replays_dto_without_candidate(case, db):
    user, parent, service, calls = offline_service(case)
    first = run(service.start(user, parent))
    assert first["state"] == "AWAITING_ANSWER", first
    done = run(answer(service, user, first, "今は嬉しい。"))
    assert done["body_state"] == "REFINED", done
    assert calls == [False, True]
    saved = run(service.store.read(user, input_id=parent))
    checkpoints = [e["payload"] for e in saved["events"] if e["kind"] == "MEANING_UPDATE"]
    assert len(checkpoints) == 2
    assert all(c["semantic_schema_version"] == CHECKPOINT_SCHEMA and c["semantic_snapshot"] for c in checkpoints)
    assert saved["thread"]["data"]["runtime_profile"] == "q2.free.one_round.v1"
    class NoAuthor:
        def __getattr__(self, name):
            raise AssertionError("saved reader invoked generation")
    restarted = EmlisThreadService(store=service.store, engine=NoAuthor(),
        semantic_profile=PROFILE, offline_candidate_source=lambda *args: pytest.fail("saved reader acquired candidate"))
    assert run(restarted.get(user, parent)) == done
    assert run(restarted.get(user, parent)) == done
    public = json.dumps(done)
    assert all(k not in public for k in ("semantic_snapshot", "candidate_receipt", "snapshot_ref", "semantic_profile"))


def test_nonadopted_answer_keeps_private_evaluation_without_current_old_body(case):
    user, parent, service, calls = offline_service(case, unsupported=True)
    first = run(service.start(user, parent))
    done = run(answer(service, user, first, "今は嬉しい。"))
    assert done["body_state"] == "ANSWER_UNREFLECTED", done
    assert done["current_observation"] is None
    saved = run(service.store.read(user, input_id=parent))
    assert len([e for e in saved["events"] if e["kind"] == "MEANING_UPDATE"]) == 1
    assert saved["thread"]["evaluated_prefix_ref"] != saved["thread"]["source_prefix_ref"]
    ev = next(e for e in saved["events"] if e["id"] == saved["thread"]["data"]["semantic_evaluation_ref"])
    assert ev["payload"]["decision"] == "UNSUPPORTED"
    assert ev["payload"]["candidate_receipt"]["raw_output"]
    assert run(service.get(user, parent)) == done and len(calls) == 2


def test_unconfigured_service_can_read_but_cannot_mutate_offline_profile(case):
    user, parent, service, calls = offline_service(case)
    first = run(service.start(user, parent))
    normal = EmlisThreadService(store=service.store)
    read = run(normal.get(user, parent))
    assert read["current_observation"] == first["current_observation"]
    assert not read["can_write"]
    before = run(service.store.read(user, input_id=parent))
    with pytest.raises(emlis_thread_store.ThreadStoreError) as exc:
        run(answer(normal, user, first, "今は嬉しい。"))
    assert exc.value.code == "semantic_offline_configuration_required"
    with pytest.raises(emlis_thread_store.ThreadStoreError):
        run(normal.action(user, first["thread_id"], action="skip", expected_revision=first["revision"],
            idempotency_key="blocked-semantic-skip", question_id=first["pending_question"]["question_id"]))
    after = run(service.store.read(user, input_id=parent))
    assert after["thread"] == before["thread"] and after["events"] == before["events"]
    assert calls == [False]


@pytest.mark.parametrize("stage", ["candidate_saved", "meaning_saved", "body_save"])
def test_interruption_reuses_saved_candidate_or_meaning_without_reacquisition(case, db, monkeypatch, stage):
    user, parent, service, calls = offline_service(case)
    first = run(service.start(user, parent))
    original_rpc = db.rpc
    failed = False
    async def rpc(name, payload, **kwargs):
        nonlocal failed
        events = payload.get("p_events", [])
        target = any(e["kind"] == ("MEANING_UPDATE" if stage == "candidate_saved" else "OBSERVATION") for e in events)
        if stage != "meaning_saved" and not failed and payload.get("p_next", {}).get("latest_answer_event_id") and target:
            failed = True
            return httpx.Response(503, json={"code":"57P03"})
        return await original_rpc(name, payload, **kwargs)
    monkeypatch.setattr(emlis_thread_store, "sb_post_rpc", rpc)
    if stage == "meaning_saved":
        old_generate = service.engine.generate
        def interrupt(*args, **kwargs):
            raise asyncio.CancelledError()
        monkeypatch.setattr(service.engine, "generate", interrupt)
        with pytest.raises(asyncio.CancelledError):
            run(answer(service, user, first, "今は嬉しい。"))
        broken = run(service.get(user, parent))
        monkeypatch.setattr(service.engine, "generate", old_generate)
    else:
        broken = run(answer(service, user, first, "今は嬉しい。"))
    assert broken["can_retry"], broken
    saved_before = run(service.store.read(user, input_id=parent))
    new_cp_before = [e["id"] for e in saved_before["events"] if e["kind"] == "MEANING_UPDATE"]
    def never(*args, **kwargs):
        raise AssertionError("candidate must not be reacquired")
    service.offline_candidate_source = never
    done = run(service.action(user, broken["thread_id"], action="retry_response",
        expected_revision=broken["revision"], idempotency_key="snapshot-retry", operation_id=broken["operation_id"]))
    assert done["body_state"] == "REFINED", done
    saved = run(service.store.read(user, input_id=parent))
    new_cp_after = [e["id"] for e in saved["events"] if e["kind"] == "MEANING_UPDATE"]
    assert len(new_cp_after) == 2
    assert new_cp_after[:len(new_cp_before)] == new_cp_before
    assert len([e for e in saved["events"] if e["kind"] == "ANSWER"]) == 1
    assert calls == [False, True]


def test_interrupted_acquisition_finishes_retry_without_acquiring_again(case):
    user, parent, service, calls = offline_service(case)
    first = run(service.start(user, parent))
    def interrupt(*args, **kwargs):
        raise asyncio.CancelledError()
    service.offline_candidate_source = interrupt
    with pytest.raises(asyncio.CancelledError):
        run(answer(service, user, first, "今は嬉しい。"))
    broken = run(service.get(user, parent))
    assert broken["can_retry"], broken
    def never(*args, **kwargs):
        raise AssertionError("interrupted candidate must not be reacquired")
    service.offline_candidate_source = never
    done = run(service.action(user, broken["thread_id"], action="retry_response",
        expected_revision=broken["revision"], idempotency_key="snapshot-incomplete-retry", operation_id=broken["operation_id"]))
    assert done["state"] == "COMPLETED" and not done["can_retry"], done
    assert done["body_state"] == "ANSWER_UNREFLECTED" and done["current_observation"] is None
    saved = run(service.store.read(user, input_id=parent))
    assert saved["thread"]["active_attempt_id"] is None
    assert len([e for e in saved["events"] if e["kind"] == "MEANING_UPDATE"]) == 1
    evaluation = next(e for e in reversed(saved["events"]) if e["payload"].get("stage") == "SEMANTIC_NOT_ADOPTED")
    assert evaluation["payload"]["reason_codes"] == ["semantic_candidate_acquisition_incomplete"]
    assert calls == [False]


def multi_packet(req):
    raw = req.current_input_bundle.raw_current_input
    sid, memo = raw["id"], raw["memo"]
    packet = dict(candidate=dict(schema_version=CANDIDATE_SCHEMA, core="emlis", claims=[],
        relations=[], unknowns=[], conflicts=[], updates=[]), evidence=[])
    for n, (event, feeling) in enumerate((("褒められた", "嬉しくなかった"), ("誘われた", "悲しかった"), ("頼まれた", "寂しかった"))):
        offset = memo.index(event)
        e = dict(source_id=sid, field_path="memo", start=offset, end=offset+len(event), quote=event)
        f = evidence(sid, "memo", memo, feeling)
        marker = dict(source_id=sid,field_path="memo",start=offset+len(event),end=offset+len(event)+2,quote="のに")
        i = len(packet["evidence"])
        packet["evidence"] += [e,f,marker]
        packet["candidate"]["claims"] += [claim(f"e{n}","EVENT",event,i), claim(f"r{n}","STATE",feeling,i+1,negative=n==0)]
        packet["candidate"]["relations"].append(dict(relation_id=f"c{n}",type="SOURCE_WRITTEN_CONCESSION",
            from_claim_id=f"e{n}",to_claim_id=f"r{n}",polarity="AFFIRMED",scope_refs=[f"c{n}"],qualifiers=[],evidence_indexes=[i+2]))
    return packet


def multi_source(calls):
    def source(req, prior):
        calls.append(len(req.emlis_thread.answers))
        if prior is None:
            return receipt(req, multi_packet(req))
        p = json.loads(prior)
        packet = copy.deepcopy(p["packet"])
        packet["candidate"]["updates"] = []
        answer = req.emlis_thread.answers[-1]
        if answer.answer_text_private == "わからない。":
            return receipt(req, packet)
        number = len(req.emlis_thread.answers)
        quote = answer.answer_text_private.rstrip("。")
        predicate = {1:"重かった", 2:"怖かった", 3:"苦しかった"}[number]
        i = len(packet["evidence"])
        packet["evidence"].append(evidence(answer.answer_id,"answer_text_private",answer.answer_text_private,quote))
        cid = f"a{number}"
        packet["candidate"]["claims"].append(claim(cid,"STATE",quote,i,time="ORIGINAL_OCCASION",
            expression="その時",source=answer.answer_id,predicate=predicate))
        packet["candidate"]["updates"] = [dict(operation="ADD",target_claim_refs=[f"r{number-1}"],new_claim_refs=[cid],
            answer_source_id=answer.answer_id,prior_meaning_ref=p["snapshot_ref"])]
        return receipt(req, packet)
    return source


@pytest.mark.parametrize("last_unknown", [False, True])
def test_q3_real_continue_keeps_prior_answers_about_relations_and_nochange(qcase, qdb, last_unknown):
    user, parent, old = qcase
    calls = []
    service = EmlisThreadService(store=old.store, runtime_profile=Q3_PROFILE,
        semantic_profile=PROFILE, offline_candidate_source=multi_source(calls))
    dto = run(service.start(user,parent))
    assert dto["state"] == "AWAITING_ANSWER", dto
    for number, text in enumerate(("その時は重かった。","その時は怖かった。","わからない。" if last_unknown else "その時は苦しかった。"),1):
        assert dto["issued_count"] == number
        dto = run(answer(service,user,dto,text,f"semantic-answer-{number}"))
        assert dto["body_state"] == ("UNCHANGED" if number==3 and last_unknown else "REFINED"), dto
        if number < 3:
            assert dto["state"] == "AWAITING_CONTINUE", dto
            dto = run(cont(service,user,dto,f"semantic-continue-{number}"))
    assert calls == [0,1,2,3]
    assert not dto["can_continue"]
    saved = run(service.store.read(user,input_id=parent))
    checkpoints = [e["payload"] for e in saved["events"] if e["kind"] == "MEANING_UPDATE"]
    assert len(checkpoints) == 4
    assert len(checkpoints[-1]["accepted_update_refs"]) == (2 if last_unknown else 3)
    observations = [e for e in saved["events"] if e["kind"] == "OBSERVATION"]
    graph = observations[-1]["payload"]["meaning_graph"]
    assert len([e for e in graph["edges"] if e["relation"] == "evaluation_about_event"]) == (2 if last_unknown else 3)
