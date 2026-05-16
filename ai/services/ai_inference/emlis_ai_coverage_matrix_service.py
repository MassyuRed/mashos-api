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
_LIMITED_COMPOSER_SCORECARD_EVENT_VERSION = "emlis.limited_composer_scorecard_event.v1"
_LIMITED_COMPOSER_SCORECARD_AGGREGATE_VERSION = "emlis.limited_composer_scorecard_aggregate.v1"
_LIMITED_COMPOSER_SCORECARD_HARNESS_VERSION = "emlis.limited_composer_scorecard_harness.v1"
_LIMITED_COMPOSER_SCORECARD_STEP = "9_scorecard_harness"
_SCORECARD_STATUSES: Sequence[str] = ("passed", "rejected", "unavailable", "safety_blocked")


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



def _scorecard_mapping(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _scorecard_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return _dedupe(value)
    return _dedupe([value])


def _scorecard_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _scorecard_rate(numerator: int, denominator: int) -> float:
    return (float(numerator) / float(denominator)) if denominator else 0.0


def _scorecard_status(value: Any) -> str:
    status = str(value or "").strip()
    return status if status in _SCORECARD_STATUSES else "unavailable"


def _scorecard_source(record: Any) -> Dict[str, Any]:
    item = _scorecard_mapping(record)
    for key in ("diagnostic_summary", "summary", "metric_event", "rollout_metric_event"):
        nested = item.get(key)
        if isinstance(nested, Mapping):
            return dict(nested)
    return item


def _scorecard_matrix(summary: Mapping[str, Any]) -> Dict[str, Any]:
    return _scorecard_mapping(summary.get("coverage_matrix"))


def _scorecard_coverage_groups(summary: Mapping[str, Any]) -> List[str]:
    matrix = _scorecard_matrix(summary)
    groups = _dedupe([
        *_scorecard_list(summary.get("coverage_groups")),
        *_scorecard_list(matrix.get("coverage_groups")),
        *_scorecard_list(matrix.get("active_groups")),
    ])
    primary = (
        str(summary.get("coverage_group") or "").strip()
        or str(summary.get("coverage_primary_group") or "").strip()
        or str(matrix.get("primary_coverage_group") or "").strip()
    )
    if primary and primary not in groups:
        groups.insert(0, primary)
    return groups or ["unclassified"]


def _scorecard_reason_codes(summary: Mapping[str, Any], primary_reason: str) -> List[str]:
    values: List[Any] = [primary_reason]
    for key in (
        "secondary_reasons",
        "scope_rejection_reasons",
        "composer_rejection_reasons",
        "gate_rejection_reasons",
        "coverage_unclassified_reasons",
        "coverage_unmapped_reasons",
    ):
        values.extend(_scorecard_list(summary.get(key)))
    extension = summary.get("step2_diagnostic_summary_extension")
    if isinstance(extension, Mapping):
        values.extend(_scorecard_list(extension.get("reason_codes")))
    return _dedupe(values)


def _scorecard_binding_meta(summary: Mapping[str, Any]) -> Dict[str, Any]:
    for key in ("binding_diagnostic", "binding_presence", "binding", "step2_diagnostic_summary_extension", "diagnostic_summary_extension", "diagnostic_summary_v2"):
        value = summary.get(key)
        if not isinstance(value, Mapping):
            continue
        nested = value.get("binding")
        if isinstance(nested, Mapping):
            return dict(nested)
        return dict(value)
    return {}


def _scorecard_binding(summary: Mapping[str, Any]) -> Dict[str, Any]:
    binding = _scorecard_binding_meta(summary)
    binding_count = max(_scorecard_int(summary.get("binding_count")), _scorecard_int(binding.get("binding_count")))
    expected_count = max(_scorecard_int(summary.get("expected_binding_count")), _scorecard_int(binding.get("expected_binding_count")))
    if expected_count <= 0:
        expected_count = max(
            _scorecard_int(summary.get("body_sentence_count")),
            _scorecard_int(binding.get("body_sentence_count")),
            _scorecard_int(summary.get("sentence_count")),
            _scorecard_int(binding.get("sentence_count")),
        )
    binding_present = bool(summary.get("binding_present") or binding.get("binding_present") or binding_count > 0)
    binding_required = bool(summary.get("binding_required") or summary.get("binding_expected") or binding.get("binding_required") or binding.get("binding_expected") or expected_count > 0)
    missing_count = max(0, expected_count - binding_count)
    binding_missing = bool(summary.get("binding_missing") or binding.get("binding_missing") or missing_count > 0)
    relation_types = _dedupe([
        *_scorecard_list(summary.get("relation_types")),
        *_scorecard_list(binding.get("relation_types")),
    ])
    return {
        "binding_required": binding_required,
        "binding_expected": binding_required,
        "binding_present": binding_present,
        "binding_missing": binding_missing,
        "binding_count": binding_count,
        "expected_binding_count": expected_count,
        "missing_binding_count": missing_count,
        "relation_types": relation_types,
        "binding_version": str(binding.get("binding_version") or binding.get("version") or summary.get("binding_version") or "").strip(),
    }


def _scorecard_event_from_summary(summary: Mapping[str, Any]) -> Dict[str, Any]:
    status = _scorecard_status(summary.get("observation_status"))
    primary_reason = str(summary.get("primary_reason") or status).strip()
    groups = _scorecard_coverage_groups(summary)
    primary_group = groups[0] if groups else "unclassified"
    binding = _scorecard_binding(summary)
    expected_count = int(binding.get("expected_binding_count") or 0)
    binding_count = int(binding.get("binding_count") or 0)
    binding_numerator = min(binding_count, expected_count) if expected_count > 0 else 0
    return {
        "version": _LIMITED_COMPOSER_SCORECARD_EVENT_VERSION,
        "phase": "limited_composer_extension",
        "step": _LIMITED_COMPOSER_SCORECARD_STEP,
        "purpose": "coverage_group_status_and_binding_coverage_scorecard_event",
        "ready": bool(status and primary_reason and primary_group),
        "metric_complete": bool(status and primary_reason and primary_group),
        "observation_status": status,
        "passed": status == "passed",
        "rejected": status == "rejected",
        "unavailable": status == "unavailable",
        "safety_blocked": status == "safety_blocked",
        "primary_reason": primary_reason,
        "failed_stage": str(summary.get("failed_stage") or summary.get("stage") or "").strip(),
        "coverage_group": primary_group,
        "coverage_primary_group": primary_group,
        "coverage_groups": groups,
        "reason_codes": _scorecard_reason_codes(summary, primary_reason),
        "composer_status": str(summary.get("composer_status") or "").strip(),
        "composer_model": str(summary.get("composer_model") or "").strip(),
        "binding": binding,
        "binding_required": bool(binding.get("binding_required")),
        "binding_present": bool(binding.get("binding_present")),
        "binding_missing": bool(binding.get("binding_missing")),
        "binding_count": binding_count,
        "expected_binding_count": expected_count,
        "missing_binding_count": int(binding.get("missing_binding_count") or 0),
        "binding_coverage_numerator": binding_numerator,
        "binding_coverage_denominator": expected_count,
        "binding_coverage_rate": _scorecard_rate(binding_numerator, expected_count),
        "relation_types": list(binding.get("relation_types") or []),
        "raw_input_included": False,
        "raw_text_included": False,
    }


def _scorecard_empty_bucket(group_key: str) -> Dict[str, Any]:
    definition = _GROUP_BY_KEY.get(group_key)
    return {
        "coverage_group": group_key,
        "label": definition.label if definition else group_key,
        "record_count": 0,
        "eligible_count": 0,
        "passed": 0,
        "passed_count": 0,
        "rejected": 0,
        "rejected_count": 0,
        "unavailable": 0,
        "unavailable_count": 0,
        "safety_blocked": 0,
        "safety_blocked_count": 0,
        "status_counts": {status: 0 for status in _SCORECARD_STATUSES},
        "primary_reason_counts": {},
        "reason_counts": {},
        "binding_expected_count": 0,
        "binding_present_count": 0,
        "binding_missing_count": 0,
        "binding_sentence_expected_total": 0,
        "binding_sentence_present_total": 0,
        "binding_sentence_missing_total": 0,
        "binding_present_rate": 0.0,
        "binding_sentence_coverage_rate": 0.0,
        "passed_rate": 0.0,
        "relation_type_counts": {},
    }


def _increment_bucket_counter(bucket: Dict[str, Any], field: str, key: str, count: int = 1) -> None:
    key = str(key or "").strip()
    if not key:
        return
    values = dict(bucket.get(field) or {})
    values[key] = int(values.get(key) or 0) + int(count)
    bucket[field] = values


def _merge_scorecard_event(bucket: Dict[str, Any], event: Mapping[str, Any]) -> None:
    status = _scorecard_status(event.get("observation_status"))
    bucket["record_count"] = int(bucket.get("record_count") or 0) + 1
    if status in {"passed", "rejected", "unavailable"}:
        bucket["eligible_count"] = int(bucket.get("eligible_count") or 0) + 1
    counts = dict(bucket.get("status_counts") or {})
    counts[status] = int(counts.get(status) or 0) + 1
    bucket["status_counts"] = counts
    bucket[status] = int(bucket.get(status) or 0) + 1
    bucket[f"{status}_count"] = int(bucket.get(f"{status}_count") or 0) + 1
    primary_reason = str(event.get("primary_reason") or status).strip()
    _increment_bucket_counter(bucket, "primary_reason_counts", primary_reason)
    for reason in _scorecard_list(event.get("reason_codes")):
        _increment_bucket_counter(bucket, "reason_counts", reason)
    expected_count = _scorecard_int(event.get("expected_binding_count"))
    binding_count = _scorecard_int(event.get("binding_count"))
    missing_count = _scorecard_int(event.get("missing_binding_count"))
    if bool(event.get("binding_required")) or expected_count > 0:
        bucket["binding_expected_count"] = int(bucket.get("binding_expected_count") or 0) + 1
    if bool(event.get("binding_present")):
        bucket["binding_present_count"] = int(bucket.get("binding_present_count") or 0) + 1
    if bool(event.get("binding_missing")):
        bucket["binding_missing_count"] = int(bucket.get("binding_missing_count") or 0) + 1
    bucket["binding_sentence_expected_total"] = int(bucket.get("binding_sentence_expected_total") or 0) + expected_count
    bucket["binding_sentence_present_total"] = int(bucket.get("binding_sentence_present_total") or 0) + binding_count
    bucket["binding_sentence_missing_total"] = int(bucket.get("binding_sentence_missing_total") or 0) + missing_count
    for relation_type in _scorecard_list(event.get("relation_types")):
        _increment_bucket_counter(bucket, "relation_type_counts", relation_type)
    bucket["passed_rate"] = _scorecard_rate(int(bucket.get("passed_count") or 0), int(bucket.get("eligible_count") or 0))
    bucket["binding_present_rate"] = _scorecard_rate(int(bucket.get("binding_present_count") or 0), int(bucket.get("binding_expected_count") or 0))
    bucket["binding_sentence_coverage_rate"] = _scorecard_rate(int(bucket.get("binding_sentence_present_total") or 0), int(bucket.get("binding_sentence_expected_total") or 0))


def build_emlis_limited_composer_scorecard_event(*, diagnostic_summary: Mapping[str, Any] | None) -> Dict[str, Any]:
    return _scorecard_event_from_summary(_scorecard_mapping(diagnostic_summary))


def aggregate_emlis_limited_composer_scorecard_events(events: Sequence[Any] | Iterable[Any] | None = None) -> Dict[str, Any]:
    normalized = [
        dict(item) if isinstance(item, Mapping) and item.get("version") == _LIMITED_COMPOSER_SCORECARD_EVENT_VERSION else _scorecard_event_from_summary(_scorecard_source(item))
        for item in list(events or [])
    ]
    totals = _scorecard_empty_bucket("all")
    by_group: Dict[str, Dict[str, Any]] = {}
    for event in normalized:
        _merge_scorecard_event(totals, event)
        for group in _scorecard_list(event.get("coverage_groups")) or [str(event.get("coverage_group") or "unclassified")]:
            bucket = by_group.setdefault(group, _scorecard_empty_bucket(group))
            _merge_scorecard_event(bucket, event)
    rows = sorted(by_group.values(), key=lambda row: (-int(row.get("record_count") or 0), str(row.get("coverage_group") or "")))
    groups_needing_attention = [
        str(row.get("coverage_group") or "")
        for row in rows
        if int(row.get("rejected_count") or 0) or int(row.get("unavailable_count") or 0) or int(row.get("binding_missing_count") or 0)
    ]
    return {
        "version": _LIMITED_COMPOSER_SCORECARD_AGGREGATE_VERSION,
        "phase": "limited_composer_extension",
        "step": _LIMITED_COMPOSER_SCORECARD_STEP,
        "purpose": "aggregate_passed_rejected_unavailable_by_coverage_group_and_binding_coverage",
        "ready": bool(normalized),
        "scorecard_ready": bool(normalized),
        "event_count": len(normalized),
        "record_count": len(normalized),
        "totals": totals,
        "coverage_group_rows": rows,
        "by_coverage_group": {str(row.get("coverage_group") or ""): dict(row) for row in rows},
        "status_counts": dict(totals.get("status_counts") or {}),
        "primary_reason_counts": dict(totals.get("primary_reason_counts") or {}),
        "reason_counts": dict(totals.get("reason_counts") or {}),
        "binding_coverage": {
            "binding_expected_count": int(totals.get("binding_expected_count") or 0),
            "binding_present_count": int(totals.get("binding_present_count") or 0),
            "binding_missing_count": int(totals.get("binding_missing_count") or 0),
            "binding_present_rate": float(totals.get("binding_present_rate") or 0.0),
            "binding_sentence_expected_total": int(totals.get("binding_sentence_expected_total") or 0),
            "binding_sentence_present_total": int(totals.get("binding_sentence_present_total") or 0),
            "binding_sentence_missing_total": int(totals.get("binding_sentence_missing_total") or 0),
            "binding_sentence_coverage_rate": float(totals.get("binding_sentence_coverage_rate") or 0.0),
        },
        "groups_needing_attention": groups_needing_attention,
        "raw_input_included": False,
        "raw_text_included": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "reader_gate_relaxed": False,
    }


def build_emlis_limited_composer_scorecard_harness(*, diagnostic_summary: Mapping[str, Any] | None, records: Sequence[Any] | Iterable[Any] | None = None) -> Dict[str, Any]:
    event = build_emlis_limited_composer_scorecard_event(diagnostic_summary=diagnostic_summary or {})
    all_records: List[Any] = [event, *list(records or [])]
    aggregate = aggregate_emlis_limited_composer_scorecard_events(all_records)
    coverage_group = str(event.get("coverage_group") or "unclassified")
    group_scorecard = dict((aggregate.get("by_coverage_group") or {}).get(coverage_group) or {})
    return {
        "version": _LIMITED_COMPOSER_SCORECARD_HARNESS_VERSION,
        "phase": "limited_composer_extension",
        "target_step": _LIMITED_COMPOSER_SCORECARD_STEP,
        "step": _LIMITED_COMPOSER_SCORECARD_STEP,
        "purpose": "coverage_group_status_and_binding_coverage_scorecard_harness",
        "ready": bool(event.get("ready") and aggregate.get("ready")),
        "scorecard_ready": bool(event.get("ready") and aggregate.get("ready")),
        "event": event,
        "scorecard_event": event,
        "aggregate": aggregate,
        "scorecard_aggregate": aggregate,
        "coverage_group_scorecard": group_scorecard,
        "coverage_group_status_scorecard": group_scorecard,
        "coverage_group_rows": list(aggregate.get("coverage_group_rows") or []),
        "by_coverage_group": dict(aggregate.get("by_coverage_group") or {}),
        "coverage_group": coverage_group,
        "coverage_groups": list(event.get("coverage_groups") or []),
        "observation_status": str(event.get("observation_status") or ""),
        "primary_reason": str(event.get("primary_reason") or ""),
        "binding_coverage": dict(aggregate.get("binding_coverage") or {}),
        "groups_needing_attention": list(aggregate.get("groups_needing_attention") or []),
        "next_tasks_visible": True,
        "raw_input_included": False,
        "raw_text_included": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "input_specific_template_added": False,
        "fixed_completed_sentence_template_added": False,
    }


build_limited_composer_scorecard_harness = build_emlis_limited_composer_scorecard_harness
build_limited_composer_scorecard_event = build_emlis_limited_composer_scorecard_event
aggregate_limited_composer_scorecard_events = aggregate_emlis_limited_composer_scorecard_events


__all__ = [
    "COVERAGE_GROUP_ORDER",
    "aggregate_emlis_limited_composer_scorecard_events",
    "aggregate_limited_composer_scorecard_events",
    "build_emlis_coverage_matrix",
    "build_emlis_limited_composer_scorecard_event",
    "build_emlis_limited_composer_scorecard_harness",
    "build_limited_composer_scorecard_event",
    "build_limited_composer_scorecard_harness",
]
