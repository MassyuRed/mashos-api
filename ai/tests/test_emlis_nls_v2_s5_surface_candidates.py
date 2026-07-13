# -*- coding: utf-8 -*-
from __future__ import annotations

"""Development-only Step 5 Surface Candidate Generator contract tests."""

import ast
from collections import Counter
from functools import lru_cache
import inspect
import json
from pathlib import Path
import re

from helpers.emlis_nls_v2_s2_development import (
    load_development_cases,
    sha256_file,
    sha256_json,
)
from emlis_ai_evidence_ledger_service import (
    build_evidence_ledger,
    build_evidence_span_resolver,
)
from emlis_ai_grounded_human_reception_v2 import (
    RECEPTION_SURFACE_CANDIDATE_SET_V2_SCHEMA_VERSION,
    RECEPTION_SURFACE_CANDIDATE_V2_SCHEMA_VERSION,
    generate_reception_surface_candidates_v2,
    validate_reception_surface_candidate_set_v2,
    validate_reception_surface_candidate_v2,
)
from emlis_ai_grounded_observation_plan import build_grounded_observation_plan
from emlis_ai_grounded_reception_candidate_plan_v2 import (
    build_reception_candidate_plans_v2,
)
from emlis_ai_grounded_reception_content_plan_v2 import (
    build_reception_content_plan_v2,
)


_TEST_ROOT = Path(__file__).resolve().parent
_AI_ROOT = _TEST_ROOT.parent
_REPO_ROOT = _AI_ROOT.parent
_GENERATOR_PATH = (
    _AI_ROOT
    / "services"
    / "ai_inference"
    / "emlis_ai_grounded_human_reception_v2.py"
)
_SELECTOR_PATH = (
    _AI_ROOT
    / "services"
    / "ai_inference"
    / "emlis_ai_grounded_reception_candidate_selector_v2.py"
)
_REPLY_SERVICE_PATH = (
    _AI_ROOT / "services" / "ai_inference" / "emlis_ai_reply_service.py"
)
_S1_RECEIPT_PATH = (
    _TEST_ROOT / "fixtures" / "emlis_nls_v2_s1_receipt_20260713.json"
)
_QUESTION_RE = re.compile(r"[?？]")
_CAUSAL_CONNECTOR_RE = re.compile(
    r"(?:だから|そのため|ことで|につながっている|として表れている)"
)
_TERMINAL_RE = re.compile(r"(?:います|ません|です)\。$")
_FORBIDDEN_META_KEYS = frozenset(
    {
        "text",
        "surface_text",
        "candidate_text",
        "visible_surface",
        "expected_text",
        "raw_input",
        "raw_text",
        "source_text",
    }
)


@lru_cache(maxsize=1)
def _development_surfaces():
    rows = []
    for case in load_development_cases():
        observation_plan = build_grounded_observation_plan(case.current_input)
        content_plan = build_reception_content_plan_v2(observation_plan)
        candidate_plan_set = build_reception_candidate_plans_v2(content_plan)
        spans = tuple(build_evidence_ledger(case.current_input))
        resolver = build_evidence_span_resolver(
            spans,
            current_input=case.current_input,
        )
        surface_set = generate_reception_surface_candidates_v2(
            observation_plan,
            content_plan,
            candidate_plan_set,
            resolver,
        )
        rows.append(
            (
                case,
                observation_plan,
                content_plan,
                candidate_plan_set,
                resolver,
                surface_set,
            )
        )
    return tuple(rows)


def _walk_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from _walk_keys(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from _walk_keys(child)


def _split_sentences(text: str) -> tuple[str, ...]:
    assert text.endswith("。")
    rows = text.split("。")
    assert rows[-1] == ""
    assert all(row.strip() for row in rows[:-1])
    return tuple(f"{row.strip()}。" for row in rows[:-1])


def test_step5_generates_process_local_candidates_for_development_42() -> None:
    rows = _development_surfaces()
    assert len(rows) == 42
    depth_candidate_counts = Counter()
    classifications = Counter()
    total_candidates = 0
    total_sentences = 0
    for _, _, content_plan, plan_set, _, surface_set in rows:
        assert surface_set.schema_version == (
            RECEPTION_SURFACE_CANDIDATE_SET_V2_SCHEMA_VERSION
        )
        assert validate_reception_surface_candidate_set_v2(
            surface_set,
            plan_set,
        ) == ()
        assert len(surface_set.candidates) == len(plan_set.candidates)
        assert len(surface_set.candidates) > 1
        assert surface_set.process_local_bodies is True
        assert surface_set.selection_performed is False
        assert surface_set.hard_gate_performed is False
        assert surface_set.runtime_connected is False
        depth_candidate_counts[(content_plan.depth, len(surface_set.candidates))] += 1
        classifications[surface_set.v1_comparison_classification] += 1
        total_candidates += len(surface_set.candidates)
        total_sentences += sum(
            candidate.sentence_count for candidate in surface_set.candidates
        )

    assert depth_candidate_counts == {
        ("minimal", 3): 12,
        ("focused", 5): 21,
        ("layered", 8): 9,
    }
    assert classifications == {"v1_distinct_only": 42}
    assert total_candidates == 213
    assert total_sentences == 470


def test_step5_every_sentence_has_structural_japanese_integrity() -> None:
    anchored_candidates = 0
    max_anchor_chars = 0
    for _, observation, content_plan, plan_set, resolver, surface_set in (
        _development_surfaces()
    ):
        reception_plan = observation.response_plan.human_reception_plan
        assert reception_plan is not None
        assert len({item.text for item in surface_set.candidates}) == len(
            surface_set.candidates
        )
        for plan, surface in zip(plan_set.candidates, surface_set.candidates):
            assert surface.schema_version == RECEPTION_SURFACE_CANDIDATE_V2_SCHEMA_VERSION
            assert validate_reception_surface_candidate_v2(
                surface,
                plan,
                content_plan,
                reception_plan,
                resolver,
            ) == ()
            sentences = _split_sentences(surface.text)
            assert len(sentences) == surface.sentence_count
            assert len(sentences) == len(plan.sentence_groups)
            assert len(set(sentences)) == len(sentences)
            assert all(_TERMINAL_RE.search(sentence) for sentence in sentences)
            assert not _QUESTION_RE.search(surface.text)
            assert not _CAUSAL_CONNECTOR_RE.search(surface.text)
            assert surface.text.count("「") == surface.text.count("」")
            assert resolver.unresolved_ids(surface.grounded_evidence_span_ids) == ()
            assert surface.realized_unit_ids == plan.ordered_unit_ids
            assert len(surface.predicate_families) == len(plan.ordered_unit_ids)
            assert len(surface.referent_kinds) == len(plan.ordered_unit_ids)
            assert surface.process_local is True
            anchored_candidates += surface.source_anchor_count > 0
            max_anchor_chars = max(
                max_anchor_chars,
                surface.source_anchor_max_visible_chars,
            )
    assert anchored_candidates == 41
    assert max_anchor_chars == 16


def test_step5_reuses_v1_referent_predicate_and_anchor_owners() -> None:
    source = _GENERATOR_PATH.read_text(encoding="utf-8")
    assert "resolve_grounded_reception_move_referent" in source
    assert "reception_move_predicate_family" in source
    assert "realize_grounded_human_reception" in source
    assert "allow_short_anchor" in source
    assert "_short_bound_anchor" not in source
    assert "_compact_bound_anchor as _compact_v1_bound_anchor" in source


def test_step5_is_deterministic_and_body_free_meta_never_copies_candidate_text() -> None:
    signature = inspect.signature(generate_reception_surface_candidates_v2)
    assert tuple(signature.parameters) == (
        "observation_plan",
        "content_plan",
        "candidate_plan_set",
        "resolver",
    )
    receipt_rows = []
    for case, observation, content_plan, plan_set, resolver, surface_set in (
        _development_surfaces()
    ):
        rerun = generate_reception_surface_candidates_v2(
            observation,
            content_plan,
            plan_set,
            resolver,
        )
        assert rerun == surface_set
        meta = surface_set.as_body_free_meta()
        assert not (_FORBIDDEN_META_KEYS & set(_walk_keys(meta)))
        encoded = json.dumps(meta, ensure_ascii=False, sort_keys=True)
        for candidate in surface_set.candidates:
            assert candidate.text not in encoded
        assert meta["candidate_bodies_included"] is False
        assert meta["selection_performed"] is False
        assert meta["hard_gate_performed"] is False
        assert meta["runtime_connected"] is False
        receipt_rows.append(
            {
                "case_id": case.case_id,
                "content_plan_id": content_plan.plan_id,
                "surface_meta": meta,
            }
        )
    assert sha256_json(receipt_rows) == (
        "3f0225b6a4f6580e5141bae32efb13f4ea98d6acb3b6717e9affb8c91eec51f6"
    )


def test_step5_has_no_exact_case_bank_random_external_ai_selector_or_runtime_hook() -> None:
    tree = ast.parse(_GENERATOR_PATH.read_text(encoding="utf-8"))
    imported_modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)
    source = _GENERATOR_PATH.read_text(encoding="utf-8")
    assert "NLS2-" not in source
    assert "exact8" not in source.lower()
    assert "expected_text" not in source
    assert "random" not in imported_modules
    assert "emlis_ai_reply_service" not in imported_modules
    assert not any(
        module.startswith(
            (
                "openai",
                "anthropic",
                "google.generativeai",
                "transformers",
                "llama_cpp",
            )
        )
        for module in imported_modules
    )
    assert _SELECTOR_PATH.is_file()
    reply_source = _REPLY_SERVICE_PATH.read_text(encoding="utf-8")
    assert "emlis_ai_grounded_human_reception_v2" not in reply_source
    assert "generate_reception_surface_candidates_v2" not in reply_source
    assert "emlis_ai_grounded_reception_candidate_selector_v2" not in reply_source


def test_step5_preserves_step1_public_backend_owner_snapshot() -> None:
    receipt = json.loads(_S1_RECEIPT_PATH.read_text(encoding="utf-8"))
    contract = receipt["public_contract_snapshot"]
    owner_rows = contract["backend_owner_files"]
    live_rows = [
        {
            "path": row["path"],
            "sha256": sha256_file(_REPO_ROOT / row["path"]),
        }
        for row in owner_rows
    ]
    assert live_rows == owner_rows
    assert sha256_json(live_rows) == contract["backend_owner_snapshot_sha256"]
    assert contract["route"] == "/emotion/submit"
    assert contract["comment_path"] == "input_feedback.comment_text"
    assert contract["status_path"] == "input_feedback.emlis_ai.observation_status"
