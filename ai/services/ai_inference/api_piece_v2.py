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
    from piece_v2_save_service import PieceSaveService, SAVE_STATUS
    try:
        owner = await _authenticated_owner(request)
        keys = request.headers.getlist('idempotency-key')
        if len(keys) != 1 or not keys[0].strip() or request.query_params:
            raise PieceContractError('PIECE_REQUEST_INVALID')
        try:
            value = await request.json()
        except (ValueError, UnicodeError):
            raise PieceContractError('PIECE_REQUEST_INVALID') from None
        result = await PieceSaveService().save(request.headers['authorization'],
            authenticated_user_id=owner, request=value, idempotency_key=keys[0])
        return _response(result)
    except PieceContractError as exc:
        code = exc.code if exc.code in SAVE_STATUS else 'PIECE_TEMPORARILY_UNAVAILABLE'
        return _response({'code': code}, SAVE_STATUS[code])
    except Exception:
        return _response({'code': 'PIECE_TEMPORARILY_UNAVAILABLE'}, 503)


# Static owner paths must precede /{piece_id}; production remains unregistered.
@router.get('/history')
async def owner_history(request: Request) -> JSONResponse:
    """Read only the authenticated owner's saved private/public artifacts."""
    from piece_v2_owner_service import PieceOwnerService, OWNER_READ_STATUS
    try:
        owner = await _authenticated_owner(request)
        pairs = list(request.query_params.multi_items())
        query = dict(pairs)
        if (len(query) != len(pairs) or set(query) - {'limit', 'cursor'}
                or await request.body()):
            raise PieceContractError('PIECE_REQUEST_INVALID')
        result = await PieceOwnerService().history(authenticated_user_id=owner,
            limit=query.get('limit', '20'), cursor=query.get('cursor'))
        return _response(result)
    except PieceContractError as exc:
        code = exc.code if exc.code in OWNER_READ_STATUS else 'PIECE_TEMPORARILY_UNAVAILABLE'
        return _response({'code': code}, OWNER_READ_STATUS[code])
    except Exception:
        return _response({'code': 'PIECE_TEMPORARILY_UNAVAILABLE'}, 503)


@router.get('/{piece_id}')
async def owner_detail(piece_id: str, request: Request) -> JSONResponse:
    """Return the exact saved body and recipe for subsequent owner display."""
    from piece_v2_owner_service import PieceOwnerService, OWNER_READ_STATUS
    try:
        owner = await _authenticated_owner(request)
        if request.query_params or await request.body():
            raise PieceContractError('PIECE_REQUEST_INVALID')
        result = await PieceOwnerService().detail(authenticated_user_id=owner, piece_id=piece_id)
        return _response(result)
    except PieceContractError as exc:
        code = exc.code if exc.code in OWNER_READ_STATUS else 'PIECE_TEMPORARILY_UNAVAILABLE'
        return _response({'code': code}, OWNER_READ_STATUS[code])
    except Exception:
        return _response({'code': 'PIECE_TEMPORARILY_UNAVAILABLE'}, 503)


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
    try:
        owner = await _authenticated_owner(request)
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
            result = await set_piece_visibility(authenticated_user_id=owner,
                piece_id=str(pid), request=value, rpc=_owner_mutation_rpc)
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
                rpc=_owner_mutation_rpc)
        else:
            raise PieceContractError('PIECE_TEMPORARILY_UNAVAILABLE')
        return _response(result)
    except PieceContractError as exc:
        code = exc.code if exc.code in _OWNER_MUTATION_STATUS else 'PIECE_TEMPORARILY_UNAVAILABLE'
        return _response({'code': code}, _OWNER_MUTATION_STATUS[code])
    except Exception:
        return _response({'code': 'PIECE_TEMPORARILY_UNAVAILABLE'}, 503)


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
    router registration, capabilities/quota and RN delivery remain separate.
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
    Production registration/readiness and capability delivery remain separate.
    """
    disabled = False

    def require_preview() -> None:
        nonlocal disabled
        if disabled:
            raise PieceContractError('PIECE_FEATURE_DISABLED')
        try:
            require_piece_feature_enabled(request.app, 'piece_v2_preview_enabled')
        except PieceContractError:
            disabled = True
            raise

    async def gated_rpc(name: str, args: dict) -> dict:
        require_preview()
        return await _preview_rpc(name, args)

    try:
        await _authenticated_owner(request)
        require_preview()
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
        require_preview()
        result = await PiecePreviewService().issue_original(
            request.headers['authorization'], value, idempotency_key=keys[0],
            ttl_seconds=ttl, renderer_version=renderer, rpc=gated_rpc)
        require_preview()
        return _response(_preview_public_response(result))
    except PieceContractError as exc:
        code = ('PIECE_FEATURE_DISABLED' if disabled else
                exc.code if exc.code in _PREVIEW_STATUS else 'PIECE_TEMPORARILY_UNAVAILABLE')
        return _response({'code': code}, _PREVIEW_STATUS[code])
    except Exception:
        # Cancellation (BaseException) is deliberately not converted to HTTP.
        code = 'PIECE_FEATURE_DISABLED' if disabled else 'PIECE_TEMPORARILY_UNAVAILABLE'
        return _response({'code': code}, 503)
