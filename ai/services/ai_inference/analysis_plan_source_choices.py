"""Lossless, request-local abbreviations for PLAN evidence. All offsets are Unicode scalars."""
import hashlib
import json
import re
import unicodedata


_CONTENT_PLAN_PROFILES = frozenset({
    'semantic_map.node_local.v4.occurrence.v13', 'semantic_map.node_local.v4.occurrence.v14',
    'semantic_map.node_local.v4.occurrence.v15', 'semantic_map.node_local.v4.occurrence.v16'})


_CLOSED_TAG = re.compile(r'</?[A-Za-z_][\w:.-]*(?:\s+[^<>]*)?/?>|/>')
_UNFINISHED_CLOSING_TAG = re.compile(r'</[A-Za-z_][\w:.-]*$')


def source_markup_bound(text, quote):
    return all(m[0] in quote for m in _CLOSED_TAG.finditer(text))


def source_fact_text(text, quote):
    """A fact needs visible content; markup and symbolic facts must have a source."""
    value = text.strip()
    if not value or not source_markup_bound(value, quote):
        return False
    unfinished = _UNFINISHED_CLOSING_TAG.search(value)
    if unfinished and unfinished[0] not in quote:
        return False
    if any(char.isalnum() for char in value):
        return True
    return value == quote.strip() or (value in quote and
        any(unicodedata.category(char).startswith('S') for char in value))


def literal_fact_handles(quote):
    return set(re.findall(r'(?<![A-Za-z0-9_.%+@-])@[0-9]+(?![A-Za-z0-9_@-])', quote))


def fact_sentence_choices(quote, sentences, limit):
    """Expose only complete contiguous sentences within this exact PLAN root."""
    parts = sorted((s for s in sentences if s in quote), key=quote.index)
    if len(parts) < 2 or ''.join(parts) != quote:
        return {}
    choices = {}
    for index, value in enumerate([quote, *parts]):
        ref = '@' + str(index)
        if len(value) <= limit and ref not in quote and source_fact_text(value, quote):
            choices[ref] = value
    return choices


def source_closer_runs(quotes):
    """Only a run present verbatim in the assigned evidence may close an unopened delimiter."""
    return sorted({run for quote in quotes for run in re.findall(r'[]}]+', quote)})


def visible_closers_bound(text, source_runs):
    if '}' not in text and ']' not in text:
        return True
    stack, unmatched = [], ''
    quote = None
    escaped = False
    for index, char in enumerate(text):
        if quote:
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == quote:
                quote = None
            continue
        if stack and char in ('"', "'", '`') and not text[index - 1].isalnum():
            quote = char
        elif char in '{[':
            stack.append('}' if char == '{' else ']')
        elif char in '}]':
            if stack and stack[-1] == char:
                stack.pop()
            else:
                unmatched += char
                if not any(unmatched in run for run in source_runs):
                    return False
                continue
        unmatched = ''
    return True


def choice_scope(request_ref, choices, material=None):
    if type(request_ref) is not str or not request_ref:
        raise ValueError('semantic_plan_request_ref_invalid')
    rows = [[field, key, text] for (field, key), text in choices.items()]
    binding = ['plan-source-choices.v1', request_ref, rows]
    if material and material.get('author_profile') in _CONTENT_PLAN_PROFILES:
        # The same words may occur in records, answers and corrections. Bind the
        # actual field text, source role, record/cohort and shown scalar range.
        fields = [{k: v for k, v in field.items() if k not in {'unassessed_passage_cues', 'original_recorded_at'}}
                  for field in sorted(material['fields'], key=lambda f: f['field'])]
        records = [[r['record'], r['recorded_at']] for r in material.get('records', [])]
        binding = ['plan-content-choices.v1', request_ref, rows, fields, records, material.get('history_stage'),
                   material.get('leaf_source_index')]
    raw = json.dumps(binding, ensure_ascii=False, separators=(',', ':'), sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()


def _sentences(text):
    ends = {'「': '」', '『': '』'}
    stack, spans = [], []
    start = 0
    for i, char in enumerate(text):
        if stack and char == stack[-1]:
            stack.pop()
        elif char in ends:
            stack.append(ends[char])
        elif char in ends.values():
            return []
        elif not stack and char in '。！？!?\r\n':
            if char in '。！？!?' and i + 1 < len(text) and text[i + 1] in '。！？!?':
                continue
            spans.append(text[start:i+1].strip())
            start = i + 1
    if stack:
        return []
    spans.append(text[start:].strip())
    return [q for q in spans if q and len(q) <= 4000 and text.count(q) == 1
            and not re.search(r'["\\\x00-\x1f]', q)]


def choices_for_field(field):
    """Use the same unique bounded literals as the staged native quote menu."""
    text = field['text']
    if field['source_role'] == 'USER_ANALYSIS_MAP_CORRECTION':
        # A correction is admissible only in full.
        simple = [text] if 0 < len(text) <= 4000 and not re.search(r'["\\\x00-\x1f]', text) else []
        return simple, set(simple)
    sentences = _sentences(text)
    short = [q for q in sentences if len(q) <= 240]
    if short:
        literals = set(short)
    else:
        chunks = re.findall(r'[^"\\\x00-\x1f]+', text)
        literals = {part[i:i+4000].strip() for part in chunks for i in range(0, len(part), 2000)}
        literals.update(sentences)
    for left, right in zip(sentences, sentences[1:]):
        span = text[text.index(left):text.index(right)+len(right)]
        if len(span) <= 240 and not re.search(r'["\\\x00-\x1f]', span):
            literals.add(span)
    literals = {q for q in literals if q and text.count(q) == 1}
    return [q for q in sentences if q in literals], literals



def _content_choices(text, quote, literals, choices, number):
    """Offer at most three disjoint, unique, verbatim clauses of this quotation."""
    parts = re.split('[、，,；;：:「」『』。！？!?]', quote)
    cues = []
    for part in parts:
        cue = part.strip()
        if (3 <= len(cue) <= 32 and any(char.isalpha() for char in cue)
                and (cue == quote or cue not in literals)
                and text.find(cue) == text.rfind(cue)
                and choices.get((number, cue), quote) == quote):
            cues.append(cue)
    if len(cues) > 3:
        cues = [cues[0], cues[len(cues) // 2], cues[-1]]
    # Never require a cut inside a word, an ambiguous phrase, or a made-up token.
    return cues or [quote]


def _mark_content_choices(quote, cues):
    pieces, at = [], 0
    for cue in cues:
        start = quote.index(cue, at)
        if start > at:
            pieces.append(quote[at:start])
        pieces.append([cue])
        at = start + len(cue)
    if at < len(quote):
        pieces.append(quote[at:])
    return pieces


def prepare(material):
    """Keep each original once. In MERGE add labels only to existing leaf citations."""
    content_cued = material.get('author_profile') in _CONTENT_PLAN_PROFILES
    fields = {}
    for field in material['fields']:
        number = field.get('field')
        if type(number) is not int or number < 1 or number in fields or type(field.get('text')) is not str:
            raise ValueError('semantic_field_invalid')
        fields[number] = field
    sparse = material.get('history_stage', {}).get('kind') == 'MERGE'
    choices, allowed, numbered, index = {}, {}, {}, []
    for number in sorted(fields):
        field = fields[number]
        text = field['text']
        simple, allowed[number] = choices_for_field(field)
        if sparse or (not content_cued and re.search(r'@[1-9][0-9]*', text)):
            continue
        pieces, at = [], 0
        for quote in simple:
            start = text.index(quote)
            if at < start:
                pieces.append(text[at:start])
            if content_cued:
                cues = _content_choices(text, quote, allowed[number], choices, number)
                pieces.append(_mark_content_choices(quote, cues))
                choices.update(((number, cue), quote) for cue in cues)
            else:
                key = '@' + str(len(choices) + 1)
                pieces.append([key, quote])
                choices[number, key] = quote
            at = start + len(quote)
        if pieces:
            if at < len(text):
                pieces.append(text[at:])
            numbered[number] = pieces
    if sparse:
        for entry in material.get('leaf_source_index', []):
            number, quote = entry['field'], entry['quote']
            field = fields[number]
            start, end = entry['scalar_range']
            base = field.get('fragment_scalar_range', [0])[0]
            text = field['text']
            if not (0 <= start-base < end-base <= len(text) and text[start-base:end-base] == quote):
                raise ValueError('semantic_plan_leaf_source_unbound')
            if quote in allowed[number] and (content_cued or not re.search(r'@[1-9][0-9]*', text)):
                if content_cued:
                    cues = _content_choices(text, quote, allowed[number], choices, number)
                    choices.update(((number, cue), quote) for cue in cues)
                    entry = dict(entry, choice=cues)
                else:
                    key = '@' + str(len(choices) + 1)
                    choices[number, key] = quote
                    entry = dict(entry, choice=key)
            index.append(entry)
    view = dict(material)
    view['fields'] = []
    for f in material['fields']:
        if f['field'] in numbered:
            f = dict(f, passages=numbered[f['field']])
            del f['text']
        view['fields'].append(f)
    if sparse:
        view['leaf_source_index'] = index
    return view, choices, allowed


def _restore_view(material):
    """Recover the exact input and validate the displayed table before constrained decoding."""
    original = dict(material)
    original['fields'] = []
    for field in material['fields']:
        if 'passages' in field:
            if 'text' in field:
                raise ValueError('semantic_plan_sources_ambiguous')
            field = dict(field)
            passages = field.pop('passages')
            if material.get('author_profile') in _CONTENT_PLAN_PROFILES:
                field['text'] = ''.join(part if isinstance(part, str) else ''.join(
                    piece if isinstance(piece, str) else piece[0] for piece in part) for part in passages)
            else:
                field['text'] = ''.join(part if isinstance(part, str) else part[1] for part in passages)
        original['fields'].append(field)
    if 'leaf_source_index' in original:
        original['leaf_source_index'] = [{k:v for k,v in entry.items() if k != 'choice'}
                                         for entry in material['leaf_source_index']]
    verified, choices, allowed = prepare(original)
    if 'source_choices_sha256' in material and material['source_choices_sha256'] != choice_scope(
            material.get('source_choices_request_ref'), choices, original):
        raise ValueError('semantic_plan_choice_scope_invalid')
    if verified != material:
        raise ValueError('semantic_plan_choices_unbound')
    return original, choices, allowed


def restore_view(material):
    try:
        return _restore_view(material)
    except (AttributeError, IndexError, KeyError, TypeError) as exc:
        raise ValueError('semantic_plan_sources_invalid') from exc


def _original_field_records(material):
    return {field['field']: field['record'] for field in material['fields']
            if field['source_role'] == 'ORIGINAL_INPUT'}


def _unit_record(field_records, unit):
    records = {field_records.get(root['field']) for root in unit['evidence']}
    return records.pop() if len(records) == 1 else None


def separate_record_labels(material, units):
    """Date the source record only when it owns the whole fact."""
    if len(units) != 2:
        return ()
    field_records = _original_field_records(material)
    records = [_unit_record(field_records, unit) for unit in units]
    if None in records or records[0] == records[1]:
        return ()
    return _source_date_labels(material, records)


def _source_date_labels(material, records):
    from datetime import datetime, timedelta, timezone

    timestamps = {row['record']: row['recorded_at'] for row in material['records']}
    local = []
    for record in records:
        stamp = datetime.fromisoformat(timestamps[record].replace('Z', '+00:00'))
        # Stored timestamps without an offset are UTC, as in source_adapter.
        if stamp.tzinfo is None:
            stamp = stamp.replace(tzinfo=timezone.utc)
        local.append(stamp.astimezone(timezone(timedelta(hours=9))))
    dates = [stamp.date() for stamp in local]
    across_years = len({stamp.year for stamp in local}) > 1
    labels = []
    for stamp in local:
        label = f'{stamp.month}月{stamp.day}日'
        if across_years:
            label = f'{stamp.year}年' + label
        if dates.count(stamp.date()) > 1:
            label += stamp.strftime(' %H:%M')
        labels.append(label)
    return tuple(f'記録{record}（{label}）' if labels.count(label) > 1 else label + 'の記録'
                 for record, label in zip(records, labels, strict=True))


def mixed_record_facts(material, units, fixed_units):
    """Attribute independently restored source sentences without dating a jointly authored fact."""
    owners = _original_field_records(material)
    groups, mixed = [], False
    for unit, fixed in zip(units, fixed_units, strict=True):
        roots = unit['evidence']
        records = [owners.get(r['field']) for r in roots]
        quotes = [r['quote'] for r in roots]
        # An explicit sentence choice carries its own original field and clock.
        shown = fixed if isinstance(fixed, tuple) else quotes
        if (fixed and None not in records and len(set(records)) > 1 and len(set(quotes)) > 1
                and ''.join(shown) == unit['fact']):
            mixed = True
            pieces = []
            for record, quote in zip(records, shown, strict=True):
                # Group only consecutive pieces from the same source. Never reorder facts.
                if pieces and pieces[-1][0] == record:
                    pieces[-1][1] += quote
                else:
                    pieces.append([record, quote])
            groups.extend(pieces)
        else:
            # Supplements and free facts from several sources have no single original clock.
            groups.append([_unit_record(owners, unit), unit['fact']])
    if not mixed:
        return (), []
    records = list(dict.fromkeys(record for record, _ in groups if record is not None))
    labels = _source_date_labels(material, records)
    by_record = dict(zip(records, labels, strict=True))
    return labels, [by_record[record] + '：' + body if record is not None else body for record, body in groups]


TITLE_END_MARKS = '。！？!?、，,'


def source_title_key(title):
    """Ignore only trailing sentence separators when comparing original records."""
    return title.rstrip(TITLE_END_MARKS)


def one_sided_source_titles(material, units, *, compare_end_marks=False):
    """Filter literal titles only when independent facts have distinct original owners."""
    field_records = _original_field_records(material)
    owners = {_unit_record(field_records, unit) for unit in units} - {None}
    if len(owners) < 2:
        # Other records may corroborate the same fact without making it a comparison.
        return None
    by_owner = {owner: set() for owner in owners}
    for unit in units:
        for root in unit['evidence']:
            owner = field_records.get(root['field'])
            if owner in by_owner:
                quote = root['quote']
                titles = (source_title_key(quote),) if compare_end_marks else (quote, quote.rstrip('。！？!?'))
                by_owner[owner].update(title for title in titles if 0 < len(title) <= 80)
    shared = set.intersection(*by_owner.values())
    return sorted(set.union(*by_owner.values()) - shared)
