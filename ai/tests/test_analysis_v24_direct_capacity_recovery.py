"""Use bound synthetic responses to exercise direct-PLAN growth and recovery."""
import asyncio
import json

import httpx
import pytest
from fastapi import HTTPException

import analysis_cumulative_service as cumulative
import analysis_merge_wire as wire
import analysis_model_source as sources
import analysis_semantic_map as maps
from analysis_job_progress import map_job_progress
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_cumulative import OWNER, source_snapshot
from test_analysis_cumulative_model_source import sql_source  # noqa: F401
from test_analysis_interpretation_correction_sources import sql_script
from test_analysis_node_local_native_profile import probe
from test_analysis_occurrence_v17_record_owners import packet as plan_packet


def bind_reply(messages):
    if wire.is_compact(messages):
        messages_for_model = wire.legacy_messages(messages)
        codec = wire.response_codec(messages)
    else:
        messages_for_model = messages
        codec = None
    material = json.loads(messages_for_model[1]['content'])
    phase = material['author_phase']
    props = probe.semantic_output_schema(messages)['properties']
    packet = dict(schema_version=props['schema_version']['enum'][0])
    if phase == 'PLAN':
        from analysis_plan_source_choices import restore_view

        restored, choices, _ = restore_view(material)
        selected = {(field, quote): cue for (field, cue), quote in choices.items()}
        packet.update(source_choices_sha256=material['source_choices_sha256'], nodes=[
            dict(node_id=f'n{i}', units=[dict(evidence=[dict(field=f['field'],
                quote=selected.get((f['field'], f['text']), f['text']))])])
            for i, f in enumerate(restored['fields'], 1)])
    elif phase == 'NODES':
        nodes = {}
        for node in material['plan']['nodes']:
            ref = node['node_id']
            spec = props['nodes']['properties'][ref]['properties']
            root = node['units'][0]['evidence'][0]
            units = {}
            for unit_id, unit_shape in spec['units']['properties'].items():
                facts = {key: value.get('enum', [root['quote']])[0] for key, value in
                    unit_shape['properties']['fact_parts']['properties'].items()}
                units[unit_id] = dict(evidence_ref=f'{ref}.{unit_id}', source_mode='RECORDED',
                    fact_parts=facts, unknowns=[])
            nodes[ref] = dict(units=units, node_kind='CHOICE_OUTPUT', perspective='SELF',
                title=spec['title'].get('enum', [root['quote']])[0], meaning=spec['meaning'].get('enum', [''])[0])
        packet.update(plan_sha256=props['plan_sha256']['enum'][0], nodes=nodes)
    else:
        from analysis_plan_source_choices import WholeMapTitle

        registry = material['candidate_nodes']
        overview = dict(node_refs=[node['node_id'] for node in registry],
            title=WholeMapTitle(material, registry).neutral)
        if 'title_proposal' in props['overview']['properties']:
            overview['title_proposal'] = ''
        packet.update(nodes_sha256=props['nodes_sha256']['enum'][0],
            qualification_review={}, edges=[], overview=overview)
    return material.get('history_stage', {}).get('kind', 'DIRECT'), phase, codec.encode(packet) if codec else packet


@pytest.mark.parametrize('rejected_phase', ['NODES', 'RELATIONS', 'PROVIDER', 'TOKEN_BUDGET', 'PROMPT_BUILD'])
def test_later_direct_capacity_uses_same_guard_and_saves_once(monkeypatch, sql_source, rejected_phase):
    db, db_rpc = sql_source
    sql_script(db, '20261107071033_analysis_semantic_map_wire.sql')
    snapshot = source_snapshot(2, tier='premium')
    for index, note in enumerate(['私は朝に庭の土を見た。', '私は夕方に植木鉢へ水を足した。']):
        snapshot['members'][index]['original']['memo'] = note
    initial = maps.prepare_semantic_map(OWNER, snapshot, prompt_version=core.SEMANTIC_MAP_OCCURRENCE_V24_PROFILE)
    leaf_refs = tuple(member.saved_record_ref for member in initial.frozen.members)
    assert cumulative.prepare_semantic_history_batches(initial) == ()
    assert [leaf.record_refs for leaf in cumulative.prepare_semantic_history_batches(initial,
        split_fitting_parent=True)] == [(ref,) for ref in leaf_refs]

    original_wire = core.semantic_node_local_v4_wire_messages

    def grow_direct_prompt(prepared, phase='PLAN', **kwargs):
        messages = original_wire(prepared, phase, **kwargs)
        if (type(prepared) is core.AnalysisSemanticMapInput
                and not prepared.request_ref.startswith('analysis-semantic-stage:')):
            if phase == rejected_phase:
                messages = [*messages, dict(role='user', content='x' * sources.SEMANTIC_MAX_PROMPT_BYTES)]
            elif phase == 'RELATIONS' and rejected_phase == 'PROMPT_BUILD':
                raise ValueError('invalid test prompt')
        return messages

    monkeypatch.setattr(core, 'semantic_node_local_v4_wire_messages', grow_direct_prompt)
    assert 'code' not in db.query('insert into auth.users values ($1)', [OWNER])
    assert 'code' not in db.query("insert into public.profiles values ($1, 'premium')", [OWNER])
    for member in snapshot['members']:
        original = member['original']
        params = [original['id'], OWNER, original['created_at'], original['memo'], '',
            original['category'], original['emotions'], '[]']
        assert 'code' not in db.query('insert into public.emotions values ($1,$2,$3,$4,$5,$6,$7,$8)', params)
    seen, commits, ownership_checks = [], [], []

    async def tracked_rpc(name, payload):
        if name == 'analysis_cumulative_commit':
            commits.append(payload)
        return await db_rpc(name, payload)

    async def check():
        ownership_checks.append(list(seen))

    def handler(request):
        body = json.loads(request.content)
        kind, phase, packet = bind_reply(body['messages'])
        seen.append((kind, phase))
        if rejected_phase == 'PROVIDER':
            return httpx.Response(503)
        completion = body['max_tokens'] if rejected_phase == 'TOKEN_BUDGET' and phase == 'NODES' else 20
        return httpx.Response(200, json=dict(model='synthetic-v24', usage=dict(completion_tokens=completion),
            choices=[dict(finish_reason='stop', message=dict(role='assistant',
                content=json.dumps(packet, ensure_ascii=False, separators=(',', ':'))))]))

    source = sources.SelfHostedSemanticAnalysisModelSource(endpoint='https://synthetic.invalid/chat/completions',
        model='synthetic-v24', api_key='synthetic-only', transport=httpx.MockTransport(handler),
        semantic_prompt_version=initial.prompt_version)
    monkeypatch.setattr(cumulative, '_rpc', tracked_rpc)
    monkeypatch.setenv('COCOLON_ANALYSIS_OBSERVED_MODE', 'development')
    if rejected_phase in {'PROVIDER', 'TOKEN_BUDGET', 'PROMPT_BUILD'}:
        with map_job_progress(check, check), pytest.raises(HTTPException) as error:
            asyncio.run(cumulative.ensure_map(OWNER, model_source=source))
        assert error.value.status_code == 503
        assert seen == ([('DIRECT', 'PLAN')] if rejected_phase == 'PROVIDER'
                        else [('DIRECT', 'PLAN'), ('DIRECT', 'NODES')])
        assert not ownership_checks and not commits
        return
    with map_job_progress(check, check):
        result = asyncio.run(cumulative.ensure_map(OWNER, model_source=source))
        readback = asyncio.run(cumulative.read_maps(OWNER, limit=1))

    phases = core.SEMANTIC_MAP_NODE_LOCAL_V4_PHASES
    direct_phases = phases[:phases.index(rejected_phase)]
    assert seen == ([('DIRECT', phase) for phase in direct_phases]
        + [(kind, phase) for kind in ('LEAF', 'LEAF', 'MERGE') for phase in phases])
    assert ownership_checks[0] == seen[:len(direct_phases)]
    assert ownership_checks[-1] == seen
    assert len(commits) == 1
    assert commits[0]['p_private_evidence']['coverage']['source_count'] == 2
    assert set(commits[0]['p_private_evidence']['source_record_refs']) == set(leaf_refs)
    assert result['refreshed'] and readback['items'][0]['id'] == result['report_id']


def test_later_prompt_can_exceed_limit_when_plan_fits_without_exhausting_output_tokens(caplog):
    snapshot = source_snapshot(91, tier='premium')
    for i, row in enumerate(snapshot['members']):
        row['original']['memo'] = (f'予算の条件{i}と納期を考え、締め切りを担当課へ確認し、会議に参加するか確かめた。'
            if i < 38 else '')
        row['original']['memo_action'] = (f'資料の手順{i}を確かめて、担当者へ聞いた条件を照合してから、担当者へ確認した。'
            if i % 5 == 0 else '')
    profile = core.SEMANTIC_MAP_OCCURRENCE_V24_PROFILE
    prepared = maps.prepare_semantic_map(OWNER, snapshot, prompt_version=profile,
        primary_structures='karen.v3', recover_witnessed_structures=True)
    fields = json.loads(prepared.material_json)['fields'][:48]
    units = [[(f['field'], f['text']) for f in fields[i:i + 4]] for i in range(0, len(fields), 4)]
    raw = plan_packet(prepared, [[roots[:3], roots[3:]] for roots in units])
    admitted = core.admit_semantic_node_local_v4_plan_response(prepared, raw)
    nodes_prompt = core.semantic_node_local_v4_wire_messages(prepared, 'NODES', plan=admitted)
    assert cumulative.prepare_semantic_history_batches(prepared) == ()
    assert len(core.semantic_map_canonical(nodes_prompt).encode()) > sources.SEMANTIC_MAX_PROMPT_BYTES
    seen = []

    def handler(request):
        body = json.loads(request.content)
        seen.append(json.loads(body['messages'][1]['content'])['author_phase'])
        return httpx.Response(200, json=dict(model='synthetic-v24', usage=dict(completion_tokens=1000),
            choices=[dict(finish_reason='stop', message=dict(role='assistant', content=json.dumps(raw)))]))

    source = sources.SelfHostedSemanticAnalysisModelSource(endpoint='https://synthetic.invalid/chat/completions',
        model='synthetic-v24', api_key='synthetic-only', transport=httpx.MockTransport(handler),
        semantic_prompt_version=profile)
    with pytest.raises(sources.AnalysisDirectHistoryPromptTooLarge):
        asyncio.run(source(prepared))
    assert seen == ['PLAN']
    assert 'phase=NODES stage=prompt_bytes http_status=None' in caplog.text
