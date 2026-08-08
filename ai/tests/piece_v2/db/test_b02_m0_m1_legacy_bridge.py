from __future__ import annotations

"""PCE-9A B02-A causal RED for M0/M1 migration ownership.

Authorized lifecycle:
  PCE9A_B02A_M0_M1_TRACKED_MIGRATION_AND_LEGACY_BRIDGE_CAUSAL_RED_FREEZE_ONLY

Covered release-blocking contracts:
  PCE7-R035 public.pieces must not change meaning before legacy/shared callers are exact0
  PCE7-R040 untracked migration or catalog drift must fail before DDL/data effects

The current valid RED is emitted from the test call only after the current
``COCOLON_PIECES_READ_TABLE`` caller set is proven to be the frozen exact6 set.
The future GREEN additionally requires the complete M0/M1 artifact set and an
actual disposable PostgreSQL database. Missing driver/database evidence is
non-credit and can never be reclassified as the causal RED or GREEN.
"""

import hashlib
import json
import os
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

import pytest


_REPO_ROOT = Path(__file__).resolve().parents[4]
_SERVICE_ROOT = _REPO_ROOT / "ai" / "services" / "ai_inference"

_RED_SIGNATURE = "PCE9A_B02A_M0_M1_TRACKED_MIGRATION_AND_LEGACY_BRIDGE_OWNER_ABSENT_RED"
_CALLER_SCOPE_DRIFT_STOP = "PCE9A_B02A_LEGACY_CALLER_SCOPE_DRIFT_STOP"
_CALLER_PREIMAGE_DRIFT_STOP = "PCE9A_B02A_LEGACY_CALLER_PREIMAGE_DRIFT_STOP"
_PARTIAL_MATERIALIZATION_STOP = "PCE9A_B02A_PARTIAL_M0_M1_MATERIALIZATION_STOP"
_ISOLATED_DB_NONCREDIT = "PCE9A_B02A_ISOLATED_DATABASE_UNAVAILABLE_NONCREDIT"
_DB_DRIVER_NONCREDIT = "PCE9A_B02A_POSTGRES_DRIVER_UNAVAILABLE_NONCREDIT"
_DB_EXECUTION_NONCREDIT = "PCE9A_B02A_POSTGRES_EXECUTION_FAILURE_NONCREDIT"

_BASELINE_HEAD = "7a10fc593b123cb9d9b02147c4b345894dba0c0b"
_BASELINE_TREE = "842715d588c0573f0de5411dae62b8b8bb22f3a4"
_PCE0_CATALOG_PACKET_VERSION = "pce0.current_supabase_piece_catalog.v2"
_PCE0_CATALOG_CAPTURED_AT_UTC = "2026-08-07T09:41:56.410491"
_PCE0_CATALOG_SHA256 = "2f51e5e6e4207a186aaacbeb355c07ade3b4f777960f3f46d1dbea9f8f9d810e"

_MIGRATION_ID = "20260808_001_piece_v2_legacy_read_bridge"
_MIGRATION_PATH = "supabase/migrations/20260808_001_piece_v2_legacy_read_bridge.sql"

_EXPECTED_CALLER_PREIMAGES = {
    "ai/services/ai_inference/astor_worker.py": "78ae6649346cc4c0f3dd126fee24c8752bc7ea1b",
    "ai/services/ai_inference/api_piece_runtime.py": "3b11ef5de990ced1e1388f7f45d389375a561e32",
    "ai/services/ai_inference/emlis_ai_readers.py": "f87152c592461cf2b593842c0969c394bdc77790",
    "ai/services/ai_inference/piece_generated_metrics.py": "4df0fbebc3da1dc1d0417ccd752749ae40c826bb",
    "ai/services/ai_inference/piece_generation_store.py": "ae2c4518c628a46bc3c09485c2c4ddb0912e1dab",
    "ai/services/ai_inference/piece_public_read_store.py": "174a75dcd0be160551422a58533299074c76d2b5",
}
_EXPECTED_CALLERS = frozenset(_EXPECTED_CALLER_PREIMAGES)

_REQUIRED_ARTIFACTS = {
    "readme": _REPO_ROOT / "supabase" / "migrations" / "README.md",
    "manifest": _REPO_ROOT / "supabase" / "migrations" / "manifest.json",
    "migration": _REPO_ROOT / _MIGRATION_PATH,
    "requirements": _REPO_ROOT / "requirements-piece-v2-test.txt",
    "conftest": _REPO_ROOT / "ai" / "tests" / "piece_v2" / "db" / "conftest.py",
}

_EXPECTED_COLUMNS = (
    "id",
    "public_id",
    "owner_user_id",
    "source_type",
    "status",
    "is_active",
    "question_id",
    "q_key",
    "topic_key",
    "category",
    "question",
    "answer",
    "content_json",
    "source_snapshot_id",
    "source_hash",
    "source_refs",
    "locked",
    "lock_note",
    "created_at",
    "updated_at",
    "published_at",
)

_COLUMN_DEFINITIONS = (
    "id uuid primary key",
    "public_id text",
    "owner_user_id uuid",
    "source_type text",
    "status text",
    "is_active boolean",
    "question_id integer",
    "q_key text",
    "topic_key text",
    "category text",
    "question text",
    "answer text",
    "content_json jsonb",
    "source_snapshot_id uuid",
    "source_hash text",
    "source_refs jsonb",
    "locked boolean",
    "lock_note text",
    "created_at timestamptz",
    "updated_at timestamptz",
    "published_at timestamptz",
)


class _ContractFailure(AssertionError):
    pass


def _fail(signature: str, detail: str = "") -> None:
    suffix = f":{detail}" if detail else ""
    pytest.fail(f"{signature}{suffix}", pytrace=False)


def _git_blob_sha1(path: Path) -> str:
    body = path.read_bytes()
    return hashlib.sha1(
        b"blob " + str(len(body)).encode("ascii") + b"\0" + body
    ).hexdigest()


def _discover_legacy_callers() -> frozenset[str]:
    found: set[str] = set()
    if not _SERVICE_ROOT.is_dir():
        _fail(_CALLER_SCOPE_DRIFT_STOP, "service_root_absent")
    for path in sorted(_SERVICE_ROOT.rglob("*.py")):
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            _fail(_CALLER_SCOPE_DRIFT_STOP, f"unreadable:{path.name}:{type(exc).__name__}")
        if "COCOLON_PIECES_READ_TABLE" in source:
            found.add(path.relative_to(_REPO_ROOT).as_posix())
    return frozenset(found)


def _artifact_presence() -> dict[str, bool]:
    return {name: path.is_file() for name, path in _REQUIRED_ARTIFACTS.items()}


def _require_current_red_preconditions(callers: frozenset[str]) -> None:
    if callers != _EXPECTED_CALLERS:
        missing = sorted(_EXPECTED_CALLERS - callers)
        extra = sorted(callers - _EXPECTED_CALLERS)
        _fail(
            _CALLER_SCOPE_DRIFT_STOP,
            f"missing={','.join(missing) or 'none'};extra={','.join(extra) or 'none'}",
        )


def _require_complete_artifact_set(presence: Mapping[str, bool]) -> None:
    present = sorted(name for name, exists in presence.items() if exists)
    if not present:
        _fail(_RED_SIGNATURE, f"missing_exact{len(_REQUIRED_ARTIFACTS)}")
    if len(present) != len(_REQUIRED_ARTIFACTS):
        missing = sorted(name for name, exists in presence.items() if not exists)
        _fail(
            _PARTIAL_MATERIALIZATION_STOP,
            f"present={','.join(present)};missing={','.join(missing)}",
        )


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise _ContractFailure(f"json_invalid:{path.name}:{type(exc).__name__}") from exc
    if not isinstance(value, dict):
        raise _ContractFailure(f"json_not_object:{path.name}")
    return value


def _validate_manifest(manifest: Mapping[str, Any], migration_sha256: str) -> None:
    assert manifest.get("schema_version") == "cocolon.piece.migration_manifest.v1"
    assert manifest.get("application_migration_identity") == "mashos-api.supabase.migrations.v1"
    assert manifest.get("automatic_progression") is False
    assert manifest.get("production_apply_authorized") is False

    baseline = manifest.get("catalog_baseline")
    assert isinstance(baseline, Mapping)
    assert baseline.get("repository_head") == _BASELINE_HEAD
    assert baseline.get("repository_tree") == _BASELINE_TREE
    assert baseline.get("packet_version") == _PCE0_CATALOG_PACKET_VERSION
    assert baseline.get("captured_at_utc") == _PCE0_CATALOG_CAPTURED_AT_UTC
    assert baseline.get("sha256") == _PCE0_CATALOG_SHA256
    assert baseline.get("public_mymodel_reflections_kind") == "table"
    assert baseline.get("public_pieces_kind") == "security_invoker_view"
    assert baseline.get("public_mymodel_reflections_read_state") == "absent"
    assert baseline.get("application_migration_relation_state") == "absent"

    preimages = manifest.get("legacy_caller_preimages")
    assert preimages == _EXPECTED_CALLER_PREIMAGES

    migrations = manifest.get("migrations")
    assert isinstance(migrations, list) and len(migrations) == 1
    entry = migrations[0]
    assert isinstance(entry, Mapping)
    assert entry.get("id") == _MIGRATION_ID
    assert entry.get("phase") == "M1_LEGACY_READ_BRIDGE"
    assert entry.get("path") == _MIGRATION_PATH
    assert entry.get("sha256") == migration_sha256
    assert entry.get("expected_catalog_sha256") == _PCE0_CATALOG_SHA256
    assert entry.get("production_applied") is False
    assert entry.get("destructive") is False
    assert entry.get("public_pieces_semantics_changed") is False


def _validate_readme(source: str) -> None:
    required = (
        "mashos-api.supabase.migrations.v1",
        "APPLIED_MIGRATIONS_ARE_IMMUTABLE",
        "PRODUCTION_APPLICATION_REQUIRES_SEPARATE_MASH_APPROVAL",
        "PCE0_CATALOG_SHA256",
        _PCE0_CATALOG_SHA256,
        "ROLLBACK_AND_POSTVERIFICATION_REQUIRED",
    )
    for marker in required:
        assert marker in source, f"readme_marker_absent:{marker}"


def _validate_requirements(source: str) -> None:
    lines = [
        line.strip()
        for line in source.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    assert lines, "requirements_empty"
    assert all("==" in line and not re.search(r"\s", line) for line in lines)
    lowered = [line.lower() for line in lines]
    assert any(line.startswith("pytest==") for line in lowered)
    assert any(line.startswith("psycopg[binary]==") for line in lowered)


def _validate_conftest(source: str) -> None:
    required = (
        "PIECE_V2_TEST_DATABASE_URL",
        "PIECE_V2_TEST_DATABASE_DISPOSABLE_ACK",
        "piece_v2_test",
        "PRODUCTION_DATABASE_PROHIBITED",
    )
    for marker in required:
        assert marker in source, f"conftest_marker_absent:{marker}"
    assert "SUPABASE_SERVICE_ROLE_KEY" not in source
    assert "SUPABASE_URL" not in source


def _validate_callers_rebound(callers: frozenset[str], manifest: Mapping[str, Any]) -> None:
    assert callers == frozenset(), "PCE7_R035_LEGACY_CALLER_NOT_EXACT0"
    assert manifest.get("legacy_caller_preimages") == _EXPECTED_CALLER_PREIMAGES
    for relpath in sorted(_EXPECTED_CALLERS):
        path = _REPO_ROOT / relpath
        assert path.is_file(), f"caller_absent:{relpath}"
        source = path.read_text(encoding="utf-8")
        assert "COCOLON_PIECES_READ_TABLE" not in source
        assert "COCOLON_MYMODEL_REFLECTIONS_READ_TABLE" in source
        assert "MYMODEL_REFLECTIONS_READ_TABLE" in source
        assert "mymodel_reflections_read" in source


def _validate_migration_sql(source: str) -> None:
    normalized = source.lower()
    required = (
        f"migration_id: {_MIGRATION_ID}",
        f"expected_pce0_catalog_sha256: {_PCE0_CATALOG_SHA256}",
        "create or replace view public.mymodel_reflections_read",
        "with (security_invoker = true)",
        "from public.mymodel_reflections",
        "public.pieces",
    )
    for marker in required:
        assert marker in normalized, f"migration_marker_absent:{marker}"

    prohibited_patterns = (
        r"\bcreate\s+(?:or\s+replace\s+)?view\s+public\.pieces\b",
        r"\bdrop\s+(?:view|table)\s+(?:if\s+exists\s+)?public\.pieces\b",
        r"\balter\s+(?:view|table)\s+public\.pieces\b",
        r"\balter\s+table\s+public\.mymodel_reflections\b",
        r"\bdrop\s+table\s+(?:if\s+exists\s+)?public\.mymodel_reflections\b",
        r"\btruncate\s+(?:table\s+)?public\.mymodel_reflections\b",
        r"\binsert\s+into\s+public\.mymodel_reflections\b",
        r"\bupdate\s+public\.mymodel_reflections\b",
        r"\bdelete\s+from\s+public\.mymodel_reflections\b",
        r"(?m)^\s*(?:begin|commit|rollback)\s*;",
    )
    for pattern in prohibited_patterns:
        assert re.search(pattern, normalized) is None, f"migration_prohibited:{pattern}"

    for column in _EXPECTED_COLUMNS:
        assert re.search(rf"\b{re.escape(column)}\b", normalized), f"column_absent:{column}"


def _database_contract() -> tuple[str, str]:
    url = str(os.getenv("PIECE_V2_TEST_DATABASE_URL") or "").strip()
    ack = str(os.getenv("PIECE_V2_TEST_DATABASE_DISPOSABLE_ACK") or "").strip()
    if not url or ack != "I_ACKNOWLEDGE_DISPOSABLE_DATABASE":
        _fail(_ISOLATED_DB_NONCREDIT, "url_or_ack_missing")
    parsed = urlparse(url)
    if parsed.scheme not in {"postgres", "postgresql"}:
        _fail(_ISOLATED_DB_NONCREDIT, "url_scheme_invalid")
    database_name = unquote(parsed.path.lstrip("/")).split("?", 1)[0]
    if not database_name.startswith("piece_v2_test"):
        _fail(_ISOLATED_DB_NONCREDIT, "database_name_not_disposable")
    return url, database_name


def _setup_current_catalog(cursor: Any, *, omit_published_at: bool = False) -> None:
    cursor.execute("drop view if exists public.mymodel_reflections_read")
    cursor.execute("drop view if exists public.pieces")
    cursor.execute("drop table if exists public.mymodel_reflections cascade")
    definitions = list(_COLUMN_DEFINITIONS)
    if omit_published_at:
        definitions = [item for item in definitions if not item.startswith("published_at ")]
    cursor.execute(
        "create table public.mymodel_reflections (" + ",".join(definitions) + ")"
    )
    columns = [
        name
        for name in _EXPECTED_COLUMNS
        if not (omit_published_at and name == "published_at")
    ]
    cursor.execute(
        "create view public.pieces with (security_invoker = true) as select "
        + ",".join(columns)
        + " from public.mymodel_reflections"
    )


def _view_definition(cursor: Any, relation: str) -> str:
    cursor.execute("select pg_get_viewdef(%s::regclass, true)", (relation,))
    row = cursor.fetchone()
    assert row and isinstance(row[0], str)
    return re.sub(r"\s+", " ", row[0]).strip()


def _view_options(cursor: Any, relation: str) -> tuple[str, ...]:
    cursor.execute("select coalesce(reloptions, array[]::text[]) from pg_class where oid=%s::regclass", (relation,))
    row = cursor.fetchone()
    assert row
    return tuple(row[0] or ())


def _view_columns(cursor: Any, name: str) -> tuple[str, ...]:
    cursor.execute(
        "select column_name from information_schema.columns "
        "where table_schema='public' and table_name=%s order by ordinal_position",
        (name,),
    )
    return tuple(row[0] for row in cursor.fetchall())


def _execute_isolated_db_contract(migration_sql: str) -> None:
    url, expected_database_name = _database_contract()
    try:
        import psycopg  # type: ignore
    except Exception as exc:  # pragma: no cover - environment-specific noncredit
        _fail(_DB_DRIVER_NONCREDIT, type(exc).__name__)

    try:
        connection = psycopg.connect(url)
    except Exception as exc:  # pragma: no cover - environment-specific noncredit
        _fail(_DB_EXECUTION_NONCREDIT, f"connect:{type(exc).__name__}")

    try:
        with connection.cursor() as cursor:
            cursor.execute("select current_database()")
            row = cursor.fetchone()
            if not row or row[0] != expected_database_name:
                _fail(_ISOLATED_DB_NONCREDIT, "connected_database_mismatch")

            _setup_current_catalog(cursor)
            pieces_before = _view_definition(cursor, "public.pieces")
            pieces_options_before = _view_options(cursor, "public.pieces")
            cursor.execute(migration_sql, prepare=False)

            assert _view_columns(cursor, "mymodel_reflections_read") == _EXPECTED_COLUMNS
            assert "security_invoker=true" in _view_options(
                cursor, "public.mymodel_reflections_read"
            )
            assert _view_definition(cursor, "public.pieces") == pieces_before
            assert _view_options(cursor, "public.pieces") == pieces_options_before
            cursor.execute(
                "insert into public.mymodel_reflections "
                "(id,public_id,source_type,status,is_active,question,answer,content_json) "
                "values ('00000000-0000-4000-8000-000000000001','reflection:test',"
                "'generated','ready',true,'q','a','{}'::jsonb)"
            )
            cursor.execute("select public_id from public.mymodel_reflections_read")
            assert cursor.fetchall() == [("reflection:test",)]
        connection.rollback()

        with connection.cursor() as cursor:
            _setup_current_catalog(cursor, omit_published_at=True)
            cursor.execute("savepoint before_piece_migration")
            failed = False
            try:
                cursor.execute(migration_sql, prepare=False)
            except Exception:
                failed = True
                cursor.execute("rollback to savepoint before_piece_migration")
            assert failed is True, "PCE7_R040_CATALOG_DRIFT_NOT_REJECTED"
            cursor.execute("select to_regclass('public.mymodel_reflections_read')")
            assert cursor.fetchone() == (None,)
        connection.rollback()
    except pytest.fail.Exception:
        raise
    except Exception as exc:
        _fail(_DB_EXECUTION_NONCREDIT, type(exc).__name__)
    finally:
        try:
            connection.rollback()
        finally:
            connection.close()


def test_b02a_m0_m1_tracked_migration_and_legacy_bridge_contract() -> None:
    """Freeze M0/M1 artifacts, exact6 caller cutover and actual-DB guards."""

    callers = _discover_legacy_callers()
    presence = _artifact_presence()

    if not any(presence.values()):
        _require_current_red_preconditions(callers)
        _require_complete_artifact_set(presence)
        raise AssertionError("unreachable")

    _require_complete_artifact_set(presence)

    migration_path = _REQUIRED_ARTIFACTS["migration"]
    migration_bytes = migration_path.read_bytes()
    migration_sha256 = hashlib.sha256(migration_bytes).hexdigest()
    migration_sql = migration_bytes.decode("utf-8")

    manifest = _read_json(_REQUIRED_ARTIFACTS["manifest"])
    _validate_manifest(manifest, migration_sha256)
    _validate_readme(_REQUIRED_ARTIFACTS["readme"].read_text(encoding="utf-8"))
    _validate_requirements(
        _REQUIRED_ARTIFACTS["requirements"].read_text(encoding="utf-8")
    )
    _validate_conftest(_REQUIRED_ARTIFACTS["conftest"].read_text(encoding="utf-8"))
    _validate_callers_rebound(callers, manifest)
    _validate_migration_sql(migration_sql)
    _execute_isolated_db_contract(migration_sql)

    assert _git_blob_sha1(migration_path)
