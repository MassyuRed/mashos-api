"""B2-B file candidate and native, rollback-only foundation regression.

The fixture tests validate only synthetic content/recipe preparation against
existing B1/B9. They are NOT SQL acceptance. The native test requires a real
acknowledged empty local PostgreSQL database and psycopg; absence is NONCREDIT,
never a skip, mock database, or successful migration. No commit is performed.
B3/B4 authorization, atomic lifecycle RPCs and saved-preview issuance are absent.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import runpy
import sys
from uuid import UUID, uuid4

import pytest

_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_ROOT / 'ai/services/ai_inference'))
from piece_v2_contract import (  # noqa: E402
    canonical_sha256_hex, reconstruct_piece_text, validate_piece_text_binding,
)
from piece_v2_visual import build_visual_recipe, validate_visual_recipe  # noqa: E402

_M1 = _ROOT / 'supabase/migrations/20260808_001_piece_v2_legacy_read_bridge.sql'
_M2 = _ROOT / 'supabase/migrations/20260808_002_piece_v2_foundation.sql'
_TABLES = (
    'piece_records', 'piece_quota_month_locks', 'piece_quota_consumptions',
    'piece_record_metrics', 'piece_record_reads', 'piece_record_resonances',
    'piece_export_receipts', 'piece_delete_receipts',
)
_ROLES = ('anon', 'authenticated', 'service_role')
_STAGES = ('normal_observation', 'pre_question_observation', 'refined_observation')
_OWNER = UUID('10000000-0000-4000-8000-000000000001')
_VIEWER = UUID('20000000-0000-4000-8000-000000000002')
_WHEN = datetime(2026, 9, 30, 15, 0, tzinfo=timezone.utc)  # October in JST.
# Same consumed projection as the existing M1 test; no real records are copied.
_LEGACY_COLUMNS = (
    'id uuid primary key', 'public_id text', 'owner_user_id uuid',
    'source_type text', 'status text', 'is_active boolean', 'question_id integer',
    'q_key text', 'topic_key text', 'category text', 'question text', 'answer text',
    'content_json jsonb', 'source_snapshot_id uuid', 'source_hash text',
    'source_refs jsonb', 'locked boolean', 'lock_note text',
    'created_at timestamptz', 'updated_at timestamptz', 'published_at timestamptz',
)


def _record(stage='normal_observation', fmt='quote'):
    source_id = 'synthetic-saved-input'
    commitment = 'sha256:' + hashlib.sha256(b'synthetic-source').hexdigest()
    observation = {
        'emlis_observation_stage': stage,
        'emlis_observation_result_identity': 'synthetic-terminal-result',
        'emlis_observation_result_state': 'terminal_success',
        'question_need_decision_identity': None if stage == _STAGES[0] else 'synthetic-question',
        'supplemental_answer_identity': None,
        'supplemental_answer_version': None,
        'supplemental_answer_bundle_commitment': None,
    }
    semantic = ['original_input']
    controls = ['emlis_observation_result']
    if stage != _STAGES[0]:
        controls.append('question_need_decision')
    if stage == _STAGES[2]:
        semantic.append('supplemental_answer')
        observation.update(supplemental_answer_identity='synthetic-answer',
            supplemental_answer_version='synthetic-answer.v1',
            supplemental_answer_bundle_commitment='sha256:' + 'b' * 64)
    lineage = {
        'handoff_contract_version': 'cocolon.cross_core.source_handoff.v1',
        'piece_source_lineage_version': 'piece.source_lineage.v1',
        'source_input': {
            'source_input_id': source_id, 'source_input_version': 'emlis.current_input_bundle.v1',
            'source_input_bundle_commitment': commitment,
            'source_owner_user_id': str(_OWNER), 'source_recorded_at': _WHEN.isoformat(),
        },
        'observation': observation, 'semantic_source_roles': semantic,
        'lineage_control_roles': controls,
        'piece_generation_eligibility': {
            'contract_version': 'piece.generation_eligibility.v1',
            'decision': 'eligible', 'reason_codes': [],
        },
        'body_free': True,
    }
    blocks = ['私は、一人で静かに考える時間を大切にしている。']
    if fmt != 'quote':
        blocks.append('私は、自分で納得して選びたい。')
    payload = {
        'schema_version': 'piece.content_payload.v1',
        'meaning_contract_version': 'piece.content_meaning.v1',
        'safety_contract_version': 'piece.public_safety_transformation.v1',
        'language': 'ja', 'format_type': fmt, 'title': None, 'body_blocks': blocks,
    }
    text = reconstruct_piece_text(payload)
    recipe = build_visual_recipe(fmt, tier='premium', language='ja', aspect_ratio='9:16')
    return {
        'id': uuid4(), 'owner_user_id': _OWNER, 'source_input_id': source_id,
        'source_input_version': 'emlis.current_input_bundle.v1',
        'source_input_bundle_commitment': commitment, 'source_lineage': lineage,
        'expires_at': datetime(2026, 10, 2, tzinfo=timezone.utc),
        'format_type': fmt, 'content_payload': payload,
        'content_payload_hash': canonical_sha256_hex(payload), 'piece_text': text,
        'piece_text_hash': hashlib.sha256(text.encode('utf-8')).hexdigest(),
        'safety_state': 'ready', 'visual_recipe': recipe,
        'visual_recipe_hash': canonical_sha256_hex(recipe),
        # Synthetic identity only; this does not assert a real renderer exists.
        'renderer_version': 'synthetic-test-renderer.v1',
    }


@pytest.mark.parametrize('stage', _STAGES)
@pytest.mark.parametrize('fmt', ('quote', 'short_essay', 'declaration'))
def test_b02_synthetic_fixture_uses_existing_content_and_visual_owners(stage, fmt):
    row = _record(stage, fmt)
    assert validate_piece_text_binding(row['content_payload'], row['piece_text'],
                                     row['piece_text_hash']) == row['piece_text']
    assert validate_visual_recipe(row['visual_recipe'], format_type=fmt, language='ja',
        expected_hash=row['visual_recipe_hash']) == row['visual_recipe']
    assert row['source_lineage']['body_free'] is True
    assert row['source_lineage']['source_input']['source_owner_user_id'] == str(row['owner_user_id'])
    assert len(row['source_lineage']['semantic_source_roles']) == (2 if stage == _STAGES[2] else 1)


@contextmanager
def _disposable_database():
    url = os.environ.get('PIECE_V2_TEST_DATABASE_URL', '').strip()
    if not url:
        pytest.fail('PIECE_B2B_ISOLATED_DATABASE_UNAVAILABLE_NONCREDIT', pytrace=False)
    # Reuse the unchanged B2-A URL boundary even when this test is invoked alone.
    boundary = runpy.run_path(str(Path(__file__).with_name('conftest.py')))
    boundary['validate_disposable_database_url'](url,
        os.environ.get('PIECE_V2_TEST_DATABASE_DISPOSABLE_ACK', '').strip())
    try:
        import psycopg
    except ImportError:
        pytest.fail('PIECE_B2B_POSTGRES_DRIVER_UNAVAILABLE_NONCREDIT', pytrace=False)
    try:
        conn = psycopg.connect(url, connect_timeout=3, autocommit=False)
    except psycopg.OperationalError:
        pytest.fail('PIECE_B2B_POSTGRES_CONNECTION_UNAVAILABLE_NONCREDIT', pytrace=False)
    empty_verified = False
    try:
        assert conn.info.dbname.startswith('piece_v2_test'), 'DISPOSABLE_DATABASE_REQUIRED'
        assert conn.info.server_version >= 150000, 'POSTGRESQL_15_REQUIRED'
        assert conn.execute('SELECT rolsuper FROM pg_roles WHERE rolname=current_user').fetchone() == (True,), 'DISPOSABLE_TEST_SUPERUSER_REQUIRED'
        assert conn.execute("SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relkind IN ('r','p','v','m','f','S')").fetchone() == (0,), 'EMPTY_DISPOSABLE_DATABASE_REQUIRED'
        empty_verified = True
        yield conn, psycopg
    finally:
        try:
            conn.rollback()
            if empty_verified:
                assert conn.execute("SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relkind IN ('r','p','v','m','f','S')").fetchone() == (0,), 'ROLLBACK_LEFT_FIXTURE_OBJECTS'
                conn.rollback()
        finally:
            conn.close()


def _insert(conn, table, values):
    from psycopg import sql
    from psycopg.types.json import Jsonb
    fields = list(values)
    query = sql.SQL('INSERT INTO public.{} ({}) VALUES ({})').format(
        sql.Identifier(table), sql.SQL(',').join(map(sql.Identifier, fields)),
        sql.SQL(',').join(sql.Placeholder() for _ in fields))
    conn.execute(query, [Jsonb(values[k]) if isinstance(values[k], (dict, list)) else values[k] for k in fields])


def _legacy_identity(conn):
    return (
        conn.execute('SELECT id,source_type,question,answer FROM public.mymodel_reflections ORDER BY id').fetchall(),
        conn.execute("SELECT relname,relowner,reloptions,relacl::text,pg_get_viewdef(oid,false) FROM pg_class WHERE oid IN ('public.pieces'::regclass,'public.mymodel_reflections_read'::regclass) ORDER BY relname").fetchall(),
    )


def test_b02_foundation_native_postgresql():
    """Real SQL: schema, binding, access, retention, preconditions and rollback.

    One native acceptance test, not a collection of claimed database successes
    when no database is available. Every fixture object/data/role is rolled back.
    """
    with _disposable_database() as (conn, pg):
        from psycopg import sql
        for role in _ROLES:
            if not conn.execute('SELECT 1 FROM pg_roles WHERE rolname=%s', (role,)).fetchone():
                conn.execute(sql.SQL('CREATE ROLE {} NOLOGIN').format(sql.Identifier(role)))
        conn.execute('CREATE TABLE public.mymodel_reflections (' + ','.join(_LEGACY_COLUMNS) + ')')
        columns = ','.join(c.split()[0] for c in _LEGACY_COLUMNS)
        conn.execute('CREATE VIEW public.pieces WITH (security_invoker=true) AS SELECT ' + columns + ' FROM public.mymodel_reflections')
        conn.execute('REVOKE ALL ON public.pieces FROM PUBLIC, anon, authenticated')
        conn.execute('GRANT SELECT ON public.pieces TO service_role')
        _insert(conn, 'mymodel_reflections', {'id': uuid4(), 'source_type': 'generated',
            'question': 'synthetic legacy question', 'answer': 'synthetic legacy answer'})
        conn.execute(_M1.read_text(encoding='utf-8'))
        before = _legacy_identity(conn)
        ddl = _M2.read_text(encoding='utf-8')

        # Missing prerequisite and pre-existing target both stop before M2 DDL.
        with pytest.raises(pg.errors.RaiseException, match='PIECE_M2_PRECONDITION'):
            with conn.transaction():
                conn.execute('DROP VIEW public.mymodel_reflections_read')
                conn.execute(ddl)
        with pytest.raises(pg.errors.RaiseException, match='PIECE_M2_TARGET_EXISTS'):
            with conn.transaction():
                conn.execute('CREATE TABLE public.piece_export_receipts (synthetic_marker integer)')
                conn.execute(ddl)
        assert all(conn.execute('SELECT to_regclass(%s)', ('public.' + t,)).fetchone() == (None,) for t in _TABLES)
        conn.execute(ddl)
        assert _legacy_identity(conn) == before
        with pytest.raises(pg.errors.RaiseException, match='PIECE_M2_TARGET_EXISTS'):
            with conn.transaction():
                conn.execute(ddl)

        for table in _TABLES:
            assert conn.execute('SELECT relrowsecurity,relforcerowsecurity FROM pg_class WHERE oid=%s::regclass', ('public.' + table,)).fetchone() == (True, True)
            assert conn.execute('SELECT count(*) FROM pg_policy WHERE polrelid=%s::regclass', ('public.' + table,)).fetchone() == (0,)
            for role in _ROLES:
                for privilege in ('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'TRUNCATE', 'REFERENCES', 'TRIGGER'):
                    assert conn.execute('SELECT has_table_privilege(%s,%s,%s)', (role, 'public.' + table, privilege)).fetchone() == (False,), (table, role, privilege)
                with pytest.raises(pg.errors.InsufficientPrivilege):
                    with conn.transaction():
                        conn.execute(sql.SQL('SET LOCAL ROLE {}').format(sql.Identifier(role)))
                        conn.execute(sql.SQL('SELECT * FROM public.{}').format(sql.Identifier(table)))
        forbidden = {'question','answer','title','raw_input','supplemental_answer_body',
                     'emlis_body','analysis_body','png_bytes','recipient','local_path'}
        for table in _TABLES:
            cols = conn.execute("SELECT column_name,data_type FROM information_schema.columns WHERE table_schema='public' AND table_name=%s", (table,)).fetchall()
            assert not forbidden.intersection(c[0] for c in cols)
            assert not any(t == 'bytea' for _, t in cols)
            if table != 'piece_records':
                assert not any(t in ('json', 'jsonb') for _, t in cols)

        # Real round-trips for each source stage/format; same input is nonunique.
        for stage in _STAGES:
            for fmt in ('quote', 'short_essay', 'declaration'):
                row = _record(stage, fmt)
                _insert(conn, 'piece_records', row)
                stored = conn.execute('SELECT public_id,visibility_scope,lifecycle_status,piece_text,piece_text_hash,source_lineage,content_payload,visual_recipe FROM public.piece_records WHERE id=%s', (row['id'],)).fetchone()
                assert stored == ('piece:' + str(row['id']), 'private', 'preview_draft',
                    row['piece_text'], row['piece_text_hash'], row['source_lineage'],
                    row['content_payload'], row['visual_recipe'])

        invalid_rows = []
        for key, value in (
            ('visibility_scope', 'unknown'), ('visibility_scope', 'public'),
            ('lifecycle_status', 'saved'), ('expires_at', None),
            ('piece_text_hash', '0' * 64), ('piece_text', 'different text'),
            ('preview_revision', 0), ('row_version', 0), ('safety_state', 'unavailable'),
            ('format_type', 'question_answer'), ('piece_contract_version', 'piece.core.v1'),
        ):
            row = _record(); row[key] = value; invalid_rows.append(row)
        for mutation in ('missing_owner', 'other_owner', 'raw_body', 'false_body_free',
                         'wrong_source', 'nonterminal', 'extra_supplemental', 'missing_question',
                         'same_source_answer', 'missing_supplemental'):
            row = _record(_STAGES[2] if mutation in ('same_source_answer','missing_supplemental') else
                          _STAGES[1] if mutation == 'missing_question' else _STAGES[0])
            lineage = row['source_lineage']; inp = lineage['source_input']; obs = lineage['observation']
            if mutation == 'missing_owner': del inp['source_owner_user_id']
            elif mutation == 'other_owner': inp['source_owner_user_id'] = str(_VIEWER)
            elif mutation == 'raw_body': lineage['raw_input'] = 'synthetic forbidden body'
            elif mutation == 'false_body_free': lineage['body_free'] = False
            elif mutation == 'wrong_source': inp['source_input_id'] = 'different-source'
            elif mutation == 'nonterminal': obs['emlis_observation_result_state'] = 'terminal_nonadmitting'
            elif mutation == 'extra_supplemental': obs['supplemental_answer_identity'] = 'unexpected'
            elif mutation == 'missing_question': obs['question_need_decision_identity'] = None
            elif mutation == 'same_source_answer': obs['supplemental_answer_identity'] = row['source_input_id']
            else: obs['supplemental_answer_bundle_commitment'] = None
            invalid_rows.append(row)
        for mutation in ('body_object', 'empty_body', 'extra_content', 'extra_recipe', 'extra_theme'):
            row = _record()
            if mutation == 'body_object': row['content_payload']['body_blocks'] = [{'raw_input': 'synthetic'}]
            elif mutation == 'empty_body': row['content_payload']['body_blocks'] = []
            elif mutation == 'extra_content': row['content_payload']['raw_input'] = 'synthetic'
            elif mutation == 'extra_recipe': row['visual_recipe']['raw_input'] = 'synthetic'
            else: row['visual_recipe']['theme']['raw_input'] = 'synthetic'
            invalid_rows.append(row)
        for row in invalid_rows:
            with pytest.raises(pg.errors.CheckViolation):
                with conn.transaction():
                    _insert(conn, 'piece_records', row)

        row = _record(); key = 'c' * 64
        row.update(lifecycle_status='saved', saved_at=_WHEN, expires_at=None,
                   save_idempotency_key_hash=key, visibility_scope='public')
        _insert(conn, 'piece_records', row)
        quota = {'owner_user_id': _OWNER, 'piece_id': row['id'], 'month_key': '2026-10',
                 'subscription_tier_at_consumption': 'premium', 'consumed_at': _WHEN,
                 'save_idempotency_key_hash': key}
        _insert(conn, 'piece_quota_consumptions', quota)
        for bad in (dict(quota, save_idempotency_key_hash='d' * 64), dict(quota, piece_id=uuid4())):
            with pytest.raises(pg.errors.UniqueViolation):
                with conn.transaction(): _insert(conn, 'piece_quota_consumptions', bad)
        with pytest.raises(pg.errors.CheckViolation):
            with conn.transaction():
                _insert(conn, 'piece_quota_consumptions', dict(quota, piece_id=uuid4(),
                    save_idempotency_key_hash='d' * 64, month_key='2026-09'))
        _insert(conn, 'piece_record_metrics', {'piece_id': row['id']})
        _insert(conn, 'piece_record_reads', {'piece_id': row['id'], 'viewer_user_id': _VIEWER})
        _insert(conn, 'piece_record_resonances', {'piece_id': row['id'],
            'owner_user_id': _OWNER, 'viewer_user_id': _VIEWER})
        with pytest.raises(pg.errors.CheckViolation):
            with conn.transaction():
                _insert(conn, 'piece_record_resonances', {'piece_id': row['id'],
                    'owner_user_id': _OWNER, 'viewer_user_id': _OWNER})
        with pytest.raises(pg.errors.ForeignKeyViolation):
            with conn.transaction():
                _insert(conn, 'piece_record_resonances', {'piece_id': row['id'],
                    'owner_user_id': _VIEWER, 'viewer_user_id': uuid4()})
        receipt = {'owner_user_id': _OWNER, 'piece_id': row['id'],
                   'idempotency_key_hash': 'e' * 64, 'outcome': 'succeeded'}
        _insert(conn, 'piece_delete_receipts', receipt)
        _insert(conn, 'piece_export_receipts', dict(receipt,
            piece_text_hash=row['piece_text_hash'], visual_recipe_hash=row['visual_recipe_hash']))
        for table in ('piece_export_receipts', 'piece_delete_receipts'):
            bad = dict(receipt, idempotency_key_hash='f' * 64, outcome='failed', error_code='/tmp/private-body.png')
            if table == 'piece_export_receipts':
                bad.update(piece_text_hash=row['piece_text_hash'], visual_recipe_hash=row['visual_recipe_hash'])
            with pytest.raises(pg.errors.CheckViolation):
                with conn.transaction(): _insert(conn, table, bad)
        conn.execute('DELETE FROM public.piece_records WHERE id=%s', (row['id'],))
        for table in ('piece_record_metrics','piece_record_reads','piece_record_resonances'):
            assert conn.execute(sql.SQL('SELECT count(*) FROM public.{} WHERE piece_id=%s').format(sql.Identifier(table)), (row['id'],)).fetchone() == (0,)
        for table in ('piece_quota_consumptions','piece_export_receipts','piece_delete_receipts'):
            assert conn.execute(sql.SQL('SELECT count(*) FROM public.{} WHERE piece_id=%s').format(sql.Identifier(table)), (row['id'],)).fetchone() == (1,)
        assert _legacy_identity(conn) == before
        # Exiting the context rolls back ALL fixtures, roles, M1, M2 and rows.
