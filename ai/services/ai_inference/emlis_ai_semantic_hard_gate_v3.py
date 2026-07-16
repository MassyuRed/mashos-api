# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step 9 twenty-row Semantic Hard Gate for NLS v3.

The Gate never accepts candidate-declared coverage, scores or pass status.  It
replays the frozen forward renderer and the independent body parser/matcher,
then derives every decision and selector attribute from those trusted results.
"""

from dataclasses import fields
import hashlib
from typing import Any, Iterable, Mapping, Sequence
import unicodedata

from emlis_ai_body_semantic_atom_parser_v3 import (
    FROZEN_PARSER_RULEBOOK_SHA256,
    PARSER_RULEBOOK_SHA256,
    BodySemanticAtomParseError,
    parse_body_semantic_atoms,
)
from emlis_ai_canonical_renderer_v3 import (
    CanonicalRenderedSurface,
    CanonicalSurfaceRenderError,
    RequestLexicalAuthority,
    render_canonical_surface,
)
from emlis_ai_content_selection_v3 import validate_content_selection_policy
from emlis_ai_discourse_graph_planner_v3 import build_discourse_graph_plans
from emlis_ai_independent_semantic_matcher_v3 import (
    FROZEN_MATCHER_RULEBOOK_SHA256,
    MATCHER_RULEBOOK_SHA256,
    IndependentMatchSourceAuthority,
    IndependentSemanticMatchError,
    match_parsed_surface_witness,
)
from emlis_ai_nls_v3_artifact_contract import (
    STANCE_KIND,
    artifact_sha256,
    validate_discourse_plan,
    validate_surface_ast,
)
from emlis_ai_semantic_obligation_inventory_v3 import (
    FROZEN_SOURCE_POLICY_SHA256,
    SOURCE_POLICY_SHA256,
    SemanticObligationInventoryResult,
    validate_semantic_obligation_inventory,
)
from emlis_ai_step8_artifact_contract_v3 import (
    validate_parsed_surface_witness_v2,
    validate_verified_surface_binding_v2,
)
from emlis_ai_step9_artifact_contract_v3 import (
    FROZEN_HARD_GATE_POLICY_SHA256,
    HARD_GATE_DECISION_SCHEMA,
    HARD_GATE_POLICY,
    HARD_GATE_POLICY_SHA256,
    GateOutcome,
    HardGateResult,
    SemanticCandidate,
    SelectorAttributes,
    validate_hard_gate_result_structure,
    validate_step9_policies,
)
from emlis_ai_step9_dependency_manifest_v3 import (
    FROZEN_STEP9_DEPENDENCY_MANIFEST_SHA256,
    dependency_source_file_matches,
    validate_step9_dependency_manifest,
)
from emlis_ai_surface_grammar_catalog_v3 import (
    FROZEN_SURFACE_GRAMMAR_CATALOG_SHA256,
    SURFACE_GRAMMAR_CATALOG,
    validate_surface_grammar_catalog,
)
from emlis_ai_surface_grammar_catalog_v3_step8 import (
    FROZEN_STEP8_SURFACE_GRAMMAR_CATALOG_SHA256,
    STEP8_SURFACE_GRAMMAR_CATALOG,
    STEP8_SURFACE_GRAMMAR_CATALOG_SHA256,
    validate_step8_surface_grammar_catalog,
)
from emlis_ai_typed_surface_ast_v3 import (
    build_typed_surface_ast,
    validate_typed_surface_ast,
)


_ATOM_TO_OBLIGATION_KIND = {
    "grounded_nucleus": "grounded_nucleus_notice",
    "grounded_relation": "grounded_relation_preservation",
    "unknown_boundary": "unknown_boundary_preservation",
    "significance_or_shift": "significance_or_shift",
    "intention_or_next_action": "intention_or_next_action",
    "self_denial_boundary": "self_denial_boundary",
    "bounded_counterposition": "bounded_counterposition",
    "bound_emlis_reception": STANCE_KIND,
}
_ALLOWED_AST_NODE_TYPES = frozenset(
    {
        "connector",
        "grounded_referent",
        "observation_predicate",
        "grounded_relation",
        "unknown_boundary",
        "self_denial_boundary",
        "emlis_stance",
        "modality",
    }
)
_UNSUPPORTED_CLAIM_VALUE_CODES = {
    "invented_cause": "INVENTED_CAUSE",
    "personality_claim": "PERSONALITY_CLAIM",
    "diagnosis_claim": "DIAGNOSIS_CLAIM",
    "future_guarantee": "FUTURE_GUARANTEE",
}
_TARGET_GROUP_COUNT = {"minimal": 2, "focused": 3, "layered": 4}
class SemanticHardGateError(ValueError):
    """Fail-closed Step 9 Gate error with one body-free machine code."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _safe_hash(value: Any) -> str:
    try:
        return artifact_sha256(value)
    except (AttributeError, KeyError, TypeError, ValueError, UnicodeError, RecursionError):
        return "0" * 64


def _rendered_bytes(candidate: SemanticCandidate) -> bytes:
    rendered = candidate.rendered_surface
    if type(rendered) is CanonicalRenderedSurface and type(rendered.utf8_bytes) is bytes:
        return rendered.utf8_bytes
    return b""


def _source_snapshot_hash(match_authority: Any) -> str:
    value = getattr(match_authority, "source_snapshot_sha256", None)
    if (
        type(value) is str
        and len(value) == 64
        and all(char in "0123456789abcdef" for char in value)
    ):
        return value
    return "0" * 64


def derive_semantic_candidate_id(
    candidate: SemanticCandidate,
    *,
    inventory_result: SemanticObligationInventoryResult,
) -> str:
    """Derive the full content identity; input list order is never included."""

    if type(candidate) is not SemanticCandidate:
        raise SemanticHardGateError("HARD_GATE_CANDIDATE_REQUIRED")
    ledger = (
        inventory_result.ledger
        if type(inventory_result) is SemanticObligationInventoryResult
        and type(inventory_result.ledger) is dict
        else {}
    )
    structural_signature = (
        candidate.discourse_plan.get("structural_signature")
        if type(candidate.discourse_plan) is dict
        else None
    )
    if type(structural_signature) is not str:
        structural_signature = None
    text_sha = hashlib.sha256(_rendered_bytes(candidate)).hexdigest()
    identity = {
        "obligation_ledger_sha256": _safe_hash(ledger),
        "structural_signature": structural_signature,
        "discourse_plan_sha256": _safe_hash(candidate.discourse_plan),
        "surface_ast_sha256": _safe_hash(candidate.surface_ast),
        "final_text_sha256": text_sha,
        "parsed_surface_witness_sha256": _safe_hash(
            candidate.parsed_surface_witness
        ),
        "verified_surface_binding_sha256": _safe_hash(
            candidate.verified_surface_binding
        ),
    }
    return "nls3cand_" + artifact_sha256(identity)


def build_semantic_candidate(
    discourse_plan: Mapping[str, Any],
    *,
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
    lexical_authority: RequestLexicalAuthority,
    match_authority: IndependentMatchSourceAuthority,
) -> SemanticCandidate:
    """Build one private candidate only through the frozen Step 6--8 chain."""

    surface_ast = build_typed_surface_ast(
        discourse_plan,
        inventory_result=inventory_result,
        content_plan=content_plan,
    )
    rendered = render_canonical_surface(
        surface_ast,
        discourse_plan=discourse_plan,
        content_plan=content_plan,
        inventory_result=inventory_result,
        lexical_authority=lexical_authority,
    )
    witness = parse_body_semantic_atoms(rendered.utf8_bytes)
    binding = match_parsed_surface_witness(
        witness,
        candidate_text_bytes=rendered.utf8_bytes,
        inventory_result=inventory_result,
        match_authority=match_authority,
    )
    return SemanticCandidate(
        discourse_plan=dict(discourse_plan),
        surface_ast=surface_ast,
        rendered_surface=rendered,
        parsed_surface_witness=witness,
        verified_surface_binding=binding,
    )


def _contract_issue_codes(values: Iterable[Any]) -> set[str]:
    result: set[str] = set()
    for value in values:
        code = getattr(value, "code", value)
        if type(code) is str:
            result.add(code)
    return result


def _semantic_key(
    atom: Mapping[str, Any],
    binding: Mapping[str, Any] | None,
) -> tuple[Any, ...]:
    binding = binding or {}
    return (
        atom.get("kind"),
        binding.get("obligation_id"),
        atom.get("polarity"),
        atom.get("modality"),
        atom.get("temporal_scope"),
        atom.get("referent_scope"),
        tuple(atom.get("topic_fingerprints", [])),
        atom.get("relation_type"),
        binding.get("relation_direction"),
        tuple(binding.get("target_obligation_ids", [])),
        atom.get("reception_act"),
    )


def _diagnostic_atom_order_key(atom: Mapping[str, Any]) -> tuple[Any, ...]:
    start = atom.get("utf8_byte_start")
    if type(start) is int:
        return (0, start, _safe_hash(atom))
    return (1, 0, _safe_hash(atom))


def _dict_rows(value: Any) -> list[dict[str, Any]]:
    if type(value) is not list:
        return []
    return [row for row in value if type(row) is dict]


def _string_set(value: Any) -> set[str]:
    if type(value) is not list:
        return set()
    return {item for item in value if type(item) is str}


def _budget_int(value: Any, default: int) -> int:
    return value if type(value) is int else default


def _walk_mapping(value: Any) -> Iterable[tuple[str, Any]]:
    if type(value) is dict:
        for key, item in value.items():
            yield str(key), item
            yield from _walk_mapping(item)
    elif type(value) in {list, tuple}:
        for item in value:
            yield from _walk_mapping(item)


def _selector_attributes(
    *,
    candidate_id: str,
    content_plan: Mapping[str, Any],
    discourse_plan: Mapping[str, Any],
    surface_ast: Mapping[str, Any],
    rendered: CanonicalRenderedSurface,
    witness: Mapping[str, Any],
    binding: Mapping[str, Any],
    ledger: Mapping[str, Any],
) -> SelectorAttributes:
    atoms = [row for row in witness.get("semantic_atoms", []) if type(row) is dict]
    binding_rows = [row for row in binding.get("bindings", []) if type(row) is dict]
    binding_by_atom = {
        row.get("atom_id"): row
        for row in binding_rows
        if type(row.get("atom_id")) is str
    }
    required = _string_set(ledger.get("required_obligation_ids"))
    bound_required = {
        row.get("obligation_id") for row in binding_rows
    } & required
    obligation_by_id = {
        row.get("obligation_id"): row
        for row in _dict_rows(ledger.get("obligations"))
        if type(row.get("obligation_id")) is str
    }
    required_distinctness_groups = {
        obligation_by_id[obligation_id].get("distinctness_group")
        for obligation_id in bound_required
        if obligation_id in obligation_by_id
        and type(obligation_by_id[obligation_id].get("distinctness_group")) is str
    }
    reception_targets = {
        target
        for atom in atoms
        if atom.get("kind") == "bound_emlis_reception"
        for target in binding_by_atom.get(atom.get("atom_id"), {}).get(
            "target_obligation_ids", []
        )
        if target in required
    }
    keys_by_section: dict[str, list[tuple[Any, ...]]] = {
        "observation": [],
        "reception": [],
    }
    for atom in atoms:
        section = atom.get("section_role")
        if section in keys_by_section:
            keys_by_section[section].append(
                _semantic_key(atom, binding_by_atom.get(atom.get("atom_id")))
            )
    observation_keys = set(keys_by_section["observation"])
    reception_keys = set(keys_by_section["reception"])
    replay_count = len(observation_keys & reception_keys)
    generic_referents = sum(
        atom.get("referent_scope") == "unknown"
        or not atom.get("topic_fingerprints")
        for atom in atoms
    )
    semantic_phrase_obligations = {
        clause.get("obligation_id")
        for section in surface_ast.get("sections", [])
        if type(section) is dict
        for sentence in section.get("sentences", [])
        if type(sentence) is dict
        for clause in sentence.get("clauses", [])
        if type(clause) is dict
        and any(
            type(node) is dict
            and node.get("node_type") == "grounded_referent"
            and node.get("form") == "semantic_phrase"
            for node in clause.get("nodes", [])
        )
    }
    anchors = sum(
        atom.get("source_anchor_sha256") is not None
        and binding_by_atom.get(atom.get("atom_id"), {}).get(
            "match_candidate_count"
        )
        == 1
        and binding_by_atom.get(atom.get("atom_id"), {}).get("obligation_id")
        in semantic_phrase_obligations
        for atom in atoms
        if atom.get("kind") != "bound_emlis_reception"
    )
    redundant = sum(
        len(values) - len(set(values)) for values in keys_by_section.values()
    )
    actual_groups = len(discourse_plan.get("sentence_groups", []))
    target_groups = _TARGET_GROUP_COUNT.get(content_plan.get("depth"), actual_groups)
    atom_order = {
        atom.get("atom_id"): index
        for index, atom in enumerate(
            sorted(atoms, key=lambda row: row.get("utf8_byte_start", -1))
        )
    }
    anaphora_distance = 0
    for atom in atoms:
        if atom.get("kind") != "bound_emlis_reception":
            continue
        stance_index = atom_order.get(atom.get("atom_id"), 0)
        for target in atom.get("target_atom_ids", []):
            target_index = atom_order.get(target, stance_index)
            anaphora_distance += max(0, stance_index - target_index)
    return SelectorAttributes(
        required_binding_count=len(bound_required),
        required_distinctness_group_count=len(required_distinctness_groups),
        bound_reception_target_count=len(reception_targets),
        section_semantic_replay_count=replay_count,
        generic_referent_count=generic_referents,
        unnecessary_source_anchor_count=anchors,
        redundant_atom_count=redundant,
        depth_deviation=abs(actual_groups - target_groups),
        anaphora_distance=anaphora_distance,
        candidate_id=candidate_id,
    )


def _evaluate(
    candidate: SemanticCandidate,
    *,
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
    lexical_authority: RequestLexicalAuthority,
    match_authority: IndependentMatchSourceAuthority,
) -> HardGateResult:
    if type(candidate) is not SemanticCandidate:
        raise SemanticHardGateError("HARD_GATE_CANDIDATE_REQUIRED")

    ledger = (
        inventory_result.ledger
        if type(inventory_result) is SemanticObligationInventoryResult
        and type(inventory_result.ledger) is dict
        else {}
    )
    safe_content_plan = content_plan if type(content_plan) is dict else {}
    ledger_rows = _dict_rows(ledger.get("obligations"))
    required = _string_set(ledger.get("required_obligation_ids"))
    source_snapshot = (
        inventory_result.source_snapshot
        if type(inventory_result) is SemanticObligationInventoryResult
        else None
    )
    final_bytes = _rendered_bytes(candidate)
    candidate_id = derive_semantic_candidate_id(
        candidate, inventory_result=inventory_result
    )
    parent_hashes = (
        ("content_plan", _safe_hash(content_plan)),
        (
            "dependency_manifest",
            FROZEN_STEP9_DEPENDENCY_MANIFEST_SHA256,
        ),
        ("discourse_plan", _safe_hash(candidate.discourse_plan)),
        ("obligation_ledger", _safe_hash(ledger)),
        ("parsed_surface_witness", _safe_hash(candidate.parsed_surface_witness)),
        ("source_snapshot", _source_snapshot_hash(match_authority)),
        ("surface_ast", _safe_hash(candidate.surface_ast)),
        ("verified_surface_binding", _safe_hash(candidate.verified_surface_binding)),
    )
    failures: dict[str, set[str]] = {
        row["gate_id"]: set() for row in HARD_GATE_POLICY["gates"]
    }
    not_evaluated: set[str] = set()

    def fail(gate_id: str, *codes: str) -> None:
        failures[gate_id].update(codes)

    # Gate 1: every frozen parent validator, including the Step 8 v2 owners.
    contract_codes: set[str] = set()
    parents_valid = True
    if type(inventory_result) is not SemanticObligationInventoryResult:
        contract_codes.add("INVENTORY_RESULT_TYPE_INVALID")
        parents_valid = False
    else:
        try:
            contract_codes.update(
                validate_semantic_obligation_inventory(
                    ledger,
                    source_snapshot=source_snapshot,
                )
            )
        except (
            AttributeError,
            KeyError,
            RecursionError,
            TypeError,
            ValueError,
            UnicodeError,
        ):
            contract_codes.add("INVENTORY_VALIDATION_FAILED")
    try:
        contract_codes.update(
            _contract_issue_codes(
                validate_content_selection_policy(
                    content_plan,
                    inventory_result=inventory_result,
                )
            )
        )
    except (
        AttributeError,
        KeyError,
        RecursionError,
        TypeError,
        ValueError,
        UnicodeError,
    ):
        contract_codes.add("CONTENT_VALIDATION_FAILED")
    try:
        contract_codes.update(
            _contract_issue_codes(
                validate_discourse_plan(
                    candidate.discourse_plan,
                    content_plan=content_plan,
                    obligation_ledger=ledger,
                )
            )
        )
        plans = build_discourse_graph_plans(inventory_result, content_plan)
        if candidate.discourse_plan not in plans.plans:
            contract_codes.add("DISCOURSE_PLAN_SET_MISMATCH")
    except (
        AttributeError,
        KeyError,
        RecursionError,
        TypeError,
        ValueError,
        UnicodeError,
    ):
        contract_codes.add("DISCOURSE_VALIDATION_FAILED")
    try:
        contract_codes.update(
            _contract_issue_codes(
                validate_surface_ast(
                    candidate.surface_ast,
                    discourse_plan=candidate.discourse_plan,
                    obligation_ledger=ledger,
                )
            )
        )
        contract_codes.update(
            validate_typed_surface_ast(
                candidate.surface_ast,
                discourse_plan=candidate.discourse_plan,
                inventory_result=inventory_result,
                content_plan=content_plan,
            )
        )
    except (
        AttributeError,
        KeyError,
        RecursionError,
        TypeError,
        ValueError,
        UnicodeError,
    ):
        contract_codes.add("AST_VALIDATION_FAILED")
    if type(candidate.rendered_surface) is not CanonicalRenderedSurface:
        contract_codes.add("RENDERED_SURFACE_TYPE_INVALID")
    try:
        contract_codes.update(
            _contract_issue_codes(
                validate_parsed_surface_witness_v2(
                    candidate.parsed_surface_witness,
                    candidate_text_bytes=final_bytes,
                )
            )
        )
        contract_codes.update(
            _contract_issue_codes(
                validate_verified_surface_binding_v2(
                    candidate.verified_surface_binding,
                    parsed_surface_witness=candidate.parsed_surface_witness,
                    candidate_text_bytes=final_bytes,
                    obligation_ledger=ledger,
                    ledger_authority=(
                        source_snapshot.ledger_source_authority
                        if source_snapshot is not None
                        else None
                    ),
                    source_snapshot_sha256=_source_snapshot_hash(match_authority),
                    observation_stage=getattr(match_authority, "observation_stage", ""),
                )
            )
        )
    except (
        AttributeError,
        KeyError,
        RecursionError,
        TypeError,
        ValueError,
        UnicodeError,
    ):
        contract_codes.add("STEP8_ARTIFACT_VALIDATION_FAILED")
    if contract_codes:
        parents_valid = False
        if any("HASH" in code or "PARENT" in code for code in contract_codes):
            fail("artifact_schema_parent_hash", "PARENT_HASH_MISMATCH")
        fail("artifact_schema_parent_hash", "INVALID_SCHEMA")

    # Gate 2: offline dependency closure.  Runtime manifest ownership is Step 10.
    dependencies_valid = not (
        validate_step9_policies()
        or validate_step9_dependency_manifest()
        or HARD_GATE_POLICY_SHA256 != FROZEN_HARD_GATE_POLICY_SHA256
        or validate_surface_grammar_catalog()
        or validate_step8_surface_grammar_catalog()
        or artifact_sha256(SURFACE_GRAMMAR_CATALOG)
        != FROZEN_SURFACE_GRAMMAR_CATALOG_SHA256
        or STEP8_SURFACE_GRAMMAR_CATALOG_SHA256
        != FROZEN_STEP8_SURFACE_GRAMMAR_CATALOG_SHA256
        or artifact_sha256(STEP8_SURFACE_GRAMMAR_CATALOG)
        != FROZEN_STEP8_SURFACE_GRAMMAR_CATALOG_SHA256
        or PARSER_RULEBOOK_SHA256 != FROZEN_PARSER_RULEBOOK_SHA256
        or MATCHER_RULEBOOK_SHA256 != FROZEN_MATCHER_RULEBOOK_SHA256
        or SOURCE_POLICY_SHA256 != FROZEN_SOURCE_POLICY_SHA256
    )
    if not dependencies_valid:
        fail("version_dependency_closure", "DEPENDENCY_DRIFT")

    # Gate 3: independently rebuild AST policy and exact final renderer output.
    replay_render: CanonicalRenderedSurface | None = None
    try:
        expected_ast = build_typed_surface_ast(
            candidate.discourse_plan,
            inventory_result=inventory_result,
            content_plan=content_plan,
        )
        replay_render = render_canonical_surface(
            candidate.surface_ast,
            discourse_plan=candidate.discourse_plan,
            content_plan=content_plan,
            inventory_result=inventory_result,
            lexical_authority=lexical_authority,
        )
        if expected_ast != candidate.surface_ast or replay_render != candidate.rendered_surface:
            fail("canonical_render_equality", "RENDER_TEXT_MISMATCH")
    except (
        AttributeError,
        CanonicalSurfaceRenderError,
        KeyError,
        RecursionError,
        TypeError,
        ValueError,
        UnicodeError,
    ):
        fail("canonical_render_equality", "RENDER_TEXT_MISMATCH")

    # Gate 4: bytes-only parser replay.  Supplied witness is only a comparison.
    replay_witness: dict[str, Any] | None = None
    try:
        replay_witness = parse_body_semantic_atoms(final_bytes)
        if (
            replay_witness.get("parse_status") != "parsed"
            or replay_witness != candidate.parsed_surface_witness
        ):
            fail("body_parseability", "UNPARSABLE_CONTROLLED_SURFACE")
    except (
        BodySemanticAtomParseError,
        AttributeError,
        RecursionError,
        TypeError,
        ValueError,
    ):
        fail("body_parseability", "UNPARSABLE_CONTROLLED_SURFACE")

    # Gate 5: source-bound matcher replay; no candidate ID/coverage is an input.
    replay_binding: dict[str, Any] | None = None
    if replay_witness is not None:
        try:
            replay_binding = match_parsed_surface_witness(
                replay_witness,
                candidate_text_bytes=final_bytes,
                inventory_result=inventory_result,
                match_authority=match_authority,
            )
            status = replay_binding.get("binding_status")
            if status == "ambiguous_semantic_binding":
                fail("evidence_resolution", "AMBIGUOUS_SEMANTIC_BINDING")
            elif status == "source_context_mismatch":
                fail(
                    "evidence_resolution",
                    "SOURCE_CONTEXT_NOT_BODY_RECOVERABLE",
                )
            elif status != "matched" or replay_binding != candidate.verified_surface_binding:
                fail("evidence_resolution", "NO_SEMANTIC_BINDING")
            allowed_evidence = {
                item
                for obligation in ledger_rows
                for item in obligation.get("evidence_ids", [])
                if type(item) is str
            }
            bound_evidence = {
                item
                for row in replay_binding.get("bindings", [])
                if type(row) is dict
                for item in row.get("evidence_ids", [])
                if type(item) is str
            }
            if not bound_evidence <= allowed_evidence:
                fail("evidence_resolution", "UNKNOWN_EVIDENCE_REF")
        except (
            AttributeError,
            IndependentSemanticMatchError,
            KeyError,
            RecursionError,
            TypeError,
            ValueError,
            UnicodeError,
        ):
            fail("evidence_resolution", "NO_SEMANTIC_BINDING")
    else:
        not_evaluated.add("evidence_resolution")

    semantic_ready = (
        replay_witness is not None
        and replay_witness.get("parse_status") == "parsed"
        and replay_binding is not None
        and replay_binding.get("binding_status") == "matched"
    )
    semantic_evaluable = (
        replay_witness is not None
        and replay_witness.get("parse_status") == "parsed"
        and replay_binding is not None
    )
    atoms: list[dict[str, Any]] = []
    binding_rows: list[dict[str, Any]] = []
    obligation_by_id: dict[str, dict[str, Any]] = {}
    atom_by_id: dict[str, dict[str, Any]] = {}
    binding_by_atom: dict[str, dict[str, Any]] = {}
    if semantic_evaluable:
        atoms = [
            row
            for row in replay_witness.get("semantic_atoms", [])
            if type(row) is dict
        ]
        binding_rows = [
            row for row in replay_binding.get("bindings", []) if type(row) is dict
        ]
        obligation_by_id = {
            row.get("obligation_id"): row
            for row in ledger_rows
            if type(row.get("obligation_id")) is str
        }
        atom_by_id = {
            row.get("atom_id"): row
            for row in atoms
            if type(row.get("atom_id")) is str
        }
        binding_by_atom = {
            row.get("atom_id"): row
            for row in binding_rows
            if type(row.get("atom_id")) is str
        }

    # Diagnostic comparisons may only add failures.  They never make an
    # untrusted supplied witness/binding pass; replayed artifacts above remain
    # the sole positive authority for every semantic gate.
    supplied_atom_values = (
        candidate.parsed_surface_witness.get("semantic_atoms", [])
        if type(candidate.parsed_surface_witness) is dict
        else []
    )
    supplied_atoms = (
        [row for row in supplied_atom_values if type(row) is dict]
        if type(supplied_atom_values) is list
        else []
    )
    supplied_binding_values = (
        candidate.verified_surface_binding.get("bindings", [])
        if type(candidate.verified_surface_binding) is dict
        else []
    )
    supplied_bindings = (
        [row for row in supplied_binding_values if type(row) is dict]
        if type(supplied_binding_values) is list
        else []
    )
    if replay_witness is not None and replay_witness.get("parse_status") == "parsed":
        expected_atoms = sorted(
            [
                row
                for row in replay_witness.get("semantic_atoms", [])
                if type(row) is dict
            ],
            key=_diagnostic_atom_order_key,
        )
        supplied_ordered = sorted(
            supplied_atoms,
            key=_diagnostic_atom_order_key,
        )
        if len(supplied_ordered) != len(expected_atoms):
            fail("required_obligation_coverage", "REQUIRED_OBLIGATION_MISSING")
            if sum(
                atom.get("kind") == "bound_emlis_reception"
                for atom in supplied_ordered
            ) < sum(
                atom.get("kind") == "bound_emlis_reception"
                for atom in expected_atoms
            ):
                fail("bound_emlis_reception", "UNBOUND_EMLIS_RECEPTION")
            if sum(
                atom.get("kind") == "unknown_boundary"
                for atom in supplied_ordered
            ) < sum(
                atom.get("kind") == "unknown_boundary"
                for atom in expected_atoms
            ):
                fail("unknown_boundary", "UNKNOWN_BOUNDARY_DROPPED")
        for expected_atom, supplied_atom in zip(expected_atoms, supplied_ordered):
            if supplied_atom.get("polarity") != expected_atom.get("polarity"):
                fail("polarity_modality_time", "POLARITY_INVERSION")
            if supplied_atom.get("modality") != expected_atom.get("modality"):
                fail("polarity_modality_time", "MODALITY_OVERCLAIM")
            if supplied_atom.get("temporal_scope") != expected_atom.get(
                "temporal_scope"
            ):
                fail("polarity_modality_time", "TEMPORAL_SCOPE_DRIFT")
            if supplied_atom.get("relation_type") != expected_atom.get(
                "relation_type"
            ):
                fail("relation_type_direction", "RELATION_TYPE_MISMATCH")
            if supplied_atom.get("referent_scope") != expected_atom.get(
                "referent_scope"
            ) or supplied_atom.get("topic_fingerprints") != expected_atom.get(
                "topic_fingerprints"
            ):
                fail("referent_topic_scope", "TOPIC_MIX")
            if supplied_atom.get("section_role") != expected_atom.get(
                "section_role"
            ):
                fail(
                    "observation_reception_distinctness",
                    "SECTION_SEMANTIC_REPLAY",
                )
            if supplied_atom.get("source_anchor_sha256") != expected_atom.get(
                "source_anchor_sha256"
            ):
                fail("input_enumeration_shallow_mirror", "ANCHOR_REPLAY")
            if expected_atom.get("kind") == "unknown_boundary" and (
                supplied_atom.get("kind") != "unknown_boundary"
                or supplied_atom.get("unknown_dimension_codes")
                != expected_atom.get("unknown_dimension_codes")
            ):
                fail("unknown_boundary", "UNKNOWN_BOUNDARY_DROPPED")
            expected_kind = expected_atom.get("kind")
            supplied_kind = supplied_atom.get("kind")
            if (
                expected_kind == "self_denial_boundary"
                or supplied_kind == "self_denial_boundary"
            ) and supplied_kind != expected_kind:
                fail("self_denial_boundary", "SELF_DENIAL_ADOPTED")

    if replay_binding is not None:
        expected_by_atom = {
            row.get("atom_id"): row
            for row in replay_binding.get("bindings", [])
            if type(row) is dict and type(row.get("atom_id")) is str
        }
        supplied_by_atom = {
            row.get("atom_id"): row
            for row in supplied_bindings
            if type(row.get("atom_id")) is str
        }
        expected_required_ids = required
        supplied_bound_ids = {
            row.get("obligation_id")
            for row in supplied_bindings
            if type(row.get("obligation_id")) is str
        }
        if not expected_required_ids <= supplied_bound_ids:
            fail("required_obligation_coverage", "REQUIRED_OBLIGATION_MISSING")
        if len(supplied_bound_ids) != len(supplied_bindings):
            fail(
                "contribution_distinctness",
                "DISTINCT_OBLIGATIONS_COLLAPSED",
            )
        for atom_id, expected_row in expected_by_atom.items():
            supplied_row = supplied_by_atom.get(atom_id)
            if supplied_row is None:
                continue
            if supplied_row.get("relation_direction") != expected_row.get(
                "relation_direction"
            ):
                fail(
                    "relation_type_direction",
                    "RELATION_DIRECTION_INVERSION",
                )
            if supplied_row.get("topic_scope_ids") != expected_row.get(
                "topic_scope_ids"
            ):
                fail("referent_topic_scope", "TOPIC_MIX")
            if supplied_row.get("target_obligation_ids") != expected_row.get(
                "target_obligation_ids"
            ):
                fail("bound_emlis_reception", "UNBOUND_EMLIS_RECEPTION")
            if supplied_row.get("unknown_boundary_ids") != expected_row.get(
                "unknown_boundary_ids"
            ):
                fail("unknown_boundary", "UNKNOWN_BOUNDARY_DROPPED")

    for gate_id in (
        "required_obligation_coverage",
        "bound_emlis_reception",
        "polarity_modality_time",
        "relation_type_direction",
        "referent_topic_scope",
        "unknown_boundary",
        "self_denial_boundary",
        "observation_reception_distinctness",
        "input_enumeration_shallow_mirror",
        "contribution_distinctness",
        "depth_proportionality",
    ):
        if not semantic_evaluable:
            not_evaluated.add(gate_id)

    bound_ids = {row.get("obligation_id") for row in binding_rows}

    # Gate 6: exact required set coverage from matcher replay.
    if semantic_evaluable and not required <= bound_ids:
        fail("required_obligation_coverage", "REQUIRED_OBLIGATION_MISSING")

    # Gate 7: reception stance and its non-stance targets remain independently bound.
    if semantic_evaluable:
        required_stances = [
            row
            for obligation_id, row in obligation_by_id.items()
            if obligation_id in required and row.get("kind") == STANCE_KIND
        ]
        reception_ok = bool(required_stances)
        for stance in required_stances:
            binding_row = next(
                (
                    row
                    for row in binding_rows
                    if row.get("obligation_id") == stance.get("obligation_id")
                ),
                None,
            )
            atom = atom_by_id.get(binding_row.get("atom_id")) if binding_row else None
            targets = list(stance.get("target_obligation_ids", []))
            if (
                binding_row is None
                or atom is None
                or atom.get("kind") != "bound_emlis_reception"
                or binding_row.get("target_obligation_ids") != targets
                or not targets
                or any(
                    target not in required
                    or obligation_by_id.get(target, {}).get("kind") == STANCE_KIND
                    for target in targets
                )
            ):
                reception_ok = False
        if not reception_ok:
            fail("bound_emlis_reception", "UNBOUND_EMLIS_RECEPTION")

    # Gates 8--10: replay source features independently of matcher acceptance.
    if semantic_evaluable:
        for row in binding_rows:
            atom = atom_by_id.get(row.get("atom_id"))
            obligation = obligation_by_id.get(row.get("obligation_id"))
            if atom is None or obligation is None:
                fail("referent_topic_scope", "AMBIGUOUS_REFERENT")
                continue
            if atom.get("polarity") != obligation.get("polarity"):
                fail("polarity_modality_time", "POLARITY_INVERSION")
            if atom.get("modality") != obligation.get("modality"):
                fail("polarity_modality_time", "MODALITY_OVERCLAIM")
            if atom.get("temporal_scope") != obligation.get("temporal_scope"):
                fail("polarity_modality_time", "TEMPORAL_SCOPE_DRIFT")
            if row.get("match_candidate_count") != 1:
                fail("referent_topic_scope", "AMBIGUOUS_REFERENT")
            if row.get("topic_scope_ids") != obligation.get("topic_scope_ids"):
                fail("referent_topic_scope", "TOPIC_MIX")
            if not atom.get("topic_fingerprints"):
                fail("referent_topic_scope", "AMBIGUOUS_REFERENT")
            if atom.get("kind") == "grounded_relation":
                descriptors = obligation.get("relation_directions", [])
                descriptor = next(
                    (
                        item
                        for item in descriptors
                        if type(item) is dict
                        and item.get("relation_id") == row.get("relation_id")
                    ),
                    None,
                )
                if descriptor is None or atom.get("relation_type") != descriptor.get(
                    "relation_type"
                ):
                    fail("relation_type_direction", "RELATION_TYPE_MISMATCH")
                if descriptor is None or row.get("relation_direction") != descriptor.get(
                    "direction"
                ):
                    fail(
                        "relation_type_direction",
                        "RELATION_DIRECTION_INVERSION",
                    )

    # Gate 11: every required unknown remains a typed, exact unknown atom.
    if semantic_evaluable:
        for obligation_id in required:
            obligation = obligation_by_id.get(obligation_id, {})
            if obligation.get("kind") != "unknown_boundary_preservation":
                continue
            row = next(
                (
                    item
                    for item in binding_rows
                    if item.get("obligation_id") == obligation_id
                ),
                None,
            )
            atom = atom_by_id.get(row.get("atom_id")) if row else None
            if (
                row is None
                or atom is None
                or atom.get("kind") != "unknown_boundary"
                or row.get("unknown_boundary_ids")
                != obligation.get("unknown_boundary_ids")
                or not atom.get("unknown_dimension_codes")
            ):
                fail("unknown_boundary", "UNKNOWN_BOUNDARY_DROPPED")

    # Gate 12: controlled self-denial/bounded counterposition forms only.
    if semantic_evaluable:
        safety_kinds = {"self_denial_boundary", "bounded_counterposition"}
        for obligation_id in required:
            obligation = obligation_by_id.get(obligation_id, {})
            if obligation.get("kind") not in safety_kinds:
                continue
            row = next(
                (
                    item
                    for item in binding_rows
                    if item.get("obligation_id") == obligation_id
                ),
                None,
            )
            atom = atom_by_id.get(row.get("atom_id")) if row else None
            expected_atom_kind = {
                "self_denial_boundary": "self_denial_boundary",
                "bounded_counterposition": "bounded_counterposition",
            }[obligation.get("kind")]
            if atom is None or atom.get("kind") != expected_atom_kind:
                fail("self_denial_boundary", "SELF_DENIAL_ADOPTED")
            elif atom.get("polarity") != obligation.get("polarity"):
                fail("self_denial_boundary", "SELF_DENIAL_AMPLIFIED")

    # Gate 13: closed atom/AST claim vocabulary, even when another gate also fails.
    unsupported = False
    if type(candidate.surface_ast) is dict:
        try:
            for key, value in _walk_mapping(candidate.surface_ast):
                if type(value) is str and value in _UNSUPPORTED_CLAIM_VALUE_CODES:
                    unsupported = True
                    fail(
                        "unsupported_claim",
                        _UNSUPPORTED_CLAIM_VALUE_CODES[value],
                    )
                if key == "node_type" and (
                    type(value) is not str or value not in _ALLOWED_AST_NODE_TYPES
                ):
                    unsupported = True
        except RecursionError:
            unsupported = True
    else:
        unsupported = True
    if semantic_evaluable:
        for atom in atoms:
            row = binding_by_atom.get(atom.get("atom_id"))
            obligation = obligation_by_id.get(row.get("obligation_id")) if row else None
            if (
                obligation is None
                or _ATOM_TO_OBLIGATION_KIND.get(atom.get("kind"))
                != obligation.get("kind")
            ):
                unsupported = True
    elif failures["body_parseability"]:
        unsupported = True
    if unsupported:
        fail("unsupported_claim", "UNSUPPORTED_CLAIM")

    # Gate 14: section role contributes a distinct stance, not a replayed claim.
    if semantic_evaluable:
        keys_by_section: dict[str, set[tuple[Any, ...]]] = {
            "observation": set(),
            "reception": set(),
        }
        for atom in atoms:
            section = atom.get("section_role")
            if section in keys_by_section:
                keys_by_section[section].add(
                    _semantic_key(atom, binding_by_atom.get(atom.get("atom_id")))
                )
        if keys_by_section["observation"] & keys_by_section["reception"]:
            fail(
                "observation_reception_distinctness",
                "SECTION_SEMANTIC_REPLAY",
            )
        if any(
            atom.get("section_role") == "reception"
            and atom.get("kind") != "bound_emlis_reception"
            for atom in atoms
        ):
            fail(
                "observation_reception_distinctness",
                "SECTION_SEMANTIC_REPLAY",
            )

    # Gate 15: parser-derived anchor and semantic-key repetition only.
    if semantic_evaluable:
        anchors = [
            atom.get("source_anchor_sha256")
            for atom in atoms
            if atom.get("kind") != "bound_emlis_reception"
            and atom.get("source_anchor_sha256") is not None
        ]
        if len(anchors) != len(set(anchors)) or len(anchors) > 1:
            fail("input_enumeration_shallow_mirror", "ANCHOR_REPLAY")
        if replay_render is not None and replay_render.raw_anchor_count != len(anchors):
            fail("input_enumeration_shallow_mirror", "ANCHOR_REPLAY")
        observation_keys = [
            _semantic_key(atom, binding_by_atom.get(atom.get("atom_id")))
            for atom in atoms
            if atom.get("section_role") == "observation"
        ]
        if len(observation_keys) != len(set(observation_keys)):
            fail("input_enumeration_shallow_mirror", "INPUT_ENUMERATION")

    # Gate 16: required and must-not-merge contributions remain separate.
    if semantic_evaluable:
        obligation_to_atom = {
            row.get("obligation_id"): row.get("atom_id") for row in binding_rows
        }
        if len({obligation_to_atom.get(item) for item in required}) != len(required):
            fail(
                "contribution_distinctness",
                "DISTINCT_OBLIGATIONS_COLLAPSED",
            )
        for obligation_id in required:
            row = obligation_by_id.get(obligation_id, {})
            for other in _string_set(row.get("must_not_merge_with")):
                if (
                    other in required
                    and obligation_to_atom.get(obligation_id)
                    == obligation_to_atom.get(other)
                ):
                    fail(
                        "contribution_distinctness",
                        "DISTINCT_OBLIGATIONS_COLLAPSED",
                    )

    # Gate 17: exact active set and validated sentence budget.
    if semantic_evaluable:
        decisions = _dict_rows(safe_content_plan.get("decisions"))
        active = {
            row.get("obligation_id")
            for row in decisions
            if type(row.get("obligation_id")) is str
            and row.get("status") in ("selected", "integrated_into")
        }
        if not active <= bound_ids:
            fail("depth_proportionality", "DEPTH_TRUNCATED")
        if not bound_ids <= active:
            fail("depth_proportionality", "DEPTH_INFLATED")
        groups = (
            candidate.discourse_plan.get("sentence_groups", [])
            if type(candidate.discourse_plan) is dict
            else []
        )
        if type(groups) is not list:
            groups = []
        counts = {
            role: sum(
                type(group) is dict and group.get("section_role") == role
                for group in groups
            )
            for role in ("observation", "reception")
        }
        budget = safe_content_plan.get("section_budget", {})
        if type(budget) is not dict:
            budget = {}
        observation_min = _budget_int(
            budget.get("observation_sentence_min"), 0
        )
        reception_min = _budget_int(
            budget.get("reception_sentence_min"), 0
        )
        observation_max = _budget_int(
            budget.get("observation_sentence_max"), -1
        )
        reception_max = _budget_int(
            budget.get("reception_sentence_max"), -1
        )
        total_max = _budget_int(budget.get("total_sentence_max"), -1)
        if (
            counts["observation"] < observation_min
            or counts["reception"] < reception_min
        ):
            fail("depth_proportionality", "DEPTH_TRUNCATED")
        if (
            counts["observation"] > observation_max
            or counts["reception"] > reception_max
            or len(groups) > total_max
        ):
            fail("depth_proportionality", "DEPTH_INFLATED")

    # Gate 18: canonical UTF-8, labels, spans and fragment uniqueness.
    try:
        text = final_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        text = ""
        fail("surface_integrity", "BROKEN_GRAMMAR")
    document = SURFACE_GRAMMAR_CATALOG["document"]
    if text and (unicodedata.normalize("NFC", text) != text or "\r" in text):
        fail("surface_integrity", "BROKEN_GRAMMAR")
    expected_prefix = document["observation_label"] + "\n"
    expected_separator = document["section_separator"] + document["reception_label"] + "\n"
    if (
        not text.startswith(expected_prefix)
        or text.count(document["observation_label"]) != 1
        or text.count(document["reception_label"]) != 1
        or expected_separator not in text
    ):
        fail("surface_integrity", "LABEL_ORDER_INVALID")
    if semantic_evaluable:
        spans = [
            (atom.get("utf8_byte_start"), atom.get("utf8_byte_end"))
            for atom in atoms
        ]
        if spans != sorted(spans) or any(
            left[1] > right[0] for left, right in zip(spans, spans[1:])
        ):
            fail("surface_integrity", "BROKEN_GRAMMAR")
        span_keys = [
            (atom.get("kind"), atom.get("span_sha256")) for atom in atoms
        ]
        if len(span_keys) != len(set(span_keys)):
            fail("surface_integrity", "DUPLICATE_FRAGMENT")

    # Gate 19: current Step 9 has no address node; do not guess names by regex.
    forbidden_address_keys = {
        "username",
        "user_name",
        "address_target",
        "honorific",
        "greeting",
    }
    try:
        ast_keys = {key for key, _value in _walk_mapping(candidate.surface_ast)}
    except RecursionError:
        ast_keys = forbidden_address_keys
    if ast_keys & forbidden_address_keys:
        fail("naming_address_contract", "USER_NAME_INVENTED")
    if not text.startswith(expected_prefix):
        fail("naming_address_contract", "ADDRESS_RETARGETED")

    # Gate 20: Step 9 remains private/runtime-disconnected and exports hashes only.
    if (
        type(candidate.parsed_surface_witness) is not dict
        or candidate.parsed_surface_witness.get("body_free_export_allowed") is not False
        or type(candidate.verified_surface_binding) is not dict
        or candidate.verified_surface_binding.get("body_free_export_allowed") is not False
        or type(candidate.surface_ast) is not dict
        or candidate.surface_ast.get("body_free") is not True
        or type(candidate.discourse_plan) is not dict
        or candidate.discourse_plan.get("body_free") is not True
    ):
        fail("body_free_public_contract", "RAW_BODY_LEAK")
    if not dependency_source_file_matches("emlis_ai_reply_service.py"):
        fail("body_free_public_contract", "PUBLIC_CONTRACT_DIFF")

    if not parents_valid:
        # Rows whose trusted source parents cannot be established are explicit,
        # never silently passed.  Gate 2, 13, 18--20 remain independently useful.
        for gate_id in (
            "canonical_render_equality",
            "body_parseability",
        ):
            if not failures[gate_id]:
                not_evaluated.add(gate_id)

    outcomes: list[GateOutcome] = []
    for row in HARD_GATE_POLICY["gates"]:
        gate_id = row["gate_id"]
        gate_failures = tuple(sorted(failures[gate_id]))
        if gate_failures:
            status = "failed"
        elif gate_id in not_evaluated:
            status = "not_evaluated"
        else:
            status = "passed"
        outcomes.append(
            GateOutcome(
                ordinal=row["ordinal"],
                gate_id=gate_id,
                status=status,
                failure_codes=gate_failures,
            )
        )

    hard_pass = all(row.status == "passed" for row in outcomes)
    attributes: SelectorAttributes | None = None
    if hard_pass and semantic_ready and replay_render is not None:
        attributes = _selector_attributes(
            candidate_id=candidate_id,
            content_plan=content_plan,
            discourse_plan=candidate.discourse_plan,
            surface_ast=candidate.surface_ast,
            rendered=replay_render,
            witness=replay_witness,
            binding=replay_binding,
            ledger=ledger,
        )
    result = HardGateResult(
        schema_version=HARD_GATE_DECISION_SCHEMA,
        candidate_id=candidate_id,
        candidate_text_sha256=hashlib.sha256(final_bytes).hexdigest(),
        parent_hashes=parent_hashes,
        gate_policy_sha256=FROZEN_HARD_GATE_POLICY_SHA256,
        outcomes=tuple(outcomes),
        hard_pass=hard_pass,
        selector_eligible=hard_pass,
        selector_attributes=attributes,
        body_free=True,
    )
    return result


def evaluate_semantic_hard_gate(
    candidate: SemanticCandidate,
    *,
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
    lexical_authority: RequestLexicalAuthority,
    match_authority: IndependentMatchSourceAuthority,
) -> HardGateResult:
    result = _evaluate(
        candidate,
        inventory_result=inventory_result,
        content_plan=content_plan,
        lexical_authority=lexical_authority,
        match_authority=match_authority,
    )
    structural_issues = validate_hard_gate_result_structure(result)
    if structural_issues:
        raise SemanticHardGateError("HARD_GATE_RESULT_CONTRACT_REJECTED")
    return result


def validate_semantic_hard_gate_result(
    value: Any,
    *,
    candidate: SemanticCandidate,
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
    lexical_authority: RequestLexicalAuthority,
    match_authority: IndependentMatchSourceAuthority,
) -> tuple[str, ...]:
    """Recompute all twenty rows and reject any self-declared pass/score."""

    try:
        structural = validate_hard_gate_result_structure(value)
        expected = _evaluate(
            candidate,
            inventory_result=inventory_result,
            content_plan=content_plan,
            lexical_authority=lexical_authority,
            match_authority=match_authority,
        )
    except (
        AttributeError,
        KeyError,
        SemanticHardGateError,
        TypeError,
        ValueError,
        UnicodeError,
        RecursionError,
    ):
        return ("HARD_GATE_REVALIDATION_FAILED",)
    issues = set(structural)
    if value != expected:
        issues.add("HARD_GATE_RESULT_RECOMPUTATION_MISMATCH")
    return tuple(sorted(issues))


def hard_gate_failure_codes(value: HardGateResult) -> tuple[str, ...]:
    if type(value) is not HardGateResult:
        raise SemanticHardGateError("HARD_GATE_RESULT_REQUIRED")
    return tuple(
        sorted(
            {
                code
                for outcome in value.outcomes
                for code in outcome.failure_codes
            }
        )
    )


def hard_gate_dataclass_fields() -> tuple[str, ...]:
    """Test-facing closed field inventory; no score/coverage claim can appear."""

    return tuple(field.name for field in fields(SemanticCandidate))


__all__ = [
    "SemanticHardGateError",
    "build_semantic_candidate",
    "derive_semantic_candidate_id",
    "evaluate_semantic_hard_gate",
    "hard_gate_dataclass_fields",
    "hard_gate_failure_codes",
    "validate_semantic_hard_gate_result",
]
