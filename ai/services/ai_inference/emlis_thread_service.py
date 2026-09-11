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
        "round_index": 1 if thread.get("latest_answer_event_id") or kind in {"QUESTION", "ANSWER"} else 0,
        "question_id": question_id, "operation_id": thread.get("active_operation_id"),
        "attempt_id": thread.get("active_attempt_id"), "idempotency_key": key, "payload": _json(payload)}


def _find(snapshot, event_id):
    return next((e for e in snapshot["events"] if e["id"] == event_id), None)


def _request(snapshot, *, checkpoint_ref=None):
    t, original = snapshot["thread"], dict(snapshot["original"])
    original["created_at"] = parse_iso_utc(original["created_at"]).isoformat()
    req = GenerationRequest("emlis-" + t["id"], build_emlis_current_input_bundle(original), original["id"])
    ref = freeze_text_source(req).envelope.envelope_id
    if t["data"].get("original_source_ref", ref) != ref:
        raise ValueError("original_source_changed")
    question_event = next((e for e in snapshot["events"] if e["kind"] == "QUESTION"), None)
    question, asked = None, ()
    if question_event:
        q = dict(question_event["payload"])
        d = dict(q.pop("decision"))
        for field in ("supporting_evidence_refs", "affected_meaning_refs", "affected_reception_refs", "asked_target_refs"):
            d[field] = tuple(d[field])
        question = EmlisClarificationV1(decision=EmlisQuestionDecisionV1(**d), **q)
        asked = (question.decision.target_ref,)
    answers = tuple(SupplementalAnswerSource(**e["payload"]["source"])
                    for e in snapshot["events"] if e["kind"] == "ANSWER")
    control = EmlisQuestionControlV1(question, asked, t["issued_count"])
    return replace(req, emlis_thread=EmlisThreadInputV1(t["id"], ref, answers=answers,
        current_round=len(answers), question_control_context=control,
        prepared_meaning_checkpoint_ref=checkpoint_ref))


def _check(snapshot):
    t = snapshot.get("thread")
    if not timestamp_in_history_retention(snapshot["original"]["created_at"], snapshot["tier"], _now(snapshot)):
        raise ThreadStoreError("thread_unavailable", 404)
    if t and (t["source_snapshot"] != snapshot["original"] or t["data"]["runtime_profile"] != RUNTIME_PROFILE):
        raise ThreadStoreError("thread_source_or_contract_changed", 409)
    return t


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
    timeline = []
    for event in snapshot["events"]:
        p = event["payload"]
        common = {"event_id": event["id"], "kind": event["kind"], "recorded_at": event.get("recorded_at")}
        if event["kind"] == "OBSERVATION":
            timeline.append({**common, "text": p["text"], "stage": p["stage"],
                "is_current": bool(current and current["id"] == event["id"])})
        elif event["kind"] == "QUESTION":
            timeline.append({**common, "question_id": event["question_id"], "text": p["prompt_private"]})
        elif event["kind"] == "ANSWER":
            timeline.append({**common, "text": p["source"]["answer_text_private"],
                "authored_at": p["source"]["authored_at"]})
    q = next((e for e in timeline if e["kind"] == "QUESTION"), None)
    failure = "save_result_unknown" if expired else d.get("failure_code")
    return {"schema_version": DTO_SCHEMA, "thread_id": t["id"], "revision": t["revision"],
        "state": state, "original": original, "timeline": timeline,
        "pending_question": q if state == "AWAITING_ANSWER" else None,
        "current_observation": {"event_id": current["id"], "text": current["payload"]["text"]} if current else None,
        "body_state": body_state, "answer_saved": bool(t.get("latest_answer_event_id")),
        "answer_assessment": d.get("answer_assessment", "NOT_APPLICABLE"),
        "meaning_updated": d.get("meaning_updated", False),
        "failure_code": failure,
        "operation_id": t.get("active_operation_id") or d.get("operation_id"),
        "attempt_id": t.get("active_attempt_id") or d.get("attempt_id"),
        "requested_attempt_id": requested_attempt_id,
        "can_retry": bool(state == "RESPONSE_FAILED" and not expired and failure in RETRYABLE_FAILURES),
        "can_continue": False, "issued_count": t["issued_count"], "question_limit": 1,
        "processing_deadline_at": t.get("processing_deadline_at")}


class EmlisThreadService:
    def __init__(self, store=None, engine=None):
        self.store = store or EmlisThreadStore()
        self.engine = engine or MeaningExperienceEngine()

    async def get(self, user_id, input_id):
        return thread_dto(await self.store.read(user_id, input_id=input_id))

    async def start(self, user_id, input_id):
        snapshot = await self.store.read(user_id, input_id=input_id)
        if _check(snapshot):
            return thread_dto(snapshot)
        t = {"id": str(uuid4()), "state": "INITIALIZING", "issued_count": 0,
            "data": {"runtime_profile": RUNTIME_PROFILE, "execution_mode": APPLICATION_EXECUTION_MODE,
                     "started_tier": snapshot["tier"],
                     "body_state": "UNAVAILABLE", "answer_assessment": "NOT_APPLICABLE"}}
        self._begin(t, snapshot)
        initial = {**snapshot, "thread": t}
        req = _request(initial)
        t["data"]["original_source_ref"] = req.emlis_thread.original_source_ref
        t["source_prefix_ref"] = admit_emlis_thread(req).source_prefix_ref
        event = _event("OPERATION", {"status": "RUNNING", "stage": "INITIAL"}, t, key="initial")
        try:
            snapshot = await self.store.commit(user_id, snapshot, t, [event])
        except ThreadStoreError as exc:
            if exc.status == 409:
                fresh = await self.store.read(user_id, input_id=input_id)
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
            return thread_dto(snapshot, requested_attempt_id=found["attempt_id"])

    async def answer(self, user_id, thread_id, *, question_id, expected_revision, idempotency_key,
                     answer_text, authored_at=None):
        if not isinstance(answer_text, str) or not answer_text.strip() or len(answer_text) > MAX_ANSWER_CHARS:
            raise ThreadStoreError("answer_invalid", 422)
        snapshot = await self.store.read(user_id, thread_id=thread_id)
        t = _check(snapshot)
        fingerprint = identity("answer-request", question_id, answer_text, authored_at)
        replay = self._replay(snapshot, idempotency_key, fingerprint)
        if replay:
            return replay
        if t["revision"] != expected_revision or t["state"] != "AWAITING_ANSWER":
            raise ThreadStoreError("thread_conflict", 409)
        q = next(e for e in snapshot["events"] if e["kind"] == "QUESTION")
        if q["question_id"] != question_id or t.get("latest_answer_event_id"):
            raise ThreadStoreError("question_conflict", 409)
        t = copy.deepcopy(t)
        t["state"] = "REFINING"
        self._begin(t, snapshot)
        answer_id = str(uuid4())
        t["latest_answer_event_id"] = answer_id
        source = SupplementalAnswerSource(answer_id, thread_id, question_id, 1,
            t["data"]["original_source_ref"], answer_text, _now(snapshot).isoformat(), authored_at)
        answer = _event("ANSWER", {"source": source, "request_fingerprint": fingerprint}, t,
                        key=idempotency_key, question_id=question_id, event_id=answer_id)
        t["data"].update(body_state="ANSWER_UNREFLECTED", answer_assessment="PENDING", meaning_updated=False)
        proposed = {**snapshot, "thread": t, "events": snapshot["events"] + [answer]}
        t["source_prefix_ref"] = admit_emlis_thread(_request(proposed)).source_prefix_ref
        operation = _event("OPERATION", {"status": "RUNNING", "stage": "ANSWER"}, t)
        try:
            snapshot = await self.store.commit(user_id, snapshot, t, [answer, operation])
        except ThreadStoreError as exc:
            if exc.status == 409:
                replay = self._replay(await self.store.read(user_id, thread_id=thread_id), idempotency_key, fingerprint)
                if replay:
                    return replay
            raise
        return await self._process(user_id, snapshot)

    async def action(self, user_id, thread_id, *, action, expected_revision, idempotency_key,
                     question_id=None, operation_id=None):
        snapshot = await self.store.read(user_id, thread_id=thread_id)
        t = _check(snapshot)
        fingerprint = identity("action-request", action, question_id, operation_id)
        replay = self._replay(snapshot, idempotency_key, fingerprint)
        if replay:
            return replay
        if t["revision"] != expected_revision:
            raise ThreadStoreError("thread_conflict", 409)
        t = copy.deepcopy(t)
        if action in {"skip", "stop"}:
            q = next((e for e in snapshot["events"] if e["kind"] == "QUESTION"), None)
            if t["state"] != "AWAITING_ANSWER" or not q or q["question_id"] != question_id:
                raise ThreadStoreError("question_conflict", 409)
            t["state"] = "COMPLETED"
            t["data"]["body_state"] = "FINAL"
            event = _event("TERMINAL", {"reason": action, "request_fingerprint": fingerprint}, t, key=idempotency_key)
            try:
                return thread_dto(await self.store.commit(user_id, snapshot, t, [event]))
            except ThreadStoreError as exc:
                if exc.status == 409:
                    replay = self._replay(await self.store.read(user_id, thread_id=thread_id), idempotency_key, fingerprint)
                    if replay:
                        return replay
                raise
        if action != "retry_response" or not thread_dto(snapshot)["can_retry"] or operation_id != t["data"].get("operation_id"):
            raise ThreadStoreError("retry_not_available", 409)
        t["state"] = "REFINING" if t.get("latest_answer_event_id") else "INITIALIZING"
        self._begin(t, snapshot, operation_id)
        event = _event("OPERATION", {"status": "RUNNING", "request_fingerprint": fingerprint}, t, key=idempotency_key)
        try:
            snapshot = await self.store.commit(user_id, snapshot, t, [event])
        except ThreadStoreError as exc:
            if exc.status == 409:
                replay = self._replay(await self.store.read(user_id, thread_id=thread_id), idempotency_key, fingerprint)
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
                t["data"].update(answer_assessment=cp.assessment_status if update else "NOT_APPLICABLE",
                    meaning_updated=bool(update and cp.accepted_update_refs))
                if update:
                    t["data"]["body_state"] = "MEANING_UPDATED_BODY_UNAVAILABLE" if cp.accepted_update_refs else "ANSWER_UNREFLECTED"
                snapshot = await self.store.commit(user_id, snapshot, t, [checkpoint], finishing_attempt=attempt)
                t = snapshot["thread"]
                checkpoint = _find(snapshot, t["current_meaning_event_id"])
            cp = checkpoint["payload"]
            if cp["semantic_schema_version"] != SEMANTIC_SCHEMA or cp["source_prefix_ref"] != t["source_prefix_ref"]:
                raise ValueError("checkpoint_contract_changed")
            update = cp.get("answer_update")
            if update and update["disposition"] == "NO_MATERIAL_UPDATE":
                return await self._finish(user_id, snapshot, body_state="UNCHANGED", state="COMPLETED")
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
            observation = _event("OBSERVATION", {"text": artifact.text,
                "stage": "REFINED" if t.get("latest_answer_event_id") else "INITIAL",
                "meaning_checkpoint_ref": cp["checkpoint_id"], "source_prefix_ref": cp["source_prefix_ref"],
                "artifact": artifact, "meaning_graph": outcome.meaning_graph}, t)
            question = _event("QUESTION", outcome.question, t, question_id=outcome.question.question_id) if outcome.question else None
            return await self._finish(user_id, snapshot, body_state=outcome.body_state,
                state="AWAITING_ANSWER" if question else "COMPLETED", observation=observation, question=question)
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
            return thread_dto(fresh)
        return await self._finish(user_id, fresh, body_state=fresh["thread"]["data"]["body_state"],
                                  state="RESPONSE_FAILED", failure=reason)

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
        return thread_dto(await self.store.commit(user_id, snapshot, t, events, finishing_attempt=attempt))
