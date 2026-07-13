# -*- coding: utf-8 -*-
from __future__ import annotations

"""Development-only loader for the frozen Natural Language Surface v2 corpus.

Holdout paths and bodies intentionally do not exist in this module.  Step 3
unit tests may import this helper without opening either independent cohort.
"""

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping


_AI_ROOT = Path(__file__).resolve().parents[2]
DEVELOPMENT_FIXTURE_PATH = (
    _AI_ROOT
    / "tests"
    / "local_only"
    / "emlis_nls_v2_s2_development42_20260713.json"
)

EVALUATION_FAMILIES = (
    "low_information_short",
    "limited_grounding",
    "daily_unpleasant",
    "daily_positive",
    "self_denial",
    "anger_or_boundary",
    "uncertainty_support",
    "standard_state_answer",
    "structure_question",
    "long_meaning_arc",
    "relationship_gratitude_recovery",
    "change_future_intention_transition",
    "source_unavailable_high_information",
    "history_line_eligible_input",
)
APP_VALID_EMOTIONS = frozenset(
    {"喜び", "悲しみ", "怒り", "不安", "平穏", "自己理解"}
)
APP_VALID_CATEGORIES = frozenset(
    {"生活", "仕事", "趣味", "人間関係", "恋愛", "健康", "学習", "価値観", "人生"}
)
DEPTH_ORDER = {"minimal": 0, "focused": 1, "layered": 2}

_CASE_ID_RE = re.compile(r"^NLS2-F(0[1-9]|1[0-4])-D0[1-3]$")
_CODE_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_REQUIRED_CASE_FIELDS = frozenset(
    {
        "case_id",
        "family",
        "current_input",
        "semantic_obligation_codes",
        "forbidden_claim_codes",
        "polarity_contract",
        "topic_separation_codes",
        "response_opportunity_codes",
        "depth_range",
        "safety_boundary_codes",
    }
)
_FORBIDDEN_EXPECTED_FIELDS = frozenset(
    {
        "expected_text",
        "expected_surface",
        "expected_sentence",
        "correct_text",
        "correct_wording",
        "correct_predicate",
        "surface_template",
        "candidate_text",
    }
)


@dataclass(frozen=True)
class EvaluationCase:
    case_id: str
    family: str
    current_input: Mapping[str, Any]
    semantic_obligation_codes: tuple[str, ...]
    forbidden_claim_codes: tuple[str, ...]
    polarity_contract: Mapping[str, Any]
    topic_separation_codes: tuple[str, ...]
    response_opportunity_codes: tuple[str, ...]
    min_depth: str
    max_depth: str
    safety_boundary_codes: tuple[str, ...]


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_json(value: Any) -> str:
    return sha256_bytes(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_codes(case_id: str, field: str, values: Any) -> tuple[str, ...]:
    if not isinstance(values, list) or not values:
        raise ValueError(f"development_case_codes_missing:{case_id}:{field}")
    rows = tuple(str(value) for value in values)
    if len(rows) != len(set(rows)) or any(not _CODE_RE.fullmatch(row) for row in rows):
        raise ValueError(f"development_case_codes_invalid:{case_id}:{field}")
    return rows


def _assert_no_expected_surface_fields(value: Any, *, case_id: str) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key) in _FORBIDDEN_EXPECTED_FIELDS:
                raise ValueError(f"development_expected_surface_forbidden:{case_id}:{key}")
            _assert_no_expected_surface_fields(child, case_id=case_id)
    elif isinstance(value, list):
        for child in value:
            _assert_no_expected_surface_fields(child, case_id=case_id)


def load_development_cases() -> tuple[EvaluationCase, ...]:
    payload = _load_json(DEVELOPMENT_FIXTURE_PATH)
    if payload.get("schema_version") != (
        "cocolon.emlis.nls_v2.evaluation_corpus.development.v1"
    ):
        raise ValueError("development_fixture_schema_mismatch")
    if payload.get("cohort") != "development":
        raise ValueError("development_fixture_cohort_mismatch")
    if payload.get("local_only") is not True:
        raise ValueError("development_fixture_must_be_local_only")
    if payload.get("contains_expected_surface") is not False:
        raise ValueError("development_fixture_expected_surface_flag_invalid")

    raw_cases = payload.get("cases")
    if not isinstance(raw_cases, list) or len(raw_cases) != 42:
        raise ValueError("development_fixture_case_count_invalid")
    if payload.get("case_count") != 42:
        raise ValueError("development_fixture_declared_count_invalid")
    case_order = payload.get("case_order")
    if case_order != [row.get("case_id") for row in raw_cases]:
        raise ValueError("development_fixture_case_order_invalid")

    cases: list[EvaluationCase] = []
    for raw in raw_cases:
        case_id = str(raw.get("case_id") or "")
        if not _CASE_ID_RE.fullmatch(case_id):
            raise ValueError(f"development_case_id_invalid:{case_id}")
        if set(raw) != set(_REQUIRED_CASE_FIELDS):
            raise ValueError(f"development_case_shape_invalid:{case_id}")
        _assert_no_expected_surface_fields(raw, case_id=case_id)

        family = str(raw.get("family") or "")
        if family not in EVALUATION_FAMILIES:
            raise ValueError(f"development_family_invalid:{case_id}:{family}")
        current_input = raw.get("current_input")
        if not isinstance(current_input, dict) or set(current_input) != {
            "memo",
            "memo_action",
            "emotions",
            "category",
        }:
            raise ValueError(f"development_current_input_shape_invalid:{case_id}")
        emotions = tuple(str(item) for item in current_input.get("emotions") or ())
        categories = tuple(str(item) for item in current_input.get("category") or ())
        if not emotions or any(item not in APP_VALID_EMOTIONS for item in emotions):
            raise ValueError(f"development_emotion_not_app_valid:{case_id}")
        if not categories or any(item not in APP_VALID_CATEGORIES for item in categories):
            raise ValueError(f"development_category_not_app_valid:{case_id}")
        if len(emotions) != len(set(emotions)) or len(categories) != len(set(categories)):
            raise ValueError(f"development_option_duplicate:{case_id}")

        depth_range = raw.get("depth_range")
        if not isinstance(depth_range, dict) or set(depth_range) != {"min", "max"}:
            raise ValueError(f"development_depth_range_shape_invalid:{case_id}")
        min_depth = str(depth_range.get("min") or "")
        max_depth = str(depth_range.get("max") or "")
        if (
            min_depth not in DEPTH_ORDER
            or max_depth not in DEPTH_ORDER
            or DEPTH_ORDER[min_depth] > DEPTH_ORDER[max_depth]
        ):
            raise ValueError(f"development_depth_range_invalid:{case_id}")

        polarity = raw.get("polarity_contract")
        if not isinstance(polarity, dict) or set(polarity) != {
            "source",
            "inversion_forbidden",
        }:
            raise ValueError(f"development_polarity_contract_invalid:{case_id}")
        if polarity.get("source") not in {
            "positive",
            "negative",
            "mixed",
            "neutral",
            "uncertain",
        } or polarity.get("inversion_forbidden") is not True:
            raise ValueError(f"development_polarity_contract_invalid:{case_id}")

        cases.append(
            EvaluationCase(
                case_id=case_id,
                family=family,
                current_input={
                    "memo": str(current_input.get("memo") or ""),
                    "memo_action": str(current_input.get("memo_action") or ""),
                    "emotions": list(emotions),
                    "category": list(categories),
                },
                semantic_obligation_codes=_validate_codes(
                    case_id,
                    "semantic_obligation_codes",
                    raw.get("semantic_obligation_codes"),
                ),
                forbidden_claim_codes=_validate_codes(
                    case_id,
                    "forbidden_claim_codes",
                    raw.get("forbidden_claim_codes"),
                ),
                polarity_contract=dict(polarity),
                topic_separation_codes=tuple(
                    str(value) for value in raw.get("topic_separation_codes") or ()
                ),
                response_opportunity_codes=_validate_codes(
                    case_id,
                    "response_opportunity_codes",
                    raw.get("response_opportunity_codes"),
                ),
                min_depth=min_depth,
                max_depth=max_depth,
                safety_boundary_codes=_validate_codes(
                    case_id,
                    "safety_boundary_codes",
                    raw.get("safety_boundary_codes"),
                ),
            )
        )

    identities = [item.case_id for item in cases]
    input_hashes = [sha256_json(item.current_input) for item in cases]
    if len(identities) != len(set(identities)):
        raise ValueError("development_case_id_duplicate")
    if len(input_hashes) != len(set(input_hashes)):
        raise ValueError("development_current_input_duplicate")
    if Counter(item.family for item in cases) != {
        family: 3 for family in EVALUATION_FAMILIES
    }:
        raise ValueError("development_family_distribution_invalid")
    for family in EVALUATION_FAMILIES:
        family_rows = [item for item in cases if item.family == family]
        semantic_shapes = {
            item.semantic_obligation_codes for item in family_rows
        }
        if len(semantic_shapes) != 3:
            raise ValueError(
                f"development_family_semantic_shape_duplicate:{family}"
            )
    return tuple(cases)


__all__ = [
    "DEVELOPMENT_FIXTURE_PATH",
    "EVALUATION_FAMILIES",
    "APP_VALID_EMOTIONS",
    "APP_VALID_CATEGORIES",
    "DEPTH_ORDER",
    "EvaluationCase",
    "sha256_bytes",
    "sha256_file",
    "sha256_json",
    "load_development_cases",
]
