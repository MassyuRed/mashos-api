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
# A sentence-initial time topic qualifies an explicit evaluation. The comma
# fixes its boundary; time words inside the nominal target are not extracted.
# Preserve the written relative time and contrast/additive particle without
# resolving a date, inferring a previous evaluation, or changing predicate tense.
# The same operator also qualifies a proved direct transitive expression.
# It is not a general temporal parser or authority for other scoped wishes.
_TEMPORAL_EVALUATION = re.compile(
    r'^(?P<scope>(?P<premise>以前|当時|今|現在)(?P<marker>は|も))[、，,][ \t\u3000]*'
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
    'SOURCE_EXPLICIT_TIME_CONTEXT': 'PIECE_SOURCE_TIME_SCOPED_EXPRESSION',
}



def _same_self_scope_author(premise: str, speaker: str) -> bool:
    """Reuse the existing conservative, literally identical scope author."""
    from piece_v2_expression import _SELF_TOPIC, _DEPENDENT_START, _EMBEDDED_REPORT
    topic = _SELF_TOPIC.fullmatch(premise + '。')
    return (topic is not None and topic['speaker'] == speaker
            and not re.search(r'[はがも、，,]', topic['body'])
            and not _DEPENDENT_START.search(topic['body'])
            and not _EMBEDDED_REPORT.search(topic['body']))


def _direct_transitive_expression(sentence: str) -> re.Match[str] | None:
    """Read an explicit self topic, nominal object and existing transitive verb.

    Reuse the focal grammar's predicates, not a second intention dictionary.
    The written を and complete object own the argument; a state or rejection
    is not rewritten as a wish. Comma-delimited or marked outer clauses are
    not swallowed into an antecedent. Existing scope parsing owns those.
    This is bounded surface interpretation, not general Japanese parsing.
    """
    from piece_v2_generation import _transitive_predicate_forms, _NESTED, _DEICTIC
    from piece_v2_expression import _REFERENCE
    # Derive finite register/time forms of the existing transitive predicates,
    # not another lexical predicate or a guessed current intention. The past
    # branch is explicitly bound for format planning; every matched surface
    # stays in the original scalar/UTF-8 span and is written without tense or
    # polarity conversion. A single existing finite modal may qualify a plain
    # predicate; its complete written surface remains the predicate span.
    # Relative focus, reported speech and stacked modals remain separate.
    predicates, past_predicates, modal_predicates = _transitive_predicate_forms()
    match = re.fullmatch(
        r'(?P<speaker>私|わたし|僕|ぼく|俺|おれ)は[、，,]?'
        r'(?P<object>.+?)を(?P<predicate>(?:(?:'
        + '|'.join(map(re.escape, predicates)) + r')|(?P<past_predicate>'
        + '|'.join(map(re.escape, past_predicates)) + r'))(?P<modal>'
        + _FINITE_EVALUATION_MODAL + r')?)。', sentence)
    if match is None:
        return None
    # The modal's own polite register is allowed, not a polite finite base
    # followed by another auxiliary. Reuse the evaluation owner's closed
    # possibility/non-universality operators; never remove them to authorize
    # a current intention, affirmative refusal, or another predicate.
    modal = match['modal']
    if modal and match['predicate'][:-len(modal)] not in modal_predicates:
        return None
    obj = match['object']
    # Two complete references joined by the written と form ONE object of
    # this existing transitive predicate. The source resolver must still bind
    # both independently. No literal/comparative/nested operand or same-head
    # ambiguity is admitted here; punctuation inside this exact pair is not
    # an outer clause boundary. Preserve its order and predicate verbatim.
    pair = _NOMINAL_REFERENCE_CONJUNCTION.fullmatch(obj)
    paired = (pair is not None
              and _NOMINAL_REFERENCE_TARGET.fullmatch(pair['left'])['head']
              != _NOMINAL_REFERENCE_TARGET.fullmatch(pair['right'])['head'])
    if (not obj.endswith(('こと', 'もの', '時間'))
            or (re.search(r'[、，,]', obj) and not paired) or 'のは' in obj
            or any(marker in obj for marker in _SCOPE_RELATIONS)
            or _NESTED.search(obj) or _DEICTIC.search(obj)
            or _SELF_TOPIC_MENTION.search(obj)
            or (_REFERENCE.search(obj)
                and not (_NOMINAL_REFERENCE_TARGET.fullmatch(obj) or paired))):
        return None
    return match


def _scoped_focal_expression(sentence: str) -> tuple[re.Match[str], re.Match[str]] | None:
    """Bind a focal or direct transitive expression inside its written scope.

    Reuse the same transitive predicate/author grammar; a condition, reason or
    concession does not establish a missing author or fulfill a wish. The
    returned offsets are relative to the original sentence and expression,
    so nominal references can retain their exact original evidence ranges.
    A time topic may qualify the same complete direct transitive expression,
    but does not extend the focal construction or infer an omitted author.
    """
    from piece_v2_generation import _FOCUS, _DEICTIC, _NESTED
    scoped = (_SCOPED_EXPRESSION.fullmatch(sentence)
              or _TEMPORAL_EVALUATION.fullmatch(sentence))
    if scoped is None:
        return None
    # Time qualifies the whole written direct expression, not its object or
    # predicate tense. Reuse the finite author/object/polarity/register proof;
    # neither a time word nor a wish suffix licenses a different construction.
    # In particular the existing relative focal grammar stays outside this
    # temporal extension. Evaluation frames retain their separate owner.
    focal = (_direct_transitive_expression(scoped['intention'])
             if scoped.re is _TEMPORAL_EVALUATION else
             (_FOCUS.fullmatch(scoped['intention'])
              or _direct_transitive_expression(scoped['intention'])))
    if focal is None:
        return None
    self_premise = _SELF_TOPIC_MENTION.search(scoped['premise']) is not None
    if self_premise:
        # Share only the already-admitted sentence-initial author. This is
        # not general participant inference or a speaker-alias equivalence.
        if not _same_self_scope_author(scoped['premise'], focal['speaker']):
            return None
    obj = focal['object'].lstrip('、，,')
    if (not obj.endswith(('こと', 'もの', '時間')) or 'のは' in obj
            or _NESTED.search(obj) or _DEICTIC.search(obj)):
        if self_premise:
            return None
        raise unavailable('focal_object_not_self_contained')
    return scoped, focal

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
        focal = _scoped_focal_expression(node.value)
        match = (_SCOPED_EXPRESSION.fullmatch(node.value)
                 or _TEMPORAL_EVALUATION.fullmatch(node.value))
        frame = evaluations.get(node.node_id)
        # A whole-sentence finite match is not evidence of an inner scope.
        # The evaluation parser must have bound its speaker after the actual
        # connective, leaving the premise outside the evaluated argument.
        inner_evaluation = (match is not None and frame is not None
                            and frame.scalar_parts[0][0] == start + match.start('intention'))
        if _SELF_TOPIC.fullmatch(node.value) and focal is None and not inner_evaluation:
            continue
        if match is None or (_SELF_TOPIC_MENTION.search(match['premise'])
                             and focal is None and not inner_evaluation):
            continue
        temporal = match.re is _TEMPORAL_EVALUATION
        if temporal and node.node_id not in evaluations and focal is None:
            continue
        topic = _SELF_TOPIC.fullmatch(match['intention'])
        if node.node_id not in evaluations:
            if focal is None and (
                    topic is None or not _SCOPED_SELF_END.search(topic['body'])
                    or _DEPENDENT_START.search(topic['body'])
                    or _EMBEDDED_REPORT.search(topic['body'])):
                continue
        relation = ('SOURCE_EXPLICIT_TIME_CONTEXT' if temporal
                    else _SCOPE_RELATIONS[match['marker']])
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
# abstract an identity using the roles and owner links the author writes.
_ROLE = r'(?:友人|同僚|上司|部下|先輩|後輩|先生)'
# A written relational chain is one role, not just its terminal noun.
# Keep every link (including repeated roles); the existing vocabulary is
# unchanged. Reuse the existing speaker vocabulary only when its possessive
# is written; an omitted possessor or unknown modifier is not inferred.
_ROLE_OWNER = r'(?:(?:私|わたし|僕|ぼく|俺|おれ)の)?'
# Name recognition and replacement share one complete written token boundary.
# Script is not evidence of a relationship: kana and mixed-script identities
# still need the same explicit role/owner proof as kanji identities. Do not
# truncate a longer name to a known suffix or normalize its original spelling.
# Halfwidth voiced marks remain separate source scalars. Width and the two
# middle-dot spellings are NOT aliases; each exact name needs its own proof.
# Hiragana/Latin are still outside this grammar. In particular ordinary words
# such as たくさん are not people. This is not general PII recognition.
_PERSON_NAME_CHARS = '一-龥々ァ-ヺーｦ-ﾟ'
_PERSON_NAME_TOKEN_CHARS = _PERSON_NAME_CHARS + '・･'
_PERSON_NAME = (r'[' + _PERSON_NAME_CHARS + r']+'
                r'(?:[・･][' + _PERSON_NAME_CHARS + r']+)*さん')
# A dot inside a name is not the same boundary as a dot AFTER a completed
# さん. The latter can separate two named people or two role phrases.
_PERSON_NAME_LEFT_BOUNDARY = (r'(?:(?<![' + _PERSON_NAME_TOKEN_CHARS
                              + r'])|(?<=さん・)|(?<=さん･))')
_ROLE_NAME = re.compile(_PERSON_NAME_LEFT_BOUNDARY + r'(?P<role>' + _ROLE_OWNER + _ROLE
                        + r'(?:の' + _ROLE + r')*)の'
                        r'(?P<name>' + _PERSON_NAME + r')')
# Scan a whole potential token, including malformed joins, before checking its
# binding. A leading/trailing/doubled dot must not expose a shorter known
# suffix to the writer or silently escape the existing unbound-name check.
_HONORIFIC_NAME = re.compile(
    r'(?:[' + _PERSON_NAME_CHARS + r']|(?<!さん)[・･])'
    r'[' + _PERSON_NAME_TOKEN_CHARS + r']*さん')


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def piece_public_role_aliases(bindings: tuple[PieceRoleBinding, ...]) -> dict[str, str]:
    """Resolve written name/role links without dropping an intermediate owner.

    Raw bindings retain their original spans. A named possessor contributes
    only its own explicit, uniquely resolved role; it is never guessed from
    proximity. Resolve dependencies before suffix compatibility so a later
    written qualification also reaches the person's dependent relationships.
    """
    relations: dict[str, list[tuple[str | None, str]]] = {}
    for binding in bindings:
        owners = tuple(_HONORIFIC_NAME.finditer(binding.role))
        if owners:
            owner = owners[-1]
            # The nearest named owner includes the earlier links through its
            # own binding. Reusing the whole prefix would duplicate them.
            suffix = binding.role[owner.end():]
            if not re.fullmatch(r'の' + _ROLE + r'(?:の' + _ROLE + r')*', suffix):
                raise unavailable('public_role_binding_missing')
            relation = (owner.group(), suffix[1:])
        else:
            relation = (None, binding.role)
        relations.setdefault(binding.name, []).append(relation)
    for choices in relations.values():
        owners = {owner for owner, _ in choices if owner is not None}
        if len(owners) > 1:
            # Different explicitly named people are not the same owner merely
            # because one public role happens to be a suffix of the other.
            raise unavailable('public_role_binding_ambiguous')
        if any(owner not in relations for owner in owners):
            raise unavailable('public_role_owner_not_bound')
    by_name: dict[str, str] = {}
    pending = dict(relations)
    while pending:
        resolved = []
        for name, choices in pending.items():
            if any(owner is not None and owner not in by_name for owner, _ in choices):
                continue
            selected = None
            for owner, role in choices:
                role = by_name[owner] + 'の' + role if owner is not None else role
                if selected is None or role.endswith('の' + selected):
                    selected = role
                elif selected != role and not selected.endswith('の' + role):
                    raise unavailable('public_role_binding_ambiguous')
            by_name[name] = selected
            resolved.append(name)
        if not resolved:
            # A cycle, including a self-reference, has no source-proven root.
            # Even an additional short role cannot license guessing the edge.
            raise unavailable('public_role_binding_ambiguous')
        for name in resolved:
            del pending[name]
    if len(set(by_name.values())) != len(by_name):
        raise unavailable('public_role_binding_ambiguous')
    return by_name


def _role_bindings(text: str) -> tuple[PieceRoleBinding, ...]:
    names = tuple(_HONORIFIC_NAME.finditer(text))
    names_by_end = {match.end(): match for match in names}
    by_end: dict[int, PieceRoleBinding] = {}
    collected = []
    for match in _ROLE_NAME.finditer(text):
        start = match.start()
        if text[:start].rstrip().endswith('の'):
            owner = names_by_end.get(start - 1)
            if owner is None:
                raise unavailable('public_role_owner_not_bound')
            # Inline owners extend the exact source range, including their
            # names. A bare named owner can be bound elsewhere in this input.
            enclosing = by_end.get(owner.end())
            start = enclosing.source_start if enclosing is not None else owner.start()
            if text[:start].rstrip().endswith('の'):
                raise unavailable('public_role_owner_not_bound')
        binding = PieceRoleBinding(match['name'], text[start:match.start('name') - 1],
                                   start, match.end())
        collected.append(binding)
        by_end[binding.source_end] = binding
    bindings = tuple(collected)
    by_name = piece_public_role_aliases(bindings)
    bound_ends = {binding.source_end for binding in bindings}
    for match in names:
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
_NOMINAL_REFERENCE_BODY = r'(?P<reference>(?:その|この)(?P<head>時間|こと|もの))'
_NOMINAL_REFERENCE_TARGET = re.compile(_NOMINAL_REFERENCE_BODY)
# A whole conjunction, shared by the conditional and transitive boundaries.
# Matching this surface supplies no antecedent or author authority.
_NOMINAL_REFERENCE_CONJUNCTION = re.compile(
    r'(?P<left>(?:その|この)(?:時間|こと|もの))と[、，,]?[ \t\u3000]*'
    r'(?P<right>(?:その|この)(?:時間|こと|もの))')
_NOMINAL_REFERENCE = re.compile(
    r'^(?:(?:私|わたし|僕|ぼく|俺|おれ)は[、，,]?)?'
    + _NOMINAL_REFERENCE_BODY
    + r'(?=[はがをにでとのも]|から|だけ|さえ|まで|より)')
_COMPOSITE_OBJECT = re.compile(r'より|ではなく|だけでなく|または|あるいは')
_REFERENCE_RELATION = 'SOURCE_BOUND_NOMINAL_REFERENCE'


def _evaluation_target_references(target: str) -> tuple[tuple[int, int, str], ...]:
    """Locate whole reference operands without replacing the evaluation target.

    A source-written ``Aより、B`` retains the existing single-reference
    operand rule. It can also contain two references with distinct nominal
    heads, as can ``Aと、B``. Each must independently bind to one prior
    source object in the resolver below; neither operand certifies the other.
    Two whole reference operands can also use their explicit と/より operator
    without a comma. This compact form does not admit a literal operand or
    infer a missing operator. Same-head and nested pairs stay unresolved.
    Both sides and the exact marker remain ONE evaluation target, not two
    separately evaluated objects, an inferred winner, or a user's wish.
    These relative source ranges do not themselves resolve any referent.
    """
    from piece_v2_expression import _REFERENCE
    from piece_v2_generation import _NESTED
    direct = _NOMINAL_REFERENCE_TARGET.fullmatch(target)
    if direct is not None:
        return ((0, len(target), direct['head']),)
    if not _REFERENCE.search(target):
        return ()
    comparison = re.fullmatch(r'(?P<left>.+?)より[、，,][ \t\u3000]*(?P<right>.+)', target)
    # Keep comparison precedence: a と inside its complete literal operand
    # must not steal the outer より boundary from the existing grammar.
    # Only two complete reference tokens can omit punctuation. Matching the
    # entire target prevents a nested comparison or a suffix inside an operand
    # from being treated as the outer operator. The existing resolver below
    # must still bind BOTH references to distinct, unique source objects.
    compact_pair = re.fullmatch(
        r'(?P<left>(?:その|この)(?:時間|こと|もの))(?:より|と)[ \t\u3000]*'
        r'(?P<right>(?:その|この)(?:時間|こと|もの))', target)
    compound = comparison or compact_pair or re.fullmatch(
        r'(?P<left>.+?)と[、，,][ \t\u3000]*(?P<right>.+)', target)
    if compound is None:
        raise unavailable('evaluation_target_not_self_contained')
    references = []
    for part in ('left', 'right'):
        operand = compound[part]
        reference = _NOMINAL_REFERENCE_TARGET.fullmatch(operand)
        if reference is not None:
            references.append((compound.start(part), compound.end(part), reference['head']))
        elif (not operand.endswith(('こと', 'もの', '時間'))
                or _REFERENCE.search(operand) or _COMPOSITE_OBJECT.search(operand)
                or _NESTED.search(operand) or 'のは' in operand
                or operand.startswith(('、', '，', ',', ' ', '\t', '\u3000'))):
            raise unavailable('evaluation_target_not_self_contained')
    single_comparison = comparison is not None and len(references) == 1
    distinct_pair = len(references) == 2 and references[0][2] != references[1][2]
    if not (single_comparison or distinct_pair):
        raise unavailable('evaluation_target_not_self_contained')
    return tuple(references)


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
    # Parse evaluation arguments without granting their reference authority.
    # This resolver is the sole source of that authority, avoiding a cycle in
    # which a candidate evaluation would certify its own antecedent.
    evaluations = {frame.node_id: frame for frame in
                   _personal_evaluation_shapes(text, nodes, sentences)}
    candidates: dict[str, list[tuple[str, int, int]]] = {}
    bound: list[PieceNominalReference] = []
    for node, sentence in zip(nodes, sentences, strict=True):
        start, end = sentence.source_start, sentence.source_end
        if (sentence.node_id != node.node_id or start < 0 or end > len(text)
                or text[start:end] != node.value):
            raise unavailable('piece_reference_source_binding')
        # Preserve the old sentence-initial reference grammar. A parsed
        # personal evaluation can additionally bind a whole nominal target or
        # an explicit comparison operand at its original range. The
        # two views of a finite self-topic can describe the SAME mention; it
        # must receive exactly one edge. A scope and a target can instead own
        # two different mentions, both checked in original source order.
        mentions: dict[tuple[int, int], tuple[str, str, int]] = {}
        mention = _NOMINAL_REFERENCE.match(node.value)
        if mention is None and _NOMINAL_REFERENCE_TARGET.match(node.value):
            # A whole nominal premise can meet the existing conditional
            # connective directly, without a case/topic particle in between.
            # Bind only that complete written premise at the sentence start;
            # a suffix inside a larger premise or a partial connective is not
            # licensed. The same unique-prior-object resolver below owns its
            # authority. Referring to an earlier wish/value does not assert
            # its existence, fulfill this condition, or transfer its stance.
            conditional = _SCOPED_EXPRESSION.fullmatch(node.value)
            if (conditional is not None and _SCOPE_RELATIONS[conditional['marker']]
                    == 'SOURCE_EXPLICIT_CONDITION'):
                mention = _NOMINAL_REFERENCE_TARGET.fullmatch(conditional['premise'])
        if mention is not None:
            span = (start + mention.start('reference'), start + mention.end('reference'))
            mentions[span] = (mention['head'], 'unresolved_reference', span[0])
        # A coordinated conditional premise retains BOTH complete source
        # referents. Reuse the existing two-operand parser and unique-prior
        # resolver; the first case-marked mention is the same span, not a
        # second edge. No predicate, comparison, third operand or suffix is
        # admitted by this bounded nominal conjunction.
        if _NOMINAL_REFERENCE_TARGET.match(node.value):
            conditional = _SCOPED_EXPRESSION.fullmatch(node.value)
            if (conditional is not None
                    and _SCOPE_RELATIONS[conditional['marker']] == 'SOURCE_EXPLICIT_CONDITION'
                    and _NOMINAL_REFERENCE_CONJUNCTION.fullmatch(conditional['premise'])):
                for left, right, head in _evaluation_target_references(conditional['premise']):
                    # Both operands resolve against preceding discourse, not
                    # each other. Same-head pairs remain outside the parser.
                    mentions[(start + left, start + right)] = (head, 'unresolved_reference', start)
        frame = evaluations.get(node.node_id)
        if frame is not None:
            a, b = frame.scalar_parts[2]
            for left, right, head in _evaluation_target_references(text[a:b]):
                # A sibling operand is part of the complete evaluation
                # target, not a new discourse antecedent. Resolve both
                # against the context preceding that whole target; never
                # select an object from inside the pair by proximity.
                mentions[(a + left, a + right)] = (
                    head, 'evaluation_target_not_self_contained', a)
        focal = (_FOCUS.fullmatch(node.value)
                 or _direct_transitive_expression(node.value))
        expression_start = start
        if focal is None:
            scoped_focal = _scoped_focal_expression(node.value)
            if scoped_focal is not None:
                scoped, focal = scoped_focal
                expression_start += scoped.start('intention')
        if focal is not None:
            # The already-admitted focal grammar owns this whole object and
            # its explicit speaker/predicate, including a written outer scope.
            # A complete nominal reference uses the SAME unique-prior-object
            # resolver as an evaluation; matching a pronoun alone is not proof.
            # Do not extend this to embedded or comparative focal operands.
            obj = focal['object'].lstrip('、，,')
            reference = _NOMINAL_REFERENCE_TARGET.fullmatch(obj)
            if reference is not None:
                r_end = expression_start + focal.end('object')
                r_start = r_end - len(obj)
                mentions[(r_start, r_end)] = (
                    reference['head'], 'unresolved_reference', r_start)
            elif _NOMINAL_REFERENCE_CONJUNCTION.fullmatch(obj):
                # The existing focal and direct word orders own the same
                # complete transitive argument. Neither supplies a referent;
                # reuse the operand parser and exact unique-prior resolver.
                # Both mentions see the context BEFORE the whole argument;
                # the first operand cannot supply the second's antecedent.
                r_start = expression_start + focal.end('object') - len(obj)
                for left, right, head in _evaluation_target_references(obj):
                    mentions[(r_start + left, r_start + right)] = (
                        head, 'unresolved_reference', r_start)
        for (r_start, r_end), (head, failure, context_end) in sorted(mentions.items()):
            prior = candidates.get(head, [])
            if len(prior) != 1:
                raise unavailable(failure)
            antecedent_id, a_start, a_end = prior[0]
            known = {(a_end - len(head), a_end)}
            known.update((r.reference_scalar_span[1] - len(head), r.reference_scalar_span[1])
                         for r in bound if r.nominal_head == head)
            if any(m.span() not in known for m in re.finditer(re.escape(head), text[:context_end])):
                raise unavailable(failure)
            bound.append(PieceNominalReference(
                antecedent_id, node.node_id, head, (a_start, a_end),
                (len(text[:a_start].encode('utf-8')), len(text[:a_end].encode('utf-8'))),
                (r_start, r_end),
                (len(text[:r_start].encode('utf-8')), len(text[:r_end].encode('utf-8')))))
        if focal is not None:
            # Bind the complete object, not its preceding scope or speaker.
            # Its existence as a referent never asserts that a condition was
            # met or changes the focal predicate's negation/commitment.
            obj = focal['object'].lstrip('、，,')
            a_end = expression_start + focal.end('object')
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
# Both word orders share state/modal composition. Finite polite auxiliaries
# are separate from the relative focus grammar: a complete polite denial is
# not a relative predicate and cannot be followed by another modal here.
# A single source-written degree modifier belongs to the WHOLE predicate.
# Keep it inside its scalar/UTF-8 span in both word orders, including negative,
# past and modal forms. Do not turn degree into certainty or a numeric score,
# infer an omitted modifier, or move a modifier out of the nominal argument.
# Unmodelled adverbs and stacked modifiers do not acquire scope here.
# Register is source text, not a normalization instruction. Plain state may
# take a polite outer modal; a polite negative is already finite. Keep the
# whole predicate in its original span so the existing writer preserves it.
_PLAIN_EVALUATION_MODAL = r'かもしれない|とは限らない'
_FINITE_EVALUATION_MODAL = _PLAIN_EVALUATION_MODAL + r'|かもしれません|とは限りません'
_FINITE_NEGATIVE = (r'(?P<finite_negative>(?:では|じゃ)'
                    r'(?:ありませんでした|ありません|なかったです|ないです))|')
_EVALUATIVE_PREDICATE = (
    r'(?P<predicate>(?:とても|かなり|少し|あまり)?'
    r'(?P<base>大切|大事|重要|必要|好き|苦手)'
    r'(?P<inflection>(?:(?P<state>(?:では|じゃ)(?:なかった|ない)|だった)'
    r'(?P<state_modal>{modal})?|'
    r'(?P<bare_modal>{modal})|{finite_negative}{copula})))')
_EVALUATIVE_FOCUS = re.compile(
    r'^(?P<speaker>私|わたし|僕|ぼく|俺|おれ)'
    r'(?P<construction>にとって|が)[、，,]?'
    + _EVALUATIVE_PREDICATE.format(
        copula='な', modal=_PLAIN_EVALUATION_MODAL, finite_negative='')
    + r'のは[、，,]?(?P<target>.+?)(?P<copula>です|だ)。$')
_EVALUATIVE_FINITE = re.compile(
    r'^(?P<speaker>私|わたし|僕|ぼく|俺|おれ)'
    r'(?P<construction>にとって|は)[、，,]?'
    r'(?P<target>.+?)が'
    # A complete finite evaluation may leave its nonpast affirmative copula
    # unwritten. The explicit speaker, target particle and predicate still
    # bind here; an absent copula is not inserted into the source or author.
    # Keep the focal construction's required relative/final copulas separate.
    + _EVALUATIVE_PREDICATE.format(
        copula=r'(?P<copula>でした|です|だ)?', modal=_FINITE_EVALUATION_MODAL,
        finite_negative=_FINITE_NEGATIVE)
    + r'。$')
_SIMPLE_NOUN = re.compile(r'[一-龥々ァ-ヴー]+')


def _personal_evaluation_shapes(text: str, nodes: tuple[MeaningNode, ...],
                          sentences: tuple[PieceSentenceMeaning, ...]
                          ) -> tuple[PiecePersonalEvaluation, ...]:
    """Recover an explicit personal evaluation, never an omitted viewpoint.

    A complete nominal target is kept as one argument: internal comparison,
    negation and conditions are not shortened into a winning keyword. Outer
    denial, reported speech, nested focus and unresolved deixis are not this
    construction. They are not turned into the author's current conviction.
    A nominal-reference target or comparison operand is only a candidate
    here; the source resolver must bind it before evaluation admission.
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
        scoped = (_SCOPED_EXPRESSION.fullmatch(node.value)
                  or _TEMPORAL_EVALUATION.fullmatch(node.value))
        if scoped is not None:
            inner = (_EVALUATIVE_FOCUS.fullmatch(scoped['intention'])
                     or _EVALUATIVE_FINITE.fullmatch(scoped['intention']))
            if inner is not None and (
                    not _SELF_TOPIC_MENTION.search(scoped['premise'])
                    or _same_self_scope_author(scoped['premise'], inner['speaker'])):
                # Prefer the proven inner evaluation even when the outer
                # finite grammar could swallow its premise and second author
                # into the target. Both word orders keep the same argument;
                # the scope does not become an evaluated object or a wish.
                match = inner
                expression_start += scoped.start('intention')
        if match is None:
            continue
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
        referential = bool(_evaluation_target_references(target))
        if (not (nominal or bare)
                or (_REFERENCE.search(target) and not referential) or _NESTED.search(target)
                or 'のは' in target or target.startswith(('、', '，', ','))):
            raise unavailable('evaluation_target_not_self_contained')
        spans = tuple((expression_start + match.start(key), expression_start + match.end(key))
                      for key in ('speaker', 'predicate', 'target'))
        utf8 = tuple((len(text[:a].encode('utf-8')), len(text[:b].encode('utf-8')))
                     for a, b in spans)
        state = match['state'] or match.groupdict().get('finite_negative') or ''
        modal = match['state_modal'] or match['bare_modal'] or ''
        # These describe the inner evaluation under the outer commitment.
        # NON_UNIVERSAL over NEGATIVE is not an affirmative evaluation, and
        # a present modal must not reset the evaluation's original past time.
        polarity = 'NEGATIVE' if state.startswith(('では', 'じゃ')) else 'AFFIRMATIVE'
        temporal = ('PAST' if state.endswith(('だった', 'なかった', 'なかったです',
                                             'ありませんでした'))
                    or match['copula'] == 'でした' else 'NONPAST')
        commitment = ('POSSIBLE' if modal in ('かもしれない', 'かもしれません') else
                      'NON_UNIVERSAL' if modal in ('とは限らない', 'とは限りません') else 'ASSERTED')
        frames.append(PiecePersonalEvaluation(
            node.node_id, match['construction'], kind, spans, utf8,
            match['copula'] or '', polarity, temporal, commitment))
    return tuple(frames)


def _personal_evaluations(text: str, nodes: tuple[MeaningNode, ...],
                          sentences: tuple[PieceSentenceMeaning, ...]
                          ) -> tuple[PiecePersonalEvaluation, ...]:
    """Admit evaluative arguments only after their actual source binding.

    A reference keeps its own speaker, polarity, time and commitment. It does
    not inherit the antecedent's evaluation, become a new antecedent, or gain
    a guessed expanded surface. The existing plan/author retains both full
    propositions and validates the exact reference edges independently.
    """
    frames = _personal_evaluation_shapes(text, nodes, sentences)
    referential = [(frame, _evaluation_target_references(text[slice(*frame.scalar_parts[2])]))
                   for frame in frames]
    if any(parts for _, parts in referential):
        references = _nominal_references(text, nodes, sentences)
        for frame, parts in referential:
            for left, right, head in parts:
                a, b = frame.scalar_parts[2][0] + left, frame.scalar_parts[2][0] + right
                utf8 = (len(text[:a].encode('utf-8')), len(text[:b].encode('utf-8')))
                matching = tuple(ref for ref in references
                                 if ref.reference_node_id == frame.node_id
                                 and ref.nominal_head == head
                                 and ref.reference_scalar_span == (a, b)
                                 and ref.reference_utf8_span == utf8)
                if len(matching) != 1:
                    raise unavailable('evaluation_target_not_self_contained')
    return frames


def validate_piece_personal_evaluations(meaning: PieceSourceMeaning) -> None:
    expected = _personal_evaluations(meaning.envelope.raw_utf8.decode('utf-8'),
                                     meaning.graph.nodes, meaning.sentences)
    if meaning.personal_evaluations != expected:
        raise unavailable('piece_evaluation_source_binding')


def _piece_editorial_roles(sentences: tuple[str, ...],
                           evidence: InputEvidenceRef) -> dict[int, str]:
    """Project register only for provisional role classification.

    The existing Piece grammar already admits an optional polite auxiliary,
    while the shared compatibility classifier can miss the same predicate in
    that register. Keep its original admitted roles. For an otherwise missing
    intent role, classify a register-neutral view of the SAME ordered source
    sentences, using only the already-admitted self-topic/wish grammar.

    This view is not an envelope, graph, evidence span or visible wording. No
    speaker, predicate, negation, scope, or sentence is removed. A projected
    slot still needs the shared classifier's admitted intent role; matching
    the terminal grammar alone never supplies that role. The shared owner,
    duplicate handling, and author/format admission are not relaxed.
    """
    from piece_v2_expression import (
        _DEPENDENT_START, _EMBEDDED_REPORT, _INTENT_ROLES, _SELF_TOPIC, _WISH_END,
    )

    def classify(values: tuple[str, ...]) -> dict[int, str]:
        blocks = build_input_meaning_blocks(
            current_input={'memo': ''.join(values)}, shaped_user_phrases=(),
            evidence=evidence)
        result: dict[int, str] = {}
        for block in blocks:
            match = re.fullmatch(r'meaning:(\d+):[^:]+', block.block_key)
            if match and block.include_in_piece_core:
                result[int(match[1])] = block.role
        return result

    roles = classify(sentences)
    projected = list(sentences)
    changed: list[int] = []
    for index, sentence in enumerate(sentences):
        if roles.get(index) in _INTENT_ROLES:
            continue
        topic = _SELF_TOPIC.fullmatch(sentence)
        if (topic is None or not _WISH_END.search(topic['body'])
                or not topic['body'].endswith('です')
                or _DEPENDENT_START.search(topic['body'])
                or _EMBEDDED_REPORT.search(topic['body'])):
            continue
        # Only the grammar's optional register auxiliary is projected away.
        # Original punctuation and the rest of the complete source stay put.
        end = topic.end('body')
        projected[index] = sentence[:end - len('です')] + sentence[end:]
        changed.append(index)
    if changed:
        projected_roles = classify(tuple(projected))
        for index in changed:
            role = projected_roles.get(index)
            if role in _INTENT_ROLES:
                roles[index] = role
    return roles


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
    role_by_position = _piece_editorial_roles(
        sentences, InputEvidenceRef(kind='saved_input', ref_id=source.saved_input_id))
    # Provisional role classification may omit duplicate summaries. It is
    # NEVER allowed to omit an original sentence in the Piece graph below.
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
