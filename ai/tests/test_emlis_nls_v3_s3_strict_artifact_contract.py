# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step 3 independent negative suite for NLS v3 artifact contracts."""

import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unicodedata
from typing import Any, Callable

import emlis_ai_nls_v3_artifact_contract as s3
from helpers import emlis_nls_v3_s0_s1_baseline as s01
from helpers import emlis_nls_v3_s2_sample_registry as s2


_AI_ROOT = Path(__file__).resolve().parents[1]
_REPO_ROOT = _AI_ROOT.parent
_INFERENCE_ROOT = _AI_ROOT / "services" / "ai_inference"
_FIXTURE_PATH = (
    _AI_ROOT
    / "tests"
    / "fixtures"
    / "emlis_nls_v3"
    / "contract"
    / "step3_valid_artifacts_v1.json"
)
_ATTACK_CATALOG_PATH = (
    _AI_ROOT / "tests" / "fixtures" / "emlis_nls_v3_s3_red_attack_catalog_20260715.json"
)
_RECEIPT_SCHEMA_PATH = (
    _AI_ROOT / "tests" / "schemas" / "emlis_nls_v3_case_evidence_receipt_v2.schema.json"
)
_STEP3_RECEIPT_PATH = (
    _AI_ROOT / "tests" / "fixtures" / "emlis_nls_v3_s3_contract_receipt_20260715.json"
)
_FROZEN_HASHES = {
    "step0": (
        _AI_ROOT / "tests" / "fixtures" / "emlis_nls_v3_s0_boundary_20260714.json",
        "57f0a583ca970c753bfe656627ca75879dd279ff4e2a1471ee2dd7b55586a024",
    ),
    "step1": (
        _AI_ROOT / "tests" / "fixtures" / "emlis_nls_v3_s1_baseline_receipt_20260714.json",
        "669835b0fdce3bc1e2e897325ab37b5f82abc9a353bc864993aa284083b7a518",
    ),
    "step2": (
        _AI_ROOT / "tests" / "fixtures" / "emlis_nls_v3_s2_corpus_registry_20260714.json",
        "7746ec94267fae0b89adbf8b5a676e469386fd3376275bc5197e39742941eb3d",
    ),
    "batch001": (
        _AI_ROOT / "tests" / "fixtures" / "emlis_nls_v3" / "generated" / "batch_001_manifest.json",
        "2b3308c4ada090539a2fc71c1cb235970aa0b90687b8d9633464ba61e94deba4",
    ),
}


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert type(value) is dict
    return value


def _bundle() -> dict[str, Any]:
    return _load(_FIXTURE_PATH)


def _ledger_authority(bundle: dict[str, Any]) -> s3.LedgerSourceAuthority:
    value = bundle["ledger_source_authority"]
    semantics = tuple(
        s3.TrustedSourceSemantic(
            source_id=row["source_id"],
            source_authority_code=row["source_authority_code"],
            source_role=row["source_role"],
            polarity=row["polarity"],
            modality=row["modality"],
            temporal_scope=row["temporal_scope"],
            topic_scope_ids=tuple(row["topic_scope_ids"]),
            referent_scope=row["referent_scope"],
            relation_type=row["relation_type"],
            relation_direction=row["relation_direction"],
        )
        for row in value["source_semantics"]
    )
    return s3.LedgerSourceAuthority(
        source_observation_plan_sha256=value["source_observation_plan_sha256"],
        source_observation_stage_context_sha256=value[
            "source_observation_stage_context_sha256"
        ],
        source_reception_opportunity_plan_sha256=value[
            "source_reception_opportunity_plan_sha256"
        ],
        response_eligibility_source_sha256=value[
            "response_eligibility_source_sha256"
        ],
        response_eligibility=value["response_eligibility"],
        source_policy_sha256=value["source_policy_sha256"],
        allowed_source_owners=tuple(value["allowed_source_owners"]),
        evidence_ids=frozenset(value["evidence_ids"]),
        nucleus_ids=frozenset(value["nucleus_ids"]),
        relation_ids=frozenset(value["relation_ids"]),
        unknown_boundary_ids=frozenset(value["unknown_boundary_ids"]),
        reception_opportunity_ids=frozenset(value["reception_opportunity_ids"]),
        topic_scope_ids=frozenset(value["topic_scope_ids"]),
        allowed_source_roles=tuple(value["allowed_source_roles"]),
        source_role_bindings=tuple(
            (row[0], row[1]) for row in value["source_role_bindings"]
        ),
        source_semantics=semantics,
        obligation_inventory_max=value["obligation_inventory_max"],
    )


def _receipt_authority(bundle: dict[str, Any]) -> s3.ReceiptLineageAuthority:
    return s3.ReceiptLineageAuthority(**bundle["receipt_lineage_authority"])


def _codes(issues: Any) -> set[str]:
    return {issue.code for issue in issues}


def _assert_code(issues: Any, expected: str) -> None:
    codes = _codes(issues)
    assert expected in codes, (expected, sorted(codes), issues)


def _assert_value_error(call: Callable[[], Any], expected: str) -> None:
    try:
        call()
    except ValueError as exc:
        assert expected in str(exc), (expected, str(exc))
    else:
        raise AssertionError(f"expected ValueError containing {expected}")


def _assert_rejected(issues: Any) -> None:
    assert issues, "malformed artifact was accepted"
    assert all(isinstance(issue, s3.ContractIssue) for issue in issues), issues


def _resign(value: dict[str, Any], field: str, prefix: str) -> None:
    value[field] = s3.derive_content_id(prefix, value, field)


def _dict_field_paths(value: Any, prefix: tuple[Any, ...] = ()) -> list[tuple[Any, ...]]:
    paths: list[tuple[Any, ...]] = []
    if type(value) is dict:
        for key, item in value.items():
            path = prefix + (key,)
            paths.append(path)
            paths.extend(_dict_field_paths(item, path))
    elif type(value) is list:
        for index, item in enumerate(value):
            paths.extend(_dict_field_paths(item, prefix + (index,)))
    return paths


def _delete_path(value: Any, path: tuple[Any, ...]) -> None:
    parent = value
    for component in path[:-1]:
        parent = parent[component]
    del parent[path[-1]]


def test_s3_hand_authored_valid_bundle_passes_all_owner_validators() -> None:
    bundle = _bundle()
    artifacts = bundle["artifacts"]
    assert s3.load_canonical_json_bytes(_FIXTURE_PATH.read_bytes()) == bundle
    assert s3.validate_observation_stage_context(
        artifacts["observation_stage_context"],
        original_input_bundle=bundle["parents"]["original_input_bundle"],
    ) == ()
    assert s3.validate_semantic_obligation_ledger(
        artifacts["semantic_obligation_ledger"], authority=_ledger_authority(bundle)
    ) == ()
    assert s3.validate_content_selection_plan(
        artifacts["content_selection_plan"],
        obligation_ledger=artifacts["semantic_obligation_ledger"],
    ) == ()
    assert s3.validate_discourse_plan(
        artifacts["discourse_plan"],
        content_plan=artifacts["content_selection_plan"],
        obligation_ledger=artifacts["semantic_obligation_ledger"],
    ) == ()
    assert s3.validate_surface_ast(
        artifacts["surface_ast"],
        discourse_plan=artifacts["discourse_plan"],
        obligation_ledger=artifacts["semantic_obligation_ledger"],
    ) == ()
    assert s3.validate_parsed_surface_witness(
        artifacts["parsed_surface_witness"],
        candidate_text_bytes=bundle["candidate_text"].encode("utf-8"),
    ) == ()
    assert s3.validate_verified_surface_binding(
        artifacts["verified_surface_binding"],
        parsed_surface_witness=artifacts["parsed_surface_witness"],
        obligation_ledger=artifacts["semantic_obligation_ledger"],
    ) == ()
    assert s3.validate_case_evidence_receipt(
        artifacts["case_evidence_receipt"], authority=_receipt_authority(bundle)
    ) == ()
    assert s3.validate_artifact_chain(
        artifacts,
        original_input_bundle=bundle["parents"]["original_input_bundle"],
        ledger_authority=_ledger_authority(bundle),
        candidate_text_bytes=bundle["candidate_text"].encode("utf-8"),
        receipt_authority=_receipt_authority(bundle),
    ) == ()


def test_s3_every_top_level_artifact_field_is_required() -> None:
    bundle = _bundle()
    artifacts = bundle["artifacts"]
    validators: dict[str, Callable[[dict[str, Any]], Any]] = {
        "observation_stage_context": lambda value: s3.validate_observation_stage_context(
            value,
            original_input_bundle=bundle["parents"]["original_input_bundle"],
        ),
        "semantic_obligation_ledger": lambda value: s3.validate_semantic_obligation_ledger(
            value, authority=_ledger_authority(bundle)
        ),
        "content_selection_plan": lambda value: s3.validate_content_selection_plan(
            value, obligation_ledger=artifacts["semantic_obligation_ledger"]
        ),
        "discourse_plan": lambda value: s3.validate_discourse_plan(
            value,
            content_plan=artifacts["content_selection_plan"],
            obligation_ledger=artifacts["semantic_obligation_ledger"],
        ),
        "surface_ast": lambda value: s3.validate_surface_ast(
            value,
            discourse_plan=artifacts["discourse_plan"],
            obligation_ledger=artifacts["semantic_obligation_ledger"],
        ),
        "parsed_surface_witness": lambda value: s3.validate_parsed_surface_witness(
            value, candidate_text_bytes=bundle["candidate_text"].encode("utf-8")
        ),
        "verified_surface_binding": lambda value: s3.validate_verified_surface_binding(
            value,
            parsed_surface_witness=artifacts["parsed_surface_witness"],
            obligation_ledger=artifacts["semantic_obligation_ledger"],
        ),
        "case_evidence_receipt": lambda value: s3.validate_case_evidence_receipt(
            value, authority=_receipt_authority(bundle)
        ),
    }
    checked = 0
    for owner, validator in validators.items():
        for field in artifacts[owner]:
            mutation = deepcopy(artifacts[owner])
            del mutation[field]
            _assert_code(validator(mutation), "MISSING_FIELD")
            checked += 1
    assert checked == 79


def test_s3_owner_and_nested_keysets_are_closed() -> None:
    bundle = _bundle()
    artifacts = bundle["artifacts"]

    mutation = deepcopy(artifacts["observation_stage_context"])
    mutation["question_text"] = "forbidden"
    _assert_code(
        s3.validate_observation_stage_context(
            mutation, original_input_bundle=bundle["parents"]["original_input_bundle"]
        ),
        "UNKNOWN_FIELD",
    )

    mutation = deepcopy(artifacts["semantic_obligation_ledger"])
    mutation["obligations"][0]["covered_obligation_ids"] = []
    _assert_code(
        s3.validate_semantic_obligation_ledger(
            mutation, authority=_ledger_authority(bundle)
        ),
        "UNKNOWN_FIELD",
    )

    mutation = deepcopy(artifacts["content_selection_plan"])
    mutation["final_text"] = "forbidden"
    _assert_code(
        s3.validate_content_selection_plan(
            mutation, obligation_ledger=artifacts["semantic_obligation_ledger"]
        ),
        "UNKNOWN_FIELD",
    )

    mutation = deepcopy(artifacts["discourse_plan"])
    mutation["nodes"][0]["wording"] = "forbidden"
    _assert_code(
        s3.validate_discourse_plan(
            mutation,
            content_plan=artifacts["content_selection_plan"],
            obligation_ledger=artifacts["semantic_obligation_ledger"],
        ),
        "UNKNOWN_FIELD",
    )

    for field in (
        "final_text",
        "covered_obligation_ids",
        "realized_unit_ids",
        "generator_span_map",
        "score",
        "gate_status",
    ):
        mutation = deepcopy(artifacts["surface_ast"])
        mutation[field] = [] if field.endswith("ids") or field.endswith("map") else "x"
        _assert_code(
            s3.validate_surface_ast(
                mutation,
                discourse_plan=artifacts["discourse_plan"],
                obligation_ledger=artifacts["semantic_obligation_ledger"],
            ),
            "UNKNOWN_FIELD",
        )

    mutation = deepcopy(artifacts["parsed_surface_witness"])
    mutation["semantic_atoms"][0]["obligation_id"] = "obl_fake0000000000"
    _assert_code(
        s3.validate_parsed_surface_witness(
            mutation, candidate_text_bytes=bundle["candidate_text"].encode("utf-8")
        ),
        "UNKNOWN_FIELD",
    )

    mutation = deepcopy(artifacts["verified_surface_binding"])
    mutation["covered_obligation_ids"] = []
    _assert_code(
        s3.validate_verified_surface_binding(
            mutation,
            parsed_surface_witness=artifacts["parsed_surface_witness"],
            obligation_ledger=artifacts["semantic_obligation_ledger"],
        ),
        "UNKNOWN_FIELD",
    )

    mutation = deepcopy(artifacts["case_evidence_receipt"])
    mutation["candidate_text"] = "forbidden"
    issues = s3.validate_case_evidence_receipt(
        mutation, authority=_receipt_authority(bundle)
    )
    _assert_code(issues, "UNKNOWN_FIELD")
    _assert_code(issues, "BODY_CONTENT_FORBIDDEN")

    validators: dict[str, Callable[[dict[str, Any]], Any]] = {
        "observation_stage_context": lambda value: s3.validate_observation_stage_context(
            value,
            original_input_bundle=bundle["parents"]["original_input_bundle"],
        ),
        "semantic_obligation_ledger": lambda value: s3.validate_semantic_obligation_ledger(
            value, authority=_ledger_authority(bundle)
        ),
        "content_selection_plan": lambda value: s3.validate_content_selection_plan(
            value, obligation_ledger=artifacts["semantic_obligation_ledger"]
        ),
        "discourse_plan": lambda value: s3.validate_discourse_plan(
            value,
            content_plan=artifacts["content_selection_plan"],
            obligation_ledger=artifacts["semantic_obligation_ledger"],
        ),
        "surface_ast": lambda value: s3.validate_surface_ast(
            value,
            discourse_plan=artifacts["discourse_plan"],
            obligation_ledger=artifacts["semantic_obligation_ledger"],
        ),
        "parsed_surface_witness": lambda value: s3.validate_parsed_surface_witness(
            value,
            candidate_text_bytes=bundle["candidate_text"].encode("utf-8"),
        ),
        "verified_surface_binding": lambda value: s3.validate_verified_surface_binding(
            value,
            parsed_surface_witness=artifacts["parsed_surface_witness"],
            obligation_ledger=artifacts["semantic_obligation_ledger"],
        ),
        "case_evidence_receipt": lambda value: s3.validate_case_evidence_receipt(
            value, authority=_receipt_authority(bundle)
        ),
    }
    nested_checked = 0
    for owner, validator in validators.items():
        for path in _dict_field_paths(artifacts[owner]):
            if len(path) == 1:
                continue
            mutation = deepcopy(artifacts[owner])
            _delete_path(mutation, path)
            _assert_code(validator(mutation), "MISSING_FIELD")
            nested_checked += 1
    assert nested_checked > 100


def test_s3_invalid_enums_are_rejected_by_each_owner() -> None:
    bundle = _bundle()
    artifacts = bundle["artifacts"]

    mutation = deepcopy(artifacts["observation_stage_context"])
    mutation["stage"] = "question_maybe"
    _assert_code(
        s3.validate_observation_stage_context(
            mutation, original_input_bundle=bundle["parents"]["original_input_bundle"]
        ),
        "ENUM_INVALID",
    )

    mutation = deepcopy(artifacts["semantic_obligation_ledger"])
    mutation["obligations"][0]["kind"] = "generic_summary"
    _assert_code(
        s3.validate_semantic_obligation_ledger(
            mutation, authority=_ledger_authority(bundle)
        ),
        "ENUM_INVALID",
    )

    mutation = deepcopy(artifacts["content_selection_plan"])
    mutation["depth"] = "verbose"
    _assert_code(
        s3.validate_content_selection_plan(
            mutation, obligation_ledger=artifacts["semantic_obligation_ledger"]
        ),
        "ENUM_INVALID",
    )

    mutation = deepcopy(artifacts["discourse_plan"])
    mutation["edges"][0]["type"] = "sounds_natural"
    _assert_code(
        s3.validate_discourse_plan(
            mutation,
            content_plan=artifacts["content_selection_plan"],
            obligation_ledger=artifacts["semantic_obligation_ledger"],
        ),
        "ENUM_INVALID",
    )

    mutation = deepcopy(artifacts["surface_ast"])
    mutation["sections"][0]["sentences"][0]["clauses"][0]["nodes"][0][
        "node_type"
    ] = "arbitrary_text"
    _assert_code(
        s3.validate_surface_ast(
            mutation,
            discourse_plan=artifacts["discourse_plan"],
            obligation_ledger=artifacts["semantic_obligation_ledger"],
        ),
        "ENUM_INVALID",
    )

    mutation = deepcopy(artifacts["parsed_surface_witness"])
    mutation["parse_status"] = "looks_valid"
    _assert_code(
        s3.validate_parsed_surface_witness(
            mutation, candidate_text_bytes=bundle["candidate_text"].encode("utf-8")
        ),
        "ENUM_INVALID",
    )

    mutation = deepcopy(artifacts["verified_surface_binding"])
    mutation["binding_status"] = "probably_matched"
    _assert_code(
        s3.validate_verified_surface_binding(
            mutation,
            parsed_surface_witness=artifacts["parsed_surface_witness"],
            obligation_ledger=artifacts["semantic_obligation_ledger"],
        ),
        "ENUM_INVALID",
    )

    mutation = deepcopy(artifacts["case_evidence_receipt"])
    mutation["sample_source"] = "unreviewed_external"
    _assert_code(
        s3.validate_case_evidence_receipt(
            mutation, authority=_receipt_authority(bundle)
        ),
        "ENUM_INVALID",
    )


def test_s3_bool_and_integer_types_are_never_coerced() -> None:
    bundle = _bundle()
    artifacts = bundle["artifacts"]

    mutation = deepcopy(artifacts["observation_stage_context"])
    mutation["body_free"] = 1
    _assert_code(
        s3.validate_observation_stage_context(
            mutation, original_input_bundle=bundle["parents"]["original_input_bundle"]
        ),
        "STRICT_BOOL_REQUIRED",
    )

    mutation = deepcopy(artifacts["semantic_obligation_ledger"])
    mutation["obligations"][0]["required"] = "true"
    _assert_code(
        s3.validate_semantic_obligation_ledger(
            mutation, authority=_ledger_authority(bundle)
        ),
        "STRICT_BOOL_REQUIRED",
    )

    mutation = deepcopy(artifacts["content_selection_plan"])
    mutation["section_budget"]["total_sentence_max"] = True
    _assert_code(
        s3.validate_content_selection_plan(
            mutation, obligation_ledger=artifacts["semantic_obligation_ledger"]
        ),
        "STRICT_INTEGER_REQUIRED",
    )

    mutation = deepcopy(artifacts["discourse_plan"])
    mutation["nodes"][0]["merge_eligible"] = 1
    _assert_code(
        s3.validate_discourse_plan(
            mutation,
            content_plan=artifacts["content_selection_plan"],
            obligation_ledger=artifacts["semantic_obligation_ledger"],
        ),
        "STRICT_BOOL_REQUIRED",
    )

    mutation = deepcopy(artifacts["surface_ast"])
    mutation["body_free"] = "true"
    _assert_code(
        s3.validate_surface_ast(
            mutation,
            discourse_plan=artifacts["discourse_plan"],
            obligation_ledger=artifacts["semantic_obligation_ledger"],
        ),
        "STRICT_BOOL_REQUIRED",
    )

    mutation = deepcopy(artifacts["parsed_surface_witness"])
    mutation["body_free_export_allowed"] = 0
    _assert_code(
        s3.validate_parsed_surface_witness(
            mutation, candidate_text_bytes=bundle["candidate_text"].encode("utf-8")
        ),
        "STRICT_BOOL_REQUIRED",
    )

    mutation = deepcopy(artifacts["verified_surface_binding"])
    mutation["bindings"][0]["match_candidate_count"] = True
    _assert_code(
        s3.validate_verified_surface_binding(
            mutation,
            parsed_surface_witness=artifacts["parsed_surface_witness"],
            obligation_ledger=artifacts["semantic_obligation_ledger"],
        ),
        "STRICT_INTEGER_REQUIRED",
    )

    mutation = deepcopy(artifacts["case_evidence_receipt"])
    mutation["body_free"] = 1
    _assert_code(
        s3.validate_case_evidence_receipt(
            mutation, authority=_receipt_authority(bundle)
        ),
        "STRICT_BOOL_REQUIRED",
    )


def test_s3_adversarial_nested_shapes_fail_closed_without_exceptions() -> None:
    bundle = _bundle()
    artifacts = bundle["artifacts"]

    mutation = deepcopy(artifacts["observation_stage_context"])
    mutation["allowed_source_roles"] = [["original_input"]]
    _assert_rejected(
        s3.validate_observation_stage_context(
            mutation, original_input_bundle=bundle["parents"]["original_input_bundle"]
        )
    )

    mutation = deepcopy(artifacts["semantic_obligation_ledger"])
    mutation["obligations"][1]["target_obligation_ids"] = 1
    _assert_rejected(
        s3.validate_semantic_obligation_ledger(
            mutation, authority=_ledger_authority(bundle)
        )
    )

    mutation = deepcopy(artifacts["content_selection_plan"])
    mutation["decisions"][0]["obligation_id"] = []
    _assert_rejected(
        s3.validate_content_selection_plan(
            mutation, obligation_ledger=artifacts["semantic_obligation_ledger"]
        )
    )

    mutation = deepcopy(artifacts["discourse_plan"])
    mutation["nodes"][0]["node_id"] = []
    _assert_rejected(
        s3.validate_discourse_plan(
            mutation,
            content_plan=artifacts["content_selection_plan"],
            obligation_ledger=artifacts["semantic_obligation_ledger"],
        )
    )

    mutation = deepcopy(artifacts["surface_ast"])
    mutation["sections"][0]["sentences"][0]["clauses"][0]["nodes"][0][
        "node_type"
    ] = {}
    _assert_rejected(
        s3.validate_surface_ast(
            mutation,
            discourse_plan=artifacts["discourse_plan"],
            obligation_ledger=artifacts["semantic_obligation_ledger"],
        )
    )

    mutation = deepcopy(artifacts["parsed_surface_witness"])
    mutation["semantic_atoms"][0]["kind"] = {}
    _assert_rejected(
        s3.validate_parsed_surface_witness(
            mutation, candidate_text_bytes=bundle["candidate_text"].encode("utf-8")
        )
    )

    mutation = deepcopy(artifacts["verified_surface_binding"])
    mutation["bindings"][0]["atom_id"] = []
    _assert_rejected(
        s3.validate_verified_surface_binding(
            mutation,
            parsed_surface_witness=artifacts["parsed_surface_witness"],
            obligation_ledger=artifacts["semantic_obligation_ledger"],
        )
    )

    mutation = deepcopy(artifacts["case_evidence_receipt"])
    mutation["hard_gate"]["failed_codes"] = [["NOT_A_CODE"]]
    _assert_rejected(
        s3.validate_case_evidence_receipt(
            mutation, authority=_receipt_authority(bundle)
        )
    )


def test_s3_duplicate_ids_and_references_are_rejected_owner_by_owner() -> None:
    bundle = _bundle()
    artifacts = bundle["artifacts"]

    mutation = deepcopy(artifacts["observation_stage_context"])
    mutation["allowed_source_roles"].append("original_input")
    _assert_code(
        s3.validate_observation_stage_context(
            mutation, original_input_bundle=bundle["parents"]["original_input_bundle"]
        ),
        "DUPLICATE_VALUE",
    )

    mutation = deepcopy(artifacts["semantic_obligation_ledger"])
    mutation["obligations"].append(deepcopy(mutation["obligations"][0]))
    _assert_code(
        s3.validate_semantic_obligation_ledger(
            mutation, authority=_ledger_authority(bundle)
        ),
        "DUPLICATE_ID",
    )

    mutation = deepcopy(artifacts["content_selection_plan"])
    mutation["decisions"].append(deepcopy(mutation["decisions"][0]))
    _assert_code(
        s3.validate_content_selection_plan(
            mutation, obligation_ledger=artifacts["semantic_obligation_ledger"]
        ),
        "DUPLICATE_ID",
    )

    mutation = deepcopy(artifacts["discourse_plan"])
    mutation["nodes"].append(deepcopy(mutation["nodes"][0]))
    _assert_code(
        s3.validate_discourse_plan(
            mutation,
            content_plan=artifacts["content_selection_plan"],
            obligation_ledger=artifacts["semantic_obligation_ledger"],
        ),
        "DUPLICATE_ID",
    )

    mutation = deepcopy(artifacts["surface_ast"])
    mutation["sections"][1]["sentences"][0]["clauses"][0]["clause_id"] = "cl_01"
    _assert_code(
        s3.validate_surface_ast(
            mutation,
            discourse_plan=artifacts["discourse_plan"],
            obligation_ledger=artifacts["semantic_obligation_ledger"],
        ),
        "DUPLICATE_ID",
    )

    mutation = deepcopy(artifacts["parsed_surface_witness"])
    mutation["semantic_atoms"][1]["atom_id"] = "atom_01"
    _assert_code(
        s3.validate_parsed_surface_witness(
            mutation, candidate_text_bytes=bundle["candidate_text"].encode("utf-8")
        ),
        "DUPLICATE_ID",
    )

    mutation = deepcopy(artifacts["verified_surface_binding"])
    mutation["bindings"].append(deepcopy(mutation["bindings"][0]))
    _assert_code(
        s3.validate_verified_surface_binding(
            mutation,
            parsed_surface_witness=artifacts["parsed_surface_witness"],
            obligation_ledger=artifacts["semantic_obligation_ledger"],
        ),
        "DUPLICATE_ID",
    )

    mutation = deepcopy(artifacts["case_evidence_receipt"])
    mutation["local_product_review"]["reason_codes"].append("INPUT_SPECIFIC")
    _assert_code(
        s3.validate_case_evidence_receipt(
            mutation, authority=_receipt_authority(bundle)
        ),
        "DUPLICATE_VALUE",
    )


def test_s3_each_owner_rejects_one_byte_parent_hash_drift() -> None:
    bundle = _bundle()
    artifacts = bundle["artifacts"]
    wrong = "0" * 64

    mutation = deepcopy(artifacts["observation_stage_context"])
    mutation["original_input_bundle_sha256"] = wrong
    _assert_code(
        s3.validate_observation_stage_context(
            mutation, original_input_bundle=bundle["parents"]["original_input_bundle"]
        ),
        "PARENT_HASH_MISMATCH",
    )

    mutation = deepcopy(artifacts["semantic_obligation_ledger"])
    mutation["source_observation_plan_sha256"] = wrong
    _resign(mutation, "ledger_id", "nls3obl_")
    issues = s3.validate_semantic_obligation_ledger(
        mutation, authority=_ledger_authority(bundle)
    )
    assert _codes(issues) == {"PARENT_HASH_MISMATCH"}, issues

    mutation = deepcopy(artifacts["content_selection_plan"])
    mutation["source_obligation_ledger_sha256"] = wrong
    _resign(mutation, "content_plan_id", "nls3cp_")
    issues = s3.validate_content_selection_plan(
        mutation, obligation_ledger=artifacts["semantic_obligation_ledger"]
    )
    assert _codes(issues) == {"PARENT_HASH_MISMATCH"}, issues

    mutation = deepcopy(artifacts["discourse_plan"])
    mutation["source_content_plan_sha256"] = wrong
    _resign(mutation, "discourse_plan_id", "nls3dp_")
    issues = s3.validate_discourse_plan(
        mutation,
        content_plan=artifacts["content_selection_plan"],
        obligation_ledger=artifacts["semantic_obligation_ledger"],
    )
    assert _codes(issues) == {"PARENT_HASH_MISMATCH"}, issues

    mutation = deepcopy(artifacts["surface_ast"])
    mutation["source_discourse_plan_sha256"] = wrong
    _resign(mutation, "surface_ast_id", "nls3ast_")
    issues = s3.validate_surface_ast(
        mutation,
        discourse_plan=artifacts["discourse_plan"],
        obligation_ledger=artifacts["semantic_obligation_ledger"],
    )
    assert _codes(issues) == {"PARENT_HASH_MISMATCH"}, issues

    mutation = deepcopy(artifacts["parsed_surface_witness"])
    mutation["candidate_text_sha256"] = wrong
    _assert_code(
        s3.validate_parsed_surface_witness(
            mutation, candidate_text_bytes=bundle["candidate_text"].encode("utf-8")
        ),
        "PARENT_HASH_MISMATCH",
    )

    mutation = deepcopy(artifacts["verified_surface_binding"])
    mutation["parsed_surface_witness_sha256"] = wrong
    _assert_code(
        s3.validate_verified_surface_binding(
            mutation,
            parsed_surface_witness=artifacts["parsed_surface_witness"],
            obligation_ledger=artifacts["semantic_obligation_ledger"],
        ),
        "PARENT_HASH_MISMATCH",
    )

    mutation = deepcopy(artifacts["case_evidence_receipt"])
    mutation["content_plan_commitment"] = wrong
    _assert_code(
        s3.validate_case_evidence_receipt(
            mutation, authority=_receipt_authority(bundle)
        ),
        "PARENT_HASH_MISMATCH",
    )

    forged_chain = deepcopy(artifacts)
    forged_ledger = forged_chain["semantic_obligation_ledger"]
    forged_ledger["schema_version"] = "cocolon.emlis.nls_v3.forged.v1"
    _resign(forged_ledger, "ledger_id", "nls3obl_")
    forged_content = forged_chain["content_selection_plan"]
    forged_content["source_obligation_ledger_sha256"] = s3.artifact_sha256(
        forged_ledger
    )
    _resign(forged_content, "content_plan_id", "nls3cp_")
    forged_discourse = forged_chain["discourse_plan"]
    forged_discourse["source_content_plan_sha256"] = s3.artifact_sha256(
        forged_content
    )
    _resign(forged_discourse, "discourse_plan_id", "nls3dp_")
    forged_ast = forged_chain["surface_ast"]
    forged_ast["source_discourse_plan_sha256"] = s3.artifact_sha256(
        forged_discourse
    )
    _resign(forged_ast, "surface_ast_id", "nls3ast_")
    forged_binding = forged_chain["verified_surface_binding"]
    forged_binding["source_obligation_ledger_sha256"] = s3.artifact_sha256(
        forged_ledger
    )
    chain_issues = s3.validate_artifact_chain(
        forged_chain,
        original_input_bundle=bundle["parents"]["original_input_bundle"],
        ledger_authority=_ledger_authority(bundle),
        candidate_text_bytes=bundle["candidate_text"].encode("utf-8"),
        receipt_authority=_receipt_authority(bundle),
    )
    assert any(
        issue.code == "SCHEMA_VERSION_MISMATCH"
        and issue.path == "$.semantic_obligation_ledger.schema_version"
        for issue in chain_issues
    ), chain_issues


def test_s3_future_stage_requires_resolved_upstream_authority() -> None:
    bundle = _bundle()
    original = bundle["parents"]["original_input_bundle"]
    original_hash = s3.artifact_sha256(original)
    question_hash = "a" * 64

    pre = deepcopy(bundle["artifacts"]["observation_stage_context"])
    pre.update(
        {
            "stage": "pre_question_observation",
            "question_need_decision_sha256": question_hash,
            "allowed_source_roles": ["original_input", "question_need_decision"],
        }
    )
    _assert_code(
        s3.validate_observation_stage_context(pre, original_input_bundle=original),
        "FUTURE_STAGE_AUTHORITY_REQUIRED",
    )
    trusted_pre = s3.TrustedFutureStageAuthority(
        authority_owner="question_system_core",
        question_need_decision_sha256=question_hash,
        permitted_stages=("pre_question_observation",),
        original_input_bundle_sha256=original_hash,
        supplemental_answer_bundle_sha256=None,
    )
    assert s3.validate_observation_stage_context(
        pre,
        original_input_bundle=original,
        trusted_future_authority=trusted_pre,
    ) == ()
    mixed_stage_chain = deepcopy(bundle["artifacts"])
    mixed_stage_chain["observation_stage_context"] = pre
    mixed_stage_issues = s3.validate_artifact_chain(
        mixed_stage_chain,
        original_input_bundle=original,
        ledger_authority=_ledger_authority(bundle),
        candidate_text_bytes=bundle["candidate_text"].encode("utf-8"),
        receipt_authority=_receipt_authority(bundle),
        trusted_future_authority=trusted_pre,
    )
    assert {
        issue.path
        for issue in mixed_stage_issues
        if issue.code == "PARENT_CHAIN_MISMATCH"
    } >= {
        "$.semantic_obligation_ledger.source_observation_stage_context_sha256",
        "$.case_evidence_receipt.observation_stage",
    }

    supplemental = {
        "schema_version": "cocolon.question.answer_bundle.commitment.v1",
        "answer_commitment": "b" * 64,
        "body_free": True,
    }
    supplemental_hash = s3.artifact_sha256(supplemental)
    refined = deepcopy(pre)
    refined.update(
        {
            "stage": "refined_observation",
            "supplemental_answer_bundle_sha256": supplemental_hash,
            "allowed_source_roles": [
                "original_input",
                "question_need_decision",
                "supplemental_answer",
            ],
        }
    )
    trusted_refined = s3.TrustedFutureStageAuthority(
        authority_owner="question_system_core",
        question_need_decision_sha256=question_hash,
        permitted_stages=("refined_observation",),
        original_input_bundle_sha256=original_hash,
        supplemental_answer_bundle_sha256=supplemental_hash,
    )
    _assert_code(
        s3.validate_observation_stage_context(
            refined,
            original_input_bundle=original,
            trusted_future_authority=trusted_refined,
        ),
        "SUPPLEMENTAL_SOURCE_REQUIRED",
    )
    assert s3.validate_observation_stage_context(
        refined,
        original_input_bundle=original,
        trusted_future_authority=trusted_refined,
        supplemental_answer_bundle=supplemental,
    ) == ()


def test_s3_obligation_references_and_bound_reception_are_closed() -> None:
    bundle = _bundle()
    ledger = bundle["artifacts"]["semantic_obligation_ledger"]

    mutation = deepcopy(ledger)
    mutation["obligations"][0]["evidence_ids"] = ["other_case_evidence"]
    _assert_code(
        s3.validate_semantic_obligation_ledger(
            mutation, authority=_ledger_authority(bundle)
        ),
        "UNRESOLVED_EVIDENCE_REFERENCE",
    )

    mutation = deepcopy(ledger)
    mutation["obligations"][1]["target_obligation_ids"] = []
    _assert_code(
        s3.validate_semantic_obligation_ledger(
            mutation, authority=_ledger_authority(bundle)
        ),
        "BOUND_RECEPTION_TARGET_REQUIRED",
    )

    mutation = deepcopy(ledger)
    mutation["required_obligation_ids"] = [mutation["required_obligation_ids"][0]]
    _assert_code(
        s3.validate_semantic_obligation_ledger(
            mutation, authority=_ledger_authority(bundle)
        ),
        "REQUIRED_SET_MISMATCH",
    )

    for field in ("distinctness_group", "forbidden_claim_codes"):
        mutation = deepcopy(ledger)
        mutation["obligations"][0][field] = (
            "入力本文をそのまま格納した文字列"
            if field == "distinctness_group"
            else ["入力本文をそのまま格納した文字列"]
        )
        _assert_code(
            s3.validate_semantic_obligation_ledger(
                mutation, authority=_ledger_authority(bundle)
            ),
            "PATTERN_MISMATCH",
        )


def test_s3_content_discourse_ast_cross_references_are_closed() -> None:
    bundle = _bundle()
    artifacts = bundle["artifacts"]

    mutation = deepcopy(artifacts["content_selection_plan"])
    mutation["decisions"][0]["status"] = "deferred_by_budget"
    issues = s3.validate_content_selection_plan(
        mutation, obligation_ledger=artifacts["semantic_obligation_ledger"]
    )
    _assert_code(issues, "REQUIRED_OBLIGATION_NOT_SELECTED")
    _assert_code(issues, "BOUND_RECEPTION_TARGET_NOT_SELECTED")

    mutation = deepcopy(artifacts["content_selection_plan"])
    mutation["section_budget"]["total_sentence_max"] = 1
    _assert_code(
        s3.validate_content_selection_plan(
            mutation, obligation_ledger=artifacts["semantic_obligation_ledger"]
        ),
        "BUDGET_RANGE_INVALID",
    )

    forged_parent = deepcopy(artifacts["semantic_obligation_ledger"])
    forged_parent["obligations"].append(deepcopy(forged_parent["obligations"][0]))
    mutation = deepcopy(artifacts["content_selection_plan"])
    mutation["source_obligation_ledger_sha256"] = s3.artifact_sha256(forged_parent)
    _resign(mutation, "content_plan_id", "nls3cp_")
    _assert_code(
        s3.validate_content_selection_plan(
            mutation, obligation_ledger=forged_parent
        ),
        "PARENT_ARTIFACT_INVALID",
    )

    mutation = deepcopy(artifacts["discourse_plan"])
    mutation["nodes"][1]["antecedent_node_ids"] = ["dn_missing"]
    _assert_code(
        s3.validate_discourse_plan(
            mutation,
            content_plan=artifacts["content_selection_plan"],
            obligation_ledger=artifacts["semantic_obligation_ledger"],
        ),
        "UNRESOLVED_NODE_REFERENCE",
    )

    mutation = deepcopy(artifacts["discourse_plan"])
    mutation["nodes"][1]["obligation_id"] = mutation["nodes"][0]["obligation_id"]
    _assert_code(
        s3.validate_discourse_plan(
            mutation,
            content_plan=artifacts["content_selection_plan"],
            obligation_ledger=artifacts["semantic_obligation_ledger"],
        ),
        "DISCOURSE_OBLIGATION_COVERAGE_MISMATCH",
    )

    mutation = deepcopy(artifacts["discourse_plan"])
    mutation["nodes"][0]["clause_role"] = "next_action"
    _assert_code(
        s3.validate_discourse_plan(
            mutation,
            content_plan=artifacts["content_selection_plan"],
            obligation_ledger=artifacts["semantic_obligation_ledger"],
        ),
        "CLAUSE_ROLE_MISMATCH",
    )

    budget_overflow = deepcopy(artifacts["discourse_plan"])
    budget_overflow["sentence_groups"].extend(
        [
            {
                "sentence_group_id": "sg_03",
                "section_role": "observation",
                "node_ids": [],
            },
            {
                "sentence_group_id": "sg_04",
                "section_role": "observation",
                "node_ids": [],
            },
        ]
    )
    _assert_code(
        s3.validate_discourse_plan(
            budget_overflow,
            content_plan=artifacts["content_selection_plan"],
            obligation_ledger=artifacts["semantic_obligation_ledger"],
        ),
        "CONTENT_BUDGET_MISMATCH",
    )

    missing_target_content = deepcopy(artifacts["content_selection_plan"])
    missing_target_content["decisions"][0]["status"] = "deferred_by_budget"
    _resign(missing_target_content, "content_plan_id", "nls3cp_")
    missing_target_discourse = deepcopy(artifacts["discourse_plan"])
    missing_target_discourse["nodes"] = [missing_target_discourse["nodes"][1]]
    missing_target_discourse["edges"] = []
    missing_target_discourse["sentence_groups"][0]["node_ids"] = []
    missing_target_discourse["source_content_plan_sha256"] = s3.artifact_sha256(
        missing_target_content
    )
    _assert_code(
        s3.validate_discourse_plan(
            missing_target_discourse,
            content_plan=missing_target_content,
            obligation_ledger=artifacts["semantic_obligation_ledger"],
        ),
        "BOUND_RECEPTION_TARGET_NODE_MISSING",
    )

    mutation = deepcopy(artifacts["discourse_plan"])
    mutation["edges"][0]["type"] = "contrasts_with"
    _assert_code(
        s3.validate_discourse_plan(
            mutation,
            content_plan=artifacts["content_selection_plan"],
            obligation_ledger=artifacts["semantic_obligation_ledger"],
        ),
        "BOUND_RECEPTION_EDGE_MISMATCH",
    )

    mutation = deepcopy(artifacts["surface_ast"])
    mutation["sections"][1]["sentences"][0]["clauses"][0][
        "discourse_node_id"
    ] = "dn_missing"
    _assert_code(
        s3.validate_surface_ast(
            mutation,
            discourse_plan=artifacts["discourse_plan"],
            obligation_ledger=artifacts["semantic_obligation_ledger"],
        ),
        "UNRESOLVED_DISCOURSE_NODE",
    )

    mutation = deepcopy(artifacts["surface_ast"])
    relation_nodes = mutation["sections"][0]["sentences"][0]["clauses"][0]["nodes"]
    mutation["sections"][0]["sentences"][0]["clauses"][0]["nodes"] = [
        node for node in relation_nodes if node["node_type"] != "grounded_relation"
    ]
    _assert_code(
        s3.validate_surface_ast(
            mutation,
            discourse_plan=artifacts["discourse_plan"],
            obligation_ledger=artifacts["semantic_obligation_ledger"],
        ),
        "SEMANTIC_NODE_TYPE_REQUIRED",
    )

    mutation = deepcopy(artifacts["surface_ast"])
    stance_nodes = mutation["sections"][1]["sentences"][0]["clauses"][0][
        "nodes"
    ]
    mutation["sections"][1]["sentences"][0]["clauses"][0]["nodes"] = [
        node for node in stance_nodes if node["node_type"] != "emlis_stance"
    ]
    _assert_code(
        s3.validate_surface_ast(
            mutation,
            discourse_plan=artifacts["discourse_plan"],
            obligation_ledger=artifacts["semantic_obligation_ledger"],
        ),
        "EMLIS_STANCE_NODE_REQUIRED",
    )

    mutation = deepcopy(artifacts["surface_ast"])
    observation_sentence = mutation["sections"][0]["sentences"][0]
    reception_sentence = mutation["sections"][1]["sentences"][0]
    observation_sentence["clauses"], reception_sentence["clauses"] = (
        reception_sentence["clauses"],
        observation_sentence["clauses"],
    )
    _assert_code(
        s3.validate_surface_ast(
            mutation,
            discourse_plan=artifacts["discourse_plan"],
            obligation_ledger=artifacts["semantic_obligation_ledger"],
        ),
        "DISCOURSE_SENTENCE_PARTITION_MISMATCH",
    )

    integrated_content = deepcopy(artifacts["content_selection_plan"])
    integrated_content["decisions"][0]["status"] = "integrated_into"
    integrated_content["decisions"][0]["integrated_into_obligation_id"] = (
        integrated_content["decisions"][1]["obligation_id"]
    )
    _resign(integrated_content, "content_plan_id", "nls3cp_")
    integrated_discourse = deepcopy(artifacts["discourse_plan"])
    integrated_discourse["sentence_groups"][0]["node_ids"] = ["dn_01", "dn_02"]
    integrated_discourse["sentence_groups"][1]["node_ids"] = []
    integrated_discourse["source_content_plan_sha256"] = s3.artifact_sha256(
        integrated_content
    )
    integrated_discourse["structural_signature"] = (
        "nls3sig_"
        + s3.artifact_sha256(
            {
                "nodes": integrated_discourse["nodes"],
                "edges": integrated_discourse["edges"],
                "sentence_groups": integrated_discourse["sentence_groups"],
            }
        )[:16]
    )
    _resign(integrated_discourse, "discourse_plan_id", "nls3dp_")
    _assert_code(
        s3.validate_discourse_plan(
            integrated_discourse,
            content_plan=integrated_content,
            obligation_ledger=artifacts["semantic_obligation_ledger"],
        ),
        "INTEGRATED_NODE_NOT_MERGE_ELIGIBLE",
    )


def test_s3_witness_has_no_internal_ids_and_spans_bind_actual_utf8_bytes() -> None:
    bundle = _bundle()
    witness = bundle["artifacts"]["parsed_surface_witness"]
    candidate = bundle["candidate_text"].encode("utf-8")

    mutation = deepcopy(witness)
    mutation["semantic_atoms"][0]["utf8_byte_end"] = 1
    _assert_code(
        s3.validate_parsed_surface_witness(
            mutation, candidate_text_bytes=candidate
        ),
        "SPAN_NOT_UTF8_SCALAR_BOUNDARY",
    )

    mutation = deepcopy(witness)
    mutation["semantic_atoms"][0]["span_sha256"] = "0" * 64
    _assert_code(
        s3.validate_parsed_surface_witness(
            mutation, candidate_text_bytes=candidate
        ),
        "SPAN_HASH_MISMATCH",
    )

    mutation = deepcopy(witness)
    mutation["semantic_atoms"][0]["evidence_ids"] = ["ev_thought_01"]
    _assert_code(
        s3.validate_parsed_surface_witness(
            mutation, candidate_text_bytes=candidate
        ),
        "UNKNOWN_FIELD",
    )


def test_s3_binding_contract_requires_unique_resolved_refs() -> None:
    bundle = _bundle()
    artifacts = bundle["artifacts"]
    binding = artifacts["verified_surface_binding"]

    mutation = deepcopy(binding)
    mutation["bindings"][0]["match_candidate_count"] = 2
    _assert_code(
        s3.validate_verified_surface_binding(
            mutation,
            parsed_surface_witness=artifacts["parsed_surface_witness"],
            obligation_ledger=artifacts["semantic_obligation_ledger"],
        ),
        "UNIQUE_MATCH_REQUIRED",
    )

    mutation = deepcopy(binding)
    mutation["bindings"][0]["match_basis"] = "UNIQUE_NUCLEUS_POLARITY_MATCH"
    _assert_code(
        s3.validate_verified_surface_binding(
            mutation,
            parsed_surface_witness=artifacts["parsed_surface_witness"],
            obligation_ledger=artifacts["semantic_obligation_ledger"],
        ),
        "MATCH_BASIS_MISMATCH",
    )

    mutation = deepcopy(binding)
    mutation["bindings"][0]["relation_id"] = None
    _assert_code(
        s3.validate_verified_surface_binding(
            mutation,
            parsed_surface_witness=artifacts["parsed_surface_witness"],
            obligation_ledger=artifacts["semantic_obligation_ledger"],
        ),
        "RELATION_BINDING_REQUIRED",
    )

    mutated_witness = deepcopy(artifacts["parsed_surface_witness"])
    mutated_witness["semantic_atoms"][0]["polarity"] = "positive"
    mutation = deepcopy(binding)
    mutation["parsed_surface_witness_sha256"] = s3.artifact_sha256(mutated_witness)
    _assert_code(
        s3.validate_verified_surface_binding(
            mutation,
            parsed_surface_witness=mutated_witness,
            obligation_ledger=artifacts["semantic_obligation_ledger"],
        ),
        "ATOM_OBLIGATION_FEATURE_MISMATCH",
    )

    mutation = deepcopy(binding)
    mutation["bindings"][0]["obligation_id"] = mutation["bindings"][1][
        "obligation_id"
    ]
    _assert_code(
        s3.validate_verified_surface_binding(
            mutation,
            parsed_surface_witness=artifacts["parsed_surface_witness"],
            obligation_ledger=artifacts["semantic_obligation_ledger"],
        ),
        "ATOM_OBLIGATION_KIND_MISMATCH",
    )

    mutation = deepcopy(binding)
    mutation["bindings"][0]["evidence_ids"] = ["other_case_evidence"]
    _assert_code(
        s3.validate_verified_surface_binding(
            mutation,
            parsed_surface_witness=artifacts["parsed_surface_witness"],
            obligation_ledger=artifacts["semantic_obligation_ledger"],
        ),
        "UNRESOLVED_EVIDENCE_REFERENCE",
    )

    mutation = deepcopy(binding)
    mutation["bindings"] = mutation["bindings"][:1]
    issues = s3.validate_verified_surface_binding(
        mutation,
        parsed_surface_witness=artifacts["parsed_surface_witness"],
        obligation_ledger=artifacts["semantic_obligation_ledger"],
    )
    _assert_code(issues, "WITNESS_BINDING_COVERAGE_MISMATCH")
    _assert_code(issues, "REQUIRED_BINDING_COVERAGE_MISSING")


def test_s3_generic_body_retained_metadata_attacks_fail_closed() -> None:
    bundle = _bundle()
    artifacts = bundle["artifacts"]
    generic = (
        "そのことを受け取っています。"
        "その点を受け止めています。"
        "今のことを心に留めています。"
    ).encode("utf-8")

    injected = deepcopy(artifacts["surface_ast"])
    injected["final_text"] = generic.decode("utf-8")
    injected["covered_obligation_ids"] = deepcopy(
        artifacts["semantic_obligation_ledger"]["required_obligation_ids"]
    )
    injected["realized_unit_ids"] = ["fake_unit_01"]
    _assert_code(
        s3.validate_surface_ast(
            injected,
            discourse_plan=artifacts["discourse_plan"],
            obligation_ledger=artifacts["semantic_obligation_ledger"],
        ),
        "UNKNOWN_FIELD",
    )

    stale_witness_issues = s3.validate_parsed_surface_witness(
        artifacts["parsed_surface_witness"], candidate_text_bytes=generic
    )
    _assert_code(stale_witness_issues, "PARENT_HASH_MISMATCH")
    _assert_code(stale_witness_issues, "SPAN_HASH_MISMATCH")

    rehashed_witness = deepcopy(artifacts["parsed_surface_witness"])
    rehashed_witness["candidate_text_sha256"] = hashlib.sha256(generic).hexdigest()
    rehashed_witness["semantic_atoms"][-1]["utf8_byte_end"] = len(generic)
    for atom in rehashed_witness["semantic_atoms"]:
        start = atom["utf8_byte_start"]
        end = atom["utf8_byte_end"]
        atom["span_sha256"] = hashlib.sha256(generic[start:end]).hexdigest()
    assert s3.validate_parsed_surface_witness(
        rehashed_witness, candidate_text_bytes=generic
    ) == ()
    _assert_code(
        s3.validate_verified_surface_binding(
            artifacts["verified_surface_binding"],
            parsed_surface_witness=rehashed_witness,
            obligation_ledger=artifacts["semantic_obligation_ledger"],
        ),
        "PARENT_HASH_MISMATCH",
    )
    rehashed_binding = deepcopy(artifacts["verified_surface_binding"])
    rehashed_binding["parsed_surface_witness_sha256"] = s3.artifact_sha256(
        rehashed_witness
    )
    assert s3.validate_verified_surface_binding(
        rehashed_binding,
        parsed_surface_witness=rehashed_witness,
        obligation_ledger=artifacts["semantic_obligation_ledger"],
    ) == ()

    catalog = _load(_ATTACK_CATALOG_PATH)
    generic_row = next(
        row
        for row in catalog["attacks"]
        if row["attack_id"] == "V3A-01_GENERIC_THREE_SENTENCES_RETAINED_METADATA"
    )
    assert generic_row["step3_state"] == (
        "contract_envelope_closed_semantic_red_frozen"
    )
    assert generic_row["earliest_semantic_closure_step"] == 8
    assert generic_row["release_blocking"] is True


def test_s3_receipt_is_strict_body_free_and_upstream_bound() -> None:
    bundle = _bundle()
    receipt = bundle["artifacts"]["case_evidence_receipt"]
    authority = _receipt_authority(bundle)

    for key in (
        "raw_input",
        "comment_text",
        "candidate_text",
        "question_answer",
        "local_review_note",
    ):
        mutation = deepcopy(receipt)
        mutation[key] = "forbidden"
        issues = s3.validate_case_evidence_receipt(mutation, authority=authority)
        _assert_code(issues, "BODY_CONTENT_FORBIDDEN")
        _assert_code(issues, "UNKNOWN_FIELD")

    mutation = deepcopy(receipt)
    mutation["commitment_policy"]["key_or_nonce_stored_in_receipt"] = True
    _assert_code(
        s3.validate_case_evidence_receipt(mutation, authority=authority),
        "COMMITMENT_SECRET_FORBIDDEN",
    )

    mutation = deepcopy(receipt)
    mutation["source_dependency_closure_sha256"] = "f" * 64
    _assert_code(
        s3.validate_case_evidence_receipt(mutation, authority=authority),
        "PARENT_HASH_MISMATCH",
    )

    mutation = deepcopy(receipt)
    mutation["selector_decision"]["status"] = "no_valid_candidate"
    mutation["selector_decision"]["selected_candidate_id"] = None
    _assert_code(
        s3.validate_case_evidence_receipt(mutation, authority=authority),
        "RECEIPT_GATE_SELECTOR_MISMATCH",
    )

    mutation = deepcopy(receipt)
    mutation["selector_decision"]["selected_candidate_id"] = "free text"
    _assert_code(
        s3.validate_case_evidence_receipt(mutation, authority=authority),
        "PATTERN_MISMATCH",
    )

    mutation = deepcopy(receipt)
    mutation["previous_output"] = {
        "commitment": "a" * 64,
        "changed": True,
    }
    _assert_code(
        s3.validate_case_evidence_receipt(mutation, authority=authority),
        "PREVIOUS_OUTPUT_AUTHORITY_MISMATCH",
    )

    mutation = deepcopy(receipt)
    mutation["sample_source"] = "real_user_current_valid"
    mutation["commitment_policy"]["scheme"] = "salted_sha256_v1"
    assert s3.validate_case_evidence_receipt(
        mutation, authority=authority
    ) == ()

    for review_status in ("passed", "failed"):
        mutation = deepcopy(receipt)
        mutation["local_product_review"] = {
            "status": review_status,
            "reason_codes": [],
        }
        _assert_code(
            s3.validate_case_evidence_receipt(mutation, authority=authority),
            "ARRAY_TOO_SHORT",
        )

    mutation = deepcopy(receipt)
    mutation["hard_gate"] = {
        "status": "failed",
        "failed_codes": ["SEMANTIC_FAILURE"],
    }
    mutation["selector_decision"]["status"] = "no_valid_candidate"
    mutation["selector_decision"]["selected_candidate_id"] = None
    _assert_code(
        s3.validate_case_evidence_receipt(mutation, authority=authority),
        "RECEIPT_REVIEW_GATE_MISMATCH",
    )

    schema = _load(_RECEIPT_SCHEMA_PATH)
    assert schema["$id"] == s3.RECEIPT_SCHEMA
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == set(receipt)
    assert set(schema["properties"]) == set(receipt)
    for key in (
        "app_reachable_validation",
        "commitment_policy",
        "hard_gate",
        "selector_decision",
        "local_product_review",
        "previous_output",
    ):
        assert schema["properties"][key]["additionalProperties"] is False
    assert len(schema["allOf"]) == 3
    assert any(
        condition.get("if", {}).get("properties", {}).get(
            "local_product_review", {}
        ).get("properties", {}).get("status", {}).get("const")
        == "passed"
        and condition.get("then", {}).get("properties", {}).get(
            "hard_gate", {}
        ).get("properties", {}).get("status", {}).get("const")
        == "passed"
        for condition in schema["allOf"]
    )
    assert len(schema["properties"]["local_product_review"]["allOf"]) == 3
    assert len(schema["properties"]["selector_decision"]["allOf"]) == 2
    assert len(schema["properties"]["previous_output"]["oneOf"]) == 2
    assert set(
        schema["properties"]["commitment_policy"]["properties"]["scheme"][
            "enum"
        ]
    ) == {"hmac_sha256_v1", "salted_sha256_v1"}
    selected_candidate_schema = schema["properties"]["selector_decision"][
        "properties"
    ]["selected_candidate_id"]
    assert selected_candidate_schema["anyOf"][0]["pattern"] == (
        "^nls3cand_[0-9a-f]{16,64}$"
    )


def test_s3_v2_import_guard_detects_static_and_dynamic_probes() -> None:
    probes = {
        "import emlis_ai_grounded_human_reception_v2": (
            "emlis_ai_grounded_human_reception_v2",
        ),
        "from emlis_ai_grounded_reception_content_plan_v2 import build": (
            "emlis_ai_grounded_reception_content_plan_v2",
        ),
        "from ai.services.ai_inference import emlis_ai_grounded_human_reception_v2": (
            "emlis_ai_grounded_human_reception_v2",
        ),
        "import importlib\nimportlib.import_module('emlis_ai_grounded_reception_candidate_plan_v2')": (
            "emlis_ai_grounded_reception_candidate_plan_v2",
        ),
        "__import__('emlis_ai_grounded_reception_candidate_selector_v2')": (
            "emlis_ai_grounded_reception_candidate_selector_v2",
        ),
        "import emlis_ai_grounded_human_reception_v2.submodule": (
            "emlis_ai_grounded_human_reception_v2",
        ),
        "from emlis_ai_grounded_reception_content_plan_v2.submodule import x": (
            "emlis_ai_grounded_reception_content_plan_v2",
        ),
        "import importlib\nimportlib.import_module('emlis_ai_grounded_reception_candidate_plan_v2.submodule')": (
            "emlis_ai_grounded_reception_candidate_plan_v2",
        ),
        "from emlis_ai_reply_service import render_emlis_ai_reply": (
            "emlis_ai_reply_service",
        ),
    }
    for source, expected in probes.items():
        assert s3.forbidden_imports_in_source(source) == expected
    assert s3.forbidden_imports_in_source(
        "RECEIPT_SCHEMA = 'cocolon.emlis.nls_v3.case_evidence_receipt.v2'"
    ) == ()

    active_modules = sorted(_INFERENCE_ROOT.glob("emlis_ai_nls_v3*.py"))
    assert [path.name for path in active_modules] == [
        "emlis_ai_nls_v3_artifact_contract.py"
    ]
    assert s3.forbidden_imports_in_module_tree(active_modules) == ()

    reply_tree = ast.parse(
        (_INFERENCE_ROOT / "emlis_ai_reply_service.py").read_text(encoding="utf-8")
    )
    reply_imports = {
        alias.name
        for node in ast.walk(reply_tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module
        for node in ast.walk(reply_tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert not any(target.startswith("emlis_ai_nls_v3") for target in reply_imports)


def test_s3_active_canonical_serializer_is_single_and_deterministic() -> None:
    active_modules = sorted(_INFERENCE_ROOT.glob("emlis_ai_nls_v3*.py"))
    serializer_defs: list[tuple[str, str]] = []
    dumps_owners: list[tuple[str, str]] = []
    for path in active_modules:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        parents: dict[ast.AST, ast.AST] = {}
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                parents[child] = parent
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in {
                "canonical_json_bytes",
                "canonical_json_text",
                "canonical_serialize",
            }:
                serializer_defs.append((path.name, node.name))
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "dumps"
            ):
                owner = node
                while owner in parents and not isinstance(
                    owner, (ast.FunctionDef, ast.AsyncFunctionDef)
                ):
                    owner = parents[owner]
                dumps_owners.append((path.name, getattr(owner, "name", "<module>")))
    assert serializer_defs == [
        ("emlis_ai_nls_v3_artifact_contract.py", "canonical_json_bytes")
    ]
    assert dumps_owners == [
        ("emlis_ai_nls_v3_artifact_contract.py", "canonical_json_bytes")
    ]

    composed = "é"
    decomposed = unicodedata.normalize("NFD", composed)
    left = {"z": "line1\r\nline2", "a": decomposed, "array": [True, 1, None]}
    right = {"array": [True, 1, None], "a": composed, "z": "line1\nline2"}
    assert s3.canonical_json_bytes(left) == s3.canonical_json_bytes(right)
    assert s3.artifact_sha256(left) == s3.artifact_sha256(right)

    representative = {"a": [True, 1, None, "日本語"], "z": {"k": "v"}}
    assert s3.canonical_json_bytes(representative) == s01.canonical_json_bytes(
        representative
    )
    assert s3.canonical_json_bytes(representative) == s2.canonical_json_bytes(
        representative
    )


def test_s3_canonical_codec_rejects_ambiguous_or_non_json_input() -> None:
    _assert_value_error(lambda: s3.canonical_json_bytes(1.0), "NON_JSON_TYPE")
    _assert_value_error(lambda: s3.canonical_json_bytes(float("nan")), "NON_JSON_TYPE")
    _assert_value_error(lambda: s3.canonical_json_bytes({"x": "\ud800"}), "NON_UTF8_SCALAR")
    _assert_value_error(
        lambda: s3.canonical_json_bytes({"é": 1, unicodedata.normalize("NFD", "é"): 2}),
        "NORMALIZED_KEY_COLLISION",
    )
    _assert_value_error(
        lambda: s3.load_canonical_json_bytes(b'{"a":1,"a":2}\n'),
        "CANONICAL_DUPLICATE_KEY",
    )
    _assert_value_error(
        lambda: s3.load_canonical_json_bytes(b"\xef\xbb\xbf{}\n"),
        "CANONICAL_BOM_FORBIDDEN",
    )
    _assert_value_error(
        lambda: s3.load_canonical_json_bytes(b"{}\r\n"),
        "CANONICAL_CR_FORBIDDEN",
    )
    _assert_value_error(
        lambda: s3.load_canonical_json_bytes(b"{}"),
        "CANONICAL_FINAL_LF_REQUIRED",
    )
    _assert_value_error(
        lambda: s3.load_canonical_json_bytes(b'{"z":1,"a":2}\n'),
        "CANONICAL_BYTES_MISMATCH",
    )


def test_s3_validator_remains_independent_from_future_builders() -> None:
    source_path = _INFERENCE_ROOT / "emlis_ai_nls_v3_artifact_contract.py"
    tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
    function_names = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert not any(name.startswith(("build_", "render_", "parse_", "select_")) for name in function_names)
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert not any(target.startswith("helpers") for target in imports)
    assert "emlis_ai_reply_service" not in imports
    assert not imports & s3.STOPPED_V2_MODULES


def test_s3_red_attack_catalog_is_complete_body_free_and_step_scoped() -> None:
    catalog = _load(_ATTACK_CATALOG_PATH)
    assert catalog["schema_version"] == (
        "cocolon.emlis.nls_v3.step3_red_attack_catalog.v1"
    )
    assert catalog["body_free"] is True
    assert catalog["design_sha256"] == (
        "6aa3fb799919ac30b0eb84571ac4009d62a2bd799c84322272a59bba533f13bc"
    )
    assert catalog["parent_batch001_manifest_sha256"] == _FROZEN_HASHES[
        "batch001"
    ][1]
    rows = catalog["attacks"]
    assert len(rows) == 14
    assert len({row["attack_id"] for row in rows}) == 14
    assert all(row["release_blocking"] is True for row in rows)
    assert next(row for row in rows if row["attack_id"].startswith("V3A-11"))[
        "step3_state"
    ] == "closed"
    assert next(row for row in rows if row["attack_id"].startswith("V3A-12"))[
        "step3_state"
    ] == "closed"
    assert any(row["earliest_semantic_closure_step"] == 8 for row in rows)
    assert {row["attack_id"] for row in rows} == {
        "V3A-01_GENERIC_THREE_SENTENCES_RETAINED_METADATA",
        "V3A-02_ORIGINAL_BODY_OTHER_OBLIGATION_METADATA",
        "V3A-03_ORIGINAL_BODY_OTHER_CASE_EVIDENCE",
        "V3A-04_CLAUSE_DELETION_STALE_SPAN_MAP",
        "V3A-05_AST_CHANGED_BODY_UNCHANGED",
        "V3A-06_AST_AND_BODY_CHANGED_TO_OTHER_MEANING",
        "V3A-07_CANDIDATE_PERMUTATION",
        "V3A-08_SAME_BODY_REUSED_MULTIPLE_INPUTS",
        "V3A-09_ANCHOR_ONLY_GENERIC_PREDICATE",
        "V3A-10_EMLIS_TOKEN_ONLY_RECEPTION",
        "V3A-11_FAKE_COVERED_OBLIGATION_IDS",
        "V3A-12_BODY_MIXED_INTO_RECEIPT",
        "V3A-13_BATCH_FAMILY_CASE_ID_GENERATION_CUE",
        "V3A-14_PAST_FAILURE_TRIGGER_BRANCH",
    }
    expected_row_keys = {
        "attack_id",
        "earliest_semantic_closure_step",
        "release_blocking",
        "step3_contract_closure_codes",
        "step3_state",
    }
    assert all(set(row) == expected_row_keys for row in rows)
    closure_codes = {
        code for row in rows for code in row["step3_contract_closure_codes"]
    }
    contract_tree = ast.parse(
        (_INFERENCE_ROOT / "emlis_ai_nls_v3_artifact_contract.py").read_text(
            encoding="utf-8"
        )
    )
    test_tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    contract_literals = {
        node.value
        for node in ast.walk(contract_tree)
        if isinstance(node, ast.Constant) and type(node.value) is str
    }
    test_literals = {
        node.value
        for node in ast.walk(test_tree)
        if isinstance(node, ast.Constant) and type(node.value) is str
    }
    assert closure_codes <= contract_literals
    assert closure_codes <= test_literals
    forbidden_keys = {
        "raw_input",
        "thought_text",
        "action_text",
        "candidate_text",
        "final_text",
        "comment_text",
    }
    assert not forbidden_keys & set().union(*(set(row) for row in rows))


def test_s3_step0_step2_and_batch001_remain_byte_frozen() -> None:
    for name, (path, expected) in _FROZEN_HASHES.items():
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual == expected, (name, path, expected, actual)
    manifest = _load(_FROZEN_HASHES["batch001"][0])
    assert manifest["case_count"] == 100
    assert manifest["frozen"] is True
    assert manifest["next_authority"] == "step3_only"


def test_s3_completion_receipt_binds_implementation_and_next_authority() -> None:
    receipt = _load(_STEP3_RECEIPT_PATH)
    assert s3.load_canonical_json_bytes(_STEP3_RECEIPT_PATH.read_bytes()) == receipt
    assert set(receipt) == {
        "schema_version",
        "completed_at_jst",
        "design_sha256",
        "parent_artifacts",
        "implementation_files",
        "artifact_owners",
        "canonical_serializer",
        "negative_suite",
        "import_boundary",
        "runtime_boundary",
        "completion_condition",
        "next_step_authority",
        "valid_for_runtime_switch",
        "body_free",
    }
    assert receipt["schema_version"] == (
        "cocolon.emlis.nls_v3.step3_contract_receipt.v1"
    )
    assert receipt["design_sha256"] == (
        "6aa3fb799919ac30b0eb84571ac4009d62a2bd799c84322272a59bba533f13bc"
    )
    assert receipt["parent_artifacts"]["batch001_manifest_sha256"] == (
        _FROZEN_HASHES["batch001"][1]
    )
    assert len(receipt["artifact_owners"]) == 8
    assert all(row["strict_validator"] is True for row in receipt["artifact_owners"])
    assert receipt["canonical_serializer"] == {
        "active_owner_ref": "ai/services/ai_inference/emlis_ai_nls_v3_artifact_contract.py",
        "function": "canonical_json_bytes",
        "active_serializer_implementation_count": 1,
        "historical_frozen_serializers_unchanged": True,
    }
    test_tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    actual_test_count = sum(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_s3_")
        for node in ast.walk(test_tree)
    )
    assert receipt["negative_suite"]["direct_test_function_count"] == (
        actual_test_count
    )
    assert receipt["negative_suite"]["owner_count"] == 8
    assert receipt["negative_suite"][
        "top_level_required_field_mutation_count"
    ] == sum(len(value) for value in _bundle()["artifacts"].values())
    assert receipt["negative_suite"][
        "nested_required_field_mutation_count"
    ] == sum(
        1
        for value in _bundle()["artifacts"].values()
        for path in _dict_field_paths(value)
        if len(path) > 1
    )
    assert receipt["negative_suite"]["red_attack_count"] == 14
    assert receipt["negative_suite"]["generic_attack_contract_envelope_closed"] is True
    assert receipt["negative_suite"]["generic_attack_semantic_closure_owner_step"] == 8
    assert set(receipt["negative_suite"]["deferred_step8_semantic_red_ids"]) == {
        "BODY_ONLY_TOPIC_FINGERPRINT_AUTHORITY",
        "BODY_ONLY_REFERENT_FINGERPRINT_AUTHORITY",
        "INDEPENDENT_MATCH_CANDIDATE_COUNT",
    }
    assert receipt["import_boundary"]["stopped_v2_import_count"] == 0
    assert receipt["runtime_boundary"]["reply_service_imports_v3"] is False
    assert receipt["runtime_boundary"]["runtime_connected"] is False
    assert receipt["completion_condition"] == {
        "all_step3_tests_passed": True,
        "artifact_chain_validator": "validate_artifact_chain",
        "formal_acceptance_requires_full_chain": True,
        "previous_step_regression_passed": True,
    }
    assert receipt["next_step_authority"] == "step4_only"
    assert receipt["valid_for_runtime_switch"] is False
    assert receipt["body_free"] is True
    assert {row["ref"] for row in receipt["implementation_files"]} == {
        "ai/docs/Cocolon_EmlisAI_NLSv3_Step3_Result_20260715.md",
        "ai/services/ai_inference/emlis_ai_nls_v3_artifact_contract.py",
        "ai/tests/fixtures/emlis_nls_v3/contract/step3_valid_artifacts_v1.json",
        "ai/tests/fixtures/emlis_nls_v3_s3_red_attack_catalog_20260715.json",
        "ai/tests/schemas/emlis_nls_v3_case_evidence_receipt_v2.schema.json",
        "ai/tests/test_emlis_nls_v3_s0_s1.py",
        "ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py",
    }
    for row in receipt["implementation_files"]:
        path = _REPO_ROOT / row["ref"]
        assert path.is_file(), path
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"]
