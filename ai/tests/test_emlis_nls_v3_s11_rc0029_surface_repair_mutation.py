# -*- coding: utf-8 -*-
from __future__ import annotations

"""Executed D0 section 6.2 mutation ledger for rc0029 E0b.

Each active parametrized node performs one distinct mutation against a frozen
representative execution and requires the exact closed consumer code.  Static
import-graph and shareable-material privacy checks remain in their dedicated
rc0029 suites; this file does not inflate its count with callable placeholders.
No source or output body is embedded in this shareable suite.
"""

from dataclasses import dataclass, fields, replace
from functools import lru_cache
import hashlib
import importlib
import json
from pathlib import Path
from typing import Any, Callable

import pytest


_FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures" / "emlis_nls_v3"
_BATCH = _FIXTURE_ROOT / "generated" / "batch_001.jsonl"
_REPRESENTATIVE = _FIXTURE_ROOT / "cycle_001" / (
    "rc0029_representative8_body_free.json"
)
_RC0029_MANIFEST = _FIXTURE_ROOT / "cycle_001" / (
    "cycle001_dependency_manifest_rc0029_surface_repair_experiment.json"
)
_PREDECESSOR_MANIFEST = _FIXTURE_ROOT / "cycle_001" / (
    "cycle001_dependency_manifest_rc0028_downstream_experiment.json"
)
_MUTATION_CASE_IDS = frozenset(
    {
        "nls3s_b001_0001",
        "nls3s_b001_0009",
        "nls3s_b001_0019",
        "nls3s_b001_0035",
        "nls3s_b001_0043",
        "nls3s_b001_0063",
        "nls3s_b001_0100",
    }
)


@dataclass(frozen=True, slots=True)
class _Attack:
    attack_id: str
    module_name: str
    api_name: str
    expected_closed_failure: str


_MATCHER = "emlis_ai_step11_natural_surface_matcher_v3"
_GATE = "emlis_ai_step11_hard_gate_v3"
_CATALOG = "emlis_ai_step11_rc0029_experiment_surface_catalog_v3"
_RUNTIME = "emlis_ai_step11_rc0029_experiment_runtime_adapter_v3"

_LEXICALIZE_API = "build_step11_rc0029_natural_handle_specs"
_SURFACE_API = "build_step11_rc0029_experiment_surface_candidates"
_PARSE_API = "parse_step11_rc0029_experiment_surface"
_MATCH_API = "match_step11_rc0029_experiment_surface"
_GATE_API = "evaluate_step11_rc0029_experiment_candidate"
_SELECT_API = "select_step11_rc0029_experiment_candidate"
_CATALOG_VALIDATE_API = "validate_step11_rc0029_experiment_surface_catalog"
_RUNTIME_API = "run_step11_rc0029_experiment"


def _attack(
    attack_id: str,
    module_name: str,
    api_name: str,
    expected_closed_failure: str,
) -> _Attack:
    return _Attack(
        attack_id,
        module_name,
        api_name,
        expected_closed_failure,
    )


# The first D0 draft listed 48 callable-presence placeholders.  E0b does not
# count placeholders: this retained ledger contains only distinct mutations
# that this file actually executes.  Import-graph and shareable-material
# privacy attacks live in their dedicated rc0029 suites and are not duplicated
# here merely to preserve the draft's incidental number.
_ATTACKS = (
    _attack(
        "generic-body-replacement-retaining-forward-metadata",
        _GATE,
        _GATE_API,
        "STEP11_RC0029_FINAL_BYTES_COMMITMENT_MISMATCH",
    ),
    _attack(
        "forward-metadata-injection",
        _MATCHER,
        _PARSE_API,
        "STEP11_RC0029_PARSER_FORWARD_METADATA_FORBIDDEN",
    ),
    _attack(
        "relation-from-to-swap",
        _MATCHER,
        _MATCH_API,
        "STEP11_RC0029_RELATION_ENDPOINT_MISMATCH",
    ),
    _attack(
        "relation-direction-reverse",
        _MATCHER,
        _MATCH_API,
        "STEP11_RC0029_RELATION_DIRECTION_MISMATCH",
    ),
    _attack(
        "effective-relation-type-mutation",
        _MATCHER,
        _MATCH_API,
        "STEP11_RC0029_EFFECTIVE_RELATION_TYPE_MISMATCH",
    ),
    _attack(
        "inner-construction-deletion",
        _MATCHER,
        _MATCH_API,
        "STEP11_RC0029_CONSTRUCTION_CARDINALITY_MISMATCH",
    ),
    _attack(
        "construction-slot-duplicate",
        _MATCHER,
        _MATCH_API,
        "STEP11_RC0029_CONSTRUCTION_SLOT_BINDING_MISMATCH",
    ),
    _attack(
        "construction-slot-orphan",
        _MATCHER,
        _MATCH_API,
        "STEP11_RC0029_PARTICIPATION_OWNER_MISMATCH",
    ),
    _attack(
        "construction-role-field-key-mismatch",
        _MATCHER,
        _MATCH_API,
        "STEP11_RC0029_CONSTRUCTION_SLOT_BINDING_MISMATCH",
    ),
    _attack(
        "participation-owner-mutation",
        _MATCHER,
        _MATCH_API,
        "STEP11_RC0029_PARTICIPATION_OWNER_MISMATCH",
    ),
    _attack(
        "semantic-link-endpoint-mutation",
        _MATCHER,
        _MATCH_API,
        "STEP11_RC0029_SEMANTIC_LINK_ENDPOINT_MISMATCH",
    ),
    _attack(
        "semantic-link-type-mutation",
        _MATCHER,
        _MATCH_API,
        "STEP11_RC0029_SEMANTIC_LINK_TYPE_MISMATCH",
    ),
    _attack(
        "semantic-link-direction-mutation",
        _MATCHER,
        _MATCH_API,
        "STEP11_RC0029_SEMANTIC_LINK_DIRECTION_MISMATCH",
    ),
    _attack(
        "explicit-unknown-drop",
        _MATCHER,
        _MATCH_API,
        "STEP11_RC0029_EXPLICIT_UNKNOWN_MISSING",
    ),
    _attack(
        "explicit-unknown-duplicate",
        _MATCHER,
        _MATCH_API,
        "STEP11_RC0029_EXPLICIT_UNKNOWN_DUPLICATE",
    ),
    _attack(
        "explicit-unknown-valid-other-dimension",
        _MATCHER,
        _MATCH_API,
        "STEP11_RC0029_EXPLICIT_UNKNOWN_DIMENSION_MISMATCH",
    ),
    _attack(
        "explicit-unknown-affected-owner-order-mutation",
        _MATCHER,
        _MATCH_API,
        "STEP11_RC0029_EXPLICIT_UNKNOWN_OWNER_MISMATCH",
    ),
    _attack(
        "natural-handle-collision",
        _MATCHER,
        _MATCH_API,
        "STEP11_RC0029_NATURAL_HANDLE_SET_INVALID",
    ),
    _attack(
        "valid-other-input-natural-handle-cross-swap",
        _MATCHER,
        _MATCH_API,
        "STEP11_RC0029_NATURAL_HANDLE_SOURCE_MISMATCH",
    ),
    _attack(
        "depth-compaction-overflow",
        _MATCHER,
        _MATCH_API,
        "STEP11_RC0029_STRUCTURE_DEPTH_EXCEEDED",
    ),
    _attack(
        "generic-reception-without-antecedent",
        _MATCHER,
        _MATCH_API,
        "STEP11_RC0029_RECEPTION_ANTECEDENT_MISMATCH",
    ),
    _attack(
        "reception-antecedent-owner-swap",
        _MATCHER,
        _MATCH_API,
        "STEP11_RC0029_RECEPTION_ANTECEDENT_MISMATCH",
    ),
    _attack(
        "required-reception-obligation-drop",
        _MATCHER,
        _MATCH_API,
        "STEP11_RC0029_RECEPTION_CARDINALITY_MISMATCH",
    ),
    _attack(
        "required-reception-obligation-duplicate",
        _MATCHER,
        _MATCH_API,
        "STEP11_RC0029_RECEPTION_CARDINALITY_MISMATCH",
    ),
    _attack(
        "semantic-coverage-authorized-bool-true",
        _GATE,
        _GATE_API,
        "STEP11_RC0029_SEMANTIC_COVERAGE_SELF_CLAIM",
    ),
    _attack(
        "semantic-coverage-authorized-int-one",
        _GATE,
        _GATE_API,
        "STEP11_RC0029_SEMANTIC_COVERAGE_SELF_CLAIM",
    ),
    _attack(
        "semantic-coverage-authorized-string-false",
        _GATE,
        _GATE_API,
        "STEP11_RC0029_SEMANTIC_COVERAGE_SELF_CLAIM",
    ),
    _attack(
        "stale-artifact-hash",
        _GATE,
        _GATE_API,
        "STEP11_RC0029_ARTIFACT_COMMITMENT_MISMATCH",
    ),
    _attack(
        "valid-other-input-successor-swap",
        _MATCHER,
        _MATCH_API,
        "STEP11_RC0029_NATURAL_HANDLE_SOURCE_MISMATCH",
    ),
    _attack(
        "catalog-token-mutation",
        _CATALOG,
        _CATALOG_VALIDATE_API,
        "STEP11_RC0029_CATALOG_TOKEN_MISMATCH",
    ),
    _attack(
        "resource-bound-plus-one",
        _RUNTIME,
        "validate_step11_rc0029_experiment_result",
        "STEP11_RC0029_RESOURCE_BOUND_EXCEEDED",
    ),
    _attack(
        "candidate-count-thirteen",
        _RUNTIME,
        _RUNTIME_API,
        "STEP11_RC0029_CANDIDATE_BOUND_EXCEEDED",
    ),
    _attack(
        "replan-count-two",
        _RUNTIME,
        _RUNTIME_API,
        "STEP11_RC0029_REPLAN_BOUND_EXCEEDED",
    ),
)


def _node_id(attack: _Attack) -> str:
    return (
        f"{attack.attack_id}__expects__"
        f"{attack.expected_closed_failure}"
    )


@lru_cache(maxsize=1)
def _authority() -> tuple[
    dict[str, dict[str, Any]],
    dict[str, str],
    str,
]:
    samples = {
        row["case_id"]: row
        for row in (
            json.loads(line)
            for line in _BATCH.read_text(encoding="utf-8").splitlines()
            if line
        )
        if row.get("case_id") in _MUTATION_CASE_IDS
    }
    representative = json.loads(_REPRESENTATIVE.read_text(encoding="utf-8"))
    commitments = {
        row["case_id"]: row["source_case_commitment"]
        for row in representative["rows"]
        if row.get("case_id") in _MUTATION_CASE_IDS
    }
    manifest_path = (
        _RC0029_MANIFEST
        if _RC0029_MANIFEST.exists()
        else _PREDECESSOR_MANIFEST
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    closure = manifest.get("source_dependency_closure_sha256")
    assert set(samples) == set(_MUTATION_CASE_IDS)
    assert set(commitments) == set(_MUTATION_CASE_IDS)
    assert type(closure) is str and len(closure) == 64
    return samples, commitments, closure


@lru_cache(maxsize=None)
def _execution(case_id: str) -> Any:
    samples, commitments, closure = _authority()
    runtime = importlib.import_module(_RUNTIME)
    value = runtime.execute_step11_rc0029_experiment_private(
        samples[case_id]["input"],
        case_id=case_id,
        source_case_commitment=commitments[case_id],
        source_dependency_closure_sha256=closure,
    )
    result = value.body_free_result
    assert result.disposition == "selected", (
        "RC0029_MUTATION_BASELINE_NOT_SELECTED:"
        f"{case_id}:{result.closed_failure_codes}"
    )
    assert value.experiment_candidates
    assert value.parsed_witnesses
    assert value.successor_snapshot is not None
    assert value.lexical_atom_specs is not None
    return value


def _capture_closed_codes(call: Callable[[], Any]) -> tuple[str, ...]:
    try:
        result = call()
    except BaseException as error:
        code = getattr(error, "code", None)
        if type(code) is str:
            return (code,)
        return ("UNEXPECTED_" + type(error).__name__.upper(),)
    if type(result) in {tuple, list} and all(
        type(item) is str for item in result
    ):
        return tuple(result)
    for name in ("failure_codes", "closed_failure_codes", "issue_codes"):
        values = getattr(result, name, None)
        if type(values) in {tuple, list} and all(
            type(item) is str for item in values
        ):
            return tuple(values)
    return ()


def _candidate(case_id: str) -> Any:
    return _execution(case_id).experiment_candidates[0]


def _witness(case_id: str) -> Any:
    return _execution(case_id).parsed_witnesses[0]


def _matcher_codes(case_id: str, witness: Any) -> tuple[str, ...]:
    matcher = importlib.import_module(_MATCHER)
    return _capture_closed_codes(
        lambda: matcher.match_step11_rc0029_experiment_surface(
            witness,
            successor_snapshot=_execution(case_id).successor_snapshot,
        )
    )


def _gate_codes(case_id: str, candidate: Any) -> tuple[str, ...]:
    execution = _execution(case_id)
    gate = importlib.import_module(_GATE)
    base = execution.base_execution
    return _capture_closed_codes(
        lambda: gate.evaluate_step11_rc0029_experiment_candidate(
            candidate,
            successor_snapshot=execution.successor_snapshot,
            lexical_atom_specs=execution.lexical_atom_specs,
            inventory_result=base.inventory_result,
            content_plan=base.content_plan,
            current_input=base.projected_current_input,
        )
    )


def _with_atoms(witness: Any, **updates: Any) -> Any:
    names = {
        "construction_atoms",
        "relation_atoms",
        "semantic_link_atoms",
        "explicit_unknown_atoms",
    }
    current = {
        name: updates.get(name, getattr(witness, name)) for name in names
    }
    if "fused_structure_item_count" in {row.name for row in fields(witness)}:
        updates.setdefault(
            "fused_structure_item_count",
            sum(bool(current[name]) for name in names),
        )
    return replace(witness, **updates)


def _reception_target_field(value: Any) -> str:
    names = {row.name for row in fields(value)}
    if "target_handle_indices" in names:
        return "target_handle_indices"
    if "antecedent_handle_indices" in names:
        return "antecedent_handle_indices"
    raise AssertionError("RC0029_RECEPTION_TARGET_FIELD_MISSING")


def _replace_reception(
    value: Any,
    *,
    targets: tuple[int, ...] | None = None,
    supports: tuple[int, ...] | None = None,
    **updates: Any,
) -> Any:
    names = {row.name for row in fields(value)}
    if targets is not None:
        updates[_reception_target_field(value)] = targets
    if supports is not None and "supporting_handle_indices" in names:
        updates["supporting_handle_indices"] = supports
    return replace(value, **updates)


def _other_handle_index(witness: Any, excluded: tuple[int, ...]) -> int:
    return next(
        row.handle_index
        for row in witness.natural_handles
        if row.handle_index not in excluded
    )


def _natural_handle_swap(witness: Any) -> Any:
    left, right, *rest = witness.natural_handles
    names = {row.name for row in fields(left)} - {"handle_index"}
    left_updates = {name: getattr(right, name) for name in names}
    right_updates = {name: getattr(left, name) for name in names}
    return replace(
        witness,
        natural_handles=(
            replace(left, **left_updates),
            replace(right, **right_updates),
            *rest,
        ),
    )


def _valid_other_input_handle_swap(witness: Any) -> Any:
    other = _witness("nls3s_b001_0043")
    signature_names = {
        "semantic_head_kind",
        "semantic_head_text",
        "qualifier_tokens",
    }
    existing = {
        tuple(getattr(row, name) for name in sorted(signature_names))
        for row in witness.natural_handles
    }
    replacement = next(
        row
        for row in other.natural_handles
        if tuple(
            getattr(row, name) for name in sorted(signature_names)
        )
        not in existing
    )
    target, *rest = witness.natural_handles
    names = {row.name for row in fields(target)} - {"handle_index"}
    return replace(
        witness,
        natural_handles=(
            replace(
                target,
                **{name: getattr(replacement, name) for name in names},
            ),
            *rest,
        ),
    )


def _parser_metadata_attack(name: str) -> tuple[str, ...]:
    matcher = importlib.import_module(_MATCHER)
    body = _candidate("nls3s_b001_0001").final_utf8_bytes
    return _capture_closed_codes(
        lambda: matcher.parse_step11_rc0029_experiment_surface(
            body,
            **{name: ()},
        )
    )


def _gate_generic_body() -> tuple[str, ...]:
    candidate = _candidate("nls3s_b001_0019")
    base_bytes = candidate.base_candidate.final_utf8_bytes
    forged = replace(
        candidate,
        rendered_surface=replace(
            candidate.rendered_surface,
            utf8_bytes=base_bytes,
            sha256=hashlib.sha256(base_bytes).hexdigest(),
            added_observation_line_count=0,
            fused_structure_item_count=0,
            fused_structure_group_count=0,
            reception_binding_count=0,
        ),
    )
    return _gate_codes("nls3s_b001_0019", forged)


def _relation_attack(kind: str) -> tuple[str, ...]:
    case_id = "nls3s_b001_0019"
    witness = _witness(case_id)
    relation = witness.relation_atoms[0]
    if kind in {"endpoint", "endpoint_role"}:
        forged_relation = replace(
            relation,
            from_handle_index=relation.to_handle_index,
            to_handle_index=relation.from_handle_index,
        )
    elif kind == "direction":
        forged_relation = replace(
            relation,
            direction=(
                "bidirectional"
                if relation.direction == "source_to_target"
                else "source_to_target"
            ),
        )
    else:
        forged_relation = replace(
            relation,
            effective_relation_type=(
                "contrast"
                if relation.effective_relation_type != "contrast"
                else "coexistence"
            ),
        )
    forged = _with_atoms(
        witness,
        relation_atoms=(forged_relation, *witness.relation_atoms[1:]),
    )
    return _matcher_codes(case_id, forged)


def _construction_attack(kind: str) -> tuple[str, ...]:
    case_id = "nls3s_b001_0063"
    witness = _witness(case_id)
    atoms = witness.construction_atoms
    if kind in {"delete", "flatten"}:
        forged = _with_atoms(witness, construction_atoms=atoms[:-1])
        return _matcher_codes(case_id, forged)
    atom = atoms[0]
    roles = atom.role_owner_bindings
    if kind == "duplicate":
        forged_roles = (*roles, roles[-1])
    elif kind == "orphan":
        forged_roles = (
            replace(roles[0], handle_index=10_000),
            *roles[1:],
        )
    elif kind == "owner":
        forged_roles = (
            replace(
                roles[0],
                handle_index=_other_handle_index(
                    witness, (roles[0].handle_index,)
                ),
            ),
            *roles[1:],
        )
    elif kind == "field_key":
        forged_roles = (
            replace(roles[0], construction_position="forged_range"),
            *roles[1:],
        )
    else:
        raise AssertionError("RC0029_CONSTRUCTION_ATTACK_KIND_INVALID")
    forged_atom = replace(atom, role_owner_bindings=forged_roles)
    forged = _with_atoms(
        witness,
        construction_atoms=(forged_atom, *atoms[1:]),
    )
    return _matcher_codes(case_id, forged)


def _semantic_link_attack(kind: str) -> tuple[str, ...]:
    case_id = "nls3s_b001_0009"
    witness = _witness(case_id)
    atom = witness.semantic_link_atoms[0]
    if kind == "endpoint":
        forged_atom = replace(
            atom,
            from_handle_index=atom.to_handle_index,
            to_handle_index=atom.from_handle_index,
        )
    elif kind == "direction":
        forged_atom = replace(
            atom,
            direction=(
                "bidirectional"
                if atom.direction == "source_to_target"
                else "source_to_target"
            ),
        )
    else:
        forged_atom = replace(
            atom,
            relation_type=(
                "contrasts_with"
                if atom.relation_type != "contrasts_with"
                else "coexists_with"
            ),
        )
    forged = _with_atoms(witness, semantic_link_atoms=(forged_atom,))
    return _matcher_codes(case_id, forged)


def _unknown_attack(kind: str) -> tuple[str, ...]:
    case_id = "nls3s_b001_0035"
    witness = _witness(case_id)
    atoms = witness.explicit_unknown_atoms
    atom = atoms[0]
    if kind == "drop":
        forged_atoms = atoms[1:]
    elif kind == "duplicate":
        forged_atoms = (atom, atom, *atoms[1:])
    elif kind == "dimension":
        forged_atoms = (
            replace(atom, dimension="forged_valid_other_dimension"),
            *atoms[1:],
        )
    else:
        affected = atom.affected_handle_indices
        if len(affected) > 1:
            changed = tuple(reversed(affected))
        else:
            changed = (
                _other_handle_index(witness, affected),
            )
        forged_atoms = (
            replace(atom, affected_handle_indices=changed),
            *atoms[1:],
        )
    forged = _with_atoms(witness, explicit_unknown_atoms=forged_atoms)
    return _matcher_codes(case_id, forged)


def _handle_attack(kind: str) -> tuple[str, ...]:
    case_id = "nls3s_b001_0035"
    witness = _witness(case_id)
    if kind == "collision":
        left, right, *rest = witness.natural_handles
        forged = replace(
            witness,
            natural_handles=(
                left,
                replace(right, handle_text=left.handle_text),
                *rest,
            ),
        )
    else:
        forged = _valid_other_input_handle_swap(witness)
    return _matcher_codes(case_id, forged)


def _reception_attack(kind: str) -> tuple[str, ...]:
    case_id = (
        "nls3s_b001_0100"
        if kind in {"drop", "duplicate"}
        else "nls3s_b001_0035"
    )
    witness = _witness(case_id)
    bindings = witness.reception_bindings
    if kind == "drop":
        forged_bindings = bindings[:-1]
    elif kind == "duplicate":
        forged_bindings = (*bindings, bindings[0])
    else:
        binding = bindings[0]
        target_field = _reception_target_field(binding)
        targets = getattr(binding, target_field)
        if kind == "missing":
            changed = ()
        else:
            changed = (_other_handle_index(witness, targets),)
        forged_bindings = (
            _replace_reception(binding, targets=changed),
            *bindings[1:],
        )
    forged = replace(witness, reception_bindings=forged_bindings)
    return _matcher_codes(case_id, forged)


def _semantic_coverage_attack(value: Any) -> tuple[str, ...]:
    candidate = replace(
        _candidate("nls3s_b001_0019"),
        semantic_coverage_authorized=value,
    )
    return _gate_codes("nls3s_b001_0019", candidate)


def _catalog_attack(kind: str) -> tuple[str, ...]:
    owner = importlib.import_module(_CATALOG)
    catalog = {
        key: dict(value) if type(value) is dict else value
        for key, value in owner.STEP11_RC0029_EXPERIMENT_SURFACE_CATALOG.items()
    }
    if kind == "token":
        name = "morphology"
        key = next(iter(catalog[name]))
        catalog[name][key] = catalog[name][key] + "改変"
    else:
        name = "construction_surface_tokens"
        key = next(iter(catalog[name]))
        catalog[name]["forged_atom_code"] = catalog[name].pop(key)
    return _capture_closed_codes(
        lambda: owner.validate_step11_rc0029_experiment_surface_catalog(
            catalog
        )
    )


def _runtime_limit_attack(*, candidate_limit: int, replan_limit: int) -> tuple[str, ...]:
    samples, commitments, closure = _authority()
    case_id = "nls3s_b001_0001"
    runtime = importlib.import_module(_RUNTIME)
    return _capture_closed_codes(
        lambda: runtime.execute_step11_rc0029_experiment_private(
            samples[case_id]["input"],
            case_id=case_id,
            source_case_commitment=commitments[case_id],
            source_dependency_closure_sha256=closure,
            candidate_limit=candidate_limit,
            replan_limit=replan_limit,
        )
    )


def _resource_plus_one_attack() -> tuple[str, ...]:
    runtime = importlib.import_module(_RUNTIME)
    result = _execution("nls3s_b001_0001").body_free_result
    forged = replace(
        result,
        experiment_candidate_count=result.bounded_candidate_limit + 1,
    )
    return _capture_closed_codes(
        lambda: runtime.validate_step11_rc0029_experiment_result(forged)
    )


def _observe_attack(attack_id: str) -> tuple[str, ...]:
    if attack_id == "generic-body-replacement-retaining-forward-metadata":
        return _gate_generic_body()
    if attack_id == "forward-metadata-injection":
        return _parser_metadata_attack(attack_id.replace("-", "_"))
    if attack_id == "relation-from-to-swap":
        return _relation_attack("endpoint")
    if attack_id == "relation-direction-reverse":
        return _relation_attack("direction")
    if attack_id == "effective-relation-type-mutation":
        return _relation_attack("type")
    if attack_id == "inner-construction-deletion":
        return _construction_attack("delete")
    if attack_id == "construction-slot-duplicate":
        return _construction_attack("duplicate")
    if attack_id == "construction-slot-orphan":
        return _construction_attack("orphan")
    if attack_id == "construction-role-field-key-mismatch":
        return _construction_attack("field_key")
    if attack_id == "participation-owner-mutation":
        return _construction_attack("owner")
    if attack_id == "semantic-link-endpoint-mutation":
        return _semantic_link_attack("endpoint")
    if attack_id == "semantic-link-type-mutation":
        return _semantic_link_attack("type")
    if attack_id == "semantic-link-direction-mutation":
        return _semantic_link_attack("direction")
    if attack_id == "explicit-unknown-drop":
        return _unknown_attack("drop")
    if attack_id == "explicit-unknown-duplicate":
        return _unknown_attack("duplicate")
    if attack_id == "explicit-unknown-valid-other-dimension":
        return _unknown_attack("dimension")
    if attack_id == "explicit-unknown-affected-owner-order-mutation":
        return _unknown_attack("owner")
    if attack_id == "natural-handle-collision":
        return _handle_attack("collision")
    if attack_id == "valid-other-input-natural-handle-cross-swap":
        return _handle_attack("cross_swap")
    if attack_id == "depth-compaction-overflow":
        case_id = "nls3s_b001_0063"
        witness = _witness(case_id)
        forged = replace(
            witness,
            fused_structure_item_count=(
                witness.fused_structure_item_count + 1
            ),
        )
        return _matcher_codes(case_id, forged)
    if attack_id == "generic-reception-without-antecedent":
        return _reception_attack("missing")
    if attack_id == "reception-antecedent-owner-swap":
        return _reception_attack("swap")
    if attack_id == "required-reception-obligation-drop":
        return _reception_attack("drop")
    if attack_id == "required-reception-obligation-duplicate":
        return _reception_attack("duplicate")
    if attack_id == "semantic-coverage-authorized-bool-true":
        return _semantic_coverage_attack(True)
    if attack_id == "semantic-coverage-authorized-int-one":
        return _semantic_coverage_attack(1)
    if attack_id == "semantic-coverage-authorized-string-false":
        return _semantic_coverage_attack("false")
    if attack_id == "stale-artifact-hash":
        candidate = replace(
            _candidate("nls3s_b001_0019"),
            lexical_atom_specs_sha256="0" * 64,
        )
        return _gate_codes("nls3s_b001_0019", candidate)
    if attack_id == "valid-other-input-successor-swap":
        matcher = importlib.import_module(_MATCHER)
        return _capture_closed_codes(
            lambda: matcher.match_step11_rc0029_experiment_surface(
                _witness("nls3s_b001_0019"),
                successor_snapshot=_execution(
                    "nls3s_b001_0043"
                ).successor_snapshot,
            )
        )
    if attack_id == "catalog-token-mutation":
        return _catalog_attack("token")
    if attack_id == "resource-bound-plus-one":
        return _resource_plus_one_attack()
    if attack_id == "candidate-count-thirteen":
        return _runtime_limit_attack(candidate_limit=13, replan_limit=1)
    if attack_id == "replan-count-two":
        return _runtime_limit_attack(candidate_limit=12, replan_limit=2)
    raise AssertionError("RC0029_MUTATION_ATTACK_NOT_IMPLEMENTED:" + attack_id)


@pytest.mark.parametrize("attack", _ATTACKS, ids=_node_id)
def test_rc0029_e0b_mandatory_attack_has_closed_consumer(
    attack: _Attack,
) -> None:
    observed = _observe_attack(attack.attack_id)
    assert attack.expected_closed_failure in observed, (
        "E0B_ATTACK_DID_NOT_FIRE_REQUIRED_CLOSED_CODE:"
        f"{attack.attack_id}:expected={attack.expected_closed_failure}:"
        f"observed={observed}"
    )


def _parsed_handle_index_by_source_owner(
    candidate: Any,
    witness: Any,
) -> dict[str, int]:
    parsed_by_text = {
        row.handle_text: row.handle_index for row in witness.natural_handles
    }
    assert len(parsed_by_text) == len(witness.natural_handles)
    return {
        row.source_owner_id: parsed_by_text[row.handle_text]
        for row in candidate.natural_handle_specs.handles
    }


def test_rc0029_e0b_0009_direct_semantic_owners_are_not_parent_fallbacks(
) -> None:
    case_id = "nls3s_b001_0009"
    execution = _execution(case_id)
    candidate = _candidate(case_id)
    direct_owner_ids = {
        row.source_owner_id
        for row in candidate.natural_handle_specs.handles
        if row.source_owner_kind == "semantic_unit"
    }
    actual_owner_ids = {
        str(row.actual_source_id)
        for row in execution.successor_snapshot.base_snapshot.nuclei
    }
    participation_owner_ids = {
        row.target_owner_id
        for row in execution.lexical_atom_specs.participation_bindings
        if row.target_owner_kind == "semantic_unit"
    }
    assert len(direct_owner_ids) == 2
    assert direct_owner_ids <= actual_owner_ids
    assert direct_owner_ids.isdisjoint(participation_owner_ids)
    assert {
        row.semantic_head_kind
        for row in candidate.natural_handle_specs.handles
    } == {"reaction", "change"}

    witness = _witness(case_id)
    dropped = _with_atoms(witness, semantic_link_atoms=())
    assert "STEP11_RC0029_SEMANTIC_LINK_BINDING_MISMATCH" in (
        _matcher_codes(case_id, dropped)
    )
    assert "STEP11_RC0029_SEMANTIC_LINK_ENDPOINT_MISMATCH" in (
        _semantic_link_attack("endpoint")
    )


def test_rc0029_e0b_0035_reception_uses_exact_opportunity_not_wider_ast(
) -> None:
    case_id = "nls3s_b001_0035"
    execution = _execution(case_id)
    candidate = _candidate(case_id)
    assert len(candidate.reception_bindings) == 1
    exact = candidate.reception_bindings[0]
    base_bindings = candidate.base_candidate.surface_ast.reception_antecedent_bindings
    matching = tuple(
        row
        for row in base_bindings
        if row.binding_id == exact.source_base_binding_id
    )
    assert len(matching) == 1
    base_binding = matching[0]
    actual_by_source = {
        str(row.source_id): str(row.actual_source_id)
        for row in execution.successor_snapshot.base_snapshot.nuclei
    }
    wider_targets = {
        actual_by_source[source_id]
        for source_id in base_binding.source_target_nucleus_ids
    }
    wider_supports = {
        actual_by_source[source_id]
        for source_id in base_binding.supporting_nucleus_ids
    }
    assert set(exact.source_target_owner_ids) < wider_targets
    assert set(exact.supporting_source_owner_ids) != wider_supports

    witness = _witness(case_id)
    index_by_owner = _parsed_handle_index_by_source_owner(candidate, witness)
    parsed = witness.reception_bindings[0]
    target_field = _reception_target_field(parsed)
    exact_indices = tuple(index_by_owner[item] for item in exact.source_target_owner_ids)
    extra_owner = next(iter(wider_targets - set(exact.source_target_owner_ids)))
    extra_target = _replace_reception(
        parsed,
        targets=(*exact_indices, index_by_owner[extra_owner]),
    )
    forged_target = replace(
        witness,
        reception_bindings=(extra_target,),
    )
    assert "STEP11_RC0029_RECEPTION_ANTECEDENT_MISMATCH" in (
        _matcher_codes(case_id, forged_target)
    )

    if wider_supports and "supporting_handle_indices" in {
        row.name for row in fields(parsed)
    }:
        extra_support = _replace_reception(
            parsed,
            targets=getattr(parsed, target_field),
            supports=tuple(index_by_owner[item] for item in wider_supports),
        )
        forged_support = replace(
            witness,
            reception_bindings=(extra_support,),
        )
        assert "STEP11_RC0029_RECEPTION_ANTECEDENT_MISMATCH" in (
            _matcher_codes(case_id, forged_support)
        )


def test_rc0029_e0b_0100_second_required_opportunity_is_atomic(
) -> None:
    case_id = "nls3s_b001_0100"
    candidate = _candidate(case_id)
    witness = _witness(case_id)
    assert len(
        candidate.base_candidate.surface_ast.reception_antecedent_bindings
    ) == 1
    assert len(candidate.reception_bindings) == 2
    assert len(witness.reception_bindings) == 2
    additional = tuple(
        row for row in candidate.reception_bindings if row.additional_clause
    )
    assert len(additional) == 1
    assert additional[0].reception_act == "honor_concrete_action"
    assert len(additional[0].source_target_owner_ids) == 1
    handle_by_owner = {
        row.source_owner_id: row
        for row in candidate.natural_handle_specs.handles
    }
    assert handle_by_owner[
        additional[0].source_target_owner_ids[0]
    ].semantic_head_kind == "action"

    assert "STEP11_RC0029_RECEPTION_CARDINALITY_MISMATCH" in (
        _reception_attack("drop")
    )
    assert "STEP11_RC0029_RECEPTION_CARDINALITY_MISMATCH" in (
        _reception_attack("duplicate")
    )

    first, second = witness.reception_bindings
    first_targets = getattr(first, _reception_target_field(first))
    second_targets = getattr(second, _reception_target_field(second))
    forged = replace(
        witness,
        reception_bindings=(
            _replace_reception(
                first,
                targets=first_targets,
                reception_act=second.reception_act,
            ),
            _replace_reception(
                second,
                targets=second_targets,
                reception_act=first.reception_act,
            ),
        ),
    )
    observed = _matcher_codes(case_id, forged)
    assert (
        "STEP11_RC0029_RECEPTION_ANTECEDENT_MISMATCH" in observed
        or "STEP11_RC0029_RECEPTION_ACT_ASSOCIATION_MISMATCH" in observed
    )


def test_rc0029_e0b_matcher_is_semantic_multiset_not_source_order_zip(
) -> None:
    case_id = "nls3s_b001_0063"
    witness = _witness(case_id)
    permuted = replace(
        witness,
        construction_atoms=tuple(reversed(witness.construction_atoms)),
        relation_atoms=tuple(reversed(witness.relation_atoms)),
        semantic_link_atoms=tuple(reversed(witness.semantic_link_atoms)),
        explicit_unknown_atoms=tuple(reversed(witness.explicit_unknown_atoms)),
        reception_bindings=tuple(reversed(witness.reception_bindings)),
    )
    matcher = importlib.import_module(_MATCHER)
    result = matcher.match_step11_rc0029_experiment_surface(
        permuted,
        successor_snapshot=_execution(case_id).successor_snapshot,
    )
    assert result.hard_verified is True
    assert result.unique_solution_count == 1

    collision_case = "nls3s_b001_0035"
    collision_witness = _witness(collision_case)
    event_handles = tuple(
        row
        for row in collision_witness.natural_handles
        if row.semantic_head_kind == "event"
    )
    assert len(event_handles) == 2
    assert len(
        {
            row.semantic_head_kind
            for row in event_handles
        }
    ) == 1
    assert "STEP11_RC0029_PARTICIPATION_OWNER_MISMATCH" in (
        _matcher_codes(
            collision_case,
            _natural_handle_swap(collision_witness),
        )
    )


def test_rc0029_e0b_construction_shorthand_requires_same_parent_and_layout(
) -> None:
    case_id = "nls3s_b001_0063"
    execution = _execution(case_id)
    candidate = _candidate(case_id)
    assert len(candidate.construction_atoms) >= 2
    for atom in candidate.construction_atoms:
        owner_ordinals = {
            ordinal
            for role in atom.role_atoms
            for ordinal in role.target_owner_ordinals
        }
        assert len(owner_ordinals) == 1

    witness = _witness(case_id)
    first = witness.construction_atoms[0]
    other_code = next(
        row.construction_code
        for row in witness.construction_atoms[1:]
        if row.construction_code != first.construction_code
    )
    forged = _with_atoms(
        witness,
        construction_atoms=(
            replace(first, construction_code=other_code),
            *witness.construction_atoms[1:],
        ),
    )
    observed = _matcher_codes(case_id, forged)
    assert (
        "STEP11_RC0029_CONSTRUCTION_SLOT_BINDING_MISMATCH" in observed
        or "STEP11_RC0029_CONSTRUCTION_CARDINALITY_MISMATCH" in observed
    )
    assert "STEP11_RC0029_CONSTRUCTION_CARDINALITY_MISMATCH" in (
        _construction_attack("delete")
    )


@pytest.mark.parametrize(
    "case_id,expected_atom_count",
    (
        ("nls3s_b001_0009", 2),
        ("nls3s_b001_0035", 8),
        ("nls3s_b001_0063", 11),
        ("nls3s_b001_0100", 10),
    ),
)
def test_rc0029_e0b_family_component_multiset_is_exact(
    case_id: str,
    expected_atom_count: int,
) -> None:
    candidate = _candidate(case_id)
    assert len(candidate.fused_structure_groups) == 1
    group = candidate.fused_structure_groups[0]
    denominator = (
        len(candidate.construction_atoms)
        + len(candidate.relation_atoms)
        + len(candidate.semantic_link_atoms)
        + len(candidate.explicit_unknown_atoms)
        + len(candidate.reception_bindings)
    )
    assert denominator == expected_atom_count
    assert group.typed_atom_count == denominator
    assert len(group.typed_atom_keys) == denominator
    assert len(set(group.typed_atom_keys)) == denominator
    assert candidate.rendered_surface.fused_structure_group_count == 1

    witness = _witness(case_id)
    changed = replace(
        witness,
        fused_structure_group_count=witness.fused_structure_group_count + 1,
    )
    observed = _matcher_codes(case_id, changed)
    assert "STEP11_RC0029_FUSED_GROUP_COMMITMENT_MISMATCH" in observed


def test_rc0029_e0b_attack_ledger_is_exact_nonempty_and_unique() -> None:
    assert len(_ATTACKS) == 33
    assert len({row.attack_id for row in _ATTACKS}) == len(_ATTACKS)
    assert all(row.expected_closed_failure for row in _ATTACKS)
    assert all(
        row.expected_closed_failure.startswith("STEP11_RC0029_")
        for row in _ATTACKS
    )
    assert {
        "relation-from-to-swap",
        "inner-construction-deletion",
        "semantic-link-endpoint-mutation",
        "explicit-unknown-drop",
        "natural-handle-collision",
        "required-reception-obligation-drop",
        "resource-bound-plus-one",
    } <= {row.attack_id for row in _ATTACKS}


def test_rc0029_e0b_no_assertion_weakening_empty_expectation_or_gate_downgrade(
) -> None:
    expected = tuple(row.expected_closed_failure for row in _ATTACKS)
    assert expected
    assert all(expected)
    assert len(expected) == len(_ATTACKS)
    assert "STEP11_RC0029_RELATION_ENDPOINT_MISMATCH" in expected
    assert "STEP11_RC0029_PARTICIPATION_OWNER_MISMATCH" in expected
    assert "STEP11_RC0029_RECEPTION_CARDINALITY_MISMATCH" in expected
    assert "STEP11_RC0029_RESOURCE_BOUND_EXCEEDED" in expected


def test_rc0029_e0b_does_not_double_count_static_or_privacy_suites() -> None:
    attack_ids = {row.attack_id for row in _ATTACKS}
    assert not any("forward-helper-imported" in item for item in attack_ids)
    assert not any("shareable-material" in item for item in attack_ids)
