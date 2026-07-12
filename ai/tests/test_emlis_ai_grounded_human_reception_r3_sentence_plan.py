# -*- coding: utf-8 -*-
from __future__ import annotations

"""R3 SentencePlan role contract for the distinct human reception line."""

from dataclasses import replace
import json
from pathlib import Path

from emlis_ai_current_input_bundle import normalize_emlis_current_input
from emlis_ai_evidence_ledger_service import (
    build_evidence_ledger,
    build_evidence_span_resolver,
)
from emlis_ai_grounded_observation_plan import build_grounded_observation_plan
from emlis_ai_grounded_human_reception import reception_active_acts
from emlis_ai_grounded_sentence_surface import (
    GROUND_RECOVERY_STAGES,
    build_grounded_sentence_plan,
    validate_grounded_sentence_plan,
)


_FIXTURE = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "grounded_human_reception_exact8_v2_20260712.json"
)


def _load_cases():
    return json.loads(_FIXTURE.read_text(encoding="utf-8"))["cases"]


def _artifacts(current_input, *, recovery_stage="full"):
    normalized = normalize_emlis_current_input(current_input)
    spans = tuple(build_evidence_ledger(normalized))
    resolver = build_evidence_span_resolver(spans, current_input=normalized)
    plan = build_grounded_observation_plan(normalized, evidence_spans=spans)
    sentence_plan = build_grounded_sentence_plan(
        plan,
        resolver,
        recovery_stage=recovery_stage,
    )
    return plan, sentence_plan, resolver


def _human_line(sentence_plan):
    lines = tuple(
        line
        for line in sentence_plan.lines
        if line.binding.line_role == "human_follow"
    )
    assert len(lines) == 1
    return lines[0]


def _dedupe(values):
    return tuple(dict.fromkeys(values))


def _replace_human_line(sentence_plan, line):
    return replace(
        sentence_plan,
        lines=tuple(
            line if item.binding.line_role == "human_follow" else item
            for item in sentence_plan.lines
        ),
    )


def test_r3_exact8_binds_one_final_reception_line_to_plan_role_and_evidence() -> None:
    for case in _load_cases():
        plan, sentence_plan, resolver = _artifacts(case["exact_current_input"])
        reception = plan.response_plan.human_reception_plan
        assert reception is not None
        line = _human_line(sentence_plan)
        atoms = line.binding.functional_atom_ids
        reception_atoms = tuple(
            atom for atom in atoms if atom.startswith("reception_")
        )

        assert sentence_plan.lines[-1] is line
        assert line.surface_function == "render_human_follow"
        assert line.binding.relation_ids == ()
        assert line.binding.nucleus_ids == _dedupe(
            (*reception.target_nucleus_ids, *reception.support_nucleus_ids)
        )
        assert line.binding.evidence_span_ids == reception.source_evidence_span_ids
        assert not resolver.unresolved_ids(line.binding.evidence_span_ids)

        expected_acts = tuple(
            f"reception_act:{act}"
            for act in reception_active_acts(reception, "full")
        )
        assert tuple(
            atom for atom in reception_atoms if atom.startswith("reception_act:")
        ) == expected_acts
        assert (
            f"reception_follow_primary:{reception.primary_follow_element}"
            in reception_atoms
        )
        assert tuple(
            atom
            for atom in reception_atoms
            if atom.startswith("reception_follow_secondary:")
        ) == tuple(
            f"reception_follow_secondary:{element}"
            for element in reception.secondary_follow_elements
        )
        expected_afterglow = (
            (
                "reception_follow_afterglow:"
                f"{reception.afterglow_follow_element}"
            ,)
            if reception.afterglow_follow_element is not None
            else ()
        )
        assert tuple(
            atom
            for atom in reception_atoms
            if atom.startswith("reception_follow_afterglow:")
        ) == expected_afterglow
        assert {
            f"reception_stance:{reception.stance}",
            f"reception_speaker:{reception.speaker_presence}",
            f"reception_reference:{reception.reference_mode}",
            "reception_quote_policy:no_full_quote_replay",
            "reception_sentence_budget:one_to_three",
            f"reception_sentence_min:{reception.depth_policy.min_sentences}",
            f"reception_sentence_max:{reception.depth_policy.max_sentences}",
            "reception_distinctness:required",
            "reception_non_enumeration:required",
            "human_follow_delivery:separate",
            "closure_role:human_follow",
        } <= set(atoms)
        assert not any(
            atom == "source_anchor_quote"
            or atom.startswith("relation:")
            or atom.startswith("relation_surface_role:")
            or atom.startswith("observation_surface_role:")
            or atom.startswith("semantic_arc:")
            for atom in atoms
        )

        observation_lines = sentence_plan.lines[:-1]
        assert observation_lines
        assert all(
            not any(
                atom.startswith("reception_")
                for atom in observation_line.binding.functional_atom_ids
            )
            for observation_line in observation_lines
        )
        relation_owners = {
            relation_id
            for observation_line in observation_lines
            for relation_id in observation_line.binding.relation_ids
        }
        assert set(plan.coverage_requirements.required_relation_ids) <= relation_owners
        assert validate_grounded_sentence_plan(sentence_plan, plan, resolver) == ()


def test_r3_recovery_stages_keep_the_reception_role_separate_and_grounded() -> None:
    for case in _load_cases():
        plan, sentence_plan, resolver = _artifacts(
            case["exact_current_input"],
            recovery_stage="full",
        )
        reception = plan.response_plan.human_reception_plan
        assert reception is not None
        eligible_stages = tuple(
            stage
            for stage in GROUND_RECOVERY_STAGES
            if stage != "minimal_grounded"
            or (
                reception.depth_policy.level == "minimal"
                and reception.depth_policy.safety_mode == "standard"
                and len(reception.moves) == 1
            )
        )
        for recovery_stage in eligible_stages:
            if recovery_stage != "full":
                plan, sentence_plan, resolver = _artifacts(
                    case["exact_current_input"],
                    recovery_stage=recovery_stage,
                )
            line = _human_line(sentence_plan)
            reception_atoms = tuple(
                atom
                for atom in line.binding.functional_atom_ids
                if atom.startswith("reception_")
            )
            assert sentence_plan.lines[-1] is line
            assert line.binding.relation_ids == ()
            assert line.binding.evidence_span_ids == reception.source_evidence_span_ids
            assert f"recovery:{recovery_stage}" in line.binding.functional_atom_ids
            assert "human_follow_delivery:separate" in line.binding.functional_atom_ids
            expected_acts = reception_active_acts(
                reception,
                recovery_stage,
            )
            assert tuple(
                atom.split(":", 1)[1]
                for atom in reception_atoms
                if atom.startswith("reception_act:")
            ) == expected_acts
            if recovery_stage != "full":
                assert not any(
                    atom.startswith("reception_follow_secondary:")
                    or atom.startswith("reception_follow_afterglow:")
                    for atom in reception_atoms
                )
            assert validate_grounded_sentence_plan(sentence_plan, plan, resolver) == ()


def test_r3_validator_rejects_reception_role_contract_mutations() -> None:
    case = next(case for case in _load_cases() if case["case_id"] == "I6-D02")
    plan, sentence_plan, resolver = _artifacts(case["exact_current_input"])
    reception = plan.response_plan.human_reception_plan
    assert reception is not None
    line = _human_line(sentence_plan)

    def without_prefix(prefix):
        return tuple(
            atom
            for atom in line.binding.functional_atom_ids
            if not atom.startswith(prefix)
        )

    relation_id = plan.coverage_requirements.required_relation_ids[0]
    mutations = (
        (
            replace(
                line,
                binding=replace(
                    line.binding,
                    functional_atom_ids=without_prefix("reception_act:"),
                ),
            ),
            "human_reception_act_missing",
        ),
        (
            replace(
                line,
                binding=replace(line.binding, relation_ids=(relation_id,)),
            ),
            "human_reception_relation_owner_forbidden",
        ),
        (
            replace(
                line,
                binding=replace(
                    line.binding,
                    functional_atom_ids=(
                        *line.binding.functional_atom_ids,
                        "observation_surface_role:state_arc",
                    ),
                ),
            ),
            "human_reception_observation_atom_forbidden",
        ),
        (
            replace(
                line,
                binding=replace(
                    line.binding,
                    functional_atom_ids=without_prefix(
                        "reception_sentence_budget:"
                    ),
                ),
            ),
            "human_reception_sentence_budget_invalid",
        ),
        (
            replace(
                line,
                binding=replace(
                    line.binding,
                    functional_atom_ids=without_prefix("reception_reference:"),
                ),
            ),
            "human_reception_reference_policy_missing",
        ),
        (
            replace(
                line,
                binding=replace(
                    line.binding,
                    functional_atom_ids=without_prefix(
                        "reception_distinctness:"
                    ),
                ),
            ),
            "human_reception_distinctness_contract_missing",
        ),
        (
            replace(
                line,
                binding=replace(
                    line.binding,
                    functional_atom_ids=without_prefix("reception_speaker:"),
                ),
            ),
            "self_denial_explicit_stance_missing",
        ),
        (
            replace(
                line,
                binding=replace(
                    line.binding,
                    nucleus_ids=reception.target_nucleus_ids,
                ),
            ),
            "human_reception_target_mismatch",
        ),
    )
    for mutated_line, expected_issue in mutations:
        mutated = _replace_human_line(sentence_plan, mutated_line)
        assert expected_issue in validate_grounded_sentence_plan(
            mutated,
            plan,
            resolver,
        )

    unresolved_reception = replace(
        reception,
        source_evidence_span_ids=(
            *reception.source_evidence_span_ids,
            "s999999",
        ),
    )
    unresolved_plan = replace(
        plan,
        response_plan=replace(
            plan.response_plan,
            human_reception_plan=unresolved_reception,
        ),
    )
    unresolved_line = replace(
        line,
        binding=replace(
            line.binding,
            evidence_span_ids=unresolved_reception.source_evidence_span_ids,
        ),
    )
    unresolved_sentence_plan = _replace_human_line(sentence_plan, unresolved_line)
    assert "human_reception_source_evidence_unresolved" in (
        validate_grounded_sentence_plan(
            unresolved_sentence_plan,
            unresolved_plan,
            resolver,
        )
    )
