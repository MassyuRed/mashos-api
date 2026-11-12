"""Existing source meanings improve the actual map, independently of model prose.

Responses are synthetic. These tests establish source/graph/text/save-reader
behavior, not real-4B editing quality or product acceptance.
"""
from copy import deepcopy
from dataclasses import replace
import asyncio
import hashlib
import json
from pathlib import Path

import httpx
import pytest

import analysis_semantic_map as semantic
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as admission
from test_analysis_cumulative import OWNER, source_snapshot
from test_analysis_semantic_map import response
from test_analysis_cumulative_model_source import sql_source


def prepare(snapshot):
    return semantic.prepare_semantic_map(OWNER, snapshot,
        prompt_version=admission.SEMANTIC_MAP_SOURCE_DUTIES_PROFILE)


def condition_sample():
    snapshot = source_snapshot(2)
    snapshot['members'][0]['original'].update(
        memo='私は会議にいた。', memo_action='私は資料を調べなかった。')
    snapshot['members'][1]['original'].update(
        memo='私は自宅にいた。', memo_action='私は資料を調べた。')
    return snapshot


def condition_candidate():
    return dict(schema_version=semantic.MODEL_SCHEMA,
        overview=dict(title='資料との関わり方', summary='二つの記録で行動が異なっています。'),
        nodes=[dict(node_id='n1', node_kind='CHOICE_OUTPUT', title='調べなかった記録',
                    summary='資料を調べなかったと記されています。',
                    explanation='この記録で選ばれた行動を、別の記録と見比べます。',
                    perspective='SELF', unknowns=[],
                    evidence=[dict(field=2, quote='私は資料を調べなかった')]),
               dict(node_id='n2', node_kind='CHOICE_OUTPUT', title='調べた記録',
                    summary='資料を調べたと記されています。',
                    explanation='調べたという結果だけから、その意図は決めません。',
                    perspective='SELF', unknowns=[],
                    evidence=[dict(field=4, quote='私は資料を調べた')])],
        edges=[dict(**{'from': 'n1', 'to': 'n2'}, relation_kind='CONTEXT_CONTRAST',
                    label='記録された行動の違い',
                    explanation='行動が異なる二つの記録として見比べられます。')])


def build(snapshot, packet, *, legacy=False):
    current = prepare(snapshot)
    prepared = (admission.prepare_analysis_semantic_map(current.source_request, snapshot,
        prompt_version=admission.SEMANTIC_MAP_PROFILE) if legacy else current)
    artifact, coverage = semantic.build_semantic_map(prepared, response(prepared, packet))
    return prepared, artifact, coverage


def test_source_duties_keep_all_fields_and_independent_claim_axes_without_intent_inference():
    snapshot = condition_sample()
    before = deepcopy(snapshot)
    prepared = prepare(snapshot)
    assert prepared.prompt_version == admission.SEMANTIC_MAP_SOURCE_DUTIES_PROFILE
    material = json.loads(prepared.material_json)
    assert [field['text'] for field in material['fields']] == [
        '私は会議にいた。', '私は資料を調べなかった。',
        '私は自宅にいた。', '私は資料を調べた。']
    duties = json.loads(prepared.source_duties_json)
    compact = material['source_duties']
    assert all(set(claim) == {'claim_ref', 'field', 'span', 'reading'} for claim in compact['claims'])
    assert all('quote' not in claim and 'source_parts' not in claim['reading']
               for claim in compact['claims'])
    assert len(duties['claims']) == 4
    actions = [c for c in duties['claims'] if c['node_kind'] == 'ACTION_OR_NONACTION']
    assert [c['proposition']['polarity'] for c in actions] == ['negative', 'positive']
    assert all(c['proposition']['actor'] == 'SELF' and c['proposition']['modality'] == 'fact'
               and c['proposition']['temporal_scope'] == 'past' for c in actions)
    assert duties['written_relations'] == []  # field/record order is not event order
    assert 'RESULT_TO_INTENT' in duties['forbidden_promotions']
    assert duties['interpretation_status'] == 'UNASSESSED'
    assert snapshot == before and OWNER not in prepared.material_json
    assert '条件を見比べ' in prepared.messages()[0]['content']


def test_proved_conditions_survive_on_actual_map_edge_text_and_private_roots():
    packet = condition_candidate()
    prepared, artifact, coverage = build(condition_sample(), packet)
    projection = artifact.safe_projection(authenticated_owner_scope=OWNER)
    private = artifact.private_evidence()
    assert projection['nodes'][0]['summary'] == packet['nodes'][0]['summary']
    assert '同じ記録に書かれた場面：私は会議にいた' in projection['nodes'][0]['context']
    assert '同じ記録に書かれた場面：私は自宅にいた' in projection['nodes'][1]['context']
    explanation = projection['edges'][0]['explanation']
    assert explanation.startswith(packet['edges'][0]['explanation'])
    assert '「私は会議にいた」と「私は自宅にいた」' in explanation
    text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
    assert explanation in text
    assert all(note in text for node in projection['nodes'] for note in node['context'])
    assert coverage['mapped_count'] == 2  # records, never meaning-validation counts
    for node, record in zip(private['graph']['nodes'], (1, 2)):
        assert node['record_refs'] == [prepared.frozen.members[record - 1].saved_record_ref]
        assert {root['field_path'] for root in node['evidence_refs']} == {'memo', 'memo_action'}
        for root in node['evidence_refs']:
            field = next(f for f in prepared.fields if f[3].source_envelope_id == root['source_envelope_id']
                         and f[3].field_path == root['field_path'])
            quote = field[1][root['scalar_start']:root['scalar_end']]
            assert hashlib.sha256(quote.encode()).hexdigest() == root['literal_sha256']
    assert 'source_duties' not in json.dumps(projection)
    assert 'source_envelope_id' not in json.dumps(projection)


def test_v1_prepared_messages_and_map_remain_unchanged_and_replay_through_same_engine():
    snapshot, packet = condition_sample(), condition_candidate()
    prepared, artifact, _ = build(snapshot, packet, legacy=True)
    assert prepared.prompt_version == 'semantic_map.v1'
    assert 'source_duties' not in json.loads(prepared.material_json)
    assert prepared.messages() == [
        dict(role='system', content=admission._SEMANTIC_MAP_INSTRUCTION +
             '\n参照辞書（本人の事実ではない）:\n' + prepared.dictionary_json),
        dict(role='user', content=prepared.material_json)]
    expected_ref = 'analysis-semantic-request:' + admission.semantic_map_hash([
        'semantic_map.v1', prepared.frozen.owner_scope, prepared.frozen.source_set_ref,
        snapshot['guard'], prepared.material_json, prepared.dictionary_json])
    assert prepared.request_ref == expected_ref
    projection = artifact.safe_projection(authenticated_owner_scope=OWNER)
    assert all(node['context'] == ['仕事：平穏'] for node in projection['nodes'])
    assert projection['edges'][0]['explanation'] == packet['edges'][0]['explanation']
    # Saved projection/text reading does not acquire a new model response.
    saved = deepcopy(projection)
    assert semantic.semantic_projection_text(saved) == artifact.safe_text_projection(
        authenticated_owner_scope=OWNER)['text']


def test_interpretation_is_not_rejected_or_classified_by_the_finite_source_reader():
    snapshot = source_snapshot(1)
    snapshot['members'][0]['original'].update(
        memo='気持ちを急いで決めず、今ある迷いをそのまま見ておきたい。', memo_action='')
    prepared = prepare(snapshot)
    duties = json.loads(prepared.source_duties_json)
    assert duties['claims'] == [] and duties['unassessed_source_ranges']
    packet = condition_candidate()
    packet['nodes'] = [dict(packet['nodes'][0],
        title='迷いを残しておく', summary='迷いを急いで確定しないという読みです。',
        explanation='本人が気持ちをどう扱いたいかを考える手がかりとして読めます。',
        evidence=[dict(field=1, quote='今ある迷いをそのまま見ておきたい')])]
    packet['edges'] = []
    artifact, _ = semantic.build_semantic_map(prepared, response(prepared, packet))
    assert artifact.safe_projection(authenticated_owner_scope=OWNER)['nodes'][0]['explanation'] == packet['nodes'][0]['explanation']


def test_each_premise_keeps_wish_day_and_unknown_actor_instead_of_promoting_it_to_fact():
    snapshot = source_snapshot(1)
    snapshot['members'][0]['original'].update(
        memo='私は資料を調べたい。', memo_action='昨日資料を調べた。')
    prepared = prepare(snapshot)
    duties = json.loads(prepared.source_duties_json)
    assert any(c['proposition']['modality'] == 'wish' for c in duties['claims'])
    assert any(c['proposition']['actor'] == 'UNSPECIFIED'
               and c['proposition']['relative_day'] == 'YESTERDAY' for c in duties['claims'])
    packet = condition_candidate()
    packet['nodes'][0].update(title='資料を調べたいという希望',
        summary='資料を調べる希望が書かれています。',
        explanation='希望は、実行済みの記録と分けて読めます。',
        evidence=[dict(field=1, quote='私は資料を調べたい')])
    packet['nodes'][1].update(title='昨日の資料との関わり',
        summary='昨日資料を調べた記録です。',
        explanation='誰が行ったかは、この記述では明記されていません。',
        evidence=[dict(field=2, quote='昨日資料を調べた')])
    packet['edges'] = []
    artifact, _ = semantic.build_semantic_map(prepared, response(prepared, packet))
    nodes = artifact.safe_projection(authenticated_owner_scope=OWNER)['nodes']
    assert '希望として書かれた内容：私は資料を調べたい' in nodes[0]['context']
    assert '根拠に書かれた時点：この記述時点の昨日' in nodes[1]['context']
    assert '誰についての記述かは、この根拠だけでは特定されていません。' in nodes[1]['context']


def test_source_duty_tampering_does_not_acquire_evidence_or_a_saved_map():
    prepared = prepare(condition_sample())
    material = json.loads(prepared.material_json)
    material['source_duties']['claims'][0]['span'] = [0, 1]
    forged = replace(prepared, material_json=admission.semantic_map_canonical(material))
    with pytest.raises(semantic.SemanticMapError, match='analysis_semantic_input_unbound'):
        semantic.build_semantic_map(forged, response(forged, condition_candidate()))


def test_long_existing_edge_text_is_preserved_while_conditions_remain_on_nodes():
    packet = condition_candidate()
    packet['edges'][0]['explanation'] = '記' * 1800
    _, artifact, _ = build(condition_sample(), packet)
    projection = artifact.safe_projection(authenticated_owner_scope=OWNER)
    assert projection['edges'][0]['explanation'] == packet['edges'][0]['explanation']
    assert all(any(note.startswith('同じ記録に書かれた場面：') for note in node['context'])
               for node in projection['nodes'])


def test_actual_visible_polarity_reversal_is_rejected_even_with_a_valid_quoted_root():
    prepared = prepare(condition_sample())
    packet = condition_candidate()
    packet['nodes'][0]['summary'] = '私は資料を調べた。'
    with pytest.raises(semantic.SemanticMapError, match='analysis_semantic_meaning_conflict'):
        semantic.build_semantic_map(prepared, response(prepared, packet))


def test_private_review_distinguishes_a_checked_premise_from_unassessed_interpretation():
    packet = condition_candidate()
    packet['nodes'][0]['summary'] = '私は資料を調べなかった。'
    _, artifact, _ = build(condition_sample(), packet)
    private = artifact.private_evidence()
    review = private['graph']['meaning_review']
    fields = {row['field']: row for row in review['nodes'][0]['fields']}
    assert fields['summary']['verdict'] == 'NO_CONFLICT_IN_CHECKED_SCOPE'
    assert fields['explanation']['verdict'] == 'UNASSESSED'
    assert review['interpretation_status'] == 'UNASSESSED'
    assert 'meaning_review' not in json.dumps(artifact.safe_projection(authenticated_owner_scope=OWNER))


def test_scene_change_updates_only_its_supported_context_and_relationship():
    packet = condition_candidate()
    _, old, _ = build(condition_sample(), packet)
    changed = condition_sample()
    changed['members'][0]['original']['memo'] = '私は図書館にいた。'
    _, new, _ = build(changed, packet)
    old_map = old.safe_projection(authenticated_owner_scope=OWNER)
    new_map = new.safe_projection(authenticated_owner_scope=OWNER)
    assert old_map['nodes'][1] == new_map['nodes'][1]
    for field in ('title', 'summary', 'explanation', 'unknowns'):
        assert old_map['nodes'][0][field] == new_map['nodes'][0][field]
    assert '同じ記録に書かれた場面：私は図書館にいた' in new_map['nodes'][0]['context']
    assert '私は会議にいた' not in new.safe_text_projection(authenticated_owner_scope=OWNER)['text']
    assert '私は図書館にいた' in new_map['edges'][0]['explanation']


@pytest.mark.parametrize('written,visible', [
    ('私は資料を調べたい。', '私は資料を調べた。'),
    ('私は資料を調べたかった。', '私は資料を調べたい。'),
    ('私は昨日資料を調べた。', '私は今日資料を調べた。'),
])
def test_existing_full_clause_axes_reject_modality_and_time_changes(written, visible):
    snapshot = source_snapshot(1)
    snapshot['members'][0]['original'].update(memo=written, memo_action='')
    prepared = prepare(snapshot)
    packet = condition_candidate()
    packet['nodes'] = [dict(packet['nodes'][0], summary=visible,
        evidence=[dict(field=1, quote=written[:-1])])]
    packet['edges'] = []
    with pytest.raises(semantic.SemanticMapError, match='analysis_semantic_meaning_conflict'):
        semantic.build_semantic_map(prepared, response(prepared, packet))


def test_a_quote_about_someone_else_does_not_supply_a_self_scene_condition():
    snapshot = source_snapshot(1)
    snapshot['members'][0]['original'].update(
        memo='友人は「私は会議にいた」と言った。', memo_action='私は資料を調べた。')
    prepared = prepare(snapshot)
    duties = json.loads(prepared.source_duties_json)
    assert not any(c['proposition']['scene_state'] for c in duties['claims'])
    packet = condition_candidate()
    packet['nodes'] = [dict(packet['nodes'][1], node_id='n1',
        evidence=[dict(field=2, quote='私は資料を調べた')])]
    packet['edges'] = []
    artifact, _ = semantic.build_semantic_map(prepared, response(prepared, packet))
    assert not any(note.startswith('同じ記録に書かれた場面：')
        for note in artifact.safe_projection(authenticated_owner_scope=OWNER)['nodes'][0]['context'])


def test_explicit_profile_reaches_http_engine_save_and_non_generating_read(monkeypatch):
    import analysis_cumulative_service as service
    import analysis_model_source as sources
    from test_analysis_semantic_integration import (OwnedStore, setup_store,
        completion, ENDPOINT, MODEL)
    store = OwnedStore(snapshot=condition_sample())
    setup_store(monkeypatch, store)
    acquired = []

    def handler(request):
        body = json.loads(request.content)
        material = json.loads(body['messages'][1]['content'])
        assert material['source_duties']['claims']
        assert all('quote' not in c for c in material['source_duties']['claims'])
        acquired.append(body)
        return httpx.Response(200, json=completion(condition_candidate()))

    source = sources.SelfHostedSemanticAnalysisModelSource(endpoint=ENDPOINT, model=MODEL,
        api_key='synthetic-private-key', transport=httpx.MockTransport(handler),
        semantic_prompt_version=admission.SEMANTIC_MAP_SOURCE_DUTIES_PROFILE)
    assert sources.analysis_model_prompt_version(source) == admission.SEMANTIC_MAP_SOURCE_DUTIES_PROFILE
    ordinary = sources.SelfHostedSemanticAnalysisModelSource(endpoint=ENDPOINT,
        model=MODEL, api_key='synthetic-private-key')
    assert sources.analysis_model_prompt_version(ordinary) == admission.SEMANTIC_MAP_PROFILE

    async def run():
        created = await service.ensure_map(OWNER, model_source=source)
        monkeypatch.setattr(semantic.MeaningExperienceEngine, 'generate', lambda *a, **kw:
            (_ for _ in ()).throw(AssertionError('saved read must not generate')))
        reread = await service.ensure_map(OWNER, model_source=source)
        readonly = await service.ensure_map(OWNER, ensure=False, model_source=source)
        assert created['meta'] == reread['meta'] == readonly['meta']
        assert created['content_text'] == reread['content_text'] == readonly['content_text']
        assert len(acquired) == len(store.saved) == 1
        assert '私は会議にいた' in created['content_text']
        assert '私は自宅にいた' in created['meta']['edges'][0]['explanation']
        legacy = service.map_response_for_renderer(created, None)
        assert legacy['meta']['wire_kind'] == 'watashi.map.v2'
        assert '私は会議にいた' in legacy['content_text']
        assert '私は自宅にいた' in legacy['content_text']
        private = store.saved[0]['p_private_evidence']
        assert private['graph']['meaning_review']['interpretation_status'] == 'UNASSESSED'

    asyncio.run(run())


def test_explicit_source_context_survives_actual_sql_and_non_generating_read(sql_source, monkeypatch):
    """Real existing SQL/RPC storage; the HTTP/model result is synthetic."""
    import analysis_cumulative_service as service
    import analysis_model_source as sources
    from test_analysis_semantic_integration import completion, ENDPOINT, MODEL
    db, _ = sql_source
    migration = Path(__file__).parents[2] / 'supabase/migrations/20261107071033_analysis_semantic_map_wire.sql'
    db.proc.stdin.write(json.dumps(dict(script=True, sql=migration.read_text())) + '\n')
    db.proc.stdin.flush()
    assert 'code' not in json.loads(db.proc.stdout.readline())
    assert 'code' not in db.query('insert into auth.users values ($1)', [OWNER])
    assert 'code' not in db.query("insert into public.profiles values ($1,'free')", [OWNER])
    for member in condition_sample()['members']:
        row = member['original']
        assert 'code' not in db.query('insert into public.emotions values ($1,$2,$3,$4,$5,$6,$7,$8)',
            [row['id'], OWNER, row['created_at'], row['memo'], row['memo_action'],
             row['category'], row['emotions'], json.dumps(row['emotion_details'])])
    acquired = []

    def handler(request):
        material = json.loads(json.loads(request.content)['messages'][1]['content'])
        assert len(material['source_duties']['claims']) == 4
        acquired.append(material)
        return httpx.Response(200, json=completion(condition_candidate()))

    source = sources.SelfHostedSemanticAnalysisModelSource(endpoint=ENDPOINT, model=MODEL,
        api_key='synthetic-private-key', transport=httpx.MockTransport(handler),
        semantic_prompt_version=admission.SEMANTIC_MAP_SOURCE_DUTIES_PROFILE)

    async def run():
        created = await service.ensure_map(OWNER, model_source=source)
        stored = db.query('select private_evidence,safe_projection,content_text '
            'from public.analysis_observed_artifacts where id=$1', [created['report_id']])['rows'][0]
        assert stored['safe_projection'] == created['meta']
        assert stored['content_text'] == created['content_text']
        assert stored['private_evidence']['graph']['meaning_review']['interpretation_status'] == 'UNASSESSED'
        assert all({root['field_path'] for root in node['evidence_refs']} == {'memo', 'memo_action'}
            for node in stored['private_evidence']['graph']['nodes'])
        monkeypatch.setattr(semantic.MeaningExperienceEngine, 'generate', lambda *a, **kw:
            (_ for _ in ()).throw(AssertionError('SQL read must not generate')))
        reread = await service.ensure_map(OWNER, model_source=source)
        readonly = await service.ensure_map(OWNER, ensure=False, model_source=source)
        assert created['meta'] == reread['meta'] == readonly['meta']
        assert created['content_text'] == reread['content_text'] == readonly['content_text']
        assert '私は会議にいた' in created['meta']['edges'][0]['explanation']
        assert len(acquired) == 1

    asyncio.run(run())
