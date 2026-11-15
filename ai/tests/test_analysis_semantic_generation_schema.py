"""Source-copy decoding constraints; no model or semantic-quality acceptance."""
from copy import deepcopy
import json
import logging
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
        'content': json.dumps({'fields': [{'field': 1, 'text': '部屋を整えた。'}]}, ensure_ascii=False)}]
    beginning = '{"schema_version":"cocolon.analysis.semantic_map.model.v2","overview":{"title":"部屋'
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
    config = package.CharacterLevelParserConfig()
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
