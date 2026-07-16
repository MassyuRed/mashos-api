#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""Run a frozen NLS v3 sample batch through the dormant runtime adapter."""

import argparse
import asyncio
import hashlib
import os
from pathlib import Path
import stat as stat_module
import sys
from typing import Any, Mapping, Sequence


AI_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = AI_ROOT.parent
SERVICES = AI_ROOT / "services" / "ai_inference"
HELPERS = AI_ROOT / "tests" / "helpers"
for entry in (SERVICES, HELPERS):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

from emlis_ai_nls_v3_artifact_contract import canonical_json_bytes  # noqa: E402
from emlis_ai_reply_service import (  # noqa: E402
    _render_emlis_ai_reply_v3_dormant,
    render_emlis_ai_reply,
)
from emlis_ai_step10_evidence_v3 import (  # noqa: E402
    CaseEvidenceBundle,
    RUNNER_CASE_FAILURE_CODES,
    Step10EvidenceError,
    build_batch_evidence,
    build_case_evidence,
    commitment_key_id,
    validate_historical_batch_run_summary,
)
from emlis_ai_dormant_runtime_adapter_v3 import (  # noqa: E402
    DormantRuntimeAdapterError,
)
from emlis_ai_step10_dependency_manifest_v3 import (  # noqa: E402
    FROZEN_STEP10_CANDIDATE_VERSION_ID,
    fresh_step10_source_closure_sha256,
    step10_source_file_sha256,
)
from emlis_nls_v3_s2_sample_registry import (  # noqa: E402
    load_canonical_json,
    load_canonical_jsonl,
    validate_batch_manifest,
)


_FATAL_CASE_CODES = frozenset(
    {
        "EXECUTION_SAMPLE_INPUT_MISMATCH",
        "RUNTIME_EXECUTION_DEPENDENCY_DRIFT",
        "RUNTIME_EXECUTION_DEPENDENCY_MISMATCH",
        "RUNTIME_EXECUTION_SOURCE_LINEAGE_INVALID",
        "RUNTIME_EXECUTION_SOURCE_LINEAGE_MISMATCH",
        "RUNNER_OWNER_HASH_UNFROZEN",
        "SAMPLE_VALIDATOR_OWNER_UNAVAILABLE",
        "STEP10_DEPENDENCY_DRIFT",
    }
)
_FATAL_CASE_CODE_PREFIXES = (
    "PREVIOUS_RECEIPT_",
    "RUNTIME_EXECUTION_DEPENDENCY_",
    "RUNTIME_EXECUTION_SOURCE_LINEAGE_",
    "STEP10_DEPENDENCY_",
)
_PASSED_PRIVACY_REVIEW = {
    "status": "passed",
    "reviewer": "karen",
    "pii_absent": True,
    "real_user_text_copy_absent": True,
    "expected_response_absent": True,
}


def _resolve_repo_ref(value: Any) -> Path:
    if type(value) is not str:
        raise ValueError("manifest_ref_invalid")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("manifest_ref_unsafe")
    resolved = (REPO_ROOT / path).resolve()
    if REPO_ROOT.resolve() not in resolved.parents:
        raise ValueError("manifest_ref_outside_repo")
    return resolved


def load_validated_batch(
    batch_path: Path,
    manifest_path: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    samples = load_canonical_jsonl(batch_path)
    manifest = load_canonical_json(manifest_path)
    if type(manifest) is not dict:
        raise ValueError("batch_manifest_mapping_required")
    if (
        manifest.get("state") != "VALIDATED"
        or manifest.get("frozen") is not True
        or manifest.get("privacy_review") != _PASSED_PRIVACY_REVIEW
    ):
        raise ValueError("batch_manifest_not_validated_frozen_private_reviewed")
    corpus_path = _resolve_repo_ref(manifest.get("corpus_file_ref"))
    if corpus_path != batch_path.resolve():
        raise ValueError("batch_manifest_corpus_path_mismatch")
    issues = validate_batch_manifest(
        manifest,
        samples,
        corpus_path=corpus_path,
        coverage_matrix_path=_resolve_repo_ref(manifest.get("coverage_matrix_ref")),
        duplicate_report_path=_resolve_repo_ref(manifest.get("duplicate_report_ref")),
        expected_state="VALIDATED",
        expected_frozen=True,
        expected_privacy_review=_PASSED_PRIVACY_REVIEW,
        expected_near_review_decisions=manifest.get("near_review_decisions", ()),
        expected_invalid_case_history=manifest.get("invalid_case_history", ()),
    )
    if issues:
        raise ValueError(f"batch_manifest_invalid:{issues[0]}")
    return samples, manifest


def _secure_parent_dirfd(
    path: Path,
    *,
    create_parents: bool,
    parent_mode: int = 0o700,
) -> tuple[int, str]:
    """Open every ancestor without following links and return its dirfd.

    A preflight ``resolve()`` check alone is subject to an ancestor-symlink
    swap before the later file open.  Keeping each opened directory as the
    authority for the next ``openat``/``mkdirat`` step closes that race for the
    private packet and commitment key paths.
    """

    absolute = Path(os.path.abspath(os.fspath(path)))
    parts = absolute.parts
    if not absolute.is_absolute() or len(parts) < 2:
        raise ValueError("step10_secure_path_invalid")
    if any(part in {"", ".", ".."} for part in parts[1:]):
        raise ValueError("step10_secure_path_invalid")
    if not hasattr(os, "O_DIRECTORY") or not hasattr(os, "O_NOFOLLOW"):
        raise ValueError("step10_secure_nofollow_unavailable")
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    if hasattr(os, "O_CLOEXEC"):
        directory_flags |= os.O_CLOEXEC
    current = os.open(parts[0], directory_flags)
    try:
        for component in parts[1:-1]:
            try:
                following = os.open(
                    component,
                    directory_flags,
                    dir_fd=current,
                )
            except FileNotFoundError:
                if not create_parents:
                    raise
                os.mkdir(component, mode=parent_mode, dir_fd=current)
                following = os.open(
                    component,
                    directory_flags,
                    dir_fd=current,
                )
            os.close(current)
            current = following
        return current, parts[-1]
    except BaseException:
        os.close(current)
        raise


def _secure_unlink(path: Path) -> None:
    parent_fd, name = _secure_parent_dirfd(path, create_parents=False)
    try:
        os.unlink(name, dir_fd=parent_fd)
    finally:
        os.close(parent_fd)


def _read_key(path: Path) -> bytes:
    lexical = path.absolute()
    repo = REPO_ROOT.resolve()
    if repo == lexical or repo in lexical.parents:
        raise ValueError("commitment_key_file_must_be_outside_repo")
    resolved = path.resolve()
    if repo == resolved or repo in resolved.parents:
        raise ValueError("commitment_key_file_must_be_outside_repo")
    flags = os.O_RDONLY | os.O_NOFOLLOW
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    parent_fd: int | None = None
    try:
        parent_fd, name = _secure_parent_dirfd(path, create_parents=False)
        descriptor = os.open(name, flags, dir_fd=parent_fd)
    except OSError as exc:
        raise ValueError("commitment_key_file_open_rejected") from exc
    finally:
        if parent_fd is not None:
            os.close(parent_fd)
    try:
        status = os.fstat(descriptor)
        if not stat_module.S_ISREG(status.st_mode):
            raise ValueError("commitment_key_file_must_be_regular")
        if stat_module.S_IMODE(status.st_mode) != 0o600:
            raise ValueError("commitment_key_file_permissions_must_be_0600")
        if hasattr(os, "getuid") and status.st_uid != os.getuid():
            raise ValueError("commitment_key_file_owner_mismatch")
        chunks: list[bytes] = []
        remaining = 257
        while remaining:
            chunk = os.read(descriptor, remaining)
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
        if len(raw) == 257:
            raise ValueError("commitment_key_file_too_large")
    finally:
        os.close(descriptor)
    if len(raw) == 32:
        return raw
    try:
        text = raw.decode("ascii", errors="strict").strip()
        key = bytes.fromhex(text)
    except (UnicodeError, ValueError) as exc:
        raise ValueError("commitment_key_file_invalid") from exc
    if len(key) != 32:
        raise ValueError("commitment_key_file_must_hold_32_bytes")
    return key


async def _v1_body(current_input: dict[str, Any], case_id: str) -> bytes:
    reply = await render_emlis_ai_reply(
        user_id=f"nls-v3-step10-local-{case_id}",
        subscription_tier="free",
        current_input=current_input,
    )
    body = reply.comment_text
    if type(body) is not str:
        raise ValueError("V1_BASELINE_PUBLIC_CONTRACT_REJECTED")
    return body.encode("utf-8", errors="strict")


def _previous_by_case(
    summary: Mapping[str, Any] | None,
) -> tuple[str | None, dict[str, dict[str, Any]]]:
    if summary is None:
        return None, {}
    if validate_historical_batch_run_summary(summary):
        raise ValueError("previous_summary_contract_invalid")
    rows = summary.get("case_rows") if type(summary) is dict else None
    if type(rows) is not list:
        raise ValueError("previous_summary_case_rows_invalid")
    return summary.get("commitment_key_id"), {
        row["case_id"]: row["receipt"]
        for row in rows
        if type(row) is dict and type(row.get("receipt")) is dict
    }


def run_batch(
    samples: Sequence[Mapping[str, Any]],
    manifest: Mapping[str, Any],
    *,
    candidate_version_id: str,
    run_id: str,
    commitment_key: bytes,
    previous_summary: Mapping[str, Any] | None = None,
    limit: int | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if candidate_version_id != FROZEN_STEP10_CANDIDATE_VERSION_ID:
        raise ValueError("candidate_version_not_frozen_step10_rc")
    source_closure_start_sha256 = fresh_step10_source_closure_sha256()
    selected_samples = list(samples if limit is None else samples[:limit])
    previous_key_id, previous = _previous_by_case(previous_summary)
    manifest_sha256 = hashlib.sha256(
        canonical_json_bytes(dict(manifest)) + b"\n"
    ).hexdigest()
    if previous_summary is not None:
        if previous_summary.get("batch_id") != manifest.get("batch_id"):
            raise ValueError("previous_summary_batch_mismatch")
        if previous_summary.get("run_id") == run_id:
            raise ValueError("previous_summary_run_id_reuse")
        if previous_key_id != commitment_key_id(commitment_key):
            raise ValueError("previous_summary_commitment_key_mismatch")
        if previous_summary.get("batch_manifest_sha256") != manifest_sha256:
            raise ValueError("previous_summary_manifest_mismatch")
    bundles: list[CaseEvidenceBundle] = []
    failures: list[dict[str, Any]] = []
    runner_sha256 = step10_source_file_sha256(
        "ai/tools/emlis_nls_v3_batch_run.py"
    )
    if type(runner_sha256) is not str:
        raise ValueError("batch_runner_owner_hash_unfrozen")
    for sample in selected_samples:
        case_id = str(sample.get("case_id") or "")
        current_input = sample.get("input")
        v1_body: bytes | None = None
        try:
            if type(current_input) is not dict:
                raise ValueError("SAMPLE_GENERATION_INPUT_INVALID")
            v1_body = asyncio.run(_v1_body(dict(current_input), case_id))
        except ValueError:
            failures.append(
                {
                    "case_id": case_id,
                    "failure_code": "V1_BASELINE_EXECUTION_REJECTED",
                    "sample_case": dict(sample),
                    "v1_body_utf8": None,
                }
            )
            continue
        try:
            # Only the actual app input projection reaches generation.  Case ID,
            # coverage family and expected semantic annotations stay outside.
            execution = _render_emlis_ai_reply_v3_dormant(
                current_input=dict(current_input),
                candidate_version_id=candidate_version_id,
            )
            bundles.append(
                build_case_evidence(
                    execution,
                    sample_case=sample,
                    v1_body_utf8=v1_body,
                    commitment_key=commitment_key,
                    run_id=run_id,
                    runner_sha256=runner_sha256,
                    previous_receipt=previous.get(case_id),
                    previous_commitment_key_id=(
                        previous_key_id if case_id in previous else None
                    ),
                )
            )
        except (DormantRuntimeAdapterError, Step10EvidenceError) as exc:
            code = (
                getattr(exc, "code", None)
                if isinstance(exc, (DormantRuntimeAdapterError, Step10EvidenceError))
                else None
            )
            if (
                code in _FATAL_CASE_CODES
                or (
                    type(code) is str
                    and code.startswith(_FATAL_CASE_CODE_PREFIXES)
                )
            ):
                raise
            if isinstance(exc, Step10EvidenceError):
                code = "STEP10_EVIDENCE_BUILD_REJECTED"
            else:
                code = "STEP10_CASE_EXECUTION_REJECTED"
            if code not in RUNNER_CASE_FAILURE_CODES:
                raise AssertionError("runner_failure_taxonomy_drift")
            failures.append(
                {
                    "case_id": case_id,
                    "failure_code": code,
                    "sample_case": dict(sample),
                    "v1_body_utf8": v1_body,
                }
            )
    source_closure_end_sha256 = fresh_step10_source_closure_sha256()
    return build_batch_evidence(
        bundles,
        failure_rows=failures,
        batch_id=str(manifest["batch_id"]),
        run_id=run_id,
        candidate_version_id=candidate_version_id,
        batch_manifest_sha256=manifest_sha256,
        expected_case_count=int(manifest["case_count"]),
        commitment_key=commitment_key,
        source_closure_start_sha256=source_closure_start_sha256,
        source_closure_end_sha256=source_closure_end_sha256,
    )


def _write_json(path: Path, value: Any, *, private: bool) -> None:
    payload = canonical_json_bytes(value) + b"\n"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    descriptor: int | None = None
    parent_fd: int | None = None
    name: str | None = None
    created = False
    try:
        parent_fd, name = _secure_parent_dirfd(
            path,
            create_parents=True,
            parent_mode=0o700 if private else 0o755,
        )
        descriptor = os.open(
            name,
            flags,
            0o600 if private else 0o644,
            dir_fd=parent_fd,
        )
        created = True
        with os.fdopen(descriptor, "wb", closefd=False) as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        if created and parent_fd is not None and name is not None:
            try:
                os.unlink(name, dir_fd=parent_fd)
            except OSError:
                pass
        raise
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if parent_fd is not None:
            os.close(parent_fd)
    return None


def _validate_cli_paths(args: argparse.Namespace) -> None:
    inputs = [args.batch, args.manifest, args.commitment_key_file]
    if args.previous_summary is not None:
        inputs.append(args.previous_summary)
    outputs = [args.private_output, args.body_free_output]
    resolved = [path.resolve() for path in [*inputs, *outputs]]
    if len(resolved) != len(set(resolved)):
        raise ValueError("step10_cli_path_collision")
    private = args.private_output.resolve()
    private_lexical = args.private_output.absolute()
    if (
        private == REPO_ROOT.resolve()
        or REPO_ROOT.resolve() in private.parents
        or private_lexical == REPO_ROOT.resolve()
        or REPO_ROOT.resolve() in private_lexical.parents
    ):
        raise ValueError("private_packet_must_be_outside_repo")
    if any(path.exists() for path in outputs):
        raise ValueError("step10_output_already_exists")
    if args.limit is not None and (
        type(args.limit) is not int or args.limit < 1
    ):
        raise ValueError("step10_limit_must_be_positive")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run frozen NLS v3 fixtures through the default-off adapter."
    )
    parser.add_argument("--batch", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--candidate-version", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--commitment-key-file", type=Path, required=True)
    parser.add_argument("--private-output", type=Path, required=True)
    parser.add_argument("--body-free-output", type=Path, required=True)
    parser.add_argument("--previous-summary", type=Path)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args(argv)
    _validate_cli_paths(args)
    samples, manifest = load_validated_batch(
        args.batch.resolve(), args.manifest.resolve()
    )
    previous = (
        load_canonical_json(args.previous_summary)
        if args.previous_summary is not None
        else None
    )
    private_packet, summary = run_batch(
        samples,
        manifest,
        candidate_version_id=args.candidate_version,
        run_id=args.run_id,
        commitment_key=_read_key(args.commitment_key_file),
        previous_summary=previous,
        limit=args.limit,
    )
    private_written = False
    try:
        _write_json(args.private_output, private_packet, private=True)
        private_written = True
        _write_json(args.body_free_output, summary, private=False)
    except BaseException:
        if private_written:
            try:
                _secure_unlink(args.private_output)
            except OSError:
                pass
        raise
    return 0 if summary["machine_status"] == "clean" else 2


if __name__ == "__main__":
    raise SystemExit(main())
