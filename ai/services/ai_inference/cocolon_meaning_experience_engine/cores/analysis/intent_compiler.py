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
from .source_adapter import AnalysisSourceError, AnalysisSourceSet, commitment

NODE_KINDS = ('SCENE', 'ROLE', 'ATTENTION_OR_THOUGHT',
              'ACTION_OR_NONACTION', 'IMMEDIATE_RESULT_OR_AFTERMATH')


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


def compile_observed_graph(source_set: AnalysisSourceSet) -> ObservedGraph:
    # Binding a permitted answer is not equivalent to interpreting its effect
    # on the original. Until correction/withdrawal semantics are connected,
    # never show a possibly withdrawn original as an established observation.
    if any(s.envelope.source_role == 'SUPPLEMENTAL_ANSWER' for s in source_set.sources):
        raise AnalysisSourceError('analysis_supplement_interpretation_pending')
    nodes, edges, gaps = [], [], []
    unresolved_sources = 0
    by_signature, occurrences = {}, {}
    for source in source_set.sources:
        plan = build_final_stage1_grounded_observation_plan(
            source.normalized, evidence_spans=source.spans)
        if plan.input_profile.material_quality == 'safety_routed':
            raise AnalysisSourceError('analysis_separate_safety_required')
        admitted, unresolved = {}, False
        for nucleus in plan.nuclei:
            kind = _node_kind(nucleus)
            fragment = _fragment(source, nucleus) if kind else None
            if fragment is None:
                if any(s.source_field in ('memo', 'memo_action') and
                       s.span_id in nucleus.source_span_ids for s in source.spans):
                    unresolved = True
                continue
            label, evidence = fragment
            frame = nucleus.semantic_frame
            signature = (kind, label, frame.polarity, frame.modality, frame.time_scope)
            index = by_signature.get(signature)
            if index is None:
                index = len(nodes)
                by_signature[signature] = index
                nodes.append(ObservedNode('n' + str(index + 1), kind, label,
                    (source.record_ref,), (evidence,), frame.polarity,
                    frame.modality, frame.time_scope))
            else:
                old = nodes[index]
                nodes[index] = replace(old,
                    record_refs=tuple(dict.fromkeys((*old.record_refs, source.record_ref))),
                    evidence_refs=tuple(dict.fromkeys((*old.evidence_refs, evidence))))
            node = nodes[index]
            admitted[nucleus.nucleus_id] = node.node_ref
            occurrences.setdefault(source.record_ref, set()).add(node.node_ref)
        for relation in plan.relations:
            endpoints = (admitted.get(relation.from_nucleus_id),
                         admitted.get(relation.to_nucleus_id))
            refs = tuple(r for r in source.evidence
                         if r.source_span_id in relation.source_span_ids)
            if (relation.type == 'temporal_before_after' and
                    relation.grounding_kind == 'user_stated_relation' and
                    all(endpoints) and endpoints[0] != endpoints[1] and refs and
                    {r.source_span_id for r in refs} == set(relation.source_span_ids)):
                # Requires an explicit temporal marker in the same source;
                # order in a list or in the period is not an order assertion.
                marker = any(re.search(r'その後|それから|した後|終えてから',
                    source.envelope.raw_utf8[r.utf8_start:r.utf8_end].decode('utf-8'))
                    for r in refs)
                if marker:
                    edges.append(ObservedEdge('e' + str(len(edges) + 1),
                        'OBSERVED_ORDER', endpoints, refs))
        if admitted:
            anchors = tuple(dict.fromkeys(admitted.values()))
            present = {n.node_kind for n in nodes if n.node_ref in anchors}
            for kind in NODE_KINDS:
                if kind not in present:
                    gaps.append(UnknownGap('g' + str(len(gaps) + 1),
                        anchors[:1], kind, 'NOT_ESTABLISHED_FROM_SOURCE'))
            if unresolved:
                gaps.append(UnknownGap('g' + str(len(gaps) + 1), anchors[:1],
                    'SOURCE_SCOPE', 'UNSUPPORTED_OR_UNCERTAIN_SOURCE_SCOPE'))
            if len(anchors) > 1:
                gaps.append(UnknownGap('g' + str(len(gaps) + 1), anchors[:2],
                    'ROUTE_CONNECTION', 'ONLY_EXPLICIT_ORDER_IS_SHOWN'))
        elif any(s.source_field in ('memo', 'memo_action') for s in source.spans):
            unresolved_sources += 1
    if nodes and unresolved_sources:
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
    return ObservedGraph(tuple(nodes), tuple(edges), tuple(gaps))
