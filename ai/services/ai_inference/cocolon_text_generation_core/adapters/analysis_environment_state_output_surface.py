# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 8 Analysis display connection for environment/state/output material.

This module turns Phase 7 ``analysis_environment_state_output_period_material``
into a bounded, public-display candidate for AnalysisComposer. It is purposely
small and conservative:

- it only uses aggregate counts / date counts / safe labels, never raw memo text
- tendency wording is period-scoped with 「この期間の記録では」
- recovery-label paths are sequence observations, not cures or prescriptions
- it returns composer-ready emotion-structure material rows for grounding
- it does not mutate content_json / standardReport / contentText by itself
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import re
from typing import Any, Final

ANALYSIS_ENVIRONMENT_STATE_OUTPUT_SURFACE_SCHEMA_VERSION: Final = "cocolon.analysis.environment_state_output_surface.v1"
ANALYSIS_ENVIRONMENT_STATE_OUTPUT_SURFACE_MATERIAL_ID: Final = "analysis_environment_state_output_surface"
ANALYSIS_ENVIRONMENT_STATE_OUTPUT_SURFACE_PHASE: Final = "Phase8_AnalysisComposer_display_connection"
ANALYSIS_ENVIRONMENT_STATE_OUTPUT_PERIOD_MATERIAL_ID: Final = "analysis_environment_state_output_period_material"
ANALYSIS_ENVIRONMENT_STATE_OUTPUT_COMPOSER_DOMAIN: Final = "emotion_structure"

SURFACE_STATUS_RENDERED: Final = "rendered"
SURFACE_STATUS_NO_DISPLAYABLE_MATERIAL: Final = "no_displayable_material"
SURFACE_STATUS_REJECTED: Final = "rejected"

_OUTPUT_THEME_LABELS: Final = {
    "continuation_concern": "継続できるかへの心配",
    "relation_loss_concern": "関係が離れることへの心配",
    "maintenance_concern": "維持できるかへの心配",
    "direction_concern": "方向性への心配",
    "unfairness_concern": "不公平さへの反応",
    "unrewarded_effort": "報われなさへの反応",
    "reason_became_visible": "理由が見えたこと",
    "unformed_self_insight": "まだ形になりきっていない自己理解",
}
_ALLOWED_RECURRENCE_LEVELS: Final = {
    "recurrence_candidate",
    "period_tendency_candidate",
    "strong_period_signal",
}
_FORBIDDEN_SURFACE_FRAGMENTS: Final = (
    "あなたはこういう人",
    "あなたの本質",
    "性格診断",
    "心理診断",
    "医療診断",
    "診断できます",
    "必ず",
    "絶対に",
    "完全に",
    "いつも",
    "原因です",
    "原因は",
    "仕事が原因",
    "カテゴリが原因",
    "感情の強さが原因",
    "戻りやすい",
    "回復方法",
    "治ります",
    "治る",
    "処方",
    "対処法です",
    "解決策です",
)
_SPACE_RE: Final = re.compile(r"\s+")
_TRIM: Final = " \t\r\n　、,。.!！?？『』「」\"'"


def _clean(value: Any, *, limit: int = 0) -> str:
    text = _SPACE_RE.sub(" ", str(value or "").replace("\r", " ").replace("\n", " ").replace("\u3000", " ")).strip(_TRIM)
    if limit > 0 and len(text) > limit:
        text = text[:limit].rstrip(_TRIM)
    return text


def _sequence(value: Any) -> list[Any]:
    if value in (None, ""):
        return []
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return list(value)
    return [value]


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return max(0, int(value or 0))
    except Exception:
        return default


def _period_label(period_scope: Mapping[str, Any]) -> str:
    label = _clean(period_scope.get("label"), limit=80)
    if label:
        return label
    start = _clean(period_scope.get("start_at"), limit=10)
    end = _clean(period_scope.get("end_at"), limit=10)
    if start and end:
        return f"{start}〜{end}"
    kind = _clean(period_scope.get("kind"), limit=40)
    return kind or "この期間"


def _is_period_material(value: Any) -> bool:
    return isinstance(value, Mapping) and _clean(value.get("material_id")) == ANALYSIS_ENVIRONMENT_STATE_OUTPUT_PERIOD_MATERIAL_ID


def is_analysis_environment_state_output_period_material(value: Any) -> bool:
    """Return True when ``value`` is a Phase 7 Analysis ESO period material."""

    if _is_period_material(value):
        return True
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_is_period_material(item) for item in value)
    return False


def extract_analysis_environment_state_output_period_material(value: Any) -> Mapping[str, Any] | None:
    """Extract the first Phase 7 period material from mapping / sequence input."""

    if _is_period_material(value):
        return value  # type: ignore[return-value]
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for item in value:
            if _is_period_material(item):
                return item  # type: ignore[return-value]
    return None


def _theme_label(theme_id: Any) -> str:
    key = _clean(theme_id, limit=100)
    return _OUTPUT_THEME_LABELS.get(key, "")


def _tendency_sentence(tendency: Mapping[str, Any]) -> str:
    query = tendency.get("query_key") if isinstance(tendency.get("query_key"), Mapping) else {}
    env = _clean(query.get("environment_key"), limit=80)
    state = _clean(query.get("state_key"), limit=80)
    theme = _theme_label(query.get("output_theme_key"))
    record_count = _safe_int(tendency.get("record_count"))
    day_count = _safe_int(tendency.get("distinct_day_count"))
    recurrence_level = _clean(tendency.get("recurrence_level"), limit=80)
    if not env or not state or not theme or record_count < 2 or recurrence_level not in _ALLOWED_RECURRENCE_LEVELS:
        return ""
    day_phrase = f"、{day_count}日分にまたがって" if day_count >= 2 else ""
    return f"この期間の記録では、{env}カテゴリで{state}が選ばれた入力の中に、{theme}が{record_count}件{day_phrase}見えます。"


def _path_sentence(path: Mapping[str, Any]) -> str:
    candidate = path.get("path_candidate") if isinstance(path.get("path_candidate"), Mapping) else {}
    before = candidate.get("from") if isinstance(candidate.get("from"), Mapping) else {}
    after = candidate.get("to") if isinstance(candidate.get("to"), Mapping) else {}
    from_env = _clean(before.get("environment_key"), limit=80)
    from_state = _clean(before.get("state_key"), limit=80)
    from_theme = _theme_label(before.get("output_theme_key"))
    to_env = _clean(after.get("environment_key"), limit=80)
    to_state = _clean(after.get("state_key"), limit=80)
    to_theme = _theme_label(after.get("output_theme_key"))
    if not (from_env and from_state and to_env and to_state):
        return ""
    from_tail = f"、{from_theme}" if from_theme else ""
    to_tail = f"、{to_theme}" if to_theme else ""
    return f"その後の記録では、{from_env}カテゴリで{from_state}が出たあと{from_tail}、{to_env}カテゴリで{to_state}が選ばれた入力{to_tail}も見えます。"


def _surface_is_safe(text: str) -> bool:
    if not _clean(text):
        return False
    return not any(fragment in text for fragment in _FORBIDDEN_SURFACE_FRAGMENTS)


def _composer_material_row(*, row_id: str, text: str, category: str = "", emotion: str = "", meta: Mapping[str, Any] | None = None) -> dict[str, Any]:
    row: dict[str, Any] = {
        "id": row_id,
        "domain": ANALYSIS_ENVIRONMENT_STATE_OUTPUT_COMPOSER_DOMAIN,
        "summary": text,
    }
    if category:
        row["category"] = category
    if emotion:
        row["emotion"] = emotion
    if isinstance(meta, Mapping):
        row["phase8_meta"] = dict(meta)
    return row


def _tendency_source_claim(tendency: Mapping[str, Any], *, sentence: str, index: int) -> dict[str, Any]:
    query = tendency.get("query_key") if isinstance(tendency.get("query_key"), Mapping) else {}
    return {
        "claim_id": f"eso_tendency_claim_{index}",
        "claim_kind": "conditional_output_tendency_period_observation",
        "surface_text": sentence,
        "environment_key": _clean(query.get("environment_key"), limit=80),
        "state_key": _clean(query.get("state_key"), limit=80),
        "output_theme_key": _clean(query.get("output_theme_key"), limit=100),
        "record_count": _safe_int(tendency.get("record_count")),
        "distinct_day_count": _safe_int(tendency.get("distinct_day_count")),
        "matching_frame_ids": list(_sequence(tendency.get("matching_frame_ids"))),
        "representative_evidence_span_ids": list(_sequence(tendency.get("representative_evidence_span_ids"))),
        "claim_strength": "period_observed_recurrence",
        "must_include_period_scope": True,
        "diagnosis_allowed": False,
        "personality_type_allowed": False,
        "cause_claim_allowed": False,
    }


def _path_source_claim(path: Mapping[str, Any], *, sentence: str, index: int) -> dict[str, Any]:
    candidate = path.get("path_candidate") if isinstance(path.get("path_candidate"), Mapping) else {}
    return {
        "claim_id": f"eso_recovery_path_claim_{index}",
        "claim_kind": "recovery_label_path_sequence_observation",
        "surface_text": sentence,
        "path_candidate": dict(candidate),
        "recurrence_level": _clean(path.get("recurrence_level"), limit=80),
        "claim_strength": "sequence_observation",
        "must_not_call_cure": True,
        "must_not_prescribe": True,
        "treatment_claim_allowed": False,
        "recovery_prescription_allowed": False,
    }


def build_analysis_environment_state_output_surface_material(
    material: Mapping[str, Any] | None,
    *,
    max_tendency_items: int = 2,
    max_recovery_path_items: int = 1,
) -> dict[str, Any]:
    """Build a bounded AnalysisComposer display candidate from Phase 7 material.

    The returned object is still an internal adapter payload. Callers may pass
    ``content_text`` and ``composer_material_sources`` to AnalysisComposer; this
    function itself does not write to public response payloads.
    """

    source = material if isinstance(material, Mapping) else {}
    period_scope = dict(source.get("period_scope") or {}) if isinstance(source.get("period_scope"), Mapping) else {}
    period_label = _period_label(period_scope)
    source_summary = dict(source.get("source_summary") or {}) if isinstance(source.get("source_summary"), Mapping) else {}
    domain_boundary = dict(source.get("domain_boundary") or {}) if isinstance(source.get("domain_boundary"), Mapping) else {}
    tendencies = [item for item in _sequence(source.get("conditional_output_tendencies")) if isinstance(item, Mapping)]
    paths = [item for item in _sequence(source.get("recovery_label_paths")) if isinstance(item, Mapping)]

    source_claims: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    sentences: list[str] = []
    used_tendency_count = 0

    for tendency in tendencies:
        if used_tendency_count >= max(0, int(max_tendency_items or 0)):
            break
        sentence = _tendency_sentence(tendency)
        if not _surface_is_safe(sentence):
            continue
        claim = _tendency_source_claim(tendency, sentence=sentence, index=used_tendency_count + 1)
        query = tendency.get("query_key") if isinstance(tendency.get("query_key"), Mapping) else {}
        rows.append(
            _composer_material_row(
                row_id=claim["claim_id"],
                text=sentence,
                category=claim["environment_key"],
                emotion=claim["state_key"],
                meta={
                    "claim_kind": claim["claim_kind"],
                    "record_count": claim["record_count"],
                    "distinct_day_count": claim["distinct_day_count"],
                    "output_theme_key": _clean(query.get("output_theme_key"), limit=100),
                    "raw_text_included": False,
                },
            )
        )
        source_claims.append(claim)
        sentences.append(sentence)
        used_tendency_count += 1

    used_path_count = 0
    for path in paths:
        if used_path_count >= max(0, int(max_recovery_path_items or 0)):
            break
        sentence = _path_sentence(path)
        if not _surface_is_safe(sentence):
            continue
        claim = _path_source_claim(path, sentence=sentence, index=used_path_count + 1)
        candidate = claim.get("path_candidate") if isinstance(claim.get("path_candidate"), Mapping) else {}
        before = candidate.get("from") if isinstance(candidate.get("from"), Mapping) else {}
        rows.append(
            _composer_material_row(
                row_id=claim["claim_id"],
                text=sentence,
                category=_clean(before.get("environment_key"), limit=80),
                emotion=_clean(before.get("state_key"), limit=80),
                meta={
                    "claim_kind": claim["claim_kind"],
                    "recurrence_level": claim["recurrence_level"],
                    "raw_text_included": False,
                    "must_not_call_cure": True,
                    "must_not_prescribe": True,
                },
            )
        )
        source_claims.append(claim)
        sentences.append(sentence)
        used_path_count += 1

    content_text = "".join(sentences)
    status = SURFACE_STATUS_RENDERED if content_text and source_claims else SURFACE_STATUS_NO_DISPLAYABLE_MATERIAL
    if content_text and not _surface_is_safe(content_text):
        status = SURFACE_STATUS_REJECTED
        content_text = ""
        rows = []
        source_claims = []

    return {
        "schema_version": ANALYSIS_ENVIRONMENT_STATE_OUTPUT_SURFACE_SCHEMA_VERSION,
        "material_id": ANALYSIS_ENVIRONMENT_STATE_OUTPUT_SURFACE_MATERIAL_ID,
        "phase": ANALYSIS_ENVIRONMENT_STATE_OUTPUT_SURFACE_PHASE,
        "status": status,
        "source_material_id": _clean(source.get("material_id"), limit=120),
        "source_schema_version": _clean(source.get("schema_version"), limit=120),
        "period_scope": period_scope,
        "period_label": period_label,
        "source_summary": source_summary,
        "domain_boundary": {
            "source_domain_separated": bool(domain_boundary.get("source_domain_separated", True)),
            "emotion_self_structure_material_mixing_allowed": False,
            "analysis_composer_surface_connected": status == SURFACE_STATUS_RENDERED,
        },
        "content_text": content_text,
        "composer_domain": ANALYSIS_ENVIRONMENT_STATE_OUTPUT_COMPOSER_DOMAIN,
        "composer_material_sources": rows,
        "composer_material_fields": ["summary", "category", "emotion"],
        "source_claims": source_claims,
        "surface_policy": {
            "public_analysis_text_connected": status == SURFACE_STATUS_RENDERED,
            "must_include_period_scope": True,
            "required_scope_marker": "この期間の記録では",
            "recovery_label_path_surface_max_claim_strength": "sequence_observation",
            "must_not_call_cure": True,
            "must_not_prescribe": True,
            "diagnosis_allowed": False,
            "personality_type_allowed": False,
            "cause_from_category": False,
            "cause_from_emotion_strength": False,
            "record_count_required_for_tendency": 2,
            "raw_text_included": False,
            "content_json_mutation_allowed_here": False,
            "standardReport_contract_untouched": True,
            "contentText_contract_untouched": True,
            "forbidden_surface_fragments": list(_FORBIDDEN_SURFACE_FRAGMENTS),
        },
        "text_generation_connection": {
            "analysis_composer_required": True,
            "analysis_composer_input_domain": ANALYSIS_ENVIRONMENT_STATE_OUTPUT_COMPOSER_DOMAIN,
            "mode": "phase8_environment_state_output_surface_candidate",
            "raw_material_pass_through_allowed": False,
            "composer_material_sources_are_safe_summaries": True,
        },
    }


@dataclass(frozen=True)
class AnalysisEnvironmentStateOutputSurfaceConnection:
    surface_material: Mapping[str, Any]
    evaluation: Any
    phase: str = ANALYSIS_ENVIRONMENT_STATE_OUTPUT_SURFACE_PHASE
    adapter_name: str = "analysis_environment_state_output_surface.v1"
    meta: Mapping[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return bool(getattr(self.evaluation, "passed", False))

    @property
    def text(self) -> str:
        return str(getattr(self.evaluation, "text", "") or "") if self.passed else ""

    @property
    def save_allowed(self) -> bool:
        return bool(getattr(self.evaluation, "save_allowed", False))

    def as_meta(self) -> dict[str, Any]:
        eval_meta = self.evaluation.as_meta() if hasattr(self.evaluation, "as_meta") else {}
        return {
            "adapter_name": self.adapter_name,
            "phase": self.phase,
            "passed": self.passed,
            "save_allowed": self.save_allowed,
            "analysis_composer_surface_connected": True,
            "content_json_shape_changed": False,
            "standardReport_contract_untouched": True,
            "contentText_contract_untouched": True,
            "surface_material": {
                "schema_version": _clean(self.surface_material.get("schema_version"), limit=120),
                "material_id": _clean(self.surface_material.get("material_id"), limit=120),
                "status": _clean(self.surface_material.get("status"), limit=80),
                "period_scope": dict(self.surface_material.get("period_scope") or {}),
                "source_summary": dict(self.surface_material.get("source_summary") or {}),
                "source_claim_count": len(self.surface_material.get("source_claims") or []),
                "raw_text_included": False,
            },
            "evaluation": eval_meta,
            "meta": dict(self.meta or {}),
        }


__all__ = [
    "ANALYSIS_ENVIRONMENT_STATE_OUTPUT_SURFACE_SCHEMA_VERSION",
    "ANALYSIS_ENVIRONMENT_STATE_OUTPUT_SURFACE_MATERIAL_ID",
    "ANALYSIS_ENVIRONMENT_STATE_OUTPUT_SURFACE_PHASE",
    "ANALYSIS_ENVIRONMENT_STATE_OUTPUT_PERIOD_MATERIAL_ID",
    "ANALYSIS_ENVIRONMENT_STATE_OUTPUT_COMPOSER_DOMAIN",
    "SURFACE_STATUS_RENDERED",
    "SURFACE_STATUS_NO_DISPLAYABLE_MATERIAL",
    "SURFACE_STATUS_REJECTED",
    "AnalysisEnvironmentStateOutputSurfaceConnection",
    "build_analysis_environment_state_output_surface_material",
    "extract_analysis_environment_state_output_period_material",
    "is_analysis_environment_state_output_period_material",
]
