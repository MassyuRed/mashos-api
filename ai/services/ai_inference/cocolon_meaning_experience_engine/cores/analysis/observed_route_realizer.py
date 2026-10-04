"""Owner-facing projections and private previews of one observed artifact.

Only safe_projection reconstructs labels from complete grammatical parts.
Private previews retain source clauses and must never be returned by an API.
Owner authorization, retention and deletion checks remain the caller's duty.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from uuid import uuid4

from ...contracts import EngineStatus
from .intent_compiler import (ObservedGraph, compile_observed_graph, _proposition,
                              _CANONICAL_CONTENT, _RESULT_STEMS, _CHANGE_PAST,
                              _FEELING_PAST, _te_action_proposition, _burden_predicate)
from .source_adapter import (
    AnalysisObservedMapRequest, AnalysisSourceError, AnalysisSourceMember,
    freeze_analysis_sources,
)

LABELS = {'SCENE': '場面', 'ROLE': '役割',
          'ATTENTION_OR_THOUGHT': '考え・注意',
          'ACTION_OR_NONACTION': '行動・非行動',
          'IMMEDIATE_RESULT_OR_AFTERMATH': '結果・余韻',
          'SOURCE_SCOPE': 'まだ読み取れていない内容',
          'ROUTE_CONNECTION': '段階同士のつながり'}

CONFLICT_LABEL = '同じ記録に肯定と否定の記述があります。同じ機会のことかは確定していません。'
BURDEN_LABELS = {predicate: 'この希望と対比して、' + predicate
    + 'と記述されています。原因や続いている期間は確定していません。'
    for predicate in ('つらい', '苦しい')}


def _te_order_context(node, graph):
    """A dependent te fragment remains bound to its complete past episode."""
    for edge in graph.edges:
        if (edge.edge_kind != 'OBSERVED_ORDER' or edge.endpoint_refs[0] != node.node_ref
                or len(edge.evidence_refs) != 3):
            continue
        right = next((n for n in graph.nodes if n.node_ref == edge.endpoint_refs[1]), None)
        a, b, whole = edge.evidence_refs
        if (right and right.proposition
                and (right.proposition.result_state, right.modality) in {
                    ('BOUNDED_CHANGE', 'fact'), ('PAST_FEELING', 'feeling')}
                and right.node_kind == 'IMMEDIATE_RESULT_OR_AFTERMATH'
                and right.temporal_scope == 'past'
                and a in node.evidence_refs and b in right.evidence_refs
                and len({(e.source_envelope_id, e.source_span_id, e.field_path)
                         for e in (a, b, whole)}) == 1
                and whole.scalar_start == a.scalar_start < a.scalar_end < b.scalar_start
                and b.scalar_end == whole.scalar_end):
            return True
    return False


def _safe_label(node, graph):
    parts = node.proposition
    replay = _proposition(node.visible_label)
    if parts and parts.dependent_form == 'TE_BEFORE_PAST_CHANGE' and _te_order_context(node, graph):
        dependent = _te_action_proposition(node.visible_label)
        if dependent is not None:
            replay = replace(dependent, temporal_scope='past', dependent_form='TE_BEFORE_PAST_CHANGE')
    # Replay the complete typed interpretation; never wrap an arbitrary raw
    # clause in a label and call it a safe projection.
    if (parts is None or parts != replay
            or (parts.polarity, parts.modality, parts.temporal_scope) !=
               (node.polarity, node.modality, node.temporal_scope)):
        raise AnalysisSourceError('analysis_safe_surface_unavailable')
    if parts.result_state == 'NOT_YET':
        phrase = ''.join(noun + case for case, noun in parts.arguments)
        return ('まだ' + phrase + _RESULT_STEMS[parts.predicate_lemma]
                + 'っていない（この記述時点）')
    if parts.result_state == 'BOUNDED_CHANGE':
        phrase = ''.join(noun + case for case, noun in parts.arguments)
        return phrase + _CHANGE_PAST[parts.predicate_lemma] + '（記録された変化）'
    if parts.result_state == 'PAST_FEELING':
        return _FEELING_PAST[parts.predicate_lemma] + '（記録された気持ち）'
    if parts.scene_state == 'PAST_PRESENCE':
        phrase = ''.join(noun + case for case, noun in parts.arguments)
        return phrase + ('いた' if parts.polarity == 'positive' else 'いなかった') + '（記録された場面）'
    if parts.role_state == 'PAST_RESPONSIBILITY':
        phrase = ''.join(noun + case for case, noun in parts.arguments)
        return phrase + ('担当した' if parts.polarity == 'positive' else '担当しなかった') + '（記録された担当）'
    if parts.possible_content is not None:
        content = parts.possible_content
        phrase = ''.join(noun + case for case, noun in content.arguments)
        phrase += _CANONICAL_CONTENT[(content.predicate_lemma, content.polarity, content.temporal_scope)]
        return phrase + 'かもしれないと' + parts.predicate_lemma + '（この記述時点の考え）'
    phrase = ''.join(noun + case for case, noun in parts.arguments) + parts.predicate_lemma
    if parts.sequence_marker:
        phrase = {'AFTER_PREVIOUS': 'その後：',
                  'THEN_OR_ADDITION': 'それから：'}[parts.sequence_marker] + phrase
    if parts.relative_day:
        phrase = 'この記述時点の' + {'TODAY': '今日', 'YESTERDAY': '昨日'}[parts.relative_day] + '：' + phrase
    if parts.modality == 'wish':
        label = phrase + ('ことへの希望' if parts.polarity == 'positive'
                          else 'ことを望まない')
        return label + ('（当時）' if parts.temporal_scope == 'past' else '')
    return phrase + ('（実行済み）' if parts.polarity == 'positive'
                     else '（行わなかった）')


@dataclass(frozen=True, slots=True, repr=False)
class ObservedSelfStructureMap:
    artifact_id: str
    artifact_version: int
    owner_scope: str
    source_set_ref: str
    period: tuple[str, str]
    graph: ObservedGraph
    source_members: tuple[AnalysisSourceMember, ...]
    artifact_kind: str = 'ANALYSIS_OBSERVED_SELF_STRUCTURE_MAP'
    epistemic_partition: str = 'OBSERVED'
    wire_kind: str = 'watashi.map.v2'

    @property
    def reference(self):
        return self.artifact_id + '@' + str(self.artifact_version)

    def _conflict_badges(self):
        return [{'conflict_ref': c.conflict_ref, 'target_refs': list(c.target_refs),
                 'visible_label': CONFLICT_LABEL} for c in self.graph.conflicts]

    def _unknown_gap_projection(self):
        # Several records may share a node and the same missing scope. Keep
        # every private gap, but show that exact target/scope/reason once.
        # Preserve the first gap identity and order; labels alone are not keys.
        gaps, seen = [], set()
        for gap in self.graph.unknown_gaps:
            key = (gap.between_node_refs, gap.missing_scope, gap.reason_code)
            if key in seen:
                continue
            seen.add(key)
            gaps.append({'gap_ref': gap.gap_ref,
                'between_node_refs': list(gap.between_node_refs),
                'visible_label': LABELS[gap.missing_scope] + 'は、この記録からは確定していません。'})
        return gaps

    def _annotation_badges(self):
        badges = []
        nodes = {n.node_ref: n for n in self.graph.nodes}
        for claim in self.graph.annotations:
            target = nodes.get(claim.target_ref)
            p = target.proposition if target else None
            if (p is None or target.node_kind != 'ATTENTION_OR_THOUGHT'
                    or (p.actor, p.polarity, p.modality, p.temporal_scope) !=
                       ('SELF', 'positive', 'wish', 'current_input')
                    or claim.kind != 'BURDEN' or claim.annotation_state != 'SOURCE_EXPLICIT_ANNOTATION'
                    or claim.predicate_lemma not in BURDEN_LABELS or not claim.source_labels
                    or any(_burden_predicate(label) != claim.predicate_lemma for label in claim.source_labels)
                    or not claim.evidence_refs or len(claim.evidence_refs) % 3):
                raise AnalysisSourceError('analysis_safe_surface_unavailable')
            for i in range(0, len(claim.evidence_refs), 3):
                left, right, whole = claim.evidence_refs[i:i + 3]
                if (left not in target.evidence_refs
                        or len({(e.source_envelope_id, e.source_span_id, e.field_path)
                                for e in (left, right, whole)}) != 1
                        or not (whole.scalar_start == left.scalar_start < left.scalar_end
                                < right.scalar_start < right.scalar_end == whole.scalar_end)):
                    raise AnalysisSourceError('analysis_safe_surface_unavailable')
            badges.append({'annotation_ref': claim.annotation_ref, 'target_ref': claim.target_ref,
                'kind': claim.kind, 'visible_label': BURDEN_LABELS[claim.predicate_lemma]})
        return badges

    def private_visual_preview(self, *, authenticated_owner_scope: str) -> dict:
        # Pure second-line owner binding, not a substitute for lifecycle auth,
        # tier, retention, deletion and audience policy in the future API.
        if authenticated_owner_scope != self.owner_scope:
            raise AnalysisSourceError('analysis_projection_owner_mismatch')
        return {
            'schema_version': 'cocolon.cmee.analysis_private_preview.v1',
            'wire_kind': 'watashi.map.v2.private-preview', 'projection_of': self.reference,
            'artifact_version': self.artifact_version,
            'period_label': ' ～ '.join(self.period),
            'period_comparison': {'state': 'NO_PREVIOUS', 'reason_codes': [],
                                  'safe_change_kinds': []},
            'nodes': [{'node_ref': n.node_ref, 'node_kind': n.node_kind,
                'visible_label': n.visible_label,
                'evidence_badge_count': len(n.record_refs)} for n in self.graph.nodes],
            'edges': [dict({'edge_ref': e.edge_ref, 'edge_kind': e.edge_kind,
                'visible_label': ('記録内に書かれた順序' if e.edge_kind == 'OBSERVED_ORDER'
                                  else '複数の記録で一緒に現れた内容')},
                **({'from_ref': e.endpoint_refs[0], 'to_ref': e.endpoint_refs[1]}
                   if e.edge_kind == 'OBSERVED_ORDER'
                   else {'endpoint_refs': list(e.endpoint_refs)})) for e in self.graph.edges],
            'annotation_badges': self._annotation_badges(),
            'unknown_gaps': self._unknown_gap_projection(),
            'conflict_badges': self._conflict_badges(),
            'accessibility_linear_order': [n.node_ref for n in self.graph.nodes],
        }

    def private_text_preview(self, *, authenticated_owner_scope: str) -> dict:
        visual = self.private_visual_preview(authenticated_owner_scope=authenticated_owner_scope)
        return self._text_from_visual(visual)

    def safe_projection(self, *, authenticated_owner_scope: str) -> dict:
        """Canonical SELF_ONLY product DTO, not anonymized sharing/telemetry.

        A matching scope string is a second-line binding check, not proof of
        authentication. The future API must recheck its live owner lifecycle.
        No source body, private identifier, locator or commitment is copied.
        """
        if authenticated_owner_scope != self.owner_scope:
            raise AnalysisSourceError('analysis_projection_owner_mismatch')
        labels = {node.node_ref: _safe_label(node, self.graph) for node in self.graph.nodes}
        return {
            'schema_version': 'cocolon.cmee.analysis_watashi_map_safe_projection.v1alpha1',
            'wire_kind': 'watashi.map.v2', 'projection_of': self.reference,
            'artifact_version': self.artifact_version,
            'period_label': ' ～ '.join(self.period),
            'period_comparison': {'state': 'NO_PREVIOUS', 'reason_codes': [],
                                  'safe_change_kinds': []},
            'nodes': [{'node_ref': n.node_ref, 'node_kind': n.node_kind,
                'visible_label': labels[n.node_ref],
                'evidence_badge_count': len(n.record_refs)} for n in self.graph.nodes],
            'edges': [dict({'edge_ref': e.edge_ref, 'edge_kind': e.edge_kind,
                'visible_label': ('記録内に書かれた順序' if e.edge_kind == 'OBSERVED_ORDER'
                                  else '複数の記録で一緒に現れた内容')},
                **({'from_ref': e.endpoint_refs[0], 'to_ref': e.endpoint_refs[1]}
                   if e.edge_kind == 'OBSERVED_ORDER'
                   else {'endpoint_refs': list(e.endpoint_refs)})) for e in self.graph.edges],
            'annotation_badges': self._annotation_badges(),
            'unknown_gaps': self._unknown_gap_projection(),
            'conflict_badges': self._conflict_badges(),
            'accessibility_linear_order': [n.node_ref for n in self.graph.nodes],
        }

    def safe_text_projection(self, *, authenticated_owner_scope: str) -> dict:
        return self._text_from_visual(self.safe_projection(
            authenticated_owner_scope=authenticated_owner_scope))

    @staticmethod
    def _text_from_visual(visual):
        lines = [LABELS[n['node_kind']] + '：' + n['visible_label']
                 + '（' + str(n['evidence_badge_count']) + '件の記録）'
                 for n in visual['nodes']]
        labels = {n['node_ref']: n['visible_label'] for n in visual['nodes']}
        for edge in visual['edges']:
            if edge['edge_kind'] == 'OBSERVED_ORDER':
                lines.append('記録内の順序：' + labels[edge['from_ref']] + ' → '
                             + labels[edge['to_ref']] + '。原因を示す線ではありません。')
            else:
                lines.append('複数の記録で一緒に現れた内容：' + ' ／ '.join(
                    labels[ref] for ref in edge['endpoint_refs'])
                    + '。順序や原因は確定していません。')
        lines.extend('未確定（' + ' ／ '.join(labels[ref] for ref in g['between_node_refs'])
                     + '）：' + g['visible_label'] for g in visual['unknown_gaps'])
        lines.extend('注記（' + labels[a['target_ref']] + '）：' + a['visible_label']
                     for a in visual['annotation_badges'])
        lines.extend('一致していない記録（' + ' ／ '.join(labels[ref] for ref in c['target_refs'])
                     + '）：' + c['visible_label'] for c in visual['conflict_badges'])
        return {'projection_of': visual['projection_of'], 'text': '\n'.join(lines),
                'accessibility_linear_order': visual['accessibility_linear_order']}


@dataclass(frozen=True, slots=True, repr=False)
class AnalysisEngineOutcome:
    status: EngineStatus
    reason_codes: tuple[str, ...]
    artifact: ObservedSelfStructureMap | None = None
    automatic_progression: bool = False

    def as_body_free(self):
        return {'core_id': 'analysis', 'execution_mode': 'OFFLINE_CANDIDATE',
            'status': self.status.value, 'reason_codes': list(self.reason_codes),
            'artifact_present': self.artifact is not None,
            'production_enabled': False, 'record_effect': 0,
            'automatic_progression': False}


def generate_observed_map(request: AnalysisObservedMapRequest) -> AnalysisEngineOutcome:
    try:
        sources = freeze_analysis_sources(request)
    except AnalysisSourceError as exc:
        return AnalysisEngineOutcome(EngineStatus.REJECTED, (str(exc),))
    except Exception:
        return AnalysisEngineOutcome(EngineStatus.REJECTED, ('analysis_source_invalid',))
    try:
        graph = compile_observed_graph(sources)
        if not graph.nodes:
            return AnalysisEngineOutcome(EngineStatus.UNAVAILABLE,
                ('analysis_observed_route_not_established',))
        artifact = ObservedSelfStructureMap('artifact:' + uuid4().hex, 1,
            sources.owner_scope, sources.source_set_ref, sources.period,
            graph, sources.members)
        # A partial observed map is a valid result, not a fallback to v1.
        return AnalysisEngineOutcome(EngineStatus.GENERATED,
            ('analysis_partial_observed_map',), artifact)
    except AnalysisSourceError as exc:
        return AnalysisEngineOutcome(EngineStatus.UNAVAILABLE, (str(exc),))
    except Exception:
        return AnalysisEngineOutcome(EngineStatus.UNAVAILABLE,
            ('analysis_semantic_generation_unavailable',))
