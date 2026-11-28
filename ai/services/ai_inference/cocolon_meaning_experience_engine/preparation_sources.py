"""Source-only Piece/Analysis projections for CMEE's offline preparation.

These internal materials are not admitted meanings or public DTOs. Callers
must obtain native snapshots from the existing owner/auth/retention boundary;
owner equality below is a binding check, not authentication. No generation,
model, storage or lifecycle owner is called here.
"""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import json


def _tier(tier: str) -> str:
    if tier not in ('free', 'plus', 'premium'):
        raise ValueError('preparation_tier_invalid')
    return tier


def _field_evidence(source_id: str, commitment: str, field: str, text: str) -> dict:
    """A complete-field locator, not a native semantic EvidenceRef."""
    digest = hashlib.sha256((commitment + ':' + field).encode('utf-8')).hexdigest()
    return {
        'evidence_id': 'preparation-field:' + digest,
        'source_id': source_id,
        'field_path': field,
        'coordinate_space': 'FIELD',
        'scalar_start': 0,
        'scalar_end': len(text),
        'utf8_start': 0,
        'utf8_end': len(text.encode('utf-8')),
        'literal': text,
    }


def piece_material(source, *, expected_owner_id: str, tier: str = 'free') -> dict:
    """Keep the immutable seven fields before Piece's finite meaning grammar.

    `_saved_field_projection` also calls `_sentences`, so it cannot serve as
    this source-only boundary. Its canonical JSON/identity/view checks are
    retained here, without its complete-sentence or selected-feeling grammar.
    The existing Piece production admission remains unchanged.
    """
    from piece_v2_contract import canonical_json_bytes
    from piece_v2_generation import PieceSourceSnapshot

    _tier(tier)
    if type(source) is not PieceSourceSnapshot:
        raise ValueError('preparation_piece_source_type')
    if (any(type(value) is not str or not value.strip() for value in (
            expected_owner_id, source.owner_id, source.saved_input_id,
            source.source_version, source.original_text)) or
            source.owner_id != expected_owner_id):
        raise ValueError('preparation_piece_owner_or_identity_invalid')
    if source.source_role != 'original' or source.source_stage not in (
            'normal_observation', 'pre_question_observation'):
        raise ValueError('source_role_or_stage_not_yet_supported')
    try:
        if type(source.saved_original_json) is not bytes:
            raise ValueError
        original = json.loads(source.saved_original_json)
        if (type(original) is not dict or
                set(original) != {'id', 'created_at', 'memo', 'memo_action',
                                  'category', 'emotions', 'emotion_details'} or
                canonical_json_bytes(original) != source.saved_original_json or
                original['id'] != source.saved_input_id or
                source.source_version != 'emlis.current_input_bundle.v1' or
                type(original['created_at']) is not str or not original['created_at'] or
                any(original[key] is not None and type(original[key]) is not str
                    for key in ('memo', 'memo_action')) or
                any(original[key] is not None and type(original[key]) is not list
                    for key in ('category', 'emotions', 'emotion_details')) or
                any(type(value) is not str for key in ('category', 'emotions')
                    for value in (original[key] or []))):
            raise ValueError
    except (ValueError, TypeError, UnicodeError):
        raise ValueError('saved_original_projection_invalid') from None
    view = '\n\n'.join(original[key] for key in ('memo', 'memo_action')
                       if original[key] is not None and original[key].strip())
    if not view or view != source.original_text:
        raise ValueError('saved_original_projection_mismatch')
    record_commitment = 'sha256:' + hashlib.sha256(source.saved_original_json).hexdigest()
    fields = {key: original[key] for key in ('memo', 'memo_action')}
    evidence = [_field_evidence(source.saved_input_id, record_commitment, key, text)
                for key, text in fields.items() if isinstance(text, str) and text]
    return {
        'core': 'piece', 'task': 'PIECE_ORIGINAL_MATERIAL', 'tier': tier,
        'sources': [{
            'source_id': source.saved_input_id,
            'source_version': source.source_version,
            'source_commitment': record_commitment,
            'role': 'ORIGINAL_INPUT', 'original': original,
            'text_fields': fields, 'envelope_id': None,
            'recorded_at': original['created_at'],
            'parent_record_id': None, 'evidence': evidence,
        }],
        'period': None,
        'control': {'source_stage': source.source_stage,
                    'source_role': source.source_role,
                    'original_text_view': view,
                    'projection_only': True},
    }


def _corrected_piece_model_material(source, *, expected_owner_id, tier):
    from dataclasses import asdict
    from .piece_refined import _validate_corrected_source, refined_source_ref, corrected_history_ranges, corrected_answer_ranges
    from .cores.analysis.source_adapter import commitment
    frozen = _validate_corrected_source(source)
    material = piece_material(source.original, expected_owner_id=expected_owner_id, tier=tier)
    original = material['sources'][0]
    _, rows = corrected_history_ranges(source.original, source.correction, as_of=source.as_of,
        prior_corrections=source.prior_corrections,answer_sources=source.answer_sources,
        circumstance_control=source.circumstance_control,
        direct_feeling_correction_ids=source.direct_feeling_correction_ids)
    selected_ranges = {}
    from .emlis_thread_source import freeze_supplemental_answer
    for answer,operation,active_range,_,_ in corrected_answer_ranges(source):
        frozen_answer = freeze_supplemental_answer(answer)
        selected = operation == 'REVISE' or answer.answer_id == source.selected_answer_id
        ranges = (() if operation == 'WITHDRAW' or not selected else
            (('answer_text_private',*(active_range if active_range is not None else (0,len(answer.answer_text_private)))),))
        material['sources'].append(dict(source_id=answer.answer_id,source_version=answer.source_version,
            source_commitment='sha256:'+frozen_answer.envelope.raw_sha256,role='SUPPLEMENTAL_ANSWER',original=None,
            text_fields={'answer_text_private':answer.answer_text_private},envelope_id=frozen_answer.envelope.envelope_id,
            recorded_at=answer.recorded_at,parent_record_id=source.original.saved_input_id,
            evidence=[dict(asdict(ref),literal=frozen_answer.envelope.raw_utf8[ref.utf8_start:ref.utf8_end].decode('utf-8'),
                coordinate_space='SOURCE_ENVELOPE') for ref in frozen_answer.evidence_refs]))
        selected_ranges[answer.answer_id] = ranges
    for correction, _, active_range, commitment_value, frozen in rows:
        material['sources'].append(dict(source_id=correction.correction_id,
            source_version=commitment(asdict(correction)), source_commitment=commitment_value,
            role='USER_INTERPRETATION_CORRECTION', original=None,
            text_fields={'memo': correction.explanation}, envelope_id=frozen.envelope.envelope_id,
            recorded_at=correction.recorded_at, parent_record_id=source.original.saved_input_id,
            evidence=[dict(asdict(ref), literal=frozen.envelope.raw_utf8[ref.utf8_start:ref.utf8_end].decode('utf-8'),
                coordinate_space='SOURCE_ENVELOPE') for ref in frozen.evidence]))
        selected_ranges[correction.correction_id] = (() if active_range is None else (('memo', *active_range),))
    partition = []
    for item in material['sources']:
        selected = source.original_active_ranges if item is original else selected_ranges[item['source_id']]
        for field in item['text_fields']:
            groups = []
            text = item['text_fields'][field]
            for name, start, end in selected:
                if name != field:
                    continue
                if not groups or any(c in text[groups[-1][-1][1]:start] for c in '\r\n'):
                    groups.append([])
                groups[-1].append([start, end])
            partition.extend(dict(source_id=item['source_id'], field_path=field, scalar_ranges=group)
                for group in groups)
    if not partition or len(partition) > 3:
        raise ValueError('piece_model_block_partition')
    material.update(task='PIECE_MODEL_BODY', control=dict(source_stage='corrected_observation',
        source_ref=refined_source_ref(source), block_partition=partition, format_type='short_essay',
        language='ja', model_body_only=True, authorship='USER_OWNED_COCOLON_SHAPED',
        source_selections_are_not_written_propositions=True,
        interpretation_correction=True, active_source_update=source.correction_update_operation,
        correction_control=asdict(source.correction)))
    if source.prior_corrections:
        material['control']['prior_correction_controls'] = [asdict(c) for c in source.prior_corrections]
    return material


def piece_model_material(source, *, expected_owner_id: str, tier: str = 'free',
                         original_memo_only: bool = False) -> dict:
    """Source-only material for one explicitly selected Piece model attempt.

    Keep legacy piece_material bytes/IDs unchanged. This projection does not
    admit the candidate's meaning, call a parser/author, or authenticate a
    fabricated private snapshot. The saved-source adapter owns eligibility.
    """
    from piece_v2_contract import canonical_json_bytes
    from piece_v2_generation import PieceSourceSnapshot
    from .piece_refined import PieceRefinedSourceSnapshot, PieceCorrectedSourceSnapshot, refined_source_ref
    from .emlis_thread_source import freeze_supplemental_answer

    if type(source) is PieceCorrectedSourceSnapshot:
        return _corrected_piece_model_material(source, expected_owner_id=expected_owner_id, tier=tier)
    refined = type(source) is PieceRefinedSourceSnapshot
    original = source.original if refined else source
    material = piece_material(original, expected_owner_id=expected_owner_id, tier=tier)
    sources = material['sources']
    if refined:
        frozen = freeze_supplemental_answer(source.supplemental)
        operation = source.supplemental_update_operation
        if (source.opted_in is not True or operation not in {'ADD', 'REVISE', 'WITHDRAW'}
                or source.supplemental_owner_id != expected_owner_id
                or source.original_commitment != sources[0]['source_commitment']
                or source.supplemental_commitment != 'sha256:' + frozen.envelope.raw_sha256
                or type(source.supplemental.round_index) is not int
                or not 1 <= source.supplemental.round_index <= 3
                or source.supplemental.answer_id == original.saved_input_id
                or any(type(v) is not str or not v.strip() for v in (
                    source.question_need_decision_identity, source.refined_result_identity))):
            raise ValueError('piece_model_refined_binding')
        sources.append({
            'source_id': source.supplemental.answer_id,
            'source_version': source.supplemental.source_version,
            'source_commitment': source.supplemental_commitment,
            'role': 'SUPPLEMENTAL_ANSWER', 'original': None,
            'text_fields': {'answer_text_private': source.supplemental.answer_text_private},
            'envelope_id': frozen.envelope.envelope_id,
            'recorded_at': source.supplemental.recorded_at,
            'parent_record_id': original.saved_input_id,
            'evidence': [dict(asdict(ref), literal=frozen.envelope.raw_utf8[
                ref.utf8_start:ref.utf8_end].decode('utf-8'), coordinate_space='SOURCE_ENVELOPE')
                for ref in frozen.evidence_refs],
        })
        if source.effective_round_sources:
            # Retain each prior replacement's own answer envelope. It is not
            # appended to the latest answer or disguised as original input.
            latest = sources.pop()
            seen_rounds = []
            for answer, active_range in source.prior_revisions:
                previous = freeze_supplemental_answer(answer)
                if (answer.thread_id != source.supplemental.thread_id
                        or answer.original_source_ref != source.supplemental.original_source_ref
                        or not 0 < answer.round_index < source.supplemental.round_index):
                    raise ValueError('piece_model_refined_binding')
                seen_rounds.append(answer.round_index)
                sources.append(dict(source_id=answer.answer_id, source_version=answer.source_version,
                    source_commitment='sha256:' + previous.envelope.raw_sha256,
                    role='SUPPLEMENTAL_ANSWER', original=None,
                    text_fields={'answer_text_private': answer.answer_text_private},
                    envelope_id=previous.envelope.envelope_id, recorded_at=answer.recorded_at,
                    parent_record_id=original.saved_input_id,
                    evidence=[dict(asdict(ref), literal=previous.envelope.raw_utf8[
                        ref.utf8_start:ref.utf8_end].decode('utf-8'), coordinate_space='SOURCE_ENVELOPE')
                        for ref in previous.evidence_refs]))
            if seen_rounds != sorted(set(seen_rounds)):
                raise ValueError('piece_model_refined_binding')
            sources.append(latest)
        source_ref = refined_source_ref(source)
    else:
        if type(source) is not PieceSourceSnapshot:
            raise ValueError('piece_model_source_type')
        source_ref = 'piece-model-source:' + hashlib.sha256(canonical_json_bytes({
            'owner': expected_owner_id, 'source_stage': source.source_stage,
            'source': sources[0]})).hexdigest()
    partition = []
    active_update = refined and (source.supplemental_update_operation in {'REVISE', 'WITHDRAW'}
                                 or source.effective_round_sources)
    if active_update:
        ranges = source.original_active_ranges
        answer_range = source.supplemental_active_range
        if (type(ranges) is not tuple or not ranges
                or any(type(row) is not tuple or len(row) != 3 for row in ranges)
                or (source.supplemental_update_operation == 'REVISE') != (answer_range is not None)):
            raise ValueError('piece_model_refined_binding')
        for item in sources:
            by_field = {}
            if item['role'] == 'ORIGINAL_INPUT':
                selected = ranges
            elif item['source_id'] == source.supplemental.answer_id:
                if source.effective_round_sources and source.supplemental_update_operation == 'ADD':
                    selected = (('answer_text_private', 0, len(source.supplemental.answer_text_private)),)
                else:
                    selected = (() if answer_range is None else (('answer_text_private', *answer_range),))
            else:
                matches = [r for answer, r in source.prior_revisions if answer.answer_id == item['source_id']]
                if len(matches) != 1:
                    raise ValueError('piece_model_refined_binding')
                selected = (('answer_text_private', *matches[0]),)
            for field, start, end in selected:
                text = item['text_fields'].get(field)
                allowed = ('memo', 'memo_action') if item['role'] == 'ORIGINAL_INPUT' else ('answer_text_private',)
                if (field not in allowed or type(text) is not str
                        or type(start) is not int or type(end) is not int
                        or not 0 <= start < end <= len(text) or not text[start:end].strip()
                        or '\n' in text[start:end] or '\r' in text[start:end]):
                    raise ValueError('piece_model_refined_binding')
                previous = by_field.setdefault(field, [])
                if previous and previous[-1][1] > start:
                    raise ValueError('piece_model_refined_binding')
                previous.append([start, end])
            for field in item['text_fields']:
                if field in by_field:
                    groups = []
                    text = item['text_fields'][field]
                    for start, end in by_field[field]:
                        if (not groups or '\n' in text[groups[-1][-1][1]:start]
                                or '\r' in text[groups[-1][-1][1]:start]):
                            groups.append([])
                        groups[-1].append([start, end])
                    partition.extend(dict(source_id=item['source_id'], field_path=field,
                                          scalar_ranges=group) for group in groups)
    for item in (() if active_update else sources):
        for field, text in item['text_fields'].items():
            if not isinstance(text, str) or (original_memo_only and field == 'memo_action'):
                continue
            offset = 0
            for line in text.splitlines(keepends=True):
                body = line.rstrip('\r\n')
                if body.strip():
                    partition.append(dict(source_id=item['source_id'], field_path=field,
                                          scalar_start=offset, scalar_end=offset + len(body)))
                offset += len(line)
    if not partition or len(partition) > 3:
        raise ValueError('piece_model_block_partition')
    material.update(task='PIECE_MODEL_BODY', control={
        'source_stage': 'refined_observation' if refined else original.source_stage,
        'source_ref': source_ref, 'block_partition': partition,
        'format_type': 'short_essay', 'language': 'ja', 'model_body_only': True,
        'authorship': 'USER_OWNED_COCOLON_SHAPED',
        'source_selections_are_not_written_propositions': True,
    })
    if original_memo_only:
        material['control']['original_memo_only'] = True
    if refined and source.feeling_circumstance is not None:
        from .piece_refined import _validate_feeling_circumstance_source
        _validate_feeling_circumstance_source(source)
        material['control']['feeling_circumstance'] = {
            'feeling_source_id': original.saved_input_id,
            'feeling_range': list(source.feeling_circumstance.feeling_range),
            'circumstance_source_id': source.supplemental.answer_id,
            'circumstance_range': list(source.feeling_circumstance.circumstance_range),
        }
    if active_update:
        material['control']['active_source_update'] = source.supplemental_update_operation
    if refined and source.effective_round_sources:
        material['control']['effective_round_sources'] = True
    return material


def piece_model_field_slots(material):
    """Resolve the existing Piece partition; this is not source admission.

    Names/order are server-owned. Literal values stay exact Unicode scalar
    slices, not expected author text or model-provided source locators.
    """
    try:
        sources = material['sources']
        control = material['control']
        partition = control['block_partition']
        if (material['core'] != 'piece' or material['task'] != 'PIECE_MODEL_BODY'
                or control['model_body_only'] is not True or type(sources) is not list
                or ([s['role'] for s in sources] not in (
                    ['ORIGINAL_INPUT'], ['ORIGINAL_INPUT', 'SUPPLEMENTAL_ANSWER'])
                    and not (control.get('interpretation_correction') is True
                        and len(sources) >= 2 and sources[0]['role'] == 'ORIGINAL_INPUT'
                        and all(s['role'] in {'USER_INTERPRETATION_CORRECTION','SUPPLEMENTAL_ANSWER'} for s in sources[1:])
                        and any(s['role'] == 'USER_INTERPRETATION_CORRECTION' for s in sources[1:]))
                    and not (control.get('effective_round_sources') is True
                        and 2 <= len(sources) <= 4 and sources[0]['role'] == 'ORIGINAL_INPUT'
                        and all(s['role'] == 'SUPPLEMENTAL_ANSWER' for s in sources[1:])))
                or type(partition) is not list or not 1 <= len(partition) <= 3):
            raise ValueError
        by_id = {s['source_id']: s for s in sources}
        if len(by_id) != len(sources):
            raise ValueError
        slots = {}
        for index, item in enumerate(partition):
            active = (control.get('active_source_update') in {'REVISE', 'WITHDRAW'}
                      or control.get('effective_round_sources') is True)
            expected_keys = ({'source_id', 'field_path', 'scalar_ranges'} if active else
                             {'source_id', 'field_path', 'scalar_start', 'scalar_end'})
            if type(item) is not dict or set(item) != expected_keys:
                raise ValueError
            source = by_id[item['source_id']]
            field = item['field_path']
            allowed = (('memo', 'memo_action') if source['role'] == 'ORIGINAL_INPUT' else
                ('memo',) if source['role'] == 'USER_INTERPRETATION_CORRECTION' else ('answer_text_private',))
            text = source['text_fields'][field]
            if active:
                ranges = item['scalar_ranges']
                if type(ranges) is not list or not ranges:
                    raise ValueError
                literals = []
                for row in ranges:
                    if type(row) is not list or len(row) != 2:
                        raise ValueError
                    start, end = row
                    if (field not in allowed or type(text) is not str
                            or type(start) is not int or type(end) is not int
                            or not 0 <= start < end <= len(text) or not text[start:end].strip()
                            or (literals and literals[-1]['scalar_end'] > start)):
                        raise ValueError
                    literals.append(dict(scalar_start=start, scalar_end=end,
                        utf8_start=len(text[:start].encode('utf-8')),
                        utf8_end=len(text[:end].encode('utf-8')), literal=text[start:end]))
                slots[field + '_' + str(index)] = dict(item, source_role=source['role'],
                    scalar_start=literals[0]['scalar_start'], scalar_end=literals[-1]['scalar_end'],
                    field_sha256=hashlib.sha256(text.encode('utf-8')).hexdigest(), literal_ranges=literals)
                continue
            start, end = item['scalar_start'], item['scalar_end']
            if (field not in allowed or type(text) is not str
                    or type(start) is not int or type(end) is not int
                    or not 0 <= start < end <= len(text) or not text[start:end].strip()):
                raise ValueError
            slots[field + '_' + str(index)] = dict(item,
                source_role=source['role'], literal=text[start:end])
        return slots
    except (KeyError, TypeError, AttributeError, ValueError):
        raise ValueError('piece_model_field_slots_invalid') from None


def analysis_material(request, *, tier: str) -> dict:
    """Reuse Analysis's source freeze, including period and supplement checks."""
    from .cores.analysis.source_adapter import freeze_analysis_sources

    _tier(tier)
    if getattr(request, 'comparison_previous_request', None) is not None:
        raise ValueError('preparation_analysis_comparison_not_yet_supported')
    frozen = freeze_analysis_sources(request)
    members = {member.saved_record_ref: member for member in request.members}
    sources = []
    for source in frozen.sources:
        parent = members[source.record_ref]
        original = json.loads(parent.original_json)
        role = source.envelope.source_role
        if role == 'ORIGINAL_INPUT':
            fields = {key: original[key] for key in ('memo', 'memo_action')}
            version = parent.saved_record_version
            recorded_at = original['created_at']
        else:
            supplement = next(item for item in parent.supplements
                              if item.source_id == source.envelope.source_record_id)
            fields = {'answer_text_private': supplement.text}
            version = supplement.source_version
            recorded_at = None  # This native supplement has no timestamp field.
        evidence = []
        for ref in source.evidence:
            row = asdict(ref)
            row['literal'] = source.envelope.raw_utf8[ref.utf8_start:ref.utf8_end].decode('utf-8')
            row['coordinate_space'] = 'SOURCE_ENVELOPE'
            # Native Analysis stores a supplement in its memo field. Keep
            # that locator unchanged and state the projection's field name.
            row['material_field_path'] = (ref.field_path if role == 'ORIGINAL_INPUT'
                                          else 'answer_text_private')
            evidence.append(row)
        sources.append({
            'source_id': source.envelope.source_record_id,
            'source_version': version,
            'role': role,
            'original': original if role == 'ORIGINAL_INPUT' else None,
            'text_fields': fields,
            'envelope_id': source.envelope.envelope_id,
            'recorded_at': recorded_at,
            'parent_record_id': source.record_ref if role != 'ORIGINAL_INPUT' else None,
            'parent_record_version': source.record_version if role != 'ORIGINAL_INPUT' else None,
            'evidence': evidence,
        })
    return {
        'core': 'analysis', 'task': 'ANALYSIS_OBSERVED_PERIOD_MATERIAL',
        'tier': tier, 'sources': sources,
        'period': {'start': frozen.period[0], 'end_exclusive': frozen.period[1]},
        'control': {'source_set_ref': frozen.source_set_ref,
                    'members': [asdict(member) for member in frozen.members],
                    'operation': request.operation,
                    'projection_only': True},
    }
