# -*- coding: utf-8 -*-
"""P7-R47 R4/R5 local review packet schema/manifest contracts."""

from __future__ import annotations

import json

import pytest

from emlis_ai_p7_r47_local_review_packet_policy import (
    P7_R47_BODY_FREE_LOCAL_REVIEW_MANIFEST_SCHEMA_VERSION,
    P7_R47_BODY_FREE_MANIFEST_CASE_REF_FIELD_REFS,
    P7_R47_BODY_FREE_MANIFEST_FORBIDDEN_FIELD_REFS,
    P7_R47_BODY_FREE_MANIFEST_REQUIRED_FIELD_REFS,
    P7_R47_BODY_FULL_LOCAL_REVIEW_PACKET_SCHEMA_VERSION,
    P7_R47_BODY_FULL_PACKET_REQUIRED_FIELD_REFS,
    P7_R47_BODY_FULL_REVIEW_FORM_REQUIRED_FIELD_REFS,
    P7_R47_BODY_FULL_REVIEWER_PAYLOAD_FIELD_REFS,
    P7_R47_PACKET_KINDS,
    P7_R47_R4_R5_IMPLEMENTED_STEPS,
    P7_R47_R4_R5_NEXT_REQUIRED_STEP_REF,
    P7_R47_R4_R5_NOT_YET_IMPLEMENTED_STEPS,
    P7_R47_R4_R5_SCHEMA_FREEZE_SCHEMA_VERSION,
    P7_R47_REVIEWER_FACING_FORBIDDEN_FIELD_REFS,
    assert_p7_r47_body_free_local_review_manifest_payload_contract,
    assert_p7_r47_body_free_local_review_manifest_schema_contract,
    assert_p7_r47_body_full_local_review_packet_schema_contract,
    assert_p7_r47_r4_r5_schema_freeze_contract,
    build_p7_r47_body_free_local_review_manifest_schema,
    build_p7_r47_body_full_local_review_packet_schema,
    build_p7_r47_r4_r5_schema_freeze,
)

SECRET_INPUT = "R47 R4/R5 secret raw input must not enter schema freeze material"
SECRET_SURFACE = "R47 R4/R5 secret Emlis surface must not enter schema freeze material"
SECRET_REVIEWER = "R47 R4/R5 reviewer free text must not enter schema freeze material"
SECRET_ROOT = "/tmp/cocolon_emlis_r47_local_review_root"


def _dumped(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _assert_no_actual_body_or_release_promotion(value: dict[str, object]) -> None:
    dumped = _dumped(value)
    assert SECRET_INPUT not in dumped
    assert SECRET_SURFACE not in dumped
    assert SECRET_REVIEWER not in dumped
    assert SECRET_ROOT not in dumped
    assert '"raw_input":' not in dumped
    assert '"comment_text":' not in dumped
    assert '"candidate_body":' not in dumped
    assert '"surface_body":' not in dumped
    assert '"reviewer_free_text":' not in dumped
    assert '"terminal_output":' not in dumped
    assert '"release_allowed": true' not in dumped.lower()
    assert '"p7_complete": true' not in dumped.lower()
    assert '"p8_start_allowed": true' not in dumped.lower()
    assert '"hold004_close_allowed": true' not in dumped.lower()


def _body_free_manifest_payload() -> dict[str, object]:
    return {
        "schema_version": P7_R47_BODY_FREE_LOCAL_REVIEW_MANIFEST_SCHEMA_VERSION,
        "phase": "P7_ProductQualityRunner_LongRunGate",
        "step": "R47_LocalReviewPacketPolicy_20260618",
        "scope": "p7_r47_local_review_packet_storage_generation_disposal_policy",
        "manifest_kind": "body_free_local_review_manifest",
        "review_session_id": "review-session-001",
        "packet_kind": P7_R47_PACKET_KINDS[0],
        "case_refs": [
            {
                "blind_case_id": "blind-case-001",
                "case_ref_id": "case-ref-001",
                "family": "history_line_eligible_input",
                "subscription_tier": "plus",
                "packet_ref_id": "packet-ref-001",
                "body_free": True,
            }
        ],
        "local_body_packet_materialized_here": False,
        "body_full_packet_export_allowed": False,
        "body_free": True,
        "release_allowed": False,
        "p7_complete": False,
        "p8_start_allowed": False,
    }


def test_r47_r4_body_full_local_packet_schema_is_local_only_and_not_a_writer() -> None:
    schema = build_p7_r47_body_full_local_review_packet_schema()
    assert_p7_r47_body_full_local_review_packet_schema_contract(schema)

    assert schema["schema_version"] == P7_R47_BODY_FULL_LOCAL_REVIEW_PACKET_SCHEMA_VERSION
    assert schema["policy_section"] == "R4_body_full_local_packet_schema"
    assert schema["schema_definition_only"] is True
    assert schema["json_schema_file_created_here"] is False
    assert schema["local_only"] is True
    assert schema["must_not_export"] is True
    assert schema["must_not_enter_p7_material"] is True
    assert schema["disposal_required"] is True
    assert tuple(schema["packet_kind_enum"]) == P7_R47_PACKET_KINDS
    assert tuple(schema["required_field_refs"]) == P7_R47_BODY_FULL_PACKET_REQUIRED_FIELD_REFS
    assert tuple(schema["reviewer_payload_allowed_field_refs"]) == P7_R47_BODY_FULL_REVIEWER_PAYLOAD_FIELD_REFS
    assert tuple(schema["review_form_required_field_refs"]) == P7_R47_BODY_FULL_REVIEW_FORM_REQUIRED_FIELD_REFS
    assert schema["reviewer_facing_identifier_policy"] == "blind_case_id_only"
    assert set(P7_R47_REVIEWER_FACING_FORBIDDEN_FIELD_REFS).issubset(set(schema["reviewer_facing_forbidden_field_refs"]))
    assert set(schema["reviewer_payload_allowed_field_refs"]).isdisjoint(set(schema["reviewer_facing_forbidden_field_refs"]))
    assert schema["actual_body_full_packet_generated_here"] is False
    assert schema["body_full_writer_created_here"] is False
    assert schema["local_reviewer_payload_materialized_here"] is False
    assert schema["body_full_packet_schema_created_here"] is True
    assert schema["body_free_manifest_schema_created_here"] is False
    assert schema["release_allowed"] is False

    json_schema = schema["json_schema"]
    assert json_schema["$id"] == P7_R47_BODY_FULL_LOCAL_REVIEW_PACKET_SCHEMA_VERSION
    assert tuple(json_schema["required"]) == P7_R47_BODY_FULL_PACKET_REQUIRED_FIELD_REFS
    payload_props = json_schema["properties"]["reviewer_payload"]["properties"]
    assert tuple(payload_props.keys()) == P7_R47_BODY_FULL_REVIEWER_PAYLOAD_FIELD_REFS
    assert "family" not in json_schema["properties"]
    assert "case_ref_id" not in json_schema["properties"]

    _assert_no_actual_body_or_release_promotion(schema)


def test_r47_r5_body_free_manifest_schema_rejects_body_and_reviewer_text_fields() -> None:
    schema = build_p7_r47_body_free_local_review_manifest_schema()
    assert_p7_r47_body_free_local_review_manifest_schema_contract(schema)

    assert schema["schema_version"] == P7_R47_BODY_FREE_LOCAL_REVIEW_MANIFEST_SCHEMA_VERSION
    assert schema["policy_section"] == "R5_body_free_manifest_schema"
    assert schema["manifest_kind"] == "body_free_local_review_manifest"
    assert schema["schema_definition_only"] is True
    assert schema["json_schema_file_created_here"] is False
    assert tuple(schema["packet_kind_enum"]) == P7_R47_PACKET_KINDS
    assert tuple(schema["required_field_refs"]) == P7_R47_BODY_FREE_MANIFEST_REQUIRED_FIELD_REFS
    assert tuple(schema["case_ref_allowed_field_refs"]) == P7_R47_BODY_FREE_MANIFEST_CASE_REF_FIELD_REFS
    assert tuple(schema["forbidden_field_refs"]) == P7_R47_BODY_FREE_MANIFEST_FORBIDDEN_FIELD_REFS
    assert schema["forbidden_field_rejection_policy_fixed"] is True
    assert schema["local_body_packet_materialized_here"] is False
    assert schema["body_full_packet_export_allowed"] is False
    assert schema["actual_body_free_manifest_materialized_here"] is False
    assert schema["actual_body_full_packet_generated_here"] is False
    assert schema["body_full_writer_created_here"] is False
    assert schema["body_free_manifest_schema_created_here"] is True
    assert schema["release_allowed"] is False

    case_ref_props = schema["json_schema"]["properties"]["case_refs"]["items"]["properties"]
    assert tuple(case_ref_props.keys()) == P7_R47_BODY_FREE_MANIFEST_CASE_REF_FIELD_REFS
    for forbidden in P7_R47_BODY_FREE_MANIFEST_FORBIDDEN_FIELD_REFS:
        assert forbidden not in schema["json_schema"]["properties"]
        assert forbidden not in case_ref_props

    _assert_no_actual_body_or_release_promotion(schema)


def test_r47_r5_manifest_payload_contract_accepts_only_body_free_case_refs() -> None:
    manifest = _body_free_manifest_payload()
    assert_p7_r47_body_free_local_review_manifest_payload_contract(manifest)
    _assert_no_actual_body_or_release_promotion(manifest)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("raw_input", SECRET_INPUT),
        ("comment_text", SECRET_SURFACE),
        ("surface_body", SECRET_SURFACE),
        ("reviewer_free_text", SECRET_REVIEWER),
        ("terminal_output", "stdout/stderr must not enter manifest"),
    ],
)
def test_r47_r5_manifest_payload_contract_rejects_body_keys(key: str, value: str) -> None:
    manifest = _body_free_manifest_payload()
    manifest[key] = value
    with pytest.raises(ValueError):
        assert_p7_r47_body_free_local_review_manifest_payload_contract(manifest)


def test_r47_r5_manifest_payload_contract_rejects_case_ref_extra_body_key_and_release_promotion() -> None:
    manifest = _body_free_manifest_payload()
    manifest["case_refs"][0]["current_input_for_reviewer"] = SECRET_INPUT
    with pytest.raises(ValueError):
        assert_p7_r47_body_free_local_review_manifest_payload_contract(manifest)

    manifest = _body_free_manifest_payload()
    manifest["local_body_packet_materialized_here"] = True
    with pytest.raises(ValueError):
        assert_p7_r47_body_free_local_review_manifest_payload_contract(manifest)

    manifest = _body_free_manifest_payload()
    manifest["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_r47_body_free_local_review_manifest_payload_contract(manifest)


def test_r47_r4_r5_combined_schema_freeze_advances_only_to_schema_fixed_not_review_ready() -> None:
    freeze = build_p7_r47_r4_r5_schema_freeze(local_review_root=SECRET_ROOT, export_roots=("/mnt/data",))
    assert_p7_r47_r4_r5_schema_freeze_contract(freeze)

    assert freeze["schema_version"] == P7_R47_R4_R5_SCHEMA_FREEZE_SCHEMA_VERSION
    assert tuple(freeze["implemented_steps"]) == P7_R47_R4_R5_IMPLEMENTED_STEPS
    assert tuple(freeze["not_yet_implemented_steps"]) == P7_R47_R4_R5_NOT_YET_IMPLEMENTED_STEPS
    assert freeze["next_required_step"] == P7_R47_R4_R5_NEXT_REQUIRED_STEP_REF
    assert freeze["body_full_local_packet_schema_version"] == P7_R47_BODY_FULL_LOCAL_REVIEW_PACKET_SCHEMA_VERSION
    assert freeze["body_free_manifest_schema_version"] == P7_R47_BODY_FREE_LOCAL_REVIEW_MANIFEST_SCHEMA_VERSION
    assert freeze["body_full_local_packet_schema_fixed"] is True
    assert freeze["body_full_local_packet_schema_local_only"] is True
    assert freeze["body_full_local_packet_schema_must_not_export"] is True
    assert freeze["body_free_manifest_schema_fixed"] is True
    assert freeze["body_free_manifest_forbidden_field_policy_fixed"] is True
    assert freeze["body_full_packet_schema_created_here"] is True
    assert freeze["body_free_manifest_schema_created_here"] is True
    assert freeze["local_review_packet_policy_ready"] is False
    assert freeze["policy_ready"] is False
    assert freeze["r47_policy_ready"] is False
    assert freeze["p5_human_blind_qa_start_allowed_after_r4_r5"] is False
    assert freeze["p5_human_blind_qa_confirmed"] is False
    assert freeze["p6_limited_human_readfeel_start_allowed"] is False
    assert freeze["real_device_modal_review_start_allowed"] is False
    assert freeze["actual_body_full_packet_generated_here"] is False
    assert freeze["actual_body_free_manifest_materialized_here"] is False
    assert freeze["body_full_writer_created_here"] is False
    assert freeze["rating_row_schema_created_here"] is False
    assert freeze["disposal_policy_created_here"] is False
    assert freeze["release_allowed"] is False
    assert freeze["p7_complete"] is False
    assert freeze["p8_start_allowed"] is False
    assert freeze["hold004_close_allowed"] is False

    _assert_no_actual_body_or_release_promotion(freeze)


def test_r47_r4_r5_contracts_reject_schema_drift_and_false_readiness() -> None:
    body_full = build_p7_r47_body_full_local_review_packet_schema()
    body_full["json_schema"]["properties"]["family"] = {"type": "string"}
    with pytest.raises(ValueError):
        assert_p7_r47_body_full_local_review_packet_schema_contract(body_full)

    manifest_schema = build_p7_r47_body_free_local_review_manifest_schema()
    manifest_schema["json_schema"]["properties"]["case_refs"]["items"]["properties"]["comment_text"] = {"type": "string"}
    with pytest.raises(ValueError):
        assert_p7_r47_body_free_local_review_manifest_schema_contract(manifest_schema)

    freeze = build_p7_r47_r4_r5_schema_freeze(local_review_root=SECRET_ROOT, export_roots=("/mnt/data",))
    freeze["p5_human_blind_qa_start_allowed_after_r4_r5"] = True
    with pytest.raises(ValueError):
        assert_p7_r47_r4_r5_schema_freeze_contract(freeze)
