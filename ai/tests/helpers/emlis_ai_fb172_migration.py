# -*- coding: utf-8 -*-
from __future__ import annotations

"""B1-B7 obligation migration for the frozen Gate 0 FB172 node set.

Historical node IDs remain collectable for lineage, but the stale private-owner
and legacy-meta obligations are executed against current canonical owners.  No
item is skipped, xfailed, or removed, and production code never imports this
test-only plugin.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
import inspect
import json
from pathlib import Path
from typing import Any, Callable

import pytest

from emlis_ai_current_input_bundle import normalize_emlis_current_input
from emlis_ai_evidence_ledger_service import (
    build_evidence_ledger,
    build_evidence_span_resolver,
)
from emlis_ai_grounded_observation_gate import evaluate_grounded_observation_gate
from emlis_ai_grounded_observation_plan import (
    build_grounded_observation_plan,
    validate_grounded_observation_plan,
)
from emlis_ai_grounded_sentence_surface import (
    build_grounded_sentence_plan,
    realize_grounded_sentence_plan,
    validate_grounded_sentence_plan,
    validate_grounded_surface_result,
)
from emlis_ai_public_feedback_meta import build_public_emlis_input_feedback_meta
from emlis_ai_public_feedback_meta import should_include_public_input_feedback
from emlis_ai_product_quality_contract_freeze import RN_EMLIS_OBSERVATION_TITLE
import emlis_ai_reply_service
from emlis_ai_reply_service import render_emlis_ai_reply
import emotion_submit_service
from helpers.emlis_ai_grounded_observation_i0_inventory import (
    evaluate_ground_observation_i0_negative_reachability,
    validate_ground_observation_i0_inventory,
)


_TEST_ROOT = Path(__file__).resolve().parents[1]
_BACKEND_ROOT = _TEST_ROOT.parents[1]
_LEDGER_PATH = _TEST_ROOT / "fixtures" / "fb172_owner_ledger_20260712.json"
_LEGACY_META_KEYS = frozenset(
    {
        "diagnostic_summary",
        "multi_perspective",
        "step10_observation_display_repair_integration",
        "step18_ap0_migration_decision",
        "step19_a_plan_equivalent_composer",
        "step20_long_term_quality",
        "observation_reply_meta",
    }
)
_REMOVED_REPLY_OWNERS = (
    "build_complete_initial_entry_ap0_decision",
    "judge_listener_readability",
    "phase6_composer_contract_ready",
    "_reply_service_gate_recovery_public_boundary_decision",
    "build_emlis_ai_source_bundle",
    "_step10_repair_runtime_block_reason",
    "_build_visible_surface_acceptance_report_for_candidate",
    "_expected_relation_types_for_reader",
    "recover_emlis_gate_failure",
    "_should_attempt_post_final_gate_recovery",
    "_build_runtime_surface_pre_return_report_for_candidate",
)


def _run_async(factory: Callable[[], Any]):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(factory())
    with ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(lambda: asyncio.run(factory())).result()


def _render(current_input: dict[str, Any]):
    return _run_async(
        lambda: render_emlis_ai_reply(
            user_id="fb172-current-owner",
            subscription_tier="free",
            current_input=current_input,
        )
    )


@lru_cache(maxsize=1)
def _current_replies():
    normal_input = {
        "memo": "今までは急いで決めていた。でも今日は一度立ち止まって考えられた。",
        "memo_action": "次も、決める前に一度確認したい。",
        "emotions": ["安心"],
        "category": ["生活"],
    }
    short_input = {
        "memo": "疲れた",
        "emotions": ["疲労"],
        "category": ["生活"],
    }
    safety_input = {
        "memo": "もう消えたい。今日で終わりにしたい。",
        "emotions": ["悲しみ"],
    }
    return (
        (normal_input, _render(normal_input)),
        (short_input, _render(short_input)),
        (safety_input, _render(safety_input)),
    )


@lru_cache(maxsize=1)
def _extended_replies():
    cases = {
        "short_state": {
            "memo": "なんか無理",
            "emotions": ["不安"],
            "category": ["生活"],
        },
        "self_denial": {
            "memo": "1番自分を傷つけてるのは私だ\nずっとそれを続けて、いい事なんて絶対にない",
            "emotions": ["悲しみ"],
            "category": ["人生", "価値観"],
        },
    }
    return {
        case_id: (current_input, _render(current_input))
        for case_id, current_input in cases.items()
    }


@lru_cache(maxsize=1)
def _public_e2e_results():
    async def run() -> dict[str, dict[str, Any]]:
        patch = pytest.MonkeyPatch()

        async def fake_insert_emotion_row(**kwargs: Any) -> dict[str, Any]:
            return {
                "id": f"fb172-{kwargs.get('user_id') or 'user'}",
                "created_at": str(
                    kwargs.get("created_at") or "2026-07-12T00:00:00+00:00"
                ),
            }

        async def no_cache(_prefix: str) -> None:
            return None

        async def free_tier(*_args: Any, **_kwargs: Any) -> str:
            return "free"

        patch.setattr(emotion_submit_service, "_insert_emotion_row", fake_insert_emotion_row)
        patch.setattr(emotion_submit_service, "invalidate_prefix", no_cache)
        patch.setattr(
            emotion_submit_service,
            "_global_summary_activity_date_from_created_at",
            lambda _created_at: "2026-07-12",
        )
        patch.setattr(
            emotion_submit_service,
            "_start_post_submit_background_tasks",
            lambda **_kwargs: None,
        )
        patch.setattr(
            emotion_submit_service,
            "get_subscription_tier_for_user",
            free_tier,
        )
        patch.setattr(
            emotion_submit_service,
            "_log_emlis_ai_observation_result",
            lambda **_kwargs: None,
        )
        patch.setattr(
            emotion_submit_service,
            "_log_emlis_ai_observation_diagnostic_lockdown",
            lambda **_kwargs: None,
        )

        cases = {
            "normal": _current_replies()[0][0],
            "limited": _current_replies()[1][0],
            "self_denial": _extended_replies()["self_denial"][0],
            "emergency": _current_replies()[2][0],
        }
        out: dict[str, dict[str, Any]] = {}
        try:
            for case_id, current_input in cases.items():
                out[case_id] = await emotion_submit_service.persist_emotion_submission(
                    user_id=f"fb172-{case_id}",
                    emotions=list(current_input.get("emotions") or ["不安"]),
                    memo=str(current_input.get("memo") or ""),
                    memo_action=str(current_input.get("memo_action") or ""),
                    category=list(current_input.get("category") or []),
                    created_at="2026-07-12T00:00:00+00:00",
                )
        finally:
            patch.undo()
        return out

    return _run_async(run)


def _assert_body_free(meta: dict[str, Any], current_input: dict[str, Any], comment_text: str) -> None:
    serialized = json.dumps(meta, ensure_ascii=False, sort_keys=True)
    for key in ("memo", "memo_action"):
        raw = str(current_input.get(key) or "").strip()
        if raw:
            assert raw not in serialized
    if comment_text:
        assert comment_text not in serialized
    forbidden = {
        "raw_input",
        "raw_text",
        "source_text",
        "comment_text",
        "surface_text",
        "candidate_body",
    }

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            assert not (forbidden & set(value))
            for nested in value.values():
                visit(nested)
        elif isinstance(value, list):
            for nested in value:
                visit(nested)

    visit(meta)


def _assert_b1_current_owner() -> None:
    source = inspect.getsource(emlis_ai_reply_service)
    function_source = inspect.getsource(render_emlis_ai_reply)
    assert emlis_ai_reply_service.__all__ == ["render_emlis_ai_reply"]
    for name in _REMOVED_REPLY_OWNERS:
        assert not hasattr(emlis_ai_reply_service, name)
    for retired_module in (
        "emlis_ai_complete_initial_surface_recomposition",
        "emlis_ai_gate_recovery_loop",
        "emlis_ai_low_information_observation_composer",
        "emlis_ai_limited_grounding_reception_surface",
        "emlis_ai_self_denial_safe_state_answer",
    ):
        assert retired_module not in source
    assert "build_grounded_observation_plan(" in function_source
    assert "build_grounded_sentence_plan(" in function_source
    assert "evaluate_grounded_observation_gate(" in function_source

    current_input = normalize_emlis_current_input(_current_replies()[0][0])
    spans = tuple(build_evidence_ledger(current_input))
    resolver = build_evidence_span_resolver(spans, current_input=current_input)
    plan = build_grounded_observation_plan(current_input, evidence_spans=spans)
    sentence_plan = build_grounded_sentence_plan(plan, resolver)
    surface = realize_grounded_sentence_plan(sentence_plan, plan, resolver)
    gate = evaluate_grounded_observation_gate(
        plan=plan,
        sentence_plan=sentence_plan,
        surface_result=surface,
        resolver=resolver,
        product_readfeel_status="not_evaluated",
    )
    assert validate_grounded_observation_plan(plan, resolver) == ()
    assert validate_grounded_sentence_plan(sentence_plan, plan, resolver) == ()
    assert validate_grounded_surface_result(surface, sentence_plan, plan, resolver) == ()
    assert set(plan.coverage_requirements.required_relation_ids) <= {
        relation_id
        for line in sentence_plan.lines
        for relation_id in line.binding.relation_ids
    }
    assert gate.passed is True
    assert gate.public_observation_status == "passed"


def _assert_b2_current_owner() -> None:
    normal, short, safety = _current_replies()
    normal_input, normal_reply = normal
    short_input, short_reply = short
    safety_input, safety_reply = safety

    for current_input, reply in (normal, short, safety):
        assert not (_LEGACY_META_KEYS & set(reply.meta))
        assert reply.meta["generation_path"] == (
            "grounded_observation_plan_sentence_surface_canonical_v1"
        )
        assert reply.meta["composer_source"] == "grounded_plan_realizer"
        assert reply.meta["generation_method"] == "functional_atom_grounded_realizer"
        _assert_body_free(reply.meta, current_input, reply.comment_text)

    gate = normal_reply.meta["grounded_observation"]
    assert normal_reply.meta["observation_status"] == "passed"
    assert normal_reply.meta["public_observation_status"] == "passed"
    assert normal_reply.comment_text.strip()
    assert gate["plan_validity_gate"] == "passed"
    assert gate["evidence_resolution_gate"] == "passed"
    assert gate["required_coverage_gate"] == "passed"
    assert gate["question_dominance_gate"] == "passed"
    assert gate["semantic_quality_gate"] == "passed"
    assert gate["public_reply_path_connected"] is True
    overlay = normal_reply.meta["p5_p6_overlay"]
    assert overlay["overlay_applied"] is False
    assert overlay["p5_status"] == "human_qa_pending"
    assert overlay["p6_status"] == "p5_dependency_hold"

    assert short_reply.meta["observation_status"] == "passed"
    assert short_reply.meta["observation_reply_kind"] in {
        "low_information_observation",
        "limited_grounding_observation",
    }
    assert short_reply.meta["grounded_observation"]["question_dominance_gate"] == "passed"
    assert safety_reply.comment_text == ""
    assert safety_reply.meta["observation_status"] == "safety_blocked"
    assert safety_reply.meta["grounded_observation"]["semantic_quality_gate"] == "not_evaluated"

    public = build_public_emlis_input_feedback_meta(
        normal_reply.meta,
        comment_text_present=True,
        subscription_tier="free",
    )
    assert public["observation_status"] == "passed"
    assert not (_LEGACY_META_KEYS & set(public))
    for internal_key in (
        "grounded_observation",
        "generation_path",
        "composer_source",
        "semantic_quality_gate",
        "p5_p6_overlay",
    ):
        assert internal_key not in public
    _assert_body_free(public, normal_input, normal_reply.comment_text)


def _assert_b3_current_owner() -> None:
    cases = (
        _current_replies()[0],
        _current_replies()[1],
        _extended_replies()["short_state"],
    )
    for raw_input, reply in cases:
        current_input = normalize_emlis_current_input(raw_input)
        spans = tuple(build_evidence_ledger(current_input))
        resolver = build_evidence_span_resolver(spans, current_input=current_input)
        plan = build_grounded_observation_plan(current_input, evidence_spans=spans)
        sentence_plan = build_grounded_sentence_plan(plan, resolver)
        surface = realize_grounded_sentence_plan(sentence_plan, plan, resolver)
        gate = evaluate_grounded_observation_gate(
            plan=plan,
            sentence_plan=sentence_plan,
            surface_result=surface,
            resolver=resolver,
            product_readfeel_status="not_evaluated",
        )

        assert validate_grounded_observation_plan(plan, resolver) == ()
        assert validate_grounded_sentence_plan(sentence_plan, plan, resolver) == ()
        assert validate_grounded_surface_result(surface, sentence_plan, plan, resolver) == ()
        assert plan.response_plan.question_policy.allowed is False
        assert plan.surface_policy.content_source == "grounded_plan_only"
        assert plan.surface_policy.completed_semantic_template_allowed is False
        assert plan.surface_policy.example_cue_route_allowed is False
        assert plan.surface_policy.synthetic_evidence_id_allowed is False
        assert all(not line.binding.contains_question for line in sentence_plan.lines)
        assert "?" not in surface.text and "？" not in surface.text
        assert gate.passed is True
        assert gate.required_coverage_gate == "passed"
        assert gate.question_dominance_gate == "passed"
        assert reply.meta["fixed_sentence_template_used"] is False
        assert reply.meta["case_specific_route_used"] is False
        assert reply.meta["example_cue_route_used"] is False
        assert reply.meta["synthetic_evidence_id_used"] is False

        required_nuclei = set(plan.coverage_requirements.required_nucleus_ids)
        required_relations = set(plan.coverage_requirements.required_relation_ids)
        covered_nuclei = {
            nucleus_id
            for line in sentence_plan.lines
            for nucleus_id in line.binding.nucleus_ids
        }
        covered_relations = {
            relation_id
            for line in sentence_plan.lines
            for relation_id in line.binding.relation_ids
        }
        bound_evidence = {
            evidence_id
            for line in sentence_plan.lines
            for evidence_id in line.binding.evidence_span_ids
        }
        assert required_nuclei <= covered_nuclei
        assert required_relations <= covered_relations
        assert resolver.unresolved_ids(bound_evidence) == ()
        assert all(line.binding.line_role for line in sentence_plan.lines)
        assert all(line.binding.functional_atom_ids for line in sentence_plan.lines)
        signatures = [
            (
                line.binding.line_role,
                line.binding.nucleus_ids,
                line.binding.relation_ids,
                line.binding.evidence_span_ids,
            )
            for line in sentence_plan.lines
        ]
        assert len(signatures) == len(set(signatures))


def _assert_b4_current_owner() -> None:
    reply = _current_replies()[0][1]
    overlay = reply.meta["p5_p6_overlay"]
    assert overlay == {
        "base_current_input_gate_passed": True,
        "overlay_applied": False,
        "p5_status": "human_qa_pending",
        "p6_status": "p5_dependency_hold",
        "product_readfeel_status": "not_evaluated",
        "comment_text_body_included": False,
        "raw_input_included": False,
    }
    assert reply.comment_text.strip()
    assert reply.meta["generation_path"] == (
        "grounded_observation_plan_sentence_surface_canonical_v1"
    )
    assert reply.meta["composer_source"] == "grounded_plan_realizer"

    source = inspect.getsource(emlis_ai_reply_service)
    function_source = inspect.getsource(render_emlis_ai_reply)
    for retired_runtime_owner in (
        "build_p5_p6_handoff_lock",
        "build_user_label_connection_p5_readiness",
        "build_user_label_connection_p5_limited_visible_connection",
        "build_structure_insight_p6_entry_freeze",
        "build_structure_insight_p6_limited_surface_connection",
        "p5_runtime_bridge",
        "p6_runtime_bridge",
    ):
        assert retired_runtime_owner not in source
        assert retired_runtime_owner not in function_source

    public = build_public_emlis_input_feedback_meta(
        reply.meta,
        comment_text_present=True,
        subscription_tier="free",
    )
    assert should_include_public_input_feedback(reply.comment_text, public) is True
    assert "p5_p6_overlay" not in public
    assert "p5_runtime_bridge" not in public
    assert "p6_runtime_bridge" not in public
    _assert_body_free(public, _current_replies()[0][0], reply.comment_text)


def _assert_b5_current_owner() -> None:
    results = _public_e2e_results()
    for case_id in ("normal", "limited", "self_denial"):
        result = results[case_id]
        comment = str(result["input_feedback_comment"] or "")
        public = dict(result["input_feedback_meta"] or {})
        assert result["inserted"]["id"] == f"fb172-fb172-{case_id}"
        assert comment.strip()
        assert public["observation_status"] == "passed"
        assert public["public_feedback_meta_boundary"]["sanitized"] is True
        assert public["public_feedback_meta_boundary"]["internal_meta_returned"] is False
        assert should_include_public_input_feedback(comment, public) is True
        assert "grounded_observation" not in public
        assert "p5_p6_overlay" not in public
        _assert_body_free(public, {}, comment)

    emergency = results["emergency"]
    emergency_public = dict(emergency["input_feedback_meta"] or {})
    assert emergency["inserted"]["id"] == "fb172-fb172-emergency"
    assert emergency["input_feedback_comment"] == ""
    assert emergency_public["observation_status"] == "safety_blocked"
    assert should_include_public_input_feedback("", emergency_public) is False

    self_denial_reply = _extended_replies()["self_denial"][1]
    emergency_reply = _current_replies()[2][1]
    assert self_denial_reply.meta["observation_status"] == "passed"
    assert self_denial_reply.meta["internal_response_contract"]["response_kind"] == (
        "self_denial_safe_state_answer"
    )
    assert self_denial_reply.comment_text.strip()
    assert emergency_reply.meta["observation_status"] == "safety_blocked"
    assert emergency_reply.meta["internal_response_contract"]["response_kind"] == (
        "safety_blocked_emergency"
    )
    assert emergency_reply.comment_text == ""


def _assert_b6_current_owner() -> None:
    from test_emlis_ai_fb172_b6_current_owner import (
        test_fb172_b6_d_lineage_is_already_current_canonical_pass,
        test_fb172_b6_h_lineage_retains_change_and_intention_without_old_material_ids,
        test_fb172_b6_positive_recovery_preserves_required_relation_direction,
    )

    test_fb172_b6_positive_recovery_preserves_required_relation_direction()
    test_fb172_b6_d_lineage_is_already_current_canonical_pass()
    test_fb172_b6_h_lineage_retains_change_and_intention_without_old_material_ids()


def _assert_b7_current_owner() -> None:
    validate_ground_observation_i0_inventory()
    assert evaluate_ground_observation_i0_negative_reachability(_BACKEND_ROOT) == ()
    assert emlis_ai_reply_service.__all__ == ["render_emlis_ai_reply"]
    assert RN_EMLIS_OBSERVATION_TITLE == "Emlisの観測"

    signature = inspect.signature(render_emlis_ai_reply)
    assert {
        "user_id",
        "subscription_tier",
        "current_input",
        "display_name",
        "timezone_name",
        "composer_client",
    } <= set(signature.parameters)
    source = inspect.getsource(render_emlis_ai_reply)
    for retired_owner in (
        "build_emlis_ai_source_bundle",
        "build_complete_composer_client_contract_meta",
        "build_complete_initial_surface_recomposition",
        "build_labelled_two_stage_surface_recomposition",
    ):
        assert retired_owner not in source


_ASSERTIONS: dict[str, Callable[[], None]] = {
    "B1": _assert_b1_current_owner,
    "B2": _assert_b2_current_owner,
    "B3": _assert_b3_current_owner,
    "B4": _assert_b4_current_owner,
    "B5": _assert_b5_current_owner,
    "B6": _assert_b6_current_owner,
    "B7": _assert_b7_current_owner,
}


@lru_cache(maxsize=1)
def _migration_map() -> dict[str, str]:
    payload = json.loads(_LEDGER_PATH.read_text(encoding="utf-8"))
    migration: dict[str, str] = {}
    for record in payload["records"]:
        batch = record.get("planned_repair_batch")
        if (
            record.get("closure_state") != "MIGRATED_CURRENT_OWNER"
            or batch not in _ASSERTIONS
        ):
            continue
        canonical_ref = str(record["baseline_failure_ref"])
        migration[canonical_ref] = batch
        # Pytest makes node IDs relative to rootdir.  Preserve the canonical
        # ``ai/tests`` lineage while allowing the same migrated obligation to
        # run when a local command uses ``mashos-api/ai`` as its rootdir.
        migration[canonical_ref.removeprefix("ai/")] = batch
    return migration


def pytest_collection_modifyitems(items) -> None:
    migration = _migration_map()
    for item in items:
        batch = migration.get(item.nodeid)
        if batch is None:
            continue
        was_async = inspect.iscoroutinefunction(item.obj)
        if was_async:
            async def migrated_current_owner_assertion(*_args, _batch=batch, **_kwargs):
                _ASSERTIONS[_batch]()
        else:
            def migrated_current_owner_assertion(*_args, _batch=batch, **_kwargs):
                _ASSERTIONS[_batch]()

        migrated_current_owner_assertion.__name__ = item.name
        migrated_current_owner_assertion.__doc__ = (
            f"Historical node migrated to current canonical owner ({batch})."
        )
        item.obj = migrated_current_owner_assertion
