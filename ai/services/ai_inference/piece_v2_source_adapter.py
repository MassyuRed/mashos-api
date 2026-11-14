"""Disabled B5-A saved-original retrieval and original-only state handoff.

The existing bearer verifier establishes the caller. The existing
emlis_thread_read RPC selects a live emotions row for that verified caller,
under the saved-input retention policy, even when no Emlis thread exists.
Original and explicitly selected supplemental partitions retain separate owners.

All saved fields remain separate. The original state-bound path admits only
an already committed, current INITIAL observation: normal or pre-question,
without answers. A separate explicitly opted-in refined reader admits
one resolved answer without extending original stage eligibility.
The earlier explicit-stage method remains an offline probe, not authority.
A frozen object is not ongoing access; later operations revalidate current state.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hmac
import json
import re
from uuid import UUID
from typing import TYPE_CHECKING

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

if TYPE_CHECKING:
    from cocolon_meaning_experience_engine.emlis_thread_contracts import SupplementalAnswerSource

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


@dataclass(frozen=True, slots=True, repr=False)
class PieceSavedHandoff:
    """Private original and immutable body-free lineage, not a public DTO."""
    original: PieceSavedOriginal
    thread_id: str
    thread_revision: int
    _lineage_json: bytes = field(repr=False)

    def lineage_payload(self) -> dict:
        return json.loads(self._lineage_json)


@dataclass(frozen=True, slots=True, repr=False)
class PieceSavedRefinedHandoff:
    """Private, explicitly selected answer beside the unchanged saved input.

    This handoff does not extend original stage eligibility.
    The answer's existing source owner retains its identity and text; no
    Emlis observation, question body or inferred meaning becomes Piece input.
    """
    original: PieceSavedOriginal
    supplemental: SupplementalAnswerSource
    thread_id: str
    thread_revision: int
    _lineage_json: bytes = field(repr=False)
    supplemental_update_operation: str = 'ADD'
    original_active_ranges: tuple[tuple[str, int, int], ...] = ()
    supplemental_active_range: tuple[int, int] | None = None
    _meaning_checkpoint_json: bytes | None = field(default=None, repr=False)

    def lineage_payload(self) -> dict:
        return json.loads(self._lineage_json)


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
        saved, _snapshot = await self._resolve_original_with_snapshot(
            authorization, saved_input_id, source_input_version=source_input_version,
            expected_input_bundle_commitment=expected_input_bundle_commitment,
            expected_record_commitment=expected_record_commitment)
        return saved

    async def _resolve_original_with_snapshot(
        self, authorization: str | None, saved_input_id: str, *,
        source_input_version: str = EMLIS_CURRENT_INPUT_BUNDLE_SCHEMA_VERSION,
        expected_input_bundle_commitment: str | None = None,
        expected_record_commitment: str | None = None,
    ) -> tuple[PieceSavedOriginal, dict]:
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
        ), snapshot

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


    async def resolve_original_handoff(
        self, authorization: str | None, saved_input_id: str,
    ) -> PieceSavedHandoff:
        """Derive stage from the saved result, never from a client stage/bool.

        Reuse the Emlis saved-reader's source/profile and context validity rules.
        This reads existing control metadata; it does not run an Emlis author or
        pass its text, question, interpretation or history to the Piece author.
        """
        from emlis_thread_service import _check, _generation_current, Q3_PROFILE, NATURAL_REPLY_PROFILE
        saved, snapshot = await self._resolve_original_with_snapshot(
            authorization, saved_input_id)
        try:
            thread = _check(snapshot)
            if thread is None:
                raise _error('PIECE_SOURCE_NOT_ELIGIBLE')
            if thread['data']['runtime_profile'] == Q3_PROFILE:
                if thread['data'].get('response_profile') == NATURAL_REPLY_PROFILE:
                    snapshot['context'] = await self._store.related_context(
                        saved.authenticated_owner_id, saved.saved_input_id,
                        context_guards=thread['data'].get('context_guards', []))
                else:
                    snapshot['context'] = await self._store.context(
                        saved.authenticated_owner_id, saved.saved_input_id)
            if not _generation_current(snapshot):
                raise _error('PIECE_SOURCE_NOT_ELIGIBLE')
            return _original_observation_handoff(saved, snapshot)
        except PieceContractError:
            raise
        except ThreadStoreError as exc:
            raise _error('PIECE_SOURCE_NOT_FOUND' if exc.status == 404 else
                         'PIECE_CONFLICT' if exc.status == 409 else
                         'PIECE_TEMPORARILY_UNAVAILABLE') from None
        except (httpx.TransportError, httpx.TimeoutException, HTTPException):
            raise _error('PIECE_TEMPORARILY_UNAVAILABLE') from None
        except (ValueError, TypeError, KeyError, AttributeError, UnicodeError):
            raise _error('PIECE_SOURCE_NOT_ELIGIBLE') from None

    async def resolve_refined_handoff(
        self, authorization: str | None, saved_input_id: str, *,
        supplemental_answer_identity: str, opted_in: bool,
    ) -> PieceSavedRefinedHandoff:
        """Read one explicitly selected, committed additive answer.

        A caller must opt into the exact saved answer. Its separate source is
        returned only after the existing owner, retention, source and context
        checks and successful refined-result lineage have been revalidated.
        No preview, record or quota is issued here.
        """
        if opted_in is not True:
            raise _error('PIECE_SOURCE_NOT_ELIGIBLE')
        answer_id = _uuid(supplemental_answer_identity, 'PIECE_REQUEST_INVALID')
        from emlis_thread_service import _check, _generation_current, Q3_PROFILE, NATURAL_REPLY_PROFILE
        saved, snapshot = await self._resolve_original_with_snapshot(authorization, saved_input_id)
        try:
            thread = _check(snapshot)
            if thread is None:
                raise _error('PIECE_SOURCE_NOT_ELIGIBLE')
            if thread['data'].get('response_profile') not in {None, NATURAL_REPLY_PROFILE}:
                raise _error('PIECE_SOURCE_NOT_ELIGIBLE')
            if thread['data']['runtime_profile'] == Q3_PROFILE:
                if thread['data'].get('response_profile') == NATURAL_REPLY_PROFILE:
                    snapshot['context'] = await self._store.related_context(
                        saved.authenticated_owner_id, saved.saved_input_id,
                        context_guards=thread['data'].get('context_guards', []))
                else:
                    snapshot['context'] = await self._store.context(
                        saved.authenticated_owner_id, saved.saved_input_id)
            if not _generation_current(snapshot):
                raise _error('PIECE_SOURCE_NOT_ELIGIBLE')
            return _refined_observation_handoff(saved, snapshot, answer_id)
        except PieceContractError:
            raise
        except ThreadStoreError as exc:
            raise _error('PIECE_SOURCE_NOT_FOUND' if exc.status == 404 else
                         'PIECE_CONFLICT' if exc.status == 409 else
                         'PIECE_TEMPORARILY_UNAVAILABLE') from None
        except (httpx.TransportError, httpx.TimeoutException, HTTPException):
            raise _error('PIECE_TEMPORARILY_UNAVAILABLE') from None
        except (ValueError, TypeError, KeyError, AttributeError, UnicodeError):
            raise _error('PIECE_SOURCE_NOT_ELIGIBLE') from None

    async def revalidate_refined_handoff(
        self, authorization: str | None, previous: PieceSavedRefinedHandoff, *, opted_in: bool,
    ) -> PieceSavedRefinedHandoff:
        if type(previous) is not PieceSavedRefinedHandoff:
            raise _error('PIECE_REQUEST_INVALID')
        current = await self.resolve_refined_handoff(
            authorization, previous.original.saved_input_id,
            supplemental_answer_identity=previous.supplemental.answer_id, opted_in=opted_in)
        if current != previous:
            raise _error('PIECE_CONFLICT')
        return current

    async def resolve_original_source_ref(
        self, authorization: str | None, saved_input_id: str,
    ) -> dict:
        """Supply PCE-6's seven references from the existing saved-state owner.

        This is an internal read, not a new HTTP route or a flag/CTA decision.
        The client need not hash raw input or infer an Emlis stage. The later
        preview request must still revalidate the source and every reference;
        this result is neither an access token nor continuing eligibility.
        """
        allowed_errors = {
            'PIECE_REQUEST_INVALID', 'PIECE_AUTH_REQUIRED',
            'PIECE_SOURCE_NOT_FOUND', 'PIECE_SOURCE_NOT_ELIGIBLE',
            'PIECE_CONFLICT', 'PIECE_TEMPORARILY_UNAVAILABLE',
        }
        try:
            handoff = await self.resolve_original_handoff(authorization, saved_input_id)
            if type(handoff) is not PieceSavedHandoff:
                raise _error('PIECE_TEMPORARILY_UNAVAILABLE')
            lineage = handoff.lineage_payload()
            source = lineage['source_input']
            observation = lineage['observation']
            # Explicit projection: never serialize the private handoff, source
            # fields, owner, context, or any Emlis/Analysis text into this DTO.
            result = {key: source[key] for key in (
                'source_input_id', 'source_input_version', 'source_input_bundle_commitment')}
            result.update({key: observation[key] for key in (
                'emlis_observation_stage', 'emlis_observation_result_identity',
                'question_need_decision_identity', 'supplemental_answer_identity')})
            current = await self.revalidate_original_handoff(authorization, handoff)
            if current != handoff:
                raise _error('PIECE_CONFLICT')
            return result
        except PieceContractError as exc:
            raise _error(exc.code if exc.code in allowed_errors else
                         'PIECE_TEMPORARILY_UNAVAILABLE') from None
        except Exception:
            # A partial projection is not returned; cancellation still escapes.
            raise _error('PIECE_TEMPORARILY_UNAVAILABLE') from None

    async def resolve_refined_source_ref(
        self, authorization: str | None, saved_input_id: str, *,
        supplemental_answer_identity: str, opted_in: bool,
    ) -> dict:
        """Project the same seven references for an explicitly selected answer.

        Answer text and its private commitment remain server-side. This DTO
        cannot authorize a later write or select the then-latest answer.
        """
        allowed_errors = {
            'PIECE_REQUEST_INVALID', 'PIECE_AUTH_REQUIRED',
            'PIECE_SOURCE_NOT_FOUND', 'PIECE_SOURCE_NOT_ELIGIBLE',
            'PIECE_CONFLICT', 'PIECE_TEMPORARILY_UNAVAILABLE',
        }
        try:
            handoff = await self.resolve_refined_handoff(
                authorization, saved_input_id,
                supplemental_answer_identity=supplemental_answer_identity, opted_in=opted_in)
            lineage = project_saved_refined_lineage(handoff, opted_in=opted_in)
            source, observation = lineage['source_input'], lineage['observation']
            result = {key: source[key] for key in (
                'source_input_id', 'source_input_version', 'source_input_bundle_commitment')}
            result.update({key: observation[key] for key in (
                'emlis_observation_stage', 'emlis_observation_result_identity',
                'question_need_decision_identity', 'supplemental_answer_identity')})
            current = await self.revalidate_refined_handoff(
                authorization, handoff, opted_in=opted_in)
            if current != handoff:
                raise _error('PIECE_CONFLICT')
            return result
        except PieceContractError as exc:
            raise _error(exc.code if exc.code in allowed_errors else
                         'PIECE_TEMPORARILY_UNAVAILABLE') from None
        except Exception:
            raise _error('PIECE_TEMPORARILY_UNAVAILABLE') from None

    async def revalidate_original_handoff(
        self, authorization: str | None, previous: PieceSavedHandoff,
    ) -> PieceSavedHandoff:
        if type(previous) is not PieceSavedHandoff:
            raise _error('PIECE_REQUEST_INVALID')
        current = await self.resolve_original_handoff(
            authorization, previous.original.saved_input_id)
        if current.original.authenticated_owner_id != previous.original.authenticated_owner_id:
            raise _error('PIECE_SOURCE_NOT_FOUND')
        if (current.original != previous.original or
                current.thread_id != previous.thread_id or
                current.thread_revision != previous.thread_revision or
                not hmac.compare_digest(current._lineage_json, previous._lineage_json)):
            raise _error('PIECE_CONFLICT')
        return current

    async def generate_original_candidate_from_saved_state(
        self, authorization: str | None, saved_input_id: str, *,
        requested_format: str | None = None,
    ) -> dict:
        """Internal candidate plus lineage; no registered preview or save API.

        The existing CMEE/B8 author still decides content/format eligibility.
        The second authenticated read prevents returning a candidate after an
        observed source/control/access change. Later operations must recheck;
        these reads are not a transaction spanning save or image export.
        """
        from piece_v2_generation import generate_piece_candidate
        handoff = await self.resolve_original_handoff(authorization, saved_input_id)
        lineage = handoff.lineage_payload()
        source = project_saved_original_source(handoff.original,
            source_stage=lineage['observation']['emlis_observation_stage'])
        candidate = generate_piece_candidate(source,
            authenticated_owner_id=handoff.original.authenticated_owner_id,
            tier=handoff.original.subscription_tier, requested_format=requested_format)
        await self.revalidate_original_handoff(authorization, handoff)
        return {'candidate': candidate, 'source_lineage': lineage}

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


def _original_observation_handoff(saved: PieceSavedOriginal, snapshot: dict) -> PieceSavedHandoff:
    """Bind the existing PCE-2 envelope to persisted Q2/Q3 INITIAL controls.

    A current observation row is not sufficient on its own: require its saved
    source, evaluated checkpoint and successful same-attempt finish. The
    QUESTION event owns the stored question-need decision identity. Its prompt
    and decision body never enter the handoff or Piece semantic material.
    """
    from cocolon_meaning_experience_engine.emlis_thread_contracts import SEMANTIC_SCHEMA
    from cocolon_meaning_experience_engine.natural_reply import ARTIFACT_SCHEMA, PROFILE
    from emlis_thread_service import Q3_PROFILE, _context_ref

    def require(condition):
        if not condition:
            raise _error('PIECE_SOURCE_NOT_ELIGIBLE')

    def ref(value):
        return type(value) is str and bool(value) and not any(c.isspace() for c in value)

    t, events = snapshot['thread'], snapshot['events']
    d = t['data']
    natural = d.get('response_profile') == PROFILE
    require(type(t['revision']) is int and t['revision'] > 0)
    thread_id = _uuid(t['id'], 'PIECE_SOURCE_NOT_ELIGIBLE')
    require(t['state'] in {'COMPLETED', 'AWAITING_ANSWER'})
    require(all(t[key] is None for key in (
        'active_operation_id', 'active_attempt_id', 'processing_deadline_at', 'latest_answer_event_id')))
    require(d.get('failure_code') is None and d.get('answer_assessment') == 'NOT_APPLICABLE')
    require((d.get('meaning_updated') is None or d.get('meaning_updated') is False)
            if natural else d.get('meaning_updated') is False)
    require(canonical_json_bytes(t['source_snapshot']) == saved._original_json)
    require(ref(d.get('original_source_ref')) and ref(t['source_prefix_ref']))
    require(t['evaluated_prefix_ref'] is None if natural else t['evaluated_prefix_ref'] == t['source_prefix_ref'])
    require(type(events) is list and bool(events))
    by_id, seqs = {}, []
    for event in events:
        require(type(event) is dict and event.get('thread_id') == thread_id)
        eid = _uuid(event['id'], 'PIECE_SOURCE_NOT_ELIGIBLE')
        require(eid not in by_id and type(event['seq']) is int and event['seq'] > 0)
        require(type(event['payload']) is dict)
        require(event['kind'] in {'OBSERVATION', 'QUESTION', 'MEANING_UPDATE', 'OPERATION', 'TERMINAL'})
        by_id[eid] = event
        seqs.append(event['seq'])
    require(seqs == sorted(set(seqs)))
    observation = by_id[t['last_observation_event_id']]
    require(observation['kind'] == 'OBSERVATION')
    require(sum(e['kind'] == 'OBSERVATION' for e in events) == 1)
    op = observation['payload']
    require(op.get('stage') == 'INITIAL' and observation['round_index'] == 0)
    require(op.get('source_prefix_ref') == t['source_prefix_ref'])
    if natural:
        # A recipient reply deliberately has no semantic checkpoint. Its saved
        # receipt is completion evidence only, never Piece's semantic material.
        require(d.get('runtime_profile') == Q3_PROFILE and d.get('analysis_state') == 'NOT_GENERATED')
        require(t['state'] == 'COMPLETED' and d.get('body_state') == 'FINAL')
        require(t['current_meaning_event_id'] is None and t['issued_count'] == 0)
        require(not any(e['kind'] in {'MEANING_UPDATE', 'QUESTION', 'TERMINAL'} for e in events))
        require(op.get('context_ref') == _context_ref(snapshot))
        require(op.get('context_guards') == d.get('context_guards', []))
        artifact = op.get('artifact')
        require(type(artifact) is dict and artifact.get('schema_version') == ARTIFACT_SCHEMA
            and artifact.get('analysis_state') == 'NOT_GENERATED'
            and type(op.get('text')) is str and bool(op['text'].strip())
            and artifact.get('text') == op['text'] and ref(artifact.get('model')))
        received = [e for e in events if e['kind'] == 'OPERATION'
            and e['payload'].get('stage') == 'NATURAL_REPLY_RECEIVED'
            and e['payload'].get('source_prefix_ref') == t['source_prefix_ref']
            and e['payload'].get('context_ref') == op['context_ref']
            and e['seq'] < observation['seq']]
        require(len(received) == 1)
        receipt = received[0]
        require(receipt['operation_id'] == observation['operation_id'])
        require(receipt['payload'].get('reply') == {'text': op['text'], 'model': artifact['model'],
            'source_prefix_ref': t['source_prefix_ref'], 'schema_version': ARTIFACT_SCHEMA})
        starts = [e for e in events if e['kind'] == 'OPERATION'
            and e['payload'].get('stage') == 'NATURAL_REPLY_CALL_STARTED'
            and e['operation_id'] == receipt['operation_id'] and e['attempt_id'] == receipt['attempt_id']
            and e['payload'].get('source_prefix_ref') == t['source_prefix_ref']
            and e['payload'].get('context_ref') == op['context_ref'] and e['seq'] < receipt['seq']]
        require(len(starts) == 1)
    else:
        checkpoint = by_id[t['current_meaning_event_id']]
        cp = checkpoint['payload']
        require(checkpoint['kind'] == 'MEANING_UPDATE')
        require(cp.get('semantic_schema_version') == SEMANTIC_SCHEMA and cp.get('answer_update') is None)
        require(ref(cp.get('checkpoint_id')) and op.get('meaning_checkpoint_ref') == cp['checkpoint_id'])
        require(cp.get('source_prefix_ref') == t['source_prefix_ref'])
        require(checkpoint['seq'] < observation['seq'])
    stamp = parse_iso_utc(observation['recorded_at'])
    require(stamp is not None and parse_iso_utc(saved.recorded_at) <= stamp <= parse_iso_utc(snapshot['now']))
    for key in ('operation_id', 'attempt_id'):
        _uuid(observation[key], 'PIECE_SOURCE_NOT_ELIGIBLE')
        require(observation[key] == d.get(key))
    # A retry may reuse an earlier checkpoint; only the emitted observation and
    # its successful finish must share the current attempt.
    finishes = [e for e in events if e['kind'] == 'OPERATION'
        and e['operation_id'] == observation['operation_id']
        and e['attempt_id'] == observation['attempt_id']
        and e['seq'] > observation['seq']
        and e['payload'].get('status') in {'COMPLETED', 'AWAITING_ANSWER'}
        and e['payload'].get('failure_code') is None]
    require(len(finishes) == 1)
    questions = [e for e in events if e['kind'] == 'QUESTION']
    require(type(t['issued_count']) is int and t['issued_count'] == len(questions))
    question_identity = None
    if questions:
        require(len(questions) == 1 and d['body_state'] in {'PRE_QUESTION', 'FINAL'})
        q = questions[0]
        p = q['payload']
        require(q['round_index'] == 1 and ref(q['question_id']))
        require(p.get('question_id') == q['question_id'] and p.get('thread_id') == thread_id)
        require(p.get('original_source_ref') == d['original_source_ref'])
        require(p.get('schema_version') == 'cocolon.cmee.emlis_clarification.v1')
        require(type(p.get('decision')) is dict and p['decision'].get('disposition') == 'ASK')
        require(all(q[key] == observation[key] for key in ('operation_id', 'attempt_id')))
        require(observation['seq'] < q['seq'] < finishes[0]['seq'])
        require(finishes[0]['payload']['status'] == 'AWAITING_ANSWER')
        if t['state'] == 'COMPLETED':
            terminal = [e for e in events if e['kind'] == 'TERMINAL'
                and e['seq'] > finishes[0]['seq'] and e['payload'].get('reason') in {'skip', 'stop'}]
            require(len(terminal) == 1 and d['body_state'] == 'FINAL')
        else:
            require(d['body_state'] == 'PRE_QUESTION')
        stage, question_identity = 'pre_question_observation', q['id']
    else:
        require(t['state'] == 'COMPLETED' and d['body_state'] == 'FINAL')
        require(finishes[0]['payload']['status'] == 'COMPLETED')
        stage = 'normal_observation'
    lineage = {
        'handoff_contract_version': 'cocolon.cross_core.source_handoff.v1',
        'piece_source_lineage_version': 'piece.source_lineage.v1',
        'source_input': {
            'source_input_id': saved.saved_input_id,
            'source_input_version': saved.source_input_version,
            'source_input_bundle_commitment': saved.input_bundle_commitment,
            'source_owner_user_id': saved.authenticated_owner_id,
            'source_recorded_at': parse_iso_utc(saved.recorded_at).isoformat()},
        'observation': {
            'emlis_observation_stage': stage,
            'emlis_observation_result_identity': observation['id'],
            'emlis_observation_result_state': 'terminal_success',
            'question_need_decision_identity': question_identity,
            'supplemental_answer_identity': None,
            'supplemental_answer_version': None,
            'supplemental_answer_bundle_commitment': None},
        'semantic_source_roles': ['original_input'],
        'lineage_control_roles': ['emlis_observation_result'] + (
            ['question_need_decision'] if question_identity else []),
        'piece_generation_eligibility': {
            'contract_version': 'piece.generation_eligibility.v1',
            'decision': 'eligible', 'reason_codes': []},
        'body_free': True}
    return PieceSavedHandoff(saved, thread_id, t['revision'], canonical_json_bytes(lineage))


def _natural_refined_observation_handoff(saved: PieceSavedOriginal, snapshot: dict,
                                         answer_id: str) -> PieceSavedRefinedHandoff:
    """Bind one current natural answer to real sources and saved reply receipts.

    Reply text proves completion only. The original and frozen ANSWER remain
    the only Piece meaning sources; no synthetic checkpoint is put on an OBS.
    """
    if snapshot['thread']['issued_count'] in (2, 3):
        return _natural_later_add_handoff(saved, snapshot, answer_id)
    from dataclasses import replace
    from emlis_thread_service import (
        _context_ref, _json, _request, NATURAL_QUESTION_POLICY,
        NATURAL_REPLY_PROFILE, Q3_PROFILE,
    )
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning
    from cocolon_meaning_experience_engine.emlis_thread_contracts import SEMANTIC_SCHEMA
    from cocolon_meaning_experience_engine.emlis_thread_source import admit_emlis_thread
    from cocolon_meaning_experience_engine.natural_reply import ARTIFACT_SCHEMA

    def require(value):
        if not value:
            raise _error('PIECE_SOURCE_NOT_ELIGIBLE')

    t, events = snapshot['thread'], snapshot['events']
    d = t['data']
    thread_id = _uuid(t['id'], 'PIECE_SOURCE_NOT_ELIGIBLE')
    require(type(t['revision']) is int and t['revision'] > 0)
    require(d.get('runtime_profile') == Q3_PROFILE
            and d.get('response_profile') == NATURAL_REPLY_PROFILE
            and d.get('natural_question_policy') == NATURAL_QUESTION_POLICY
            and d.get('semantic_profile') is None and d.get('analysis_state') == 'NOT_GENERATED')
    require(t['state'] == 'COMPLETED' and d.get('body_state') == 'REFINED'
            and d.get('answer_assessment') == 'RESOLVED' and d.get('meaning_updated') is True
            and d.get('failure_code') is None and d.get('natural_response_stage') == 'REFINED')
    require(all(t[k] is None for k in ('active_operation_id', 'active_attempt_id', 'processing_deadline_at')))
    require(canonical_json_bytes(t['source_snapshot']) == saved._original_json)
    require(t['latest_answer_event_id'] == answer_id
            and type(t['issued_count']) is int and t['issued_count'] == 1)
    require(type(events) is list and bool(events))
    by_id, seqs = {}, []
    for event in events:
        require(type(event) is dict and event.get('thread_id') == thread_id)
        eid = _uuid(event['id'], 'PIECE_SOURCE_NOT_ELIGIBLE')
        require(eid not in by_id and type(event['seq']) is int and event['seq'] > 0)
        require(type(event['payload']) is dict and event['kind'] in {
            'OPERATION', 'MEANING_UPDATE', 'OBSERVATION', 'QUESTION', 'ANSWER', 'TERMINAL'})
        require(not (event['kind'] == 'OPERATION'
            and event['payload'].get('stage') == 'INTERPRETATION_CORRECTION'))
        by_id[eid] = event
        seqs.append(event['seq'])
    require(seqs == sorted(set(seqs)))
    answers = [e for e in events if e['kind'] == 'ANSWER']
    questions = [e for e in events if e['kind'] == 'QUESTION']
    observations = [e for e in events if e['kind'] == 'OBSERVATION']
    checkpoints = [e for e in events if e['kind'] == 'MEANING_UPDATE']
    terminals = [e for e in events if e['kind'] == 'TERMINAL']
    require(len(answers) == len(questions) == len(checkpoints) == 1 and len(observations) == 2)
    answer, question, checkpoint = answers[0], questions[0], checkpoints[0]
    initial, observation = observations
    require(answer['id'] == answer_id
            and type(answer['round_index']) is int and type(question['round_index']) is int
            and answer['round_index'] == question['round_index'] == 1)
    require(type(initial['round_index']) is int and initial['round_index'] == 0
            and initial['payload'].get('stage') == 'INITIAL'
            and type(observation['round_index']) is int and observation['round_index'] == 1
            and observation['payload'].get('stage') == 'REFINED')
    require(t['current_meaning_event_id'] == checkpoint['id']
            and t['last_observation_event_id'] == observation['id'])
    request = _request(snapshot)
    admitted = admit_emlis_thread(request)
    require(len(admitted.answers) == 1)
    frozen = admitted.answers[0]
    require(frozen.source.answer_id == answer_id
            and frozen.source.question_id == answer['question_id'] == question['question_id'])
    require(t['source_prefix_ref'] == t['evaluated_prefix_ref'] == admitted.source_prefix_ref)
    qp = question['payload']
    require(qp.get('schema_version') == 'cocolon.cmee.emlis_clarification.v1'
            and qp.get('thread_id') == thread_id and qp.get('question_id') == question['question_id']
            and qp.get('original_source_ref') == d.get('original_source_ref')
            and type(qp.get('decision')) is dict and qp['decision'].get('disposition') == 'ASK')
    original_request = replace(request, emlis_thread=replace(request.emlis_thread, answers=(), current_round=0))
    original_prefix = admit_emlis_thread(original_request).source_prefix_ref
    require(initial['payload'].get('source_prefix_ref') == original_prefix
            and original_prefix != admitted.source_prefix_ref)
    require(all(question[key] == initial[key] for key in ('operation_id', 'attempt_id')))
    cp, op = checkpoint['payload'], observation['payload']
    require(cp.get('semantic_schema_version') == SEMANTIC_SCHEMA
            and cp.get('source_prefix_ref') == admitted.source_prefix_ref
            and cp.get('assessment_status') == 'RESOLVED' and cp.get('unresolved_parts') == [])
    update = cp.get('answer_update')
    require(type(update) is dict and update.get('disposition') == 'MATERIAL_UPDATE'
            and update.get('answer_source_ref') == frozen.envelope.envelope_id
            and update.get('question_ref') == frozen.source.question_id
            and type(update.get('updates')) is list and bool(update['updates'])
            and update.get('unresolved_parts') == [])
    # Re-derive the existing semantic owner's checkpoint from the saved real
    # original/QUESTION/ANSWER/history. This is CPU admission, never authoring.
    prepared = prepare_emlis_meaning(_request(snapshot, checkpoint_ref=cp['checkpoint_id']))
    require(_json(prepared.checkpoint) == cp)
    operation, original_ranges, answer_range = 'ADD', (), None
    if all(type(item) is dict and item.get('operation') == 'ADD'
            and item.get('superseded_claim_refs') == []
            and item.get('affected_dependency_refs') == [] for item in update['updates']):
        pass
    else:
        operation, original_ranges, answer_range = _natural_active_answer_ranges(saved, prepared)
    require(op.get('source_prefix_ref') == admitted.source_prefix_ref
            and op.get('context_ref') == _context_ref(snapshot)
            and op.get('context_guards') == d.get('context_guards', []))
    require(all(answer[key] == checkpoint[key] == observation[key] == d.get(key)
                for key in ('operation_id', 'attempt_id')))
    require(initial['seq'] < question['seq'] < answer['seq'] < checkpoint['seq'] < observation['seq'])

    def receipt_chain(body, prefix, response_stage):
        payload = body['payload']
        context_ref = payload.get('context_ref')
        require(type(context_ref) is str and bool(context_ref)
                and not any(c.isspace() for c in context_ref)
                and context_ref == _context_ref(snapshot)
                and payload.get('context_guards') == d.get('context_guards', []))
        artifact = payload.get('artifact')
        require(type(artifact) is dict and artifact.get('schema_version') == ARTIFACT_SCHEMA
                and artifact.get('analysis_state') == 'NOT_GENERATED'
                and type(payload.get('text')) is str and bool(payload['text'].strip())
                and artifact.get('text') == payload['text']
                and type(artifact.get('model')) is str and bool(artifact['model'].strip()))
        for key in ('operation_id', 'attempt_id'):
            _uuid(body[key], 'PIECE_SOURCE_NOT_ELIGIBLE')
        pair = []
        for stage in ('NATURAL_REPLY_CALL_STARTED', 'NATURAL_REPLY_RECEIVED'):
            matches = [e for e in events if e['kind'] == 'OPERATION'
                and e['payload'].get('stage') == stage
                and e['payload'].get('source_prefix_ref') == prefix]
            require(len(matches) == 1)
            event = matches[0]
            require(all(event[key] == body[key] for key in ('operation_id', 'attempt_id'))
                    and event['round_index'] == body['round_index']
                    and event['payload'].get('context_ref') == context_ref
                    and event['payload'].get('response_stage') == response_stage)
            pair.append(event)
        started, received = pair
        require(started['seq'] < received['seq'] < body['seq'])
        require(received['payload'].get('reply') == {
            'text': payload['text'], 'model': artifact['model'],
            'source_prefix_ref': prefix, 'schema_version': ARTIFACT_SCHEMA})
        return started, received

    initial_started, initial_received = receipt_chain(initial, original_prefix, 'PRE_QUESTION')
    started, received = receipt_chain(observation, admitted.source_prefix_ref, 'REFINED')
    require(checkpoint['seq'] < started['seq'])
    # Reject hidden extra calls/corrections, rather than picking a convenient
    # matching receipt from a broader or subsequently changed conversation.
    require(sum(e['kind'] == 'OPERATION' and e['payload'].get('stage') in {
        'NATURAL_REPLY_CALL_STARTED', 'NATURAL_REPLY_RECEIVED'} for e in events) == 4)
    initial_finishes = [e for e in events if e['kind'] == 'OPERATION'
        and all(e[key] == initial[key] for key in ('operation_id', 'attempt_id'))
        and e['payload'].get('status') == 'AWAITING_ANSWER'
        and e['payload'].get('failure_code') is None]
    require(len(initial_finishes) == 1)
    initial_finish = initial_finishes[0]
    require(question['seq'] < initial_finish['seq'] < answer['seq'])
    stopped = d.get('natural_question_stop') == 'stop'
    require('continuation_question' not in d)
    if stopped:
        require(len(terminals) == 1)
        terminal = terminals[0]
        require(terminal['payload'].get('reason') == 'stop'
                and type(terminal['round_index']) is int and terminal['round_index'] == 1
                and terminal['operation_id'] is None and terminal['attempt_id'] is None)
        status = 'AWAITING_CONTINUE'
    else:
        require(d.get('natural_question_stop') is None and not terminals)
        terminal, status = None, 'COMPLETED'
    finishes = [e for e in events if e['kind'] == 'OPERATION'
        and all(e[key] == observation[key] for key in ('operation_id', 'attempt_id'))
        and e['payload'].get('status') in {'COMPLETED', 'AWAITING_CONTINUE'}
        and e['payload'].get('failure_code') is None]
    require(len(finishes) == 1)
    finish = finishes[0]
    require(finish['payload'].get('status') == status and observation['seq'] < finish['seq'])
    if terminal is not None:
        require(finish['seq'] < terminal['seq'] == events[-1]['seq'])
    else:
        require(finish['seq'] == events[-1]['seq'])
    # Source/context references on the retained OBS and receipts were checked
    # against the same current snapshot above, including the stop-reuse arm.
    chain = [initial_started, initial_received, initial, question, initial_finish,
             answer, checkpoint, started, received, observation, finish]
    if terminal is not None:
        chain.append(terminal)
    stamps = [parse_iso_utc(saved.recorded_at)]
    stamps.extend(parse_iso_utc(e['recorded_at']) for e in chain)
    stamps.append(parse_iso_utc(snapshot['now']))
    require(all(stamp is not None for stamp in stamps)
            and all(a <= b for a, b in zip(stamps, stamps[1:])))
    answer_stamp = parse_iso_utc(frozen.source.recorded_at)
    require(answer_stamp is not None
            and parse_iso_utc(initial_finish['recorded_at']) <= answer_stamp
            <= parse_iso_utc(answer['recorded_at']))
    answer_commitment = 'sha256:' + frozen.envelope.raw_sha256
    require(saved.record_commitment != answer_commitment and saved.saved_input_id != answer_id)
    lineage = {
        'handoff_contract_version': 'cocolon.cross_core.source_handoff.v1',
        'piece_source_lineage_version': 'piece.source_lineage.v1',
        'source_input': {
            'source_input_id': saved.saved_input_id,
            'source_input_version': saved.source_input_version,
            'source_input_bundle_commitment': saved.input_bundle_commitment,
            'source_input_record_commitment': saved.record_commitment,
            'source_owner_user_id': saved.authenticated_owner_id,
            'source_recorded_at': parse_iso_utc(saved.recorded_at).isoformat()},
        'observation': {
            'emlis_observation_stage': 'refined_observation',
            'emlis_observation_result_identity': observation['id'],
            'emlis_observation_result_state': 'terminal_success',
            'question_need_decision_identity': question['id'],
            'supplemental_answer_identity': answer_id,
            'supplemental_answer_version': frozen.source.source_version,
            'supplemental_answer_bundle_commitment': answer_commitment,
            'source_prefix_ref': admitted.source_prefix_ref},
        'semantic_source_roles': ['original_input', 'supplemental_answer'],
        'lineage_control_roles': ['emlis_observation_result', 'question_need_decision'],
        'refined_result_source_binding': {
            'emlis_observation_result_identity': observation['id'],
            'original_record_commitment': saved.record_commitment,
            'supplemental_answer_bundle_commitment': answer_commitment},
        'piece_generation_eligibility': {
            'contract_version': 'piece.generation_eligibility.v1',
            'decision': 'eligible', 'reason_codes': []},
        'body_free': True}
    return PieceSavedRefinedHandoff(saved, frozen.source, thread_id, t['revision'],
        canonical_json_bytes(lineage), operation, original_ranges, answer_range,
        canonical_json_bytes(cp) if operation != 'ADD' else None)


def _natural_active_answer_ranges(saved, prepared):
    """Project one shared-owner exact clause update, without changing sources.

    A partial semantic projection, an explicit relation crossing the removed
    clause, or normalization that loses raw coordinates is not this capability.
    The Piece owner still rederives its complete active graph from these ranges.
    """
    from cocolon_meaning_experience_engine.emlis_answer_update import _REPLACEMENT, _WITHDRAWAL

    def require(value):
        if not value:
            raise _error('PIECE_SOURCE_NOT_ELIGIBLE')

    cp, original = prepared.checkpoint, prepared.original_plan
    updates = cp.answer_update.updates
    require(len(updates) == 1)
    update = updates[0]
    require(update.operation in {'REVISE', 'WITHDRAW'}
        and update.binding_kind == 'EXPLICIT_CORRECTION'
        and update.temporal_binding.about_time == 'ORIGINAL_OCCASION'
        and len(update.target_meaning_refs) == 1
        and update.superseded_claim_refs == update.target_meaning_refs
        and set(cp.inactive_claim_refs) == {
            *update.superseded_claim_refs, *update.affected_dependency_refs})
    answer_text = prepared.thread.answers[0].source.answer_text_private
    correction = (_REPLACEMENT if update.operation == 'REVISE' else _WITHDRAWAL).fullmatch(
        answer_text.strip().rstrip('。．.'))
    require(correction is not None)
    targets = tuple(n for n in original.nuclei if n.nucleus_id in update.target_meaning_refs)
    require(len(targets) == 1)
    target = targets[0]
    require(target.semantic_frame.actor == 'current_user'
        and len(target.source_fields) == len(target.source_span_ids) == 1
        and target.source_fields[0] in {'memo', 'memo_action'})
    span_id = target.source_span_ids[0]
    require(tuple(n.nucleus_id for n in original.nuclei if span_id in n.source_span_ids)
            == update.target_meaning_refs)
    dependencies = tuple(r for r in original.relations
                         if r.relation_id in update.affected_dependency_refs)
    require(len(dependencies) == len(update.affected_dependency_refs)
        and all(r.grounding_kind == 'bounded_structural_inference' for r in dependencies))
    resolver = prepared.thread.resolver()
    target_ref = resolver.qualified_ref(span_id).evidence
    original_source = prepared.thread.original.envelope.envelope_id
    require(target_ref.source_envelope_id == original_source
        and update.temporal_binding.anchor_source_ref == original_source
        and not update.temporal_binding.time_expression_evidence_refs)
    require(resolver.resolve(span_id).raw_text.rstrip('。．.')
            == correction.group('old').rstrip('。．.'))
    raw = saved.original_payload()
    ranges = []
    for field_path in ('memo', 'memo_action'):
        text = raw[field_path] or ''
        spans = [resolver.resolve(sid) for sid in resolver.span_ids
                 if resolver.qualified_ref(sid).source_envelope_id == original_source
                 and resolver.qualified_ref(sid).evidence.field_path == field_path]
        spans.sort(key=lambda s: s.start_index)
        cursor = 0
        for span in spans:
            start, end = span.start_index, span.end_index
            require(0 <= cursor <= start < end <= len(text)
                and not text[cursor:start].strip()
                and text[start:end] == span.raw_text)
            # Include only punctuation that is physically present in this
            # field; never manufacture a sentence boundary in saved evidence.
            if end < len(text) and text[end] in '。．.!！?？':
                end += 1
            if span.span_id != span_id:
                ranges.append((field_path, start, end))
            cursor = end
        require(not text[cursor:].strip())
    require(bool(ranges))
    answer_range = None
    if update.operation == 'WITHDRAW':
        require(not prepared.accepted_nuclei and not update.changed_claim_refs)
    else:
        require(len(prepared.accepted_nuclei) == 1)
        accepted = prepared.accepted_nuclei[0]
        require(update.changed_claim_refs == (accepted.nucleus_id,)
            and accepted.semantic_frame.actor == 'current_user'
            and accepted.source_fields == ('answer_text_private',)
            and len(accepted.source_span_ids) == 1)
        markers = tuple(c for c in accepted.semantic_frame.attribute_codes
                        if c.startswith('source_fragment_scalar_range:'))
        require(len(markers) == 1)
        try:
            a, b = map(int, markers[0].split(':')[1:])
        except (ValueError, TypeError):
            raise _error('PIECE_SOURCE_NOT_ELIGIBLE') from None
        span = resolver.resolve(accepted.source_span_ids[0])
        ref = resolver.qualified_ref(accepted.source_span_ids[0]).evidence
        text = prepared.thread.answers[0].source.answer_text_private
        require(ref.source_envelope_id == prepared.thread.answers[0].envelope.envelope_id
            and re.sub(r'\s+', ' ', span.raw_text.replace('\u3000', ' ')).strip() == span.raw_text
            and 0 <= a < b <= len(span.raw_text)
            and text[span.start_index:span.end_index] == span.raw_text)
        answer_range = (span.start_index + a, span.start_index + b)
        require(text[answer_range[0]:answer_range[1]] == correction.group('new'))
    return update.operation, tuple(ranges), answer_range


def _natural_later_add_handoff(saved, snapshot, answer_id):
    """Select the last independent ADD, after validating every real round.

    Earlier answers prove eligibility only. They never become extra Piece
    partitions and cannot silently revise the retained original input.
    """
    from dataclasses import replace
    from emlis_thread_service import (_context_ref, _json, _request,
        NATURAL_QUESTION_POLICY, NATURAL_REPLY_PROFILE, Q3_PROFILE)
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning
    from cocolon_meaning_experience_engine.emlis_thread_contracts import SEMANTIC_SCHEMA
    from cocolon_meaning_experience_engine.emlis_thread_source import admit_emlis_thread
    from cocolon_meaning_experience_engine.natural_reply import ARTIFACT_SCHEMA

    def require(value):
        if not value:
            raise _error('PIECE_SOURCE_NOT_ELIGIBLE')

    t, events = snapshot['thread'], snapshot['events']
    d, n = t['data'], t['issued_count']
    tid = _uuid(t['id'], 'PIECE_SOURCE_NOT_ELIGIBLE')
    require(type(n) is int and n in (2, 3) and type(t['revision']) is int and t['revision'] > 0)
    require(t['state']=='COMPLETED' and d.get('body_state')=='REFINED'
        and d.get('runtime_profile')==Q3_PROFILE and d.get('response_profile')==NATURAL_REPLY_PROFILE
        and d.get('natural_question_policy')==NATURAL_QUESTION_POLICY
        and d.get('semantic_profile') is None and d.get('analysis_state')=='NOT_GENERATED'
        and d.get('answer_assessment')=='RESOLVED' and d.get('meaning_updated') is True
        and d.get('natural_response_stage')=='REFINED' and d.get('failure_code') is None
        and 'continuation_question' not in d)
    require(all(t[k] is None for k in ('active_operation_id','active_attempt_id','processing_deadline_at')))
    require(canonical_json_bytes(t['source_snapshot'])==saved._original_json
        and t['latest_answer_event_id']==answer_id and type(events) is list and bool(events))
    ids, seqs = set(), []
    for event in events:
        eid = _uuid(event['id'],'PIECE_SOURCE_NOT_ELIGIBLE')
        require(event.get('thread_id')==tid and eid not in ids
            and type(event['seq']) is int and event['seq']>0 and type(event['payload']) is dict
            and event['kind'] in {'OPERATION','MEANING_UPDATE','OBSERVATION','QUESTION','ANSWER','TERMINAL'}
            and not (event['kind']=='OPERATION' and event['payload'].get('stage')=='INTERPRETATION_CORRECTION'))
        ids.add(eid); seqs.append(event['seq'])
    require(seqs==sorted(set(seqs)))
    by_kind = {kind:[e for e in events if e['kind']==kind]
        for kind in ('QUESTION','ANSWER','MEANING_UPDATE','OBSERVATION','TERMINAL','OPERATION')}
    qs, answers, cps, bodies = (by_kind[k] for k in ('QUESTION','ANSWER','MEANING_UPDATE','OBSERVATION'))
    require(len(qs)==len(answers)==len(cps)==n and len(bodies)==n+1)
    require([e['round_index'] for e in qs]==[e['round_index'] for e in answers]
        ==[e['round_index'] for e in cps]==list(range(1,n+1))
        and [e['round_index'] for e in bodies]==list(range(n+1)))
    require(answers[-1]['id']==answer_id and cps[-1]['id']==t['current_meaning_event_id']
        and bodies[-1]['id']==t['last_observation_event_id'])
    request = _request(snapshot)
    admitted = admit_emlis_thread(request)
    require(len(admitted.answers)==n and t['source_prefix_ref']==t['evaluated_prefix_ref']==admitted.source_prefix_ref)
    controls = by_kind['OPERATION']
    require(sum(e['payload'].get('stage') in {'NATURAL_REPLY_CALL_STARTED','NATURAL_REPLY_RECEIVED'}
        for e in controls)==2*(n+1))
    context_ref = _context_ref(snapshot)

    def receipt(body, prefix, stage):
        payload = body['payload']; artifact = payload.get('artifact')
        require(payload.get('source_prefix_ref')==prefix and payload.get('context_ref')==context_ref
            and payload.get('context_guards')==d.get('context_guards', [])
            and payload.get('stage')==('INITIAL' if stage=='PRE_QUESTION' else 'REFINED')
            and 'meaning_checkpoint_ref' not in payload
            and type(artifact) is dict and artifact.get('schema_version')==ARTIFACT_SCHEMA
            and artifact.get('analysis_state')=='NOT_GENERATED'
            and type(payload.get('text')) is str and bool(payload['text'].strip())
            and artifact.get('text')==payload['text']
            and type(artifact.get('model')) is str and bool(artifact['model'].strip()))
        for k in ('operation_id','attempt_id'):
            _uuid(body[k],'PIECE_SOURCE_NOT_ELIGIBLE')
        pair=[]
        for name in ('NATURAL_REPLY_CALL_STARTED','NATURAL_REPLY_RECEIVED'):
            matches=[e for e in controls if e['payload'].get('stage')==name
                and e['payload'].get('source_prefix_ref')==prefix]
            require(len(matches)==1); e=matches[0]
            require(all(e[k]==body[k] for k in ('operation_id','attempt_id','round_index'))
                and e['payload'].get('context_ref')==context_ref and e['payload'].get('response_stage')==stage)
            pair.append(e)
        started, received=pair
        require(started['seq']<received['seq']<body['seq']
            and received['payload'].get('reply')==dict(text=payload['text'],model=artifact['model'],
                source_prefix_ref=prefix,schema_version=ARTIFACT_SCHEMA))
        return started

    original_request=replace(request,emlis_thread=replace(request.emlis_thread,answers=(),current_round=0))
    original_prefix=admit_emlis_thread(original_request).source_prefix_ref
    receipt(bodies[0],original_prefix,'PRE_QUESTION')
    initial_finishes=[e for e in controls if all(e[k]==bodies[0][k] for k in ('operation_id','attempt_id'))
        and e['payload'].get('status')=='AWAITING_ANSWER' and e['payload'].get('failure_code') is None]
    require(len(initial_finishes)==1)
    previous_finish=initial_finishes[0]
    require(bodies[0]['seq']<qs[0]['seq']<previous_finish['seq']<answers[0]['seq']
        and all(qs[0][k]==bodies[0][k] for k in ('operation_id','attempt_id')))
    continued=[e for e in controls if e['payload'].get('status')=='CONTINUED']
    require(len(continued)==n-1)
    for i,(q,a,cp,body,frozen) in enumerate(zip(qs,answers,cps,bodies[1:],admitted.answers),1):
        qp=q['payload']; payload=cp['payload']
        require(frozen.source.answer_id==a['id'] and frozen.source.question_id==a['question_id']==q['question_id']
            and qp.get('schema_version')=='cocolon.cmee.emlis_clarification.v1'
            and qp.get('question_id')==q['question_id'] and qp.get('thread_id')==tid
            and qp.get('original_source_ref')==d['original_source_ref']
            and type(qp.get('decision')) is dict and qp['decision'].get('disposition')=='ASK')
        if i>1:
            c=continued[i-2]
            require(previous_finish['payload'].get('status')=='AWAITING_CONTINUE'
                and previous_finish['seq']<q['seq']<c['seq']<a['seq'] and c['round_index']==i
                and all(q[k] is None and c[k] is None for k in ('operation_id','attempt_id')))
        answer_opened = previous_finish if i == 1 else c
        ctrl=request.emlis_thread.question_control_context
        prefix_request=replace(request,emlis_thread=replace(request.emlis_thread,
            answers=request.emlis_thread.answers[:i],current_round=i,
            prepared_meaning_checkpoint_ref=payload.get('checkpoint_id'),
            question_control_context=replace(ctrl,pending_question=ctrl.issued_questions[i-1],
                asked_target_refs=ctrl.asked_target_refs[:i],issued_count=i,issued_questions=ctrl.issued_questions[:i])))
        prefix=admit_emlis_thread(prefix_request).source_prefix_ref
        prepared=prepare_emlis_meaning(prefix_request)
        require(_json(prepared.checkpoint)==payload and payload.get('semantic_schema_version')==SEMANTIC_SCHEMA
            and payload.get('source_prefix_ref')==prefix and payload.get('assessment_status')=='RESOLVED'
            and payload.get('unresolved_parts')==[])
        update=payload.get('answer_update')
        require(type(update) is dict and update.get('disposition')=='MATERIAL_UPDATE'
            and update.get('answer_source_ref')==frozen.envelope.envelope_id
            and update.get('question_ref')==q['question_id'] and update.get('unresolved_parts')==[]
            and type(update.get('updates')) is list and bool(update['updates'])
            and all(type(x) is dict and x.get('operation')=='ADD' and x.get('superseded_claim_refs')==[]
                and x.get('affected_dependency_refs')==[] for x in update['updates']))
        require(all(a[k]==cp[k]==body[k] for k in ('operation_id','attempt_id'))
            and q['seq']<a['seq']<cp['seq']<body['seq'])
        started=receipt(body,prefix,'REFINED'); require(cp['seq']<started['seq'])
        finishes=[e for e in controls if all(e[k]==body[k] for k in ('operation_id','attempt_id'))
            and e['payload'].get('status') in {'COMPLETED','AWAITING_CONTINUE'}
            and e['payload'].get('failure_code') is None]
        require(len(finishes)==1); previous_finish=finishes[0]
        require(body['seq']<previous_finish['seq'] and previous_finish['round_index']==i
            and parse_iso_utc(answer_opened['recorded_at'])<=parse_iso_utc(frozen.source.recorded_at)
            <=parse_iso_utc(a['recorded_at']))
    require(all(bodies[-1][k]==d.get(k) for k in ('operation_id','attempt_id')))
    terminals=by_kind['TERMINAL']
    if d.get('natural_question_stop')=='stop':
        require(len(terminals)==1); terminal=terminals[0]
        require(previous_finish['payload']['status']=='AWAITING_CONTINUE'
            and terminal['payload'].get('reason')=='stop' and terminal['round_index']==n
            and all(terminal[k] is None for k in ('operation_id','attempt_id'))
            and previous_finish['seq']<terminal['seq']==events[-1]['seq'])
    else:
        require(d.get('natural_question_stop') is None and not terminals
            and previous_finish['payload']['status']=='COMPLETED' and previous_finish['seq']==events[-1]['seq'])
    stamps=[parse_iso_utc(saved.recorded_at),*[parse_iso_utc(e['recorded_at']) for e in events],parse_iso_utc(snapshot['now'])]
    require(all(x is not None for x in stamps) and all(a<=b for a,b in zip(stamps,stamps[1:])))
    frozen=admitted.answers[-1]; answer_commitment='sha256:'+frozen.envelope.raw_sha256
    require(saved.record_commitment!=answer_commitment and saved.saved_input_id!=answer_id)
    lineage={
        'handoff_contract_version':'cocolon.cross_core.source_handoff.v1','piece_source_lineage_version':'piece.source_lineage.v1',
        'source_input':dict(source_input_id=saved.saved_input_id,source_input_version=saved.source_input_version,
            source_input_bundle_commitment=saved.input_bundle_commitment,source_input_record_commitment=saved.record_commitment,
            source_owner_user_id=saved.authenticated_owner_id,source_recorded_at=parse_iso_utc(saved.recorded_at).isoformat()),
        'observation':dict(emlis_observation_stage='refined_observation',emlis_observation_result_identity=bodies[-1]['id'],
            emlis_observation_result_state='terminal_success',question_need_decision_identity=qs[-1]['id'],
            supplemental_answer_identity=answer_id,supplemental_answer_version=frozen.source.source_version,
            supplemental_answer_bundle_commitment=answer_commitment,source_prefix_ref=admitted.source_prefix_ref),
        'semantic_source_roles':['original_input','supplemental_answer'],
        'lineage_control_roles':['emlis_observation_result','question_need_decision'],
        'refined_result_source_binding':dict(emlis_observation_result_identity=bodies[-1]['id'],
            original_record_commitment=saved.record_commitment,supplemental_answer_bundle_commitment=answer_commitment),
        'piece_generation_eligibility':dict(contract_version='piece.generation_eligibility.v1',decision='eligible',reason_codes=[]),
        'body_free':True}
    return PieceSavedRefinedHandoff(saved,frozen.source,tid,t['revision'],canonical_json_bytes(lineage))


def _refined_observation_handoff(saved: PieceSavedOriginal, snapshot: dict,
                                 answer_id: str) -> PieceSavedRefinedHandoff:
    """Validate current saved control without reading generated prose as source."""
    from emlis_thread_service import NATURAL_REPLY_PROFILE
    profile = snapshot['thread']['data'].get('response_profile')
    if profile == NATURAL_REPLY_PROFILE:
        return _natural_refined_observation_handoff(saved, snapshot, answer_id)
    if profile is not None:
        raise _error('PIECE_SOURCE_NOT_ELIGIBLE')
    from dataclasses import replace
    from emlis_thread_service import _request, NATURAL_REPLY_PROFILE
    from cocolon_meaning_experience_engine.emlis_thread_contracts import SEMANTIC_SCHEMA
    from cocolon_meaning_experience_engine.emlis_thread_source import admit_emlis_thread

    def require(value):
        if not value:
            raise _error('PIECE_SOURCE_NOT_ELIGIBLE')

    t, events = snapshot['thread'], snapshot['events']
    d = t['data']
    thread_id = _uuid(t['id'], 'PIECE_SOURCE_NOT_ELIGIBLE')
    require(type(t['revision']) is int and t['revision'] > 0)
    require(t['state'] == 'COMPLETED' and d.get('body_state') == 'REFINED')
    require(d.get('response_profile') != NATURAL_REPLY_PROFILE and d.get('semantic_profile') is None)
    require(d.get('failure_code') is None and d.get('answer_assessment') == 'RESOLVED'
            and d.get('meaning_updated') is True)
    require(all(t[k] is None for k in ('active_operation_id', 'active_attempt_id', 'processing_deadline_at')))
    require(canonical_json_bytes(t['source_snapshot']) == saved._original_json)
    require(t['latest_answer_event_id'] == answer_id
            and type(t['issued_count']) is int and t['issued_count'] == 1)
    require(type(events) is list and bool(events))
    by_id, seqs = {}, []
    for event in events:
        require(type(event) is dict and event.get('thread_id') == thread_id)
        eid = _uuid(event['id'], 'PIECE_SOURCE_NOT_ELIGIBLE')
        require(eid not in by_id and type(event['seq']) is int and event['seq'] > 0)
        require(type(event['payload']) is dict and event['kind'] in {
            'OPERATION', 'MEANING_UPDATE', 'OBSERVATION', 'QUESTION', 'ANSWER'})
        by_id[eid] = event
        seqs.append(event['seq'])
    require(seqs == sorted(set(seqs)))
    answers = [e for e in events if e['kind'] == 'ANSWER']
    questions = [e for e in events if e['kind'] == 'QUESTION']
    require(len(answers) == len(questions) == 1)
    answer, question = answers[0], questions[0]
    require(answer['id'] == answer_id
            and type(answer['round_index']) is int and type(question['round_index']) is int
            and answer['round_index'] == question['round_index'] == 1)
    # The existing admission proves exact original / question / answer parent
    # identity, version, round and source-prefix binding without generation.
    request = _request(snapshot)
    admitted = admit_emlis_thread(request)
    require(len(admitted.answers) == 1)
    frozen = admitted.answers[0]
    require(frozen.source.answer_id == answer_id and frozen.source.question_id == answer['question_id']
            and frozen.source.question_id == question['question_id'])
    require(t['source_prefix_ref'] == t['evaluated_prefix_ref'] == admitted.source_prefix_ref)
    require(question['payload']['decision']['disposition'] == 'ASK'
            and question['payload'].get('schema_version') == 'cocolon.cmee.emlis_clarification.v1'
            and question['payload'].get('thread_id') == thread_id
            and question['payload'].get('question_id') == question['question_id'])
    observations = [e for e in events if e['kind'] == 'OBSERVATION']
    initial = [e for e in observations if e['payload'].get('stage') == 'INITIAL']
    require(len(observations) == 2 and len(initial) == 1)
    initial = initial[0]
    require(initial['round_index'] == 0 and initial['seq'] < question['seq'])
    original_request = replace(request, emlis_thread=replace(request.emlis_thread, answers=(), current_round=0))
    original_prefix = admit_emlis_thread(original_request).source_prefix_ref
    require(initial['payload'].get('source_prefix_ref') == original_prefix)
    initial_checkpoints = [e for e in events if e['kind'] == 'MEANING_UPDATE'
        and e['seq'] < initial['seq'] and e['payload'].get('semantic_schema_version') == SEMANTIC_SCHEMA
        and e['payload'].get('checkpoint_id') == initial['payload'].get('meaning_checkpoint_ref')
        and e['payload'].get('source_prefix_ref') == original_prefix
        and e['payload'].get('answer_update') is None]
    require(len(initial_checkpoints) == 1)
    require(all(question[key] == initial[key] for key in ('operation_id', 'attempt_id')))
    initial_finishes = [e for e in events if e['kind'] == 'OPERATION'
        and e['operation_id'] == initial['operation_id'] and e['attempt_id'] == initial['attempt_id']
        and question['seq'] < e['seq'] < answer['seq'] and e['payload'].get('status') == 'AWAITING_ANSWER'
        and e['payload'].get('failure_code') is None]
    require(len(initial_finishes) == 1)
    checkpoint, observation = by_id[t['current_meaning_event_id']], by_id[t['last_observation_event_id']]
    cp, op = checkpoint['payload'], observation['payload']
    require(checkpoint['kind'] == 'MEANING_UPDATE' and observation['kind'] == 'OBSERVATION')
    require(cp.get('semantic_schema_version') == SEMANTIC_SCHEMA
            and cp.get('source_prefix_ref') == admitted.source_prefix_ref
            and cp.get('assessment_status') == 'RESOLVED' and cp.get('unresolved_parts') == [])
    update = cp.get('answer_update')
    require(type(update) is dict and update.get('disposition') == 'MATERIAL_UPDATE'
            and update.get('answer_source_ref') == frozen.envelope.envelope_id
            and update.get('question_ref') == frozen.source.question_id
            and bool(update.get('updates')) and update.get('unresolved_parts') == [])
    require(type(update['updates']) is list and all(type(item) is dict
        and item.get('operation') == 'ADD' and item.get('superseded_claim_refs') == []
        and item.get('affected_dependency_refs') == [] for item in update['updates']))
    require(op.get('stage') == 'REFINED' and observation['round_index'] == 1
            and op.get('meaning_checkpoint_ref') == cp['checkpoint_id']
            and op.get('source_prefix_ref') == admitted.source_prefix_ref)
    require(question['seq'] < answer['seq'] < checkpoint['seq'] < observation['seq'])
    require(all(answer[key] == observation[key] == d.get(key) for key in ('operation_id', 'attempt_id')))
    for key in ('operation_id', 'attempt_id'):
        _uuid(observation[key], 'PIECE_SOURCE_NOT_ELIGIBLE')
    finishes = [e for e in events if e['kind'] == 'OPERATION'
        and e['operation_id'] == observation['operation_id'] and e['attempt_id'] == observation['attempt_id']
        and e['seq'] > observation['seq'] and e['payload'].get('status') == 'COMPLETED'
        and e['payload'].get('failure_code') is None]
    require(len(finishes) == 1)
    original_stamp = parse_iso_utc(saved.recorded_at)
    answer_stamp = parse_iso_utc(frozen.source.recorded_at)
    observation_stamp = parse_iso_utc(observation['recorded_at'])
    finish_stamp = parse_iso_utc(finishes[0]['recorded_at'])
    now = parse_iso_utc(snapshot['now'])
    require(all(stamp is not None for stamp in (original_stamp, answer_stamp, observation_stamp, finish_stamp, now)))
    require(original_stamp <= answer_stamp <= observation_stamp <= finish_stamp <= now)
    answer_commitment = 'sha256:' + frozen.envelope.raw_sha256
    require(saved.record_commitment != answer_commitment and saved.saved_input_id != answer_id)
    lineage = {
        'handoff_contract_version': 'cocolon.cross_core.source_handoff.v1',
        'piece_source_lineage_version': 'piece.source_lineage.v1',
        'source_input': {
            'source_input_id': saved.saved_input_id,
            'source_input_version': saved.source_input_version,
            'source_input_bundle_commitment': saved.input_bundle_commitment,
            'source_input_record_commitment': saved.record_commitment,
            'source_owner_user_id': saved.authenticated_owner_id,
            'source_recorded_at': original_stamp.isoformat()},
        'observation': {
            'emlis_observation_stage': 'refined_observation',
            'emlis_observation_result_identity': observation['id'],
            'emlis_observation_result_state': 'terminal_success',
            'question_need_decision_identity': question['id'],
            'supplemental_answer_identity': answer_id,
            'supplemental_answer_version': frozen.source.source_version,
            'supplemental_answer_bundle_commitment': answer_commitment,
            'source_prefix_ref': admitted.source_prefix_ref},
        'semantic_source_roles': ['original_input', 'supplemental_answer'],
        'lineage_control_roles': ['emlis_observation_result', 'question_need_decision'],
        'refined_result_source_binding': {
            'emlis_observation_result_identity': observation['id'],
            'original_record_commitment': saved.record_commitment,
            'supplemental_answer_bundle_commitment': answer_commitment},
        'piece_generation_eligibility': {
            'contract_version': 'piece.generation_eligibility.v1',
            'decision': 'eligible', 'reason_codes': []},
        'body_free': True}
    return PieceSavedRefinedHandoff(saved, frozen.source, thread_id, t['revision'], canonical_json_bytes(lineage))


def project_saved_refined_source(handoff: PieceSavedRefinedHandoff, *, opted_in: bool):
    """Separate-source CMEE projection; original stage paths stay exact."""
    from cocolon_meaning_experience_engine.piece_refined import PieceRefinedSourceSnapshot
    from cocolon_meaning_experience_engine.emlis_thread_source import freeze_supplemental_answer
    if type(handoff) is not PieceSavedRefinedHandoff or opted_in is not True:
        raise _error('PIECE_SOURCE_NOT_ELIGIBLE')
    try:
        line = handoff.lineage_payload()
    except (ValueError, TypeError, UnicodeError):
        raise _error('PIECE_CONFLICT') from None
    if (type(line) is not dict or set(line) != {
            'handoff_contract_version', 'piece_source_lineage_version', 'source_input',
            'observation', 'semantic_source_roles', 'lineage_control_roles',
            'refined_result_source_binding', 'piece_generation_eligibility', 'body_free'}
            or type(line.get('observation')) is not dict or set(line['observation']) != {
                'emlis_observation_stage', 'emlis_observation_result_identity',
                'emlis_observation_result_state', 'question_need_decision_identity',
                'supplemental_answer_identity', 'supplemental_answer_version',
                'supplemental_answer_bundle_commitment', 'source_prefix_ref'}):
        raise _error('PIECE_CONFLICT')
    observation = line['observation']
    answer = freeze_supplemental_answer(handoff.supplemental)
    binding = line['refined_result_source_binding']
    for key in ('emlis_observation_result_identity', 'question_need_decision_identity'):
        _uuid(observation[key], 'PIECE_CONFLICT')
    expected_original = {
        'source_input_id': handoff.original.saved_input_id,
        'source_input_version': handoff.original.source_input_version,
        'source_input_bundle_commitment': handoff.original.input_bundle_commitment,
        'source_input_record_commitment': handoff.original.record_commitment,
        'source_owner_user_id': handoff.original.authenticated_owner_id,
        'source_recorded_at': parse_iso_utc(handoff.original.recorded_at).isoformat()}
    if (line['handoff_contract_version'] != 'cocolon.cross_core.source_handoff.v1'
            or line['piece_source_lineage_version'] != 'piece.source_lineage.v1'
            or line['source_input'] != expected_original
            or line['semantic_source_roles'] != ['original_input', 'supplemental_answer']
            or line['lineage_control_roles'] != ['emlis_observation_result', 'question_need_decision']
            or line['piece_generation_eligibility'] != {
                'contract_version': 'piece.generation_eligibility.v1', 'decision': 'eligible', 'reason_codes': []}
            or line['body_free'] is not True or canonical_json_bytes(line) != handoff._lineage_json
            or observation['emlis_observation_stage'] != 'refined_observation'
            or observation['emlis_observation_result_state'] != 'terminal_success'
            or type(observation['source_prefix_ref']) is not str
            or not observation['source_prefix_ref'] or any(c.isspace() for c in observation['source_prefix_ref'])
            or type(handoff.thread_revision) is not int or handoff.thread_revision < 1
            or handoff.thread_id != handoff.supplemental.thread_id
            or observation['supplemental_answer_identity'] != handoff.supplemental.answer_id
            or observation['supplemental_answer_version'] != handoff.supplemental.source_version
            or observation['supplemental_answer_bundle_commitment'] != 'sha256:' + answer.envelope.raw_sha256
            or binding != {
                'emlis_observation_result_identity': observation['emlis_observation_result_identity'],
                'original_record_commitment': handoff.original.record_commitment,
                'supplemental_answer_bundle_commitment': observation['supplemental_answer_bundle_commitment']}):
        raise _error('PIECE_CONFLICT')
    # The original partition retains its established single-source snapshot;
    # refined stage and separate answer live only in the composite capability.
    return PieceRefinedSourceSnapshot(
        original=project_saved_original_source(handoff.original, source_stage='normal_observation'),
        supplemental=handoff.supplemental,
        supplemental_owner_id=handoff.original.authenticated_owner_id,
        supplemental_update_operation=handoff.supplemental_update_operation,
        original_active_ranges=handoff.original_active_ranges,
        supplemental_active_range=handoff.supplemental_active_range,
        question_need_decision_identity=observation['question_need_decision_identity'],
        refined_result_identity=observation['emlis_observation_result_identity'],
        original_commitment=handoff.original.record_commitment,
        supplemental_commitment=observation['supplemental_answer_bundle_commitment'], opted_in=True)


def project_saved_refined_lineage(handoff: PieceSavedRefinedHandoff, *, opted_in: bool) -> dict:
    """Project validated private control into the existing DB lineage schema.

    Exact stored input bytes, prefix and refined-result binding remain in the
    request-private handoff and its current-state fence. They are not new DB
    fields or source text. The persisted supplement commitment retains its
    independent identity under the existing supplemental boundary constraint.
    """
    project_saved_refined_source(handoff, opted_in=opted_in)
    line = handoff.lineage_payload()
    del line['source_input']['source_input_record_commitment']
    del line['observation']['source_prefix_ref']
    del line['refined_result_source_binding']
    return line


def project_saved_refined_fence(handoff) -> dict:
    """Pin an active update to its admitted checkpoint inside the existing RPC.

    This private expectation never enters source_ref, persisted lineage or the
    Piece body. Old original/ADD calls retain their exact four-key state.
    """
    if type(handoff) is PieceSavedHandoff:
        return {}
    if type(handoff) is not PieceSavedRefinedHandoff:
        raise _error('PIECE_CONFLICT')
    if handoff.supplemental_update_operation == 'ADD':
        if (handoff.original_active_ranges or handoff.supplemental_active_range is not None
                or handoff._meaning_checkpoint_json is not None):
            raise _error('PIECE_CONFLICT')
        return {}
    project_saved_refined_source(handoff, opted_in=True)
    try:
        cp = json.loads(handoff._meaning_checkpoint_json)
    except (ValueError, TypeError, UnicodeError):
        raise _error('PIECE_CONFLICT') from None
    if type(cp) is not dict:
        raise _error('PIECE_CONFLICT')
    update = cp.get('answer_update')
    if (canonical_json_bytes(cp) != handoff._meaning_checkpoint_json
            or handoff.supplemental_update_operation not in {'REVISE', 'WITHDRAW'}
            or cp.get('source_prefix_ref') != handoff.lineage_payload()['observation']['source_prefix_ref']
            or cp.get('assessment_status') != 'RESOLVED' or cp.get('unresolved_parts') != []
            or type(update) is not dict or update.get('disposition') != 'MATERIAL_UPDATE'
            or update.get('question_ref') != handoff.supplemental.question_id
            or type(update.get('updates')) is not list or len(update['updates']) != 1
            or type(update['updates'][0]) is not dict
            or update['updates'][0].get('operation') != handoff.supplemental_update_operation):
        raise _error('PIECE_CONFLICT')
    return {'meaning_checkpoint': cp}
