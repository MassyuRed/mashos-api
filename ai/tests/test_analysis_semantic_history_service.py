"""Normal semantic history lifecycle over real PostgreSQL transactions.

All provider packets in this file are independently synthetic. These checks
establish source, acquisition and atomic persistence behavior, not model
interpretation quality or real 4B capacity.
"""
from copy import deepcopy
import asyncio
import hashlib
import json

from fastapi import FastAPI, HTTPException
import httpx
import pytest

import analysis_cumulative_service as cumulative
import analysis_model_source as model_sources
import analysis_observed_service as observed
import analysis_semantic_map as semantic
from test_analysis_cumulative import OWNER, source_snapshot
from test_analysis_cumulative_model_source import sql_source
from test_analysis_interpretation_correction_sources import sql_script
from test_emlis_q2_application import run


@pytest.fixture
def history_db(sql_source, monkeypatch):
    db, rpc = sql_source
    for name in (
        '20261107071033_analysis_semantic_map_wire.sql',
        '20261114032520_analysis_interpretation_correction_sources.sql',
        '20261114120000_analysis_if_route_artifacts.sql',
        '20261114123000_analysis_emlis_material_handoff.sql',
        '20261114132000_analysis_map_interpretation_corrections.sql',
        '20261114133000_analysis_map_correction_handoff.sql',
    ):
        sql_script(db, name)
    calls = []

    async def tracked(name, payload):
        calls.append((name, deepcopy(payload)))
        return await rpc(name, payload)

    monkeypatch.setenv('COCOLON_ANALYSIS_OBSERVED_MODE', 'development')
    monkeypatch.setattr(cumulative, '_rpc', tracked)
    monkeypatch.setattr(observed, '_rpc', tracked)
    return db, tracked, calls


def insert_history(db, count=3):
    assert 'code' not in db.query('insert into auth.users values ($1)', [OWNER])
    assert 'code' not in db.query("insert into public.profiles values ($1,'premium')", [OWNER])
    rows = source_snapshot(count, tier='premium')['members']
    for index, row in enumerate(rows):
        original = row['original']
        original.update(memo=f'私は資料{index + 1}を読んだ。',
            memo_action=f'私は費用{index + 1}を記録した。',
            emotion_details=[dict(type='平穏', strength='medium')])
        result = db.query('insert into public.emotions values ($1,$2,$3,$4,$5,$6,$7,$8)',
            [original['id'], OWNER, original['created_at'], original['memo'], original['memo_action'],
             original['category'], original['emotions'], json.dumps(original['emotion_details'])])
        assert 'code' not in result, result
    return [row['original'] for row in rows]


def map_packet(fields, *, selected=None, edge=True, roots_per_node=1):
    usable = [field for field in fields if selected is None or field['field'] in selected]
    groups = [usable[index:index + roots_per_node] for index in range(0, len(usable), roots_per_node)]
    nodes = [dict(node_id=f'n{index}', node_kind='CHOICE_OUTPUT',
        title=f'記録の内容{index}', summary='本人が記した内容を参照します。',
        explanation='この項目は本人の記録にある内容に基づいています。',
        perspective='SELF', unknowns=[], evidence=[dict(field=field['field'], quote=field['text']) for field in group])
        for index, group in enumerate(groups, 1)]
    edges = ([dict(from_='n1', to=f'n{len(nodes)}', relation_kind='CONTEXT_CONTRAST',
        label='記録された内容の比較', explanation='それぞれの記録の内容を分けて見比べます。')]
        if edge and len(nodes) >= 2 else [])
    for item in edges:
        item['from'] = item.pop('from_')
    return dict(schema_version=semantic.MODEL_SCHEMA,
        overview=dict(title='記録から見たこと', summary='本人が残した記録を分けて読みます。'),
        nodes=nodes, edges=edges)


def provider(handler):
    return model_sources.SelfHostedSemanticAnalysisModelSource(
        endpoint='https://synthetic-history.invalid/v1/chat/completions',
        model='synthetic-semantic-history', api_key='synthetic-private-key',
        transport=httpx.MockTransport(handler))


def provider_response(packet, *, finish='stop'):
    return httpx.Response(200, json=dict(model='synthetic-semantic-history', choices=[dict(
        finish_reason=finish, message=dict(role='assistant', content=json.dumps(packet, ensure_ascii=False)))]))


def stored_private(db, report_id):
    result = db.query('select private_evidence from public.analysis_observed_artifacts where id=$1', [report_id])
    assert 'code' not in result, result
    return result['rows'][0]['private_evidence']


def generation_commits(calls):
    return [payload for name, payload in calls
            if name == 'analysis_cumulative_commit' and 'p_artifact_id' in payload]


def force_synthetic_partition(monkeypatch, *, records_per_leaf=1):
    """A deterministic test budget; this is not a tokenizer measurement."""
    def fits(prepared):
        if getattr(prepared, 'kind', None) == 'MERGE':
            return True
        refs = getattr(prepared, 'record_refs', None)
        count = len(refs) if refs is not None else len(prepared.request.members)
        return count <= records_per_leaf
    monkeypatch.setattr(model_sources, 'semantic_analysis_input_fits', fits)


def stage_material(request):
    body = json.loads(request.content)
    return json.loads(body['messages'][1]['content'])


def successful_history_source(received, *, mutate=None, select_final=None, roots_per_node=1,
                              leaf_field_limit=None):
    def handler(request):
        material = stage_material(request)
        received.append(deepcopy(material))
        kind = material.get('history_stage', {}).get('kind')
        selected = select_final if kind == 'MERGE' else None
        if kind == 'LEAF' and leaf_field_limit is not None:
            selected = {field['field'] for field in material['fields'][:leaf_field_limit]}
        packet = map_packet(material['fields'], selected=selected, roots_per_node=roots_per_node)
        if mutate is not None:
            altered = mutate(material, packet, len(received))
            if altered is not None:
                return altered
        return provider_response(packet)
    return provider(handler)


def assert_no_new_artifacts(db, expected=0):
    assert db.query('select count(*) as n from public.analysis_observed_artifacts')['rows'][0]['n'] == expected


def test_three_leaf_semantic_history_saves_once_and_cross_boundary_evidence_rereads(history_db, monkeypatch):
    db, rpc, calls = history_db
    originals = insert_history(db)
    force_synthetic_partition(monkeypatch)
    received = []
    current = run(cumulative.ensure_map(OWNER, model_source=successful_history_source(received)))
    assert [m['history_stage']['kind'] for m in received] == ['LEAF', 'LEAF', 'LEAF', 'MERGE']
    leaves, merge = received[:3], received[3]
    assert all(len(m['records']) == 1 and len(m['fields']) == 2 for m in leaves)
    assert sorted(f['field'] for m in leaves for f in m['fields']) == list(range(1, 7))
    assert len(generation_commits(calls)) == 1
    assert current['refreshed'] and current['map_context']['source_count'] == 3
    assert current['map_context']['processed_count'] == current['map_context']['mapped_count'] == 3
    assert current['map_context']['unparsed_count'] == current['map_context']['excluded_count'] == 0
    private = stored_private(db, current['report_id'])
    assert private['coverage'] == current['map_context']
    assert set(private['source_record_refs']) == {original['id'] for original in originals}
    assert len(private['source_members']) == 3
    graph = private['graph']
    assert len(graph['edges']) == 1
    left = next(n for n in graph['nodes'] if n['node_ref'] == graph['edges'][0]['from_ref'])
    right = next(n for n in graph['nodes'] if n['node_ref'] == graph['edges'][0]['to_ref'])
    assert set(left['record_refs']).isdisjoint(right['record_refs'])
    for node in graph['nodes']:
        evidence = run(cumulative.map_evidence(OWNER, current['report_id'], node['node_ref']))['items']
        assert evidence and all(item['version_state'] == 'CURRENT' for item in evidence)
    assert merge['leaf_interpretations'] and merge['field_manifest']
    # The same current and pinned month are ordinary non-generating reads.
    forbidden = provider(lambda request: (_ for _ in ()).throw(AssertionError('saved read generated')))
    for kwargs in (dict(ensure=False), dict(monthly=True, force=True)):
        saved = run(cumulative.ensure_map(OWNER, model_source=forbidden, **kwargs))
        assert saved['report_id'] == current['report_id'] and saved['content_text'] == current['content_text']
    assert len(generation_commits(calls)) == 1


def test_history_final_coverage_counts_unmapped_records_without_losing_source_manifest(history_db, monkeypatch):
    db, _, calls = history_db
    originals = insert_history(db)
    force_synthetic_partition(monkeypatch)
    received = []
    current = run(cumulative.ensure_map(OWNER,
        model_source=successful_history_source(received, select_final={1})))
    assert len(received) == 4 and len(generation_commits(calls)) == 1
    counts = current['map_context']
    assert counts['source_count'] == counts['processed_count'] == 3
    assert counts['mapped_count'] == 1 and counts['unparsed_count'] == 2
    private = stored_private(db, current['report_id'])
    assert len(private['source_members']) == 3
    assert set(private['source_record_refs']) == {original['id'] for original in originals}


@pytest.mark.parametrize('failure_call', [2, 4])
def test_history_provider_failure_never_commits_a_partial_map(history_db, monkeypatch, failure_call):
    db, _, calls = history_db
    insert_history(db)
    force_synthetic_partition(monkeypatch)
    received = []
    def fail(material, packet, number):
        return httpx.Response(503) if number == failure_call else None
    with pytest.raises(HTTPException) as error:
        run(cumulative.ensure_map(OWNER, model_source=successful_history_source(received, mutate=fail)))
    assert error.value.status_code == 503
    assert len(received) == failure_call and generation_commits(calls) == []
    assert_no_new_artifacts(db)
    assert db.query('select count(*) as n from public.analysis_cumulative_months')['rows'][0]['n'] == 0


@pytest.mark.parametrize('defect', ['leaf_foreign_field', 'merge_invented_quote', 'empty_leaf', 'incomplete_leaf'])
def test_history_invalid_stage_never_reaches_atomic_commit(history_db, monkeypatch, defect):
    db, _, calls = history_db
    insert_history(db)
    force_synthetic_partition(monkeypatch)
    received = []
    def damage(material, packet, number):
        kind = material['history_stage']['kind']
        if defect == 'leaf_foreign_field' and number == 1:
            packet['nodes'][0]['evidence'][0]['field'] = 999
        elif defect == 'merge_invented_quote' and kind == 'MERGE':
            packet['nodes'][0]['evidence'][0]['quote'] = '本人はいつも賛成していました。'
        elif defect == 'empty_leaf' and number == 1:
            packet['nodes'] = []; packet['edges'] = []
        elif defect == 'incomplete_leaf' and number == 1:
            return provider_response(packet, finish='length')
    with pytest.raises(HTTPException) as error:
        run(cumulative.ensure_map(OWNER, model_source=successful_history_source(received, mutate=damage)))
    assert error.value.status_code in {422, 503}
    assert generation_commits(calls) == []
    assert_no_new_artifacts(db)


def test_history_nonfirst_source_edit_during_leafs_rejects_whole_final_commit(history_db, monkeypatch):
    db, _, calls = history_db
    originals = insert_history(db)
    force_synthetic_partition(monkeypatch)
    received = []
    def edit(material, packet, number):
        if number == 2:
            result = db.query('update public.emotions set memo=$2 where id=$1',
                [originals[-1]['id'], '私は別の予定を決めた。'])
            assert 'code' not in result, result
    with pytest.raises(HTTPException) as error:
        run(cumulative.ensure_map(OWNER, model_source=successful_history_source(received, mutate=edit)))
    assert error.value.status_code == 409 and error.value.detail == '40001'
    assert len(received) == 4 and len(generation_commits(calls)) == 1
    assert_no_new_artifacts(db)


def test_forced_history_refresh_preserves_first_month_and_new_current_reentry(history_db, monkeypatch):
    db, _, calls = history_db
    insert_history(db)
    # Establish the actual month with the existing one-request semantic owner.
    monkeypatch.setattr(model_sources, 'semantic_analysis_input_fits', lambda prepared: True)
    initial_received = []
    initial = run(cumulative.ensure_map(OWNER,
        model_source=successful_history_source(initial_received)))
    initial_private = deepcopy(stored_private(db, initial['report_id']))
    month = run(cumulative.ensure_map(OWNER, monthly=True))
    force_synthetic_partition(monkeypatch)
    received = []
    updated = run(cumulative.ensure_map(OWNER, force=True,
        model_source=successful_history_source(received)))
    assert len(initial_received) == 1 and len(received) == 4
    assert updated['report_id'] != initial['report_id'] and len(generation_commits(calls)) == 2
    forbidden = provider(lambda request: (_ for _ in ()).throw(AssertionError('reentry generated')))
    saved = run(cumulative.ensure_map(OWNER, ensure=False, model_source=forbidden))
    historical = run(cumulative.ensure_map(OWNER, monthly=True, force=True, model_source=forbidden))
    assert saved['report_id'] == updated['report_id'] and saved['meta'] == updated['meta']
    assert historical['report_id'] == initial['report_id'] and historical['meta'] == month['meta']
    assert historical['captured_at'] == month['captured_at']
    assert stored_private(db, initial['report_id']) == initial_private


@pytest.mark.parametrize('impossible', ['four_leaves', 'one_record_group', 'single_leaf_plan'])
def test_history_unplannable_complete_input_refuses_before_provider_call(history_db, monkeypatch, impossible):
    db, _, calls = history_db
    insert_history(db, 4 if impossible == 'four_leaves' else 1)
    force_synthetic_partition(monkeypatch)
    if impossible == 'one_record_group':
        monkeypatch.setattr(model_sources, 'semantic_analysis_input_fits', lambda prepared: False)
    elif impossible == 'single_leaf_plan':
        # A reduced LEAF view can fit when the parent retains extra excluded
        # handoff control. A one-leaf plan cannot satisfy the merge contract.
        monkeypatch.setattr(model_sources, 'semantic_analysis_input_fits',
            lambda prepared: getattr(prepared, 'kind', None) == 'LEAF')
    received = []
    with pytest.raises(HTTPException) as error:
        run(cumulative.ensure_map(OWNER, model_source=successful_history_source(received)))
    assert error.value.status_code in {422, 503}
    assert received == [] and generation_commits(calls) == []
    assert_no_new_artifacts(db)


def test_history_merge_over_budget_never_posts_or_saves_a_partial_map(history_db, monkeypatch):
    db, _, calls = history_db
    insert_history(db)
    def fits(prepared):
        if getattr(prepared, 'kind', None) == 'MERGE':
            return False
        refs = getattr(prepared, 'record_refs', None)
        return (len(refs) if refs is not None else len(prepared.request.members)) == 1
    monkeypatch.setattr(model_sources, 'semantic_analysis_input_fits', fits)
    received = []
    with pytest.raises(HTTPException) as error:
        run(cumulative.ensure_map(OWNER, model_source=successful_history_source(received)))
    assert error.value.status_code in {422, 503}
    assert len(received) == 3 and all(m['history_stage']['kind'] == 'LEAF' for m in received)
    assert generation_commits(calls) == []
    assert_no_new_artifacts(db)


def test_http_latest_uses_normal_semantic_history_then_reads_same_saved_map(history_db, monkeypatch):
    import api_self_structure as latest
    from unittest.mock import AsyncMock
    db, _, calls = history_db
    insert_history(db)
    force_synthetic_partition(monkeypatch)
    received = []
    source = successful_history_source(received)
    monkeypatch.setattr(model_sources, 'application_analysis_model_source', lambda: source)
    monkeypatch.setattr(latest, '_resolve_user_id_from_token', AsyncMock(return_value=OWNER))
    app = FastAPI()
    latest.register_self_structure_routes(app)

    async def scenario():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                base_url='https://synthetic-app.invalid') as client:
            headers = {'Authorization': 'Bearer synthetic-owner-token', 'X-Watashi-Map-Renderer': 'semantic.v1'}
            first = await client.get('/self-structure/latest?ensure=true', headers=headers)
            assert first.status_code == 200, first.text
            payload = first.json()
            saved = await client.get('/self-structure/latest?ensure=false&force=true', headers=headers)
            assert saved.status_code == 200, saved.text
            again = saved.json()
            assert again['report_id'] == payload['report_id']
            assert again['meta'] == payload['meta']
            assert again['content_text'] == payload['content_text']
            assert not again['refreshed']
            return payload

    payload = run(scenario())
    assert len(received) == 4 and len(generation_commits(calls)) == 1
    assert payload['map_context']['source_count'] == payload['map_context']['mapped_count'] == 3


def test_history_one_pipeline_deadline_prevents_per_call_budget_reset(history_db, monkeypatch):
    db, _, calls = history_db
    insert_history(db)
    force_synthetic_partition(monkeypatch)
    monkeypatch.setattr(model_sources, 'SEMANTIC_PIPELINE_TIMEOUT_SECONDS', 0.12)
    received, completed = [], []

    async def handler(request):
        material = stage_material(request)
        received.append(material)
        # Every individual acquisition fits 0.12s; their total does not.
        await asyncio.sleep(0.05)
        completed.append(material)
        return provider_response(map_packet(material['fields']))

    with pytest.raises(HTTPException) as error:
        run(cumulative.ensure_map(OWNER, model_source=provider(handler)))
    assert error.value.status_code == 504 and error.value.detail == 'analysis_model_source_timeout'
    assert 1 <= len(completed) <= len(received) <= 3
    assert generation_commits(calls) == []
    assert_no_new_artifacts(db)


def test_overlapping_history_requests_share_one_pipeline_and_one_sql_save(history_db, monkeypatch):
    db, _, calls = history_db
    insert_history(db)
    force_synthetic_partition(monkeypatch)
    received = []

    async def handler(request):
        material = stage_material(request)
        received.append(material)
        await asyncio.sleep(0)
        return provider_response(map_packet(material['fields']))

    source = provider(handler)
    async def scenario():
        return await asyncio.gather(cumulative.ensure_map(OWNER, model_source=source),
            cumulative.ensure_map(OWNER, model_source=source))
    first, second = run(scenario())
    assert len(received) == 4 and len(generation_commits(calls)) == 1
    assert first == second and first is not second
    assert first['report_id'] == second['report_id']
    first['meta']['overview']['title'] = 'LOCAL_DTO_MUTATION'
    assert second['meta']['overview']['title'] != 'LOCAL_DTO_MUTATION'
    assert_no_new_artifacts(db, 1)


def test_failed_history_pipeline_is_not_automatically_retried_but_fresh_call_can_succeed(history_db, monkeypatch):
    db, _, calls = history_db
    insert_history(db)
    force_synthetic_partition(monkeypatch)
    received = []
    def fail_once(material, packet, number):
        return httpx.Response(503) if number == 2 else None
    source = successful_history_source(received, mutate=fail_once)
    with pytest.raises(HTTPException):
        run(cumulative.ensure_map(OWNER, model_source=source))
    assert len(received) == 2 and generation_commits(calls) == []
    assert_no_new_artifacts(db)
    saved = run(cumulative.ensure_map(OWNER, model_source=source))
    assert len(received) == 6 and len(generation_commits(calls)) == 1
    assert saved['refreshed'] and saved['map_context']['source_count'] == 3
    assert_no_new_artifacts(db, 1)


def test_failed_history_refresh_keeps_previous_current_and_month_visible(history_db, monkeypatch):
    db, _, calls = history_db
    insert_history(db)
    monkeypatch.setattr(model_sources, 'semantic_analysis_input_fits', lambda prepared: True)
    initial = run(cumulative.ensure_map(OWNER, model_source=successful_history_source([])))
    previous_private = deepcopy(stored_private(db, initial['report_id']))
    force_synthetic_partition(monkeypatch)
    received = []
    def fail_merge(material, packet, number):
        return httpx.Response(503) if material['history_stage']['kind'] == 'MERGE' else None
    with pytest.raises(HTTPException) as error:
        run(cumulative.ensure_map(OWNER, force=True,
            model_source=successful_history_source(received, mutate=fail_merge)))
    assert error.value.status_code == 503 and len(received) == 4
    assert len(generation_commits(calls)) == 1
    assert_no_new_artifacts(db, 1)
    forbidden = provider(lambda request: (_ for _ in ()).throw(AssertionError('failed-refresh read generated')))
    for kwargs in (dict(ensure=False), dict(monthly=True, force=True)):
        saved = run(cumulative.ensure_map(OWNER, model_source=forbidden, **kwargs))
        assert saved['report_id'] == initial['report_id'] and saved['content_text'] == initial['content_text']
    assert stored_private(db, initial['report_id']) == previous_private


def test_real_map_correction_cohort_stays_together_and_whole_explanation_reaches_new_history_map(history_db, monkeypatch):
    import analysis_map_correction_service as corrections
    db, rpc, calls = history_db
    insert_history(db)
    old_text = '二つの記録から、普段から確認を急ぐように読みました。'
    explanation = ('その推定は違います。この二回は締切が近かったので確認しました。'
                   '普段から確認を急いでいるわけではありません。')
    monkeypatch.setattr(model_sources, 'semantic_analysis_input_fits', lambda prepared: True)

    def old_handler(request):
        material = stage_material(request)
        packet = map_packet(material['fields'], selected={1}, edge=False)
        other = next(field for field in material['fields'] if field['field'] == 3)
        packet['nodes'][0]['evidence'].append(dict(field=3, quote=other['text']))
        packet['nodes'][0]['explanation'] = old_text
        return provider_response(packet)

    old = run(cumulative.ensure_map(OWNER, model_source=provider(old_handler)))
    old_private = deepcopy(stored_private(db, old['report_id']))
    assert len(old_private['graph']['nodes'][0]['record_refs']) == 2
    month = run(cumulative.ensure_map(OWNER, monthly=True))
    receipt = run(corrections.submit_map_correction(OWNER, dict(
        artifact_ref=old['meta']['projection_of'], kind='node', ref='n1', field='explanation',
        target_text=old_text, explanation=explanation, idempotency_key='history-cohort-correction')))
    assert receipt['source_state'] == 'ACTIVE'
    force_synthetic_partition(monkeypatch, records_per_leaf=2)
    received = []
    updated = run(cumulative.ensure_map(OWNER, force=True,
        model_source=successful_history_source(received)))
    assert [m['history_stage']['kind'] for m in received] == ['LEAF', 'LEAF', 'MERGE']
    corrected_leaf, = [m for m in received[:-1] if any(
        f['source_role'] == 'USER_ANALYSIS_MAP_CORRECTION' for f in m['fields'])]
    assert len(corrected_leaf['records']) == 2
    correction_field, = [f for f in corrected_leaf['fields']
        if f['source_role'] == 'USER_ANALYSIS_MAP_CORRECTION']
    assert correction_field['text'] == explanation and correction_field['record'] is None
    assert len(correction_field['record_refs']) == 2
    private = stored_private(db, updated['report_id'])
    assert private['source_guard'] != old_private['source_guard']
    assert updated['map_context']['source_count'] == updated['map_context']['mapped_count'] == 3
    assert updated['map_context']['excluded_count'] == 0
    assert len(generation_commits(calls)) == 2
    assert any(root['literal_sha256'] == hashlib.sha256(explanation.encode()).hexdigest()
        for node in private['graph']['nodes'] for root in node['evidence_refs'])
    # Historical identity and bytes are not retrofitted with a new correction.
    saved_month = run(cumulative.ensure_map(OWNER, monthly=True))
    assert saved_month['report_id'] == old['report_id'] and saved_month['meta'] == month['meta']
    assert stored_private(db, old['report_id']) == old_private


def test_real_sql_201_record_history_keeps_oldest_and_all_fields_in_three_leaves(history_db, monkeypatch):
    """The injected budget proves whole-source wiring, not 4B token capacity."""
    db, _, calls = history_db
    originals = insert_history(db, 201)
    force_synthetic_partition(monkeypatch, records_per_leaf=67)
    received = []
    current = run(cumulative.ensure_map(OWNER,
        model_source=successful_history_source(received, leaf_field_limit=1)))
    assert [m['history_stage']['kind'] for m in received] == ['LEAF', 'LEAF', 'LEAF', 'MERGE']
    assert [len(m['records']) for m in received[:3]] == [67, 67, 67]
    assert sorted(f['field'] for m in received[:3] for f in m['fields']) == list(range(1, 403))
    assert len(generation_commits(calls)) == 1
    counts = current['map_context']
    assert counts['source_count'] == counts['processed_count'] == 201
    assert counts['mapped_count'] == 3 and counts['unparsed_count'] == 198
    assert counts['excluded_count'] == 0
    private = stored_private(db, current['report_id'])
    expected = {original['id'] for original in originals}
    assert len(private['source_members']) == 201 and set(private['source_record_refs']) == expected
    assert {ref for node in private['graph']['nodes'] for ref in node['record_refs']} == {
        originals[index]['id'] for index in (0, 67, 134)}
    first = next(node for node in private['graph']['nodes'] if originals[0]['id'] in node['record_refs'])
    items = run(cumulative.map_evidence(OWNER, current['report_id'], first['node_ref']))['items']
    oldest = next(item for item in items if item['id'] == originals[0]['id'])
    assert oldest['memo'] == originals[0]['memo'] and oldest['version_state'] == 'CURRENT'


def test_small_fit_keeps_one_exact_semantic_request_then_only_reads_saved_sql(history_db, monkeypatch):
    db, rpc, calls = history_db
    insert_history(db, 2)
    received, prepared = [], []
    original_prepare = semantic.prepare_semantic_map

    def capture(*args, **kwargs):
        value = original_prepare(*args, **kwargs)
        prepared.append(value)
        return value

    monkeypatch.setattr(semantic, 'prepare_semantic_map', capture)

    def handler(request):
        body = json.loads(request.content)
        received.append(body)
        assert len(prepared) == 1 and body['messages'] == prepared[0].messages()
        material = json.loads(body['messages'][1]['content'])
        return provider_response(map_packet(material['fields']))

    source = provider(handler)
    first = run(cumulative.ensure_map(OWNER, model_source=source))
    before, = prepared
    assert first['refreshed'] and len(received) == 1
    assert len(generation_commits(calls)) == 1
    assert first['map_context']['source_count'] == first['map_context']['processed_count'] == 2
    assert first['map_context']['mapped_count'] == 2 and first['map_context']['unparsed_count'] == 0
    private = stored_private(db, first['report_id'])
    assert private['source_guard'] == before.source_guard
    assert private['coverage'] == first['map_context'] and len(private['source_members']) == 2

    def forbidden(request):
        raise AssertionError('saved semantic history read acquired a provider response')

    saved_source = provider(forbidden)
    for options in ({}, dict(ensure=False, force=True), dict(monthly=True, force=True)):
        saved = run(cumulative.ensure_map(OWNER, model_source=saved_source, **options))
        assert saved['report_id'] == first['report_id'] and saved['content_text'] == first['content_text']
        assert not saved['refreshed']
    assert len(generation_commits(calls)) == 1 and len(received) == 1
