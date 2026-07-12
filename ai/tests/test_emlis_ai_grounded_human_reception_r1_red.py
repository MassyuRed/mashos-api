# -*- coding: utf-8 -*-
from __future__ import annotations

"""R1 historical RED evidence and the repaired current structural contract.

The manifest keeps the pre-repair failure counts immutable.  Current runtime
assertions stay body-free and verify that R3/R4 removed those failure reasons
without changing the frozen observation section.
"""

import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

from helpers.emlis_ai_grounded_observation_i0_inventory import (
    GROUND_OBSERVATION_I0_KNOWN_REGRESSION_CASES,
)
from helpers.emlis_ai_grounded_observation_i6_cases import (
    GROUND_OBSERVATION_I6_BLIND_CASES,
)
from emlis_ai_current_input_bundle import normalize_emlis_current_input
from emlis_ai_evidence_ledger_service import (
    build_evidence_ledger,
    build_evidence_span_resolver,
)
from emlis_ai_grounded_observation_gate import evaluate_grounded_observation_gate
from emlis_ai_grounded_observation_plan import build_grounded_observation_plan
from emlis_ai_grounded_sentence_surface import (
    build_grounded_sentence_plan,
    realize_grounded_sentence_plan,
    split_two_stage_surface,
)


_FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures"
_APP_VALID_FIXTURE = _FIXTURE_ROOT / "grounded_human_reception_exact8_v2_20260712.json"
_HASH_MANIFEST = _FIXTURE_ROOT / "grounded_human_reception_section_hashes_20260712.json"
_QUOTE_RE = re.compile(r"「([^」]+)」")
_POLICY_EXPLANATION_RE = re.compile(r"(?:理由|原因).{0,16}(?:決めつけ|断定)")


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _artifacts(current_input):
    normalized = normalize_emlis_current_input(current_input)
    spans = tuple(build_evidence_ledger(normalized))
    resolver = build_evidence_span_resolver(spans, current_input=normalized)
    plan = build_grounded_observation_plan(normalized, evidence_spans=spans)
    sentence_plan = build_grounded_sentence_plan(plan, resolver)
    surface = realize_grounded_sentence_plan(sentence_plan, plan, resolver)
    report = evaluate_grounded_observation_gate(
        plan=plan,
        sentence_plan=sentence_plan,
        surface_result=surface,
        resolver=resolver,
    )
    observation, reception, issues = split_two_stage_surface(surface.text)
    assert issues == ()
    return plan, sentence_plan, observation.strip(), reception.strip(), report


def _replayed_long_anchor(observation: str, reception: str) -> bool:
    observation_quotes = set(_QUOTE_RE.findall(observation))
    reception_quotes = set(_QUOTE_RE.findall(reception))
    return any(len(anchor.strip()) > 16 for anchor in observation_quotes & reception_quotes)


def _closing_family(reception: str) -> str:
    text = reception.strip()
    if text.endswith("受け取りました。"):
        return "analytic_received"
    if text.endswith("届きました。"):
        return "analytic_arrived"
    return "other"


def _human_follow_line(sentence_plan):
    return next(line for line in sentence_plan.lines if line.binding.line_role == "human_follow")


def test_r1_exact8_historical_red_is_fixed_without_completed_text_expectations() -> None:
    fixture = _load(_APP_VALID_FIXTURE)
    manifest = _load(_HASH_MANIFEST)
    expected_by_id = {case["case_id"]: case for case in manifest["cases"]}
    current_anchor_replays = 0
    current_policy_explanations = 0
    current_closings: Counter[str] = Counter()

    for case in fixture["cases"]:
        plan, sentence_plan, observation, reception, report = _artifacts(case["exact_current_input"])
        expected = expected_by_id[case["case_id"]]
        follow = _human_follow_line(sentence_plan)
        follow_atoms = set(follow.binding.functional_atom_ids)

        # The historical RED counts remain in the immutable manifest; the
        # current runtime must now carry and realize the R3/R4 contract.
        assert any(atom.startswith("human_follow:") for atom in follow_atoms)
        assert any(atom.startswith("reception_act:") for atom in follow_atoms)
        assert any(atom.startswith("reception_stance:") for atom in follow_atoms)
        assert any(atom.startswith("reception_reference:") for atom in follow_atoms)
        assert any(
            atom.startswith("reception_terminal_predicate:human_response_")
            for atom in follow_atoms
        )
        assert _replayed_long_anchor(observation, reception) is False
        assert _POLICY_EXPLANATION_RE.search(reception) is None
        assert _closing_family(reception) != expected["closing_family"]
        assert hashlib.sha256(observation.encode("utf-8")).hexdigest() == (
            expected["observation_section_sha256"]
        )
        assert expected["failure_reason_refs"]
        assert report.public_observation_status == "passed"
        assert report.semantic_quality_gate == "passed"
        assert plan.response_plan.surface_shape == "two_stage"

        current_anchor_replays += int(_replayed_long_anchor(observation, reception))
        current_policy_explanations += int(bool(_POLICY_EXPLANATION_RE.search(reception)))
        current_closings[_closing_family(reception)] += 1

    baseline = manifest["batch_failure_baseline"]
    assert baseline["exact8_long_anchor_replay_count"] == 7
    assert baseline["exact8_policy_explanation_count"] == 1
    assert baseline["exact8_received_closing_family_count"] == 7
    assert current_anchor_replays == 0
    assert current_policy_explanations == 0
    assert current_closings["analytic_received"] == 0


def test_r1_same16_historical_closing_concentration_is_not_current_runtime() -> None:
    cases = (
        *GROUND_OBSERVATION_I0_KNOWN_REGRESSION_CASES,
        *GROUND_OBSERVATION_I6_BLIND_CASES,
    )
    manifest = _load(_HASH_MANIFEST)
    families = Counter(
        _closing_family(_artifacts(case.as_current_input())[3])
        for case in cases
    )
    baseline = manifest["batch_failure_baseline"]
    assert len(cases) == baseline["same16_case_count"] == 16
    assert baseline["same16_received_closing_family_count"] == 15
    assert families["analytic_received"] == 0


def test_r1_unseen_families_receive_the_current_reception_contract() -> None:
    unseen_inputs = (
        {
            "memo": "喉の奥が詰まる感じがする。",
            "memo_action": "",
            "emotions": ["不安"],
            "category": ["健康"],
        },
        {
            "memo": (
                "発表資料を作り直した。最初の案は説明が多すぎると感じた。"
                "ただ、残したい図は一つある。まだ順番は決めきれていない。"
                "次は図から組み直したい。"
            ),
            "memo_action": "修正した箇所を一覧に残した。",
            "emotions": ["自己理解"],
            "category": ["仕事"],
        },
        {
            "memo": "自分には何もできない。それでも、明日の予約は取り消していない。",
            "memo_action": "",
            "emotions": ["悲しみ"],
            "category": ["人生"],
        },
        {
            "memo": "前回より手順を一つ減らせそうだ。まだ速くなったとは言えない。",
            "memo_action": "作業時間を表に記録した。",
            "emotions": ["自己理解"],
            "category": ["仕事"],
        },
    )

    for current_input in unseen_inputs:
        plan, sentence_plan, _observation, _reception, report = _artifacts(current_input)
        follow_atoms = set(_human_follow_line(sentence_plan).binding.functional_atom_ids)
        assert plan.response_plan.human_follow_target_ids
        assert any(atom.startswith("reception_act:") for atom in follow_atoms)
        assert "reception_distinctness:required" in follow_atoms
        assert "reception_quote_policy:no_full_quote_replay" in follow_atoms
        assert report.public_observation_status == "passed"
        assert report.semantic_quality_gate == "passed"


def test_r1_self_denial_fact_boundary_and_relation_direction_remain_green() -> None:
    fixture = _load(_APP_VALID_FIXTURE)
    for case in fixture["cases"]:
        plan = _artifacts(case["exact_current_input"])[0]
        required_relations = {
            relation.relation_id: relation
            for relation in plan.relations
            if relation.relation_id in plan.coverage_requirements.required_relation_ids
        }
        assert all(
            relation.from_nucleus_id != relation.to_nucleus_id
            for relation in required_relations.values()
        )
        if case["case_id"] in {"D", "I6-D02"}:
            assert plan.response_plan.fact_boundary_nucleus_ids
            assert plan.coverage_requirements.fact_boundary_required is True
            assert plan.safety_policy.identity_claim_must_not_be_accepted_as_fact is True


def test_r1_file_contains_no_exact_completed_reception_assertion() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare) or not any(
            isinstance(operator, ast.Eq) for operator in node.ops
        ):
            continue
        values = (node.left, *node.comparators)
        has_completed_body_field = any(
            isinstance(value, ast.Attribute)
            and value.attr in {"text", "comment_text", "current_body"}
            for value in values
        )
        has_literal_sentence = any(
            isinstance(value, ast.Constant)
            and isinstance(value.value, str)
            and len(value.value) >= 20
            for value in values
        )
        assert not (has_completed_body_field and has_literal_sentence)
