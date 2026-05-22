from __future__ import annotations

import json

import pytest

from emlis_ai_complete_product_quality_measurement_connection import (
    build_complete_product_quality_measurement_connection,
)
from emlis_ai_complete_surface_quality_branching import (
    RUNTIME_SURFACE_QUALITY_BRANCHING_VERSION,
    assert_runtime_surface_quality_branch_meta_only,
    dump_runtime_surface_quality_branch,
    known_runtime_surface_quality_branch_targets,
    resolve_runtime_surface_quality_branch,
)
from emlis_ai_complete_surface_quality_signature import build_surface_quality_signature
from emlis_ai_runtime_surface_source_lock import build_runtime_surface_source_lock

_TEMPLATE_LIKE_TEXT = (
    "Emlisです。\n"
    "体調を整えることが中心にあります。\n"
    "その中でも、お仕事を頑張って今後の準備をすることも見えています。\n"
    "その中でも、だいぶ先になることも重なっています。"
)
_GRAMMAR_RISK_TEXT = (
    "Emlisです。\n"
    "最近仲良くなった男の人にはなんて事ない日を大切にしてもらえることが中心にあります。\n"
    "その中でも、だからこそ私から離れことも見えています。\n"
    "同じ時間の中に重なっていることも残っています。"
)
_NATURAL_TEXT = (
    "Emlisです。\n"
    "今は、自分の内側を少し整え直したい時間が前に出ています。\n"
    "急いで決めるよりも、いま残っている疲れを見落とさないことが大事そうです。\n"
    "その奥には、次へ進みたい気持ちも一緒に残っています。"
)


def _lock(source: str = "complete_initial") -> dict[str, object]:
    return build_runtime_surface_source_lock(
        trace_id=f"trace-{source}",
        emotion_log_id=f"emotion-{source}",
        observation_status="passed",
        backend_comment_text_length=120,
        display_confirmed=True,
        coverage_group="short_daily",
        resolution_meta={"requested_composer": source, "complete_initial_client_used": source == "complete_initial"},
        runtime_meta={"composer_source": source, "composer_model": "cocolon.test"},
    )


def _base_report(*, source: str = "complete_initial", signature: dict[str, object] | None = None) -> dict[str, object]:
    signature = signature or build_surface_quality_signature(comment_text=_NATURAL_TEXT)
    return {
        "row_count": 1,
        "event_count": 1,
        "runtime_surface_source_lock": _lock(source),
        "scorecard": {
            "machine_metrics_ready": True,
            "blind_qa_ready": True,
            "read_feeling_score": 1.0,
            "binding_pass_rate": 1.0,
            "expected_binding_count": 2,
            "binding_supported_sentence_count": 2,
            "surface_metrics_ready": True,
            "surface_signature_count": 1,
            "surface_signature_repeat_rate": 0.0,
            "connector_repetition_rate": 0.0,
            "predicate_family_repetition_rate": 0.0,
            "ending_repetition_rate": 0.0,
            "generic_opening_rate": 0.0,
            "grammar_warning_rate": 0.0,
            "surface_template_major_count": 0,
            "release_blockers": [],
            "blind_qa_metrics": {
                "blind_qa_ready": True,
                "read_feeling_score": 1.0,
                "dimension_scores": {"read_feeling": 1.0, "distance": 1.0, "naturalness": 1.0},
                "raw_input_included": False,
                "comment_text_included": False,
            },
            "raw_input_included": False,
            "comment_text_included": False,
        },
        "coverage_runtime_baseline": {
            "coverage_runtime_baseline_ready": True,
            "runtime_branching_uses_fixture_strings": False,
            "fixture_text_used_for_runtime_branching": False,
            "raw_input_included": False,
            "comment_text_included": False,
        },
        "surface_quality_signature": signature,
        "release_blockers": [],
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
    }


def _row(signature: dict[str, object], *, trace_id: str = "step5-report") -> dict[str, object]:
    source_lock = _lock("complete_initial")
    return {
        "trace_id": trace_id,
        "emotion_log_id": f"emotion-{trace_id}",
        "coverage_group": "short_daily",
        "backend_status": "passed",
        "backend_len": 120,
        "backend_comment_text_present": True,
        "backend_public_passed": True,
        "frontend_joined": True,
        "frontend_join_status": "joined",
        "modal_opened": True,
        "display_confirmed": True,
        "diagnostic_capture_status": "captured",
        "backend_diagnostic_capture_status": "captured",
        "frontend_diagnostic_capture_status": "captured",
        "classification": "passed_displayed",
        "measurement_classification": "passed_displayed",
        "candidate_generated": True,
        "binding_supported_sentence_count": 2,
        "expected_binding_count": 2,
        "runtime_surface_source_lock": source_lock,
        "surface_quality_signature": signature,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
    }


def _green_review(group: str = "short_daily") -> dict[str, object]:
    return {
        "review_id": f"green-{group}",
        "coverage_group": group,
        "ratings": {
            "read_feeling": "green",
            "evidence_retention": "green",
            "distance": "green",
            "naturalness": "green",
            "non_template": "green",
        },
    }


def test_step5_branch_resolver_prioritizes_complete_runtime_activation_before_surface() -> None:
    report = _base_report(source="limited", signature=build_surface_quality_signature(comment_text=_TEMPLATE_LIKE_TEXT))
    report["scorecard"]["surface_template_major_count"] = 1  # type: ignore[index]
    report["scorecard"]["release_blockers"] = ["surface_template_major_detected"]  # type: ignore[index]

    branch = resolve_runtime_surface_quality_branch(report)

    assert branch["version"] == RUNTIME_SURFACE_QUALITY_BRANCHING_VERSION
    assert branch["step5_branch_resolver_ready"] is True
    assert branch["target_layer"] == "complete_runtime_activation"
    assert branch["repair_allowed"] is True
    assert "composer_source:limited" in branch["branch_reasons"]
    assert branch["runtime_branching_uses_fixture_strings"] is False
    assert branch["surface_text_repaired_by_step5"] is False


def test_step5_branch_resolver_prioritizes_grounding_then_grammar_then_surface() -> None:
    grammar_report = _base_report(signature=build_surface_quality_signature(comment_text=_GRAMMAR_RISK_TEXT))
    grammar_report["scorecard"]["grammar_warning_rate"] = 1.0  # type: ignore[index]
    grammar_report["scorecard"]["surface_template_major_count"] = 1  # type: ignore[index]

    grammar_branch = resolve_runtime_surface_quality_branch(grammar_report)
    assert grammar_branch["target_layer"] == "phrase_unit_grammar_normalizer"
    assert grammar_branch["repair_allowed"] is True

    grounding_report = _base_report(signature=build_surface_quality_signature(comment_text=_GRAMMAR_RISK_TEXT))
    grounding_report["scorecard"]["binding_pass_rate"] = 0.5  # type: ignore[index]
    grounding_report["scorecard"]["binding_supported_sentence_count"] = 1  # type: ignore[index]
    grounding_report["scorecard"]["expected_binding_count"] = 2  # type: ignore[index]
    grounding_report["release_blockers"] = ["unsupported_sentence"]

    grounding_branch = resolve_runtime_surface_quality_branch(grounding_report)
    assert grounding_branch["target_layer"] == "grounding_relation_binding_repair"
    assert "unsupported_sentence" in grounding_branch["branch_reasons"]

    surface_report = _base_report(signature=build_surface_quality_signature(comment_text=_TEMPLATE_LIKE_TEXT))
    surface_report["scorecard"]["surface_template_major_count"] = 1  # type: ignore[index]
    surface_report["scorecard"]["surface_signature_repeat_rate"] = 0.5  # type: ignore[index]

    surface_branch = resolve_runtime_surface_quality_branch(surface_report)
    assert surface_branch["target_layer"] == "surface_realizer_2_1_anti_template"
    assert surface_branch["repair_allowed"] is True
    assert "固定完成文" in " ".join(surface_branch["do_not_touch"])


def test_step5_unknown_diagnostic_returns_to_enrichment_with_repair_blocked() -> None:
    branch = resolve_runtime_surface_quality_branch(
        {
            "row_count": 1,
            "event_count": 1,
            "classification": "unknown_diagnostic_missing",
            "requires_diagnostic_enrichment": True,
            "raw_input_included": False,
            "comment_text_included": False,
        }
    )

    assert branch["target_layer"] == "diagnostic_enrichment"
    assert branch["repair_allowed"] is False
    assert branch["requires_diagnostic_enrichment"] is True
    assert branch["unknown_or_unclassified_returns_to_diagnostic_enrichment"] is True


def test_step5_blind_qa_low_routes_to_tone_but_missing_qa_routes_to_long_run() -> None:
    tone_report = _base_report(signature=build_surface_quality_signature(comment_text=_NATURAL_TEXT))
    tone_report["scorecard"]["read_feeling_score"] = 0.5  # type: ignore[index]
    tone_report["scorecard"]["blind_qa_metrics"] = {  # type: ignore[index]
        "blind_qa_ready": True,
        "read_feeling_score": 0.5,
        "dimension_scores": {"read_feeling": 0.5, "distance": 0.6, "naturalness": 1.0},
        "raw_input_included": False,
        "comment_text_included": False,
    }

    tone_branch = resolve_runtime_surface_quality_branch(tone_report)
    assert tone_branch["target_layer"] == "tone_engine_2_1_blind_qa"
    assert tone_branch["tone_branch_requires_blind_qa"] is True

    qa_report = _base_report(signature=build_surface_quality_signature(comment_text=_NATURAL_TEXT))
    qa_report["scorecard"]["blind_qa_ready"] = False  # type: ignore[index]
    qa_report["scorecard"]["read_feeling_score"] = None  # type: ignore[index]
    qa_report["scorecard"]["blind_qa_metrics"] = {"blind_qa_ready": False, "raw_input_included": False, "comment_text_included": False}  # type: ignore[index]

    qa_branch = resolve_runtime_surface_quality_branch(qa_report)
    assert qa_branch["target_layer"] == "blind_qa_long_run"
    assert qa_branch["repair_allowed"] is False
    assert qa_branch["qa_branch_only"] is True


def test_step5_measurement_connection_carries_branch_resolver_without_contract_changes() -> None:
    signature = build_surface_quality_signature(comment_text=_TEMPLATE_LIKE_TEXT)
    report = build_complete_product_quality_measurement_connection(
        rows=[_row(signature)],
        blind_qa_reviews=[_green_review()],
        run_id="runtime-surface-step5",
    )

    branch = report["runtime_surface_quality_branch"]
    assert report["step5_runtime_surface_quality_branch_resolver_ready"] is True
    assert report["runtime_surface_quality_target_layer"] == "surface_realizer_2_1_anti_template"
    assert branch["target_layer"] == "surface_realizer_2_1_anti_template"
    assert branch["runtime_branching_uses_fixture_strings"] is False
    assert branch["surface_text_repaired_by_step5"] is False
    assert report["fixture_text_used_for_runtime_branching"] is False
    assert report["public_release_applied"] is False
    assert report["product_gate_public_release_applied"] is False
    assert report["api_route_changed"] is False
    assert report["db_physical_name_changed"] is False
    assert report["display_gate_relaxed"] is False

    dumped = json.dumps(report, ensure_ascii=False)
    assert _TEMPLATE_LIKE_TEXT not in dumped
    assert "体調を整える" not in dumped
    assert '"comment_text"' not in dumped


def test_step5_branch_plan_is_meta_only_and_rejects_text_payload_keys() -> None:
    branch = resolve_runtime_surface_quality_branch(_base_report(signature=build_surface_quality_signature(comment_text=_NATURAL_TEXT)))
    dumped = dump_runtime_surface_quality_branch(branch)

    assert "blind_qa_long_run" in known_runtime_surface_quality_branch_targets()
    assert json.loads(dumped)["comment_text_body_included"] is False
    assert '"comment_text"' not in dumped

    unsafe = dict(branch)
    unsafe["comment_text"] = "出してはいけない本文"
    with pytest.raises(ValueError):
        assert_runtime_surface_quality_branch_meta_only(unsafe)
