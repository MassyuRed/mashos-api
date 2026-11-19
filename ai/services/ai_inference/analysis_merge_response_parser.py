"""Project the private MERGE tuple notation into the existing native grammar.

The logical parser owns every source, meaning and visible-text constraint.
Only JSON syntax, request-bound constants and citation spellings are supplied
by this adapter. Decoder branches retain independent logical parser states.
"""
import json

from lmformatenforcer import CharacterLevelParser


def _literal(physical, logical=None):
    return ('literal', physical, physical if logical is None else logical)


def _scalar(name=''):
    return ('scalar', name, '', False)


def _series(make_item, minimum, maximum, closing, count=0):
    return ('series', make_item, minimum, maximum, closing, count)


def _enum_strings(parser):
    """The logical parser has already narrowed each quote to this exact slot."""
    if hasattr(parser, 'parsers'):
        for branch in parser.parsers:
            yield from _enum_strings(branch)
    elif hasattr(parser, 'object_stack') and parser.object_stack:
        yield from _enum_strings(parser.object_stack[-1])
    else:
        yield from (getattr(parser, 'allowed_strings', ()) or ())


def _advance(parser, spelling):
    for char in spelling:
        if char not in parser.get_allowed_characters():
            return None
        parser = parser.add_character(char)
    return parser


def response_parser(logical, codec):
    alphabet = frozenset(logical.config.alphabet)
    def quoted(value):
        return ''.join(c if ord(c) < 128 or c in alphabet and c != '\ufffd'
                       else json.dumps(c)[1:-1] for c in json.dumps(value, ensure_ascii=False))

    def pair(qualification):
        name, number = ('source_quote', 'source_field') if qualification else ('quote', 'field')
        return (_literal('[', '{' + quoted(name) + ':'), ('alias',),
                _literal(',', ',' + quoted(number) + ':'), _scalar(), _literal(']', '}'))

    def planned_node(index):
        def unit(_):
            return (_literal('[', '{"evidence":['), _series(lambda _: pair(False), 1, 4, ']}'))
        return (_literal('[', '{"node_id":"n' + str(index) + '","units":['),
                _series(unit, 1, 2, ']}'))

    def authored_node(index):
        layout = codec.plan_units[index - 1]
        def unit(number):
            keys = layout[number - 1]
            ref = f'n{index}.u{number}'
            out = [_literal('[', f'"u{number}":{{"evidence_ref":"{ref}","source_mode":'),
                   _scalar(), _literal(',', ',"fact_parts":')]
            for i, key in enumerate(keys):
                out.extend((_literal(',' if i else '[', (',' if i else '{') + quoted(key) + ':'),
                            _scalar()))
            out.extend((_literal(']', '}'), _literal(',', ',"unknowns":'), _literal('['),
                        _series(lambda _: pair(True), 0, 2, ']'), _literal(']', '}')))
            return tuple(out)
        out = [_literal('[', f'"n{index}":{{'), _literal('[', '"units":{'),
               _series(unit, len(layout), len(layout), '}')]
        for name in ('node_kind', 'perspective', 'title', 'meaning'):
            out.extend((_literal(',', ',' + quoted(name) + ':'), _scalar(name)))
        out.append(_literal(']', '}'))
        return tuple(out)

    plan = codec.phase == 'PLAN'
    count = len(codec.plan_units)
    logical_header = ('{"schema_version":"cocolon.analysis.semantic_map.node_local.model.v4.'
                      + codec.phase.lower() + '","' + ('source_choices_sha256' if plan else 'plan_sha256')
                      + '":' + quoted(codec.binding) + ',"nodes":' + ('[' if plan else '{'))
    ops = (_literal('{"h":' + quoted(codec.binding) + ',"n":[', logical_header),
           _series(planned_node if plan else authored_node, 1 if plan else count, 12 if plan else count,
                   ']' if plan else '}'), _literal('}'))
    return ResponseParser(logical, codec, quoted, ops)


class ResponseParser(CharacterLevelParser):
    def __init__(self, logical, codec, quoted, ops, history=None):
        super().__init__(logical.config)
        self.logical = logical
        self.context = logical.context if hasattr(logical, 'context') else None
        self.codec = codec
        self.quoted = quoted
        self.ops = ops
        self.history = history
        self._options = None

    @property
    def object_stack(self):
        return getattr(self.logical, 'object_stack', ())

    def projected_prefix(self):
        chunks = []
        part = self.history
        while part:
            part, chunk = part
            chunks.append(chunk)
        return ''.join(reversed(chunks))

    def _next(self, ops, parser=None, logical_text=''):
        history = (self.history, logical_text) if logical_text else self.history
        return ResponseParser(self.logical if parser is None else parser, self.codec, self.quoted, ops, history)

    def _choices(self):
        if self._options is not None:
            return self._options
        options = {}
        if self.ops:
            op, tail = self.ops[0], self.ops[1:]
            kind = op[0]
            if kind == 'literal':
                physical, logical = op[1:]
                parser = _advance(self.logical, logical)
                if parser is not None:
                    rest = (_literal(physical[1:], ''),) if len(physical) > 1 else ()
                    options[physical[0]] = self._next(rest + tail, parser, logical)
            elif kind == 'series':
                factory, minimum, maximum, closing, count = op[1:]
                if count >= minimum:
                    options.update(self._next((_literal(']', closing),) + tail)._choices())
                if count < maximum:
                    comma = (_literal(','),) if count else ()
                    remaining = (_series(factory, minimum, maximum, closing, count + 1),)
                    options.update(self._next(comma + factory(count + 1) + remaining + tail)._choices())
            elif kind in ('alias', 'spelling'):
                if kind == 'alias':
                    strings = set(_enum_strings(self.logical))
                    if not strings:
                        raise ValueError('analysis_merge_native_quote_options_missing')
                    choices = [(self.quoted(self.codec.quote_code(q)), self.quoted(q)) for q in strings]
                else:
                    choices = op[1]
                buckets = {}
                for physical, logical in choices:
                    buckets.setdefault(physical[0], []).append((physical[1:], logical))
                for char, values in buckets.items():
                    if values[0][0]:
                        options[char] = self._next((('spelling', values),) + tail)
                    else:
                        assert len(values) == 1
                        logical = values[0][1]
                        parser = _advance(self.logical, logical)
                        if parser is not None:
                            options[char] = self._next(tail, parser, logical)
            else:
                raise ValueError('analysis_merge_native_step_invalid')
        self._options = options
        return options

    def _scalar_chars(self):
        _, _, mode, _ = self.ops[0]
        chars = self.logical.get_allowed_characters()
        if mode == 'string':
            return chars
        if mode == 'number':
            return ''.join(c for c in chars if c in '0123456789') + ''.join(self._next(self.ops[1:])._choices())
        return ''.join(c for c in chars if c in '"-0123456789')

    def get_allowed_characters(self):
        if self.ops and self.ops[0][0] == 'scalar':
            return self._scalar_chars()
        return ''.join(self._choices())

    def add_character(self, char):
        if not self.ops or self.ops[0][0] != 'scalar':
            return self._choices()[char]
        _, name, mode, escaped = self.ops[0]
        tail = self.ops[1:]
        if mode == 'number' and char not in '0123456789':
            return self._next(tail).add_character(char)
        parser = self.logical.add_character(char)
        if mode == 'string' and char == '"' and not escaped:
            return self._next(tail, parser, char)
        next_mode = mode or ('string' if char == '"' else 'number')
        escaped = mode == 'string' and char == '\\' and not escaped
        return self._next((('scalar', name, next_mode, escaped),) + tail, parser, char)

    def can_end(self):
        return not self.ops and self.logical.can_end()

    def shortcut_key(self):
        if self.ops and self.ops[0][0] == 'scalar' and self.ops[0][2] == 'string':
            return self.logical.shortcut_key()
        return None
