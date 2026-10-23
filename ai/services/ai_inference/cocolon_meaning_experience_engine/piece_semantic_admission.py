"""Mash-approved P4: bounded, private offline Piece semantic snapshots.

Not a provider, public B8 adapter, general Japanese parser or safety issuer.
The initial family keeps six claims in five written sentences. Source/selection
and candidate meaning stay distinct; this module never authors Piece text.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, fields, replace
import hashlib
import json
import re

from .contracts import EngineStatus, ExecutionMode
from .preparation import (PreparedRequest, CandidateReceipt, prepare_piece,
                          receive_candidate, _candidate, _unique_object)

PROFILE = 'piece_candidate_snapshot.v1'
SCHEMA = 'cocolon.cmee.piece_semantic_snapshot.v1'
PLAN_SCHEMA = 'cocolon.cmee.piece_semantic_plan.v1'
ARTIFACT_SCHEMA = 'cocolon.cmee.piece_semantic_artifact.v1'
MEANING_VERSION = 'cocolon.cmee.piece_candidate_meaning.v1'
STATE_SCHEMA = 'cocolon.cmee.piece_semantic_state.v1'


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()


class PieceSemanticError(ValueError):
    pass


class PieceSemanticUnsupported(PieceSemanticError):
    pass


def require(condition, code='piece_semantic_binding_invalid'):
    if not condition:
        raise PieceSemanticError(code)


@dataclass(frozen=True, slots=True, repr=False)
class PieceSemanticInputV1:
    prepared: PreparedRequest
    receipt: CandidateReceipt
    semantic_profile: str = PROFILE


@dataclass(frozen=True, slots=True, repr=False)
class PieceSemanticClaimBindingV1:
    claim_ref: str
    node_ref: str
    source_binding_ref: str
    source_id: str
    field_path: str
    scalar_start: int
    scalar_end: int
    utf8_start: int
    utf8_end: int
    claim_json: str


@dataclass(frozen=True, slots=True, repr=False)
class PieceSemanticRelationBindingV1:
    relation_ref: str
    relation_type: str
    endpoint_claim_refs: tuple[str, str]
    evidence_json: str


@dataclass(frozen=True, slots=True, repr=False)
class PieceSourceSelectionV1:
    selection_field: str
    selection_index: int
    label: str
    strength: str
    source_commitment: str
    alias_refs: tuple[str, ...]
    text_binding_refs: tuple[str, ...] = ()
    coverage_state: str = 'SOURCE_SELECTION_RETAINED_NOT_TEXTUALIZED'


@dataclass(frozen=True, slots=True, repr=False)
class PieceSemanticSnapshotV1:
    request_ref: str
    source_snapshot: object
    source_commitment: str
    candidate_packet: str
    claim_bindings: tuple[PieceSemanticClaimBindingV1, ...]
    relation_bindings: tuple[PieceSemanticRelationBindingV1, ...]
    source_selections: tuple[PieceSourceSelectionV1, ...]
    snapshot_ref: str
    schema_version: str = SCHEMA
    semantic_profile: str = PROFILE
    admission_version: int = 1
    adapter_version: int = 1


@dataclass(frozen=True, slots=True, repr=False)
class PieceSemanticDutyBindingV1:
    duty_ref: str
    claim_refs: tuple[str, ...]
    node_refs: tuple[str, ...]
    source_binding_refs: tuple[str, ...]
    required_scope_refs: tuple[str, ...]
    operation: str = 'KEEP_COMPLETE_SOURCE_CONTEXT'


@dataclass(frozen=True, slots=True, repr=False)
class PieceSemanticPlanV1:
    snapshot_ref: str
    source_commitment: str
    graph_id: str
    duties: tuple[PieceSemanticDutyBindingV1, ...]
    block_node_ids: tuple[tuple[str, ...], ...]
    selection_duties: tuple[str, ...]
    eligible_formats: tuple[str, ...]
    intent: str = 'USER_OWNED_COCOLON_SHAPED'
    schema_version: str = PLAN_SCHEMA
    semantic_profile: str = PROFILE

    @property
    def plan_ref(self):
        return 'piece-plan:' + digest(asdict(self))


@dataclass(frozen=True, slots=True, repr=False)
class PieceSemanticRealizationV1:
    claim_ref: str
    duty_ref: str
    node_refs: tuple[str, ...]
    source_binding_refs: tuple[str, ...]
    block_index: int
    visible_scalar_start: int
    visible_scalar_end: int


@dataclass(frozen=True, slots=True, repr=False)
class PieceSemanticArtifactV1:
    snapshot_ref: str
    plan_ref: str
    source_commitment: str
    body_blocks: tuple[str, ...]
    piece_text: str
    piece_text_hash: str
    format_type: str
    eligible_formats: tuple[str, ...]
    claim_realizations: tuple[PieceSemanticRealizationV1, ...]
    retained_selection_refs: tuple[str, ...]
    schema_version: str = ARTIFACT_SCHEMA
    semantic_profile: str = PROFILE
    meaning_contract_version: str = MEANING_VERSION


@dataclass(frozen=True, slots=True, repr=False)
class PieceSemanticResultV1:
    decision: str
    reason_codes: tuple[str, ...]
    request_ref: str
    snapshot: PieceSemanticSnapshotV1 | None = None
    plan: PieceSemanticPlanV1 | None = None
    artifact: PieceSemanticArtifactV1 | None = None

    @property
    def status(self):
        return (EngineStatus.GENERATED if self.artifact is not None
                else EngineStatus.REJECTED if self.decision == 'REJECTED'
                else EngineStatus.UNAVAILABLE)


def _request(request):
    from .piece_v1c import PieceGenerationRequest
    from piece_v2_generation import PieceSourceSnapshot
    require(type(request) is PieceGenerationRequest
            and request.execution_mode == ExecutionMode.OFFLINE_CANDIDATE.value
            and request.core_id == 'piece' and request.product_job == 'EXPRESS_AND_SHARE'
            and type(request.request_id) is str and bool(request.request_id.strip()),
            'piece_semantic_offline_request_required')
    source = request.source
    require(type(source) is PieceSourceSnapshot
            and source.saved_input_id == request.expected_saved_input_id
            and source.source_version == request.expected_source_version,
            'piece_semantic_source_identity')
    return prepare_piece(source, expected_owner_id=request.expected_owner_id, tier=request.tier)


def _source_payload(source):
    row = asdict(source)
    row['saved_original_json'] = source.saved_original_json.decode('utf-8')
    return row


def _selections(original, commitment):
    from .source_kernel import CANONICAL_EMOTIONS
    tags, details = original['emotions'] or [], original['emotion_details'] or []
    labels = tuple(x for x in CANONICAL_EMOTIONS if x != '自己理解')
    require(all(type(x) is str and x in labels for x in tags), 'piece_selection_invalid')
    require(len(tags) == len(set(tags)), 'piece_selection_duplicate')
    detail_labels = []
    for d in details:
        require(type(d) is dict and set(d) == {'type', 'strength'}
                and type(d['type']) is str and d['type'] in labels
                and type(d['strength']) is str
                and d['strength'] in ('weak', 'medium', 'strong'), 'piece_selection_invalid')
        detail_labels.append(d['type'])
    require(len(detail_labels) == len(set(detail_labels)), 'piece_selection_duplicate')
    require(not tags or not details or tags == detail_labels, 'piece_selection_alias_mismatch')
    result = []
    for i, label in enumerate(tags or detail_labels):
        refs = tuple(([f'emotions:{i}'] if tags else []) +
                     ([f'emotion_details:{i}'] if details else []))
        field = 'emotion_details' if details else 'emotions'
        strength = details[i]['strength'] if details else ''
        result.append(PieceSourceSelectionV1(field, i, label, strength, commitment, refs))
    return tuple(result)


# Closed P01 constructions; these inspect source scopes, never produce prose.
# IDs, dates, categories, source role/stage and selected feelings are not lexemes.
_MEMO = re.compile(
    r'(?P<joy>(?P<report>助かったと言ってもらえて)(?:うれしかった|嬉しかった)。)'
    r'(?P<second>でも(?P<work>自分の仕事が残って)、(?P<late>帰るのが遅くなった。))'
    r'(?P<negative>手伝ったことを後悔している(?P<negation>わけではない)。)'
    r'(?P<next>次も引き受けるかは、(?P<margin>そのときの余裕)で決めたい。)')
_ACTION = re.compile(r'頼まれて(?:同僚|先輩|後輩)の発表資料を一緒に直した。')


def _family(original):
    memo, action = original['memo'], original['memo_action']
    m = _MEMO.fullmatch(memo or '')
    if m is None or _ACTION.fullmatch(action or '') is None:
        raise PieceSemanticUnsupported('piece_semantic_family_not_supported')
    # field, scalar span, semantic role; two claims share the second sentence.
    rows = [('memo', m.span('joy'), 'joy'), ('memo', m.span('work'), 'work'),
            ('memo', m.span('late'), 'late'), ('memo', m.span('negative'), 'negative'),
            ('memo', m.span('next'), 'next'), ('memo_action', (0, len(action)), 'help')]
    return m, rows


def _packet_bindings(original, packet, source_id, commitment):
    m, roles = _family(original)
    c = packet['candidate']; evidence = packet['evidence']
    require(type(c) is dict and set(c) == {'schema_version', 'core', 'claims',
        'relations', 'unknowns', 'conflicts', 'updates'}, 'piece_candidate_closed_shape')
    require(c['schema_version'] == 'cocolon.cmee.semantic_mapping_proposal.v1'
            and c['core'] == 'piece', 'piece_candidate_profile')
    if c['unknowns'] != [] or c['conflicts'] != [] or c['updates'] != []:
        raise PieceSemanticUnsupported('piece_semantic_extra_responsibilities')
    require(type(c['claims']) is list and len(c['claims']) == 6
            and type(c['relations']) is list and len(c['relations']) == 2,
            'piece_candidate_complete_coverage')
    require(all(type(x) is dict and type(x.get('claim_id')) is str
                and bool(x['claim_id'].strip()) for x in c['claims']), 'piece_claim_id')
    ids = [x['claim_id'] for x in c['claims']]
    require(len(set(ids)) == 6, 'piece_claim_duplicate')
    used = set()

    def ev(indexes, field, span):
        require(type(indexes) is list and len(indexes) == 1
                and type(indexes[0]) is int and 0 <= indexes[0] < len(evidence),
                'piece_evidence_reference')
        idx = indexes[0]; row = evidence[idx]; text = original[field]
        a, b = span
        require(type(row) is dict and set(row) == {'source_id','field_path','start','end','quote'}
                and type(row['start']) is int and type(row['end']) is int
                and row == dict(source_id=source_id,field_path=field,start=a,end=b,quote=text[a:b]),
                'piece_evidence_scope')
        used.add(idx)
        return indexes

    kinds = ('STATE','RESULT_STATE','RESULT_STATE','SCOPED_EVALUATION','CONDITIONAL_INTENTION','ACTION')
    predicates = (original['memo'][len(m['report']):m.end('joy')-1], '残って',
                  '遅くなった','後悔しているわけではない','決めたい','直した')
    times = ('WRITTEN_PAST_UNRESOLVED_OCCASION',)*3 + (
        'WRITTEN_CURRENT_EVALUATION','WRITTEN_FUTURE_RELATIVE','WRITTEN_PAST_UNRESOLVED_OCCASION')
    bindings = []
    for i, ((field, span, role), claim) in enumerate(zip(roles,c['claims'],strict=True)):
        ref = ids[i]; main = ev(claim.get('evidence_indexes'),field,span)
        subject = {'binding':'OMITTED','source_entity':None,'evidence_indexes':[]}
        args = []; qualifiers = []
        if role == 'work':
            subject = {'binding':'EXPLICIT','source_entity':'自分の仕事',
                       'evidence_indexes':ev(claim.get('subject',{}).get('evidence_indexes'),field,(span[0],span[0]+5))}
            supplied = claim.get('predicate',{}).get('arguments',[])
            require(type(supplied) is list and len(supplied) == 1)
            args = [dict(role='WRITTEN_が',text='自分の仕事',claim_ref=None,
                         evidence_indexes=ev(supplied[0].get('evidence_indexes'),field,(span[0],span[0]+6)))]
        if role in ('negative','next'):
            supplied = claim.get('predicate',{}).get('arguments',[])
            require(type(supplied) is list and len(supplied) == 1)
            asp = (span[0],span[0]+7) if role == 'negative' else (m.start('margin'),m.end('margin')+1)
            args = [dict(role='WRITTEN_を' if role=='negative' else 'WRITTEN_で',
                         text='手伝ったこと' if role=='negative' else m['margin'],claim_ref=None,
                         evidence_indexes=ev(supplied[0].get('evidence_indexes'),field,asp))]
        if role in ('joy','negative'):
            supplied = claim.get('qualifiers',[])
            require(type(supplied) is list and len(supplied) == 1)
            qspan = m.span('report') if role=='joy' else m.span('negation')
            qualifiers = [dict(kind='REPORTED_SPEECH_SCOPE' if role=='joy' else 'NEGATION_SCOPE',
                text=original[field][slice(*qspan)],scope_refs=[ref],
                evidence_indexes=ev(supplied[0].get('evidence_indexes'),field,qspan))]
        tspan = (m.start('next'),m.start('next')+1) if role=='next' else span
        expected = dict(claim_id=ref,kind=kinds[i],text=original[field][slice(*span)],subject=subject,
            predicate=dict(surface=predicates[i],arguments=args),
            polarity=dict(value='SCOPED_NEGATION' if role=='negative' else 'AFFIRMED',
                          scope_refs=[ref],evidence_indexes=ev(claim.get('polarity',{}).get('evidence_indexes'),field,span)),
            modality=dict(value='WISH_OR_INTENTION_NOT_ACTION' if role=='next' else 'ASSERTED_AS_WRITTEN',
                          evidence_indexes=ev(claim.get('modality',{}).get('evidence_indexes'),field,span)),
            about_time=dict(kind=times[i],expression='次' if role=='next' else None,
                anchor_source_id=source_id if role=='next' else None,
                evidence_indexes=ev(claim.get('about_time',{}).get('evidence_indexes'),field,tspan)),
            qualifiers=qualifiers,evidence_indexes=main)
        require(claim == expected,'piece_candidate_semantic_scope')
        nspan = m.span('second') if role in ('work','late') else span
        node = f'{field}:{nspan[0]}:{nspan[1]}'
        binding_ref='piece-binding:'+digest([commitment,field,*span])
        bindings.append(PieceSemanticClaimBindingV1(ref,node,binding_ref,source_id,field,
            *span,len(original[field][:span[0]].encode()),len(original[field][:span[1]].encode()),canonical(claim)))
    relations=[]
    for i, supplied in enumerate(c['relations']):
        require(type(supplied) is dict and type(supplied.get('relation_id')) is str
                and supplied['relation_id'].strip(), 'piece_relation_id')
        ref=supplied['relation_id']; rtype=('SOURCE_WRITTEN_CONCESSION',
                'WRITTEN_TE_LINK_CAUSALITY_UNRESOLVED')[i]
        start=m.start('second') if i==0 else m.start('work'); end=m.end('second')
        indexes=ev(supplied.get('evidence_indexes'),'memo',(start,end))
        left,right=(ids[0],ids[1]) if i==0 else (ids[1],ids[2])
        require(supplied==dict(relation_id=ref,type=rtype,from_claim_id=left,to_claim_id=right,
            polarity='AFFIRMED',scope_refs=[ref],qualifiers=[],evidence_indexes=indexes),
            'piece_candidate_relation_scope')
        relations.append(PieceSemanticRelationBindingV1(ref,rtype,(left,right),canonical(evidence[indexes[0]])))
    require(len({r.relation_ref for r in relations})==2
            and not set(ids)&{r.relation_ref for r in relations},'piece_relation_duplicate')
    require(used==set(range(len(evidence))),'piece_unused_evidence')
    return tuple(bindings),tuple(relations)


def _snapshot_payload(snapshot):
    row=asdict(snapshot); row['source_snapshot']=_source_payload(snapshot.source_snapshot)
    return row


def _derive_snapshot(request, packet):
    prepared=_request(request); material=prepared.payload(); original=material['sources'][0]['original']
    commitment=material['sources'][0]['source_commitment']
    require(type(packet) is dict and set(packet)=={'candidate','evidence'})
    claims,relations=_packet_bindings(original,packet,request.source.saved_input_id,commitment)
    selections=_selections(original,commitment)
    snapshot=PieceSemanticSnapshotV1(prepared.request_id,request.source,commitment,canonical(packet),claims,relations,selections,'')
    row=_snapshot_payload(snapshot); row.pop('snapshot_ref')
    return replace(snapshot,snapshot_ref='piece-snapshot:'+digest(row))


def validate_piece_semantic_snapshot(request, snapshot):
    require(type(snapshot) is PieceSemanticSnapshotV1,'piece_snapshot_type')
    # Verification of immutable saved meaning, not a new candidate acquisition/adoption.
    require(canonical(_snapshot_payload(snapshot)) == canonical(_snapshot_payload(
        _derive_snapshot(request,_candidate(snapshot.candidate_packet)))),
            'piece_snapshot_source_or_meaning_changed')
    return snapshot


def source_nodes(snapshot):
    """Source-owned full sentences; no prose transformations or plan decisions."""
    original=json.loads(snapshot.source_snapshot.saved_original_json)
    m,_=_family(original)
    spans=[('memo',m.span('joy')),('memo',m.span('second')),('memo',m.span('negative')),
           ('memo',m.span('next')),('memo_action',(0,len(original['memo_action'])))]
    return tuple((f'{f}:{a}:{b}',f,a,b,original[f][a:b]) for f,(a,b) in spans)


def validate_snapshot_self(snapshot):
    from .piece_v1c import PieceGenerationRequest
    source=snapshot.source_snapshot
    # Full request binding (including owner) is checked again at Engine/reload.
    for tier in ('free','plus','premium'):
        request=PieceGenerationRequest('verify-saved-piece',source,source.owner_id,
            source.saved_input_id,source.source_version,tier=tier)
        if _request(request).request_id==snapshot.request_ref:
            return validate_piece_semantic_snapshot(request,snapshot)
    raise PieceSemanticError('piece_snapshot_request_binding')


def admit_piece_semantic_snapshot(request, semantic_input):
    prepared=_request(request)
    require(type(semantic_input) is PieceSemanticInputV1
            and semantic_input.semantic_profile==PROFILE
            and type(semantic_input.prepared) is PreparedRequest
            and semantic_input.prepared==prepared,'piece_semantic_input_binding')
    receipt=semantic_input.receipt
    require(type(receipt) is CandidateReceipt,'piece_receipt_type')
    metadata=json.loads(receipt.metadata_json)
    require(set(metadata)=={'provider','model','revision','usage','finish_reason','elapsed_seconds','evidence_check'})
    checked=receive_candidate(prepared,request_id=receipt.request_id,raw_output=receipt.raw_output,
        **{k:v for k,v in metadata.items() if k!='evidence_check'})
    require(receipt==checked,'piece_receipt_forged')
    if receipt.status!='CANDIDATE_UNREVIEWED':
        decision='HOLD' if receipt.status in ('TIMEOUT','TOKEN_LIMIT','EMPTY','PROVIDER_ERROR','UNKNOWN_FINISH') else 'REJECTED'
        return PieceSemanticResultV1(decision,('piece_receipt_'+receipt.status.lower(),),prepared.request_id)
    snapshot=_derive_snapshot(request,_candidate(receipt.candidate_json))
    return PieceSemanticResultV1('ADOPTED_PROVISIONAL',(),prepared.request_id,snapshot)


def generate_piece_semantic(request, semantic_input):
    request_ref = ''
    result = None
    try:
        request_ref = _request(request).request_id
        result=admit_piece_semantic_snapshot(request,semantic_input)
        if result.snapshot is None:
            return result
        return resume_piece_semantic(request,serialize_piece_semantic_state(request,result.snapshot))
    except PieceSemanticUnsupported as exc:
        return PieceSemanticResultV1('UNSUPPORTED',(str(exc),),request_ref)
    except (ValueError,TypeError,KeyError,AttributeError,IndexError,UnicodeError,RecursionError,OverflowError):
        if result is not None and result.snapshot is not None:
            # A body failure cannot turn an adopted immutable meaning into
            # a rejection or erase it. The caller can save this snapshot and
            # explicitly resume; no body is attached to the failed attempt.
            return replace(result,reason_codes=('piece_semantic_body_unavailable',))
        return PieceSemanticResultV1('REJECTED',('piece_semantic_input_rejected',),request_ref)


def serialize_piece_semantic_state(request,snapshot,plan=None,artifact=None):
    validate_piece_semantic_snapshot(request,snapshot)
    require(artifact is None or plan is not None,'piece_artifact_without_plan')
    if plan is not None:
        from piece_v2_content_policy import validate_piece_semantic_preservation
        validate_piece_semantic_preservation(snapshot,plan,artifact,tier=request.tier,
                                            requested_format=request.requested_format)
    return canonical(dict(schema_version=STATE_SCHEMA,request_binding=dict(
        request_id=request.request_id,owner_id=request.expected_owner_id,
        saved_input_id=request.expected_saved_input_id,source_version=request.expected_source_version,
        tier=request.tier,requested_format=request.requested_format),snapshot=_snapshot_payload(snapshot),
        plan=asdict(plan) if plan is not None else None,
        artifact=asdict(artifact) if artifact is not None else None))


def _row(cls,row,**converted):
    require(type(row) is dict and set(row)=={f.name for f in fields(cls)},'piece_saved_closed_shape')
    return cls(**(row|converted))


def load_piece_semantic_state(request,raw):
    require(type(raw) is str,'piece_saved_state_type')
    row=json.loads(raw,object_pairs_hook=_unique_object,parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    require(type(row) is dict and set(row)=={'schema_version','request_binding','snapshot','plan','artifact'}
            and row['schema_version']==STATE_SCHEMA,'piece_saved_schema')
    expected=dict(request_id=request.request_id,owner_id=request.expected_owner_id,
        saved_input_id=request.expected_saved_input_id,source_version=request.expected_source_version,
        tier=request.tier,requested_format=request.requested_format)
    require(row['request_binding']==expected,'piece_saved_request_binding')
    stored=row['snapshot']; require(type(stored) is dict and type(stored.get('candidate_packet')) is str)
    snapshot=_derive_snapshot(request,_candidate(stored['candidate_packet']))
    require(canonical(stored)==canonical(_snapshot_payload(snapshot)),'piece_saved_snapshot_binding')
    p=row['plan'];a=row['artifact']; plan=artifact=None
    if p is not None:
        plan=_row(PieceSemanticPlanV1,p,duties=tuple(_row(PieceSemanticDutyBindingV1,d,
            **{k:tuple(d[k]) for k in ('claim_refs','node_refs','source_binding_refs','required_scope_refs')}) for d in p['duties']),
            block_node_ids=tuple(tuple(b) for b in p['block_node_ids']),
            selection_duties=tuple(p['selection_duties']),eligible_formats=tuple(p['eligible_formats']))
    if a is not None:
        artifact=_row(PieceSemanticArtifactV1,a,body_blocks=tuple(a['body_blocks']),
            eligible_formats=tuple(a['eligible_formats']),retained_selection_refs=tuple(a['retained_selection_refs']),
            claim_realizations=tuple(_row(PieceSemanticRealizationV1,r,node_refs=tuple(r['node_refs']),
                source_binding_refs=tuple(r['source_binding_refs'])) for r in a['claim_realizations']))
    # Canonical roundtrip rejects bool-as-int and shape coercions as well as hashes.
    require(serialize_piece_semantic_state(request,snapshot,plan,artifact)==canonical(row),
            'piece_saved_state_binding')
    return snapshot,plan,artifact


def resume_piece_semantic(request,raw):
    from .piece_v1c import compile_piece_artifact_plan,realize_piece_artifact
    from piece_v2_content_policy import validate_piece_semantic_preservation
    snapshot,plan,artifact=load_piece_semantic_state(request,raw)
    if plan is None:
        plan=compile_piece_artifact_plan(snapshot)
    if artifact is None:
        artifact=realize_piece_artifact(snapshot,plan,tier=request.tier,requested_format=request.requested_format)
    validate_piece_semantic_preservation(snapshot,plan,artifact,tier=request.tier,
                                        requested_format=request.requested_format)
    return PieceSemanticResultV1('ADOPTED_PROVISIONAL',('piece_semantic_generated_private',),
                                snapshot.request_ref,snapshot,plan,artifact)
