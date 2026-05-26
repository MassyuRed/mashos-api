# -*- coding: utf-8 -*-
from __future__ import annotations

"""EmlisAI environment-state-output surface contract completion helper.

This module owns only the pre-validation surface completion needed by the
single-record environment-state-output contract.  It does not relax Display
Gate, does not generate completed observation replies, and does not repair
forbidden overclaim surfaces.
"""

from dataclasses import dataclass
import re
from typing import Any, Mapping, Sequence

ENVIRONMENT_STATE_OUTPUT_SURFACE_CONTRACT_COMPLETION_VERSION = (
    "cocolon.emlis.environment_state_output_surface_contract_completion.v1"
)
DEFAULT_ENVIRONMENT_STATE_OUTPUT_SCOPE_MARKER = "今回の入力では"
DEFAULT_ENVIRONMENT_STATE_OUTPUT_SCOPE_MARKERS: tuple[str, ...] = (
    "今回の入力では",
    "今の入力では",
    "この入力では",
    "今回の記録では",
    "この記録では",
)
DEFAULT_ENVIRONMENT_STATE_OUTPUT_FORBIDDEN_SURFACE_CLAIMS: tuple[str, ...] = (
    "period_tendency_from_single_record",
    "personality_tendency",
    "diagnosis",
    "cause_from_category",
    "cause_from_emotion_strength",
    "recovery_prescription",
)

_PERIOD_TENDENCY_RE = re.compile(
    r"(?:いつも|毎回|たびに|度に|よく|繰り返し|くり返し|傾向|出やすい|なりやすい|しやすい|パターン|最近ずっと|このところ|しばらく|長く続いて|続いています|続いている)"
)
_PERSONALITY_RE = re.compile(r"(?:タイプ|性格|人格|本質|こういう人)")
_DIAGNOSIS_RE = re.compile(
    r"(?:診断|治療|病気|疾患|症状|トラウマ|障害|発達障害|ADHD|うつ|鬱|躁|不安障害|依存症|PTSD|医療|心理療法|心理学的)"
)
_CAUSE_CATEGORY_RE = re.compile(
    r"(?:(?:カテゴリ|仕事|職場|家庭|家族|学校|人間関係|生活|環境)[^。！？!?\n]{0,32}(?:原因|理由)|"
    r"(?:原因は|理由は|原因として|原因にな)[^。！？!?\n]{0,40}(?:カテゴリ|仕事|職場|家庭|家族|学校|人間関係|生活|環境))"
)
_CAUSE_EMOTION_STRENGTH_RE = re.compile(
    r"(?:(?:感情|不安|怒り|悲しみ|寂しさ|疲れ|自己理解|焦り|恐怖)[^。！？!?\n]{0,32}(?:原因|理由)|"
    r"(?:原因は|理由は|原因として|原因にな)[^。！？!?\n]{0,40}(?:感情|不安|怒り|悲しみ|寂しさ|疲れ|自己理解|焦り|恐怖|強さ|強度|強い))"
)
_CAUSE_UNSUPPORTED_RE = re.compile(r"(?:原因は|原因です|原因として|原因にな|理由は|理由です)")
_RECOVERY_RE = re.compile(
    r"(?:回復方法|治る|治ります|解決策|こうすれば|すれば戻れ|戻りやすい|戻れます|必要があります|すべきです|するべきです|べきです)"
)

_FORBIDDEN_CLAIM_ALIASES = {
    "period_tendency_from_single_record": "period_tendency_from_single_record",
    "period_tendency": "period_tendency_from_single_record",
    "personality_tendency": "personality_tendency",
    "personality_type": "personality_tendency",
    "diagnosis": "diagnosis",
    "diagnosis_surface": "diagnosis",
    "cause_from_category": "cause_from_category",
    "cause_from_emotion_strength": "cause_from_emotion_strength",
    "recovery_prescription": "recovery_prescription",
}
_FORBIDDEN_CLAIM_TO_REASON: dict[str, str] = {
    "period_tendency_from_single_record": "period_tendency_from_single_record_surface",
    "personality_tendency": "personality_tendency_surface",
    "diagnosis": "diagnosis_surface",
    "cause_from_category": "cause_from_category_surface",
    "cause_from_emotion_strength": "cause_from_emotion_strength_surface",
    "recovery_prescription": "recovery_prescription_surface",
}

@dataclass(frozen=True)
class EnvironmentStateOutputSurfaceContract:
    connected: bool = False
    single_record_only: bool = True
    scope_marker_required: bool = True
    required_scope_marker: str = DEFAULT_ENVIRONMENT_STATE_OUTPUT_SCOPE_MARKER
    allowed_scope_markers: tuple[str, ...] = DEFAULT_ENVIRONMENT_STATE_OUTPUT_SCOPE_MARKERS
    forbidden_surface_claims: tuple[str, ...] = DEFAULT_ENVIRONMENT_STATE_OUTPUT_FORBIDDEN_SURFACE_CLAIMS

    def as_meta(self) -> dict[str, Any]:
        return {
            "schema_version": "cocolon.emlis.environment_state_output_surface_contract.v1",
            "connected": bool(self.connected),
            "single_record_only": bool(self.single_record_only),
            "scope_marker_required": bool(self.scope_marker_required),
            "required_scope_marker": self.required_scope_marker,
            "allowed_scope_markers": list(self.allowed_scope_markers),
            "forbidden_surface_claims": list(self.forbidden_surface_claims),
            "display_gate_relaxed": False,
            "raw_input_included": False,
        }


@dataclass(frozen=True)
class ScopeMarkerCompletionResult:
    text: str
    evaluated: bool
    applied: bool
    skipped_reason: str = ""
    marker: str = ""
    target_line_index: int | None = None
    before_marker_present: bool = False
    after_marker_present: bool = False
    rejection_reasons: tuple[str, ...] = ()
    action: str = "skip"
    display_gate_relaxed: bool = False
    raw_input_included: bool = False

    def as_meta(self) -> dict[str, Any]:
        return {
            "schema_version": ENVIRONMENT_STATE_OUTPUT_SURFACE_CONTRACT_COMPLETION_VERSION,
            "evaluated": bool(self.evaluated),
            "applied": bool(self.applied),
            "scope_marker": self.marker or None,
            "target_line": "first_body_line" if self.target_line_index is not None else None,
            "target_line_index": self.target_line_index,
            "before_marker_present": bool(self.before_marker_present),
            "after_marker_present": bool(self.after_marker_present),
            "claim_rejection_reasons": list(self.rejection_reasons),
            "action": self.action,
            "skip_reason": self.skipped_reason or None,
            "display_gate_relaxed": False,
            "raw_input_included": False,
        }


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _clean_tuple(values: Any) -> tuple[str, ...]:
    if not isinstance(values, (list, tuple, set)):
        return ()
    out: list[str] = []
    for item in values:
        clean = _clean(item)
        if clean and clean not in out:
            out.append(clean)
    return tuple(out)


def _is_mapping(value: Any) -> bool:
    return isinstance(value, Mapping)


def _nested_mapping(source: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = source.get(key)
    return value if isinstance(value, Mapping) else {}


def normalize_environment_state_output_surface_contract(
    source: EnvironmentStateOutputSurfaceContract | Mapping[str, Any] | None,
) -> EnvironmentStateOutputSurfaceContract:
    """Normalize a frame/material/meta contract into a shared helper contract."""

    if isinstance(source, EnvironmentStateOutputSurfaceContract):
        return source
    if not isinstance(source, Mapping):
        return EnvironmentStateOutputSurfaceContract()

    nested_contract = source.get("environment_state_output_surface_contract")
    if isinstance(nested_contract, Mapping):
        return normalize_environment_state_output_surface_contract(nested_contract)

    for material_key in ("observation_structure_material", "observation_structure_dictionary"):
        material = source.get(material_key)
        if isinstance(material, Mapping):
            nested = normalize_environment_state_output_surface_contract(material)
            if nested.connected:
                return nested

    frame = source.get("environment_state_output_frame")
    if isinstance(frame, Mapping):
        return normalize_environment_state_output_surface_contract(frame)

    policy = _nested_mapping(source, "frame_policy") or _nested_mapping(source, "surface_policy")
    if not policy and isinstance(source.get("policy"), Mapping):
        policy = _nested_mapping(source, "policy")

    connected = bool(
        source.get("connected")
        or source.get("enabled")
        or source.get("environment_state_output_frame_limited_use")
        or source.get("material_id") == "environment_state_output_frame"
        or bool(policy)
    )
    single_record_only = bool(source.get("single_record_only", policy.get("single_record_only", True)))
    marker_required = bool(
        source.get(
            "scope_marker_required",
            source.get("must_use_scope_marker", policy.get("must_use_scope_marker", True)),
        )
    )
    marker = _clean(
        source.get("required_scope_marker")
        or source.get("scope_marker")
        or policy.get("scope_marker")
        or DEFAULT_ENVIRONMENT_STATE_OUTPUT_SCOPE_MARKER
    )
    allowed_markers = _clean_tuple(source.get("allowed_scope_markers")) or DEFAULT_ENVIRONMENT_STATE_OUTPUT_SCOPE_MARKERS
    if marker not in allowed_markers:
        marker = DEFAULT_ENVIRONMENT_STATE_OUTPUT_SCOPE_MARKER
    forbidden_claims = (
        _clean_tuple(source.get("forbidden_surface_claims"))
        or _clean_tuple(source.get("forbidden_claims"))
        or _clean_tuple(policy.get("forbidden_claims"))
        or DEFAULT_ENVIRONMENT_STATE_OUTPUT_FORBIDDEN_SURFACE_CLAIMS
    )
    return EnvironmentStateOutputSurfaceContract(
        connected=connected,
        single_record_only=single_record_only,
        scope_marker_required=marker_required,
        required_scope_marker=marker,
        allowed_scope_markers=allowed_markers,
        forbidden_surface_claims=forbidden_claims,
    )


def environment_state_output_scope_marker_present(text: Any, contract_source: EnvironmentStateOutputSurfaceContract | Mapping[str, Any] | None) -> bool:
    contract = normalize_environment_state_output_surface_contract(contract_source)
    body = _clean(text)
    if not body:
        return False
    return any(marker in body for marker in contract.allowed_scope_markers if marker)


def _active_forbidden_claims(
    contract_source: EnvironmentStateOutputSurfaceContract | Mapping[str, Any] | None = None,
) -> set[str]:
    contract = (
        normalize_environment_state_output_surface_contract(contract_source)
        if contract_source is not None
        else EnvironmentStateOutputSurfaceContract(
            forbidden_surface_claims=DEFAULT_ENVIRONMENT_STATE_OUTPUT_FORBIDDEN_SURFACE_CLAIMS
        )
    )
    raw_claims = contract.forbidden_surface_claims or DEFAULT_ENVIRONMENT_STATE_OUTPUT_FORBIDDEN_SURFACE_CLAIMS
    claims: set[str] = set()
    for claim in raw_claims:
        normalized = _FORBIDDEN_CLAIM_ALIASES.get(_clean(claim), _clean(claim))
        if normalized:
            claims.add(normalized)
    return claims or set(DEFAULT_ENVIRONMENT_STATE_OUTPUT_FORBIDDEN_SURFACE_CLAIMS)


def environment_state_output_forbidden_surface_rejection_reasons(
    text: Any,
    contract_source: EnvironmentStateOutputSurfaceContract | Mapping[str, Any] | None = None,
) -> tuple[str, ...]:
    body = _clean(text)
    if not body:
        return ()
    active_claims = _active_forbidden_claims(contract_source)
    reasons: list[str] = []
    if "period_tendency_from_single_record" in active_claims and _PERIOD_TENDENCY_RE.search(body):
        reasons.append(_FORBIDDEN_CLAIM_TO_REASON["period_tendency_from_single_record"])
    if "personality_tendency" in active_claims and _PERSONALITY_RE.search(body):
        reasons.append(_FORBIDDEN_CLAIM_TO_REASON["personality_tendency"])
    if "diagnosis" in active_claims and _DIAGNOSIS_RE.search(body):
        reasons.append(_FORBIDDEN_CLAIM_TO_REASON["diagnosis"])
    emotion_cause_claim = bool(_CAUSE_EMOTION_STRENGTH_RE.search(body))
    if "cause_from_emotion_strength" in active_claims and emotion_cause_claim:
        reasons.append(_FORBIDDEN_CLAIM_TO_REASON["cause_from_emotion_strength"])
    if "cause_from_category" in active_claims and (
        _CAUSE_CATEGORY_RE.search(body) or (_CAUSE_UNSUPPORTED_RE.search(body) and not emotion_cause_claim)
    ):
        reasons.append(_FORBIDDEN_CLAIM_TO_REASON["cause_from_category"])
    if "recovery_prescription" in active_claims and _RECOVERY_RE.search(body):
        reasons.append(_FORBIDDEN_CLAIM_TO_REASON["recovery_prescription"])
    return tuple(dict.fromkeys(reasons))


def environment_state_output_surface_rejection_reasons(
    text: Any,
    contract_source: EnvironmentStateOutputSurfaceContract | Mapping[str, Any] | None,
) -> tuple[str, ...]:
    contract = normalize_environment_state_output_surface_contract(contract_source)
    if not contract.connected:
        return ()
    body = _clean(text)
    if not body:
        return ()
    reasons: list[str] = []
    if contract.scope_marker_required and not environment_state_output_scope_marker_present(body, contract):
        reasons.append("environment_state_output_scope_marker_missing")
    reasons.extend(environment_state_output_forbidden_surface_rejection_reasons(body, contract))
    return tuple(dict.fromkeys(reasons))


def _is_greeting_line(line: str) -> bool:
    clean = _clean(line)
    if not clean:
        return False
    if clean in {"こんにちは。", "こんにちは", "Emlisです。", "Emlisです", "エムリスです。", "エムリスです"}:
        return True
    if len(clean) <= 32 and "Emlis" in clean and (clean.endswith("です。") or clean.endswith("です") or clean.endswith("です！")):
        return True
    if len(clean) <= 32 and "エムリス" in clean and (clean.endswith("です。") or clean.endswith("です") or clean.endswith("です！")):
        return True
    return False


def _find_first_body_line_index(lines: Sequence[str]) -> int | None:
    for index, line in enumerate(lines):
        if not _clean(line):
            continue
        if _is_greeting_line(line):
            continue
        return index
    return None


def _finish_sentence(line: str) -> str:
    clean = _clean(line)
    if not clean:
        return clean
    if clean.endswith(("。", "！", "!", "？", "?")):
        return clean
    return f"{clean}。"


def _prefix_scope_marker(line: str, marker: str) -> str:
    clean = _clean(line)
    marker = _clean(marker) or DEFAULT_ENVIRONMENT_STATE_OUTPUT_SCOPE_MARKER
    if not clean:
        return clean
    if clean.startswith("今は、"):
        return _finish_sentence(f"{marker}、{clean[len('今は、'):]}")
    return _finish_sentence(f"{marker}、{clean.lstrip('、，')}")



def environment_state_output_scoped_line(
    line: Any,
    marker: Any = DEFAULT_ENVIRONMENT_STATE_OUTPUT_SCOPE_MARKER,
    *,
    allowed_markers: Sequence[str] = DEFAULT_ENVIRONMENT_STATE_OUTPUT_SCOPE_MARKERS,
) -> str:
    """Return a single line with the scope marker applied once.

    This keeps the legacy line-level helper available while routing the actual
    marker formatting through the shared Phase 1 completion rules.
    """

    clean = _clean(line)
    marker_text = _clean(marker) or DEFAULT_ENVIRONMENT_STATE_OUTPUT_SCOPE_MARKER
    markers = tuple(str(item or "").strip() for item in allowed_markers if str(item or "").strip())
    if not clean:
        return clean
    if any(scope_marker in clean for scope_marker in markers):
        return clean
    return _prefix_scope_marker(clean, marker_text)

def complete_environment_state_output_scope_marker(
    text: Any,
    contract_source: EnvironmentStateOutputSurfaceContract | Mapping[str, Any] | None,
) -> ScopeMarkerCompletionResult:
    """Apply a single-record scope marker before public surface validation.

    The helper is idempotent.  It only repairs a missing scope marker; forbidden
    surface claims remain fail-closed and are reported as rejection reasons.
    """

    original_text = str(text or "")
    contract = normalize_environment_state_output_surface_contract(contract_source)
    marker = contract.required_scope_marker or DEFAULT_ENVIRONMENT_STATE_OUTPUT_SCOPE_MARKER

    if not contract.connected:
        return ScopeMarkerCompletionResult(
            text=original_text,
            evaluated=True,
            applied=False,
            skipped_reason="contract_not_connected",
            marker=marker,
            before_marker_present=environment_state_output_scope_marker_present(original_text, contract),
            after_marker_present=environment_state_output_scope_marker_present(original_text, contract),
            action="skip",
        )
    if not contract.single_record_only:
        return ScopeMarkerCompletionResult(
            text=original_text,
            evaluated=True,
            applied=False,
            skipped_reason="not_single_record",
            marker=marker,
            before_marker_present=environment_state_output_scope_marker_present(original_text, contract),
            after_marker_present=environment_state_output_scope_marker_present(original_text, contract),
            action="skip",
        )
    if not contract.scope_marker_required:
        return ScopeMarkerCompletionResult(
            text=original_text,
            evaluated=True,
            applied=False,
            skipped_reason="scope_marker_not_required",
            marker=marker,
            before_marker_present=environment_state_output_scope_marker_present(original_text, contract),
            after_marker_present=environment_state_output_scope_marker_present(original_text, contract),
            action="skip",
        )

    before_marker_present = environment_state_output_scope_marker_present(original_text, contract)
    if before_marker_present:
        claim_reasons = environment_state_output_forbidden_surface_rejection_reasons(original_text, contract)
        if claim_reasons:
            return ScopeMarkerCompletionResult(
                text=original_text,
                evaluated=True,
                applied=False,
                marker=marker,
                before_marker_present=True,
                after_marker_present=True,
                rejection_reasons=claim_reasons,
                action="reject",
            )
        return ScopeMarkerCompletionResult(
            text=original_text,
            evaluated=True,
            applied=False,
            marker=marker,
            before_marker_present=True,
            after_marker_present=True,
            action="continue",
        )

    if not _clean(original_text):
        return ScopeMarkerCompletionResult(
            text=original_text,
            evaluated=True,
            applied=False,
            marker=marker,
            before_marker_present=False,
            after_marker_present=False,
            rejection_reasons=("environment_state_output_empty_body",),
            action="reject",
        )

    claim_reasons = environment_state_output_forbidden_surface_rejection_reasons(original_text, contract)
    if claim_reasons:
        return ScopeMarkerCompletionResult(
            text=original_text,
            evaluated=True,
            applied=False,
            marker=marker,
            before_marker_present=False,
            after_marker_present=False,
            rejection_reasons=claim_reasons,
            action="reject",
        )

    lines = original_text.split("\n")
    target_index = _find_first_body_line_index(lines)
    if target_index is None:
        return ScopeMarkerCompletionResult(
            text=original_text,
            evaluated=True,
            applied=False,
            marker=marker,
            before_marker_present=False,
            after_marker_present=False,
            rejection_reasons=("environment_state_output_body_line_missing",),
            action="reject",
        )

    lines[target_index] = _prefix_scope_marker(lines[target_index], marker)
    completed_text = "\n".join(lines)
    after_marker_present = environment_state_output_scope_marker_present(completed_text, contract)
    if not after_marker_present:
        return ScopeMarkerCompletionResult(
            text=completed_text,
            evaluated=True,
            applied=False,
            marker=marker,
            target_line_index=target_index,
            before_marker_present=False,
            after_marker_present=False,
            rejection_reasons=("environment_state_output_scope_marker_missing",),
            action="reject",
        )

    claim_reasons = environment_state_output_forbidden_surface_rejection_reasons(completed_text, contract)
    if claim_reasons:
        return ScopeMarkerCompletionResult(
            text=completed_text,
            evaluated=True,
            applied=False,
            marker=marker,
            target_line_index=target_index,
            before_marker_present=False,
            after_marker_present=True,
            rejection_reasons=claim_reasons,
            action="reject",
        )

    return ScopeMarkerCompletionResult(
        text=completed_text,
        evaluated=True,
        applied=True,
        marker=marker,
        target_line_index=target_index,
        before_marker_present=False,
        after_marker_present=True,
        action="continue",
    )


__all__ = [
    "DEFAULT_ENVIRONMENT_STATE_OUTPUT_FORBIDDEN_SURFACE_CLAIMS",
    "DEFAULT_ENVIRONMENT_STATE_OUTPUT_SCOPE_MARKER",
    "DEFAULT_ENVIRONMENT_STATE_OUTPUT_SCOPE_MARKERS",
    "ENVIRONMENT_STATE_OUTPUT_SURFACE_CONTRACT_COMPLETION_VERSION",
    "EnvironmentStateOutputSurfaceContract",
    "ScopeMarkerCompletionResult",
    "complete_environment_state_output_scope_marker",
    "environment_state_output_forbidden_surface_rejection_reasons",
    "environment_state_output_scope_marker_present",
    "environment_state_output_scoped_line",
    "environment_state_output_surface_rejection_reasons",
    "normalize_environment_state_output_surface_contract",
]
