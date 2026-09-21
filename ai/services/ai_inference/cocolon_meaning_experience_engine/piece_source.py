"""Piece's original-source adapter into CMEE's existing grounded graph types.

No Emlis label, observation, reception, question answer or inferred relationship
is a Piece source. The shared meaning blocks supply provisional editorial roles
only. Full original sentences, including duplicates and dependent clauses, own
all visible propositions. Authenticated saved-record retrieval remains B5.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
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
class PiecePersonalEvaluation:
    """Source-bound experiencer, evaluation predicate and nominal argument.

    These are provisional Piece semantics, not a shared classifier's label or
    a new source. Parts are ordered speaker / predicate / target, in the exact
    original scalar and UTF-8 coordinate systems, before role publicization.
    """
    node_id: str
    construction: str
    kind: str
    scalar_parts: tuple[tuple[int, int], ...]
    utf8_parts: tuple[tuple[int, int], ...]
    copula: str
    polarity: str
    temporal_scope: str
    commitment: str


@dataclass(frozen=True, slots=True, repr=False)
class PieceExpressionScope:
    """A source-marked relation attached to an explicit first-person expression.

    Both clauses remain private exact ranges of the same original sentence.
    The relation describes the written connective, not an inferred cause or
    an assertion that a hypothetical condition has happened or a comparison is a wish.
    A written concession keeps its two sides; it does not supply an inferred
    expectation, a causal explanation or a resolution of their tension.
    """
    node_id: str
    relation: str
    marker: str
    scope_scalar_span: tuple[int, int]
    scope_utf8_span: tuple[int, int]
    expression_scalar_span: tuple[int, int]
    expression_utf8_span: tuple[int, int]


@dataclass(frozen=True, slots=True, repr=False)
class PieceSourceMeaning:
    envelope: SourceEnvelope
    graph: GroundedMeaningGraph
    evidence: tuple[EvidenceRef, ...]
    sentences: tuple[PieceSentenceMeaning, ...]
    role_bindings: tuple[PieceRoleBinding, ...]
    nominal_references: tuple[PieceNominalReference, ...] = ()
    personal_evaluations: tuple[PiecePersonalEvaluation, ...] = ()
    expression_scopes: tuple[PieceExpressionScope, ...] = ()


# These are clause operators, not a list of causes, topics or output phrases.
# Ambiguous origin/causal "から", purpose/concessive "のに", reported wishes
# and unmarked links are not promoted to a relation. Already-admitted
# self-topic sentences keep their previous canonical identity.
_SCOPE_RELATIONS = {
    'ので': 'SOURCE_EXPLICIT_REASON',
    'ならば': 'SOURCE_EXPLICIT_CONDITION',
    'なら': 'SOURCE_EXPLICIT_CONDITION',
    'けれども': 'SOURCE_EXPLICIT_CONCESSION',
    'けれど': 'SOURCE_EXPLICIT_CONCESSION',
}
_SCOPED_EXPRESSION = re.compile(
    r'^(?P<scope>(?P<premise>.+?)(?P<marker>'
    + '|'.join(map(re.escape, _SCOPE_RELATIONS)) + r'))[、，,][ \t]*'
    r'(?P<intention>(?:私|わたし|僕|ぼく|俺|おれ)(?:は|にとって|が)[、，,]?.+。)$')
# Preserve the complete self expression, not an inferred desire lemma.
# 読みたい / 休みたい and a source-written comparison ending みたい retain
# their exact surface. Neither is promoted to a declaration by this operator.
_SCOPED_SELF_END = re.compile(r'(?:たい|たくない)(?:です)?$')
_SELF_TOPIC_MENTION = re.compile(r'(?:私|わたし|僕|ぼく|俺|おれ)は')
_SCOPE_KINDS = {
    'SOURCE_EXPLICIT_REASON': 'PIECE_SOURCE_REASON_SCOPED_EXPRESSION',
    'SOURCE_EXPLICIT_CONDITION': 'PIECE_SOURCE_CONDITION_SCOPED_EXPRESSION',
    'SOURCE_EXPLICIT_CONCESSION': 'PIECE_SOURCE_CONCESSION_SCOPED_EXPRESSION',
}


def _expression_scopes(text: str, nodes: tuple[MeaningNode, ...],
                   sentences: tuple[PieceSentenceMeaning, ...]
                   ) -> tuple[PieceExpressionScope, ...]:
    from piece_v2_expression import (_SELF_TOPIC, _DEPENDENT_START, _EMBEDDED_REPORT)
    # A scope can qualify an existing value/preference, not only a wish.
    # The evaluation parser proves its speaker, predicate and whole argument;
    # a clause ending alone cannot grant authorship or invent an intention.
    evaluations = {frame.node_id: frame for frame in
                   _personal_evaluations(text, nodes, sentences)}
    scopes = []
    for node, sentence in zip(nodes, sentences, strict=True):
        start, end = sentence.source_start, sentence.source_end
        if (sentence.node_id != node.node_id or start < 0 or end > len(text)
                or text[start:end] != node.value):
            raise unavailable('piece_intent_scope_source_binding')
        if _SELF_TOPIC.fullmatch(node.value):
            continue
        match = _SCOPED_EXPRESSION.fullmatch(node.value)
        if match is None or _SELF_TOPIC_MENTION.search(match['premise']):
            continue
        topic = _SELF_TOPIC.fullmatch(match['intention'])
        if node.node_id not in evaluations:
            if (topic is None or not _SCOPED_SELF_END.search(topic['body'])
                    or _DEPENDENT_START.search(topic['body'])
                    or _EMBEDDED_REPORT.search(topic['body'])):
                continue
        relation = _SCOPE_RELATIONS[match['marker']]
        a, b = start + match.start('scope'), start + match.end('scope')
        c, d = start + match.start('intention'), start + match.end('intention')
        scopes.append(PieceExpressionScope(
            node.node_id, relation, match['marker'], (a, b),
            (len(text[:a].encode('utf-8')), len(text[:b].encode('utf-8'))),
            (c, d), (len(text[:c].encode('utf-8')), len(text[:d].encode('utf-8')))))
    return tuple(scopes)


def validate_piece_expression_scopes(meaning: PieceSourceMeaning) -> None:
    """Keep the writer's scope interpretation tied to its actual source."""
    expected = _expression_scopes(meaning.envelope.raw_utf8.decode('utf-8'),
                              meaning.graph.nodes, meaning.sentences)
    if meaning.expression_scopes != expected:
        raise unavailable('piece_intent_scope_source_binding')
    by_node = {scope.node_id: scope for scope in expected}
    for node in meaning.graph.nodes:
        expected_kind = (_SCOPE_KINDS[by_node[node.node_id].relation]
                         if node.node_id in by_node else 'PIECE_SOURCE_PROPOSITION')
        if node.node_kind != expected_kind:
            raise unavailable('piece_intent_scope_kind_binding')


# Relationship terms, not topic/final-sentence dispatch vocabulary. We only
# abstract an identity when the author supplies the replacement role verbatim.
_ROLE = r'(?:友人|同僚|上司|部下|先輩|後輩|先生)'
# A written relational chain is one role, not just its terminal noun.
# Keep every link (including repeated roles); the existing vocabulary is
# unchanged. Reuse the existing speaker vocabulary only when its possessive
# is written; an omitted possessor or unknown modifier is not inferred.
_ROLE_OWNER = r'(?:(?:私|わたし|僕|ぼく|俺|おれ)の)?'
_ROLE_NAME = re.compile(r'(?<![一-龥々])(?P<role>' + _ROLE_OWNER + _ROLE
                        + r'(?:の' + _ROLE + r')*)の'
                        r'(?P<name>[一-龥々]{1,6}さん)')
_HONORIFIC_NAME = re.compile(r'[一-龥々]{1,6}さん')


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def piece_public_role_aliases(bindings: tuple[PieceRoleBinding, ...]) -> dict[str, str]:
    """Use the most qualified compatible role explicitly bound to each name.

    A shorter written suffix must not erase an existing qualification. Two
    incompatible chains remain ambiguous; this is not general coreference.
    Every selected alias is a whole source-written role, never a merged one.
    """
    by_name: dict[str, str] = {}
    for binding in bindings:
        previous = by_name.get(binding.name)
        if previous is None or binding.role.endswith('の' + previous):
            by_name[binding.name] = binding.role
        elif previous != binding.role and not previous.endswith('の' + binding.role):
            raise unavailable('public_role_binding_ambiguous')
    if len(set(by_name.values())) != len(by_name):
        # Complete qualifications can distinguish people with the same final
        # role, but two identical full aliases cannot distinguish two names.
        raise unavailable('public_role_binding_ambiguous')
    return by_name


def _role_bindings(text: str) -> tuple[PieceRoleBinding, ...]:
    bindings = tuple(PieceRoleBinding(m['name'], m['role'], m.start(), m.end())
                     for m in _ROLE_NAME.finditer(text))
    for binding in bindings:
        if text[:binding.source_start].rstrip().endswith('の'):
            # A suffix match inside an unresolved genitive would silently
            # discard its owner in subsequent name mentions. Do not infer it.
            raise unavailable('public_role_owner_not_bound')
    by_name = piece_public_role_aliases(bindings)
    bound_ends = {binding.source_end for binding in bindings}
    for match in _HONORIFIC_NAME.finditer(text):
        if (text[:match.start()].rstrip().endswith('の')
                and match.end() not in bound_ends):
            # An earlier alias cannot license a later, unsupported role phrase
            # or a role-looking suffix inside another noun for that same name.
            raise unavailable('public_role_binding_missing')
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

    Only complete focal objects or source-bound personal-evaluation arguments
    can introduce an antecedent. Every earlier occurrence of its nominal head
    must belong to that object or an
    already bound mention. A second candidate, an unmodelled mention or an
    internal contrast remains unresolved; nearest-word guessing is not used.
    The writer keeps the entire antecedent and following qualification in one
    source-ordered reading group, rather than expanding a vague pronoun into
    an invented visible proposition.
    """
    from piece_v2_generation import _FOCUS
    from piece_v2_expression import _REFERENCE
    # Derive from actual source again, not caller-supplied frame metadata.
    # Evaluation polarity/time describes the evaluation, not the referent's
    # existence: a tentative or past value does not become a present promise.
    evaluations = {frame.node_id: frame for frame in
                   _personal_evaluations(text, nodes, sentences)}
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
        if focal is not None:
            obj = focal['object'].lstrip('、，,')
            a_end = start + focal.end('object')
        elif node.node_id in evaluations:
            a_start, a_end = evaluations[node.node_id].scalar_parts[2]
            obj = text[a_start:a_end]
        else:
            continue
        head = next((h for h in ('こと', 'もの', '時間') if obj.endswith(h)), None)
        if (head is None or obj.count(head) != 1 or _REFERENCE.search(obj)
                or _COMPOSITE_OBJECT.search(obj)):
            continue
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


# Typed evaluative predicates, not topic keywords or canned output sentences.
# A wish is not inferred from liking, importance, need or a negative evaluation.
_VALUE_BASES = frozenset({'大切', '大事', '重要', '必要'})
# Both word orders share the same state/modal composition. The only
# construction-specific inflection is the relative or finite copula.
_EVALUATIVE_PREDICATE = (
    r'(?P<predicate>(?P<base>大切|大事|重要|必要|好き|苦手)'
    r'(?P<inflection>(?:(?P<state>(?:では|じゃ)(?:なかった|ない)|だった)'
    r'(?P<state_modal>かもしれない|とは限らない)?|'
    r'(?P<bare_modal>かもしれない|とは限らない)|{copula})))')
_EVALUATIVE_FOCUS = re.compile(
    r'^(?P<speaker>私|わたし|僕|ぼく|俺|おれ)'
    r'(?P<construction>にとって|が)[、，,]?'
    + _EVALUATIVE_PREDICATE.format(copula='な')
    + r'のは[、，,]?(?P<target>.+?)(?P<copula>です|だ)。$')
_EVALUATIVE_FINITE = re.compile(
    r'^(?P<speaker>私|わたし|僕|ぼく|俺|おれ)'
    r'(?P<construction>にとって|は)[、，,]?'
    r'(?P<target>.+?)が'
    + _EVALUATIVE_PREDICATE.format(copula=r'(?P<copula>でした|です|だ)')
    + r'。$')
_SIMPLE_NOUN = re.compile(r'[一-龥々ァ-ヴー]+')


def _personal_evaluations(text: str, nodes: tuple[MeaningNode, ...],
                          sentences: tuple[PieceSentenceMeaning, ...]
                          ) -> tuple[PiecePersonalEvaluation, ...]:
    """Recover an explicit personal evaluation, never an omitted viewpoint.

    A complete nominal target is kept as one argument: internal comparison,
    negation and conditions are not shortened into a winning keyword. Outer
    denial, reported speech, nested focus and unresolved deixis are not this
    construction. They are not turned into the author's current conviction.
    """
    from piece_v2_expression import _REFERENCE
    from piece_v2_generation import _NESTED
    frames = []
    for node, sentence in zip(nodes, sentences, strict=True):
        start, end = sentence.source_start, sentence.source_end
        if (sentence.node_id != node.node_id or start < 0 or end > len(text)
                or text[start:end] != node.value):
            raise unavailable('piece_evaluation_source_binding')
        match = (_EVALUATIVE_FOCUS.fullmatch(node.value)
                 or _EVALUATIVE_FINITE.fullmatch(node.value))
        expression_start = start
        if match is None:
            scoped = _SCOPED_EXPRESSION.fullmatch(node.value)
            if scoped is None or _SELF_TOPIC_MENTION.search(scoped['premise']):
                continue
            # Interpret the already-modelled evaluation inside its written
            # scope. Do not reinterpret the premise as the evaluation target.
            match = (_EVALUATIVE_FOCUS.fullmatch(scoped['intention'])
                     or _EVALUATIVE_FINITE.fullmatch(scoped['intention']))
            if match is None:
                continue
            expression_start += scoped.start('intention')
        kind = 'PERSONAL_VALUE' if match['base'] in _VALUE_BASES else 'PERSONAL_PREFERENCE'
        # A self topic and a が experiencer bind liking/difficulty; neither
        # is freely substituted for the explicit value viewpoint にとって.
        # The target's が is preserved. A contrastive は/も is not rewritten.
        if match['construction'] in ('が', 'は') and kind != 'PERSONAL_PREFERENCE':
            continue
        target = match['target']
        nominal = target.endswith(('こと', 'もの', '時間'))
        # A finite self-topic already owns the experiencer: 私はXが好き.
        # Reuse the existing bounded noun shape without guessing a missing
        # nominalizer or changing the target. Do not extend the が-focus:
        # 私が好きなのはX can instead make a person-like X the experiencer.
        bare = match['construction'] in ('にとって', 'は') and _SIMPLE_NOUN.fullmatch(target)
        if (not (nominal or bare)
                or _REFERENCE.search(target) or _NESTED.search(target)
                or 'のは' in target or target.startswith(('、', '，', ','))):
            raise unavailable('evaluation_target_not_self_contained')
        spans = tuple((expression_start + match.start(key), expression_start + match.end(key))
                      for key in ('speaker', 'predicate', 'target'))
        utf8 = tuple((len(text[:a].encode('utf-8')), len(text[:b].encode('utf-8')))
                     for a, b in spans)
        state = match['state'] or ''
        modal = match['state_modal'] or match['bare_modal'] or ''
        # These describe the inner evaluation under the outer commitment.
        # NON_UNIVERSAL over NEGATIVE is not an affirmative evaluation, and
        # a present modal must not reset the evaluation's original past time.
        polarity = 'NEGATIVE' if state.startswith(('では', 'じゃ')) else 'AFFIRMATIVE'
        temporal = ('PAST' if state.endswith(('だった', 'なかった'))
                    or match['copula'] == 'でした' else 'NONPAST')
        commitment = ('POSSIBLE' if modal == 'かもしれない' else
                      'NON_UNIVERSAL' if modal == 'とは限らない' else 'ASSERTED')
        frames.append(PiecePersonalEvaluation(
            node.node_id, match['construction'], kind, spans, utf8,
            match['copula'] or '', polarity, temporal, commitment))
    return tuple(frames)


def validate_piece_personal_evaluations(meaning: PieceSourceMeaning) -> None:
    expected = _personal_evaluations(meaning.envelope.raw_utf8.decode('utf-8'),
                                     meaning.graph.nodes, meaning.sentences)
    if meaning.personal_evaluations != expected:
        raise unavailable('piece_evaluation_source_binding')


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
    evaluations = _personal_evaluations(text, tuple(nodes), tuple(meanings))
    scopes = _expression_scopes(text, tuple(nodes), tuple(meanings))
    scope_by_node = {scope.node_id: scope for scope in scopes}
    nodes = [replace(node, node_kind=_SCOPE_KINDS[scope_by_node[node.node_id].relation])
             if node.node_id in scope_by_node else node for node in nodes]
    references = _nominal_references(text, tuple(nodes), tuple(meanings))
    edges.extend(_reference_edges(references, tuple(nodes)))
    # Preserve predecessor identities when the graph has no new attachment.
    graph_seed = envelope_id if not references else json.dumps(
        [envelope_id, 'piece.nominal_reference.v1',
         [(r.antecedent_node_id, r.reference_node_id, r.nominal_head,
           r.antecedent_scalar_span, r.reference_scalar_span) for r in references]])
    if evaluations:
        graph_seed = json.dumps([graph_seed, 'piece.personal_evaluation.v1',
                                 [asdict(frame) for frame in evaluations]], ensure_ascii=False)
    owners = tuple(node.owner_id for node in nodes)
    if scopes:
        graph_seed = json.dumps([
            graph_seed, 'piece.intent_scope.v1',
            [(scope.node_id, scope.relation, scope.marker,
              scope.scope_scalar_span, scope.scope_utf8_span,
              scope.expression_scalar_span, scope.expression_utf8_span)
             for scope in scopes]], ensure_ascii=False, separators=(',', ':'))
    graph = GroundedMeaningGraph(
        graph_id='piece-graph:' + _digest(graph_seed), source_envelope_id=envelope_id,
        nodes=tuple(nodes), edges=tuple(edges), owner_dispositions=tuple(resolutions),
        required_owner_refs=owners, active_optional_owner_refs=(),
        source_version=source.source_version, obligation_version='piece.content_meaning.v1',
        owner_universe_digest=_digest(json.dumps(owners)))
    return PieceSourceMeaning(envelope, graph, tuple(evidence), tuple(meanings), aliases,
                              references, evaluations, scopes)
