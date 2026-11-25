"""Bind relations between admitted structures to complete original action statements."""
from dataclasses import dataclass, field
from itertools import combinations
import json
import re


MAX_RELATIONS = 12


@dataclass(frozen=True)
class OriginalSpan:
    """Exact Unicode scalar offsets in a numbered snapshot field."""

    field_number: int
    start: int
    end: int
    quote: str = field(repr=False)


@dataclass(frozen=True)
class AdmittedStructure:
    ref: int
    literal_factor: str = field(repr=False)
    roots: tuple[OriginalSpan, ...] = field(repr=False)


@dataclass(frozen=True)
class WitnessedStructureRelation:
    kind: str
    first_ref: int
    second_ref: int
    settlement: OriginalSpan = field(repr=False)
    first_grounding: OriginalSpan = field(repr=False)
    second_grounding: OriginalSpan = field(repr=False)
    first_factor: OriginalSpan = field(repr=False)
    second_factor: OriginalSpan = field(repr=False)
    selected_option: OriginalSpan = field(repr=False)
    confirmed_outcome: OriginalSpan | None = field(repr=False)


_FACTOR = re.compile(r'[\w・ ]{2,32}')
_OPTION = r'(?P<option>[\w・ ]{2,40})'


def _original_field(fields, span):
    source = fields.get(span.field_number)
    if (source and source['source_role'] == 'ORIGINAL_INPUT'
            and source['field_path'] in ('memo', 'memo_action')
            and source.get('fragment_is_complete_field', True)
            and 0 <= span.start < span.end <= len(source['text'])
            and source['text'][span.start:span.end] == span.quote):
        return source
    return None


def _independent_grounding(fields, axis, excluded_records):
    return next((root for root in axis.roots if axis.literal_factor in root.quote
                 and (source := _original_field(fields, root))
                 and source['record'] not in excluded_records), None)


def _match_choice(text, first, second):
    first_factor = rf'(?P<first>{re.escape(first)})'
    second_factor = rf'(?P<second>{re.escape(second)})'
    coexistence = re.fullmatch(
        rf'私は、{first_factor}と{second_factor}を両立できると判断して、'
        rf'{_OPTION}を選び、実際に(?P<outcome>(?P=first)と(?P=second)を両立できました)。', text)
    if coexistence:
        return 'COEXISTENCE', coexistence

    # For priority, the first structure is the one favored in this choice.
    priority = re.fullmatch(
        rf'私は、{second_factor}より{first_factor}を優先して、{_OPTION}を選び'
        r'(?:ました|、実際に(?P<outcome>(?P=second)を確保できませんでした))。', text)
    return ('PRIORITY', priority) if priority else (None, None)


def admit_witnessed_structure_relation(fields, first, second, settlement):
    """Return private proof only where both criteria occur in one actual choice."""
    if (first.ref == second.ref or first.literal_factor == second.literal_factor
            or not all(_FACTOR.fullmatch(axis.literal_factor) for axis in (first, second))):
        return None

    source = _original_field(fields, settlement)
    if not source or source['field_path'] != 'memo_action' or settlement.quote != source['text']:
        return None

    # A companion memo or later correction can qualify the original action.
    # This reader only interprets a standalone complete source field.
    if any(entry['record'] == source['record'] and entry['field'] != source['field']
           for entry in fields.values()):
        return None
    supplemented = {entry['record'] for entry in fields.values() if entry['source_role'] != 'ORIGINAL_INPUT'}

    # Each axis needs grounding of its own beyond the shared choice record and
    # beyond the records used by the other structure. Only exact originals count.
    def origin_records(axis):
        return {root_source['record'] for root in axis.roots
                if (root_source := _original_field(fields, root))}

    unavailable = supplemented | {source['record']}
    first_grounding = _independent_grounding(fields, first, origin_records(second) | unavailable)
    second_grounding = _independent_grounding(fields, second, origin_records(first) | unavailable)
    if first_grounding is None or second_grounding is None:
        return None

    kind, match = _match_choice(settlement.quote, first.literal_factor, second.literal_factor)
    if match is None:
        first, second = second, first
        first_grounding, second_grounding = second_grounding, first_grounding
        kind, match = _match_choice(settlement.quote, first.literal_factor, second.literal_factor)
    if match is None:
        return None

    def located_span(name):
        start, end = match.span(name)
        return OriginalSpan(settlement.field_number, start, end, match[name])

    return WitnessedStructureRelation(kind, first.ref, second.ref, settlement,
        first_grounding, second_grounding, located_span('first'), located_span('second'),
        located_span('option'), located_span('outcome') if match['outcome'] is not None else None)


def structure_relation_review(prepared, parent, nodes, retained_axes, shown_axes):
    """Review only finally accepted axes, in their corrected public index order."""
    if len(shown_axes) < 2 or json.loads(prepared.map_correction_sources_json or '[]'):
        return None
    material = json.loads(parent.material_json)
    fields = {entry['field']: entry for entry in material['fields']}
    original_fields = {number: (ref, base) for number, _, ref, base in parent.fields}

    def original_span(root):
        number, quote = root['field'], root['quote']
        entry = fields[number]
        if entry['source_role'] != 'ORIGINAL_INPUT' or entry['field_path'] not in ('memo', 'memo_action'):
            return None
        source = entry['text']
        start = source.find(quote)
        if start >= 0 and source.find(quote, start + 1) < 0:
            return OriginalSpan(number, start, start + len(quote), quote)
        return None

    origins = {f"{node['node_id']}.u{i}.e{j}": original_span(root)
               for node in nodes if node['perspective'] == 'SELF'
               for i, unit in enumerate(node['units'], 1) if unit['source_mode'] in ('RECORDED', 'PERSON_JUDGMENT')
               for j, root in enumerate(unit['evidence'], 1)}
    structures = [AdmittedStructure(shown_axes.index(visible), raw['decision_factor'],
                       tuple(origins[a] for a in raw['anchors']))
                  for visible, raw in retained_axes
                  if visible in shown_axes and all(origins.get(a) is not None for a in raw['anchors'])]
    if len(structures) < 2:
        return None

    def private_span(span):
        if span is None:
            return None
        record_ref, base = original_fields[span.field_number]
        return dict(field=base.field_path, record_ref=record_ref, source_envelope_id=base.source_envelope_id,
                    start=base.scalar_start + span.start, end=base.scalar_start + span.end, quote=span.quote)

    complete_actions = {entry['field'] for entry in json.loads(prepared.material_json)['fields']
                        if entry['source_role'] == 'ORIGINAL_INPUT' and entry['field_path'] == 'memo_action'
                        and entry.get('fragment_is_complete_field', True)}
    candidates = set(span for span in origins.values() if span and span.field_number in complete_actions)
    pairs = tuple(combinations(structures, 2))
    views, witnesses = [], []
    for settlement in sorted(candidates, key=lambda span: (span.field_number, span.start), reverse=True):
        for first, second in pairs:
            proof = admit_witnessed_structure_relation(fields, first, second, settlement)
            if proof is None:
                continue
            view = dict(kind=proof.kind, first_index=proof.first_ref, second_index=proof.second_ref,
                        description=proof.settlement.quote)
            if view in views:
                continue
            views.append(view)
            witnesses.append(dict(settlement=private_span(proof.settlement),
                first_grounding=private_span(proof.first_grounding), second_grounding=private_span(proof.second_grounding),
                first_factor=private_span(proof.first_factor), second_factor=private_span(proof.second_factor),
                selected_option=private_span(proof.selected_option), confirmed_outcome=private_span(proof.confirmed_outcome)))
            if len(views) == MAX_RELATIONS:
                break
        if len(views) == MAX_RELATIONS:
            break
    return dict(views=views, witnesses=witnesses) if views else None


def safe_structure_relations(value, axis_count):
    """Accept only the finite public fields, even when the value comes from storage."""
    if type(value) is not list or not 0 < len(value) <= MAX_RELATIONS:
        return []
    for relation in value:
        if (type(relation) is not dict or set(relation) != {'kind', 'first_index', 'second_index', 'description'}
                or relation['kind'] not in ('COEXISTENCE', 'PRIORITY')
                or relation['first_index'] == relation['second_index']
                or not all(type(relation[k]) is int and 0 <= relation[k] < axis_count
                           for k in ('first_index', 'second_index'))
                or type(relation['description']) is not str or not 1 <= len(relation['description']) <= 240
                or not re.fullmatch(r'私は、[\w・ 、。]+。', relation['description'])):
            return []
    return value
