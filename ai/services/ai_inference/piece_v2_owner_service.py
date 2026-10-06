"""B7 owner-only saved history/detail, disabled until Piece clean cutover.

Read the persisted canonical artifact without consulting its former source,
current plan, author or public feed. This grants no new safety approval and
never regenerates text, changes a recipe, writes metrics or consumes quota.
"""
from __future__ import annotations

import base64
import binascii
from datetime import datetime, timezone
import json
import re
from uuid import UUID

from piece_v2_access import require_piece_access
from piece_v2_contract import (
    PIECE_V2_CONTRACT_VERSIONS, PieceContractError, canonical_json_bytes,
    canonical_sha256_hex, validate_piece_text_binding,
)
from piece_v2_visual import validate_visual_recipe

OWNER_READ_STATUS = {
    'PIECE_REQUEST_INVALID': 400, 'PIECE_AUTH_REQUIRED': 401,
    'PIECE_NOT_FOUND': 404, 'PIECE_TEMPORARILY_UNAVAILABLE': 503,
}
_VERSIONS = ('piece_contract_version', 'export_contract_version',
             'render_interface_version', 'render_reproducibility_version')
_ARTIFACT_FIELDS = ('format_type', 'piece_text', 'piece_text_hash',
    'content_payload', 'content_payload_hash', 'visual_recipe',
    'visual_recipe_hash', 'renderer_version')
_COLUMNS = ('id', 'public_id', 'owner_user_id', 'lifecycle_status',
    'visibility_scope', 'row_version', 'saved_at', 'safety_state',
    *_VERSIONS, *_ARTIFACT_FIELDS)


def _fail(code='PIECE_TEMPORARILY_UNAVAILABLE'):
    raise PieceContractError(code) from None


def _uuid(value: object, code: str) -> str:
    try:
        if type(value) is not str:
            raise ValueError
        parsed = UUID(value)
        if not parsed.int:
            raise ValueError
        return str(parsed)
    except (ValueError, AttributeError):
        _fail(code)


def _timestamp(value: object) -> datetime:
    if type(value) is not str or len(value) > 64:
        raise ValueError
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.utcoffset() is None:
        raise ValueError
    return parsed.astimezone(timezone.utc)


def _boundary(row: dict) -> tuple[datetime, str]:
    return _timestamp(row['saved_at']), row['id']


def _cursor(owner: str, row: dict) -> str:
    # A continuation boundary, never an authorization token. Every read still
    # filters by the freshly authenticated owner. No signing secret is needed.
    value = [1, owner, _timestamp(row['saved_at']).isoformat(), row['id']]
    return base64.urlsafe_b64encode(canonical_json_bytes(value)).decode('ascii').rstrip('=')


def _history_request(owner: str, limit: object, cursor: object) -> tuple[int, tuple | None]:
    if type(limit) is not str or not re.fullmatch(r'[1-9][0-9]{0,2}', limit) or int(limit) > 100:
        _fail('PIECE_REQUEST_INVALID')
    if cursor is None:
        return int(limit), None
    try:
        if type(cursor) is not str or not re.fullmatch(r'[A-Za-z0-9_-]{1,512}', cursor):
            raise ValueError
        data = base64.b64decode(cursor + '=' * (-len(cursor) % 4), altchars=b'-_', validate=True)
        value = json.loads(data)
        if (type(value) is not list or len(value) != 4 or type(value[0]) is not int
                or value[0] != 1 or value[1] != owner):
            raise ValueError
        stamp = _timestamp(value[2])
        pid = _uuid(value[3], 'PIECE_REQUEST_INVALID')
        # Reject alternate encodings and normalize all filter values locally.
        if cursor != _cursor(owner, {'id': pid, 'saved_at': stamp.isoformat()}):
            raise ValueError
        return int(limit), (stamp, pid)
    except (ValueError, TypeError, UnicodeError, binascii.Error, OverflowError, RecursionError):
        _fail('PIECE_REQUEST_INVALID')


async def load_saved_records(params: dict) -> list:
    """Service-role transport; the service constructs all filters itself."""
    from supabase_client import sb_get
    response = await sb_get('/rest/v1/piece_records', params=params, timeout=8.0)
    if response.status_code != 200:
        _fail()
    value = response.json()
    if type(value) is not list:
        _fail()
    return value


def _project(row: dict, owner: str) -> dict:
    # Reuse B3's owner operation, not its public-detail relation exception.
    # Authorization precedes content validation, so another owner's private
    # row cannot become a corruption oracle if the upstream filter is broken.
    if (type(row) is not dict or row.get('lifecycle_status') != 'saved'
            or row.get('owner_user_id') != owner):
        _fail('PIECE_NOT_FOUND')
    try:
        require_piece_access(row, authenticated_user_id=owner, operation='owner_history')
        if row['id'] != _uuid(row['id'], 'PIECE_TEMPORARILY_UNAVAILABLE'):
            raise ValueError
        if (row['visibility_scope'] not in ('private', 'public')
                or row['row_version'] > 9223372036854775807
                or any(row[k] != PIECE_V2_CONTRACT_VERSIONS[k] for k in _VERSIONS)
                or row['safety_state'] not in ('ready', 'adjusted')
                or type(row['renderer_version']) is not str
                or not re.fullmatch(r'[A-Za-z0-9_.:\\-]{1,128}', row['renderer_version'])):
            raise ValueError
        _timestamp(row['saved_at'])
        payload = row['content_payload']
        validate_piece_text_binding(payload, row['piece_text'], row['piece_text_hash'])
        if (payload['format_type'] != row['format_type']
                or canonical_sha256_hex(payload) != row['content_payload_hash']):
            raise ValueError
        validate_visual_recipe(row['visual_recipe'], format_type=row['format_type'],
            language=payload['language'], expected_hash=row['visual_recipe_hash'])
        # Closed owner projection; never serialize a storage row wholesale.
        return {
            'api_contract_version': PIECE_V2_CONTRACT_VERSIONS['api_contract_version'],
            **{k: row[k] for k in _VERSIONS + _ARTIFACT_FIELDS},
            'piece_id': row['id'], 'public_id': row['public_id'],
            'lifecycle_status': 'saved', 'visibility_scope': row['visibility_scope'],
            'row_version': row['row_version'], 'saved_at': row['saved_at'],
            'content_status': row['safety_state'],
        }
    except (PieceContractError, KeyError, ValueError, TypeError, OverflowError):
        _fail()


class PieceOwnerService:
    def __init__(self, *, load_records=load_saved_records):
        self._load_records = load_records

    async def _read(self, params: dict) -> list:
        try:
            return json.loads(canonical_json_bytes(await self._load_records(params)))
        except Exception:
            # Reader/serialization failures are infrastructure failures, never
            # caller validation or a database provider's auth/not-found code.
            _fail()

    async def detail(self, *, authenticated_user_id: str, piece_id: str) -> dict:
        try:
            owner = _uuid(authenticated_user_id, 'PIECE_AUTH_REQUIRED')
            raw = piece_id[6:] if isinstance(piece_id, str) and piece_id.startswith('piece:') else piece_id
            pid = _uuid(raw, 'PIECE_NOT_FOUND')
            rows = await self._read({'select': ','.join(_COLUMNS),
                'owner_user_id': 'eq.' + owner, 'lifecycle_status': 'eq.saved',
                'id': 'eq.' + pid, 'limit': '2'})
            if type(rows) is not list or len(rows) > 1:
                _fail()
            if not rows or type(rows[0]) is not dict or rows[0].get('id') != pid:
                _fail('PIECE_NOT_FOUND')
            return _project(rows[0], owner)
        except PieceContractError as exc:
            _fail(exc.code if exc.code in OWNER_READ_STATUS else 'PIECE_TEMPORARILY_UNAVAILABLE')
        except Exception:
            _fail()

    async def history(self, *, authenticated_user_id: str, limit: str = '20',
                      cursor: str | None = None) -> dict:
        try:
            owner = _uuid(authenticated_user_id, 'PIECE_AUTH_REQUIRED')
            size, boundary = _history_request(owner, limit, cursor)
            params = {'select': ','.join(_COLUMNS), 'owner_user_id': 'eq.' + owner,
                'lifecycle_status': 'eq.saved', 'order': 'saved_at.desc,id.desc',
                'limit': str(size + 1)}
            if boundary is not None:
                stamp, pid = boundary[0].isoformat(), boundary[1]
                params['or'] = f'(saved_at.lt.{stamp},and(saved_at.eq.{stamp},id.lt.{pid}))'
            rows = await self._read(params)
            if type(rows) is not list or len(rows) > size + 1:
                _fail()
            items, previous = [], boundary
            for row in rows:
                try:
                    item = _project(row, owner)
                    current = _boundary(row)
                    if previous is not None and current >= previous:
                        _fail()
                    previous = current
                    items.append(item)
                except PieceContractError:
                    # A bad page fails as a whole; do not leak partial bodies,
                    # silently skip a row, or hide an upstream filter failure.
                    _fail()
            return {
                'api_contract_version': PIECE_V2_CONTRACT_VERSIONS['api_contract_version'],
                'items': items[:size],
                'next_cursor': _cursor(owner, rows[size-1]) if len(rows) > size else None,
            }
        except PieceContractError as exc:
            _fail(exc.code if exc.code in OWNER_READ_STATUS else 'PIECE_TEMPORARILY_UNAVAILABLE')
        except Exception:
            _fail()
