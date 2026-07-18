# -*- coding: utf-8 -*-
from __future__ import annotations

"""RED coverage for rc0023 independent action-lifecycle matching."""

from dataclasses import replace
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import emlis_ai_step11_natural_surface_matcher_v3 as matcher
import emlis_ai_step11_natural_surface_v3 as surface
from emlis_ai_step11_runtime_adapter_v3 import execute_step11_offline_v3


_CYCLE001_REGRESSION_CASE_IDS = (
    "nls3s_b001_0002",
    "nls3s_b001_0044",
    "nls3s_b001_0045",
    "nls3s_b001_0048",
    "nls3s_b001_0059",
)
_APP_REACHABLE_FIELDS = frozenset(
    {"thought_text", "action_text", "emotions", "categories"}
)


def _cycle001_inputs() -> dict[str, dict[str, object]]:
    fixture = (
        Path(__file__).parent
        / "fixtures"
        / "emlis_nls_v3"
        / "generated"
        / "batch_001.jsonl"
    )
    wanted = set(_CYCLE001_REGRESSION_CASE_IDS)
    result: dict[str, dict[str, object]] = {}
    for line in fixture.read_text(encoding="utf-8").splitlines():
        sample = json.loads(line)
        case_id = sample.get("case_id")
        if case_id in wanted:
            projected = dict(sample["input"])
            assert set(projected) == _APP_REACHABLE_FIELDS
            result[str(case_id)] = projected
    assert set(result) == wanted
    return result


@pytest.fixture(scope="module")
def cycle001_lifecycle_executions():
    return {
        case_id: execute_step11_offline_v3(
            current_input,
            candidate_version_id=surface.STEP11_CANDIDATE_VERSION_ID,
            source_dependency_closure_sha256="7" * 64,
        )
        for case_id, current_input in _cycle001_inputs().items()
    }


@pytest.mark.parametrize("case_id", _CYCLE001_REGRESSION_CASE_IDS)
def test_rc0023_plain_dictionary_intentions_select_from_four_fields_only(
    cycle001_lifecycle_executions,
    case_id: str,
) -> None:
    execution = cycle001_lifecycle_executions[case_id]

    assert set(execution.projected_current_input) == _APP_REACHABLE_FIELDS
    assert execution.status == "selected"
    assert execution.selected_candidate is not None
    assert execution.selection_result.gate_results
    assert all(
        result.hard_pass is True and result.failure_codes == ()
        for result in execution.selection_result.gate_results
    )


@pytest.fixture(scope="module")
def plain_future_execution():
    execution = execute_step11_offline_v3(
        {
            "thought_text": "",
            "action_text": "明日は机の上を片づける。",
            "emotions": [{"type": "平穏", "strength": "weak"}],
            "categories": ["生活"],
        },
        candidate_version_id=surface.STEP11_CANDIDATE_VERSION_ID,
        source_dependency_closure_sha256="6" * 64,
    )
    assert execution.status == "selected"
    assert execution.selected_candidate is not None
    return execution


def test_rc0023_plain_future_uses_exact_source_modality_fallback(
    plain_future_execution,
) -> None:
    candidate = plain_future_execution.selected_candidate
    assert candidate is not None
    witness = matcher.parse_step11_natural_surface(
        candidate.rendered_surface.utf8_bytes
    )
    reception = next(
        atom for atom in witness.atoms if atom.section_role == "reception"
    )

    assert reception.reception_scope == "action"
    assert reception.realization_status == "intended"
    binding = matcher.match_step11_natural_surface(
        witness,
        inventory_result=plain_future_execution.inventory_result,
        content_plan=plain_future_execution.content_plan,
        discourse_plan=candidate.discourse_plan,
        current_input=plain_future_execution.projected_current_input,
    )
    assert binding.verified is True


def test_rc0023_plain_future_reception_status_tamper_fails_closed(
    plain_future_execution,
) -> None:
    candidate = plain_future_execution.selected_candidate
    assert candidate is not None
    witness = matcher.parse_step11_natural_surface(
        candidate.rendered_surface.utf8_bytes
    )
    reception = next(
        atom for atom in witness.atoms if atom.section_role == "reception"
    )
    forged = replace(
        witness,
        atoms=tuple(
            replace(atom, realization_status="undetermined")
            if atom is reception
            else atom
            for atom in witness.atoms
        ),
    )

    binding = matcher.match_step11_natural_surface(
        forged,
        inventory_result=plain_future_execution.inventory_result,
        content_plan=plain_future_execution.content_plan,
        discourse_plan=candidate.discourse_plan,
        current_input=plain_future_execution.projected_current_input,
    )

    assert binding.verified is False
    assert (
        "S11_MATCH_RECEPTION_TARGET_SCOPE_STATUS_MISMATCH"
        in binding.issue_codes
    )


def _source_nucleus(modality: str, *, kind: str = "action"):
    return SimpleNamespace(kind=kind, modality=modality)


@pytest.mark.parametrize(
    ("action_text", "expected"),
    (
        ("まだ資料を提出していない。", "reported_not_completed"),
        ("資料をまとめている。", "reported_ongoing"),
        ("資料を確認するつもり。", "intended"),
        ("机の上を片づけた。", "reported_completed"),
        ("明日は机の上を片づける。", "intended"),
    ),
)
def test_rc0023_explicit_lifecycle_precedes_source_modality_fallback(
    action_text: str,
    expected: str,
) -> None:
    assert matcher._independent_action_lifecycle_for_nuclei(
        ("nucleus-action",),
        nucleus_by_id={
            "nucleus-action": _source_nucleus("intended"),
        },
        action_text=action_text,
    ) == expected


def test_rc0023_non_intended_or_conflicting_source_modality_fails_closed(
) -> None:
    plain_dictionary_action = "明日は机の上を片づける。"

    assert matcher._independent_action_lifecycle_for_nuclei(
        ("nucleus-observed",),
        nucleus_by_id={
            "nucleus-observed": _source_nucleus("observed"),
        },
        action_text=plain_dictionary_action,
    ) == "undetermined"
    assert matcher._independent_action_lifecycle_for_nuclei(
        ("nucleus-intended", "nucleus-observed"),
        nucleus_by_id={
            "nucleus-intended": _source_nucleus("intended"),
            "nucleus-observed": _source_nucleus("observed"),
        },
        action_text=plain_dictionary_action,
    ) == "undetermined"
    assert matcher._independent_action_lifecycle_for_nuclei(
        ("nucleus-thought",),
        nucleus_by_id={
            "nucleus-thought": _source_nucleus(
                "intended", kind="proposition"
            ),
        },
        action_text=plain_dictionary_action,
    ) == "not_applicable"
