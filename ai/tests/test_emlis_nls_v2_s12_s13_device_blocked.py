# -*- coding: utf-8 -*-
from __future__ import annotations

"""Fail-closed device evidence guards for NLS v2 Steps 12/13.

The four visible samples are representative device inputs, not Holdout cases.
Their bodies stay in this regression test only.  The durable receipt is
body-free and stores hashes, metrics, decisions, and screenshot references.
"""

import hashlib
import json
from pathlib import Path
import re

from emlis_ai_current_input_bundle import normalize_emlis_current_input
from emlis_ai_evidence_ledger_service import (
    build_evidence_ledger,
    build_evidence_span_resolver,
)
from emlis_ai_grounded_observation_plan import build_grounded_observation_plan
from emlis_ai_grounded_sentence_surface import (
    GROUND_SURFACE_GENERATION_PATH,
    build_grounded_sentence_plan,
    realize_grounded_sentence_plan,
    split_two_stage_surface,
)


_TEST_ROOT = Path(__file__).resolve().parent
_AI_ROOT = _TEST_ROOT.parent
_REPO_ROOT = _AI_ROOT.parent
_FIXTURE_ROOT = _TEST_ROOT / "fixtures"
_RECEIPT_PATH = (
    _FIXTURE_ROOT / "emlis_nls_v2_s12_s13_device_blocked_20260713.json"
)
_A_RECEIPT_PATH = (
    _FIXTURE_ROOT / "emlis_nls_v2_s8_holdout_a_receipt_20260713.json"
)
_B_RECEIPT_PATH = (
    _FIXTURE_ROOT / "emlis_nls_v2_s9_holdout_b_receipt_20260713.json"
)
_S10_S11_RECEIPT_PATH = (
    _FIXTURE_ROOT / "emlis_nls_v2_s10_s11_runtime_blocked_20260713.json"
)
_RUNTIME_PATHS = (
    _AI_ROOT / "services" / "ai_inference" / "emlis_ai_grounded_sentence_surface.py",
    _AI_ROOT / "services" / "ai_inference" / "emlis_ai_grounded_observation_gate.py",
    _AI_ROOT / "services" / "ai_inference" / "emlis_ai_reply_service.py",
)
_V2_RUNTIME_TOKENS = (
    "emlis_ai_grounded_reception_content_plan_v2",
    "emlis_ai_grounded_reception_candidate_plan_v2",
    "emlis_ai_grounded_human_reception_v2",
    "emlis_ai_grounded_reception_candidate_selector_v2",
    "build_reception_content_plan_v2",
    "build_reception_candidate_plans_v2",
    "generate_reception_surface_candidates_v2",
    "evaluate_and_select_reception_candidate_v2",
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_FORBIDDEN_BODY_KEYS = frozenset(
    {
        "current_input",
        "memo",
        "memo_action",
        "text",
        "v1_text",
        "v2_text",
        "surface_text",
        "candidate_text",
        "selected_text",
        "raw_input",
        "raw_text",
        "source_text",
        "comment_text",
        "expected_text",
        "returned_surface",
    }
)

# These are operator-visible Step 12 samples only.  They are deliberately not
# imported by production and do not add any case-cued branch or fixed reply.
_REPRESENTATIVE_CASES = (
    {
        "case_number": 1,
        "memo": "まだ決めきれない。",
        "memo_action": "",
        "emotions": ["不安"],
        "category": ["価値観"],
    },
    {
        "case_number": 2,
        "memo": (
            "後回しにしていた机の引き出しを一段だけ片づけた。"
            "思ったより気持ちが軽くて、今日は少しうれしい。"
        ),
        "memo_action": "不要な紙を五枚だけ分けた。",
        "emotions": ["喜び", "平穏"],
        "category": ["生活"],
    },
    {
        "case_number": 3,
        "memo": (
            "今月から勉強会の進行役を外れることにした。"
            "最後まで続けられなかった悔しさはあるけれど、"
            "参加そのものをやめたいわけではない。"
            "準備に使っていた時間を自分の学習へ戻したい気持ちと、"
            "仲間に申し訳ない気持ちが両方ある。"
            "役割を降りることと、関係を切ることは分けて考えたい。"
        ),
        "memo_action": (
            "次回の担当者へ資料の場所を送り、"
            "自分が参加できる日を二つだけ残した。"
        ),
        "emotions": ["悲しみ", "不安", "自己理解"],
        "category": ["学習", "人間関係"],
    },
    {
        "case_number": 4,
        "memo": (
            "面接でうまく話せず、やっぱり自分には価値がないと思った。"
            "それでも、聞かれた一つには最後まで答えた。"
        ),
        "memo_action": (
            "帰宅して、答えられなかった質問と答えられた質問を"
            "分けて書いた。"
        ),
        "emotions": ["悲しみ", "自己理解"],
        "category": ["仕事", "人生"],
    },
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _sha256_text(value: str) -> str:
    return _sha256_bytes(value.encode("utf-8"))


def _sha256_json(value) -> str:
    return _sha256_text(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    )


def _assert_body_free(value) -> None:
    if isinstance(value, dict):
        assert not _FORBIDDEN_BODY_KEYS.intersection(value)
        for child in value.values():
            _assert_body_free(child)
    elif isinstance(value, list):
        for child in value:
            _assert_body_free(child)


def _render_v1(current_input: dict) -> tuple[str, str, str, str]:
    normalized = normalize_emlis_current_input(current_input)
    spans = tuple(build_evidence_ledger(normalized))
    resolver = build_evidence_span_resolver(spans, current_input=normalized)
    plan = build_grounded_observation_plan(normalized, evidence_spans=spans)
    sentence_plan = build_grounded_sentence_plan(plan, resolver)
    surface = realize_grounded_sentence_plan(sentence_plan, plan, resolver)
    observation, reception, issues = split_two_stage_surface(surface.text)
    assert issues == ()
    return surface.generation_path, observation, reception, surface.text


def test_live_prerequisites_keep_formal_step12_and_step13_blocked() -> None:
    receipt = _load(_RECEIPT_PATH)
    holdout_a = _load(_A_RECEIPT_PATH)
    holdout_b = _load(_B_RECEIPT_PATH)
    runtime_steps = _load(_S10_S11_RECEIPT_PATH)

    assert receipt["schema_version"] == (
        "cocolon.emlis.nls_v2.s12_s13.device_blocked.v1"
    )
    assert receipt["decision"] == "blocked_fail_closed"

    a_meta = receipt["prerequisite_evidence"]["holdout_a"]
    assert _sha256_file(_A_RECEIPT_PATH) == a_meta["receipt_sha256"]
    assert holdout_a["overall_status"] == a_meta["overall_status"] == "stop"
    assert holdout_a["evaluation_run_count"] == a_meta["evaluation_run_count"] == 1

    b_meta = receipt["prerequisite_evidence"]["holdout_b"]
    assert _sha256_file(_B_RECEIPT_PATH) == b_meta["receipt_sha256"]
    assert holdout_b["overall_status"] == b_meta["overall_status"] == "not_evaluated"
    assert holdout_b["evaluation_run_count"] == b_meta["evaluation_run_count"] == 0
    assert holdout_b["opened_for_evaluation"] is b_meta["opened_for_evaluation"] is False

    runtime_meta = receipt["prerequisite_evidence"]["runtime_steps"]
    assert _sha256_file(_S10_S11_RECEIPT_PATH) == runtime_meta["receipt_sha256"]
    assert runtime_steps["decision"] == "blocked_fail_closed"
    assert runtime_steps["step10_runtime_preconnection_shadow"]["status"] == (
        runtime_meta["step10_status"]
    ) == "not_executed"
    assert runtime_steps["step11_runtime_owner_switch"]["status"] == (
        runtime_meta["step11_status"]
    ) == "not_executed"
    assert receipt["prerequisite_evidence"]["formal_step12_progression_allowed"] is False

    representative = receipt["representative4_review"]
    assert representative["formal_v2_evaluation_status"] == "not_executed"
    assert representative["exact8"] == {"status": "not_executed", "run_count": 0}
    assert representative["holdout_derived_representatives"]["run_count"] == 0
    assert representative["holdout_derived_representatives"]["holdout_b_opened"] is False
    assert representative["progression_allowed"] is False

    step13 = receipt["step13_two_stage_quantity_ratio_adjustment"]
    assert step13["status"] == "not_executed"
    assert step13["natural_language_v2_qualified"] is False
    assert step13["prerequisite_met"] is False
    assert step13["production_adjustment_count"] == 0


def test_received_four_cases_exactly_reproduce_canonical_v1() -> None:
    receipt = _load(_RECEIPT_PATH)
    rows = {
        row["case_number"]: row
        for row in receipt["representative4_review"]["cases"]
    }
    assert set(rows) == {1, 2, 3, 4}

    for case in _REPRESENTATIVE_CASES:
        case_number = case["case_number"]
        current_input = {
            key: value
            for key, value in case.items()
            if key != "case_number"
        }
        row = rows[case_number]
        generation_path, observation, reception, full_surface = _render_v1(
            current_input
        )
        total_chars = len(observation) + len(reception)

        assert _sha256_json(current_input) == row["input_identity_sha256"]
        assert generation_path == row["generation_path"] == (
            "grounded_sentence_surface_canonical_v1"
        )
        assert _sha256_text(observation) == row["observation_section_sha256"]
        assert _sha256_text(reception) == row["reception_section_sha256"]
        assert _sha256_text(full_surface) == row["visible_surface_sha256"]
        assert len(observation) == row["observation_char_count"]
        assert len(reception) == row["reception_char_count"]
        assert round(len(observation) / total_chars, 6) == row["observation_share"]
        assert round(len(reception) / total_chars, 6) == row["reception_share"]
        assert row["actual_device_visual_match_to_local_v1"] == "pass"

    evidence = receipt["device_evidence"]
    assert evidence["local_v1_reproduction_count"] == 4
    assert evidence["local_v1_visible_match_count"] == 4
    assert evidence["v2_runtime_generation_count"] == 0
    assert evidence["screenshot_review_is_raw_body_hash_proof"] is False
    assert evidence["actual_device_raw_comment_sha256_machine_match"] == (
        "not_available_from_screenshots"
    )


def test_device_evidence_and_product_failure_receipt_are_exact_and_body_free() -> None:
    receipt = _load(_RECEIPT_PATH)
    evidence = receipt["device_evidence"]
    rows = receipt["representative4_review"]["cases"]
    refs: list[tuple[str, str]] = []

    for row in rows:
        log_ref = row["backend_log_ref"]
        refs.append((log_ref["path"], log_ref["sha256"]))
        refs.extend(
            (screenshot["path"], screenshot["sha256"])
            for screenshot in row["screenshot_refs"]
        )
        assert row["ratio_guidance"]["gate_type"] == "qa_advisory"
        assert row["ratio_guidance"]["within_guidance"] is False
        assert row["product_status"] == "fail"
        assert row["layout"]["clipping_observed"] is False
        assert row["layout"]["overlap_observed"] is False
        assert row["failure_codes"]

    assert len(refs) == len(set(refs)) == evidence["evidence_file_count"] == 10
    assert sum(len(row["screenshot_refs"]) for row in rows) == (
        evidence["display_screenshot_count"]
    ) == 6
    assert len(rows) == evidence["backend_log_screenshot_count"] == 4
    assert all(_SHA256_RE.fullmatch(sha256) for _path, sha256 in refs)
    assert sum(row["layout"]["scroll_required"] for row in rows) == 2
    assert receipt["representative4_review"]["ratio_guidance_is_hard_gate"] is False
    assert receipt["representative4_review"]["product_read_status"] == "fail"
    assert receipt["representative4_review"]["product_pass_count"] == 0
    assert receipt["representative4_review"]["product_failure_count"] == 4
    assert receipt["screenshot_files_included"] is False
    assert receipt["raw_input_included"] is False
    assert receipt["returned_surface_included"] is False
    _assert_body_free(receipt)


def test_step13_performs_no_case_tuning_or_ui_contract_change() -> None:
    receipt = _load(_RECEIPT_PATH)
    step13 = receipt["step13_two_stage_quantity_ratio_adjustment"]
    assert step13 == {
        "status": "not_executed",
        "v1_device_baseline_ratio_review_status": "complete",
        "natural_language_v2_qualified": False,
        "prerequisite_met": False,
        "production_adjustment_count": 0,
        "v1_source_modified": False,
        "v2_source_modified": False,
        "reception_density_adjustment_performed": False,
        "sentence_count_adjustment_performed": False,
        "observation_replay_compression_performed": False,
        "observation_coverage_revalidation_performed": False,
        "rn_visual_emphasis_changed": False,
        "ui_order_changed": False,
        "completion_status": (
            "blocked_by_unqualified_v2_and_non_v2_device_evidence"
        ),
    }
    assert receipt["production_files_modified"] == []
    assert receipt["holdout_files_modified"] == []
    assert "STEP13_PREREQUISITE_UNMET" in receipt["block_reason_codes"]
    assert "STEP13_NOT_EXECUTED" in receipt["block_reason_codes"]


def test_runtime_owner_sources_and_public_contract_remain_frozen() -> None:
    receipt = _load(_RECEIPT_PATH)
    runtime = receipt["runtime_boundary"]
    live_rows = [
        {"path": row["path"], "sha256": _sha256_file(_REPO_ROOT / row["path"])}
        for row in runtime["runtime_source_files"]
    ]
    assert live_rows == runtime["runtime_source_files"]
    assert GROUND_SURFACE_GENERATION_PATH == "grounded_sentence_surface_canonical_v1"
    assert runtime["production_owner"] == "v1"
    assert runtime["v2_state"] == "offline_only"
    assert runtime["runtime_source_modified_count"] == 0

    for path in _RUNTIME_PATHS:
        source = path.read_text(encoding="utf-8")
        assert all(token not in source for token in _V2_RUNTIME_TOKENS)

    assert runtime["api_contract_changed"] is False
    assert runtime["db_contract_changed"] is False
    assert runtime["rn_contract_changed"] is False
    assert runtime["public_contract_diff_count"] == 0


def test_truncated_source_archive_is_never_claimed_as_complete() -> None:
    receipt = _load(_RECEIPT_PATH)
    source = receipt["source_archive"]
    assert source["archive_complete"] is False
    assert source["central_directory_present"] is False
    assert source["integrity_status"] == (
        "truncated_missing_end_of_central_directory"
    )
    assert source["safely_decoded_non_pycache_diff_count_against_basis"] == 0
    assert source["complete_working_tree_basis_integrity_status"] == (
        "verified_complete"
    )
    assert source["current_archive_used_as_complete_source"] is False
    assert "SOURCE_ARCHIVE_TRUNCATED" in receipt["block_reason_codes"]
