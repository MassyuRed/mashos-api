"""Unregistered transport for Piece's existing original-source references.

The 2026-10-08 binding is GET /emotion/piece/source-ref/{saved_input_id}.
This separate router is NOT included in api_piece_v2.router or production app.
The binding's adoption does not authorize registration, deployment or activation.
Importing this module performs no reads or writes. Explicitly mounted test apps
can exercise it with explicit server readiness; live admission is separate.
Source eligibility belongs to the saved adapter. References do not authorize
preview, save or image export.
"""
from __future__ import annotations

import json
import re
from uuid import UUID

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from api_piece_v2 import _authenticated_owner, _response
from piece_v2_contract import PieceContractError
from piece_v2_runtime_control import require_piece_feature_enabled

source_ref_router = APIRouter(prefix='/emotion/piece')
_SOURCE_REF_FIELDS = frozenset({
    'source_input_id', 'source_input_version', 'source_input_bundle_commitment',
    'emlis_observation_stage', 'emlis_observation_result_identity',
    'question_need_decision_identity', 'supplemental_answer_identity',
})
_SOURCE_REF_STATUS = {
    'PIECE_REQUEST_INVALID': 400, 'PIECE_AUTH_REQUIRED': 401,
    'PIECE_SOURCE_NOT_FOUND': 404, 'PIECE_SOURCE_NOT_ELIGIBLE': 422,
    'PIECE_CONFLICT': 409, 'PIECE_TEMPORARILY_UNAVAILABLE': 503,
    'PIECE_FEATURE_DISABLED': 503,
}


def _source_ref_response(value: object, saved_input_id: str) -> dict:
    """Reject malformed/private additions, rather than trimming them away."""
    def reference(item):
        return (type(item) is str and bool(item)
                and not any(c.isspace() or 0xD800 <= ord(c) <= 0xDFFF for c in item))

    try:
        if type(value) is not dict or set(value) != _SOURCE_REF_FIELDS:
            raise ValueError
        if (value['source_input_id'] != saved_input_id
                or value['source_input_version'] != 'emlis.current_input_bundle.v1'
                or type(value['source_input_bundle_commitment']) is not str
                or re.fullmatch(r'sha256:[0-9a-f]{64}', value['source_input_bundle_commitment']) is None
                or not reference(value['emlis_observation_result_identity'])
                or value['supplemental_answer_identity'] is not None):
            raise ValueError
        stage, question = value['emlis_observation_stage'], value['question_need_decision_identity']
        if not ((stage == 'normal_observation' and question is None)
                or (stage == 'pre_question_observation' and reference(question))):
            raise ValueError
        # Exact scalar-only projection; no private handoff, body, owner or tier.
        return json.loads(json.dumps(value, ensure_ascii=False, allow_nan=False))
    except Exception:
        raise PieceContractError('PIECE_TEMPORARILY_UNAVAILABLE') from None


@source_ref_router.get('/source-ref/{saved_input_id}')
async def read_original_source_ref(saved_input_id: str, request: Request) -> JSONResponse:
    """Explicit authenticated GET, without source generation or persistence.

    The saved-state adapter performs the current-owner/source checks and its
    pre-return revalidation. A later preview request independently revalidates.
    No body/query, caller stage, owner, tier, eligibility or new key is accepted.
    """
    try:
        await _authenticated_owner(request)
        require_piece_feature_enabled(request.app, 'piece_v2_preview_enabled')
        if request.query_params or await request.body():
            raise PieceContractError('PIECE_REQUEST_INVALID')
        try:
            identifier = UUID(saved_input_id)
            if identifier.int == 0 or str(identifier) != saved_input_id:
                raise ValueError
        except (ValueError, AttributeError):
            raise PieceContractError('PIECE_REQUEST_INVALID') from None
        require_piece_feature_enabled(request.app, 'piece_v2_preview_enabled')
        from piece_v2_source_adapter import PieceSavedSourceAdapter
        result = await PieceSavedSourceAdapter().resolve_original_source_ref(
            request.headers['authorization'], saved_input_id)
        require_piece_feature_enabled(request.app, 'piece_v2_preview_enabled')
        return _response(_source_ref_response(result, saved_input_id))
    except PieceContractError as exc:
        code = exc.code if exc.code in _SOURCE_REF_STATUS else 'PIECE_TEMPORARILY_UNAVAILABLE'
        return _response({'code': code}, _SOURCE_REF_STATUS[code])
    except Exception:
        # No source fragments, tokens or infrastructure details in the reply.
        # BaseException/task cancellation is intentionally not caught.
        return _response({'code': 'PIECE_TEMPORARILY_UNAVAILABLE'}, 503)
