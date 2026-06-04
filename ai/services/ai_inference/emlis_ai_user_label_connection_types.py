# -*- coding: utf-8 -*-
from __future__ import annotations

"""Internal types for EmlisAI User Label Connection Observation v1.

Phase 2 materializes backend-internal, text-free point/material structures.
Phase 3 adds backend-internal edge family scoring on top of that material.  The
classes do not generate ``comment_text``, do not add public response keys, and
must not be treated as RN/API/DB contract changes.
"""

from dataclasses import dataclass, field
from typing import Any, Final, Mapping

USER_LABEL_POINT_SCHEMA_VERSION: Final = "cocolon.emlis.user_label_point.v1"
USER_LABEL_CONNECTION_MATERIAL_SCHEMA_VERSION: Final = "cocolon.emlis.user_label_connection_material.v1"
USER_LABEL_CONNECTION_EDGE_SCORE_SCHEMA_VERSION: Final = "cocolon.emlis.user_label_connection_edge_score.v1"
USER_LABEL_CONNECTION_MATERIAL_STEP: Final = "UserLabelConnection_Material_v1"

SOURCE_KIND_CURRENT_INPUT: Final = "current_input"
SOURCE_KIND_LAST_INPUT: Final = "last_input"
SOURCE_KIND_SAME_DAY_RECENT_INPUT: Final = "same_day_recent_input"
SOURCE_KIND_SIMILAR_INPUT: Final = "similar_input"
SOURCE_KIND_DERIVED_USER_MODEL_ANCHOR: Final = "derived_user_model_anchor"

SOURCE_SCOPE_CURRENT_ONLY: Final = "current_input_only"
SOURCE_SCOPE_OWNED_HISTORY: Final = "current_input_with_owned_history"
SOURCE_SCOPE_OWNED_HISTORY_AND_CROSS_CORE: Final = "current_input_with_owned_history_and_cross_core"

RECORD_SCOPE_CURRENT_ONLY: Final = "current_only"
RECORD_SCOPE_CURRENT_PLUS_OWNED_HISTORY: Final = "current_plus_owned_history"
RECORD_SCOPE_BLOCKED_FREE_TIER: Final = "blocked_free_tier"
RECORD_SCOPE_BLOCKED_GROUNDING_BOUNDARY: Final = "blocked_grounding_boundary"

MATERIAL_QUALITY_NO_HISTORY_AVAILABLE: Final = "no_history_available"
MATERIAL_QUALITY_HISTORY_CONNECTION_CANDIDATE: Final = "history_connection_candidate"
MATERIAL_QUALITY_HISTORY_CONNECTION_BLOCKED: Final = "history_connection_blocked"
MATERIAL_QUALITY_LOW_INFORMATION_PROTECTED: Final = "low_information_protected"
MATERIAL_QUALITY_SAFETY_TRIAGE_REQUIRED: Final = "safety_triage_required"

EDGE_FAMILY_CATEGORY_STATE_RECURRENCE: Final = "category_state_recurrence"
EDGE_FAMILY_STATE_OUTPUT_ATTACHMENT: Final = "state_output_attachment"
EDGE_FAMILY_ACTION_STATE_BRIDGE: Final = "action_state_bridge"
EDGE_FAMILY_CATEGORY_OUTPUT_ROUTE: Final = "category_output_route"
EDGE_FAMILY_UNRESOLVED_WEIGHT_REAPPEARANCE: Final = "unresolved_weight_reappearance"
EDGE_FAMILY_VALUE_LINE_REAPPEARANCE: Final = "value_line_reappearance"
EDGE_FAMILY_LABEL_ROUTE_CURRENT_ALIGNMENT: Final = "label_route_current_alignment"
EDGE_FAMILY_CONTRAST_LINE_SHIFT: Final = "contrast_line_shift"
EDGE_FAMILY_RECOVERY_LABEL_ROUTE: Final = "recovery_label_route"

_ALLOWED_SOURCE_KINDS: Final = frozenset(
    {
        SOURCE_KIND_CURRENT_INPUT,
        SOURCE_KIND_LAST_INPUT,
        SOURCE_KIND_SAME_DAY_RECENT_INPUT,
        SOURCE_KIND_SIMILAR_INPUT,
        SOURCE_KIND_DERIVED_USER_MODEL_ANCHOR,
    }
)
_ALLOWED_SOURCE_SCOPES: Final = frozenset(
    {
        SOURCE_SCOPE_CURRENT_ONLY,
        SOURCE_SCOPE_OWNED_HISTORY,
        SOURCE_SCOPE_OWNED_HISTORY_AND_CROSS_CORE,
    }
)
_ALLOWED_RECORD_SCOPES: Final = frozenset(
    {
        RECORD_SCOPE_CURRENT_ONLY,
        RECORD_SCOPE_CURRENT_PLUS_OWNED_HISTORY,
        RECORD_SCOPE_BLOCKED_FREE_TIER,
        RECORD_SCOPE_BLOCKED_GROUNDING_BOUNDARY,
    }
)
_ALLOWED_MATERIAL_QUALITIES: Final = frozenset(
    {
        MATERIAL_QUALITY_NO_HISTORY_AVAILABLE,
        MATERIAL_QUALITY_HISTORY_CONNECTION_CANDIDATE,
        MATERIAL_QUALITY_HISTORY_CONNECTION_BLOCKED,
        MATERIAL_QUALITY_LOW_INFORMATION_PROTECTED,
        MATERIAL_QUALITY_SAFETY_TRIAGE_REQUIRED,
    }
)
_ALLOWED_STRENGTH_BUCKETS: Final = frozenset({"", "weak", "medium", "strong", "mixed", "unknown"})
_ALLOWED_SELECTED_AT_BUCKETS: Final = frozenset({"current", "same_day", "recent", "history", "unknown"})
_ALLOWED_SOURCE_FIELD_IDS: Final = frozenset(
    {"category", "emotion_details", "emotions", "strength", "memo_action", "memo", "created_at", "selected_at"}
)
_ALLOWED_EDGE_FAMILIES: Final = frozenset(
    {
        EDGE_FAMILY_CATEGORY_STATE_RECURRENCE,
        EDGE_FAMILY_STATE_OUTPUT_ATTACHMENT,
        EDGE_FAMILY_ACTION_STATE_BRIDGE,
        EDGE_FAMILY_CATEGORY_OUTPUT_ROUTE,
        EDGE_FAMILY_UNRESOLVED_WEIGHT_REAPPEARANCE,
        EDGE_FAMILY_VALUE_LINE_REAPPEARANCE,
        EDGE_FAMILY_LABEL_ROUTE_CURRENT_ALIGNMENT,
        EDGE_FAMILY_CONTRAST_LINE_SHIFT,
        EDGE_FAMILY_RECOVERY_LABEL_ROUTE,
    }
)


def _dedupe(values: tuple[str, ...] | list[str] | set[str]) -> tuple[str, ...]:
    out: list[str] = []
    for value in values:
        item = str(value or "").strip()
        if item and item not in out:
            out.append(item)
    return tuple(out)


def _validate_source_fields(values: tuple[str, ...], *, source: str) -> None:
    for value in values:
        if value not in _ALLOWED_SOURCE_FIELD_IDS:
            raise ValueError(f"unsupported source field id in {source}: {value}")


def _score(value: float) -> float:
    try:
        number = float(value)
    except Exception:
        return 0.0
    if number < 0.0:
        return 0.0
    if number > 1.0:
        return 1.0
    return round(number, 4)


@dataclass(frozen=True)
class UserLabelPoint:
    """One Cocolon input record normalized as a memory-label point.

    The point may keep user-selected labels, booleans, source field ids, counts,
    and evidence-anchor presence.  It never exposes raw memo/action text or raw
    record identifiers through ``as_meta``.
    """

    point_id: str
    source_kind: str
    source_scope: str = SOURCE_SCOPE_CURRENT_ONLY
    source_record_id_present: bool = False
    selected_at_present: bool = False
    category_labels: tuple[str, ...] = field(default_factory=tuple)
    emotion_labels: tuple[str, ...] = field(default_factory=tuple)
    strength_bucket: str = "unknown"
    has_action_axis: bool = False
    has_thought_axis: bool = False
    thought_token_fingerprint_count: int = 0
    selected_at_bucket: str = "unknown"
    environment_source_field_ids: tuple[str, ...] = field(default_factory=tuple)
    state_source_field_ids: tuple[str, ...] = field(default_factory=tuple)
    output_source_field_ids: tuple[str, ...] = field(default_factory=tuple)
    time_source_field_ids: tuple[str, ...] = field(default_factory=tuple)
    point_is_tendency: bool = False
    raw_text_included: bool = False
    raw_input_included: bool = False
    comment_text_body_included: bool = False
    schema_version: str = USER_LABEL_POINT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not str(self.point_id or "").strip():
            raise ValueError("UserLabelPoint.point_id is required")
        if self.source_kind not in _ALLOWED_SOURCE_KINDS:
            raise ValueError(f"unsupported source_kind: {self.source_kind}")
        if self.source_scope not in _ALLOWED_SOURCE_SCOPES:
            raise ValueError(f"unsupported source_scope: {self.source_scope}")
        if self.strength_bucket not in _ALLOWED_STRENGTH_BUCKETS:
            raise ValueError(f"unsupported strength_bucket: {self.strength_bucket}")
        if self.selected_at_bucket not in _ALLOWED_SELECTED_AT_BUCKETS:
            raise ValueError(f"unsupported selected_at_bucket: {self.selected_at_bucket}")
        _validate_source_fields(self.environment_source_field_ids, source="environment")
        _validate_source_fields(self.state_source_field_ids, source="state")
        _validate_source_fields(self.output_source_field_ids, source="output")
        _validate_source_fields(self.time_source_field_ids, source="time")
        if self.point_is_tendency:
            raise ValueError("a single UserLabelPoint must not be marked as tendency")
        if self.raw_text_included or self.raw_input_included or self.comment_text_body_included:
            raise ValueError("UserLabelPoint must remain text-free in public/meta form")

    def as_meta(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "point_id": self.point_id,
            "source_kind": self.source_kind,
            "source_scope": self.source_scope,
            "source_record_id_present": bool(self.source_record_id_present),
            "selected_at_present": bool(self.selected_at_present),
            "label_axes": {
                "environment": {
                    "category_labels": list(_dedupe(self.category_labels)),
                    "has_action_axis": bool(self.has_action_axis),
                    "source_field_ids": list(_dedupe(self.environment_source_field_ids)),
                },
                "state": {
                    "emotion_labels": list(_dedupe(self.emotion_labels)),
                    "strength_bucket": self.strength_bucket,
                    "source_field_ids": list(_dedupe(self.state_source_field_ids)),
                },
                "output": {
                    "has_thought_axis": bool(self.has_thought_axis),
                    "thought_token_fingerprint_count": int(max(0, self.thought_token_fingerprint_count)),
                    "source_field_ids": list(_dedupe(self.output_source_field_ids)),
                },
                "time": {
                    "selected_at_bucket": self.selected_at_bucket,
                    "source_field_ids": list(_dedupe(self.time_source_field_ids)),
                },
            },
            "evidence_anchor": {
                "record_id_hash_present": bool(self.source_record_id_present),
                "raw_text_included": False,
                "raw_input_included": False,
                "comment_text_body_included": False,
            },
            "point_is_tendency": False,
        }


@dataclass(frozen=True)
class UserLabelConnectionEdge:
    """Text-free connection edge produced by Phase 3 edge-family scoring.

    The score is only internal selection material.  It is exposed through
    ``as_meta`` with ``score_is_public=false`` so later public-meta plumbing can
    prove that numerical scoring is not a user-facing surface.
    """

    edge_id: str
    edge_family: str
    source_field_ids: tuple[str, ...] = field(default_factory=tuple)
    evidence_record_count: int = 0
    evidence_point_ids: tuple[str, ...] = field(default_factory=tuple)
    time_scope: str = "owned_history_window"
    source_scope_marker_required: bool = True
    soft_marker_required: bool = True
    line_is_candidate: bool = True
    line_is_fact: bool = False
    label_overlap_score: float = 0.0
    axis_overlap_score: float = 0.0
    evidence_record_count_score: float = 0.0
    current_alignment_score: float = 0.0
    low_information_penalty: float = 0.0
    safety_penalty: float = 0.0
    final_score: float = 0.0
    score_is_public: bool = False
    raw_text_included: bool = False
    comment_text_body_included: bool = False

    def __post_init__(self) -> None:
        if self.edge_family not in _ALLOWED_EDGE_FAMILIES:
            raise ValueError(f"unsupported edge_family: {self.edge_family}")
        _validate_source_fields(self.source_field_ids, source="connection_edge")
        if self.line_is_fact:
            raise ValueError("User Label Connection edges are candidates, not facts")
        if self.score_is_public:
            raise ValueError("UserLabelConnectionEdge score must not be public")
        if self.raw_text_included or self.comment_text_body_included:
            raise ValueError("UserLabelConnectionEdge must not carry raw text/comment bodies")

    def as_meta(self) -> dict[str, Any]:
        return {
            "edge_id": self.edge_id,
            "edge_family": self.edge_family,
            "source_field_ids": list(_dedupe(self.source_field_ids)),
            "evidence_record_count": int(max(0, self.evidence_record_count)),
            "evidence_point_ids": list(_dedupe(self.evidence_point_ids)),
            "time_scope": self.time_scope,
            "source_scope_marker_required": bool(self.source_scope_marker_required),
            "soft_marker_required": bool(self.soft_marker_required),
            "line_is_candidate": bool(self.line_is_candidate),
            "line_is_fact": False,
            "edge_score": {
                "schema_version": USER_LABEL_CONNECTION_EDGE_SCORE_SCHEMA_VERSION,
                "label_overlap_score": _score(self.label_overlap_score),
                "axis_overlap_score": _score(self.axis_overlap_score),
                "evidence_record_count_score": _score(self.evidence_record_count_score),
                "current_alignment_score": _score(self.current_alignment_score),
                "low_information_penalty": _score(self.low_information_penalty),
                "safety_penalty": _score(self.safety_penalty),
                "final_score": _score(self.final_score),
                "score_is_public": False,
            },
            "raw_text_included": False,
            "comment_text_body_included": False,
        }


@dataclass(frozen=True)
class UserLabelConnectionMaterial:
    """Meta-only material produced by Phase 2 and enriched by Phase 3.

    Phase 2 normalizes points and summaries.  Phase 3 may attach dynamic
    connection edges and private scores.  Candidate construction, gates,
    surface plans, and visible text connection remain deferred to later phases.
    """

    source_scope: str
    record_scope: str
    capability_tier: str
    history_read_allowed: bool
    user_fact_grounding_boundary_passed: bool
    low_information_protected: bool
    current_point: UserLabelPoint | None = None
    owned_history_points: tuple[UserLabelPoint, ...] = field(default_factory=tuple)
    connection_edges: tuple[UserLabelConnectionEdge, ...] = field(default_factory=tuple)
    material_quality: str = MATERIAL_QUALITY_NO_HISTORY_AVAILABLE
    same_day_count: int = 0
    similar_count: int = 0
    last_input_present: bool = False
    derived_user_model_anchor_count: int = 0
    schema_version: str = USER_LABEL_CONNECTION_MATERIAL_SCHEMA_VERSION
    step: str = USER_LABEL_CONNECTION_MATERIAL_STEP

    def __post_init__(self) -> None:
        if self.source_scope not in _ALLOWED_SOURCE_SCOPES:
            raise ValueError(f"unsupported material source_scope: {self.source_scope}")
        if self.record_scope not in _ALLOWED_RECORD_SCOPES:
            raise ValueError(f"unsupported record_scope: {self.record_scope}")
        if self.material_quality not in _ALLOWED_MATERIAL_QUALITIES:
            raise ValueError(f"unsupported material_quality: {self.material_quality}")
        if self.current_point is None:
            raise ValueError("current_point is required for UserLabelConnectionMaterial")

    @property
    def current_point_present(self) -> bool:
        return self.current_point is not None

    @property
    def owned_history_point_count(self) -> int:
        return len(self.owned_history_points)

    def owned_history_points_summary(self) -> dict[str, Any]:
        return {
            "available": bool(self.owned_history_points),
            "point_count": len(self.owned_history_points),
            "same_day_count": int(max(0, self.same_day_count)),
            "similar_count": int(max(0, self.similar_count)),
            "last_input_present": bool(self.last_input_present),
            "derived_user_model_anchor_count": int(max(0, self.derived_user_model_anchor_count)),
            "raw_text_included": False,
        }

    def as_meta(self) -> dict[str, Any]:
        current = self.current_point.as_meta() if self.current_point else None
        return {
            "schema_version": self.schema_version,
            "step": self.step,
            "source_scope": self.source_scope,
            "record_scope": self.record_scope,
            "capability_tier": self.capability_tier,
            "history_read_allowed": bool(self.history_read_allowed),
            "user_fact_grounding_boundary_passed": bool(self.user_fact_grounding_boundary_passed),
            "low_information_protected": bool(self.low_information_protected),
            "current_point_present": bool(current),
            "current_point": current,
            "owned_history_points_summary": self.owned_history_points_summary(),
            "owned_history_points": [point.as_meta() for point in self.owned_history_points],
            "connection_edges": [edge.as_meta() for edge in self.connection_edges],
            "connection_edge_count": len(self.connection_edges),
            "material_quality": self.material_quality,
            "phase2_point_builder_ready": True,
            "phase2_material_builder_ready": True,
            "phase3_edge_family_scoring_ready": True,
            "phase3_edge_family_scoring_deferred": False,
            "candidate_builder_deferred": True,
            "gate_deferred": True,
            "surface_plan_deferred": True,
            "comment_text_generated": False,
            "comment_text_generated_by_this_layer": False,
            "public_response_key_added": False,
            "api_route_changed": False,
            "request_key_changed": False,
            "response_shape_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_contract_changed": False,
            "rn_visible_title_changed": False,
            "raw_input_included": False,
            "raw_text_included": False,
            "history_raw_text_included": False,
            "comment_text_body_included": False,
            "candidate_body_included": False,
            "surface_body_included": False,
            "fixed_sentence_template_added": False,
            "external_ai_added": False,
            "local_llm_added": False,
        }


__all__ = [
    "USER_LABEL_POINT_SCHEMA_VERSION",
    "USER_LABEL_CONNECTION_MATERIAL_SCHEMA_VERSION",
    "USER_LABEL_CONNECTION_EDGE_SCORE_SCHEMA_VERSION",
    "USER_LABEL_CONNECTION_MATERIAL_STEP",
    "SOURCE_KIND_CURRENT_INPUT",
    "SOURCE_KIND_LAST_INPUT",
    "SOURCE_KIND_SAME_DAY_RECENT_INPUT",
    "SOURCE_KIND_SIMILAR_INPUT",
    "SOURCE_KIND_DERIVED_USER_MODEL_ANCHOR",
    "SOURCE_SCOPE_CURRENT_ONLY",
    "SOURCE_SCOPE_OWNED_HISTORY",
    "SOURCE_SCOPE_OWNED_HISTORY_AND_CROSS_CORE",
    "RECORD_SCOPE_CURRENT_ONLY",
    "RECORD_SCOPE_CURRENT_PLUS_OWNED_HISTORY",
    "RECORD_SCOPE_BLOCKED_FREE_TIER",
    "RECORD_SCOPE_BLOCKED_GROUNDING_BOUNDARY",
    "MATERIAL_QUALITY_NO_HISTORY_AVAILABLE",
    "MATERIAL_QUALITY_HISTORY_CONNECTION_CANDIDATE",
    "MATERIAL_QUALITY_HISTORY_CONNECTION_BLOCKED",
    "MATERIAL_QUALITY_LOW_INFORMATION_PROTECTED",
    "MATERIAL_QUALITY_SAFETY_TRIAGE_REQUIRED",
    "EDGE_FAMILY_CATEGORY_STATE_RECURRENCE",
    "EDGE_FAMILY_STATE_OUTPUT_ATTACHMENT",
    "EDGE_FAMILY_ACTION_STATE_BRIDGE",
    "EDGE_FAMILY_CATEGORY_OUTPUT_ROUTE",
    "EDGE_FAMILY_UNRESOLVED_WEIGHT_REAPPEARANCE",
    "EDGE_FAMILY_VALUE_LINE_REAPPEARANCE",
    "EDGE_FAMILY_LABEL_ROUTE_CURRENT_ALIGNMENT",
    "EDGE_FAMILY_CONTRAST_LINE_SHIFT",
    "EDGE_FAMILY_RECOVERY_LABEL_ROUTE",
    "UserLabelPoint",
    "UserLabelConnectionEdge",
    "UserLabelConnectionMaterial",
]
