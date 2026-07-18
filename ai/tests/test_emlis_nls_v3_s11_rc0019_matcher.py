# -*- coding: utf-8 -*-
from __future__ import annotations

from types import SimpleNamespace

import pytest

import emlis_ai_step11_natural_surface_matcher_v3 as matcher
import emlis_ai_step11_natural_surface_v3 as surface
from emlis_ai_step11_surface_catalog_v3 import STEP11_SURFACE_CATALOG


def _grouped_body() -> bytes:
    introductions = STEP11_SURFACE_CATALOG["endpoint_reference_grammar"][
        "natural_introduction"
    ]["forms"]
    relation = STEP11_SURFACE_CATALOG["relation_forms"]["precedes"][
        "source_to_target"
    ]["proposition"]["action"][0]["stem"].format(
        from_ref="1つ目の記述内容",
        to_ref="2つ目の行動",
    )
    observation = "、また、".join(
        (
            introductions["thought"]["proposition"][0].format(
                quoted_literal="『A、また、B』"
            ),
            introductions["action"]["action"][0].format(
                quoted_literal="『書いた』"
            ),
            relation,
        )
    )
    reception = (
        "〔1つ目の記述内容〕から〔2つ目の行動〕への関わりを、"
        "Emlisは気に留めています"
    )
    return (
        "見えたこと：\n"
        + observation
        + "。\n\nEmlisから：\n"
        + reception
        + "。"
    ).encode("utf-8")


def test_parser_recovers_group_sentences_and_typed_references() -> None:
    witness = matcher.parse_step11_natural_surface(_grouped_body())

    assert witness.schema_version.endswith("witness.v7")
    assert len(witness.sentences) == 2
    assert witness.sentences[0].clause_atom_ids == tuple(
        row.atom_id for row in witness.atoms[:3]
    )
    assert tuple(row.clause_ordinal for row in witness.atoms[:3]) == (
        1,
        2,
        3,
    )
    first, second, relation = witness.atoms[:3]
    assert first.source_fragments == ("A、また、B",)
    assert first.introduced_reference == matcher.Step11EndpointReference(
        1, "proposition"
    )
    assert second.introduced_reference == matcher.Step11EndpointReference(
        2, "action"
    )
    assert relation.source_fragments == ()
    assert relation.claim_kinds == ("relation_notice",)
    assert relation.relation_endpoint_references == (
        matcher.Step11EndpointReference(1, "proposition"),
        matcher.Step11EndpointReference(2, "action"),
    )


def test_new_parsed_atom_fields_keep_legacy_constructor_compatibility() -> None:
    atom = matcher.Step11ParsedAtom(
        atom_id="nls3s11atom_0000000000000000",
        section_role="observation",
        form_id="unknown_dimension:generic:0",
        claim_kinds=("unknown_boundary",),
        source_slot_hints=(),
        source_fragments=(),
        predicate_role="unknown",
        realization_status="undetermined",
        relation_type=None,
        relation_direction=None,
        relation_endpoint_roles=(),
        unknown_dimension_class="generic",
        self_denial_not_fact=False,
        reception_act=None,
        reception_scope=None,
        byte_start=0,
        byte_end=1,
    )

    assert atom.introduced_reference is None
    assert atom.relation_endpoint_references == ()
    assert atom.sentence_ordinal == 0
    assert atom.clause_ordinal == 0


def test_independent_registry_uses_exact_active_source_order() -> None:
    anchors = (
        SimpleNamespace(
            anchor_id="anchor_action",
            source_slot="action",
            start=0,
            end=3,
            text="書いた",
        ),
        SimpleNamespace(
            anchor_id="anchor_thought",
            source_slot="thought",
            start=0,
            end=3,
            text="考えた",
        ),
    )
    overlay = SimpleNamespace(
        anchors=anchors,
        label_anchors=(),
        nucleus_anchor_bindings=(
            SimpleNamespace(
                nucleus_id="n_action",
                source_anchor_ids=("anchor_action",),
                source_label_anchor_ids=(),
            ),
            SimpleNamespace(
                nucleus_id="n_thought",
                source_anchor_ids=("anchor_thought",),
                source_label_anchor_ids=(),
            ),
        ),
    )
    relation = SimpleNamespace(
        from_source_anchor_ids=("anchor_thought",),
        from_label_anchor_ids=(),
        from_endpoint_role="proposition",
        to_source_anchor_ids=("anchor_action",),
        to_label_anchor_ids=(),
        to_endpoint_role="action",
    )

    registry, issues = matcher._independent_reference_registry(
        active_nucleus_ids=frozenset({"n_action", "n_thought"}),
        semantic_overlay=overlay,
        relations=(relation,),
    )

    assert issues == ()
    assert tuple(row.reference_ordinal for row in registry) == (1, 2)
    assert tuple(row.source_slot for row in registry) == (
        "thought",
        "action",
    )
    assert tuple(row.endpoint_role for row in registry) == (
        "proposition",
        "action",
    )


def test_independent_unknown_classifier_excludes_completed_choice() -> None:
    assert (
        matcher._independent_explicit_unknown_type(
            "今の情報だけでは選べない。"
        )
        == "decision_state"
    )
    assert matcher._independent_explicit_unknown_type("一つ選べた。") is None


@pytest.mark.parametrize(
    ("source_dimension", "anaphora_key", "inverse_dimension"),
    (
        ("cause", "cause", "cause"),
        ("omitted_referent", "referent", "referent"),
        (
            "other_person",
            "referent_other",
            "other_person_awareness",
        ),
        ("future_outcome", "future", "future"),
        ("decision_state", "decision_state", "decision_state"),
        (
            "post_decision_comparative_merit",
            "post_decision_comparative_merit",
            "post_decision_comparative_merit",
        ),
        ("outcome", "outcome", "outcome"),
        ("relation", "relation", "relation"),
        ("unspecified", "generic", "generic"),
    ),
)
def test_unknown_anaphora_forward_inverse_dimension_mapping_is_exact(
    source_dimension: str,
    anaphora_key: str,
    inverse_dimension: str,
) -> None:
    forward_dimension = surface._unknown_dimension_class(source_dimension)
    forward_key = (
        "referent_other"
        if forward_dimension == "other_person_awareness"
        else forward_dimension
    )
    rule = STEP11_SURFACE_CATALOG["observation_forms"][
        "unknown_anaphora"
    ][anaphora_key][0]
    if anaphora_key == "relation":
        line = rule["stem"].format(
            from_ref="1つ目の記述内容",
            to_ref="2つ目の行動",
        )
    else:
        line = rule["stem"].format(
            target_ref="1つ目の記述内容"
        )
    parsed = matcher._unknown_reference_clause(
        matcher._catalog_clause_stem(line)
    )

    assert forward_key == anaphora_key
    assert parsed is not None
    assert parsed[0].startswith(f"unknown_anaphora:{anaphora_key}:")
    assert parsed[1] == inverse_dimension
    assert len(parsed[2]) == (2 if anaphora_key == "relation" else 1)


def test_other_person_anaphora_does_not_alias_generic_referent() -> None:
    other_rule = STEP11_SURFACE_CATALOG["observation_forms"][
        "unknown_anaphora"
    ]["referent_other"][0]
    generic_rule = STEP11_SURFACE_CATALOG["observation_forms"][
        "unknown_anaphora"
    ]["referent"][0]
    target_ref = "1つ目の記述内容"
    other = matcher._unknown_reference_clause(
        matcher._catalog_clause_stem(
            other_rule["stem"].format(target_ref=target_ref)
        )
    )
    generic = matcher._unknown_reference_clause(
        matcher._catalog_clause_stem(
            generic_rule["stem"].format(target_ref=target_ref)
        )
    )
    assert other is not None and generic is not None
    other_dimension = other[1]
    generic_dimension = generic[1]

    assert other_dimension == "other_person_awareness"
    assert generic_dimension == "referent"
    assert matcher._unknown_class("other_person") == other_dimension
    assert matcher._unknown_class("other_person") != generic_dimension


def test_semantic_action_role_is_independent_of_physical_source_slot() -> None:
    legacy_memo_action = SimpleNamespace(
        source_fields=("memo",),
        kind="other_explicit",
        source_predicate_kind="action",
        modality="observed",
    )
    ordinary_memo_proposition = SimpleNamespace(
        source_fields=("memo",),
        kind="event",
        source_predicate_kind="event",
        modality="observed",
    )

    assert matcher._independent_endpoint_role(legacy_memo_action) == "action"
    assert (
        matcher._independent_endpoint_role(ordinary_memo_proposition)
        == "proposition"
    )
