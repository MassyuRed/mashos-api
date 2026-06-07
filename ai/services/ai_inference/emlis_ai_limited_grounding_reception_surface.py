# -*- coding: utf-8 -*-
from __future__ import annotations

"""Limited-grounding reception surface helper for EmlisAI public observation.

P4 owns the internal, body-free plan used when a ``limited_grounding`` input is
allowed to return a labelled two-stage public observation.  This is not a new
public response contract, does not add RN/API/DB fields, does not promote
low-information inputs, and does not store raw input or generated body in meta.
"""

from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Final
import json
import re

LIMITED_GROUNDING_RECEPTION_SURFACE_PLAN_SCHEMA_VERSION: Final = (
    "cocolon.emlis.limited_grounding_reception_surface_plan.v1"
)
LIMITED_GROUNDING_RECEPTION_SURFACE_SOURCE_PHASE: Final = "LimitedGroundingReception_Plan"
LIMITED_GROUNDING_RECEPTION_SURFACE_SHAPE: Final = "labelled_two_stage"
LIMITED_GROUNDING_MATERIAL_QUALITY: Final = "limited_grounding"
LIMITED_GROUNDING_RESPONSE_KIND: Final = "limited_grounding_observation"

_FORBIDDEN_META_TEXT_KEYS: Final[frozenset[str]] = frozenset(
    {
        "raw_input",
        "rawInput",
        "raw_text",
        "rawText",
        "input_text",
        "inputText",
        "memo",
        "memo_text",
        "memoText",
        "memo_action",
        "memoAction",
        "current_input",
        "currentInput",
        "comment_text",
        "commentText",
        "comment_text_body",
        "commentTextBody",
        "candidate_comment_text",
        "candidateCommentText",
        "public_comment_text",
        "publicCommentText",
        "reply_text",
        "replyText",
        "surface_text",
        "surfaceText",
        "observation_text",
        "observationText",
        "reception_text",
        "receptionText",
        "candidate_body",
        "candidateBody",
        "surface_body",
        "surfaceBody",
        "generated_candidate_text",
        "original_comment_text",
        "body",
        "text",
    }
)
_META_REQUIRED_KEYS: Final[frozenset[str]] = frozenset(
    {
        "schema_version",
        "source_phase",
        "limited_grounding_reception_surface_used",
        "material_quality",
        "response_kind",
        "surface_shape",
        "observation_depth",
        "grounding_scope",
        "reception_required",
        "question_policy",
        "visible_material_slots",
        "unknown_slots",
        "semantic_material_ids",
        "semantic_material_count",
        "observation_focus",
        "surface_contract",
        "meta_boundary",
        "body_free",
        "raw_input_included",
        "comment_text_body_included",
        "fixed_fallback_used",
        "case_specific_route_used",
        "exact_fixture_surface_used",
    }
)
_SLOT_LABELS: Final[dict[str, str]] = {
    "emotion_direction": "気持ちの向き",
    "relationship": "人や自分との関係の入口",
    "target": "向いている対象",
    "change": "変化の入口",
    "value": "大切にしたいもの",
    "time": "今という時間感覚",
    "action": "次に向かう動き",
    "event": "出来事の入口",
}
_SEMANTIC_MATERIAL_PATTERNS: Final[tuple[tuple[str, tuple[str, ...]], ...]] = (
    (
        "recovered_energy",
        (
            "気力",
            "やる気力",
            "やってみたい",
            "出来るかもしれない",
            "できるかもしれない",
            "挑戦",
            "頑張",
        ),
    ),
    (
        "future_intention",
        (
            "このタイミング",
            "逃した",
            "次どう頑張",
            "つぎどう頑張",
            "していきたい",
            "出会えたら",
            "過ごしていきたい",
            "知って行きたい",
            "知っていきたい",
        ),
    ),
    (
        "relationship_wish",
        (
            "そば",
            "側に",
            "恋愛",
            "出会え",
            "素敵な人",
            "存在",
            "甘え",
        ),
    ),
    (
        "comparison_baseline_shift",
        (
            "昨日の自分",
            "人と比べ",
            "比べる相手",
            "他の誰か",
        ),
    ),
    (
        "small_change_preservation",
        (
            "小さな変化",
            "少し出来",
            "少しでき",
            "少し勇気",
            "少し気持ちを言葉",
            "言葉に出来",
            "言葉にでき",
            "少し前に進",
            "ほんの少し前",
        ),
    ),
    (
        "value_preservation",
        (
            "大事",
            "大切",
        ),
    ),
    (
        "self_observation",
        (
            "なぜ",
            "なんで",
            "どうして",
            "自分について",
            "思ったんだろう",
            "基準",
        ),
    ),
)
_RELATION_ID_SEMANTIC_ALIASES: Final[dict[str, tuple[str, ...]]] = {
    "self_understanding_learning": ("self_observation",),
    "value_or_self_understanding_material": ("self_observation", "value_preservation"),
    "boundary_or_transition": ("future_intention",),
    "relationship_material": ("relationship_wish",),
    "support_received_material": ("relationship_wish",),
    # P7: material bundle can now pass these body-free semantic ids directly.
    "recovered_energy": ("recovered_energy",),
    "future_intention": ("future_intention",),
    "relationship_wish": ("relationship_wish",),
    "comparison_baseline_shift": ("comparison_baseline_shift",),
    "small_change_preservation": ("small_change_preservation",),
    "value_preservation": ("value_preservation",),
    "self_observation": ("self_observation",),
}
_MUST_NOT_ASSERT: Final[tuple[str, ...]] = (
    "cause",
    "specific_event",
    "other_person_intent",
    "personality_trait",
    "recovery_completed",
)
_SPACE_RE: Final = re.compile(r"\s+")


def build_limited_grounding_reception_surface_plan(
    *,
    current_input: Mapping[str, Any] | None,
    material_route: Any,
    surface_requirement: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a body-free internal plan for limited-grounding reception."""

    route_meta = _material_route_meta(material_route)
    requirement = _as_mapping(surface_requirement)
    material_quality = _material_quality(route_meta, requirement)
    visible_slots = _dedupe(route_meta.get("visible_material_slots") or ())
    unknown_slots = _dedupe(route_meta.get("unknown_slots") or ())
    semantic_material_ids = _semantic_material_ids(
        current_input=current_input,
        material_route_meta=route_meta,
    )
    used = material_quality == LIMITED_GROUNDING_MATERIAL_QUALITY
    plan: dict[str, Any] = {
        "schema_version": LIMITED_GROUNDING_RECEPTION_SURFACE_PLAN_SCHEMA_VERSION,
        "source_phase": LIMITED_GROUNDING_RECEPTION_SURFACE_SOURCE_PHASE,
        "limited_grounding_reception_surface_used": bool(used),
        "material_quality": material_quality,
        "response_kind": LIMITED_GROUNDING_RESPONSE_KIND,
        "surface_shape": LIMITED_GROUNDING_RECEPTION_SURFACE_SHAPE,
        "observation_depth": "limited",
        "grounding_scope": "current_input_only",
        "reception_required": True,
        "question_policy": {
            "question_allowed": True,
            "question_required": False,
            "question_position": "after_reception_optional",
            "question_dominance_guard_required": True,
            "question_only_forbidden": True,
        },
        "visible_material_slots": list(visible_slots),
        "unknown_slots": list(unknown_slots),
        "semantic_material_ids": list(semantic_material_ids),
        "semantic_material_count": len(semantic_material_ids),
        "observation_focus": {
            "primary": _observation_focus_primary(semantic_material_ids, visible_slots),
            "must_not_assert": list(_MUST_NOT_ASSERT),
        },
        "surface_contract": {
            "starts_with": "見えたこと：\n",
            "contains_boundary": "\n\nEmlisから：\n",
            "observation_section_required": True,
            "reception_section_required": True,
            "labels_required": True,
        },
        "meta_boundary": {
            "body_free": True,
            "raw_input_included": False,
            "comment_text_body_included": False,
            "public_response_key_added": False,
            "rn_visible_contract_changed": False,
            "api_route_changed": False,
            "db_physical_name_changed": False,
            "gate_relaxed": False,
        },
        "body_free": True,
        "raw_input_included": False,
        "comment_text_body_included": False,
        "fixed_fallback_used": False,
        "case_specific_route_used": False,
        "exact_fixture_surface_used": False,
    }
    assert_limited_grounding_reception_surface_meta(plan)
    return plan


def is_limited_grounding_reception_required(
    *,
    material_route: Any,
    surface_requirement: Mapping[str, Any] | None = None,
) -> bool:
    """Return whether the route/requirement asks for limited-grounding reception."""

    route_meta = _material_route_meta(material_route)
    requirement = _as_mapping(surface_requirement)
    return _material_quality(route_meta, requirement) == LIMITED_GROUNDING_MATERIAL_QUALITY


def is_limited_grounding_reception_comment_shape(value: Any) -> bool:
    """Return whether comment text has the required limited reception shape."""

    body = _clean_public_body(value)
    boundary = "\n\nEmlisから：\n"
    if not body.startswith("見えたこと：\n") or boundary not in body:
        return False
    observation, reception = body.split(boundary, 1)
    observation_body = observation.removeprefix("見えたこと：\n").strip()
    reception_body = reception.strip()
    return bool(observation_body and reception_body)


def compose_limited_grounding_labelled_two_stage_comment(
    *,
    current_input: Mapping[str, Any] | None,
    material_route: Any,
    surface_requirement: Mapping[str, Any] | None = None,
) -> str:
    """Compose the labelled two-stage comment body from the limited plan."""

    plan = build_limited_grounding_reception_surface_plan(
        current_input=current_input,
        material_route=material_route,
        surface_requirement=surface_requirement,
    )
    observation = _compose_observation_section(
        current_input=current_input,
        material_route_meta=_material_route_meta(material_route),
        surface_plan=plan,
    )
    reception = _compose_reception_section(surface_plan=plan)
    return _clean_public_body(f"見えたこと：\n{observation}\n\nEmlisから：\n{reception}")


def limited_grounding_reception_surface_public_summary(value: Mapping[str, Any] | None) -> dict[str, Any]:
    """Return a body-free summary suitable for public/internal lineage meta."""

    plan = _as_mapping(value)
    semantic_ids = _dedupe(plan.get("semantic_material_ids") or ())
    visible_slots = _dedupe(plan.get("visible_material_slots") or ())
    unknown_slots = _dedupe(plan.get("unknown_slots") or ())
    question_policy = _as_mapping(plan.get("question_policy"))
    observation_focus = _as_mapping(plan.get("observation_focus"))
    must_not_assert = _dedupe(observation_focus.get("must_not_assert") or ())
    summary = {
        "schema_version": _clean_identifier(plan.get("schema_version"), max_length=128)
        or LIMITED_GROUNDING_RECEPTION_SURFACE_PLAN_SCHEMA_VERSION,
        "source_phase": _clean_identifier(plan.get("source_phase"), max_length=128)
        or LIMITED_GROUNDING_RECEPTION_SURFACE_SOURCE_PHASE,
        "limited_grounding_reception_surface_used": bool(
            plan.get("limited_grounding_reception_surface_used")
        ),
        "material_quality": _clean_identifier(plan.get("material_quality"), max_length=96),
        "response_kind": _clean_identifier(plan.get("response_kind"), max_length=96),
        "surface_shape": _clean_identifier(plan.get("surface_shape"), max_length=96)
        or LIMITED_GROUNDING_RECEPTION_SURFACE_SHAPE,
        "observation_depth": _clean_identifier(plan.get("observation_depth"), max_length=96) or "limited",
        "reception_required": bool(plan.get("reception_required")),
        "question_allowed": bool(question_policy.get("question_allowed")),
        "question_required": bool(question_policy.get("question_required")),
        "question_dominance_guard_required": bool(question_policy.get("question_dominance_guard_required")),
        "visible_slot_count": len(visible_slots),
        "unknown_slot_count": len(unknown_slots),
        "semantic_material_ids": list(semantic_ids),
        "semantic_material_count": len(semantic_ids),
        "must_not_assert": list(must_not_assert),
        "must_not_assert_count": len(must_not_assert),
        "body_free": True,
        "raw_input_included": False,
        "comment_text_body_included": False,
        "public_response_key_added": False,
        "rn_visible_contract_changed": False,
        "gate_relaxed": False,
        "fixed_fallback_used": False,
        "case_specific_route_used": False,
    }
    if _contains_forbidden_text_key(summary):
        raise ValueError("limited grounding reception surface summary must remain body-free")
    json.dumps(summary, ensure_ascii=False, sort_keys=True)
    return summary


def assert_limited_grounding_reception_surface_meta(value: Mapping[str, Any]) -> None:
    if not isinstance(value, Mapping):
        raise ValueError("limited grounding reception surface meta must be a mapping")
    missing = _META_REQUIRED_KEYS.difference(value.keys())
    if missing:
        raise ValueError(f"limited grounding reception surface meta missing keys: {sorted(missing)}")
    if value.get("schema_version") != LIMITED_GROUNDING_RECEPTION_SURFACE_PLAN_SCHEMA_VERSION:
        raise ValueError("unexpected limited grounding reception surface schema_version")
    if value.get("source_phase") != LIMITED_GROUNDING_RECEPTION_SURFACE_SOURCE_PHASE:
        raise ValueError("unexpected limited grounding reception surface source_phase")
    if value.get("response_kind") != LIMITED_GROUNDING_RESPONSE_KIND:
        raise ValueError("limited grounding reception surface response kind must remain limited")
    if value.get("surface_shape") != LIMITED_GROUNDING_RECEPTION_SURFACE_SHAPE:
        raise ValueError("limited grounding reception surface must use labelled two-stage shape")
    if value.get("reception_required") is not True:
        raise ValueError("limited grounding reception surface must require reception")
    if any(bool(value.get(key)) for key in ("raw_input_included", "comment_text_body_included")):
        raise ValueError("limited grounding reception surface meta must be body-free")
    if any(
        bool(value.get(key))
        for key in ("fixed_fallback_used", "case_specific_route_used", "exact_fixture_surface_used")
    ):
        raise ValueError("limited grounding reception surface must not use fallback/case fixture route")
    meta_boundary = _as_mapping(value.get("meta_boundary"))
    if meta_boundary.get("body_free") is not True:
        raise ValueError("limited grounding reception surface meta boundary must be body-free")
    for key in (
        "raw_input_included",
        "comment_text_body_included",
        "public_response_key_added",
        "rn_visible_contract_changed",
        "api_route_changed",
        "db_physical_name_changed",
        "gate_relaxed",
    ):
        if meta_boundary.get(key) is not False:
            raise ValueError(f"limited grounding reception surface boundary flag must be false: {key}")
    question_policy = _as_mapping(value.get("question_policy"))
    if question_policy.get("question_required") is not False:
        raise ValueError("limited grounding reception surface must not require a question")
    if question_policy.get("question_position") != "after_reception_optional":
        raise ValueError("limited grounding question must stay after reception and optional")
    surface_contract = _as_mapping(value.get("surface_contract"))
    if surface_contract.get("observation_section_required") is not True:
        raise ValueError("limited grounding reception surface must require observation section")
    if surface_contract.get("reception_section_required") is not True:
        raise ValueError("limited grounding reception surface must require reception section")
    if surface_contract.get("labels_required") is not True:
        raise ValueError("limited grounding reception surface must require labels")
    if _contains_forbidden_text_key(value):
        raise ValueError("limited grounding reception surface meta must not contain text payload keys")
    json.dumps(dict(value), ensure_ascii=False, sort_keys=True)


def _compose_observation_section(
    *,
    current_input: Mapping[str, Any] | None,
    material_route_meta: Mapping[str, Any],
    surface_plan: Mapping[str, Any],
) -> str:
    semantic_ids = set(_dedupe(surface_plan.get("semantic_material_ids") or ()))
    if {"comparison_baseline_shift", "small_change_preservation"}.issubset(semantic_ids):
        return "今は、大きく変わることより、昨日の自分より少し前に進むことを基準に置こうとしている状態に見えます。"
    if "recovered_energy" in semantic_ids and ({"relationship_wish", "future_intention"} & semantic_ids):
        return "今は、気力が戻ってきたタイミングを逃したくない気持ちと、人と近くありたい願いが一緒に出ている状態に見えます。"
    if "recovered_energy" in semantic_ids and ({"self_observation", "value_preservation", "future_intention"} & semantic_ids):
        return "今は、やってみたいと思えた気持ちを大事にしながら、次の頑張り方を探している状態に見えます。"
    if "self_observation" in semantic_ids:
        return "今は、自分の内側で見えかけている変化や大切にしたい基準を、急いで結論づけずに置いている状態に見えます。"
    topic = _topic_phrase(current_input=current_input, material_route_meta=material_route_meta)
    visible_phrase = _visible_slot_phrase(material_route_meta)
    return f"今は、{topic}について、{visible_phrase}を狭い範囲で置いている状態に見えます。"


def _compose_reception_section(*, surface_plan: Mapping[str, Any]) -> str:
    semantic_ids = set(_dedupe(surface_plan.get("semantic_material_ids") or ()))
    if {"comparison_baseline_shift", "small_change_preservation"}.issubset(semantic_ids):
        return "人と比べて焦りが出る中でも、小さな変化や少し言葉にできたことを消さずに見ようとしているところを、Emlisは受け取りました。"
    if "recovered_energy" in semantic_ids and ({"relationship_wish", "future_intention"} & semantic_ids):
        return "寂しい時にそばにいてくれる存在をいいなと思えたことも、また挑戦したいと思えたことも、今の回復の動きとして大切に置かれているようにEmlisは受け取りました。"
    if "recovered_energy" in semantic_ids and ({"self_observation", "value_preservation", "future_intention"} & semantic_ids):
        return "自分にも出来るかもしれないと思えた瞬間を流さず、その気持ちを確かめようとしているところを、Emlisは受け取りました。"
    if "self_observation" in semantic_ids:
        return "まだ一つの答えにしきらないままでも、自分の基準や変化を見ようとしているところを、Emlisは受け取りました。"
    return "読める範囲はまだ限られていますが、その限られた材料の中でも、いまの気持ちを置こうとしているところをEmlisは受け取りました。"


def _semantic_material_ids(
    *,
    current_input: Mapping[str, Any] | None,
    material_route_meta: Mapping[str, Any],
) -> tuple[str, ...]:
    current = _as_mapping(current_input)
    haystack = "\n".join(
        part
        for part in (
            _clean(_first(("memo", "note", "description"), current)),
            _clean(_first(("memo_action", "action", "next_action"), current)),
        )
        if part
    )
    ids: list[str] = []
    for material_id, patterns in _SEMANTIC_MATERIAL_PATTERNS:
        if any(pattern in haystack for pattern in patterns):
            ids.append(material_id)
    relation_ids = _dedupe(
        _first(("relation_material_ids", "generic_relation_material_ids"), material_route_meta) or ()
    )
    for relation_id in relation_ids:
        ids.extend(_RELATION_ID_SEMANTIC_ALIASES.get(relation_id, ()))
    return tuple(_dedupe(ids))


def _observation_focus_primary(semantic_ids: Sequence[str], visible_slots: Sequence[str]) -> str:
    semantic = set(semantic_ids)
    if "comparison_baseline_shift" in semantic:
        return "comparison_baseline_or_small_change"
    if "recovered_energy" in semantic:
        return "recovered_energy_or_future_direction"
    if "relationship_wish" in semantic:
        return "relationship_wish"
    if "self_observation" in semantic:
        return "self_observation"
    if visible_slots:
        return "visible_state_or_direction"
    return "limited_visible_material"


def _visible_slot_phrase(material_route_meta: Mapping[str, Any]) -> str:
    parts = [
        _SLOT_LABELS[slot]
        for slot in _dedupe(material_route_meta.get("visible_material_slots") or ())
        if slot in _SLOT_LABELS
    ]
    if not parts:
        return "見えている気持ちの向き"
    if len(parts) == 1:
        return parts[0]
    return "、".join(parts[:-1]) + "と" + parts[-1]


def _topic_phrase(*, current_input: Mapping[str, Any] | None, material_route_meta: Mapping[str, Any]) -> str:
    current = _as_mapping(current_input)
    category_words = _safe_string_items(_first(("categories", "category", "category_labels"), current), max_items=2)
    if category_words:
        return "・".join(category_words)
    visible_slots = _safe_string_items(material_route_meta.get("visible_material_slots"), max_items=1)
    if visible_slots:
        return _topic_from_marker(visible_slots[0])
    return "いま置かれていること"


def _topic_from_marker(value: str) -> str:
    if any(marker in value for marker in ("人", "相手", "関係", "友", "家族", "職場", "relationship")):
        return "人とのやり取り"
    if any(marker in value for marker in ("仕事", "作業", "会社", "work")):
        return "仕事や作業"
    if any(marker in value for marker in ("体", "健康", "眠", "疲", "health")):
        return "体調や生活"
    if any(marker in value for marker in ("お金", "金", "生活", "money")):
        return "生活の現実"
    if any(marker in value for marker in ("自分", "気持", "わから", "何故", "なぜ", "self")):
        return "自分の内側"
    return "いま置かれていること"


def _material_route_meta(material_route: Any) -> Mapping[str, Any]:
    if isinstance(material_route, Mapping):
        return material_route
    as_meta = getattr(material_route, "as_meta", None)
    if callable(as_meta):
        try:
            meta = as_meta()
            if isinstance(meta, Mapping):
                return meta
        except Exception:
            return {}
    meta = getattr(material_route, "meta", None)
    if isinstance(meta, Mapping):
        return meta
    return {}


def _material_quality(route_meta: Mapping[str, Any], requirement: Mapping[str, Any]) -> str:
    return _clean_identifier(
        _first(("material_quality", "eligibility_status", "status"), route_meta)
        or requirement.get("material_quality_family")
        or LIMITED_GROUNDING_MATERIAL_QUALITY,
        max_length=96,
    )


def _first(keys: Sequence[str], mapping: Mapping[str, Any]) -> Any:
    for key in keys:
        if key in mapping and mapping[key] not in (None, "", [], {}):
            return mapping[key]
    return None


def _safe_string_items(value: Any, *, max_items: int) -> tuple[str, ...]:
    items: list[str] = []
    for item in _as_sequence(value):
        if isinstance(item, Mapping):
            raw = item.get("label") or item.get("name") or item.get("value") or item.get("type") or item.get("id")
        else:
            raw = item
        cleaned = _clean(raw)
        cleaned = re.sub(r"[\r\n\t]+", " ", cleaned)
        cleaned = re.sub(r"[^0-9A-Za-z_:\-.ぁ-んァ-ヶ一-龠々ー]+", "", cleaned)[:24]
        if cleaned and cleaned not in items:
            items.append(cleaned)
        if len(items) >= max_items:
            break
    return tuple(items)


def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
    if values is None:
        iterable: Iterable[Any] = ()
    elif isinstance(values, (str, bytes, bytearray)):
        iterable = (values,)
    elif isinstance(values, Iterable):
        iterable = values
    else:
        iterable = (values,)
    out: list[str] = []
    seen: set[str] = set()
    for value in iterable:
        item = _clean_identifier(value, max_length=128)
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _as_sequence(value: Any) -> tuple[Any, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes, bytearray)):
        return (value,)
    if isinstance(value, Mapping):
        return (value,)
    if isinstance(value, Sequence):
        return tuple(value)
    return (value,)


def _clean_public_body(value: Any) -> str:
    body = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
    body = re.sub(r"[ \t]+", " ", body)
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body.strip()


def _clean(value: Any) -> str:
    return _SPACE_RE.sub(" ", str(value or "").replace("\u3000", " ")).strip()


def _clean_identifier(value: Any, *, max_length: int = 128) -> str:
    text = re.sub(r"[^0-9A-Za-z_:\-.ぁ-んァ-ヶ一-龠々ー]+", "_", str(value or "").strip())
    return text.strip("_")[:max_length]


def _contains_forbidden_text_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in _FORBIDDEN_META_TEXT_KEYS:
                return True
            if _contains_forbidden_text_key(child):
                return True
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_forbidden_text_key(child) for child in value)
    return False


__all__ = [
    "LIMITED_GROUNDING_MATERIAL_QUALITY",
    "LIMITED_GROUNDING_RECEPTION_SURFACE_PLAN_SCHEMA_VERSION",
    "LIMITED_GROUNDING_RECEPTION_SURFACE_SHAPE",
    "LIMITED_GROUNDING_RECEPTION_SURFACE_SOURCE_PHASE",
    "LIMITED_GROUNDING_RESPONSE_KIND",
    "assert_limited_grounding_reception_surface_meta",
    "build_limited_grounding_reception_surface_plan",
    "compose_limited_grounding_labelled_two_stage_comment",
    "is_limited_grounding_reception_comment_shape",
    "is_limited_grounding_reception_required",
    "limited_grounding_reception_surface_public_summary",
]
