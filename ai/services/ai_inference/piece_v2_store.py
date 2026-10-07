"""Disabled Piece v2 terminal RPC adapter; no credential or network at import.

The caller must pass identity from server authentication, never a body user_id.
B5/B6 own persisted-preview admission, current source/format/visual checks and
HTTP authentication. An injected service-only RPC transport executes exactly
one SQL function. This adapter does not implement authentication or a DB client,
pre-consume quota, log bodies, retry automatically, or register production routes.
"""
from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from datetime import datetime
import hashlib
import re
from typing import Any
from uuid import UUID

from piece_v2_contract import PieceContractError, normalize_visibility_scope

RpcCall = Callable[[str, Mapping[str, Any]], Awaitable[Mapping[str, Any]]]
_ERRORS = frozenset({
    'PIECE_REQUEST_INVALID', 'PIECE_AUTH_REQUIRED', 'PIECE_NOT_FOUND',
    'PIECE_PREVIEW_STALE', 'PIECE_PREVIEW_EXPIRED', 'PIECE_HASH_MISMATCH',
    'PIECE_QUOTA_EXHAUSTED', 'PIECE_CONFLICT', 'PIECE_TEMPORARILY_UNAVAILABLE',
})


def _uuid(value: Any, *, owner: bool = False) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PieceContractError('PIECE_AUTH_REQUIRED' if owner else 'PIECE_REQUEST_INVALID')
    try:
        return str(UUID(value))
    except (ValueError, AttributeError):
        raise PieceContractError('PIECE_AUTH_REQUIRED' if owner else 'PIECE_REQUEST_INVALID') from None


def _positive(value: Any) -> int:
    if type(value) is not int or not 0 < value <= 9223372036854775807:
        raise PieceContractError('PIECE_REQUEST_INVALID')
    return value


def _hash(value: Any) -> str:
    if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value):
        raise PieceContractError('PIECE_REQUEST_INVALID')
    return value


def _key_hash(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PieceContractError('PIECE_REQUEST_INVALID')
    try:
        return hashlib.sha256(value.encode('utf-8')).hexdigest()
    except UnicodeError:
        raise PieceContractError('PIECE_REQUEST_INVALID') from None


def _request(value: Any, required: set[str], optional: set[str] | None = None) -> dict:
    if not isinstance(value, Mapping):
        raise PieceContractError('PIECE_REQUEST_INVALID')
    keys = set(value)
    if not required <= keys or keys - required - (optional or set()):
        raise PieceContractError('PIECE_REQUEST_INVALID')
    return dict(value)


async def _execute(rpc: RpcCall, name: str, args: dict, fields: set[str]) -> dict:
    try:
        response = await rpc(name, args)
    except Exception as exc:
        # Only exact known machine codes may escape. Never stringify transport
        # exceptions, SQL diagnostics, request bodies or provider response text.
        code = getattr(exc, 'code', None)
        raise PieceContractError(code if isinstance(code, str) and code in _ERRORS
                                 else 'PIECE_TEMPORARILY_UNAVAILABLE') from None
    if not isinstance(response, Mapping) or set(response) != fields:
        raise PieceContractError('PIECE_TEMPORARILY_UNAVAILABLE')
    result = dict(response)
    try:
        if _uuid(result['piece_id']) != args.get('p_piece_id', args.get('p_preview_id')):
            raise ValueError
        for field in ('consumption_id', 'receipt_id'):
            if field in result:
                _uuid(result[field])
        if 'row_version' in result:
            _positive(result['row_version'])
        if 'visibility_scope' in result and result['visibility_scope'] not in ('private', 'public'):
            raise ValueError
        if 'lifecycle_status' in result and result['lifecycle_status'] != 'saved':
            raise ValueError
        if 'outcome' in result and result['outcome'] != 'succeeded':
            raise ValueError
        if 'idempotency_replayed' in result and type(result['idempotency_replayed']) is not bool:
            raise ValueError
        if 'saved_at' in result:
            if not isinstance(result['saved_at'], str) or datetime.fromisoformat(result['saved_at']).utcoffset() is None:
                raise ValueError
    except (PieceContractError, ValueError, TypeError, OverflowError):
        raise PieceContractError('PIECE_TEMPORARILY_UNAVAILABLE') from None
    return result


def save_request_arguments(authenticated_user_id: str, request: Mapping[str, Any],
                           idempotency_key: str) -> dict:
    """Validate the closed save request before any server read can yield."""
    owner = _uuid(authenticated_user_id, owner=True)
    if UUID(owner).int == 0:
        raise PieceContractError('PIECE_AUTH_REQUIRED')
    r = _request(request, {'preview_id', 'expected_preview_revision', 'piece_text_hash',
                          'content_payload_hash', 'visual_recipe_hash'}, {'visibility_scope'})
    return {
        'p_owner_user_id': owner,
        'p_preview_id': _uuid(r['preview_id']),
        'p_expected_preview_revision': _positive(r['expected_preview_revision']),
        'p_piece_text_hash': _hash(r['piece_text_hash']),
        'p_content_payload_hash': _hash(r['content_payload_hash']),
        'p_visual_recipe_hash': _hash(r['visual_recipe_hash']),
        'p_idempotency_key_hash': _key_hash(idempotency_key),
        'p_visibility_scope': normalize_visibility_scope(r.get('visibility_scope')),
    }


async def save_piece(*, authenticated_user_id: str, request: Mapping[str, Any],
                     idempotency_key: str, rpc: RpcCall,
                     expected_subscription_tier: str | None = None,
                     expected_source_state: Mapping[str, Any] | None = None,
                     replay_only: bool = False) -> dict:
    """Save through B4, optionally binding a server-side B5/B6 tier check.

    The expectation is a separate internal argument, never accepted in request.
    It grants no plan and does not replace source/format/visual/safety admission.
    SQL compares it with the locked current profile before first save/quota.
    Saved replay remains the same record/consumption after a plan change.
    B6 supplies the server-only original/thread expectation as well. SQL locks
    those current owners through commit; no source body is added to the public
    request or response. replay_only may never enter the first-save branch.
    Unfenced low-level B4 callers remain supported, not HTTP admission.
    """
    args = save_request_arguments(authenticated_user_id, request, idempotency_key)
    if expected_subscription_tier is not None:
        if type(expected_subscription_tier) is not str or expected_subscription_tier not in ('free', 'plus', 'premium'):
            raise PieceContractError('PIECE_REQUEST_INVALID')
        args['p_expected_subscription_tier'] = expected_subscription_tier
    if type(replay_only) is not bool:
        raise PieceContractError('PIECE_REQUEST_INVALID')
    if replay_only:
        args['p_replay_only'] = True
    if expected_source_state is not None:
        import json
        from piece_v2_contract import canonical_json_bytes
        try:
            value = json.loads(canonical_json_bytes(_request(expected_source_state,
                {'original', 'thread_id', 'thread_revision', 'lineage'})))
            value['thread_id'] = _uuid(value['thread_id'])
            _positive(value['thread_revision'])
            if (expected_subscription_tier is None or type(value['original']) is not dict
                    or type(value['lineage']) is not dict
                    or value['lineage']['source_input']['source_owner_user_id'] != args['p_owner_user_id']
                    or value['original']['id'] != value['lineage']['source_input']['source_input_id']):
                raise ValueError
        except (PieceContractError, KeyError, ValueError, TypeError, UnicodeError, RecursionError):
            raise PieceContractError('PIECE_REQUEST_INVALID') from None
        args['p_expected_source_state'] = value
    return await _execute(rpc, 'piece_save_v2', args, {
        'piece_id', 'consumption_id', 'lifecycle_status', 'visibility_scope',
        'row_version', 'saved_at', 'idempotency_replayed',
    })


async def set_piece_visibility(*, authenticated_user_id: str, piece_id: str,
                               request: Mapping[str, Any], rpc: RpcCall) -> dict:
    owner = _uuid(authenticated_user_id, owner=True)
    r = _request(request, {'expected_row_version', 'visibility_scope'})
    if r['visibility_scope'] is None:
        raise PieceContractError('PIECE_REQUEST_INVALID')
    args = {'p_owner_user_id': owner, 'p_piece_id': _uuid(piece_id),
            'p_expected_row_version': _positive(r['expected_row_version']),
            'p_visibility_scope': normalize_visibility_scope(r['visibility_scope'])}
    return await _execute(rpc, 'piece_set_visibility_v2', args,
                          {'piece_id', 'visibility_scope', 'row_version'})


async def delete_piece(*, authenticated_user_id: str, piece_id: str,
                       request: Mapping[str, Any], idempotency_key: str, rpc: RpcCall) -> dict:
    owner = _uuid(authenticated_user_id, owner=True)
    r = _request(request, {'expected_row_version'})
    args = {'p_owner_user_id': owner, 'p_piece_id': _uuid(piece_id),
            'p_expected_row_version': _positive(r['expected_row_version']),
            'p_idempotency_key_hash': _key_hash(idempotency_key)}
    return await _execute(rpc, 'piece_delete_v2', args,
                          {'piece_id', 'receipt_id', 'outcome', 'idempotency_replayed'})


_PREVIEW_CONTENT_FIELDS = {
    'format_type', 'eligible_formats', 'content_payload', 'content_payload_hash',
    'piece_text', 'piece_text_hash', 'safety_state', 'visual_recipe',
    'visual_recipe_hash', 'renderer_version',
}
_PREVIEW_RESPONSE_FIELDS = _PREVIEW_CONTENT_FIELDS | {
    'preview_id', 'preview_revision', 'row_version', 'expires_at',
    'visibility_scope', 'idempotency_replayed',
}


def _preview_content(value: Mapping[str, Any]) -> None:
    # This verifies representation, NOT source ownership, semantic eligibility,
    # native rendering or public-safety acceptance. Their current owners must
    # supply the admitted candidate; in particular safety_state has no default.
    from piece_v2_contract import canonical_sha256_hex, validate_piece_text_binding
    from piece_v2_visual import validate_visual_recipe
    formats = value['eligible_formats']
    if (type(formats) is not list or not 1 <= len(formats) <= 3
            or any(type(f) is not str or f not in ('short_essay', 'quote', 'declaration') for f in formats)
            or len(set(formats)) != len(formats) or value['format_type'] not in formats
            or value['safety_state'] not in ('ready', 'adjusted')
            or type(value['renderer_version']) is not str
            or not re.fullmatch(r'[A-Za-z0-9_.:\-]{1,128}', value['renderer_version'])):
        raise PieceContractError('PIECE_REQUEST_INVALID')
    payload = value['content_payload']
    validate_piece_text_binding(payload, value['piece_text'], _hash(value['piece_text_hash']))
    if (payload['format_type'] != value['format_type']
            or canonical_sha256_hex(payload) != _hash(value['content_payload_hash'])):
        raise PieceContractError('PIECE_HASH_MISMATCH')
    validate_visual_recipe(value['visual_recipe'], format_type=value['format_type'],
                           language=payload['language'], expected_hash=_hash(value['visual_recipe_hash']))


async def issue_piece_preview(*, authenticated_user_id: str, record: Mapping[str, Any],
                              request_fingerprint: str, idempotency_key: str,
                              ttl_seconds: int, rpc: RpcCall,
                              expected_subscription_tier: str | None = None,
                              expected_source_state: Mapping[str, Any] | None = None) -> dict:
    """Persist an already-admitted server candidate, without consuming quota.

    INTERNAL STORE ENTRY, NOT an HTTP request parser or a safety approval.
    B5 must authenticate, resolve/revalidate the current source and entitlement,
    admit safety, and construct this record. A PreparedPiecePreview alone does
    not grant those approvals. TTL has no shipped default: the server supplies
    its separately chosen lifetime. Never pass client replacement text here.
    The fingerprint binds the original canonical request; retry returns the
    persisted candidate, not a newly generated candidate or extended lifetime.

    B5 passes BOTH server-only expectations to the fenced SQL overload. It
    holds the original/profile/thread and consumed Q3 context through issuance
    and replay. Neither expectation is a safety decision or a client field.
    Omitting both preserves the existing low-level five-argument primitive,
    not public admission; an incomplete pair never falls back to that path.
    """
    import json
    from piece_v2_contract import canonical_json_bytes
    owner = _uuid(authenticated_user_id, owner=True)
    if UUID(owner).int == 0:
        raise PieceContractError('PIECE_AUTH_REQUIRED')
    key, fingerprint = _key_hash(idempotency_key), _hash(request_fingerprint)
    if type(ttl_seconds) is not int or not 0 < ttl_seconds <= 2147483647:
        raise PieceContractError('PIECE_REQUEST_INVALID')
    try:
        value = json.loads(canonical_json_bytes(_request(record, _PREVIEW_CONTENT_FIELDS | {'source_lineage'})))
        _preview_content(value)
        if value['source_lineage']['source_input']['source_owner_user_id'] != owner:
            raise PieceContractError('PIECE_REQUEST_INVALID')
    except (PieceContractError, KeyError, TypeError, ValueError, OverflowError, RecursionError):
        raise PieceContractError('PIECE_REQUEST_INVALID') from None
    args = {
        'p_owner_user_id': owner, 'p_idempotency_key_hash': key,
        'p_request_hash': fingerprint, 'p_record': value, 'p_ttl_seconds': ttl_seconds,
    }
    if expected_subscription_tier is not None or expected_source_state is not None:
        try:
            if (type(expected_subscription_tier) is not str
                    or expected_subscription_tier not in ('free', 'plus', 'premium')):
                raise ValueError
            expected = json.loads(canonical_json_bytes(_request(expected_source_state,
                {'original', 'thread_id', 'thread_revision', 'lineage'})))
            expected['thread_id'] = _uuid(expected['thread_id'])
            _positive(expected['thread_revision'])
            if (type(expected['original']) is not dict or type(expected['lineage']) is not dict
                    or expected['lineage']['source_input']['source_owner_user_id'] != owner
                    or expected['original']['id'] != expected['lineage']['source_input']['source_input_id']
                    or canonical_json_bytes(expected['lineage']) != canonical_json_bytes(value['source_lineage'])):
                raise ValueError
        except (PieceContractError, KeyError, TypeError, ValueError, OverflowError, RecursionError):
            raise PieceContractError('PIECE_REQUEST_INVALID') from None
        args.update(p_expected_subscription_tier=expected_subscription_tier,
                    p_expected_source_state=expected)
    expected_id = str(UUID(hashlib.sha256(f'piece.preview.v2:{owner}:{key}'.encode()).hexdigest()[:32]))
    try:
        response = await rpc('piece_issue_preview_v2', args)
    except Exception as exc:
        code = getattr(exc, 'code', None)
        raise PieceContractError(code if isinstance(code, str) and code in _ERRORS
                                 else 'PIECE_TEMPORARILY_UNAVAILABLE') from None
    try:
        result = json.loads(canonical_json_bytes(_request(response, _PREVIEW_RESPONSE_FIELDS)))
        _preview_content(result)
        if (_uuid(result['preview_id']) != expected_id or result['visibility_scope'] != 'private'
                or type(result['idempotency_replayed']) is not bool
                or type(result['expires_at']) is not str
                or datetime.fromisoformat(result['expires_at']).utcoffset() is None):
            raise ValueError
        _positive(result['preview_revision']); _positive(result['row_version'])
        # For a new insertion, even an internally inconsistent transport result
        # must not replace the candidate. Replay is deliberately the stored one.
        if not result['idempotency_replayed'] and any(result[k] != value[k] for k in _PREVIEW_CONTENT_FIELDS):
            raise ValueError
    except (PieceContractError, KeyError, ValueError, TypeError, OverflowError, RecursionError):
        raise PieceContractError('PIECE_TEMPORARILY_UNAVAILABLE') from None
    return result


async def cancel_piece_preview(*, authenticated_user_id: str, preview_id: str,
                               expected_preview_revision: int, rpc: RpcCall) -> dict:
    """Owner-only, revision-bound cancellation; repeated cancellation is a no-op."""
    args = {'p_owner_user_id': _uuid(authenticated_user_id, owner=True),
            'p_preview_id': _uuid(preview_id),
            'p_expected_preview_revision': _positive(expected_preview_revision)}
    try:
        response = await rpc('piece_cancel_preview_v2', args)
    except Exception as exc:
        code = getattr(exc, 'code', None)
        raise PieceContractError(code if isinstance(code, str) and code in _ERRORS
                                 else 'PIECE_TEMPORARILY_UNAVAILABLE') from None
    try:
        result = _request(response, {'preview_id', 'preview_revision', 'row_version',
                                     'lifecycle_status', 'idempotency_replayed'})
        if (_uuid(result['preview_id']) != args['p_preview_id']
                or _positive(result['preview_revision']) != args['p_expected_preview_revision']
                or result['lifecycle_status'] != 'cancelled'
                or type(result['idempotency_replayed']) is not bool):
            raise ValueError
        _positive(result['row_version'])
    except (PieceContractError, KeyError, TypeError, ValueError, OverflowError):
        raise PieceContractError('PIECE_TEMPORARILY_UNAVAILABLE') from None
    return result
