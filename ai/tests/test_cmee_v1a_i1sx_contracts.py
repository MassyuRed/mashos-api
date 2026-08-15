# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json
import unittest

from emlis_ai_current_input_bundle import build_emlis_current_input_bundle
from cocolon_meaning_experience_engine import EngineStatus, GenerationRequest, MeaningExperienceEngine
from cocolon_meaning_experience_engine.contracts import RouteBDisposition
from cocolon_meaning_experience_engine.source_kernel import freeze_text_source


SAMPLE_MEMO = "仕事が続いて疲れていて、朝から何も手につかない。"


def _request(
    *,
    record_id: str = "cmee-contract-1",
    memo: str = SAMPLE_MEMO,
    category: str = "生活",
    emotion: str = "不安",
    strength: str = "medium",
    **request_overrides: object,
) -> GenerationRequest:
    raw = {
        "id": record_id,
        "created_at": "2026-08-15T00:00:00Z",
        "memo": memo,
        "memo_action": "",
        "category": [category],
        "emotion_details": [{"type": emotion, "strength": strength}],
        "emotions": [emotion],
        "is_secret": False,
    }
    values: dict[str, object] = {
        "request_id": f"req-{record_id}",
        "current_input_bundle": build_emlis_current_input_bundle(raw),
        "expected_source_record_id": record_id,
    }
    values.update(request_overrides)
    return GenerationRequest(**values)


class CMEEV1AI1SXContractsTest(unittest.TestCase):
    def test_body_free_projection_never_contains_private_body_digest_or_locator(self) -> None:
        outcome = MeaningExperienceEngine().generate(_request())

        self.assertEqual(outcome.status.value, "LIMITED", outcome.reason_codes)
        report = outcome.as_body_free()
        serialized = json.dumps(report, ensure_ascii=False, sort_keys=True)
        for forbidden in (
            "疲れている",
            "生活",
            "自己理解",
            "cmee-contract-1",
            "raw_sha256",
            "literal_sha256",
            "envelope_id",
            "graph_id",
            "artifact_id",
        ):
            self.assertNotIn(forbidden, serialized)
        self.assertNotIn("observation", report)
        self.assertNotIn("reception", report)
        self.assertEqual(report["status"], "LIMITED")
        self.assertTrue(report["artifact_present"])
        self.assertGreaterEqual(report["observation_unit_count"], 1)
        self.assertEqual(report["reception_unit_count"], 1)
        self.assertFalse(report["product_read_evaluated"])
        self.assertEqual(report["implementation_state"], "DRAFT_WIP_DISABLED")
        self.assertFalse(report["route_b_contract_complete"])
        self.assertFalse(report["candidate_ready"])
        self.assertFalse(report["product_read_eligible"])
        self.assertFalse(report["exact8_acceptance_complete"])
        self.assertEqual(report["production_effect"], 0)
        self.assertFalse(report["automatic_progression"])

    def test_source_envelope_locators_are_exact_and_bound_to_one_envelope(self) -> None:
        source = freeze_text_source(_request())
        self.assertGreaterEqual(len(source.evidence_refs), 4)
        self.assertEqual(len({row.evidence_id for row in source.evidence_refs}), len(source.evidence_refs))
        for ref in source.evidence_refs:
            selected = source.envelope.raw_utf8[ref.utf8_start : ref.utf8_end]
            self.assertEqual(hashlib.sha256(selected).hexdigest(), ref.literal_sha256)
            field = source.envelope.raw_utf8[ref.field_utf8_start : ref.field_utf8_end]
            self.assertEqual(hashlib.sha256(field).hexdigest(), ref.field_sha256)
            self.assertLessEqual(ref.field_utf8_start, ref.utf8_start)
            self.assertLessEqual(ref.utf8_end, ref.field_utf8_end)
            self.assertEqual(ref.source_envelope_id, source.envelope.envelope_id)
        memo_ref = next(row for row in source.evidence_refs if row.field_path == "memo")
        self.assertEqual(memo_ref.element_index, -1)
        strength_ref = next(
            row for row in source.evidence_refs if row.source_span_id == "structured:emotion_strength"
        )
        self.assertEqual(strength_ref.field_path, "emotion_details.0.strength")
        self.assertEqual(strength_ref.element_index, 0)

    def test_route_b_disposition_contract_is_exact_six(self) -> None:
        self.assertEqual(
            {row.value for row in RouteBDisposition},
            {
                "SOURCE_EXPLICIT_VISIBLE",
                "SUPPLEMENTAL_USER_VISIBLE",
                "UNKNOWN_PRESERVED_LIMITED",
                "CLARIFICATION_TARGET",
                "NOT_VISIBLE_UNRESOLVED",
                "SEPARATE_SAFETY",
            },
        )

    def test_engine_status_contract_is_exact_six(self) -> None:
        self.assertEqual(
            {row.value for row in EngineStatus},
            {
                "GENERATED",
                "LIMITED",
                "QUESTION_PENDING",
                "UNAVAILABLE",
                "SEPARATE_SAFETY",
                "REJECTED",
            },
        )

    def test_original_field_locators_preserve_whitespace_and_repeated_spans(self) -> None:
        request = _request(memo="　同じ。同じ。  ")
        source = freeze_text_source(request)
        memo_refs = tuple(row for row in source.evidence_refs if row.field_path == "memo")

        self.assertEqual(len(memo_refs), 2)
        self.assertNotEqual(memo_refs[0].utf8_start, memo_refs[1].utf8_start)
        field_bodies = {
            source.envelope.raw_utf8[row.field_utf8_start : row.field_utf8_end]
            for row in memo_refs
        }
        self.assertEqual(field_bodies, {"　同じ。同じ。  ".encode("utf-8")})
        self.assertEqual(
            [
                source.envelope.raw_utf8[row.utf8_start : row.utf8_end].decode("utf-8")
                for row in memo_refs
            ],
            ["同じ", "同じ"],
        )
        self.assertTrue(all(row.element_index == -1 for row in memo_refs))

    def test_wrong_core_job_and_mode_are_rejected_without_source_admission(self) -> None:
        engine = MeaningExperienceEngine()
        cases = (
            _request(core_id="piece"),
            _request(product_job="GENERATE_PIECE"),
            _request(execution_mode="PRODUCTION"),
        )
        for request in cases:
            with self.subTest(request=request):
                outcome = engine.generate(request)
                self.assertEqual(outcome.status.value, "REJECTED")
                self.assertIsNone(outcome.artifact)
                self.assertIsNone(outcome.source_envelope)
                self.assertFalse(outcome.automatic_progression)

    def test_source_lineage_violation_is_rejected_but_thin_input_is_unavailable(self) -> None:
        mismatch = MeaningExperienceEngine().generate(
            _request(expected_source_record_id="different-record")
        )
        labels_only = MeaningExperienceEngine().generate(_request(memo=""))

        self.assertEqual(mismatch.status.value, "REJECTED")
        self.assertEqual(mismatch.reason_codes, ("source_record_binding_mismatch",))
        self.assertIsNone(mismatch.artifact)
        self.assertEqual(labels_only.status.value, "UNAVAILABLE")
        self.assertEqual(labels_only.reason_codes, ("text_grounded_material_required",))
        self.assertIsNone(labels_only.artifact)


if __name__ == "__main__":
    unittest.main()
