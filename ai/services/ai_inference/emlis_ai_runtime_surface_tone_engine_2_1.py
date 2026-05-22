# -*- coding: utf-8 -*-
from __future__ import annotations

"""Runtime Surface Quality Step9: Tone Engine 2.1 for EmlisAI.

This module is a meta-only tone quality layer.  It measures and constrains
Emlis' observation distance without adding meaning, without completed fallback
sentences, and without storing raw input or public ``comment_text`` bodies in
reports.  Text is used only in-memory to detect guard patterns.
"""

from collections import Counter
from collections.abc import Iterable, Mapping
import re
from typing import Any, Sequence

RUNTIME_SURFACE_TONE_ENGINE_2_1_VERSION = "emlis.runtime_surface_tone_engine.v2_1"
RUNTIME_SURFACE_TONE_ENGINE_2_1_POLICY_VERSION = "emlis.runtime_surface_tone_policy.v2_1"
RUNTIME_SURFACE_TONE_ENGINE_2_1_REPORT_VERSION = "emlis.runtime_surface_tone_engine_report.v2_1"
RUNTIME_SURFACE_TONE_ENGINE_2_1_STEP = "Step9_Tone_Engine_2_1"
RUNTIME_SURFACE_TONE_ENGINE_2_1_TARGET_LAYER = "tone_engine_2_1_blind_qa"

_FORBIDDEN_TEXT_PAYLOAD_KEYS = {
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
    "memo",
    "memo_text",
    "memoText",
    "current_input",
    "currentInput",
    "comment_text",
    "commentText",
    "public_comment_text",
    "candidate_comment_text",
    "reply_text",
    "replyText",
    "surface_text",
    "realized_text",
    "body",
    "text",
}

_FORBIDDEN_TRUE_FLAGS = {
    "raw_input_included",
    "raw_text_included",
    "comment_text_included",
    "comment_text_body_included",
    "comment_text_key_written",
    "response_shape_changed",
    "public_response_key_change",
    "api_route_changed",
    "db_physical_name_changed",
    "rn_visible_contract_changed",
    "rn_visible_title_changed",
    "display_gate_relaxed",
    "grounding_gate_relaxed",
    "template_gate_relaxed",
    "reader_gate_relaxed",
    "gate_relaxed",
    "public_release_applied",
    "product_gate_public_release_applied",
    "product_gate_achieved",
    "external_ai_used",
    "local_llm_used",
    "fixed_sentence_template_added_by_tone",
    "fixed_sentence_template_used_by_tone",
    "input_specific_tone_branch_added",
    "meaning_added_by_tone_engine_2_1",
    "tone_engine_2_1_uses_fixture_strings",
    "tone_engine_2_1_relaxes_gate",
}

_SPACE_RE = re.compile(r"\s+")
_TRIM = " \t\r\n　、,。.!！?？『』\"'「」（）()[]【】"

# These are guard patterns for tone, not text templates.  They are only used to
# classify visible-output risk and are never inserted into an observation.
_TONE_PATTERNS: tuple[tuple[str, str, re.Pattern[str]], ...] = (
    ("diagnostic_tone", "safety", re.compile(r"(?:診断|治療|病気|症状|トラウマ|障害|発達障害|ADHD|うつ|鬱|PTSD|心理学的|医学的)")),
    ("advice_like", "safety", re.compile(r"(?:してください|しましょう|するべき|しなければ|行動しましょう|正解は|まずは[^。\n]{0,24}(?:やってみ|行動|相談|休んで))")),
    ("action_instruction", "safety", re.compile(r"(?:行動して|動いてみて|変えましょう|決めましょう|連絡しましょう|距離を取りましょう)")),
    ("personality_claim", "safety", re.compile(r"(?:あなたは(?:本当は|根が|性格的に|いつも)|本質は|性格だから|依存している|弱い人)")),
    ("cause_overclaim", "safety", re.compile(r"(?:原因は|理由はひとつ|だからこそ必ず|本当の原因)")),
    ("over_empathy", "distance", re.compile(r"(?:つらかったね|よく頑張った|もう大丈夫|必ず良く|安心してください|泣いていい|全部受け止めます)")),
    ("too_close", "distance", re.compile(r"(?:ずっとそばに|抱きしめ|絶対味方|何があっても味方|一緒なら大丈夫)")),
    ("generic_comfort", "distance", re.compile(r"(?:よくあること|誰でも|大丈夫です|小さく扱いません|軽く扱いません|一緒に見ます|無理しなくていい)")),
    ("cold_tone", "distance", re.compile(r"(?:関係ありません|ただの反応です|それだけです|終わりです|問題ありません)")),
    ("generic_generalization", "read_feeling", re.compile(r"(?:多くの人が|一般的には|よくある反応|自然なことです)")),
)

_ENDING_TEXT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("diagnostic", re.compile(r"(?:診断です|症状です|病気です)。?$")),
    ("advice", re.compile(r"(?:してください|しましょう|するといいです|するべきです)。?$")),
    ("comfort", re.compile(r"(?:大丈夫です|安心してください|無理しなくていいです)。?$")),
    ("ne_desu", re.compile(r"のですね。?$")),
    ("visible", re.compile(r"見えています。?$")),
    ("remain", re.compile(r"(?:残っています|残っていると思います|残っているようです)。?$")),
    ("overlap", re.compile(r"(?:重なっています|並んでいます)。?$")),
    ("teimasu", re.compile(r"ています。?$")),
    ("masu", re.compile(r"ます。?$")),
    ("aru", re.compile(r"あります。?$")),
    ("plain_desu", re.compile(r"です。?$")),
)

_ENDING_KEY_FAMILY = {
    "teimasu": "teimasu_observation",
    "masu": "masu_observation",
    "aru": "aru_observation",
    "nokoru": "remain_observation",
    "tsuzuku": "continue_observation",
    "kuru": "movement_observation",
    "deru": "movement_observation",
    "oku": "placement_observation",
    "motsu": "hold_observation",
    "narabu": "parallel_observation",
    "tamotsu": "hold_observation",
    "atsukau": "handling_observation",
    "kimaranai": "undecided_observation",
}

_TONE_GUARD_TO_QA_DIMENSION = {
    "diagnostic_tone": "distance",
    "advice_like": "distance",
    "action_instruction": "distance",
    "personality_claim": "distance",
    "cause_overclaim": "evidence_retention",
    "over_empathy": "distance",
    "too_close": "distance",
    "generic_comfort": "read_feeling",
    "cold_tone": "distance",
    "generic_generalization": "read_feeling",
    "ending_family_repetition": "naturalness",
}


def _clean(value: Any, *, limit: int = 0) -> str:
    if value is None:
        return ""
    text = _SPACE_RE.sub(" ", str(value).replace("\u3000", " ").replace("\r", " ").replace("\n", " ")).strip(_TRIM)
    if limit > 0 and len(text) > limit:
        text = text[:limit].rstrip(_TRIM)
    return text


def _clean_token(value: Any) -> str:
    return re.sub(r"[^0-9a-zA-Z_\-.]+", "_", str(value or "").strip().lower()).strip("_")


def _listify(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, (tuple, set)):
        return list(value)
    return [value]


def _dedupe(values: Iterable[Any] | Any) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in _listify(values):
        text = _clean(item)
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def _safe_mapping(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    return {str(k): v for k, v in value.items()}


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        if isinstance(value, bool):
            return int(value)
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _json_safe_value(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, Mapping):
        return _json_safe_mapping(value)
    if isinstance(value, (list, tuple, set)):
        return [_json_safe_value(item) for item in value]
    return str(value)


def _json_safe_mapping(value: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    out: dict[str, Any] = {}
    for key, item in value.items():
        key_text = str(key)
        if key_text in _FORBIDDEN_TEXT_PAYLOAD_KEYS:
            continue
        out[key_text] = _json_safe_value(item)
    return out


def _contains_forbidden_text_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key) in _FORBIDDEN_TEXT_PAYLOAD_KEYS:
                return True
            if _contains_forbidden_text_payload_key(item):
                return True
        return False
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_text_payload_key(item) for item in value)
    return False


def assert_runtime_surface_tone_engine_2_1_meta_only(value: Mapping[str, Any], *, source: str = "tone_engine_2_1") -> None:
    if _contains_forbidden_text_payload_key(value):
        raise ValueError(f"{source} must stay meta-only and must not include text payload keys")
    for key in _FORBIDDEN_TRUE_FLAGS:
        if value.get(key) is True:
            raise ValueError(f"{source} violates fixed contract: {key}=true")


def _surface_rows(surface_realization: Any = None, *, comment_text: Any = "") -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if surface_realization is not None and hasattr(surface_realization, "surface_lines"):
        for index, line in enumerate(list(getattr(surface_realization, "surface_lines", []) or []), start=1):
            rows.append(
                {
                    "sentence_id": _clean(getattr(line, "sentence_id", "")) or f"line_{index}",
                    "line_role": _clean(getattr(line, "line_role", "")) or "unknown",
                    # internal only, removed from reports
                    "_surface_text": _clean(getattr(line, "surface_text", "")),
                    "ending_key": _clean(getattr(line, "ending_key", "")),
                    "tone_policy_key": _clean(getattr(line, "tone_policy_key", "")),
                    "temperature_key": _clean(getattr(line, "temperature_key", "")),
                    "read_feeling_policy_key": _clean(getattr(line, "read_feeling_policy_key", "")),
                    "closing_policy_key": _clean(getattr(line, "closing_policy_key", "")),
                }
            )
    elif isinstance(surface_realization, Mapping):
        items = surface_realization.get("surface_lines") or surface_realization.get("surface_component_rows") or []
        for index, item in enumerate(list(items or []), start=1):
            if not isinstance(item, Mapping):
                continue
            rows.append(
                {
                    "sentence_id": _clean(item.get("sentence_id")) or f"line_{index}",
                    "line_role": _clean(item.get("line_role")) or "unknown",
                    "_surface_text": _clean(item.get("surface_text")),
                    "ending_key": _clean(item.get("ending_key")),
                    "tone_policy_key": _clean(item.get("tone_policy_key")),
                    "temperature_key": _clean(item.get("temperature_key")),
                    "read_feeling_policy_key": _clean(item.get("read_feeling_policy_key")),
                    "closing_policy_key": _clean(item.get("closing_policy_key")),
                }
            )
    if not rows:
        text = str(comment_text or "")
        for index, line in enumerate([line.strip() for line in text.splitlines() if line.strip()], start=1):
            rows.append(
                {
                    "sentence_id": f"text_line_{index}",
                    "line_role": "text_line",
                    "_surface_text": _clean(line),
                    "ending_key": "",
                    "tone_policy_key": "",
                    "temperature_key": "",
                    "read_feeling_policy_key": "",
                    "closing_policy_key": "",
                }
            )
    return rows


def ending_family_key(value: Any, *, text: Any = "") -> str:
    key = _clean_token(value)
    if key in _ENDING_KEY_FAMILY:
        return _ENDING_KEY_FAMILY[key]
    for marker, pattern in _ENDING_TEXT_PATTERNS:
        if pattern.search(str(text or "")):
            if marker == "remain":
                return "remain_observation"
            if marker == "overlap":
                return "overlap_observation"
            if marker in {"visible", "teimasu"}:
                return "teimasu_observation"
            return f"{marker}_ending"
    if key:
        if "remain" in key or "nokor" in key or "residue" in key:
            return "remain_observation"
        if "overlap" in key or "coexist" in key:
            return "overlap_observation"
        if "advice" in key:
            return "advice_ending"
        return f"{key}_ending"
    return "unknown_ending"


def _run_max(values: Sequence[str]) -> int:
    max_run = 0
    cur = 0
    prev = object()
    for value in values:
        if value == prev:
            cur += 1
        else:
            cur = 1
            prev = value
        max_run = max(max_run, cur)
    return max_run


def _hit_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        text = str(row.get("_surface_text") or "")
        if not text:
            continue
        for reason, family, pattern in _TONE_PATTERNS:
            if pattern.search(text):
                hits.append(
                    {
                        "sentence_id": _clean(row.get("sentence_id")) or f"line_{index}",
                        "line_role": _clean(row.get("line_role")) or "unknown",
                        "reason": reason,
                        "reason_family": family,
                        "qa_dimension": _TONE_GUARD_TO_QA_DIMENSION.get(reason, "distance"),
                    }
                )
    return hits


def _blind_qa_meta(blind_qa: Mapping[str, Any] | None) -> dict[str, Any]:
    qa = _safe_mapping(blind_qa)
    read = _safe_float(qa.get("read_feeling_score"))
    distance = _safe_float(qa.get("distance_score"))
    naturalness = _safe_float(qa.get("naturalness_score"))
    return {
        "blind_qa_required": True,
        "blind_qa_ready": bool(qa and read is not None),
        "blind_qa_score_present": read is not None,
        "read_feeling_score": read,
        "distance_score": distance,
        "naturalness_score": naturalness,
        "read_feeling_source": "blind_qa_review_rating" if read is not None else "blind_qa_required_not_machine_metrics",
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "read_feeling_auto_estimation_allowed": False,
    }


def build_runtime_surface_tone_engine_2_1_policy_meta(
    *,
    coverage_group: Any = "",
    relation_types: Iterable[Any] | Any | None = None,
    meta: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "version": RUNTIME_SURFACE_TONE_ENGINE_2_1_POLICY_VERSION,
        "tone_engine_2_1_version": RUNTIME_SURFACE_TONE_ENGINE_2_1_VERSION,
        "source_step": RUNTIME_SURFACE_TONE_ENGINE_2_1_STEP,
        "target_layer": RUNTIME_SURFACE_TONE_ENGINE_2_1_TARGET_LAYER,
        "coverage_group": _clean_token(coverage_group) or "unknown",
        "relation_types": _dedupe(relation_types),
        "distance_policy_enabled": True,
        "read_feeling_policy_enabled": True,
        "ending_family_policy_enabled": True,
        "over_empathy_guard_enabled": True,
        "diagnostic_tone_guard_enabled": True,
        "advice_like_guard_enabled": True,
        "personality_claim_guard_enabled": True,
        "generic_generalization_guard_enabled": True,
        "generic_comfort_guard_enabled": True,
        "tone_engine_2_1_is_surface_constraint": True,
        "tone_engine_2_1_is_not_post_gate_decoration": True,
        "blind_qa_required_for_completion": True,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "meaning_added_by_tone_engine_2_1": False,
        "fixed_sentence_template_added_by_tone": False,
        "input_specific_tone_branch_added": False,
        "tone_engine_2_1_uses_fixture_strings": False,
        "tone_engine_2_1_relaxes_gate": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_body_included": False,
        "meta": _json_safe_mapping(meta),
    }
    assert_runtime_surface_tone_engine_2_1_meta_only(payload, source="tone_engine_2_1_policy")
    return payload


def build_runtime_surface_tone_engine_2_1_report(
    *,
    comment_text: Any = "",
    surface_realization: Any = None,
    tone_policy: Mapping[str, Any] | None = None,
    blind_qa: Mapping[str, Any] | None = None,
    composer_meta: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    rows = _surface_rows(surface_realization, comment_text=comment_text)
    if not rows and isinstance(composer_meta, Mapping):
        surface = composer_meta.get("surface_realizer")
        if isinstance(surface, Mapping):
            rows = _surface_rows(surface)

    hits = _hit_rows(rows)
    reason_counter = Counter(hit["reason"] for hit in hits)
    family_counter = Counter(hit["reason_family"] for hit in hits)
    qa_counter = Counter(hit["qa_dimension"] for hit in hits)
    ending_families = [ending_family_key(row.get("ending_key"), text=row.get("_surface_text")) for row in rows]
    ending_family_counts = Counter(ending_families)
    same_ending_family_run_max = _run_max(ending_families)
    same_ending_family_count = max(ending_family_counts.values() or [0])
    ending_family_repetition_major = same_ending_family_run_max >= 3 or same_ending_family_count >= 4

    blocker_reasons = list(dict.fromkeys([hit["reason"] for hit in hits]))
    if ending_family_repetition_major and "ending_family_repetition" not in blocker_reasons:
        blocker_reasons.append("ending_family_repetition")
        qa_counter["naturalness"] += 1

    policy = _safe_mapping(tone_policy)
    qa_meta = _blind_qa_meta(blind_qa)
    tone_major_count = len(hits) + (1 if ending_family_repetition_major else 0)
    safety_major_count = family_counter.get("safety", 0)
    distance_major_count = family_counter.get("distance", 0)
    read_feeling_machine_warning_count = family_counter.get("read_feeling", 0)
    report = {
        "version": RUNTIME_SURFACE_TONE_ENGINE_2_1_REPORT_VERSION,
        "tone_engine_2_1_version": RUNTIME_SURFACE_TONE_ENGINE_2_1_VERSION,
        "tone_engine_2_1_policy_version": RUNTIME_SURFACE_TONE_ENGINE_2_1_POLICY_VERSION,
        "source_step": RUNTIME_SURFACE_TONE_ENGINE_2_1_STEP,
        "target_layer": RUNTIME_SURFACE_TONE_ENGINE_2_1_TARGET_LAYER,
        "tone_engine_2_1_ready": True,
        "step9_tone_engine_2_1_ready": True,
        "line_count": len(rows),
        "guarded_sentence_ids": [str(row.get("sentence_id") or f"line_{i}") for i, row in enumerate(rows, start=1)],
        "tone_guard_major_count": tone_major_count,
        "tone_guard_hit_count": len(hits),
        "tone_engine_2_1_major_count": tone_major_count,
        "tone_safety_major_count": safety_major_count,
        "tone_distance_major_count": distance_major_count,
        "tone_read_feeling_machine_warning_count": read_feeling_machine_warning_count,
        "tone_naturalness_major_count": 1 if ending_family_repetition_major else 0,
        "tone_guard_hits": hits,
        "tone_guard_reasons": blocker_reasons,
        "blocker_reasons": blocker_reasons,
        "tone_reason_counts": dict(reason_counter),
        "tone_reason_family_counts": dict(family_counter),
        "tone_qa_dimension_warning_counts": dict(qa_counter),
        "diagnostic_tone_count": reason_counter.get("diagnostic_tone", 0),
        "advice_like_count": reason_counter.get("advice_like", 0) + reason_counter.get("action_instruction", 0),
        "action_instruction_count": reason_counter.get("action_instruction", 0),
        "personality_claim_count": reason_counter.get("personality_claim", 0),
        "cause_overclaim_count": reason_counter.get("cause_overclaim", 0),
        "over_empathy_count": reason_counter.get("over_empathy", 0),
        "too_close_count": reason_counter.get("too_close", 0),
        "cold_tone_count": reason_counter.get("cold_tone", 0),
        "generic_comfort_count": reason_counter.get("generic_comfort", 0),
        "generic_generalization_count": reason_counter.get("generic_generalization", 0),
        "ending_family_sequence": ending_families,
        "ending_family_counts": dict(ending_family_counts),
        "same_ending_family_run_max": same_ending_family_run_max,
        "same_ending_family_count": same_ending_family_count,
        "ending_family_repetition_major": ending_family_repetition_major,
        "ending_family_repetition_major_count": 1 if ending_family_repetition_major else 0,
        "distance_guard_passed": distance_major_count == 0,
        "safety_tone_guard_passed": safety_major_count == 0,
        "naturalness_tone_guard_passed": not ending_family_repetition_major,
        "read_feeling_machine_warning_present": read_feeling_machine_warning_count > 0,
        "passed": tone_major_count == 0,
        "release_blocker": tone_major_count > 0,
        "tone_engine_2_1_passed": tone_major_count == 0,
        "tone_engine_2_1_release_blocker": tone_major_count > 0,
        "tone_policy_version": policy.get("version") or policy.get("tone_policy_version") or RUNTIME_SURFACE_TONE_ENGINE_2_1_POLICY_VERSION,
        "tone_policy_keys": _dedupe(policy.get("guard_keys")),
        "blind_qa_required_for_tone_completion": True,
        "tone_completion_requires_blind_qa": True,
        "machine_metrics_can_clear_tone_safety": True,
        "machine_metrics_can_clear_read_feeling": False,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "read_feeling_auto_estimation_allowed": False,
        "read_feeling_score": qa_meta["read_feeling_score"],
        "read_feeling_source": qa_meta["read_feeling_source"],
        "blind_qa_ready": qa_meta["blind_qa_ready"],
        "blind_qa_required": True,
        "meaning_added": False,
        "meaning_added_by_tone_engine_2_1": False,
        "meaning_added_by_tone_policy": False,
        "post_gate_decoration": False,
        "fixed_sentence_template_added_by_tone": False,
        "fixed_sentence_template_used_by_tone": False,
        "input_specific_tone_branch_added": False,
        "tone_engine_2_1_uses_fixture_strings": False,
        "tone_engine_2_1_relaxes_gate": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "comment_text_key_written": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
    }
    assert_runtime_surface_tone_engine_2_1_meta_only(report, source="tone_engine_2_1_report")
    return report


def normalize_tone_engine_2_1_to_scorecard_event(report: Mapping[str, Any] | None) -> dict[str, Any]:
    data = _safe_mapping(report)
    reasons = _dedupe(data.get("tone_guard_reasons") or data.get("blocker_reasons"))
    event = {
        "tone_engine_2_1_version": data.get("tone_engine_2_1_version") or RUNTIME_SURFACE_TONE_ENGINE_2_1_VERSION,
        "tone_engine_2_1_ready": bool(data.get("tone_engine_2_1_ready") or data.get("step9_tone_engine_2_1_ready")),
        "step9_tone_engine_2_1_ready": bool(data.get("step9_tone_engine_2_1_ready") or data.get("tone_engine_2_1_ready")),
        "tone_guard_major_count": _safe_int(data.get("tone_guard_major_count"), 0),
        "tone_engine_2_1_major_count": _safe_int(data.get("tone_engine_2_1_major_count"), _safe_int(data.get("tone_guard_major_count"), 0)),
        "tone_safety_major_count": _safe_int(data.get("tone_safety_major_count"), 0),
        "tone_distance_major_count": _safe_int(data.get("tone_distance_major_count"), 0),
        "tone_naturalness_major_count": _safe_int(data.get("tone_naturalness_major_count"), 0),
        "tone_read_feeling_machine_warning_count": _safe_int(data.get("tone_read_feeling_machine_warning_count"), 0),
        "tone_guard_reasons": reasons,
        "tone_engine_2_1_reasons": reasons,
        "tone_diagnostic_count": _safe_int(data.get("diagnostic_tone_count"), 0),
        "tone_advice_count": _safe_int(data.get("advice_like_count"), 0),
        "tone_personality_claim_count": _safe_int(data.get("personality_claim_count"), 0),
        "tone_over_empathy_count": _safe_int(data.get("over_empathy_count"), 0),
        "tone_generic_count": _safe_int(data.get("generic_comfort_count"), 0) + _safe_int(data.get("generic_generalization_count"), 0),
        "tone_ending_family_repetition_major_count": _safe_int(data.get("ending_family_repetition_major_count"), 0),
        "same_ending_family_run_max": _safe_int(data.get("same_ending_family_run_max"), 0),
        "tone_guard_passed": bool(data.get("passed", _safe_int(data.get("tone_guard_major_count"), 0) == 0)) and _safe_int(data.get("tone_guard_major_count"), 0) == 0,
        "tone_meaning_added": bool(data.get("meaning_added") or data.get("meaning_added_by_tone_engine_2_1") or data.get("meaning_added_by_tone_policy")),
        "tone_completion_requires_blind_qa": True,
        "read_feeling_requires_blind_qa": True,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "read_feeling_score": None,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
    }
    assert_runtime_surface_tone_engine_2_1_meta_only(event, source="tone_engine_2_1_scorecard_event")
    return event


__all__ = [
    "RUNTIME_SURFACE_TONE_ENGINE_2_1_POLICY_VERSION",
    "RUNTIME_SURFACE_TONE_ENGINE_2_1_REPORT_VERSION",
    "RUNTIME_SURFACE_TONE_ENGINE_2_1_STEP",
    "RUNTIME_SURFACE_TONE_ENGINE_2_1_TARGET_LAYER",
    "RUNTIME_SURFACE_TONE_ENGINE_2_1_VERSION",
    "assert_runtime_surface_tone_engine_2_1_meta_only",
    "build_runtime_surface_tone_engine_2_1_policy_meta",
    "build_runtime_surface_tone_engine_2_1_report",
    "ending_family_key",
    "normalize_tone_engine_2_1_to_scorecard_event",
]
