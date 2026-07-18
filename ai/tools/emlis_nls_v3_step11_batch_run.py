#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""Run Cycle 001 through the offline rc0023 adapter.

The body-full packet and HMAC key are private local artifacts.  The companion
summary contains commitments and closed structural metrics only.  This tool
does not import or activate the production reply route.
"""

import argparse
from dataclasses import fields, is_dataclass
import hashlib
import math
from pathlib import Path
import platform
import re
import sys
from typing import Any, Mapping, Sequence


AI_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = AI_ROOT.parent
SERVICES = AI_ROOT / "services" / "ai_inference"
HELPERS = AI_ROOT / "tests" / "helpers"
TOOLS = AI_ROOT / "tools"
for entry in (SERVICES, HELPERS, TOOLS):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

from emlis_ai_nls_v3_artifact_contract import (  # noqa: E402
    artifact_sha256,
)
from emlis_ai_step10_app_reachable_contract_v3 import (  # noqa: E402
    project_app_reachable_input,
)
from emlis_ai_step10_evidence_v3 import (  # noqa: E402
    commitment_key_id,
    hmac_commit_bytes,
    hmac_commit_json,
    verify_batch_evidence,
)
from emlis_ai_step11_cycle_evidence_v3 import (  # noqa: E402
    STEP11_COMMITMENT_POLICY_SHA256,
    STEP11_REVIEW_RUBRIC_SHA256,
    STEP11_RUNTIME_VALIDATION_PROTOCOL_SHA256,
    build_step11_batch_run_summary,
    build_step11_private_verification_receipt,
    validate_step11_batch_run_summary,
    validate_step11_dependency_manifest,
)
from emlis_ai_step11_natural_surface_matcher_v3 import (  # noqa: E402
    match_step11_natural_surface,
    parse_step11_natural_surface,
)
from emlis_ai_step11_natural_surface_v3 import (  # noqa: E402
    STEP11_CANDIDATE_VERSION_ID,
)
from emlis_ai_step11_runtime_adapter_v3 import (  # noqa: E402
    Step11RuntimeAdapterError,
    execute_step11_offline_v3,
    runtime_execution_body_free_summary,
    validate_step11_runtime_execution,
)
from emlis_nls_v3_batch_run import (  # noqa: E402
    _read_key,
    _secure_unlink,
    _write_json,
    load_validated_batch,
)
from emlis_nls_v3_step11_dependency_manifest import (  # noqa: E402
    assert_current_step11_dependency_manifest,
)
from emlis_nls_v3_s2_sample_registry import load_canonical_json  # noqa: E402


STEP11_PRIVATE_PACKET_SCHEMA = (
    "cocolon.emlis.nls_v3.private_batch_packet.step11.v1"
)
_CASE_RE = re.compile(r"^nls3s_b001_[0-9]{4}$")
_LOWER_CODE_CLEAN_RE = re.compile(r"[^a-z0-9_]+")
_SURFACE_ENDPOINT_ROLES = frozenset({"action", "affect", "proposition"})


def _json_material(value: Any, path: str = "$") -> Any:
    """Convert private lineage to strict canonical-JSON material.

    The frozen artifact canonicalizer intentionally rejects tuples, floats and
    bytes.  These tagged projections preserve their exact value and type before
    an HMAC is calculated; they are never emitted in the body-free summary.
    """

    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_material(getattr(value, field.name), f"{path}.{field.name}")
            for field in fields(value)
        }
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, child in value.items():
            if type(key) is not str:
                raise ValueError(f"step11_private_non_string_key:{path}")
            result[key] = _json_material(child, f"{path}.{key}")
        return result
    if type(value) in {list, tuple}:
        return [
            _json_material(child, f"{path}[{index}]")
            for index, child in enumerate(value)
        ]
    if type(value) is bytes:
        return {"tag": "bytes_hex", "value": value.hex()}
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError(f"step11_private_non_finite_float:{path}")
        return {"tag": "float_decimal", "value": format(value, ".17g")}
    if value is None or type(value) in {bool, int, str}:
        return value
    raise ValueError(f"step11_private_value_type_invalid:{path}:{type(value).__name__}")


def _commit_json(key: bytes, domain: str, value: Any) -> str:
    return hmac_commit_json(key, domain, _json_material(value))


def _safe_family(value: str) -> str:
    cleaned = _LOWER_CODE_CLEAN_RE.sub("_", value.lower()).strip("_")
    if not cleaned:
        return "unknown"
    if not cleaned[0].isalpha():
        cleaned = "form_" + cleaned
    return cleaned[:64].rstrip("_")


def _semantic_form_family(form_id: str) -> str:
    """Return the semantic form family without its catalog variant index.

    Parsed witness form ids encode the catalog variant as one or more trailing
    decimal components.  Removing only those components preserves relation
    type/direction and unknown-boundary dimensions while making the aggregate
    independent of the selected wording variant.
    """

    if type(form_id) is not str or not form_id:
        raise ValueError("step11_surface_profile_form_id_invalid")
    components = form_id.split(":")
    while len(components) > 1 and components[-1].isdigit():
        components.pop()
    return _safe_family(":".join(components))


def _surface_distribution_fields(
    atoms: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Derive body-free distribution evidence from parsed witness atoms.

    Literal values are used only as ephemeral equality keys.  The returned
    profile contains counts and catalog identities, never a source fragment.
    A direct reception has an owned antecedent only when every quoted target
    has exactly one observation-side owner.  A typed reception is non-literal
    anaphora only when each visible local reference resolves to exactly one
    earlier, source-backed observation reference with the same endpoint role.
    Both checks use the parsed witness only and never consult the source
    semantic contract.
    """

    if not atoms:
        raise ValueError("step11_surface_profile_atom_required")
    observation_counts: dict[str, int] = {}
    reception_atoms: list[tuple[int, Mapping[str, Any]]] = []
    introduced_by_ordinal: dict[int, list[tuple[int, str]]] = {}

    def reference_row(value: Any) -> tuple[int, str]:
        if type(value) is not dict or set(value) != {
            "reference_ordinal",
            "endpoint_role",
        }:
            raise ValueError("step11_surface_reference_invalid")
        ordinal = value["reference_ordinal"]
        role = value["endpoint_role"]
        if (
            type(ordinal) is not int
            or ordinal < 1
            or type(role) is not str
            or role not in _SURFACE_ENDPOINT_ROLES
        ):
            raise ValueError("step11_surface_reference_invalid")
        return ordinal, role

    for atom_index, atom in enumerate(atoms):
        if type(atom) is not dict:
            raise ValueError("step11_surface_profile_atom_invalid")
        section_role = atom.get("section_role")
        form_id = atom.get("form_id")
        fragments = atom.get("source_fragments")
        if (
            section_role not in {"observation", "reception"}
            or type(form_id) is not str
            or not form_id
            or type(fragments) not in {list, tuple}
            or any(type(fragment) is not str or not fragment for fragment in fragments)
        ):
            raise ValueError("step11_surface_profile_atom_invalid")
        introduced_reference = atom.get("introduced_reference")
        if introduced_reference is not None:
            ordinal, role = reference_row(introduced_reference)
            if section_role != "observation" or not fragments:
                raise ValueError("step11_introduced_reference_owner_invalid")
            introduced_by_ordinal.setdefault(ordinal, []).append(
                (atom_index, role)
            )
        if section_role == "observation":
            for fragment in fragments:
                observation_counts[fragment] = observation_counts.get(fragment, 0) + 1
        else:
            reception_atoms.append((atom_index, atom))

    direct_owned = False
    direct_present = False
    anaphoric_present = False
    reception_literal_count = 0
    for atom_index, atom in reception_atoms:
        form_id = atom["form_id"]
        fragments = tuple(atom["source_fragments"])
        if form_id.startswith("reception:typed:"):
            if fragments:
                raise ValueError("step11_typed_reception_literal_forbidden")
            references = atom.get("reception_antecedent_references")
            if type(references) not in {list, tuple} or not references:
                raise ValueError("step11_typed_reception_reference_required")
            typed_references = tuple(reference_row(row) for row in references)
            if len(set(typed_references)) != len(typed_references):
                raise ValueError("step11_typed_reception_reference_duplicate")
            for ordinal, role in typed_references:
                owners = introduced_by_ordinal.get(ordinal, ())
                if not owners:
                    raise ValueError("step11_typed_reception_reference_unowned")
                if len(owners) != 1:
                    raise ValueError(
                        "step11_typed_reception_reference_owner_ambiguous"
                    )
                owner_index, owner_role = owners[0]
                if owner_role != role:
                    raise ValueError(
                        "step11_typed_reception_reference_role_mismatch"
                    )
                if owner_index >= atom_index:
                    raise ValueError("step11_typed_reception_reference_forward")
            anaphoric_present = True
            continue
        if form_id.startswith("reception:anaphoric:"):
            anaphoric_present = True
            if fragments:
                raise ValueError("step11_anaphoric_reception_literal_forbidden")
            continue
        if not form_id.startswith("reception:direct:") or not fragments:
            raise ValueError("step11_reception_content_kind_invalid")
        direct_present = True
        reception_literal_count += len(fragments)
        direct_owned = direct_owned or all(
            observation_counts.get(fragment, 0) == 1 for fragment in fragments
        )

    if direct_present:
        prefix = "mixed" if anaphoric_present else "direct"
        ownership = "owned_antecedent" if direct_owned else "unowned_antecedent"
        reception_content_kind = f"{prefix}_{ownership}"
    elif anaphoric_present:
        reception_content_kind = "anaphoric"
    else:
        reception_content_kind = "none"

    observation_literal_count = sum(observation_counts.values())
    unique_literal_owner_count = len(observation_counts)
    return {
        "opening_semantic_family": _semantic_form_family(atoms[0]["form_id"]),
        "opening_variant_id": _safe_family(atoms[0]["form_id"]),
        "reception_content_kind": reception_content_kind,
        "observation_literal_count": observation_literal_count,
        "unique_literal_owner_count": unique_literal_owner_count,
        "literal_replay_count": (
            observation_literal_count - unique_literal_owner_count
        ),
        "reception_literal_count": reception_literal_count,
    }


def _environment_sha256() -> str:
    return artifact_sha256(
        {
            "schema_version": "cocolon.emlis.nls_v3.local_environment.step11.v1",
            "python_implementation": platform.python_implementation(),
            "python_version": list(sys.version_info[:3]),
            "platform_system": platform.system(),
            "platform_machine": platform.machine(),
        }
    )


def _runner_sha256() -> str:
    return hashlib.sha256(Path(__file__).resolve().read_bytes()).hexdigest()


def _initial_private_by_case(
    initial_private_packet: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    rows = initial_private_packet.get("cases")
    if type(rows) is not list or len(rows) != 100:
        raise ValueError("step11_initial_private_exact_100_required")
    by_case = {
        row.get("case_id"): row
        for row in rows
        if type(row) is dict and type(row.get("case_id")) is str
    }
    if len(by_case) != 100:
        raise ValueError("step11_initial_private_case_set_invalid")
    return by_case


def _initial_summary_by_case(
    initial_summary: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    rows = initial_summary.get("case_rows")
    if type(rows) is not list or len(rows) != 100:
        raise ValueError("step11_initial_summary_exact_100_required")
    by_case = {
        row.get("case_id"): row
        for row in rows
        if type(row) is dict and type(row.get("case_id")) is str
    }
    if len(by_case) != 100:
        raise ValueError("step11_initial_summary_case_set_invalid")
    return by_case


def _candidate_set_material(execution: Any, key: bytes) -> list[dict[str, str]]:
    rows = []
    for candidate in execution.natural_candidates:
        rows.append(
            {
                "candidate_id": candidate.candidate_id,
                "body_commitment": hmac_commit_bytes(
                    key,
                    "candidate_body",
                    candidate.rendered_surface.utf8_bytes,
                ),
                "discourse_plan_commitment": _commit_json(
                    key, "candidate_discourse_plan", candidate.discourse_plan
                ),
                "surface_ast_commitment": _commit_json(
                    key, "candidate_surface_ast", candidate.surface_ast
                ),
            }
        )
    rows.sort(key=lambda row: row["candidate_id"])
    return rows


def _surface_profile(witness: Any, key: bytes) -> dict[str, Any]:
    atoms = tuple(witness.atoms)
    if not atoms:
        raise ValueError("step11_surface_profile_atom_required")
    atom_rows = [
        {
            "section_role": atom.section_role,
            "form_id": atom.form_id,
            "claim_kinds": list(atom.claim_kinds),
            "source_fragments": list(atom.source_fragments),
            "relation_type": atom.relation_type,
            "relation_direction": atom.relation_direction,
            "unknown_dimension_class": atom.unknown_dimension_class,
            "reception_act": atom.reception_act,
            "reception_scope": atom.reception_scope,
            "self_denial_not_fact": atom.self_denial_not_fact,
            "introduced_reference": (
                {
                    "reference_ordinal": (
                        atom.introduced_reference.reference_ordinal
                    ),
                    "endpoint_role": atom.introduced_reference.endpoint_role,
                }
                if atom.introduced_reference is not None
                else None
            ),
            "reception_antecedent_references": [
                {
                    "reference_ordinal": row.reference_ordinal,
                    "endpoint_role": row.endpoint_role,
                }
                for row in atom.reception_antecedent_references
            ],
        }
        for atom in atoms
    ]
    skeleton = _skeleton_material(atom_rows)
    return {
        "opening_family": _safe_family(atoms[0].form_id),
        "ending_family": _safe_family(atoms[-1].form_id),
        "predicate_families": sorted({_safe_family(atom.form_id) for atom in atoms}),
        "reception_act_families": sorted(
            {
                _safe_family(atom.reception_act)
                for atom in atoms
                if type(atom.reception_act) is str
            }
        ),
        "near_duplicate_skeleton_commitment": _commit_json(
            key, "near_duplicate_skeleton", skeleton
        ),
        **_surface_distribution_fields(atom_rows),
    }


def _skeleton_material(atoms: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "section_role": atom["section_role"],
            "form_id": atom["form_id"],
            "claim_kinds": list(atom["claim_kinds"]),
            "relation_type": atom["relation_type"],
            "relation_direction": atom["relation_direction"],
            "unknown_dimension_class": atom["unknown_dimension_class"],
            "reception_act": atom["reception_act"],
            "reception_scope": atom["reception_scope"],
            "self_denial_not_fact": atom["self_denial_not_fact"],
        }
        for atom in atoms
    ]


def _surface_profile_from_private_witness(
    witness: Mapping[str, Any], key: bytes
) -> dict[str, Any]:
    atoms = witness.get("atoms")
    if type(atoms) is not list or not atoms or any(type(row) is not dict for row in atoms):
        raise ValueError("step11_private_witness_atoms_invalid")
    return {
        "opening_family": _safe_family(atoms[0]["form_id"]),
        "ending_family": _safe_family(atoms[-1]["form_id"]),
        "predicate_families": sorted({_safe_family(row["form_id"]) for row in atoms}),
        "reception_act_families": sorted(
            {
                _safe_family(row["reception_act"])
                for row in atoms
                if type(row.get("reception_act")) is str
            }
        ),
        "near_duplicate_skeleton_commitment": _commit_json(
            key, "near_duplicate_skeleton", _skeleton_material(atoms)
        ),
        **_surface_distribution_fields(atoms),
    }


def _build_selected_case(
    sample: Mapping[str, Any],
    *,
    v1_body: str,
    execution: Any,
    commitment_key: bytes,
    run_id: str,
    source_dependency_closure_sha256: str,
    environment_sha256: str,
    runner_sha256: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    case_id = sample.get("case_id")
    if type(case_id) is not str or _CASE_RE.fullmatch(case_id) is None:
        raise ValueError("step11_case_id_invalid")
    issues = validate_step11_runtime_execution(execution)
    if issues:
        raise Step11RuntimeAdapterError(issues[0])
    if execution.status != "selected" or execution.selected_candidate is None:
        raise Step11RuntimeAdapterError("STEP11_RUNTIME_NO_VALID_CANDIDATE")

    selected = execution.selected_candidate
    selected_body = execution.final_utf8_bytes
    if type(selected_body) is not bytes or not selected_body:
        raise Step11RuntimeAdapterError("STEP11_RUNTIME_SELECTED_BYTES_INVALID")
    witness = parse_step11_natural_surface(selected_body)
    binding = match_step11_natural_surface(
        witness,
        inventory_result=execution.inventory_result,
        content_plan=execution.content_plan,
        discourse_plan=selected.discourse_plan,
        current_input=execution.projected_current_input,
    )
    if binding.verified is not True or binding.issue_codes:
        raise Step11RuntimeAdapterError("STEP11_RUNTIME_BINDING_NOT_VERIFIED")
    matching_gates = tuple(
        gate
        for gate in execution.selection_result.gate_results
        if gate.candidate_id == selected.candidate_id
    )
    if len(matching_gates) != 1 or matching_gates[0].hard_pass is not True:
        raise Step11RuntimeAdapterError("STEP11_RUNTIME_SELECTED_GATE_INVALID")
    gate = matching_gates[0]

    projected_input = project_app_reachable_input(sample["input"])
    runtime_summary = runtime_execution_body_free_summary(execution)
    candidate_set = _candidate_set_material(execution, commitment_key)
    witness_binding = {"witness": witness, "binding": binding}
    selector_attributes = {
        "selected_candidate_id": selected.candidate_id,
        "selector_attributes": list(gate.selector_attributes),
        "evaluated_candidate_ids": list(
            execution.selection_result.evaluated_candidate_ids
        ),
    }

    commitments = {
        "case_identity_commitment": _commit_json(
            commitment_key, "case_identity", projected_input
        ),
        "observation_stage_context_commitment": _commit_json(
            commitment_key,
            "observation_stage_context",
            execution.observation_stage_context,
        ),
        "source_observation_plan_commitment": _commit_json(
            commitment_key, "source_observation_plan", execution.grounded_plan
        ),
        "obligation_ledger_commitment": _commit_json(
            commitment_key,
            "obligation_ledger",
            execution.inventory_result.ledger,
        ),
        "content_plan_commitment": _commit_json(
            commitment_key, "content_plan", execution.content_plan
        ),
        "candidate_set_commitment": _commit_json(
            commitment_key, "candidate_set", candidate_set
        ),
        "selected_discourse_plan_commitment": _commit_json(
            commitment_key,
            "selected_discourse_plan",
            selected.discourse_plan,
        ),
        "selected_surface_ast_commitment": _commit_json(
            commitment_key, "selected_surface_ast", selected.surface_ast
        ),
        "selected_candidate_body_commitment": hmac_commit_bytes(
            commitment_key, "selected_candidate_body", selected_body
        ),
        "parsed_witness_binding_commitment": _commit_json(
            commitment_key, "parsed_witness_binding", witness_binding
        ),
        "v1_baseline_body_commitment": hmac_commit_bytes(
            commitment_key,
            "v1_baseline_body",
            v1_body.encode("utf-8", errors="strict"),
        ),
        "runtime_summary_commitment": _commit_json(
            commitment_key, "runtime_summary", runtime_summary
        ),
        "selection_attributes_commitment": _commit_json(
            commitment_key, "selection_attributes", selector_attributes
        ),
    }
    receipt = {
        "schema_version": "cocolon.emlis.nls_v3.case_evidence_receipt.step11.v1",
        "candidate_version_id": STEP11_CANDIDATE_VERSION_ID,
        "run_id": run_id,
        "batch_id": "nls3_batch_001",
        "case_id": case_id,
        "sample_source": "karen_generated",
        "case_identity_commitment": commitments["case_identity_commitment"],
        "commitment_policy_sha256": STEP11_COMMITMENT_POLICY_SHA256,
        "app_reachable_validation": {
            "status": "passed",
            "contract_version": "cocolon.input_contract.20260714",
        },
        "source_dependency_closure_sha256": source_dependency_closure_sha256,
        "observation_stage_context_commitment": commitments[
            "observation_stage_context_commitment"
        ],
        "source_observation_plan_commitment": commitments[
            "source_observation_plan_commitment"
        ],
        "obligation_ledger_commitment": commitments[
            "obligation_ledger_commitment"
        ],
        "content_plan_commitment": commitments["content_plan_commitment"],
        "candidate_set_commitment": commitments["candidate_set_commitment"],
        "selected_discourse_plan_commitment": commitments[
            "selected_discourse_plan_commitment"
        ],
        "selected_surface_ast_commitment": commitments[
            "selected_surface_ast_commitment"
        ],
        "selected_candidate_body_commitment": commitments[
            "selected_candidate_body_commitment"
        ],
        "parsed_witness_binding_commitment": commitments[
            "parsed_witness_binding_commitment"
        ],
        "hard_gate": {"status": "passed", "failed_codes": []},
        "selector_decision": {
            "status": "selected",
            "selection_attributes_commitment": commitments[
                "selection_attributes_commitment"
            ],
        },
        "v1_baseline_body_commitment": commitments[
            "v1_baseline_body_commitment"
        ],
        "runtime_summary_commitment": commitments[
            "runtime_summary_commitment"
        ],
        "environment_sha256": environment_sha256,
        "runner_sha256": runner_sha256,
        "body_free": True,
    }
    row = {
        "case_id": case_id,
        "sample_case_commitment": _commit_json(
            commitment_key, "sample_case", sample
        ),
        "case_identity_commitment": commitments["case_identity_commitment"],
        "v1_baseline_body_commitment": commitments[
            "v1_baseline_body_commitment"
        ],
        "status": "selected",
        "failure_code": None,
        "private_failure_code_commitment": None,
        "runtime_summary": runtime_summary,
        "runtime_summary_commitment": commitments[
            "runtime_summary_commitment"
        ],
        "surface_profile": _surface_profile(witness, commitment_key),
        "receipt": receipt,
        "v1_fallback_used": False,
    }
    private_row = {
        "case_id": case_id,
        "sample_case": _json_material(sample),
        "v1_body": v1_body,
        "v3_body": selected_body.decode("utf-8", errors="strict"),
        "runtime_summary": runtime_summary,
        "commitment_material": {
            "projected_input": _json_material(projected_input),
            "observation_stage_context": _json_material(
                execution.observation_stage_context
            ),
            "source_observation_plan": _json_material(execution.grounded_plan),
            "obligation_ledger": _json_material(execution.inventory_result.ledger),
            "content_plan": _json_material(execution.content_plan),
            "candidate_set": candidate_set,
            "selected_discourse_plan": _json_material(selected.discourse_plan),
            "selected_surface_ast": _json_material(selected.surface_ast),
            "parsed_witness_binding": _json_material(witness_binding),
            "selector_attributes": selector_attributes,
        },
        "receipt": receipt,
    }
    return row, private_row


def _build_no_valid_case(
    sample: Mapping[str, Any],
    *,
    v1_body: str,
    execution: Any,
    commitment_key: bytes,
    run_id: str,
    source_dependency_closure_sha256: str,
    environment_sha256: str,
    runner_sha256: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build a completed fail-closed row without relabelling it an exception."""

    case_id = sample.get("case_id")
    if type(case_id) is not str or _CASE_RE.fullmatch(case_id) is None:
        raise ValueError("step11_case_id_invalid")
    issues = validate_step11_runtime_execution(execution)
    if issues:
        raise Step11RuntimeAdapterError(issues[0])
    if (
        execution.status != "v3_no_valid_candidate"
        or execution.selected_candidate is not None
        or execution.final_utf8_bytes is not None
        or any(row.hard_pass is True for row in execution.selection_result.gate_results)
    ):
        raise Step11RuntimeAdapterError("STEP11_RUNTIME_NO_VALID_SELECTION_INVALID")

    projected_input = project_app_reachable_input(sample["input"])
    runtime_summary = runtime_execution_body_free_summary(execution)
    candidate_set = _candidate_set_material(execution, commitment_key)
    failed_codes = sorted(
        {
            code
            for gate in execution.selection_result.gate_results
            for code in gate.failure_codes
        }
    )
    if not failed_codes:
        raise Step11RuntimeAdapterError("STEP11_RUNTIME_NO_VALID_FAILURE_CODE_MISSING")
    selector_attributes = {
        "selected_candidate_id": None,
        "evaluated_candidate_ids": list(
            execution.selection_result.evaluated_candidate_ids
        ),
        "gate_results": [
            {
                "candidate_id": gate.candidate_id,
                "failure_codes": list(gate.failure_codes),
                "hard_pass": gate.hard_pass,
                "selector_attributes": list(gate.selector_attributes),
            }
            for gate in execution.selection_result.gate_results
        ],
    }
    commitments = {
        "case_identity_commitment": _commit_json(
            commitment_key, "case_identity", projected_input
        ),
        "observation_stage_context_commitment": _commit_json(
            commitment_key,
            "observation_stage_context",
            execution.observation_stage_context,
        ),
        "source_observation_plan_commitment": _commit_json(
            commitment_key, "source_observation_plan", execution.grounded_plan
        ),
        "obligation_ledger_commitment": _commit_json(
            commitment_key, "obligation_ledger", execution.inventory_result.ledger
        ),
        "content_plan_commitment": _commit_json(
            commitment_key, "content_plan", execution.content_plan
        ),
        "candidate_set_commitment": _commit_json(
            commitment_key, "candidate_set", candidate_set
        ),
        "v1_baseline_body_commitment": hmac_commit_bytes(
            commitment_key,
            "v1_baseline_body",
            v1_body.encode("utf-8", errors="strict"),
        ),
        "runtime_summary_commitment": _commit_json(
            commitment_key, "runtime_summary", runtime_summary
        ),
        "selection_attributes_commitment": _commit_json(
            commitment_key, "selection_attributes", selector_attributes
        ),
    }
    receipt = {
        "schema_version": "cocolon.emlis.nls_v3.case_evidence_receipt.step11.v1",
        "candidate_version_id": STEP11_CANDIDATE_VERSION_ID,
        "run_id": run_id,
        "batch_id": "nls3_batch_001",
        "case_id": case_id,
        "sample_source": "karen_generated",
        "case_identity_commitment": commitments["case_identity_commitment"],
        "commitment_policy_sha256": STEP11_COMMITMENT_POLICY_SHA256,
        "app_reachable_validation": {
            "status": "passed",
            "contract_version": "cocolon.input_contract.20260714",
        },
        "source_dependency_closure_sha256": source_dependency_closure_sha256,
        "observation_stage_context_commitment": commitments[
            "observation_stage_context_commitment"
        ],
        "source_observation_plan_commitment": commitments[
            "source_observation_plan_commitment"
        ],
        "obligation_ledger_commitment": commitments[
            "obligation_ledger_commitment"
        ],
        "content_plan_commitment": commitments["content_plan_commitment"],
        "candidate_set_commitment": commitments["candidate_set_commitment"],
        "selected_discourse_plan_commitment": None,
        "selected_surface_ast_commitment": None,
        "selected_candidate_body_commitment": None,
        "parsed_witness_binding_commitment": None,
        "hard_gate": {"status": "failed", "failed_codes": failed_codes},
        "selector_decision": {
            "status": "no_valid_candidate",
            "selection_attributes_commitment": commitments[
                "selection_attributes_commitment"
            ],
        },
        "v1_baseline_body_commitment": commitments[
            "v1_baseline_body_commitment"
        ],
        "runtime_summary_commitment": commitments[
            "runtime_summary_commitment"
        ],
        "environment_sha256": environment_sha256,
        "runner_sha256": runner_sha256,
        "body_free": True,
    }
    row = {
        "case_id": case_id,
        "sample_case_commitment": _commit_json(
            commitment_key, "sample_case", sample
        ),
        "case_identity_commitment": commitments["case_identity_commitment"],
        "v1_baseline_body_commitment": commitments[
            "v1_baseline_body_commitment"
        ],
        "status": "v3_no_valid_candidate",
        "failure_code": None,
        "private_failure_code_commitment": None,
        "runtime_summary": runtime_summary,
        "runtime_summary_commitment": commitments[
            "runtime_summary_commitment"
        ],
        "surface_profile": None,
        "receipt": receipt,
        "v1_fallback_used": False,
    }
    private_row = {
        "case_id": case_id,
        "sample_case": _json_material(sample),
        "v1_body": v1_body,
        "v3_body": None,
        "runtime_summary": runtime_summary,
        "commitment_material": {
            "projected_input": _json_material(projected_input),
            "observation_stage_context": _json_material(
                execution.observation_stage_context
            ),
            "source_observation_plan": _json_material(execution.grounded_plan),
            "obligation_ledger": _json_material(execution.inventory_result.ledger),
            "content_plan": _json_material(execution.content_plan),
            "candidate_set": candidate_set,
            "selected_discourse_plan": None,
            "selected_surface_ast": None,
            "parsed_witness_binding": None,
            "selector_attributes": selector_attributes,
        },
        "receipt": receipt,
    }
    return row, private_row


def _build_exception_case(
    sample: Mapping[str, Any],
    *,
    v1_body: str,
    case_identity_commitment: str,
    v1_baseline_body_commitment: str,
    commitment_key: bytes,
    public_failure_code: str,
    private_failure_code: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    case_id = sample.get("case_id")
    return (
        {
            "case_id": case_id,
            "sample_case_commitment": _commit_json(
                commitment_key, "sample_case", sample
            ),
            "case_identity_commitment": case_identity_commitment,
            "v1_baseline_body_commitment": v1_baseline_body_commitment,
            "status": "exception",
            "failure_code": public_failure_code,
            "private_failure_code_commitment": hmac_commit_bytes(
                commitment_key,
                "private_failure_code",
                private_failure_code.encode("utf-8", errors="strict"),
            ),
            "runtime_summary": None,
            "runtime_summary_commitment": None,
            "surface_profile": None,
            "receipt": None,
            "v1_fallback_used": False,
        },
        {
            "case_id": case_id,
            "sample_case": _json_material(sample),
            "v1_body": v1_body,
            "v3_body": None,
            "failure_code": private_failure_code,
        },
    )


def run_step11_batch(
    samples: Sequence[Mapping[str, Any]],
    manifest: Mapping[str, Any],
    *,
    initial_private_packet: Mapping[str, Any],
    initial_summary: Mapping[str, Any],
    before_dependency_manifest: Mapping[str, Any],
    dependency_manifest: Mapping[str, Any],
    commitment_key: bytes,
    run_id: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    if validate_step11_dependency_manifest(dependency_manifest):
        raise ValueError("step11_dependency_manifest_invalid")
    source_closure = assert_current_step11_dependency_manifest(
        dependency_manifest,
        before_manifest=before_dependency_manifest,
    )
    if dependency_manifest.get("candidate_version_id") != STEP11_CANDIDATE_VERSION_ID:
        raise ValueError("step11_dependency_candidate_mismatch")
    if len(samples) != 100 or manifest.get("case_count") != 100:
        raise ValueError("step11_exact_100_required")
    private_by_case = _initial_private_by_case(initial_private_packet)
    initial_by_case = _initial_summary_by_case(initial_summary)
    initial_issues = verify_batch_evidence(
        initial_private_packet, initial_summary
    )
    if initial_issues:
        raise ValueError(f"step11_initial_evidence_invalid:{initial_issues[0]}")
    if initial_summary.get("commitment_key_id") != commitment_key_id(commitment_key):
        raise ValueError("step11_commitment_key_continuity_invalid")

    environment_sha256 = _environment_sha256()
    runner_sha256 = _runner_sha256()
    declared_runner_sha256 = next(
        (
            row["sha256"]
            for row in dependency_manifest["file_hashes"]
            if row["path"] == "ai/tools/emlis_nls_v3_step11_batch_run.py"
        ),
        None,
    )
    if runner_sha256 != declared_runner_sha256:
        raise ValueError("step11_runner_dependency_hash_mismatch")
    rows: list[dict[str, Any]] = []
    private_rows: list[dict[str, Any]] = []
    for sample in samples:
        case_id = sample.get("case_id")
        if type(case_id) is not str or case_id not in private_by_case:
            raise ValueError("step11_sample_case_set_mismatch")
        historical = private_by_case[case_id]
        initial_row = initial_by_case[case_id]
        if historical.get("sample_case") != sample:
            raise ValueError("step11_frozen_sample_changed_after_initial_run")
        v1_body = historical.get("v1_body")
        if type(v1_body) is not str:
            raise ValueError("step11_initial_v1_body_missing")
        projected_input = project_app_reachable_input(sample["input"])
        case_identity = _commit_json(commitment_key, "case_identity", projected_input)
        v1_commitment = hmac_commit_bytes(
            commitment_key,
            "v1_baseline_body",
            v1_body.encode("utf-8", errors="strict"),
        )
        if (
            case_identity != initial_row.get("case_identity_commitment")
            or v1_commitment
            != initial_row.get("receipt", {}).get("v1_baseline_body_commitment")
        ):
            raise ValueError("step11_initial_commitment_continuity_invalid")
        try:
            execution = execute_step11_offline_v3(
                # Only the app-reachable four-field projection may enter the
                # production-equivalent runtime.  The frozen sample wrapper's
                # semantic_contract remains an evaluation oracle and is never
                # available to content selection, rendering, or matching.
                projected_input,
                candidate_version_id=STEP11_CANDIDATE_VERSION_ID,
                source_dependency_closure_sha256=source_closure,
            )
        except Step11RuntimeAdapterError as exc:
            row, private_row = _build_exception_case(
                sample,
                v1_body=v1_body,
                case_identity_commitment=case_identity,
                v1_baseline_body_commitment=v1_commitment,
                commitment_key=commitment_key,
                public_failure_code="STEP11_CASE_EXECUTION_REJECTED",
                private_failure_code=exc.code,
            )
        else:
            builder = (
                _build_selected_case
                if execution.status == "selected"
                else _build_no_valid_case
                if execution.status == "v3_no_valid_candidate"
                else None
            )
            if builder is None:
                evidence_issue = "STEP11_RUNTIME_SELECTOR_STATUS_INVALID"
            else:
                try:
                    row, private_row = builder(
                        sample,
                        v1_body=v1_body,
                        execution=execution,
                        commitment_key=commitment_key,
                        run_id=run_id,
                        source_dependency_closure_sha256=source_closure,
                        environment_sha256=environment_sha256,
                        runner_sha256=runner_sha256,
                    )
                    evidence_issue = None
                except (
                    KeyError,
                    Step11RuntimeAdapterError,
                    TypeError,
                    UnicodeError,
                    ValueError,
                ):
                    evidence_issue = "STEP11_EVIDENCE_BUILD_REJECTED"
            if evidence_issue is not None:
                row, private_row = _build_exception_case(
                    sample,
                    v1_body=v1_body,
                    case_identity_commitment=case_identity,
                    v1_baseline_body_commitment=v1_commitment,
                    commitment_key=commitment_key,
                    public_failure_code="STEP11_EVIDENCE_BUILD_REJECTED",
                    private_failure_code=evidence_issue,
                )
        rows.append(row)
        private_rows.append(private_row)

    if (
        assert_current_step11_dependency_manifest(
            dependency_manifest,
            before_manifest=before_dependency_manifest,
        )
        != source_closure
    ):
        raise ValueError("step11_source_dependency_changed_during_run")

    summary = build_step11_batch_run_summary(
        rows,
        dependency_manifest=dependency_manifest,
        run_id=run_id,
        commitment_key_id=commitment_key_id(commitment_key),
        environment_sha256=environment_sha256,
        runner_sha256=runner_sha256,
        runtime_validation_protocol_sha256=(
            STEP11_RUNTIME_VALIDATION_PROTOCOL_SHA256
        ),
        local_review_rubric_sha256=STEP11_REVIEW_RUBRIC_SHA256,
    )
    private_packet = {
        "schema_version": STEP11_PRIVATE_PACKET_SCHEMA,
        "storage_scope": "private_local_only_outside_repo",
        "body_full": True,
        "candidate_version_id": STEP11_CANDIDATE_VERSION_ID,
        "run_id": run_id,
        "source_dependency_closure_sha256": source_closure,
        "commitment_key_id": commitment_key_id(commitment_key),
        "hmac_key_hex": commitment_key.hex(),
        "body_free_summary_sha256": artifact_sha256(summary),
        "cases": private_rows,
    }
    private_issues = validate_step11_private_packet(
        private_packet,
        summary,
        initial_private_packet=initial_private_packet,
        dependency_manifest=dependency_manifest,
        commitment_key=commitment_key,
    )
    if private_issues:
        raise ValueError(f"step11_private_packet_invalid:{private_issues[0]}")
    verification_receipt = build_step11_private_verification_receipt(
        summary,
        final_dependency_manifest=dependency_manifest,
        private_packet_commitment=_commit_json(
            commitment_key, "step11_private_packet", private_packet
        ),
        initial_private_packet_commitment=_commit_json(
            commitment_key,
            "step11_initial_private_packet",
            initial_private_packet,
        ),
        initial_batch_summary_sha256=artifact_sha256(initial_summary),
        verifier_sha256=runner_sha256,
        verified_case_count=len(private_rows),
        initial_verified_case_count=len(initial_private_packet["cases"]),
    )
    return private_packet, summary, verification_receipt


def validate_step11_private_packet(
    private_packet: Any,
    summary: Any,
    *,
    initial_private_packet: Mapping[str, Any],
    dependency_manifest: Mapping[str, Any],
    commitment_key: bytes,
) -> tuple[str, ...]:
    """Recompute every private HMAC and its body-free row binding."""

    issues: set[str] = set()
    if (
        type(private_packet) is not dict
        or type(summary) is not dict
        or type(initial_private_packet) is not dict
    ):
        return ("STEP11_PRIVATE_PACKET_MAPPING_REQUIRED",)
    if set(private_packet) != {
        "schema_version",
        "storage_scope",
        "body_full",
        "candidate_version_id",
        "run_id",
        "source_dependency_closure_sha256",
        "commitment_key_id",
        "hmac_key_hex",
        "body_free_summary_sha256",
        "cases",
    }:
        issues.add("STEP11_PRIVATE_PACKET_KEYSET_INVALID")
    if validate_step11_batch_run_summary(
        summary, dependency_manifest=dependency_manifest
    ):
        issues.add("STEP11_PRIVATE_PACKET_SUMMARY_INVALID")
    if (
        private_packet.get("schema_version") != STEP11_PRIVATE_PACKET_SCHEMA
        or private_packet.get("storage_scope")
        != "private_local_only_outside_repo"
        or private_packet.get("body_full") is not True
        or private_packet.get("candidate_version_id")
        != summary.get("candidate_version_id")
        or private_packet.get("run_id") != summary.get("run_id")
        or private_packet.get("source_dependency_closure_sha256")
        != summary.get("source_dependency_closure_sha256")
        or private_packet.get("commitment_key_id")
        != commitment_key_id(commitment_key)
        or private_packet.get("hmac_key_hex") != commitment_key.hex()
        or private_packet.get("body_free_summary_sha256")
        != artifact_sha256(summary)
        or initial_private_packet.get("commitment_key_id")
        != commitment_key_id(commitment_key)
        or initial_private_packet.get("hmac_key_hex") != commitment_key.hex()
    ):
        issues.add("STEP11_PRIVATE_PACKET_PARENT_INVALID")
    private_rows = private_packet.get("cases")
    public_rows = summary.get("case_rows")
    initial_rows = initial_private_packet.get("cases")
    if (
        type(private_rows) is not list
        or type(public_rows) is not list
        or len(private_rows) != 100
        or len(public_rows) != 100
        or type(initial_rows) is not list
        or len(initial_rows) != 100
    ):
        issues.add("STEP11_PRIVATE_PACKET_EXACT_100_REQUIRED")
        return tuple(sorted(issues))
    private_by_case = {
        row.get("case_id"): row for row in private_rows if type(row) is dict
    }
    initial_by_case = {
        row.get("case_id"): row for row in initial_rows if type(row) is dict
    }
    if len(private_by_case) != 100 or len(initial_by_case) != 100:
        issues.add("STEP11_PRIVATE_PACKET_CASE_SET_INVALID")
        return tuple(sorted(issues))
    for public in public_rows:
        case_id = public.get("case_id") if type(public) is dict else None
        private = private_by_case.get(case_id)
        initial = initial_by_case.get(case_id)
        if type(private) is not dict:
            issues.add("STEP11_PRIVATE_PACKET_CASE_SET_INVALID")
            continue
        status = public.get("status")
        sample = private.get("sample_case")
        v1_body = private.get("v1_body")
        try:
            if (
                type(sample) is not dict
                or sample.get("case_id") != case_id
                or type(sample.get("input")) is not dict
                or type(v1_body) is not str
                or type(initial) is not dict
                or initial.get("sample_case") != sample
                or initial.get("v1_body") != v1_body
            ):
                raise ValueError("private sample invalid")
            projected_from_sample = _json_material(
                project_app_reachable_input(sample["input"])
            )
            case_identity_commitment = _commit_json(
                commitment_key, "case_identity", projected_from_sample
            )
            v1_commitment = hmac_commit_bytes(
                commitment_key,
                "v1_baseline_body",
                v1_body.encode("utf-8", errors="strict"),
            )
        except (KeyError, TypeError, UnicodeError, ValueError):
            issues.add("STEP11_PRIVATE_PACKET_SAMPLE_BINDING_INVALID")
            continue
        if (
            public.get("sample_case_commitment")
            != _commit_json(commitment_key, "sample_case", sample)
            or
            public.get("case_identity_commitment") != case_identity_commitment
            or public.get("v1_baseline_body_commitment") != v1_commitment
        ):
            issues.add("STEP11_PRIVATE_PACKET_SAMPLE_BINDING_MISMATCH")

        if status == "exception":
            expected_failure_commitment = (
                hmac_commit_bytes(
                    commitment_key,
                    "private_failure_code",
                    private["failure_code"].encode("utf-8", errors="strict"),
                )
                if type(private.get("failure_code")) is str
                else None
            )
            if (
                private.get("v3_body") is not None
                or type(private.get("failure_code")) is not str
                or public.get("receipt") is not None
                or public.get("private_failure_code_commitment")
                != expected_failure_commitment
                or (
                    public.get("failure_code")
                    == "STEP11_EVIDENCE_BUILD_REJECTED"
                    and private.get("failure_code")
                    != "STEP11_EVIDENCE_BUILD_REJECTED"
                )
            ):
                issues.add("STEP11_PRIVATE_PACKET_EXCEPTION_INVALID")
            continue
        if status not in {"selected", "v3_no_valid_candidate"}:
            issues.add("STEP11_PRIVATE_PACKET_STATUS_INVALID")
            continue
        if public.get("private_failure_code_commitment") is not None:
            issues.add("STEP11_PRIVATE_PACKET_FAILURE_COMMITMENT_FORBIDDEN")

        material = private.get("commitment_material")
        receipt = private.get("receipt")
        if type(material) is not dict or type(receipt) is not dict:
            issues.add("STEP11_PRIVATE_PACKET_MATERIAL_INVALID")
            continue
        if material.get("projected_input") != projected_from_sample:
            issues.add("STEP11_PRIVATE_PACKET_PROJECTED_INPUT_MISMATCH")
        witness_binding = material.get("parsed_witness_binding")
        witness = (
            witness_binding.get("witness")
            if type(witness_binding) is dict
            else None
        )
        try:
            recomputed = {
                "case_identity_commitment": case_identity_commitment,
                "observation_stage_context_commitment": _commit_json(
                    commitment_key,
                    "observation_stage_context",
                    material["observation_stage_context"],
                ),
                "source_observation_plan_commitment": _commit_json(
                    commitment_key,
                    "source_observation_plan",
                    material["source_observation_plan"],
                ),
                "obligation_ledger_commitment": _commit_json(
                    commitment_key,
                    "obligation_ledger",
                    material["obligation_ledger"],
                ),
                "content_plan_commitment": _commit_json(
                    commitment_key, "content_plan", material["content_plan"]
                ),
                "candidate_set_commitment": _commit_json(
                    commitment_key, "candidate_set", material["candidate_set"]
                ),
                "v1_baseline_body_commitment": v1_commitment,
                "runtime_summary_commitment": _commit_json(
                    commitment_key,
                    "runtime_summary",
                    private["runtime_summary"],
                ),
                "selection_attributes_commitment": _commit_json(
                    commitment_key,
                    "selection_attributes",
                    material["selector_attributes"],
                ),
            }
            if status == "selected":
                if type(private.get("v3_body")) is not str:
                    raise ValueError("selected body missing")
                recomputed.update(
                    {
                        "selected_discourse_plan_commitment": _commit_json(
                            commitment_key,
                            "selected_discourse_plan",
                            material["selected_discourse_plan"],
                        ),
                        "selected_surface_ast_commitment": _commit_json(
                            commitment_key,
                            "selected_surface_ast",
                            material["selected_surface_ast"],
                        ),
                        "selected_candidate_body_commitment": hmac_commit_bytes(
                            commitment_key,
                            "selected_candidate_body",
                            private["v3_body"].encode("utf-8", errors="strict"),
                        ),
                        "parsed_witness_binding_commitment": _commit_json(
                            commitment_key,
                            "parsed_witness_binding",
                            witness_binding,
                        ),
                    }
                )
                profile = _surface_profile_from_private_witness(
                    witness, commitment_key
                )
            else:
                if (
                    private.get("v3_body") is not None
                    or witness_binding is not None
                    or material.get("selected_discourse_plan") is not None
                    or material.get("selected_surface_ast") is not None
                ):
                    raise ValueError("no-valid selected material present")
                recomputed.update(
                    {
                        "selected_discourse_plan_commitment": None,
                        "selected_surface_ast_commitment": None,
                        "selected_candidate_body_commitment": None,
                        "parsed_witness_binding_commitment": None,
                    }
                )
                profile = None
        except (KeyError, TypeError, UnicodeError, ValueError):
            issues.add("STEP11_PRIVATE_PACKET_RECOMPUTATION_FAILED")
            continue
        receipt_fields = {
            key: receipt.get(key)
            for key in recomputed
            if key != "selection_attributes_commitment"
        }
        receipt_fields["selection_attributes_commitment"] = receipt.get(
            "selector_decision", {}
        ).get("selection_attributes_commitment")
        if recomputed != receipt_fields:
            issues.add("STEP11_PRIVATE_PACKET_HMAC_MISMATCH")
        if public.get("receipt") != receipt:
            issues.add("STEP11_PRIVATE_PACKET_RECEIPT_BINDING_MISMATCH")
        if public.get("runtime_summary") != private.get("runtime_summary"):
            issues.add("STEP11_PRIVATE_PACKET_RUNTIME_SUMMARY_MISMATCH")
        if public.get("surface_profile") != profile:
            issues.add("STEP11_PRIVATE_PACKET_SURFACE_PROFILE_MISMATCH")
    return tuple(sorted(issues))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run frozen Cycle 001 through the offline rc0023 adapter with "
            "the exact frozen rc0022 failed-run manifest as predecessor."
        )
    )
    parser.add_argument("--batch", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--initial-private", type=Path, required=True)
    parser.add_argument("--initial-summary", type=Path, required=True)
    parser.add_argument("--before-dependency-manifest", type=Path, required=True)
    parser.add_argument("--dependency-manifest", type=Path, required=True)
    parser.add_argument("--commitment-key-file", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--private-output", type=Path, required=True)
    parser.add_argument("--body-free-output", type=Path, required=True)
    parser.add_argument("--private-verification-output", type=Path, required=True)
    args = parser.parse_args(argv)

    outputs = (
        args.private_output,
        args.body_free_output,
        args.private_verification_output,
    )
    if any(path.exists() for path in outputs):
        raise ValueError("step11_output_already_exists")
    repo = REPO_ROOT.resolve()
    private = args.private_output.absolute()
    private_resolved = args.private_output.resolve()
    if (
        private == repo
        or repo in private.parents
        or private_resolved == repo
        or repo in private_resolved.parents
    ):
        raise ValueError("step11_private_packet_must_be_outside_repo")
    inputs = (
        args.batch,
        args.manifest,
        args.initial_private,
        args.initial_summary,
        args.before_dependency_manifest,
        args.dependency_manifest,
        args.commitment_key_file,
    )
    resolved = [path.resolve() for path in (*inputs, *outputs)]
    if len(resolved) != len(set(resolved)):
        raise ValueError("step11_cli_path_collision")

    samples, manifest = load_validated_batch(
        args.batch.resolve(), args.manifest.resolve()
    )
    dependency_manifest = load_canonical_json(args.dependency_manifest)
    before_dependency_manifest = load_canonical_json(
        args.before_dependency_manifest
    )
    commitment_key = _read_key(args.commitment_key_file)
    private_packet, summary, verification_receipt = run_step11_batch(
        samples,
        manifest,
        initial_private_packet=load_canonical_json(args.initial_private),
        initial_summary=load_canonical_json(args.initial_summary),
        before_dependency_manifest=before_dependency_manifest,
        dependency_manifest=dependency_manifest,
        commitment_key=commitment_key,
        run_id=args.run_id,
    )
    created: list[Path] = []
    try:
        _write_json(args.private_output, private_packet, private=True)
        created.append(args.private_output)
        _write_json(args.body_free_output, summary, private=False)
        created.append(args.body_free_output)
        _write_json(
            args.private_verification_output,
            verification_receipt,
            private=False,
        )
        created.append(args.private_verification_output)
    except BaseException:
        for path in reversed(created):
            try:
                _secure_unlink(path)
            except OSError:
                pass
        raise
    return 0 if summary["machine_status"] == "clean" else 2


if __name__ == "__main__":
    raise SystemExit(main())
