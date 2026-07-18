# -*- coding: utf-8 -*-
from __future__ import annotations

"""Forward-aware hard gate and deterministic selector for Step 11 rc0023.

The body parser and semantic matcher remain inverse-only owners.  This module
is the trust boundary that joins their result to the exact forward candidate
type and fully recomputes the forward AST, canonical rendering, parent hashes,
and candidate identity before any bytes can become selectable.
"""

import hashlib
import re
from typing import Any, Mapping, Sequence

from emlis_ai_content_selection_v3 import (
    derive_content_depth,
    validate_content_selection_policy,
)
from emlis_ai_nls_v3_artifact_contract import (
    STANCE_KIND,
    artifact_sha256,
    validate_discourse_plan,
)
from emlis_ai_semantic_obligation_inventory_v3 import (
    SemanticObligationInventoryResult,
)
from emlis_ai_step11_natural_surface_matcher_v3 import (
    STEP11_HARD_GATE_SCHEMA,
    STEP11_PARSED_WITNESS_SCHEMA,
    STEP11_SELECTION_SCHEMA,
    STEP11_VERIFIED_BINDING_SCHEMA,
    Step11GateOutcome,
    Step11HardGateResult,
    Step11InverseSurfaceError,
    Step11ParsedSurfaceWitness,
    Step11SelectionResult,
    Step11VerifiedSurfaceBinding,
    _binding_material,
    _witness_material,
    match_step11_natural_surface,
    parse_step11_natural_surface,
)
from emlis_ai_step11_natural_surface_v3 import (
    STEP11_CANDIDATE_SCHEMA,
    STEP11_CANDIDATE_VERSION_ID,
    STEP11_RENDERED_SURFACE_SCHEMA,
    STEP11_SURFACE_AST_SCHEMA,
    Step11CanonicalRenderedSurface,
    Step11NaturalSurfaceCandidate,
    Step11NaturalSurfaceAst,
    project_step11_current_input,
    render_step11_natural_surface,
    step11_surface_ast_material,
    validate_step11_natural_surface_candidate,
)
from emlis_ai_step11_semantic_overlay_v3 import (
    build_step11_semantic_overlay,
    step11_semantic_overlay_material,
)
from emlis_ai_step11_surface_catalog_v3 import (
    STEP11_SURFACE_CATALOG,
    STEP11_SURFACE_CATALOG_SHA256,
    validate_step11_surface_catalog,
)


_GATE_CODES = (
    ("artifact_schema_parent_hash", "S11_GATE01_ARTIFACT_SCHEMA_PARENT_HASH"),
    ("version_dependency", "S11_GATE02_VERSION_DEPENDENCY"),
    ("canonical_render_equality", "S11_GATE03_CANONICAL_RENDER_EQUALITY"),
    ("body_parseability", "S11_GATE04_BODY_PARSEABILITY"),
    ("evidence_resolution", "S11_GATE05_EVIDENCE_RESOLUTION"),
    ("required_obligation_coverage", "S11_GATE06_REQUIRED_OBLIGATION_COVERAGE"),
    ("bound_reception", "S11_GATE07_BOUND_RECEPTION"),
    ("polarity_modality_time", "S11_GATE08_POLARITY_MODALITY_TIME"),
    ("relation_type_direction", "S11_GATE09_RELATION_TYPE_DIRECTION"),
    ("referent_topic", "S11_GATE10_REFERENT_TOPIC"),
    ("unknown_boundary", "S11_GATE11_UNKNOWN_BOUNDARY"),
    ("self_denial", "S11_GATE12_SELF_DENIAL"),
    ("unsupported_claim", "S11_GATE13_UNSUPPORTED_CLAIM"),
    ("section_distinctness", "S11_GATE14_SECTION_DISTINCTNESS"),
    ("input_enumeration", "S11_GATE15_INPUT_ENUMERATION"),
    ("contribution_distinctness", "S11_GATE16_CONTRIBUTION_DISTINCTNESS"),
    ("depth", "S11_GATE17_DEPTH"),
    ("surface_integrity", "S11_GATE18_SURFACE_INTEGRITY"),
    ("naming_address", "S11_GATE19_NAMING_ADDRESS"),
    ("body_free_public_contract", "S11_GATE20_BODY_FREE_PUBLIC_CONTRACT"),
)

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_EVIDENCE_BINDING_ISSUES = frozenset(
    {
        "S11_MATCH_FRAGMENT_NOT_SOURCE_BACKED",
        "S11_MATCH_LABEL_ANCHOR_CONTRACT_MISMATCH",
        "S11_MATCH_NUCLEUS_BINDING_CONTRACT_MISMATCH",
        "S11_MATCH_SOURCE_ANCHOR_CONTRACT_MISMATCH",
    }
)
_UNSUPPORTED_EXACT_ISSUES = frozenset(
    {
        "S11_MATCH_DUPLICATE_SEMANTIC_ATOM",
        "S11_MATCH_PREDICATE_ROLE_MISMATCH",
        "S11_MATCH_SEMANTIC_SUBSUMPTION",
        "S11_MATCH_SURPLUS_SEMANTIC_ATOM",
    }
)

# Gate 17 owns an independent copy of the frozen Step 5 depth lattice.  It
# intentionally does not derive a looser ceiling from the number of bindings:
# a large obligation set must still be realised through the sentence groups
# selected by the body-free Content Plan and Discourse Plan.
_DEPTH_BUDGET_ROWS = (
    ("minimal", 1, 1, 1, 1, 2),
    ("focused", 1, 2, 1, 2, 4),
    ("layered", 2, 3, 1, 2, 5),
)
_DEPTH_BUDGET_KEYS = (
    "observation_sentence_min",
    "observation_sentence_max",
    "reception_sentence_min",
    "reception_sentence_max",
    "total_sentence_max",
)


def _forward_candidate_issues(
    candidate: Any,
    *,
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
    current_input: Mapping[str, Any],
) -> tuple[str, ...]:
    if type(candidate) is not Step11NaturalSurfaceCandidate:
        return ("STEP11_CANDIDATE_TYPE_INVALID",)
    try:
        return validate_step11_natural_surface_candidate(
            candidate,
            inventory_result=inventory_result,
            content_plan=content_plan,
            current_input=current_input,
        )
    except (
        AttributeError,
        KeyError,
        RecursionError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        return ("STEP11_CANDIDATE_REVALIDATION_FAILED",)


def _valid_nonzero_sha256(value: Any) -> bool:
    return type(value) is str and bool(set(value) - {"0"}) and bool(
        _SHA256_RE.fullmatch(value)
    )


def _artifact_schema_parent_hash_green(
    candidate: Step11NaturalSurfaceCandidate,
    *,
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
    current_input: Mapping[str, Any],
    semantic_overlay: Any,
    forward_issues: Sequence[str],
) -> bool:
    ast = candidate.surface_ast
    rendered = candidate.rendered_surface
    if (
        candidate.schema_version != STEP11_CANDIDATE_SCHEMA
        or type(candidate.discourse_plan) is not dict
        or type(ast) is not Step11NaturalSurfaceAst
        or ast.schema_version != STEP11_SURFACE_AST_SCHEMA
        or type(rendered) is not Step11CanonicalRenderedSurface
        or rendered.schema_version != STEP11_RENDERED_SURFACE_SCHEMA
        or type(rendered.utf8_bytes) is not bytes
        or rendered.sha256
        != hashlib.sha256(rendered.utf8_bytes).hexdigest()
        or rendered.source_surface_ast_sha256
        != artifact_sha256(step11_surface_ast_material(ast))
        or ast.surface_catalog_sha256 != STEP11_SURFACE_CATALOG_SHA256
        or rendered.surface_catalog_sha256
        != STEP11_SURFACE_CATALOG_SHA256
        or ast.source_obligation_ledger_sha256
        != artifact_sha256(inventory_result.ledger)
        or ast.source_content_plan_sha256 != artifact_sha256(content_plan)
        or ast.source_discourse_plan_sha256
        != artifact_sha256(candidate.discourse_plan)
        or semantic_overlay is None
        or ast.source_semantic_overlay_sha256
        != artifact_sha256(
            step11_semantic_overlay_material(semantic_overlay)
        )
    ):
        return False
    try:
        projection = project_step11_current_input(current_input)
    except (KeyError, TypeError, UnicodeError, ValueError):
        return False
    if candidate.current_input_projection != projection:
        return False
    artifact_issue_markers = (
        "_SCHEMA_INVALID",
        "_PARENT_MISMATCH",
        "_ID_INVALID",
        "_ID_MISMATCH",
        "_BYTES_INVALID",
        "_INPUT_PROJECTION_MISMATCH",
    )
    return not any(
        any(marker in code for marker in artifact_issue_markers)
        for code in forward_issues
    )


def _required_coverage_green(
    binding: Step11VerifiedSurfaceBinding,
    *,
    semantic_overlay: Any,
    content_plan: Mapping[str, Any],
    binding_issues: set[str],
) -> bool:
    required_ids = content_plan.get("required_coverage_obligation_ids")
    if type(required_ids) is not list or any(
        type(item) is not str or not item for item in required_ids
    ):
        return False
    required = tuple(required_ids)
    binding_row_ids = tuple(row.obligation_id for row in binding.binding_rows)
    mixed_ids = tuple(
        sorted(
            row.requirement_id
            for row in semantic_overlay.mixed_emotion_requirements
        )
    )
    return bool(
        len(required) == len(set(required))
        and binding.required_obligation_ids == required
        and binding_row_ids == required
        and len(binding_row_ids) == len(set(binding_row_ids))
        and all(
            row.atom_ids and len(row.atom_ids) == len(set(row.atom_ids))
            for row in binding.binding_rows
        )
        and binding.integrated_mixed_emotion_requirement_ids == mixed_ids
        and not any(
            code.startswith("S11_MATCH_REQUIRED_")
            or code.startswith("S11_MATCH_MIXED_EMOTION_")
            for code in binding_issues
        )
    )


def _reception_binding_green(
    witness: Step11ParsedSurfaceWitness,
    binding: Step11VerifiedSurfaceBinding,
    *,
    semantic_overlay: Any,
    binding_issues: set[str],
) -> bool:
    expected_ids = tuple(
        sorted(
            row.binding_id
            for row in semantic_overlay.reception_antecedent_bindings
        )
    )
    expected_obligation_ids = {
        row.reception_obligation_id
        for row in semantic_overlay.reception_antecedent_bindings
    }
    reception_rows = tuple(
        row
        for row in binding.binding_rows
        if row.obligation_kind == STANCE_KIND
    )
    reception_atoms = tuple(
        row for row in witness.atoms if row.section_role == "reception"
    )
    reception_atom_ids = {row.atom_id for row in reception_atoms}
    return bool(
        expected_ids
        and binding.integrated_reception_binding_ids == expected_ids
        and {row.obligation_id for row in reception_rows}
        == expected_obligation_ids
        and all(
            len(row.atom_ids) == 1
            and row.atom_ids[0] in reception_atom_ids
            and row.match_basis
            == "bound_reception_typed_referent_exact_source_owner"
            for row in reception_rows
        )
        and {row.atom_ids[0] for row in reception_rows}
        == reception_atom_ids
        and all(
            row.form_id.startswith("reception:typed:")
            and row.claim_kinds == ("bound_reception",)
            and row.source_fragments == ()
            and row.reception_antecedent_references
            and len(row.reception_antecedent_references)
            == len(
                {
                    reference.reference_ordinal
                    for reference in row.reception_antecedent_references
                }
            )
            for row in reception_atoms
        )
        and not any(
            code.startswith("S11_MATCH_RECEPTION_")
            for code in binding_issues
        )
    )


def _relation_binding_green(
    witness: Step11ParsedSurfaceWitness,
    binding: Step11VerifiedSurfaceBinding,
    *,
    semantic_overlay: Any,
    binding_issues: set[str],
) -> bool:
    anchor_by_id = {row.anchor_id: row for row in semantic_overlay.anchors}
    label_by_id = {
        row.label_anchor_id: row for row in semantic_overlay.label_anchors
    }

    def endpoint_values(
        anchor_ids: Sequence[str], label_anchor_ids: Sequence[str]
    ) -> tuple[str, ...]:
        return tuple(
            [
                anchor_by_id[anchor_id].text
                for anchor_id in anchor_ids
                if anchor_id in anchor_by_id
            ]
            + [
                label_by_id[anchor_id].label
                for anchor_id in label_anchor_ids
                if anchor_id in label_by_id
            ]
        )

    expected_source_ids = tuple(
        sorted(
            {
                source_id
                for relation in semantic_overlay.relations
                for source_id in relation.source_relation_ids
            }
        )
    )

    def introduction_reference(
        atom: Any,
        literal: str,
        endpoint_role: str,
    ) -> Any:
        if (
            atom.claim_kinds == ("nucleus_notice",)
            and atom.source_fragments == (literal,)
            and atom.introduced_reference is not None
            and atom.introduced_reference.endpoint_role == endpoint_role
        ):
            return atom.introduced_reference
        if (
            atom.claim_kinds
            == ("nucleus_notice", "mixed_emotion_relation")
            and len(atom.source_fragments)
            == len(atom.compound_label_references)
        ):
            matches = tuple(
                reference
                for fragment, reference in zip(
                    atom.source_fragments,
                    atom.compound_label_references,
                )
                if fragment == literal
                and reference.endpoint_role == endpoint_role
            )
            return matches[0] if len(matches) == 1 else None
        return None

    owned_atom_ids: list[str] = []
    for relation in semantic_overlay.relations:
        left = endpoint_values(
            relation.from_source_anchor_ids,
            relation.from_label_anchor_ids,
        )
        right = endpoint_values(
            relation.to_source_anchor_ids,
            relation.to_label_anchor_ids,
        )
        if len(left) != 1 or len(right) != 1:
            return False
        left_introductions = tuple(
            (atom, introduction_reference(
                atom, left[0], relation.from_endpoint_role
            ))
            for atom in witness.atoms
            if atom.section_role == "observation"
            and introduction_reference(
                atom, left[0], relation.from_endpoint_role
            ) is not None
        )
        right_introductions = tuple(
            (atom, introduction_reference(
                atom, right[0], relation.to_endpoint_role
            ))
            for atom in witness.atoms
            if atom.section_role == "observation"
            and introduction_reference(
                atom, right[0], relation.to_endpoint_role
            ) is not None
        )
        if len(left_introductions) != 1 or len(right_introductions) != 1:
            return False
        expected_references = (
            left_introductions[0][1],
            right_introductions[0][1],
        )
        if (
            expected_references[0] is None
            or expected_references[1] is None
            or expected_references[0].reference_ordinal
            == expected_references[1].reference_ordinal
        ):
            return False
        roles = (
            relation.from_endpoint_role,
            relation.to_endpoint_role,
        )
        prefix = (
            f"relation:{relation.relation_type}:"
            f"{relation.relation_direction}:{roles[0]}:{roles[1]}:"
        )
        matches = tuple(
            atom
            for atom in witness.atoms
            if atom.section_role == "observation"
            and atom.form_id.startswith(prefix)
            and atom.claim_kinds == ("relation_notice",)
            and atom.source_fragments == ()
            and atom.introduced_reference is None
            and atom.relation_endpoint_references == expected_references
            and atom.relation_type == relation.relation_type
            and atom.relation_direction == relation.relation_direction
            and atom.relation_endpoint_roles == roles
        )
        if len(matches) != 1:
            return False
        owned_atom_ids.append(matches[0].atom_id)
    return bool(
        binding.integrated_relation_ids == expected_source_ids
        and len(owned_atom_ids) == len(set(owned_atom_ids))
        and not any(
            code.startswith("S11_MATCH_RELATION_")
            for code in binding_issues
        )
    )


def _unknown_oracle_green(
    binding: Step11VerifiedSurfaceBinding,
    *,
    semantic_overlay: Any,
    binding_issues: set[str],
) -> bool:
    expected_unknown_ids = tuple(
        sorted(row.unknown_id for row in semantic_overlay.unknowns)
    )
    return bool(
        _valid_nonzero_sha256(binding.source_unknown_oracle_sha256)
        and binding.integrated_unknown_ids == expected_unknown_ids
        and not binding_issues
        & {
            "S11_MATCH_REQUIRED_UNKNOWN_UNCLASSIFIABLE",
            "S11_MATCH_SOURCE_UNKNOWN_ORACLE_MISMATCH",
        }
        and not any(
            code.startswith("S11_MATCH_UNKNOWN_")
            for code in binding_issues
        )
    )


def _expected_depth_budget(depth: Any) -> dict[str, int] | None:
    for row in _DEPTH_BUDGET_ROWS:
        if row[0] == depth:
            return dict(zip(_DEPTH_BUDGET_KEYS, row[1:]))
    return None


def _final_section_line_counts(body: Any) -> tuple[int, int] | None:
    """Count canonical rendered sentences without trusting AST metadata."""

    if type(body) is not bytes:
        return None
    try:
        text = body.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return None
    labels = STEP11_SURFACE_CATALOG.get("labels")
    layout = STEP11_SURFACE_CATALOG.get("layout")
    if type(labels) is not dict or type(layout) is not dict:
        return None
    observation_label = labels.get("observation")
    reception_label = labels.get("reception")
    sentence_separator = layout.get("sentence_separator")
    section_separator = layout.get("section_separator")
    if (
        type(observation_label) is not str
        or not observation_label
        or type(reception_label) is not str
        or not reception_label
        or sentence_separator != "\n"
        or section_separator != "\n\n"
    ):
        return None
    prefix = f"{observation_label}\n"
    separator = f"\n\n{reception_label}\n"
    if (
        not text.startswith(prefix)
        or text.count(separator) != 1
        or text.endswith("\n")
        or "\r" in text
    ):
        return None
    observation_text, reception_text = text[len(prefix) :].split(separator)
    observation_lines = observation_text.split("\n")
    reception_lines = reception_text.split("\n")
    if (
        not observation_lines
        or not reception_lines
        or any(not line for line in (*observation_lines, *reception_lines))
    ):
        return None
    return len(observation_lines), len(reception_lines)


def _outside_quote_joiner_count(line: str, joiner: str) -> int:
    pairs = tuple(
        (str(row["open"]), str(row["close"]))
        for row in STEP11_SURFACE_CATALOG["layout"]["quote_pairs"]
    )
    active_close: str | None = None
    escaped = False
    index = 0
    count = 0
    while index < len(line):
        if escaped:
            escaped = False
            index += 1
            continue
        if line[index] == "\\":
            escaped = True
            index += 1
            continue
        if active_close is not None:
            if line.startswith(active_close, index):
                index += len(active_close)
                active_close = None
            else:
                index += 1
            continue
        opening = next(
            (row for row in pairs if line.startswith(row[0], index)),
            None,
        )
        if opening is not None:
            active_close = opening[1]
            index += len(opening[0])
            continue
        if line.startswith(joiner, index):
            count += 1
            index += len(joiner)
            continue
        index += 1
    return count if active_close is None and not escaped else 10**6


def _surface_density_metrics(
    body: Any,
    witness: Step11ParsedSurfaceWitness | None,
) -> tuple[int, int, int]:
    """Independently derive group, grammatical, and joiner density."""

    if type(body) is not bytes or witness is None or not witness.sentences:
        return (999, 999, 999)
    try:
        text = body.decode("utf-8", errors="strict")
        labels = STEP11_SURFACE_CATALOG["labels"]
        prefix = f"{labels['observation']}\n"
        separator = f"\n\n{labels['reception']}\n"
        if not text.startswith(prefix) or text.count(separator) != 1:
            return (999, 999, 999)
        observation, reception = text[len(prefix) :].split(separator)
        lines = (*observation.split("\n"), *reception.split("\n"))
        joiner = STEP11_SURFACE_CATALOG["group_grammar"][
            "clause_separator"
        ]
        joiner_peak = max(
            _outside_quote_joiner_count(line, joiner) for line in lines
        )
    except (KeyError, TypeError, UnicodeError, ValueError):
        return (999, 999, 999)
    clause_peak = max(
        len(sentence.clause_atom_ids) for sentence in witness.sentences
    )
    if any(
        not sentence.grammatical_chunk_clause_counts
        or any(
            type(count) is not int or count < 1
            for count in sentence.grammatical_chunk_clause_counts
        )
        or sum(sentence.grammatical_chunk_clause_counts)
        != len(sentence.clause_atom_ids)
        for sentence in witness.sentences
    ):
        return (999, 999, 999)
    grammatical_peak = max(
        count
        for sentence in witness.sentences
        for count in sentence.grammatical_chunk_clause_counts
    )
    return clause_peak, grammatical_peak, joiner_peak


def _surface_density_green(
    body: Any,
    witness: Step11ParsedSurfaceWitness | None,
) -> bool:
    clause_peak, grammatical_peak, joiner_peak = _surface_density_metrics(
        body, witness
    )
    grammar = STEP11_SURFACE_CATALOG.get("group_grammar", {})
    return bool(
        witness is not None
        and clause_peak
        <= grammar.get("maximum_observation_clauses_per_sentence", -1)
        and grammatical_peak
        <= grammar.get(
            "maximum_visible_clauses_per_grammatical_sentence", -1
        )
        and joiner_peak
        <= grammar.get("maximum_repeated_joiner_per_group", -1)
        and all(row.clause_atom_ids for row in witness.sentences)
    )


def _surface_quality_key(attributes: Sequence[int]) -> tuple[int, ...]:
    """Keep peak and repetition ahead of every identity tie-break."""

    if type(attributes) not in {list, tuple} or len(attributes) < 2:
        return (999, 999)
    return tuple(int(value) for value in attributes)


def _depth_contract_green(
    *,
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
    discourse_plan: Any,
    body: Any,
    witness: Any,
    binding: Any,
    semantic_overlay: Any,
    binding_issues: set[str],
) -> bool:
    """Recompute the Step 5/6/final-bytes depth boundary fail-closed.

    Sentence depth is owned by the Content Plan and Discourse sentence groups,
    not by an adaptive binding-count ceiling.  A sentence may contain several
    independently parsed clauses and one atom may legitimately satisfy more
    than one integrated obligation, so atom/node cardinality is deliberately
    not required to be equal.
    """

    if (
        type(content_plan) is not dict
        or type(discourse_plan) is not dict
        or type(witness) is not Step11ParsedSurfaceWitness
        or type(binding) is not Step11VerifiedSurfaceBinding
        or binding.verified is not True
        or type(witness.atoms) is not tuple
        or type(binding.binding_rows) is not tuple
        or binding_issues
        or semantic_overlay is None
    ):
        return False
    try:
        if validate_content_selection_policy(
            content_plan,
            inventory_result=inventory_result,
        ):
            return False
        decisions = content_plan.get("decisions")
        if type(decisions) is not list or any(
            type(row) is not dict for row in decisions
        ):
            return False
        active_ids = tuple(
            row.get("obligation_id")
            for row in decisions
            if row.get("status") in {"selected", "integrated_into"}
        )
        if (
            not active_ids
            or any(type(item) is not str or not item for item in active_ids)
            or len(active_ids) != len(set(active_ids))
        ):
            return False
        expected_depth = derive_content_depth(
            inventory_result,
            active_obligation_ids=active_ids,
        )
        expected_budget = _expected_depth_budget(expected_depth)
        budget = content_plan.get("section_budget")
        if (
            expected_budget is None
            or content_plan.get("depth") != expected_depth
            or type(budget) is not dict
            or set(budget) != set(_DEPTH_BUDGET_KEYS)
            or any(
                type(budget.get(key)) is not int
                for key in _DEPTH_BUDGET_KEYS
            )
            or budget != expected_budget
        ):
            return False
        if validate_discourse_plan(
            discourse_plan,
            content_plan=content_plan,
            obligation_ledger=inventory_result.ledger,
        ):
            return False
    except (
        AttributeError,
        KeyError,
        RecursionError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        return False

    groups = discourse_plan.get("sentence_groups")
    nodes = discourse_plan.get("nodes")
    if (
        type(groups) is not list
        or type(nodes) is not list
        or any(type(row) is not dict for row in (*groups, *nodes))
    ):
        return False
    group_roles = tuple(row.get("section_role") for row in groups)
    node_roles = tuple(row.get("section_role") for row in nodes)
    if (
        any(role not in {"observation", "reception"} for role in group_roles)
        or any(role not in {"observation", "reception"} for role in node_roles)
    ):
        return False
    observation_group_count = group_roles.count("observation")
    reception_group_count = group_roles.count("reception")
    if not (
        budget["observation_sentence_min"]
        <= observation_group_count
        <= budget["observation_sentence_max"]
        and budget["reception_sentence_min"]
        <= reception_group_count
        <= budget["reception_sentence_max"]
        and len(groups) <= budget["total_sentence_max"]
    ):
        return False

    final_counts = _final_section_line_counts(body)
    if final_counts != (observation_group_count, reception_group_count):
        return False
    atom_ids = tuple(row.atom_id for row in witness.atoms)
    actual_observation_atoms = sum(
        row.section_role == "observation" for row in witness.atoms
    )
    actual_reception_atoms = sum(
        row.section_role == "reception" for row in witness.atoms
    )
    if (
        any(
            row.section_role not in {"observation", "reception"}
            for row in witness.atoms
        )
        or any(type(atom_id) is not str or not atom_id for atom_id in atom_ids)
        or len(atom_ids) != len(set(atom_ids))
        or witness.observation_atom_count != actual_observation_atoms
        or witness.reception_atom_count != actual_reception_atoms
        or actual_observation_atoms < observation_group_count
        or actual_reception_atoms < reception_group_count
    ):
        return False
    witness_atom_ids = set(atom_ids)
    if any(
        type(row.atom_ids) is not tuple
        or not row.atom_ids
        or any(type(atom_id) is not str for atom_id in row.atom_ids)
        or not set(row.atom_ids) <= witness_atom_ids
        for row in binding.binding_rows
    ):
        return False
    try:
        return _required_coverage_green(
            binding,
            semantic_overlay=semantic_overlay,
            content_plan=content_plan,
            binding_issues=binding_issues,
        )
    except (AttributeError, KeyError, TypeError, UnicodeError, ValueError):
        return False


def evaluate_step11_natural_surface_candidate(
    candidate: Any,
    *,
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
    current_input: Mapping[str, Any],
) -> Step11HardGateResult:
    """Recompute both forward and inverse contracts and return 20 gates."""

    exact_candidate = type(candidate) is Step11NaturalSurfaceCandidate
    candidate_id = (
        candidate.candidate_id
        if exact_candidate and type(candidate.candidate_id) is str
        else ""
    )
    version = (
        candidate.candidate_version_id
        if exact_candidate and type(candidate.candidate_version_id) is str
        else ""
    )
    discourse_plan = candidate.discourse_plan if exact_candidate else None
    rendered = candidate.rendered_surface if exact_candidate else None
    body = (
        rendered.utf8_bytes
        if type(rendered) is Step11CanonicalRenderedSurface
        else None
    )
    forward_issues = _forward_candidate_issues(
        candidate,
        inventory_result=inventory_result,
        content_plan=content_plan,
        current_input=current_input,
    )
    semantic_overlay = None
    if exact_candidate and type(discourse_plan) is dict:
        try:
            semantic_overlay = build_step11_semantic_overlay(
                current_input,
                inventory_result=inventory_result,
                content_plan=content_plan,
                discourse_plan=discourse_plan,
            )
        except (AttributeError, KeyError, TypeError, UnicodeError, ValueError):
            semantic_overlay = None
    canonical_recomputed = None
    if exact_candidate and type(discourse_plan) is dict:
        try:
            canonical_recomputed = render_step11_natural_surface(
                candidate.surface_ast,
                discourse_plan=discourse_plan,
                inventory_result=inventory_result,
                content_plan=content_plan,
                current_input=current_input,
            )
        except (
            AttributeError,
            KeyError,
            RecursionError,
            TypeError,
            UnicodeError,
            ValueError,
        ):
            canonical_recomputed = None

    checks = {gate_id: True for gate_id, _code in _GATE_CODES}
    checks["artifact_schema_parent_hash"] = bool(
        exact_candidate
        and _artifact_schema_parent_hash_green(
            candidate,
            inventory_result=inventory_result,
            content_plan=content_plan,
            current_input=current_input,
            semantic_overlay=semantic_overlay,
            forward_issues=forward_issues,
        )
    )
    checks["version_dependency"] = bool(
        exact_candidate
        and version == STEP11_CANDIDATE_VERSION_ID
        and type(candidate.surface_ast) is Step11NaturalSurfaceAst
        and candidate.surface_ast.candidate_version_id
        == STEP11_CANDIDATE_VERSION_ID
        and not validate_step11_surface_catalog()
        and candidate.surface_ast.surface_catalog_sha256
        == STEP11_SURFACE_CATALOG_SHA256
        and type(rendered) is Step11CanonicalRenderedSurface
        and rendered.surface_catalog_sha256 == STEP11_SURFACE_CATALOG_SHA256
    )
    checks["canonical_render_equality"] = bool(
        exact_candidate
        and type(candidate.surface_ast) is Step11NaturalSurfaceAst
        and type(rendered) is Step11CanonicalRenderedSurface
        and type(canonical_recomputed) is Step11CanonicalRenderedSurface
        and type(body) is bytes
        and canonical_recomputed == rendered
        and canonical_recomputed.utf8_bytes == body
        and rendered.sha256 == hashlib.sha256(body).hexdigest()
        and rendered.source_surface_ast_sha256
        == artifact_sha256(
            step11_surface_ast_material(candidate.surface_ast)
        )
        and rendered.surface_catalog_sha256 == STEP11_SURFACE_CATALOG_SHA256
    )

    witness: Step11ParsedSurfaceWitness | None = None
    binding: Step11VerifiedSurfaceBinding | None = None
    if type(body) is bytes:
        try:
            witness = parse_step11_natural_surface(body)
        except (Step11InverseSurfaceError, TypeError, UnicodeError, ValueError):
            witness = None
    checks["body_parseability"] = witness is not None
    if witness is not None and type(discourse_plan) is dict:
        try:
            binding = match_step11_natural_surface(
                witness,
                inventory_result=inventory_result,
                content_plan=content_plan,
                discourse_plan=discourse_plan,
                current_input=current_input,
            )
        except (
            AttributeError,
            KeyError,
            RecursionError,
            Step11InverseSurfaceError,
            TypeError,
            UnicodeError,
            ValueError,
        ):
            binding = None

    binding_verified = binding is not None and binding.verified is True
    binding_issues = set(binding.issue_codes) if binding is not None else set()
    exact_fragment_count = (
        sum(len(row.source_fragments) for row in witness.atoms)
        if witness is not None
        else -1
    )
    checks["evidence_resolution"] = bool(
        binding_verified
        and witness is not None
        and binding.schema_version == STEP11_VERIFIED_BINDING_SCHEMA
        and witness.schema_version == STEP11_PARSED_WITNESS_SCHEMA
        and binding.parsed_witness_sha256
        == artifact_sha256(_witness_material(witness))
        and binding.obligation_ledger_sha256
        == artifact_sha256(inventory_result.ledger)
        and binding.content_plan_sha256 == artifact_sha256(content_plan)
        and type(discourse_plan) is dict
        and binding.discourse_plan_sha256 == artifact_sha256(discourse_plan)
        and binding.source_fragment_count == exact_fragment_count
        and exact_fragment_count > 0
        and _valid_nonzero_sha256(binding.source_unknown_oracle_sha256)
        and not binding_issues & _EVIDENCE_BINDING_ISSUES
    )
    checks["required_obligation_coverage"] = bool(
        binding is not None
        and semantic_overlay is not None
        and _required_coverage_green(
            binding,
            semantic_overlay=semantic_overlay,
            content_plan=content_plan,
            binding_issues=binding_issues,
        )
    )
    checks["bound_reception"] = bool(
        binding is not None
        and witness is not None
        and semantic_overlay is not None
        and _reception_binding_green(
            witness,
            binding,
            semantic_overlay=semantic_overlay,
            binding_issues=binding_issues,
        )
    )
    # Forward recomputation owns polarity/modality/time.  The inverse binding
    # must independently verify the concrete surface that carries it.
    checks["polarity_modality_time"] = bool(
        binding_verified
        and binding is not None
        and not binding_issues
        & {
            "S11_MATCH_MODALITY_STATUS_MISMATCH",
            "S11_MATCH_PREDICATE_ROLE_MISMATCH",
            "S11_MATCH_RECEPTION_TARGET_SCOPE_STATUS_MISMATCH",
        }
    )
    checks["relation_type_direction"] = bool(
        binding is not None
        and witness is not None
        and semantic_overlay is not None
        and _relation_binding_green(
            witness,
            binding,
            semantic_overlay=semantic_overlay,
            binding_issues=binding_issues,
        )
    )
    checks["referent_topic"] = bool(
        binding is not None
        and not any(
            code.startswith("S11_MATCH_UNKNOWN_")
            for code in binding_issues
        )
    )
    checks["unknown_boundary"] = bool(
        binding is not None
        and semantic_overlay is not None
        and _unknown_oracle_green(
            binding,
            semantic_overlay=semantic_overlay,
            binding_issues=binding_issues,
        )
    )
    checks["self_denial"] = bool(
        binding is not None
        and not any(code.startswith("S11_MATCH_SELF_DENIAL_") for code in binding_issues)
    )
    checks["unsupported_claim"] = bool(
        binding is not None
        and not binding_issues & _UNSUPPORTED_EXACT_ISSUES
        and not any(
            "_UNKNOWN_" in code
            or "_RELATION_" in code
            or code.startswith("S11_MATCH_MIXED_EMOTION_")
            for code in binding_issues
        )
    )
    checks["section_distinctness"] = bool(
        witness is not None
        and witness.observation_atom_count >= 1
        and witness.reception_atom_count >= 1
    )

    if witness is not None and type(body) is bytes:
        try:
            projection = project_step11_current_input(current_input)
        except (KeyError, TypeError, UnicodeError, ValueError):
            projection = None
        literal_fragments = tuple(
            item for row in witness.atoms for item in row.source_fragments
        )
        unique_fragments = set(literal_fragments)
        whole_maximum = int(
            STEP11_SURFACE_CATALOG["fragment_policy"]["whole_text_max_chars"]
        )
        long_sources = (
            {
                value
                for value in (
                    projection.thought_text,
                    projection.action_text,
                )
                if len(value) > whole_maximum
            }
            if projection is not None
            else set()
        )
        # Equal text is not itself a replay: one exact source endpoint may be
        # owned by several distinct required relations.  The inverse matcher
        # resolves source ranges and enforces its owner budget; this gate adds
        # the independent whole-input/enumeration ceiling without collapsing
        # those graph edges by their display text.
        checks["input_enumeration"] = bool(
            projection is not None
            and binding_verified
            and all(len(item) <= whole_maximum for item in unique_fragments)
            and not (unique_fragments & long_sources)
            and not any(
                row.form_id.startswith("relation_chain:")
                for row in witness.atoms
            )
            and not binding_issues
            & {
                "S11_MATCH_LITERAL_OWNER_BUDGET_EXCEEDED",
                "S11_MATCH_LITERAL_SOURCE_RANGE_INVALID",
            }
        )
        semantic_signatures = tuple(
            (
                row.section_role,
                row.form_id,
                row.claim_kinds,
                row.source_fragments,
                row.predicate_role,
                row.realization_status,
                row.relation_type,
                row.relation_direction,
                row.relation_endpoint_roles,
                row.unknown_dimension_class,
                row.self_denial_not_fact,
                row.reception_act,
                row.reception_scope,
                row.introduced_reference,
                row.compound_label_references,
                row.relation_endpoint_references,
                row.unknown_target_references,
                row.reception_antecedent_references,
            )
            for row in witness.atoms
        )
        checks["contribution_distinctness"] = bool(
            binding_verified
            and len(set(semantic_signatures)) == len(semantic_signatures)
            and witness.observation_atom_count >= 1
            and witness.reception_atom_count >= 1
            and all(
                not row.form_id.startswith("reception:direct:")
                and row.form_id.startswith("reception:typed:")
                and row.source_fragments == ()
                and row.reception_antecedent_references
                for row in witness.atoms
                if row.section_role == "reception"
            )
        )
        checks["depth"] = _depth_contract_green(
            inventory_result=inventory_result,
            content_plan=content_plan,
            discourse_plan=discourse_plan,
            body=body,
            witness=witness,
            binding=binding,
            semantic_overlay=semantic_overlay,
            binding_issues=binding_issues,
        )
        checks["surface_integrity"] = bool(
            type(rendered) is Step11CanonicalRenderedSurface
            and type(canonical_recomputed) is Step11CanonicalRenderedSurface
            and canonical_recomputed == rendered
            and rendered.utf8_bytes == body
            and rendered.sha256 == hashlib.sha256(body).hexdigest()
            and witness.body_sha256 == hashlib.sha256(body).hexdigest()
            and _surface_density_green(body, witness)
        )
        checks["naming_address"] = all(
            row.form_id.startswith(
                (
                    "reception:",
                    "thought",
                    "action",
                    "emotion",
                    "category",
                    "reference_introduction:",
                    "relation:",
                    "unknown",
                    "self_denial",
                    "bounded_counter",
                    "mixed_emotion:",
                    "mixed_emotion_compound:",
                )
            )
            for row in witness.atoms
        )
        checks["body_free_public_contract"] = (
            witness.body_free_export_allowed is False
        )
    else:
        for gate_id in (
            "input_enumeration",
            "contribution_distinctness",
            "depth",
            "surface_integrity",
            "naming_address",
            "body_free_public_contract",
        ):
            checks[gate_id] = False

    outcomes = tuple(
        Step11GateOutcome(
            ordinal,
            gate_id,
            bool(checks[gate_id]),
            None if checks[gate_id] else failure_code,
        )
        for ordinal, (gate_id, failure_code) in enumerate(_GATE_CODES, 1)
    )
    failures = tuple(
        row.failure_code for row in outcomes if row.failure_code is not None
    )
    density = _surface_density_metrics(body, witness)
    attributes = (
        density[0],
        density[1],
        density[2],
        -len(binding.binding_rows) if binding_verified else 0,
        len(binding.integrated_relation_ids) if binding_verified else 999,
        witness.observation_atom_count if witness is not None else 999,
        witness.reception_atom_count if witness is not None else 999,
    )
    return Step11HardGateResult(
        schema_version=STEP11_HARD_GATE_SCHEMA,
        candidate_id=candidate_id,
        candidate_version_id=version,
        parsed_witness_sha256=(
            artifact_sha256(_witness_material(witness))
            if witness is not None
            else None
        ),
        verified_binding_sha256=(
            artifact_sha256(_binding_material(binding))
            if binding is not None
            else None
        ),
        outcomes=outcomes,
        failure_codes=failures,
        hard_pass=not failures,
        selector_attributes=attributes,
    )


def select_step11_natural_surface_candidates(
    candidates: Sequence[Any],
    *,
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
    current_input: Mapping[str, Any],
    candidate_limit: int = 12,
) -> Step11SelectionResult:
    """Select from exact, valid candidates after body-hash deduplication."""

    if (
        type(candidates) not in {list, tuple}
        or not candidates
        or type(candidate_limit) is not int
        or type(candidate_limit) is bool
        or not 1 <= candidate_limit <= 12
        or len(candidates) > candidate_limit
    ):
        raise Step11InverseSurfaceError("S11_SELECTOR_CANDIDATE_SET_INVALID")
    if any(type(row) is not Step11NaturalSurfaceCandidate for row in candidates):
        raise Step11InverseSurfaceError("S11_SELECTOR_CANDIDATE_TYPE_INVALID")
    if any(
        type(row.candidate_id) is not str or not row.candidate_id
        for row in candidates
    ):
        raise Step11InverseSurfaceError("S11_SELECTOR_CANDIDATE_ID_INVALID")

    ordered = tuple(sorted(candidates, key=lambda row: row.candidate_id))
    ids = tuple(row.candidate_id for row in ordered)
    if any(not item for item in ids) or len(set(ids)) != len(ids):
        raise Step11InverseSurfaceError("S11_SELECTOR_CANDIDATE_ID_INVALID")
    results = tuple(
        evaluate_step11_natural_surface_candidate(
            row,
            inventory_result=inventory_result,
            content_plan=content_plan,
            current_input=current_input,
        )
        for row in ordered
    )

    # Several discourse plans may canonically render to equal bytes.  Keep one
    # deterministic representative per body before applying selector scores;
    # duplicate plan identities therefore cannot bias the selection.
    passing_by_body: dict[
        str,
        tuple[
            tuple[Any, ...],
            Step11NaturalSurfaceCandidate,
            Step11HardGateResult,
        ],
    ] = {}
    for candidate, result in zip(ordered, results):
        if not result.hard_pass:
            continue
        body_sha256 = hashlib.sha256(candidate.final_utf8_bytes).hexdigest()
        row = (
            _surface_quality_key(result.selector_attributes)
            + (result.candidate_id,),
            candidate,
            result,
        )
        previous = passing_by_body.get(body_sha256)
        if previous is None or row[0] < previous[0]:
            passing_by_body[body_sha256] = row
    passing = tuple(passing_by_body.values())
    selected = min(passing, key=lambda row: row[0])[1] if passing else None
    selected_id = selected.candidate_id if selected is not None else None
    return Step11SelectionResult(
        schema_version=STEP11_SELECTION_SCHEMA,
        candidate_version_id=STEP11_CANDIDATE_VERSION_ID,
        evaluated_candidate_ids=ids,
        gate_results=results,
        selected_candidate_id=selected_id,
        selected_candidate=selected,
        status="selected" if selected is not None else "v3_no_valid_candidate",
        bounded_candidate_limit=candidate_limit,
        recovery_attempted=False,
        v1_fallback_used=False,
    )


__all__ = [
    "Step11GateOutcome",
    "Step11HardGateResult",
    "Step11SelectionResult",
    "evaluate_step11_natural_surface_candidate",
    "select_step11_natural_surface_candidates",
]
