"""Bounded private refined Piece sources through the existing author.

This slice composes an original, its effective prior replacement fragments,
and one explicitly selected real answer. Saved-source admission owns the
shared update proof; this module retains source-qualified complete-clause
ranges without resolving another target or rewriting the source envelopes.
It does not authenticate a caller or issue a preview.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, fields, replace
import base64
import hashlib
import json
import re
from typing import TYPE_CHECKING

from piece_v2_content_policy import (
    check_existing_detectors, choose_format, unavailable,
    validate_candidate_text, validate_source_meaning_preservation,
)
from piece_v2_contract import canonical_json_bytes
from .contracts import EngineStatus
from .emlis_thread_contracts import SupplementalAnswerSource, InterpretationCorrectionSource
from .emlis_thread_source import FrozenSupplementalAnswer, freeze_supplemental_answer
from .piece_source import PieceSourceMeaning, build_piece_source_meaning
from .emlis_answer_update import BoundFeelingCircumstance

if TYPE_CHECKING:
    from .cores.analysis.source_adapter import AnalysisCircumstanceControl


@dataclass(frozen=True, slots=True)
class PieceRelativeFeelingAnchor:
    """Exact saved QUESTION_FOCUS evidence for one selected answer."""
    question_id: str
    answer_id: str
    event_range: tuple[int, int]


@dataclass(frozen=True, slots=True, repr=False)
class PieceRefinedSourceSnapshot:
    original: object
    supplemental: SupplementalAnswerSource
    supplemental_owner_id: str
    question_need_decision_identity: str
    refined_result_identity: str
    original_commitment: str
    supplemental_commitment: str
    opted_in: bool
    supplemental_update_operation: str
    # Populated only by the saved answer-update source owner. These are
    # exact scalar ranges of the unchanged original fields and real answer.
    original_active_ranges: tuple[tuple[str, int, int], ...] = ()
    supplemental_active_range: tuple[int, int] | None = None
    # Current, source-bound replacement fragments from preceding rounds.
    # Independent unselected ADD answers are not included here.
    prior_revisions: tuple[tuple[SupplementalAnswerSource, tuple[int, int]], ...] = ()
    effective_round_sources: bool = False
    feeling_question_id: str | None = None
    feeling_circumstance: BoundFeelingCircumstance | None = None
    relative_feeling_anchor: PieceRelativeFeelingAnchor | None = None


@dataclass(frozen=True, slots=True, repr=False)
class PieceCorrectedSourceSnapshot:
    original: object
    correction: InterpretationCorrectionSource
    original_commitment: str
    correction_commitment: str
    corrected_result_identity: str
    opted_in: bool
    original_active_ranges: tuple[tuple[str, int, int], ...]
    correction_active_range: tuple[int, int] | None
    correction_update_operation: str
    as_of: str
    prior_corrections: tuple[InterpretationCorrectionSource, ...] = ()
    answer_sources: tuple[SupplementalAnswerSource, ...] = ()
    selected_answer_id: str | None = None
    question_need_decision_identity: str | None = None
    circumstance_control: AnalysisCircumstanceControl | None = None


@dataclass(frozen=True, slots=True, repr=False)
class PieceCorrectionMeaning(PieceSourceMeaning):
    source_snapshot: PieceCorrectedSourceSnapshot | None = None
    frozen_correction: object | None = None
    active_range: tuple[int, int] | None = None


@dataclass(frozen=True, slots=True, repr=False)
class PieceSupplementalMeaning(PieceSourceMeaning):
    # A real answer envelope, never an original-input identity. Local grammar
    # coordinates address answer_text_private; UTF-8 evidence addresses this
    # metadata-framed envelope from the existing answer-source owner.
    frozen_answer: FrozenSupplementalAnswer | None = None
    grammar_owner_id: str = ''
    feeling_question_id: str | None = None
    active_range: tuple[int, int] | None = None


@dataclass(frozen=True, slots=True, repr=False)
class PieceActiveOriginalMeaning(PieceSourceMeaning):
    active_ranges: tuple[tuple[str, int, int], ...] = ()
    effective_round_sources: bool = False


@dataclass(frozen=True, slots=True, repr=False)
class PieceRefinedMeaning:
    source: PieceRefinedSourceSnapshot | PieceCorrectedSourceSnapshot
    source_ref: str
    original: PieceSourceMeaning | None
    supplemental: PieceSupplementalMeaning | PieceCorrectionMeaning | None
    prior_revisions: tuple[PieceSupplementalMeaning, ...] = ()


@dataclass(frozen=True, slots=True, repr=False)
class PieceRefinedPlan:
    source_ref: str
    original_plan: object | None
    supplemental_plan: object
    # No relation is invented across sources. Preserve the original blocks,
    # then the answer blocks, with explicit source boundaries in private state.
    source_roles: tuple[str, ...] = ('ORIGINAL_USER_INPUT', 'SUPPLEMENTAL_ANSWER')
    eligible_formats: tuple[str, ...] = ('short_essay',)
    prior_revision_plans: tuple[object, ...] = ()


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _require(value, code='piece_refined_source_binding'):
    if not value:
        raise unavailable(code)


def _source_payload(source):
    from piece_v2_generation import PieceSourceSnapshot
    _require(type(source) in (PieceRefinedSourceSnapshot, PieceCorrectedSourceSnapshot))
    _require(type(source.original) is PieceSourceSnapshot)
    original = asdict(source.original)
    raw = original.pop('saved_original_json')
    _require(type(raw) is bytes)
    original['saved_original_base64'] = base64.b64encode(raw).decode('ascii')
    result = asdict(source)
    result['original'] = original
    if type(source) is PieceCorrectedSourceSnapshot:
        if source.circumstance_control is None:
            del result['circumstance_control']
        else:
            result['circumstance_control'] = json.loads(json.dumps(result['circumstance_control']))
        if not source.prior_corrections:
            del result['prior_corrections']
        else:
            result['prior_corrections'] = [asdict(c) for c in source.prior_corrections]
        if source.answer_sources:
            result['answer_sources'] = [asdict(a) for a in source.answer_sources]
        else:
            for key in ('answer_sources', 'selected_answer_id', 'question_need_decision_identity'):
                del result[key]
        result['source_kind'] = 'USER_INTERPRETATION_CORRECTION'
        result['original_active_ranges'] = [list(row) for row in source.original_active_ranges]
        result['correction_active_range'] = (None if source.correction_active_range is None
                                             else list(source.correction_active_range))
        return result
    # Existing ADD source identities and private saved bytes remain exact.
    if source.feeling_question_id is None:
        del result['feeling_question_id']
    if source.feeling_circumstance is None:
        del result['feeling_circumstance']
    else:
        for key in ('feeling_range', 'circumstance_range'):
            result['feeling_circumstance'][key] = list(result['feeling_circumstance'][key])
    if source.relative_feeling_anchor is None:
        del result['relative_feeling_anchor']
    else:
        result['relative_feeling_anchor']['event_range'] = list(source.relative_feeling_anchor.event_range)
    if not source.original_active_ranges and source.supplemental_active_range is None:
        del result['original_active_ranges']
        del result['supplemental_active_range']
    if source.original_active_ranges:
        result['original_active_ranges'] = [list(row) for row in source.original_active_ranges]
    if source.supplemental_active_range is not None:
        result['supplemental_active_range'] = list(source.supplemental_active_range)
    if not source.effective_round_sources:
        _require(not source.prior_revisions, 'piece_refined_active_range_binding')
        del result['prior_revisions']
        del result['effective_round_sources']
    else:
        result['prior_revisions'] = [dict(answer=asdict(answer), active_range=list(active_range))
                                     for answer, active_range in source.prior_revisions]
    return result


def refined_source_ref(source) -> str:
    prefix = 'piece-corrected:' if type(source) is PieceCorrectedSourceSnapshot else 'piece-refined:'
    payload = _source_payload(source)
    if type(source) is PieceCorrectedSourceSnapshot:
        # Qualification is checked at each read; a moving read clock is not
        # a new source or a new author request. Actual source dates stay bound.
        del payload['as_of']
    return prefix + _sha(canonical_json_bytes(payload))


def _corrected_source_set(original, correction, *, as_of, prior_corrections=(), answer_sources=(),
                          circumstance_control=None):
    """Reuse the shared source freezer; no Analysis graph or AI text is read."""
    from piece_v2_generation import PieceSourceSnapshot
    from .cores.analysis.source_adapter import (
        AnalysisCircumstanceControl, AnalysisSavedRecord, AnalysisSupplement, AnalysisObservedMapRequest, freeze_analysis_sources,
        commitment, _time,
    )
    _require(type(original) is PieceSourceSnapshot
        and type(original.saved_original_json) is bytes
        and type(correction) is InterpretationCorrectionSource,
        'piece_correction_source_binding')
    raw = json.loads(original.saved_original_json)
    _require(type(raw) is dict and raw.get('id') == original.saved_input_id
        and correction.source_role == 'USER_INTERPRETATION_CORRECTION'
        and correction.correction_id != original.saved_input_id
        and all(type(value) is str and bool(value.strip()) for value in (
            correction.thread_id, correction.target_event_id, correction.correction_id,
            correction.original_source_ref, correction.target_text, correction.explanation,
            correction.recorded_at, as_of)), 'piece_correction_source_binding')
    start, end, stamp = _time(raw['created_at'], saved_utc=True), _time(as_of), _time(correction.recorded_at)
    _require(start < end and start <= stamp <= end, 'piece_correction_source_clock')
    _require(circumstance_control is None or (type(circumstance_control) is AnalysisCircumstanceControl
        and answer_sources == (circumstance_control.answer,)), 'piece_correction_answer_binding')
    member = AnalysisSavedRecord(original.owner_id, original.saved_input_id,
        commitment(raw), original.saved_original_json.decode('utf-8'),
        supplements=tuple(AnalysisSupplement(a.answer_id, original.owner_id, original.saved_input_id,
            commitment(raw), a.answer_text_private, commitment(a.answer_text_private),
            circumstance_control=circumstance_control) for a in answer_sources),
        interpretation_corrections=(*prior_corrections, correction))
    request = AnalysisObservedMapRequest('piece-corrected-source', original.owner_id,
        start.isoformat(), end.isoformat(), (member,))
    return freeze_analysis_sources(request)


def _corrected_projection(original, correction, *, as_of, prior_corrections=(), answer_sources=(),
                          circumstance_control=None):
    """Apply the shared original-clause updates without selecting every ADD."""
    from .cores.analysis.intent_compiler import _active_sources, _REPLACEMENT, _WITHDRAWAL, _self_propositions
    from .cores.analysis.source_adapter import _time, source_field_text
    _require(type(prior_corrections) is tuple
        and all(type(c) is InterpretationCorrectionSource for c in prior_corrections),
        'piece_correction_source_binding')
    history = (*prior_corrections, correction)
    _require(len({c.correction_id for c in history}) == len(history)
        and all(c.thread_id == correction.thread_id and c.original_source_ref == correction.original_source_ref
            for c in history), 'piece_correction_source_binding')
    stamps = [_time(c.recorded_at) for c in history]
    raw_original = json.loads(original.saved_original_json)
    start = _time(raw_original['created_at'], saved_utc=True)
    _require(stamps == sorted(stamps) and start <= stamps[0]
        and stamps[-1] <= _time(as_of), 'piece_correction_source_clock')
    _require(type(answer_sources) is tuple and len(answer_sources) <= 3
        and all(type(a) is SupplementalAnswerSource for a in answer_sources),
        'piece_correction_answer_binding')
    if answer_sources:
        _require([a.round_index for a in answer_sources] == list(range(1,len(answer_sources)+1))
            and len({a.answer_id for a in answer_sources}) == len(answer_sources)
            and all(a.thread_id == correction.thread_id and a.original_source_ref == correction.original_source_ref
                and a.answer_id not in {original.saved_input_id, *[c.correction_id for c in history]}
                for a in answer_sources), 'piece_correction_answer_binding')
        astamps = [_time(a.recorded_at) for a in answer_sources]
        _require(start <= astamps[0] and astamps == sorted(astamps) and astamps[-1] <= stamps[0],
            'piece_correction_source_clock')
        for a in answer_sources:
            freeze_supplemental_answer(a)
    frozen = _corrected_source_set(original, correction, as_of=as_of,
        prior_corrections=prior_corrections, answer_sources=answer_sources, circumstance_control=circumstance_control)
    # The full freezer retains every real answer. Fully read ADD claims
    # participate in the existing compatibility checks. An unselected,
    # unread prior ADD qualifies history only; it cannot supply a new claim.
    ordinary_answer_ids = {a.answer_id for a in answer_sources if not (
        _REPLACEMENT.fullmatch(a.answer_text_private.strip().rstrip('。．.'))
        or _WITHDRAWAL.fullmatch(a.answer_text_private.strip().rstrip('。．.')))}
    opaque_ids=set()
    from .cores.analysis.source_adapter import AnalysisSourceError
    bound_feeling = None
    for view in frozen.sources:
        if view.envelope.source_record_id not in ordinary_answer_ids:
            continue
        if view.feeling_circumstance_ranges is not None:
            bound_feeling, (start, end) = view.feeling_circumstance_ranges
            literal = source_field_text(view, 'memo')
            _require(0 <= start < end <= len(literal) and not literal[:start].strip()
                and literal[end:].strip() in ('', '。', '！', '!')
                and not re.search(r'[\r\n?？「」『』]', literal), 'piece_feeling_circumstance_source_binding')
            continue
        try:
            _self_propositions(view,require_complete=True)
        except AnalysisSourceError as exc:
            if str(exc) != 'analysis_supplement_interpretation_pending':
                raise
            opaque_ids.add(view.envelope.source_record_id)
    _require(circumstance_control is None or bound_feeling is not None,
        'piece_feeling_circumstance_source_binding')
    _require(not answer_sources or answer_sources[-1].answer_id not in opaque_ids,
        'piece_correction_selected_answer_pending')
    update_view = replace(frozen,sources=tuple(v for v in frozen.sources
        if v.envelope.source_record_id not in opaque_ids)) if opaque_ids else frozen
    active, excluded, updates, _ = _active_sources(update_view)
    by_id = {s.envelope.source_record_id:s for s in frozen.sources}
    original_source = next(s for s in frozen.sources if s.envelope.source_role == 'ORIGINAL_INPUT')
    removed = [e for e in original_source.evidence
        if e.source_span_id in excluded.get(original_source.envelope.envelope_id, set())]
    _require(len(removed) == len(updates), 'piece_correction_active_range_binding')
    full = build_piece_source_meaning(original, expected_owner_id=original.owner_id,
        expected_saved_input_id=original.saved_input_id, expected_source_version=original.source_version,
        bound_complete_clause=bound_feeling is not None)
    removed_refs = []
    for target in removed:
        matches = [ref for ref in full.evidence if ref.field_path == target.field_path
            and ref.scalar_start == target.scalar_start
            and raw_original[ref.field_path][ref.scalar_start:ref.scalar_end].rstrip('。．.!！?？')
                == raw_original[target.field_path][target.scalar_start:target.scalar_end].rstrip('。．.!！?？')]
        _require(len(matches) == 1, 'piece_correction_active_range_binding')
        removed_refs.extend(matches)
    ranges = tuple((r.field_path, r.scalar_start, r.scalar_end) for r in full.evidence if r not in removed_refs)
    _require(bool(ranges) or (bound_feeling is not None and len(removed) == 1
        and removed[0].field_path == 'memo' and (removed[0].scalar_start, removed[0].scalar_end) == bound_feeling
        and updates[0].operation == 'REVISE'), 'piece_correction_active_range_binding')
    if answer_sources:
        # A quote cannot silently choose ORIGINAL when an active answer says
        # the same thing. AI target excerpts are not person-source selectors.
        for update in updates:
            ref = update.target_evidence
            literal = raw_original[ref.field_path][ref.scalar_start:ref.scalar_end].strip().rstrip('。．.')
            _require(all(literal not in a.answer_text_private for a in answer_sources
                if a.answer_id in ordinary_answer_ids), 'piece_correction_ambiguous_person_source')
            for view in active:
                if view.envelope.source_role != 'SUPPLEMENTAL_ANSWER':
                    continue
                text = source_field_text(view, 'memo')
                if view.scoped_memo_range is not None:
                    text = text[slice(*view.scoped_memo_range)]
                _require(literal not in text, 'piece_correction_ambiguous_person_source')
    def row(proper, *, correction_role):
        fs = by_id.get(proper.correction_id if correction_role else proper.answer_id)
        _require(fs is not None, 'piece_correction_source_binding')
        changes = [u for u in updates if u.answer_evidence_refs
            and u.answer_evidence_refs[0].source_envelope_id == fs.envelope.envelope_id]
        _require(len(changes) <= 1 and (not correction_role or len(changes) == 1),
            'piece_correction_update_not_supported')
        views = [v for v in active if v.envelope.envelope_id == fs.envelope.envelope_id]
        operation = changes[0].operation if changes else 'ADD'
        if not correction_role and proper.answer_id in opaque_ids:
            _require(not changes and not views, 'piece_correction_active_range_binding'); active_range = None
        elif operation == 'WITHDRAW':
            _require(not views, 'piece_correction_active_range_binding'); active_range = None
        else:
            _require(len(views) == 1, 'piece_correction_active_range_binding')
            active_range = views[0].scoped_memo_range
            _require((operation == 'REVISE') == (active_range is not None),
                'piece_correction_active_range_binding')
        return proper,operation,active_range,'sha256:'+fs.envelope.raw_sha256,fs
    return ranges,tuple(row(c,correction_role=True) for c in history),tuple(
        row(a,correction_role=False) for a in answer_sources)


def corrected_history_ranges(original, correction, *, as_of, prior_corrections=(), answer_sources=(),
                             circumstance_control=None):
    ranges, rows, _ = _corrected_projection(original,correction,as_of=as_of,
        prior_corrections=prior_corrections,answer_sources=answer_sources,circumstance_control=circumstance_control)
    return ranges,rows


def corrected_answer_ranges(source):
    _,_,rows = _corrected_projection(source.original,source.correction,as_of=source.as_of,
        prior_corrections=source.prior_corrections,answer_sources=source.answer_sources,
        circumstance_control=source.circumstance_control)
    return rows


def corrected_active_ranges(original, correction, *, as_of, prior_corrections=(), answer_sources=(),
                            circumstance_control=None):
    ranges, rows = corrected_history_ranges(original, correction, as_of=as_of,
        prior_corrections=prior_corrections, answer_sources=answer_sources, circumstance_control=circumstance_control)
    _, operation, active_range, commitment, _ = rows[-1]
    return operation, ranges, active_range, commitment


def _validate_corrected_source(source):
    _require(type(source) is PieceCorrectedSourceSnapshot and source.opted_in is True,
        'piece_correction_opt_in_required')
    _require(source.original_commitment == 'sha256:' + _sha(source.original.saved_original_json)
        and type(source.corrected_result_identity) is str and bool(source.corrected_result_identity.strip())
        and source.corrected_result_identity not in {
            source.original.saved_input_id, source.correction.correction_id, source.correction.target_event_id},
        'piece_correction_source_binding')
    _require((not source.answer_sources and source.selected_answer_id is None
            and source.question_need_decision_identity is None)
        or (bool(source.answer_sources) and source.selected_answer_id == source.answer_sources[-1].answer_id
            and type(source.question_need_decision_identity) is str
            and bool(source.question_need_decision_identity.strip())), 'piece_correction_answer_opt_in')
    expected = corrected_active_ranges(source.original, source.correction, as_of=source.as_of,
        prior_corrections=source.prior_corrections, answer_sources=source.answer_sources,
        circumstance_control=source.circumstance_control)
    _require(expected == (source.correction_update_operation, source.original_active_ranges,
        source.correction_active_range, source.correction_commitment), 'piece_correction_active_range_binding')
    return next(s for s in _corrected_source_set(source.original, source.correction, as_of=source.as_of,
            prior_corrections=source.prior_corrections, answer_sources=source.answer_sources,
            circumstance_control=source.circumstance_control).sources
        if s.envelope.source_role == 'USER_INTERPRETATION_CORRECTION'
        and s.envelope.source_record_id == source.correction.correction_id)


def _correction_meaning(source):
    """Bind the qualified replacement to its real correction envelope."""
    from piece_v2_generation import PieceSourceSnapshot
    from .source_kernel import _evidence_id
    frozen = _validate_corrected_source(source)
    start, end = source.correction_active_range
    raw, owner = source.correction.explanation, source.original.owner_id
    literal = raw[start:end]
    from .piece_source import _qualified_self_topic, _literal_self_account
    from .cores.analysis.intent_compiler import _finite_feeling_proposition
    statement = literal if literal.endswith(tuple('。！？!?')) else literal + '。'
    # A replacement for the proved original feeling can retain its own
    # complete written feeling. Its source words do not inherit the old Q&A relation.
    feeling = (_finite_feeling_proposition(statement[:-1])
        if source.circumstance_control is not None else None)
    bound_feeling = feeling is not None and feeling.actor == 'SELF'
    _require(_qualified_self_topic(statement) is not None
        and (bound_feeling or _literal_self_account(statement)),
        'piece_correction_replacement_not_self_contained')
    parsed = build_piece_source_meaning(PieceSourceSnapshot(owner, source.correction.correction_id,
        frozen.envelope.source_schema_version, statement), expected_owner_id=owner,
        expected_saved_input_id=source.correction.correction_id,
        expected_source_version=frozen.envelope.source_schema_version, bound_complete_clause=bound_feeling)
    _require(len(parsed.graph.nodes) == 1 and not parsed.role_bindings
        and not parsed.nominal_references and not parsed.personal_evaluations and not parsed.expression_scopes,
        'piece_correction_replacement_not_self_contained')
    field = next(e for e in frozen.evidence if e.field_path == 'memo')
    refs, ids = [], {}
    for local in parsed.evidence:
        a, b = start + local.scalar_start, start + min(local.scalar_end, len(literal))
        values = dict(source_span_id=local.source_span_id, field_path=field.field_path,
            element_index=field.element_index, field_utf8_start=field.field_utf8_start,
            field_utf8_end=field.field_utf8_end, scalar_start=a, scalar_end=b,
            utf8_start=field.field_utf8_start + len(raw[:a].encode('utf-8')),
            utf8_end=field.field_utf8_start + len(raw[:b].encode('utf-8')),
            field_sha256=field.field_sha256, literal_sha256=_sha(raw[a:b].encode('utf-8')))
        eid = _evidence_id(envelope_id=frozen.envelope.envelope_id, **values)
        ids[local.evidence_id] = eid
        refs.append(replace(local, evidence_id=eid, source_envelope_id=frozen.envelope.envelope_id, **values))
    graph = replace(parsed.graph, source_envelope_id=frozen.envelope.envelope_id,
        graph_id='piece-graph:' + _sha(canonical_json_bytes([frozen.envelope.envelope_id,
            parsed.graph.graph_id, list(source.correction_active_range)])),
        nodes=tuple(replace(n, value=literal, evidence_ids=tuple(ids[e] for e in n.evidence_ids))
            for n in parsed.graph.nodes),
        edges=tuple(replace(e, evidence_ids=tuple(ids[r] for r in e.evidence_ids)) for e in parsed.graph.edges),
        owner_dispositions=tuple(replace(o, evidence_refs=tuple(ids[e] for e in o.evidence_refs))
            for o in parsed.graph.owner_dispositions))
    values = {f.name: getattr(parsed, f.name) for f in fields(PieceSourceMeaning)}
    values.update(envelope=frozen.envelope, graph=graph, evidence=tuple(refs),
        sentences=tuple(replace(s, evidence_id=ids[s.evidence_id], source_start=start+s.source_start,
            source_end=start+min(s.source_end, len(literal))) for s in parsed.sentences))
    return PieceCorrectionMeaning(**values, source_snapshot=source, frozen_correction=frozen,
        active_range=source.correction_active_range)


def validate_correction_meaning(meaning):
    _require(type(meaning) is PieceCorrectionMeaning and meaning == _correction_meaning(meaning.source_snapshot),
        'piece_correction_evidence_binding')


def _supplemental_meaning(answer, owner_id, active_range=None, *, feeling_question_id=None,
                          bound_complete_clause=False):
    """Adapt existing finite grammar, then bind every node to its answer source.

    The temporary text view is only a parser input. It is not retained as
    semantic source or saved original, nor joined to the actual original.
    The returned graph and all evidence use the answer owner's real envelope.
    """
    from piece_v2_generation import PieceSourceSnapshot
    from .source_kernel import _evidence_id
    frozen = freeze_supplemental_answer(answer)
    _require(feeling_question_id is None or (feeling_question_id == answer.question_id and active_range is None),
             'piece_refined_question_binding')
    raw = answer.answer_text_private
    start, end = (0, len(raw)) if active_range is None else active_range
    _require(type(start) is int and type(end) is int and 0 <= start < end <= len(raw))
    literal = raw[start:end]
    # A source-bound complete SELF replacement can end at its closing quote.
    # The stop below is grammar-only. It never enters the node/evidence/raw
    # source and does not supply an omitted predicate or narrator.
    grammar_stop = active_range is not None and literal[-1] not in '。！？!?'
    if grammar_stop:
        from .piece_source import _qualified_self_topic, _literal_self_account
        _require(_qualified_self_topic(literal + '。') is not None
                 and _literal_self_account(literal + '。'), 'piece_refined_replacement_not_self_contained')
    view = PieceSourceSnapshot(owner_id, answer.answer_id, answer.source_version,
                               literal + ('。' if grammar_stop else ''))
    parsed = build_piece_source_meaning(view, expected_owner_id=owner_id,
        expected_saved_input_id=answer.answer_id, expected_source_version=answer.source_version,
        bound_complete_clause=bound_complete_clause)
    _require(bool(frozen.evidence_refs))
    if active_range is not None:
        _require(len(parsed.graph.nodes) == 1 and not parsed.role_bindings
            and not parsed.nominal_references and not parsed.personal_evaluations
            and not parsed.expression_scopes, 'piece_refined_replacement_not_self_contained')
    field = frozen.evidence_refs[0]
    evidence = []
    ids = {}
    for local in parsed.evidence:
        local_end = min(local.scalar_end, len(literal))
        quote = literal[local.scalar_start:local_end]
        values = dict(source_span_id=local.source_span_id, field_path=field.field_path,
            element_index=field.element_index, field_utf8_start=field.field_utf8_start,
            field_utf8_end=field.field_utf8_end, scalar_start=start + local.scalar_start,
            scalar_end=start + local_end,
            utf8_start=field.field_utf8_start + len(raw[:start + local.scalar_start].encode('utf-8')),
            utf8_end=field.field_utf8_start + len(raw[:start + local_end].encode('utf-8')),
            field_sha256=field.field_sha256, literal_sha256=_sha(quote.encode('utf-8')))
        eid = _evidence_id(envelope_id=frozen.envelope.envelope_id, **values)
        ids[local.evidence_id] = eid
        evidence.append(replace(local, evidence_id=eid,
            source_envelope_id=frozen.envelope.envelope_id, **values))
    graph = replace(parsed.graph,
        graph_id='piece-graph:' + _sha(canonical_json_bytes(
            [frozen.envelope.envelope_id, parsed.graph.graph_id] if active_range is None else
            [frozen.envelope.envelope_id, parsed.graph.graph_id, list(active_range)])),
        source_envelope_id=frozen.envelope.envelope_id,
        nodes=tuple(replace(n, value=literal if grammar_stop else n.value,
                            evidence_ids=tuple(ids[e] for e in n.evidence_ids))
                    for n in parsed.graph.nodes),
        edges=tuple(replace(e, evidence_ids=tuple(ids[r] for r in e.evidence_ids))
                    for e in parsed.graph.edges),
        owner_dispositions=tuple(replace(o, evidence_refs=tuple(ids[e] for e in o.evidence_refs))
                                 for o in parsed.graph.owner_dispositions))
    values = {f.name: getattr(parsed, f.name) for f in fields(PieceSourceMeaning)}
    values.update(envelope=frozen.envelope, graph=graph, evidence=tuple(evidence),
        sentences=tuple(replace(s, evidence_id=ids[s.evidence_id],
            source_start=start + s.source_start, source_end=start + min(s.source_end, len(literal)))
            for s in parsed.sentences))
    return PieceSupplementalMeaning(**values, frozen_answer=frozen, grammar_owner_id=owner_id,
                                    active_range=active_range, feeling_question_id=feeling_question_id)


def validate_supplemental_meaning(meaning):
    _require(type(meaning) is PieceSupplementalMeaning
             and type(meaning.frozen_answer) is FrozenSupplementalAnswer)
    # Re-derive parser/evidence only, never the author. Saved re-read below
    # does not enter this function; this is generation-time source validation.
    _require(type(meaning.grammar_owner_id) is str and bool(meaning.grammar_owner_id.strip()))
    expected = _supplemental_meaning(meaning.frozen_answer.source, meaning.grammar_owner_id, meaning.active_range,
                                     feeling_question_id=meaning.feeling_question_id,
                                     bound_complete_clause=meaning.bound_complete_clause)
    # The grammar's local owner is not part of its graph/source identity.
    _require(meaning == expected, 'piece_refined_answer_evidence_binding')



def _active_original_meaning(source, ranges, *, effective_round_sources=False):
    """Keep complete surviving nodes at their original field/envelope offsets.

    Saved-source admission supplies the shared Emlis update proof. This view
    does not infer a target, splice an envelope or connect across a removal.
    """
    from .piece_source import (piece_text_nodes, _qualified_self_topic,
                               _selected_feeling_bindings)
    full = build_piece_source_meaning(source, expected_owner_id=source.owner_id,
        expected_saved_input_id=source.saved_input_id, expected_source_version=source.source_version)
    _require(type(ranges) is tuple and bool(ranges), 'piece_refined_active_range_binding')
    by_range = {(ref.field_path, ref.scalar_start, ref.scalar_end): ref for ref in full.evidence}
    _require(all(type(item) is tuple and len(item) == 3
        and type(item[0]) is str and type(item[1]) is int and type(item[2]) is int
        and item in by_range for item in ranges)
        and len(set(ranges)) == len(ranges), 'piece_refined_active_range_binding')
    chosen = {by_range[item].source_span_id for item in ranges}
    nodes = tuple(node for node in piece_text_nodes(full) if node.node_id in chosen)
    evidence = tuple(ref for ref in full.evidence if ref.source_span_id in chosen)
    _require(tuple((ref.field_path, ref.scalar_start, ref.scalar_end) for ref in evidence) == ranges,
             'piece_refined_active_range_binding')
    removed = tuple(node for node in piece_text_nodes(full) if node.node_id not in chosen)
    _require((effective_round_sources or len(removed) == 1)
        and all(_qualified_self_topic(node.value) is not None for node in removed),
             'piece_refined_update_not_supported')
    # An antecedent or its dependent may not be silently reattached after
    # removal. Within-node conditions/evaluations survive only in full.
    _require(not full.role_bindings
        and not any(row.node_id in {node.node_id for node in removed}
                    for row in (*full.expression_scopes, *full.personal_evaluations))
        and not any(node.node_id in (ref.antecedent_node_id, ref.reference_node_id)
                    for node in removed for ref in full.nominal_references),
        'piece_refined_update_dependency_not_supported')
    sentences = tuple(row for row in full.sentences if row.node_id in chosen)
    edges = tuple(row for row in full.graph.edges
                  if row.source_node_id in chosen and row.target_node_id in chosen)
    owners = tuple(node.owner_id for node in nodes)
    graph = replace(full.graph,
        graph_id='piece-graph:' + _sha(canonical_json_bytes([full.graph.graph_id, [list(row) for row in ranges]])),
        nodes=nodes, edges=edges,
        owner_dispositions=tuple(row for row in full.graph.owner_dispositions
                                 if row.meaning_owner_id in owners),
        required_owner_refs=owners,
        owner_universe_digest=_sha(json.dumps(owners).encode()))
    selected, selection_evidence, selection_contexts = _selected_feeling_bindings(source, nodes, evidence)
    values = {field.name: getattr(full, field.name) for field in fields(PieceSourceMeaning)}
    values.update(graph=graph, evidence=evidence, sentences=sentences,
        nominal_references=tuple(row for row in full.nominal_references
            if row.antecedent_node_id in chosen and row.reference_node_id in chosen),
        personal_evaluations=tuple(row for row in full.personal_evaluations if row.node_id in chosen),
        expression_scopes=tuple(row for row in full.expression_scopes if row.node_id in chosen),
        selected_feelings=selected, selection_evidence=selection_evidence,
        selection_contexts=selection_contexts)
    return PieceActiveOriginalMeaning(**values, active_ranges=ranges,
                                      effective_round_sources=effective_round_sources)


def validate_active_original_meaning(meaning):
    _require(type(meaning) is PieceActiveOriginalMeaning
             and meaning == _active_original_meaning(meaning.saved_snapshot, meaning.active_ranges,
                 effective_round_sources=meaning.effective_round_sources),
             'piece_refined_active_range_binding')


def supplemental_statement_view(meaning, node):
    """A grammar-only terminator for one already qualified replacement."""
    if (type(meaning) in (PieceSupplementalMeaning, PieceCorrectionMeaning) and meaning.active_range is not None
            and node in meaning.graph.nodes and not node.value.endswith(tuple('。！？!?'))):
        return node.value + '。'
    return node.value


def supplemental_complete_self_account(meaning):
    from .piece_source import _qualified_self_topic, _literal_self_account
    return (type(meaning) in (PieceSupplementalMeaning, PieceCorrectionMeaning) and meaning.active_range is not None
        and len(meaning.graph.nodes) == 1 and all(
            _qualified_self_topic(supplemental_statement_view(meaning, node)) is not None
            and ((type(meaning) is PieceCorrectionMeaning and meaning.bound_complete_clause)
                or _literal_self_account(supplemental_statement_view(meaning, node)))
            for node in meaning.graph.nodes))


def refined_meaning_parts(meaning, plan):
    _require((meaning.original is None) == (plan.original_plan is None), 'piece_refined_plan_binding')
    parts = () if meaning.original is None else ((meaning.original, plan.original_plan),)
    _require(len(meaning.prior_revisions) == len(plan.prior_revision_plans),
             'piece_refined_plan_binding')
    parts += tuple(zip(meaning.prior_revisions, plan.prior_revision_plans, strict=True))
    if meaning.supplemental is not None:
        _require(plan.supplemental_plan is not None, 'piece_refined_plan_binding')
        parts += ((meaning.supplemental, plan.supplemental_plan),)
    else:
        operation = (meaning.source.correction_update_operation if type(meaning.source) is PieceCorrectedSourceSnapshot
                     else meaning.source.supplemental_update_operation)
        _require(plan.supplemental_plan is None and operation == 'WITHDRAW',
                 'piece_refined_plan_binding')
    return parts


def _supplemental_feeling_prefix_end(text, *, bound_answer=False):
    """Read a complete SELF feeling without changing its written time.

    The answer owner's NOW/THEN grammar supplies only a parse boundary. The
    original relative-time words remain in the proposition and its evidence;
    neither the original's recorded date nor its selected feeling fills them.
    """
    from piece_v2_expression import _SELF_TOPIC
    from .emlis_answer_update import _FEELING, _NOW, _THEN
    from .piece_source import _written_feeling_expression
    if type(text) is not str or not text.endswith('。'):
        return None
    prefix = _NOW.match(text) or _THEN.match(text)
    end = prefix.end() if prefix is not None else 0
    body = text[end:]
    if bound_answer and _THEN.match(text) and _FEELING.fullmatch(body[:-1]):
        return end
    topic = _SELF_TOPIC.fullmatch(body)
    if topic is None or not (
            _FEELING.fullmatch('私は' + topic['body'])
            or _written_feeling_expression(body, current_affirmative_only=False) is not None):
        return None
    return end


def supplemental_feeling_time_span(meaning, node):
    """Locate only a fully read answer feeling's written THEN prefix.

    This is a local temporal-token exemption, not a nominal-reference
    resolver. Other source types and references elsewhere remain unchanged.
    """
    from .emlis_answer_update import _THEN
    if type(meaning) is not PieceSupplementalMeaning or node not in meaning.graph.nodes:
        return None
    prefix = _THEN.match(node.value)
    end = _supplemental_feeling_prefix_end(node.value, bound_answer=meaning.feeling_question_id is not None)
    return (0, end) if prefix is not None and end == prefix.end() else None


def supplemental_feeling_account(meaning):
    """Keep a complete explicit SELF feeling from its own answer field.

    The optional source-written NOW/THEN prefix stays in the unchanged KEEP
    proposition. It is never resolved to an absolute date or removed.
    """
    if type(meaning) is not PieceSupplementalMeaning or not meaning.graph.nodes:
        return False
    for node in meaning.graph.nodes:
        if _supplemental_feeling_prefix_end(node.value, bound_answer=meaning.feeling_question_id is not None) is None:
            return False
    return True


def _validate_feeling_circumstance_source(source):
    """Rebind exact authored sides of the authenticated single-answer relation."""
    bound = source.feeling_circumstance
    answer = source.supplemental
    original = json.loads(source.original.saved_original_json)
    memo = original['memo']
    answer_text = answer.answer_text_private
    _require(type(bound) is BoundFeelingCircumstance
        and type(memo) is str and not (original['memo_action'] or '').strip()
        and bound.question_id == answer.question_id and bound.answer_id == answer.answer_id
        and answer.round_index == 1 and source.supplemental_update_operation == 'ADD'
        and not source.effective_round_sources and source.feeling_question_id is None,
        'piece_feeling_circumstance_source_binding')
    for literal, span in ((memo, bound.feeling_range), (answer_text, bound.circumstance_range)):
        start, end = span
        _require(0 <= start < end <= len(literal) and not literal[:start].strip()
            and literal[end:].strip() in ('', '。', '！', '!')
            and not re.search(r'[\r\n?？「」『』]', literal), 'piece_feeling_circumstance_source_binding')


def feeling_circumstance_blocks(meaning):
    """Exact source clauses, plus the connective licensed by their saved Q&A."""
    if (type(meaning) is not PieceRefinedMeaning
            or type(meaning.source) is not PieceRefinedSourceSnapshot
            or meaning.source.feeling_circumstance is None):
        return None
    _validate_feeling_circumstance_source(meaning.source)
    parts = (meaning.original, meaning.supplemental)
    _require(all(part is not None and part.bound_complete_clause and not part.role_bindings
        and not part.nominal_references and not part.expression_scopes and len(part.graph.nodes) == 1
        for part in parts), 'piece_feeling_circumstance_source_binding')
    originals = tuple(part.graph.nodes[0].value for part in parts)
    complete = tuple(raw if raw.endswith(('。', '！', '!')) else raw + '。' for raw in originals)
    return originals, (complete[0], 'というのも、' + complete[1])


def validate_feeling_circumstance_body(meaning, blocks):
    """The only permitted new connector is the proved answer relationship."""
    admitted = feeling_circumstance_blocks(meaning)
    if admitted is None:
        return False
    originals, connected = admitted
    _require(len(blocks) == 2 and all(
        text in (raw, linked) or not raw.endswith(('。', '！', '!')) and text == raw + '。'
        for text, raw, linked in zip(blocks, originals, connected, strict=True)),
        'piece_feeling_circumstance_meaning_not_preserved')
    return True


def relative_feeling_anchor_blocks(meaning, plan):
    """Resolve one optional, source-bound clarification of the answer's time."""
    if (type(meaning) is not PieceRefinedMeaning
            or type(meaning.source) is not PieceRefinedSourceSnapshot):
        return None
    source = meaning.source
    anchor = source.relative_feeling_anchor
    if (type(anchor) is not PieceRelativeFeelingAnchor
            or source.opted_in is not True or source.supplemental_update_operation != 'ADD'
            or source.effective_round_sources or source.feeling_circumstance is not None
            or source.supplemental.round_index != 1
            or anchor.question_id != source.feeling_question_id
            or anchor.question_id != source.supplemental.question_id
            or anchor.answer_id != source.supplemental.answer_id
            or meaning.original is None or type(meaning.supplemental) is not PieceSupplementalMeaning
            or len(meaning.supplemental.graph.nodes) != 1
            or len(plan.original_plan.block_node_ids) != 2
            or len(plan.supplemental_plan.block_node_ids) != 1
            or meaning.original.role_bindings or meaning.supplemental.role_bindings):
        return None
    record = json.loads(source.original.saved_original_json)
    memo, action = record['memo'], record['memo_action']
    answer = source.supplemental.answer_text_private
    start, end = anchor.event_range
    if (not memo or not action or not answer.startswith('その時は')
            or meaning.supplemental.graph.nodes[0].value != answer
            or not 0 <= start < end <= len(memo)):
        return None
    event = memo[start:end]
    if (memo.find(event) != start or memo.find(event, start + 1) != -1 or event in action
            or re.search(r'[\r\n。！？!?「」『』]', event)):
        return None
    return answer, event + answer[len('その'):]


def build_refined_meaning(request):
    from piece_v2_generation import PieceSourceSnapshot
    source = request.source
    if type(source) is PieceCorrectedSourceSnapshot:
        _validate_corrected_source(source)
        original = source.original
        _require(original.owner_id == request.expected_owner_id
            and original.saved_input_id == request.expected_saved_input_id
            and original.source_version == request.expected_source_version, 'piece_correction_source_binding')
        active = (_active_original_meaning(original, source.original_active_ranges,
            effective_round_sources=bool(source.prior_corrections or source.answer_sources))
            if source.original_active_ranges else None)
        prior = []
        for answer,operation,active_range,_,view in corrected_answer_ranges(source):
            if operation != 'WITHDRAW' and (operation == 'REVISE' or answer.answer_id == source.selected_answer_id):
                bound = view.feeling_circumstance_ranges is not None
                prior.append(_supplemental_meaning(answer, original.owner_id, active_range,
                    feeling_question_id=answer.question_id if bound else None, bound_complete_clause=bound))
        for i, previous in enumerate(source.prior_corrections):
            prefix = source.prior_corrections[:i]
            op, ranges, active_range, commitment = corrected_active_ranges(
                original, previous, as_of=source.as_of, prior_corrections=prefix, answer_sources=source.answer_sources,
                circumstance_control=source.circumstance_control)
            if op == 'REVISE':
                child = replace(source, correction=previous, prior_corrections=prefix,
                    original_active_ranges=ranges, correction_update_operation=op,
                    correction_active_range=active_range, correction_commitment=commitment)
                prior.append(_correction_meaning(child))
        correction = (_correction_meaning(source) if source.correction_update_operation == 'REVISE' else None)
        return PieceRefinedMeaning(source, refined_source_ref(source), active, correction, tuple(prior))
    _require(type(source) is PieceRefinedSourceSnapshot)
    original, answer = source.original, source.supplemental
    _require(type(original) is PieceSourceSnapshot and type(answer) is SupplementalAnswerSource)
    _require(source.opted_in is True, 'piece_refined_opt_in_required')
    _require(source.supplemental_update_operation in {'ADD', 'REVISE', 'WITHDRAW'}, 'piece_refined_update_not_supported')
    _require(source.supplemental_owner_id == original.owner_id == request.expected_owner_id,
             'piece_refined_owner_mismatch')
    # Event identity and the logical question_id are distinct in saved Q2.
    # Their actual pairing is established by the saved-source adapter; this
    # pure constructor does not authenticate fabricated private snapshots.
    _require(type(source.question_need_decision_identity) is str
        and bool(source.question_need_decision_identity.strip()),
        'piece_refined_question_binding')
    _require(type(source.refined_result_identity) is str and bool(source.refined_result_identity.strip()))
    _require(type(answer.round_index) is int and 1 <= answer.round_index <= 3
             and answer.answer_id != original.saved_input_id,
             'piece_refined_answer_binding')
    _require(type(original.saved_original_json) is bytes,
             'piece_refined_saved_original_required')
    _require(source.original_commitment == 'sha256:' + _sha(original.saved_original_json),
             'piece_refined_original_commitment')
    frozen = freeze_supplemental_answer(answer)
    _require(source.supplemental_commitment == 'sha256:' + frozen.envelope.raw_sha256
        and source.original_commitment != source.supplemental_commitment,
        'piece_refined_answer_commitment')
    _require(type(source.effective_round_sources) is bool
        and type(source.prior_revisions) is tuple, 'piece_refined_active_range_binding')
    circumstance = source.feeling_circumstance
    if circumstance is not None:
        _validate_feeling_circumstance_source(source)
    if source.effective_round_sources:
        _require(bool(source.original_active_ranges)
            and len(source.prior_revisions) < answer.round_index,
            'piece_refined_active_range_binding')
        original_meaning = _active_original_meaning(original, source.original_active_ranges,
                                                   effective_round_sources=True)
        prior = []
        rounds, ids = [], []
        for previous, active_range in source.prior_revisions:
            _require(type(previous) is SupplementalAnswerSource
                and previous.thread_id == answer.thread_id
                and previous.original_source_ref == answer.original_source_ref
                and 0 < previous.round_index < answer.round_index
                and previous.answer_id not in {original.saved_input_id, answer.answer_id},
                'piece_refined_answer_binding')
            rounds.append(previous.round_index); ids.append(previous.answer_id)
            prior.append(_supplemental_meaning(previous, original.owner_id, active_range))
        _require(rounds == sorted(set(rounds)) and len(ids) == len(set(ids)),
                 'piece_refined_answer_binding')
        prior_revisions = tuple(prior)
        if source.supplemental_update_operation == 'WITHDRAW':
            _require(source.supplemental_active_range is None, 'piece_refined_active_range_binding')
            supplemental = None
        else:
            _require((source.supplemental_update_operation == 'REVISE')
                     == (source.supplemental_active_range is not None),
                     'piece_refined_active_range_binding')
            supplemental = _supplemental_meaning(answer, original.owner_id,
                                                  source.supplemental_active_range)
    elif source.supplemental_update_operation == 'ADD':
        _require(not source.prior_revisions, 'piece_refined_active_range_binding')
        _require(not source.original_active_ranges and source.supplemental_active_range is None,
                 'piece_refined_active_range_binding')
        _require(not re.search(r'訂正|撤回|ではなく|じゃなく|違います|違った', answer.answer_text_private),
                 'piece_refined_update_not_supported')
        original_meaning = build_piece_source_meaning(original,
            expected_owner_id=request.expected_owner_id,
            expected_saved_input_id=request.expected_saved_input_id,
            expected_source_version=request.expected_source_version,
            bound_complete_clause=circumstance is not None)
        supplemental = _supplemental_meaning(answer, original.owner_id,
            feeling_question_id=source.feeling_question_id, bound_complete_clause=circumstance is not None)
    else:
        original_meaning = _active_original_meaning(original, source.original_active_ranges)
        if source.supplemental_update_operation == 'REVISE':
            _require(type(source.supplemental_active_range) is tuple
                     and len(source.supplemental_active_range) == 2,
                     'piece_refined_active_range_binding')
            supplemental = _supplemental_meaning(answer, original.owner_id, source.supplemental_active_range)
        else:
            _require(source.supplemental_active_range is None, 'piece_refined_active_range_binding')
            supplemental = None
    if supplemental is not None and circumstance is None:
        _require(all(re.match(r'^(?:(?:以前|当時|今|現在|これから)[はも][、，,]\s*)?'
                             r'(?:私|わたし|僕|ぼく|俺|おれ)(?:は|が|にとって)', n.value)
                     or supplemental_feeling_time_span(supplemental, n) is not None
                     for n in supplemental.graph.nodes), 'piece_refined_answer_not_self_contained')
    return PieceRefinedMeaning(source, refined_source_ref(source), original_meaning, supplemental,
                              prior_revisions if source.effective_round_sources else ())


def refined_source_roles(source):
    if type(source) is PieceCorrectedSourceSnapshot:
        return (('ORIGINAL_USER_INPUT','SUPPLEMENTAL_ANSWER','USER_INTERPRETATION_CORRECTION')
            if source.answer_sources else ('ORIGINAL_USER_INPUT','USER_INTERPRETATION_CORRECTION'))
    return ('ORIGINAL_USER_INPUT','SUPPLEMENTAL_ANSWER')


def _plans(meaning):
    from .piece_v1c import compile_piece_artifact_plan
    return PieceRefinedPlan(meaning.source_ref,
        compile_piece_artifact_plan(meaning.original) if meaning.original is not None else None,
        compile_piece_artifact_plan(meaning.supplemental) if meaning.supplemental is not None else None,
        source_roles=refined_source_roles(meaning.source),
        prior_revision_plans=tuple(compile_piece_artifact_plan(part) for part in meaning.prior_revisions))


def validate_refined_preservation(meaning, plan, artifact):
    from .piece_v1c import PieceArtifact, PieceGenerationRequest
    _require(type(meaning) is PieceRefinedMeaning and type(plan) is PieceRefinedPlan
        and type(artifact) is PieceArtifact and plan.source_ref == meaning.source_ref
        and meaning.source_ref == refined_source_ref(meaning.source)
        and plan.source_roles == refined_source_roles(meaning.source)
        and plan.eligible_formats == ('short_essay',), 'piece_refined_artifact_binding')
    source = meaning.source.original
    expected = build_refined_meaning(PieceGenerationRequest(
        'piece-refined-review', meaning.source, source.owner_id,
        source.saved_input_id, source.source_version))
    _require(meaning == expected, 'piece_refined_artifact_source_binding')
    validate_candidate_text(artifact.content_payload())
    _require(artifact.format_type == 'short_essay' and artifact.eligible_formats == ('short_essay',)
        and artifact.piece_text == '\n\n'.join(artifact.body_blocks)
        and artifact.piece_text_hash == _sha(artifact.piece_text.encode()),
        'piece_refined_artifact_binding')
    if validate_feeling_circumstance_body(meaning, artifact.body_blocks):
        check_existing_detectors(artifact.piece_text)
        return
    parts = refined_meaning_parts(meaning, plan)
    _require(len(artifact.body_blocks) == sum(len(child.block_node_ids) for _, child in parts),
        'piece_refined_artifact_binding')
    offset = 0
    for part, child_plan in parts:
        blocks = artifact.body_blocks[offset:offset + len(child_plan.block_node_ids)]
        offset += len(blocks)
        text = '\n\n'.join(blocks)
        child = PieceArtifact(blocks, text, _sha(text.encode()), 'short_essay', ('short_essay',))
        validate_source_meaning_preservation(part, child_plan, child)
    check_existing_detectors(artifact.piece_text)


def realize_refined_piece_artifact(meaning, plan, *, tier, requested_format):
    """Use the sole Piece author for each qualified partition, in order."""
    from .piece_v1c import PieceArtifact, realize_piece_artifact
    _require(plan == _plans(meaning), 'piece_refined_plan_binding')
    choose_format(tier=tier, requested=requested_format,
                  eligible=('short_essay',), recommended='short_essay')
    circumstance = feeling_circumstance_blocks(meaning)
    if circumstance is not None:
        blocks = circumstance[1]
    else:
        parts = tuple(realize_piece_artifact(part, child, tier='free', requested_format=None)
            for part, child in refined_meaning_parts(meaning, plan))
        blocks = tuple(b for p in parts for b in p.body_blocks)
    text = '\n\n'.join(blocks)
    artifact = PieceArtifact(blocks, text, _sha(text.encode()), 'short_essay', ('short_essay',))
    validate_refined_preservation(meaning, plan, artifact)
    return artifact


def generate_refined_piece(request):
    from .piece_v1c import PieceEngineOutcome
    from piece_v2_contract import PieceContractError
    meaning = plan = None
    try:
        meaning = build_refined_meaning(request)
        plan = _plans(meaning)
        # Both partitions use the unchanged sole author. There is no author
        # for inferred bridges, no raw-text append and no generated Emlis text.
        artifact = realize_refined_piece_artifact(meaning, plan, tier=request.tier,
                                                  requested_format=request.requested_format)
        return PieceEngineOutcome(EngineStatus.GENERATED, ('piece_refined_source_plan_generated',),
                                   meaning, plan, artifact)
    except PieceContractError as exc:
        return PieceEngineOutcome(EngineStatus.UNAVAILABLE, (exc.detail or 'piece_refined_unavailable',),
                                   meaning, plan)
    except Exception:
        return PieceEngineOutcome(EngineStatus.UNAVAILABLE, ('piece_refined_internal_failure',))


def serialize_refined_piece(outcome):
    _require(outcome.status == EngineStatus.GENERATED and outcome.artifact is not None)
    validate_refined_preservation(outcome.source_meaning, outcome.artifact_plan, outcome.artifact)
    state = dict(schema_version='piece.refined_private_saved.v1',
        source_ref=outcome.source_meaning.source_ref,
        sources=_source_payload(outcome.source_meaning.source),
        plan=asdict(outcome.artifact_plan), artifact=asdict(outcome.artifact))
    if ((type(outcome.source_meaning.source) is PieceCorrectedSourceSnapshot
            and not outcome.source_meaning.source.prior_corrections
            and not outcome.source_meaning.source.answer_sources)
            or (type(outcome.source_meaning.source) is PieceRefinedSourceSnapshot
                and not outcome.source_meaning.source.effective_round_sources)):
        del state['plan']['prior_revision_plans']
    # Private dataclass tuples become JSON arrays; the existing canonical
    # contract deliberately rejects Python tuples as public request values.
    return canonical_json_bytes(json.loads(json.dumps(state, ensure_ascii=False, allow_nan=False)))


def read_saved_refined_artifact(raw, *, expected_state_sha256):
    """Read exact saved bytes; expected digest belongs to the trusted store.

    This is private file persistence, not Piece SQL/preview authority. No
    parser, source reader, compiler, author, Engine or model runs on re-read.
    """
    from .piece_v1c import PieceArtifact
    _require(type(raw) is bytes and _sha(raw) == expected_state_sha256,
             'piece_refined_saved_integrity')
    try:
        row = json.loads(raw)
        _require(row['schema_version'] == 'piece.refined_private_saved.v1')
        a = row['artifact']
        artifact = PieceArtifact(tuple(a['body_blocks']), a['piece_text'], a['piece_text_hash'],
                                 a['format_type'], tuple(a['eligible_formats']))
        validate_candidate_text(artifact.content_payload())
        _require(artifact.piece_text == '\n\n'.join(artifact.body_blocks)
            and artifact.piece_text_hash == _sha(artifact.piece_text.encode()))
        return artifact
    except (ValueError, KeyError, TypeError):
        raise unavailable('piece_refined_saved_integrity') from None
