"""Server-only IF/Saved RPC adapter; authenticated owner is never body input."""
from __future__ import annotations

import re
from uuid import UUID
from fastapi import HTTPException
from analysis_observed_service import _rpc


def owner_id(value):
    try:
        return str(UUID(value))
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(404, 'analysis_if_unavailable') from None


def artifact_id(value):
    return owner_id(value)


async def base_context(owner, base_ref):
    if type(base_ref) is not str or re.fullmatch(r'artifact:[0-9a-f]{32}@1', base_ref) is None:
        raise HTTPException(400, 'analysis_if_base_invalid')
    return await _rpc('analysis_if_base_context', dict(p_user_id=owner_id(owner), p_base_ref=base_ref))


async def read(owner, kind, *, identity=None, limit=60, offset=0, key_hash=None, request_hash=None, scenario_set_ref=None):
    if kind not in {'scenario_set', 'saved_intent'}:
        raise HTTPException(400, 'analysis_if_kind_invalid')
    return await _rpc('analysis_if_artifacts_read', dict(p_user_id=owner_id(owner),p_kind=kind,
        p_id=artifact_id(identity) if identity is not None else None,p_limit=limit,p_offset=offset,
        p_key_hash=key_hash,p_request_hash=request_hash,p_set_ref=scenario_set_ref))


async def commit_set(owner, base_ref, guard, key_hash, request_hash, storage):
    return await _rpc('analysis_if_set_commit', dict(p_user_id=owner_id(owner),p_base_ref=base_ref,
        p_guard=guard,p_key_hash=key_hash,p_request_hash=request_hash,p_storage=storage))


async def reserve(owner,key_hash,request_hash,*,base_ref=None,guard=None,material=None):
    result = await _rpc('analysis_if_operation_reserve',dict(p_user_id=owner_id(owner),p_key_hash=key_hash,
        p_request_hash=request_hash,p_base_ref=base_ref,p_guard=guard,p_material=material))
    if result is None:
        return None
    try:
        if type(result) is not dict or set(result) != {'state','operation_id','call_token','material','receipt','artifact_id'}:
            raise ValueError
        state=result['state']
        if state not in {'RESERVED','CALL_STARTED','RECEIVED','COMPLETED','FAILED'}:
            raise ValueError
        UUID(result['operation_id'])
        if result['call_token'] is not None:
            UUID(result['call_token'])
            if state != 'RESERVED':
                raise ValueError
        if state=='RECEIVED':
            if type(result['material']) is not dict or type(result['receipt']) is not dict:
                raise ValueError
        elif result['material'] is not None or result['receipt'] is not None:
            raise ValueError
        if state=='COMPLETED':
            UUID(result['artifact_id'])
        elif result['artifact_id'] is not None:
            raise ValueError
    except (ValueError,KeyError,TypeError,AttributeError):
        raise HTTPException(503,'analysis_if_operation_unavailable') from None
    return result


async def start(owner,key_hash,token):
    return await _rpc('analysis_if_operation_start',dict(p_user_id=owner_id(owner),p_key_hash=key_hash,p_token=token))


async def receive(owner,key_hash,token,receipt):
    return await _rpc('analysis_if_operation_receive',dict(p_user_id=owner_id(owner),p_key_hash=key_hash,p_token=token,p_receipt=receipt))


async def fail(owner,key_hash,token):
    return await _rpc('analysis_if_operation_fail',dict(p_user_id=owner_id(owner),p_key_hash=key_hash,p_token=token))


async def commit_intent(owner, set_ref, key_hash, request_hash, storage):
    return await _rpc('analysis_if_intent_commit', dict(p_user_id=owner_id(owner),p_set_ref=set_ref,
        p_key_hash=key_hash,p_request_hash=request_hash,p_storage=storage))


async def delete(owner, kind, identity):
    if kind not in {'scenario_set', 'saved_intent'}:
        raise HTTPException(400, 'analysis_if_kind_invalid')
    return await _rpc('analysis_if_artifact_delete',dict(p_user_id=owner_id(owner),p_kind=kind,p_id=artifact_id(identity)))
