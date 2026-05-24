# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step0 screenshot-derived visible-surface QA inventory for EmlisAI.

The inventory locks observed display-quality cases as QA material only.  It does
not prescribe a good replacement body and does not add runtime special cases.
"""

from dataclasses import dataclass, field
from typing import Literal

VISIBLE_SURFACE_ACCEPTANCE_INVENTORY_VERSION = "emlis.visible_surface_acceptance_inventory.v1"
VISIBLE_SURFACE_ACCEPTANCE_SOURCE = "screenshot_2026_05_24"

VisibleSurfaceClassification = Literal["red", "repair_required", "yellow", "pass", "out_of_scope"]


@dataclass(frozen=True)
class VisibleSurfaceAcceptanceFixture:
    fixture_id: str
    source: str
    source_date: str
    classification: VisibleSurfaceClassification
    public_body: str = ""
    public_body_family_markers: tuple[str, ...] = field(default_factory=tuple)
    selected_emotions: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    visible_header_dominant_emotion: str = ""
    expected_rejection_reasons: tuple[str, ...] = field(default_factory=tuple)
    forbidden_surface_markers: tuple[str, ...] = field(default_factory=tuple)
    required_bridge_markers: tuple[str, ...] = field(default_factory=tuple)
    expected_action: str = "allow"
    expected_public_status_after_gate: str = "passed"
    notes: tuple[str, ...] = field(default_factory=tuple)


VISIBLE_SURFACE_ACCEPTANCE_SCREENSHOT_INVENTORY: tuple[VisibleSurfaceAcceptanceFixture, ...] = (
    VisibleSurfaceAcceptanceFixture(
        fixture_id="visible_surface_red_malformed_tari_koto_20260524",
        source=VISIBLE_SURFACE_ACCEPTANCE_SOURCE,
        source_date="2026-05-24",
        classification="red",
        public_body=(
            "Emlisです。\n"
            "今は、大切にしたい気持ちが先に出ています。\n"
            "さらに、無理に変えようとしたりこともあり、今見えている範囲は一つの要素だけではありません。"
        ),
        selected_emotions=(("平穏", "medium"),),
        visible_header_dominant_emotion="平穏",
        expected_rejection_reasons=("malformed_phrase_unit", "malformed_nominalization_tari_fragment"),
        forbidden_surface_markers=("したりこと", "たりこと"),
        expected_action="rerender_surface",
        expected_public_status_after_gate="not_passed",
        notes=("bad surface only", "no fixed replacement body"),
    ),
    VisibleSurfaceAcceptanceFixture(
        fixture_id="visible_surface_repair_unbridged_secondary_emotion_focus_20260524",
        source=VISIBLE_SURFACE_ACCEPTANCE_SOURCE,
        source_date="2026-05-24",
        classification="repair_required",
        public_body="今は、不安の重さが先に出ているように見えます。",
        selected_emotions=(("悲しみ", "medium"), ("不安", "medium")),
        visible_header_dominant_emotion="悲しみ",
        expected_rejection_reasons=("emotion_focus_unbridged_secondary",),
        required_bridge_markers=("悲しみ", "不安"),
        expected_action="rerender_surface",
        expected_public_status_after_gate="not_passed",
        notes=("secondary emotion is allowed only when bridged to the header-dominant emotion",),
    ),
    VisibleSurfaceAcceptanceFixture(
        fixture_id="visible_surface_pass_mixed_emotion_layered_20260524",
        source=VISIBLE_SURFACE_ACCEPTANCE_SOURCE,
        source_date="2026-05-24",
        classification="pass",
        public_body_family_markers=("状態が一色ではありません", "片方だけに減らさず", "重なりとして並んで"),
        selected_emotions=(("平穏", "medium"), ("喜び", "medium")),
        visible_header_dominant_emotion="平穏",
        expected_action="allow",
        expected_public_status_after_gate="passed",
        notes=("locks acceptable surface family markers, not one exact good sentence",),
    ),
    VisibleSurfaceAcceptanceFixture(
        fixture_id="visible_surface_pass_low_information_prompt_20260524",
        source=VISIBLE_SURFACE_ACCEPTANCE_SOURCE,
        source_date="2026-05-24",
        classification="pass",
        public_body_family_markers=(
            "まだ詳しい出来事までは見えません",
            "詳しく残せそうなら、何があったか残してみませんか",
        ),
        selected_emotions=(("不安", "medium"),),
        visible_header_dominant_emotion="不安",
        forbidden_surface_markers=("よければ、何がありましたか",),
        expected_action="allow",
        expected_public_status_after_gate="passed",
        notes=("low-information prompt wording from previous baseline remains acceptable",),
    ),
    VisibleSurfaceAcceptanceFixture(
        fixture_id="visible_surface_out_of_scope_user_account_display_20260524",
        source=VISIBLE_SURFACE_ACCEPTANCE_SOURCE,
        source_date="2026-05-24",
        classification="out_of_scope",
        public_body="Userさん、Emlisです。",
        expected_action="none",
        expected_public_status_after_gate="out_of_scope",
        notes=("User is the account display name in this local check and is not a red surface case",),
    ),
)


def iter_visible_surface_acceptance_screenshot_inventory() -> tuple[VisibleSurfaceAcceptanceFixture, ...]:
    return VISIBLE_SURFACE_ACCEPTANCE_SCREENSHOT_INVENTORY


__all__ = [
    "VISIBLE_SURFACE_ACCEPTANCE_INVENTORY_VERSION",
    "VISIBLE_SURFACE_ACCEPTANCE_SCREENSHOT_INVENTORY",
    "VISIBLE_SURFACE_ACCEPTANCE_SOURCE",
    "VisibleSurfaceAcceptanceFixture",
    "iter_visible_surface_acceptance_screenshot_inventory",
]
