from __future__ import annotations

"""PCE-9A B02-A M0/M1 causal RED for the tracked migration owner.

Authorized first lifecycle:
  PCE9A_B02A_M0_M1_MIGRATION_PREFLIGHT_CAUSAL_RED_FREEZE_ONLY

Covered release-blocking contracts:
  PCE7-R035 public.pieces must not change semantics while legacy/shared callers remain
  PCE7-R040 missing/untracked migration identity or catalog guard fails before DDL

This test is collection-safe.  Before the separately approved implementation exists,
the test call verifies the frozen current caller set and then emits one stable RED.
Caller-set drift, a partial migration packet, import/collection failure, or the absence
of an isolated database are never reclassified as this RED.
"""

import json
import re
from collections.abc import Mapping
from pathlib import Path

import pytest


_REPO_ROOT = Path(__file__).resolve().parents[4]
_SERVICE_ROOT = _REPO_ROOT / "ai" / "services" / "ai_inference"

_OLD_READ_TABLE_ENV = "COCOLON_PIECES_READ_TABLE"
_BRIDGE_RELATION_TOKEN = "mymodel_reflections_read"
_PCE0_CATALOG_SHA256 = (
    "2f51e5e6e4207a186aaacbeb355c07ade3b4f777960f3f46d1dbea9f8f9d810e"
)
_MANIFEST_SCHEMA = "cocolon.supabase.application_migration_manifest.v1"
_MIGRATION_ID = "20260808_001_piece_v2_legacy_read_bridge"
_MIGRATION_PATH = (
    "supabase/migrations/20260808_001_piece_v2_legacy_read_bridge.sql"
)

_EXPECTED_CURRENT_CALLERS = frozenset(
    {
        "ai/services/ai_inference/api_piece_runtime.py",
        "ai/services/ai_inference/astor_worker.py",
        "ai/services/ai_inference/emlis_ai_readers.py",
        "ai/services/ai_inference/piece_generated_metrics.py",
        "ai/services/ai_inference/piece_generation_store.py",
        "ai/services/ai_inference/piece_public_read_store.py",
    }
)

_REQUIRED_IMPLEMENTATION_PATHS = (
    "supabase/migrations/README.md",
    "supabase/migrations/manifest.json",
    _MIGRATION_PATH,
    "requirements-piece-v2-test.txt",
    "ai/tests/piece_v2/db/conftest.py",
)

_RED_SIGNATURE = (
    "PCE9A_B02A_M0_M1_TRACKED_MIGRATION_AND_LEGACY_BRIDGE_OWNER_ABSENT_RED"
)
_CALLER_DRIFT_SIGNATURE = "PCE9A_B02A_CURRENT_CALLER_SET_DRIFT_NONCREDIT"
_PARTIAL_PACKET_SIGNATURE = "PCE9A_B02A_PARTIAL_MIGRATION_PACKET_NONCREDIT"


def _relative(path: Path) -> str:
    return path.relative_to(_REPO_ROOT).as_posix()


def _read(relative_path: str) -> str:
    path = _REPO_ROOT / relative_path
    assert path.is_file(), f"PCE9A_B02A_REQUIRED_PATH_ABSENT:{relative_path}"
    return path.read_text(encoding="utf-8")


def _direct_old_read_table_callers() -> frozenset[str]:
    if not _SERVICE_ROOT.is_dir():
        pytest.fail("PCE9A_B02A_SERVICE_ROOT_ABSENT_NONCREDIT", pytrace=False)
    return frozenset(
        _relative(path)
        for path in _SERVICE_ROOT.glob("*.py")
        if _OLD_READ_TABLE_ENV in path.read_text(encoding="utf-8")
    )


def _implementation_state() -> dict[str, bool]:
    return {
        relative_path: (_REPO_ROOT / relative_path).is_file()
        for relative_path in _REQUIRED_IMPLEMENTATION_PATHS
    }


def _assert_frozen_current_preflight() -> None:
    callers = _direct_old_read_table_callers()
    assert callers == _EXPECTED_CURRENT_CALLERS, (
        f"{_CALLER_DRIFT_SIGNATURE}:"
        f"expected={sorted(_EXPECTED_CURRENT_CALLERS)!r}:actual={sorted(callers)!r}"
    )
    for relative_path in sorted(_EXPECTED_CURRENT_CALLERS):
        source = _read(relative_path)
        assert _OLD_READ_TABLE_ENV in source, (
            f"{_CALLER_DRIFT_SIGNATURE}:token_absent:{relative_path}"
        )


def _assert_manifest() -> None:
    manifest = json.loads(_read("supabase/migrations/manifest.json"))
    assert isinstance(manifest, Mapping), "PCE9A_B02A_MANIFEST_NOT_OBJECT"
    assert manifest.get("schema_version") == _MANIFEST_SCHEMA
    assert manifest.get("repository") == "MassyuRed/mashos-api"
    assert manifest.get("source_catalog_sha256") == _PCE0_CATALOG_SHA256
    assert manifest.get("production_apply") is False

    migrations = manifest.get("migrations")
    assert isinstance(migrations, list), "PCE9A_B02A_MIGRATIONS_NOT_LIST"
    matches = [
        item
        for item in migrations
        if isinstance(item, Mapping)
        and item.get("migration_id") == _MIGRATION_ID
        and item.get("path") == _MIGRATION_PATH
    ]
    assert len(matches) == 1, "PCE9A_B02A_MIGRATION_IDENTITY_NOT_EXACT1"
    entry = matches[0]
    assert entry.get("phase") == "M1_LEGACY_READ_BRIDGE"
    assert entry.get("destructive") is False
    assert entry.get("production_applied") is False
    assert entry.get("rollback_required") is True
    assert entry.get("verification_required") is True


def _assert_sql() -> None:
    sql = _read(_MIGRATION_PATH)
    lowered = re.sub(r"\s+", " ", sql.lower()).strip()

    assert _PCE0_CATALOG_SHA256 in sql
    assert re.search(
        r"create\s+(?:or\s+replace\s+)?view\s+public\.mymodel_reflections_read",
        lowered,
    )
    assert "security_invoker" in lowered
    assert re.search(r"\bfrom\s+public\.mymodel_reflections\b", lowered)

    prohibited_patterns = (
        r"\b(?:create|alter|drop)\s+(?:or\s+replace\s+)?"
        r"(?:materialized\s+)?view\s+(?:if\s+exists\s+)?public\.pieces\b",
        r"\bdrop\s+table\s+(?:if\s+exists\s+)?public\.mymodel_reflections\b",
        r"\btruncate(?:\s+table)?\s+public\.mymodel_reflections\b",
        r"\bdelete\s+from\s+public\.mymodel_reflections\b",
        r"\balter\s+table\s+public\.mymodel_reflections\b",
    )
    for pattern in prohibited_patterns:
        assert not re.search(pattern, lowered), (
            f"PCE9A_B02A_PROHIBITED_SQL_PATTERN:{pattern}"
        )


def _assert_caller_rebind() -> None:
    assert _direct_old_read_table_callers() == frozenset(), (
        "PCE9A_B02A_OLD_READ_TABLE_CALLER_RESIDUAL"
    )
    shared_owner = _read(
        "ai/services/ai_inference/piece_public_read_store.py"
    )
    assert _BRIDGE_RELATION_TOKEN in shared_owner

    for relative_path in sorted(_EXPECTED_CURRENT_CALLERS):
        source = _read(relative_path)
        directly_bound = _BRIDGE_RELATION_TOKEN in source
        shared_bound = (
            "piece_public_read_store" in source
            and "MYMODEL_REFLECTIONS_READ_TABLE" in source
            and _BRIDGE_RELATION_TOKEN in shared_owner
        )
        assert directly_bound or shared_bound, (
            f"PCE9A_B02A_CALLER_NOT_REBOUND:{relative_path}"
        )


def _assert_test_runtime_contract() -> None:
    readme = _read("supabase/migrations/README.md")
    conftest = _read("ai/tests/piece_v2/db/conftest.py")
    requirements = _read("requirements-piece-v2-test.txt")

    assert "PIECE_V2_TEST_DATABASE_URL" in readme
    assert "PIECE_V2_TEST_DATABASE_URL" in conftest
    credential_surface = conftest.replace("PIECE_V2_TEST_DATABASE_URL", "")
    for forbidden_name in (
        "DATABASE_URL",
        "SUPABASE_DB_URL",
        "SUPABASE_URL",
        "SUPABASE_SERVICE_ROLE_KEY",
    ):
        assert f'"{forbidden_name}"' not in credential_surface
        assert f"'{forbidden_name}'" not in credential_surface
    assert requirements.strip(), "PCE9A_B02A_TEST_REQUIREMENTS_EMPTY"


def test_b02a_m0_m1_tracked_migration_and_legacy_bridge_r035_r040() -> None:
    """Freeze exact current callers and the future tracked M0/M1 owner packet."""

    state = _implementation_state()
    present = {path for path, exists in state.items() if exists}

    if not present:
        _assert_frozen_current_preflight()
        pytest.fail(_RED_SIGNATURE, pytrace=False)

    if len(present) != len(state):
        missing = sorted(path for path, exists in state.items() if not exists)
        pytest.fail(
            f"{_PARTIAL_PACKET_SIGNATURE}:missing={missing!r}",
            pytrace=False,
        )

    _assert_manifest()
    _assert_sql()
    _assert_caller_rebind()
    _assert_test_runtime_contract()
