"""Transport for Piece's saved-source references and explicit answer selection.

The 2026-10-08 binding is GET /emotion/piece/source-ref/{saved_input_id}.
The separate router is installed by the existing Piece application factory,
not included in api_piece_v2.router. Import does not enable a deployed service.
Importing this module performs no reads or writes. Explicitly mounted test apps
can exercise it with explicit server readiness; live admission is separate.
An optional exact saved answer identity selects refined material; its absence
retains the existing original-only lookup and never selects a latest answer.
Source eligibility belongs to the saved adapter. References do not authorize
preview, save or image export.
"""
from __future__ import annotations

import json
import re
from uuid import UUID

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from api_piece_v2 import _authenticated_owner, _response, _OperationFeatures
from piece_v2_contract import PieceContractError

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


def _source_ref_response(value: object, saved_input_id: str, *, selected_answer: str | None = None) -> dict:
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
                or not reference(value['emlis_observation_result_identity'])):
            raise ValueError
        stage, question = value['emlis_observation_stage'], value['question_need_decision_identity']
        answer = value['supplemental_answer_identity']
        if not ((selected_answer is None and answer is None and (
                    stage == 'normal_observation' and question is None
                    or stage == 'pre_question_observation' and reference(question)))
                or (selected_answer is not None and stage == 'refined_observation'
                    and reference(question) and answer == selected_answer)):
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
    A single supplemental_answer_identity query explicitly selects one saved
    answer. Without it the original-only request remains unchanged. A caller
    stage, owner, tier, answer body or eligibility flag is never accepted.
    """
    features = _OperationFeatures(request, 'piece_v2_preview_enabled')
    try:
        await _authenticated_owner(request)
        features.require()
        query = list(request.query_params.multi_items())
        if (query and (len(query) != 1 or query[0][0] != 'supplemental_answer_identity')) or await request.body():
            raise PieceContractError('PIECE_REQUEST_INVALID')
        selected_answer = query[0][1] if query else None
        try:
            identifier = UUID(saved_input_id)
            if identifier.int == 0 or str(identifier) != saved_input_id:
                raise ValueError
            if selected_answer is not None:
                answer_uuid = UUID(selected_answer)
                if answer_uuid.int == 0 or str(answer_uuid) != selected_answer:
                    raise ValueError
        except (ValueError, AttributeError):
            raise PieceContractError('PIECE_REQUEST_INVALID') from None
        features.require()
        from piece_v2_source_adapter import PieceSavedSourceAdapter
        adapter = PieceSavedSourceAdapter()
        if selected_answer is None:
            result = await features.wrap(adapter.resolve_original_source_ref)(
                request.headers['authorization'], saved_input_id)
        else:
            result = await features.wrap(adapter.resolve_refined_source_ref)(
                request.headers['authorization'], saved_input_id,
                supplemental_answer_identity=selected_answer, opted_in=True)
        features.require()
        return _response(_source_ref_response(result, saved_input_id, selected_answer=selected_answer))
    except Exception as exc:
        # No source fragments, tokens or infrastructure details in the reply.
        # BaseException/task cancellation is intentionally not caught.
        return features.failure(exc, _SOURCE_REF_STATUS)
