# -*- coding: utf-8 -*-
from __future__ import annotations

"""RED coverage for rc0023 typed-Reception batch evidence."""

import json
from pathlib import Path
import sys
from typing import Any

import pytest


_HERE = Path(__file__).resolve().parent
_AI_ROOT = _HERE.parent
_SERVICES = _AI_ROOT / "services" / "ai_inference"
_HELPERS = _HERE / "helpers"
_TOOLS = _AI_ROOT / "tools"
for entry in (_SERVICES, _HELPERS, _TOOLS):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

from emlis_ai_step10_app_reachable_contract_v3 import (  # noqa: E402
    project_app_reachable_input,
)
from emlis_ai_step11_natural_surface_v3 import (  # noqa: E402
    STEP11_CANDIDATE_VERSION_ID,
)
from emlis_ai_step11_runtime_adapter_v3 import (  # noqa: E402
    execute_step11_offline_v3,
)
from emlis_nls_v3_step11_batch_run import (  # noqa: E402
    _build_selected_case,
    _surface_distribution_fields,
    _surface_profile_from_private_witness,
)


_BATCH = (
    _HERE
    / "fixtures"
    / "emlis_nls_v3"
    / "generated"
    / "batch_001.jsonl"
)
_SOURCE_CLOSURE = "a" * 64
_COMMITMENT_KEY = b"r" * 32


def _reference(ordinal: int = 1, role: str = "proposition") -> dict[str, Any]:
    return {"reference_ordinal": ordinal, "endpoint_role": role}


def _observation(
    ordinal: int = 1,
    role: str = "proposition",
    *,
    fragment: str = "source-backed observation",
) -> dict[str, Any]:
    return {
        "section_role": "observation",
        "form_id": f"reference_introduction:{role}:0",
        "source_fragments": [fragment],
        "introduced_reference": _reference(ordinal, role),
        "reception_antecedent_references": [],
    }


def _typed_reception(
    references: list[dict[str, Any]] | None,
    *,
    fragments: list[str] | None = None,
    include_reference_field: bool = True,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "section_role": "reception",
        "form_id": (
            "reception:typed:hold_in_attention:thought:"
            "reported_content:0:0:0"
        ),
        "source_fragments": [] if fragments is None else fragments,
        "introduced_reference": None,
    }
    if include_reference_field:
        row["reception_antecedent_references"] = references
    return row


def _frozen_public_case_0001() -> dict[str, Any]:
    first_line = _BATCH.read_text(encoding="utf-8").splitlines()[0]
    sample = json.loads(first_line)
    assert sample["case_id"] == "nls3s_b001_0001"
    return sample


def test_rc0023_production_selected_case_builds_typed_reception_evidence(
) -> None:
    """Exercise the exact selected-case builder used by the batch loop."""

    sample = _frozen_public_case_0001()
    projected_input = project_app_reachable_input(sample["input"])
    execution = execute_step11_offline_v3(
        projected_input,
        candidate_version_id=STEP11_CANDIDATE_VERSION_ID,
        source_dependency_closure_sha256=_SOURCE_CLOSURE,
    )
    assert execution.status == "selected"

    public_row, private_row = _build_selected_case(
        sample,
        v1_body="frozen-v1-baseline",
        execution=execution,
        commitment_key=_COMMITMENT_KEY,
        run_id="nls3run_0023e1de00000001",
        source_dependency_closure_sha256=_SOURCE_CLOSURE,
        environment_sha256="b" * 64,
        runner_sha256="c" * 64,
    )

    profile = public_row["surface_profile"]
    assert public_row["status"] == "selected"
    assert profile["reception_content_kind"] == "anaphoric"
    assert profile["reception_literal_count"] == 0
    private_witness = private_row["commitment_material"][
        "parsed_witness_binding"
    ]["witness"]
    assert _surface_profile_from_private_witness(
        private_witness, _COMMITMENT_KEY
    ) == profile


def test_rc0023_typed_reception_is_nonliteral_anaphoric_evidence() -> None:
    fields = _surface_distribution_fields(
        [_observation(), _typed_reception([_reference()])]
    )

    assert fields["reception_content_kind"] == "anaphoric"
    assert fields["reception_literal_count"] == 0
    assert fields["observation_literal_count"] == 1
    assert fields["unique_literal_owner_count"] == 1


@pytest.mark.parametrize(
    ("atoms", "expected_code"),
    (
        pytest.param(
            [
                _observation(),
                _typed_reception(None, include_reference_field=False),
            ],
            "step11_typed_reception_reference_required",
            id="missing-reference",
        ),
        pytest.param(
            [
                _observation(),
                _typed_reception([_reference(), _reference()]),
            ],
            "step11_typed_reception_reference_duplicate",
            id="duplicate-reference",
        ),
        pytest.param(
            [_observation(), _typed_reception([_reference(2)])],
            "step11_typed_reception_reference_unowned",
            id="unowned-reference",
        ),
        pytest.param(
            [_typed_reception([_reference()]), _observation()],
            "step11_typed_reception_reference_forward",
            id="forward-reference",
        ),
        pytest.param(
            [_observation(), _typed_reception([_reference(role="action")])],
            "step11_typed_reception_reference_role_mismatch",
            id="role-mismatch",
        ),
        pytest.param(
            [
                _observation(fragment="owner one"),
                _observation(fragment="owner two"),
                _typed_reception([_reference()]),
            ],
            "step11_typed_reception_reference_owner_ambiguous",
            id="ambiguous-owner",
        ),
        pytest.param(
            [
                _observation(),
                _typed_reception(
                    [_reference()], fragments=["literal replay"]
                ),
            ],
            "step11_typed_reception_literal_forbidden",
            id="literal-replay",
        ),
    ),
)
def test_rc0023_typed_reception_reference_contract_fails_closed(
    atoms: list[dict[str, Any]], expected_code: str
) -> None:
    with pytest.raises(ValueError, match=f"^{expected_code}$"):
        _surface_distribution_fields(atoms)
