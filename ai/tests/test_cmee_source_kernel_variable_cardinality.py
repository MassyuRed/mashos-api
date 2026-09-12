# -*- coding: utf-8 -*-
from __future__ import annotations

"""Source admission invariants for canonical variable-cardinality labels."""

import unittest

from emlis_ai_current_input_bundle import build_emlis_current_input_bundle
from cocolon_meaning_experience_engine.contracts import GenerationRequest
from cocolon_meaning_experience_engine.source_kernel import (
    SourceAdmissionError,
    build_source_owner_universe,
    freeze_text_source,
)


def _request(
    *,
    record_id: str,
    thought: str,
    action: str,
    categories: tuple[str, ...],
    emotions: tuple[tuple[str, str], ...],
) -> GenerationRequest:
    raw = {
        "id": record_id,
        "created_at": "2026-08-15T00:00:00Z",
        "memo": thought,
        "memo_action": action,
        "category": list(categories),
        "emotion_details": [
            {"type": emotion, "strength": strength}
            for emotion, strength in emotions
        ],
        "emotions": [emotion for emotion, _strength in emotions],
        "is_secret": False,
    }
    return GenerationRequest(
        request_id=f"req-{record_id}",
        current_input_bundle=build_emlis_current_input_bundle(raw),
        expected_source_record_id=record_id,
    )


class CMEESourceKernelVariableCardinalityTest(unittest.TestCase):
    def test_historical_exact1_source_identity_is_bit_stable(self) -> None:
        source = freeze_text_source(
            _request(
                record_id="cmee-contract-1",
                thought="仕事が続いて疲れていて、朝から何も手につかない。",
                action="",
                categories=("生活",),
                emotions=(("不安", "medium"),),
            )
        )

        self.assertEqual(source.envelope.envelope_id, "src-4f7e691bd0dbbaf94fadbd0f")
        self.assertEqual(
            source.envelope.raw_sha256,
            "80462b09efe627c2221b637bf0338f212a681462cc791fd4db101e87910fdeb7",
        )
        self.assertEqual(
            tuple(row.evidence_id for row in source.evidence_refs),
            (
                "ev-675a06f2b40139177ff86bcf",
                "ev-d3c6c68e36afdf77bf8c7ac5",
                "ev-42d3f17f60cb081e5aca5ce6",
                "ev-748abf6d407e4665e93a7796",
                "ev-f0ddb42b63130d5fb614c781",
            ),
        )
        self.assertEqual(
            source.owner_universe.owner_universe_digest,
            "c97712c83fd358e178236c2963bebb6a5103348f3aabb3988a5df3c2dcbe8f14",
        )

    def test_all_ordered_labels_have_distinct_frame_evidence_and_owners(self) -> None:
        categories = ("生活", "仕事", "学習", "価値観")
        emotions = (("不安", "strong"), ("喜び", "weak"), ("平穏", "medium"))
        source = freeze_text_source(
            _request(
                record_id="cmee-source-variable",
                thought="考えは残っている。",
                action="一つ試した。",
                categories=categories,
                emotions=emotions,
            )
        )

        self.assertEqual(source.categories, categories)
        self.assertEqual(source.emotions, tuple(row[0] for row in emotions))
        self.assertEqual(source.strengths, tuple(row[1] for row in emotions))
        structured_refs = tuple(
            row
            for row in source.evidence_refs
            if row.field_path not in {"memo", "memo_action"}
        )
        expected_paths = (
            *(f"emotion_details.{index}.type" for index in range(3)),
            *(f"emotions.{index}" for index in range(3)),
            *(f"category.{index}" for index in range(4)),
            *(f"emotion_details.{index}.strength" for index in range(3)),
        )
        self.assertEqual(tuple(row.field_path for row in structured_refs), expected_paths)
        self.assertEqual(
            tuple(row.element_index for row in structured_refs),
            (0, 1, 2, 0, 1, 2, 0, 1, 2, 3, 0, 1, 2),
        )
        self.assertEqual(
            tuple(
                source.envelope.raw_utf8[row.utf8_start : row.utf8_end].decode(
                    "utf-8"
                )
                for row in structured_refs
            ),
            (
                "不安",
                "喜び",
                "平穏",
                "不安",
                "喜び",
                "平穏",
                "生活",
                "仕事",
                "学習",
                "価値観",
                "strong",
                "weak",
                "medium",
            ),
        )
        self.assertEqual(
            len({row.source_span_id for row in source.evidence_refs}),
            len(source.evidence_refs),
        )
        self.assertEqual(
            len({row.evidence_id for row in source.evidence_refs}),
            len(source.evidence_refs),
        )

        obligations = {
            row.obligation_kind: row for row in source.owner_universe.obligations
        }
        self.assertEqual(
            obligations["EMOTION_CONTEXT"].evidence_refs,
            tuple(row.evidence_id for row in structured_refs[:6]),
        )
        self.assertEqual(
            obligations["CATEGORY_CONTEXT"].evidence_refs,
            tuple(row.evidence_id for row in structured_refs[6:10]),
        )
        self.assertEqual(
            obligations["EMOTION_STRENGTH_CONTEXT"].evidence_refs,
            tuple(row.evidence_id for row in structured_refs[10:]),
        )
        base = tuple(
            row
            for row in source.owner_universe.obligations
            if row.obligation_kind != "STRUCTURED_CONTEXT_ATTACHMENT"
        )
        self.assertEqual(
            tuple(evidence_id for row in base for evidence_id in row.evidence_refs),
            tuple(row.evidence_id for row in source.evidence_refs),
        )

    def test_list_order_and_nonfirst_values_bind_all_source_identities(self) -> None:
        def admitted(
            categories: tuple[str, ...],
            emotions: tuple[tuple[str, str], ...],
        ):
            return freeze_text_source(
                _request(
                    record_id="cmee-source-list-binding",
                    thought="同じ本文。",
                    action="同じ行動。",
                    categories=categories,
                    emotions=emotions,
                )
            )

        sources = (
            admitted(("生活", "仕事"), (("不安", "strong"), ("喜び", "weak"))),
            admitted(("生活", "趣味"), (("不安", "strong"), ("喜び", "weak"))),
            admitted(("仕事", "生活"), (("不安", "strong"), ("喜び", "weak"))),
            admitted(("生活", "仕事"), (("不安", "strong"), ("平穏", "weak"))),
            admitted(("生活", "仕事"), (("喜び", "weak"), ("不安", "strong"))),
        )
        self.assertEqual(len({row.envelope.envelope_id for row in sources}), len(sources))
        self.assertEqual(len({row.envelope.raw_sha256 for row in sources}), len(sources))
        self.assertEqual(
            len({row.owner_universe.owner_universe_digest for row in sources}),
            len(sources),
        )

    def test_action_only_source_is_required_and_missing_thought_is_credited(self) -> None:
        source = freeze_text_source(
            _request(
                record_id="cmee-source-action-only",
                thought="",
                action="今日は一つだけ片づけた。",
                categories=("生活", "仕事"),
                emotions=(("平穏", "medium"), ("喜び", "weak")),
            )
        )

        self.assertFalse(any(row.field_path == "memo" for row in source.evidence_refs))
        self.assertTrue(any(row.field_path == "memo_action" for row in source.evidence_refs))
        required = tuple(
            row.obligation_kind
            for row in source.owner_universe.obligations
            if row.meaning_owner_id in source.owner_universe.required_owner_refs
        )
        self.assertEqual(required, ("ACTION_MEANING",))
        self.assertEqual(len(source.owner_universe.credit_only_owner_refs), 1)

    def test_missing_one_nonfirst_ref_is_rejected_without_first_only_fallback(self) -> None:
        source = freeze_text_source(
            _request(
                record_id="cmee-source-missing-ref",
                thought="本文。",
                action="",
                categories=("生活", "仕事"),
                emotions=(("不安", "strong"), ("喜び", "weak")),
            )
        )
        refs = tuple(
            row for row in source.evidence_refs if row.field_path != "category.1"
        )
        with self.assertRaisesRegex(
            SourceAdmissionError,
            "evidence_canonical_binding_invalid",
        ):
            build_source_owner_universe(source.envelope, refs)


if __name__ == "__main__":
    unittest.main()
