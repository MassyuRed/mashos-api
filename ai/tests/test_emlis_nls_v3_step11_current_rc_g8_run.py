from __future__ import annotations

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


def _private_row(index: int) -> dict[str, object]:
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
        "selected_output_utf8": f"private output {index}",
        "machine_checks": {key: True for key in runner._CHECK_KEYS},
        "failure_code": None,
    }


def test_cli_help_exposes_exact100_workers_and_private_pair() -> None:
    help_text = runner._parser().format_help()
    assert "exact-100" in help_text
    assert "--workers" in help_text
    assert "--commitment-key-file" in help_text
    assert "--output-dir" in help_text


def test_frozen_batch_preflight_is_exact_ordered_100() -> None:
    samples, manifest, commitments = runner._exact100_sources(
        runner._BATCH_PATH, runner._MANIFEST_PATH
    )
    expected_ids = tuple(
        f"nls3s_b001_{index:04d}" for index in range(1, 101)
    )
    assert tuple(row["case_id"] for row in samples) == expected_ids
    assert tuple(manifest["case_ids"]) == expected_ids
    assert tuple(commitments) == expected_ids


def test_body_free_rows_have_only_four_fields_and_hmac_commitment() -> None:
    rows = [_private_row(index) for index in range(1, 101)]
    private_payload, body_free_payload, summary = runner._result_payloads(
        rows,
        key=b"k" * 32,
        run_id="g8-focused-test",
        source_closure="a" * 64,
    )
    decoded = json.loads(body_free_payload)
    assert decoded == summary
    assert set(decoded) == {
        "schema_version",
        "run_id",
        "source_closure_sha256",
        "case_count",
        "disposition_counts",
        "cases",
    }
    assert decoded["schema_version"] == runner._BODY_FREE_SCHEMA
    assert decoded["run_id"] == "g8-focused-test"
    assert decoded["source_closure_sha256"] == "a" * 64
    assert decoded["case_count"] == 100
    assert decoded["disposition_counts"] == {
        "selected": 100,
        "no_valid_candidate": 0,
        "fail_close": 0,
    }
    assert len(decoded["cases"]) == 100
    assert all(
        set(row)
        == {
            "case_id",
            "disposition",
            "machine_checks",
            "hmac_commitment",
        }
        for row in decoded["cases"]
    )
    assert all(
        row["machine_checks"]["hmac_commitment_verified"]
        for row in decoded["cases"]
    )
    assert "private thought" not in body_free_payload.decode("utf-8")
    assert "private output" not in body_free_payload.decode("utf-8")
    assert "private thought" in private_payload.decode("utf-8")
    assert "private output" in private_payload.decode("utf-8")
    assert decoded["cases"][0]["hmac_commitment"] == runner._case_commitment(
        b"k" * 32, "g8-focused-test", rows[0]
    )


def test_private_pair_is_0600_and_cannot_overwrite(tmp_path: Path) -> None:
    output_dir = tmp_path / "g8-private"
    output_dir.mkdir(mode=0o700)
    os.chmod(output_dir, 0o700)
    runner._write_outputs(output_dir, b"private\n", b"summary\n")
    private_path = output_dir / runner._PRIVATE_FILENAME
    summary_path = output_dir / runner._BODY_FREE_FILENAME
    assert stat.S_IMODE(private_path.stat().st_mode) == 0o600
    assert stat.S_IMODE(summary_path.stat().st_mode) == 0o600
    assert private_path.read_bytes() == b"private\n"
    assert summary_path.read_bytes() == b"summary\n"
    with pytest.raises(Exception):
        runner._write_outputs(output_dir, b"replacement\n", b"replacement\n")
    assert private_path.read_bytes() == b"private\n"
    assert summary_path.read_bytes() == b"summary\n"
