"""Shared source meaning reaches the sole writer and the same saved OBS.

Provider text is synthetic. These checks establish source/realization and
receipt continuity, not a claim that the real model's prose is now correct.
"""
import copy
from dataclasses import replace
import hashlib
import json

import httpx
import pytest

import emlis_thread_store
from emlis_thread_service import EmlisThreadService, Q3_PROFILE
from cocolon_meaning_experience_engine.natural_reply import (
    ACTIVE_MEANING_PROFILE, NaturalReplyInput, build_natural_reply_messages,
    prepare_natural_reply, system_message_for,
)
from test_emlis_q2_application import run
from test_emlis_q3_application import qdb
from test_emlis_natural_reply_application import natural_case, BODY
from test_emlis_interpretation_correction import correct


def _source(qdb, parent, *, unknown=False):
    memo = '私は仕事を続けたい。私は費用を記録した。'
    if unknown:
        memo += 'くるくるした余韻だけが残った。'
    qdb.query("update public.emotions set memo=$2,memo_action=$3 where id=$1",
              [parent, memo, '私は資料を調べた。'])
    return memo


def _observations(snapshot):
    return [event for event in snapshot['events'] if event['kind'] == 'OBSERVATION']


def test_active_meaning_and_unread_text_reach_writer_without_replacing_original(natural_case, qdb, monkeypatch):
    user, parent, service, calls = natural_case
    original = _source(qdb, parent, unknown=True)
    dto = run(service.start(user, parent))
    assert len(calls) == 1 and dto['current_observation']['text'] == BODY
    request = calls[0]
    original_material = json.loads(request.material_json)
    assert original_material['current']['memo'] == original
    writer = json.loads(build_natural_reply_messages(request)[1]['content'])
    current, = writer['records']
    assert current['scope'] == 'CURRENT_INPUT'
    assert current['metadata']['category'] == ['仕事']
    assert current['metadata']['emotion_details'] == [{'type': '平穏', 'strength': 'medium'}]
    # The unsupported clause is still source text, not erased to fit the
    # finite graph. Full source identity remains in the separate original.
    assert 'くるくるした余韻だけが残った。' in ''.join(f['text'] for f in current['active_fields'])
    assert current['source_duties']['unassessed_source_ranges']
    assert current['source_duties']['claims']
    saved = run(service.store.read(user, input_id=parent))
    artifact = _observations(saved)[-1]['payload']['artifact']
    assert artifact['analysis_state'] == saved['thread']['data']['analysis_state'] == 'GENERATED'
    assert artifact['analysis_material'] == json.loads(request.analysis_material_json)
    assert artifact['analysis_material'] == saved['thread']['data']['analysis_material']
    assert artifact['analysis_material']['coverage']['full_source_semantic_coverage'] is False
    assert artifact['meaning_profile'] == ACTIVE_MEANING_PROFILE
    assert 'analysis_material' not in json.dumps(dto)

    def no_derivation(*args, **kwargs):
        raise AssertionError('saved GET must not derive meaning or regenerate')
    import cocolon_meaning_experience_engine.cores.analysis.semantic_admission as shared
    monkeypatch.setattr(shared, 'prepare_emlis_analysis_material', no_derivation)
    assert run(service.get(user, parent))['current_observation'] == dto['current_observation']
    assert len(calls) == 1


@pytest.mark.parametrize('explanation, new_text', [
    ('「私は仕事を続けたい」は取り消します。', None),
    ('「私は仕事を続けたい」ではなく「私は家族を守りたい」です。', '私は家族を守りたい'),
])
def test_person_update_changes_active_author_meaning_not_unrelated_fields(natural_case, qdb, explanation, new_text):
    user, parent, service, calls = natural_case
    original = _source(qdb, parent)
    first = run(service.start(user, parent))
    before = run(service.store.read(user, input_id=parent))
    old_observation = copy.deepcopy(_observations(before)[-1])
    updated = run(correct(service, user, first, explanation=explanation))
    assert updated['current_observation'] is not None and len(calls) == 2
    request = calls[-1]
    current, = json.loads(build_natural_reply_messages(request)[1]['content'])['records']
    texts = [f['text'] for f in current['active_fields']]
    assert all('私は仕事を続けたい' not in text for text in texts)
    assert any('私は費用を記録した' in text for text in texts)
    assert any('私は資料を調べた' in text for text in texts)
    assert bool(new_text and any(new_text in text for text in texts)) == (new_text is not None)
    assert current['source_updates']
    assert json.loads(request.material_json)['current']['memo'] == original
    saved = run(service.store.read(user, input_id=parent))
    assert _observations(saved)[0] == old_observation
    assert saved['thread']['current_meaning_event_id'] is None
    assert _observations(saved)[-1]['payload']['artifact']['analysis_material']['state'] == 'GENERATED'
    assert run(service.get(user, parent))['current_observation'] == updated['current_observation']
    assert len(calls) == 2


def test_unsupported_replacement_remains_full_unresolved_source_not_old_active_facts(natural_case, qdb):
    user, parent, service, calls = natural_case
    original = _source(qdb, parent)
    first = run(service.start(user, parent))
    explanation = '「私は仕事を続けたい」ではなく「私は友人を助けたい」です。'
    updated = run(correct(service, user, first, explanation=explanation))
    current, = json.loads(build_natural_reply_messages(calls[-1])[1]['content'])['records']
    assert current['meaning_state'] == 'NOT_GENERATED'
    assert current['active_state'] == 'PENDING'
    assert current['active_fields'] == [] and current['source_duties'] is None
    all_sources = json.dumps(current['unresolved_sources'], ensure_ascii=False)
    assert original in all_sources and explanation in all_sources
    assert '私は資料を調べた。' in all_sources
    target, = current['correction_targets']
    assert target['source_role'] == 'AI_INTERPRETATION_TARGET'
    assert target['text'] == '少し安心できた'
    assert current['unresolved_sources'][target['explanation_source'] - 1]['fields']['memo'] == explanation
    saved = run(service.store.read(user, input_id=parent))
    artifact = _observations(saved)[-1]['payload']['artifact']
    assert artifact['analysis_state'] == 'NOT_GENERATED'
    assert artifact['analysis_material']['coverage']['pending_source_ranges']
    assert updated['current_observation']['text'] == BODY and len(calls) == 2


def test_unknown_only_text_is_kept_without_generated_meaning(natural_case, qdb):
    user, parent, service, calls = natural_case
    text = 'くるくるした余韻だけが残った。'
    qdb.query("update public.emotions set memo=$2,memo_action='' where id=$1", [parent, text])
    run(service.start(user, parent))
    current, = json.loads(build_natural_reply_messages(calls[0])[1]['content'])['records']
    assert current['meaning_state'] == 'NOT_GENERATED'
    assert current['active_state'] == 'RESOLVED'
    assert [field['text'] for field in current['active_fields']] == [text]
    assert current['source_duties']['claims'] == []
    assert current['source_duties']['unassessed_source_ranges']
    saved = run(service.store.read(user, input_id=parent))
    assert _observations(saved)[-1]['payload']['artifact']['analysis_state'] == 'NOT_GENERATED'


def test_legacy_received_reply_keeps_legacy_messages_after_new_service_restart(natural_case, monkeypatch, qdb):
    user, parent, service, calls = natural_case
    _source(qdb, parent)
    service.natural_meaning_profile = None
    failed = False

    async def rpc(name, payload, **kwargs):
        nonlocal failed
        if not failed and any(e['kind'] == 'OBSERVATION' for e in payload.get('p_events', [])):
            failed = True
            return httpx.Response(503, json={'code': '57P03'})
        return await qdb.rpc(name, payload, **kwargs)

    monkeypatch.setattr(emlis_thread_store, 'sb_post_rpc', rpc)
    pending = run(service.start(user, parent))
    assert pending['can_retry'] and len(calls) == 1
    assert calls[0].meaning_profile is None and calls[0].writer_material_json is None
    before = run(service.store.read(user, input_id=parent))
    received = copy.deepcopy(next(e for e in before['events']
        if e['payload'].get('stage') == 'NATURAL_REPLY_RECEIVED'))
    import cocolon_meaning_experience_engine.cores.analysis.semantic_admission as shared

    def no_new_material(*args, **kwargs):
        raise AssertionError('a legacy receipt is not rebound to new meaning')

    monkeypatch.setattr(shared, 'prepare_emlis_analysis_material', no_new_material)
    restarted = EmlisThreadService(runtime_profile=Q3_PROFILE,
        natural_reply_source=service.natural_reply_source)
    result = run(restarted.action(user, pending['thread_id'], action='retry_response',
        expected_revision=pending['revision'], idempotency_key='resume-old-receipt',
        operation_id=pending['operation_id']))
    assert result['current_observation']['text'] == BODY and len(calls) == 1
    saved = run(service.store.read(user, input_id=parent))
    assert next(e for e in saved['events'] if e['id'] == received['id']) == received
    artifact = _observations(saved)[-1]['payload']['artifact']
    assert artifact['analysis_state'] == 'NOT_GENERATED' and 'analysis_material' not in artifact
    assert 'natural_meaning_profile' not in saved['thread']['data']


@pytest.mark.parametrize('receipt_kind', ['current', 'previous', 'changed_hash'])
def test_new_received_reply_reuses_only_the_same_fixed_meaning_and_messages(natural_case, monkeypatch, qdb, receipt_kind):
    user, parent, service, calls = natural_case
    _source(qdb, parent)
    failed = False

    async def rpc(name, payload, **kwargs):
        nonlocal failed
        if not failed and any(e['kind'] == 'OBSERVATION' for e in payload.get('p_events', [])):
            failed = True
            return httpx.Response(503, json={'code': '57P03'})
        return await qdb.rpc(name, payload, **kwargs)

    monkeypatch.setattr(emlis_thread_store, 'sb_post_rpc', rpc)
    pending = run(service.start(user, parent))
    before = run(service.store.read(user, input_id=parent))
    as_of = before['thread']['data']['natural_meaning_as_of']
    material_ref = json.loads(calls[0].analysis_material_json)['material_ref']
    receipt = next(e for e in before['events'] if e['payload'].get('stage') == 'NATURAL_REPLY_RECEIVED')
    assert receipt['payload']['meaning_profile'] == ACTIVE_MEANING_PROFILE
    if receipt_kind == 'previous':
        # Before context-aware writing the same two-field record was sent
        # with no context protocol tag. Preserve its exact receipt on retry.
        old_writer = json.loads(calls[0].writer_material_json)
        assert old_writer.pop('source_context_version')
        old_input = replace(calls[0], writer_material_json=json.dumps(old_writer, ensure_ascii=False, separators=(',', ':')))
        old_messages = build_natural_reply_messages(old_input)
        old_hash = hashlib.sha256(json.dumps(old_messages, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
        assert old_hash != receipt['payload']['writer_messages_sha256']
        for event in before['events']:
            if event['payload'].get('stage') in {'NATURAL_REPLY_CALL_STARTED', 'NATURAL_REPLY_RECEIVED'}:
                qdb.query("update public.emlis_thread_events set payload=jsonb_set(payload-'writer_context_version',"
                          "'{writer_messages_sha256}',to_jsonb($2::text)) where id=$1", [event['id'], old_hash])
        receipt['payload']['writer_messages_sha256'] = old_hash
    if receipt_kind == 'changed_hash':
        qdb.query("update public.emlis_thread_events set payload=jsonb_set(payload,'{writer_messages_sha256}',to_jsonb($2::text)) where id=$1",
                  [receipt['id'], 'different-writer-message-hash'])
    restarted = EmlisThreadService(runtime_profile=Q3_PROFILE,
        natural_reply_source=service.natural_reply_source)
    result = run(restarted.action(user, pending['thread_id'], action='retry_response',
        expected_revision=pending['revision'], idempotency_key='resume-meaning-receipt',
        operation_id=pending['operation_id']))
    after = run(service.store.read(user, input_id=parent))
    assert len(calls) == 1 and after['thread']['data']['natural_meaning_as_of'] == as_of
    if receipt_kind == 'changed_hash':
        assert result['current_observation'] is None and not result['can_retry']
        assert result['failure_code'] == 'natural_reply_writer_identity_changed'
        assert not _observations(after)
    else:
        assert result['current_observation']['text'] == BODY
        artifact = _observations(after)[-1]['payload']['artifact']
        assert artifact['analysis_material']['material_ref'] == material_ref
        assert artifact['writer_messages_sha256'] == receipt['payload']['writer_messages_sha256']
        assert artifact['analysis_state'] == 'GENERATED'



@pytest.mark.parametrize('old_receipt', [False, True])
def test_corrected_circumstance_writer_retries_exact_prior_projection(natural_case, qdb, monkeypatch, old_receipt):
    from cocolon_meaning_experience_engine import natural_reply
    from test_emlis_q2_application import answer

    user, parent, service, calls = natural_case
    feeling = 'つらかったんです'
    circumstance = '会議がうまくできませんでした'
    qdb.query("update public.emotions set memo=$2,memo_action='' where id=$1", [parent, feeling])
    initial = run(service.start(user, parent))
    assert initial['pending_question']['text'] == 'なにがつらかったんですか？'
    refined = run(answer(service, user, initial, circumstance))
    assert refined['body_state'] == 'REFINED' and refined['meaning_updated']

    failed = False

    async def fail_first_observation_save(name, payload, **kwargs):
        nonlocal failed
        if not failed and any(e['kind'] == 'OBSERVATION' for e in payload.get('p_events', [])):
            failed = True
            return httpx.Response(503, json={'code': '57P03'})
        return await qdb.rpc(name, payload, **kwargs)

    def legacy_writer_context(*args, **kwargs):
        kwargs['include_corrected_circumstance'] = False
        return prepare_natural_reply(*args, **kwargs)

    monkeypatch.setattr(emlis_thread_store, 'sb_post_rpc', fail_first_observation_save)
    with monkeypatch.context() as prior:
        if old_receipt:
            prior.setattr(natural_reply, 'prepare_natural_reply', legacy_writer_context)
        pending = run(correct(service, user, refined, explanation='「つらかったんです」ではなく「私は不安だった」です。'))
    assert failed and pending['can_retry'] and len(calls) == 3
    material = json.loads(calls[-1].analysis_material_json)
    writer = json.loads(calls[-1].writer_material_json)
    row, = writer['records']
    if old_receipt:
        assert row['active_state'] == 'PENDING' and not row['active_fields']
        assert 'corrected_circumstance' not in material
        version = natural_reply.SOURCE_CONTEXT_VERSION
    else:
        assert row['active_state'] == 'RESOLVED'
        assert [(field['source_role'], field['text']) for field in row['active_fields']] == [
            ('SUPPLEMENTAL_ANSWER', circumstance), ('USER_INTERPRETATION_CORRECTION', '私は不安だった'),
        ]
        assert all('ai_question_context' not in field for field in row['active_fields'])
        assert material['corrected_circumstance'] is True
        version = natural_reply.CORRECTED_SOURCE_CONTEXT_VERSION
    assert writer['source_context_version'] == version

    before = run(service.store.read(user, input_id=parent))
    receipt = [e for e in before['events'] if e['payload'].get('stage') == 'NATURAL_REPLY_RECEIVED'][-1]
    assert receipt['payload']['writer_context_version'] == version
    restarted = EmlisThreadService(runtime_profile=Q3_PROFILE, natural_reply_source=service.natural_reply_source)
    result = run(restarted.action(user, pending['thread_id'], action='retry_response',
        expected_revision=pending['revision'], idempotency_key='resume-corrected-reply',
        operation_id=pending['operation_id']))
    assert result['current_observation']['text'] == BODY and len(calls) == 3
    after = run(service.store.read(user, input_id=parent))
    assert next(e for e in after['events'] if e['id'] == receipt['id']) == receipt
    saved = _observations(after)[-1]['payload']['artifact']
    assert saved['analysis_material'] == material
    assert saved['writer_messages_sha256'] == receipt['payload']['writer_messages_sha256']
    assert run(restarted.get(user, parent))['current_observation'] == result['current_observation']


def test_corrected_circumstance_sources_occupy_independent_v24_plan_nodes(natural_case, qdb):
    from datetime import datetime, timedelta
    from analysis_semantic_map import prepare_semantic_map
    from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as admission
    from test_analysis_node_local_native_profile import accepts
    from test_emlis_q2_application import answer

    user, parent, service, _ = natural_case
    qdb.query("update public.emotions set memo=$2,memo_action='' where id=$1", [parent, 'つらかったんです'])
    initial = run(service.start(user, parent))
    refined = run(answer(service, user, initial, '会議がうまくできませんでした'))

    def prepared_map(*other_members):
        saved = run(service.store.read(user, input_id=parent))
        saved['context'] = run(service.store.related_context(user, parent,
            context_guards=saved['thread']['data'].get('context_guards', [])))
        end = datetime.fromisoformat(saved['now']) + timedelta(days=1)
        snapshot = dict(tier='free', now=saved['now'], members=[saved, *other_members],
            period_start='2020-01-01T00:00:00Z', period_end=end.isoformat(),
            guard='analysis-db-cumulative-v1:' + '1' * 64)
        return prepare_semantic_map(user, snapshot, prompt_version=admission.SEMANTIC_MAP_OCCURRENCE_V24_PROFILE)

    def plan(prepared, groups):
        messages = admission.semantic_node_local_v4_wire_messages(prepared)
        material = json.loads(messages[1]['content'])
        quotes = {f['field']: f['text'] for f in json.loads(prepared.material_json)['fields']}
        nodes = [dict(node_id=f'n{i}', units=[
            dict(evidence=[dict(quote=quotes[field], field=field) for field in unit])
            for unit in units]) for i, units in enumerate(groups, 1)]
        return messages, dict(schema_version=admission._semantic_v4_schema('PLAN'),
            source_choices_sha256=material['source_choices_sha256'], nodes=nodes)

    uncorrected = prepared_map()
    original = json.loads(uncorrected.material_json)
    assert original['answered_feeling_circumstances']
    assert 'independent_corrected_source_fields' not in original['records'][0]
    _, linked = plan(uncorrected, [[[1, 2]]])
    assert admission.admit_semantic_node_local_v4_plan_response(uncorrected, linked)['nodes'] == linked['nodes']

    run(correct(service, user, refined, explanation='「つらかったんです」ではなく「私は不安だった」です。'))
    corrected = prepared_map()
    material = json.loads(corrected.material_json)
    assert not material.get('answered_feeling_circumstances')
    assert material['records'][0]['independent_corrected_source_fields'] == [1, 2]
    for groups in ([[[1, 2]]], [[[1], [2]]], [[[1]]]):
        _, merged = plan(corrected, groups)
        with pytest.raises(admission.AnalysisSemanticMapError, match='analysis_semantic_plan_independent_correction_scope_invalid'):
            admission.admit_semantic_node_local_v4_plan_response(corrected, merged)
    messages, separate = plan(corrected, [[[1]], [[2]]])
    assert accepts(separate, messages)
    admitted = admission.admit_semantic_node_local_v4_plan_response(corrected, separate)
    assert admitted['nodes'] == separate['nodes']
    first, second = (f['text'] for f in material['fields'])
    nodes = {}
    for node, quote in zip(admitted['nodes'], (first, second), strict=True):
        node_id = node['node_id']
        key = admission._semantic_fact_part_key(node['units'][0]['evidence'], 0)
        nodes[node_id] = dict(units={'u1': dict(evidence_ref=node_id + '.u1',
            source_mode='RECORDED', fact_parts={key: quote}, unknowns=[])},
            node_kind='STATE_CONTEXT', perspective='SELF', title=quote, meaning='')
    bodies = dict(schema_version=admission._semantic_v4_schema('NODES'),
        plan_sha256=admission.semantic_map_hash(admitted), nodes=nodes)
    unsupported = copy.deepcopy(bodies)
    unsupported['nodes']['n2']['meaning'] = '会議の後に感じた不安が書かれています。'
    with pytest.raises(admission.AnalysisSemanticMapError, match='analysis_semantic_node_independent_correction_scope_invalid'):
        admission.semantic_node_local_v4_nodes(corrected, admitted, unsupported)
    registry = admission._semantic_v4_join(admitted, bodies)
    relations = dict(schema_version=admission._semantic_v4_schema('RELATIONS'),
        nodes_sha256=admission.semantic_map_hash(registry), qualification_review={},
        edges=[], overview=dict(node_refs=['n1', 'n2'], title='本人の補足回答と訂正'))
    assert admission.semantic_node_local_v4_relations(corrected, admitted, bodies, relations)['edges'] == []
    unsupported = copy.deepcopy(relations)
    unsupported['overview']['title'] = '会議の状況と、その後に感じた不安'
    with pytest.raises(admission.AnalysisSemanticMapError, match='analysis_semantic_overview_independent_correction_scope_invalid'):
        admission.semantic_node_local_v4_relations(corrected, admitted, bodies, unsupported)
    relations['edges'] = [{
        'from': 'n1', 'to': 'n2', 'from_unit': 'n1.u1', 'to_unit': 'n2.u1',
        'from_source': first, 'to_source': second, 'relation_kind': 'SHARED_MEANING',
        'label': '会議の後で不安になった',
    }]
    with pytest.raises(admission.AnalysisSemanticMapError, match='analysis_semantic_relation_independent_correction_scope_invalid'):
        admission.semantic_node_local_v4_relations(corrected, admitted, bodies, relations)

    from test_analysis_deep_insight_handoff import answer_row
    from test_analysis_cumulative import source_snapshot

    deep_answer = answer_row()
    deep_answer['deep_insight']['user_id'] = user
    deep_answer['deep_insight']['question_text'] = '準備したことをどう振り返りますか？'
    recall = '準備を始める前に相談できていなかったと振り返りました。'
    deep_answer['original']['memo'] = recall
    other = source_snapshot(1)['members'][0]
    other['original']['memo'] = '図書館で本を借りた。'
    other['original']['memo_action'] = ''
    for separate_records in ((), (other,)):
        after = prepared_map(deep_answer, *separate_records)
        after_material = json.loads(after.material_json)
        texts = {field['field']: field['text'] for field in after_material['fields']}
        _, selected = plan(after, [[[number]] for number in texts])
        _, choices, _ = admission._semantic_plan_choices(after, after_material)
        for node in selected['nodes']:
            root = node['units'][0]['evidence'][0]
            root['quote'] = next((cue for (number, cue), quote in choices.items()
                if number == root['field'] and quote == root['quote']), root['quote'])
        selected = admission.admit_semantic_node_local_v4_plan_response(after, selected)
        classified = {}
        for planned in selected['nodes']:
            ref = planned['node_id']
            evidence = planned['units'][0]['evidence']
            literal = texts[evidence[0]['field']]
            key = admission._semantic_fact_part_key(evidence, 0)
            classified[ref] = dict(units={'u1': dict(evidence_ref=ref + '.u1',
                source_mode='PERSON_JUDGMENT' if literal == recall else 'RECORDED',
                fact_parts={key: literal}, unknowns=[])}, node_kind='STATE_CONTEXT',
                perspective='SELF', title=literal, meaning='')
        after_bodies = dict(schema_version=admission._semantic_v4_schema('NODES'),
            plan_sha256=admission.semantic_map_hash(selected), nodes=classified)
        after_registry = admission._semantic_v4_join(selected, after_bodies)
        after_relations = dict(schema_version=admission._semantic_v4_schema('RELATIONS'),
            nodes_sha256=admission.semantic_map_hash(after_registry), qualification_review={}, edges=[],
            overview=dict(node_refs=list(classified), title=f'{len(after_material["records"])}件の記録を振り返って'))
        answer_ref = next(node for node, body in classified.items() if body['title'] == recall)
        result = admission.semantic_node_local_v4_relations(after, selected, after_bodies, after_relations)
        assert result['edges'] == [] and set(n['title'] for n in result['nodes']) == set(texts.values())
        assert 'source_modeはPERSON_JUDGMENT' in admission.semantic_node_local_v4_wire_messages(
            after, 'NODES', plan=selected)[0]['content']
        relation_instruction = admission.semantic_node_local_v4_wire_messages(
            after, 'RELATIONS', plan=selected, nodes=after_bodies)[0]['content']
        assert '一つの場面だけで概要を構成できます' not in relation_instruction
        assert json.dumps(after_relations['overview'], ensure_ascii=False, separators=(',', ':')) in relation_instruction
        exact_overview = copy.deepcopy(after_relations)
        exact_overview['overview']['title'] = recall.rstrip('。')
        assert admission.semantic_node_local_v4_relations(after, selected, after_bodies, exact_overview) == result
        assert exact_overview['overview']['title'] == recall.rstrip('。')
        exact_overview['overview']['node_refs'].pop()
        with pytest.raises(admission.AnalysisSemanticMapError, match='analysis_semantic_overview_independent_correction_scope_invalid'):
            admission.semantic_node_local_v4_relations(after, selected, after_bodies, exact_overview)
        changed = copy.deepcopy(after_bodies)
        changed['nodes'][answer_ref]['units']['u1']['source_mode'] = 'PERSON_WISH'
        with pytest.raises(admission.AnalysisSemanticMapError, match='analysis_semantic_node_independent_correction_scope_invalid'):
            admission.semantic_node_local_v4_nodes(after, selected, changed)
        changed = copy.deepcopy(after_bodies)
        changed['nodes'][answer_ref]['meaning'] = 'その後、論点を確認しました。'
        with pytest.raises(admission.AnalysisSemanticMapError, match='analysis_semantic_node_independent_correction_scope_invalid'):
            admission.semantic_node_local_v4_nodes(after, selected, changed)
        after_relations['overview']['title'] = '会議の後で確認したこと'
        with pytest.raises(admission.AnalysisSemanticMapError, match='analysis_semantic_overview_independent_correction_scope_invalid'):
            admission.semantic_node_local_v4_relations(after, selected, after_bodies, after_relations)


def test_writer_uses_compact_meaning_without_private_evidence_or_losing_source():
    from test_analysis_active_update_material import saved_update, REVISE
    from test_analysis_saved_period import OWNER, NOW
    from emlis_thread_service import _request
    saved = saved_update(REVISE)
    request = _request(saved, include_context=False, analysis_source_only=True)
    material, _ = prepare_natural_reply(request, meaning_profile=ACTIVE_MEANING_PROFILE,
        owner_scope=OWNER, original_record=saved['original'], as_of=NOW)
    private = json.loads(material.analysis_material_json)
    messages = build_natural_reply_messages(material)
    writer = json.loads(messages[1]['content'])
    record, = writer['records']
    assert [f['text'] for f in record['active_fields']] == [f['text'] for f in private['active_fields']]
    assert [c['reading']['polarity'] for c in record['source_duties']['claims']] == [
        c['proposition']['polarity'] for c in private['source_duties']['claims']]
    assert [c['reading']['time'] for c in record['source_duties']['claims']] == [
        c['proposition']['temporal_scope'] for c in private['source_duties']['claims']]
    assert [c['reading']['actor'] for c in record['source_duties']['claims']] == [
        c['proposition']['actor'] for c in private['source_duties']['claims']]
    assert record['source_updates'][0]['operation'] == 'REVISE'
    assert record['source_updates'][0]['target_text'] == '私は仕事を続けたい'
    assert 'graph' not in record and 'sources' not in record
    assert 'active_claims' not in messages[0]['content']
    assert 'answer_meaning' not in messages[0]['content']

    def keys(value):
        if isinstance(value, dict):
            for key, item in value.items():
                yield key
                yield from keys(item)
        elif isinstance(value, list):
            for item in value:
                yield from keys(item)

    forbidden = {'source_envelope_id', 'source_id', 'field_ref', 'material_ref', 'record_ref',
        'record_version', 'source_set_ref', 'evidence', 'evidence_refs', 'evidence_id',
        'field_sha256', 'literal_sha256', 'utf8_start', 'utf8_end', 'source_parts'}
    assert not forbidden.intersection(keys(writer))
    # Private evidence remains available for save/replay; author input does
    # not repeat its graph, locators, hashes and full quotation per claim.
    assert private['active_fields'][0]['evidence']['literal_sha256']
    assert len(messages[1]['content'].encode()) < len(material.analysis_material_json.encode()) // 2


def test_compact_wire_keeps_long_unparsed_fields_once_and_legacy_bytes_unchanged():
    from test_emlis_analysis_material import uncorrected
    from test_analysis_saved_period import OWNER, NOW
    from emlis_thread_service import _request
    memo, action = 'くるくるした余韻。' * 120, '🦉QKZ。' * 120
    saved = uncorrected(memo, action)
    request = _request(saved, include_context=False, analysis_source_only=True)
    legacy, _ = prepare_natural_reply(request)
    old_messages = [dict(role='system', content=system_message_for(legacy)),
                    dict(role='user', content=legacy.material_json)]
    old_bytes = json.dumps(old_messages, ensure_ascii=False).encode()
    material, _ = prepare_natural_reply(request, meaning_profile=ACTIVE_MEANING_PROFILE,
        owner_scope=OWNER, original_record=saved['original'], as_of=NOW)
    wire = build_natural_reply_messages(material)[1]['content']
    assert wire.count(memo) == wire.count(action) == 1
    assert [f['text'] for f in json.loads(wire)['records'][0]['active_fields']] == [memo, action]
    assert json.loads(material.analysis_material_json)['original_record'] == saved['original']
    # No implicit migration of a historical request to the new author view.
    restored = NaturalReplyInput(legacy.source_prefix_ref, legacy.material_json)
    assert json.dumps(build_natural_reply_messages(restored), ensure_ascii=False).encode() == old_bytes


@pytest.mark.parametrize('answers', [('その時は重かった。',), ('はい。', 'はい。')])
def test_answer_writing_keeps_each_issued_question_with_its_answer_not_as_user_evidence(answers):
    from test_emlis_analysis_material import uncorrected, answer_request
    from test_analysis_saved_period import OWNER, NOW

    saved = uncorrected('褒められたのに、嬉しくなかった。', '会議で発表した。')
    request = answer_request(saved, answers)
    control = request.emlis_thread.question_control_context
    prompts = ('「褒められた」は、あなたにはどんな意味として届きましたか。', 'その日の発表はどうでしたか。')
    questions = tuple(replace(q, prompt_private=prompts[i]) for i, q in enumerate(control.issued_questions))
    thread = replace(request.emlis_thread, question_control_context=replace(control, pending_question=questions[-1],
                      issued_questions=questions))
    request = replace(request, emlis_thread=thread)
    options = dict(response_stage='REFINED', meaning_profile=ACTIVE_MEANING_PROFILE,
                   owner_scope=OWNER, original_record=saved['original'], as_of=NOW)
    previous, _ = prepare_natural_reply(request, **options, bind_writer_context=False)
    current, _ = prepare_natural_reply(request, **options)
    assert current.material_json == previous.material_json and current.analysis_material_json == previous.analysis_material_json
    system, wire = build_natural_reply_messages(current)
    assert '欄は出来事の順番を示しません' in system['content']
    assert 'current_answers' not in system['content']
    record, = json.loads(wire['content'])['records']
    rows = record['unresolved_sources'] if record['active_state'] == 'PENDING' else record['active_fields']
    bound = [row for row in rows if row['source_role'] == 'SUPPLEMENTAL_ANSWER']
    assert [row['ai_question_context'] for row in bound] == list(prompts[:len(answers)])
    assert all('ai_question_context' not in row for row in rows if row['source_role'] != 'SUPPLEMENTAL_ANSWER')
    assert all(prompt not in previous.writer_material_json for prompt in prompts)


def test_final_single_field_uses_the_recipient_instruction_without_an_answer():
    from test_emlis_analysis_material import uncorrected
    from test_analysis_saved_period import OWNER, NOW
    from emlis_thread_service import _request

    saved = uncorrected('誘われたのに、悲しかった。', '')
    request = _request(saved, include_context=False, analysis_source_only=True)
    options = dict(meaning_profile=ACTIVE_MEANING_PROFILE, owner_scope=OWNER,
                   original_record=saved['original'], as_of=NOW)
    current, _ = prepare_natural_reply(request, **options)
    previous, _ = prepare_natural_reply(request, **options, bind_writer_context=False)
    system, source = build_natural_reply_messages(current)
    assert '書き出しからEmlisが本人に話しかける返事' in system['content']
    assert 'この記録で大事な点を一つ' in system['content']
    assert '短い受け取りや一度の言い換えも構いません' not in system['content']
    assert '今回は回答後です' not in system['content']
    assert json.loads(source['content'])['records'] == json.loads(previous.writer_material_json)['records']


@pytest.mark.parametrize('old_writer', [False, True])
def test_received_answer_source_roles_keep_exact_saved_writer_on_retry(natural_case, qdb, monkeypatch, old_writer):
    from cocolon_meaning_experience_engine import natural_reply
    from test_emlis_q2_application import answer

    user, parent, service, calls = natural_case
    memo = '褒められたのに、嬉しくなかった。'
    action = '会議で発表した。'
    supplement = 'その時は重かった。'
    qdb.query('update public.emotions set memo=$2,memo_action=$3 where id=$1', [parent, memo, action])
    initial = run(service.start(user, parent))
    prompt = initial['pending_question']['text']
    assert prompt == '「褒められた」は、あなたにはどんな意味として届きましたか。'
    failed = False

    async def fail_first_observation_save(name, payload, **kwargs):
        nonlocal failed
        if not failed and any(e['kind'] == 'OBSERVATION' for e in payload.get('p_events', [])):
            failed = True
            return httpx.Response(503, json={'code': '57P03'})
        return await qdb.rpc(name, payload, **kwargs)

    def previous_writer(*args, **kwargs):
        kwargs['include_received_answer'] = False
        return prepare_natural_reply(*args, **kwargs)

    monkeypatch.setattr(emlis_thread_store, 'sb_post_rpc', fail_first_observation_save)
    with monkeypatch.context() as old:
        if old_writer:
            old.setattr(natural_reply, 'prepare_natural_reply', previous_writer)
        pending = run(answer(service, user, initial, supplement))
    assert failed and pending['can_retry'] and len(calls) == 2
    request = calls[-1]
    messages = build_natural_reply_messages(request)
    message = json.loads(messages[-1]['content'])
    if old_writer:
        assert 'records' in message
        assert prompt in messages[-1]['content']
        version = natural_reply.SOURCE_CONTEXT_VERSION
    else:
        assert message['今回の場面'] == {'起きたこと': '褒められた', 'その時の反応': '嬉しくなかった',
                                      '補足': supplement, '思考欄の原文': memo}
        assert '行動欄' not in message
        assert action not in messages[-1]['content']
        assert prompt not in messages[-1]['content']
        version = natural_reply.RECEIVED_ANSWER_CONTEXT_VERSION
    material = json.loads(request.analysis_material_json)
    assert material['coverage']['active_state'] == 'PENDING' and not material['active_fields']
    assert (material['original_record']['memo'], material['original_record']['memo_action']) == (memo, action)
    before = run(service.store.read(user, input_id=parent))
    receipt = [e for e in before['events'] if e['payload'].get('stage') == 'NATURAL_REPLY_RECEIVED'][-1]['payload']
    assert receipt['writer_context_version'] == version
    encoded = json.dumps(messages, ensure_ascii=False, separators=(',', ':')).encode()
    assert receipt['writer_messages_sha256'] == hashlib.sha256(encoded).hexdigest()

    async def no_new_author(material):
        raise AssertionError('the saved reply must not generate again')

    restarted = EmlisThreadService(runtime_profile=Q3_PROFILE, natural_reply_source=no_new_author)
    result = run(restarted.action(user, pending['thread_id'], action='retry_response',
        expected_revision=pending['revision'], idempotency_key='resume-received-answer',
        operation_id=pending['operation_id']))
    assert result['current_observation']['text'] == receipt['reply']['text']
    assert run(restarted.get(user, parent))['current_observation'] == result['current_observation']
    after = run(service.store.read(user, input_id=parent))
    artifact = _observations(after)[-1]['payload']['artifact']
    assert artifact['analysis_material'] == material
    assert artifact['writer_messages_sha256'] == receipt['writer_messages_sha256']


@pytest.mark.parametrize('action,supplement', [
    ('その時に会議で発表した。', 'その時は重かった。'),
    ('褒められた直後に資料を片づけた。', 'その時は重かった。'),
    ('会議で発表した。', 'その時は重かった。分かりません。'),
])
def test_received_answer_only_uses_fully_bound_sources(natural_case, qdb, action, supplement):
    from cocolon_meaning_experience_engine.natural_reply import SOURCE_CONTEXT_VERSION
    from test_emlis_q2_application import answer

    user, parent, service, calls = natural_case
    qdb.query('update public.emotions set memo=$2,memo_action=$3 where id=$1',
        [parent, '褒められたのに、嬉しくなかった。', action])
    initial = run(service.start(user, parent))
    final = run(answer(service, user, initial, supplement))
    assert final['body_state'] == 'REFINED'
    writer = json.loads(calls[-1].writer_material_json)
    assert writer['source_context_version'] == SOURCE_CONTEXT_VERSION
    assert 'received_answer_dialogue' not in writer
