"""B3 internal Piece visibility/access owner; not a registered HTTP route.

The authenticated user and readers must come from trusted backend code, never
request JSON or a service-role claim. Decisions are per-operation snapshots,
not reusable capabilities. B4 owns write-time locks and atomic reauthorization;
B5/B7/B12 own Bearer authentication, HTTP wiring and final response projection.
No database write, metrics update, cache or notification occurs here.
"""
from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from piece_v2_contract import PieceContractError

_OWNER_OPERATIONS = frozenset({'owner_history', 'export', 'reexport', 'set_visibility', 'delete'})
_PUBLIC_OPERATIONS = frozenset({'detail', 'feed', 'public_profile', 'unread', 'read_marker', 'resonance'})
_OPERATIONS = _OWNER_OPERATIONS | _PUBLIC_OPERATIONS | {'preview_read'}


class PieceAccessError(PieceContractError):
    """Fixed status/code only; never disclose record metadata or backend errors."""

    def __init__(self, code: str) -> None:
        statuses = {'PIECE_AUTH_REQUIRED': 401, 'PIECE_NOT_FOUND': 404,
                    'PIECE_PREVIEW_EXPIRED': 409, 'PIECE_REQUEST_INVALID': 400,
                    'PIECE_TEMPORARILY_UNAVAILABLE': 503}
        if code not in statuses:
            code = 'PIECE_TEMPORARILY_UNAVAILABLE'
        super().__init__(code)
        self.status_code = statuses[code]

    def to_public_error(self) -> dict[str, str]:
        return {'code': self.code}


@dataclass(frozen=True)
class PieceAccessDecision:
    is_owner: bool
    public_state_write_allowed: bool = False


def _uuid(value: Any) -> str | None:
    if not isinstance(value, (str, UUID)):
        return None
    try:
        parsed = UUID(str(value))
        return str(parsed) if parsed.int else None
    except (ValueError, AttributeError):
        return None


def _fail(code: str = 'PIECE_NOT_FOUND') -> None:
    raise PieceAccessError(code) from None


def _request(viewer: Any, operation: Any) -> str:
    user = _uuid(viewer)
    if user is None:
        _fail('PIECE_AUTH_REQUIRED')
    if not isinstance(operation, str) or operation not in _OPERATIONS:
        _fail('PIECE_REQUEST_INVALID')
    return user


def _metadata(row: Any) -> tuple[str, str, str, str]:
    if not isinstance(row, Mapping):
        _fail()
    rid, owner = _uuid(row.get('id')), _uuid(row.get('owner_user_id'))
    state, visibility = row.get('lifecycle_status'), row.get('visibility_scope')
    visibility = 'private' if visibility is None else visibility
    if (rid is None or owner is None or row.get('public_id') != 'piece:' + rid
            or row.get('piece_contract_version') != 'piece.record.v2'
            or not isinstance(state, str) or state not in {'saved', 'preview_draft'}
            or not isinstance(visibility, str) or visibility not in {'private', 'public'}
            or type(row.get('row_version')) is not int or row['row_version'] < 1):
        _fail()
    return rid, owner, state, visibility


def require_piece_access(row: Mapping[str, Any] | None, *, authenticated_user_id: Any,
                         operation: str, relation_allowed: bool = False,
                         preview_identity_valid: bool = False,
                         now: datetime | None = None) -> PieceAccessDecision:
    """Apply the frozen PCE-3 matrix to a freshly read, server-owned record.

    relation_allowed is the current viewer->owner myprofile_links decision, not
    a value taken from a client or stored inside the Piece. Preview identity
    validation belongs to its server-side preview service; True is required.
    """
    user = _request(authenticated_user_id, operation)
    _, owner, state, visibility = _metadata(row)
    is_owner = user == owner
    if state == 'preview_draft':
        if not (is_owner and operation == 'preview_read' and preview_identity_valid is True
                and visibility == 'private' and type(row.get('preview_revision')) is int
                and row['preview_revision'] > 0):
            _fail()
        try:
            expiry = row.get('expires_at')
            expiry = datetime.fromisoformat(expiry.replace('Z', '+00:00')) if isinstance(expiry, str) else expiry
            clock = datetime.now(timezone.utc) if now is None else now
            if (not isinstance(expiry, datetime) or expiry.utcoffset() is None
                    or not isinstance(clock, datetime) or clock.utcoffset() is None):
                _fail()
            expired = expiry <= clock
        except (TypeError, ValueError, OverflowError):
            _fail()
        if expired:
            _fail('PIECE_PREVIEW_EXPIRED')
        return PieceAccessDecision(True)
    if operation == 'preview_read':
        _fail()
    if is_owner:
        if operation in _OWNER_OPERATIONS or operation in {'detail', 'read_marker'}:
            return PieceAccessDecision(True)
        if visibility == 'public' and operation in {'feed', 'public_profile'}:
            return PieceAccessDecision(True)
        _fail()  # no self-unread or self-resonance
    if (visibility == 'public' and relation_allowed is True
            and operation in _PUBLIC_OPERATIONS):
        return PieceAccessDecision(False, operation in {'read_marker', 'resonance'})
    _fail()


async def resolve_piece_access(*, authenticated_user_id: Any, piece_id: Any, operation: str,
                               load_record: Callable[[str], Awaitable[Mapping[str, Any] | None]],
                               check_relation: Callable[..., Awaitable[bool]],
                               preview_identity_valid: bool = False,
                               now: datetime | None = None) -> PieceAccessDecision:
    """Resolve current state and relationship without persisting a decision.

    Readers are injected trusted backend dependencies. check_relation must use
    the existing myprofile_links viewer_user_id -> owner_user_id direction.
    A second record read detects visibility changes during that lookup. This
    does not replace a transaction or promise race-free later reads/writes.
    Returns no Piece body, source, owner identity, hash or metrics.
    """
    user = _request(authenticated_user_id, operation)
    raw = piece_id[6:] if isinstance(piece_id, str) and piece_id.startswith('piece:') else piece_id
    rid = _uuid(raw)
    if rid is None:
        _fail()

    async def read():
        try:
            row = await load_record(rid)
        except Exception:
            _fail('PIECE_TEMPORARILY_UNAVAILABLE')
        metadata = _metadata(row)
        if metadata[0] != rid:
            _fail()
        return row, metadata

    row, (_, owner, state, visibility) = await read()
    relation_allowed = False
    if user != owner:
        if state != 'saved' or visibility != 'public' or operation not in _PUBLIC_OPERATIONS:
            _fail()
        try:
            relation_allowed = await check_relation(viewer_user_id=user, owner_user_id=owner)
        except Exception:
            _fail('PIECE_TEMPORARILY_UNAVAILABLE')
        if relation_allowed is not True:
            _fail()
        row, metadata = await read()
        if metadata[1] != owner:
            _fail()
    return require_piece_access(row, authenticated_user_id=user, operation=operation,
        relation_allowed=relation_allowed, preview_identity_valid=preview_identity_valid, now=now)
