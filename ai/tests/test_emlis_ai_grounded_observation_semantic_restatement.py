# -*- coding: utf-8 -*-
from __future__ import annotations

"""V3 adapter tests; the frozen Grounded contract remains byte-identical."""

from dataclasses import fields, replace
from inspect import signature
import json
from pathlib import Path
from unittest.mock import patch

import pytest

import emlis_ai_grounded_observation_semantic_restatement_v3 as semantic_module
from emlis_ai_current_input_bundle import normalize_emlis_current_input
from emlis_ai_evidence_ledger_service import (
    build_evidence_ledger,
    build_evidence_span_resolver,
)
from emlis_ai_grounded_observation_plan import build_grounded_observation_plan
from emlis_ai_grounded_observation_semantic_restatement_v3 import (
    GROUND_SEMANTIC_RESTATEMENT_ADAPTER_VERSION,
    GROUND_SEMANTIC_RESTATEMENT_WITNESS_SCHEMA,
    GroundedSemanticRestatementError,
    build_grounded_semantic_restatement_witness,
    validate_grounded_semantic_restatement_witness,
)
from emlis_ai_nls_v3_artifact_contract import artifact_sha256


_BATCH_001 = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "emlis_nls_v3"
    / "generated"
    / "batch_001.jsonl"
)
_ADAPTER_SOURCE = (
    Path(__file__).resolve().parents[1]
    / "services"
    / "ai_inference"
    / "emlis_ai_grounded_observation_semantic_restatement_v3.py"
)

_CROSS_ROLE_WITNESS_SCHEMA = (
    "cocolon.emlis.nls_v3."
    "grounded_cross_role_semantic_restatement_witness.v1"
)
_CROSS_ROLE_ADAPTER_VERSION = (
    "cocolon.emlis.nls_v3."
    "grounded_cross_role_semantic_restatement_adapter.20260723.v1"
)
_CROSS_ROLE_DEPTH_SCHEMA = (
    "cocolon.emlis.nls_v3.cross_role_semantic_depth_equivalence.v1"
)
_CROSS_ROLE_PROOF_CODE = "TYPED_SEMANTIC_GRAPH_EQUIVALENCE"
_CROSS_ROLE_PROOF_BASIS = "COMPLETE_BODY_FREE_TYPED_COMPONENT_BIJECTION"
_CROSS_ROLE_EFFECT_SCOPE = "CONTENT_DEPTH_ONLY"
_CROSS_ROLE_OWNER_RED = (
    "RECOVERY_EPOCH001_S5_CROSS_ROLE_SEMANTIC_RESTATEMENT_OWNER_NOT_PROVED"
)
_CROSS_ROLE_TYPED_COMPONENT_FIELDS = (
    "source_role",
    "source_kind",
    "component_id",
    "component_kind",
    "semantic_identity_sha256",
    "referent_identity_sha256",
    "topic_identity_sha256",
    "predicate_identity_sha256",
    "polarity",
    "modality",
    "time_scope",
    "quantifier_degree",
    "relation_type",
    "relation_direction",
    "relation_from_identity_sha256",
    "relation_to_identity_sha256",
    "unknown_dimension",
    "affected_identity_sha256s",
    "must_separate",
    "required",
    "body_free",
)
_CROSS_ROLE_COMPONENT_FIELDS = (
    "binding_id",
    "component_kind",
    "original_source_role",
    "original_source_kind",
    "original_component_id",
    "supplemental_source_role",
    "supplemental_source_kind",
    "supplemental_component_id",
    "canonical_typed_component_sha256",
    "proof_code",
    "proof_basis",
)
_CROSS_ROLE_WITNESS_FIELDS = (
    "schema_version",
    "adapter_version",
    "original_plan_binding_sha256",
    "supplemental_plan_binding_sha256",
    "original_source_witness_sha256",
    "supplemental_source_witness_sha256",
    "component_bindings",
    "effect_scope",
    "depth_equivalence_schema_version",
    "witness_sha256",
    "body_free",
)
_CROSS_ROLE_NEGATIVE_CODES = frozenset(
    {
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_WITNESS_INVALID",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_WITNESS_TYPE_INVALID",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_WITNESS_SCHEMA_MISMATCH",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_WITNESS_ADAPTER_MISMATCH",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_PLAN_BINDING_MISMATCH",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_SOURCE_WITNESS_MISMATCH",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_ROLE_PAIR_INVALID",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_COMPONENT_UNRESOLVED",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_COMPONENT_KIND_MISMATCH",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_AMBIGUOUS",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_GRAPH_MISMATCH",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_PROOF_CODE_INVALID",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_PROOF_BASIS_INVALID",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_EFFECT_SCOPE_INVALID",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_DEPTH_CONTRACT_INVALID",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_BODY_FREE_REQUIRED",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_ORDER_INVALID",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_WITNESS_HASH_MISMATCH",
    }
)
_CROSS_ROLE_FALSE_COLLAPSE_FAMILIES = (
    "referent_or_topic_difference",
    "polarity_or_negation_difference",
    "modality_difference",
    "temporal_scope_difference",
    "predicate_intention_or_completion_difference",
    "quantifier_or_degree_difference",
    "subset_or_superset",
    "relation_type_direction_or_endpoint_difference",
    "unknown_dimension_or_affected_graph_difference",
    "safety_or_must_separate_pressure",
    "ambiguous_partial_one_to_many_or_many_to_one",
    "same_role_or_role_swap",
    "unresolved_id_or_kind_mismatch",
    "question_decision_endpoint",
    "witness_effect_hash_or_parent_tamper",
    "plan_resolver_bundle_partition_or_stage_drift",
    "snapshot_witness_injection_or_removal",
    "obligation_omit_defer_or_integrate",
    "active_role_drop",
    "raw_private_body_or_case_cue",
    "nondeterministic_ordering",
)


def _rows() -> tuple[dict[str, object], ...]:
    return tuple(
        json.loads(line)
        for line in _BATCH_001.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )


def _row(case_id: str) -> dict[str, object]:
    return next(item for item in _rows() if item["case_id"] == case_id)


def _artifacts(current_input: dict[str, object]):
    normalized = normalize_emlis_current_input(current_input)
    spans = tuple(build_evidence_ledger(normalized))
    resolver = build_evidence_span_resolver(spans, current_input=normalized)
    plan = build_grounded_observation_plan(normalized, evidence_spans=spans)
    witness = build_grounded_semantic_restatement_witness(plan, resolver)
    return plan, resolver, witness


def _case_artifacts(case_id: str):
    return _artifacts(_row(case_id)["input"])


def _statuses(witness) -> tuple[str, ...]:
    return tuple(item.endpoint_semantic_relation for item in witness.relations)


def test_batch001_has_only_the_two_source_semantic_restatements() -> None:
    positives: list[str] = []
    for row in _rows():
        plan, resolver, witness = _artifacts(row["input"])
        assert not validate_grounded_semantic_restatement_witness(
            witness,
            plan=plan,
            resolver=resolver,
        )
        if "semantic_restatement" in _statuses(witness):
            positives.append(row["case_id"])
    assert positives == ["nls3s_b001_0093", "nls3s_b001_0098"]


def test_restatement_unit_keeps_dependent_fragment_and_action_endpoint() -> None:
    _plan_0093, _resolver_0093, witness_0093 = _case_artifacts(
        "nls3s_b001_0093"
    )
    restatement_0093 = next(
        item
        for item in witness_0093.relations
        if item.endpoint_semantic_relation == "semantic_restatement"
    )
    assert restatement_0093.semantic_restatement_unit_nucleus_ids == (
        "nucleus:s1",
        "nucleus:s2",
        "nucleus:s3",
    )

    _plan_0098, _resolver_0098, witness_0098 = _case_artifacts(
        "nls3s_b001_0098"
    )
    restatement_0098 = next(
        item
        for item in witness_0098.relations
        if item.endpoint_semantic_relation == "semantic_restatement"
    )
    assert restatement_0098.semantic_restatement_unit_nucleus_ids == (
        "nucleus:s1",
        "nucleus:s2",
    )


def test_different_event_and_action_meanings_remain_distinct() -> None:
    for case_id in ("nls3s_b001_0017", "nls3s_b001_0053"):
        _plan, _resolver, witness = _case_artifacts(case_id)
        assert set(_statuses(witness)) == {"distinct_meanings"}
        assert all(
            not item.semantic_restatement_unit_nucleus_ids
            for item in witness.relations
        )


def test_time_destination_aspect_and_object_conflicts_are_not_restatements() -> None:
    negatives = (
        {
            "thought_text": "昨日は鉢を窓辺へ移した。",
            "action_text": "今日は鉢を棚へ移した。",
        },
        {
            "thought_text": "朝に鉢を窓辺へ移した。",
            "action_text": "夜に鉢を窓辺へ移した。",
        },
        {
            "thought_text": "書類を書いた。",
            "action_text": "書類を書き直した。",
        },
        {
            "thought_text": "鉢を窓辺へ移した。",
            "action_text": "本を棚へ移した。",
        },
        {
            "thought_text": "会議が鉢を窓辺へ移した。",
            "action_text": "鉢が会議を窓辺へ移した。",
        },
        {
            "thought_text": "掃除についての鉢を窓辺へ移した。",
            "action_text": "宿題についての鉢を窓辺へ移した。",
        },
    )
    for current_input in negatives:
        _plan, _resolver, witness = _artifacts(current_input)
        assert "semantic_restatement" not in _statuses(witness)


def test_completed_events_require_compatible_topic_or_argument_anchors() -> None:
    negatives = (
        {
            "thought_text": "掃除は終わった。",
            "action_text": "宿題は完了した。",
        },
        {
            "thought_text": "掃除については終わった。",
            "action_text": "宿題については完了した。",
        },
        {
            "thought_text": "私は掃除を終えた。",
            "action_text": "私は宿題を完了した。",
        },
        {
            "thought_text": "掃除も終わった。",
            "action_text": "宿題も完了した。",
        },
        {
            "thought_text": "掃除、終わった。",
            "action_text": "宿題、完了した。",
        },
        {
            "thought_text": "会議が作業を終わらせた。",
            "action_text": "作業が会議を終わらせた。",
        },
    )
    for current_input in negatives:
        _plan, _resolver, distinct = _artifacts(current_input)
        assert "semantic_restatement" not in _statuses(distinct)

    _plan, _resolver, restatement = _artifacts(
        {
            "thought_text": "掃除は終わった。",
            "action_text": "掃除を完了した。",
        }
    )
    assert "semantic_restatement" in _statuses(restatement)


def test_builder_rejects_cross_input_plan_and_resolver() -> None:
    plan, _resolver, _witness = _case_artifacts("nls3s_b001_0093")
    _other_plan, other_resolver, _other_witness = _case_artifacts(
        "nls3s_b001_0017"
    )
    try:
        build_grounded_semantic_restatement_witness(plan, other_resolver)
    except GroundedSemanticRestatementError as exc:
        message = str(exc)
    else:
        raise AssertionError("cross-input plan/resolver was accepted")
    assert message == "SEMANTIC_RESTATEMENT_PLAN_INVALID"
    assert _row("nls3s_b001_0093")["input"]["thought_text"] not in message
    assert _row("nls3s_b001_0017")["input"]["thought_text"] not in message


def test_validator_recomputes_status_member_set_and_hashes() -> None:
    plan, resolver, witness = _case_artifacts("nls3s_b001_0093")
    relation = witness.relations[0]
    forged_status = replace(
        witness,
        relations=(
            replace(
                relation,
                endpoint_semantic_relation="distinct_meanings",
                semantic_restatement_unit_nucleus_ids=(),
            ),
            *witness.relations[1:],
        ),
    )
    assert "SEMANTIC_RESTATEMENT_RELATIONS_MISMATCH" in (
        validate_grounded_semantic_restatement_witness(
            forged_status,
            plan=plan,
            resolver=resolver,
        )
    )

    missing_member = replace(
        witness,
        relations=(
            replace(
                relation,
                semantic_restatement_unit_nucleus_ids=(
                    "nucleus:s1",
                    "nucleus:s3",
                ),
            ),
            *witness.relations[1:],
        ),
    )
    assert "SEMANTIC_RESTATEMENT_RELATIONS_MISMATCH" in (
        validate_grounded_semantic_restatement_witness(
            missing_member,
            plan=plan,
            resolver=resolver,
        )
    )

    extra_member = replace(
        witness,
        relations=(
            replace(
                relation,
                semantic_restatement_unit_nucleus_ids=(
                    *relation.semantic_restatement_unit_nucleus_ids,
                    "nucleus:s4",
                ),
            ),
            *witness.relations[1:],
        ),
    )
    issues = validate_grounded_semantic_restatement_witness(
        extra_member,
        plan=plan,
        resolver=resolver,
    )
    assert "SEMANTIC_RESTATEMENT_RELATIONS_MISMATCH" in issues

    resigned_hash = artifact_sha256(
        {
            "schema_version": GROUND_SEMANTIC_RESTATEMENT_WITNESS_SCHEMA,
            "adapter_version": GROUND_SEMANTIC_RESTATEMENT_ADAPTER_VERSION,
            "plan_binding_sha256": extra_member.plan_binding_sha256,
            "relations": [
                {
                    "relation_id": row.relation_id,
                    "endpoint_semantic_relation": (
                        row.endpoint_semantic_relation
                    ),
                    "semantic_restatement_unit_nucleus_ids": list(
                        row.semantic_restatement_unit_nucleus_ids
                    ),
                }
                for row in extra_member.relations
            ],
            "body_free": True,
        }
    )
    resigned_attack = replace(
        extra_member,
        witness_sha256=resigned_hash,
    )
    assert "SEMANTIC_RESTATEMENT_RELATIONS_MISMATCH" in (
        validate_grounded_semantic_restatement_witness(
            resigned_attack,
            plan=plan,
            resolver=resolver,
        )
    )

    forged_hash = replace(witness, witness_sha256="0" * 64)
    assert "SEMANTIC_RESTATEMENT_WITNESS_HASH_MISMATCH" in (
        validate_grounded_semantic_restatement_witness(
            forged_hash,
            plan=plan,
            resolver=resolver,
        )
    )


def test_validator_rejects_relation_row_deletion_and_addition() -> None:
    plan, resolver, witness = _case_artifacts("nls3s_b001_0053")
    deleted = replace(witness, relations=witness.relations[:-1])
    assert "SEMANTIC_RESTATEMENT_RELATIONS_MISMATCH" in (
        validate_grounded_semantic_restatement_witness(
            deleted,
            plan=plan,
            resolver=resolver,
        )
    )
    added = replace(witness, relations=(*witness.relations, witness.relations[0]))
    assert "SEMANTIC_RESTATEMENT_RELATIONS_MISMATCH" in (
        validate_grounded_semantic_restatement_witness(
            added,
            plan=plan,
            resolver=resolver,
        )
    )


def test_witness_is_deterministic_body_free_and_has_no_fixture_cues() -> None:
    current_input = _row("nls3s_b001_0098")["input"]
    plan, resolver, witness = _artifacts(current_input)
    repeated = build_grounded_semantic_restatement_witness(plan, resolver)
    assert witness == repeated
    body_free_meta = witness.as_body_free_meta()
    assert body_free_meta["body_free"] is True
    encoded = json.dumps(
        body_free_meta,
        ensure_ascii=False,
        sort_keys=True,
    )
    assert current_input["thought_text"] not in encoded
    assert current_input["action_text"] not in encoded
    assert len(witness.plan_binding_sha256) == 64
    assert len(witness.witness_sha256) == 64

    source = _ADAPTER_SOURCE.read_text(encoding="utf-8")
    for forbidden_cue in (
        "case_id",
        "batch_001",
        "semantic_contract",
        "expected_depth_range",
        "family_id",
    ):
        assert forbidden_cue not in source


def test_v3_adapter_decomposes_only_closed_two_predicate_sources() -> None:
    expected = {
        "nls3s_b001_0009",
        "nls3s_b001_0015",
        "nls3s_b001_0038",
        "nls3s_b001_0051",
        "nls3s_b001_0054",
    }
    actual: set[str] = set()
    for row in _rows():
        plan, resolver, witness = _artifacts(row["input"])
        assert not validate_grounded_semantic_restatement_witness(
            witness,
            plan=plan,
            resolver=resolver,
        )
        if not witness.semantic_units:
            continue
        actual.add(str(row["case_id"]))
        assert len(witness.semantic_units) == 2
        assert len(witness.semantic_links) == 1
        left, right = witness.semantic_units
        link = witness.semantic_links[0]
        assert left.parent_nucleus_id == right.parent_nucleus_id
        assert left.source_span_id == right.source_span_id
        assert left.end_index <= right.start_index
        assert {link.from_unit_id, link.to_unit_id} == {
            left.unit_id,
            right.unit_id,
        }
        assert left.required is True and right.required is True
        assert link.required is True
        encoded = str(witness.as_body_free_meta())
        for body in (
            row["input"]["thought_text"],
            row["input"]["action_text"],
        ):
            if body:
                assert body not in encoded
    assert actual == expected


def test_v3_adapter_preserves_explicit_unknown_without_forcing_a_split() -> None:
    plan, resolver, witness = _case_artifacts("nls3s_b001_0001")
    assert witness.semantic_units == ()
    assert witness.semantic_links == ()
    assert witness.explicit_unknowns
    assert all(item.required is True for item in witness.explicit_unknowns)
    assert not validate_grounded_semantic_restatement_witness(
        witness,
        plan=plan,
        resolver=resolver,
    )


def _cross_role_api_or_red():
    required = (
        "GROUND_CROSS_ROLE_SEMANTIC_RESTATEMENT_WITNESS_SCHEMA",
        "GROUND_CROSS_ROLE_SEMANTIC_RESTATEMENT_ADAPTER_VERSION",
        "CROSS_ROLE_SEMANTIC_DEPTH_EQUIVALENCE_SCHEMA",
        "GROUND_CROSS_ROLE_SEMANTIC_RESTATEMENT_NEGATIVE_CODES",
        "_GroundedCrossRoleTypedSemanticComponent",
        "GroundedCrossRoleSemanticComponentBinding",
        "GroundedCrossRoleSemanticRestatementWitness",
        "_project_grounded_cross_role_typed_semantic_components",
        (
            "_build_grounded_cross_role_semantic_restatement_witness_"
            "from_typed_components"
        ),
        (
            "_validate_grounded_cross_role_semantic_restatement_witness_"
            "from_typed_components"
        ),
        "build_grounded_cross_role_semantic_restatement_witness",
        "validate_grounded_cross_role_semantic_restatement_witness",
    )
    missing = tuple(
        name for name in required if not hasattr(semantic_module, name)
    )
    if missing:
        pytest.fail(
            f"{_CROSS_ROLE_OWNER_RED}:{','.join(missing)}",
            pytrace=False,
        )
    return (
        semantic_module._GroundedCrossRoleTypedSemanticComponent,
        semantic_module.GroundedCrossRoleSemanticComponentBinding,
        semantic_module.GroundedCrossRoleSemanticRestatementWitness,
        semantic_module._project_grounded_cross_role_typed_semantic_components,
        (
            semantic_module
            ._build_grounded_cross_role_semantic_restatement_witness_from_typed_components
        ),
        (
            semantic_module
            ._validate_grounded_cross_role_semantic_restatement_witness_from_typed_components
        ),
        semantic_module.build_grounded_cross_role_semantic_restatement_witness,
        semantic_module.validate_grounded_cross_role_semantic_restatement_witness,
    )


def _semantic_commitment(namespace: str, identity: str) -> str:
    return artifact_sha256(
        {
            "namespace": namespace,
            "typed_semantic_identity": identity,
        }
    )


def _typed_component(
    component_type,
    *,
    source_role: str,
    component_id: str,
    semantic_identity: str,
    component_kind: str = "nucleus",
    **overrides,
):
    values = {
        "source_role": source_role,
        "source_kind": component_kind,
        "component_id": component_id,
        "component_kind": component_kind,
        "semantic_identity_sha256": _semantic_commitment(
            "semantic_identity",
            semantic_identity,
        ),
        "referent_identity_sha256": _semantic_commitment(
            "referent_identity",
            semantic_identity,
        ),
        "topic_identity_sha256": _semantic_commitment(
            "topic_identity",
            semantic_identity,
        ),
        "predicate_identity_sha256": _semantic_commitment(
            "predicate_identity",
            semantic_identity,
        ),
        "polarity": "positive",
        "modality": "fact",
        "time_scope": "current",
        "quantifier_degree": "exact_one",
        "relation_type": None,
        "relation_direction": None,
        "relation_from_identity_sha256": None,
        "relation_to_identity_sha256": None,
        "unknown_dimension": None,
        "affected_identity_sha256s": (),
        "must_separate": False,
        "required": True,
        "body_free": True,
    }
    values.update(overrides)
    return component_type(**values)


def _typed_graph(
    component_type,
    *,
    source_role: str,
    id_prefix: str,
):
    event = _typed_component(
        component_type,
        source_role=source_role,
        component_id=f"{id_prefix}:event",
        semantic_identity="event_identity",
    )
    context = _typed_component(
        component_type,
        source_role=source_role,
        component_id=f"{id_prefix}:context",
        semantic_identity="context_identity",
    )
    relation = _typed_component(
        component_type,
        source_role=source_role,
        component_id=f"{id_prefix}:relation",
        semantic_identity="relation_identity",
        component_kind="relation",
        relation_type="qualifies",
        relation_direction="source_to_target",
        relation_from_identity_sha256=event.semantic_identity_sha256,
        relation_to_identity_sha256=context.semantic_identity_sha256,
    )
    unknown = _typed_component(
        component_type,
        source_role=source_role,
        component_id=f"{id_prefix}:unknown",
        semantic_identity="unknown_identity",
        component_kind="unknown_boundary",
        unknown_dimension="bounded_cause",
        affected_identity_sha256s=(event.semantic_identity_sha256,),
    )
    return (event, context, relation, unknown)


def test_cross_role_semantic_restatement_contract_false_collapse_and_tamper_red() -> None:
    (
        typed_component_type,
        component_type,
        witness_type,
        project_typed_components,
        build_from_typed_components,
        validate_from_typed_components,
        build_cross_role,
        validate_cross_role,
    ) = _cross_role_api_or_red()

    assert (
        semantic_module.GROUND_CROSS_ROLE_SEMANTIC_RESTATEMENT_WITNESS_SCHEMA
        == _CROSS_ROLE_WITNESS_SCHEMA
    )
    assert (
        semantic_module.GROUND_CROSS_ROLE_SEMANTIC_RESTATEMENT_ADAPTER_VERSION
        == _CROSS_ROLE_ADAPTER_VERSION
    )
    assert (
        semantic_module.CROSS_ROLE_SEMANTIC_DEPTH_EQUIVALENCE_SCHEMA
        == _CROSS_ROLE_DEPTH_SCHEMA
    )
    assert frozenset(
        semantic_module.GROUND_CROSS_ROLE_SEMANTIC_RESTATEMENT_NEGATIVE_CODES
    ) == _CROSS_ROLE_NEGATIVE_CODES
    assert tuple(row.name for row in fields(typed_component_type)) == (
        _CROSS_ROLE_TYPED_COMPONENT_FIELDS
    )
    assert tuple(row.name for row in fields(component_type)) == (
        _CROSS_ROLE_COMPONENT_FIELDS
    )
    assert tuple(row.name for row in fields(witness_type)) == (
        _CROSS_ROLE_WITNESS_FIELDS
    )
    assert tuple(signature(build_cross_role).parameters) == (
        "original_plan",
        "original_resolver",
        "supplemental_plan",
        "supplemental_resolver",
    )
    assert tuple(signature(validate_cross_role).parameters) == (
        "value",
        "original_plan",
        "original_resolver",
        "supplemental_plan",
        "supplemental_resolver",
    )
    validate_parameters = tuple(
        signature(validate_cross_role).parameters.values()
    )
    assert all(
        parameter.kind.name == "KEYWORD_ONLY"
        for parameter in validate_parameters[1:]
    )
    assert tuple(signature(project_typed_components).parameters) == (
        "plan",
        "resolver",
        "source_local_witness",
        "source_role",
    )
    assert not {
        "_GroundedCrossRoleTypedSemanticComponent",
        "_project_grounded_cross_role_typed_semantic_components",
        (
            "_build_grounded_cross_role_semantic_restatement_witness_"
            "from_typed_components"
        ),
        (
            "_validate_grounded_cross_role_semantic_restatement_witness_"
            "from_typed_components"
        ),
    } & set(semantic_module.__all__)
    assert len(_CROSS_ROLE_FALSE_COLLAPSE_FAMILIES) == 21
    assert len(set(_CROSS_ROLE_FALSE_COLLAPSE_FAMILIES)) == 21

    forbidden_shareable_fields = {
        "raw_text",
        "normalized_text",
        "synonym",
        "case_id",
        "family_id",
        "fixture_id",
        "parsed_span",
        "private_note",
        "body_digest",
        "key",
    }
    assert not (
        forbidden_shareable_fields & set(_CROSS_ROLE_TYPED_COMPONENT_FIELDS)
    )
    assert not (
        forbidden_shareable_fields & set(_CROSS_ROLE_COMPONENT_FIELDS)
    )
    assert not forbidden_shareable_fields & set(_CROSS_ROLE_WITNESS_FIELDS)
    adapter_source = _ADAPTER_SOURCE.read_text(encoding="utf-8")
    for cue in (
        "case_id",
        "family_id",
        "fixture_id",
        "expected_surface",
        "private_note",
        "body_digest",
    ):
        assert cue not in adapter_source

    original_components = _typed_graph(
        typed_component_type,
        source_role="original_input",
        id_prefix="original",
    )
    supplemental_components = _typed_graph(
        typed_component_type,
        source_role="supplemental_answer",
        id_prefix="supplemental",
    )
    lineage = {
        "original_plan_binding_sha256": _semantic_commitment(
            "plan_binding",
            "original",
        ),
        "supplemental_plan_binding_sha256": _semantic_commitment(
            "plan_binding",
            "supplemental",
        ),
        "original_source_witness_sha256": _semantic_commitment(
            "source_witness",
            "original",
        ),
        "supplemental_source_witness_sha256": _semantic_commitment(
            "source_witness",
            "supplemental",
        ),
    }
    witness = build_from_typed_components(
        original_components=original_components,
        supplemental_components=supplemental_components,
        **lineage,
    )
    repeated = build_from_typed_components(
        original_components=original_components,
        supplemental_components=supplemental_components,
        **lineage,
    )
    assert type(witness) is witness_type
    assert witness == repeated
    assert witness.schema_version == _CROSS_ROLE_WITNESS_SCHEMA
    assert witness.adapter_version == _CROSS_ROLE_ADAPTER_VERSION
    assert witness.effect_scope == _CROSS_ROLE_EFFECT_SCOPE
    assert witness.depth_equivalence_schema_version == _CROSS_ROLE_DEPTH_SCHEMA
    assert witness.body_free is True
    assert len(witness.component_bindings) == len(original_components)
    assert all(type(row) is component_type for row in witness.component_bindings)
    assert {
        row.component_kind for row in witness.component_bindings
    } == {"nucleus", "relation", "unknown_boundary"}
    assert all(
        row.component_kind in {"nucleus", "relation", "unknown_boundary"}
        and row.original_source_role == "original_input"
        and row.original_source_kind == row.component_kind
        and row.supplemental_source_role == "supplemental_answer"
        and row.supplemental_source_kind == row.component_kind
        and row.proof_code == _CROSS_ROLE_PROOF_CODE
        and row.proof_basis == _CROSS_ROLE_PROOF_BASIS
        and len(row.canonical_typed_component_sha256) == 64
        for row in witness.component_bindings
    )
    assert len(
        {row.original_component_id for row in witness.component_bindings}
    ) == len(witness.component_bindings)
    assert len(
        {row.supplemental_component_id for row in witness.component_bindings}
    ) == len(witness.component_bindings)
    assert validate_from_typed_components(
        witness,
        original_components=original_components,
        supplemental_components=supplemental_components,
        **lineage,
    ) == ()

    encoded = json.dumps(
        witness.as_body_free_meta(),
        ensure_ascii=False,
        sort_keys=True,
    )
    assert not any(
        marker in encoded
        for marker in (
            "raw_text",
            "normalized_text",
            "synonym",
            "case_id",
            "family_id",
            "fixture_id",
            "expected_surface",
            "body_digest",
            "parsed_span",
            "private_note",
        )
    )

    parent_rows = _rows()
    original_plan, original_resolver, _original_local_witness = _artifacts(
        parent_rows[0]["input"]
    )
    (
        supplemental_plan,
        supplemental_resolver,
        _supplemental_local_witness,
    ) = _artifacts(parent_rows[-1]["input"])

    projected_roles: list[str] = []

    def owner_projection(
        plan,
        resolver,
        source_local_witness,
        source_role,
    ):
        assert validate_grounded_semantic_restatement_witness(
            source_local_witness,
            plan=plan,
            resolver=resolver,
        ) == ()
        if source_role == "original_input":
            assert plan is original_plan
            assert resolver is original_resolver
        elif source_role == "supplemental_answer":
            assert plan is supplemental_plan
            assert resolver is supplemental_resolver
        else:
            raise AssertionError("cross_role_source_role_invalid")
        projected_roles.append(source_role)
        return (
            original_components
            if source_role == "original_input"
            else supplemental_components
        )

    with patch.object(
        semantic_module,
        "_project_grounded_cross_role_typed_semantic_components",
        side_effect=owner_projection,
    ) as project_spy:
        public_witness = build_cross_role(
            original_plan,
            original_resolver,
            supplemental_plan,
            supplemental_resolver,
        )
    assert project_spy.call_count == 2
    assert projected_roles == ["original_input", "supplemental_answer"]
    assert public_witness.component_bindings == witness.component_bindings
    assert len(public_witness.original_plan_binding_sha256) == 64
    assert len(public_witness.supplemental_plan_binding_sha256) == 64
    assert len(public_witness.original_source_witness_sha256) == 64
    assert len(public_witness.supplemental_source_witness_sha256) == 64

    projected_roles.clear()
    with patch.object(
        semantic_module,
        "_project_grounded_cross_role_typed_semantic_components",
        side_effect=owner_projection,
    ) as project_spy:
        assert validate_cross_role(
            public_witness,
            original_plan=original_plan,
            original_resolver=original_resolver,
            supplemental_plan=supplemental_plan,
            supplemental_resolver=supplemental_resolver,
        ) == ()
    assert project_spy.call_count == 2
    assert projected_roles == ["original_input", "supplemental_answer"]

    restatement_sources = []
    for candidate in parent_rows:
        _candidate_plan, _candidate_resolver, candidate_witness = _artifacts(
            candidate["input"]
        )
        candidate_input = candidate["input"]
        if (
            candidate_input.get("thought_text")
            and candidate_input.get("action_text")
            and candidate_input["thought_text"] != candidate_input["action_text"]
            and any(
                row.endpoint_semantic_relation == "semantic_restatement"
                for row in candidate_witness.relations
            )
        ):
            restatement_sources.append(candidate_input)
            if len(restatement_sources) == 2:
                break
    assert len(restatement_sources) == 2
    restatement_source = restatement_sources[0]
    original_restatement_input = {
        "thought_text": restatement_source["thought_text"],
        "action_text": "",
        "emotions": [],
        "categories": [],
    }
    supplemental_restatement_input = {
        "thought_text": restatement_source["action_text"],
        "action_text": "",
        "emotions": [],
        "categories": [],
    }
    (
        original_restatement_plan,
        original_restatement_resolver,
        _original_restatement_local,
    ) = _artifacts(original_restatement_input)
    (
        supplemental_restatement_plan,
        supplemental_restatement_resolver,
        _supplemental_restatement_local,
    ) = _artifacts(supplemental_restatement_input)
    actual_public_witness = build_cross_role(
        original_restatement_plan,
        original_restatement_resolver,
        supplemental_restatement_plan,
        supplemental_restatement_resolver,
    )
    assert actual_public_witness == build_cross_role(
        original_restatement_plan,
        original_restatement_resolver,
        supplemental_restatement_plan,
        supplemental_restatement_resolver,
    )
    assert actual_public_witness.component_bindings
    assert all(
        row.original_source_role == "original_input"
        and row.supplemental_source_role == "supplemental_answer"
        and row.original_source_kind == row.component_kind
        and row.supplemental_source_kind == row.component_kind
        for row in actual_public_witness.component_bindings
    )
    assert (
        actual_public_witness.original_plan_binding_sha256
        == _original_restatement_local.plan_binding_sha256
    )
    assert (
        actual_public_witness.supplemental_plan_binding_sha256
        == _supplemental_restatement_local.plan_binding_sha256
    )
    assert (
        actual_public_witness.original_source_witness_sha256
        == _original_restatement_local.witness_sha256
    )
    assert (
        actual_public_witness.supplemental_source_witness_sha256
        == _supplemental_restatement_local.witness_sha256
    )
    assert validate_cross_role(
        actual_public_witness,
        original_plan=original_restatement_plan,
        original_resolver=original_restatement_resolver,
        supplemental_plan=supplemental_restatement_plan,
        supplemental_resolver=supplemental_restatement_resolver,
    ) == ()
    actual_public_meta = json.dumps(
        actual_public_witness.as_body_free_meta(),
        ensure_ascii=False,
        sort_keys=True,
    )
    assert original_restatement_input["thought_text"] not in actual_public_meta
    assert (
        supplemental_restatement_input["thought_text"]
        not in actual_public_meta
    )
    body_derived_digests = {
        artifact_sha256({"raw_text": body})
        for body in (
            original_restatement_input["thought_text"],
            supplemental_restatement_input["thought_text"],
        )
    } | {
        artifact_sha256(
            {
                "normalized_text": " ".join(body.split()),
            }
        )
        for body in (
            original_restatement_input["thought_text"],
            supplemental_restatement_input["thought_text"],
        )
    }
    assert not body_derived_digests & {
        row.canonical_typed_component_sha256
        for row in actual_public_witness.component_bindings
    }
    if any(
        body in adapter_source
        for body in (
            original_restatement_input["thought_text"],
            supplemental_restatement_input["thought_text"],
        )
    ):
        pytest.fail(
            "CROSS_ROLE_SEMANTIC_RESTATEMENT_BODY_FREE_REQUIRED",
            pytrace=False,
        )

    distinct_supplemental_input = {
        "thought_text": restatement_sources[1]["action_text"],
        "action_text": "",
        "emotions": [],
        "categories": [],
    }
    (
        distinct_supplemental_plan,
        distinct_supplemental_resolver,
        _distinct_supplemental_local,
    ) = _artifacts(distinct_supplemental_input)
    distinct_public_witness = build_cross_role(
        original_restatement_plan,
        original_restatement_resolver,
        distinct_supplemental_plan,
        distinct_supplemental_resolver,
    )
    assert distinct_public_witness.component_bindings == ()
    assert validate_cross_role(
        distinct_public_witness,
        original_plan=original_restatement_plan,
        original_resolver=original_restatement_resolver,
        supplemental_plan=distinct_supplemental_plan,
        supplemental_resolver=distinct_supplemental_resolver,
    ) == ()

    with patch.object(
        semantic_module,
        "_project_grounded_cross_role_typed_semantic_components",
        side_effect=owner_projection,
    ):
        assert (
            "CROSS_ROLE_SEMANTIC_RESTATEMENT_SOURCE_WITNESS_MISMATCH"
            in set(
                validate_cross_role(
                    replace(
                        public_witness,
                        original_source_witness_sha256="0" * 64,
                    ),
                    original_plan=original_plan,
                    original_resolver=original_resolver,
                    supplemental_plan=supplemental_plan,
                    supplemental_resolver=supplemental_resolver,
                )
            )
        )

    projected_roles.clear()
    with patch.object(
        semantic_module,
        "_project_grounded_cross_role_typed_semantic_components",
        side_effect=owner_projection,
    ) as project_spy:
        with pytest.raises(
            GroundedSemanticRestatementError
        ) as resolver_drift_error:
            build_cross_role(
                original_plan,
                supplemental_resolver,
                supplemental_plan,
                supplemental_resolver,
            )
    assert resolver_drift_error.value.code == (
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_PLAN_BINDING_MISMATCH"
    )
    assert project_spy.call_count == 0

    projected_roles.clear()
    with patch.object(
        semantic_module,
        "_project_grounded_cross_role_typed_semantic_components",
        side_effect=owner_projection,
    ):
        parent_drift_codes = set(
            validate_cross_role(
                public_witness,
                original_plan=supplemental_plan,
                original_resolver=supplemental_resolver,
                supplemental_plan=supplemental_plan,
                supplemental_resolver=supplemental_resolver,
            )
        )
    assert "CROSS_ROLE_SEMANTIC_RESTATEMENT_PLAN_BINDING_MISMATCH" in (
        parent_drift_codes
    )

    no_collapse_mutations = (
        {
            "referent_identity_sha256": _semantic_commitment(
                "referent_identity",
                "different",
            )
        },
        {
            "topic_identity_sha256": _semantic_commitment(
                "topic_identity",
                "different",
            )
        },
        {"polarity": "negative"},
        {"modality": "intention"},
        {"time_scope": "future"},
        {
            "predicate_identity_sha256": _semantic_commitment(
                "predicate_identity",
                "different",
            )
        },
        {"quantifier_degree": "strictly_more_than_one"},
        {"must_separate": True},
    )
    for mutation in no_collapse_mutations:
        changed = (
            replace(supplemental_components[0], **mutation),
            *supplemental_components[1:],
        )
        distinct = build_from_typed_components(
            original_components=original_components,
            supplemental_components=changed,
            **lineage,
        )
        assert distinct.component_bindings == ()
        assert validate_from_typed_components(
            distinct,
            original_components=original_components,
            supplemental_components=changed,
            **lineage,
        ) == ()

    separated_original = (
        replace(original_components[0], must_separate=True),
        *original_components[1:],
    )
    separated_supplemental = (
        replace(supplemental_components[0], must_separate=True),
        *supplemental_components[1:],
    )
    separated = build_from_typed_components(
        original_components=separated_original,
        supplemental_components=separated_supplemental,
        **lineage,
    )
    assert separated.component_bindings == ()

    safety_source = next(
        candidate["input"]
        for candidate in parent_rows
        if (
            (
                candidate_plan := _artifacts(candidate["input"])[0]
            ).safety_policy.identity_claim_must_not_be_accepted_as_fact
            and candidate_plan.safety_policy.required_boundary_codes
            and candidate_plan.response_plan.fact_boundary_nucleus_ids
        )
    )
    (
        safety_plan,
        safety_resolver,
        safety_local_witness,
    ) = _artifacts(safety_source)
    safety_nucleus_ids = set(
        safety_plan.response_plan.fact_boundary_nucleus_ids
    )
    safety_original_projected = project_typed_components(
        safety_plan,
        safety_resolver,
        safety_local_witness,
        "original_input",
    )
    safety_supplemental_projected = project_typed_components(
        safety_plan,
        safety_resolver,
        safety_local_witness,
        "supplemental_answer",
    )
    for projected in (
        safety_original_projected,
        safety_supplemental_projected,
    ):
        projected_safety = [
            row
            for row in projected
            if row.component_id in safety_nucleus_ids
        ]
        assert projected_safety
        assert all(row.must_separate for row in projected_safety)
    safety_public_witness = build_cross_role(
        safety_plan,
        safety_resolver,
        safety_plan,
        safety_resolver,
    )
    safety_bound_endpoint_ids = {
        endpoint_id
        for binding in safety_public_witness.component_bindings
        for endpoint_id in (
            binding.original_component_id,
            binding.supplemental_component_id,
        )
    }
    assert safety_public_witness.component_bindings
    assert safety_nucleus_ids.isdisjoint(safety_bound_endpoint_ids)
    assert validate_cross_role(
        safety_public_witness,
        original_plan=safety_plan,
        original_resolver=safety_resolver,
        supplemental_plan=safety_plan,
        supplemental_resolver=safety_resolver,
    ) == ()

    safety_original = (
        replace(original_components[0], must_separate=True),
        original_components[1],
    )
    safety_supplemental = (
        supplemental_components[0],
        supplemental_components[1],
    )
    safety_partial = build_from_typed_components(
        original_components=safety_original,
        supplemental_components=safety_supplemental,
        **lineage,
    )
    assert safety_partial.component_bindings
    assert {
        row.original_component_id
        for row in safety_partial.component_bindings
    } == {original_components[1].component_id}
    assert {
        row.supplemental_component_id
        for row in safety_partial.component_bindings
    } == {supplemental_components[1].component_id}
    assert validate_from_typed_components(
        safety_partial,
        original_components=safety_original,
        supplemental_components=safety_supplemental,
        **lineage,
    ) == ()

    relation_index = next(
        index
        for index, row in enumerate(supplemental_components)
        if row.component_kind == "relation"
    )
    unknown_index = next(
        index
        for index, row in enumerate(supplemental_components)
        if row.component_kind == "unknown_boundary"
    )
    for mutation in (
        {"relation_type": "contrasts_with"},
        {"relation_direction": "bidirectional"},
        {
            "relation_to_identity_sha256": _semantic_commitment(
                "semantic_identity",
                "different_endpoint",
            )
        },
    ):
        changed = list(supplemental_components)
        changed[relation_index] = replace(changed[relation_index], **mutation)
        distinct = build_from_typed_components(
            original_components=original_components,
            supplemental_components=tuple(changed),
            **lineage,
        )
        assert distinct.component_bindings == ()

    for mutation in (
        {"unknown_dimension": "different_dimension"},
        {
            "affected_identity_sha256s": (
                _semantic_commitment(
                    "semantic_identity",
                    "different_affected_component",
                ),
            )
        },
    ):
        changed = list(supplemental_components)
        changed[unknown_index] = replace(changed[unknown_index], **mutation)
        distinct = build_from_typed_components(
            original_components=original_components,
            supplemental_components=tuple(changed),
            **lineage,
        )
        assert distinct.component_bindings == ()

    unmatched = _typed_component(
        typed_component_type,
        source_role="supplemental_answer",
        component_id="supplemental:unmatched",
        semantic_identity="unmatched_identity",
    )
    partial = build_from_typed_components(
        original_components=original_components,
        supplemental_components=(*supplemental_components, unmatched),
        **lineage,
    )
    assert len(partial.component_bindings) == len(original_components)
    assert all(
        row.supplemental_component_id != unmatched.component_id
        for row in partial.component_bindings
    )

    def codes(
        candidate,
        *,
        current_original=original_components,
        current_supplemental=supplemental_components,
        current_lineage=lineage,
    ) -> set[str]:
        return set(
            validate_from_typed_components(
                candidate,
                original_components=current_original,
                supplemental_components=current_supplemental,
                **current_lineage,
            )
        )

    assert "CROSS_ROLE_SEMANTIC_RESTATEMENT_WITNESS_TYPE_INVALID" in codes(
        object()
    )
    assert "CROSS_ROLE_SEMANTIC_RESTATEMENT_WITNESS_INVALID" in codes(
        replace(witness, component_bindings=None)
    )
    assert "CROSS_ROLE_SEMANTIC_RESTATEMENT_WITNESS_SCHEMA_MISMATCH" in codes(
        replace(witness, schema_version="forged")
    )
    assert "CROSS_ROLE_SEMANTIC_RESTATEMENT_WITNESS_ADAPTER_MISMATCH" in codes(
        replace(witness, adapter_version="forged")
    )

    first = witness.component_bindings[0]
    second = witness.component_bindings[1]
    role_swap = replace(
        witness,
        component_bindings=(
            replace(
                first,
                original_source_role="supplemental_answer",
                supplemental_source_role="original_input",
            ),
            *witness.component_bindings[1:],
        ),
    )
    assert "CROSS_ROLE_SEMANTIC_RESTATEMENT_ROLE_PAIR_INVALID" in codes(
        role_swap
    )

    question_endpoint = replace(
        witness,
        component_bindings=(
            replace(first, original_source_role="question_need_decision"),
            *witness.component_bindings[1:],
        ),
    )
    assert "CROSS_ROLE_SEMANTIC_RESTATEMENT_ROLE_PAIR_INVALID" in codes(
        question_endpoint
    )

    same_role_components = tuple(
        replace(row, source_role="original_input")
        for row in supplemental_components
    )
    with pytest.raises(GroundedSemanticRestatementError) as same_role_error:
        build_from_typed_components(
            original_components=original_components,
            supplemental_components=same_role_components,
            **lineage,
        )
    assert same_role_error.value.code == (
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_ROLE_PAIR_INVALID"
    )

    wrong_kind = replace(
        witness,
        component_bindings=(
            replace(first, component_kind="unknown_boundary"),
            *witness.component_bindings[1:],
        ),
    )
    assert "CROSS_ROLE_SEMANTIC_RESTATEMENT_COMPONENT_KIND_MISMATCH" in codes(
        wrong_kind
    )

    one_to_many = replace(
        witness,
        component_bindings=(
            first,
            replace(
                second,
                original_component_id=first.original_component_id,
            ),
            *witness.component_bindings[2:],
        ),
    )
    assert "CROSS_ROLE_SEMANTIC_RESTATEMENT_AMBIGUOUS" in codes(one_to_many)

    many_to_one = replace(
        witness,
        component_bindings=(
            first,
            replace(
                second,
                supplemental_component_id=first.supplemental_component_id,
            ),
            *witness.component_bindings[2:],
        ),
    )
    assert "CROSS_ROLE_SEMANTIC_RESTATEMENT_AMBIGUOUS" in codes(many_to_one)

    ambiguous_components = (
        *supplemental_components,
        replace(
            supplemental_components[0],
            component_id="supplemental:ambiguous",
        ),
    )
    with pytest.raises(GroundedSemanticRestatementError) as ambiguous_error:
        build_from_typed_components(
            original_components=original_components,
            supplemental_components=ambiguous_components,
            **lineage,
        )
    assert ambiguous_error.value.code == (
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_AMBIGUOUS"
    )

    ambiguous_original_components = (
        *original_components,
        replace(
            original_components[0],
            component_id="original:ambiguous",
        ),
    )
    with pytest.raises(
        GroundedSemanticRestatementError
    ) as ambiguous_original_error:
        build_from_typed_components(
            original_components=ambiguous_original_components,
            supplemental_components=supplemental_components,
            **lineage,
        )
    assert ambiguous_original_error.value.code == (
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_AMBIGUOUS"
    )

    unresolved = replace(
        witness,
        component_bindings=(
            replace(first, original_component_id="original:unresolved"),
            *witness.component_bindings[1:],
        ),
    )
    assert "CROSS_ROLE_SEMANTIC_RESTATEMENT_COMPONENT_UNRESOLVED" in codes(
        unresolved
    )

    deleted = replace(
        witness,
        component_bindings=witness.component_bindings[:-1],
    )
    assert "CROSS_ROLE_SEMANTIC_RESTATEMENT_GRAPH_MISMATCH" in codes(deleted)

    injected = replace(
        witness,
        component_bindings=(
            *witness.component_bindings,
            witness.component_bindings[0],
        ),
    )
    assert "CROSS_ROLE_SEMANTIC_RESTATEMENT_AMBIGUOUS" in codes(injected)

    reordered = replace(
        witness,
        component_bindings=tuple(reversed(witness.component_bindings)),
    )
    assert "CROSS_ROLE_SEMANTIC_RESTATEMENT_ORDER_INVALID" in codes(reordered)

    wrong_graph = replace(
        witness,
        component_bindings=(
            replace(first, canonical_typed_component_sha256="0" * 64),
            *witness.component_bindings[1:],
        ),
    )
    assert "CROSS_ROLE_SEMANTIC_RESTATEMENT_GRAPH_MISMATCH" in codes(
        wrong_graph
    )

    wrong_proof_code = replace(
        witness,
        component_bindings=(
            replace(first, proof_code="FORGED"),
            *witness.component_bindings[1:],
        ),
    )
    assert "CROSS_ROLE_SEMANTIC_RESTATEMENT_PROOF_CODE_INVALID" in codes(
        wrong_proof_code
    )

    wrong_proof_basis = replace(
        witness,
        component_bindings=(
            replace(first, proof_basis="FORGED"),
            *witness.component_bindings[1:],
        ),
    )
    assert "CROSS_ROLE_SEMANTIC_RESTATEMENT_PROOF_BASIS_INVALID" in codes(
        wrong_proof_basis
    )

    assert "CROSS_ROLE_SEMANTIC_RESTATEMENT_PLAN_BINDING_MISMATCH" in codes(
        replace(witness, original_plan_binding_sha256="0" * 64)
    )
    changed_lineage = {
        **lineage,
        "original_source_witness_sha256": "0" * 64,
    }
    assert "CROSS_ROLE_SEMANTIC_RESTATEMENT_SOURCE_WITNESS_MISMATCH" in codes(
        witness,
        current_lineage=changed_lineage,
    )
    assert "CROSS_ROLE_SEMANTIC_RESTATEMENT_EFFECT_SCOPE_INVALID" in codes(
        replace(witness, effect_scope="OBLIGATION_SELECTION")
    )
    assert "CROSS_ROLE_SEMANTIC_RESTATEMENT_DEPTH_CONTRACT_INVALID" in codes(
        replace(witness, depth_equivalence_schema_version="forged")
    )
    assert "CROSS_ROLE_SEMANTIC_RESTATEMENT_BODY_FREE_REQUIRED" in codes(
        replace(witness, body_free=False)
    )
    assert "CROSS_ROLE_SEMANTIC_RESTATEMENT_WITNESS_HASH_MISMATCH" in codes(
        replace(witness, witness_sha256="0" * 64)
    )
