"""Lossless, request-local abbreviations for PLAN evidence. All offsets are Unicode scalars."""
import hashlib
import json
import re
import unicodedata


_CONTENT_PLAN_PROFILES = frozenset({
    'semantic_map.node_local.v4.occurrence.v13', 'semantic_map.node_local.v4.occurrence.v14',
    'semantic_map.node_local.v4.occurrence.v15', 'semantic_map.node_local.v4.occurrence.v16',
    'semantic_map.node_local.v4.occurrence.v17'})


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


# The finite reporting verbs already used by the analysis reader. Only the outer
# communication act is classified here; its topic never becomes an occurred event.
_SPEECH_ACT_NEGATIVE = (r'(?:言って|話して|語って|述べて|書いて|伝えて|答えて|説明して)'
                        r'(?:いない(?:です)?|いません(?:でした)?|いなかった(?:です)?)')
_NOMINAL_ARGUMENT = r'[一-鿿々ァ-ヺーA-Za-z0-9]{1,48}(?:の[一-鿿々ァ-ヺーA-Za-z0-9]{1,48}){0,2}'
_RECIPIENT = _NOMINAL_ARGUMENT + r'(?:に|へ)(?:は|も)?'
_SPEECH_TOPIC = _NOMINAL_ARGUMENT + r'を'
# A suru-form with the nominal head 話 is an act of communication. The
# written topic may be a deverbal noun (e.g. a kanji mixed with okurigana).
_TALK_NOUN = r'(?:[一-鿿々ァ-ヺー][ぁ-ゖ]{0,3}){1,24}'
_UNPERFORMED_TALK = r'(?:(?:' + _TALK_NOUN + r'の){1,2})?話をして(?:いない(?:です)?|いません(?:でした)?|いなかった(?:です)?)'
_NONACTION_SPEECH = re.compile(
    r'(?P<self>(?:私|わたし|僕|ぼく|俺|おれ)(?:は|が))?(?:まだ)?'
    + '(?:(?P<recipient>' + _RECIPIENT + ')(?:まだ)?(?:(?:' + _SPEECH_TOPIC
    + ')?(?:まだ)?' + _SPEECH_ACT_NEGATIVE + '|' + _UNPERFORMED_TALK + ')'
    + '|' + _SPEECH_TOPIC + '(?:まだ)?' + _SPEECH_ACT_NEGATIVE + ')')
# A conjunct ending in -sezu supplies a second known non-action, not an
# epistemic or conditional host. Leave arbitrary comma prefixes unclassified.
_NONACTION_CONJUNCT = re.compile(
    '(?:' + _NOMINAL_ARGUMENT + '(?:には|では|は|も|を)){0,2}' + _NOMINAL_ARGUMENT + 'せず')


def recorded_non_actions(material):
    """Verbatim facts that cannot themselves be an OPEN result; never supply a missing actor."""
    fields = {f['field']: f for f in material['fields']}
    result = set()
    for claim in material.get('source_duties', {}).get('claims', ()):
        reading = claim['reading']
        field = fields.get(claim['field'])
        if (not field or reading.get('actor') != 'SELF' or reading.get('modality') != 'fact'
                or reading.get('polarity') != 'negative' or reading.get('time') != 'past'
                or any(reading.get(k) for k in ('possible_content', 'dependent', 'sequence'))):
            continue
        offset = field.get('fragment_scalar_range', [0])[0]
        start, end = (position - offset for position in claim['span'])
        if 0 <= start < end <= len(field['text']):
            result.add((field['field'], field['text'][start:end]))
    direct_recipients = set()
    contextual = []
    for number, field in fields.items():
        if (field.get('source_role') != 'ORIGINAL_INPUT' or field.get('field_path') not in {'memo', 'memo_action'}
                or field.get('fragment_is_complete_field') is False):
            continue
        source = field['text'].strip()
        # Quoted/reported text, a question, or an introduction can frame the
        # following line as someone else's account. Keep these readings open.
        if re.search(r'[「」『』“”‘’"（）()【】!?！？:：]|(?:仮に|もし|例えば|たとえば|例として|によると|によれば|曰く)', source):
            continue
        if re.search(r'(?:言った|話した|語った|説明した|伝えた|言いました|話しました)[。．]\s*'
                     r'|[。．]\s*(?:と|って)|(?:例文|仮定|仮の話|仮説|架空|転記|引用)', source):
            continue
        # An enclosing or later sentence can withdraw the apparent fact.
        # Process only the final complete source statement and never choose
        # the last *returned* candidate if a nonunique or quoted tail was skipped.
        sentences = _sentences(source)
        if not sentences or not source.endswith(sentences[-1]):
            continue
        sentence = sentences[-1]
        clause = sentence.removesuffix('。')
        parts = re.split('[、，]', clause)
        coordinated = len(parts) == 2 and _NONACTION_CONJUNCT.fullmatch(parts[0]) is not None
        if len(parts) != 1 and not coordinated:
            continue
        speech = parts[-1]
        match = _NONACTION_SPEECH.fullmatch(speech)
        if not match:
            continue
        recipient = re.sub(r'(?:に|へ)(?:は|も)?$', '', match['recipient'] or '')
        # A single independent sentence needs no discourse actor. If previous
        # sentences exist, require an explicit SELF or the paired non-action
        # in the action field; do not carry a third person's subject across a stop.
        direct = source == sentence or bool(match['self']) or (coordinated and field['field_path'] == 'memo_action')
        if direct:
            result.update(((number, clause), (number, speech)))
            if recipient and field['field_path'] == 'memo_action' and field.get('record') is not None:
                direct_recipients.add((field['record'], recipient))
        elif recipient and field['field_path'] == 'memo' and field.get('record') is not None:
            contextual.append((field['record'], recipient, number, clause))
    # Use a paired original entry only to recognize an outward communication
    # reading to the same addressee. Never substitute its topic, words or date.
    for record, recipient, number, clause in contextual:
        if (record, recipient) in direct_recipients:
            result.add((number, clause))
    return result


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




def record_plan_owners(material, available=None):
    """Return (original fields, local fields) per independently representable record.

    A correction's record_refs name its dependencies, never its original author.
    Keep room to represent unowned sources separately. Fall back to ordinary
    flexible allocation if source coverage or available nodes do not permit it.
    """
    if (material.get('author_profile') != 'semantic_map.node_local.v4.occurrence.v17'
            or material.get('history_stage')):
        return ()
    records = [row['record'] for row in material.get('records', ())]
    if not 1 <= len(records) <= 12:
        return ()
    fields = material['fields']
    if available is None:
        available = {f['field'] for f in fields if choices_for_field(f)[1]}
    originals = {record: set() for record in records}
    locals_by_record = {record: set() for record in records}
    unowned = set()
    for f in fields:
        number, record = f['field'], f.get('record')
        if number not in available:
            continue
        if record not in originals:
            unowned.add(number)
            continue
        locals_by_record[record].add(number)
        if f['source_role'] == 'ORIGINAL_INPUT':
            originals[record].add(number)
    if not all(originals.values()) or len(records) + len(unowned) > 12:
        return ()
    return tuple((frozenset(originals[r]), frozenset(locals_by_record[r])) for r in records)


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
