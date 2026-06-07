# -*- coding: utf-8 -*-
from __future__ import annotations

"""Body-free question-dominance guard for reception-required EmlisAI surfaces.

The helper inspects public ``comment_text`` only to derive structural booleans.
It never returns raw text, section bodies, or user input material. Product
surface validation uses this to keep limited-grounding and true low-information
surfaces from becoming question-led input prompts.
"""

from collections.abc import Mapping, Sequence
from typing import Any, Final
import json
import re

QUESTION_DOMINANCE_GUARD_SCHEMA_VERSION: Final = "cocolon.emlis.question_dominance_guard.v1"
QUESTION_DOMINANCE_GUARD_SOURCE_PHASE: Final = "ReceptionRequiredSurface_QuestionDominanceGuard"

QUESTION_DOMINANCE_BLOCKER_NONE: Final = ""
QUESTION_DOMINANCE_BLOCKER_RECEPTION_SECTION_MISSING: Final = "product_surface_invalid_reception_section_missing"
QUESTION_DOMINANCE_BLOCKER_QUESTION_DOMINANT_SURFACE: Final = "product_surface_invalid_question_dominant_surface"
QUESTION_DOMINANCE_BLOCKER_QUESTION_BEFORE_RECEPTION: Final = "product_surface_invalid_question_before_reception"
QUESTION_DOMINANCE_BLOCKER_QUESTION_ONLY_SURFACE: Final = "product_surface_invalid_question_only_surface"
QUESTION_DOMINANCE_BLOCKER_REQUIRED_QUESTION_MISSING: Final = "product_surface_invalid_surface_requirement_unsatisfied"

QUESTION_GUARD_VALID: Final = "question_dominance_guard_valid"
QUESTION_GUARD_BLOCKER_RECEPTION_SECTION_MISSING: Final = QUESTION_DOMINANCE_BLOCKER_RECEPTION_SECTION_MISSING
QUESTION_GUARD_BLOCKER_QUESTION_DOMINANT_SURFACE: Final = QUESTION_DOMINANCE_BLOCKER_QUESTION_DOMINANT_SURFACE
QUESTION_GUARD_BLOCKER_QUESTION_BEFORE_RECEPTION: Final = QUESTION_DOMINANCE_BLOCKER_QUESTION_BEFORE_RECEPTION
QUESTION_GUARD_BLOCKER_QUESTION_ONLY_SURFACE: Final = QUESTION_DOMINANCE_BLOCKER_QUESTION_ONLY_SURFACE

_OBSERVATION_LABEL: Final = "見えたこと："
_RECEPTION_LABEL: Final = "Emlisから："
_RECEPTION_BOUNDARY: Final = f"\n\n{_RECEPTION_LABEL}\n"
_QUESTION_PROMPT_RE: Final = re.compile(
    r"(詳しく残せそうなら[^。！？!?]*残してみませんか"
    r"|詳しくできそうなら[^。！？!?]*足して[^。！？!?]*"
    r"|何があったか[^。！？!?]*残してみませんか"
    r"|何が変わったのか[^。！？!?]*残してみませんか"
    r"|残してみませんか"
    r"|足してみませんか"
    r"|教えてください"
    r"|聞かせてください"
    r"|ありますか"
    r"|できますか"
    r"|でしょうか"
    r"|ですか"
    r"|[？?])"
)
_SENTENCE_RE: Final = re.compile(r"[^。！？!?\n]+[。！？!?]?")
_ALLOWED_BLOCKER_CODES: Final[frozenset[str]] = frozenset(
    {
        QUESTION_DOMINANCE_BLOCKER_NONE,
        QUESTION_DOMINANCE_BLOCKER_RECEPTION_SECTION_MISSING,
        QUESTION_DOMINANCE_BLOCKER_QUESTION_DOMINANT_SURFACE,
        QUESTION_DOMINANCE_BLOCKER_QUESTION_BEFORE_RECEPTION,
        QUESTION_DOMINANCE_BLOCKER_QUESTION_ONLY_SURFACE,
        QUESTION_DOMINANCE_BLOCKER_REQUIRED_QUESTION_MISSING,
    }
)
_SUMMARY_KEYS: Final[frozenset[str]] = frozenset(
    {
        "schema_version",
        "source_phase",
        "target_surface_family",
        "material_quality_family",
        "checked",
        "passed",
        "question_required",
        "observation_section_present",
        "reception_section_present",
        "question_surface_present",
        "question_before_reception",
        "question_after_reception",
        "starts_with_question_prompt",
        "question_only_surface",
        "question_sentence_count",
        "non_question_sentence_count",
        "question_dominant",
        "blocker_code",
        "body_free",
        "raw_input_included",
        "comment_text_body_included",
    }
)
_BODY_FORBIDDEN_EXACT_KEYS: Final[frozenset[str]] = frozenset(
    {
        "raw_input", "rawInput", "raw_text", "rawText", "input_text", "inputText",
        "user_input", "userInput", "current_input", "currentInput", "memo",
        "memo_text", "memoText", "memo_action", "memoAction", "comment_text",
        "commentText", "comment_text_body", "commentTextBody", "candidate_comment_text",
        "candidateCommentText", "public_comment_text", "publicCommentText", "observation_text",
        "observationText", "reception_text", "receptionText", "evidence_text",
        "evidenceText", "body", "text", "candidate_body", "candidateBody", "surface_body",
        "surfaceBody", "surface_text", "surfaceText",
    }
)


def build_question_dominance_guard_summary(
    comment_text: Any = "",
    *,
    target_surface_family: Any = "",
    surface_requirement_family: Any = "",
    material_quality: Any = "",
    material_quality_family: Any = "",
    question_required: bool = False,
    checked: bool | None = None,
    reception_required: bool | None = None,
) -> dict[str, Any]:
    """Return a body-free question dominance summary for a public surface."""

    raw = str(comment_text or "").replace("\r\n", "\n").replace("\r", "\n")
    should_check = bool(reception_required) if reception_required is not None else bool(True if checked is None else checked)
    surface_family = _clean_identifier(target_surface_family or surface_requirement_family, max_length=96)
    quality = _clean_identifier(material_quality or material_quality_family, max_length=96)
    should_check = bool(checked if checked is not None else (reception_required if reception_required is not None else True))

    observation_section, reception_section = _sections(raw)
    body_without_labels = _remove_labels(raw)
    question_sentence_count, non_question_sentence_count = _sentence_counts(body_without_labels)
    first_question_index = _first_question_index(raw)
    boundary_index = raw.find(_RECEPTION_BOUNDARY)
    question_before_reception = bool(
        first_question_index >= 0 and (boundary_index < 0 or first_question_index < boundary_index)
    )
    question_after_reception = bool(
        first_question_index >= 0 and boundary_index >= 0 and first_question_index > boundary_index
    )
    starts_with_question_prompt = bool(
        _starts_with_question_prompt(raw)
        or _starts_with_question_prompt(observation_section)
        or _starts_with_question_prompt(reception_section)
    )
    question_surface_present = bool(question_sentence_count > 0 or first_question_index >= 0)
    observation_present = bool(observation_section.strip())
    reception_present = bool(reception_section.strip())
    question_only_surface = bool(question_surface_present and non_question_sentence_count <= 0)
    question_dominant = bool(
        starts_with_question_prompt
        or question_only_surface
        or (question_sentence_count > 0 and question_sentence_count > non_question_sentence_count)
    )

    blocker_code = QUESTION_DOMINANCE_BLOCKER_NONE
    passed = True
    if should_check:
        if not observation_present or not reception_present:
            blocker_code = QUESTION_DOMINANCE_BLOCKER_RECEPTION_SECTION_MISSING
            passed = False
        elif question_before_reception:
            blocker_code = QUESTION_DOMINANCE_BLOCKER_QUESTION_BEFORE_RECEPTION
            passed = False
        elif question_only_surface:
            blocker_code = QUESTION_DOMINANCE_BLOCKER_QUESTION_ONLY_SURFACE
            passed = False
        elif question_dominant:
            blocker_code = QUESTION_DOMINANCE_BLOCKER_QUESTION_DOMINANT_SURFACE
            passed = False
        elif question_required and not question_after_reception:
            blocker_code = QUESTION_DOMINANCE_BLOCKER_REQUIRED_QUESTION_MISSING
            passed = False

    summary = {
        "schema_version": QUESTION_DOMINANCE_GUARD_SCHEMA_VERSION,
        "source_phase": QUESTION_DOMINANCE_GUARD_SOURCE_PHASE,
        "target_surface_family": surface_family,
        "material_quality_family": quality,
        "checked": bool(should_check),
        "passed": bool(passed),
        "question_required": bool(question_required),
        "observation_section_present": observation_present,
        "reception_section_present": reception_present,
        "question_surface_present": question_surface_present,
        "question_before_reception": question_before_reception,
        "question_after_reception": question_after_reception,
        "starts_with_question_prompt": starts_with_question_prompt,
        "question_only_surface": question_only_surface,
        "question_sentence_count": int(question_sentence_count),
        "non_question_sentence_count": int(non_question_sentence_count),
        "question_dominant": question_dominant,
        "blocker_code": blocker_code,
        "body_free": True,
        "raw_input_included": False,
        "comment_text_body_included": False,
    }
    assert_question_dominance_guard_summary(summary)
    return summary


def question_dominance_guard_public_summary(value: Mapping[str, Any] | None) -> dict[str, Any]:
    source = _as_mapping(value)
    if not source:
        return {}
    payload = {
        "schema_version": _clean_identifier(source.get("schema_version"), max_length=128)
        or QUESTION_DOMINANCE_GUARD_SCHEMA_VERSION,
        "source_phase": _clean_identifier(source.get("source_phase"), max_length=128)
        or QUESTION_DOMINANCE_GUARD_SOURCE_PHASE,
        "target_surface_family": _clean_identifier(source.get("target_surface_family"), max_length=96),
        "material_quality_family": _clean_identifier(source.get("material_quality_family"), max_length=96),
        "checked": bool(source.get("checked")),
        "passed": bool(source.get("passed")),
        "question_required": bool(source.get("question_required")),
        "observation_section_present": bool(source.get("observation_section_present")),
        "reception_section_present": bool(source.get("reception_section_present")),
        "question_surface_present": bool(source.get("question_surface_present")),
        "question_before_reception": bool(source.get("question_before_reception")),
        "question_after_reception": bool(source.get("question_after_reception")),
        "starts_with_question_prompt": bool(source.get("starts_with_question_prompt")),
        "question_only_surface": bool(source.get("question_only_surface")),
        "question_sentence_count": _safe_int(source.get("question_sentence_count")),
        "non_question_sentence_count": _safe_int(source.get("non_question_sentence_count")),
        "question_dominant": bool(source.get("question_dominant")),
        "blocker_code": _clean_identifier(source.get("blocker_code"), max_length=128),
        "body_free": True,
        "raw_input_included": False,
        "comment_text_body_included": False,
    }
    assert_question_dominance_guard_summary(payload)
    return payload


def assert_question_dominance_guard_summary(value: Any) -> None:
    if not isinstance(value, Mapping):
        raise ValueError("question dominance guard summary must be a mapping")
    actual = set(value.keys())
    if actual != set(_SUMMARY_KEYS):
        raise ValueError(
            "question dominance guard key set changed: "
            f"missing={sorted(set(_SUMMARY_KEYS) - actual)} "
            f"extra={sorted(actual - set(_SUMMARY_KEYS))}"
        )
    if value.get("schema_version") != QUESTION_DOMINANCE_GUARD_SCHEMA_VERSION:
        raise ValueError("unexpected question dominance guard schema_version")
    if value.get("source_phase") != QUESTION_DOMINANCE_GUARD_SOURCE_PHASE:
        raise ValueError("unexpected question dominance guard source_phase")
    for key in (
        "checked", "passed", "question_required", "observation_section_present",
        "reception_section_present", "question_surface_present", "question_before_reception",
        "question_after_reception", "starts_with_question_prompt", "question_only_surface",
        "question_dominant", "body_free", "raw_input_included", "comment_text_body_included",
    ):
        if not isinstance(value.get(key), bool):
            raise ValueError(f"question_dominance_guard.{key} must be boolean")
    for key in ("question_sentence_count", "non_question_sentence_count"):
        if not isinstance(value.get(key), int) or value.get(key) < 0:
            raise ValueError(f"question_dominance_guard.{key} must be non-negative int")
    if value.get("blocker_code") not in _ALLOWED_BLOCKER_CODES:
        raise ValueError("unknown question dominance blocker code")
    if value.get("body_free") is not True:
        raise ValueError("question dominance guard summary must be body-free")
    if value.get("raw_input_included") is not False or value.get("comment_text_body_included") is not False:
        raise ValueError("question dominance guard summary must not include raw/comment text")
    _assert_no_forbidden_body_keys(value)
    json.dumps(dict(value), ensure_ascii=False, sort_keys=True)


def _sections(raw: str) -> tuple[str, str]:
    if _RECEPTION_BOUNDARY not in raw:
        return (_remove_observation_label(raw), "")
    before, after = raw.split(_RECEPTION_BOUNDARY, 1)
    return (_remove_observation_label(before), after.strip())


def _remove_observation_label(text: str) -> str:
    value = str(text or "").strip()
    if value.startswith(f"{_OBSERVATION_LABEL}\n"):
        return value[len(f"{_OBSERVATION_LABEL}\n"):].strip()
    if value.startswith(_OBSERVATION_LABEL):
        return value[len(_OBSERVATION_LABEL):].strip()
    return value


def _remove_labels(text: str) -> str:
    value = str(text or "")
    value = value.replace(f"{_OBSERVATION_LABEL}\n", "")
    value = value.replace(_OBSERVATION_LABEL, "")
    value = value.replace(_RECEPTION_BOUNDARY, "\n")
    value = value.replace(f"{_RECEPTION_LABEL}\n", "")
    value = value.replace(_RECEPTION_LABEL, "")
    return value.strip()


def _first_question_index(text: str) -> int:
    match = _QUESTION_PROMPT_RE.search(text or "")
    return match.start() if match else -1


def _starts_with_question_prompt(text: str) -> bool:
    value = _remove_labels(text).strip()
    if not value:
        return False
    match = _QUESTION_PROMPT_RE.search(value)
    return bool(match and match.start() <= 2)


def _sentence_counts(text: str) -> tuple[int, int]:
    question_count = 0
    non_question_count = 0
    for sentence in _sentences(text):
        if _QUESTION_PROMPT_RE.search(sentence):
            question_count += 1
        else:
            non_question_count += 1
    return question_count, non_question_count


def _sentences(text: str) -> list[str]:
    cleaned = _remove_labels(text)
    if not cleaned:
        return []
    parts = [match.group(0).strip() for match in _SENTENCE_RE.finditer(cleaned)]
    return [part for part in parts if part and part not in {_OBSERVATION_LABEL, _RECEPTION_LABEL}]


def _as_mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _clean_identifier(value: Any, *, max_length: int = 160) -> str:
    return str(value or "").strip().replace(" ", "_")[:max_length]


def _safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _assert_no_forbidden_body_keys(value: Any) -> None:
    if isinstance(value, Mapping):
        forbidden = set(value.keys()) & _BODY_FORBIDDEN_EXACT_KEYS
        if forbidden:
            raise ValueError(f"question dominance summary contains body-like key(s): {sorted(forbidden)}")
        for child in value.values():
            _assert_no_forbidden_body_keys(child)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for item in value:
            _assert_no_forbidden_body_keys(item)


__all__ = [
    "QUESTION_DOMINANCE_BLOCKER_NONE",
    "QUESTION_DOMINANCE_BLOCKER_QUESTION_BEFORE_RECEPTION",
    "QUESTION_DOMINANCE_BLOCKER_QUESTION_DOMINANT_SURFACE",
    "QUESTION_DOMINANCE_BLOCKER_QUESTION_ONLY_SURFACE",
    "QUESTION_DOMINANCE_BLOCKER_RECEPTION_SECTION_MISSING",
    "QUESTION_DOMINANCE_BLOCKER_REQUIRED_QUESTION_MISSING",
    "QUESTION_DOMINANCE_GUARD_SCHEMA_VERSION",
    "QUESTION_DOMINANCE_GUARD_SOURCE_PHASE",
    "QUESTION_GUARD_BLOCKER_QUESTION_BEFORE_RECEPTION",
    "QUESTION_GUARD_BLOCKER_QUESTION_DOMINANT_SURFACE",
    "QUESTION_GUARD_BLOCKER_QUESTION_ONLY_SURFACE",
    "QUESTION_GUARD_BLOCKER_RECEPTION_SECTION_MISSING",
    "QUESTION_GUARD_VALID",
    "assert_question_dominance_guard_summary",
    "build_question_dominance_guard_summary",
    "question_dominance_guard_public_summary",
]
