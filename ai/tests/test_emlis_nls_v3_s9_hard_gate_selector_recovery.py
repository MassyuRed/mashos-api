# -*- coding: utf-8 -*-
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import replace
import ast as python_ast
import hashlib
import inspect
from itertools import permutations
from pathlib import Path
import random

import emlis_ai_lexicographic_selector_v3 as selector_module
import emlis_ai_step9_artifact_contract_v3 as contract_module
from emlis_ai_bounded_recovery_v3 import (
    BoundedRecoveryError,
)
from emlis_ai_canonical_renderer_v3 import open_request_lexical_authority
from emlis_ai_content_selection_v3 import build_content_selection_plan
from emlis_ai_discourse_graph_planner_v3 import build_discourse_graph_plans
from emlis_ai_evidence_ledger_service import (
    build_evidence_ledger,
    build_evidence_span_resolver,
)
from emlis_ai_grounded_observation_plan import build_grounded_observation_plan
from emlis_ai_independent_semantic_matcher_v3 import (
    open_independent_match_source_authority,
)
from emlis_ai_lexicographic_selector_v3 import (
    LexicographicSelectorError,
)
from emlis_ai_nls_v3_artifact_contract import (
    TrustedFutureStageAuthority,
    artifact_sha256,
)
from emlis_ai_observation_stage_context_v3 import (
    build_observation_stage_context,
)
from emlis_ai_semantic_hard_gate_v3 import (
    hard_gate_dataclass_fields,
    hard_gate_failure_codes,
)
from emlis_ai_semantic_obligation_inventory_v3 import (
    build_grounded_source_snapshot,
    build_semantic_obligation_inventory,
)
from emlis_ai_step9_artifact_contract_v3 import (
    FROZEN_STEP9_DEPENDENCY_MANIFEST_SHA256,
    FROZEN_HARD_GATE_POLICY_SHA256,
    FROZEN_RECOVERY_POLICY_SHA256,
    FROZEN_SELECTOR_POLICY_SHA256,
    HARD_GATE_POLICY,
    RECOVERY_POLICY,
    SemanticCandidate,
    validate_hard_gate_result_structure,
    validate_recovery_trace_structure,
    validate_selector_decision_structure,
    validate_step9_policies as validate_historical_step9_policies,
)
import emlis_ai_step9_dependency_manifest_v3 as dependency_manifest_module
from emlis_ai_step9_recovery_epoch001_successor_v3 import (
    apply_bounded_recovery as select_with_bounded_recovery,
    build_semantic_candidate_set,
    evaluate_semantic_hard_gate,
    select_semantic_candidate_lexicographically as select_semantic_candidates,
    validate_bounded_recovery_result,
    validate_semantic_hard_gate_result,
    validate_semantic_selection_result,
)
from test_emlis_nls_v3_s8_body_parser_independent_matcher import (
    _first_context,
    _normal_parents,
    _samples,
)


_HERE = Path(__file__).resolve().parent
_INFERENCE_ROOT = _HERE.parent / "services" / "ai_inference"


def _candidate(context, plan_index: int = 0) -> SemanticCandidate:
    return build_semantic_candidate_set(
        (context["plans"].plans[plan_index],),
        inventory_result=context["inventory"],
        content_plan=context["content"],
        lexical_authority=context["lexical_authority"],
        match_authority=context["match_authority"],
    )[0]


def _candidate_from_parents(parents, plan_index: int = 0) -> SemanticCandidate:
    (
        _grounded,
        _resolver,
        _stage,
        inventory,
        content,
        plans,
        lexical_authority,
        match_authority,
    ) = parents
    return build_semantic_candidate_set(
        (plans.plans[plan_index],),
        inventory_result=inventory,
        content_plan=content,
        lexical_authority=lexical_authority,
        match_authority=match_authority,
    )[0]


def _assert_historical_step9_manifest_is_noncurrent() -> None:
    assert validate_historical_step9_policies() == (
        "STEP9_DEPENDENCY_SOURCE_BYTES_DRIFT",
    )


def _gate(context, candidate: SemanticCandidate):
    return evaluate_semantic_hard_gate(
        candidate,
        inventory_result=context["inventory"],
        content_plan=context["content"],
        lexical_authority=context["lexical_authority"],
        match_authority=context["match_authority"],
    )


def _outcome(result, gate_id: str):
    return next(row for row in result.outcomes if row.gate_id == gate_id)


def _with(
    candidate: SemanticCandidate,
    *,
    discourse_plan=None,
    surface_ast=None,
    rendered_surface=None,
    witness=None,
    binding=None,
) -> SemanticCandidate:
    return SemanticCandidate(
        discourse_plan=(
            discourse_plan if discourse_plan is not None else candidate.discourse_plan
        ),
        surface_ast=surface_ast if surface_ast is not None else candidate.surface_ast,
        rendered_surface=(
            rendered_surface
            if rendered_surface is not None
            else candidate.rendered_surface
        ),
        parsed_surface_witness=(
            witness if witness is not None else candidate.parsed_surface_witness
        ),
        verified_surface_binding=(
            binding if binding is not None else candidate.verified_surface_binding
        ),
    )


def _candidate_with_atom(case_id: str, kind: str):
    context = _first_context(case_id)
    for index in range(len(context["plans"].plans)):
        candidate = _candidate(context, index)
        if any(
            atom["kind"] == kind
            for atom in candidate.parsed_surface_witness["semantic_atoms"]
        ):
            return context, candidate
    raise AssertionError((case_id, kind))


def test_s9_step0_step8_bytes_and_side_by_side_policies_are_frozen() -> None:
    expected_files = {
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
        "emlis_ai_surface_grammar_catalog_v3_step8.py": (
            "844e2c314bcfadbee6bc59b8a1863f958c5418c9da3a4c3ac960ad902b27fafb"
        ),
        "emlis_ai_step8_artifact_contract_v3.py": (
            "50768051c12128ebb62ed0f01116251fb488f2c3204ffb6f291d895c36d8fbe8"
        ),
        "emlis_ai_body_semantic_atom_parser_v3.py": (
            "a006c87081b7f3978305a8a024c22f9d27be0e5f034a900f5341f3b59a13cc9f"
        ),
        "emlis_ai_independent_semantic_matcher_v3.py": (
            "12f040407adc299b2695ee58b93619157690cfb745072b4e72f529ee5dd2ed9e"
        ),
    }
    for filename, expected in expected_files.items():
        assert hashlib.sha256((_INFERENCE_ROOT / filename).read_bytes()).hexdigest() == expected

    assert FROZEN_HARD_GATE_POLICY_SHA256 == (
        "18007a7bbe794ebf77c148558d787d69cab0653b35ea2c2cc776e22161f2e46f"
    )
    assert FROZEN_SELECTOR_POLICY_SHA256 == (
        "39855afcaa59fe09d00a8fd1d95afaf99e4ac5d5524526e4e1217ea9f293663f"
    )
    assert FROZEN_RECOVERY_POLICY_SHA256 == (
        "867ebcfb171f823f4a675ac544f216039b63d5db1dddced7178a95f6b0427a55"
    )
    assert FROZEN_STEP9_DEPENDENCY_MANIFEST_SHA256 == (
        "9ac49f3ee8978f48ff402afdd9fb15f16063595546898e514b09b9bdaf58e880"
    )
    _assert_historical_step9_manifest_is_noncurrent()
    assert [row["ordinal"] for row in HARD_GATE_POLICY["gates"]] == list(
        range(1, 21)
    )
    assert hard_gate_dataclass_fields() == (
        "discourse_plan",
        "surface_ast",
        "rendered_surface",
        "parsed_surface_witness",
        "verified_surface_binding",
    )
    for forbidden in (
        "covered_obligation_ids",
        "score",
        "weighted_score",
        "hard_gate_status",
        "selection_preference",
    ):
        assert forbidden not in hard_gate_dataclass_fields()


def test_s9_decision_contracts_reject_malformed_shapes_fail_closed() -> None:
    context = _first_context("nls3s_b001_0001")
    candidate = _candidate(context)
    gate = _gate(context, candidate)

    malformed_parents = replace(gate, parent_hashes=(("broken",),))
    assert "HARD_GATE_PARENT_HASHES_INVALID" in (
        validate_hard_gate_result_structure(malformed_parents)
    )
    malformed_outcomes = replace(gate, outcomes=(object(),) * 20)
    assert "HARD_GATE_OUTCOME_TYPE_INVALID" in (
        validate_hard_gate_result_structure(malformed_outcomes)
    )
    malformed_attributes = replace(
        gate.selector_attributes,
        required_binding_count=True,
    )
    assert "SELECTOR_ATTRIBUTE_VALUE_INVALID" in (
        validate_hard_gate_result_structure(
            replace(gate, selector_attributes=malformed_attributes)
        )
    )

    selection = select_semantic_candidates(
        [candidate],
        inventory_result=context["inventory"],
        content_plan=context["content"],
        lexical_authority=context["lexical_authority"],
        match_authority=context["match_authority"],
    )
    malformed_decision = replace(
        selection.decision,
        evaluated_candidate_ids=None,
    )
    assert "SELECTOR_EVALUATED_IDS_INVALID" in (
        validate_selector_decision_structure(malformed_decision)
    )

    recovered = select_with_bounded_recovery(
        [candidate],
        inventory_result=context["inventory"],
        content_plan=context["content"],
        lexical_authority=context["lexical_authority"],
        match_authority=context["match_authority"],
    )
    malformed_attempts = replace(recovered.trace, attempts=(object(),))
    assert "RECOVERY_ATTEMPT_TYPE_INVALID" in (
        validate_recovery_trace_structure(malformed_attempts)
    )
    malformed_count = replace(recovered.trace, total_candidate_count="1")
    assert "RECOVERY_TOTAL_LIMIT_EXCEEDED" in (
        validate_recovery_trace_structure(malformed_count)
    )
    malformed_result = replace(recovered, selection=None)
    assert validate_bounded_recovery_result(
        malformed_result,
        initial_candidates=[candidate],
        inventory_result=context["inventory"],
        content_plan=context["content"],
        lexical_authority=context["lexical_authority"],
        match_authority=context["match_authority"],
    ) == ("RECOVERY_RESULT_TYPE_INVALID",)


def test_s9_all_100_inputs_596_candidates_hard_pass_and_select() -> None:
    samples = _samples()
    assert len(samples) == 100
    candidate_count = 0
    selected_count = 0
    plan_distribution: Counter[int] = Counter()
    for sample in samples:
        parents = _normal_parents(sample["input"])
        (
            _grounded,
            _resolver,
            _stage,
            inventory,
            content,
            plans,
            lexical_authority,
            match_authority,
        ) = parents
        candidates = list(
            build_semantic_candidate_set(
                plans.plans,
                inventory_result=inventory,
                content_plan=content,
                lexical_authority=lexical_authority,
                match_authority=match_authority,
            )
        )
        selection = select_semantic_candidates(
            candidates,
            inventory_result=inventory,
            content_plan=content,
            lexical_authority=lexical_authority,
            match_authority=match_authority,
        )
        assert selection.decision.status == "selected", sample["case_id"]
        assert selection.decision.v3_success is True
        assert selection.decision.v1_fallback_used is False
        assert selection.decision.v1_fallback_counts_as_v3_success is False
        assert len(selection.gate_results) == len(candidates)
        assert all(result.hard_pass for result in selection.gate_results)
        assert all(len(result.outcomes) == 20 for result in selection.gate_results)
        required_count = len(inventory.ledger["required_obligation_ids"])
        required_groups = {
            row["distinctness_group"]
            for row in inventory.ledger["obligations"]
            if row["obligation_id"] in inventory.ledger["required_obligation_ids"]
        }
        assert all(
            result.selector_attributes.required_binding_count == required_count
            for result in selection.gate_results
        )
        assert all(
            result.selector_attributes.required_distinctness_group_count
            == len(required_groups)
            for result in selection.gate_results
        )
        assert not validate_selector_decision_structure(selection.decision)
        candidate_count += len(candidates)
        selected_count += 1
        plan_distribution[len(candidates)] += 1
    assert candidate_count == 596
    assert selected_count == 100
    assert plan_distribution == Counter(
        {1: 8, 2: 35, 4: 8, 6: 13, 8: 4, 9: 2, 10: 1, 12: 29}
    )


def test_s9_each_of_twenty_gate_rows_has_a_dedicated_negative_path() -> None:
    base_context = _first_context("nls3s_b001_0051")
    base = _candidate(base_context)
    mutations: dict[str, tuple[SemanticCandidate, str]] = {}

    witness = deepcopy(base.parsed_surface_witness)
    witness["schema_version"] = "forged.witness.v9"
    mutations["artifact_schema_parent_hash"] = (
        _with(base, witness=witness),
        "INVALID_SCHEMA",
    )

    rendered = replace(base.rendered_surface, sha256="0" * 64)
    mutations["canonical_render_equality"] = (
        _with(base, rendered_surface=rendered),
        "RENDER_TEXT_MISMATCH",
    )

    invalid_bytes = b"not controlled surface"
    rendered = replace(
        base.rendered_surface,
        utf8_bytes=invalid_bytes,
        sha256=hashlib.sha256(invalid_bytes).hexdigest(),
    )
    mutations["body_parseability"] = (
        _with(base, rendered_surface=rendered),
        "UNPARSABLE_CONTROLLED_SURFACE",
    )

    binding = deepcopy(base.verified_surface_binding)
    binding["bindings"] = []
    binding["binding_status"] = "no_semantic_binding"
    binding["failure_codes"] = ["NO_SEMANTIC_BINDING"]
    mutations["evidence_resolution"] = (
        _with(base, binding=binding),
        "NO_SEMANTIC_BINDING",
    )

    binding = deepcopy(base.verified_surface_binding)
    binding["bindings"] = binding["bindings"][1:]
    mutations["required_obligation_coverage"] = (
        _with(base, binding=binding),
        "REQUIRED_OBLIGATION_MISSING",
    )

    binding = deepcopy(base.verified_surface_binding)
    stance = next(
        row for row in binding["bindings"] if row["target_obligation_ids"]
    )
    stance["target_obligation_ids"] = []
    mutations["bound_emlis_reception"] = (
        _with(base, binding=binding),
        "UNBOUND_EMLIS_RECEPTION",
    )

    witness = deepcopy(base.parsed_surface_witness)
    atom = witness["semantic_atoms"][0]
    atom["polarity"] = (
        "negative" if atom["polarity"] != "negative" else "positive"
    )
    mutations["polarity_modality_time"] = (
        _with(base, witness=witness),
        "POLARITY_INVERSION",
    )

    relation_context, relation_candidate = _candidate_with_atom(
        "nls3s_b001_0051", "grounded_relation"
    )
    binding = deepcopy(relation_candidate.verified_surface_binding)
    relation_row = next(row for row in binding["bindings"] if row["relation_id"])
    relation_row["relation_direction"] = (
        "bidirectional"
        if relation_row["relation_direction"] != "bidirectional"
        else "source_to_target"
    )
    mutations["relation_type_direction"] = (
        _with(relation_candidate, binding=binding),
        "RELATION_DIRECTION_INVERSION",
    )

    binding = deepcopy(base.verified_surface_binding)
    binding["bindings"][0]["topic_scope_ids"] = ["topic_deadbeefdeadbeef"]
    mutations["referent_topic_scope"] = (
        _with(base, binding=binding),
        "TOPIC_MIX",
    )

    witness = deepcopy(base.parsed_surface_witness)
    unknown = next(
        atom for atom in witness["semantic_atoms"] if atom["kind"] == "unknown_boundary"
    )
    unknown["unknown_dimension_codes"] = (
        ["cause"]
        if unknown["unknown_dimension_codes"] != ["cause"]
        else ["other"]
    )
    mutations["unknown_boundary"] = (
        _with(base, witness=witness),
        "UNKNOWN_BOUNDARY_DROPPED",
    )

    witness = deepcopy(base.parsed_surface_witness)
    self_atom = next(
        atom
        for atom in witness["semantic_atoms"]
        if atom["kind"] == "grounded_nucleus"
    )
    self_atom["kind"] = "self_denial_boundary"
    mutations["self_denial_boundary"] = (
        _with(base, witness=witness),
        "SELF_DENIAL_ADOPTED",
    )

    surface_ast = deepcopy(base.surface_ast)
    surface_ast["sections"][0]["sentences"][0]["clauses"][0]["nodes"].append(
        {"node_type": "invented_claim", "form": "invented_cause"}
    )
    mutations["unsupported_claim"] = (
        _with(base, surface_ast=surface_ast),
        "UNSUPPORTED_CLAIM",
    )

    witness = deepcopy(base.parsed_surface_witness)
    reception = next(
        atom
        for atom in witness["semantic_atoms"]
        if atom["kind"] == "bound_emlis_reception"
    )
    reception["section_role"] = "observation"
    mutations["observation_reception_distinctness"] = (
        _with(base, witness=witness),
        "SECTION_SEMANTIC_REPLAY",
    )

    witness = deepcopy(base.parsed_surface_witness)
    nonstance = [
        atom
        for atom in witness["semantic_atoms"]
        if atom["kind"] != "bound_emlis_reception"
    ]
    anchor = next(
        atom["source_anchor_sha256"]
        for atom in nonstance
        if atom["source_anchor_sha256"] is not None
    )
    target = next(atom for atom in nonstance if atom["source_anchor_sha256"] is None)
    target["source_anchor_sha256"] = anchor
    target["source_anchor_scalar_count"] = 2
    mutations["input_enumeration_shallow_mirror"] = (
        _with(base, witness=witness),
        "ANCHOR_REPLAY",
    )

    binding = deepcopy(base.verified_surface_binding)
    binding["bindings"][1]["obligation_id"] = binding["bindings"][0][
        "obligation_id"
    ]
    mutations["contribution_distinctness"] = (
        _with(base, binding=binding),
        "DISTINCT_OBLIGATIONS_COLLAPSED",
    )

    discourse = deepcopy(base.discourse_plan)
    discourse["sentence_groups"] = []
    mutations["depth_proportionality"] = (
        _with(base, discourse_plan=discourse),
        "DEPTH_TRUNCATED",
    )

    broken_bytes = b"\xff"
    rendered = replace(
        base.rendered_surface,
        utf8_bytes=broken_bytes,
        sha256=hashlib.sha256(broken_bytes).hexdigest(),
    )
    mutations["surface_integrity"] = (
        _with(base, rendered_surface=rendered),
        "BROKEN_GRAMMAR",
    )

    surface_ast = deepcopy(base.surface_ast)
    surface_ast["username"] = "invented"
    mutations["naming_address_contract"] = (
        _with(base, surface_ast=surface_ast),
        "USER_NAME_INVENTED",
    )

    witness = deepcopy(base.parsed_surface_witness)
    witness["body_free_export_allowed"] = True
    mutations["body_free_public_contract"] = (
        _with(base, witness=witness),
        "RAW_BODY_LEAK",
    )

    for gate_id, (mutation, expected_code) in mutations.items():
        context = (
            relation_context
            if gate_id == "relation_type_direction"
            else base_context
        )
        result = _gate(context, mutation)
        outcome = _outcome(result, gate_id)
        assert outcome.status == "failed", (gate_id, outcome)
        assert expected_code in outcome.failure_codes, (gate_id, outcome)
        if gate_id == "unsupported_claim":
            assert "INVENTED_CAUSE" in outcome.failure_codes
        assert result.hard_pass is False

    for claim_value, expected_code in (
        ("personality_claim", "PERSONALITY_CLAIM"),
        ("diagnosis_claim", "DIAGNOSIS_CLAIM"),
        ("future_guarantee", "FUTURE_GUARANTEE"),
    ):
        surface_ast = deepcopy(base.surface_ast)
        surface_ast["sections"][0]["sentences"][0]["clauses"][0][
            "nodes"
        ].append({"node_type": "invented_claim", "form": claim_value})
        outcome = _outcome(
            _gate(base_context, _with(base, surface_ast=surface_ast)),
            "unsupported_claim",
        )
        assert expected_code in outcome.failure_codes

    original_scope = HARD_GATE_POLICY["runtime_scope"]
    try:
        HARD_GATE_POLICY["runtime_scope"] = "mutated"
        dependency = _gate(base_context, base)
        outcome = _outcome(dependency, "version_dependency_closure")
        assert outcome.status == "failed"
        assert outcome.failure_codes == ("DEPENDENCY_DRIFT",)
    finally:
        HARD_GATE_POLICY["runtime_scope"] = original_scope
    _assert_historical_step9_manifest_is_noncurrent()

    HARD_GATE_POLICY["cycle"] = HARD_GATE_POLICY
    try:
        dependency = _gate(base_context, base)
        assert _outcome(
            dependency, "version_dependency_closure"
        ).failure_codes == ("DEPENDENCY_DRIFT",)
    finally:
        del HARD_GATE_POLICY["cycle"]
    _assert_historical_step9_manifest_is_noncurrent()

    source_files = dependency_manifest_module.STEP9_DEPENDENCY_MANIFEST[
        "source_files"
    ]
    original_public_owner_sha = source_files["emlis_ai_reply_service.py"]
    try:
        source_files["emlis_ai_reply_service.py"] = "0" * 64
        dependency = _gate(base_context, base)
        assert _outcome(
            dependency, "version_dependency_closure"
        ).status == "passed"
        assert _outcome(
            dependency, "body_free_public_contract"
        ).status == "passed"
        assert validate_historical_step9_policies()
    finally:
        source_files["emlis_ai_reply_service.py"] = original_public_owner_sha
    _assert_historical_step9_manifest_is_noncurrent()

    original_source_files = dependency_manifest_module.STEP9_DEPENDENCY_MANIFEST[
        "source_files"
    ]
    try:
        dependency_manifest_module.STEP9_DEPENDENCY_MANIFEST["source_files"] = []
        dependency = _gate(base_context, base)
        assert _outcome(
            dependency, "version_dependency_closure"
        ).status == "passed"
        assert _outcome(
            dependency, "body_free_public_contract"
        ).status == "passed"
        assert validate_historical_step9_policies()
    finally:
        dependency_manifest_module.STEP9_DEPENDENCY_MANIFEST[
            "source_files"
        ] = original_source_files
    _assert_historical_step9_manifest_is_noncurrent()


def test_s9_v2_recurrence_attacks_and_result_self_declaration_fail() -> None:
    first = _first_context("nls3s_b001_0001")
    second = _first_context("nls3s_b001_0054")
    first_candidate = _candidate(first)
    second_candidate = _candidate(second)

    generic = (
        "見えたこと：\nいくつかのことが見えます。\n\n"
        "Emlisから：\nそのことを受け取ります。"
    ).encode("utf-8")
    generic_render = replace(
        first_candidate.rendered_surface,
        utf8_bytes=generic,
        sha256=hashlib.sha256(generic).hexdigest(),
    )
    generic_candidate = _with(
        first_candidate,
        rendered_surface=generic_render,
    )
    generic_result = _gate(first, generic_candidate)
    assert generic_result.hard_pass is False
    assert {
        "RENDER_TEXT_MISMATCH",
        "UNPARSABLE_CONTROLLED_SURFACE",
    } <= set(hard_gate_failure_codes(generic_result))

    stale_hash_render = replace(
        first_candidate.rendered_surface,
        utf8_bytes=b"stale final bytes",
    )
    stale_hash_result = _gate(
        first,
        _with(first_candidate, rendered_surface=stale_hash_render),
    )
    valid_identity_result = _gate(first, first_candidate)
    assert stale_hash_result.candidate_id != valid_identity_result.candidate_id
    assert stale_hash_result.candidate_text_sha256 == hashlib.sha256(
        b"stale final bytes"
    ).hexdigest()

    source_swap = evaluate_semantic_hard_gate(
        first_candidate,
        inventory_result=second["inventory"],
        content_plan=second["content"],
        lexical_authority=second["lexical_authority"],
        match_authority=second["match_authority"],
    )
    assert source_swap.hard_pass is False
    assert "NO_SEMANTIC_BINDING" in hard_gate_failure_codes(source_swap)

    simultaneous_swap = evaluate_semantic_hard_gate(
        second_candidate,
        inventory_result=first["inventory"],
        content_plan=first["content"],
        lexical_authority=first["lexical_authority"],
        match_authority=first["match_authority"],
    )
    assert simultaneous_swap.hard_pass is False
    assert "REQUIRED_OBLIGATION_MISSING" in hard_gate_failure_codes(
        simultaneous_swap
    )

    cyclic_ast = dict(first_candidate.surface_ast)
    cyclic_ast["cycle"] = cyclic_ast
    cyclic_result = _gate(
        first,
        _with(first_candidate, surface_ast=cyclic_ast),
    )
    assert cyclic_result.hard_pass is False
    assert "INVALID_SCHEMA" in hard_gate_failure_codes(cyclic_result)

    malformed_witness = deepcopy(first_candidate.parsed_surface_witness)
    malformed_witness["semantic_atoms"][0]["utf8_byte_start"] = "x"
    malformed_witness["semantic_atoms"][0]["atom_id"] = []
    malformed_witness["semantic_atoms"][0]["kind"] = []
    malformed_binding = deepcopy(first_candidate.verified_surface_binding)
    malformed_binding["bindings"][0]["obligation_id"] = []
    malformed_nested_result = _gate(
        first,
        _with(
            first_candidate,
            witness=malformed_witness,
            binding=malformed_binding,
        ),
    )
    assert malformed_nested_result.hard_pass is False
    assert "INVALID_SCHEMA" in hard_gate_failure_codes(malformed_nested_result)

    malformed_witness_shape = deepcopy(first_candidate.parsed_surface_witness)
    malformed_witness_shape["semantic_atoms"] = 1
    malformed_binding_shape = deepcopy(first_candidate.verified_surface_binding)
    malformed_binding_shape["bindings"] = 1
    malformed_shape_result = _gate(
        first,
        SemanticCandidate(
            discourse_plan=[],
            surface_ast=[],
            rendered_surface=first_candidate.rendered_surface,
            parsed_surface_witness=malformed_witness_shape,
            verified_surface_binding=malformed_binding_shape,
        ),
    )
    assert malformed_shape_result.hard_pass is False
    assert "INVALID_SCHEMA" in hard_gate_failure_codes(malformed_shape_result)

    malformed_signature_plan = dict(first_candidate.discourse_plan)
    cyclic_signature: dict[str, object] = {}
    cyclic_signature["cycle"] = cyclic_signature
    malformed_signature_plan["structural_signature"] = cyclic_signature
    malformed_signature_result = _gate(
        first,
        _with(first_candidate, discourse_plan=malformed_signature_plan),
    )
    assert malformed_signature_result.hard_pass is False
    assert "INVALID_SCHEMA" in hard_gate_failure_codes(
        malformed_signature_result
    )

    malformed_ledger = deepcopy(first["inventory"].ledger)
    malformed_ledger["required_obligation_ids"] = 1
    malformed_inventory = replace(first["inventory"], ledger=malformed_ledger)
    malformed_content = deepcopy(first["content"])
    malformed_content["decisions"] = 1
    malformed_content["section_budget"] = {
        "observation_sentence_min": "0",
        "observation_sentence_max": "1",
        "reception_sentence_min": "0",
        "reception_sentence_max": "1",
        "total_sentence_max": "2",
    }
    malformed_parent_result = evaluate_semantic_hard_gate(
        first_candidate,
        inventory_result=malformed_inventory,
        content_plan=malformed_content,
        lexical_authority=first["lexical_authority"],
        match_authority=first["match_authority"],
    )
    assert malformed_parent_result.hard_pass is False
    assert "INVALID_SCHEMA" in hard_gate_failure_codes(malformed_parent_result)

    malformed_match_authority = replace(
        first["match_authority"],
        source_snapshot_sha256="z" * 64,
    )
    malformed_authority_result = evaluate_semantic_hard_gate(
        first_candidate,
        inventory_result=first["inventory"],
        content_plan=first["content"],
        lexical_authority=first["lexical_authority"],
        match_authority=malformed_match_authority,
    )
    assert malformed_authority_result.hard_pass is False
    assert "INVALID_SCHEMA" in hard_gate_failure_codes(
        malformed_authority_result
    )

    valid_result = _gate(first, first_candidate)
    assert not validate_semantic_hard_gate_result(
        valid_result,
        candidate=first_candidate,
        inventory_result=first["inventory"],
        content_plan=first["content"],
        lexical_authority=first["lexical_authority"],
        match_authority=first["match_authority"],
    )
    forged = replace(valid_result, hard_pass=False, selector_eligible=False)
    assert validate_hard_gate_result_structure(forged)
    assert "HARD_GATE_RESULT_RECOMPUTATION_MISMATCH" in (
        validate_semantic_hard_gate_result(
            forged,
            candidate=first_candidate,
            inventory_result=first["inventory"],
            content_plan=first["content"],
            lexical_authority=first["lexical_authority"],
            match_authority=first["match_authority"],
        )
    )
    try:
        SemanticCandidate(
            discourse_plan=first_candidate.discourse_plan,
            surface_ast=first_candidate.surface_ast,
            rendered_surface=first_candidate.rendered_surface,
            parsed_surface_witness=first_candidate.parsed_surface_witness,
            verified_surface_binding=first_candidate.verified_surface_binding,
            weighted_score=10**12,
        )
    except TypeError:
        pass
    else:
        raise AssertionError("caller score unexpectedly accepted")


def test_s9_selector_is_lexicographic_permutation_invariant_and_hard_only() -> None:
    context = _first_context("nls3s_b001_0007")
    candidates = [
        _candidate(context, index) for index in range(len(context["plans"].plans))
    ]
    assert len(candidates) == 4
    original = select_semantic_candidates(
        candidates,
        inventory_result=context["inventory"],
        content_plan=context["content"],
        lexical_authority=context["lexical_authority"],
        match_authority=context["match_authority"],
    )
    reversed_result = select_semantic_candidates(
        list(reversed(candidates)),
        inventory_result=context["inventory"],
        content_plan=context["content"],
        lexical_authority=context["lexical_authority"],
        match_authority=context["match_authority"],
    )
    assert original.decision == reversed_result.decision
    assert not validate_semantic_selection_result(
        original,
        candidates=candidates,
        inventory_result=context["inventory"],
        content_plan=context["content"],
        lexical_authority=context["lexical_authority"],
        match_authority=context["match_authority"],
    )

    expected_id = original.decision.selected_candidate_id
    gate_results = list(original.gate_results)
    rng = random.Random(20260716)
    for _ in range(101):
        rng.shuffle(gate_results)
        assert (
            selector_module._selected_candidate_id_from_results(gate_results)
            == expected_id
        )
    for ordering in permutations(original.gate_results):
        assert selector_module._selected_candidate_id_from_results(ordering) == expected_id

    try:
        select_semantic_candidates(
            [candidates[0], candidates[0]],
            inventory_result=context["inventory"],
            content_plan=context["content"],
            lexical_authority=context["lexical_authority"],
            match_authority=context["match_authority"],
        )
    except LexicographicSelectorError as exc:
        assert exc.code == "SELECTOR_DUPLICATE_CANDIDATE_ID"
    else:
        raise AssertionError("duplicate candidate ID accepted")

    bad_bytes = b"invalid"
    bad_render = replace(
        candidates[0].rendered_surface,
        utf8_bytes=bad_bytes,
        sha256=hashlib.sha256(bad_bytes).hexdigest(),
    )
    failed = _with(candidates[0], rendered_surface=bad_render)
    no_valid = select_semantic_candidates(
        [failed],
        inventory_result=context["inventory"],
        content_plan=context["content"],
        lexical_authority=context["lexical_authority"],
        match_authority=context["match_authority"],
    )
    assert no_valid.decision.status == "v3_no_valid_candidate"
    assert no_valid.decision.selected_candidate_id is None
    assert no_valid.decision.v3_success is False

    original_weighted = contract_module.SELECTOR_POLICY[
        "weighted_score_forbidden"
    ]
    try:
        contract_module.SELECTOR_POLICY["weighted_score_forbidden"] = False
        try:
            select_semantic_candidates(
                [candidates[0]],
                inventory_result=context["inventory"],
                content_plan=context["content"],
                lexical_authority=context["lexical_authority"],
                match_authority=context["match_authority"],
            )
        except LexicographicSelectorError as exc:
            assert exc.code == "SELECTOR_POLICY_DRIFT"
        else:
            raise AssertionError("selector policy drift accepted")
    finally:
        contract_module.SELECTOR_POLICY[
            "weighted_score_forbidden"
        ] = original_weighted
    _assert_historical_step9_manifest_is_noncurrent()


def test_s9_bounded_recovery_rebuild_split_and_minimal_lanes() -> None:
    context = _first_context("nls3s_b001_0007")
    plans = context["plans"].plans
    candidates = [_candidate(context, index) for index in range(len(plans))]

    good = candidates[0]
    direct = select_with_bounded_recovery(
        [good],
        inventory_result=context["inventory"],
        content_plan=context["content"],
        lexical_authority=context["lexical_authority"],
        match_authority=context["match_authority"],
    )
    assert direct.trace.final_status == "selected"
    assert direct.trace.attempts == ()
    assert direct.trace.planner_rebuild_count == 0

    generic = b"unparseable"
    broken = _with(
        good,
        rendered_surface=replace(
            good.rendered_surface,
            utf8_bytes=generic,
            sha256=hashlib.sha256(generic).hexdigest(),
        ),
    )
    rebuilt = select_with_bounded_recovery(
        [broken],
        inventory_result=context["inventory"],
        content_plan=context["content"],
        lexical_authority=context["lexical_authority"],
        match_authority=context["match_authority"],
    )
    assert rebuilt.trace.final_status == "selected"
    assert rebuilt.trace.attempts[0].lane == (
        "same_semantic_topology_safer_layout"
    )
    assert rebuilt.trace.total_candidate_count == 2

    plan_with_two_groups = next(
        plan for plan in plans if len(plan["sentence_groups"]) == 2
    )
    source_index = plans.index(plan_with_two_groups)
    source = candidates[source_index]
    untrusted_plan = deepcopy(source.discourse_plan)
    untrusted_plan["discourse_plan_id"] = "nls3dp_0000000000000000"
    split_source = _with(source, discourse_plan=untrusted_plan)
    split = select_with_bounded_recovery(
        [split_source],
        inventory_result=context["inventory"],
        content_plan=context["content"],
        lexical_authority=context["lexical_authority"],
        match_authority=context["match_authority"],
    )
    assert split.trace.final_status == "selected"
    assert any(
        attempt.lane == "safe_split" and attempt.candidate_id is not None
        for attempt in split.trace.attempts
    )

    plan_with_three_groups = next(
        plan for plan in plans if len(plan["sentence_groups"]) == 3
    )
    source_index = plans.index(plan_with_three_groups)
    source = candidates[source_index]
    untrusted_plan = deepcopy(source.discourse_plan)
    untrusted_plan["discourse_plan_id"] = "nls3dp_ffffffffffffffff"
    minimal_source = _with(source, discourse_plan=untrusted_plan)
    minimal = select_with_bounded_recovery(
        [minimal_source],
        inventory_result=context["inventory"],
        content_plan=context["content"],
        lexical_authority=context["lexical_authority"],
        match_authority=context["match_authority"],
    )
    assert minimal.trace.final_status == "selected"
    assert any(
        attempt.lane == "minimal_required_complete"
        and attempt.candidate_id is not None
        for attempt in minimal.trace.attempts
    )
    required = set(context["inventory"].ledger["required_obligation_ids"])
    selected_plan = minimal.selection.selected_candidate.discourse_plan
    selected_ids = {row["obligation_id"] for row in selected_plan["nodes"]}
    assert selected_ids == required
    assert not validate_bounded_recovery_result(
        minimal,
        initial_candidates=[minimal_source],
        inventory_result=context["inventory"],
        content_plan=context["content"],
        lexical_authority=context["lexical_authority"],
        match_authority=context["match_authority"],
    )

    forged_lexical_authority = replace(
        context["lexical_authority"],
        authority_id="lexauth_" + "0" * 24,
    )
    bounded_failures = select_with_bounded_recovery(
        candidates,
        inventory_result=context["inventory"],
        content_plan=context["content"],
        lexical_authority=forged_lexical_authority,
        match_authority=context["match_authority"],
    )
    assert sum(
        attempt.lane == "same_semantic_topology_safer_layout"
        for attempt in bounded_failures.trace.attempts
    ) <= RECOVERY_POLICY["same_semantic_topology_recovery_limit"]


def test_s9_no_valid_candidate_stays_failure_and_never_counts_v1() -> None:
    context = _first_context("nls3s_b001_0001")
    candidate = _candidate(context)
    forged_lexical_authority = replace(
        context["lexical_authority"],
        authority_id="lexauth_" + "0" * 24,
    )
    result = select_with_bounded_recovery(
        [candidate],
        inventory_result=context["inventory"],
        content_plan=context["content"],
        lexical_authority=forged_lexical_authority,
        match_authority=context["match_authority"],
    )
    assert result.trace.final_status == "v3_no_valid_candidate"
    assert result.trace.selected_candidate_id is None
    assert result.trace.v3_success is False
    assert result.trace.v1_fallback_used is False
    assert result.trace.v1_fallback_counts_as_v3_success is False
    assert result.trace.total_candidate_count <= RECOVERY_POLICY[
        "candidate_total_limit_including_initial"
    ]
    assert result.trace.planner_rebuild_count <= RECOVERY_POLICY[
        "planner_rebuild_limit"
    ]
    assert sum(
        attempt.candidate_id is not None
        and attempt.lane == "same_semantic_topology_safer_layout"
        for attempt in result.trace.attempts
    ) <= RECOVERY_POLICY["same_semantic_topology_recovery_limit"]
    assert not validate_recovery_trace_structure(result.trace)

    cyclic_plan = dict(candidate.discourse_plan)
    cyclic_plan["cycle"] = cyclic_plan
    cyclic_recovery = select_with_bounded_recovery(
        [_with(candidate, discourse_plan=cyclic_plan)],
        inventory_result=context["inventory"],
        content_plan=context["content"],
        lexical_authority=context["lexical_authority"],
        match_authority=context["match_authority"],
    )
    assert cyclic_recovery.trace.final_status in {
        "selected",
        "v3_no_valid_candidate",
    }
    assert not validate_recovery_trace_structure(cyclic_recovery.trace)

    shape_recovery = select_with_bounded_recovery(
        [_with(candidate, discourse_plan=[])],
        inventory_result=context["inventory"],
        content_plan=context["content"],
        lexical_authority=context["lexical_authority"],
        match_authority=context["match_authority"],
    )
    assert shape_recovery.trace.final_status in {
        "selected",
        "v3_no_valid_candidate",
    }
    assert not validate_recovery_trace_structure(shape_recovery.trace)

    malformed_ledger = deepcopy(context["inventory"].ledger)
    malformed_ledger["required_obligation_ids"] = [[]]
    malformed_inventory = replace(context["inventory"], ledger=malformed_ledger)
    malformed_content = deepcopy(context["content"])
    malformed_content["decisions"] = 1
    malformed_parent_recovery = select_with_bounded_recovery(
        [candidate],
        inventory_result=malformed_inventory,
        content_plan=malformed_content,
        lexical_authority=context["lexical_authority"],
        match_authority=context["match_authority"],
    )
    assert malformed_parent_recovery.trace.final_status == (
        "v3_no_valid_candidate"
    )
    assert not validate_recovery_trace_structure(
        malformed_parent_recovery.trace
    )

    try:
        select_with_bounded_recovery(
            [candidate] * 13,
            inventory_result=context["inventory"],
            content_plan=context["content"],
            lexical_authority=context["lexical_authority"],
            match_authority=context["match_authority"],
        )
    except BoundedRecoveryError as exc:
        assert exc.code == "RECOVERY_INITIAL_LIMIT_EXCEEDED"
    else:
        raise AssertionError("recovery limit bypass accepted")

    original_repair_policy = RECOVERY_POLICY["post_render_text_repair_forbidden"]
    try:
        RECOVERY_POLICY["post_render_text_repair_forbidden"] = False
        try:
            select_with_bounded_recovery(
                [candidate],
                inventory_result=context["inventory"],
                content_plan=context["content"],
                lexical_authority=context["lexical_authority"],
                match_authority=context["match_authority"],
            )
        except BoundedRecoveryError as exc:
            assert exc.code == "RECOVERY_POLICY_DRIFT"
        else:
            raise AssertionError("recovery policy drift accepted")
    finally:
        RECOVERY_POLICY[
            "post_render_text_repair_forbidden"
        ] = original_repair_policy
    _assert_historical_step9_manifest_is_noncurrent()


def test_s9_pre_question_source_context_is_not_recovered_or_selected() -> None:
    normal = _first_context("nls3s_b001_0001")
    candidate = _candidate(normal)
    current_input = normal["sample"]["input"]
    spans = build_evidence_ledger(current_input)
    resolver = build_evidence_span_resolver(spans, current_input=current_input)
    grounded = build_grounded_observation_plan(
        current_input,
        evidence_spans=spans,
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
    content = build_content_selection_plan(inventory)
    lexical_authority = open_request_lexical_authority(
        inventory,
        grounded_plan=grounded,
        resolver=resolver,
        observation_stage_context=stage,
        original_input_bundle=current_input,
        trusted_future_authority=future,
    )
    match_authority = open_independent_match_source_authority(
        inventory,
        grounded_plan=grounded,
        resolver=resolver,
        observation_stage_context=stage,
        original_input_bundle=current_input,
        trusted_future_authority=future,
    )
    result = evaluate_semantic_hard_gate(
        candidate,
        inventory_result=inventory,
        content_plan=content,
        lexical_authority=lexical_authority,
        match_authority=match_authority,
    )
    assert result.hard_pass is False
    evidence = _outcome(result, "evidence_resolution")
    assert "SOURCE_CONTEXT_NOT_BODY_RECOVERABLE" in evidence.failure_codes


def test_s9_modules_are_runtime_disconnected_and_fixture_cue_free() -> None:
    module_paths = [
        _INFERENCE_ROOT / "emlis_ai_step9_dependency_manifest_v3.py",
        _INFERENCE_ROOT / "emlis_ai_step9_artifact_contract_v3.py",
        _INFERENCE_ROOT / "emlis_ai_semantic_hard_gate_v3.py",
        _INFERENCE_ROOT / "emlis_ai_lexicographic_selector_v3.py",
        _INFERENCE_ROOT / "emlis_ai_bounded_recovery_v3.py",
        (
            _INFERENCE_ROOT
            / "emlis_ai_step9_recovery_epoch001_successor_v3.py"
        ),
    ]
    banned_imports = {
        "emlis_ai_reply_service",
        "emlis_ai_grounded_reception_candidate_plan_v2",
        "emlis_ai_grounded_reception_candidate_selector_v2",
    }
    for path in module_paths:
        source = path.read_text(encoding="utf-8")
        tree = python_ast.parse(source)
        imports: set[str] = set()
        for node in python_ast.walk(tree):
            if isinstance(node, python_ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, python_ast.ImportFrom) and node.module:
                imports.add(node.module)
        assert not imports & banned_imports
        for cue in (
            "case_id",
            "family_id",
            "batch_id",
            "expected_text",
            "expected_surface",
        ):
            assert cue not in source

    reply_source = (_INFERENCE_ROOT / "emlis_ai_reply_service.py").read_text(
        encoding="utf-8"
    )
    for path in module_paths:
        assert path.stem not in reply_source
    assert tuple(
        inspect.signature(build_semantic_candidate_set).parameters
    ) == (
        "discourse_plans",
        "inventory_result",
        "content_plan",
        "lexical_authority",
        "match_authority",
    )
    assert contract_module.RECOVERY_POLICY[
        "post_render_text_repair_forbidden"
    ] is True
    recovery_source = (
        _INFERENCE_ROOT / "emlis_ai_bounded_recovery_v3.py"
    ).read_text(encoding="utf-8")
    assert ".replace(" not in recovery_source
