# -*- coding: utf-8 -*-
from __future__ import annotations

"""RED coverage for rc0024 Reception source-slot ownership."""

from dataclasses import replace
from types import SimpleNamespace

import pytest

import emlis_ai_step11_natural_surface_matcher_v3 as matcher
import emlis_ai_step11_natural_surface_v3 as surface
from emlis_ai_step11_runtime_adapter_v3 import execute_step11_offline_v3


_CROSS_SLOT_INPUT = {
    "thought_text": (
        "応募書類を最後まで書いた。ただ、通るかどうかはまだ分からず、"
        "内容への迷いも残っている。"
    ),
    "action_text": "送る前の版を保存した。",
    "emotions": [{"type": "不安", "strength": "medium"}],
    "categories": ["仕事"],
}


def _action_nucleus(*, source_fields: tuple[str, ...]):
    return SimpleNamespace(
        kind="action",
        modality="observed",
        source_fields=source_fields,
    )


@pytest.mark.parametrize(
    ("source_fields", "expected"),
    (
        pytest.param(("memo",), "not_applicable", id="thought-owner"),
        pytest.param(
            ("memo_action",), "reported_completed", id="action-owner"
        ),
    ),
)
def test_rc0024_matcher_lifecycle_requires_exact_memo_action_owner(
    source_fields: tuple[str, ...], expected: str
) -> None:
    """Action grammar in one app slot cannot classify another slot's nucleus."""

    assert matcher._independent_action_lifecycle_for_nuclei(
        ("nucleus-action",),
        nucleus_by_id={
            "nucleus-action": _action_nucleus(source_fields=source_fields),
        },
        action_text="送る前の版を保存した。",
    ) == expected


@pytest.fixture(scope="module")
def cross_slot_execution():
    return execute_step11_offline_v3(
        _CROSS_SLOT_INPUT,
        candidate_version_id=surface.STEP11_CANDIDATE_VERSION_ID,
        source_dependency_closure_sha256="8" * 64,
    )


def test_rc0024_thought_semantic_action_and_distinct_action_slot_select(
    cross_slot_execution,
) -> None:
    """A semantic action written in thought stays reported thought content."""

    execution = cross_slot_execution
    candidate = execution.selected_candidate

    assert execution.status == "selected"
    assert candidate is not None
    assert execution.selection_result.gate_results
    assert all(
        result.hard_pass is True and result.failure_codes == ()
        for result in execution.selection_result.gate_results
    )

    witness = matcher.parse_step11_natural_surface(
        candidate.rendered_surface.utf8_bytes
    )
    thought_receptions = tuple(
        atom
        for atom in witness.atoms
        if atom.section_role == "reception"
        and atom.reception_scope == "thought"
    )

    assert thought_receptions
    assert all(
        atom.realization_status == "reported_content"
        for atom in thought_receptions
    )


def test_rc0024_cross_slot_lifecycle_tamper_fails_closed(
    cross_slot_execution,
) -> None:
    """The inverse matcher rejects completion borrowed from action_text."""

    execution = cross_slot_execution
    candidate = execution.selected_candidate
    assert candidate is not None
    witness = matcher.parse_step11_natural_surface(
        candidate.rendered_surface.utf8_bytes
    )
    thought_reception = next(
        atom
        for atom in witness.atoms
        if atom.section_role == "reception"
        and atom.reception_scope == "thought"
        and atom.realization_status == "reported_content"
    )
    forged = replace(
        witness,
        atoms=tuple(
            replace(atom, realization_status="reported_completed")
            if atom is thought_reception
            else atom
            for atom in witness.atoms
        ),
    )

    binding = matcher.match_step11_natural_surface(
        forged,
        inventory_result=execution.inventory_result,
        content_plan=execution.content_plan,
        discourse_plan=candidate.discourse_plan,
        current_input=execution.projected_current_input,
    )

    assert binding.verified is False
    assert (
        "S11_MATCH_RECEPTION_TARGET_SCOPE_STATUS_MISMATCH"
        in binding.issue_codes
    )
