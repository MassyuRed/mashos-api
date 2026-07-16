# -*- coding: utf-8 -*-
from __future__ import annotations

"""Strict Step 2 sample contract, duplicate policy, and corpus registry.

This module is local evaluation tooling.  It does not import any production
surface owner, stopped NLS v2 module, RN implementation, or reply service.
"""

from collections import Counter
from copy import deepcopy
from difflib import SequenceMatcher
import hashlib
import hmac
import json
from pathlib import Path
import re
from typing import Any, Callable, Iterable, Mapping, Sequence
import unicodedata


_AI_ROOT = Path(__file__).resolve().parents[2]
_REPO_ROOT = _AI_ROOT.parent
_TEST_ROOT = _AI_ROOT / "tests"
_SCHEMA_ROOT = _TEST_ROOT / "schemas"
_FIXTURE_ROOT = _TEST_ROOT / "fixtures"

SAMPLE_SCHEMA_PATH = _SCHEMA_ROOT / "emlis_nls_v3_sample_case_v1.schema.json"
COVERAGE_SCHEMA_PATH = _SCHEMA_ROOT / "emlis_nls_v3_coverage_matrix_v1.schema.json"
BATCH_MANIFEST_SCHEMA_PATH = (
    _SCHEMA_ROOT / "emlis_nls_v3_sample_batch_manifest_v1.schema.json"
)
CORPUS_REGISTRY_SCHEMA_PATH = (
    _SCHEMA_ROOT / "emlis_nls_v3_corpus_registry_v1.schema.json"
)
VALID_FIXTURE_PATH = (
    _FIXTURE_ROOT / "emlis_nls_v3" / "contract" / "valid_v1.jsonl"
)
INVALID_FIXTURE_PATH = (
    _FIXTURE_ROOT / "emlis_nls_v3" / "contract" / "invalid_v1.jsonl"
)
LEGACY_FIXTURE_PATH = (
    _FIXTURE_ROOT / "emlis_nls_v3" / "contract" / "legacy_v1.jsonl"
)
REGISTRY_PATH = _FIXTURE_ROOT / "emlis_nls_v3_s2_corpus_registry_20260714.json"
STEP2_TEST_PATH = _TEST_ROOT / "test_emlis_nls_v3_s2_sample_registry.py"
STEP1_RECEIPT_PATH = _FIXTURE_ROOT / "emlis_nls_v3_s1_baseline_receipt_20260714.json"
STEP1_INPUT_CONTRACT_PATH = (
    _FIXTURE_ROOT / "emlis_nls_v3_s1_input_contract_20260714.json"
)

DESIGN_SHA256 = "6aa3fb799919ac30b0eb84571ac4009d62a2bd799c84322272a59bba533f13bc"
STEP1_RECEIPT_SHA256 = "669835b0fdce3bc1e2e897325ab37b5f82abc9a353bc864993aa284083b7a518"
STEP1_INPUT_CONTRACT_SHA256 = (
    "d577ac80457e25389c0bac351139b2c80a9a506f225023fb7928a1b9068d53c6"
)

SAMPLE_SCHEMA_VERSION = "cocolon.emlis.nls_v3.sample_case.v1"
COVERAGE_SCHEMA_VERSION = "cocolon.emlis.nls_v3.coverage_matrix.v1"
BATCH_MANIFEST_SCHEMA_VERSION = (
    "cocolon.emlis.nls_v3.sample_batch_manifest.v1"
)
CORPUS_REGISTRY_SCHEMA_VERSION = "cocolon.emlis.nls_v3.corpus_registry.v1"

EMOTION_TYPES = ("喜び", "悲しみ", "怒り", "不安", "平穏", "自己理解")
STRENGTH_TYPES = ("weak", "medium", "strong")
CATEGORY_TYPES = (
    "生活",
    "仕事",
    "趣味",
    "人間関係",
    "恋愛",
    "健康",
    "学習",
    "価値観",
    "人生",
)
SOURCE_TYPES = (
    "karen_generated",
    "other_ai_generated_reviewed",
    "real_user_anonymized_private",
)
SHAREABLE_SYNTHETIC_SOURCES = (
    "karen_generated",
    "other_ai_generated_reviewed",
)
COVERAGE_FAMILIES = (
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
    "history_eligible_current_input_only",
)
DEPTH_LEVELS = ("minimal", "focused", "layered")

_COVERAGE_ENUMS: dict[str, tuple[str, ...]] = {
    "category_cardinality": ("single", "multiple"),
    "category_text_alignment": ("strong", "weak"),
    "cause_explicitness": ("explicit", "unknown"),
    "emotion_cardinality": ("single", "multiple", "self_insight_only"),
    "emotion_strength_shape": (
        "single_strength",
        "mixed_strength",
        "self_insight_medium",
    ),
    "families": COVERAGE_FAMILIES,
    "input_field_presence": ("thought_only", "action_only", "both"),
    "intention_state": ("none", "explicit", "uncertain", "completed"),
    "length_class": ("short", "medium", "long", "very_long"),
    "question_system_relevance": (
        "not_needed",
        "possible",
        "burden_risk",
        "future_refined_candidate",
    ),
    "referent_clarity": ("clear", "multiple_candidates", "omitted"),
    "surface_shape": (
        "complete_sentence",
        "fragment",
        "colloquial",
        "colloquial_fragment",
        "typo_or_orthographic_variation",
        "truncated",
    ),
    "temporal_scope": ("past", "current", "future_intention", "mixed"),
    "thought_action_relation": (
        "not_applicable",
        "same",
        "complement",
        "contrast",
        "time_shift",
        "cause_unknown",
    ),
    "topic_cardinality": ("single", "multiple"),
    "valence": ("positive", "negative", "mixed", "neutral", "self_denial_adjacent"),
}
STRUCTURAL_VARIATION_KEYS = (
    "merge_split_eligible",
    "minimal_single_structure_expected",
    "order_variation_eligible",
    "reception_position_variation_eligible",
)

_SAMPLE_KEYS = frozenset(
    {"schema_version", "case_id", "batch_id", "source", "input", "semantic_contract", "coverage"}
)
_INPUT_KEYS = frozenset({"thought_text", "action_text", "emotions", "categories"})
_EMOTION_KEYS = frozenset({"type", "strength"})
_SEMANTIC_KEYS = frozenset(
    {
        "required_meaning_codes",
        "forbidden_claim_codes",
        "relation_codes",
        "unknown_codes",
        "expected_depth_range",
    }
)
_COVERAGE_KEYS = frozenset({*_COVERAGE_ENUMS, "structural_variation"})
_CODE_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,63}$")
_CASE_ID_RE = re.compile(r"^nls3s_b([0-9]{3})_[0-9]{4}$")
_BATCH_ID_RE = re.compile(r"^nls3_batch_([0-9]{3})$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

# ECMAScript WhiteSpace + LineTerminator used by JavaScript String.trim().
# Deliberately excludes Python-only whitespace such as U+0085 and U+001C..U+001F.
_ECMASCRIPT_TRIM_CODEPOINTS = frozenset(
    {
        0x0009,
        0x000A,
        0x000B,
        0x000C,
        0x000D,
        0x0020,
        0x00A0,
        0x1680,
        0x2000,
        0x2001,
        0x2002,
        0x2003,
        0x2004,
        0x2005,
        0x2006,
        0x2007,
        0x2008,
        0x2009,
        0x200A,
        0x2028,
        0x2029,
        0x202F,
        0x205F,
        0x3000,
        0xFEFF,
    }
)

VALIDATOR_POLICY = {
    "schema_version": "cocolon.emlis.nls_v3.app_reachable_input_policy.v1",
    "authority": "step1_frozen_current_rn_production_contract",
    "step1_input_contract_sha256": STEP1_INPUT_CONTRACT_SHA256,
    "text_presence": "ecmascript_string_trim_thought_or_action_nonempty",
    "text_length_limit": None,
    "emotion_types": list(EMOTION_TYPES),
    "strength_types": list(STRENGTH_TYPES),
    "emotion_unique": True,
    "self_insight_exclusive": True,
    "self_insight_strength": "medium",
    "category_types": list(CATEGORY_TYPES),
    "category_unique": True,
    "backend_permissiveness_is_app_reachable_authority": False,
}

DUPLICATE_POLICY = {
    "schema_version": "cocolon.emlis.nls_v3.duplicate_policy.v1",
    "exact_identity": "canonical_untouched_input_json_array_order_preserved",
    "normalized_identity": "nfkc_ecmascript_trim_collapse_lf_emotion_category_rn_order",
    "near_similarity": "max_bidirectional_sequence_matcher_and_character_bigram_dice",
    "near_threshold_basis_points": 7600,
    "near_minimum_text_characters": 12,
    "near_requires_same_field_presence": True,
    "precedence": ["exact", "normalized", "near"],
    "near_result": "review_flag_never_silent_merge",
    "case_id_batch_source_annotations_in_identity": False,
    "maximum_pair_comparisons": 150000,
    "maximum_total_normalized_text_characters": 10000000,
    "resource_budget_result": "novelty_check_indeterminate_freeze_forbidden",
}


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_json_text(value: Any) -> str:
    return canonical_json_bytes(value).decode("utf-8")


def strict_json_equal(left: Any, right: Any) -> bool:
    """Compare JSON values without Python's bool/int equality coercion."""

    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return set(left) == set(right) and all(
            strict_json_equal(left[key], right[key]) for key in left
        )
    if isinstance(left, list):
        return len(left) == len(right) and all(
            strict_json_equal(left_item, right_item)
            for left_item, right_item in zip(left, right)
        )
    return bool(left == right)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_json(value: Any) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


VALIDATOR_POLICY_SHA256 = sha256_json(VALIDATOR_POLICY)
DUPLICATE_POLICY_SHA256 = sha256_json(DUPLICATE_POLICY)


def _validator_policy_binding_issue() -> str | None:
    try:
        return (
            None
            if sha256_json(VALIDATOR_POLICY) == VALIDATOR_POLICY_SHA256
            else "validator_policy_hash_drift"
        )
    except (TypeError, ValueError, OverflowError):
        return "validator_policy_not_canonical_json"


def _duplicate_policy_binding_issue() -> str | None:
    try:
        return (
            None
            if sha256_json(DUPLICATE_POLICY) == DUPLICATE_POLICY_SHA256
            else "duplicate_policy_hash_drift"
        )
    except (TypeError, ValueError, OverflowError):
        return "duplicate_policy_not_canonical_json"


def policy_binding_issues() -> tuple[str, ...]:
    """Detect in-process mutation of the version-frozen Step 2 policies."""

    return tuple(
        issue
        for issue in (
            _validator_policy_binding_issue(),
            _duplicate_policy_binding_issue(),
        )
        if issue is not None
    )


def _require_frozen_policy_bindings() -> None:
    issues = policy_binding_issues()
    if issues:
        raise ValueError("frozen_policy_binding_invalid:" + issues[0])


def _exact_keys(value: Any, expected: frozenset[str]) -> bool:
    return isinstance(value, Mapping) and set(value) == expected


def _has_lone_surrogate(value: str) -> bool:
    return any(0xD800 <= ord(char) <= 0xDFFF for char in value)


def _valid_scalar_text(value: Any) -> bool:
    return isinstance(value, str) and not _has_lone_surrogate(value)


def ecmascript_trim(value: str) -> str:
    """Mirror JavaScript String.trim() for the frozen RN submit contract."""

    start = 0
    end = len(value)
    while start < end and ord(value[start]) in _ECMASCRIPT_TRIM_CODEPOINTS:
        start += 1
    while end > start and ord(value[end - 1]) in _ECMASCRIPT_TRIM_CODEPOINTS:
        end -= 1
    return value[start:end]


def _issue(path: str, code: str) -> str:
    return f"{path}:{code}"


def _safe_relative_artifact_ref(value: Any) -> bool:
    if not isinstance(value, str) or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,255}", value) is None:
        return False
    if "//" in value or "\\" in value or ":" in value or "~" in value:
        return False
    path = Path(value)
    return not path.is_absolute() and all(
        part not in {"", ".", ".."} for part in value.split("/")
    )


def _repo_ref(path: Path) -> str:
    resolved = path.resolve()
    try:
        value = resolved.relative_to(_REPO_ROOT.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError("artifact_path_outside_repo_root") from exc
    if not _safe_relative_artifact_ref(value):
        raise ValueError("artifact_repo_ref_unsafe")
    return value


def validate_app_reachable_input(value: Any) -> tuple[str, ...]:
    issues: list[str] = []
    policy_issue = _validator_policy_binding_issue()
    if policy_issue is not None:
        return (_issue("input.policy", policy_issue),)
    if not _exact_keys(value, _INPUT_KEYS):
        return (_issue("input", "keyset_mismatch"),)

    thought = value.get("thought_text")
    action = value.get("action_text")
    if not _valid_scalar_text(thought):
        issues.append(_issue("input.thought_text", "string_or_unicode_invalid"))
    if not _valid_scalar_text(action):
        issues.append(_issue("input.action_text", "string_or_unicode_invalid"))
    if _valid_scalar_text(thought) and _valid_scalar_text(action):
        if not ecmascript_trim(thought) and not ecmascript_trim(action):
            issues.append(_issue("input", "thought_action_both_empty_after_js_trim"))

    emotions = value.get("emotions")
    emotion_types: list[str] = []
    if not isinstance(emotions, list):
        issues.append(_issue("input.emotions", "array_required"))
    elif not emotions:
        issues.append(_issue("input.emotions", "minimum_one_required"))
    else:
        for index, emotion in enumerate(emotions):
            path = f"input.emotions[{index}]"
            if not _exact_keys(emotion, _EMOTION_KEYS):
                issues.append(_issue(path, "keyset_mismatch"))
                continue
            emotion_type = emotion.get("type")
            strength = emotion.get("strength")
            if not _valid_scalar_text(emotion_type):
                issues.append(_issue(f"{path}.type", "string_or_unicode_invalid"))
            elif emotion_type not in EMOTION_TYPES:
                issues.append(_issue(f"{path}.type", "unknown_emotion_type"))
            else:
                emotion_types.append(emotion_type)
            if not _valid_scalar_text(strength):
                issues.append(_issue(f"{path}.strength", "string_or_unicode_invalid"))
            elif strength not in STRENGTH_TYPES:
                issues.append(_issue(f"{path}.strength", "unknown_strength"))
        if len(emotion_types) != len(set(emotion_types)):
            issues.append(_issue("input.emotions", "duplicate_emotion_type"))
        if "自己理解" in emotion_types:
            if len(emotions) != 1:
                issues.append(_issue("input.emotions", "self_insight_must_be_exclusive"))
            elif emotions[0].get("strength") != "medium":
                issues.append(_issue("input.emotions[0].strength", "self_insight_requires_medium"))

    categories = value.get("categories")
    valid_categories: list[str] = []
    if not isinstance(categories, list):
        issues.append(_issue("input.categories", "array_required"))
    elif not categories:
        issues.append(_issue("input.categories", "minimum_one_required"))
    else:
        for index, category in enumerate(categories):
            path = f"input.categories[{index}]"
            if not _valid_scalar_text(category):
                issues.append(_issue(path, "string_or_unicode_invalid"))
            elif category not in CATEGORY_TYPES:
                issues.append(_issue(path, "unknown_category"))
            else:
                valid_categories.append(category)
        if len(valid_categories) != len(set(valid_categories)):
            issues.append(_issue("input.categories", "duplicate_category"))
    return tuple(dict.fromkeys(issues))


def _validate_code_array(value: Any, path: str, *, minimum: int = 0) -> list[str]:
    issues: list[str] = []
    if not isinstance(value, list):
        return [_issue(path, "array_required")]
    if len(value) < minimum:
        issues.append(_issue(path, f"minimum_{minimum}_required"))
    if any(not _valid_scalar_text(item) or not _CODE_RE.fullmatch(item) for item in value):
        issues.append(_issue(path, "code_format_invalid"))
    if len(value) != len(set(item for item in value if isinstance(item, str))):
        issues.append(_issue(path, "duplicate_value"))
    return issues


def _expected_presence(input_value: Mapping[str, Any]) -> str | None:
    thought = input_value.get("thought_text")
    action = input_value.get("action_text")
    if not _valid_scalar_text(thought) or not _valid_scalar_text(action):
        return None
    has_thought = bool(ecmascript_trim(thought))
    has_action = bool(ecmascript_trim(action))
    if has_thought and has_action:
        return "both"
    if has_thought:
        return "thought_only"
    if has_action:
        return "action_only"
    return None


def validate_sample_case(value: Any) -> tuple[str, ...]:
    issues: list[str] = []
    policy_issue = _validator_policy_binding_issue()
    if policy_issue is not None:
        return (_issue("sample.policy", policy_issue),)
    if not _exact_keys(value, _SAMPLE_KEYS):
        return (_issue("sample", "keyset_mismatch"),)
    if value.get("schema_version") != SAMPLE_SCHEMA_VERSION:
        issues.append(_issue("sample.schema_version", "mismatch"))

    case_id = value.get("case_id")
    batch_id = value.get("batch_id")
    case_match = _CASE_ID_RE.fullmatch(case_id) if isinstance(case_id, str) else None
    batch_match = _BATCH_ID_RE.fullmatch(batch_id) if isinstance(batch_id, str) else None
    if case_match is None:
        issues.append(_issue("sample.case_id", "format_invalid"))
    if batch_match is None:
        issues.append(_issue("sample.batch_id", "format_invalid"))
    if case_match is not None and batch_match is not None and case_match.group(1) != batch_match.group(1):
        issues.append(_issue("sample.case_id", "batch_identity_mismatch"))
    if value.get("source") not in SOURCE_TYPES:
        issues.append(_issue("sample.source", "enum_invalid"))

    input_value = value.get("input")
    issues.extend(validate_app_reachable_input(input_value))

    semantic = value.get("semantic_contract")
    if not _exact_keys(semantic, _SEMANTIC_KEYS):
        issues.append(_issue("sample.semantic_contract", "keyset_mismatch"))
    else:
        issues.extend(
            _validate_code_array(
                semantic.get("required_meaning_codes"),
                "sample.semantic_contract.required_meaning_codes",
                minimum=1,
            )
        )
        issues.extend(
            _validate_code_array(
                semantic.get("forbidden_claim_codes"),
                "sample.semantic_contract.forbidden_claim_codes",
                minimum=1,
            )
        )
        issues.extend(
            _validate_code_array(
                semantic.get("relation_codes"),
                "sample.semantic_contract.relation_codes",
            )
        )
        issues.extend(
            _validate_code_array(
                semantic.get("unknown_codes"),
                "sample.semantic_contract.unknown_codes",
            )
        )
        depths = semantic.get("expected_depth_range")
        if not isinstance(depths, list) or not depths:
            issues.append(_issue("sample.semantic_contract.expected_depth_range", "nonempty_array_required"))
        elif (
            any(item not in DEPTH_LEVELS for item in depths)
            or len(depths) != len(set(depths))
            or depths != [item for item in DEPTH_LEVELS if item in depths]
            or [DEPTH_LEVELS.index(item) for item in depths]
            != list(
                range(
                    DEPTH_LEVELS.index(depths[0]),
                    DEPTH_LEVELS.index(depths[-1]) + 1,
                )
            )
        ):
            issues.append(_issue("sample.semantic_contract.expected_depth_range", "enum_unique_order_invalid"))

    coverage = value.get("coverage")
    if not _exact_keys(coverage, _COVERAGE_KEYS):
        issues.append(_issue("sample.coverage", "keyset_mismatch"))
    else:
        for key, allowed in _COVERAGE_ENUMS.items():
            current = coverage.get(key)
            if key == "families":
                if (
                    not isinstance(current, list)
                    or not current
                    or any(item not in allowed for item in current)
                    or len(current) != len(set(current))
                    or current != [item for item in allowed if item in current]
                ):
                    issues.append(_issue(f"sample.coverage.{key}", "enum_unique_order_invalid"))
            elif current not in allowed:
                issues.append(_issue(f"sample.coverage.{key}", "enum_invalid"))
        variation = coverage.get("structural_variation")
        if not _exact_keys(variation, frozenset(STRUCTURAL_VARIATION_KEYS)):
            issues.append(_issue("sample.coverage.structural_variation", "keyset_mismatch"))
        elif any(type(variation[key]) is not bool for key in STRUCTURAL_VARIATION_KEYS):
            issues.append(_issue("sample.coverage.structural_variation", "strict_boolean_required"))

        if isinstance(input_value, Mapping):
            presence = _expected_presence(input_value)
            if presence is not None and coverage.get("input_field_presence") != presence:
                issues.append(_issue("sample.coverage.input_field_presence", "input_mismatch"))
            relation = coverage.get("thought_action_relation")
            if presence in {"thought_only", "action_only"} and relation != "not_applicable":
                issues.append(_issue("sample.coverage.thought_action_relation", "must_be_not_applicable"))
            if presence == "both" and relation == "not_applicable":
                issues.append(_issue("sample.coverage.thought_action_relation", "both_requires_relation"))
            emotions = input_value.get("emotions")
            if (
                isinstance(emotions, list)
                and emotions
                and all(
                    _exact_keys(item, _EMOTION_KEYS)
                    and item.get("type") in EMOTION_TYPES
                    and item.get("strength") in STRENGTH_TYPES
                    for item in emotions
                )
            ):
                types = [item.get("type") for item in emotions if isinstance(item, Mapping)]
                strengths = [
                    item.get("strength") for item in emotions if isinstance(item, Mapping)
                ]
                expected_emotion_cardinality = (
                    "self_insight_only"
                    if types == ["自己理解"]
                    else "single"
                    if len(emotions) == 1
                    else "multiple"
                )
                if coverage.get("emotion_cardinality") != expected_emotion_cardinality:
                    issues.append(_issue("sample.coverage.emotion_cardinality", "input_mismatch"))
                expected_strength_shape = (
                    "self_insight_medium"
                    if types == ["自己理解"]
                    else "single_strength"
                    if len(set(strengths)) == 1
                    else "mixed_strength"
                )
                if coverage.get("emotion_strength_shape") != expected_strength_shape:
                    issues.append(
                        _issue("sample.coverage.emotion_strength_shape", "input_mismatch")
                    )
            categories = input_value.get("categories")
            if isinstance(categories, list) and categories:
                expected_category_cardinality = "single" if len(categories) == 1 else "multiple"
                if coverage.get("category_cardinality") != expected_category_cardinality:
                    issues.append(_issue("sample.coverage.category_cardinality", "input_mismatch"))
    return tuple(dict.fromkeys(issues))


def _reject_constant(value: str) -> None:
    raise ValueError(f"non_finite_number:{value}")


def _reject_duplicate_pairs(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_json_key")
        result[key] = value
    return result


def strict_json_loads(text: str) -> Any:
    return json.loads(
        text,
        object_pairs_hook=_reject_duplicate_pairs,
        parse_constant=_reject_constant,
    )


def _assert_no_lone_surrogate(value: Any, path: str = "$") -> None:
    if isinstance(value, str):
        if _has_lone_surrogate(value):
            raise ValueError(f"lone_surrogate:{path}")
    elif isinstance(value, Mapping):
        for key, nested in value.items():
            _assert_no_lone_surrogate(key, f"{path}.<key>")
            _assert_no_lone_surrogate(nested, f"{path}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            _assert_no_lone_surrogate(nested, f"{path}[{index}]")


def load_canonical_jsonl(
    path: Path,
    *,
    validator: Callable[[Any], tuple[str, ...]] | None = validate_sample_case,
) -> list[Any]:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ValueError("jsonl_utf8_bom_forbidden")
    if b"\r" in raw:
        raise ValueError("jsonl_lf_only_required")
    if not raw or not raw.endswith(b"\n"):
        raise ValueError("jsonl_final_lf_required")
    text = raw.decode("utf-8", errors="strict")
    rows: list[Any] = []
    seen_case_ids: set[str] = set()
    for line_number, line in enumerate(text.split("\n")[:-1], start=1):
        if not line:
            raise ValueError(f"jsonl_blank_line:{line_number}")
        row = strict_json_loads(line)
        _assert_no_lone_surrogate(row)
        if canonical_json_text(row) != line:
            raise ValueError(f"jsonl_noncanonical_line:{line_number}")
        if validator is not None:
            issues = validator(row)
            if issues:
                raise ValueError(f"jsonl_contract_invalid:{line_number}:{issues[0]}")
        if validator is validate_sample_case:
            case_id = str(row["case_id"])
            if case_id in seen_case_ids:
                raise ValueError(f"jsonl_duplicate_case_id:{line_number}")
            seen_case_ids.add(case_id)
        rows.append(row)
    return rows


def load_canonical_json(path: Path) -> Any:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ValueError("json_utf8_bom_forbidden")
    if b"\r" in raw:
        raise ValueError("json_lf_only_required")
    if not raw.endswith(b"\n") or raw.endswith(b"\n\n"):
        raise ValueError("json_single_final_lf_required")
    text = raw[:-1].decode("utf-8", errors="strict")
    value = strict_json_loads(text)
    _assert_no_lone_surrogate(value)
    if canonical_json_text(value) != text:
        raise ValueError("json_noncanonical")
    return value


def project_generation_input(sample: Mapping[str, Any]) -> dict[str, Any]:
    issues = validate_sample_case(sample)
    if issues:
        raise ValueError("invalid_sample_for_projection:" + issues[0])
    source = sample["input"]
    return {
        "thought_text": str(source["thought_text"]),
        "action_text": str(source["action_text"]),
        "emotions": [
            {"type": str(item["type"]), "strength": str(item["strength"])}
            for item in source["emotions"]
        ],
        "categories": [str(item) for item in source["categories"]],
    }


def _collapse_ecmascript_whitespace(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value.replace("\r\n", "\n").replace("\r", "\n"))
    output: list[str] = []
    in_space = False
    for char in ecmascript_trim(normalized):
        if ord(char) in _ECMASCRIPT_TRIM_CODEPOINTS:
            if not in_space:
                output.append(" ")
            in_space = True
        else:
            output.append(char)
            in_space = False
    return "".join(output)


def _require_shareable_synthetic_sample(sample: Mapping[str, Any]) -> None:
    issues = validate_sample_case(sample)
    if issues:
        raise ValueError("shareable_artifact_invalid_sample:" + issues[0])
    if sample.get("source") not in SHAREABLE_SYNTHETIC_SOURCES:
        raise ValueError("shareable_artifact_requires_reviewed_synthetic_source")


def exact_input_identity(sample: Mapping[str, Any]) -> str:
    _require_shareable_synthetic_sample(sample)
    return sha256_json(sample["input"])


def normalized_input_value(sample: Mapping[str, Any]) -> dict[str, Any]:
    value = sample["input"]
    emotion_order = {item: index for index, item in enumerate(EMOTION_TYPES)}
    strength_order = {item: index for index, item in enumerate(STRENGTH_TYPES)}
    category_order = {item: index for index, item in enumerate(CATEGORY_TYPES)}
    emotions = sorted(
        (
            {"type": str(item["type"]), "strength": str(item["strength"])}
            for item in value["emotions"]
        ),
        key=lambda item: (emotion_order[item["type"]], strength_order[item["strength"]]),
    )
    return {
        "thought_text": _collapse_ecmascript_whitespace(str(value["thought_text"])),
        "action_text": _collapse_ecmascript_whitespace(str(value["action_text"])),
        "emotions": emotions,
        "categories": sorted(
            (str(item) for item in value["categories"]),
            key=category_order.__getitem__,
        ),
    }


def normalized_input_identity(sample: Mapping[str, Any]) -> str:
    _require_shareable_synthetic_sample(sample)
    return sha256_json(normalized_input_value(sample))


def case_commitment(sample: Mapping[str, Any]) -> str:
    _require_shareable_synthetic_sample(sample)
    return sha256_json(sample)


def corpus_set_commitment(samples: Sequence[Mapping[str, Any]]) -> str:
    return sha256_json(sorted(case_commitment(sample) for sample in samples))


def private_input_identity_hmac(
    input_value: Mapping[str, Any],
    *,
    key: bytes,
    key_id: str,
) -> str:
    if len(key) < 32:
        raise ValueError("private_identity_key_must_be_at_least_256_bits")
    if not re.fullmatch(r"^[a-z][a-z0-9_-]{2,63}$", key_id):
        raise ValueError("private_identity_key_id_invalid")
    domain = f"cocolon:nls3:private-input:v1:{key_id}\0".encode("utf-8")
    return hmac.new(key, domain + canonical_json_bytes(input_value), hashlib.sha256).hexdigest()


def private_case_commitment_hmac(
    sample: Mapping[str, Any],
    *,
    key: bytes,
    key_id: str,
) -> str:
    issues = validate_sample_case(sample)
    if issues:
        raise ValueError("private_case_invalid_sample:" + issues[0])
    if sample.get("source") != "real_user_anonymized_private":
        raise ValueError("private_case_source_required")
    if len(key) < 32:
        raise ValueError("private_identity_key_must_be_at_least_256_bits")
    if not re.fullmatch(r"^[a-z][a-z0-9_-]{2,63}$", key_id):
        raise ValueError("private_identity_key_id_invalid")
    domain = f"cocolon:nls3:private-case:v1:{key_id}\0".encode("utf-8")
    return hmac.new(key, domain + canonical_json_bytes(sample), hashlib.sha256).hexdigest()


def private_corpus_set_commitment_hmac(
    samples: Sequence[Mapping[str, Any]],
    *,
    key: bytes,
    key_id: str,
) -> str:
    case_hmacs = sorted(
        private_case_commitment_hmac(sample, key=key, key_id=key_id)
        for sample in samples
    )
    case_ids = [str(sample["case_id"]) for sample in samples]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("private_corpus_duplicate_case_id")
    if len(case_hmacs) != len(set(case_hmacs)):
        raise ValueError("private_corpus_duplicate_case_commitment")
    domain = f"cocolon:nls3:private-corpus-set:v1:{key_id}\0".encode("utf-8")
    return hmac.new(key, domain + canonical_json_bytes(case_hmacs), hashlib.sha256).hexdigest()


def _near_text(sample: Mapping[str, Any]) -> str:
    normalized = normalized_input_value(sample)
    return f"{normalized['thought_text']}\u241f{normalized['action_text']}"


def _character_bigram_dice(left: str, right: str) -> float:
    if left == right:
        return 1.0
    left_bigrams = Counter(left[index : index + 2] for index in range(max(0, len(left) - 1)))
    right_bigrams = Counter(right[index : index + 2] for index in range(max(0, len(right) - 1)))
    total = sum(left_bigrams.values()) + sum(right_bigrams.values())
    if total == 0:
        return 0.0
    overlap = sum((left_bigrams & right_bigrams).values())
    return (2.0 * overlap) / total


def _near_score_basis_points(left: Mapping[str, Any], right: Mapping[str, Any]) -> int:
    left_text = _near_text(left)
    right_text = _near_text(right)
    sequence = max(
        SequenceMatcher(None, left_text, right_text, autojunk=False).ratio(),
        SequenceMatcher(None, right_text, left_text, autojunk=False).ratio(),
    )
    bigram = _character_bigram_dice(left_text, right_text)
    return int(round(max(sequence, bigram) * 10000))


def _near_source_text_length(sample: Mapping[str, Any]) -> int:
    normalized = normalized_input_value(sample)
    return len(normalized["thought_text"]) + len(normalized["action_text"])


def build_duplicate_report(
    samples: Sequence[Mapping[str, Any]],
    *,
    reference_samples: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    _require_frozen_policy_bindings()
    for sample in [*samples, *reference_samples]:
        _require_shareable_synthetic_sample(sample)
    case_ids = [str(sample["case_id"]) for sample in [*samples, *reference_samples]]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("duplicate_case_id")

    pair_count = len(samples) * (len(samples) - 1) // 2 + len(samples) * len(reference_samples)
    if pair_count > int(DUPLICATE_POLICY["maximum_pair_comparisons"]):
        raise ValueError("novelty_check_indeterminate_pair_budget")
    total_characters = sum(
        _near_source_text_length(sample) for sample in [*samples, *reference_samples]
    )
    if total_characters > int(
        DUPLICATE_POLICY["maximum_total_normalized_text_characters"]
    ):
        raise ValueError("novelty_check_indeterminate_text_budget")

    pairs: list[dict[str, Any]] = []
    counts = {"exact": 0, "normalized": 0, "near": 0}
    minimum = int(DUPLICATE_POLICY["near_minimum_text_characters"])
    threshold = int(DUPLICATE_POLICY["near_threshold_basis_points"])
    comparisons: list[tuple[Mapping[str, Any], Mapping[str, Any], str]] = []
    for left_index, left in enumerate(samples):
        for right in samples[left_index + 1 :]:
            comparisons.append((left, right, "within_query"))
        for right in reference_samples:
            comparisons.append((left, right, "against_registry"))
    for left, right, scope in comparisons:
        kind: str | None = None
        score: int | None = None
        if exact_input_identity(left) == exact_input_identity(right):
            kind = "exact"
            score = 10000
        elif normalized_input_identity(left) == normalized_input_identity(right):
            kind = "normalized"
            score = 10000
        else:
            same_presence = (
                left["coverage"]["input_field_presence"]
                == right["coverage"]["input_field_presence"]
            )
            if (
                min(_near_source_text_length(left), _near_source_text_length(right))
                >= minimum
                and same_presence
            ):
                candidate_score = _near_score_basis_points(left, right)
                if candidate_score >= threshold:
                    kind = "near"
                    score = candidate_score
        if kind is not None and score is not None:
            counts[kind] += 1
            pair_ids = sorted((str(left["case_id"]), str(right["case_id"])))
            pairs.append(
                {
                    "left_case_id": pair_ids[0],
                    "match_kind": kind,
                    "right_case_id": pair_ids[1],
                    "score_basis_points": score,
                    "scope": scope,
                }
            )
    pairs.sort(
        key=lambda row: (
            row["left_case_id"],
            row["right_case_id"],
            row["match_kind"],
            row["scope"],
        )
    )
    return {
        "schema_version": "cocolon.emlis.nls_v3.duplicate_report.v1",
        "policy_sha256": DUPLICATE_POLICY_SHA256,
        "query_case_count": len(samples),
        "reference_case_count": len(reference_samples),
        "query_corpus_set_commitment": corpus_set_commitment(samples),
        "reference_corpus_set_commitment": corpus_set_commitment(reference_samples),
        "counts": counts,
        "pairs": pairs,
        "body_free": True,
    }


def _coverage_axis_values() -> dict[str, tuple[str, ...]]:
    values = dict(_COVERAGE_ENUMS)
    values["expected_depth_range"] = DEPTH_LEVELS
    for key in STRUCTURAL_VARIATION_KEYS:
        values[f"structural_variation.{key}"] = ("false", "true")
    return values


def build_coverage_matrix(
    samples: Sequence[Mapping[str, Any]],
    *,
    batch_id: str,
) -> dict[str, Any]:
    if _BATCH_ID_RE.fullmatch(batch_id) is None:
        raise ValueError("coverage_batch_id_invalid")
    for sample in samples:
        _require_shareable_synthetic_sample(sample)
        if sample["batch_id"] != batch_id:
            raise ValueError("coverage_sample_batch_mismatch")
    case_ids = [str(sample["case_id"]) for sample in samples]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("coverage_duplicate_case_id")
    axis_values = _coverage_axis_values()
    counters = {axis: Counter() for axis in axis_values}
    for sample in samples:
        coverage = sample["coverage"]
        for axis in _COVERAGE_ENUMS:
            current = coverage[axis]
            for item in current if axis == "families" else (current,):
                counters[axis][item] += 1
        for depth in sample["semantic_contract"]["expected_depth_range"]:
            counters["expected_depth_range"][depth] += 1
        for key in STRUCTURAL_VARIATION_KEYS:
            counters[f"structural_variation.{key}"][
                str(coverage["structural_variation"][key]).lower()
            ] += 1
    rows = [
        {
            "axis": axis,
            "value_counts": [
                {"value": value, "case_count": int(counters[axis][value])}
                for value in allowed
            ],
        }
        for axis, allowed in sorted(axis_values.items())
    ]
    payload = {
        "schema_version": COVERAGE_SCHEMA_VERSION,
        "batch_id": batch_id,
        "sample_schema_sha256": sha256_file(SAMPLE_SCHEMA_PATH),
        "source_case_set_commitment": corpus_set_commitment(samples),
        "case_count": len(samples),
        "axis_counts": rows,
        "body_free": True,
    }
    return {"matrix_id": "nls3cov_" + sha256_json(payload)[:16], **payload}


_COVERAGE_MATRIX_KEYS = frozenset(
    {
        "schema_version",
        "matrix_id",
        "batch_id",
        "sample_schema_sha256",
        "source_case_set_commitment",
        "case_count",
        "axis_counts",
        "body_free",
    }
)


def validate_coverage_matrix(
    value: Any,
    samples: Sequence[Mapping[str, Any]],
) -> tuple[str, ...]:
    if not _exact_keys(value, _COVERAGE_MATRIX_KEYS):
        return (_issue("coverage_matrix", "keyset_mismatch"),)
    batch_id = value.get("batch_id")
    if not isinstance(batch_id, str):
        return (_issue("coverage_matrix.batch_id", "type_invalid"),)
    try:
        expected = build_coverage_matrix(samples, batch_id=batch_id)
    except ValueError as exc:
        return (_issue("coverage_matrix", str(exc)),)
    return () if strict_json_equal(dict(value), expected) else (
        _issue("coverage_matrix", "recomputed_value_mismatch"),
    )


_BATCH_MANIFEST_KEYS = frozenset(
    {
        "schema_version",
        "manifest_id",
        "batch_id",
        "state",
        "source_partition",
        "parent_registry_ref",
        "parent_registry_sha256",
        "sample_schema_ref",
        "sample_schema_sha256",
        "validator_policy_sha256",
        "duplicate_policy_sha256",
        "corpus_file_ref",
        "corpus_file_sha256",
        "corpus_set_commitment",
        "coverage_matrix_ref",
        "coverage_matrix_sha256",
        "duplicate_report_ref",
        "duplicate_report_sha256",
        "reference_case_count",
        "reference_corpus_set_commitment",
        "case_count",
        "valid_case_count",
        "invalid_case_count",
        "invalid_case_history",
        "case_ids",
        "case_commitments",
        "duplicate_counts",
        "near_review_decisions",
        "near_review_summary",
        "privacy_review",
        "counts_toward_karen_minimum",
        "frozen",
        "replacement_policy",
        "body_free",
        "next_authority",
    }
)
_NEAR_REVIEW_KEYS = frozenset(
    {"left_case_id", "right_case_id", "verdict", "reason_code"}
)
_INVALID_HISTORY_KEYS = frozenset(
    {"invalid_case_id", "reason_code", "replacement_case_id", "status"}
)
_PRIVACY_REVIEW_KEYS = frozenset(
    {
        "status",
        "reviewer",
        "pii_absent",
        "real_user_text_copy_absent",
        "expected_response_absent",
    }
)


def _validate_privacy_review(value: Any) -> None:
    if not _exact_keys(value, _PRIVACY_REVIEW_KEYS):
        raise ValueError("batch_manifest_privacy_review_shape_invalid")
    if value.get("status") not in {"pending", "passed"}:
        raise ValueError("batch_manifest_privacy_review_status_invalid")
    if value.get("reviewer") not in {None, "karen"}:
        raise ValueError("batch_manifest_privacy_review_reviewer_invalid")
    for key in ("pii_absent", "real_user_text_copy_absent", "expected_response_absent"):
        if type(value.get(key)) is not bool:
            raise ValueError("batch_manifest_privacy_review_boolean_invalid")
    expected = (
        {
            "status": "pending",
            "reviewer": None,
            "pii_absent": False,
            "real_user_text_copy_absent": False,
            "expected_response_absent": False,
        }
        if value["status"] == "pending"
        else {
            "status": "passed",
            "reviewer": "karen",
            "pii_absent": True,
            "real_user_text_copy_absent": True,
            "expected_response_absent": True,
        }
    )
    if not strict_json_equal(dict(value), expected):
        raise ValueError("batch_manifest_privacy_review_claim_invalid")


def _load_registry_reference_samples(
    registry: Mapping[str, Any],
    *,
    exclude_path: Path,
) -> list[Mapping[str, Any]]:
    rows: list[Mapping[str, Any]] = []
    for collection in registry["collections"]:
        classification = collection["classification"]
        if classification not in SHAREABLE_SYNTHETIC_SOURCES:
            continue
        ref = collection["corpus_ref"]
        if not isinstance(ref, str) or not _safe_relative_artifact_ref(ref):
            raise ValueError("registry_reference_corpus_ref_invalid")
        path = (_REPO_ROOT / ref).resolve()
        if path == exclude_path.resolve():
            continue
        if _REPO_ROOT.resolve() not in path.parents:
            raise ValueError("registry_reference_corpus_outside_repo")
        current = load_canonical_jsonl(path)
        if any(sample["source"] != classification for sample in current):
            raise ValueError("registry_reference_source_mismatch")
        rows.extend(current)
    if len({str(sample["case_id"]) for sample in rows}) != len(rows):
        raise ValueError("registry_reference_duplicate_case_id")
    return rows


def _near_review_result(
    report: Mapping[str, Any],
    decisions: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, str]], dict[str, int]]:
    near_pairs = {
        (row["left_case_id"], row["right_case_id"])
        for row in report["pairs"]
        if row["match_kind"] == "near"
    }
    normalized: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for decision in decisions:
        if not _exact_keys(decision, _NEAR_REVIEW_KEYS):
            raise ValueError("near_review_decision_shape_invalid")
        left = decision.get("left_case_id")
        right = decision.get("right_case_id")
        if not isinstance(left, str) or not isinstance(right, str) or left >= right:
            raise ValueError("near_review_decision_pair_invalid")
        pair = (left, right)
        if pair not in near_pairs or pair in seen:
            raise ValueError("near_review_decision_pair_not_candidate_or_duplicate")
        seen.add(pair)
        verdict = decision.get("verdict")
        reason_code = decision.get("reason_code")
        if verdict not in {"accepted_distinct", "reject_duplicate"}:
            raise ValueError("near_review_decision_verdict_invalid")
        if not isinstance(reason_code, str) or _CODE_RE.fullmatch(reason_code) is None:
            raise ValueError("near_review_decision_reason_invalid")
        normalized.append(
            {
                "left_case_id": left,
                "right_case_id": right,
                "verdict": verdict,
                "reason_code": reason_code,
            }
        )
    normalized.sort(key=lambda row: (row["left_case_id"], row["right_case_id"]))
    accepted = sum(row["verdict"] == "accepted_distinct" for row in normalized)
    rejected = sum(row["verdict"] == "reject_duplicate" for row in normalized)
    return normalized, {
        "candidate_count": len(near_pairs),
        "accepted_distinct_count": accepted,
        "rejected_duplicate_count": rejected,
        "unresolved_count": len(near_pairs) - len(normalized),
    }


def _normalize_invalid_case_history(
    history: Sequence[Mapping[str, Any]],
    *,
    batch_id: str,
    final_case_ids: set[str],
    registry: Mapping[str, Any],
) -> list[dict[str, str]]:
    batch_match = _BATCH_ID_RE.fullmatch(batch_id)
    if batch_match is None:
        raise ValueError("invalid_history_batch_id_invalid")
    registered = set(registry["cumulative_novelty_index"]["registered_case_ids"])
    retired = set(registry["cumulative_novelty_index"]["retired_invalid_case_ids"])
    normalized: list[dict[str, str]] = []
    invalid_ids: set[str] = set()
    replacement_ids: set[str] = set()
    for row in history:
        if not _exact_keys(row, _INVALID_HISTORY_KEYS):
            raise ValueError("invalid_history_row_shape_invalid")
        invalid_id = row.get("invalid_case_id")
        replacement_id = row.get("replacement_case_id")
        reason_code = row.get("reason_code")
        invalid_match = (
            _CASE_ID_RE.fullmatch(invalid_id) if isinstance(invalid_id, str) else None
        )
        replacement_match = (
            _CASE_ID_RE.fullmatch(replacement_id)
            if isinstance(replacement_id, str)
            else None
        )
        if (
            invalid_match is None
            or replacement_match is None
            or invalid_match.group(1) != batch_match.group(1)
            or replacement_match.group(1) != batch_match.group(1)
        ):
            raise ValueError("invalid_history_case_batch_mismatch")
        if invalid_id == replacement_id:
            raise ValueError("invalid_history_replacement_must_use_new_id")
        if invalid_id in final_case_ids or replacement_id not in final_case_ids:
            raise ValueError("invalid_history_final_corpus_membership_invalid")
        if invalid_id in registered or invalid_id in retired:
            raise ValueError("invalid_history_case_id_reused")
        if replacement_id in registered or replacement_id in retired:
            raise ValueError("invalid_history_replacement_case_id_reused")
        if invalid_id in invalid_ids or replacement_id in replacement_ids:
            raise ValueError("invalid_history_duplicate_id")
        if not isinstance(reason_code, str) or _CODE_RE.fullmatch(reason_code) is None:
            raise ValueError("invalid_history_reason_code_invalid")
        if row.get("status") != "replaced_before_manifest_freeze":
            raise ValueError("invalid_history_status_invalid")
        invalid_ids.add(invalid_id)
        replacement_ids.add(replacement_id)
        normalized.append(
            {
                "invalid_case_id": invalid_id,
                "reason_code": reason_code,
                "replacement_case_id": replacement_id,
                "status": "replaced_before_manifest_freeze",
            }
        )
    normalized.sort(key=lambda row: row["invalid_case_id"])
    return normalized


def build_batch_manifest(
    samples: Sequence[Mapping[str, Any]],
    *,
    corpus_path: Path,
    coverage_matrix_path: Path,
    duplicate_report_path: Path,
    state: str,
    frozen: bool,
    privacy_review: Mapping[str, Any],
    near_review_decisions: Sequence[Mapping[str, Any]] = (),
    invalid_case_history: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    _require_frozen_policy_bindings()
    if not samples:
        raise ValueError("batch_manifest_requires_cases")
    batch_ids = {str(sample.get("batch_id")) for sample in samples}
    if len(batch_ids) != 1:
        raise ValueError("batch_manifest_mixed_batch_ids")
    batch_id = next(iter(batch_ids))
    for sample in samples:
        _require_shareable_synthetic_sample(sample)
        if sample["source"] != "karen_generated":
            raise ValueError("batch_manifest_source_partition_mismatch")
    if len(samples) > 100:
        raise ValueError("batch_manifest_case_count_above_100")

    if state not in {"DRAFT", "VALIDATED"}:
        raise ValueError("batch_manifest_state_invalid")
    if type(frozen) is not bool:
        raise ValueError("batch_manifest_frozen_strict_boolean_required")
    if frozen and state != "VALIDATED":
        raise ValueError("batch_manifest_only_validated_can_freeze")
    _validate_privacy_review(privacy_review)
    if state == "VALIDATED" and len(samples) != 100:
        raise ValueError("batch_manifest_validated_requires_100_cases")
    if state == "VALIDATED" and privacy_review.get("status") != "passed":
        raise ValueError("batch_manifest_validated_requires_privacy_review")

    corpus_file_ref = _repo_ref(corpus_path)
    coverage_matrix_ref = _repo_ref(coverage_matrix_path)
    duplicate_report_ref = _repo_ref(duplicate_report_path)
    corpus_rows = load_canonical_jsonl(corpus_path)
    if not strict_json_equal(
        sorted(corpus_rows, key=lambda row: row["case_id"]),
        sorted(samples, key=lambda row: row["case_id"]),
    ):
        raise ValueError("batch_manifest_corpus_content_mismatch")
    corpus_file_sha256 = sha256_file(corpus_path)

    registry = load_canonical_json(REGISTRY_PATH)
    registry_issues = validate_corpus_registry(registry)
    if registry_issues:
        raise ValueError("batch_manifest_parent_registry_invalid:" + registry_issues[0])
    reference_samples = _load_registry_reference_samples(
        registry,
        exclude_path=corpus_path,
    )
    final_case_ids = {str(sample["case_id"]) for sample in samples}
    novelty_index = registry["cumulative_novelty_index"]
    unavailable_case_ids = set(novelty_index["registered_case_ids"]) | set(
        novelty_index["retired_invalid_case_ids"]
    )
    if final_case_ids & unavailable_case_ids:
        raise ValueError("batch_manifest_case_id_reused")
    normalized_invalid_history = _normalize_invalid_case_history(
        invalid_case_history,
        batch_id=batch_id,
        final_case_ids=final_case_ids,
        registry=registry,
    )

    coverage_matrix = load_canonical_json(coverage_matrix_path)
    if validate_coverage_matrix(coverage_matrix, samples):
        raise ValueError("batch_manifest_coverage_invalid")
    duplicate_report = load_canonical_json(duplicate_report_path)
    expected_duplicate_report = build_duplicate_report(
        samples,
        reference_samples=reference_samples,
    )
    if not strict_json_equal(duplicate_report, expected_duplicate_report):
        raise ValueError("batch_manifest_duplicate_report_invalid")
    duplicate_counts = dict(duplicate_report["counts"])
    decisions, near_summary = _near_review_result(
        duplicate_report,
        near_review_decisions,
    )
    if state == "VALIDATED" and (
        duplicate_counts["exact"]
        or duplicate_counts["normalized"]
        or near_summary["rejected_duplicate_count"]
        or near_summary["unresolved_count"]
    ):
        raise ValueError("batch_manifest_validated_novelty_not_resolved")
    case_rows = [
        {"case_id": str(sample["case_id"]), "case_commitment": case_commitment(sample)}
        for sample in sorted(samples, key=lambda row: str(row["case_id"]))
    ]
    if state == "DRAFT":
        next_authority = "continue_batch_construction"
    elif not frozen:
        next_authority = "freeze_batch_manifest"
    elif batch_id == "nls3_batch_001":
        next_authority = "step3_only"
    else:
        next_authority = "none_outside_step2_transition"

    payload = {
        "schema_version": BATCH_MANIFEST_SCHEMA_VERSION,
        "batch_id": batch_id,
        "state": state,
        "source_partition": "karen_generated",
        "parent_registry_ref": _repo_ref(REGISTRY_PATH),
        "parent_registry_sha256": sha256_file(REGISTRY_PATH),
        "sample_schema_ref": _repo_ref(SAMPLE_SCHEMA_PATH),
        "sample_schema_sha256": sha256_file(SAMPLE_SCHEMA_PATH),
        "validator_policy_sha256": VALIDATOR_POLICY_SHA256,
        "duplicate_policy_sha256": DUPLICATE_POLICY_SHA256,
        "corpus_file_ref": corpus_file_ref,
        "corpus_file_sha256": corpus_file_sha256,
        "corpus_set_commitment": corpus_set_commitment(samples),
        "coverage_matrix_ref": coverage_matrix_ref,
        "coverage_matrix_sha256": sha256_file(coverage_matrix_path),
        "duplicate_report_ref": duplicate_report_ref,
        "duplicate_report_sha256": sha256_file(duplicate_report_path),
        "reference_case_count": len(reference_samples),
        "reference_corpus_set_commitment": corpus_set_commitment(reference_samples),
        "case_count": len(samples),
        "valid_case_count": len(samples),
        "invalid_case_count": len(normalized_invalid_history),
        "invalid_case_history": normalized_invalid_history,
        "case_ids": [row["case_id"] for row in case_rows],
        "case_commitments": case_rows,
        "duplicate_counts": duplicate_counts,
        "near_review_decisions": decisions,
        "near_review_summary": near_summary,
        "privacy_review": dict(privacy_review),
        "counts_toward_karen_minimum": False,
        "frozen": frozen,
        "replacement_policy": "invalid_case_id_never_reused_replacement_gets_new_id",
        "body_free": True,
        "next_authority": next_authority,
    }
    return {"manifest_id": "nls3manifest_" + sha256_json(payload)[:16], **payload}


def validate_batch_manifest(
    value: Any,
    samples: Sequence[Mapping[str, Any]],
    *,
    corpus_path: Path,
    coverage_matrix_path: Path,
    duplicate_report_path: Path,
    expected_state: str,
    expected_frozen: bool,
    expected_privacy_review: Mapping[str, Any],
    expected_near_review_decisions: Sequence[Mapping[str, Any]] = (),
    expected_invalid_case_history: Sequence[Mapping[str, Any]] = (),
) -> tuple[str, ...]:
    if not _exact_keys(value, _BATCH_MANIFEST_KEYS):
        return (_issue("batch_manifest", "keyset_mismatch"),)
    try:
        expected = build_batch_manifest(
            samples,
            corpus_path=corpus_path,
            coverage_matrix_path=coverage_matrix_path,
            duplicate_report_path=duplicate_report_path,
            state=expected_state,
            frozen=expected_frozen,
            privacy_review=expected_privacy_review,
            near_review_decisions=expected_near_review_decisions,
            invalid_case_history=expected_invalid_case_history,
        )
    except (OSError, UnicodeError, ValueError) as exc:
        return (_issue("batch_manifest", str(exc)),)
    return () if strict_json_equal(dict(value), expected) else (
        _issue("batch_manifest", "recomputed_value_mismatch"),
    )


_REGISTRY_KEYS = frozenset(
    {
        "schema_version",
        "registry_id",
        "design_sha256",
        "parent_step1_ref",
        "parent_step1_sha256",
        "schemas",
        "validator_owner",
        "test_evidence",
        "policies",
        "collections",
        "aggregate_counts",
        "cumulative_novelty_index",
        "batch001_status",
        "completion_condition",
        "step2_status",
        "next_step_authority",
        "valid_for_batch001_creation",
        "valid_for_runtime_switch",
        "body_free",
    }
)
_COLLECTION_KEYS = frozenset(
    {
        "collection_id",
        "classification",
        "provenance_subtype",
        "status",
        "storage",
        "corpus_ref",
        "corpus_sha256",
        "case_count",
        "app_reachable_valid_count",
        "counts_toward_karen_minimum",
        "raw_body_in_registry",
        "private_commitment_policy",
    }
)
_CUMULATIVE_NOVELTY_INDEX_KEYS = frozenset(
    {
        "registered_case_ids",
        "retired_invalid_case_ids",
        "exact_input_identities",
        "normalized_input_identities",
        "accepted_batch_refs",
        "reference_case_count",
        "accepted_karen_case_count",
        "replacement_case_id_reuse_allowed",
        "identity_scope",
    }
)


def _load_schema(path: Path) -> Mapping[str, Any]:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ValueError("schema_bom_forbidden")
    value = strict_json_loads(raw.decode("utf-8", errors="strict"))
    _assert_no_lone_surrogate(value)
    if not isinstance(value, dict):
        raise ValueError("schema_root_object_required")
    return value


def schema_runtime_binding_issues() -> tuple[str, ...]:
    issues: list[str] = []
    try:
        sample = _load_schema(SAMPLE_SCHEMA_PATH)
        coverage = _load_schema(COVERAGE_SCHEMA_PATH)
        manifest = _load_schema(BATCH_MANIFEST_SCHEMA_PATH)
        registry = _load_schema(CORPUS_REGISTRY_SCHEMA_PATH)
    except (OSError, UnicodeError, ValueError) as exc:
        return (f"schema_load_failed_{type(exc).__name__}",)

    expected_roots = (
        (sample, SAMPLE_SCHEMA_VERSION, _SAMPLE_KEYS),
        (coverage, COVERAGE_SCHEMA_VERSION, _COVERAGE_MATRIX_KEYS),
        (manifest, BATCH_MANIFEST_SCHEMA_VERSION, _BATCH_MANIFEST_KEYS),
        (registry, CORPUS_REGISTRY_SCHEMA_VERSION, _REGISTRY_KEYS),
    )
    for current, schema_id, required in expected_roots:
        if current.get("$id") != schema_id:
            issues.append(f"schema_id_mismatch:{schema_id}")
        if current.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            issues.append(f"schema_draft_mismatch:{schema_id}")
        if current.get("type") != "object" or current.get("additionalProperties") is not False:
            issues.append(f"schema_root_not_closed:{schema_id}")
        if set(current.get("properties") or {}) != set(required):
            issues.append(f"schema_property_mismatch:{schema_id}")
        if set(current.get("required") or []) != set(required):
            issues.append(f"schema_required_mismatch:{schema_id}")

    sample_properties = sample.get("properties") or {}
    input_schema = sample_properties.get("input") or {}
    input_properties = input_schema.get("properties") or {}
    if set(input_properties) != _INPUT_KEYS or set(input_schema.get("required") or []) != _INPUT_KEYS:
        issues.append("sample_schema_input_keyset_mismatch")
    if input_schema.get("additionalProperties") is not False:
        issues.append("sample_schema_input_not_closed")
    categories_schema = input_properties.get("categories") or {}
    if (
        (categories_schema.get("items") or {}).get("enum") != list(CATEGORY_TYPES)
        or categories_schema.get("minItems") != 1
        or categories_schema.get("maxItems") != len(CATEGORY_TYPES)
        or categories_schema.get("uniqueItems") is not True
    ):
        issues.append("sample_schema_category_enum_mismatch")
    emotion_union = (input_properties.get("emotions") or {}).get("oneOf")
    if not isinstance(emotion_union, list) or len(emotion_union) != 2:
        issues.append("sample_schema_emotion_union_missing")
    else:
        normal_type = (
            emotion_union[0].get("items", {}).get("properties", {}).get("type", {}).get("enum")
        )
        normal_strength = (
            emotion_union[0]
            .get("items", {})
            .get("properties", {})
            .get("strength", {})
            .get("enum")
        )
        self_properties = emotion_union[1].get("items", {}).get("properties", {})
        if (
            normal_type != list(EMOTION_TYPES[:-1])
            or normal_strength != list(STRENGTH_TYPES)
            or emotion_union[0].get("minItems") != 1
            or emotion_union[0].get("maxItems") != len(EMOTION_TYPES) - 1
            or emotion_union[0].get("uniqueItems") is not True
        ):
            issues.append("sample_schema_emotion_enum_mismatch")
        if (
            self_properties.get("type", {}).get("const") != "自己理解"
            or self_properties.get("strength", {}).get("const") != "medium"
            or emotion_union[1].get("minItems") != 1
            or emotion_union[1].get("maxItems") != 1
        ):
            issues.append("sample_schema_self_insight_union_mismatch")
    if sample_properties.get("source", {}).get("enum") != list(SOURCE_TYPES):
        issues.append("sample_schema_source_enum_mismatch")

    coverage_schema = sample_properties.get("coverage") or {}
    coverage_properties = coverage_schema.get("properties") or {}
    if set(coverage_properties) != _COVERAGE_KEYS:
        issues.append("sample_schema_coverage_keyset_mismatch")
    for key, allowed in _COVERAGE_ENUMS.items():
        current = coverage_properties.get(key) or {}
        actual = (current.get("items") or {}).get("enum") if key == "families" else current.get("enum")
        if actual != list(allowed):
            issues.append(f"sample_schema_coverage_enum_mismatch:{key}")
    variation = coverage_properties.get("structural_variation") or {}
    if (
        set(variation.get("properties") or {}) != set(STRUCTURAL_VARIATION_KEYS)
        or set(variation.get("required") or []) != set(STRUCTURAL_VARIATION_KEYS)
        or variation.get("additionalProperties") is not False
    ):
        issues.append("sample_schema_structural_variation_mismatch")
    semantic_schema = sample_properties.get("semantic_contract") or {}
    semantic_properties = semantic_schema.get("properties") or {}
    if (
        set(semantic_properties) != _SEMANTIC_KEYS
        or set(semantic_schema.get("required") or []) != _SEMANTIC_KEYS
        or semantic_schema.get("additionalProperties") is not False
    ):
        issues.append("sample_schema_semantic_contract_mismatch")
    depth_options = [
        row.get("const")
        for row in (semantic_properties.get("expected_depth_range") or {}).get(
            "oneOf", []
        )
    ]
    expected_depth_options = [
        ["minimal"],
        ["focused"],
        ["layered"],
        ["minimal", "focused"],
        ["focused", "layered"],
        ["minimal", "focused", "layered"],
    ]
    if depth_options != expected_depth_options:
        issues.append("sample_schema_depth_range_mismatch")

    coverage_axis = (
        coverage.get("properties", {})
        .get("axis_counts", {})
        .get("items", {})
        .get("properties", {})
        .get("axis", {})
        .get("enum")
    )
    if coverage_axis != sorted(_coverage_axis_values()):
        issues.append("coverage_schema_axis_enum_mismatch")
    coverage_values = (
        coverage.get("properties", {})
        .get("axis_counts", {})
        .get("items", {})
        .get("properties", {})
        .get("value_counts", {})
        .get("items", {})
        .get("properties", {})
        .get("value", {})
        .get("enum")
    )
    expected_values = list(
        dict.fromkeys(
            value
            for allowed in _coverage_axis_values().values()
            for value in allowed
        )
    )
    if coverage_values != expected_values:
        issues.append("coverage_schema_value_enum_mismatch")
    if manifest.get("properties", {}).get("state", {}).get("enum") != [
        "DRAFT",
        "VALIDATED",
    ]:
        issues.append("manifest_schema_state_enum_mismatch")
    if manifest.get("properties", {}).get("source_partition", {}).get("const") != "karen_generated":
        issues.append("manifest_schema_source_partition_mismatch")
    if manifest.get("properties", {}).get("counts_toward_karen_minimum", {}).get("const") is not False:
        issues.append("manifest_schema_premature_count_mismatch")
    invalid_history_schema = (
        manifest.get("properties", {}).get("invalid_case_history", {}).get("items", {})
    )
    if (
        set(invalid_history_schema.get("properties") or {}) != _INVALID_HISTORY_KEYS
        or set(invalid_history_schema.get("required") or []) != _INVALID_HISTORY_KEYS
        or invalid_history_schema.get("additionalProperties") is not False
        or (
            (invalid_history_schema.get("properties") or {})
            .get("status", {})
            .get("const")
            != "replaced_before_manifest_freeze"
        )
    ):
        issues.append("manifest_schema_invalid_history_mismatch")
    if (
        manifest.get("properties", {}).get("replacement_policy", {}).get("const")
        != "invalid_case_id_never_reused_replacement_gets_new_id"
    ):
        issues.append("manifest_schema_replacement_policy_mismatch")
    cumulative_schema = registry.get("properties", {}).get(
        "cumulative_novelty_index", {}
    )
    if (
        set(cumulative_schema.get("properties") or {})
        != _CUMULATIVE_NOVELTY_INDEX_KEYS
        or set(cumulative_schema.get("required") or [])
        != _CUMULATIVE_NOVELTY_INDEX_KEYS
        or cumulative_schema.get("additionalProperties") is not False
    ):
        issues.append("registry_schema_cumulative_novelty_index_mismatch")
    if registry.get("properties", {}).get("valid_for_runtime_switch", {}).get("const") is not False:
        issues.append("registry_schema_runtime_switch_mismatch")
    return tuple(dict.fromkeys(issues))


def _load_fixture_wrapper(path: Path, *, expected_keys: frozenset[str]) -> list[Mapping[str, Any]]:
    rows = load_canonical_jsonl(path, validator=None)
    if any(not _exact_keys(row, expected_keys) for row in rows):
        raise ValueError(f"fixture_wrapper_keyset_mismatch:{path.name}")
    return rows


def _validate_negative_fixture_rows(rows: Sequence[Mapping[str, Any]]) -> None:
    fixture_ids: set[str] = set()
    for row in rows:
        fixture_id = row.get("fixture_id")
        expected_issue = row.get("expected_issue")
        input_value = row.get("input")
        if not isinstance(fixture_id, str) or fixture_id in fixture_ids:
            raise ValueError("negative_fixture_id_invalid_or_duplicate")
        fixture_ids.add(fixture_id)
        if not isinstance(expected_issue, str):
            raise ValueError("negative_fixture_expected_issue_invalid")
        issues = validate_app_reachable_input(input_value)
        if expected_issue not in issues:
            raise ValueError(f"negative_fixture_not_rejected:{fixture_id}")


def _validate_legacy_fixture_rows(rows: Sequence[Mapping[str, Any]]) -> None:
    fixture_ids: set[str] = set()
    for row in rows:
        fixture_id = row.get("fixture_id")
        payload = row.get("legacy_payload")
        if not isinstance(fixture_id, str) or fixture_id in fixture_ids:
            raise ValueError("legacy_fixture_id_invalid_or_duplicate")
        fixture_ids.add(fixture_id)
        if row.get("classification") != "legacy_input":
            raise ValueError("legacy_fixture_classification_invalid")
        if row.get("provenance_subtype") != "synthetic_real_user_legacy":
            raise ValueError("legacy_fixture_provenance_invalid")
        if not isinstance(payload, Mapping):
            raise ValueError("legacy_fixture_payload_invalid")
        if set(payload) == _INPUT_KEYS and not validate_app_reachable_input(payload):
            raise ValueError("legacy_fixture_is_current_app_reachable")


def validate_rn_contract_snapshot(contract: Any) -> tuple[str, ...]:
    if not isinstance(contract, Mapping):
        return ("step1_input_contract_mapping_required",)
    issues: list[str] = []
    app = contract.get("app_reachable") or {}
    expected = {
        "text_requirement": "trimmed_memo_or_memo_action_nonempty",
        "emotion_min_count": 1,
        "emotion_unique": True,
        "emotion_types": list(EMOTION_TYPES),
        "strength_types": list(STRENGTH_TYPES),
        "self_insight_type": "自己理解",
        "self_insight_exclusive": True,
        "self_insight_strength": "medium",
        "non_self_insight_multiple_allowed": True,
        "category_min_count": 1,
        "category_unique": True,
        "category_types": list(CATEGORY_TYPES),
        "category_multiple_allowed": True,
        "text_length_limit_added_by_nls_v3": False,
        "submit_condition": "not_submitting_and_text_and_emotion_and_category",
    }
    if app != expected:
        issues.append("step2_policy_rn_contract_mismatch")
    if contract.get("authority") != "current_rn_production_files":
        issues.append("step1_rn_authority_mismatch")
    if contract.get("step1_input_contract_status") != "completed":
        issues.append("step1_input_contract_not_completed")
    return tuple(issues)


def rn_contract_binding_issues() -> tuple[str, ...]:
    issues: list[str] = []
    if sha256_file(STEP1_RECEIPT_PATH) != STEP1_RECEIPT_SHA256:
        issues.append("step1_receipt_hash_drift")
    if sha256_file(STEP1_INPUT_CONTRACT_PATH) != STEP1_INPUT_CONTRACT_SHA256:
        issues.append("step1_input_contract_hash_drift")
        return tuple(issues)
    contract = json.loads(STEP1_INPUT_CONTRACT_PATH.read_text(encoding="utf-8"))
    issues.extend(validate_rn_contract_snapshot(contract))
    return tuple(dict.fromkeys(issues))


def _assert_annotation_projection_guard(valid_rows: Sequence[Mapping[str, Any]]) -> None:
    for sample in valid_rows:
        baseline = project_generation_input(sample)
        annotation_mutation = deepcopy(sample)
        annotation_mutation["coverage"]["structural_variation"][
            "order_variation_eligible"
        ] = not annotation_mutation["coverage"]["structural_variation"][
            "order_variation_eligible"
        ]
        annotation_mutation["semantic_contract"]["relation_codes"].append(
            "EVALUATION_ONLY_SENTINEL"
        )
        if validate_sample_case(annotation_mutation):
            raise ValueError("annotation_probe_mutation_not_contract_valid")
        if not strict_json_equal(project_generation_input(annotation_mutation), baseline):
            raise ValueError("annotation_projection_changed_generation_input")

        forbidden_mutation = deepcopy(sample)
        forbidden_mutation["expected_final_text"] = "forbidden evaluation sentinel"
        if not validate_sample_case(forbidden_mutation):
            raise ValueError("forbidden_annotation_was_accepted")
        try:
            project_generation_input(forbidden_mutation)
        except ValueError:
            pass
        else:
            raise ValueError("forbidden_annotation_reached_projection")


def build_corpus_registry() -> dict[str, Any]:
    _require_frozen_policy_bindings()
    binding_issues = rn_contract_binding_issues()
    if binding_issues:
        raise ValueError("rn_contract_binding_invalid:" + binding_issues[0])
    schema_issues = schema_runtime_binding_issues()
    if schema_issues:
        raise ValueError("schema_runtime_binding_invalid:" + schema_issues[0])
    if not STEP2_TEST_PATH.is_file():
        raise ValueError("step2_test_owner_missing")

    valid_rows = load_canonical_jsonl(VALID_FIXTURE_PATH)
    if any(
        row["source"] != "karen_generated" or row["batch_id"] != "nls3_batch_000"
        for row in valid_rows
    ):
        raise ValueError("valid_contract_fixture_partition_mismatch")
    if len({str(row["case_id"]) for row in valid_rows}) != len(valid_rows):
        raise ValueError("valid_contract_fixture_duplicate_case_id")
    duplicate_probe = build_duplicate_report(valid_rows)
    if any(duplicate_probe["counts"].values()):
        raise ValueError("valid_contract_fixture_duplicate_or_near")
    if not strict_json_equal(duplicate_probe, build_duplicate_report(list(reversed(valid_rows)))):
        raise ValueError("duplicate_report_order_dependent")
    coverage_probe = build_coverage_matrix(valid_rows, batch_id="nls3_batch_000")
    if validate_coverage_matrix(coverage_probe, valid_rows):
        raise ValueError("coverage_matrix_completion_probe_failed")
    _assert_annotation_projection_guard(valid_rows)

    invalid_rows = _load_fixture_wrapper(
        INVALID_FIXTURE_PATH,
        expected_keys=frozenset({"expected_issue", "fixture_id", "input"}),
    )
    _validate_negative_fixture_rows(invalid_rows)
    legacy_rows = _load_fixture_wrapper(
        LEGACY_FIXTURE_PATH,
        expected_keys=frozenset(
            {"classification", "fixture_id", "legacy_payload", "provenance_subtype"}
        ),
    )
    _validate_legacy_fixture_rows(legacy_rows)

    schema_paths = (
        ("sample_case", SAMPLE_SCHEMA_PATH),
        ("coverage_matrix", COVERAGE_SCHEMA_PATH),
        ("sample_batch_manifest", BATCH_MANIFEST_SCHEMA_PATH),
        ("corpus_registry", CORPUS_REGISTRY_SCHEMA_PATH),
    )
    schemas = [
        {
            "role": role,
            "ref": _repo_ref(path),
            "sha256": sha256_file(path),
        }
        for role, path in schema_paths
    ]
    collections = [
        {
            "collection_id": "step2_contract_valid",
            "classification": "karen_generated",
            "provenance_subtype": "contract_fixture_only",
            "status": "available_contract_fixture",
            "storage": "repo_safe_synthetic_fixture",
            "corpus_ref": _repo_ref(VALID_FIXTURE_PATH),
            "corpus_sha256": sha256_file(VALID_FIXTURE_PATH),
            "case_count": len(valid_rows),
            "app_reachable_valid_count": len(valid_rows),
            "counts_toward_karen_minimum": False,
            "raw_body_in_registry": False,
            "private_commitment_policy": "none_repo_safe_synthetic",
        },
        {
            "collection_id": "step2_invalid_contract",
            "classification": "invalid_contract",
            "provenance_subtype": "synthetic_negative_contract_fixture",
            "status": "available_contract_fixture",
            "storage": "repo_safe_synthetic_fixture",
            "corpus_ref": _repo_ref(INVALID_FIXTURE_PATH),
            "corpus_sha256": sha256_file(INVALID_FIXTURE_PATH),
            "case_count": len(invalid_rows),
            "app_reachable_valid_count": 0,
            "counts_toward_karen_minimum": False,
            "raw_body_in_registry": False,
            "private_commitment_policy": "none_repo_safe_synthetic",
        },
        {
            "collection_id": "step2_legacy_input",
            "classification": "legacy_input",
            "provenance_subtype": "synthetic_real_user_legacy",
            "status": "available_contract_fixture",
            "storage": "repo_safe_synthetic_fixture",
            "corpus_ref": _repo_ref(LEGACY_FIXTURE_PATH),
            "corpus_sha256": sha256_file(LEGACY_FIXTURE_PATH),
            "case_count": len(legacy_rows),
            "app_reachable_valid_count": 0,
            "counts_toward_karen_minimum": False,
            "raw_body_in_registry": False,
            "private_commitment_policy": "none_repo_safe_synthetic",
        },
        {
            "collection_id": "real_user_current_valid",
            "classification": "real_user_current_valid",
            "provenance_subtype": "supabase_not_received",
            "status": "not_received",
            "storage": "private_local_only",
            "corpus_ref": None,
            "corpus_sha256": None,
            "case_count": 0,
            "app_reachable_valid_count": 0,
            "counts_toward_karen_minimum": False,
            "raw_body_in_registry": False,
            "private_commitment_policy": "hmac_sha256_private_key_required",
        },
    ]
    aggregate = {
        "contract_fixture_valid": len(valid_rows),
        "invalid_contract": len(invalid_rows),
        "legacy_input": len(legacy_rows),
        "other_ai_generated_reviewed": 0,
        "real_user_current_valid": 0,
        "accepted_karen_minimum": 0,
    }
    owner_path = Path(__file__).resolve()
    test_evidence = {
        "test_ref": _repo_ref(STEP2_TEST_PATH),
        "test_sha256": sha256_file(STEP2_TEST_PATH),
        "positive_fixture_count": len(valid_rows),
        "independent_negative_fixture_count": len(invalid_rows),
        "legacy_fixture_count": len(legacy_rows),
        "required_test_contracts": [
            "app_reachable_positive_and_independent_negative",
            "rn_contract_and_hash_drift",
            "canonical_json_and_jsonl_adversarial",
            "exact_normalized_near_and_order_determinism",
            "schema_runtime_parity",
            "annotation_projection_allowlist",
            "private_hmac_and_shareable_source_boundary",
            "coverage_manifest_registry_recomputation",
            "batch001_100_case_transition_boundary",
            "invalid_replacement_lineage_and_retired_id_nonreuse",
        ],
        "live_completion_probes_passed": True,
    }
    cumulative_index = {
        "registered_case_ids": sorted(str(row["case_id"]) for row in valid_rows),
        "retired_invalid_case_ids": [],
        "exact_input_identities": sorted(exact_input_identity(row) for row in valid_rows),
        "normalized_input_identities": sorted(
            normalized_input_identity(row) for row in valid_rows
        ),
        "accepted_batch_refs": [],
        "reference_case_count": len(valid_rows),
        "accepted_karen_case_count": 0,
        "replacement_case_id_reuse_allowed": False,
        "identity_scope": "repo_safe_synthetic_only_private_sources_require_hmac",
    }
    payload = {
        "schema_version": CORPUS_REGISTRY_SCHEMA_VERSION,
        "design_sha256": DESIGN_SHA256,
        "parent_step1_ref": _repo_ref(STEP1_RECEIPT_PATH),
        "parent_step1_sha256": STEP1_RECEIPT_SHA256,
        "schemas": schemas,
        "validator_owner": {
            "ref": _repo_ref(owner_path),
            "sha256": sha256_file(owner_path),
        },
        "test_evidence": test_evidence,
        "policies": {
            "validator_policy_sha256": VALIDATOR_POLICY_SHA256,
            "duplicate_policy_sha256": DUPLICATE_POLICY_SHA256,
            "annotation_projection": "explicit_input_allowlist_only",
            "raw_real_user_repo_allowed": False,
            "private_real_user_identity": "versioned_domain_separated_hmac_private_key",
        },
        "collections": collections,
        "aggregate_counts": aggregate,
        "cumulative_novelty_index": cumulative_index,
        "batch001_status": "not_created_post_step2_transition",
        "completion_condition": "strict_schema_validator_duplicate_registry_annotation_guard_green",
        "step2_status": "completed",
        "next_step_authority": "create_and_freeze_batch001_then_step3_only",
        "valid_for_batch001_creation": True,
        "valid_for_runtime_switch": False,
        "body_free": True,
    }
    return {"registry_id": "nls3registry_" + sha256_json(payload)[:16], **payload}


def validate_corpus_registry(value: Any) -> tuple[str, ...]:
    if not _exact_keys(value, _REGISTRY_KEYS):
        return (_issue("corpus_registry", "keyset_mismatch"),)
    collections = value.get("collections")
    if not isinstance(collections, list) or any(
        not _exact_keys(row, _COLLECTION_KEYS) for row in collections
    ):
        return (_issue("corpus_registry.collections", "shape_invalid"),)
    if not _exact_keys(
        value.get("cumulative_novelty_index"),
        _CUMULATIVE_NOVELTY_INDEX_KEYS,
    ):
        return (_issue("corpus_registry.cumulative_novelty_index", "shape_invalid"),)
    try:
        expected = build_corpus_registry()
    except (ValueError, OSError, UnicodeError) as exc:
        return (_issue("corpus_registry", f"live_rebuild_failed_{type(exc).__name__}"),)
    return () if strict_json_equal(dict(value), expected) else (
        _issue("corpus_registry", "recomputed_value_mismatch"),
    )


def batch001_creation_preflight(value: Mapping[str, Any]) -> tuple[str, ...]:
    if not isinstance(value, Mapping):
        return ("corpus_registry_mapping_required",)
    issues = list(validate_corpus_registry(value))
    if value.get("batch001_status") != "not_created_post_step2_transition":
        issues.append("batch001_status_invalid")
    if value.get("valid_for_batch001_creation") is not True:
        issues.append("batch001_creation_not_authorized")
    if value.get("valid_for_runtime_switch") is not False:
        issues.append("runtime_switch_wrongly_authorized")
    if value.get("next_step_authority") != "create_and_freeze_batch001_then_step3_only":
        issues.append("next_step_authority_invalid")
    return tuple(dict.fromkeys(issues))


def write_registry() -> None:
    value = build_corpus_registry()
    REGISTRY_PATH.write_bytes(canonical_json_bytes(value) + b"\n")


__all__ = [
    "BATCH_MANIFEST_SCHEMA_PATH",
    "BATCH_MANIFEST_SCHEMA_VERSION",
    "CATEGORY_TYPES",
    "CORPUS_REGISTRY_SCHEMA_PATH",
    "CORPUS_REGISTRY_SCHEMA_VERSION",
    "COVERAGE_FAMILIES",
    "COVERAGE_SCHEMA_PATH",
    "COVERAGE_SCHEMA_VERSION",
    "DEPTH_LEVELS",
    "DESIGN_SHA256",
    "DUPLICATE_POLICY",
    "DUPLICATE_POLICY_SHA256",
    "EMOTION_TYPES",
    "INVALID_FIXTURE_PATH",
    "LEGACY_FIXTURE_PATH",
    "SHAREABLE_SYNTHETIC_SOURCES",
    "REGISTRY_PATH",
    "SAMPLE_SCHEMA_PATH",
    "SAMPLE_SCHEMA_VERSION",
    "STEP1_INPUT_CONTRACT_PATH",
    "STEP1_INPUT_CONTRACT_SHA256",
    "STEP1_RECEIPT_PATH",
    "STEP1_RECEIPT_SHA256",
    "STEP2_TEST_PATH",
    "STRENGTH_TYPES",
    "STRUCTURAL_VARIATION_KEYS",
    "VALIDATOR_POLICY",
    "VALIDATOR_POLICY_SHA256",
    "VALID_FIXTURE_PATH",
    "batch001_creation_preflight",
    "build_batch_manifest",
    "build_corpus_registry",
    "build_coverage_matrix",
    "build_duplicate_report",
    "canonical_json_text",
    "case_commitment",
    "corpus_set_commitment",
    "ecmascript_trim",
    "exact_input_identity",
    "load_canonical_jsonl",
    "load_canonical_json",
    "normalized_input_identity",
    "policy_binding_issues",
    "private_input_identity_hmac",
    "private_case_commitment_hmac",
    "private_corpus_set_commitment_hmac",
    "project_generation_input",
    "rn_contract_binding_issues",
    "schema_runtime_binding_issues",
    "sha256_file",
    "sha256_json",
    "strict_json_loads",
    "strict_json_equal",
    "validate_app_reachable_input",
    "validate_batch_manifest",
    "validate_corpus_registry",
    "validate_coverage_matrix",
    "validate_sample_case",
    "validate_rn_contract_snapshot",
    "write_registry",
]
