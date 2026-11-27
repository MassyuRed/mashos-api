"""Exact receipt admission, persistence and plan reads for actual structure relations."""

import asyncio
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from uuid import UUID

from fastapi import HTTPException
import pytest

import analysis_cumulative_service as service
from analysis_plan_source_choices import WholeMapTitle
import analysis_semantic_map as maps
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from report_artifact_read_service import get_detail
from test_analysis_cumulative import OWNER, source_snapshot
from test_analysis_cumulative_model_source import sql_source
from test_analysis_interpretation_correction_sources import sql_script
from test_analysis_node_local_v4_phases import response
from test_analysis_occurrence_v17_record_owners import packet
from test_analysis_v13_separate_record_titles import wire


COEXISTENCE = ('私は、提出期限と手伝いの時間を両立できると判断して、資料確認を選び、'
               '実際に提出期限と手伝いの時間を両立できました。')
PRIORITY = ('私は、手伝いの時間より提出期限を優先して、取引先への連絡を断る方法を選び、'
            '実際に手伝いの時間を確保できませんでした。')
REVERSE = '私は、提出期限より手伝いの時間を優先して、取引先への連絡を選びました。'
UNRELATED = '提出期限を確認し、手伝いの時間に伝票を見ました。'
ADDED_RESULT = '資料の確認が期限内に終わりました。'
NOTES = ('提出期限に余裕があったので、私は資料の確認を引き受けた。',
         '提出期限に間に合わないので、私は取引先への連絡を断った。',
         '手伝いの時間が取れたので、私は見積もりを引き受けた。',
         '手伝いの時間が取れなかったので、私は会議への同席を断った。')


def _snapshot(action):
    snapshot = source_snapshot(5)
    for member, note in zip(snapshot['members'], (*NOTES, ''), strict=True):
        member['original'].update(memo=note, memo_action='' if note else action)
    return snapshot


def _artifact(action, snapshot=None, *, authored_axes=True, recover_witnessed_structures=False):
    snapshot = _snapshot(action) if snapshot is None else snapshot
    prepared = maps.prepare_semantic_map(OWNER, snapshot,
        prompt_version=core.SEMANTIC_MAP_OCCURRENCE_V24_PROFILE, primary_structures='karen.v3',
        recover_witnessed_structures=recover_witnessed_structures)
    material = json.loads(prepared.material_json)
    by_text = {field['text']: field['field'] for field in material['fields']}
    plan = dict(schema_version=core._semantic_v4_schema('PLAN'), nodes=[])
    bodies = dict(schema_version=core._semantic_v4_schema('NODES'), nodes={})
    by_root = []
    for i, member in enumerate(snapshot['members'], 1):
        original = member['original']
        quote = original['memo'] or original['memo_action']
        node_id = f'n{i}'
        row = [(by_text[quote], quote)]
        by_root.append([row])
        evidence = [dict(field=field, quote=text) for field, text in row]
        plan['nodes'].append(dict(node_id=node_id, units=[dict(evidence=evidence)]))
        unit = dict(evidence_ref=node_id + '.u1', source_mode='RECORDED', unknowns=[],
                    fact_parts={core._semantic_fact_part_key(evidence, 0): quote})
        meaning = ADDED_RESULT if i == 1 and not authored_axes else ''
        bodies['nodes'][node_id] = dict(units={'u1': unit}, node_kind='CHOICE_OUTPUT',
                                        perspective='SELF', title=quote, meaning=meaning)
    bodies['plan_sha256'] = core.semantic_map_hash(plan)
    nodes = core._semantic_v4_join(plan, bodies)
    axes = [dict(scope='across_records', anchors=['n1.u1.e1', 'n2.u1.e1'], heading='提出との兼ね合い',
                 decision_factor='提出期限', criterion='手伝いを引き受ける際は、提出期限を守れるかを考えています。',
                 case_reading='「提出期限に余裕があった」ときは資料の確認を引き受けました。'
                              '「提出期限に間に合わない」ときは取引先への連絡を断りました。'),
            dict(scope='across_records', anchors=['n3.u1.e1', 'n4.u1.e1'], heading='手を貸せる時間',
                 decision_factor='手伝いの時間', criterion='引き受けるかは、手伝いの時間を取れるかで決めています。',
                 case_reading='「手伝いの時間が取れた」ときは見積もりを引き受けました。'
                              '「手伝いの時間が取れなかった」ときは会議への同席を断りました。')]
    relations = dict(schema_version=core._semantic_v4_schema('RELATIONS'), nodes_sha256=core.semantic_map_hash(nodes),
        qualification_review={}, edges=[], primary_structures=axes if authored_axes else [],
        overview=dict(title=WholeMapTitle(material, nodes).neutral, title_proposal='',
                      node_refs=[node['node_id'] for node in nodes]))
    receipts = []
    phases = (packet(prepared, by_root), wire(prepared, plan, bodies), relations)
    for phase, value in zip(core.SEMANTIC_MAP_NODE_LOCAL_V4_PHASES, phases, strict=True):
        messages = core.semantic_node_local_v4_messages(prepared, phase,
            plan=plan if phase != 'PLAN' else None, nodes=bodies if phase == 'RELATIONS' else None)
        raw = json.dumps(value, ensure_ascii=False, separators=(',', ':'))
        receipts.append(dict(phase=phase, messages_sha256=core.semantic_map_hash(messages), raw=raw,
            raw_sha256=hashlib.sha256(raw.encode()).hexdigest(), finish_reason='stop', completion_tokens=100))
    receipt = dict(schema_version=core.semantic_node_local_v4_artifact_schema(prepared), phases=receipts)
    artifact, coverage = maps.build_semantic_map(prepared, response(prepared, receipt))
    return artifact, coverage, snapshot


@pytest.mark.parametrize('action, kind, preferred, other, outcome', [
    (COEXISTENCE, 'COEXISTENCE', 0, 1, '提出期限と手伝いの時間を両立できました'),
    (PRIORITY, 'PRIORITY', 0, 1, '手伝いの時間を確保できませんでした'),
    (REVERSE, 'PRIORITY', 1, 0, None),
    (UNRELATED, None, None, None, None),
])
def test_private_review_uses_both_admitted_axes_and_exact_actual_choice(action, kind, preferred, other, outcome):
    artifact, _, snapshot = _artifact(action)
    graph = artifact.safe_projection(authenticated_owner_scope=OWNER)
    assert len(graph['overview']['primary_structures']) == 2
    assert 'structure_relations' not in graph['overview']
    assert action not in graph['overview']['primary_structures'][0]['description']
    private = artifact.private_evidence()
    review = private['graph']['meaning_review'].get('structure_relations')
    if kind is None:
        assert review is None
        return
    assert review['views'] == [dict(kind=kind, first_index=preferred, second_index=other, description=action)]
    witness, = review['witnesses']
    original = snapshot['members'][-1]['original']
    for key in ('settlement', 'first_factor', 'second_factor', 'selected_option'):
        span = witness[key]
        assert span['record_ref'] == original['id'] and span['field'] == 'memo_action'
        assert action[span['start']:span['end']] == span['quote']
    assert (witness['confirmed_outcome'] or {}).get('quote') == outcome
    assert len({witness[key]['record_ref'] for key in ('settlement', 'first_grounding', 'second_grounding')}) == 3


@pytest.mark.parametrize('action, expected', [
    (COEXISTENCE, ('COEXISTENCE', 0, 1)),
    (PRIORITY, ('PRIORITY', 0, 1)),
    (REVERSE, ('PRIORITY', 1, 0)),
    (UNRELATED, None),
])
def test_missing_authored_axes_can_use_two_distinct_complete_choice_comparisons(action, expected):
    gated, _, _ = _artifact(action, authored_axes=False)
    assert gated.safe_projection(authenticated_owner_scope=OWNER)['overview']['primary_structures'] == []
    artifact, _, _ = _artifact(action, authored_axes=False, recover_witnessed_structures=True)
    graph = artifact.safe_projection(authenticated_owner_scope=OWNER)
    axes = graph['overview']['primary_structures']
    review = artifact.private_evidence()['graph']['meaning_review']
    roots = review.get('original_choice_contrast_roots')
    relation = review.get('structure_relations')
    if expected is None:
        assert axes == graph['edges'] == []
        assert roots is relation is None
        return
    assert roots == [['n1.u1.e1', 'n2.u1.e1'], ['n3.u1.e1', 'n4.u1.e1']]
    assert [axis['title'] for axis in axes] == ['提出期限', '手伝いの時間']
    assert [axis['node_refs'] for axis in axes] == [['n1', 'n2'], ['n3', 'n4']]
    assert NOTES[0] in graph['nodes'][0]['explanation']
    assert ADDED_RESULT not in graph['nodes'][0]['explanation']
    raw_nodes = json.loads(review['node_local_plan']['phase_artifact']['phases'][1]['raw'])
    assert raw_nodes['nodes']['n1']['meaning'] == ADDED_RESULT
    assert '提出期限に間に合わないので、取引先への連絡を断りました。' in axes[0]['description']
    assert '手伝いの時間が取れなかったので、会議への同席を断りました。' in axes[1]['description']
    assert all(action not in axis['description'] for axis in axes)
    assert [(edge['from_ref'], edge['to_ref']) for edge in graph['edges']] == [('n1', 'n2'), ('n3', 'n4')]
    assert '提出期限に間に合わない → 私は取引先への連絡を断った' in graph['edges'][0]['label']
    kind, first, second = expected
    assert relation['views'] == [dict(kind=kind, first_index=first, second_index=second, description=action)]
    assert (relation['witnesses'][0]['confirmed_outcome'] is None) is (action == REVERSE)


def test_explicit_settlement_without_independent_acceptance_and_refusal_is_not_enough():
    snapshot = _snapshot(PRIORITY)
    snapshot['members'][3]['original']['memo'] = '手伝いの時間が取れなかったので、私は会議への同席を引き受けた。'
    artifact, _, _ = _artifact(PRIORITY, snapshot, authored_axes=False, recover_witnessed_structures=True)
    graph = artifact.safe_projection(authenticated_owner_scope=OWNER)
    assert graph['overview']['primary_structures'] == graph['edges'] == []
    assert 'structure_relations' not in artifact.private_evidence()['graph']['meaning_review']


def test_source_comparison_keeps_the_written_negative_and_retains_qualification_checks():
    exact = '印刷費の節約にならないので、私は冊子の増刷を断った。'
    confirmed = dict(field=1, text=exact)
    assert core._bound_choice(confirmed, exact, {1: (exact,)}) is None
    admitted = core._bound_choice(confirmed, exact, {1: (exact,)}, allow_written_negative=True)
    assert admitted[:2] == ('印刷費の節約にならない', '私は冊子の増刷を断った')
    for text in ('もし' + exact, exact + 'これは仮定です。'):
        qualified = dict(field=1, text=text)
        assert core._bound_choice(qualified, text, {1: (text,)}, allow_written_negative=True) is None
        assert core._bound_choice(qualified, exact, {1: (exact,)}, allow_written_negative=True) is None


def test_saved_premium_relation_is_not_reflected_in_lower_plans_or_legacy_renderers(monkeypatch):
    monkeypatch.setenv('COCOLON_ANALYSIS_PRIMARY_STRUCTURE_READING', 'karen.v3')
    artifact, coverage, _ = _artifact(COEXISTENCE)
    rid = str(UUID(artifact.artifact_id[9:]))
    graph = artifact.safe_projection(authenticated_owner_scope=OWNER)
    private = artifact.private_evidence()
    relation, = private['graph']['meaning_review']['structure_relations']['views']
    row = dict(id=rid, report_type='latest', report_mode='standard', source_profile='cumulative.v1',
               title='わたしマップ', period_start='2025-01-01', period_end='2026-11-01', generated_at='2026-11-01',
               snapshot_month=None, captured_at=None, content_text=service._projection_text(graph),
               content_json=dict(watashiMap=graph, report_mode='standard', map_context=coverage))
    month = datetime.now(timezone(timedelta(hours=9))).date().replace(day=1).isoformat()
    tier = 'premium'
    corrupt = None

    async def rpc(name, params):
        assert name == 'analysis_cumulative_read' and params['p_user_id'] == OWNER
        item = deepcopy(row)
        if params['p_history'] or params['p_month']:
            item.update(report_type='monthly', snapshot_month=month)
        if tier == 'premium' or corrupt == 'down-tier':
            item['content_json']['structure_relations'] = [dict(relation)]
            if corrupt == 'extra-private-field':
                item['content_json']['structure_relations'][0]['record_ref'] = 'private-source-ref'
        return dict(items=[item], subscription_tier=tier, matched=True,
                    history_limit={'free': 2, 'plus': 12, 'premium': None}[tier])

    monkeypatch.setattr(service, '_rpc', rpc)
    monkeypatch.setattr('analysis_observed_service.observed_enabled', lambda: True)

    def latest(capability='v1', monthly=False, renderer='semantic.v3'):
        payload = asyncio.run(service.ensure_map(OWNER, ensure=False, monthly=monthly))
        return service.map_response_for_renderer(payload, renderer, capability)

    def detail(capability='v1', renderer='semantic.v3'):
        payload = asyncio.run(get_detail(user_id=OWNER, family='self_structure', report_id=rid, month=month))
        return service.map_response_for_renderer(payload, renderer, capability)['item']

    paid = latest()
    assert paid['report_id'] == latest(monthly=True)['report_id'] == detail()['id'] == rid
    assert paid['meta'] == latest(monthly=True)['meta'] == detail()['content_json']['watashiMap']
    assert paid['meta']['overview']['structure_relations'] == [relation]
    assert paid['content_text'].endswith(COEXISTENCE) and detail()['content_text'] == paid['content_text']
    assert paid['meta']['overview']['summary'] == paid['content_text']
    assert paid['meta']['overview']['summary'].count(COEXISTENCE) == 1
    assert 'structure_relations' not in detail()['content_json']
    assert 'structure_relations' not in latest(None)['meta']['overview']
    assert COEXISTENCE not in latest(None)['content_text'] and COEXISTENCE not in latest(renderer=None)['content_text']
    assert COEXISTENCE not in detail(None)['content_text']

    corrupt = 'extra-private-field'
    assert latest() == latest(None)
    corrupt = None
    for tier in ('plus', 'free'):
        assert latest()['report_id'] == rid
        assert 'structure_relations' not in json.dumps(latest(monthly=True))
        assert COEXISTENCE not in detail()['content_text']
    corrupt = 'down-tier'
    with pytest.raises(HTTPException, match='analysis_saved_artifact_invalid'):
        latest()

    corrupt = None
    tier = 'premium'
    monkeypatch.setenv('COCOLON_ANALYSIS_PLAN_READ_ROLLOUT', 'free_plus.v1')
    basic_premium = latest()
    assert basic_premium['report_id'] == rid
    assert 'structure_relations' not in json.dumps(basic_premium)
    assert basic_premium['meta']['overview']['primary_structures'] == paid['meta']['overview']['primary_structures']
    assert COEXISTENCE not in detail()['content_text']
    tier = 'plus'
    assert basic_premium['meta'] == latest()['meta']

    monkeypatch.setenv('COCOLON_ANALYSIS_PREMIUM_RELATION_ROLLOUT', 'grounded.v1')
    assert latest()['meta'] == basic_premium['meta']
    tier = 'premium'
    assert latest()['meta'] == latest(monthly=True)['meta'] == detail()['content_json']['watashiMap'] == paid['meta']
    assert latest()['content_text'] == detail()['content_text'] == paid['content_text']
    assert latest(None) == basic_premium
    assert basic_premium['meta']['overview']['summary'] == basic_premium['content_text']
    for renderer in ('semantic.v1', 'semantic.v2'):
        older = latest(None, renderer=renderer)
        assert older['content_text'] == latest(None, monthly=True, renderer=renderer)['content_text'] == paid['content_text']
        assert older['meta']['overview'] == dict(title=paid['meta']['overview']['title'], summary=paid['content_text'])
        assert older['meta'] == detail(None, renderer)['content_json']['watashiMap']
        tier = 'plus'
        assert COEXISTENCE not in latest(None, renderer=renderer)['content_text']
        tier = 'premium'
    monkeypatch.delenv('COCOLON_ANALYSIS_PRIMARY_STRUCTURE_READING')
    monkeypatch.delenv('COCOLON_ANALYSIS_PLAN_READ_ROLLOUT')
    assert latest() == basic_premium
    assert COEXISTENCE not in latest(None, renderer='semantic.v1')['content_text']


@pytest.fixture
def saved_map_source(sql_source):
    db, rpc = sql_source
    for migration in (
        '20261107071033_analysis_semantic_map_wire.sql',
        '20261114032520_analysis_interpretation_correction_sources.sql',
        '20261114120000_analysis_if_route_artifacts.sql',
        '20261114123000_analysis_emlis_material_handoff.sql',
        '20261114132000_analysis_map_interpretation_corrections.sql',
        '20261114133000_analysis_map_correction_handoff.sql',
        '20261121132000_deep_insight_questions.sql',
        '20261121133000_analysis_deep_insight_answer_handoff.sql',
        '20261121134000_deep_insight_grounded_questions.sql',
        '20261122145000_deep_insight_effective_emlis_corrections.sql',
        '20261125184500_analysis_scoped_map_correction.sql',
        '20261125191500_analysis_plan_independent_map_identity.sql',
    ):
        sql_script(db, migration)
    other = str(UUID(int=2))
    for owner in (OWNER, other):
        assert 'code' not in db.query('insert into auth.users values ($1)', [owner])
        assert 'code' not in db.query("insert into public.profiles values ($1,'free')", [owner])
    originals = [item['original'] for item in _snapshot(COEXISTENCE)['members']]
    for source in originals:
        response_row = db.query('insert into public.emotions values ($1,$2,$3,$4,$5,$6,$7,$8)',
            [source['id'], OWNER, source['created_at'], source['memo'], source['memo_action'],
             source['category'], source['emotions'], json.dumps(source['emotion_details'])])
        assert 'code' not in response_row
    snapshot = asyncio.run(rpc('analysis_cumulative_source_snapshot', dict(p_user_id=OWNER)))
    return db, rpc, other, originals, snapshot


def test_rollout_keeps_valid_text_without_a_figure_and_does_not_replace_it_with_raw_records(saved_map_source, monkeypatch):
    import analysis_model_source as sources
    from unittest.mock import AsyncMock

    db, _, _, _, snapshot = saved_map_source
    first, coverage, _ = _artifact(COEXISTENCE, snapshot)
    second, _, _ = _artifact(COEXISTENCE, snapshot, authored_axes=False)
    proposed = first.safe_projection(authenticated_owner_scope=OWNER)
    assert service.map_projection_for_plan(proposed, 'free')[0]['nodes'] == []
    assert proposed['overview']['primary_structures']

    monkeypatch.setenv('COCOLON_ANALYSIS_PLAN_READ_ROLLOUT', 'free_plus.v1')
    acquired = AsyncMock(side_effect=((first, coverage), (second, coverage)))
    monkeypatch.setattr(service, '_semantic_history_map', acquired)
    notify = AsyncMock()
    monkeypatch.setattr(service, '_queue_map_update_notification', notify)
    source = sources.SelfHostedSemanticAnalysisModelSource(endpoint='https://synthetic.invalid/v1/chat/completions',
        model=sources.SEMANTIC_OCCURRENCE_V24_9B_MODEL, api_key='synthetic',
        semantic_prompt_version=core.SEMANTIC_MAP_OCCURRENCE_V24_PROFILE)
    initial = asyncio.run(service.ensure_map(OWNER, force=True, model_source=source))
    reread = asyncio.run(service.ensure_map(OWNER, force=True, model_source=source))
    assert initial['refreshed'] and not reread['refreshed']
    assert initial['report_id'] == reread['report_id']
    assert initial['meta'] == reread['meta']
    assert initial['meta']['nodes'] == []
    assert initial['meta']['overview']['primary_structures']
    assert reread['reason'] == service.NO_ACCEPTED_MAP_STRUCTURE
    assert reread['refresh_status'] == 'failed'
    assert service.map_response_for_renderer(reread, 'semantic.v1')['map_plan_scoped']
    assert all(axis['criterion'] in reread['content_text'] for axis in proposed['overview']['primary_structures'])
    assert db.query('select count(*)::integer as total from public.analysis_observed_artifacts')['rows'] == [{'total': 1}]
    assert db.query('select count(*)::integer as total from public.analysis_cumulative_months')['rows'] == [{'total': 1}]
    assert acquired.await_count == 2
    notify.assert_awaited_once()


@pytest.mark.parametrize('legacy', [False, True])
def test_saved_map_eligibility_is_shared_by_history_detail_if_deep_insight_and_push(saved_map_source, monkeypatch, legacy):
    import httpx
    from unittest.mock import AsyncMock
    import analysis_model_source as sources
    import astor_worker as worker

    db, rpc, other, originals, snapshot = saved_map_source
    artifact, coverage, _ = _artifact(COEXISTENCE, snapshot, authored_axes=False)
    graph = artifact.safe_projection(authenticated_owner_scope=OWNER)
    graph['overview'].pop('primary_structures')
    graph['overview']['summary'] = ('1月4日の記録：棚の寸法を測った。\n'
                                    '2月5日の記録：部品を探した。\n箱にしまった。') if not legacy else (
                                    '二つの場面で、続けられる条件を見比べています。')
    private = artifact.private_evidence()
    private.update(coverage=coverage, source_record_refs=[row['id'] for row in originals])
    if legacy:
        private['graph']['meaning_review']['node_local_plan']['plan']['overview'].pop('primary_structures')
    candidate = dict(p_user_id=OWNER, p_guard=snapshot['guard'], p_artifact_id=artifact.artifact_id,
                     p_private_evidence=private, p_projection=graph, p_text=service._projection_text(graph),
                     p_start=snapshot['period_start'], p_end=snapshot['period_end'])
    rid = asyncio.run(rpc('analysis_cumulative_commit', candidate))
    month = db.query('select snapshot_month::text as month from public.analysis_cumulative_months')['rows'][0]['month']
    sql_script(db, '20261125205000_analysis_premium_structure_relations.sql')
    sql_script(db, '20261127080000_analysis_withhold_unaccepted_map.sql')
    for function in (
        'analysis_cumulative_has_accepted_reading(jsonb,jsonb)',
        'analysis_cumulative_current_id(uuid,text)',
        'analysis_cumulative_commit(uuid,text,text,jsonb,jsonb,text,timestamptz,timestamptz,uuid,boolean)',
        'analysis_cumulative_read(uuid,uuid,boolean,integer,integer,date,boolean)',
        'analysis_if_base_context(uuid,text)',
    ):
        acl = db.query("select has_function_privilege('anon',$1,'execute') anon, "
            "has_function_privilege('authenticated',$1,'execute') authenticated, "
            "has_function_privilege('service_role',$1,'execute') service_role", ['public.' + function])
        assert acl['rows'] == [dict(anon=False, authenticated=False, service_role=True)]

    async def get(path, *, params, **_kwargs):
        assert path == '/rest/v1/astor_jobs'
        return httpx.Response(200, json=[dict(status='done', job_type='myprofile_latest_refresh_v1')])

    monkeypatch.setattr('supabase_client.sb_get', get)
    monkeypatch.setenv('COCOLON_ANALYSIS_OBSERVED_MODE', 'development')
    monkeypatch.setenv('ASTOR_WORKER_QUEUE_ENABLED', 'true')
    latest = asyncio.run(service.ensure_map(OWNER, ensure=False))
    monthly = asyncio.run(service.ensure_map(OWNER, monthly=True, ensure=False))
    status = asyncio.run(service.map_status(OWNER))
    material = asyncio.run(rpc('deep_insight_material', dict(p_user_id=OWNER)))
    assert not asyncio.run(service.read_maps(other, report_id=rid))['items']
    assert 'code' not in db.query("update public.profiles set subscription_tier='premium' where id=$1", [OWNER])
    if legacy:
        assert latest['report_id'] == monthly['report_id'] == rid
        assert status['has_visible_content']
        assert material['map']['id'] == rid
        plan = asyncio.run(rpc('analysis_if_base_context', dict(p_user_id=OWNER, p_base_ref=artifact.reference)))
        assert plan['base_projection'] == graph
        assert [row['id'] for row in asyncio.run(service.map_history(OWNER))['items']] == [rid]
        return

    assert not latest['has_visible_content'] and latest['report_id'] is None and latest['meta'] is None
    assert latest['reason'] == monthly['reason'] == service.NO_ACCEPTED_MAP_STRUCTURE
    assert status['refresh_status'] == latest['refresh_status'] == 'failed'
    assert not status['has_visible_content'] and material['map'] is None
    assert not asyncio.run(service.read_maps(OWNER, report_id=rid))['items']
    assert not asyncio.run(service.map_history(OWNER))['items']
    assert asyncio.run(service.read_maps(OWNER, limit=1, metadata_only=True))['withheld'] is True
    with pytest.raises(HTTPException, match='analysis_report_unavailable'):
        asyncio.run(get_detail(user_id=OWNER, family='self_structure', report_id=rid, month=month))
    with pytest.raises(HTTPException, match='analysis_report_unavailable'):
        asyncio.run(service.map_evidence(OWNER, rid, 'n1', month=month))
    with pytest.raises(HTTPException, match='P0002'):
        asyncio.run(rpc('analysis_if_base_context', dict(p_user_id=OWNER, p_base_ref=artifact.reference)))
    with pytest.raises(HTTPException, match='22023'):
        asyncio.run(rpc('analysis_cumulative_commit', dict(candidate, p_force=True)))

    tokens, sender, enqueue = AsyncMock(), AsyncMock(), AsyncMock()
    monkeypatch.setattr(worker, '_fetch_push_tokens_for_users', tokens)
    monkeypatch.setattr(worker, '_send_fcm_push', sender)
    stale = asyncio.run(worker._handle_send_fcm_push_v1(user_id=OWNER,
        payload=dict(recipient_mode='user_ids', recipient_user_ids=[OWNER], actor_user_id=OWNER,
            title='Emlis', body='わたしマップが更新されました', event_type='watashi_map_updated',
            data=dict(type='watashi_map_updated', target='watashi_map', user_id=OWNER,
                      report_id=rid, version_key=artifact.reference))))
    assert stale['status'] == 'skipped_stale_map_notification'
    tokens.assert_not_awaited()
    sender.assert_not_awaited()
    monkeypatch.setattr('astor_job_queue.enqueue_job', enqueue)
    assert asyncio.run(service.request_map_refresh(OWNER)) == 'failed'
    enqueue.assert_not_awaited()

    monkeypatch.setenv('COCOLON_ANALYSIS_PLAN_READ_ROLLOUT', 'free_plus.v1')
    accepted, good_coverage, _ = _artifact(COEXISTENCE, snapshot)
    next_accepted, _, _ = _artifact(COEXISTENCE, snapshot)
    monkeypatch.setattr(service, '_semantic_history_map', AsyncMock(
        side_effect=[(artifact, coverage), (accepted, good_coverage), (next_accepted, good_coverage)]))
    notify = AsyncMock()
    monkeypatch.setattr(service, '_queue_map_update_notification', notify)
    model = sources.SelfHostedSemanticAnalysisModelSource(endpoint='https://synthetic.invalid/v1/chat/completions',
        model=sources.SEMANTIC_OCCURRENCE_V24_9B_MODEL, api_key='synthetic',
        semantic_prompt_version=core.SEMANTIC_MAP_OCCURRENCE_V24_PROFILE)
    declined = asyncio.run(service.ensure_map(OWNER, model_source=model))
    assert declined['reason'] == service.NO_ACCEPTED_MAP_STRUCTURE
    assert not declined['refreshed'] and not declined['has_visible_content']
    notify.assert_not_awaited()
    recovered = asyncio.run(service.ensure_map(OWNER, model_source=model))
    assert recovered['refreshed'] and recovered['report_id'] != rid
    notify.assert_awaited_once()
    retained = asyncio.run(service.ensure_map(OWNER, monthly=True, ensure=False))
    assert retained['report_id'] == recovered['report_id'] and retained['snapshot_month'] == month
    next_report = asyncio.run(service.ensure_map(OWNER, force=True, model_source=model))
    assert next_report['refreshed'] and next_report['report_id'] != retained['report_id']
    assert asyncio.run(service.ensure_map(OWNER, monthly=True, ensure=False)) == retained
    assert db.query('select count(*)::integer as total from public.analysis_cumulative_months')['rows'] == [{'total': 1}]
    assert db.query('select count(*)::integer as total from public.analysis_observed_artifacts')['rows'] == [{'total': 3}]
    assert not asyncio.run(service.read_maps(OWNER, report_id=rid))['items']
    for historical_id, months_ago in ((rid, '1 month'), (next_report['report_id'], '2 months')):
        assert 'code' not in db.query('insert into public.analysis_cumulative_months(user_id,snapshot_month,artifact_id) '
            'values ($1,($2::date-$3::interval)::date,$4)', [OWNER, month, months_ago, historical_id])
    assert 'code' not in db.query("update public.profiles set subscription_tier='free' where id=$1", [OWNER])
    history = asyncio.run(service.map_history(OWNER, limit=1))
    assert [row['id'] for row in history['items']] == [retained['report_id']]
    assert history['has_more'] and history['next_offset'] == 1
    assert [row['id'] for row in asyncio.run(service.map_history(OWNER, limit=1, offset=1))['items']] == [
        next_report['report_id']]

    assert 'code' not in db.query('update public.emotions set memo_action=$1 where id=$2',
                                  ['以前と別の行動をとった。', originals[0]['id']])
    assert not asyncio.run(service.ensure_map(OWNER, ensure=False))['has_visible_content']
    assert asyncio.run(rpc('deep_insight_material', dict(p_user_id=OWNER)))['map'] is None
    after_edit = asyncio.run(service.ensure_map(OWNER, monthly=True, ensure=False))
    assert (after_edit['report_id'], after_edit['captured_at']) == (retained['report_id'], retained['captured_at'])
    assert after_edit['map_subscription_tier'] == 'free'


@pytest.mark.parametrize('queue_status,last_error,expected,will_enqueue', [
    ('failed', service.NO_ACCEPTED_MAP_STRUCTURE, 'failed', False),
    ('failed', 'analysis_model_source_unavailable', 'queued', True),
    ('queued', service.NO_ACCEPTED_MAP_STRUCTURE, 'queued', False),
    ('running', service.NO_ACCEPTED_MAP_STRUCTURE, 'running', False),
])
def test_only_terminal_empty_map_failure_stops_automatic_requeue(monkeypatch, queue_status, last_error, expected, will_enqueue):
    import httpx
    from unittest.mock import AsyncMock

    response = httpx.Response(200, json=[dict(status=queue_status, last_error=last_error,
                                              job_type='myprofile_latest_refresh_v1')])
    get = AsyncMock(return_value=response)
    enqueue = AsyncMock()
    monkeypatch.setenv('ASTOR_WORKER_QUEUE_ENABLED', 'true')
    monkeypatch.setenv('COCOLON_ANALYSIS_PLAN_READ_ROLLOUT', 'free_plus.v1')
    monkeypatch.setattr(service, 'observed_mode', lambda: 'development')
    monkeypatch.setattr(service, 'read_maps', AsyncMock(return_value={'items': []}))
    monkeypatch.setattr('supabase_client.sb_get', get)
    monkeypatch.setattr('astor_job_queue.enqueue_job', enqueue)

    assert asyncio.run(service.request_map_refresh(OWNER)) == expected
    assert bool(enqueue.await_count) == will_enqueue
    assert get.await_args.kwargs['params']['select'] == 'status,job_type,last_error'


def test_real_sql_commits_private_proof_and_rereads_one_saved_id_at_each_tier(saved_map_source):
    db, rpc, other, originals, snapshot = saved_map_source
    sql_script(db, '20261125205000_analysis_premium_structure_relations.sql')
    artifact, coverage, _ = _artifact(COEXISTENCE, snapshot)
    graph = artifact.safe_projection(authenticated_owner_scope=OWNER)
    private = artifact.private_evidence()
    private.update(coverage=coverage, source_record_refs=[x['id'] for x in originals])
    rid = asyncio.run(rpc('analysis_cumulative_commit', dict(p_user_id=OWNER, p_guard=snapshot['guard'],
        p_artifact_id=artifact.artifact_id, p_private_evidence=private, p_projection=graph,
        p_text=artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'],
        p_start=snapshot['period_start'], p_end=snapshot['period_end'])))
    expected = private['graph']['meaning_review']['structure_relations']['views']

    for tier in ('free', 'plus', 'premium', 'plus', 'free', 'premium'):
        assert 'code' not in db.query('update public.profiles set subscription_tier=$1 where id=$2', [tier, OWNER])
        current, = asyncio.run(service.read_maps(OWNER, limit=1))['items']
        history, = asyncio.run(service.read_maps(OWNER, history=True))['items']
        detail, = asyncio.run(service.read_maps(OWNER, report_id=rid, month=history['snapshot_month']))['items']
        for row in (current, history, detail):
            assert row['id'] == rid
            assert row['content_json']['watashiMap'] == graph
            assert row['content_json'].get('structure_relations') == (expected if tier == 'premium' else None)
            assert 'confirmed_outcome' not in json.dumps(row)
        summary, = asyncio.run(service.read_maps(OWNER, history=True, metadata_only=True))['items']
        assert summary['id'] == rid and 'content_json' not in summary
    assert not asyncio.run(service.read_maps(other, report_id=rid))['items']

    changed = db.query("update public.analysis_observed_artifacts set private_evidence="
        "jsonb_set(private_evidence,'{projection_of}','\"unrelated-artifact\"') where id=$1", [rid])
    assert changed['code'] == '55000'
    still_saved, = asyncio.run(service.read_maps(OWNER, limit=1))['items']
    assert still_saved['id'] == rid and still_saved['content_json']['structure_relations'] == expected
