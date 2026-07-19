# -*- coding: utf-8 -*-
from __future__ import annotations

"""Forward-aware hard gate and deterministic selector for Step 11 rc0027.

The body parser and semantic matcher remain inverse-only owners.  This module
is the trust boundary that joins their result to the exact forward candidate
type and fully recomputes the forward AST, canonical rendering, parent hashes,
and candidate identity before any bytes can become selectable.
"""

import hashlib
import re
import unicodedata
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
    Step11SelectorAttributes,
    Step11VerifiedSurfaceBinding,
    _binding_material,
    _independent_action_lifecycle_for_nuclei,
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
_GATE_ANCHOR_FORBIDDEN_RE = re.compile(
    r"[\r\n\x00-\x1f\x7f\u2028\u2029"
    r"。、，．！？!?;；:：,.'\"`"
    r"\(\)\[\]\{\}（）［］｛｝〈〉《》【】〔〕"
    r"\u300c\u300d\u300e\u300f]"
)
_GATE_ANCHOR_SEGMENT_AUTHORITIES = (
    "trusted_fragment_entire_text",
    "complete_punctuation_delimited_run",
)
_GATE_ANCHOR_DANGLING_PREFIXES = (
    "そして", "また", "ただ", "それでも", "けれど", "けど", "だけ", "は",
    "が", "を", "に", "へ", "と", "の", "も", "や", "で", "から",
    "ので",
)
_GATE_ANCHOR_DANGLING_SUFFIXES = (
    "は", "が", "を", "に", "へ", "と", "の", "も", "や", "て", "で",
    "し", "から", "ので", "けれど", "けど", "ながら", "つつ", "たり",
    "なら", "れば", "たら",
)


def _step11_gate_visible_anchor_text_safe(
    value: Any, maximum_scalars: int = 16
) -> bool:
    """Revalidate visible anchor scalars at the forward-aware gate."""

    return bool(
        type(value) is str
        and type(maximum_scalars) is int
        and type(maximum_scalars) is not bool
        and maximum_scalars >= 2
        and unicodedata.normalize("NFC", value) == value
        and value == value.strip()
        and 2 <= len(value) <= maximum_scalars
        and _GATE_ANCHOR_FORBIDDEN_RE.search(value) is None
        and not any(scalar.isspace() for scalar in value)
        and not any(
            label in value for label in ("見えたこと", "Emlisから", "Emlis")
        )
        and not any(
            unicodedata.category(scalar).startswith("C")
            for scalar in value
        )
    )


def _step11_gate_anchor_candidate_complete(
    value: Any, maximum_scalars: int = 16
) -> bool:
    return bool(
        _step11_gate_visible_anchor_text_safe(value, maximum_scalars)
        and not str(value).startswith(_GATE_ANCHOR_DANGLING_PREFIXES)
        and not str(value).endswith(_GATE_ANCHOR_DANGLING_SUFFIXES)
    )


def _step11_gate_safe_anchor_segments(
    source_text: Any, maximum_scalars: int = 16
) -> tuple[tuple[str, int, int], ...]:
    """Gate-owned reconstruction of whole trusted/punctuation runs only."""

    if (
        type(source_text) is not str
        or unicodedata.normalize("NFC", source_text) != source_text
        or type(maximum_scalars) is not int
        or type(maximum_scalars) is bool
        or maximum_scalars < 2
        or any(
            scalar.isspace()
            or unicodedata.category(scalar).startswith("C")
            for scalar in source_text
        )
    ):
        return ()

    runs: list[tuple[int, int]] = []
    run_start: int | None = None
    for index, scalar in enumerate(source_text):
        punctuation = _GATE_ANCHOR_FORBIDDEN_RE.search(scalar) is not None
        if not punctuation and run_start is None:
            run_start = index
        if punctuation and run_start is not None:
            runs.append((run_start, index))
            run_start = None
    if run_start is not None:
        runs.append((run_start, len(source_text)))
    candidates: set[tuple[str, int, int]] = set()
    for run_start, run_end in runs:
        run = source_text[run_start:run_end]
        if len(run) <= maximum_scalars and (
            _step11_gate_anchor_candidate_complete(run, maximum_scalars)
        ):
            candidates.add((run, run_start, run_end))
    return tuple(
        (text, start, end) for text, start, end in sorted(
            candidates,
            key=lambda row: (-len(row[0]), row[1], row[2], row[0]),
        )
    )


def _step11_gate_action_lifecycle_green(
    *,
    witness: Step11ParsedSurfaceWitness,
    binding: Step11VerifiedSurfaceBinding,
    inventory_result: SemanticObligationInventoryResult,
    semantic_overlay: Any,
    action_text: str,
) -> bool:
    """Recompute observation and Reception lifecycle from source authority."""

    nucleus_by_id = {
        str(row.source_id): row
        for row in inventory_result.source_snapshot.nuclei
    }
    parsed_phrases = tuple(
        phrase
        for atom in witness.atoms
        if atom.section_role == "observation"
        for phrase in getattr(atom, "grounded_phrases", ())
    )
    phrase_bindings = tuple(binding.grounded_phrase_bindings)
    if len(parsed_phrases) != len(phrase_bindings):
        return False
    expected_action_lifecycles: set[str] = set()
    for phrase, row in zip(parsed_phrases, phrase_bindings):
        if len(row.owner_nucleus_ids) != 1:
            return False
        expected = _independent_action_lifecycle_for_nuclei(
            row.owner_nucleus_ids,
            nucleus_by_id=nucleus_by_id,
            action_text=action_text,
        )
        if (
            phrase.action_lifecycle != expected
            or row.action_lifecycle != expected
            or dict(phrase.visible_feature_fields).get(
                "action_lifecycle", "not_applicable"
            )
            != expected
        ):
            return False
        owner = nucleus_by_id.get(row.owner_nucleus_ids[0])
        if owner is None:
            return False
        if expected != "not_applicable":
            if (
                getattr(owner, "kind", None) != "action"
                or row.binding_family not in {None, "action_lifecycle"}
            ):
                return False
            expected_action_lifecycles.add(expected)

    for overlay_row in semantic_overlay.reception_antecedent_bindings:
        target_ids = tuple(
            dict.fromkeys(
                (
                    *overlay_row.antecedent_nucleus_ids,
                    *overlay_row.supporting_nucleus_ids,
                )
            )
        )
        expected = _independent_action_lifecycle_for_nuclei(
            target_ids,
            nucleus_by_id=nucleus_by_id,
            action_text=action_text,
        )
        if str(overlay_row.action_lifecycle) != expected:
            return False
        if expected != "not_applicable":
            expected_action_lifecycles.add(expected)

    reception_statuses = {
        str(atom.realization_status)
        for atom in witness.atoms
        if atom.section_role == "reception"
        and atom.reception_scope
        in {"action", "thought_action", "relation_action"}
    }
    if reception_statuses and (
        not expected_action_lifecycles
        or not reception_statuses <= expected_action_lifecycles
    ):
        return False
    contradictory = (
        {"intended"}
        & (reception_statuses | expected_action_lifecycles)
        and {
            "reported_completed",
            "reported_ongoing",
            "reported_not_completed",
        }
        & (reception_statuses | expected_action_lifecycles)
    )
    return not bool(contradictory)
_EVIDENCE_BINDING_ISSUES = frozenset(
    {
        "S11_MATCH_FRAGMENT_NOT_SOURCE_BACKED",
        "S11_MATCH_FUSED_LITERAL_OWNER_AMBIGUOUS",
        "S11_MATCH_FUSED_LITERAL_OWNER_COVERAGE_MISMATCH",
        "S11_MATCH_FUSED_LITERAL_OWNER_UNRESOLVED",
        "S11_MATCH_LABEL_ANCHOR_CONTRACT_MISMATCH",
        "S11_MATCH_NUCLEUS_BINDING_CONTRACT_MISMATCH",
        "S11_MATCH_SOURCE_ANCHOR_CONTRACT_MISMATCH",
        "S11_MATCH_GROUNDED_ACTION_LIFECYCLE_MISMATCH",
        "S11_MATCH_GROUNDED_PROFILE_UNRESOLVED",
        "S11_MATCH_VISIBLE_SOURCE_ANCHOR_FAMILY_INVALID",
        "S11_MATCH_VISIBLE_SOURCE_ANCHOR_FAMILY_MISMATCH",
        "S11_MATCH_VISIBLE_SOURCE_ANCHOR_BOUNDARY_INVALID",
        "S11_MATCH_VISIBLE_REFERENCE_BOOKKEEPING_FORBIDDEN",
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
_TARGET_GROUP_COUNT = {"minimal": 2, "focused": 3, "layered": 4}
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
    reception_atom_by_id = {
        row.atom_id: row for row in reception_atoms
    }
    reception_atom_ids = {row.atom_id for row in reception_atoms}

    def row_mode_green(row: Any) -> bool:
        if len(row.atom_ids) != 1:
            return False
        atom = reception_atom_by_id.get(row.atom_ids[0])
        if atom is None:
            return False
        anaphoric_green = bool(
            row.match_basis
            == "bound_reception_anaphoric_exact_semantic_owner"
            and atom.form_id.startswith("reception:anaphoric:")
            and not atom.reception_antecedent_references
        )
        return bool(
            anaphoric_green
            and atom.claim_kinds == ("bound_reception",)
            and atom.source_fragments == ()
            and atom.introduced_reference is None
            and not atom.compound_label_references
            and not atom.relation_endpoint_references
            and not atom.unknown_target_references
        )

    return bool(
        expected_ids
        and binding.integrated_reception_binding_ids == expected_ids
        and {row.obligation_id for row in reception_rows}
        == expected_obligation_ids
        and all(row_mode_green(row) for row in reception_rows)
        and {row.atom_ids[0] for row in reception_rows}
        == reception_atom_ids
        and all(
            row.form_id.startswith("reception:anaphoric:")
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
    grounded_owner_sequence_by_atom = {
        atom.atom_id: tuple(
            row.owner_nucleus_ids[0]
            for row in binding.grounded_phrase_bindings
            if row.atom_id == atom.atom_id
            and len(row.owner_nucleus_ids) == 1
        )
        for atom in witness.atoms
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
        prefix = (
            "obligation_fused:relation:"
            f"{relation.relation_type}:"
            f"{relation.relation_direction}:"
        )
        ambiguous_prefix = (
            "obligation_fused:relation:"
            f"{relation.relation_type}:source_or_target:"
        )

        def relation_surface_green(atom: Any) -> bool:
            if not atom.form_id.startswith((prefix, ambiguous_prefix)):
                return False
            if getattr(atom, "grounded_phrases", ()):
                form_parts = atom.form_id.split(":")
                local_marker = (
                    form_parts[5]
                    if len(form_parts) >= 8
                    and form_parts[5].startswith("local_")
                    else None
                )
                owner_sequence = grounded_owner_sequence_by_atom.get(
                    atom.atom_id, ()
                )
                if local_marker is not None:
                    local_role = form_parts[6]
                    for local_endpoint in {
                        "local_from": ("from",),
                        "local_to": ("to",),
                        "local_source_or_target": ("from", "to"),
                    }.get(local_marker, ()):
                        local_nucleus_id = (
                            relation.from_nucleus_id
                            if local_endpoint == "from"
                            else relation.to_nucleus_id
                        )
                        exact_nucleus_id = (
                            relation.to_nucleus_id
                            if local_endpoint == "from"
                            else relation.from_nucleus_id
                        )
                        endpoint_role = (
                            relation.from_endpoint_role
                            if local_endpoint == "from"
                            else relation.to_endpoint_role
                        )
                        earlier_local_owners = tuple(
                            row
                            for row in witness.atoms
                            if row.section_role == "observation"
                            and local_nucleus_id
                            in grounded_owner_sequence_by_atom.get(
                                row.atom_id, ()
                            )
                            and row.byte_start < atom.byte_start
                        )
                        if (
                            local_role == endpoint_role
                            and owner_sequence == (exact_nucleus_id,)
                            and len(earlier_local_owners) == 1
                        ):
                            return True
                    return False
                lexical_rule = STEP11_SURFACE_CATALOG[
                    "grounded_lexicalization"
                ]["relation_atoms"][relation.relation_type][
                    relation.relation_direction
                ]
                owner_by_endpoint = {
                    "from": relation.from_nucleus_id,
                    "to": relation.to_nucleus_id,
                }
                return owner_sequence == tuple(
                    owner_by_endpoint[endpoint]
                    for endpoint in lexical_rule["endpoint_order"]
                )
            try:
                form_parts = atom.form_id.split(":")
                rule_index = int(form_parts[4])
                rule = STEP11_SURFACE_CATALOG[
                    "obligation_fused_grammar"
                ]["relation_forms"][relation.relation_type][
                    relation.relation_direction
                ][rule_index]
                stem = rule["stem"]
            except (IndexError, KeyError, TypeError, ValueError):
                return False
            if type(stem) is not str:
                return False
            local_marker = (
                form_parts[5]
                if len(form_parts) >= 8
                and form_parts[5].startswith("local_")
                else None
            )
            if local_marker is not None:
                local_role = form_parts[6]
                try:
                    anaphor_index = int(form_parts[7])
                    local_anaphor = STEP11_SURFACE_CATALOG[
                        "obligation_fused_grammar"
                    ]["local_anaphors"][local_role][anaphor_index]
                except (IndexError, KeyError, TypeError, ValueError):
                    return False
                if type(local_anaphor) is not str or not local_anaphor:
                    return False
                endpoint_contracts = {
                    "from": (left[0], right[0], relation.from_endpoint_role),
                    "to": (right[0], left[0], relation.to_endpoint_role),
                }
                allowed_local_endpoints = {
                    "local_from": ("from",),
                    "local_to": ("to",),
                    "local_source_or_target": ("from", "to"),
                }.get(local_marker, ())
                observation_atoms = tuple(
                    row
                    for row in witness.atoms
                    if row.section_role == "observation"
                )
                for endpoint in allowed_local_endpoints:
                    local_value, exact_value, endpoint_role = (
                        endpoint_contracts[endpoint]
                    )
                    local_owners = tuple(
                        row
                        for row in observation_atoms
                        if local_value in row.source_fragments
                    )
                    exact_owners = tuple(
                        row
                        for row in observation_atoms
                        if exact_value in row.source_fragments
                    )
                    if (
                        local_role == endpoint_role
                        and len(local_owners) == 1
                        and local_owners[0].byte_start < atom.byte_start
                        and exact_owners == (atom,)
                        and atom.source_fragments == (exact_value,)
                    ):
                        return True
                return False
            values = {
                "{from_endpoint}": left[0],
                "{to_endpoint}": right[0],
            }
            visible = tuple(
                values[token]
                for token in sorted(values, key=lambda row: stem.index(row))
            )
            return atom.source_fragments == visible

        matches = tuple(
            atom
            for atom in witness.atoms
            if atom.section_role == "observation"
            and atom.form_id.startswith((prefix, ambiguous_prefix))
            and "nucleus_notice" in atom.claim_kinds
            and "relation_notice" in atom.claim_kinds
            and relation_surface_green(atom)
            and atom.introduced_reference is None
            and not atom.compound_label_references
            and not atom.relation_endpoint_references
            and not atom.unknown_target_references
            and not atom.reception_antecedent_references
            and atom.relation_type == relation.relation_type
            and atom.relation_direction
            in {relation.relation_direction, "source_or_target"}
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


def _surface_quality_key(attributes: Any) -> tuple[Any, ...]:
    """Return the frozen section-14.1 lexicographic direction tuple."""

    if type(attributes) is Step11SelectorAttributes:
        return (
            -attributes.required_binding_count,
            -attributes.required_distinctness_group_count,
            -attributes.bound_reception_target_count,
            attributes.section_semantic_replay_count,
            attributes.generic_referent_count,
            attributes.unnecessary_source_anchor_count,
            attributes.redundant_atom_count,
            attributes.depth_deviation,
            attributes.anaphora_distance,
            attributes.candidate_id.encode("ascii"),
        )
    # Append-only compatibility for historical unit tests that exercise the
    # old helper directly.  Production results never enter this branch.
    if type(attributes) not in {list, tuple} or len(attributes) < 2:
        return (999, 999)
    try:
        return tuple(int(value) for value in attributes)
    except (TypeError, ValueError):
        return (999, 999)


def _selector_atom_semantic_key(
    atom: Any,
    *,
    bound_obligation_ids: Sequence[str],
    reception_target_ids: Sequence[str],
) -> tuple[Any, ...]:
    """Rebuild one body/binding semantic key without candidate metadata."""

    return (
        tuple(atom.claim_kinds),
        tuple(sorted(bound_obligation_ids)),
        tuple(sorted(reception_target_ids)),
        tuple(
            (
                phrase.visible_feature_fingerprint_sha256,
                phrase.anchor_text,
            )
            for phrase in getattr(atom, "grounded_phrases", ())
        ),
        atom.predicate_role,
        atom.realization_status,
        atom.relation_type,
        atom.relation_direction,
        tuple(atom.relation_endpoint_roles),
        atom.unknown_dimension_class,
        atom.self_denial_not_fact,
        atom.reception_act,
        atom.reception_scope,
    )


def _step11_selector_attributes(
    *,
    candidate_id: str,
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
    discourse_plan: Mapping[str, Any],
    witness: Step11ParsedSurfaceWitness | None,
    binding: Step11VerifiedSurfaceBinding | None,
    semantic_overlay: Any,
) -> Step11SelectorAttributes:
    """Compute the ten canonical attributes from inverse-owned evidence."""

    required = {
        value
        for value in content_plan.get(
            "required_coverage_obligation_ids", []
        )
        if type(value) is str
    }
    ledger_rows = inventory_result.ledger.get("obligations", [])
    obligation_by_id = {
        row.get("obligation_id"): row
        for row in ledger_rows
        if type(row) is dict and type(row.get("obligation_id")) is str
    }
    binding_rows = binding.binding_rows if binding is not None else ()
    bound_required = {
        row.obligation_id for row in binding_rows if row.obligation_id in required
    }
    distinctness_groups = {
        obligation_by_id[obligation_id].get("distinctness_group")
        for obligation_id in bound_required
        if obligation_id in obligation_by_id
        and type(
            obligation_by_id[obligation_id].get("distinctness_group")
        )
        is str
    }

    integrated_reception_ids = (
        set(binding.integrated_reception_binding_ids)
        if binding is not None
        else set()
    )
    reception_binding_rows = tuple(
        row
        for row in getattr(
            semantic_overlay, "reception_antecedent_bindings", ()
        )
        if row.binding_id in integrated_reception_ids
    )
    reception_targets = {
        obligation_id
        for row in reception_binding_rows
        for obligation_id in row.source_target_obligation_ids
        if obligation_id in required
        and obligation_by_id.get(obligation_id, {}).get("kind")
        != STANCE_KIND
    }

    bound_by_atom: dict[str, set[str]] = {}
    for row in binding_rows:
        for atom_id in row.atom_ids:
            bound_by_atom.setdefault(atom_id, set()).add(row.obligation_id)
    reception_targets_by_atom: dict[str, set[str]] = {}
    reception_atom_by_obligation = {
        row.obligation_id: atom_id
        for row in binding_rows
        if row.obligation_kind == STANCE_KIND and len(row.atom_ids) == 1
        for atom_id in row.atom_ids
    }
    for row in reception_binding_rows:
        atom_id = reception_atom_by_obligation.get(
            row.reception_obligation_id
        )
        if atom_id is not None:
            reception_targets_by_atom.setdefault(atom_id, set()).update(
                row.source_target_obligation_ids
            )

    keys_by_section: dict[str, list[tuple[Any, ...]]] = {
        "observation": [],
        "reception": [],
    }
    if witness is not None:
        for atom in witness.atoms:
            if atom.section_role not in keys_by_section:
                continue
            keys_by_section[atom.section_role].append(
                _selector_atom_semantic_key(
                    atom,
                    bound_obligation_ids=bound_by_atom.get(
                        atom.atom_id, ()
                    ),
                    reception_target_ids=reception_targets_by_atom.get(
                        atom.atom_id, ()
                    ),
                )
            )
    section_replay = len(
        set(keys_by_section["observation"])
        & set(keys_by_section["reception"])
    )
    redundant = sum(
        len(rows) - len(set(rows)) for rows in keys_by_section.values()
    )
    generic_referents = (
        sum(
            atom.section_role == "observation"
            and not atom.source_fragments
            and not getattr(atom, "grounded_phrases", ())
            for atom in witness.atoms
        )
        if witness is not None
        else 999
    )
    unnecessary_anchors = sum(
        bool(getattr(row, "source_anchor_ids", ()))
        and getattr(row, "match_candidate_count", 0) == 1
        and getattr(row, "source_anchor_use_reason_code", None) is None
        for row in (
            getattr(binding, "grounded_phrase_bindings", ())
            if binding is not None
            else ()
        )
    )
    actual_groups = (
        len(discourse_plan.get("sentence_groups", []))
        if type(discourse_plan) is dict
        else 999
    )
    target_groups = _TARGET_GROUP_COUNT.get(
        content_plan.get("depth"), actual_groups
    )

    anaphora_pairs: set[tuple[str, str]] = set()
    atom_order = (
        {
            atom.atom_id: index
            for index, atom in enumerate(
                sorted(witness.atoms, key=lambda row: row.byte_start)
            )
        }
        if witness is not None
        else {}
    )
    owner_atoms_by_obligation = {
        row.obligation_id: tuple(row.atom_ids) for row in binding_rows
    }
    for reception in reception_binding_rows:
        reception_atom_id = reception_atom_by_obligation.get(
            reception.reception_obligation_id
        )
        if reception_atom_id is None:
            continue
        for obligation_id in (
            *reception.antecedent_obligation_ids,
            *reception.supporting_obligation_ids,
        ):
            for owner_atom_id in owner_atoms_by_obligation.get(
                obligation_id, ()
            ):
                anaphora_pairs.add((reception_atom_id, owner_atom_id))
    anaphora_distance = sum(
        max(
            0,
            atom_order.get(reception_atom_id, 0)
            - atom_order.get(owner_atom_id, 0),
        )
        for reception_atom_id, owner_atom_id in anaphora_pairs
    )
    return Step11SelectorAttributes(
        required_binding_count=len(bound_required),
        required_distinctness_group_count=len(distinctness_groups),
        bound_reception_target_count=len(reception_targets),
        section_semantic_replay_count=section_replay,
        generic_referent_count=generic_referents,
        unnecessary_source_anchor_count=unnecessary_anchors,
        redundant_atom_count=redundant,
        depth_deviation=abs(actual_groups - target_groups),
        anaphora_distance=anaphora_distance,
        candidate_id=candidate_id,
    )


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
    projected_input = None
    try:
        projected_input = project_step11_current_input(current_input)
    except (KeyError, TypeError, UnicodeError, ValueError):
        projected_input = None
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
        sum(
            len(row.source_fragments)
            + len(getattr(row, "grounded_phrases", ()))
            for row in witness.atoms
        )
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
        and len(binding.grounded_phrase_bindings)
        == sum(
            len(getattr(row, "grounded_phrases", ()))
            for row in witness.atoms
        )
        and all(
            row.match_candidate_count == 1
            and len(row.owner_nucleus_ids) == 1
            and bool(row.owner_obligation_ids)
            for row in binding.grounded_phrase_bindings
        )
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
        and witness is not None
        and semantic_overlay is not None
        and projected_input is not None
        and _step11_gate_action_lifecycle_green(
            witness=witness,
            binding=binding,
            inventory_result=inventory_result,
            semantic_overlay=semantic_overlay,
            action_text=projected_input.action_text,
        )
        and not binding_issues
        & {
            "S11_MATCH_GROUNDED_ACTION_LIFECYCLE_MISMATCH",
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
            code.startswith(
                ("S11_MATCH_UNKNOWN_", "S11_MATCH_REFERENCE_")
            )
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
        projection = projected_input
        literal_fragments = tuple(
            item for row in witness.atoms for item in row.source_fragments
        )
        unique_fragments = set(literal_fragments)
        parsed_grounded_phrases = tuple(
            phrase
            for atom in witness.atoms
            if atom.section_role == "observation"
            for phrase in getattr(atom, "grounded_phrases", ())
        )
        parsed_anchor_phrases = tuple(
            phrase
            for phrase in parsed_grounded_phrases
            if phrase.anchor_text is not None
        )
        phrase_binding_rows = tuple(
            binding.grounded_phrase_bindings
            if binding is not None
            else ()
        )
        ast_specs = tuple(
            getattr(candidate.surface_ast, "grounded_phrase_specs", ())
            if type(candidate.surface_ast) is Step11NaturalSurfaceAst
            else ()
        )
        ast_anchor = (
            getattr(candidate.surface_ast, "visible_source_anchor_use", None)
            if type(candidate.surface_ast) is Step11NaturalSurfaceAst
            else None
        )
        grounded_contract_green = bool(
            parsed_grounded_phrases
            and len(parsed_grounded_phrases)
            == len(phrase_binding_rows)
            == len(ast_specs)
            and all(
                phrase_binding.match_candidate_count == 1
                and len(phrase_binding.owner_nucleus_ids) == 1
                and sum(
                    spec.phrase_text == phrase.phrase_text
                    and spec.visible_feature_fields
                    == phrase.visible_feature_fields
                    and spec.visible_feature_fingerprint_sha256
                    == phrase.visible_feature_fingerprint_sha256
                    and spec.phrase_profile_id
                    == phrase.phrase_profile_id
                    == phrase_binding.phrase_profile_id
                    and spec.anchor_risk_rank
                    == phrase.anchor_risk_rank
                    == phrase_binding.anchor_risk_rank
                    and dict(spec.visible_feature_fields).get(
                        "action_lifecycle", "not_applicable"
                    )
                    == phrase.action_lifecycle
                    == phrase_binding.action_lifecycle
                    and tuple(spec.owner_nucleus_ids)
                    == tuple(phrase_binding.owner_nucleus_ids)
                    and set(spec.owner_obligation_ids)
                    == set(phrase_binding.owner_obligation_ids)
                    for spec in ast_specs
                )
                == 1
                for phrase, phrase_binding in zip(
                    parsed_grounded_phrases, phrase_binding_rows
                )
            )
        )
        anchor_binding_rows = tuple(
            row for row in phrase_binding_rows if row.source_anchor_ids
        )
        overlay_anchor_by_id = {
            str(row.anchor_id): row
            for row in (
                semantic_overlay.anchors
                if semantic_overlay is not None
                else ()
            )
        }
        gate_lexical_contract = STEP11_SURFACE_CATALOG.get(
            "grounded_lexicalization", {}
        )
        gate_anchor_policy = (
            gate_lexical_contract.get("anchor_segment_policy", {})
            if type(gate_lexical_contract) is dict
            else {}
        )
        gate_anchor_policy_green = bool(
            type(gate_anchor_policy) is dict
            and gate_anchor_policy.get("unicode_category_c_forbidden") is True
            and gate_anchor_policy.get("mechanical_prefix_truncation") is False
            and gate_anchor_policy.get("minimum_scalars") == 2
            and gate_anchor_policy.get("maximum_scalars") == 16
            and tuple(
                gate_anchor_policy.get("accepted_segment_authorities", ())
            )
            == _GATE_ANCHOR_SEGMENT_AUTHORITIES
            and gate_anchor_policy.get("long_run_subrange_authority")
            == "forbidden"
            and gate_anchor_policy.get("whitespace_or_control_disposition")
            == "fail_closed"
            and gate_anchor_policy.get("unsafe_result") == "fail_closed"
            and "clause_boundary_tokens" not in gate_anchor_policy
            and "safe_subrange_terminal_suffixes" not in gate_anchor_policy
        )
        gate_binding_families_green = bool(
            type(gate_lexical_contract) is dict
            and gate_lexical_contract.get("source_anchor_binding_families")
            == {
                "reported_profile": "に表れている",
                "action_lifecycle": "として示された",
                "relation_shift": "を起点にした",
            }
        )
        gate_safe_boundary_green = False
        if ast_anchor is not None and len(anchor_binding_rows) == 1:
            phrase_binding = anchor_binding_rows[0]
            source_anchor_id = str(
                getattr(ast_anchor, "source_fragment_anchor_id", "")
            )
            source_anchor = overlay_anchor_by_id.get(source_anchor_id)
            if source_anchor is not None:
                anchor_text = str(getattr(ast_anchor, "anchor_text", ""))
                relative_start = int(getattr(ast_anchor, "source_start", -1)) - int(
                    source_anchor.start
                )
                relative_end = int(getattr(ast_anchor, "source_end", -1)) - int(
                    source_anchor.start
                )
                safe_segments = _step11_gate_safe_anchor_segments(
                    str(source_anchor.text), 16
                )
                gate_safe_boundary_green = bool(
                    (anchor_text, relative_start, relative_end)
                    in safe_segments
                    and phrase_binding.source_anchor_slot
                    == getattr(ast_anchor, "source_slot", None)
                    == str(source_anchor.source_slot)
                    and phrase_binding.source_anchor_start
                    == getattr(ast_anchor, "source_start", None)
                    and phrase_binding.source_anchor_end
                    == getattr(ast_anchor, "source_end", None)
                    and phrase_binding.source_anchor_text_sha256
                    == getattr(ast_anchor, "anchor_text_sha256", None)
                    == hashlib.sha256(anchor_text.encode("utf-8")).hexdigest()
                )
        anchor_contract_green = bool(
            gate_anchor_policy_green
            and gate_binding_families_green
            and ast_anchor is not None
            and len(parsed_anchor_phrases) == 1
            and len(anchor_binding_rows) == 1
            and len(anchor_binding_rows[0].source_anchor_ids) == 1
            and parsed_anchor_phrases[0].anchor_text
            == getattr(ast_anchor, "anchor_text", None)
            and _step11_gate_visible_anchor_text_safe(
                parsed_anchor_phrases[0].anchor_text, 16
            )
            and _step11_gate_visible_anchor_text_safe(
                getattr(ast_anchor, "anchor_text", None), 16
            )
            and tuple(anchor_binding_rows[0].owner_nucleus_ids)
            == (getattr(ast_anchor, "owner_nucleus_id", None),)
            and getattr(ast_anchor, "owner_obligation_id", None)
            in anchor_binding_rows[0].owner_obligation_ids
            and anchor_binding_rows[0].source_anchor_ids
            == (getattr(ast_anchor, "source_fragment_anchor_id", None),)
            and parsed_anchor_phrases[0].binding_family
            == anchor_binding_rows[0].binding_family
            == getattr(ast_anchor, "binding_family", None)
            and getattr(ast_anchor, "binding_family", None)
            in {"reported_profile", "action_lifecycle", "relation_shift"}
            and body.decode("utf-8").count(
                "「"
                + str(getattr(ast_anchor, "anchor_text", ""))
                + "」"
                + str(
                    STEP11_SURFACE_CATALOG["grounded_lexicalization"]
                    ["source_anchor_binding_families"].get(
                        getattr(ast_anchor, "binding_family", None), ""
                    )
                )
            )
            == 1
            and anchor_binding_rows[0].source_anchor_use_reason_code
            == "INPUT_SPECIFIC_BINDING_REQUIRED"
            and getattr(ast_anchor, "reason_code", None)
            == "INPUT_SPECIFIC_BINDING_REQUIRED"
            and getattr(ast_anchor, "scalar_count", None)
            == len(parsed_anchor_phrases[0].anchor_text or "")
            and 2 <= getattr(ast_anchor, "scalar_count", 0) <= 16
            and getattr(ast_anchor, "source_end", 0)
            - getattr(ast_anchor, "source_start", 0)
            == getattr(ast_anchor, "scalar_count", -1)
            and _valid_nonzero_sha256(
                getattr(ast_anchor, "anchor_text_sha256", None)
            )
            and gate_safe_boundary_green
        )
        raw_sources = (
            {
                value
                for value in (
                    projection.thought_text,
                    projection.action_text,
                )
                if value
            }
            if projection is not None
            else set()
        )
        decoded_body = body.decode("utf-8")
        raw_source_replay_green = bool(
            projection is not None
            and all(
                source not in decoded_body
                or (
                    len(source) <= 16
                    and len(parsed_anchor_phrases) == 1
                    and parsed_anchor_phrases[0].anchor_text == source
                    and decoded_body.count(source) == 1
                )
                for source in raw_sources
            )
        )
        fused_grammar = STEP11_SURFACE_CATALOG.get(
            "obligation_fused_grammar", {}
        )
        forbidden_fragments = fused_grammar.get(
            "forbidden_generated_fragments", []
        )
        forbidden_patterns = fused_grammar.get(
            "forbidden_generated_patterns", []
        )
        visible_contract_green = bool(
            type(forbidden_fragments) is list
            and type(forbidden_patterns) is list
            and all(type(row) is str for row in forbidden_fragments)
            and all(type(row) is str for row in forbidden_patterns)
            and not any(
                fragment.encode("utf-8") in body
                for fragment in forbidden_fragments
            )
            and not any(
                re.search(pattern, body.decode("utf-8")) is not None
                for pattern in forbidden_patterns
            )
            and all(
                row.introduced_reference is None
                and not row.compound_label_references
                and not row.relation_endpoint_references
                and not row.unknown_target_references
                and not row.reception_antecedent_references
                for row in witness.atoms
            )
            and grounded_contract_green
            and anchor_contract_green
        )
        checks["input_enumeration"] = bool(
            projection is not None
            and binding_verified
            and visible_contract_green
            and literal_fragments
            == tuple(
                phrase.anchor_text
                for phrase in parsed_anchor_phrases
                if phrase.anchor_text is not None
            )
            and len(unique_fragments) == 1
            and all(2 <= len(item) <= 16 for item in unique_fragments)
            and raw_source_replay_green
            and not any(
                row.form_id.startswith("relation_chain:")
                for row in witness.atoms
            )
            and not binding_issues
            & {
                "S11_MATCH_GROUNDED_PHRASE_ASSIGNMENT_AMBIGUOUS",
                "S11_MATCH_GROUNDED_PHRASE_COVERAGE_MISMATCH",
                "S11_MATCH_GROUNDED_PHRASE_UNRESOLVED",
                "S11_MATCH_LITERAL_OWNER_BUDGET_EXCEEDED",
                "S11_MATCH_LITERAL_SOURCE_RANGE_INVALID",
                "S11_MATCH_RAW_INPUT_REPLAY_FORBIDDEN",
                "S11_MATCH_VISIBLE_SOURCE_ANCHOR_COUNT_INVALID",
                "S11_MATCH_VISIBLE_SOURCE_ANCHOR_BOUNDARY_INVALID",
                "S11_MATCH_VISIBLE_SOURCE_ANCHOR_FAMILY_INVALID",
                "S11_MATCH_VISIBLE_SOURCE_ANCHOR_FAMILY_MISMATCH",
                "S11_MATCH_VISIBLE_SOURCE_ANCHOR_OWNER_INVALID",
                "S11_MATCH_VISIBLE_SOURCE_ANCHOR_RANGE_INVALID",
            }
        )
        semantic_signatures = tuple(
            (
                row.section_role,
                row.form_id,
                row.claim_kinds,
                row.source_fragments,
                tuple(
                    (
                        phrase.visible_feature_fingerprint_sha256,
                        phrase.phrase_profile_id,
                        phrase.action_lifecycle,
                        phrase.binding_family,
                        phrase.anchor_text,
                    )
                    for phrase in getattr(row, "grounded_phrases", ())
                ),
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
                row.form_id.startswith("reception:anaphoric:")
                and row.source_fragments == ()
                and row.introduced_reference is None
                and not row.compound_label_references
                and not row.relation_endpoint_references
                and not row.unknown_target_references
                and not row.reception_antecedent_references
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
                    "obligation_fused:",
                    "mixed_emotion:",
                    "mixed_emotion_compound:",
                    "mixed_emotion_relation:",
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
    attributes = _step11_selector_attributes(
        candidate_id=candidate_id,
        inventory_result=inventory_result,
        content_plan=content_plan,
        discourse_plan=(
            discourse_plan if type(discourse_plan) is dict else {}
        ),
        witness=witness,
        binding=binding,
        semantic_overlay=semantic_overlay,
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
            _surface_quality_key(result.selector_attributes),
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


# ---------------------------------------------------------------------------
# rc0028 runtime-disconnected experiment Hard Gate (append-only)
#
# The default rc0027 owner above remains byte-for-byte unchanged.  All imports
# of rc0028 forward/inverse APIs stay inside functions so importing the shared
# runtime does not load successor experiment owners transitively.

from dataclasses import dataclass as _rc0028_dataclass


STEP11_RC0028_EXPERIMENT_HARD_GATE_SCHEMA = (
    "cocolon.emlis.nls_v3.step11_rc0028_experiment_hard_gate.v1"
)
STEP11_RC0028_EXPERIMENT_SELECTION_SCHEMA = (
    "cocolon.emlis.nls_v3.step11_rc0028_experiment_selection.v1"
)
STEP11_RC0028_EXPERIMENT_CANDIDATE_LIMIT = 12
STEP11_RC0028_EXPERIMENT_REPLAN_LIMIT = 1

_STEP11_RC0028_CLOSED_CODE_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,127}$")


class Step11Rc0028ExperimentGateError(ValueError):
    """Fail-closed experiment error that never carries request text."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@_rc0028_dataclass(frozen=True, slots=True, repr=False)
class Step11Rc0028ExperimentGateResult:
    schema_version: str
    candidate_id: str
    candidate_version_id: str
    final_bytes_sha256: str | None
    parsed_witness_sha256: str | None
    verified_binding_sha256: str | None
    successor_snapshot_sha256: str | None
    experiment_catalog_sha256: str | None
    base_gate_failure_codes: tuple[str, ...]
    failure_codes: tuple[str, ...]
    hard_pass: bool
    semantic_coverage_authorized: bool
    replan_count: int | None
    experimental_only: bool = True
    runtime_connected: bool = False


@_rc0028_dataclass(frozen=True, slots=True, repr=False)
class Step11Rc0028ExperimentSelectionResult:
    schema_version: str
    candidate_version_id: str
    evaluated_candidate_ids: tuple[str, ...]
    gate_results: tuple[Step11Rc0028ExperimentGateResult, ...]
    selected_candidate_id: str | None
    selected_candidate: Any | None
    status: str
    bounded_candidate_limit: int
    bounded_replan_limit: int
    recovery_attempted: bool
    soft_rescue_used: bool
    experimental_only: bool = True
    runtime_connected: bool = False


def _step11_rc0028_closed_code(value: Any, fallback: str) -> str:
    if (
        type(value) is str
        and _STEP11_RC0028_CLOSED_CODE_RE.fullmatch(value) is not None
        and (
            value.startswith("STEP11_RC0028_")
            or value.startswith("S11_GATE")
        )
    ):
        return value
    return fallback


def _step11_rc0028_surface_contracts() -> tuple[Any, ...]:
    from emlis_ai_step11_natural_surface_v3 import (
        STEP11_RC0028_EXPERIMENT_CANDIDATE_VERSION_ID,
        Step11Rc0028ExperimentSurfaceCandidate,
        render_step11_rc0028_experiment_surface,
        validate_step11_rc0028_experiment_surface_candidate,
    )

    return (
        STEP11_RC0028_EXPERIMENT_CANDIDATE_VERSION_ID,
        Step11Rc0028ExperimentSurfaceCandidate,
        render_step11_rc0028_experiment_surface,
        validate_step11_rc0028_experiment_surface_candidate,
    )


def _step11_rc0028_inverse_contracts() -> tuple[Any, ...]:
    from emlis_ai_step11_natural_surface_matcher_v3 import (
        match_step11_rc0028_experiment_surface,
        parse_step11_rc0028_experiment_surface,
        step11_rc0028_experiment_parsed_witness_material,
        step11_rc0028_experiment_verified_binding_material,
    )

    return (
        parse_step11_rc0028_experiment_surface,
        match_step11_rc0028_experiment_surface,
        step11_rc0028_experiment_parsed_witness_material,
        step11_rc0028_experiment_verified_binding_material,
    )


def _step11_rc0028_gate_result_material(
    value: Step11Rc0028ExperimentGateResult,
) -> dict[str, Any]:
    if type(value) is not Step11Rc0028ExperimentGateResult:
        raise Step11Rc0028ExperimentGateError(
            "STEP11_RC0028_GATE_RESULT_TYPE_INVALID"
        )
    return {
        "schema_version": value.schema_version,
        "candidate_id": value.candidate_id,
        "candidate_version_id": value.candidate_version_id,
        "final_bytes_sha256": value.final_bytes_sha256,
        "parsed_witness_sha256": value.parsed_witness_sha256,
        "verified_binding_sha256": value.verified_binding_sha256,
        "successor_snapshot_sha256": value.successor_snapshot_sha256,
        "experiment_catalog_sha256": value.experiment_catalog_sha256,
        "base_gate_failure_codes": list(value.base_gate_failure_codes),
        "failure_codes": list(value.failure_codes),
        "hard_pass": value.hard_pass,
        "semantic_coverage_authorized": (
            value.semantic_coverage_authorized
        ),
        "replan_count": value.replan_count,
        "experimental_only": value.experimental_only,
        "runtime_connected": value.runtime_connected,
    }


def step11_rc0028_experiment_gate_result_material(
    value: Step11Rc0028ExperimentGateResult,
) -> dict[str, Any]:
    """Return a body-free, canonicalizable experiment gate receipt."""

    return _step11_rc0028_gate_result_material(value)


def step11_rc0028_experiment_selection_result_material(
    value: Step11Rc0028ExperimentSelectionResult,
) -> dict[str, Any]:
    """Return a body-free selection receipt without the selected candidate."""

    if type(value) is not Step11Rc0028ExperimentSelectionResult:
        raise Step11Rc0028ExperimentGateError(
            "STEP11_RC0028_SELECTION_RESULT_TYPE_INVALID"
        )
    return {
        "schema_version": value.schema_version,
        "candidate_version_id": value.candidate_version_id,
        "evaluated_candidate_ids": list(value.evaluated_candidate_ids),
        "gate_results": [
            _step11_rc0028_gate_result_material(row)
            for row in value.gate_results
        ],
        "selected_candidate_id": value.selected_candidate_id,
        "status": value.status,
        "bounded_candidate_limit": value.bounded_candidate_limit,
        "bounded_replan_limit": value.bounded_replan_limit,
        "recovery_attempted": value.recovery_attempted,
        "soft_rescue_used": value.soft_rescue_used,
        "experimental_only": value.experimental_only,
        "runtime_connected": value.runtime_connected,
    }


def _step11_rc0028_result(
    *,
    candidate_id: str,
    candidate_version_id: str,
    final_bytes_sha256: str | None,
    parsed_witness_sha256: str | None,
    verified_binding_sha256: str | None,
    successor_snapshot_sha256: str | None,
    experiment_catalog_sha256: str | None,
    base_gate_failure_codes: Sequence[str],
    failure_codes: Sequence[str],
    semantic_coverage_authorized: bool,
    replan_count: int | None,
) -> Step11Rc0028ExperimentGateResult:
    base_codes = tuple(
        sorted(
            {
                _step11_rc0028_closed_code(
                    value,
                    "STEP11_RC0028_BASE_GATE_REJECTED",
                )
                for value in base_gate_failure_codes
            }
        )
    )
    codes = tuple(
        sorted(
            {
                _step11_rc0028_closed_code(
                    value,
                    "STEP11_RC0028_UNCLOSED_FAILURE_CODE",
                )
                for value in (*failure_codes, *base_codes)
            }
        )
    )
    return Step11Rc0028ExperimentGateResult(
        schema_version=STEP11_RC0028_EXPERIMENT_HARD_GATE_SCHEMA,
        candidate_id=candidate_id,
        candidate_version_id=candidate_version_id,
        final_bytes_sha256=final_bytes_sha256,
        parsed_witness_sha256=parsed_witness_sha256,
        verified_binding_sha256=verified_binding_sha256,
        successor_snapshot_sha256=successor_snapshot_sha256,
        experiment_catalog_sha256=experiment_catalog_sha256,
        base_gate_failure_codes=base_codes,
        failure_codes=codes,
        hard_pass=not codes,
        semantic_coverage_authorized=semantic_coverage_authorized,
        replan_count=replan_count,
    )


def evaluate_step11_rc0028_experiment_candidate(
    candidate: Any,
    *,
    successor_snapshot: Any,
    lexical_atom_specs: Any,
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
    current_input: Mapping[str, Any],
) -> Step11Rc0028ExperimentGateResult:
    """Fail closed across exact forward, inverse, and source commitments."""

    candidate_id = ""
    candidate_version_id = ""
    final_bytes_sha256: str | None = None
    parsed_witness_sha256: str | None = None
    verified_binding_sha256: str | None = None
    successor_snapshot_sha256 = getattr(
        successor_snapshot,
        "experiment_snapshot_sha256",
        None,
    )
    if type(successor_snapshot_sha256) is not str:
        successor_snapshot_sha256 = None
    experiment_catalog_sha256: str | None = None
    semantic_coverage_authorized = False
    replan_count: int | None = None
    base_gate_failure_codes: tuple[str, ...] = ()
    failure_codes: list[str] = []

    try:
        (
            expected_version,
            candidate_type,
            render_surface,
            validate_candidate,
        ) = _step11_rc0028_surface_contracts()
    except Exception:
        failure_codes.append("STEP11_RC0028_FORWARD_OWNER_UNAVAILABLE")
        return _step11_rc0028_result(
            candidate_id=candidate_id,
            candidate_version_id=candidate_version_id,
            final_bytes_sha256=final_bytes_sha256,
            parsed_witness_sha256=parsed_witness_sha256,
            verified_binding_sha256=verified_binding_sha256,
            successor_snapshot_sha256=successor_snapshot_sha256,
            experiment_catalog_sha256=experiment_catalog_sha256,
            base_gate_failure_codes=base_gate_failure_codes,
            failure_codes=failure_codes,
            semantic_coverage_authorized=semantic_coverage_authorized,
            replan_count=replan_count,
        )

    if type(candidate) is not candidate_type:
        failure_codes.append("STEP11_RC0028_CANDIDATE_TYPE_INVALID")
        return _step11_rc0028_result(
            candidate_id=candidate_id,
            candidate_version_id=candidate_version_id,
            final_bytes_sha256=final_bytes_sha256,
            parsed_witness_sha256=parsed_witness_sha256,
            verified_binding_sha256=verified_binding_sha256,
            successor_snapshot_sha256=successor_snapshot_sha256,
            experiment_catalog_sha256=experiment_catalog_sha256,
            base_gate_failure_codes=base_gate_failure_codes,
            failure_codes=failure_codes,
            semantic_coverage_authorized=semantic_coverage_authorized,
            replan_count=replan_count,
        )

    candidate_id = (
        candidate.candidate_id
        if type(candidate.candidate_id) is str
        else ""
    )
    candidate_version_id = (
        candidate.candidate_version_id
        if type(candidate.candidate_version_id) is str
        else ""
    )
    experiment_catalog_sha256 = (
        candidate.experiment_catalog_sha256
        if type(candidate.experiment_catalog_sha256) is str
        else None
    )
    semantic_coverage_authorized = (
        candidate.semantic_coverage_authorized
        if type(candidate.semantic_coverage_authorized) is bool
        else True
    )
    replan_count = (
        candidate.replan_count
        if type(candidate.replan_count) is int
        and type(candidate.replan_count) is not bool
        else None
    )
    try:
        body = candidate.final_utf8_bytes
    except Exception:
        body = None
    if type(body) is bytes:
        final_bytes_sha256 = hashlib.sha256(body).hexdigest()
    else:
        failure_codes.append("STEP11_RC0028_FINAL_BYTES_COMMITMENT_MISMATCH")

    if not candidate_id:
        failure_codes.append("STEP11_RC0028_CANDIDATE_ID_INVALID")
    if candidate_version_id != expected_version:
        failure_codes.append("STEP11_RC0028_ARTIFACT_COMMITMENT_MISMATCH")
    if (
        type(candidate.semantic_coverage_authorized) is not bool
        or candidate.semantic_coverage_authorized is not False
        or type(
            getattr(successor_snapshot, "semantic_coverage_authorized", None)
        )
        is not bool
        or successor_snapshot.semantic_coverage_authorized is not False
    ):
        failure_codes.append("STEP11_RC0028_SEMANTIC_COVERAGE_SELF_CLAIM")
    if replan_count is None or not 0 <= replan_count <= 1:
        failure_codes.append("STEP11_RC0028_REPLAN_BOUND_EXCEEDED")
    if (
        candidate.experimental_only is not True
        or candidate.runtime_connected is not False
        or getattr(successor_snapshot, "experimental_only", None) is not True
        or getattr(successor_snapshot, "runtime_connected", None) is not False
    ):
        failure_codes.append("STEP11_RC0028_RUNTIME_BOUNDARY_INVALID")
    if (
        successor_snapshot_sha256 is None
        or candidate.successor_snapshot_sha256
        != successor_snapshot_sha256
    ):
        failure_codes.append("STEP11_RC0028_SOURCE_COMMITMENT_MISMATCH")

    try:
        forward_issues = validate_candidate(
            candidate,
            successor_snapshot=successor_snapshot,
            lexical_atom_specs=lexical_atom_specs,
        )
    except Exception:
        forward_issues = (
            "STEP11_RC0028_CANDIDATE_REVALIDATION_FAILED",
        )
    if type(forward_issues) not in {tuple, list}:
        forward_issues = (
            "STEP11_RC0028_CANDIDATE_REVALIDATION_FAILED",
        )
    failure_codes.extend(
        _step11_rc0028_closed_code(
            value,
            "STEP11_RC0028_CANDIDATE_REVALIDATION_FAILED",
        )
        for value in forward_issues
    )

    try:
        rerendered = render_surface(
            candidate.base_candidate.final_utf8_bytes,
            construction_atoms=candidate.construction_atoms,
            relation_atoms=candidate.relation_atoms,
            semantic_link_atoms=candidate.semantic_link_atoms,
            explicit_unknown_atoms=candidate.explicit_unknown_atoms,
        )
        if (
            rerendered != candidate.rendered_surface
            or type(body) is not bytes
            or rerendered.utf8_bytes != body
            or rerendered.sha256 != final_bytes_sha256
        ):
            failure_codes.append(
                "STEP11_RC0028_FINAL_BYTES_COMMITMENT_MISMATCH"
            )
    except Exception:
        failure_codes.append("STEP11_RC0028_FINAL_BYTES_COMMITMENT_MISMATCH")

    try:
        base_result = evaluate_step11_natural_surface_candidate(
            candidate.base_candidate,
            inventory_result=inventory_result,
            content_plan=content_plan,
            current_input=current_input,
        )
        base_gate_failure_codes = tuple(base_result.failure_codes)
        if not base_result.hard_pass:
            failure_codes.append("STEP11_RC0028_BASE_GATE_REJECTED")
    except Exception:
        failure_codes.append("STEP11_RC0028_BASE_GATE_EVALUATION_FAILED")

    parsed_witness = None
    verified_binding = None
    try:
        (
            parse_surface,
            match_surface,
            parsed_material,
            binding_material,
        ) = _step11_rc0028_inverse_contracts()
        if type(body) is not bytes:
            raise Step11Rc0028ExperimentGateError(
                "STEP11_RC0028_FINAL_BYTES_COMMITMENT_MISMATCH"
            )
        # Deliberately pass final bytes only.  Candidate AST, metadata, covered
        # IDs, and generator span maps are not visible to the Parser.
        parsed_witness = parse_surface(body)
        parsed_witness_sha256 = artifact_sha256(
            parsed_material(parsed_witness)
        )
    except Exception as error:
        failure_codes.append(
            _step11_rc0028_closed_code(
                getattr(error, "code", None),
                "STEP11_RC0028_PARSE_FAILED",
            )
        )

    if parsed_witness is not None:
        if getattr(parsed_witness, "body_sha256", None) != final_bytes_sha256:
            failure_codes.append(
                "STEP11_RC0028_FINAL_BYTES_COMMITMENT_MISMATCH"
            )
        if (
            getattr(parsed_witness, "experiment_catalog_sha256", None)
            != experiment_catalog_sha256
        ):
            failure_codes.append("STEP11_RC0028_CATALOG_COMMITMENT_MISMATCH")
        try:
            # The Matcher receives only the inverse witness and frozen source
            # authority.  It cannot consume forward atoms or candidate claims.
            verified_binding = match_surface(
                parsed_witness,
                successor_snapshot=successor_snapshot,
            )
            verified_binding_sha256 = artifact_sha256(
                binding_material(verified_binding)
            )
        except Exception as error:
            failure_codes.append(
                _step11_rc0028_closed_code(
                    getattr(error, "code", None),
                    "STEP11_RC0028_MATCH_FAILED",
                )
            )

    if verified_binding is not None:
        binding_issues = getattr(verified_binding, "issue_codes", None)
        if type(binding_issues) is not tuple:
            failure_codes.append("STEP11_RC0028_BINDING_NOT_VERIFIED")
            binding_issues = ()
        failure_codes.extend(
            _step11_rc0028_closed_code(
                value,
                "STEP11_RC0028_BINDING_NOT_VERIFIED",
            )
            for value in binding_issues
        )
        if getattr(verified_binding, "hard_verified", None) is not True:
            failure_codes.append("STEP11_RC0028_BINDING_NOT_VERIFIED")
        if (
            getattr(verified_binding, "parsed_witness_sha256", None)
            != parsed_witness_sha256
        ):
            failure_codes.append("STEP11_RC0028_ARTIFACT_COMMITMENT_MISMATCH")
        if (
            getattr(verified_binding, "successor_snapshot_sha256", None)
            != successor_snapshot_sha256
        ):
            failure_codes.append("STEP11_RC0028_SOURCE_COMMITMENT_MISMATCH")
        if (
            getattr(verified_binding, "experiment_catalog_sha256", None)
            != experiment_catalog_sha256
        ):
            failure_codes.append("STEP11_RC0028_CATALOG_COMMITMENT_MISMATCH")

    lexical_specs_sha256 = getattr(lexical_atom_specs, "specs_sha256", None)
    if (
        type(lexical_specs_sha256) is str
        and candidate.lexical_atom_specs_sha256 != lexical_specs_sha256
    ):
        failure_codes.append("STEP11_RC0028_ARTIFACT_COMMITMENT_MISMATCH")

    return _step11_rc0028_result(
        candidate_id=candidate_id,
        candidate_version_id=candidate_version_id,
        final_bytes_sha256=final_bytes_sha256,
        parsed_witness_sha256=parsed_witness_sha256,
        verified_binding_sha256=verified_binding_sha256,
        successor_snapshot_sha256=successor_snapshot_sha256,
        experiment_catalog_sha256=experiment_catalog_sha256,
        base_gate_failure_codes=base_gate_failure_codes,
        failure_codes=failure_codes,
        semantic_coverage_authorized=semantic_coverage_authorized,
        replan_count=replan_count,
    )


def select_step11_rc0028_experiment_candidate(
    candidates: Sequence[Any],
    *,
    successor_snapshot: Any,
    lexical_atom_specs: Any,
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
    current_input: Mapping[str, Any],
    candidate_limit: int = STEP11_RC0028_EXPERIMENT_CANDIDATE_LIMIT,
    replan_limit: int = STEP11_RC0028_EXPERIMENT_REPLAN_LIMIT,
) -> Step11Rc0028ExperimentSelectionResult:
    """Select the first hard-pass candidate in candidate-ID order only."""

    if type(candidates) not in {list, tuple} or not candidates:
        raise Step11Rc0028ExperimentGateError(
            "STEP11_RC0028_CANDIDATE_SET_INVALID"
        )
    if (
        type(candidate_limit) is not int
        or type(candidate_limit) is bool
        or not 1 <= candidate_limit <= STEP11_RC0028_EXPERIMENT_CANDIDATE_LIMIT
        or len(candidates) > candidate_limit
        or len(candidates) > STEP11_RC0028_EXPERIMENT_CANDIDATE_LIMIT
    ):
        raise Step11Rc0028ExperimentGateError(
            "STEP11_RC0028_CANDIDATE_BOUND_EXCEEDED"
        )
    if (
        type(replan_limit) is not int
        or type(replan_limit) is bool
        or not 0 <= replan_limit <= STEP11_RC0028_EXPERIMENT_REPLAN_LIMIT
    ):
        raise Step11Rc0028ExperimentGateError(
            "STEP11_RC0028_REPLAN_BOUND_EXCEEDED"
        )

    try:
        expected_version, candidate_type, _render, _validate = (
            _step11_rc0028_surface_contracts()
        )
    except Exception as error:
        raise Step11Rc0028ExperimentGateError(
            "STEP11_RC0028_FORWARD_OWNER_UNAVAILABLE"
        ) from error
    if any(type(row) is not candidate_type for row in candidates):
        raise Step11Rc0028ExperimentGateError(
            "STEP11_RC0028_CANDIDATE_TYPE_INVALID"
        )
    if any(
        type(row.candidate_id) is not str or not row.candidate_id
        for row in candidates
    ):
        raise Step11Rc0028ExperimentGateError(
            "STEP11_RC0028_CANDIDATE_ID_INVALID"
        )
    ordered = tuple(sorted(candidates, key=lambda row: row.candidate_id))
    candidate_ids = tuple(row.candidate_id for row in ordered)
    if len(set(candidate_ids)) != len(candidate_ids):
        raise Step11Rc0028ExperimentGateError(
            "STEP11_RC0028_CANDIDATE_ID_INVALID"
        )
    if any(
        type(row.replan_count) is not int
        or type(row.replan_count) is bool
        or not 0 <= row.replan_count <= replan_limit
        for row in ordered
    ):
        raise Step11Rc0028ExperimentGateError(
            "STEP11_RC0028_REPLAN_BOUND_EXCEEDED"
        )

    results = tuple(
        evaluate_step11_rc0028_experiment_candidate(
            row,
            successor_snapshot=successor_snapshot,
            lexical_atom_specs=lexical_atom_specs,
            inventory_result=inventory_result,
            content_plan=content_plan,
            current_input=current_input,
        )
        for row in ordered
    )
    selected = next(
        (
            candidate
            for candidate, result in zip(ordered, results)
            if result.hard_pass
        ),
        None,
    )
    return Step11Rc0028ExperimentSelectionResult(
        schema_version=STEP11_RC0028_EXPERIMENT_SELECTION_SCHEMA,
        candidate_version_id=expected_version,
        evaluated_candidate_ids=candidate_ids,
        gate_results=results,
        selected_candidate_id=(
            selected.candidate_id if selected is not None else None
        ),
        selected_candidate=selected,
        status=(
            "selected"
            if selected is not None
            else "rc0028_experiment_no_valid_candidate"
        ),
        bounded_candidate_limit=candidate_limit,
        bounded_replan_limit=replan_limit,
        recovery_attempted=False,
        soft_rescue_used=False,
    )


def select_step11_rc0028_experiment_candidates(
    candidates: Sequence[Any],
    *,
    successor_snapshot: Any,
    lexical_atom_specs: Any,
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
    current_input: Mapping[str, Any],
    candidate_limit: int = STEP11_RC0028_EXPERIMENT_CANDIDATE_LIMIT,
    replan_limit: int = STEP11_RC0028_EXPERIMENT_REPLAN_LIMIT,
) -> Step11Rc0028ExperimentSelectionResult:
    """Plural compatibility name frozen by the E0b RED contract."""

    return select_step11_rc0028_experiment_candidate(
        candidates,
        successor_snapshot=successor_snapshot,
        lexical_atom_specs=lexical_atom_specs,
        inventory_result=inventory_result,
        content_plan=content_plan,
        current_input=current_input,
        candidate_limit=candidate_limit,
        replan_limit=replan_limit,
    )


__all__ += [
    "STEP11_RC0028_EXPERIMENT_CANDIDATE_LIMIT",
    "STEP11_RC0028_EXPERIMENT_HARD_GATE_SCHEMA",
    "STEP11_RC0028_EXPERIMENT_REPLAN_LIMIT",
    "STEP11_RC0028_EXPERIMENT_SELECTION_SCHEMA",
    "Step11Rc0028ExperimentGateError",
    "Step11Rc0028ExperimentGateResult",
    "Step11Rc0028ExperimentSelectionResult",
    "evaluate_step11_rc0028_experiment_candidate",
    "select_step11_rc0028_experiment_candidate",
    "select_step11_rc0028_experiment_candidates",
    "step11_rc0028_experiment_gate_result_material",
    "step11_rc0028_experiment_selection_result_material",
]


# ---------------------------------------------------------------------------
# rc0029 runtime-disconnected common-Surface repair Hard Gate (append-only)
#
# rc0027 and rc0028 entry points above are frozen predecessors.  Project
# imports for this successor remain local so importing the default hard gate
# cannot connect the experiment catalog/runtime to a shared or public route.

STEP11_RC0029_EXPERIMENT_HARD_GATE_SCHEMA = (
    "cocolon.emlis.nls_v3.step11_rc0029_experiment_hard_gate.v1"
)
STEP11_RC0029_EXPERIMENT_SELECTION_SCHEMA = (
    "cocolon.emlis.nls_v3.step11_rc0029_experiment_selection.v1"
)
STEP11_RC0029_EXPERIMENT_CANDIDATE_LIMIT = 12
STEP11_RC0029_EXPERIMENT_REPLAN_LIMIT = 1

_STEP11_RC0029_CLOSED_CODE_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,127}$")


class Step11Rc0029ExperimentGateError(ValueError):
    """Fail closed with one body-free rc0029 machine code."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@_rc0028_dataclass(frozen=True, slots=True, repr=False)
class Step11Rc0029ExperimentGateResult:
    schema_version: str
    candidate_id: str
    candidate_version_id: str
    final_bytes_sha256: str | None
    parsed_witness_sha256: str | None
    verified_binding_sha256: str | None
    successor_snapshot_sha256: str | None
    experiment_catalog_sha256: str | None
    base_gate_failure_codes: tuple[str, ...]
    failure_codes: tuple[str, ...]
    hard_pass: bool
    semantic_coverage_authorized: bool
    replan_count: int | None
    experimental_only: bool = True
    runtime_connected: bool = False


@_rc0028_dataclass(frozen=True, slots=True, repr=False)
class Step11Rc0029ExperimentSelectionResult:
    schema_version: str
    candidate_version_id: str
    evaluated_candidate_ids: tuple[str, ...]
    gate_results: tuple[Step11Rc0029ExperimentGateResult, ...]
    selected_candidate_id: str | None
    selected_candidate: Any | None
    status: str
    bounded_candidate_limit: int
    bounded_replan_limit: int
    recovery_attempted: bool
    soft_rescue_used: bool
    experimental_only: bool = True
    runtime_connected: bool = False


def _step11_rc0029_closed_code(value: Any, fallback: str) -> str:
    if (
        type(value) is str
        and _STEP11_RC0029_CLOSED_CODE_RE.fullmatch(value) is not None
        and (
            value.startswith("STEP11_RC0029_")
            or value.startswith("S11_GATE")
        )
    ):
        return value
    return fallback


def _step11_rc0029_surface_contracts() -> tuple[Any, ...]:
    from emlis_ai_step11_natural_surface_v3 import (
        STEP11_RC0029_EXPERIMENT_CANDIDATE_VERSION_ID,
        Step11Rc0029ExperimentSurfaceCandidate,
        render_step11_rc0029_experiment_surface,
        validate_step11_rc0029_experiment_surface_candidate,
    )

    return (
        STEP11_RC0029_EXPERIMENT_CANDIDATE_VERSION_ID,
        Step11Rc0029ExperimentSurfaceCandidate,
        render_step11_rc0029_experiment_surface,
        validate_step11_rc0029_experiment_surface_candidate,
    )


def _step11_rc0029_inverse_contracts() -> tuple[Any, ...]:
    from emlis_ai_step11_natural_surface_matcher_v3 import (
        match_step11_rc0029_experiment_surface,
        parse_step11_rc0029_experiment_surface,
        step11_rc0029_experiment_parsed_witness_material,
        step11_rc0029_experiment_verified_binding_material,
    )

    return (
        parse_step11_rc0029_experiment_surface,
        match_step11_rc0029_experiment_surface,
        step11_rc0029_experiment_parsed_witness_material,
        step11_rc0029_experiment_verified_binding_material,
    )


def _step11_rc0029_gate_result_material(
    value: Step11Rc0029ExperimentGateResult,
) -> dict[str, Any]:
    if type(value) is not Step11Rc0029ExperimentGateResult:
        raise Step11Rc0029ExperimentGateError(
            "STEP11_RC0029_GATE_RESULT_TYPE_INVALID"
        )
    return {
        "schema_version": value.schema_version,
        "candidate_id": value.candidate_id,
        "candidate_version_id": value.candidate_version_id,
        "final_bytes_sha256": value.final_bytes_sha256,
        "parsed_witness_sha256": value.parsed_witness_sha256,
        "verified_binding_sha256": value.verified_binding_sha256,
        "successor_snapshot_sha256": value.successor_snapshot_sha256,
        "experiment_catalog_sha256": value.experiment_catalog_sha256,
        "base_gate_failure_codes": list(value.base_gate_failure_codes),
        "failure_codes": list(value.failure_codes),
        "hard_pass": value.hard_pass,
        "semantic_coverage_authorized": value.semantic_coverage_authorized,
        "replan_count": value.replan_count,
        "experimental_only": value.experimental_only,
        "runtime_connected": value.runtime_connected,
    }


def step11_rc0029_experiment_gate_result_material(
    value: Step11Rc0029ExperimentGateResult,
) -> dict[str, Any]:
    return _step11_rc0029_gate_result_material(value)


def step11_rc0029_experiment_selection_result_material(
    value: Step11Rc0029ExperimentSelectionResult,
) -> dict[str, Any]:
    if type(value) is not Step11Rc0029ExperimentSelectionResult:
        raise Step11Rc0029ExperimentGateError(
            "STEP11_RC0029_SELECTION_RESULT_TYPE_INVALID"
        )
    return {
        "schema_version": value.schema_version,
        "candidate_version_id": value.candidate_version_id,
        "evaluated_candidate_ids": list(value.evaluated_candidate_ids),
        "gate_results": [
            _step11_rc0029_gate_result_material(row)
            for row in value.gate_results
        ],
        "selected_candidate_id": value.selected_candidate_id,
        "status": value.status,
        "bounded_candidate_limit": value.bounded_candidate_limit,
        "bounded_replan_limit": value.bounded_replan_limit,
        "recovery_attempted": value.recovery_attempted,
        "soft_rescue_used": value.soft_rescue_used,
        "experimental_only": value.experimental_only,
        "runtime_connected": value.runtime_connected,
    }


def _step11_rc0029_result(
    *,
    candidate_id: str,
    candidate_version_id: str,
    final_bytes_sha256: str | None,
    parsed_witness_sha256: str | None,
    verified_binding_sha256: str | None,
    successor_snapshot_sha256: str | None,
    experiment_catalog_sha256: str | None,
    base_gate_failure_codes: Sequence[str],
    failure_codes: Sequence[str],
    semantic_coverage_authorized: bool,
    replan_count: int | None,
) -> Step11Rc0029ExperimentGateResult:
    base_codes = tuple(
        sorted(
            {
                _step11_rc0029_closed_code(
                    value, "STEP11_RC0029_BASE_GATE_REJECTED"
                )
                for value in base_gate_failure_codes
            }
        )
    )
    codes = tuple(
        sorted(
            {
                _step11_rc0029_closed_code(
                    value, "STEP11_RC0029_UNCLOSED_FAILURE_CODE"
                )
                for value in (*failure_codes, *base_codes)
            }
        )
    )
    return Step11Rc0029ExperimentGateResult(
        schema_version=STEP11_RC0029_EXPERIMENT_HARD_GATE_SCHEMA,
        candidate_id=candidate_id,
        candidate_version_id=candidate_version_id,
        final_bytes_sha256=final_bytes_sha256,
        parsed_witness_sha256=parsed_witness_sha256,
        verified_binding_sha256=verified_binding_sha256,
        successor_snapshot_sha256=successor_snapshot_sha256,
        experiment_catalog_sha256=experiment_catalog_sha256,
        base_gate_failure_codes=base_codes,
        failure_codes=codes,
        hard_pass=not codes,
        semantic_coverage_authorized=semantic_coverage_authorized,
        replan_count=replan_count,
    )


def evaluate_step11_rc0029_experiment_candidate(
    candidate: Any,
    *,
    successor_snapshot: Any,
    lexical_atom_specs: Any,
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
    current_input: Mapping[str, Any],
) -> Step11Rc0029ExperimentGateResult:
    """Join forward, final-byte inverse, and source commitments fail closed."""

    candidate_id = ""
    candidate_version_id = ""
    final_bytes_sha256: str | None = None
    parsed_witness_sha256: str | None = None
    verified_binding_sha256: str | None = None
    successor_snapshot_sha256 = getattr(
        successor_snapshot, "experiment_snapshot_sha256", None
    )
    if type(successor_snapshot_sha256) is not str:
        successor_snapshot_sha256 = None
    experiment_catalog_sha256: str | None = None
    semantic_coverage_authorized = False
    replan_count: int | None = None
    base_gate_failure_codes: tuple[str, ...] = ()
    failure_codes: list[str] = []

    try:
        expected_version, candidate_type, render_surface, validate_candidate = (
            _step11_rc0029_surface_contracts()
        )
    except Exception:
        failure_codes.append("STEP11_RC0029_FORWARD_OWNER_UNAVAILABLE")
        return _step11_rc0029_result(
            candidate_id=candidate_id,
            candidate_version_id=candidate_version_id,
            final_bytes_sha256=None,
            parsed_witness_sha256=None,
            verified_binding_sha256=None,
            successor_snapshot_sha256=successor_snapshot_sha256,
            experiment_catalog_sha256=None,
            base_gate_failure_codes=(),
            failure_codes=failure_codes,
            semantic_coverage_authorized=False,
            replan_count=None,
        )
    if type(candidate) is not candidate_type:
        failure_codes.append("STEP11_RC0029_CANDIDATE_TYPE_INVALID")
        return _step11_rc0029_result(
            candidate_id="",
            candidate_version_id="",
            final_bytes_sha256=None,
            parsed_witness_sha256=None,
            verified_binding_sha256=None,
            successor_snapshot_sha256=successor_snapshot_sha256,
            experiment_catalog_sha256=None,
            base_gate_failure_codes=(),
            failure_codes=failure_codes,
            semantic_coverage_authorized=False,
            replan_count=None,
        )

    candidate_id = candidate.candidate_id if type(candidate.candidate_id) is str else ""
    candidate_version_id = (
        candidate.candidate_version_id
        if type(candidate.candidate_version_id) is str
        else ""
    )
    experiment_catalog_sha256 = (
        candidate.experiment_catalog_sha256
        if type(candidate.experiment_catalog_sha256) is str
        else None
    )
    semantic_coverage_authorized = (
        candidate.semantic_coverage_authorized
        if type(candidate.semantic_coverage_authorized) is bool
        else True
    )
    replan_count = (
        candidate.replan_count
        if type(candidate.replan_count) is int
        and type(candidate.replan_count) is not bool
        else None
    )
    body = getattr(candidate, "final_utf8_bytes", None)
    if type(body) is bytes:
        final_bytes_sha256 = hashlib.sha256(body).hexdigest()
        base_body = getattr(candidate.base_candidate, "final_utf8_bytes", None)
        structural_rows = tuple(
            getattr(candidate, name, None)
            for name in (
                "construction_atoms",
                "relation_atoms",
                "semantic_link_atoms",
                "explicit_unknown_atoms",
            )
        )
        if (
            type(base_body) is bytes
            and body == base_body
            and any(type(rows) is tuple and rows for rows in structural_rows)
        ):
            failure_codes.append("STEP11_RC0029_REQUIRED_ATOM_MISSING")
    else:
        failure_codes.append("STEP11_RC0029_FINAL_BYTES_COMMITMENT_MISMATCH")

    if not candidate_id:
        failure_codes.append("STEP11_RC0029_CANDIDATE_ID_INVALID")
    if candidate_version_id != expected_version:
        failure_codes.append("STEP11_RC0029_ARTIFACT_COMMITMENT_MISMATCH")
    if (
        semantic_coverage_authorized is not False
        or getattr(successor_snapshot, "semantic_coverage_authorized", None)
        is not False
    ):
        failure_codes.append("STEP11_RC0029_SEMANTIC_COVERAGE_SELF_CLAIM")
    if replan_count is None or not 0 <= replan_count <= 1:
        failure_codes.append("STEP11_RC0029_REPLAN_BOUND_EXCEEDED")
    if (
        getattr(candidate, "experimental_only", None) is not True
        or getattr(candidate, "runtime_connected", None) is not False
        or getattr(successor_snapshot, "experimental_only", None) is not True
        or getattr(successor_snapshot, "runtime_connected", None) is not False
    ):
        failure_codes.append("STEP11_RC0029_RUNTIME_BOUNDARY_INVALID")
    if (
        successor_snapshot_sha256 is None
        or getattr(candidate, "successor_snapshot_sha256", None)
        != successor_snapshot_sha256
    ):
        failure_codes.append("STEP11_RC0029_SOURCE_COMMITMENT_MISMATCH")

    try:
        forward_issues = validate_candidate(
            candidate,
            successor_snapshot=successor_snapshot,
            lexical_atom_specs=lexical_atom_specs,
        )
    except Exception:
        forward_issues = ("STEP11_RC0029_CANDIDATE_REVALIDATION_FAILED",)
    if type(forward_issues) not in {tuple, list}:
        forward_issues = ("STEP11_RC0029_CANDIDATE_REVALIDATION_FAILED",)
    failure_codes.extend(
        _step11_rc0029_closed_code(
            value, "STEP11_RC0029_CANDIDATE_REVALIDATION_FAILED"
        )
        for value in forward_issues
    )

    # Canonical forward rerender must be identical.  The gate supplies only
    # typed candidate fields; inverse output never participates in rendering.
    try:
        rerendered = render_surface(
            candidate.base_candidate.final_utf8_bytes,
            natural_handle_specs=candidate.natural_handle_specs,
            construction_atoms=candidate.construction_atoms,
            relation_atoms=candidate.relation_atoms,
            semantic_link_atoms=candidate.semantic_link_atoms,
            explicit_unknown_atoms=candidate.explicit_unknown_atoms,
            fused_structure_groups=candidate.fused_structure_groups,
            reception_bindings=candidate.reception_bindings,
        )
        rendered = getattr(candidate, "rendered_surface", None)
        if (
            rerendered != rendered
            or getattr(rerendered, "utf8_bytes", None) != body
            or getattr(rerendered, "sha256", None) != final_bytes_sha256
        ):
            failure_codes.append(
                "STEP11_RC0029_FINAL_BYTES_COMMITMENT_MISMATCH"
            )
    except Exception:
        failure_codes.append("STEP11_RC0029_FINAL_BYTES_COMMITMENT_MISMATCH")

    try:
        base_result = evaluate_step11_natural_surface_candidate(
            candidate.base_candidate,
            inventory_result=inventory_result,
            content_plan=content_plan,
            current_input=current_input,
        )
        base_gate_failure_codes = tuple(base_result.failure_codes)
        if not base_result.hard_pass:
            failure_codes.append("STEP11_RC0029_BASE_GATE_REJECTED")
    except Exception:
        failure_codes.append("STEP11_RC0029_BASE_GATE_EVALUATION_FAILED")

    parsed_witness = None
    verified_binding = None
    try:
        parse_surface, match_surface, parsed_material, binding_material = (
            _step11_rc0029_inverse_contracts()
        )
        if type(body) is not bytes:
            raise Step11Rc0029ExperimentGateError(
                "STEP11_RC0029_FINAL_BYTES_COMMITMENT_MISMATCH"
            )
        parsed_witness = parse_surface(body)
        parsed_witness_sha256 = artifact_sha256(
            parsed_material(parsed_witness)
        )
    except Exception as error:
        failure_codes.append(
            _step11_rc0029_closed_code(
                getattr(error, "code", None), "STEP11_RC0029_PARSE_FAILED"
            )
        )
    if parsed_witness is not None:
        if getattr(parsed_witness, "body_sha256", None) != final_bytes_sha256:
            failure_codes.append(
                "STEP11_RC0029_FINAL_BYTES_COMMITMENT_MISMATCH"
            )
        if (
            getattr(parsed_witness, "experiment_catalog_sha256", None)
            != experiment_catalog_sha256
        ):
            failure_codes.append("STEP11_RC0029_CATALOG_COMMITMENT_MISMATCH")
        rendered = getattr(candidate, "rendered_surface", None)
        structural_rows = tuple(
            getattr(candidate, name, None)
            for name in (
                "construction_atoms",
                "relation_atoms",
                "semantic_link_atoms",
                "explicit_unknown_atoms",
            )
        )
        if any(type(rows) is not tuple for rows in structural_rows):
            failure_codes.append("STEP11_RC0029_REQUIRED_ATOM_MISSING")
        else:
            structural_atom_count = sum(len(rows) for rows in structural_rows)
            nonempty_family_count = sum(bool(rows) for rows in structural_rows)
            parsed_item_count = getattr(
                parsed_witness, "fused_structure_item_count", None
            )
            rendered_item_count = getattr(
                rendered, "fused_structure_item_count", None
            )
            if (
                parsed_item_count != nonempty_family_count
                or rendered_item_count != nonempty_family_count
                or (
                    structural_atom_count > nonempty_family_count
                    and not rendered_item_count < structural_atom_count
                )
            ):
                failure_codes.append(
                    "STEP11_RC0029_STRUCTURE_DEPTH_EXCEEDED"
                )
        candidate_groups = getattr(candidate, "fused_structure_groups", None)
        parsed_group_count = getattr(
            parsed_witness, "fused_structure_group_count", None
        )
        rendered_group_count = getattr(
            rendered, "fused_structure_group_count", None
        )
        if (
            type(candidate_groups) is not tuple
            or parsed_group_count != len(candidate_groups)
            or rendered_group_count != len(candidate_groups)
        ):
            failure_codes.append(
                "STEP11_RC0029_FUSED_GROUP_COMMITMENT_MISMATCH"
            )
        candidate_receptions = getattr(candidate, "reception_bindings", None)
        parsed_receptions = getattr(
            parsed_witness, "reception_bindings", None
        )
        if (
            type(candidate_receptions) is not tuple
            or type(parsed_receptions) is not tuple
            or len(parsed_receptions) != len(candidate_receptions)
            or getattr(rendered, "reception_binding_count", None)
            != len(candidate_receptions)
        ):
            failure_codes.append(
                "STEP11_RC0029_RECEPTION_CARDINALITY_MISMATCH"
            )
        if (
            getattr(parsed_witness, "added_observation_line_count", None) != 0
            or getattr(rendered, "added_observation_line_count", None) != 0
        ):
            failure_codes.append("STEP11_RC0029_SURFACE_LAYOUT_INVALID")
        try:
            verified_binding = match_surface(
                parsed_witness, successor_snapshot=successor_snapshot
            )
            verified_binding_sha256 = artifact_sha256(
                binding_material(verified_binding)
            )
        except Exception as error:
            failure_codes.append(
                _step11_rc0029_closed_code(
                    getattr(error, "code", None),
                    "STEP11_RC0029_MATCH_FAILED",
                )
            )
    if verified_binding is not None:
        failure_codes.extend(
            _step11_rc0029_closed_code(
                code, "STEP11_RC0029_BINDING_NOT_VERIFIED"
            )
            for code in getattr(verified_binding, "issue_codes", ())
        )
        if getattr(verified_binding, "hard_verified", None) is not True:
            failure_codes.append("STEP11_RC0029_BINDING_NOT_VERIFIED")
        for actual, expected, code in (
            (
                getattr(verified_binding, "parsed_witness_sha256", None),
                parsed_witness_sha256,
                "STEP11_RC0029_ARTIFACT_COMMITMENT_MISMATCH",
            ),
            (
                getattr(verified_binding, "successor_snapshot_sha256", None),
                successor_snapshot_sha256,
                "STEP11_RC0029_SOURCE_COMMITMENT_MISMATCH",
            ),
            (
                getattr(verified_binding, "experiment_catalog_sha256", None),
                experiment_catalog_sha256,
                "STEP11_RC0029_CATALOG_COMMITMENT_MISMATCH",
            ),
        ):
            if actual != expected:
                failure_codes.append(code)

    lexical_specs_sha256 = getattr(lexical_atom_specs, "specs_sha256", None)
    if (
        type(lexical_specs_sha256) is str
        and getattr(candidate, "lexical_atom_specs_sha256", None)
        != lexical_specs_sha256
    ):
        failure_codes.append("STEP11_RC0029_ARTIFACT_COMMITMENT_MISMATCH")

    return _step11_rc0029_result(
        candidate_id=candidate_id,
        candidate_version_id=candidate_version_id,
        final_bytes_sha256=final_bytes_sha256,
        parsed_witness_sha256=parsed_witness_sha256,
        verified_binding_sha256=verified_binding_sha256,
        successor_snapshot_sha256=successor_snapshot_sha256,
        experiment_catalog_sha256=experiment_catalog_sha256,
        base_gate_failure_codes=base_gate_failure_codes,
        failure_codes=failure_codes,
        semantic_coverage_authorized=semantic_coverage_authorized,
        replan_count=replan_count,
    )


def select_step11_rc0029_experiment_candidate(
    candidates: Sequence[Any],
    *,
    successor_snapshot: Any,
    lexical_atom_specs: Any,
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
    current_input: Mapping[str, Any],
    candidate_limit: int = STEP11_RC0029_EXPERIMENT_CANDIDATE_LIMIT,
    replan_limit: int = STEP11_RC0029_EXPERIMENT_REPLAN_LIMIT,
) -> Step11Rc0029ExperimentSelectionResult:
    if type(candidates) not in {list, tuple} or not candidates:
        raise Step11Rc0029ExperimentGateError(
            "STEP11_RC0029_CANDIDATE_SET_INVALID"
        )
    if (
        type(candidate_limit) is not int
        or type(candidate_limit) is bool
        or not 1 <= candidate_limit <= STEP11_RC0029_EXPERIMENT_CANDIDATE_LIMIT
        or len(candidates) > candidate_limit
    ):
        raise Step11Rc0029ExperimentGateError(
            "STEP11_RC0029_CANDIDATE_BOUND_EXCEEDED"
        )
    if (
        type(replan_limit) is not int
        or type(replan_limit) is bool
        or not 0 <= replan_limit <= STEP11_RC0029_EXPERIMENT_REPLAN_LIMIT
    ):
        raise Step11Rc0029ExperimentGateError(
            "STEP11_RC0029_REPLAN_BOUND_EXCEEDED"
        )
    try:
        expected_version, candidate_type, _render, _validate = (
            _step11_rc0029_surface_contracts()
        )
    except Exception as error:
        raise Step11Rc0029ExperimentGateError(
            "STEP11_RC0029_FORWARD_OWNER_UNAVAILABLE"
        ) from error
    if any(type(row) is not candidate_type for row in candidates):
        raise Step11Rc0029ExperimentGateError(
            "STEP11_RC0029_CANDIDATE_TYPE_INVALID"
        )
    ordered = tuple(sorted(candidates, key=lambda row: row.candidate_id))
    candidate_ids = tuple(row.candidate_id for row in ordered)
    if (
        any(type(value) is not str or not value for value in candidate_ids)
        or len(set(candidate_ids)) != len(candidate_ids)
        or any(
            type(row.replan_count) is not int
            or type(row.replan_count) is bool
            or not 0 <= row.replan_count <= replan_limit
            for row in ordered
        )
    ):
        raise Step11Rc0029ExperimentGateError(
            "STEP11_RC0029_CANDIDATE_ID_OR_REPLAN_INVALID"
        )
    results = tuple(
        evaluate_step11_rc0029_experiment_candidate(
            row,
            successor_snapshot=successor_snapshot,
            lexical_atom_specs=lexical_atom_specs,
            inventory_result=inventory_result,
            content_plan=content_plan,
            current_input=current_input,
        )
        for row in ordered
    )
    selected = next(
        (
            candidate
            for candidate, result in zip(ordered, results)
            if result.hard_pass
        ),
        None,
    )
    return Step11Rc0029ExperimentSelectionResult(
        schema_version=STEP11_RC0029_EXPERIMENT_SELECTION_SCHEMA,
        candidate_version_id=expected_version,
        evaluated_candidate_ids=candidate_ids,
        gate_results=results,
        selected_candidate_id=(
            selected.candidate_id if selected is not None else None
        ),
        selected_candidate=selected,
        status=(
            "selected"
            if selected is not None
            else "rc0029_experiment_no_valid_candidate"
        ),
        bounded_candidate_limit=candidate_limit,
        bounded_replan_limit=replan_limit,
        recovery_attempted=False,
        soft_rescue_used=False,
    )


def select_step11_rc0029_experiment_candidates(
    candidates: Sequence[Any],
    **kwargs: Any,
) -> Step11Rc0029ExperimentSelectionResult:
    return select_step11_rc0029_experiment_candidate(candidates, **kwargs)


__all__ += [
    "STEP11_RC0029_EXPERIMENT_CANDIDATE_LIMIT",
    "STEP11_RC0029_EXPERIMENT_HARD_GATE_SCHEMA",
    "STEP11_RC0029_EXPERIMENT_REPLAN_LIMIT",
    "STEP11_RC0029_EXPERIMENT_SELECTION_SCHEMA",
    "Step11Rc0029ExperimentGateError",
    "Step11Rc0029ExperimentGateResult",
    "Step11Rc0029ExperimentSelectionResult",
    "evaluate_step11_rc0029_experiment_candidate",
    "select_step11_rc0029_experiment_candidate",
    "select_step11_rc0029_experiment_candidates",
    "step11_rc0029_experiment_gate_result_material",
    "step11_rc0029_experiment_selection_result_material",
]


# ---------------------------------------------------------------------------
# rc0030 runtime-disconnected Surface-planning Hard Gate (append-only P4)
#
# The preceding 129,756 bytes are the immutable rc0027/rc0028/rc0029 owner.
# All project imports below remain function-local.  In particular, importing
# the default Hard Gate cannot load the rc0030 forward, inverse, catalog, or
# runtime owners and cannot connect this experiment to a shared/public route.

import weakref as _step11_rc0030_weakref


STEP11_RC0030_EXPERIMENT_BASE_INVERSE_CONTEXT_SCHEMA = (
    "cocolon.emlis.nls_v3.step11.rc0030_base_inverse_context.v1"
)
STEP11_RC0030_EXPERIMENT_BASE_INVERSE_EVALUATION_SCHEMA = (
    "cocolon.emlis.nls_v3.step11.rc0030_base_inverse_evaluation.v1"
)
STEP11_RC0030_EXPERIMENT_GATE_VERIFIED_BINDING_SCHEMA = (
    "cocolon.emlis.nls_v3.step11.rc0030_gate_verified_binding.v1"
)
STEP11_RC0030_EXPERIMENT_HARD_GATE_SCHEMA = (
    "cocolon.emlis.nls_v3.step11.rc0030_experiment_hard_gate.v1"
)
STEP11_RC0030_EXPERIMENT_GATE_EVALUATION_SCHEMA = (
    "cocolon.emlis.nls_v3.step11.rc0030_gate_evaluation.v1"
)
STEP11_RC0030_EXPERIMENT_SELECTION_SCHEMA = (
    "cocolon.emlis.nls_v3.step11.rc0030_experiment_selection.v1"
)
STEP11_RC0030_EXPERIMENT_CANDIDATE_LIMIT = 12
STEP11_RC0030_EXPERIMENT_REPLAN_LIMIT = 1
STEP11_RC0030_PARSER_INVOCATION_PER_CANDIDATE_LIMIT = 2
STEP11_RC0030_MATCHER_INVOCATION_PER_CANDIDATE_LIMIT = 2
STEP11_RC0030_PARSER_INVOCATION_ACROSS_CANDIDATES_LIMIT = 24
STEP11_RC0030_BODY_BYTE_INSPECTION_ACROSS_CANDIDATES_LIMIT = 48_000_000
STEP11_RC0030_BODY_BYTE_LIMIT = 1_000_000

_STEP11_RC0030_CLOSED_CODE_RE = re.compile(
    r"^(?:STEP11_RC0030_[A-Z0-9_]{2,111}|S11_GATE[A-Z0-9_]{0,120})$"
)
_STEP11_RC0030_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class Step11Rc0030ExperimentGateError(ValueError):
    """Fail closed with one body-free rc0030 machine code."""

    def __init__(self, code: str) -> None:
        if (
            type(code) is not str
            or re.fullmatch(r"STEP11_RC0030_[A-Z0-9_]{2,111}", code)
            is None
        ):
            code = "STEP11_RC0030_GATE_REJECTED"
        self.code = code
        super().__init__(code)


@_rc0028_dataclass(frozen=True, slots=True, repr=False, weakref_slot=True)
class Step11Rc0030ExperimentBaseInverseContext:
    schema_version: str
    context_sha256: str
    source_base_candidate_id: str
    base_surface_sha256: str
    base_body_byte_count: int
    successor_snapshot_sha256: str
    source_authority_sha256: str
    inventory_ledger_sha256: str
    content_plan_sha256: str
    discourse_plan_sha256: str
    current_input_sha256: str
    base_body_witness: Any
    verified_base_reuse_bindings: tuple[Any, ...]
    parser_invocation_count: int
    matcher_invocation_count: int
    body_scan_pass_count: int
    body_byte_inspection_count: int
    private_request_local: bool = True
    shareable: bool = False
    experimental_only: bool = True
    runtime_connected: bool = False
    body_free_export_allowed: bool = False


@_rc0028_dataclass(frozen=True, slots=True, repr=False, weakref_slot=True)
class Step11Rc0030ExperimentBaseInverseEvaluation:
    schema_version: str
    source_base_candidate_id: str
    base_surface_sha256: str | None
    base_body_byte_count: int
    base_inverse_context: Step11Rc0030ExperimentBaseInverseContext | None
    base_inverse_context_sha256: str | None
    failure_code: str | None
    failure_codes: tuple[str, ...]
    hard_pass: bool
    parser_invocation_count: int
    matcher_invocation_count: int
    charged_body_scan_pass_count: int
    body_byte_inspection_count: int
    private_request_local: bool = True
    shareable: bool = False
    experimental_only: bool = True
    runtime_connected: bool = False
    body_free_export_allowed: bool = False


@_rc0028_dataclass(frozen=True, slots=True, repr=False, weakref_slot=True)
class Step11Rc0030ExperimentGateVerifiedBinding:
    schema_version: str
    candidate_id: str
    parsed_witness_sha256: str
    verified_surface_binding_sha256: str
    base_witness_sha256: str
    successor_snapshot_sha256: str
    source_authority_sha256: str
    experiment_catalog_sha256: str
    base_leading_observation_match_count: int
    semantic_binding_count: int
    exact_reuse_count: int
    reception_binding_count: int
    parser_invocation_count: int
    matcher_invocation_count: int
    body_byte_inspection_count: int
    parsed_witness: Any
    verified_surface_binding: Any
    semantic_coverage_authorized: bool
    issue_codes: tuple[str, ...]
    hard_verified: bool
    body_free_export_allowed: bool = False


@_rc0028_dataclass(frozen=True, slots=True, repr=False)
class Step11Rc0030ExperimentGateResult:
    schema_version: str
    candidate_id: str
    candidate_version_id: str
    final_bytes_sha256: str | None
    surface_realization_plan_sha256: str | None
    parsed_witness_sha256: str | None
    verified_binding_sha256: str | None
    gate_verified_binding_sha256: str | None
    successor_snapshot_sha256: str | None
    source_authority_sha256: str | None
    experiment_catalog_sha256: str | None
    base_gate_failure_codes: tuple[str, ...]
    failure_codes: tuple[str, ...]
    hard_pass: bool
    semantic_coverage_authorized: bool
    base_leading_observation_match_count: int
    semantic_binding_count: int
    exact_reuse_count: int
    reception_binding_count: int
    parser_invocation_count: int
    matcher_invocation_count: int
    body_byte_inspection_count: int
    replan_count: int | None
    experimental_only: bool = True
    runtime_connected: bool = False


@_rc0028_dataclass(frozen=True, slots=True, repr=False)
class Step11Rc0030ExperimentGateEvaluation:
    schema_version: str
    gate_result: Step11Rc0030ExperimentGateResult
    parsed_witness: Any | None
    verified_binding: Step11Rc0030ExperimentGateVerifiedBinding | None
    private_request_local: bool = True
    shareable: bool = False
    experimental_only: bool = True
    runtime_connected: bool = False

    @property
    def candidate_id(self) -> str:
        return self.gate_result.candidate_id

    @property
    def failure_codes(self) -> tuple[str, ...]:
        return self.gate_result.failure_codes

    @property
    def hard_pass(self) -> bool:
        return self.gate_result.hard_pass


@_rc0028_dataclass(frozen=True, slots=True, repr=False)
class Step11Rc0030ExperimentSelectionResult:
    schema_version: str
    candidate_version_id: str
    evaluated_candidate_ids: tuple[str, ...]
    gate_results: tuple[Step11Rc0030ExperimentGateResult, ...]
    gate_evaluations: tuple[Step11Rc0030ExperimentGateEvaluation, ...]
    selected_candidate_id: str | None
    selected_candidate: Any | None
    selected_parsed_witness: Any | None
    selected_verified_binding: (
        Step11Rc0030ExperimentGateVerifiedBinding | None
    )
    status: str
    bounded_candidate_limit: int
    bounded_replan_limit: int
    parser_invocation_count: int
    matcher_invocation_count: int
    body_byte_inspection_count: int
    recovery_attempted: bool
    soft_rescue_used: bool
    experimental_only: bool = True
    runtime_connected: bool = False


def _step11_rc0030_origin_registry():
    registry: dict[int, _step11_rc0030_weakref.ReferenceType[Any]] = {}

    def register(value: Any) -> None:
        key = id(value)

        def remove(
            reference: _step11_rc0030_weakref.ReferenceType[Any],
            *,
            registry_key: int = key,
        ) -> None:
            if registry.get(registry_key) is reference:
                registry.pop(registry_key, None)

        registry[key] = _step11_rc0030_weakref.ref(value, remove)

    def validate(value: Any) -> bool:
        reference = registry.get(id(value))
        return reference is not None and reference() is value

    return register, validate


(
    _step11_rc0030_register_base_inverse_context,
    _step11_rc0030_validate_base_inverse_context_origin,
) = _step11_rc0030_origin_registry()
(
    _step11_rc0030_register_base_inverse_evaluation,
    _step11_rc0030_validate_base_inverse_evaluation_origin,
) = _step11_rc0030_origin_registry()
(
    _step11_rc0030_register_gate_verified_binding,
    _step11_rc0030_validate_gate_verified_binding_origin,
) = _step11_rc0030_origin_registry()


def _step11_rc0030_closed_code(value: Any, fallback: str) -> str:
    if (
        type(value) is str
        and _STEP11_RC0030_CLOSED_CODE_RE.fullmatch(value) is not None
    ):
        return value
    return fallback


def _step11_rc0030_valid_sha256(value: Any) -> bool:
    return bool(
        type(value) is str
        and _STEP11_RC0030_SHA256_RE.fullmatch(value) is not None
        and value != "0" * 64
    )


def _step11_rc0030_source_commitments(
    *,
    successor_snapshot: Any,
    inventory_result: Any,
    content_plan: Mapping[str, Any],
    discourse_plan: Mapping[str, Any],
    current_input: Mapping[str, Any],
) -> tuple[str, str, str, str, str, str]:
    try:
        snapshot_sha256 = successor_snapshot.experiment_snapshot_sha256
        authority_sha256 = (
            successor_snapshot.relation_construction_authority.authority_sha256
        )
        inventory_sha256 = artifact_sha256(inventory_result.ledger)
        content_sha256 = artifact_sha256(dict(content_plan))
        discourse_sha256 = artifact_sha256(dict(discourse_plan))
        current_sha256 = artifact_sha256(dict(current_input))
    except (AttributeError, KeyError, TypeError, UnicodeError, ValueError):
        raise Step11Rc0030ExperimentGateError(
            "STEP11_RC0030_SOURCE_COMMITMENT_INVALID"
        ) from None
    if not all(
        _step11_rc0030_valid_sha256(row)
        for row in (
            snapshot_sha256,
            authority_sha256,
            inventory_sha256,
            content_sha256,
            discourse_sha256,
            current_sha256,
        )
    ):
        raise Step11Rc0030ExperimentGateError(
            "STEP11_RC0030_SOURCE_COMMITMENT_INVALID"
        )
    return (
        snapshot_sha256,
        authority_sha256,
        inventory_sha256,
        content_sha256,
        discourse_sha256,
        current_sha256,
    )


def _step11_rc0030_inverse_contracts() -> tuple[Any, ...]:
    from emlis_ai_step11_natural_surface_matcher_v3 import (
        Step11Rc0030BaseBodyParsedWitness,
        Step11Rc0030ExperimentParsedSurfaceWitness,
        Step11Rc0030ExperimentVerifiedSurfaceBinding,
        match_step11_rc0030_base_body_exact_reuse,
        match_step11_rc0030_experiment_surface,
        parse_step11_rc0030_base_body_exact_reuse,
        parse_step11_rc0030_experiment_surface,
        step11_rc0030_base_body_parsed_witness_material,
        step11_rc0030_experiment_parsed_witness_material,
        step11_rc0030_experiment_verified_binding_material,
        step11_rc0030_verified_base_body_reuse_material,
    )

    return (
        Step11Rc0030BaseBodyParsedWitness,
        Step11Rc0030ExperimentParsedSurfaceWitness,
        Step11Rc0030ExperimentVerifiedSurfaceBinding,
        parse_step11_rc0030_base_body_exact_reuse,
        match_step11_rc0030_base_body_exact_reuse,
        parse_step11_rc0030_experiment_surface,
        match_step11_rc0030_experiment_surface,
        step11_rc0030_base_body_parsed_witness_material,
        step11_rc0030_experiment_parsed_witness_material,
        step11_rc0030_experiment_verified_binding_material,
        step11_rc0030_verified_base_body_reuse_material,
    )


def _step11_rc0030_surface_contracts() -> tuple[Any, ...]:
    from emlis_ai_step11_natural_surface_v3 import (
        STEP11_RC0030_EXPERIMENT_CANDIDATE_VERSION_ID,
        Step11NaturalSurfaceCandidate,
        Step11Rc0030ExperimentSurfaceCandidate,
        render_step11_rc0030_experiment_surface,
        step11_rc0030_surface_realization_plan_material,
        validate_step11_rc0030_experiment_surface_candidate,
    )

    return (
        STEP11_RC0030_EXPERIMENT_CANDIDATE_VERSION_ID,
        Step11NaturalSurfaceCandidate,
        Step11Rc0030ExperimentSurfaceCandidate,
        render_step11_rc0030_experiment_surface,
        step11_rc0030_surface_realization_plan_material,
        validate_step11_rc0030_experiment_surface_candidate,
    )


def _step11_rc0030_base_context_payload(
    value: Step11Rc0030ExperimentBaseInverseContext,
    *,
    include_context_sha256: bool,
) -> dict[str, Any]:
    result = {
        "schema_version": value.schema_version,
        "context_sha256": value.context_sha256,
        "source_base_candidate_id": value.source_base_candidate_id,
        "base_surface_sha256": value.base_surface_sha256,
        "base_body_byte_count": value.base_body_byte_count,
        "successor_snapshot_sha256": value.successor_snapshot_sha256,
        "source_authority_sha256": value.source_authority_sha256,
        "inventory_ledger_sha256": value.inventory_ledger_sha256,
        "content_plan_sha256": value.content_plan_sha256,
        "discourse_plan_sha256": value.discourse_plan_sha256,
        "current_input_sha256": value.current_input_sha256,
        "base_body_witness_sha256": artifact_sha256(
            _step11_rc0030_inverse_contracts()[7](
                value.base_body_witness
            )
        ),
        "verified_base_reuse_binding_sha256": [
            artifact_sha256(_step11_rc0030_inverse_contracts()[10](row))
            for row in value.verified_base_reuse_bindings
        ],
        "parser_invocation_count": value.parser_invocation_count,
        "matcher_invocation_count": value.matcher_invocation_count,
        "body_scan_pass_count": value.body_scan_pass_count,
        "body_byte_inspection_count": value.body_byte_inspection_count,
        "private_request_local": value.private_request_local,
        "shareable": value.shareable,
        "experimental_only": value.experimental_only,
        "runtime_connected": value.runtime_connected,
    }
    if not include_context_sha256:
        result.pop("context_sha256")
    return result


def step11_rc0030_experiment_base_inverse_context_material(
    value: Step11Rc0030ExperimentBaseInverseContext,
) -> dict[str, Any]:
    if type(value) is not Step11Rc0030ExperimentBaseInverseContext:
        raise Step11Rc0030ExperimentGateError(
            "STEP11_RC0030_BASE_INVERSE_CONTEXT_TYPE_INVALID"
        )
    if not _step11_rc0030_validate_base_inverse_context_origin(value):
        raise Step11Rc0030ExperimentGateError(
            "STEP11_RC0030_BASE_INVERSE_CONTEXT_ORIGIN_REQUIRED"
        )
    try:
        base_type = _step11_rc0030_inverse_contracts()[0]
        base_material = _step11_rc0030_inverse_contracts()[7](
            value.base_body_witness
        )
        reuse_materials = tuple(
            _step11_rc0030_inverse_contracts()[10](row)
            for row in value.verified_base_reuse_bindings
        )
    except Exception as error:
        raise Step11Rc0030ExperimentGateError(
            _step11_rc0030_closed_code(
                getattr(error, "code", None),
                "STEP11_RC0030_BASE_INVERSE_CONTEXT_INVALID",
            )
        ) from None
    if (
        value.schema_version
        != STEP11_RC0030_EXPERIMENT_BASE_INVERSE_CONTEXT_SCHEMA
        or type(value.source_base_candidate_id) is not str
        or not value.source_base_candidate_id
        or type(value.base_body_witness) is not base_type
        or value.base_surface_sha256
        != getattr(value.base_body_witness, "body_sha256", None)
        or not all(
            _step11_rc0030_valid_sha256(row)
            for row in (
                value.context_sha256,
                value.base_surface_sha256,
                value.successor_snapshot_sha256,
                value.source_authority_sha256,
                value.inventory_ledger_sha256,
                value.content_plan_sha256,
                value.discourse_plan_sha256,
                value.current_input_sha256,
            )
        )
        or type(value.verified_base_reuse_bindings) is not tuple
        or len(
            {
                getattr(row, "source_atom_id", None)
                for row in value.verified_base_reuse_bindings
            }
        )
        != len(value.verified_base_reuse_bindings)
        or value.parser_invocation_count != 1
        or value.matcher_invocation_count != 1
        or value.body_scan_pass_count != 2
        or type(value.base_body_byte_count) is not int
        or type(value.base_body_byte_count) is bool
        or not 1 <= value.base_body_byte_count <= STEP11_RC0030_BODY_BYTE_LIMIT
        or value.body_byte_inspection_count
        != value.base_body_byte_count * value.body_scan_pass_count
        or value.private_request_local is not True
        or value.shareable is not False
        or value.experimental_only is not True
        or value.runtime_connected is not False
        or base_material.get("body_sha256") != value.base_surface_sha256
        or len(reuse_materials) != len(value.verified_base_reuse_bindings)
        or value.context_sha256
        != artifact_sha256(
            _step11_rc0030_base_context_payload(
                value, include_context_sha256=False
            )
        )
    ):
        raise Step11Rc0030ExperimentGateError(
            "STEP11_RC0030_BASE_INVERSE_CONTEXT_INVALID"
        )
    return _step11_rc0030_base_context_payload(
        value, include_context_sha256=True
    )


def _step11_rc0030_base_inverse_evaluation_payload(
    value: Step11Rc0030ExperimentBaseInverseEvaluation,
) -> dict[str, Any]:
    """Return only the body-free, private diagnostic projection."""

    return {
        "schema_version": value.schema_version,
        "source_base_candidate_id": value.source_base_candidate_id,
        "base_surface_sha256": value.base_surface_sha256,
        "base_body_byte_count": value.base_body_byte_count,
        "base_inverse_context_sha256": (
            value.base_inverse_context_sha256
        ),
        "failure_code": value.failure_code,
        "failure_codes": list(value.failure_codes),
        "hard_pass": value.hard_pass,
        "parser_invocation_count": value.parser_invocation_count,
        "matcher_invocation_count": value.matcher_invocation_count,
        "charged_body_scan_pass_count": (
            value.charged_body_scan_pass_count
        ),
        "body_byte_inspection_count": value.body_byte_inspection_count,
        "private_request_local": value.private_request_local,
        "shareable": value.shareable,
        "experimental_only": value.experimental_only,
        "runtime_connected": value.runtime_connected,
        "body_free_export_allowed": value.body_free_export_allowed,
    }


def step11_rc0030_experiment_base_inverse_evaluation_material(
    value: Step11Rc0030ExperimentBaseInverseEvaluation,
) -> dict[str, Any]:
    """Validate an origin-bound evaluation and expose no body material."""

    if type(value) is not Step11Rc0030ExperimentBaseInverseEvaluation:
        raise Step11Rc0030ExperimentGateError(
            "STEP11_RC0030_BASE_INVERSE_EVALUATION_TYPE_INVALID"
        )
    if not _step11_rc0030_validate_base_inverse_evaluation_origin(value):
        raise Step11Rc0030ExperimentGateError(
            "STEP11_RC0030_BASE_INVERSE_EVALUATION_ORIGIN_REQUIRED"
        )
    context_material: dict[str, Any] | None = None
    if value.base_inverse_context is not None:
        context_material = (
            step11_rc0030_experiment_base_inverse_context_material(
                value.base_inverse_context
            )
        )
    codes_valid = (
        type(value.failure_codes) is tuple
        and len(value.failure_codes) in (0, 1)
        and all(
            type(code) is str
            and _STEP11_RC0030_CLOSED_CODE_RE.fullmatch(code) is not None
            for code in value.failure_codes
        )
    )
    count_fields_valid = all(
        type(count) is int and type(count) is not bool and count >= 0
        for count in (
            value.base_body_byte_count,
            value.parser_invocation_count,
            value.matcher_invocation_count,
            value.charged_body_scan_pass_count,
            value.body_byte_inspection_count,
        )
    )
    context_matches = (
        value.base_inverse_context is not None
        and context_material is not None
        and value.base_inverse_context_sha256
        == value.base_inverse_context.context_sha256
        and value.source_base_candidate_id
        == value.base_inverse_context.source_base_candidate_id
        and value.base_surface_sha256
        == value.base_inverse_context.base_surface_sha256
        and value.base_body_byte_count
        == value.base_inverse_context.base_body_byte_count
        and value.parser_invocation_count
        == value.base_inverse_context.parser_invocation_count
        and value.matcher_invocation_count
        == value.base_inverse_context.matcher_invocation_count
        and value.charged_body_scan_pass_count
        == value.base_inverse_context.body_scan_pass_count
        and value.body_byte_inspection_count
        == value.base_inverse_context.body_byte_inspection_count
    )
    if (
        value.schema_version
        != STEP11_RC0030_EXPERIMENT_BASE_INVERSE_EVALUATION_SCHEMA
        or type(value.source_base_candidate_id) is not str
        or not value.source_base_candidate_id
        or not count_fields_valid
        or value.parser_invocation_count not in (0, 1)
        or value.matcher_invocation_count not in (0, 1)
        or value.matcher_invocation_count > value.parser_invocation_count
        or value.charged_body_scan_pass_count
        != 2 * value.parser_invocation_count
        or value.body_byte_inspection_count
        != (
            value.base_body_byte_count
            * value.charged_body_scan_pass_count
        )
        or (
            value.parser_invocation_count == 1
            and not (
                1
                <= value.base_body_byte_count
                <= STEP11_RC0030_BODY_BYTE_LIMIT
            )
        )
        or (
            value.base_surface_sha256 is not None
            and not _step11_rc0030_valid_sha256(
                value.base_surface_sha256
            )
        )
        or not codes_valid
        or value.failure_code
        != (value.failure_codes[0] if value.failure_codes else None)
        or value.hard_pass is not (len(value.failure_codes) == 0)
        or (
            value.hard_pass
            and (
                not context_matches
                or value.parser_invocation_count != 1
                or value.matcher_invocation_count != 1
            )
        )
        or (
            not value.hard_pass
            and (
                value.base_inverse_context is not None
                or value.base_inverse_context_sha256 is not None
            )
        )
        or value.private_request_local is not True
        or value.shareable is not False
        or value.experimental_only is not True
        or value.runtime_connected is not False
        or value.body_free_export_allowed is not False
    ):
        raise Step11Rc0030ExperimentGateError(
            "STEP11_RC0030_BASE_INVERSE_EVALUATION_INVALID"
        )
    return _step11_rc0030_base_inverse_evaluation_payload(value)


def _step11_rc0030_finish_base_inverse_evaluation(
    *,
    source_base_candidate_id: str,
    base_surface_sha256: str | None,
    base_body_byte_count: int,
    base_inverse_context: Step11Rc0030ExperimentBaseInverseContext | None,
    failure_code: str | None,
    parser_invocation_count: int,
    matcher_invocation_count: int,
) -> Step11Rc0030ExperimentBaseInverseEvaluation:
    closed_failure = (
        None
        if failure_code is None
        else _step11_rc0030_closed_code(
            failure_code,
            "STEP11_RC0030_BASE_INVERSE_PREPASS_FAILED",
        )
    )
    value = Step11Rc0030ExperimentBaseInverseEvaluation(
        schema_version=(
            STEP11_RC0030_EXPERIMENT_BASE_INVERSE_EVALUATION_SCHEMA
        ),
        source_base_candidate_id=source_base_candidate_id,
        base_surface_sha256=base_surface_sha256,
        base_body_byte_count=base_body_byte_count,
        base_inverse_context=(
            base_inverse_context if closed_failure is None else None
        ),
        base_inverse_context_sha256=(
            base_inverse_context.context_sha256
            if base_inverse_context is not None and closed_failure is None
            else None
        ),
        failure_code=closed_failure,
        failure_codes=(
            () if closed_failure is None else (closed_failure,)
        ),
        hard_pass=(closed_failure is None and base_inverse_context is not None),
        parser_invocation_count=parser_invocation_count,
        matcher_invocation_count=matcher_invocation_count,
        charged_body_scan_pass_count=(2 * parser_invocation_count),
        body_byte_inspection_count=(
            base_body_byte_count * 2 * parser_invocation_count
        ),
    )
    _step11_rc0030_register_base_inverse_evaluation(value)
    step11_rc0030_experiment_base_inverse_evaluation_material(value)
    return value


def evaluate_step11_rc0030_experiment_base_inverse(
    base_candidate: Any,
    *,
    successor_snapshot: Any,
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
    current_input: Mapping[str, Any],
) -> Step11Rc0030ExperimentBaseInverseEvaluation:
    """Evaluate the sole base Parser/Matcher prepass without losing counts."""

    source_base_candidate_id = (
        "STEP11_RC0030_BASE_CANDIDATE_UNAVAILABLE"
    )
    body: bytes | None = None
    body_byte_count = 0
    body_sha256: str | None = None

    def reject(
        code: str,
        *,
        parser_count: int = 0,
        matcher_count: int = 0,
    ) -> Step11Rc0030ExperimentBaseInverseEvaluation:
        return _step11_rc0030_finish_base_inverse_evaluation(
            source_base_candidate_id=source_base_candidate_id,
            base_surface_sha256=body_sha256,
            base_body_byte_count=body_byte_count,
            base_inverse_context=None,
            failure_code=code,
            parser_invocation_count=parser_count,
            matcher_invocation_count=matcher_count,
        )

    try:
        (
            _expected,
            base_candidate_type,
            _candidate_type,
            _render,
            _plan,
            _validate,
        ) = _step11_rc0030_surface_contracts()
    except Exception:
        return reject("STEP11_RC0030_FORWARD_OWNER_UNAVAILABLE")
    if type(base_candidate) is not base_candidate_type:
        return reject("STEP11_RC0030_BASE_CANDIDATE_TYPE_INVALID")
    try:
        candidate_id = base_candidate.candidate_id
        body = base_candidate.final_utf8_bytes
        discourse_plan = base_candidate.discourse_plan
    except Exception:
        return reject("STEP11_RC0030_BASE_CANDIDATE_INVALID")
    if type(candidate_id) is str and candidate_id:
        source_base_candidate_id = candidate_id
    if type(body) is bytes:
        body_byte_count = len(body)
    if (
        type(candidate_id) is not str
        or not candidate_id
        or type(body) is not bytes
        or not body
        or len(body) > STEP11_RC0030_BODY_BYTE_LIMIT
        or type(discourse_plan) is not dict
    ):
        return reject("STEP11_RC0030_BASE_CANDIDATE_INVALID")
    body_sha256 = hashlib.sha256(body).hexdigest()
    try:
        commitments = _step11_rc0030_source_commitments(
            successor_snapshot=successor_snapshot,
            inventory_result=inventory_result,
            content_plan=content_plan,
            discourse_plan=discourse_plan,
            current_input=current_input,
        )
    except Exception as error:
        return reject(
            _step11_rc0030_closed_code(
                getattr(error, "code", None),
                "STEP11_RC0030_SOURCE_COMMITMENT_INVALID",
            )
        )
    try:
        inverse = _step11_rc0030_inverse_contracts()
    except Exception:
        return reject("STEP11_RC0030_BASE_INVERSE_PREPASS_FAILED")

    parser_count = 1
    try:
        base_witness = inverse[3](body)
        inverse[7](base_witness)
    except Exception as error:
        return reject(
            _step11_rc0030_closed_code(
                getattr(error, "code", None),
                "STEP11_RC0030_BASE_INVERSE_PREPASS_FAILED",
            ),
            parser_count=parser_count,
        )

    matcher_count = 1
    try:
        reuse = tuple(
            inverse[4](
                base_witness,
                successor_snapshot=successor_snapshot,
                inventory_result=inventory_result,
                content_plan=content_plan,
                discourse_plan=discourse_plan,
                current_input=current_input,
            )
        )
        for row in reuse:
            inverse[10](row)
        if len(
            {
                getattr(row, "source_atom_id", None)
                for row in reuse
            }
        ) != len(reuse):
            raise Step11Rc0030ExperimentGateError(
                "STEP11_RC0030_BASE_INVERSE_CONTEXT_INVALID"
            )
    except Exception as error:
        return reject(
            _step11_rc0030_closed_code(
                getattr(error, "code", None),
                "STEP11_RC0030_BASE_INVERSE_PREPASS_FAILED",
            ),
            parser_count=parser_count,
            matcher_count=matcher_count,
        )

    provisional = Step11Rc0030ExperimentBaseInverseContext(
        schema_version=(
            STEP11_RC0030_EXPERIMENT_BASE_INVERSE_CONTEXT_SCHEMA
        ),
        context_sha256="0" * 64,
        source_base_candidate_id=source_base_candidate_id,
        base_surface_sha256=body_sha256,
        base_body_byte_count=body_byte_count,
        successor_snapshot_sha256=commitments[0],
        source_authority_sha256=commitments[1],
        inventory_ledger_sha256=commitments[2],
        content_plan_sha256=commitments[3],
        discourse_plan_sha256=commitments[4],
        current_input_sha256=commitments[5],
        base_body_witness=base_witness,
        verified_base_reuse_bindings=reuse,
        parser_invocation_count=parser_count,
        matcher_invocation_count=matcher_count,
        body_scan_pass_count=2,
        body_byte_inspection_count=body_byte_count * 2,
    )
    value = Step11Rc0030ExperimentBaseInverseContext(
        schema_version=provisional.schema_version,
        context_sha256=artifact_sha256(
            _step11_rc0030_base_context_payload(
                provisional, include_context_sha256=False
            )
        ),
        source_base_candidate_id=provisional.source_base_candidate_id,
        base_surface_sha256=provisional.base_surface_sha256,
        base_body_byte_count=provisional.base_body_byte_count,
        successor_snapshot_sha256=provisional.successor_snapshot_sha256,
        source_authority_sha256=provisional.source_authority_sha256,
        inventory_ledger_sha256=provisional.inventory_ledger_sha256,
        content_plan_sha256=provisional.content_plan_sha256,
        discourse_plan_sha256=provisional.discourse_plan_sha256,
        current_input_sha256=provisional.current_input_sha256,
        base_body_witness=provisional.base_body_witness,
        verified_base_reuse_bindings=(
            provisional.verified_base_reuse_bindings
        ),
        parser_invocation_count=provisional.parser_invocation_count,
        matcher_invocation_count=provisional.matcher_invocation_count,
        body_scan_pass_count=provisional.body_scan_pass_count,
        body_byte_inspection_count=provisional.body_byte_inspection_count,
    )
    _step11_rc0030_register_base_inverse_context(value)
    step11_rc0030_experiment_base_inverse_context_material(value)
    return _step11_rc0030_finish_base_inverse_evaluation(
        source_base_candidate_id=source_base_candidate_id,
        base_surface_sha256=body_sha256,
        base_body_byte_count=body_byte_count,
        base_inverse_context=value,
        failure_code=None,
        parser_invocation_count=parser_count,
        matcher_invocation_count=matcher_count,
    )


def prepare_step11_rc0030_experiment_base_inverse(
    base_candidate: Any,
    *,
    successor_snapshot: Any,
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
    current_input: Mapping[str, Any],
) -> Step11Rc0030ExperimentBaseInverseContext:
    """Compatibility wrapper for callers that require a passing context."""

    evaluation = evaluate_step11_rc0030_experiment_base_inverse(
        base_candidate,
        successor_snapshot=successor_snapshot,
        inventory_result=inventory_result,
        content_plan=content_plan,
        current_input=current_input,
    )
    if (
        not evaluation.hard_pass
        or evaluation.base_inverse_context is None
    ):
        raise Step11Rc0030ExperimentGateError(
            evaluation.failure_code
            or "STEP11_RC0030_BASE_INVERSE_PREPASS_FAILED"
        )
    return evaluation.base_inverse_context


def _step11_rc0030_reuse_projection(value: Any) -> tuple[Any, ...]:
    return (
        getattr(value, "source_atom_id", None),
        getattr(value, "semantic_family", None),
        getattr(value, "base_parsed_atom_id", None),
        getattr(value, "base_obligation_id", None),
        getattr(value, "match_basis", None),
        getattr(value, "base_surface_sha256", None),
        getattr(value, "source_authority_sha256", None),
        getattr(value, "independent_binding_sha256", None),
    )


def _step11_rc0030_gate_binding_payload(
    value: Step11Rc0030ExperimentGateVerifiedBinding,
) -> dict[str, Any]:
    return {
        "schema_version": value.schema_version,
        "candidate_id": value.candidate_id,
        "parsed_witness_sha256": value.parsed_witness_sha256,
        "verified_surface_binding_sha256": (
            value.verified_surface_binding_sha256
        ),
        "base_witness_sha256": value.base_witness_sha256,
        "successor_snapshot_sha256": value.successor_snapshot_sha256,
        "source_authority_sha256": value.source_authority_sha256,
        "experiment_catalog_sha256": value.experiment_catalog_sha256,
        "base_leading_observation_match_count": (
            value.base_leading_observation_match_count
        ),
        "semantic_binding_count": value.semantic_binding_count,
        "exact_reuse_count": value.exact_reuse_count,
        "reception_binding_count": value.reception_binding_count,
        "parser_invocation_count": value.parser_invocation_count,
        "matcher_invocation_count": value.matcher_invocation_count,
        "body_byte_inspection_count": value.body_byte_inspection_count,
        "semantic_coverage_authorized": (
            value.semantic_coverage_authorized
        ),
        "issue_codes": list(value.issue_codes),
        "hard_verified": value.hard_verified,
        "body_free_export_allowed": value.body_free_export_allowed,
    }


def step11_rc0030_experiment_gate_verified_binding_material(
    value: Step11Rc0030ExperimentGateVerifiedBinding,
) -> dict[str, Any]:
    if type(value) is not Step11Rc0030ExperimentGateVerifiedBinding:
        raise Step11Rc0030ExperimentGateError(
            "STEP11_RC0030_GATE_BINDING_TYPE_INVALID"
        )
    if not _step11_rc0030_validate_gate_verified_binding_origin(value):
        raise Step11Rc0030ExperimentGateError(
            "STEP11_RC0030_GATE_BINDING_ORIGIN_REQUIRED"
        )
    try:
        inverse = _step11_rc0030_inverse_contracts()
        parsed_material = inverse[8](value.parsed_witness)
        binding_material = inverse[9](value.verified_surface_binding)
    except Exception as error:
        raise Step11Rc0030ExperimentGateError(
            _step11_rc0030_closed_code(
                getattr(error, "code", None),
                "STEP11_RC0030_GATE_BINDING_INVALID",
            )
        ) from None
    if (
        value.schema_version
        != STEP11_RC0030_EXPERIMENT_GATE_VERIFIED_BINDING_SCHEMA
        or not value.candidate_id
        or not all(
            _step11_rc0030_valid_sha256(row)
            for row in (
                value.parsed_witness_sha256,
                value.verified_surface_binding_sha256,
                value.base_witness_sha256,
                value.successor_snapshot_sha256,
                value.source_authority_sha256,
                value.experiment_catalog_sha256,
            )
        )
        or value.parsed_witness_sha256 != artifact_sha256(parsed_material)
        or value.verified_surface_binding_sha256
        != artifact_sha256(binding_material)
        or value.base_witness_sha256
        != getattr(value.verified_surface_binding, "base_witness_sha256", None)
        or value.base_leading_observation_match_count != 1
        or type(value.semantic_binding_count) is not int
        or value.semantic_binding_count < 1
        or type(value.exact_reuse_count) is not int
        or not 0 <= value.exact_reuse_count <= value.semantic_binding_count
        or type(value.reception_binding_count) is not int
        or not 1 <= value.reception_binding_count <= 3
        or value.parser_invocation_count
        != STEP11_RC0030_PARSER_INVOCATION_PER_CANDIDATE_LIMIT
        or value.matcher_invocation_count
        != STEP11_RC0030_MATCHER_INVOCATION_PER_CANDIDATE_LIMIT
        or type(value.body_byte_inspection_count) is not int
        or not 1
        <= value.body_byte_inspection_count
        <= 4 * STEP11_RC0030_BODY_BYTE_LIMIT
        or value.semantic_coverage_authorized is not False
        or value.issue_codes != ()
        or value.hard_verified is not True
        or value.body_free_export_allowed is not False
    ):
        raise Step11Rc0030ExperimentGateError(
            "STEP11_RC0030_GATE_BINDING_INVALID"
        )
    return _step11_rc0030_gate_binding_payload(value)


def _step11_rc0030_gate_result_material(
    value: Step11Rc0030ExperimentGateResult,
) -> dict[str, Any]:
    if type(value) is not Step11Rc0030ExperimentGateResult:
        raise Step11Rc0030ExperimentGateError(
            "STEP11_RC0030_GATE_RESULT_TYPE_INVALID"
        )
    return {
        "schema_version": value.schema_version,
        "candidate_id": value.candidate_id,
        "candidate_version_id": value.candidate_version_id,
        "final_bytes_sha256": value.final_bytes_sha256,
        "surface_realization_plan_sha256": (
            value.surface_realization_plan_sha256
        ),
        "parsed_witness_sha256": value.parsed_witness_sha256,
        "verified_binding_sha256": value.verified_binding_sha256,
        "gate_verified_binding_sha256": (
            value.gate_verified_binding_sha256
        ),
        "successor_snapshot_sha256": value.successor_snapshot_sha256,
        "source_authority_sha256": value.source_authority_sha256,
        "experiment_catalog_sha256": value.experiment_catalog_sha256,
        "base_gate_failure_codes": list(value.base_gate_failure_codes),
        "failure_codes": list(value.failure_codes),
        "hard_pass": value.hard_pass,
        "semantic_coverage_authorized": (
            value.semantic_coverage_authorized
        ),
        "base_leading_observation_match_count": (
            value.base_leading_observation_match_count
        ),
        "semantic_binding_count": value.semantic_binding_count,
        "exact_reuse_count": value.exact_reuse_count,
        "reception_binding_count": value.reception_binding_count,
        "parser_invocation_count": value.parser_invocation_count,
        "matcher_invocation_count": value.matcher_invocation_count,
        "body_byte_inspection_count": value.body_byte_inspection_count,
        "replan_count": value.replan_count,
        "experimental_only": value.experimental_only,
        "runtime_connected": value.runtime_connected,
    }


def step11_rc0030_experiment_gate_result_material(
    value: Step11Rc0030ExperimentGateResult,
) -> dict[str, Any]:
    return _step11_rc0030_gate_result_material(value)


def step11_rc0030_experiment_selection_result_material(
    value: Step11Rc0030ExperimentSelectionResult,
) -> dict[str, Any]:
    if type(value) is not Step11Rc0030ExperimentSelectionResult:
        raise Step11Rc0030ExperimentGateError(
            "STEP11_RC0030_SELECTION_RESULT_TYPE_INVALID"
        )
    return {
        "schema_version": value.schema_version,
        "candidate_version_id": value.candidate_version_id,
        "evaluated_candidate_ids": list(value.evaluated_candidate_ids),
        "gate_results": [
            _step11_rc0030_gate_result_material(row)
            for row in value.gate_results
        ],
        "selected_candidate_id": value.selected_candidate_id,
        "status": value.status,
        "bounded_candidate_limit": value.bounded_candidate_limit,
        "bounded_replan_limit": value.bounded_replan_limit,
        "parser_invocation_count": value.parser_invocation_count,
        "matcher_invocation_count": value.matcher_invocation_count,
        "body_byte_inspection_count": value.body_byte_inspection_count,
        "recovery_attempted": value.recovery_attempted,
        "soft_rescue_used": value.soft_rescue_used,
        "experimental_only": value.experimental_only,
        "runtime_connected": value.runtime_connected,
    }


def _step11_rc0030_result(
    *,
    candidate_id: str,
    candidate_version_id: str,
    final_bytes_sha256: str | None,
    surface_realization_plan_sha256: str | None,
    parsed_witness_sha256: str | None,
    verified_binding_sha256: str | None,
    gate_verified_binding_sha256: str | None,
    successor_snapshot_sha256: str | None,
    source_authority_sha256: str | None,
    experiment_catalog_sha256: str | None,
    base_gate_failure_codes: Sequence[str],
    failure_codes: Sequence[str],
    base_leading_observation_match_count: int,
    semantic_binding_count: int,
    exact_reuse_count: int,
    reception_binding_count: int,
    parser_invocation_count: int,
    matcher_invocation_count: int,
    body_byte_inspection_count: int,
    replan_count: int | None,
) -> Step11Rc0030ExperimentGateResult:
    base_codes = tuple(
        sorted(
            {
                _step11_rc0030_closed_code(
                    row, "STEP11_RC0030_BASE_GATE_REJECTED"
                )
                for row in base_gate_failure_codes
            }
        )
    )
    codes = tuple(
        sorted(
            {
                _step11_rc0030_closed_code(
                    row, "STEP11_RC0030_UNCLOSED_FAILURE_CODE"
                )
                for row in (*failure_codes, *base_codes)
            }
        )
    )
    return Step11Rc0030ExperimentGateResult(
        schema_version=STEP11_RC0030_EXPERIMENT_HARD_GATE_SCHEMA,
        candidate_id=candidate_id,
        candidate_version_id=candidate_version_id,
        final_bytes_sha256=final_bytes_sha256,
        surface_realization_plan_sha256=(
            surface_realization_plan_sha256
        ),
        parsed_witness_sha256=parsed_witness_sha256,
        verified_binding_sha256=verified_binding_sha256,
        gate_verified_binding_sha256=gate_verified_binding_sha256,
        successor_snapshot_sha256=successor_snapshot_sha256,
        source_authority_sha256=source_authority_sha256,
        experiment_catalog_sha256=experiment_catalog_sha256,
        base_gate_failure_codes=base_codes,
        failure_codes=codes,
        hard_pass=not codes,
        semantic_coverage_authorized=False,
        base_leading_observation_match_count=(
            base_leading_observation_match_count
        ),
        semantic_binding_count=semantic_binding_count,
        exact_reuse_count=exact_reuse_count,
        reception_binding_count=reception_binding_count,
        parser_invocation_count=parser_invocation_count,
        matcher_invocation_count=matcher_invocation_count,
        body_byte_inspection_count=body_byte_inspection_count,
        replan_count=replan_count,
    )


def _step11_rc0030_forward_inverse_join(
    candidate: Any,
    parsed_witness: Any,
    verified_binding: Any,
    *,
    verified_base_reuse_bindings: Sequence[Any],
) -> tuple[int, int, int, int]:
    """Verify exact forward/inverse placement without granting coverage."""

    plan = candidate.surface_realization_plan
    forward_reuse = tuple(plan.base_body_exact_reuse_bindings)
    inverse_reuse = tuple(verified_base_reuse_bindings)
    if tuple(map(_step11_rc0030_reuse_projection, forward_reuse)) != tuple(
        map(_step11_rc0030_reuse_projection, inverse_reuse)
    ):
        raise Step11Rc0030ExperimentGateError(
            "STEP11_RC0030_BASE_REUSE_COMMITMENT_MISMATCH"
        )

    parsed_by_id = {row.atom_id: row for row in parsed_witness.semantic_atoms}
    if len(parsed_by_id) != len(parsed_witness.semantic_atoms):
        raise Step11Rc0030ExperimentGateError(
            "STEP11_RC0030_SEMANTIC_BINDING_JOIN_MISMATCH"
        )
    forward_by_source = {
        row.source_atom_id: row for row in plan.semantic_chunk_bindings
    }
    if len(forward_by_source) != len(plan.semantic_chunk_bindings):
        raise Step11Rc0030ExperimentGateError(
            "STEP11_RC0030_SEMANTIC_BINDING_JOIN_MISMATCH"
        )
    reuse_by_source = {
        row.source_atom_id: row for row in inverse_reuse
    }
    seen_sources: set[str] = set()
    for row in verified_binding.semantic_bindings:
        source_id = row.source_atom_id
        if source_id in seen_sources:
            raise Step11Rc0030ExperimentGateError(
                "STEP11_RC0030_SEMANTIC_BINDING_JOIN_MISMATCH"
            )
        seen_sources.add(source_id)
        if row.parsed_atom_id is None:
            reuse = reuse_by_source.get(source_id)
            if (
                reuse is None
                or row.verified_reuse_binding_sha256
                != reuse.independent_binding_sha256
                or source_id in forward_by_source
            ):
                raise Step11Rc0030ExperimentGateError(
                    "STEP11_RC0030_BASE_REUSE_COMMITMENT_MISMATCH"
                )
            continue
        atom = parsed_by_id.get(row.parsed_atom_id)
        forward = forward_by_source.get(source_id)
        if (
            atom is None
            or forward is None
            or row.verified_reuse_binding_sha256 is not None
            or atom.semantic_family != forward.semantic_family
            or atom.sentence_group_ordinal != forward.sentence_group_ordinal
            or atom.grammatical_chunk_ordinal != forward.chunk_ordinal
            or atom.direction != forward.direction
        ):
            raise Step11Rc0030ExperimentGateError(
                "STEP11_RC0030_SEMANTIC_CHUNK_DISTRIBUTION_MISMATCH"
            )
    if seen_sources != set((*forward_by_source, *reuse_by_source)):
        raise Step11Rc0030ExperimentGateError(
            "STEP11_RC0030_SEMANTIC_BINDING_JOIN_MISMATCH"
        )

    forward_receptions = tuple(
        (
            row.source_reception_opportunity_id,
            row.reception_line_ordinal,
            row.chunk_ordinal,
            row.reception_act,
            len(row.source_target_owner_ids),
            len(row.supporting_source_owner_ids),
            row.association_basis,
        )
        for row in candidate.reception_bindings
    )
    inverse_receptions = tuple(
        (
            row.source_reception_opportunity_id,
            row.reception_line_ordinal,
            row.move_ordinal,
            row.reception_act,
            row.target_owner_count,
            row.supporting_owner_count,
            row.association_basis,
        )
        for row in verified_binding.reception_bindings
    )
    if forward_receptions != inverse_receptions:
        raise Step11Rc0030ExperimentGateError(
            "STEP11_RC0030_GROUNDED_RECEPTION_BINDING_MISMATCH"
        )

    base_plan = candidate.base_candidate.surface_ast.surface_realization_plan
    observation_units = tuple(
        sorted(
            (
                row
                for row in base_plan.units
                if row.section_role == "observation"
            ),
            key=lambda row: row.source_order,
        )
    )
    assignments = tuple(
        sorted(
            plan.observation_chunk_assignments,
            key=lambda row: (
                row.sentence_group_ordinal,
                row.chunk_ordinal,
            ),
        )
    )
    if not observation_units or not assignments:
        raise Step11Rc0030ExperimentGateError(
            "STEP11_RC0030_MAIN_MEANING_DOMINANCE_UNVERIFIED"
        )
    leading_id = observation_units[0].semantic_unit_id
    first_ids = tuple(assignments[0].source_unit_ids)
    if (
        plan.base_leading_observation_unit_id != leading_id
        or leading_id not in first_ids
        or any(
            unit_id in set(plan.structure_only_unit_ids)
            for unit_id in first_ids[: first_ids.index(leading_id)]
        )
    ):
        raise Step11Rc0030ExperimentGateError(
            "STEP11_RC0030_MAIN_MEANING_DOMINANCE_UNVERIFIED"
        )
    return (
        1,
        len(verified_binding.semantic_bindings),
        len(inverse_reuse),
        len(verified_binding.reception_bindings),
    )


def evaluate_step11_rc0030_experiment_candidate(
    candidate: Any,
    *,
    base_inverse_context: Step11Rc0030ExperimentBaseInverseContext,
    successor_snapshot: Any,
    lexical_atom_specs: Any,
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
    current_input: Mapping[str, Any],
) -> Step11Rc0030ExperimentGateEvaluation:
    """Rerender, parse, rematch, and join one rc0030 candidate once."""

    candidate_id = ""
    candidate_version_id = ""
    final_bytes_sha256: str | None = None
    plan_sha256: str | None = None
    parsed_sha256: str | None = None
    verified_sha256: str | None = None
    joined_sha256: str | None = None
    successor_sha256: str | None = None
    authority_sha256: str | None = None
    catalog_sha256: str | None = None
    base_codes: tuple[str, ...] = ()
    failures: list[str] = []
    leading_count = 0
    semantic_count = 0
    reuse_count = 0
    reception_count = 0
    parser_count = 0
    matcher_count = 0
    byte_inspections = 0
    replan_count: int | None = None
    parsed_witness: Any | None = None
    joined_binding: Step11Rc0030ExperimentGateVerifiedBinding | None = None
    final_body_bounded = False

    try:
        contracts = _step11_rc0030_surface_contracts()
        expected_version = contracts[0]
        candidate_type = contracts[2]
    except Exception:
        failures.append("STEP11_RC0030_FORWARD_OWNER_UNAVAILABLE")
        expected_version = ""
        candidate_type = None
        contracts = ()
    exact_candidate = candidate_type is not None and type(candidate) is candidate_type
    if not exact_candidate:
        failures.append("STEP11_RC0030_CANDIDATE_TYPE_INVALID")
    else:
        candidate_id = (
            candidate.candidate_id
            if type(candidate.candidate_id) is str
            else ""
        )
        candidate_version_id = (
            candidate.candidate_version_id
            if type(candidate.candidate_version_id) is str
            else ""
        )
        replan_count = (
            candidate.replan_count
            if type(candidate.replan_count) is int
            and type(candidate.replan_count) is not bool
            else None
        )
        body = candidate.final_utf8_bytes
        if (
            type(body) is bytes
            and 1 <= len(body) <= STEP11_RC0030_BODY_BYTE_LIMIT
        ):
            final_bytes_sha256 = hashlib.sha256(body).hexdigest()
            final_body_bounded = True
        else:
            failures.append("STEP11_RC0030_BODY_BOUND_INVALID")
        catalog_sha256 = (
            candidate.experiment_catalog_sha256
            if type(candidate.experiment_catalog_sha256) is str
            else None
        )
        if not candidate_id:
            failures.append("STEP11_RC0030_CANDIDATE_ID_INVALID")
        if candidate_version_id != expected_version:
            failures.append("STEP11_RC0030_ARTIFACT_COMMITMENT_MISMATCH")
        if (
            candidate.semantic_coverage_authorized is not False
            or getattr(successor_snapshot, "semantic_coverage_authorized", None)
            is not False
        ):
            failures.append("STEP11_RC0030_SEMANTIC_COVERAGE_SELF_CLAIM")
        if replan_count is None or not 0 <= replan_count <= 1:
            failures.append("STEP11_RC0030_REPLAN_BOUND_EXCEEDED")
        if (
            candidate.experimental_only is not True
            or candidate.private_body_full is not True
            or candidate.shareable is not False
            or candidate.runtime_connected is not False
        ):
            failures.append("STEP11_RC0030_RUNTIME_BOUNDARY_INVALID")

    context_valid = False
    if exact_candidate:
        try:
            step11_rc0030_experiment_base_inverse_context_material(
                base_inverse_context
            )
            context_valid = True
            parser_count = base_inverse_context.parser_invocation_count
            matcher_count = base_inverse_context.matcher_invocation_count
            byte_inspections = base_inverse_context.body_byte_inspection_count
        except Exception as error:
            failures.append(
                _step11_rc0030_closed_code(
                    getattr(error, "code", None),
                    "STEP11_RC0030_BASE_INVERSE_CONTEXT_INVALID",
                )
            )

    if exact_candidate and context_valid and final_body_bounded:
        discourse_plan = candidate.base_candidate.discourse_plan
        try:
            commitments = _step11_rc0030_source_commitments(
                successor_snapshot=successor_snapshot,
                inventory_result=inventory_result,
                content_plan=content_plan,
                discourse_plan=discourse_plan,
                current_input=current_input,
            )
            successor_sha256, authority_sha256 = commitments[:2]
            if (
                base_inverse_context.source_base_candidate_id
                != candidate.base_candidate.candidate_id
                or base_inverse_context.base_surface_sha256
                != hashlib.sha256(
                    candidate.base_candidate.final_utf8_bytes
                ).hexdigest()
                or base_inverse_context.base_body_byte_count
                != len(candidate.base_candidate.final_utf8_bytes)
                or (
                    base_inverse_context.successor_snapshot_sha256,
                    base_inverse_context.source_authority_sha256,
                    base_inverse_context.inventory_ledger_sha256,
                    base_inverse_context.content_plan_sha256,
                    base_inverse_context.discourse_plan_sha256,
                    base_inverse_context.current_input_sha256,
                )
                != commitments
            ):
                failures.append("STEP11_RC0030_BASE_INVERSE_CONTEXT_MISMATCH")
        except Exception as error:
            failures.append(
                _step11_rc0030_closed_code(
                    getattr(error, "code", None),
                    "STEP11_RC0030_SOURCE_COMMITMENT_INVALID",
                )
            )

        try:
            forward_issues = contracts[5](
                candidate,
                successor_snapshot=successor_snapshot,
                lexical_atom_specs=lexical_atom_specs,
            )
            if type(forward_issues) not in {tuple, list}:
                forward_issues = (
                    "STEP11_RC0030_CANDIDATE_REVALIDATION_FAILED",
                )
        except Exception:
            forward_issues = (
                "STEP11_RC0030_CANDIDATE_REVALIDATION_FAILED",
            )
        failures.extend(
            _step11_rc0030_closed_code(
                row, "STEP11_RC0030_CANDIDATE_REVALIDATION_FAILED"
            )
            for row in forward_issues
        )

        try:
            rerendered = contracts[3](
                candidate.base_candidate,
                clause_ready_lexical_specs=candidate.natural_handle_specs,
                surface_realization_plan=candidate.surface_realization_plan,
                construction_atoms=candidate.construction_atoms,
                relation_atoms=candidate.relation_atoms,
                semantic_link_atoms=candidate.semantic_link_atoms,
                explicit_unknown_atoms=candidate.explicit_unknown_atoms,
                reception_predications=candidate.reception_bindings,
            )
            if (
                rerendered != candidate.rendered_surface
                or rerendered.utf8_bytes != candidate.final_utf8_bytes
                or rerendered.sha256 != final_bytes_sha256
            ):
                failures.append(
                    "STEP11_RC0030_FINAL_BYTES_COMMITMENT_MISMATCH"
                )
            plan_sha256 = artifact_sha256(
                contracts[4](candidate.surface_realization_plan)
            )
        except Exception:
            failures.append("STEP11_RC0030_FINAL_BYTES_COMMITMENT_MISMATCH")

        try:
            base_result = evaluate_step11_natural_surface_candidate(
                candidate.base_candidate,
                inventory_result=inventory_result,
                content_plan=content_plan,
                current_input=current_input,
            )
            base_codes = tuple(base_result.failure_codes)
            if base_result.hard_pass is not True:
                failures.append("STEP11_RC0030_BASE_GATE_REJECTED")
        except Exception:
            failures.append("STEP11_RC0030_BASE_GATE_EVALUATION_FAILED")

        try:
            inverse = _step11_rc0030_inverse_contracts()
            parser_count += 1
            byte_inspections += len(candidate.final_utf8_bytes) * 2
            parsed_witness = inverse[5](candidate.final_utf8_bytes)
            parsed_material = inverse[8](parsed_witness)
            parsed_sha256 = artifact_sha256(parsed_material)
        except Exception as error:
            failures.append(
                _step11_rc0030_closed_code(
                    getattr(error, "code", None),
                    "STEP11_RC0030_PARSE_FAILED",
                )
            )

        verified_surface = None
        if parsed_witness is not None:
            try:
                matcher_count += 1
                verified_surface = inverse[6](
                    parsed_witness,
                    base_body_witness=base_inverse_context.base_body_witness,
                    successor_snapshot=successor_snapshot,
                    inventory_result=inventory_result,
                    content_plan=content_plan,
                    discourse_plan=discourse_plan,
                    current_input=current_input,
                    verified_base_reuse_bindings=(
                        base_inverse_context.verified_base_reuse_bindings
                    ),
                )
                verified_material = inverse[9](verified_surface)
                verified_sha256 = artifact_sha256(verified_material)
            except Exception as error:
                failures.append(
                    _step11_rc0030_closed_code(
                        getattr(error, "code", None),
                        "STEP11_RC0030_MATCH_FAILED",
                    )
                )
        if verified_surface is not None:
            if (
                verified_surface.hard_verified is not True
                or verified_surface.issue_codes != ()
                or verified_surface.semantic_coverage_authorized is not False
                or verified_surface.parsed_witness_sha256 != parsed_sha256
                or verified_surface.successor_snapshot_sha256
                != successor_sha256
                or verified_surface.source_authority_sha256
                != authority_sha256
                or verified_surface.experiment_catalog_sha256
                != catalog_sha256
            ):
                failures.append("STEP11_RC0030_BINDING_NOT_VERIFIED")
            try:
                (
                    leading_count,
                    semantic_count,
                    reuse_count,
                    reception_count,
                ) = _step11_rc0030_forward_inverse_join(
                    candidate,
                    parsed_witness,
                    verified_surface,
                    verified_base_reuse_bindings=(
                        base_inverse_context.verified_base_reuse_bindings
                    ),
                )
            except Exception as error:
                failures.append(
                    _step11_rc0030_closed_code(
                        getattr(error, "code", None),
                        "STEP11_RC0030_FORWARD_INVERSE_JOIN_MISMATCH",
                    )
                )

        if (
            parser_count
            > STEP11_RC0030_PARSER_INVOCATION_PER_CANDIDATE_LIMIT
            or matcher_count
            > STEP11_RC0030_MATCHER_INVOCATION_PER_CANDIDATE_LIMIT
            or byte_inspections > 4 * STEP11_RC0030_BODY_BYTE_LIMIT
        ):
            failures.append("STEP11_RC0030_RESOURCE_BOUND_EXCEEDED")

        if verified_surface is not None and not failures:
            joined_binding = Step11Rc0030ExperimentGateVerifiedBinding(
                schema_version=(
                    STEP11_RC0030_EXPERIMENT_GATE_VERIFIED_BINDING_SCHEMA
                ),
                candidate_id=candidate_id,
                parsed_witness_sha256=str(parsed_sha256),
                verified_surface_binding_sha256=str(verified_sha256),
                base_witness_sha256=verified_surface.base_witness_sha256,
                successor_snapshot_sha256=str(successor_sha256),
                source_authority_sha256=str(authority_sha256),
                experiment_catalog_sha256=str(catalog_sha256),
                base_leading_observation_match_count=leading_count,
                semantic_binding_count=semantic_count,
                exact_reuse_count=reuse_count,
                reception_binding_count=reception_count,
                parser_invocation_count=parser_count,
                matcher_invocation_count=matcher_count,
                body_byte_inspection_count=byte_inspections,
                parsed_witness=parsed_witness,
                verified_surface_binding=verified_surface,
                semantic_coverage_authorized=False,
                issue_codes=(),
                hard_verified=True,
            )
            _step11_rc0030_register_gate_verified_binding(joined_binding)
            try:
                joined_sha256 = artifact_sha256(
                    step11_rc0030_experiment_gate_verified_binding_material(
                        joined_binding
                    )
                )
            except Exception as error:
                failures.append(
                    _step11_rc0030_closed_code(
                        getattr(error, "code", None),
                        "STEP11_RC0030_GATE_BINDING_INVALID",
                    )
                )
                joined_binding = None

    result = _step11_rc0030_result(
        candidate_id=candidate_id,
        candidate_version_id=candidate_version_id,
        final_bytes_sha256=final_bytes_sha256,
        surface_realization_plan_sha256=plan_sha256,
        parsed_witness_sha256=parsed_sha256,
        verified_binding_sha256=verified_sha256,
        gate_verified_binding_sha256=joined_sha256,
        successor_snapshot_sha256=successor_sha256,
        source_authority_sha256=authority_sha256,
        experiment_catalog_sha256=catalog_sha256,
        base_gate_failure_codes=base_codes,
        failure_codes=failures,
        base_leading_observation_match_count=leading_count,
        semantic_binding_count=semantic_count,
        exact_reuse_count=reuse_count,
        reception_binding_count=reception_count,
        parser_invocation_count=parser_count,
        matcher_invocation_count=matcher_count,
        body_byte_inspection_count=byte_inspections,
        replan_count=replan_count,
    )
    if result.hard_pass and joined_binding is None:
        result = _step11_rc0030_result(
            candidate_id=candidate_id,
            candidate_version_id=candidate_version_id,
            final_bytes_sha256=final_bytes_sha256,
            surface_realization_plan_sha256=plan_sha256,
            parsed_witness_sha256=parsed_sha256,
            verified_binding_sha256=verified_sha256,
            gate_verified_binding_sha256=None,
            successor_snapshot_sha256=successor_sha256,
            source_authority_sha256=authority_sha256,
            experiment_catalog_sha256=catalog_sha256,
            base_gate_failure_codes=base_codes,
            failure_codes=("STEP11_RC0030_GATE_BINDING_INVALID",),
            base_leading_observation_match_count=leading_count,
            semantic_binding_count=semantic_count,
            exact_reuse_count=reuse_count,
            reception_binding_count=reception_count,
            parser_invocation_count=parser_count,
            matcher_invocation_count=matcher_count,
            body_byte_inspection_count=byte_inspections,
            replan_count=replan_count,
        )
    return Step11Rc0030ExperimentGateEvaluation(
        schema_version=STEP11_RC0030_EXPERIMENT_GATE_EVALUATION_SCHEMA,
        gate_result=result,
        parsed_witness=parsed_witness,
        verified_binding=joined_binding if result.hard_pass else None,
    )


def select_step11_rc0030_experiment_candidate(
    candidates: Sequence[Any],
    *,
    base_inverse_contexts: Sequence[
        Step11Rc0030ExperimentBaseInverseContext
    ],
    successor_snapshot: Any,
    lexical_atom_specs: Any,
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
    current_input: Mapping[str, Any],
    candidate_limit: int = STEP11_RC0030_EXPERIMENT_CANDIDATE_LIMIT,
    replan_limit: int = STEP11_RC0030_EXPERIMENT_REPLAN_LIMIT,
) -> Step11Rc0030ExperimentSelectionResult:
    """Evaluate every candidate exactly once and select deterministically."""

    if type(candidates) not in {tuple, list} or not candidates:
        raise Step11Rc0030ExperimentGateError(
            "STEP11_RC0030_CANDIDATE_SET_INVALID"
        )
    if (
        type(candidate_limit) is not int
        or type(candidate_limit) is bool
        or not 1
        <= candidate_limit
        <= STEP11_RC0030_EXPERIMENT_CANDIDATE_LIMIT
        or len(candidates) > candidate_limit
    ):
        raise Step11Rc0030ExperimentGateError(
            "STEP11_RC0030_CANDIDATE_BOUND_EXCEEDED"
        )
    if (
        type(replan_limit) is not int
        or type(replan_limit) is bool
        or not 0 <= replan_limit <= STEP11_RC0030_EXPERIMENT_REPLAN_LIMIT
    ):
        raise Step11Rc0030ExperimentGateError(
            "STEP11_RC0030_REPLAN_BOUND_EXCEEDED"
        )
    if (
        type(base_inverse_contexts) not in {tuple, list}
        or len(base_inverse_contexts) != len(candidates)
        or any(
            type(row) is not Step11Rc0030ExperimentBaseInverseContext
            for row in base_inverse_contexts
        )
    ):
        raise Step11Rc0030ExperimentGateError(
            "STEP11_RC0030_BASE_INVERSE_CONTEXT_SET_INVALID"
        )
    try:
        expected_version, _base_type, candidate_type, _render, _plan, _validate = (
            _step11_rc0030_surface_contracts()
        )
    except Exception:
        raise Step11Rc0030ExperimentGateError(
            "STEP11_RC0030_FORWARD_OWNER_UNAVAILABLE"
        ) from None
    if any(type(row) is not candidate_type for row in candidates):
        raise Step11Rc0030ExperimentGateError(
            "STEP11_RC0030_CANDIDATE_TYPE_INVALID"
        )
    ordered = tuple(sorted(candidates, key=lambda row: row.candidate_id))
    candidate_ids = tuple(row.candidate_id for row in ordered)
    base_ids = tuple(row.base_candidate.candidate_id for row in ordered)
    if (
        any(type(row) is not str or not row for row in candidate_ids)
        or len(set(candidate_ids)) != len(candidate_ids)
        or len(set(base_ids)) != len(base_ids)
        or any(
            type(row.replan_count) is not int
            or type(row.replan_count) is bool
            or not 0 <= row.replan_count <= replan_limit
            for row in ordered
        )
    ):
        raise Step11Rc0030ExperimentGateError(
            "STEP11_RC0030_CANDIDATE_ID_OR_REPLAN_INVALID"
        )
    context_by_base: dict[str, Step11Rc0030ExperimentBaseInverseContext] = {}
    for context in base_inverse_contexts:
        step11_rc0030_experiment_base_inverse_context_material(context)
        if context.source_base_candidate_id in context_by_base:
            raise Step11Rc0030ExperimentGateError(
                "STEP11_RC0030_BASE_INVERSE_CONTEXT_DUPLICATE"
            )
        context_by_base[context.source_base_candidate_id] = context
    if set(context_by_base) != set(base_ids):
        raise Step11Rc0030ExperimentGateError(
            "STEP11_RC0030_BASE_INVERSE_CONTEXT_SET_MISMATCH"
        )
    evaluations = tuple(
        evaluate_step11_rc0030_experiment_candidate(
            candidate,
            base_inverse_context=context_by_base[
                candidate.base_candidate.candidate_id
            ],
            successor_snapshot=successor_snapshot,
            lexical_atom_specs=lexical_atom_specs,
            inventory_result=inventory_result,
            content_plan=content_plan,
            current_input=current_input,
        )
        for candidate in ordered
    )
    gate_results = tuple(row.gate_result for row in evaluations)
    parser_count = sum(row.parser_invocation_count for row in gate_results)
    matcher_count = sum(row.matcher_invocation_count for row in gate_results)
    byte_inspections = sum(
        row.body_byte_inspection_count for row in gate_results
    )
    if (
        any(
            row.parser_invocation_count
            > STEP11_RC0030_PARSER_INVOCATION_PER_CANDIDATE_LIMIT
            or row.matcher_invocation_count
            > STEP11_RC0030_MATCHER_INVOCATION_PER_CANDIDATE_LIMIT
            for row in gate_results
        )
        or parser_count
        > STEP11_RC0030_PARSER_INVOCATION_ACROSS_CANDIDATES_LIMIT
        or matcher_count
        > (
            STEP11_RC0030_MATCHER_INVOCATION_PER_CANDIDATE_LIMIT
            * len(ordered)
        )
        or byte_inspections
        > STEP11_RC0030_BODY_BYTE_INSPECTION_ACROSS_CANDIDATES_LIMIT
    ):
        raise Step11Rc0030ExperimentGateError(
            "STEP11_RC0030_RESOURCE_BOUND_EXCEEDED"
        )
    selected_index = next(
        (
            index
            for index, evaluation in enumerate(evaluations)
            if evaluation.hard_pass
        ),
        None,
    )
    selected = ordered[selected_index] if selected_index is not None else None
    selected_evaluation = (
        evaluations[selected_index] if selected_index is not None else None
    )
    return Step11Rc0030ExperimentSelectionResult(
        schema_version=STEP11_RC0030_EXPERIMENT_SELECTION_SCHEMA,
        candidate_version_id=expected_version,
        evaluated_candidate_ids=candidate_ids,
        gate_results=gate_results,
        gate_evaluations=evaluations,
        selected_candidate_id=(
            selected.candidate_id if selected is not None else None
        ),
        selected_candidate=selected,
        selected_parsed_witness=(
            selected_evaluation.parsed_witness
            if selected_evaluation is not None
            else None
        ),
        selected_verified_binding=(
            selected_evaluation.verified_binding
            if selected_evaluation is not None
            else None
        ),
        status=(
            "selected"
            if selected is not None
            else "rc0030_experiment_no_valid_candidate"
        ),
        bounded_candidate_limit=candidate_limit,
        bounded_replan_limit=replan_limit,
        parser_invocation_count=parser_count,
        matcher_invocation_count=matcher_count,
        body_byte_inspection_count=byte_inspections,
        recovery_attempted=False,
        soft_rescue_used=False,
    )


def select_step11_rc0030_experiment_candidates(
    candidates: Sequence[Any],
    **kwargs: Any,
) -> Step11Rc0030ExperimentSelectionResult:
    return select_step11_rc0030_experiment_candidate(candidates, **kwargs)


__all__ += [
    "STEP11_RC0030_BODY_BYTE_INSPECTION_ACROSS_CANDIDATES_LIMIT",
    "STEP11_RC0030_BODY_BYTE_LIMIT",
    "STEP11_RC0030_EXPERIMENT_BASE_INVERSE_CONTEXT_SCHEMA",
    "STEP11_RC0030_EXPERIMENT_BASE_INVERSE_EVALUATION_SCHEMA",
    "STEP11_RC0030_EXPERIMENT_CANDIDATE_LIMIT",
    "STEP11_RC0030_EXPERIMENT_GATE_EVALUATION_SCHEMA",
    "STEP11_RC0030_EXPERIMENT_GATE_VERIFIED_BINDING_SCHEMA",
    "STEP11_RC0030_EXPERIMENT_HARD_GATE_SCHEMA",
    "STEP11_RC0030_EXPERIMENT_REPLAN_LIMIT",
    "STEP11_RC0030_EXPERIMENT_SELECTION_SCHEMA",
    "STEP11_RC0030_MATCHER_INVOCATION_PER_CANDIDATE_LIMIT",
    "STEP11_RC0030_PARSER_INVOCATION_ACROSS_CANDIDATES_LIMIT",
    "STEP11_RC0030_PARSER_INVOCATION_PER_CANDIDATE_LIMIT",
    "Step11Rc0030ExperimentBaseInverseContext",
    "Step11Rc0030ExperimentBaseInverseEvaluation",
    "Step11Rc0030ExperimentGateError",
    "Step11Rc0030ExperimentGateEvaluation",
    "Step11Rc0030ExperimentGateResult",
    "Step11Rc0030ExperimentGateVerifiedBinding",
    "Step11Rc0030ExperimentSelectionResult",
    "evaluate_step11_rc0030_experiment_base_inverse",
    "evaluate_step11_rc0030_experiment_candidate",
    "prepare_step11_rc0030_experiment_base_inverse",
    "select_step11_rc0030_experiment_candidate",
    "select_step11_rc0030_experiment_candidates",
    "step11_rc0030_experiment_base_inverse_context_material",
    "step11_rc0030_experiment_base_inverse_evaluation_material",
    "step11_rc0030_experiment_gate_result_material",
    "step11_rc0030_experiment_gate_verified_binding_material",
    "step11_rc0030_experiment_selection_result_material",
]
