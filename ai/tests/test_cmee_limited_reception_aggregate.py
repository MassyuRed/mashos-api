# -*- coding: utf-8 -*-
from __future__ import annotations

"""Canonical LIMITED reception aggregation without meaning reselection."""

from dataclasses import replace
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import cocolon_meaning_experience_engine.contracts as contracts
from cocolon_meaning_experience_engine.contracts import (
    CMEEStage1ContractError,
    ObservationContributionKind,
    PlannedObservationContribution,
    RelationOperator,
    SemanticOperator,
    SubjectiveMode,
    SubjectiveOperator,
    resolve_limited_reception_aggregate,
)
from cocolon_meaning_experience_engine.emlis_stage1_composition import (
    RetainedReceptionActRow,
)


def _contribution(
    ref: str,
    *,
    semantic_operator: SemanticOperator = SemanticOperator.PRESENT_STATE,
    contribution_kind: ObservationContributionKind = (
        ObservationContributionKind.OBSERVE_CENTER
    ),
    evidence_refs: tuple[str, ...] | None = None,
) -> PlannedObservationContribution:
    return PlannedObservationContribution(
        schema_version="test-v1",
        contribution_id=ref,
        parent_duty_ref="observation-duty:test",
        contribution_kind=contribution_kind,
        interpretation_candidate_refs=(f"candidate:{ref}",),
        semantic_operator=semantic_operator,
        argument_bindings=(),
        relation_operator=RelationOperator.NO_RELATION_CLAIM,
        relation_basis_refs=(),
        derivation_rule_id="test.direct.v1",
        semantic_refs=(f"node:{ref}",),
        evidence_refs=(f"evidence:{ref}",) if evidence_refs is None else evidence_refs,
        retention="REQUIRED",
        semantic_key_version="test-key-v1",
        canonical_semantic_key=f"semantic-key:{ref}",
        prerequisite_contribution_refs=(),
        forbidden_operations=("NO_USER_FACT_PROMOTION",),
    )


def _act(name: str, *basis_refs: str) -> RetainedReceptionActRow:
    return RetainedReceptionActRow(name, name, tuple(basis_refs))


class CMEELimitedReceptionAggregateResolverTest(unittest.TestCase):
    def setUp(self) -> None:
        self.contributions = (
            _contribution("c1", semantic_operator=SemanticOperator.PRESENT_BURDEN),
            _contribution(
                "c2",
                semantic_operator=SemanticOperator.PRESENT_ACTUAL_OUTPUT,
            ),
            _contribution("c3", semantic_operator=SemanticOperator.PRESENT_DIRECTION),
            _contribution("c4", semantic_operator=SemanticOperator.PRESENT_CHANGE),
            _contribution("c5"),
        )

    def _resolve(
        self,
        rows: tuple[RetainedReceptionActRow, ...],
        *,
        expected: tuple[str, ...],
        retained: tuple[str, ...] = ("c1", "c2", "c3", "c4", "c5"),
        contributions: tuple[PlannedObservationContribution, ...] | None = None,
    ):
        return resolve_limited_reception_aggregate(
            rows,
            expected_act_refs=expected,
            retained_layer1_refs=retained,
            observation_contribution_rows=(
                self.contributions if contributions is None else contributions
            ),
        )

    def test_exact_two_to_four_share_one_attention_proposition_basis(self) -> None:
        matrices = (
            (
                (
                    _act("stay_with_current_burden", "c1"),
                    _act("honor_concrete_effort", "c2"),
                ),
                ("c1", "c2"),
            ),
            (
                (
                    _act("stay_with_current_burden", "c1"),
                    _act("honor_concrete_effort", "c2"),
                    _act("protect_retained_intention", "c3"),
                ),
                ("c1", "c2", "c3"),
            ),
            (
                (
                    _act("stay_with_current_burden", "c1"),
                    _act("honor_concrete_effort", "c2"),
                    _act("protect_retained_intention", "c3"),
                    _act("recognize_lived_change", "c2", "c4"),
                ),
                ("c1", "c2", "c3", "c4"),
            ),
            (
                (
                    _act("stay_with_current_burden", "c1"),
                    # Act-local order is not a second meaning authority.
                    _act("protect_retained_intention", "c3", "c2"),
                ),
                ("c1", "c2", "c3"),
            ),
        )
        for rows, expected_basis in matrices:
            with self.subTest(act_count=len(rows)):
                mode, operator, act_refs, basis_refs, aggregate = self._resolve(
                    rows,
                    expected=tuple(row.act_ref for row in rows),
                )
                self.assertIs(mode, SubjectiveMode.ATTENTION)
                self.assertIs(operator, SubjectiveOperator.ATTEND_TO)
                self.assertEqual(act_refs, tuple(row.act_ref for row in rows))
                self.assertEqual(basis_refs, expected_basis)
                self.assertTrue(aggregate)

    def test_single_act_preserves_the_existing_specialized_choice(self) -> None:
        row = _act("honor_concrete_effort", "c2")
        mode, operator, act_refs, basis_refs, aggregate = self._resolve(
            (row,),
            expected=(row.act_ref,),
        )
        legacy_pairs = contracts._im04_limited_reception_mode_operator_pairs(
            row.reception_act,
            (self.contributions[1],),
        )
        self.assertEqual(legacy_pairs, ((mode, operator),))
        self.assertEqual(
            (mode, operator),
            (
                SubjectiveMode.PERSONAL_APPRAISAL,
                SubjectiveOperator.APPRAISE_AS_MATERIAL,
            ),
        )
        self.assertEqual(act_refs, (row.act_ref,))
        self.assertEqual(basis_refs, row.basis_contribution_refs)
        self.assertEqual(len(self.contributions), 5)
        self.assertEqual(len(basis_refs), 1)
        self.assertFalse(aggregate)

    def test_single_attention_act_aggregates_its_selected_basis(self) -> None:
        row = _act("protect_retained_intention", "c5", "c1")
        mode, operator, act_refs, basis_refs, aggregate = self._resolve(
            (row,),
            expected=(row.act_ref,),
            retained=("c1", "c5"),
        )
        self.assertIs(mode, SubjectiveMode.ATTENTION)
        self.assertIs(operator, SubjectiveOperator.ATTEND_TO)
        self.assertEqual(act_refs, (row.act_ref,))
        self.assertEqual(basis_refs, ("c1", "c5"))
        self.assertTrue(aggregate)

        exact_one = _act("protect_retained_intention", "c5")
        mode, operator, act_refs, basis_refs, aggregate = self._resolve(
            (exact_one,),
            expected=(exact_one.act_ref,),
            retained=("c5",),
        )
        self.assertIs(mode, SubjectiveMode.ATTENTION)
        self.assertIs(operator, SubjectiveOperator.ATTEND_TO)
        self.assertEqual(act_refs, (exact_one.act_ref,))
        self.assertEqual(basis_refs, ("c5",))
        self.assertFalse(aggregate)

    def test_counter_foreign_evidence_order_and_cap_tampers_stop(self) -> None:
        counter = _act("bounded_counter_self_denial", "c1")
        affirmative = _act("stay_with_current_burden", "c1")
        invalid = (
            ((counter,), ("c1",), self.contributions),
            ((affirmative, counter), ("c1",), self.contributions),
            ((affirmative, affirmative), ("c1",), self.contributions),
            ((_act("unknown_reception", "c1"),), ("c1",), self.contributions),
            ((_act("stay_with_current_burden"),), ("c1",), self.contributions),
            ((_act("stay_with_current_burden", "foreign"),), ("c1",), self.contributions),
            (
                (affirmative,),
                ("c1",),
                (replace(self.contributions[0], evidence_refs=()),),
            ),
            (
                (affirmative,),
                ("c1",),
                (replace(self.contributions[0], evidence_refs=(None,)),),
            ),
            (
                (
                    SimpleNamespace(
                        act_ref="stay_with_current_burden",
                        reception_act="stay_with_current_burden",
                        basis_contribution_refs=("c1",),
                    ),
                ),
                ("c1",),
                self.contributions,
            ),
            ((affirmative,), ("c1", "c1"), self.contributions),
            ((affirmative,), ("c1", "c2", "c3", "c4", "c5", "c6"), self.contributions),
            (
                (
                    affirmative,
                    _act("honor_concrete_effort", "c2"),
                    _act("protect_retained_intention", "c3"),
                    _act("recognize_lived_change", "c4"),
                    _act("respect_words_placed", "c5"),
                ),
                ("c1", "c2", "c3", "c4", "c5"),
                self.contributions,
            ),
        )
        for index, (rows, retained, contributions) in enumerate(invalid):
            with self.subTest(invalid=index):
                with self.assertRaisesRegex(
                    CMEEStage1ContractError,
                    "LIMITED_RECEPTION_CAPABILITY_GAP_STOP",
                ):
                    self._resolve(
                        rows,
                        expected=tuple(row.act_ref for row in rows),
                        retained=retained,
                        contributions=contributions,
                    )

        ordered_rows = (
            _act("stay_with_current_burden", "c1"),
            _act("honor_concrete_effort", "c2"),
        )
        expected = tuple(row.act_ref for row in ordered_rows)
        with self.assertRaisesRegex(
            CMEEStage1ContractError,
            "LIMITED_RECEPTION_CAPABILITY_GAP_STOP",
        ):
            self._resolve(
                tuple(reversed(ordered_rows)),
                expected=expected,
            )
        with self.assertRaisesRegex(
            CMEEStage1ContractError,
            "LIMITED_RECEPTION_CAPABILITY_GAP_STOP",
        ):
            self._resolve(
                ordered_rows,
                expected=expected,
                retained=("c2", "c1"),
            )

    def test_exact_two_requires_the_common_registered_attention_pair(self) -> None:
        mappings = tuple(
            replace(
                row,
                eligible_mode_operator_pairs=tuple(
                    pair
                    for pair in row.eligible_mode_operator_pairs
                    if pair
                    != (
                        SubjectiveMode.ATTENTION,
                        SubjectiveOperator.ATTEND_TO,
                    )
                ),
            )
            if row.reception_act == "honor_concrete_effort"
            else row
            for row in contracts.CMEE_STAGE1_RECEPTION_ACT_MAPPING_EXACT7
        )
        with patch.object(
            contracts,
            "CMEE_STAGE1_RECEPTION_ACT_MAPPING_EXACT7",
            mappings,
        ):
            with self.assertRaisesRegex(
                CMEEStage1ContractError,
                "LIMITED_RECEPTION_CAPABILITY_GAP_STOP",
            ):
                self._resolve(
                    (
                        _act("stay_with_current_burden", "c1"),
                        _act("honor_concrete_effort", "c2"),
                    ),
                    expected=(
                        "stay_with_current_burden",
                        "honor_concrete_effort",
                    ),
                )


if __name__ == "__main__":
    unittest.main()
