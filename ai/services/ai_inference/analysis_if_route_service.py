"""Analysis-owned IF generation and explicit Saved-intent lifecycle.

Only generation calls the configured model. Every subsequent read reauthorizes
the pinned source cohort and returns the same immutable stored text/graph.
"""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from uuid import UUID

from fastapi import HTTPException
import analysis_if_route_store as store
from analysis_observed_service import observed_mode

_locks = {}


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def _digest(value):
    return hashlib.sha256(_json(value).encode('utf-8')).hexdigest()


def _require_write():
    if observed_mode() != 'development' or asyncio.current_task().cancelling():
        raise HTTPException(503, 'analysis_if_generation_unavailable')


def _identity(owner, request):
    key = request.get('idempotency_key')
    if type(key) is not str or not key.strip() or len(key) > 128:
        raise HTTPException(400, 'analysis_if_request_invalid')
    return _digest(key), _digest({k: v for k, v in request.items() if k != 'idempotency_key'})


@asynccontextmanager
async def _operation(owner, kind, key_hash):
    # Identical overlapping HTTP requests share one model/write operation. The
    # durable RPC key handles retries and another process, with no auto retry.
    key = (asyncio.get_running_loop(), owner, kind, key_hash)
    entry = _locks.setdefault(key, [asyncio.Lock(), 0])
    entry[1] += 1
    try:
        async with entry[0]:
            yield
    finally:
        entry[1] -= 1
        if entry[1] == 0:
            _locks.pop(key, None)


def _pure():
    from cocolon_meaning_experience_engine.cores.analysis import if_route_realizer
    return if_route_realizer


def _engine():
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    return MeaningExperienceEngine()


def _safe_row(owner, row, kind, *, replay=False):
    try:
        artifact = _pure().from_storage(row['storage'], authenticated_owner_scope=owner)
        projection = artifact.safe_projection(authenticated_owner_scope=owner)
        identity = str(UUID(row['id']))
        if artifact.reference != 'artifact:' + identity.replace('-', '') + '@1':
            raise ValueError
        expected = {'scenario_set': 'watashi.if-route-set.v1', 'saved_intent': 'watashi.saved-route-intent.v1'}[kind]
        if projection['wire_kind'] != expected:
            raise ValueError
        result = dict(status='GENERATED', id=identity, artifact_ref=artifact.reference, kind=kind,
            content_text=row['storage']['content_text'], projection=projection, idempotency_replayed=replay)
        if kind == 'scenario_set':
            result['scenario_set_ref'] = artifact.scenario_set_reference
        else:
            labels = [item['scenario_display_label'] for item in row['storage']['parent_scenario_set']['primary_artifact']['scenarios']
                if item['scenario_artifact_ref'] == projection['selected_scenario_ref']]
            if len(labels) != 1:
                raise ValueError
            result['selected_scenario_label'] = labels[0]
        return result
    except (ValueError, KeyError, TypeError, AttributeError):
        raise HTTPException(503, 'analysis_if_saved_artifact_invalid') from None


def _items(result):
    if type(result) is not dict or set(result) != {'items', 'subscription_tier'} or result['subscription_tier'] != 'premium' or type(result['items']) is not list:
        raise HTTPException(503, 'analysis_if_storage_unavailable')
    return result['items']


async def _replay(owner, kind, key_hash, request_hash):
    rows = _items(await store.read(owner, kind, key_hash=key_hash, request_hash=request_hash, limit=1))
    return _safe_row(owner, rows[0], kind, replay=True) if rows else None


def _session_source(owner, request_id, role, text):
    from cocolon_meaning_experience_engine.cores.analysis.if_route_contracts import AnalysisSimulationSource
    return AnalysisSimulationSource('if-session:' + _digest([owner, request_id, role]), owner, text)


def _request(owner, request, base, key_hash):
    from cocolon_meaning_experience_engine.cores.analysis.if_route_contracts import AnalysisIfRouteRequest
    request_id = 'analysis-if-request:' + _digest([owner, key_hash])
    intent = request.get('branch_intent_text')
    return AnalysisIfRouteRequest(request_id=request_id, authenticated_owner_scope=owner,
        base_observed_map_ref=request['base_observed_map_ref'],
        base_route_ref=_pure().observed_route_reference(request['base_observed_map_ref'], request['branch_point_id']),
        branch_point_id=request['branch_point_id'],
        base_projection_json=_json(base['base_projection']),
        base_private_evidence_json=_json(base['base_private_evidence']),
        base_source_guard=base['base_source_guard'],
        branch_intent=_session_source(owner, request_id, 'intent', intent) if intent is not None else None,
        constraints=tuple(_session_source(owner, request_id, 'constraint:' + str(i), text)
            for i, text in enumerate(request.get('constraint_texts', []))),
        requested_candidate_count=request.get('requested_candidate_count', 1),
        constraints_confirmed=request.get('constraints_confirmed', False),
        scenario_choices=tuple(_session_source(owner, request_id, 'choice:' + str(i), text)
            for i, text in enumerate(request.get('scenario_choice_texts', []))))


def _outcome(outcome):
    status = getattr(outcome.status, 'value', outcome.status)
    if status == 'GENERATED' and outcome.artifact is not None:
        return None
    if status == 'QUESTION_PENDING':
        return dict(status=status, reason_codes=list(outcome.reason_codes),
            clarification_request=outcome.clarification_request, artifact=None)
    if status == 'SEPARATE_SAFETY':
        return dict(status=status, reason_codes=list(outcome.reason_codes), clarification_request=None, artifact=None)
    raise HTTPException(422 if status == 'REJECTED' else 503, 'analysis_if_generation_unavailable')


def _freeze_prepared(prepared):
    return dict(request=asdict(prepared.request),request_ref=prepared.request_ref,
        messages_json=prepared.messages_json,base_seed_json=prepared.base_seed_json)


def _restore_prepared(material):
    from cocolon_meaning_experience_engine.cores.analysis.if_route_contracts import (
        AnalysisIfRouteRequest, AnalysisSimulationSource, AnalysisIfModelPrepared)
    if type(material) is not dict or set(material) != {'request','request_ref','messages_json','base_seed_json'}:
        raise ValueError('analysis_if_operation_invalid')
    request = dict(material['request'])
    request['branch_intent'] = AnalysisSimulationSource(**request['branch_intent']) if request['branch_intent'] is not None else None
    for field in ('constraints','scenario_choices'):
        request[field] = tuple(AnalysisSimulationSource(**source) for source in request[field])
    return AnalysisIfModelPrepared(AnalysisIfRouteRequest(**request),material['request_ref'],
        material['messages_json'],material['base_seed_json'])


def _restore_receipt(receipt):
    from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import AnalysisModelQuotedParentUnitsResponse
    if type(receipt) is not dict or set(receipt) != {'request_ref','messages_sha256','raw_sha256','finish_reason','raw'}:
        raise ValueError('analysis_if_operation_invalid')
    return AnalysisModelQuotedParentUnitsResponse(**receipt)


def _pending_operation(operation):
    return dict(status='PENDING',operation_id=operation['operation_id'],state=operation['state'],
        reason_codes=['analysis_if_result_pending'],artifact=None)


async def create_scenario_set(owner, request, *, model_source=None):
    owner = store.owner_id(owner)
    key_hash, request_hash = _identity(owner, request)
    async with _operation(owner, 'scenario_set', key_hash):
        operation = await store.reserve(owner,key_hash,request_hash)
        prepared = None
        if operation is None:
            _require_write()
            base = await store.base_context(owner, request['base_observed_map_ref'])
            prepared = _pure().prepare_if_model_request(_request(owner, request, base, key_hash))
            from cocolon_meaning_experience_engine.cores.analysis.if_route_contracts import AnalysisIfRouteOutcome
            if isinstance(prepared, AnalysisIfRouteOutcome):
                return _outcome(prepared)
            operation = await store.reserve(owner,key_hash,request_hash,
                base_ref=request['base_observed_map_ref'],guard=base['base_source_guard'],material=_freeze_prepared(prepared))
        if operation['state']=='RESERVED' and operation['call_token'] is None:
            if observed_mode()!='development':
                return _pending_operation(operation)
            _require_write()
            operation=await store.reserve(owner,key_hash,request_hash,reclaim=True)
            # The frozen original request belongs to the reservation. Do not
            # recompute it from a newer map or the retrying process's context.
            prepared=None
        if operation['state'] == 'COMPLETED':
            result = await get_artifact(owner,'scenario_set',operation['artifact_id'])
            result['idempotency_replayed'] = True
            return result
        if operation['state'] == 'FAILED':
            raise HTTPException(409,'analysis_if_operation_failed')
        token = operation['call_token']
        if operation['state'] in {'RESERVED','CALL_STARTED'} and token is None:
            return _pending_operation(operation)
        try:
            if operation['state'] == 'RECEIVED':
                prepared = _restore_prepared(operation['material'])
                response = _restore_receipt(operation['receipt'])
            else:
                _require_write()
                if prepared is None:
                    prepared=_restore_prepared(operation['material'])
                if model_source is None:
                    from analysis_if_model_source import application_analysis_if_model_source
                    model_source = application_analysis_if_model_source()
                if model_source is None:
                    raise HTTPException(503, 'analysis_if_model_source_unavailable')
                started = await store.start(owner,key_hash,token)
                if started != {'started':True}:
                    return _pending_operation(operation)
                _require_write()
                async with asyncio.timeout(215.0) as deadline:
                    response = await model_source(prepared)
                if deadline.expired() or asyncio.current_task().cancelling():
                    raise TimeoutError
                received = await store.receive(owner,key_hash,token,asdict(response))
                if received != {'received':True}:
                    raise HTTPException(503,'analysis_if_receipt_unconfirmed')
            _require_write()
            if _pure().prepare_if_model_request(prepared.request, response=response) != prepared:
                raise ValueError('analysis_if_operation_invalid')
            outcome = _engine().generate(prepared.request,semantic_input=response)
            pending = _outcome(outcome)
            if pending is not None:
                return pending
            storage = outcome.artifact.to_storage()
        except HTTPException:
            if operation['state'] != 'RECEIVED' and token is not None:
                # A failed result never authorizes another provider call for
                # this operation, even if the failure update loses its ACK.
                try:
                    await store.fail(owner,key_hash,token)
                except HTTPException:
                    pass
            raise
        except TimeoutError:
            if token is not None:
                try:
                    await store.fail(owner,key_hash,token)
                except HTTPException:
                    pass
            raise HTTPException(504, 'analysis_if_model_source_timeout') from None
        except asyncio.CancelledError:
            if token is not None:
                try:
                    await store.fail(owner,key_hash,token)
                except (HTTPException,asyncio.CancelledError):
                    pass
            raise
        except (ValueError, TypeError, KeyError, RuntimeError, OSError):
            if token is not None:
                try:
                    await store.fail(owner,key_hash,token)
                except HTTPException:
                    pass
            raise HTTPException(503, 'analysis_if_model_source_unavailable') from None
        identity = await store.commit_set(owner, prepared.request.base_observed_map_ref, prepared.request.base_source_guard,
            key_hash, request_hash, storage)
        return await get_artifact(owner, 'scenario_set', identity)


async def save_intent(owner, request):
    owner = store.owner_id(owner)
    key_hash, request_hash = _identity(owner, request)
    async with _operation(owner, 'saved_intent', key_hash):
        previous = await _replay(owner, 'saved_intent', key_hash, request_hash)
        if previous is not None:
            return previous
        _require_write()
        # Resolve a versioned scenario-set reference, never a body artifact.
        rows = _items(await store.read(owner, 'scenario_set', scenario_set_ref=request['source_scenario_set_ref'], limit=1))
        parent = None
        for row in rows:
            try:
                artifact = _pure().from_storage(row['storage'], authenticated_owner_scope=owner)
            except (ValueError,KeyError,TypeError,AttributeError):
                raise HTTPException(503,'analysis_if_saved_artifact_invalid') from None
            if artifact.scenario_set_reference == request['source_scenario_set_ref']:
                parent = artifact
                break
        if parent is None:
            raise HTTPException(404, 'analysis_if_scenario_set_unavailable')
        operation_id = 'analysis-if-save:' + _digest([owner, key_hash])
        selection = _session_source(owner, operation_id, 'selection', request['selected_scenario_ref'])
        note = request.get('user_note')
        note_source = _session_source(owner, operation_id, 'note', note) if note is not None else None
        try:
            saved = _engine().save_analysis_route_intent(parent, authenticated_owner_scope=owner,
                selected_scenario_ref=request['selected_scenario_ref'], selection_source=selection,
                note_source=note_source, saved_at=datetime.now(timezone.utc).isoformat())
        except ValueError:
            raise HTTPException(422, 'analysis_if_selection_invalid') from None
        identity = await store.commit_intent(owner, request['source_scenario_set_ref'], key_hash, request_hash, saved.to_storage())
        return await get_artifact(owner, 'saved_intent', identity)


async def list_artifacts(owner, kind, *, limit=60, offset=0):
    owner = store.owner_id(owner)
    rows = _items(await store.read(owner, kind, limit=limit, offset=offset))
    return dict(status='ok', items=[_safe_row(owner, row, kind) for row in rows], limit=limit, offset=offset)


async def get_artifact(owner, kind, artifact_id):
    owner = store.owner_id(owner)
    rows = _items(await store.read(owner, kind, identity=artifact_id, limit=1))
    if not rows:
        raise HTTPException(404, 'analysis_if_unavailable')
    return _safe_row(owner, rows[0], kind)


async def delete_artifact(owner, kind, artifact_id):
    owner = store.owner_id(owner)
    result = await store.delete(owner, kind, artifact_id)
    if type(result) is not dict or set(result) != {'deleted', 'id'} or result['deleted'] is not True or result['id'] != str(UUID(artifact_id)):
        raise HTTPException(503, 'analysis_if_delete_unavailable')
    return result
