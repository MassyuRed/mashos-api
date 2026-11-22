"""Keep original qualifications and their authored resolution across MAP and history."""
import asyncio
import json

import httpx
import pytest

import analysis_if_model_source as if_sources
import analysis_model_source as sources
import analysis_semantic_map as app
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_cumulative import OWNER, source_snapshot
from test_analysis_event_plan_model_alias import environment
from test_analysis_node_local_native_profile import accepts
import test_analysis_node_local_v4_phases as phases


PENDING = '初日は修理が終わったか聞いていない。'
REPORTED = '翌日、画面の修理が終わったと連絡が来た。'
BROTHER = '弟が電池の相談を店へ送ったかは聞いていない。'
MIXED = '完了の連絡は読んだが、' + BROTHER
FIRST_FACT = '初日は修理の進み具合を知らずにいました。'
SECOND_FACT = '翌日に店から修理完了の知らせが届きました。'
THIRD_FACT = '知らせは読みました。弟が店に相談したかは把握していません。'


def prepared(profile):
    snapshot = source_snapshot(2)
    for member, text in zip(snapshot['members'], (PENDING, REPORTED + MIXED), strict=True):
        member['original'].update(memo=text, memo_action='')
    return app.prepare_semantic_map(OWNER, snapshot, prompt_version=profile)


def packets(p):
    """Build a pair of dated repair notes, or the subset present in one leaf."""
    fields = json.loads(p.material_json)['fields']
    plan = dict(schema_version=core._semantic_v4_schema('PLAN'), nodes=[])
    node_map, review = {}, {}
    for index, field in enumerate(fields, 1):
        ref = f'n{index}'
        earlier = field['text'] == PENDING
        quotes = [PENDING] if earlier else [REPORTED, MIXED]
        parts = [FIRST_FACT] if earlier else [SECOND_FACT, THIRD_FACT]
        source = [dict(quote=quote, field=field['field']) for quote in quotes]
        plan['nodes'].append(dict(node_id=ref, units=[dict(evidence=source)]))
        candidate = PENDING if earlier else MIXED
        unit = dict(evidence_ref=ref + '.u1', source_mode='RECORDED',
                    fact_parts={f'e{i}': part for i, part in enumerate(parts, 1)},
                    unknowns=[dict(source_quote=candidate, source_field=field['field'])])
        node_map[ref] = dict(units={'u1': unit}, node_kind='STATE_CONTEXT', perspective='SELF',
                             title='当初の修理状況' if earlier else '修理の知らせと弟の相談', meaning='')
        key = ref + '.u1.q1'
        review[key] = (dict(status='EARLIER') if earlier and len(fields) == 2
                       else dict(status='OPEN', source_quote=PENDING if earlier else BROTHER))
    nodes = dict(schema_version=core._semantic_v4_schema('NODES'),
                 plan_sha256=core.semantic_map_hash(plan), nodes=node_map)
    relations = dict(schema_version=core._semantic_v4_schema('RELATIONS'),
                     nodes_sha256=core.semantic_map_hash(core._semantic_v4_join(plan, nodes)))
    if p.prompt_version == core.SEMANTIC_MAP_OCCURRENCE_V7_PROFILE:
        relations['qualification_review'] = review
    relations.update(edges=[], overview=dict(node_refs=list(node_map), title='修理の経過'))
    return plan, nodes, relations


def reply(p, values):
    packet = phases.artifact(p, values)
    packet['schema_version'] = core.semantic_node_local_v4_artifact_schema(p)
    return phases.response(p, packet)


def public_unknowns(artifact):
    projection = artifact.safe_projection(authenticated_owner_scope=OWNER)
    return {node['node_ref']: node['unknowns'] for node in projection['nodes']}


def test_v7_mixed_source_preserves_unknown_and_factual_paraphrase_in_public_output():
    p = prepared(core.SEMANTIC_MAP_OCCURRENCE_V7_PROFILE)
    plan, nodes, relations = packets(p)
    for phase, value in zip(core.SEMANTIC_MAP_NODE_LOCAL_V4_PHASES, (plan, nodes, relations), strict=True):
        messages = core.semantic_node_local_v4_messages(p, phase, plan=plan, nodes=nodes)
        assert accepts(value, messages)
    material = json.loads(messages[1]['content'])
    assert set(material['qualification_candidates']) == {'n1.u1.q1', 'n2.u1.q1'}
    assert material['qualification_candidates']['n2.u1.q1']['source_quote'] == MIXED
    response = reply(p, (plan, nodes, relations))
    artifact, coverage = app.build_semantic_map(p, response)
    assert coverage['mapped_count'] == 2
    assert public_unknowns(artifact) == {'n1': [], 'n2': [BROTHER]}
    text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
    assert FIRST_FACT in text and SECOND_FACT + THIRD_FACT in text
    proof = artifact.private_evidence()['graph']['meaning_review']['node_local_plan']['phase_artifact']
    assert proof == json.loads(response.raw)


def test_leaf_keeps_earlier_unknown_and_merge_can_resolve_it_from_later_record():
    parent = prepared(core.SEMANTIC_MAP_OCCURRENCE_V7_PROFILE)
    leaves = []
    for member in parent.frozen.members:
        leaf = core.prepare_semantic_leaf(parent, (member.saved_record_ref,))
        values = packets(leaf)
        result = reply(leaf, values)
        graph = core.build_semantic_stage(leaf, result)
        assert json.loads(graph.meaning_review_json)['node_local_plan']['phase_artifact'] == json.loads(result.raw)
        expected = [PENDING] if not leaves else [BROTHER]
        assert json.loads(graph.nodes_json)[0]['unknowns'] == expected
        leaves.append((leaf, result))
    merge = core.prepare_semantic_merge(parent, tuple(leaves))
    merged = core.build_semantic_stage(merge, reply(merge, packets(merge)))
    assert public_unknowns(merged.artifact) == {'n1': [], 'n2': [BROTHER]}


@pytest.mark.parametrize('error', ['missing', 'extra', 'foreign_source', 'unbounded_fragment', 'closed_with_quote', 'invented_status'])
def test_reject_malformed_or_unbound_review_in_decoder_and_map(error):
    p = prepared(core.SEMANTIC_MAP_OCCURRENCE_V7_PROFILE)
    plan, nodes, rel = packets(p)
    review = rel['qualification_review']
    if error == 'missing':
        del review['n1.u1.q1']
    elif error == 'extra':
        review['n2.u1.q2'] = dict(status='STATED')
    elif error == 'foreign_source':
        review['n2.u1.q1']['source_quote'] = PENDING
    elif error == 'unbounded_fragment':
        review['n2.u1.q1']['source_quote'] = '電池'
    elif error == 'closed_with_quote':
        review['n1.u1.q1']['source_quote'] = PENDING
    else:
        review['n1.u1.q1']['status'] = 'UNKNOWN'
    messages = core.semantic_node_local_v4_messages(p, 'RELATIONS', plan=plan, nodes=nodes)
    assert not accepts(rel, messages)
    with pytest.raises(core.AnalysisSemanticMapError):
        core.semantic_node_local_v4_relations(p, plan, nodes, rel)


def test_legacy_candidates_are_unchanged_and_review_is_profile_bound():
    v6 = prepared(core.SEMANTIC_MAP_OCCURRENCE_V6_PROFILE)
    v7 = prepared(core.SEMANTIC_MAP_OCCURRENCE_V7_PROFILE)
    legacy, current = packets(v6), packets(v7)
    artifact, _ = app.build_semantic_map(v6, reply(v6, legacy))
    assert public_unknowns(artifact) == {'n1': [PENDING], 'n2': [MIXED]}
    for p, values, opposite in ((v6, legacy, current), (v7, current, legacy)):
        plan, nodes, valid = values
        messages = core.semantic_node_local_v4_messages(p, 'RELATIONS', plan=plan, nodes=nodes)
        assert accepts(valid, messages) and not accepts(opposite[2], messages)
        with pytest.raises(core.AnalysisSemanticMapError):
            core.semantic_node_local_v4_relations(p, plan, nodes, opposite[2])


def test_configured_map_uses_three_model_replies_and_keeps_if_on_its_own_model(monkeypatch):
    alias = sources.SEMANTIC_OCCURRENCE_V7_MODEL
    environment(monkeypatch, model=alias)
    selected = sources.application_analysis_model_source()
    assert if_sources.application_analysis_if_model_source().model == sources.SEMANTIC_EVENT_PLAN_BASE_MODEL
    profile = sources.analysis_model_prompt_version(selected)
    assert profile == core.SEMANTIC_MAP_OCCURRENCE_V7_PROFILE
    p = prepared(profile)
    values = packets(p)
    received = []

    def receive(request):
        body = json.loads(request.content)
        index = len(received)
        phase = json.loads(body['messages'][1]['content'])['author_phase']
        assert phase == core.SEMANTIC_MAP_NODE_LOCAL_V4_PHASES[index]
        assert body['model'] == alias and body['max_tokens'] == 4096 - index * 100
        text = json.dumps(values[index], ensure_ascii=False)
        received.append(text)
        return httpx.Response(200, json={'model': alias, 'usage': {'completion_tokens': 100},
            'choices': [{'finish_reason': 'stop', 'message': {'role': 'assistant', 'content': text}}]})

    original_client = httpx.AsyncClient
    monkeypatch.setattr(sources.httpx, 'AsyncClient', lambda **kwargs:
                        original_client(**{**kwargs, 'transport': httpx.MockTransport(receive)}))
    acquired = asyncio.run(selected(p))
    assert len(received) == 3
    assert [stage['raw'] for stage in json.loads(acquired.raw)['phases']] == received
    artifact, _ = app.build_semantic_map(p, acquired)
    assert public_unknowns(artifact) == {'n1': [], 'n2': [BROTHER]}
