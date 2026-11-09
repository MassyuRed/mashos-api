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


def piece_model_material(source, *, expected_owner_id: str, tier: str = 'free') -> dict:
    """Source-only material for one explicitly selected Piece model attempt.

    Keep legacy piece_material bytes/IDs unchanged. This projection does not
    admit the candidate's meaning, call a parser/author, or authenticate a
    fabricated private snapshot. The saved-source adapter owns eligibility.
    """
    from piece_v2_contract import canonical_json_bytes
    from piece_v2_generation import PieceSourceSnapshot
    from .piece_refined import PieceRefinedSourceSnapshot, refined_source_ref
    from .emlis_thread_source import freeze_supplemental_answer

    refined = type(source) is PieceRefinedSourceSnapshot
    original = source.original if refined else source
    material = piece_material(original, expected_owner_id=expected_owner_id, tier=tier)
    sources = material['sources']
    if refined:
        frozen = freeze_supplemental_answer(source.supplemental)
        if (source.opted_in is not True or source.supplemental_update_operation != 'ADD'
                or source.supplemental_owner_id != expected_owner_id
                or source.original_commitment != sources[0]['source_commitment']
                or source.supplemental_commitment != 'sha256:' + frozen.envelope.raw_sha256
                or source.supplemental.round_index != 1
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
        source_ref = refined_source_ref(source)
    else:
        if type(source) is not PieceSourceSnapshot:
            raise ValueError('piece_model_source_type')
        source_ref = 'piece-model-source:' + hashlib.sha256(canonical_json_bytes({
            'owner': expected_owner_id, 'source_stage': source.source_stage,
            'source': sources[0]})).hexdigest()
    partition = []
    for item in sources:
        for field, text in item['text_fields'].items():
            if not isinstance(text, str):
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
                or [s['role'] for s in sources] not in (
                    ['ORIGINAL_INPUT'], ['ORIGINAL_INPUT', 'SUPPLEMENTAL_ANSWER'])
                or type(partition) is not list or not 1 <= len(partition) <= 3):
            raise ValueError
        by_id = {s['source_id']: s for s in sources}
        if len(by_id) != len(sources):
            raise ValueError
        slots = {}
        for index, item in enumerate(partition):
            if type(item) is not dict or set(item) != {
                    'source_id', 'field_path', 'scalar_start', 'scalar_end'}:
                raise ValueError
            source = by_id[item['source_id']]
            field = item['field_path']
            allowed = ('memo', 'memo_action') if source['role'] == 'ORIGINAL_INPUT' else ('answer_text_private',)
            text = source['text_fields'][field]
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
