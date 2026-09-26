"""Disabled B5-A saved-original retrieval and original-only state handoff.

The existing bearer verifier establishes the caller. The existing
emlis_thread_read RPC selects a live emotions row for that verified caller,
under the saved-input retention policy, even when no Emlis thread exists.
Only the original partition and body-free control lineage are retained here.

All saved fields remain separate. The state-bound path admits only an already
committed, current INITIAL observation: normal or pre-question, without answers.
Refined content remains unconnected. The earlier explicit-stage method remains
an offline probe, not authority. No route, preview record or quota is enabled;
a frozen object is not ongoing access.
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


@dataclass(frozen=True, slots=True, repr=False)
class PieceSavedHandoff:
    """Private original and immutable body-free lineage, not a public DTO."""
    original: PieceSavedOriginal
    thread_id: str
    thread_revision: int
    _lineage_json: bytes = field(repr=False)

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
        from emlis_thread_service import _check, _generation_current, Q3_PROFILE
        saved, snapshot = await self._resolve_original_with_snapshot(
            authorization, saved_input_id)
        try:
            thread = _check(snapshot)
            if thread is None:
                raise _error('PIECE_SOURCE_NOT_ELIGIBLE')
            if thread['data']['runtime_profile'] == Q3_PROFILE:
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

    def require(condition):
        if not condition:
            raise _error('PIECE_SOURCE_NOT_ELIGIBLE')

    def ref(value):
        return type(value) is str and bool(value) and not any(c.isspace() for c in value)

    t, events = snapshot['thread'], snapshot['events']
    d = t['data']
    require(type(t['revision']) is int and t['revision'] > 0)
    thread_id = _uuid(t['id'], 'PIECE_SOURCE_NOT_ELIGIBLE')
    require(t['state'] in {'COMPLETED', 'AWAITING_ANSWER'})
    require(all(t[key] is None for key in (
        'active_operation_id', 'active_attempt_id', 'processing_deadline_at', 'latest_answer_event_id')))
    require(d.get('failure_code') is None and d.get('answer_assessment') == 'NOT_APPLICABLE')
    require(d.get('meaning_updated') is False)
    require(canonical_json_bytes(t['source_snapshot']) == saved._original_json)
    require(ref(d.get('original_source_ref')) and ref(t['source_prefix_ref']))
    require(t['evaluated_prefix_ref'] == t['source_prefix_ref'])
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
    checkpoint = by_id[t['current_meaning_event_id']]
    require(observation['kind'] == 'OBSERVATION' and checkpoint['kind'] == 'MEANING_UPDATE')
    require(sum(e['kind'] == 'OBSERVATION' for e in events) == 1)
    op, cp = observation['payload'], checkpoint['payload']
    require(op.get('stage') == 'INITIAL' and observation['round_index'] == 0)
    require(cp.get('semantic_schema_version') == SEMANTIC_SCHEMA and cp.get('answer_update') is None)
    require(ref(cp.get('checkpoint_id')) and op.get('meaning_checkpoint_ref') == cp['checkpoint_id'])
    require(op.get('source_prefix_ref') == cp.get('source_prefix_ref') == t['source_prefix_ref'])
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
