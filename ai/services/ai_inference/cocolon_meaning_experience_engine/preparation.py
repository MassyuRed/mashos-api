"""P1 internal material projection and unadopted candidate receipt.

Pure offline functions, deliberately unconnected to Engine/service/persistence.
Source admission is not semantic admission. A matching quotation proves only
its location, never the candidate's interpretation, safety or product quality.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math

from .contracts import GenerationRequest
from .emlis_thread_source import admit_emlis_thread

SCHEMA = "cocolon.cmee.internal_preparation.v1"
POLICIES = {
    "source": "Original, supplemental, history and generated interpretation stay separate.",
    "meaning": "Preserve subject, time, polarity, relations, unknowns and conflicts.",
    "adoption": "NOT_ADOPTED; source quotation checks do not validate interpretation.",
    "cross_core": "Generated observations, Piece prose and Analysis claims are not user sources.",
}
OUTPUT_CONDITIONS = {
    "emlis": "Observation, human reception and optional question have separate responsibilities; preserve the actual question budget.",
    "piece": "Preserve the person's voice, negations and conditions; existing owners retain format, recipe, fit and export responsibilities.",
    "analysis": "Only source-supported period nodes, edges, unknowns and conflicts; do not fill missing roles or predict outcomes.",
}


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


@dataclass(frozen=True, slots=True, repr=False)
class PreparedRequest:
    """Private immutable material; payload() returns a detached working copy."""
    request_id: str
    private_json: str

    def payload(self):
        return json.loads(self.private_json)


@dataclass(frozen=True, slots=True, repr=False)
class CandidateReceipt:
    request_id: str
    status: str
    raw_output: str | None
    candidate_json: str | None
    metadata_json: str

    @property
    def adoption_state(self):
        return "NOT_ADOPTED"


def _prepare(material):
    if material["tier"] not in {"free", "plus", "premium"}:
        raise ValueError("preparation_tier_invalid")
    sources = material["sources"]
    if not sources or len({s["source_id"] for s in sources}) != len(sources):
        raise ValueError("preparation_source_identity_invalid")
    value = dict(material, schema_version=SCHEMA, policies=POLICIES,
                 output_conditions=OUTPUT_CONDITIONS[material["core"]],
                 adoption_state="NOT_ADOPTED", execution_mode="OFFLINE_PREPARATION")
    frozen = _json(value)
    return PreparedRequest("prep-" + hashlib.sha256(frozen.encode()).hexdigest(), frozen)


def _text_source(frozen, original, *, role, parent_record_id=None):
    envelope = frozen.envelope
    fields = ({"memo": original.get("memo"), "memo_action": original.get("memo_action")}
              if original is not None else
              {"answer_text_private": frozen.source.answer_text_private})
    evidence = []
    for ref in frozen.evidence_refs:
        # Structured selection refs are retained as native locators. They do
        # not acquire a synthetic sentence or an inferred feeling proposition.
        item = asdict(ref)
        item.update(literal=envelope.raw_utf8[ref.utf8_start:ref.utf8_end].decode(),
                    coordinate_space="SOURCE_ENVELOPE")
        evidence.append(item)
    return dict(source_id=envelope.source_record_id,
                source_version=envelope.source_schema_version,
                role=role, native_source_role=envelope.source_role,
                envelope_id=envelope.envelope_id,
                source_commitment=envelope.raw_sha256,
                original=original, text_fields=fields, evidence=evidence,
                recorded_at=(original.get("created_at") if original is not None
                             else frozen.source.recorded_at),
                parent_record_id=parent_record_id)


def prepare_emlis(request, *, supplemental_probe=None):
    """Use the existing native source owner without preparing finite meanings.

    supplemental_probe is a fixed, synthetic material experiment only. It has
    no question/thread authority and can never be counted as an actual answer.
    Real native answers continue to pass admit_emlis_thread's parent checks.
    """
    if type(request) is not GenerationRequest or request.core_id != "emlis_ai":
        raise ValueError("preparation_emlis_request_invalid")
    thread = admit_emlis_thread(request)
    raw = request.current_input_bundle.raw_current_input
    sources = [_text_source(thread.original, raw, role="ORIGINAL_INPUT")]
    sources.extend(_text_source(a, None, role="SUPPLEMENTAL_ANSWER",
                                parent_record_id=raw["id"]) for a in thread.answers)
    history_groups = []
    for history in thread.control.admitted_history:
        past_request = history.request
        if (past_request.emlis_thread.admitted_history
                or past_request.emlis_thread.original_source_ref == thread.control.original_source_ref):
            raise ValueError("owned_history_recursive_or_current")
        past = admit_emlis_thread(past_request)
        original = past_request.current_input_bundle.raw_current_input
        group = [_text_source(past.original, original, role="HISTORY_ORIGINAL_INPUT")]
        group.extend(_text_source(a, None, role="HISTORY_SUPPLEMENTAL_ANSWER",
                                  parent_record_id=original["id"]) for a in past.answers)
        sources.extend(group)
        history_groups.append(dict(source_guard=history.source_guard,
            recorded_at=history.recorded_at, source_ids=[s["source_id"] for s in group]))
    control = asdict(thread.control.question_control_context)
    control.update(current_round=thread.control.current_round,
                   capability=thread.control.capability_snapshot,
                   history_groups=history_groups,
                   rejected_frame_keys=thread.control.rejected_frame_keys,
                   frame_feedback=[asdict(f) for f in thread.control.frame_feedback_sources],
                   probe_only=False)
    control["actual_question_budget_remaining"] = (0 if control["stop"] else max(
        0, control["question_limit"] - control["issued_count"]))
    task = "EMLIS_ANSWER_MATERIAL" if thread.answers else "EMLIS_INITIAL_MATERIAL"
    if supplemental_probe is not None:
        probe = supplemental_probe
        if (thread.answers or control["pending_question"] is not None
                or type(probe) is not dict
                or set(probe) != {"source_id", "source_role", "parent_record_id", "text"}
                or probe["source_role"] != "SUPPLEMENTAL_ANSWER"
                or probe["parent_record_id"] != raw["id"]
                or type(probe["source_id"]) is not str or not probe["source_id"]
                or type(probe["text"]) is not str or not probe["text"].strip()):
            raise ValueError("preparation_supplemental_probe_invalid")
        sources.append(dict(source_id=probe["source_id"], source_version=None,
            role="SUPPLEMENTAL_PROBE", native_source_role=probe["source_role"],
            original=None, text_fields={"answer_text_private": probe["text"]},
            envelope_id=None, recorded_at=None, evidence=[],
            parent_record_id=raw["id"], thread_answer_admitted=False))
        task = "EMLIS_SUPPLEMENTAL_MATERIAL_PROBE"
        control.update(probe_only=True,
                       probe_question_budget_remaining=0,
                       actual_update_status="N_A_NO_ACTUAL_PENDING_QUESTION")
    tier = {"FREE_Q1": "free", "Q3_FREE": "free", "Q3_PLUS": "plus",
            "Q3_PREMIUM": "premium"}[thread.control.capability_snapshot]
    return _prepare(dict(core="emlis", task=task, tier=tier, sources=sources,
                         period=None, control=control))


def prepare_piece(source, *, expected_owner_id, tier):
    from .preparation_sources import piece_material
    return _prepare(piece_material(source, expected_owner_id=expected_owner_id, tier=tier))


def prepare_analysis(request, *, tier):
    from .preparation_sources import analysis_material
    return _prepare(analysis_material(request, tier=tier))


def _unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate_json_key")
        value[key] = item
    return value


def _candidate(raw):
    def invalid_constant(_):
        raise ValueError("non_finite_json")
    obj = json.loads(raw, object_pairs_hook=_unique_object, parse_constant=invalid_constant)
    if (type(obj) is not dict or set(obj) != {"candidate", "evidence"}
            or type(obj["candidate"]) is not dict or not obj["candidate"]
            or type(obj["evidence"]) is not list or not obj["evidence"]):
        raise ValueError("candidate_shape_invalid")
    return obj


def _check_evidence(request, candidate):
    sources = {s["source_id"]: s for s in request.payload()["sources"]}
    for ref in candidate["evidence"]:
        if type(ref) is not dict or set(ref) != {"source_id", "field_path", "start", "end", "quote"}:
            return False
        if type(ref["source_id"]) is not str or type(ref["field_path"]) is not str:
            return False
        source = sources.get(ref["source_id"])
        text = source["text_fields"].get(ref["field_path"]) if source else None
        start, end = ref["start"], ref["end"]
        if (type(text) is not str or type(start) is not int or type(end) is not int
                or not 0 <= start < end <= len(text) or type(ref["quote"]) is not str
                or text[start:end] != ref["quote"]):
            return False
    return True


def receive_candidate(request, *, request_id, raw_output, finish_reason,
                      provider=None, model=None, revision=None, usage=None,
                      elapsed_seconds=None):
    """Retain raw response/metadata; nothing here adopts or generates meaning.

    No provider is called. Timeout/length/error always dominate parse success;
    partial candidate JSON may be retained but cannot become normal success.
    """
    if (type(request) is not PreparedRequest or request_id != request.request_id
            or request.request_id != "prep-" + hashlib.sha256(request.private_json.encode()).hexdigest()):
        raise ValueError("preparation_response_request_mismatch")
    if raw_output is not None and type(raw_output) is not str:
        raise ValueError("preparation_raw_output_invalid")
    if any(v is not None and type(v) is not str for v in (provider, model, revision, finish_reason)):
        raise ValueError("preparation_metadata_invalid")
    if (elapsed_seconds is not None and
            (type(elapsed_seconds) not in (int, float) or not math.isfinite(elapsed_seconds)
             or elapsed_seconds < 0)):
        raise ValueError("preparation_elapsed_invalid")
    if usage is not None and (type(usage) is not dict or any(
            type(k) is not str or (v is not None and (type(v) is not int or v < 0))
            for k, v in usage.items())):
        raise ValueError("preparation_usage_invalid")
    candidate = None
    if raw_output is None or not raw_output.strip():
        status = "EMPTY"
    else:
        try:
            candidate = _candidate(raw_output)
            # JSON exponent overflow and unpaired Unicode are not candidates.
            _json(candidate).encode("utf-8")
            status = "CANDIDATE_UNREVIEWED" if _check_evidence(request, candidate) else "INVALID_EVIDENCE"
        except (ValueError, TypeError, RecursionError, UnicodeError):
            candidate = None
            status = "INVALID_FORMAT"
    override = {"timeout": "TIMEOUT", "length": "TOKEN_LIMIT", "error": "PROVIDER_ERROR"}
    if finish_reason in override:
        status = override[finish_reason]
    elif finish_reason != "stop":
        status = "UNKNOWN_FINISH"
    metadata = dict(provider=provider, model=model, revision=revision, usage=usage,
                    finish_reason=finish_reason, elapsed_seconds=elapsed_seconds,
                    evidence_check="LOCATION_ONLY_NOT_SEMANTIC_ADMISSION")
    return CandidateReceipt(request_id, status, raw_output,
                            _json(candidate) if candidate is not None else None, _json(metadata))
