from __future__ import annotations

"""Versioned multi-source admission; legacy ledger admission stays exact."""

from dataclasses import asdict, dataclass, replace
from datetime import datetime
import hashlib
import json
from typing import Any

from emlis_ai_evidence_ledger_service import (
    EvidenceSpanResolver, _split_source_text, _detect_type,
)
from emlis_ai_types import EvidenceSpan

from .contracts import EvidenceRef, GenerationRequest, SourceEnvelope
from .emlis_thread_contracts import (
    ANSWER_FIELD, THREAD_SCHEMA, EmlisThreadInputV1, EmlisQuestionControlV1,
    QualifiedEvidenceRef, SupplementalAnswerSource,
)
from .source_kernel import (
    AdmittedTextSource, SourceAdmissionError, _evidence_id,
    _source_envelope_id, freeze_text_source, validate_evidence_refs,
)


def identity(kind: str, *parts: Any) -> str:
    raw = json.dumps(parts, ensure_ascii=False, sort_keys=True,
                     separators=(",", ":"), default=str).encode("utf-8")
    return kind + "-" + hashlib.sha256(raw).hexdigest()


def _timestamp(value: str | None, *, optional: bool = False) -> None:
    if optional and value is None:
        return
    try:
        if type(value) is not str or datetime.fromisoformat(value.replace("Z", "+00:00")).tzinfo is None:
            raise ValueError
    except (ValueError, TypeError):
        raise SourceAdmissionError("emlis_answer_timestamp_invalid") from None


@dataclass(frozen=True, slots=True, repr=False)
class FrozenSupplementalAnswer:
    source: SupplementalAnswerSource
    envelope: SourceEnvelope
    evidence_spans: tuple[EvidenceSpan, ...]
    evidence_refs: tuple[EvidenceRef, ...]


def freeze_supplemental_answer(answer: SupplementalAnswerSource) -> FrozenSupplementalAnswer:
    if type(answer) is not SupplementalAnswerSource:
        raise SourceAdmissionError("emlis_answer_type_invalid")
    if (answer.source_role != "SUPPLEMENTAL_ANSWER"
            or answer.source_version != "cocolon.cmee.supplemental_answer.v1"
            or any(type(x) is not str or not x.strip() for x in (
                answer.answer_id, answer.thread_id, answer.question_id,
                answer.original_source_ref, answer.answer_text_private))):
        raise SourceAdmissionError("emlis_answer_identity_or_text_invalid")
    if type(answer.round_index) is not int or not 1 <= answer.round_index <= 3:
        raise SourceAdmissionError("emlis_q1_answer_round_out_of_scope")
    _timestamp(answer.recorded_at)
    _timestamp(answer.authored_at, optional=True)
    metadata = asdict(answer)
    text = metadata.pop("answer_text_private")
    payload = text.encode("utf-8")
    header = json.dumps(metadata, ensure_ascii=False, sort_keys=True,
                        separators=(",", ":")).encode("utf-8")
    encoding = "CMEE_EMLIS_ANSWER_FRAME_UTF8_V1"
    prefix = (encoding + "\n").encode() + header + b"\n@answer_text_private:" + str(len(payload)).encode() + b"\n"
    raw = prefix + payload
    digest = hashlib.sha256(raw).hexdigest()
    envelope_id = _source_envelope_id(
        source_record_id=answer.answer_id, source_role=answer.source_role,
        source_schema_version=answer.source_version, source_contract_version=THREAD_SCHEMA,
        source_encoding=encoding, label_contract_id="", label_contract_digest="", raw_sha256=digest,
    )
    envelope = SourceEnvelope(envelope_id, answer.answer_id, answer.source_role,
        answer.source_version, THREAD_SCHEMA, encoding, "", "", raw, digest)
    spans, refs = [], []
    for index, part in enumerate(_split_source_text(text), 1):
        span_id = f"s{index}"
        spans.append(EvidenceSpan(span_id, part.text, part.start, part.end,
                                  _detect_type(part.text, ()), 1.0, ANSWER_FIELD))
        fields = dict(source_span_id=span_id, field_path=ANSWER_FIELD,
                      element_index=-1, field_utf8_start=len(prefix),
                      field_utf8_end=len(raw), scalar_start=part.start, scalar_end=part.end,
                      utf8_start=len(prefix) + len(text[:part.start].encode()),
                      utf8_end=len(prefix) + len(text[:part.end].encode()),
                      field_sha256=hashlib.sha256(payload).hexdigest(),
                      literal_sha256=hashlib.sha256(text[part.start:part.end].encode()).hexdigest())
        refs.append(EvidenceRef(evidence_id=_evidence_id(envelope_id=envelope_id, **fields),
                                source_envelope_id=envelope_id, **fields))
    if not spans:
        raise SourceAdmissionError("emlis_answer_empty")
    return FrozenSupplementalAnswer(answer, envelope, tuple(spans), tuple(refs))


class ThreadEvidenceSpanResolver(EvidenceSpanResolver):
    """Source-validated aliases for the existing grammar's local sN ABI."""

    def __init__(self, original: AdmittedTextSource,
                 answers: tuple[FrozenSupplementalAnswer, ...]):
        validate_evidence_refs(original.envelope, original.evidence_refs)
        # Original evidence includes structured refs outside the sN ledger.
        original_refs = {row.source_span_id: row for row in original.evidence_refs}
        spans = list(original.evidence_spans)
        qualified = [QualifiedEvidenceRef(span.span_id, span.span_id, original_refs[span.span_id])
                     for span in spans]
        for answer in answers:
            if freeze_supplemental_answer(answer.source) != answer:
                raise SourceAdmissionError("emlis_answer_canonical_binding_invalid")
            for span, ref in zip(answer.evidence_spans, answer.evidence_refs, strict=True):
                alias = f"s{len(spans) + 1}"
                spans.append(replace(span, span_id=alias))
                qualified.append(QualifiedEvidenceRef(alias, span.span_id, ref))
        self._spans = tuple(spans)
        self._index = {span.span_id: span for span in spans}
        self.qualified_refs = tuple(qualified)
        self._qualified = {row.thread_span_id: row for row in qualified}
        self._source_envelopes = {row.envelope_id: row
                                 for row in (original.envelope, *(a.envelope for a in answers))}
        self.source_contract = THREAD_SCHEMA

    def qualified_ref(self, span_id: str) -> QualifiedEvidenceRef:
        self.resolve(span_id)
        return self._qualified[span_id]

    def source_text_for_contiguous_spans(self, span_ids: tuple[str, ...]) -> str:
        """Read an exact source range, including separators between its spans.

        No evidence identity or segmentation changes. A missing intervening
        span cannot be quoted as if it belonged to the requested range.
        """
        import re
        if not span_ids or len(set(span_ids)) != len(span_ids):
            raise ValueError("emlis_contiguous_source_range_invalid")
        refs = tuple(self.qualified_ref(s).evidence for s in span_ids)
        first, last = refs[0], refs[-1]
        if (any(r.source_envelope_id != first.source_envelope_id or r.field_path != first.field_path
                for r in refs) or first.utf8_start > last.utf8_start):
            raise ValueError("emlis_contiguous_source_range_invalid")
        actual = tuple(q.thread_span_id for q in self.qualified_refs
                       if q.source_envelope_id == first.source_envelope_id
                       and q.evidence.field_path == first.field_path
                       and first.utf8_start <= q.evidence.utf8_start <= last.utf8_start)
        if actual != span_ids:
            raise ValueError("emlis_contiguous_source_range_invalid")
        raw = self._source_envelopes[first.source_envelope_id].raw_utf8[first.utf8_start:last.utf8_end].decode('utf-8')
        return re.sub(r"\s+", " ", raw).strip()


@dataclass(frozen=True, slots=True, repr=False)
class AdmittedEmlisThread:
    original: AdmittedTextSource
    control: EmlisThreadInputV1
    answers: tuple[FrozenSupplementalAnswer, ...]
    source_prefix_ref: str

    def resolver(self) -> ThreadEvidenceSpanResolver:
        return ThreadEvidenceSpanResolver(self.original, self.answers)


def admit_emlis_thread(request: GenerationRequest) -> AdmittedEmlisThread:
    thread = request.emlis_thread
    if type(thread) is not EmlisThreadInputV1 or thread.schema_version != THREAD_SCHEMA:
        raise SourceAdmissionError("emlis_thread_schema_invalid")
    original = freeze_text_source(request)
    if (type(thread.thread_id) is not str or not thread.thread_id.strip()
            or thread.original_source_ref != original.envelope.envelope_id):
        raise SourceAdmissionError("emlis_thread_original_binding_invalid")
    q3 = thread.capability_snapshot in {"Q3_FREE", "Q3_PLUS", "Q3_PREMIUM"}
    if (not q3 and thread.capability_snapshot != "FREE_Q1") or (thread.capability_snapshot in {"FREE_Q1", "Q3_FREE"} and thread.admitted_history != ()):
        raise SourceAdmissionError("emlis_q1_capability_or_history_out_of_scope")
    if (type(thread.answers) is not tuple or len(thread.answers) > (3 if q3 else 1)
            or type(thread.current_round) is not int or thread.current_round != len(thread.answers)):
        raise SourceAdmissionError("emlis_q1_round_invalid")
    control = thread.question_control_context
    if (type(control) is not EmlisQuestionControlV1 or type(control.issued_count) is not int
            or control.issued_count not in range(4 if q3 else 2)
            or type(control.asked_target_refs) is not tuple
            or len(control.asked_target_refs) != control.issued_count
            or len(set(control.asked_target_refs)) != control.issued_count
            or type(control.question_limit) is not int or control.question_limit not in (1, 3)):
        raise SourceAdmissionError("emlis_question_control_invalid")
    answers = tuple(freeze_supplemental_answer(answer) for answer in thread.answers)
    if q3:
        questions = control.issued_questions
        if (type(questions) is not tuple or len(questions) != control.issued_count
                or tuple(q.decision.target_ref for q in questions) != control.asked_target_refs
                or len({q.question_id for q in questions}) != len(questions)
                or len({a.source.answer_id for a in answers}) != len(answers)):
            raise SourceAdmissionError("emlis_q3_question_sequence_invalid")
        for index, answer in enumerate(answers, 1):
            if index > len(questions):
                raise SourceAdmissionError("emlis_q3_answer_question_missing")
            q, a = questions[index - 1], answer.source
            if (a.round_index != index or a.thread_id != thread.thread_id
                    or a.question_id != q.question_id or a.original_source_ref != thread.original_source_ref
                    or q.thread_id != thread.thread_id or q.original_source_ref != thread.original_source_ref):
                raise SourceAdmissionError("emlis_answer_parent_binding_invalid")
        if questions and control.pending_question != questions[-1]:
            raise SourceAdmissionError("emlis_q3_current_question_invalid")
    elif answers:
        question = control.pending_question
        if (question is None or control.issued_count != 1 or control.stop
                or question.thread_id != thread.thread_id
                or question.original_source_ref != thread.original_source_ref
                or question.decision.target_ref not in control.asked_target_refs):
            raise SourceAdmissionError("emlis_answer_question_control_invalid")
        answer = answers[0].source
        if (answer.round_index != 1 or answer.thread_id != thread.thread_id or answer.question_id != question.question_id
                or answer.original_source_ref != thread.original_source_ref):
            raise SourceAdmissionError("emlis_answer_parent_binding_invalid")
    if thread.frame_feedback_sources:
        from .emlis_thread_history import FrameFeedbackSourceV1
        if thread.capability_snapshot != "Q3_PREMIUM" or type(thread.frame_feedback_sources) is not tuple:
            raise SourceAdmissionError("emlis_frame_capability_invalid")
        if any(type(f) is not FrameFeedbackSourceV1 or f.version < 1 or f.status not in {"CONFIRMED","REJECTED","REVISED"}
               or (f.status == "REVISED") != bool(f.correction_text) for f in thread.frame_feedback_sources):
            raise SourceAdmissionError("emlis_frame_feedback_invalid")
    history_guards = []
    if thread.admitted_history:
        from .emlis_thread_history import OwnedHistorySourceV1
        limit = 6 if thread.capability_snapshot == "Q3_PREMIUM" else 3
        if type(thread.admitted_history) is not tuple or len(thread.admitted_history) > limit:
            raise SourceAdmissionError("emlis_history_limit_invalid")
        for source in thread.admitted_history:
            if type(source) is not OwnedHistorySourceV1:
                raise SourceAdmissionError("emlis_history_source_invalid")
            history_guards.append(source.source_guard)
        if len(set(history_guards)) != len(history_guards):
            raise SourceAdmissionError("emlis_history_duplicate")
    prefix = identity("emlis-source-prefix", thread.thread_id, original.envelope.envelope_id,
                      tuple(answer.envelope.envelope_id for answer in answers))
    if q3:
        prefix = identity("emlis-q3-source-prefix", prefix, thread.capability_snapshot, history_guards, thread.rejected_frame_keys, tuple(f.evidence_ref for f in thread.frame_feedback_sources))
    return AdmittedEmlisThread(original, thread, answers, prefix)
