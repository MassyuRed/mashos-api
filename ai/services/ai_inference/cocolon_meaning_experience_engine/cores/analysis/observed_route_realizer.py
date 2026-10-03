"""Private offline previews of one observed artifact, never public DTOs.

Labels currently preserve finite source clauses. These previews are private
development output, not the canonical safe projection for API/RN publication.
The lifecycle/public-surface integration must not return them to public APIs.
"""
from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from ...contracts import EngineStatus
from .intent_compiler import ObservedGraph, compile_observed_graph
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
            'annotation_badges': [],
            'unknown_gaps': [{'gap_ref': g.gap_ref,
                'between_node_refs': list(g.between_node_refs),
                'visible_label': LABELS[g.missing_scope] + 'は、この記録からは確定していません。'}
                for g in self.graph.unknown_gaps],
            'conflict_badges': [],
            'accessibility_linear_order': [n.node_ref for n in self.graph.nodes],
        }

    def private_text_preview(self, *, authenticated_owner_scope: str) -> dict:
        visual = self.private_visual_preview(authenticated_owner_scope=authenticated_owner_scope)
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
        lines.extend(dict.fromkeys(g['visible_label'] for g in visual['unknown_gaps']))
        return {'projection_of': self.reference, 'text': '\n'.join(lines),
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
