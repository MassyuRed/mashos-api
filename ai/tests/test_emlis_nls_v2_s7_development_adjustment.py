# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step 7 Development adjustment and freeze tests for offline NLS v2."""

from collections import Counter
import json
from pathlib import Path
import re

from helpers.emlis_nls_v2_s2_development import DEPTH_ORDER, sha256_file, sha256_json
from helpers.emlis_nls_v2_s6_s7_development import (
    body_free_development_receipt,
    development_distribution,
    load_development_selection_rows,
)
from emlis_ai_grounded_human_reception import realize_grounded_human_reception
from emlis_ai_grounded_reception_candidate_selector_v2 import (
    DISTRIBUTION_THRESHOLD_FREEZE,
    selector_config_as_body_free_meta,
)


_TEST_ROOT = Path(__file__).resolve().parent
_AI_ROOT = _TEST_ROOT.parent
_REPO_ROOT = _AI_ROOT.parent
_FREEZE_PATH = _TEST_ROOT / "fixtures" / "emlis_nls_v2_s7_freeze_20260713.json"
_HELPER_PATH = _TEST_ROOT / "helpers" / "emlis_nls_v2_s6_s7_development.py"
_REPLY_SERVICE_PATH = (
    _AI_ROOT / "services" / "ai_inference" / "emlis_ai_reply_service.py"
)
_BURDEN_RE = re.compile(r"(?:苦しさ|つらさ|しんどさ|負担)")
_UNCERTAINTY_RE = re.compile(r"(?:分から|わから|不明|まだ|決めつけず)")
_ABSOLUTE_FAILURE_RE = re.compile(
    r"(?:必ず成功|もう解決|回復しました|うつ病|鬱病|パニック障害|"
    r"適応障害|あなたは(?:強い|優しい|立派|素晴らしい)(?:人)?です|"
    r"してください|しましょう|すべき|した方がいい)"
)


def _load_freeze() -> dict:
    return json.loads(_FREEZE_PATH.read_text(encoding="utf-8"))


def test_step7_development_42_meets_absolute_machine_conditions() -> None:
    rows = load_development_selection_rows()
    assert len(rows) == 42
    selected_texts = []
    family_counts = Counter()
    for row in rows:
        case = row.case
        surface = row.selected_surface
        family_counts[case.family] += 1
        selected_texts.append(surface.text)
        assert row.selection.status == "selected"
        assert not _ABSOLUTE_FAILURE_RE.search(surface.text)
        assert DEPTH_ORDER[case.min_depth] <= DEPTH_ORDER[row.content_plan.depth]
        assert DEPTH_ORDER[row.content_plan.depth] <= DEPTH_ORDER[case.max_depth]
        normalized_signatures = {
            unit.semantic_signature.removeprefix("emlis_reception_of_")
            for unit in row.content_plan.content_units
        }
        required_distinct = {
            "minimal": 1,
            "focused": 2,
            "layered": 3,
        }[row.content_plan.depth]
        assert len(normalized_signatures) >= required_distinct
        if case.polarity_contract["source"] == "positive":
            assert not _BURDEN_RE.search(surface.text)
        if case.family == "self_denial":
            assert "あなた自身が決まるとは思えません" in surface.text
        if case.polarity_contract["source"] == "uncertain":
            assert _UNCERTAINTY_RE.search(surface.text)

    assert set(family_counts.values()) == {3}
    assert len(selected_texts) == len(set(selected_texts))


def test_step7_distribution_stays_inside_frozen_development_thresholds() -> None:
    distribution = development_distribution()
    thresholds = DISTRIBUTION_THRESHOLD_FREEZE
    assert distribution["selected_count"] == 42
    assert distribution["exact_duplicate_count"] <= thresholds[
        "exact_duplicate_max"
    ]
    assert distribution["rich_single_sentence_count"] <= thresholds[
        "rich_single_sentence_max"
    ]
    assert distribution["short_meaningless_inflation_count"] <= thresholds[
        "short_meaningless_inflation_max"
    ]
    assert distribution["max_strategy_share"] <= thresholds["strategy_share_max"]
    assert distribution["max_terminal_family_share"] <= thresholds[
        "terminal_family_share_max"
    ]
    assert distribution["max_predicate_family_share"] <= thresholds[
        "predicate_family_share_max"
    ]
    assert distribution["max_skeleton_share"] <= thresholds[
        "skeleton_share_max"
    ]


def test_step7_selected_v2_is_distinct_from_reproducible_v1_without_runtime_switch() -> None:
    for row in load_development_selection_rows():
        reception = row.observation_plan.response_plan.human_reception_plan
        assert reception is not None
        v1 = realize_grounded_human_reception(
            reception,
            {
                nucleus.nucleus_id: nucleus
                for nucleus in row.observation_plan.nuclei
            },
            row.resolver,
        ).text
        assert row.selected_surface.text != v1
        assert row.selection.runtime_connected is False
        assert row.selection.v1_fallback_used is False

    reply_source = _REPLY_SERVICE_PATH.read_text(encoding="utf-8")
    assert "emlis_ai_grounded_reception_candidate_selector_v2" not in reply_source
    assert "evaluate_and_select_reception_candidate_v2" not in reply_source


def test_step7_freezes_body_free_receipt_selector_config_and_source_snapshot() -> None:
    freeze = _load_freeze()
    assert freeze["schema_version"] == "cocolon.emlis.nls_v2.s7_freeze.v1"
    assert sha256_json(body_free_development_receipt()) == (
        freeze["development_body_free_receipt_sha256"]
    )
    assert sha256_json(selector_config_as_body_free_meta()) == (
        freeze["selector_config_sha256"]
    )
    live_source_rows = [
        {
            "path": row["path"],
            "sha256": sha256_file(_REPO_ROOT / row["path"]),
        }
        for row in freeze["source_snapshot"]
    ]
    assert live_source_rows == freeze["source_snapshot"]
    assert sha256_json(live_source_rows) == freeze["source_snapshot_sha256"]
    assert freeze["structural_redesign_count"] == 1
    assert freeze["candidate_bodies_included"] is False
    assert freeze["selected_bodies_included"] is False
    encoded = json.dumps(freeze, ensure_ascii=False, sort_keys=True)
    for row in load_development_selection_rows():
        assert row.selected_surface.text not in encoded


def test_step7_development_author_read_reaches_roadmap_floor_without_holdout_claim() -> None:
    freeze = _load_freeze()
    review = freeze["development_author_read"]
    count = freeze["case_count"]
    assert review["review_mode"] == "development_author_read_not_holdout_blind"
    assert review["body_persisted"] is False
    assert review["read_feeling_pass_count"] / count >= 0.90
    assert review["naturalness_pass_count"] / count >= 0.90
    assert review["non_template_pass_count"] / count >= 0.90
    assert review["wants_more_input_or_accumulation_pass_count"] / count >= 0.90
    assert review["self_blame_non_amplification_pass_count"] == count
    assert review["overclaim_absence_pass_count"] == count
    assert review["family_clearly_worse_than_v1_count"] == 0
    assert (
        review["paired_v2_clearly_better_count"]
        + review["paired_same_count"]
        + review["paired_v1_clearly_better_count"]
        == count
    )


def test_step7_holdout_cohorts_remain_unopened_and_unreferenced_by_runner() -> None:
    freeze = _load_freeze()
    assert freeze["holdout_a_opened"] is False
    assert freeze["holdout_b_opened"] is False
    helper_source = _HELPER_PATH.read_text(encoding="utf-8").lower()
    assert "holdout" not in helper_source
    assert "development42" not in helper_source
