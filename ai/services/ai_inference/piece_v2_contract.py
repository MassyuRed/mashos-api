from __future__ import annotations

"""Deterministic, side-effect-free Piece v2 contract owner (PCE-9A B01)."""

import copy
import hashlib
import json
import math
from collections.abc import Mapping
from types import MappingProxyType
from typing import Any


class PieceContractError(ValueError):
    """Stable body-free contract failure."""

    def __init__(self, code: str, detail: str | None = None) -> None:
        self.code = str(code or "PIECE_REQUEST_INVALID").strip() or "PIECE_REQUEST_INVALID"
        self.detail = str(detail or "").strip() or None
        super().__init__(self.code if self.detail is None else f"{self.code}:{self.detail}")


PIECE_V2_CONTRACT_VERSIONS = MappingProxyType(
    {
        "api_contract_version": "piece.api.v2",
        "content_meaning_version": "piece.content_meaning.v1",
        "content_payload_version": "piece.content_payload.v1",
        "data_contract_version": "piece.data_contract.v1",
        "export_contract_version": "piece.export_contract.v1",
        "format_owner_version": "piece.format_owner.v1",
        "layout_policy_version": "piece.long_text_layout.v1",
        "lifecycle_contract_version": "piece.record_lifecycle.v1",
        "piece_contract_version": "piece.record.v2",
        "quota_contract_version": "piece.quota_consumption.v1",
        "render_interface_version": "piece.render_interface.v1",
        "render_reproducibility_version": "piece.render_reproducibility.v1",
        "safety_contract_version": "piece.public_safety_transformation.v1",
        "source_lineage_version": "piece.source_lineage.v1",
        "visibility_access_version": "piece.visibility_access.v1",
        "visual_catalog_version": "piece.visual_catalog.v1",
        "visual_recipe_version": "piece.visual_recipe.v1",
    }
)

PUBLIC_PIECE_FIELD_ALLOWLIST = frozenset(
    {
        "format_type", "metrics", "owner_profile", "piece_id", "piece_text",
        "piece_text_hash", "public_id", "saved_at", "viewer_state",
        "visual_recipe", "visual_recipe_hash",
    }
)

PIECE_OPS_EVENT_FIELD_ALLOWLIST = frozenset(
    {
        "app_build", "app_version", "aspect_ratio", "branding_mode",
        "duration_bucket", "error_code", "event_name", "event_version",
        "feature_state", "format_type", "hash_check_result", "http_status",
        "idempotency_replayed", "migration_stage", "occurred_at", "outcome",
        "platform", "request_id", "retry_count", "safety_state",
        "schema_version", "source_layer", "source_stage", "stage",
        "subscription_tier", "theme_id", "visibility_scope",
    }
)

_CONTENT_FIELDS = frozenset(
    {
        "body_blocks", "format_type", "language", "meaning_contract_version",
        "safety_contract_version", "schema_version", "title",
    }
)
_REQUIRED_EVENT_FIELDS = frozenset(
    {
        "event_name", "event_version", "occurred_at", "outcome", "request_id",
        "schema_version", "source_layer", "stage",
    }
)
_EVENT_NAMES = frozenset(
    """piece_preview_requested piece_preview_succeeded piece_preview_failed
    piece_preview_mutated piece_preview_cancelled piece_save_requested
    piece_record_saved_private piece_record_saved_public piece_save_failed
    piece_quota_exhausted piece_idempotency_replayed piece_owner_history_loaded
    piece_owner_history_failed piece_visibility_changed piece_visibility_change_failed
    piece_delete_requested piece_delete_succeeded piece_delete_failed
    piece_access_denied piece_concealed_not_found piece_public_list_loaded
    piece_public_detail_loaded piece_public_read_recorded piece_resonance_changed
    piece_public_operation_denied piece_export_requested piece_export_succeeded
    piece_export_failed piece_share_opened piece_reexport_succeeded
    piece_reexport_failed piece_layout_unavailable piece_hash_mismatch
    piece_private_visibility_guard_failed piece_old_qna_residual_detected
    piece_migration_guard_failed piece_feature_disabled piece_rollback_activated
    piece_rollback_verified""".split()
)
_ENUMS = {
    "aspect_ratio": {"4:5", "9:16"},
    "branding_mode": {"required_small", "required_subtle", "off"},
    "duration_bucket": {"lt_100ms", "100_499ms", "500_1499ms", "1500_4999ms", "gte_5000ms"},
    "format_type": {"short_essay", "quote", "declaration"},
    "hash_check_result": {"match", "mismatch", "not_applicable"},
    "outcome": {"requested", "succeeded", "failed", "denied", "concealed", "replayed", "disabled"},
    "platform": {"ios", "android", "unknown"},
    "safety_state": {"ready", "adjusted", "unavailable", "not_applicable"},
    "source_layer": {"rn", "api", "service", "store", "db_rpc", "renderer", "migration"},
    "source_stage": {"normal_observation", "pre_question_observation", "refined_observation", "not_applicable"},
    "stage": {"source_resolve", "preview", "preview_mutation", "save", "owner_read", "visibility", "public_read", "resonance", "export", "delete", "migration", "rollback"},
    "subscription_tier": {"free", "plus", "premium", "unknown"},
    "theme_id": {"soft_paper", "quiet_night"},
    "visibility_scope": {"private", "public", "not_applicable"},
}


def _invalid(detail: str) -> PieceContractError:
    return PieceContractError("PIECE_REQUEST_INVALID", detail)


def _json_value(value: Any, path: str = "$") -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if math.isfinite(value):
            return value
        raise _invalid(f"non_finite:{path}")
    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise _invalid(f"non_string_key:{path}")
            out[key] = _json_value(item, f"{path}.{key}")
        return out
    if isinstance(value, list):
        return [_json_value(item, f"{path}[{i}]") for i, item in enumerate(value)]
    raise _invalid(f"unsupported_type:{path}:{type(value).__name__}")


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            _json_value(value), ensure_ascii=False, sort_keys=True,
            separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")
    except PieceContractError:
        raise
    except (TypeError, ValueError) as exc:
        raise _invalid("canonical_json_unavailable") from exc


def canonical_sha256_hex(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def validate_contract_versions(value: Mapping[str, Any]) -> dict[str, str]:
    if not isinstance(value, Mapping):
        raise _invalid("versions_not_mapping")
    expected, supplied = dict(PIECE_V2_CONTRACT_VERSIONS), dict(value)
    if set(supplied) != set(expected) or any(supplied[k] != v for k, v in expected.items()):
        raise _invalid("contract_versions_mismatch")
    return expected


def normalize_visibility_scope(value: Any) -> str:
    if value is None:
        return "private"
    if not isinstance(value, str):
        raise _invalid("visibility_type_invalid")
    normalized = value.strip()
    if normalized in {"private", "public"}:
        return normalized
    raise _invalid("visibility_value_invalid")


def _content(payload: Mapping[str, Any]) -> tuple[str, list[str]]:
    if not isinstance(payload, Mapping) or set(payload) != _CONTENT_FIELDS:
        raise _invalid("content_payload_shape_invalid")
    expected = {
        "schema_version": "piece.content_payload.v1",
        "meaning_contract_version": "piece.content_meaning.v1",
        "safety_contract_version": "piece.public_safety_transformation.v1",
        "title": None,
    }
    if any(payload.get(k) != v for k, v in expected.items()):
        raise _invalid("content_payload_contract_invalid")
    if payload.get("language") not in {"ja", "en", "mixed"}:
        raise _invalid("language_invalid")
    format_type, blocks = payload.get("format_type"), payload.get("body_blocks")
    if format_type not in {"short_essay", "quote", "declaration"} or not isinstance(blocks, list):
        raise _invalid("format_or_blocks_invalid")
    if not blocks or any(not isinstance(block, str) or not block or "\r" in block for block in blocks):
        raise _invalid("body_blocks_invalid")
    if format_type == "quote" and len(blocks) != 1:
        raise _invalid("quote_block_count_invalid")
    if format_type != "quote" and not 1 <= len(blocks) <= 3:
        raise _invalid("block_count_invalid")
    return format_type, list(blocks)


def reconstruct_piece_text(payload: Mapping[str, Any]) -> str:
    format_type, blocks = _content(payload)
    return ("\n\n" if format_type == "short_essay" else "\n").join(blocks) if format_type != "quote" else blocks[0]


def validate_piece_text_binding(payload: Mapping[str, Any], piece_text: Any, piece_text_hash: Any) -> str:
    reconstructed = reconstruct_piece_text(payload)
    expected_hash = hashlib.sha256(piece_text.encode("utf-8")).hexdigest() if isinstance(piece_text, str) else None
    if reconstructed != piece_text or piece_text_hash != expected_hash:
        raise PieceContractError("PIECE_HASH_MISMATCH")
    return piece_text


def project_public_piece(source: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(source, Mapping) or not PUBLIC_PIECE_FIELD_ALLOWLIST.issubset(source):
        raise _invalid("public_piece_shape_invalid")
    return {key: copy.deepcopy(source[key]) for key in sorted(PUBLIC_PIECE_FIELD_ALLOWLIST)}


def serialize_piece_ops_event(event: Mapping[str, Any]) -> bytes:
    if not isinstance(event, Mapping):
        raise _invalid("ops_event_not_mapping")
    fields = set(event)
    if not fields.issubset(PIECE_OPS_EVENT_FIELD_ALLOWLIST) or not _REQUIRED_EVENT_FIELDS.issubset(fields):
        raise _invalid("ops_event_shape_invalid")
    payload = dict(event)
    if any(not isinstance(payload[field], str) or not payload[field].strip() for field in _REQUIRED_EVENT_FIELDS):
        raise _invalid("ops_event_required_value_invalid")
    if payload["schema_version"] != "piece.ops_event.v1" or payload["event_version"] != "1":
        raise _invalid("ops_event_version_invalid")
    if payload["event_name"] not in _EVENT_NAMES:
        raise _invalid("ops_event_name_invalid")
    for field, allowed in _ENUMS.items():
        if field in payload and payload[field] not in allowed:
            raise _invalid(f"ops_event_enum_invalid:{field}")
    for field in ("error_code", "migration_stage", "feature_state", "app_version", "app_build"):
        if field in payload and (not isinstance(payload[field], str) or not payload[field].strip()):
            raise _invalid(f"ops_event_string_invalid:{field}")
    if "http_status" in payload and (isinstance(payload["http_status"], bool) or not isinstance(payload["http_status"], int) or not 100 <= payload["http_status"] <= 599):
        raise _invalid("ops_event_http_status_invalid")
    if "retry_count" in payload and (isinstance(payload["retry_count"], bool) or not isinstance(payload["retry_count"], int) or not 0 <= payload["retry_count"] <= 100):
        raise _invalid("ops_event_retry_count_invalid")
    if "idempotency_replayed" in payload and not isinstance(payload["idempotency_replayed"], bool):
        raise _invalid("ops_event_replay_invalid")
    return canonical_json_bytes(payload)


__all__ = [
    "PIECE_OPS_EVENT_FIELD_ALLOWLIST", "PIECE_V2_CONTRACT_VERSIONS",
    "PUBLIC_PIECE_FIELD_ALLOWLIST", "PieceContractError", "canonical_json_bytes",
    "canonical_sha256_hex", "normalize_visibility_scope", "project_public_piece",
    "reconstruct_piece_text", "serialize_piece_ops_event", "validate_contract_versions",
    "validate_piece_text_binding",
]
