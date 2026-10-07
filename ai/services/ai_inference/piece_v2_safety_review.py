"""Code-disabled review of a server-held original Piece before B5 issuance.

Use with PiecePreviewService.issue_prepared_original(safety_review=...). That
service, not this pure reviewer, owns authentication, source/tier revalidation
and the transactional source fence. A dataclass is not proof of authentication.

This connects the existing source scanner, role abstraction, format contracts
and author-free S7 review. It does not author or repair text, call an external
model, select a renderer/TTL, mount HTTP, or enable public/private export.
The scanner and source parser remain bounded implementations, not a claim of
complete PCE-4 coverage, independent linguistic review or product acceptance.
"""
from __future__ import annotations

import unicodedata

from piece_text_formatter import STATE_BLOCKED, format_reflection_text
from piece_v2_content_policy import (
    FORMATS, check_existing_detectors, validate_candidate_text,
    validate_source_meaning_preservation,
)
from piece_v2_contract import (
    PIECE_V2_CONTRACT_VERSIONS, PieceContractError, canonical_sha256_hex,
    validate_piece_text_binding,
)
from piece_v2_preview_service import PreparedPiecePreview
from piece_v2_source_adapter import PieceSavedHandoff, project_saved_original_source
from cocolon_meaning_experience_engine.piece_source import build_piece_source_meaning
from cocolon_meaning_experience_engine.piece_v1c import (
    PieceArtifact, compile_piece_artifact_plan,
)

_ARTIFACT_FIELDS = frozenset({
    'api_contract_version', 'piece_contract_version', 'format_type',
    'eligible_formats', 'content_payload', 'content_payload_hash',
    'piece_text', 'piece_text_hash', 'visual_recipe', 'visual_recipe_hash',
    'visibility_scope',
})


def _reject() -> None:
    raise PieceContractError('PIECE_SAFETY_UNAVAILABLE')


def _scan(text: str) -> bool:
    """Return blocked for the existing severe detector; otherwise check all.

    Compatibility normalization is a detection-only view. Neither this view
    nor the legacy formatter's masked/normalized display is ever returned as
    Piece text or used to replace the original source/hash.
    """
    if type(text) is not str:
        _reject()
    result = format_reflection_text(unicodedata.normalize('NFKC', text))
    if result.display_state == STATE_BLOCKED:
        return True
    check_existing_detectors(text)
    return False


def _artifact(prepared: PreparedPiecePreview) -> tuple[dict, PieceArtifact]:
    value = prepared.artifact_payload()
    if (type(value) is not dict or set(value) != _ARTIFACT_FIELDS
            or value['api_contract_version'] != PIECE_V2_CONTRACT_VERSIONS['api_contract_version']
            or value['piece_contract_version'] != PIECE_V2_CONTRACT_VERSIONS['piece_contract_version']
            or value['visibility_scope'] != 'private'):
        _reject()
    payload, eligible = value['content_payload'], value['eligible_formats']
    if (type(payload) is not dict or type(eligible) is not list
            or not eligible or any(type(fmt) is not str or fmt not in FORMATS for fmt in eligible)
            or type(payload.get('body_blocks')) is not list
            or any(type(block) is not str for block in payload['body_blocks'])
            or value['format_type'] not in eligible):
        _reject()
    validate_piece_text_binding(payload, value['piece_text'], value['piece_text_hash'])
    if value['content_payload_hash'] != canonical_sha256_hex(payload):
        _reject()
    artifact = PieceArtifact(tuple(payload['body_blocks']), value['piece_text'],
                             value['piece_text_hash'], value['format_type'], tuple(eligible))
    # No title/translated text/hidden content or future payload schema may be
    # silently discarded when projecting into the current Piece artifact.
    if artifact.content_payload() != payload:
        _reject()
    return payload, artifact


def _check_formats(meaning, plan, payload: dict, artifact: PieceArtifact) -> None:
    """Review the supplied whole body; never rerun the author for each format.

    Reuse the current envelope validator and source-plan eligibility. Quote
    must not drop a second proposition or written scope; declaration needs
    the source plan's explicit present-commitment admission. Check the entire
    offered list as well as the selected format, without trusting list order,
    duplicates, a client choice, a generated flag, or a matching text hash.
    """
    eligible = []
    for fmt in FORMATS:
        if fmt == 'quote' and (len(meaning.graph.nodes) != 1 or meaning.expression_scopes):
            continue
        if fmt == 'declaration' and not plan.declaration_eligible:
            continue
        try:
            validate_candidate_text(dict(payload, format_type=fmt))
        except PieceContractError:
            continue
        eligible.append(fmt)
    if (artifact.eligible_formats != tuple(eligible)
            or artifact.format_type not in eligible):
        _reject()


async def review_prepared_original(prepared: PreparedPiecePreview) -> str:
    """Return only ready/transformed/ineligible/blocked for this exact artifact.

    There is no success shortcut for private visibility or a paid tier. Source
    and post-format scans are distinct from meaning preservation. Rebuilding
    source meaning/plan uses the existing owners, NOT an author or engine
    replay. Only the current source-stated role abstraction is accepted as a
    safety transform; the S7 check must account for every visible proposition.

    Contract rejection is a body-free ineligible verdict. An unexpected
    implementation failure remains a fixed temporary-unavailable exception;
    cancellation and other BaseException signals still propagate.
    """
    try:
        if type(prepared) is not PreparedPiecePreview or type(prepared.handoff) is not PieceSavedHandoff:
            _reject()
        payload, artifact = _artifact(prepared)
        handoff = prepared.handoff
        stage = handoff.lineage_payload()['observation']['emlis_observation_stage']
        source = project_saved_original_source(handoff.original, source_stage=stage)
        # Check the full projected original before any role abstraction. Raw
        # source is neither replaced by the Piece body nor scanned only after
        # a potentially unsafe detail has disappeared from public wording.
        if _scan(source.original_text):
            return 'blocked'
        meaning = build_piece_source_meaning(source,
            expected_owner_id=handoff.original.authenticated_owner_id,
            expected_saved_input_id=source.saved_input_id,
            expected_source_version=source.source_version)
        plan = compile_piece_artifact_plan(meaning)
        if _scan(artifact.piece_text):
            return 'blocked'
        validate_source_meaning_preservation(meaning, plan, artifact)
        _check_formats(meaning, plan, payload, artifact)
        # Editorial restructuring/normalization alone is ready, not adjusted.
        # A role binding is not sufficient by itself: S7 above verifies the
        # complete source-stated substitution in the actual supplied body.
        return 'transformed' if meaning.role_bindings else 'ready'
    except PieceContractError:
        return 'ineligible'
    except (KeyError, TypeError, ValueError, UnicodeError, RecursionError):
        return 'ineligible'
    except Exception:
        raise PieceContractError('PIECE_TEMPORARILY_UNAVAILABLE') from None
