from __future__ import annotations

"""Cycle001 source-bound Product recovery contract."""

import ast
import copy
import hashlib
import inspect
import json
import re
from collections import Counter
from collections.abc import Mapping, Sequence
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SERVICE_ROOT = _REPO_ROOT / "ai" / "services" / "ai_inference"
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
_PUBLIC_KWARGS = (
    "plan",
    "resolver",
    "successor_snapshot",
    "lexical_atom_specs",
    "inventory_result",
    "content_plan",
    "discourse_plans",
    "current_input",
)
_UNKNOWN_DIMENSION_BY_TYPE = {
    "cause": "cause",
    "future_outcome": "outcome",
    "omitted_referent": "referent",
    "unresolved_intention": "future",
    "decision_state": "decision_state",
    "post_decision_comparative_merit": (
        "post_decision_comparative_merit"
    ),
    "other_person": "other_person_awareness",
    "relation": "relation",
    "unspecified": "generic",
}
_UNKNOWN_BOUNDARY_SUFFIX_BY_DIMENSION = {
    "decision_state": "で選ぶ先は、まだ確定したことにしません",
    "post_decision_comparative_merit": (
        "を決めた後の比べ方は、まだ補いません"
    ),
    "other_person_awareness": (
        "が相手からどう見えるかは、まだ決めつけません"
    ),
    "cause": "の理由や背景は、まだ一つに決めません",
    "referent": "が何を指すかは、こちらで補いません",
    "future": "の先の展開は、まだ決まったことにしません",
    "outcome": "の結果は、まだ確定したことにしません",
    "relation": "の間の関係は、まだ一つに決めません",
    "generic": "に残る不明な部分は、そのまま開いておきます",
}


def _require(condition: bool, code: str) -> None:
    """Raise one body-free failure code without rendering private values."""

    if not condition:
        raise AssertionError(code)


def _ordered_unique(values: Sequence[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


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
    _require(len(rows) == 100, "CYCLE001_EXACT100_CARDINALITY_INVALID")
    identities = tuple(row.get("case_id") for row in rows)
    _require(
        all(type(value) is str and bool(value) for value in identities),
        "CYCLE001_EXACT100_IDENTITY_INVALID",
    )
    _require(
        len(set(identities)) == len(identities),
        "CYCLE001_EXACT100_IDENTITY_DUPLICATE",
    )
    _require(
        all(type(row.get("input")) is dict for row in rows),
        "CYCLE001_EXACT100_INPUT_INVALID",
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


def _product_projection(recovery: Any, kwargs: Mapping[str, Any]) -> Any:
    return recovery._build_product_projection(
        discourse_plans=kwargs["discourse_plans"],
        inventory_result=kwargs["inventory_result"],
        content_plan=kwargs["content_plan"],
        current_input=kwargs["current_input"],
    )


def _surface_sections(
    recovery: Any,
    candidate: Any,
) -> tuple[tuple[str, ...], tuple[str, ...], str]:
    _owner, catalog, grammar, _catalog_sha256 = (
        recovery._step11_rc0031_product_surface_authorities()
    )
    body = candidate.final_utf8_bytes.decode("utf-8", errors="strict")
    header = str(grammar["observation_header"])
    separator = str(grammar["section_separator"])
    suffix = str(catalog["clause_morphology"]["sentence_suffix"])
    _require(
        body.startswith(header) and body.count(separator) == 1,
        "CYCLE001_SURFACE_TOPOLOGY_INVALID",
    )
    observation_body, reception_body = body[len(header) :].split(
        separator, 1
    )

    def rows(value: str) -> tuple[str, ...]:
        if not value:
            return ()
        result = tuple(value.split("\n"))
        _require(
            all(row.endswith(suffix) for row in result),
            "CYCLE001_SURFACE_SENTENCE_BOUNDARY_INVALID",
        )
        return tuple(row[: -len(suffix)] for row in result)

    return rows(observation_body), rows(reception_body), body


def _identity_peers(snapshot: Any, source_kind: str) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for binding in snapshot.source_id_alias_bindings:
        if str(binding.source_kind) != source_kind:
            continue
        actual = str(binding.actual_source_id)
        alias = str(binding.alias_source_id)
        result.setdefault(actual, set()).update((actual, alias))
        result.setdefault(alias, set()).update((actual, alias))
    return result


def _unknown_dimension_key(value: str) -> str | None:
    """Project only the closed production unknown enum; never substring-match."""

    return _UNKNOWN_DIMENSION_BY_TYPE.get(value)


def _audit_candidate(
    recovery: Any,
    candidate: Any,
    kwargs: Mapping[str, Any],
    projection: Any,
) -> dict[str, Any]:
    """Return only body-free structural results for one private candidate."""

    envelope = candidate.source_envelope
    overlay = projection.semantic_overlay
    visible = recovery.step11_cycle001_product_recovery_visible_inverse(
        candidate
    )
    observation_visible = tuple(
        row for row in visible if row.section_role == "observation"
    )
    reception_visible = tuple(
        row for row in visible if row.section_role == "reception"
    )
    observation_lines, reception_lines, body = _surface_sections(
        recovery, candidate
    )
    observation_pairs = tuple(
        zip(observation_visible, observation_lines, strict=True)
    )
    reception_pairs = tuple(
        zip(reception_visible, reception_lines, strict=True)
    )
    observation_predicate = str(
        recovery.STEP11_SURFACE_CATALOG["grounded_lexicalization"]
        ["observation_predicate"]
    )

    grounded_owner_exact = all(
        owner.referent_basis == "grounded_semantic_feature_phrase"
        and owner.source_owner_id in projection.grounded_spec_by_actual_owner
        and owner.referent_text
        == recovery.render_step11_grounded_phrase(
            projection.grounded_spec_by_actual_owner[owner.source_owner_id]
        )
        for owner in envelope.owner_bindings
    )
    grounded_root_exact = True
    for root in envelope.root_bindings:
        matches = tuple(
            visible_row
            for visible_row, _line in observation_pairs
            if {
                fragment.source_fragment_id
                for fragment in root.source_fragments
            }
            <= set(visible_row.source_fragment_ids)
        )
        grounded_root_exact = (
            grounded_root_exact
            and len(matches) == 1
            and root.source_owner_id in matches[0].source_owner_ids
            and set(root.source_obligation_ids)
            <= set(matches[0].source_obligation_ids)
        )

    quotes = tuple(re.findall(r"「([^」]*)」", body))
    selected_owner_id = projection.selected_anchor_owner_id
    anchor_policy_exact = (
        len(quotes) <= 1
        and all(2 <= len(value) <= 16 for value in quotes)
        and (
            (selected_owner_id is not None)
            != (projection.specificity_companion_phrase is not None)
        )
    )
    if selected_owner_id is not None:
        anchor_policy_exact = (
            anchor_policy_exact
            and selected_owner_id
            in projection.first_mention_by_actual_owner
            and "「"
            in projection.first_mention_by_actual_owner[selected_owner_id]
            and all(
                owner_id == selected_owner_id or "「" not in phrase
                for owner_id, phrase
                in projection.first_mention_by_actual_owner.items()
            )
        )

    companion_units = tuple(
        (visible_row, line)
        for visible_row, line in observation_pairs
        if not visible_row.source_owner_ids
        and not visible_row.source_atom_ids
        and not visible_row.source_fragment_ids
        and not visible_row.source_obligation_ids
    )
    companion_isolated = not companion_units
    if projection.specificity_companion_phrase is not None and companion_units:
        companion_isolated = (
            len(companion_units) == 1
            and companion_units[0][1]
            == projection.specificity_companion_phrase
            + observation_predicate
        )

    visible_atom_counts = Counter(
        atom_id
        for row in observation_visible
        for atom_id in row.source_atom_ids
    )
    expected_atom_counts = Counter(
        {row.source_atom_id: 1 for row in envelope.atom_bindings}
    )
    visible_fragment_counts = Counter(
        fragment_id
        for row in observation_visible
        for fragment_id in row.source_fragment_ids
    )
    expected_fragment_counts = Counter(
        fragment.source_fragment_id
        for root in envelope.root_bindings
        for fragment in root.source_fragments
    )

    visible_relations = tuple(
        relation
        for relation in overlay.relations
        if relation.required or relation.explicit
    )
    suppressed_relations = tuple(
        relation
        for relation in overlay.relations
        if not relation.required and not relation.explicit
    )
    unassigned_relation_ids = {
        row.source_atom_id
        for row in envelope.atom_bindings
        if row.semantic_family in {"relation", "semantic_link"}
    }
    relation_exact = len(unassigned_relation_ids) == len(visible_relations)
    relation_forms = recovery.STEP11_SURFACE_CATALOG[
        "grounded_lexicalization"
    ]["relation_atoms"]
    for relation in visible_relations:
        from_owner = projection.actual_owner_by_nucleus_id[
            relation.from_nucleus_id
        ]
        to_owner = projection.actual_owner_by_nucleus_id[
            relation.to_nucleus_id
        ]
        matches = tuple(
            row
            for row in envelope.atom_bindings
            if row.source_atom_id in unassigned_relation_ids
            and row.semantic_family in {"relation", "semantic_link"}
            and tuple(row.source_owner_ids[:2]) == (from_owner, to_owner)
        )
        if len(matches) != 1:
            relation_exact = False
            continue
        atom = matches[0]
        unassigned_relation_ids.discard(atom.source_atom_id)
        rendered = tuple(
            (visible_row, line)
            for visible_row, line in observation_pairs
            if visible_row.source_unit_id == atom.source_atom_id
        )
        try:
            form = relation_forms[relation.relation_type][
                relation.relation_direction
            ]
            grammar_exact = (
                tuple(form["endpoint_order"])
                in {("from", "to"), ("to", "from")}
                and str(form["left"]) in rendered[0][1]
                and str(form["right"]) in rendered[0][1]
            )
        except (IndexError, KeyError, TypeError):
            grammar_exact = False
        relation_exact = (
            relation_exact
            and len(rendered) == 1
            and rendered[0][0].source_atom_ids == (atom.source_atom_id,)
            and rendered[0][0].source_owner_ids == (from_owner, to_owner)
            and bool(atom.direction)
            and grammar_exact
        )
    relation_exact = relation_exact and not unassigned_relation_ids
    suppressed_relation_exact = (
        relation_exact
        and len(visible_relations) + len(suppressed_relations)
        == len(overlay.relations)
        and sum(
            row.semantic_family in {"relation", "semantic_link"}
            for row in envelope.atom_bindings
        )
        == len(visible_relations)
    )

    unknown_exact = True
    explicit_unknown_ids = {
        row.source_atom_id
        for row in envelope.atom_bindings
        if row.semantic_family == "explicit_unknown"
    }
    unassigned_unknown_ids = set(explicit_unknown_ids)
    unknown_peers = _identity_peers(
        kwargs["successor_snapshot"].base_snapshot, "unknown_boundary"
    )

    def unknown_identities(values: Sequence[str]) -> set[str]:
        result: set[str] = set()
        for value in values:
            result.add(value)
            result.update(unknown_peers.get(value, ()))
        return result

    for unknown in overlay.unknowns:
        dimension_key = _unknown_dimension_key(unknown.unknown_type)
        target_ids = tuple(unknown.target_nucleus_ids)
        context_ids = tuple(unknown.context_nucleus_ids)
        if (
            dimension_key is None
            or not target_ids
            or any(
                value not in projection.actual_owner_by_nucleus_id
                for value in (*target_ids, *context_ids)
            )
        ):
            unknown_exact = False
            continue
        expected_target_owners = _ordered_unique(
            tuple(
                projection.actual_owner_by_nucleus_id[value]
                for value in target_ids
            )
        )
        expected_context_owners = _ordered_unique(
            tuple(
                projection.actual_owner_by_nucleus_id[value]
                for value in context_ids
            )
        )
        source_unknown_ids = unknown_identities(unknown.source_unknown_ids)
        matches = tuple(
            row
            for row in envelope.atom_bindings
            if row.semantic_family == "explicit_unknown"
            and row.source_atom_id in unassigned_unknown_ids
            and unknown_identities((row.source_atom_id,))
            & source_unknown_ids
        )
        rendered = tuple(
            (visible_row, line)
            for visible_row, line in observation_pairs
            if visible_row.source_unit_id == unknown.unknown_id
        )
        matched_atom_ids = tuple(row.source_atom_id for row in matches)
        matched_owner_ids = {
            owner_id for row in matches for owner_id in row.source_owner_ids
        }
        context_only_owner_ids = set(expected_context_owners) - set(
            expected_target_owners
        )
        unknown_exact = (
            unknown_exact
            and len(rendered) == 1
            and bool(matches)
            and rendered[0][0].source_owner_ids
            == expected_target_owners
            and rendered[0][0].source_atom_ids == matched_atom_ids
            and matched_owner_ids == set(expected_target_owners)
            and not context_only_owner_ids & matched_owner_ids
            and rendered[0][1].endswith(
                _UNKNOWN_BOUNDARY_SUFFIX_BY_DIMENSION[dimension_key]
            )
            and unknown.surface_policy == "preserve_open"
            and all(
                source_id not in rendered[0][1]
                for source_id in (
                    unknown.unknown_id,
                    *unknown.source_unknown_ids,
                    *unknown.target_nucleus_ids,
                    *unknown.context_nucleus_ids,
                )
            )
        )
        unassigned_unknown_ids.difference_update(matched_atom_ids)
    unknown_exact = unknown_exact and not unassigned_unknown_ids

    visible_unknown_identities = {
        *(
            row.source_atom_id
            for row in envelope.atom_bindings
            if row.semantic_family == "explicit_unknown"
        ),
        *(row.source_unit_id for row in observation_visible),
        *(
            atom_id
            for row in observation_visible
            for atom_id in row.source_atom_ids
        ),
    }
    suppressed_absent = True
    for suppressed in overlay.suppressed_unknowns:
        identities = unknown_peers.get(
            suppressed.source_unknown_id,
            {suppressed.source_unknown_id},
        )
        suppressed_absent = (
            suppressed_absent
            and not bool(identities & visible_unknown_identities)
        )

    snapshot = kwargs["successor_snapshot"].base_snapshot
    actual_by_source = {
        str(row.source_id): str(row.actual_source_id)
        for row in snapshot.nuclei
    }
    nucleus_by_actual = {
        str(row.actual_source_id): row for row in snapshot.nuclei
    }
    opportunity_by_id = {
        identity: row
        for row in snapshot.reception_opportunities
        for identity in (str(row.source_id), str(row.actual_source_id))
    }
    source_fragments = recovery._source_fragments(overlay)
    lifecycle_policy = recovery.STEP11_SURFACE_CATALOG[
        "grounded_lexicalization"
    ]["lifecycle_authority_policy"]["action_projection"]
    lifecycle_values = {*lifecycle_policy, "not_applicable"}
    _owner, catalog, _grammar, _catalog_sha256 = (
        recovery._step11_rc0031_product_surface_authorities()
    )
    act_fragments = catalog["reception_act_predicate_fragments"]
    reception_binding_exact = (
        len(overlay.reception_antecedent_bindings)
        == len(envelope.reception_bindings)
        == len(reception_pairs)
    )
    reception_lifecycle_exact = True
    reception_surface_exact = True
    for ordinal, (overlay_row, source_row) in enumerate(
        zip(
            overlay.reception_antecedent_bindings,
            envelope.reception_bindings,
            strict=True,
        ),
        start=1,
    ):
        opportunities = tuple(
            dict.fromkeys(
                opportunity_by_id[value]
                for value in overlay_row.source_reception_opportunity_ids
                if value in opportunity_by_id
            )
        )
        antecedents = (
            overlay_row.antecedent_nucleus_ids
            or overlay_row.source_target_nucleus_ids
        )
        targets = _ordered_unique(
            tuple(actual_by_source.get(value, value) for value in antecedents)
        )
        supports = _ordered_unique(
            tuple(
                actual_by_source.get(value, value)
                for value in overlay_row.supporting_nucleus_ids
            )
        )
        focus = _ordered_unique((*targets, *supports))
        visible_support = tuple(
            value for value in supports if value not in set(targets)
        )
        _require(
            all(value in nucleus_by_actual for value in targets),
            "CYCLE001_RECEPTION_TARGET_UNRESOLVED",
        )
        concrete_action = overlay_row.action_lifecycle in {
            "reported_completed",
            "reported_ongoing",
        }
        if (
            source_row.inventory_reception_act == "honor_concrete_action"
            and not concrete_action
        ):
            expected_act = "do_not_dismiss"
            expected_basis = "nonactual_action_nonpromotion"
        else:
            expected_act = source_row.inventory_reception_act
            expected_basis = "source_reception_act_projection"
        rendered = tuple(
            (visible_row, line)
            for visible_row, line in reception_pairs
            if visible_row.source_unit_id
            == source_row.source_reception_opportunity_id
        )
        exact_lifecycle_fragments = {
            fragment.realization_status
            for fragment in source_fragments
            if fragment.realization_status in lifecycle_policy
            and bool(
                set(fragment.source_nucleus_ids)
                & set(overlay_row.source_target_nucleus_ids)
            )
        }
        lifecycle_exact = (
            overlay_row.action_lifecycle in lifecycle_values
            and (
                overlay_row.action_lifecycle == "not_applicable"
                or exact_lifecycle_fragments == {overlay_row.action_lifecycle}
            )
        )
        reception_binding_exact = (
            reception_binding_exact
            and len(opportunities) == 1
            and source_row.source_reception_opportunity_id
            == str(opportunities[0].source_id)
            and source_row.source_scope == str(opportunities[0].family)
            and source_row.source_target_owner_ids == targets
            and source_row.supporting_source_owner_ids == supports
            and source_row.source_focus_owner_ids == focus
            and source_row.visible_support_owner_ids == visible_support
            and source_row.inventory_reception_act
            == str(opportunities[0].reception_act)
            and source_row.inventory_reception_act
            in overlay_row.allowed_response_acts
            and source_row.effective_reception_act == expected_act
            and source_row.act_refinement_basis == expected_basis
            and source_row.sentence_group_ordinal == ordinal
        )
        reception_lifecycle_exact = (
            reception_lifecycle_exact and lifecycle_exact
        )
        reception_surface_exact = (
            reception_surface_exact
            and len(rendered) == 1
            and rendered[0][0].source_owner_ids
            == _ordered_unique((*targets, *visible_support))
            and bool(str(act_fragments[expected_act]))
            and bool(rendered[0][1])
            and "「" not in rendered[0][1]
            and "」" not in rendered[0][1]
        )
    reception_exact = (
        reception_binding_exact
        and reception_lifecycle_exact
        and reception_surface_exact
    )

    full_input_fields = (
        envelope.current_input_binding.thought_text,
        envelope.current_input_binding.action_text,
    )
    fragment_texts = tuple(
        fragment.source_fragment_text
        for root in envelope.root_bindings
        for fragment in root.source_fragments
    )
    full_source_replay_zero = (
        all(not value or value not in body for value in full_input_fields)
        and all(
            not value
            or all(value not in reception_line for reception_line in reception_lines)
            for value in fragment_texts
        )
    )
    reception_no_echo = all(
        "「" not in line
        and "」" not in line
        and all(
            not field or field not in line
            for field in (
                envelope.current_input_binding.thought_text,
                envelope.current_input_binding.action_text,
            )
        )
        and all(
            not observation_line or observation_line not in line
            for observation_line in observation_lines
        )
        for line in reception_lines
    )

    return {
        "official_grounded": grounded_owner_exact and grounded_root_exact,
        "anchor_policy_exact": anchor_policy_exact,
        "companion_isolated": companion_isolated,
        "full_source_replay_zero": full_source_replay_zero,
        "visible_fragment_coverage_exact": (
            visible_fragment_counts == expected_fragment_counts
        ),
        "visible_atom_coverage_exact": (
            visible_atom_counts == expected_atom_counts
        ),
        "relation_exact": relation_exact,
        "suppressed_relation_exact": suppressed_relation_exact,
        "unknown_exact": unknown_exact,
        "suppressed_absent": suppressed_absent,
        "reception_exact": reception_exact,
        "reception_binding_exact": reception_binding_exact,
        "reception_lifecycle_exact": reception_lifecycle_exact,
        "reception_surface_exact": reception_surface_exact,
        "reception_no_echo": reception_no_echo,
        "relation_count": len(overlay.relations),
        "visible_relation_count": len(visible_relations),
        "suppressed_relation_count": len(suppressed_relations),
        "unknown_count": len(overlay.unknowns),
        "suppressed_count": len(overlay.suppressed_unknowns),
        "companion_count": int(
            projection.specificity_companion_phrase is not None
        ),
    }


def _exercise_exact100_row(sample: dict[str, Any]) -> dict[str, Any]:
    try:
        _context, kwargs = _context_and_kwargs(sample)
        import emlis_ai_step11_cycle001_product_recovery_v3 as recovery

        candidate = recovery.build_step11_cycle001_product_recovery_candidate(
            **kwargs
        )
        projection = _product_projection(recovery, kwargs)
        checks = _audit_candidate(recovery, candidate, kwargs, projection)
        return {
            "case_id": sample["case_id"],
            "error_code": None,
            "replay_green": (
                recovery.validate_step11_cycle001_product_recovery_candidate(
                    candidate, **kwargs
                )
                == ()
            ),
            **checks,
        }
    except Exception as exc:  # noqa: BLE001  # pragma: no cover
        code = getattr(exc, "code", None)
        if type(code) is not str:
            message = str(exc)
            code = (
                message
                if message.startswith("CYCLE001_")
                else "UNEXPECTED_RECOVERY_EXERCISE_FAILURE"
            )
        return {
            "case_id": sample.get("case_id"),
            "error_code": code,
        }


def _surface_module() -> Any:
    _install_paths()
    return __import__("emlis_ai_step11_natural_surface_v3")


@pytest.fixture(scope="module")
def semantic_representative() -> tuple[Any, Any, dict[str, Any], Any, Any]:
    """Select by active semantic topology, never by dataset identity."""

    _install_paths()
    import emlis_ai_step11_cycle001_product_recovery_v3 as recovery

    for sample in _samples():
        _context, kwargs = _context_and_kwargs(sample)
        projection = _product_projection(recovery, kwargs)
        if (
            len(kwargs["discourse_plans"]) > 1
            and projection.semantic_overlay.relations
            and projection.semantic_overlay.unknowns
        ):
            candidate = (
                recovery.build_step11_cycle001_product_recovery_candidate(
                    **kwargs
                )
            )
            return recovery, candidate, kwargs, projection, sample
    raise AssertionError("CYCLE001_STRUCTURAL_REPRESENTATIVE_MISSING")


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
    assert surface._STEP11_RC0036_CYCLE001_PRODUCT_QUALITY_CANDIDATE_VERSION_ID == (
        "nls_v3_rc_0036_cycle001_product_quality"
    )
    assert surface._STEP11_RC0036_CYCLE001_PRODUCT_QUALITY_CANDIDATE_SCHEMA == (
        "cocolon.emlis.nls_v3.step11."
        "cycle001_product_quality_candidate.rc0036.v1"
    )


def test_cycle001_recovery_public_api_is_unchanged() -> None:
    _install_paths()
    recovery = __import__("emlis_ai_step11_cycle001_product_recovery_v3")
    build_signature = inspect.signature(
        recovery.build_step11_cycle001_product_recovery_candidate
    )
    validate_signature = inspect.signature(
        recovery.validate_step11_cycle001_product_recovery_candidate
    )
    assert tuple(build_signature.parameters) == _PUBLIC_KWARGS
    assert all(
        row.kind is inspect.Parameter.KEYWORD_ONLY
        for row in build_signature.parameters.values()
    )
    assert tuple(validate_signature.parameters) == ("value", *_PUBLIC_KWARGS)
    assert all(
        validate_signature.parameters[name].kind
        is inspect.Parameter.KEYWORD_ONLY
        for name in _PUBLIC_KWARGS
    )
    expected_exports = {
        "STEP11_CYCLE001_PRODUCT_RECOVERY_SOURCE_SCHEMA",
        "Step11Cycle001ProductRecoverySourceEnvelope",
        "Step11Cycle001ProductRecoveryCandidate",
        "build_step11_cycle001_product_recovery_candidate",
        "validate_step11_cycle001_product_recovery_candidate",
    }
    assert expected_exports <= set(recovery.__all__)


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
        node.id for node in ast.walk(tree) if isinstance(node, ast.Name)
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


def test_cycle001_recovery_uses_official_grounded_authority_causally(
    semantic_representative: tuple[Any, Any, dict[str, Any], Any, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recovery, _candidate, kwargs, _projection, _sample = (
        semantic_representative
    )
    original_build = recovery.build_step11_grounded_phrase_specs
    original_select = recovery.select_step11_visible_source_anchor_use
    original_render = recovery.render_step11_grounded_phrase
    calls = Counter()

    def build_wrapper(*args: Any, **inner_kwargs: Any) -> Any:
        calls["build"] += 1
        return original_build(*args, **inner_kwargs)

    def select_wrapper(
        specs: Sequence[Any],
        fragments: Sequence[Any],
        **inner_kwargs: Any,
    ) -> Any:
        calls["select"] += 1
        _require(
            len(specs) == 1,
            "CYCLE001_OFFICIAL_SELECTOR_NOT_SINGLE_OWNER",
        )
        _require(
            inner_kwargs.get("require_input_specific_binding") is True,
            "CYCLE001_OFFICIAL_SELECTOR_BINDING_NOT_REQUIRED",
        )
        return original_select(specs, fragments, **inner_kwargs)

    def render_wrapper(*args: Any, **inner_kwargs: Any) -> str:
        calls["render"] += 1
        return original_render(*args, **inner_kwargs)

    monkeypatch.setattr(
        recovery, "build_step11_grounded_phrase_specs", build_wrapper
    )
    monkeypatch.setattr(
        recovery, "select_step11_visible_source_anchor_use", select_wrapper
    )
    monkeypatch.setattr(
        recovery, "render_step11_grounded_phrase", render_wrapper
    )
    candidate = recovery.build_step11_cycle001_product_recovery_candidate(
        **kwargs
    )
    projection = _product_projection(recovery, kwargs)
    audit = _audit_candidate(recovery, candidate, kwargs, projection)
    _require(calls["build"] > 0, "CYCLE001_OFFICIAL_BUILDER_NOT_REACHED")
    _require(calls["select"] > 0, "CYCLE001_OFFICIAL_SELECTOR_NOT_REACHED")
    _require(calls["render"] > 0, "CYCLE001_OFFICIAL_RENDERER_NOT_REACHED")
    _require(audit["official_grounded"], "CYCLE001_OFFICIAL_GROUNDING_LOST")
    _require(audit["anchor_policy_exact"], "CYCLE001_ANCHOR_POLICY_INVALID")
    _require(audit["companion_isolated"], "CYCLE001_COMPANION_NOT_ISOLATED")


def test_cycle001_recovery_legacy_quote_and_residual_paths_are_unreachable(
    semantic_representative: tuple[Any, Any, dict[str, Any], Any, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recovery, _candidate, kwargs, _projection, _sample = (
        semantic_representative
    )

    def legacy_path(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("CYCLE001_LEGACY_RENDER_PATH_REACHED")

    monkeypatch.setattr(recovery, "_root_quote", legacy_path)
    monkeypatch.setattr(recovery, "_residual_source_segments", legacy_path)
    monkeypatch.setattr(recovery, "_render", legacy_path)
    candidate = recovery.build_step11_cycle001_product_recovery_candidate(
        **kwargs
    )
    assert recovery.validate_step11_cycle001_product_recovery_candidate(
        candidate, **kwargs
    ) == ()


def test_cycle001_recovery_active_semantics_are_exact_and_nonreplaying(
    semantic_representative: tuple[Any, Any, dict[str, Any], Any, Any],
) -> None:
    recovery, candidate, kwargs, projection, _sample = (
        semantic_representative
    )
    audit = _audit_candidate(recovery, candidate, kwargs, projection)
    for key in (
        "official_grounded",
        "anchor_policy_exact",
        "companion_isolated",
        "full_source_replay_zero",
        "visible_fragment_coverage_exact",
        "visible_atom_coverage_exact",
        "relation_exact",
        "suppressed_relation_exact",
        "unknown_exact",
        "suppressed_absent",
        "reception_exact",
        "reception_no_echo",
    ):
        _require(bool(audit[key]), "CYCLE001_" + key.upper())


def test_cycle001_recovery_relation_direction_uses_typed_catalog_branch(
    semantic_representative: tuple[Any, Any, dict[str, Any], Any, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recovery, _candidate, kwargs, projection, _sample = (
        semantic_representative
    )
    patched_catalog = copy.deepcopy(recovery.STEP11_SURFACE_CATALOG)
    relation_forms = patched_catalog["grounded_lexicalization"][
        "relation_atoms"
    ]
    marker_by_branch: dict[tuple[str, str], tuple[str, str]] = {}
    for type_ordinal, (relation_type, directions) in enumerate(
        relation_forms.items(), start=1
    ):
        for direction_ordinal, (direction, form) in enumerate(
            directions.items(), start=1
        ):
            left = f"<relation-{type_ordinal}-{direction_ordinal}-left>"
            right = f"<relation-{type_ordinal}-{direction_ordinal}-right>"
            form["left"] = left
            form["right"] = right
            marker_by_branch[(relation_type, direction)] = (left, right)
    monkeypatch.setattr(recovery, "STEP11_SURFACE_CATALOG", patched_catalog)
    candidate = recovery.build_step11_cycle001_product_recovery_candidate(
        **kwargs
    )
    observation_lines, _reception_lines, _body = _surface_sections(
        recovery, candidate
    )
    visible = recovery.step11_cycle001_product_recovery_visible_inverse(
        candidate
    )
    observation_visible = tuple(
        row for row in visible if row.section_role == "observation"
    )
    visible_relations = tuple(
        relation
        for relation in projection.semantic_overlay.relations
        if relation.required or relation.explicit
    )
    suppressed_relations = tuple(
        relation
        for relation in projection.semantic_overlay.relations
        if not relation.required and not relation.explicit
    )
    relation_atom_ids = {
        row.source_atom_id
        for row in candidate.source_envelope.atom_bindings
        if row.semantic_family in {"relation", "semantic_link"}
    }
    visible_relation_rows = tuple(
        row
        for row in observation_visible
        if bool(set(row.source_atom_ids) & relation_atom_ids)
    )
    _require(
        len(visible_relation_rows) == len(visible_relations)
        and len(visible_relations) + len(suppressed_relations)
        == len(projection.semantic_overlay.relations),
        "CYCLE001_OPTIONAL_NONEXPLICIT_RELATION_NOT_SUPPRESSED",
    )
    for relation in visible_relations:
        expected_markers = marker_by_branch[
            (relation.relation_type, relation.relation_direction)
        ]
        from_owner = projection.actual_owner_by_nucleus_id[
            relation.from_nucleus_id
        ]
        to_owner = projection.actual_owner_by_nucleus_id[
            relation.to_nucleus_id
        ]
        matching_lines = tuple(
            line
            for row, line in zip(
                observation_visible, observation_lines, strict=True
            )
            if row.source_owner_ids == (from_owner, to_owner)
            and bool(set(row.source_atom_ids) & relation_atom_ids)
        )
        _require(
            len(matching_lines) == 1
            and all(marker in matching_lines[0] for marker in expected_markers),
            "CYCLE001_RELATION_DIRECTION_BRANCH_INVALID",
        )


def test_cycle001_recovery_optional_nonexplicit_relation_is_suppressed(
    semantic_representative: tuple[Any, Any, dict[str, Any], Any, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recovery, original, kwargs, projection, _sample = (
        semantic_representative
    )
    relations = tuple(projection.semantic_overlay.relations)
    _require(bool(relations), "CYCLE001_RELATION_REPRESENTATIVE_MISSING")
    suppressed = replace(relations[0], required=False, explicit=False)
    projected = replace(
        projection,
        semantic_overlay=replace(
            projection.semantic_overlay,
            relations=(suppressed, *relations[1:]),
        ),
    )
    monkeypatch.setattr(
        recovery,
        "_build_product_projection",
        lambda **_kwargs: projected,
    )
    candidate = recovery.build_step11_cycle001_product_recovery_candidate(
        **kwargs
    )
    original_relation_count = sum(
        row.semantic_family in {"relation", "semantic_link"}
        for row in original.source_envelope.atom_bindings
    )
    candidate_relation_count = sum(
        row.semantic_family in {"relation", "semantic_link"}
        for row in candidate.source_envelope.atom_bindings
    )
    audit = _audit_candidate(recovery, candidate, kwargs, projected)
    _require(
        candidate_relation_count == original_relation_count - 1,
        "CYCLE001_OPTIONAL_NONEXPLICIT_RELATION_RETAINED",
    )
    _require(
        bool(audit["relation_exact"])
        and bool(audit["suppressed_relation_exact"])
        and audit["suppressed_relation_count"] == 1,
        "CYCLE001_OPTIONAL_NONEXPLICIT_RELATION_SUPPRESSION_INVALID",
    )


def test_cycle001_recovery_is_deterministic_and_replays_strictly(
    semantic_representative: tuple[Any, Any, dict[str, Any], Any, Any],
) -> None:
    recovery, candidate, kwargs, _projection, _sample = (
        semantic_representative
    )
    replay = recovery.build_step11_cycle001_product_recovery_candidate(
        **kwargs
    )
    _require(replay == candidate, "CYCLE001_DETERMINISTIC_CANDIDATE_MISMATCH")
    _require(
        replay.candidate_id == candidate.candidate_id,
        "CYCLE001_DETERMINISTIC_IDENTITY_MISMATCH",
    )
    replay_digest = hashlib.sha256(replay.final_utf8_bytes).hexdigest()
    candidate_digest = hashlib.sha256(candidate.final_utf8_bytes).hexdigest()
    _require(
        replay_digest == candidate_digest,
        "CYCLE001_DETERMINISTIC_FINAL_DIGEST_MISMATCH",
    )
    _require(
        recovery.step11_cycle001_product_recovery_visible_inverse(replay)
        == recovery.step11_cycle001_product_recovery_visible_inverse(candidate),
        "CYCLE001_DETERMINISTIC_VISIBLE_INVERSE_MISMATCH",
    )
    _require(
        recovery.validate_step11_cycle001_product_recovery_candidate(
            replay, **kwargs
        )
        == (),
        "CYCLE001_DETERMINISTIC_REPLAY_VALIDATION_RED",
    )


def test_cycle001_recovery_full_discourse_set_is_committed_and_tamper_red(
    semantic_representative: tuple[Any, Any, dict[str, Any], Any, Any],
) -> None:
    recovery, candidate, kwargs, _projection, _sample = (
        semantic_representative
    )
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


def test_cycle001_recovery_candidate_and_typed_preimage_tamper_are_red(
    semantic_representative: tuple[Any, Any, dict[str, Any], Any, Any],
) -> None:
    recovery, candidate, kwargs, _projection, _sample = (
        semantic_representative
    )
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

    payloads = {
        name: getattr(candidate, name)
        for name in (
            "construction_atoms",
            "relation_atoms",
            "semantic_link_atoms",
            "explicit_unknown_atoms",
        )
        if getattr(candidate, name)
    }
    _require(bool(payloads), "CYCLE001_TYPED_PAYLOAD_REPRESENTATIVE_MISSING")
    payload_name, payload = next(iter(payloads.items()))
    typed_payload_tamper = replace(
        candidate, **{payload_name: payload[:-1]}
    )
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


def test_cycle001_recovery_relation_lineage_tamper_is_red(
    semantic_representative: tuple[Any, Any, dict[str, Any], Any, Any],
) -> None:
    recovery, candidate, kwargs, _projection, _sample = (
        semantic_representative
    )
    relation = next(
        row
        for row in candidate.source_envelope.atom_bindings
        if row.semantic_family in {"relation", "semantic_link"}
    )
    assert relation.source_nucleus_owner_ids == relation.source_owner_ids
    assert relation.source_parent_nucleus_ids
    changed_relation = replace(
        relation,
        source_marker_span_ids=(
            *relation.source_marker_span_ids,
            "recovery-tamper-probe",
        ),
    )
    changed = replace(
        candidate,
        source_envelope=replace(
            candidate.source_envelope,
            atom_bindings=tuple(
                changed_relation if row is relation else row
                for row in candidate.source_envelope.atom_bindings
            ),
        ),
    )
    issues = recovery.validate_step11_cycle001_product_recovery_candidate(
        changed, **kwargs
    )
    assert "STEP11_CYCLE001_RECOVERY_SOURCE_MISMATCH" in issues
    assert "STEP11_CYCLE001_RECOVERY_SOURCE_ENVELOPE_INVALID" in issues


def test_cycle001_recovery_rejects_cross_request_current_input_swap(
    semantic_representative: tuple[Any, Any, dict[str, Any], Any, Any],
) -> None:
    recovery, candidate, kwargs, _projection, _sample = (
        semantic_representative
    )
    other_kwargs = next(
        candidate_kwargs
        for row in _samples()
        for _context, candidate_kwargs in (_context_and_kwargs(row),)
        if candidate_kwargs["current_input"] != kwargs["current_input"]
    )
    swapped = {**kwargs, "current_input": other_kwargs["current_input"]}
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
    semantic_representative: tuple[Any, Any, dict[str, Any], Any, Any],
) -> None:
    recovery, candidate, kwargs, _projection, _sample = (
        semantic_representative
    )
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


def test_cycle001_recovery_exact100_product_architecture() -> None:
    samples = _samples()
    with ProcessPoolExecutor(max_workers=8) as pool:
        results = tuple(pool.map(_exercise_exact100_row, samples, chunksize=1))
    assert tuple(row["case_id"] for row in results) == tuple(
        row["case_id"] for row in samples
    )
    assert [row for row in results if row.get("error_code") is not None] == []
    architecture_keys = (
        "replay_green",
        "official_grounded",
        "anchor_policy_exact",
        "companion_isolated",
        "full_source_replay_zero",
        "visible_fragment_coverage_exact",
        "visible_atom_coverage_exact",
        "relation_exact",
        "suppressed_relation_exact",
        "unknown_exact",
        "suppressed_absent",
        "reception_binding_exact",
        "reception_lifecycle_exact",
        "reception_surface_exact",
        "reception_no_echo",
    )
    failed_architecture_keys = tuple(
        key
        for key in architecture_keys
        if not all(bool(row[key]) for row in results)
    )
    _require(
        not failed_architecture_keys,
        "CYCLE001_EXACT100_CONTRACT_RED__"
        + "__".join(key.upper() for key in failed_architecture_keys),
    )
    _require(
        sum(row["relation_count"] for row in results) > 0,
        "CYCLE001_EXACT100_RELATION_COVERAGE_MISSING",
    )
    _require(
        sum(row["unknown_count"] for row in results) > 0,
        "CYCLE001_EXACT100_UNKNOWN_COVERAGE_MISSING",
    )
    _require(
        sum(row["suppressed_count"] for row in results) > 0,
        "CYCLE001_EXACT100_SUPPRESSED_UNKNOWN_COVERAGE_MISSING",
    )
    _require(
        sum(row["companion_count"] for row in results) > 0,
        "CYCLE001_EXACT100_COMPANION_COVERAGE_MISSING",
    )
