"""Owner-facing projections and private previews of one observed artifact.

Only safe_projection reconstructs labels from complete grammatical parts.
Private previews retain source clauses and must never be returned by an API.
Owner authorization, retention and deletion checks remain the caller's duty.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import json
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
    if parts.written_modifiers:
        modifier_text = ''.join({'THIS_OCCASION': '今回は、', 'IN_ADVANCE': '事前に',
                         'DEGREE_SLIGHT': '少し', 'DEGREE_TOTEMO': 'とても',
                         'DEGREE_KANARI': 'かなり', 'DEGREE_YAYA': 'やや',
                         'DEGREE_CHOTTO': 'ちょっと',
                         'NEGATION_MATTAKU_KANJI': '全く', 'NEGATION_MATTAKU_KANA': 'まったく',
                         'NEGATION_ZENZEN': '全然',
                         'PARTIAL_NEGATION_AMARI': 'あまり',
                         'PARTIAL_NEGATION_ANMARI': 'あんまり',
                         'NEGATION_SUKOSHIMO': '少しも', 'NEGATION_CHITTOMO': 'ちっとも'}[modifier]
                         for modifier in parts.written_modifiers)
        # Safe replay has already checked every source coordinate. Preserve a
        # degree written after 不安は/が while keeping its meaning key unchanged.
        post_degree = (parts.predicate_lemma == 'ある'
            and parts.arguments in {(('は', '不安'),), (('が', '不安'),)}
            and any(kind.startswith('WRITTEN_MODIFIER_') and start == case_end
                    for kind, start, _ in parts.source_parts
                    for case_kind, _, case_end in parts.source_parts
                    if case_kind == 'CASE_' + parts.arguments[0][0]))
        phrase = phrase[:3] + modifier_text + phrase[3:] if post_degree else modifier_text + phrase
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
        scope = '（誰の気持ちかは未確定）' if parts.actor == 'UNSPECIFIED' else '（記録された気持ち）'
        phrase = (''.join(noun + case for case, noun in parts.arguments)
                  + ('なかった' if parts.polarity == 'negative' else 'あった')
                  if parts.predicate_lemma == 'ある' else forms[parts.predicate_lemma])
        return _source_prefix(phrase, parts) + scope
    if parts.result_state == 'CURRENT_FEELING':
        phrase = (''.join(noun + case for case, noun in parts.arguments)
                  + ('ない' if parts.polarity == 'negative' else 'ある')
                  if parts.predicate_lemma == 'ある' else
                  '不安ではない' if parts.polarity == 'negative' else parts.predicate_lemma)
        return _source_prefix(phrase, parts) + '（この記述時点の気持ち）'
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
    label = phrase + ('（実行済み）' if parts.polarity == 'positive'
                     else '（行わなかった）')
    return label + ('（誰の行動かは未確定）' if parts.actor == 'UNSPECIFIED' else '')


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


# Private snapshot projection. The legacy safe projection and its edge wording
# remain unchanged; no new scope relation is sent through _text_from_visual.
from .intent_compiler import (
    AnalysisSemanticGraphV1, _semantic_json, _semantic_digest, _semantic_ref,
    _semantic_same, _semantic_snapshot_view, validate_semantic_graph,
)

_ANALYSIS_SEMANTIC_ARTIFACT_SCHEMA = 'cocolon.cmee.analysis_semantic_artifact.v1'
_ANALYSIS_SEMANTIC_MEANING_VERSION = 'cocolon.cmee.analysis_candidate_meaning.v1'
_ANALYSIS_SEMANTIC_VISUAL_SCHEMA = 'cocolon.cmee.analysis_semantic_visual.v1'


@dataclass(frozen=True, slots=True, repr=False)
class AnalysisSemanticArtifactV1:
    artifact_json: str

    def payload(self):
        if type(self.artifact_json) is not str:
            raise AnalysisSourceError('analysis_semantic_artifact_invalid')
        value = json.loads(self.artifact_json)
        if not _semantic_same(self.artifact_json, _semantic_json(value)):
            raise AnalysisSourceError('analysis_semantic_artifact_invalid')
        return value

    @property
    def artifact_ref(self):
        return self.payload()['artifact_ref']

    @property
    def text_sections(self):
        return tuple(self.payload()['text_sections'])

    @property
    def visual_projection_json(self):
        return _semantic_json(self.payload()['visual_projection_json'])


def _semantic_evidence_ref(graph, index):
    return _semantic_ref('evidence', graph['snapshot_ref'],
                         _semantic_json(graph['evidence'][index]))


def _semantic_visual_material(graph):
    # This is a schema projection, not a second graph or semantic author.
    value = {k: v for k, v in graph.items()
             if k not in ('schema_version', 'unit_node_bindings')}
    value['schema_version'] = _ANALYSIS_SEMANTIC_VISUAL_SCHEMA
    value['source_selections'] = [dict(s, visual_ref=_semantic_ref(
        'selection', graph['snapshot_ref'], s['selection_ref']))
        for s in graph['source_selections']]
    value['evidence'] = [dict(e, evidence_ref=_semantic_evidence_ref(graph, i))
                         for i, e in enumerate(graph['evidence'])]
    return value


def _semantic_text_layout(graph):
    """Place complete source groups and the bounded material-unknown label."""
    sections, group_ranges = [], {}
    source_ids = list(dict.fromkeys(g['source_id'] for g in graph['groups']))
    for source_id in source_ids:
        groups = [g for g in graph['groups'] if g['source_id'] == source_id]
        text, previous_field = '', None
        section_index = len(sections)
        for group in groups:
            if previous_field is not None and group['field_path'] != previous_field:
                text += '\n'
            start = len(text)
            text += group['original_text']
            evidence = graph['evidence'][group['evidence_indexes'][0]]
            group_ranges[group['group_ref']] = (section_index, start, evidence)
            previous_field = group['field_path']
        sections.append(dict(source_id=source_id,
                             section_kind='ORIGINAL_SOURCE_GROUPS', text=text))
    unknown_ranges = {}
    for unknown in graph['unknowns']:
        evidence = graph['evidence'][unknown['evidence_indexes'][0]]
        label = unknown['proposed_label']
        unknown_ranges[unknown['unknown_ref']] = (len(sections), 0, len(label))
        sections.append(dict(source_id=evidence['source_id'],
            section_kind='MATERIAL_UNKNOWN', text=label))
    return sections, group_ranges, unknown_ranges


def _semantic_trace_rows(graph, group_ranges, unknown_ranges):
    rows = []
    carriers = [(n['unit_ref'], n['node_ref'], n) for n in graph['nodes']]
    carriers += [(n['unit_ref'], n['carrier_ref'], n)
                 for n in graph['dependent_scopes']]
    carriers += [(a['unit_ref'], a['carrier_ref'], a['unit_binding'])
                 for a in graph['annotations']]
    for unit_ref, carrier_ref, carrier in carriers:
        unit = carrier['claim_json']
        section_index, group_start, group_evidence = group_ranges[unit['group_ref']]
        evidence = graph['evidence'][unit['evidence_indexes'][0]]
        start = group_start + evidence['start'] - group_evidence['start']
        rows.append(dict(meaning_ref=unit_ref, trace_kind=unit['carrier'],
            carrier_ref=carrier_ref, group_ref=unit['group_ref'],
            source_binding_refs=[carrier['source_binding_ref']],
            text_section_index=section_index, visible_scalar_start=start,
            visible_scalar_end=start + len(evidence['quote']), visual_ref=carrier_ref))
    for relation in graph['scope_relations']:
        evidence = graph['evidence'][relation['evidence_indexes'][0]]
        group = next(g for g in graph['groups'] if
            g['source_id'] == evidence['source_id'] and g['field_path'] == evidence['field_path'] and
            (base := graph['evidence'][g['evidence_indexes'][0]])['start'] <= evidence['start'] and
            evidence['end'] <= base['end'])
        section_index, group_start, group_evidence = group_ranges[group['group_ref']]
        start = group_start + evidence['start'] - group_evidence['start']
        indexes = list(dict.fromkeys(relation['evidence_indexes'] + relation['marker_evidence_indexes']))
        rows.append(dict(meaning_ref=relation['relation_ref'],
            trace_kind='SOURCE_SCOPE_RELATION', carrier_ref=relation['scope_ref'],
            group_ref=group['group_ref'],
            source_binding_refs=[_semantic_evidence_ref(graph, i) for i in indexes],
            text_section_index=section_index, visible_scalar_start=start,
            visible_scalar_end=start + len(evidence['quote']), visual_ref=relation['scope_ref']))
    for unknown in graph['unknowns']:
        section_index, start, end = unknown_ranges[unknown['unknown_ref']]
        rows.append(dict(meaning_ref=unknown['unknown_ref'], trace_kind='MATERIAL_UNKNOWN',
            carrier_ref=unknown['carrier_ref'], group_ref=None,
            source_binding_refs=[_semantic_evidence_ref(graph, i) for i in unknown['evidence_indexes']],
            text_section_index=section_index, visible_scalar_start=start,
            visible_scalar_end=end, visual_ref=unknown['carrier_ref']))
    for selection in graph['source_selections']:
        visual_ref = _semantic_ref('selection', graph['snapshot_ref'], selection['selection_ref'])
        rows.append(dict(meaning_ref=selection['selection_ref'],
            trace_kind='RETAINED_SOURCE_SELECTION', carrier_ref=visual_ref,
            group_ref=None, source_binding_refs=[_semantic_ref('selection-binding',
                graph['snapshot_ref'], _semantic_json([selection['source_id'], alias]))
                for alias in selection['alias_refs']], text_section_index=None,
            visible_scalar_start=None, visible_scalar_end=None, visual_ref=visual_ref))
    return rows


def _semantic_artifact_identity(payload):
    material = {k: v for k, v in payload.items() if k not in ('artifact_ref', 'content_hash')}
    content_hash = 'sha256:' + _semantic_digest(material)
    artifact_ref = 'analysis-semantic-artifact:' + _semantic_digest([
        content_hash, material['schema_version'], material['semantic_profile'],
        material['snapshot_ref'], material['graph_ref']])
    return content_hash, artifact_ref


def realize_semantic_graph(snapshot, graph):
    """The existing sole realizer's explicit private snapshot arm."""
    validate_semantic_graph(snapshot, graph)
    view, source = _semantic_snapshot_view(snapshot), graph.payload()
    sections, group_ranges, unknown_ranges = _semantic_text_layout(source)
    payload = dict(schema_version=_ANALYSIS_SEMANTIC_ARTIFACT_SCHEMA,
        meaning_contract_version=_ANALYSIS_SEMANTIC_MEANING_VERSION,
        semantic_profile=view['semantic_profile'], snapshot_ref=view['snapshot_ref'],
        graph_ref=source['graph_ref'], source_commitment=view['source_commitment'],
        visual_projection_json=_semantic_visual_material(source), text_sections=sections,
        realizations=_semantic_trace_rows(source, group_ranges, unknown_ranges),
        retained_selection_refs=[s['selection_ref'] for s in source['source_selections']])
    payload['content_hash'], payload['artifact_ref'] = _semantic_artifact_identity(payload)
    artifact = AnalysisSemanticArtifactV1(_semantic_json(payload))
    validate_semantic_artifact(snapshot, graph, artifact)
    return artifact


def validate_semantic_artifact(snapshot, graph, artifact):
    """Read saved surfaces from source/graph constraints without the author.

    The reader does not call realize_semantic_graph, compile_semantic_graph,
    the old safe label/parser, or the old text renderer. A matching hash alone
    cannot satisfy source content, typed coverage, or visible-range checks.
    """
    validate_semantic_graph(snapshot, graph)
    view, source = _semantic_snapshot_view(snapshot), graph.payload()
    if type(artifact) is not AnalysisSemanticArtifactV1:
        raise AnalysisSourceError('analysis_semantic_artifact_invalid')
    payload = artifact.payload()
    keys = {'schema_version', 'meaning_contract_version', 'semantic_profile',
        'snapshot_ref', 'graph_ref', 'source_commitment', 'visual_projection_json',
        'text_sections', 'realizations', 'retained_selection_refs', 'content_hash', 'artifact_ref'}
    if type(payload) is not dict or set(payload) != keys:
        raise AnalysisSourceError('analysis_semantic_artifact_invalid')
    expected_identity = dict(schema_version=_ANALYSIS_SEMANTIC_ARTIFACT_SCHEMA,
        meaning_contract_version=_ANALYSIS_SEMANTIC_MEANING_VERSION,
        semantic_profile=view['semantic_profile'], snapshot_ref=view['snapshot_ref'],
        graph_ref=source['graph_ref'], source_commitment=view['source_commitment'])
    if any(not _semantic_same(payload[k], expected) for k, expected in expected_identity.items()):
        raise AnalysisSourceError('analysis_semantic_artifact_invalid')
    visual = payload['visual_projection_json']
    if not _semantic_same(visual, _semantic_visual_material(source)):
        raise AnalysisSourceError('analysis_semantic_artifact_invalid')
    # Inspect record/field groups as saved visible text, not generated prose.
    sections = payload['text_sections']
    source_ids = list(dict.fromkeys(g['source_id'] for g in source['groups']))
    if type(sections) is not list or len(sections) != len(source_ids) + len(source['unknowns']):
        raise AnalysisSourceError('analysis_semantic_artifact_invalid')
    group_ranges, unknown_ranges = {}, {}
    for section_index, source_id in enumerate(source_ids):
        groups = [g for g in source['groups'] if g['source_id'] == source_id]
        pieces, size, previous_field = [], 0, None
        for group in groups:
            if previous_field is not None and group['field_path'] != previous_field:
                pieces.append('\n')
                size += 1
            group_ranges[group['group_ref']] = (section_index, size,
                source['evidence'][group['evidence_indexes'][0]])
            pieces.append(group['original_text'])
            size += len(group['original_text'])
            previous_field = group['field_path']
        expected_section = dict(source_id=source_id,
            section_kind='ORIGINAL_SOURCE_GROUPS', text=''.join(pieces))
        if not _semantic_same(sections[section_index], expected_section):
            raise AnalysisSourceError('analysis_semantic_artifact_invalid')
    for index, unknown in enumerate(source['unknowns'], len(source_ids)):
        evidence = source['evidence'][unknown['evidence_indexes'][0]]
        expected_section = dict(source_id=evidence['source_id'],
            section_kind='MATERIAL_UNKNOWN', text=unknown['proposed_label'])
        if not _semantic_same(sections[index], expected_section):
            raise AnalysisSourceError('analysis_semantic_artifact_invalid')
        unknown_ranges[unknown['unknown_ref']] = (index, 0, len(unknown['proposed_label']))
    expected_traces = _semantic_trace_rows(source, group_ranges, unknown_ranges)
    if not _semantic_same(payload['realizations'], expected_traces):
        raise AnalysisSourceError('analysis_semantic_artifact_invalid')
    # Every visible range must literally address its source quote or bounded
    # unknown label. Retained selections deliberately have no text range.
    units = {u['unit_ref']: u for u in view['candidate_packet']['candidate']['units']}
    relations = {r['relation_ref']: r for r in source['scope_relations']}
    unknowns = {u['unknown_ref']: u for u in source['unknowns']}
    for trace in payload['realizations']:
        if trace['trace_kind'] == 'RETAINED_SOURCE_SELECTION':
            if any(trace[k] is not None for k in ('group_ref', 'text_section_index',
                                                'visible_scalar_start', 'visible_scalar_end')):
                raise AnalysisSourceError('analysis_semantic_artifact_invalid')
            continue
        section = sections[trace['text_section_index']]['text']
        a, b = trace['visible_scalar_start'], trace['visible_scalar_end']
        if type(a) is not int or type(b) is not int or not 0 <= a < b <= len(section):
            raise AnalysisSourceError('analysis_semantic_artifact_invalid')
        meaning_ref = trace['meaning_ref']
        if meaning_ref in units:
            literal = source['evidence'][units[meaning_ref]['evidence_indexes'][0]]['quote']
        elif meaning_ref in relations:
            literal = source['evidence'][relations[meaning_ref]['evidence_indexes'][0]]['quote']
        else:
            literal = unknowns[meaning_ref]['proposed_label']
        if section[a:b] != literal:
            raise AnalysisSourceError('analysis_semantic_artifact_invalid')
    if not _semantic_same(payload['retained_selection_refs'],
            [s['selection_ref'] for s in source['source_selections']]):
        raise AnalysisSourceError('analysis_semantic_artifact_invalid')
    content_hash, artifact_ref = _semantic_artifact_identity(payload)
    if payload['content_hash'] != content_hash or payload['artifact_ref'] != artifact_ref:
        raise AnalysisSourceError('analysis_semantic_artifact_invalid')
    return artifact


def artifact_from_payload(snapshot, graph, payload):
    artifact = AnalysisSemanticArtifactV1(_semantic_json(payload))
    return validate_semantic_artifact(snapshot, graph, artifact)
