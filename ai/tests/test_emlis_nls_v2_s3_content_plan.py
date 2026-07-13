# -*- coding: utf-8 -*-
from __future__ import annotations

"""Development-only Step 3 Content Planner v2 contract tests."""

import ast
from collections import Counter
from dataclasses import asdict
from functools import lru_cache
import inspect
import json
from pathlib import Path

from helpers.emlis_nls_v2_s2_development import (
    DEPTH_ORDER,
    EVALUATION_FAMILIES,
    load_development_cases,
    sha256_file,
    sha256_json,
)
from emlis_ai_grounded_observation_plan import build_grounded_observation_plan
from emlis_ai_grounded_reception_content_plan_v2 import (
    RECEPTION_CONTENT_PLAN_V2_SCHEMA_VERSION,
    RECEPTION_CONTENT_PLAN_V2_SOURCE_VERSION,
    build_reception_content_plan_v2,
    validate_reception_content_plan_v2,
)


_TEST_ROOT = Path(__file__).resolve().parent
_AI_ROOT = _TEST_ROOT.parent
_REPO_ROOT = _AI_ROOT.parent
_PLANNER_PATH = (
    _AI_ROOT
    / "services"
    / "ai_inference"
    / "emlis_ai_grounded_reception_content_plan_v2.py"
)
_REPLY_SERVICE_PATH = (
    _AI_ROOT / "services" / "ai_inference" / "emlis_ai_reply_service.py"
)
_S1_RECEIPT_PATH = (
    _TEST_ROOT / "fixtures" / "emlis_nls_v2_s1_receipt_20260713.json"
)
_FORBIDDEN_BODY_KEYS = frozenset(
    {
        "case_id",
        "fixture_id",
        "input_family",
        "memo",
        "memo_action",
        "raw_input",
        "raw_text",
        "source_text",
        "surface_text",
        "candidate_text",
        "expected_text",
        "visible_surface",
        "wording_cue",
    }
)


@lru_cache(maxsize=1)
def _development_plans():
    rows = []
    for case in load_development_cases():
        observation_plan = build_grounded_observation_plan(case.current_input)
        content_plan = build_reception_content_plan_v2(observation_plan)
        rows.append((case, observation_plan, content_plan))
    return tuple(rows)


def _walk_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from _walk_keys(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from _walk_keys(child)


def test_step3_generates_valid_content_plans_for_all_development_42() -> None:
    rows = _development_plans()
    assert len(rows) == 42
    assert Counter(case.family for case, _, _ in rows) == {
        family: 3 for family in EVALUATION_FAMILIES
    }

    depth_counts = Counter()
    unit_counts = Counter()
    role_counts = Counter()
    semantic_signatures = set()
    receipt_rows = []
    for case, observation_plan, content_plan in rows:
        assert content_plan.schema_version == RECEPTION_CONTENT_PLAN_V2_SCHEMA_VERSION
        assert content_plan.source_observation_plan_version == (
            RECEPTION_CONTENT_PLAN_V2_SOURCE_VERSION
        )
        assert validate_reception_content_plan_v2(
            content_plan,
            observation_plan,
        ) == ()
        assert DEPTH_ORDER[case.min_depth] <= DEPTH_ORDER[content_plan.depth]
        assert DEPTH_ORDER[content_plan.depth] <= DEPTH_ORDER[case.max_depth]

        depth_counts[content_plan.depth] += 1
        unit_counts[len(content_plan.content_units)] += 1
        role_counts.update(item.role for item in content_plan.content_units)
        semantic_signatures.update(
            item.semantic_signature for item in content_plan.content_units
        )
        receipt_rows.append(
            {
                "case_id": case.case_id,
                "plan_id": content_plan.plan_id,
                "depth": content_plan.depth,
                "unit_count": len(content_plan.content_units),
                "unit_contract_sha256": sha256_json(
                    [asdict(item) for item in content_plan.content_units]
                ),
            }
        )

    assert depth_counts == {"minimal": 12, "focused": 21, "layered": 9}
    assert unit_counts == {1: 12, 2: 21, 3: 8, 4: 1}
    assert set(role_counts) == {
        "attention",
        "significance",
        "connection",
        "bounded_counterposition",
    }
    assert len(semantic_signatures) == 12
    assert sha256_json(receipt_rows) == (
        "9117bdf42e11c1845a4a05050ff60a990179066c92f9f198334ce70d5a28bdf6"
    )


def test_step3_is_deterministic_and_uses_only_observation_plan_input() -> None:
    signature = inspect.signature(build_reception_content_plan_v2)
    assert tuple(signature.parameters) == ("observation_plan",)

    for _, observation_plan, content_plan in _development_plans():
        rerun = build_reception_content_plan_v2(observation_plan)
        assert rerun == content_plan
        assert rerun.plan_id == content_plan.plan_id
        assert rerun.content_units == content_plan.content_units


def test_step3_content_units_are_body_free_and_all_evidence_resolves() -> None:
    for case, observation_plan, content_plan in _development_plans():
        serialized = asdict(content_plan)
        assert not (_FORBIDDEN_BODY_KEYS & set(_walk_keys(serialized)))
        serialized_text = json.dumps(
            serialized,
            ensure_ascii=False,
            sort_keys=True,
        )
        assert case.case_id not in serialized_text
        for raw_value in (
            case.current_input["memo"],
            case.current_input["memo_action"],
        ):
            if raw_value:
                assert raw_value not in serialized_text

        available_evidence = set(observation_plan.referenced_evidence_span_ids)
        assert content_plan.required_unit_ids == tuple(
            item.unit_id for item in content_plan.content_units if item.required
        )
        assert content_plan.required_unit_ids
        for item in content_plan.content_units:
            assert item.target_nucleus_ids
            assert item.evidence_span_ids
            assert set(item.evidence_span_ids) <= available_evidence
            assert item.allowed_stance_codes
            assert item.forbidden_claim_codes
            assert 0.0 <= item.priority <= 1.0

        meta = content_plan.as_body_free_meta()
        assert meta["body_free"] is True
        assert meta["case_id_included"] is False
        assert meta["fixture_family_included"] is False
        assert meta["raw_input_included"] is False
        assert meta["raw_text_included"] is False
        assert meta["source_text_included"] is False
        assert meta["surface_text_included"] is False
        assert meta["candidate_text_included"] is False
        assert meta["expected_text_included"] is False
        assert meta["runtime_connected"] is False
        assert meta["public_contract_changed"] is False


def test_step3_depth_unit_budget_and_required_optional_contract_are_bounded() -> None:
    ranges = {
        "minimal": (1, 1, (1, 1, 2)),
        "focused": (2, 2, (2, 2, 3)),
        "layered": (3, 4, (3, 3, 4)),
    }
    for _, _, content_plan in _development_plans():
        min_units, max_units, sentence_budget = ranges[content_plan.depth]
        assert min_units <= len(content_plan.content_units) <= max_units
        assert (
            content_plan.sentence_budget.min,
            content_plan.sentence_budget.target,
            content_plan.sentence_budget.max,
        ) == sentence_budget
        assert all(isinstance(item.required, bool) for item in content_plan.content_units)


def test_step3_self_denial_counterposition_preserves_existing_safety_policy() -> None:
    for case, observation_plan, content_plan in _development_plans():
        if case.family != "self_denial":
            continue
        assert observation_plan.safety_policy.safety_kind == (
            "self_denial_safe_state_answer"
        )
        reception = observation_plan.response_plan.human_reception_plan
        assert reception is not None
        counter_available = any(
            item.family == "counterdirection" for item in reception.opportunities
        )
        counter_planned = any(
            item.role == "bounded_counterposition"
            for item in content_plan.content_units
        )
        assert counter_planned is bool(
            counter_available
            or observation_plan.safety_policy.identity_claim_must_not_be_accepted_as_fact
        )


def test_step3_module_has_no_surface_runtime_external_ai_or_random_owner() -> None:
    tree = ast.parse(_PLANNER_PATH.read_text(encoding="utf-8"))
    imported_modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)

    assert "emlis_ai_grounded_observation_plan" in imported_modules
    assert "emlis_ai_grounded_sentence_surface" not in imported_modules
    assert "emlis_ai_grounded_human_reception" not in imported_modules
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
    assert "emlis_ai_grounded_reception_content_plan_v2" not in reply_source
    assert "build_reception_content_plan_v2" not in reply_source


def test_step3_preserves_step1_public_backend_owner_snapshot() -> None:
    receipt = json.loads(_S1_RECEIPT_PATH.read_text(encoding="utf-8"))
    contract = receipt["public_contract_snapshot"]
    owner_rows = contract["backend_owner_files"]
    live_rows = [
        {
            "path": row["path"],
            "sha256": sha256_file(_REPO_ROOT / row["path"]),
        }
        for row in owner_rows
    ]
    assert live_rows == owner_rows
    assert sha256_json(live_rows) == contract["backend_owner_snapshot_sha256"]
    assert contract["route"] == "/emotion/submit"
    assert contract["comment_path"] == "input_feedback.comment_text"
    assert contract["status_path"] == "input_feedback.emlis_ai.observation_status"
    assert contract["two_stage_order"] == "observation_then_reception"
