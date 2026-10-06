"""B3 native PostgreSQL tests. Synthetic-only, complete transaction rollback.

Uses the unchanged B2 disposable-DB boundary/fixtures. No production connection,
no migration history update, no mocked database and no successful skip fallback.
"""
from __future__ import annotations

import asyncio
from contextlib import contextmanager
from pathlib import Path
import runpy
import sys
from uuid import UUID, uuid4

import pytest

_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_ROOT / 'ai/services/ai_inference'))
_B2 = runpy.run_path(str(Path(__file__).with_name('test_b02_piece_v2_foundation.py')))
_M3 = _ROOT / 'supabase/migrations/20260808_003_piece_v2_rls_and_staging.sql'
_OWNER, _VIEWER = _B2['_OWNER'], _B2['_VIEWER']


@contextmanager
def _as_role(conn, role):
    from psycopg import sql
    with conn.transaction():
        conn.execute(sql.SQL('SET LOCAL ROLE {}').format(sql.Identifier(role)))
        yield
        conn.execute('RESET ROLE')


@pytest.fixture
def foundation():
    from psycopg import sql
    with _B2['_disposable_database']() as (conn, pg):
        for role in _B2['_ROLES']:
            if not conn.execute('SELECT 1 FROM pg_roles WHERE rolname=%s', (role,)).fetchone():
                conn.execute(sql.SQL('CREATE ROLE {} NOLOGIN NOBYPASSRLS').format(sql.Identifier(role)))
        assert conn.execute("SELECT rolbypassrls FROM pg_roles WHERE rolname='service_role'").fetchone() == (False,)
        conn.execute('CREATE TABLE public.mymodel_reflections (' + ','.join(_B2['_LEGACY_COLUMNS']) + ')')
        columns = ','.join(c.split()[0] for c in _B2['_LEGACY_COLUMNS'])
        conn.execute('CREATE VIEW public.pieces WITH (security_invoker=true) AS SELECT ' + columns + ' FROM public.mymodel_reflections')
        conn.execute('REVOKE ALL ON public.pieces FROM PUBLIC, anon, authenticated')
        conn.execute('GRANT SELECT ON public.pieces TO service_role')
        _B2['_insert'](conn, 'mymodel_reflections', dict(id=uuid4(), source_type='generated',
            question='SYNTHETIC_LEGACY_QUESTION', answer='SYNTHETIC_LEGACY_ANSWER'))
        conn.execute(_B2['_M1'].read_text())
        conn.execute(_B2['_M2'].read_text())
        yield conn, pg


def _saved(conn, visibility='private', owner=None):
    row = _B2['_record']()
    if owner is not None:
        row['owner_user_id'] = owner
        row['source_lineage']['source_input']['source_owner_user_id'] = str(owner)
    row.update(lifecycle_status='saved', visibility_scope=visibility,
               saved_at=_B2['_WHEN'], expires_at=None, save_idempotency_key_hash=uuid4().hex * 2)
    _B2['_insert'](conn, 'piece_records', row)
    return row


def test_b03_native_preconditions_and_legacy_preservation(foundation):
    conn, pg = foundation
    old = _B2['_legacy_identity'](conn)
    ddl = _M3.read_text()
    for drift in ('ALTER TABLE public.piece_records DISABLE ROW LEVEL SECURITY',
                  'GRANT SELECT ON public.piece_records TO authenticated',
                  'GRANT SELECT (piece_text) ON public.piece_records TO authenticated',
                  'CREATE POLICY unexpected ON public.piece_records FOR SELECT USING(true)'):
        with pytest.raises(pg.errors.RaiseException, match='PIECE_B3_PRECONDITION'):
            with conn.transaction():
                conn.execute(drift); conn.execute(ddl)
        assert conn.execute("SELECT to_regclass('public.pieces_v2_staging')").fetchone() == (None,)
    with pytest.raises(pg.errors.RaiseException, match='PIECE_B3_TARGET_EXISTS'):
        with conn.transaction():
            conn.execute('CREATE TABLE public.pieces_v2_staging (unrelated integer)'); conn.execute(ddl)
    conn.execute(ddl)
    with pytest.raises(pg.errors.RaiseException, match='PIECE_B3_TARGET_EXISTS'):
        with conn.transaction(): conn.execute(ddl)
    assert _B2['_legacy_identity'](conn) == old
    assert conn.execute('SELECT count(*) FROM public.piece_records').fetchone() == (0,)


def test_b03_native_service_only_select_no_client_or_service_dml(foundation):
    conn, pg = foundation
    conn.execute(_M3.read_text())
    for table in (*_B2['_TABLES'], 'pieces_v2_staging'):
        for role in _B2['_ROLES']:
            for privilege in ('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'TRUNCATE', 'REFERENCES', 'TRIGGER'):
                expected = role == 'service_role' and privilege == 'SELECT' and table in ('piece_records', 'pieces_v2_staging')
                assert conn.execute('SELECT has_table_privilege(%s,%s,%s)',
                    (role, 'public.' + table, privilege)).fetchone() == (expected,), (table, role, privilege)
            if role != 'service_role' or table not in ('piece_records', 'pieces_v2_staging'):
                with pytest.raises(pg.errors.InsufficientPrivilege):
                    with _as_role(conn, role): conn.execute('SELECT * FROM public.' + table)
    for table in _B2['_TABLES']:
        assert conn.execute('SELECT relrowsecurity,relforcerowsecurity FROM pg_class WHERE oid=%s::regclass',
                            ('public.' + table,)).fetchone() == (True, True)
    for role in _B2['_ROLES']:
        with pytest.raises(pg.errors.InsufficientPrivilege):
            with _as_role(conn, role): conn.execute("UPDATE public.piece_records SET visibility_scope='public'")
    policy = conn.execute("SELECT polcmd,polpermissive,pg_get_expr(polqual,polrelid) FROM pg_policy WHERE polrelid='public.piece_records'::regclass").fetchall()
    assert policy == [('r', True, 'true')]


def test_b03_native_staging_has_only_current_public_saved_projection(foundation):
    conn, pg = foundation
    conn.execute(_M3.read_text())
    public, private = _saved(conn, 'public'), _saved(conn)
    preview = _B2['_record'](); _B2['_insert'](conn, 'piece_records', preview)
    options = conn.execute("SELECT reloptions FROM pg_class WHERE oid='public.pieces_v2_staging'::regclass").fetchone()[0]
    assert set(options) == {'security_invoker=true', 'security_barrier=true'}
    cols = conn.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='pieces_v2_staging' ORDER BY ordinal_position").fetchall()
    assert [c[0] for c in cols] == ['piece_id','public_id','owner_user_id','format_type','piece_text',
        'piece_text_hash','visual_recipe','visual_recipe_hash','saved_at','row_version']
    with _as_role(conn, 'service_role'):
        visible = conn.execute('SELECT piece_id,piece_text,visual_recipe FROM public.pieces_v2_staging').fetchall()
        assert visible == [(public['id'], public['piece_text'], public['visual_recipe'])]
        # Service SELECT intentionally includes owner-private rows internally;
        # it is not a viewer authorization or an HTTP/public response.
        assert conn.execute('SELECT count(*) FROM public.piece_records').fetchone() == (3,)
    conn.execute("UPDATE public.piece_records SET visibility_scope='private',row_version=row_version+1 WHERE id=%s", (public['id'],))
    with _as_role(conn, 'service_role'):
        assert conn.execute('SELECT piece_id FROM public.pieces_v2_staging').fetchall() == []
    conn.execute("UPDATE public.piece_records SET visibility_scope='public',row_version=row_version+1 WHERE id=%s", (public['id'],))
    conn.execute('DELETE FROM public.piece_records WHERE id=%s', (public['id'],))
    with _as_role(conn, 'service_role'):
        assert conn.execute('SELECT piece_id FROM public.pieces_v2_staging').fetchall() == []


def test_b03_native_current_rows_and_viewer_relation_policy_have_no_write_effect(foundation):
    from piece_v2_access import PieceAccessError, resolve_piece_access
    conn, pg = foundation
    conn.execute(_M3.read_text())
    # Disposable representation of the existing relation owner; not a migration.
    conn.execute('CREATE TABLE public.myprofile_links (viewer_user_id uuid, owner_user_id uuid)')
    conn.execute('GRANT SELECT ON public.myprofile_links TO service_role')
    public, private = _saved(conn, 'public'), _saved(conn)
    calls = []
    async def load(piece_id):
        calls.append('record')
        with _as_role(conn, 'service_role'):
            result = conn.execute('SELECT to_jsonb(p) FROM public.piece_records p WHERE id=%s', (UUID(piece_id),)).fetchone()
        return result[0] if result else None
    async def relation(*, viewer_user_id, owner_user_id):
        calls.append('relation')
        with _as_role(conn, 'service_role'):
            return conn.execute('SELECT 1 FROM public.myprofile_links WHERE viewer_user_id=%s AND owner_user_id=%s',
                (UUID(viewer_user_id), UUID(owner_user_id))).fetchone() is not None
    def resolve(row, viewer=_VIEWER, operation='detail'):
        return asyncio.run(resolve_piece_access(authenticated_user_id=str(viewer) if viewer else None,
            piece_id=str(row['id']), operation=operation, load_record=load, check_relation=relation))
    assert resolve(private, _OWNER, 'owner_history').is_owner
    errors = []
    for row in (private, public, dict(id=uuid4())):
        with pytest.raises(PieceAccessError) as error: resolve(row)
        errors.append((error.value.status_code, error.value.to_public_error()))
    assert errors == [(404, {'code': 'PIECE_NOT_FOUND'})] * 3
    # Reverse relation is not sufficient.
    conn.execute('INSERT INTO public.myprofile_links VALUES (%s,%s)', (_OWNER, _VIEWER))
    with pytest.raises(PieceAccessError, match='^PIECE_NOT_FOUND$'): resolve(public)
    conn.execute('INSERT INTO public.myprofile_links VALUES (%s,%s)', (_VIEWER, _OWNER))
    assert not resolve(public).is_owner
    conn.execute('DELETE FROM public.myprofile_links WHERE viewer_user_id=%s', (_VIEWER,))
    with pytest.raises(PieceAccessError, match='^PIECE_NOT_FOUND$'): resolve(public)
    conn.execute('INSERT INTO public.myprofile_links VALUES (%s,%s)', (_VIEWER, _OWNER))
    conn.execute("UPDATE public.piece_records SET visibility_scope='private',row_version=row_version+1 WHERE id=%s", (public['id'],))
    with pytest.raises(PieceAccessError, match='^PIECE_NOT_FOUND$'): resolve(public)
    calls.clear()
    with pytest.raises(PieceAccessError, match='^PIECE_AUTH_REQUIRED$'): resolve(public, None)
    assert calls == []
    for table in _B2['_TABLES'][1:]:
        assert conn.execute('SELECT count(*) FROM public.' + table).fetchone() == (0,)
