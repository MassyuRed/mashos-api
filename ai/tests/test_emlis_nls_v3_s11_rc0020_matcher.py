# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path

import pytest

import emlis_ai_step11_natural_surface_matcher_v3 as matcher
import emlis_ai_step11_semantic_overlay_v3 as overlay
from emlis_ai_step11_natural_surface_v3 import STEP11_CANDIDATE_VERSION_ID
from emlis_ai_step11_planning_frontier_v3 import (
    build_step11_planning_frontier,
)
from emlis_ai_step11_runtime_adapter_v3 import execute_step11_offline_v3
from emlis_ai_step11_semantic_overlay_v3 import (
    build_step11_semantic_overlay,
)


_FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "emlis_nls_v3"
    / "generated"
    / "batch_001.jsonl"
)


def _fixture_input(case_id: str) -> dict[str, object]:
    for line in _FIXTURE.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("case_id") == case_id:
            return dict(row["input"])
    raise AssertionError(f"missing fixture: {case_id}")


def _execute(case_id: str):
    return execute_step11_offline_v3(
        _fixture_input(case_id),
        candidate_version_id=STEP11_CANDIDATE_VERSION_ID,
        source_dependency_closure_sha256="1" * 64,
    )


@pytest.fixture(scope="module")
def connector_execution():
    return _execute("nls3s_b001_0032")


@pytest.fixture(scope="module")
def two_unknown_execution():
    return _execute("nls3s_b001_0035")


@pytest.fixture(scope="module")
def relation_scoped_unknown_execution():
    return execute_step11_offline_v3(
        {
            "thought_text": (
                "どうして予定を決めた後になると、急に別の選択のほうが"
                "よかった気がするんだろう。"
            ),
            "action_text": "",
            "emotions": [{"type": "不安", "strength": "medium"}],
            "categories": ["生活"],
        },
        candidate_version_id=STEP11_CANDIDATE_VERSION_ID,
        source_dependency_closure_sha256="2" * 64,
    )


def _binding(execution, witness):
    candidate = execution.selected_candidate
    assert candidate is not None
    return matcher.match_step11_natural_surface(
        witness,
        inventory_result=execution.inventory_result,
        content_plan=execution.content_plan,
        discourse_plan=candidate.discourse_plan,
        current_input=execution.projected_current_input,
    )


def test_evidence_ledger_exact_range_accepts_relation_prefix_split(
    connector_execution,
) -> None:
    execution = connector_execution
    assert execution.status == "selected"
    candidate = execution.selected_candidate
    assert candidate is not None
    witness = matcher.parse_step11_natural_surface(
        candidate.final_utf8_bytes
    )
    assert _binding(execution, witness).verified is True

    projection = matcher._project_input(execution.projected_current_input)
    frontier = build_step11_planning_frontier(
        execution.inventory_result,
        execution.content_plan,
        candidate.discourse_plan,
    )
    ranges, issues = matcher._independent_nucleus_source_ranges(
        execution.projected_current_input,
        projection=projection,
        snapshot=execution.inventory_result.source_snapshot,
        active_nucleus_ids=frozenset(frontier.active_nucleus_ids),
    )

    assert issues == ()
    second = next(
        row
        for row in ranges.values()
        if row.evidence_span_id == "s3"
    )
    assert second.text == "黙って受け入れるのも違う"
    assert projection[second.source_slot][second.start : second.end] == (
        second.text
    )


def _anchor_contract(execution, overlay):
    candidate = execution.selected_candidate
    assert candidate is not None
    frontier = build_step11_planning_frontier(
        execution.inventory_result,
        execution.content_plan,
        candidate.discourse_plan,
    )
    return matcher._independent_anchor_binding_contract(
        current_input=execution.projected_current_input,
        projection=matcher._project_input(
            execution.projected_current_input
        ),
        snapshot=execution.inventory_result.source_snapshot,
        active_nucleus_ids=frozenset(frontier.active_nucleus_ids),
        semantic_overlay=overlay,
    )


def test_adjacent_evidence_span_cannot_replace_target_nucleus_range(
    connector_execution,
) -> None:
    execution = connector_execution
    candidate = execution.selected_candidate
    assert candidate is not None
    overlay = build_step11_semantic_overlay(
        execution.projected_current_input,
        inventory_result=execution.inventory_result,
        content_plan=execution.content_plan,
        discourse_plan=candidate.discourse_plan,
    )
    thought_bindings = tuple(
        row
        for row in overlay.nucleus_anchor_bindings
        if row.source_role == "thought" and row.source_anchor_ids
    )
    assert len(thought_bindings) >= 2
    left, right = thought_bindings[:2]
    forged_right = replace(
        right,
        source_anchor_ids=left.source_anchor_ids,
    )
    forged = replace(
        overlay,
        nucleus_anchor_bindings=tuple(
            forged_right if row.nucleus_id == right.nucleus_id else row
            for row in overlay.nucleus_anchor_bindings
        ),
    )

    _, issues = _anchor_contract(execution, forged)

    assert "S11_MATCH_NUCLEUS_BINDING_CONTRACT_MISMATCH" in issues


def test_narrowed_source_range_fails_even_with_self_consistent_anchor_id(
    connector_execution,
) -> None:
    execution = connector_execution
    candidate = execution.selected_candidate
    assert candidate is not None
    overlay = build_step11_semantic_overlay(
        execution.projected_current_input,
        inventory_result=execution.inventory_result,
        content_plan=execution.content_plan,
        discourse_plan=candidate.discourse_plan,
    )
    binding = next(
        row
        for row in overlay.nucleus_anchor_bindings
        if row.source_role == "thought" and row.source_anchor_ids
    )
    anchor = next(
        row
        for row in overlay.anchors
        if row.anchor_id == binding.source_anchor_ids[0]
    )
    projection = matcher._project_input(execution.projected_current_input)
    narrowed_start = anchor.start + 1
    narrowed_text = projection[anchor.source_slot][
        narrowed_start : anchor.end
    ]
    text_sha256 = hashlib.sha256(narrowed_text.encode("utf-8")).hexdigest()
    anchor_id = "s11anc_" + matcher.artifact_sha256(
        {
            "source_slot": anchor.source_slot,
            "role": anchor.role,
            "start": narrowed_start,
            "end": anchor.end,
            "text_sha256": text_sha256,
        }
    )[:16]
    narrowed_anchor = replace(
        anchor,
        anchor_id=anchor_id,
        start=narrowed_start,
        text=narrowed_text,
        text_sha256=text_sha256,
    )
    forged_binding = replace(binding, source_anchor_ids=(anchor_id,))
    forged = replace(
        overlay,
        anchors=tuple(
            narrowed_anchor if row.anchor_id == anchor.anchor_id else row
            for row in overlay.anchors
        ),
        nucleus_anchor_bindings=tuple(
            forged_binding if row.nucleus_id == binding.nucleus_id else row
            for row in overlay.nucleus_anchor_bindings
        ),
    )

    _, issues = _anchor_contract(execution, forged)

    assert "S11_MATCH_SOURCE_ANCHOR_CONTRACT_MISMATCH" not in issues
    assert "S11_MATCH_NUCLEUS_BINDING_CONTRACT_MISMATCH" in issues


def test_two_identical_unknown_forms_remain_distinct_by_typed_target(
    two_unknown_execution,
) -> None:
    execution = two_unknown_execution
    assert execution.status == "selected"
    candidate = execution.selected_candidate
    assert candidate is not None
    witness = matcher.parse_step11_natural_surface(
        candidate.final_utf8_bytes
    )
    unknown_atoms = tuple(
        row
        for row in witness.atoms
        if row.form_id.startswith("unknown_anaphora:decision_state:")
    )

    assert len(unknown_atoms) == 2
    assert tuple(
        row.unknown_target_references for row in unknown_atoms
    ) == (
        (matcher.Step11EndpointReference(1, "proposition"),),
        (matcher.Step11EndpointReference(2, "proposition"),),
    )
    binding = _binding(execution, witness)
    assert binding.verified is True
    assert "S11_MATCH_DUPLICATE_SEMANTIC_ATOM" not in binding.issue_codes


@pytest.mark.parametrize("tamper", ("missing", "wrong_ordinal", "wrong_role", "duplicate_target"))
def test_unknown_target_reference_tamper_fails_closed(
    two_unknown_execution,
    tamper: str,
) -> None:
    execution = two_unknown_execution
    candidate = execution.selected_candidate
    assert candidate is not None
    witness = matcher.parse_step11_natural_surface(
        candidate.final_utf8_bytes
    )
    indexes = [
        index
        for index, row in enumerate(witness.atoms)
        if row.form_id.startswith("unknown_anaphora:decision_state:")
    ]
    assert len(indexes) == 2
    first = witness.atoms[indexes[0]]
    second = witness.atoms[indexes[1]]
    if tamper == "missing":
        references = ()
    elif tamper == "wrong_ordinal":
        references = (matcher.Step11EndpointReference(99, "proposition"),)
    elif tamper == "wrong_role":
        references = (matcher.Step11EndpointReference(2, "action"),)
    else:
        references = first.unknown_target_references
    atoms = list(witness.atoms)
    atoms[indexes[1]] = replace(
        second,
        unknown_target_references=references,
    )
    forged = replace(witness, atoms=tuple(atoms))

    binding = _binding(execution, forged)

    assert binding.verified is False
    assert {
        "S11_MATCH_UNKNOWN_TARGET_UNRESOLVED",
        "S11_MATCH_UNKNOWN_TARGET_REFERENCE_MISMATCH",
        "S11_MATCH_DUPLICATE_SEMANTIC_ATOM",
    } & set(binding.issue_codes)


@pytest.mark.parametrize("tamper", ("missing_endpoint", "permuted"))
def test_relation_scoped_unknown_requires_exact_ordered_endpoint_pair(
    relation_scoped_unknown_execution,
    tamper: str,
) -> None:
    execution = relation_scoped_unknown_execution
    assert execution.status == "selected"
    candidate = execution.selected_candidate
    assert candidate is not None
    witness = matcher.parse_step11_natural_surface(
        candidate.final_utf8_bytes
    )
    unknown = next(
        row
        for row in witness.atoms
        if row.form_id.startswith("unknown_anaphora:cause:")
    )
    assert len(unknown.unknown_target_references) == 2
    references = (
        unknown.unknown_target_references[:1]
        if tamper == "missing_endpoint"
        else tuple(reversed(unknown.unknown_target_references))
    )
    forged_unknown = replace(
        unknown,
        unknown_target_references=references,
    )
    forged = replace(
        witness,
        atoms=tuple(
            forged_unknown if row is unknown else row
            for row in witness.atoms
        ),
    )

    binding = _binding(execution, forged)

    assert binding.verified is False
    assert "S11_MATCH_UNKNOWN_TARGET_UNRESOLVED" in binding.issue_codes


def test_explicit_choice_hesitation_is_independently_classified() -> None:
    source = "やりたいと言ったのに迷うなんて、覚悟が足りないのかな。"
    assert matcher._independent_source_unknown_type(
        "EXPLICIT_CHOICE_DECISION_UNKNOWN",
        source,
        contextual_text=source,
    ) == "decision_state"
    assert matcher._independent_source_unknown_type(
        "EXPLICIT_CHOICE_DECISION_UNKNOWN",
        "迷った末に一つに決めた。",
        contextual_text="迷った末に一つに決めた。",
    ) is None
    execution = _execute("nls3s_b001_0027")
    assert execution.status == "selected"
    assert all(
        result.hard_pass
        for result in execution.selection_result.gate_results
    )


def test_unknown_lifecycle_forward_inverse_conflict_fails_closed() -> None:
    source = "参加すると決めたのに、まだ迷っている。"

    assert matcher._independent_source_unknown_type(
        "EXPLICIT_CHOICE_DECISION_UNKNOWN",
        source,
        contextual_text=source,
    ) is None


def test_nonexplicit_nonterminal_hesitation_does_not_widen_inverse_oracle() -> None:
    source = "参加したい気持ちはあるのに迷うなんて、準備不足なのかな。"

    assert matcher._independent_source_unknown_type(
        "CHOICE_DECISION_UNKNOWN",
        source,
        contextual_text=source,
    ) is None
    assert matcher._independent_source_unknown_type(
        "EXPLICIT_CHOICE_DECISION_UNKNOWN",
        source,
        contextual_text=source,
    ) == "decision_state"


@pytest.mark.parametrize(
    ("dimension_code", "source"),
    (
        (
            "CHOICE_DECISION_UNKNOWN",
            "予定を決めた後、気持ちが揺れている。",
        ),
        (
            "BETTER_CHOICE_UNKNOWN",
            "前のほうがよかった気がする。",
        ),
    ),
)
def test_post_decision_comparative_requires_exact_source_grammar(
    dimension_code: str,
    source: str,
) -> None:
    assert matcher._independent_source_unknown_type(
        dimension_code,
        source,
        contextual_text=source,
    ) is None


@pytest.mark.parametrize(
    ("dimension_code", "source", "expected"),
    (
        ("CHOICE_DECISION_UNKNOWN", "どれ？", "omitted_referent"),
        ("CHOICE_DECISION_UNKNOWN", "この件。", "omitted_referent"),
        (
            "CHOICE_DECISION_UNKNOWN",
            "内容が分からない。",
            "omitted_referent",
        ),
        (
            "CHOICE_DECISION_UNKNOWN",
            "何についてか言葉にできない。",
            "omitted_referent",
        ),
        (
            "CHOICE_DECISION_UNKNOWN",
            "何についての話かもしれない。",
            None,
        ),
        (
            "CHOICE_DECISION_UNKNOWN",
            "選ぶつもりか分からない。",
            None,
        ),
        (
            "INTENTION_UNKNOWN",
            "選択の意図が分からない。",
            None,
        ),
        (
            "CHOICE_DECISION_UNKNOWN",
            "別の選択\nのほうがよかった。",
            None,
        ),
        (
            "CHOICE_DECISION_UNKNOWN",
            "別の選択のほうがよかった。",
            "post_decision_comparative_merit",
        ),
        (
            "CHOICE_DECISION_UNKNOWN",
            "一つを選へ\u3099ない。",
            None,
        ),
        (
            "EXPLICIT_CHOICE_DECISION_UNKNOWN",
            "一つを選んた\u3099のに、まだ迷っている。",
            "decision_state",
        ),
        (
            "CHOICE_DECISION_UNKNOWN",
            "別の選択\rのほうがよかった。",
            "post_decision_comparative_merit",
        ),
    ),
)
def test_choice_unknown_forward_inverse_contract_is_symmetric(
    dimension_code: str,
    source: str,
    expected: str | None,
) -> None:
    assert overlay._frozen_unknown_type(
        dimension_code,
        source,
        contextual_text=source,
    ) == expected
    assert matcher._independent_source_unknown_type(
        dimension_code,
        source,
        contextual_text=source,
    ) == expected


@pytest.mark.parametrize(
    ("dimension_code", "source", "context", "expected"),
    (
        ("CAUSE_UNKNOWN", "なんとなく不安だ。", "なんとなく不安だ。", "cause"),
        (
            "CAUSE_UNKNOWN",
            "理由が分からない。",
            "理由が分からない。",
            "cause",
        ),
        ("EXPLICIT_CAUSE_UNKNOWN", "記録済み。", "記録済み。", "cause"),
        (
            "OTHER_PERSON_UNKNOWN",
            "悪く思われそう。",
            "悪く思われそう。",
            "other_person",
        ),
        (
            "EXPLICIT_OTHER_PERSON_UNKNOWN",
            "記録済み。",
            "記録済み。",
            "other_person",
        ),
        (
            "FUTURE_UNKNOWN",
            "来週は分からない。",
            "来週は分からない。",
            "future_outcome",
        ),
        (
            "FUTURE_UNKNOWN",
            "先のことが分からない。",
            "先のことが分からない。",
            None,
        ),
        (
            "RELATION_UNKNOWN",
            "関係が分からない。",
            "関係が分からない。",
            "relation",
        ),
        (
            "RELATION_UNKNOWN",
            "何についての関係か分からない。",
            "何についての関係か分からない。",
            None,
        ),
        (
            "REFERENT_UNKNOWN",
            "何についての関係か分からない。",
            "何についての関係か分からない。",
            "omitted_referent",
        ),
        (
            "OTHER_PERSON_UNKNOWN",
            "相手の考えが分からない。",
            "相手の考えが分からない。",
            "other_person",
        ),
        (
            "OTHER_PERSON_UNKNOWN",
            "周りがどう思うか分からない。",
            "周りがどう思うか分からない。",
            "other_person",
        ),
        ("REFERENT_UNKNOWN", "どれ？", "どれ？", "omitted_referent"),
        ("REFERENT_UNKNOWN", "わからない。", "わからない。", None),
        (
            "CHOICE_DECISION_UNKNOWN",
            "わからない。",
            "わからない。",
            None,
        ),
        (
            "EXPLICIT_REFERENT_UNKNOWN",
            "記録済み。",
            "記録済み。",
            "unspecified",
        ),
        (
            "TEMPORAL_REFERENT_UNKNOWN",
            "その後、どうするか未定。",
            "その後、どうするか未定。",
            "omitted_referent",
        ),
        (
            "TEMPORAL_REFERENT_UNKNOWN",
            "面談をした。その後、どうするか未定。",
            "面談をした。その後、どうするか未定。",
            None,
        ),
        (
            "TEMPORAL_REFERENT_UNKNOWN",
            "その後、どうするか未定。",
            "面談をした。その後、どうするか未定。",
            None,
        ),
    ),
)
def test_unknown_dimension_matrix_forward_inverse_contract_is_symmetric(
    dimension_code: str,
    source: str,
    context: str,
    expected: str | None,
) -> None:
    assert overlay._frozen_unknown_type(
        dimension_code,
        source,
        contextual_text=context,
    ) == expected
    assert matcher._independent_source_unknown_type(
        dimension_code,
        source,
        contextual_text=context,
    ) == expected
