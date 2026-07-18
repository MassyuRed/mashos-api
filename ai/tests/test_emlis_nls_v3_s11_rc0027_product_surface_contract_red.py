# -*- coding: utf-8 -*-
from __future__ import annotations

"""rc0027 Product Read contract for a grounded, bookkeeping-free Surface.

The representative cases are selected only by structural coverage.  No
expected completed sentence, case branch, or source-body fragment is frozen
here.
"""

from collections import Counter
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import re

import pytest

import emlis_ai_step11_natural_surface_matcher_v3 as matcher
from emlis_ai_step11_natural_surface_v3 import (
    STEP11_CANDIDATE_VERSION_ID,
)
from emlis_ai_step11_runtime_adapter_v3 import execute_step11_offline_v3
from emlis_ai_step11_surface_catalog_v3 import (
    FROZEN_STEP11_SURFACE_CATALOG_SHA256,
    STEP11_SURFACE_CATALOG,
    STEP11_SURFACE_CATALOG_SHA256,
    validate_step11_surface_catalog,
)


_HERE = Path(__file__).resolve().parent
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
_REPRESENTATIVE_ACTION_LIFECYCLES = {
    "nls3s_b001_0019": "reported_completed",
    "nls3s_b001_0035": "reported_ongoing",
    "nls3s_b001_0043": "reported_completed",
}
_VISIBLE_BOOKKEEPING_TOKENS = (
    "意味特徴",
    "入力片",
    "記述内容",
    "前者",
    "後者",
    "後者側",
    "〔",
    "〕",
    "感情欄",
    "行動欄",
    "、また、",
    "に表れた伝えられた",
)
_VISIBLE_ORDINAL = re.compile(r"[1-9][0-9]*つ目の")
_QUOTE_TOKENS = ("『", "』", "「", "」")
_GENERIC_BARE_HEADS = frozenset(
    {"出来事", "状態", "明示された内容", "制約", "大切さ"}
)
_DANGLING_ANCHOR_END_RE = re.compile(
    r"(?:つなが|分から|止|取り戻|ことを|試し|"
    r"(?:て|で|を|が|は|に|へ|と|も|の))$"
)
_BOOKKEEPING_CHAIN_RE = re.compile(
    r"(?:nucleus|obligation|source|owner|semantic|grounded)"
    r"(?:[_:.-][A-Za-z0-9_:-]+){1,}"
)
_ANCHOR_BINDING_FAMILIES = frozenset(
    {"reported_profile", "action_lifecycle", "relation_shift"}
)
_FINAL_CATALOG_SHA256 = (
    "1beec18839ed77abd1e52b0a06eb60c5867223fd54183c251a8f0efbc37ccc08"
)
_LIFECYCLE_INPUTS = {
    "completed": {
        "expected": "reported_completed",
        "input": {
            "thought_text": "",
            "action_text": "机の上を片づけた。",
            "emotions": [{"type": "平穏", "strength": "weak"}],
            "categories": ["生活"],
        },
    },
    "ongoing": {
        "expected": "reported_ongoing",
        "input": {
            "thought_text": "",
            "action_text": "資料をまとめている。",
            "emotions": [{"type": "平穏", "strength": "weak"}],
            "categories": ["生活"],
        },
    },
    "intended": {
        "expected": "intended",
        "input": {
            "thought_text": "",
            "action_text": "明日は机の上を片づける。",
            "emotions": [{"type": "平穏", "strength": "weak"}],
            "categories": ["生活"],
        },
    },
}
_PRODUCTION_OWNER_PATHS = (
    _HERE.parent
    / "services"
    / "ai_inference"
    / "emlis_ai_step11_grounded_lexicalization_v3.py",
    _HERE.parent
    / "services"
    / "ai_inference"
    / "emlis_ai_step11_surface_catalog_v3.py",
    _HERE.parent
    / "services"
    / "ai_inference"
    / "emlis_ai_step11_natural_surface_v3.py",
    _HERE.parent
    / "services"
    / "ai_inference"
    / "emlis_ai_step11_natural_surface_matcher_v3.py",
    _HERE.parent
    / "services"
    / "ai_inference"
    / "emlis_ai_step11_hard_gate_v3.py",
    _HERE.parent
    / "services"
    / "ai_inference"
    / "emlis_ai_step11_semantic_overlay_v3.py",
    _HERE.parent
    / "services"
    / "ai_inference"
    / "emlis_ai_step11_planning_frontier_v3.py",
)


def _fixture_inputs() -> dict[str, dict[str, object]]:
    rows: dict[str, dict[str, object]] = {}
    for line in _FIXTURE.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        case_id = str(row.get("case_id", ""))
        if case_id in _REPRESENTATIVE_CASE_IDS:
            rows[case_id] = dict(row["input"])
    assert set(rows) == set(_REPRESENTATIVE_CASE_IDS)
    return rows


@pytest.fixture(scope="module")
def executions():
    inputs = _fixture_inputs()
    return {
        case_id: execute_step11_offline_v3(
            inputs[case_id],
            candidate_version_id=STEP11_CANDIDATE_VERSION_ID,
            source_dependency_closure_sha256="7" * 64,
        )
        for case_id in _REPRESENTATIVE_CASE_IDS
    }


@pytest.fixture(scope="module")
def lifecycle_executions():
    return {
        name: execute_step11_offline_v3(
            dict(row["input"]),
            candidate_version_id=STEP11_CANDIDATE_VERSION_ID,
            source_dependency_closure_sha256="6" * 64,
        )
        for name, row in _LIFECYCLE_INPUTS.items()
    }


def _witness(execution):
    assert execution.final_utf8_bytes is not None
    return matcher.parse_step11_natural_surface(execution.final_utf8_bytes)


def _binding(execution, witness):
    candidate = execution.selected_candidate
    assert candidate is not None
    return matcher.match_step11_natural_surface(
        witness,
        inventory_result=execution.inventory_result,
        content_plan=execution.content_plan,
        discourse_plan=candidate.discourse_plan,
        current_input=execution.projected_current_input,
    )


def _atom_text(execution, atom: matcher.Step11ParsedAtom) -> str:
    body = execution.final_utf8_bytes
    assert body is not None
    return body[atom.byte_start : atom.byte_end].decode("utf-8")


def _action_owner_and_phrase_spec(execution):
    candidate = execution.selected_candidate
    assert candidate is not None
    action_owners = tuple(
        row
        for row in execution.inventory_result.source_snapshot.nuclei
        if row.kind == "action" and "memo_action" in row.source_fields
    )
    assert len(action_owners) == 1
    owner = action_owners[0]
    specs = tuple(
        row
        for row in candidate.surface_ast.grounded_phrase_specs
        if owner.source_id in row.owner_nucleus_ids
    )
    assert len(specs) == 1
    return owner, specs[0]


def test_rc0027_version_and_catalog_are_frozen_and_valid() -> None:
    assert STEP11_CANDIDATE_VERSION_ID == "nls_v3_rc_0027"
    assert STEP11_SURFACE_CATALOG["candidate_version_id"] == (
        STEP11_CANDIDATE_VERSION_ID
    )
    assert STEP11_SURFACE_CATALOG_SHA256 == _FINAL_CATALOG_SHA256
    assert FROZEN_STEP11_SURFACE_CATALOG_SHA256 == _FINAL_CATALOG_SHA256
    assert validate_step11_surface_catalog() == ()
    lexical = STEP11_SURFACE_CATALOG["grounded_lexicalization"]
    assert len(lexical["phrase_profile_registry"]["profiles"]) == 42
    assert "source_anchor_binding" not in lexical
    assert lexical["source_anchor_binding_families"] == {
        "reported_profile": "に表れている",
        "action_lifecycle": "として示された",
        "relation_shift": "を起点にした",
    }


def test_rc0027_production_owners_are_case_and_corpus_cue_free() -> None:
    corpus_case_pattern = re.compile(r"nls3s_b[0-9]+_[0-9]+")
    forbidden_cues = (
        "case_id",
        "batch_001",
        "cycle_001",
        "known28",
        "development42",
        "invalid16",
    )
    for path in _PRODUCTION_OWNER_PATHS:
        source = path.read_text(encoding="utf-8")
        assert corpus_case_pattern.search(source) is None, path.name
        assert all(cue not in source for cue in forbidden_cues), path.name


def test_rc0027_representative_structures_all_select_v3(executions) -> None:
    assert set(executions) == set(_REPRESENTATIVE_CASE_IDS)
    for case_id, execution in executions.items():
        assert execution.status == "selected", case_id
        assert execution.selected_candidate is not None, case_id
        assert execution.final_utf8_bytes is not None, case_id
        assert execution.v1_fallback_used is False, case_id


@pytest.mark.parametrize("lifecycle_name", tuple(_LIFECYCLE_INPUTS))
def test_rc0027_observation_and_reception_share_exact_action_lifecycle(
    lifecycle_executions,
    lifecycle_name: str,
) -> None:
    """Lifecycle is one source-backed fact across both public sections."""

    execution = lifecycle_executions[lifecycle_name]
    expected = str(_LIFECYCLE_INPUTS[lifecycle_name]["expected"])
    assert execution.status == "selected"
    owner, spec = _action_owner_and_phrase_spec(execution)
    phrase_features = dict(spec.visible_feature_fields)
    assert phrase_features["action_lifecycle"] == expected

    reception_atoms = tuple(
        atom
        for atom in _witness(execution).atoms
        if atom.section_role == "reception"
        and atom.realization_status != "not_applicable"
    )
    assert reception_atoms
    assert {row.realization_status for row in reception_atoms} == {expected}


@pytest.mark.parametrize(
    ("lifecycle_name", "forged_status"),
    (("completed", "intended"), ("intended", "reported_completed")),
)
def test_rc0027_future_complete_contradiction_fails_independent_binding(
    lifecycle_executions,
    lifecycle_name: str,
    forged_status: str,
) -> None:
    execution = lifecycle_executions[lifecycle_name]
    witness = _witness(execution)
    reception = next(
        atom
        for atom in witness.atoms
        if atom.section_role == "reception"
        and atom.reception_scope in {"action", "thought_action", "relation_action"}
    )
    forged = replace(
        witness,
        atoms=tuple(
            replace(atom, realization_status=forged_status)
            if atom is reception
            else atom
            for atom in witness.atoms
        ),
    )

    binding = _binding(execution, forged)

    assert binding.verified is False
    assert "S11_MATCH_RECEPTION_TARGET_SCOPE_STATUS_MISMATCH" in (
        binding.issue_codes
    )


def test_rc0027_public_bodies_hide_all_reference_bookkeeping(
    executions,
) -> None:
    violations: list[tuple[str, str]] = []
    for case_id, execution in executions.items():
        body = execution.final_utf8_bytes
        assert body is not None
        text = body.decode("utf-8")
        if _VISIBLE_ORDINAL.search(text) is not None:
            violations.append((case_id, "VISIBLE_ORDINAL"))
        violations.extend(
            (case_id, token)
            for token in _VISIBLE_BOOKKEEPING_TOKENS
            if token in text
        )
    assert violations == []


@pytest.mark.parametrize(
    ("case_id", "expected_lifecycle"),
    tuple(_REPRESENTATIVE_ACTION_LIFECYCLES.items()),
)
def test_rc0027_representative_action_lifecycle_is_visible_and_consistent(
    executions,
    case_id: str,
    expected_lifecycle: str,
) -> None:
    execution = executions[case_id]
    owner, spec = _action_owner_and_phrase_spec(execution)
    assert dict(spec.visible_feature_fields)["action_lifecycle"] == (
        expected_lifecycle
    )
    relevant_atoms = tuple(
        row
        for row in _witness(execution).atoms
        if row.section_role == "reception"
        and row.realization_status != "not_applicable"
    )
    assert relevant_atoms
    assert {
        row.realization_status for row in relevant_atoms
    } == {expected_lifecycle}


def test_rc0027_complex_case_keeps_unique_profiles_lifecycle_and_relation_owners(
    executions,
) -> None:
    """The complex case is checked by owners, not by a frozen sentence shape."""

    execution = executions["nls3s_b001_0063"]
    candidate = execution.selected_candidate
    body = execution.final_utf8_bytes
    assert candidate is not None and body is not None
    text = body.decode("utf-8")
    assert _BOOKKEEPING_CHAIN_RE.search(text) is None

    anchor = candidate.surface_ast.visible_source_anchor_use
    assert anchor is not None
    assert _DANGLING_ANCHOR_END_RE.search(anchor.anchor_text) is None
    assert anchor.binding_family in _ANCHOR_BINDING_FAMILIES

    source_by_id = {
        row.source_id: row
        for row in execution.inventory_result.source_snapshot.nuclei
    }
    specs = candidate.surface_ast.grounded_phrase_specs
    profile_ids = {
        row["profile_id"]
        for row in STEP11_SURFACE_CATALOG["grounded_lexicalization"]
        ["phrase_profile_registry"]["profiles"]
    }
    assert len({row.grounded_phrase_id for row in specs}) == len(specs)
    assert all(row.phrase_profile_id in profile_ids for row in specs)
    assert all(
        len(row.owner_nucleus_ids) == 1
        and row.owner_nucleus_ids[0] in source_by_id
        for row in specs
    )
    assert len(
        {
            (
                row.visible_feature_fields,
                row.visible_feature_fingerprint_sha256,
                row.phrase_profile_id,
                row.anchor_risk_rank,
            )
            for row in specs
        }
    ) == len(specs)
    for spec in specs:
        assert spec.phrase_text not in _GENERIC_BARE_HEADS
        assert 3 <= len(spec.phrase_text) <= 40
        assert _BOOKKEEPING_CHAIN_RE.search(spec.phrase_text) is None
        assert spec.phrase_text in text
    action_specs = tuple(
        row
        for row in specs
        if source_by_id[row.owner_nucleus_ids[0]].kind == "action"
    )
    assert action_specs
    assert {
        dict(row.visible_feature_fields)["action_lifecycle"]
        for row in action_specs
    } == {"intended"}

    witness = _witness(execution)
    binding = _binding(execution, witness)
    assert binding.verified is True, binding.issue_codes
    bindings_by_atom: dict[str, list[object]] = {}
    for row in binding.grounded_phrase_bindings:
        bindings_by_atom.setdefault(row.atom_id, []).append(row)
    relation_atoms = tuple(
        row for row in witness.atoms if row.relation_type is not None
    )
    assert relation_atoms
    for atom in relation_atoms:
        owned = bindings_by_atom.get(atom.atom_id, [])
        assert owned
        assert all(
            row.match_candidate_count == 1
            and set(row.owner_nucleus_ids) <= set(source_by_id)
            and row.owner_obligation_ids
            for row in owned
        )


def test_rc0027_representative_distribution_is_not_one_surface_family(
    executions,
) -> None:
    """Design 18.4: wrappers are allowed; lexical/predicate monoculture is not."""

    profile_case_counts: Counter[str] = Counter()
    predicate_case_counts: Counter[str] = Counter()
    anchor_family_counts: Counter[str] = Counter()
    for case_id, execution in executions.items():
        candidate = execution.selected_candidate
        body = execution.final_utf8_bytes
        assert candidate is not None and body is not None, case_id
        text = body.decode("utf-8")
        profile_case_counts.update(
            {
                row.phrase_profile_id
                for row in candidate.surface_ast.grounded_phrase_specs
            }
        )
        witness = _witness(execution)
        predicate_families = {
            atom.form_id
            for atom in witness.atoms
            if atom.section_role == "observation"
        }
        predicate_case_counts.update(predicate_families)
        anchor = candidate.surface_ast.visible_source_anchor_use
        assert anchor is not None, case_id
        assert anchor.binding_family in _ANCHOR_BINDING_FAMILIES
        assert text.count(f"「{anchor.anchor_text}」") == 1
        assert anchor.scalar_count == len(anchor.anchor_text)
        assert anchor.source_end - anchor.source_start == anchor.scalar_count
        assert anchor.anchor_text_sha256 == hashlib.sha256(
            anchor.anchor_text.encode("utf-8")
        ).hexdigest()
        anchor_family_counts[anchor.binding_family] += 1

    cohort_size = len(executions)
    # A representative cohort is a diagnostic, not the formal 100-case
    # threshold.  It nevertheless rejects a 7/8 or 8/8 structural monoculture.
    concentration_limit = cohort_size * 3 // 4
    assert len(profile_case_counts) >= 3
    assert max(predicate_case_counts.values(), default=0) <= concentration_limit
    assert 2 <= len(anchor_family_counts) <= 3
    assert max(anchor_family_counts.values()) <= concentration_limit


def test_rc0027_reception_has_no_literal_replay_and_keeps_action_lifecycle(
    executions,
) -> None:
    violations: list[tuple[str, str]] = []
    for case_id, execution in executions.items():
        reception_atoms = tuple(
            atom
            for atom in _witness(execution).atoms
            if atom.section_role == "reception"
        )
        assert reception_atoms, case_id
        action_lifecycles = {
            dict(spec.visible_feature_fields)["action_lifecycle"]
            for spec in execution.selected_candidate.surface_ast.grounded_phrase_specs
            if dict(spec.visible_feature_fields).get("nucleus_kind") == "action"
            and "action_lifecycle" in dict(spec.visible_feature_fields)
        }
        for atom in reception_atoms:
            atom_text = _atom_text(execution, atom)
            if atom.source_fragments:
                violations.append((case_id, "RECEPTION_SOURCE_LITERAL"))
            if atom.grounded_phrases:
                violations.append((case_id, "RECEPTION_REPLAYS_GROUNDED_PHRASE"))
            if any(token in atom_text for token in _QUOTE_TOKENS):
                violations.append((case_id, "RECEPTION_QUOTED_LITERAL"))
            if (
                atom.reception_scope
                in {"action", "thought_action", "relation_action"}
                and atom.realization_status not in action_lifecycles
            ):
                violations.append((case_id, "RECEPTION_LIFECYCLE_MISMATCH"))
    assert violations == []


def test_rc0027_relation_and_unknown_are_fused_with_grounded_owner(
    executions,
) -> None:
    relation_count = 0
    unknown_count = 0
    violations: list[tuple[str, str]] = []
    for case_id, execution in executions.items():
        witness = _witness(execution)
        binding = _binding(execution, witness)
        assert binding.verified is True, (case_id, binding.issue_codes)
        source_nucleus_ids = {
            row.source_id
            for row in execution.inventory_result.source_snapshot.nuclei
        }
        phrase_bindings_by_atom: dict[str, list[object]] = {}
        for row in binding.grounded_phrase_bindings:
            phrase_bindings_by_atom.setdefault(row.atom_id, []).append(row)
        observation_atoms = tuple(
            atom
            for atom in witness.atoms
            if atom.section_role == "observation"
        )
        for atom in observation_atoms:
            is_relation = bool(
                atom.relation_type is not None
                or "mixed_emotion_relation" in atom.claim_kinds
            )
            is_unknown = "unknown_boundary" in atom.claim_kinds
            if not (is_relation or is_unknown):
                continue
            relation_count += int(is_relation)
            unknown_count += int(is_unknown)
            if "nucleus_notice" not in atom.claim_kinds:
                violations.append((case_id, "MEANING_WITHOUT_NUCLEUS_OWNER"))
            if not atom.grounded_phrases:
                violations.append((case_id, "MEANING_WITHOUT_GROUNDED_PHRASE"))
            bounded_anchor_texts = tuple(
                phrase.anchor_text
                for phrase in atom.grounded_phrases
                if phrase.anchor_text is not None
            )
            if atom.source_fragments not in {(), bounded_anchor_texts}:
                violations.append((case_id, "RAW_SOURCE_LITERAL_REPLAY"))
            if any(len(fragment) > 16 for fragment in atom.source_fragments):
                violations.append((case_id, "UNBOUNDED_SOURCE_ANCHOR"))
            owned_bindings = phrase_bindings_by_atom.get(atom.atom_id, [])
            if not owned_bindings:
                violations.append((case_id, "GROUNDED_OWNER_UNBOUND"))
            if any(
                row.match_candidate_count != 1
                or not row.owner_nucleus_ids
                or not row.owner_obligation_ids
                or not set(row.owner_nucleus_ids) <= source_nucleus_ids
                for row in owned_bindings
            ):
                violations.append((case_id, "GROUNDED_OWNER_NOT_UNIQUE"))
    assert relation_count > 0
    assert unknown_count > 0
    assert violations == []
