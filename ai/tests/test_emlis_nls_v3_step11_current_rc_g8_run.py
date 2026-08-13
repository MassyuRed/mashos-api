from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import stat
import sys

import pytest


_AI_ROOT = Path(__file__).resolve().parents[1]
_TOOLS = _AI_ROOT / "tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

import emlis_nls_v3_step11_current_rc_g8_run as runner  # noqa: E402


_KEY = b"k" * 32
_RUN_ID = "g8-evidence-v3-focused"


def _source_snapshot(marker: str = "a") -> dict[str, object]:
    files = [{"path": "ai/tools/focused_source.py", "sha256": marker * 64}]
    return {
        "source_closure_sha256": runner._closure_digest(files),
        "source_closure_file_count": 1,
        "source_closure_files": files,
    }


def _selected_row(index: int) -> dict[str, object]:
    case_id = f"nls3s_b001_{index:04d}"
    return {
        "case_id": case_id,
        "source_case_commitment": f"{index:064x}",
        "source_input": {
            "thought_text": f"private thought {index}",
            "action_text": "",
            "emotions": [{"type": "平穏", "strength": "medium"}],
            "categories": ["生活"],
        },
        "disposition": "selected",
        "current_candidate_id": f"current-{index}",
        "candidate_output_utf8": f"private output {index}",
        "machine_checks": {key: True for key in runner._CHECK_KEYS},
        "failure_code": None,
        "exception_captured": False,
    }


def _rows() -> list[dict[str, object]]:
    return [_selected_row(index) for index in range(1, 101)]


def _case_sources() -> tuple[tuple[str, str, bytes], ...]:
    return tuple(
        (
            str(row["case_id"]),
            str(row["source_case_commitment"]),
            runner._canonical_json_bytes(row["source_input"]),
        )
        for row in _rows()
    )


def _payloads(
    rows: list[dict[str, object]] | None = None,
    *,
    source: dict[str, object] | None = None,
) -> tuple[bytes, bytes, dict[str, object], dict[str, object], dict[str, object]]:
    snapshot = source or _source_snapshot()
    private_payload, public_payload, public = runner._result_payloads(
        rows or _rows(),
        key=_KEY,
        run_id=_RUN_ID,
        source_snapshot=snapshot,
        expected_case_sources=_case_sources(),
    )
    private = json.loads(private_payload)
    return private_payload, public_payload, private, public, snapshot


def test_01_cli_help_exposes_exact100_v3_private_pair() -> None:
    help_text = runner._parser().format_help()
    assert "exact-100" in help_text
    assert "--workers" in help_text
    assert "--commitment-key-file" in help_text
    assert "--output-dir" in help_text


def test_02_frozen_batch_preflight_is_exact_ordered_100() -> None:
    samples, manifest, commitments = runner._exact100_sources(
        runner._BATCH_PATH, runner._MANIFEST_PATH
    )
    expected_ids = tuple(
        f"nls3s_b001_{index:04d}" for index in range(1, 101)
    )
    assert tuple(row["case_id"] for row in samples) == expected_ids
    assert tuple(manifest["case_ids"]) == expected_ids
    assert tuple(commitments) == expected_ids


def test_03_v3_pair_is_canonical_body_free_and_hmac_bound() -> None:
    private_payload, public_payload, private, public, source = _payloads()
    assert runner._canonical_json_bytes(private) == private_payload
    assert runner._canonical_json_bytes(public) == public_payload
    assert public["schema_version"] == runner._BODY_FREE_SCHEMA
    assert private["schema_version"] == runner._PRIVATE_SCHEMA
    assert public["source_closure_sha256"] == source["source_closure_sha256"]
    assert public["disposition_counts"] == {
        "fail_close": 0,
        "no_valid_candidate": 0,
        "selected": 100,
    }
    assert public["exception_count"] == 0
    assert len(public["cases"]) == 100
    assert set(public["cases"][0]) == {
        "ordinal",
        "case_id",
        "source_case_commitment",
        "disposition",
        "candidate_present",
        "output_present",
        "exception_present",
        "failure_reason_code",
        "machine_checks",
        "case_hmac",
    }
    assert public["cases"][0]["case_hmac"] == runner._case_commitment(
        _KEY,
        _RUN_ID,
        str(source["source_closure_sha256"]),
        1,
        _rows()[0],
    )
    assert private["pair_integrity"] == public["pair_integrity"]
    assert set(public["pair_integrity"]) == {
        "body_free_core_sha256",
        "run_hmac",
    }
    assert "private_core_sha256" not in public_payload.decode("utf-8")
    assert "private thought" in private_payload.decode("utf-8")
    assert "private output" in private_payload.decode("utf-8")
    assert "private thought" not in public_payload.decode("utf-8")
    assert "private output" not in public_payload.decode("utf-8")
    runner._validate_pair(
        private,
        public,
        key=_KEY,
        expected_source=source,
        expected_case_sources=_case_sources(),
    )

    wrong_input = _rows()
    wrong_input[0]["source_input"] = dict(wrong_input[1]["source_input"])
    wrong_commitment = _rows()
    wrong_commitment[0]["source_case_commitment"] = "f" * 64
    for invalid in (wrong_input, wrong_commitment):
        with pytest.raises(runner.CurrentRcG8RunError) as source_binding:
            runner._result_payloads(
                invalid,
                key=_KEY,
                run_id=_RUN_ID,
                source_snapshot=source,
                expected_case_sources=_case_sources(),
            )
        assert source_binding.value.code == (
            "CURRENT_RC_G8_CASE_SOURCE_BINDING_INVALID"
        )


def test_04_selected_state_rejects_missing_output_or_failed_check() -> None:
    rows = _rows()
    rows[0]["candidate_output_utf8"] = None
    with pytest.raises(runner.CurrentRcG8RunError) as captured:
        runner._result_payloads(
            rows,
            key=_KEY,
            run_id=_RUN_ID,
            source_snapshot=_source_snapshot(),
            expected_case_sources=_case_sources(),
        )
    assert captured.value.code == "CURRENT_RC_G8_PRIVATE_STATE_INVALID"


def test_05_no_valid_state_rejects_candidate_or_private_output() -> None:
    rows = _rows()
    row = rows[0]
    row["disposition"] = "no_valid_candidate"
    row["failure_code"] = None
    row["machine_checks"] = {
        key: key in {"input_projected", "base_runtime_valid"}
        for key in runner._CHECK_KEYS
    }
    with pytest.raises(runner.CurrentRcG8RunError) as captured:
        runner._result_payloads(
            rows,
            key=_KEY,
            run_id=_RUN_ID,
            source_snapshot=_source_snapshot(),
            expected_case_sources=_case_sources(),
        )
    assert captured.value.code == "CURRENT_RC_G8_PRIVATE_STATE_INVALID"


def test_06_fail_close_state_requires_failure_and_a_failed_check() -> None:
    rows = _rows()
    rows[0]["disposition"] = "fail_close"
    with pytest.raises(runner.CurrentRcG8RunError) as captured:
        runner._result_payloads(
            rows,
            key=_KEY,
            run_id=_RUN_ID,
            source_snapshot=_source_snapshot(),
            expected_case_sources=_case_sources(),
        )
    assert captured.value.code == "CURRENT_RC_G8_PRIVATE_STATE_INVALID"

    impossible_rows = []
    builder_without_candidate = _rows()
    row = builder_without_candidate[0]
    row["disposition"] = "fail_close"
    row["current_candidate_id"] = None
    row["candidate_output_utf8"] = None
    row["failure_code"] = "CURRENT_RC_G8_CASE_REJECTED"
    row["machine_checks"] = dict(row["machine_checks"])
    row["machine_checks"]["semantic_atoms_exact"] = False
    impossible_rows.append(builder_without_candidate)

    inverse_without_output = _rows()
    row = inverse_without_output[0]
    row["disposition"] = "fail_close"
    row["candidate_output_utf8"] = None
    row["failure_code"] = "CURRENT_RC_G8_INVERSE_REJECTED"
    row["machine_checks"] = dict(row["machine_checks"])
    row["machine_checks"]["semantic_atoms_exact"] = False
    impossible_rows.append(inverse_without_output)

    builder_without_input = _rows()
    row = builder_without_input[0]
    row["disposition"] = "fail_close"
    row["failure_code"] = "CURRENT_RC_G8_INVERSE_REJECTED"
    row["machine_checks"] = dict(row["machine_checks"])
    row["machine_checks"]["input_projected"] = False
    row["machine_checks"]["semantic_atoms_exact"] = False
    impossible_rows.append(builder_without_input)

    for invalid in impossible_rows:
        with pytest.raises(runner.CurrentRcG8RunError) as impossible:
            runner._result_payloads(
                invalid,
                key=_KEY,
                run_id=_RUN_ID,
                source_snapshot=_source_snapshot(),
                expected_case_sources=_case_sources(),
            )
        assert impossible.value.code == "CURRENT_RC_G8_PRIVATE_STATE_INVALID"


def test_07_unknown_private_failure_is_mapped_to_public_allowlist() -> None:
    rows = _rows()
    row = rows[0]
    row["disposition"] = "fail_close"
    row["current_candidate_id"] = None
    row["candidate_output_utf8"] = None
    row["failure_code"] = "PRIVATE_THOUGHT_SECRET"
    row["machine_checks"] = {
        key: key == "input_projected" for key in runner._CHECK_KEYS
    }
    row["exception_captured"] = True
    private_payload, public_payload, _private, public, _source = _payloads(rows)
    assert "PRIVATE_THOUGHT_SECRET" in private_payload.decode("utf-8")
    assert "PRIVATE_THOUGHT_SECRET" not in public_payload.decode("utf-8")
    assert (
        public["cases"][0]["failure_reason_code"]
        == "CURRENT_RC_G8_CASE_REJECTED"
    )
    assert public["cases"][0]["exception_present"] is True
    assert public["exception_count"] == 1


def test_08_private_row_mutation_is_rejected_by_case_hmac() -> None:
    _private_payload, _public_payload, private, public, source = _payloads()
    private["cases"][0]["result"]["candidate_output_utf8"] = "mutated"
    with pytest.raises(runner.CurrentRcG8RunError) as captured:
        runner._validate_pair(
            private,
            public,
            key=_KEY,
            expected_source=source,
            expected_case_sources=_case_sources(),
        )
    assert captured.value.code == "CURRENT_RC_G8_HMAC_VERIFICATION_FAILED"


def test_09_body_free_projection_mutation_is_rejected() -> None:
    _private_payload, _public_payload, private, public, source = _payloads()
    public["cases"][0]["output_present"] = False
    with pytest.raises(runner.CurrentRcG8RunError) as captured:
        runner._validate_pair(
            private,
            public,
            key=_KEY,
            expected_source=source,
            expected_case_sources=_case_sources(),
        )
    assert captured.value.code == "CURRENT_RC_G8_BODY_FREE_PROJECTION_INVALID"


def test_10_order_replay_or_duplicate_is_rejected() -> None:
    _private_payload, _public_payload, private, public, source = _payloads()
    private["cases"][0], private["cases"][1] = (
        private["cases"][1],
        private["cases"][0],
    )
    with pytest.raises(runner.CurrentRcG8RunError):
        runner._validate_pair(
            private,
            public,
            key=_KEY,
            expected_source=source,
            expected_case_sources=_case_sources(),
        )


def test_11_aggregate_and_run_hmac_mutations_are_rejected() -> None:
    _private_payload, _public_payload, private, public, source = _payloads()
    changed_counts = copy.deepcopy(public)
    changed_counts["disposition_counts"]["selected"] = 99
    changed_counts["disposition_counts"]["fail_close"] = 1
    with pytest.raises(runner.CurrentRcG8RunError) as aggregate:
        runner._validate_pair(
            private,
            changed_counts,
            key=_KEY,
            expected_source=source,
            expected_case_sources=_case_sources(),
        )
    assert aggregate.value.code == "CURRENT_RC_G8_ACCOUNTING_INVALID"
    changed_private = copy.deepcopy(private)
    changed_public = copy.deepcopy(public)
    changed_private["pair_integrity"]["run_hmac"] = "f" * 64
    changed_public["pair_integrity"]["run_hmac"] = "f" * 64
    with pytest.raises(runner.CurrentRcG8RunError) as run_hmac:
        runner._validate_pair(
            changed_private,
            changed_public,
            key=_KEY,
            expected_source=source,
            expected_case_sources=_case_sources(),
        )
    assert run_hmac.value.code == "CURRENT_RC_G8_HMAC_VERIFICATION_FAILED"


def test_12_source_closure_contains_product_runtime_fixture_schema_and_io() -> None:
    source = runner._source_closure_snapshot(
        runner._BATCH_PATH, runner._MANIFEST_PATH
    )
    paths = {row["path"] for row in source["source_closure_files"]}
    assert {
        "ai/services/ai_inference/emlis_ai_step11_natural_surface_v3.py",
        "ai/services/ai_inference/"
        "emlis_ai_step11_rc0030_experiment_surface_catalog_v3.py",
        "ai/tools/emlis_nls_v3_step11_current_rc_g8_run.py",
        "ai/tools/emlis_nls_v3_batch_run.py",
        "ai/tools/emlis_nls_v3_rc0029_surface_repair_bounded_experiment.py",
        "ai/tests/helpers/emlis_nls_v3_s2_sample_registry.py",
        "ai/tests/fixtures/emlis_nls_v3/generated/batch_001.jsonl",
        "ai/tests/fixtures/emlis_nls_v3/generated/batch_001_manifest.json",
        "ai/tests/fixtures/emlis_nls_v3/generated/batch_001_coverage_matrix.json",
        "ai/tests/fixtures/emlis_nls_v3/generated/batch_001_duplicate_report.json",
        "ai/tests/fixtures/emlis_nls_v3_s2_corpus_registry_20260714.json",
        "ai/tests/schemas/emlis_nls_v3_sample_case_v1.schema.json",
    } <= paths
    assert source["source_closure_file_count"] == len(paths)
    assert runner._validated_source_snapshot(source) == source


def test_13_prewrite_source_drift_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    snapshots = iter((_source_snapshot("a"), _source_snapshot("b")))
    monkeypatch.setattr(
        runner, "_source_closure_snapshot", lambda _batch, _manifest: next(snapshots)
    )
    monkeypatch.setattr(
        runner,
        "_exact100_sources",
        lambda _batch, _manifest: ([], {}, {}),
    )
    with pytest.raises(runner.CurrentRcG8RunError) as preflight:
        runner._bound_exact100_sources(
            runner._BATCH_PATH, runner._MANIFEST_PATH
        )
    assert preflight.value.code == "CURRENT_RC_G8_SOURCE_CHANGED_DURING_PREFLIGHT"

    source = _source_snapshot()
    private_payload, public_payload, _private, _public, _source = _payloads(
        source=source
    )
    output_dir = tmp_path / "drift"
    output_dir.mkdir(mode=0o700)
    os.chmod(output_dir, 0o700)
    monkeypatch.setattr(
        runner,
        "_source_closure_snapshot",
        lambda _batch, _manifest: _source_snapshot("b"),
    )
    with pytest.raises(runner.CurrentRcG8RunError) as captured:
        runner._write_outputs(
            output_dir,
            private_payload,
            public_payload,
            key=_KEY,
            source_snapshot=source,
            expected_case_sources=_case_sources(),
            batch_path=runner._BATCH_PATH,
            manifest_path=runner._MANIFEST_PATH,
        )
    assert captured.value.code == "CURRENT_RC_G8_SOURCE_CHANGED_BEFORE_WRITE"
    assert list(output_dir.iterdir()) == []

    during_write = tmp_path / "during-write-drift"
    during_write.mkdir(mode=0o700)
    os.chmod(during_write, 0o700)
    write_snapshots = iter((copy.deepcopy(source), _source_snapshot("b")))
    monkeypatch.setattr(
        runner,
        "_source_closure_snapshot",
        lambda _batch, _manifest: next(write_snapshots),
    )
    with pytest.raises(runner.CurrentRcG8RunError) as postwrite_drift:
        runner._write_outputs(
            during_write,
            private_payload,
            public_payload,
            key=_KEY,
            source_snapshot=source,
            expected_case_sources=_case_sources(),
            batch_path=runner._BATCH_PATH,
            manifest_path=runner._MANIFEST_PATH,
        )
    assert postwrite_drift.value.code == (
        "CURRENT_RC_G8_SOURCE_CHANGED_DURING_WRITE"
    )
    assert list(during_write.iterdir()) == []


def test_14_secure_disk_round_trip_is_0600_canonical_and_no_overwrite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _source_snapshot()
    private_payload, public_payload, _private, _public, _source = _payloads(
        source=source
    )
    output_dir = tmp_path / "g8-private"
    output_dir.mkdir(mode=0o700)
    os.chmod(output_dir, 0o700)
    monkeypatch.setattr(
        runner,
        "_source_closure_snapshot",
        lambda _batch, _manifest: copy.deepcopy(source),
    )
    private, public = runner._write_outputs(
        output_dir,
        private_payload,
        public_payload,
        key=_KEY,
        source_snapshot=source,
        expected_case_sources=_case_sources(),
        batch_path=runner._BATCH_PATH,
        manifest_path=runner._MANIFEST_PATH,
    )
    private_path = output_dir / runner._PRIVATE_FILENAME
    public_path = output_dir / runner._BODY_FREE_FILENAME
    assert stat.S_IMODE(private_path.stat().st_mode) == 0o600
    assert stat.S_IMODE(public_path.stat().st_mode) == 0o600
    assert private_path.read_bytes() == private_payload
    assert public_path.read_bytes() == public_payload
    assert {path.name for path in output_dir.iterdir()} == {
        runner._PRIVATE_FILENAME,
        runner._BODY_FREE_FILENAME,
    }
    runner._validate_pair(
        private,
        public,
        key=_KEY,
        expected_source=source,
        expected_case_sources=_case_sources(),
    )
    with pytest.raises(runner.CurrentRcG8RunError):
        runner._write_outputs(
            output_dir,
            private_payload,
            public_payload,
            key=_KEY,
            source_snapshot=source,
            expected_case_sources=_case_sources(),
            batch_path=runner._BATCH_PATH,
            manifest_path=runner._MANIFEST_PATH,
        )
    assert private_path.read_bytes() == private_payload
    assert public_path.read_bytes() == public_payload

    nonfresh = tmp_path / "nonfresh-private"
    nonfresh.mkdir(mode=0o700)
    os.chmod(nonfresh, 0o700)
    (nonfresh / "unrelated").write_text("occupied", encoding="utf-8")
    with pytest.raises(runner.CurrentRcG8RunError) as occupied:
        runner._write_outputs(
            nonfresh,
            private_payload,
            public_payload,
            key=_KEY,
            source_snapshot=source,
            expected_case_sources=_case_sources(),
            batch_path=runner._BATCH_PATH,
            manifest_path=runner._MANIFEST_PATH,
        )
    assert occupied.value.code == "CURRENT_RC_G8_PRIVATE_DIRECTORY_NOT_FRESH"
    assert not (nonfresh / runner._PRIVATE_FILENAME).exists()
    assert not (nonfresh / runner._BODY_FREE_FILENAME).exists()

    postverify = tmp_path / "postverify-private"
    postverify.mkdir(mode=0o700)
    os.chmod(postverify, 0o700)
    calls = 0
    original_validate_pair = runner._validate_pair

    def reject_after_write(*args: object, **kwargs: object) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise runner.CurrentRcG8RunError(
                "CURRENT_RC_G8_PRIVATE_OUTPUT_POSTVERIFY_FAILED"
            )
        original_validate_pair(*args, **kwargs)

    monkeypatch.setattr(runner, "_validate_pair", reject_after_write)
    with pytest.raises(runner.CurrentRcG8RunError) as postwrite:
        runner._write_outputs(
            postverify,
            private_payload,
            public_payload,
            key=_KEY,
            source_snapshot=source,
            expected_case_sources=_case_sources(),
            batch_path=runner._BATCH_PATH,
            manifest_path=runner._MANIFEST_PATH,
        )
    assert postwrite.value.code == (
        "CURRENT_RC_G8_PRIVATE_OUTPUT_POSTVERIFY_FAILED"
    )
    assert list(postverify.iterdir()) == []

    mixed = tmp_path / "mixed-private"
    mixed.mkdir(mode=0o700)
    os.chmod(mixed, 0o700)
    source_checks = 0

    def insert_unrelated_after_write(*args: object, **kwargs: object) -> None:
        nonlocal source_checks
        source_checks += 1
        if source_checks == 2:
            (mixed / "unrelated").write_text("occupied", encoding="utf-8")

    monkeypatch.setattr(runner, "_assert_source_unchanged", insert_unrelated_after_write)
    monkeypatch.setattr(runner, "_validate_pair", original_validate_pair)
    with pytest.raises(runner.CurrentRcG8RunError) as mixed_result:
        runner._write_outputs(
            mixed,
            private_payload,
            public_payload,
            key=_KEY,
            source_snapshot=source,
            expected_case_sources=_case_sources(),
            batch_path=runner._BATCH_PATH,
            manifest_path=runner._MANIFEST_PATH,
        )
    assert mixed_result.value.code == (
        "CURRENT_RC_G8_PRIVATE_DIRECTORY_POSTVERIFY_FAILED"
    )
    assert {path.name for path in mixed.iterdir()} == {"unrelated"}
