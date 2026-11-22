"""Synthetic candidate admission and actual existing thread/service boundaries."""
import copy
import json
from pathlib import Path
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


V1_FIXTURE = json.loads((Path(__file__).parent / "fixtures/cmee_emlis_semantic_adapter_v1.json").read_text())


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


@pytest.mark.parametrize("row", V1_FIXTURE["records"], ids=lambda row: row["case"])
def test_frozen_adapter_v1_snapshots_replay_complete_original_outcomes(row):
    req = initial(memo_action=row["original_memo_action"])
    req, cp, first = generate(req, SemanticInput("RESUME_ADOPTED", snapshot_json=row["initial_snapshot"]))
    assert json.loads(json.dumps(asdict(first))) == row["initial_outcome"]
    req = answered(req, first, row["answer_text"])
    _, cp, out = generate(req, SemanticInput("RESUME_ADOPTED", snapshot_json=row["answer_snapshot"]))
    assert json.loads(json.dumps(asdict(out))) == row["answer_outcome"]
    assert cp.semantic_snapshot == row["answer_snapshot"]


@pytest.mark.parametrize("row", V1_FIXTURE["records"], ids=lambda row: row["case"])
def test_new_adapter_separates_time_topic_without_dropping_additive_particle(row):
    req = initial(memo_action=row["original_memo_action"])
    _, cp, first = generate(req, fresh(req))
    req = answered(req, first, row["answer_text"])
    packet = answer_packet(req, cp.semantic_snapshot, operation="REVISE" if row["case"] == "REVISE" else "ADD",
        withdraw=row["case"] == "WITHDRAW")
    req, cp, out = generate(req, fresh(req, packet, cp.semantic_snapshot))
    assert json.loads(cp.semantic_snapshot)["adapter_version"] == "2"
    assert out.artifact is not None, out.reason_codes
    assert all(phrase not in out.artifact.text for phrase in (
        "回答した時点では今は", "その時にその時は", "その時は「その時は"))
    prepared = prepare_snapshot_meaning(req, SemanticInput("RESUME_ADOPTED", snapshot_json=cp.semantic_snapshot))
    node = prepared.accepted_nuclei[-1]
    raw = node.semantic_frame.attribute_codes
    expected = {"ADD":"source_fragment_scalar_range:2:5", "REVISE":"source_fragment_scalar_range:0:12",
                "WITHDRAW":"source_fragment_scalar_range:4:9"}[row["case"]]
    assert expected in raw
    if row["case"] == "REVISE":
        assert "あの時も本当は" in out.artifact.text
    assert json.loads(cp.semantic_snapshot)["packet"] == packet


def test_actual_v1_pending_can_take_one_new_v2_answer_without_reinterpreting_prior():
    row = V1_FIXTURE["records"][0]
    req, old_cp, first = generate(initial(), SemanticInput("RESUME_ADOPTED", snapshot_json=row["initial_snapshot"]))
    req = answered(req, first, row["answer_text"])
    packet = answer_packet(req, old_cp.semantic_snapshot)
    _, cp, out = generate(req, fresh(req, packet, old_cp.semantic_snapshot))
    snapshot = json.loads(cp.semantic_snapshot)
    assert snapshot["adapter_version"] == "2" and snapshot["prior_snapshot"]["adapter_version"] == "1"
    assert snapshot["prior_snapshot"] == json.loads(old_cp.semantic_snapshot)
    assert out.artifact is not None
    assert "では今は" not in out.artifact.text


@pytest.mark.parametrize("text,kind,expression,predicate,negative", [
    ("現在は少し嬉しくない。", "ANSWER_TIME", "現在", "嬉しくない", True),
    ("今も少し嬉しくない。", "ANSWER_TIME", "今", "嬉しくない", True),
    ("当時は本当は嬉しかった。書き方を間違えた。", "ORIGINAL_OCCASION", "当時", "嬉しかった", False)])
def test_time_alias_keeps_degree_and_polarity(text, kind, expression, predicate, negative):
    req = initial()
    _, cp, first = generate(req, fresh(req))
    req = answered(req, first, text)
    packet = answer_packet(replace(req, emlis_thread=replace(req.emlis_thread, answers=(replace(
        req.emlis_thread.answers[0], answer_text_private=("今は嬉しい。" if kind == "ANSWER_TIME"
            else "あの時も本当は嬉しかった。書き方を間違えた。")),))), cp.semantic_snapshot,
        operation="ADD" if kind == "ANSWER_TIME" else "REVISE")
    i = len(packet["evidence"]) - 1
    quote = text.split("。")[0]
    packet["evidence"][i] = evidence("snapshot-answer", "answer_text_private", text, quote)
    packet["candidate"]["claims"][-1] = claim("answer", "STATE", quote, i, negative=negative,
        time=kind, expression=expression, source="snapshot-answer", predicate=predicate)
    req, cp, out = generate(req, fresh(req, packet, cp.semantic_snapshot))
    assert out.artifact is not None, out.reason_codes
    assert ("少し嬉しくない" if negative else "本当は嬉しかった") in out.artifact.text
    if expression + "も" in quote:
        assert expression + "も" in out.artifact.text
    assert "では現在は" not in out.artifact.text and "その時は当時は" not in out.artifact.text
    prepared = prepare_snapshot_meaning(req, SemanticInput("RESUME_ADOPTED", snapshot_json=cp.semantic_snapshot))
    assert prepared.accepted_nuclei[-1].semantic_frame.polarity == ("negative" if negative else "positive")


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

# The second offline profile has a distinct namespace. Original P2 is frozen;
# it is never relabelled as model output or substituted for the old fixtures.
from cocolon_meaning_experience_engine.emlis_semantic_admission import (
    PROFILE_V2, CHECKPOINT_SCHEMA_V3, snapshot_resolver, _semantic_ref, _json)
from cocolon_meaning_experience_engine.contracts import GenerationRequest
from emlis_ai_current_input_bundle import build_emlis_current_input_bundle
from cocolon_meaning_experience_engine.source_kernel import freeze_text_source
from cocolon_meaning_experience_engine.emlis_thread_contracts import EmlisThreadInputV1
from cocolon_meaning_experience_engine.emlis_thread_projection import project_thread_meaning

V2_FIXTURE = json.loads((Path(__file__).parent / 'fixtures/cmee_emlis_semantic_targeted_unknown_action_v2.json').read_text())


def e02_case(*, mixed=False, withdraw=False):
    raw, packet = copy.deepcopy(V2_FIXTURE['original']), copy.deepcopy(V2_FIXTURE['packet'])
    if mixed:
        prefix = '褒められたのに、嬉しくなかった。'
        raw['memo'] = prefix + raw['memo']
        for e in packet['evidence']:
            if e['field_path'] == 'memo': e['start'] += len(prefix); e['end'] += len(prefix)
        index = len(packet['evidence'])
        packet['evidence'] += [evidence(raw['id'], 'memo', raw['memo'], q) for q in ('褒められた','嬉しくなかった','のに')]
        packet['candidate']['claims'][:0] = [claim('event','EVENT','褒められた',index),
            claim('reaction','STATE','嬉しくなかった',index+1,negative=True)]
        packet['candidate']['relations'].insert(0, dict(relation_id='contrast',type='SOURCE_WRITTEN_CONCESSION',
            from_claim_id='event',to_claim_id='reaction',polarity='AFFIRMED',scope_refs=['contrast'],qualifiers=[],evidence_indexes=[index+2]))
    if withdraw:
        raw['memo_action'] += '帰宅しても苦しかった。'
        index = len(packet['evidence'])
        packet['evidence'].append(evidence(raw['id'],'memo_action',raw['memo_action'],'帰宅しても苦しかった'))
        packet['candidate']['claims'].append(claim('other','STATE','帰宅しても苦しかった',index,predicate='苦しかった'))
    req=GenerationRequest('offline-trial-E02-0',build_emlis_current_input_bundle(raw),raw['id'])
    src=freeze_text_source(req)
    return replace(req,emlis_thread=EmlisThreadInputV1('offline-thread-'+raw['id'],src.envelope.envelope_id,
        capability_snapshot='Q3_FREE',question_control_context=EmlisQuestionControlV1(question_limit=1))),packet


def fresh_v2(req, packet, prior=None):
    return SemanticInput('FRESH_CANDIDATE',receipt(req,packet),prior_snapshot_json=prior,semantic_profile=PROFILE_V2)


def resume_v2(snapshot):
    return SemanticInput('RESUME_ADOPTED',snapshot_json=snapshot,semantic_profile=PROFILE_V2)


def generate_v2(req, semantic):
    cp=MeaningExperienceEngine().prepare_emlis_update(req,semantic_input=semantic)
    req=replace(req,emlis_thread=replace(req.emlis_thread,prepared_meaning_checkpoint_ref=cp.checkpoint_id))
    return req,cp,MeaningExperienceEngine().generate(req,semantic_input=resume_v2(cp.semantic_snapshot))


def test_v2_original_e02_full_body_typed_targets_and_replay():
    req, packet=e02_case()
    assert prepare_emlis(req).request_id == 'prep-b9e74c65cdf2eaac838906c19e661d18ee980855c5bda172bd7a520997869763'
    req,cp,out=generate_v2(req,fresh_v2(req,packet))
    assert cp.semantic_schema_version == CHECKPOINT_SCHEMA_V3
    assert out.artifact is not None, out.reason_codes
    assert out.question is None
    p=json.loads(cp.semantic_snapshot)
    assert p['packet']==packet and p['semantic_profile']==PROFILE_V2 and p['adapter_version']=='1'
    b=p['native_bindings']; u,=b['person_stated_unknowns']
    assert u['target_nucleus_refs']==[p['claim_mapping']['e0.joy']]
    assert u['statement_nucleus_ref']==p['claim_mapping']['e0.unclear']
    assert (u['statement_time_scope'],u['target_time_scope'])==('present','past')
    assert [a['written_role'] for a in b['case_arguments']]==['WRITTEN_で','WRITTEN_に','WRITTEN_を','WRITTEN_まで']
    assert all(s['subject_binding']=='OMITTED' and s['source_entity'] is None for s in b['source_slices'])
    listen=next(s for s in b['source_slices'] if s['claim_ref']=='e0.listen')
    assert (listen['raw_field_start'],listen['raw_field_end'],listen['lexical_start'],listen['lexical_end'])==(14,22,14,21)
    prepared=prepare_snapshot_meaning(req,resume_v2(cp.semantic_snapshot));plan=derive_snapshot_plan(prepared)
    projection=project_thread_meaning(prepared,plan)
    ids=[p['claim_mapping'][c] for c in ('e0.delegate','e0.listen')]
    assert ids[0]!=ids[1] and projection.binding.nucleus_to_node[ids[0]]!=projection.binding.nucleus_to_node[ids[1]]
    assert all(word in out.artifact.text for word in ('打合せで','後輩に','説明を任せて','最後まで聞いた','うれしかった','まだ曖昧'))
    assert all(word not in out.artifact.text for word in ('信頼','成長','同時','この順','だから'))
    from cocolon_meaning_experience_engine.contracts import SnapshotBindingConsumptionV2, source_explicit_epistemic_unknown_object_ref
    for trace,section,text in ((out.artifact.meaning_trace,'OBSERVATION',out.artifact.observation),
                               (out.artifact.reception_trace,'RECEPTION',out.artifact.reception)):
        consumed=tuple(t for t in trace if type(t) is SnapshotBindingConsumptionV2)
        assert len(consumed)==17
        assert {t.binding_kind for t in consumed}=={'SOURCE_SLICE','WRITTEN_CASE','PERSON_STATED_UNKNOWN','WRITTEN_LINK'}
        assert all(t.section==section and text[t.visible_scalar_start:t.visible_scalar_end] and t.graph_node_refs for t in consumed)
    unknown_owner=next(d for d in projection.graph.owner_dispositions if d.target_unknown_ref)
    assert source_explicit_epistemic_unknown_object_ref(projection.premeaning,unknown_owner) is not None
    assert MeaningExperienceEngine().generate(req,semantic_input=resume_v2(cp.semantic_snapshot))==out


@pytest.mark.parametrize('text,operation,withdraw',[
    ('今は嬉しい。','ADD',False),
    ('あの時も本当は嬉しかった。書き方を間違えた。','REVISE',False),
    ('その時は寂しかった。「帰宅しても苦しかった」は誤りです。','ADD',True)])
def test_v2_actual_pending_preserves_new_sources(text,operation,withdraw):
    req,packet=e02_case(mixed=True,withdraw=withdraw)
    req,before,first=generate_v2(req,fresh_v2(req,packet))
    assert first.artifact is not None,first.reason_codes
    assert first.question is not None
    req=answered(req,first,text)
    req=replace(req,emlis_thread=replace(req.emlis_thread,question_control_context=replace(
        req.emlis_thread.question_control_context,issued_questions=(first.question,))))
    updated=answer_packet(req,before.semantic_snapshot,operation=operation,withdraw=withdraw)
    if operation=='REVISE':
        updated['candidate']['relations']=[r for r in packet['candidate']['relations'] if 'reaction' not in (r['from_claim_id'],r['to_claim_id'])]
    req,cp,out=generate_v2(req,fresh_v2(req,updated,before.semantic_snapshot))
    assert out.artifact is not None,out.reason_codes
    b,a=json.loads(before.semantic_snapshot),json.loads(cp.semantic_snapshot)
    assert b['native_bindings']==a['native_bindings']
    assert a['prior_snapshot']==b
    for cid in ('e0.joy','e0.unclear','e0.delegate','e0.listen'):
        assert a['claim_mapping'][cid]==b['claim_mapping'][cid]
    assert '説明を任せて' in out.artifact.text and '最後まで聞いた' in out.artifact.text and 'まだ曖昧' in out.artifact.text
    assert MeaningExperienceEngine().generate(req,semantic_input=resume_v2(cp.semantic_snapshot))==out


@pytest.mark.parametrize('mutation', ['target','case','te','unknown','predicate_extra'])
def test_v2_candidate_closed_boundaries(mutation):
    req,packet=e02_case()
    c=packet['candidate']
    if mutation=='target': c['unknowns'][0]['target_claim_refs']=['e0.listen']
    if mutation=='case': c['claims'][2]['predicate']['arguments'][1]['role']='RECIPIENT'
    if mutation=='te': c['relations'][0]['type']='ACTION_BEFORE_AFTER'
    if mutation=='unknown': c['unknowns'][0]['dimension']='REASON'
    if mutation=='predicate_extra': c['claims'][2]['predicate']['extra']='trust'
    with pytest.raises(SemanticNotAdopted):
        prepare_snapshot_meaning(req,fresh_v2(req,packet))


@pytest.mark.parametrize('mutation', ['target','slice','adapter','schema','profile'])
def test_v2_canonical_rehash_does_not_authorize_changed_bindings(mutation):
    req,packet=e02_case();prepared=prepare_snapshot_meaning(req,fresh_v2(req,packet))
    p=json.loads(prepared.semantic_snapshot)
    if mutation=='target': p['native_bindings']['person_stated_unknowns'][0]['target_nucleus_refs']=[p['claim_mapping']['e0.listen']]
    if mutation=='slice': p['native_bindings']['source_slices'][0]['lexical_end']-=1
    if mutation=='adapter': p['adapter_version']='2'
    if mutation=='schema': p['schema_version']='cocolon.cmee.emlis_semantic_snapshot.v1'
    if mutation=='profile': p['semantic_profile']=PROFILE
    p['snapshot_ref']=_semantic_ref(p)
    with pytest.raises(SemanticNotAdopted):
        prepare_snapshot_meaning(req,resume_v2(_json(p)))


@pytest.mark.parametrize('target',['e0.joy','e0.unclear','e0.delegate','e0.listen'])
def test_v2_new_elements_cannot_be_answer_update_targets(target):
    req,packet=e02_case(mixed=True);req,cp,first=generate_v2(req,fresh_v2(req,packet))
    req=answered(req,first,'今は嬉しい。')
    req=replace(req,emlis_thread=replace(req.emlis_thread,question_control_context=replace(
        req.emlis_thread.question_control_context,issued_questions=(first.question,))))
    packet=answer_packet(req,cp.semantic_snapshot)
    packet['candidate']['updates'][0]['target_claim_refs']=[target]
    with pytest.raises(SemanticNotAdopted) as exc:
        prepare_snapshot_meaning(req,fresh_v2(req,packet,cp.semantic_snapshot))
    assert exc.value.decision=='HOLD' and exc.value.reason_code=='semantic_v2_target_update_unsupported'


@pytest.mark.parametrize('before,after',[
    ('後輩に','後輩が'),('説明を任せて','説明を任せたので'),('最後まで聞いた','聞いた'),
    ('説明を任せて、最後まで聞いた','最後まで聞いた、説明を任せて'),
    ('うれしかった一方で','うれしくなかった一方で'),
    ('どこがうれしかったかはまだ曖昧','うれしかったかどうかはまだ曖昧'),
    ('その打合せでの関わり方','後輩を信頼したこと'),('どの部分かまだ曖昧','喜びの原因がまだ曖昧')])
def test_v2_body_inverse_rejects_changed_arguments_targets_and_both_actions(before,after):
    from emlis_ai_grounded_sentence_surface import build_grounded_sentence_plan
    from emlis_ai_grounded_observation_gate import evaluate_grounded_surface_body_inverse
    req,packet=e02_case();req,cp,out=generate_v2(req,fresh_v2(req,packet))
    prepared=prepare_snapshot_meaning(req,resume_v2(cp.semantic_snapshot));plan=derive_snapshot_plan(prepared)
    projection=project_thread_meaning(prepared,plan);resolver=snapshot_resolver(prepared)
    sentence=build_grounded_sentence_plan(plan,resolver,recovery_stage='full')
    body=out.artifact.text
    assert before in body
    bad=evaluate_grounded_surface_body_inverse(body=body.replace(before,after).encode(),plan=plan,
        sentence_plan=sentence,resolver=resolver,selected_subjective_input=projection.selected_reception)
    assert not bad.passed


def offline_service_v2(case,db,*,unsupported=False):
    user,parent,old=case
    _,packet=e02_case(mixed=True)
    raw=V2_FIXTURE['original']
    db.query('update public.emotions set memo=$1,memo_action=$2 where id=$3',
        ['褒められたのに、嬉しくなかった。'+raw['memo'],raw['memo_action'],parent])
    calls=[]
    def source(req,prior):
        calls.append(bool(prior))
        value=answer_packet(req,prior) if prior else copy.deepcopy(packet)
        if prior and unsupported:
            value['candidate']['updates'][0]['target_claim_refs']=['e0.delegate']
        for e in value['evidence']:
            if e['source_id']=='E02-O': e['source_id']=parent
        return receipt(req,value)
    return user,parent,EmlisThreadService(store=old.store,runtime_profile=Q3_PROFILE,semantic_profile=PROFILE_V2,offline_candidate_source=source),calls


def test_v2_actual_sql_save_interruption_retry_and_read_only_restart(qcase,qdb,monkeypatch):
    user,parent,service,calls=offline_service_v2(qcase,qdb)
    first=run(service.start(user,parent));assert first['pending_question'],first
    old_generate=service.engine.generate
    def interrupt(*args,**kwargs): raise asyncio.CancelledError()
    monkeypatch.setattr(service.engine,'generate',interrupt)
    with pytest.raises(asyncio.CancelledError): run(answer(service,user,first,'今は嬉しい。'))
    broken=run(service.get(user,parent));assert broken['can_retry'],broken
    saved=run(service.store.read(user,input_id=parent));before=[e['id'] for e in saved['events'] if e['kind']=='MEANING_UPDATE']
    assert len(before)==2
    monkeypatch.setattr(service.engine,'generate',old_generate)
    def never(*a,**k): raise AssertionError('must not reacquire or author saved DTO')
    service.offline_candidate_source=never
    done=run(service.action(user,broken['thread_id'],action='retry_response',expected_revision=broken['revision'],
        idempotency_key='snapshot-v2-retry',operation_id=broken['operation_id']))
    assert done['body_state']=='REFINED',done
    assert '最後まで聞いた' in done['current_observation']['text']
    saved=run(service.store.read(user,input_id=parent));assert before==[e['id'] for e in saved['events'] if e['kind']=='MEANING_UPDATE']
    assert calls==[False,True]
    class NoAuthor:
        def __getattr__(self,name): return never
    restarted=EmlisThreadService(store=service.store,engine=NoAuthor())
    read=run(restarted.get(user,parent))
    assert not read["can_write"]
    assert {k:v for k,v in read.items() if k!="can_write"}=={k:v for k,v in done.items() if k!="can_write"}


def test_v2_unsupported_answer_preserves_private_evaluation_without_current_old_body(qcase,qdb):
    user,parent,service,calls=offline_service_v2(qcase,qdb,unsupported=True)
    first=run(service.start(user,parent));done=run(answer(service,user,first,'今は嬉しい。'))
    assert done['body_state']=='ANSWER_UNREFLECTED' and done['current_observation'] is None,done
    saved=run(service.store.read(user,input_id=parent))
    assert len([e for e in saved['events'] if e['kind']=='MEANING_UPDATE'])==1
    assert any(e['payload'].get('stage')=='SEMANTIC_NOT_ADOPTED' for e in saved['events'] if e['kind']=='OPERATION')
    assert run(service.get(user,parent))==done and calls==[False,True]


def test_v2_period_permission_does_not_allow_crossing_native_sentences():
    from cocolon_meaning_experience_engine.emlis_semantic_admission import _locate_v2
    from cocolon_meaning_experience_engine.emlis_thread_source import admit_emlis_thread
    req,_=e02_case(withdraw=True)
    raw=req.current_input_bundle.raw_current_input
    quote=raw['memo_action']
    ev=dict(source_id=raw['id'],field_path='memo_action',start=0,end=len(quote),quote=quote)
    with pytest.raises(SemanticNotAdopted) as exc:
        _locate_v2(admit_emlis_thread(req),prepare_emlis(req),[ev])
    assert exc.value.reason_code=='semantic_subrange_crosses_native_span'


@pytest.mark.parametrize('mutation',['statement_past','joy_present','duplicate_mapping'])
def test_v2_unknown_carrier_checks_exact_axes_and_graph_mapping(mutation):
    from cocolon_meaning_experience_engine.contracts import SnapshotSourceQualifierRowV2, source_explicit_epistemic_unknown_object_ref
    req,packet=e02_case();prepared=prepare_snapshot_meaning(req,fresh_v2(req,packet));plan=derive_snapshot_plan(prepared)
    projection=project_thread_meaning(prepared,plan);pre=projection.premeaning
    disposition=next(d for d in projection.graph.owner_dispositions if d.target_unknown_ref)
    assert source_explicit_epistemic_unknown_object_ref(pre,disposition)
    mapping=json.loads(prepared.semantic_snapshot)['claim_mapping']
    target=projection.binding.nucleus_to_node[mapping['e0.joy' if mutation=='joy_present' else 'e0.unclear']]
    qualifiers=[]
    for row in pre.source_qualifier_rows:
        if type(row) is SnapshotSourceQualifierRowV2 and target in row.node_ref:
            row=replace(row,nucleus_node_bindings=(*row.nucleus_node_bindings,row.nucleus_node_bindings[0])) if mutation=='duplicate_mapping' else replace(
                row,qualifier_refs=(*row.qualifier_refs,'time_scope:present' if mutation=='joy_present' else 'time_scope:past'))
        qualifiers.append(row)
    bad=replace(pre,source_qualifier_rows=tuple(qualifiers))
    assert source_explicit_epistemic_unknown_object_ref(bad,disposition) is None


@pytest.mark.parametrize('mutation',['marker','scope','relation'])
def test_v2_te_scope_requires_actual_link_and_marker(mutation):
    from cocolon_meaning_experience_engine.contracts import SnapshotSourceQualifierRowV2,EmlisThreadScopeRelationKind
    from cocolon_meaning_experience_engine.emlis_input_specific_meaning import _thread_scope_relation_source_is_bound
    req,packet=e02_case();prepared=prepare_snapshot_meaning(req,fresh_v2(req,packet));plan=derive_snapshot_plan(prepared)
    pre=project_thread_meaning(prepared,plan).premeaning
    link=next(r for r in pre.source_relation_rows if r.relation_kind is EmlisThreadScopeRelationKind.WRITTEN_TE_LINK)
    assert _thread_scope_relation_source_is_bound(link,pre)
    qualifiers=[]
    for row in pre.source_qualifier_rows:
        if type(row) is SnapshotSourceQualifierRowV2:
            links=tuple(replace(w,**({'marker_slice_refs':()} if mutation=='marker' else
                {'scope_refs':()} if mutation=='scope' else {'relation_ref':'semantic-relation-unbound'}))
                if w.source_type=='SOURCE_WRITTEN_TE_LINK' else w for w in row.written_links)
            row=replace(row,written_links=links)
        qualifiers.append(row)
    assert not _thread_scope_relation_source_is_bound(link,replace(pre,source_qualifier_rows=tuple(qualifiers)))
