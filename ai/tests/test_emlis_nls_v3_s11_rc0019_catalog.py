# -*- coding: utf-8 -*-
from __future__ import annotations

from emlis_ai_step11_cycle_evidence_v3 import (
    STEP11_CURRENT_CANDIDATE_VERSION_ID,
)
from emlis_ai_step11_surface_catalog_v3 import (
    STEP11_SURFACE_CATALOG,
    validate_step11_surface_catalog,
)


def test_rc0022_catalog_owns_ref_only_relations_and_group_delimiters(
    monkeypatch,
) -> None:
    assert validate_step11_surface_catalog() == ()
    assert STEP11_SURFACE_CATALOG["schema_version"].endswith(".v6")
    assert STEP11_SURFACE_CATALOG["candidate_version_id"] == (
        STEP11_CURRENT_CANDIDATE_VERSION_ID
    )

    group = STEP11_SURFACE_CATALOG["group_grammar"]
    references = STEP11_SURFACE_CATALOG["endpoint_reference_grammar"]
    assert group == {
        "schema_version": (
            "cocolon.emlis.nls_v3.step11_group_grammar.rc0022.v1"
        ),
        "clause_separator": "、また、",
        "sentence_suffix": "。",
        "grammatical_chunk_separator": "。",
        "one_line_per_discourse_sentence_group": True,
        "split_outside_quotes_only": True,
        "clause_stems_exclude_sentence_suffix": True,
        "maximum_observation_clauses_per_sentence": 4,
        "maximum_visible_clauses_per_grammatical_sentence": 2,
        "maximum_grammatical_complexity_load": 4,
        "maximum_repeated_joiner_per_group": 2,
        "maximum_repeated_joiner_per_sentence": 2,
    }
    assert references["reference_token_template"] == (
        "{ordinal}つ目の{role_label}"
    )
    assert references["relation_endpoint_policy"] == "typed_reference_only"
    assert references["direct_introduction"]["literal_owner_policy"] == (
        "exact_source_identity_once"
    )
    direct_stems = references["direct_introduction"]["stems"]
    assert len(direct_stems) >= 4
    assert len(direct_stems) == len(set(direct_stems))
    assert all(
        stem.count("{quoted_literal}") == 1
        and group["clause_separator"] not in stem
        and not stem.endswith(group["sentence_suffix"])
        and "『" not in stem
        and "』" not in stem
        for stem in direct_stems
    )
    assert STEP11_SURFACE_CATALOG[
        "legacy_quoted_relation_forms_rc0018"
    ]["forward_emission"] is False

    relation_rows = tuple(
        row
        for directions in STEP11_SURFACE_CATALOG["relation_forms"].values()
        for from_roles in directions.values()
        for to_roles in from_roles.values()
        for rows in to_roles.values()
        for row in rows
    )
    assert relation_rows
    assert all(
        set(row) == {"stem", "endpoint_realization"}
        and row["endpoint_realization"] == "typed_reference_only"
        and row["stem"].count("{from_ref}") == 1
        and row["stem"].count("{to_ref}") == 1
        and "『" not in row["stem"]
        and "』" not in row["stem"]
        and "{quoted_literal}" not in row["stem"]
        and not row["stem"].endswith(group["sentence_suffix"])
        for row in relation_rows
    )

    first = relation_rows[0]
    monkeypatch.setitem(
        first,
        "stem",
        first["stem"] + group["clause_separator"] + "『再引用』",
    )
    issues = validate_step11_surface_catalog()
    assert "STEP11_SURFACE_CATALOG_RELATION_LITERAL_FORBIDDEN" in issues
    assert "STEP11_SURFACE_CATALOG_GROUP_SEPARATOR_COLLISION" in issues

    monkeypatch.setitem(
        references,
        "reference_token_template",
        "{ordinal}番目",
    )
    assert (
        "STEP11_SURFACE_CATALOG_ENDPOINT_REFERENCE_GRAMMAR_INVALID"
        in validate_step11_surface_catalog()
    )
