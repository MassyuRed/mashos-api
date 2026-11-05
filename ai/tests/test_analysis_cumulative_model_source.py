"""Explicit source lifecycle; all responses here are independently synthetic."""
import asyncio
import copy
from dataclasses import replace
import json
import os
from pathlib import Path
from unittest.mock import AsyncMock, patch
from uuid import UUID

from fastapi import HTTPException
import pytest

import analysis_cumulative_service as service
from test_analysis_cumulative import OWNER, source_snapshot
from test_analysis_model_observed_roles import material
from test_analysis_model_quoted_parent_units import call
from test_analysis_saved_period import with_answer


def synthetic_response(prepared):
    fields = json.loads(prepared.messages()[1]['content'])['fields']
    packet = dict(fields=[dict(field=f['field'], units=[dict(quote=text,
        node_kind='ROLE' if 'の役割は' in text or '担当' in text else 'ACTION_OR_NONACTION',
        parent_quote=None, scope_role=None, qualifiers=[])
        for text in f['text'].rstrip('。').split('。')]) for f in fields])
    return call(prepared, packet).response


def run(awaitable):
    return asyncio.run(awaitable)


@pytest.mark.parametrize('defect', ['request', 'messages', 'raw', 'hash', 'finish',
    'missing', 'wrong_type', 'invalid_json', 'source_failure', 'stale_clock', 'foreign_owner'])
def test_bad_response_is_not_saved_or_replaced_with_finite_output(monkeypatch, defect):
    snap = material('pair')
    prepared = service.prepare_cumulative_category_units(OWNER, snap, prompt_version='selected_material.v4')
    response = synthetic_response(prepared)
    if defect == 'request': response = replace(response, request_ref='foreign')
    if defect == 'messages': response = replace(response, messages_sha256='0'*64)
    if defect == 'raw': response = replace(response, raw=response.raw+' ')
    if defect == 'hash': response = replace(response, raw_sha256='0'*64)
    if defect == 'finish': response = replace(response, finish_reason='length')
    if defect == 'missing': response = None
    if defect == 'wrong_type': response = prepared
    if defect == 'invalid_json': response = call(prepared, raw='{"fields":NaN}').response
    if defect == 'stale_clock': snap = dict(snap, now='2026-11-01T08:00:01+00:00', period_end='2026-11-01T08:00:01+00:00')
    if defect == 'foreign_owner':
        other = service.prepare_cumulative_category_units(str(UUID(int=2)), snap, prompt_version='selected_material.v4')
        response = synthetic_response(other)
    source = AsyncMock(side_effect=ValueError('unavailable')) if defect == 'source_failure' else AsyncMock(return_value=response)
    async def rpc(name, payload):
        if name == 'analysis_cumulative_read':
            return dict(items=[], subscription_tier='free', matched=True, history_limit=2)
        assert name == 'analysis_cumulative_source_snapshot', 'invalid response reached commit'
        return snap
    monkeypatch.setattr(service, '_rpc', rpc)
    monkeypatch.setattr(service, 'observed_mode', lambda:'development')
    with pytest.raises(HTTPException) as error:
        run(service.ensure_map(OWNER, model_source=source))
    assert error.value.status_code == 422
    source.assert_awaited_once()


@pytest.mark.parametrize('scope', ['empty', 'safety'])
def test_unqualified_source_does_not_acquire_a_response(monkeypatch, scope):
    snap = source_snapshot(0 if scope == 'empty' else 1)
    if scope == 'safety': snap['members'][0]['original']['memo'] = '死にたい。'
    source = AsyncMock(side_effect=AssertionError('unqualified source acquisition'))
    monkeypatch.setattr(service, 'read_maps', AsyncMock(return_value={'items':[]}))
    monkeypatch.setattr(service, '_rpc', AsyncMock(return_value=snap))
    monkeypatch.setattr(service, 'observed_mode', lambda:'development')
    with pytest.raises(HTTPException) as error:
        run(service.ensure_map(OWNER, model_source=source))
    assert error.value.status_code == 422
    source.assert_not_awaited()


def multi_material():
    snap = source_snapshot(7)
    bodies = [
        ('僕の役割は受付係だった。', ''),
        ('僕の役割は受付係だった。', '僕は費用を記録した。'),
        ('僕の役割は案内係だった。費用を記録した。', ''),
        ('僕の役割は案内係だった。僕は資料を調べた。', ''),
        ('私は会合の進行を担当した。その後、私は分担を決めた。', ''),
        ('僕は費用を記録しなかった。', ''),
        ('まだ言葉にはできません。', ''),
    ]
    for i, (member, (memo, action)) in enumerate(zip(snap['members'], bodies)):
        member['original'].update(memo=memo, memo_action=action,
            category=['仕事'] if i % 2 == 0 else ['生活'])
    return snap


def multi_proposal(snap):
    prepared = service.prepare_cumulative_category_units(OWNER, snap, prompt_version='selected_material.v4')
    return replace(prepared, response=synthetic_response(prepared))


def answer_material(original='私は資料を見た。', answer='私は費用を記録した。'):
    snap = source_snapshot(1)
    snap['members'][0]['original'].update(memo=original, memo_action='',
        emotion_details=[dict(type='平穏', strength='medium')])
    snap['members'][0] = with_answer(snap['members'][0], answer)
    return snap


@pytest.mark.parametrize('prompt', ['selected_material.v3', 'selected_material.v4'])
@pytest.mark.parametrize('original,answer,role,duplicate', [
    ('僕の役割は受付係だった。', '僕は費用を記録した。', True, False),
    ('私は資料を見た。', '私は費用を記録しなかった。', False, False),
    ('私は資料を見た。', '私は資料を見ました。', False, True),
])
def test_ordinary_answer_keeps_own_witness_and_one_record_occasion(prompt, original, answer, role, duplicate):
    snap = answer_material(original, answer)
    prepared = service.prepare_cumulative_category_units(OWNER, snap, prompt_version=prompt)
    artifact, counts = service.build_cumulative_map(OWNER, snap,
        model_input=replace(prepared, response=synthetic_response(prepared)))
    assert counts['source_count'] == counts['processed_count'] == counts['mapped_count'] == 1
    assert counts['unparsed_count'] == 0 and len(artifact.source_members) == 1
    assert len(artifact.graph.nodes) == (1 if duplicate else 2) and not artifact.graph.edges
    fields = json.loads(prepared.messages()[1]['content'])['fields']
    assert [f['source_role'] for f in fields] == ['ORIGINAL_INPUT', 'SUPPLEMENTAL_ANSWER']
    assert fields[0]['record'] == fields[1]['record'] == 1
    envelopes = {e.source_envelope_id for n in artifact.graph.nodes for e in n.evidence_refs}
    assert len(envelopes) == 2 and envelopes == set(artifact.source_members[0].child_source_envelope_refs)
    assert all(n.record_refs == (snap['members'][0]['original']['id'],)
        and n.selected_categories == ('仕事',) for n in artifact.graph.nodes)
    projection = artifact.safe_projection(authenticated_owner_scope=OWNER)
    assert all(n['evidence_badge_count'] == 1 for n in projection['nodes'])
    if role:
        assert artifact.graph.nodes[0].proposition.role_state == 'WRITTEN_PAST_ROLE'
        assert '受付係' in artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
    else:
        finite, finite_counts = service.build_cumulative_map(OWNER, snap)
        assert artifact.graph == finite.graph and counts == finite_counts


def test_answer_and_independent_record_keep_categories_without_new_order_or_repetition():
    snap = answer_material(answer='私は資料を調べた。')
    other = source_snapshot(2)['members'][1]
    other['original'].update(memo='私は費用を記録した。', memo_action='', category=['生活'])
    snap['members'].append(other)
    artifact, counts = service.build_cumulative_map(OWNER, snap, model_input=multi_proposal(snap))
    assert counts['source_count'] == counts['mapped_count'] == 2 and counts['unparsed_count'] == 0
    assert len(artifact.graph.nodes) == 3 and not artifact.graph.edges
    assert [n.selected_categories for n in artifact.graph.nodes] == [('仕事',), ('仕事',), ('生活',)]


@pytest.mark.parametrize('defect', ['missing', 'kind', 'sibling_quote'])
def test_answer_requires_its_own_complete_model_proposal_without_finite_rescue(defect):
    snap = answer_material()
    value = multi_proposal(snap)
    packet = json.loads(value.response.raw)
    if defect == 'missing': packet['fields'].pop()
    if defect == 'kind': packet['fields'][1]['units'][0]['node_kind'] = 'ROLE'
    if defect == 'sibling_quote': packet['fields'][1]['units'][0]['quote'] = '私は資料を見た。'
    value = call(replace(value, response=None), packet)
    if defect == 'kind':
        artifact, counts = service.build_cumulative_map(OWNER, snap, model_input=value)
        assert artifact is None and counts['mapped_count'] == 0 and counts['unparsed_count'] == 1
    else:
        with pytest.raises(ValueError):
            service.build_cumulative_map(OWNER, snap, model_input=value)


@pytest.mark.parametrize('defect', ['owner', 'parent', 'round', 'version', 'answer', 'guard'])
def test_answer_or_parent_binding_change_cannot_reuse_previous_whole_response(defect):
    snap = answer_material()
    value = multi_proposal(snap)
    changed = copy.deepcopy(snap)
    member = changed['members'][0]
    answer = next(e for e in member['events'] if e['kind'] == 'ANSWER')
    if defect == 'owner': member['thread']['user_id'] = str(UUID(int=2))
    if defect == 'parent': answer['payload']['source']['original_source_ref'] = 'foreign'
    if defect == 'round': answer['payload']['source']['round_index'] = 2
    if defect == 'version': member['original']['memo'] = '私は資料を調べた。'
    if defect == 'answer': answer['payload']['source']['answer_text_private'] = '私は資料を調べた。'
    if defect == 'guard': changed['guard'] = 'analysis-db-cumulative-v1:' + 'b' * 64
    with pytest.raises(ValueError):
        service.build_cumulative_map(OWNER, changed, model_input=value)


@pytest.mark.parametrize('answer', ['費用を記録した。', '彼は費用を記録した。',
    '私は資料を見なかった。', '「私は資料を見た」を撤回します。',
    '「私は資料を見た」ではなく「私は資料を調べた」です。',
    '私は費用を記録した。まだ言葉にできません。', '死にたい。'])
def test_ineligible_answer_does_not_acquire_a_response_or_inherit_parent_actor(monkeypatch, answer):
    snap = answer_material(answer=answer)
    source = AsyncMock(side_effect=AssertionError('ineligible answer acquisition'))
    monkeypatch.setattr(service, 'read_maps', AsyncMock(return_value={'items': []}))
    monkeypatch.setattr(service, '_rpc', AsyncMock(return_value=snap))
    monkeypatch.setattr(service, 'observed_mode', lambda: 'development')
    with pytest.raises(HTTPException) as error:
        run(service.ensure_map(OWNER, model_source=source))
    assert error.value.status_code == 422
    source.assert_not_awaited()


def test_original_edit_excludes_old_answer_without_a_second_record_or_old_answer_reuse():
    snap = answer_material()
    snap['members'][0]['original']['memo'] = '私は資料を調べた。'
    artifact, counts = service.build_cumulative_map(OWNER, snap, model_input=multi_proposal(snap))
    assert counts['source_count'] == counts['mapped_count'] == counts['stale_supplement_count'] == 1
    assert counts['unparsed_count'] == 0 and len(artifact.graph.nodes) == 1
    assert len(artifact.source_members[0].child_source_envelope_refs) == 1
    assert artifact.graph.nodes[0].proposition.predicate_lemma == '調べる'


def test_supplement_parent_version_and_comparison_remain_unsupported():
    from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import prepare_analysis_model_quoted_parent_units
    prepared = service.prepare_cumulative_category_units(OWNER, answer_material(), prompt_version='selected_material.v4')
    member, = prepared.request.members
    supplement, = member.supplements
    bad_member = replace(member, supplements=(replace(supplement, parent_record_version='foreign'),))
    for request in (replace(prepared.request, members=(bad_member,)),
            replace(prepared.request, comparison_previous_request=prepared.request)):
        with pytest.raises(ValueError):
            prepare_analysis_model_quoted_parent_units(request, source_guard=prepared.source_guard,
                prompt_version='selected_material.v4')


def test_complete_snapshot_keeps_each_witness_unknown_record_category_and_local_order():
    snap = multi_material()
    value = multi_proposal(snap)
    artifact, counts = service.build_cumulative_map(OWNER, snap, model_input=value)
    assert counts == dict(profile='cumulative.v1', source_count=7, processed_count=7,
        mapped_count=6, unparsed_count=2, excluded_count=0, exclusion_reasons={}, stale_supplement_count=0)
    assert len(artifact.source_members) == len(artifact.category_records) == 7
    assert {m.saved_record_ref for m in artifact.source_members} == {m['original']['id'] for m in snap['members']}
    nodes = artifact.graph.nodes
    assert len({n.node_ref for n in nodes}) == len(nodes) == 9
    assert [n.node_ref for n in nodes] == ['n' + str(i) for i in range(1, 10)]
    by_record = {m['original']['id']: [n for n in nodes if m['original']['id'] in n.record_refs]
        for m in snap['members']}
    assert [len(by_record[m['original']['id']]) for m in snap['members']] == [1, 2, 1, 2, 2, 1, 0]
    for member in snap['members']:
        ref = member['original']['id']
        for node in by_record[ref]:
            assert node.record_refs == (ref,)
            assert node.selected_categories == tuple(member['original']['category'])
            assert {e.source_envelope_id for e in node.evidence_refs} <= set(next(
                m.child_source_envelope_refs for m in artifact.source_members if m.saved_record_ref == ref))
    edge, = artifact.graph.edges
    assert edge.edge_kind == 'OBSERVED_ORDER'
    endpoints = [next(n for n in nodes if n.node_ref == r) for r in edge.endpoint_refs]
    assert endpoints[0].record_refs == endpoints[1].record_refs == (snap['members'][4]['original']['id'],)
    text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
    assert '受付係' in text and '案内係' in text and '記録された担当' in text and '行わなかった' in text
    service._checked_projection(artifact.safe_projection(authenticated_owner_scope=OWNER), str(UUID(artifact.artifact_id[9:])))


@pytest.mark.parametrize('count', [2, 201])
def test_all_owned_records_remain_in_one_model_request_including_oldest(count):
    snap = source_snapshot(count)
    for member in snap['members']:
        member['original'].update(memo='僕の役割は受付係だった。', memo_action='')
    value = multi_proposal(snap)
    assert len(json.loads(value.messages()[1]['content'])['fields']) == count
    artifact, counts = service.build_cumulative_map(OWNER, snap, model_input=value)
    assert counts['source_count'] == counts['processed_count'] == counts['mapped_count'] == count
    assert counts['unparsed_count'] == 0 and len(artifact.source_members) == count
    assert {r for n in artifact.graph.nodes for r in n.record_refs} == {m['original']['id'] for m in snap['members']}
    assert not artifact.graph.edges


@pytest.mark.parametrize('different_category', [False, True])
def test_finite_action_equivalence_and_record_badges_use_the_canonical_cumulative_signature(different_category):
    snap = source_snapshot(2)
    for member, memo in zip(snap['members'], ['僕は費用を記録した。', '僕は費用を記録しました。']):
        member['original'].update(memo=memo, memo_action='')
    if different_category: snap['members'][1]['original']['category'] = ['生活']
    artifact, counts = service.build_cumulative_map(OWNER, snap, model_input=multi_proposal(snap))
    finite, finite_counts = service.build_cumulative_map(OWNER, snap)
    assert counts == finite_counts and artifact.graph == finite.graph
    assert len(artifact.graph.nodes) == (2 if different_category else 1)
    projection = artifact.safe_projection(authenticated_owner_scope=OWNER)
    assert [n['evidence_badge_count'] for n in projection['nodes']] == ([1, 1] if different_category else [2])
    assert not artifact.graph.edges


@pytest.mark.parametrize('defect', ['memo', 'category', 'guard', 'owner'])
def test_later_record_or_full_snapshot_identity_cannot_reuse_an_old_response(defect):
    snap = multi_material()
    value = multi_proposal(snap)
    owner = OWNER
    if defect == 'memo': snap['members'][-1]['original']['memo'] += '変更。'
    if defect == 'category': snap['members'][-1]['original']['category'] = ['別場面']
    if defect == 'guard': snap['guard'] = 'analysis-db-cumulative-v1:' + 'b' * 64
    if defect == 'owner': owner = str(UUID(int=2))
    with pytest.raises(ValueError):
        service.build_cumulative_map(owner, snap, model_input=value)


def test_bad_later_record_kind_does_not_borrow_another_records_role_or_finite_fallback():
    snap = multi_material()
    value = multi_proposal(snap)
    packet = json.loads(value.response.raw)
    packet['fields'][4]['units'][0]['node_kind'] = 'ACTION_OR_NONACTION'
    value = call(replace(value, response=None), packet)
    artifact, counts = service.build_cumulative_map(OWNER, snap, model_input=value)
    rejected = snap['members'][3]['original']['id']
    assert all(rejected not in n.record_refs for n in artifact.graph.nodes)
    assert counts['source_count'] == 7 and counts['mapped_count'] == 5 and counts['unparsed_count'] == 3


def test_safety_in_a_later_record_is_rejected_before_acquisition(monkeypatch):
    snap = multi_material()
    snap['members'][-1]['original']['memo'] = '死にたい。'
    source = AsyncMock(side_effect=AssertionError('unsafe response acquisition'))
    monkeypatch.setattr(service, 'read_maps', AsyncMock(return_value={'items': []}))
    monkeypatch.setattr(service, '_rpc', AsyncMock(return_value=snap))
    monkeypatch.setattr(service, 'observed_mode', lambda: 'development')
    with pytest.raises(HTTPException) as error:
        run(service.ensure_map(OWNER, model_source=source))
    assert error.value.status_code == 422
    source.assert_not_awaited()


def test_clause_author_uses_its_own_action_witness_after_canonical_action_aggregation():
    snap = source_snapshot(3)
    for member, memo in zip(snap['members'], ['僕は費用を記録しました。',
            '僕の役割は受付係だった。僕は費用を記録した。', 'まだ言葉にできません。']):
        member['original'].update(memo=memo, memo_action='')
    artifact, counts = service.build_cumulative_map(OWNER, snap, model_input=multi_proposal(snap))
    assert len(artifact.graph.nodes) == 2 and counts['mapped_count'] == 2 and counts['unparsed_count'] == 1
    action, role = artifact.graph.nodes
    assert len(action.record_refs) == len(action.evidence_refs) == 2
    assert role.proposition.role_state == 'WRITTEN_PAST_ROLE_CLAUSE'
    assert '受付係' in artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
    assert any(g.missing_scope == 'SOURCE_SCOPE' for g in artifact.graph.unknown_gaps)


@pytest.mark.parametrize('defect', ['source_records', 'source_members', 'cross_edge', 'cross_gap'])
def test_multi_clause_author_does_not_accept_another_records_proof(defect):
    from cocolon_meaning_experience_engine.cores.analysis import intent_compiler as compiler
    from cocolon_meaning_experience_engine.cores.analysis.source_adapter import AnalysisSourceError
    snap = multi_material()
    artifact, _ = service.build_cumulative_map(OWNER, snap, model_input=multi_proposal(snap))
    clause = next(n for n in artifact.graph.nodes if n.proposition.role_state == 'WRITTEN_PAST_ROLE_CLAUSE')
    other = next(n for n in artifact.graph.nodes if n.record_refs != clause.record_refs)
    if defect == 'source_records': artifact = replace(artifact, category_records=artifact.category_records[:-1])
    if defect == 'source_members': artifact = replace(artifact, source_members=artifact.source_members[:-1])
    if defect == 'cross_edge':
        artifact = replace(artifact, graph=replace(artifact.graph, edges=artifact.graph.edges + (
            compiler.ObservedEdge('e99', 'OBSERVED_ORDER', (clause.node_ref, other.node_ref), clause.evidence_refs + other.evidence_refs),)))
    if defect == 'cross_gap':
        artifact = replace(artifact, graph=replace(artifact.graph, unknown_gaps=artifact.graph.unknown_gaps + (
            compiler.UnknownGap('g99', (clause.node_ref, other.node_ref), 'ROUTE_CONNECTION', 'ONLY_EXPLICIT_ORDER_IS_SHOWN'),)))
    with pytest.raises(AnalysisSourceError):
        artifact.safe_projection(authenticated_owner_scope=OWNER)


@pytest.mark.parametrize('ensure,mode', [(False,'development'), (True,'read_only'), (True,'off')])
def test_read_only_routes_never_acquire_a_response(monkeypatch, ensure, mode):
    source = AsyncMock(side_effect=AssertionError('read generated'))
    monkeypatch.setattr(service, 'read_maps', AsyncMock(return_value={'items':[]}))
    monkeypatch.setattr(service, '_rpc', AsyncMock(side_effect=AssertionError('read wrote')))
    monkeypatch.setattr(service, 'observed_mode', lambda:mode)
    assert not run(service.ensure_map(OWNER, ensure=ensure, model_source=source))['has_visible_content']
    source.assert_not_awaited()


@pytest.fixture
def sql_source(monkeypatch):
    if not os.environ.get('Q2_PGLITE_MODULE'):
        pytest.skip('PostgreSQL WASM dependency is not configured')
    from test_emlis_q3_application import Q3Database
    db = Q3Database()
    try:
        db.migrate()
        for name in ('20261003134440_analysis_observed_artifacts.sql', '20261004041627_analysis_period_comparison.sql',
                     '20261101080144_cumulative_watashi_map.sql'):
            db.proc.stdin.write(json.dumps({'script':True, 'sql':(Path(__file__).parents[2]/'supabase/migrations'/name).read_text()})+'\n')
            db.proc.stdin.flush()
            assert 'code' not in json.loads(db.proc.stdout.readline())
        async def rpc(name, payload):
            args = ','.join(f'{key} => ${i}' for i,key in enumerate(payload,1))
            params = [json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for v in payload.values()]
            result = await asyncio.to_thread(db.query, f'select public.{name}({args}) as value', params, 'service_role')
            if 'code' in result: raise HTTPException(409, result['code'])
            return result['rows'][0]['value']
        monkeypatch.setattr(service, '_rpc', rpc)
        monkeypatch.setattr(service, 'observed_mode', lambda:'development')
        yield db, rpc
    finally:
        db.proc.stdin.close()
        db.proc.wait(timeout=10)


def insert_material(db, mode):
    original = material('role' if mode == 'combined' else mode)['members'][0]['original']
    if mode == 'combined': original['memo'] += '僕は費用を記録した。'
    assert 'code' not in db.query('insert into auth.users values ($1)', [OWNER])
    assert 'code' not in db.query("insert into public.profiles values ($1,'free')", [OWNER])
    assert 'code' not in db.query('insert into public.emotions values ($1,$2,$3,$4,$5,$6,$7,$8)',
        [original['id'], OWNER, original['created_at'], original['memo'], original['memo_action'],
         original['category'], original['emotions'], json.dumps(original['emotion_details'])])
    return original


@pytest.mark.parametrize('mode', ['role', 'pair', 'clause', 'combined'])
def test_real_sql_fresh_source_normal_commit_and_immutable_month(sql_source, monkeypatch, mode):
    db, rpc = sql_source
    original = insert_material(db, mode)
    earlier = run(rpc('analysis_cumulative_source_snapshot', {'p_user_id':OWNER}))
    stale = service.prepare_cumulative_category_units(OWNER, earlier, prompt_version='selected_material.v4')
    received = []
    async def source(prepared):
        assert prepared.response is None and prepared.prompt_version == 'selected_material.v4'
        assert prepared.source_guard == earlier['guard']
        assert prepared.request_ref != stale.request_ref
        received.append(prepared)
        return synthetic_response(prepared)
    first = run(service.ensure_map(OWNER, model_source=source))
    assert first['has_visible_content'] and first['refreshed'] and len(received) == 1
    assert '受付係' in first['content_text'] and '記録された役割' in first['content_text']
    assert len(first['meta']['nodes']) == (2 if mode in {'pair', 'combined'} else 1)
    assert first['map_context']['unparsed_count'] == int(mode == 'clause')
    if mode == 'clause': assert '費用を記録' not in first['content_text']
    raw = db.query('select private_evidence from public.analysis_observed_artifacts where id=$1', [first['report_id']])['rows'][0]['private_evidence']
    assert raw['source_record_refs'] == [original['id']]
    assert raw['coverage'] == first['map_context']
    assert 'raw_sha256' not in json.dumps(raw)
    # Actual read validators and SQL run; only generation and source are forbidden.
    forbidden = AsyncMock(side_effect=AssertionError('saved read acquired a response'))
    with patch.object(service, 'build_cumulative_map', side_effect=AssertionError('saved read generated')):
        current = run(service.ensure_map(OWNER, model_source=forbidden))
        monthly = run(service.ensure_map(OWNER, monthly=True, force=True, model_source=forbidden))
        readonly = run(service.ensure_map(OWNER, ensure=False, force=True, model_source=forbidden))
        detail = run(service.read_maps(OWNER, report_id=first['report_id']))['items'][0]
    forbidden.assert_not_awaited()
    for value in (current,monthly,readonly):
        assert value['meta'] == first['meta'] and value['content_text'] == first['content_text']
        assert value['report_id'] == first['report_id'] and not value['refreshed']
    assert detail['content_json']['watashiMap'] == first['meta']
    evidence = run(service.map_evidence(OWNER, first['report_id'], first['meta']['nodes'][0]['node_ref'], month=monthly['snapshot_month']))
    assert evidence['items'] and all(x['version_state'] == 'CURRENT' for x in evidence['items'])
    # A later valid rebuild updates current, but never rewrites this month's capture.
    db.query("update public.emotions set memo=replace(memo,'だった','ではなかった') where id=$1", [original['id']])
    async def updated(prepared): return synthetic_response(prepared)
    second = run(service.ensure_map(OWNER, force=True, model_source=updated))
    assert second['refreshed'] and second['report_id'] != first['report_id']
    assert second['content_text'] != first['content_text']
    history = run(service.ensure_map(OWNER, monthly=True, force=True, model_source=forbidden))
    assert history['meta'] == monthly['meta'] and history['content_text'] == monthly['content_text']
    assert history['captured_at'] == monthly['captured_at']
    forbidden.assert_not_awaited()


def test_real_sql_source_edit_during_response_rejects_commit(sql_source):
    db, _ = sql_source
    original = insert_material(db, 'pair')
    calls = []
    async def source(prepared):
        response = synthetic_response(prepared)
        calls.append(prepared.request_ref)
        db.query("update public.emotions set memo=memo || '変更。' where id=$1", [original['id']])
        return response
    with pytest.raises(HTTPException) as error:
        run(service.ensure_map(OWNER, model_source=source))
    assert error.value.status_code == 409 and error.value.detail == '40001'
    assert len(calls) == 1
    assert db.query('select count(*) as n from public.analysis_observed_artifacts')['rows'][0]['n'] == 0
    assert db.query('select count(*) as n from public.analysis_cumulative_months')['rows'][0]['n'] == 0


def insert_additional_original(db, template, number, memo, category):
    original = dict(template, id=str(UUID(int=number)), memo=memo, memo_action='', category=[category])
    assert 'code' not in db.query('insert into public.emotions values ($1,$2,$3,$4,$5,$6,$7,$8)',
        [original['id'], OWNER, original['created_at'], original['memo'], original['memo_action'],
         original['category'], original['emotions'], json.dumps(original['emotion_details'])])
    return original


def test_real_sql_full_snapshot_single_acquisition_saved_reads_force_refresh_and_monthly_immutability(sql_source):
    db, rpc = sql_source
    original = insert_material(db, 'role')
    action = insert_additional_original(db, original, 5002, '僕は費用を記録した。', '生活')
    unknown = insert_additional_original(db, original, 5003, 'まだ言葉にできません。', '仕事')
    calls = []
    async def source(prepared):
        calls.append(prepared.request_ref)
        assert len(prepared.request.members) == 3
        assert len(json.loads(prepared.messages()[1]['content'])['fields']) == 3
        return synthetic_response(prepared)
    first = run(service.ensure_map(OWNER, model_source=source))
    assert first['refreshed'] and len(calls) == 1
    assert first['map_context']['source_count'] == first['map_context']['processed_count'] == 3
    assert first['map_context']['mapped_count'] == 2 and first['map_context']['unparsed_count'] == 1
    private = db.query('select private_evidence from public.analysis_observed_artifacts where id=$1',
        [first['report_id']])['rows'][0]['private_evidence']
    assert set(private['source_record_refs']) == {original['id'], action['id'], unknown['id']}
    assert private['coverage'] == first['map_context'] and len(private['source_members']) == 3
    forbidden = AsyncMock(side_effect=AssertionError('saved multi-record read acquired a response'))
    with patch.object(service, 'build_cumulative_map', side_effect=AssertionError('saved multi-record generation')):
        current = run(service.ensure_map(OWNER, model_source=forbidden))
        month = run(service.ensure_map(OWNER, monthly=True, force=True, model_source=forbidden))
        readonly = run(service.ensure_map(OWNER, ensure=False, force=True, model_source=forbidden))
        detail = run(service.read_maps(OWNER, report_id=first['report_id']))['items'][0]
    for saved in (current, month, readonly):
        assert saved['report_id'] == first['report_id'] and saved['meta'] == first['meta']
        assert saved['content_text'] == first['content_text'] and not saved['refreshed']
    assert detail['content_json']['map_context'] == first['map_context']
    forbidden.assert_not_awaited()
    assert 'code' not in db.query('update public.emotions set memo=$2 where id=$1',
        [action['id'], '僕は費用を記録しなかった。'])
    second = run(service.ensure_map(OWNER, force=True, model_source=source))
    assert second['refreshed'] and second['report_id'] != first['report_id'] and len(calls) == 2
    assert calls[0] != calls[1] and second['content_text'] != first['content_text']
    with patch.object(service, 'build_cumulative_map', side_effect=AssertionError('saved multi-record refresh generation')):
        history = run(service.ensure_map(OWNER, monthly=True, force=True, model_source=forbidden))
        current = run(service.ensure_map(OWNER, ensure=False, model_source=forbidden))
    assert history['report_id'] == first['report_id'] and history['meta'] == month['meta']
    assert history['captured_at'] == month['captured_at'] and history['content_text'] == month['content_text']
    assert current['meta'] == second['meta'] and current['content_text'] == second['content_text']
    forbidden.assert_not_awaited()


def test_real_sql_nonfirst_record_change_during_multi_response_rejects_whole_commit(sql_source):
    db, _ = sql_source
    original = insert_material(db, 'role')
    action = insert_additional_original(db, original, 5002, '僕は費用を記録した。', '生活')
    calls = []
    async def source(prepared):
        assert len(prepared.request.members) == 2
        response = synthetic_response(prepared)
        calls.append(prepared.request_ref)
        assert 'code' not in db.query('update public.emotions set memo=$2 where id=$1',
            [action['id'], '僕は費用を記録しなかった。'])
        return response
    with pytest.raises(HTTPException) as error:
        run(service.ensure_map(OWNER, model_source=source))
    assert error.value.status_code == 409 and error.value.detail == '40001' and len(calls) == 1
    assert db.query('select count(*) as n from public.analysis_observed_artifacts')['rows'][0]['n'] == 0
    assert db.query('select count(*) as n from public.analysis_cumulative_months')['rows'][0]['n'] == 0


def test_real_sql_natural_role_decision_preserves_order_negative_refresh_and_month(sql_source):
    from test_analysis_model_role_decision import sample, response_for
    db, _ = sql_source
    original = insert_material(db, 'role')
    positive = sample()['members'][0]['original']
    assert 'code' not in db.query('update public.emotions set memo=$2,memo_action=$3,category=$4 where id=$1',
        [original['id'], positive['memo'], positive['memo_action'], ['生活']])
    calls = []
    async def source(prepared):
        calls.append(prepared.request_ref)
        return response_for(prepared, qualifiers=True, reorder=True)
    first = run(service.ensure_map(OWNER, model_source=source))
    assert first['has_visible_content'] and first['refreshed'] and len(calls) == 1
    assert [n['node_kind'] for n in first['meta']['nodes']] == ['ROLE', 'ACTION_OR_NONACTION']
    role, decision = first['meta']['nodes']
    edge, = first['meta']['edges']
    assert edge['edge_kind'] == 'OBSERVED_ORDER'
    assert (edge['from_ref'], edge['to_ref']) == (role['node_ref'], decision['node_ref'])
    assert '会合の進行' in role['visible_label'] and '記録された担当' in role['visible_label']
    assert '分担を決める' in decision['visible_label'] and '実行済み' in decision['visible_label']
    assert '原因を示す線ではありません' in first['content_text']
    assert first['map_context']['source_count'] == first['map_context']['processed_count'] == first['map_context']['mapped_count'] == 1
    assert first['map_context']['unparsed_count'] == 0
    forbidden = AsyncMock(side_effect=AssertionError('saved natural role/decision acquired a response'))
    with patch.object(service, 'build_cumulative_map', side_effect=AssertionError('saved natural role/decision generated')):
        current = run(service.ensure_map(OWNER, model_source=forbidden))
        monthly = run(service.ensure_map(OWNER, monthly=True, force=True, model_source=forbidden))
        readonly = run(service.ensure_map(OWNER, ensure=False, model_source=forbidden))
        detail = run(service.read_maps(OWNER, report_id=first['report_id']))['items'][0]
    forbidden.assert_not_awaited()
    for saved in (current, monthly, readonly):
        assert not saved['refreshed'] and saved['report_id'] == first['report_id']
        assert saved['meta'] == first['meta'] and saved['content_text'] == first['content_text']
    assert detail['content_json']['watashiMap'] == first['meta']
    negative = sample(True, True)['members'][0]['original']
    assert 'code' not in db.query('update public.emotions set memo=$2 where id=$1',
        [original['id'], negative['memo']])
    second = run(service.ensure_map(OWNER, force=True, model_source=source))
    assert second['refreshed'] and second['report_id'] != first['report_id'] and len(calls) == 2
    assert calls[0] != calls[1]
    assert [n['node_kind'] for n in second['meta']['nodes']] == ['ROLE', 'ACTION_OR_NONACTION']
    assert '担当しなかった' in second['meta']['nodes'][0]['visible_label']
    assert '行わなかった' in second['meta']['nodes'][1]['visible_label']
    assert second['meta']['edges'] == first['meta']['edges'] and second['map_context']['unparsed_count'] == 0
    with patch.object(service, 'build_cumulative_map', side_effect=AssertionError('saved natural role/decision generated')):
        history = run(service.ensure_map(OWNER, monthly=True, force=True, model_source=forbidden))
        current = run(service.ensure_map(OWNER, ensure=False, model_source=forbidden))
    forbidden.assert_not_awaited()
    assert history['report_id'] == first['report_id'] and history['captured_at'] == monthly['captured_at']
    assert history['meta'] == first['meta'] and history['content_text'] == first['content_text']
    assert current['meta'] == second['meta'] and current['content_text'] == second['content_text']


def test_real_sql_saved_supplement_does_not_acquire_a_response(sql_source, monkeypatch):
    db, _ = sql_source
    original = insert_material(db, 'pair')
    import emlis_thread_store
    from emlis_thread_service import EmlisThreadService, Q3_PROFILE
    from test_emlis_q3_application import answer
    monkeypatch.setattr(emlis_thread_store, 'sb_post_rpc', db.rpc)
    db.query("update public.emotions set memo=$2,memo_action='',created_at=(now()-interval '1 day') at time zone 'UTC',emotions=array['不安'],emotion_details=$3 where id=$1",
        [original['id'], '褒められたのに、嬉しくなかった。', json.dumps([dict(type='不安',strength='medium')])])
    emlis = EmlisThreadService(runtime_profile=Q3_PROFILE)
    dto = run(emlis.start(OWNER, original['id']))
    assert dto.get('pending_question') is not None
    run(answer(emlis, OWNER, dto, 'その時は重かった。', 'analysis-supplement'))
    source = AsyncMock(side_effect=AssertionError('supplement response acquired'))
    with pytest.raises(HTTPException) as error:
        run(service.ensure_map(OWNER, model_source=source))
    assert error.value.status_code == 422
    source.assert_not_awaited()


def insert_bound_answer(db, rpc):
    """Use the existing saved-answer envelope shape in the real SQL snapshot."""
    original = insert_material(db, 'role')
    assert 'code' not in db.query('update public.emotions set emotion_details=$2 where id=$1',
        [original['id'], json.dumps([dict(type='平穏', strength='medium')])])
    snapshot = run(rpc('analysis_cumulative_source_snapshot', {'p_user_id': OWNER}))
    member = with_answer(snapshot['members'][0], '僕は費用を記録した。')
    thread = member['thread']
    assert 'code' not in db.query('''insert into public.emlis_input_threads
        (id,user_id,original_emotion_id,revision,state,issued_count,source_snapshot,data)
        values ($1,$2,$3,$4,'COMPLETED',$5,$6,$7)''',
        [thread['id'], OWNER, original['id'], thread['revision'], thread['issued_count'],
         json.dumps(thread['source_snapshot']), json.dumps(thread['data'])])
    for seq, event in enumerate(member['events'][:2], 1):
        assert 'code' not in db.query('''insert into public.emlis_thread_events
            (id,thread_id,seq,kind,round_index,question_id,payload) values ($1,$2,$3,$4,$5,$6,$7)''',
            [event['id'], thread['id'], seq, event['kind'], event['round_index'],
             event['question_id'], json.dumps(event['payload'])])
    return original, member['events'][1]['id']


def replace_bound_answer(db, answer_id, text):
    assert 'code' not in db.query('''update public.emlis_thread_events set
        payload=jsonb_set(payload,'{source,answer_text_private}',to_jsonb($2::text)) where id=$1''',
        [answer_id, text])


def test_real_sql_ordinary_answer_normal_save_readonly_fresh_answer_and_immutable_month(sql_source):
    db, rpc = sql_source
    original, answer_id = insert_bound_answer(db, rpc)
    calls = []
    async def source(prepared):
        calls.append(prepared)
        fields = json.loads(prepared.messages()[1]['content'])['fields']
        assert [f['source_role'] for f in fields] == ['ORIGINAL_INPUT', 'SUPPLEMENTAL_ANSWER']
        return synthetic_response(prepared)
    first = run(service.ensure_map(OWNER, model_source=source))
    assert first['refreshed'] and len(calls) == 1 and len(first['meta']['nodes']) == 2
    assert first['map_context']['source_count'] == first['map_context']['mapped_count'] == 1
    assert first['map_context']['unparsed_count'] == 0 and not first['meta']['edges']
    private = db.query('select private_evidence from public.analysis_observed_artifacts where id=$1',
        [first['report_id']])['rows'][0]['private_evidence']
    assert private['source_record_refs'] == [original['id']]
    assert len({e['source_envelope_id'] for n in private['graph']['nodes'] for e in n['evidence_refs']}) == 2
    forbidden = AsyncMock(side_effect=AssertionError('saved answer read generated'))
    with patch.object(service, 'build_cumulative_map', side_effect=AssertionError('saved answer build')):
        current = run(service.ensure_map(OWNER, model_source=forbidden))
        month = run(service.ensure_map(OWNER, monthly=True, force=True, model_source=forbidden))
        readonly = run(service.ensure_map(OWNER, ensure=False, force=True, model_source=forbidden))
    for saved in (current, month, readonly):
        assert saved['report_id'] == first['report_id'] and saved['meta'] == first['meta']
        assert saved['content_text'] == first['content_text'] and not saved['refreshed']
    replace_bound_answer(db, answer_id, '僕は費用を記録しなかった。')
    stale = AsyncMock(return_value=synthetic_response(calls[0]))
    with pytest.raises(HTTPException) as error:
        run(service.ensure_map(OWNER, force=True, model_source=stale))
    assert error.value.status_code == 422
    second = run(service.ensure_map(OWNER, force=True, model_source=source))
    assert second['refreshed'] and len(calls) == 2 and second['report_id'] != first['report_id']
    assert calls[1].source_guard != calls[0].source_guard and calls[1].request_ref != calls[0].request_ref
    assert '行わなかった' in second['content_text'] and second['map_context']['source_count'] == 1
    with patch.object(service, 'build_cumulative_map', side_effect=AssertionError('saved answer refresh build')):
        history = run(service.ensure_map(OWNER, monthly=True, force=True, model_source=forbidden))
    assert history['report_id'] == month['report_id'] and history['meta'] == month['meta']
    assert history['captured_at'] == month['captured_at'] and history['content_text'] == month['content_text']
    forbidden.assert_not_awaited()


def test_real_sql_answer_edit_during_response_rejects_whole_commit(sql_source):
    db, rpc = sql_source
    _, answer_id = insert_bound_answer(db, rpc)
    calls = []
    async def source(prepared):
        calls.append(prepared.request_ref)
        response = synthetic_response(prepared)
        replace_bound_answer(db, answer_id, '僕は費用を記録しなかった。')
        return response
    with pytest.raises(HTTPException) as error:
        run(service.ensure_map(OWNER, model_source=source))
    assert error.value.status_code == 409 and error.value.detail == '40001' and len(calls) == 1
    assert db.query('select count(*) as n from public.analysis_observed_artifacts')['rows'][0]['n'] == 0
    assert db.query('select count(*) as n from public.analysis_cumulative_months')['rows'][0]['n'] == 0
