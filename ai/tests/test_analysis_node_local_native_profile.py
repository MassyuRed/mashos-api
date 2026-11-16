"""Native/private transport checks with fictional packets; no model or GPU."""
from copy import deepcopy
from http.server import ThreadingHTTPServer
import asyncio
import json
import threading

import httpx
import pytest

import analysis_if_model_source as if_sources
import analysis_model_source as sources
from test_emlis_natural_reply_probe_http import probe

PROFILE = 'semantic_map.node_local.v3'
SCHEMA = 'cocolon.analysis.semantic_map.node_local.model.v3'
ALIAS = 'cocolon-qwen3.5-4b-analysis-node-local-v3'
BASE_ALIAS = 'cocolon-qwen3.5-4b-analysis-node-local-v3-base-851bf6e'
SAVED = '私は図面を保存した。'
REPAIRED = '妹は棚を直した。'
UNKNOWN = '塗装を終えたかは聞いていない。'


def messages(fields=None, *, leaf=False):
    material = dict(model_schema=SCHEMA, fields=fields or [
        dict(field=1, record=1, text=SAVED + 'まだ送っていない。'),
        dict(field=2, record=2, text=REPAIRED + UNKNOWN)])
    if leaf:
        material['history_stage'] = dict(kind='LEAF')
    return [dict(role='system', content='Fictional native protocol check.'),
        dict(role='user', content=json.dumps(material, ensure_ascii=False))]


def unit(field, quote, *, unknown=False):
    return dict(evidence=[dict(quote=quote, field=field)], source_mode='RECORDED',
        fact=quote, unknowns=[dict(source_quote=quote, source_field=field)] if unknown else [])


def packet():
    # Both units in the first node belong to record2. Record1 stays in its own
    # later node instead of being forced into the first node's second unit.
    return dict(schema_version=SCHEMA, nodes=[
        dict(units=[unit(2, REPAIRED), unit(2, UNKNOWN, unknown=True)],
            node_kind='STATE_CONTEXT', perspective='OBSERVED_INTERACTION',
            title='妹の作業と未確認の範囲', meaning=''),
        dict(units=[unit(1, SAVED)], node_kind='CHOICE_OUTPUT', perspective='SELF',
            title='本人が保存した図面', meaning='本人が保存を終えた記録です。')],
        edges=[dict(**{'from': 'n1', 'to': 'n2'}, relation_kind='CONTEXT_CONTRAST',
            label='別々の人の作業')], overview=dict(title='作業の記録', node_refs=['n1', 'n2']))


def advance(parser, text):
    for char in text:
        if char not in parser.get_allowed_characters():
            raise ValueError('native_character_rejected')
        parser = parser.add_character(char)
    return parser


def accepts(value, selected=None):
    pytest.importorskip('lmformatenforcer')
    selected = selected or messages()
    text = json.dumps(value, ensure_ascii=False, separators=(',', ':'))
    alphabet = ''.join(dict.fromkeys(text + json.dumps(selected, ensure_ascii=False) + ' '))
    try:
        return advance(probe.semantic_json_parser(selected, alphabet), text).can_end()
    except ValueError:
        return False


def test_node_local_units_do_not_force_a_different_record_into_the_same_node():
    value = packet()
    assert accepts(value)
    prefix = json.dumps(value, ensure_ascii=False, separators=(',', ':'))
    prefix = prefix[:prefix.index('],"edges"') + 1]
    # Closing after only the first node would omit record1, even though its
    # second unit may legally continue to describe the already visited record2.
    first = json.dumps(value['nodes'][0], ensure_ascii=False, separators=(',', ':'))
    start = '{"schema_version":' + json.dumps(SCHEMA) + ',"nodes":[' + first
    alphabet = ''.join(dict.fromkeys(prefix + json.dumps(messages(), ensure_ascii=False)))
    state = advance(probe.semantic_json_parser(messages(), alphabet), start)
    assert ']' not in state.get_allowed_characters()
    assert ',' in state.get_allowed_characters()
    second = json.dumps(value['nodes'][1], ensure_ascii=False, separators=(',', ':'))
    state = advance(state, ',' + second)
    assert ']' in state.get_allowed_characters()


@pytest.mark.parametrize('mutation', [
    'unit-overflow', 'node-overflow', 'unknown-overflow', 'overview-overflow',
    'wire-node-id', 'unknown-from-neighbour-unit', 'duplicate-pair',
    'missing-node-endpoint', 'self-edge', 'duplicate-edge',
    'missing-overview-node', 'duplicate-overview-node', 'no-record1',
])
def test_native_rejects_unbound_local_roots_refs_and_public_budget_overflows(mutation):
    value = packet()
    if mutation == 'unit-overflow':
        value['nodes'][0]['units'].append(unit(2, REPAIRED))
    elif mutation == 'node-overflow':
        value['nodes'] = [deepcopy(value['nodes'][0]) for _ in range(12)] + [value['nodes'][1]]
    elif mutation == 'unknown-overflow':
        value['nodes'][0]['units'][1]['unknowns'] *= 3
    elif mutation == 'overview-overflow':
        value['nodes'] = [deepcopy(value['nodes'][0]) for _ in range(8)] + [value['nodes'][1]]
        value['overview']['node_refs'] = ['n' + str(i) for i in range(1, 10)]
    elif mutation == 'wire-node-id':
        value['nodes'][0]['node_id'] = 'n1'
    elif mutation == 'unknown-from-neighbour-unit':
        value['nodes'][0]['units'][0]['unknowns'] = [dict(source_quote=UNKNOWN, source_field=2)]
    elif mutation == 'duplicate-pair':
        value['nodes'][0]['units'][0]['evidence'] *= 2
    elif mutation == 'missing-node-endpoint':
        value['edges'][0]['to'] = 'n3'
    elif mutation == 'self-edge':
        value['edges'][0]['to'] = 'n1'
    elif mutation == 'duplicate-edge':
        value['edges'].append(dict(value['edges'][0], **{'from': 'n2', 'to': 'n1'}))
    elif mutation == 'missing-overview-node':
        value['overview']['node_refs'] = ['n3']
    elif mutation == 'duplicate-overview-node':
        value['overview']['node_refs'] = ['n1', 'n1']
    else:
        value['nodes'] = value['nodes'][:1]
        value['edges'] = []
        value['overview']['node_refs'] = ['n1']
    assert not accepts(value), mutation


def test_leaf_keeps_local_units_but_has_no_edges():
    value = packet()
    value['edges'] = []
    assert accepts(value, messages(leaf=True))
    assert not accepts(packet(), messages(leaf=True))


def test_token_enforcement_completes_the_node_local_wire_without_premature_eos():
    pytest.importorskip('lmformatenforcer')
    from lmformatenforcer.tokenenforcer import TokenEnforcer, TokenEnforcerTokenizerData
    raw = json.dumps(packet(), ensure_ascii=False, separators=(',', ':'))
    vocabulary = list(dict.fromkeys(raw + json.dumps(messages(), ensure_ascii=False)))
    ids = {char: index for index, char in enumerate(vocabulary)}
    eos = len(vocabulary)
    data = TokenEnforcerTokenizerData([(index, char, False) for index, char in enumerate(vocabulary)],
        lambda tokens: ''.join(vocabulary[token] for token in tokens), eos, False, eos + 1)
    parser = probe.semantic_json_parser(messages(), data.tokenizer_alphabet)
    enforcer = TokenEnforcer(data, parser)
    enforcer.root_parser.config.force_json_field_order = True
    prefix = [eos]  # The initial prompt is not parsed as generated output.
    for char in raw:
        allowed = enforcer.get_allowed_tokens(prefix).allowed_tokens
        assert eos not in allowed
        assert ids[char] in allowed
        prefix.append(ids[char])
    assert eos in enforcer.get_allowed_tokens(prefix).allowed_tokens


def test_large_source_retains_the_existing_explicit_partial_coverage_exception():
    fields = [dict(field=i, record=i, text='資料' + str(i) + 'を保存した。') for i in range(1, 101)]
    selected = messages(fields)
    value = packet()
    value['nodes'] = [dict(value['nodes'][1], units=[unit(100, fields[-1]['text'])])]
    value['edges'] = []
    value['overview']['node_refs'] = ['n1']
    assert accepts(value, selected)
    assert len(json.loads(selected[1]['content'])['fields']) == 100


@pytest.mark.parametrize('model, expected', [
    (ALIAS, PROFILE),
    (BASE_ALIAS, PROFILE),
    (ALIAS + '-unconfigured', 'semantic_map.v1'),
    (BASE_ALIAS + '-unconfigured', 'semantic_map.v1'),
    (sources.SEMANTIC_EVENT_PLAN_V2_MODEL, 'semantic_map.event_plan.v2'),
    (sources.SEMANTIC_EVENT_PLAN_V2_BASE_MODEL, 'semantic_map.event_plan.v2'),
    (sources.SEMANTIC_EVENT_PLAN_MODEL, 'semantic_map.event_plan.v1'),
])
def test_exact_model_identity_selects_the_map_contract_and_keeps_if_on_120u(monkeypatch, model, expected):
    for key, value in dict(COCOLON_ANALYSIS_MODEL_SOURCE=sources.SEMANTIC_SELECTOR,
            COCOLON_ANALYSIS_MODEL_ENDPOINT='https://private.invalid/v1/chat/completions',
            COCOLON_ANALYSIS_MODEL=model, COCOLON_ANALYSIS_MODEL_API_KEY='synthetic-private-key').items():
        monkeypatch.setenv(key, value)
    selected = sources.application_analysis_model_source()
    assert sources.analysis_model_prompt_version(selected) == expected
    actual_if = if_sources.application_analysis_if_model_source()
    assert actual_if.model == (model if model.endswith('-unconfigured') else sources.SEMANTIC_EVENT_PLAN_BASE_MODEL)
    assert actual_if._max_tokens == 4096
    assert actual_if._settings_snapshot == sources._settings()


@pytest.mark.parametrize('alias', [ALIAS, BASE_ALIAS])
def test_application_node_local_transport_uses_the_existing_long_semantic_budgets(monkeypatch, alias):
    from test_analysis_semantic_map import OWNER, sample
    import analysis_semantic_map as app
    from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
    prepared = app.prepare_semantic_map(OWNER, sample(), prompt_version=PROFILE)
    calls = []
    def handler(request):
        body = json.loads(request.content)
        calls.append(body)
        assert body['model'] == alias and body['max_tokens'] == 4096
        assert body['messages'] == prepared.messages()
        assert request.extensions['timeout']['read'] == 220.0
        assert request.extensions['timeout']['connect'] == 15.0
        return httpx.Response(200, json=dict(model=alias, choices=[dict(finish_reason='stop',
            message=dict(role='assistant', content='fictional-raw-transport-check'))]))
    source = sources.SelfHostedSemanticAnalysisModelSource(endpoint='https://private.invalid/v1/chat/completions',
        model=alias, api_key='synthetic-private-key', semantic_prompt_version=PROFILE,
        transport=httpx.MockTransport(handler))
    result = asyncio.run(source(prepared))
    assert result.finish_reason == 'stop' and len(calls) == 1
    assert source.prompt_version == core.SEMANTIC_MAP_NODE_LOCAL_V3_PROFILE
    assert sources.SEMANTIC_REQUEST_TIMEOUT_SECONDS == 225.0
    assert sources.SEMANTIC_PIPELINE_TIMEOUT_SECONDS == 840.0


@pytest.mark.parametrize('alias, expected_profile', [(ALIAS, 'event_plan'), (BASE_ALIAS, 'event_plan_base')])
def test_native_admits_only_the_configured_node_local_alias_and_schema(alias, expected_profile):
    calls = []
    def generate(selected, end, *, profile=None):
        calls.append(profile)
        return 'fictional-native-response', 'stop'
    server = ThreadingHTTPServer(('127.0.0.1', 0), probe.make_handler(generate,
        api_key='analysis-test-key', model_name=sources.SEMANTIC_EVENT_PLAN_BASE_MODEL,
        deadline=float('inf'), max_requests=0, max_new_tokens=4096, request_seconds=210,
        natural_reply=dict(api_key='natural-test-key', model_name='natural'), event_plan_model=alias))
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        with httpx.Client(trust_env=False) as client:
            url = 'http://127.0.0.1:' + str(server.server_port) + '/v1/chat/completions'
            def post(model, marker, *, key='analysis-test-key', tokens=4096):
                selected = [dict(role='system', content='fictional'),
                    dict(role='user', content=json.dumps(dict(model_schema=marker)))]
                return client.post(url, headers={'Authorization': 'Bearer ' + key},
                    json=dict(model=model, messages=selected, max_tokens=tokens, temperature=0,
                        stream=False, chat_template_kwargs={'enable_thinking': False}))
            assert post(alias, probe.EVENT_PLAN_V2_SCHEMA).status_code == 400
            assert post(sources.SEMANTIC_EVENT_PLAN_BASE_MODEL, SCHEMA).status_code == 400
            assert post(alias + '-other', SCHEMA).status_code == 400
            assert post(BASE_ALIAS if alias == ALIAS else ALIAS, SCHEMA).status_code == 400
            assert calls == []
            response = post(alias, SCHEMA)
            assert response.status_code == 200 and response.json()['model'] == alias
            assert post(sources.SEMANTIC_EVENT_PLAN_BASE_MODEL, probe.IF_CANDIDATE_SCHEMA).status_code == 200
            assert post('natural', None, key='natural-test-key', tokens=2048).status_code == 200
            assert calls == [expected_profile, None, 'natural']
    finally:
        server.shutdown()
        server.server_close()
        worker.join(3)
