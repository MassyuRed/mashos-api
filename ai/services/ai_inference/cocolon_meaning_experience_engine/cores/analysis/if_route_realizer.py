"""Person-authored IF choices and immutable, separately partitioned intentions.

This is the source-grounded IF arm: it shows the person's possible choices,
their constraints and an explicit unknown outcome. It does not invent future
steps, predict a result, rank alternatives, or treat an AI map as a source.
Persistence, current-source checks and entitlement belong to the lifecycle.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
import hashlib
import json
import re

from ...contracts import EngineStatus, SourceEnvelope
from .if_route_contracts import (AnalysisIfRouteOutcome, AnalysisIfRouteRequest,
                                 AnalysisIfModelPrepared, AnalysisSimulationSource)
from .source_adapter import canonical_bytes, commitment

POLICY = 'analysis.if.user-choices.v1'
STORAGE_SCHEMA = 'analysis.if-storage.v1'
IF_KIND = 'ANALYSIS_IF_SCENARIO_SET'
SAVED_KIND = 'ANALYSIS_SAVED_ROUTE_INTENT'
IF_SCHEMA = 'cocolon.cmee.analysis_if_safe_projection.v1alpha1'
SAVED_SCHEMA = 'cocolon.cmee.analysis_saved_intent_safe_projection.v1alpha1'
UNKNOWN_RESULT = 'この選択の後に起こることは、まだ分かりません。'
UNMODELLED = '相手の反応や、その後の状況は、ここでは分かりません。'
_ARTIFACT = re.compile(r'artifact:[0-9a-f]{32}@1\Z')
_STORAGE_KEYS = frozenset(('schema_version', 'owner_scope', 'bundle',
    'base_projection', 'base_private_evidence', 'session_sources',
    'scenario_graphs', 'parent_scenario_set', 'model_receipt', 'safe_projection',
    'content_text', 'integrity'))


class AnalysisIfRouteError(ValueError):
    """Fixed, body-free reason codes only."""


def _require(value, reason='analysis_if_artifact_invalid'):
    if not value:
        raise AnalysisIfRouteError(reason)


def _json(value):
    return canonical_bytes(value).decode('utf-8')


def _load(value):
    try:
        def unique(pairs):
            result = {}
            for key, item in pairs:
                if key in result:
                    raise ValueError
                result[key] = item
            return result
        return json.loads(value, object_pairs_hook=unique,
                          parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    except (ValueError, TypeError, UnicodeError):
        raise AnalysisIfRouteError('analysis_if_json_invalid') from None


def _text(value, limit=2000):
    return (type(value) is str and bool(value.strip()) and value == value.strip()
            and len(value) <= limit and '\x00' not in value)


def _ref(prefix, value):
    return prefix + commitment(value)[7:] + '@1'


def observed_route_reference(base_observed_map_ref, branch_point_id):
    """Versioned locator for a selected saved subgraph, not an inferred order."""
    _require(type(base_observed_map_ref) is str and _ARTIFACT.fullmatch(base_observed_map_ref),
             'analysis_if_base_reference_invalid')
    _require(_text(branch_point_id, 200), 'analysis_if_branch_unavailable')
    return _ref('route:', [base_observed_map_ref, branch_point_id])


def _source(source, owner):
    _require(type(source) is AnalysisSimulationSource,
             'analysis_if_session_source_invalid')
    _require(source.owner_scope == owner and _text(source.source_id, 200)
             and _text(source.text) and _text(source.source_version, 100)
             and '@' not in source.source_version
             and source.source_role == 'SIMULATION_SESSION_MATERIAL',
             'analysis_if_session_source_invalid')
    return asdict(source)


def _source_ref(source):
    return _ref('source:', source)


def _session_envelope(source):
    raw = canonical_bytes({'text': source['text']})
    return SourceEnvelope(_source_ref(source), source['source_id'], source['source_role'],
        'cocolon.cmee.analysis_simulation_session_source.v1alpha1', POLICY, 'utf-8',
        POLICY, commitment(POLICY), raw, hashlib.sha256(raw).hexdigest())


def freeze_simulation_source(source, *, authenticated_owner_scope):
    """Freeze a genuine session operation separately from all derived parents."""
    return _session_envelope(_source(source, authenticated_owner_scope))


def _commitments(sources):
    return [dict(source_id=_source_ref(source), source_version=source['source_version'],
                 commitment_id=commitment(source),
                 private_digest_ref='sha256:' + _session_envelope(source).raw_sha256)
            for source in sources]


def _base(projection, private, reference, branch):
    _require(type(projection) is dict and type(private) is dict,
             'analysis_if_base_invalid')
    _require(projection.get('projection_of') == private.get('projection_of') == reference
             and projection.get('artifact_version') == 1
             and projection.get('wire_kind') in {'watashi.map.v2', 'watashi.map.v3'},
             'analysis_if_base_reference_invalid')
    graph = private.get('graph')
    _require(type(graph) is dict and private.get('graph_commitment') == commitment(graph)
             and private.get('schema_version') in {'analysis.private-evidence.v1',
                 'analysis.private-evidence.v2', 'analysis.semantic-private-evidence.v1'}
             and type(private.get('source_members')) is list
             and bool(private['source_members']), 'analysis_if_base_evidence_invalid')
    nodes, edges = projection.get('nodes'), projection.get('edges')
    _require(type(nodes) is list and type(edges) is list
             and type(graph.get('nodes')) is list and type(graph.get('edges')) is list,
             'analysis_if_base_invalid')
    by_node = {node.get('node_ref'): node for node in nodes if type(node) is dict}
    by_edge = {edge.get('edge_ref'): edge for edge in edges if type(edge) is dict}
    _require(len(by_node) == len(nodes) and len(by_edge) == len(edges)
             and None not in by_node and None not in by_edge,
             'analysis_if_base_invalid')
    private_nodes = {node.get('node_ref'): node for node in graph['nodes']}
    private_edges = {edge.get('edge_ref'): edge for edge in graph['edges']}
    _require(set(private_nodes) == set(by_node) and set(private_edges) == set(by_edge),
             'analysis_if_base_evidence_invalid')
    # A v3 interpretation remains a derived map anchor, never original evidence.
    if projection['wire_kind'] == 'watashi.map.v3':
        from .observed_route_realizer import validate_analysis_semantic_projection
        validate_analysis_semantic_projection(projection, reference[9:].split('@')[0])
        _require(all(all(private_nodes[ref].get(key) == value for key, value in node.items())
                     for ref, node in by_node.items())
                 and all(private_edges[ref] == edge for ref, edge in by_edge.items()),
                 'analysis_if_base_evidence_invalid')
    if branch in by_node:
        selected = [branch]
    elif branch in by_edge:
        edge = by_edge[branch]
        selected = (edge.get('endpoint_refs') if 'endpoint_refs' in edge
                    else [edge.get('from_ref'), edge.get('to_ref')])
        _require(type(selected) is list and len(selected) == 2
                 and len(set(selected)) == 2 and all(ref in by_node for ref in selected),
                 'analysis_if_branch_unavailable')
    else:
        raise AnalysisIfRouteError('analysis_if_branch_unavailable')
    anchors = []
    for ref in selected:
        node, evidence = by_node[ref], private_nodes[ref]
        _require(type(evidence.get('evidence_refs')) is list and bool(evidence['evidence_refs']),
                 'analysis_if_base_evidence_invalid')
        label = node.get('title') if projection['wire_kind'] == 'watashi.map.v3' else node.get('visible_label')
        _require(_text(label), 'analysis_if_base_invalid')
        anchors.append(dict(node_ref=ref, visible_label=label, evidence_refs=evidence['evidence_refs']))
    return anchors


def _pending(request, code, prompt):
    clarification = dict(clarification_id=_ref('analysis-if-clarification:',
        [request.request_id, request.base_observed_map_ref, code]), core_id='ANALYSIS',
        parent_request_ref=request.request_id, target_unknown_ref='analysis-if:' + code,
        reason_code=code, prompt_private=prompt, skip_allowed=True, max_answer_count=1,
        answer_source_role='SIMULATION_SESSION_MATERIAL', status='PENDING')
    return AnalysisIfRouteOutcome(EngineStatus.QUESTION_PENDING, (code,),
                                 clarification_json=_json(clarification))


def _base_guard(private):
    # The DB source guard is a lifecycle binding, not a person-authored source.
    return private.get('source_guard')


def _bundle(kind, artifact_id, primary, sources, graphs, parents, base_ref, guard):
    content_hash = commitment([primary, graphs])
    suffix = content_hash[7:]
    return dict(schema_version='cocolon.cmee.generation_artifact_bundle.v1alpha1',
        artifact_id=artifact_id, artifact_version=1, artifact_kind=kind,
        epistemic_partition='HYPOTHETICAL' if kind == IF_KIND else 'USER_SAVED_INTENT',
        core_id='ANALYSIS', product_job='MAP_AND_EXPLORE', source_commitments=_commitments(sources),
        semantic_graph_ref=(primary['candidate_set_id'] + '@1' if kind == IF_KIND
                            else graphs[0]['scenario_graph_id'] + '@1'),
        experience_plan_ref='plan:' + suffix + '@1', parent_artifact_refs=parents,
        derivation_lineage=parents, primary_artifact=primary, companion_artifacts=[],
        realization_trace_ref='trace:' + suffix + '@1',
        machine_quality_report_ref='machine-report:' + suffix + '@1',
        lifecycle_bindings=dict(canonical_content_hash=content_hash,
            version_set={'policy': POLICY, 'base_map': base_ref, 'base_source_guard': guard or ''},
            storage_owner='ANALYSIS_LIFECYCLE', projection_refs=[artifact_id + '@1']),
        status='GENERATED')


def _if_text(projection):
    sections = ['もし別の選択をするとしたら（予測やおすすめの順位ではありません）']
    for scenario in projection['scenarios']:
        sections.append(scenario['visible_label'])
        sections.extend(node['visible_label'] for node in scenario['nodes'])
        if scenario['required_conditions']:
            sections.append('この選択で大切にしたい条件：' + '／'.join(scenario['required_conditions']))
        sections.extend(scenario['frictions'])
        sections.extend(scenario['unmodelled_factors'])
    return '\n\n'.join(sections)


def _saved_text(projection):
    return '\n\n'.join(['保存した関心の方向（実行した記録ではありません）']
                        + ([projection['visible_note']] if projection['visible_note'] else []))


def generate_if_set(request):
    """Compile 1–3 explicit person-authored alternatives, or request missing data.

    One complete intent can form one scenario. More alternatives must have their
    own authentic session sources; a count request never fabricates their meaning.
    """
    try:
        _require(type(request) is AnalysisIfRouteRequest and _text(request.request_id, 200)
                 and _text(request.authenticated_owner_scope, 200)
                 and request.analysis_if_policy_version == POLICY
                 and (request.core_id, request.product_job, request.operation)
                    == ('analysis', 'MAP_AND_EXPLORE', 'ANALYSIS_IF_ROUTE')
                 and type(request.requested_candidate_count) is int
                 and 1 <= request.requested_candidate_count <= 3
                 and type(request.constraints_confirmed) is bool,
                 'analysis_if_request_invalid')
        _require(type(request.base_source_guard) is str and re.fullmatch(
            r'analysis-db-(?:cumulative-)?v1:[0-9a-f]{64}', request.base_source_guard),
            'analysis_if_source_guard_invalid')
        _require(type(request.base_observed_map_ref) is str
                 and _ARTIFACT.fullmatch(request.base_observed_map_ref),
                 'analysis_if_base_reference_invalid')
        if not request.branch_point_id:
            return _pending(request, 'analysis_if_branch_required', 'どの項目や関係から、別の選択を考えたいですか？')
        expected_route = observed_route_reference(request.base_observed_map_ref, request.branch_point_id)
        _require(request.base_route_ref == expected_route, 'analysis_if_route_binding_invalid')
        projection, private = _load(request.base_projection_json), _load(request.base_private_evidence_json)
        anchors = _base(projection, private, request.base_observed_map_ref, request.branch_point_id)
        if request.branch_intent is None:
            return _pending(request, 'analysis_if_intent_required', 'その場で、どういう選択を考えたいですか？')
        owner = request.authenticated_owner_scope
        intent = _source(request.branch_intent, owner)
        _require(type(request.constraints) is tuple and type(request.scenario_choices) is tuple,
                 'analysis_if_session_source_invalid')
        constraints = [_source(source, owner) for source in request.constraints]
        if not constraints and not request.constraints_confirmed:
            return _pending(request, 'analysis_if_constraints_required',
                            '大切にしたい条件や、避けたいことはありますか？ない場合も教えてください。')
        choices = [_source(source, owner) for source in request.scenario_choices]
        if not choices and request.requested_candidate_count == 1:
            choices = [intent]
        if len(choices) != request.requested_candidate_count:
            return _pending(request, 'analysis_if_choices_required',
                            '並べて考えたい別の選択を、それぞれ教えてください。')
        normalized = [re.sub(r'[\s。．.!！?？、,，]+', '', source['text']) for source in choices]
        _require(len(set(normalized)) == len(choices), 'analysis_if_duplicate_choices')
        sources = [intent, *constraints, *choices]
        unique = {}
        for source in sources:
            key = source['source_id']
            _require(key not in unique or unique[key] == source, 'analysis_if_session_source_invalid')
            unique[key] = source
        sources = list(unique.values())
        from emlis_ai_safety_triage import classify_emlis_safety_triage_text
        if any(not classify_emlis_safety_triage_text(source['text']).normal_observation_allowed
               for source in sources):
            return AnalysisIfRouteOutcome(EngineStatus.SEPARATE_SAFETY,
                                           ('analysis_if_separate_safety_required',))
        seed = [POLICY, request.request_id, owner, projection, private, request.branch_point_id,
                sources, request.requested_candidate_count]
        digest = commitment(seed)[7:]
        artifact_id, set_id = 'artifact:' + digest[:32], 'scenario-set:' + digest
        condition_refs = [_source_ref(source) for source in constraints]
        graphs, scenarios, visible = [], [], []
        for index, choice in enumerate(choices, 1):
            suffix = commitment([set_id, index, choice])[7:]
            scenario_ref = 'analysis-if-scenario:' + suffix + '@1'
            graph_id = 'hypothetical:' + suffix
            anchor_refs = ['anchor' + str(i) for i in range(1, len(anchors) + 1)]
            nodes = [dict(node_id=ref, step_kind='BASE_MAP_ANCHOR', origin='OBSERVED_ANCHOR',
                          source_refs=[], unknown_reasons=[])
                     for ref in anchor_refs]
            nodes += [dict(node_id='choice', step_kind='POSSIBLE_CHOICE', origin='USER_CHOICE',
                           source_refs=[_source_ref(choice)], unknown_reasons=[]),
                      dict(node_id='after', step_kind='UNKNOWN_AFTERMATH', origin='UNKNOWN',
                           source_refs=[], unknown_reasons=['AFTERMATH_NOT_OBSERVED'])]
            edges = [dict(edge_id='branch' + str(i), edge_type='SIMULATED_TRANSITION',
                          from_node_ref=ref, to_node_ref='choice', condition_refs=condition_refs)
                     for i, ref in enumerate(anchor_refs, 1)]
            edges.append(dict(edge_id='after', edge_type='SIMULATED_TRANSITION',
                              from_node_ref='choice', to_node_ref='after', condition_refs=condition_refs))
            graph = dict(scenario_graph_id=graph_id, scenario_graph_version=1,
                base_observed_map_ref=request.base_observed_map_ref, base_route_ref=expected_route,
                branch_point_id=request.branch_point_id, branch_intent_source_ref=_source_ref(intent),
                constraint_source_refs=condition_refs, nodes=nodes, edges=edges,
                unmodelled_factors=[UNMODELLED], status='GENERATED')
            graphs.append(graph)
            scenarios.append(dict(kind='ANALYSIS_IF_ROUTE_SIMULATION', wire_kind='watashi.if-route.v1',
                scenario_artifact_ref=scenario_ref, base_observed_map_ref=request.base_observed_map_ref,
                base_route_ref=expected_route, branch_point_id=request.branch_point_id,
                scenario_graph_ref=graph_id + '@1', branch_intent_source_ref=_source_ref(intent),
                condition_refs=condition_refs, unmodelled_factor_refs=[graph_id + ':unknown'],
                text_projection_ref=scenario_ref, visual_projection_ref=scenario_ref,
                scenario_display_label=choice['text']))
            visible.append(dict(scenario_ref=scenario_ref, branch_point_ref=request.branch_point_id,
                visible_label=choice['text'], nodes=[dict(node_ref=ref, origin='OBSERVED_ANCHOR',
                    visible_label=anchor['visible_label']) for ref, anchor in zip(anchor_refs, anchors)]
                    + [dict(node_ref='choice', origin='USER_CHOICE', visible_label=choice['text']),
                       dict(node_ref='after', origin='UNKNOWN', visible_label=UNKNOWN_RESULT)],
                edges=[dict(edge_ref=edge['edge_id'], from_ref=edge['from_node_ref'],
                    to_ref=edge['to_node_ref'], visible_condition_labels=[source['text'] for source in constraints])
                    for edge in edges], required_conditions=[source['text'] for source in constraints],
                frictions=[], unmodelled_factors=[UNMODELLED]))
        primary = dict(kind=IF_KIND, wire_kind='watashi.if-route-set.v1', candidate_set_id=set_id,
            base_observed_map_ref=request.base_observed_map_ref, base_route_ref=expected_route,
            scenarios=scenarios, display_order=[s['scenario_artifact_ref'] for s in scenarios],
            selection_policy='PARALLEL_NOT_RANKED')
        safe = dict(schema_version=IF_SCHEMA, wire_kind='watashi.if-route-set.v1',
            projection_of=artifact_id + '@1', base_observed_map_ref=request.base_observed_map_ref,
            base_route_ref=expected_route, selection_policy='PARALLEL_NOT_RANKED', scenarios=visible)
        payload = dict(schema_version=STORAGE_SCHEMA, owner_scope=owner,
            bundle=_bundle(IF_KIND, artifact_id, primary, sources, graphs,
                [request.base_observed_map_ref], request.base_observed_map_ref, request.base_source_guard),
            base_projection=projection, base_private_evidence=private, session_sources=sources,
            scenario_graphs=graphs, parent_scenario_set=None, model_receipt=None, safe_projection=safe,
            content_text=_if_text(safe))
        payload['integrity'] = commitment(payload)
        artifact = AnalysisIfArtifact(_json(payload))
        _validate_storage(payload, owner)
        return AnalysisIfRouteOutcome(EngineStatus.GENERATED, ('analysis_if_set_generated',), artifact)
    except AnalysisIfRouteError as exc:
        return AnalysisIfRouteOutcome(EngineStatus.REJECTED, (str(exc),))


@dataclass(frozen=True, slots=True, repr=False)
class AnalysisIfArtifact:
    payload_json: str

    @property
    def bundle(self):
        return _load(self.payload_json)['bundle']

    @property
    def artifact_id(self):
        return self.bundle['artifact_id']

    @property
    def reference(self):
        return self.artifact_id + '@1'

    @property
    def kind(self):
        return self.bundle['artifact_kind']

    @property
    def owner_scope(self):
        return _load(self.payload_json)['owner_scope']

    @property
    def base_source_guard(self):
        return self.bundle['lifecycle_bindings']['version_set']['base_source_guard']

    @property
    def base_source_members(self):
        return _load(self.payload_json)['base_private_evidence']['source_members']

    @property
    def scenario_set_reference(self):
        _require(self.kind == IF_KIND)
        return self.bundle['primary_artifact']['candidate_set_id'] + '@1'

    def safe_projection(self, *, authenticated_owner_scope):
        _require(authenticated_owner_scope == self.owner_scope, 'analysis_if_owner_mismatch')
        return _load(self.payload_json)['safe_projection']

    def safe_text_projection(self, *, authenticated_owner_scope):
        _require(authenticated_owner_scope == self.owner_scope, 'analysis_if_owner_mismatch')
        return {'text': _load(self.payload_json)['content_text']}

    def private_evidence(self):
        payload = _load(self.payload_json)
        return dict(schema_version='analysis.if-private-evidence.v1', projection_of=self.reference,
            base_observed_map_ref=payload['base_projection']['projection_of'],
            base_source_guard=self.base_source_guard, source_members=self.base_source_members,
            base_graph=payload['base_private_evidence']['graph'],
            session_sources=payload['session_sources'], scenario_graphs=payload['scenario_graphs'])

    def to_storage(self):
        return _load(self.payload_json)

    @classmethod
    def from_storage(cls, payload, *, authenticated_owner_scope):
        _validate_storage(payload, authenticated_owner_scope)
        return cls(_json(payload))


def save_route_intent(source_artifact, *, authenticated_owner_scope, selected_scenario_ref,
                      selection_source, note_source=None, saved_at):
    _require(type(source_artifact) is AnalysisIfArtifact and source_artifact.kind == IF_KIND,
             'analysis_if_parent_invalid')
    source = source_artifact.to_storage()
    _validate_storage(source, authenticated_owner_scope)
    selected = [s for s in source['bundle']['primary_artifact']['scenarios']
                if s['scenario_artifact_ref'] == selected_scenario_ref]
    _require(len(selected) == 1, 'analysis_if_selection_not_member')
    selection = _source(selection_source, authenticated_owner_scope)
    _require(selection['text'] == selected_scenario_ref, 'analysis_if_selection_source_invalid')
    note = _source(note_source, authenticated_owner_scope) if note_source is not None else None
    _require(note is None or note['source_id'] != selection['source_id'],
             'analysis_if_session_source_invalid')
    try:
        instant = datetime.fromisoformat(saved_at.replace('Z', '+00:00'))
        _require(instant.tzinfo is not None, 'analysis_if_saved_at_invalid')
    except (ValueError, TypeError, AttributeError):
        raise AnalysisIfRouteError('analysis_if_saved_at_invalid') from None
    sources = [selection] + ([note] if note else [])
    selected = selected[0]
    graphs = [graph for graph in source['scenario_graphs']
              if graph['scenario_graph_id'] + '@1' == selected['scenario_graph_ref']]
    _require(len(graphs) == 1)
    primary = dict(kind=SAVED_KIND, wire_kind='watashi.saved-route-intent.v1',
        source_scenario_set_ref=source_artifact.scenario_set_reference,
        selected_scenario_ref=selected_scenario_ref, selection_source_ref=_source_ref(selection),
        user_note_source_ref=_source_ref(note) if note else None, saved_at=saved_at)
    digest = commitment([source_artifact.reference, primary, sources])[7:]
    artifact_id = 'artifact:' + digest[:32]
    safe = dict(schema_version=SAVED_SCHEMA, wire_kind='watashi.saved-route-intent.v1',
        projection_of=artifact_id + '@1', source_scenario_set_ref=primary['source_scenario_set_ref'],
        selected_scenario_ref=selected_scenario_ref, visible_note=note['text'] if note else None,
        saved_at=saved_at)
    payload = dict(schema_version=STORAGE_SCHEMA, owner_scope=authenticated_owner_scope,
        bundle=_bundle(SAVED_KIND, artifact_id, primary, sources, graphs,
            [source_artifact.reference], source['base_projection']['projection_of'], source_artifact.base_source_guard),
        base_projection=source['base_projection'], base_private_evidence=source['base_private_evidence'],
        session_sources=sources, scenario_graphs=graphs, parent_scenario_set=source['bundle'],
        model_receipt=source['model_receipt'], safe_projection=safe, content_text=_saved_text(safe))
    payload['integrity'] = commitment(payload)
    _validate_storage(payload, authenticated_owner_scope)
    return AnalysisIfArtifact(_json(payload))


def _validate_storage_inner(payload, owner):
    _require(type(payload) is dict and set(payload) == _STORAGE_KEYS
             and payload.get('schema_version') == STORAGE_SCHEMA)
    _require(payload['owner_scope'] == owner, 'analysis_if_owner_mismatch')
    _require(payload['integrity'] == commitment({key: value for key, value in payload.items()
                                               if key != 'integrity'}))
    bundle, safe, graphs = payload['bundle'], payload['safe_projection'], payload['scenario_graphs']
    _require(type(bundle) is dict and type(safe) is dict and type(graphs) is list and bool(graphs))
    reference = bundle.get('artifact_id', '') + '@1'
    _require(_ARTIFACT.fullmatch(reference) and bundle.get('artifact_version') == 1
             and bundle.get('core_id') == 'ANALYSIS' and bundle.get('product_job') == 'MAP_AND_EXPLORE'
             and bundle.get('status') == 'GENERATED' and safe.get('projection_of') == reference)
    _require(type(payload['session_sources']) is list and bool(payload['session_sources']))
    sources = [_source(AnalysisSimulationSource(**row), owner) for row in payload['session_sources']]
    _require(bundle.get('source_commitments') == _commitments(sources))
    primary = bundle.get('primary_artifact')
    _require(type(primary) is dict and primary.get('kind') == bundle.get('artifact_kind'))
    base_ref = payload['base_projection'].get('projection_of')
    _require(type(base_ref) is str and _ARTIFACT.fullmatch(base_ref))
    _require(bundle['lifecycle_bindings']['canonical_content_hash'] == commitment([primary, graphs])
             and bundle['lifecycle_bindings']['version_set']['base_map'] == base_ref
             and bundle['lifecycle_bindings']['projection_refs'] == [reference])
    if bundle['artifact_kind'] == IF_KIND:
        _require(bundle['epistemic_partition'] == 'HYPOTHETICAL'
                 and safe.get('wire_kind') == primary.get('wire_kind') == 'watashi.if-route-set.v1'
                 and safe.get('schema_version') == IF_SCHEMA
                 and primary.get('selection_policy') == safe.get('selection_policy') == 'PARALLEL_NOT_RANKED'
                 and payload['parent_scenario_set'] is None
                 and bundle['parent_artifact_refs'] == [base_ref])
        scenarios = primary.get('scenarios')
        _require(type(scenarios) is list and 1 <= len(scenarios) <= 3
                 and len(graphs) == len(scenarios) == len(safe.get('scenarios', [])))
        refs = [scenario['scenario_artifact_ref'] for scenario in scenarios]
        _require(len(set(refs)) == len(refs) and primary['display_order'] == refs
                 and [scenario['scenario_ref'] for scenario in safe['scenarios']] == refs
                 and bundle['semantic_graph_ref'] == primary['candidate_set_id'] + '@1')
        _require(payload['content_text'] == _if_text(safe))
    elif bundle['artifact_kind'] == SAVED_KIND:
        _require(bundle['epistemic_partition'] == 'USER_SAVED_INTENT'
                 and safe.get('wire_kind') == primary.get('wire_kind') == 'watashi.saved-route-intent.v1'
                 and safe.get('schema_version') == SAVED_SCHEMA and len(graphs) == 1
                 and len(sources) == (2 if primary['user_note_source_ref'] else 1)
                 and primary['selection_source_ref'] == _source_ref(sources[0])
                 and sources[0]['text'] == primary['selected_scenario_ref']
                 and (primary['user_note_source_ref'] == _source_ref(sources[1]) if len(sources) == 2
                      else primary['user_note_source_ref'] is None))
        parent = payload['parent_scenario_set']
        _require(type(parent) is dict and parent.get('artifact_kind') == IF_KIND
                 and bundle['parent_artifact_refs'] == [parent['artifact_id'] + '@1']
                 and primary['source_scenario_set_ref'] == parent['primary_artifact']['candidate_set_id'] + '@1')
        selected = [s for s in parent['primary_artifact']['scenarios']
                    if s['scenario_artifact_ref'] == primary['selected_scenario_ref']]
        _require(len(selected) == 1 and selected[0]['scenario_graph_ref'] == graphs[0]['scenario_graph_id'] + '@1'
                 and bundle['semantic_graph_ref'] == selected[0]['scenario_graph_ref'])
        _require(safe['source_scenario_set_ref'] == primary['source_scenario_set_ref']
                 and safe['selected_scenario_ref'] == primary['selected_scenario_ref']
                 and safe['saved_at'] == primary['saved_at']
                 and safe['visible_note'] == (sources[1]['text'] if len(sources) == 2 else None)
                 and payload['content_text'] == _saved_text(safe))
        scenarios = selected
    else:
        raise AnalysisIfRouteError('analysis_if_artifact_invalid')
    for scenario, graph in zip(scenarios, graphs):
        _require(scenario['scenario_graph_ref'] == graph['scenario_graph_id'] + '@1'
                 and scenario['base_observed_map_ref'] == graph['base_observed_map_ref'] == base_ref
                 and scenario['base_route_ref'] == graph['base_route_ref']
                    == observed_route_reference(base_ref, graph['branch_point_id'])
                 and scenario['branch_point_id'] == graph['branch_point_id']
                 and graph['status'] == 'GENERATED')
        _base(payload['base_projection'], payload['base_private_evidence'], base_ref, graph['branch_point_id'])
        _require(all(node.get('origin') in {'OBSERVED_ANCHOR', 'USER_CHOICE', 'SIMULATED_EXTENSION', 'UNKNOWN'} for node in graph['nodes'])
                 and all(edge.get('edge_type') == 'SIMULATED_TRANSITION' for edge in graph['edges']))


def _validate_storage(payload, owner):
    try:
        _validate_storage_inner(payload, owner)
        _validate_projection_graphs(payload)
    except AnalysisIfRouteError:
        raise
    except (KeyError, ValueError, TypeError, IndexError, AttributeError):
        raise AnalysisIfRouteError('analysis_if_artifact_invalid') from None


def _keys(value, names):
    return type(value) is dict and set(value) == set(names.split())


def _validate_projection_graphs(payload):
    """Closed graph/projection binding is checked on reads without an author."""
    bundle, safe = payload['bundle'], payload['safe_projection']
    _require(_keys(bundle, 'schema_version artifact_id artifact_version artifact_kind epistemic_partition '
        'core_id product_job source_commitments semantic_graph_ref experience_plan_ref parent_artifact_refs '
        'derivation_lineage primary_artifact companion_artifacts realization_trace_ref machine_quality_report_ref '
        'lifecycle_bindings status') and bundle['schema_version'] == 'cocolon.cmee.generation_artifact_bundle.v1alpha1')
    _require(_keys(bundle['lifecycle_bindings'], 'canonical_content_hash version_set storage_owner projection_refs')
             and bundle['derivation_lineage'] == bundle['parent_artifact_refs']
             and bundle['companion_artifacts'] == [])
    _require(re.fullmatch(r'analysis-db-(?:cumulative-)?v1:[0-9a-f]{64}',
                          bundle['lifecycle_bindings']['version_set']['base_source_guard']))
    _require(len({s['source_id'] for s in payload['session_sources']}) == len(payload['session_sources']))
    source_refs = {s['source_id'] for s in (bundle if bundle['artifact_kind'] == IF_KIND
                   else payload['parent_scenario_set'])['source_commitments']}
    for graph in payload['scenario_graphs']:
        _require(_keys(graph, 'scenario_graph_id scenario_graph_version base_observed_map_ref base_route_ref '
            'branch_point_id branch_intent_source_ref constraint_source_refs nodes edges unmodelled_factors status')
            and graph['scenario_graph_version'] == 1
            and graph['branch_intent_source_ref'] in source_refs
            and type(graph['constraint_source_refs']) is list
            and set(graph['constraint_source_refs']) <= source_refs)
        nodes, edges = graph['nodes'], graph['edges']
        _require(type(nodes) is list and bool(nodes) and type(edges) is list and bool(edges))
        ids = {node['node_id'] for node in nodes}
        _require(len(ids) == len(nodes) and len({edge['edge_id'] for edge in edges}) == len(edges))
        for node in nodes:
            _require(_keys(node, 'node_id step_kind origin source_refs unknown_reasons')
                     and _text(node['node_id'], 200) and _text(node['step_kind'], 100)
                     and type(node['source_refs']) is list and set(node['source_refs']) <= source_refs
                     and type(node['unknown_reasons']) is list)
            if node['origin'] in {'OBSERVED_ANCHOR', 'UNKNOWN'}:
                _require(node['source_refs'] == [])
            if node['origin'] == 'UNKNOWN':
                _require(bool(node['unknown_reasons']))
            if node['origin'] == 'USER_CHOICE':
                _require(bool(node['source_refs']))
        for edge in edges:
            _require(_keys(edge, 'edge_id edge_type from_node_ref to_node_ref condition_refs')
                     and edge['from_node_ref'] in ids and edge['to_node_ref'] in ids
                     and edge['from_node_ref'] != edge['to_node_ref']
                     and type(edge['condition_refs']) is list)
    if bundle['artifact_kind'] == IF_KIND:
        _require(_keys(safe, 'schema_version wire_kind projection_of base_observed_map_ref base_route_ref '
            'selection_policy scenarios')
            and _keys(bundle['primary_artifact'], 'kind wire_kind candidate_set_id base_observed_map_ref '
                'base_route_ref scenarios display_order selection_policy'))
        for public, graph in zip(safe['scenarios'], payload['scenario_graphs']):
            _require(_keys(public, 'scenario_ref branch_point_ref visible_label nodes edges required_conditions '
                'frictions unmodelled_factors') and public['branch_point_ref'] == graph['branch_point_id']
                and _text(public['visible_label'])
                and len(public['nodes']) == len(graph['nodes']) and len(public['edges']) == len(graph['edges']))
            for shown, node in zip(public['nodes'], graph['nodes']):
                _require(_keys(shown, 'node_ref origin visible_label')
                         and shown['node_ref'] == node['node_id'] and shown['origin'] == node['origin']
                         and _text(shown['visible_label']))
            for shown, edge in zip(public['edges'], graph['edges']):
                _require(_keys(shown, 'edge_ref from_ref to_ref visible_condition_labels')
                         and (shown['edge_ref'], shown['from_ref'], shown['to_ref'])
                            == (edge['edge_id'], edge['from_node_ref'], edge['to_node_ref'])
                         and type(shown['visible_condition_labels']) is list)
            for field in ('required_conditions', 'frictions', 'unmodelled_factors'):
                _require(type(public[field]) is list and all(_text(value) for value in public[field]))
    else:
        _require(_keys(safe, 'schema_version wire_kind projection_of source_scenario_set_ref '
            'selected_scenario_ref visible_note saved_at')
            and _keys(bundle['primary_artifact'], 'kind wire_kind source_scenario_set_ref selected_scenario_ref '
                'selection_source_ref user_note_source_ref saved_at'))
    receipt = payload['model_receipt']
    if receipt is not None:
        _require(_keys(receipt, 'request_ref messages_sha256 raw_sha256 finish_reason raw')
                 and receipt['finish_reason'] == 'stop' and type(receipt['raw']) is str
                 and len(receipt['raw'].encode('utf-8')) <= 262144
                 and hashlib.sha256(receipt['raw'].encode('utf-8')).hexdigest() == receipt['raw_sha256'])
        _validate_receipt_binding(payload)
    elif bundle['artifact_kind'] == IF_KIND:
        # The non-model arm also has exact authored text, not editable labels.
        by_source = {_source_ref(source): source for source in payload['session_sources']}
        for public, graph in zip(safe['scenarios'], payload['scenario_graphs']):
            anchors = _base(payload['base_projection'], payload['base_private_evidence'],
                            graph['base_observed_map_ref'], graph['branch_point_id'])
            shown_anchors = [node['visible_label'] for node in public['nodes'] if node['origin'] == 'OBSERVED_ANCHOR']
            _require(shown_anchors == [anchor['visible_label'] for anchor in anchors])
            _require(public['required_conditions'] == [by_source[ref]['text'] for ref in graph['constraint_source_refs']]
                     and public['frictions'] == [] and public['unmodelled_factors'] == [UNMODELLED])
            for shown, node in zip(public['nodes'], graph['nodes']):
                if node['origin'] == 'USER_CHOICE':
                    _require(len(node['source_refs']) == 1
                             and shown['visible_label'] == by_source[node['source_refs'][0]]['text']
                             and public['visible_label'] == shown['visible_label'])
                elif node['origin'] == 'UNKNOWN':
                    _require(shown['visible_label'] == UNKNOWN_RESULT)
                else:
                    _require(node['origin'] == 'OBSERVED_ANCHOR')


def _validate_receipt_binding(payload):
    """Validate saved model-to-graph correspondence; do not re-author a view."""
    bundle = payload['bundle']
    parent = bundle if bundle['artifact_kind'] == IF_KIND else payload['parent_scenario_set']
    primary = parent['primary_artifact']
    packet = _load(payload['model_receipt']['raw'])
    _require(_keys(packet, 'schema_version scenarios clarification')
             and packet['schema_version'] == IF_MODEL_SCHEMA and packet['clarification'] is None
             and type(packet['scenarios']) is list
             and len(packet['scenarios']) == len(primary['scenarios']))
    refs = {i: source['source_id'] for i, source in enumerate(parent['source_commitments'], 1)}
    proposals = {}
    for proposed, scenario in zip(packet['scenarios'], primary['scenarios']):
        _require(_keys(proposed, 'scenario_id label nodes edges required_conditions frictions unmodelled_factors'))
        ref = _ref('analysis-if-scenario:', [primary['candidate_set_id'], proposed['scenario_id']])
        _require(ref == scenario['scenario_artifact_ref'] and ref not in proposals
                 and proposed['label'] == scenario['scenario_display_label'])
        proposals[ref] = proposed
    scenarios = (bundle['primary_artifact']['scenarios'] if bundle['artifact_kind'] == IF_KIND else
                 [s for s in primary['scenarios'] if s['scenario_artifact_ref'] == bundle['primary_artifact']['selected_scenario_ref']])
    shown = (payload['safe_projection']['scenarios'] if bundle['artifact_kind'] == IF_KIND else [None])
    for scenario, graph, public in zip(scenarios, payload['scenario_graphs'], shown):
        proposed = proposals[scenario['scenario_artifact_ref']]
        _require(len(proposed['nodes']) == len(graph['nodes']) and len(proposed['edges']) == len(graph['edges'])
                 and graph['unmodelled_factors'] == proposed['unmodelled_factors'])
        anchors = {anchor['node_ref']: anchor for anchor in _base(payload['base_projection'],
            payload['base_private_evidence'], graph['base_observed_map_ref'], graph['branch_point_id'])}
        for raw, node in zip(proposed['nodes'], graph['nodes']):
            _require(_keys(raw, 'node_id step_kind origin text anchor_ref source_refs unknown_reasons')
                     and (node['node_id'], node['step_kind'], node['origin'], node['unknown_reasons'])
                        == (raw['node_id'], raw['step_kind'], raw['origin'], raw['unknown_reasons'])
                     and node['source_refs'] == _model_source_numbers(raw['source_refs'], refs))
            if raw['origin'] == 'OBSERVED_ANCHOR':
                _require(raw['anchor_ref'] in anchors and raw['text'] == anchors[raw['anchor_ref']]['visible_label'])
            if raw['origin'] == 'USER_CHOICE' and bundle['artifact_kind'] == IF_KIND:
                # A substring can discard negation, a condition or a reservation.
                # Only an exact complete authored field may claim USER_CHOICE.
                by_source = {_source_ref(source): source for source in payload['session_sources']}
                _require(len(node['source_refs']) == 1
                         and raw['text'] == by_source[node['source_refs'][0]]['text'],
                         'analysis_if_model_choice_unbound')
        condition_labels = {condition['condition_id']: condition['text'] for condition in proposed['required_conditions']}
        for raw, edge in zip(proposed['edges'], graph['edges']):
            _require(_keys(raw, 'edge_id from to condition_refs')
                     and (edge['edge_id'], edge['from_node_ref'], edge['to_node_ref'])
                        == (raw['edge_id'], raw['from'], raw['to'])
                     and edge['condition_refs'] == [graph['scenario_graph_id'] + ':condition:' + ref for ref in raw['condition_refs']])
        if public is not None:
            _require(public['visible_label'] == proposed['label']
                     and public['required_conditions'] == [row['text'] for row in proposed['required_conditions']]
                     and public['frictions'] == proposed['frictions']
                     and public['unmodelled_factors'] == proposed['unmodelled_factors'])
            _require([row['visible_label'] for row in public['nodes']] == [row['text'] for row in proposed['nodes']])
            _require([edge['visible_condition_labels'] for edge in public['edges']] ==
                     [[condition_labels[ref] for ref in edge['condition_refs']] for edge in proposed['edges']])


def from_storage(payload, *, authenticated_owner_scope):
    """Validate saved bytes without invoking an author, model or generation."""
    return AnalysisIfArtifact.from_storage(payload, authenticated_owner_scope=authenticated_owner_scope)


generate_if_route = generate_if_set
compile_saved_route_intent = save_route_intent


IF_MODEL_SCHEMA = 'cocolon.analysis.if-candidates.model.v1'
_IF_MODEL_INSTRUCTION_LEGACY = '''あなたはCocolonのAnalysis IF候補を作ります。結果は仮説であり、未来予測、成功保証、正解、おすすめ順位ではありません。
base_mapは保存されたAIの読み取りです。本人の確定事実や新しい原入力ではありません。OBSERVED_ANCHORのtextは渡されたanchorのvisible_labelを完全に保ちます。
本人のbranch_intentとconstraintsは別の真正なsourceです。USER_CHOICEのtextは一つのfieldの全文と完全一致させ、source_refsもそのfield一つだけにします。否定・条件・留保を落とす部分引用や複数fieldの合成を本人選択にしません。AIが考えた別の行動、言い換え、必要条件はSIMULATED_EXTENSIONとして明示します。本人が選択済み、実行済み、結果が生じたとは書きません。
意味の異なる候補を要求数だけ並列に作り、rank/score/probability/best/optimalityは出しません。各候補には元mapのanchor、仮の選択、結果不明のUNKNOWNを含め、必要条件・引っかかり・分からない要因を表示します。共起や元の関係線を因果や順序へ変換しません。
本人の意図や制約が分からなければclarificationを返し、空graphで成功しません。診断、隠れた動機、固定人格や未来の断定は作りません。
JSONのみを返します。schema_versionはcocolon.analysis.if-candidates.model.v1。最上位keysはschema_version,scenarios,clarificationです。
scenariosの各objectはscenario_id,label,nodes,edges,required_conditions,frictions,unmodelled_factors。
nodeはnode_id,step_kind,origin,text,anchor_ref,source_refs,unknown_reasons。originはOBSERVED_ANCHOR/USER_CHOICE/SIMULATED_EXTENSION/UNKNOWN。anchor_refはOBSERVED_ANCHORだけ渡されたnode_ref、それ以外null。source_refsは本人材料のfield番号だけ、UNKNOWNとanchorでは空配列。
edgeはedge_id,from,to,condition_refs。required_conditionsはcondition_id,text,source_refsのobject配列、condition_refsはそのcondition_id。edgesは仮想上の接続だけです。
frictions,unmodelled_factorsは文字列配列。各候補にUNKNOWN nodeとunmodelled_factorsを必ず含めます。clarificationはnull、またはreason_codeとpromptのobjectです。その場合scenariosは空配列です。'''

_IF_MODEL_INSTRUCTION_PERSON_ALTERNATIVES = _IF_MODEL_INSTRUCTION_LEGACY + '''
各scenarioのnodesは、最初に渡された元mapのanchorをOBSERVED_ANCHORとしてそのまま置き、その後に今回の仮の選択や手順、最後に結果不明のUNKNOWNを置きます。元mapのanchorを省略しません。
PERSON_ALTERNATIVEがある場合、本人が提示した各代替案を別々のscenarioへ対応させます。複数案を比べる行為自体を一つの代替案にせず、本人がその案の実行を決めたとも書きません。
UNKNOWNには、その仮の進め方で分からない条件や結果を記します。「実行したか不明」という反復だけで代用しません。指定されたJSON field順を保ち、次のobjectの構文やkey名を説明用文字列へ混ぜません。'''

_IF_MODEL_INSTRUCTION_UNKNOWN_ORDER = _IF_MODEL_INSTRUCTION_PERSON_ALTERNATIVES + '''
不明・未観測の内容を述べるnodeはoriginをUNKNOWNにし、source_refsは空、unknown_reasonsには分からない理由を一つ以上置きます。SIMULATED_EXTENSIONはAIが仮に加える具体的な手順であり、不明や未記載の説明を入れる場所ではありません。そのunknown_reasonsは空配列にします。
本人案に明示された作業、先後関係、時間配分、否定や条件は既知の材料として保ちます。資料の内容・量や到達できる結果が不明でも、書かれた作業や順序そのものを「未提示」「明示されていない」と説明しません。既知の手順と未知の条件・結果を分けます。
本人案の全文を一つのUSER_CHOICE nodeで表せる場合、手順を重ねて分解したり、同じ内容の補助nodeを増やす必要はありません。各scenarioは元mapのanchor、その本人案、結果や条件が不明なUNKNOWNを含めます。'''

_IF_MODEL_INSTRUCTION_PERSON_OPTIONS = _IF_MODEL_INSTRUCTION_UNKNOWN_ORDER + '''
要求数と同数の異なるPERSON_ALTERNATIVEがある場合だけ、各scenarioのlabelとUSER_CHOICEを対応する本人案の全文にします。既知の手順を言い換えたSIMULATED_EXTENSIONは作りません。本人案をそのまま示した上で、未知の条件・結果だけをUNKNOWN、必要条件、frictions、unmodelled_factorsに分けます。それ以外の仮の手順生成や必要確認とは区別します。'''

_IF_MODEL_INSTRUCTION_FIXED_PERSON = _IF_MODEL_INSTRUCTION_PERSON_OPTIONS + '''
本人案が要求数そろう場合、nodesは渡された全anchorをanchor_1等として置き、choiceにその本人案、unknownにUNKNOWN_AFTERMATHを置きます。edgesは各anchorからchoice、choiceからunknownへの仮想上の接続です。UNKNOWNのtextは「何が分からないか」の説明にし、本人の意向文を貼り付けません。各候補のUNKNOWN・必要条件・frictions・unmodelled_factorsには、その案の手順と共通制約だけを使い、別の本人案の行動・目的を混ぜません。'''


_IF_MODEL_INSTRUCTION_STANDARD = _IF_MODEL_INSTRUCTION_FIXED_PERSON + '''
本人案が要求数そろわない通常入力では、本人の意向と制約に沿う、意味の異なる具体的な進め方を要求数だけ作ります。本人が書いていない提案はSIMULATED_EXTENSIONです。意向文の反復だけを複数の案にせず、同じ内容のlabelだけを変えて水増ししません。本人の条件文は行動の選択ではありません。
どの経路でも、全anchorの後にchoice、最後にunknownを置き、各anchorからchoice、choiceからunknownへ仮に接続します。既知のCONSTRAINTは全文とfield番号をrequired_conditionsにそのまま保持します。追加で必要かもしれない条件や負荷はUNKNOWN、frictions、unmodelled_factorsに分け、本人が既に書いた条件を不明と扱いません。
labelはその案の具体的な進め方を簡潔な日本語で表します。UNKNOWNには案を試したときに分からない結果や条件を具体的に記し、「未定」や「不明」の単語だけ、本人の意向文のコピー、他の候補の作業で代用しません。'''


_IF_MODEL_INSTRUCTION = _IF_MODEL_INSTRUCTION_STANDARD + '''
BRANCH_INTENTは比較したい意向であり、それ自体を各案のUSER_CHOICEへ繰り返しません。本人案のない通常入力のchoiceは、各案の具体的な仮の進め方をSIMULATED_EXTENSIONとして作ります。labelとchoiceは同じ進め方を表し、見出しだけ変えてgraphを同一内容にしません。USER_CHOICEにできるのはPERSON_ALTERNATIVEの全文だけです。
UNKNOWNは、その案で実際に理解できる範囲や生じる結果が未観測であることを表します。将来の結果を「本人が成果を書いていない」という記録不足へ読み替えず、その案の行動に即して説明します。'''


def prepare_if_model_request(request, *, response=None):
    """Freeze owned material before the application makes one model request."""
    try:
        _require(type(request) is AnalysisIfRouteRequest and _text(request.request_id, 200)
                 and _text(request.authenticated_owner_scope, 200)
                 and request.analysis_if_policy_version == POLICY
                 and (request.core_id, request.product_job, request.operation)
                    == ('analysis', 'MAP_AND_EXPLORE', 'ANALYSIS_IF_ROUTE')
                 and type(request.requested_candidate_count) is int
                 and 1 <= request.requested_candidate_count <= 3
                 and type(request.constraints_confirmed) is bool,
                 'analysis_if_request_invalid')
        _require(type(request.base_source_guard) is str and re.fullmatch(
            r'analysis-db-(?:cumulative-)?v1:[0-9a-f]{64}', request.base_source_guard),
            'analysis_if_source_guard_invalid')
        if not request.branch_point_id:
            return _pending(request, 'analysis_if_branch_required', 'どの項目や関係から、別の選択を考えたいですか？')
        route = observed_route_reference(request.base_observed_map_ref, request.branch_point_id)
        _require(request.base_route_ref == route, 'analysis_if_route_binding_invalid')
        projection, private = _load(request.base_projection_json), _load(request.base_private_evidence_json)
        anchors = _base(projection, private, request.base_observed_map_ref, request.branch_point_id)
        if request.branch_intent is None:
            return _pending(request, 'analysis_if_intent_required', 'その場で、どういう選択を考えたいですか？')
        owner = request.authenticated_owner_scope
        intent = _source(request.branch_intent, owner)
        _require(type(request.constraints) is tuple and type(request.scenario_choices) is tuple,
                 'analysis_if_session_source_invalid')
        constraints = [_source(source, owner) for source in request.constraints]
        choices = [_source(source, owner) for source in request.scenario_choices]
        if not constraints and not request.constraints_confirmed:
            return _pending(request, 'analysis_if_constraints_required',
                            '大切にしたい条件や、避けたいことはありますか？ない場合も教えてください。')
        sources, seen = [], {}
        for source in [intent, *constraints, *choices]:
            _require(source['source_id'] not in seen or seen[source['source_id']] == source,
                     'analysis_if_session_source_invalid')
            if source['source_id'] not in seen:
                sources.append(source)
                seen[source['source_id']] = source
        from emlis_ai_safety_triage import classify_emlis_safety_triage_text
        if any(not classify_emlis_safety_triage_text(source['text']).normal_observation_allowed for source in sources):
            return AnalysisIfRouteOutcome(EngineStatus.SEPARATE_SAFETY, ('analysis_if_separate_safety_required',))
        fields = [dict(field=i, source_role=source['source_role'], text=source['text'],
                       purpose=('BRANCH_INTENT' if source == intent else
                                'CONSTRAINT' if source in constraints else 'PERSON_ALTERNATIVE'))
                  for i, source in enumerate(sources, 1)]
        material = dict(base_map_kind='DERIVED_AI_MAP_ANCHOR',
            branch_point_ref=request.branch_point_id,
            anchors=[{'node_ref': anchor['node_ref'], 'visible_label': anchor['visible_label']} for anchor in anchors],
            fields=fields, requested_candidate_count=request.requested_candidate_count,
            constraints_confirmed=request.constraints_confirmed, model_schema=IF_MODEL_SCHEMA)
        seed = dict(projection=projection, private=private, anchors=anchors, sources=sources,
                    intent_ref=_source_ref(intent), constraint_refs=[_source_ref(source) for source in constraints])
        if response is not None:
            from .semantic_admission import AnalysisModelQuotedParentUnitsResponse
            _require(type(response) is AnalysisModelQuotedParentUnitsResponse,
                     'analysis_if_model_response_unbound')
        for instruction in (_IF_MODEL_INSTRUCTION, _IF_MODEL_INSTRUCTION_STANDARD,
                            _IF_MODEL_INSTRUCTION_FIXED_PERSON,
                            _IF_MODEL_INSTRUCTION_PERSON_OPTIONS,
                            _IF_MODEL_INSTRUCTION_UNKNOWN_ORDER,
                            _IF_MODEL_INSTRUCTION_PERSON_ALTERNATIVES,
                            _IF_MODEL_INSTRUCTION_LEGACY):
            messages = [dict(role='system', content=instruction), dict(role='user', content=_json(material))]
            request_ref = 'analysis-if-request:' + commitment([asdict(request), seed, messages])[7:]
            if response is None or (response.request_ref == request_ref
                    and response.messages_sha256 == commitment(messages)[7:]):
                return AnalysisIfModelPrepared(request, request_ref, _json(messages), _json(seed))
        raise AnalysisIfRouteError('analysis_if_model_response_unbound')
    except AnalysisIfRouteError as exc:
        return AnalysisIfRouteOutcome(EngineStatus.REJECTED, (str(exc),))
    except (KeyError, TypeError, ValueError, IndexError, AttributeError):
        return AnalysisIfRouteOutcome(EngineStatus.REJECTED, ('analysis_if_request_invalid',))


def _model_surface(value, maximum=2000):
    _require(_text(value, maximum), 'analysis_if_model_packet_invalid')
    _require(not re.search(r'必ず(?:成功|改善|治|良く)|絶対に(?:成功|改善|治|良く)|最適な(?:選択|ルート)|'
                          r'成功確率|[0-9０-９]+\s*[%％]', value), 'analysis_if_model_forbidden_assertion')
    return value


def admit_if_model_response(prepared, response):
    """Admit a bound proposal as hypothetical, with no model-to-user promotion."""
    try:
        _require(type(prepared) is AnalysisIfModelPrepared, 'analysis_if_model_input_invalid')
        from .semantic_admission import AnalysisModelQuotedParentUnitsResponse
        _require(type(response) is AnalysisModelQuotedParentUnitsResponse
                 and response.request_ref == prepared.request_ref
                 and response.messages_sha256 == commitment(prepared.messages())[7:]
                 and response.finish_reason == 'stop' and type(response.raw) is str
                 and len(response.raw.encode('utf-8')) <= 262144
                 and response.raw_sha256 == hashlib.sha256(response.raw.encode('utf-8')).hexdigest(),
                 'analysis_if_model_response_unbound')
        expected = prepare_if_model_request(prepared.request, response=response)
        _require(type(expected) is AnalysisIfModelPrepared and expected == prepared,
                 'analysis_if_model_input_unbound')
        packet = _load(response.raw)
        _require(_keys(packet, 'schema_version scenarios clarification')
                 and packet['schema_version'] == IF_MODEL_SCHEMA and type(packet['scenarios']) is list,
                 'analysis_if_model_packet_invalid')
        if packet['clarification'] is not None:
            question = packet['clarification']
            _require(not packet['scenarios'] and _keys(question, 'reason_code prompt')
                     and question['reason_code'] in {'BRANCH_INTENT_UNCLEAR', 'CONSTRAINT_UNCLEAR', 'ALTERNATIVES_UNCLEAR'},
                     'analysis_if_model_packet_invalid')
            return _pending(prepared.request, 'analysis_if_' + question['reason_code'].lower(),
                            _model_surface(question['prompt'], 300))
        if len(packet['scenarios']) < prepared.request.requested_candidate_count:
            return _pending(prepared.request, 'analysis_if_choices_required',
                            '並べて考える選択をもう少し具体的にするため、大切にしたいことを教えてください。')
        _require(len(packet['scenarios']) == prepared.request.requested_candidate_count,
                 'analysis_if_model_packet_invalid')
        return _realize_model_set(prepared, response, packet)
    except AnalysisIfRouteError as exc:
        return AnalysisIfRouteOutcome(EngineStatus.REJECTED, (str(exc),))
    except (KeyError, TypeError, ValueError, IndexError, AttributeError):
        return AnalysisIfRouteOutcome(EngineStatus.REJECTED, ('analysis_if_model_packet_invalid',))


def _realize_model_set(prepared, response, packet):
    request, seed = prepared.request, _load(prepared.base_seed_json)
    sources, anchors = seed['sources'], {a['node_ref']: a for a in seed['anchors']}
    source_refs = {i: _source_ref(source) for i, source in enumerate(sources, 1)}
    suffix = commitment([prepared.request_ref, response.raw_sha256])[7:]
    artifact_id, set_id = 'artifact:' + suffix[:32], 'scenario-set:' + suffix
    scenarios, graphs, shown = [], [], []
    ids, labels = set(), set()
    for proposal in packet['scenarios']:
        _require(_keys(proposal, 'scenario_id label nodes edges required_conditions frictions unmodelled_factors'),
                 'analysis_if_model_packet_invalid')
        _require(_text(proposal['scenario_id'], 100) and proposal['scenario_id'] not in ids,
                 'analysis_if_model_packet_invalid')
        ids.add(proposal['scenario_id'])
        label = _model_surface(proposal['label'])
        normal = re.sub(r'[\s。．.!！?？、,，]+', '', label)
        _require(normal not in labels, 'analysis_if_duplicate_choices')
        labels.add(normal)
        for key in ('nodes', 'edges', 'required_conditions', 'frictions', 'unmodelled_factors'):
            _require(type(proposal[key]) is list, 'analysis_if_model_packet_invalid')
        _require(1 <= len(proposal['nodes']) <= 24 and 1 <= len(proposal['edges']) <= 48
                 and 1 <= len(proposal['unmodelled_factors']) <= 12
                 and len(proposal['required_conditions']) <= 12 and len(proposal['frictions']) <= 12,
                 'analysis_if_model_packet_invalid')
        digest = commitment([set_id, proposal['scenario_id']])[7:]
        scenario_ref, graph_id = 'analysis-if-scenario:' + digest + '@1', 'hypothetical:' + digest
        condition_ids, conditions = set(), []
        for condition in proposal['required_conditions']:
            _require(_keys(condition, 'condition_id text source_refs')
                     and _text(condition['condition_id'], 100) and condition['condition_id'] not in condition_ids,
                     'analysis_if_model_packet_invalid')
            condition_ids.add(condition['condition_id'])
            _model_source_numbers(condition['source_refs'], source_refs)
            conditions.append(_model_surface(condition['text']))
        nodes, visible_nodes, node_ids, origins = [], [], set(), set()
        for node in proposal['nodes']:
            _require(_keys(node, 'node_id step_kind origin text anchor_ref source_refs unknown_reasons')
                     and _text(node['node_id'], 100) and node['node_id'] not in node_ids
                     and _text(node['step_kind'], 100) and node['origin'] in
                        {'OBSERVED_ANCHOR', 'USER_CHOICE', 'SIMULATED_EXTENSION', 'UNKNOWN'}
                     and type(node['unknown_reasons']) is list
                     and all(_text(reason, 200) for reason in node['unknown_reasons']),
                     'analysis_if_model_packet_invalid')
            node_ids.add(node['node_id'])
            origins.add(node['origin'])
            refs = _model_source_numbers(node['source_refs'], source_refs)
            text = _model_surface(node['text'])
            if node['origin'] == 'OBSERVED_ANCHOR':
                _require(node['anchor_ref'] in anchors and not refs
                         and text == anchors[node['anchor_ref']]['visible_label'],
                         'analysis_if_model_anchor_unbound')
            else:
                _require(node['anchor_ref'] is None, 'analysis_if_model_anchor_unbound')
            if node['origin'] == 'USER_CHOICE':
                _require(len(refs) == 1 and text == sources[node['source_refs'][0] - 1]['text'],
                         'analysis_if_model_choice_unbound')
            if node['origin'] == 'UNKNOWN':
                _require(not refs and bool(node['unknown_reasons']), 'analysis_if_model_packet_invalid')
            nodes.append(dict(node_id=node['node_id'], step_kind=node['step_kind'], origin=node['origin'],
                              source_refs=refs, unknown_reasons=node['unknown_reasons']))
            visible_nodes.append(dict(node_ref=node['node_id'], origin=node['origin'], visible_label=text))
        _require('OBSERVED_ANCHOR' in origins and 'UNKNOWN' in origins
                 and bool(origins & {'USER_CHOICE', 'SIMULATED_EXTENSION'}), 'analysis_if_model_packet_invalid')
        edges, visible_edges, edge_ids = [], [], set()
        for edge in proposal['edges']:
            _require(_keys(edge, 'edge_id from to condition_refs') and _text(edge['edge_id'], 100)
                     and edge['edge_id'] not in edge_ids and edge['from'] in node_ids and edge['to'] in node_ids
                     and edge['from'] != edge['to'] and type(edge['condition_refs']) is list
                     and all(type(ref) is str and ref in condition_ids for ref in edge['condition_refs'])
                     and len(set(edge['condition_refs'])) == len(edge['condition_refs']),
                     'analysis_if_model_packet_invalid')
            edge_ids.add(edge['edge_id'])
            refs = [graph_id + ':condition:' + ref for ref in edge['condition_refs']]
            edges.append(dict(edge_id=edge['edge_id'], edge_type='SIMULATED_TRANSITION',
                from_node_ref=edge['from'], to_node_ref=edge['to'], condition_refs=refs))
            by_condition = {row['condition_id']: row['text'] for row in proposal['required_conditions']}
            visible_edges.append(dict(edge_ref=edge['edge_id'], from_ref=edge['from'], to_ref=edge['to'],
                visible_condition_labels=[by_condition[ref] for ref in edge['condition_refs']]))
        factors = [_model_surface(text) for text in proposal['unmodelled_factors']]
        frictions = [_model_surface(text) for text in proposal['frictions']]
        graph = dict(scenario_graph_id=graph_id, scenario_graph_version=1,
            base_observed_map_ref=request.base_observed_map_ref, base_route_ref=request.base_route_ref,
            branch_point_id=request.branch_point_id, branch_intent_source_ref=seed['intent_ref'],
            constraint_source_refs=seed['constraint_refs'], nodes=nodes, edges=edges,
            unmodelled_factors=factors, status='GENERATED')
        graphs.append(graph)
        scenarios.append(dict(kind='ANALYSIS_IF_ROUTE_SIMULATION', wire_kind='watashi.if-route.v1',
            scenario_artifact_ref=scenario_ref, base_observed_map_ref=request.base_observed_map_ref,
            base_route_ref=request.base_route_ref, branch_point_id=request.branch_point_id,
            scenario_graph_ref=graph_id + '@1', branch_intent_source_ref=seed['intent_ref'],
            condition_refs=[graph_id + ':condition:' + row['condition_id'] for row in proposal['required_conditions']],
            unmodelled_factor_refs=[graph_id + ':unknown:' + str(i) for i in range(len(factors))],
            text_projection_ref=scenario_ref, visual_projection_ref=scenario_ref, scenario_display_label=label))
        shown.append(dict(scenario_ref=scenario_ref, branch_point_ref=request.branch_point_id, visible_label=label,
            nodes=visible_nodes, edges=visible_edges, required_conditions=conditions, frictions=frictions,
            unmodelled_factors=factors))
    primary = dict(kind=IF_KIND, wire_kind='watashi.if-route-set.v1', candidate_set_id=set_id,
        base_observed_map_ref=request.base_observed_map_ref, base_route_ref=request.base_route_ref,
        scenarios=scenarios, display_order=[scenario['scenario_artifact_ref'] for scenario in scenarios],
        selection_policy='PARALLEL_NOT_RANKED')
    safe = dict(schema_version=IF_SCHEMA, wire_kind='watashi.if-route-set.v1', projection_of=artifact_id + '@1',
        base_observed_map_ref=request.base_observed_map_ref, base_route_ref=request.base_route_ref,
        selection_policy='PARALLEL_NOT_RANKED', scenarios=shown)
    payload = dict(schema_version=STORAGE_SCHEMA, owner_scope=request.authenticated_owner_scope,
        bundle=_bundle(IF_KIND, artifact_id, primary, sources, graphs, [request.base_observed_map_ref],
            request.base_observed_map_ref, request.base_source_guard), base_projection=seed['projection'],
        base_private_evidence=seed['private'], session_sources=sources, scenario_graphs=graphs,
        parent_scenario_set=None, safe_projection=safe, content_text=_if_text(safe),
        model_receipt=dict(request_ref=response.request_ref, messages_sha256=response.messages_sha256,
            raw_sha256=response.raw_sha256, finish_reason=response.finish_reason, raw=response.raw))
    payload['integrity'] = commitment(payload)
    _validate_storage(payload, request.authenticated_owner_scope)
    return AnalysisIfRouteOutcome(EngineStatus.GENERATED, ('analysis_if_model_set_generated',),
                                 AnalysisIfArtifact(_json(payload)))


def _model_source_numbers(numbers, refs):
    _require(type(numbers) is list and all(type(number) is int and number in refs for number in numbers)
             and len(set(numbers)) == len(numbers), 'analysis_if_model_source_unbound')
    return [refs[number] for number in numbers]
