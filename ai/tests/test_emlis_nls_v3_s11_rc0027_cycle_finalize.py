# -*- coding: utf-8 -*-
from __future__ import annotations

"""rc0027 finalizer boundary over exact clean rc0026 public parents."""

import inspect

import pytest

from emlis_ai_nls_v3_artifact_contract import artifact_sha256
from emlis_ai_step11_cycle_evidence_v3 import build_step11_dependency_manifest
import emlis_nls_v3_step11_cycle_finalize as finalizer
import emlis_nls_v3_step11_dependency_manifest as dependency_tool
from test_emlis_nls_v3_s11_rc0021_append_only_lineage import _commitment


_RC0027_ADDED_PATHS = (
    "ai/services/ai_inference/emlis_ai_step11_grounded_lexicalization_v3.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0027_append_only_lineage.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0027_cycle_finalize.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0027_grounded_lexicalization_red.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0027_product_surface_contract_red.py",
)


def _rc0026_product_read_failure() -> dict[str, object]:
    return {
        "schema_version": finalizer._RC0026_PRODUCT_READ_FAILURE_SCHEMA,
        "candidate_version_id": "nls_v3_rc_0026",
        "batch_summary_sha256": (
            finalizer.FROZEN_RC0026_FORMAL_BATCH_SUMMARY_SHA256
        ),
        "private_verification_receipt_sha256": (
            finalizer.FROZEN_RC0026_FORMAL_PRIVATE_VERIFICATION_SHA256
        ),
        "known28_receipt_sha256": (
            finalizer.FROZEN_RC0026_KNOWN28_RECEIPT_SHA256
        ),
        "development42_receipt_sha256": (
            finalizer.FROZEN_RC0026_DEVELOPMENT42_RECEIPT_SHA256
        ),
        "invalid16_receipt_sha256": (
            finalizer.FROZEN_RC0026_INVALID16_RECEIPT_SHA256
        ),
        "review_outcome": "failed",
        "maximum_severity": "MAJOR",
        "failure_axis_codes": list(
            finalizer.FROZEN_RC0026_PRODUCT_READ_FAILURE_AXES
        ),
        "failure_reason_codes": list(
            finalizer.FROZEN_RC0026_PRODUCT_READ_FAILURE_REASONS
        ),
        "body_free": True,
    }


def test_rc0027_finalizer_requires_exact_rc0026_public_parents() -> None:
    parameters = inspect.signature(finalizer.build_cycle_artifacts).parameters
    for name in (
        "rc0026_final_summary",
        "rc0026_private_verification_receipt",
        "rc0026_product_read_failure",
        "rc0026_known28_receipt",
        "rc0026_development42_receipt",
        "rc0026_invalid16_receipt",
    ):
        assert name in parameters
        assert parameters[name].default is inspect.Parameter.empty

    wrapper = getattr(finalizer, "_build_rc0010_rc0027_lineage", None)
    assert callable(wrapper)
    wrapper_parameters = inspect.signature(wrapper).parameters
    for name in (
        "rc0026_private_verification_receipt",
        "rc0026_product_read_failure",
        "rc0026_known28_receipt",
        "rc0026_development42_receipt",
        "rc0026_invalid16_receipt",
    ):
        assert name in wrapper_parameters
        assert wrapper_parameters[name].default is inspect.Parameter.empty

    main_source = inspect.getsource(finalizer.main)
    for flag in (
        "rc0026-final-summary",
        "rc0026-private-verification-receipt",
        "rc0026-product-read-failure",
        "rc0026-known28-receipt",
        "rc0026-development42-receipt",
        "rc0026-invalid16-receipt",
    ):
        assert flag in main_source


def test_rc0027_exact_rc0026_private_verification_shape(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt = {
        "schema_version": (
            "cocolon.emlis.nls_v3.private_verification_receipt.step11.v1"
        ),
        "candidate_version_id": "nls_v3_rc_0026",
        "dependency_manifest_sha256": (
            finalizer.FROZEN_RC0026_FORMAL_MANIFEST_ARTIFACT_SHA256
        ),
        "source_dependency_closure_sha256": (
            finalizer.FROZEN_RC0026_FORMAL_SOURCE_CLOSURE_SHA256
        ),
        "final_batch_summary_sha256": (
            finalizer.FROZEN_RC0026_FORMAL_BATCH_SUMMARY_SHA256
        ),
        "verified_case_count": 100,
        "verified_selected_count": 100,
        "verified_no_valid_candidate_count": 0,
        "verified_exception_count": 0,
        "private_packet_validation_status": "clean",
        "body_free": True,
    }
    monkeypatch.setattr(
        finalizer,
        "artifact_sha256",
        lambda value: (
            finalizer.FROZEN_RC0026_FORMAL_PRIVATE_VERIFICATION_SHA256
        ),
    )

    finalizer._validate_frozen_rc0026_private_verification(receipt)
    with pytest.raises(ValueError):
        finalizer._validate_frozen_rc0026_private_verification(
            {**receipt, "verified_selected_count": 0}
        )


def test_rc0027_rc0026_product_read_major_is_exact() -> None:
    failure = _rc0026_product_read_failure()
    assert artifact_sha256(failure) == (
        finalizer.FROZEN_RC0026_PRODUCT_READ_FAILURE_SHA256
    )

    validated = finalizer._validated_product_read_failure(
        failure,
        schema_version=finalizer._RC0026_PRODUCT_READ_FAILURE_SCHEMA,
        candidate_version_id="nls_v3_rc_0026",
        batch_summary_sha256=(
            finalizer.FROZEN_RC0026_FORMAL_BATCH_SUMMARY_SHA256
        ),
        failure_axis_codes=finalizer.FROZEN_RC0026_PRODUCT_READ_FAILURE_AXES,
        failure_reason_codes=(
            finalizer.FROZEN_RC0026_PRODUCT_READ_FAILURE_REASONS
        ),
        maximum_severity="MAJOR",
        exact_parent_receipt_sha256s={
            "private_verification_receipt_sha256": (
                finalizer.FROZEN_RC0026_FORMAL_PRIVATE_VERIFICATION_SHA256
            ),
            "known28_receipt_sha256": (
                finalizer.FROZEN_RC0026_KNOWN28_RECEIPT_SHA256
            ),
            "development42_receipt_sha256": (
                finalizer.FROZEN_RC0026_DEVELOPMENT42_RECEIPT_SHA256
            ),
            "invalid16_receipt_sha256": (
                finalizer.FROZEN_RC0026_INVALID16_RECEIPT_SHA256
            ),
        },
    )
    assert validated == failure
    with pytest.raises(ValueError):
        finalizer._validated_product_read_failure(
            {**failure, "maximum_severity": "BLOCKER"},
            schema_version=finalizer._RC0026_PRODUCT_READ_FAILURE_SCHEMA,
            candidate_version_id="nls_v3_rc_0026",
            batch_summary_sha256=(
                finalizer.FROZEN_RC0026_FORMAL_BATCH_SUMMARY_SHA256
            ),
            failure_axis_codes=(
                finalizer.FROZEN_RC0026_PRODUCT_READ_FAILURE_AXES
            ),
            failure_reason_codes=(
                finalizer.FROZEN_RC0026_PRODUCT_READ_FAILURE_REASONS
            ),
            maximum_severity="MAJOR",
            exact_parent_receipt_sha256s={
                "private_verification_receipt_sha256": (
                    finalizer.FROZEN_RC0026_FORMAL_PRIVATE_VERIFICATION_SHA256
                ),
                "known28_receipt_sha256": (
                    finalizer.FROZEN_RC0026_KNOWN28_RECEIPT_SHA256
                ),
                "development42_receipt_sha256": (
                    finalizer.FROZEN_RC0026_DEVELOPMENT42_RECEIPT_SHA256
                ),
                "invalid16_receipt_sha256": (
                    finalizer.FROZEN_RC0026_INVALID16_RECEIPT_SHA256
                ),
            },
        )


def test_rc0027_exact_rc0026_regression_bindings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    summary = {"run_id": "nls3run_0026c00100000001"}
    manifest: dict[str, object] = {}

    def receipt(run_suffix: str, schema_version: str) -> dict[str, object]:
        return {
            "schema_version": schema_version,
            "candidate_version_id": "nls_v3_rc_0026",
            "final_batch_summary_sha256": (
                finalizer.FROZEN_RC0026_FORMAL_BATCH_SUMMARY_SHA256
            ),
            "source_dependency_closure_sha256": (
                finalizer.FROZEN_RC0026_FORMAL_SOURCE_CLOSURE_SHA256
            ),
            "formal_status": "clean",
            "body_free": True,
            "run_id": f"nls3run_0026c0010000000{run_suffix}",
        }

    known = receipt("2", "cocolon.emlis.nls_v3.known28_receipt.v3")
    development = receipt(
        "3", "cocolon.emlis.nls_v3.development42_receipt.step11.v1"
    )
    invalid = receipt("4", "cocolon.emlis.nls_v3.invalid16_receipt.v2")
    exact_hashes = {
        id(known): finalizer.FROZEN_RC0026_KNOWN28_RECEIPT_SHA256,
        id(development): (
            finalizer.FROZEN_RC0026_DEVELOPMENT42_RECEIPT_SHA256
        ),
        id(invalid): finalizer.FROZEN_RC0026_INVALID16_RECEIPT_SHA256,
    }
    monkeypatch.setattr(
        finalizer,
        "artifact_sha256",
        lambda value: exact_hashes.get(id(value), "0" * 64),
    )
    monkeypatch.setattr(finalizer, "validate_known28_receipt", lambda *a, **k: ())
    monkeypatch.setattr(
        finalizer, "validate_development42_receipt", lambda *a, **k: ()
    )
    monkeypatch.setattr(finalizer, "validate_invalid16_receipt", lambda *a, **k: ())

    assert finalizer._validated_frozen_rc0026_regression_bindings(
        known28_receipt=known,
        development42_receipt=development,
        invalid16_receipt=invalid,
        final_batch_summary=summary,
        dependency_manifest=manifest,
    ) == {
        "known28_receipt_sha256": (
            finalizer.FROZEN_RC0026_KNOWN28_RECEIPT_SHA256
        ),
        "development42_receipt_sha256": (
            finalizer.FROZEN_RC0026_DEVELOPMENT42_RECEIPT_SHA256
        ),
        "invalid16_receipt_sha256": (
            finalizer.FROZEN_RC0026_INVALID16_RECEIPT_SHA256
        ),
    }


def test_rc0027_manifest_is_exact_156_plus_five_new_source_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = [
        {
            "path": f"ai/tests/frozen_rc0026/path_{index:03d}.py",
            "sha256": _commitment(f"rc26:{index}"),
        }
        for index in range(156)
    ]
    rc26 = build_step11_dependency_manifest(
        before_candidate_version_id="nls_v3_rc_0025",
        before_source_closure_sha256=_commitment("rc25"),
        candidate_version_id="nls_v3_rc_0026",
        file_hashes=rows,
        changed_file_hashes=rows[:1],
    )
    changed_path = rows[40]["path"]
    current = {row["path"]: row["sha256"] for row in rows}
    current[changed_path] = _commitment("rc27:changed")
    for path in _RC0027_ADDED_PATHS:
        current[path] = _commitment(f"rc27:{path}")
    monkeypatch.setattr(
        dependency_tool,
        "FROZEN_RC0026_FORMAL_MANIFEST_ARTIFACT_SHA256",
        artifact_sha256(rc26),
    )
    monkeypatch.setattr(
        dependency_tool,
        "FROZEN_RC0026_FORMAL_SOURCE_CLOSURE_SHA256",
        rc26["source_dependency_closure_sha256"],
    )
    monkeypatch.setattr(
        dependency_tool,
        "FROZEN_RC0025_FORMAL_SOURCE_CLOSURE_SHA256",
        rc26["before_source_closure_sha256"],
    )
    monkeypatch.setattr(dependency_tool, "_sha256", lambda path: current[path])

    assert dependency_tool.RC0027_ADDED_SOURCE_PATHS == _RC0027_ADDED_PATHS
    result = dependency_tool.build_current_step11_dependency_manifest(rc26)

    assert result["before_candidate_version_id"] == "nls_v3_rc_0026"
    assert result["candidate_version_id"] == "nls_v3_rc_0027"
    assert len(result["file_hashes"]) == 161
    assert {row["path"] for row in result["changed_file_hashes"]} == {
        changed_path,
        *_RC0027_ADDED_PATHS,
    }
