"""Bounded offline Emlis semantic admission, distinct from source admission.

No model, I/O, alternate author, or legacy-parser fallback. The receipt remains
unadopted; this owner makes a separate provisional decision and freezes it.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import hashlib
import json
import re

import emlis_ai_grounded_observation_plan as gp
from emlis_ai_evidence_ledger_service import EvidenceLedgerValidationReport
from emlis_ai_safety_triage import classify_emlis_safety_triage_text, TRIAGE_SAFE_OBSERVATION

from .contracts import ExecutionMode
from .emlis_answer_update import PreparedEmlisMeaning, _base_ref
from .emlis_thread_contracts import (EmlisMeaningCheckpointV1, AnswerMeaningUpdateV1,
    EmlisAnswerUpdateItemV1, AnswerTemporalBindingV1, EmlisQuestionControlV1,
    EmlisQuestionDecisionV1, EmlisClarificationV1)
from .emlis_thread_source import admit_emlis_thread, identity
from .preparation import prepare_emlis, receive_candidate, CandidateReceipt

PROFILE = "emlis_candidate_snapshot.v1"
SCHEMA = "cocolon.cmee.emlis_semantic_snapshot.v1"
CHECKPOINT_SCHEMA = "cocolon.cmee.emlis_answer_meaning.v2"
CANDIDATE_SCHEMA = "cocolon.cmee.semantic_mapping_proposal.v1"
_CLAIM_KEYS = {"claim_id", "kind", "text", "subject", "predicate", "polarity",
               "modality", "about_time", "qualifiers", "evidence_indexes"}
_PUNCT = re.compile(r"[\s。、，,.！？!?「」『』]+")
_FEELING = re.compile(r"(?:嬉し|うれし|寂し|さびし|悲し|苦し|つら|辛|怖|こわ|重|楽し|軽)(?:い|かった|くない|くなかった)(?:です)?$")


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


@dataclass(frozen=True, slots=True, repr=False)
class SemanticInput:
    mode: str
    receipt: CandidateReceipt | None = None
    snapshot_json: str | None = None
    prior_snapshot_json: str | None = None


@dataclass(frozen=True, slots=True, repr=False)
class SnapshotCheckpoint(EmlisMeaningCheckpointV1):
    semantic_schema_version: str = CHECKPOINT_SCHEMA
    semantic_profile: str = PROFILE
    semantic_snapshot: str = ""
    snapshot_ref: str = ""


@dataclass(frozen=True, slots=True, repr=False)
class SnapshotPreparedMeaning(PreparedEmlisMeaning):
    semantic_snapshot: str = ""
    semantic_material_json: str = ""


class SemanticNotAdopted(ValueError):
    def __init__(self, decision, code, receipt=None):
        super().__init__(code)
        self.decision, self.reason_code, self.receipt = decision, code, receipt


def _fail(decision, code):
    raise SemanticNotAdopted(decision, code)


def _keys(value, keys):
    if type(value) is not dict or set(value) != set(keys):
        _fail("REJECT", "semantic_shape_invalid")


def _refs(value, size):
    if type(value) is not list or not value or any(
            type(i) is not int or not 0 <= i < size for i in value) or len(set(value)) != len(value):
        _fail("REJECT", "semantic_evidence_index_invalid")
    return value


def _source_binding(material):
    return [{k: s[k] for k in ("source_id", "source_version", "role", "envelope_id", "source_commitment")}
            for s in material.payload()["sources"]]


def _semantic_ref(payload):
    # Execution diagnostics and raw JSON formatting are deliberately excluded.
    semantic = {k: payload[k] for k in ("schema_version", "semantic_profile", "admission_version",
        "adapter_version", "request_ref", "source_prefix_ref", "source_bindings", "packet", "prior_ref",
        "answer_count", "question_control", "claim_mapping")}
    return "semantic-" + hashlib.sha256(_json(semantic).encode()).hexdigest()


def _decode_question(q):
    if q is None:
        return None
    q = dict(q)
    d = dict(q.pop("decision"))
    for k in ("supporting_evidence_refs", "affected_meaning_refs", "affected_reception_refs", "asked_target_refs"):
        d[k] = tuple(d[k])
    return EmlisClarificationV1(decision=EmlisQuestionDecisionV1(**d), **q)


def _control(payload):
    d = dict(payload)
    d["pending_question"] = _decode_question(d["pending_question"])
    d["issued_questions"] = tuple(_decode_question(q) for q in d["issued_questions"])
    d["asked_target_refs"] = tuple(d["asked_target_refs"])
    return EmlisQuestionControlV1(**d)


def _thread_at(thread, payload):
    count = payload["answer_count"]
    control = replace(thread.control, answers=thread.control.answers[:count], current_round=count,
        question_control_context=_control(payload["question_control"]), prepared_meaning_checkpoint_ref=None)
    return replace(thread, control=control, answers=thread.answers[:count], source_prefix_ref=payload["source_prefix_ref"])


def snapshot_question(thread, plan, snapshot_json, *, parent_request_id, respect_control=True):
    from .emlis_question import question_candidate
    decision, question = question_candidate(thread, plan, parent_request_id=parent_request_id,
                                           respect_control=respect_control)
    if question:
        ref = json.loads(snapshot_json)["snapshot_ref"]
        question = replace(question, question_id=identity("semantic-question", question.question_id, ref))
    return decision, question


def _locate(thread, material, evidence):
    sources = {s["source_id"]: s for s in material.payload()["sources"]}
    rows = []
    resolver = thread.resolver()
    for e in evidence:
        source = sources[e["source_id"]]
        matches = [q for q in resolver.qualified_refs
            if q.source_envelope_id == source["envelope_id"]
            and q.evidence.field_path == e["field_path"]
            and q.evidence.scalar_start <= e["start"] < e["end"] <= q.evidence.scalar_end]
        if len(matches) != 1:
            _fail("UNSUPPORTED", "semantic_subrange_crosses_native_span")
        q = matches[0]
        span = resolver.resolve(q.thread_span_id)
        # Fragment locators are into the native normalized span, not envelope bytes.
        local_start = e["start"] - q.evidence.scalar_start
        local_end = e["end"] - q.evidence.scalar_start
        if gp._clean(span.raw_text)[local_start:local_end] != e["quote"]:
            _fail("UNSUPPORTED", "semantic_normalized_coordinate_unsupported")
        rows.append((q, local_start, local_end))
    return rows


def _validate_packet(packet, material, thread):
    _keys(packet, {"candidate", "evidence"})
    c, ev = packet["candidate"], packet["evidence"]
    _keys(c, {"schema_version", "core", "claims", "relations", "unknowns", "conflicts", "updates"})
    if c["schema_version"] != CANDIDATE_SCHEMA or c["core"] != "emlis":
        _fail("REJECT", "semantic_core_or_schema_invalid")
    if any(type(c[k]) is not list for k in ("claims", "relations", "unknowns", "conflicts", "updates")):
        _fail("REJECT", "semantic_collection_invalid")
    if c["unknowns"] or c["conflicts"]:
        _fail("UNSUPPORTED", "semantic_unknown_or_conflict_not_projectable")
    if not c["claims"] or len(c["claims"]) > 16:
        _fail("UNSUPPORTED", "semantic_claim_count_not_supported")
    ids, anchors = [], []
    for claim in c["claims"]:
        _keys(claim, _CLAIM_KEYS)
        cid = claim["claim_id"]
        if type(cid) is not str or not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", cid) or cid in ids:
            _fail("REJECT", "semantic_claim_id_invalid")
        ids.append(cid)
        refs = _refs(claim["evidence_indexes"], len(ev))
        if len(refs) != 1 or claim["text"] != ev[refs[0]]["quote"]:
            _fail("UNSUPPORTED", "semantic_claim_anchor_not_atomic")
        anchor = ev[refs[0]]
        if any(anchor["source_id"] == old["source_id"] and anchor["field_path"] == old["field_path"]
                and anchor["start"] < old["end"] and old["start"] < anchor["end"] for old in anchors):
            _fail("REJECT", "semantic_claim_anchor_overlap")
        anchors.append(anchor)
        _keys(claim["subject"], {"binding", "source_entity", "evidence_indexes"})
        sub = claim["subject"]
        if sub["binding"] == "EXPLICIT":
            if sub["source_entity"] not in {"私", "自分", "わたし", "僕", "俺"}:
                _fail("HOLD", "semantic_subject_not_self_bound")
            _refs(sub["evidence_indexes"], len(ev))
            if not any(sub["source_entity"] in ev[i]["quote"] for i in sub["evidence_indexes"]):
                _fail("REJECT", "semantic_subject_evidence_invalid")
        elif sub != {"binding": "OMITTED", "source_entity": None, "evidence_indexes": []}:
            _fail("HOLD", "semantic_subject_unresolved")
        _keys(claim["predicate"], {"surface", "arguments"})
        if (claim["predicate"]["arguments"] or claim["qualifiers"]):
            _fail("UNSUPPORTED", "semantic_argument_or_qualifier_not_projectable")
        if type(claim["predicate"]["surface"]) is not str or not claim["predicate"]["surface"] or claim["predicate"]["surface"] not in claim["text"]:
            _fail("REJECT", "semantic_predicate_anchor_invalid")
        if claim["kind"] not in {"EVENT", "STATE"}:
            _fail("UNSUPPORTED", "semantic_kind_not_projectable")
        _keys(claim["polarity"], {"value", "scope_refs", "evidence_indexes"})
        _refs(claim["polarity"]["evidence_indexes"], len(ev))
        if claim["polarity"]["scope_refs"] != [cid] or claim["polarity"]["value"] not in {"AFFIRMED", "NEGATED"}:
            _fail("UNSUPPORTED", "semantic_polarity_scope_not_projectable")
        _keys(claim["modality"], {"value", "evidence_indexes"})
        _refs(claim["modality"]["evidence_indexes"], len(ev))
        if claim["modality"]["value"] != "ASSERTED_AS_WRITTEN":
            _fail("UNSUPPORTED", "semantic_modality_not_projectable")
        _keys(claim["about_time"], {"kind", "expression", "anchor_source_id", "evidence_indexes"})
        _refs(claim["about_time"]["evidence_indexes"], len(ev))
        if claim["about_time"]["kind"] not in {"WRITTEN_PAST_UNRESOLVED_OCCASION", "ANSWER_TIME", "ORIGINAL_OCCASION"}:
            _fail("UNSUPPORTED", "semantic_time_not_projectable")
        if re.search(r"[「」『』]|(?:彼|彼女|上司|母|父)(?:は|が)|もし|なら|たら|という|と言|らしい|かもしれ", claim["text"]):
            _fail("UNSUPPORTED", "semantic_embedded_scope_not_projectable")
        predicate = claim["predicate"]["surface"]
        if claim["kind"] == "STATE" and not _FEELING.fullmatch(predicate):
            _fail("UNSUPPORTED", "semantic_native_feeling_lexeme_unsupported")
        if claim["kind"] == "STATE" and not re.fullmatch(
                r"(?:(?:私|自分|わたし|僕|俺)(?:は|も|には))?"
                r"(?:(?:その時|あの時|当時|今|現在)(?:は|も)?)?"
                r"(?:本当は|少し|とても|まだ|全然|あまり)?(?:帰宅しても)?" + re.escape(predicate), claim["text"]):
            _fail("HOLD", "semantic_subject_or_unprojected_clause")
        if sub["binding"] == "EXPLICIT" and (not claim["text"].startswith(sub["source_entity"])
                or any(ev[i]["source_id"] != ev[refs[0]]["source_id"]
                       or ev[i]["field_path"] != ev[refs[0]]["field_path"]
                       or not ev[refs[0]]["start"] <= ev[i]["start"] < ev[i]["end"] <= ev[refs[0]]["end"]
                       for i in sub["evidence_indexes"])):
            _fail("HOLD", "semantic_self_subject_not_claim_bound")
        if claim["kind"] == "EVENT" and not re.fullmatch(r"(?:(?:私|自分|わたし)(?:は|が))?(?:褒められ|ほめられ|言われ|頼まれ|誘われ|断られ)(?:た|ました)", claim["text"]):
            _fail("UNSUPPORTED", "semantic_native_event_lexeme_unsupported")
    relids = []
    for r in c["relations"]:
        _keys(r, {"relation_id", "type", "from_claim_id", "to_claim_id", "polarity", "scope_refs", "qualifiers", "evidence_indexes"})
        if r["relation_id"] in relids or r["relation_id"] in ids:
            _fail("REJECT", "semantic_relation_id_invalid")
        relids.append(r["relation_id"])
        _refs(r["evidence_indexes"], len(ev))
        if r["from_claim_id"] not in ids or r["to_claim_id"] not in ids or r["from_claim_id"] == r["to_claim_id"]:
            _fail("REJECT", "semantic_relation_endpoint_invalid")
        if r["type"] != "SOURCE_WRITTEN_CONCESSION" or r["polarity"] != "AFFIRMED" or r["qualifiers"] or r["scope_refs"] != [r["relation_id"]]:
            _fail("UNSUPPORTED", "semantic_relation_scope_not_projectable")
        if len(r["evidence_indexes"]) != 1 or ev[r["evidence_indexes"][0]]["quote"] not in {"のに", "けど", "けれど", "けれども"}:
            _fail("UNSUPPORTED", "semantic_relation_marker_not_atomic")
    return _locate(thread, material, ev)


def _nuclei(packet, material, thread):
    c, ev = packet["candidate"], packet["evidence"]
    locations = _validate_packet(packet, material, thread)
    contrasts = {r["from_claim_id"]: (r, "before") for r in c["relations"]}
    contrasts.update({r["to_claim_id"]: (r, "after") for r in c["relations"]})
    rows, mapping = [], {}
    for claim in c["claims"]:
        cid = claim["claim_id"]
        i = claim["evidence_indexes"][0]
        q, start, end = locations[i]
        field = ev[i]["field_path"]
        if field not in {"memo", "memo_action", "answer_text_private"}:
            _fail("REJECT", "semantic_claim_source_role_invalid")
        source = next(s for s in material.payload()["sources"] if s["source_id"] == ev[i]["source_id"])
        if source["role"] not in {"ORIGINAL_INPUT", "SUPPLEMENTAL_ANSWER"}:
            _fail("UNSUPPORTED", "semantic_history_claim_not_current_source")
        if source["role"] == "ORIGINAL_INPUT" and claim["about_time"] != {
                "kind":"WRITTEN_PAST_UNRESOLVED_OCCASION", "expression":None,
                "anchor_source_id":None, "evidence_indexes":claim["about_time"]["evidence_indexes"]}:
            _fail("HOLD", "semantic_original_time_not_bound")
        native_id = identity("semantic-nucleus", q.source_envelope_id, cid, ev[i])
        mapping[cid] = native_id
        kind = "event" if claim["kind"] == "EVENT" else "reaction"
        pred = claim["predicate"]["surface"]
        polarity = "neutral" if kind == "event" else "negative" if re.search(r"くない|くなかった|寂|さび|悲|苦|つら|辛|怖|こわ|重", pred) else "positive"
        if (claim["polarity"]["value"] == "NEGATED") != bool(re.search(r"くない|くなかった", pred)):
            _fail("HOLD", "semantic_claim_polarity_not_bound")
        time = "present" if claim["about_time"]["kind"] == "ANSWER_TIME" else "past"
        written_past = bool(re.search(r"(?:かった|ました|た)(?:です)?$", pred))
        if written_past != (time == "past"):
            _fail("HOLD", "semantic_predicate_time_not_bound")
        attrs = ["semantic_role:generic_relation_fragment", f"source_fragment_scalar_range:{start}:{end}",
            "source_fragment_scalar_source:normalized_raw_text", "time_scope:" + time]
        if kind == "reaction":
            attrs.append("operator:feeling")
        if cid in contrasts:
            rel, side = contrasts[cid]
            attrs += ["semantic_role:final_stage1_compound_meaning", "semantic_role:contrast_" + side]
            marker = ev[rel["evidence_indexes"][0]]["quote"]
            attrs.append("source_received_event_link:" + {"のに":"noni", "けど":"kedo", "けれど":"keredo", "けれども":"keredomo"}[marker])
        if field == "answer_text_private":
            if claim["about_time"]["kind"] not in {"ANSWER_TIME", "ORIGINAL_OCCASION"}:
                _fail("HOLD", "semantic_answer_time_unbound")
            expr = claim["about_time"]["expression"]
            if not expr or expr not in claim["text"] or claim["about_time"]["anchor_source_id"] != source["source_id"]:
                _fail("HOLD", "semantic_answer_time_evidence_missing")
            if not re.match(r"^(?:今|現在)(?:は|も)" if time == "present" else r"^(?:その時|あの時|当時)(?:は|も)?", claim["text"]):
                _fail("HOLD", "semantic_answer_time_expression_unbound")
            attrs += ["thread_time:" + claim["about_time"]["kind"].lower(),
                "lexical:preserve_source_predicate", "lexical:no_new_sensation_family"]
        frame = gp.GroundedSemanticFrame("current_user", "event" if kind == "event" else "feeling",
            polarity, "fact" if kind == "event" else "feeling", time_scope=time, attribute_codes=tuple(attrs))
        rows.append(gp.GroundedSemanticNucleus(native_id, kind, (q.thread_span_id,), (field,), (q.thread_span_id,),
            frame, "explicit", 1.0, 1.0, "required", "explicit_supplemental_answer" if field == "answer_text_private" else "explicit_current_input",
            ("no_unstated_cause", "no_third_party_intention", "no_stable_personality")))
    relations = []
    index = {c["claim_id"]: c for c in c["claims"]}
    for r in c["relations"]:
        left, right = index[r["from_claim_id"]], index[r["to_claim_id"]]
        if left["kind"] != "EVENT" or right["kind"] != "STATE":
            _fail("UNSUPPORTED", "semantic_concession_endpoints_unsupported")
        q, _, _ = locations[r["evidence_indexes"][0]]
        qs = [locations[x["evidence_indexes"][0]][0] for x in (left, right)]
        marker = ev[r["evidence_indexes"][0]]
        a, b = (ev[x["evidence_indexes"][0]] for x in (left, right))
        if any(x.thread_span_id != q.thread_span_id for x in qs) or not (a["end"] <= marker["start"] < marker["end"] <= b["start"]):
            _fail("REJECT", "semantic_relation_marker_binding_invalid")
        relations.append(gp.GroundedSemanticRelation(identity("semantic-relation", q.source_envelope_id, r), "contrast",
            mapping[r["from_claim_id"]], mapping[r["to_claim_id"]], (q.thread_span_id,), "user_stated_relation", 1.0, "required"))
    return tuple(rows), tuple(relations), mapping


def _plan(packet, material, thread, *, extra_relations=(), focus=()):
    nuclei, relations, mapping = _nuclei(packet, material, thread)
    relations += tuple(extra_relations)
    text = "\n".join(str(s["text_fields"].get(f) or "") for s in material.payload()["sources"]
                      for f in s["text_fields"])
    safety = classify_emlis_safety_triage_text(text)
    if safety.safety_triage_kind != TRIAGE_SAFE_OBSERVATION:
        _fail("REJECT", "separate_safety_owner_required")
    complexity = gp._semantic_complexity(nuclei=nuclei, relations=relations, meaning_artifacts=gp._MeaningArtifacts())
    response, coverage, surface, safety_policy = gp._build_response_and_policies(
        nuclei=nuclei, relations=relations, safety_decision=safety, complexity=complexity,
        material_quality="grounded", include_reception_relation_support=True, final_source_fidelity=True,
        primary_focus_nucleus_ids=focus)
    resolver = thread.resolver()
    result = gp.GroundedObservationPlan(gp.GROUND_OBSERVATION_PLAN_SCHEMA_VERSION,
        gp.GROUND_OBSERVATION_PLAN_ADAPTER_VERSION, gp.GROUND_OBSERVATION_PLAN_GENERATION_PATH,
        gp.GroundedInputProfile("text_present", "grounded", complexity, len(nuclei), len(relations), safety.safety_triage_kind),
        nuclei, relations, (), response, coverage, surface, safety_policy,
        EvidenceLedgerValidationReport(True, canonical_span_ids=resolver.span_ids),
        gp._all_plan_evidence_ids(nuclei, relations, ()),
        (gp.FINAL_STAGE1_GROUNDED_PROJECTION_VERSION, PROFILE))
    if gp.validate_grounded_observation_plan(result, resolver):
        _fail("UNSUPPORTED", "semantic_native_plan_not_validated")
    return result, mapping


def _receipt(material, receipt):
    if type(receipt) is not CandidateReceipt:
        _fail("REJECT", "semantic_receipt_required")
    metadata = json.loads(receipt.metadata_json)
    metadata.pop("evidence_check", None)
    replay = receive_candidate(material, request_id=receipt.request_id, raw_output=receipt.raw_output, **metadata)
    if replay != receipt or receipt.status != "CANDIDATE_UNREVIEWED":
        _fail("REJECT", "semantic_receipt_not_validated")
    return json.loads(receipt.candidate_json)


def _restore(request, text):
    try:
        p = json.loads(text)
        _keys(p, {"schema_version", "semantic_profile", "admission_version", "adapter_version",
            "request_ref", "source_prefix_ref", "source_bindings", "packet", "prior_ref", "prior_snapshot",
            "receipt", "answer_count", "question_control", "snapshot_ref", "claim_mapping"})
        if _json(p) != text or p["schema_version"] != SCHEMA or p["semantic_profile"] != PROFILE or p["snapshot_ref"] != _semantic_ref(p):
            raise ValueError()
        thread = admit_emlis_thread(request)
        material = prepare_emlis(request)
        if (p["admission_version"] != "1" or p["adapter_version"] != "1"
            or p["request_ref"] != material.request_id or type(p["answer_count"]) is not int
            or p["answer_count"] != len(thread.answers)
            or p["question_control"] != json.loads(_json(asdict(thread.control.question_control_context)))
            or p["prior_ref"] != (p["prior_snapshot"]["snapshot_ref"] if p["prior_snapshot"] else None)
            or p["source_prefix_ref"] != thread.source_prefix_ref or p["source_bindings"] != _source_binding(material)):
            raise ValueError()
        _receipt(material, CandidateReceipt(**p["receipt"]))
        if p["packet"] != json.loads(p["receipt"]["candidate_json"]):
            raise ValueError()
        return thread, material, p
    except SemanticNotAdopted:
        raise
    except (ValueError, KeyError, TypeError):
        _fail("REJECT", "semantic_snapshot_invalid")


def prepare_snapshot_meaning(request, semantic_input):
    try:
        return _prepare_snapshot_meaning(request, semantic_input)
    except SemanticNotAdopted as exc:
        if type(semantic_input) is SemanticInput:
            exc.receipt = semantic_input.receipt
        raise
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RecursionError):
        raise SemanticNotAdopted("REJECT", "semantic_payload_invalid",
            semantic_input.receipt if type(semantic_input) is SemanticInput else None) from None


def _prepare_snapshot_meaning(request, semantic_input):
    """Adopt once or replay one immutable saved decision; never call a model."""
    if type(semantic_input) is not SemanticInput or request.execution_mode != ExecutionMode.OFFLINE_CANDIDATE.value:
        _fail("REJECT", "semantic_offline_input_required")
    thread, material = admit_emlis_thread(request), prepare_emlis(request)
    if semantic_input.mode == "RESUME_ADOPTED":
        if semantic_input.receipt is not None or semantic_input.prior_snapshot_json is not None or not semantic_input.snapshot_json:
            _fail("REJECT", "semantic_resume_input_invalid")
        thread, material, p = _restore(request, semantic_input.snapshot_json)
    elif semantic_input.mode == "FRESH_CANDIDATE":
        if semantic_input.snapshot_json is not None or request.emlis_thread.prepared_meaning_checkpoint_ref is not None:
            _fail("REJECT", "semantic_same_prefix_readoption_forbidden")
        packet = _receipt(material, semantic_input.receipt)
        p = dict(schema_version=SCHEMA, semantic_profile=PROFILE, admission_version="1", adapter_version="1",
            request_ref=material.request_id, source_prefix_ref=thread.source_prefix_ref,
            source_bindings=_source_binding(material), packet=packet, prior_ref=None,
            prior_snapshot=None, receipt=asdict(semantic_input.receipt), answer_count=len(thread.answers),
            question_control=asdict(thread.control.question_control_context))
        if semantic_input.prior_snapshot_json:
            prior = json.loads(semantic_input.prior_snapshot_json)
            if not thread.answers or prior["answer_count"] != len(thread.answers) - 1 or prior["snapshot_ref"] != _semantic_ref(prior):
                _fail("REJECT", "semantic_prior_snapshot_invalid")
            p.update(prior_ref=prior["snapshot_ref"], prior_snapshot=prior)
        elif thread.answers:
            _fail("REJECT", "semantic_prior_snapshot_required")
        p["claim_mapping"] = _nuclei(packet, material, thread)[2]
        p["snapshot_ref"] = _semantic_ref(p)
    else:
        _fail("REJECT", "semantic_input_mode_invalid")
    try:
        return _prepare_payload(thread, material, p, request)
    except SemanticNotAdopted as exc:
        exc.receipt = semantic_input.receipt
        raise
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RecursionError):
        raise SemanticNotAdopted("REJECT", "semantic_payload_invalid", semantic_input.receipt) from None


def _prepare_payload(thread, material, p, request):
    prior = p["prior_snapshot"]
    packet = p["packet"]
    updates = packet["candidate"]["updates"]
    if bool(prior) != bool(thread.answers):
        _fail("REJECT", "semantic_snapshot_lineage_invalid")
    original_p = p
    while original_p["prior_snapshot"]:
        original_p = original_p["prior_snapshot"]
    original_thread = _thread_at(thread, original_p)
    # Source-only material for the same original source; no legacy meaning parser.
    original_req = replace(request, emlis_thread=original_thread.control)
    original_material = prepare_emlis(original_req)
    if original_p["source_bindings"] != _source_binding(original_material):
        _fail("REJECT", "semantic_original_snapshot_binding_invalid")
    original_plan, _ = _plan(original_p["packet"], original_material, original_thread)
    current_plan, mapping = _plan(packet, material, thread)
    if p["claim_mapping"] != mapping:
        _fail("REJECT", "semantic_claim_mapping_mismatch")
    accepted, inactive, update_items, extras = (), (), [], []
    if prior:
        prior_thread = _thread_at(thread, prior)
        prior_req = replace(request, emlis_thread=prior_thread.control)
        _, prior_material, checked_prior = _restore(prior_req, _json(prior))
        prior_prepared = _prepare_payload(prior_thread, prior_material, checked_prior, prior_req)
        prior_plan = derive_snapshot_plan(prior_prepared)
        actual = thread.control.question_control_context.pending_question
        _, canonical = snapshot_question(prior_thread, prior_plan, _json(prior), parent_request_id=actual.parent_request_id)
        if actual != canonical:
            _fail("REJECT", "semantic_question_noncanonical")
        before = {c["claim_id"]: c for c in prior["packet"]["candidate"]["claims"]}
        now = {c["claim_id"]: c for c in packet["candidate"]["claims"]}
        prior_mapping = _nuclei(prior["packet"], prior_material, prior_thread)[2]
        prior_nodes = {n.nucleus_id: n for n in prior_plan.nuclei}
        removed, added, affected = set(), set(), []
        answer = thread.answers[-1]
        for u in updates:
            _keys(u, {"operation", "target_claim_refs", "new_claim_refs", "answer_source_id", "prior_meaning_ref"})
            operation, targets, new = u["operation"], u["target_claim_refs"], u["new_claim_refs"]
            if (operation not in {"ADD", "REVISE", "WITHDRAW"} or not targets or len(set(targets)) != len(targets)
                or not set(targets) <= before.keys() or not set(new) <= now.keys()
                or set(new) & before.keys() or u["answer_source_id"] != answer.source.answer_id or u["prior_meaning_ref"] != prior["snapshot_ref"]):
                _fail("REJECT", "semantic_update_binding_invalid")
            target_ids = tuple(prior_mapping[c] for c in targets)
            if operation == "ADD" and not set(target_ids) <= set(actual.decision.affected_meaning_refs):
                _fail("HOLD", "semantic_add_target_not_pending")
            if (operation == "WITHDRAW") != (not new):
                _fail("REJECT", "semantic_update_replacement_invalid")
            if operation == "REVISE" and (len(targets) != 1 or len(new) != 1 or "書き方を間違えた" not in answer.source.answer_text_private):
                _fail("UNSUPPORTED", "semantic_revision_not_explicit")
            if operation == "REVISE" and (not set(target_ids) <= set(actual.decision.affected_meaning_refs)
                or any(prior_nodes[t].kind != "reaction" for t in target_ids)
                or any(now[c]["kind"] != "STATE" for c in new)):
                _fail("HOLD", "semantic_revision_target_not_reaction")
            if operation == "WITHDRAW" and any('「' + before[t]["text"].rstrip('。') + '」は誤りです' not in answer.source.answer_text_private for t in targets):
                _fail("HOLD", "semantic_withdrawal_target_not_explicit")
            for cid in new:
                refs = now[cid]["evidence_indexes"]
                if any(packet["evidence"][i]["source_id"] != answer.source.answer_id for i in refs):
                    _fail("REJECT", "semantic_update_not_answer_source")
            about = now[new[0]]["about_time"]["kind"] if new else "ORIGINAL_OCCASION"
            if operation == "REVISE" and about != "ORIGINAL_OCCASION":
                _fail("HOLD", "semantic_revision_time_not_original")
            deps = tuple(r.relation_id for r in prior_plan.relations if r.from_nucleus_id in target_ids or r.to_nucleus_id in target_ids)
            superseded = target_ids if operation != "ADD" else ()
            if operation != "ADD": removed.update(targets)
            added.update(new)
            changed = tuple(mapping[c] for c in new)
            evidence_ids = tuple(q.evidence.evidence_id for q in thread.resolver().qualified_refs if q.source_envelope_id == answer.envelope.envelope_id)
            item = EmlisAnswerUpdateItemV1(identity("semantic-update", p["snapshot_ref"], u),
                "QUESTION_FOCUS" if operation == "ADD" else "EXPLICIT_CORRECTION", target_ids, evidence_ids,
                AnswerTemporalBindingV1(about, thread.original.envelope.envelope_id if about == "ORIGINAL_OCCASION" else answer.envelope.envelope_id,
                    evidence_ids), operation, changed, superseded, deps if superseded else ())
            update_items.append(item)
            if changed:
                focus_id = next((n for n in actual.decision.affected_meaning_refs if n in {x.nucleus_id for x in current_plan.nuclei}), None)
                if focus_id:
                    for nid in changed:
                        sid = next(n.source_span_ids[0] for n in current_plan.nuclei if n.nucleus_id == nid)
                        extras.append(gp.GroundedSemanticRelation(identity("semantic-about", p["snapshot_ref"], nid),
                            "evaluation_about_event", focus_id, nid, (sid,), "user_stated_relation", 1.0, "required"))
        if set(before) - set(now) != removed or set(now) - set(before) != added:
            _fail("REJECT", "semantic_update_coverage_mismatch")
        # Canonical evidence indexes for retained claims must not be rebound.
        for cid in set(before) & set(now):
            if before[cid] != now[cid] or any(prior["packet"]["evidence"][i] != packet["evidence"][i] for i in before[cid]["evidence_indexes"]):
                _fail("REJECT", "semantic_unchanged_claim_modified")
        old_rel = {r["relation_id"]: r for r in prior["packet"]["candidate"]["relations"]}
        expected_rel = [r for r in old_rel.values() if not {r["from_claim_id"], r["to_claim_id"]} & removed]
        if packet["candidate"]["relations"] != expected_rel:
            _fail("REJECT", "semantic_unchanged_relation_modified")
        inactive = tuple(dict.fromkeys((*prior_prepared.checkpoint.inactive_claim_refs,
            *(prior_mapping[t] for t in removed), *(d for item in update_items for d in item.affected_dependency_refs))))
        active_ids = {n.nucleus_id for n in current_plan.nuclei}
        extras = [r for r in prior_plan.relations if r.type == "evaluation_about_event"
            and r.from_nucleus_id in active_ids and r.to_nucleus_id in active_ids
            and r.relation_id not in inactive] + extras
        accepted = tuple(n for n in current_plan.nuclei if n.nucleus_id not in {x.nucleus_id for x in original_plan.nuclei})
        current_plan, mapping = _plan(packet, material, thread, extra_relations=extras,
                                    focus=tuple(n.nucleus_id for n in accepted))
    elif updates:
        _fail("REJECT", "semantic_initial_update_forbidden")
    _coverage(packet, material, thread, prior)
    update = None
    if prior:
        update = AnswerMeaningUpdateV1(thread.answers[-1].envelope.envelope_id,
            thread.control.question_control_context.pending_question.question_id, prior["snapshot_ref"],
            tuple(update_items), (), "MATERIAL_UPDATE" if update_items else "NO_MATERIAL_UPDATE", p["snapshot_ref"])
    cp = SnapshotCheckpoint(identity("semantic-checkpoint", thread.source_prefix_ref, p["snapshot_ref"]),
        thread.source_prefix_ref, _base_ref(thread, prior_plan if prior else original_plan), update, "RESOLVED",
        tuple(dict.fromkeys((*(prior_prepared.checkpoint.accepted_update_refs if prior else ()),
            *(x.update_ref for x in update_items)))), inactive, (), semantic_snapshot=_json(p), snapshot_ref=p["snapshot_ref"])
    if request.emlis_thread.prepared_meaning_checkpoint_ref not in {None, cp.checkpoint_id}:
        _fail("REJECT", "semantic_checkpoint_reference_mismatch")
    return SnapshotPreparedMeaning(thread, original_plan, accepted, cp, semantic_snapshot=_json(p), semantic_material_json=material.private_json)


def _coverage(packet, material, thread, prior):
    """Only actually represented claims/markers cover source, never unused quotes."""
    packets = [packet]
    contexts = [(packet, prior)]
    history = prior
    while history:
        packets.append(history["packet"])
        contexts.append((history["packet"], history["prior_snapshot"]))
        history = history["prior_snapshot"]
    used = []
    for p in packets:
        indexes = [i for c in p["candidate"]["claims"] for i in c["evidence_indexes"]]
        indexes += [i for r in p["candidate"]["relations"] for i in r["evidence_indexes"]]
        used.extend(p["evidence"][i] for i in indexes)
    for source in material.payload()["sources"]:
        if source["role"] not in {"ORIGINAL_INPUT", "SUPPLEMENTAL_ANSWER"}:
            continue
        for field, text in source["text_fields"].items():
            text = text or ""
            remaining = list(text)
            for e in used:
                if e["source_id"] == source["source_id"] and e["field_path"] == field:
                    remaining[e["start"]:e["end"]] = [" "] * (e["end"] - e["start"])
            for candidate_packet, before_snapshot in contexts:
                if not before_snapshot or source["role"] != "SUPPLEMENTAL_ANSWER":
                    continue
                before = {c["claim_id"]: c for c in before_snapshot["packet"]["candidate"]["claims"]}
                for u in candidate_packet["candidate"]["updates"]:
                    if u["answer_source_id"] != source["source_id"]:
                        continue
                    phrases = (["書き方を間違えた"] if u["operation"] == "REVISE" else
                        ['「' + before[t]["text"].rstrip('。') + '」は誤りです' for t in u["target_claim_refs"]]
                        if u["operation"] == "WITHDRAW" else [])
                    for phrase in phrases:
                        for match in re.finditer(re.escape(phrase), text):
                            remaining[match.start():match.end()] = [" "] * len(phrase)
                if not candidate_packet["candidate"]["updates"] and text.strip() in {"わからない。", "わからない", "まだわからない。", "まだわからない"}:
                    remaining = []
            if _PUNCT.sub("", "".join(remaining)):
                _fail("UNSUPPORTED", "semantic_material_not_fully_represented")


def derive_snapshot_plan(prepared):
    """Re-derive expected semantics from the same frozen adopted snapshot."""
    p = json.loads(prepared.semantic_snapshot)
    from .preparation import PreparedRequest
    material = PreparedRequest("prep-" + hashlib.sha256(prepared.semantic_material_json.encode()).hexdigest(), prepared.semantic_material_json)
    if p["snapshot_ref"] != _semantic_ref(p) or p["source_bindings"] != _source_binding(material):
        _fail("REJECT", "semantic_prepared_snapshot_mismatch")
    extras = []
    if p["prior_snapshot"]:
        prior = p["prior_snapshot"]
        prior_thread = _thread_at(prepared.thread, prior)
        from .contracts import GenerationRequest
        from emlis_ai_current_input_bundle import build_emlis_current_input_bundle
        original = next(s["original"] for s in material.payload()["sources"] if s["role"] == "ORIGINAL_INPUT")
        prior_req = GenerationRequest("snapshot-lineage-replay", build_emlis_current_input_bundle(original),
            prior_thread.original.envelope.source_record_id, emlis_thread=prior_thread.control)
        _, prior_material, checked = _restore(prior_req, _json(prior))
        previous = _prepare_payload(prior_thread, prior_material, checked, prior_req)
        active_ids = {n.nucleus_id for n in _plan(p["packet"], material, prepared.thread)[0].nuclei}
        extras = [r for r in derive_snapshot_plan(previous).relations if r.type == "evaluation_about_event"
            and r.from_nucleus_id in active_ids and r.to_nucleus_id in active_ids
            and r.relation_id not in prepared.checkpoint.inactive_claim_refs]
    if prepared.checkpoint.answer_update:
        active = _plan(p["packet"], material, prepared.thread)[0]
        active_ids = {n.nucleus_id for n in active.nuclei}
        q = prepared.thread.control.question_control_context.pending_question
        focus = next((n for n in q.decision.affected_meaning_refs if n in active_ids), None)
        if focus:
            for item in prepared.checkpoint.answer_update.updates:
                for nid in item.changed_claim_refs:
                    sid = next(n.source_span_ids[0] for n in active.nuclei if n.nucleus_id == nid)
                    extras.append(gp.GroundedSemanticRelation(identity("semantic-about", p["snapshot_ref"], nid),
                        "evaluation_about_event", focus, nid, (sid,), "user_stated_relation", 1.0, "required"))
    return _plan(p["packet"], material, prepared.thread, extra_relations=extras,
        focus=tuple(n.nucleus_id for n in prepared.accepted_nuclei))[0]

