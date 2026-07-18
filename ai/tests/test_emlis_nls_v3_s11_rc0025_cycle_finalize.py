# -*- coding: utf-8 -*-
from __future__ import annotations

"""rc0025 finalizer boundary over the immutable clean rc0024 parent."""

import inspect
import json
from pathlib import Path

import pytest

from emlis_ai_nls_v3_artifact_contract import artifact_sha256
import emlis_nls_v3_step11_cycle_finalize as finalizer


_CYCLE = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "emlis_nls_v3"
    / "cycle_001"
)
_PHASE_C_RESULT_PARAMETERS = (
    "final_summary",
    "final_decisions",
    "private_verification_receipt",
    "known28_receipt",
    "development42_receipt",
    "invalid16_receipt",
)


def test_rc0025_exact_frozen_rc0024_private_parent_is_required() -> None:
    receipt = json.loads(
        (_CYCLE / "cycle001_final_rc0024_private_verification.json").read_text(
            encoding="utf-8"
        )
    )

    assert artifact_sha256(receipt) == (
        finalizer.FROZEN_RC0024_FORMAL_PRIVATE_VERIFICATION_SHA256
    )
    finalizer._validate_frozen_rc0024_private_verification(receipt)

    with pytest.raises(ValueError):
        finalizer._validate_frozen_rc0024_private_verification(
            {**receipt, "verified_selected_count": 0}
        )


def test_rc0025_finalizer_has_no_phase_c_result_defaults() -> None:
    parameters = inspect.signature(finalizer.build_cycle_artifacts).parameters

    assert "rc0024_private_verification_receipt" in parameters
    assert parameters[
        "rc0024_private_verification_receipt"
    ].default is inspect.Parameter.empty
    for name in _PHASE_C_RESULT_PARAMETERS:
        assert name in parameters
        assert parameters[name].default is inspect.Parameter.empty


def test_rc0025_lineage_wrapper_requires_the_rc0024_private_parent() -> None:
    wrapper = getattr(finalizer, "_build_rc0010_rc0025_lineage", None)

    assert callable(wrapper)
    parameters = inspect.signature(wrapper).parameters
    assert "rc0024_private_verification_receipt" in parameters
    assert parameters[
        "rc0024_private_verification_receipt"
    ].default is inspect.Parameter.empty
    assert "rc0023_private_verification_receipt" in parameters
    assert parameters[
        "rc0023_private_verification_receipt"
    ].default is inspect.Parameter.empty


def test_rc0025_finalizer_source_does_not_fabricate_phase_c_results() -> None:
    source = inspect.getsource(finalizer._build_rc0010_rc0025_lineage)

    assert "rc0024_private_verification_receipt:" in source
    assert "FROZEN_RC0025_FORMAL" not in source
