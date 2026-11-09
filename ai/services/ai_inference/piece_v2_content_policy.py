"""B8 candidate policy. Pure, offline-only; not source retrieval or a public gate.

The bounded editorial compiler has no permission to infer missing meaning.
Original and supplemental admission/CMEE integration remain separate work.
"""
from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping
from piece_v2_contract import PieceContractError, reconstruct_piece_text
from piece_text_formatter import format_reflection_text

FORMATS = ('short_essay', 'quote', 'declaration')
# Short original inputs remain short; minimum length never authorizes padding.
ENVELOPES = {'short_essay': (1, 420, 6), 'quote': (12, 120, 2),
             'declaration': (12, 180, 4)}


# PCE-4 bounded refusal only. Removing a written name does not verify an
# assertion about the remaining relationship. Require a complete affirmative
# clause; label words inside negation, uncertainty, quotation or conditions
# are not proof of this form. A non-match is never public-safety admission.
_ROLE_ASSERTION = re.compile(
    r'(?:^|[。！？!?\r\n])\s*'
    r'(?:(?:私|わたし|僕|ぼく|俺|おれ)の)?'
    r'(?:友人|同僚|上司|家族|先輩|後輩|知人)'
    r'(?:の(?:友人|同僚|上司|家族|先輩|後輩|知人))*'
    r'[はが]\s*[、,]?\s*'
    r'(?:詐欺師|犯罪者|泥棒|嘘つき|うそつき)\s*'
    r'(?:だった|でした|である|です|だ)\s*(?=[。！？!?\r\n]|\Z)'
)


def unavailable(code: str) -> PieceContractError:
    return PieceContractError('PIECE_CONTENT_UNAVAILABLE', code)


def validate_candidate_text(payload: Mapping) -> str:
    """Validate canonical shape/envelope, not semantic or public acceptance."""
    text = reconstruct_piece_text(payload)
    return _validate_text_envelope(text, payload['body_blocks'], payload['format_type'])


def _validate_text_envelope(text, blocks, format_type):
    """Shared shape limits only; this does not confer any meaning/Safety version."""
    lo, hi, sentences = ENVELOPES[format_type]
    n = len(re.sub(r'\s', '', text))
    if not lo <= n <= hi or len(re.findall(r'[。！？!?]', text)) > sentences:
        raise unavailable('content_envelope')
    if any('\n' in b for b in blocks):
        raise unavailable('embedded_block_break')
    return text


def check_existing_detectors(text: str) -> None:
    """Reuse existing detectors; refusal is NOT a complete public safety proof.

    No masked-token or generic fallback is emitted. In particular the legacy
    normalizer's zero-width removal must not split a ZWJ emoji in Piece.
    """
    if any(0xD800 <= ord(c) <= 0xDFFF for c in text):
        raise unavailable('malformed_unicode')
    if any(ord(c) in {*range(0x202A, 0x202F), *range(0x2066, 0x206A),
                     0x200B, 0xFEFF} for c in text):
        raise unavailable('hidden_control')
    # Detection-only view: never use compatibility normalization or the
    # legacy formatter's display_text as canonical Piece/source bytes. This
    # catches fullwidth contact syntax without folding the visible wording,
    # evidence coordinates, emoji sequences or content hashes.
    result = format_reflection_text(unicodedata.normalize('NFKC', text))
    scan = result.normalized_text
    # Japanese letters are Unicode word characters. ASCII contact syntax can
    # touch them, so the legacy \b / \w boundaries cannot protect this path.
    adjacent_mail = re.search(r'(?i)[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}', scan)
    adjacent_url = re.search(r'(?i)(?:https?://|www\.)[^\s<>()]+', scan)
    adjacent_handle = re.search(r'(?<![A-Za-z0-9_@])@[A-Za-z0-9_][A-Za-z0-9_.-]{0,31}', scan)
    if (result.flags or result.display_text is None or adjacent_mail
            or adjacent_url or adjacent_handle or _ROLE_ASSERTION.search(scan)):
        raise unavailable('existing_safety_detector')
    if re.search(r'(?i)(?:bearer\s+|(?:api[_ -]?key|password|token)\s*[:=]|postgres(?:ql)?://)', scan):
        raise unavailable('credential_like_material')


def choose_format(*, tier: str, requested: str | None, eligible: tuple[str, ...],
                  recommended: str) -> str:
    if tier not in ('free', 'plus', 'premium'):
        raise unavailable('tier_invalid')
    if requested is not None and (tier != 'premium' or requested not in eligible):
        raise unavailable('format_choice_not_admitted')
    selected = requested or ('short_essay' if tier == 'free' else recommended)
    if selected not in eligible:
        raise unavailable('format_not_eligible')
    return selected


def _piece_model_feeling(text):
    """Read existing complete SELF feelings; never infer from a selection."""
    from piece_v2_expression import _SELF_TOPIC
    from cocolon_meaning_experience_engine.emlis_answer_update import _FEELING, _NOW
    now = _NOW.match(text)
    prefix = now.group() if now else ''
    value = text[now.end():] if now else text
    topic = _SELF_TOPIC.fullmatch(value)
    if topic is None or not _FEELING.fullmatch('私は' + topic['body']):
        return None
    finite = re.fullmatch(r'(?P<degree>少し|とても|本当は|まだ|全然|あまり)?'
        r'(?P<stem>嬉し|うれし|寂し|さびし|悲し|苦し|つら|辛|怖|こわ|重|楽し|軽)'
        r'(?P<ending>くなかった|かった|くない|い)(?:です)?', topic['body'])
    if finite is None:
        return None
    ending = finite['ending']
    return ('FEELING', 'SELF', finite['stem'], finite['degree'] or '',
        'negative' if ending.startswith('くな') else 'positive',
        'past' if ending.endswith('かった') else 'nonpast',
        ('NOW', 'も' if 'も' in prefix else 'は') if now else ())


def _piece_model_evaluation(text):
    """Read a complete written SELF evaluation with the existing Piece owner.

    The original source still needs its normal admission. These temporary
    nodes are parser input for the visible sentence, never evidence/authority
    supplied by the model. Only the established evaluation grammar supplies
    polarity, time and commitment; the entire nominal target stays literal.
    """
    from cocolon_meaning_experience_engine.contracts import MeaningNode, EpistemicState
    from cocolon_meaning_experience_engine.piece_source import (
        PieceSentenceMeaning, _personal_evaluation_shapes,
        _EVALUATIVE_FOCUS, _EVALUATIVE_FINITE, _evaluation_target_references,
        _SCOPED_EXPRESSION, _TEMPORAL_EVALUATION,
    )
    if _SCOPED_EXPRESSION.fullmatch(text) or _TEMPORAL_EVALUATION.fullmatch(text):
        return None
    match = _EVALUATIVE_FOCUS.fullmatch(text) or _EVALUATIVE_FINITE.fullmatch(text)
    if match is None or _evaluation_target_references(match['target']):
        return None
    node = MeaningNode('piece:visible', 'piece:visible', 'PIECE_SOURCE_PROPOSITION',
        'explicit', text, EpistemicState.SOURCE_EXPLICIT, ())
    span = PieceSentenceMeaning(node.node_id, '', 0, len(text), 'source_context')
    try:
        frames = _personal_evaluation_shapes(text, (node,), (span,))
    except PieceContractError:
        return None
    if len(frames) != 1:
        return None
    frame = frames[0]
    if frame.scalar_parts != tuple(match.span(key) for key in ('speaker', 'predicate', 'target')):
        return None
    predicate = text[slice(*frame.scalar_parts[1])]
    # The grammar admits exactly one of its existing degree operators.
    # Retain it separately from the base and inflection, rather than dropping
    # modifiers or equating a negative modal with an affirmative assertion.
    degree = predicate[:predicate.index(match['base'])]
    return ('EVALUATION', 'SELF', frame.construction, frame.kind,
        text[slice(*frame.scalar_parts[2])], match['base'], degree,
        frame.polarity, frame.temporal_scope, frame.commitment)


def _piece_model_focal(text):
    """Keep the existing complete SELF focal grammar in its original form.

    Predicate wording retains polarity/time/modal scope; the complete target
    stays literal. Named roles/references/scopes still require the S7 owner.
    This does not grant arbitrary unchanged text a semantic interpretation.
    """
    from piece_v2_generation import _FOCUS
    match = _FOCUS.fullmatch(text)
    if match is None:
        return None
    return ('FOCAL', 'SELF', match['predicate'], match['object'])


def _piece_model_read_block(text, *, allow_self_omission=False):
    """Use the finite reader in the person's voice, not Emlis's voice.

    Every visible clause must be read. The only parse-only subject completion
    is a later clause in this same block after explicit SELF, and only when
    the source block was completely explicit SELF. No output is rewritten.
    """
    from cocolon_meaning_experience_engine import natural_reply_meaning as reader
    from emlis_ai_evidence_ledger_service import _split_source_text
    if type(text) is not str or not text.endswith('。') or reader._top_level_text(text) != text:
        return None
    rows = _split_source_text(text, max_len=max(1, len(text)))
    if not rows:
        return None
    result, self_context = [], False
    for row in rows:
        raw = text[row.start:row.end]
        # The ledger excludes a terminal stop; the feeling grammar owns it.
        feeling = _piece_model_feeling(raw + '。')
        evaluation = _piece_model_evaluation(raw + '。')
        focal = _piece_model_focal(raw + '。')
        parsed, count = reader._clauses(raw, 'piece.visible', 'PIECE_OUTPUT', reply=False)
        if feeling is not None or evaluation is not None or focal is not None:
            result.append(next(value for value in (feeling, evaluation, focal) if value is not None))
            self_context = True
            continue
        if len(parsed) != count or len(parsed) != 1:
            if not allow_self_omission or not self_context:
                return None
            day = reader._DAY.match(raw)
            start = day.end() if day else 0
            if reader._SUBJECT.match(raw[start:]):
                return None
            view = raw[:start] + '私は' + raw[start:]
            feeling = _piece_model_feeling(view + '。')
            parsed, count = reader._clauses(view, 'piece.visible', 'PIECE_OUTPUT', reply=False)
            if feeling is not None:
                result.append(feeling)
                continue
            if len(parsed) != count or len(parsed) != 1:
                return None
        witness = parsed[0]
        # The initial slice changes register/order/SELF repetition only. A
        # focus or voice conversion is not licensed by event-key equality.
        if witness.source_construction != 'PLAIN_FINITE':
            return None
        agent, target, arguments = reader._comparison_event(witness)
        # The existing Emlis comparator drops ni/kara while deriving roles.
        # Retain those written cases here: consultation from someone cannot
        # become consultation to someone merely because names/lemmas match.
        value = witness.raw_text
        day = reader._DAY.match(value)
        value = value[day.end():] if day else value
        subject = reader._SUBJECT.match(value)
        start = subject.end() if subject else 0
        written = set()
        for finite, predicate, polarity, modality, time, voice, receiving in reader._FORMS:
            if (predicate, polarity, modality, time, voice) != (witness.predicate,
                    witness.polarity, witness.modality, witness.temporal_scope, witness.voice):
                continue
            if value.endswith(finite):
                args = reader._arguments(value[start:len(value) - len(finite)])
                if args is not None:
                    written.add(tuple((case, reader._participant(noun, reply=False))
                        for case, noun in args if case in {'に', 'から'}))
        if len(written) != 1:
            return None
        result.append(('FINITE', witness.subject, agent, target, tuple(sorted(arguments)),
            witness.predicate, witness.polarity, witness.modality, witness.temporal_scope,
            witness.relative_day, witness.voice, next(iter(written))))
        self_context = self_context and witness.subject == 'SELF' if result[:-1] else witness.subject == 'SELF'
    return tuple(result)


def _piece_model_source_blocks(meaning, plan):
    from cocolon_meaning_experience_engine.piece_source import (
        piece_source_text, piece_text_nodes, validate_piece_saved_fields,
        validate_piece_nominal_references, validate_piece_personal_evaluations,
        validate_piece_expression_scopes,
    )
    from cocolon_meaning_experience_engine.piece_v1c import PieceArtifactPlan
    if type(plan) is not PieceArtifactPlan:
        raise unavailable('piece_model_plan_binding')
    validate_piece_saved_fields(meaning)
    validate_piece_nominal_references(meaning)
    validate_piece_personal_evaluations(meaning)
    validate_piece_expression_scopes(meaning)
    nodes = piece_text_nodes(meaning)
    ids = tuple(n.node_id for n in nodes)
    ordered = tuple(n for group in plan.block_node_ids for n in group)
    if (plan.graph_id != meaning.graph.graph_id or plan.source_version != meaning.graph.source_version
            or len(set(ids)) != len(ids) or sorted(ordered) != sorted(ids)
            or tuple(d.node_id for d in plan.duties) != tuple(n.node_id for n in meaning.graph.nodes)):
        raise unavailable('piece_model_plan_binding')
    spans = {span.node_id: span for span in meaning.sentences}
    text = piece_source_text(meaning)
    if set(spans) != set(ids):
        raise unavailable('piece_model_source_binding')
    blocks = []
    for group in plan.block_node_ids:
        if not group:
            raise unavailable('piece_model_plan_binding')
        positions = [ids.index(n) for n in group]
        if positions != list(range(min(positions), max(positions) + 1)):
            raise unavailable('piece_model_plan_binding')
        a, b = spans[group[0]].source_start, spans[group[-1]].source_end
        block = text[a:b]
        if '\n' in block or '\r' in block:
            raise unavailable('piece_model_source_partition')
        blocks.append(block)
    return tuple(blocks)


def validate_piece_model_preservation(meaning, plan, artifact):
    """Author-free whole-body review for the bounded model Piece arm.

    The reader is independent of the model and author, not an independent
    general Japanese parser. Unknown source/output clauses cannot pass the
    new finite comparison. Existing S7 may still prove its known scopes in
    full; an unchanged opaque substring is not a general semantic admission.
    """
    from collections import Counter
    from cocolon_meaning_experience_engine.piece_v1c import PieceArtifact
    from cocolon_meaning_experience_engine.piece_refined import (
        PieceRefinedMeaning, PieceRefinedPlan, refined_source_ref,
    )
    from piece_v2_contract import validate_piece_text_binding
    if (type(artifact) is not PieceArtifact or artifact.format_type != 'short_essay'
            or artifact.eligible_formats != ('short_essay',)):
        raise unavailable('piece_model_artifact_binding')
    validate_piece_text_binding(artifact.content_payload(), artifact.piece_text, artifact.piece_text_hash)
    validate_candidate_text(artifact.content_payload())
    if type(meaning) is PieceRefinedMeaning:
        if (type(plan) is not PieceRefinedPlan or plan.source_ref != meaning.source_ref
                or meaning.source_ref != refined_source_ref(meaning.source)
                or plan.source_roles != ('ORIGINAL_USER_INPUT', 'SUPPLEMENTAL_ANSWER')
                or plan.eligible_formats != ('short_essay',)):
            raise unavailable('piece_model_source_binding')
        parts = ((meaning.original, plan.original_plan), (meaning.supplemental, plan.supplemental_plan))
    else:
        parts = ((meaning, plan),)
    offset = 0
    for part, child_plan in parts:
        source_blocks = _piece_model_source_blocks(part, child_plan)
        blocks = artifact.body_blocks[offset:offset + len(source_blocks)]
        offset += len(source_blocks)
        if len(blocks) != len(source_blocks):
            raise unavailable('piece_model_block_partition')
        # Existing named-person abstraction and reference dependencies remain
        # owned by S7. Event-key comparison alone must not retain a raw name
        # or reorder the antecedent of "その..." across its dependent clause.
        complete = not (part.role_bindings or part.nominal_references or part.expression_scopes)
        for source_text, output_text in zip(source_blocks, blocks, strict=True):
            source = _piece_model_read_block(source_text)
            all_self = source is not None and all(row[1] == 'SELF' for row in source)
            visible = _piece_model_read_block(output_text, allow_self_omission=all_self)
            if source is None or visible is None or Counter(source) != Counter(visible):
                complete = False
                break
            if source != visible and not all_self:
                complete = False
                break
        if not complete:
            text = '\n\n'.join(blocks)
            import hashlib
            child = PieceArtifact(blocks, text, hashlib.sha256(text.encode()).hexdigest(),
                                  'short_essay', ('short_essay',))
            try:
                validate_source_meaning_preservation(part, child_plan, child)
            except PieceContractError:
                raise unavailable('piece_model_meaning_unassessed_or_changed') from None
    if offset != len(artifact.body_blocks):
        raise unavailable('piece_model_block_partition')
    check_existing_detectors(artifact.piece_text)


def validate_source_meaning_preservation(meaning, plan, artifact) -> None:
    """Inspect a Piece artifact against source arguments, without author replay.

    The existing source owner supplies validated explicit grammar and spans.
    This review checks complete proposition multiplicity, argument order,
    predicate wording (including negation/time/modality), written scope and
    public role identity. Only the current finite editorial operations are
    recognized; it is not a general paraphrase judge or public-safety issuer.
    Nothing here produces/rewrites a candidate, calls an author/plan compiler,
    reads stored data, or grants ready/adjusted. Source-parser independence and
    an independent human review are NOT claimed by this author-free check.
    """
    from cocolon_meaning_experience_engine.piece_semantic_admission import PieceSemanticSnapshotV1
    if type(meaning) is PieceSemanticSnapshotV1:
        # Source identity includes the P1 tier; this path performs review only.
        import json
        from cocolon_meaning_experience_engine.piece_semantic_admission import _request
        from cocolon_meaning_experience_engine.piece_v1c import PieceGenerationRequest
        source = meaning.source_snapshot
        for tier in ('free', 'plus', 'premium'):
            req = PieceGenerationRequest('review-private-piece', source, source.owner_id,
                source.saved_input_id, source.source_version, tier=tier)
            if _request(req).request_id == meaning.request_ref:
                return validate_piece_semantic_preservation(meaning, plan, artifact,
                    tier=tier, requested_format=None)
        raise unavailable('piece_semantic_request_binding')
    from piece_v2_contract import validate_piece_text_binding
    from piece_v2_generation import _FOCUS, _is_unpunctuated_account
    from piece_v2_expression import _SELF_TOPIC, _WISH_END
    from cocolon_meaning_experience_engine.piece_source import (
        PieceSourceMeaning, _direct_transitive_expression, _PERSON_NAME_LEFT_BOUNDARY,
        piece_public_role_aliases, validate_piece_saved_fields,
        validate_piece_nominal_references, validate_piece_personal_evaluations,
        validate_piece_expression_scopes,
        piece_text_nodes, piece_source_text, _scoped_self_topic, _qualified_self_topic,
    )
    from cocolon_meaning_experience_engine.piece_v1c import PieceArtifact, PieceArtifactPlan

    def reject():
        raise unavailable('piece_meaning_not_preserved')

    from cocolon_meaning_experience_engine.piece_refined import PieceSupplementalMeaning
    if (type(meaning) not in (PieceSourceMeaning, PieceSupplementalMeaning) or type(plan) is not PieceArtifactPlan
            or type(artifact) is not PieceArtifact):
        reject()
    validate_piece_saved_fields(meaning)
    validate_piece_nominal_references(meaning)
    validate_piece_personal_evaluations(meaning)
    validate_piece_expression_scopes(meaning)
    validate_piece_text_binding(artifact.content_payload(), artifact.piece_text,
                                artifact.piece_text_hash)
    original = piece_source_text(meaning)
    nodes = meaning.graph.nodes
    ids = tuple(node.node_id for node in nodes)
    ordered = tuple(node_id for group in plan.block_node_ids for node_id in group)
    if (plan.graph_id != meaning.graph.graph_id
            or plan.source_version != meaning.graph.source_version
            or len(set(ids)) != len(ids) or sorted(ordered) != sorted(ids)
            or tuple(d.node_id for d in plan.duties) != ids
            or len(artifact.body_blocks) != len(plan.block_node_ids)
            or not ids or any(not group for group in plan.block_node_ids)):
        reject()
    spans = {s.node_id: s for s in meaning.sentences}
    text_nodes = piece_text_nodes(meaning)
    if set(spans) != {n.node_id for n in text_nodes} or len(meaning.evidence) != len(text_nodes):
        reject()
    for node, evidence in zip(text_nodes, meaning.evidence, strict=True):
        span = spans[node.node_id]
        if (original[span.source_start:span.source_end] != node.value
                or node.evidence_ids != (evidence.evidence_id,)
                or meaning.envelope.raw_utf8[evidence.utf8_start:evidence.utf8_end]
                != node.value.encode('utf-8')):
            reject()
    if meaning.saved_snapshot is not None:
        # Independently retain every field/complete-line boundary from the
        # original spans. A forged plan cannot concatenate those paragraphs.
        paragraphs = []
        previous = None
        for node, evidence in zip(text_nodes, meaning.evidence, strict=True):
            span = spans[node.node_id]
            if (previous is None or evidence.field_path != previous[0]
                    or re.search(r'[\r\n]', original[previous[1]:span.source_start])):
                paragraphs.append([])
            paragraphs[-1].append(node.node_id)
            previous = (evidence.field_path, span.source_end)
        if plan.block_node_ids != tuple(tuple(group) for group in paragraphs):
            reject()

    # Match source nouns to their already-proved public role, never infer a
    # relationship or replace a detected unsafe token with a generic phrase.
    aliases = piece_public_role_aliases(meaning.role_bindings)
    phrases = {}
    for binding in meaning.role_bindings:
        phrase = binding.role + 'の' + binding.name
        if original[binding.source_start:binding.source_end] != phrase:
            reject()
        phrases[phrase] = aliases[binding.name]
    replacements = {**phrases, **aliases}
    matcher = None
    if aliases:
        matcher = re.compile('|'.join(re.escape(p) for p in sorted(phrases, key=len, reverse=True))
                             + '|' + _PERSON_NAME_LEFT_BOUNDARY + '(?:'
                             + '|'.join(re.escape(n) for n in sorted(aliases, key=len, reverse=True)) + ')')

    def anchor(fragment):
        """An escaped matching pattern, not generated Piece text."""
        if matcher is None:
            return re.escape(fragment)
        parts, end = [], 0
        for match in matcher.finditer(fragment):
            parts.extend((re.escape(fragment[end:match.start()]),
                          re.escape(replacements[match.group()])))
            end = match.end()
        return ''.join(parts) + re.escape(fragment[end:])

    evaluations = {f.node_id: f for f in meaning.personal_evaluations}
    scopes = {s.node_id: s for s in meaning.expression_scopes}
    duties = {d.node_id: d.operation for d in plan.duties}
    source_nodes = {n.node_id: n for n in nodes}
    positions = {node_id: i for i, node_id in enumerate(ids)}

    def arguments(node_id, expression):
        stop = re.escape(source_nodes[node_id].value[-1])
        frame = evaluations.get(node_id)
        if frame is not None:
            author, predicate, target = (original[a:b] for a, b in frame.scalar_parts)
            finite = predicate[:-1] + frame.copula if predicate.endswith('な') else predicate
            viewpoint = 'にとって' if frame.construction == 'にとって' else 'は'
            return author, viewpoint, anchor(target) + 'が' + anchor(finite) + stop, None
        focal = _FOCUS.fullmatch(expression)
        direct = _direct_transitive_expression(expression) if focal is None else None
        if focal is not None or direct is not None:
            parsed = focal if focal is not None else direct
            target = parsed['object'].lstrip('、，,') if focal is not None else parsed['object']
            return parsed['speaker'], 'は', anchor(target) + 'を' + anchor(parsed['predicate']) + stop, None
        topic = (_scoped_self_topic(expression) if node_id in scopes
                 else _qualified_self_topic(expression))
        if topic is None:
            reject()
        kind = 'wish' if _WISH_END.search(topic['body']) else 'literal'
        if kind == 'literal' and node_id not in scopes:
            reject()
        return topic['speaker'], 'は', anchor(topic['body']) + stop, kind

    for group, block in zip(plan.block_node_ids, artifact.body_blocks, strict=True):
        sentences = re.findall(r'[^。！？!?]+[。！？!?]', block)
        covered = ''.join(sentences)
        final_id = group[-1]
        if (covered != block and block.startswith(covered)
                and meaning.saved_snapshot is not None
                and duties[final_id] == 'KEEP_COMPLETE_SOURCE_CONTEXT'
                and _is_unpunctuated_account(source_nodes[final_id].value)):
            # A source-bound paragraph may end in its complete action line
            # without a stop. The exact KEEP check still rejects text edits.
            sentences.append(block[len(covered):])
        if ''.join(sentences) != block or len(sentences) != len(group):
            reject()
        previous_id, previous_author = None, None
        for node_id, visible in zip(group, sentences, strict=True):
            node, operation = source_nodes[node_id], duties[node_id]
            if operation == 'KEEP_COMPLETE_SOURCE_CONTEXT':
                if re.fullmatch(anchor(node.value), visible) is None:
                    reject()
                previous_id, previous_author = node_id, None
                continue
            if operation not in {
                    'SOURCE_FIRST_PERSON_TOPIC', 'SOURCE_TRANSITIVE_SELF_TOPIC',
                    'SOURCE_FOCAL_TO_FIRST_PERSON', 'SOURCE_PERSONAL_EVALUATION',
                    'SOURCE_SCOPED_EXPRESSION_TO_FIRST_PERSON'}:
                reject()
            scope = scopes.get(node_id)
            if (operation == 'SOURCE_SCOPED_EXPRESSION_TO_FIRST_PERSON') != (scope is not None):
                reject()
            expression = original[slice(*scope.expression_scalar_span)] if scope else node.value
            author, viewpoint, body, topic_kind = arguments(node_id, expression)
            prefix = re.escape(author + viewpoint) + '[、，,]?'
            same_author = (previous_id is not None and previous_author == author
                           and positions[node_id] == positions[previous_id] + 1
                           and not re.search(r'[\r\n]', original[
                               spans[previous_id].source_end:spans[node_id].source_start]))
            # This only recognizes an already explicit adjacent author. It
            # never infers the first author, crosses a field/paragraph/newline,
            # or elides an explicit にとって value viewpoint.
            optional_prefix = '(?:' + prefix + ')?' if same_author and viewpoint == 'は' else prefix
            literal_emphasis = False
            if scope is None:
                pattern = optional_prefix + body
            else:
                premise = original[slice(*scope.scope_scalar_span)]
                if premise.startswith(author + 'は') and viewpoint == 'は':
                    optional_prefix = '(?:' + prefix + ')?'
                premise_pattern = anchor(premise) + '、'
                pattern = premise_pattern + optional_prefix + body
                # Existing simple-wish grammar may front its self topic, but
                # an explicit concession/reference keeps the premise first.
                referenced = any(ref.reference_node_id == node_id
                                 and scope.scope_scalar_span[0] <= ref.reference_scalar_span[0]
                                 and ref.reference_scalar_span[1] <= scope.scope_scalar_span[1]
                                 for ref in meaning.nominal_references)
                premise_first = scope.relation == 'SOURCE_EXPLICIT_CONCESSION' or referenced
                if topic_kind == 'literal':
                    # Scoped literal comparisons already have an explicit
                    # first person and complete predicate. Match the same
                    # authored clause order without granting topic omission.
                    pattern = (premise_pattern + prefix if premise_first
                               else prefix + premise_pattern) + body
                    if node.value.endswith(('！', '!')):
                        # Match the complete literal source only. Its words,
                        # subject, scope order and emphasis remain source-
                        # owned; no inferred wish or author omission follows.
                        pattern = anchor(node.value)
                        literal_emphasis = True
                elif topic_kind == 'wish' and not premise_first:
                    pattern = '(?:' + pattern + '|' + optional_prefix + premise_pattern + body + ')'
            if re.fullmatch(pattern, visible) is None:
                reject()
            previous_id, previous_author = node_id, None if literal_emphasis else author


def validate_piece_semantic_preservation(snapshot, plan, artifact, *, tier, requested_format):
    """P4 author-free review of actual private blocks and their source duties.

    No compiler/realizer/candidate acquisition is called. Source-scope validation
    is shared with admission; parser independence or general paraphrase review
    is not claimed. The closed arm allows no source-to-text lexical changes.
    """
    import hashlib
    import json
    from dataclasses import asdict
    from cocolon_meaning_experience_engine.piece_semantic_admission import (
        PieceSemanticPlanV1, PieceSemanticArtifactV1, PieceSemanticRealizationV1,
        PLAN_SCHEMA, ARTIFACT_SCHEMA, MEANING_VERSION, PROFILE,
        canonical, digest, require, validate_snapshot_self, source_nodes,
    )
    validate_snapshot_self(snapshot)
    require(type(plan) is PieceSemanticPlanV1, 'piece_semantic_plan_type')
    nodes = source_nodes(snapshot)
    expected_duties = [dict(duty_ref='duty:' + b.claim_ref, claim_refs=[b.claim_ref],
        node_refs=[b.node_ref], source_binding_refs=[b.source_binding_ref],
        required_scope_refs=json.loads(b.claim_json)['polarity']['scope_refs'],
        operation='KEEP_COMPLETE_SOURCE_CONTEXT') for b in snapshot.claim_bindings]
    groups = (tuple(n[0] for n in nodes[:-1]), (nodes[-1][0],))
    selection_refs = tuple('selection:' + '|'.join(r.alias_refs) for r in snapshot.source_selections)
    expected_plan = dict(schema_version=PLAN_SCHEMA, semantic_profile=PROFILE,
        snapshot_ref=snapshot.snapshot_ref, source_commitment=snapshot.source_commitment,
        graph_id='piece-graph:' + digest([snapshot.snapshot_ref,[n[0] for n in nodes]]),
        duties=expected_duties,block_node_ids=groups,selection_duties=selection_refs,
        eligible_formats=('short_essay',),intent='USER_OWNED_COCOLON_SHAPED')
    require(canonical(asdict(plan))==canonical(expected_plan), 'piece_semantic_plan_coverage')
    selected = choose_format(tier=tier,requested=requested_format,
                             eligible=plan.eligible_formats,recommended='short_essay')
    if artifact is None:
        return
    require(type(artifact) is PieceSemanticArtifactV1, 'piece_semantic_artifact_type')
    require((artifact.schema_version,artifact.semantic_profile,artifact.meaning_contract_version)==
            (ARTIFACT_SCHEMA,PROFILE,MEANING_VERSION),'piece_semantic_artifact_namespace')
    require(artifact.snapshot_ref==snapshot.snapshot_ref and artifact.plan_ref==plan.plan_ref
            and artifact.source_commitment==snapshot.source_commitment
            and artifact.format_type==selected and artifact.eligible_formats==plan.eligible_formats
            and artifact.retained_selection_refs==selection_refs,'piece_semantic_artifact_binding')
    require(type(artifact.body_blocks) is tuple and len(artifact.body_blocks)==len(groups)
            and all(type(b) is str and b for b in artifact.body_blocks),'piece_semantic_blocks')
    # Inspect the entire visible source interval, including every connective;
    # checking the six isolated predicates alone would miss an invented cause.
    locations = {}
    by_node = {n[0]:n for n in nodes}
    for bi, group in enumerate(groups):
        offset = 0
        for node_ref in group:
            _, field, start, end, source_text = by_node[node_ref]
            require(artifact.body_blocks[bi][offset:offset+len(source_text)]==source_text,
                    'piece_semantic_visible_scope')
            locations[node_ref]=(bi,offset,start)
            offset += len(source_text)
        require(offset==len(artifact.body_blocks[bi]),'piece_semantic_extra_visible_meaning')
    require(artifact.piece_text=='\n\n'.join(artifact.body_blocks)
            and artifact.piece_text_hash==hashlib.sha256(artifact.piece_text.encode()).hexdigest(),
            'piece_semantic_text_binding')
    expected_realizations=[]
    for b in snapshot.claim_bindings:
        bi,offset,base=locations[b.node_ref]
        a=offset+b.scalar_start-base;end=offset+b.scalar_end-base
        require(artifact.body_blocks[bi][a:end]==json.loads(b.claim_json)['text'],
                'piece_semantic_claim_visible_binding')
        expected_realizations.append(dict(claim_ref=b.claim_ref,duty_ref='duty:'+b.claim_ref,
            node_refs=[b.node_ref],source_binding_refs=[b.source_binding_ref],
            block_index=bi,visible_scalar_start=a,visible_scalar_end=end))
    require(all(type(r) is PieceSemanticRealizationV1 for r in artifact.claim_realizations)
            and canonical([asdict(r) for r in artifact.claim_realizations])==canonical(expected_realizations),
            'piece_semantic_visible_trace')
    _validate_text_envelope(artifact.piece_text,artifact.body_blocks,artifact.format_type)
    check_existing_detectors(artifact.piece_text)
