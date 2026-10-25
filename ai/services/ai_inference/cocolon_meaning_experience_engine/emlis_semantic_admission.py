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

from .contracts import (ExecutionMode, SnapshotSourceSliceBindingV2, SnapshotCaseArgumentBindingV2,
    SnapshotPersonStatedUnknownBindingV2, SnapshotWrittenLinkBindingV2)
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
CURRENT_ADAPTER_VERSION = "2"
PROFILE_V2 = "emlis_candidate_snapshot.v2"
SCHEMA_V2 = "cocolon.cmee.emlis_semantic_snapshot.v2"
CHECKPOINT_SCHEMA_V3 = "cocolon.cmee.emlis_answer_meaning.v3"
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
    semantic_profile: str = PROFILE


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
    if payload["semantic_profile"] == PROFILE_V2:
        semantic["native_bindings"] = payload["native_bindings"]
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


def _nuclei(packet, material, thread, *, adapter_version, semantic_profile=PROFILE):
    if semantic_profile == PROFILE_V2:
        if adapter_version != "1":
            _fail("REJECT", "semantic_adapter_version_unsupported")
        return _nuclei_v2(packet, material, thread)[:3]
    if adapter_version not in {"1", "2"}:
        _fail("REJECT", "semantic_adapter_version_unsupported")
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
            if adapter_version == "2" and not re.match(r"^(?:今|現在|その時|あの時|当時)も", claim["text"]):
                # The author supplies thread_time itself. Keep the full claim in
                # the snapshot, but pass its lexical content without that prefix.
                # Additive `も` is not an expendable time label. Its original
                # lexical range stays intact until the author can represent it.
                prefix = re.match(r"^(?:今|現在|その時|あの時|当時)(?:は)?", claim["text"])
                attrs[1] = f"source_fragment_scalar_range:{start + prefix.end()}:{end}"
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


def _v2_parts(packet):
    _keys(packet, {"candidate", "evidence"})
    c = packet["candidate"]
    _keys(c, {"schema_version", "core", "claims", "relations", "unknowns", "conflicts", "updates"})
    if c["schema_version"] != CANDIDATE_SCHEMA or c["core"] != "emlis" or c["conflicts"]:
        _fail("UNSUPPORTED", "semantic_v2_candidate_scope_unsupported")
    if any(type(c[k]) is not list for k in ("claims", "relations", "unknowns", "conflicts", "updates")):
        _fail("REJECT", "semantic_collection_invalid")
    if not 4 <= len(c["claims"]) <= 16:
        _fail("UNSUPPORTED", "semantic_v2_claim_count_unsupported")
    ids = [x["claim_id"] for x in c["claims"]]
    if len(set(ids)) != len(ids) or any(type(x) is not str or not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", x) for x in ids):
        _fail("REJECT", "semantic_claim_id_invalid")
    index = {x["claim_id"]: x for x in c["claims"]}
    unknowns = c["unknowns"]
    if len(unknowns) != 1:
        _fail("UNSUPPORTED", "semantic_v2_unknown_scope_unsupported")
    u = unknowns[0]
    _keys(u, {"unknown_id", "target_claim_refs", "dimension", "description", "origin", "resolution_state", "evidence_indexes"})
    if (u["origin"] != "PERSON_STATED" or u["dimension"] != "JOY_ASPECT"
        or u["resolution_state"] != "SOURCE_STATEMENT_RETAINED" or len(u["target_claim_refs"]) != 1
        or u["target_claim_refs"][0] not in index):
        _fail("UNSUPPORTED", "semantic_v2_unknown_scope_unsupported")
    joy = index[u["target_claim_refs"][0]]
    statements = [x for x in c["claims"] if x["kind"] == "EXPLICIT_UNKNOWN"]
    actions = [x for x in c["claims"] if x["kind"] == "ACTION"]
    if len(statements) != 1 or len(actions) != 2:
        _fail("UNSUPPORTED", "semantic_v2_group_incomplete")
    statement = statements[0]
    delegates = [x for x in actions if x["predicate"]["surface"] == "任せて"]
    listeners = [x for x in actions if x["predicate"]["surface"] == "聞いた"]
    if len(delegates) != 1 or len(listeners) != 1:
        _fail("UNSUPPORTED", "semantic_v2_action_scope_unsupported")
    delegate, listener = delegates[0], listeners[0]
    if (joy["kind"] != "STATE" or joy["text"] not in {"うれしかった", "嬉しかった"}
        or statement["text"] != "どこが" + joy["text"] + "かはまだ曖昧"
        or statement["predicate"] != {"surface":"曖昧", "arguments":[]}
        or statement["evidence_indexes"] != u["evidence_indexes"]):
        _fail("HOLD", "semantic_v2_unknown_target_not_bound")
    # This finite grammar admits written case, not inferred recipient/cause.
    if delegate["text"] != "打合せで後輩に説明を任せて" or listener["text"] != "最後まで聞いた。":
        _fail("UNSUPPORTED", "semantic_v2_action_grammar_unsupported")
    special = (joy, statement, delegate, listener)
    for x in special:
        _keys(x, _CLAIM_KEYS)
        _keys(x["predicate"], {"surface", "arguments"})
        refs = _refs(x["evidence_indexes"], len(packet["evidence"]))
        if len(refs) != 1 or packet["evidence"][refs[0]]["quote"] != x["text"]:
            _fail("REJECT", "semantic_v2_claim_anchor_invalid")
        if (x["subject"] != {"binding":"OMITTED", "source_entity":None, "evidence_indexes":[]}
            or x["polarity"] != {"value":"AFFIRMED", "scope_refs":[x["claim_id"]], "evidence_indexes":refs}
            or x["modality"] != {"value":"ASSERTED_AS_WRITTEN", "evidence_indexes":refs}
            or x["qualifiers"]
            or x["about_time"] != {"kind":"WRITTEN_STILL_UNKNOWN" if x is statement else "WRITTEN_PAST_UNRESOLVED_OCCASION",
                "expression":None, "anchor_source_id":None, "evidence_indexes":refs}):
            _fail("HOLD", "semantic_v2_written_scope_unbound")
    wanted = ((delegate, (("WRITTEN_で", "打合せ"), ("WRITTEN_に", "後輩"), ("WRITTEN_を", "説明"))),
              (listener, (("WRITTEN_まで", "最後"),)))
    for x, pairs in wanted:
        args = x["predicate"]["arguments"]
        if len(args) != len(pairs):
            _fail("UNSUPPORTED", "semantic_v2_case_scope_unsupported")
        for a, (role, text) in zip(args, pairs):
            _keys(a, {"role", "text", "claim_ref", "evidence_indexes"})
            if (a["role"], a["text"], a["claim_ref"]) != (role, text, None):
                _fail("HOLD", "semantic_v2_case_not_bound")
            refs = _refs(a["evidence_indexes"], len(packet["evidence"]))
            e = packet["evidence"][x["evidence_indexes"][0]]
            if len(refs) != 1:
                _fail("UNSUPPORTED", "semantic_v2_case_not_atomic")
            part = packet["evidence"][refs[0]]
            if (part["quote"] != text + role.removeprefix("WRITTEN_")
                or part["source_id"] != e["source_id"] or part["field_path"] != e["field_path"]
                or not e["start"] <= part["start"] < part["end"] <= e["end"]):
                _fail("REJECT", "semantic_v2_case_evidence_invalid")
    special_ids = {x["claim_id"] for x in special}
    links = [r for r in c["relations"] if {r["from_claim_id"], r["to_claim_id"]} & special_ids]
    expected = {(delegate["claim_id"], listener["claim_id"], "SOURCE_WRITTEN_TE_LINK"),
                (joy["claim_id"], statement["claim_id"], "SOURCE_WRITTEN_CONCESSION")}
    if len(links) != 2 or {(r["from_claim_id"], r["to_claim_id"], r["type"]) for r in links} != expected:
        _fail("UNSUPPORTED", "semantic_v2_written_links_incomplete")
    if len({r["relation_id"] for r in c["relations"]}) != len(c["relations"]):
        _fail("REJECT", "semantic_relation_id_invalid")
    for r in links:
        _keys(r, {"relation_id", "type", "from_claim_id", "to_claim_id", "polarity", "scope_refs", "qualifiers", "evidence_indexes"})
        refs = _refs(r["evidence_indexes"], len(packet["evidence"]))
        if (r["relation_id"] in ids or r["polarity"] != "AFFIRMED" or r["scope_refs"] != [r["relation_id"]]
            or r["qualifiers"] or len(refs) != 1):
            _fail("REJECT", "semantic_v2_relation_scope_invalid")
        e = packet["evidence"][refs[0]]
        a, b = (packet["evidence"][index[r[k]]["evidence_indexes"][0]] for k in ("from_claim_id", "to_claim_id"))
        te = r["type"] == "SOURCE_WRITTEN_TE_LINK"
        if (a["source_id"] != b["source_id"] or e["source_id"] != a["source_id"]
            or a["field_path"] != b["field_path"] or e["field_path"] != a["field_path"]
            or e["start"] != (a["end"] - 3 if te else a["start"]) or e["end"] != b["end"]
            or b["start"] != a["end"] + (1 if te else 3)
            or e["quote"] != ("任せて、" + b["quote"] if te else a["quote"] + "けど、" + b["quote"])):
            _fail("REJECT", "semantic_v2_relation_evidence_invalid")
    return special, tuple(links)


def _compact_packet(packet, claims, relations):
    """Reuse v1 validation only for its exact retained finite language."""
    result = json.loads(_json(packet))
    result["candidate"].update(claims=list(claims), relations=list(relations), unknowns=[])
    used = set()
    def collect(value):
        if type(value) is dict:
            for k, v in value.items():
                if k == "evidence_indexes": used.update(v)
                else: collect(v)
        elif type(value) is list:
            for v in value: collect(v)
    collect(result["candidate"])
    order = sorted(used)
    positions = {i: j for j, i in enumerate(order)}
    def remap(value):
        if type(value) is dict:
            return {k: [positions[i] for i in v] if k == "evidence_indexes" else remap(v) for k, v in value.items()}
        if type(value) is list: return [remap(v) for v in value]
        return value
    result["candidate"] = remap(result["candidate"])
    result["evidence"] = [packet["evidence"][i] for i in order]
    return result


def _locate_v2(thread, material, evidence):
    # Only the single terminal full stop may lie outside a native lexical span.
    fields = {s["source_id"]: s["text_fields"] for s in material.payload()["sources"]}
    lexical = []
    for e in evidence:
        value = dict(e)
        text = fields[e["source_id"]][e["field_path"]]
        if e["quote"].endswith("。") and text[e["end"] - 1:e["end"]] == "。":
            value.update(end=e["end"] - 1, quote=e["quote"][:-1])
        lexical.append(value)
    return _locate(thread, material, lexical)


def _nuclei_v2(packet, material, thread):
    special, links = _v2_parts(packet)
    joy, statement, delegate, listener = special
    c, ev = packet["candidate"], packet["evidence"]
    special_ids = {x["claim_id"] for x in special}
    retained = _compact_packet(packet, [x for x in c["claims"] if x["claim_id"] not in special_ids - {joy["claim_id"]}],
        [r for r in c["relations"] if r not in links])
    rows, relations, mapping = _nuclei(retained, material, thread, adapter_version="2")
    rows, relations = list(rows), list(relations)
    locations = _locate_v2(thread, material, ev)
    for x in special:
        i = x["evidence_indexes"][0]
        q, start, end = locations[i]
        source = next(s for s in material.payload()["sources"] if s["source_id"] == ev[i]["source_id"])
        if source["role"] != "ORIGINAL_INPUT" or ev[i]["field_path"] not in {"memo", "memo_action"}:
            _fail("UNSUPPORTED", "semantic_v2_original_source_required")
        nid = identity("semantic-nucleus", q.source_envelope_id, x["claim_id"], ev[i])
        mapping[x["claim_id"]] = nid
        if x is joy:
            continue
        unknown = x is statement
        kind, time = ("uncertainty", "present") if unknown else ("action", "past")
        attrs = ("semantic_role:generic_relation_fragment", f"source_fragment_scalar_range:{start}:{end}",
            "source_fragment_scalar_source:normalized_raw_text", "time_scope:" + time,
            "semantic_role:limiting_unknown" if unknown else "operator:performed_action",
            "source_snapshot_v2:" + ("joy_aspect_statement" if unknown else "written_te_action"))
        frame = gp.GroundedSemanticFrame("current_user", kind, "neutral", "uncertain" if unknown else "fact",
            time_scope=time, attribute_codes=attrs)
        rows.append(gp.GroundedSemanticNucleus(nid, kind, (q.thread_span_id,), (ev[i]["field_path"],), (q.thread_span_id,),
            frame, "explicit", 1.0, 1.0, "required", "explicit_current_input",
            ("no_unstated_cause", "no_third_party_intention", "no_stable_personality")))
    # No overlapping primary claims, even when their native ledger span is shared.
    anchors = [ev[x["evidence_indexes"][0]] for x in c["claims"]]
    for i, a in enumerate(anchors):
        if any(a["source_id"] == b["source_id"] and a["field_path"] == b["field_path"]
            and a["start"] < b["end"] and b["start"] < a["end"] for b in anchors[:i]):
            _fail("REJECT", "semantic_claim_anchor_overlap")
    for r in links:
        q = locations[r["evidence_indexes"][0]][0]
        if any(locations[x["evidence_indexes"][0]][0].thread_span_id != q.thread_span_id
               for x in special if x["claim_id"] in {r["from_claim_id"], r["to_claim_id"]}):
            _fail("UNSUPPORTED", "semantic_v2_relation_crosses_native_span")
        relations.append(gp.GroundedSemanticRelation(identity("semantic-relation", q.source_envelope_id, r),
            "source_written_te_link" if r["type"] == "SOURCE_WRITTEN_TE_LINK" else "contrast",
            mapping[r["from_claim_id"]], mapping[r["to_claim_id"]], (q.thread_span_id,), "user_stated_relation", 1.0, "required"))
    u = c["unknowns"][0]
    sid = locations[statement["evidence_indexes"][0]][0].thread_span_id
    boundaries = (gp.GroundedUnknownBoundary(identity("semantic-unknown", u), "source_explicit_epistemic_limit",
        (mapping[statement["claim_id"]],), (sid,), "hedge_only"),)
    return tuple(rows), tuple(relations), mapping, boundaries


def native_bindings_v2(packet, material, thread):
    special, links = _v2_parts(packet)
    _, _, mapping, _ = _nuclei_v2(packet, material, thread)
    locations = _locate_v2(thread, material, packet["evidence"])
    slices, args = [], []
    def bind(x, i):
        e = packet["evidence"][i]
        q, start, end = locations[i]
        ref = identity("semantic-slice", x["claim_id"], e)
        row = SnapshotSourceSliceBindingV2(ref, x["claim_id"], mapping[x["claim_id"]], e["source_id"],
            next(s["source_version"] for s in material.payload()["sources"] if s["source_id"] == e["source_id"]), q.thread_span_id, e["field_path"], e["start"], e["end"], start, end,
            e["quote"], x["subject"]["binding"], x["subject"]["source_entity"])
        if row not in slices: slices.append(row)
        return ref
    for x in special:
        bind(x, x["evidence_indexes"][0])
        for a in x["predicate"]["arguments"]:
            refs = tuple(bind(x, i) for i in a["evidence_indexes"])
            args.append(SnapshotCaseArgumentBindingV2(identity("semantic-case", x["claim_id"], a),
                mapping[x["claim_id"]], a["role"], a["text"], refs))
    written = []
    index = {x["claim_id"]: x for x in special}
    for r in links:
        refs = tuple(bind(index[r["from_claim_id"]], i) for i in r["evidence_indexes"])
        q = locations[r["evidence_indexes"][0]][0]
        written.append(SnapshotWrittenLinkBindingV2(identity("semantic-relation", q.source_envelope_id, r), r["type"], mapping[r["from_claim_id"]],
            mapping[r["to_claim_id"]], refs, tuple(r["scope_refs"]), r["polarity"]))
    u = packet["candidate"]["unknowns"][0]
    unknown = SnapshotPersonStatedUnknownBindingV2(u["unknown_id"], mapping[special[1]["claim_id"]],
        (mapping[special[0]["claim_id"]],), u["origin"], u["dimension"], u["resolution_state"],
        "AFFIRMED", "ASSERTED_AS_WRITTEN", "present", "past", tuple(bind(special[1], i) for i in u["evidence_indexes"]))
    return json.loads(_json(dict(source_slices=[asdict(x) for x in slices], case_arguments=[asdict(x) for x in args],
        person_stated_unknowns=[asdict(unknown)], written_links=[asdict(x) for x in written])))


def _plan(packet, material, thread, *, adapter_version, extra_relations=(), focus=(), semantic_profile=PROFILE):
    nuclei, relations, mapping = _nuclei(packet, material, thread, adapter_version=adapter_version, semantic_profile=semantic_profile)
    unknowns = _nuclei_v2(packet, material, thread)[3] if semantic_profile == PROFILE_V2 else ()
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
        nuclei, relations, unknowns, response, coverage, surface, safety_policy,
        EvidenceLedgerValidationReport(True, canonical_span_ids=resolver.span_ids),
        gp._all_plan_evidence_ids(nuclei, relations, unknowns),
        (gp.FINAL_STAGE1_GROUNDED_PROJECTION_VERSION, semantic_profile))
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
            "receipt", "answer_count", "question_control", "snapshot_ref", "claim_mapping"}
            | ({"native_bindings"} if p.get("semantic_profile") == PROFILE_V2 else set()))
        if _json(p) != text or (p["schema_version"], p["semantic_profile"]) not in {(SCHEMA, PROFILE), (SCHEMA_V2, PROFILE_V2)} or p["snapshot_ref"] != _semantic_ref(p):
            raise ValueError()
        thread = admit_emlis_thread(request)
        material = prepare_emlis(request)
        if (p["admission_version"] != "1" or p["adapter_version"] not in ({"1"} if p["semantic_profile"] == PROFILE_V2 else {"1", "2"})
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
    if type(semantic_input) is SemanticInput and semantic_input.semantic_profile == MODEL_PROFILE:
        return prepare_model_snapshot(request, semantic_input)
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
    if semantic_input.semantic_profile not in {PROFILE, PROFILE_V2}:
        _fail("REJECT", "semantic_profile_invalid")
    thread, material = admit_emlis_thread(request), prepare_emlis(request)
    if semantic_input.mode == "RESUME_ADOPTED":
        if semantic_input.receipt is not None or semantic_input.prior_snapshot_json is not None or not semantic_input.snapshot_json:
            _fail("REJECT", "semantic_resume_input_invalid")
        thread, material, p = _restore(request, semantic_input.snapshot_json)
        if p["semantic_profile"] != semantic_input.semantic_profile:
            _fail("REJECT", "semantic_profile_mismatch")
    elif semantic_input.mode == "FRESH_CANDIDATE":
        if semantic_input.snapshot_json is not None or request.emlis_thread.prepared_meaning_checkpoint_ref is not None:
            _fail("REJECT", "semantic_same_prefix_readoption_forbidden")
        packet = _receipt(material, semantic_input.receipt)
        p = dict(schema_version=SCHEMA_V2 if semantic_input.semantic_profile == PROFILE_V2 else SCHEMA,
            semantic_profile=semantic_input.semantic_profile, admission_version="1",
            adapter_version="1" if semantic_input.semantic_profile == PROFILE_V2 else CURRENT_ADAPTER_VERSION,
            request_ref=material.request_id, source_prefix_ref=thread.source_prefix_ref,
            source_bindings=_source_binding(material), packet=packet, prior_ref=None,
            prior_snapshot=None, receipt=asdict(semantic_input.receipt), answer_count=len(thread.answers),
            question_control=asdict(thread.control.question_control_context))
        if semantic_input.prior_snapshot_json:
            prior = json.loads(semantic_input.prior_snapshot_json)
            if not thread.answers or prior["answer_count"] != len(thread.answers) - 1 or prior["snapshot_ref"] != _semantic_ref(prior):
                _fail("REJECT", "semantic_prior_snapshot_invalid")
            if prior["semantic_profile"] != p["semantic_profile"]:
                _fail("REJECT", "semantic_profile_lineage_mismatch")
            p.update(prior_ref=prior["snapshot_ref"], prior_snapshot=prior)
        elif thread.answers:
            _fail("REJECT", "semantic_prior_snapshot_required")
        p["claim_mapping"] = _nuclei(packet, material, thread, adapter_version=p["adapter_version"], semantic_profile=p["semantic_profile"])[2]
        if p["semantic_profile"] == PROFILE_V2:
            p["native_bindings"] = native_bindings_v2(packet, material, thread)
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
    if prior and prior["semantic_profile"] != p["semantic_profile"]:
        _fail("REJECT", "semantic_profile_lineage_mismatch")
    packet = p["packet"]
    updates = packet["candidate"]["updates"]
    if p["semantic_profile"] == PROFILE_V2 and p["native_bindings"] != native_bindings_v2(packet, material, thread):
        _fail("REJECT", "semantic_native_binding_mismatch")
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
    original_plan, _ = _plan(original_p["packet"], original_material, original_thread,
        adapter_version=original_p["adapter_version"], semantic_profile=original_p["semantic_profile"])
    current_plan, mapping = _plan(packet, material, thread, adapter_version=p["adapter_version"], semantic_profile=p["semantic_profile"])
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
        prior_mapping = _nuclei(prior["packet"], prior_material, prior_thread,
            adapter_version=prior["adapter_version"], semantic_profile=prior["semantic_profile"])[2]
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
            if p["semantic_profile"] == PROFILE_V2:
                protected = {s["claim_ref"] for s in prior["native_bindings"]["source_slices"]
                    if s["nucleus_ref"] in {u["statement_nucleus_ref"] for u in prior["native_bindings"]["person_stated_unknowns"]}
                    | {n for u in prior["native_bindings"]["person_stated_unknowns"] for n in u["target_nucleus_refs"]}
                    | {a["owning_nucleus_ref"] for a in prior["native_bindings"]["case_arguments"]}}
                if set(targets) & protected:
                    _fail("HOLD", "semantic_v2_target_update_unsupported")
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
        if p["semantic_profile"] == PROFILE_V2:
            if packet["candidate"]["unknowns"] != prior["packet"]["candidate"]["unknowns"]:
                _fail("HOLD", "semantic_v2_unknown_update_unsupported")
            before_bindings, now_bindings = prior["native_bindings"], p["native_bindings"]
            for family in ("case_arguments", "person_stated_unknowns", "written_links"):
                if before_bindings[family] != now_bindings[family]:
                    _fail("HOLD", "semantic_v2_binding_update_unsupported")
        inactive = tuple(dict.fromkeys((*prior_prepared.checkpoint.inactive_claim_refs,
            *(prior_mapping[t] for t in removed), *(d for item in update_items for d in item.affected_dependency_refs))))
        active_ids = {n.nucleus_id for n in current_plan.nuclei}
        extras = [r for r in prior_plan.relations if r.type == "evaluation_about_event"
            and r.from_nucleus_id in active_ids and r.to_nucleus_id in active_ids
            and r.relation_id not in inactive] + extras
        accepted = tuple(n for n in current_plan.nuclei if n.nucleus_id not in {x.nucleus_id for x in original_plan.nuclei})
        current_plan, mapping = _plan(packet, material, thread, extra_relations=extras,
            adapter_version=p["adapter_version"], semantic_profile=p["semantic_profile"], focus=tuple(n.nucleus_id for n in accepted))
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
            *(x.update_ref for x in update_items)))), inactive, (),
        semantic_schema_version=CHECKPOINT_SCHEMA_V3 if p["semantic_profile"] == PROFILE_V2 else CHECKPOINT_SCHEMA,
        semantic_profile=p["semantic_profile"], semantic_snapshot=_json(p), snapshot_ref=p["snapshot_ref"])
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
        active_ids = {n.nucleus_id for n in _plan(p["packet"], material, prepared.thread,
            adapter_version=p["adapter_version"], semantic_profile=p["semantic_profile"])[0].nuclei}
        extras = [r for r in derive_snapshot_plan(previous).relations if r.type == "evaluation_about_event"
            and r.from_nucleus_id in active_ids and r.to_nucleus_id in active_ids
            and r.relation_id not in prepared.checkpoint.inactive_claim_refs]
    if prepared.checkpoint.answer_update:
        active = _plan(p["packet"], material, prepared.thread, adapter_version=p["adapter_version"], semantic_profile=p["semantic_profile"])[0]
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
        adapter_version=p["adapter_version"], semantic_profile=p["semantic_profile"], focus=tuple(n.nucleus_id for n in prepared.accepted_nuclei))[0]



from .emlis_thread_source import ThreadEvidenceSpanResolver


class SnapshotEvidenceSpanResolverV2(ThreadEvidenceSpanResolver):
    """Private typed source adapter for the same immutable adopted snapshot."""
    def __init__(self, prepared, payload):
        super().__init__(prepared.thread.original, prepared.thread.answers)
        self.snapshot_ref = payload["snapshot_ref"]
        self.checkpoint_ref = prepared.checkpoint.checkpoint_id
        value = payload["native_bindings"]
        def rows(cls, family, tuple_fields):
            return tuple(cls(**{k: tuple(v) if k in tuple_fields else v for k,v in x.items()}) for x in value[family])
        self.source_slices = rows(SnapshotSourceSliceBindingV2, "source_slices", ())
        self.case_arguments = rows(SnapshotCaseArgumentBindingV2, "case_arguments", ("source_slice_refs",))
        self.person_stated_unknowns = rows(SnapshotPersonStatedUnknownBindingV2, "person_stated_unknowns", ("target_nucleus_refs", "evidence_slice_refs"))
        self.written_links = rows(SnapshotWrittenLinkBindingV2, "written_links", ("marker_slice_refs", "scope_refs"))
        self.native_nucleus_ids = tuple(dict.fromkeys(x.nucleus_ref for x in self.source_slices))

    def binding_rows(self, node_ids, edge_ids):
        if not set(self.native_nucleus_ids) <= set(node_ids) or len(set(node_ids.values())) != len(node_ids):
            _fail("REJECT", "semantic_v2_graph_binding_invalid")
        return dict(snapshot_ref=self.snapshot_ref, checkpoint_ref=self.checkpoint_ref, source_slices=self.source_slices,
            case_arguments=self.case_arguments, person_stated_unknowns=self.person_stated_unknowns,
            written_links=self.written_links, nucleus_node_bindings=tuple(sorted(node_ids.items())),
            relation_edge_bindings=tuple(sorted(edge_ids.items())))


def snapshot_resolver(prepared):
    if type(prepared) is not SnapshotPreparedMeaning:
        return prepared.thread.resolver()
    p = json.loads(prepared.semantic_snapshot)
    if p["semantic_profile"] != PROFILE_V2:
        return prepared.thread.resolver()
    from .preparation import PreparedRequest
    material = PreparedRequest("prep-" + hashlib.sha256(prepared.semantic_material_json.encode()).hexdigest(), prepared.semantic_material_json)
    if (p["snapshot_ref"] != _semantic_ref(p) or p["native_bindings"] != native_bindings_v2(p["packet"], material, prepared.thread)):
        _fail("REJECT", "semantic_v2_resolver_binding_invalid")
    return SnapshotEvidenceSpanResolverV2(prepared, p)


# The learned-response profile is a separate, bounded offline vertical. It does
# not weaken or route arbitrary predicates through either historical adapter.
MODEL_PROFILE = "emlis_model_proposal.v1"
MODEL_SCHEMA = "cocolon.cmee.emlis_semantic_snapshot.v3"
MODEL_CHECKPOINT_SCHEMA = "cocolon.cmee.emlis_answer_meaning.v4"
MODEL_CANDIDATE_SCHEMA = "cocolon.cmee.semantic_and_surface_proposal.v1"


def is_model_profile(value):
    return value == MODEL_PROFILE


@dataclass(frozen=True, slots=True, repr=False)
class ModelCheckpoint(EmlisMeaningCheckpointV1):
    semantic_schema_version: str = MODEL_CHECKPOINT_SCHEMA
    semantic_profile: str = MODEL_PROFILE
    semantic_snapshot: str = ""
    snapshot_ref: str = ""


@dataclass(frozen=True, slots=True, repr=False)
class ModelPreparedMeaning:
    thread: object
    checkpoint: ModelCheckpoint
    semantic_snapshot: str
    semantic_material_json: str
    meaning_json: str
    surface_proposal_json: str
    question_proposal_json: str
    native_bindings_json: str


def _model_fail(code, decision="REJECT"):
    _fail(decision, "model_" + code)


def _model_span(text, quote, source_id, field):
    if type(quote) is not str or not quote or text.count(quote) != 1:
        _model_fail("source_anchor_not_unique", "HOLD")
    start = text.index(quote)
    return dict(source_id=source_id, field_path=field, start=start,
                end=start + len(quote), quote=quote)


def _model_nominal_slot(text, *, state_modifier=False):
    """Accept one written nominal slot, never a hidden subordinate action.

    The bounded repair family allows a single listed state modifier followed
    by a noun token (Kanji/Katakana/ASCII digits or letters). This is a lexical
    script/grammar boundary, not a dictionary of permitted item/person names.
    Hiragana-containing compound names, additional case particles, relative
    clauses and action conjunctions are unsupported rather than shortened.
    For example, a second 'を...して' must not become part of one patient.
    """
    if state_modifier:
        text = re.sub(r"^(?:ぐらついていた|壊れていた|緩んでいた|傷んでいた|古い|新しい)", "", text, count=1)
    return bool(re.fullmatch(r"[一-龥々ァ-ヶーA-Za-z0-9０-９]{1,32}", text))


def _model_daily_source_roles(thread, material):
    """The approved initial meal/calm family; all text remains in its field.

    A written tara link is not a general causal claim. The two eating roles
    stay distinct: neither food identity nor a purpose is inferred across fields.
    """
    original = material.payload()["sources"][0]
    sid, fields = original["source_id"], original["text_fields"]
    memo, action = fields.get("memo"), fields.get("memo_action")
    if type(memo) is not str or type(action) is not str:
        return None
    am = re.fullmatch(r"(?P<return>帰って)から、(?P<cook>(?P<food>うどん|雑炊)を作って)(?P<eat>食べた)。", action)
    mm = re.fullmatch(r"(?P<meal>(?:あったかいもの|温かいもの)を?食べた)ら、(?P<calm>(?:ちょっと|少し)落ち着いた)。", memo)
    if not am or not mm:
        return None
    if thread.answers:
        _model_fail("daily_initial_only", "UNSUPPORTED")
    roles = {name: _model_span(text, match[group], sid, field)
             for name, text, match, group, field in (
                 ("return", action, am, "return", "memo_action"),
                 ("cook", action, am, "cook", "memo_action"),
                 ("eat", action, am, "eat", "memo_action"),
                 ("warm_food_eat", memo, mm, "meal", "memo"),
                 ("slight_calm", memo, mm, "calm", "memo"))}
    markers = {
        "return_scope": _model_span(action, action[:-1], sid, "memo_action"),
        "cook_and_eat": _model_span(action, "作って食べた", sid, "memo_action"),
        "written_eat_calm": _model_span(memo, memo[:-1], sid, "memo"),
    }
    cases = [dict(role="cook", written_role="を", text=am["food"], source_id=sid,
                  field_path="memo_action", start=am.start("food"), end=am.end("food"))]
    return roles, markers, {}, cases, {
        s["source_id"]: s["text_fields"] for s in material.payload()["sources"]}, []


def _model_source_roles(thread, material):
    """Read a repair/reuse syntax family, not a fixture or a free-text parser.

    Lexical objects and participants are read from their written case slots.
    Unsupported subjects, polarity, embedding or added clauses are retained in
    the source and cause UNSUPPORTED; they are never discarded to fit a case.
    """
    daily = _model_daily_source_roles(thread, material)
    if daily is not None:
        return daily
    original = material.payload()["sources"][0]
    sid, fields = original["source_id"], original["text_fields"]
    memo, action = fields.get("memo"), fields.get("memo_action")
    if type(memo) is not str or type(action) is not str:
        _model_fail("source_text_required", "UNSUPPORTED")
    am = re.fullmatch(r"(?P<object>[^、。\n]{1,60})を(?P<repair>修理して|直して)[、,]"
                     r"(?P<result>また(?:座れる|使える)ようになった)[。]?", action)
    mm = re.fullmatch(r"(?P<solo>(?:全部|すべて)?一人で(?:直せた|修理できた)こと)が[、,]?"
                     r"(?P<joy>うれしかった|嬉しかった)[。]?", memo)
    if not am or not mm or not _model_nominal_slot(am["object"], state_modifier=True):
        _model_fail("repair_reuse_source_out_of_scope", "UNSUPPORTED")
    roles = {
        "repair": _model_span(action, action[:am.start("result")].rstrip("、,"), sid, "memo_action"),
        "usable_again": _model_span(action, am["result"], sid, "memo_action"),
        "joy": _model_span(memo, mm["joy"], sid, "memo"),
        "solo_appraisal_object": _model_span(memo, mm["solo"], sid, "memo"),
    }
    markers = {
        "repair_and_result": _model_span(action, am["repair"][-2:] + action[am.end("repair"):am.start("result")], sid, "memo_action"),
        "joy_ground": _model_span(memo, memo.rstrip("。"), sid, "memo"),
    }
    cases = [dict(role="repair", written_role="を", text=am["object"], source_id=sid,
                  field_path="memo_action", start=am.start("object"), end=am.end("object"))]
    source_fields = {s["source_id"]: s["text_fields"] for s in material.payload()["sources"]}
    corrections, negations = {}, []
    if thread.answers:
        answer = thread.answers[0].source
        text, aid = answer.answer_text_private, answer.answer_id
        # A visible correction, cooperation and explicit non-solo/reuse reason
        # are required together. No model assertion can supply a missing one.
        pattern = (r"(?P<correction>(?:さっき|先ほど)「(?P<old>(?:全部|すべて)?一人で)」と(?:書いた|言った)のは訂正します)[。]"
                   r"(?:途中で)?(?P<guidance>(?P<person>[^、。\n]{1,24})に(?P<procedure>手順|やり方|方法)を(?:教えてもらって|教わって))[、,]"
                   r"(?P<joint>一緒に(?:直しました|修理しました))[。][\s]*"
                   r"(?P<reason_sentence>(?:うれしかった|嬉しかった)のも、?(?P<old_reason>一人で(?:できた|直せた)からではなく)[、,]"
                   r"(?P<reuse>捨てずにまた使えるようになったからです))[。]?")
        cm = re.fullmatch(pattern, text)
        if not cm or not _model_nominal_slot(cm["person"]):
            _model_fail("correction_source_out_of_scope", "UNSUPPORTED")
        if cm["old"] not in mm["solo"]:
            _model_fail("correction_target_not_bound", "HOLD")
        roles.pop("solo_appraisal_object")
        for role, group in (("friend_guidance", "guidance"), ("joint_repair", "joint"),
                            ("reuse_appraisal_object", "reuse")):
            roles[role] = _model_span(text, cm[group], aid, "answer_text_private")
        for key, group in (("revise_solo", "correction"), ("old_reason_negated", "old_reason"),
                           ("joy_ground_revised", "reason_sentence")):
            corrections[key] = _model_span(text, cm[group], aid, "answer_text_private")
        person_start = cm.start("person")
        cases.extend([dict(role="friend_guidance", written_role="に", text=cm["person"],
            source_id=aid, field_path="answer_text_private", start=person_start, end=cm.end("person")),
            dict(role="friend_guidance", written_role="を", text=cm["procedure"],
            source_id=aid, field_path="answer_text_private", start=cm.start("procedure"), end=cm.end("procedure"))])
        negations = [corrections["old_reason_negated"], _model_span(text, "捨てずに", aid, "answer_text_private")]
    return roles, markers, corrections, cases, source_fields, negations


def _model_packet(packet, material, thread, prior):
    _keys(packet, {"candidate", "evidence"})
    c, ev = packet["candidate"], packet["evidence"]
    _keys(c, {"schema_version", "core", "claims", "relations", "unknowns", "conflicts", "updates",
              "surface_proposal", "question_proposal"})
    if c["schema_version"] != MODEL_CANDIDATE_SCHEMA or c["core"] != "emlis":
        _model_fail("candidate_version_invalid")
    if any(type(c[k]) is not list for k in ("claims", "relations", "unknowns", "conflicts", "updates")):
        _model_fail("collection_invalid")
    if c["conflicts"]:
        _model_fail("conflicts_not_supported", "UNSUPPORTED")
    roles, markers, corrections, cases, source_fields, negations = _model_source_roles(thread, material)
    daily = "slight_calm" in roles
    if daily and (prior is not None or c["updates"] or c["unknowns"]
                  or c["question_proposal"] is not None
                  or c["surface_proposal"].get("update_note") is not None):
        _model_fail("daily_initial_only", "UNSUPPORTED")
    if type(ev) is not list or len(ev) > 32 or len({_json(e) for e in ev}) != len(ev):
        _model_fail("evidence_collection_invalid")
    def ev_index(anchor):
        found = [i for i, e in enumerate(ev) if e == anchor]
        if len(found) != 1:
            _model_fail("required_source_anchor_missing", "HOLD")
        return found[0]
    # Old evidence may remain in a correction packet, but every row must be a
    # known source role/connector/correction. Arbitrary extra text is not lost.
    original_roles, original_markers, _, _, _, _ = _model_source_roles(
        replace(thread, answers=()), material)
    allowed = list(original_roles.values()) + list(original_markers.values()) + list(roles.values()) + list(corrections.values())
    if any(e not in allowed for e in ev):
        _model_fail("evidence_out_of_scope", "UNSUPPORTED")
    mapped, ids = {}, set()
    role_for_text = {v["quote"]: k for k, v in roles.items()}
    if len(role_for_text) != len(roles) or len(c["claims"]) != len(roles):
        _model_fail("claim_coverage_invalid", "HOLD")
    for claim in c["claims"]:
        _keys(claim, _CLAIM_KEYS)
        cid = claim["claim_id"]
        if type(cid) is not str or not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", cid) or cid in ids:
            _model_fail("claim_identity_invalid")
        ids.add(cid)
        role = role_for_text.get(claim["text"])
        if role is None or role in mapped:
            _model_fail("claim_source_semantics_not_bound", "HOLD")
        anchor = roles[role]
        index = ev_index(anchor)
        kind = "STATE" if role in {"joy", "slight_calm"} else "ACTION_RESULT" if role == "usable_again" else "USER_APPRAISAL_OBJECT" if role.endswith("appraisal_object") else "EVENT"
        expected = dict(kind=kind, subject=dict(binding="OMITTED", source_entity=None, evidence_indexes=[]),
            predicate=dict(surface=anchor["quote"], arguments=[]),
            polarity=dict(value="AFFIRMED", scope_refs=[cid], evidence_indexes=[index]),
            modality=dict(value="ASSERTED_AS_WRITTEN", evidence_indexes=[index]),
            about_time=dict(kind="WRITTEN_PAST_UNRESOLVED_OCCASION", expression=None,
                            anchor_source_id=anchor["source_id"], evidence_indexes=[index]),
            qualifiers=[], evidence_indexes=[index])
        if any(claim[k] != v for k, v in expected.items()):
            _model_fail("claim_axes_not_source_bound", "HOLD")
        mapped[role] = dict(claim_ref=cid, text=anchor["quote"], **{k:v for k,v in anchor.items() if k != "quote"})
    relation_roles, relids = {}, set()
    if daily:
        required_relations = {
            "return_before_cook": ("SOURCE_WRITTEN_TEMPORAL_KARA_LINK", "return", "cook", markers["return_scope"]),
            "return_before_eat": ("SOURCE_WRITTEN_TEMPORAL_KARA_LINK", "return", "eat", markers["return_scope"]),
            "cook_and_eat": ("SOURCE_WRITTEN_TE_LINK", "cook", "eat", markers["cook_and_eat"]),
            "written_eat_calm": ("SOURCE_WRITTEN_TARA_LINK", "warm_food_eat", "slight_calm", markers["written_eat_calm"]),
        }
    else:
        required_relations = {"repair_and_result": ("SOURCE_WRITTEN_TE_LINK", "repair", "usable_again", markers["repair_and_result"])}
        joy_role = "reuse_appraisal_object" if thread.answers else "solo_appraisal_object"
        ground_role = "joy_ground_revised" if thread.answers else "joy_ground"
        required_relations[ground_role] = ("USER_STATED_JOY_GROUND", joy_role, "joy",
            corrections["joy_ground_revised"] if thread.answers else markers["joy_ground"])
    if len(c["relations"]) != len(required_relations):
        _model_fail("relation_coverage_invalid", "HOLD")
    for r in c["relations"]:
        _keys(r, {"relation_id", "type", "from_claim_id", "to_claim_id", "polarity", "scope_refs", "qualifiers", "evidence_indexes"})
        rid = r["relation_id"]
        if type(rid) is not str or not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", rid) or rid in ids | relids:
            _model_fail("relation_identity_invalid")
        relids.add(rid)
        matches = [role for role,(kind,frm,to,anchor) in required_relations.items()
            if r["type"] == kind and r["from_claim_id"] == mapped[frm]["claim_ref"]
            and r["to_claim_id"] == mapped[to]["claim_ref"] and r["evidence_indexes"] == [ev_index(anchor)]]
        if len(matches) != 1 or matches[0] in relation_roles or r["polarity"] != "AFFIRMED" or r["scope_refs"] != [rid] or r["qualifiers"]:
            _model_fail("relation_direction_or_scope_not_bound", "HOLD")
        relation_roles[matches[0]] = rid
    unknowns = c["unknowns"]
    if daily:
        if unknowns:
            _model_fail("daily_initial_only", "UNSUPPORTED")
    elif thread.answers:
        if unknowns:
            _model_fail("corrected_gap_not_inactive", "HOLD")
    else:
        if len(unknowns) != 1:
            _model_fail("initial_gap_missing", "HOLD")
        u = unknowns[0]
        _keys(u, {"unknown_id", "kind", "target_claim_refs", "description", "evidence_indexes"})
        if (type(u["unknown_id"]) is not str or not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", u["unknown_id"])
            or u["unknown_id"] in ids | relids or u["kind"] != "NOT_STATED"
            or u["target_claim_refs"] != [mapped["solo_appraisal_object"]["claim_ref"], mapped["joy"]["claim_ref"]]
            or u["evidence_indexes"] != [ev_index(roles["solo_appraisal_object"]), ev_index(roles["joy"])]
            or type(u["description"]) is not str or not u["description"].strip()):
            _model_fail("not_stated_gap_not_bound", "HOLD")
    _model_updates(c, ev, mapped, relation_roles, corrections, prior)
    _model_surface_shape(c, ids, relids)
    native_slices = []
    resolver = thread.resolver()
    sources = {s["source_id"]:s for s in material.payload()["sources"]}
    for e in ev:
        native_refs = [q.thread_span_id for q in resolver.qualified_refs
            if q.source_envelope_id == sources[e["source_id"]]["envelope_id"]
            and q.evidence.field_path == e["field_path"]
            and q.evidence.scalar_start < e["end"] and e["start"] < q.evidence.scalar_end]
        if not native_refs:
            _model_fail("native_span_binding_missing")
        native_slices.append(dict(e, native_span_refs=native_refs))
    for case in cases:
        case["owner_claim_ref"] = mapped[case.pop("role")]["claim_ref"]
    raw = sources[next(iter(source_fields))]["original"]
    native = dict(stage="AFTER_CORRECTION" if thread.answers else "INITIAL", roles=mapped,
        relation_roles=relation_roles, source_fields=source_fields, source_slices=native_slices,
        case_arguments=cases, source_negations=negations,
        written_links=[dict(relation_ref=r["relation_id"], type=r["type"], from_claim_ref=r["from_claim_id"],
                            to_claim_ref=r["to_claim_id"], evidence_indexes=r["evidence_indexes"]) for r in c["relations"]],
        preserved_selections={k:raw.get(k) for k in ("category", "emotions", "emotion_details", "is_secret")})
    if daily:
        native["family"] = "DAILY_CALM_V1"
    return native


def _model_surface_shape(c, ids, relids):
    surface = c["surface_proposal"]
    _keys(surface, {"observation", "reception", "update_note", "bindings"})
    if (any(type(surface[k]) is not str or not surface[k].strip() for k in ("observation", "reception"))
        or surface["update_note"] is not None and (type(surface["update_note"]) is not str or not surface["update_note"].strip())
        or type(surface["bindings"]) is not list):
        _model_fail("surface_shape_invalid")
    expected_sections = {"observation", "reception"} | ({"update_note"} if surface["update_note"] is not None else set())
    seen = set()
    for b in surface["bindings"]:
        if type(b) is not dict:
            _model_fail("surface_binding_invalid")
        section = b.get("section")
        _keys(b, {"section", "claim_refs", "relation_refs"} | ({"update_refs"} if section == "update_note" else set()))
        if section not in expected_sections or section in seen:
            _model_fail("surface_section_invalid")
        seen.add(section)
        for field, allowed in (("claim_refs",ids), ("relation_refs",relids)):
            values = b[field]
            if type(values) is not list or len(set(values)) != len(values) or any(v not in allowed for v in values):
                _model_fail("surface_reference_invalid")
        if not b["claim_refs"]:
            _model_fail("surface_claim_binding_required")
        if section == "update_note" and (type(b["update_refs"]) is not list or any(type(i) is not int or not 0 <= i < len(c["updates"]) for i in b["update_refs"])):
            _model_fail("surface_update_reference_invalid")
    if seen != expected_sections:
        _model_fail("surface_section_coverage_invalid")
    q = c["question_proposal"]
    if q is not None:
        _keys(q, {"text", "target_unknown_ref", "focus", "claim_refs"})
        if (not c["unknowns"] or q["target_unknown_ref"] != c["unknowns"][0]["unknown_id"]
            or q["focus"] != "PERSONAL_JOY_SIGNIFICANCE" or q["claim_refs"] != c["unknowns"][0]["target_claim_refs"]
            or type(q["text"]) is not str or not q["text"].strip()):
            _model_fail("question_proposal_not_bound", "HOLD")


def _model_updates(c, ev, mapped, relation_roles, corrections, prior):
    if prior is None:
        if c["updates"]:
            _model_fail("initial_updates_forbidden")
        return
    previous = prior["native_bindings"]
    pc = prior["meaning_packet"]["candidate"]
    expected = [
        ("REVISE", "CLAIM", previous["roles"]["solo_appraisal_object"]["claim_ref"],
         [mapped["friend_guidance"]["claim_ref"],mapped["joint_repair"]["claim_ref"]],
         [corrections["revise_solo"], dict((k,v) for k,v in mapped["friend_guidance"].items() if k not in {"claim_ref","text"}), dict((k,v) for k,v in mapped["joint_repair"].items() if k not in {"claim_ref","text"})]),
        ("REVISE", "RELATION", previous["relation_roles"]["joy_ground"], [relation_roles["joy_ground_revised"]],
         [corrections["old_reason_negated"], corrections["joy_ground_revised"]]),
        ("INVALIDATE_GAP", "UNKNOWN", pc["unknowns"][0]["unknown_id"], [],
         [corrections["revise_solo"], corrections["joy_ground_revised"]])]
    # Retained original source meanings cannot disappear, change role or acquire
    # different IDs when only the personal explanation was corrected.
    for role in ("repair", "usable_again", "joy"):
        if mapped[role] != previous["roles"][role]:
            _model_fail("unaffected_meaning_changed", "HOLD")
    if relation_roles["repair_and_result"] != previous["relation_roles"]["repair_and_result"]:
        _model_fail("unaffected_relation_changed", "HOLD")
    if len(c["updates"]) != len(expected):
        _model_fail("update_coverage_invalid", "HOLD")
    for row, (op,kind,target,replacements,anchors) in zip(c["updates"],expected):
        _keys(row, {"operation","target_kind","target_ref","replacement_refs","evidence_indexes","prior_snapshot_ref"})
        indices = []
        for anchor in anchors:
            if "quote" not in anchor:
                role = next(v for v in mapped.values() if all(v.get(k) == a for k,a in anchor.items()))
                anchor = dict(anchor,quote=role["text"])
            match = [i for i,e in enumerate(ev) if e == anchor]
            if len(match) != 1:
                _model_fail("update_evidence_missing")
            indices.append(match[0])
        if row != dict(operation=op,target_kind=kind,target_ref=target,replacement_refs=replacements,
                       evidence_indexes=indices,prior_snapshot_ref=prior["snapshot_ref"]):
            _model_fail("update_not_prior_or_source_bound", "HOLD")


def _model_meaning_packet(packet):
    # Free-form model descriptions are diagnostics, not trusted meaning. The
    # typed missing dimension and targets are source-validated separately.
    # Keep the exact original explanation in packet/receipt, and give the
    # adopted NOT_STATED gap a CMEE-owned coverage explanation.
    candidate = json.loads(_json({k:v for k,v in packet["candidate"].items()
                                  if k not in {"surface_proposal","question_proposal"}}))
    for row in candidate.get("unknowns", []):
        if type(row) is dict and row.get("kind") == "NOT_STATED":
            row["description"] = "詳しい本人の意味づけは未記載。"
    return dict(candidate=candidate, evidence=packet["evidence"])


def _model_semantic_ref(p):
    semantic = {k:p[k] for k in ("schema_version","semantic_profile","admission_version","adapter_version",
        "request_ref","source_prefix_ref","source_bindings","meaning_packet","native_bindings",
        "prior_ref","answer_count","question_control")}
    return "semantic-" + hashlib.sha256(_json(semantic).encode()).hexdigest()


def _model_proposal_ref(packet):
    return identity("model-proposal", packet)


def _model_checkpoint(thread, material, p):
    ref = p["snapshot_ref"]
    update = None
    accepted, inactive = (), ()
    if p["prior_snapshot"]:
        rows = p["meaning_packet"]["candidate"]["updates"]
        accepted = tuple(identity("model-update",p["prior_ref"],r) for r in rows)
        inactive = tuple(r["target_ref"] for r in rows)
        answer = thread.answers[0].source
        items = tuple(EmlisAnswerUpdateItemV1(uid,r["target_kind"],(r["target_ref"],),
            tuple(identity("model-evidence",p["request_ref"],p["packet"]["evidence"][i]) for i in r["evidence_indexes"]),
            AnswerTemporalBindingV1("ORIGINAL_OCCASION",thread.control.original_source_ref),
            r["operation"],tuple(r["replacement_refs"]),(r["target_ref"],),())
            for uid,r in zip(accepted,rows))
        update = AnswerMeaningUpdateV1(answer.answer_id,answer.question_id,p["prior_ref"],items,(),"RESOLVED",ref)
    cp = ModelCheckpoint(identity("model-checkpoint",thread.source_prefix_ref,ref),thread.source_prefix_ref,
        ref,update,"RESOLVED",accepted,inactive,(),semantic_snapshot=_json(p),snapshot_ref=ref)
    c = p["packet"]["candidate"]
    return ModelPreparedMeaning(thread,cp,_json(p),material.private_json,_json(p["meaning_packet"]),
        _json(c["surface_proposal"]),_json(c["question_proposal"]),_json(p["native_bindings"]))


def prepare_model_snapshot(request, semantic_input):
    """Source-bound provisional meaning; no provider, alternate author or I/O."""
    try:
        return _prepare_model_snapshot(request, semantic_input)
    except SemanticNotAdopted as exc:
        exc.receipt = semantic_input.receipt if type(semantic_input) is SemanticInput else None
        raise
    except (ValueError,TypeError,KeyError,IndexError,AttributeError,RecursionError):
        raise SemanticNotAdopted("REJECT","model_payload_invalid",
            semantic_input.receipt if type(semantic_input) is SemanticInput else None) from None


def _prepare_model_snapshot(request, semantic_input):
    if (type(semantic_input) is not SemanticInput or semantic_input.semantic_profile != MODEL_PROFILE
        or request.execution_mode != ExecutionMode.OFFLINE_CANDIDATE.value):
        _model_fail("offline_profile_required")
    thread, material = admit_emlis_thread(request), prepare_emlis(request)
    control = thread.control
    if (control.capability_snapshot not in {"FREE_Q1","Q3_FREE"} or len(thread.answers)>1
        or control.admitted_history or control.frame_feedback_sources or control.rejected_frame_keys
        or control.question_control_context.question_limit != 1):
        _model_fail("free_scope_required", "UNSUPPORTED")
    for source in material.payload()["sources"]:
        for text in source["text_fields"].values():
            if type(text) is str and classify_emlis_safety_triage_text(text).safety_triage_kind != TRIAGE_SAFE_OBSERVATION:
                _model_fail("separate_safety_owner_required", "HOLD")
    resume = semantic_input.mode == "RESUME_ADOPTED"
    if resume:
        if semantic_input.receipt is not None or semantic_input.prior_snapshot_json is not None or not semantic_input.snapshot_json:
            _model_fail("resume_input_invalid")
        p = json.loads(semantic_input.snapshot_json)
        _keys(p, {"schema_version","semantic_profile","admission_version","adapter_version","request_ref",
            "source_prefix_ref","source_bindings","packet","meaning_packet","native_bindings","prior_ref",
            "prior_snapshot","receipt","answer_count","question_control","snapshot_ref","proposal_ref"})
        if _json(p) != semantic_input.snapshot_json:
            _model_fail("snapshot_not_canonical")
        packet = _receipt(material,CandidateReceipt(**p["receipt"]))
        prior = p["prior_snapshot"]
    elif semantic_input.mode == "FRESH_CANDIDATE":
        if semantic_input.snapshot_json is not None or request.emlis_thread.prepared_meaning_checkpoint_ref is not None:
            _model_fail("same_prefix_readoption_forbidden")
        packet = _receipt(material,semantic_input.receipt)
        prior = json.loads(semantic_input.prior_snapshot_json) if semantic_input.prior_snapshot_json else None
        p = dict(schema_version=MODEL_SCHEMA,semantic_profile=MODEL_PROFILE,admission_version="1",adapter_version="1",
            request_ref=material.request_id,source_prefix_ref=thread.source_prefix_ref,source_bindings=_source_binding(material),
            packet=packet,meaning_packet=_model_meaning_packet(packet),prior_ref=prior["snapshot_ref"] if prior else None,
            prior_snapshot=prior,receipt=asdict(semantic_input.receipt),answer_count=len(thread.answers),
            question_control=json.loads(_json(asdict(control.question_control_context))))
    else:
        _model_fail("input_mode_invalid")
    if bool(prior) != bool(thread.answers):
        _model_fail("prior_snapshot_required")
    if prior:
        if prior.get("answer_count") != 0 or prior.get("semantic_profile") != MODEL_PROFILE or prior.get("prior_snapshot") is not None:
            _model_fail("prior_lineage_invalid")
        previous_thread = _thread_at(thread,prior)
        previous_request = replace(request,emlis_thread=previous_thread.control)
        old = prepare_model_snapshot(previous_request,SemanticInput("RESUME_ADOPTED",snapshot_json=_json(prior),semantic_profile=MODEL_PROFILE))
        decision, question = model_question(old,parent_request_id=request.request_id)
        actual = control.question_control_context.pending_question
        if question is None or actual != question or actual.question_id != thread.answers[0].source.question_id:
            _model_fail("actual_pending_question_not_bound")
        if control.question_control_context.stop or control.question_control_context.issued_count != 1:
            _model_fail("answer_control_invalid")
    native = _model_packet(packet,material,thread,prior)
    # Source-derived versioning keeps all old chair snapshots byte-identical.
    # A saved or generated family/version label cannot select its own parser.
    version = "2" if native.get("family") == "DAILY_CALM_V1" else "1"
    if resume:
        expected = (MODEL_SCHEMA,MODEL_PROFILE,version,version,material.request_id,thread.source_prefix_ref,
                    _source_binding(material),len(thread.answers),json.loads(_json(asdict(control.question_control_context))))
        actual = tuple(p[k] for k in ("schema_version","semantic_profile","admission_version","adapter_version",
            "request_ref","source_prefix_ref","source_bindings","answer_count","question_control"))
        if (actual != expected or type(p["answer_count"]) is not int or p["packet"] != packet
            or p["meaning_packet"] != _model_meaning_packet(packet) or p["native_bindings"] != native
            or p["prior_ref"] != (prior["snapshot_ref"] if prior else None)
            or p["snapshot_ref"] != _model_semantic_ref(p) or p["proposal_ref"] != _model_proposal_ref(packet)):
            _model_fail("snapshot_binding_invalid")
    else:
        p["admission_version"] = p["adapter_version"] = version
        p["native_bindings"] = native
        p["snapshot_ref"] = _model_semantic_ref(p)
        p["proposal_ref"] = _model_proposal_ref(packet)
    return _model_checkpoint(thread,material,p)


def model_snapshot_payload(prepared):
    if type(prepared) is not ModelPreparedMeaning:
        _model_fail("prepared_type_invalid")
    return json.loads(prepared.semantic_snapshot)


def restore_model_snapshot(request, snapshot_json):
    return prepare_model_snapshot(request,SemanticInput("RESUME_ADOPTED",snapshot_json=snapshot_json,semantic_profile=MODEL_PROFILE))


def model_question(prepared, *, parent_request_id, respect_control=True):
    from .emlis_question import model_question_candidate
    return model_question_candidate(prepared, parent_request_id=parent_request_id,
                                    respect_control=respect_control)


def model_prior_for_messages(request, prior_snapshot_json):
    """Validate the actual source/question lineage before exposing old meaning.

    The returned interpretation excludes all proposed surface/question wording,
    raw provider output and usage metadata. It never becomes a user source.
    """
    try:
        thread = admit_emlis_thread(request)
        if not thread.answers:
            if prior_snapshot_json is not None:
                _model_fail("initial_prior_forbidden")
            return None
        if type(prior_snapshot_json) is not str:
            _model_fail("prior_snapshot_required")
        p = json.loads(prior_snapshot_json)
        if (p.get("semantic_profile") != MODEL_PROFILE or p.get("answer_count") != 0
            or p.get("prior_snapshot") is not None):
            _model_fail("prior_lineage_invalid")
        prior_thread = _thread_at(thread,p)
        old = restore_model_snapshot(replace(request,emlis_thread=prior_thread.control),prior_snapshot_json)
        _, expected_question = model_question(old,parent_request_id=request.request_id)
        actual = thread.control.question_control_context.pending_question
        if (expected_question is None or expected_question != actual
            or thread.answers[0].source.question_id != expected_question.question_id
            or thread.control.question_control_context.stop
            or thread.control.question_control_context.issued_count != 1):
            _model_fail("actual_pending_question_not_bound")
        return dict(semantic_profile=MODEL_PROFILE,snapshot_ref=old.checkpoint.snapshot_ref,
                    meaning_packet=json.loads(old.meaning_json),
                    native_bindings=json.loads(old.native_bindings_json))
    except SemanticNotAdopted:
        raise
    except (ValueError,TypeError,KeyError,AttributeError,IndexError,RecursionError):
        _model_fail("prior_snapshot_invalid")
