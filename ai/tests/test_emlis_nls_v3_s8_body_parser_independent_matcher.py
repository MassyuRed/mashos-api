# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step 8 body-only parser and independent matcher acceptance tests."""

import ast as python_ast
from collections import Counter
from copy import deepcopy
import hashlib
import inspect
import json
from pathlib import Path
import re
import unicodedata

import emlis_ai_body_semantic_atom_parser_v3 as parser_module
import emlis_ai_canonical_renderer_v3 as renderer_module
import emlis_ai_independent_semantic_matcher_v3 as matcher_module
import emlis_ai_nls_v3_artifact_contract as v1_contract
import emlis_ai_surface_grammar_catalog_v3 as step7_catalog_module
import emlis_ai_surface_grammar_catalog_v3_step8 as step8_catalog_module
from emlis_ai_body_semantic_atom_parser_v3 import (
    BodySemanticAtomParseError,
    parse_body_semantic_atoms,
)
from emlis_ai_canonical_renderer_v3 import (
    open_request_lexical_authority,
    render_canonical_surface,
)
from emlis_ai_content_selection_v3 import build_content_selection_plan
from emlis_ai_discourse_graph_planner_v3 import build_discourse_graph_plans
from emlis_ai_evidence_ledger_service import (
    build_evidence_ledger,
    build_evidence_span_resolver,
)
from emlis_ai_grounded_observation_plan import build_grounded_observation_plan
from emlis_ai_independent_semantic_matcher_v3 import (
    IndependentMatchSourceAuthority,
    IndependentSemanticMatchError,
    match_parsed_surface_witness,
    open_independent_match_source_authority,
)
from emlis_ai_nls_v3_artifact_contract import (
    TrustedFutureStageAuthority,
    artifact_sha256,
)
from emlis_ai_observation_stage_context_v3 import (
    build_observation_stage_context,
)
from emlis_ai_semantic_obligation_inventory_v3 import (
    SemanticObligationInventoryError,
    build_grounded_source_snapshot,
    build_semantic_obligation_inventory,
)
from emlis_ai_step8_artifact_contract_v3 import (
    BINDING_V2_SCHEMA,
    WITNESS_V2_SCHEMA,
    validate_parsed_surface_witness_v2,
    validate_verified_surface_binding_v2,
)
from emlis_ai_surface_grammar_catalog_v3 import SURFACE_GRAMMAR_CATALOG
from emlis_ai_typed_surface_ast_v3 import build_typed_surface_ast


_AI_ROOT = Path(__file__).resolve().parents[1]
_INFERENCE_ROOT = _AI_ROOT / "services" / "ai_inference"
_BATCH_PATH = (
    _AI_ROOT
    / "tests"
    / "fixtures"
    / "emlis_nls_v3"
    / "generated"
    / "batch_001.jsonl"
)
_ANCHOR_RE = re.compile(r"「([^」]+)」に表れた")


def _samples() -> tuple[dict[str, object], ...]:
    return tuple(
        json.loads(line)
        for line in _BATCH_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )


def _sample(case_id: str) -> dict[str, object]:
    return next(row for row in _samples() if row["case_id"] == case_id)


def _normal_parents(current_input: dict[str, object]):
    spans = build_evidence_ledger(current_input)
    resolver = build_evidence_span_resolver(
        spans, current_input=current_input
    )
    grounded = build_grounded_observation_plan(
        current_input, evidence_spans=spans
    )
    stage = build_observation_stage_context(
        stage="normal_observation",
        original_input_bundle=current_input,
    )
    snapshot = build_grounded_source_snapshot(
        grounded,
        resolver,
        observation_stage_context=stage,
        original_input_bundle=current_input,
    )
    inventory = build_semantic_obligation_inventory(snapshot)
    content = build_content_selection_plan(inventory)
    plans = build_discourse_graph_plans(inventory, content)
    lexical_authority = open_request_lexical_authority(
        inventory,
        grounded_plan=grounded,
        resolver=resolver,
        observation_stage_context=stage,
        original_input_bundle=current_input,
    )
    match_authority = open_independent_match_source_authority(
        inventory,
        grounded_plan=grounded,
        resolver=resolver,
        observation_stage_context=stage,
        original_input_bundle=current_input,
    )
    return (
        grounded,
        resolver,
        stage,
        inventory,
        content,
        plans,
        lexical_authority,
        match_authority,
    )


def _render(
    discourse: dict[str, object],
    *,
    inventory,
    content: dict[str, object],
    lexical_authority,
):
    surface_ast = build_typed_surface_ast(
        discourse,
        inventory_result=inventory,
        content_plan=content,
    )
    return render_canonical_surface(
        surface_ast,
        discourse_plan=discourse,
        content_plan=content,
        inventory_result=inventory,
        lexical_authority=lexical_authority,
    )


def _first_context(case_id: str) -> dict[str, object]:
    sample = _sample(case_id)
    parents = _normal_parents(sample["input"])
    (
        grounded,
        resolver,
        stage,
        inventory,
        content,
        plans,
        lexical_authority,
        match_authority,
    ) = parents
    rendered = _render(
        plans.plans[0],
        inventory=inventory,
        content=content,
        lexical_authority=lexical_authority,
    )
    witness = parse_body_semantic_atoms(rendered.utf8_bytes)
    binding = match_parsed_surface_witness(
        witness,
        candidate_text_bytes=rendered.utf8_bytes,
        inventory_result=inventory,
        match_authority=match_authority,
    )
    return {
        "sample": sample,
        "grounded": grounded,
        "resolver": resolver,
        "stage": stage,
        "inventory": inventory,
        "content": content,
        "plans": plans,
        "lexical_authority": lexical_authority,
        "match_authority": match_authority,
        "rendered": rendered,
        "witness": witness,
        "binding": binding,
    }


def _codes(issues) -> set[str]:
    return {issue.code for issue in issues}


def _raises_parse_code(call, expected: str) -> None:
    try:
        call()
    except BodySemanticAtomParseError as exc:
        assert exc.code == expected, (expected, exc.code)
    else:
        raise AssertionError(f"expected parser failure {expected}")


def _raises_match_code(call, expected: str) -> None:
    try:
        call()
    except IndependentSemanticMatchError as exc:
        assert exc.code == expected, (expected, exc.code)
    else:
        raise AssertionError(f"expected matcher failure {expected}")


def _match_mutated(context: dict[str, object], candidate: bytes):
    witness = parse_body_semantic_atoms(candidate)
    binding = match_parsed_surface_witness(
        witness,
        candidate_text_bytes=candidate,
        inventory_result=context["inventory"],
        match_authority=context["match_authority"],
    )
    return witness, binding


def _all_strings(value):
    if type(value) is str:
        yield value
    elif type(value) is dict:
        for child in value.values():
            yield from _all_strings(child)
    elif type(value) is list:
        for child in value:
            yield from _all_strings(child)


def test_s8_v1_release_bytes_remain_frozen_with_v2_side_by_side() -> None:
    expected_file_hashes = {
        "emlis_ai_grounded_observation_plan.py": (
            "b422093f907f3a825ec30f687f2f8b1d2688bf89950d9bc7436bfe0b5a67d177"
        ),
        "emlis_ai_nls_v3_artifact_contract.py": (
            "c20b262495276c9b549b257380e1a7c28069c316a7aca4b6e00a49de03d1512b"
        ),
        "emlis_ai_surface_grammar_catalog_v3.py": (
            "954a2dec34443d664ff3a58c0abe4336c113c11f5be72eade41f24685d8dbc3c"
        ),
        "emlis_ai_canonical_renderer_v3.py": (
            "7f85e7dc8c5e2009409adf5a6700cfc12a4c1e7b2ffa522c96f7319fcbfa5507"
        ),
    }
    for name, expected in expected_file_hashes.items():
        assert hashlib.sha256((_INFERENCE_ROOT / name).read_bytes()).hexdigest() == expected

    active_v1_namespace = sorted(
        path.name for path in _INFERENCE_ROOT.glob("emlis_ai_nls_v3*.py")
    )
    assert active_v1_namespace == ["emlis_ai_nls_v3_artifact_contract.py"]
    assert v1_contract.WITNESS_SCHEMA.endswith("parsed_surface_witness.v1")
    assert v1_contract.BINDING_SCHEMA.endswith("verified_surface_binding.v1")
    assert WITNESS_V2_SCHEMA.endswith("parsed_surface_witness.v2")
    assert BINDING_V2_SCHEMA.endswith("verified_surface_binding.v2")
    assert not step7_catalog_module.validate_surface_grammar_catalog()
    assert not step8_catalog_module.validate_step8_surface_grammar_catalog()
    assert step7_catalog_module.FROZEN_SURFACE_GRAMMAR_CATALOG_SHA256 == (
        "af4a49bc08437cbd6ab968d52acf45971eb8a51f1468c87328717398e7f067e4"
    )
    assert step8_catalog_module.FROZEN_STEP8_SURFACE_GRAMMAR_CATALOG_SHA256 == (
        "482a45a3f4962af996aed70dc407cab05e03013a4612e1f13c853151f8d68148"
    )


def test_s8_all_100_inputs_and_596_candidates_parse_and_bind() -> None:
    samples = _samples()
    assert len(samples) == 100
    candidate_count = 0
    first_candidate_count = 0
    unknown_mapping: Counter[tuple[tuple[str, ...], tuple[str, ...]]] = Counter()
    relation_types: set[str] = set()
    relation_directions: set[str] = set()
    graph_roles: set[str] = set()

    for sample in samples:
        current_input = sample["input"]
        (
            grounded,
            resolver,
            stage,
            inventory,
            content,
            plans,
            lexical_authority,
            match_authority,
        ) = _normal_parents(current_input)
        unknown_by_id = {
            row.source_id: row.source_dimension
            for row in inventory.source_snapshot.unknowns
        }
        source_ids = {
            value
            for obligation in inventory.ledger["obligations"]
            for key, values in obligation.items()
            if key.endswith("_ids") and type(values) is list
            for value in values
            if type(value) is str
        }

        for plan_index, discourse in enumerate(plans.plans):
            rendered = _render(
                discourse,
                inventory=inventory,
                content=content,
                lexical_authority=lexical_authority,
            )
            witness = parse_body_semantic_atoms(rendered.utf8_bytes)
            if plan_index == 0:
                assert witness == parse_body_semantic_atoms(
                    rendered.utf8_bytes
                )
            assert witness["parse_status"] == "parsed", sample["case_id"]
            assert not validate_parsed_surface_witness_v2(
                witness, candidate_text_bytes=rendered.utf8_bytes
            ), sample["case_id"]
            assert not (set(_all_strings(witness)) & source_ids)
            binding = match_parsed_surface_witness(
                witness,
                candidate_text_bytes=rendered.utf8_bytes,
                inventory_result=inventory,
                match_authority=match_authority,
            )
            assert binding["binding_status"] == "matched", (
                sample["case_id"],
                binding,
            )
            assert not validate_verified_surface_binding_v2(
                binding,
                parsed_surface_witness=witness,
                candidate_text_bytes=rendered.utf8_bytes,
                obligation_ledger=inventory.ledger,
                ledger_authority=inventory.source_snapshot.ledger_source_authority,
                source_snapshot_sha256=match_authority.source_snapshot_sha256,
                observation_stage=match_authority.observation_stage,
            ), sample["case_id"]
            assert len(binding["bindings"]) == len(witness["semantic_atoms"])
            bound_ids = {row["obligation_id"] for row in binding["bindings"]}
            assert set(inventory.ledger["required_obligation_ids"]) <= bound_ids

            atom_by_id = {
                row["atom_id"]: row for row in witness["semantic_atoms"]
            }
            graph_roles.update(
                row["graph_role"]
                for row in witness["semantic_atoms"]
                if row["kind"] != "bound_emlis_reception"
            )
            for row in binding["bindings"]:
                atom = atom_by_id[row["atom_id"]]
                if atom["kind"] == "grounded_relation":
                    relation_types.add(atom["relation_type"])
                    relation_directions.add(row["relation_direction"])
                if plan_index == 0 and atom["kind"] == "unknown_boundary":
                    source_dimensions = tuple(
                        sorted(
                            unknown_by_id[item]
                            for item in row["unknown_boundary_ids"]
                        )
                    )
                    unknown_mapping[
                        (source_dimensions, tuple(atom["unknown_dimension_codes"]))
                    ] += 1
            if plan_index == 0:
                first_candidate_count += 1
            candidate_count += 1

    assert first_candidate_count == 100
    assert candidate_count == 596
    assert unknown_mapping == Counter(
        {
            (("explicit_cause_unknown",), ("cause",)): 5,
            (("explicit_choice_decision_unknown",), ("choice",)): 11,
            (("explicit_temporal_referent_unknown",), ("referent",)): 3,
            (("explicit_unverbalized_unknown",), ("other",)): 8,
        }
    )
    assert relation_types == {
        "precedes",
        "contrasts_with",
        "coexists_with",
        "supports_without_guarantee",
    }
    assert relation_directions == {"source_to_target", "bidirectional"}
    assert "unknown_related" in graph_roles


def test_s8_contracts_are_closed_hash_bound_and_semantically_signed() -> None:
    context = _first_context("nls3s_b001_0001")
    witness = context["witness"]
    binding = context["binding"]
    candidate = context["rendered"].utf8_bytes
    inventory = context["inventory"]
    authority = context["match_authority"]
    assert not validate_parsed_surface_witness_v2(
        witness, candidate_text_bytes=candidate
    )
    assert not validate_verified_surface_binding_v2(
        binding,
        parsed_surface_witness=witness,
        candidate_text_bytes=candidate,
        obligation_ledger=inventory.ledger,
        ledger_authority=inventory.source_snapshot.ledger_source_authority,
        source_snapshot_sha256=authority.source_snapshot_sha256,
        observation_stage=authority.observation_stage,
    )

    mutation = deepcopy(witness)
    mutation["covered_obligation_ids"] = []
    assert "UNKNOWN_FIELD" in _codes(
        validate_parsed_surface_witness_v2(
            mutation, candidate_text_bytes=candidate
        )
    )
    mutation = deepcopy(witness)
    mutation["body_free_export_allowed"] = True
    assert "PRIVATE_ARTIFACT_EXPORT_FORBIDDEN" in _codes(
        validate_parsed_surface_witness_v2(
            mutation, candidate_text_bytes=candidate
        )
    )
    mutation = deepcopy(witness)
    mutation["grammar_catalog_sha256"] = "0" * 64
    assert "GRAMMAR_CATALOG_HASH_MISMATCH" in _codes(
        validate_parsed_surface_witness_v2(
            mutation, candidate_text_bytes=candidate
        )
    )
    mutation = deepcopy(witness)
    mutation["semantic_atoms"][0]["semantic_signature_sha256"] = "0" * 64
    assert "SEMANTIC_SIGNATURE_MISMATCH" in _codes(
        validate_parsed_surface_witness_v2(
            mutation, candidate_text_bytes=candidate
        )
    )
    mutation = deepcopy(witness)
    unknown = next(
        row
        for row in mutation["semantic_atoms"]
        if row["kind"] == "unknown_boundary"
    )
    unknown["unknown_dimension_codes"] = ["invented"]
    assert "ENUM_VALUE_INVALID" in _codes(
        validate_parsed_surface_witness_v2(
            mutation, candidate_text_bytes=candidate
        )
    )
    mutation = deepcopy(witness)
    predicate = next(
        row
        for row in mutation["semantic_atoms"]
        if "predicate_code" in row
    )
    predicate["predicate_code"] = "FORGED_PREDICATE"
    predicate["semantic_signature_sha256"] = artifact_sha256(
        {
            key: value
            for key, value in predicate.items()
            if key
            not in {
                "atom_id",
                "semantic_signature_sha256",
                "utf8_byte_start",
                "utf8_byte_end",
                "span_sha256",
            }
        }
    )
    assert "PREDICATE_CODE_MISMATCH" in _codes(
        validate_parsed_surface_witness_v2(
            mutation, candidate_text_bytes=candidate
        )
    )
    mutation = deepcopy(witness)
    mutation["semantic_atoms"][0]["atom_id"] = "atom_forged"
    assert "ATOM_ID_DERIVATION_MISMATCH" in _codes(
        validate_parsed_surface_witness_v2(
            mutation, candidate_text_bytes=candidate
        )
    )
    mutation = deepcopy(witness)
    unknown = next(
        row
        for row in mutation["semantic_atoms"]
        if row["kind"] == "unknown_boundary"
    )
    unknown["unknown_dimension_codes"] = ["intention"]
    assert "ENUM_VALUE_INVALID" in _codes(
        validate_parsed_surface_witness_v2(
            mutation, candidate_text_bytes=candidate
        )
    )

    mutation = deepcopy(binding)
    mutation["covered_obligation_ids"] = []
    assert "UNKNOWN_FIELD" in _codes(
        validate_verified_surface_binding_v2(
            mutation,
            parsed_surface_witness=witness,
            candidate_text_bytes=candidate,
            obligation_ledger=inventory.ledger,
            ledger_authority=inventory.source_snapshot.ledger_source_authority,
            source_snapshot_sha256=authority.source_snapshot_sha256,
            observation_stage=authority.observation_stage,
        )
    )
    mutation = deepcopy(binding)
    mutation["bindings"][0]["match_candidate_count"] = 2
    assert "UNIQUE_MATCH_REQUIRED" in _codes(
        validate_verified_surface_binding_v2(
            mutation,
            parsed_surface_witness=witness,
            candidate_text_bytes=candidate,
            obligation_ledger=inventory.ledger,
            ledger_authority=inventory.source_snapshot.ledger_source_authority,
            source_snapshot_sha256=authority.source_snapshot_sha256,
            observation_stage=authority.observation_stage,
        )
    )
    mutation = deepcopy(binding)
    mutation["bindings"] = []
    mutation["binding_status"] = "unparseable_surface"
    mutation["failure_codes"] = ["UNPARSABLE_CONTROLLED_SURFACE"]
    assert "BINDING_WITNESS_STATUS_MISMATCH" in _codes(
        validate_verified_surface_binding_v2(
            mutation,
            parsed_surface_witness=witness,
            candidate_text_bytes=candidate,
            obligation_ledger=inventory.ledger,
            ledger_authority=inventory.source_snapshot.ledger_source_authority,
            source_snapshot_sha256=authority.source_snapshot_sha256,
            observation_stage=authority.observation_stage,
        )
    )
    parent_issues = validate_verified_surface_binding_v2(
        mutation,
        parsed_surface_witness=None,
        candidate_text_bytes=candidate,
        obligation_ledger=None,
        ledger_authority=None,
        source_snapshot_sha256=authority.source_snapshot_sha256,
        observation_stage=authority.observation_stage,
    )
    assert parent_issues
    assert "PARENT_SCHEMA_MISMATCH" in _codes(parent_issues)

    mixed_key_issues = validate_parsed_surface_witness_v2(
        {1: object(), "x": object()},
        candidate_text_bytes=candidate,
    )
    assert mixed_key_issues
    assert "STRING_OBJECT_KEY_REQUIRED" in _codes(mixed_key_issues)

    non_json_parent_issues = validate_verified_surface_binding_v2(
        binding,
        parsed_surface_witness=object(),
        candidate_text_bytes=candidate,
        obligation_ledger=object(),
        ledger_authority=inventory.source_snapshot.ledger_source_authority,
        source_snapshot_sha256=authority.source_snapshot_sha256,
        observation_stage=authority.observation_stage,
    )
    assert non_json_parent_issues
    assert "PARENT_NON_CANONICAL" in _codes(non_json_parent_issues)

    malformed_atom = deepcopy(witness)
    malformed_atom["semantic_atoms"][0]["predicate_code"] = object()
    assert "MALFORMED_ARTIFACT" in _codes(
        validate_parsed_surface_witness_v2(
            malformed_atom,
            candidate_text_bytes=candidate,
        )
    )

    normal_stage_mismatch = deepcopy(binding)
    normal_stage_mismatch["bindings"] = []
    normal_stage_mismatch["binding_status"] = "source_context_mismatch"
    normal_stage_mismatch["failure_codes"] = [
        "SOURCE_CONTEXT_NOT_BODY_RECOVERABLE"
    ]
    assert "BINDING_STAGE_STATUS_MISMATCH" in _codes(
        validate_verified_surface_binding_v2(
            normal_stage_mismatch,
            parsed_surface_witness=witness,
            candidate_text_bytes=candidate,
            obligation_ledger=inventory.ledger,
            ledger_authority=inventory.source_snapshot.ledger_source_authority,
            source_snapshot_sha256=authority.source_snapshot_sha256,
            observation_stage=authority.observation_stage,
        )
    )

    pre_question_mismatch = deepcopy(binding)
    pre_question_mismatch["observation_stage"] = "pre_question_observation"
    assert "BINDING_STAGE_STATUS_MISMATCH" in _codes(
        validate_verified_surface_binding_v2(
            pre_question_mismatch,
            parsed_surface_witness=witness,
            candidate_text_bytes=candidate,
            obligation_ledger=inventory.ledger,
            ledger_authority=inventory.source_snapshot.ledger_source_authority,
            source_snapshot_sha256=authority.source_snapshot_sha256,
            observation_stage="pre_question_observation",
        )
    )


def test_s8_generic_body_stale_witness_and_clause_deletion_fail() -> None:
    context = _first_context("nls3s_b001_0001")
    generic = (
        "見えたこと：\nいくつかのことが見えます。\n\n"
        "Emlisから：\nその点を気に留めます。"
    ).encode("utf-8")
    generic_witness = parse_body_semantic_atoms(generic)
    assert generic_witness["parse_status"] == "unparseable"
    generic_binding = match_parsed_surface_witness(
        generic_witness,
        candidate_text_bytes=generic,
        inventory_result=context["inventory"],
        match_authority=context["match_authority"],
    )
    assert generic_binding["binding_status"] == "unparseable_surface"

    original = context["rendered"].utf8_bytes
    changed = original.replace("重さ".encode(), "軽さ".encode())
    assert len(changed) == len(original) and changed != original
    forged = deepcopy(context["witness"])
    candidate_sha = hashlib.sha256(changed).hexdigest()
    forged["candidate_text_sha256"] = candidate_sha
    old_to_new_atom_id: dict[str, str] = {}
    for atom in forged["semantic_atoms"]:
        start = atom["utf8_byte_start"]
        end = atom["utf8_byte_end"]
        atom["span_sha256"] = hashlib.sha256(changed[start:end]).hexdigest()
        old_atom_id = atom["atom_id"]
        atom["atom_id"] = "atom_" + artifact_sha256(
            {
                "candidate_text_sha256": candidate_sha,
                "section_role": atom["section_role"],
                "utf8_byte_start": start,
                "utf8_byte_end": end,
                "kind": atom["kind"],
            }
        )[:16]
        old_to_new_atom_id[old_atom_id] = atom["atom_id"]
    for atom in forged["semantic_atoms"]:
        if atom["kind"] != "bound_emlis_reception":
            continue
        atom["target_atom_ids"] = [
            old_to_new_atom_id[target] for target in atom["target_atom_ids"]
        ]
        atom["semantic_signature_sha256"] = artifact_sha256(
            {
                key: value
                for key, value in atom.items()
                if key
                not in {
                    "atom_id",
                    "semantic_signature_sha256",
                    "utf8_byte_start",
                    "utf8_byte_end",
                    "span_sha256",
                }
            }
        )
    assert not validate_parsed_surface_witness_v2(
        forged, candidate_text_bytes=changed
    )
    rejected = match_parsed_surface_witness(
        forged,
        candidate_text_bytes=changed,
        inventory_result=context["inventory"],
        match_authority=context["match_authority"],
    )
    assert rejected["binding_status"] == "no_semantic_binding"
    assert rejected["failure_codes"] == ["PARSED_WITNESS_REPLAY_MISMATCH"]

    _raises_match_code(
        lambda: match_parsed_surface_witness(
            context["witness"],
            candidate_text_bytes=changed,
            inventory_result=context["inventory"],
            match_authority=context["match_authority"],
        ),
        "MATCH_WITNESS_CONTRACT_REJECTED",
    )

    unknown = next(
        atom
        for atom in context["witness"]["semantic_atoms"]
        if atom["kind"] == "unknown_boundary"
    )
    joiner = SURFACE_GRAMMAR_CATALOG["clause_joiner"].encode("utf-8")
    assert original[unknown["utf8_byte_end"] :].startswith(joiner)
    without_unknown = (
        original[: unknown["utf8_byte_start"]]
        + original[unknown["utf8_byte_end"] + len(joiner) :]
    )
    witness, binding = _match_mutated(context, without_unknown)
    assert witness["parse_status"] == "parsed"
    assert binding["binding_status"] == "no_semantic_binding"


def test_s8_source_swap_authority_forgery_and_toctou_fail() -> None:
    first = _first_context("nls3s_b001_0051")
    second = _first_context("nls3s_b001_0054")
    swapped = match_parsed_surface_witness(
        first["witness"],
        candidate_text_bytes=first["rendered"].utf8_bytes,
        inventory_result=second["inventory"],
        match_authority=second["match_authority"],
    )
    assert swapped["binding_status"] == "no_semantic_binding"

    authority = first["match_authority"]
    forged = IndependentMatchSourceAuthority(
        authority_id=authority.authority_id,
        source_snapshot_sha256=authority.source_snapshot_sha256,
        obligation_ledger_sha256=authority.obligation_ledger_sha256,
        observation_stage=authority.observation_stage,
        grammar_catalog_sha256=authority.grammar_catalog_sha256,
        matcher_rulebook_sha256=authority.matcher_rulebook_sha256,
        body_free=True,
    )
    _raises_match_code(
        lambda: match_parsed_surface_witness(
            first["witness"],
            candidate_text_bytes=first["rendered"].utf8_bytes,
            inventory_result=first["inventory"],
            match_authority=forged,
        ),
        "MATCH_SOURCE_AUTHORITY_REQUIRED",
    )

    original_id = authority.authority_id
    try:
        object.__setattr__(authority, "authority_id", "matchauth_" + "0" * 24)
        _raises_match_code(
            lambda: match_parsed_surface_witness(
                first["witness"],
                candidate_text_bytes=first["rendered"].utf8_bytes,
                inventory_result=first["inventory"],
                match_authority=authority,
            ),
            "MATCH_SOURCE_PARENT_MISMATCH",
        )
    finally:
        object.__setattr__(authority, "authority_id", original_id)

    context = _first_context("nls3s_b001_0001")
    span = context["resolver"].resolve("s1")
    original_raw_text = span.raw_text
    try:
        object.__setattr__(span, "raw_text", "完全に別の入力")
        text = context["rendered"].utf8_bytes.decode("utf-8")
        anchor = _ANCHOR_RE.search(text)
        assert anchor is not None
        changed = text.replace(anchor.group(1), "完全に別の入力", 1).encode(
            "utf-8"
        )
        witness, binding = _match_mutated(context, changed)
        assert witness["parse_status"] == "parsed"
        assert binding["binding_status"] == "no_semantic_binding"
    finally:
        object.__setattr__(span, "raw_text", original_raw_text)

    fresh = _first_context("nls3s_b001_0001")
    span = fresh["resolver"].resolve("s1")
    original_raw_text = span.raw_text
    try:
        object.__setattr__(span, "raw_text", "完全に別の入力")
        _raises_match_code(
            lambda: open_independent_match_source_authority(
                fresh["inventory"],
                grounded_plan=fresh["grounded"],
                resolver=fresh["resolver"],
                observation_stage_context=fresh["stage"],
                original_input_bundle=fresh["sample"]["input"],
            ),
            "MATCH_SOURCE_REPLAY_FAILED",
        )
    finally:
        object.__setattr__(span, "raw_text", original_raw_text)


def test_s8_relation_unknown_graph_role_and_feature_mutations_fail() -> None:
    relation_context = _first_context("nls3s_b001_0051")
    relation_row = next(
        row
        for row in relation_context["binding"]["bindings"]
        if row["relation_id"] is not None
    )
    snapshot = relation_context["inventory"].source_snapshot
    relation = next(
        row
        for row in snapshot.relations
        if row.source_id == relation_row["relation_id"]
    )
    nuclei = {row.source_id: row for row in snapshot.nuclei}
    source_id = relation.from_nucleus_id
    target_id = relation.to_nucleus_id
    if relation_row["relation_direction"] == "target_to_source":
        source_id, target_id = target_id, source_id
    source_phrase = renderer_module._nucleus_phrase(nuclei[source_id])
    target_phrase = renderer_module._nucleus_phrase(nuclei[target_id])
    joiner = SURFACE_GRAMMAR_CATALOG["directed_relation_joiner"][
        relation.relation_type
    ]
    original_fragment = (
        source_phrase + joiner["left"] + target_phrase + joiner["right"]
    )
    reversed_fragment = (
        target_phrase + joiner["left"] + source_phrase + joiner["right"]
    )
    relation_text = relation_context["rendered"].utf8_bytes.decode("utf-8")
    assert relation_text.count(original_fragment) == 1
    reversed_bytes = relation_text.replace(
        original_fragment, reversed_fragment, 1
    ).encode("utf-8")
    witness, binding = _match_mutated(relation_context, reversed_bytes)
    assert witness["parse_status"] == "parsed"
    assert binding["binding_status"] == "no_semantic_binding"

    ordered_rendered = None
    ordered_witness = None
    for discourse in relation_context["plans"].plans:
        candidate = _render(
            discourse,
            inventory=relation_context["inventory"],
            content=relation_context["content"],
            lexical_authority=relation_context["lexical_authority"],
        )
        parsed = parse_body_semantic_atoms(candidate.utf8_bytes)
        roles = {
            row.get("graph_role")
            for row in parsed["semantic_atoms"]
            if row["kind"] != "bound_emlis_reception"
        }
        if {"precedes_source", "precedes_target"} <= roles:
            ordered_rendered = candidate
            ordered_witness = parsed
            break
    assert ordered_rendered is not None and ordered_witness is not None
    source_atom = next(
        row
        for row in ordered_witness["semantic_atoms"]
        if row.get("graph_role") == "precedes_source"
    )
    target_atom = next(
        row
        for row in ordered_witness["semantic_atoms"]
        if row.get("graph_role") == "precedes_target"
    )
    assert source_atom["utf8_byte_end"] <= target_atom["utf8_byte_start"]
    ordered_bytes = ordered_rendered.utf8_bytes
    swapped_order = (
        ordered_bytes[: source_atom["utf8_byte_start"]]
        + ordered_bytes[
            target_atom["utf8_byte_start"] : target_atom["utf8_byte_end"]
        ]
        + ordered_bytes[
            source_atom["utf8_byte_end"] : target_atom["utf8_byte_start"]
        ]
        + ordered_bytes[
            source_atom["utf8_byte_start"] : source_atom["utf8_byte_end"]
        ]
        + ordered_bytes[target_atom["utf8_byte_end"] :]
    )
    swapped_witness, swapped_binding = _match_mutated(
        relation_context, swapped_order
    )
    assert swapped_witness["parse_status"] == "parsed"
    assert swapped_binding["binding_status"] == "no_semantic_binding"

    context = _first_context("nls3s_b001_0001")
    text = context["rendered"].utf8_bytes.decode("utf-8")
    mutations = (
        text.replace("重さを含む", "明るさを含む"),
        text.replace("伝えられた範囲で、", "可能性の範囲で、", 1),
        text.replace("気に留めます", "軽く扱いません", 1),
        text.replace(_ANCHOR_RE.search(text).group(1), "完全に別の入力", 1),
        text.replace("分からなさが関わる", "順序の前側にある", 1),
    )
    for mutation in mutations:
        witness, binding = _match_mutated(context, mutation.encode("utf-8"))
        assert witness["parse_status"] == "parsed"
        assert binding["binding_status"] == "no_semantic_binding"

    marker_attack = text.replace(
        "見えたこと：\n", "見えたこと：\n逆向きとして、", 1
    ).encode("utf-8")
    marker_witness = parse_body_semantic_atoms(marker_attack)
    assert marker_witness["parse_status"] == "unparseable"
    predicate_attack = text.replace(
        "が見えます", "結びつきが保たれています", 1
    ).encode("utf-8")
    predicate_witness = parse_body_semantic_atoms(predicate_attack)
    assert predicate_witness["parse_status"] == "unparseable"


def test_s8_stage_boundary_and_source_role_are_fail_closed() -> None:
    normal = _first_context("nls3s_b001_0001")
    current_input = normal["sample"]["input"]
    spans = build_evidence_ledger(current_input)
    resolver = build_evidence_span_resolver(
        spans, current_input=current_input
    )
    grounded = build_grounded_observation_plan(
        current_input, evidence_spans=spans
    )
    future = TrustedFutureStageAuthority(
        authority_owner="question_system_core",
        question_need_decision_sha256="a" * 64,
        permitted_stages=("pre_question_observation",),
        original_input_bundle_sha256=artifact_sha256(current_input),
        supplemental_answer_bundle_sha256=None,
    )
    stage = build_observation_stage_context(
        stage="pre_question_observation",
        original_input_bundle=current_input,
        trusted_future_authority=future,
    )
    snapshot = build_grounded_source_snapshot(
        grounded,
        resolver,
        observation_stage_context=stage,
        original_input_bundle=current_input,
        trusted_future_authority=future,
    )
    inventory = build_semantic_obligation_inventory(snapshot)
    authority = open_independent_match_source_authority(
        inventory,
        grounded_plan=grounded,
        resolver=resolver,
        observation_stage_context=stage,
        original_input_bundle=current_input,
        trusted_future_authority=future,
    )
    result = match_parsed_surface_witness(
        normal["witness"],
        candidate_text_bytes=normal["rendered"].utf8_bytes,
        inventory_result=inventory,
        match_authority=authority,
    )
    assert result["binding_status"] == "source_context_mismatch"
    assert result["failure_codes"] == ["SOURCE_CONTEXT_NOT_BODY_RECOVERABLE"]

    supplemental = {"answer": "不安は結果が読めない点についてです。"}
    refined_future = TrustedFutureStageAuthority(
        authority_owner="question_system_core",
        question_need_decision_sha256="b" * 64,
        permitted_stages=("refined_observation",),
        original_input_bundle_sha256=artifact_sha256(current_input),
        supplemental_answer_bundle_sha256=artifact_sha256(supplemental),
    )
    refined_stage = build_observation_stage_context(
        stage="refined_observation",
        original_input_bundle=current_input,
        trusted_future_authority=refined_future,
        supplemental_answer_bundle=supplemental,
    )
    try:
        build_grounded_source_snapshot(
            grounded,
            resolver,
            observation_stage_context=refined_stage,
            original_input_bundle=current_input,
            trusted_future_authority=refined_future,
            supplemental_answer_bundle=supplemental,
        )
    except SemanticObligationInventoryError as exc:
        assert exc.code == "REFINED_SOURCE_PARTITION_OWNER_UNAVAILABLE"
    else:
        raise AssertionError("refined source-role partition became implicit")


def test_s8_syntax_dependency_drift_and_import_boundaries_fail_closed() -> None:
    context = _first_context("nls3s_b001_0001")
    candidate = context["rendered"].utf8_bytes
    _raises_parse_code(
        lambda: parse_body_semantic_atoms(b"\xff"),
        "CANDIDATE_UTF8_REQUIRED",
    )
    crlf = candidate.decode("utf-8").replace("\n", "\r\n").encode("utf-8")
    assert parse_body_semantic_atoms(crlf)["parse_status"] == "unparseable"
    nfd = ("e\u0301" + candidate.decode("utf-8")).encode("utf-8")
    assert unicodedata.normalize("NFC", nfd.decode("utf-8")) != nfd.decode(
        "utf-8"
    )
    assert parse_body_semantic_atoms(nfd)["parse_status"] == "unparseable"
    swapped_labels = candidate.decode("utf-8").replace(
        "見えたこと：", "Emlisから：", 1
    ).encode("utf-8")
    assert parse_body_semantic_atoms(swapped_labels)["parse_status"] == (
        "unparseable"
    )

    original_label = step8_catalog_module.STEP8_SURFACE_GRAMMAR_CATALOG[
        "document"
    ]["observation_label"]
    try:
        step8_catalog_module.STEP8_SURFACE_GRAMMAR_CATALOG["document"][
            "observation_label"
        ] = "INJECTED"
        _raises_parse_code(
            lambda: parse_body_semantic_atoms(candidate),
            "PARSER_DEPENDENCY_DRIFT",
        )
    finally:
        step8_catalog_module.STEP8_SURFACE_GRAMMAR_CATALOG["document"][
            "observation_label"
        ] = original_label

    original_parser_version = parser_module._PARSER_RULEBOOK["version"]
    try:
        parser_module._PARSER_RULEBOOK["version"] = "mutated"
        _raises_parse_code(
            lambda: parse_body_semantic_atoms(candidate),
            "PARSER_DEPENDENCY_DRIFT",
        )
    finally:
        parser_module._PARSER_RULEBOOK["version"] = original_parser_version

    original_matcher_version = matcher_module._MATCHER_RULEBOOK["version"]
    try:
        matcher_module._MATCHER_RULEBOOK["version"] = "mutated"
        _raises_match_code(
            lambda: match_parsed_surface_witness(
                context["witness"],
                candidate_text_bytes=candidate,
                inventory_result=context["inventory"],
                match_authority=context["match_authority"],
            ),
            "MATCHER_DEPENDENCY_DRIFT",
        )
    finally:
        matcher_module._MATCHER_RULEBOOK["version"] = original_matcher_version

    parser_path = _INFERENCE_ROOT / "emlis_ai_body_semantic_atom_parser_v3.py"
    matcher_path = _INFERENCE_ROOT / "emlis_ai_independent_semantic_matcher_v3.py"
    banned = {
        "emlis_ai_canonical_renderer_v3",
        "emlis_ai_typed_surface_ast_v3",
        "emlis_ai_discourse_graph_planner_v3",
        "emlis_ai_content_selection_v3",
    }
    for path in (parser_path, matcher_path):
        tree = python_ast.parse(path.read_text(encoding="utf-8"))
        targets: set[str] = set()
        for node in python_ast.walk(tree):
            if isinstance(node, python_ast.Import):
                targets.update(alias.name for alias in node.names)
            elif isinstance(node, python_ast.ImportFrom) and node.module:
                targets.add(node.module)
        assert not (targets & banned), (path.name, targets & banned)
        source = path.read_text(encoding="utf-8")
        for cue in (
            "case_id",
            "family_id",
            "batch_id",
            "expected_surface",
            "expected_text",
        ):
            assert cue not in source

    parser_signature = inspect.signature(parse_body_semantic_atoms)
    assert tuple(parser_signature.parameters) == ("candidate_text_bytes",)
    reply_imports = (_INFERENCE_ROOT / "emlis_ai_reply_service.py").read_text(
        encoding="utf-8"
    )
    assert "emlis_ai_body_semantic_atom_parser_v3" not in reply_imports
    assert "emlis_ai_independent_semantic_matcher_v3" not in reply_imports
