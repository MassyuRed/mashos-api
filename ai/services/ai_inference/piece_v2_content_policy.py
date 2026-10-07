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
ENVELOPES = {'short_essay': (24, 420, 6), 'quote': (12, 120, 2),
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
    lo, hi, sentences = ENVELOPES[payload['format_type']]
    n = len(re.sub(r'\s', '', text))
    if not lo <= n <= hi or len(re.findall(r'[。！？!?]', text)) > sentences:
        raise unavailable('content_envelope')
    if any('\n' in b for b in payload['body_blocks']):
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
    from piece_v2_contract import validate_piece_text_binding
    from piece_v2_generation import _FOCUS
    from piece_v2_expression import _SELF_TOPIC, _WISH_END
    from cocolon_meaning_experience_engine.piece_source import (
        PieceSourceMeaning, _direct_transitive_expression, _PERSON_NAME_LEFT_BOUNDARY,
        piece_public_role_aliases, validate_piece_saved_fields,
        validate_piece_nominal_references, validate_piece_personal_evaluations,
        validate_piece_expression_scopes,
    )
    from cocolon_meaning_experience_engine.piece_v1c import PieceArtifact, PieceArtifactPlan

    def reject():
        raise unavailable('piece_meaning_not_preserved')

    if (type(meaning) is not PieceSourceMeaning or type(plan) is not PieceArtifactPlan
            or type(artifact) is not PieceArtifact):
        reject()
    validate_piece_saved_fields(meaning)
    validate_piece_nominal_references(meaning)
    validate_piece_personal_evaluations(meaning)
    validate_piece_expression_scopes(meaning)
    validate_piece_text_binding(artifact.content_payload(), artifact.piece_text,
                                artifact.piece_text_hash)
    original = meaning.envelope.raw_utf8.decode('utf-8')
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
    if set(spans) != set(ids) or len(meaning.evidence) != len(nodes):
        reject()
    for node, evidence in zip(nodes, meaning.evidence, strict=True):
        span = spans[node.node_id]
        if (original[span.source_start:span.source_end] != node.value
                or node.evidence_ids != (evidence.evidence_id,)
                or meaning.envelope.raw_utf8[evidence.utf8_start:evidence.utf8_end]
                != node.value.encode('utf-8')):
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
        frame = evaluations.get(node_id)
        if frame is not None:
            author, predicate, target = (original[a:b] for a, b in frame.scalar_parts)
            finite = predicate[:-1] + frame.copula if predicate.endswith('な') else predicate
            viewpoint = 'にとって' if frame.construction == 'にとって' else 'は'
            return author, viewpoint, anchor(target) + 'が' + anchor(finite) + '。'
        focal = _FOCUS.fullmatch(expression)
        direct = _direct_transitive_expression(expression) if focal is None else None
        if focal is not None or direct is not None:
            parsed = focal if focal is not None else direct
            target = parsed['object'].lstrip('、，,') if focal is not None else parsed['object']
            return parsed['speaker'], 'は', anchor(target) + 'を' + anchor(parsed['predicate']) + '。'
        topic = _SELF_TOPIC.fullmatch(expression)
        if topic is None or not _WISH_END.search(topic['body']):
            reject()
        return topic['speaker'], 'は', anchor(topic['body']) + '。'

    for group, block in zip(plan.block_node_ids, artifact.body_blocks, strict=True):
        sentences = re.findall(r'[^。！？!?]+[。！？!?]', block)
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
            author, viewpoint, body = arguments(node_id, expression)
            prefix = re.escape(author + viewpoint) + '[、，,]?'
            same_author = (previous_id is not None and previous_author == author
                           and positions[node_id] == positions[previous_id] + 1
                           and not re.search(r'[\r\n]', original[
                               spans[previous_id].source_end:spans[node_id].source_start]))
            # This only recognizes an already explicit adjacent author. It
            # never infers the first author, crosses a field/paragraph/newline,
            # or elides an explicit にとって value viewpoint.
            optional_prefix = '(?:' + prefix + ')?' if same_author and viewpoint == 'は' else prefix
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
                simple = (node_id not in evaluations and _FOCUS.fullmatch(expression) is None
                          and _direct_transitive_expression(expression) is None)
                if simple and scope.relation != 'SOURCE_EXPLICIT_CONCESSION' and not referenced:
                    pattern = '(?:' + pattern + '|' + optional_prefix + premise_pattern + body + ')'
            if re.fullmatch(pattern, visible) is None:
                reject()
            previous_id, previous_author = node_id, author
