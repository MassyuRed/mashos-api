"""B6 saved-preview admission; unregistered until the Piece clean cutover.

Only an already persisted, server-admitted preview is accepted. This module
neither issues previews nor grants safety approval to PreparedPiecePreview.
It never generates, repairs or replaces the preview's canonical text/recipe.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from piece_v2_content_policy import choose_format
from piece_v2_contract import PieceContractError, canonical_json_bytes
from piece_v2_source_adapter import PieceSavedHandoff, PieceSavedSourceAdapter
from piece_v2_store import _preview_content, save_piece, save_request_arguments
from piece_v2_visual import build_visual_recipe

SAVE_STATUS = {
    'PIECE_REQUEST_INVALID': 400, 'PIECE_AUTH_REQUIRED': 401,
    'PIECE_NOT_FOUND': 404, 'PIECE_SOURCE_NOT_FOUND': 404,
    'PIECE_PREVIEW_STALE': 409, 'PIECE_PREVIEW_EXPIRED': 409,
    'PIECE_HASH_MISMATCH': 409, 'PIECE_QUOTA_EXHAUSTED': 409, 'PIECE_CONFLICT': 409,
    'PIECE_SOURCE_NOT_ELIGIBLE': 422, 'PIECE_FORMAT_NOT_ELIGIBLE': 422,
    'PIECE_VISUAL_SELECTION_NOT_ALLOWED': 422, 'PIECE_SAFETY_UNAVAILABLE': 422,
    'PIECE_TEMPORARILY_UNAVAILABLE': 503,
}
_COLUMNS = ('id', 'owner_user_id', 'piece_contract_version', 'lifecycle_status',
    'preview_revision', 'expires_at', 'visibility_scope', 'source_lineage',
    'format_type', 'preview_eligible_formats', 'content_payload', 'content_payload_hash',
    'piece_text', 'piece_text_hash', 'safety_state', 'visual_recipe',
    'visual_recipe_hash', 'renderer_version')


def _fail(code='PIECE_TEMPORARILY_UNAVAILABLE'):
    raise PieceContractError(code) from None


async def load_owned_preview(owner: str, preview_id: str) -> dict | None:
    """Service-only read, always constrained by the verified owner AND ID."""
    from supabase_client import sb_get
    response = await sb_get('/rest/v1/piece_records', params={
        'select': ','.join(_COLUMNS), 'id': 'eq.' + preview_id,
        'owner_user_id': 'eq.' + owner, 'limit': '2'}, timeout=8.0)
    if response.status_code != 200:
        _fail()
    rows = response.json()
    if type(rows) is not list or len(rows) > 1:
        _fail()
    return rows[0] if rows else None


async def save_rpc(name: str, args: dict) -> dict:
    """One POST; transport uncertainty never starts another save automatically."""
    if name != 'piece_save_v2':
        _fail()
    from supabase_client import sb_post_rpc
    response = await sb_post_rpc(name, args, timeout=8.0)
    value = response.json()
    if response.status_code == 200 and type(value) is dict:
        return value
    if (response.status_code == 400 and type(value) is dict
            and value.get('code') == 'P0001' and type(value.get('message')) is str
            and value['message'] in SAVE_STATUS):
        _fail(value['message'])
    _fail()


class PieceSaveService:
    def __init__(self, *, load_record=load_owned_preview, rpc=save_rpc,
                 source_adapter=None):
        self._load_record, self._rpc = load_record, rpc
        self._source_adapter = source_adapter if source_adapter is not None else PieceSavedSourceAdapter()

    async def save(self, authorization: str, *, authenticated_user_id: str,
                   request: dict, idempotency_key: str) -> dict:
        """The HTTP owner authenticates every call, including committed replay.

        For a first save, B5 rechecks current source eligibility without calling
        the Piece author. SQL then holds the exact original/profile/thread
        through the atomic save. Q3 historical context, complete public-safety
        issuance, and production registration remain separate acceptance work.
        """
        try:
            args = save_request_arguments(authenticated_user_id, request, idempotency_key)
            # Own all request fields before the first await.
            value = {k[2:]: v for k, v in args.items() if k not in
                     ('p_owner_user_id', 'p_idempotency_key_hash')}
            owner, pid = args['p_owner_user_id'], args['p_preview_id']
            raw = await self._load_record(owner, pid)
            if raw is None:
                _fail('PIECE_NOT_FOUND')
            row = json.loads(canonical_json_bytes(raw))
            if (type(row) is not dict or row.get('id') != pid
                    or row.get('owner_user_id') != owner
                    or row.get('piece_contract_version') != 'piece.record.v2'):
                _fail('PIECE_NOT_FOUND')
            if type(row.get('preview_revision')) is not int or row['preview_revision'] < 1:
                _fail()
            if row['preview_revision'] != value['expected_preview_revision']:
                _fail('PIECE_PREVIEW_STALE')
            if any(row.get(key) != value[key] for key in
                   ('piece_text_hash', 'content_payload_hash', 'visual_recipe_hash')):
                _fail('PIECE_HASH_MISMATCH')
            if row.get('lifecycle_status') == 'saved':
                # SQL verifies the persisted key/consumption; it cannot fall
                # back to first save after this read, even with a stale row.
                return await save_piece(authenticated_user_id=owner, request=value,
                    idempotency_key=idempotency_key, rpc=self._rpc, replay_only=True)
            if row.get('lifecycle_status') != 'preview_draft':
                _fail('PIECE_CONFLICT')
            if row.get('visibility_scope') != 'private':
                _fail()
            expiry = datetime.fromisoformat(row['expires_at'].replace('Z', '+00:00'))
            if expiry.utcoffset() is None:
                _fail()
            if expiry <= datetime.now(timezone.utc):
                _fail('PIECE_PREVIEW_EXPIRED')
            if row.get('safety_state') not in ('ready', 'adjusted'):
                _fail('PIECE_SAFETY_UNAVAILABLE')
            content = dict(row, eligible_formats=row.get('preview_eligible_formats'))
            try:
                _preview_content(content)
            except PieceContractError:
                _fail('PIECE_HASH_MISMATCH')
            lineage = row['source_lineage']
            current = await self._source_adapter.resolve_original_handoff(
                authorization, lineage['source_input']['source_input_id'])
            if (type(current) is not PieceSavedHandoff
                    or current.original.authenticated_owner_id != owner):
                _fail('PIECE_SOURCE_NOT_FOUND')
            if canonical_json_bytes(current.lineage_payload()) != canonical_json_bytes(lineage):
                _fail('PIECE_CONFLICT')
            tier, fmt = current.original.subscription_tier, row['format_type']
            formats = tuple(row['preview_eligible_formats'])
            # The existing CMEE author recommends declaration, then quote,
            # then essay. Validate that decision only; never re-run its author.
            recommended = next((f for f in ('declaration', 'quote', 'short_essay') if f in formats), None)
            try:
                selected = choose_format(tier=tier, requested=fmt if tier == 'premium' else None,
                    eligible=formats, recommended=recommended)
                if selected != fmt:
                    _fail('PIECE_FORMAT_NOT_ELIGIBLE')
            except PieceContractError:
                _fail('PIECE_FORMAT_NOT_ELIGIBLE')
            recipe = row['visual_recipe']
            try:
                allowed = build_visual_recipe(fmt, tier=tier, language=row['content_payload']['language'],
                    theme=recipe['theme']['theme_id'], aspect_ratio=recipe['aspect_ratio'],
                    branding=recipe['branding']['branding_mode'])
                if allowed != recipe:
                    _fail('PIECE_VISUAL_SELECTION_NOT_ALLOWED')
            except PieceContractError:
                _fail('PIECE_VISUAL_SELECTION_NOT_ALLOWED')
            return await save_piece(authenticated_user_id=owner, request=value,
                idempotency_key=idempotency_key, rpc=self._rpc, expected_subscription_tier=tier,
                expected_source_state={'original': current.original.original_payload(),
                    'thread_id': current.thread_id, 'thread_revision': current.thread_revision,
                    'lineage': current.lineage_payload()})
        except PieceContractError as exc:
            _fail(exc.code if exc.code in SAVE_STATUS else 'PIECE_TEMPORARILY_UNAVAILABLE')
        except Exception:
            _fail()
