"""Source-copy decoding constraints; no model or semantic-quality acceptance."""
from copy import deepcopy
import ast
import hashlib
import inspect
import json
import logging
import string
import sys
from types import SimpleNamespace
import pytest
from test_emlis_natural_reply_probe_http import probe


def schema_for(fields):
    return probe.semantic_output_schema([{'role': 'system', 'content': 'synthetic'},
        {'role': 'user', 'content': json.dumps({'fields': fields}, ensure_ascii=False)}])


UNIQUE_EVIDENCE_CASES = [
    ([[(1, '同じ。')]], True),
    ([[(1, '同じ。'), (1, '同じ。')]], False),
    ([[(1, '同じ。'), (2, '同じ。')]], True),
    ([[(1, '同じ。'), (1, '別の根拠。')]], True),
    ([[(1, '同じ。'), (2, 'さらに。'), (1, '同じ。')]], False),
    ([[(1, '同じ。')], [(1, '同じ。')]], True),
    ([[(1, '同じ。'), (1, '別の根拠。'), (2, '同じ。'), (2, 'さらに。')]], True),
    ([[(1, '同じ。'), (1, '別の根拠。'), (2, '同じ。'), (2, 'さらに。'), (2, 'さらに。')]], False),
    ([[(1, '同じ。'), (1, '別の根拠。'), (2, '同じ。'), (2, 'さらに。')], [(2, '同じ。'), (1, '同じ。')]], True),
]


def unique_evidence_document(rows):
    return json.dumps(dict(nodes=[dict(title='題', evidence=[dict(field=f, quote=q)
        for f, q in row]) for row in rows]), ensure_ascii=False, separators=(',', ':'))


def unique_evidence_parser():
    package = pytest.importorskip('lmformatenforcer')
    def pair(field, quotes):
        return dict(type='object', properties=dict(field=dict(type='integer', enum=[field]),
            quote=dict(type='string', enum=quotes)), required=['field', 'quote'], additionalProperties=False)
    evidence = dict(type='array', items=dict(oneOf=[pair(1, ['同じ。', '別の根拠。']),
        pair(2, ['同じ。', 'さらに。'])]), minItems=1, maxItems=24)
    node = dict(type='object', properties=dict(title=dict(type='string', minLength=1, maxLength=20),
        evidence=evidence), required=['title', 'evidence'], additionalProperties=False)
    schema = dict(type='object', properties=dict(nodes=dict(type='array', items=node,
        minItems=1, maxItems=24)), required=['nodes'], additionalProperties=False)
    alphabet = ''.join(dict.fromkeys(''.join(unique_evidence_document(rows)
        for rows, _ in UNIQUE_EVIDENCE_CASES) + 'P '))
    parser = probe._semantic_unique_json_schema_parser(schema,
        package.CharacterLevelParserConfig(alphabet=alphabet, force_json_field_order=True))
    return parser, alphabet


def unique_evidence_accept(parser, text):
    for char in text:
        if char not in parser.get_allowed_characters():
            return False
        parser = parser.add_character(char)
    return parser.can_end()


@pytest.mark.parametrize('rows,expected', UNIQUE_EVIDENCE_CASES)
def test_native_semantic_evidence_pairs_are_unique_per_node(rows, expected):
    parser, alphabet = unique_evidence_parser()
    assert unique_evidence_accept(parser, unique_evidence_document(rows)) == expected
    from lmformatenforcer.tokenenforcer import TokenEnforcer, TokenEnforcerTokenizerData
    vocabulary = list(alphabet)
    ids = {char: index for index, char in enumerate(vocabulary)}
    eos = len(vocabulary)
    data = TokenEnforcerTokenizerData([(i, char, False) for i, char in enumerate(vocabulary)],
        lambda tokens: ''.join(vocabulary[i] for i in tokens if i < eos), eos, False, eos + 1)
    enforcer = TokenEnforcer(data, unique_evidence_parser()[0])
    sent, accepted = [ids['P']], True
    for char in unique_evidence_document(rows):
        if ids[char] not in enforcer.get_allowed_tokens(sent).allowed_tokens:
            accepted = False
            break
        sent.append(ids[char])
    if accepted:
        accepted = eos in enforcer.get_allowed_tokens(sent).allowed_tokens
    assert accepted == expected


def test_native_semantic_evidence_branches_and_other_parsers_are_isolated():
    from lmformatenforcer import jsonschemaparser as upstream
    before = upstream.ListParsingState, upstream.ObjectParsingState, upstream.get_parser
    parser, _ = unique_evidence_parser()
    for char in '{"nodes":[{"title":"題","evidence":[':
        parser = parser.add_character(char)
    assert unique_evidence_accept(parser, '{"field":1,"quote":"同じ。"}]}]}')
    assert unique_evidence_accept(parser, '{"field":1,"quote":"別の根拠。"}]}]}')
    assert before == (upstream.ListParsingState, upstream.ObjectParsingState, upstream.get_parser)


GRAPH_CASES = [
    (['n1'], [], True),
    (['n1'], [('n1', 'n1')], False),
    (['n1'], [('n1', 'n2')], False),
    (['n1', 'n2'], [('n1', 'n2')], True),
    (['n1', 'n2'], [('n2', 'n1')], True),
    (['n1', 'n2'], [('n1', 'n1')], False),
    (['n1', 'n2'], [('n1', 'n14')], False),
    (['n1', 'n2'], [('n14', 'n2')], False),
    (['n1', 'n1'], [], False),
    (['n14', 'n2'], [('n14', 'n2')], False),
    (['n1', 'n2', 'n3'], [('n1', 'n3'), ('n2', 'n1')], True),
    (['n' + str(i) for i in range(1, 25)], [('n24', 'n1')], True),
    (['n' + str(i) for i in range(1, 25)] + ['n1'], [], False),
]


def graph_document(ids, edges):
    value = dict(schema_version='cocolon.analysis.semantic_map.model.v2',
        overview=dict(title='題', summary='要旨'), nodes=[dict(node_id=id,
            node_kind='SELF_POSITION', title='題', summary='要旨', explanation='説明',
            perspective='SELF', unknowns=[], evidence=[dict(quote='本人の記録です。', field=1)])
            for id in ids], edges=[dict(zip(('from', 'to', 'relation_kind', 'label', 'explanation'),
                (a, b, 'CONTEXT_CONTRAST', '比較', '説明'))) for a, b in edges])
    for node in value['nodes']:
        evidence = node.pop('evidence')
        node_fields = dict(node)
        node.clear()
        node.update(evidence=evidence, **node_fields)
    value = {key: value[key] for key in ('schema_version', 'nodes', 'edges', 'overview')}
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'))


def graph_parser():
    pytest.importorskip('lmformatenforcer')
    messages = [dict(role='system', content='synthetic'), dict(role='user',
        content=json.dumps(dict(fields=[dict(field=1, text='本人の記録です。補足です。'),
            dict(field=2, text='本人の記録です。別欄です。')]), ensure_ascii=False))]
    alphabet = ''.join(dict.fromkeys(''.join(graph_document(ids, edges)
        for ids, edges, _ in GRAPH_CASES) + 'P '))
    return probe.semantic_json_parser(messages, alphabet), alphabet, messages


@pytest.mark.parametrize('stage', ['LEAF', 'MERGE'])
def test_native_history_detail_budget_stops_repetition_without_changing_source(stage):
    pytest.importorskip('lmformatenforcer')
    original = '本人の記録です。補足です。'
    material = dict(fields=[dict(field=1, text=original)],
        history_stage=dict(kind=stage))
    messages = [dict(role='system', content='synthetic'), dict(role='user',
        content=json.dumps(material, ensure_ascii=False))]
    def document(length, *, source_first=True):
        value = json.loads(graph_document(['n1'], []))
        value['nodes'][0]['explanation'] = '説' * length
        if source_first:
            node = value['nodes'][0]
            value['nodes'][0] = dict(evidence=node.pop('evidence'), **node)
        return json.dumps(value, ensure_ascii=False, separators=(',', ':'))
    limit = 240 if stage == 'LEAF' else 420
    alphabet = ''.join(dict.fromkeys(document(421)))
    before = deepcopy(messages)
    assert unique_evidence_accept(probe.semantic_json_parser(messages, alphabet), document(limit))
    assert not unique_evidence_accept(probe.semantic_json_parser(messages, alphabet), document(limit + 1))
    ordinary = deepcopy(messages)
    ordinary[1]['content'] = json.dumps(dict(fields=material['fields']), ensure_ascii=False)
    assert unique_evidence_accept(probe.semantic_json_parser(ordinary, alphabet), document(3000, source_first=False))
    assert not unique_evidence_accept(probe.semantic_json_parser(ordinary, alphabet), document(3001, source_first=False))
    assert messages == before and json.loads(messages[1]['content'])['fields'][0]['text'] == original


@pytest.mark.parametrize('roots,expected', [([[1]], False), ([[1], [1]], False),
    ([[1], [2]], True), ([[2], [1]], True), ([[1, 2]], True),
    ([[1], [2], [1]], True), ([[1], [2, 1]], True), ([[1], [1, 2]], False),
    ([[1, 3]], False)])
@pytest.mark.parametrize('stage', ['LEAF', 'MERGE'])
def test_history_source_first_cannot_finish_before_each_quoted_record_is_represented(roots, expected, stage):
    pytest.importorskip('lmformatenforcer')
    fields = [dict(field=1, record=9, text='一つ目の原文。'),
        dict(field=2, record=37, text='もう一つの原文。'),
        dict(field=3, record=None, text='本人訂正。', record_refs=[9, 37])]
    packet = json.loads(graph_document([f'n{i}' for i in range(1, len(roots) + 1)], []))
    for node, numbers in zip(packet['nodes'], roots):
        node['evidence'] = [dict(quote=fields[n - 1]['text'], field=n) for n in numbers]
    # Rebuild insertion order: evidence is selected before any interpretation.
    packet['nodes'] = [dict(evidence=node['evidence'], **{k: v for k, v in node.items()
        if k != 'evidence'}) for node in packet['nodes']]
    text = json.dumps(packet, ensure_ascii=False, separators=(',', ':'))
    messages = [dict(role='system', content='synthetic'), dict(role='user',
        content=json.dumps(dict(fields=fields, history_stage=dict(kind=stage)), ensure_ascii=False))]
    if stage == 'LEAF' and len(roots) > 2:
        # Both records are covered, but a third node exceeds this leaf's
        # provisional reading budget. The final merge still allows it.
        expected = False
    alphabet = ''.join(dict.fromkeys(text + ''.join(f['text'] for f in fields)))
    assert unique_evidence_accept(probe.semantic_json_parser(messages, alphabet), text) == expected
    from lmformatenforcer.tokenenforcer import TokenEnforcer, TokenEnforcerTokenizerData
    vocabulary = list(alphabet) + ['P']
    ids = {char: index for index, char in enumerate(vocabulary)}
    eos = len(vocabulary)
    data = TokenEnforcerTokenizerData([(i, char, False) for i, char in enumerate(vocabulary)],
        lambda tokens: ''.join(vocabulary[i] for i in tokens if i < eos), eos, False, eos + 1)
    enforcer = TokenEnforcer(data, probe.semantic_json_parser(messages, alphabet))
    enforcer.root_parser.config.force_json_field_order = True
    sent, accepted = [ids['P']], True
    for char in text:
        if ids[char] not in enforcer.get_allowed_tokens(sent).allowed_tokens:
            accepted = False
            break
        sent.append(ids[char])
    if accepted:
        accepted = eos in enforcer.get_allowed_tokens(sent).allowed_tokens
    assert accepted == expected


@pytest.mark.parametrize('ids,edges,expected', GRAPH_CASES)
def test_native_semantic_graph_references_only_completed_distinct_nodes(ids, edges, expected):
    parser, alphabet, messages = graph_parser()
    original = deepcopy(messages), deepcopy(probe.semantic_output_schema(messages))
    text = graph_document(ids, edges)
    assert unique_evidence_accept(parser, text) == expected
    from lmformatenforcer.tokenenforcer import TokenEnforcer, TokenEnforcerTokenizerData
    vocabulary = list(alphabet) + ['[]', '[{']
    tokens = {char: i for i, char in enumerate(vocabulary)}
    eos = len(vocabulary)
    data = TokenEnforcerTokenizerData([(i, char, False) for i, char in enumerate(vocabulary)],
        lambda ids: ''.join(vocabulary[i] for i in ids if i < eos), eos, False, eos + 1)
    enforcer, sent, accepted = TokenEnforcer(data, graph_parser()[0]), [tokens['P']], True
    for char in text:
        if tokens[char] not in enforcer.get_allowed_tokens(sent).allowed_tokens:
            accepted = False
            break
        sent.append(tokens[char])
    if accepted:
        accepted = eos in enforcer.get_allowed_tokens(sent).allowed_tokens
    assert accepted == expected
    assert original == (messages, probe.semantic_output_schema(messages))


def test_native_semantic_graph_decoder_branches_do_not_share_node_ids():
    from lmformatenforcer import jsonschemaparser as upstream
    before = upstream.ListParsingState, upstream.ObjectParsingState, upstream.get_parser
    first = graph_document(['n1', 'n2'], [('n1', 'n2')])
    second = graph_document(['n1', 'n2', 'n3'], [('n1', 'n3')])
    invalid = graph_document(['n1', 'n2'], [('n1', 'n3')])
    split = first.index('},{"evidence":') + 2
    parser = graph_parser()[0]
    for char in first[:split]:
        assert char in parser.get_allowed_characters()
        parser = parser.add_character(char)
    assert unique_evidence_accept(parser, first[split:])
    assert unique_evidence_accept(parser, second[split:])
    assert not unique_evidence_accept(parser, invalid[split:])
    assert before == (upstream.ListParsingState, upstream.ObjectParsingState, upstream.get_parser)


EDGE_KINDS = ['SELF_OUTSIDE_GAP', 'CRITERION_EXPRESSION', 'CONTEXT_CONTRAST', 'SHARED_MEANING']
EDGE_UNIQUENESS_CASES = [
    (2, [], True),
    (2, [('n1', 'n2', 'CONTEXT_CONTRAST')], True),
    (2, [('n1', 'n2', 'CONTEXT_CONTRAST')] * 2, False),
    (2, [('n1', 'n2', 'CONTEXT_CONTRAST'), ('n2', 'n1', 'CONTEXT_CONTRAST')], False),
    (2, [('n1', 'n2', 'CONTEXT_CONTRAST'), ('n1', 'n2', 'SHARED_MEANING')], True),
    (2, [('n1', 'n2', 'CONTEXT_CONTRAST'), ('n2', 'n1', 'SHARED_MEANING')], True),
    (2, [('n1', 'n2', kind) for kind in EDGE_KINDS], True),
    (2, [('n1', 'n2', kind) for kind in EDGE_KINDS] + [('n2', 'n1', EDGE_KINDS[0])], False),
    (3, [('n1', 'n2', 'CONTEXT_CONTRAST'), ('n2', 'n3', 'CONTEXT_CONTRAST')], True),
    (3, [('n1', 'n2', kind) for kind in EDGE_KINDS]
        + [('n2', 'n1', 'SHARED_MEANING')], False),
    (3, [('n1', 'n2', kind) for kind in EDGE_KINDS]
        + [('n2', 'n3', 'SHARED_MEANING')], True),
    (3, [('n1', target, kind) for target in ['n2', 'n3'] for kind in EDGE_KINDS]
        + [('n1', 'n2', 'SHARED_MEANING')], False),
    (3, [('n1', target, kind) for target in ['n2', 'n3'] for kind in EDGE_KINDS]
        + [('n2', 'n3', 'SHARED_MEANING')], True),
]


def unique_edge_document(node_count, edges):
    packet = json.loads(graph_document([f'n{i}' for i in range(1, node_count + 1)], []))
    packet['edges'] = [dict(zip(('from', 'to', 'relation_kind', 'label', 'explanation'),
        (start, end, kind, '比較', '説明'))) for start, end, kind in edges]
    return json.dumps(packet, ensure_ascii=False, separators=(',', ':'))


def unique_edge_runtime(texts):
    from lmformatenforcer.tokenenforcer import TokenEnforcer, TokenEnforcerTokenizerData
    messages = graph_parser()[2]
    alphabet = ''.join(dict.fromkeys(''.join(texts) + 'P '))
    vocabulary = list(alphabet) + [',{', ']}', '"from":"n1"']
    ids = {value: index for index, value in enumerate(vocabulary)}
    eos = len(vocabulary)
    data = TokenEnforcerTokenizerData([(i, value, False) for i, value in enumerate(vocabulary)],
        lambda tokens: ''.join(vocabulary[i] for i in tokens if i < eos), eos, False, eos + 1)
    parser = probe.semantic_json_parser(messages, alphabet)
    enforcer = TokenEnforcer(data, parser)
    enforcer.root_parser.config.force_json_field_order = True
    return enforcer, ids, eos


def unique_edge_token_follow(enforcer, ids, sent, text):
    sent = list(sent)
    for char in text:
        if ids[char] not in enforcer.get_allowed_tokens(sent).allowed_tokens:
            return None
        sent.append(ids[char])
    return sent


@pytest.mark.parametrize('node_count,edges,expected', EDGE_UNIQUENESS_CASES)
def test_native_edges_match_unordered_pair_and_relation_uniqueness(node_count, edges, expected):
    pytest.importorskip('lmformatenforcer')
    text = unique_edge_document(node_count, edges)
    messages = graph_parser()[2]
    before = deepcopy(messages), deepcopy(probe.semantic_output_schema(messages))
    assert unique_evidence_accept(probe.semantic_json_parser(messages, text), text) == expected
    enforcer, ids, eos = unique_edge_runtime([text])
    sent = unique_edge_token_follow(enforcer, ids, [ids['P']], text)
    assert (sent is not None and eos in enforcer.get_allowed_tokens(sent).allowed_tokens) == expected
    assert before == (messages, probe.semantic_output_schema(messages))


def test_native_edges_can_close_early_and_must_close_after_all_pairs_are_used():
    pytest.importorskip('lmformatenforcer')
    empty = unique_edge_document(2, [])
    exhausted = unique_edge_document(2, [('n1', 'n2', kind) for kind in EDGE_KINDS])
    enforcer, ids, eos = unique_edge_runtime([empty, exhausted])
    sent = unique_edge_token_follow(enforcer, ids, [ids['P']], empty)
    assert sent is not None and eos in enforcer.get_allowed_tokens(sent).allowed_tokens
    parser = probe.semantic_json_parser(graph_parser()[2], exhausted)
    before_close = exhausted.rsplit('],"overview":', 1)[0]
    for char in before_close:
        assert char in parser.get_allowed_characters()
        parser = parser.add_character(char)
    assert ']' in parser.get_allowed_characters() and ',' not in parser.get_allowed_characters()
    sent = unique_edge_token_follow(enforcer, ids, [ids['P']], before_close)
    allowed = enforcer.get_allowed_tokens(sent).allowed_tokens
    assert ids[']'] in allowed and ids[','] not in allowed


def test_native_edge_keys_are_immutable_across_decoder_branches():
    pytest.importorskip('lmformatenforcer')
    first_edge = ('n1', 'n2', 'CONTEXT_CONTRAST')
    branch_a = unique_edge_document(3, [first_edge, ('n1', 'n3', 'SHARED_MEANING'),
        ('n1', 'n2', 'SHARED_MEANING')])
    branch_b = unique_edge_document(3, [first_edge, ('n2', 'n3', 'SHARED_MEANING'),
        ('n1', 'n3', 'SHARED_MEANING')])
    invalid = unique_edge_document(3, [first_edge, ('n2', 'n1', 'CONTEXT_CONTRAST')])
    split = branch_a.index(',{"from":"n1","to":"n3"') + 1
    parser = probe.semantic_json_parser(graph_parser()[2], branch_a + branch_b + invalid)
    for char in branch_a[:split]:
        assert char in parser.get_allowed_characters()
        parser = parser.add_character(char)
    assert unique_evidence_accept(parser, branch_a[split:])
    assert unique_evidence_accept(parser, branch_b[split:])
    assert not unique_evidence_accept(parser, invalid[split:])
    enforcer, ids, eos = unique_edge_runtime([branch_a, branch_b, invalid])
    common = unique_edge_token_follow(enforcer, ids, [ids['P']], branch_a[:split])
    for text, expected in [(branch_a, True), (branch_b, True), (invalid, False)]:
        sent = unique_edge_token_follow(enforcer, ids, common, text[split:])
        assert (sent is not None and eos in enforcer.get_allowed_tokens(sent).allowed_tokens) == expected


@pytest.mark.parametrize('evidence,expected', [
    ([('補足です。', 1)], True),
    ([('補足です。', 2)], False),
    ([('別欄です。', 1)], False),
    ([('別欄です。', 2)], True),
    ([('架空です。', 1)], False),
    ([('本人の記録です。', 1), ('本人の記録です。', 2)], True),
    ([('本人の記録です。', 1), ('本人の記録です。', 1)], False),
    ([('本人の記録です。', 1), ('補足です。', 1), ('本人の記録です。', 2), ('別欄です。', 2)], True),
    ([('本人の記録です。', 1), ('補足です。', 1), ('本人の記録です。', 2), ('別欄です。', 2),
      ('本人の記録です。補足です。', 1)], False),
])
def test_native_semantic_quote_first_binds_its_source_and_bounds_composition(evidence, expected):
    _, alphabet, messages = graph_parser()
    packet = json.loads(graph_document(['n1'], []))
    packet['nodes'][0]['evidence'] = [dict(quote=q, field=f) for q, f in evidence]
    text = json.dumps(packet, ensure_ascii=False, separators=(',', ':'))
    before = deepcopy(messages)
    parser = probe.semantic_json_parser(messages, alphabet + text)
    assert unique_evidence_accept(parser, text) == expected
    assert messages == before


RARE_CASES = [
    ([[(17, '鞄を置く。')]], True),
    ([[(18, '🪴を置いた。')]], True),
    ([[(17, '鞄を置く。'), (17, '鞄を置く。')]], False),
    ([[(17, '鞄を置く。'), (18, '鞄を置く。')]], True),
    ([[(17, '鞄を置く。'), (17, '鞄を移す。')]], True),
    ([[(17, '鞄を置く。')], [(17, '鞄を置く。')]], True),
    ([[(17, '🪴を置いた。')]], False),
    ([[(17, '鞄を消した。')]], False),
]


def rare_packet(rows):
    value = json.loads(graph_document(['n' + str(i) for i in range(1, len(rows) + 1)], []))
    for node, roots in zip(value['nodes'], rows):
        node['evidence'] = [dict(quote=q, field=f) for f, q in roots]
    return value


def rare_encoded(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':')).replace(
        '鞄', r'\u9784').replace('🪴', r'\ud83e\udeb4')


def rare_fixture():
    import string
    pytest.importorskip('lmformatenforcer')
    messages = [dict(role='system', content='synthetic'), dict(role='user', content=json.dumps(
        dict(fields=[dict(field=17, text='鞄を置く。鞄を移す。'),
            dict(field=18, text='鞄を置く。🪴を置いた。')]), ensure_ascii=False))]
    alphabet = ''.join(dict.fromkeys(''.join(rare_encoded(rare_packet(rows))
        for rows, _ in RARE_CASES) + string.printable + 'P '))
    assert '鞄' not in alphabet and '🪴' not in alphabet
    return messages, alphabet


@pytest.mark.parametrize('rows,expected', RARE_CASES)
def test_native_rare_unicode_quotes_keep_original_pairs_through_json_escapes(rows, expected):
    from lmformatenforcer.tokenenforcer import TokenEnforcer, TokenEnforcerTokenizerData
    messages, alphabet = rare_fixture()
    before = deepcopy(messages), deepcopy(probe.semantic_output_schema(messages))
    text = rare_encoded(rare_packet(rows))
    parser = probe.semantic_json_parser(messages, alphabet)
    assert unique_evidence_accept(parser, text) == expected
    if expected:
        assert json.loads(text) == rare_packet(rows)
    vocabulary = list(alphabet) + [r'\u9784', r'\ud83e', r'\udeb4', r'\ud83e\udeb4']
    ids = {value: i for i, value in enumerate(vocabulary)}
    eos = len(vocabulary)
    data = TokenEnforcerTokenizerData([(i, value, False) for i, value in enumerate(vocabulary)],
        lambda tokens: ''.join(vocabulary[i] for i in tokens if i < eos), eos, False, eos + 1)
    parser = probe.semantic_json_parser(messages, alphabet)
    enforcer = TokenEnforcer(data, parser)
    parser.config.force_json_field_order = True
    sent, accepted = [ids['P']], True
    for char in text:
        if ids[char] not in enforcer.get_allowed_tokens(sent).allowed_tokens:
            accepted = False
            break
        sent.append(ids[char])
    if accepted:
        accepted = eos in enforcer.get_allowed_tokens(sent).allowed_tokens
    assert accepted == expected
    assert before == (messages, probe.semantic_output_schema(messages))


def test_native_rare_unicode_field_branches_and_installed_parser_remain_isolated():
    from lmformatenforcer import jsonschemaparser as upstream
    before = upstream.StringParsingState, upstream.ListParsingState, upstream.ObjectParsingState
    messages, alphabet = rare_fixture()
    prefix = rare_encoded(rare_packet([[(17, '鞄を置く。')]])).split('"evidence":[')[0] + '"evidence":['
    parser = probe.semantic_json_parser(messages, alphabet)
    for char in prefix:
        assert char in parser.get_allowed_characters()
        parser = parser.add_character(char)
    for field, quote, expected in [(17, '鞄を置く。', True), (18, '鞄を置く。', True),
            (18, '鞄を移す。', False)]:
        branch = rare_encoded(rare_packet([[(field, quote)]]))
        assert branch.startswith(prefix)
        assert unique_evidence_accept(parser, branch[len(prefix):]) == expected
    assert before == (upstream.StringParsingState, upstream.ListParsingState, upstream.ObjectParsingState)


def test_upstream_constraint_exception_log_cannot_reveal_source_or_generated_prefix():
    record = logging.LogRecord('root', logging.ERROR, '/vendor/lmformatenforcer/tokenenforcer.py',
        130, 'Prefix: %s', ('SYNTHETIC_PRIVATE_SOURCE',),
        (ValueError, ValueError('SYNTHETIC_PRIVATE_SOURCE'), None), sinfo='SYNTHETIC_PRIVATE_SOURCE')
    record.exc_text = 'SYNTHETIC_PRIVATE_SOURCE'
    assert probe.SourcePrivateConstraintLog().filter(record)
    assert record.getMessage() == 'analysis_generation_constraint_internal_error'
    assert record.exc_info is record.exc_text is record.stack_info is None


@pytest.mark.parametrize('key,expected', [(('json_freetext', 0, 1, 80), [3]),
    (None, [1, 2, 3])])
def test_blank_and_raw_control_tokens_are_excluded_only_from_free_prose(key, expected):
    class Sent:
        def tolist(self):
            return [90]
    class Prefix:
        token_enforcer = SimpleNamespace(prefix_states={(90,): SimpleNamespace(
            parser=SimpleNamespace(shortcut_key=lambda: key))})
        def __call__(self, batch, sent):
            return [1, 2, 3]
    assert probe.semantic_free_text_tokens(Prefix(), 0, Sent(), {1, 2}) == expected


def test_raw_control_tokens_are_excluded_also_when_upstream_is_in_a_union_or_escape_state():
    class Sent:
        def tolist(self):
            return [90]
    class Prefix:
        token_enforcer = SimpleNamespace(prefix_states={(90,): SimpleNamespace(
            parser=SimpleNamespace(shortcut_key=lambda: None))})
        def __call__(self, batch, sent):
            return [1, 2, 3]
    assert probe.semantic_free_text_tokens(Prefix(), 0, Sent(), {1, 2}, {1}) == [2, 3]


def runtime_token_filters(tokenizer_data, profile=None):
    """Run the actual startup/profile assignments without loading a model."""
    function = ast.parse(inspect.getsource(probe.load_generator)).body[0]
    startup = next(node for node in function.body if isinstance(node, ast.If)
        and isinstance(node.test, ast.Name) and node.test.id == 'semantic_json')
    names = {'blocked_free_text', 'invalid_json_tokens', 'tokenizer_alphabet',
        'unsupported_unicode_tokens', 'profile_invalid_json_tokens'}
    assignments = [node for node in startup.body if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id in names for target in node.targets)]
    assignments.append(next(node for node in ast.walk(function) if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == 'profile_invalid_json_tokens'
            for target in node.targets)))
    namespace = dict(tokenizer_data=tokenizer_data, profile=profile)
    exec(compile(ast.fix_missing_locations(ast.Module(body=assignments, type_ignores=[])),
        '<native-token-filter-assignments>', 'exec'), namespace)
    return namespace['blocked_free_text'], namespace['profile_invalid_json_tokens']


def unicode_prose_runtime(rare, owner='analysis'):
    """Synthetic byte segmentation, not a reconstruction of model token IDs."""
    from lmformatenforcer.tokenenforcer import TokenEnforcer, TokenEnforcerTokenizerData
    if owner == 'analysis':
        packet = json.loads(graph_document(['n1'], []))
        packet['nodes'][0].update(explanation=rare + 'を置く。',
            evidence=[dict(quote=rare + 'を置く。', field=1)])
        material = dict(fields=[dict(field=1, text=rare + 'を置く。')])
        marker = '"explanation":"'
    else:
        packet = dict(schema_version=probe.IF_CANDIDATE_SCHEMA, scenarios=[],
            clarification=dict(reason_code='BRANCH_INTENT_UNCLEAR', prompt=rare + 'を置く。'))
        material = dict(model_schema=probe.IF_CANDIDATE_SCHEMA,
            base_map_kind='DERIVED_AI_MAP_ANCHOR', branch_point_ref='branch',
            anchors=[dict(node_ref='anchor', visible_label=rare + 'を置く。')],
            fields=[dict(field=1, source_role='SIMULATION_SESSION_MATERIAL',
                purpose='BRANCH_INTENT', text='試す。')], requested_candidate_count=1,
            constraints_confirmed=False)
        marker = '"prompt":"'
    escaped = json.dumps(rare, ensure_ascii=True)[1:-1]
    text = json.dumps(packet, ensure_ascii=False, separators=(',', ':')).replace(
        '"quote":"' + rare, '"quote":"' + escaped)
    head, tail = text.split(marker)
    beginning = head + marker
    alphabet = ''.join(dict.fromkeys(beginning + tail.replace(rare, '') + string.printable + '\ufffd'))
    vocabulary = list(alphabet) + ['\ufffd', '\ufffd', 'て' + rare, ':"\ufffd', ':"' + rare]
    first, last, composite, crossing, crossing_raw = range(len(vocabulary) - 5, len(vocabulary))
    eos = len(vocabulary)
    ids = {char: i for i, char in enumerate(alphabet)}

    def decoder(tokens):
        decoded, i = [], 0
        while i < len(tokens):
            token = tokens[i]
            if token in (first, crossing) and i + 1 < len(tokens) and tokens[i + 1] == last:
                decoded.append((':' + '"' if token == crossing else '') + rare)
                i += 2
            else:
                if token < eos:
                    decoded.append(vocabulary[token])
                i += 1
        # Same trailing replacement cleanup as the pinned Transformers integration.
        return ''.join(decoded).rstrip('\ufffd')

    data = TokenEnforcerTokenizerData([(i, value, False) for i, value in enumerate(vocabulary)],
        decoder, eos, False, eos + 1)
    assert rare == '\ufffd' or rare not in data.tokenizer_alphabet
    messages = [dict(role='system', content='synthetic'), dict(role='user',
        content=json.dumps(material, ensure_ascii=False))]
    parser = probe.semantic_json_parser(messages, data.tokenizer_alphabet)
    enforcer = TokenEnforcer(data, parser)
    enforcer.root_parser.config.force_json_field_order = True
    class Sent(list):
        def tolist(self):
            return list(self)
    class Prefix:
        token_enforcer = enforcer
        def __call__(self, batch, sent):
            return self.token_enforcer.get_allowed_tokens(sent.tolist()).allowed_tokens
    prefix = Prefix()
    blocked, invalid = runtime_token_filters(data)
    def follow(sent, characters):
        branch = Sent(sent)
        for char in characters:
            assert ids[char] in probe.semantic_free_text_tokens(prefix, 0, branch, blocked, invalid)
            branch.append(ids[char])
        prefix(0, branch)
        return branch
    return SimpleNamespace(packet=packet, data=data, enforcer=enforcer, prefix=prefix,
        sent=Sent([ids['P']]), follow=follow, beginning=beginning, tail=tail,
        escaped=escaped, first=first, last=last, composite=composite, crossing=crossing,
        crossing_raw=crossing_raw, blocked=blocked, invalid=invalid, eos=eos, decoder=decoder)


@pytest.mark.parametrize('owner', ['analysis', 'if'])
@pytest.mark.parametrize('rare', ['鞄', '🪴'])
def test_native_unicode_protocol_tokens_cannot_empty_an_open_json_parser(rare, owner):
    pytest.importorskip('lmformatenforcer')
    runtime = unicode_prose_runtime(rare, owner)
    sent = runtime.follow(runtime.sent, runtime.beginning)
    assert runtime.enforcer.prefix_states[tuple(sent)].parser.shortcut_key()[0] == 'json_freetext'
    raw_allowed = runtime.prefix(0, sent)
    assert {runtime.first, runtime.composite}.issubset(raw_allowed)
    filtered = probe.semantic_free_text_tokens(runtime.prefix, 0, sent, runtime.blocked, runtime.invalid)
    assert not {runtime.first, runtime.last, runtime.composite}.intersection(filtered)
    # Both uncontrolled paths reproduce LMFE's empty-stack/premature-EOS failure.
    for tokens in ([runtime.first, runtime.last], [runtime.composite]):
        branch = type(sent)(sent)
        for token in tokens:
            assert token in runtime.prefix(0, branch)
            branch.append(token)
        assert runtime.eos in runtime.prefix(0, branch)
        assert runtime.enforcer.prefix_states[tuple(branch)].parser.object_stack == []
    # A token can start outside prose and end with a partial UTF-8 character.
    before = runtime.follow(runtime.sent, runtime.beginning[:-2])
    assert runtime.enforcer.prefix_states[tuple(before)].parser.shortcut_key() is None
    assert runtime.crossing in runtime.prefix(0, before)
    assert runtime.crossing_raw not in runtime.prefix(0, before)
    assert runtime.crossing not in probe.semantic_free_text_tokens(
        runtime.prefix, 0, before, runtime.blocked, runtime.invalid)
    _, piece_invalid = runtime_token_filters(runtime.data, 'piece')
    assert runtime.crossing in probe.semantic_free_text_tokens(
        runtime.prefix, 0, before, set(), piece_invalid)
    # The same immutable prefix still closes legally through JSON Unicode escapes.
    complete = runtime.follow(sent, runtime.escaped + runtime.tail[len(rare):])
    assert runtime.eos in runtime.prefix(0, complete)
    assert json.loads(runtime.decoder(complete[1:])) == runtime.packet


@pytest.mark.parametrize('owner', ['analysis', 'if'])
def test_native_literal_source_replacement_character_is_preserved_by_json_escape(owner):
    pytest.importorskip('lmformatenforcer')
    import lmformatenforcer as package
    source = '\ufffdを置く。'
    alphabet = string.printable + 'を置く。\ufffd'
    schema = dict(type='object', properties=dict(text=dict(type='string', enum=[source])),
        required=['text'], additionalProperties=False)
    make_parser = (probe._semantic_unique_json_schema_parser if owner == 'analysis'
        else probe._if_json_schema_parser)
    parser = make_parser(schema, package.CharacterLevelParserConfig(
        alphabet=alphabet, force_json_field_order=True))
    text = r'{"text":"\ufffdを置く。"}'
    assert unique_evidence_accept(parser, text)
    assert not unique_evidence_accept(parser, json.dumps(dict(text=source), ensure_ascii=False,
        separators=(',', ':')))
    assert json.loads(text)['text'] == source
    runtime = unicode_prose_runtime('\ufffd', owner)
    before = deepcopy(runtime.packet)
    sent = runtime.follow(runtime.sent, runtime.beginning)
    complete = runtime.follow(sent, runtime.escaped + runtime.tail[1:])
    assert runtime.eos in runtime.prefix(0, complete)
    assert json.loads(runtime.decoder(complete[1:])) == before


def test_actual_pinned_parser_empty_decoder_root_loop_is_removed_before_generation():
    package = pytest.importorskip('lmformatenforcer')
    from lmformatenforcer.tokenenforcer import TokenEnforcer, TokenEnforcerTokenizerData
    vocabulary = ['P', '', '{', '}']
    data = TokenEnforcerTokenizerData([(index, char, False) for index, char in enumerate(vocabulary)],
        lambda tokens: ''.join(vocabulary[index] for index in tokens), 4, False, 5)
    class Sent(list):
        def tolist(self):
            return list(self)
    class Prefix:
        token_enforcer = TokenEnforcer(data, package.JsonSchemaParser(dict(type='object',
            properties={}, additionalProperties=False)))
        def __call__(self, batch, sent):
            return self.token_enforcer.get_allowed_tokens(sent.tolist()).allowed_tokens
    prefix, sent = Prefix(), Sent([0])
    assert 1 in prefix(0, sent)  # Empty token is in upstream root.tokens.
    allowed = probe.semantic_free_text_tokens(prefix, 0, sent, {1}, {1})
    assert 1 not in allowed and 2 in allowed


def test_runtime_parser_initializes_unicode_before_context_and_does_not_end_on_first_japanese():
    package = pytest.importorskip('lmformatenforcer')
    from lmformatenforcer.tokenenforcer import TokenEnforcer, TokenEnforcerTokenizerData
    messages = [{'role': 'system', 'content': 'synthetic'}, {'role': 'user',
        'content': json.dumps({'fields': [{'field': 1, 'text': 'source'}]}, ensure_ascii=False)}]
    packet = json.loads(graph_document(['n1'], []))
    packet['nodes'][0].update(title='部屋を整えた。', evidence=[dict(quote='source', field=1)])
    beginning = json.dumps(packet, ensure_ascii=False, separators=(',', ':')).split(
        '"title":"', 1)[0] + '"title":"部屋'
    alphabet = ''.join(dict.fromkeys(beginning + 'を整えた。P'))
    data = TokenEnforcerTokenizerData([(index, char, False) for index, char in enumerate(alphabet)],
        lambda tokens: ''.join(alphabet[index] for index in tokens), len(alphabet), False, len(alphabet) + 1)
    old = package.JsonSchemaParser(probe.semantic_output_schema(messages))
    TokenEnforcer(data, old)  # The upstream late config replacement.
    new = probe.semantic_json_parser(messages, data.tokenizer_alphabet)
    for char in beginning:
        old = old.add_character(char)
        assert char in new.get_allowed_characters()
        new = new.add_character(char)
    assert old.can_end()  # Reproduces the observed premature completion.
    assert not new.can_end() and new.object_stack
    assert new.shortcut_key()[0] == 'json_freetext'


def test_actual_pinned_parser_blank_prose_is_filtered_and_literal_quote_space_is_preserved():
    package = pytest.importorskip('lmformatenforcer')
    from lmformatenforcer.tokenenforcer import TokenEnforcer, TokenEnforcerTokenizerData
    characters = list(dict.fromkeys('P{"text":}私 の希望\t\n'))
    ids = {char: index for index, char in enumerate(characters)}
    data = TokenEnforcerTokenizerData([(index, char, False) for index, char in enumerate(characters)],
        lambda tokens: ''.join(characters[index] for index in tokens), len(characters), False, len(characters) + 1)
    class Sent(list):
        def tolist(self):
            return list(self)
    class Prefix:
        def __call__(self, batch, sent):
            return self.token_enforcer.get_allowed_tokens(sent.tolist()).allowed_tokens
    blocked = {ids[char] for char in (' ', '\t', '\n')}
    def at_string_start(string_schema):
        prefix = Prefix()
        prefix.token_enforcer = TokenEnforcer(data, package.JsonSchemaParser(dict(type='object',
            properties=dict(text=string_schema), required=['text'], additionalProperties=False)))
        sent = Sent([ids['P']])
        prefix(0, sent)
        for char in '{"text":"':
            sent.append(ids[char])
            prefix(0, sent)
        return prefix, sent
    prefix, sent = at_string_start(dict(type='string', minLength=1, maxLength=80))
    assert ids['\t'] in prefix(0, sent)  # Reproduces the upstream free-text path.
    filtered = probe.semantic_free_text_tokens(prefix, 0, sent, blocked)
    assert ids['私'] in filtered and not blocked.intersection(filtered)
    prefix, sent = at_string_start(dict(type='string', enum=['私 の希望']))
    sent.append(ids['私'])
    assert ids[' '] in probe.semantic_free_text_tokens(prefix, 0, sent, blocked)


def evidence_schema(schema):
    return schema['properties']['nodes']['items']['properties']['evidence']['items']


def allowed(schema, packet):
    package = pytest.importorskip('lmformatenforcer')
    encoded = json.dumps(packet, ensure_ascii=False)
    # These cases check the receiver's key-order-independent JSON schema.
    # Native decoding order is exercised separately with its actual enforcer.
    config = package.CharacterLevelParserConfig(force_json_field_order=False)
    config.alphabet += encoded  # The real token enforcer supplies tokenizer Unicode.
    parser = package.JsonSchemaParser(schema, config=config)
    for char in encoded:
        if char not in parser.get_allowed_characters():
            return False
        parser = parser.add_character(char)
    return parser.can_end()


def test_evidence_field_and_literal_are_one_pair_and_cannot_cross():
    schema = evidence_schema(schema_for([{'field': 1, 'text': '自分で選びたい。'},
        {'field': 2, 'text': 'その場では話さなかった。'}]))
    assert allowed(schema, {'field': 1, 'quote': '自分で選びたい。'})
    assert allowed(schema, {'field': 2, 'quote': 'その場では話さなかった。'})
    assert not allowed(schema, {'field': 1, 'quote': 'その場では話さなかった。'})
    assert not allowed(schema, {'field': 99, 'quote': '自分で選びたい。'})
    assert not allowed(schema, {'field': 1, 'quote': '自分で選びたくない。'})


def test_paragraph_can_quote_a_unique_sentence_without_replacing_its_context():
    original = '私は参加した。というわけではありません。費用が整えば、進めたい。'
    fields = [{'field': 1, 'text': original}, {'field': 2, 'text': '別の内容を記録した。'}]
    before = deepcopy(fields)
    schema = evidence_schema(schema_for(fields))
    assert fields == before
    assert allowed(schema, {'field': 1, 'quote': original})
    assert allowed(schema, {'field': 1, 'quote': 'というわけではありません。'})
    assert allowed(schema, {'field': 1, 'quote': '費用が整えば、進めたい。'})
    assert not allowed(schema, {'field': 2, 'quote': '費用が整えば、進めたい。'})
    assert not allowed(schema, {'field': 1, 'quote': '費用が整ったので、進めた。'})
    # A quote option is not a declaration of semantic independence. The full
    # denial/condition stays in the source for the unchanged CMEE checks.


@pytest.mark.parametrize('original', [
    '「行った。『良かった！』」とは言わなかった。実際は不参加だった。',
    '同じ文です。同じ文です。別の内容です。',
    'URLはhttps://example.test/a.b。値は1.25です。',
])
def test_additional_sentence_quotes_preserve_nesting_uniqueness_and_ascii_periods(original):
    schema = evidence_schema(schema_for([{'field': 1, 'text': original}]))
    quotes = schema['oneOf'][0]['properties']['quote']['enum']
    assert all(original.count(quote) == 1 for quote in quotes)
    if original.startswith('「'):
        assert '「行った。『良かった！』」とは言わなかった。' in quotes
        assert '行った。' not in quotes and '良かった！' not in quotes
    elif original.startswith('同じ'):
        assert '同じ文です。' not in quotes and '別の内容です。' in quotes
    else:
        assert 'URLはhttps://example.test/a.b。' in quotes
        assert '値は1.25です。' in quotes
    assert all(allowed(schema, {'field': 1, 'quote': quote}) for quote in quotes)


@pytest.mark.parametrize('original', ['先の文です。「閉じない。次の文です。',
    '先の文です。『組が違う」。次の文です。'])
def test_unbalanced_quotes_only_keep_the_legacy_full_candidate(original):
    schema = evidence_schema(schema_for([{'field': 1, 'text': original}]))
    assert schema['oneOf'][0]['properties']['quote']['enum'] == [original]


def test_map_correction_still_requires_its_complete_explanation():
    original = 'その意味ではありません。今回の条件を伝えたいです。'
    schema = evidence_schema(schema_for([{'field': 7, 'text': original,
        'source_role': 'USER_ANALYSIS_MAP_CORRECTION'}]))
    assert allowed(schema, {'field': 7, 'quote': original})
    assert not allowed(schema, {'field': 7, 'quote': 'その意味ではありません。'})


def test_new_sentences_do_not_join_across_escaped_source_fragments():
    original = 'まず"引用した。続き"です。C:\\tmpです。別の文です。'
    quotes = evidence_schema(schema_for([{'field': 1, 'text': original}]))['oneOf'][0]['properties']['quote']['enum']
    assert '別の文です。' in quotes
    assert 'まず引用した。' not in quotes and 'C:tmpです。' not in quotes
    assert all(original.count(quote) == 1 and '"' not in quote and '\\' not in quote for quote in quotes)


@pytest.mark.parametrize('original', ['日本語の"引用"', r'C:\tmp\file', '一行目\r\n二行目',
    '前半\t後半', 'あ' * 3999 + 'イ' + 'あ' * 3999 + 'ウ'])
def test_escaped_or_long_source_remains_complete_and_quotes_are_real_unique_substrings(original):
    fields = [{'field': 1, 'text': original}]
    before = deepcopy(fields)
    evidence = evidence_schema(schema_for(fields))
    assert fields == before
    for branch in evidence['oneOf']:
        for quote in branch['properties']['quote']['enum']:
            assert len(quote) <= 4000 and original.count(quote) == 1
            assert allowed(evidence, {'field': 1, 'quote': quote})
            assert json.loads(json.dumps(quote, ensure_ascii=False)) == quote


@pytest.mark.parametrize('field', [{'field': True, 'text': '本人の記録'},
    {'field': '1', 'text': '本人の記録'}, {'field': 1, 'text': ''}])
def test_invalid_identity_or_no_literal_does_not_get_an_invented_quote(field):
    with pytest.raises(ValueError):
        schema_for([field])


def test_semantic_constraints_cannot_be_enabled_for_the_existing_emlis_probe(monkeypatch):
    monkeypatch.setattr(sys, 'argv',
        ['serve', '--model-name', 'synthetic', '--semantic-json', '--max-requests', '1', '--seconds', '1'])
    with pytest.raises(SystemExit):
        probe.main()


def test_a_source_constrained_complete_map_is_still_admitted_by_the_same_cmee():
    import analysis_semantic_map as semantic
    from test_analysis_semantic_map import sample, candidate, response, OWNER
    prepared = semantic.prepare_semantic_map(OWNER, sample())
    original_messages = deepcopy(prepared.messages())
    material = json.loads(original_messages[1]['content'])
    fields = {field['field']: field['text'] for field in material['fields']}
    packet = candidate()
    for node in packet['nodes']:
        for root in node['evidence']:
            root['quote'] = fields[root['field']].strip()
    assert allowed(probe.semantic_output_schema(original_messages), packet)
    artifact, _ = semantic.build_semantic_map(prepared, response(prepared, packet))
    assert artifact.safe_projection(authenticated_owner_scope=OWNER)['wire_kind'] == 'watashi.map.v3'
    assert prepared.messages() == original_messages


def test_sentence_evidence_passes_existing_cmee_with_the_complete_source_unchanged():
    import analysis_semantic_map as semantic
    from test_analysis_semantic_map import sample, candidate, response, OWNER
    prepared = semantic.prepare_semantic_map(OWNER, sample())
    before = deepcopy(prepared.messages()), prepared.source_guard
    fields = {field['field']: field['text']
        for field in json.loads(prepared.messages()[1]['content'])['fields']}
    packet = candidate()
    for node in packet['nodes']:
        for root in node['evidence']:
            text = fields[root['field']]
            root['quote'] = text if root['field'] == 1 else (
                text.split('。')[0] + '。' if root['field'] == 2 else '私は意見を言わなかった。')
    assert allowed(probe.semantic_output_schema(prepared.messages()), packet)
    artifact, _ = semantic.build_semantic_map(prepared, response(prepared, packet))
    assert artifact.safe_projection(authenticated_owner_scope=OWNER)['wire_kind'] == 'watashi.map.v3'
    assert (prepared.messages(), prepared.source_guard) == before


def compact_leaf_wire(fields, groups, *, stage='LEAF', quotes=None, edges=()):
    messages = [dict(role='system', content='synthetic'), dict(role='user',
        content=json.dumps(dict(fields=fields, history_stage=dict(kind=stage)), ensure_ascii=False))]
    packet = json.loads(graph_document([f'n{i}' for i in range(1, len(groups) + 1)], []))
    originals = {field['field']: field['text'] for field in fields}
    for node, numbers in zip(packet['nodes'], groups):
        node['evidence'] = [dict(quote=(quotes or {}).get(number, originals[number]), field=number)
            for number in numbers]
    packet['nodes'] = [dict(evidence=node['evidence'], **{key: value for key, value in node.items()
        if key != 'evidence'}) for node in packet['nodes']]
    packet['edges'] = [dict(zip(('from', 'to', 'relation_kind', 'label', 'explanation'),
        (start, end, 'CONTEXT_CONTRAST', '比較', '説明'))) for start, end in edges]
    text = json.dumps(packet, ensure_ascii=False, separators=(',', ':'))
    return messages, text


def assert_compact_leaf_native(messages, text, expected):
    pytest.importorskip('lmformatenforcer')
    from lmformatenforcer.tokenenforcer import TokenEnforcer, TokenEnforcerTokenizerData
    before = deepcopy(messages), deepcopy(probe.semantic_output_schema(messages))
    alphabet = ''.join(dict.fromkeys(text + 'P '))
    assert unique_evidence_accept(probe.semantic_json_parser(messages, alphabet), text) == expected
    vocabulary = list(alphabet) + ['[]', ']}']
    ids = {value: index for index, value in enumerate(vocabulary)}
    eos = len(vocabulary)
    data = TokenEnforcerTokenizerData([(i, value, False) for i, value in enumerate(vocabulary)],
        lambda tokens: ''.join(vocabulary[i] for i in tokens if i < eos), eos, False, eos + 1)
    enforcer = TokenEnforcer(data, probe.semantic_json_parser(messages, alphabet))
    enforcer.root_parser.config.force_json_field_order = True
    sent = unique_edge_token_follow(enforcer, ids, [ids['P']], text)
    assert (sent is not None and eos in enforcer.get_allowed_tokens(sent).allowed_tokens) == expected
    assert before == (messages, probe.semantic_output_schema(messages))


@pytest.mark.parametrize('groups,expected', [([[1]], True), ([[1], [1]], True),
    ([[1], [1], [1]], False), ([[1, 2]], True), ([[1, 2, 3]], False)])
def test_compact_leaf_allows_two_meanings_for_one_record_and_two_roots_per_node(groups, expected):
    fields = [dict(field=i, record=37, text=f'原文{i}。') for i in range(1, 4)]
    messages, text = compact_leaf_wire(fields, groups)
    schema = probe.semantic_output_schema(messages)
    assert schema['properties']['nodes']['maxItems'] == 2
    assert_compact_leaf_native(messages, text, expected)


@pytest.mark.parametrize('groups,expected', [([[1], [2], [3]], True),
    ([[1, 2], [3]], True), ([[1]], False)])
def test_compact_leaf_keeps_distinct_record_coverage_without_fixed_final_node_assignment(groups, expected):
    fields = [dict(field=i, record=i * 37, text=f'別記録{i}。') for i in range(1, 4)]
    messages, text = compact_leaf_wire(fields, groups)
    assert probe.semantic_output_schema(messages)['properties']['nodes']['maxItems'] == 3
    assert_compact_leaf_native(messages, text, expected)


@pytest.mark.parametrize('stage,expected', [('LEAF', False), ('MERGE', True)])
def test_only_provisional_leaves_omit_edges(stage, expected):
    fields = [dict(field=i, record=i, text=f'別記録{i}。') for i in range(1, 3)]
    messages, text = compact_leaf_wire(fields, [[1], [2]], stage=stage, edges=[('n1', 'n2')])
    assert_compact_leaf_native(messages, text, expected)


def test_compact_leaf_reserves_capacity_for_eight_whole_map_corrections():
    fields = [dict(field=1, record=37, text='本人の原記録。')]
    fields += [dict(field=i + 2, record=None, record_refs=[37],
        source_role='USER_ANALYSIS_MAP_CORRECTION', text=f'訂正{i}。' + '長い本人説明' * 30 + '。')
        for i in range(8)]
    messages, text = compact_leaf_wire(fields, [[1, 2], [3, 4], [5, 6], [7, 8], [9]])
    schema = probe.semantic_output_schema(messages)
    assert schema['properties']['nodes']['maxItems'] == 5  # ceil((1 + 8) / 2)
    pairs = evidence_schema(schema)['oneOf']
    by_field = {part['properties']['field']['enum'][0]: part['properties']['quote']['enum'] for part in pairs}
    assert all(by_field[field['field']] == [field['text']] for field in fields[1:])
    assert_compact_leaf_native(messages, text, True)
    shortened = json.loads(text)
    shortened['nodes'][0]['evidence'][1]['quote'] = fields[1]['text'][:160]
    assert_compact_leaf_native(messages,
        json.dumps(shortened, ensure_ascii=False, separators=(',', ':')), False)


def test_compact_leaf_record_none_corrections_do_not_invent_record_counts():
    fields = [dict(field=i + 1, record=None, record_refs=[9, 37],
        source_role='USER_ANALYSIS_MAP_CORRECTION', text=f'本人訂正{i}。') for i in range(8)]
    messages, text = compact_leaf_wire(fields, [[1, 2], [3, 4], [5, 6], [7, 8]])
    assert probe.semantic_output_schema(messages)['properties']['nodes']['maxItems'] == 4
    assert_compact_leaf_native(messages, text, True)


@pytest.mark.parametrize('original,expected_quotes', [
    ('長' * 180 + '。短い根拠。', ['短い根拠。']),
    ('長' * 180 + '。', ['長' * 180 + '。']),
])
def test_compact_leaf_selects_real_short_sentences_or_retains_legal_long_fallback(original, expected_quotes):
    fields = [dict(field=17, record=37, text=original)]
    messages, text = compact_leaf_wire(fields, [[17]], quotes={17: expected_quotes[0]})
    before = deepcopy(messages)
    quotes = evidence_schema(probe.semantic_output_schema(messages))['oneOf'][0]['properties']['quote']['enum']
    assert quotes == expected_quotes and all(original.count(quote) == 1 for quote in quotes)
    assert_compact_leaf_native(messages, text, True)
    assert messages == before and json.loads(messages[1]['content'])['fields'][0]['text'] == original


def test_compact_leaf_preserves_existing_partial_coverage_above_twenty_four_records():
    fields = [dict(field=i, record=i * 37, text=f'原記録{i}。') for i in range(1, 26)]
    messages, text = compact_leaf_wire(fields, [[1]])
    assert probe.semantic_output_schema(messages)['properties']['nodes']['maxItems'] == 24
    assert_compact_leaf_native(messages, text, True)


@pytest.mark.parametrize('stage,title,summary,explanation,unknown,overview,roots,edges', [
    (None, 80, 400, 3000, 500, 2000, 4, 48),
    ('MERGE', 60, 160, 420, 240, 480, 4, 48),
    ('LEAF', 36, 100, 240, 160, 160, 2, 0),
])
def test_generation_budgets_preserve_ordinary_and_history_profiles(
        stage, title, summary, explanation, unknown, overview, roots, edges):
    fields = [dict(field=17, record=37, text='長' * 180 + '。短い根拠。')]
    material = dict(fields=fields)
    if stage is not None:
        material['history_stage'] = dict(kind=stage)
    messages = [dict(role='system', content='synthetic'), dict(role='user',
        content=json.dumps(material, ensure_ascii=False))]
    before = deepcopy(messages)
    schema = probe.semantic_output_schema(messages)
    node = schema['properties']['nodes']['items']['properties']
    assert (node['title']['maxLength'], node['summary']['maxLength'], node['explanation']['maxLength'],
        node['unknowns']['items']['maxLength']) == (title, summary, explanation, unknown)
    assert schema['properties']['overview']['properties']['summary']['maxLength'] == overview
    assert node['evidence']['maxItems'] == roots and schema['properties']['edges']['maxItems'] == edges
    quotes = evidence_schema(schema)['oneOf'][0]['properties']['quote']['enum']
    if stage == 'LEAF':
        assert quotes == ['短い根拠。']
        assert schema['properties']['nodes']['maxItems'] == 2
    else:
        assert fields[0]['text'] in quotes and '長' * 180 + '。' in quotes
        assert schema['properties']['nodes']['maxItems'] == 24
    assert messages == before


@pytest.mark.parametrize('stage,expected_sha256,prior_sha256', [
    (None, '87f4da00e006085117d293e52878d3ca422a2d609d21050e1eb3d7b6bcbb92ee',
        'ecb0919848b64b7369c28dc97cbe9342621b5b4d742249f401f2241fd6e11e29'),
    ('LEAF', '45fee182cd6fdaad2d82144593f9c7b2735d95c9c70c0cdc2a221f44df5197b3',
        '05849d591f871e08795e351802ded921c32b1911b3c63d56bdc6d283afe4c6cc'),
    ('MERGE', 'cbb785e9355b6e2b8fa262f8cfacbeab0647c34eec2d465dc8d3ab304c1a45b2',
        'f1125f1997f2403f2bc40929528951a062379ff95b46bff52c21b93f05851ebb'),
])
def test_schema_sequence_changes_only_order_not_source_options_or_capacity(stage, expected_sha256, prior_sha256):
    # Pin the new decoding order and compare all other schema bytes against
    # the original grammar, including long input and a whole map correction.
    fields = [dict(field=1, record=9, text='長' * 180 + '。短い根拠。'),
        dict(field=2, record=37, text='別の原文。'),
        dict(field=3, record=None, record_refs=[9, 37],
            source_role='USER_ANALYSIS_MAP_CORRECTION',
            text='その意味ではありません。' + '本人説明' * 60 + '。')]
    material = dict(fields=fields)
    if stage is not None:
        material['history_stage'] = dict(kind=stage)
    messages = [dict(role='system', content='synthetic'), dict(role='user',
        content=json.dumps(material, ensure_ascii=False))]
    schema = probe.semantic_output_schema(messages)
    raw = json.dumps(schema, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
    assert hashlib.sha256(raw).hexdigest() == expected_sha256
    schema['required'] = ['schema_version', 'overview', 'nodes', 'edges']
    if stage is None:
        schema['properties']['nodes']['items']['required'] = ['node_id', 'node_kind', 'title',
            'summary', 'explanation', 'perspective', 'unknowns', 'evidence']
    prior_raw = json.dumps(schema, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
    assert hashlib.sha256(prior_raw).hexdigest() == prior_sha256


@pytest.mark.parametrize('fields,nodes,edges', [
    ([dict(field=i, record=(9 if i < 3 else 37), text=f'原文{i}。') for i in range(1, 5)], 24, 48),
    ([dict(field=1, record=37, text='本人の原記録。')] + [
        dict(field=i + 2, record=None, record_refs=[37], source_role='USER_ANALYSIS_MAP_CORRECTION',
            text=f'訂正{i}。' + '長い本人説明' * 30 + '。') for i in range(8)], 24, 48),
    ([dict(field=i + 1, record=None, record_refs=[9, 37],
        source_role='USER_ANALYSIS_MAP_CORRECTION', text=f'本人訂正{i}。') for i in range(8)], 24, 48),
    ([dict(field=1, text='記録番号のない原文。')], 24, 48),
])
def test_ordinary_capacity_preserves_independent_meanings_and_whole_corrections(fields, nodes, edges):
    before = deepcopy(fields)
    schema = schema_for(fields)
    assert schema['properties']['nodes']['maxItems'] == nodes
    assert schema['properties']['edges']['maxItems'] == edges
    by_field = {part['properties']['field']['enum'][0]: part['properties']['quote']['enum']
        for part in evidence_schema(schema)['oneOf']}
    for field in fields:
        if field.get('source_role') == 'USER_ANALYSIS_MAP_CORRECTION':
            assert by_field[field['field']] == [field['text']]
            assert allowed(evidence_schema(schema), dict(field=field['field'], quote=field['text']))
            assert not allowed(evidence_schema(schema), dict(field=field['field'], quote=field['text'][:5]))
    assert fields == before


def test_single_record_keeps_multiple_meanings_long_root_and_distinct_relation_kinds():
    # One record can contain separate meanings. A short sentence must not
    # remove a longer root needed to support one of them, nor cap its graph
    # at two nodes or one relation kind per pair.
    roots = ['長い事情' * 45 + 'を考えて保留した。',
        '私は本を読んだ。', '私は友人への返事をまだ送っていない。']
    original = ''.join(roots)
    fields = [dict(field=1, record=37, text=original)]
    messages = [dict(role='system', content='synthetic'), dict(role='user',
        content=json.dumps(dict(fields=fields), ensure_ascii=False))]
    before = deepcopy(messages)
    schema = probe.semantic_output_schema(messages)
    quotes = evidence_schema(schema)['oneOf'][0]['properties']['quote']['enum']
    assert len(roots[0]) > 160 and all(root in quotes for root in roots)
    assert original in quotes
    packet = json.loads(graph_document(['n1', 'n2', 'n3'], []))
    for index, (node, quote) in enumerate(zip(packet['nodes'], roots), 1):
        node['title'] = f'独立した意味{index}'
        node['evidence'] = [dict(quote=quote, field=1)]
    packet['edges'] = [dict(zip(('from', 'to', 'relation_kind', 'label', 'explanation'),
        ('n1', 'n2', kind, '比較', '両項目の関係'))) for kind in (
            'CONTEXT_CONTRAST', 'SHARED_MEANING')]
    text = json.dumps(packet, ensure_ascii=False, separators=(',', ':'))
    assert allowed(schema, packet)
    assert_compact_leaf_native(messages, text, True)
    assert messages == before


@pytest.mark.parametrize('stage', [None, 'LEAF', 'MERGE'])
def test_native_selects_evidence_then_meanings_and_relations_before_overview(stage):
    fields = [dict(field=1, record=9, text='本人の記録です。補足です。'),
        dict(field=2, record=37, text='本人の記録です。別欄です。')]
    material = dict(fields=fields)
    if stage is not None:
        material['history_stage'] = dict(kind=stage)
    messages = [dict(role='system', content='synthetic'), dict(role='user',
        content=json.dumps(material, ensure_ascii=False))]
    before = deepcopy(messages)
    packet = json.loads(graph_document(['n1', 'n2'], [] if stage == 'LEAF' else [('n1', 'n2')]))
    packet['nodes'][1]['evidence'][0]['field'] = 2
    def encoded(value):
        return json.dumps(value, ensure_ascii=False, separators=(',', ':'))
    assert list(packet) == ['schema_version', 'nodes', 'edges', 'overview']
    assert all(next(iter(node)) == 'evidence' for node in packet['nodes'])
    assert_compact_leaf_native(messages, encoded(packet), True)
    overview_first = {key: packet[key] for key in ('schema_version', 'overview', 'nodes', 'edges')}
    assert_compact_leaf_native(messages, encoded(overview_first), False)
    evidence_last = deepcopy(packet)
    node = evidence_last['nodes'][0]
    evidence_last['nodes'][0] = {**{key: value for key, value in node.items() if key != 'evidence'},
        'evidence': node['evidence']}
    assert_compact_leaf_native(messages, encoded(evidence_last), False)
    schema = probe.semantic_output_schema(messages)
    assert set(schema['properties']) == {'schema_version', 'overview', 'nodes', 'edges'}
    assert set(schema['properties']['nodes']['items']['properties']) == {
        'node_id', 'node_kind', 'title', 'summary', 'explanation', 'perspective', 'unknowns', 'evidence'}
    assert messages == before


def test_prior_and_new_raw_key_orders_keep_exact_receipt_binding_and_same_map_text():
    import analysis_semantic_map as semantic
    from test_analysis_semantic_map import sample, candidate, response, OWNER
    prepared = semantic.prepare_semantic_map(OWNER, sample())
    before = deepcopy(prepared.messages()), prepared.source_guard, prepared.request_ref
    prior = candidate()
    fields = {field['field']: field['text'] for field in json.loads(prepared.material_json)['fields']}
    for node in prior['nodes']:
        for root in node['evidence']:
            root['quote'] = fields[root['field']]
    ordered = deepcopy(prior)
    ordered['nodes'] = [dict(evidence=node['evidence'], **{key: value for key, value in node.items()
        if key != 'evidence'}) for node in ordered['nodes']]
    ordered = {key: ordered[key] for key in ('schema_version', 'nodes', 'edges', 'overview')}
    texts, public_keys = [], []
    for packet in (prior, ordered):
        receipt = response(prepared, raw=json.dumps(packet, ensure_ascii=False, separators=(',', ':')))
        artifact, _ = semantic.build_semantic_map(prepared, receipt)
        assert artifact.private_evidence()['response_sha256'] == receipt.raw_sha256
        projection = artifact.safe_projection(authenticated_owner_scope=OWNER)
        assert not {'fields', 'source_guard', 'messages_sha256', 'raw'} & set(projection)
        public_keys.append(set(projection))
        texts.append(artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'])
    assert public_keys[0] == public_keys[1] and texts[0] == texts[1]
    assert (prepared.messages(), prepared.source_guard, prepared.request_ref) == before


def test_instruction_format_example_matches_native_generation_sequence():
    import analysis_semantic_map as semantic
    from test_analysis_semantic_map import sample, OWNER
    prepared = semantic.prepare_semantic_map(OWNER, sample())
    messages = prepared.messages()
    exemplar = json.loads(messages[0]['content'].split('厳密な形式:\n', 1)[1].splitlines()[0])
    schema = probe.semantic_output_schema(messages)
    assert list(exemplar) == list(schema['properties']) == ['schema_version', 'nodes', 'edges', 'overview']
    assert list(exemplar['nodes'][0]) == list(schema['properties']['nodes']['items']['properties'])
    assert next(iter(exemplar['nodes'][0])) == 'evidence'
