"""B3 service policy tests with synthetic records; not registered HTTP routes.

Relation/record readers below are in-process fixtures, not live Supabase. The
same policy is also exercised against real SQL rows by the companion DB test.
"""
from __future__ import annotations

import asyncio
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import importlib.util
from pathlib import Path
import sys
from uuid import UUID

import pytest

_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_ROOT / 'ai/services/ai_inference'))
_OWNER = '10000000-0000-4000-8000-000000000001'
_VIEWER = '20000000-0000-4000-8000-000000000002'
_ID = '30000000-0000-4000-8000-000000000003'
_NOW = datetime(2026, 10, 6, tzinfo=timezone.utc)


@pytest.fixture
def access():
    # Keep absence a call-phase capability assertion, not an import failure.
    assert importlib.util.find_spec('piece_v2_access') is not None, 'B3_ACCESS_OWNER_NOT_IMPLEMENTED'
    import piece_v2_access
    return piece_v2_access


def _row(state='saved', visibility='private'):
    return dict(id=_ID, public_id='piece:' + _ID, owner_user_id=_OWNER,
                piece_contract_version='piece.record.v2', lifecycle_status=state,
                visibility_scope=visibility, row_version=1, preview_revision=1,
                expires_at=(_NOW + timedelta(hours=1)).isoformat(),
                piece_text='SYNTHETIC_PRIVATE_PIECE_CANARY', source_lineage={'raw_input': 'NEVER_RETURN'})


def _deny(access, row, viewer=_VIEWER, operation='detail', **kwargs):
    with pytest.raises(access.PieceAccessError) as error:
        access.require_piece_access(row, authenticated_user_id=viewer,
                                    operation=operation, now=_NOW, **kwargs)
    return error.value


@pytest.mark.parametrize('visibility', ['private', 'public', None])
@pytest.mark.parametrize('operation', ['owner_history', 'detail', 'export', 'reexport', 'set_visibility', 'delete'])
def test_owner_saved_access_is_independent_of_viewer_relation(access, visibility, operation):
    row = _row(visibility=visibility)
    before = deepcopy(row)
    decision = access.require_piece_access(row, authenticated_user_id=_OWNER,
        operation=operation, now=_NOW)
    assert decision.is_owner is True
    assert decision.public_state_write_allowed is False
    assert row == before
    assert not hasattr(decision, 'piece_text')


@pytest.mark.parametrize('operation', ['detail', 'feed', 'public_profile', 'unread', 'read_marker', 'resonance'])
def test_allowed_nonowner_requires_saved_public(access, operation):
    result = access.require_piece_access(_row(visibility='public'), authenticated_user_id=_VIEWER,
        operation=operation, relation_allowed=True, now=_NOW)
    assert result.is_owner is False
    assert result.public_state_write_allowed == (operation in {'read_marker', 'resonance'})
    for state in ('preview_draft', 'cancelled', 'rejected', 'expired', 'deleted'):
        assert _deny(access, _row(state, 'public'), operation=operation, relation_allowed=True).code == 'PIECE_NOT_FOUND'
    for visibility in ('private', None):
        assert _deny(access, _row(visibility=visibility), operation=operation, relation_allowed=True).code == 'PIECE_NOT_FOUND'


@pytest.mark.parametrize('relation', [False, None, 0, 1, 'true', {}, []])
def test_relation_must_be_current_explicit_boolean(access, relation):
    assert _deny(access, _row(visibility='public'), relation_allowed=relation).code == 'PIECE_NOT_FOUND'


@pytest.mark.parametrize('viewer', [None, '', 'service_role', True, {}, 123, '00000000-0000-0000-0000-000000000000'])
def test_service_role_or_missing_auth_is_not_a_user_decision(access, viewer):
    error = _deny(access, _row(visibility='public'), viewer=viewer, relation_allowed=True)
    assert (error.status_code, error.to_public_error()) == (401, {'code': 'PIECE_AUTH_REQUIRED'})


def test_nonowner_concealment_is_identical(access):
    candidates = [None, _row(), _row('deleted', 'public'), _row('preview_draft', 'public'),
                  _row(visibility='public'), _row(visibility='unknown')]
    errors = [_deny(access, r) for r in candidates]
    assert {(e.status_code, e.code, str(e)) for e in errors} == {(404, 'PIECE_NOT_FOUND', 'PIECE_NOT_FOUND')}
    assert all(e.to_public_error() == {'code': 'PIECE_NOT_FOUND'} for e in errors)
    assert all(e.detail is None for e in errors)


@pytest.mark.parametrize('operation', ['owner_history', 'export', 'reexport', 'set_visibility', 'delete', 'preview_read'])
def test_allowed_viewer_cannot_use_owner_operations(access, operation):
    assert _deny(access, _row(visibility='public'), operation=operation, relation_allowed=True).status_code == 404


def test_owner_private_never_becomes_public_projection_or_public_interaction(access):
    for operation in ('feed', 'public_profile', 'unread', 'resonance'):
        assert _deny(access, _row(), viewer=_OWNER, operation=operation).status_code == 404
    for operation in ('feed', 'public_profile', 'read_marker'):
        decision = access.require_piece_access(_row(visibility='public'), authenticated_user_id=_OWNER,
            operation=operation, now=_NOW)
        assert decision.public_state_write_allowed is False
    assert _deny(access, _row(visibility='public'), viewer=_OWNER, operation='resonance').status_code == 404


def test_preview_is_owner_identity_and_expiry_bound(access):
    row = _row('preview_draft')
    result = access.require_piece_access(row, authenticated_user_id=_OWNER, operation='preview_read',
        preview_identity_valid=True, now=_NOW)
    assert result.is_owner and not result.public_state_write_allowed
    for proof in (False, None, 1, 'true'):
        assert _deny(access, row, viewer=_OWNER, operation='preview_read', preview_identity_valid=proof).status_code == 404
    assert _deny(access, row, operation='preview_read', preview_identity_valid=True).status_code == 404
    row['expires_at'] = _NOW.isoformat()
    assert _deny(access, row, viewer=_OWNER, operation='preview_read', preview_identity_valid=True).code == 'PIECE_PREVIEW_EXPIRED'
    row['expires_at'] = 'not-a-date'
    assert _deny(access, row, viewer=_OWNER, operation='preview_read', preview_identity_valid=True).code == 'PIECE_NOT_FOUND'


def test_missing_visibility_defaults_private_unknown_is_never_public(access):
    from piece_v2_contract import normalize_visibility_scope, PieceContractError
    assert normalize_visibility_scope(None) == 'private'
    with pytest.raises(PieceContractError):
        normalize_visibility_scope('unknown')
    row = _row(); del row['visibility_scope']
    assert _deny(access, row, relation_allowed=True).code == 'PIECE_NOT_FOUND'
    assert access.require_piece_access(row, authenticated_user_id=_OWNER, operation='detail').is_owner


@pytest.mark.parametrize('field,value', [
    ('piece_contract_version', 'piece.core.v1'), ('public_id', 'reflection:' + _ID),
    ('public_id', 'piece:' + _VIEWER), ('owner_user_id', 'service_role'),
    ('row_version', 0), ('row_version', True), ('lifecycle_status', ['saved']),
    ('visibility_scope', {'public': True}),
])
def test_invalid_or_legacy_record_is_not_admitted(access, field, value):
    row = _row(visibility='public'); row[field] = value
    assert _deny(access, row, viewer=_OWNER, relation_allowed=True).code == 'PIECE_NOT_FOUND'


def test_resolver_checks_auth_before_loading_and_never_trusts_service_identity(access):
    calls = []
    async def load(piece_id):
        calls.append('load'); return _row(visibility='public')
    async def relation(*, viewer_user_id, owner_user_id):
        calls.append('relation'); return True
    with pytest.raises(access.PieceAccessError) as error:
        asyncio.run(access.resolve_piece_access(authenticated_user_id='service_role', piece_id=_ID,
            operation='detail', load_record=load, check_relation=relation))
    assert error.value.code == 'PIECE_AUTH_REQUIRED'
    assert calls == []


def test_resolver_uses_fresh_state_and_relation_without_writes(access):
    row, allowed, calls = _row(visibility='public'), True, []
    async def load(piece_id):
        calls.append(('load', piece_id)); return deepcopy(row)
    async def relation(*, viewer_user_id, owner_user_id):
        calls.append(('relation', viewer_user_id, owner_user_id)); return allowed
    def resolve(viewer=_VIEWER, operation='detail'):
        return asyncio.run(access.resolve_piece_access(authenticated_user_id=viewer,
            piece_id='piece:' + _ID, operation=operation, load_record=load, check_relation=relation))
    assert not resolve().is_owner
    assert calls == [('load', _ID), ('relation', _VIEWER, _OWNER), ('load', _ID)]
    allowed = False
    with pytest.raises(access.PieceAccessError, match='^PIECE_NOT_FOUND$'): resolve()
    allowed = True; row['visibility_scope'] = 'private'
    calls.clear()
    with pytest.raises(access.PieceAccessError, match='^PIECE_NOT_FOUND$'): resolve()
    assert calls == [('load', _ID)]
    assert resolve(_OWNER, 'owner_history').is_owner
    row['visibility_scope'] = 'public'; row['lifecycle_status'] = 'deleted'
    with pytest.raises(access.PieceAccessError, match='^PIECE_NOT_FOUND$'): resolve()


def test_resolver_rechecks_record_after_relation_lookup(access):
    row = _row(visibility='public')
    async def load(piece_id): return deepcopy(row)
    async def relation(**kwargs):
        row['visibility_scope'] = 'private'; return True
    with pytest.raises(access.PieceAccessError, match='^PIECE_NOT_FOUND$'):
        asyncio.run(access.resolve_piece_access(authenticated_user_id=_VIEWER, piece_id=_ID,
            operation='detail', load_record=load, check_relation=relation))


def test_resolver_rejects_wrong_record_and_dependency_errors_body_free(access):
    async def wrong(piece_id): return dict(_row(visibility='public'), id=_VIEWER, public_id='piece:' + _VIEWER)
    async def relation(**kwargs): return True
    async def broken(piece_id): raise RuntimeError('SYNTHETIC_PRIVATE_BODY_DO_NOT_FORWARD')
    for loader, code in [(wrong, 'PIECE_NOT_FOUND'), (broken, 'PIECE_TEMPORARILY_UNAVAILABLE')]:
        with pytest.raises(access.PieceAccessError) as error:
            asyncio.run(access.resolve_piece_access(authenticated_user_id=_VIEWER, piece_id=_ID,
                operation='detail', load_record=loader, check_relation=relation))
        assert error.value.code == code
        assert str(error.value) == code
        assert error.value.__suppress_context__ is True


def test_invalid_operation_fails_before_io(access):
    async def fail(*args, **kwargs): pytest.fail('unexpected I/O')
    with pytest.raises(access.PieceAccessError, match='^PIECE_REQUEST_INVALID$'):
        asyncio.run(access.resolve_piece_access(authenticated_user_id=_OWNER, piece_id=_ID,
            operation='arbitrary', load_record=fail, check_relation=fail))
