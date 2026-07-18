# -*- coding: utf-8 -*-
from __future__ import annotations

"""RED contract for the rc0027 semantic-feature lexicalization repair.

The assertions intentionally freeze structure, not completed responses.  In
particular, this file never reads the fixture ``semantic_contract`` oracle and
does not prescribe a sentence for any Cycle case.  It verifies that a short
feature phrase can be independently rebound to its exact source owner, and
that the one candidate-wide source anchor remains a bounded typed binding
rather than becoming the visible observation.
"""

from dataclasses import fields, replace
import hashlib
import importlib
from itertools import product
import json
from pathlib import Path
import re
from types import SimpleNamespace
import unicodedata

import pytest

import emlis_ai_step11_hard_gate_v3 as hard_gate
import emlis_ai_step11_natural_surface_matcher_v3 as matcher
import emlis_ai_step11_natural_surface_v3 as surface
import emlis_ai_step11_surface_catalog_v3 as catalog
from emlis_ai_nls_v3_artifact_contract import artifact_sha256
from emlis_ai_step11_runtime_adapter_v3 import execute_step11_offline_v3


_HERE = Path(__file__).resolve().parent
_INFERENCE = _HERE.parent / "services" / "ai_inference"
_FIXTURE = (
    _HERE / "fixtures" / "emlis_nls_v3" / "generated" / "batch_001.jsonl"
)
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
_SELECTOR_FIELD_ORDER = (
    "required_binding_count",
    "required_distinctness_group_count",
    "bound_reception_target_count",
    "section_semantic_replay_count",
    "generic_referent_count",
    "unnecessary_source_anchor_count",
    "redundant_atom_count",
    "depth_deviation",
    "anaphora_distance",
    "candidate_id",
)
_VISIBLE_BOOKKEEPING = (
    "意味特徴",
    "入力片",
    "source_field",
    "source_role",
    "nucleus_kind",
    "semantic_role",
    "semantic_qualifier",
    "temporal_scope",
    "referent_scope",
    "fingerprint",
    "sha256",
    "grounded_phrase",
)
_UNNATURAL_ATOMIC_JOINS = (
    "に表れた伝えられた",
)
_GENERIC_BARE_HEADS = frozenset(
    {"出来事", "状態", "明示された内容", "制約", "大切さ"}
)
_ANCHOR_BINDING_FAMILIES = {
    "reported_profile": "に表れている",
    "action_lifecycle": "として示された",
    "relation_shift": "を起点にした",
}
_COLLISION_FEATURE_AXES = (
    "label_strength",
    "semantic_qualifier",
    "source_field",
    "referent_scope",
)
_FINAL_CATALOG_SHA256 = (
    "1beec18839ed77abd1e52b0a06eb60c5867223fd54183c251a8f0efbc37ccc08"
)
_PRODUCTION_OWNER_PATHS = (
    _INFERENCE / "emlis_ai_step11_grounded_lexicalization_v3.py",
    _INFERENCE / "emlis_ai_step11_surface_catalog_v3.py",
    _INFERENCE / "emlis_ai_step11_natural_surface_v3.py",
    _INFERENCE / "emlis_ai_step11_natural_surface_matcher_v3.py",
    _INFERENCE / "emlis_ai_step11_hard_gate_v3.py",
    _INFERENCE / "emlis_ai_step11_semantic_overlay_v3.py",
    _INFERENCE / "emlis_ai_step11_planning_frontier_v3.py",
)
_CORPUS_CASE_RE = re.compile(r"nls3s_b[0-9]+_[0-9]+")
_FORBIDDEN_PRODUCTION_CUES = (
    "case_id",
    "batch_001",
    "cycle_001",
    "semantic_contract",
    "known28",
    "development42",
    "invalid16",
)
_ANCHOR_GRAMMAR_RE = re.compile(r"「([^」]{2,16})」")


def _lexicalizer():
    try:
        return importlib.import_module(
            "emlis_ai_step11_grounded_lexicalization_v3"
        )
    except ModuleNotFoundError:
        pytest.fail(
            "rc0027 grounded lexicalization owner is not implemented",
            pytrace=False,
        )


def _representative_inputs() -> dict[str, dict[str, object]]:
    rows: dict[str, dict[str, object]] = {}
    for line in _FIXTURE.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        case_id = str(row.get("case_id", ""))
        if case_id in _REPRESENTATIVE_CASE_IDS:
            # Production receives only the app input.  The fixture's coverage
            # labels and semantic oracle are deliberately not returned.
            rows[case_id] = dict(row["input"])
    assert set(rows) == set(_REPRESENTATIVE_CASE_IDS)
    return rows


def _source(
    source_id: str,
    *,
    field: str = "memo",
    kind: str = "state",
    polarity: str = "negative",
    modality: str = "reported",
    temporal_scope: str = "current_input",
    referent_scope: str = "state",
    source_attribute_codes: tuple[str, ...] = (),
) -> SimpleNamespace:
    """Create a body-free semantic source, never a response fixture."""

    return SimpleNamespace(
        source_id=source_id,
        source_fields=(field,),
        source_role="current_input_semantic_nucleus",
        kind=kind,
        source_predicate_kind=kind,
        source_actor="self",
        source_degree="unspecified",
        source_attribute_codes=source_attribute_codes,
        source_meaning_block_keys=(),
        polarity=polarity,
        modality=modality,
        temporal_scope=temporal_scope,
        referent_scope=referent_scope,
        required=True,
    )


def _clause(nucleus_id: str, ordinal: int) -> SimpleNamespace:
    return SimpleNamespace(
        obligation_id=f"obl_generic_{ordinal}",
        source_nucleus_ids=(nucleus_id,),
    )


def _fragment(
    nucleus_id: str,
    text: str,
    ordinal: int,
    *,
    fragment_role: str = "nucleus",
    source_role: str = "reported_state",
    label_strength: str | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        source_slot="thought",
        source_start=ordinal * 32,
        source_end=ordinal * 32 + len(text),
        source_anchor_id=f"anchor_generic_{ordinal}",
        source_nucleus_ids=(nucleus_id,),
        fragment_role=fragment_role,
        source_role=source_role,
        label_strength=label_strength,
        text=text,
    )


def _collision_specs(lexicalizer, count: int):
    sources = tuple(_source(f"nucleus:generic:{index}") for index in range(count))
    specs = lexicalizer.build_step11_grounded_phrase_specs(
        SimpleNamespace(nuclei=sources),
        tuple(_clause(row.source_id, index) for index, row in enumerate(sources)),
    )
    assert len(specs) == count
    assert len({row.phrase_text for row in specs}) == 1
    assert len({row.visible_feature_fingerprint_sha256 for row in specs}) == 1
    # A feature fingerprint may collide by design.  The typed AST identities
    # remain owner-exact and therefore may not collide.
    assert len({row.grounded_phrase_id for row in specs}) == count
    return sources, specs


def _match(execution, witness):
    candidate = execution.selected_candidate
    assert candidate is not None
    return matcher.match_step11_natural_surface(
        witness,
        inventory_result=execution.inventory_result,
        content_plan=execution.content_plan,
        discourse_plan=candidate.discourse_plan,
        current_input=execution.projected_current_input,
    )


def _assert_mutated_body_rejected(
    execution,
    body: bytes,
    *,
    issue_terms: tuple[str, ...],
) -> None:
    try:
        witness = matcher.parse_step11_natural_surface(body)
    except matcher.Step11InverseSurfaceError:
        return
    binding = _match(execution, witness)
    assert binding.verified is False
    assert any(
        any(term in issue for term in issue_terms)
        for issue in binding.issue_codes
    ), binding.issue_codes


@pytest.fixture(scope="module")
def representative_executions():
    inputs = _representative_inputs()
    return {
        case_id: execute_step11_offline_v3(
            inputs[case_id],
            candidate_version_id=surface.STEP11_CANDIDATE_VERSION_ID,
            source_dependency_closure_sha256="b" * 64,
        )
        for case_id in _REPRESENTATIVE_CASE_IDS
    }


def test_rc0027_grounded_owner_exports_typed_forward_contract() -> None:
    lexicalizer = _lexicalizer()
    assert lexicalizer.STEP11_GROUNDED_LEXICALIZATION_SCHEMA.endswith(
        ".rc0027.v2"
    )
    assert surface.STEP11_SURFACE_AST_SCHEMA.endswith(".v10")
    assert surface.STEP11_RENDERED_SURFACE_SCHEMA.endswith(".v10")
    assert surface.STEP11_CANDIDATE_SCHEMA.endswith(".v10")
    assert hasattr(lexicalizer, "Step11GroundedPhraseSpec")
    assert hasattr(lexicalizer, "Step11VisibleSourceAnchorUse")
    phrase_fields = {
        row.name for row in fields(lexicalizer.Step11GroundedPhraseSpec)
    }
    assert {"phrase_profile_id", "anchor_risk_rank"} <= phrase_fields
    assert callable(lexicalizer.build_step11_grounded_phrase_specs)
    assert callable(lexicalizer.select_step11_visible_source_anchor_use)
    assert callable(lexicalizer.render_step11_grounded_phrase)
    assert catalog.STEP11_SURFACE_CATALOG_SHA256 == _FINAL_CATALOG_SHA256
    assert catalog.FROZEN_STEP11_SURFACE_CATALOG_SHA256 == _FINAL_CATALOG_SHA256
    profiles = catalog.STEP11_SURFACE_CATALOG["grounded_lexicalization"][
        "phrase_profile_registry"
    ]["profiles"]
    assert len(profiles) == 42


def test_rc0027_unique_feature_phrases_are_anchorless_and_owner_exact() -> None:
    lexicalizer = _lexicalizer()
    sources = (
        _source("nucleus:thought:1"),
        _source(
            "nucleus:action:1",
            field="memo_action",
            kind="action",
            polarity="neutral",
            modality="intended",
            referent_scope="action",
            source_attribute_codes=("semantic_role:concrete_action",),
        ),
    )
    clauses = tuple(
        _clause(source.source_id, index)
        for index, source in enumerate(sources)
    )
    specs = lexicalizer.build_step11_grounded_phrase_specs(
        SimpleNamespace(nuclei=sources), clauses
    )
    assert len(specs) == 2
    assert len({row.grounded_phrase_id for row in specs}) == 2
    assert len({row.visible_feature_fingerprint_sha256 for row in specs}) == 2
    assert {
        nucleus_id
        for row in specs
        for nucleus_id in row.owner_nucleus_ids
    } == {row.source_id for row in sources}
    assert lexicalizer.select_step11_visible_source_anchor_use(specs, ()) is None
    for spec in specs:
        assert lexicalizer.render_step11_grounded_phrase(spec) == spec.phrase_text
        assert not any(token in spec.phrase_text for token in _VISIBLE_BOOKKEEPING)
        assert "「" not in spec.phrase_text and "」" not in spec.phrase_text


def test_rc0027_candidate_primary_anchor_prefers_concrete_action_evidence() -> None:
    lexicalizer = _lexicalizer()
    sources = (
        _source("nucleus:thought:primary"),
        _source(
            "nucleus:action:primary",
            field="memo_action",
            kind="action",
            polarity="neutral",
            referent_scope="action",
            source_attribute_codes=("semantic_role:concrete_action_evidence",),
        ),
    )
    specs = lexicalizer.build_step11_grounded_phrase_specs(
        SimpleNamespace(nuclei=sources),
        tuple(
            _clause(source.source_id, index)
            for index, source in enumerate(sources)
        ),
    )
    fragments = (
        _fragment(sources[0].source_id, "先が気になる", 0),
        _fragment(
            sources[1].source_id,
            "確認を一項目だけ試した",
            1,
            source_role="concrete_action_evidence",
        ),
    )
    anchor = lexicalizer.select_step11_visible_source_anchor_use(
        specs,
        fragments,
        preferred_owner_nucleus_ids=(sources[1].source_id,),
        require_input_specific_binding=True,
    )
    assert anchor is not None
    assert anchor.owner_nucleus_id == sources[1].source_id
    assert anchor.anchor_text in fragments[1].text
    assert anchor.reason_code == "INPUT_SPECIFIC_BINDING_REQUIRED"


@pytest.mark.parametrize("relation_kind", ("event", "state"))
def test_rc0027_input_specific_relation_owner_precedes_concrete_action_anchor(
    relation_kind: str,
) -> None:
    """The residual-loss order gives a relation owner the sole anchor."""

    lexicalizer = _lexicalizer()
    relation_owner = _source(
        f"nucleus:relation:{relation_kind}",
        kind=relation_kind,
        polarity="neutral",
        modality="observed",
        referent_scope="relation",
        source_attribute_codes=("semantic_role:other_explicit_relation",),
    )
    action_owner = _source(
        "nucleus:action:concrete",
        field="memo_action",
        kind="action",
        polarity="neutral",
        modality="intended",
        referent_scope="action",
        source_attribute_codes=("semantic_role:concrete_action_evidence",),
    )
    sources = (action_owner, relation_owner)
    specs = lexicalizer.build_step11_grounded_phrase_specs(
        SimpleNamespace(nuclei=sources),
        tuple(
            _clause(source.source_id, index)
            for index, source in enumerate(sources)
        ),
    )
    fragments = (
        _fragment(
            action_owner.source_id,
            "確認を一項目だけ試した",
            0,
            source_role="concrete_action_evidence",
        ),
        _fragment(
            relation_owner.source_id,
            "前提と結果の間に残る違い",
            1,
            source_role="other_explicit_relation",
        ),
    )

    anchor = lexicalizer.select_step11_visible_source_anchor_use(
        specs,
        fragments,
        # This is the residual-information-loss order produced by the common
        # Surface owner, not candidate enumeration or a selector score.
        preferred_owner_nucleus_ids=(
            relation_owner.source_id,
            action_owner.source_id,
        ),
        require_input_specific_binding=True,
    )

    assert anchor is not None
    assert anchor.owner_nucleus_id == relation_owner.source_id
    assert anchor.anchor_text in fragments[1].text


def test_rc0027_primary_anchor_uses_an_exact_safe_segment_not_punctuation() -> None:
    lexicalizer = _lexicalizer()
    source = _source("nucleus:thought:safe-segment")
    specs = lexicalizer.build_step11_grounded_phrase_specs(
        SimpleNamespace(nuclei=(source,)),
        (_clause(source.source_id, 1),),
    )
    fragment = _fragment(
        source.source_id,
        "なんとなく、落ち着かない。",
        3,
    )
    anchor = lexicalizer.select_step11_visible_source_anchor_use(
        specs, (fragment,), require_input_specific_binding=True
    )
    assert anchor is not None
    assert 2 <= len(anchor.anchor_text) <= 16
    assert anchor.anchor_text == "落ち着かない"
    assert anchor.anchor_text in fragment.text
    local_start = anchor.source_start - fragment.source_start
    local_end = anchor.source_end - fragment.source_start
    assert fragment.text[local_start:local_end] == anchor.anchor_text
    assert re.search(r"[、。，．！？!?,.;:()「」]", anchor.anchor_text) is None


@pytest.mark.parametrize(
    "source_text",
    (
        "今日はゆっくり人との新しいつながりを育てたい",
        "今も理由を考え続けているが分からないままだ",
        "静かになると考えがまた頭の中で止まらない",
        "時間をかけて少しずつ自分を取り戻したい",
        "今の自分自身にとって大切なことを書き出した",
    ),
)
def test_rc0027_long_unpunctuated_run_has_no_subrange_authority(
    source_text: str,
) -> None:
    """No 16-scalar prefix, particle cut, or other subrange is authoritative."""

    assert len(source_text) > 16
    lexicalizer = _lexicalizer()
    source = _source("nucleus:anchor:long-safe-clause")
    specs = lexicalizer.build_step11_grounded_phrase_specs(
        SimpleNamespace(nuclei=(source,)),
        (_clause(source.source_id, 1),),
    )
    fragment = _fragment(source.source_id, source_text, 0)

    assert lexicalizer.step11_safe_anchor_segments(fragment) == ()
    assert matcher._step11_inverse_safe_anchor_segments(source_text, 16) == ()
    assert hard_gate._step11_gate_safe_anchor_segments(source_text, 16) == ()
    with pytest.raises(
        lexicalizer.Step11GroundedLexicalizationError,
        match="STEP11_INPUT_SPECIFIC_ANCHOR_UNRESOLVED",
    ):
        lexicalizer.select_step11_visible_source_anchor_use(
            specs,
            (fragment,),
            require_input_specific_binding=True,
        )


def test_rc0027_punctuation_delimited_complete_run_keeps_anchor_authority() -> None:
    lexicalizer = _lexicalizer()
    source = _source("nucleus:anchor:punctuation-run")
    specs = lexicalizer.build_step11_grounded_phrase_specs(
        SimpleNamespace(nuclei=(source,)),
        (_clause(source.source_id, 1),),
    )
    source_text = "今日はゆっくり人との新しいつながりを育てたい、落ち着かない。"
    fragment = _fragment(source.source_id, source_text, 0)

    forward = lexicalizer.step11_safe_anchor_segments(fragment)
    inverse = matcher._step11_inverse_safe_anchor_segments(source_text, 16)
    gated = hard_gate._step11_gate_safe_anchor_segments(source_text, 16)

    assert tuple(row[0] for row in forward) == ("落ち着かない",)
    assert tuple(row[0] for row in inverse) == ("落ち着かない",)
    assert tuple(row[0] for row in gated) == ("落ち着かない",)
    anchor = lexicalizer.select_step11_visible_source_anchor_use(
        specs,
        (fragment,),
        require_input_specific_binding=True,
    )
    assert anchor is not None
    assert anchor.anchor_text == "落ち着かない"


def test_rc0027_reaction_profile_does_not_claim_unencoded_modality() -> None:
    lexicalizer = _lexicalizer()
    source = _source("nucleus:reaction:1", kind="reaction")
    (spec,) = lexicalizer.build_step11_grounded_phrase_specs(
        SimpleNamespace(nuclei=(source,)),
        (_clause(source.source_id, 1),),
    )
    fields_by_name = dict(spec.visible_feature_fields)
    assert spec.phrase_profile_id == "reaction_fallback"
    assert fields_by_name == {"nucleus_kind": "reaction"}
    assert "modality" not in fields_by_name
    assert 2 <= len(spec.phrase_text) <= 32
    assert spec.visible_feature_fingerprint_sha256 == artifact_sha256(
        {
            "visible_feature_fields": [
                list(row) for row in spec.visible_feature_fields
            ],
            "phrase_profile_id": spec.phrase_profile_id,
        }
    )


@pytest.mark.parametrize(
    ("kind", "field", "referent_scope", "attribute_codes"),
    (
        ("event", "category", "event", ()),
        ("state", "memo", "state", ()),
        (
            "other_explicit",
            "memo",
            "relation",
            ("semantic_role:other_explicit_relation",),
        ),
        ("constraint", "memo", "state", ("operator:constraint",)),
        ("value", "category", "self", ("operator:value",)),
    ),
)
def test_rc0027_generic_profile_collision_requires_an_extra_visible_axis(
    kind: str,
    field: str,
    referent_scope: str,
    attribute_codes: tuple[str, ...],
) -> None:
    """Generic ontology heads alone are bookkeeping, not a Product Surface."""

    lexicalizer = _lexicalizer()
    sources = (
        _source(
            f"nucleus:profile:{kind}:left",
            field=field,
            kind=kind,
            polarity="neutral",
            modality="observed",
            referent_scope=referent_scope,
            source_attribute_codes=attribute_codes,
        ),
        _source(
            f"nucleus:profile:{kind}:right",
            field="memo_action" if field != "memo_action" else "memo",
            kind=kind,
            polarity="neutral",
            modality="observed",
            referent_scope=referent_scope,
            source_attribute_codes=attribute_codes,
        ),
    )
    specs = lexicalizer.build_step11_grounded_phrase_specs(
        SimpleNamespace(nuclei=sources),
        tuple(_clause(row.source_id, index) for index, row in enumerate(sources)),
    )
    generic_profile_ids = set(
        surface.STEP11_SURFACE_CATALOG["grounded_lexicalization"]
        ["phrase_profile_registry"]["specificity_policy"]
        ["kind_only_generic_profile_ids"]
    )

    assert len(specs) == 2
    assert all(row.phrase_profile_id in generic_profile_ids for row in specs)
    assert len({row.phrase_text for row in specs}) == 2
    for spec in specs:
        fields_by_name = dict(spec.visible_feature_fields)
        assert spec.phrase_text not in _GENERIC_BARE_HEADS
        assert "nucleus_kind" in fields_by_name
        assert any(name != "nucleus_kind" for name in fields_by_name)
        assert 3 <= len(spec.phrase_text) <= 32
        assert not any(token in spec.phrase_text for token in _VISIBLE_BOOKKEEPING)
    assert (
        surface.STEP11_SURFACE_CATALOG["grounded_lexicalization"]
        ["phrase_profile_registry"]["specificity_policy"]
        ["unanchored_required_kind_only_generic"]
        == "fail_closed"
    )


def test_rc0027_one_feature_collision_uses_one_bounded_exact_anchor() -> None:
    lexicalizer = _lexicalizer()
    sources, specs = _collision_specs(lexicalizer, 2)
    fragments = (
        _fragment(sources[0].source_id, "朝の予定", 0),
        _fragment(sources[1].source_id, "夜の予定", 1),
    )
    anchor = lexicalizer.select_step11_visible_source_anchor_use(
        specs, fragments
    )
    assert type(anchor) is lexicalizer.Step11VisibleSourceAnchorUse
    assert anchor.reason_code == "INPUT_SPECIFIC_BINDING_REQUIRED"
    assert 2 <= anchor.scalar_count <= 16
    assert anchor.scalar_count == len(anchor.anchor_text)
    assert anchor.anchor_text == unicodedata.normalize("NFC", anchor.anchor_text)
    assert anchor.source_end - anchor.source_start == anchor.scalar_count
    owner_fragment = next(
        row for row in fragments if row.source_anchor_id == anchor.source_fragment_anchor_id
    )
    assert anchor.source_slot == owner_fragment.source_slot
    assert anchor.source_start == owner_fragment.source_start
    assert anchor.source_end <= owner_fragment.source_end
    assert owner_fragment.text.startswith(anchor.anchor_text)
    assert anchor.anchor_text_sha256 == hashlib.sha256(
        anchor.anchor_text.encode("utf-8")
    ).hexdigest()
    owner_spec = next(
        row for row in specs if anchor.owner_nucleus_id in row.owner_nucleus_ids
    )
    rendered = lexicalizer.render_step11_grounded_phrase(owner_spec, anchor)
    grammar = surface.STEP11_SURFACE_CATALOG["grounded_lexicalization"]
    binding_family = anchor.binding_family
    assert binding_family in grammar["source_anchor_binding_families"]
    assert rendered == (
        grammar["source_anchor_open"]
        + anchor.anchor_text
        + grammar["source_anchor_close"]
        + grammar["source_anchor_binding_families"][binding_family]
        + owner_spec.phrase_text
    )
    assert not any(token in rendered for token in _UNNATURAL_ATOMIC_JOINS)


def test_rc0027_selected_label_can_supply_the_sole_collision_anchor() -> None:
    lexicalizer = _lexicalizer()
    sources, specs = _collision_specs(lexicalizer, 2)
    fragments = (
        _fragment(
            sources[0].source_id,
            "悲しみ",
            0,
            fragment_role="label",
        ),
        _fragment(
            sources[1].source_id,
            "不安",
            1,
            fragment_role="label",
        ),
    )
    anchor = lexicalizer.select_step11_visible_source_anchor_use(
        specs, fragments
    )
    assert anchor is not None
    assert anchor.source_fragment_anchor_id in {
        row.source_anchor_id for row in fragments
    }
    assert anchor.anchor_text in {"悲しみ", "不安"}
    assert anchor.reason_code == "INPUT_SPECIFIC_BINDING_REQUIRED"
    assert anchor.source_end - anchor.source_start == len(anchor.anchor_text)
    assert anchor.anchor_text_sha256 == hashlib.sha256(
        anchor.anchor_text.encode("utf-8")
    ).hexdigest()


def test_rc0027_source_backed_strength_resolves_emotion_feature_collision() -> None:
    lexicalizer = _lexicalizer()
    sources = (
        _source("nucleus:emotion:weak", field="emotions", kind="reaction"),
        _source("nucleus:emotion:strong", field="emotions", kind="reaction"),
    )
    specs = lexicalizer.build_step11_grounded_phrase_specs(
        SimpleNamespace(nuclei=sources),
        tuple(
            _clause(source.source_id, index)
            for index, source in enumerate(sources)
        ),
        additional_visible_feature_values={
            sources[0].source_id: {"label_strength": "weak"},
            sources[1].source_id: {"label_strength": "strong"},
        },
    )
    assert len({row.phrase_text for row in specs}) == 2
    assert {
        dict(row.visible_feature_fields)["label_strength"] for row in specs
    } == {"weak", "strong"}
    assert all(len(row.phrase_text) <= 32 for row in specs)


def test_rc0027_double_collision_fails_closed_without_partial_anchor() -> None:
    lexicalizer = _lexicalizer()
    sources, specs = _collision_specs(lexicalizer, 3)
    fragments = tuple(
        _fragment(source.source_id, f"固有部分{index}", index)
        for index, source in enumerate(sources)
    )
    with pytest.raises(
        lexicalizer.Step11GroundedLexicalizationError,
        match="STEP11_GROUNDED_PHRASE_AMBIGUOUS",
    ):
        lexicalizer.select_step11_visible_source_anchor_use(specs, fragments)


@pytest.mark.parametrize(
    "unsafe_text",
    (
        "一。二",
        "一、二",
        "一：二",
        "一（二）",
        "一「二」",
        "見えたこと",
        "Emlisから",
        "改行\n片",
        "制御\x00片",
        " 余白片",
        "か\u3099片",
    ),
)
def test_rc0027_anchor_rejects_punctuation_brackets_headers_and_non_nfc(
    unsafe_text: str,
) -> None:
    lexicalizer = _lexicalizer()
    sources, specs = _collision_specs(lexicalizer, 2)
    fragments = tuple(
        _fragment(source.source_id, unsafe_text, index)
        for index, source in enumerate(sources)
    )
    with pytest.raises(
        lexicalizer.Step11GroundedLexicalizationError,
        match="STEP11_GROUNDED_PHRASE_AMBIGUOUS",
    ):
        lexicalizer.select_step11_visible_source_anchor_use(specs, fragments)


@pytest.mark.parametrize(
    "unsafe_character",
    (
        "\x00",       # Cc: control
        "\u200b",     # Cf: format
        "\ud800",     # Cs: surrogate
        "\ue000",     # Co: private use
        "\u0378",     # Cn: unassigned
    ),
)
def test_rc0027_forward_rejects_every_unicode_c_category_anchor(
    unsafe_character: str,
) -> None:
    lexicalizer = _lexicalizer()
    source = _source("nucleus:unicode:forward")
    specs = lexicalizer.build_step11_grounded_phrase_specs(
        SimpleNamespace(nuclei=(source,)),
        (_clause(source.source_id, 1),),
    )
    fragment = _fragment(
        source.source_id,
        "安全" + unsafe_character + "な入力片",
        0,
    )

    try:
        anchor = lexicalizer.select_step11_visible_source_anchor_use(
            specs,
            (fragment,),
            require_input_specific_binding=True,
        )
    except lexicalizer.Step11GroundedLexicalizationError:
        return
    assert anchor is not None
    assert all(
        not unicodedata.category(character).startswith("C")
        for character in anchor.anchor_text
    )


@pytest.mark.parametrize(
    "unsafe_text",
    (
        "安全\u202e片",
        "安全\u2066片",
        "安全\u200b片",
        "安全\x01片",
        "安全\ud800片",
        "安全\ue000片",
        "安全\u0378片",
        "か\u3099片",
    ),
)
def test_rc0027_inverse_and_gate_reject_unicode_control_categories(
    unsafe_text: str,
) -> None:
    lexicalizer = _lexicalizer()
    (spec,) = lexicalizer.build_step11_grounded_phrase_specs(
        SimpleNamespace(nuclei=(_source("nucleus:unicode:unsafe"),)),
        (_clause("nucleus:unicode:unsafe", 1),),
    )
    grammar = surface.STEP11_SURFACE_CATALOG["grounded_lexicalization"]
    envelope = (
        grammar["source_anchor_open"]
        + unsafe_text
        + grammar["source_anchor_close"]
        + grammar["source_anchor_binding_families"]["reported_profile"]
        + spec.phrase_text
    )
    assert matcher._step11_inverse_visible_anchor_text_safe(
        unsafe_text, 16
    ) is False
    assert hard_gate._step11_gate_visible_anchor_text_safe(
        unsafe_text, 16
    ) is False
    assert matcher._grounded_phrase_prefixes(envelope, 0) == ()


def test_rc0027_inverse_and_gate_accept_normal_nfc_japanese_anchor() -> None:
    lexicalizer = _lexicalizer()
    (spec,) = lexicalizer.build_step11_grounded_phrase_specs(
        SimpleNamespace(nuclei=(_source("nucleus:unicode:safe"),)),
        (_clause("nucleus:unicode:safe", 1),),
    )
    anchor_text = "落ち着かない"
    grammar = surface.STEP11_SURFACE_CATALOG["grounded_lexicalization"]
    envelope = (
        grammar["source_anchor_open"]
        + anchor_text
        + grammar["source_anchor_close"]
        + grammar["source_anchor_binding_families"]["reported_profile"]
        + spec.phrase_text
    )
    assert matcher._step11_inverse_visible_anchor_text_safe(
        anchor_text, 16
    ) is True
    assert hard_gate._step11_gate_visible_anchor_text_safe(
        anchor_text, 16
    ) is True
    parsed = matcher._grounded_phrase_prefixes(envelope, 0)
    assert len(parsed) == 1
    phrase, end = parsed[0]
    assert end == len(envelope)
    assert phrase.anchor_text == anchor_text


def test_rc0027_anchor_binding_catalog_has_three_typed_families() -> None:
    lexicalizer = _lexicalizer()
    grammar = surface.STEP11_SURFACE_CATALOG["grounded_lexicalization"]
    bindings = grammar["source_anchor_binding_families"]

    assert "source_anchor_binding" not in grammar
    assert type(bindings) is dict
    assert bindings == _ANCHOR_BINDING_FAMILIES
    assert len(set(bindings.values())) == len(bindings)
    assert all(
        type(value) is str
        and value
        and "「" not in value
        and "」" not in value
        for value in bindings.values()
    )
    anchor_fields = {row.name for row in fields(
        lexicalizer.Step11VisibleSourceAnchorUse
    )}
    assert "binding_family" in anchor_fields


def test_rc0027_all_42_bare_profiles_round_trip_with_recomputed_fingerprint() -> None:
    grammar = surface.STEP11_SURFACE_CATALOG["grounded_lexicalization"]
    profiles = grammar["phrase_profile_registry"]["profiles"]

    assert len(profiles) == 42
    for profile in profiles:
        parsed = tuple(
            phrase
            for phrase, end in matcher._grounded_phrase_prefixes(
                profile["noun_phrase"], 0
            )
            if end == len(profile["noun_phrase"])
        )
        assert len(parsed) == 1, profile["profile_id"]
        (phrase,) = parsed
        assert phrase.phrase_profile_id == profile["profile_id"]
        assert phrase.anchor_risk_rank == profile["anchor_risk_rank"]
        assert phrase.binding_family is None
        assert phrase.anchor_text is None
        assert phrase.visible_feature_fingerprint_sha256 == artifact_sha256(
            {
                "visible_feature_fields": [
                    list(row) for row in phrase.visible_feature_fields
                ],
                "phrase_profile_id": phrase.phrase_profile_id,
            }
        )
        fields_by_name = dict(phrase.visible_feature_fields)
        assert fields_by_name["nucleus_kind"] in profile["match"][
            "nucleus_kinds"
        ]
        if fields_by_name["nucleus_kind"] == "action":
            assert phrase.action_lifecycle in profile["match"]["lifecycles"]
        else:
            assert phrase.action_lifecycle == "not_applicable"


def test_rc0027_collision_four_axis_full_product_is_statically_injective() -> None:
    grammar = surface.STEP11_SURFACE_CATALOG["grounded_lexicalization"]
    token_maps = grammar["feature_tokens"]
    profiles = grammar["phrase_profile_registry"]["profiles"]
    render_owner: dict[str, tuple[str, tuple[tuple[str, str], ...]]] = {}

    for profile in profiles:
        options_by_axis = []
        for axis in _COLLISION_FEATURE_AXES:
            if axis in profile["visible_feature_names"]:
                options_by_axis.append((("", ""),))
                continue
            options_by_axis.append(
                (("", ""),)
                + tuple(
                    (value, token)
                    for value, token in token_maps[axis].items()
                    if token
                )
            )
        for selected in product(*options_by_axis):
            explicit = tuple(
                (axis, value)
                for axis, (value, token) in zip(
                    _COLLISION_FEATURE_AXES, selected, strict=True
                )
                if token
            )
            phrase_text = "".join(token for _value, token in selected) + profile[
                "noun_phrase"
            ]
            semantic_key = (profile["profile_id"], explicit)
            previous = render_owner.setdefault(phrase_text, semantic_key)
            assert previous == semantic_key, (phrase_text, previous, semantic_key)


def test_rc0027_visible_singleton_to_multi_mutation_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profiles = surface.STEP11_SURFACE_CATALOG["grounded_lexicalization"][
        "phrase_profile_registry"
    ]["profiles"]
    profile = next(
        row for row in profiles if row["profile_id"] == "reaction_positive"
    )
    monkeypatch.setitem(
        profile["match"], "polarities", ["positive", "negative"]
    )

    assert "STEP11_GROUNDED_LEXICALIZATION_CATALOG_INVALID" in (
        catalog.validate_step11_surface_catalog()
    )
    with pytest.raises(
        matcher.Step11InverseSurfaceError,
        match="S11_PARSE_GROUNDED_PROFILE_VISIBLE_NONINJECTIVE",
    ):
        matcher._grounded_lexicalization_contract()


def test_rc0027_anchor_family_is_owner_feature_stable_under_argument_order() -> None:
    lexicalizer = _lexicalizer()
    sources = (
        _source("nucleus:stable:state", polarity="neutral", modality="observed"),
        _source(
            "nucleus:stable:action",
            field="memo_action",
            kind="action",
            polarity="neutral",
            modality="intended",
            referent_scope="action",
            source_attribute_codes=("semantic_role:concrete_action_evidence",),
        ),
    )
    specs = lexicalizer.build_step11_grounded_phrase_specs(
        SimpleNamespace(nuclei=sources),
        tuple(_clause(row.source_id, index) for index, row in enumerate(sources)),
    )
    fragments = (
        _fragment(sources[0].source_id, "状況の変化を確かめた", 0),
        _fragment(
            sources[1].source_id,
            "確認を一項目だけ試した",
            1,
            source_role="concrete_action_evidence",
        ),
    )
    kwargs = {
        "preferred_owner_nucleus_ids": (sources[1].source_id,),
        "require_input_specific_binding": True,
    }

    forward = lexicalizer.select_step11_visible_source_anchor_use(
        specs, fragments, **kwargs
    )
    reversed_order = lexicalizer.select_step11_visible_source_anchor_use(
        tuple(reversed(specs)), tuple(reversed(fragments)), **kwargs
    )

    assert forward is not None and reversed_order is not None
    assert (
        forward.owner_nucleus_id,
        forward.anchor_text,
        forward.binding_family,
    ) == (
        reversed_order.owner_nucleus_id,
        reversed_order.anchor_text,
        reversed_order.binding_family,
    )


def test_rc0027_anchor_tamper_is_rejected_before_render() -> None:
    lexicalizer = _lexicalizer()
    sources, specs = _collision_specs(lexicalizer, 2)
    fragments = (
        _fragment(sources[0].source_id, "朝の予定", 0),
        _fragment(sources[1].source_id, "夜の予定", 1),
    )
    anchor = lexicalizer.select_step11_visible_source_anchor_use(specs, fragments)
    assert anchor is not None
    owner_spec = next(
        row for row in specs if anchor.owner_nucleus_id in row.owner_nucleus_ids
    )
    tampered = replace(anchor, anchor_text="改変部分")
    with pytest.raises(lexicalizer.Step11GroundedLexicalizationError):
        lexicalizer.render_step11_grounded_phrase(owner_spec, tampered)


def test_rc0027_anchor_is_singular_and_cannot_replay_on_another_owner() -> None:
    lexicalizer = _lexicalizer()
    sources, specs = _collision_specs(lexicalizer, 2)
    fragments = (
        _fragment(sources[0].source_id, "朝の予定", 0),
        _fragment(sources[1].source_id, "夜の予定", 1),
    )
    anchor = lexicalizer.select_step11_visible_source_anchor_use(specs, fragments)
    assert anchor is not None
    owner = next(
        row for row in specs if anchor.owner_nucleus_id in row.owner_nucleus_ids
    )
    other = next(row for row in specs if row is not owner)
    assert len(_ANCHOR_GRAMMAR_RE.findall(
        lexicalizer.render_step11_grounded_phrase(owner, anchor)
    )) == 1
    with pytest.raises(
        lexicalizer.Step11GroundedLexicalizationError,
        match="STEP11_VISIBLE_SOURCE_ANCHOR_INVALID",
    ):
        lexicalizer.render_step11_grounded_phrase(other, anchor)
    ast_field = next(
        row
        for row in fields(surface.Step11NaturalSurfaceAst)
        if row.name == "visible_source_anchor_use"
    )
    assert "tuple" not in str(ast_field.type).lower()
    assert "Sequence" not in str(ast_field.type)


def test_rc0027_inverse_contract_has_grounded_types_and_named_selector() -> None:
    assert hasattr(matcher, "Step11ParsedGroundedPhrase")
    assert hasattr(matcher, "Step11GroundedPhraseBinding")
    assert hasattr(matcher, "Step11SelectorAttributes")
    assert tuple(matcher.Step11SelectorAttributes._fields) == (
        _SELECTOR_FIELD_ORDER
    )

    gate_fields = {row.name: row for row in fields(matcher.Step11HardGateResult)}
    assert "selector_attributes" in gate_fields
    assert "Step11SelectorAttributes" in str(
        gate_fields["selector_attributes"].type
    )


def test_rc0027_production_is_fixture_and_case_cue_free() -> None:
    missing = [path.name for path in _PRODUCTION_OWNER_PATHS if not path.is_file()]
    assert missing == []
    for path in _PRODUCTION_OWNER_PATHS:
        source_text = path.read_text(encoding="utf-8")
        assert _CORPUS_CASE_RE.search(source_text) is None, path.name
        assert all(
            cue not in source_text for cue in _FORBIDDEN_PRODUCTION_CUES
        ), path.name


def test_rc0027_visible_body_has_no_bookkeeping_or_broken_atomic_join(
    representative_executions,
) -> None:
    violations: list[tuple[str, str]] = []
    for case_id, execution in representative_executions.items():
        assert execution.status == "selected", case_id
        assert execution.final_utf8_bytes is not None, case_id
        body = execution.final_utf8_bytes.decode("utf-8")
        violations.extend(
            (case_id, token)
            for token in (*_VISIBLE_BOOKKEEPING, *_UNNATURAL_ATOMIC_JOINS)
            if token in body
        )
    assert violations == []


def test_rc0027_representative_phrases_bind_exact_source_owners(
    representative_executions,
) -> None:
    for case_id, execution in representative_executions.items():
        candidate = execution.selected_candidate
        assert candidate is not None, case_id
        ast = candidate.surface_ast
        specs = ast.grounded_phrase_specs
        assert specs, case_id
        active_nucleus_ids = {
            nucleus_id
            for sentence in ast.sentences
            for clause in sentence.clauses
            for nucleus_id in clause.source_nucleus_ids
        }
        source_by_id = {
            row.source_id: row
            for row in execution.inventory_result.source_snapshot.nuclei
        }
        spec_owner_nucleus_ids = {
            nucleus_id
            for spec in specs
            for nucleus_id in spec.owner_nucleus_ids
        }
        # Render-reachable source-boundary companions may be integrated
        # without owning a discourse clause.  Clause owners are mandatory;
        # every additional spec must still resolve to the frozen snapshot.
        assert active_nucleus_ids <= spec_owner_nucleus_ids
        assert spec_owner_nucleus_ids <= set(source_by_id)
        assert len({row.grounded_phrase_id for row in specs}) == len(specs)
        for spec in specs:
            assert len(spec.owner_nucleus_ids) == 1
            assert spec.owner_obligation_ids
            assert 2 <= len(spec.phrase_text) <= 32
            assert spec.visible_feature_fingerprint_sha256 == artifact_sha256(
                {
                    "visible_feature_fields": [
                        list(row) for row in spec.visible_feature_fields
                    ],
                    "phrase_profile_id": spec.phrase_profile_id,
                }
            )
            owner = source_by_id[spec.owner_nucleus_ids[0]]
            fields_by_name = dict(spec.visible_feature_fields)
            direct_values = {"polarity": owner.polarity,
                             "referent_scope": owner.referent_scope,
                             "nucleus_kind": owner.kind}
            assert all(
                name not in fields_by_name or fields_by_name[name] == value
                for name, value in direct_values.items()
            )
            if owner.kind == "action" and "action_lifecycle" in fields_by_name:
                projection = surface.STEP11_SURFACE_CATALOG[
                    "grounded_lexicalization"
                ]["lifecycle_authority_policy"]["action_projection"][
                    fields_by_name["action_lifecycle"]
                ]
                assert all(
                    name not in fields_by_name
                    or fields_by_name[name] == projection[name]
                    for name in ("modality", "temporal_scope")
                )
            if (
                ast.visible_source_anchor_use is None
                or ast.visible_source_anchor_use.owner_nucleus_id
                not in spec.owner_nucleus_ids
            ):
                assert spec.phrase_text in candidate.final_utf8_bytes.decode(
                    "utf-8"
                )

        anchor = ast.visible_source_anchor_use
        assert type(anchor).__name__ == "Step11VisibleSourceAnchorUse"
        assert sum(
            anchor.owner_nucleus_id in spec.owner_nucleus_ids
            for spec in specs
        ) == 1

        witness = matcher.parse_step11_natural_surface(
            candidate.final_utf8_bytes
        )
        parsed_phrases = tuple(
            phrase
            for atom in witness.atoms
            for phrase in atom.grounded_phrases
        )
        assert parsed_phrases, case_id
        spec_keys = {
            (
                row.visible_feature_fields,
                row.visible_feature_fingerprint_sha256,
                row.phrase_profile_id,
                row.anchor_risk_rank,
            )
            for row in specs
        }
        assert all(
            (
                row.visible_feature_fields,
                row.visible_feature_fingerprint_sha256,
                row.phrase_profile_id,
                row.anchor_risk_rank,
            )
            in spec_keys
            for row in parsed_phrases
        )
        binding = matcher.match_step11_natural_surface(
            witness,
            inventory_result=execution.inventory_result,
            content_plan=execution.content_plan,
            discourse_plan=candidate.discourse_plan,
            current_input=execution.projected_current_input,
        )
        assert binding.verified is True, (case_id, binding.issue_codes)
        assert binding.grounded_phrase_bindings, case_id
        assert all(
            row.match_candidate_count == 1
            and row.owner_nucleus_ids
            and row.owner_obligation_ids
            for row in binding.grounded_phrase_bindings
        ), case_id


def test_rc0027_representative_raw_text_is_not_the_observation(
    representative_executions,
) -> None:
    for case_id, execution in representative_executions.items():
        body = execution.final_utf8_bytes
        assert body is not None, case_id
        text = body.decode("utf-8")
        for source_text in (
            execution.projected_current_input["thought_text"],
            execution.projected_current_input["action_text"],
        ):
            normalized = " ".join(str(source_text).split())
            if len(normalized) > 16:
                assert normalized not in text, (case_id, normalized)
        anchors = _ANCHOR_GRAMMAR_RE.findall(text)
        assert len(anchors) == 1, case_id
        quoted = re.findall(r"[「『]([^」』]+)[」』]", text)
        assert quoted == anchors, (case_id, quoted)


def test_rc0027_phrase_token_mutation_fails_inverse_binding(
    representative_executions,
) -> None:
    execution = next(iter(representative_executions.values()))
    body = execution.final_utf8_bytes
    assert body is not None
    witness = matcher.parse_step11_natural_surface(body)
    phrase = next(
        phrase for atom in witness.atoms for phrase in atom.grounded_phrases
    )
    mutated = b"".join(
        (
            body[: phrase.byte_start],
            "一般的なこと".encode("utf-8"),
            body[phrase.byte_end :],
        )
    )
    _assert_mutated_body_rejected(
        execution,
        mutated,
        issue_terms=("GROUNDED_PHRASE", "EVIDENCE", "REQUIRED"),
    )


def test_rc0027_unknown_deletion_fails_independent_matcher(
    representative_executions,
) -> None:
    selected = None
    for execution in representative_executions.values():
        body = execution.final_utf8_bytes
        assert body is not None
        witness = matcher.parse_step11_natural_surface(body)
        for atom_index, atom in enumerate(witness.atoms):
            if (
                "unknown_boundary" in atom.claim_kinds
                or atom.unknown_dimension_class is not None
            ):
                selected = (execution, witness, atom_index, atom)
                break
        if selected is not None:
            break
    assert selected is not None
    execution, witness, atom_index, atom = selected
    without_unknown = replace(
        atom,
        claim_kinds=tuple(
            row for row in atom.claim_kinds if row != "unknown_boundary"
        ),
        unknown_dimension_class=None,
    )
    mutated_atoms = list(witness.atoms)
    mutated_atoms[atom_index] = without_unknown
    binding = _match(execution, replace(witness, atoms=tuple(mutated_atoms)))
    assert binding.verified is False
    assert any("UNKNOWN" in row or "REQUIRED" in row for row in binding.issue_codes)


def test_rc0027_selected_reception_is_specific_and_unreplayed(
    representative_executions,
) -> None:
    for case_id, execution in representative_executions.items():
        selected_id = execution.selection_result.selected_candidate_id
        result = next(
            row
            for row in execution.selection_result.gate_results
            if row.candidate_id == selected_id
        )
        attributes = result.selector_attributes
        assert attributes.section_semantic_replay_count == 0, case_id
        assert attributes.unnecessary_source_anchor_count == 0, case_id


def test_rc0027_selector_attributes_are_not_an_unnamed_score_tuple(
    representative_executions,
) -> None:
    for case_id, execution in representative_executions.items():
        assert execution.selection_result is not None, case_id
        for result in execution.selection_result.gate_results:
            assert type(result.selector_attributes) is (
                matcher.Step11SelectorAttributes
            ), (case_id, result.candidate_id)
            assert tuple(result.selector_attributes._fields) == (
                _SELECTOR_FIELD_ORDER
            )


def test_rc0027_forward_and_inverse_modules_remain_independent() -> None:
    forward_source = (
        _INFERENCE / "emlis_ai_step11_grounded_lexicalization_v3.py"
    ).read_text(encoding="utf-8")
    inverse_source = (
        _INFERENCE / "emlis_ai_step11_natural_surface_matcher_v3.py"
    ).read_text(encoding="utf-8")
    assert "emlis_ai_step11_natural_surface_matcher_v3" not in forward_source
    assert "emlis_ai_step11_grounded_lexicalization_v3" not in inverse_source
    assert "emlis_ai_step11_natural_surface_v3" not in inverse_source
