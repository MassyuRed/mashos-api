"""Lossless, request-local abbreviations for PLAN evidence. All offsets are Unicode scalars."""
from bisect import bisect_left
from copy import copy
import hashlib
import json
import re
import unicodedata


_CONTENT_PLAN_PROFILES = frozenset({
    'semantic_map.node_local.v4.occurrence.v13', 'semantic_map.node_local.v4.occurrence.v14',
    'semantic_map.node_local.v4.occurrence.v15', 'semantic_map.node_local.v4.occurrence.v16',
    'semantic_map.node_local.v4.occurrence.v17', 'semantic_map.node_local.v4.occurrence.v18', 'semantic_map.node_local.v4.occurrence.v19', 'semantic_map.node_local.v4.occurrence.v20', 'semantic_map.node_local.v4.occurrence.v21', 'semantic_map.node_local.v4.occurrence.v22', 'semantic_map.node_local.v4.occurrence.v23', 'semantic_map.node_local.v4.occurrence.v24'})


_CLOSED_TAG = re.compile(r'</?[A-Za-z_][\w:.-]*(?:\s+[^<>]*)?/?>|/>')
_UNFINISHED_CLOSING_TAG = re.compile(r'</[A-Za-z_][\w:.-]*$')


def source_markup_bound(text, quote):
    return all(m[0] in quote for m in _CLOSED_TAG.finditer(text))


_FACT_KEY_PREFIX = re.compile(r"(?<![A-Za-z0-9_./-])e[1-4]/")


def source_fact_keys_bound(text, quote):
    """Wire labels such as e2/ are metadata unless the selected source literally uses them."""
    matches = _FACT_KEY_PREFIX.findall(text)
    return not matches or set(matches).issubset(_FACT_KEY_PREFIX.findall(quote))


# A leading object separator plus a quoted member or collection begins a
# serialized fragment. A genuine example copied from this source remains legal.
_FACT_MEMBER_START = re.compile(r"""^\s*,\s*['"{\[]""")
_FACT_MEMBER = re.compile(r"""(['"])([^'"\n]*)\1\s*:""")
_FACT_NUMBER_COLLECTION = re.compile(r'(?:\{\s*\d+(?:\s*,\s*\d+)+\s*\}|\[\s*\d+(?:\s*,\s*\d+)+\s*\])')


def fact_starts_with_member(text):
    return bool(_FACT_MEMBER_START.match(text))


def source_fact_members_bound(text, quote):
    """A serialized member or numeric collection needs evidence in this exact root."""
    if fact_starts_with_member(text):
        return text.lstrip() in quote
    if not all(match[0].strip() in quote for match in _FACT_MEMBER.finditer(text)):
        return False
    for match in _FACT_NUMBER_COLLECTION.finditer(text):
        # Insignificant spaces may differ in a displayed mathematical set.
        source = ''.join(quote.split())
        if ''.join(match[0].split()) not in source:
            return False
    return True


def fact_member_suffixes(text, quote, maximum):
    """Possible source continuations after a literal serialized prefix."""
    value = text.lstrip()
    offset = quote.find(value)
    while offset >= 0:
        end = offset + len(value)
        yield quote[end:end + maximum - len(text)]
        offset = quote.find(value, offset + 1)


def source_fact_numeric_bound(text, quote):
    """When the complete fact is purely numeric notation, ground that expression too."""
    if any(c.isalpha() for c in text) or not any(c.isdigit() for c in text):
        return True
    value = ''.join(unicodedata.normalize('NFKC', text).split())
    source = ''.join(unicodedata.normalize('NFKC', quote).split())
    return re.search(r'(?<![0-9])' + re.escape(value) + r'(?![0-9])', source) is not None


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


def source_fact_ranges(quote):
    """Partition an overlong PLAN root into bounded, contiguous source excerpts.

    Prefer complete sentence boundaries. When a single sentence exceeds a
    display part, mark both cut ends explicitly. Wire ranges count Unicode
    scalars from the start of this root, regardless of its enclosing field.
    """
    if len(quote) <= 160:
        return {}
    stops = {0, len(quote)}
    position = 0
    for sentence in _sentences(quote, original_for_overview=True):
        start = quote.find(sentence, position)
        if start < 0 or quote[position:start].strip():
            # An unparsed enclosure or unsupported sentence is not a boundary.
            break
        position = start + len(sentence)
        stops.add(position)
    choices = {}
    start = 0
    while start < len(quote):
        prefix = '' if start in stops else '…'
        limit = start + 160 - len(prefix)
        ends = [end for end in stops if start < end <= limit]
        end = max(ends) if ends else limit - 1
        suffix = '' if end in stops else '…'
        text = quote[start:end].strip()
        if text:
            choices[f'@{start}:{end}'] = prefix + text + suffix
        start = end
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


def _outer_sentences(text, *, original_for_overview=False):
    ends = {'「': '」', '『': '』'}
    if original_for_overview:
        ends.update({'（': '）', '(': ')', '［': '］', '[': ']', '【': '】', '〈': '〉',
            '《': '》', '｛': '｝', '{': '}', '“': '”', '‘': '’', '"': '"', "'": "'", '`': '`'})
    stack, spans = [], []
    escaped = False
    start = 0
    for i, char in enumerate(text):
        if original_for_overview and stack and stack[-1] in ('"', "'", '`'):
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == stack[-1]:
                stack.pop()
            continue
        if original_for_overview and char == "'" and text[i-1:i].isalnum() and text[i+1:i+2].isalnum():
            continue
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
    return [q for q in spans if q]


def _sentences(text, *, original_for_overview=False):
    spans = _outer_sentences(text, original_for_overview=original_for_overview)
    return [q for q in spans if len(q) <= 4000 and (original_for_overview or text.count(q) == 1)
            and not re.search(r'["\\\x00-\x1f]', q)]


_SELF_ACCOUNT_ACTION = re.compile(
    r'(?:自分|自身|私|わたし|僕|ぼく|俺|おれ)の(?:読み|解釈|理解|考え|意見|見方|受け取り方)'
    r'[^。！？]{0,40}?(?:話した|伝えた|述べた|説明した)。')
_SELF_ACCOUNT_LINE = re.compile(
    r'^(?:私|わたし|僕|ぼく|俺|おれ)(?:は|が)[^。！？]+と(?:話した|伝えた|述べた|説明した)。$')
_ASKED_WHO = re.compile(
    r'(?<![一-鿿々ァ-ヺーA-Za-z0-9])([一-鿿々ァ-ヺーA-Za-z0-9]{1,24})の'
    r'(?:希望|意向|要望|意見)を(?:聞いた|聞いて|尋ねた|尋ねて)(?=[。、，])')


def _reported_content_choices(action, memo_sentences, allowed, leaf_quotes):
    """Retrieve what someone actually said, preserving the addressee of a reply.

    A person's own reported account must already be cited by the leaf. For a
    reply without a named speaker, require the immediately preceding contact
    with the participant named in the short action. Return only source quotes.
    """
    results = set()
    action = ''.join(s for s in _sentences(action) if s.endswith('。')
        and not re.search(r'[「」『』“”‘’？?]|(?:予定|つもり|仮に|もし|例えば|たとえば)', s))
    if _SELF_ACCOUNT_ACTION.search(action):
        for sentence in memo_sentences:
            if (_SELF_ACCOUNT_LINE.fullmatch(sentence) and len(sentence) <= 160
                    and not any(mark in sentence for mark in '「」『』“”‘’？?')
                    and any(sentence in quote for quote in leaf_quotes)):
                results.add(sentence)
    participants = _ASKED_WHO.findall(action)
    if participants:
        for contact, reply in zip(memo_sentences, memo_sentences[1:]):
            if not any(re.search(r'(?<![一-鿿々ァ-ヺーA-Za-z0-9])' + re.escape(person) + r'(?:に|へ)(?:連絡した|尋ねた|電話した|聞いた)。$',
                                 contact) for person in participants):
                continue
            if re.search(r'(?:という|との)(?:返事|回答|返答)だった。$', reply):
                passage = contact + reply
                if (len(passage) <= 160 and passage in allowed
                        and not any(mark in passage for mark in '「」『』“”‘’？?')):
                    results.add(passage)
    return results


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




def record_plan_owners(material, available=None, *, merge_anchors=False):
    """Return (original fields, local fields) per independently representable record.

    A correction's record_refs name its dependencies, never its original author.
    Keep room to represent unowned sources separately. Fall back to ordinary
    flexible allocation if source coverage or available nodes do not permit it.
    """
    if (material.get('author_profile') not in {
            'semantic_map.node_local.v4.occurrence.v17', 'semantic_map.node_local.v4.occurrence.v18', 'semantic_map.node_local.v4.occurrence.v19', 'semantic_map.node_local.v4.occurrence.v20', 'semantic_map.node_local.v4.occurrence.v21', 'semantic_map.node_local.v4.occurrence.v22', 'semantic_map.node_local.v4.occurrence.v23', 'semantic_map.node_local.v4.occurrence.v24'}
            or (material.get('history_stage') and not (merge_anchors
                and material['history_stage'].get('kind') == 'MERGE'))):
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


class MergeActionSources:
    """Cover the short original action literally, alongside its own independent account."""

    def __init__(self, action, memo, sentences, allowed, memo_choices=(), context_groups=(), memo_allowed=()):
        self.action_field = action['field']
        self.memo_field = memo['field']
        self.memo_choices = tuple(memo_choices)
        self.action_text = action['text']
        self.action_masks = {q: sum(1 << i for i, s in enumerate(sentences) if s in q)
                             for q in allowed}
        self.memo_bit = 1 << len(sentences)
        # Alternatives in one group express the same retrieval obligation. Two
        # groups can share one bit-covering quote if the source itself joins them.
        self.context_groups = (self.memo_choices, *context_groups)
        if context_groups:
            self.memo_masks = {
                q: self.memo_bit * sum(1 << i for i, group in enumerate(self.context_groups)
                                      if any(witness in q for witness in group))
                for q in memo_allowed if len(q) <= 160 and q not in self.action_text}
        else:
            self.memo_masks = None
        self.required = (self.memo_bit << len(self.context_groups)) - 1
        memo_masks = self.memo_masks.values() if self.memo_masks is not None else (self.memo_bit,)
        masks = set(self.action_masks.values()).union(memo_masks)
        self.minimum_roots = [0]
        for missing in range(1, self.required + 1):
            self.minimum_roots.append(1 + min(self.minimum_roots[missing & ~mask]
                                              for mask in masks if missing & mask))

    def coverage(self, field, quote):
        if field == self.action_field:
            return self.action_masks.get(quote, 0)
        if field == self.memo_field and quote not in self.action_text:
            if self.memo_masks is not None:
                return self.memo_masks.get(quote, 0)
            if not self.memo_choices or (len(quote) <= 160 and any(q in quote for q in self.memo_choices)):
                return self.memo_bit
        return 0

    def missing(self, roots):
        missing = self.required
        for field, quote in roots:
            missing &= ~self.coverage(field, quote)
        return missing

# These are source-retrieval cues for complete quotations. They never assign a
# speaker, label an action as performed, or fabricate a paraphrase or conclusion.
_CONTEXT_NOUN = r'[一-鿿々ァ-ヺーA-Za-z0-9]{1,32}(?:さん|くん|ちゃん)?'
_NAME_START = r'(?<![一-鿿々ァ-ヺーA-Za-z0-9])'
_HEARD_TOPIC = re.compile(_NAME_START + '(' + _CONTEXT_NOUN + r'の(?:話|説明|意見))を(?:聞いた|聴いた|聞きました|聴きました|尋ねた|聞いて|聴いて|尋ねて)(?=[。、，])')
_PARTNER = re.compile(_NAME_START + '(' + _CONTEXT_NOUN + r')(?:と|から|へ|に)'
    + r'(?:' + _CONTEXT_NOUN + r'(?:について|を))?(?:話|相談|聞|聴|伝え|尋ね|語|答え)')
_FINITE_REPORT = r'(?:言った|話した|伝えた|答えた|語った|述べた|説明した|言いました|話しました)'
_WISH_REPORT = re.compile(r'(?:たい|たくない|ほしい|欲しい|ほしくない)と' + _FINITE_REPORT + r'。$')
_TIMED_RECIPIENT = re.compile(_NAME_START + '(' + _CONTEXT_NOUN + r'(?:へ|に))(' + _CONTEXT_NOUN
                              + r')(?:した|して|し)(?=[。、，])')
_TIME_BOUNDARY = re.compile(r'(?:して|えて|って|いて|んで|けて)から|(?:の後|の前|中|直後|直前)に')
_TRIAL_END = re.compile(r'(?:試した|試してみた|試しました|試してみました)。$')
_TRIAL_OBSERVATION = re.compile(r'[^。！？]+と[^。！？]+(?:た|だ)。$')


def _action_context_choices(memo, action, simple, allowed, leaf_index):
    """Locate complete original passages that qualify a condensed action field.

    Two readings can support the same condensed action. Keep the author's
    choice between them. When the menu is not small, retain ordinary free
    allocation. An immutable prior leaf quote is required for trial results.
    """
    text = action['text']
    topics = set()
    partners = set()
    timed_links = set()
    for line in _sentences(text):
        if re.search(r'[「」『』“”？?]|もし|仮に|(?:予定|つもり)(?:だった|です|だ)', line):
            continue
        topics.update(_HEARD_TOPIC.findall(line))
        if re.search(r'希望|意向|要望|願い|望み|ほしい|したい|たいと', line):
            partners.update(_PARTNER.findall(line))
        timed_links.update(_TIMED_RECIPIENT.findall(line))
    leaf_quotes = [row['quote'] for row in leaf_index if isinstance(row, dict)
                   and row.get('field') == memo['field'] and isinstance(row.get('quote'), str)]
    choices = _reported_content_choices(text, simple, allowed, leaf_quotes)
    for line in simple:
        if (len(line) > 160 or line in text or not line.endswith('。')
                or any(symbol in line for symbol in '「」『』“”‘’？?')):
            continue
        # The two fields literally share the named topic. The memoir sentence
        # must contain the outward act, not a guess about what was said.
        if (any(topic + 'を' in line for topic in topics) and
                re.search(r'(?:話|説明|意見)を(?:した|聞いた|述べた|話した)。$', line)):
            choices.add(line)
        # The explicitly named participant in the action recurs at a clause
        # boundary. Keep the entire utterance including its subordinate subject.
        if _WISH_REPORT.search(line) and any(re.search(r'(?:^|[、，])' + re.escape(name)
                + r'(?:は|が|も)', line) for name in partners):
            choices.add(line)
        for recipient, noun in timed_links:
            before, sep, after = line.partition(recipient)
            if sep and _TIME_BOUNDARY.search(before) and noun in after:
                choices.add(line)
    # A recorded trial can supply the outcome of the action's stated check.
    # A leaf that discusses an unrelated trial is insufficient on its own.
    checks = re.search(r'(?:を(?:確認|検証|検査)(?:し|した)|を確かめ(?:て|た)|を試(?:し|した))', text)
    for quote in leaf_quotes if checks else ():
        if len(quote) > 160 or quote not in allowed:
            continue
        # A trial and the immediately following recorded observation need their
        # common source. An open question, future trial or truncated quote does
        # not establish a result, and no part is rewritten as a precondition.
        parts = _outer_sentences(quote, original_for_overview=True)
        if (len(parts) == 2 and ''.join(parts) == quote and _TRIAL_END.search(parts[0])
                and _TRIAL_OBSERVATION.fullmatch(parts[1])
                and not any(mark in quote for mark in ('「', '」', '『', '』', 'かもしれ', 'と思', 'と言', 'と聞'))):
            choices.add(quote)
    return sorted(choices, key=memo['text'].index) if len(choices) <= 4 else []


_DIRECT_SUGGESTION = re.compile(r'(?:よう|[こごそぞとのぼもろ]う|ましょう)と' + _FINITE_REPORT + r'。$')
_CORRECTED_ACTION = re.compile(r'(説明|回答|記述|記載|認識|見解|記録)を(?:修正した|訂正した|直した)。')
_CHECK_TOPIC = re.compile(r'([一-鿿々ァ-ヺー]{2,12}?)(?:の予定|予定|の結果)')
_DEFERRED_RESULT = re.compile(r'(?:かどうか|可否|可能か|できるか)[^。]{0,30}(?:確定|判明|決定|分かる|わかる)')
_UNKNOWN_MOTIVE = re.compile(r'(?:気持ち|理由|意図|動機|事情|考え)[^。]{0,36}(?:分からない|わからない|不明だ|確かめていない)。$')


def _distinct_context_groups(action, simple, allowed, selected, leaf_quotes):
    """Return independent sets of source quotes for decisions and corrections.

    Retain an earlier attributed proposal only when the account explicitly
    identifies its proposer. For a correction, locate the source statement
    being corrected and distinguish it from the motive still left open.
    """
    eligible = {q for q in allowed if len(q) <= 160 and q not in action and q.endswith('。')
                and not any(c in q for c in '「」『』“”‘’？?')}
    groups = []

    def add(candidates):
        group = tuple(dict.fromkeys(q for q in candidates if q in eligible))
        if group and len(group) <= 4 and group not in groups:
            groups.append(group)

    # An acknowledged answer and the earlier request have different chronology.
    # Match the explicitly named subject in both, with a leaf supporting the
    # response; a pending reply or an expected future result cannot satisfy it.
    if re.search(r'(?:返答|回答|返事|返信)(?:の)?後に', action):
        topics = set()
        for request in selected:
            if re.search(r'(?:尋ねた|問い合わせた|聞いた)。$', request):
                topics.update(re.findall(r'([一-鿿々ァ-ヺー]{2,16})を(?:確認|確かめ|照会|教え)', request))
        for topic in sorted(topics):
            if topic not in action:
                continue
            received = re.compile(re.escape(topic) + r'(?:の[一-鿿々ァ-ヺー]{1,16})?が'
                                  r'(?:届き|届いた|知らされ|分かり|判明し)(?:[。、，]|た。)')
            add(q for q in simple if received.search(q) and any(q in witness for witness in leaf_quotes))

    # The stated wish to retain an explanation needs the explanation and its
    # explicit reason. A complete adjacent quote was already selected by LEAF.
    retained = re.search(r'(?:残したい|留めたい|保ちたい)[^。]{0,30}?(説明|記述|解説|文章)を'
                         r'(?:伝えた|話した|述べた)。', action)
    if retained:
        content = re.compile(r'(?:削られた|省かれた|省略された|外された)のは[、，][^。]+'
                             + re.escape(retained[1]) + r'だった。$')
        add(q for q in leaf_quotes if len(parts := _sentences(q)) == 2 and ''.join(parts) == q
            and content.search(parts[0]) and re.search(r'(?:なので|から|ため)[、，][^。]{0,48}'
                r'(?:残したかった|留めたかった|保ちたかった)。$', parts[1]))

    for participant in dict.fromkeys(_ASKED_WHO.findall(action)):
        # A reply already bound to its addressee is required. The relative
        # clause, rather than shared spelling, attributes another proposal.
        if not any(participant in q and re.search(r'(?:返事|回答|返答)だった。$', q) for q in selected):
            continue
        role = re.escape(participant.removesuffix('本人') or participant)
        proposer = re.compile(r'(?:先に|最初に|初めに|以前に)[^。！？]{1,36}'
                              r'(?:勧めた|薦めた|提案した|推した)' + role + r'(?:が|は|も)')
        followup = [line for line in simple if proposer.search(line) and _DIRECT_SUGGESTION.search(line)]
        if followup:
            original = re.compile(r'(?:^|[、，])' + role + r'(?:は|が)')
            before = simple.index(followup[0])
            earlier = [q for q in simple[:before] if original.search(q) and _DIRECT_SUGGESTION.search(q)]
            if len(earlier) == 1:
                add(earlier)
            add(followup)
        topics = _CHECK_TOPIC.findall(action)
        add(q for q in simple if any(topic in q for topic in topics) and _DEFERRED_RESULT.search(q))

    for correction in dict.fromkeys(_CORRECTED_ACTION.findall(action)):
        changed = re.compile(re.escape(correction) + r'を(?:直した|訂正した|修正した)。$')
        for position, (before, current) in enumerate(zip(simple, simple[1:]), 2):
            if not (changed.search(current) and re.search(r'(?:そこ|その|これ|この|それ|指摘)', current)
                    and re.search(r'(?:が話題になった|と指摘された|との指摘があった)。$', before)):
                continue
            passage = before + current
            if passage not in eligible:
                continue
            add([passage])
            after = simple[position] if position < len(simple) else ''
            if re.search(r'(?:^|[、，])(?:その|この)', after) and _UNKNOWN_MOTIVE.search(after):
                # A demonstrative must point to wording in the corrected
                # account. An unrelated unknown in the next topic is optional.
                head = re.search(r'(?:その|この)([一-鿿々ァ-ヺー]{1,20})(?:が|は|を|の)', after)
                if head and head[1] in passage:
                    add([after])
    # Never force a subset chosen by iteration order in a crowded record.
    return tuple(groups) if len(groups) <= 4 else ()


def uses_speaker_context(version):
    return version in ('cocolon.analysis.merge_wire.v8', 'cocolon.analysis.merge_wire.v9')


_NARRATOR = frozenset(('私', 'わたし', '僕', 'ぼく', '俺', 'おれ', '自分'))
_NAMED_SUBJECT = re.compile(r'(?:^|[、，])(' + _CONTEXT_NOUN + r')(?:は|が|も)')
_TURN = re.compile(r'と(?:' + _FINITE_REPORT + r'|聞いた|尋ねた|頼んだ|返した)|と(?:いう|の)(?:回答|返事|返答)だった')
_SELF_REPLY = re.compile(r'^(?:そこで[、，]?|それに対して[、，]?|一方[、，]?)?(?:私|わたし|僕|ぼく|俺|おれ)(?:は|が)[^。！？]*と' + _FINITE_REPORT + r'。$')
_POSITION = re.compile(r'希望|望ん|望む|願い|願って|意向|要望|ほしい|欲し|たい|たくない|つもり|賛成|同意|引き受け|了承|勝手に決め|落ち着かな')
_QUALIFIED_POSITION = re.compile(r'ことと|ことは別|わけではな|だけではな|とは限ら|一方|ただ[、，]|条件|場合')
_REPORTED_INTERPRETATION = re.compile(r'(?:そう|そういう意味に|そのように|その意味で)(?:受け取|受け止め|捉え|とらえ|解釈|理解)')


def _speaker_context_groups(memo, action, selected, allowed):
    """Keep the narrator's own qualified reply beside a reported participant's wish.

    Bind only full quotations in the same paragraph. An explicit interpretation
    of the narrator's stance needs the statement immediately before it. These
    are source passages, not assertions about the other person's intentions.
    """
    partner_wishes = {name: [q for q in selected if _WISH_REPORT.search(q)
                      and re.search(r'(?:^|[、，])' + re.escape(name) + r'(?:は|が|も)', q)]
                      for name in set(_PARTNER.findall(action))}
    speakers = [name for name, wishes in partner_wishes.items() if wishes]
    if len(speakers) != 1:
        return ()
    partner, = speakers
    replies = set()
    references = set()
    for paragraph in memo.splitlines():
        lines = _outer_sentences(paragraph, original_for_overview=True)
        pending = False
        for i, line in enumerate(lines):
            if line in partner_wishes[partner]:
                pending = not re.search(r'仮に|もしも|例えば|たとえば|仮定', line)
            elif pending and _SELF_REPLY.fullmatch(line):
                following = lines[i+1] if i+1 < len(lines) else ''
                if (_POSITION.search(line) and _POSITION.search(following)
                        and _QUALIFIED_POSITION.search(following)
                        and not any(name not in _NARRATOR for name in _NAMED_SUBJECT.findall(following))):
                    replies.add(line + following)
                elif _POSITION.search(line):
                    replies.add(line)
                pending = False
            elif _TURN.search(line):
                pending = False
            if (i and re.search(r'(?:^|[、，])'+re.escape(partner)+r'(?:は|が|も)', line)
                    and _REPORTED_INTERPRETATION.search(line) and _POSITION.search(lines[i-1])
                    and not any(name not in _NARRATOR for name in _NAMED_SUBJECT.findall(lines[i-1]))
                    and (not _TURN.search(lines[i-1]) or _SELF_REPLY.fullmatch(lines[i-1]))):
                references.add(lines[i-1] + line)

    def unique_passage(candidates):
        if len(candidates) == 1:
            q, = candidates
            if len(q) <= 160 and q in allowed and q not in action and not any(c in q for c in '「」『』“”‘’？?'):
                return (q,)
        return ()

    reply = unique_passage(replies)
    if not reply:
        return ()
    referent = unique_passage(references)
    return (reply, referent) if referent and referent != reply else (reply,)


def uses_attributed_context(version):
    return version == 'cocolon.analysis.merge_wire.v9'


_NARRATOR_SUBJECT = r'(?:私|わたし|僕|ぼく|俺|おれ)(?:は|が)'
_NAMED_ACCOUNT = re.compile(r'^(' + _NOMINAL_ARGUMENT + r')(?:は|が)[、，]?[^。！？]+と' + _FINITE_REPORT + r'。$')
_RECEIVED_ACCOUNT = re.compile(r'^' + _NARRATOR_SUBJECT + r'[、，]?(?:その|この)(?:言葉|発言|説明|意見|感想|話)'
                               r'を(?:聞|聴|読|受け)')


def _attributed_account_groups(selected, leaf_quotes, allowed, memo):
    """Preserve a separately attributed remark and the narrator's uncertainty about it.

    The first-person account already selected for the short action is independent
    of the other person's actual words. A same-paragraph leaf passage must state
    both those words and the narrator's own explicitly unresolved interpretation
    of the named speaker. Keep the two sentences together in their original order.
    """
    if not any(_SELF_ACCOUNT_LINE.fullmatch(q) for q in selected):
        return ()
    candidates = set()
    for quote in leaf_quotes:
        if (len(quote) > 160 or quote not in allowed
                or any(mark in quote for mark in '「」『』“”‘’？?\r\n')):
            continue
        parts = _outer_sentences(quote, original_for_overview=True)
        if len(parts) != 2 or ''.join(parts) != quote:
            continue
        words, response = parts
        speaker = _NAMED_ACCOUNT.fullmatch(words)
        if (not speaker or speaker[1] in _NARRATOR or not _RECEIVED_ACCOUNT.match(response)
                or re.search(r'もし|仮に|たとえば|例えば|と仮定|と(?:言った|述べた|話した)と', words)):
            continue
        # An unresolved question about this named speaker's meaning anchors
        # the uptake. An unrelated person's uncertainty is not interchangeable.
        if (re.search(r'[、，]' + re.escape(speaker[1]) + r'(?:は|が)[^。]+'
                      r'(?:のか|かどうか|意図|真意)[^。]*(?:分からない|わからない|不明だ)。$', response)
                and memo.count(quote) == 1):
            candidates.add(quote)
    return (tuple(candidates),) if len(candidates) == 1 else ()


def merge_action_sources(material, owners, *, context_sources=False, distinct_context_sources=False,
                         speaker_context_sources=False, attributed_context_sources=False):
    """For the new MERGE only, reserve already selectable original sentences.

    A passage can record proposed, declined, completed or reported actions, even
    with different actors. Preserve its exact text without classifying any of them.
    A node has two units of four roots. Extra contexts reserve only literals
    that can fit alongside all action sentences in these eight slots.
    """
    if (not owners or material.get('history_stage', {}).get('kind') != 'MERGE'
            or material.get('author_profile') != 'semantic_map.node_local.v4.occurrence.v24'
            or material.get('map_corrections')):
        return {}
    records = {row['record']: [] for row in material['records']}
    excluded = {row.get('record') for row in material.get('emlis_source_materials', ())
                if any(row.get(k) for k in ('source_updates', 'conflicts', 'unresolved_sources'))}
    for field in material['fields']:
        record = field.get('record')
        if record not in records:
            # An unowned later correction may relate to more than one original.
            return {}
        records[record].append(field)
    manifest = {f['field']: f for f in material.get('field_manifest', ())}
    for item in manifest.values():
        if item.get('record') not in records:
            return {}
        if item.get('source_role') != 'ORIGINAL_INPUT' or item.get('field_path') not in {'memo', 'memo_action'}:
            excluded.add(item['record'])
    result = {}
    for record, fields in records.items():
        if record in excluded or len(fields) != 2:
            continue
        by_path = {f['field_path']: f for f in fields}
        if set(by_path) != {'memo', 'memo_action'}:
            continue
        if any(f['source_role'] != 'ORIGINAL_INPUT' or f.get('supplement') is not None
               or f.get('fragment_is_complete_field') is not True
               or f.get('fragment_scalar_range') != [0, len(f['text'])]
               or manifest.get(f['field'], {}).get('text_sha256') != hashlib.sha256(f['text'].encode()).hexdigest()
               for f in fields):
            continue
        action, memo = by_path['memo_action'], by_path['memo']
        if not 0 < len(action['text']) <= 160 < len(memo['text']):
            continue
        sentences, allowed = choices_for_field(action)
        if (not 1 <= len(sentences) <= 4 or ''.join(sentences) != action['text']
                or not all(s.endswith(('。', '!', '?', '！', '？')) and any(c.isalnum() for c in s) for s in sentences)):
            continue
        memo_sentences, memo_allowed = choices_for_field(memo)
        if any(s not in action['text'] for s in memo_sentences):
            selected = (_action_context_choices(memo, action, memo_sentences, memo_allowed,
                        material.get('leaf_source_index', ())) if context_sources else ())
            groups = ()
            if distinct_context_sources:
                leaf_quotes = [row['quote'] for row in material.get('leaf_source_index', ())
                               if isinstance(row, dict) and row.get('field') == memo['field'] and isinstance(row.get('quote'), str)]
                groups = _distinct_context_groups(action['text'], memo_sentences, memo_allowed, selected, leaf_quotes)
                if groups and not any(q not in action['text'] for q in selected):
                    selected, groups = groups[0], groups[1:]
            row = MergeActionSources(action, memo, sentences, allowed, selected, groups, memo_allowed)
            if groups and row.minimum_roots[row.required] > 8:
                row = MergeActionSources(action, memo, sentences, allowed, selected)
            extra = ()
            if speaker_context_sources:
                extra = _speaker_context_groups(memo['text'], action['text'], selected, memo_allowed)
            if attributed_context_sources and distinct_context_sources:
                extra += _attributed_account_groups(selected, leaf_quotes, memo_allowed, memo['text'])
            if extra:
                expanded = MergeActionSources(action, memo, sentences, allowed, selected,
                                              (*row.context_groups[1:], *extra), memo_allowed)
                if expanded.minimum_roots[expanded.required] <= 8:
                    row = expanded
            result[record] = row
    return result



def compact_action_pairs(material):
    """Keep a bounded original action available beside a longer original account.

    A short pair may simply restate the same observation. Updates, excerpts
    and history have separate provenance and allocation rules. Preserve their
    existing author choices. Never infer that two acts or actors are identical.
    """
    if (material.get('author_profile') not in {'semantic_map.node_local.v4.occurrence.v18', 'semantic_map.node_local.v4.occurrence.v19', 'semantic_map.node_local.v4.occurrence.v20', 'semantic_map.node_local.v4.occurrence.v21', 'semantic_map.node_local.v4.occurrence.v22', 'semantic_map.node_local.v4.occurrence.v23', 'semantic_map.node_local.v4.occurrence.v24'}
            or material.get('history_stage') or material.get('map_corrections')
            or not 1 <= len(material.get('records', ())) <= 12):
        return {}
    fields_by_record = {}
    for field in material['fields']:
        record = field.get('record')
        if record is None:
            return {}
        fields_by_record.setdefault(record, []).append(field)
    for entry in material.get('emlis_source_materials', ()):
        if entry.get('conflicts') or entry.get('unresolved_sources') or entry.get('source_updates'):
            fields_by_record.pop(entry.get('record'), None)
    pairs = {}
    wire_bytes = 0
    for record, fields in fields_by_record.items():
        if len(fields) != 2 or any(f['source_role'] != 'ORIGINAL_INPUT'
                or f.get('fragment_scalar_range') or f.get('fragment_is_complete_field') is False for f in fields):
            continue
        by_path = {f['field_path']: f for f in fields}
        if set(by_path) != {'memo_action', 'memo'}:
            continue
        action, thought = by_path['memo_action'], by_path['memo']
        text = action['text']
        if not 0 < len(text) <= 160 < len(thought['text']):
            continue
        sentences = _sentences(text)
        if (not 1 <= len(sentences) <= 4 or ''.join(sentences) != text
                or not all(q.endswith(('。', '!', '?', '！', '？')) and any(c.isalnum() for c in q) for q in sentences)):
            continue
        thought_parts = [q for q in _sentences(thought['text']) if len(q) <= 240]
        alternatives = [q for q in thought_parts if q not in text]
        if len(thought_parts) < 2 or not alternatives:
            continue
        # The three replies share 4096 tokens. UTF-8 byte lengths upper-bound
        # the tokenizer cost of a literal. Keep an ordinary completion path
        # without requiring a large cohort to transcribe every compact field.
        shortest = min(alternatives, key=lambda q: len(q.encode('utf-8')))
        extra = json.dumps({'quote': shortest, 'field': thought['field']},
                           separators=(',', ':'), ensure_ascii=False)
        wire_bytes += len(text.encode('utf-8')) + len(extra.encode('utf-8')) + 1
        if wire_bytes > 4096 // 4:
            return {}
        pairs[record] = (action['field'], text, thought['field'])
    return pairs if pairs and record_plan_owners(material) else {}


class PlanReadingRegions:
    """Index complete original sentences in bounded, independently selectable source regions."""

    def __init__(self, field, groups, allowed, *, open_reports=()):
        self.field = field['field']
        self.open_reports = tuple(open_reports)
        text = field['text']
        positions = {quote: text.index(quote) for quote in allowed}
        self.intervals = {q: (start, start + len(q)) for q, start in positions.items()}
        self.ranges = [[positions[group[0]], positions[group[-1]] + len(group[-1])] for group in groups]
        self.openings = [group[0][:12] for group in groups]
        self.required = (1 << len(groups)) - 1
        # A two-sentence citation can genuinely cover both sides of a boundary.
        # Index only the few boundaries, without rescanning the source for every candidate.
        self.coverage = {}
        endpoints = [([positions[s] for s in group], [positions[s] + len(s) for s in group]) for group in groups]
        for quote, (start, end) in self.intervals.items():
            mask = 0
            for index, (starts, ends) in enumerate(endpoints):
                first = bisect_left(starts, start)
                if first < len(ends) and ends[first] <= end:
                    mask |= 1 << index
            self.coverage[quote] = mask
        self._index_root_counts()

    def _index_root_counts(self):
        available = set(self.coverage.values()) - {0}
        self.minimum_roots = {0: 0}
        for missing in range(1, self.required + 1):
            self.minimum_roots[missing] = 1 + min(self.minimum_roots[missing & ~mask]
                for mask in available if mask & missing)

    def requiring(self, sentence):
        # A node with an exclusively owned field is the only legal place
        # for that field at the twelve-record limit. Index the union so a
        # single quote can satisfy both the old region and the new sentence.
        result = copy(self)
        bit = self.required + 1
        result.required |= bit
        result.coverage = {quote: mask | (bit if sentence in quote else 0)
                           for quote, mask in self.coverage.items()}
        result._index_root_counts()
        return result

    def description(self):
        row = dict(field=self.field, scalar_ranges=self.ranges, opening_cues=self.openings)
        if self.open_reports:
            row['unconfirmed_report_ranges'] = [list(self.intervals[q]) for q in self.open_reports]
        return row

    def missing(self, units):
        mask = self.required
        for unit in units:
            for field, quote in unit:
                if field == self.field:
                    mask &= ~self.coverage.get(quote, 0)
        return mask

    def can_reuse(self, completed_units, current, field, quote):
        if not self.open_reports or not any((field, quote) in unit for unit in completed_units):
            return True
        # The model may choose an entirely different focus or reuse a genuinely
        # necessary source after the separate reported status is represented.
        cited = [s for unit in (*completed_units, current) for f, s in unit if f == self.field]
        return all(any(sentence in s for s in cited) for sentence in self.open_reports)

    def adds_text(self, unit, field, quote):
        if field != self.field or quote not in self.intervals:
            return True
        start, end = self.intervals[quote]
        for left, right in sorted(self.intervals[prior] for f, prior in unit
                                  if f == field and prior in self.intervals):
            if left > start:
                break
            start = max(start, right)
            if start >= end:
                return False
        return True


# An explicit, linked schedule and current state belongs to one original account.
# Match the stated calendar construction, never a subject, event, or domain word.
_FUTURE_TIME = (r'(?:明日|あした|明後日|あさって|来週|翌週|来月|翌月|来年|翌年|'
                r'次の(?:週|月曜|火曜|水曜|木曜|金曜|土曜|日曜)(?:日)?|'
                r'[0-9０-９一二三四五六七八九十]+(?:日|週間|か月|ヶ月|年)後)')
_LINKED_SCHEDULE = re.compile(_FUTURE_TIME + r'(?:の予定)?(?:なので|だから|だが|のため|'
    r'(?:に|と)(?:決めた|決まった|定めた)(?:が|ので|けれど(?:も)?))$')
_STILL_NOW = re.compile(r'^(?:まだ|いまだに).*(?:て|で)(?:いない|いません|おらず)|'
    r'^(?:今は|いまは|現在は|現時点では).+(?:ある|いる|ない|います|あります|いません)')


_UNCONFIRMED_REPORT = re.compile(r'(?:た|だ|る)か(?:どうか)?(?:は|を|も)?(?:まだ)?'
    r'(?:聞いて|確認して|確かめて|尋ねて)(?:いない|いません|いなかった)(?:。|！|!)$')


# The author relates a past observation to the limits of what it establishes
# now. Both clauses belong to the same source; never infer the current outcome.
_PAST_ACCOUNT = re.compile(r'以前|かつて|当時|前回|先日|先月|先週|昨[日年]|去年|過去|'
    r'[0-9０-９一二三四五六七八九十]+(?:日|週間|か月|年)前')
_CURRENT_REFERENCE = re.compile(r'現時点|現在|今(?:は|も|の|なお|でも)|いま(?:は|も|の)')
_DENIED_INFERENCE = re.compile(
    r'(?:(?:意味|証拠|根拠|証明)(?:に(?:は|も)?(?:していない|していません|ならない|なりません)|では(?:ない|ありません))'
    r'|(?:示す|意味する|保証する)(?:もの|わけ)では(?:ない|ありません)'
    r'|とは(?:限らない|限りません|言えない|言えません|断定できない|判断できない))[。！!]$')


def _limits_current_inference(sentence):
    if any(mark in sentence for mark in ('「', '」', '『', '』', '？', '?', 'もし', '仮に')):
        return False
    for boundary in re.finditer(r'(?:が|けれど(?:も)?|ものの)[、，,]', sentence):
        current = _CURRENT_REFERENCE.search(sentence, boundary.end())
        if (_PAST_ACCOUNT.search(sentence, 0, boundary.start()) and current
                and _DENIED_INFERENCE.search(sentence, current.start())):
            return True
    return False


def prior_evidence_limits(material):
    """Return a unique selectable prior/current qualification per complete original record."""
    if (material.get('author_profile') not in {'semantic_map.node_local.v4.occurrence.v22', 'semantic_map.node_local.v4.occurrence.v23', 'semantic_map.node_local.v4.occurrence.v24'}
            or material.get('history_stage') or material.get('map_corrections')
            or any(entry.get(key) for entry in material.get('emlis_source_materials', ())
                   for key in ('source_updates', 'conflicts', 'unresolved_sources'))):
        return {}
    fields = material['fields']
    if any(field['source_role'] != 'ORIGINAL_INPUT' or field.get('fragment_scalar_range')
           or field.get('fragment_is_complete_field') is False for field in fields):
        return {}
    by_record = {}
    for field in fields:
        if field['field_path'] != 'memo':
            continue
        simple, _ = choices_for_field(field)
        found = {sentence for sentence in _sentences(field['text'], original_for_overview=True)
                 if sentence in simple and _limits_current_inference(sentence)}
        if found:
            by_record.setdefault(field['record'], set()).update(found)
    return {record: found for record, found in by_record.items() if len(found) == 1}


def _scheduled_current_state(sentence):
    # Include a reported claim only with its speaker when selected normally. We
    # reserve no source slot for quoted dialogue, guesses, hypotheticals, or a
    # wish. The binding below spans the full original sentence, not the clause.
    if any(mark in sentence for mark in ('「', '」', '『', '』', '？', '?', 'もし', '仮に')):
        return False
    parts = re.split('[、，,]', sentence)
    return any(_LINKED_SCHEDULE.search(left) and _STILL_NOW.match(right)
               for left, right in zip(parts, parts[1:]))


# Compare only directly written elapsed measurements of a repeated finite action.
# An absolute clock, a price and a calendar day are not elapsed durations.
_DURATION_NUMBER = r'[0-9０-９一二三四五六七八九十百千]+'
_ELAPSED = re.compile(r'(?<![0-9０-９一二三四五六七八九十百千時間.．:：])' + _DURATION_NUMBER
    + r'(?:時間(?:半)?|分(?:間)?|秒(?:間)?|日間|週間)(?:ほど|程|くらい|ぐらい|程度|だけ|も)?')
_FINISHED = re.compile(r'(?P<stem>[一-鿿々]+)(?P<ending>[ぁ-ゖ]{0,5}[ただ])'
                       r'(?=[。！!?、，,]|が[、，,]|けれど(?:も)?[、，,]|ものの[、，,])')


_NONACTUAL = re.compile(r'そうだった|はずだった|つもりだった|予定だった|らしかった|かもしれ')
_SUBJECT = re.compile(r'([一-鿿々ァ-ヶー]+(?:さん|たち)?)(?:が|は)')


def _completed_form(ending):
    return (ending not in {'だった', 'でした'}
            and not any(mark in ending for mark in ('かった', 'そうだった', 'らしかった')))


def _measured_predicates(sentence):
    if any(mark in sentence for mark in ('「', '」', '『', '』', '？', '?')):
        return
    for elapsed in _ELAPSED.finditer(sentence):
        if elapsed[0] == '十分':
            continue
        preceding = sentence[:elapsed.start()]
        if re.search(r'(?:仮に|もし|なら|れば|たら)', preceding):
            continue
        act = _FINISHED.match(sentence, elapsed.end())
        # Consequences of a plan, wish, guess, or hearsay remain ordinary source choices.
        if (act and _completed_form(act['ending']) and not _NONACTUAL.search(sentence[elapsed.start():act.end()])
                and not re.search(r'仮に|もし', sentence)):
            # Do not align a separately named actor with an unowned action.
            clause = re.split('[、，,。]', preceding)[-1]
            subject = _SUBJECT.findall(clause)
            yield act[0], act['stem'], elapsed[0], tuple(subject)


def _action_support(action, stem, duration, subjects):
    # Read the original action separately. A matching stem must belong to a
    # completed predicate, and the duration must be in that same clause to
    # establish a measured action in the compact field.
    expr = re.compile(re.escape(stem) + r'(?P<ending>[ぁ-ゖ]{0,5}[ただ])(?=[。！!?、，,]|が[、，,]|けれど(?:も)?[、，,])')
    completed = False
    measured = False
    for sentence in _sentences(action):
        for clause in re.findall(r'[^。！!?、，,]+[。！!?、，,]', sentence):
            if _NONACTUAL.search(clause) or re.search(r'仮に|もし|なら|れば|たら|[「」『』]', clause):
                continue
            for act in expr.finditer(clause):
                preceding = clause[:act.start()]
                elapsed = list(_ELAPSED.finditer(preceding))
                if (re.search(r'[一-鿿々]$', preceding) and not any(d.end() == len(preceding) for d in elapsed)
                        or not _completed_form(act['ending']) or any(name not in preceding for name in subjects)
                        or not subjects and re.search(r'[一-鿿々ァ-ヶー](?:さん|たち)?が', preceding)):
                    continue
                completed = True
                for d in elapsed:
                    between = clause[d.end():act.start()]
                    # A directly governed object is allowed. Another act, a
                    # waiting period, or a temporal modifier cannot supply its measure.
                    if d[0] == duration and (not between or (re.fullmatch(r'[一-鿿々ぁ-ゖァ-ヶー]{1,16}を', between)
                            and not re.search(r'[をのがはもへにでと後前]|から|まで', between[:-1]))):
                        measured = True
    return completed, measured


def _paired_measurements(fields):
    by_record = {}
    for field in fields:
        by_record.setdefault(field['record'], {})[field['field_path']] = field['text']
    by_predicate = {}
    for record, originals in by_record.items():
        if set(originals) != {'memo', 'memo_action'}:
            continue
        for sentence in _sentences(originals['memo']):
            for predicate, stem, duration, subjects in _measured_predicates(sentence):
                completed, measured = _action_support(originals['memo_action'], stem, duration, subjects)
                if completed:
                    rows = by_predicate.setdefault((predicate, subjects), {})
                    rows.setdefault(record, []).append((sentence, measured))
    result = {}
    for records in by_predicate.values():
        # Competing timed occurrences within one record have no unique pairing.
        if len(records) < 2 or any(len(rows) != 1 for rows in records.values()):
            continue
        if any(rows[0][1] for rows in records.values()):
            for record, rows in records.items():
                result.setdefault(record, set()).add(rows[0][0])
    return result


# A repeated topic is only a reason to keep the person's exact words visible.
# It is never used to identify a person, resolve a pronoun, or infer an event.
_SOURCE_TOPIC = re.compile(r'^([一-鿿々ァ-ヺーぁ-ゖA-Za-z0-9]{1,32}?)(?:は|が)')
_SOURCE_LIMIT = re.compile(r'(?:いない|いません|なかった|していなかった|わからない|分からない|わかりません|分かりません|不明|未確認|ではない|ではありません)(?:です)?。$')


def repeated_qualified_topics(fields):
    """Return complete accounts whose named topic and qualification recur in paired records."""
    by_record = {}
    for field in fields:
        by_record.setdefault(field['record'], {})[field['field_path']] = field
    by_topic = {}
    for record, paths in by_record.items():
        if set(paths) != {'memo', 'memo_action'}:
            continue
        action = paths['memo_action']['text']
        action_notes = _outer_sentences(action, original_for_overview=True)
        memo = paths['memo']
        for sentence in _sentences(memo['text'], original_for_overview=True):
            match = _SOURCE_TOPIC.match(sentence)
            if (not match or not _SOURCE_LIMIT.search(sentence)
                    or any(mark in sentence for mark in ('「', '」', '『', '』', '?', '？', 'もし', '仮に'))):
                continue
            topic = match[1]
            if topic in ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ', '自分', '本人', 'これ', 'それ', 'あれ'):
                continue
            if any(note.startswith((topic + 'の', topic + 'は', topic + 'が'))
                   and _SOURCE_LIMIT.search(note) for note in action_notes):
                by_topic.setdefault(topic, {}).setdefault(record, set()).add(sentence)
    # Multiple possible accounts in a field leave its focus with the author.
    # Never enforce only the uncomplicated side of such an ambiguous pair.
    candidates = {}
    for records in by_topic.values():
        if len(records) < 2:
            continue
        for record, sentences in records.items():
            candidates.setdefault(record, set()).update(sentences)
    result = {}
    for records in by_topic.values():
        if len(records) >= 2 and all(len(candidates[record]) == 1 for record in records):
            result.update((record, next(iter(sentences))) for record, sentences in records.items())
    return result


def plan_reading_regions(material, pairs):
    """Reserve a few separated portions of an ordinary original, without assigning their meaning."""
    if (material.get('author_profile') not in {'semantic_map.node_local.v4.occurrence.v20', 'semantic_map.node_local.v4.occurrence.v21', 'semantic_map.node_local.v4.occurrence.v22', 'semantic_map.node_local.v4.occurrence.v23', 'semantic_map.node_local.v4.occurrence.v24'}
            or material.get('history_stage') or material.get('map_corrections') or not record_plan_owners(material)):
        return {}
    if any(f['source_role'] != 'ORIGINAL_INPUT' or f.get('fragment_scalar_range')
           or f.get('fragment_is_complete_field') is False for f in material['fields']):
        return {}
    if any(entry.get(k) for entry in material.get('emlis_source_materials', ())
           for k in ('source_updates', 'conflicts', 'unresolved_sources')):
        return {}
    regions = {}
    prioritized = {}
    extra_wire_bytes = 0
    # Bound the shortest complete route for every record together, including existing action transcriptions.
    def wire_size(field, quote):
        return len(json.dumps(dict(quote=quote, field=field), ensure_ascii=False, separators=(',', ':')).encode('utf-8')) + 1

    wire_bytes = sum(wire_size(field, action) for field, action, _ in pairs.values())
    for row in material['records']:
        record = row['record']
        fields = [f for f in material['fields'] if f['record'] == record]
        paths = {f['field_path']: f for f in fields}
        if len(fields) != 2 or set(paths) != {'memo', 'memo_action'} or not paths['memo_action']['text']:
            continue
        memo, action = paths['memo'], paths['memo_action']
        simple, allowed = choices_for_field(memo)
        distinct = set(simple)
        independent = [s for s in _sentences(memo['text'], original_for_overview=True)
                       if s in distinct and s not in action['text'] and s.endswith(('。', '!', '?', '！', '？'))]
        count = min(3, len(independent) // 2)
        # Each abridged cue must be one that the ordinary PLAN source table actually exposes.
        def cheapest(group):
            return min(wire_size(memo['field'], cue) for q in group
                for cue in (_content_choices(memo['text'], q, allowed, {}, memo['field']) or [q]))

        if count < 2:
            if record in pairs:
                wire_bytes += cheapest([s for s in simple if s not in action['text']])
            continue
        # Prefer real paragraph boundaries. A single paragraph can still contain several complete observations.
        paragraphs = [paragraph for paragraph in re.split(r'\n\s*\n', memo['text']) if paragraph]
        blocks = [[s for s in independent if s in paragraph] for paragraph in paragraphs]
        blocks = [block for block in blocks if block]
        if len(blocks) < count:
            blocks = [[s] for s in independent]
        groups = [sum(blocks[i*len(blocks)//count:(i+1)*len(blocks)//count], []) for i in range(count)]
        if any(len(group) < 2 for group in groups):
            if record in pairs:
                wire_bytes += cheapest(independent)
            continue
        wire_bytes += sum(cheapest(group) for group in groups)
        regions[record] = PlanReadingRegions(memo, groups, allowed)
        if material.get('author_profile') in {'semantic_map.node_local.v4.occurrence.v21', 'semantic_map.node_local.v4.occurrence.v22', 'semantic_map.node_local.v4.occurrence.v23', 'semantic_map.node_local.v4.occurrence.v24'}:
            # Prefer the whole temporal statement within its existing reading
            # portion. Competing statements leave the choice within that portion free.
            preferred = []
            for group in groups:
                linked = [sentence for sentence in group if _scheduled_current_state(sentence)]
                preferred.append(linked if len(linked) == 1 else group)
            open_reports = [s for s in independent if _UNCONFIRMED_REPORT.search(s)
                            and not any(mark in s for mark in ('「', '」', '『', '』', '?', '？'))]
            # A second unit accepts four roots. Keep room for a distinct event
            # and a repeated source when asking for outstanding report evidence.
            if len(open_reports) > 2:
                open_reports = []
            if preferred != groups or open_reports:
                extra_wire_bytes += sum(cheapest(g) for g in preferred) - sum(cheapest(g) for g in groups)
                prioritized[record] = PlanReadingRegions(memo, preferred, allowed, open_reports=open_reports)
    if wire_bytes > 4096 // 4:
        return {}
    if wire_bytes + extra_wire_bytes <= 4096 // 4:
        regions.update(prioritized)
    return regions


def whole_plan_sources(material, owners):
    """Find independently representable complete source sentences anywhere in an ordinary PLAN."""
    if (material.get('author_profile') not in {'semantic_map.node_local.v4.occurrence.v22', 'semantic_map.node_local.v4.occurrence.v23', 'semantic_map.node_local.v4.occurrence.v24'}
            or not owners or len(owners) > 12 or material.get('history_stage') or material.get('map_corrections')):
        return {}
    fields = material['fields']
    if (any(f['source_role'] != 'ORIGINAL_INPUT' or f.get('fragment_scalar_range')
            or f.get('fragment_is_complete_field') is False for f in fields)
            or any(entry.get(k) for entry in material.get('emlis_source_materials', ())
                   for k in ('source_updates', 'conflicts', 'unresolved_sources'))):
        return {}
    def selectable(field, sentence):
        simple, allowed = choices_for_field(field)
        # Every legal root that covers the witness must keep it visible in
        # NODES. A different root may not consume the same leading position.
        return (sentence in simple and not any(
            (sentence in quote and len(quote) > 160)
            or (quote != sentence and sentence.startswith(quote)) for quote in allowed))

    measured = _paired_measurements(fields)
    limits = prior_evidence_limits(material)
    required, qualified_limits, selected_measurements = {}, {}, set()
    for field in fields:
        if field['field_path'] != 'memo':
            continue
        record = field['record']
        found = measured.get(record, set()) | limits.get(record, set())
        # Avoid prioritizing one of several qualifications on the same field.
        if len(found) != 1:
            continue
        sentence, = found
        if not selectable(field, sentence):
            continue
        number = field['field']
        required[number] = sentence
        if sentence in limits.get(record, ()):
            qualified_limits[number] = sentence
        if sentence in measured.get(record, ()):
            selected_measurements.add(record)
    # If one measurement cannot be preserved, do not prioritize the other
    # as though the two original observations were both represented.
    if selected_measurements != set(measured):
        required = qualified_limits
    def fits(sources):
        # At most one extra unit, within the existing shared completion budget.
        return len(sources) <= 4 and sum(
            len(json.dumps(dict(quote=q, field=f), ensure_ascii=False).encode('utf-8')) + 1
            for f, q in sources.items()) <= 4096 // 8

    required = required if fits(required) else {}
    if material.get('author_profile') == 'semantic_map.node_local.v4.occurrence.v24':
        topics = repeated_qualified_topics(fields)
        combined = dict(required)
        for field in fields:
            sentence = topics.get(field['record'])
            if field['field_path'] != 'memo' or sentence is None:
                continue
            number = field['field']
            if number in required and required[number] != sentence:
                return required
            if not selectable(field, sentence):
                return required
            combined[number] = sentence
        if fits(combined):
            return combined
    return required


def owner_source_regions(material, owners, regions, required):
    """At exactly twelve owners every source has just one possible node."""
    if len(owners) != 12 or not required:
        return regions
    result = dict(regions)
    for field in material['fields']:
        number = field['field']
        if number not in required:
            continue
        record = field['record']
        region = regions.get(record)
        if region is None:
            _, allowed = choices_for_field(field)
            region = PlanReadingRegions(field, [], allowed)
            # No reading regions previously applied here. Keep the record's
            # full choice of overlapping in-unit quotations.
            region.intervals = {}
        result[record] = region.requiring(required[number])
    return result


def missing_plan_sources(required, allocations):
    """A citation in any unit can supply the complete sentence from its own field."""
    missing = dict(required)
    for node in allocations:
        for unit in node:
            for field, quote in unit:
                if field in missing and missing[field] in quote:
                    del missing[field]
    return missing


def paired_original_root(pair, preceding, field, quote):
    """The first root covers the complete action; the next supplies its own original account."""
    action_field, action, thought_field = pair
    if not preceding:
        return (field == action_field and quote == action
                or field == thought_field and action in quote)
    if len(preceding) == 1 and preceding[0][0] == action_field:
        return field == thought_field and quote not in action
    return True


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
    # A bounded entire action is also a literal source choice. Existing sentence
    # cues continue to name precisely the same passages.
    pairs = compact_action_pairs(material)
    for number, full_action, _ in pairs.values():
        allowed[number].add(full_action)
        choices[number, full_action] = full_action
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
    if pairs:
        view['records'] = [
            dict(row, paired_original_fields=[pairs[row['record']][0], pairs[row['record']][2]])
            if row['record'] in pairs else row for row in material['records']]
    regions = plan_reading_regions(material, pairs)
    if regions:
        view['records'] = [dict(row, memo_reading_regions=regions[row['record']].description())
            if row['record'] in regions else row for row in view['records']]
    if material.get('author_profile') in {'semantic_map.node_local.v4.occurrence.v22', 'semantic_map.node_local.v4.occurrence.v23', 'semantic_map.node_local.v4.occurrence.v24'}:
        required = whole_plan_sources(material, record_plan_owners(material))
        if required:
            view['whole_plan_source_ranges'] = [
                dict(field=number, scalar_range=[fields[number]['text'].index(sentence),
                     fields[number]['text'].index(sentence) + len(sentence)], opening_cue=sentence[:12])
                for number, sentence in required.items()]
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
    if material.get('author_profile') in {'semantic_map.node_local.v4.occurrence.v22', 'semantic_map.node_local.v4.occurrence.v23', 'semantic_map.node_local.v4.occurrence.v24'}:
        original.pop('whole_plan_source_ranges', None)
    if material.get('author_profile') in {'semantic_map.node_local.v4.occurrence.v18', 'semantic_map.node_local.v4.occurrence.v19', 'semantic_map.node_local.v4.occurrence.v20', 'semantic_map.node_local.v4.occurrence.v21', 'semantic_map.node_local.v4.occurrence.v22', 'semantic_map.node_local.v4.occurrence.v23', 'semantic_map.node_local.v4.occurrence.v24'} and 'records' in material:
        original['records'] = [{k: v for k, v in row.items() if k != 'paired_original_fields'}
                               for row in material['records']]
    if material.get('author_profile') in {'semantic_map.node_local.v4.occurrence.v20', 'semantic_map.node_local.v4.occurrence.v21', 'semantic_map.node_local.v4.occurrence.v22', 'semantic_map.node_local.v4.occurrence.v23', 'semantic_map.node_local.v4.occurrence.v24'} and 'records' in original:
        original['records'] = [{k: v for k, v in row.items() if k != 'memo_reading_regions'} for row in original['records']]
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


def _source_timestamp(value):
    from datetime import datetime, timezone

    stamp = datetime.fromisoformat(value.replace('Z', '+00:00'))
    # Stored timestamps without an offset are UTC, as in source_adapter.
    return stamp if stamp.tzinfo is not None else stamp.replace(tzinfo=timezone.utc)


def earlier_unknown_fields(material):
    """Bind an original field to its record clock only when a strictly later record exists."""
    stamps = {row['record']: _source_timestamp(row['recorded_at']) for row in material['records']}
    if len(stamps) < 2:
        return {}
    last = max(stamps.values())
    labels = dict(zip(stamps, _source_date_labels(material, stamps), strict=True))
    return {field: labels[record] for field, record in _original_field_records(material).items()
            if record in stamps and stamps[record] < last}


def _source_date_labels(material, records):
    from collections import Counter
    from datetime import timedelta, timezone

    timestamps = {row['record']: row['recorded_at'] for row in material['records']}
    local = [_source_timestamp(timestamps[record]).astimezone(timezone(timedelta(hours=9)))
             for record in records]
    date_counts = Counter(stamp.date() for stamp in local)
    across_years = len({stamp.year for stamp in local}) > 1
    labels = []
    for stamp in local:
        label = f'{stamp.month}月{stamp.day}日'
        if across_years:
            label = f'{stamp.year}年' + label
        if date_counts[stamp.date()] > 1:
            label += stamp.strftime(' %H:%M')
        labels.append(label)
    label_counts = Counter(labels)
    return tuple(f'記録{record}（{label}）' if label_counts[label] > 1 else label + 'の記録'
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


def paired_node_meanings(fields, units, sentences):
    """Retain a person's complete, qualified thought alongside their own action."""
    by_number = {f['field']: f for f in fields}
    roots = [root for unit in units for root in unit['evidence']]
    selected = [by_number[root['field']] for root in roots]
    if (not selected or any(f.get('source_role') != 'ORIGINAL_INPUT' for f in selected)
            or len({f.get('record') for f in selected}) != 1 or not selected[0].get('record')
            or {f.get('field_path') for f in selected} != {'memo', 'memo_action'}):
        return []
    record = selected[0]['record']
    if any(f.get('source_role') != 'ORIGINAL_INPUT' and f.get('record') in (record, None)
            for f in fields):
        return []
    choices = []
    for root, field in zip(roots, selected, strict=True):
        if field['field_path'] != 'memo':
            continue
        # Only a whole source sentence selected in this PLAN can qualify the
        # action. Do not attach another sentence from the surrounding record.
        for sentence in sorted(sentences.get(root['field'], ()), key=field['text'].index):
            if (len(sentence) <= 240 and sentence in root['quote']
                    and any(mark in sentence for mark in ('、', '，', ','))
                    and sentence not in choices):
                choices.append(sentence)
    return choices


def single_original_leaf(material):
    """Two complete fields from one source, with no corrections or other speakers' records."""
    fields = material.get('fields', ())
    return (material.get('history_stage', {}).get('kind') == 'LEAF'
            and len(fields) == 2
            and {f.get('field_path') for f in fields} == {'memo', 'memo_action'}
            and all(f.get('source_role') == 'ORIGINAL_INPUT'
                    and f.get('fragment_is_complete_field') is not False for f in fields)
            and fields[0].get('record') is not None and fields[0]['record'] == fields[1].get('record'))


def leaf_meanings(fields, units, sentences):
    """Choose one complete selected thought, or leave the intermediate description empty."""
    thought = next(field for field in fields if field['field_path'] == 'memo')
    selected = [root['quote'] for unit in units for root in unit['evidence']
                if root['field'] == thought['field']]
    return [''] + sorted(
        (s for s in sentences.get(thought['field'], ()) if len(s) <= 240
         and thought['text'].count(s) == 1 and any(s in quote for quote in selected)),
        key=thought['text'].index)


def source_ordered_merge(wire_version):
    return wire_version in ('cocolon.analysis.merge_wire.v6', 'cocolon.analysis.merge_wire.v7', 'cocolon.analysis.merge_wire.v8', 'cocolon.analysis.merge_wire.v9')


def ordered_record_sections(fields, units, fixed_parts=None):
    """Order original excerpts by field and scalar position, without inferring an inter-field event time."""
    by_id = {f['field']: f for f in fields}
    roots = [r for u in units for r in u['evidence']]
    owners = {by_id[r['field']].get('record') for r in roots}
    if len(owners) != 1 or None in owners:
        return None
    owner = next(iter(owners))
    if any(f.get('source_role') != 'ORIGINAL_INPUT' and f.get('record') in (owner, None) for f in fields):
        return None
    groups = {}
    numbers = {}
    for i, unit in enumerate(units):
        if fixed_parts is not None and (not fixed_parts[i] or len(fixed_parts[i]) != len(unit['evidence'])):
            return None
        for j, root in enumerate(unit['evidence']):
            field = by_id[root['field']]
            path, original, quote = field.get('field_path'), field['text'], root['quote']
            if (path not in ('memo', 'memo_action') or field.get('source_role') != 'ORIGINAL_INPUT'
                    or field.get('supplement') is not None or field.get('fragment_is_complete_field') is not True
                    or field.get('fragment_scalar_range') != [0, len(original)] or original.count(quote) != 1
                    or numbers.setdefault(path, root['field']) != root['field']):
                return None
            start = original.index(quote)
            phrase = fixed_parts[i][j] if fixed_parts is not None else quote
            if phrase != quote:
                # Literal display ranges are the sole other v24 fact form. Keep cut
                # markers and use the assigned root's scalar offset for ordering.
                ranges = [key for key, text in source_fact_ranges(quote).items() if text == phrase]
                if len(ranges) != 1:
                    return None
                start += int(ranges[0][1:].split(':')[0])
            sentences = _outer_sentences(phrase, original_for_overview=True)
            parts = sentences if sentences and ''.join(sentences) == phrase else [phrase]
            group = groups.setdefault(path, {})
            for part in parts:
                if any(line in ('考えたこと・感じたこと', '出来事・行動') for line in part.splitlines()):
                    return None
                group[start, part] = part
                start += len(part)
    return [(path, [group[k] for k in sorted(group)])
            for path in ('memo', 'memo_action') if (group := groups.get(path))]


def record_opening_choices(fields, units):
    """Offer the first selected original sentence, including one inside a multi-sentence root."""
    sections = ordered_record_sections(fields, units)
    if not sections:
        return None
    path, lines = sections[0]
    first = lines[0]
    selected = {r['field'] for u in units for r in u['evidence']}
    field = next(f for f in fields if f.get('field_path') == path and f['field'] in selected)
    # Overlong roots can be shortened by the author during NODES. No heading
    # anticipates a passage whose display range has not yet been chosen.
    if (len(first) <= 80 and field['text'].count(first) == 1
            and first in _sentences(field['text'], original_for_overview=True)
            and any(r['field'] == field['field'] and len(r['quote']) <= 160 and first in r['quote']
                    for u in units for r in u['evidence'])):
        return [first, '記録にある場面']
    return ['記録にある場面']


def source_node_titles(material, units, literal_titles):
    """Offer a complete source sentence scoped to this node, or a nonfactual heading."""
    if literal_titles:
        return sorted(set(literal_titles))
    fields = {field['field']: field for field in material['fields']}
    quotes = {}
    for unit in units:
        for root in unit['evidence']:
            quotes.setdefault(root['field'], []).append(root['quote'])
    owners = {fields[number].get('record') for number in quotes}
    # A sentence owned by just one record cannot stand for a comparison.
    if len(owners) > 1:
        return ['記録を比べて']
    titles = []
    for number, selected in quotes.items():
        field = fields[number]
        if field.get('fragment_is_complete_field') is False:
            continue
        source = field['text']
        for text in _sentences(source, original_for_overview=True):
            if (len(text) <= 80 and text.endswith(('。', '！', '？', '!', '?'))
                    and source.count(text) == 1 and any(text in quote for quote in selected)
                    and text not in titles):
                titles.append(text)
    return titles or ['記録にある場面']


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


# Separators are recognized only *between* complete source phrases. Embedded
# punctuation (a decimal point, a quotation, etc.) remains part of the phrase.
_OVERVIEW_SEPARATORS = frozenset(TITLE_END_MARKS + '・／/：:；;―—…　 ')


class OverviewSourcePhrases:
    """Identify a literal collage of selected evidence that omits a selected record."""

    def __init__(self, material, units, *, include_original_fields=False, restricted_titles=()):
        fields = _original_field_records(material)
        owners = {_unit_record(fields, unit) for unit in units} - {None}
        bits = {owner: 1 << index for index, owner in enumerate(sorted(owners))}
        self.required = (1 << len(owners)) - 1 if len(owners) >= 2 else 0
        self.restricted_titles = restricted_titles
        original_title_owners = dict.fromkeys(restricted_titles or (), 0) if include_original_fields else {}
        self.by_initial = {}
        self.end_chars = set(_OVERVIEW_SEPARATORS)
        if not self.required:
            return

        def index(phrase, owner):
            phrase = source_title_key(phrase)
            if 0 < len(phrase) <= 80 and any(c.isalnum() for c in phrase):
                mask = bits.get(owner, self.required)
                if phrase in original_title_owners and owner in bits:
                    original_title_owners[phrase] |= bits[owner]
                by_length = self.by_initial.setdefault(phrase[0], {})
                same_length = by_length.setdefault(len(phrase), {})
                same_length[phrase] = same_length.get(phrase, 0) | mask
                self.end_chars.add(phrase[-1])

        for unit in units:
            for root in unit['evidence']:
                # Supplementary or corroborating text without an independent
                # owner cannot establish that a selected record is missing.
                owner = fields.get(root['field'])
                quote = root['quote']
                for phrase in (quote, *_sentences(quote)):
                    index(phrase, owner)
        if include_original_fields:
            for field in material['fields']:
                owner = fields.get(field['field'])
                if owner not in bits or field.get('fragment_is_complete_field') is False:
                    continue
                # Only complete outer sentences contribute source ownership.
                # Repetition within a single physical record keeps that owner.
                for phrase in _sentences(field['text'], original_for_overview=True):
                    if phrase.endswith(('。', '！', '？', '!', '?')):
                        index(phrase, owner)

        if original_title_owners:
            # A legacy restriction can be lifted only with positive, complete
            # original-record support. A supplement never supplies that support.
            self.restricted_titles = [title for title, mask in original_title_owners.items() if mask != self.required]

    def omits_record(self, title):
        if not self.required:
            return False
        # Each offset retains the union of all defensible source attributions
        # for that prefix. A shared phrase does not force a single attribution.
        masks = {0: 0}
        for start, char in enumerate(title):
            if start not in masks:
                continue
            if char in _OVERVIEW_SEPARATORS:
                masks[start + 1] = masks.get(start + 1, 0) | masks[start]
            # A title has at most 80 characters. Unrelated equal-initial
            # originals never make this loop scale with the source vocabulary.
            for length, phrases in self.by_initial.get(char, {}).items():
                end = start + length
                if end <= len(title):
                    owner_bits = phrases.get(title[start:end])
                    if owner_bits is not None:
                        masks[end] = masks.get(end, 0) | masks[start] | owner_bits
        covered = masks.get(len(title), 0)
        return bool(covered) and covered != self.required


def repeated_record_node_dates(material, nodes):
    """Date separate nodes from one record only when every root belongs to that original."""
    from collections import Counter

    fields = _original_field_records(material)
    owners = []
    for node in nodes:
        source_records = {fields.get(root['field']) for unit in node['units'] for root in unit['evidence']}
        owners.append(source_records.pop() if len(source_records) == 1 else None)
    counts = Counter(owner for owner in owners if owner is not None)
    records = [row['record'] for row in material['records']]
    if len(records) < 2 or not any(count > 1 for count in counts.values()):
        return {}
    labels = dict(zip(records, _source_date_labels(material, records), strict=True))
    return {index: labels[owner] for index, owner in enumerate(owners) if owner in counts}


def selected_record_overview(material, nodes, fixed_parts, heading, *, include_authored_titles=False):
    """Summarize selected complete original sentences for a whole-map heading."""
    from collections import Counter
    rows = material['records']
    if include_authored_titles:
        rows = sorted(rows, key=lambda row: _source_timestamp(row['recorded_at']))
    records = [row['record'] for row in rows]
    if len(records) < 2 or (not include_authored_titles and heading != f'{len(records)}件の記録を振り返って'):
        return ''
    single_clock = len({_source_timestamp(row['recorded_at']) for row in material['records']}) == 1
    chosen = {}
    if not isinstance(fixed_parts, dict):
        return ''
    fields = {f['field']: f for f in material['fields']}
    for i, node in enumerate(nodes, 1):
        for j, unit in enumerate(node['units'], 1):
            parts = fixed_parts.get(f'n{i}.u{j}')
            if not parts:
                return ''
            for root, phrase in zip(unit['evidence'], parts, strict=True):
                field = fields[root['field']]
                if (field['source_role'] != 'ORIGINAL_INPUT' or field.get('fragment_scalar_range')
                        or field.get('fragment_is_complete_field') is False):
                    return ''
                if phrase in root['quote']:
                    chosen.setdefault(field['field'], []).append(phrase)

    labels = _source_date_labels(material, records)
    leads, details = [], []
    for record, label in zip(records, labels, strict=True):
        action, thought = [], []
        for field in material['fields']:
            if field['record'] != record or field['field_path'] not in ('memo', 'memo_action'):
                continue
            target = action if field['field_path'] == 'memo_action' else thought
            selected = chosen.get(field['field'], ())
            for sentence in _outer_sentences(field['text'], original_for_overview=True):
                if (field['text'].count(sentence) == 1 and sentence not in target
                        and any(sentence in phrase for phrase in selected)):
                    target.append(sentence)
        if not action and not thought:
            # Keep the existing authored overview for cohorts with a supplement, an
            # unresolved fragment or no independently attributed complete sentence.
            return ''
        # Put the person's short action from every record first. The mobile card
        # shows three lines, so a long first explanation can hide the later act.
        lead = (action or thought)[0]
        extra = []
        if len(records) <= 3:
            extra = thought[:1] + action[1:2]
            extra.extend(sentence for sentence in thought if _scheduled_current_state(sentence))
        extra = [line for line in dict.fromkeys(extra) if line != lead]
        if len(records) > 3 and len(lead) > 80:
            return ''
        # Each extended account carries its own date even when its lead is nearby.
        short_label = re.sub(r'(?:(\d{4})年)?(\d+)月(\d+)日の記録$',
                             lambda m: '/'.join(t for t in m.groups() if t), label)
        leads.append((short_label, lead))
        if extra:
            details.append(label + '：' + ''.join(extra))
    counts = Counter(lead for _, lead in leads)
    lines = [lead if single_clock and len(records) > 3 and counts[lead] == 1
             else label + ' ' + lead for label, lead in leads]
    summary = '\n'.join(lines + details)
    return summary if len(summary) <= 2000 else ''



# Each title atom is a complete statement or a grammatical variant of
# one original source. Do not build new relations by matching loose words.
_TITLE_NOUN_PART = r'[一-鿿々ァ-ヺーA-Za-z0-9０-９]+(?:(?![がをにでへはものと])[ぁ-ゖ]){0,3}'
_TITLE_NOUN = _TITLE_NOUN_PART + r'(?:の' + _TITLE_NOUN_PART + r'){0,3}'
_TITLE_ACTION = re.compile(r'(?P<context>(?:' + _TITLE_NOUN + r'[にでへ]){0,2})'
    + r'(?P<object>' + _TITLE_NOUN + r')を(?P<process>(?:[一-鿿々]+して){0,2})'
    + r'(?P<verb>[一-鿿々]+)(?P<form>[ぁ-ゖ]{0,5}[ただ]|し)$')
_TITLE_INCOMING = re.compile(r'(?P<sender>' + _TITLE_NOUN + r')から'
    + r'(?P<topic>' + _TITLE_NOUN + r')が(?P<event>[一-鿿々]+[ぁ-ゖ]{0,4}[ただ])と'
    + r'(?P<notice>' + _TITLE_NOUN + r')が(?:あった|来た|届いた)$')


def _title_atom_choices(sentence, *, original_action):
    """Preserve the object, arguments, source and polarity while shortening a sentence."""
    if not sentence.endswith(('。', '！', '!', '？', '?')):
        return set()
    if sentence[-1] != '。':
        # A question or exclamation can only be used with its own end mark.
        return {sentence} if len(sentence) <= 80 else set()
    body = sentence[:-1].strip()
    if not body:
        return set()
    choices = {body}
    # Parse an entire explicit report, not its nested proposition or speaker
    # in isolation. The resulting relative clause still names the report.
    incoming = _TITLE_INCOMING.fullmatch(body)
    if incoming and not incoming['event'].endswith(('なかった', 'たかった', 'そうだった')):
        choices.add(incoming['sender'] + 'から' + incoming['notice'] + 'を受けた' + incoming['topic'])
    clauses = [body]
    if original_action:
        # Only a list of directly written actions with a final finite verb
        # can contribute separate parts of a compound action field.
        parts = re.split('[、，,]', body)
        matches = [_TITLE_ACTION.fullmatch(part) for part in parts]
        if (len(parts) > 1 and all(matches) and all(m['form'] == 'し' for m in matches[:-1])
                and matches[-1]['form'].endswith(('た', 'だ')) and 'なかっ' not in matches[-1]['form']):
            clauses = [part + 'た' for part in parts[:-1]] + [parts[-1]]
    for clause in clauses:
        m = _TITLE_ACTION.fullmatch(clause)
        if not m or m['form'] == 'し':
            continue
        choices.add(clause)
        if m['form'].endswith(('なかった', 'たかった', 'そうだった')):
            continue
        choices.add(clause + '日')
        if m['process']:
            continue
        # Japanese can move an object into the head of a relative clause.
        # Keep each original adjunct in that same clause.
        choices.add(m['context'] + m['verb'] + m['form'] + m['object'])
        if not m['context'] and m['form'] == 'した':
            choices.add(m['object'] + 'の' + m['verb'])
            choices.add(m['object'])
    return {q for q in choices if q and len(q) <= 80}


def _title_atoms(material, nodes):
    fields = {f['field']: f for f in material['fields'] if f['source_role'] == 'ORIGINAL_INPUT'}
    selected = {}
    for node in nodes:
        for unit in node['units']:
            for root in unit['evidence']:
                if root['field'] in fields:
                    selected.setdefault(root['field'], set()).add(root['quote'])
    index = {}
    for number, quotations in selected.items():
        f = fields[number]
        # In a history fragment require a complete, admitted original
        # sentence; no unbound text nearby is admitted as a heading.
        for sentence in _outer_sentences(f['text'], original_for_overview=True):
            if not any(sentence in quote for quote in quotations):
                continue
            for atom in _title_atom_choices(sentence, original_action=f.get('field_path') == 'memo_action'):
                index.setdefault(atom, set()).add(f['record'])
    return index


def _source_composed_title(proposal, material, nodes):
    """Read every character as an intact per-record atom or a neutral connective."""
    index = _title_atoms(material, nodes)
    refs = {f['field']: f['record'] for f in material['fields'] if f['source_role'] == 'ORIGINAL_INPUT'}
    required = {owner for node in nodes for unit in node['units']
                if (owner := _unit_record(refs, unit)) is not None}
    if len(required) < 2:
        return False
    # Use only a complete ending. Question marks, quotes and negative forms
    # belong to their original statement and are not interchangeable punctuation.
    body = proposal[:-1] if proposal.endswith('。') else proposal
    # The composed order may be thematic. The chronological construction
    # additionally requires increasing actual record timestamps.
    records = {r['record']: r.get('recorded_at') for r in material.get('records', ())}
    def matches(text, *, chronological=False):
        pending = [(0, frozenset(), None)]
        visited = set()
        while pending:
            at, covered, previous = pending.pop()
            state = at, covered, previous
            if state in visited:
                continue
            visited.add(state)
            for atom, owners in index.items():
                if not text.startswith(atom, at):
                    continue
                end = at + len(atom)
                for owner in owners:
                    if (owner in covered or chronological and previous is not None
                            and (not records.get(owner) or not records.get(previous)
                                 or _source_timestamp(records[owner]) <= _source_timestamp(records[previous]))):
                        continue
                    reached = covered | {owner}
                    if end == len(text):
                        if reached == required:
                            return True
                        continue
                    separators = ('から',) if chronological else ('と、', 'と', '。', '／', '・')
                    for sep in separators:
                        if text.startswith(sep, end):
                            pending.append((end + len(sep), reached, owner))
        return False
    return matches(body) or (body.endswith('まで') and matches(body[:-2], chronological=True))


class WholeMapTitle:
    """Ground a topical overview in the independent original records it summarizes."""

    def __init__(self, material, nodes):
        fields = _original_field_records(material)
        sources = {}
        for node in nodes:
            for unit in node['units']:
                owner = _unit_record(fields, unit)
                if owner is not None:
                    sources.setdefault(owner, []).extend(root['quote'] for root in unit['evidence'])
        self.count = len(sources)
        self.neutral = f'{self.count}件の記録を振り返って'
        self.words = {}
        self.witnesses = []
        if self.count < 2:
            return
        # Compare source text, never the generated node title or meaning. A shared
        # word (e.g. a repeated object name) cannot stand in for distinct episodes.
        complete = {owner: list(quotes) for owner, quotes in sources.items()}
        for field in material['fields']:
            owner = fields.get(field['field'])
            if owner in complete and field.get('fragment_is_complete_field') is not False:
                complete[owner].append(field['text'])
        for index, (owner, quotes) in enumerate(sources.items()):
            other = '\n'.join(q for key, group in complete.items() if key != owner for q in group)
            candidates = {}
            for quote in quotes:
                for match in re.finditer(r'[一-鿿々ァ-ヺー]{2,}|[A-Za-z0-9]+', quote):
                    word = match[0]
                    if 2 <= len(word) <= 12 and word not in other:
                        candidates[word] = None
                for start in range(len(quote) - 3):
                    word = quote[start:start + 4]
                    if (sum(c.isalnum() for c in word) == 4 and
                            any('一' <= c <= '鿿' or 'ァ' <= c <= 'ヺ' for c in word) and word not in other):
                        candidates[word] = None
            for word in candidates:
                self.words[word] = 1 << index
            self.witnesses.append(min(candidates, key=len) if candidates else '')
        self.lengths = tuple(sorted({len(word) for word in self.words}))
        self.required = (1 << self.count) - 1

    def mask(self, text):
        bits = 0
        for length in self.lengths:
            for pos in range(len(text) - length + 1):
                bits |= self.words.get(text[pos:pos + length], 0)
        return bits

    def accepts(self, text):
        return self.count < 2 or text == self.neutral or self.mask(text) == self.required

    def completion(self, text):
        """One bounded continuation, or None if only the neutral title was possible."""
        mask = self.mask(text)
        if mask == self.required:
            return ''
        missing = [word for i, word in enumerate(self.witnesses) if not mask & (1 << i)]
        return ('・' if text else '') + '・'.join(missing) if all(missing) else None

    def authored_choices(self, proposal, material, nodes):
        """Offer the exact proposed heading only when it represents the complete map."""
        if (not proposal or proposal == self.neutral or proposal != proposal.strip()
                or len(proposal) > 80 or any(ord(char) < 32 for char in proposal)
                or not self.accepts(proposal)):
            return [self.neutral]
        spans = _outer_sentences(proposal, original_for_overview=True)
        if not spans:
            return [self.neutral]
        if len(spans) > 1:
            # A copied sentence with its attribution or qualification cut off cannot
            # carry a different record. Likewise a fragment after a sentence stop
            # cannot supply that record just by listing terms. Complete quotations
            # and independently worded passages retain their own source support.
            originals = [field['text'] for field in material['fields']
                if field['source_role'] == 'ORIGINAL_INPUT' and field.get('fragment_is_complete_field') is not False]
            complete = {sentence.rstrip('。！？!?') for text in originals
                for sentence in _outer_sentences(text, original_for_overview=True)}
            supported = 0
            for span in spans:
                body = span.rstrip('。！？!?')
                if body not in complete:
                    if any(body in text for text in originals):
                        continue
                    terms = body.split('・')
                    if (span == body and len(terms) > 1
                            and all(term and any(term in text for text in originals) for term in terms)):
                        continue
                supported |= self.mask(span)
            if supported != self.required:
                return [self.neutral]
        if (material.get('author_profile') in {'semantic_map.node_local.v4.occurrence.v23', 'semantic_map.node_local.v4.occurrence.v24'}
                and not _source_composed_title(proposal, material, nodes)):
            return [self.neutral]
        units = [unit for node in nodes for unit in node['units']]
        quotes = [root['quote'] for unit in units for root in unit['evidence']]
        forbidden = one_sided_source_titles(material, units, compare_end_marks=True)
        phrases = OverviewSourcePhrases(material, units, restricted_titles=forbidden, include_original_fields=True)
        if (source_title_key(proposal) in (phrases.restricted_titles or ())
                or phrases.omits_record(proposal) or not visible_closers_bound(proposal, source_closer_runs(quotes))):
            return [self.neutral]
        return [proposal, self.neutral]
