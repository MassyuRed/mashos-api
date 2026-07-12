# -*- coding: utf-8 -*-
from __future__ import annotations

"""RR8 ordered local QA for depth, Move use, fingerprints, and boundaries."""

import asyncio
from collections import Counter
from copy import deepcopy
import hashlib
import inspect
import json
from pathlib import Path
import re

import pytest

from helpers.emlis_ai_grounded_human_reception_rr8_qa import (
    RR8BatchThresholds,
    RR8ReceptionQaCase,
    assert_body_free_metadata,
    evaluate_rr8_reception_batch,
    sha256_json,
    sha256_text,
)
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
from emlis_ai_grounded_human_reception import (
    build_grounded_reception_clause_plans,
    reception_active_moves,
    reception_effective_sentence_budget,
)
from emlis_ai_grounded_observation_gate import (
    RECEPTION_GATE_REPORT_FIELDS,
    evaluate_grounded_observation_gate,
)
from emlis_ai_grounded_observation_plan import build_grounded_observation_plan
from emlis_ai_grounded_sentence_surface import (
    build_grounded_sentence_plan,
    realize_grounded_sentence_plan,
    split_two_stage_surface,
)
from emlis_ai_public_feedback_meta import build_public_emlis_input_feedback_meta
from emlis_ai_reply_service import render_emlis_ai_reply


_TEST_ROOT = Path(__file__).resolve().parent
_AI_ROOT = _TEST_ROOT.parent
_REPO_ROOT = _AI_ROOT.parent
_EXACT8 = (
    _TEST_ROOT / "fixtures" / "grounded_human_reception_exact8_v2_20260712.json"
)
_OBSERVATION_HASHES = (
    _TEST_ROOT / "fixtures" / "grounded_human_reception_section_hashes_20260712.json"
)
_UNSEEN12 = (
    _TEST_ROOT
    / "local_only"
    / "grounded_human_reception_rr8_unseen12_20260713.json"
)
_AUTOMATED_RECEIPT = (
    _TEST_ROOT
    / "fixtures"
    / "grounded_human_reception_rr8_local_qa_receipt_20260713.json"
)
_DESIGN_SOURCE_SHA256 = (
    "bef049a1751e636dc05bc065c90e297ab5bded23208bfd52523f8e36ae0c22f4"
)
_SOURCE_OWNER_PATHS = (
    "ai/services/ai_inference/emlis_ai_grounded_observation_plan.py",
    "ai/services/ai_inference/emlis_ai_grounded_human_reception.py",
    "ai/services/ai_inference/emlis_ai_grounded_sentence_surface.py",
    "ai/services/ai_inference/emlis_ai_grounded_observation_gate.py",
    "ai/services/ai_inference/emlis_ai_reply_service.py",
)
_EXACT_DEPTH = {
    "A": ("minimal", 1, 1),
    "B": ("layered", 2, 2),
    "C": ("layered", 2, 2),
    "D": ("focused", 2, 2),
    "I6-S03": ("minimal", 1, 1),
    "I6-L03": ("layered", 2, 2),
    "I6-C01": ("layered", 2, 2),
    "I6-D02": ("focused", 2, 2),
}
_SAME16_EXPECTED = {
    **_EXACT_DEPTH,
    **{
        **{f"I6-S0{index}": ("minimal", 1, 1) for index in range(1, 4)},
        **{f"I6-L0{index}": ("layered", 2, 2) for index in range(1, 4)},
        **{f"I6-C0{index}": ("layered", 2, 2) for index in range(1, 4)},
        **{f"I6-D0{index}": ("focused", 2, 2) for index in range(1, 4)},
    },
}
_EXACT_THRESHOLDS = RR8BatchThresholds(
    3,
    4,
    3,
    4,
    "design_exact8_plus_local_opening_calibration",
)
_SAME16_THRESHOLDS = RR8BatchThresholds(
    6,
    8,
    6,
    8,
    "exact8_ratio_scaled_to_16",
)
_UNSEEN12_THRESHOLDS = RR8BatchThresholds(
    5,
    6,
    5,
    6,
    "exact8_ratio_scaled_to_12_ceiling",
)
_POLICY_RE = re.compile(
    r"理由を(?:こちらで)?決めつけず|入力から言える範囲で|"
    r"診断はしません|ここでは事実として扱いません|原因は分かりませんが"
)


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_input_sha256(current_input) -> str:
    return sha256_json(current_input)


def _source_snapshot():
    manifest = [
        {
            "path": path,
            "sha256": _sha256_file(_REPO_ROOT / path),
        }
        for path in _SOURCE_OWNER_PATHS
    ]
    return manifest, sha256_json(manifest)


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
    return (
        plan,
        sentence_plan,
        surface,
        report,
        observation.strip(),
        reception.strip(),
    )


def _assert_all_gates(artifacts) -> None:
    report = artifacts[3]
    assert report.passed is True
    assert report.public_observation_status == "passed"
    assert report.product_readfeel_status == "not_evaluated"
    assert report.all_reception_gates_passed is True
    assert all(
        getattr(report, field_name) == "passed"
        for field_name in RECEPTION_GATE_REPORT_FIELDS
    )


def _qa_case(case_id: str, artifacts) -> RR8ReceptionQaCase:
    plan, sentence_plan, surface, report, _observation, reception = artifacts
    reception_plan = plan.response_plan.human_reception_plan
    assert reception_plan is not None
    active_moves = reception_active_moves(
        reception_plan,
        sentence_plan.recovery_stage,
    )
    clauses = build_grounded_reception_clause_plans(
        reception_plan,
        sentence_plan.recovery_stage,
    )
    return RR8ReceptionQaCase(
        case_id=case_id,
        reception_text=reception,
        full_surface_sha256=sha256_text(surface.text),
        depth_level=report.reception_depth_level,
        opportunity_count=report.reception_opportunity_count,
        planned_move_count=report.reception_planned_move_count,
        realized_move_count=report.reception_realized_move_count,
        sentence_count=report.reception_sentence_count,
        move_roles=tuple(report.reception_move_roles),
        surface_strategies=tuple(report.reception_surface_strategies),
        predicate_families=tuple(
            report.reception_terminal_predicate_families
        ),
        connector_patterns=tuple(clause.connector_policy for clause in clauses),
        speaker_presences=tuple(clause.speaker_presence for clause in clauses),
        required_move_ids=tuple(
            move.move_id for move in reception_plan.moves if move.required
        ),
        realized_move_ids=tuple(move.move_id for move in active_moves),
        move_distinctness_gate=report.reception_move_distinctness_gate,
        non_enumeration_gate=report.reception_non_enumeration_gate,
    )


def _synthetic_case(
    case_id: str,
    reception_text: str,
    *,
    depth: str = "minimal",
    sentences: int = 1,
    roles=("felt_response",),
    strategies=("quiet_referent_first",),
    families=("human_response_quiet_presence",),
    connectors=("none",),
    speakers=("implicit_emlis",),
    planned_moves: int | None = None,
    distinctness_gate: str = "passed",
    non_enumeration_gate: str = "passed",
) -> RR8ReceptionQaCase:
    realized = len(tuple(roles))
    planned = realized if planned_moves is None else planned_moves
    return RR8ReceptionQaCase(
        case_id=case_id,
        reception_text=reception_text,
        full_surface_sha256=sha256_text(f"surface:{case_id}"),
        depth_level=depth,
        opportunity_count=planned,
        planned_move_count=planned,
        realized_move_count=realized,
        sentence_count=sentences,
        move_roles=tuple(roles),
        surface_strategies=tuple(strategies),
        predicate_families=tuple(families),
        connector_patterns=tuple(connectors),
        speaker_presences=tuple(speakers),
        required_move_ids=tuple(f"rm{index}" for index in range(1, planned + 1)),
        realized_move_ids=tuple(f"rm{index}" for index in range(1, realized + 1)),
        move_distinctness_gate=distinctness_gate,
        non_enumeration_gate=non_enumeration_gate,
    )


def _exact8_results():
    fixture = _load(_EXACT8)
    return tuple(
        (row, _artifacts(row["exact_current_input"]))
        for row in fixture["cases"]
    )


def _same16_results():
    cases = (
        *GROUND_OBSERVATION_I0_KNOWN_REGRESSION_CASES,
        *GROUND_OBSERVATION_I6_BLIND_CASES,
    )
    return tuple(
        (case.case_id, _artifacts(case.as_current_input())) for case in cases
    )


def _unseen12_results():
    fixture = _load(_UNSEEN12)
    return fixture, tuple(
        (row, _artifacts(row["current_input"]))
        for row in fixture["cases"]
    )


def _cohort_results():
    exact = _exact8_results()
    same = _same16_results()
    _fixture, unseen = _unseen12_results()
    return {
        "exact8": evaluate_rr8_reception_batch(
            "exact8_app_valid",
            tuple(_qa_case(row["case_id"], artifacts) for row, artifacts in exact),
            thresholds=_EXACT_THRESHOLDS,
        ),
        "same16": evaluate_rr8_reception_batch(
            "same16_current",
            tuple(_qa_case(case_id, artifacts) for case_id, artifacts in same),
            thresholds=_SAME16_THRESHOLDS,
        ),
        "unseen12": evaluate_rr8_reception_batch(
            "unseen12_synthetic_local",
            tuple(_qa_case(row["case_id"], artifacts) for row, artifacts in unseen),
            thresholds=_UNSEEN12_THRESHOLDS,
        ),
    }


def _receipt_cohort_summary(result):
    meta = result.as_body_free_meta()
    return {
        "qa_meta_sha256": sha256_json(meta),
        "case_count": result.case_count,
        "verdict": result.verdict,
        "depth_distribution": dict(result.depth_distribution),
        "exact_sentence_duplicate_group_count": len(
            result.duplicate_sentence_groups
        ),
        "maximum_closing_stem_family_count": max(
            (row["case_count"] for row in result.closing_stem_families),
            default=0,
        ),
        "maximum_terminal_lexeme_family_count": max(
            dict(result.terminal_lexeme_family_counts).values(),
            default=0,
        ),
        "maximum_skeleton_family_count": max(
            (row["case_count"] for row in result.skeleton_families),
            default=0,
        ),
        "maximum_opening_strategy_family_count": max(
            dict(result.opening_strategy_counts).values(),
            default=0,
        ),
        "rich_input_case_count": result.rich_input_case_count,
        "rich_one_line_case_count": len(result.rich_one_line_cases),
        "one_line_rich_input_rate_basis_points": (
            result.one_line_rich_input_rate_basis_points
        ),
        "short_water_filling_case_count": len(
            result.short_water_filling_cases
        ),
        "meaningful_support_unutilized_case_count": len(
            result.meaningful_support_unutilized_cases
        ),
        "clipped_anchor_case_count": len(result.clipped_anchor_cases),
        "surface_set_sha256": sha256_json(
            dict(result.surface_sha256_by_case)
        ),
        "threshold_basis": result.thresholds.basis,
    }


def test_rr8_exact8_observation_freeze_depth_targets_and_batch_metrics() -> None:
    expected_observation_hashes = {
        row["case_id"]: row["observation_section_sha256"]
        for row in _load(_OBSERVATION_HASHES)["cases"]
    }
    results = _exact8_results()
    for row, artifacts in results:
        case_id = row["case_id"]
        _assert_all_gates(artifacts)
        report = artifacts[3]
        expected_depth, expected_moves, expected_sentences = _EXACT_DEPTH[case_id]
        assert sha256_text(artifacts[4]) == expected_observation_hashes[case_id]
        assert report.reception_depth_level == expected_depth
        assert report.reception_realized_move_count == expected_moves
        assert report.reception_sentence_count == expected_sentences
        assert _POLICY_RE.search(artifacts[5]) is None

    batch = _cohort_results()["exact8"]
    assert len(results) == 8
    assert batch.verdict == "passed"
    assert batch.reason_codes == ()
    assert batch.duplicate_sentence_groups == ()
    assert batch.rich_one_line_cases == ()
    assert batch.short_water_filling_cases == ()
    assert batch.clipped_anchor_cases == ()
    assert len(batch.meaningful_support_eligible_cases) == 6
    assert batch.meaningful_support_unutilized_cases == ()
    assert batch.as_body_free_meta()["surface_body_included"] is False


def test_rr8_same16_and_unseen12_pass_scaled_batch_thresholds() -> None:
    same = _same16_results()
    fixture, unseen = _unseen12_results()
    for case_id, artifacts in same:
        _assert_all_gates(artifacts)
        expected_depth, expected_moves, expected_sentences = (
            _SAME16_EXPECTED[case_id]
        )
        assert artifacts[3].reception_depth_level == expected_depth
        assert artifacts[3].reception_realized_move_count == expected_moves
        assert artifacts[3].reception_sentence_count == expected_sentences
    for _row, artifacts in unseen:
        _assert_all_gates(artifacts)

    cohorts = _cohort_results()
    assert len(same) == 16
    assert len(unseen) == 12
    assert fixture["case_order"] == [row["case_id"] for row, _ in unseen]
    assert fixture["local_only"] is True
    assert fixture["synthetic_inputs"] is True
    assert fixture["progression_authority"] == "none"
    assert all(result.verdict == "passed" for result in cohorts.values())
    assert all(
        result.duplicate_sentence_groups == () for result in cohorts.values()
    )
    assert all(result.rich_one_line_cases == () for result in cohorts.values())
    assert all(
        result.short_water_filling_cases == () for result in cohorts.values()
    )
    assert all(result.clipped_anchor_cases == () for result in cohorts.values())


def test_rr8_unseen12_covers_required_families_and_fixed_expectations() -> None:
    fixture, results = _unseen12_results()
    required_families = {
        "short_burden",
        "body_sensation",
        "long_repetitive_burden",
        "positive_change_with_action",
        "retained_intention_with_uncertainty",
        "action_without_success",
        "long_arc_with_two_human_opportunities",
        "long_arc_with_one_human_opportunity",
        "comparison_with_self_measurement",
        "self_denial_without_counterevidence",
        "self_denial_with_help_seeking",
        "labels_only_limited",
    }
    assert {row["input_family"] for row, _ in results} == required_families
    assert len(
        {_canonical_input_sha256(row["current_input"]) for row, _ in results}
    ) == 12

    for row, artifacts in results:
        plan, _sentence_plan, _surface, report, _observation, reception = artifacts
        reception_plan = plan.response_plan.human_reception_plan
        assert reception_plan is not None
        assert plan.input_profile.semantic_complexity == row[
            "expected_semantic_complexity"
        ]
        assert plan.safety_policy.safety_kind == row["expected_safety_kind"]
        assert report.reception_depth_level == row["expected_depth_level"]
        assert report.reception_opportunity_count == row[
            "expected_opportunity_count"
        ]
        assert report.reception_realized_move_count == row["expected_move_count"]
        assert report.reception_sentence_count == row["expected_sentence_count"]
        assert len(reception_plan.moves) == row["expected_move_count"]
        assert _POLICY_RE.search(reception) is None


def test_rr8_long_repetitive_burden_is_not_false_positive_change() -> None:
    row, artifacts = next(
        item
        for item in _unseen12_results()[1]
        if item[0]["case_id"] == "RR8-U03"
    )
    reception_plan = artifacts[0].response_plan.human_reception_plan
    assert reception_plan is not None
    assert {opportunity.family for opportunity in reception_plan.opportunities} == {
        "current_burden"
    }
    assert {move.reception_act for move in reception_plan.moves} == {
        "stay_with_current_burden"
    }
    assert "うれし" not in artifacts[5]
    assert row["input_family"] == "long_repetitive_burden"
    _assert_all_gates(artifacts)


@pytest.mark.parametrize(
    "memo",
    (
        "前はできたのに今日はできなかった。",
        "前より痛みが増えた。",
        "間違いが前より増えた。",
        "残業が前より増えた。",
        "借金が前より増えた。",
        "問題が前より増えた。",
        "不満が前より増えた。",
    ),
)
def test_rr8_negative_change_never_becomes_a_glad_reception(memo: str) -> None:
    artifacts = _artifacts(
        {
            "memo": memo,
            "memo_action": "",
            "emotions": ["悲しみ"],
            "category": ["生活"],
        }
    )
    reception_plan = artifacts[0].response_plan.human_reception_plan
    assert reception_plan is not None
    assert "うれし" not in artifacts[5]
    _assert_all_gates(artifacts)


def test_rr8_explicit_value_from_another_topic_never_supports_adverse_change() -> None:
    artifacts = _artifacts(
        {
            "memo": "痛みが前より増えた。部屋の模様替えは良い変化だった。",
            "memo_action": "",
            "emotions": ["不安"],
            "category": ["生活"],
        }
    )
    plan = artifacts[0]
    reception_plan = plan.response_plan.human_reception_plan
    assert reception_plan is not None
    lived_move = next(
        move
        for move in reception_plan.moves
        if move.reception_act == "recognize_lived_change"
    )
    target_nuclei = tuple(
        nucleus
        for nucleus in plan.nuclei
        if nucleus.nucleus_id in lived_move.target_nucleus_ids
    )
    assert lived_move.support_nucleus_ids == ()
    assert target_nuclei
    assert any(
        "semantic_role:explicit_evaluation"
        in nucleus.semantic_frame.attribute_codes
        for nucleus in target_nuclei
    )
    _assert_all_gates(artifacts)


def test_rr8_self_denial_without_counterevidence_stays_grounded_one_move() -> None:
    _row, artifacts = next(
        item
        for item in _unseen12_results()[1]
        if item[0]["case_id"] == "RR8-U10"
    )
    plan, sentence_plan, _surface, report, _observation, reception = artifacts
    reception_plan = plan.response_plan.human_reception_plan
    assert reception_plan is not None
    assert reception_plan.depth_policy.safety_mode == "self_denial_bounded"
    assert len(reception_plan.moves) == 1
    assert reception_plan.moves[0].move_role == "felt_response"
    assert "bounded_counter_self_denial" not in {
        move.reception_act for move in reception_plan.moves
    }
    assert "Emlis" not in reception
    assert report.reception_safety_boundary_gate == "passed"
    assert report.reception_depth_plan_gate == "passed"
    assert report.reception_sentence_count == 1
    assert sentence_plan.recovery_stage == "full"
    for stage in ("optional_removed", "integrated", "hedged"):
        assert len(reception_active_moves(reception_plan, stage)) == 1
        assert reception_effective_sentence_budget(reception_plan, stage) == (
            1,
            1,
        )
    _assert_all_gates(artifacts)


def test_rr8_counterdirection_surface_does_not_invent_continuation_intent() -> None:
    artifacts = _artifacts(
        {
            "memo": "自分には価値がないと思う。でも、友だちの言葉まで否定したくない。",
            "memo_action": "",
            "emotions": ["悲しみ"],
            "category": ["人生"],
        }
    )
    assert "今のまま続けたくない" not in artifacts[5]
    assert "その自己評価だけでは終わらない別の思い" in artifacts[5]
    _assert_all_gates(artifacts)


@pytest.mark.parametrize(
    ("cases", "expected_reason"),
    [
        (
            (
                _synthetic_case("one", "同じ　文です。"),
                _synthetic_case("two", "同じ 文です！"),
            ),
            "rr8_exact_reception_sentence_duplicate",
        ),
        (
            tuple(
                _synthetic_case(
                    f"closing{index}",
                    f"入口{index}から、違いを保ったまま受け止めています。",
                )
                for index in range(4)
            ),
            "rr8_closing_stem_concentration",
        ),
        (
            tuple(
                _synthetic_case(f"terminal{index}", f"別文{index}です。")
                for index in range(5)
            ),
            "rr8_terminal_lexeme_family_concentration",
        ),
        (
            tuple(
                _synthetic_case(
                    f"skeleton{index}",
                    f"骨格は同じでも本文{index}は別です。",
                )
                for index in range(4)
            ),
            "rr8_sentence_skeleton_concentration",
        ),
        (
            tuple(
                _synthetic_case(
                    f"opening{index}",
                    f"入口の集中だけを検査する本文{index}です。",
                    families=(f"human_response_family_{index}",),
                )
                for index in range(5)
            ),
            "rr8_opening_strategy_concentration",
        ),
        (
            (
                _synthetic_case(
                    "rich_one_line",
                    "二手を一文へ押し込みました。",
                    depth="layered",
                    roles=("attention", "felt_response"),
                    strategies=("emlis_attention_first", "felt_response_first"),
                    families=("human_response_attention", "human_response_felt"),
                    planned_moves=2,
                ),
            ),
            "rr8_rich_input_one_line_collapse",
        ),
        (
            (
                _synthetic_case(
                    "minimal_filled",
                    "短い入力を一文。さらに一文。",
                    sentences=2,
                    roles=("attention", "felt_response"),
                    strategies=("emlis_attention_first", "felt_response_first"),
                    families=("human_response_attention", "human_response_felt"),
                    planned_moves=2,
                ),
            ),
            "rr8_short_input_water_filling",
        ),
        (
            (
                _synthetic_case(
                    "distinctness_failed",
                    "役割が重なっています。",
                    distinctness_gate="failed",
                ),
            ),
            "rr8_move_distinctness_failed",
        ),
        (
            (
                _synthetic_case(
                    "enumeration_failed",
                    "列挙になっています。",
                    non_enumeration_gate="failed",
                ),
            ),
            "rr8_non_enumerative_selection_failed",
        ),
    ],
)
def test_rr8_batch_qa_negative_contracts(cases, expected_reason: str) -> None:
    batch = evaluate_rr8_reception_batch(
        "negative_contract",
        cases,
        thresholds=_EXACT_THRESHOLDS,
    )
    assert batch.verdict == "failed"
    assert expected_reason in batch.reason_codes


def test_rr8_body_free_meta_rejects_raw_body() -> None:
    payload = _cohort_results()["exact8"].as_body_free_meta()
    leaked = deepcopy(payload)
    leaked["raw_input"] = "body"
    with pytest.raises(ValueError, match="rr8_body_free_metadata_contract_failed"):
        assert_body_free_metadata(leaked)
    for key in (
        "comment_text",
        "source_anchor",
        "input",
        "text",
        "body",
        "content",
        "user_input",
        "visible_text",
    ):
        leaked = deepcopy(payload)
        leaked[key] = "secret"
        with pytest.raises(
            ValueError,
            match="rr8_body_free_metadata_contract_failed",
        ):
            assert_body_free_metadata(leaked)


def test_rr8_selector_and_surface_have_no_case_specific_route() -> None:
    import emlis_ai_grounded_human_reception as surface_owner
    import emlis_ai_grounded_observation_plan as plan_owner

    selector_source = inspect.getsource(
        plan_owner.build_grounded_reception_opportunities
    )
    surface_source = inspect.getsource(
        surface_owner.realize_grounded_human_reception
    )
    combined = selector_source + surface_source
    assert "case_id" not in combined
    assert "expected_hash" not in combined
    assert "completed_sentence" not in combined
    assert "raw_character_count" not in selector_source
    assert "I6-L03" not in combined
    assert "I6-C01" not in combined
    assert "I6-D02" not in combined


def test_rr8_anchor_compaction_uses_only_safe_contiguous_boundaries() -> None:
    from emlis_ai_grounded_human_reception import _compact_bound_anchor

    assert _compact_bound_anchor("長い長い長いたのしい記録内容です", 12) == ""
    assert _compact_bound_anchor("これはとても大切な記録です", 10) == ""
    source = "見出しを紙に書き、終わった箇所へ印を付けた"
    anchor = _compact_bound_anchor(source, 20)
    assert anchor
    assert anchor in source
    assert len(anchor) <= 20


def test_rr8_public_api_db_rn_boundary_remains_sanitized() -> None:
    row = _load(_EXACT8)["cases"][0]
    reply = asyncio.run(
        render_emlis_ai_reply(
            user_id="rr8-public-boundary",
            subscription_tier="free",
            current_input=row["exact_current_input"],
        )
    )
    public = build_public_emlis_input_feedback_meta(
        reply.meta,
        comment_text_present=bool(reply.comment_text),
        subscription_tier="free",
    )
    public_payload = json.dumps(public, ensure_ascii=False, sort_keys=True)
    assert reply.comment_text
    assert reply.meta["public_contract_changed"] is False
    assert reply.meta["api_route_changed"] is False
    assert reply.meta["db_physical_name_changed"] is False
    assert reply.meta["rn_visible_contract_changed"] is False
    assert public["schema_version"] == "emlis.public_input_feedback_meta.v1"
    assert public["observation_status"] == "passed"
    assert "grounded_observation" not in public
    assert row["exact_current_input"]["memo"] not in public_payload
    assert reply.comment_text not in public_payload


def test_rr8_automated_receipt_is_live_hash_bound_and_body_free() -> None:
    receipt = _load(_AUTOMATED_RECEIPT)
    source_manifest, source_snapshot_sha256 = _source_snapshot()
    cohorts = _cohort_results()

    assert receipt["schema_version"] == (
        "cocolon.emlis.grounded_human_reception.rr8_local_qa_receipt.v1"
    )
    assert receipt["source_snapshot_files"] == source_manifest
    assert receipt["source_snapshot_sha256"] == source_snapshot_sha256
    assert receipt["design_source_sha256"] == _DESIGN_SOURCE_SHA256
    assert receipt["exact8_fixture_sha256"] == _sha256_file(_EXACT8)
    assert receipt["unseen12_fixture_sha256"] == _sha256_file(_UNSEEN12)
    assert receipt["automated_qa_order"] == [
        "type_and_unit",
        "opportunity_tests",
        "depth_and_move_plan_tests",
        "sentence_plan_and_clause_plan_tests",
        "surface_tests",
        "gate_tests",
        "recovery_tests",
        "exact8",
        "same16",
        "unseen12",
        "api_db_rn_boundary_regression",
        "relevant_backend_regression",
        "compile",
    ]
    assert set(receipt["automated_qa_order_status"].values()) == {"passed"}
    assert receipt["cohorts"] == {
        key: _receipt_cohort_summary(result)
        for key, result in cohorts.items()
    }
    assert receipt["technical_acceptance"] == "passed"
    assert receipt["product_readfeel_status"] == "separate_rr9_human_receipt"
    assert receipt["technical_pass_is_product_readfeel_pass"] is False
    assert receipt["progression_authority"] == "none"
    assert receipt["valid_for_progression"] is False
    assert receipt["actual_device_result_included"] is False
    assert_body_free_metadata(receipt)
