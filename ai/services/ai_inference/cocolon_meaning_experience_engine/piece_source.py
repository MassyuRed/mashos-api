"""Piece's original-source adapter into CMEE's existing grounded graph types.

No Emlis label, observation, reception, question answer or inferred relationship
is a Piece source. The shared meaning blocks supply provisional editorial roles
only. Full original sentences, including duplicates and dependent clauses, own
all visible propositions. Authenticated saved-record retrieval remains B5.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re

from emlis_ai_input_meaning_block_service import build_input_meaning_blocks
from emlis_ai_types import EvidenceRef as InputEvidenceRef
from piece_v2_content_policy import check_existing_detectors, unavailable
from .contracts import (
    AttachmentAdmission, EpistemicState, EvidenceRef, GroundedMeaningGraph,
    MeaningEdge, MeaningNode, OwnerClass, ResolverResolution, SourceEnvelope,
    SourceOwnerDisposition, SourceOwnerResolution, VisibleAuthority,
)


@dataclass(frozen=True, slots=True, repr=False)
class PieceSentenceMeaning:
    node_id: str
    evidence_id: str
    source_start: int
    source_end: int
    role: str


@dataclass(frozen=True, slots=True, repr=False)
class PieceRoleBinding:
    """A user's explicit name-to-role binding, not an inferred anonymization."""
    name: str
    role: str
    source_start: int
    source_end: int


@dataclass(frozen=True, slots=True, repr=False)
class PieceNominalReference:
    """Private source spans for a bounded, provisional discourse attachment."""
    antecedent_node_id: str
    reference_node_id: str
    nominal_head: str
    antecedent_scalar_span: tuple[int, int]
    antecedent_utf8_span: tuple[int, int]
    reference_scalar_span: tuple[int, int]
    reference_utf8_span: tuple[int, int]


@dataclass(frozen=True, slots=True, repr=False)
class PieceSourceMeaning:
    envelope: SourceEnvelope
    graph: GroundedMeaningGraph
    evidence: tuple[EvidenceRef, ...]
    sentences: tuple[PieceSentenceMeaning, ...]
    role_bindings: tuple[PieceRoleBinding, ...]
    nominal_references: tuple[PieceNominalReference, ...] = ()


# Relationship terms, not topic/final-sentence dispatch vocabulary. We only
# abstract an identity when the author supplies the replacement role verbatim.
_ROLE_NAME = re.compile(r'(?P<role>友人|同僚|上司|部下|先輩|後輩|先生)の'
                        r'(?P<name>[一-龥々]{1,6}さん)')
_HONORIFIC_NAME = re.compile(r'[一-龥々]{1,6}さん')


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def _role_bindings(text: str) -> tuple[PieceRoleBinding, ...]:
    bindings = tuple(PieceRoleBinding(m['name'], m['role'], m.start(), m.end())
                     for m in _ROLE_NAME.finditer(text))
    by_name: dict[str, str] = {}
    by_role: dict[str, str] = {}
    for binding in bindings:
        if (binding.name in by_name and by_name[binding.name] != binding.role
                or binding.role in by_role and by_role[binding.role] != binding.name):
            # Do not collapse two different people into one indistinguishable
            # role, or resolve an ambiguous identity by picking the last one.
            raise unavailable('public_role_binding_ambiguous')
        by_name[binding.name] = binding.role
        by_role[binding.role] = binding.name
    for match in _HONORIFIC_NAME.finditer(text):
        if match.group() not in by_name:
            raise unavailable('public_role_binding_missing')
        if (re.match(r'(?:という|と言う|っていう|と呼|と書|と読)', text[match.end():])
                or re.search(r'(?:名前|名字|姓|呼び名)は[、，,]?$', text[:match.start()])):
            # Here the name is itself what the author is talking about.
            # Replacing it by a relationship would change the proposition.
            raise unavailable('public_identity_is_material')
    return bindings


# Reuse the nominal heads admitted by the existing focal grammar. This does
# not infer an omitted event, person, cause or a bare pronoun's referent.
_NOMINAL_REFERENCE = re.compile(
    r'^(?:(?:私|わたし|僕|ぼく|俺|おれ)は[、，,]?)?'
    r'(?P<reference>(?:その|この)(?P<head>時間|こと|もの))'
    r'(?=[はがをにでとのも]|から|だけ|さえ|まで|より)')
_COMPOSITE_OBJECT = re.compile(r'より|ではなく|だけでなく|または|あるいは')
_REFERENCE_RELATION = 'SOURCE_BOUND_NOMINAL_REFERENCE'


def _nominal_references(text: str, nodes: tuple[MeaningNode, ...],
                        sentences: tuple[PieceSentenceMeaning, ...]
                        ) -> tuple[PieceNominalReference, ...]:
    """Attach an explicit nominal reference to one prior focal object.

    Only existing, complete focal objects can introduce an antecedent. Every
    earlier occurrence of its nominal head must belong to that object or an
    already bound mention. A second candidate, an unmodelled mention or an
    internal contrast remains unresolved; nearest-word guessing is not used.
    The writer keeps the entire antecedent and following qualification in one
    source-ordered reading group, rather than expanding a vague pronoun into
    an invented visible proposition.
    """
    from piece_v2_generation import _FOCUS
    from piece_v2_expression import _REFERENCE
    candidates: dict[str, list[tuple[str, int, int]]] = {}
    bound: list[PieceNominalReference] = []
    for node, sentence in zip(nodes, sentences, strict=True):
        start, end = sentence.source_start, sentence.source_end
        if (sentence.node_id != node.node_id or start < 0 or end > len(text)
                or text[start:end] != node.value):
            raise unavailable('piece_reference_source_binding')
        mention = _NOMINAL_REFERENCE.match(node.value)
        if mention is not None:
            head = mention['head']
            prior = candidates.get(head, [])
            if len(prior) != 1:
                raise unavailable('unresolved_reference')
            antecedent_id, a_start, a_end = prior[0]
            r_start, r_end = start + mention.start('reference'), start + mention.end('reference')
            known = {(a_end - len(head), a_end)}
            known.update((r.reference_scalar_span[1] - len(head), r.reference_scalar_span[1])
                         for r in bound if r.nominal_head == head)
            if any(m.span() not in known for m in re.finditer(re.escape(head), text[:r_start])):
                raise unavailable('unresolved_reference')
            bound.append(PieceNominalReference(
                antecedent_id, node.node_id, head, (a_start, a_end),
                (len(text[:a_start].encode('utf-8')), len(text[:a_end].encode('utf-8'))),
                (r_start, r_end),
                (len(text[:r_start].encode('utf-8')), len(text[:r_end].encode('utf-8')))))
        focal = _FOCUS.fullmatch(node.value)
        if focal is None:
            continue
        obj = focal['object'].lstrip('、，,')
        head = next((h for h in ('こと', 'もの', '時間') if obj.endswith(h)), None)
        if (head is None or obj.count(head) != 1 or _REFERENCE.search(obj)
                or _COMPOSITE_OBJECT.search(obj)):
            continue
        a_end = start + focal.end('object')
        candidates.setdefault(head, []).append((node.node_id, a_end - len(obj), a_end))
    return tuple(bound)


def _reference_edges(references: tuple[PieceNominalReference, ...],
                      nodes: tuple[MeaningNode, ...]) -> tuple[MeaningEdge, ...]:
    by_id = {node.node_id: node for node in nodes}
    return tuple(MeaningEdge(
        edge_id=f'piece:reference{index+1}', owner_id=by_id[ref.reference_node_id].owner_id,
        relation=_REFERENCE_RELATION, source_node_id=ref.reference_node_id,
        target_node_id=ref.antecedent_node_id, grounding_kind='source_bound_nominal_reference',
        epistemic_state=EpistemicState.SOURCE_EXPLICIT,
        evidence_ids=(by_id[ref.antecedent_node_id].evidence_ids[0],
                      by_id[ref.reference_node_id].evidence_ids[0]))
        for index, ref in enumerate(references))


def validate_piece_nominal_references(meaning: PieceSourceMeaning) -> None:
    """The artifact planner consumes the source attachments, not a free allowlist."""
    expected = _nominal_references(meaning.envelope.raw_utf8.decode('utf-8'),
                                   meaning.graph.nodes, meaning.sentences)
    edges = tuple(e for e in meaning.graph.edges if e.relation == _REFERENCE_RELATION)
    if (meaning.nominal_references != expected
            or edges != _reference_edges(expected, meaning.graph.nodes)):
        raise unavailable('piece_reference_source_binding')


def build_piece_source_meaning(source: object, *, expected_owner_id: str,
                               expected_saved_input_id: str,
                               expected_source_version: str) -> PieceSourceMeaning:
    # Import the established internal snapshot/grammar owner, not its output
    # compiler. Its complete-sentence admission is retained without a raw fallback.
    from piece_v2_generation import PieceSourceSnapshot, _sentences
    if type(source) is not PieceSourceSnapshot:
        raise unavailable('source_type')
    if not all(isinstance(value, str) and value.strip() for value in (
            source.owner_id, source.saved_input_id, source.source_version,
            source.original_text, expected_owner_id, expected_saved_input_id,
            expected_source_version)):
        raise unavailable('source_identity')
    if source.owner_id != expected_owner_id:
        raise unavailable('source_owner_mismatch')
    if source.saved_input_id != expected_saved_input_id:
        raise unavailable('saved_input_binding_mismatch')
    if source.source_version != expected_source_version:
        raise unavailable('source_version_binding_mismatch')
    if source.source_role != 'original' or source.source_stage not in (
            'normal_observation', 'pre_question_observation'):
        raise unavailable('source_role_or_stage_not_yet_supported')
    text = source.original_text
    check_existing_detectors(text)
    sentences = _sentences(text)
    aliases = _role_bindings(text)
    roles = build_input_meaning_blocks(
        current_input={'memo': ''.join(sentences)}, shaped_user_phrases=(),
        evidence=InputEvidenceRef(kind='saved_input', ref_id=source.saved_input_id))
    role_by_position: dict[int, str] = {}
    for block in roles:
        # The shared compatibility classifier may omit duplicate summaries.
        # It is NEVER allowed to omit an original sentence in the Piece graph.
        match = re.fullmatch(r'meaning:(\d+):[^:]+', block.block_key)
        if match and block.include_in_piece_core:
            role_by_position[int(match[1])] = block.role
    raw = text.encode('utf-8')
    identity = json.dumps([source.owner_id, source.saved_input_id,
                           source.source_version, source.source_role,
                           source.source_stage, _digest(text)], ensure_ascii=False)
    envelope_id = 'piece-source:' + _digest(identity)
    envelope = SourceEnvelope(
        envelope_id=envelope_id, source_record_id=source.saved_input_id,
        source_role='ORIGINAL_USER_INPUT',
        source_schema_version='piece.saved_source.original.v1',
        source_contract_version='piece.source_lineage.v1', source_encoding='UTF-8',
        label_contract_id='NOT_APPLICABLE', label_contract_digest='',
        raw_utf8=raw, raw_sha256=_digest(text))
    nodes, edges, evidence, meanings, resolutions = [], [], [], [], []
    cursor = 0
    for index, sentence in enumerate(sentences):
        start = text.find(sentence, cursor)
        end = start + len(sentence)
        if start < cursor or text[start:end] != sentence:
            raise unavailable('source_sentence_range_mismatch')
        cursor = end
        node_id, owner_id, evidence_id = f'piece:s{index+1}', f'piece:o{index+1}', f'piece:e{index+1}'
        utf8_start = len(text[:start].encode('utf-8'))
        utf8_end = len(text[:end].encode('utf-8'))
        evidence.append(EvidenceRef(
            evidence_id=evidence_id, source_span_id=node_id,
            source_envelope_id=envelope_id, field_path='original_text', element_index=0,
            field_utf8_start=0, field_utf8_end=len(raw), scalar_start=start,
            scalar_end=end, utf8_start=utf8_start, utf8_end=utf8_end,
            field_sha256=_digest(text), literal_sha256=_digest(sentence)))
        nodes.append(MeaningNode(
            node_id=node_id, owner_id=owner_id, node_kind='PIECE_SOURCE_PROPOSITION',
            grounding_kind='explicit', value=sentence,
            epistemic_state=EpistemicState.SOURCE_EXPLICIT, evidence_ids=(evidence_id,)))
        meanings.append(PieceSentenceMeaning(node_id, evidence_id, start, end,
                                            role_by_position.get(index, 'source_context')))
        resolutions.append(SourceOwnerResolution(
            meaning_owner_id=owner_id, owner_class=OwnerClass.REQUIRED,
            resolver_resolution=ResolverResolution.UNIQUE,
            attachment_admission=AttachmentAdmission.PROVISIONAL_ONLY,
            visible_authority=VisibleAuthority.SOURCE_EXPLICIT,
            source_owner_disposition=SourceOwnerDisposition.SOURCE_EXPLICIT_VISIBLE,
            visible_claim_refs=(node_id,), evidence_refs=(evidence_id,),
            target_unknown_ref=None, reason_codes=('piece_complete_source_proposition',)))
        if index:
            edges.append(MeaningEdge(
                edge_id=f'piece:order{index}', owner_id=owner_id,
                relation='SOURCE_ORDER', source_node_id=nodes[index-1].node_id,
                target_node_id=node_id, grounding_kind='explicit',
                epistemic_state=EpistemicState.SOURCE_EXPLICIT,
                evidence_ids=(evidence[index-1].evidence_id, evidence_id)))
    references = _nominal_references(text, tuple(nodes), tuple(meanings))
    edges.extend(_reference_edges(references, tuple(nodes)))
    # Preserve predecessor identities when the graph has no new attachment.
    graph_seed = envelope_id if not references else json.dumps(
        [envelope_id, 'piece.nominal_reference.v1',
         [(r.antecedent_node_id, r.reference_node_id, r.nominal_head,
           r.antecedent_scalar_span, r.reference_scalar_span) for r in references]])
    owners = tuple(node.owner_id for node in nodes)
    graph = GroundedMeaningGraph(
        graph_id='piece-graph:' + _digest(graph_seed), source_envelope_id=envelope_id,
        nodes=tuple(nodes), edges=tuple(edges), owner_dispositions=tuple(resolutions),
        required_owner_refs=owners, active_optional_owner_refs=(),
        source_version=source.source_version, obligation_version='piece.content_meaning.v1',
        owner_universe_digest=_digest(json.dumps(owners)))
    return PieceSourceMeaning(envelope, graph, tuple(evidence), tuple(meanings), aliases, references)
