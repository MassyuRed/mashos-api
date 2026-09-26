"""B5-A original retrieval slice; not a registered route or a Piece handoff.

The existing bearer verifier establishes the caller. The existing
emlis_thread_read RPC selects a live emotions row for that verified caller,
under the saved-input retention policy, even when no Emlis thread exists.
Only its original partition is retained here, never thread/event bodies.

All saved fields remain separate. This does not turn memo alone into a complete
PieceSourceSnapshot, infer a normal/refined observation stage, issue terminal
eligibility, or create a preview/record. The lifecycle caller must revalidate
before using an earlier resolution; a frozen object is not ongoing access.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hmac
import json
import re
from uuid import UUID

import httpx
from fastapi import HTTPException

from api_account_visibility import _require_user_id
from emlis_ai_current_input_bundle import (
    EMLIS_CURRENT_INPUT_BUNDLE_SCHEMA_VERSION,
    normalize_emlis_current_input,
)
from emlis_ai_nls_v3_artifact_contract import artifact_sha256
from emlis_thread_store import EmlisThreadStore, ThreadStoreError
from piece_v2_contract import PieceContractError, canonical_json_bytes, canonical_sha256_hex
from publish_governance import parse_iso_utc, timestamp_in_history_retention

# Exact projection of the existing emlis_parent_source SQL function. Unknown
# fields require an explicit adapter update, not silent source truncation.
_ORIGINAL_FIELDS = frozenset({
    'id', 'created_at', 'memo', 'memo_action', 'category', 'emotions', 'emotion_details',
})
_COMMITMENT = re.compile(r'^sha256:[0-9a-f]{64}$')


@dataclass(frozen=True, slots=True, repr=False)
class PieceSavedOriginal:
    """Request-private, immutable original data, not a public source_ref DTO.

    input_bundle_commitment uses the existing normalized input-bundle owner.
    record_commitment also covers exact stored values, including whitespace and
    nulls; the bundle schema version alone is never treated as a row revision.
    Copies returned below cannot mutate either frozen byte representation.
    """
    authenticated_owner_id: str
    saved_input_id: str
    source_input_version: str
    input_bundle_commitment: str
    record_commitment: str
    recorded_at: str
    subscription_tier: str
    _original_json: bytes = field(repr=False)
    _bundle_json: bytes = field(repr=False)

    def original_payload(self) -> dict:
        """Private source material; never include in a preview/public response."""
        return json.loads(self._original_json)

    def input_bundle_payload(self) -> dict:
        """Existing normalized bundle, still private and field-partitioned."""
        return json.loads(self._bundle_json)


def _error(code: str) -> PieceContractError:
    # Never propagate token, RPC response, source bytes or arbitrary exceptions.
    return PieceContractError(code)


def _uuid(value: object, code: str) -> str:
    if type(value) is not str:
        raise _error(code)
    try:
        return str(UUID(value))
    except (ValueError, AttributeError):
        raise _error(code) from None


def _expected(value: object) -> None:
    if value is not None and (type(value) is not str or not _COMMITMENT.fullmatch(value)):
        raise _error('PIECE_REQUEST_INVALID')


def _original(snapshot: object, input_id: str) -> tuple[dict, str]:
    if type(snapshot) is not dict or type(snapshot.get('original')) is not dict:
        raise _error('PIECE_SOURCE_NOT_FOUND')
    original = snapshot['original']
    if set(original) != _ORIGINAL_FIELDS:
        raise _error('PIECE_TEMPORARILY_UNAVAILABLE')
    if original['id'] != input_id:
        raise _error('PIECE_SOURCE_NOT_FOUND')
    if any(original[key] is not None and type(original[key]) is not str
           for key in ('memo', 'memo_action')):
        raise _error('PIECE_TEMPORARILY_UNAVAILABLE')
    for key in ('category', 'emotions'):
        value = original[key]
        if value is not None and (type(value) is not list or
                                  any(type(item) is not str for item in value)):
            raise _error('PIECE_TEMPORARILY_UNAVAILABLE')
    details = original['emotion_details']
    if details is not None and (type(details) is not list or any(
        type(item) is not dict or set(item) - {'type', 'strength'} or
        type(item.get('type')) is not str or
        ('strength' in item and type(item['strength']) is not str)
        for item in details
    )):
        raise _error('PIECE_TEMPORARILY_UNAVAILABLE')
    tier = snapshot.get('tier')
    now = snapshot.get('now')
    if (type(tier) is not str or tier not in {'free', 'plus', 'premium'} or
            type(now) is not str or parse_iso_utc(now) is None or
            type(original['created_at']) is not str or
            parse_iso_utc(original['created_at']) is None):
        raise _error('PIECE_TEMPORARILY_UNAVAILABLE')
    if not timestamp_in_history_retention(original['created_at'], tier, parse_iso_utc(now)):
        raise _error('PIECE_SOURCE_NOT_FOUND')
    return original, tier


class PieceSavedSourceAdapter:
    """Read-only binding to the current saved-original owner.

    Store injection is an internal server/test seam. Neither a caller-supplied
    owner, raw text, subscription tier nor an Emlis result is accepted by resolve.
    Reading an original is not proof that a Piece format or stage is eligible.
    """
    def __init__(self, *, store: EmlisThreadStore | None = None) -> None:
        self._store = store if store is not None else EmlisThreadStore()

    async def resolve_original(
        self, authorization: str | None, saved_input_id: str, *,
        source_input_version: str = EMLIS_CURRENT_INPUT_BUNDLE_SCHEMA_VERSION,
        expected_input_bundle_commitment: str | None = None,
        expected_record_commitment: str | None = None,
    ) -> PieceSavedOriginal:
        if authorization is not None and type(authorization) is not str:
            raise _error('PIECE_AUTH_REQUIRED')
        try:
            verified_owner = await _require_user_id(authorization)
        except HTTPException as exc:
            raise _error('PIECE_AUTH_REQUIRED' if exc.status_code in (401, 403)
                         else 'PIECE_TEMPORARILY_UNAVAILABLE') from None
        except (httpx.TransportError, httpx.TimeoutException):
            raise _error('PIECE_TEMPORARILY_UNAVAILABLE') from None
        except (ValueError, TypeError, AttributeError):
            raise _error('PIECE_TEMPORARILY_UNAVAILABLE') from None
        owner = _uuid(verified_owner, 'PIECE_AUTH_REQUIRED')
        input_id = _uuid(saved_input_id, 'PIECE_REQUEST_INVALID')
        if (type(source_input_version) is not str or
                source_input_version != EMLIS_CURRENT_INPUT_BUNDLE_SCHEMA_VERSION):
            raise _error('PIECE_SOURCE_NOT_ELIGIBLE')
        _expected(expected_input_bundle_commitment)
        _expected(expected_record_commitment)
        try:
            snapshot = await self._store.read(owner, input_id=input_id)
        except ThreadStoreError as exc:
            raise _error('PIECE_SOURCE_NOT_FOUND' if exc.status == 404
                         else 'PIECE_TEMPORARILY_UNAVAILABLE') from None
        except (httpx.TransportError, httpx.TimeoutException):
            raise _error('PIECE_TEMPORARILY_UNAVAILABLE') from None
        except HTTPException:
            raise _error('PIECE_TEMPORARILY_UNAVAILABLE') from None
        original, tier = _original(snapshot, input_id)
        # The SQL query, not an untrusted source_owner field, proves ownership.
        # Still reject a contradictory thread envelope from an invalid backend.
        thread = snapshot.get('thread')
        if thread is not None and (type(thread) is not dict or
                thread.get('user_id') != owner or thread.get('original_emotion_id') != input_id):
            raise _error('PIECE_SOURCE_NOT_FOUND')
        try:
            raw = canonical_json_bytes(original)
            # Normalize only a private copy, and retain exact original bytes too.
            bundle_source = json.loads(raw)
            # Match emlis_thread_service._request's saved-original time adapter;
            # the raw snapshot retains the database's exact representation.
            bundle_source['created_at'] = parse_iso_utc(original['created_at']).isoformat()
            bundle = normalize_emlis_current_input(bundle_source)
            bundle_bytes = canonical_json_bytes(bundle)
            raw_commitment = 'sha256:' + canonical_sha256_hex(original)
            # The source-bundle owner uses NFC/LF canonicalization. A Piece
            # artifact hash is not a substitute; exact edits remain covered
            # independently by raw_commitment.
            bundle_commitment = 'sha256:' + artifact_sha256(bundle)
        except (ValueError, TypeError, UnicodeError):
            raise _error('PIECE_TEMPORARILY_UNAVAILABLE') from None
        if ((expected_record_commitment is not None and
             not hmac.compare_digest(expected_record_commitment, raw_commitment)) or
            (expected_input_bundle_commitment is not None and
             not hmac.compare_digest(expected_input_bundle_commitment, bundle_commitment))):
            raise _error('PIECE_CONFLICT')
        return PieceSavedOriginal(
            owner, input_id, source_input_version, bundle_commitment, raw_commitment,
            original['created_at'], tier, raw, bundle_bytes,
        )

    async def revalidate_original(
        self, authorization: str | None, previous: PieceSavedOriginal,
    ) -> PieceSavedOriginal:
        """Re-read owner, liveness, retention and exact revision at this instant.

        A later preview/save still needs its own operation-boundary checks.
        This read is not a transaction spanning future generation or writes.
        """
        if type(previous) is not PieceSavedOriginal:
            raise _error('PIECE_REQUEST_INVALID')
        current = await self.resolve_original(
            authorization, previous.saved_input_id,
            source_input_version=previous.source_input_version,
            expected_input_bundle_commitment=previous.input_bundle_commitment,
            expected_record_commitment=previous.record_commitment,
        )
        if current.authenticated_owner_id != previous.authenticated_owner_id:
            raise _error('PIECE_SOURCE_NOT_FOUND')
        if current.subscription_tier != previous.subscription_tier:
            raise _error('PIECE_CONFLICT')
        return current


    async def generate_original_candidate_for_development(
        self, authorization: str | None, saved_input_id: str, *,
        source_stage: str, requested_format: str | None = None,
    ) -> dict:
        """Exercise saved retrieval -> CMEE without issuing preview eligibility.

        source_stage is an explicit OFFLINE caller choice, not a terminal-state
        attestation. No API registers this method; production B5 must still
        resolve its stage/control lineage. Revalidation prevents returning a
        candidate after an observed edit, revocation or entitlement change; it
        is not a transaction spanning a future save or image export.
        """
        from piece_v2_generation import generate_piece_candidate
        saved = await self.resolve_original(authorization, saved_input_id)
        source = project_saved_original_source(saved, source_stage=source_stage)
        candidate = generate_piece_candidate(
            source, authenticated_owner_id=saved.authenticated_owner_id,
            tier=saved.subscription_tier, requested_format=requested_format)
        await self.revalidate_original(authorization, saved)
        return candidate


def project_saved_original_source(saved: PieceSavedOriginal, *, source_stage: str):
    """Project both written fields; preserve the complete private record.

    The complete-sentence and semantic admission remain in CMEE. Structured
    feelings must be interpreted there before they can be omitted or verbalized;
    this projection neither converts labels to a stance nor assumes eligibility.
    """
    from piece_v2_generation import PieceSourceSnapshot
    if type(saved) is not PieceSavedOriginal:
        raise _error('PIECE_REQUEST_INVALID')
    if source_stage not in ('normal_observation', 'pre_question_observation'):
        raise _error('PIECE_SOURCE_NOT_ELIGIBLE')
    original = saved.original_payload()
    if (original.get('id') != saved.saved_input_id or
            saved.record_commitment != 'sha256:' + canonical_sha256_hex(original)):
        raise _error('PIECE_CONFLICT')
    fields = [original[key] for key in ('memo', 'memo_action')
              if original[key] is not None and original[key].strip()]
    return PieceSourceSnapshot(
        saved.authenticated_owner_id, saved.saved_input_id,
        saved.source_input_version, '\n\n'.join(fields),
        source_role='original', source_stage=source_stage,
        saved_original_json=saved._original_json)
