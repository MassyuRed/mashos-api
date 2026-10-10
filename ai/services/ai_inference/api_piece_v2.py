"""Unregistered Piece v2 HTTP routes: cancellation, B6 save and B7 owner operations.

PCE-6 owns the wire shape; the existing B5 store/SQL owns cancellation and
revision locking. Mount this router only in a dedicated test application until
the separately approved B12-C clean cutover. Production app.py is unchanged.
No preview issuance, safety approval or source author is invented.
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from piece_v2_contract import PieceContractError, normalize_visibility_scope
from piece_v2_store import cancel_piece_preview
from piece_v2_runtime_control import require_piece_feature_enabled, validate_piece_preview_runtime

router = APIRouter(prefix='/emotion/piece')
_CANCEL_STATUS = {
    'PIECE_REQUEST_INVALID': 400,
    'PIECE_AUTH_REQUIRED': 401,
    'PIECE_NOT_FOUND': 404,
    'PIECE_PREVIEW_STALE': 409,
    'PIECE_PREVIEW_EXPIRED': 409,
    'PIECE_CONFLICT': 409,
    'PIECE_TEMPORARILY_UNAVAILABLE': 503,
}


async def _verify_bearer(authorization: str) -> str:
    # Reuse the established verifier; never decode a caller's UUID/JWT claim
    # here or accept a service-role claim as the Piece's owner.
    from api_account_visibility import _require_user_id
    return await _require_user_id(authorization)


async def _authenticated_owner(request: Request) -> str:
    headers = request.headers.getlist('authorization')
    if len(headers) != 1:
        raise PieceContractError('PIECE_AUTH_REQUIRED')
    parts = headers[0].split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        raise PieceContractError('PIECE_AUTH_REQUIRED')
    try:
        verified = await _verify_bearer(headers[0])
        if type(verified) is not str:
            raise PieceContractError('PIECE_AUTH_REQUIRED')
        owner = UUID(verified)
        if owner.int == 0:
            raise PieceContractError('PIECE_AUTH_REQUIRED')
        return str(owner)
    except HTTPException as exc:
        raise PieceContractError('PIECE_AUTH_REQUIRED' if exc.status_code in (401, 403)
                                 else 'PIECE_TEMPORARILY_UNAVAILABLE') from None
    except (ValueError, AttributeError):
        raise PieceContractError('PIECE_AUTH_REQUIRED') from None
    except PieceContractError:
        raise
    except Exception:
        raise PieceContractError('PIECE_TEMPORARILY_UNAVAILABLE') from None


async def _cancel_rpc(name: str, args: dict) -> dict:
    """Use the existing service-only HTTP client once; do not retry a POST.

    PostgREST puts our SQL RAISE code in message and SQLSTATE in code. Accept
    only the exact P0001 + known-message pair, never details, hints, substrings
    or infrastructure 404/401 as an application's not-found/auth result.
    The store validates the successful response's closed field set and IDs.
    """
    if name != 'piece_cancel_preview_v2':
        raise PieceContractError('PIECE_TEMPORARILY_UNAVAILABLE')
    try:
        from supabase_client import sb_post_rpc
        response = await sb_post_rpc(name, args, timeout=8.0)
        value = response.json()
        if response.status_code == 200 and type(value) is dict:
            return value
        code = 'PIECE_TEMPORARILY_UNAVAILABLE'
        if (response.status_code == 400 and type(value) is dict
                and value.get('code') == 'P0001'
                and type(value.get('message')) is str
                and value['message'] in _CANCEL_STATUS):
            code = value['message']
        raise PieceContractError(code)
    except PieceContractError:
        raise
    except Exception:
        # Timeout/invalid ACK may follow a committed cancellation. Keep the
        # outcome unknown; a caller can repeat the SAME ID/revision explicitly.
        raise PieceContractError('PIECE_TEMPORARILY_UNAVAILABLE') from None


def _response(value: dict, status: int = 200) -> JSONResponse:
    headers = {'Cache-Control': 'no-store'}
    if status == 401:
        headers['WWW-Authenticate'] = 'Bearer'
    return JSONResponse(value, status_code=status, headers=headers)


class _OperationFeatures:
    """Request-local stop latch over the existing authoritative resolver.

    IO wrappers recheck before dispatch and after completion, including errors.
    A dispatched write may already have committed; no retry/undo is attempted.
    Task cancellation still propagates unchanged.
    """
    def __init__(self, request: Request, feature: str):
        self.app, self.names, self.disabled = request.app, [feature], False

    def require(self, *additional: str) -> None:
        self.names.extend(name for name in additional if name not in self.names)
        if self.disabled:
            raise PieceContractError('PIECE_FEATURE_DISABLED')
        try:
            for name in self.names:
                require_piece_feature_enabled(self.app, name)
        except PieceContractError:
            self.disabled = True
            raise

    def wrap(self, operation):
        async def guarded(*args, **kwargs):
            self.require()
            try:
                result = await operation(*args, **kwargs)
            except Exception:
                self.require()
                raise
            self.require()
            return result
        return guarded

    def failure(self, exc: Exception, statuses: dict) -> JSONResponse:
        if self.disabled:
            return _response({'code': 'PIECE_FEATURE_DISABLED'}, 503)
        code = exc.code if isinstance(exc, PieceContractError) else None
        code = code if code in statuses else 'PIECE_TEMPORARILY_UNAVAILABLE'
        return _response({'code': code}, statuses[code])


@router.delete('/preview/{preview_id}')
async def cancel_preview(preview_id: str, request: Request) -> JSONResponse:
    """Cancel only the authenticated owner's current preview revision.

    Parse the closed JSON request inside the route, so framework validation
    errors cannot echo a submitted token, source text or replacement payload.
    Every repeat is authenticated again; SQL decides its idempotent outcome.
    """
    try:
        owner = await _authenticated_owner(request)
        try:
            value = await request.json()
        except (ValueError, UnicodeError):
            raise PieceContractError('PIECE_REQUEST_INVALID') from None
        if (type(value) is not dict or set(value) != {'expected_preview_revision'}
                or request.query_params):
            raise PieceContractError('PIECE_REQUEST_INVALID')
        result = await cancel_piece_preview(
            authenticated_user_id=owner, preview_id=preview_id,
            expected_preview_revision=value['expected_preview_revision'], rpc=_cancel_rpc)
        return _response(result)
    except PieceContractError as exc:
        code = exc.code if exc.code in _CANCEL_STATUS else 'PIECE_TEMPORARILY_UNAVAILABLE'
        return _response({'code': code}, _CANCEL_STATUS[code])
    except Exception:
        # Do not catch BaseException: task cancellation still propagates.
        return _response({'code': 'PIECE_TEMPORARILY_UNAVAILABLE'}, 503)


@router.post('/save')
async def save_preview(request: Request) -> JSONResponse:
    """Save only a persisted admitted preview; never accept replacement text."""
    from piece_v2_save_service import PieceSaveService, SAVE_STATUS, load_owned_preview, save_rpc
    from piece_v2_store import save_request_arguments
    features = _OperationFeatures(request, 'piece_v2_save_enabled')
    try:
        owner = await _authenticated_owner(request)
        features.require()
        keys = request.headers.getlist('idempotency-key')
        if len(keys) != 1 or not keys[0].strip() or request.query_params:
            raise PieceContractError('PIECE_REQUEST_INVALID')
        try:
            value = await request.json()
        except (ValueError, UnicodeError):
            raise PieceContractError('PIECE_REQUEST_INVALID') from None
        args = save_request_arguments(owner, value, keys[0])
        if args['p_visibility_scope'] == 'public':
            features.require('piece_v2_public_write_enabled')
        features.require()
        result = await PieceSaveService(load_record=features.wrap(load_owned_preview),
            rpc=features.wrap(save_rpc)).save(request.headers['authorization'],
            authenticated_user_id=owner, request=value, idempotency_key=keys[0])
        features.require()
        return _response(result)
    except Exception as exc:
        return features.failure(exc, SAVE_STATUS)


# Static owner paths must precede /{piece_id}; production remains unregistered.
@router.get('/quota')
async def read_quota(request: Request) -> JSONResponse:
    """B5 preview quota display; can_save is quota-only, not save authority."""
    from piece_v2_quota import read_piece_quota
    from supabase_client import sb_post_rpc
    # PCE-8 assigns quota to B5's preview surface. Saving can be stopped while
    # its read-only preview quota remains visible; no new flag is invented.
    features = _OperationFeatures(request, 'piece_v2_preview_enabled')
    try:
        owner = await _authenticated_owner(request)
        features.require()
        if request.query_params or await request.body():
            raise PieceContractError('PIECE_REQUEST_INVALID')
        result = await read_piece_quota(authenticated_user_id=owner,
            post_rpc=features.wrap(sb_post_rpc))
        features.require()
        return _response(result)
    except Exception as exc:
        return features.failure(exc, _CANCEL_STATUS)


@router.get('/history')
async def owner_history(request: Request) -> JSONResponse:
    """Read only the authenticated owner's saved private/public artifacts."""
    from piece_v2_owner_service import PieceOwnerService, OWNER_READ_STATUS, load_saved_records
    features = _OperationFeatures(request, 'piece_v2_owner_read_enabled')
    try:
        owner = await _authenticated_owner(request)
        features.require()
        pairs = list(request.query_params.multi_items())
        query = dict(pairs)
        if (len(query) != len(pairs) or set(query) - {'limit', 'cursor'}
                or await request.body()):
            raise PieceContractError('PIECE_REQUEST_INVALID')
        features.require()
        result = await PieceOwnerService(load_records=features.wrap(load_saved_records)).history(authenticated_user_id=owner,
            limit=query.get('limit', '20'), cursor=query.get('cursor'))
        features.require()
        return _response(result)
    except Exception as exc:
        return features.failure(exc, OWNER_READ_STATUS)


@router.get('/{piece_id}')
async def owner_detail(piece_id: str, request: Request) -> JSONResponse:
    """Return the exact saved body and recipe for subsequent owner display."""
    from piece_v2_owner_service import PieceOwnerService, OWNER_READ_STATUS, load_saved_records
    features = _OperationFeatures(request, 'piece_v2_owner_read_enabled')
    try:
        owner = await _authenticated_owner(request)
        features.require()
        if request.query_params or await request.body():
            raise PieceContractError('PIECE_REQUEST_INVALID')
        features.require()
        result = await PieceOwnerService(load_records=features.wrap(load_saved_records)).detail(
            authenticated_user_id=owner, piece_id=piece_id)
        features.require()
        return _response(result)
    except Exception as exc:
        return features.failure(exc, OWNER_READ_STATUS)


_OWNER_MUTATION_STATUS = {
    'PIECE_REQUEST_INVALID': 400,
    'PIECE_AUTH_REQUIRED': 401,
    'PIECE_NOT_FOUND': 404,
    'PIECE_CONFLICT': 409,
    'PIECE_TEMPORARILY_UNAVAILABLE': 503,
}


async def _owner_mutation_rpc(name: str, args: dict) -> dict:
    """Call only the existing B4 visibility/delete terminal, once.

    Ownership, row-version conflict, same-key delete replay and purge remain
    the SQL terminal's responsibilities. Do not pre-read the former input or
    saved row: doing so would both race and reject a valid deletion replay.
    A transport failure is an unknown outcome, not permission or absence.
    """
    if name not in ('piece_set_visibility_v2', 'piece_delete_v2'):
        raise PieceContractError('PIECE_TEMPORARILY_UNAVAILABLE')
    try:
        from supabase_client import sb_post_rpc
        response = await sb_post_rpc(name, args, timeout=8.0)
        value = response.json()
        if response.status_code == 200 and type(value) is dict:
            return value
        code = 'PIECE_TEMPORARILY_UNAVAILABLE'
        if (response.status_code == 400 and type(value) is dict
                and value.get('code') == 'P0001'
                and type(value.get('message')) is str
                and value['message'] in _OWNER_MUTATION_STATUS):
            code = value['message']
        raise PieceContractError(code)
    except PieceContractError:
        raise
    except Exception:
        # No retry: a timeout/invalid ACK may follow a committed write.
        # BaseException, including task cancellation, must still propagate.
        raise PieceContractError('PIECE_TEMPORARILY_UNAVAILABLE') from None


async def _mutate_saved_piece(piece_id: str, request: Request,
                              *, operation: str) -> JSONResponse:
    from piece_v2_store import delete_piece, set_piece_visibility
    features = _OperationFeatures(request, 'piece_v2_visibility_toggle_enabled'
        if operation == 'visibility' else 'piece_v2_delete_enabled')
    try:
        owner = await _authenticated_owner(request)
        features.require()
        if request.query_params:
            raise PieceContractError('PIECE_REQUEST_INVALID')
        try:
            value = await request.json()
            raw = piece_id[6:] if piece_id.startswith('piece:') else piece_id
            pid = UUID(raw)
            if pid.int == 0 or type(value) is not dict:
                raise ValueError
        except (ValueError, UnicodeError, AttributeError):
            # Closed errors, not FastAPI's body-echoing validation response.
            raise PieceContractError('PIECE_REQUEST_INVALID') from None
        if operation == 'visibility':
            if normalize_visibility_scope(value.get('visibility_scope')) == 'public':
                features.require('piece_v2_public_write_enabled')
            result = await set_piece_visibility(authenticated_user_id=owner,
                piece_id=str(pid), request=value, rpc=features.wrap(_owner_mutation_rpc))
            # Compare with the same canonical scope that the unchanged store sent.
            # Otherwise an accepted padded value reports failure after a write.
            if result['visibility_scope'] != normalize_visibility_scope(value['visibility_scope']):
                raise PieceContractError('PIECE_TEMPORARILY_UNAVAILABLE')
        elif operation == 'delete':
            keys = request.headers.getlist('idempotency-key')
            if len(keys) != 1 or not keys[0].strip():
                raise PieceContractError('PIECE_REQUEST_INVALID')
            result = await delete_piece(authenticated_user_id=owner,
                piece_id=str(pid), request=value, idempotency_key=keys[0],
                rpc=features.wrap(_owner_mutation_rpc))
        else:
            raise PieceContractError('PIECE_TEMPORARILY_UNAVAILABLE')
        features.require()
        return _response(result)
    except Exception as exc:
        return features.failure(exc, _OWNER_MUTATION_STATUS)


@router.patch('/{piece_id}/visibility')
async def owner_visibility(piece_id: str, request: Request) -> JSONResponse:
    """Change this owner's saved visibility without rewriting the artifact."""
    return await _mutate_saved_piece(piece_id, request, operation='visibility')


@router.delete('/{piece_id}')
async def owner_delete(piece_id: str, request: Request) -> JSONResponse:
    """Delete through the existing owner/version/key-bound purge terminal."""
    return await _mutate_saved_piece(piece_id, request, operation='delete')


_PREVIEW_STATUS = {
    **_CANCEL_STATUS,
    'PIECE_FEATURE_DISABLED': 503,
    'PIECE_SOURCE_NOT_FOUND': 404,
    'PIECE_HASH_MISMATCH': 409,
    'PIECE_SOURCE_NOT_ELIGIBLE': 422,
    'PIECE_FORMAT_NOT_ELIGIBLE': 422,
    'PIECE_VISUAL_SELECTION_NOT_ALLOWED': 422,
    'PIECE_SAFETY_UNAVAILABLE': 422,
}


async def _preview_rpc(name: str, args: dict) -> dict:
    """One call to the existing fenced B5 terminal, with closed SQL errors."""
    if name != 'piece_issue_preview_v2':
        raise PieceContractError('PIECE_TEMPORARILY_UNAVAILABLE')
    try:
        from supabase_client import sb_post_rpc
        response = await sb_post_rpc(name, args, timeout=8.0)
        value = response.json()
        if response.status_code == 200 and type(value) is dict:
            return value
        code = 'PIECE_TEMPORARILY_UNAVAILABLE'
        if (response.status_code == 400 and type(value) is dict
                and value.get('code') == 'P0001'
                and type(value.get('message')) is str
                and value['message'] in _PREVIEW_STATUS):
            code = value['message']
        raise PieceContractError(code)
    except PieceContractError:
        raise
    except Exception:
        # A missing ACK is not an absent row. Only a later explicit request
        # with the same key may recover through issue_original's read path.
        raise PieceContractError('PIECE_TEMPORARILY_UNAVAILABLE') from None


def _preview_runtime(request: Request) -> tuple[int, str]:
    """Explicit server configuration; no env/defaults or client authority.

    Dedicated test applications supply app.state.piece_preview_runtime with
    ttl_seconds and renderer_version. Production admission of those values,
    router registration and live readiness remain separate.
    Missing or malformed server configuration must never issue a preview.
    """
    return validate_piece_preview_runtime(
        getattr(request.app.state, 'piece_preview_runtime', None))


def _preview_public_response(result: object) -> dict:
    """Project the persisted artifact, not the source or internal review."""
    import json
    from datetime import datetime
    from piece_v2_contract import PIECE_V2_CONTRACT_VERSIONS, canonical_json_bytes
    from piece_v2_store import _PREVIEW_RESPONSE_FIELDS, _positive, _preview_content, _uuid
    try:
        if type(result) is not dict or set(result) != _PREVIEW_RESPONSE_FIELDS:
            raise ValueError
        value = json.loads(canonical_json_bytes(result))
        _preview_content(value)
        if (UUID(_uuid(value['preview_id'])).int == 0
                or value['visibility_scope'] != 'private'
                or type(value['idempotency_replayed']) is not bool
                or type(value['expires_at']) is not str
                or datetime.fromisoformat(value['expires_at']).utcoffset() is None):
            raise ValueError
        _positive(value['preview_revision'])
        _positive(value['row_version'])
        public = {k: value[k] for k in _PREVIEW_RESPONSE_FIELDS - {
            'safety_state', 'idempotency_replayed'}}
        public.update(
            api_contract_version=PIECE_V2_CONTRACT_VERSIONS['api_contract_version'],
            piece_contract_version=PIECE_V2_CONTRACT_VERSIONS['piece_contract_version'],
            content_status=value['safety_state'])
        return public
    except Exception:
        # Corruption is not a caller error and must not return a partial body.
        raise PieceContractError('PIECE_TEMPORARILY_UNAVAILABLE') from None


@router.post('/preview')
async def create_preview(request: Request) -> JSONResponse:
    """Original-only first issuance and same-key replay via the existing B5.

    Server feature state is checked after authentication, before the service,
    immediately before RPC dispatch, and before returning a candidate. A stop
    observed here survives B5's closed error mapping. An already dispatched
    RPC cannot be undone by a later stop; no rollback or retry is attempted.
    Production registration/readiness remain separate.
    """
    from piece_v2_quota import read_piece_quota, project_piece_plan_capabilities
    from supabase_client import sb_post_rpc
    features = _OperationFeatures(request, 'piece_v2_preview_enabled')
    try:
        owner = await _authenticated_owner(request)
        features.require()
        from piece_v2_preview_service import PiecePreviewService, _request_snapshot
        keys = request.headers.getlist('idempotency-key')
        if len(keys) != 1 or not keys[0].strip() or request.query_params:
            raise PieceContractError('PIECE_REQUEST_INVALID')
        try:
            raw = await request.json()
        except (ValueError, UnicodeError):
            raise PieceContractError('PIECE_REQUEST_INVALID') from None
        value = _request_snapshot(raw)
        ttl, renderer = _preview_runtime(request)
        # Read before generation/issuance: missing quota infrastructure must
        # not create a hidden preview. This snapshot does not admit a save.
        quota = await read_piece_quota(authenticated_user_id=owner,
            post_rpc=features.wrap(sb_post_rpc))
        features.require()
        result = await PiecePreviewService().issue_original(
            request.headers['authorization'], value, idempotency_key=keys[0],
            ttl_seconds=ttl, renderer_version=renderer,
            expected_subscription_tier=quota['subscription_tier'],
            rpc=features.wrap(_preview_rpc))
        features.require()
        public = _preview_public_response(result)
        public.update(quota=quota, plan_capabilities=project_piece_plan_capabilities(
            server_tier=quota['subscription_tier']))
        return _response(public)
    except Exception as exc:
        # Cancellation (BaseException) deliberately propagates unchanged.
        return features.failure(exc, _PREVIEW_STATUS)
