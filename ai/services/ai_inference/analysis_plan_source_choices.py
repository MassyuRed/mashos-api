"""Lossless, request-local abbreviations for PLAN evidence. All offsets are Unicode scalars."""
import hashlib
import json
import re


def choice_scope(request_ref, choices, material=None):
    if type(request_ref) is not str or not request_ref:
        raise ValueError('semantic_plan_request_ref_invalid')
    rows = [[field, key, text] for (field, key), text in choices.items()]
    binding = ['plan-source-choices.v1', request_ref, rows]
    if material and material.get('author_profile') == 'semantic_map.node_local.v4.occurrence.v13':
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
    content_cued = material.get('author_profile') == 'semantic_map.node_local.v4.occurrence.v13'
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
            if material.get('author_profile') == 'semantic_map.node_local.v4.occurrence.v13':
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
    from datetime import datetime, timedelta, timezone

    if len(units) != 2:
        return ()
    field_records = _original_field_records(material)
    records = [_unit_record(field_records, unit) for unit in units]
    if None in records or records[0] == records[1]:
        return ()
    timestamps = {row['record']: row['recorded_at'] for row in material['records']}
    local = []
    for record in records:
        stamp = datetime.fromisoformat(timestamps[record].replace('Z', '+00:00'))
        # Stored timestamps without an offset are UTC, as in source_adapter.
        if stamp.tzinfo is None:
            stamp = stamp.replace(tzinfo=timezone.utc)
        local.append(stamp.astimezone(timezone(timedelta(hours=9))))
    labels = []
    for stamp in local:
        label = f'{stamp.month}月{stamp.day}日'
        if local[0].year != local[1].year:
            label = f'{stamp.year}年' + label
        if local[0].date() == local[1].date():
            label += stamp.strftime(' %H:%M')
        labels.append(label)
    if labels[0] == labels[1]:
        # Distinct records may share an observation minute (or the entire timestamp).
        return tuple(f'記録{record}（{label}）' for record, label in zip(records, labels, strict=True))
    return tuple(label + 'の記録' for label in labels)


def one_sided_source_titles(material, units):
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
                by_owner[owner].update(title for title in (quote, quote.rstrip('。！？!?')) if 0 < len(title) <= 80)
    shared = set.intersection(*by_owner.values())
    return sorted(set.union(*by_owner.values()) - shared)
