# -*- coding: utf-8 -*-
from __future__ import annotations

"""Focused G4-C causal REDs for the rejected Cycle001 Product Read.

The assertions keep private bodies in memory and report machine reason codes
only.  They exercise the frozen representative contexts; they do not create a
fixture, packet, digest, or expected final sentence.
"""

from dataclasses import replace
import ast
from functools import lru_cache
import importlib
from typing import Any

from emlis_ai_evidence_ledger_service import (
    build_evidence_ledger,
    build_evidence_span_resolver,
)
from emlis_ai_nls_v3_artifact_contract import artifact_sha256
import test_emlis_nls_v3_s11_rc0031_forward_inverse_independence as frozen


_OWNED_TYPED_RED = "OWNED_ROOT_TYPED_DEPENDENT_SURFACE_REALIZATION_NOT_PROVED"
_RECEPTION_RED = "INTEGRATED_RECEPTION_PRODUCT_SURFACE_REALIZATION_NOT_PROVED"


def _closed(value: bool, code: str) -> None:
    if not value:
        raise AssertionError(code)


def _accepted_authority(context: tuple[Any, ...]) -> tuple[Any, Any]:
    _case, baseline, successor, _lexical, candidate, _witness = context
    owner = importlib.import_module(
        "emlis_ai_step11_rc0031_reception_focus_authority_v3"
    )
    resolver = build_evidence_span_resolver(
        tuple(build_evidence_ledger(baseline.normalized_input)),
        current_input=baseline.normalized_input,
    )
    authority = owner.build_step11_rc0031_reception_focus_authority(
        baseline.grounded_plan,
        resolver,
        successor_snapshot=successor,
        base_candidate=candidate.base_candidate,
        inventory_result=baseline.inventory_result,
        content_plan=baseline.content_plan,
        current_input=baseline.projected_current_input,
    )
    _closed(
        owner.validate_step11_rc0031_reception_focus_authority(
            authority,
            plan=baseline.grounded_plan,
            resolver=resolver,
            successor_snapshot=successor,
            base_candidate=candidate.base_candidate,
            inventory_result=baseline.inventory_result,
            content_plan=baseline.content_plan,
            current_input=baseline.projected_current_input,
        )
        == (),
        _RECEPTION_RED,
    )
    return authority, resolver


def _build(context: tuple[Any, ...], authority: Any, resolver: Any) -> Any:
    _case, baseline, successor, lexical, candidate, _witness = context
    surface = frozen._surface_module()
    builder = getattr(surface, frozen._B6_ROLE_TYPED_PRIVATE_BUILDER)
    return builder(
        candidate,
        successor_snapshot=successor,
        lexical_atom_specs=lexical,
        reception_focus_authority=authority,
        plan=baseline.grounded_plan,
        resolver=resolver,
        inventory_result=baseline.inventory_result,
        content_plan=baseline.content_plan,
        current_input=baseline.projected_current_input,
    )


def _cluster_maps(context: tuple[Any, ...], built: Any) -> tuple[Any, ...]:
    _case, _baseline, successor, lexical, _candidate, _witness = context
    rows = frozen._b5_owner_projection_or_red()(
        built.base_candidate,
        successor_snapshot=successor,
        lexical_atom_specs=lexical,
    )
    return (
        {row[0]: row[3] for row in rows},
        {row[0]: row[1] for row in rows},
        {str(row.construction_instance_id): row for row in built.construction_atoms},
        {str(row.experiment_relation_id): row for row in built.relation_atoms},
        {str(row.source_semantic_link_id): row for row in built.semantic_link_atoms},
        {str(row.source_unknown_id): row for row in built.explicit_unknown_atoms},
    )


@lru_cache(maxsize=1)
def _owned_typed_evidence() -> tuple[int, int, int, int]:
    surface = frozen._surface_module()
    contexts = frozen._rc0031_final_candidate_contexts()
    builder_source = ast.parse(
        open(surface.__file__, encoding="utf-8").read()
    )
    builder = next(
        row
        for row in builder_source.body
        if isinstance(row, ast.FunctionDef)
        and row.name == frozen._B6_ROLE_TYPED_PRIVATE_BUILDER
    )
    legacy_calls = sum(
        isinstance(row, ast.Call)
        and isinstance(row.func, ast.Name)
        and row.func.id == "_step11_rc0031_product_render"
        for row in ast.walk(builder)
    )
    dependent_count = 0
    changed_count = 0
    plan_owned_group_count = 0
    original = surface._step11_rc0031_product_source_dimensions
    for context in contexts:
        authority, resolver = _accepted_authority(context)
        built = _build(context, authority, resolver)
        maps = _cluster_maps(context, built)
        _owner, catalog, grammar, _sha = (
            surface._step11_rc0031_product_surface_authorities()
        )
        separator = grammar["section_separator"]
        suffix = catalog["clause_morphology"]["sentence_suffix"]
        observation = built.rendered_surface.utf8_bytes.decode(
            "utf-8", errors="strict"
        ).split(separator, 1)[0].split("\n")[1:]
        base_ast = built.base_candidate.surface_ast
        base_lines = tuple(
            row.text
            for row in surface._observation_sentence_lines(
                base_ast, surface._additional_observation_lines(base_ast)
            )
        )
        by_group: dict[int, list[str]] = {}
        for binding in built.surface_realization_plan.proposition_clause_bindings:
            by_group.setdefault(binding.sentence_group_ordinal, []).append(
                surface._rc0031_rt_cluster(
                    binding, c=catalog, g=grammar, m=maps, s=context[2]
                )
            )
        plan_owned_group_count += sum(
            observation[group - 1]
            == catalog["clause_morphology"]["grammatical_sentence_join"].join(
                clusters
            )
            + suffix
            and not observation[group - 1].startswith(
                base_lines[group - 1][:-len(suffix)]
            )
            for group, clusters in by_group.items()
        )
        for binding in built.surface_realization_plan.proposition_clause_bindings:
            finite = tuple(
                (str(atom), str(family), tuple(map(str, owners)))
                for atom, family, owners in zip(
                    binding.source_atom_ids,
                    binding.semantic_families,
                    binding.source_atom_owner_ids,
                    strict=True,
                )
                if str(family) != "construction"
            )
            for atom, family, owners in finite:
                if atom == str(binding.head_source_atom_id):
                    continue
                dependent_count += 1
                baseline = surface._rc0031_rt_cluster(
                    binding, c=catalog, g=grammar, m=maps, s=context[2]
                )
                dimensions = original(
                    atom,
                    family,
                    owners,
                    successor_snapshot=context[2],
                    rc0031_nucleus_by_owner=maps[1],
                )
                alternate = next(
                    key
                    for key in grammar["modality_cues"]
                    if key != dimensions[1]
                )

                def controlled(*args: Any, **kwargs: Any) -> tuple[str, ...]:
                    actual = original(*args, **kwargs)
                    return (
                        (actual[0], alternate, actual[2], actual[3])
                        if str(args[0]) == atom
                        else actual
                    )

                surface._step11_rc0031_product_source_dimensions = controlled
                try:
                    changed = surface._rc0031_rt_cluster(
                        binding, c=catalog, g=grammar, m=maps, s=context[2]
                    )
                finally:
                    surface._step11_rc0031_product_source_dimensions = original
                changed_count += changed != baseline
    return (
        legacy_calls,
        dependent_count,
        changed_count,
        plan_owned_group_count,
    )


def _authority_with_controlled_focus(
    context: tuple[Any, ...], authority: Any
) -> Any:
    _case, _baseline, successor, _lexical, candidate, _witness = context
    bindings = tuple(authority.bindings)
    _closed(len(bindings) >= 2, _RECEPTION_RED)
    plan_bindings = candidate.surface_realization_plan.proposition_clause_bindings
    group_by_owner: dict[str, int] = {}
    for binding in plan_bindings:
        for owner_id in binding.source_owner_ids:
            group_by_owner[str(owner_id)] = min(
                binding.sentence_group_ordinal,
                group_by_owner.get(str(owner_id), binding.sentence_group_ordinal),
            )
    original_group = min(
        (group_by_owner.get(str(row), 0) for row in bindings[0].source_focus_owner_ids),
        default=0,
    )
    alternate_owner, _alternate_group = max(
        group_by_owner.items(), key=lambda row: (row[1], row[0])
    )
    _closed(_alternate_group != original_group, _RECEPTION_RED)
    nucleus = next(
        row
        for row in successor.base_snapshot.nuclei
        if str(row.actual_source_id) == alternate_owner
    )
    changed_row = replace(
        bindings[0],
        source_focus_owner_ids=(alternate_owner,),
        focus_modality_codes=(str(nucleus.modality),),
        focus_temporal_scope_codes=(str(nucleus.temporal_scope),),
        focus_referent_scope_codes=(str(nucleus.referent_scope),),
        owner_count=len(
            {
                alternate_owner,
                *map(str, bindings[0].source_target_owner_ids),
                *map(str, bindings[0].supporting_source_owner_ids),
            }
        ),
    )
    changed_bindings = (changed_row, *bindings[1:])
    distinct = sum(
        bool(
            set(row.source_focus_owner_ids)
            - set((*row.source_target_owner_ids, *row.supporting_source_owner_ids))
        )
        for row in changed_bindings
    )
    changed = replace(
        authority,
        bindings=changed_bindings,
        distinct_focus_binding_count=distinct,
        maximum_owner_count=max(row.owner_count for row in changed_bindings),
        authority_sha256="",
    )
    owner = importlib.import_module(
        "emlis_ai_step11_rc0031_reception_focus_authority_v3"
    )
    payload = owner._payload(
        schema_version=changed.schema_version,
        adapter_version=changed.adapter_version,
        source_observation_plan_sha256=changed.source_observation_plan_sha256,
        source_successor_snapshot_sha256=changed.source_successor_snapshot_sha256,
        bindings=changed.bindings,
        binding_count=changed.binding_count,
        distinct_focus_binding_count=changed.distinct_focus_binding_count,
        aspect_refinement_count=changed.aspect_refinement_count,
        maximum_owner_count=changed.maximum_owner_count,
        experimental_only=changed.experimental_only,
        body_free=changed.body_free,
        runtime_connected=changed.runtime_connected,
    )
    return replace(changed, authority_sha256=artifact_sha256(payload))


def test_g4c_owned_root_typed_dependent_surface_realization_is_causal() -> None:
    (
        legacy_calls,
        dependent_count,
        changed_count,
        plan_owned_group_count,
    ) = _owned_typed_evidence()
    _closed(
        legacy_calls == 0
        and dependent_count == 4
        and changed_count == dependent_count
        and plan_owned_group_count == 12,
        _OWNED_TYPED_RED,
    )


def test_g4c_integrated_reception_product_surface_realization_is_causal() -> None:
    contexts = frozen._rc0031_final_candidate_contexts()
    context = next(
        row for row in contexts if len(row[4].reception_bindings) >= 2
    )
    authority, resolver = _accepted_authority(context)
    baseline = _build(context, authority, resolver)
    changed = _authority_with_controlled_focus(context, authority)
    owner = importlib.import_module(
        "emlis_ai_step11_rc0031_reception_focus_authority_v3"
    )
    original = owner.build_step11_rc0031_reception_focus_authority
    owner.build_step11_rc0031_reception_focus_authority = (
        lambda *_args, **_kwargs: changed
    )
    try:
        rebuilt = _build(context, changed, resolver)
    finally:
        owner.build_step11_rc0031_reception_focus_authority = original
    _closed(
        rebuilt.rendered_surface.sha256 != baseline.rendered_surface.sha256,
        _RECEPTION_RED,
    )
