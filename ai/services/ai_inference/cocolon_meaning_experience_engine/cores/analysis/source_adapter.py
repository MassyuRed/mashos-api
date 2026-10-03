"""Freeze owner-resolved saved material, without treating generated text as input.

This is a pure, offline boundary. Authentication, entitlement, retention and
fresh DB reads remain responsibilities of the future Analysis lifecycle caller.
An arbitrary HTTP caller must never be allowed to construct these requests.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
import hashlib
import json

from emlis_ai_current_input_bundle import normalize_emlis_current_input
from emlis_ai_evidence_ledger_service import build_evidence_ledger
from ...contracts import EvidenceRef, SourceEnvelope
from ...source_kernel import _text_span_raw_subrange

POLICY = 'cocolon.cmee.analysis.observed.offline.v1'
ORIGINAL_FIELDS = frozenset(('id', 'created_at', 'memo', 'memo_action',
                             'category', 'emotions', 'emotion_details'))


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def commitment(value: object) -> str:
    return 'sha256:' + hashlib.sha256(canonical_bytes(value)).hexdigest()


class AnalysisSourceError(ValueError):
    """Only fixed reason codes, never private values, cross this boundary."""


@dataclass(frozen=True, slots=True, repr=False)
class AnalysisSupplement:
    source_id: str
    owner_scope: str
    parent_record_ref: str
    parent_record_version: str
    text: str
    source_version: str
    # Only a saved, permitted supplemental answer, not question/control text.
    source_role: str = 'SUPPLEMENTAL_ANSWER'


@dataclass(frozen=True, slots=True, repr=False)
class AnalysisSavedRecord:
    owner_scope: str
    saved_record_ref: str
    saved_record_version: str
    original_json: str
    supplements: tuple[AnalysisSupplement, ...] = ()
    record_state: str = 'LIVE'


@dataclass(frozen=True, slots=True, repr=False)
class AnalysisObservedMapRequest:
    request_id: str
    authenticated_owner_scope: str
    period_start: str
    period_end: str
    members: tuple[AnalysisSavedRecord, ...]
    core_id: str = 'analysis'
    product_job: str = 'MAP_AND_EXPLORE'
    operation: str = 'ANALYSIS_OBSERVED_MAP'
    execution_mode: str = 'OFFLINE_CANDIDATE'
    locale: str = 'ja-JP'


@dataclass(frozen=True, slots=True, repr=False)
class AnalysisSource:
    envelope: SourceEnvelope
    record_ref: str
    record_version: str
    normalized: dict = field(repr=False)
    spans: tuple = field(repr=False)
    evidence: tuple[EvidenceRef, ...] = field(repr=False)


@dataclass(frozen=True, slots=True, repr=False)
class AnalysisSourceMember:
    saved_record_ref: str
    saved_record_version: str
    member_role: str
    source_commitment: str
    inclusion_status: str
    inclusion_or_exclusion_reason: str
    child_source_envelope_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True, repr=False)
class AnalysisSourceSet:
    source_set_ref: str
    owner_scope: str
    period: tuple[str, str]
    members: tuple[AnalysisSourceMember, ...]
    sources: tuple[AnalysisSource, ...]


def _time(value: str) -> datetime:
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if result.tzinfo is None:
            raise ValueError
        return result.astimezone(timezone.utc)
    except (ValueError, TypeError, AttributeError):
        raise AnalysisSourceError('analysis_timestamp_invalid') from None


def _source(record, role, source_id, version, original):
    normalized = normalize_emlis_current_input(original)
    spans = tuple(build_evidence_ledger(normalized))
    # Length-prefixed, exact original fields; offsets never refer to normalized
    # or generated text. Labels remain available to the existing semantic owner
    # but are not independently promoted to observed route facts.
    raw = bytearray()
    fields = {}
    for key in ('memo', 'memo_action'):
        value = original.get(key) or ''
        if not isinstance(value, str):
            raise AnalysisSourceError('analysis_text_field_invalid')
        encoded = value.encode('utf-8')
        raw.extend((key + ':' + str(len(encoded)) + ':').encode())
        start = len(raw)
        raw.extend(encoded)
        fields[key] = (value, start, len(raw))
    raw_bytes = bytes(raw)
    envelope_id = 'analysis-source:' + commitment([record.saved_record_ref,
        record.saved_record_version, role, source_id, version, POLICY])[7:]
    envelope = SourceEnvelope(envelope_id, source_id, role, POLICY, POLICY,
        'utf-8', POLICY, commitment(POLICY), raw_bytes,
        hashlib.sha256(raw_bytes).hexdigest())
    evidence = []
    for span in spans:
        if span.source_field not in fields or span.start_index < 0:
            continue
        value, field_start, field_end = fields[span.source_field]
        start, end = _text_span_raw_subrange(raw_field_text=value,
            normalized_field_text=normalized[span.source_field], span=span)
        literal = value[start:end].encode('utf-8')
        eid = 'analysis-evidence:' + commitment([envelope_id,
            span.source_field, start, end])[7:]
        evidence.append(EvidenceRef(eid, span.span_id, envelope_id,
            span.source_field, 0, field_start, field_end, start, end,
            field_start + len(value[:start].encode('utf-8')),
            field_start + len(value[:end].encode('utf-8')),
            hashlib.sha256(value.encode('utf-8')).hexdigest(),
            hashlib.sha256(literal).hexdigest()))
    return AnalysisSource(envelope, record.saved_record_ref,
        record.saved_record_version, normalized, spans, tuple(evidence))


def source_field_text(source: AnalysisSource, field_name: str) -> str:
    ref = next((e for e in source.evidence if e.field_path == field_name), None)
    if ref is None:
        raise AnalysisSourceError('analysis_source_field_unbound')
    return source.envelope.raw_utf8[ref.field_utf8_start:ref.field_utf8_end].decode('utf-8')


def scoped_source_view(source: AnalysisSource, start: int, end: int) -> AnalysisSource:
    """Parse a proved answer range without creating a derived source envelope.

    Local ledger coordinates belong only to the parser view. Every returned
    EvidenceRef still addresses the complete, unchanged supplemental field.
    """
    raw = source_field_text(source, 'memo')
    if not (0 <= start < end <= len(raw)):
        raise AnalysisSourceError('analysis_answer_range_invalid')
    base = next(e for e in source.evidence if e.field_path == 'memo')
    fragment = raw[start:end]
    normalized = normalize_emlis_current_input({'memo': fragment})
    spans = tuple(build_evidence_ledger(normalized))
    evidence = []
    for span in spans:
        if span.source_field != 'memo':
            continue
        a, b = _text_span_raw_subrange(raw_field_text=fragment,
            normalized_field_text=normalized['memo'], span=span)
        a, b = start + a, start + b
        evidence.append(replace(base,
            evidence_id='analysis-evidence:' + commitment([
                source.envelope.envelope_id, 'memo', a, b])[7:],
            source_span_id=span.span_id, scalar_start=a, scalar_end=b,
            utf8_start=base.field_utf8_start + len(raw[:a].encode('utf-8')),
            utf8_end=base.field_utf8_start + len(raw[:b].encode('utf-8')),
            literal_sha256=hashlib.sha256(raw[a:b].encode('utf-8')).hexdigest()))
    return replace(source, normalized=normalized, spans=spans,
                   evidence=tuple(evidence))


def freeze_analysis_sources(request: AnalysisObservedMapRequest) -> AnalysisSourceSet:
    if (type(request) is not AnalysisObservedMapRequest or
            request.execution_mode != 'OFFLINE_CANDIDATE' or
            request.core_id != 'analysis' or
            request.product_job != 'MAP_AND_EXPLORE' or
            request.operation != 'ANALYSIS_OBSERVED_MAP' or
            request.locale != 'ja-JP' or not request.request_id or
            not isinstance(request.authenticated_owner_scope, str) or
            not request.authenticated_owner_scope.strip() or
            not isinstance(request.members, tuple)):
        raise AnalysisSourceError('analysis_request_out_of_scope')
    start, end = _time(request.period_start), _time(request.period_end)
    if start >= end:
        raise AnalysisSourceError('analysis_period_invalid')
    originals, versions, supplements = {}, {}, set()
    for member in request.members:
        if (type(member) is not AnalysisSavedRecord or
                member.owner_scope != request.authenticated_owner_scope):
            raise AnalysisSourceError('analysis_owner_mismatch')
        if member.record_state != 'LIVE':
            raise AnalysisSourceError('analysis_record_not_live')
        if not isinstance(member.supplements, tuple) or len(member.supplements) > 1:
            raise AnalysisSourceError('analysis_supplement_cardinality')
        if any(type(s) is not AnalysisSupplement for s in member.supplements):
            raise AnalysisSourceError('analysis_supplement_binding_invalid')
        try:
            original = json.loads(member.original_json)
        except (TypeError, ValueError):
            raise AnalysisSourceError('analysis_original_invalid') from None
        if (not isinstance(original, dict) or set(original) != ORIGINAL_FIELDS or
                not isinstance(member.saved_record_ref, str) or
                not member.saved_record_ref or original['id'] != member.saved_record_ref):
            raise AnalysisSourceError('analysis_original_shape_invalid')
        if commitment(original) != member.saved_record_version:
            raise AnalysisSourceError('analysis_record_version_mismatch')
        identity = commitment([original, [
            [s.source_id, s.owner_scope, s.parent_record_ref, s.parent_record_version,
             s.text, s.source_version, s.source_role] for s in member.supplements
             if type(s) is AnalysisSupplement]])
        if member.saved_record_ref in versions:
            if versions[member.saved_record_ref] != identity:
                raise AnalysisSourceError('analysis_duplicate_record_conflict')
            continue
        versions[member.saved_record_ref] = identity
        originals[member.saved_record_ref] = (member, original)
    members, sources = [], []
    for ref, (member, original) in sorted(originals.items(),
            key=lambda item: (_time(item[1][1]['created_at']), item[0])):
        included = start <= _time(original['created_at']) < end
        children = []
        for supplement in member.supplements:
            if (type(supplement) is not AnalysisSupplement or
                    supplement.owner_scope != request.authenticated_owner_scope or
                    supplement.parent_record_ref != ref or
                    supplement.parent_record_version != member.saved_record_version or
                    supplement.source_role != 'SUPPLEMENTAL_ANSWER' or
                    not isinstance(supplement.source_id, str) or
                    not supplement.source_id or supplement.source_id in supplements or
                    not isinstance(supplement.text, str) or not supplement.text.strip() or
                    supplement.source_version != commitment(supplement.text)):
                raise AnalysisSourceError('analysis_supplement_binding_invalid')
            supplements.add(supplement.source_id)
        if included:
            child = _source(member, 'ORIGINAL_INPUT', ref,
                            member.saved_record_version, original)
            sources.append(child)
            children.append(child.envelope.envelope_id)
            for supplement in member.supplements:
                child = _source(member, 'SUPPLEMENTAL_ANSWER', supplement.source_id,
                    supplement.source_version, {'id': ref, 'memo': supplement.text})
                sources.append(child)
                children.append(child.envelope.envelope_id)
        members.append(AnalysisSourceMember(ref, member.saved_record_version,
            'PERIOD_RECORD_IDENTITY', versions[ref],
            'INCLUDED' if included else 'EXCLUDED',
            'IN_PERIOD' if included else 'OUTSIDE_PERIOD', tuple(children)))
    period = (start.isoformat(), end.isoformat())
    source_set_ref = 'analysis-set:' + commitment([
        request.authenticated_owner_scope, period, [asdict(m) for m in members], POLICY])[7:]
    return AnalysisSourceSet(source_set_ref, request.authenticated_owner_scope,
                             period, tuple(members), tuple(sources))
