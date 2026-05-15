# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step08 coverage matrix for EmlisAI B-plan diagnostics.

The coverage matrix is developer-facing meta.  It translates stop reasons from
Step01-07 diagnostics into the B-S1 coverage groups that should be expanded
next.  It never creates or changes user-facing observation text.
"""

from dataclasses import dataclass
import re
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

_COVERAGE_MATRIX_VERSION = "emlis.coverage_matrix.v1"


@dataclass(frozen=True)
class CoverageGroupDefinition:
    group_key: str
    label: str
    target_step: str
    phase: str
    purpose: str

    def as_meta(self) -> Dict[str, Any]:
        return {
            "group_key": self.group_key,
            "label": self.label,
            "target_step": self.target_step,
            "phase": self.phase,
            "purpose": self.purpose,
        }


_INPUT_COVERAGE_GROUPS: Sequence[CoverageGroupDefinition] = (
    CoverageGroupDefinition(
        "energy_fatigue",
        "energy / fatigue",
        "Step09 Scope拡張 / Step11 PhraseUnit拡張",
        "B-S1",
        "疲れ、しんどさ、動けなさ、回復待ちの入力構造を扱う。",
    ),
    CoverageGroupDefinition(
        "anxiety",
        "anxiety",
        "Step09 Scope拡張 / Step12 Profile拡張",
        "B-S1",
        "不安、怖さ、悪化予感、心配が中心にある入力構造を扱う。",
    ),
    CoverageGroupDefinition(
        "anger_hurt",
        "anger / hurt",
        "Step09 Scope拡張 / Step11 PhraseUnit拡張",
        "B-S1",
        "怒り、傷つき、引っかかり、責められ感の入力構造を扱う。",
    ),
    CoverageGroupDefinition(
        "positive_recovery",
        "positive / recovery",
        "Step09 Scope拡張 / Step12 Profile拡張",
        "B-S1",
        "嬉しさ、安心、リラックス、整え直し、回復の入力構造を扱う。",
    ),
    CoverageGroupDefinition(
        "relationship",
        "relationship",
        "Step09 Scope拡張 / Step12 Profile拡張",
        "B-S1",
        "友人、家族、相手、職場など対人関係を含む入力構造を扱う。",
    ),
    CoverageGroupDefinition(
        "limit_escape",
        "limit / escape",
        "Step09 Scope拡張 / Step10 Safety境界",
        "B-S1",
        "限界、逃げたい、距離を置きたい、普通に生活したい入力構造を扱う。",
    ),
    CoverageGroupDefinition(
        "value_wish",
        "value / wish",
        "Step09 Scope拡張 / Step11 PhraseUnit拡張",
        "B-S1",
        "したいこと、大事にしたいこと、願い、価値観を含む入力構造を扱う。",
    ),
    CoverageGroupDefinition(
        "long_meaning_arc",
        "long meaning arc",
        "Step12 SentencePlan拡張 / Step15 共通Core安定化",
        "B-S1",
        "複数文・長文の意味の流れを扱う。",
    ),
)

_TECHNICAL_GROUPS: Sequence[CoverageGroupDefinition] = (
    CoverageGroupDefinition(
        "connection_rollout",
        "connection / rollout",
        "Step06 B案通常接続",
        "B-D1",
        "feature flag、rollout、registry接続の停止を扱う。",
    ),
    CoverageGroupDefinition(
        "scope_contract",
        "scope contract",
        "Step09 Scope拡張",
        "B-S1",
        "primary_state、required structure、claim/relation選別の停止を扱う。",
    ),
    CoverageGroupDefinition(
        "composer_material",
        "composer material",
        "Step11-13 Composer拡張",
        "B-C1",
        "PhraseUnit、role、profile、SentencePlan不足の停止を扱う。",
    ),
    CoverageGroupDefinition(
        "gate_quality",
        "gate quality",
        "Step14 Guard強化",
        "B-G1",
        "Reader、Grounding、TemplateEcho、Display Gateの停止を扱う。",
    ),
    CoverageGroupDefinition(
        "safety_boundary",
        "safety boundary",
        "Step10 Safety境界",
        "B-S1",
        "安全境界により本文生成前に止めるケースを扱う。",
    ),
)

_GROUP_BY_KEY = {item.group_key: item for item in [*_INPUT_COVERAGE_GROUPS, *_TECHNICAL_GROUPS]}
_INPUT_GROUP_KEYS = tuple(item.group_key for item in _INPUT_COVERAGE_GROUPS)
_TECHNICAL_GROUP_KEYS = tuple(item.group_key for item in _TECHNICAL_GROUPS)
COVERAGE_GROUP_ORDER = _INPUT_GROUP_KEYS

# Symbolic next-step keys are stable for QA and are kept separate from the
# human-readable target_step labels.
_NEXT_STEPS_BY_GROUP: Dict[str, Sequence[str]] = {
    "energy_fatigue": ("Step09_scope_expansion", "Step11_phrase_unit_role_expansion"),
    "anxiety": ("Step09_scope_expansion", "Step11_phrase_unit_role_expansion", "Step12_profile_sentence_plan_expansion"),
    "anger_hurt": ("Step09_scope_expansion", "Step11_phrase_unit_role_expansion"),
    "positive_recovery": ("Step09_scope_expansion", "Step12_profile_sentence_plan_expansion"),
    "relationship": ("Step09_scope_expansion", "Step12_profile_sentence_plan_expansion"),
    "limit_escape": ("Step09_scope_expansion", "Step10_safety_boundary"),
    "value_wish": ("Step09_scope_expansion", "Step11_phrase_unit_role_expansion"),
    "long_meaning_arc": ("Step12_profile_sentence_plan_expansion", "Step15_common_core_stabilization"),
    "connection_rollout": ("Step06_b_plan_normal_connection",),
    "scope_contract": ("Step09_scope_expansion",),
    "composer_material": ("Step11_phrase_unit_role_expansion", "Step12_profile_sentence_plan_expansion", "Step13_surface_realizer"),
    "gate_quality": ("Step14_guard_strengthening",),
    "safety_boundary": ("Step10_safety_boundary",),
}

_GROUP_PATTERNS: Dict[str, re.Pattern[str]] = {
    "energy_fatigue": re.compile(r"(疲れ|疲労|だる|しんど|重い|眠|寝|休み|休め|動けな|体力|消耗|ぐったり|へとへと)"),
    "anxiety": re.compile(r"(不安|怖|恐|心配|焦|悪化|落ちる|嫌われ|見捨て|大丈夫かな|どうしよう|緊張|迷惑かも|迷惑かもしれない)"),
    "anger_hurt": re.compile(r"(怒|腹が立|ムカ|許せ|傷つ|刺さ|悲し|つら|責め|ゲンナリ|嫌|言い方|悔し)"),
    "positive_recovery": re.compile(r"(嬉し|うれし|楽しか|楽し|安心|リラックス|落ち着|回復|元気|整え|整っ|できた|気持ちが軽|休めた)"),
    "relationship": re.compile(r"(友達|友人|家族|親|母|父|兄|姉|弟|妹|相手|恋人|彼氏|彼女|職場|学校|上司|同僚|誰か|人間関係|距離|言われ|相談|迷惑)"),
    "limit_escape": re.compile(r"(限界|逃げ|逃げ出|無理|離れ|距離|普通に生活|何もしたくない|やめたい|休みたい|全部無視|投げ出|耐えられ|きつい)"),
    "value_wish": re.compile(r"(したい|なりたい|欲しい|ほしい|願|大事|大切|優先|守りたい|頼りたい|生活したい|選びたい|価値|望んで)"),
}

_ROLE_PATTERNS: Sequence[Tuple[str, str, re.Pattern[str]]] = (
    ("energy_fatigue", "low_energy", re.compile(r"(疲れ|だる|しんど|動けな|消耗|休み|休め|何もしたくない)")),
    ("anxiety", "anxiety_return", re.compile(r"(不安|怖|心配|悪化|どうしよう|迷惑かも|迷惑かもしれない)")),
    ("anger_hurt", "hurt_or_anger", re.compile(r"(怒|傷つ|刺さ|ゲンナリ|つら|嫌|悔し)")),
    ("positive_recovery", "positive_state", re.compile(r"(嬉し|うれし|安心|リラックス|整え|回復|楽しか|楽し)")),
    ("relationship", "relationship_burden", re.compile(r"(相談|迷惑|人間関係|相手|友達|家族|職場|誰か)")),
    ("relationship", "wish_to_rely", re.compile(r"(頼りたい|相談したい|話したい|支えて|助けて)")),
    ("limit_escape", "limit", re.compile(r"(限界|逃げ|何もしたくない|全部無視|投げ出|やめたい|休みたい|普通に生活)")),
    ("value_wish", "wish_or_value", re.compile(r"(したい|願|大事|大切|優先|生活したい|選びたい|頼りたい)")),
)

_HINT_TO_GROUPS: Dict[str, Sequence[str]] = {
    # Scope-side hints.
    "safety_boundary": ("safety_boundary", "limit_escape"),
    "required_structure": ("scope_contract",),
    "primary_state_grounding": ("scope_contract",),
    "current_input_core_evidence": ("scope_contract",),
    "minimum_claim": ("scope_contract",),
    "current_input_core": ("scope_contract",),
    "partial_observation": ("scope_contract",),
    "eligible_current_input_core": ("scope_contract",),
    "eligible_partial_observation": ("scope_contract",),
    "core_tension": ("scope_contract", "relationship"),
    "complexity_limit": ("scope_contract", "long_meaning_arc"),
    "scope_complexity": ("scope_contract", "long_meaning_arc"),
    # Composer-side hints.
    "required_role_missing": ("composer_material",),
    "missing_phrase_units": ("composer_material",),
    "shallow_insufficient_evidence": ("composer_material", "scope_contract"),
    "profile_unmatched": ("composer_material",),
    "sentence_plan_unavailable": ("composer_material", "long_meaning_arc"),
    "composer_generated": ("composer_material",),
    "composer_not_classified": ("composer_material",),
    # Gate-side hints.
    "reader_readability": ("gate_quality",),
    "grounding_unsupported": ("gate_quality", "scope_contract"),
    "grounding_evidence": ("gate_quality", "scope_contract"),
    "template_echo_raw_copy": ("gate_quality",),
    "template_echo_surface": ("gate_quality",),
    "display_phase": ("gate_quality",),
    "gate_not_classified": ("gate_quality",),
    "gate_passed": ("gate_quality",),
}

_REASON_SUBSTRINGS_TO_GROUPS: Sequence[tuple[str, Sequence[str]]] = (
    ("feature", ("connection_rollout",)),
    ("rollout", ("connection_rollout",)),
    ("registry", ("connection_rollout",)),
    ("composer_client_not_connected", ("connection_rollout",)),
    ("safety", ("safety_boundary", "limit_escape")),
    ("required_structure", ("scope_contract",)),
    ("primary", ("scope_contract",)),
    ("ground", ("scope_contract",)),
    ("evidence", ("scope_contract",)),
    ("relation", ("scope_contract", "long_meaning_arc")),
    ("tension", ("scope_contract", "long_meaning_arc")),
    ("claim_limit", ("scope_contract", "long_meaning_arc")),
    ("phrase_unit", ("composer_material",)),
    ("required_role", ("composer_material",)),
    ("profile", ("composer_material",)),
    ("sentence_plan", ("composer_material", "long_meaning_arc")),
    ("shallow", ("composer_material",)),
    ("reader", ("gate_quality",)),
    ("unsupported_sentence", ("gate_quality", "scope_contract")),
    ("template", ("gate_quality",)),
    ("raw_quote", ("gate_quality",)),
    ("display", ("gate_quality",)),
    ("phase_not_complete", ("gate_quality",)),
)

_ROLE_TO_GROUP_SUBSTRINGS: Sequence[tuple[str, str]] = (
    ("anxiety", "anxiety"),
    ("fear", "anxiety"),
    ("worry", "anxiety"),
    ("positive", "positive_recovery"),
    ("recovery", "positive_recovery"),
    ("repair", "positive_recovery"),
    ("fatigue", "energy_fatigue"),
    ("low_energy", "energy_fatigue"),
    ("energy", "energy_fatigue"),
    ("anger", "anger_hurt"),
    ("hurt", "anger_hurt"),
    ("relationship", "relationship"),
    ("burden", "relationship"),
    ("rely", "relationship"),
    ("limit", "limit_escape"),
    ("escape", "limit_escape"),
    ("avoid", "limit_escape"),
    ("wish", "value_wish"),
    ("value", "value_wish"),
    ("meaning", "long_meaning_arc"),
    ("arc", "long_meaning_arc"),
    ("tension", "long_meaning_arc"),
)


def _dedupe(values: Iterable[Any]) -> List[str]:
    out: List[str] = []
    for value in values or []:
        item = str(value or "").strip()
        if item and item not in out:
            out.append(item)
    return out


def _text_from_current_input(current_input: Mapping[str, Any] | None) -> str:
    if not isinstance(current_input, Mapping):
        return ""
    parts: List[str] = []
    for key in ("memo", "memo_action", "text", "free_text"):
        value = str(current_input.get(key) or "").strip()
        if value:
            parts.append(value)
    for key in ("emotions", "category"):
        value = current_input.get(key)
        if isinstance(value, (list, tuple, set)):
            parts.extend(str(item or "").strip() for item in value if str(item or "").strip())
        elif str(value or "").strip():
            parts.append(str(value).strip())
    emotion_details = current_input.get("emotion_details")
    if isinstance(emotion_details, list):
        for item in emotion_details:
            if isinstance(item, Mapping):
                type_name = str(item.get("type") or "").strip()
                if type_name:
                    parts.append(type_name)
    return "\n".join(parts)


def _detect_input_groups(text: str) -> tuple[List[str], Dict[str, List[str]]]:
    body = str(text or "")
    groups: List[str] = []
    evidence_terms: Dict[str, List[str]] = {}
    for group_key, pattern in _GROUP_PATTERNS.items():
        matches = _dedupe(match.group(0) for match in pattern.finditer(body))
        if matches:
            groups.append(group_key)
            evidence_terms[group_key] = matches[:8]
    stripped = body.strip()
    sentence_markers = len(re.findall(r"[。！？!?\n]", stripped))
    if len(stripped) >= 120 or sentence_markers >= 3:
        if "long_meaning_arc" not in groups:
            groups.append("long_meaning_arc")
        evidence_terms.setdefault("long_meaning_arc", [f"length={len(stripped)}", f"markers={sentence_markers}"])
    return groups, evidence_terms


def _roles_from_text(text: str) -> Dict[str, List[str]]:
    roles: Dict[str, List[str]] = {}
    body = str(text or "")
    for group_key, role, pattern in _ROLE_PATTERNS:
        if pattern.search(body):
            roles.setdefault(group_key, [])
            if role not in roles[group_key]:
                roles[group_key].append(role)
    return roles


def _role_to_group(role: str) -> str:
    value = str(role or "").strip().lower()
    if not value:
        return ""
    for needle, group_key in _ROLE_TO_GROUP_SUBSTRINGS:
        if needle in value:
            return group_key
    return ""


def _scope_expansion_groups(summary: Mapping[str, Any]) -> List[str]:
    groups: List[str] = []
    diagnostic = summary.get("scope_diagnostic")
    if isinstance(diagnostic, Mapping):
        raw = diagnostic.get("coverage_groups")
        if isinstance(raw, list):
            groups.extend(str(item or "").strip() for item in raw if str(item or "").strip())
        expansion = diagnostic.get("scope_expansion")
        if isinstance(expansion, Mapping):
            raw = expansion.get("coverage_groups")
            if isinstance(raw, list):
                groups.extend(str(item or "").strip() for item in raw if str(item or "").strip())
    return [group for group in _dedupe(groups) if group in _GROUP_BY_KEY]


def _composer_role_groups(summary: Mapping[str, Any]) -> tuple[Dict[str, List[str]], List[str]]:
    diagnostic = summary.get("composer_diagnostic")
    if not isinstance(diagnostic, Mapping):
        diagnostic = {}
    roles: List[str] = []
    for key in ("missing_roles", "required_roles", "available_roles", "covered_roles"):
        raw = diagnostic.get(key)
        if isinstance(raw, list):
            roles.extend(str(item or "").strip() for item in raw if str(item or "").strip())
    groups_by_role: Dict[str, List[str]] = {}
    for role in _dedupe(roles):
        group_key = _role_to_group(role)
        if group_key:
            groups_by_role.setdefault(group_key, [])
            if role not in groups_by_role[group_key]:
                groups_by_role[group_key].append(role)
    return groups_by_role, _dedupe(roles)


def _reason_groups(reason: str) -> List[str]:
    value = str(reason or "").strip()
    if not value:
        return []
    if value in _GROUP_BY_KEY:
        return [value]
    if value in _HINT_TO_GROUPS:
        return list(_HINT_TO_GROUPS[value])
    lowered = value.lower()
    out: List[str] = []
    for needle, groups in _REASON_SUBSTRINGS_TO_GROUPS:
        if needle in lowered:
            out.extend(groups)
    return _dedupe(out)


def _collect_reason_codes(summary: Mapping[str, Any]) -> List[str]:
    values: List[Any] = [summary.get("primary_reason")]
    for key in (
        "secondary_reasons",
        "scope_rejection_reasons",
        "scope_safety_boundaries",
        "scope_excluded_reason_codes",
        "scope_coverage_matrix_hints",
        "composer_rejection_reasons",
        "composer_coverage_matrix_hints",
        "gate_rejection_reasons",
        "gate_coverage_matrix_hints",
    ):
        raw = summary.get(key)
        if isinstance(raw, list):
            values.extend(raw)
        elif raw:
            values.append(raw)
    for nested_key in ("scope_diagnostic", "composer_diagnostic", "gate_diagnostic"):
        nested = summary.get(nested_key)
        if not isinstance(nested, Mapping):
            continue
        for key in ("reason_codes", "reason_categories", "coverage_matrix_hints", "rejection_reasons", "safety_boundaries", "excluded_reason_codes"):
            raw = nested.get(key)
            if isinstance(raw, list):
                values.extend(raw)
            elif raw:
                values.append(raw)
    return _dedupe(values)


def _target_step_for(group_key: str) -> str:
    definition = _GROUP_BY_KEY.get(group_key)
    return definition.target_step if definition else "Step08 coverage matrix"


def _phase_for(group_key: str) -> str:
    definition = _GROUP_BY_KEY.get(group_key)
    return definition.phase if definition else "B-S1"


def _input_priority_group(groups: Sequence[str]) -> str:
    for group_key in _INPUT_GROUP_KEYS:
        if group_key in groups:
            return group_key
    return str(groups[0] or "") if groups else ""


def build_emlis_coverage_matrix(
    *,
    diagnostic_summary: Mapping[str, Any],
    current_input: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Translate diagnostic reasons into Step08 coverage groups.

    The result is meta-only and safe to expose to developer QA.  It keeps three
    views: semantic groups detected from the submitted input, technical groups
    from the stop reason, and role hints from Composer.  That lets Step09+ decide
    what to expand without turning single examples into fixed templates.
    """

    summary = diagnostic_summary if isinstance(diagnostic_summary, Mapping) else {}
    text = _text_from_current_input(current_input)
    input_groups, input_evidence_terms = _detect_input_groups(text)
    text_roles_by_group = _roles_from_text(text)
    scope_expansion_groups = _scope_expansion_groups(summary)
    composer_roles_by_group, composer_roles = _composer_role_groups(summary)
    reason_codes = _collect_reason_codes(summary)

    reasons_by_group: Dict[str, List[str]] = {}
    reason_to_groups: Dict[str, List[str]] = {}
    unclassified_reasons: List[str] = []
    for reason in reason_codes:
        groups = _reason_groups(reason)
        # Composer role failures should also point to the semantic group whose
        # role is missing, e.g. anxiety_return -> anxiety.
        if "required_role" in str(reason).lower() or str(reason).strip() == "required_role_missing":
            groups = _dedupe([*composer_roles_by_group.keys(), *groups])
        if groups:
            reason_to_groups[reason] = list(groups)
            for group in groups:
                reasons_by_group.setdefault(group, [])
                if reason not in reasons_by_group[group]:
                    reasons_by_group[group].append(reason)
        else:
            unclassified_reasons.append(reason)
            reason_to_groups[reason] = []

    # If a completely new reason arrives, keep it visible and anchor the repair
    # route at scope_contract until a specific mapping is added in a later step.
    fallback_groups = ["scope_contract"] if unclassified_reasons and not reasons_by_group else []
    input_groups = _dedupe([*input_groups, *scope_expansion_groups, *composer_roles_by_group.keys()])
    target_groups = _dedupe([*input_groups, *reasons_by_group.keys(), *fallback_groups])
    if not target_groups:
        target_groups = ["scope_contract"]

    entries: List[Dict[str, Any]] = []
    coverage_group_map: Dict[str, Dict[str, Any]] = {}
    for group_key in target_groups:
        definition = _GROUP_BY_KEY.get(group_key)
        matched_from_input = group_key in input_groups or group_key in text_roles_by_group
        reason_list = reasons_by_group.get(group_key, [])
        roles = _dedupe([*(text_roles_by_group.get(group_key) or []), *(composer_roles_by_group.get(group_key) or [])])
        is_input_group = group_key in _INPUT_GROUP_KEYS
        is_technical_group = group_key in _TECHNICAL_GROUP_KEYS
        priority = 0
        # Prefer semantic repair groups when the input tells us what structure is
        # missing; keep connection/rollout first only when no semantic group is
        # present.
        if is_input_group:
            priority += 40
        if matched_from_input:
            priority += 20
        if roles:
            priority += 15
        if reason_list:
            priority += 10
        if is_technical_group:
            priority += 5
        if str(summary.get("stage") or "") in {"scope", "composer", "reader", "grounding", "template", "display"}:
            priority += 3
        status = "needs_expansion" if str(summary.get("observation_status") or "") != "passed" else "covered_or_observed"
        entry = {
            "coverage_group": group_key,
            "label": definition.label if definition else group_key,
            "phase": definition.phase if definition else "B-S1",
            "target_step": definition.target_step if definition else "Step08 coverage matrix",
            "next_steps": list(_NEXT_STEPS_BY_GROUP.get(group_key) or (definition.target_step if definition else "Step08 coverage matrix",)),
            "matched_from_input": matched_from_input,
            "input_evidence_terms": list(input_evidence_terms.get(group_key) or []),
            "roles": roles,
            "composer_roles": list(composer_roles_by_group.get(group_key) or []),
            "reason_codes": list(reason_list),
            "reason_count": len(reason_list),
            "priority": priority,
            "active": True,
            "status": status,
        }
        entries.append(entry)
        coverage_group_map[group_key] = dict(entry)
    entries.sort(key=lambda item: (-int(item.get("priority") or 0), str(item.get("coverage_group") or "")))

    active_groups = _dedupe(item.get("coverage_group") for item in entries)
    input_coverage_groups = [group for group in active_groups if group in _INPUT_GROUP_KEYS]
    technical_coverage_groups = [group for group in active_groups if group in _TECHNICAL_GROUP_KEYS]
    next_steps = _dedupe(step for entry in entries for step in (entry.get("next_steps") or []))
    primary_coverage_group = _input_priority_group(input_coverage_groups) or (active_groups[0] if active_groups else "")
    if not input_coverage_groups and technical_coverage_groups:
        primary_coverage_group = technical_coverage_groups[0]
    status = "classified" if active_groups and not (len(active_groups) == 1 and active_groups[0] == "scope_contract" and unclassified_reasons) else "unclassified"
    if str(summary.get("stage") or "") in {"flag", "rollout"} and not input_coverage_groups:
        status = "blocked_by_boundary" if technical_coverage_groups else status

    return {
        "version": _COVERAGE_MATRIX_VERSION,
        "phase": "B-S1",
        "purpose": "diagnostic reasons -> coverage groups",
        "matrix_purpose": "map_diagnostic_reasons_to_coverage_groups",
        "stop_stage": str(summary.get("stage") or ""),
        "observation_status": str(summary.get("observation_status") or ""),
        "primary_reason": str(summary.get("primary_reason") or ""),
        "status": status,
        "input_coverage_groups": input_coverage_groups,
        "technical_coverage_groups": technical_coverage_groups,
        # Keep coverage_groups as a flat list for the existing diagnostic
        # contract.  Detailed per-group data lives in coverage_group_map.
        "coverage_groups": active_groups,
        "active_groups": active_groups,
        "primary_coverage_group": primary_coverage_group,
        "reason_codes": reason_codes,
        "reason_to_groups": reason_to_groups,
        "composer_roles": composer_roles,
        "scope_expansion_groups": scope_expansion_groups,
        "unclassified_reasons": unclassified_reasons,
        "unmapped_reason_codes": unclassified_reasons,
        "unclassified_reason_count": len(unclassified_reasons),
        "next_steps": next_steps,
        "entries": entries,
        "coverage_group_map": coverage_group_map,
        "coverage_group_details": coverage_group_map,
        "input_group_definitions": [item.as_meta() for item in _INPUT_COVERAGE_GROUPS],
        "technical_group_definitions": [item.as_meta() for item in _TECHNICAL_GROUPS],
    }


__all__ = [
    "COVERAGE_GROUP_ORDER",
    "build_emlis_coverage_matrix",
]
