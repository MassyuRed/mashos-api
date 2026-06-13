# -*- coding: utf-8 -*-
"""Shared P7 Product Quality Runner contract helpers.

P7 starts after the P5/P6 runtime-repair handoff, but it must not convert that
handoff into product readiness.  These helpers keep the first P7 materials
body-free and release-closed: they reject raw input, ``comment_text`` bodies,
candidate/surface bodies, terminal output, public contract mutations, and
release flags.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Final

P7_PHASE: Final = "P7_ProductQualityRunner_LongRunGate"
P7_IMPLEMENTATION_STEP: Final = "P7-0_P7-1_ProductQualityRunner_20260612"
P7_SOURCE_MODE: Final = "local_snapshot"
P7_GIT_CHECKED: Final = False
P7_HANDOFF_SUMMARY_SCHEMA_VERSION: Final = "cocolon.emlis.p7.handoff_summary.v1"
P7_RED_LEDGER_SCHEMA_VERSION: Final = "cocolon.emlis.p7.red_ledger.v1"
P7_BLOCKER_REGISTRY_SCHEMA_VERSION: Final = "cocolon.emlis.p7.blocker_registry.v1"

P7_INITIAL_RED_IDS: Final[tuple[str, ...]] = ("P7-RED-001", "P7-RED-002", "P7-RED-003")
P7_INITIAL_HOLD_IDS: Final[tuple[str, ...]] = (
    "P7-HOLD-001",
    "P7-HOLD-002",
    "P7-HOLD-003",
    "P7-HOLD-004",
)
P7_INITIAL_OUT_OF_SCOPE_IDS: Final[tuple[str, ...]] = (
    "P7-OUT-001",
    "P7-OUT-002",
    "P7-OUT-003",
    "P7-OUT-004",
    "P7-OUT-005",
    "P7-OUT-006",
    "P7-OUT-007",
    "P7-OUT-008",
)

P7_DEFAULT_LOCAL_FILES: Final[tuple[str, ...]] = (
    "Cocolon_前提資料(205).zip",
    "EmlisAIの実装済み資料(56).zip",
    "Cocolon_EmlisAI_P7_ProductQualityRunner_DetailedDesign_ImplementationOrder_20260612(1).md",
    "Cocolon(227).zip",
    "mashos-api(140).zip",
)

P7_PUBLIC_CONTRACT_KEYS: Final[tuple[str, ...]] = (
    "rn_visible_contract_changed",
    "api_response_key_added",
    "db_schema_changed",
    "public_release_applied",
)
P7_BODY_FREE_MARKER_KEYS: Final[tuple[str, ...]] = (
    "raw_input_included",
    "history_raw_text_included",
    "comment_text_body_included",
    "candidate_body_included",
    "surface_body_included",
)
P7_RED_LEDGER_BODY_FREE_MARKER_KEYS: Final[tuple[str, ...]] = (
    "raw_input_included",
    "comment_text_body_included",
    "candidate_body_included",
    "surface_body_included",
    "reviewer_free_text_included",
)

P7_FORBIDDEN_BODY_KEYS: Final[frozenset[str]] = frozenset(
    {
        "raw_input",
        "rawInput",
        "raw_text",
        "rawText",
        "source_text",
        "sourceText",
        "input",
        "input_text",
        "inputText",
        "user_input",
        "userInput",
        "current_input",
        "currentInput",
        "history_context",
        "historyContext",
        "history_records",
        "historyRecords",
        "history_raw_text",
        "historyRawText",
        "memo",
        "memo_text",
        "memoText",
        "memo_action",
        "memoAction",
        "thought_text",
        "thoughtText",
        "action_text",
        "actionText",
        "comment_text",
        "commentText",
        "comment_text_body",
        "commentTextBody",
        "comment_body",
        "commentBody",
        "input_feedback_comment",
        "public_comment_text",
        "candidate_comment_text",
        "reply_text",
        "replyText",
        "surface_text",
        "surfaceText",
        "visible_text",
        "visibleText",
        "realized_text",
        "realizedText",
        "display_text",
        "displayText",
        "observation_text",
        "reception_text",
        "candidate_body",
        "candidateBody",
        "surface_body",
        "surfaceBody",
        "reviewer_free_text",
        "reviewer_note",
        "reviewer_notes",
        "terminal_output",
        "stdout",
        "stderr",
        "traceback",
        "body",
        "text",
    }
)

P7_FORBIDDEN_TRUE_FLAGS: Final[frozenset[str]] = frozenset(
    {
        "api_route_changed",
        "request_key_changed",
        "response_shape_changed",
        "public_response_key_added",
        "public_response_key_change",
        "api_response_key_added",
        "db_schema_changed",
        "db_physical_name_changed",
        "rn_visible_contract_changed",
        "rn_visible_title_changed",
        "display_gate_relaxed",
        "grounding_gate_relaxed",
        "reader_gate_relaxed",
        "template_gate_relaxed",
        "runtime_surface_gate_relaxed",
        "visible_surface_gate_relaxed",
        "gate_relaxed",
        "raw_input_included",
        "raw_text_included",
        "history_raw_text_included",
        "comment_text_included",
        "comment_text_body_included",
        "candidate_body_included",
        "surface_body_included",
        "reviewer_free_text_included",
        "terminal_output_included",
        "p7_ready",
        "product_gate_ready",
        "product_gate_reached",
        "product_gate_public_release_applied",
        "public_release_applied",
        "release_allowed",
        "release_decision_applied",
        "product_quality_released",
        "product_pass_promoted_to_release_ready",
        "fixed_sentence_template_added",
        "fixed_sentence_template_used",
        "input_specific_template_added",
        "runtime_fixture_branch_added",
        "machine_metrics_used_for_read_feeling",
        "read_feeling_auto_filled_from_machine_metrics",
        "read_feeling_auto_estimation_allowed",
        "external_ai_used",
        "local_llm_used",
    }
)


def clean_identifier(value: Any, *, default: str = "", max_length: int = 160) -> str:
    """Return a compact identifier string, not free text."""

    if value is None or isinstance(value, (Mapping, list, tuple, set)):
        return default
    text = str(value).strip()[:max_length]
    return text or default


def safe_mapping(value: Any) -> dict[str, Any]:
    return {str(key): item for key, item in value.items()} if isinstance(value, Mapping) else {}


def listify(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (str, bytes, bytearray)):
        return [value]
    if isinstance(value, Mapping):
        return list(value.values())
    if isinstance(value, Iterable):
        return list(value)
    return [value]


def dedupe_identifiers(values: Iterable[Any] | Any | None, *, limit: int = 40, max_length: int = 160) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in listify(values):
        text = clean_identifier(value, max_length=max_length)
        if text and text not in seen:
            seen.add(text)
            out.append(text)
        if len(out) >= limit:
            break
    return out


def body_free_flags(*, include_history: bool = True, include_reviewer: bool = False, include_terminal: bool = False) -> dict[str, bool]:
    keys = [
        "raw_input_included",
        "comment_text_body_included",
        "candidate_body_included",
        "surface_body_included",
    ]
    if include_history:
        keys.insert(1, "history_raw_text_included")
    if include_reviewer:
        keys.append("reviewer_free_text_included")
    if include_terminal:
        keys.append("terminal_output_included")
    return {key: False for key in keys}


def public_contract_flags() -> dict[str, bool]:
    return {key: False for key in P7_PUBLIC_CONTRACT_KEYS}


def contains_forbidden_body_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in P7_FORBIDDEN_BODY_KEYS:
                return True
            if contains_forbidden_body_key(child):
                return True
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(contains_forbidden_body_key(child) for child in value)
    return False


def forbidden_true_flag_paths(value: Any, *, path: str = "payload") -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if str(key) in P7_FORBIDDEN_TRUE_FLAGS and child is True:
                paths.append(child_path)
            paths.extend(forbidden_true_flag_paths(child, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            paths.extend(forbidden_true_flag_paths(child, path=f"{path}[{index}]"))
    return paths


def assert_p7_no_body_payload_or_contract_mutation(value: Any, *, source: str) -> None:
    if contains_forbidden_body_key(value):
        raise ValueError(f"{source} contains a forbidden body payload key")
    true_flags = forbidden_true_flag_paths(value, path=source)
    if true_flags:
        raise ValueError(f"{source} contains forbidden true flags: {', '.join(true_flags[:6])}")


def assert_false_markers(markers: Mapping[str, Any], *, source: str) -> None:
    if not isinstance(markers, Mapping):
        raise ValueError(f"{source} must be a mapping")
    true_keys = [str(key) for key, value in markers.items() if value is True]
    if true_keys:
        raise ValueError(f"{source} must keep all body-free/public-contract markers false: {true_keys}")
