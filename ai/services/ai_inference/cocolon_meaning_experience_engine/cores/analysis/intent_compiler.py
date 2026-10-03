"""Analysis-owned observed graph from existing source-grounded semantic frames.

The shared semantic owner supplies evidence, polarity and modality, never an
Emlis response. Analysis decides its own node kinds, edges and missing scopes.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import re

from emlis_ai_grounded_observation_plan import (
    build_final_stage1_grounded_observation_plan,
    source_proven_performed_action_status,
)
from ...contracts import EvidenceRef
from ...emlis_answer_update import _WITHDRAWAL, _REPLACEMENT
from .source_adapter import (AnalysisSourceError, AnalysisSourceSet, commitment,
                            scoped_source_view, source_field_text)

NODE_KINDS = ('SCENE', 'ROLE', 'ATTENTION_OR_THOUGHT',
              'ACTION_OR_NONACTION', 'IMMEDIATE_RESULT_OR_AFTERMATH')


@dataclass(frozen=True, slots=True, repr=False)
class ObservedProposition:
    """Whole-clause grammatical interpretation, private and source-bound.

    Arguments retain written case particles; a ni-case is not guessed to be
    a recipient, location or cause. This is not anonymized telemetry.
    """
    actor: str
    arguments: tuple[tuple[str, str], ...]
    predicate_lemma: str
    polarity: str
    modality: str
    temporal_scope: str
    source_parts: tuple[tuple[str, int, int], ...]
    sequence_marker: str = ''


# A bounded verb/inflection inventory, not an input/topic-to-answer table.
# The finite operator and every argument must consume the complete clause.
_VERBS = (
    ('書く', '書', 'k'), ('調べる', '調べ', 'vowel'),
    ('試す', '試', 's'), ('見る', '見', 'vowel'),
    ('作る', '作', 'r'), ('残す', '残', 's'),
    ('記録する', '記録', 'suru'), ('メモする', 'メモ', 'suru'),
    ('続ける', '続け', 'vowel'),
)
# Kana-bearing nouns need a lexical proof: allowing arbitrary okurigana would
# misread 急いで / 読んで as a noun plus de-case and erase a second predicate.
# These are nominal lexemes, not triggers selecting a response or a topic.
_NOMINAL = r'(?:考え|思い|気持ち|学び|振り返り|取り組み|[一-鿿々]+|[ァ-ヴー]+)'
_ARGUMENT = re.compile(r'(?P<noun>' + _NOMINAL + r'(?:の' + _NOMINAL
                       + r')*)(?P<case>を|に|で|と)')


def _finite_predicates():
    forms = []
    for lemma, stem, group in _VERBS:
        i, a, past = {
            'k': (stem + 'き', stem + 'か', stem + 'いた'),
            's': (stem + 'し', stem + 'さ', stem + 'した'),
            'r': (stem + 'り', stem + 'ら', stem + 'った'),
            'vowel': (stem, stem, stem + 'た'),
            'suru': (stem + 'し', stem + 'し', stem + 'した'),
        }[group]
        for surface, polarity, modality, time in (
            (past, 'positive', 'fact', 'past'),
            (i + 'ました', 'positive', 'fact', 'past'),
            (a + 'なかった', 'negative', 'fact', 'past'),
            (i + 'ませんでした', 'negative', 'fact', 'past'),
            (i + 'たい', 'positive', 'wish', 'current_input'),
            (i + 'たいです', 'positive', 'wish', 'current_input'),
            (i + 'たくない', 'negative', 'wish', 'current_input'),
            (i + 'たくないです', 'negative', 'wish', 'current_input'),
            (i + 'たかった', 'positive', 'wish', 'past'),
            (i + 'たくなかった', 'negative', 'wish', 'past'),
        ):
            forms.append((surface, lemma, polarity, modality, time))
    return tuple(sorted(forms, key=lambda row: len(row[0]), reverse=True))


_FINITE_PREDICATES = _finite_predicates()
_SEQUENCE_PREFIX = re.compile(r'^(その後|それから)[、，\s]*')


def _proposition(value: str) -> ObservedProposition | None:
    sequence = _SEQUENCE_PREFIX.match(value)
    start = sequence.end() if sequence else 0
    marker = ({'その後': 'AFTER_PREVIOUS', 'それから': 'THEN_OR_ADDITION'}
              [sequence.group(1)] if sequence else '')
    subject = re.compile(r'(?:私|僕|わたし|自分)は').match(value, start)
    if subject is None:
        return None
    for finite, lemma, polarity, modality, time in _FINITE_PREDICATES:
        if not value.endswith(finite):
            continue
        end = len(value) - len(finite)
        offset, arguments = subject.end(), []
        parts = ([(marker, 0, start)] if sequence else [])
        parts.append(('SELF_TOPIC', start, offset))
        while offset < end:
            argument = _ARGUMENT.match(value, offset, end)
            if argument is None:
                break
            noun = argument['noun']
            if re.search(r'(?:った|いた|した|んだ|ない|たい)$', noun):
                break
            arguments.append((argument['case'], noun))
            parts.append(('CASE_' + argument['case'], offset, argument.end()))
            offset = argument.end()
        if offset != end or len({case for case, _ in arguments}) != len(arguments):
            continue
        parts.append(('FINITE_PREDICATE', end, len(value)))
        return ObservedProposition('SELF', tuple(arguments), lemma,
            polarity, modality, time, tuple(parts),
            marker)
    return None


@dataclass(frozen=True, slots=True, repr=False)
class ObservedNode:
    node_ref: str
    node_kind: str
    visible_label: str
    record_refs: tuple[str, ...]
    evidence_refs: tuple[EvidenceRef, ...]
    polarity: str
    modality: str
    temporal_scope: str
    proposition: ObservedProposition | None = None
    update_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True, repr=False)
class ObservedSourceUpdate:
    update_ref: str
    operation: str
    record_ref: str
    target_evidence: EvidenceRef
    answer_evidence_refs: tuple[EvidenceRef, ...]
    replacement_evidence_refs: tuple[EvidenceRef, ...]


@dataclass(frozen=True, slots=True, repr=False)
class ObservedEdge:
    edge_ref: str
    edge_kind: str
    endpoint_refs: tuple[str, str]
    evidence_refs: tuple[EvidenceRef, ...]


@dataclass(frozen=True, slots=True)
class UnknownGap:
    gap_ref: str
    between_node_refs: tuple[str, ...]
    missing_scope: str
    reason_code: str


@dataclass(frozen=True, slots=True, repr=False)
class ObservedGraph:
    nodes: tuple[ObservedNode, ...]
    edges: tuple[ObservedEdge, ...]
    unknown_gaps: tuple[UnknownGap, ...]
    source_updates: tuple[ObservedSourceUpdate, ...] = ()


def _node_kind(nucleus):
    frame = nucleus.semantic_frame
    codes = set(frame.attribute_codes)
    if nucleus.grounding_kind not in ('explicit', 'user_stated_relation'):
        return None
    if frame.actor != 'current_user':
        return None
    if source_proven_performed_action_status(nucleus):
        return 'ACTION_OR_NONACTION'
    if nucleus.kind == 'wish' and frame.modality == 'wish':
        return 'ATTENTION_OR_THOUGHT'
    if codes.intersection({'lexical:source_current_cognition',
            'lexical:source_self_appraisal', 'lexical:source_original_cognition'}):
        return 'ATTENTION_OR_THOUGHT'
    if (nucleus.kind == 'event' and frame.modality == 'fact' and
            'semantic_role:source_event' in codes):
        return 'SCENE'
    # Do not infer a role or a result from a generic reaction/change label.
    return None


def _fragment(source, nucleus):
    # Multi-span nuclei can contain unbounded relations. Keep them unknown in
    # this first consumer rather than stitching a new proposition together.
    if len(nucleus.source_span_ids) != 1:
        return None
    span_id = nucleus.source_span_ids[0]
    ref = next((r for r in source.evidence if r.source_span_id == span_id), None)
    span = next((s for s in source.spans if s.span_id == span_id), None)
    if ref is None or span is None:
        return None
    a, b = 0, len(span.raw_text)
    codes = nucleus.semantic_frame.attribute_codes
    ranges = [c for c in codes if c.startswith((
        'surface_scalar_range:', 'source_fragment_scalar_range:'))]
    if ranges:
        if len(ranges) != 1:
            return None
        prefix, raw_a, raw_b = ranges[0].split(':')
        witness = prefix.replace('_range', '_source') + ':normalized_raw_text'
        if witness not in codes:
            return None
        a, b = int(raw_a), int(raw_b)
        if not (0 <= a < b <= len(span.raw_text)):
            return None
    # Analysis preserves the whole finite host including negation/modality.
    # Quote, report and conditional scopes need additional route semantics;
    # their presence is explicit in unknown gaps rather than silently dropped.
    context = source.normalized.get(span.source_field, '')
    if re.search(r'[「」『』“”"?？]|(?:と言われ|と聞い|そうだ|なら|もし|かもしれ)', context):
        return None
    # An open reported speaker can carry across sentences and source fields.
    # First-person grammar alone cannot close that attribution scope.
    record_context = '\n'.join(str(source.normalized.get(field, ''))
                               for field in ('memo', 'memo_action'))
    if re.search(r'によると|いわく|曰く|の(?:話|感想|気持ち|説明|報告|発言)(?:です|だ|[。．.])',
                 record_context):
        return None
    value = span.raw_text[a:b].strip(' 、，。．')
    if not value:
        return None
    # current_user is the shared frame's default, not proof of its subject.
    # This initial cohort requires an explicit first-person finite host.
    if not re.match(r'^(?:(?:今日|昨日|その後|それから)[、\s]*)?(?:私は|僕は|わたしは|自分は)', value):
        return None
    # The source helper already proved a length-preserving normalization.
    field = source.envelope.raw_utf8[ref.field_utf8_start:ref.field_utf8_end].decode('utf-8')
    start, end = ref.scalar_start + a, ref.scalar_start + b
    literal = field[start:end]
    if literal.replace('\u3000', ' ').strip() != span.raw_text[a:b].strip():
        raise AnalysisSourceError('analysis_fragment_evidence_mismatch')
    evidence = replace(ref,
        evidence_id='analysis-evidence:' + commitment([ref.source_envelope_id,
            ref.field_path, start, end])[7:],
        scalar_start=start, scalar_end=end,
        utf8_start=ref.field_utf8_start + len(field[:start].encode('utf-8')),
        utf8_end=ref.field_utf8_start + len(field[:end].encode('utf-8')),
        literal_sha256=hashlib.sha256(literal.encode('utf-8')).hexdigest())
    return value, evidence


def _self_propositions(source, *, require_complete=False, plan=None):
    """Read existing grammatical claims, retaining original field coordinates.

    An ordinary answer must stand on its own. Unread text may qualify, retract
    or correct the apparent claim, so a parsed fragment is not enough.
    """
    if plan is None:
        plan = build_final_stage1_grounded_observation_plan(
            source.normalized, evidence_spans=source.spans)
    if plan.input_profile.material_quality == 'safety_routed':
        raise AnalysisSourceError('analysis_separate_safety_required')
    claims = []
    for nucleus in plan.nuclei:
        if (nucleus.grounding_kind not in ('explicit', 'user_stated_relation')
                or nucleus.semantic_frame.actor != 'current_user'):
            continue
        fragment = _fragment(source, nucleus)
        proposition = _proposition(fragment[0]) if fragment else None
        if proposition is not None:
            claims.append((proposition, fragment[1]))
    if require_complete:
        raw = source_field_text(source, 'memo')
        covered = set()
        for _, evidence in claims:
            if evidence.field_path == 'memo':
                covered.update(range(evidence.scalar_start, evidence.scalar_end))
        # Deliberately not all punctuation: question marks, quotes and other
        # unparsed operators cannot be treated as harmless sentence separators.
        if not claims or any(i not in covered and char not in ' \t\r\n\u3000。．.'
                             for i, char in enumerate(raw)):
            raise AnalysisSourceError('analysis_supplement_interpretation_pending')
    return tuple(claims)


def _explicit_order_pairs(source, plan, withdrawn):
    """Bind a written connective to adjacent complete clauses in one field.

    The shared plan establishes the claims, while Analysis owns this relation.
    Never bridge an unread clause, another field/source, or a removed target.
    A current wish is not proof that a later action occurred.
    """
    whole = {(r.field_path, r.scalar_start, r.scalar_end) for r in source.evidence}
    claims = {e.evidence_id: (p, e) for p, e in _self_propositions(source, plan=plan)
              if e.source_span_id not in withdrawn
              and (e.field_path, e.scalar_start, e.scalar_end) in whole}
    ordered = sorted(claims.values(), key=lambda item:
                     (item[1].field_path, item[1].scalar_start, item[1].scalar_end))
    pairs = []
    for (left, a), (right, b) in zip(ordered, ordered[1:]):
        if (a.field_path != b.field_path or a.scalar_end >= b.scalar_start
                or right.sequence_marker not in {'AFTER_PREVIOUS', 'THEN_OR_ADDITION'}
                or (left.modality, right.modality) != ('fact', 'fact')
                or (left.temporal_scope, right.temporal_scope) != ('past', 'past')):
            continue
        separator = source_field_text(source, a.field_path)[a.scalar_end:b.scalar_start]
        if (re.fullmatch(r'[。．.\s]+', separator)
                and any(char in separator for char in '。．.\r\n')):
            pairs.append((a, b))
    return tuple(pairs)


def _admit_ordinary_supplement(answer, original):
    claims = _self_propositions(answer, require_complete=True)
    earlier = [p for p, _ in _self_propositions(original)]
    for current, _ in claims:
        for previous in earlier:
            # Without an explicit correction target, do not choose between
            # opposing descriptions of the same possible action/wish. Missing
            # arguments do not prove a different occasion or a different object.
            a, b = dict(current.arguments), dict(previous.arguments)
            compatible_arguments = all(a[case] == b[case] for case in a.keys() & b.keys())
            if (current.actor == previous.actor
                    and current.predicate_lemma == previous.predicate_lemma
                    and current.modality == previous.modality
                    and current.temporal_scope == previous.temporal_scope
                    and current.polarity != previous.polarity
                    and compatible_arguments):
                raise AnalysisSourceError('analysis_supplement_interpretation_pending')
        earlier.append(current)


def _active_sources(source_set):
    """Apply whole-clause corrections to occurrences before period grouping."""
    originals = {s.record_ref: s for s in source_set.sources
                 if s.envelope.source_role == 'ORIGINAL_INPUT'}
    excluded, views, updates, replacement_updates = {}, [], [], {}
    for answer in source_set.sources:
        if answer.envelope.source_role != 'SUPPLEMENTAL_ANSWER':
            views.append(answer)
            continue
        raw = source_field_text(answer, 'memo')
        text = raw.strip().rstrip('。．.')
        replacement, withdrawal = _REPLACEMENT.fullmatch(text), _WITHDRAWAL.fullmatch(text)
        match = replacement or withdrawal
        original = originals.get(answer.record_ref)
        if original is None:
            raise AnalysisSourceError('analysis_supplement_parent_missing')
        if match is None:
            _admit_ordinary_supplement(answer, original)
            views.append(answer)
            continue
        old = match['old'].rstrip('。．.')
        targets = []
        for ref in original.evidence:
            field = source_field_text(original, ref.field_path)
            literal = field[ref.scalar_start:ref.scalar_end]
            prefix, suffix = field[:ref.scalar_start].rstrip(), field[ref.scalar_end:].lstrip()
            if (literal.replace('\u3000', ' ').strip().rstrip('。．.') == old
                    and (not prefix or prefix[-1] in '。．.!！?？')
                    and (not suffix or suffix[0] in '。．.!！?？')):
                targets.append(ref)
        if len(targets) != 1:
            raise AnalysisSourceError('analysis_correction_target_unresolved')
        target = targets[0]
        original_plan = build_final_stage1_grounded_observation_plan(
            original.normalized, evidence_spans=original.spans)
        target_is_self_claim = False
        for nucleus in original_plan.nuclei:
            if (nucleus.source_span_ids != (target.source_span_id,)
                    or nucleus.grounding_kind not in ('explicit', 'user_stated_relation')
                    or nucleus.semantic_frame.actor != 'current_user'):
                continue
            fragment = _fragment(original, nucleus)
            if (fragment and (fragment[1].scalar_start, fragment[1].scalar_end) ==
                    (target.scalar_start, target.scalar_end)
                    and (_proposition(fragment[0]) or _node_kind(nucleus))):
                target_is_self_claim = True
        # Quote location alone cannot prove that a reported first-person
        # clause belongs to the current user. Preserve its original scope.
        if not target_is_self_claim:
            raise AnalysisSourceError('analysis_correction_target_unresolved')
        excluded.setdefault(original.envelope.envelope_id, set()).add(target.source_span_id)
        view = None
        if replacement:
            leading = len(raw) - len(raw.lstrip())
            view = scoped_source_view(answer, leading + match.start('new'),
                                      leading + match.end('new'))
            views.append(view)
        update = ObservedSourceUpdate('analysis-update:' + commitment([
            answer.envelope.envelope_id, target.evidence_id,
            'REVISE' if replacement else 'WITHDRAW'])[7:],
            'REVISE' if replacement else 'WITHDRAW', answer.record_ref,
            target, answer.evidence, view.evidence if view else ())
        updates.append(update)
        if view:
            replacement_updates[view.envelope.envelope_id] = update.update_ref
    return tuple(views), excluded, tuple(updates), replacement_updates


def compile_observed_graph(source_set: AnalysisSourceSet) -> ObservedGraph:
    active_sources, excluded, updates, replacement_updates = _active_sources(source_set)
    nodes, edges, gaps = [], [], []
    unresolved_records = set()
    by_signature, occurrences, record_orders = {}, {}, {}
    for source in active_sources:
        plan = build_final_stage1_grounded_observation_plan(
            source.normalized, evidence_spans=source.spans)
        if plan.input_profile.material_quality == 'safety_routed':
            raise AnalysisSourceError('analysis_separate_safety_required')
        order_pairs = _explicit_order_pairs(source, plan,
            excluded.get(source.envelope.envelope_id, set()))
        ordered_evidence = {e.evidence_id for pair in order_pairs for e in pair}
        admitted, by_evidence, unresolved = {}, {}, False
        for nucleus in plan.nuclei:
            if set(nucleus.source_span_ids) & excluded.get(source.envelope.envelope_id, set()):
                continue
            explicit = (nucleus.grounding_kind in ('explicit', 'user_stated_relation')
                        and nucleus.semantic_frame.actor == 'current_user')
            fragment = _fragment(source, nucleus) if explicit else None
            proposition = _proposition(fragment[0]) if fragment else None
            kind = ('ATTENTION_OR_THOUGHT' if proposition.modality == 'wish'
                    else 'ACTION_OR_NONACTION') if proposition else _node_kind(nucleus)
            if not kind:
                fragment = None
            if fragment is None:
                if any(s.source_field in ('memo', 'memo_action') and
                       s.span_id in nucleus.source_span_ids for s in source.spans):
                    unresolved = True
                continue
            label, evidence = fragment
            frame = nucleus.semantic_frame
            polarity, modality, time = ((proposition.polarity, proposition.modality,
                proposition.temporal_scope) if proposition else
                (frame.polarity, frame.modality, frame.time_scope))
            update_ref = replacement_updates.get(source.envelope.envelope_id)
            node_updates = (update_ref,) if update_ref else ()
            # Exact grammatical equivalence, not synonymous/topic matching.
            # A polite restatement or reordered cases is still one claim;
            # preserve each source witness without inventing a cooccurrence.
            meaning = ((proposition.actor, tuple(sorted(proposition.arguments)),
                        proposition.predicate_lemma) if proposition else label)
            # A sequence is about occurrences: collapsing A -> B -> A by
            # proposition would create a false cycle or erase repeated A.
            # Ordinary, unqualified claims retain their existing aggregation.
            occurrence_scope = (evidence.evidence_id if evidence.evidence_id in ordered_evidence
                or (proposition and proposition.sequence_marker) else None)
            signature = (kind, meaning, polarity, modality, time, occurrence_scope)
            index = by_signature.get(signature)
            if index is None:
                index = len(nodes)
                by_signature[signature] = index
                nodes.append(ObservedNode('n' + str(index + 1), kind, label,
                    (source.record_ref,), (evidence,), polarity,
                    modality, time, proposition, node_updates))
            else:
                old = nodes[index]
                nodes[index] = replace(old,
                    record_refs=tuple(dict.fromkeys((*old.record_refs, source.record_ref))),
                    evidence_refs=tuple(dict.fromkeys((*old.evidence_refs, evidence))),
                    update_refs=tuple(dict.fromkeys((*old.update_refs, *node_updates))))
            node = nodes[index]
            admitted[nucleus.nucleus_id] = node.node_ref
            by_evidence[evidence.evidence_id] = node.node_ref
            occurrences.setdefault(source.record_ref, set()).add(node.node_ref)
        # The whole replacement, not just a convenient sub-clause, must be
        # interpreted. Otherwise no old result can be returned as current.
        if source.envelope.envelope_id in replacement_updates and (not admitted or unresolved):
            raise AnalysisSourceError('analysis_correction_replacement_unsupported')
        for a, b in order_pairs:
            endpoints = (by_evidence.get(a.evidence_id), by_evidence.get(b.evidence_id))
            if all(endpoints) and endpoints[0] != endpoints[1]:
                edges.append(ObservedEdge('e' + str(len(edges) + 1),
                    'OBSERVED_ORDER', endpoints, (a, b)))
                record_orders.setdefault(source.record_ref, set()).add(endpoints)
        if unresolved or (not admitted and any(
                s.source_field in ('memo', 'memo_action') and
                s.span_id not in excluded.get(source.envelope.envelope_id, set())
                for s in source.spans)):
            unresolved_records.add(source.record_ref)
    # Original and supplemental content are one occasion. Determine gaps only
    # after both have contributed, not independently for each source child.
    for record_ref, ids in occurrences.items():
        anchors = tuple(n.node_ref for n in nodes if n.node_ref in ids)
        present = {n.node_kind for n in nodes if n.node_ref in ids}
        for kind in NODE_KINDS:
            if kind not in present:
                gaps.append(UnknownGap('g' + str(len(gaps) + 1), anchors[:1],
                    kind, 'NOT_ESTABLISHED_FROM_SOURCE'))
        if record_ref in unresolved_records:
            gaps.append(UnknownGap('g' + str(len(gaps) + 1), anchors[:1],
                'SOURCE_SCOPE', 'UNSUPPORTED_OR_UNCERTAIN_SOURCE_SCOPE'))
        known_pairs = record_orders.get(record_ref, set())
        for pair in zip(anchors, anchors[1:]):
            if pair not in known_pairs and pair[::-1] not in known_pairs:
                gaps.append(UnknownGap('g' + str(len(gaps) + 1), pair,
                    'ROUTE_CONNECTION', 'ONLY_EXPLICIT_ORDER_IS_SHOWN'))
        for node in nodes:
            if (node.node_ref in ids and node.proposition
                    and node.proposition.sequence_marker
                    and not any(pair[1] == node.node_ref for pair in known_pairs)):
                gaps.append(UnknownGap('g' + str(len(gaps) + 1), (node.node_ref,),
                    'ROUTE_CONNECTION', 'EXPLICIT_PREDECESSOR_NOT_ESTABLISHED'))
    if nodes and unresolved_records - occurrences.keys():
        gaps.append(UnknownGap('g' + str(len(gaps) + 1), (nodes[0].node_ref,),
            'SOURCE_SCOPE', 'UNSUPPORTED_OR_UNCERTAIN_SOURCE_SCOPE'))
    # A supplemental answer shares its original's occasion. Two fields or two
    # answers from one record therefore never turn into a repeated pattern.
    for i, left in enumerate(nodes):
        for right in nodes[i + 1:]:
            together = [ref for ref, ids in occurrences.items()
                        if {left.node_ref, right.node_ref} <= ids]
            if len(together) < 2:
                continue
            supporting_envelopes = {s.envelope.envelope_id for s in source_set.sources
                                    if s.record_ref in together}
            refs = tuple(dict.fromkeys(r for r in (*left.evidence_refs, *right.evidence_refs)
                                      if r.source_envelope_id in supporting_envelopes))
            edges.append(ObservedEdge('e' + str(len(edges) + 1),
                'REPEATED_COOCCURRENCE', (left.node_ref, right.node_ref), refs))
    return ObservedGraph(tuple(nodes), tuple(edges), tuple(gaps), updates)
