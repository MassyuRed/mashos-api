"""Disabled B5-B preparation and internal reviewed-artifact issuance.

prepare_original retains its pre-issuance contract. issue_prepared_original
connects an already prepared CMEE/B9 artifact to the existing B5 store only
when a supplied server reviewer accepts that exact source and artifact.
No reviewer, renderer or TTL default, HTTP registration or production effect
is introduced. The concrete safety owner and final transaction fence remain
unfinished; this internal connection is not a complete public preview issuer.
"""
from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
import json
import re

from emlis_ai_current_input_bundle import EMLIS_CURRENT_INPUT_BUNDLE_SCHEMA_VERSION
from piece_v2_contract import (
    PIECE_V2_CONTRACT_VERSIONS, PieceContractError, canonical_json_bytes,
    canonical_sha256_hex, validate_piece_text_binding,
)
from piece_v2_generation import generate_piece_candidate
from piece_v2_source_adapter import (
    PieceSavedHandoff, PieceSavedSourceAdapter, project_saved_original_source,
)
from piece_v2_visual import build_visual_recipe, validate_visual_recipe

_SOURCE_FIELDS = frozenset({
    'source_input_id', 'source_input_version', 'source_input_bundle_commitment',
    'emlis_observation_stage', 'emlis_observation_result_identity',
    'question_need_decision_identity', 'supplemental_answer_identity',
})
_VISUAL_FIELDS = frozenset({'theme_id', 'aspect_ratio', 'branding_mode'})
_REQUEST_FIELDS = frozenset({'source_ref', 'requested_format', 'visual_selection'})
_COMMITMENT = re.compile(r'sha256:[0-9a-f]{64}')
_FORMAT_FAILURES = frozenset({'tier_invalid', 'format_choice_not_admitted', 'format_not_eligible'})
_SAFETY_FAILURES = frozenset({
    'existing_safety_detector', 'hidden_control', 'malformed_unicode', 'credential_like_material',
})
_SERVICE_ERRORS = frozenset({
    'PIECE_REQUEST_INVALID', 'PIECE_AUTH_REQUIRED', 'PIECE_SOURCE_NOT_FOUND',
    'PIECE_SOURCE_NOT_ELIGIBLE', 'PIECE_FORMAT_NOT_ELIGIBLE',
    'PIECE_VISUAL_SELECTION_NOT_ALLOWED', 'PIECE_SAFETY_UNAVAILABLE',
    'PIECE_HASH_MISMATCH', 'PIECE_CONFLICT', 'PIECE_TEMPORARILY_UNAVAILABLE',
})


def _error(code: str) -> PieceContractError:
    return PieceContractError(code)


def _request_snapshot(request: object) -> dict:
    """Copy once before the first await; do not retain caller-owned mappings."""
    try:
        if type(request) is not dict or set(request) != _REQUEST_FIELDS:
            raise _error('PIECE_REQUEST_INVALID')
        value = json.loads(canonical_json_bytes(request))
        source, visual = value['source_ref'], value['visual_selection']
        if (type(source) is not dict or set(source) != _SOURCE_FIELDS or
                type(visual) is not dict or set(visual) != _VISUAL_FIELDS):
            raise _error('PIECE_REQUEST_INVALID')
        for key in ('source_input_id', 'source_input_version',
                    'source_input_bundle_commitment', 'emlis_observation_stage',
                    'emlis_observation_result_identity'):
            if type(source[key]) is not str or not source[key].strip():
                raise _error('PIECE_REQUEST_INVALID')
        if not _COMMITMENT.fullmatch(source['source_input_bundle_commitment']):
            raise _error('PIECE_REQUEST_INVALID')
        for key in ('question_need_decision_identity', 'supplemental_answer_identity'):
            if source[key] is not None and (type(source[key]) is not str or not source[key].strip()):
                raise _error('PIECE_REQUEST_INVALID')
        if (source['source_input_version'] != EMLIS_CURRENT_INPUT_BUNDLE_SCHEMA_VERSION or
                source['emlis_observation_stage'] not in ('normal_observation', 'pre_question_observation') or
                source['supplemental_answer_identity'] is not None):
            raise _error('PIECE_SOURCE_NOT_ELIGIBLE')
        chosen = value['requested_format']
        if chosen is not None and (type(chosen) is not str or chosen not in ('short_essay', 'quote', 'declaration')):
            raise _error('PIECE_FORMAT_NOT_ELIGIBLE')
        if any(item is not None and (type(item) is not str or not item) for item in visual.values()):
            raise _error('PIECE_VISUAL_SELECTION_NOT_ALLOWED')
        return value
    except PieceContractError as exc:
        raise _error(exc.code if exc.code in _SERVICE_ERRORS else 'PIECE_REQUEST_INVALID') from None
    except (ValueError, TypeError, UnicodeError, RecursionError):
        raise _error('PIECE_REQUEST_INVALID') from None


@dataclass(frozen=True, slots=True, repr=False)
class PreparedPiecePreview:
    """Request-private assembly only; never authority to save or display publicly.

    The handoff retains original/state identity for the future persistence
    owner. artifact_payload returns a copy containing neither source identity
    nor raw source fields. This object asserts no native layout or safety PASS.
    """
    handoff: PieceSavedHandoff = field(repr=False)
    _artifact_json: bytes = field(repr=False)

    def artifact_payload(self) -> dict:
        return json.loads(self._artifact_json)


class PiecePreviewService:
    def __init__(self, *, source_adapter: PieceSavedSourceAdapter | None = None) -> None:
        self._source_adapter = source_adapter if source_adapter is not None else PieceSavedSourceAdapter()

    async def prepare_original(self, authorization: str | None, request: dict) -> PreparedPiecePreview:
        """Assemble one source-bound artifact without issuing a stored preview.

        No caller tier, body, owner or recipe is admitted. B5-A establishes the
        owner and current saved state; request references are comparisons only.
        Revalidation happens after both text and visual assembly. A subsequent
        save/preview issuance still needs its own current transactional checks.
        """
        value = _request_snapshot(request)
        source_ref = value['source_ref']
        try:
            handoff = await self._source_adapter.resolve_original_handoff(
                authorization, source_ref['source_input_id'])
            if type(handoff) is not PieceSavedHandoff:
                raise _error('PIECE_TEMPORARILY_UNAVAILABLE')
            lineage = handoff.lineage_payload()
            expected = {key: lineage['source_input'][key] for key in (
                'source_input_id', 'source_input_version', 'source_input_bundle_commitment')}
            expected.update({key: lineage['observation'][key] for key in (
                'emlis_observation_stage', 'emlis_observation_result_identity',
                'question_need_decision_identity', 'supplemental_answer_identity')})
            if source_ref != expected:
                raise _error('PIECE_CONFLICT')
            original = handoff.original
            source = project_saved_original_source(original,
                source_stage=expected['emlis_observation_stage'])
            try:
                candidate = generate_piece_candidate(source,
                    authenticated_owner_id=original.authenticated_owner_id,
                    tier=original.subscription_tier, requested_format=value['requested_format'])
            except PieceContractError as exc:
                code = ('PIECE_FORMAT_NOT_ELIGIBLE' if exc.detail in _FORMAT_FAILURES else
                        'PIECE_SAFETY_UNAVAILABLE' if exc.detail in _SAFETY_FAILURES else
                        'PIECE_SOURCE_NOT_ELIGIBLE')
                raise _error(code) from None
            payload = candidate['content_payload']
            try:
                validate_piece_text_binding(payload, candidate['piece_text'], candidate['piece_text_hash'])
            except PieceContractError:
                raise _error('PIECE_HASH_MISMATCH') from None
            selection = value['visual_selection']
            try:
                recipe = build_visual_recipe(candidate['format_type'],
                    tier=original.subscription_tier, language=payload['language'],
                    theme=selection['theme_id'], aspect_ratio=selection['aspect_ratio'],
                    branding=selection['branding_mode'])
            except PieceContractError:
                raise _error('PIECE_VISUAL_SELECTION_NOT_ALLOWED') from None
            artifact = {
                'api_contract_version': PIECE_V2_CONTRACT_VERSIONS['api_contract_version'],
                'piece_contract_version': PIECE_V2_CONTRACT_VERSIONS['piece_contract_version'],
                'format_type': candidate['format_type'], 'eligible_formats': candidate['eligible_formats'],
                'piece_text': candidate['piece_text'], 'piece_text_hash': candidate['piece_text_hash'],
                'content_payload': payload, 'content_payload_hash': canonical_sha256_hex(payload),
                'visual_recipe': recipe, 'visual_recipe_hash': canonical_sha256_hex(recipe),
                'visibility_scope': 'private',
            }
            artifact_bytes = canonical_json_bytes(artifact)
            current = await self._source_adapter.revalidate_original_handoff(authorization, handoff)
            if current != handoff:
                raise _error('PIECE_CONFLICT')
            return PreparedPiecePreview(handoff, artifact_bytes)
        except PieceContractError as exc:
            raise _error(exc.code if exc.code in _SERVICE_ERRORS else 'PIECE_TEMPORARILY_UNAVAILABLE') from None
        except Exception:
            # No internal detector code, input, token or RPC body crosses this
            # service boundary. Cancellation (BaseException) still propagates.
            raise _error('PIECE_TEMPORARILY_UNAVAILABLE') from None


    async def prepare_visual_change(
        self, authorization: str | None, previous: PreparedPiecePreview,
        visual_selection: dict,
    ) -> PreparedPiecePreview:
        """Replace only B9 settings on a server-held, pre-issuance assembly.

        This is not PATCH or persistence: the caller must hold the immutable
        result of prepare_original, never deserialize a client-supplied body.
        All three selectors are required; None uses B9's existing tier default.
        No author, format change, preview ID, expiry or save effect is involved.
        """
        if type(previous) is not PreparedPiecePreview or type(previous.handoff) is not PieceSavedHandoff:
            raise _error('PIECE_REQUEST_INVALID')
        try:
            # Own the choice before either authenticated read can yield.
            if type(visual_selection) is not dict or set(visual_selection) != _VISUAL_FIELDS:
                raise _error('PIECE_REQUEST_INVALID')
            selection = json.loads(canonical_json_bytes(visual_selection))
            if any(v is not None and (type(v) is not str or not v) for v in selection.values()):
                raise _error('PIECE_VISUAL_SELECTION_NOT_ALLOWED')
        except PieceContractError as exc:
            raise _error(exc.code if exc.code in _SERVICE_ERRORS else 'PIECE_REQUEST_INVALID') from None
        except (ValueError, TypeError, UnicodeError, RecursionError):
            raise _error('PIECE_REQUEST_INVALID') from None
        try:
            handoff = previous.handoff
            current = await self._source_adapter.revalidate_original_handoff(authorization, handoff)
            if current != handoff:
                raise _error('PIECE_CONFLICT')
            # Reuse the established text/recipe contracts. This checks internal
            # corruption, not authorship of arbitrary client replacement prose.
            artifact = previous.artifact_payload()
            try:
                payload = artifact['content_payload']
                validate_piece_text_binding(payload, artifact['piece_text'], artifact['piece_text_hash'])
                if (artifact['content_payload_hash'] != canonical_sha256_hex(payload)
                        or artifact['format_type'] != payload['format_type']
                        or artifact['api_contract_version'] != PIECE_V2_CONTRACT_VERSIONS['api_contract_version']
                        or artifact['piece_contract_version'] != PIECE_V2_CONTRACT_VERSIONS['piece_contract_version']
                        or artifact['visibility_scope'] != 'private'):
                    raise _error('PIECE_HASH_MISMATCH')
                validate_visual_recipe(artifact['visual_recipe'],
                    format_type=artifact['format_type'], language=payload['language'],
                    expected_hash=artifact['visual_recipe_hash'])
            except (PieceContractError, KeyError, TypeError):
                raise _error('PIECE_HASH_MISMATCH') from None
            try:
                recipe = build_visual_recipe(artifact['format_type'],
                    tier=current.original.subscription_tier, language=payload['language'],
                    theme=selection['theme_id'], aspect_ratio=selection['aspect_ratio'],
                    branding=selection['branding_mode'])
            except PieceContractError:
                raise _error('PIECE_VISUAL_SELECTION_NOT_ALLOWED') from None
            artifact['visual_recipe'] = recipe
            artifact['visual_recipe_hash'] = canonical_sha256_hex(recipe)
            artifact_bytes = canonical_json_bytes(artifact)
            current = await self._source_adapter.revalidate_original_handoff(authorization, handoff)
            if current != handoff:
                raise _error('PIECE_CONFLICT')
            return PreparedPiecePreview(handoff, artifact_bytes)
        except PieceContractError as exc:
            raise _error(exc.code if exc.code in _SERVICE_ERRORS else 'PIECE_TEMPORARILY_UNAVAILABLE') from None
        except Exception:
            raise _error('PIECE_TEMPORARILY_UNAVAILABLE') from None


    async def issue_prepared_original(
        self, authorization: str | None, request: dict, previous: PreparedPiecePreview,
        *, idempotency_key: str, ttl_seconds: int, renderer_version: str,
        rpc: Callable[[str, dict], Awaitable[dict]],
        safety_review: Callable[[PreparedPiecePreview], Awaitable[str]] | None = None,
    ) -> dict:
        """Connect a server-held CMEE/B9 assembly to the existing B5 store.

        This is an INTERNAL orchestration seam, not a mounted HTTP issuer.
        A supplied server reviewer must inspect this exact source AND artifact
        under all applicable PCE-4 stages. Only its ready/transformed decision
        can proceed; the default is unavailable. Detector non-match, a frozen
        dataclass and these transport tests do not supply that decision.

        The reviewer cannot return replacement text. The original request is
        copied before any await and rebound to the prepared source/selection.
        Repeats with the same server-held assembly never call a text author;
        SQL alone owns replay, expiry, revision and atomic insertion. A lost
        reply is not retried automatically. TTL and renderer identity have no
        invented defaults and must come from the server's admitted runtime.

        Source/tier are revalidated around review, NOT transactionally locked
        through the following RPC. That final read/write fence, a concrete
        PCE-4 reviewer, restart-time replay retrieval and HTTP/UI activation
        remain prerequisites to exposing this path. No live route is changed.
        """
        from piece_v2_content_policy import choose_format
        from piece_v2_store import issue_piece_preview, _key_hash
        errors = _SERVICE_ERRORS | {
            'PIECE_NOT_FOUND', 'PIECE_PREVIEW_STALE', 'PIECE_PREVIEW_EXPIRED',
        }
        try:
            value = _request_snapshot(request)
            if (type(previous) is not PreparedPiecePreview
                    or type(previous.handoff) is not PieceSavedHandoff):
                raise _error('PIECE_REQUEST_INVALID')
            _key_hash(idempotency_key)
            if (type(ttl_seconds) is not int or not 0 < ttl_seconds <= 2147483647
                    or type(renderer_version) is not str
                    or re.fullmatch(r'[A-Za-z0-9_.:\-]{1,128}', renderer_version) is None):
                raise _error('PIECE_REQUEST_INVALID')
            if not callable(safety_review):
                raise _error('PIECE_SAFETY_UNAVAILABLE')
            if not callable(rpc):
                raise _error('PIECE_TEMPORARILY_UNAVAILABLE')
            handoff = previous.handoff
            lineage = handoff.lineage_payload()
            expected = {key: lineage['source_input'][key] for key in (
                'source_input_id', 'source_input_version', 'source_input_bundle_commitment')}
            expected.update({key: lineage['observation'][key] for key in (
                'emlis_observation_stage', 'emlis_observation_result_identity',
                'question_need_decision_identity', 'supplemental_answer_identity')})
            if value['source_ref'] != expected:
                raise _error('PIECE_CONFLICT')
            # Hold a detached copy; neither the request nor a reviewer's copy
            # of artifact_payload can alter the actual bytes submitted below.
            artifact = previous.artifact_payload()
            content_fields = {
                'format_type', 'eligible_formats', 'content_payload', 'content_payload_hash',
                'piece_text', 'piece_text_hash', 'visual_recipe', 'visual_recipe_hash',
            }
            if (type(artifact) is not dict or set(artifact) != content_fields | {
                    'api_contract_version', 'piece_contract_version', 'visibility_scope'}
                    or artifact['api_contract_version'] != PIECE_V2_CONTRACT_VERSIONS['api_contract_version']
                    or artifact['piece_contract_version'] != PIECE_V2_CONTRACT_VERSIONS['piece_contract_version']
                    or artifact['visibility_scope'] != 'private'):
                raise _error('PIECE_HASH_MISMATCH')
            payload = artifact['content_payload']
            validate_piece_text_binding(payload, artifact['piece_text'], artifact['piece_text_hash'])
            if (canonical_sha256_hex(payload) != artifact['content_payload_hash']
                    or payload['format_type'] != artifact['format_type']):
                raise _error('PIECE_HASH_MISMATCH')
            try:
                selected = choose_format(tier=handoff.original.subscription_tier,
                    requested=value['requested_format'], eligible=tuple(artifact['eligible_formats']),
                    recommended=artifact['format_type'])
                if selected != artifact['format_type']:
                    raise _error('PIECE_FORMAT_NOT_ELIGIBLE')
            except PieceContractError:
                raise _error('PIECE_FORMAT_NOT_ELIGIBLE') from None
            selection = value['visual_selection']
            try:
                validate_visual_recipe(artifact['visual_recipe'], format_type=selected,
                    language=payload['language'], expected_hash=artifact['visual_recipe_hash'])
                expected_recipe = build_visual_recipe(selected, tier=handoff.original.subscription_tier,
                    language=payload['language'], theme=selection['theme_id'],
                    aspect_ratio=selection['aspect_ratio'], branding=selection['branding_mode'])
                if expected_recipe != artifact['visual_recipe']:
                    raise _error('PIECE_VISUAL_SELECTION_NOT_ALLOWED')
            except PieceContractError:
                raise _error('PIECE_VISUAL_SELECTION_NOT_ALLOWED') from None
            current = await self._source_adapter.revalidate_original_handoff(authorization, handoff)
            if current != handoff:
                raise _error('PIECE_CONFLICT')
            decision = await safety_review(previous)
            if type(decision) is not str or decision not in ('ready', 'transformed'):
                raise _error('PIECE_SAFETY_UNAVAILABLE')
            current = await self._source_adapter.revalidate_original_handoff(authorization, handoff)
            if current != handoff:
                raise _error('PIECE_CONFLICT')
            record = {key: artifact[key] for key in content_fields}
            record.update(source_lineage=lineage, renderer_version=renderer_version,
                          safety_state='adjusted' if decision == 'transformed' else 'ready')
            return await issue_piece_preview(
                authenticated_user_id=handoff.original.authenticated_owner_id,
                record=record, request_fingerprint=canonical_sha256_hex(value),
                idempotency_key=idempotency_key, ttl_seconds=ttl_seconds, rpc=rpc)
        except PieceContractError as exc:
            raise _error(exc.code if exc.code in errors else 'PIECE_TEMPORARILY_UNAVAILABLE') from None
        except Exception:
            # Cancellation still propagates; no arbitrary reviewer/DB body or
            # diagnostic is surfaced and no recovery write is attempted here.
            raise _error('PIECE_TEMPORARILY_UNAVAILABLE') from None
