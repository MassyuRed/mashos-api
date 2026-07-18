# -*- coding: utf-8 -*-
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace

import emlis_ai_step11_hard_gate_v3 as gate_module
from emlis_ai_step11_natural_surface_matcher_v3 import (
    STEP11_PARSED_WITNESS_SCHEMA,
    STEP11_VERIFIED_BINDING_SCHEMA,
    Step11BindingRow,
    Step11ParsedAtom,
    Step11ParsedSurfaceWitness,
    Step11VerifiedSurfaceBinding,
)
from emlis_ai_step11_surface_catalog_v3 import STEP11_SURFACE_CATALOG


_FOCUSED_BUDGET = {
    "observation_sentence_min": 1,
    "observation_sentence_max": 2,
    "reception_sentence_min": 1,
    "reception_sentence_max": 2,
    "total_sentence_max": 4,
}


def _atom(atom_id: str, section_role: str) -> Step11ParsedAtom:
    return Step11ParsedAtom(
        atom_id=atom_id,
        section_role=section_role,
        form_id=(
            "thought:notice:bounded"
            if section_role == "observation"
            else "reception:anaphoric:acknowledge:thought"
        ),
        claim_kinds=(
            ("nucleus_notice",)
            if section_role == "observation"
            else ("bound_reception",)
        ),
        source_slot_hints=(),
        source_fragments=(),
        predicate_role=(
            "thought" if section_role == "observation" else "thought"
        ),
        realization_status=(
            "reported_content"
            if section_role == "observation"
            else "status_neutral"
        ),
        relation_type=None,
        relation_direction=None,
        relation_endpoint_roles=(),
        unknown_dimension_class=None,
        self_denial_not_fact=False,
        reception_act=(
            None if section_role == "observation" else "acknowledge"
        ),
        reception_scope=(
            None if section_role == "observation" else "thought"
        ),
        byte_start=0,
        byte_end=1,
    )


def _contract_material():
    required_ids = ["obl_obs_a", "obl_obs_b", "obl_rec"]
    content_plan = {
        "depth": "focused",
        "section_budget": dict(_FOCUSED_BUDGET),
        "decisions": [
            {"obligation_id": item, "status": "selected"}
            for item in required_ids
        ],
        "required_coverage_obligation_ids": list(required_ids),
    }
    discourse_plan = {
        "nodes": [
            {"node_id": "node_obs_a", "section_role": "observation"},
            {"node_id": "node_obs_b", "section_role": "observation"},
            {"node_id": "node_rec", "section_role": "reception"},
        ],
        "sentence_groups": [
            {
                "sentence_group_id": "group_obs",
                "section_role": "observation",
                "node_ids": ["node_obs_a", "node_obs_b"],
            },
            {
                "sentence_group_id": "group_rec",
                "section_role": "reception",
                "node_ids": ["node_rec"],
            },
        ],
    }
    atoms = (_atom("atom_obs", "observation"), _atom("atom_rec", "reception"))
    witness = Step11ParsedSurfaceWitness(
        schema_version=STEP11_PARSED_WITNESS_SCHEMA,
        surface_catalog_sha256="a" * 64,
        body_sha256="b" * 64,
        atoms=atoms,
        observation_atom_count=1,
        reception_atom_count=1,
        body_free_export_allowed=False,
    )
    binding = Step11VerifiedSurfaceBinding(
        schema_version=STEP11_VERIFIED_BINDING_SCHEMA,
        parsed_witness_sha256="c" * 64,
        obligation_ledger_sha256="d" * 64,
        content_plan_sha256="e" * 64,
        discourse_plan_sha256="f" * 64,
        binding_rows=(
            Step11BindingRow(
                "obl_obs_a", "grounded_nucleus_notice", ("atom_obs",), "exact"
            ),
            Step11BindingRow(
                "obl_obs_b", "grounded_relation_preservation", ("atom_obs",), "integrated"
            ),
            Step11BindingRow(
                "obl_rec", "emlis_stance", ("atom_rec",), "bound"
            ),
        ),
        required_obligation_ids=tuple(required_ids),
        integrated_relation_ids=(),
        integrated_unknown_ids=(),
        source_unknown_oracle_sha256="1" * 64,
        integrated_mixed_emotion_requirement_ids=(),
        integrated_reception_binding_ids=(),
        source_fragment_count=0,
        issue_codes=(),
        verified=True,
    )
    labels = STEP11_SURFACE_CATALOG["labels"]
    body = (
        f"{labels['observation']}\n観察文。\n\n"
        f"{labels['reception']}\n受け止め文。"
    ).encode("utf-8")
    overlay = SimpleNamespace(mixed_emotion_requirements=())
    inventory = SimpleNamespace(ledger={})
    return (
        inventory,
        content_plan,
        discourse_plan,
        body,
        witness,
        binding,
        overlay,
    )


def _evaluate(monkeypatch, **changes) -> bool:
    (
        inventory,
        content_plan,
        discourse_plan,
        body,
        witness,
        binding,
        overlay,
    ) = _contract_material()
    monkeypatch.setattr(
        gate_module, "validate_content_selection_policy", lambda *args, **kwargs: ()
    )
    monkeypatch.setattr(
        gate_module, "validate_discourse_plan", lambda *args, **kwargs: ()
    )
    monkeypatch.setattr(
        gate_module, "derive_content_depth", lambda *args, **kwargs: "focused"
    )
    material = {
        "inventory_result": inventory,
        "content_plan": content_plan,
        "discourse_plan": discourse_plan,
        "body": body,
        "witness": witness,
        "binding": binding,
        "semantic_overlay": overlay,
        "binding_issues": set(),
    }
    material.update(changes)
    return gate_module._depth_contract_green(**material)


def test_gate17_accepts_one_atom_bound_to_multiple_integrated_obligations(
    monkeypatch,
) -> None:
    assert _evaluate(monkeypatch) is True


def test_gate17_fails_closed_when_binding_is_unverified(monkeypatch) -> None:
    *_, binding, _overlay = _contract_material()
    assert _evaluate(monkeypatch, binding=replace(binding, verified=False)) is False


def test_gate17_rejects_content_budget_tampering(monkeypatch) -> None:
    _inventory, content_plan, *_rest = _contract_material()
    mutation = deepcopy(content_plan)
    mutation["section_budget"]["observation_sentence_max"] = 99
    assert _evaluate(monkeypatch, content_plan=mutation) is False


def test_gate17_rejects_final_sentence_group_count_mismatch(monkeypatch) -> None:
    inventory, content_plan, discourse_plan, body, *_rest = _contract_material()
    del inventory, content_plan, discourse_plan
    labels = STEP11_SURFACE_CATALOG["labels"]
    mutation = (
        f"{labels['observation']}\n観察文一。\n観察文二。\n\n"
        f"{labels['reception']}\n受け止め文。"
    ).encode("utf-8")
    assert mutation != body
    assert _evaluate(monkeypatch, body=mutation) is False


def test_gate17_rejects_reported_parsed_count_tampering(monkeypatch) -> None:
    *_prefix, witness, _binding, _overlay = _contract_material()
    mutation = replace(witness, observation_atom_count=2)
    assert _evaluate(monkeypatch, witness=mutation) is False
