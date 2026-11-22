"""Real saved-map bindings with synthetic proposals; no model quality claim."""
from copy import deepcopy
from dataclasses import replace
import hashlib
import json

import pytest

from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.cores.analysis.if_route_contracts import (
    AnalysisIfModelPrepared, AnalysisIfRouteRequest, AnalysisSimulationSource)
from cocolon_meaning_experience_engine.cores.analysis import if_route_realizer as if_route
from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import AnalysisModelQuotedParentUnitsResponse
from cocolon_meaning_experience_engine.cores.analysis.source_adapter import commitment
from test_analysis_semantic_map import build
from test_analysis_cumulative import OWNER, source_snapshot


def source(identifier, text, owner=OWNER):
    return AnalysisSimulationSource(identifier, owner, text)


def request(*, count=1, branch='n1', legacy=False):
    if legacy:
        import analysis_cumulative_service
        from analysis_observed_service import private_storage_evidence
        artifact, _ = analysis_cumulative_service.build_cumulative_map(OWNER, source_snapshot(2))
        private = private_storage_evidence(artifact)
    else:
        _, artifact, _ = build()
        private = artifact.private_evidence()
    projection = artifact.safe_projection(authenticated_owner_scope=OWNER)
    return AnalysisIfRouteRequest('if-operation-1', OWNER, artifact.reference,
        if_route.observed_route_reference(artifact.reference, branch), branch,
        json.dumps(projection, ensure_ascii=False), json.dumps(private, ensure_ascii=False),
        base_source_guard='analysis-db-cumulative-v1:' + 'a' * 64,
        branch_intent=source('intent', '次は自分の意見を言ってみたい。'),
        constraints=(source('constraint', '相手が話している間は、話を遮りたくない。'),),
        requested_candidate_count=count)


def packet(prepared, count=None):
    materials = json.loads(prepared.messages()[1]['content'])
    anchor = materials['anchors'][0]
    scenarios = []
    for i in range(count or prepared.request.requested_candidate_count):
        scenarios.append(dict(scenario_id='s' + str(i + 1), label=f'選択肢{i + 1}を仮に考える',
            nodes=[dict(node_id='anchor', step_kind='BASE_MAP_ANCHOR', origin='OBSERVED_ANCHOR',
                text=anchor['visible_label'], anchor_ref=anchor['node_ref'], source_refs=[], unknown_reasons=[]),
                dict(node_id='choice', step_kind='POSSIBLE_CHOICE', origin='SIMULATED_EXTENSION',
                    text=f'相手の話が終わった時に、方法{i + 1}で意見を伝えることを考える。',
                    anchor_ref=None, source_refs=[1], unknown_reasons=[]),
                dict(node_id='after', step_kind='UNKNOWN_AFTERMATH', origin='UNKNOWN',
                    text='その後の相手の反応は分かりません。', anchor_ref=None,
                    source_refs=[], unknown_reasons=['AFTERMATH_NOT_OBSERVED'])],
            edges=[dict(edge_id='e1', **{'from': 'anchor', 'to': 'choice'}, condition_refs=['c1']),
                   dict(edge_id='e2', **{'from': 'choice', 'to': 'after'}, condition_refs=[])],
            required_conditions=[dict(condition_id='c1', text='相手の話が終わった場面を仮定する。', source_refs=[2])],
            frictions=['意見を言葉にする際、言いづらさがあるかもしれません。'],
            unmodelled_factors=['相手の反応や、その後の状況は分かりません。']))
    return dict(schema_version=if_route.IF_MODEL_SCHEMA, scenarios=scenarios, clarification=None)


def response(prepared, value=None):
    raw = json.dumps(packet(prepared) if value is None else value, ensure_ascii=False,
                     sort_keys=True, separators=(',', ':'))
    return AnalysisModelQuotedParentUnitsResponse(prepared.request_ref,
        commitment(prepared.messages())[7:], hashlib.sha256(raw.encode()).hexdigest(), 'stop', raw)


def rehash(payload):
    if payload['bundle']['artifact_kind'] == if_route.IF_KIND:
        payload['content_text'] = if_route._if_text(payload['safe_projection'])
    payload['bundle']['lifecycle_bindings']['canonical_content_hash'] = commitment(
        [payload['bundle']['primary_artifact'], payload['scenario_graphs']])
    payload['integrity'] = commitment({k: v for k, v in payload.items() if k != 'integrity'})
    return payload


@pytest.mark.parametrize('count', [1, 2, 3])
def test_model_choices_keep_separate_hypothetical_identity_and_same_saved_bytes(count, monkeypatch):
    req = request(count=count)
    before = (req.base_projection_json, req.base_private_evidence_json)
    prepared = if_route.prepare_if_model_request(req)
    assert type(prepared) is AnalysisIfModelPrepared
    result = if_route.admit_if_model_response(prepared, response(prepared))
    assert result.status is EngineStatus.GENERATED, result.reason_codes
    artifact = result.artifact
    stored = artifact.to_storage()
    projection = artifact.safe_projection(authenticated_owner_scope=OWNER)
    assert projection['selection_policy'] == 'PARALLEL_NOT_RANKED'
    assert len(projection['scenarios']) == count
    assert stored['bundle']['epistemic_partition'] == 'HYPOTHETICAL'
    assert all(g['base_observed_map_ref'] == req.base_observed_map_ref for g in stored['scenario_graphs'])
    assert all(e['edge_type'] == 'SIMULATED_TRANSITION' for g in stored['scenario_graphs'] for e in g['edges'])
    assert any(n['origin'] == 'SIMULATED_EXTENSION' for g in stored['scenario_graphs'] for n in g['nodes'])
    assert req.base_projection_json == before[0] and req.base_private_evidence_json == before[1]
    assert stored['base_private_evidence'] == json.loads(before[1])
    assert 'evidence_refs' not in json.dumps(projection) and 'source_envelope_id' not in json.dumps(projection)
    assert set(c['source_id'] for c in stored['bundle']['source_commitments']) == {
        if_route._source_ref(if_route._source(req.branch_intent, OWNER)),
        if_route._source_ref(if_route._source(req.constraints[0], OWNER))}
    monkeypatch.setattr(if_route, 'prepare_if_model_request', lambda *a, **k: pytest.fail('reader prepared a new request'))
    monkeypatch.setattr(if_route, 'generate_if_set', lambda *a, **k: pytest.fail('reader generated'))
    restored = if_route.from_storage(stored, authenticated_owner_scope=OWNER)
    assert restored.to_storage() == stored
    assert restored.safe_projection(authenticated_owner_scope=OWNER) == projection
    assert restored.safe_text_projection(authenticated_owner_scope=OWNER) == artifact.safe_text_projection(authenticated_owner_scope=OWNER)


@pytest.mark.parametrize('legacy', [False, True])
def test_person_authored_choice_preserves_legacy_and_current_saved_map(legacy):
    req = request(legacy=legacy)
    outcome = if_route.generate_if_set(req)
    assert outcome.status is EngineStatus.GENERATED, outcome.reason_codes
    private = outcome.artifact.private_evidence()
    assert private['base_graph'] == json.loads(req.base_private_evidence_json)['graph']
    projection = outcome.artifact.safe_projection(authenticated_owner_scope=OWNER)
    assert [n['origin'] for n in projection['scenarios'][0]['nodes']] == ['OBSERVED_ANCHOR', 'USER_CHOICE', 'UNKNOWN']


def test_edge_branch_keeps_both_anchors_without_turning_original_relation_into_order():
    req = request(branch='e1')
    outcome = if_route.generate_if_set(req)
    assert outcome.status is EngineStatus.GENERATED, outcome.reason_codes
    anchors = [n for n in outcome.artifact.safe_projection(authenticated_owner_scope=OWNER)['scenarios'][0]['nodes']
               if n['origin'] == 'OBSERVED_ANCHOR']
    assert len(anchors) == 2
    assert json.loads(req.base_projection_json)['edges'][0]['relation_kind'] == 'SELF_OUTSIDE_GAP'


@pytest.mark.parametrize('change,reason', [
    (lambda r: replace(r, branch_point_id='', base_route_ref=''), 'analysis_if_branch_required'),
    (lambda r: replace(r, branch_intent=None), 'analysis_if_intent_required'),
    (lambda r: replace(r, constraints=(), constraints_confirmed=False), 'analysis_if_constraints_required'),
])
def test_missing_person_material_is_a_question_with_no_artifact(change, reason):
    outcome = if_route.prepare_if_model_request(change(request()))
    assert outcome.status is EngineStatus.QUESTION_PENDING
    assert outcome.artifact is None and outcome.reason_codes == (reason,)
    question = outcome.clarification_request
    assert question['answer_source_role'] == 'SIMULATION_SESSION_MATERIAL'
    assert question['core_id'] == 'ANALYSIS' and question['skip_allowed'] is True


def test_explicit_no_constraints_allows_model_preparation_without_making_constraints_up():
    prepared = if_route.prepare_if_model_request(replace(request(), constraints=(), constraints_confirmed=True))
    assert type(prepared) is AnalysisIfModelPrepared
    fields = json.loads(prepared.messages()[1]['content'])['fields']
    assert len(fields) == 1 and fields[0]['purpose'] == 'BRANCH_INTENT'


def test_candidate_shortfall_or_clarification_returns_question_without_empty_graph():
    prepared = if_route.prepare_if_model_request(request(count=3))
    result = if_route.admit_if_model_response(prepared, response(prepared, packet(prepared, 1)))
    assert result.status is EngineStatus.QUESTION_PENDING and result.artifact is None
    value = dict(schema_version=if_route.IF_MODEL_SCHEMA, scenarios=[],
                 clarification=dict(reason_code='ALTERNATIVES_UNCLEAR', prompt='どの点を変えて考えたいですか？'))
    result = if_route.admit_if_model_response(prepared, response(prepared, value))
    assert result.status is EngineStatus.QUESTION_PENDING and result.artifact is None


@pytest.mark.parametrize('change', [
    lambda p: p.update(rank=1),
    lambda p: p['scenarios'][0].update(score=0.9),
    lambda p: p['scenarios'][0]['nodes'][1].update(origin='SOURCE_EXPLICIT'),
    lambda p: p['scenarios'][0]['nodes'][0].update(text='元マップにない人格'),
    lambda p: p['scenarios'][0]['nodes'][1].update(origin='USER_CHOICE', text='本人が書いていない希望'),
    lambda p: p['scenarios'][0]['nodes'][1].update(source_refs=[True]),
    lambda p: p['scenarios'][0]['edges'][0].update(to='missing'),
    lambda p: p['scenarios'][0]['edges'][0].update(condition_refs=['missing']),
    lambda p: p['scenarios'][0].update(label='必ず成功します'),
    lambda p: p['scenarios'][0].update(unmodelled_factors=[]),
])
def test_unbound_claims_rank_guarantee_and_graph_mutations_are_rejected(change):
    prepared = if_route.prepare_if_model_request(request())
    value = packet(prepared)
    change(value)
    result = if_route.admit_if_model_response(prepared, response(prepared, value))
    assert result.status is EngineStatus.REJECTED and result.artifact is None


@pytest.mark.parametrize('change', [
    lambda r: replace(r, request_ref='wrong'),
    lambda r: replace(r, messages_sha256='0' * 64),
    lambda r: replace(r, raw_sha256='0' * 64),
    lambda r: replace(r, finish_reason='length'),
])
def test_model_response_belongs_to_exact_prepared_request(change):
    prepared = if_route.prepare_if_model_request(request())
    result = if_route.admit_if_model_response(prepared, change(response(prepared)))
    assert result.status is EngineStatus.REJECTED and result.reason_codes == ('analysis_if_model_response_unbound',)


def test_prepared_source_or_messages_cannot_change_after_capture():
    prepared = if_route.prepare_if_model_request(request())
    changed = replace(prepared, messages_json=prepared.messages_json.replace('意見', '退職'))
    result = if_route.admit_if_model_response(changed, response(changed))
    assert result.status is EngineStatus.REJECTED and result.reason_codes == ('analysis_if_model_input_unbound',)


def test_saved_selection_has_own_sources_parent_and_non_generating_round_trip(monkeypatch):
    prepared = if_route.prepare_if_model_request(request(count=3))
    artifact = if_route.admit_if_model_response(prepared, response(prepared)).artifact
    chosen = artifact.to_storage()['bundle']['primary_artifact']['scenarios'][1]['scenario_artifact_ref']
    saved = if_route.save_route_intent(artifact, authenticated_owner_scope=OWNER,
        selected_scenario_ref=chosen, selection_source=source('selected', chosen),
        note_source=source('note', '今はこの方向を考えておきたい。'), saved_at='2026-11-14T09:00:00+00:00')
    payload = saved.to_storage()
    assert saved.reference != artifact.reference
    assert payload['bundle']['epistemic_partition'] == 'USER_SAVED_INTENT'
    assert payload['bundle']['parent_artifact_refs'] == [artifact.reference]
    assert payload['bundle']['primary_artifact']['source_scenario_set_ref'] == artifact.scenario_set_reference
    assert [source['source_id'] for source in payload['session_sources']] == ['selected', 'note']
    assert len(payload['bundle']['source_commitments']) == 2
    assert len(payload['scenario_graphs']) == 1
    assert saved.base_source_guard == prepared.request.base_source_guard
    monkeypatch.setattr(if_route, 'save_route_intent', lambda *a, **k: pytest.fail('read compiled selection'))
    restored = if_route.from_storage(payload, authenticated_owner_scope=OWNER)
    assert restored.to_storage() == payload
    assert '実行した記録ではありません' in restored.safe_text_projection(authenticated_owner_scope=OWNER)['text']


def test_wrong_owner_nonmember_and_fabricated_selection_operation_are_rejected():
    artifact = if_route.generate_if_set(request()).artifact
    chosen = artifact.to_storage()['bundle']['primary_artifact']['scenarios'][0]['scenario_artifact_ref']
    with pytest.raises(if_route.AnalysisIfRouteError, match='owner_mismatch'):
        if_route.from_storage(artifact.to_storage(), authenticated_owner_scope='other')
    for ref, text in [('analysis-if-scenario:absent@1', chosen), (chosen, '違う選択')]:
        with pytest.raises(if_route.AnalysisIfRouteError):
            if_route.save_route_intent(artifact, authenticated_owner_scope=OWNER, selected_scenario_ref=ref,
                selection_source=source('selection', text), saved_at='2026-11-14T09:00:00+00:00')


@pytest.mark.parametrize('change', [
    lambda p: p['safe_projection'].update(rank=1),
    lambda p: p['scenario_graphs'][0]['nodes'][1].update(origin='OBSERVED_ANCHOR'),
    lambda p: p['scenario_graphs'][0]['edges'][0].update(edge_type='OBSERVED_ORDER'),
    lambda p: p['safe_projection']['scenarios'][0]['nodes'][0].update(visible_label='改変された読み'),
    lambda p: p['safe_projection']['scenarios'][0].update(frictions=[]),
])
def test_rehashed_storage_cannot_change_graph_or_model_surface(change):
    prepared = if_route.prepare_if_model_request(request())
    artifact = if_route.admit_if_model_response(prepared, response(prepared)).artifact
    payload = artifact.to_storage()
    change(payload)
    rehash(payload)
    with pytest.raises(if_route.AnalysisIfRouteError):
        if_route.from_storage(payload, authenticated_owner_scope=OWNER)


def test_safety_material_does_not_become_an_if_scenario():
    req = replace(request(), branch_intent=source('intent', '死にたい。'))
    outcome = if_route.prepare_if_model_request(req)
    assert outcome.status is EngineStatus.SEPARATE_SAFETY and outcome.artifact is None


def test_session_operation_uses_shared_source_envelope_role_and_exact_original_bytes():
    from cocolon_meaning_experience_engine.contracts import SourceEnvelope
    material = source('person-operation', '話を聞いてから、自分の意見を伝えたい。')
    envelope = if_route.freeze_simulation_source(material, authenticated_owner_scope=OWNER)
    assert type(envelope) is SourceEnvelope
    assert envelope.source_role == 'SIMULATION_SESSION_MATERIAL'
    assert json.loads(envelope.raw_utf8)['text'] == material.text
    assert envelope.raw_sha256 == hashlib.sha256(envelope.raw_utf8).hexdigest()


@pytest.mark.parametrize('authored,fragment', [
    ('会社を辞めるつもりはありません。', '会社を辞める'),
    ('話す準備ができたら、自分の意見を言ってみたい。', '自分の意見を言ってみたい'),
    ('話してみたいけれど、まだ決めていません。', '話してみたい'),
    ('今日は参加しない。次回は考えてみたい。', '今日は参加'),
])
def test_user_choice_cannot_drop_negation_condition_reservation_or_other_authored_clauses(authored, fragment):
    req = replace(request(), branch_intent=source('intent', authored))
    prepared = if_route.prepare_if_model_request(req)
    value = packet(prepared)
    value['scenarios'][0]['nodes'][1].update(origin='USER_CHOICE', text=fragment, source_refs=[1])
    outcome = if_route.admit_if_model_response(prepared, response(prepared, value))
    assert outcome.status is EngineStatus.REJECTED
    assert outcome.reason_codes == ('analysis_if_model_choice_unbound',)
    assert outcome.artifact is None


def test_complete_user_choice_field_is_retained_and_multiple_source_composition_is_not_admitted():
    req = replace(request(), branch_intent=source('intent', '会社を辞めるつもりはありません。'))
    prepared = if_route.prepare_if_model_request(req)
    value = packet(prepared)
    value['scenarios'][0]['nodes'][1].update(origin='USER_CHOICE', text=req.branch_intent.text, source_refs=[1])
    outcome = if_route.admit_if_model_response(prepared, response(prepared, value))
    assert outcome.status is EngineStatus.GENERATED, outcome.reason_codes
    shown = outcome.artifact.safe_projection(authenticated_owner_scope=OWNER)['scenarios'][0]['nodes'][1]
    assert shown['visible_label'] == req.branch_intent.text and shown['origin'] == 'USER_CHOICE'
    value['scenarios'][0]['nodes'][1]['source_refs'] = [1, 2]
    assert if_route.admit_if_model_response(prepared, response(prepared, value)).status is EngineStatus.REJECTED


def test_rehashed_legacy_partial_user_choice_is_also_rejected_on_saved_read():
    req = replace(request(), branch_intent=source('intent', '会社を辞めるつもりはありません。'))
    prepared = if_route.prepare_if_model_request(req)
    value = packet(prepared)
    value['scenarios'][0]['nodes'][1].update(origin='USER_CHOICE', text=req.branch_intent.text, source_refs=[1])
    payload = if_route.admit_if_model_response(prepared, response(prepared, value)).artifact.to_storage()
    value['scenarios'][0]['nodes'][1]['text'] = '会社を辞める'
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    payload['model_receipt'].update(raw=raw, raw_sha256=hashlib.sha256(raw.encode()).hexdigest())
    payload['safe_projection']['scenarios'][0]['nodes'][1]['visible_label'] = '会社を辞める'
    rehash(payload)
    with pytest.raises(if_route.AnalysisIfRouteError, match='analysis_if_model_choice_unbound'):
        if_route.from_storage(payload, authenticated_owner_scope=OWNER)
