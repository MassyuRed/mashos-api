# -*- coding: utf-8 -*-
from __future__ import annotations

"""I7 local Product Read Feel, device provenance, and P5-entry tests."""

import asyncio
import json
import unittest

from helpers.emlis_ai_grounded_observation_i0_inventory import (
    GROUND_OBSERVATION_I0_KNOWN_REGRESSION_CASES,
)
from helpers.emlis_ai_grounded_observation_i6_cases import (
    GROUND_OBSERVATION_I6_BLIND_CASES,
)
from helpers.emlis_ai_grounded_observation_i7_readfeel import (
    I7_CANONICAL_COMPOSER_SOURCE,
    I7_CANONICAL_GENERATION_PATH,
    I7KarenLocalReview,
    assess_i7_device_evidence,
    assess_i7_local_surface,
    decide_i7_progression,
)
from emlis_ai_reply_service import render_emlis_ai_reply


def _render(current_input):
    return asyncio.run(
        render_emlis_ai_reply(
            user_id="i7-local-product-read",
            subscription_tier="free",
            current_input=current_input,
        )
    )


def _assert_body_free(test: unittest.TestCase, payload) -> None:
    dumped = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    for forbidden in ("raw_input", "surface_text", "comment_text", "returned_surface"):
        test.assertNotIn(f'"{forbidden}": "', dumped)
    test.assertFalse(payload.get("raw_input_included"))
    test.assertFalse(payload.get("returned_surface_included"))
    test.assertFalse(payload.get("comment_text_included"))


def _explicit_passed_reviews(case_ids) -> list[I7KarenLocalReview]:
    return [
        I7KarenLocalReview(
            case_id=case_id,
            snapshot_fingerprint="a" * 64,
            required_nucleus_retained="pass",
            required_relation_direction="pass",
            lexical_fidelity="pass",
            whole_input_balance="pass",
            human_follow_fit="pass",
            natural_japanese="pass",
            non_template_readfeel="pass",
            safety_boundary="pass",
            wants_more_input_candidate="pass",
            fatal_reason_refs=(),
            verdict="local_human_pass",
        )
        for case_id in case_ids
    ]


class I7LocalProductReadFeelTests(unittest.TestCase):
    def test_known_four_and_unseen_twelve_have_no_deterministic_fatal(self) -> None:
        assessments = []
        for case in (
            *GROUND_OBSERVATION_I0_KNOWN_REGRESSION_CASES,
            *GROUND_OBSERVATION_I6_BLIND_CASES,
        ):
            with self.subTest(case_id=case.case_id):
                reply = _render(case.as_current_input())
                assessment = assess_i7_local_surface(
                    case_id=case.case_id,
                    surface_text=reply.comment_text,
                    grounded_meta=reply.meta["grounded_observation"],
                )
                self.assertEqual("candidate_pass", assessment.candidate_status)
                self.assertEqual((), assessment.fatal_reason_refs)
                self.assertFalse(assessment.human_review_claimed)
                _assert_body_free(self, assessment.as_body_free_meta())
                assessments.append(assessment)
        self.assertEqual(16, len(assessments))

    def test_revised_supplied_device_evidence_is_rejected_as_old_runtime(self) -> None:
        # Body-free facts read from the supplied A-D backend logs.  Their
        # displayed bodies are intentionally not copied into this fixture.
        supplied = {
            case_id: {
                "generation_path": "",
                "composer_source": "ai_generated",
                "semantic_quality_gate": "",
                "public_reply_path_connected": False,
            }
            for case_id in ("A", "B", "C", "D")
        }
        assessments = [
            assess_i7_device_evidence(case_id=case_id, evidence_meta=meta)
            for case_id, meta in supplied.items()
        ]
        self.assertTrue(all(item.evidence_status == "runtime_mismatch" for item in assessments))
        self.assertTrue(
            all("canonical_generation_path_not_verified" in item.reason_refs for item in assessments)
        )
        self.assertTrue(
            all("grounded_plan_realizer_not_verified" in item.reason_refs for item in assessments)
        )
        for item in assessments:
            _assert_body_free(self, item.as_body_free_meta())

    def test_stale_or_incomplete_device_lane_blocks_p5_formal_24(self) -> None:
        local = []
        for case in (
            *GROUND_OBSERVATION_I0_KNOWN_REGRESSION_CASES,
            *GROUND_OBSERVATION_I6_BLIND_CASES,
        ):
            reply = _render(case.as_current_input())
            local.append(
                assess_i7_local_surface(
                    case_id=case.case_id,
                    surface_text=reply.comment_text,
                    grounded_meta=reply.meta["grounded_observation"],
                )
            )
        stale_device = [
            assess_i7_device_evidence(
                case_id=case_id,
                evidence_meta={"composer_source": "ai_generated"},
            )
            for case_id in ("A", "B", "C", "D")
        ]
        decision = decide_i7_progression(
            local_assessments=local,
            device_assessments=stale_device,
        )
        self.assertTrue(decision["local_product_read_candidate_ready"])
        self.assertFalse(decision["actual_local_human_ready"])
        self.assertFalse(decision["current_input_baseline_verified"])
        self.assertEqual(24, decision["p5_formal_required_case_count"])
        self.assertFalse(decision["p5_formal_24_start_allowed"])
        self.assertFalse(decision["p5_formal_24_started_here"])
        self.assertEqual(
            "return_to_current_input_surface_repair",
            decision["next_action_ref"],
        )
        self.assertFalse(decision["p6_start_allowed"])
        self.assertFalse(decision["p8_start_allowed"])
        _assert_body_free(self, decision)

    def test_eight_canonical_device_records_cannot_replace_actual_local_review(self) -> None:
        local = []
        for case in (
            *GROUND_OBSERVATION_I0_KNOWN_REGRESSION_CASES,
            *GROUND_OBSERVATION_I6_BLIND_CASES,
        ):
            reply = _render(case.as_current_input())
            local.append(
                assess_i7_local_surface(
                    case_id=case.case_id,
                    surface_text=reply.comment_text,
                    grounded_meta=reply.meta["grounded_observation"],
                )
            )
        canonical_meta = {
            "generation_path": I7_CANONICAL_GENERATION_PATH,
            "composer_source": I7_CANONICAL_COMPOSER_SOURCE,
            "semantic_quality_gate": "passed",
            "public_reply_path_connected": True,
        }
        device = [
            assess_i7_device_evidence(case_id=f"device-{index}", evidence_meta=canonical_meta)
            for index in range(1, 9)
        ]
        decision = decide_i7_progression(
            local_assessments=local,
            device_assessments=device,
        )
        self.assertFalse(decision["current_input_baseline_verified"])
        self.assertFalse(decision["p5_formal_24_start_allowed"])
        self.assertFalse(decision["p5_formal_24_started_here"])
        self.assertEqual("return_to_current_input_surface_repair", decision["next_action_ref"])
        self.assertFalse(decision["p6_start_allowed"])
        self.assertFalse(decision["p8_start_allowed"])

    def test_explicit_sixteen_local_pass_receipts_and_eight_devices_open_p5_entry(self) -> None:
        cases = (
            *GROUND_OBSERVATION_I0_KNOWN_REGRESSION_CASES,
            *GROUND_OBSERVATION_I6_BLIND_CASES,
        )
        local = []
        for case in cases:
            reply = _render(case.as_current_input())
            local.append(
                assess_i7_local_surface(
                    case_id=case.case_id,
                    surface_text=reply.comment_text,
                    grounded_meta=reply.meta["grounded_observation"],
                )
            )
        canonical_meta = {
            "generation_path": I7_CANONICAL_GENERATION_PATH,
            "composer_source": I7_CANONICAL_COMPOSER_SOURCE,
            "semantic_quality_gate": "passed",
            "public_reply_path_connected": True,
        }
        device = [
            assess_i7_device_evidence(case_id=f"device-{index}", evidence_meta=canonical_meta)
            for index in range(1, 9)
        ]
        decision = decide_i7_progression(
            local_assessments=local,
            actual_local_reviews=_explicit_passed_reviews(case.case_id for case in cases),
            device_assessments=device,
        )
        self.assertTrue(decision["actual_local_human_ready"])
        self.assertTrue(decision["current_input_baseline_verified"])
        self.assertTrue(decision["p5_formal_24_start_allowed"])
        self.assertEqual("start_p5_formal_24_owned_history_blind_qa", decision["next_action_ref"])


if __name__ == "__main__":
    unittest.main()
