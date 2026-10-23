"""Mash-approved P5: private, finite Analysis meaning and caller-managed replay.

This is an explicit offline profile for three reviewed original constructions.
It does not call a provider, author text, alter legacy Analysis, or issue a
public/Safety acceptance. Source ownership is not an authentication service.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import hashlib
import json

from .source_adapter import (AnalysisObservedMapRequest, AnalysisSourceError, freeze_analysis_sources,
                             source_field_text, commitment, canonical_bytes)
from ...preparation import (PreparedRequest, CandidateReceipt, prepare_analysis,
                            receive_candidate, _candidate, _unique_object)

PROFILE = 'analysis_candidate_snapshot.v1'
SCHEMA = 'cocolon.cmee.analysis_semantic_snapshot.v1'
STATE_SCHEMA = 'cocolon.cmee.analysis_semantic_state.v1'


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()


class AnalysisSemanticError(ValueError):
    pass


class AnalysisSemanticUnsupported(AnalysisSemanticError):
    pass


def require(condition, code='analysis_semantic_binding_invalid'):
    if not condition:
        raise AnalysisSemanticError(code)


def _load(raw):
    require(type(raw) is str, 'analysis_semantic_json_type')
    def bad_constant(_):
        raise AnalysisSemanticError('analysis_semantic_non_finite')
    try:
        obj = json.loads(raw, object_pairs_hook=_unique_object, parse_constant=bad_constant)
        canonical(obj).encode('utf-8')
        return obj
    except (ValueError, TypeError, UnicodeError, RecursionError, OverflowError):
        raise AnalysisSemanticError('analysis_semantic_json_invalid') from None


@dataclass(frozen=True, slots=True, repr=False)
class AnalysisSemanticInputV1:
    prepared: PreparedRequest
    receipt: CandidateReceipt
    tier: str = 'plus'
    semantic_profile: str = PROFILE


@dataclass(frozen=True, slots=True, repr=False)
class AnalysisSemanticUnitBindingV1:
    unit_ref: str
    carrier: str
    node_kind: str | None
    source_binding_ref: str
    source_binding_json: str
    claim_json: str
    group_ref: str

    def payload(self):
        return dict(unit_ref=self.unit_ref, carrier=self.carrier,
                    node_kind=self.node_kind, source_binding_ref=self.source_binding_ref,
                    source_binding_json=_load(self.source_binding_json),
                    claim_json=_load(self.claim_json), group_ref=self.group_ref)


@dataclass(frozen=True, slots=True, repr=False)
class AnalysisSemanticSnapshotV1:
    schema_version: str
    semantic_profile: str
    admission_version: int
    adapter_version: int
    request_binding: str
    source_snapshot: str
    source_commitment: str
    candidate_packet: str
    unit_bindings: tuple[AnalysisSemanticUnitBindingV1, ...]
    source_set_ref: str
    period: tuple[str, str]
    snapshot_ref: str

    def payload(self):
        return dict(schema_version=self.schema_version,
                    semantic_profile=self.semantic_profile,
                    admission_version=self.admission_version,
                    adapter_version=self.adapter_version,
                    request_binding=_load(self.request_binding),
                    source_snapshot=_load(self.source_snapshot),
                    source_commitment=self.source_commitment,
                    candidate_packet=_load(self.candidate_packet),
                    unit_bindings=[b.payload() for b in self.unit_bindings],
                    source_set_ref=self.source_set_ref, period=list(self.period),
                    snapshot_ref=self.snapshot_ref)


@dataclass(frozen=True, slots=True, repr=False)
class AnalysisSemanticResultV1:
    decision: str
    reason_codes: tuple[str, ...]
    request_ref: str
    status: str = 'UNAVAILABLE'
    snapshot: AnalysisSemanticSnapshotV1 | None = None
    graph: object | None = None
    artifact: object | None = None

    def payload(self):
        return dict(decision=self.decision, reason_codes=list(self.reason_codes),
                    request_ref=self.request_ref, status=self.status,
                    snapshot=self.snapshot.payload() if self.snapshot else None,
                    graph=self.graph.payload() if self.graph else None,
                    artifact=self.artifact.payload() if self.artifact else None)


# Reviewed written constructions, not record IDs, dates, owner or fixture hashes.
# A different wording is unsupported rather than silently reduced or paraphrased.
_FAMILIES = (('今日も連絡係だった。まだ返事のない人がいることも残したかった。前より待つ時間は短かった。', '回答済みと未回答を分けて途中の案内を送り、最終の返事を待った。'), ('今日は道具係だった。数を照らし合わせられてほっとした。使いやすかったかは聞いていない。', '道具を貸す時に数を記録し、返ってきた数と照合した。全て戻っていた。'), ('買う物は買えたけど、今日はメモを作るのが少し面倒だった。', '買い物前にメモを作り、メモを見ながら買った。'))


def _source(request, tier):
    require(type(request) is AnalysisObservedMapRequest,
            'analysis_semantic_exact_request_required')
    require(type(request.request_id) is str and bool(request.request_id.strip()),
            'analysis_semantic_request_id')
    try:
        frozen = freeze_analysis_sources(request)
    except AnalysisSourceError as exc:
        raise AnalysisSemanticError(str(exc)) from None
    if (type(tier) is not str or tier != 'plus'
            or request.comparison_previous_request is not None
            or len(frozen.members) != 3 or len(frozen.sources) != 3
            or any(m.inclusion_status != 'INCLUDED' for m in frozen.members)
            or any(m.supplements for m in request.members)):
        raise AnalysisSemanticUnsupported('analysis_semantic_profile_scope')
    originals = {s.record_ref: json.loads(next(m.original_json for m in request.members
                  if m.saved_record_ref == s.record_ref)) for s in frozen.sources}
    ordered = {}
    for memo, action in _FAMILIES:
        matches = [sid for sid, raw in originals.items()
                   if raw['memo'] == memo and raw['memo_action'] == action]
        if len(matches) != 1:
            raise AnalysisSemanticUnsupported('analysis_semantic_family_not_supported')
        sid = matches[0]
        raw = originals[sid]
        require(type(raw['category']) is list and
                all(type(x) is str for x in raw['category']), 'analysis_semantic_category')
        _selection_shape(raw)
        ordered[sid] = raw
    prepared = prepare_analysis(request, tier=tier)
    source = dict(owner_scope=frozen.owner_scope, operation_request_id=request.request_id,
                  tier=tier, period=list(frozen.period), source_set_ref=frozen.source_set_ref,
                  members=[asdict(m) for m in frozen.members], originals=list(ordered.values()),
                  p1_request_ref=prepared.request_id)
    # Canonical JSON deep-freezes all nested original metadata, never normalized dict.
    source = _load(canonical(source))
    binding = {k:source[k] for k in ('owner_scope','operation_request_id','tier','period',
                                    'source_set_ref','members','p1_request_ref')}
    return frozen, prepared, source, binding, ordered


def _selection_shape(raw):
    from ...source_kernel import CANONICAL_EMOTIONS
    tags, details = raw['emotions'], raw['emotion_details']
    require(type(tags) is list and type(details) is list, 'analysis_semantic_selection_shape')
    require(all(type(t) is str and t in CANONICAL_EMOTIONS and t != '自己理解'
                for t in tags) and len(set(tags)) == len(tags), 'analysis_semantic_selection_label')
    require(all(type(d) is dict and set(d) == {'type','strength'} and
                type(d['type']) is str and type(d['strength']) is str and
                d['strength'] in ('weak','medium','strong') for d in details),
            'analysis_semantic_selection_detail')
    require(tags == [d['type'] for d in details], 'analysis_semantic_selection_alias')


def _reviewed_packet(originals, source_set_ref):
    """Source-bound, finite meaning constraints; no old parser or prose generation.

    Full written groups prove dependent context. All semantic rows below are
    inspected independently from a candidate, including polarity/time, unknown
    coverage, and annotation target. Quote hashes alone cannot grant admission.
    """
    ids = list(originals)
    evidence = []
    def ev(sid, field, a, b):
        text = originals[sid][field]
        require(type(a) is int and type(b) is int and 0 <= a < b <= len(text))
        item = dict(source_id=sid, field_path=field, start=a, end=b, quote=text[a:b])
        if item not in evidence:
            evidence.append(item)
        return evidence.index(item)
    groups = []
    for sid, raw in originals.items():
        for field in ('memo', 'memo_action'):
            start = 0
            for part in raw[field].split('。'):
                if not part:
                    continue
                end = start + len(part) + 1
                groups.append(dict(group_ref=f'{sid}.{field}.g{start}', evidence_indexes=[ev(sid, field, start, end)]))
                start = end

    units = []
    def unit(ref, sid, field, a, b, kind, predicate, *, carrier='GRAPH_NODE', node='ACTION_OR_NONACTION', polarity='AFFIRMED', modality='ASSERTED_AS_WRITTEN', time='WRITTEN_PAST_UNRESOLVED_OCCASION', arguments=(), qualifiers=(), parent=None):
        group = next(g['group_ref'] for g in groups if (e := evidence[g['evidence_indexes'][0]])['source_id'] == sid and e['field_path'] == field and e['start'] <= a < b <= e['end'])
        units.append(dict(unit_ref=ref, source_id=sid, field_path=field,
            carrier=carrier, proposed_node_kind=node if carrier == 'GRAPH_NODE' else None,
            kind=kind, group_ref=group, evidence_indexes=[ev(sid, field, a, b)],
            actor_binding='OMITTED_NOT_OWNER_DERIVED', predicate_surface=predicate,
            arguments=list(arguments), polarity=polarity, modality=modality,
            temporal_scope=time, qualifiers=list(qualifiers), parent_unit_ref=parent))
    def arg(role, sid, field, a, b):
        return dict(role=role, text=originals[sid][field][a:b], evidence_indexes=[ev(sid, field, a, b)])
    def qual(kind, sid, field, a, b, **extra):
        return dict(kind=kind, evidence_indexes=[ev(sid, field, a, b)], **extra)

    s=ids[0]; f='memo'
    unit('a.role',s,f,0,10,'ROLE','連絡係だった',node='ROLE',time='WRITTEN_TODAY_RELATIVE',qualifiers=[qual('RELATIVE_DAY',s,f,0,2),qual('ADDITIVE_NO_REPEAT_COUNT',s,f,2,3)])
    unit('a.intention',s,f,10,31,'RECORDED_INTENTION','残したかった',node='ATTENTION_OR_THOUGHT',modality='WISH_REALIZATION_NOT_ASSERTED',arguments=[arg('WISH_CONTENT_NOT_INDEPENDENT_FACT',s,f,10,23)],qualifiers=[qual('ADDITIVE_WISH_CONTENT',s,f,23,24)])
    unit('a.relative_wait',s,f,31,44,'PERSON_STATED_RELATIVE_COMPARISON','短かった',node='IMMEDIATE_RESULT_OR_AFTERMATH',time='COMPARISON_BASELINE_UNRESOLVED',arguments=[arg('WRITTEN_は',s,f,34,39)],qualifiers=[qual('UNRESOLVED_COMPARISON_BASELINE',s,f,31,34)])
    f='memo_action'
    unit('a.classify',s,f,0,12,'ACTION','分けて',arguments=[arg('WRITTEN_を',s,f,0,9)])
    unit('a.send',s,f,12,20,'ACTION','送り',arguments=[arg('WRITTEN_を',s,f,12,18)])
    unit('a.wait',s,f,21,31,'ACTION','待った',arguments=[arg('WRITTEN_を',s,f,21,27)])
    s=ids[1]; f='memo'
    unit('a.tools_role',s,f,0,10,'ROLE','道具係だった',node='ROLE',time='WRITTEN_TODAY_RELATIVE',qualifiers=[qual('RELATIVE_DAY',s,f,0,2)])
    unit('a.match_scope',s,f,10,21,'WRITTEN_DEPENDENT_MATCH_SCOPE','照らし合わせられて',carrier='DEPENDENT_SCOPE',modality='WRITTEN_RARERU_NOT_INDEPENDENTLY_DISAMBIGUATED',arguments=[arg('WRITTEN_を',s,f,10,12)],parent='a.relief')
    unit('a.relief',s,f,21,27,'FEELING_WITH_WRITTEN_SCOPE','ほっとした',node='IMMEDIATE_RESULT_OR_AFTERMATH')
    unit('a.non_action',s,f,27,43,'EXPLICIT_NON_ACTION','聞いていない',polarity='NEGATED',time='UP_TO_THIS_SOURCE_WRITING',arguments=[arg('WRITTEN_は_QUESTION_CONTENT',s,f,27,36)])
    f='memo_action'
    unit('a.record_count',s,f,0,12,'ACTION','記録し',arguments=[arg('WRITTEN_を',s,f,7,9)],qualifiers=[qual('WHEN_CONTEXT_NOT_SEPARATE_LOAN_EVENT',s,f,0,7)])
    unit('a.compare_count',s,f,13,25,'ACTION','照合した',arguments=[arg('WRITTEN_と',s,f,13,20)])
    unit('a.tools_result',s,f,25,33,'RESULT_STATE','戻っていた',node='IMMEDIATE_RESULT_OR_AFTERMATH',arguments=[arg('WRITTEN_QUANTIFIED_ENTITY_UNRESOLVED',s,f,25,27)])
    s=ids[2]; f='memo'
    unit('a.bought_result',s,f,0,7,'RESULT_STATE','買えた',node='IMMEDIATE_RESULT_OR_AFTERMATH',arguments=[arg('WRITTEN_は',s,f,0,4)])
    unit('a.burden',s,f,10,28,'WRITTEN_BURDEN','面倒だった',carrier='ANNOTATION',time='WRITTEN_TODAY_RELATIVE',arguments=[arg('WRITTEN_が_ACTION_TARGET',s,f,13,20)],qualifiers=[qual('RELATIVE_DAY',s,f,10,12),qual('DEGREE',s,f,20,22)])
    f='memo_action'
    unit('a.make_memo',s,f,0,10,'ACTION','作り',arguments=[arg('WRITTEN_を',s,f,5,8)],qualifiers=[qual('WRITTEN_BEFORE_SHOPPING_CONTEXT',s,f,0,5)])
    unit('a.read_memo',s,f,11,18,'ACTION','見ながら',arguments=[arg('WRITTEN_を',s,f,11,14)])
    unit('a.buy',s,f,18,22,'ACTION','買った')

    relations=[]
    def rel(ref, kind, a, b, sid, field, start, end, ma, mb):
        relations.append(dict(relation_ref=ref, kind=kind, endpoint_unit_refs=[a,b],
            evidence_indexes=[ev(sid,field,start,end)], marker_evidence_indexes=[ev(sid,field,ma,mb)],
            projection_role='SOURCE_SCOPE_NOT_ROUTE_EDGE'))
    rel('a.classify_send','SOURCE_WRITTEN_TE_LINK','a.classify','a.send',ids[0],'memo_action',0,31,11,12)
    rel('a.send_wait','SOURCE_WRITTEN_COORDINATE_LINK','a.send','a.wait',ids[0],'memo_action',0,31,18,21)
    rel('a.match_relief','SOURCE_WRITTEN_FEELING_SCOPE','a.match_scope','a.relief',ids[1],'memo',10,27,19,21)
    rel('a.record_compare','SOURCE_WRITTEN_COORDINATE_LINK','a.record_count','a.compare_count',ids[1],'memo_action',0,25,10,13)
    rel('a.concession','SOURCE_WRITTEN_CONCESSION','a.bought_result','a.burden',ids[2],'memo',0,28,7,9)
    rel('a.make_read','SOURCE_WRITTEN_COORDINATE_LINK','a.make_memo','a.read_memo',ids[2],'memo_action',0,22,8,11)
    rel('a.before_context','SOURCE_WRITTEN_BEFORE_CONTEXT','a.make_memo','a.buy',ids[2],'memo_action',0,22,0,5)
    rel('a.nagara','SOURCE_WRITTEN_NAGARA_SCOPE','a.read_memo','a.buy',ids[2],'memo_action',11,22,15,18)

    checked_fields=[dict(source_id=sid,field_path=f,field_sha256=hashlib.sha256(raw[f].encode()).hexdigest()) for sid,raw in originals.items() for f in ('memo','memo_action')]
    unknown=dict(unknown_ref='a.usability', target_unit_refs=['a.non_action'],
        target_dimension='USABILITY_QUESTION_CONTENT', origin='NOT_OBSERVED_IN_MATERIAL',
        resolution_state='NO_USABILITY_ANSWER_IN_MATERIAL',
        evidence_indexes=[ev(ids[1],'memo',27,43),ev(ids[1],'memo',27,35)],
        checked_source_set_ref=source_set_ref,checked_text_fields=checked_fields,
        proposed_label='今回の材料には、使いやすさについての回答が記されていない。',
        forbidden_promotions=['PERSON_STATED_UNKNOWN','POOR_USABILITY','AWAITING_REPLY','NEVER_RECEIVED_AN_ANSWER'])
    annotation=dict(annotation_ref='a.burden_annotation', unit_ref='a.burden',
        target_unit_refs=['a.make_memo'],target_nominal_evidence_indexes=[ev(ids[2],'memo',13,20)],
        target_link_policy='SAME_RECORD_EXACT_MEMO_CREATION_ONLY_NOT_GENERAL_COREFERENCE',
        evidence_indexes=[ev(ids[2],'memo',10,28)],degree_evidence_indexes=[ev(ids[2],'memo',20,22)],
        temporal_scope='WRITTEN_TODAY_RELATIVE_PAST',
        forbidden_promotions=['CAUSE','TRAIT','DIAGNOSIS','BUYING_FAILURE','ROUTE_ORDER'])
    selections=[]
    for sid,raw in originals.items():
        for i,d in enumerate(raw['emotion_details']):
            j=raw['emotions'].index(d['type'])
            selections.append(dict(selection_ref=f'{sid}.selection.{i}',source_id=sid,
                label=d['type'],strength=d['strength'],source_commitment=commitment(raw),
                alias_refs=[['emotions',j],['emotion_details',i]],
                coverage_state='SOURCE_SELECTION_RETAINED_NOT_TEXTUALIZED'))
    packet=dict(candidate=dict(schema_version='cocolon.cmee.analysis_semantic_proposal.v1',core='analysis',
        units=units,sentence_groups=groups,scope_relations=relations,unknowns=[unknown],annotations=[annotation],
        source_selections=selections,route_edges=[],conflicts=[],updates=[]),evidence=evidence)
    return packet


def _locator(frozen, source_snapshot, evidence):
    sid, field, start, end = (evidence[k] for k in ('source_id','field_path','start','end'))
    source = next(s for s in frozen.sources if s.record_ref == sid)
    text = source_field_text(source, field)
    require(type(start) is int and type(end) is int and 0 <= start < end <= len(text))
    require(text[start:end] == evidence['quote'], 'analysis_semantic_quote_changed')
    base = next(e for e in source.evidence if e.field_path == field)
    a = base.field_utf8_start + len(text[:start].encode('utf-8'))
    b = base.field_utf8_start + len(text[:end].encode('utf-8'))
    require(source.envelope.raw_utf8[a:b].decode('utf-8') == evidence['quote'])
    return dict(source_id=sid, record_version=source.record_version,
                source_envelope_id=source.envelope.envelope_id, field_path=field,
                scalar_start=start, scalar_end=end, field_utf8_start=base.field_utf8_start,
                field_utf8_end=base.field_utf8_end, utf8_start=a, utf8_end=b,
                field_sha256=base.field_sha256,
                literal_sha256=hashlib.sha256(evidence['quote'].encode('utf-8')).hexdigest(),
                quote=evidence['quote'],
                overlapping_native_evidence_ids=[e.evidence_id for e in source.evidence
                    if e.field_path == field and e.scalar_start < end and start < e.scalar_end],
                locator_status='PROPOSED_RANGE_PROVED_FROM_RAW_FIELD_NOT_NATIVE_SPAN_ID')


def _snapshot_ref(payload):
    return 'analysis-semantic-snapshot:' + digest({k:v for k,v in payload.items()
                                                if k != 'snapshot_ref'})


def _derive_snapshot(request, packet, *, tier='plus'):
    frozen, prepared, source, binding, originals = _source(request, tier)
    expected = _reviewed_packet(originals, frozen.source_set_ref)
    # Canonical comparison rejects bool/int substitution, extra fields, renamed
    # duplicate meaning and rehashed semantic tamper, not merely located quotes.
    require(canonical(packet) == canonical(expected), 'analysis_semantic_meaning_changed')
    bindings = []
    for unit in packet['candidate']['units']:
        e = packet['evidence'][unit['evidence_indexes'][0]]
        loc = _locator(frozen, source, e)
        bindings.append(AnalysisSemanticUnitBindingV1(
            unit['unit_ref'], unit['carrier'], unit['proposed_node_kind'],
            'analysis-source-binding:' + digest(loc), canonical(loc), canonical(unit), unit['group_ref']))
    # Prove every qualifier/marker/whole-group range, not just each main unit.
    for e in packet['evidence']:
        _locator(frozen, source, e)
    snapshot = AnalysisSemanticSnapshotV1(SCHEMA, PROFILE, 1, 1,
        canonical(binding), canonical(source), 'sha256:' + digest(source), canonical(packet),
        tuple(bindings), frozen.source_set_ref, frozen.period, '')
    return replace(snapshot, snapshot_ref=_snapshot_ref(snapshot.payload()))


def validate_analysis_snapshot(request, snapshot, *, tier='plus'):
    require(type(snapshot) is AnalysisSemanticSnapshotV1, 'analysis_semantic_snapshot_type')
    require(type(snapshot.unit_bindings) is tuple and
            all(type(b) is AnalysisSemanticUnitBindingV1 for b in snapshot.unit_bindings)
            and type(snapshot.period) is tuple and
            all(type(p) is str for p in snapshot.period), 'analysis_semantic_immutable_shape')
    expected = _derive_snapshot(request, _load(snapshot.candidate_packet), tier=tier)
    require(canonical(snapshot.payload()) == canonical(expected.payload()),
            'analysis_semantic_snapshot_changed')
    return snapshot


def _snapshot_from_payload(request, payload, *, tier='plus'):
    require(type(payload) is dict and type(payload.get('candidate_packet')) is dict,
            'analysis_semantic_saved_snapshot_shape')
    expected = _derive_snapshot(request, payload['candidate_packet'], tier=tier)
    require(canonical(payload) == canonical(expected.payload()),
            'analysis_semantic_saved_snapshot_changed')
    return expected


def admit_analysis_semantics(request, semantic_input):
    require(type(semantic_input) is AnalysisSemanticInputV1,
            'analysis_semantic_input_type')
    frozen, prepared, source, binding, originals = _source(request, semantic_input.tier)
    require(semantic_input.semantic_profile == PROFILE and
            type(semantic_input.semantic_profile) is str and
            type(semantic_input.prepared) is PreparedRequest and
            canonical(asdict(semantic_input.prepared)) == canonical(asdict(prepared)),
            'analysis_semantic_prepared_binding')
    receipt = semantic_input.receipt
    require(type(receipt) is CandidateReceipt, 'analysis_semantic_receipt_type')
    metadata = _load(receipt.metadata_json)
    require(type(metadata) is dict and set(metadata) == {
        'provider','model','revision','usage','finish_reason','elapsed_seconds','evidence_check'},
        'analysis_semantic_receipt_metadata')
    checked = receive_candidate(prepared, request_id=receipt.request_id, raw_output=receipt.raw_output,
        **{k:v for k,v in metadata.items() if k != 'evidence_check'})
    require(canonical(asdict(receipt)) == canonical(asdict(checked)),
            'analysis_semantic_receipt_forged')
    if receipt.status != 'CANDIDATE_UNREVIEWED':
        decision = 'HOLD' if receipt.status in ('TIMEOUT','TOKEN_LIMIT','EMPTY','PROVIDER_ERROR','UNKNOWN_FINISH') else 'REJECTED'
        return AnalysisSemanticResultV1(decision, ('analysis_receipt_' + receipt.status.lower(),), prepared.request_id)
    snapshot = _derive_snapshot(request, _candidate(receipt.candidate_json), tier=semantic_input.tier)
    return AnalysisSemanticResultV1('ADOPTED_PROVISIONAL', (), prepared.request_id,
                                    'MEANING_READY', snapshot)


def _validate_result(request, result, tier):
    from .intent_compiler import validate_semantic_graph
    from .observed_route_realizer import validate_semantic_artifact
    require(type(result) is AnalysisSemanticResultV1 and result.decision == 'ADOPTED_PROVISIONAL'
            and result.snapshot is not None, 'analysis_semantic_state_not_adopted')
    validate_analysis_snapshot(request, result.snapshot, tier=tier)
    require(result.request_ref == _load(result.snapshot.request_binding)['p1_request_ref'],
            'analysis_semantic_result_request')
    require(result.artifact is None or result.graph is not None,
            'analysis_semantic_artifact_without_graph')
    if result.graph is not None:
        try:
            validate_semantic_graph(result.snapshot, result.graph)
        except AnalysisSourceError:
            raise AnalysisSemanticError('analysis_semantic_graph_changed') from None
    if result.artifact is not None:
        try:
            validate_semantic_artifact(result.snapshot, result.graph, result.artifact)
        except AnalysisSourceError:
            raise AnalysisSemanticError('analysis_semantic_artifact_changed') from None


def serialize_analysis_semantic_state(request, result, *, tier='plus'):
    _validate_result(request, result, tier)
    return canonical(dict(schema_version=STATE_SCHEMA,
        request_binding=_load(result.snapshot.request_binding), snapshot=result.snapshot.payload(),
        graph=result.graph.payload() if result.graph is not None else None,
        artifact=result.artifact.payload() if result.artifact is not None else None))


def reload_analysis_semantic_state(request, raw, *, tier='plus'):
    from .intent_compiler import graph_from_payload
    from .observed_route_realizer import artifact_from_payload
    row = _load(raw)
    require(type(row) is dict and set(row) == {
        'schema_version','request_binding','snapshot','graph','artifact'} and
        row['schema_version'] == STATE_SCHEMA, 'analysis_semantic_saved_schema')
    snapshot = _snapshot_from_payload(request, row['snapshot'], tier=tier)
    require(canonical(row['request_binding']) == canonical(_load(snapshot.request_binding)),
            'analysis_semantic_saved_request_binding')
    require(row['artifact'] is None or row['graph'] is not None,
            'analysis_semantic_artifact_without_graph')
    try:
        graph = graph_from_payload(snapshot, row['graph']) if row['graph'] is not None else None
        artifact = artifact_from_payload(snapshot, graph, row['artifact']) if row['artifact'] is not None else None
    except (ValueError, TypeError, KeyError, AttributeError, IndexError, UnicodeError, RecursionError, OverflowError):
        raise AnalysisSemanticError('analysis_semantic_saved_projection_changed') from None
    status = 'GENERATED' if artifact else 'GRAPH_READY' if graph else 'MEANING_READY'
    result = AnalysisSemanticResultV1('ADOPTED_PROVISIONAL', (),
        _load(snapshot.request_binding)['p1_request_ref'], status, snapshot, graph, artifact)
    require(serialize_analysis_semantic_state(request, result, tier=tier) == canonical(row),
            'analysis_semantic_saved_roundtrip')
    return result


def _complete(request, result, tier):
    from .intent_compiler import compile_semantic_graph, validate_semantic_graph
    from .observed_route_realizer import realize_semantic_graph, validate_semantic_artifact
    _validate_result(request, result, tier)
    try:
        if result.graph is None:
            graph = compile_semantic_graph(result.snapshot)
            validate_semantic_graph(result.snapshot, graph)
            result = replace(result, graph=graph, status='GRAPH_READY')
        if result.artifact is None:
            artifact = realize_semantic_graph(result.snapshot, result.graph)
            validate_semantic_artifact(result.snapshot, result.graph, artifact)
            result = replace(result, artifact=artifact, status='GENERATED')
        return result
    except Exception:
        # Actual author failure preserves adopted meaning and any valid graph.
        # No private exception message or previous artifact becomes new output.
        return replace(result, artifact=None, status='UNAVAILABLE',
                       reason_codes=('analysis_semantic_body_unavailable',))


def generate_analysis_semantic(request, semantic_input):
    request_ref = ''
    try:
        require(type(semantic_input) is AnalysisSemanticInputV1, 'analysis_semantic_input_type')
        require(type(request) is AnalysisObservedMapRequest, 'analysis_semantic_exact_request_required')
        prepared = prepare_analysis(request, tier=semantic_input.tier)
        request_ref = prepared.request_id
        result = admit_analysis_semantics(request, semantic_input)
        if result.snapshot is None:
            return result
        return _complete(request, result, semantic_input.tier)
    except AnalysisSemanticUnsupported:
        return AnalysisSemanticResultV1('UNSUPPORTED', ('analysis_semantic_profile_unsupported',), request_ref)
    except (ValueError, TypeError, KeyError, AttributeError, IndexError, UnicodeError, RecursionError, OverflowError):
        return AnalysisSemanticResultV1('REJECTED', ('analysis_semantic_input_rejected',), request_ref)


def resume_analysis_semantics(request, raw, *, tier='plus'):
    result = reload_analysis_semantic_state(request, raw, tier=tier)
    return _complete(request, result, tier)
