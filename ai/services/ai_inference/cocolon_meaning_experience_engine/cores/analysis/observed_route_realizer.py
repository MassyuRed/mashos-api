"""Owner-facing projections and private previews of one observed artifact.

Only safe_projection reconstructs labels from complete grammatical parts.
Private previews retain source clauses and must never be returned by an API.
Owner authorization, retention and deletion checks remain the caller's duty.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import logging
from uuid import uuid4

from ...contracts import EngineStatus
from .intent_compiler import (ObservedGraph, NODE_KINDS, compile_observed_graph, _proposition,
                              _CANONICAL_CONTENT, _RESULT_STEMS, _CHANGE_PAST,
                              _FEELING_PAST, _FEELING_PAST_NEGATIVE,
                              _te_action_proposition, _burden_predicate,
                              _protective_wish_proposition, _proposition_meaning,
                              PeriodComparison, compare_period_meaning)
from .source_adapter import (
    AnalysisObservedMapRequest, AnalysisSourceError, AnalysisSourceMember,
    freeze_analysis_sources,
)

logger = logging.getLogger(__name__)
# Exact literals only: exceptions and source values must never enter logs.
_FAILURE_LOG_REASONS = frozenset({
    'analysis_answer_range_invalid',
    'analysis_comparison_binding_invalid',
    'analysis_comparison_evidence_unavailable',
    'analysis_comparison_meaning_unavailable',
    'analysis_comparison_owner_mismatch',
    'analysis_comparison_request_invalid',
    'analysis_comparison_unavailable',
    'analysis_correction_replacement_unsupported',
    'analysis_correction_target_unresolved',
    'analysis_duplicate_record_conflict',
    'analysis_fragment_evidence_mismatch',
    'analysis_observed_route_not_established',
    'analysis_original_invalid',
    'analysis_original_shape_invalid',
    'analysis_owner_mismatch',
    'analysis_period_invalid',
    'analysis_previous_map_unavailable',
    'analysis_projection_owner_mismatch',
    'analysis_record_not_live',
    'analysis_record_version_mismatch',
    'analysis_request_out_of_scope',
    'analysis_safe_surface_unavailable',
    'analysis_semantic_generation_unavailable',
    'analysis_separate_safety_required',
    'analysis_source_field_unbound',
    'analysis_source_invalid',
    'analysis_supplement_binding_invalid',
    'analysis_supplement_cardinality',
    'analysis_supplement_interpretation_pending',
    'analysis_supplement_parent_missing',
    'analysis_text_field_invalid',
    'analysis_timestamp_invalid',
})

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
PROTECTIVE_LABEL = '守りたいという意向の記録です。実際に守れているかは確定していません。'
COMPARISON_CHANGES = {
    'ROUTE_EVIDENCE_CHANGED': '読み取れた内容・つながり',
    'ANNOTATION_EVIDENCE_CHANGED': '守る対象・負荷の記述',
    'UNKNOWN_SCOPE_CHANGED': '確定できない部分',
    'CONFLICT_STATE_CHANGED': '一致していない記述の組み合わせ',
}
COMPARISON_REASONS = {
    'PERIOD_LENGTH_MISMATCH': '期間の長さが異なります。',
    'PREVIOUS_PERIOD_NOT_EARLIER': '比較対象が前の期間ではありません。',
    'PERIOD_OVERLAP': '二つの期間が重なっています。',
    'PERIOD_NOT_ADJACENT': '直前の期間ではありません。',
    'SHARED_RECORD_IDENTITY': '同じ記録が両方の期間に含まれています。',
}


def _comparison_lines(comparison):
    state = comparison['state']
    if state == 'NO_PREVIOUS':
        return []  # Preserve every previously saved text byte.
    if state == 'NOT_COMPARABLE':
        return ['期間比較：この二つの期間は比較できません。'] + [
            COMPARISON_REASONS.get(code, '比較条件を確認できません。')
            for code in comparison['reason_codes']]
    changes = comparison['safe_change_kinds']
    if not changes:
        return ['期間比較：今回比較した記述内容では差分を検出していません。'
                '記録の件数や、読み取れていない内容の変化は判断していません。']
    return ['期間比較：前の同じ長さの期間と比べ、' + '、'.join(
        COMPARISON_CHANGES[kind] for kind in changes) + 'が異なります。',
        '記録上の違いであり、改善・悪化や原因を示すものではありません。']


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


def _source_prefix(phrase, parts):
    if parts.sequence_marker:
        phrase = {'AFTER_PREVIOUS': 'その後：',
                  'THEN_OR_ADDITION': 'それから：'}[parts.sequence_marker] + phrase
    if parts.relative_day:
        phrase = 'この記述時点の' + {'TODAY': '今日', 'YESTERDAY': '昨日'}[parts.relative_day] + '：' + phrase
    return phrase


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
        forms = _FEELING_PAST_NEGATIVE if parts.polarity == 'negative' else _FEELING_PAST
        return forms[parts.predicate_lemma] + '（記録された気持ち）'
    if parts.scene_state == 'PAST_PRESENCE':
        phrase = ''.join(noun + case for case, noun in parts.arguments)
        return _source_prefix(phrase + ('いた' if parts.polarity == 'positive' else 'いなかった'), parts) + '（記録された場面）'
    if parts.role_state == 'PAST_RESPONSIBILITY':
        phrase = ''.join(noun + case for case, noun in parts.arguments)
        return _source_prefix(phrase + ('担当した' if parts.polarity == 'positive' else '担当しなかった'), parts) + '（記録された担当）'
    if parts.possible_content is not None:
        content = parts.possible_content
        phrase = ''.join(noun + case for case, noun in content.arguments)
        phrase += _CANONICAL_CONTENT[(content.predicate_lemma, content.polarity, content.temporal_scope)]
        return phrase + 'かもしれないと' + parts.predicate_lemma + '（この記述時点の考え）'
    phrase = ''.join(noun + case for case, noun in parts.arguments) + parts.predicate_lemma
    phrase = _source_prefix(phrase, parts)
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
    period_comparison: PeriodComparison | None = None

    @property
    def reference(self):
        return self.artifact_id + '@' + str(self.artifact_version)

    def _comparison_projection(self):
        c = self.period_comparison
        if c is None:
            return {'state': 'NO_PREVIOUS', 'reason_codes': [], 'safe_change_kinds': []}
        if (c.current_artifact_ref != self.reference or c.current_source_set_ref != self.source_set_ref
                or c.previous_artifact_ref == self.reference
                or c.comparability_state not in {'COMPARABLE', 'NOT_COMPARABLE'}
                or (c.comparability_state == 'NOT_COMPARABLE' and (not c.reason_codes or c.change_claims))
                or (c.comparability_state == 'COMPARABLE' and c.reason_codes)
                or any(reason not in COMPARISON_REASONS for reason in c.reason_codes)
                or len({x.change_kind for x in c.change_claims}) != len(c.change_claims)
                or any(x.change_kind not in COMPARISON_CHANGES or not x.evidence_refs
                    or x.current_ref != self.reference or x.previous_ref != c.previous_artifact_ref
                    for x in c.change_claims)):
            raise AnalysisSourceError('analysis_comparison_binding_invalid')
        return {'state': c.comparability_state, 'reason_codes': list(c.reason_codes),
                'safe_change_kinds': [x.change_kind for x in c.change_claims]}

    def _conflict_badges(self):
        return [{'conflict_ref': c.conflict_ref, 'target_refs': list(c.target_refs),
                 'visible_label': CONFLICT_LABEL} for c in self.graph.conflicts]

    def _unknown_gap_projection(self):
        # Keep every private gap. In the display, list missing stages once per
        # ordered target and ordinary absence reason, retaining every scope.
        # Sources may differ: the list must not claim one shared missing episode.
        # Other reasons stay separate; preserve first identities and order.
        gaps, seen, stage_groups = [], set(), {}
        for gap in self.graph.unknown_gaps:
            key = (gap.between_node_refs, gap.missing_scope, gap.reason_code)
            if key in seen:
                continue
            seen.add(key)
            ordinary_stage = (gap.reason_code == 'NOT_ESTABLISHED_FROM_SOURCE'
                              and gap.missing_scope in NODE_KINDS)
            if ordinary_stage and gap.between_node_refs in stage_groups:
                item, scopes = stage_groups[gap.between_node_refs]
                scopes.append(LABELS[gap.missing_scope])
                item['visible_label'] = '確定していない項目：' + '、'.join(scopes) + '。'
                continue
            label = LABELS[gap.missing_scope] + 'は、この記録からは確定していません。'
            if (gap.missing_scope == 'ROUTE_CONNECTION'
                    and gap.reason_code == 'EXPLICIT_PREDECESSOR_NOT_ESTABLISHED'):
                label = 'この記述がどの内容に続くのかは、この記録からは確定していません。'
            item = {'gap_ref': gap.gap_ref,
                'between_node_refs': list(gap.between_node_refs),
                'visible_label': label}
            gaps.append(item)
            if ordinary_stage:
                stage_groups[gap.between_node_refs] = (item, [LABELS[gap.missing_scope]])
        return gaps

    def _annotation_badges(self):
        badges = []
        nodes = {n.node_ref: n for n in self.graph.nodes}
        for claim in self.graph.annotations:
            target = nodes.get(claim.target_ref)
            p = target.proposition if target else None
            if claim.kind == 'PROTECTIVE':
                if (p is None or target.node_kind != 'ATTENTION_OR_THOUGHT'
                        or _protective_wish_proposition(target.visible_label) != p
                        or (target.polarity, target.modality, target.temporal_scope)
                            != ('positive', 'wish', 'current_input')
                        or claim.predicate_lemma != '守る'
                        or claim.annotation_state != 'SOURCE_EXPLICIT_ANNOTATION'
                        or not claim.source_labels or not claim.evidence_refs
                        or claim.evidence_refs != target.evidence_refs):
                    raise AnalysisSourceError('analysis_safe_surface_unavailable')
                for label in claim.source_labels:
                    parsed = _protective_wish_proposition(label)
                    if parsed is None or _proposition_meaning(parsed) != _proposition_meaning(p):
                        raise AnalysisSourceError('analysis_safe_surface_unavailable')
                badges.append({'annotation_ref': claim.annotation_ref, 'target_ref': claim.target_ref,
                    'kind': claim.kind, 'visible_label': PROTECTIVE_LABEL})
                continue
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
            'period_comparison': self._comparison_projection(),
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
            'period_comparison': self._comparison_projection(),
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
        lines.extend(_comparison_lines(visual['period_comparison']))
        return {'projection_of': visual['projection_of'], 'text': '\n'.join(lines),
                'accessibility_linear_order': visual['accessibility_linear_order']}


@dataclass(frozen=True, slots=True, repr=False)
class AnalysisEngineOutcome:
    status: EngineStatus
    reason_codes: tuple[str, ...]
    artifact: ObservedSelfStructureMap | None = None
    automatic_progression: bool = False
    # Request-local baseline for resolving private comparison claims. It is
    # never serialized into safe DTOs or accepted by the saved-map writer.
    previous_artifact: ObservedSelfStructureMap | None = None

    def as_body_free(self):
        return {'core_id': 'analysis', 'execution_mode': 'OFFLINE_CANDIDATE',
            'status': self.status.value, 'reason_codes': list(self.reason_codes),
            'artifact_present': self.artifact is not None,
            'production_enabled': False, 'record_effect': 0,
            'automatic_progression': False}


def _failed_outcome(status, reason, *, stage, diagnostic_reason=None):
    """Log closed diagnostics without changing the existing failure contract."""
    candidate = reason if diagnostic_reason is None else diagnostic_reason
    safe_reason = (candidate if type(candidate) is str and candidate in _FAILURE_LOG_REASONS
                   else 'analysis_generation_reason_unclassified')
    safe_stage = (stage if type(stage) is str and stage in {'current', 'previous', 'comparison'}
                  else 'unclassified')
    logger.warning('analysis_observed_generation_unavailable stage=%s reason=%s',
                   safe_stage, safe_reason)
    return AnalysisEngineOutcome(status, (reason,))


def _generate_single_observed_map(request: AnalysisObservedMapRequest, *,
                                  period_role='current') -> AnalysisEngineOutcome:
    try:
        sources = freeze_analysis_sources(request)
    except AnalysisSourceError as exc:
        return _failed_outcome(EngineStatus.REJECTED, str(exc), stage=period_role)
    except Exception:
        return _failed_outcome(EngineStatus.REJECTED, 'analysis_source_invalid', stage=period_role)
    try:
        graph = compile_observed_graph(sources)
        if not graph.nodes:
            return _failed_outcome(EngineStatus.UNAVAILABLE,
                'analysis_observed_route_not_established', stage=period_role)
        artifact = ObservedSelfStructureMap('artifact:' + uuid4().hex, 1,
            sources.owner_scope, sources.source_set_ref, sources.period,
            graph, sources.members)
        # A partial observed map is a valid result, not a fallback to v1.
        return AnalysisEngineOutcome(EngineStatus.GENERATED,
            ('analysis_partial_observed_map',), artifact)
    except AnalysisSourceError as exc:
        return _failed_outcome(EngineStatus.UNAVAILABLE, str(exc), stage=period_role)
    except Exception:
        return _failed_outcome(EngineStatus.UNAVAILABLE,
            'analysis_semantic_generation_unavailable', stage=period_role)


def generate_observed_map(request: AnalysisObservedMapRequest) -> AnalysisEngineOutcome:
    previous = request.comparison_previous_request
    if previous is None:
        return _generate_single_observed_map(request)
    if (type(previous) is not AnalysisObservedMapRequest
            or previous.comparison_previous_request is not None):
        return _failed_outcome(EngineStatus.REJECTED, 'analysis_comparison_request_invalid',
                               stage='comparison')
    if previous.authenticated_owner_scope != request.authenticated_owner_scope:
        return _failed_outcome(EngineStatus.REJECTED, 'analysis_comparison_owner_mismatch',
                               stage='comparison')
    # Both periods use this same invocation's interpretation policy. Do not
    # replay an old stored map as if it was freshly generated under this code.
    current = _generate_single_observed_map(request)
    if current.artifact is None:
        return current
    before = _generate_single_observed_map(previous, period_role='previous')
    if before.artifact is None:
        return AnalysisEngineOutcome(before.status, ('analysis_previous_map_unavailable',))
    try:
        current.artifact.safe_projection(authenticated_owner_scope=request.authenticated_owner_scope)
        before.artifact.safe_projection(authenticated_owner_scope=request.authenticated_owner_scope)
        comparison = compare_period_meaning(current.artifact, before.artifact)
        return replace(current, artifact=replace(current.artifact, period_comparison=comparison),
                       previous_artifact=before.artifact)
    except (AnalysisSourceError, KeyError, TypeError, ValueError) as exc:
        return _failed_outcome(EngineStatus.UNAVAILABLE, 'analysis_comparison_unavailable',
            stage='comparison', diagnostic_reason=(str(exc) if isinstance(exc, AnalysisSourceError)
                                                    else 'analysis_comparison_unavailable'))
