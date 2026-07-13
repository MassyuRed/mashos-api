# -*- coding: utf-8 -*-
from __future__ import annotations

"""Development-only Step 4 Discourse Candidate Planner contract tests."""

import ast
from collections import Counter
from dataclasses import asdict
from functools import lru_cache
import json
from pathlib import Path

from helpers.emlis_nls_v2_s2_development import (
    load_development_cases,
    sha256_json,
)
from emlis_ai_grounded_observation_plan import build_grounded_observation_plan
from emlis_ai_grounded_reception_candidate_plan_v2 import (
    RECEPTION_CANDIDATE_PLAN_V2_SCHEMA_VERSION,
    RECEPTION_CANDIDATE_SET_V2_SCHEMA_VERSION,
    build_reception_candidate_plans_v2,
    validate_reception_candidate_plan_set_v2,
)
from emlis_ai_grounded_reception_content_plan_v2 import (
    build_reception_content_plan_v2,
)


_TEST_ROOT = Path(__file__).resolve().parent
_AI_ROOT = _TEST_ROOT.parent
_PLANNER_PATH = (
    _AI_ROOT
    / "services"
    / "ai_inference"
    / "emlis_ai_grounded_reception_candidate_plan_v2.py"
)
_REPLY_SERVICE_PATH = (
    _AI_ROOT / "services" / "ai_inference" / "emlis_ai_reply_service.py"
)
_FORBIDDEN_BODY_KEYS = frozenset(
    {
        "case_id",
        "fixture_id",
        "input_family",
        "raw_input",
        "raw_text",
        "source_text",
        "text",
        "surface_text",
        "candidate_text",
        "expected_text",
        "visible_surface",
    }
)
_LIMITS = {
    "minimal": (3, 4),
    "focused": (5, 8),
    "layered": (8, 12),
}
_TARGET_COUNTS = {"minimal": 3, "focused": 5, "layered": 8}
_STRATEGIES = {
    "attention_then_felt",
    "attention_significance_felt",
    "contrast_then_felt",
    "uncertainty_then_action",
    "action_then_meaning",
    "burden_then_counterposition",
    "parallel_layered",
}


@lru_cache(maxsize=1)
def _development_candidate_plans():
    rows = []
    for case in load_development_cases():
        observation_plan = build_grounded_observation_plan(case.current_input)
        content_plan = build_reception_content_plan_v2(observation_plan)
        candidate_set = build_reception_candidate_plans_v2(content_plan)
        rows.append((case, content_plan, candidate_set))
    return tuple(rows)


def _walk_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from _walk_keys(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from _walk_keys(child)


def test_step4_generates_bounded_multiple_candidates_for_development_42() -> None:
    rows = _development_candidate_plans()
    assert len(rows) == 42
    depth_counts = Counter()
    candidate_counts = Counter()
    strategy_counts = Counter()
    total = 0
    for _, content_plan, candidate_set in rows:
        assert candidate_set.schema_version == RECEPTION_CANDIDATE_SET_V2_SCHEMA_VERSION
        assert validate_reception_candidate_plan_set_v2(
            candidate_set,
            content_plan,
        ) == ()
        expected_count = _TARGET_COUNTS[content_plan.depth]
        assert len(candidate_set.candidates) == expected_count
        assert len(candidate_set.candidates) > 1
        minimum, maximum = _LIMITS[content_plan.depth]
        assert minimum <= len(candidate_set.candidates) <= maximum
        assert (
            candidate_set.candidate_limit_min,
            candidate_set.candidate_limit_max,
        ) == (minimum, maximum)
        assert candidate_set.enumerated_variant_count == 12
        assert candidate_set.deduplicated_variant_count == expected_count
        depth_counts[content_plan.depth] += 1
        candidate_counts[(content_plan.depth, expected_count)] += 1
        strategy_counts.update(
            candidate.strategy_code for candidate in candidate_set.candidates
        )
        total += len(candidate_set.candidates)

    assert depth_counts == {"minimal": 12, "focused": 21, "layered": 9}
    assert candidate_counts == {
        ("minimal", 3): 12,
        ("focused", 5): 21,
        ("layered", 8): 9,
    }
    assert total == 213
    assert set(strategy_counts) == _STRATEGIES


def test_step4_candidate_order_grouping_and_variation_are_complete_and_unique() -> None:
    for _, content_plan, candidate_set in _development_candidate_plans():
        expected_ids = {unit.unit_id for unit in content_plan.content_units}
        signatures = set()
        ids = set()
        for ordinal, candidate in enumerate(candidate_set.candidates, start=1):
            assert candidate.schema_version == RECEPTION_CANDIDATE_PLAN_V2_SCHEMA_VERSION
            assert candidate.candidate_rank_seed == ordinal
            assert candidate.strategy_code in (
                content_plan.discourse_constraints.allowed_strategy_codes
            )
            assert set(candidate.ordered_unit_ids) == expected_ids
            assert tuple(
                unit_id
                for group in candidate.sentence_groups
                for unit_id in group
            ) == candidate.ordered_unit_ids
            assert all(1 <= len(group) <= 2 for group in candidate.sentence_groups)
            assert (
                content_plan.sentence_budget.min
                <= len(candidate.sentence_groups)
                <= content_plan.sentence_budget.max
            )
            assert candidate.required_coverage_unit_ids == (
                content_plan.required_unit_ids
            )
            assert candidate.body_free is True
            signature = (
                candidate.strategy_code,
                tuple(asdict(candidate.variation_signature).items()),
                candidate.sentence_groups,
            )
            assert signature not in signatures
            assert candidate.candidate_id not in ids
            signatures.add(signature)
            ids.add(candidate.candidate_id)


def test_step4_advances_grounded_safety_strategy_inside_focused_budget() -> None:
    matched = 0
    for _, content_plan, candidate_set in _development_candidate_plans():
        if "burden_then_counterposition" not in (
            content_plan.discourse_constraints.allowed_strategy_codes
        ):
            continue
        matched += 1
        assert any(
            candidate.strategy_code == "burden_then_counterposition"
            for candidate in candidate_set.candidates
        )
        assert any(
            candidate.variation_signature.connection
            == "separate_responsibilities"
            for candidate in candidate_set.candidates
        )
    assert matched == 3


def test_step4_is_deterministic_and_has_a_frozen_body_free_receipt() -> None:
    receipt_rows = []
    for case, content_plan, candidate_set in _development_candidate_plans():
        assert build_reception_candidate_plans_v2(content_plan) == candidate_set
        receipt_rows.append(
            {
                "case_id": case.case_id,
                "plan_id": content_plan.plan_id,
                "candidate_meta": candidate_set.as_body_free_meta(),
            }
        )
    assert sha256_json(receipt_rows) == (
        "7ded406beb275f8b85bfe454307dbffe1a75594d4245c8c7bcee3e6efc786850"
    )


def test_step4_candidate_contract_and_metadata_contain_no_body_or_case_cue() -> None:
    for case, _, candidate_set in _development_candidate_plans():
        serialized = asdict(candidate_set)
        assert not (_FORBIDDEN_BODY_KEYS & set(_walk_keys(serialized)))
        body_free_meta = candidate_set.as_body_free_meta()
        assert not (_FORBIDDEN_BODY_KEYS & set(_walk_keys(body_free_meta)))
        encoded = json.dumps(body_free_meta, ensure_ascii=False, sort_keys=True)
        assert case.case_id not in encoded
        for source_value in (
            case.current_input["memo"],
            case.current_input["memo_action"],
        ):
            if source_value:
                assert source_value not in encoded
        assert body_free_meta["body_free"] is True
        assert body_free_meta["random_selection_used"] is False
        assert body_free_meta["runtime_connected"] is False
        assert body_free_meta["public_contract_changed"] is False


def test_step4_planner_has_no_surface_random_external_ai_or_runtime_owner() -> None:
    tree = ast.parse(_PLANNER_PATH.read_text(encoding="utf-8"))
    imported_modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)

    assert "emlis_ai_grounded_reception_content_plan_v2" in imported_modules
    assert "emlis_ai_grounded_human_reception" not in imported_modules
    assert "emlis_ai_grounded_human_reception_v2" not in imported_modules
    assert "emlis_ai_reply_service" not in imported_modules
    assert "random" not in imported_modules
    assert not any(
        module.startswith(
            (
                "openai",
                "anthropic",
                "google.generativeai",
                "transformers",
                "llama_cpp",
            )
        )
        for module in imported_modules
    )
    reply_source = _REPLY_SERVICE_PATH.read_text(encoding="utf-8")
    assert "emlis_ai_grounded_reception_candidate_plan_v2" not in reply_source
    assert "build_reception_candidate_plans_v2" not in reply_source
