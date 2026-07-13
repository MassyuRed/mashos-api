# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step 6 Hard Gate / Selector contract tests for offline NLS v2."""

import ast
from dataclasses import replace
import json
from pathlib import Path

from helpers.emlis_nls_v2_s6_s7_development import load_development_selection_rows
from emlis_ai_grounded_reception_candidate_selector_v2 import (
    CANDIDATE_LIMIT_FREEZE,
    DISTRIBUTION_THRESHOLD_FREEZE,
    HARD_GATE_CODES,
    SOFT_SCORE_AXES,
    SOFT_SCORE_WEIGHTS,
    ReceptionCandidateSelectorV2Error,
    evaluate_and_select_reception_candidate_v2,
    resolve_selected_reception_surface_v2,
    selector_config_as_body_free_meta,
    validate_reception_candidate_selection_v2,
)


_AI_ROOT = Path(__file__).resolve().parents[1]
_SELECTOR_PATH = (
    _AI_ROOT
    / "services"
    / "ai_inference"
    / "emlis_ai_grounded_reception_candidate_selector_v2.py"
)
_FORBIDDEN_META_KEYS = frozenset(
    {
        "text",
        "surface_text",
        "candidate_text",
        "selected_text",
        "visible_surface",
        "expected_text",
        "raw_input",
        "raw_text",
        "source_text",
        "comment_text",
    }
)


def _walk_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from _walk_keys(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from _walk_keys(child)


def test_step6_hard_gate_is_explainable_and_soft_score_never_rescues_failure() -> None:
    rows = load_development_selection_rows()
    assert len(rows) == 42
    for row in rows:
        selection = row.selection
        assert selection.status == "selected"
        assert selection.hard_gate_pass_count > 0
        assert selection.hard_gate_pass_count + selection.hard_gate_fail_count == len(
            selection.evaluations
        )
        assert validate_reception_candidate_selection_v2(
            selection,
            row.candidate_plan_set,
            row.surface_candidate_set,
        ) == ()
        for evaluation in selection.evaluations:
            assert tuple(check.code for check in evaluation.hard_gate.checks) == (
                HARD_GATE_CODES
            )
            failed = tuple(
                check.code
                for check in evaluation.hard_gate.checks
                if check.status == "failed"
            )
            assert evaluation.hard_gate.failed_codes == failed
            if failed:
                assert evaluation.soft_scores is None
                assert evaluation.total_score is None
                assert not evaluation.selected
            else:
                assert tuple(evaluation.soft_scores.as_mapping()) == SOFT_SCORE_AXES
                assert 0.0 <= evaluation.total_score <= 1.0


def test_step6_selection_metadata_is_body_free_and_selected_body_stays_process_local() -> None:
    for row in load_development_selection_rows():
        meta = row.selection.as_body_free_meta()
        assert not (_FORBIDDEN_META_KEYS & set(_walk_keys(meta)))
        encoded = json.dumps(meta, ensure_ascii=False, sort_keys=True)
        assert row.case.case_id not in encoded
        assert row.selected_surface.text not in encoded
        for candidate in row.surface_candidate_set.candidates:
            assert candidate.text not in encoded
        for field in ("memo", "memo_action"):
            raw = row.case.current_input[field]
            if raw:
                assert raw not in encoded
        assert meta["candidate_bodies_included"] is False
        assert meta["selected_body_included"] is False
        assert meta["runtime_connected"] is False
        assert meta["public_contract_changed"] is False


def test_step6_all_failed_candidates_return_formal_local_failure_without_v1_masking() -> None:
    row = load_development_selection_rows()[0]
    invalid_surfaces = tuple(
        replace(
            surface,
            text=surface.text + "必ず成功しました。",
            sentence_count=surface.sentence_count + 1,
        )
        for surface in row.surface_candidate_set.candidates
    )
    invalid_set = replace(row.surface_candidate_set, candidates=invalid_surfaces)
    selection = evaluate_and_select_reception_candidate_v2(
        row.observation_plan,
        row.content_plan,
        row.candidate_plan_set,
        invalid_set,
        row.resolver,
    )
    assert selection.status == "v2_no_valid_candidate"
    assert selection.selected_candidate_id is None
    assert selection.local_failure_code == "v2_no_valid_candidate"
    assert selection.hard_gate_pass_count == 0
    assert selection.v1_fallback_used is False
    assert all(evaluation.soft_scores is None for evaluation in selection.evaluations)
    try:
        resolve_selected_reception_surface_v2(selection, invalid_set)
    except ReceptionCandidateSelectorV2Error as exc:
        assert str(exc) == "v2_no_valid_candidate"
    else:
        raise AssertionError("no-valid selection unexpectedly resolved a body")


def test_step6_config_freezes_weights_limits_thresholds_and_stable_tie_break() -> None:
    assert round(sum(weight for _, weight in SOFT_SCORE_WEIGHTS), 8) == 1.0
    assert tuple(axis for axis, _ in SOFT_SCORE_WEIGHTS) == SOFT_SCORE_AXES
    assert CANDIDATE_LIMIT_FREEZE == {
        "minimal": (3, 4, 3),
        "focused": (5, 8, 5),
        "layered": (8, 12, 8),
    }
    assert DISTRIBUTION_THRESHOLD_FREEZE["exact_duplicate_max"] == 0
    config = selector_config_as_body_free_meta()
    assert config["soft_score_weights"] == dict(SOFT_SCORE_WEIGHTS)
    assert config["distribution_thresholds"] == dict(
        DISTRIBUTION_THRESHOLD_FREEZE
    )
    assert config["random_selection_used"] is False
    assert config["case_specific_weight_used"] is False
    assert config["v1_fallback_counts_as_v2_success"] is False
    assert config["candidate_body_included"] is False
    for row in load_development_selection_rows():
        assert row.selection.stable_tie_break_applied is True


def test_step6_selector_has_no_case_route_external_ai_random_or_runtime_owner() -> None:
    source = _SELECTOR_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)
    assert "NLS2-" not in source
    assert "exact8" not in source.lower()
    assert "emlis_ai_reply_service" not in imported_modules
    assert "random" not in imported_modules
    assert not any(
        module.startswith(
            ("openai", "anthropic", "google.generativeai", "transformers", "llama_cpp")
        )
        for module in imported_modules
    )
