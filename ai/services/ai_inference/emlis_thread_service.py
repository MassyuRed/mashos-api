"""Persisted Emlis application: separate answer, meaning and body commits.

Q2 and Q3 saved profiles retain their source and round contracts. GET never
evaluates an answer or starts work. Application policy is checked at admission
and before each write; pausing preserves the reader and saved corrections.
"""
from __future__ import annotations

import asyncio
import base64
import copy
import hashlib
import json
from dataclasses import asdict, is_dataclass, replace
from datetime import datetime, timedelta, timezone
from enum import Enum
from uuid import uuid4

from emlis_ai_current_input_bundle import build_emlis_current_input_bundle
from publish_governance import parse_iso_utc, timestamp_in_history_retention
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.contracts import GenerationRequest, EngineStatus, ExecutionMode
from cocolon_meaning_experience_engine.source_kernel import freeze_text_source
from cocolon_meaning_experience_engine.emlis_thread_source import admit_emlis_thread, identity
from cocolon_meaning_experience_engine.natural_reply import ACTIVE_MEANING_PROFILE
from cocolon_meaning_experience_engine.emlis_thread_contracts import (
    EmlisThreadInputV1, EmlisQuestionControlV1, EmlisClarificationV1,
    EmlisQuestionDecisionV1, SupplementalAnswerSource, InterpretationCorrectionSource, SEMANTIC_SCHEMA,
)
from emlis_thread_store import EmlisThreadStore, ThreadStoreError
from emlis_thread_config import APPLICATION_EXECUTION_MODE, MAX_ANSWER_CHARS, writes_enabled

ATTEMPT_SECONDS = 30
DTO_SCHEMA = "cocolon.emlis_thread.application.v1"
RUNTIME_PROFILE = "q2.free.one_round.v1"
Q3_PROFILE = "q3.plan.sequential.v1"
NATURAL_REPLY_PROFILE = "natural_reply.v1"
NATURAL_QUESTION_POLICY = "native_bound_question.v1"

def question_limit(t, tier):
    started = t.get("started_question_limit", 1)
    data = t.get("data", {})
    if (data.get("runtime_profile") == Q3_PROFILE
            and data.get("response_profile") == NATURAL_REPLY_PROFILE
            and data.get("natural_question_policy") == NATURAL_QUESTION_POLICY):
        return min(started, 3)
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


def _corrections(snapshot):
    return tuple(InterpretationCorrectionSource(**e["payload"]["source"])
        for e in snapshot["events"] if e["kind"] == "OPERATION"
        and e["payload"].get("stage") == "INTERPRETATION_CORRECTION")


def _needs_correction_detail(text):
    import re
    value = re.sub(r"[\s。．.!！?？、,]+", "", text)
    return value in {"違う", "違います", "そうではありません", "そうじゃない",
                     "なんか違う", "わからない", "分からない"}


def _request(snapshot, *, checkpoint_ref=None, include_context=True, analysis_source_only=False):
    t, original = snapshot["thread"], dict(snapshot["original"])
    # DB optional text is nullable; the source kernel requires text leaves.
    # Adapt only this generation copy. Preserve the raw snapshot for storage CAS.
    for field in ("memo", "memo_action"):
        if field in original and original[field] is None:
            original[field] = ""
    original["created_at"] = parse_iso_utc(original["created_at"]).isoformat()
    semantic_profile = t["data"].get("semantic_profile")
    if semantic_profile is not None:
        from cocolon_meaning_experience_engine.emlis_semantic_admission import PROFILE, PROFILE_V2, MODEL_PROFILE
        if semantic_profile not in {PROFILE, PROFILE_V2, MODEL_PROFILE} or (not include_context and not analysis_source_only) or t["data"].get("execution_mode") != ExecutionMode.OFFLINE_CANDIDATE.value:
            raise ValueError("semantic_profile_or_history_not_supported")
    req = GenerationRequest("emlis-" + t["id"], build_emlis_current_input_bundle(original), original["id"],
                            execution_mode=ExecutionMode.OFFLINE_CANDIDATE.value if semantic_profile else APPLICATION_EXECUTION_MODE)
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
    feedback_sources = tuple(FrameFeedbackSourceV1(**{k:f[k] for k in ("frame_key","frame_ref","source_emotion_id","status","correction_text","version","updated_at")},
        target_context_json=_saved_frame_target(snapshot, f) if t['data'].get('response_profile') == NATURAL_REPLY_PROFILE else None)
        for f in snapshot.get("context",{}).get("feedback",[])) if q3 and include_context else ()
    return replace(req, emlis_thread=EmlisThreadInputV1(t["id"], ref, answers=answers,
        current_round=len(answers), question_control_context=control, admitted_history=tuple(history),
        rejected_frame_keys=rejected, frame_feedback_sources=feedback_sources,
        capability_snapshot="Q3_" + snapshot["tier"].upper() if q3 else "FREE_Q1",
        prepared_meaning_checkpoint_ref=checkpoint_ref,
        interpretation_corrections=_corrections(snapshot)))


def _saved_frame_target(snapshot, feedback):
    """Use exact saved commands; cross-thread commands need frozen dependencies."""
    matches = []
    events = list(snapshot['events'])
    if 'frame_target_dependencies' in snapshot['thread']['data']:
        targets = feedback.get('target_operations', [])
        if len(targets) > 1:
            return None
        events.extend(targets)
    seen = {}
    for event in events:
        if event['id'] in seen:
            if seen[event['id']] != event['payload']:
                return None
            continue
        seen[event['id']] = event['payload']
        payload = event['payload']
        saved = payload.get('frame_feedback_target')
        if (event['kind'] != 'OPERATION' or type(saved) is not dict
                or payload.get('status') != 'FRAME_' + feedback['status']
                or payload.get('request_fingerprint') != identity('frame-feedback-request',
                    feedback['frame_ref'], feedback['status'], feedback['correction_text'])):
            continue
        if (saved.get('feedback_version') == feedback['version']
                and saved.get('frame_key') == feedback['frame_key']
                and saved.get('frame_ref') == feedback['frame_ref']
                and saved.get('input_id') == feedback['source_emotion_id']):
            matches.append(saved)
    return json.dumps(matches[0], ensure_ascii=False, sort_keys=True) if len(matches) == 1 else None


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
    targets_current = ('frame_target_dependencies' not in t['data'] or
        t['data']['frame_target_dependencies'] == snapshot.get('context', {}).get('frame_target_dependencies', []))
    return (targets_current and _context_current(snapshot) and t["data"].get("evaluated_tier",snapshot["tier"]) == snapshot["tier"]
            and t["data"].get("context_feedback",[]) == feedback)


def _context_ref(snapshot):
    base = identity("context", snapshot["tier"], snapshot["thread"]["data"].get("context_guards", []),
                    snapshot["thread"]["data"].get("context_feedback", []))
    targets = snapshot['thread']['data'].get('frame_target_dependencies', [])
    return identity('context-frame-targets', base, [':'.join(map(str, row)) for row in targets]) if targets else base


def _observation_text(snapshot, payload):
    artifact = payload.get("artifact", {})
    if artifact.get("history_line") and not _context_current(snapshot, payload.get("context_guards", [])):
        return f"見えたこと：\n{artifact['observation']}\n\nEmlisから：\n{artifact['reception']}"
    return payload["text"]


def _natural_interpretive_frames(snapshot, material):
    """Reuse owned history frames without interpreting the model's reply.

    Only histories included by natural admission/Safety may contribute. Free
    form corrections remain outside the finite frame owner's capability.
    """
    t = snapshot["thread"]
    if (snapshot["tier"] != "premium" or t["data"].get("runtime_profile") != Q3_PROFILE
            or _corrections(snapshot)):
        return ()
    from cocolon_meaning_experience_engine.emlis_thread_history import derive_interpretive_frames
    try:
        admitted = admit_emlis_thread(_request(snapshot))
        included = {row["input_id"] for row in json.loads(material.material_json)["past_user_records"]}
        admitted = replace(admitted, control=replace(admitted.control,
            admitted_history=tuple(source for source in admitted.control.admitted_history
                if source.source_guard[0] in included)))
        return tuple(frame for frame in derive_interpretive_frames(admitted)
                     if frame.frame_key not in admitted.control.rejected_frame_keys)
    except ValueError:
        # Optional finite interpretation must not erase a valid natural reply.
        return ()


def _public_frames(snapshot):
    t = snapshot.get("thread")
    if not t or snapshot["tier"] != "premium" or t["data"].get("runtime_profile") != Q3_PROFILE:
        return []
    if t["data"].get("response_profile") == NATURAL_REPLY_PROFILE and _corrections(snapshot):
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


def thread_dto(snapshot, *, requested_attempt_id=None, can_write=True):
    t = _check(snapshot)
    original = {k: snapshot["original"].get(k) for k in ("id", "created_at", "memo", "memo_action")}
    if not t:
        return {"schema_version": DTO_SCHEMA, "state": "NOT_CREATED", "original": original,
                "thread_id": None, "timeline": [], "can_retry": False, "can_write": can_write}
    d = t["data"]
    expired = bool(t["active_attempt_id"] and parse_iso_utc(t["processing_deadline_at"]) <= _now(snapshot))
    state = "RESPONSE_FAILED" if expired else t["state"]
    body_state = d.get("body_state", "UNAVAILABLE")
    latest_body = _find(snapshot, t.get("last_observation_event_id"))
    target_visible = bool(latest_body and _generation_current(snapshot)
        and _context_current(snapshot, latest_body["payload"].get("context_guards", []))
        and latest_body["payload"].get("context_ref") == _context_ref(snapshot))
    current = _find(snapshot, t.get("last_observation_event_id")) if body_state in {
        "PRE_QUESTION", "FINAL", "REFINED", "PARTIALLY_REFINED", "UNCHANGED"} else None
    if current and (not _generation_current(snapshot)
            or current["payload"].get("artifact", {}).get("schema_version") == "cocolon.emlis.recipient_reply.v1"
                and not target_visible):
        current = None
        body_state = "CONTEXT_CHANGED"
    timeline = []
    correction_events = [e for e in snapshot["events"] if e["kind"] == "OPERATION"
        and e["payload"].get("stage") == "INTERPRETATION_CORRECTION"]
    disputed = {e["payload"]["source"]["target_event_id"] for e in correction_events}
    for event in snapshot["events"]:
        p = event["payload"]
        common = {"event_id": event["id"], "kind": event["kind"], "recorded_at": event.get("recorded_at"),
                  "round_index": event["round_index"]}
        if event["kind"] == "OBSERVATION":
            if (p.get('artifact', {}).get('schema_version') == 'cocolon.emlis.recipient_reply.v1'
                    and (not _generation_current(snapshot)
                         or not _context_current(snapshot, p.get('context_guards', []))
                         or p.get('context_ref') != _context_ref(snapshot))):
                # A natural reply cannot be split into current/past sections.
                # Do not leak a stale paid/deleted source through the timeline.
                continue
            timeline.append({**common, "text": _observation_text(snapshot,p), "stage": p["stage"],
                "is_current": bool(current and current["id"] == event["id"]),
                **({"is_disputed": True} if event["id"] in disputed else {})})
        elif event["kind"] == "QUESTION":
            timeline.append({**common, "question_id": event["question_id"], "text": p["prompt_private"]})
        elif event["kind"] == "ANSWER":
            timeline.append({**common, "text": p["source"]["answer_text_private"], "question_id": event["question_id"],
                "authored_at": p["source"]["authored_at"]})
        elif event in correction_events:
            source = p["source"]
            timeline.append({**common, "kind": "CORRECTION", "text": source["explanation"],
                "target_event_id": source["target_event_id"], "target_text": source["target_text"],
                "assessment": p["assessment"], "operation_key": event["idempotency_key"]})
    q = next((e for e in reversed(timeline) if e["kind"] == "QUESTION"), None)
    failure = "save_result_unknown" if expired else d.get("failure_code")
    return {"schema_version": DTO_SCHEMA, "thread_id": t["id"], "revision": t["revision"],
        "state": state, "original": original, "timeline": timeline, "can_write": can_write,
        "pending_question": q if state == "AWAITING_ANSWER" else None,
        "current_observation": {"event_id": current["id"], "text": _observation_text(snapshot,current["payload"])} if current else None,
        "body_state": body_state, "answer_saved": bool(t.get("latest_answer_event_id")),
        "answer_assessment": d.get("answer_assessment", "NOT_APPLICABLE"),
        "meaning_updated": d.get("meaning_updated", False),
        "failure_code": failure,
        "operation_id": t.get("active_operation_id") or d.get("operation_id"),
        "attempt_id": t.get("active_attempt_id") or d.get("attempt_id"),
        "requested_attempt_id": requested_attempt_id,
        "can_retry": bool(can_write and state == "RESPONSE_FAILED" and not expired and failure in RETRYABLE_FAILURES and _generation_current(snapshot)),
        "can_continue": bool(can_write and state == "AWAITING_CONTINUE" and d.get("continuation_question")
            and t["issued_count"] < question_limit(t, snapshot["tier"]) and _generation_current(snapshot)),
        "issued_count": t["issued_count"], "question_limit": question_limit(t, snapshot["tier"]),
        "started_question_limit": t.get("started_question_limit", 1),
        "processing_deadline_at": t.get("processing_deadline_at"),
        "correction_saved": bool(correction_events),
        "correction_assessment": correction_events[-1]["payload"]["assessment"] if correction_events else None,
        "can_correct": bool(can_write and state == "COMPLETED" and not failure
            and d.get("response_profile") == NATURAL_REPLY_PROFILE and _generation_current(snapshot)
            and (current or body_state == "CORRECTION_UNREFLECTED" and target_visible)),
        "correction_target": ({"event_id": t["last_observation_event_id"],
            "text": _find(snapshot, t["last_observation_event_id"])["payload"]["text"]}
            if body_state == "CORRECTION_UNREFLECTED" and target_visible
            and t.get("last_observation_event_id") else None),
        **({"interpretive_frames":_public_frames(snapshot)} if d["runtime_profile"] == Q3_PROFILE else {})}


class EmlisThreadService:
    def __init__(self, store=None, engine=None, *, runtime_profile=RUNTIME_PROFILE, enforce_application_policy=False,
                 semantic_profile=None, offline_candidate_source=None, offline_model_attempt_seconds=None,
                 natural_reply_source=None, response_profile=None, natural_questions_enabled=True,
                 natural_meaning_profile=ACTIVE_MEANING_PROFILE):
        if runtime_profile not in {RUNTIME_PROFILE, Q3_PROFILE}:
            raise ValueError("unsupported_thread_profile")
        if natural_reply_source is not None:
            if not callable(natural_reply_source) or semantic_profile is not None:
                raise ValueError("natural_reply_configuration_invalid")
            response_profile = NATURAL_REPLY_PROFILE
        if response_profile not in {None, NATURAL_REPLY_PROFILE}:
            raise ValueError("unsupported_response_profile")
        self.response_profile = response_profile
        self.natural_reply_source = natural_reply_source
        if type(natural_questions_enabled) is not bool:
            raise ValueError("natural_question_setting_invalid")
        self.natural_questions_enabled = natural_questions_enabled
        if natural_meaning_profile not in {None, ACTIVE_MEANING_PROFILE}:
            raise ValueError('natural_reply_meaning_profile_invalid')
        self.natural_meaning_profile = natural_meaning_profile
        if semantic_profile is not None or offline_candidate_source is not None:
            from cocolon_meaning_experience_engine.emlis_semantic_admission import PROFILE, PROFILE_V2, MODEL_PROFILE
            if semantic_profile not in {PROFILE, PROFILE_V2, MODEL_PROFILE} or not callable(offline_candidate_source) or enforce_application_policy:
                raise ValueError("semantic_offline_configuration_required")
        if offline_model_attempt_seconds is not None:
            from cocolon_meaning_experience_engine.emlis_semantic_admission import MODEL_PROFILE
            if (type(offline_model_attempt_seconds) is not int or not 31 <= offline_model_attempt_seconds <= 180
                    or semantic_profile != MODEL_PROFILE or not callable(offline_candidate_source)
                    or enforce_application_policy):
                raise ValueError("offline_model_attempt_configuration_required")
        self.semantic_profile = semantic_profile
        self.offline_candidate_source = offline_candidate_source
        self.offline_model_attempt_seconds = offline_model_attempt_seconds
        self.enforce_application_policy = enforce_application_policy
        self.runtime_profile = runtime_profile
        self.store = store or EmlisThreadStore()
        self.engine = engine or MeaningExperienceEngine()

    def _writable(self):
        return not self.enforce_application_policy or writes_enabled()

    def _require_write(self):
        if not self._writable():
            raise ThreadStoreError("application_paused", 503)

    def _semantic_writable(self, snapshot):
        data = (snapshot.get("thread") or {}).get("data", {})
        response_profile = data.get("response_profile", self.response_profile if not snapshot.get("thread") else None)
        if response_profile is not None:
            return response_profile == NATURAL_REPLY_PROFILE and callable(self.natural_reply_source)
        profile = (snapshot.get("thread") or {}).get("data", {}).get("semantic_profile")
        return profile is None or (not self.enforce_application_policy and profile == self.semantic_profile
            and callable(self.offline_candidate_source))

    def _require_thread_write(self, snapshot):
        if not self._semantic_writable(snapshot):
            if (snapshot.get("thread") or {}).get("data", {}).get("response_profile"):
                raise ThreadStoreError("natural_reply_configuration_required", 503)
            raise ThreadStoreError("semantic_offline_configuration_required", 409)

    def _dto(self, snapshot, **kwargs):
        dto = thread_dto(snapshot, can_write=self._writable() and self._semantic_writable(snapshot), **kwargs)
        t = snapshot.get("thread")
        if t and t["data"].get("response_profile") == NATURAL_REPLY_PROFILE:
            # A saved receipt may resume without acquisition. An interrupted
            # source/update preparation with no call marker may also resume;
            # a started call without a receipt remains an unknown result.
            received = self._natural_receipt(snapshot, "NATURAL_REPLY_RECEIVED")
            started = self._natural_receipt(snapshot, "NATURAL_REPLY_CALL_STARTED")
            dto["can_retry"] = bool(dto.get("can_retry") and (received or not started))
        return dto

    async def get(self, user_id, input_id):
        snapshot = await self._hydrate(user_id, await self.store.read(user_id, input_id=input_id))
        return self._dto(snapshot)

    async def _hydrate(self, user_id, snapshot, *, fresh=False):
        snapshot = copy.deepcopy(snapshot)
        t = snapshot.get("thread")
        if (t["data"].get("runtime_profile") if t else self.runtime_profile) != Q3_PROFILE:
            return snapshot
        profile = t['data'].get('response_profile') if t is not None else self.response_profile
        if profile == NATURAL_REPLY_PROFILE:
            guards = None if fresh or t is None else t['data'].get('context_guards', [])
            context = await self.store.related_context(user_id, snapshot['original']['id'], context_guards=guards)
        else:
            context = await self.store.context(user_id, snapshot['original']['id'])
        snapshot["context"] = context
        if t and fresh:
            t["data"]["context_guards"] = [h["guard"] for h in context["history"]]
            t["data"]["context_feedback"] = [[f["frame_key"],f["version"]] for f in context["feedback"]]
            if profile == NATURAL_REPLY_PROFILE and 'frame_target_dependencies' in context:
                t['data']['frame_target_dependencies'] = context['frame_target_dependencies']
        return snapshot

    async def _commit(self, user_id, snapshot, next_state, events, **kwargs):
        self._require_write()
        self._require_thread_write({"thread": next_state})
        result = await self.store.commit(user_id, snapshot, next_state, events, **kwargs)
        return {**result, **({"context":snapshot["context"]} if "context" in snapshot else {})}


    async def start(self, user_id, input_id):
        self._require_write()
        snapshot = await self._hydrate(user_id, await self.store.read(user_id, input_id=input_id))
        if _check(snapshot):
            return self._dto(snapshot)
        t = {"id": str(uuid4()), "state": "INITIALIZING", "issued_count": 0,
            "started_question_limit": 3 if self.runtime_profile == Q3_PROFILE and (
                snapshot["tier"] == "premium" or self.response_profile == NATURAL_REPLY_PROFILE) else 1,
            "data": {"runtime_profile": self.runtime_profile, "execution_mode": APPLICATION_EXECUTION_MODE,
                     "started_tier": snapshot["tier"],
                     "body_state": "UNAVAILABLE", "answer_assessment": "NOT_APPLICABLE"}}
        if self.semantic_profile:
            t["data"].update(semantic_profile=self.semantic_profile, execution_mode=ExecutionMode.OFFLINE_CANDIDATE.value)
        if self.runtime_profile == Q3_PROFILE:
            # This belongs to the saved input, not to source meaning. Existing
            # threads returned above retain the preference they started with.
            receive_questions = snapshot.get("receive_emlis_questions", True)
            if type(receive_questions) is not bool:
                raise ThreadStoreError("question_setting_unavailable")
            t["data"]["receive_emlis_questions"] = receive_questions
        if self.response_profile:
            t["data"].update(response_profile=self.response_profile, analysis_state="NOT_GENERATED")
            if self.natural_meaning_profile is not None:
                t['data']['natural_meaning_profile'] = self.natural_meaning_profile
            if self.runtime_profile == Q3_PROFILE:
                t["data"].update(natural_question_policy=NATURAL_QUESTION_POLICY,
                    natural_questions_enabled=self.natural_questions_enabled and receive_questions)
        self._begin(t, snapshot)
        if self.runtime_profile == Q3_PROFILE:
            t["data"].update(context_guards=[h["guard"] for h in snapshot["context"]["history"]],
                context_feedback=[[f["frame_key"],f["version"]] for f in snapshot["context"]["feedback"]])
            if self.response_profile == NATURAL_REPLY_PROFILE and 'frame_target_dependencies' in snapshot['context']:
                t['data']['frame_target_dependencies'] = snapshot['context']['frame_target_dependencies']
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
                    return self._dto(fresh)
            raise
        return await self._process(user_id, snapshot)

    def _attempt_seconds(self, t):
        if t.get("data", {}).get("response_profile") == NATURAL_REPLY_PROFILE:
            # Includes a bounded wait behind the existing Analysis GPU job.
            return 270
        if self.offline_model_attempt_seconds is None:
            return ATTEMPT_SECONDS
        from cocolon_meaning_experience_engine.emlis_semantic_admission import MODEL_PROFILE
        data = t.get("data", {})
        if (self.offline_model_attempt_seconds is not None and self.semantic_profile == MODEL_PROFILE
                and callable(self.offline_candidate_source) and not self.enforce_application_policy
                and data.get("semantic_profile") == MODEL_PROFILE
                and data.get("execution_mode") == ExecutionMode.OFFLINE_CANDIDATE.value):
            return self.offline_model_attempt_seconds
        return ATTEMPT_SECONDS

    def _begin(self, t, snapshot, operation_id=None):
        t["active_operation_id"] = operation_id or str(uuid4())
        t["active_attempt_id"] = str(uuid4())
        t["processing_deadline_at"] = (_now(snapshot) + timedelta(seconds=self._attempt_seconds(t))).isoformat()
        t["data"].update(failure_code=None, operation_id=t["active_operation_id"], attempt_id=t["active_attempt_id"])
        if operation_id is None and t['data'].get('natural_meaning_profile') == ACTIVE_MEANING_PROFILE:
            # A new generation fixes its source interpretation time. A retry
            # of the same operation keeps the original material identity.
            t['data']['natural_meaning_as_of'] = _now(snapshot).isoformat()
            t['data']['analysis_state'] = 'NOT_GENERATED'
            t['data'].pop('analysis_material', None)

    def _replay(self, snapshot, key, fingerprint):
        found = next((e for e in snapshot["events"] if e.get("idempotency_key") == key), None)
        if found:
            if found["payload"].get("request_fingerprint") != fingerprint:
                raise ThreadStoreError("idempotency_conflict", 409)
            dto = self._dto(snapshot, requested_attempt_id=found["attempt_id"])
            if snapshot["thread"]["data"]["runtime_profile"] == Q3_PROFILE:
                terminal = next((e for e in reversed(snapshot["events"]) if found["attempt_id"] and
                    e["attempt_id"] == found["attempt_id"] and e["kind"] == "OPERATION"), found)
                dto["requested_operation"] = {"idempotency_key":key, "event_id":found["id"],
                    "question_id":found["question_id"], "operation_id":found["operation_id"],
                    "attempt_id":found["attempt_id"], "status":terminal["payload"].get("status",terminal["payload"].get("reason","SAVED"))}
            return dto

    async def answer(self, user_id, thread_id, *, question_id, expected_revision, idempotency_key,
                     answer_text, authored_at=None):
        self._require_write()
        if not isinstance(answer_text, str) or not answer_text.strip() or len(answer_text) > MAX_ANSWER_CHARS:
            raise ThreadStoreError("answer_invalid", 422)
        snapshot = await self._hydrate(user_id, await self.store.read(user_id, thread_id=thread_id))
        t = _check(snapshot)
        self._require_thread_write(snapshot)
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

    async def correct_interpretation(self, user_id, thread_id, *, target_event_id, target_text,
                                     explanation, expected_revision, idempotency_key):
        self._require_write()
        if any(not isinstance(value, str) or not value.strip() or len(value) > 2000
               for value in (target_text, explanation)):
            raise ThreadStoreError("correction_fields_required", 422)
        snapshot = await self._hydrate(user_id, await self.store.read(user_id, thread_id=thread_id))
        t = _check(snapshot)
        self._require_thread_write(snapshot)
        fingerprint = identity("interpretation-correction-request", target_event_id, target_text, explanation)
        replay = self._replay(snapshot, idempotency_key, fingerprint)
        if replay:
            return replay
        dto = self._dto(snapshot)
        target = dto.get("current_observation") or dto.get("correction_target")
        if (t["revision"] != expected_revision or not dto.get("can_correct")
                or t["active_attempt_id"] or not target or target["event_id"] != target_event_id):
            raise ThreadStoreError("correction_target_changed", 409)
        first = target["text"].find(target_text)
        if first < 0 or target["text"].find(target_text, first + 1) >= 0:
            raise ThreadStoreError("correction_target_must_be_unique_excerpt", 422)
        # Recheck the saved cohort rather than selecting different history for
        # a correction of this exact reply. A changed source cannot reappear
        # through the target preview while the normal timeline hides it.
        snapshot = await self._hydrate(user_id, snapshot)
        refreshed = self._dto(snapshot)
        if (refreshed.get("current_observation") or refreshed.get("correction_target")) != target:
            raise ThreadStoreError("correction_target_changed", 409)
        t = copy.deepcopy(snapshot["thread"])
        if self.natural_meaning_profile is not None:
            # A new correction is a new source/generation. Existing receipts
            # and checkpoints keep the profile with which they were created.
            t['data']['natural_meaning_profile'] = self.natural_meaning_profile
        detail_needed = _needs_correction_detail(explanation)
        t["state"] = "COMPLETED" if detail_needed else "REFINING"
        if not detail_needed:
            self._begin(t, snapshot)
        correction_id = str(uuid4())
        source = InterpretationCorrectionSource(correction_id, thread_id, t["data"]["original_source_ref"],
            target_event_id, target_text, explanation, _now(snapshot).isoformat())
        event = _event("OPERATION", {"stage": "INTERPRETATION_CORRECTION", "status": "SAVED",
            "source": source, "assessment": "NEEDS_DETAIL" if detail_needed else "UNASSESSED",
            "request_fingerprint": fingerprint}, t, key=idempotency_key, event_id=correction_id)
        t["data"].update(body_state="CORRECTION_UNREFLECTED", meaning_updated=False,
            natural_response_stage="FINAL", failure_code=None,
            context_guards=[h["guard"] for h in snapshot["context"]["history"]],
            context_feedback=[[f["frame_key"], f["version"]] for f in snapshot["context"]["feedback"]])
        t['data']['analysis_state'] = 'NOT_GENERATED'
        t['data'].pop('analysis_material', None)
        t["data"].pop("continuation_question", None)
        t["current_meaning_event_id"] = None
        t["evaluated_prefix_ref"] = None
        proposed = {**snapshot, "thread": t, "events": snapshot["events"] + [event]}
        t["source_prefix_ref"] = admit_emlis_thread(_request(proposed)).source_prefix_ref
        try:
            saved = await self._commit(user_id, snapshot, t, [event])
        except ThreadStoreError as exc:
            if exc.code == "save_result_unknown":
                # A lost admission ACK is not permission to repeat the write
                # or acquire the provider twice. Read the exact saved command.
                fresh = await self._hydrate(user_id, await self.store.read(user_id, thread_id=thread_id))
                admitted = _find(fresh, correction_id)
                if not admitted or admitted["payload"] != _json(event["payload"]):
                    raise
                if (fresh["thread"].get("active_attempt_id") != t.get("active_attempt_id")
                        or fresh["thread"]["source_prefix_ref"] != t["source_prefix_ref"]):
                    return self._replay(fresh, idempotency_key, fingerprint)
                saved = fresh
            elif exc.status == 409:
                replay = self._replay(await self._hydrate(user_id, await self.store.read(
                    user_id, thread_id=thread_id)), idempotency_key, fingerprint)
                if replay:
                    return replay
                raise
            else:
                raise
        return self._dto(saved) if detail_needed else await self._process(user_id, saved)

    async def frame_feedback(self,user_id,thread_id,*,frame_ref,status,correction_text,
                             expected_revision,idempotency_key):
        self._require_write()
        if (status not in {"CONFIRMED","REJECTED","REVISED"} or (status == "REVISED") != bool(correction_text)
                or correction_text is not None and (not isinstance(correction_text,str) or not correction_text.strip() or len(correction_text)>2000)):
            raise ThreadStoreError("frame_feedback_invalid",422)
        snapshot = await self._hydrate(user_id,await self.store.read(user_id,thread_id=thread_id))
        t = _check(snapshot)
        self._require_thread_write(snapshot)
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
        payload = {"status":"FRAME_"+status,"request_fingerprint":fingerprint}
        if t['data'].get('response_profile') == NATURAL_REPLY_PROFILE:
            body = _find(snapshot, t.get('last_observation_event_id'))
            artifacts = body['payload'].get('artifact', {}).get('interpretive_frames', []) if body else []
            source = next((h for h in snapshot['context']['history']
                           if h['guard'][0] == frame['input_id']), None)
            prior = next((f for f in snapshot['context']['feedback']
                          if f['frame_key'] == frame['frame_key']), None)
            targets = [row for row in artifacts if row['frame_key'] == frame['frame_key']
                       and row['input_id'] == frame['input_id']
                       and (identity('frame-view', row['frame_ref'], prior['version'])
                            if prior else row['frame_ref']) == frame_ref]
            if source and len(targets) == 1 and targets[0].get('evidence_refs'):
                # This is exactly the text shown by FrameEditor, including a
                # previous user revision, rather than the old AI wording.
                payload['frame_feedback_target'] = dict(
                    frame_key=frame['frame_key'], frame_ref=frame_ref, input_id=frame['input_id'],
                    feedback_version=(prior['version'] if prior else 0) + 1,
                    source_guard=source['guard'], trigger=frame['trigger'],
                    received_meaning=frame['correction_text'] if frame['status'] == 'REVISED' else frame['received_meaning'],
                    displayed_status=frame['status'], evidence_refs=targets[0]['evidence_refs'])
        event = _event("OPERATION",payload,t,key=idempotency_key)
        saved = await self._commit(user_id,snapshot,t,[event])
        return self._dto(await self._hydrate(user_id,saved))

    async def action(self, user_id, thread_id, *, action, expected_revision, idempotency_key,
                     question_id=None, operation_id=None):
        self._require_write()
        snapshot = await self._hydrate(user_id, await self.store.read(user_id, thread_id=thread_id))
        t = _check(snapshot)
        self._require_thread_write(snapshot)
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
            if (t["data"].get("response_profile") == NATURAL_REPLY_PROFILE
                    and t["data"].get("natural_question_policy") == NATURAL_QUESTION_POLICY):
                snapshot = await self._hydrate(user_id, snapshot, fresh=True)
                t = copy.deepcopy(snapshot["thread"])
                body = _find(snapshot, t.get("last_observation_event_id"))
                payload = body["payload"] if body else {}
                artifact = payload.get("artifact", {})
                reuse_refined = (action == "stop" and t["state"] == "AWAITING_CONTINUE"
                    and t["data"].get("body_state") == "REFINED" and t.get("latest_answer_event_id")
                    and body and body["kind"] == "OBSERVATION" and payload.get("stage") == "REFINED"
                    and artifact.get("schema_version") == "cocolon.emlis.recipient_reply.v1"
                    and artifact.get("text") == payload.get("text")
                    and payload.get("source_prefix_ref") == t["source_prefix_ref"]
                    and payload.get("context_ref") == _context_ref(snapshot)
                    and _generation_current(snapshot)
                    and _context_current(snapshot, payload.get("context_guards", []))
                    and admit_emlis_thread(_request(snapshot)).source_prefix_ref == t["source_prefix_ref"])
                if reuse_refined:
                    # The complete answer-based reply already covers the same
                    # live sources. End the questions without reacquiring it.
                    t["data"]["natural_question_stop"] = action
                    t["data"].pop("continuation_question", None)
                else:
                    # An initial acknowledgement or stale reply still needs a
                    # final response over the currently admitted sources.
                    t["data"].update(natural_question_stop=action, natural_response_stage="FINAL")
                    t["state"] = "REFINING" if t.get("latest_answer_event_id") else "INITIALIZING"
                    self._begin(t, snapshot)
                    proposed = {**snapshot, "thread": t}
                    t["source_prefix_ref"] = admit_emlis_thread(_request(proposed)).source_prefix_ref
                    event = _event("OPERATION", {"status": "RUNNING", "stage": "NATURAL_FINAL_REQUESTED",
                        "question_ending": action, "request_fingerprint": fingerprint}, t, key=idempotency_key)
                    try:
                        saved = await self._commit(user_id, snapshot, t, [event])
                    except ThreadStoreError as exc:
                        if exc.status == 409:
                            replay = self._replay(await self._hydrate(user_id, await self.store.read(
                                user_id, thread_id=thread_id)), idempotency_key, fingerprint)
                            if replay:
                                return replay
                        raise
                    return await self._process(user_id, saved)
            t["state"] = "COMPLETED"
            if t["data"]["body_state"] == "PRE_QUESTION":
                t["data"]["body_state"] = "FINAL"
            event = _event("TERMINAL", {"reason": action, "request_fingerprint": fingerprint}, t, key=idempotency_key)
            try:
                return self._dto(await self._commit(user_id, snapshot, t, [event]))
            except ThreadStoreError as exc:
                if exc.status == 409:
                    replay = self._replay(await self._hydrate(user_id, await self.store.read(user_id, thread_id=thread_id)), idempotency_key, fingerprint)
                    if replay:
                        return replay
                raise
        if action == "continue":
            if not self._dto(snapshot)["can_continue"] or t["data"]["runtime_profile"] != Q3_PROFILE:
                raise ThreadStoreError("continue_not_available", 409)
            if not _generation_current(snapshot) or admit_emlis_thread(_request(snapshot)).source_prefix_ref != t["source_prefix_ref"]:
                raise ThreadStoreError("continue_source_changed",409)
            q = t["data"].pop("continuation_question")
            question = _event("QUESTION", q, t, question_id=q["question_id"])
            t["issued_count"] += 1
            event = _event("OPERATION", {"status": "CONTINUED", "request_fingerprint": fingerprint}, t, key=idempotency_key)
            t["state"] = "AWAITING_ANSWER"
            try:
                return self._dto(await self._commit(user_id, snapshot, t, [question, event]))
            except ThreadStoreError as exc:
                if exc.status == 409:
                    replay = self._replay(await self._hydrate(user_id, await self.store.read(user_id, thread_id=thread_id)), idempotency_key, fingerprint)
                    if replay:
                        return replay
                raise
        if action != "retry_response" or not self._dto(snapshot)["can_retry"] or operation_id != t["data"].get("operation_id"):
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

    async def _semantic_candidate(self, user_id, snapshot):
        """Persist acquisition and receipt separately; interrupted acquisition is not retried."""
        from cocolon_meaning_experience_engine.preparation import CandidateReceipt
        t = snapshot["thread"]
        prefix = t["source_prefix_ref"]
        previous = [e for e in snapshot["events"] if e["kind"] == "OPERATION"
            and e["payload"].get("attempted_source_prefix_ref") == prefix]
        evaluation = next((e for e in reversed(previous) if e["payload"].get("stage") == "SEMANTIC_NOT_ADOPTED"), None)
        if evaluation:
            return snapshot, None, None, evaluation
        saved = next((e for e in reversed(previous) if e["payload"].get("stage") == "SEMANTIC_CANDIDATE_RECEIVED"), None)
        prior_event = _find(snapshot, t.get("current_meaning_event_id"))
        prior = prior_event["payload"].get("semantic_snapshot") if prior_event else None
        if saved:
            return snapshot, CandidateReceipt(**saved["payload"]["candidate_receipt"]), prior, None
        if previous:
            raise ThreadStoreError("semantic_candidate_acquisition_incomplete")
        if self.semantic_profile != t["data"].get("semantic_profile") or not self.offline_candidate_source:
            raise ThreadStoreError("semantic_candidate_source_unavailable")
        started = _event("OPERATION", {"stage":"SEMANTIC_CANDIDATE_STARTED",
            "attempted_source_prefix_ref":prefix}, t)
        snapshot = await self._commit(user_id, snapshot, copy.deepcopy(t), [started], finishing_attempt=t["active_attempt_id"])
        import inspect
        wait_seconds = None
        attempt_seconds = self._attempt_seconds(t)
        if attempt_seconds != ATTEMPT_SECONDS:
            # Only the explicit private model profile gets a longer attempt.
            # Leave 30 seconds for receipt, meaning and body commits. The
            # server-returned clock also accounts for the STARTED commit.
            wait_seconds = min(attempt_seconds - 30,
                (parse_iso_utc(t["processing_deadline_at"]) - _now(snapshot)).total_seconds() - 30)
            if wait_seconds <= 0:
                raise ThreadStoreError("semantic_candidate_acquisition_incomplete")
        candidate = self.offline_candidate_source(_request(snapshot), prior)
        if inspect.isawaitable(candidate):
            if wait_seconds is None:
                candidate = await candidate
            else:
                try:
                    candidate = await asyncio.wait_for(candidate, timeout=wait_seconds)
                except TimeoutError:
                    # STARTED remains authoritative: an absent response does
                    # not permit another provider acquisition. External
                    # CancelledError still reaches the existing worker path.
                    raise ThreadStoreError("semantic_candidate_acquisition_incomplete") from None
        # A synchronous source keeps its existing behavior; it cannot be
        # interrupted by wait_for. SQL still rejects every expired commit.
        if type(candidate) is not CandidateReceipt:
            raise ValueError("semantic_candidate_receipt_required")
        t = snapshot["thread"]
        event = _event("OPERATION", {"stage":"SEMANTIC_CANDIDATE_RECEIVED",
            "attempted_source_prefix_ref":prefix, "candidate_receipt":asdict(candidate)}, t)
        snapshot = await self._commit(user_id, snapshot, copy.deepcopy(t), [event], finishing_attempt=t["active_attempt_id"])
        return snapshot, candidate, prior, None

    async def _semantic_unadopted(self, user_id, snapshot, decision, code, receipt):
        t = copy.deepcopy(snapshot["thread"])
        prior = _find(snapshot, t.get("current_meaning_event_id"))
        event = _event("OPERATION", {"stage":"SEMANTIC_NOT_ADOPTED", "semantic_profile":t["data"]["semantic_profile"],
            "attempted_source_prefix_ref":t["source_prefix_ref"],
            "prior_active_snapshot_ref":prior["payload"].get("snapshot_ref") if prior else None,
            "decision":decision, "reason_codes":[code], "candidate_receipt":asdict(receipt) if receipt else None}, t)
        t["data"].update(semantic_evaluation_ref=event["id"], answer_assessment="UNRESOLVED" if t.get("latest_answer_event_id") else "NOT_APPLICABLE", meaning_updated=False)
        snapshot = await self._commit(user_id, snapshot, t, [event], finishing_attempt=t["active_attempt_id"])
        return await self._finish(user_id, snapshot, body_state="ANSWER_UNREFLECTED" if t.get("latest_answer_event_id") else "UNAVAILABLE",
            state="COMPLETED")

    @staticmethod
    def _natural_receipt(snapshot, stage):
        t = snapshot["thread"]
        purpose = t["data"].get("natural_response_stage", "FINAL")
        return next((e for e in reversed(snapshot["events"]) if e["kind"] == "OPERATION"
            and e["payload"].get("stage") == stage
            and e["payload"].get("source_prefix_ref") == t["source_prefix_ref"]
            and e["payload"].get("context_ref") == _context_ref(snapshot)
            and e["payload"].get("response_stage", "FINAL") == purpose), None)

    async def _prepare_natural_question(self, user_id, snapshot):
        """Reuse the source-bound question/update owners, without an old author.

        Unsupported initial prose remains a natural reply, not a compulsory
        finite checkpoint or an invented question. A persisted answer, on the
        other hand, is rebound to its actual issued question by the existing
        update owner before a new meaning checkpoint is committed.
        """
        t = snapshot["thread"]
        if t["data"].get("natural_question_policy") != NATURAL_QUESTION_POLICY:
            return snapshot, None, None
        from cocolon_meaning_experience_engine.emlis_question import (
            original_meaning_plan, question_candidate)
        request = _request(snapshot)
        admitted = admit_emlis_thread(request)
        prepared = None
        if admitted.answers:
            from cocolon_meaning_experience_engine.emlis_answer_update import (
                prepare_emlis_meaning, build_updated_grounded_plan)
            saved = _find(snapshot, t.get("current_meaning_event_id"))
            checkpoint_ref = (saved["payload"]["checkpoint_id"] if saved and
                t.get("evaluated_prefix_ref") == t["source_prefix_ref"] else None)
            prepared = await asyncio.to_thread(prepare_emlis_meaning,
                _request(snapshot, checkpoint_ref=checkpoint_ref))
            checkpoint = _json(prepared.checkpoint)
            if checkpoint_ref is not None:
                if saved["payload"] != checkpoint:
                    raise ValueError("natural_answer_checkpoint_changed")
            else:
                next_thread = copy.deepcopy(t)
                event = _event("MEANING_UPDATE", checkpoint, next_thread)
                update = prepared.checkpoint.answer_update
                next_thread.update(current_meaning_event_id=event["id"],
                    evaluated_prefix_ref=prepared.checkpoint.source_prefix_ref)
                next_thread["data"].update(evaluated_tier=snapshot["tier"],
                    answer_assessment=prepared.checkpoint.assessment_status,
                    meaning_updated=bool(update and update.updates),
                    body_state="MEANING_UPDATED_BODY_UNAVAILABLE" if update and update.updates
                        else "ANSWER_UNREFLECTED")
                snapshot = await self._commit(user_id, snapshot, next_thread, [event],
                    finishing_attempt=t["active_attempt_id"])
                t = snapshot["thread"]
            if prepared.checkpoint.assessment_status != "RESOLVED":
                return snapshot, None, prepared
            plan = await asyncio.to_thread(build_updated_grounded_plan, prepared)
        else:
            # Source/Safety admission has already succeeded in the caller.
            # This optional old finite adapter cannot manufacture a missing
            # dimension from a parser failure or block ordinary free prose.
            try:
                plan = await asyncio.to_thread(original_meaning_plan, admitted)
            except Exception:
                return snapshot, None, None
        if (not t["data"].get("natural_questions_enabled", True)
                or t["data"].get("natural_question_stop")
                or t["issued_count"] >= question_limit(t, snapshot["tier"])):
            return snapshot, None, prepared
        try:
            decision, question = await asyncio.to_thread(question_candidate,
                prepared.thread if prepared is not None else admitted, plan,
                parent_request_id=request.request_id)
        except Exception:
            if prepared is not None:
                raise
            return snapshot, None, None
        return snapshot, question if decision.disposition == "ASK" else None, prepared

    async def _process_natural(self, user_id, snapshot):
        from cocolon_meaning_experience_engine.natural_reply import (
            ARTIFACT_SCHEMA, NaturalReply, NaturalReplyError, prepare_natural_reply, validate_reply,
            build_natural_reply_messages)
        from cocolon_meaning_experience_engine.natural_reply_meaning import (
            SCHEMA as MEANING_REVIEW_SCHEMA, compare_reply_meaning)
        t = snapshot["thread"]
        # Admit and triage before consulting the optional question adapter.
        material, safety = prepare_natural_reply(_request(snapshot))
        if material.source_prefix_ref != t["source_prefix_ref"]:
            raise ValueError("natural_reply_source_changed")
        if not safety.normal_observation_allowed:
            # Non-emergency self-denial has its own owner, distinct from
            # support/emergency. Neither is sent to the ordinary provider.
            code = "safe_state_answer_owner_required" if safety.safe_state_answer_allowed else "separate_safety_owner_required"
            return await self._finish(user_id, snapshot, body_state="UNAVAILABLE", state="COMPLETED", failure=code)
        correcting = bool(_corrections(snapshot))
        if correcting:
            # Free-form correction is not a finite answer checkpoint or a new question.
            next_question, prepared_meaning = None, None
        else:
            snapshot, next_question, prepared_meaning = await self._prepare_natural_question(user_id, snapshot)
        t = snapshot["thread"]
        response_stage = ("FINAL" if correcting or t["data"].get("natural_question_stop") else
            "REFINED" if t.get("latest_answer_event_id") else
            "PRE_QUESTION" if next_question else "FINAL")
        snapshot = copy.deepcopy(snapshot)
        snapshot["thread"]["data"]["natural_response_stage"] = response_stage
        t = snapshot["thread"]
        material, safety = prepare_natural_reply(_request(snapshot), response_stage=response_stage,
            prepared_meaning=prepared_meaning,
            meaning_profile=t['data'].get('natural_meaning_profile'), owner_scope=user_id,
            original_record=snapshot['original'], as_of=t['data'].get('natural_meaning_as_of'))
        writer_identity = {}
        if material.meaning_profile is not None:
            writer_identity = {'meaning_profile': material.meaning_profile,
                'writer_messages_sha256': hashlib.sha256(json.dumps(build_natural_reply_messages(material),
                    ensure_ascii=False, separators=(',', ':')).encode('utf-8')).hexdigest()}

        def check_writer_identity(event):
            payload = event['payload']
            if ({key: payload[key] for key in writer_identity if key in payload} != writer_identity
                    or payload.get('meaning_profile') != material.meaning_profile):
                raise NaturalReplyError('natural_reply_writer_identity_changed')

        received = self._natural_receipt(snapshot, "NATURAL_REPLY_RECEIVED")
        if received:
            check_writer_identity(received)
            candidate = validate_reply(NaturalReply(**received["payload"]["reply"]), material)
        else:
            started = self._natural_receipt(snapshot, "NATURAL_REPLY_CALL_STARTED")
            if started:
                check_writer_identity(started)
                return await self._finish(user_id, snapshot, body_state="UNAVAILABLE", state="RESPONSE_FAILED",
                                          failure="natural_reply_result_unknown")
            event = _event("OPERATION", {"stage": "NATURAL_REPLY_CALL_STARTED",
                "source_prefix_ref": t["source_prefix_ref"], "context_ref": _context_ref(snapshot),
                "response_stage": response_stage, **writer_identity}, t)
            snapshot = await self._commit(user_id, snapshot, copy.deepcopy(t), [event], finishing_attempt=t["active_attempt_id"])
            t = snapshot["thread"]
            remaining = (parse_iso_utc(t["processing_deadline_at"]) - _now(snapshot)).total_seconds() - 3
            if remaining <= 0:
                raise NaturalReplyError("natural_reply_deadline")
            self._require_write()
            try:
                candidate = validate_reply(await asyncio.wait_for(self.natural_reply_source(material),
                    timeout=min(240.0, remaining)), material)
            except asyncio.CancelledError:
                raise
            except Exception:
                return await self._finish(user_id, snapshot, body_state="UNAVAILABLE", state="RESPONSE_FAILED",
                                          failure="natural_reply_unavailable")
            event = _event("OPERATION", {"stage": "NATURAL_REPLY_RECEIVED",
                "source_prefix_ref": t["source_prefix_ref"], "context_ref": _context_ref(snapshot),
                "response_stage": response_stage, "reply": asdict(candidate), **writer_identity}, t)
            try:
                snapshot = await self._commit(user_id, snapshot, copy.deepcopy(t), [event], finishing_attempt=t["active_attempt_id"])
            except ThreadStoreError as exc:
                if exc.code != "save_result_unknown":
                    raise
                # Resolve an unknown receipt ACK by reading the actual row.
                # Do not resend the HTTP request or repeat the receipt write.
                fresh = await self._hydrate(user_id, await self.store.read(user_id, thread_id=t["id"]))
                _check(fresh)
                saved = self._natural_receipt(fresh, "NATURAL_REPLY_RECEIVED")
                if (fresh["thread"]["active_attempt_id"] != t["active_attempt_id"]
                        or not saved or saved["payload"].get("reply") != asdict(candidate)):
                    raise exc
                snapshot = fresh
            t = snapshot["thread"]
        try:
            meaning_review = compare_reply_meaning(material.material_json, candidate.text,
                                                   material.source_prefix_ref).as_private_dict()
        except ValueError:
            # Invalid admitted material is not an unsupported construction.
            raise
        except Exception:
            # Initial application observes this finite reader; a reader bug
            # never certifies a reply, repeats the provider call, or replaces it.
            meaning_review = {"schema_version": MEANING_REVIEW_SCHEMA,
                "source_prefix_ref": material.source_prefix_ref, "verdict": "UNASSESSED",
                "material_sha256": hashlib.sha256(material.material_json.encode("utf-8")).hexdigest(),
                "reply_sha256": hashlib.sha256(candidate.text.encode("utf-8")).hexdigest(),
                "reason_codes": ["CHECKER_ERROR"],
                "full_reply_semantic_coverage": False}
        frames = await asyncio.to_thread(_natural_interpretive_frames, snapshot, material)
        analysis_material = (json.loads(material.analysis_material_json)
            if material.analysis_material_json is not None else None)
        analysis_state = analysis_material['state'] if analysis_material is not None else 'NOT_GENERATED'
        if analysis_state not in {'GENERATED', 'NOT_GENERATED'}:
            raise NaturalReplyError('natural_reply_analysis_material_invalid')
        t['data']['analysis_state'] = analysis_state
        if analysis_material is not None:
            t['data']['analysis_material'] = analysis_material
        observation = _event("OBSERVATION", {"text": candidate.text,
            "stage": "CORRECTED" if correcting else "REFINED" if t.get("latest_answer_event_id") else "INITIAL",
            "source_prefix_ref": t["source_prefix_ref"], "context_ref": _context_ref(snapshot),
            "context_guards": t["data"].get("context_guards", []),
            "artifact": {"schema_version": ARTIFACT_SCHEMA, "text": candidate.text,
                         "model": candidate.model, "analysis_state": analysis_state,
                         **({'analysis_material': analysis_material,
                             'meaning_profile': material.meaning_profile,
                             'writer_messages_sha256': writer_identity['writer_messages_sha256']}
                            if analysis_material is not None else {}),
                         "meaning_comparison": meaning_review,
                         **({"interpretive_frames": _json(frames)} if frames else {})}}, t)
        followup = bool(next_question and t.get("latest_answer_event_id"))
        question = (_event("QUESTION", next_question, t, question_id=next_question.question_id)
                    if next_question and not followup else None)
        if followup:
            snapshot = copy.deepcopy(snapshot)
            snapshot["thread"]["data"]["continuation_question"] = _json(next_question)
        body_state = ("FINAL" if correcting else "PRE_QUESTION" if question else
            "REFINED" if t.get("latest_answer_event_id") and t["data"].get("meaning_updated") else "FINAL")
        return await self._finish(user_id, snapshot, body_state=body_state,
            state="AWAITING_ANSWER" if question else "AWAITING_CONTINUE" if followup else "COMPLETED",
            observation=observation, question=question)

    async def _process(self, user_id, snapshot):
        t, attempt = snapshot["thread"], snapshot["thread"]["active_attempt_id"]
        try:
            self._require_write()
            self._require_thread_write(snapshot)
            if t["data"].get("response_profile") == NATURAL_REPLY_PROFILE:
                remaining = (parse_iso_utc(t["processing_deadline_at"]) - _now(snapshot)).total_seconds()
                return await asyncio.wait_for(self._process_natural(user_id, snapshot), timeout=max(0, remaining))
            semantic_input = None
            semantic = t["data"].get("semantic_profile")
            if semantic:
                from cocolon_meaning_experience_engine.emlis_semantic_admission import (
                    PROFILE, PROFILE_V2, MODEL_PROFILE, CHECKPOINT_SCHEMA, CHECKPOINT_SCHEMA_V3,
                    MODEL_CHECKPOINT_SCHEMA, SemanticInput, SemanticNotAdopted)
                if semantic not in {PROFILE, PROFILE_V2, MODEL_PROFILE} or t["data"].get("execution_mode") != ExecutionMode.OFFLINE_CANDIDATE.value:
                    raise ValueError("semantic_profile_invalid")
            checkpoint = _find(snapshot, t.get("current_meaning_event_id"))
            if t.get("evaluated_prefix_ref") != t["source_prefix_ref"]:
                if semantic:
                    snapshot, candidate, prior, evaluation = await self._semantic_candidate(user_id, snapshot)
                    t = snapshot["thread"]
                    if evaluation:
                        return await self._finish(user_id, snapshot,
                            body_state="ANSWER_UNREFLECTED" if t.get("latest_answer_event_id") else "UNAVAILABLE", state="COMPLETED")
                    semantic_input = SemanticInput("FRESH_CANDIDATE", candidate, prior_snapshot_json=prior, semantic_profile=semantic)
                    try:
                        cp = await asyncio.to_thread(self.engine.prepare_emlis_update, _request(snapshot), semantic_input=semantic_input)
                    except SemanticNotAdopted as exc:
                        return await self._semantic_unadopted(user_id, snapshot, exc.decision, exc.reason_code, candidate)
                else:
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
            expected_schema = (MODEL_CHECKPOINT_SCHEMA if semantic == MODEL_PROFILE else
                CHECKPOINT_SCHEMA_V3 if semantic == PROFILE_V2 else CHECKPOINT_SCHEMA) if semantic else SEMANTIC_SCHEMA
            if cp["semantic_schema_version"] != expected_schema or cp["source_prefix_ref"] != t["source_prefix_ref"]:
                raise ValueError("checkpoint_contract_changed")
            if semantic:
                if cp.get("semantic_profile") != semantic or not cp.get("semantic_snapshot"):
                    raise ValueError("semantic_saved_snapshot_required")
                semantic_input = SemanticInput("RESUME_ADOPTED", snapshot_json=cp["semantic_snapshot"], semantic_profile=semantic)
                restored = await asyncio.to_thread(self.engine.prepare_emlis_update,
                    _request(snapshot, checkpoint_ref=cp["checkpoint_id"]), semantic_input=semantic_input)
                if _json(restored) != cp:
                    raise ValueError("semantic_saved_checkpoint_mismatch")
            update = cp.get("answer_update")
            if update and update["disposition"] == "NO_MATERIAL_UPDATE":
                previous = _find(snapshot, t.get("last_observation_event_id"))
                valid = previous and (t["data"]["runtime_profile"] == RUNTIME_PROFILE or (
                    previous["payload"].get("effective_plan_ref") == cp["base_meaning_ref"]
                    and previous["payload"].get("context_ref") == _context_ref(snapshot)))
                return await self._finish(user_id, snapshot, body_state="UNCHANGED" if valid else "UNAVAILABLE", state="COMPLETED")
            if update and update["disposition"] == "UNRESOLVED":
                return await self._finish(user_id, snapshot, body_state="ANSWER_UNREFLECTED", state="COMPLETED")
            self._require_write()
            outcome = await asyncio.to_thread(self.engine.generate, _request(snapshot, checkpoint_ref=cp["checkpoint_id"]),
                **({"semantic_input":semantic_input} if semantic else {}))
            if _json(outcome.meaning_checkpoint) != cp:
                raise ValueError("checkpoint_body_mismatch")
            if outcome.artifact is None:
                safety = outcome.status is EngineStatus.SEPARATE_SAFETY
                return await self._finish(user_id, snapshot, body_state=outcome.body_state,
                    state="COMPLETED" if safety else "RESPONSE_FAILED",
                    failure="separate_safety_owner_required" if safety else "body_not_validated")
            artifact = outcome.artifact
            from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning, build_updated_grounded_plan, _base_ref
            prepared = prepare_emlis_meaning(_request(snapshot, checkpoint_ref=cp["checkpoint_id"]),
                **({"semantic_input":semantic_input} if semantic else {}))
            effective_ref = cp["base_meaning_ref"] if semantic and semantic == MODEL_PROFILE else _base_ref(prepared.thread, build_updated_grounded_plan(prepared))
            observation = _event("OBSERVATION", {"text": artifact.text,
                "effective_plan_ref":effective_ref, "context_guards":t["data"].get("context_guards", []), "context_ref":_context_ref(snapshot),
                "stage": "REFINED" if t.get("latest_answer_event_id") else "INITIAL",
                "meaning_checkpoint_ref": cp["checkpoint_id"], "source_prefix_ref": cp["source_prefix_ref"],
                "artifact": artifact, "meaning_graph": outcome.meaning_graph}, t)
            next_question = outcome.question if t["data"].get("receive_emlis_questions", True) else None
            followup = bool(next_question and t.get("latest_answer_event_id"))
            question = _event("QUESTION", next_question, t, question_id=next_question.question_id) if next_question and not followup else None
            if followup:
                snapshot = copy.deepcopy(snapshot)
                snapshot["thread"]["data"]["continuation_question"] = _json(next_question)
            body_state = ("FINAL" if outcome.body_state == "PRE_QUESTION" and next_question is None
                else outcome.body_state)
            return await self._finish(user_id, snapshot, body_state=body_state,
                state="AWAITING_ANSWER" if question else "AWAITING_CONTINUE" if followup else "COMPLETED", observation=observation, question=question)
        except asyncio.CancelledError:
            # Cancellation confirms the worker stopped before a further commit.
            # Only the active, unexpired attempt may record this fact.
            try:
                await asyncio.shield(self._record_failure(user_id, snapshot, attempt, "worker_interrupted", paused=not self._writable()))
            except Exception:
                pass
            raise
        except ThreadStoreError as exc:
            if exc.code in {"semantic_candidate_acquisition_incomplete", "semantic_candidate_source_unavailable"}:
                # STARTED may already have advanced the revision inside the
                # acquisition call. Close only this still-current attempt,
                # using its saved revision rather than the caller's snapshot.
                fresh = await self._hydrate(user_id, await self.store.read(user_id, thread_id=t["id"]))
                _check(fresh)
                if fresh["thread"]["active_attempt_id"] != attempt:
                    return self._dto(fresh)
                return await self._semantic_unadopted(user_id, fresh, "HOLD", exc.code, None)
            if exc.code == "application_paused":
                return await self._record_failure(user_id, snapshot, attempt, "worker_interrupted", paused=True)
            if exc.transient:
                return await self._record_failure(user_id, snapshot, attempt, exc.code)
            raise
        except ValueError as exc:
            if str(exc) == "separate_safety_owner_required":
                return await self._finish(user_id, snapshot, body_state="ANSWER_UNREFLECTED",
                    state="COMPLETED", failure="separate_safety_owner_required")
            if str(exc) in {'natural_reply_writer_identity_changed', 'natural_reply_meaning_profile_invalid'}:
                # An old receipt is neither a new-source candidate nor a
                # transient acquisition failure. Preserve it without offering
                # an automatic attempt over different author material.
                return await self._record_failure(user_id, snapshot, attempt, str(exc))
            return await self._record_failure(user_id, snapshot, attempt, "meaning_or_body_unavailable")
        except Exception:
            return await self._record_failure(user_id, snapshot, attempt, "meaning_or_body_unavailable")

    async def _record_failure(self, user_id, snapshot, attempt, reason, *, paused=False):
        fresh = await self.store.read(user_id, thread_id=snapshot["thread"]["id"])
        _check(fresh)
        if fresh["thread"]["active_attempt_id"] != attempt:
            return self._dto(await self._hydrate(user_id, fresh))
        await self._finish(user_id, fresh, body_state=fresh["thread"]["data"]["body_state"],
                                  state="RESPONSE_FAILED", failure=reason, paused=paused or not self._writable())
        # Save failure before refreshing optional paid context, so context outages
        # cannot leave an otherwise finished attempt running.
        return await self.get(user_id, fresh["original"]["id"])

    async def _finish(self, user_id, snapshot, *, body_state, state, failure=None, observation=None, question=None, paused=False):
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
        if paused:
            # Sole policy exception: close the already admitted attempt. No new
            # answer, meaning, body, question, context or frame write is allowed.
            if (observation or question or failure not in {"worker_interrupted", "storage_temporarily_unavailable", "meaning_or_body_unavailable"}
                    or state != "RESPONSE_FAILED" or body_state != snapshot["thread"]["data"]["body_state"]):
                raise ValueError("invalid_pause_receipt")
            saved = await self.store.commit(user_id, snapshot, t, events, finishing_attempt=attempt)
            return self._dto(saved)
        return self._dto(await self._commit(user_id, snapshot, t, events, finishing_attempt=attempt))

