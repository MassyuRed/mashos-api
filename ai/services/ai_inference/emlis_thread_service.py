"""Q2: authenticated application orchestration around the unchanged Q1 author.

Only persisted artifacts are returned. Answers, meaning and body are separate
commits. GET never evaluates an answer or starts work. Q3 history/rounds are not
admitted: all tiers currently use the same Free source scope and one question.
"""
from __future__ import annotations

import asyncio
import base64
import copy
import json
from dataclasses import asdict, is_dataclass, replace
from datetime import datetime, timedelta, timezone
from enum import Enum
from uuid import uuid4

from emlis_ai_current_input_bundle import build_emlis_current_input_bundle
from publish_governance import parse_iso_utc, timestamp_in_history_retention
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.contracts import GenerationRequest, EngineStatus
from cocolon_meaning_experience_engine.source_kernel import freeze_text_source
from cocolon_meaning_experience_engine.emlis_thread_source import admit_emlis_thread, identity
from cocolon_meaning_experience_engine.emlis_thread_contracts import (
    EmlisThreadInputV1, EmlisQuestionControlV1, EmlisClarificationV1,
    EmlisQuestionDecisionV1, SupplementalAnswerSource, SEMANTIC_SCHEMA,
)
from emlis_thread_store import EmlisThreadStore, ThreadStoreError
from emlis_thread_config import APPLICATION_EXECUTION_MODE, MAX_ANSWER_CHARS, development_enabled

ATTEMPT_SECONDS = 30
DTO_SCHEMA = "cocolon.emlis_thread.application.v1"
RUNTIME_PROFILE = "q2.free.one_round.v1"
Q3_PROFILE = "q3.plan.sequential.v1"

def question_limit(t, tier):
    started = t.get("started_question_limit", 1)
    return min(started, 3 if tier == "premium" else 1)
RETRYABLE_FAILURES = {"storage_temporarily_unavailable", "worker_interrupted"}


def _json(value):
    def encode(obj):
        if is_dataclass(obj):
            return asdict(obj)
        if isinstance(obj, Enum):
            return obj.value
        if isinstance(obj, bytes):
            return {"encoding": "base64", "value": base64.b64encode(obj).decode("ascii")}
        raise TypeError("unsupported_private_artifact_type")
    return json.loads(json.dumps(value, default=encode, ensure_ascii=False))


def _now(snapshot):
    return parse_iso_utc(snapshot["now"])


def _event(kind, payload, thread, *, key=None, question_id=None, event_id=None):
    return {"id": event_id or str(uuid4()), "kind": kind,
        "round_index": thread.get("issued_count", 0) + (1 if kind == "QUESTION" else 0),
        "question_id": question_id, "operation_id": thread.get("active_operation_id"),
        "attempt_id": thread.get("active_attempt_id"), "idempotency_key": key, "payload": _json(payload)}


def _find(snapshot, event_id):
    return next((e for e in snapshot["events"] if e["id"] == event_id), None)


def _request(snapshot, *, checkpoint_ref=None, include_context=True):
    t, original = snapshot["thread"], dict(snapshot["original"])
    original["created_at"] = parse_iso_utc(original["created_at"]).isoformat()
    req = GenerationRequest("emlis-" + t["id"], build_emlis_current_input_bundle(original), original["id"])
    ref = freeze_text_source(req).envelope.envelope_id
    if t["data"].get("original_source_ref", ref) != ref:
        raise ValueError("original_source_changed")
    question_events = [e for e in snapshot["events"] if e["kind"] == "QUESTION"]
    question, asked, questions = None, (), []
    for question_event in question_events:
        q = dict(question_event["payload"])
        d = dict(q.pop("decision"))
        for field in ("supporting_evidence_refs", "affected_meaning_refs", "affected_reception_refs", "asked_target_refs"):
            d[field] = tuple(d[field])
        question = EmlisClarificationV1(decision=EmlisQuestionDecisionV1(**d), **q)
        questions.append(question)
        asked = (*asked, question.decision.target_ref)
    answers = tuple(SupplementalAnswerSource(**e["payload"]["source"])
                    for e in snapshot["events"] if e["kind"] == "ANSWER")
    q3 = t["data"]["runtime_profile"] == Q3_PROFILE
    control = EmlisQuestionControlV1(question, asked, t["issued_count"],
        issued_questions=tuple(questions) if q3 else (), question_limit=question_limit(t, snapshot["tier"]))
    history = []
    if q3 and include_context:
        from cocolon_meaning_experience_engine.emlis_thread_history import OwnedHistorySourceV1
        rows = {tuple(h["guard"]):h for h in snapshot.get("context", {}).get("history", [])}
        for guard in t["data"].get("context_guards", []):
            h = rows.get(tuple(guard))
            if h is None:
                raise ValueError("history_source_changed")
            ht = h["thread"] or {"id":"history-"+h["original"]["id"], "issued_count":0,
                "data":{"runtime_profile":Q3_PROFILE}, "started_question_limit":1}
            past = _request({"thread":ht,"original":h["original"],"events":h["events"],"tier":"free"}, include_context=False)
            history.append(OwnedHistorySourceV1(past, h["original"]["created_at"], tuple(guard)))
    rejected = tuple(sorted(f["frame_key"] for f in snapshot.get("context", {}).get("feedback", [])
                            if f["status"] == "REJECTED")) if q3 else ()
    from cocolon_meaning_experience_engine.emlis_thread_history import FrameFeedbackSourceV1
    feedback_sources = tuple(FrameFeedbackSourceV1(**{k:f[k] for k in ("frame_key","frame_ref","source_emotion_id","status","correction_text","version","updated_at")})
        for f in snapshot.get("context",{}).get("feedback",[])) if q3 and include_context else ()
    return replace(req, emlis_thread=EmlisThreadInputV1(t["id"], ref, answers=answers,
        current_round=len(answers), question_control_context=control, admitted_history=tuple(history),
        rejected_frame_keys=rejected, frame_feedback_sources=feedback_sources,
        capability_snapshot="Q3_" + snapshot["tier"].upper() if q3 else "FREE_Q1",
        prepared_meaning_checkpoint_ref=checkpoint_ref))


def _check(snapshot):
    t = snapshot.get("thread")
    if not timestamp_in_history_retention(snapshot["original"]["created_at"], snapshot["tier"], _now(snapshot)):
        raise ThreadStoreError("thread_unavailable", 404)
    if t and (t["source_snapshot"] != snapshot["original"] or t["data"]["runtime_profile"] not in {RUNTIME_PROFILE, Q3_PROFILE}):
        raise ThreadStoreError("thread_source_or_contract_changed", 409)
    return t


def _context_current(snapshot, guards=None):
    t = snapshot.get("thread")
    if not t or t["data"].get("runtime_profile") != Q3_PROFILE:
        return True
    guards = guards if guards is not None else t["data"].get("context_guards", [])
    limit = 6 if snapshot["tier"] == "premium" else 3 if snapshot["tier"] == "plus" else 0
    live = {tuple(h["guard"]) for h in snapshot.get("context", {}).get("history", [])}
    return len(guards) <= limit and all(tuple(g) in live for g in guards)


def _generation_current(snapshot):
    t = snapshot.get("thread")
    if not t or t["data"].get("runtime_profile") != Q3_PROFILE:
        return True
    feedback = [[f["frame_key"], f["version"]] for f in snapshot.get("context", {}).get("feedback", [])]
    return (_context_current(snapshot) and t["data"].get("evaluated_tier",snapshot["tier"]) == snapshot["tier"]
            and t["data"].get("context_feedback",[]) == feedback)


def _context_ref(snapshot):
    return identity("context", snapshot["tier"], snapshot["thread"]["data"].get("context_guards", []),
                    snapshot["thread"]["data"].get("context_feedback", []))


def _observation_text(snapshot, payload):
    artifact = payload.get("artifact", {})
    if artifact.get("history_line") and not _context_current(snapshot, payload.get("context_guards", [])):
        return f"見えたこと：\n{artifact['observation']}\n\nEmlisから：\n{artifact['reception']}"
    return payload["text"]


def _public_frames(snapshot):
    t = snapshot.get("thread")
    if not t or snapshot["tier"] != "premium" or t["data"].get("runtime_profile") != Q3_PROFILE:
        return []
    body = _find(snapshot,t.get("last_observation_event_id"))
    if not body or not _context_current(snapshot,body["payload"].get("context_guards",[])):
        return []
    feedback = {f["frame_key"]:f for f in snapshot.get("context",{}).get("feedback",[])}
    rows = body["payload"].get("artifact",{}).get("interpretive_frames",[]) if body else []
    return [{**{k:row[k] for k in ("frame_key","frame_ref","trigger","received_meaning","input_id","recorded_at")},
        "frame_ref":identity("frame-view",row["frame_ref"],feedback[row["frame_key"]]["version"]) if row["frame_key"] in feedback else row["frame_ref"],
        "status":feedback.get(row["frame_key"],{}).get("status","TENTATIVE"),
        "correction_text":feedback.get(row["frame_key"],{}).get("correction_text")} for row in rows]


def thread_dto(snapshot, *, requested_attempt_id=None):
    t = _check(snapshot)
    original = {k: snapshot["original"].get(k) for k in ("id", "created_at", "memo", "memo_action")}
    if not t:
        return {"schema_version": DTO_SCHEMA, "state": "NOT_CREATED", "original": original,
                "thread_id": None, "timeline": [], "can_retry": False}
    d = t["data"]
    expired = bool(t["active_attempt_id"] and parse_iso_utc(t["processing_deadline_at"]) <= _now(snapshot))
    state = "RESPONSE_FAILED" if expired else t["state"]
    body_state = d.get("body_state", "UNAVAILABLE")
    current = _find(snapshot, t.get("last_observation_event_id")) if body_state in {
        "PRE_QUESTION", "FINAL", "REFINED", "PARTIALLY_REFINED", "UNCHANGED"} else None
    if current and not _generation_current(snapshot):
        current = None
        body_state = "CONTEXT_CHANGED"
    timeline = []
    for event in snapshot["events"]:
        p = event["payload"]
        common = {"event_id": event["id"], "kind": event["kind"], "recorded_at": event.get("recorded_at"),
                  "round_index": event["round_index"]}
        if event["kind"] == "OBSERVATION":
            timeline.append({**common, "text": _observation_text(snapshot,p), "stage": p["stage"],
                "is_current": bool(current and current["id"] == event["id"])})
        elif event["kind"] == "QUESTION":
            timeline.append({**common, "question_id": event["question_id"], "text": p["prompt_private"]})
        elif event["kind"] == "ANSWER":
            timeline.append({**common, "text": p["source"]["answer_text_private"], "question_id": event["question_id"],
                "authored_at": p["source"]["authored_at"]})
    q = next((e for e in reversed(timeline) if e["kind"] == "QUESTION"), None)
    failure = "save_result_unknown" if expired else d.get("failure_code")
    return {"schema_version": DTO_SCHEMA, "thread_id": t["id"], "revision": t["revision"],
        "state": state, "original": original, "timeline": timeline,
        "pending_question": q if state == "AWAITING_ANSWER" else None,
        "current_observation": {"event_id": current["id"], "text": _observation_text(snapshot,current["payload"])} if current else None,
        "body_state": body_state, "answer_saved": bool(t.get("latest_answer_event_id")),
        "answer_assessment": d.get("answer_assessment", "NOT_APPLICABLE"),
        "meaning_updated": d.get("meaning_updated", False),
        "failure_code": failure,
        "operation_id": t.get("active_operation_id") or d.get("operation_id"),
        "attempt_id": t.get("active_attempt_id") or d.get("attempt_id"),
        "requested_attempt_id": requested_attempt_id,
        "can_retry": bool(state == "RESPONSE_FAILED" and not expired and failure in RETRYABLE_FAILURES and _generation_current(snapshot)),
        "can_continue": bool(state == "AWAITING_CONTINUE" and d.get("continuation_question")
            and t["issued_count"] < question_limit(t, snapshot["tier"]) and _generation_current(snapshot)),
        "issued_count": t["issued_count"], "question_limit": question_limit(t, snapshot["tier"]),
        "started_question_limit": t.get("started_question_limit", 1),
        "processing_deadline_at": t.get("processing_deadline_at"),
        **({"interpretive_frames":_public_frames(snapshot)} if d["runtime_profile"] == Q3_PROFILE else {})}


class EmlisThreadService:
    def __init__(self, store=None, engine=None, *, runtime_profile=RUNTIME_PROFILE):
        if runtime_profile not in {RUNTIME_PROFILE, Q3_PROFILE}:
            raise ValueError("unsupported_thread_profile")
        self.runtime_profile = runtime_profile
        self.store = store or EmlisThreadStore()
        self.engine = engine or MeaningExperienceEngine()

    async def get(self, user_id, input_id):
        snapshot = await self._hydrate(user_id, await self.store.read(user_id, input_id=input_id))
        return thread_dto(snapshot)

    async def _hydrate(self, user_id, snapshot, *, fresh=False):
        snapshot = copy.deepcopy(snapshot)
        t = snapshot.get("thread")
        if (t["data"].get("runtime_profile") if t else self.runtime_profile) != Q3_PROFILE:
            return snapshot
        context = await self.store.context(user_id, snapshot["original"]["id"])
        snapshot["context"] = context
        if t and fresh:
            t["data"]["context_guards"] = [h["guard"] for h in context["history"]]
            t["data"]["context_feedback"] = [[f["frame_key"],f["version"]] for f in context["feedback"]]
        return snapshot

    async def _commit(self, user_id, snapshot, next_state, events, **kwargs):
        result = await self.store.commit(user_id, snapshot, next_state, events, **kwargs)
        return {**result, **({"context":snapshot["context"]} if "context" in snapshot else {})}


    async def start(self, user_id, input_id):
        snapshot = await self._hydrate(user_id, await self.store.read(user_id, input_id=input_id))
        if _check(snapshot):
            return thread_dto(snapshot)
        t = {"id": str(uuid4()), "state": "INITIALIZING", "issued_count": 0,
            "started_question_limit": 3 if self.runtime_profile == Q3_PROFILE and snapshot["tier"] == "premium" else 1,
            "data": {"runtime_profile": self.runtime_profile, "execution_mode": APPLICATION_EXECUTION_MODE,
                     "started_tier": snapshot["tier"],
                     "body_state": "UNAVAILABLE", "answer_assessment": "NOT_APPLICABLE"}}
        self._begin(t, snapshot)
        if self.runtime_profile == Q3_PROFILE:
            t["data"].update(context_guards=[h["guard"] for h in snapshot["context"]["history"]],
                context_feedback=[[f["frame_key"],f["version"]] for f in snapshot["context"]["feedback"]])
        initial = {**snapshot, "thread": t}
        req = _request(initial)
        t["data"]["original_source_ref"] = req.emlis_thread.original_source_ref
        t["source_prefix_ref"] = admit_emlis_thread(req).source_prefix_ref
        event = _event("OPERATION", {"status": "RUNNING", "stage": "INITIAL"}, t, key="initial")
        try:
            snapshot = await self._commit(user_id, snapshot, t, [event])
        except ThreadStoreError as exc:
            if exc.status == 409:
                fresh = await self._hydrate(user_id, await self.store.read(user_id, input_id=input_id))
                if _check(fresh):
                    return thread_dto(fresh)
            raise
        return await self._process(user_id, snapshot)

    @staticmethod
    def _begin(t, snapshot, operation_id=None):
        t["active_operation_id"] = operation_id or str(uuid4())
        t["active_attempt_id"] = str(uuid4())
        t["processing_deadline_at"] = (_now(snapshot) + timedelta(seconds=ATTEMPT_SECONDS)).isoformat()
        t["data"].update(failure_code=None, operation_id=t["active_operation_id"], attempt_id=t["active_attempt_id"])

    @staticmethod
    def _replay(snapshot, key, fingerprint):
        found = next((e for e in snapshot["events"] if e.get("idempotency_key") == key), None)
        if found:
            if found["payload"].get("request_fingerprint") != fingerprint:
                raise ThreadStoreError("idempotency_conflict", 409)
            dto = thread_dto(snapshot, requested_attempt_id=found["attempt_id"])
            if snapshot["thread"]["data"]["runtime_profile"] == Q3_PROFILE:
                terminal = next((e for e in reversed(snapshot["events"]) if found["attempt_id"] and
                    e["attempt_id"] == found["attempt_id"] and e["kind"] == "OPERATION"), found)
                dto["requested_operation"] = {"idempotency_key":key, "event_id":found["id"],
                    "question_id":found["question_id"], "operation_id":found["operation_id"],
                    "attempt_id":found["attempt_id"], "status":terminal["payload"].get("status",terminal["payload"].get("reason","SAVED"))}
            return dto

    async def answer(self, user_id, thread_id, *, question_id, expected_revision, idempotency_key,
                     answer_text, authored_at=None):
        if not isinstance(answer_text, str) or not answer_text.strip() or len(answer_text) > MAX_ANSWER_CHARS:
            raise ThreadStoreError("answer_invalid", 422)
        snapshot = await self._hydrate(user_id, await self.store.read(user_id, thread_id=thread_id))
        t = _check(snapshot)
        fingerprint = identity("answer-request", question_id, answer_text, authored_at)
        replay = self._replay(snapshot, idempotency_key, fingerprint)
        if replay:
            return replay
        if t["revision"] != expected_revision or t["state"] != "AWAITING_ANSWER":
            raise ThreadStoreError("thread_conflict", 409)
        q = next(e for e in reversed(snapshot["events"]) if e["kind"] == "QUESTION")
        if q["question_id"] != question_id or any(e["kind"] == "ANSWER" and e["question_id"] == question_id for e in snapshot["events"]):
            raise ThreadStoreError("question_conflict", 409)
        snapshot = await self._hydrate(user_id, snapshot, fresh=True)
        t = copy.deepcopy(snapshot["thread"])
        t["state"] = "REFINING"
        self._begin(t, snapshot)
        answer_id = str(uuid4())
        t["latest_answer_event_id"] = answer_id
        source = SupplementalAnswerSource(answer_id, thread_id, question_id, q["round_index"],
            t["data"]["original_source_ref"], answer_text, _now(snapshot).isoformat(), authored_at)
        answer = _event("ANSWER", {"source": source, "request_fingerprint": fingerprint}, t,
                        key=idempotency_key, question_id=question_id, event_id=answer_id)
        t["data"].update(body_state="ANSWER_UNREFLECTED", answer_assessment="PENDING", meaning_updated=False)
        proposed = {**snapshot, "thread": t, "events": snapshot["events"] + [answer]}
        t["source_prefix_ref"] = admit_emlis_thread(_request(proposed)).source_prefix_ref
        operation = _event("OPERATION", {"status": "RUNNING", "stage": "ANSWER"}, t)
        try:
            snapshot = await self._commit(user_id, snapshot, t, [answer, operation])
        except ThreadStoreError as exc:
            if exc.status == 409:
                replay = self._replay(await self._hydrate(user_id, await self.store.read(user_id, thread_id=thread_id)), idempotency_key, fingerprint)
                if replay:
                    return replay
            raise
        return await self._process(user_id, snapshot)

    async def frame_feedback(self,user_id,thread_id,*,frame_ref,status,correction_text,
                             expected_revision,idempotency_key):
        if (status not in {"CONFIRMED","REJECTED","REVISED"} or (status == "REVISED") != bool(correction_text)
                or correction_text is not None and (not isinstance(correction_text,str) or not correction_text.strip() or len(correction_text)>2000)):
            raise ThreadStoreError("frame_feedback_invalid",422)
        snapshot = await self._hydrate(user_id,await self.store.read(user_id,thread_id=thread_id))
        t = _check(snapshot)
        fingerprint = identity("frame-feedback-request",frame_ref,status,correction_text)
        replay = self._replay(snapshot,idempotency_key,fingerprint)
        if replay:
            return replay
        if t["revision"] != expected_revision or t["active_attempt_id"]:
            raise ThreadStoreError("thread_conflict",409)
        frame = next((f for f in _public_frames(snapshot) if f["frame_ref"] == frame_ref),None)
        if frame is None or (status == "CONFIRMED" and frame["status"] in {"REVISED","REJECTED"}):
            raise ThreadStoreError("frame_not_available",409)
        snapshot = await self._hydrate(user_id,snapshot)
        if not _context_current(snapshot) or not any(f["frame_ref"] == frame_ref for f in _public_frames(snapshot)):
            raise ThreadStoreError("frame_source_changed",409)
        t = copy.deepcopy(snapshot["thread"])
        t["data"]["context_feedback"] = [[f["frame_key"],f["version"]] for f in snapshot["context"]["feedback"]]
        t["data"]["frame_feedback_write"] = {"frame_key":frame["frame_key"],"frame_ref":frame_ref,
            "source_emotion_id":frame["input_id"],"status":status,"correction_text":correction_text}
        event = _event("OPERATION",{"status":"FRAME_"+status,"request_fingerprint":fingerprint},t,key=idempotency_key)
        saved = await self._commit(user_id,snapshot,t,[event])
        return thread_dto(await self._hydrate(user_id,saved))

    async def action(self, user_id, thread_id, *, action, expected_revision, idempotency_key,
                     question_id=None, operation_id=None):
        snapshot = await self._hydrate(user_id, await self.store.read(user_id, thread_id=thread_id))
        t = _check(snapshot)
        fingerprint = identity("action-request", action, question_id, operation_id)
        replay = self._replay(snapshot, idempotency_key, fingerprint)
        if replay:
            return replay
        if t["revision"] != expected_revision:
            raise ThreadStoreError("thread_conflict", 409)
        t = copy.deepcopy(t)
        if action in {"skip", "stop"}:
            q = next((e for e in reversed(snapshot["events"]) if e["kind"] == "QUESTION"), None)
            if not (t["state"] == "AWAITING_CONTINUE" and action == "stop") and (
                    t["state"] != "AWAITING_ANSWER" or not q or q["question_id"] != question_id):
                raise ThreadStoreError("question_conflict", 409)
            t["state"] = "COMPLETED"
            if t["data"]["body_state"] == "PRE_QUESTION":
                t["data"]["body_state"] = "FINAL"
            event = _event("TERMINAL", {"reason": action, "request_fingerprint": fingerprint}, t, key=idempotency_key)
            try:
                return thread_dto(await self._commit(user_id, snapshot, t, [event]))
            except ThreadStoreError as exc:
                if exc.status == 409:
                    replay = self._replay(await self._hydrate(user_id, await self.store.read(user_id, thread_id=thread_id)), idempotency_key, fingerprint)
                    if replay:
                        return replay
                raise
        if action == "continue":
            if not thread_dto(snapshot)["can_continue"] or t["data"]["runtime_profile"] != Q3_PROFILE:
                raise ThreadStoreError("continue_not_available", 409)
            if not _generation_current(snapshot) or admit_emlis_thread(_request(snapshot)).source_prefix_ref != t["source_prefix_ref"]:
                raise ThreadStoreError("continue_source_changed",409)
            q = t["data"].pop("continuation_question")
            question = _event("QUESTION", q, t, question_id=q["question_id"])
            t["issued_count"] += 1
            event = _event("OPERATION", {"status": "CONTINUED", "request_fingerprint": fingerprint}, t, key=idempotency_key)
            t["state"] = "AWAITING_ANSWER"
            try:
                return thread_dto(await self._commit(user_id, snapshot, t, [question, event]))
            except ThreadStoreError as exc:
                if exc.status == 409:
                    replay = self._replay(await self._hydrate(user_id, await self.store.read(user_id, thread_id=thread_id)), idempotency_key, fingerprint)
                    if replay:
                        return replay
                raise
        if action != "retry_response" or not thread_dto(snapshot)["can_retry"] or operation_id != t["data"].get("operation_id"):
            raise ThreadStoreError("retry_not_available", 409)
        if not _generation_current(snapshot) or admit_emlis_thread(_request(snapshot)).source_prefix_ref != t["source_prefix_ref"]:
            raise ThreadStoreError("retry_source_changed",409)
        t["state"] = "REFINING" if t.get("latest_answer_event_id") else "INITIALIZING"
        self._begin(t, snapshot, operation_id)
        event = _event("OPERATION", {"status": "RUNNING", "request_fingerprint": fingerprint}, t, key=idempotency_key)
        try:
            snapshot = await self._commit(user_id, snapshot, t, [event])
        except ThreadStoreError as exc:
            if exc.status == 409:
                replay = self._replay(await self._hydrate(user_id, await self.store.read(user_id, thread_id=thread_id)), idempotency_key, fingerprint)
                if replay:
                    return replay
            raise
        return await self._process(user_id, snapshot)

    async def _process(self, user_id, snapshot):
        t, attempt = snapshot["thread"], snapshot["thread"]["active_attempt_id"]
        try:
            checkpoint = _find(snapshot, t.get("current_meaning_event_id"))
            if t.get("evaluated_prefix_ref") != t["source_prefix_ref"]:
                cp = await asyncio.to_thread(self.engine.prepare_emlis_update, _request(snapshot))
                t = copy.deepcopy(t)
                checkpoint = _event("MEANING_UPDATE", cp, t)
                t["current_meaning_event_id"] = checkpoint["id"]
                t["evaluated_prefix_ref"] = cp.source_prefix_ref
                update = cp.answer_update
                t["data"].update(evaluated_tier=snapshot["tier"], answer_assessment=cp.assessment_status if update else "NOT_APPLICABLE",
                    meaning_updated=bool(update and update.updates))
                if update:
                    t["data"]["body_state"] = "MEANING_UPDATED_BODY_UNAVAILABLE" if update.updates else "ANSWER_UNREFLECTED"
                snapshot = await self._commit(user_id, snapshot, t, [checkpoint], finishing_attempt=attempt)
                t = snapshot["thread"]
                checkpoint = _find(snapshot, t["current_meaning_event_id"])
            cp = checkpoint["payload"]
            if cp["semantic_schema_version"] != SEMANTIC_SCHEMA or cp["source_prefix_ref"] != t["source_prefix_ref"]:
                raise ValueError("checkpoint_contract_changed")
            update = cp.get("answer_update")
            if update and update["disposition"] == "NO_MATERIAL_UPDATE":
                previous = _find(snapshot, t.get("last_observation_event_id"))
                valid = previous and (t["data"]["runtime_profile"] == RUNTIME_PROFILE or (
                    previous["payload"].get("effective_plan_ref") == cp["base_meaning_ref"]
                    and previous["payload"].get("context_ref") == _context_ref(snapshot)))
                return await self._finish(user_id, snapshot, body_state="UNCHANGED" if valid else "UNAVAILABLE", state="COMPLETED")
            if update and update["disposition"] == "UNRESOLVED":
                return await self._finish(user_id, snapshot, body_state="ANSWER_UNREFLECTED", state="COMPLETED")
            outcome = await asyncio.to_thread(self.engine.generate, _request(snapshot, checkpoint_ref=cp["checkpoint_id"]))
            if _json(outcome.meaning_checkpoint) != cp:
                raise ValueError("checkpoint_body_mismatch")
            if outcome.artifact is None:
                safety = outcome.status is EngineStatus.SEPARATE_SAFETY
                return await self._finish(user_id, snapshot, body_state=outcome.body_state,
                    state="COMPLETED" if safety else "RESPONSE_FAILED",
                    failure="separate_safety_owner_required" if safety else "body_not_validated")
            artifact = outcome.artifact
            from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning, build_updated_grounded_plan, _base_ref
            prepared = prepare_emlis_meaning(_request(snapshot))
            effective_ref = _base_ref(prepared.thread, build_updated_grounded_plan(prepared))
            observation = _event("OBSERVATION", {"text": artifact.text,
                "effective_plan_ref":effective_ref, "context_guards":t["data"].get("context_guards", []), "context_ref":_context_ref(snapshot),
                "stage": "REFINED" if t.get("latest_answer_event_id") else "INITIAL",
                "meaning_checkpoint_ref": cp["checkpoint_id"], "source_prefix_ref": cp["source_prefix_ref"],
                "artifact": artifact, "meaning_graph": outcome.meaning_graph}, t)
            followup = bool(outcome.question and t.get("latest_answer_event_id"))
            question = _event("QUESTION", outcome.question, t, question_id=outcome.question.question_id) if outcome.question and not followup else None
            if followup:
                snapshot = copy.deepcopy(snapshot)
                snapshot["thread"]["data"]["continuation_question"] = _json(outcome.question)
            return await self._finish(user_id, snapshot, body_state=outcome.body_state,
                state="AWAITING_ANSWER" if question else "AWAITING_CONTINUE" if followup else "COMPLETED", observation=observation, question=question)
        except asyncio.CancelledError:
            # Cancellation confirms the worker stopped before a further commit.
            # Only the active, unexpired attempt may record this fact.
            try:
                await asyncio.shield(self._record_failure(user_id, snapshot, attempt, "worker_interrupted"))
            except Exception:
                pass
            raise
        except ThreadStoreError as exc:
            if exc.transient:
                return await self._record_failure(user_id, snapshot, attempt, exc.code)
            raise
        except ValueError as exc:
            if str(exc) == "separate_safety_owner_required":
                return await self._finish(user_id, snapshot, body_state="ANSWER_UNREFLECTED",
                    state="COMPLETED", failure="separate_safety_owner_required")
            return await self._record_failure(user_id, snapshot, attempt, "meaning_or_body_unavailable")
        except Exception:
            return await self._record_failure(user_id, snapshot, attempt, "meaning_or_body_unavailable")

    async def _record_failure(self, user_id, snapshot, attempt, reason):
        fresh = await self.store.read(user_id, thread_id=snapshot["thread"]["id"])
        _check(fresh)
        if fresh["thread"]["active_attempt_id"] != attempt:
            return thread_dto(await self._hydrate(user_id, fresh))
        await self._finish(user_id, fresh, body_state=fresh["thread"]["data"]["body_state"],
                                  state="RESPONSE_FAILED", failure=reason)
        # Save failure before refreshing optional paid context, so context outages
        # cannot leave an otherwise finished attempt running.
        return await self.get(user_id, fresh["original"]["id"])

    async def _finish(self, user_id, snapshot, *, body_state, state, failure=None, observation=None, question=None):
        t = copy.deepcopy(snapshot["thread"])
        attempt = t["active_attempt_id"]
        events = [e for e in (observation, question) if e]
        if observation:
            t["last_observation_event_id"] = observation["id"]
        if question:
            t["issued_count"] += 1
        events.append(_event("OPERATION", {"status": state, "failure_code": failure}, t))
        t.update(state=state, active_operation_id=None, active_attempt_id=None, processing_deadline_at=None)
        t["data"].update(body_state=body_state, failure_code=failure)
        return thread_dto(await self._commit(user_id, snapshot, t, events, finishing_attempt=attempt))
