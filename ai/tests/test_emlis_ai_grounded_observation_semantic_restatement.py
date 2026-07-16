# -*- coding: utf-8 -*-
from __future__ import annotations

"""V3 adapter tests; the frozen Grounded contract remains byte-identical."""

from dataclasses import replace
import json
from pathlib import Path

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
