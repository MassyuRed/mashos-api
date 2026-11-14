"""A person's correction of a saved map, separate from the map's AI text.

No Emotion or Emlis thread is manufactured. The qualified source is exactly
the person's explanation. The saved interpretation is immutable context for
that source, and cohort references identify the inputs it can concern.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import re
from uuid import UUID

from ...contracts import SourceEnvelope, EvidenceRef

SCHEMA = 'cocolon.analysis.map_correction.v1'
SOURCE_ROLE = 'USER_ANALYSIS_MAP_CORRECTION'


def _require(condition):
    if not condition:
        raise ValueError('analysis_map_correction_invalid')


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def _digest(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def _uuid(value):
    _require(type(value) is str)
    try:
        _require(str(UUID(value)) == value)
    except (ValueError, AttributeError):
        raise ValueError('analysis_map_correction_invalid') from None
    return value


def checked_target_selector(kind, reference, field):
    _require(type(kind) is str and type(reference) is str and type(field) is str)
    if kind == 'overview':
        _require(reference == 'overview' and field in {'title', 'summary'})
    elif kind == 'node':
        _require(bool(re.fullmatch(r'n[1-9][0-9]*', reference)))
        _require(field in {'title', 'summary', 'explanation'} or
            bool(re.fullmatch(r'(context|unknowns)\.(0|[1-9][0-9]{0,3})', field)))
    elif kind == 'edge':
        _require(bool(re.fullmatch(r'e[1-9][0-9]*', reference))
                 and field in {'label', 'explanation'})
    else:
        _require(False)


def checked_target(kind, reference, field, field_text, target_text):
    checked_target_selector(kind, reference, field)
    _require(type(field_text) is str and bool(field_text.strip()))
    _require(type(target_text) is str and bool(target_text.strip()) and len(target_text) <= 2000)
    first = field_text.find(target_text)
    _require(first >= 0 and field_text.find(target_text, first + 1) < 0)
    return field_text


def map_correction_target_field(projection, *, artifact_ref, kind, reference, field, target_text):
    """Bind the actual displayed field, including array items, without I/O."""
    _require(type(projection) is dict and projection.get('wire_kind') == 'watashi.map.v3'
             and projection.get('projection_of') == artifact_ref)
    if kind == 'overview':
        target = projection.get('overview')
    else:
        family, key = ('nodes', 'node_ref') if kind == 'node' else ('edges', 'edge_ref')
        found = [item for item in projection.get(family, []) if item.get(key) == reference]
        _require(len(found) == 1)
        target = found[0]
    _require(type(target) is dict)
    if '.' in field:
        name, index = field.split('.', 1)
        _require(index.isdigit() and type(target.get(name)) is list and int(index) < len(target[name]))
        text = target[name][int(index)]
    else:
        text = target.get(field)
    return checked_target(kind, reference, field, text, target_text)


def checked_map_correction(owner_scope, row):
    """Check an owner's immutable row; ACTIVE/STALE is a derived read state."""
    _uuid(owner_scope)
    _require(type(row) is dict and set(row) == {'schema_version', 'correction_id', 'owner_scope',
        'recorded_at', 'target_context', 'explanation', 'source_state'})
    _require(row['schema_version'] == SCHEMA and row['owner_scope'] == owner_scope
             and row['source_state'] in {'ACTIVE', 'STALE'})
    _uuid(row['correction_id'])
    try:
        _require(type(row['recorded_at']) is str and
            datetime.fromisoformat(row['recorded_at'].replace('Z', '+00:00')).tzinfo is not None)
    except (ValueError, TypeError, AttributeError):
        raise ValueError('analysis_map_correction_invalid') from None
    target, explanation = row['target_context'], row['explanation']
    _require(type(target) is dict and set(target) == {'artifact_ref', 'kind', 'ref', 'field',
        'target_text', 'field_text', 'source_guard', 'cohort'})
    _require(type(target['artifact_ref']) is str and
        bool(re.fullmatch(r'artifact:[0-9a-f]{32}@[1-9][0-9]*', target['artifact_ref'])))
    _require(type(target['source_guard']) is str and bool(re.fullmatch(
        r'analysis-db-cumulative-v1:[0-9a-f]{64}', target['source_guard'])))
    checked_target(target['kind'], target['ref'], target['field'], target['field_text'], target['target_text'])
    cohort = target['cohort']
    _require(type(cohort) is list and bool(cohort))
    refs = []
    for member in cohort:
        _require(type(member) is dict and set(member) == {'record_ref', 'source_guard'})
        refs.append(_uuid(member['record_ref']))
        _require(type(member['source_guard']) is str and bool(re.fullmatch(
            r'analysis-map-member-v1:[0-9a-f]{64}', member['source_guard'])))
    _require(len(set(refs)) == len(refs))
    _require(type(explanation) is dict and set(explanation) == {'source_role', 'text'}
        and explanation['source_role'] == SOURCE_ROLE and type(explanation['text']) is str
        and bool(explanation['text'].strip()) and len(explanation['text']) <= 2000)
    return json.loads(_json(row))


@dataclass(frozen=True, slots=True, repr=False)
class AnalysisMapCorrectionSource:
    correction_id: str
    owner_scope: str
    recorded_at: str
    cohort_refs: tuple[str, ...]
    explanation: str
    target_context_json: str
    envelope: SourceEnvelope
    evidence: EvidenceRef

    @property
    def target_context(self):
        return json.loads(self.target_context_json)


def qualify_map_correction(owner_scope, row, *, allow_stale=False):
    row = checked_map_correction(owner_scope, row)
    _require(type(allow_stale) is bool and (row['source_state'] == 'ACTIVE' or allow_stale))
    # The read-state is not a new source version. A stale row cannot qualify,
    # while its immutable explanation/control history keeps the same identity.
    identity = _json({key: value for key, value in row.items() if key != 'source_state'})
    eid = 'analysis-map-correction-source:' + _digest(identity)
    text = row['explanation']['text']
    raw = text.encode('utf-8')
    literal = hashlib.sha256(raw).hexdigest()
    envelope = SourceEnvelope(eid, row['correction_id'], SOURCE_ROLE, SCHEMA, SCHEMA,
        'utf-8', SCHEMA, _digest(SCHEMA), raw, literal)
    evidence = EvidenceRef('analysis-map-correction-evidence:' + _digest(identity), 'explanation', eid,
        'explanation', 0, 0, len(raw), 0, len(text), 0, len(raw), literal, literal)
    return AnalysisMapCorrectionSource(row['correction_id'], owner_scope, row['recorded_at'],
        tuple(member['record_ref'] for member in row['target_context']['cohort']), text,
        _json(row['target_context']), envelope, evidence)
