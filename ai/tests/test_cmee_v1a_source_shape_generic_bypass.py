from __future__ import annotations

from types import SimpleNamespace
import unittest

import cocolon_meaning_experience_engine.emlis_v1a as emlis_v1a
from cocolon_meaning_experience_engine.emlis_v1a import CMEEVerticalError


def _nucleus(
    *,
    kind: str,
    modality: str,
    attributes: tuple[str, ...] = (),
) -> SimpleNamespace:
    return SimpleNamespace(
        kind=kind,
        semantic_frame=SimpleNamespace(
            modality=modality,
            attribute_codes=attributes,
        ),
    )


class CMEEV1ASourceShapeGenericBypassTest(unittest.TestCase):
    def test_bounded_malformed_special_shapes_remain_fail_closed(self) -> None:
        rows = (
            (
                _nucleus(
                    kind="state",
                    modality="fact",
                    attributes=("operator:positive_change",),
                ),
                "疲れたけど散歩なら落ち着いた",
            ),
            (
                _nucleus(
                    kind="state",
                    modality="fact",
                    attributes=("operator:positive_change",),
                ),
                "散歩したくて気分が軽かった",
            ),
            (
                _nucleus(kind="wish", modality="wish"),
                "続けたいけど晴れている",
            ),
            (
                _nucleus(kind="wish", modality="wish"),
                "けど続けたい",
            ),
        )
        for nucleus, value in rows:
            with self.subTest(value=value):
                with self.assertRaisesRegex(
                    CMEEVerticalError,
                    "stage1_source_shape_malformed",
                ):
                    emlis_v1a._cmee_validate_typed_source_shape(
                        nucleus,
                        value,
                    )

    def test_over_limit_or_untyped_hits_return_to_generic_source_role(self) -> None:
        rows = (
            (
                _nucleus(
                    kind="reaction",
                    modality="feeling",
                    attributes=("operator:positive_change",),
                ),
                "下書きを何度も読み返してから整えてうれしかった",
            ),
            (
                _nucleus(
                    kind="wish",
                    modality="wish",
                    attributes=(
                        "operator:positive_change",
                        "operator:contrast",
                        "semantic_role:retained_intention",
                    ),
                ),
                "役目を優先して選ぶことが多かったけれど、"
                "すぐ成果にならなくても心に残ることへ時間を使いたいと思うようになった",
            ),
            (
                _nucleus(
                    kind="other_explicit",
                    modality="fact",
                    attributes=("operator:contrast",),
                ),
                "以前の判断を悔やんでいるけど、今は知らせたい",
            ),
            (
                _nucleus(
                    kind="other_explicit",
                    modality="wish",
                    attributes=(
                        "operator:contrast",
                        "semantic_role:retained_intention",
                        "semantic_role:embedded_turn",
                    ),
                ),
                "以前の選択を悔やんでいるけど、今は知らせたい",
            ),
        )
        for nucleus, value in rows:
            with self.subTest(value=value):
                emlis_v1a._cmee_validate_typed_source_shape(nucleus, value)


if __name__ == "__main__":
    unittest.main()
