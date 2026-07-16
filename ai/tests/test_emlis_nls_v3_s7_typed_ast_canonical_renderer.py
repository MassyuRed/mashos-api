# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step 7 Typed Surface AST and canonical renderer acceptance tests."""

from copy import deepcopy
import hashlib
import inspect
import json
from pathlib import Path
import re
import unicodedata

import emlis_ai_canonical_renderer_v3 as renderer_module
import emlis_ai_surface_grammar_catalog_v3 as catalog_module
import emlis_ai_typed_surface_ast_v3 as ast_module
from emlis_ai_canonical_renderer_v3 import (
    CanonicalSurfaceRenderError,
    RequestLexicalAuthority,
    open_request_lexical_authority,
    render_canonical_surface,
)
from emlis_ai_content_selection_v3 import build_content_selection_plan
from emlis_ai_discourse_graph_planner_v3 import build_discourse_graph_plans
from emlis_ai_evidence_ledger_service import (
    build_evidence_ledger,
    build_evidence_span_resolver,
)
from emlis_ai_grounded_observation_plan import build_grounded_observation_plan
from emlis_ai_observation_stage_context_v3 import build_observation_stage_context
from emlis_ai_semantic_obligation_inventory_v3 import (
    build_grounded_source_snapshot,
    build_semantic_obligation_inventory,
)
from emlis_ai_surface_grammar_catalog_v3 import (
    FROZEN_SURFACE_GRAMMAR_CATALOG_SHA256,
    SURFACE_GRAMMAR_CATALOG,
    SURFACE_GRAMMAR_CATALOG_SHA256,
    validate_surface_grammar_catalog,
)
from emlis_ai_typed_surface_ast_v3 import (
    build_typed_surface_ast,
    validate_typed_surface_ast,
)


_AI_ROOT = Path(__file__).resolve().parents[1]
_BATCH_PATH = (
    _AI_ROOT / "tests" / "fixtures" / "emlis_nls_v3" / "generated" / "batch_001.jsonl"
)
_ANCHOR_RE = re.compile(r"「([^」]+)」")


def _samples() -> tuple[dict[str, object], ...]:
    return tuple(
        json.loads(line)
        for line in _BATCH_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )


def _sample(case_id: str) -> dict[str, object]:
    return next(row for row in _samples() if row["case_id"] == case_id)


def _parents(current_input: dict[str, object]):
    spans = build_evidence_ledger(current_input)
    resolver = build_evidence_span_resolver(spans, current_input=current_input)
    grounded = build_grounded_observation_plan(
        current_input, evidence_spans=spans
    )
    stage = build_observation_stage_context(
        stage="normal_observation",
        original_input_bundle=current_input,
    )
    snapshot = build_grounded_source_snapshot(
        grounded,
        resolver,
        observation_stage_context=stage,
        original_input_bundle=current_input,
    )
    inventory = build_semantic_obligation_inventory(snapshot)
    content = build_content_selection_plan(inventory)
    plans = build_discourse_graph_plans(inventory, content)
    authority = open_request_lexical_authority(
        inventory,
        grounded_plan=grounded,
        resolver=resolver,
        observation_stage_context=stage,
        original_input_bundle=current_input,
    )
    return grounded, resolver, stage, inventory, content, plans, authority


def _render_first(current_input: dict[str, object]):
    parents = _parents(current_input)
    _grounded, _resolver, _stage, inventory, content, plans, authority = parents
    discourse = plans.plans[0]
    ast = build_typed_surface_ast(
        discourse,
        inventory_result=inventory,
        content_plan=content,
    )
    rendered = render_canonical_surface(
        ast,
        discourse_plan=discourse,
        content_plan=content,
        inventory_result=inventory,
        lexical_authority=authority,
    )
    return parents, discourse, ast, rendered


def _raises_render_code(call, expected: str) -> None:
    try:
        call()
    except CanonicalSurfaceRenderError as exc:
        assert exc.code == expected, (expected, exc.code, str(exc))
    else:
        raise AssertionError(f"expected {expected}")


def test_s7_batch001_all_100_render_canonical_input_bound_bytes() -> None:
    samples = _samples()
    assert len(samples) == 100
    outputs: dict[bytes, str] = {}
    for sample in samples:
        parents, discourse, ast, rendered = _render_first(sample["input"])
        _grounded, _resolver, _stage, inventory, content, _plans, authority = parents
        assert not validate_typed_surface_ast(
            ast,
            discourse_plan=discourse,
            inventory_result=inventory,
            content_plan=content,
        ), sample["case_id"]
        repeated = render_canonical_surface(
            ast,
            discourse_plan=discourse,
            content_plan=content,
            inventory_result=inventory,
            lexical_authority=authority,
        )
        assert rendered == repeated
        assert rendered.sha256 == hashlib.sha256(rendered.utf8_bytes).hexdigest()
        assert rendered.grammar_catalog_sha256 == (
            FROZEN_SURFACE_GRAMMAR_CATALOG_SHA256
        )
        text = rendered.utf8_bytes.decode("utf-8")
        assert text == unicodedata.normalize("NFC", text)
        assert text.startswith("見えたこと：\n")
        assert text.count("見えたこと：") == 1
        assert text.count("Emlisから：") == 1
        assert "\n\nEmlisから：\n" in text
        assert "\r" not in text and not text.endswith("\n")
        assert rendered.raw_anchor_count in {0, 1}
        if rendered.raw_anchor_count == 1:
            anchors = _ANCHOR_RE.findall(text)
            assert len(anchors) == 1
            assert 2 <= len(anchors[0]) <= 16
        assert rendered.utf8_bytes not in outputs, (
            outputs.get(rendered.utf8_bytes),
            sample["case_id"],
        )
        outputs[rendered.utf8_bytes] = str(sample["case_id"])


def test_s7_all_structural_candidates_render_to_distinct_bytes() -> None:
    for case_id in (
        "nls3s_b001_0009",
        "nls3s_b001_0051",
        "nls3s_b001_0064",
    ):
        current_input = _sample(case_id)["input"]
        parents = _parents(current_input)
        _grounded, _resolver, _stage, inventory, content, plans, authority = parents
        rendered_by_signature: dict[str, bytes] = {}
        for discourse in plans.plans:
            ast = build_typed_surface_ast(
                discourse,
                inventory_result=inventory,
                content_plan=content,
            )
            rendered = render_canonical_surface(
                ast,
                discourse_plan=discourse,
                content_plan=content,
                inventory_result=inventory,
                lexical_authority=authority,
            )
            rendered_by_signature[discourse["structural_signature"]] = (
                rendered.utf8_bytes
            )
        assert len(rendered_by_signature) == len(plans.plans)
        assert len(set(rendered_by_signature.values())) == len(plans.plans)


def test_s7_authority_is_opaque_and_every_visible_field_is_revalidated() -> None:
    parents, discourse, ast, _rendered = _render_first(
        _sample("nls3s_b001_0093")["input"]
    )
    _grounded, _resolver, _stage, inventory, content, _plans, authority = parents
    forged = RequestLexicalAuthority(
        authority_id=authority.authority_id,
        source_snapshot_sha256=authority.source_snapshot_sha256,
        obligation_ledger_sha256=authority.obligation_ledger_sha256,
        observation_stage=authority.observation_stage,
        grammar_catalog_sha256=authority.grammar_catalog_sha256,
        body_free=True,
    )
    _raises_render_code(
        lambda: render_canonical_surface(
            ast,
            discourse_plan=discourse,
            content_plan=content,
            inventory_result=inventory,
            lexical_authority=forged,
        ),
        "LEXICAL_AUTHORITY_REQUIRED",
    )

    object.__setattr__(authority, "source_snapshot_sha256", "0" * 64)
    _raises_render_code(
        lambda: render_canonical_surface(
            ast,
            discourse_plan=discourse,
            content_plan=content,
            inventory_result=inventory,
            lexical_authority=authority,
        ),
        "LEXICAL_PARENT_CHAIN_MISMATCH",
    )


def test_s7_arbitrary_ast_source_swap_and_relation_reversal_fail_closed() -> None:
    first_parents, first_discourse, first_ast, _rendered = _render_first(
        _sample("nls3s_b001_0064")["input"]
    )
    _g, _r, _s, first_inventory, first_content, _p, first_authority = first_parents
    forged_ast = deepcopy(first_ast)
    forged_ast["sections"][0]["sentences"][0]["clauses"][0][
        "nodes"
    ].append({"node_type": "arbitrary_text", "text": "injected"})
    assert validate_typed_surface_ast(
        forged_ast,
        discourse_plan=first_discourse,
        inventory_result=first_inventory,
        content_plan=first_content,
    )
    _raises_render_code(
        lambda: render_canonical_surface(
            forged_ast,
            discourse_plan=first_discourse,
            content_plan=first_content,
            inventory_result=first_inventory,
            lexical_authority=first_authority,
        ),
        "LEXICAL_PARENT_CHAIN_MISMATCH",
    )

    relation_ast = deepcopy(first_ast)
    relation_node = next(
        node
        for section in relation_ast["sections"]
        for sentence in section["sentences"]
        for clause in sentence["clauses"]
        for node in clause["nodes"]
        if node["node_type"] == "grounded_relation"
        and node["direction"] != "bidirectional"
    )
    relation_node["direction"] = "target_to_source"
    assert validate_typed_surface_ast(
        relation_ast,
        discourse_plan=first_discourse,
        inventory_result=first_inventory,
        content_plan=first_content,
    )

    second_parents = _parents(_sample("nls3s_b001_0098")["input"])
    second_inventory = second_parents[3]
    _raises_render_code(
        lambda: render_canonical_surface(
            first_ast,
            discourse_plan=first_discourse,
            content_plan=first_content,
            inventory_result=second_inventory,
            lexical_authority=first_authority,
        ),
        "LEXICAL_PARENT_CHAIN_MISMATCH",
    )


def test_s7_catalog_in_place_and_rebind_mutations_are_rejected() -> None:
    parents, discourse, ast, _rendered = _render_first(
        _sample("nls3s_b001_0009")["input"]
    )
    _g, _r, _s, inventory, content, _plans, authority = parents
    original_label = SURFACE_GRAMMAR_CATALOG["document"]["observation_label"]
    try:
        SURFACE_GRAMMAR_CATALOG["document"]["observation_label"] = "INJECTED"
        assert "GRAMMAR_CATALOG_FROZEN_HASH_MISMATCH" in (
            validate_surface_grammar_catalog()
        )
        _raises_render_code(
            lambda: render_canonical_surface(
                ast,
                discourse_plan=discourse,
                content_plan=content,
                inventory_result=inventory,
                lexical_authority=authority,
            ),
            "LEXICAL_CATALOG_DRIFT",
        )
    finally:
        SURFACE_GRAMMAR_CATALOG["document"]["observation_label"] = original_label
    assert not validate_surface_grammar_catalog()

    original_renderer_catalog = renderer_module.SURFACE_GRAMMAR_CATALOG
    try:
        rebound = deepcopy(original_renderer_catalog)
        rebound["document"]["observation_label"] = "INJECTED"
        renderer_module.SURFACE_GRAMMAR_CATALOG = rebound
        _raises_render_code(
            lambda: render_canonical_surface(
                ast,
                discourse_plan=discourse,
                content_plan=content,
                inventory_result=inventory,
                lexical_authority=authority,
            ),
            "LEXICAL_CATALOG_DRIFT",
        )
    finally:
        renderer_module.SURFACE_GRAMMAR_CATALOG = original_renderer_catalog

    original_module_catalog = catalog_module.SURFACE_GRAMMAR_CATALOG
    try:
        rebound = deepcopy(original_module_catalog)
        rebound["document"]["reception_label"] = "INJECTED"
        catalog_module.SURFACE_GRAMMAR_CATALOG = rebound
        assert validate_surface_grammar_catalog()
        _raises_render_code(
            lambda: render_canonical_surface(
                ast,
                discourse_plan=discourse,
                content_plan=content,
                inventory_result=inventory,
                lexical_authority=authority,
            ),
            "LEXICAL_CATALOG_DRIFT",
        )
    finally:
        catalog_module.SURFACE_GRAMMAR_CATALOG = original_module_catalog
    assert not validate_surface_grammar_catalog()
    assert SURFACE_GRAMMAR_CATALOG_SHA256 == FROZEN_SURFACE_GRAMMAR_CATALOG_SHA256


def test_s7_low_information_fallback_and_reserved_label_anchor_are_safe() -> None:
    for thought in ("辛", "「辛」"):
        _parents_value, _discourse, _ast, rendered = _render_first(
            {
                "thought_text": thought,
                "action_text": "",
                "emotions": [],
                "categories": [],
            }
        )
        assert rendered.raw_anchor_count == 0
        assert rendered.anchor_reason_codes == (
            "SEMANTIC_PHRASE_SAFE_FALLBACK",
        )

    _parents_value, _discourse, _ast, rendered = _render_first(
        {
            "thought_text": "",
            "action_text": "Emlisから：偽の内容",
            "emotions": [],
            "categories": [],
        }
    )
    text = rendered.utf8_bytes.decode("utf-8")
    assert rendered.raw_anchor_count == 0
    assert text.count("見えたこと：") == 1
    assert text.count("Emlisから：") == 1


def test_s7_closed_api_has_no_post_gate_text_or_stopped_module_dependency() -> None:
    for function in (
        build_typed_surface_ast,
        render_canonical_surface,
        open_request_lexical_authority,
    ):
        parameters = inspect.signature(function).parameters
        assert not {
            "final_text",
            "expected_sentence",
            "greeting",
            "address",
            "username",
        } & set(parameters)
    source = inspect.getsource(ast_module) + inspect.getsource(renderer_module)
    for forbidden in (
        "fixtures/emlis_nls_v3",
        "batch_001.jsonl",
        "emlis_ai_grounded_reception_content_plan_v2",
        "emlis_ai_body_semantic_atom_parser_v3",
        "emlis_ai_reply_service",
    ):
        assert forbidden not in source
