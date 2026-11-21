"""Owner answers enter normal MAP through the actual saved-source boundary."""
from copy import deepcopy
import json
from uuid import UUID
from unittest.mock import AsyncMock

import httpx
import pytest

import analysis_cumulative_service as cumulative
import analysis_model_source as model_sources
import analysis_plan_source_choices as choices
import analysis_semantic_map as semantic
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as admission
from cocolon_meaning_experience_engine.cores.analysis.source_adapter import DEEP_INSIGHT_ANSWER_ROLE
from test_analysis_cumulative import OWNER, source_snapshot
from test_analysis_cumulative_model_source import sql_source
from test_analysis_interpretation_correction_sources import sql_script
from test_analysis_node_local_native_profile import accepts, probe
from test_analysis_v24_progress_transport import successful_response
from test_emlis_q2_application import run

QUESTION_ID = str(UUID(int=200))
OTHER = str(UUID(int=777))
QUESTION = '意見が違うとき、どんな反応だと本音を話しやすいですか？'
ANSWER = '最後まで話を聞いてくれるとき、私は本音を話しやすいです。'
NOTE = '私は会議の資料を机に置いた。'


def answer_row():
    return dict(original=dict(id=QUESTION_ID, created_at='2026-11-20T15:00:00+00:00',
            memo=ANSWER, memo_action='', category=[], emotions=[], emotion_details=[]),
        thread=None, events=[], deep_insight=dict(user_id=OWNER, lane='records', theme=None,
            question_text=QUESTION, issued_on='2026-11-21'))


def test_v24_reads_answer_as_its_own_record_and_question_as_non_evidence():
    snap = source_snapshot(0)
    snap.update(now='2026-11-21T05:00:00+00:00', period_end='2026-11-21T05:00:00+00:00',
        period_start='2026-11-20T15:00:00+00:00', members=[answer_row()])
    prepared = semantic.prepare_semantic_map(OWNER, snap,
        prompt_version=admission.SEMANTIC_MAP_OCCURRENCE_V24_PROFILE)
    material = json.loads(prepared.material_json)
    assert material['records'][0]['deep_insight_question'] == QUESTION
    assert material['fields'][0]['source_role'] == DEEP_INSIGHT_ANSWER_ROLE
    assert material['fields'][0]['text'] == ANSWER
    assert '質問の仮説や前提を本人が認めたと決めず' in prepared.messages()[0]['content']
    source, = prepared.frozen.sources
    assert ANSWER.encode() in source.envelope.raw_utf8
    assert QUESTION.encode() not in source.envelope.raw_utf8
    with pytest.raises(ValueError):
        admission._semantic_map_evidence(prepared, dict(field=1, quote='意見が違うとき'))
    changed = deepcopy(snap)
    changed['members'][0]['deep_insight']['user_id'] = OTHER
    with pytest.raises(ValueError, match='analysis_saved_owner_mismatch'):
        semantic.prepare_semantic_map(OWNER, changed)


def v24_provider(calls):
    def handler(request):
        messages = json.loads(request.content)['messages']
        material = json.loads(messages[1]['content'])
        phase = material['author_phase']
        calls.append((phase, material))
        schema = probe.semantic_output_schema(messages)['properties']
        value = dict(schema_version=schema['schema_version']['enum'][0])
        if phase == 'PLAN':
            restored, table, _ = choices.restore_view(material)
            selected = {(field, quote): cue for (field, cue), quote in table.items()}
            nodes = []
            for f in restored['fields']:
                number, text = f['field'], f['text']
                nodes.append(dict(node_id=f'n{len(nodes) + 1}', units=[dict(evidence=[
                    dict(quote=selected.get((number, text), text), field=number)])]))
            value.update(source_choices_sha256=material['source_choices_sha256'], nodes=nodes)
        elif phase == 'NODES':
            nodes = {}
            for node in material['plan']['nodes']:
                ref = node['node_id']
                spec = schema['nodes']['properties'][ref]['properties']
                unit = spec['units']['properties']['u1']['properties']
                text = node['units'][0]['evidence'][0]['quote']
                facts = {key: shape.get('enum', [text])[0] for key, shape in unit['fact_parts']['properties'].items()}
                nodes[ref] = dict(units=dict(u1=dict(evidence_ref=ref + '.u1',
                    source_mode='PERSON_JUDGMENT' if text == ANSWER else 'RECORDED', fact_parts=facts, unknowns=[])),
                    node_kind='SELF_POSITION' if text == ANSWER else 'CHOICE_OUTPUT', perspective='SELF',
                    title=spec['title'].get('enum', [text])[0], meaning=spec['meaning'].get('enum', [text])[0])
            value.update(plan_sha256=schema['plan_sha256']['enum'][0], nodes=nodes)
        else:
            registry = material['candidate_nodes']
            overview = dict(node_refs=[node['node_id'] for node in registry])
            if 'title_proposal' in schema['overview']['properties']:
                overview.update(title_proposal='', title=choices.WholeMapTitle(material, registry).neutral)
            else:
                overview['title'] = '書き残した判断と行動'
            value.update(nodes_sha256=schema['nodes_sha256']['enum'][0],
                qualification_review={}, edges=[], overview=overview)
        assert accepts(value, messages), phase
        return successful_response(json.dumps(value, ensure_ascii=False, separators=(',', ':')))

    return model_sources.SelfHostedSemanticAnalysisModelSource(endpoint='https://synthetic-analysis.invalid/chat/completions',
        model='test-model', api_key='synthetic-test', semantic_prompt_version=admission.SEMANTIC_MAP_OCCURRENCE_V24_PROFILE,
        transport=httpx.MockTransport(handler))


@pytest.mark.parametrize('prior_map', [False, True])
def test_answer_updates_normal_v24_map_through_provider_and_database(sql_source, monkeypatch, prior_map):
    pytest.importorskip('lmformatenforcer')
    db, rpc = sql_source
    for name in ('20261107071033_analysis_semantic_map_wire.sql',
                 '20261114032520_analysis_interpretation_correction_sources.sql',
                 '20261114120000_analysis_if_route_artifacts.sql',
                 '20261114123000_analysis_emlis_material_handoff.sql',
                 '20261114132000_analysis_map_interpretation_corrections.sql',
                 '20261114133000_analysis_map_correction_handoff.sql'):
        sql_script(db, name)
    for user in (OWNER, OTHER):
        assert 'code' not in db.query('insert into auth.users values ($1)', [user])
        assert 'code' not in db.query("insert into public.profiles values ($1,'free')", [user])

    if prior_map:
        original = source_snapshot(1)['members'][0]['original']
        assert 'code' not in db.query('insert into public.emotions values ($1,$2,$3,$4,$5,$6,$7,$8)',
            [original['id'], OWNER, original['created_at'], NOTE, '', original['category'],
             original['emotions'], json.dumps(original['emotion_details'])])

    def snapshot(owner=OWNER):
        return run(rpc('analysis_cumulative_source_snapshot', {'p_user_id':owner}))

    before = snapshot()['guard']
    for name in ('20261121132000_deep_insight_questions.sql',
                 '20261121133000_analysis_deep_insight_answer_handoff.sql'):
        sql_script(db, name)
    assert snapshot()['guard'] == before
    calls = []
    provider = v24_provider(calls)
    old = run(cumulative.ensure_map(OWNER, model_source=provider)) if prior_map else None
    assert 'code' not in db.query('''insert into public.deep_insight_questions
        (id,user_id,lane,question_text,issued_on,question_key,text_key)
        values ($1,$2,'records',$3,(now() at time zone 'Asia/Tokyo')::date,'question-key','text-key')''',
        [QUESTION_ID, OWNER, QUESTION])
    assert snapshot()['guard'] == before
    assert len(snapshot()['members']) == int(prior_map)
    if old:
        assert run(cumulative.read_maps(OWNER, limit=1))['items'][0]['id'] == old['report_id']
    answered = run(rpc('deep_insight_answer', dict(p_user_id=OWNER,
        p_question_id=QUESTION_ID, p_answer_text=ANSWER)))
    assert answered['inserted'] and answered['question']['answer_text'] == ANSWER
    snap = snapshot()
    assert snap['guard'] != before and not snapshot(OTHER)['members']
    assert snap['members'][-1]['original']['memo'] == ANSWER
    assert not run(cumulative.read_maps(OWNER, limit=1))['items']
    if old:
        assert run(cumulative.read_maps(OWNER, history=True))['items'][0]['id'] == old['report_id']
        assert run(rpc('analysis_if_sources_current', dict(p_user_id=OWNER, p_guard=before,
            p_refs=[original['id']])))

    import astor_job_queue as queue
    monkeypatch.setenv('ASTOR_WORKER_QUEUE_ENABLED', 'true')
    monkeypatch.setattr(cumulative, 'map_refresh_status', AsyncMock(side_effect=[None, 'queued']))
    enqueued = AsyncMock()
    monkeypatch.setattr(queue, 'enqueue_job', enqueued)
    assert run(cumulative.request_map_refresh(OWNER, trigger='deep_insight_answer')) == 'queued'
    assert run(cumulative.request_map_refresh(OWNER)) == 'queued'
    assert enqueued.await_count == 1
    assert enqueued.await_args.kwargs['payload']['force'] is False

    current = run(cumulative.ensure_map(OWNER, model_source=provider))
    report = current['report_id']
    assert [phase for phase, _ in calls] == ['PLAN', 'NODES', 'RELATIONS'] * (1 + int(prior_map))
    assert all(any(record.get('deep_insight_question') == QUESTION for record in material['records'])
        for _, material in calls[-3:])
    assert report is not None and current['refreshed']
    saved = run(cumulative.read_maps(OWNER, report_id=report))['items'][0]
    assert saved['content_text'] == current['content_text'] and ANSWER in saved['content_text']
    assert len(calls) == 3 * (1 + int(prior_map))
    evidence = run(cumulative.map_evidence(OWNER, report, f'n{1 + int(prior_map)}'))['items']
    assert evidence[0]['deep_insight'] == dict(question_text=QUESTION, answer_text=ANSWER)
    assert evidence[0]['id'] == QUESTION_ID and evidence[0]['version_state'] == 'CURRENT'
    assert not run(cumulative.read_maps(OTHER, report_id=report))['items']
    assert 'code' not in db.query('delete from public.deep_insight_questions where id=$1', [QUESTION_ID])
    assert not run(cumulative.read_maps(OWNER, report_id=report, history=True))['items']
