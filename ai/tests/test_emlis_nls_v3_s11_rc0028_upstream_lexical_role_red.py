# -*- coding: utf-8 -*-
from __future__ import annotations

"""E0 RED for the rc0028 body-free upstream lexical-role experiment.

The test fixes source ownership, bounded role resources, independent
recomputation and tamper rejection.  It does not freeze completed Surface
sentences and never passes case identity or fixture annotations to production.
"""

from dataclasses import replace
import importlib
import json
from pathlib import Path

import pytest

from emlis_ai_current_input_bundle import normalize_emlis_current_input
from emlis_ai_evidence_ledger_service import (
    build_evidence_ledger,
    build_evidence_span_resolver,
)
from emlis_ai_grounded_observation_plan import build_grounded_observation_plan
from emlis_ai_observation_integrator_service import integrate_perspective_board
from emlis_ai_perspective_board import build_perspective_board
from emlis_ai_perspective_observers import run_perspective_observers
from emlis_ai_safety_triage import build_emlis_safety_triage_decision


_HERE = Path(__file__).resolve().parent
_INFERENCE = _HERE.parent / "services" / "ai_inference"
_FIXTURE = _HERE / "fixtures" / "emlis_nls_v3" / "generated" / "batch_001.jsonl"
_REPRESENTATIVE_CASE_IDS = (
    "nls3s_b001_0001",
    "nls3s_b001_0002",
    "nls3s_b001_0009",
    "nls3s_b001_0019",
    "nls3s_b001_0035",
    "nls3s_b001_0043",
    "nls3s_b001_0063",
    "nls3s_b001_0100",
)
_EXPECTED_MAJOR_CONSTRUCTIONS = {
    "nls3s_b001_0019": {"comparative_assessment", "particle_object"},
    "nls3s_b001_0035": {
        "choice_uncertainty",
        "decision_timing",
        "purpose_action",
    },
    "nls3s_b001_0043": {"explicit_contrast", "ordered_sequence"},
    "nls3s_b001_0063": {
        "reported_self_assessment",
        "explicit_coexistence",
        "parallel_addition",
        "nonreduction_boundary",
        "withheld_action",
        "ordered_sequence",
    },
    "nls3s_b001_0100": {
        "particle_object",
        "explicit_contrast",
        "balanced_consideration",
        "withheld_action",
        "ordered_sequence",
    },
}


def _owner():
    try:
        return importlib.import_module(
            "emlis_ai_grounded_lexical_role_witness_v3"
        )
    except ModuleNotFoundError:
        pytest.fail(
            "rc0028 upstream lexical-role owner is not implemented",
            pytrace=False,
        )


def _plan_and_resolver(current_input: dict[str, object]):
    normalized = normalize_emlis_current_input(dict(current_input))
    spans = tuple(build_evidence_ledger(normalized))
    resolver = build_evidence_span_resolver(
        spans,
        current_input=normalized,
    )
    reports = tuple(run_perspective_observers(spans))
    board = build_perspective_board(
        evidence_spans=spans,
        reports=reports,
    )
    graph = integrate_perspective_board(board=board)
    safety = build_emlis_safety_triage_decision(
        current_input=normalized,
        graph=graph,
        evidence_spans=spans,
    )
    plan = build_grounded_observation_plan(
        normalized,
        evidence_spans=spans,
        reports=reports,
        board=board,
        graph=graph,
        safety_decision=safety,
    )
    return normalized, plan, resolver


def _representative_inputs() -> dict[str, dict[str, object]]:
    rows: dict[str, dict[str, object]] = {}
    for line in _FIXTURE.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        case_id = str(row.get("case_id", ""))
        if case_id in _REPRESENTATIVE_CASE_IDS:
            rows[case_id] = dict(row["input"])
    assert set(rows) == set(_REPRESENTATIVE_CASE_IDS)
    return rows


@pytest.fixture(scope="module")
def representative_witnesses():
    owner = _owner()
    result = {}
    for case_id, current_input in _representative_inputs().items():
        normalized, plan, resolver = _plan_and_resolver(current_input)
        result[case_id] = (
            normalized,
            plan,
            resolver,
            owner.build_grounded_lexical_role_witness(plan, resolver),
        )
    return result


def _text_required_nucleus_ids(plan) -> set[str]:
    required = set(plan.coverage_requirements.required_nucleus_ids)
    return {
        row.nucleus_id
        for row in plan.nuclei
        if row.nucleus_id in required
        and set(row.source_fields) <= {"memo", "memo_action"}
    }


def test_rc0028_owner_exports_closed_body_free_contract() -> None:
    owner = _owner()
    assert owner.GROUNDED_LEXICAL_ROLE_WITNESS_SCHEMA.endswith(
        ".rc0028.experiment.v1"
    )
    assert owner.GROUNDED_LEXICAL_ROLE_ADAPTER_VERSION.endswith(
        ".20260719.v1"
    )
    assert owner.MAX_LEXICAL_ROLES_PER_NUCLEUS == 6
    assert owner.GroundedLexicalRoleFacet.__module__ == owner.__name__
    assert owner.GroundedLexicalRoleWitness.__module__ == owner.__name__
    assert callable(owner.build_grounded_lexical_role_witness)
    assert callable(owner.validate_grounded_lexical_role_witness)
    assert callable(owner.grounded_lexical_role_witness_material)
    assert callable(owner.resolve_grounded_lexical_role_source_text)


def test_rc0028_representative_roles_are_owner_exact_and_bounded(
    representative_witnesses,
) -> None:
    owner = _owner()
    for case_id, (_normalized, plan, resolver, witness) in (
        representative_witnesses.items()
    ):
        required_text = _text_required_nucleus_ids(plan)
        assert witness.body_free is True, case_id
        assert owner.validate_grounded_lexical_role_witness(
            witness,
            plan=plan,
            resolver=resolver,
        ) == (), case_id
        assert set(witness.covered_required_nucleus_ids).isdisjoint(
            witness.unresolved_required_nucleus_ids
        )
        assert set(witness.covered_required_nucleus_ids) | set(
            witness.unresolved_required_nucleus_ids
        ) == required_text
        assert len(witness.facets) <= witness.resource_bound
        by_owner: dict[str, list[object]] = {}
        for facet in witness.facets:
            by_owner.setdefault(facet.owner_nucleus_id, []).append(facet)
            assert facet.owner_nucleus_id in required_text
            assert facet.visible_authority == "feature_only"
            assert owner.resolve_grounded_lexical_role_source_text(
                facet,
                resolver=resolver,
            )
        assert all(
            len(rows) <= owner.MAX_LEXICAL_ROLES_PER_NUCLEUS
            and len({row.lexical_role_kind for row in rows}) == len(rows)
            for rows in by_owner.values()
        ), case_id


def test_rc0028_major_structures_have_general_lexical_constructions(
    representative_witnesses,
) -> None:
    for case_id, expected in _EXPECTED_MAJOR_CONSTRUCTIONS.items():
        witness = representative_witnesses[case_id][3]
        actual = {row.construction_code for row in witness.facets}
        assert expected <= actual, (case_id, expected - actual)


def test_rc0028_synthetic_topics_reuse_the_same_grammar() -> None:
    owner = _owner()
    current_input = {
        "thought_text": "別の手順の方が、自分には進めやすそうだ。",
        "action_text": "確認項目を二つだけ試してみた。",
        "emotions": [{"type": "平穏", "strength": "weak"}],
        "categories": ["生活"],
    }
    _normalized, plan, resolver = _plan_and_resolver(current_input)
    witness = owner.build_grounded_lexical_role_witness(plan, resolver)
    constructions = {row.construction_code for row in witness.facets}
    assert {"comparative_assessment", "particle_object"} <= constructions
    assert owner.validate_grounded_lexical_role_witness(
        witness,
        plan=plan,
        resolver=resolver,
    ) == ()


def test_rc0028_witness_material_contains_no_source_body(
    representative_witnesses,
) -> None:
    owner = _owner()
    for case_id, (normalized, _plan, _resolver, witness) in (
        representative_witnesses.items()
    ):
        material = owner.grounded_lexical_role_witness_material(
            witness,
            plan=_plan,
            resolver=_resolver,
        )
        encoded = json.dumps(material, ensure_ascii=False, sort_keys=True)
        assert material["body_free"] is True
        assert "raw_text" not in encoded
        for field in ("memo", "memo_action"):
            source = str(normalized.get(field, ""))
            assert not source or source not in encoded, (case_id, field)
        for facet in witness.facets:
            source_text = owner.resolve_grounded_lexical_role_source_text(
                facet,
                resolver=_resolver,
            )
            assert source_text not in encoded, (case_id, facet.facet_id)


def test_rc0028_owner_has_no_case_cue_topic_dictionary_or_surface_import() -> None:
    source = (
        _INFERENCE / "emlis_ai_grounded_lexical_role_witness_v3.py"
    ).read_text(encoding="utf-8")
    forbidden = (
        "case_id",
        "batch_001",
        "semantic_contract",
        "nls3s_b",
        "例題",
        "今の仕事",
        "住む場所",
        "駅のベンチ",
        "追加の依頼",
        "締切",
        "emlis_ai_step11_natural_surface_v3",
        "emlis_ai_step11_natural_surface_matcher_v3",
    )
    assert all(token not in source for token in forbidden)


def test_rc0028_facet_hash_owner_and_range_tamper_fail_closed(
    representative_witnesses,
) -> None:
    owner = _owner()
    _normalized, plan, resolver, witness = representative_witnesses[
        "nls3s_b001_0035"
    ]
    facet = witness.facets[0]
    mutations = (
        replace(facet, source_fragment_sha256="0" * 64),
        replace(facet, owner_nucleus_id="nucleus:forged"),
        replace(facet, end_index=facet.end_index + 1),
    )
    for mutation in mutations:
        forged = replace(witness, facets=(mutation, *witness.facets[1:]))
        issues = owner.validate_grounded_lexical_role_witness(
            forged,
            plan=plan,
            resolver=resolver,
        )
        assert issues
        assert any("LEXICAL_ROLE" in code for code in issues)


def test_rc0028_duplicate_role_kind_for_one_owner_fails_closed(
    representative_witnesses,
) -> None:
    owner = _owner()
    _normalized, plan, resolver, witness = representative_witnesses[
        "nls3s_b001_0043"
    ]
    facet = witness.facets[0]
    duplicate = replace(
        facet,
        facet_id=facet.facet_id[:-1] + ("0" if facet.facet_id[-1] != "0" else "1"),
    )
    forged = replace(witness, facets=(*witness.facets, duplicate))
    issues = owner.validate_grounded_lexical_role_witness(
        forged,
        plan=plan,
        resolver=resolver,
    )
    assert "LEXICAL_ROLE_FACETS_MISMATCH" in issues


def test_rc0028_role_construction_link_and_order_mutations_fail_closed(
    representative_witnesses,
) -> None:
    owner = _owner()
    _normalized, plan, resolver, witness = representative_witnesses[
        "nls3s_b001_0043"
    ]
    facet = witness.facets[0]
    mutations = (
        replace(facet, lexical_role_kind="topic_named_role"),
        replace(facet, construction_code="fixture_only_construction"),
        replace(facet, internal_link="causes"),
    )
    for mutation in mutations:
        forged = replace(witness, facets=(mutation, *witness.facets[1:]))
        assert "LEXICAL_ROLE_FACETS_MISMATCH" in (
            owner.validate_grounded_lexical_role_witness(
                forged,
                plan=plan,
                resolver=resolver,
            )
        )
    reordered = replace(witness, facets=tuple(reversed(witness.facets)))
    assert "LEXICAL_ROLE_FACETS_MISMATCH" in (
        owner.validate_grounded_lexical_role_witness(
            reordered,
            plan=plan,
            resolver=resolver,
        )
    )
    forged_reason = replace(
        witness,
        unresolved_owner_reasons=(("nucleus:forged", "RAW_BODY"),),
    )
    issues = owner.validate_grounded_lexical_role_witness(
        forged_reason,
        plan=plan,
        resolver=resolver,
    )
    assert "LEXICAL_ROLE_UNRESOLVED_REASONS_INVALID" in issues


def test_rc0028_repr_and_fail_closed_errors_are_body_free(
    representative_witnesses,
) -> None:
    owner = _owner()
    normalized, _plan, resolver, witness = representative_witnesses[
        "nls3s_b001_0100"
    ]
    encoded = repr(witness)
    for field in ("memo", "memo_action"):
        source = str(normalized.get(field, ""))
        assert not source or source not in encoded
    facet = replace(witness.facets[0], end_index=10**6)
    with pytest.raises(owner.GroundedLexicalRoleError) as error:
        owner.resolve_grounded_lexical_role_source_text(
            facet,
            resolver=resolver,
        )
    assert str(error.value) == "LEXICAL_ROLE_SOURCE_RANGE_INVALID"
    assert all(
        str(normalized.get(field, "")) not in str(error.value)
        for field in ("memo", "memo_action")
        if normalized.get(field)
    )


def test_rc0028_materializer_revalidates_before_serialization(
    representative_witnesses,
) -> None:
    owner = _owner()
    normalized, plan, resolver, witness = representative_witnesses[
        "nls3s_b001_0035"
    ]
    forged_facet = replace(
        witness.facets[0],
        facet_id=str(normalized["memo"]),
    )
    forged = replace(witness, facets=(forged_facet, *witness.facets[1:]))
    with pytest.raises(owner.GroundedLexicalRoleError) as error:
        owner.grounded_lexical_role_witness_material(
            forged,
            plan=plan,
            resolver=resolver,
        )
    assert "LEXICAL_ROLE" in str(error.value)
    assert str(normalized["memo"]) not in str(error.value)


@pytest.mark.parametrize(
    ("thought_text", "action_text", "forbidden_construction"),
    (
        ("私は丘へ行った。", "", "reported_self_assessment"),
        ("しかし、予定を変える。", "", "parallel_addition"),
        ("一人だけで、門まで歩いた。", "", "nonreduction_boundary"),
        ("眠れなくて、朝に困った。", "", "withheld_action"),
        ("事情を知らず、先へ進んだ。", "", "withheld_action"),
        ("私は資格試験を受ける。", "", "reported_self_assessment"),
        ("私は価値を調べた。", "", "reported_self_assessment"),
        ("私は無理をせず進んだ。", "", "reported_self_assessment"),
        ("今日は家で資料を読んだ。", "", "particle_object"),
    ),
)
def test_rc0028_grammatical_lookalikes_do_not_become_required_roles(
    thought_text: str,
    action_text: str,
    forbidden_construction: str,
) -> None:
    owner = _owner()
    _normalized, plan, resolver = _plan_and_resolver(
        {
            "thought_text": thought_text,
            "action_text": action_text,
            "emotions": [{"type": "平穏", "strength": "weak"}],
            "categories": ["生活"],
        }
    )
    witness = owner.build_grounded_lexical_role_witness(plan, resolver)
    assert forbidden_construction not in {
        row.construction_code for row in witness.facets
    }


def test_rc0028_overlapping_constructions_fail_closed_per_owner() -> None:
    owner = _owner()
    _normalized, plan, resolver = _plan_and_resolver(
        {
            "thought_text": "少し迷うけれど、確認してから決める。",
            "action_text": "",
            "emotions": [{"type": "平穏", "strength": "weak"}],
            "categories": ["生活"],
        }
    )
    witness = owner.build_grounded_lexical_role_witness(plan, resolver)
    required_text = _text_required_nucleus_ids(plan)
    assert set(witness.unresolved_required_nucleus_ids) == required_text
    assert witness.covered_required_nucleus_ids == ()
    assert witness.facets == ()
    assert witness.unresolved_owner_reasons == (
        (
            next(iter(required_text)),
            "LEXICAL_ROLE_AMBIGUOUS_ROLE_OVERLAP",
        ),
    )
    assert owner.validate_grounded_lexical_role_witness(
        witness,
        plan=plan,
        resolver=resolver,
    ) == ()


def test_rc0028_frozen100_builds_without_request_level_role_failure() -> None:
    owner = _owner()
    overlap_reason_seen = False
    row_count = 0
    for line in _FIXTURE.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        _normalized, plan, resolver = _plan_and_resolver(dict(row["input"]))
        witness = owner.build_grounded_lexical_role_witness(plan, resolver)
        required_text = _text_required_nucleus_ids(plan)
        reasons = dict(witness.unresolved_owner_reasons)
        assert set(witness.covered_required_nucleus_ids).isdisjoint(
            witness.unresolved_required_nucleus_ids
        )
        assert set(witness.covered_required_nucleus_ids) | set(
            witness.unresolved_required_nucleus_ids
        ) == required_text
        assert set(reasons) == set(witness.unresolved_required_nucleus_ids)
        assert len(witness.facets) <= witness.resource_bound
        assert owner.validate_grounded_lexical_role_witness(
            witness,
            plan=plan,
            resolver=resolver,
        ) == ()
        if row["case_id"] == "nls3s_b001_0054":
            overlap_reason_seen = (
                "LEXICAL_ROLE_AMBIGUOUS_ROLE_OVERLAP" in set(reasons.values())
            )
        row_count += 1
    assert row_count == 100
    assert overlap_reason_seen is True


@pytest.mark.parametrize(
    ("thought_text", "expected"),
    (
        ("別の手順の方が自分には進めやすそうだ。", "comparative_assessment"),
        ("少し迷うけれども次へ進む。", "explicit_contrast"),
        ("切り替える時期を決められない。", "decision_timing"),
    ),
)
def test_rc0028_common_punctuation_variants_keep_the_same_construction(
    thought_text: str,
    expected: str,
) -> None:
    owner = _owner()
    _normalized, plan, resolver = _plan_and_resolver(
        {
            "thought_text": thought_text,
            "action_text": "",
            "emotions": [{"type": "平穏", "strength": "weak"}],
            "categories": ["生活"],
        }
    )
    witness = owner.build_grounded_lexical_role_witness(plan, resolver)
    assert expected in {row.construction_code for row in witness.facets}


def test_rc0028_choice_douka_keeps_only_the_choice_body_in_primary_range() -> None:
    owner = _owner()
    _normalized, plan, resolver = _plan_and_resolver(
        {
            "thought_text": "行くかどうか迷っている。",
            "action_text": "",
            "emotions": [{"type": "平穏", "strength": "weak"}],
            "categories": ["生活"],
        }
    )
    witness = owner.build_grounded_lexical_role_witness(plan, resolver)
    primary = next(
        row
        for row in witness.facets
        if row.construction_code == "choice_uncertainty"
        and row.construction_position == "primary"
    )
    assert owner.resolve_grounded_lexical_role_source_text(
        primary,
        resolver=resolver,
    ) == "行く"


def test_rc0028_input_mapping_order_and_label_distractors_do_not_choose_roles() -> None:
    owner = _owner()
    base = {
        "thought_text": "別の器具の方が、自分には扱いやすそうだ。",
        "action_text": "確認箇所を三つだけ試してみた。",
        "emotions": [{"type": "平穏", "strength": "weak"}],
        "categories": ["生活"],
    }
    reordered = dict(reversed(tuple(base.items())))
    distracted = {
        **base,
        "emotions": [{"type": "不安", "strength": "strong"}],
        "categories": ["学習"],
    }
    role_shapes = []
    for current_input in (base, reordered, distracted):
        _normalized, plan, resolver = _plan_and_resolver(current_input)
        witness = owner.build_grounded_lexical_role_witness(plan, resolver)
        role_shapes.append(
            tuple(
                (
                    row.owner_nucleus_id,
                    row.start_index,
                    row.end_index,
                    row.lexical_role_kind,
                    row.construction_code,
                    row.construction_position,
                    row.internal_link,
                )
                for row in witness.facets
            )
        )
    assert role_shapes[0] == role_shapes[1] == role_shapes[2]


def test_rc0028_source_mutation_invalidates_old_witness() -> None:
    owner = _owner()
    original = {
        "thought_text": "別の手順の方が、自分には進めやすそうだ。",
        "action_text": "確認項目を二つだけ試してみた。",
        "emotions": [{"type": "平穏", "strength": "weak"}],
        "categories": ["生活"],
    }
    _normalized, plan, resolver = _plan_and_resolver(original)
    witness = owner.build_grounded_lexical_role_witness(plan, resolver)
    changed = {**original, "thought_text": "別の手順の方が、自分には覚えやすそうだ。"}
    _changed_normalized, changed_plan, changed_resolver = _plan_and_resolver(changed)
    issues = owner.validate_grounded_lexical_role_witness(
        witness,
        plan=changed_plan,
        resolver=changed_resolver,
    )
    assert issues
    assert any(
        code
        in {
            "LEXICAL_ROLE_PLAN_BINDING_MISMATCH",
            "LEXICAL_ROLE_FACETS_MISMATCH",
            "LEXICAL_ROLE_WITNESS_HASH_MISMATCH",
        }
        for code in issues
    )
