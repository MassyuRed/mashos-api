"""Owner answers enter normal MAP through the actual saved-source boundary."""
from copy import deepcopy
import json
from uuid import UUID, uuid4
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
from test_emlis_natural_reply_application import natural_case
from test_emlis_q2_application import answer, run
from test_emlis_q3_application import qdb

QUESTION_ID = str(UUID(int=200))
OTHER = str(UUID(int=777))
QUESTION = '意見が違うとき、どんな反応だと本音を話しやすいですか？'
ANSWER = '最後まで話を聞いてくれるとき、私は本音を話しやすいです。'
NOTE = '私は会議の資料を机に置いた。'
RECEIVED_MAP_MIGRATIONS = (
    '20261003134440_analysis_observed_artifacts.sql',
    '20261004041627_analysis_period_comparison.sql',
    '20261101080144_cumulative_watashi_map.sql',
    '20261107071033_analysis_semantic_map_wire.sql',
    '20261114032520_analysis_interpretation_correction_sources.sql',
    '20261114120000_analysis_if_route_artifacts.sql',
    '20261114123000_analysis_emlis_material_handoff.sql',
    '20261114132000_analysis_map_interpretation_corrections.sql',
    '20261114133000_analysis_map_correction_handoff.sql',
    '20261121132000_deep_insight_questions.sql',
    '20261121133000_analysis_deep_insight_answer_handoff.sql',
)


@pytest.fixture(scope='module')
def received_map_db(qdb):
    for name in RECEIVED_MAP_MIGRATIONS:
        sql_script(qdb, name)
    return qdb


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


def _received_answer_plan(prepared, material, fields, selected, value):
    binding, = material['received_answer_thoughts']
    field_text = {field['field']: field['text'] for field in fields}

    def source(number):
        text = field_text[number]
        return dict(quote=selected.get((number, text), text), field=number)

    def node(index, *roots):
        return dict(node_id=f'n{index}', units=[dict(evidence=[root]) for root in roots])

    thought = source(binding['thought_field'])
    action = source(binding['action_field'])
    supplement = source(binding['answer_field'])
    insight = source(next(field['field'] for field in fields if field['source_role'] == DEEP_INSIGHT_ANSWER_ROLE))
    # The model selected the four complete sources and gave action its own
    # unit. Admission separates that unit into a node before NODES authors text.
    authored = dict(node_id='n1', units=[dict(evidence=[thought, supplement]), dict(evidence=[action])])
    value.update(source_choices_sha256=material['source_choices_sha256'],
        nodes=[authored, node(2, insight)])

    # The earlier model output attached the supplement to the action and
    # repeated it beside the thought, even though the original did not link them.
    repeated = [node(1, action, supplement), node(2, insight), node(3, thought, supplement)]
    merged = [dict(node_id='n1', units=[dict(evidence=[thought, supplement, action])]), node(2, insight)]
    for invalid in (repeated, merged):
        with pytest.raises(admission.AnalysisSemanticMapError,
                          match='analysis_semantic_plan_received_answer_scope_invalid'):
            admission.admit_semantic_node_local_v4_plan_response(prepared, dict(value, nodes=invalid))


def v24_provider(calls, *, received_case=False, plan_packet=None, scoped_node_guide=None):
    received_prepared = None
    received_plan = received_nodes = received_plan_raw = None

    def handler(request):
        nonlocal received_plan, received_nodes, received_plan_raw
        messages = json.loads(request.content)['messages']
        material = json.loads(messages[1]['content'])
        phase = material['author_phase']
        calls.append((phase, material))
        schema = probe.semantic_output_schema(messages)['properties']
        value = dict(schema_version=schema['schema_version']['enum'][0])
        if phase == 'PLAN':
            restored, table, _ = choices.restore_view(material)
            selected = {(field, quote): cue for (field, cue), quote in table.items()}
            if plan_packet is not None:
                value = plan_packet
            elif received_prepared is not None:
                _received_answer_plan(received_prepared, material, restored['fields'], selected, value)
            else:
                nodes, original_heads = [], {}
                for f in restored['fields']:
                    number, text = f['field'], f['text']
                    unit = dict(evidence=[dict(quote=selected.get((number, text), text), field=number)])
                    if f['source_role'] == 'SUPPLEMENTAL_ANSWER':
                        original_heads[f['record']]['units'].append(unit)
                    else:
                        node = dict(units=[unit])
                        nodes.append(node)
                        if f['source_role'] in {'ORIGINAL_INPUT', DEEP_INSIGHT_ANSWER_ROLE}:
                            original_heads.setdefault(f['record'], node)
                first_nodes = list(original_heads.values())
                ordered = first_nodes + [node for node in nodes if node not in first_nodes]
                value.update(source_choices_sha256=material['source_choices_sha256'],
                    nodes=[dict(node_id=f'n{index}', units=node['units']) for index, node in enumerate(ordered, 1)])
        elif phase == 'NODES':
            nodes = {}
            protected = {scope[key] for scope in material.get('received_answer_thoughts', ())
                         for key in ('thought_field', 'action_field')}
            for node in material['plan']['nodes']:
                ref = node['node_id']
                spec = schema['nodes']['properties'][ref]['properties']
                root = node['units'][0]['evidence'][0]
                text = root['quote']
                units = {}
                for index, selected_unit in enumerate(node['units'], 1):
                    unit_id = f'u{index}'
                    unit = spec['units']['properties'][unit_id]['properties']
                    quote = selected_unit['evidence'][0]['quote']
                    facts = {key: shape.get('enum', [quote])[0]
                             for key, shape in unit['fact_parts']['properties'].items()}
                    units[unit_id] = dict(evidence_ref=f'{ref}.{unit_id}',
                        source_mode='PERSON_JUDGMENT' if quote == ANSWER else 'RECORDED',
                        fact_parts=facts, unknowns=[])
                nodes[ref] = dict(units=units,
                    node_kind='SELF_POSITION' if text == ANSWER else 'CHOICE_OUTPUT', perspective='SELF',
                    title=spec['title'].get('enum', [text])[0], meaning=spec['meaning'].get('enum', [text])[0])
                if root['field'] in protected or (received_prepared is not None and text == ANSWER):
                    nodes[ref].update(title=text, meaning='')
            value.update(plan_sha256=schema['plan_sha256']['enum'][0], nodes=nodes)
            if scoped_node_guide is not None:
                prepared, titles = scoped_node_guide
                ordinary_material = dict(material)
                del ordinary_material['received_answer_thoughts']
                ordinary_messages = [messages[0], dict(role='user',
                    content=json.dumps(ordinary_material, ensure_ascii=False))]
                ordinary_nodes = probe.semantic_output_schema(ordinary_messages)['properties']['nodes']['properties']
                for node in material['plan']['nodes']:
                    ref = node['node_id']
                    spec = schema['nodes']['properties'][ref]
                    if ref not in titles:
                        assert spec == ordinary_nodes[ref]
                        continue
                    assert spec['properties']['title']['enum'] == titles[ref]
                    assert spec['properties']['meaning']['enum'] == ['']
                    changes = [('meaning', '発表後、褒められたことを重く受け止めた。')]
                    if len(node['units']) == 2:
                        changes.append(('title', node['units'][1]['evidence'][0]['quote']))
                    for field, wrong in changes:
                        changed = deepcopy(value)
                        changed['nodes'][ref][field] = wrong
                        assert accepts(changed, ordinary_messages)
                        assert not accepts(changed, messages)
                        with pytest.raises(admission.AnalysisSemanticMapError,
                                           match='analysis_semantic_node_received_answer_scope_invalid'):
                            admission.admit_semantic_node_local_v4_nodes_response(
                                prepared, material['plan'], changed)
            for node in material['plan']['nodes']:
                if received_prepared is None or node['units'][0]['evidence'][0]['field'] not in protected:
                    continue
                wrong_meaning = deepcopy(value)
                wrong_meaning['nodes'][node['node_id']]['meaning'] = '発表後、褒められたことを重く受け止めた。'
                with pytest.raises(admission.AnalysisSemanticMapError,
                                  match='analysis_semantic_node_received_answer_scope_invalid'):
                    admission.admit_semantic_node_local_v4_nodes_response(
                        received_prepared, material['plan'], wrong_meaning)
            if received_prepared is not None:
                received_plan = material['plan']
                received_nodes = admission.admit_semantic_node_local_v4_nodes_response(
                    received_prepared, received_plan, value)
        else:
            registry = material['candidate_nodes']
            overview = dict(node_refs=[node['node_id'] for node in registry])
            if 'title_proposal' in schema['overview']['properties']:
                overview.update(title_proposal='', title=choices.WholeMapTitle(material, registry).neutral)
            elif received_prepared is not None:
                overview['title'] = '2件の記録を振り返って'
            else:
                overview['title'] = '書き残した判断と行動'
            value.update(nodes_sha256=schema['nodes_sha256']['enum'][0],
                qualification_review={}, edges=[], overview=overview)
            if received_prepared is not None:
                assert overview['title'] == '2件の記録を振り返って'
                wrong_title = '発表後に褒められた経験と本音'
                wrong_overview = dict(overview, title=wrong_title)
                if 'title_proposal' in overview:
                    wrong_overview['title_proposal'] = wrong_title
                with pytest.raises(admission.AnalysisSemanticMapError,
                                  match='analysis_semantic_relation_received_answer_scope_invalid'):
                    admission.semantic_node_local_v4_relations(received_prepared, received_plan, received_nodes,
                        dict(value, overview=wrong_overview))
        assert accepts(value, messages), phase
        raw = json.dumps(value, ensure_ascii=False, separators=(',', ':'))
        if received_prepared is not None and phase == 'PLAN':
            received_plan_raw = raw
        return successful_response(raw)

    provider = model_sources.SelfHostedSemanticAnalysisModelSource(endpoint='https://synthetic-analysis.invalid/chat/completions',
        model='test-model', api_key='synthetic-test', semantic_prompt_version=admission.SEMANTIC_MAP_OCCURRENCE_V24_PROFILE,
        transport=httpx.MockTransport(handler))
    if received_case:
        complete = provider._node_local_v4

        async def capture_prepared(prepared, **kwargs):
            nonlocal received_prepared
            received_prepared = prepared
            try:
                response = await complete(prepared, **kwargs)
            except RuntimeError as error:
                phase = calls[-1][0] if calls else 'request setup'
                pytest.fail(f'V24 admission failed after {phase}: {error.__context__ or error}')
            receipt = json.loads(response.raw)['phases'][0]
            assert receipt['phase'] == 'PLAN' and receipt['raw'] == received_plan_raw
            return response

        provider._node_local_v4 = capture_prepared
    return provider


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
                 '20261121133000_analysis_deep_insight_answer_handoff.sql',
                 '20261121134000_deep_insight_grounded_questions.sql'):
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


def test_free_received_meaning_and_deep_insight_keep_original_fields_and_saved_evidence(natural_case, received_map_db, monkeypatch):
    qdb = received_map_db
    thought, action, supplement = '褒められたのに、嬉しくなかった。', '会議で発表した。', 'その時は重かった。'
    user, parent, emlis, _ = natural_case
    assert 'code' not in qdb.query("update public.emotions set memo=$2,memo_action=$3 where id=$1",
        [parent, thought, action])
    initial = run(emlis.start(user, parent))
    assert initial['pending_question']['text'] == '「褒められた」は、あなたにはどんな意味として届きましたか。'
    refined = run(answer(emlis, user, initial, supplement))
    assert refined['body_state'] == 'REFINED' and refined['answer_assessment'] == 'RESOLVED'
    assert 'code' not in qdb.query("""insert into public.deep_insight_questions
        (id,user_id,lane,theme,question_text,issued_on,question_key,text_key)
        values ($1,$2,'theme','人間関係',$3,(now() at time zone 'Asia/Tokyo')::date,'question-key','text-key')""",
        [QUESTION_ID, user, QUESTION])

    async def rpc(name, payload):
        args = ','.join(f'{key} => ${i}' for i, key in enumerate(payload, 1))
        values = [json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value
                  for value in payload.values()]
        result = qdb.query(f'select public.{name}({args}) as value', values, 'service_role')
        assert 'code' not in result, result
        return result['rows'][0]['value']

    issued_answer = run(rpc('deep_insight_answer', dict(p_user_id=user, p_question_id=QUESTION_ID, p_answer_text=ANSWER)))
    assert issued_answer['inserted'] and issued_answer['question']['id'] == QUESTION_ID
    snap = run(rpc('analysis_cumulative_source_snapshot', {'p_user_id': user}))
    assert snap['tier'] == 'free' and [row['original']['id'] for row in snap['members']] == [parent, QUESTION_ID]
    prepared = semantic.prepare_semantic_map(user, snap, prompt_version=admission.SEMANTIC_MAP_OCCURRENCE_V24_PROFILE)
    material = json.loads(prepared.material_json)
    assert not material.get('answered_feeling_circumstances')
    fields = material['fields']
    expected = [(1, 'ORIGINAL_INPUT', 'memo', thought), (1, 'ORIGINAL_INPUT', 'memo_action', action),
                (1, 'SUPPLEMENTAL_ANSWER', 'memo', supplement), (2, DEEP_INSIGHT_ANSWER_ROLE, 'memo', ANSWER)]
    assert [(field['record'], field['source_role'], field['field_path'], field['text']) for field in fields] == expected
    binding, = material['received_answer_thoughts']
    assert {key: binding[key] for key in ('record', 'thought_field', 'action_field', 'answer_field')} == dict(
        record=1, thought_field=1, action_field=2, answer_field=3)
    assert [thought[start:end].rstrip('。') for start, end in binding['thought_ranges']] == [
        '褒められた', '嬉しくなかった']
    assert [(row.saved_record_ref, len(row.child_source_envelope_refs)) for row in prepared.frozen.members] == [
        (parent, 2), (QUESTION_ID, 1)]

    pytest.importorskip('lmformatenforcer')
    calls = []
    provider = v24_provider(calls, received_case=True)
    monkeypatch.setattr(cumulative, '_rpc', rpc)
    monkeypatch.setattr(cumulative, 'observed_mode', lambda: 'development')
    monkeypatch.setattr(cumulative, '_queue_map_update_notification', AsyncMock())
    current = run(cumulative.ensure_map(user, model_source=provider))
    report = current['report_id']
    assert report and current['refreshed']
    assert current['map_context']['processed_count'] == current['map_context']['mapped_count'] == 2
    assert current['map_context']['excluded_count'] == 0
    assert [phase for phase, _ in calls] == ['PLAN', 'NODES', 'RELATIONS']
    plan = calls[1][1]['plan']
    assert [[[root['field'] for root in unit['evidence']] for unit in node['units']] for node in plan['nodes']] == [
        [[binding['thought_field']], [binding['answer_field']]], [[fields[-1]['field']]], [[binding['action_field']]]]
    assert current['meta']['edges'] == []
    assert current['meta']['overview']['title'] == '2件の記録を振り返って'
    assert [node['title'] for node in current['meta']['nodes']] == [thought, ANSWER, action]
    assert '発表後' not in current['content_text']
    reread = run(cumulative.ensure_map(user, ensure=False, model_source=provider))
    detail, = run(cumulative.read_maps(user, report_id=report, limit=1))['items']
    assert reread['report_id'] == detail['id'] == report
    assert current['meta'] == reread['meta'] == detail['content_json']['watashiMap']
    assert current['content_text'] == reread['content_text'] == detail['content_text']
    for text in (thought, action, supplement, ANSWER):
        assert text in detail['content_text']
    evidence_by_node = {node['node_ref']: run(cumulative.map_evidence(user, report, node['node_ref']))['items']
                        for node in current['meta']['nodes']}
    assert {ref: [item['id'] for item in evidence] for ref, evidence in evidence_by_node.items()} == {
        'n1': [parent], 'n2': [QUESTION_ID], 'n3': [parent]}
    assert all(item['version_state'] == 'CURRENT' for evidence in evidence_by_node.values() for item in evidence)
    thought_evidence, = evidence_by_node['n1']
    assert (thought_evidence['memo'], thought_evidence['memo_action'], thought_evidence['answers']) == (
        thought, action, [supplement])
    insight_evidence, = evidence_by_node['n2']
    assert insight_evidence['deep_insight'] == dict(question_text=QUESTION, answer_text=ANSWER)
    assert len(calls) == 3


@pytest.mark.parametrize('correct_short', [False, True])
def test_v24_whole_plan_keeps_two_answered_thoughts_and_actions_separate(natural_case, received_map_db, correct_short):
    qdb = received_map_db
    user, original, emlis, _ = natural_case
    thought, action = '褒められたのに、嬉しくなかった。', '会議で発表した。'
    short_text, replacement = 'つらかったんです', '私は不安だった'
    assert 'code' not in qdb.query('update public.emotions set memo=$2,memo_action=$3 where id=$1',
        [original, thought, action])
    second, short = str(uuid4()), str(uuid4())
    for identifier, memo, memo_action in ((second, thought, action), (short, short_text + '。', '')):
        assert 'code' not in qdb.query('''insert into public.emotions
            values ($1,$2,(now()-interval '5 seconds') at time zone 'UTC',$3,$4,
                array['仕事'],array['不安'],$5)''',
            [identifier, user, memo, memo_action, json.dumps([dict(type='不安', strength='medium')])])
    for identifier, supplement in ((original, 'その時は重かった。'), (second, 'その時は怖かった。')):
        initial = run(emlis.start(user, identifier))
        refined = run(answer(emlis, user, initial, supplement))
        assert refined['body_state'] == 'REFINED'

    if correct_short:
        from cocolon_meaning_experience_engine.natural_reply import NaturalReply
        from test_emlis_interpretation_correction import correct

        async def reply(material):
            corrections = json.loads(material.material_json).get('interpretation_corrections')
            body = (replacement if corrections else short_text) + '、と書いてくださったんですね。'
            return NaturalReply(body, 'isolated-direct-feeling', material.source_prefix_ref)

        emlis.natural_context_update_enabled = False
        emlis.natural_reply_source = reply
        original_short = run(emlis.start(user, short))
        assert (original_short['body_state'], original_short['issued_count']) == ('FINAL', 0)
        correction = run(correct(emlis, user, original_short, text=short_text,
            explanation=f'「{short_text}」ではなく「{replacement}」です。'))
        assert correction['body_state'] == 'FINAL'

    result = qdb.query('select public.analysis_cumulative_source_snapshot($1) as value', [user], 'service_role')
    assert 'code' not in result
    snapshot = result['rows'][0]['value']
    prepared = semantic.prepare_semantic_map(user, snapshot, prompt_version=admission.SEMANTIC_MAP_OCCURRENCE_V24_PROFILE)
    material = json.loads(prepared.material_json)
    received_scopes = sorted(material['received_answer_thoughts'], key=lambda scope: scope['record'])
    assert len(received_scopes) == 2
    messages = admission.semantic_node_local_v4_wire_messages(prepared, 'PLAN')
    prompt, inputs = messages
    shown = json.loads(inputs['content'])
    packet = dict(schema_version=admission._semantic_v4_schema('PLAN'),
                  source_choices_sha256=shown['source_choices_sha256'],
                  nodes=shown['received_answer_plan'])
    plan = admission.admit_semantic_node_local_v4_plan_response(prepared, packet)
    nodes = [[[part['field'] for part in unit['evidence']] for unit in node['units']] for node in plan['nodes']]
    for scope in received_scopes:
        assert [[scope['thought_field']], [scope['answer_field']]] in nodes
        assert [[scope['action_field']]] in nodes[len(material['records']):]
    if correct_short:
        field, = (field for field in material['fields'] if field['source_role'] == 'USER_INTERPRETATION_CORRECTION')
        assert field['text'] == replacement and [[field['field']]] in nodes
        assert short_text not in prompt['content']
        assert not admission._semantic_received_answer_plan(material, allow_multiple=True)
    crossed = deepcopy(packet)
    answers = [node['units'][1]['evidence'][0] for node in crossed['nodes'] if len(node['units']) == 2]
    answers[0]['field'], answers[1]['field'] = answers[1]['field'], answers[0]['field']
    with pytest.raises(admission.AnalysisSemanticMapError):
        admission.admit_semantic_node_local_v4_plan_response(prepared, crossed)

    node_prompt, _ = admission.semantic_node_local_v4_wire_messages(prepared, 'NODES', plan=plan)
    protected_titles = {scope[field]: text for scope in received_scopes
                        for field, text in (('thought_field', thought), ('action_field', action))}
    titles = {}
    for node in plan['nodes']:
        field = node['units'][0]['evidence'][0]['field']
        if field in protected_titles:
            titles[node['node_id']] = [protected_titles[field]]
    assert 'meaningは必ず空文字 ""' in node_prompt['content']
    assert json.dumps(titles, ensure_ascii=False, separators=(',', ':')) in node_prompt['content']

    pytest.importorskip('lmformatenforcer')
    assert accepts(packet, messages)
    coalesced = deepcopy(packet)
    answering_node = next(node for node in coalesced['nodes'] if len(node['units']) == 2)
    answering_node['units'][0]['evidence'].extend(answering_node['units'].pop()['evidence'])
    assert not accepts(coalesced, messages) and not accepts(crossed, messages)
    ordinary = deepcopy(messages)
    ordinary[1]['content'] = json.dumps({key: value for key, value in shown.items()
                                        if key != 'received_answer_plan'}, ensure_ascii=False)
    assert accepts(coalesced, ordinary)
    with pytest.raises(admission.AnalysisSemanticMapError, match='analysis_semantic_plan_received_answer_scope_invalid'):
        admission.admit_semantic_node_local_v4_plan_response(prepared, coalesced)

    calls = []
    response = run(v24_provider(calls, plan_packet=packet, scoped_node_guide=(prepared, titles))(prepared))
    artifact, coverage = semantic.build_semantic_map(prepared, response)
    assert [phase for phase, _ in calls] == ['PLAN', 'NODES', 'RELATIONS']
    assert coverage['mapped_count'] == 3
    projection = artifact.safe_projection(authenticated_owner_scope=user)
    assert not projection['edges']
    actions = [node for node in projection['nodes'] if node['title'] == action]
    assert len(actions) == 2
    assert len({node['summary'] for node in actions}) == 2
    assert all(node['summary'].endswith(f'の記録：\n{action}') or
               node['summary'].endswith(f'）：\n{action}') for node in actions)
    private_nodes = {node['node_ref']: node for node in artifact.private_evidence()['graph']['nodes']}
    assert {tuple(private_nodes[node['node_ref']]['record_refs']) for node in actions} == {(original,), (second,)}
    if correct_short:
        corrected, = (node for node in private_nodes.values() if node['record_refs'] == [short])
        assert replacement in corrected['explanation'] and short_text not in corrected['explanation']
