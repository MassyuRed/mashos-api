# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json
import unittest
from dataclasses import fields, replace
from unittest.mock import patch

from emlis_ai_current_input_bundle import build_emlis_current_input_bundle
from cocolon_meaning_experience_engine import EngineStatus, GenerationRequest, MeaningExperienceEngine
from cocolon_meaning_experience_engine.contracts import (
    AttachmentAdmission,
    OwnerClass,
    ProviderResolution,
    RouteBDisposition,
    RouteBOwnerDisposition,
    VisibleAuthority,
)
from cocolon_meaning_experience_engine.source_kernel import (
    SourceAdmissionError,
    _evidence_id,
    _source_envelope_id,
    build_source_owner_universe,
    freeze_text_source,
    normalize_evidence_literal,
)


SAMPLE_MEMO = "仕事が続いて疲れていて、朝から何も手につかない。"


def _with_recomputed_evidence_id(row: object) -> object:
    return replace(
        row,
        evidence_id=_evidence_id(
            envelope_id=row.source_envelope_id,
            source_span_id=row.source_span_id,
            field_path=row.field_path,
            element_index=row.element_index,
            field_utf8_start=row.field_utf8_start,
            field_utf8_end=row.field_utf8_end,
            scalar_start=row.scalar_start,
            scalar_end=row.scalar_end,
            utf8_start=row.utf8_start,
            utf8_end=row.utf8_end,
            field_sha256=row.field_sha256,
            literal_sha256=row.literal_sha256,
        ),
    )


def _request(
    *,
    record_id: str = "cmee-contract-1",
    memo: str = SAMPLE_MEMO,
    action: str = "",
    category: str = "生活",
    emotion: str = "不安",
    strength: str = "medium",
    **request_overrides: object,
) -> GenerationRequest:
    raw = {
        "id": record_id,
        "created_at": "2026-08-15T00:00:00Z",
        "memo": memo,
        "memo_action": action,
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
            "scalar_start",
            "scalar_end",
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
        self.assertEqual(report["unknown_unit_count"], 1)
        self.assertEqual(report["unknown_trace_count"], 1)
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
        self.assertEqual(
            source.envelope.source_contract_version,
            "cocolon.cmee.emlis.current_input.text_grounded.v2",
        )
        self.assertGreaterEqual(len(source.evidence_refs), 4)
        self.assertEqual(len({row.evidence_id for row in source.evidence_refs}), len(source.evidence_refs))
        for ref in source.evidence_refs:
            selected = source.envelope.raw_utf8[ref.utf8_start : ref.utf8_end]
            self.assertEqual(hashlib.sha256(selected).hexdigest(), ref.literal_sha256)
            field = source.envelope.raw_utf8[ref.field_utf8_start : ref.field_utf8_end]
            self.assertEqual(hashlib.sha256(field).hexdigest(), ref.field_sha256)
            field_text = field.decode("utf-8")
            self.assertEqual(
                field_text[ref.scalar_start : ref.scalar_end].encode("utf-8"),
                selected,
            )
            self.assertEqual(
                ref.utf8_start,
                ref.field_utf8_start
                + len(field_text[: ref.scalar_start].encode("utf-8")),
            )
            self.assertEqual(
                ref.utf8_end,
                ref.field_utf8_start
                + len(field_text[: ref.scalar_end].encode("utf-8")),
            )
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

    def test_owner_universe_recompute_rejects_forged_evidence_digests(self) -> None:
        source = freeze_text_source(_request())
        category_index = next(
            index
            for index, row in enumerate(source.evidence_refs)
            if row.field_path == "category.0"
        )
        forged_refs = list(source.evidence_refs)
        forged_refs[category_index] = replace(
            forged_refs[category_index],
            evidence_id="ev-000000000000000000000000",
            literal_sha256="0" * 64,
            field_sha256="0" * 64,
        )

        with self.assertRaisesRegex(SourceAdmissionError, "evidence_digest_invalid"):
            build_source_owner_universe(source.envelope, tuple(forged_refs))

    def test_scalar_and_utf8_ranges_identify_the_same_repeated_occurrence(self) -> None:
        source = freeze_text_source(
            _request(record_id="cmee-scalar-occurrence", memo="🙂同じ。🙂同じ。")
        )
        memo_rows = tuple(row for row in source.evidence_refs if row.field_path == "memo")
        self.assertEqual(len(memo_rows), 2)
        first, second = memo_rows
        self.assertEqual(
            source.envelope.raw_utf8[first.utf8_start : first.utf8_end],
            source.envelope.raw_utf8[second.utf8_start : second.utf8_end],
        )
        self.assertNotEqual(
            (first.scalar_start, first.scalar_end),
            (second.scalar_start, second.scalar_end),
        )
        self.assertNotEqual(
            (first.utf8_start, first.utf8_end),
            (second.utf8_start, second.utf8_end),
        )

        forged = _with_recomputed_evidence_id(
            replace(
                first,
                scalar_start=second.scalar_start,
                scalar_end=second.scalar_end,
            )
        )
        forged_refs = tuple(forged if row is first else row for row in source.evidence_refs)
        with self.assertRaisesRegex(SourceAdmissionError, "canonical_binding_invalid"):
            build_source_owner_universe(source.envelope, forged_refs)

        bool_forged = _with_recomputed_evidence_id(replace(first, scalar_start=True))
        bool_refs = tuple(
            bool_forged if row is first else row for row in source.evidence_refs
        )
        with self.assertRaisesRegex(SourceAdmissionError, "canonical_binding_invalid"):
            build_source_owner_universe(source.envelope, bool_refs)

    def test_whitespace_mapping_preserves_raw_bytes_and_engine_validation(self) -> None:
        memo = "  仕事が  続いて\t疲れていて、\u3000\u3000朝から何も手につかない。  "
        request = _request(record_id="cmee-whitespace", memo=memo)
        source = freeze_text_source(request)
        memo_rows = tuple(row for row in source.evidence_refs if row.field_path == "memo")

        self.assertEqual(len(memo_rows), 1)
        row = memo_rows[0]
        field_text = source.envelope.raw_utf8[
            row.field_utf8_start : row.field_utf8_end
        ].decode("utf-8")
        literal = source.envelope.raw_utf8[row.utf8_start : row.utf8_end].decode(
            "utf-8"
        )
        self.assertEqual(field_text, memo)
        self.assertEqual(
            literal,
            "仕事が  続いて\t疲れていて、\u3000\u3000朝から何も手につかない",
        )
        self.assertEqual(field_text[row.scalar_start : row.scalar_end], literal)
        span = next(
            span
            for span in source.evidence_spans
            if str(getattr(span, "span_id", "")) == row.source_span_id
        )
        self.assertEqual(
            normalize_evidence_literal(literal),
            str(getattr(span, "raw_text", "")),
        )

        outcome = MeaningExperienceEngine().generate(request)
        self.assertEqual(outcome.status, EngineStatus.LIMITED, outcome.reason_codes)
        self.assertIsNotNone(outcome.artifact)

    def test_canonical_field_binding_rejects_coordinated_other_field_redirect(self) -> None:
        source = freeze_text_source(_request(record_id="cmee-field-redirect"))
        category_index = next(
            index
            for index, row in enumerate(source.evidence_refs)
            if row.field_path == "category.0"
        )
        category = source.evidence_refs[category_index]
        memo = next(row for row in source.evidence_refs if row.field_path == "memo")
        redirected = _with_recomputed_evidence_id(
            replace(
                category,
                field_utf8_start=memo.field_utf8_start,
                field_utf8_end=memo.field_utf8_end,
                scalar_start=memo.scalar_start,
                scalar_end=memo.scalar_end,
                utf8_start=memo.utf8_start,
                utf8_end=memo.utf8_end,
                field_sha256=memo.field_sha256,
                literal_sha256=memo.literal_sha256,
            )
        )
        forged_refs = list(source.evidence_refs)
        forged_refs[category_index] = redirected

        with self.assertRaisesRegex(SourceAdmissionError, "canonical_binding_invalid"):
            build_source_owner_universe(source.envelope, tuple(forged_refs))

    def test_canonical_source_span_binding_rejects_equal_literal_swap(self) -> None:
        source = freeze_text_source(_request(record_id="cmee-span-swap"))
        detail_index = next(
            index
            for index, row in enumerate(source.evidence_refs)
            if row.field_path == "emotion_details.0.type"
        )
        simple_index = next(
            index
            for index, row in enumerate(source.evidence_refs)
            if row.field_path == "emotions.0"
        )
        detail = source.evidence_refs[detail_index]
        simple = source.evidence_refs[simple_index]
        self.assertEqual(detail.literal_sha256, simple.literal_sha256)
        forged_refs = list(source.evidence_refs)
        forged_refs[detail_index] = _with_recomputed_evidence_id(
            replace(detail, source_span_id=simple.source_span_id)
        )
        forged_refs[simple_index] = _with_recomputed_evidence_id(
            replace(simple, source_span_id=detail.source_span_id)
        )

        with self.assertRaisesRegex(SourceAdmissionError, "canonical_binding_invalid"):
            build_source_owner_universe(source.envelope, tuple(forged_refs))

    def test_source_envelope_metadata_is_independently_reconstructed(self) -> None:
        source = freeze_text_source(_request(record_id="cmee-envelope-identity"))
        mutations = {
            "source_record_id": "different-record",
            "source_schema_version": "emlis.current_input_bundle.v999",
            "label_contract_id": "cocolon.input_options.forged",
            "label_contract_digest": "0" * 64,
        }
        for field_name, value in mutations.items():
            with self.subTest(field_name=field_name):
                tampered = replace(source.envelope, **{field_name: value})
                with self.assertRaisesRegex(SourceAdmissionError, "source_envelope"):
                    build_source_owner_universe(tampered, source.evidence_refs)

        changed_record = "coordinated-different-record"
        coordinated_id = _source_envelope_id(
            source_record_id=changed_record,
            source_role=source.envelope.source_role,
            source_schema_version=source.envelope.source_schema_version,
            source_contract_version=source.envelope.source_contract_version,
            source_encoding=source.envelope.source_encoding,
            label_contract_id=source.envelope.label_contract_id,
            label_contract_digest=source.envelope.label_contract_digest,
            raw_sha256=source.envelope.raw_sha256,
        )
        coordinated_envelope = replace(
            source.envelope,
            source_record_id=changed_record,
            envelope_id=coordinated_id,
        )
        coordinated_refs = tuple(
            _with_recomputed_evidence_id(
                replace(row, source_envelope_id=coordinated_id)
            )
            for row in source.evidence_refs
        )
        with self.assertRaisesRegex(SourceAdmissionError, "source_envelope_identity"):
            build_source_owner_universe(coordinated_envelope, coordinated_refs)

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

    def test_route_b_owner_disposition_has_the_complete_approved_shape(self) -> None:
        self.assertEqual(
            tuple(row.name for row in fields(RouteBOwnerDisposition)),
            (
                "meaning_owner_id",
                "owner_class",
                "provider_resolution",
                "attachment_admission",
                "visible_authority",
                "route_b_disposition",
                "visible_claim_refs",
                "evidence_refs",
                "target_unknown_ref",
                "reason_codes",
            ),
        )
        self.assertEqual({row.value for row in OwnerClass}, {"REQUIRED", "ACTIVE_OPTIONAL"})
        self.assertEqual(
            {row.value for row in ProviderResolution},
            {"UNIQUE", "AMBIGUOUS", "UNRESOLVED", "MISSING_OR_INVALID"},
        )
        self.assertEqual(
            {row.value for row in AttachmentAdmission},
            {"PROVISIONAL_ONLY", "UNRESOLVED", "UNAVAILABLE"},
        )
        self.assertEqual(
            {row.value for row in VisibleAuthority},
            {"SOURCE_EXPLICIT", "SUPPLEMENTAL_USER", "NONE"},
        )

    def test_owner_universe_is_frozen_from_source_before_the_legacy_plan(self) -> None:
        with patch(
            "cocolon_meaning_experience_engine.emlis_v1a.build_grounded_observation_plan",
            side_effect=AssertionError("legacy plan must not define U"),
        ):
            source = freeze_text_source(_request())

        universe = source.owner_universe
        source_obligations = tuple(
            row
            for row in universe.obligations
            if row.obligation_kind != "STRUCTURED_CONTEXT_ATTACHMENT"
        )
        self.assertEqual(
            {evidence_id for row in source_obligations for evidence_id in row.evidence_refs},
            {row.evidence_id for row in source.evidence_refs},
        )
        self.assertEqual(
            sum(len(row.evidence_refs) for row in source_obligations),
            len(source.evidence_refs),
        )
        self.assertEqual(
            tuple(row.meaning_owner_id for row in universe.obligations),
            universe.required_owner_refs + universe.active_optional_owner_refs,
        )
        self.assertEqual(len(universe.credit_only_owner_refs), 1)
        emotion_owner = next(
            row for row in universe.obligations if row.obligation_kind == "EMOTION_CONTEXT"
        )
        self.assertEqual(len(emotion_owner.evidence_refs), 2)
        attachment_owner = next(
            row
            for row in universe.obligations
            if row.obligation_kind == "STRUCTURED_CONTEXT_ATTACHMENT"
        )
        self.assertEqual(attachment_owner.owner_class, OwnerClass.ACTIVE_OPTIONAL)
        self.assertTrue(attachment_owner.evidence_refs)
        self.assertEqual(
            freeze_text_source(_request()).owner_universe,
            universe,
        )

        other = freeze_text_source(_request(record_id="cmee-contract-2"))
        self.assertNotEqual(
            other.owner_universe.owner_universe_digest,
            universe.owner_universe_digest,
        )
        self.assertTrue(
            set(other.owner_universe.required_owner_refs).isdisjoint(
                universe.required_owner_refs
            )
        )
        with_action = freeze_text_source(
            _request(
                record_id="cmee-contract-action",
                action="今日は早く休んだ。",
            )
        )
        self.assertEqual(len(with_action.owner_universe.required_owner_refs), 2)
        self.assertEqual(with_action.owner_universe.credit_only_owner_refs, ())

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
