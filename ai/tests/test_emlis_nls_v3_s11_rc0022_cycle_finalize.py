# -*- coding: utf-8 -*-
from __future__ import annotations

"""rc0022 finalizer boundary and body-free historical-parent REDs."""

from copy import deepcopy
import inspect

import pytest

from emlis_ai_nls_v3_artifact_contract import artifact_sha256
import emlis_nls_v3_step11_cycle_finalize as finalizer


def _rc0021_product_read_failure() -> dict[str, object]:
    return {
        "schema_version": (
            "cocolon.emlis.nls_v3.product_read_failure.step11.rc0021.v1"
        ),
        "candidate_version_id": "nls_v3_rc_0021",
        "batch_summary_sha256": (
            finalizer.FROZEN_RC0021_PREFLIGHT_BATCH_SUMMARY_SHA256
        ),
        "review_outcome": "failed",
        "maximum_severity": "MAJOR",
        "failure_axis_codes": [
            "BOUND_EMLIS_RECEPTION",
            "IMMEDIATE_OBSERVATION_FEELS_READ",
            "NATURAL_NON_REPETITIVE_SURFACE",
        ],
        "failure_reason_codes": [
            "EMLIS_RECEPTION_UNBOUND",
            "IMMEDIATE_OBSERVATION_NOT_READ",
            "SURFACE_UNNATURAL_OR_REPETITIVE",
        ],
        "failure_case_ids": ["nls3s_b001_0035"],
        "body_free": True,
    }


def _validate_rc0021_product_read(value: dict[str, object]) -> None:
    finalizer._validated_product_read_failure(
        value,
        schema_version=finalizer._RC0021_PRODUCT_READ_FAILURE_SCHEMA,
        candidate_version_id="nls_v3_rc_0021",
        batch_summary_sha256=(
            finalizer.FROZEN_RC0021_PREFLIGHT_BATCH_SUMMARY_SHA256
        ),
        failure_axis_codes=(
            "BOUND_EMLIS_RECEPTION",
            "IMMEDIATE_OBSERVATION_FEELS_READ",
            "NATURAL_NON_REPETITIVE_SURFACE",
        ),
        failure_reason_codes=(
            "EMLIS_RECEPTION_UNBOUND",
            "IMMEDIATE_OBSERVATION_NOT_READ",
            "SURFACE_UNNATURAL_OR_REPETITIVE",
        ),
        failure_case_ids=("nls3s_b001_0035",),
    )


def test_rc0022_finalizer_requires_case0035_rc0021_product_read() -> None:
    _validate_rc0021_product_read(_rc0021_product_read_failure())


@pytest.mark.parametrize(
    ("field", "replacement"),
    (
        ("failure_case_ids", ["nls3s_b001_0068"]),
        ("maximum_severity", "MINOR"),
        ("candidate_version_id", "nls_v3_rc_0022"),
        ("batch_summary_sha256", "1" * 64),
    ),
)
def test_rc0022_finalizer_rejects_relabelled_rc0021_product_read(
    field: str,
    replacement: object,
) -> None:
    value = _rc0021_product_read_failure()
    value[field] = replacement
    with pytest.raises(ValueError):
        _validate_rc0021_product_read(value)


def test_rc0021_private_verification_parent_is_body_free_and_keyless(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt = {
        "schema_version": (
            "cocolon.emlis.nls_v3.private_verification_receipt.step11.v1"
        ),
        "candidate_version_id": "nls_v3_rc_0021",
        "source_dependency_closure_sha256": "2" * 64,
        "final_batch_summary_sha256": "3" * 64,
        "verified_case_count": 100,
        "verified_selected_count": 100,
        "verified_no_valid_candidate_count": 0,
        "verified_exception_count": 0,
        "private_packet_validation_status": "clean",
        "commitment_key_id": "4" * 64,
        "body_free": True,
    }
    monkeypatch.setattr(
        finalizer,
        "FROZEN_RC0021_PREFLIGHT_PRIVATE_VERIFICATION_SHA256",
        artifact_sha256(receipt),
    )
    monkeypatch.setattr(
        finalizer,
        "FROZEN_RC0021_PREFLIGHT_SOURCE_CLOSURE_SHA256",
        receipt["source_dependency_closure_sha256"],
    )
    monkeypatch.setattr(
        finalizer,
        "FROZEN_RC0021_PREFLIGHT_BATCH_SUMMARY_SHA256",
        receipt["final_batch_summary_sha256"],
    )

    finalizer._validate_frozen_rc0021_private_verification(receipt)

    forged = {**receipt, "hmac_key_hex": "not-permitted"}
    monkeypatch.setattr(
        finalizer,
        "FROZEN_RC0021_PREFLIGHT_PRIVATE_VERIFICATION_SHA256",
        artifact_sha256(forged),
    )
    with pytest.raises(ValueError):
        finalizer._validate_frozen_rc0021_private_verification(forged)


def test_rc0021_and_rc0022_scope_aliases_remain_historical_for_rc0023(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    historical_rc20 = {
        "schema_version": "historical.rc20",
        "candidate_version_id": "nls_v3_rc_0020",
        "body_free": True,
    }
    monkeypatch.setattr(
        finalizer,
        "build_historical_rc0020_available_input_scope_receipt",
        lambda **_: deepcopy(historical_rc20),
    )
    parents = {
        "step1_baseline_receipt": {},
        "step1_input_contract": {},
        "step2_corpus_registry": {},
    }

    historical_rc21 = (
        finalizer.build_historical_rc0021_available_input_scope_receipt(
            **parents
        )
    )
    historical_rc22 = (
        finalizer.build_historical_rc0022_available_input_scope_receipt(
            **parents
        )
    )
    current_rc23 = finalizer.build_available_input_scope_receipt(**parents)

    assert historical_rc21["candidate_version_id"] == "nls_v3_rc_0021"
    assert historical_rc21["schema_version"].endswith(".rc0021.v1")
    assert historical_rc22["candidate_version_id"] == "nls_v3_rc_0022"
    assert historical_rc22["schema_version"].endswith(".rc0022.v1")
    assert current_rc23["candidate_version_id"] == "nls_v3_rc_0023"
    assert current_rc23["schema_version"].endswith(".rc0023.v1")


def test_rc0022_finalizer_requires_both_historical_failure_inputs() -> None:
    parameters = inspect.signature(finalizer.build_cycle_artifacts).parameters
    assert "rc0020_product_read_failure" in parameters
    assert "rc0021_product_read_failure" in parameters
    assert "rc0021_private_verification_receipt" in parameters
    assert "rc0022_private_verification_receipt" in parameters
