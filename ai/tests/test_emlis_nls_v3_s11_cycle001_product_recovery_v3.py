# -*- coding: utf-8 -*-
from __future__ import annotations

"""Cycle001 distinct, source-bound Product recovery contract."""

import ast
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
import json
from pathlib import Path
from typing import Any

import pytest


_REPO_ROOT = Path(__file__).resolve().parents[2]
_SERVICE_ROOT = _REPO_ROOT / "ai" / "services" / "ai_inference"
_SURFACE_PATH = _SERVICE_ROOT / "emlis_ai_step11_natural_surface_v3.py"
_RECOVERY_PATH = (
    _SERVICE_ROOT / "emlis_ai_step11_cycle001_product_recovery_v3.py"
)
_TOOLS_ROOT = _REPO_ROOT / "ai" / "tools"
_EXACT100 = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "emlis_nls_v3"
    / "generated"
    / "batch_001.jsonl"
)


def _install_paths() -> None:
    import sys

    for path in (_SERVICE_ROOT, _TOOLS_ROOT):
        value = str(path)
        if value not in sys.path:
            sys.path.insert(0, value)


def _samples() -> tuple[dict[str, Any], ...]:
    rows = tuple(
        json.loads(line)
        for line in _EXACT100.read_text(encoding="utf-8").splitlines()
        if line
    )
    assert len(rows) == 100
    assert tuple(row["case_id"] for row in rows) == tuple(
        f"nls3s_b001_{ordinal:04d}" for ordinal in range(1, 101)
    )
    return rows


def _context_and_kwargs(sample: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
    _install_paths()
    from emlis_nls_v3_step11_current_rc_g8_run import (
        _build_direct_recovery_context,
    )

    context = _build_direct_recovery_context(sample["input"])
    return context, {
        "plan": context.grounded_plan,
        "resolver": context.resolver,
        "successor_snapshot": context.successor_snapshot,
        "lexical_atom_specs": context.lexical_atom_specs,
        "inventory_result": context.inventory_result,
        "content_plan": context.content_plan,
        "discourse_plans": context.discourse_plans,
        "current_input": context.projected_current_input,
    }


def _exercise_exact100_row(sample: dict[str, Any]) -> dict[str, Any]:
    try:
        _context, kwargs = _context_and_kwargs(sample)
        import emlis_ai_step11_cycle001_product_recovery_v3 as recovery

        candidate = recovery.build_step11_cycle001_product_recovery_candidate(
            **kwargs
        )
        replay_issues = (
            recovery.validate_step11_cycle001_product_recovery_candidate(
                candidate, **kwargs
            )
        )
        visible = recovery.step11_cycle001_product_recovery_visible_inverse(
            candidate
        )
        envelope = candidate.source_envelope
        family_counts = {
            family: sum(
                binding.semantic_family == family
                for binding in envelope.atom_bindings
            )
            for family in (
                "construction",
                "relation",
                "semantic_link",
                "explicit_unknown",
            )
        }
        role_dimension_lossless = all(
            len(role.source_owner_ids)
            == len(role.source_owner_dimensions)
            and bool(role.parent_nucleus_id)
            and bool(role.source_span_id)
            and role.slot_end_index > role.slot_start_index >= 0
            for binding in envelope.atom_bindings
            if binding.semantic_family == "construction"
            for role in binding.construction_roles
        )
        return {
            "case_id": sample["case_id"],
            "error_code": None,
            "replay_issues": replay_issues,
            "semantic_coverage_authorized": (
                candidate.semantic_coverage_authorized
            ),
            "owner_count": len(envelope.owner_bindings),
            "root_count": len(envelope.root_bindings),
            "atom_count": len(envelope.atom_bindings),
            "reception_count": len(envelope.reception_bindings),
            "fragment_count": sum(
                len(root.source_fragments)
                for root in envelope.root_bindings
            ),
            "visible_count": len(visible),
            "utf8_byte_count": len(candidate.final_utf8_bytes),
            "family_counts": family_counts,
            "source_counts": dict(envelope.source_counts),
            "role_dimension_lossless": role_dimension_lossless,
            "reception_focus_source_native": all(
                binding.source_focus_owner_ids == ()
                for binding in envelope.reception_bindings
            ),
            "all_roots_input_specific": all(
                root.source_fragments
                and all(
                    fragment.source_fragment_text
                    and fragment.source_fragment_text_sha256
                    for fragment in root.source_fragments
                )
                for root in envelope.root_bindings
            ),
            "visible_owner_referents_injective": len(
                {
                    owner.referent_text_sha256
                    for owner in envelope.owner_bindings
                }
            )
            == len(envelope.owner_bindings),
            "visible_root_lineage_exact": all(
                binding.source_obligation_ids
                and binding.source_fragment_ids
                and binding.source_fragment_text_sha256s
                for binding in visible[: len(envelope.root_bindings)]
            ),
        }
    except Exception as exc:  # pragma: no cover - asserted body-free below
        return {
            "case_id": sample.get("case_id"),
            "error_code": getattr(
                exc, "code", "UNEXPECTED_RECOVERY_EXERCISE_FAILURE"
            ),
        }


def _surface_module():
    import sys

    value = str(_SERVICE_ROOT)
    if value not in sys.path:
        sys.path.insert(0, value)
    return __import__("emlis_ai_step11_natural_surface_v3")


def test_cycle001_recovery_identity_is_distinct_and_legacy_stays_exact() -> None:
    surface = _surface_module()
    assert surface._STEP11_RC0035_CYCLE001_PRODUCT_RECOVERY_CANDIDATE_VERSION_ID == (
        "nls_v3_rc_0035_cycle001_product_recovery"
    )
    assert surface._STEP11_RC0035_CYCLE001_PRODUCT_RECOVERY_CANDIDATE_SCHEMA == (
        "cocolon.emlis.nls_v3.step11."
        "cycle001_product_recovery_candidate.rc0035.v1"
    )
    assert (
        surface._STEP11_RC0035_CYCLE001_PRODUCT_RECOVERY_CANDIDATE_VERSION_ID
        not in {
            surface.STEP11_CANDIDATE_VERSION_ID,
            surface.STEP11_RC0031_EXPERIMENT_CANDIDATE_VERSION_ID,
        }
    )


def test_cycle001_recovery_module_is_pure_request_local_and_oracle_free() -> None:
    tree = ast.parse(_RECOVERY_PATH.read_text(encoding="utf-8"))
    forbidden_names = {
        "execute_step11_offline_v3",
        "select_step11_natural_surface_candidates",
        "evaluate_step11_natural_surface_candidate",
        "validate_step11_natural_surface_candidate",
        "FunctionType",
        "setattr",
        "delattr",
        "globals",
        "__import__",
        "import_module",
        "compile",
        "exec",
        "eval",
    }
    forbidden_tokens = {
        "case_id",
        "batch",
        "fixture",
        "expected_text",
        "review_result",
        "selected_candidate",
        "final_plan_oracle",
    }
    seen_names = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name)
    } | {
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
    }
    seen_imports = {
        alias.name.rsplit(".", 1)[-1]
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    string_values = {
        node.value.casefold()
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    assert forbidden_names.isdisjoint(seen_names | seen_imports)
    assert not any(
        token in value
        for token in forbidden_tokens
        for value in string_values
    )


def test_cycle001_recovery_exports_source_bound_replay_contract() -> None:
    import sys

    value = str(_SERVICE_ROOT)
    if value not in sys.path:
        sys.path.insert(0, value)
    recovery = __import__("emlis_ai_step11_cycle001_product_recovery_v3")
    expected = {
        "STEP11_CYCLE001_PRODUCT_RECOVERY_SOURCE_SCHEMA",
        "Step11Cycle001ProductRecoverySourceEnvelope",
        "Step11Cycle001ProductRecoveryCandidate",
        "build_step11_cycle001_product_recovery_candidate",
        "validate_step11_cycle001_product_recovery_candidate",
    }
    assert expected <= set(recovery.__all__)


@pytest.fixture(scope="module")
def representative0015() -> tuple[Any, Any, dict[str, Any]]:
    sample = _samples()[14]
    _context, kwargs = _context_and_kwargs(sample)
    import emlis_ai_step11_cycle001_product_recovery_v3 as recovery

    candidate = recovery.build_step11_cycle001_product_recovery_candidate(
        **kwargs
    )
    return recovery, candidate, kwargs


def test_cycle001_recovery_replays_and_visible_inverse_is_source_exact(
    representative0015: tuple[Any, Any, dict[str, Any]],
) -> None:
    recovery, candidate, kwargs = representative0015
    assert candidate.semantic_coverage_authorized is True
    assert candidate.base_acceptance_claimed is False
    assert candidate.old_gate_consulted is False
    assert candidate.old_selector_consulted is False
    assert recovery.validate_step11_cycle001_product_recovery_candidate(
        candidate, **kwargs
    ) == ()
    visible = recovery.step11_cycle001_product_recovery_visible_inverse(
        candidate
    )
    envelope = candidate.source_envelope
    assert tuple(row.source_unit_id for row in visible) == (
        *(row.source_root_id for row in envelope.root_bindings),
        *(row.source_atom_id for row in envelope.atom_bindings),
        *(
            row.source_reception_opportunity_id
            for row in envelope.reception_bindings
        ),
    )
    for root, binding in zip(
        envelope.root_bindings,
        visible[: len(envelope.root_bindings)],
        strict=True,
    ):
        assert binding.source_owner_ids == (root.source_owner_id,)
        assert binding.source_obligation_ids == root.source_obligation_ids
        assert binding.source_fragment_ids == tuple(
            row.source_fragment_id for row in root.source_fragments
        )
        assert binding.source_fragment_text_sha256s == tuple(
            row.source_fragment_text_sha256 for row in root.source_fragments
        )


def test_cycle001_recovery_full_discourse_set_is_committed_and_tamper_red(
    representative0015: tuple[Any, Any, dict[str, Any]],
) -> None:
    recovery, candidate, kwargs = representative0015
    from emlis_ai_nls_v3_artifact_contract import artifact_sha256

    discourse = tuple(kwargs["discourse_plans"])
    assert len(discourse) > 1
    assert candidate.source_envelope.source_discourse_plan_sha256 == (
        artifact_sha256(
            {
                "ordered_discourse_plan_sha256s": [
                    artifact_sha256(row) for row in discourse
                ],
                "discourse_plan_count": len(discourse),
            }
        )
    )
    changed = [dict(row) for row in discourse]
    changed[-1]["recovery_nonsemantic_tamper_probe"] = True
    changed_kwargs = {**kwargs, "discourse_plans": tuple(changed)}
    assert "STEP11_CYCLE001_RECOVERY_SOURCE_MISMATCH" in (
        recovery.validate_step11_cycle001_product_recovery_candidate(
            candidate, **changed_kwargs
        )
    )


def test_cycle001_recovery_candidate_and_preimage_tamper_are_causal_red(
    representative0015: tuple[Any, Any, dict[str, Any]],
) -> None:
    recovery, candidate, kwargs = representative0015
    authorization_tamper = replace(
        candidate, semantic_coverage_authorized=False
    )
    authorization_issues = (
        recovery.validate_step11_cycle001_product_recovery_candidate(
            authorization_tamper, **kwargs
        )
    )
    assert "STEP11_CYCLE001_RECOVERY_BOUNDARY_INVALID" in authorization_issues
    assert "STEP11_CYCLE001_RECOVERY_PLAN_IDENTITY_INVALID" in (
        authorization_issues
    )
    assert "STEP11_CYCLE001_RECOVERY_AST_IDENTITY_INVALID" in (
        authorization_issues
    )
    assert "STEP11_CYCLE001_RECOVERY_IDENTITY_INVALID" in authorization_issues
    source_tamper = replace(
        candidate,
        source_envelope=replace(
            candidate.source_envelope,
            root_bindings=candidate.source_envelope.root_bindings[:-1],
        ),
    )
    source_issues = recovery.validate_step11_cycle001_product_recovery_candidate(
        source_tamper, **kwargs
    )
    assert "STEP11_CYCLE001_RECOVERY_SOURCE_MISMATCH" in source_issues
    assert "STEP11_CYCLE001_RECOVERY_SOURCE_ENVELOPE_INVALID" in source_issues
    render_tamper = replace(
        candidate,
        rendered_surface=replace(
            candidate.rendered_surface,
            utf8_bytes=candidate.final_utf8_bytes + b"x",
        ),
    )
    render_issues = recovery.validate_step11_cycle001_product_recovery_candidate(
        render_tamper, **kwargs
    )
    assert "STEP11_CYCLE001_RECOVERY_RENDER_INVALID" in render_issues
    assert "STEP11_CYCLE001_RECOVERY_VISIBLE_INVERSE_INVALID" in render_issues
    identity_tamper = replace(candidate, candidate_id="nls3s11rc0035cand_bad")
    assert "STEP11_CYCLE001_RECOVERY_IDENTITY_INVALID" in (
        recovery.validate_step11_cycle001_product_recovery_candidate(
            identity_tamper, **kwargs
        )
    )
    assert candidate.semantic_link_atoms
    typed_payload_tamper = replace(candidate, semantic_link_atoms=())
    typed_payload_issues = (
        recovery.validate_step11_cycle001_product_recovery_candidate(
            typed_payload_tamper, **kwargs
        )
    )
    assert "STEP11_CYCLE001_RECOVERY_SOURCE_ENVELOPE_INVALID" in (
        typed_payload_issues
    )
    assert "STEP11_CYCLE001_RECOVERY_PLAN_IDENTITY_INVALID" in (
        typed_payload_issues
    )
    assert "STEP11_CYCLE001_RECOVERY_AST_IDENTITY_INVALID" in (
        typed_payload_issues
    )
    assert "STEP11_CYCLE001_RECOVERY_IDENTITY_INVALID" in typed_payload_issues


def test_cycle001_recovery_relation_lineage_namespaces_are_lossless_and_red() -> None:
    _context, kwargs = _context_and_kwargs(_samples()[34])
    import emlis_ai_step11_cycle001_product_recovery_v3 as recovery_module

    candidate = recovery_module.build_step11_cycle001_product_recovery_candidate(
        **kwargs
    )
    relation = next(
        row
        for row in candidate.source_envelope.atom_bindings
        if row.semantic_family == "relation"
    )
    assert relation.source_nucleus_owner_ids == relation.source_owner_ids
    assert relation.source_semantic_unit_owner_ids == ()
    assert relation.source_parent_nucleus_ids
    assert relation.source_evidence_alias_ids
    assert relation.source_span_ids == ()
    assert relation.source_marker_span_ids == ("s2",)
    changed_relation = replace(
        relation,
        source_marker_span_ids=("s1",),
    )
    atom_bindings = tuple(
        changed_relation if row is relation else row
        for row in candidate.source_envelope.atom_bindings
    )
    changed = replace(
        candidate,
        source_envelope=replace(
            candidate.source_envelope,
            atom_bindings=atom_bindings,
        ),
    )
    issues = recovery_module.validate_step11_cycle001_product_recovery_candidate(
        changed, **kwargs
    )
    assert "STEP11_CYCLE001_RECOVERY_SOURCE_MISMATCH" in issues
    assert "STEP11_CYCLE001_RECOVERY_SOURCE_ENVELOPE_INVALID" in issues


def test_cycle001_recovery_cross_set_owner_collision_uses_typed_incident_role() -> None:
    _context, kwargs = _context_and_kwargs(_samples()[92])
    import emlis_ai_step11_cycle001_product_recovery_v3 as recovery

    candidate = recovery.build_step11_cycle001_product_recovery_candidate(
        **kwargs
    )
    owners = candidate.source_envelope.owner_bindings
    assert len({row.referent_text_sha256 for row in owners}) == len(owners)
    by_id = {row.source_owner_id: row for row in owners}
    participant = by_id["nucleus:s1"]
    isolated_root = by_id["nucleus:s2"]
    assert participant.dimensions == isolated_root.dimensions
    assert participant.referent_basis == "typed_incident_role_disambiguation"
    assert isolated_root.referent_basis == "typed_kind"
    assert participant.referent_text != isolated_root.referent_text
    assert all("「" not in row.referent_text for row in owners)
    assert all(
        owner_id not in row.referent_text
        for row in owners
        for owner_id in by_id
    )
    with pytest.raises(recovery.Step11Cycle001ProductRecoveryError) as captured:
        recovery._owner_bindings(
            successor_snapshot=kwargs["successor_snapshot"],
            lexical_atom_specs=kwargs["lexical_atom_specs"],
            active_owner_ids=set(by_id),
            role_tokens={},
        )
    assert captured.value.code == (
        "STEP11_CYCLE001_RECOVERY_OWNER_REFERENT_COLLISION"
    )


def test_cycle001_recovery_rejects_cross_request_current_input_swap(
    representative0015: tuple[Any, Any, dict[str, Any]],
) -> None:
    recovery, candidate, kwargs0015 = representative0015
    _context0016, kwargs0016 = _context_and_kwargs(_samples()[15])
    swapped = {
        **kwargs0015,
        "current_input": kwargs0016["current_input"],
    }
    with pytest.raises(recovery.Step11Cycle001ProductRecoveryError) as captured:
        recovery.build_step11_cycle001_product_recovery_candidate(**swapped)
    assert captured.value.code == (
        "STEP11_CYCLE001_RECOVERY_CURRENT_INPUT_SOURCE_MISMATCH"
    )
    assert recovery.validate_step11_cycle001_product_recovery_candidate(
        candidate, **swapped
    ) == ("STEP11_CYCLE001_RECOVERY_REPLAY_FAILED",)
    binding = candidate.source_envelope.current_input_binding
    assert binding.normalized_bundle_sha256 == (
        binding.snapshot_original_input_bundle_sha256
    )
    assert binding.projected_material_sha256


def test_cycle001_recovery_validator_is_total_for_malformed_nested_fields(
    representative0015: tuple[Any, Any, dict[str, Any]],
) -> None:
    recovery, candidate, kwargs = representative0015
    cases = (
        (
            replace(candidate, source_envelope=None),
            "STEP11_CYCLE001_RECOVERY_SOURCE_ENVELOPE_TYPE_INVALID",
        ),
        (
            replace(candidate, realization_plan=None),
            "STEP11_CYCLE001_RECOVERY_PLAN_TYPE_INVALID",
        ),
        (
            replace(candidate, rendered_surface=None),
            "STEP11_CYCLE001_RECOVERY_RENDERED_TYPE_INVALID",
        ),
        (
            replace(candidate, relation_atoms=[object()]),
            "STEP11_CYCLE001_RECOVERY_TYPED_PAYLOAD_TYPE_INVALID",
        ),
        (
            replace(candidate, relation_atoms=(object(),)),
            "STEP11_CYCLE001_RECOVERY_TYPED_PAYLOAD_INVALID",
        ),
        (
            replace(
                candidate,
                source_envelope=replace(
                    candidate.source_envelope,
                    atom_bindings=(object(),),
                ),
            ),
            "STEP11_CYCLE001_RECOVERY_CANDIDATE_MALFORMED",
        ),
        (
            replace(
                candidate,
                realization_plan=replace(
                    candidate.realization_plan,
                    units=(object(),),
                ),
            ),
            "STEP11_CYCLE001_RECOVERY_CANDIDATE_MALFORMED",
        ),
        (
            replace(
                candidate,
                rendered_surface=replace(
                    candidate.rendered_surface,
                    utf8_bytes=object(),
                ),
            ),
            (
                "STEP11_CYCLE001_RECOVERY_RENDER_INVALID",
                "STEP11_CYCLE001_RECOVERY_SOURCE_MISMATCH",
                "STEP11_CYCLE001_RECOVERY_VISIBLE_INVERSE_INVALID",
            ),
        ),
    )
    for malformed, expected_code in cases:
        expected = (
            expected_code
            if type(expected_code) is tuple
            else (expected_code,)
        )
        assert recovery.validate_step11_cycle001_product_recovery_candidate(
            malformed, **kwargs
        ) == expected


def test_cycle001_recovery_exact100_build_replay_and_body_free_counts() -> None:
    samples = _samples()
    with ProcessPoolExecutor(max_workers=8) as pool:
        results = tuple(pool.map(_exercise_exact100_row, samples, chunksize=1))
    assert tuple(row["case_id"] for row in results) == tuple(
        row["case_id"] for row in samples
    )
    assert [row for row in results if row.get("error_code") is not None] == []
    assert all(row["replay_issues"] == () for row in results)
    assert all(row["semantic_coverage_authorized"] is True for row in results)
    assert all(row["all_roots_input_specific"] is True for row in results)
    assert all(
        row["visible_owner_referents_injective"] is True
        for row in results
    )
    assert all(row["visible_root_lineage_exact"] is True for row in results)
    assert all(row["role_dimension_lossless"] is True for row in results)
    assert all(row["reception_focus_source_native"] is True for row in results)
    assert all(
        row["visible_count"]
        == row["root_count"] + row["atom_count"] + row["reception_count"]
        for row in results
    )
    assert all(row["fragment_count"] >= row["root_count"] for row in results)
    assert all(
        row["source_counts"]["constructions"]
        == row["family_counts"]["construction"]
        and row["source_counts"]["relations"]
        == row["family_counts"]["relation"]
        and row["source_counts"]["semantic_links"]
        == row["family_counts"]["semantic_link"]
        and row["source_counts"]["explicit_unknowns"]
        == row["family_counts"]["explicit_unknown"]
        for row in results
    )
    by_case = {row["case_id"]: row for row in results}
    assert by_case["nls3s_b001_0038"]["family_counts"]["construction"] == 1
    assert by_case["nls3s_b001_0051"]["family_counts"]["construction"] == 1
    assert by_case["nls3s_b001_0054"]["family_counts"]["construction"] == 2
    assert by_case["nls3s_b001_0093"]["owner_count"] == 3
