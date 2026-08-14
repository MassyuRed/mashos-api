from __future__ import annotations

import copy
from functools import lru_cache
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
import emlis_nls_v3_step11_current100_product_read as product_read  # noqa: E402


_KEY = b"r" * 32
_RUN_ID = "cycle001-current100-product-read-test"
_ORIGINAL_SOURCE_CLOSURE_SNAPSHOT = runner._source_closure_snapshot
_ORIGINAL_EXACT100_SOURCES = runner._exact100_sources
_ORIGINAL_EXACT100_SOURCE_BINDINGS = runner._exact100_source_bindings


@lru_cache(maxsize=1)
def _frozen_material() -> tuple[object, ...]:
    source = _ORIGINAL_SOURCE_CLOSURE_SNAPSHOT(
        runner._BATCH_PATH,
        runner._MANIFEST_PATH,
    )
    samples, manifest, commitments = _ORIGINAL_EXACT100_SOURCES(
        runner._BATCH_PATH,
        runner._MANIFEST_PATH,
    )
    case_sources = _ORIGINAL_EXACT100_SOURCE_BINDINGS(
        samples,
        commitments,
    )
    return samples, manifest, commitments, case_sources, source


@pytest.fixture(autouse=True)
def _reuse_independent_frozen_material(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    material = _frozen_material()

    def stable_material(_batch: Path, _manifest: Path) -> tuple[object, ...]:
        return copy.deepcopy(material)

    monkeypatch.setattr(
        runner,
        "_bound_exact100_sources",
        stable_material,
    )


def _synthetic_source_snapshot() -> dict[str, object]:
    files = [{"path": "ai/tools/product_read_parent.py", "sha256": "a" * 64}]
    return {
        "source_closure_sha256": runner._closure_digest(files),
        "source_closure_file_count": 1,
        "source_closure_files": files,
    }


def _selected_rows(
    samples: list[dict[str, object]],
    commitments: dict[str, str],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, sample in enumerate(samples, start=1):
        case_id = f"nls3s_b001_{index:04d}"
        assert sample["case_id"] == case_id
        rows.append(
            {
                "case_id": case_id,
                "source_case_commitment": commitments[case_id],
                "source_input": copy.deepcopy(sample["input"]),
                "disposition": "selected",
                "candidate_version_id": runner._RECOVERY_CANDIDATE_VERSION,
                "candidate_schema_version": runner._RECOVERY_CANDIDATE_SCHEMA,
                "current_candidate_id": f"private-candidate-{index}",
                "candidate_output_utf8": f"raw private output {index}",
                "machine_checks": {
                    key: True for key in runner._CHECK_KEYS
                },
                "failure_code": None,
                "exception_captured": False,
            }
        )
    return rows


def _runner_pair() -> tuple[dict[str, object], dict[str, object]]:
    samples, _manifest, commitments, case_sources, source = copy.deepcopy(
        _frozen_material()
    )
    rows = _selected_rows(samples, commitments)
    private_payload, public_payload, _public = runner._result_payloads(
        rows,
        key=_KEY,
        run_id=_RUN_ID,
        source_snapshot=source,
        expected_case_sources=case_sources,
    )
    return json.loads(private_payload), json.loads(public_payload)


def _synthetic_runner_pair() -> tuple[dict[str, object], dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index in range(1, 101):
        rows.append(
            {
                "case_id": f"nls3s_b001_{index:04d}",
                "source_case_commitment": f"{index:064x}",
                "source_input": {
                    "thought_text": f"synthetic private thought {index}",
                    "action_text": "",
                    "emotions": [],
                    "categories": [],
                },
                "disposition": "selected",
                "candidate_version_id": runner._RECOVERY_CANDIDATE_VERSION,
                "candidate_schema_version": runner._RECOVERY_CANDIDATE_SCHEMA,
                "current_candidate_id": f"synthetic-candidate-{index}",
                "candidate_output_utf8": f"synthetic private output {index}",
                "machine_checks": {
                    key: True for key in runner._CHECK_KEYS
                },
                "failure_code": None,
                "exception_captured": False,
            }
        )
    case_sources = tuple(
        (
            str(row["case_id"]),
            str(row["source_case_commitment"]),
            runner._canonical_json_bytes(row["source_input"]),
        )
        for row in rows
    )
    source = _synthetic_source_snapshot()
    private_payload, public_payload, _public = runner._result_payloads(
        rows,
        key=_KEY,
        run_id=_RUN_ID,
        source_snapshot=source,
        expected_case_sources=case_sources,
    )
    return json.loads(private_payload), json.loads(public_payload)


def _pass_decision(index: int) -> dict[str, object]:
    return {
        "case_id": f"nls3s_b001_{index:04d}",
        "axis_results": {
            axis: "PASS" for axis in product_read.PRODUCT_READ_AXES
        },
        "severity": "PASS",
        "reason_codes": ["PRODUCT_READ_PASS"],
        "shared_cause_codes": [],
        "private_note": f"private reviewer note {index}",
    }


def _decisions(public: dict[str, object]) -> dict[str, object]:
    return {
        "schema_version": product_read._DECISIONS_SCHEMA,
        "runner_run_id": public["run_id"],
        "runner_source_closure_sha256": public["source_closure_sha256"],
        "runner_pair_run_hmac": public["pair_integrity"]["run_hmac"],
        "candidate_version_id": public["candidate_version_id"],
        "candidate_schema_version": public["candidate_schema_version"],
        "cases": [_pass_decision(index) for index in range(1, 101)],
    }


def _coordinated_wrong_identity_parent(
    private: dict[str, object],
    public: dict[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    changed_private = copy.deepcopy(private)
    changed_public = copy.deepcopy(public)
    wrong_version = "nls_v3_rc_0036_not_the_recovery_candidate"
    changed_private["candidate_version_id"] = wrong_version
    changed_public["candidate_version_id"] = wrong_version
    for ordinal, (private_envelope, public_row) in enumerate(
        zip(
            changed_private["cases"],
            changed_public["cases"],
            strict=True,
        ),
        start=1,
    ):
        row = private_envelope["result"]
        row["candidate_version_id"] = wrong_version
        case_hmac = runner._case_commitment(
            _KEY,
            changed_private["run_id"],
            changed_private["source_closure_sha256"],
            ordinal,
            row,
        )
        private_envelope["case_hmac"] = case_hmac
        changed_public["cases"][ordinal - 1] = runner._public_case_row(
            row,
            ordinal=ordinal,
            case_hmac=case_hmac,
        )
    private_core = copy.deepcopy(changed_private)
    public_core = copy.deepcopy(changed_public)
    private_core.pop("pair_integrity")
    public_core.pop("pair_integrity")
    private_sha = runner.hashlib.sha256(
        runner._canonical_json_bytes(private_core)
    ).hexdigest()
    public_sha = runner.hashlib.sha256(
        runner._canonical_json_bytes(public_core)
    ).hexdigest()
    pair = {
        "body_free_core_sha256": public_sha,
        "run_hmac": runner._run_commitment(
            _KEY,
            run_id=changed_private["run_id"],
            source_closure=changed_private["source_closure_sha256"],
            private_core_sha256=private_sha,
            body_free_core_sha256=public_sha,
        ),
    }
    changed_private["pair_integrity"] = pair
    changed_public["pair_integrity"] = copy.deepcopy(pair)
    return changed_private, changed_public


def _review_pair() -> tuple[
    bytes,
    bytes,
    dict[str, object],
    dict[str, object],
    dict[str, object],
]:
    runner_private, runner_public = _runner_pair()
    private_payload, public_payload, public = (
        product_read.build_current100_product_read_pair(
            runner_private,
            runner_public,
            _decisions(runner_public),
            key=_KEY,
        )
    )
    return (
        private_payload,
        public_payload,
        json.loads(private_payload),
        public,
        runner_public,
    )


def test_01_exact100_pair_is_parent_bound_aggregated_and_body_free() -> None:
    private_payload, public_payload, private, public, runner_public = (
        _review_pair()
    )
    assert product_read._canonical_json_bytes(private) == private_payload
    assert product_read._canonical_json_bytes(public) == public_payload
    assert private["case_count"] == public["case_count"] == 100
    assert tuple(row["case_id"] for row in public["cases"]) == tuple(
        f"nls3s_b001_{index:04d}" for index in range(1, 101)
    )
    assert public["runner_binding"] == {
        "run_id": runner_public["run_id"],
        "source_closure_sha256": runner_public["source_closure_sha256"],
        "candidate_version_id": runner._RECOVERY_CANDIDATE_VERSION,
        "candidate_schema_version": runner._RECOVERY_CANDIDATE_SCHEMA,
        "runner_pair_run_hmac": runner_public["pair_integrity"]["run_hmac"],
    }
    assert public["review_status_counts"] == {"PASS": 100, "FAIL": 0}
    assert public["severity_counts"] == {
        "PASS": 100,
        "MINOR": 0,
        "MAJOR": 0,
        "BLOCKER": 0,
    }
    assert all(value == 0 for value in public["failure_axis_counts"].values())
    assert public["reason_code_counts"]["PRODUCT_READ_PASS"] == 100
    assert private["pair_integrity"] == public["pair_integrity"]
    assert "private reviewer note 1" in private_payload.decode("utf-8")
    assert "private reviewer note" not in public_payload.decode("utf-8")
    assert "raw private thought" not in public_payload.decode("utf-8")
    assert "raw private output" not in public_payload.decode("utf-8")
    assert "private-candidate" not in public_payload.decode("utf-8")
    assert "source_case_commitment" not in public_payload.decode("utf-8")
    product_read._validate_review_pair(
        private,
        public,
        key=_KEY,
        expected_runner_binding=public["runner_binding"],
    )


def test_02_decisions_require_exact_ordered100() -> None:
    runner_private, runner_public = _runner_pair()
    decisions = _decisions(runner_public)
    decisions["cases"][0], decisions["cases"][1] = (
        decisions["cases"][1],
        decisions["cases"][0],
    )
    with pytest.raises(product_read.Current100ProductReadError) as captured:
        product_read.build_current100_product_read_pair(
            runner_private, runner_public, decisions, key=_KEY
        )
    assert captured.value.code == "CURRENT100_PRODUCT_READ_AXIS_SET_INVALID"

    missing = _decisions(runner_public)
    missing["cases"].pop()
    with pytest.raises(product_read.Current100ProductReadError) as count:
        product_read.build_current100_product_read_pair(
            runner_private, runner_public, missing, key=_KEY
        )
    assert count.value.code == "CURRENT100_PRODUCT_READ_DECISIONS_INVALID"


def test_03_missing_axis_and_invalid_enum_are_rejected() -> None:
    runner_private, runner_public = _runner_pair()
    missing_axis = _decisions(runner_public)
    del missing_axis["cases"][0]["axis_results"][
        product_read.PRODUCT_READ_AXES[-1]
    ]
    invalid_enum = _decisions(runner_public)
    invalid_enum["cases"][0]["axis_results"][
        product_read.PRODUCT_READ_AXES[0]
    ] = "NOT_REVIEWED"
    for invalid in (missing_axis, invalid_enum):
        with pytest.raises(product_read.Current100ProductReadError) as captured:
            product_read.build_current100_product_read_pair(
                runner_private, runner_public, invalid, key=_KEY
            )
        assert captured.value.code == "CURRENT100_PRODUCT_READ_AXIS_SET_INVALID"


@pytest.mark.parametrize("severity", ["PASS", "MINOR", "MAJOR", "BLOCKER"])
def test_04_severity_is_consistent_with_axis_failures(severity: str) -> None:
    runner_private, runner_public = _runner_pair()
    decisions = _decisions(runner_public)
    row = decisions["cases"][0]
    row["axis_results"]["NATURAL_NON_REPETITIVE_SURFACE"] = "FAIL"
    row["reason_codes"] = ["SURFACE_UNNATURAL_OR_REPETITIVE"]
    row["shared_cause_codes"] = ["GENERIC_SURFACE_REALIZATION_PATTERN"]
    row["severity"] = severity
    if severity == "PASS":
        with pytest.raises(product_read.Current100ProductReadError) as captured:
            product_read.build_current100_product_read_pair(
                runner_private, runner_public, decisions, key=_KEY
            )
        assert captured.value.code == (
            "CURRENT100_PRODUCT_READ_FAILURE_STATE_INVALID"
        )
    else:
        _private, _public_payload, public = (
            product_read.build_current100_product_read_pair(
                runner_private, runner_public, decisions, key=_KEY
            )
        )
        assert public["severity_counts"][severity] == 1
        assert public["review_status_counts"] == {"PASS": 99, "FAIL": 1}
        assert public["failure_axis_counts"][
            "NATURAL_NON_REPETITIVE_SURFACE"
        ] == 1


def test_05_reason_code_must_exactly_account_for_failed_axes() -> None:
    runner_private, runner_public = _runner_pair()
    decisions = _decisions(runner_public)
    row = decisions["cases"][0]
    row["axis_results"]["DEPTH_PROPORTIONAL"] = "FAIL"
    row["severity"] = "MINOR"
    row["reason_codes"] = ["SURFACE_UNNATURAL_OR_REPETITIVE"]
    with pytest.raises(product_read.Current100ProductReadError) as captured:
        product_read.build_current100_product_read_pair(
            runner_private, runner_public, decisions, key=_KEY
        )
    assert captured.value.code == "CURRENT100_PRODUCT_READ_FAILURE_STATE_INVALID"


def test_06_shared_cause_allowlist_duplicate_and_pass_state_are_closed() -> None:
    runner_private, runner_public = _runner_pair()
    invalid_code = _decisions(runner_public)
    invalid_code["cases"][0]["shared_cause_codes"] = ["PRIVATE_FREE_TEXT"]
    duplicate = _decisions(runner_public)
    duplicate["cases"][0]["shared_cause_codes"] = [
        "GENERIC_SURFACE_REALIZATION_PATTERN",
        "GENERIC_SURFACE_REALIZATION_PATTERN",
    ]
    pass_with_cause = _decisions(runner_public)
    pass_with_cause["cases"][0]["shared_cause_codes"] = [
        "GENERIC_SURFACE_REALIZATION_PATTERN"
    ]
    expected_codes = (
        "CURRENT100_PRODUCT_READ_SHARED_CAUSE_CODE_INVALID",
        "CURRENT100_PRODUCT_READ_SHARED_CAUSE_CODE_INVALID",
        "CURRENT100_PRODUCT_READ_PASS_STATE_INVALID",
    )
    for invalid, expected in zip(
        (invalid_code, duplicate, pass_with_cause),
        expected_codes,
        strict=True,
    ):
        with pytest.raises(product_read.Current100ProductReadError) as captured:
            product_read.build_current100_product_read_pair(
                runner_private,
                runner_public,
                invalid,
                key=_KEY,
            )
        assert captured.value.code == expected


def test_07_private_public_aggregate_and_pair_tampering_are_rejected() -> None:
    _private_payload, _public_payload, private, public, runner_public = (
        _review_pair()
    )
    runner_private, _unused = _runner_pair()
    binding, _rows, _public_rows = product_read._runner_machine100_binding(
        runner_private, runner_public, key=_KEY
    )

    changed_private = copy.deepcopy(private)
    changed_private["cases"][0]["private_note"] = "changed private note"
    with pytest.raises(product_read.Current100ProductReadError) as case_hmac:
        product_read._validate_review_pair(
            changed_private,
            public,
            key=_KEY,
            expected_runner_binding=binding,
        )
    assert case_hmac.value.code == "CURRENT100_PRODUCT_READ_CASE_HMAC_INVALID"

    changed_public = copy.deepcopy(public)
    changed_public["cases"][0]["axis_results"][
        "PRIMARY_MEANING_RETAINED"
    ] = "FAIL"
    with pytest.raises(product_read.Current100ProductReadError) as projection:
        product_read._validate_review_pair(
            private,
            changed_public,
            key=_KEY,
            expected_runner_binding=binding,
        )
    assert projection.value.code == (
        "CURRENT100_PRODUCT_READ_PUBLIC_PROJECTION_INVALID"
    )

    changed_private_aggregate = copy.deepcopy(private)
    changed_public_aggregate = copy.deepcopy(public)
    changed_private_aggregate["severity_counts"]["PASS"] = 99
    changed_public_aggregate["severity_counts"]["PASS"] = 99
    with pytest.raises(product_read.Current100ProductReadError) as aggregate:
        product_read._validate_review_pair(
            changed_private_aggregate,
            changed_public_aggregate,
            key=_KEY,
            expected_runner_binding=binding,
        )
    assert aggregate.value.code == "CURRENT100_PRODUCT_READ_ACCOUNTING_INVALID"

    changed_private_pair = copy.deepcopy(private)
    changed_public_pair = copy.deepcopy(public)
    changed_private_pair["pair_integrity"]["review_run_hmac"] = "0" * 64
    changed_public_pair["pair_integrity"]["review_run_hmac"] = "0" * 64
    with pytest.raises(product_read.Current100ProductReadError) as pair_hmac:
        product_read._validate_review_pair(
            changed_private_pair,
            changed_public_pair,
            key=_KEY,
            expected_runner_binding=binding,
        )
    assert pair_hmac.value.code == "CURRENT100_PRODUCT_READ_PAIR_HMAC_INVALID"


def test_08_parent_is_independently_frozen_source_bound() -> None:
    synthetic_private, synthetic_public = _synthetic_runner_pair()
    with pytest.raises(product_read.Current100ProductReadError) as synthetic:
        product_read.build_current100_product_read_pair(
            synthetic_private,
            synthetic_public,
            _decisions(synthetic_public),
            key=_KEY,
        )
    assert synthetic.value.code == (
        "CURRENT100_PRODUCT_READ_MACHINE100_PARENT_INVALID"
    )


def test_09_parent_pair_requires_same_key_and_exact_recovery_identity() -> None:
    private, public = _runner_pair()
    with pytest.raises(product_read.Current100ProductReadError) as wrong_key:
        product_read.build_current100_product_read_pair(
            private, public, _decisions(public), key=b"x" * 32
        )
    assert wrong_key.value.code == (
        "CURRENT100_PRODUCT_READ_MACHINE100_PARENT_INVALID"
    )

    changed_private, changed_public = _coordinated_wrong_identity_parent(
        private,
        public,
    )
    with pytest.raises(product_read.Current100ProductReadError) as identity:
        product_read.build_current100_product_read_pair(
            changed_private,
            changed_public,
            _decisions(public),
            key=_KEY,
        )
    assert identity.value.code == (
        "CURRENT100_PRODUCT_READ_MACHINE100_PARENT_INVALID"
    )


def test_10_write_is_exact0600_and_never_overwrites(tmp_path: Path) -> None:
    private_payload, public_payload, _private, _public, runner_public = (
        _review_pair()
    )
    runner_private, _unused = _runner_pair()
    binding, _rows, _public_rows = product_read._runner_machine100_binding(
        runner_private, runner_public, key=_KEY
    )
    output_dir = tmp_path / "review"
    output_dir.mkdir(mode=0o700)
    os.chmod(output_dir, 0o700)
    product_read._write_pair(
        output_dir,
        private_payload,
        public_payload,
        key=_KEY,
        runner_binding=binding,
    )
    private_path = output_dir / product_read._PRIVATE_FILENAME
    public_path = output_dir / product_read._BODY_FREE_FILENAME
    assert {path.name for path in output_dir.iterdir()} == {
        private_path.name,
        public_path.name,
    }
    assert stat.S_IMODE(private_path.stat().st_mode) == 0o600
    assert stat.S_IMODE(public_path.stat().st_mode) == 0o600
    before = {path.name: path.read_bytes() for path in output_dir.iterdir()}
    with pytest.raises(product_read.Current100ProductReadError) as no_overwrite:
        product_read._write_pair(
            output_dir,
            private_payload,
            public_payload,
            key=_KEY,
            runner_binding=binding,
        )
    assert no_overwrite.value.code == (
        "CURRENT100_PRODUCT_READ_OUTPUT_DIRECTORY_NOT_FRESH"
    )
    assert {path.name: path.read_bytes() for path in output_dir.iterdir()} == before


def test_11_post_freshness_race_is_not_overwritten_or_unlinked(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    private_payload, public_payload, _private, _public, runner_public = (
        _review_pair()
    )
    runner_private, _unused = _runner_pair()
    binding, _rows, _public_rows = product_read._runner_machine100_binding(
        runner_private, runner_public, key=_KEY
    )
    output_dir = tmp_path / "race"
    output_dir.mkdir(mode=0o700)
    os.chmod(output_dir, 0o700)
    real_open = os.open
    raced = False

    def racing_open(
        path: object,
        flags: int,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ) -> int:
        nonlocal raced
        if (
            path == product_read._PRIVATE_FILENAME
            and flags & os.O_EXCL
            and not raced
        ):
            raced = True
            racer_fd = real_open(
                path,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
                dir_fd=dir_fd,
            )
            try:
                os.write(racer_fd, b"racer-owned")
                os.fsync(racer_fd)
            finally:
                os.close(racer_fd)
        return real_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(product_read.os, "open", racing_open)
    with pytest.raises(product_read.Current100ProductReadError) as race:
        product_read._write_pair(
            output_dir,
            private_payload,
            public_payload,
            key=_KEY,
            runner_binding=binding,
        )
    assert race.value.code == "CURRENT100_PRODUCT_READ_OUTPUT_FAILED"
    race_path = output_dir / product_read._PRIVATE_FILENAME
    assert race_path.read_bytes() == b"racer-owned"
    assert tuple(path.name for path in output_dir.iterdir()) == (
        product_read._PRIVATE_FILENAME,
    )


def test_12_cli_help_exposes_only_direct_pair_inputs() -> None:
    help_text = product_read._parser().format_help()
    assert "--runner-private" in help_text
    assert "--runner-body-free" in help_text
    assert "--decisions" in help_text
    assert "--commitment-key-file" in help_text
    assert "--output-dir" in help_text
