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
    'RELATIONS': ('\n各単位でfactが0なら、同じ単位のevidenceを順番に読み、各引用をそのままつないだ本文です。'
        'fact_part_overridesに同じn番号.u番号.e番号がある箇所だけ、その本文片を引用に代えて読みます。'
        'qualification_candidatesの[n,u,k]は番号nの項目、u番目の単位のunknownsのk番目と同じ留保です。'
        'unknownsとqualification_candidatesの留保は、それぞれの原文と時点を確認します。'
        '返すqualification_reviewは候補順の配列です。STATED、EARLIER、DUPLICATEは文字列で、'
        'OPENは[0]で候補の原文全体、許可された別の原文範囲なら[引用符号]で選びます。'),
}


def instruction(version, phase):
    require(version in VERSIONS)
    guidance = INSTRUCTION
    if version in (RECORD_VERSION, VERSION):
        guidance += RECORD_GUIDANCE
    if version == VERSION:
        guidance += ('\n原欄はfieldsに全文があります。根拠・留保の引用値が[開始,終了,読取り句]なら、'
            '対応する欄のその範囲の全文です。読取り句は両端の手掛かりで、途中の否定や条件を含む元の範囲を読みます。'
            '未読範囲の圧縮表示ではstartから各lengthsの長さだけ進み、次までの間隔は1、'
            'gapsにある番号だけ指定間隔です。')
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


def _range_lengths(material, *, unpack=False):
    for row in (material.get('source_duties') or {}).get('unassessed_source_ranges', ()):
        ranges = row['ranges']
        if unpack:
            if type(ranges) is not dict:
                continue
            require(set(ranges) == {'start', 'lengths', 'gaps'})
            start, lengths, gaps = ranges['start'], ranges['lengths'], ranges['gaps']
            require(type(start) is int and start >= 0 and type(lengths) is list and lengths
                    and type(gaps) is list)
            gap_at = {}
            for pair in gaps:
                require(type(pair) is list and len(pair) == 2)
                index, gap = pair
                require(type(index) is int and 1 <= index < len(lengths) and index not in gap_at
                        and type(gap) is int and gap >= 0 and gap != 1)
                gap_at[index] = gap
            expanded = []
            for i, length in enumerate(lengths):
                require(type(length) is int and length > 0)
                expanded.append([start, start + length])
                start += length + gap_at.get(i + 1, 1)
            row['ranges'] = expanded
        elif (type(ranges) is list and len(ranges) >= 4
                and all(type(pair) is list and len(pair) == 2 and all(type(n) is int for n in pair)
                        and 0 <= pair[0] < pair[1] for pair in ranges)
                and all(prev[1] <= nxt[0] for prev, nxt in zip(ranges, ranges[1:]))):
            packed = dict(start=ranges[0][0], lengths=[hi-lo for lo, hi in ranges],
                gaps=[[i, right[0]-left[1]] for i, (left, right) in enumerate(zip(ranges, ranges[1:]), 1)
                      if right[0]-left[1] != 1])
            if len(compact_json(packed)) < len(compact_json(ranges)):
                row['ranges'] = packed


def _source_spelling(row, fields, field_key, quote_key, *, unpack):
    field = fields.get(row.get(field_key))
    if not field or quote_key not in row:
        return
    quote = row[quote_key]
    if unpack and type(quote) is list:
        require(len(quote) == 3)
        start, end, cue = quote
        literal = source_slice(fields, row[field_key], start, end)
        require(cue == literal[:4] + '…' + literal[-4:])
        row[quote_key] = literal
    elif not unpack and type(quote) is str and len(quote) > 12:
        span = field.get('fragment_scalar_range')
        if type(span) is not list or len(span) != 2:
            return
        start = field['text'].find(quote)
        if start >= 0 and start == field['text'].rfind(quote):
            begin = span[0] + start
            packed = [begin, begin + len(quote), quote[:4] + '…' + quote[-4:]]
            if len(compact_json(packed).encode()) < len(compact_json(quote).encode()):
                row[quote_key] = packed


def _visible_sources(material, fields, *, unpack=False):
    """Preserve every source/qualification, including duplicates with different field owners."""
    if material['author_phase'] == 'NODES':
        for entries in material.get('evidence_parts_by_unit', {}).values():
            for root in entries.values():
                _source_spelling(root, fields, 'field', 'quote', unpack=unpack)
        return
    if material['author_phase'] != 'RELATIONS':
        return
    registry = material.get('candidate_nodes', ())
    candidates = material.get('qualification_candidates', {})
    by_indices, by_source = {}, {}
    for n, node in enumerate(registry, 1):
        for u, unit in enumerate(node['units'], 1):
            for root in unit['evidence']:
                _source_spelling(root, fields, 'field', 'quote', unpack=unpack)
            for k, source in enumerate(unit.get('unknowns', ()), 1):
                if unpack:
                    _source_spelling(source, fields, 'source_field', 'source_quote', unpack=True)
                ref = (n, u, k)
                by_indices[ref] = source
                by_source.setdefault(compact_json(source), ref)
                if not unpack:
                    _source_spelling(source, fields, 'source_field', 'source_quote', unpack=False)
    for key, candidate in candidates.items():
        if unpack and type(candidate) is list:
            require(len(candidate) == 3 and all(type(i) is int for i in candidate))
            ref = tuple(candidate)
            require(ref in by_indices)
            candidates[key] = dict(by_indices[ref])
        elif not unpack and (ref := by_source.get(compact_json(candidate))) is not None:
            candidates[key] = list(ref)
        elif type(candidate) is dict:
            _source_spelling(candidate, fields, 'source_field', 'source_quote', unpack=unpack)


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


def _relation_fact_references(material, *, unpack=False):
    """The ordered roots and explicit overrides already carry the author's entire unit fact."""
    if material['author_phase'] != 'RELATIONS' or 'fact_part_overrides' not in material:
        return
    overrides = material['fact_part_overrides']
    for node in material.get('candidate_nodes', ()):
        for index, unit in enumerate(node['units'], 1):
            ref = f"{node['node_id']}.u{index}"
            fact = ''.join(overrides.get(f'{ref}.e{i}', root['quote'])
                           for i, root in enumerate(unit['evidence'], 1))
            if unpack and type(unit['fact']) is int:
                require(unit['fact'] == 0 and bool(fact))
                unit['fact'] = fact
            elif not unpack and fact and unit['fact'] == fact:
                unit['fact'] = 0


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
        _relation_fact_references(material)
        _visible_sources(material, fields)
        _range_lengths(material)
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
            _range_lengths(material, unpack=True)
            _visible_sources(material, fields, unpack=True)
            _node_plan_references(material, unpack=True)
            _relation_fact_references(material, unpack=True)
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
        self.qualification_items = ()
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
        elif self.phase == 'RELATIONS':
            self.binding = messages_digest(material['candidate_nodes'])
            candidates = material['qualification_candidates']
            # Request serialization can place q10 before q2. The authored NODES
            # registry numbers qualifications by node, unit and unknown ordinal.
            numbered = sorted(candidates, key=lambda ref: int(ref.partition('/')[0][1:]))
            require(all(ref.startswith(f'q{i}/') for i, ref in enumerate(numbered, 1)))
            self.qualification_items = tuple((ref, candidates[ref]['source_quote']) for ref in numbered)
            literals = set()
            for _, source in self.qualification_items:
                _, parts = choice_module.choices_for_field(dict(text=source, source_role='ORIGINAL_INPUT'))
                literals.update(parts)
                literals.add(source)
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
        require(self.phase in ('NODES', 'RELATIONS'))
        original = code[1:] if code.startswith('~~') else code
        require(self.quote_code(original) == code)
        return original

    def _root(self, pair, *, qualification=False):
        require(type(pair) is list and len(pair) == 2 and type(pair[1]) is int)
        q, field = self._quote(pair[0]), pair[1]
        return dict(source_quote=q, source_field=field) if qualification else dict(quote=q, field=field)

    def _relation_values(self, value, *, unpack):
        keys = {'schema_version', 'nodes_sha256', 'qualification_review', 'edges', 'overview'}
        require(type(value) is dict and set(value) == keys and value['nodes_sha256'] == self.binding
                and value['schema_version'] == MODEL_SCHEMA + '.relations')
        source = value['qualification_review']
        closed = ('STATED', 'EARLIER', 'DUPLICATE')
        if unpack:
            require(type(source) is list and len(source) == len(self.qualification_items))
            review = {}
            for (key, original), choice in zip(self.qualification_items, source, strict=True):
                if type(choice) is str:
                    require(choice in closed)
                    review[key] = dict(status=choice)
                else:
                    require(type(choice) is list and len(choice) == 1)
                    ref = choice[0]
                    if type(ref) is int:
                        require(ref == 0)
                        quote = original
                    else:
                        quote = self._quote(ref)
                        require(quote != original)
                    review[key] = dict(status='OPEN', source_quote=quote)
        else:
            require(type(source) is dict and set(source) == {key for key, _ in self.qualification_items})
            review = []
            for key, original in self.qualification_items:
                item = source[key]
                require(type(item) is dict)
                if set(item) == {'status', 'source_quote'} and item['status'] == 'OPEN':
                    quote = item['source_quote']
                    review.append([0 if quote == original else self.quote_code(quote)])
                else:
                    require(set(item) == {'status'} and item['status'] in closed)
                    review.append(item['status'])
        return dict(schema_version=value['schema_version'], nodes_sha256=self.binding,
                    qualification_review=review, edges=value['edges'], overview=value['overview'])

    def decode(self, raw):
        if self.phase == 'RELATIONS':
            return self._relation_values(raw, unpack=True)
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
        if self.phase == 'RELATIONS':
            raw = self._relation_values(value, unpack=False)
            require(messages_digest(self.decode(raw)) == messages_digest(value))
            return raw
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
    if material['merge_wire_version'] != VERSION:
        return None
    logical = json.loads(legacy_messages(messages)[1]['content'])
    if choice_module is None:
        import analysis_plan_source_choices as choice_module
    if logical['author_phase'] == 'NODES' and fact_key is None:
        from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import _semantic_fact_part_key
        fact_key = _semantic_fact_part_key
    return ResponseCodec(logical, choice_module, fact_key)
