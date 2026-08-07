from __future__ import annotations

"""PCE-9A B01 causal RED for the future Piece v2 contract owner.

Authorized scope:
  PCE9A_B01_CONTRACT_VERSION_CAUSAL_RED_FREEZE_ONLY

Future production owner:
  ai/services/ai_inference/piece_v2_contract.py

Covered release-blocking contracts:
  PCE7-R008 structured payload / flat Piece text equality
  PCE7-R013 missing visibility defaults private and unknown visibility rejects
  PCE7-R027 required contract/version identities are present and exact
  PCE7-R037 public/monitoring serializers reject body-bearing or raw identity fields

The owner is loaded inside the test call.  While the owner is absent, collection
still succeeds and the call phase fails with one stable causal signature.  Import,
collection, fixture, network, credential and environment failures are explicitly
non-credit and must not be reclassified as this RED.
"""

import hashlib
import importlib.util
import json
from collections.abc import Mapping
from pathlib import Path
import sys
from types import ModuleType
from typing import Any, Callable

import pytest


_OWNER_MODULE_NAME = "piece_v2_contract"
_AI_ROOT = Path(__file__).resolve().parents[2]
_OWNER_PATH = _AI_ROOT / "services" / "ai_inference" / "piece_v2_contract.py"

_RED_SIGNATURE = "PCE9A_B01_PIECE_V2_CONTRACT_OWNER_IMPLEMENTATION_ABSENT_RED"
_NONCREDIT_IMPORT_SIGNATURE = "PCE9A_B01_OWNER_IMPORT_OR_LOAD_FAILURE_NONCREDIT"
_COVERED_RED_IDS = ("PCE7-R008", "PCE7-R013", "PCE7-R027", "PCE7-R037")

_EXPECTED_VERSIONS = {
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

_EXPECTED_PUBLIC_FIELDS = frozenset(
    {
        "format_type",
        "metrics",
        "owner_profile",
        "piece_id",
        "piece_text",
        "piece_text_hash",
        "public_id",
        "saved_at",
        "viewer_state",
        "visual_recipe",
        "visual_recipe_hash",
    }
)

_EXPECTED_OPS_EVENT_FIELDS = frozenset(
    {
        "app_build",
        "app_version",
        "aspect_ratio",
        "branding_mode",
        "duration_bucket",
        "error_code",
        "event_name",
        "event_version",
        "feature_state",
        "format_type",
        "hash_check_result",
        "http_status",
        "idempotency_replayed",
        "migration_stage",
        "occurred_at",
        "outcome",
        "platform",
        "request_id",
        "retry_count",
        "safety_state",
        "schema_version",
        "source_layer",
        "source_stage",
        "stage",
        "subscription_tier",
        "theme_id",
        "visibility_scope",
    }
)

_FORBIDDEN_OPS_FIELDS = (
    "analysis_inference",
    "content_payload",
    "content_payload_hash",
    "emlis_body",
    "error_message",
    "exception_message",
    "filename",
    "idempotency_key",
    "local_path",
    "message",
    "meta",
    "owner_user_id",
    "piece_id",
    "piece_text",
    "piece_text_hash",
    "preview_id",
    "raw_input",
    "recipient",
    "request_body",
    "response_body",
    "source_input_id",
    "supplemental_answer",
    "visual_recipe_hash",
)

_REQUIRED_PUBLIC_API = (
    "PieceContractError",
    "PIECE_V2_CONTRACT_VERSIONS",
    "PUBLIC_PIECE_FIELD_ALLOWLIST",
    "PIECE_OPS_EVENT_FIELD_ALLOWLIST",
    "canonical_json_bytes",
    "canonical_sha256_hex",
    "normalize_visibility_scope",
    "project_public_piece",
    "reconstruct_piece_text",
    "serialize_piece_ops_event",
    "validate_contract_versions",
    "validate_piece_text_binding",
)


def _load_future_owner() -> ModuleType:
    if not _OWNER_PATH.is_file():
        pytest.fail(_RED_SIGNATURE, pytrace=False)

    try:
        spec = importlib.util.spec_from_file_location(_OWNER_MODULE_NAME, _OWNER_PATH)
        if spec is None or spec.loader is None:
            raise RuntimeError("owner module spec unavailable")
        module = importlib.util.module_from_spec(spec)
        sys.modules[_OWNER_MODULE_NAME] = module
        spec.loader.exec_module(module)
        return module
    except Exception as exc:  # pragma: no cover - explicit noncredit branch
        pytest.fail(
            f"{_NONCREDIT_IMPORT_SIGNATURE}:{type(exc).__name__}",
            pytrace=False,
        )


def _require_callable(owner: ModuleType, name: str) -> Callable[..., Any]:
    value = getattr(owner, name, None)
    assert callable(value), f"PCE9A_B01_REQUIRED_CALLABLE_ABSENT:{name}"
    return value


def _assert_contract_error(
    owner: ModuleType,
    expected_code: str,
    operation: Callable[[], Any],
) -> None:
    error_type = getattr(owner, "PieceContractError")
    with pytest.raises(error_type) as captured:
        operation()
    assert getattr(captured.value, "code", None) == expected_code


def _content_payload(format_type: str, blocks: list[str]) -> dict[str, Any]:
    return {
        "body_blocks": blocks,
        "format_type": format_type,
        "language": "ja",
        "meaning_contract_version": "piece.content_meaning.v1",
        "safety_contract_version": "piece.public_safety_transformation.v1",
        "schema_version": "piece.content_payload.v1",
        "title": None,
    }


def test_b01_piece_v2_contract_owner_satisfies_r008_r013_r027_r037() -> None:
    """Freeze one exact future owner and four contract-level release blockers."""

    owner = _load_future_owner()

    for public_name in _REQUIRED_PUBLIC_API:
        assert hasattr(owner, public_name), (
            f"PCE9A_B01_REQUIRED_PUBLIC_API_ABSENT:{public_name}"
        )

    canonical_json_bytes = _require_callable(owner, "canonical_json_bytes")
    canonical_sha256_hex = _require_callable(owner, "canonical_sha256_hex")
    normalize_visibility_scope = _require_callable(owner, "normalize_visibility_scope")
    project_public_piece = _require_callable(owner, "project_public_piece")
    reconstruct_piece_text = _require_callable(owner, "reconstruct_piece_text")
    serialize_piece_ops_event = _require_callable(owner, "serialize_piece_ops_event")
    validate_contract_versions = _require_callable(owner, "validate_contract_versions")
    validate_piece_text_binding = _require_callable(owner, "validate_piece_text_binding")

    # R027: version identities are one exact immutable registry and are validated.
    assert dict(owner.PIECE_V2_CONTRACT_VERSIONS) == _EXPECTED_VERSIONS
    assert validate_contract_versions(dict(_EXPECTED_VERSIONS)) == _EXPECTED_VERSIONS

    missing_version = dict(_EXPECTED_VERSIONS)
    missing_version.pop("visual_catalog_version")
    _assert_contract_error(
        owner,
        "PIECE_REQUEST_INVALID",
        lambda: validate_contract_versions(missing_version),
    )

    wrong_version = dict(_EXPECTED_VERSIONS)
    wrong_version["piece_contract_version"] = "piece.record.v1"
    _assert_contract_error(
        owner,
        "PIECE_REQUEST_INVALID",
        lambda: validate_contract_versions(wrong_version),
    )

    extra_version = {**_EXPECTED_VERSIONS, "legacy_qna_version": "qna.v1"}
    _assert_contract_error(
        owner,
        "PIECE_REQUEST_INVALID",
        lambda: validate_contract_versions(extra_version),
    )

    # R008: canonical JSON/hash and structured-to-flat text equality are exact.
    canonical_input = {
        "z": 2,
        "a": "日本語",
        "nested": {"b": False, "a": None},
    }
    canonical_expected = (
        '{"a":"日本語","nested":{"a":null,"b":false},"z":2}'.encode("utf-8")
    )
    assert canonical_json_bytes(canonical_input) == canonical_expected
    assert canonical_json_bytes(canonical_input).endswith(b"\n") is False
    assert canonical_sha256_hex(canonical_input) == hashlib.sha256(
        canonical_expected
    ).hexdigest()

    essay_payload = _content_payload("short_essay", ["第一段落。", "第二段落。"])
    quote_payload = _content_payload("quote", ["一つの核。"])
    declaration_payload = _content_payload("declaration", ["私は選ぶ。", "ここから進む。"])

    assert reconstruct_piece_text(essay_payload) == "第一段落。\n\n第二段落。"
    assert reconstruct_piece_text(quote_payload) == "一つの核。"
    assert reconstruct_piece_text(declaration_payload) == "私は選ぶ。\nここから進む。"

    essay_text = "第一段落。\n\n第二段落。"
    essay_hash = hashlib.sha256(essay_text.encode("utf-8")).hexdigest()
    assert validate_piece_text_binding(essay_payload, essay_text, essay_hash) == essay_text

    _assert_contract_error(
        owner,
        "PIECE_HASH_MISMATCH",
        lambda: validate_piece_text_binding(
            essay_payload,
            "第一段落。\n第二段落。",
            essay_hash,
        ),
    )
    _assert_contract_error(
        owner,
        "PIECE_HASH_MISMATCH",
        lambda: validate_piece_text_binding(
            essay_payload,
            essay_text,
            "0" * 64,
        ),
    )

    # R013: only absence defaults private; unknown/present-invalid values reject.
    assert normalize_visibility_scope(None) == "private"
    assert normalize_visibility_scope("private") == "private"
    assert normalize_visibility_scope(" public ") == "public"
    for invalid_visibility in ("", "friends", "published", 1, True, []):
        _assert_contract_error(
            owner,
            "PIECE_REQUEST_INVALID",
            lambda value=invalid_visibility: normalize_visibility_scope(value),
        )

    # R037 public projection: source/internal fields never cross the allowlist.
    assert frozenset(owner.PUBLIC_PIECE_FIELD_ALLOWLIST) == _EXPECTED_PUBLIC_FIELDS
    public_source = {
        "content_payload": essay_payload,
        "format_type": "short_essay",
        "metrics": {"resonances": 2},
        "owner_profile": {"display_name": "Synthetic Owner"},
        "owner_user_id": "OWNER_ID_CANARY",
        "piece_id": "piece-1",
        "piece_text": essay_text,
        "piece_text_hash": essay_hash,
        "public_id": "piece:00000000-0000-4000-8000-000000000001",
        "raw_input": "RAW_INPUT_CANARY",
        "safety_trace": "SAFETY_TRACE_CANARY",
        "saved_at": "2026-08-08T00:00:00Z",
        "source_input_id": "SOURCE_ID_CANARY",
        "viewer_state": {"resonated": False},
        "visual_recipe": {"visual_recipe_version": "piece.visual_recipe.v1"},
        "visual_recipe_hash": "1" * 64,
    }
    public_projection = project_public_piece(public_source)
    assert set(public_projection) == _EXPECTED_PUBLIC_FIELDS
    serialized_projection = json.dumps(
        public_projection,
        ensure_ascii=False,
        sort_keys=True,
    )
    for canary in (
        "RAW_INPUT_CANARY",
        "SAFETY_TRACE_CANARY",
        "SOURCE_ID_CANARY",
        "OWNER_ID_CANARY",
    ):
        assert canary not in serialized_projection

    # R037 monitoring serializer: exact allowlist, no free-form/body/hash/raw IDs.
    assert frozenset(owner.PIECE_OPS_EVENT_FIELD_ALLOWLIST) == _EXPECTED_OPS_EVENT_FIELDS
    valid_event = {
        "event_name": "piece_preview_requested",
        "event_version": "1",
        "occurred_at": "2026-08-08T00:00:00Z",
        "outcome": "requested",
        "request_id": "request-1",
        "schema_version": "piece.ops_event.v1",
        "source_layer": "api",
        "stage": "preview",
        "visibility_scope": "private",
    }
    serialized_event = serialize_piece_ops_event(valid_event)
    assert isinstance(serialized_event, bytes)
    assert serialized_event == canonical_json_bytes(valid_event)

    for forbidden_field in _FORBIDDEN_OPS_FIELDS:
        body_bearing_event = dict(valid_event)
        body_bearing_event[forbidden_field] = "MONITORING_BODY_CANARY"
        _assert_contract_error(
            owner,
            "PIECE_REQUEST_INVALID",
            lambda payload=body_bearing_event: serialize_piece_ops_event(payload),
        )

    assert "MONITORING_BODY_CANARY" not in serialized_event.decode("utf-8")
    assert _COVERED_RED_IDS == (
        "PCE7-R008",
        "PCE7-R013",
        "PCE7-R027",
        "PCE7-R037",
    )
