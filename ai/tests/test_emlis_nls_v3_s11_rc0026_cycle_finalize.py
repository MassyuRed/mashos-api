# -*- coding: utf-8 -*-
from __future__ import annotations

"""rc0026 finalizer boundary over clean rc0025 and its BLOCKER review."""

import inspect

import pytest

import emlis_nls_v3_step11_cycle_finalize as finalizer


_CURRENT_RESULT_PARAMETERS = (
    "final_summary",
    "final_decisions",
    "private_verification_receipt",
    "known28_receipt",
    "development42_receipt",
    "invalid16_receipt",
)


def _rc0025_product_read_failure() -> dict[str, object]:
    return {
        "schema_version": (
            "cocolon.emlis.nls_v3.product_read_failure.step11.rc0025.v1"
        ),
        "candidate_version_id": "nls_v3_rc_0025",
        "batch_summary_sha256": (
            finalizer.FROZEN_RC0025_FORMAL_BATCH_SUMMARY_SHA256
        ),
        "private_verification_receipt_sha256": (
            finalizer.FROZEN_RC0025_FORMAL_PRIVATE_VERIFICATION_SHA256
        ),
        "known28_receipt_sha256": (
            finalizer.FROZEN_RC0025_KNOWN28_RECEIPT_SHA256
        ),
        "development42_receipt_sha256": (
            finalizer.FROZEN_RC0025_DEVELOPMENT42_RECEIPT_SHA256
        ),
        "invalid16_receipt_sha256": (
            finalizer.FROZEN_RC0025_INVALID16_RECEIPT_SHA256
        ),
        "review_outcome": "failed",
        "maximum_severity": "BLOCKER",
        "failure_axis_codes": list(
            finalizer.FROZEN_RC0025_PRODUCT_READ_FAILURE_AXES
        ),
        "failure_reason_codes": list(
            finalizer.FROZEN_RC0025_PRODUCT_READ_FAILURE_REASONS
        ),
        "body_free": True,
    }


def test_rc0026_finalizer_requires_exact_rc0025_parents() -> None:
    parameters = inspect.signature(finalizer.build_cycle_artifacts).parameters

    for name in (
        *_CURRENT_RESULT_PARAMETERS,
        "rc0025_private_verification_receipt",
        "rc0025_product_read_failure",
        "rc0025_known28_receipt",
        "rc0025_development42_receipt",
        "rc0025_invalid16_receipt",
    ):
        assert name in parameters
        assert parameters[name].default is inspect.Parameter.empty

    wrapper = getattr(finalizer, "_build_rc0010_rc0026_lineage", None)
    assert callable(wrapper)
    wrapper_parameters = inspect.signature(wrapper).parameters
    assert "rc0025_private_verification_receipt" in wrapper_parameters
    assert "rc0025_product_read_failure" in wrapper_parameters
    assert "rc0025_known28_receipt" in wrapper_parameters
    assert "rc0025_development42_receipt" in wrapper_parameters
    assert "rc0025_invalid16_receipt" in wrapper_parameters


def test_rc0026_exact_rc0025_private_verification_shape(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt = {
        "candidate_version_id": "nls_v3_rc_0025",
        "dependency_manifest_sha256": (
            finalizer.FROZEN_RC0025_FORMAL_MANIFEST_ARTIFACT_SHA256
        ),
        "source_dependency_closure_sha256": (
            finalizer.FROZEN_RC0025_FORMAL_SOURCE_CLOSURE_SHA256
        ),
        "final_batch_summary_sha256": (
            finalizer.FROZEN_RC0025_FORMAL_BATCH_SUMMARY_SHA256
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
        lambda value: finalizer.FROZEN_RC0025_FORMAL_PRIVATE_VERIFICATION_SHA256,
    )

    finalizer._validate_frozen_rc0025_private_verification(receipt)
    with pytest.raises(ValueError):
        finalizer._validate_frozen_rc0025_private_verification(
            {**receipt, "verified_selected_count": 0}
        )


def test_rc0026_rc0025_product_read_blocker_is_exact() -> None:
    failure = _rc0025_product_read_failure()
    assert finalizer.artifact_sha256(failure) == (
        finalizer.FROZEN_RC0025_PRODUCT_READ_FAILURE_SHA256
    )

    validated = finalizer._validated_product_read_failure(
        failure,
        schema_version=finalizer._RC0025_PRODUCT_READ_FAILURE_SCHEMA,
        candidate_version_id="nls_v3_rc_0025",
        batch_summary_sha256=(
            finalizer.FROZEN_RC0025_FORMAL_BATCH_SUMMARY_SHA256
        ),
        failure_axis_codes=finalizer.FROZEN_RC0025_PRODUCT_READ_FAILURE_AXES,
        failure_reason_codes=(
            finalizer.FROZEN_RC0025_PRODUCT_READ_FAILURE_REASONS
        ),
        maximum_severity="BLOCKER",
        exact_parent_receipt_sha256s={
            "private_verification_receipt_sha256": (
                finalizer.FROZEN_RC0025_FORMAL_PRIVATE_VERIFICATION_SHA256
            ),
            "known28_receipt_sha256": (
                finalizer.FROZEN_RC0025_KNOWN28_RECEIPT_SHA256
            ),
            "development42_receipt_sha256": (
                finalizer.FROZEN_RC0025_DEVELOPMENT42_RECEIPT_SHA256
            ),
            "invalid16_receipt_sha256": (
                finalizer.FROZEN_RC0025_INVALID16_RECEIPT_SHA256
            ),
        },
    )
    assert validated == failure

    with pytest.raises(ValueError):
        finalizer._validated_product_read_failure(
            {**failure, "maximum_severity": "MAJOR"},
            schema_version=finalizer._RC0025_PRODUCT_READ_FAILURE_SCHEMA,
            candidate_version_id="nls_v3_rc_0025",
            batch_summary_sha256=(
                finalizer.FROZEN_RC0025_FORMAL_BATCH_SUMMARY_SHA256
            ),
            failure_axis_codes=(
                finalizer.FROZEN_RC0025_PRODUCT_READ_FAILURE_AXES
            ),
            failure_reason_codes=(
                finalizer.FROZEN_RC0025_PRODUCT_READ_FAILURE_REASONS
            ),
            maximum_severity="BLOCKER",
            exact_parent_receipt_sha256s={
                "private_verification_receipt_sha256": (
                    finalizer.FROZEN_RC0025_FORMAL_PRIVATE_VERIFICATION_SHA256
                ),
                "known28_receipt_sha256": (
                    finalizer.FROZEN_RC0025_KNOWN28_RECEIPT_SHA256
                ),
                "development42_receipt_sha256": (
                    finalizer.FROZEN_RC0025_DEVELOPMENT42_RECEIPT_SHA256
                ),
                "invalid16_receipt_sha256": (
                    finalizer.FROZEN_RC0025_INVALID16_RECEIPT_SHA256
                ),
            },
        )


def test_rc0026_exact_rc0025_regression_constants_and_bindings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert finalizer.FROZEN_RC0025_KNOWN28_RECEIPT_SHA256 == (
        "6e90569825d3f7e2f964a7aa54f26256668a4865193e3cd85f4ef3490d326ecb"
    )
    assert finalizer.FROZEN_RC0025_DEVELOPMENT42_RECEIPT_SHA256 == (
        "dafdf8aec57cf909c74315e734d961a4c129fb4d138c2be69a824e56d5ccdadf"
    )
    assert finalizer.FROZEN_RC0025_INVALID16_RECEIPT_SHA256 == (
        "c9a5a67f39574be8d12726ae7c7fae6828467ff1673430be0074ab717f7db440"
    )
    assert finalizer.FROZEN_RC0025_PRODUCT_READ_FAILURE_SHA256 == (
        "9e13435575e822e30874d7c7340430138c199554d371d36922ce06a1ec5ceea7"
    )

    summary = {"run_id": "nls3run_0025c00100000001"}
    manifest: dict[str, object] = {}
    known = {"run_id": "nls3run_0025c00100000002"}
    development = {"run_id": "nls3run_0025c00100000003"}
    invalid = {"run_id": "nls3run_0025c00100000004"}
    exact_hashes = {
        id(known): finalizer.FROZEN_RC0025_KNOWN28_RECEIPT_SHA256,
        id(development): (
            finalizer.FROZEN_RC0025_DEVELOPMENT42_RECEIPT_SHA256
        ),
        id(invalid): finalizer.FROZEN_RC0025_INVALID16_RECEIPT_SHA256,
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

    bindings = finalizer._validated_frozen_rc0025_regression_bindings(
        known28_receipt=known,
        development42_receipt=development,
        invalid16_receipt=invalid,
        final_batch_summary=summary,
        dependency_manifest=manifest,
    )
    assert bindings == {
        "known28_receipt_sha256": (
            finalizer.FROZEN_RC0025_KNOWN28_RECEIPT_SHA256
        ),
        "development42_receipt_sha256": (
            finalizer.FROZEN_RC0025_DEVELOPMENT42_RECEIPT_SHA256
        ),
        "invalid16_receipt_sha256": (
            finalizer.FROZEN_RC0025_INVALID16_RECEIPT_SHA256
        ),
    }

    monkeypatch.setattr(
        finalizer,
        "validate_known28_receipt",
        lambda *a, **k: ("KNOWN28_INVALID",),
    )
    with pytest.raises(ValueError):
        finalizer._validated_frozen_rc0025_regression_bindings(
            known28_receipt=known,
            development42_receipt=development,
            invalid16_receipt=invalid,
            final_batch_summary=summary,
            dependency_manifest=manifest,
        )
