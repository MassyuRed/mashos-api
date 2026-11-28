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
from datetime import datetime, timezone
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
from piece_v2_contract import (
    DEEP_INSIGHT_PIECE_SOURCE_KIND, DEEP_INSIGHT_PIECE_SOURCE_VERSION,
    PieceContractError, canonical_json_bytes, canonical_sha256_hex,
)
from publish_governance import parse_iso_utc, timestamp_in_history_retention

if TYPE_CHECKING:
    from cocolon_meaning_experience_engine.cores.analysis.source_adapter import AnalysisCircumstanceControl
    from cocolon_meaning_experience_engine.emlis_answer_update import BoundFeelingCircumstance
    from cocolon_meaning_experience_engine.emlis_thread_contracts import SupplementalAnswerSource, InterpretationCorrectionSource
    from cocolon_meaning_experience_engine.piece_refined import PieceRelativeFeelingAnchor

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
    prior_revisions: tuple[tuple[SupplementalAnswerSource, tuple[int, int]], ...] = ()
    _effective_checkpoints_json: bytes | None = field(default=None, repr=False)
    feeling_question_id: str | None = None
    feeling_circumstance: BoundFeelingCircumstance | None = None
    relative_feeling_anchor: PieceRelativeFeelingAnchor | None = None

    def lineage_payload(self) -> dict:
        return json.loads(self._lineage_json)


@dataclass(frozen=True, slots=True, repr=False)
class PieceSavedCorrectedHandoff:
    """A person explanation and its original; never a synthetic ANSWER."""
    original: PieceSavedOriginal
    correction: InterpretationCorrectionSource
    thread_id: str
    thread_revision: int
    _lineage_json: bytes = field(repr=False)
    _correction_state_json: bytes = field(repr=False)
    as_of: str
    correction_update_operation: str
    original_active_ranges: tuple[tuple[str, int, int], ...]
    correction_active_range: tuple[int, int] | None

    prior_corrections: tuple[InterpretationCorrectionSource, ...] = ()
    answer_sources: tuple[SupplementalAnswerSource, ...] = ()
    circumstance_control: AnalysisCircumstanceControl | None = None

    def lineage_payload(self) -> dict:
        return json.loads(self._lineage_json)


@dataclass(frozen=True, slots=True, repr=False)
class PieceSavedDeepInsightHandoff:
    original: PieceSavedOriginal
    question_id: str
    source_commitment: str
    answer_text: str = field(repr=False)
    answered_at: str

    def lineage_payload(self) -> dict:
        saved = self.original
        return {
            'handoff_contract_version': 'cocolon.cross_core.source_handoff.v1',
            'piece_source_lineage_version': 'piece.source_lineage.v1',
            'source_kind': DEEP_INSIGHT_PIECE_SOURCE_KIND,
            'source_input': {
                'source_input_id': saved.saved_input_id,
                'source_input_version': saved.source_input_version,
                'source_input_bundle_commitment': saved.input_bundle_commitment,
                'source_owner_user_id': saved.authenticated_owner_id,
                'source_recorded_at': parse_iso_utc(saved.recorded_at).isoformat(),
            },
            'deep_insight': {
                'deep_insight_question_id': self.question_id,
                'source_version': DEEP_INSIGHT_PIECE_SOURCE_VERSION,
                'source_commitment': self.source_commitment,
            },
            'semantic_source_roles': ['original_input', 'deep_insight_answer'],
            'body_free': True,
        }


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


def _saved_original(owner: str, input_id: str, original: dict, tier: str) -> PieceSavedOriginal:
    try:
        raw = canonical_json_bytes(original)
        # Match the Emlis saved-original adapter while retaining exact raw bytes.
        bundle_source = json.loads(raw)
        bundle_source['created_at'] = parse_iso_utc(original['created_at']).isoformat()
        bundle = normalize_emlis_current_input(bundle_source)
        return PieceSavedOriginal(
            owner, input_id, EMLIS_CURRENT_INPUT_BUNDLE_SCHEMA_VERSION,
            'sha256:' + artifact_sha256(bundle), 'sha256:' + canonical_sha256_hex(original),
            original['created_at'], tier, raw, canonical_json_bytes(bundle),
        )
    except (ValueError, TypeError, UnicodeError):
        raise _error('PIECE_TEMPORARILY_UNAVAILABLE') from None


def piece_deep_insight_handoff_from_binding(owner: str, input_id: str, question_id: str,
                                           binding: object) -> PieceSavedDeepInsightHandoff:
    if binding is None:
        raise _error('PIECE_SOURCE_NOT_FOUND')
    if (type(binding) is not dict or set(binding) != {
            'source_version', 'commitment', 'subscription_tier', 'original',
            'answer_id', 'answer_text', 'answered_at', 'ai_question_context'}
            or binding['source_version'] != DEEP_INSIGHT_PIECE_SOURCE_VERSION
            or binding['subscription_tier'] != 'premium'
            or binding['answer_id'] != question_id
            or type(binding['commitment']) is not str or not _COMMITMENT.fullmatch(binding['commitment'])
            or type(binding['answer_text']) is not str or not binding['answer_text'].strip()
            or type(binding['answered_at']) is not str or parse_iso_utc(binding['answered_at']) is None):
        raise _error('PIECE_TEMPORARILY_UNAVAILABLE')
    original, tier = _original({
        'original': binding['original'], 'tier': binding['subscription_tier'],
        'now': datetime.now(timezone.utc).isoformat(),
    }, input_id)
    return PieceSavedDeepInsightHandoff(
        _saved_original(owner, input_id, original, tier), question_id,
        binding['commitment'], binding['answer_text'], binding['answered_at'],
    )


async def _verified_piece_owner(authorization: str | None) -> str:
    if authorization is not None and type(authorization) is not str:
        raise _error('PIECE_AUTH_REQUIRED')
    try:
        verified_owner = await _require_user_id(authorization)
    except HTTPException as exc:
        raise _error('PIECE_AUTH_REQUIRED' if exc.status_code in (401, 403)
                     else 'PIECE_TEMPORARILY_UNAVAILABLE') from None
    except (httpx.TransportError, httpx.TimeoutException, ValueError, TypeError, AttributeError):
        raise _error('PIECE_TEMPORARILY_UNAVAILABLE') from None
    return _uuid(verified_owner, 'PIECE_AUTH_REQUIRED')


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
        owner = await _verified_piece_owner(authorization)
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
        saved = _saved_original(owner, input_id, original, tier)
        if ((expected_record_commitment is not None and
             not hmac.compare_digest(expected_record_commitment, saved.record_commitment)) or
            (expected_input_bundle_commitment is not None and
             not hmac.compare_digest(expected_input_bundle_commitment, saved.input_bundle_commitment))):
            raise _error('PIECE_CONFLICT')
        return saved, snapshot

    async def resolve_deep_insight_handoff(
        self, authorization: str | None, saved_input_id: str, *, question_id: str,
    ) -> PieceSavedDeepInsightHandoff:
        from supabase_client import sb_post_rpc

        owner = await _verified_piece_owner(authorization)
        input_id = _uuid(saved_input_id, 'PIECE_REQUEST_INVALID')
        selected = _uuid(question_id, 'PIECE_REQUEST_INVALID')
        try:
            response = await sb_post_rpc('piece_deep_insight_source_binding', {
                'p_owner': owner, 'p_saved_input': input_id, 'p_question': selected,
                'p_expected_commitment': None,
            }, timeout=8.0)
            if response.status_code != 200:
                raise _error('PIECE_TEMPORARILY_UNAVAILABLE')
            return piece_deep_insight_handoff_from_binding(owner, input_id, selected, response.json())
        except PieceContractError:
            raise
        except (httpx.HTTPError, ValueError, TypeError, RuntimeError):
            raise _error('PIECE_TEMPORARILY_UNAVAILABLE') from None

    async def revalidate_deep_insight_handoff(self, authorization: str | None,
                                               previous: PieceSavedDeepInsightHandoff) -> PieceSavedDeepInsightHandoff:
        current = await self.resolve_deep_insight_handoff(
            authorization, previous.original.saved_input_id, question_id=previous.question_id)
        if current != previous:
            raise _error('PIECE_CONFLICT')
        return current

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
        *, include_corrected: bool = False, selected_corrected_answer: str | None = None,
    ) -> PieceSavedHandoff | PieceSavedCorrectedHandoff:
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
            if include_corrected and any(e.get('kind') == 'OPERATION'
                    and e.get('payload', {}).get('stage') == 'INTERPRETATION_CORRECTION'
                    for e in snapshot['events']):
                return _corrected_observation_handoff(saved, snapshot, selected_corrected_answer)
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

    async def resolve_corrected_handoff(self, authorization, saved_input_id, *, supplemental_answer_identity=None):
        if supplemental_answer_identity is not None:
            _uuid(supplemental_answer_identity, 'PIECE_REQUEST_INVALID')
        result = await self.resolve_original_handoff(authorization, saved_input_id, include_corrected=True,
            selected_corrected_answer=supplemental_answer_identity)
        if type(result) is not PieceSavedCorrectedHandoff:
            raise _error('PIECE_SOURCE_NOT_ELIGIBLE')
        return result

    async def revalidate_corrected_handoff(self, authorization, previous):
        if type(previous) is not PieceSavedCorrectedHandoff:
            raise _error('PIECE_REQUEST_INVALID')
        current = await self.resolve_corrected_handoff(authorization, previous.original.saved_input_id,
            supplemental_answer_identity=previous.answer_sources[-1].answer_id if previous.answer_sources else None)
        # The source clock advances on every read. It qualifies the immutable
        # sources but is not a new version of those sources.
        from dataclasses import replace
        if replace(current, as_of=previous.as_of) != previous:
            raise _error('PIECE_CONFLICT')
        return previous

    async def resolve_refined_handoff(
        self, authorization: str | None, saved_input_id: str, *,
        supplemental_answer_identity: str, opted_in: bool,
    ) -> PieceSavedRefinedHandoff | PieceSavedCorrectedHandoff:
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
            if any(e.get('kind') == 'OPERATION' and e.get('payload', {}).get('stage') == 'INTERPRETATION_CORRECTION'
                    for e in snapshot['events']):
                return _corrected_observation_handoff(saved, snapshot, answer_id)
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
        self, authorization: str | None, previous: PieceSavedRefinedHandoff | PieceSavedCorrectedHandoff, *, opted_in: bool,
    ) -> PieceSavedRefinedHandoff | PieceSavedCorrectedHandoff:
        if opted_in is not True:
            raise _error('PIECE_SOURCE_NOT_ELIGIBLE')
        if type(previous) is PieceSavedCorrectedHandoff:
            return await self.revalidate_corrected_handoff(authorization, previous)
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
            handoff = await self.resolve_original_handoff(authorization, saved_input_id, include_corrected=True)
            if type(handoff) not in (PieceSavedHandoff, PieceSavedCorrectedHandoff):
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
            current = (await self.revalidate_corrected_handoff(authorization, handoff)
                if type(handoff) is PieceSavedCorrectedHandoff else
                await self.revalidate_original_handoff(authorization, handoff))
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
            if type(handoff) is PieceSavedCorrectedHandoff:
                project_saved_corrected_source(handoff)
                lineage = handoff.lineage_payload()
            else:
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


def project_saved_deep_insight_source(handoff: PieceSavedDeepInsightHandoff):
    from cocolon_meaning_experience_engine.piece_deep_insight import PieceDeepInsightSourceSnapshot

    return PieceDeepInsightSourceSnapshot(
        project_saved_original_source(handoff.original, source_stage='normal_observation'),
        handoff.question_id, handoff.answer_text, handoff.answered_at, handoff.source_commitment,
    )


def eligible_deep_insight_history_source(owner: str, question_id: str, answer_text: str,
                                         answered_at: str, raw: object) -> str:
    from cocolon_meaning_experience_engine.piece_deep_insight import validate_deep_insight_piece_source

    if type(raw) is not dict:
        raise _error('PIECE_SOURCE_NOT_FOUND')
    input_id = _uuid(raw.get('id'), 'PIECE_SOURCE_NOT_FOUND')
    original, tier = _original({
        'original': raw, 'tier': 'premium', 'now': datetime.now(timezone.utc).isoformat(),
    }, input_id)
    # The history selector only checks grammar for this snapshot. The Piece
    # route obtains a separate locked source receipt before creating a draft.
    material_hash = 'sha256:' + canonical_sha256_hex([original, question_id, answer_text, answered_at])
    handoff = PieceSavedDeepInsightHandoff(
        _saved_original(owner, input_id, original, tier), question_id, material_hash, answer_text, answered_at,
    )
    validate_deep_insight_piece_source(project_saved_deep_insight_source(handoff))
    return input_id


def _latest_natural_analysis_state(snapshot):
    """The latest saved observation owns its Analysis state, not a constant."""
    latest = snapshot['thread'].get('last_observation_event_id')
    rows = [event for event in snapshot['events']
            if event.get('id') == latest and event.get('kind') == 'OBSERVATION']
    if len(rows) != 1:
        return 'INVALID'
    state = rows[0].get('payload', {}).get('artifact', {}).get('analysis_state')
    return state if state in {'GENERATED', 'NOT_GENERATED'} else 'INVALID'


def _natural_analysis_material_matches(saved, snapshot, body, request):
    """Admit the same source-grounded material without using reply prose.

    Old saved receipts keep their NOT_GENERATED contract. New observations may
    contain the shared private material, including a partial/unknown result;
    rederive it from this observation's exact source prefix, never from its
    generated text or from a later answer in the thread.
    """
    from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import (
        prepare_emlis_analysis_material,
    )
    artifact = body.get('payload', {}).get('artifact')
    if type(artifact) is not dict:
        return False
    material = artifact.get('analysis_material')
    profile = artifact.get('meaning_profile')
    if material is None:
        return (profile is None and artifact.get('analysis_state') == 'NOT_GENERATED')
    if (profile != 'source_grounded_active_meaning.v1' or type(material) is not dict
            or artifact.get('analysis_state') not in {'GENERATED', 'NOT_GENERATED'}
            or artifact.get('analysis_state') != material.get('state')
            or ('corrected_circumstance' in material and material['corrected_circumstance'] is not True)
            or material.get('source_prefix_ref') != body['payload'].get('source_prefix_ref')):
        return False
    try:
        instant = parse_iso_utc(material.get('as_of'))
        recorded = parse_iso_utc(body.get('recorded_at'))
        now = parse_iso_utc(snapshot.get('now'))
        if instant is None or recorded is None or now is None or not instant <= recorded <= now:
            return False
        expected = prepare_emlis_analysis_material(request,
            owner_scope=saved.authenticated_owner_id,
            original_record=saved.original_payload(), as_of=material['as_of'],
            include_corrected_circumstance=material.get('corrected_circumstance', False))
        return canonical_json_bytes(expected) == canonical_json_bytes(material)
    except (ValueError, TypeError, KeyError):
        return False


def _natural_unanswered_question(saved, snapshot, observation):
    """A bound question is control only. The latest genuine reply anchors the original."""
    from cocolon_meaning_experience_engine.emlis_thread_source import admit_emlis_thread
    from cocolon_meaning_experience_engine.natural_reply import ARTIFACT_SCHEMA
    from emlis_thread_service import NATURAL_QUESTION_POLICY, Q3_PROFILE, RETRYABLE_FAILURES, _context_ref, _request

    def require(ok):
        if not ok:
            raise _error('PIECE_SOURCE_NOT_ELIGIBLE')

    t, events = snapshot['thread'], snapshot['events']
    d = t['data']
    request = _request(snapshot)
    admitted = admit_emlis_thread(request)
    require(d.get('runtime_profile') == Q3_PROFILE and d.get('natural_question_policy') == NATURAL_QUESTION_POLICY
            and d.get('semantic_profile') is None and not admitted.answers and not admitted.control.interpretation_corrections
            and t['current_meaning_event_id'] is None
            and type(t['issued_count']) is int and t['issued_count'] == 1
            and admitted.source_prefix_ref == t['source_prefix_ref'])
    ended = t['state'] == 'COMPLETED'
    expected_stage = 'FINAL' if ended else 'PRE_QUESTION'
    require(d.get('natural_response_stage') == expected_stage and d.get('body_state') == expected_stage
            and (d.get('natural_question_stop') in ('skip', 'stop') if ended else d.get('natural_question_stop') is None)
            and d.get('analysis_state') == _latest_natural_analysis_state(snapshot))
    require(all(e['kind'] in {'OBSERVATION', 'OPERATION', 'QUESTION'} for e in events))
    qs = [e for e in events if e['kind'] == 'QUESTION']
    bodies = [e for e in events if e['kind'] == 'OBSERVATION']
    require(len(qs) == 1 and len(bodies) == (2 if ended else 1) and bodies[-1] == observation)
    q = qs[0]
    qp = q['payload']
    require(q['round_index'] == 1 and isinstance(q['question_id'], str) and bool(q['question_id'].strip())
            and qp.get('thread_id') == t['id'] and qp.get('question_id') == q['question_id']
            and qp.get('schema_version') == 'cocolon.cmee.emlis_clarification.v1'
            and qp.get('original_source_ref') == d['original_source_ref'] and qp['decision']['disposition'] == 'ASK')
    def attempt(row):
        return row['operation_id'], row['attempt_id']

    def stage_rows(stage):
        return [e for e in events if e['kind'] == 'OPERATION' and e['payload'].get('stage') == stage]

    def same_operation(earlier, later):
        if earlier['operation_id'] != later['operation_id']:
            return False
        if earlier['attempt_id'] == later['attempt_id']:
            return True
        # A saved reply may be reused after a storage failure in the same
        # operation. Keep its original attempt and verify the explicit retry.
        between = [e for e in events if e['kind'] == 'OPERATION'
                   and e['operation_id'] == later['operation_id'] and earlier['seq'] < e['seq'] < later['seq']]
        failures = [e for e in between if e['attempt_id'] == earlier['attempt_id']
                    and e['payload'].get('status') == 'RESPONSE_FAILED'
                    and e['payload'].get('failure_code') in RETRYABLE_FAILURES]
        retries = [e for e in between if e['attempt_id'] == later['attempt_id']
                   and e['payload'].get('status') == 'RUNNING' and e['payload'].get('request_fingerprint')]
        return len(failures) == len(retries) == 1 and failures[0]['seq'] < retries[0]['seq']

    requests = stage_rows('NATURAL_FINAL_REQUESTED')
    require(len(requests) == int(ended) and attempt(q) == attempt(bodies[0]))
    for stage in ('NATURAL_REPLY_CALL_STARTED', 'NATURAL_REPLY_RECEIVED'):
        require(len(stage_rows(stage)) == len(bodies))
    finish = None
    current_context = _context_ref(snapshot)
    for index, body in enumerate(bodies):
        op = body['payload']
        artifact = op['artifact']
        purpose = 'FINAL' if index else 'PRE_QUESTION'
        status = 'COMPLETED' if index else 'AWAITING_ANSWER'
        ids = attempt(body)
        for key in ids:
            _uuid(key, 'PIECE_SOURCE_NOT_ELIGIBLE')
        require(body['round_index'] == index and op.get('stage') == 'INITIAL'
                and artifact.get('schema_version') == ARTIFACT_SCHEMA and artifact.get('text') == op['text']
                and isinstance(op['text'], str) and bool(op['text'].strip())
                and isinstance(artifact.get('model'), str) and bool(artifact['model'].strip()))
        # A skip can refresh revoked paid history. Only the current context can
        # be reconstructed; its source prefix must match the admitted original.
        if op.get('context_ref') == current_context:
            require(op.get('source_prefix_ref') == admitted.source_prefix_ref
                    and op.get('context_guards') == d.get('context_guards', [])
                    and _natural_analysis_material_matches(saved, snapshot, body, request))
        pair = []
        for stage in ('NATURAL_REPLY_CALL_STARTED', 'NATURAL_REPLY_RECEIVED'):
            rows = [e for e in stage_rows(stage) if e['operation_id'] == body['operation_id']]
            require(len(rows) == 1)
            row = rows[0]
            require(row['round_index'] == index and row['payload'].get('response_stage') == purpose
                    and row['payload'].get('source_prefix_ref') == op['source_prefix_ref']
                    and row['payload'].get('context_ref') == op['context_ref']
                    and all(row['payload'].get(key) == artifact.get(key)
                            for key in ('meaning_profile', 'writer_messages_sha256')))
            pair.append(row)
        started, received = pair
        require(started['seq'] < received['seq'] < body['seq']
                and attempt(started) == attempt(received) and same_operation(received, body)
                and received['payload'].get('reply') == dict(text=op['text'], model=artifact['model'],
                    source_prefix_ref=op['source_prefix_ref'], schema_version=ARTIFACT_SCHEMA))
        finishes = [e for e in events if e['kind'] == 'OPERATION' and attempt(e) == ids
                    and e['payload'].get('status') in ('COMPLETED', 'AWAITING_ANSWER')]
        require(len(finishes) == 1 and finishes[0]['payload'].get('failure_code') is None
                and finishes[0]['payload']['status'] == status and body['seq'] < finishes[0]['seq'])
        if index:
            final_request = requests[0]
            require(finish['seq'] < final_request['seq'] < started['seq'] and same_operation(final_request, started)
                    and bodies[0]['operation_id'] != body['operation_id'] and final_request['round_index'] == 1
                    and final_request['payload'].get('status') == 'RUNNING'
                    and final_request['payload'].get('question_ending') == d['natural_question_stop'])
        else:
            require(body['seq'] < q['seq'] < finishes[0]['seq'])
        finish = finishes[0]
    op = observation['payload']
    require(attempt(observation) == (d.get('operation_id'), d.get('attempt_id'))
            and op.get('source_prefix_ref') == admitted.source_prefix_ref
            and op.get('context_ref') == current_context)
    stamp = parse_iso_utc(observation['recorded_at'])
    require(stamp is not None and parse_iso_utc(saved.recorded_at) <= stamp <= parse_iso_utc(snapshot['now']))
    return q['id']


def _original_observation_handoff(saved: PieceSavedOriginal, snapshot: dict) -> PieceSavedHandoff:
    """Bind the existing PCE-2 envelope to persisted Q2/Q3 INITIAL controls.

    A current observation row is not sufficient on its own: require its saved
    source, evaluated checkpoint and successful same-attempt finish. The
    QUESTION event owns the stored question-need decision identity. Its prompt
    and decision body never enter the handoff or Piece semantic material.
    """
    from cocolon_meaning_experience_engine.emlis_thread_contracts import SEMANTIC_SCHEMA
    from cocolon_meaning_experience_engine.natural_reply import ARTIFACT_SCHEMA, PROFILE
    from emlis_thread_service import Q3_PROFILE, _context_ref, _request

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
    if natural and t['issued_count'] == 1:
        question = _natural_unanswered_question(saved, snapshot, observation)
        return _original_piece_lineage(saved, t, observation, 'pre_question_observation', question)
    require(sum(e['kind'] == 'OBSERVATION' for e in events) == 1)
    op = observation['payload']
    require(op.get('stage') == 'INITIAL' and observation['round_index'] == 0)
    require(op.get('source_prefix_ref') == t['source_prefix_ref'])
    if natural:
        # A recipient reply deliberately has no semantic checkpoint. Its saved
        # receipt is completion evidence only, never Piece's semantic material.
        require(d.get('runtime_profile') == Q3_PROFILE)
        require(t['state'] == 'COMPLETED' and d.get('body_state') == 'FINAL')
        require(t['current_meaning_event_id'] is None and t['issued_count'] == 0)
        require(not any(e['kind'] in {'MEANING_UPDATE', 'QUESTION', 'TERMINAL'} for e in events))
        require(op.get('context_ref') == _context_ref(snapshot))
        require(op.get('context_guards') == d.get('context_guards', []))
        artifact = op.get('artifact')
        require(type(artifact) is dict and artifact.get('schema_version') == ARTIFACT_SCHEMA
            and d.get('analysis_state') == artifact.get('analysis_state')
            and _natural_analysis_material_matches(saved, snapshot, observation, _request(snapshot))
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
    return _original_piece_lineage(saved, t, observation, stage, question_identity)


def _original_piece_lineage(saved, t, observation, stage, question_identity):
    thread_id = _uuid(t['id'], 'PIECE_SOURCE_NOT_ELIGIBLE')
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


def _direct_feeling_piece_material_matches(body, saved, correction, replacement_range):
    # The completed Emlis artifact keeps the correction's actual source
    # identity, even when its reply phrases the corrected feeling differently.
    material = body['payload']['artifact'].get('analysis_material') or {}
    fields = material.get('active_fields') or []
    if replacement_range is None or material.get('coverage', {}).get('active_state') != 'RESOLVED' or len(fields) != 1:
        return False
    field = fields[0]
    return (field.get('source_id') == correction.correction_id
        and field.get('source_role') == 'USER_INTERPRETATION_CORRECTION'
        and field.get('record_ref') == saved.saved_input_id
        and field.get('field_path') == 'memo'
        and (field.get('scalar_start'), field.get('scalar_end')) == replacement_range
        and field.get('text') == correction.explanation[slice(*replacement_range)])


def _corrected_observation_handoff(saved, snapshot, answer_id=None):
    """Bind every proper correction and its actual completed FINAL receipt."""
    from dataclasses import asdict, replace
    from emlis_thread_service import _context_ref, _request, NATURAL_REPLY_PROFILE, Q3_PROFILE
    from cocolon_meaning_experience_engine.cores.analysis.source_adapter import analysis_circumstance_control
    from cocolon_meaning_experience_engine.emlis_thread_source import admit_emlis_thread
    from cocolon_meaning_experience_engine.natural_reply import ARTIFACT_SCHEMA
    from cocolon_meaning_experience_engine.piece_refined import corrected_active_ranges

    def require(value):
        if not value:
            raise _error('PIECE_SOURCE_NOT_ELIGIBLE')

    t, events = snapshot['thread'], snapshot['events']
    d = t['data']
    mixed=answer_id is not None
    n=t['issued_count']
    answer_history=(_natural_later_add_handoff(saved,snapshot,answer_id,correction_prefix=True) if mixed else None)
    thread_id = _uuid(t['id'], 'PIECE_SOURCE_NOT_ELIGIBLE')
    require(type(t['revision']) is int and t['revision'] > 0
        and t['state'] == 'COMPLETED' and type(n) is int and (1<=n<=3 if mixed else n==0)
        and d.get('runtime_profile') == Q3_PROFILE and d.get('response_profile') == NATURAL_REPLY_PROFILE
        and d.get('semantic_profile') is None and d.get('body_state') == 'FINAL'
        and d.get('answer_assessment') == ('RESOLVED' if mixed else 'NOT_APPLICABLE') and d.get('natural_response_stage') == 'FINAL'
        and d.get('failure_code') is None and d.get('meaning_updated') is False)
    require(all(t[key] is None for key in ('active_operation_id', 'active_attempt_id',
        'processing_deadline_at', 'current_meaning_event_id', 'evaluated_prefix_ref')))
    require(t['latest_answer_event_id']==answer_id)
    require(canonical_json_bytes(t['source_snapshot']) == saved._original_json)
    require(type(events) is list and bool(events))
    by_id, seqs = {}, []
    for event in events:
        require(type(event) is dict and event.get('thread_id') == thread_id
            and event.get('kind') in ({'OPERATION','OBSERVATION','QUESTION','ANSWER','MEANING_UPDATE','TERMINAL'} if mixed else {'OPERATION','OBSERVATION'}) and type(event.get('payload')) is dict
            and type(event.get('seq')) is int and event['seq'] > 0
            and type(event.get('round_index')) is int and 0<=event['round_index']<=n)
        eid = _uuid(event['id'], 'PIECE_SOURCE_NOT_ELIGIBLE')
        require(eid not in by_id)
        by_id[eid] = event
        seqs.append(event['seq'])
    require(seqs == sorted(set(seqs)))
    corrections = [e for e in events if e['kind'] == 'OPERATION'
        and e['payload'].get('stage') == 'INTERPRETATION_CORRECTION']
    observations = [e for e in events if e['kind'] == 'OBSERVATION'
        and (not mixed or e['payload'].get('stage')=='CORRECTED')]
    if mixed:
        observations.insert(0,answer_history['observation'])
    require(bool(corrections) and len(observations) == len(corrections) + 1)
    request = _request(snapshot)
    admitted = admit_emlis_thread(request)
    sources = admitted.control.interpretation_corrections
    require(len(admitted.answers)==n and len(sources)==len(corrections))
    answers=tuple(a.source for a in admitted.answers)
    require(not mixed or answers==answer_history['answers'])
    now = parse_iso_utc(snapshot['now'])
    require(now is not None and t['last_observation_event_id'] == observations[-1]['id']
        and t['source_prefix_ref'] == admitted.source_prefix_ref
        and d.get('analysis_state') == _latest_natural_analysis_state(snapshot))
    previous_finish = None
    for i, body in enumerate(observations):
        if mixed and i==0:
            previous_finish=answer_history['end_event']
            continue
        require(body['round_index']==n)
        prefix_sources = sources[:i]
        prefix_request = replace(request, emlis_thread=replace(request.emlis_thread,
            interpretation_corrections=prefix_sources,
            direct_feeling_correction_ids=tuple(s.correction_id for s in prefix_sources
                if s.correction_id in request.emlis_thread.direct_feeling_correction_ids)))
        prefix = admit_emlis_thread(prefix_request).source_prefix_ref
        bp = body['payload']
        require(bp.get('stage') == ('INITIAL' if i == 0 else 'CORRECTED')
            and bp.get('source_prefix_ref') == prefix and body.get('question_id') is None
            and bp.get('context_ref') == _context_ref(snapshot)
            and bp.get('context_guards') == d.get('context_guards', []))
        for key in ('operation_id', 'attempt_id'):
            _uuid(body.get(key), 'PIECE_SOURCE_NOT_ELIGIBLE')
        ba = bp.get('artifact')
        require(type(ba) is dict and ba.get('schema_version') == ARTIFACT_SCHEMA
            and type(bp.get('text')) is str and bool(bp['text'].strip()) and ba.get('text') == bp['text']
            and type(ba.get('model')) is str and bool(ba['model'].strip())
            and _natural_analysis_material_matches(saved, snapshot, body, prefix_request))
        paired = [e for e in events if e['kind'] == 'OPERATION'
            and e['operation_id'] == body['operation_id'] and e['attempt_id'] == body['attempt_id']]
        groups = ([e for e in paired if e['payload'].get('stage') == 'NATURAL_REPLY_CALL_STARTED'],
            [e for e in paired if e['payload'].get('stage') == 'NATURAL_REPLY_RECEIVED'],
            [e for e in paired if e['payload'].get('status') == 'COMPLETED'
                and e['payload'].get('failure_code') is None])
        require(all(len(rows) == 1 for rows in groups))
        bs, br, bf = (rows[0] for rows in groups)
        require(bs['seq'] < br['seq'] < body['seq'] < bf['seq'])
        for event in (bs, br):
            require(event['payload'].get('source_prefix_ref') == prefix
                and event['payload'].get('context_ref') == bp['context_ref']
                and event['payload'].get('response_stage') == 'FINAL')
        require(br['payload'].get('reply') == dict(text=bp['text'], model=ba['model'],
            source_prefix_ref=prefix, schema_version=ARTIFACT_SCHEMA))
        stamps = [parse_iso_utc(saved.recorded_at)] + [parse_iso_utc(e.get('recorded_at'))
            for e in (bs, br, body, bf)] + [now]
        require(all(stamp is not None for stamp in stamps) and stamps == sorted(stamps))
        if i:
            correction_event, correction = corrections[i-1], sources[i-1]
            cp, target = correction_event['payload'], observations[i-1]
            require(cp.get('status') == 'SAVED' and cp.get('assessment') == 'UNASSESSED'
                and correction_event.get('question_id') is None
                and type(correction_event.get('idempotency_key')) is str
                and bool(correction_event['idempotency_key'].strip()) and cp.get('source') == asdict(correction)
                and correction.correction_id == correction_event['id']
                and correction.target_event_id == target['id'] and correction.thread_id == thread_id
                and correction.original_source_ref == d.get('original_source_ref')
                and type(target['payload'].get('text')) is str
                and target['payload']['text'].count(correction.target_text) == 1
                and correction_event['operation_id'] == body['operation_id']
                and correction_event['attempt_id'] == body['attempt_id']
                and previous_finish['seq'] < correction_event['seq'] < bs['seq'])
            cstamp, written = parse_iso_utc(correction_event.get('recorded_at')), parse_iso_utc(correction.recorded_at)
            require(cstamp is not None and written is not None
                and parse_iso_utc(target['recorded_at']) <= written <= cstamp <= stamps[1]
                and parse_iso_utc(previous_finish['recorded_at']) <= written)
        previous_finish = bf
    observation, correction = observations[-1], sources[-1]
    for key in ('operation_id', 'attempt_id'):
        require(observation[key] == d.get(key))
    original_source = project_saved_original_source(saved, source_stage='normal_observation')
    # The saved completion time is an actual, stable source horizon. Fresh
    # access above still uses the DB's current clock; advancing that clock
    # cannot change this completed correction's artifact identity.
    source_as_of = observation['recorded_at']
    circumstance = (analysis_circumstance_control(admitted, include_corrected=True)
        if mixed and answer_history['bound_feeling_circumstance'] else None)
    direct_ids = admitted.control.direct_feeling_correction_ids if not mixed and len(sources) == 1 else ()
    operation, ranges, replacement_range, commitment = corrected_active_ranges(
        original_source, correction, as_of=source_as_of, prior_corrections=sources[:-1],
        answer_sources=answers, circumstance_control=circumstance, direct_feeling_correction_ids=direct_ids)
    if direct_ids:
        require(_direct_feeling_piece_material_matches(observation, saved, correction, replacement_range))
    source_binding = dict(correction_id=correction.correction_id,
        source_version='sha256:' + canonical_sha256_hex(asdict(correction)),
        explanation_commitment=commitment, target_event_id=correction.target_event_id)
    lineage = dict(handoff_contract_version='cocolon.cross_core.source_handoff.v1',
        piece_source_lineage_version='piece.source_lineage.v1',
        source_input=dict(source_input_id=saved.saved_input_id, source_input_version=saved.source_input_version,
            source_input_bundle_commitment=saved.input_bundle_commitment,
            source_owner_user_id=saved.authenticated_owner_id,
            source_recorded_at=parse_iso_utc(saved.recorded_at).isoformat()),
        observation=dict(emlis_observation_stage='corrected_observation',
            emlis_observation_result_identity=observation['id'], emlis_observation_result_state='terminal_success',
            question_need_decision_identity=answer_history['question_event_id'] if mixed else None,
            supplemental_answer_identity=answer_id,
            supplemental_answer_version=answers[-1].source_version if mixed else None,
            supplemental_answer_bundle_commitment='sha256:'+admitted.answers[-1].envelope.raw_sha256 if mixed else None),
        semantic_source_roles=(['original_input','supplemental_answer','interpretation_correction'] if mixed
            else ['original_input','interpretation_correction']),
        lineage_control_roles=(['emlis_observation_result','question_need_decision','ai_interpretation_target'] if mixed
            else ['emlis_observation_result','ai_interpretation_target']),
        piece_generation_eligibility=dict(contract_version='piece.generation_eligibility.v1', decision='eligible', reason_codes=[]),
        interpretation_correction_source=source_binding, body_free=True)
    fence = dict(source=asdict(correction), source_prefix_ref=admitted.source_prefix_ref,
        events=events, thread_data=d)
    if sources[:-1]:
        fence['prior_sources'] = [asdict(c) for c in sources[:-1]]
    if mixed:
        fence.update(answer_sources=[asdict(a) for a in answers],answer_checkpoints=list(answer_history['checkpoints']))
    return PieceSavedCorrectedHandoff(saved, correction, thread_id, t['revision'],
        canonical_json_bytes(lineage), canonical_json_bytes(fence), source_as_of, operation, ranges,
        replacement_range, sources[:-1], answers, circumstance)


def project_saved_corrected_source(handoff):
    from dataclasses import asdict
    from emlis_thread_service import _direct_feeling_correction_ids
    from cocolon_meaning_experience_engine.piece_refined import (
        PieceCorrectedSourceSnapshot, corrected_active_ranges,
    )
    if type(handoff) is not PieceSavedCorrectedHandoff:
        raise _error('PIECE_SOURCE_NOT_ELIGIBLE')
    source = project_saved_original_source(handoff.original, source_stage='normal_observation')
    line, control = handoff.lineage_payload(), json.loads(handoff._correction_state_json)
    if type(control) is not dict or type(control.get('events')) is not list:
        raise _error('PIECE_CONFLICT')
    events = control['events']
    mixed=bool(handoff.answer_sources)
    direct_ids = _direct_feeling_correction_ids({'events': events}) if not mixed and not handoff.prior_corrections else ()
    question=None
    question_event=None
    selected=handoff.answer_sources[-1] if mixed else None
    if mixed:
        from cocolon_meaning_experience_engine.emlis_thread_source import freeze_supplemental_answer
        matches=[e for e in control.get('events',[]) if e.get('kind')=='QUESTION'
            and e.get('round_index')==selected.round_index and e.get('question_id')==selected.question_id]
        if len(matches)!=1: raise _error('PIECE_CONFLICT')
        question_event=matches[0]
        question=question_event['id']
        _uuid(question,'PIECE_CONFLICT')
        answer_commitment='sha256:'+freeze_supplemental_answer(selected).envelope.raw_sha256
    circumstance = handoff.circumstance_control
    if circumstance is not None:
        from emlis_thread_service import _json
        from cocolon_meaning_experience_engine.cores.analysis.source_adapter import AnalysisCircumstanceControl
        if (type(circumstance) is not AnalysisCircumstanceControl or question_event is None
                or circumstance.answer != selected or _json(circumstance.question) != question_event['payload']):
            raise _error('PIECE_CONFLICT')
    operation, ranges, replacement_range, commitment = corrected_active_ranges(
        source, handoff.correction, as_of=handoff.as_of, prior_corrections=handoff.prior_corrections,
        answer_sources=handoff.answer_sources, circumstance_control=circumstance, direct_feeling_correction_ids=direct_ids)
    binding = dict(correction_id=handoff.correction.correction_id,
        source_version='sha256:' + canonical_sha256_hex(asdict(handoff.correction)),
        explanation_commitment=commitment, target_event_id=handoff.correction.target_event_id)
    observation = line.get('observation', {})
    _uuid(observation.get('emlis_observation_result_identity'), 'PIECE_CONFLICT')
    if direct_ids:
        bodies = [event for event in events if event['id'] == observation['emlis_observation_result_identity']
                  and event['kind'] == 'OBSERVATION' and event['payload'].get('stage') == 'CORRECTED']
        if len(bodies) != 1 or not _direct_feeling_piece_material_matches(
                bodies[0], handoff.original, handoff.correction, replacement_range):
            raise _error('PIECE_CONFLICT')
    expected_source = dict(source_input_id=handoff.original.saved_input_id,
        source_input_version=handoff.original.source_input_version,
        source_input_bundle_commitment=handoff.original.input_bundle_commitment,
        source_owner_user_id=handoff.original.authenticated_owner_id,
        source_recorded_at=parse_iso_utc(handoff.original.recorded_at).isoformat())
    if (set(line) != {'handoff_contract_version', 'piece_source_lineage_version',
            'source_input', 'observation', 'semantic_source_roles', 'lineage_control_roles',
            'piece_generation_eligibility', 'interpretation_correction_source', 'body_free'}
            or line.get('handoff_contract_version') != 'cocolon.cross_core.source_handoff.v1'
            or line.get('piece_source_lineage_version') != 'piece.source_lineage.v1'
            or line.get('source_input') != expected_source
            or line.get('semantic_source_roles') != (['original_input','supplemental_answer','interpretation_correction'] if mixed
                else ['original_input','interpretation_correction'])
            or line.get('lineage_control_roles') != (['emlis_observation_result','question_need_decision','ai_interpretation_target'] if mixed
                else ['emlis_observation_result','ai_interpretation_target'])
            or line.get('body_free') is not True
            or line.get('piece_generation_eligibility') != dict(
                contract_version='piece.generation_eligibility.v1', decision='eligible', reason_codes=[])
            or observation != dict(emlis_observation_stage='corrected_observation',
                emlis_observation_result_identity=observation.get('emlis_observation_result_identity'),
                emlis_observation_result_state='terminal_success', question_need_decision_identity=question,
                supplemental_answer_identity=selected.answer_id if mixed else None,
                supplemental_answer_version=selected.source_version if mixed else None,
                supplemental_answer_bundle_commitment=answer_commitment if mixed else None)
            or line.get('interpretation_correction_source') != binding
            or canonical_json_bytes(line) != handoff._lineage_json
            or type(control) is not dict or set(control) != ({'source', 'source_prefix_ref', 'events', 'thread_data'}
                | ({'prior_sources'} if handoff.prior_corrections else set())
                | ({'answer_sources','answer_checkpoints'} if mixed else set()))
            or canonical_json_bytes(control) != handoff._correction_state_json
            or control.get('source') != asdict(handoff.correction)
            or (control.get('prior_sources', []) != [asdict(c) for c in handoff.prior_corrections])
            or control.get('answer_sources',[]) != [asdict(a) for a in handoff.answer_sources]
            or (mixed and control.get('answer_checkpoints') != [e['payload'] for e in control.get('events',[])
                if e.get('kind')=='MEANING_UPDATE'])
            or (operation, ranges, replacement_range) != (handoff.correction_update_operation,
                handoff.original_active_ranges, handoff.correction_active_range)
            or handoff.thread_id != handoff.correction.thread_id
            or line['observation']['emlis_observation_stage'] != 'corrected_observation'):
        raise _error('PIECE_CONFLICT')
    return PieceCorrectedSourceSnapshot(original=source, correction=handoff.correction,
        original_commitment=handoff.original.record_commitment, correction_commitment=commitment,
        corrected_result_identity=line['observation']['emlis_observation_result_identity'],
        opted_in=True, original_active_ranges=ranges, correction_active_range=replacement_range,
        correction_update_operation=operation, as_of=handoff.as_of, prior_corrections=handoff.prior_corrections,
        answer_sources=handoff.answer_sources,selected_answer_id=selected.answer_id if mixed else None,
        question_need_decision_identity=question, circumstance_control=circumstance,
        direct_feeling_correction_ids=direct_ids)


def _natural_refined_save_retried(events, received, observation):
    """Verify each failed attempt and explicit retry between receipt and save."""
    from emlis_thread_service import RETRYABLE_FAILURES

    between = [e for e in events if received['seq'] < e['seq'] < observation['seq']]
    if not between or len(between) % 2:
        return False
    if any(e['kind'] != 'OPERATION' or e['operation_id'] != received['operation_id']
           or e['round_index'] != received['round_index'] for e in between):
        return False
    stamps = [parse_iso_utc(e['recorded_at']) for e in [received, *between, observation]]
    if None in stamps or stamps != sorted(stamps):
        return False

    attempt = received['attempt_id']
    seen = {attempt}
    for failure, retry in zip(between[::2], between[1::2], strict=True):
        fail, start = failure['payload'], retry['payload']
        next_attempt = _uuid(retry['attempt_id'], 'PIECE_SOURCE_NOT_ELIGIBLE')
        fingerprint = start.get('request_fingerprint')
        if (failure['attempt_id'] != attempt or fail.get('status') != 'RESPONSE_FAILED'
                or fail.get('failure_code') not in RETRYABLE_FAILURES
                or next_attempt in seen or start.get('status') != 'RUNNING'
                or retry['question_id'] is not None or set(start) != {'status', 'request_fingerprint'}
                or not isinstance(retry['idempotency_key'], str) or not retry['idempotency_key']
                or not isinstance(fingerprint, str) or not re.fullmatch(r'action-request-[0-9a-f]{64}', fingerprint)):
            return False
        seen.add(next_attempt)
        attempt = next_attempt
    return attempt == observation['attempt_id']


def _natural_initial_frame_feedback(saved, snapshot, initial, initial_finish, answer, request):
    """Reconstruct the initial context across the first decision on an owned past frame."""
    from dataclasses import replace
    from cocolon_meaning_experience_engine.emlis_thread_source import identity
    from emlis_thread_service import _context_ref

    thread = snapshot['thread']
    data = thread['data']
    guards = data.get('context_guards', [])
    updates = [e for e in snapshot['events'] if initial_finish['seq'] < e['seq'] < answer['seq']]
    if (snapshot['tier'] != 'premium' or len(updates) != 1
            or initial['payload'].get('context_guards') != guards):
        return None
    update, = updates
    payload = update['payload']
    target = payload.get('frame_feedback_target')
    event_status = payload.get('status')
    if (update['kind'] != 'OPERATION' or update['round_index'] != answer['round_index']
            or update['seq'] != initial_finish['seq'] + 1 or answer['seq'] != update['seq'] + 1
            or any(update[key] is not None for key in ('operation_id', 'attempt_id', 'question_id'))
            or not isinstance(update['idempotency_key'], str) or not update['idempotency_key']
            or set(payload) != {'status', 'request_fingerprint', 'frame_feedback_target'}
            or event_status not in ('FRAME_CONFIRMED', 'FRAME_REJECTED', 'FRAME_REVISED')
            or type(target) is not dict
            or type(target.get('feedback_version')) is not int or target['feedback_version'] != 1
            or target.get('displayed_status') != 'TENTATIVE'):
        return None
    times = [parse_iso_utc(e['recorded_at']) for e in (initial_finish, update, answer)]
    if None in times or times != sorted(times):
        return None

    key, source_id = target.get('frame_key'), target.get('input_id')
    source_guard = target.get('source_guard')
    if (not isinstance(source_id, str) or source_id == saved.saved_input_id
            or source_guard not in guards or source_guard[0] != source_id
            or [key, 1] not in data.get('context_feedback', [])
            or any(row[0] == key for row in data.get('frame_target_dependencies', []))):
        return None
    frames = initial['payload'].get('artifact', {}).get('interpretive_frames', [])
    frame_keys = ('frame_key', 'frame_ref', 'input_id', 'trigger', 'received_meaning', 'evidence_refs')
    if (set(target) != {*frame_keys, 'source_guard', 'displayed_status', 'feedback_version'}
            or sum(all(name in row and row[name] == target[name] for name in frame_keys)
                   and row.get('status') == 'TENTATIVE' and bool(row.get('evidence_refs')) for row in frames) != 1):
        return None
    current = request.emlis_thread.frame_feedback_sources
    status = event_status.removeprefix('FRAME_')
    matches = [f for f in current if f.frame_key == key and f.source_emotion_id == source_id
               and f.frame_ref == target.get('frame_ref') and f.version == 1 and f.status == status
               and payload.get('request_fingerprint') == identity(
                   'frame-feedback-request', f.frame_ref, f.status, f.correction_text)]
    if len(matches) != 1:
        return None
    recorded_feedback = parse_iso_utc(matches[0].updated_at)
    if recorded_feedback is None or not times[0] <= recorded_feedback <= times[1]:
        return None

    previous_data = {**data, 'context_feedback': [row for row in data['context_feedback'] if row != [key, 1]]}
    initial_context = _context_ref({**snapshot, 'thread': {**thread, 'data': previous_data}})
    initial_request = replace(request, emlis_thread=replace(request.emlis_thread,
        frame_feedback_sources=tuple(f for f in current if f is not matches[0]),
        rejected_frame_keys=tuple(k for k in request.emlis_thread.rejected_frame_keys if k != key)))
    return initial_request, initial_context


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
    from cocolon_meaning_experience_engine.emlis_answer_update import (
        bound_feeling_circumstance, prepare_emlis_meaning,
    )
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
            and d.get('semantic_profile') is None
            and d.get('analysis_state') == _latest_natural_analysis_state(snapshot))
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
    initial_finishes = [e for e in events if e['kind'] == 'OPERATION'
        and all(e[key] == initial[key] for key in ('operation_id', 'attempt_id'))
        and e['payload'].get('status') == 'AWAITING_ANSWER'
        and e['payload'].get('failure_code') is None]
    require(len(initial_finishes) == 1)
    initial_finish = initial_finishes[0]
    require(question['seq'] < initial_finish['seq'] < answer['seq'])
    original_request = replace(request, emlis_thread=replace(request.emlis_thread, answers=(), current_round=0))
    current_context = _context_ref(snapshot)
    initial_context = current_context
    if initial['payload'].get('context_ref') != current_context:
        original = _natural_initial_frame_feedback(saved, snapshot, initial, initial_finish, answer, original_request)
        require(original is not None)
        original_request, initial_context = original
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
            and op.get('context_ref') == current_context
            and op.get('context_guards') == d.get('context_guards', []))
    require(answer['operation_id'] == checkpoint['operation_id'] == observation['operation_id']
            == d.get('operation_id') and answer['attempt_id'] == checkpoint['attempt_id']
            and observation['attempt_id'] == d.get('attempt_id'))
    require(initial['seq'] < question['seq'] < answer['seq'] < checkpoint['seq'] < observation['seq'])

    def receipt_chain(body, prefix, response_stage, source_request, expected_context):
        payload = body['payload']
        context_ref = payload.get('context_ref')
        require(type(context_ref) is str and bool(context_ref)
                and not any(c.isspace() for c in context_ref)
                and context_ref == expected_context
                and payload.get('context_guards') == d.get('context_guards', []))
        artifact = payload.get('artifact')
        require(type(artifact) is dict and artifact.get('schema_version') == ARTIFACT_SCHEMA
                and _natural_analysis_material_matches(saved, snapshot, body, source_request)
                and type(payload.get('text')) is str and bool(payload['text'].strip())
                and artifact.get('text') == payload['text']
                and type(artifact.get('model')) is str and bool(artifact['model'].strip()))
        for key in ('operation_id', 'attempt_id'):
            _uuid(body[key], 'PIECE_SOURCE_NOT_ELIGIBLE')
        author_attempt = checkpoint['attempt_id'] if body is observation else body['attempt_id']
        _uuid(author_attempt, 'PIECE_SOURCE_NOT_ELIGIBLE')
        pair = []
        for stage in ('NATURAL_REPLY_CALL_STARTED', 'NATURAL_REPLY_RECEIVED'):
            matches = [e for e in events if e['kind'] == 'OPERATION'
                and e['payload'].get('stage') == stage
                and e['payload'].get('source_prefix_ref') == prefix]
            require(len(matches) == 1)
            event = matches[0]
            require(event['operation_id'] == body['operation_id'] and event['attempt_id'] == author_attempt
                    and event['round_index'] == body['round_index']
                    and event['payload'].get('context_ref') == context_ref
                    and event['payload'].get('response_stage') == response_stage)
            pair.append(event)
        started, received = pair
        require(started['seq'] < received['seq'] < body['seq'])
        require(received['payload'].get('reply') == {
            'text': payload['text'], 'model': artifact['model'],
            'source_prefix_ref': prefix, 'schema_version': ARTIFACT_SCHEMA})
        if author_attempt != body['attempt_id']:
            require(all(started['payload'].get(key) == received['payload'].get(key) == artifact.get(key)
                        for key in ('meaning_profile', 'writer_messages_sha256'))
                    and _natural_refined_save_retried(events, received, body))
        return started, received

    initial_started, initial_received = receipt_chain(initial, original_prefix, 'PRE_QUESTION', original_request, initial_context)
    started, received = receipt_chain(observation, admitted.source_prefix_ref, 'REFINED', request, current_context)
    require(checkpoint['seq'] < started['seq'])
    # Reject hidden extra calls/corrections, rather than picking a convenient
    # matching receipt from a broader or subsequently changed conversation.
    require(sum(e['kind'] == 'OPERATION' and e['payload'].get('stage') in {
        'NATURAL_REPLY_CALL_STARTED', 'NATURAL_REPLY_RECEIVED'} for e in events) == 4)
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
    # Both receipts are bound to the saved context for their own operation.
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
    feeling_question_id = _saved_personal_feeling_question(prepared, qp['decision'], frozen)
    return PieceSavedRefinedHandoff(saved, frozen.source, thread_id, t['revision'],
        canonical_json_bytes(lineage), operation, original_ranges, answer_range,
        canonical_json_bytes(cp) if operation != 'ADD' else None,
        feeling_question_id=feeling_question_id,
        feeling_circumstance=bound_feeling_circumstance(prepared),
        relative_feeling_anchor=_saved_relative_feeling_anchor(saved, prepared, feeling_question_id))


def _saved_personal_feeling_question(prepared, decision, frozen):
    """Bind the omitted speaker only to this resolved, answer-owned feeling."""
    from cocolon_meaning_experience_engine.emlis_answer_update import _THEN, _FEELING
    text = frozen.source.answer_text_private
    then = _THEN.match(text)
    update = prepared.checkpoint.answer_update
    if (not then or not text.endswith('。') or text[then.end():].startswith(('私', '自分', '僕'))
            or not _FEELING.fullmatch(text[then.end():-1])
            or decision.get('target_kind') != 'PERSONAL_RECEIVED_MEANING'
            or decision.get('missing_dimension') != 'personal_received_meaning'
            or update.question_ref != frozen.source.question_id
            or update.answer_source_ref != frozen.envelope.envelope_id or len(update.updates) != 1):
        return None
    item = update.updates[0]
    if (item.operation != 'ADD' or item.binding_kind != 'QUESTION_FOCUS'
            or item.temporal_binding.about_time != 'ORIGINAL_OCCASION'
            or item.temporal_binding.anchor_source_ref != prepared.thread.original.envelope.envelope_id
            or len(item.changed_claim_refs) != 1):
        return None
    accepted = [n for n in prepared.accepted_nuclei if n.nucleus_id == item.changed_claim_refs[0]]
    if len(accepted) != 1:
        return None
    claim = accepted[0]
    if (claim.semantic_frame.actor != 'current_user' or claim.semantic_frame.predicate_kind != 'feeling'
            or claim.source_fields != ('answer_text_private',) or len(claim.source_span_ids) != 1):
        return None
    ref = prepared.thread.resolver().qualified_ref(claim.source_span_ids[0])
    if (ref.source_envelope_id == frozen.envelope.envelope_id
            and ref.evidence.evidence_id in item.evidence_refs):
        return frozen.source.question_id
    return None


def _saved_relative_feeling_anchor(saved, prepared, feeling_question_id):
    """Find the original event through the saved question and resolved ADD."""
    from cocolon_meaning_experience_engine.emlis_answer_update import build_updated_grounded_plan
    from cocolon_meaning_experience_engine.piece_refined import PieceRelativeFeelingAnchor
    from emlis_ai_grounded_human_reception import final_reception_source_anchor_text

    if feeling_question_id is None:
        return None
    thread = prepared.thread
    control = thread.control.question_control_context
    question = control.pending_question
    if (question is None or question.question_id != feeling_question_id
            or control.issued_questions != (question,) or len(thread.answers) != 1
            or thread.control.interpretation_corrections
            or prepared.checkpoint.inactive_claim_refs):
        return None
    answer, = thread.answers
    record = saved.original_payload()
    memo, action = record['memo'], record['memo_action']
    if (not memo or not action or any(c in memo + action for c in '\r\n')
            or not answer.source.answer_text_private.startswith('その時は')):
        return None
    item, = prepared.checkpoint.answer_update.updates
    targets = item.target_meaning_refs
    if len(targets) != 1 or targets[0] not in question.decision.affected_meaning_refs:
        return None
    events = tuple(n for n in prepared.original_plan.nuclei if n.nucleus_id == targets[0])
    if len(events) != 1:
        return None
    event, = events
    frame = event.semantic_frame
    if (event.source_fields != ('memo',) or len(event.source_span_ids) != 1
            or (frame.actor, frame.predicate_kind, frame.time_scope) != ('current_user', 'event', 'past')
            or 'source_received_event_link:noni' not in frame.attribute_codes):
        return None
    resolver = thread.resolver()
    ref = resolver.qualified_ref(event.source_span_ids[0])
    if (ref.source_envelope_id != thread.original.envelope.envelope_id
            or ref.evidence.field_path != 'memo'
            or question.decision.supporting_evidence_refs != (ref.evidence.evidence_id,)):
        return None
    try:
        updated = build_updated_grounded_plan(prepared)
    except ValueError:
        return None
    target, = item.changed_claim_refs
    relations = tuple(r for r in updated.relations if r.to_nucleus_id == target
                      and r.type == 'evaluation_about_event')
    if (len(relations) != 1 or relations[0].from_nucleus_id != event.nucleus_id
            or relations[0].grounding_kind != 'user_stated_relation'
            or relations[0].retention != 'required'):
        return None
    event_literal = final_reception_source_anchor_text(event.nucleus_id, {event.nucleus_id: event}, resolver)
    start, end = ref.evidence.scalar_start, ref.evidence.scalar_end
    location = memo.find(event_literal, start, end)
    if (not event_literal or location < 0
            or memo.find(event_literal) != location or memo.find(event_literal, location + 1) != -1
            or event_literal in action):
        return None
    return PieceRelativeFeelingAnchor(question.question_id, answer.source.answer_id,
                                      (location, location + len(event_literal)))


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
    answer_text = prepared.thread.answers[-1].source.answer_text_private
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
        text = prepared.thread.answers[-1].source.answer_text_private
        require(ref.source_envelope_id == prepared.thread.answers[-1].envelope.envelope_id
            and re.sub(r'\s+', ' ', span.raw_text.replace('\u3000', ' ')).strip() == span.raw_text
            and 0 <= a < b <= len(span.raw_text)
            and text[span.start_index:span.end_index] == span.raw_text)
        answer_range = (span.start_index + a, span.start_index + b)
        require(text[answer_range[0]:answer_range[1]] == correction.group('new'))
    return update.operation, tuple(ranges), answer_range


def _natural_later_add_handoff(saved, snapshot, answer_id, *, correction_prefix=False):
    """Select the last independent answer, after validating every real round.

    Earlier answers prove eligibility only. They never become extra Piece
    partitions and cannot silently revise the retained original input.
    """
    from dataclasses import replace
    from emlis_thread_service import (_context_ref, _json, _request,
        NATURAL_QUESTION_POLICY, NATURAL_REPLY_PROFILE, Q3_PROFILE)
    from cocolon_meaning_experience_engine.emlis_answer_update import bound_feeling_circumstance, prepare_emlis_meaning
    from cocolon_meaning_experience_engine.emlis_thread_contracts import SEMANTIC_SCHEMA
    from cocolon_meaning_experience_engine.emlis_thread_source import admit_emlis_thread
    from cocolon_meaning_experience_engine.natural_reply import ARTIFACT_SCHEMA

    def require(value):
        if not value:
            raise _error('PIECE_SOURCE_NOT_ELIGIBLE')

    t, events = snapshot['thread'], snapshot['events']
    d, n = t['data'], t['issued_count']
    tid = _uuid(t['id'], 'PIECE_SOURCE_NOT_ELIGIBLE')
    require(type(n) is int and n in ((1,2,3) if correction_prefix else (2,3)) and type(t['revision']) is int and t['revision'] > 0)
    require(t['state']=='COMPLETED' and d.get('body_state')==('FINAL' if correction_prefix else 'REFINED')
        and d.get('runtime_profile')==Q3_PROFILE and d.get('response_profile')==NATURAL_REPLY_PROFILE
        and d.get('natural_question_policy')==NATURAL_QUESTION_POLICY
        and d.get('semantic_profile') is None
        and d.get('analysis_state')==_latest_natural_analysis_state(snapshot)
        and d.get('answer_assessment')=='RESOLVED' and d.get('meaning_updated') is (False if correction_prefix else True)
        and d.get('natural_response_stage')==('FINAL' if correction_prefix else 'REFINED') and d.get('failure_code') is None
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
            and (correction_prefix or not (event['kind']=='OPERATION' and event['payload'].get('stage')=='INTERPRETATION_CORRECTION')))
        ids.add(eid); seqs.append(event['seq'])
    require(seqs==sorted(set(seqs)))
    by_kind = {kind:[e for e in events if e['kind']==kind]
        for kind in ('QUESTION','ANSWER','MEANING_UPDATE','OBSERVATION','TERMINAL','OPERATION')}
    qs, answers, cps, bodies = (by_kind[k] for k in ('QUESTION','ANSWER','MEANING_UPDATE','OBSERVATION'))
    correction_events=[e for e in by_kind['OPERATION'] if e['payload'].get('stage')=='INTERPRETATION_CORRECTION']
    if correction_prefix:
        require(bool(correction_events))
        prefix_end_seq=correction_events[0]['seq']
        bodies=[e for e in bodies if e['seq']<prefix_end_seq]
        require(all(e['seq']<prefix_end_seq for e in (*qs,*answers,*cps,*by_kind['TERMINAL'])))
    require(len(qs)==len(answers)==len(cps)==n and len(bodies)==n+1)
    require([e['round_index'] for e in qs]==[e['round_index'] for e in answers]
        ==[e['round_index'] for e in cps]==list(range(1,n+1))
        and [e['round_index'] for e in bodies]==list(range(n+1)))
    require(answers[-1]['id']==answer_id and (correction_prefix or
        cps[-1]['id']==t['current_meaning_event_id'] and bodies[-1]['id']==t['last_observation_event_id']))
    request = _request(snapshot)
    if correction_prefix:
        request=replace(request,emlis_thread=replace(request.emlis_thread,
            interpretation_corrections=(),direct_feeling_correction_ids=()))
    admitted = admit_emlis_thread(request)
    require(len(admitted.answers)==n and (correction_prefix or
        t['source_prefix_ref']==t['evaluated_prefix_ref']==admitted.source_prefix_ref))
    controls = [e for e in by_kind['OPERATION'] if not correction_prefix or e['seq']<prefix_end_seq]
    require(sum(e['payload'].get('stage') in {'NATURAL_REPLY_CALL_STARTED','NATURAL_REPLY_RECEIVED'}
        for e in controls)==2*(n+1))
    context_ref = _context_ref(snapshot)

    def receipt(body, prefix, stage, source_request):
        payload = body['payload']; artifact = payload.get('artifact')
        require(payload.get('source_prefix_ref')==prefix and payload.get('context_ref')==context_ref
            and payload.get('context_guards')==d.get('context_guards', [])
            and payload.get('stage')==('INITIAL' if stage=='PRE_QUESTION' else 'REFINED')
            and 'meaning_checkpoint_ref' not in payload
            and type(artifact) is dict and artifact.get('schema_version')==ARTIFACT_SCHEMA
            and _natural_analysis_material_matches(saved, snapshot, body, source_request)
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
    receipt(bodies[0],original_prefix,'PRE_QUESTION',original_request)
    initial_finishes=[e for e in controls if all(e[k]==bodies[0][k] for k in ('operation_id','attempt_id'))
        and e['payload'].get('status')=='AWAITING_ANSWER' and e['payload'].get('failure_code') is None]
    require(len(initial_finishes)==1)
    previous_finish=initial_finishes[0]
    require(bodies[0]['seq']<qs[0]['seq']<previous_finish['seq']<answers[0]['seq']
        and all(qs[0][k]==bodies[0][k] for k in ('operation_id','attempt_id')))
    continued=[e for e in controls if e['payload'].get('status')=='CONTINUED']
    require(len(continued)==n-1)
    prepared_rounds = []
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
        prepared_rounds.append(prepared)
        require(_json(prepared.checkpoint)==payload and payload.get('semantic_schema_version')==SEMANTIC_SCHEMA
            and payload.get('source_prefix_ref')==prefix and payload.get('assessment_status')=='RESOLVED'
            and payload.get('unresolved_parts')==[])
        update=payload.get('answer_update')
        require(type(update) is dict and update.get('disposition')=='MATERIAL_UPDATE'
            and update.get('answer_source_ref')==frozen.envelope.envelope_id
            and update.get('question_ref')==q['question_id'] and update.get('unresolved_parts')==[]
            and type(update.get('updates')) is list and bool(update['updates']))
        require(all(a[k]==cp[k]==body[k] for k in ('operation_id','attempt_id'))
            and q['seq']<a['seq']<cp['seq']<body['seq'])
        started=receipt(body,prefix,'REFINED',prefix_request); require(cp['seq']<started['seq'])
        finishes=[e for e in controls if all(e[k]==body[k] for k in ('operation_id','attempt_id'))
            and e['payload'].get('status') in {'COMPLETED','AWAITING_CONTINUE'}
            and e['payload'].get('failure_code') is None]
        require(len(finishes)==1); previous_finish=finishes[0]
        require(body['seq']<previous_finish['seq'] and previous_finish['round_index']==i
            and parse_iso_utc(answer_opened['recorded_at'])<=parse_iso_utc(frozen.source.recorded_at)
            <=parse_iso_utc(a['recorded_at']))
    require(correction_prefix or all(bodies[-1][k]==d.get(k) for k in ('operation_id','attempt_id')))
    terminals=by_kind['TERMINAL']
    if (bool(terminals) if correction_prefix else d.get('natural_question_stop')=='stop'):
        require(len(terminals)==1); terminal=terminals[0]
        require(previous_finish['payload']['status']=='AWAITING_CONTINUE'
            and terminal['payload'].get('reason')=='stop' and terminal['round_index']==n
            and all(terminal[k] is None for k in ('operation_id','attempt_id'))
            and previous_finish['seq']<terminal['seq']
            and (terminal['seq']<prefix_end_seq if correction_prefix else terminal['seq']==events[-1]['seq']))
    else:
        require((correction_prefix or d.get('natural_question_stop') is None) and not terminals
            and previous_finish['payload']['status']=='COMPLETED'
            and (previous_finish['seq']<prefix_end_seq if correction_prefix else previous_finish['seq']==events[-1]['seq']))
    stamps=[parse_iso_utc(saved.recorded_at),*[parse_iso_utc(e['recorded_at']) for e in events],parse_iso_utc(snapshot['now'])]
    require(all(x is not None for x in stamps) and all(a<=b for a,b in zip(stamps,stamps[1:])))
    if correction_prefix:
        end_event=terminals[0] if terminals else previous_finish
        require(end_event['seq']<prefix_end_seq and parse_iso_utc(end_event['recorded_at'])
            <=parse_iso_utc(correction_events[0]['payload']['source']['recorded_at']))
        return dict(answers=tuple(a.source for a in admitted.answers),question_event_id=qs[-1]['id'],
            checkpoints=tuple(_json(p.checkpoint) for p in prepared_rounds),
            observation=bodies[-1],end_event=end_event,source_prefix_ref=admitted.source_prefix_ref,
            bound_feeling_circumstance=bound_feeling_circumstance(prepared_rounds[-1]) is not None)
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
    prior_update = (any(any(item.operation != 'ADD' for item in p.checkpoint.answer_update.updates)
                        for p in prepared_rounds[:-1])
        or any(ref.startswith('answer:') for item in prepared.checkpoint.answer_update.updates
               for ref in item.target_meaning_refs))
    operation, original_ranges, answer_range = 'ADD', (), None
    prior_revisions, effective_checkpoints = (), None
    if prior_update:
        operation, original_ranges, answer_range, prior_revisions = _natural_effective_round_ranges(
            saved, prepared_rounds)
        effective_checkpoints = canonical_json_bytes([_json(p.checkpoint) for p in prepared_rounds])
    elif not all(type(x) is dict and x.get('operation') == 'ADD'
            and x.get('superseded_claim_refs') == [] and x.get('affected_dependency_refs') == []
            for x in update['updates']):
        # Prior rounds were independent ADDs. Only the latest exact update
        # may remove an original clause; previous answers remain unselected.
        operation, original_ranges, answer_range = _natural_active_answer_ranges(saved, prepared)
    return PieceSavedRefinedHandoff(saved,frozen.source,tid,t['revision'],canonical_json_bytes(lineage),
        operation, original_ranges, answer_range,
        canonical_json_bytes(_json(prepared.checkpoint)) if operation != 'ADD' and not prior_update else None,
        prior_revisions, effective_checkpoints,
        feeling_question_id=_saved_personal_feeling_question(prepared, qs[-1]['payload']['decision'], frozen)
            if not prior_update else None)


def _natural_effective_round_ranges(saved, prepared_rounds):
    """Project genuine shared Emlis updates without requiring Analysis typing.

    Piece receives only surviving original clauses, still-active prior exact
    replacements and the selected latest answer. Every prefix/checkpoint was
    rederived above; quoted locators and unselected independent ADDs are not
    appended as source. Source envelopes and raw coordinates stay unchanged.
    """
    from cocolon_meaning_experience_engine.emlis_answer_update import _REPLACEMENT, _WITHDRAWAL

    def require(value):
        if not value:
            raise _error('PIECE_SOURCE_NOT_ELIGIBLE')

    resolver = prepared_rounds[-1].thread.resolver()
    original_source = prepared_rounds[-1].thread.original.envelope.envelope_id
    removed_original_spans = set()
    replacements = []

    def replacement_range(prepared, match):
        require(len(prepared.accepted_nuclei) == 1)
        accepted = prepared.accepted_nuclei[0]
        require(accepted.semantic_frame.actor == 'current_user'
            and accepted.source_fields == ('answer_text_private',)
            and len(accepted.source_span_ids) == 1)
        markers = [c for c in accepted.semantic_frame.attribute_codes
                   if c.startswith('source_fragment_scalar_range:')]
        require(len(markers) == 1)
        a, b = map(int, markers[0].split(':')[1:])
        span = resolver.resolve(accepted.source_span_ids[0])
        ref = resolver.qualified_ref(accepted.source_span_ids[0]).evidence
        answer = prepared.thread.answers[-1]
        require(ref.source_envelope_id == answer.envelope.envelope_id
            and 0 <= a < b <= len(span.raw_text)
            and answer.source.answer_text_private[span.start_index:span.end_index] == span.raw_text)
        result = (span.start_index+a, span.start_index+b)
        require(answer.source.answer_text_private[result[0]:result[1]] == match.group('new'))
        return accepted.nucleus_id, result

    for prepared in prepared_rounds:
        update = prepared.checkpoint.answer_update
        require(update.disposition == 'MATERIAL_UPDATE' and not update.unresolved_parts)
        for item in update.updates:
            require(item.operation in {'ADD', 'REVISE', 'WITHDRAW'})
            if item.operation == 'ADD':
                require(not item.superseded_claim_refs and not item.affected_dependency_refs)
                continue
            require(len(update.updates) == 1 and item.binding_kind == 'EXPLICIT_CORRECTION'
                and len(item.target_meaning_refs) == 1
                and item.superseded_claim_refs == item.target_meaning_refs
                and item.temporal_binding.about_time in {'ORIGINAL_OCCASION', 'ANSWER_TIME'})
            raw = prepared.thread.answers[-1].source.answer_text_private
            match = (_REPLACEMENT if item.operation == 'REVISE' else _WITHDRAWAL).fullmatch(
                raw.strip().rstrip('。．.'))
            require(match is not None)
            targets = [n for n in prepared.original_plan.nuclei if n.nucleus_id in item.target_meaning_refs]
            require(len(targets) == 1)
            target = targets[0]
            require(target.semantic_frame.actor == 'current_user'
                and len(target.source_span_ids) == len(target.source_fields) == 1)
            dependencies = [r for r in prepared.original_plan.relations
                            if r.relation_id in item.affected_dependency_refs]
            require(len(dependencies) == len(item.affected_dependency_refs)
                and all(r.grounding_kind == 'bounded_structural_inference' for r in dependencies))
            sid = target.source_span_ids[0]
            ref, span = resolver.qualified_ref(sid).evidence, resolver.resolve(sid)
            if ref.source_envelope_id == original_source:
                require(target.source_fields[0] in {'memo', 'memo_action'}
                    and tuple(n.nucleus_id for n in prepared.original_plan.nuclei
                              if sid in n.source_span_ids) == item.target_meaning_refs
                    and span.raw_text.rstrip('。．.') == match.group('old').rstrip('。．.'))
                removed_original_spans.add(sid)
            else:
                # This target must be an actually introduced, still-active
                # prior answer claim, not the old quote in correction syntax.
                previous = [p for p in prepared_rounds if p.thread.answers[-1].source.round_index
                            < prepared.thread.answers[-1].source.round_index
                            and any(n.nucleus_id == target.nucleus_id for n in p.accepted_nuclei)]
                require(len(previous) == 1 and target.source_fields == ('answer_text_private',)
                    and ref.source_envelope_id == previous[0].thread.answers[-1].envelope.envelope_id)
                old_markers = [c for c in target.semantic_frame.attribute_codes
                               if c.startswith('source_fragment_scalar_range:')]
                if old_markers:
                    require(len(old_markers) == 1)
                    x, y = map(int, old_markers[0].split(':')[1:])
                    literal = span.raw_text[x:y]
                else:
                    literal = span.raw_text
                require(literal.rstrip('。．.') == match.group('old').rstrip('。．.'))
            if item.operation == 'REVISE':
                changed, active_range = replacement_range(prepared, match)
                require(item.changed_claim_refs == (changed,))
                replacements.append((prepared.thread.answers[-1].source, changed, active_range))
            else:
                require(not prepared.accepted_nuclei and not item.changed_claim_refs)

    raw = saved.original_payload()
    original_ranges = []
    for field in ('memo', 'memo_action'):
        text = raw[field] or ''
        spans = [resolver.resolve(sid) for sid in resolver.span_ids
                 if resolver.qualified_ref(sid).evidence.source_envelope_id == original_source
                 and resolver.qualified_ref(sid).evidence.field_path == field]
        cursor = 0
        for span in sorted(spans, key=lambda s:s.start_index):
            start, end = span.start_index, span.end_index
            require(cursor <= start < end <= len(text) and not text[cursor:start].strip()
                and text[start:end] == span.raw_text)
            if end < len(text) and text[end] in '。．.!！?？':
                end += 1
            if span.span_id not in removed_original_spans:
                original_ranges.append((field, start, end))
            cursor = end
        require(not text[cursor:].strip())
    require(bool(original_ranges))
    latest = prepared_rounds[-1]
    inactive = set(latest.checkpoint.inactive_claim_refs)
    prior = tuple((answer, active_range) for answer, claim, active_range in replacements
                  if answer.round_index < latest.thread.answers[-1].source.round_index and claim not in inactive)
    updates = latest.checkpoint.answer_update.updates
    operation = updates[0].operation
    require(all(item.operation == operation for item in updates))
    answer_range = None
    if operation == 'REVISE':
        answer_range = next(r for answer, _, r in replacements
                            if answer.answer_id == latest.thread.answers[-1].source.answer_id)
    return operation, tuple(original_ranges), answer_range, prior


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
        prior_revisions=handoff.prior_revisions,
        effective_round_sources=handoff._effective_checkpoints_json is not None,
        feeling_question_id=handoff.feeling_question_id,
        feeling_circumstance=handoff.feeling_circumstance,
        relative_feeling_anchor=handoff.relative_feeling_anchor,
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
    if type(handoff) is PieceSavedCorrectedHandoff:
        project_saved_corrected_source(handoff)
        return {'interpretation_correction': json.loads(handoff._correction_state_json)}
    if type(handoff) is not PieceSavedRefinedHandoff:
        raise _error('PIECE_CONFLICT')
    if handoff._effective_checkpoints_json is not None:
        project_saved_refined_source(handoff, opted_in=True)
        try:
            checkpoints = json.loads(handoff._effective_checkpoints_json)
        except (ValueError, TypeError, UnicodeError):
            raise _error('PIECE_CONFLICT') from None
        if (type(checkpoints) is not list or len(checkpoints) != handoff.supplemental.round_index
                or canonical_json_bytes(checkpoints) != handoff._effective_checkpoints_json
                or any(type(cp) is not dict or cp.get('assessment_status') != 'RESOLVED'
                       or cp.get('unresolved_parts') != [] for cp in checkpoints)
                or checkpoints[-1].get('source_prefix_ref') != handoff.lineage_payload()['observation']['source_prefix_ref']):
            raise _error('PIECE_CONFLICT')
        return {'meaning_checkpoints': checkpoints}
    if handoff.prior_revisions:
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
