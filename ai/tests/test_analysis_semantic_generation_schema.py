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
