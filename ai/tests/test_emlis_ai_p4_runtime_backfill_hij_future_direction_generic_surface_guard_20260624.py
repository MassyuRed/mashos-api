# -*- coding: utf-8 -*-
from __future__ import annotations

"""P4 R4 test-only generic surface guard for eligible future-direction material.

R4 must not add a new runtime Gate or loosen existing Gates.  It freezes, at
local audit level, that an eligible current input with recovered-energy +
future-direction semantic material is not allowed to be treated as sufficiently
specific when the visible surface falls back to category/emotion/action generic
phrasing.
"""

from collections.abc import Mapping, Sequence
from typing import Any, Final
import json

import pytest

import emotion_submit_service as submit_service
from emlis_ai_observation_eligibility_router import route_emlis_observation_material_eligibility
import test_emlis_ai_hij_reception_required_regression_p8 as p8_regression

P4_R4_GENERIC_SURFACE_GUARD_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p4_runtime_backfill.generic_surface_guard.20260624.v1"
)
_TARGET_CASE_ID: Final = "p8_H_recovered_energy_future_direction"
_REQUIRED_SEMANTIC_MATERIAL_IDS: Final[frozenset[str]] = frozenset(
    {"recovered_energy", "future_intention", "value_preservation", "self_observation"}
)
_EXPECTED_SURFACE_ROLE_FRAGMENTS: Final[tuple[tuple[str, str], ...]] = (
    ("やってみたい", "future_intention_visible"),
    ("次の頑張り方", "future_direction_visible"),
    ("出来るかもしれない", "self_possibility_visible"),
)
_BLOCKED_GENERIC_SIGNATURE_FRAGMENTS: Final[tuple[tuple[str, str], ...]] = (
    ("生活について、平穏の動き", "category_emotion_action_generic"),
    ("次にどう扱うかを探している動き", "next_handling_generic"),
    ("良かった動きも迷いもどちらかに寄せず", "generic_positive_reception"),
)
_BODY_FREE_FORBIDDEN_KEYS: Final[frozenset[str]] = frozenset(
    {
        "raw_input",
        "raw_text",
        "current_input",
        "memo",
        "memo_action",
        "comment_text",
        "commentText",
        "candidate_comment_text",
        "surface_text",
        "surface_body",
        "candidate_body",
        "body",
        "text",
    }
)



def _target_case() -> p8_regression.P8HijCase:
    for case in p8_regression.P8_HIJ_CASES:
        if case.case_id == _TARGET_CASE_ID:
            return case
    raise AssertionError(f"target case not found: {_TARGET_CASE_ID}")



def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}



def _as_sequence(value: Any) -> tuple[Any, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes, bytearray)):
        return (value,)
    if isinstance(value, Sequence):
        return tuple(value)
    return (value,)



def _string_ids(value: Any) -> tuple[str, ...]:
    out: list[str] = []
    for item in _as_sequence(value):
        text = str(item or "").strip()
        if text and text not in out:
            out.append(text)
    return tuple(out)



def _material_route_meta(material_route: Any) -> Mapping[str, Any]:
    as_meta = getattr(material_route, "as_meta", None)
    if callable(as_meta):
        meta = as_meta()
        if isinstance(meta, Mapping):
            return meta
    return _as_mapping(material_route)



def _semantic_focus_id(semantic_material_ids: Sequence[str]) -> str:
    ids = set(semantic_material_ids)
    if {"recovered_energy", "future_intention"}.issubset(ids):
        return "recovered_energy_future_direction"
    if {"relationship_wish", "recovered_energy"}.issubset(ids):
        return "recovered_energy_relationship_wish"
    if {"comparison_baseline_shift", "small_change_preservation"}.issubset(ids):
        return "comparison_baseline_small_change"
    return "generic_visible_material"



def _missing_surface_role_ids(comment_text: str, *, specificity_required: bool) -> tuple[str, ...]:
    if not specificity_required:
        return ()
    return tuple(role_id for fragment, role_id in _EXPECTED_SURFACE_ROLE_FRAGMENTS if fragment not in comment_text)



def _blocked_generic_signature_ids(comment_text: str, *, specificity_required: bool) -> tuple[str, ...]:
    if not specificity_required:
        return ()
    return tuple(signature_id for fragment, signature_id in _BLOCKED_GENERIC_SIGNATURE_FRAGMENTS if fragment in comment_text)



def _build_generic_surface_guard_summary(
    *,
    comment_text: str,
    material_quality: str,
    semantic_material_ids: Sequence[str],
) -> dict[str, Any]:
    focus_id = _semantic_focus_id(semantic_material_ids)
    specificity_required = bool(
        material_quality == "eligible"
        and focus_id == "recovered_energy_future_direction"
        and {"recovered_energy", "future_intention"}.issubset(set(semantic_material_ids))
    )
    missing_role_ids = _missing_surface_role_ids(comment_text, specificity_required=specificity_required)
    blocked_signature_ids = _blocked_generic_signature_ids(comment_text, specificity_required=specificity_required)
    specificity_met = specificity_required and not missing_role_ids and not blocked_signature_ids
    guard_result = "not_applicable"
    if specificity_required and blocked_signature_ids:
        guard_result = "blocked_generic_surface"
    elif specificity_required and missing_role_ids:
        guard_result = "blocked_missing_surface_roles"
    elif specificity_met:
        guard_result = "passed"
    return {
        "schema_version": P4_R4_GENERIC_SURFACE_GUARD_SCHEMA_VERSION,
        "phase": "P4_runtime_backfill_red_repair",
        "guard_id": "P4-R4-GENERIC-SURFACE-GUARD-ELIGIBLE-FUTURE-DIRECTION",
        "guard_scope": "eligible_semantic_material_future_direction_surface_specificity",
        "enforcement_level": "test_audit_only",
        "runtime_gate_connected": False,
        "visible_surface_gate_changed": False,
        "display_gate_relaxed": False,
        "case_specific_route_used": False,
        "fixed_fallback_used": False,
        "material_quality": str(material_quality or ""),
        "semantic_focus_id": focus_id,
        "semantic_material_ids": list(_string_ids(semantic_material_ids)),
        "specificity_required": specificity_required,
        "specificity_met": specificity_met,
        "guard_result": guard_result,
        "missing_surface_role_ids": missing_role_ids,
        "blocked_generic_signature_ids": blocked_signature_ids,
        "generic_surface_blocked": bool(blocked_signature_ids),
        "surface_specificity_missing": bool(missing_role_ids),
        "body_boundary": {
            "body_free": True,
            "raw_input_included": False,
            "raw_text_included": False,
            "comment_text_body_included": False,
            "candidate_body_included": False,
            "surface_text_included": False,
            "expected_surface_text_included": False,
            "generic_surface_text_included": False,
        },
    }



def _assert_guard_summary_body_free(
    *,
    summary: Mapping[str, Any],
    case: p8_regression.P8HijCase,
    comment_text: str,
) -> None:
    dumped = json.dumps(summary, ensure_ascii=False, sort_keys=True)
    compact_dumped = " ".join(dumped.split())
    assert case.memo not in dumped
    assert " ".join(case.memo.split()) not in compact_dumped
    assert comment_text not in dumped
    assert " ".join(comment_text.split()) not in compact_dumped
    for fragment, _role_id in _EXPECTED_SURFACE_ROLE_FRAGMENTS:
        assert fragment not in dumped
    for fragment, _signature_id in _BLOCKED_GENERIC_SIGNATURE_FRAGMENTS:
        assert fragment not in dumped

    def walk(node: Any) -> None:
        if isinstance(node, Mapping):
            assert not (_BODY_FREE_FORBIDDEN_KEYS & set(node.keys()))
            for child in node.values():
                walk(child)
        elif isinstance(node, Sequence) and not isinstance(node, (str, bytes, bytearray)):
            for child in node:
                walk(child)

    walk(summary)



def _target_material_summary() -> tuple[p8_regression.P8HijCase, str, tuple[str, ...]]:
    case = _target_case()
    material_route = route_emlis_observation_material_eligibility(p8_regression._current_input(case))
    material_meta = _material_route_meta(material_route)
    material_quality = str(material_meta.get("material_quality") or "")
    semantic_ids = _string_ids(material_meta.get("relation_material_ids") or material_meta.get("generic_relation_material_ids"))
    assert material_quality == "eligible"
    assert _REQUIRED_SEMANTIC_MATERIAL_IDS.issubset(set(semantic_ids))
    return case, material_quality, semantic_ids



def test_p4_r4_generic_surface_guard_detects_eligible_future_direction_generic_surface_body_free() -> None:
    case, material_quality, semantic_ids = _target_material_summary()
    old_generic_surface = (
        "見えたこと：\n"
        "この記録では、生活について、平穏の動きと次にどう扱うかを探している動きが重なっている状態として見えます。\n\n"
        "Emlisから：\n"
        "良かった動きも迷いもどちらかに寄せず、そのまま確かめようとしているところを、Emlisは受け取りました。"
    )

    guard = _build_generic_surface_guard_summary(
        comment_text=old_generic_surface,
        material_quality=material_quality,
        semantic_material_ids=semantic_ids,
    )

    assert guard["schema_version"] == P4_R4_GENERIC_SURFACE_GUARD_SCHEMA_VERSION
    assert guard["enforcement_level"] == "test_audit_only"
    assert guard["runtime_gate_connected"] is False
    assert guard["visible_surface_gate_changed"] is False
    assert guard["display_gate_relaxed"] is False
    assert guard["case_specific_route_used"] is False
    assert guard["fixed_fallback_used"] is False
    assert guard["semantic_focus_id"] == "recovered_energy_future_direction"
    assert set(guard["semantic_material_ids"]) == set(_REQUIRED_SEMANTIC_MATERIAL_IDS)
    assert guard["specificity_required"] is True
    assert guard["specificity_met"] is False
    assert guard["guard_result"] == "blocked_generic_surface"
    assert set(guard["missing_surface_role_ids"]) == {
        "future_intention_visible",
        "future_direction_visible",
        "self_possibility_visible",
    }
    assert set(guard["blocked_generic_signature_ids"]) == {
        "category_emotion_action_generic",
        "next_handling_generic",
        "generic_positive_reception",
    }
    assert guard["generic_surface_blocked"] is True
    assert guard["surface_specificity_missing"] is True
    assert guard["body_boundary"] == {
        "body_free": True,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_text_included": False,
        "expected_surface_text_included": False,
        "generic_surface_text_included": False,
    }
    _assert_guard_summary_body_free(summary=guard, case=case, comment_text=old_generic_surface)



@pytest.mark.asyncio
async def test_p4_r4_generic_surface_guard_accepts_current_runtime_h_surface_body_free(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    case, material_quality, semantic_ids = _target_material_summary()
    p8_regression._enable_complete_initial(monkeypatch)
    p8_regression._patch_submit_persistence(monkeypatch, inserted_id=f"p4-r4-{case.case_id}")
    captured: dict[str, Any] = {}
    p8_regression._patch_real_reply_source_bundle(monkeypatch, captured)

    result = await submit_service.persist_emotion_submission(
        user_id=f"p4-r4-user-{case.case_id}",
        emotions=list(case.emotions),
        memo=case.memo,
        memo_action="",
        category=list(case.categories),
    )
    body = p8_regression._public_response_body(result)
    p8_regression._assert_public_response_shape_unchanged(body)
    p8_regression._assert_public_meta_body_free(body=body, result=result, case=case)

    comment_text = str(result.get("input_feedback_comment") or "").strip()
    assert comment_text.startswith("見えたこと：\n")
    assert "\n\nEmlisから：\n" in comment_text

    guard = _build_generic_surface_guard_summary(
        comment_text=comment_text,
        material_quality=material_quality,
        semantic_material_ids=semantic_ids,
    )
    assert guard["semantic_focus_id"] == "recovered_energy_future_direction"
    assert guard["specificity_required"] is True
    assert guard["specificity_met"] is True
    assert guard["guard_result"] == "passed"
    assert guard["missing_surface_role_ids"] == ()
    assert guard["blocked_generic_signature_ids"] == ()
    assert guard["generic_surface_blocked"] is False
    assert guard["surface_specificity_missing"] is False
    assert guard["runtime_gate_connected"] is False
    assert guard["display_gate_relaxed"] is False
    assert guard["body_boundary"]["body_free"] is True
    _assert_guard_summary_body_free(summary=guard, case=case, comment_text=comment_text)

    public_meta = _as_mapping(result.get("input_feedback_meta"))
    assert public_meta.get("observation_status") == "passed"
    reply_meta = _as_mapping(captured.get("reply_meta"))
    gate_loop = _as_mapping(reply_meta.get("phase20_5_gate_recovery_loop"))
    assert gate_loop.get("final_observation_status") == "passed"
    assert gate_loop.get("display_gate_relaxed") is False
    assert gate_loop.get("fixed_fallback_used") is False
    assert gate_loop.get("case_specific_route_used") is False
    assert gate_loop.get("case_id_runtime_condition_used") is False
