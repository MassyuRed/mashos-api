"""Owner-bound saved-map corrections and the existing background refresh.

The atomic SQL owner binds a displayed artifact and its current source cohort.
Reads never generate or enqueue work. A confirmed save schedules the existing
map queue; a lost write ACK is resolved once by key, without repeating a write.
"""
from __future__ import annotations

import re
from uuid import UUID

from fastapi import HTTPException

import analysis_observed_service as observed
from cocolon_meaning_experience_engine.cores.analysis.map_interpretation_correction import (
    checked_map_correction, checked_target_selector,
)

RESPONSE_SCHEMA = 'cocolon.analysis.map_correction.response.v1'


def _owner(value):
    try:
        return str(UUID(value))
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(404, 'analysis_report_unavailable') from None


def _key(value):
    if type(value) is not str or not value.strip() or len(value) > 128:
        raise HTTPException(422, 'analysis_map_correction_key_invalid')
    return value


def _command(value):
    if type(value) is not dict or set(value) != {'artifact_ref', 'kind', 'ref', 'field',
            'target_text', 'explanation', 'idempotency_key'}:
        raise HTTPException(422, 'analysis_map_correction_invalid')
    try:
        if (type(value['artifact_ref']) is not str or not re.fullmatch(
                r'artifact:[0-9a-f]{32}@[1-9][0-9]*', value['artifact_ref'])
                or any(type(value[key]) is not str or not value[key].strip()
                    or len(value[key]) > 2000 for key in ('target_text', 'explanation'))):
            raise ValueError
        checked_target_selector(value['kind'], value['ref'], value['field'])
        _key(value['idempotency_key'])
    except ValueError:
        raise HTTPException(422, 'analysis_map_correction_invalid') from None
    from emlis_thread_service import _needs_correction_detail
    if _needs_correction_detail(value['explanation']):
        # Reuse the existing two-input detail boundary before any admission
        # write, so a person can add detail to the same displayed target.
        raise HTTPException(422, 'analysis_map_correction_explanation_required')
    return value


def _row(owner, value):
    try:
        return checked_map_correction(owner, value)
    except (ValueError, TypeError, KeyError, AttributeError):
        raise HTTPException(503, 'analysis_map_correction_saved_source_invalid') from None


def _matches(row, command):
    target = row['target_context']
    return (all(target[key] == command[key] for key in (
        'artifact_ref', 'kind', 'ref', 'field', 'target_text'))
        and row['explanation']['text'] == command['explanation'])


def _response(row, refresh_status=None):
    target = row['target_context']
    return dict(schema_version=RESPONSE_SCHEMA, correction_id=row['correction_id'],
        **{key: target[key] for key in ('artifact_ref', 'kind', 'ref', 'field', 'target_text')},
        explanation=row['explanation']['text'], recorded_at=row['recorded_at'],
        source_state=row['source_state'], refresh_status=refresh_status)


async def read_map_correction(user_id, *, idempotency_key):
    owner, key = _owner(user_id), _key(idempotency_key)
    row = _row(owner, await observed._rpc('analysis_map_correction_read',
        dict(p_user_id=owner, p_key=key)))
    from analysis_cumulative_service import map_refresh_status
    try:
        status = await map_refresh_status(owner)
    except Exception:
        status = 'failed'
    return _response(row, status)


async def submit_map_correction(user_id, command):
    if observed.observed_mode() != 'development':
        raise HTTPException(503, 'analysis_map_correction_read_only')
    owner, command = _owner(user_id), _command(command)
    payload = dict(p_user_id=owner,
        **{'p_' + key: value for key, value in command.items()})
    try:
        row = _row(owner, await observed._rpc('analysis_map_correction_submit', payload))
    except HTTPException as failure:
        if failure.status_code != 503:
            raise
        # Do not resend an uncertain command. A matching saved row confirms
        # admission; a missing/unreadable row leaves the original result unknown.
        try:
            row = _row(owner, await observed._rpc('analysis_map_correction_read',
                dict(p_user_id=owner, p_key=command['idempotency_key'])))
        except HTTPException:
            raise failure
    if not _matches(row, command):
        raise HTTPException(409, 'analysis_map_correction_idempotency_conflict')
    status = None
    if row['source_state'] == 'ACTIVE':
        from analysis_cumulative_service import read_maps, map_refresh_status, request_map_refresh
        try:
            if (await read_maps(owner, limit=1, metadata_only=True))['items']:
                status = await map_refresh_status(owner)
            else:
                status = await request_map_refresh(owner, force=True, trigger='manual',
                    requested_at=row['recorded_at'], debounce_seconds=0)
        except Exception:
            # Source save is confirmed independently of queue availability.
            # A later normal background ensure may resume the same source.
            status = 'failed'
    return _response(row, status)
