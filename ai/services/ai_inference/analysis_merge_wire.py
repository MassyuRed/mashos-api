"""Reversible private transport for v24 history MERGE. Saved receipts retain the bytes received."""
from __future__ import annotations

import hashlib
import json


LEGACY_VERSION = 'cocolon.analysis.merge_wire.v1'
RECORD_VERSION = 'cocolon.analysis.merge_wire.v2'
VERSION = 'cocolon.analysis.merge_wire.v3'
VERSIONS = (LEGACY_VERSION, RECORD_VERSION, VERSION)
PROFILE = 'semantic_map.node_local.v4.occurrence.v24'
MODEL_SCHEMA = 'cocolon.analysis.semantic_map.node_local.model.v4'
WIRE_FIELDS = {'merge_wire_version', 'merge_original_messages_sha256'}
INSTRUCTION = ('\nMERGEのleaf_source_indexは[欄番号,元の開始位置,終了位置,選べる原文句（ある場合）]です。'
    '引用の内容は指定したfieldsの同じ原文範囲です。開始を含み、終了は含みません。'
    'field_manifestのsource_rowsは[欄番号,source_columnsの0起点の番号]の場合、'
    '表示している完全な原欄と同じです。元の各葉から届いた範囲と、本人が入力した原文の区別は変わりません。')

RECORD_GUIDANCE = ('\n記録ごとの項目を並べられる場合、先頭の項目は記録の順に作ります。'
    '各項目は対応する原記録の本人の欄から始め、その記録の根拠で説明します。'
    '12記録を超える場合、各記録の原欄を選べない場合、または訂正などの独立した項目が収まらない場合は、'
    'この順序に固定せず、原文に沿って項目を構成します。'
    '複数の記録に基づく比較では、どの記録のどの条件・時点の話かを別々のunitで示します。'
    '別項目の関連はRELATIONSで具体的な根拠を一つずつ選びます。別の対象や未確認事項を同じ出来事として扱いません。')


RESPONSE_GUIDANCE = {
    'PLAN': ('\n今回のMERGEの応答は {"h":"source_choices_sha256の値","n":[項目,…]} です。'
        '項目は単位の配列、単位は根拠の配列、一つの根拠は[原文の短い符号,欄番号]です。'
        '符号 ~先頭…末尾 はその範囲と完全に同じ原文を指します。'
        '記録ごとに本人の行動欄と経過の末尾を読み、最初の予定・検討と、実行したこと、'
        '見送ったこと、未確認のことを時点・対象とともに選びます。別の出来事には別の単位を使います。'
        '事実に必要な根拠を選び、同じ内容の繰り返しを避けます。'),
    'NODES': ('\n今回のMERGEの応答は {"h":"plan_sha256の値","n":[項目,…]} です。'
        '入力のplanの各単位の数値は、evidence_parts_by_unitに示した根拠の個数です。'
        '同じ項目・単位順で、項目は[単位の配列,node_kind,perspective,title,meaning]、'
        '単位は[source_mode,根拠順のfact値の配列,留保の配列]、留保は[原文の符号,欄番号]です。'
        '根拠名は順序で決まり、符号 ~先頭…末尾 は完全な原文を指します。'
        '未確認は確認済みに変えず、他の出来事や別人の発言を本人の行動にしません。'
        '別々の根拠にある出来事を同時とせず、後の記録や返答で判明したことを前の時点の確定事項にしません。'),
    'RELATIONS': '',
}


def instruction(version, phase):
    require(version in VERSIONS)
    guidance = INSTRUCTION
    if version in (RECORD_VERSION, VERSION):
        guidance += RECORD_GUIDANCE
    if version == VERSION:
        guidance += RESPONSE_GUIDANCE[phase]
    return guidance


def require(ok):
    if not ok:
        raise ValueError('analysis_merge_wire_invalid')


def compact_json(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def messages_digest(messages):
    return digest(json.dumps(messages, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False))


def eligible(material):
    return (isinstance(material, dict) and material.get('author_profile') == PROFILE
            and material.get('model_schema') == MODEL_SCHEMA
            and (material.get('history_stage') or {}).get('kind') == 'MERGE'
            and material.get('author_phase') in ('PLAN', 'NODES', 'RELATIONS'))


def is_compact(messages):
    material = json.loads(messages[1]['content'])
    if not isinstance(material, dict) or not WIRE_FIELDS.intersection(material):
        return False
    require(WIRE_FIELDS.issubset(material) and eligible(material)
            and material['merge_wire_version'] in VERSIONS)
    return True


def displayed_fields(material):
    """Some PLAN fields carry the same ordered text as annotated passages."""
    fields = {}
    for field in material['fields']:
        number = field['field']
        require(type(number) is int and number not in fields)
        if 'text' in field:
            require('passages' not in field and type(field['text']) is str)
            fields[number] = field
        else:
            parts = []
            for passage in field['passages']:
                if isinstance(passage, str):
                    parts.append(passage)
                else:
                    parts.extend(piece if isinstance(piece, str) else piece[0] for piece in passage)
            fields[number] = dict(field, text=''.join(parts))
    return fields


def source_slice(fields, field_number, lo, hi):
    require(type(field_number) is int and type(lo) is int and type(hi) is int and lo < hi)
    field = fields[field_number]
    start, end = field['fragment_scalar_range']
    require(start <= lo < hi <= end and end - start == len(field['text']))
    return field['text'][lo-start:hi-start]


def pack_index(index, fields):
    result = []
    for row in index:
        if tuple(row) not in (('field', 'quote', 'scalar_range'), ('field', 'quote', 'scalar_range', 'choice')):
            result.append(row)
            continue
        lo, hi = row['scalar_range']
        require(source_slice(fields, row['field'], lo, hi) == row['quote'])
        entry = [row['field'], lo, hi]
        if 'choice' in row:
            entry.append(row['choice'])
        result.append(entry)
    return result


def unpack_index(index, fields):
    result = []
    for row in index:
        if type(row) is dict:
            result.append(row)
        else:
            require(type(row) is list and len(row) in (3, 4))
            number, lo, hi = row[:3]
            entry = dict(field=number, quote=source_slice(fields, number, lo, hi), scalar_range=[lo, hi])
            if len(row) == 4:
                entry['choice'] = row[3]
            result.append(entry)
    return result


def manifest_row(field, columns):
    require(field.get('fragment_is_complete_field') is True
            and field.get('fragment_scalar_range') == [0, len(field['text'])])
    values = dict(field, scalar_length=len(field['text']), text_sha256=digest(field['text']))
    return {name: values[name] for name in columns}


def pack_manifest(manifest, fields):
    columns, rows = [], []
    for row in manifest:
        field = fields.get(row['field'])
        names = list(row)
        if (field and field.get('fragment_is_complete_field') is True
                and all(k in field or k in ('text_sha256', 'scalar_length') for k in names)
                and compact_json(manifest_row(field, names)) == compact_json(row)):
            if names not in columns:
                columns.append(names)
            rows.append([row['field'], columns.index(names)])
        else:
            # A fragment or absent field cannot reconstruct the full-field hash.
            rows.append(row)
    return dict(source_columns=columns, source_rows=rows)


def unpack_manifest(manifest, fields):
    require(type(manifest) is dict and set(manifest) == {'source_columns', 'source_rows'})
    columns = manifest['source_columns']
    result = []
    for row in manifest['source_rows']:
        if type(row) is dict:
            result.append(row)
            continue
        require(type(row) is list and len(row) == 2)
        number, layout = row
        require(type(number) is int and type(layout) is int and 0 <= layout < len(columns))
        result.append(manifest_row(fields[number], columns[layout]))
    return result


def _node_plan_references(material, *, unpack=False):
    """Keep exactly one visible copy of every selected quote and its fact references."""
    if material['author_phase'] != 'NODES' or 'plan' not in material or 'evidence_parts_by_unit' not in material:
        return
    parts = material['evidence_parts_by_unit']
    for node in material['plan']['nodes']:
        for u, unit in enumerate(node['units'], 1):
            entries = parts.get(f"{node['node_id']}.u{u}", {})
            sources = [dict(field=entries[f'e{i}']['field'], quote=entries[f'e{i}']['quote'])
                       for i in range(1, len(entries) + 1)]
            evidence = unit['evidence']
            if unpack and type(evidence) is int:
                require(evidence == len(sources) and 1 <= evidence <= 4)
                unit['evidence'] = sources
            elif not unpack and evidence == sources and sources:
                unit['evidence'] = len(sources)


def prepare_messages(messages, *, version=VERSION):
    material = json.loads(messages[1]['content'])
    if isinstance(material, dict):
        require(not WIRE_FIELDS.intersection(material))
    if not eligible(material):
        return messages
    require(compact_json(material) == messages[1]['content'])
    fields = displayed_fields(material)
    material['leaf_source_index'] = pack_index(material['leaf_source_index'], fields)
    material['field_manifest'] = pack_manifest(material['field_manifest'], fields)
    if version == VERSION:
        _node_plan_references(material)
    material['merge_wire_version'] = version
    material['merge_original_messages_sha256'] = messages_digest(messages)
    return [dict(messages[0], content=messages[0]['content'] + instruction(version, material['author_phase'])),
            dict(messages[1], content=compact_json(material))]


def legacy_messages(messages):
    try:
        material = json.loads(messages[1]['content'])
        require(eligible(material))
        version = material.pop('merge_wire_version', None)
        suffix = instruction(version, material['author_phase'])
        binding = material.pop('merge_original_messages_sha256')
        require(messages[0]['content'].endswith(suffix))
        fields = displayed_fields(material)
        material['leaf_source_index'] = unpack_index(material['leaf_source_index'], fields)
        material['field_manifest'] = unpack_manifest(material['field_manifest'], fields)
        if version == VERSION:
            _node_plan_references(material, unpack=True)
        result = [dict(messages[0], content=messages[0]['content'][:-len(suffix)]),
                  dict(messages[1], content=compact_json(material))]
        require(messages_digest(result) == binding)
        # Ensure the sender used the canonical representation, including the menu layout.
        require(prepare_messages(result, version=version) == messages)
        return result
    except (KeyError, TypeError, IndexError) as exc:
        raise ValueError('analysis_merge_wire_invalid') from exc


def _quote_codes(literals):
    """Visible beginnings and endings identify one complete source value in this request."""
    from collections import Counter

    literals = set(literals)
    # An original tilde is escaped, so even literal text resembling a code is unambiguous.
    result = {s: ('~' + s if s.startswith('~') else s) for s in literals}
    longer = [s for s in literals if len(s) > 8]
    pending = set(longer)
    for width in (2, 3, 4, 6, 8, 12):
        if not pending:
            break
        codes = {s: '~' + s[:width] + '…' + s[-width:] for s in pending}
        counts = Counter(codes.values())
        for source, code in codes.items():
            if counts[code] == 1 and len(code) < len(source) and not code.startswith('~~'):
                result[source] = code
                pending.remove(source)
    require(len(set(result.values())) == len(result))
    return result


class ResponseCodec:
    """Project only deterministic positions. Every authored choice remains in the raw receipt."""
    def __init__(self, material, choice_module, fact_key):
        self.phase = material['author_phase']
        self.plan_units = ()
        if self.phase == 'PLAN':
            _, aliases, allowed = choice_module.restore_view(material)
            assigned = {(field, quote) for (field, _), quote in aliases.items()}
            literals = {quote for field, texts in allowed.items() for quote in texts
                        if (field, quote) not in assigned}
            literals.update(alias for _, alias in aliases)
            self.binding = material['source_choices_sha256']
        elif self.phase == 'NODES':
            plan = material['plan']
            self.binding = messages_digest(['analysis.node-facts.v1', 'NODES', material['fact_source_request_ref'], plan])
            self.plan_units = tuple(tuple(tuple(fact_key(unit['evidence'], i)
                for i in range(len(unit['evidence']))) for unit in node['units']) for node in plan['nodes'])
            literals = set()
            for node in plan['nodes']:
                for unit in node['units']:
                    for root in unit['evidence']:
                        quote = root['quote']
                        literals.add(quote)
                        # Shorten common bound qualifications. Other valid original literals
                        # retain their complete spelling and pass through the same admission.
                        _, parts = choice_module.choices_for_field(dict(text=quote, source_role='ORIGINAL_INPUT'))
                        literals.update(parts)
        else:
            raise ValueError('analysis_merge_wire_phase_invalid')
        self._codes = _quote_codes(literals)
        self.quotes = {code: quote for quote, code in self._codes.items()}

    def quote_code(self, quote):
        require(type(quote) is str)
        return self._codes.get(quote, '~' + quote if quote.startswith('~') else quote)

    def _quote(self, code):
        require(type(code) is str)
        if code in self.quotes:
            return self.quotes[code]
        require(self.phase == 'NODES')
        original = code[1:] if code.startswith('~~') else code
        require(self.quote_code(original) == code)
        return original

    def _root(self, pair, *, qualification=False):
        require(type(pair) is list and len(pair) == 2 and type(pair[1]) is int)
        q, field = self._quote(pair[0]), pair[1]
        return dict(source_quote=q, source_field=field) if qualification else dict(quote=q, field=field)

    def decode(self, raw):
        require(type(raw) is dict and set(raw) == {'h', 'n'} and raw['h'] == self.binding
                and type(raw['n']) is list)
        version = MODEL_SCHEMA + '.' + self.phase.lower()
        if self.phase == 'PLAN':
            nodes = []
            require(1 <= len(raw['n']) <= 12)
            for n, row in enumerate(raw['n'], 1):
                require(type(row) is list and 1 <= len(row) <= 2)
                units = []
                for unit in row:
                    require(type(unit) is list and 1 <= len(unit) <= 4)
                    units.append(dict(evidence=[self._root(pair) for pair in unit]))
                nodes.append(dict(node_id=f'n{n}', units=units))
            return dict(schema_version=version, source_choices_sha256=self.binding, nodes=nodes)
        require(len(raw['n']) == len(self.plan_units))
        nodes = {}
        for n, (row, layout) in enumerate(zip(raw['n'], self.plan_units, strict=True), 1):
            require(type(row) is list and len(row) == 5 and type(row[0]) is list and len(row[0]) == len(layout))
            entries, kind, perspective, title, meaning = row
            units = {}
            for u, (entry, keys) in enumerate(zip(entries, layout, strict=True), 1):
                require(type(entry) is list and len(entry) == 3)
                mode, parts, unknowns = entry
                require(type(parts) is list and len(parts) == len(keys) and type(unknowns) is list
                        and len(unknowns) <= 2)
                units[f'u{u}'] = dict(evidence_ref=f'n{n}.u{u}', source_mode=mode,
                    fact_parts=dict(zip(keys, parts, strict=True)),
                    unknowns=[self._root(pair, qualification=True) for pair in unknowns])
            nodes[f'n{n}'] = dict(units=units, node_kind=kind, perspective=perspective, title=title, meaning=meaning)
        return dict(schema_version=version, plan_sha256=self.binding, nodes=nodes)

    def encode(self, value):
        """Inverse, used to check that no model selection is lost in a physical response."""
        if self.phase == 'PLAN':
            rows = [[[[self.quote_code(root['quote']), root['field']] for root in unit['evidence']]
                      for unit in node['units']] for node in value['nodes']]
        else:
            rows = []
            for n, layout in enumerate(self.plan_units, 1):
                node = value['nodes'][f'n{n}']
                entries = []
                for u, keys in enumerate(layout, 1):
                    unit = node['units'][f'u{u}']
                    entries.append([unit['source_mode'], [unit['fact_parts'][k] for k in keys],
                        [[self.quote_code(q['source_quote']), q['source_field']] for q in unit['unknowns']]])
                rows.append([entries, node['node_kind'], node['perspective'], node['title'], node['meaning']])
        raw = dict(h=self.binding, n=rows)
        # Canonical JSON also distinguishes booleans from identically valued integers.
        require(messages_digest(self.decode(raw)) == messages_digest(value))
        return raw


def response_codec(messages, *, choice_module=None, fact_key=None):
    """Construct a request-local v3 output view after checking the logical message binding."""
    if not is_compact(messages):
        return None
    material = json.loads(messages[1]['content'])
    if material['merge_wire_version'] != VERSION or material['author_phase'] == 'RELATIONS':
        return None
    logical = json.loads(legacy_messages(messages)[1]['content'])
    if choice_module is None:
        import analysis_plan_source_choices as choice_module
    if logical['author_phase'] == 'NODES' and fact_key is None:
        from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import _semantic_fact_part_key
        fact_key = _semantic_fact_part_key
    return ResponseCodec(logical, choice_module, fact_key)
