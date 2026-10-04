"""Analysis-owned observed graph from existing source-grounded semantic frames.

The shared semantic owner supplies evidence, polarity and modality, never an
Emlis response. Analysis decides its own node kinds, edges and missing scopes.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import re

from emlis_ai_grounded_observation_plan import (
    build_final_stage1_grounded_observation_plan,
    source_proven_performed_action_status,
    _source_current_cognition, _source_current_cognition_parts,
    _source_unfinished_result_clause_is_bound,
)
from ...contracts import EvidenceRef
from ...emlis_answer_update import _WITHDRAWAL, _REPLACEMENT
from .source_adapter import (AnalysisSourceError, AnalysisSourceSet, commitment,
                            scoped_source_view, source_field_text)

NODE_KINDS = ('SCENE', 'ROLE', 'ATTENTION_OR_THOUGHT',
              'ACTION_OR_NONACTION', 'IMMEDIATE_RESULT_OR_AFTERMATH')


@dataclass(frozen=True, slots=True, repr=False)
class ObservedProposition:
    """Whole-clause grammatical interpretation, private and source-bound.

    Arguments retain written case particles; a ni-case is not guessed to be
    a recipient, location or cause. This is not anonymized telemetry.
    """
    actor: str
    arguments: tuple[tuple[str, str], ...]
    predicate_lemma: str
    polarity: str
    modality: str
    temporal_scope: str
    source_parts: tuple[tuple[str, int, int], ...]
    sequence_marker: str = ''
    relative_day: str = ''
    possible_content: ObservedProposition | None = None
    result_state: str = ''
    dependent_form: str = ''
    scene_state: str = ''
    role_state: str = ''


# A bounded verb/inflection inventory, not an input/topic-to-answer table.
# The finite operator and every argument must consume the complete clause.
_VERBS = (
    ('書く', '書', 'k'), ('調べる', '調べ', 'vowel'),
    ('試す', '試', 's'), ('見る', '見', 'vowel'),
    ('作る', '作', 'r'), ('残す', '残', 's'),
    ('記録する', '記録', 'suru'), ('メモする', 'メモ', 'suru'),
    ('続ける', '続け', 'vowel'),
)
# Kana-bearing nouns need a lexical proof: allowing arbitrary okurigana would
# misread 急いで / 読んで as a noun plus de-case and erase a second predicate.
# These are nominal lexemes, not triggers selecting a response or a topic.
_NOMINAL = r'(?:考え|思い|気持ち|学び|振り返り|取り組み|[一-鿿々]+|[ァ-ヴー]+)'
_ARGUMENT = re.compile(r'(?P<noun>' + _NOMINAL + r'(?:の' + _NOMINAL
                       + r')*)(?P<case>を|に|で|と)')


def _finite_predicates(*, include_nonpast=False):
    forms = []
    for lemma, stem, group in _VERBS:
        i, a, past = {
            'k': (stem + 'き', stem + 'か', stem + 'いた'),
            's': (stem + 'し', stem + 'さ', stem + 'した'),
            'r': (stem + 'り', stem + 'ら', stem + 'った'),
            'vowel': (stem, stem, stem + 'た'),
            'suru': (stem + 'し', stem + 'し', stem + 'した'),
        }[group]
        for surface, polarity, modality, time in (
            (past, 'positive', 'fact', 'past'),
            (i + 'ました', 'positive', 'fact', 'past'),
            (a + 'なかった', 'negative', 'fact', 'past'),
            (i + 'ませんでした', 'negative', 'fact', 'past'),
            (i + 'たい', 'positive', 'wish', 'current_input'),
            (i + 'たいです', 'positive', 'wish', 'current_input'),
            (i + 'たくない', 'negative', 'wish', 'current_input'),
            (i + 'たくないです', 'negative', 'wish', 'current_input'),
            (i + 'たかった', 'positive', 'wish', 'past'),
            (i + 'たくなかった', 'negative', 'wish', 'past'),
        ):
            forms.append((surface, lemma, polarity, modality, time))
        if include_nonpast:
            forms.extend(((lemma, lemma, 'positive', 'fact', 'nonpast'),
                          (a + 'ない', lemma, 'negative', 'fact', 'nonpast')))
    return tuple(sorted(forms, key=lambda row: len(row[0]), reverse=True))


_FINITE_PREDICATES = _finite_predicates()
# Only the existing nine verbs: their plain perfective forms supply the
# corresponding te inflection. These forms carry no independent past tense.
_TE_PREDICATES = tuple((surface[:-1] + 'て', lemma, 'positive', 'fact', 'dependent')
    for surface, lemma, polarity, modality, time in _FINITE_PREDICATES
    if (polarity, modality, time) == ('positive', 'fact', 'past')
    and not surface.endswith('ました'))
_CONTENT_PREDICATES = _finite_predicates(include_nonpast=True)
_CANONICAL_CONTENT = {(lemma, polarity, time): surface
    for surface, lemma, polarity, modality, time in _CONTENT_PREDICATES
    if modality == 'fact'
    and not surface.endswith(('ました', 'ませんでした'))}
_CLAUSE_PREFIX = re.compile(r'^(その後|それから|今日|昨日)[、，\s]*')
# A post-topic day modifies the finite clause. An explicit の or case
# particle instead keeps 今日/昨日 inside the written nominal argument.
_POST_TOPIC_DAY = re.compile(r'(今日|昨日)(?!の|を|に|で|と|は|が|も)[、，\s]*')
_DAY_EXTENSION = re.compile(
    r'(?:分|以前|以後|以降|以来|当時|時点|現在|中|付|頃|ごろ|まで|から|より|だけ|'
    r'朝|昼|夜|晩|夕|午前|午後|早朝|深夜|未明|正午)')
# Observed unsupported time prefixes must not be swallowed by the open
# kanji nominal slot. This is not a new time interpretation or day enum.
_UNPARSED_TIME_NOMINAL = re.compile(r'^(?:明後日|明日|一昨日|今朝|昨夜|先週|来週)(?=.)')
_COGNITIVE_HOSTS = {value: value for value in (
    '考えてしまう', '思ってしまう', '考えている', '思っている', '考える', '思う')}
_COGNITIVE_HOSTS['考えちゃう'] = '考えてしまう'
_UNFINISHED_RESULT = re.compile(
    r'(?P<still>まだ)(?P<noun>' + _NOMINAL + r'(?:の' + _NOMINAL + r')*)'
    r'(?P<case>は|が|も)(?P<stem>見つか|決ま|定ま)って(?P<negative>いない|いません)')
_RESULT_STEMS = {'見つかる': '見つか', '決まる': '決ま', '定まる': '定ま'}
_CHANGE_PAST = {'減る': '減った', '増える': '増えた', '変わる': '変わった', '戻る': '戻った'}
_BOUNDED_CHANGE = re.compile(
    r'(?P<noun>' + _NOMINAL + r'(?:の' + _NOMINAL + r')*)'
    r'(?P<case>は|が|も)(?P<predicate>' + '|'.join(_CHANGE_PAST.values()) + r')')
# Finite feelings already witnessed by the shared action/change pair. These
# are predicate inflections, not an assessment that the preceding action helped.
_FEELING_PAST = {'安心する': '安心した', '落ち着く': '落ち着いた',
                 '嬉しい': '嬉しかった', 'うれしい': 'うれしかった'}
_FEELING_FORMS = {'安心した': '安心する', '安心しました': '安心する',
    '落ち着いた': '落ち着く',
    '嬉しかった': '嬉しい', 'うれしかった': 'うれしい'}
_PAST_EVENT_TOPIC = (
    r'(?P<subject>私|僕|わたし|自分)は'
    r'(?:(?P<day>今日|昨日)(?!の|を|に|で|と|は|が|も)(?P<day_separator>[、，\s]*))?')
_PAST_PRESENCE = re.compile(
    _PAST_EVENT_TOPIC + r'(?P<noun>' + _NOMINAL
    + r'(?:の' + _NOMINAL + r')*)(?P<case>に)'
    r'(?P<predicate>いた|いました|いなかった|いませんでした)')
_PAST_RESPONSIBILITY = re.compile(
    _PAST_EVENT_TOPIC + r'(?P<noun>' + _NOMINAL
    + r'(?:の' + _NOMINAL + r')*)(?P<case>を)'
    r'(?P<predicate>担当した|担当しました|担当しなかった|担当しませんでした)')
_PROTECTIVE_WISH = re.compile(
    r'(?P<subject>私|僕|わたし|自分)は(?P<noun>' + _NOMINAL
    + r'(?:の' + _NOMINAL + r')*)(?P<case>を)(?P<predicate>守りたい(?:です)?)')


def _protective_wish_proposition(value):
    # A written current intention with an explicit object; no other forms of
    # 守る, inferred benefit, or motive for another action are admitted here.
    match = _PROTECTIVE_WISH.fullmatch(value)
    if match is None or re.search(r'(?:^|の)(?:何|誰|幾)', match['noun']):
        return None
    return ObservedProposition('SELF', (('を', match['noun']),), '守る',
        'positive', 'wish', 'current_input', (
            ('SELF_TOPIC', 0, match.start('noun')),
            ('PROTECTIVE_OBJECT', match.start('noun'), match.end('noun')),
            ('CASE_を', match.start('case'), match.end('case')),
            ('FINITE_PROTECTIVE_WISH', match.start('predicate'), len(value))))


def _protective_wish_witness(nucleus):
    frame = nucleus.semantic_frame
    # The shared keyword frame can classify a nominal object such as 気持ち
    # as feeling before wish. The full finite surface, nucleus kind and
    # modality must still independently witness the current intention.
    predicate_matches = (frame.predicate_kind == 'wish'
        or (frame.predicate_kind == 'feeling'
            and 'operator:feeling' in frame.attribute_codes))
    return (nucleus.grounding_kind == 'explicit'
        and nucleus.allowed_claim_scope == 'explicit_current_input'
        and nucleus.retention in {'required', 'should'}
        and nucleus.kind == 'wish' and predicate_matches
        and nucleus.source_fields == ('memo',) and len(nucleus.source_span_ids) == 1
        and (frame.actor, frame.polarity, frame.modality, frame.time_scope)
            == ('current_user', 'positive', 'wish', 'current_input')
        and 'operator:wish' in frame.attribute_codes
        and not any(code.startswith(('source_fragment_', 'surface_scalar_',
                    'thread_time:', 'semantic_dependency:')) for code in frame.attribute_codes))


def _past_event_topic_parts(match):
    if match is None or re.search(r'(?:^|の)(?:何|誰|幾)', match['noun']):
        return None
    # Keep an unparsed/repeated day out of the nominal argument. Nominal
    # 今日の... remains unsupported here; it must never become an event day.
    if re.match(r'(?:今日|昨日)', match['noun']):
        return None
    if match['day'] is None:
        return (('SELF_TOPIC', 0, match.start('noun')),)
    # Match the action grammar's bounded day scope: neither a finer time
    # nor an unseparated genitive phrase establishes the event's day.
    if (_DAY_EXTENSION.match(match['noun'])
            or (not match['day_separator'] and 'の' in match['noun'])):
        return None
    day = {'今日': 'TODAY', '昨日': 'YESTERDAY'}[match['day']]
    return (('SELF_TOPIC', 0, match.start('day')),
            ('RELATIVE_DAY_' + day, match.start('day'), match.start('noun')))


def _past_responsibility_proposition(value):
    # The explicit responsibility predicate, not the noun or a job-title
    # guess, establishes the role relation. It proves no completed task.
    match = _PAST_RESPONSIBILITY.fullmatch(value)
    topic_parts = _past_event_topic_parts(match)
    if topic_parts is None:
        return None
    polarity = 'negative' if match['predicate'] in {'担当しなかった', '担当しませんでした'} else 'positive'
    return ObservedProposition('SELF', (('を', match['noun']),), '担当する',
        polarity, 'fact', 'past', topic_parts + (
            ('ROLE_NOMINAL', match.start('noun'), match.end('noun')),
            ('CASE_を', match.start('case'), match.end('case')),
            ('FINITE_RESPONSIBILITY', match.start('predicate'), len(value))),
        relative_day={'今日': 'TODAY', '昨日': 'YESTERDAY'}.get(match['day'], ''),
        role_state='PAST_RESPONSIBILITY')


def _past_presence_proposition(value):
    match = _PAST_PRESENCE.fullmatch(value)
    topic_parts = _past_event_topic_parts(match)
    if topic_parts is None:
        return None
    polarity = 'negative' if match['predicate'] in {'いなかった', 'いませんでした'} else 'positive'
    return ObservedProposition('SELF', (('に', match['noun']),), 'いる',
        polarity, 'fact', 'past', topic_parts + (
            ('SCENE_NOMINAL', match.start('noun'), match.end('noun')),
            ('CASE_に', match.start('case'), match.end('case')),
            ('FINITE_PRESENCE', match.start('predicate'), len(value))),
        relative_day={'今日': 'TODAY', '昨日': 'YESTERDAY'}.get(match['day'], ''),
        scene_state='PAST_PRESENCE')


def _past_event_proposition(value):
    """Retain one written day/connective on a complete scene or role clause.

    The finite host still proves past and SELF. Offsets address the full
    source clause, including its prefix; no rewritten source is introduced.
    """
    prefix = _CLAUSE_PREFIX.match(value)
    start = prefix.end() if prefix else 0
    event = (_past_presence_proposition(value[start:])
             or _past_responsibility_proposition(value[start:]))
    # This bounded grammar admits one day or connective, not a combination
    # whose scope would need a separate interpretation.
    if event is not None and prefix is not None and event.relative_day:
        return None
    if event is None or prefix is None:
        return event
    token = prefix.group(1)
    marker = {'その後': 'AFTER_PREVIOUS', 'それから': 'THEN_OR_ADDITION'}.get(token, '')
    day = {'今日': 'TODAY', '昨日': 'YESTERDAY'}.get(token, '')
    return replace(event, sequence_marker=marker, relative_day=day,
        source_parts=((marker or 'RELATIVE_DAY_' + day, 0, start),)
            + tuple((kind, a + start, b + start) for kind, a, b in event.source_parts))


def _past_event_witness(nucleus, proposition):
    # The shared generic event supplies grounding, not an inferred role.
    # Its current_input time is unspecified; the whole finite clause proves
    # past. Its default actor alone never proves SELF ownership.
    frame = nucleus.semantic_frame
    # The shared surface planner lowers ordinary clauses to should when
    # there are more than three. This is a display priority, not uncertainty.
    # Admit that priority for the fully parsed responsibility route; optional
    # fragments stay excluded and the existing scene admission is unchanged.
    retention = {'required', 'should'} if proposition.role_state else {'required'}
    return (nucleus.grounding_kind == 'explicit'
        and nucleus.allowed_claim_scope == 'explicit_current_input'
        and nucleus.retention in retention
        and nucleus.kind == frame.predicate_kind == 'event'
        and nucleus.source_fields == ('memo',)
        and len(nucleus.source_span_ids) == 1
        and frame.actor == 'current_user' and frame.modality == 'fact'
        and frame.polarity == ('negative' if proposition.polarity == 'negative' else 'neutral')
        # Shared 'present' marks 今日, not the finite host's tense. Accept
        # that witness only when this complete clause explicitly carries it.
        and (frame.time_scope in {'past', 'current_input'}
             or (frame.time_scope == 'present' and proposition.relative_day == 'TODAY'))
        and not any(code.startswith(('source_fragment_', 'surface_scalar_',
                    'thread_time:', 'semantic_dependency:')) for code in frame.attribute_codes))


def _past_feeling_proposition(value):
    subject = re.match(r'^(?:私|僕|わたし|自分)は', value)
    start = subject.end() if subject else 0
    lemma = _FEELING_FORMS.get(value[start:])
    if lemma is None:
        return None
    parts = (('SELF_TOPIC', 0, start),) if subject else ()
    return ObservedProposition('SELF' if subject else 'UNSPECIFIED', (),
        lemma, 'positive', 'feeling', 'past',
        parts + (('FINITE_FEELING', start, len(value)),),
        result_state='PAST_FEELING')


def _bounded_change_proposition(value):
    feeling = _past_feeling_proposition(value)
    if feeling is not None:
        return feeling
    match = _BOUNDED_CHANGE.fullmatch(value)
    if match is None or re.search(r'(?:^|の)(?:何|誰|幾)', match['noun']):
        return None
    lemma = next(k for k, v in _CHANGE_PAST.items() if v == match['predicate'])
    return ObservedProposition('UNSPECIFIED', ((match['case'], match['noun']),),
        lemma, 'positive', 'fact', 'past', (
            ('RESULT_NOMINAL', 0, match.end('noun')),
            ('CASE_' + match['case'], match.start('case'), match.end('case')),
            ('FINITE_CHANGE', match.start('predicate'), len(value))),
        result_state='BOUNDED_CHANGE')


def _unfinished_result_proposition(value):
    match = _UNFINISHED_RESULT.fullmatch(value)
    if (match is None or not _source_unfinished_result_clause_is_bound(value)
            or re.search(r'(?:^|の)(?:何|誰)', match['noun'])):
        return None
    # The noun is the written topic/subject, not proof of a first-person
    # agent, an earlier action, or the cause of this unachieved state.
    return ObservedProposition('UNSPECIFIED', ((match['case'], match['noun']),),
        match['stem'] + 'る', 'negative', 'fact', 'current_input', (
            ('STILL_OPERATOR', 0, match.end('still')),
            ('RESULT_NOMINAL', match.start('noun'), match.end('noun')),
            ('CASE_' + match['case'], match.start('case'), match.end('case')),
            ('RESULT_PREDICATE', match.start('stem'), match.start('negative')),
            ('NEGATIVE_STATE', match.start('negative'), len(value))),
        result_state='NOT_YET')


def _unfinished_result_witness(nucleus):
    frame = nucleus.semantic_frame
    return (nucleus.grounding_kind == 'explicit'
        and nucleus.allowed_claim_scope == 'explicit_current_input'
        and nucleus.retention == 'required'
        and nucleus.kind == frame.predicate_kind == 'event'
        and nucleus.source_fields == ('memo',)
        and len(nucleus.source_span_ids) == 1
        and frame.actor == 'current_user' and frame.modality == 'fact'
        and frame.polarity == 'negative'
        and frame.time_scope in {'present', 'current_input', 'continuing'}
        and 'semantic_role:present_unfinished' in frame.attribute_codes
        and not any(code.startswith(('source_fragment_', 'surface_scalar_',
                    'thread_time:', 'semantic_dependency:')) for code in frame.attribute_codes))


def _proposition_node_kind(proposition):
    if proposition.scene_state:
        return 'SCENE'
    if proposition.role_state:
        return 'ROLE'
    if proposition.result_state:
        return 'IMMEDIATE_RESULT_OR_AFTERMATH'
    if proposition.modality == 'wish' or proposition.possible_content:
        return 'ATTENTION_OR_THOUGHT'
    return 'ACTION_OR_NONACTION'


def _has_unparsed_time_nominal(proposition):
    if proposition is None:
        return False
    # Explicit の and a standalone case-marked day remain nominal: e.g.
    # 明日の資料 / 明日を記録した do not date the action. Check every
    # genitive segment and possible content, not only the first argument.
    return (any(_UNPARSED_TIME_NOMINAL.match(part)
                for _, noun in proposition.arguments for part in noun.split('の'))
            or _has_unparsed_time_nominal(proposition.possible_content))


def _proposition(value: str) -> ObservedProposition | None:
    proposition = _parsed_proposition(value)
    return None if _has_unparsed_time_nominal(proposition) else proposition


def _parsed_proposition(value: str) -> ObservedProposition | None:
    """Internal grammatical candidate; callers must check unresolved time."""
    protective = _protective_wish_proposition(value)
    if protective is not None:
        return protective
    event = _past_event_proposition(value)
    if event is not None:
        return event
    result = _unfinished_result_proposition(value) or _bounded_change_proposition(value)
    if result is not None:
        return result
    cognition = _cognitive_proposition(value)
    if cognition is not None:
        return cognition
    prefix = _CLAUSE_PREFIX.match(value)
    start = prefix.end() if prefix else 0
    token = prefix.group(1) if prefix else ''
    marker = {'その後': 'AFTER_PREVIOUS', 'それから': 'THEN_OR_ADDITION'}.get(token, '')
    relative_day = {'今日': 'TODAY', '昨日': 'YESTERDAY'}.get(token, '')
    subject = re.compile(r'(?:私|僕|わたし|自分)は').match(value, start)
    if subject is None:
        return None
    parts = ([(marker or 'RELATIVE_DAY_' + relative_day, 0, start)] if prefix else [])
    parts.append(('SELF_TOPIC', start, subject.end()))
    return _finite_proposition(value, subject.end(), 'SELF', parts, marker, relative_day)


def _finite_proposition(value, body_start, actor, prefix_parts, marker='', relative_day='', *, content_only=False, predicate_forms=None):
    day = _POST_TOPIC_DAY.match(value, body_start)
    if day is not None:
        # 昨日分の資料 / 昨日以前の資料 are not evidence that the action
        # happened yesterday. Finer day/range scopes need their own parse.
        if _DAY_EXTENSION.match(value, day.end()):
            return None
        first_argument = _ARGUMENT.match(value, day.end())
        if (day.end() == day.end(1) and first_argument is not None
                and 'の' in first_argument['noun']):
            # 昨日提出の資料 can describe the material, not the action.
            # Without a separator this bounded grammar leaves the whole
            # genitive scope unresolved rather than selecting either reading.
            return None
        # Nested cognition and dependent te episodes have their own scope
        # witnesses. Do not silently promote their day into this host.
        if content_only or predicate_forms is not None or marker or relative_day:
            return None
        relative_day = {'今日': 'TODAY', '昨日': 'YESTERDAY'}[day.group(1)]
        prefix_parts = [*prefix_parts,
            ('RELATIVE_DAY_' + relative_day, body_start, day.end())]
        body_start = day.end()
    inventory = predicate_forms if predicate_forms is not None else (
        _CONTENT_PREDICATES if content_only else _FINITE_PREDICATES)
    for finite, lemma, polarity, modality, time in inventory:
        if not value.endswith(finite):
            continue
        # Do not reinterpret a current wish as a past wish just to admit a
        # yesterday modifier. Its tense must already be explicit in the source.
        if relative_day == 'YESTERDAY' and time != 'past':
            continue
        end = len(value) - len(finite)
        offset, arguments = body_start, []
        parts = list(prefix_parts)
        while offset < end:
            argument = _ARGUMENT.match(value, offset, end)
            if argument is None:
                break
            noun = argument['noun']
            # A second/unparsed day cannot become a made-up compound noun.
            # 今日の資料 remains a nominal modifier, not an event date.
            if re.match(r'(?:今日|昨日)(?!の|$)', noun):
                break
            if re.search(r'(?:った|いた|した|んだ|ない|たい)$', noun):
                break
            arguments.append((argument['case'], noun))
            parts.append(('CASE_' + argument['case'], offset, argument.end()))
            offset = argument.end()
        if offset != end or len({case for case, _ in arguments}) != len(arguments):
            continue
        parts.append(('FINITE_PREDICATE', end, len(value)))
        return ObservedProposition(actor, tuple(arguments), lemma,
            polarity, modality, time, tuple(parts),
            marker, relative_day)
    return None


def _te_action_proposition(value):
    """Parse a dependent action without asserting that it happened."""
    subject = re.match(r'^(?:私|僕|わたし|自分)は', value)
    if subject is None:
        return None
    proposition = _finite_proposition(value, subject.end(), 'SELF',
        [('SELF_TOPIC', 0, subject.end())], predicate_forms=_TE_PREDICATES)
    if _has_unparsed_time_nominal(proposition):
        return None
    return replace(proposition, source_parts=tuple(
        ('DEPENDENT_PREDICATE' if role == 'FINITE_PREDICATE' else role, a, b)
        for role, a, b in proposition.source_parts)) if proposition else None


def _cognitive_proposition(value):
    """A proved present thinker plus a fully parsed, non-factual complement.

    The shared grammar owns the cognitive host. Its open lexical slot is not
    safe content until Analysis also understands the whole embedded clause.
    An omitted embedded subject stays unspecified, even under a SELF thinker.
    """
    subject = re.match(r'^(?:私|僕|わたし|自分)は', value)
    scopes = _source_current_cognition_parts(value) if subject else None
    if not scopes or {role for role, *_ in scopes} != {'possibility', 'cognition'}:
        return None
    bounds = {role: (a, b) for role, a, b, _ in scopes}
    a, b = bounds['possibility']
    c, d = bounds['cognition']
    suffix = re.search(r'(?:かもしれない|かも知れない|かも)$', value[a:b])
    if (a != subject.end() or d != len(value) or suffix is None
            or value[b:c] not in {'と', 'って'} or value[c:d] not in _COGNITIVE_HOSTS):
        return None
    content_end = a + suffix.start()
    content = _finite_proposition(value[:content_end], a, 'UNSPECIFIED', (), content_only=True)
    if content is None or content.modality != 'fact':
        return None
    content = replace(content, modality='possibility')
    parts = (('SELF_TOPIC', 0, a), *content.source_parts,
        ('POSSIBILITY_OPERATOR', content_end, b), ('COGNITIVE_CONNECTOR', b, c),
        ('PRESENT_COGNITIVE_HOST', c, d))
    return ObservedProposition('SELF', (), _COGNITIVE_HOSTS[value[c:d]],
        'neutral', 'fact', 'current_input', parts, possible_content=content)


def _proposition_meaning(proposition):
    content = proposition.possible_content
    return (proposition.actor, tuple(sorted(proposition.arguments)),
            proposition.predicate_lemma, proposition.result_state, proposition.scene_state, proposition.role_state,
            (_proposition_meaning(content), content.polarity, content.modality,
             content.temporal_scope) if content else None)


@dataclass(frozen=True, slots=True, repr=False)
class ObservedNode:
    node_ref: str
    node_kind: str
    visible_label: str
    record_refs: tuple[str, ...]
    evidence_refs: tuple[EvidenceRef, ...]
    polarity: str
    modality: str
    temporal_scope: str
    proposition: ObservedProposition | None = None
    update_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True, repr=False)
class ObservedSourceUpdate:
    update_ref: str
    operation: str
    record_ref: str
    target_evidence: EvidenceRef
    answer_evidence_refs: tuple[EvidenceRef, ...]
    replacement_evidence_refs: tuple[EvidenceRef, ...]


@dataclass(frozen=True, slots=True, repr=False)
class ObservedEdge:
    edge_ref: str
    edge_kind: str
    endpoint_refs: tuple[str, str]
    evidence_refs: tuple[EvidenceRef, ...]


@dataclass(frozen=True, slots=True)
class UnknownGap:
    gap_ref: str
    between_node_refs: tuple[str, ...]
    missing_scope: str
    reason_code: str


@dataclass(frozen=True, slots=True, repr=False)
class ObservedConflict:
    """Opposed written claims; shared occasion and truth remain unresolved."""
    conflict_ref: str
    target_refs: tuple[str, str]
    evidence_refs: tuple[EvidenceRef, ...]
    reason_code: str = 'OPPOSING_POLARITY_OCCASION_UNRESOLVED'


@dataclass(frozen=True, slots=True, repr=False)
class ObservedAnnotation:
    """A source-bound annotation, never a route step or an inferred cause."""
    annotation_ref: str
    target_ref: str
    predicate_lemma: str
    source_labels: tuple[str, ...]
    evidence_refs: tuple[EvidenceRef, ...]
    update_refs: tuple[str, ...] = ()
    kind: str = 'BURDEN'
    annotation_state: str = 'SOURCE_EXPLICIT_ANNOTATION'
    uncertainty: str = 'CAUSE_AND_DURATION_NOT_ESTABLISHED'
    alternative_explanations: tuple[str, ...] = ()
    forbidden_promotions: tuple[str, ...] = ('CAUSE', 'TRAIT', 'DIAGNOSIS', 'ROUTE_ORDER')


@dataclass(frozen=True, slots=True, repr=False)
class ObservedGraph:
    nodes: tuple[ObservedNode, ...]
    edges: tuple[ObservedEdge, ...]
    unknown_gaps: tuple[UnknownGap, ...]
    source_updates: tuple[ObservedSourceUpdate, ...] = ()
    conflicts: tuple[ObservedConflict, ...] = ()
    annotations: tuple[ObservedAnnotation, ...] = ()


@dataclass(frozen=True, slots=True, repr=False)
class PeriodChange:
    change_id: str
    change_kind: str
    current_ref: str
    previous_ref: str
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True, repr=False)
class PeriodComparison:
    comparison_id: str
    current_artifact_ref: str
    current_source_set_ref: str
    previous_artifact_ref: str
    previous_source_set_ref: str
    comparability_state: str
    reason_codes: tuple[str, ...]
    change_claims: tuple[PeriodChange, ...]


def _period_meaning_groups(graph):
    # IDs, source offsets, inflection and record counts are not semantic
    # differences. Keep the complete proposition operators and graph targets.
    def node_key(n):
        p = n.proposition
        if p is None:
            raise AnalysisSourceError('analysis_comparison_meaning_unavailable')
        return (n.node_kind, _proposition_meaning(p), n.polarity, n.modality,
                n.temporal_scope, p.relative_day, p.sequence_marker)
    nodes = {n.node_ref: n for n in graph.nodes}
    keys = {ref: node_key(n) for ref, n in nodes.items()}
    groups = {kind: {} for kind in ('ROUTE_EVIDENCE_CHANGED',
        'ANNOTATION_EVIDENCE_CHANGED', 'UNKNOWN_SCOPE_CHANGED', 'CONFLICT_STATE_CHANGED')}
    def add(kind, key, evidence):
        bucket = groups[kind].setdefault(key, [])
        bucket.extend(e.evidence_id for e in evidence if e.evidence_id not in bucket)
    for n in graph.nodes:
        add('ROUTE_EVIDENCE_CHANGED', ('node', keys[n.node_ref]), n.evidence_refs)
    for e in graph.edges:
        endpoints = tuple(keys[ref] for ref in e.endpoint_refs)
        if e.edge_kind == 'REPEATED_COOCCURRENCE':
            endpoints = frozenset(endpoints)
        add('ROUTE_EVIDENCE_CHANGED', ('edge', e.edge_kind, endpoints), e.evidence_refs)
    for a in graph.annotations:
        add('ANNOTATION_EVIDENCE_CHANGED', (a.kind, keys[a.target_ref],
            a.predicate_lemma, a.annotation_state, a.uncertainty), a.evidence_refs)
    for g in graph.unknown_gaps:
        # Missing-stage / unread-scope anchors and adjacent unknown pairs
        # are presentation positions, not claims about those particular
        # nodes. Compare the kinds of unresolved scope only. An explicit
        # missing predecessor really is attached to its written successor.
        target = (tuple(keys[ref] for ref in g.between_node_refs)
            if g.reason_code == 'EXPLICIT_PREDECESSOR_NOT_ESTABLISHED' else ())
        add('UNKNOWN_SCOPE_CHANGED', (target, g.missing_scope, g.reason_code),
            tuple(e for ref in g.between_node_refs for e in nodes[ref].evidence_refs))
    for c in graph.conflicts:
        add('CONFLICT_STATE_CHANGED', (frozenset(keys[ref] for ref in c.target_refs),
            c.reason_code), c.evidence_refs)
    return groups


def compare_period_meaning(current, previous):
    """Compare freshly compiled artifacts, never different stored policy versions.

    Called only by generation before current is returned. Absence from a
    period is not proof of absence from the person's life.
    """
    from .source_adapter import _time
    if current.owner_scope != previous.owner_scope:
        raise AnalysisSourceError('analysis_comparison_owner_mismatch')
    start, end = map(_time, current.period)
    before_start, before_end = map(_time, previous.period)
    reasons = []
    if end - start != before_end - before_start:
        reasons.append('PERIOD_LENGTH_MISMATCH')
    if before_start >= start:
        reasons.append('PREVIOUS_PERIOD_NOT_EARLIER')
    elif before_end > start:
        reasons.append('PERIOD_OVERLAP')
    elif before_end != start:
        reasons.append('PERIOD_NOT_ADJACENT')
    shared_records = ({m.saved_record_ref for m in current.source_members if m.inclusion_status == 'INCLUDED'}
        & {m.saved_record_ref for m in previous.source_members if m.inclusion_status == 'INCLUDED'})
    if shared_records:
        reasons.append('SHARED_RECORD_IDENTITY')
    changes = []
    if not reasons:
        now, before = _period_meaning_groups(current.graph), _period_meaning_groups(previous.graph)
        for kind in now:
            difference = now[kind].keys() ^ before[kind].keys()
            if not difference:
                continue
            # Keep evidence in deterministic graph order, not set iteration.
            evidence = tuple(dict.fromkeys(e for groups in (now, before)
                for key, refs in groups[kind].items() if key in difference for e in refs))
            if not evidence:
                raise AnalysisSourceError('analysis_comparison_evidence_unavailable')
            changes.append(PeriodChange('change' + str(len(changes) + 1), kind,
                current.reference, previous.reference, evidence))
    return PeriodComparison('comparison:' + commitment([current.reference, previous.reference])[7:],
        current.reference, current.source_set_ref, previous.reference, previous.source_set_ref,
        'NOT_COMPARABLE' if reasons else 'COMPARABLE', tuple(reasons), tuple(changes))


def _opposed_claim_pairs(claims):
    # Called for one original source only. Written day and field must agree;
    # never infer an occasion from created_at or compare different records.
    for index, (left, a, p) in enumerate(claims):
        for right, b, q in claims[index + 1:]:
            if (left != right and a.field_path == b.field_path
                    and a.source_envelope_id == b.source_envelope_id
                    and p.relative_day == q.relative_day
                    and p.polarity != q.polarity
                    and _proposition_meaning(p) == _proposition_meaning(q)):
                yield (left, right), (a, b)


def _node_kind(nucleus):
    frame = nucleus.semantic_frame
    codes = set(frame.attribute_codes)
    if nucleus.grounding_kind not in ('explicit', 'user_stated_relation'):
        return None
    if frame.actor != 'current_user':
        return None
    if source_proven_performed_action_status(nucleus):
        return 'ACTION_OR_NONACTION'
    if nucleus.kind == 'wish' and frame.modality == 'wish':
        return 'ATTENTION_OR_THOUGHT'
    if codes.intersection({'lexical:source_current_cognition',
            'lexical:source_self_appraisal', 'lexical:source_original_cognition'}):
        return 'ATTENTION_OR_THOUGHT'
    if (nucleus.kind == 'event' and frame.modality == 'fact' and
            'semantic_role:source_event' in codes):
        return 'SCENE'
    # Do not infer a role or a result from a generic reaction/change label.
    return None


def _action_change_pair(source, plan, span_id):
    """Prove both endpoints and the whole written past-after episode.

    The shared relation is necessary but may also wrap dreams/reports. Its
    marker alone cannot license either endpoint. Analysis consumes every
    character and only projects order, never causal support or improvement.
    """
    if plan is None:
        return None
    rows = [n for n in plan.nuclei if span_id in n.source_span_ids]
    if len(rows) != 2:
        return None
    action, change = rows
    if (action.kind != 'action' or change.kind != 'change'
            or not source_proven_performed_action_status(action)
            or change.semantic_frame.predicate_kind != 'change'):
        return None
    ranges = []
    for n in rows:
        f = n.semantic_frame
        codes = f.attribute_codes
        bounds = [c for c in codes if c.startswith('source_fragment_scalar_range:')]
        if (n.source_span_ids != (span_id,) or n.source_fields != ('memo',)
                or n.grounding_kind != 'explicit' or n.retention != 'required'
                or n.allowed_claim_scope != 'explicit_current_input'
                or f.actor != 'current_user' or f.time_scope != 'past'
                or (n is action and f.modality != 'fact')
                or (n is change and f.modality not in {'fact', 'feeling'})
                or 'semantic_dependency:action_before_change' not in codes
                or 'source_fragment_scalar_source:normalized_raw_text' not in codes
                or len(bounds) != 1 or any(c.startswith(('surface_scalar_', 'thread_time:')) for c in codes)):
            return None
        ranges.append(tuple(map(int, bounds[0].split(':')[1:])))
    links = [r for r in plan.relations if r.from_nucleus_id == action.nucleus_id
             and r.to_nucleus_id == change.nucleus_id]
    if (len(links) != 1 or links[0].type != 'action_supports_change'
            or links[0].grounding_kind != 'user_stated_relation' or links[0].retention != 'required'
            or links[0].source_span_ids != (span_id,)
            or links[0].source_relation_ids != ('typed_projection:perfective_action_before_bounded_change',)):
        return None
    span = next((s for s in source.spans if s.span_id == span_id), None)
    if span is None or span.source_field != 'memo':
        return None
    raw = span.raw_text
    (a, b), (c, d) = ranges
    if not (a == 0 < b < c < d == len(raw)):
        return None
    connector = raw[b:c]
    te_after = re.fullmatch(r'から[、,]\s*', connector) is not None
    if not te_after and re.fullmatch(r'(?:後|あと)(?:に)?[、,]\s*', connector) is None:
        return None
    left = _te_action_proposition(raw[a:b]) if te_after else _proposition(raw[a:b])
    right = _bounded_change_proposition(raw[c:d])
    if (left is None or right is None or _has_unparsed_time_nominal(right) or left.actor != 'SELF'
            or left.result_state or left.scene_state or left.role_state or left.possible_content or left.relative_day or left.sequence_marker
            or any(re.search(r'(?:^|の)(?:何|誰|幾)', noun) for _, noun in left.arguments)
            or (left.polarity, left.modality, left.temporal_scope) !=
                ('positive', 'fact', 'dependent' if te_after else 'past')):
        return None
    # The shared owner marks reassurance as fact and the other admitted
    # feeling predicates as feeling. Match that witness exactly; Analysis
    # retains all of these as a reported experience, never a performed action.
    expected_modality = ('feeling' if right.result_state == 'PAST_FEELING'
                         and right.predicate_lemma != '安心する' else 'fact')
    if change.semantic_frame.modality != expected_modality:
        return None
    if te_after:
        # Past is established by this whole episode and its shared witness,
        # never by the te ending. Source parts still point to the written te.
        left = replace(left, temporal_scope='past', dependent_form='TE_BEFORE_PAST_CHANGE')
    return action.nucleus_id, change.nucleus_id, ranges, left, right


def _fragment(source, nucleus, plan=None):
    # Multi-span nuclei can contain unbounded relations. Keep them unknown in
    # this first consumer rather than stitching a new proposition together.
    if len(nucleus.source_span_ids) != 1:
        return None
    span_id = nucleus.source_span_ids[0]
    ref = next((r for r in source.evidence if r.source_span_id == span_id), None)
    span = next((s for s in source.spans if s.span_id == span_id), None)
    if ref is None or span is None:
        return None
    a, b = 0, len(span.raw_text)
    codes = nucleus.semantic_frame.attribute_codes
    compound = any('semantic_dependency:action_before_change' in n.semantic_frame.attribute_codes
                   for n in plan.nuclei if span_id in n.source_span_ids) if plan else False
    pair = _action_change_pair(source, plan, span_id) if compound else None
    if compound and pair is None:
        return None
    ranges = [c for c in codes if c.startswith((
        'surface_scalar_range:', 'source_fragment_scalar_range:'))]
    if ranges:
        if len(ranges) != 1:
            return None
        prefix, raw_a, raw_b = ranges[0].split(':')
        witness = prefix.replace('_range', '_source') + ':normalized_raw_text'
        if witness not in codes:
            return None
        a, b = int(raw_a), int(raw_b)
        if not (0 <= a < b <= len(span.raw_text)):
            return None
    # Analysis preserves the whole finite host including negation/modality.
    # Quote, report and conditional scopes need additional route semantics;
    # their presence is explicit in unknown gaps rather than silently dropped.
    context = source.normalized.get(span.source_field, '')
    if re.search(r'[「」『』“”"?？]|(?:と言われ|と聞い|そうだ|なら|(?<!か)もし)', context):
        return None
    # An uncertain complement is allowed only inside a complete, shared-owner
    # cognitive witness. Unread speculative scopes still block the field.
    if re.search(r'かもしれ|かも知れ', context):
        proved = {n.source_span_ids[0] for n in plan.nuclei
                  if _source_current_cognition(n)} if plan is not None else set()
        if any(s.span_id not in proved or _cognitive_proposition(s.raw_text) is None
               for s in source.spans if s.source_field == span.source_field
               and re.search(r'かもしれ|かも知れ', s.raw_text)):
            return None
    # An open reported speaker can carry across sentences and source fields.
    # First-person grammar alone cannot close that attribution scope.
    record_context = '\n'.join(str(source.normalized.get(field, ''))
                               for field in ('memo', 'memo_action'))
    if re.search(r'によると|いわく|曰く|の(?:話|感想|気持ち|説明|報告|発言)(?:です|だ|[。．.])',
                 record_context):
        return None
    value = span.raw_text[a:b].strip(' 、，。．')
    if not value:
        return None
    proposition = _parsed_proposition(value)
    if _has_unparsed_time_nominal(proposition):
        # Use the existing unresolved-source path; never fall back to a
        # raw node that would also make unrelated readable nodes unsafe.
        return None
    if _cognitive_proposition(value) is not None and not _source_current_cognition(nucleus):
        return None
    result = _unfinished_result_proposition(value)
    change = _bounded_change_proposition(value)
    if change is not None and (pair is None or nucleus.nucleus_id != pair[1]):
        return None
    if result is not None and not _unfinished_result_witness(nucleus):
        return None
    event = _past_event_proposition(value)
    if event is not None and (a != 0 or b != len(span.raw_text)
            or not _past_event_witness(nucleus, event)):
        return None
    protective = _protective_wish_proposition(value)
    if protective is not None and (a != 0 or b != len(span.raw_text)
            or not _protective_wish_witness(nucleus)):
        return None
    if event is not None or protective is not None:
        # An open report/dream can carry across a sentence boundary; a
        # local SELF event or wish cannot close that attribution scope.
        if re.search(r'(?:聞いた|聞きました|読んだ|読みました)(?:話|内容)|夢を見',
                     record_context):
            return None
        # The ledger also splits long sentences at commas or fixed lengths.
        # A complete span is not necessarily a complete finite host. Check
        # the parser field (or proved correction view), retaining newlines as
        # boundaries; evidence below still addresses the unchanged original.
        before = context[:span.start_index].rstrip(' \t\u3000')
        after = context[span.end_index:].lstrip(' \t\u3000')
        if ((before and before[-1] not in '。．.!！\r\n')
                or (after and after[0] not in '。．.!！\r\n')):
            return None
    # current_user is the shared frame's default, not proof of its subject.
    # Actions/thoughts require an explicit first-person finite host. Only a
    # witnessed, fully parsed non-agent result state is the bounded exception.
    if result is None and change is None and not re.match(r'^(?:(?:今日|昨日|その後|それから)[、，\s]*)?(?:私は|僕は|わたしは|自分は)', value):
        return None
    # The source helper already proved a length-preserving normalization.
    field = source.envelope.raw_utf8[ref.field_utf8_start:ref.field_utf8_end].decode('utf-8')
    start, end = ref.scalar_start + a, ref.scalar_start + b
    literal = field[start:end]
    if literal.replace('\u3000', ' ').strip() != span.raw_text[a:b].strip():
        raise AnalysisSourceError('analysis_fragment_evidence_mismatch')
    evidence = replace(ref,
        evidence_id='analysis-evidence:' + commitment([ref.source_envelope_id,
            ref.field_path, start, end])[7:],
        scalar_start=start, scalar_end=end,
        utf8_start=ref.field_utf8_start + len(field[:start].encode('utf-8')),
        utf8_end=ref.field_utf8_start + len(field[:end].encode('utf-8')),
        literal_sha256=hashlib.sha256(literal.encode('utf-8')).hexdigest())
    proposition = (pair[3] if nucleus.nucleus_id == pair[0] else pair[4]) if pair else proposition
    return value, evidence, proposition


def _burden_predicate(value):
    # Complete affirmative present inflections, not negative polarity alone.
    # In particular, an absent positive feeling does not prove a burden.
    match = re.fullmatch(r'(?:私|僕|わたし|自分)は(?P<predicate>つらい|苦しい)(?:です)?', value)
    return match['predicate'] if match else None


def _wish_burden_pair(source, plan, span_id):
    """Consume one complete, shared-owner contrast with two explicit selves."""
    rows = [n for n in plan.nuclei if span_id in n.source_span_ids]
    if len(rows) != 2:
        return None
    wish, burden = rows
    for n in rows:
        f = n.semantic_frame
        codes = f.attribute_codes
        if (n.source_span_ids != (span_id,) or n.source_fields != ('memo',)
                or n.grounding_kind not in {'explicit', 'user_stated_relation'}
                or n.retention != 'required' or n.allowed_claim_scope != 'explicit_current_input'
                or f.actor != 'current_user' or f.time_scope != 'current_input'
                or 'semantic_role:generic_relation_fragment' not in codes
                or 'source_fragment_scalar_source:normalized_raw_text' not in codes
                or len([c for c in codes if c.startswith('source_fragment_scalar_range:')]) != 1
                or any(c.startswith(('surface_scalar_', 'thread_time:', 'semantic_dependency:')) for c in codes)):
            return None
    w, b = wish.semantic_frame, burden.semantic_frame
    if ((wish.kind, w.predicate_kind, w.polarity, w.modality) != ('wish', 'wish', 'positive', 'wish')
            or (burden.kind, b.predicate_kind, b.polarity, b.modality) != ('reaction', 'feeling', 'negative', 'feeling')
            or 'lexical:source_finite_contrast_feeling' not in b.attribute_codes):
        return None
    links = [r for r in plan.relations if r.from_nucleus_id == wish.nucleus_id
             and r.to_nucleus_id == burden.nucleus_id]
    if (len(links) != 1 or links[0].type != 'contrast'
            or links[0].grounding_kind != 'user_stated_relation' or links[0].retention != 'required'
            or links[0].source_span_ids != (span_id,)
            or links[0].source_relation_ids != ('typed_projection:top_level_connective',)
            or links[0].source_meaning_arc_keys != ('compound_span:top_level_relation',)):
        return None
    span = next((s for s in source.spans if s.span_id == span_id), None)
    whole = next((r for r in source.evidence if r.source_span_id == span_id), None)
    if span is None or whole is None or span.source_field != 'memo':
        return None
    # Long ledger fragments must not erase a reporting/dream host or modifier.
    context = source.normalized.get('memo', '')
    before, after = context[:span.start_index].rstrip(' \t\u3000'), context[span.end_index:].lstrip(' \t\u3000')
    if ((before and before[-1] not in '。．.!！\r\n')
            or (after and after[0] not in '。．.!！\r\n')):
        return None
    left, right = _fragment(source, wish, plan), _fragment(source, burden, plan)
    if left is None or right is None or left[2] is None:
        return None
    p, a, z = left[2], left[1], right[1]
    predicate = _burden_predicate(right[0])
    if (predicate is None or p.actor != 'SELF' or p.possible_content
            or p.sequence_marker or p.relative_day
            or (p.polarity, p.modality, p.temporal_scope) != ('positive', 'wish', 'current_input')
            or any(re.search(r'(?:^|の)(?:何|誰|幾)', noun) for _, noun in p.arguments)
            or not (whole.scalar_start == a.scalar_start < a.scalar_end < z.scalar_start < z.scalar_end == whole.scalar_end)):
        return None
    connector = source_field_text(source, 'memo')[a.scalar_end:z.scalar_start]
    if re.fullmatch(r'(?:けれども|けれど|けど|が)[、,]?\s*', connector) is None:
        return None
    return wish.nucleus_id, burden.nucleus_id, predicate, right[0], (a, z, whole)


def _self_propositions(source, *, require_complete=False, plan=None):
    """Read existing grammatical claims, retaining original field coordinates.

    An ordinary answer must stand on its own. Unread text may qualify, retract
    or correct the apparent claim, so a parsed fragment is not enough.
    """
    if plan is None:
        plan = build_final_stage1_grounded_observation_plan(
            source.normalized, evidence_spans=source.spans)
    if plan.input_profile.material_quality == 'safety_routed':
        raise AnalysisSourceError('analysis_separate_safety_required')
    claims = []
    for nucleus in plan.nuclei:
        if (nucleus.grounding_kind not in ('explicit', 'user_stated_relation')
                or nucleus.semantic_frame.actor != 'current_user'):
            continue
        fragment = _fragment(source, nucleus, plan)
        proposition = fragment[2] if fragment else None
        if proposition is not None:
            claims.append((proposition, fragment[1]))
    if require_complete:
        raw = source_field_text(source, 'memo')
        covered = set()
        for _, evidence in claims:
            if evidence.field_path == 'memo':
                covered.update(range(evidence.scalar_start, evidence.scalar_end))
        # The connector belongs to the pair, not to either finite endpoint.
        for span in source.spans:
            pair = _action_change_pair(source, plan, span.span_id)
            if pair and sum(e.source_span_id == span.span_id for _, e in claims) == 2:
                ref = next(r for r in source.evidence if r.source_span_id == span.span_id)
                covered.update(range(ref.scalar_start, ref.scalar_end))
            annotation = _wish_burden_pair(source, plan, span.span_id)
            if annotation and any(e == annotation[4][0] for _, e in claims):
                whole = annotation[4][2]
                covered.update(range(whole.scalar_start, whole.scalar_end))
        # Deliberately not all punctuation: question marks, quotes and other
        # unparsed operators cannot be treated as harmless sentence separators.
        if not claims or any(i not in covered and char not in ' \t\r\n\u3000。．.'
                             for i, char in enumerate(raw)):
            raise AnalysisSourceError('analysis_supplement_interpretation_pending')
    return tuple(claims)


def _explicit_order_pairs(source, plan, withdrawn):
    """Bind a written connective to adjacent complete clauses in one field.

    The shared plan establishes the claims, while Analysis owns this relation.
    Never bridge an unread clause, another field/source, or a removed target.
    A current wish is not proof that a later action occurred.
    """
    whole = {(r.field_path, r.scalar_start, r.scalar_end) for r in source.evidence}
    all_claims = _self_propositions(source, plan=plan)
    claims = {e.evidence_id: (p, e) for p, e in all_claims
              if e.source_span_id not in withdrawn
              and (e.field_path, e.scalar_start, e.scalar_end) in whole}
    ordered = sorted(claims.values(), key=lambda item:
                     (item[1].field_path, item[1].scalar_start, item[1].scalar_end))
    pairs = []
    for (left, a), (right, b) in zip(ordered, ordered[1:]):
        if (a.field_path != b.field_path or a.scalar_end >= b.scalar_start
                or right.sequence_marker not in {'AFTER_PREVIOUS', 'THEN_OR_ADDITION'}
                or (left.modality, right.modality) != ('fact', 'fact')
                or (left.temporal_scope, right.temporal_scope) != ('past', 'past')):
            continue
        separator = source_field_text(source, a.field_path)[a.scalar_end:b.scalar_start]
        if (re.fullmatch(r'[。．.\s]+', separator)
                and any(char in separator for char in '。．.\r\n')):
            pairs.append((a, b))
    for span in source.spans:
        if span.span_id in withdrawn or not _action_change_pair(source, plan, span.span_id):
            continue
        endpoints = sorted((e for _, e in all_claims if e.source_span_id == span.span_id),
                           key=lambda e: e.scalar_start)
        if len(endpoints) == 2:
            pairs.append(tuple(endpoints))
    return tuple(pairs)


def _admit_ordinary_supplement(answer, original):
    claims = _self_propositions(answer, require_complete=True)
    earlier = [(p, original.envelope.envelope_id) for p, _ in _self_propositions(original)]
    for current, _ in claims:
        for previous, source_id in earlier:
            # Without an explicit correction target, do not choose between
            # opposing descriptions of the same possible action/wish. Missing
            # arguments do not prove a different occasion or a different object.
            a, b = dict(current.arguments), dict(previous.arguments)
            compatible_arguments = all(a[case] == b[case] for case in a.keys() & b.keys())
            # Relative days distinguish occasions only within one statement
            # source. An answer's yesterday may be its original input's today.
            separate_days = (source_id == answer.envelope.envelope_id
                and current.relative_day and previous.relative_day
                and current.relative_day != previous.relative_day)
            if (current.actor == previous.actor
                    and current.predicate_lemma == previous.predicate_lemma
                    and current.modality == previous.modality
                    and current.temporal_scope == previous.temporal_scope
                    and current.polarity != previous.polarity
                    and compatible_arguments and not separate_days):
                raise AnalysisSourceError('analysis_supplement_interpretation_pending')
        earlier.append((current, answer.envelope.envelope_id))


def _active_sources(source_set):
    """Apply whole-clause corrections to occurrences before period grouping."""
    originals = {s.record_ref: s for s in source_set.sources
                 if s.envelope.source_role == 'ORIGINAL_INPUT'}
    excluded, views, updates, replacement_updates = {}, [], [], {}
    for answer in source_set.sources:
        if answer.envelope.source_role != 'SUPPLEMENTAL_ANSWER':
            views.append(answer)
            continue
        raw = source_field_text(answer, 'memo')
        text = raw.strip().rstrip('。．.')
        replacement, withdrawal = _REPLACEMENT.fullmatch(text), _WITHDRAWAL.fullmatch(text)
        match = replacement or withdrawal
        original = originals.get(answer.record_ref)
        if original is None:
            raise AnalysisSourceError('analysis_supplement_parent_missing')
        if match is None:
            _admit_ordinary_supplement(answer, original)
            views.append(answer)
            continue
        old = match['old'].rstrip('。．.')
        targets = []
        for ref in original.evidence:
            field = source_field_text(original, ref.field_path)
            literal = field[ref.scalar_start:ref.scalar_end]
            prefix, suffix = field[:ref.scalar_start].rstrip(), field[ref.scalar_end:].lstrip()
            if (literal.replace('\u3000', ' ').strip().rstrip('。．.') == old
                    and (not prefix or prefix[-1] in '。．.!！?？')
                    and (not suffix or suffix[0] in '。．.!！?？')):
                targets.append(ref)
        if len(targets) != 1:
            raise AnalysisSourceError('analysis_correction_target_unresolved')
        target = targets[0]
        original_plan = build_final_stage1_grounded_observation_plan(
            original.normalized, evidence_spans=original.spans)
        target_is_self_claim = False
        for nucleus in original_plan.nuclei:
            if (nucleus.source_span_ids != (target.source_span_id,)
                    or nucleus.grounding_kind not in ('explicit', 'user_stated_relation')
                    or nucleus.semantic_frame.actor != 'current_user'):
                continue
            fragment = _fragment(original, nucleus, original_plan)
            if (fragment and (fragment[1].scalar_start, fragment[1].scalar_end) ==
                    (target.scalar_start, target.scalar_end)
                    and fragment[2] is not None):
                target_is_self_claim = True
        # Quote location alone cannot prove that a reported first-person
        # clause belongs to the current user. Preserve its original scope.
        if not target_is_self_claim and _action_change_pair(original, original_plan, target.source_span_id):
            target_is_self_claim = sum(e.source_span_id == target.source_span_id
                for _, e in _self_propositions(original, plan=original_plan)) == 2
        if not target_is_self_claim:
            target_is_self_claim = _wish_burden_pair(original, original_plan, target.source_span_id) is not None
        if not target_is_self_claim:
            raise AnalysisSourceError('analysis_correction_target_unresolved')
        excluded.setdefault(original.envelope.envelope_id, set()).add(target.source_span_id)
        view = None
        if replacement:
            leading = len(raw) - len(raw.lstrip())
            view = scoped_source_view(answer, leading + match.start('new'),
                                      leading + match.end('new'))
            views.append(view)
        update = ObservedSourceUpdate('analysis-update:' + commitment([
            answer.envelope.envelope_id, target.evidence_id,
            'REVISE' if replacement else 'WITHDRAW'])[7:],
            'REVISE' if replacement else 'WITHDRAW', answer.record_ref,
            target, answer.evidence, view.evidence if view else ())
        updates.append(update)
        if view:
            replacement_updates[view.envelope.envelope_id] = update.update_ref
    return tuple(views), excluded, tuple(updates), replacement_updates


def compile_observed_graph(source_set: AnalysisSourceSet) -> ObservedGraph:
    active_sources, excluded, updates, replacement_updates = _active_sources(source_set)
    nodes, edges, gaps = [], [], []
    conflict_evidence = {}
    annotation_claims = {}
    unresolved_records = set()
    by_signature, occurrences, record_orders = {}, {}, {}
    for source in active_sources:
        plan = build_final_stage1_grounded_observation_plan(
            source.normalized, evidence_spans=source.spans)
        if plan.input_profile.material_quality == 'safety_routed':
            raise AnalysisSourceError('analysis_separate_safety_required')
        order_pairs = _explicit_order_pairs(source, plan,
            excluded.get(source.envelope.envelope_id, set()))
        ordered_evidence = {e.evidence_id for pair in order_pairs for e in pair}
        admitted, by_evidence, unresolved = {}, {}, False
        comparable_claims = []
        annotation_pairs = [pair for span in source.spans
            if span.span_id not in excluded.get(source.envelope.envelope_id, set())
            and (pair := _wish_burden_pair(source, plan, span.span_id))]
        annotation_nuclei = {pair[1] for pair in annotation_pairs}
        for nucleus in plan.nuclei:
            if set(nucleus.source_span_ids) & excluded.get(source.envelope.envelope_id, set()):
                continue
            if nucleus.nucleus_id in annotation_nuclei:
                continue
            explicit = (nucleus.grounding_kind in ('explicit', 'user_stated_relation')
                        and nucleus.semantic_frame.actor == 'current_user')
            fragment = _fragment(source, nucleus, plan) if explicit else None
            proposition = fragment[2] if fragment else None
            # A shared nucleus alone does not prove the complete clause.
            # Keep unparsed original text in the existing unknown scope so
            # it cannot make independently readable nodes unprojectable.
            kind = _proposition_node_kind(proposition) if proposition else None
            if not kind:
                fragment = None
            if fragment is None:
                if any(s.source_field in ('memo', 'memo_action') and
                       s.span_id in nucleus.source_span_ids for s in source.spans):
                    unresolved = True
                continue
            label, evidence, _ = fragment
            frame = nucleus.semantic_frame
            polarity, modality, time = ((proposition.polarity, proposition.modality,
                proposition.temporal_scope) if proposition else
                (frame.polarity, frame.modality, frame.time_scope))
            update_ref = replacement_updates.get(source.envelope.envelope_id)
            node_updates = (update_ref,) if update_ref else ()
            # Exact grammatical equivalence, not synonymous/topic matching.
            # A polite restatement or reordered cases is still one claim;
            # preserve each source witness without inventing a cooccurrence.
            meaning = _proposition_meaning(proposition) if proposition else label
            # A sequence is about occurrences: collapsing A -> B -> A by
            # proposition would create a false cycle or erase repeated A.
            # Ordinary, unqualified claims retain their existing aggregation.
            occurrence_scope = (evidence.evidence_id if evidence.evidence_id in ordered_evidence
                or (proposition and proposition.sequence_marker) else None)
            # A relative day is anchored to its own input/answer, not to the
            # viewing date or the parent's created_at. Only equivalent claims
            # in that same source and day retain ordinary aggregation.
            day_scope = ((source.envelope.envelope_id, proposition.relative_day)
                         if proposition and proposition.relative_day else None)
            signature = (kind, meaning, polarity, modality, time, occurrence_scope, day_scope)
            index = by_signature.get(signature)
            if index is None:
                index = len(nodes)
                by_signature[signature] = index
                nodes.append(ObservedNode('n' + str(index + 1), kind, label,
                    (source.record_ref,), (evidence,), polarity,
                    modality, time, proposition, node_updates))
            else:
                old = nodes[index]
                nodes[index] = replace(old,
                    record_refs=tuple(dict.fromkeys((*old.record_refs, source.record_ref))),
                    evidence_refs=tuple(dict.fromkeys((*old.evidence_refs, evidence))),
                    update_refs=tuple(dict.fromkeys((*old.update_refs, *node_updates))))
            node = nodes[index]
            if (source.envelope.source_role == 'ORIGINAL_INPUT'
                    and proposition and proposition.actor == 'SELF'
                    and (modality, time) == ('fact', 'past')
                    and polarity in {'positive', 'negative'}
                    and kind in {'SCENE', 'ROLE', 'ACTION_OR_NONACTION'}
                    and not proposition.sequence_marker and not proposition.dependent_form
                    and evidence.evidence_id not in ordered_evidence):
                comparable_claims.append((node.node_ref, evidence, proposition))
            admitted[nucleus.nucleus_id] = node.node_ref
            by_evidence[evidence.evidence_id] = node.node_ref
            occurrences.setdefault(source.record_ref, set()).add(node.node_ref)
            if proposition and _protective_wish_proposition(label) == proposition:
                key = ('PROTECTIVE', node.node_ref)
                old = annotation_claims.get(key)
                if old is None:
                    annotation_claims[key] = ObservedAnnotation(
                        'a' + str(len(annotation_claims) + 1), node.node_ref,
                        '守る', (label,), (evidence,), node_updates, kind='PROTECTIVE',
                        uncertainty='PROTECTION_OUTCOME_AND_ACTION_MOTIVE_NOT_ESTABLISHED',
                        forbidden_promotions=('PROTECTION_OUTCOME', 'ACTION_MOTIVE',
                                              'CAUSE', 'TRAIT', 'DIAGNOSIS', 'ROUTE_ORDER'))
                else:
                    annotation_claims[key] = replace(old,
                        source_labels=tuple(dict.fromkeys((*old.source_labels, label))),
                        evidence_refs=tuple(dict.fromkeys((*old.evidence_refs, evidence))),
                        update_refs=tuple(dict.fromkeys((*old.update_refs, *node_updates))))
        for wish_id, _, predicate, label, evidence in annotation_pairs:
            target = admitted.get(wish_id)
            if target is None:
                unresolved = True
                continue
            key = (target, predicate)
            update_ref = replacement_updates.get(source.envelope.envelope_id)
            old = annotation_claims.get(key)
            if old is None:
                annotation_claims[key] = ObservedAnnotation('a' + str(len(annotation_claims) + 1),
                    target, predicate, (label,), evidence, (update_ref,) if update_ref else ())
            else:
                annotation_claims[key] = replace(old,
                    source_labels=tuple(dict.fromkeys((*old.source_labels, label))),
                    evidence_refs=tuple(dict.fromkeys((*old.evidence_refs, *evidence))),
                    update_refs=tuple(dict.fromkeys((*old.update_refs, *((update_ref,) if update_ref else ())))))
        for targets, evidence in _opposed_claim_pairs(comparable_claims):
            targets = tuple(sorted(targets, key=lambda ref: int(ref[1:])))
            conflict_evidence[targets] = tuple(dict.fromkeys(
                (*conflict_evidence.get(targets, ()), *evidence)))
        # The whole replacement, not just a convenient sub-clause, must be
        # interpreted. Otherwise no old result can be returned as current.
        if source.envelope.envelope_id in replacement_updates and (not admitted or unresolved):
            raise AnalysisSourceError('analysis_correction_replacement_unsupported')
        for a, b in order_pairs:
            endpoints = (by_evidence.get(a.evidence_id), by_evidence.get(b.evidence_id))
            if all(endpoints) and endpoints[0] != endpoints[1]:
                # A compound's whole source also witnesses its connective.
                relation_evidence = ((a, b) + tuple(r for r in source.evidence
                    if r.source_span_id == a.source_span_id)) if a.source_span_id == b.source_span_id else (a, b)
                edges.append(ObservedEdge('e' + str(len(edges) + 1),
                    'OBSERVED_ORDER', endpoints, relation_evidence))
                record_orders.setdefault(source.record_ref, set()).add(endpoints)
        if unresolved or (not admitted and any(
                s.source_field in ('memo', 'memo_action') and
                s.span_id not in excluded.get(source.envelope.envelope_id, set())
                for s in source.spans)):
            unresolved_records.add(source.record_ref)
    # Original and supplemental content are one occasion. Determine gaps only
    # after both have contributed, not independently for each source child.
    for record_ref, ids in occurrences.items():
        anchors = tuple(n.node_ref for n in nodes if n.node_ref in ids)
        present = {n.node_kind for n in nodes if n.node_ref in ids}
        for kind in NODE_KINDS:
            if kind not in present:
                gaps.append(UnknownGap('g' + str(len(gaps) + 1), anchors[:1],
                    kind, 'NOT_ESTABLISHED_FROM_SOURCE'))
        if record_ref in unresolved_records:
            gaps.append(UnknownGap('g' + str(len(gaps) + 1), anchors[:1],
                'SOURCE_SCOPE', 'UNSUPPORTED_OR_UNCERTAIN_SOURCE_SCOPE'))
        known_pairs = record_orders.get(record_ref, set())
        for pair in zip(anchors, anchors[1:]):
            if pair not in known_pairs and pair[::-1] not in known_pairs:
                gaps.append(UnknownGap('g' + str(len(gaps) + 1), pair,
                    'ROUTE_CONNECTION', 'ONLY_EXPLICIT_ORDER_IS_SHOWN'))
        for node in nodes:
            if (node.node_ref in ids and node.proposition
                    and node.proposition.sequence_marker
                    and not any(pair[1] == node.node_ref for pair in known_pairs)):
                gaps.append(UnknownGap('g' + str(len(gaps) + 1), (node.node_ref,),
                    'ROUTE_CONNECTION', 'EXPLICIT_PREDECESSOR_NOT_ESTABLISHED'))
    if nodes and unresolved_records - occurrences.keys():
        gaps.append(UnknownGap('g' + str(len(gaps) + 1), (nodes[0].node_ref,),
            'SOURCE_SCOPE', 'UNSUPPORTED_OR_UNCERTAIN_SOURCE_SCOPE'))
    # A supplemental answer shares its original's occasion. Two fields or two
    # answers from one record therefore never turn into a repeated pattern.
    for i, left in enumerate(nodes):
        for right in nodes[i + 1:]:
            together = [ref for ref, ids in occurrences.items()
                        if {left.node_ref, right.node_ref} <= ids]
            if len(together) < 2:
                continue
            supporting_envelopes = {s.envelope.envelope_id for s in source_set.sources
                                    if s.record_ref in together}
            refs = tuple(dict.fromkeys(r for r in (*left.evidence_refs, *right.evidence_refs)
                                      if r.source_envelope_id in supporting_envelopes))
            edges.append(ObservedEdge('e' + str(len(edges) + 1),
                'REPEATED_COOCCURRENCE', (left.node_ref, right.node_ref), refs))
    conflicts = tuple(ObservedConflict('c' + str(index), targets, evidence)
        for index, (targets, evidence) in enumerate(conflict_evidence.items(), 1))
    return ObservedGraph(tuple(nodes), tuple(edges), tuple(gaps), updates, conflicts,
                         tuple(annotation_claims.values()))
