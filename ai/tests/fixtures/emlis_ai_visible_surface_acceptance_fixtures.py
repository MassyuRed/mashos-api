# -*- coding: utf-8 -*-
from __future__ import annotations

"""Screenshot-derived visible-surface QA inventory for EmlisAI.

The inventory locks observed display-quality cases as QA material only.  It does
not prescribe a good replacement body and does not add runtime special cases.
Step1 adds the 2026-05-24 product-surface A/B/C and display-absent cases so
later guard implementation can fail before the new surface rules are wired and
pass after those rules are implemented.
"""

from dataclasses import dataclass, field
from typing import Literal

VISIBLE_SURFACE_ACCEPTANCE_INVENTORY_VERSION = "emlis.visible_surface_acceptance_inventory.v2"
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
    input_text_available: bool = False
    input_derived_surface_markers: tuple[str, ...] = field(default_factory=tuple)
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
        fixture_id="visible_surface_pass_low_information_positive_prompt_20260524_actual_A",
        source=VISIBLE_SURFACE_ACCEPTANCE_SOURCE,
        source_date="2026-05-24",
        classification="pass",
        public_body=(
            "今は、大切にしたい気持ちがあるように見えます。"
            "まだ詳しい出来事までは見えませんが、その日に感じたことは"
            "大切に置かれているように見えます。\n"
            "詳しく残せそうなら、何が変わったのか残してみませんか。"
        ),
        public_body_family_markers=(
            "まだ詳しい出来事までは見えません",
            "詳しく残せそうなら",
            "何が変わったのか残してみませんか",
        ),
        selected_emotions=(("喜び", "medium"),),
        visible_header_dominant_emotion="喜び",
        forbidden_surface_markers=("重さ", "負荷", "不安", "予感こと", "なければこと"),
        expected_action="allow",
        expected_public_status_after_gate="passed",
        notes=("actual A positive low-information regression from 2026-05-24 device check",),
    ),
    VisibleSurfaceAcceptanceFixture(
        fixture_id="visible_surface_red_conditional_koto_splice_20260524",
        source=VISIBLE_SURFACE_ACCEPTANCE_SOURCE,
        source_date="2026-05-24",
        classification="red",
        public_body=(
            "Emlisです。\n"
            "今は、戻ってきた不安が先に出ています。\n"
            "そこに、趣味のVRCでのイベントキャストにも顔を出して"
            "コス仲間とのコミュニケーションも取らなければことも加わっていて、"
            "状態が一色ではありません。"
        ),
        selected_emotions=(("不安", "medium"),),
        visible_header_dominant_emotion="不安",
        expected_rejection_reasons=(
            "malformed_phrase_unit",
            "malformed_nominalization_conditional_fragment",
            "residual_koto_splice_fragment",
        ),
        forbidden_surface_markers=("なければこと", "取らなければこと"),
        expected_action="rerender_surface",
        expected_public_status_after_gate="not_passed",
        notes=(
            "actual C-family malformed conditional+koto splice from 2026-05-24 device check",
            "bad surface only",
            "no fixed replacement body",
        ),
    ),
    VisibleSurfaceAcceptanceFixture(
        fixture_id="visible_surface_red_prediction_noun_koto_splice_20260524",
        source=VISIBLE_SURFACE_ACCEPTANCE_SOURCE,
        source_date="2026-05-24",
        classification="red",
        public_body=(
            "Emlisです。\n"
            "さらに、色んな自分がありすぎてキャパオーバーしそうな予感こともあり、"
            "今見えている範囲は一つの要素だけではありません。"
        ),
        selected_emotions=(("不安", "medium"),),
        visible_header_dominant_emotion="不安",
        expected_rejection_reasons=(
            "malformed_phrase_unit",
            "malformed_nominalization_prediction_noun_fragment",
            "residual_koto_splice_fragment",
        ),
        forbidden_surface_markers=("予感こと", "気配こと"),
        expected_action="rerender_surface",
        expected_public_status_after_gate="not_passed",
        notes=(
            "actual C-family malformed prediction-noun+koto splice from 2026-05-24 device check",
            "bad surface only",
            "no fixed replacement body",
        ),
    ),
    VisibleSurfaceAcceptanceFixture(
        fixture_id="visible_surface_red_long_clause_koto_attachment_20260524",
        source=VISIBLE_SURFACE_ACCEPTANCE_SOURCE,
        source_date="2026-05-24",
        classification="red",
        public_body=(
            "Emlisです。\n"
            "今は、戻ってきた不安が先に出ています。\n"
            "そこに、趣味のVRCでのイベントキャストにも顔を出して"
            "コス仲間とのコミュニケーションも取らなければことも加わっていて、"
            "状態が一色ではありません。\n"
            "さらに、色んな自分がありすぎてキャパオーバーしそうな予感こともあり、"
            "今見えている範囲は一つの要素だけではありません。\n"
            "片方だけに減らさず、重なりとして並んで残っています。"
        ),
        selected_emotions=(("不安", "medium"),),
        visible_header_dominant_emotion="不安",
        expected_rejection_reasons=(
            "long_clause_koto_attachment_risk",
            "surface_relation_skeleton_major",
            "malformed_phrase_unit",
        ),
        forbidden_surface_markers=(
            "なければこと",
            "取らなければこと",
            "予感こと",
            "状態が一色ではありません",
            "一つの要素だけではありません",
        ),
        expected_action="rerender_surface",
        expected_public_status_after_gate="not_passed",
        notes=(
            "actual C full-surface family locks long raw relation attachment as red because it contains malformed koto splice",
            "long_clause_koto_attachment_risk alone can be downgraded to repair_required in later implementation",
            "no fixed replacement body",
        ),
    ),
    VisibleSurfaceAcceptanceFixture(
        fixture_id="visible_surface_repair_relation_skeleton_mechanical_20260524",
        source=VISIBLE_SURFACE_ACCEPTANCE_SOURCE,
        source_date="2026-05-24",
        classification="repair_required",
        public_body=(
            "Emlisです。\n"
            "今は、笑えたことが先に出ています。\n"
            "そこに、一日で全ての感情を網羅したことも加わっていて、"
            "状態が一色ではありません。\n"
            "片方だけに減らさず、重なりとして並んで残っています。"
        ),
        public_body_family_markers=("状態が一色ではありません", "片方だけに減らさず", "重なりとして並んで", "網羅"),
        selected_emotions=(("喜び", "medium"),),
        visible_header_dominant_emotion="喜び",
        input_text_available=False,
        expected_rejection_reasons=("surface_relation_skeleton_major", "analytic_register_leak"),
        forbidden_surface_markers=("状態が一色ではありません", "重なりとして並んで"),
        expected_action="rerender_surface",
        expected_public_status_after_gate="not_passed",
        notes=(
            "actual B-family mechanical relation skeleton stack from 2026-05-24 device check",
            "input text unavailable; not classified as over-read",
            "網羅 is not treated as overread without input text, but stacked analytic relation wording is repair material",
        ),
    ),
    VisibleSurfaceAcceptanceFixture(
        fixture_id="visible_surface_pass_mixed_emotion_layered_20260524",
        source=VISIBLE_SURFACE_ACCEPTANCE_SOURCE,
        source_date="2026-05-24",
        classification="repair_required",
        public_body_family_markers=("状態が一色ではありません", "片方だけに減らさず", "重なりとして並んで"),
        selected_emotions=(("平穏", "medium"), ("喜び", "medium")),
        visible_header_dominant_emotion="平穏",
        input_text_available=False,
        expected_rejection_reasons=("surface_relation_skeleton_major",),
        expected_action="rerender_surface",
        expected_public_status_after_gate="not_passed",
        notes=(
            "legacy fixture id kept for compatibility",
            "relation skeleton stack is no longer an unconditional pass family marker",
            "input-derived single marker can be reclassified by later gate implementation",
        ),
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
        fixture_id="visible_surface_fail_closed_no_observation_display_surface_block_20260524",
        source=VISIBLE_SURFACE_ACCEPTANCE_SOURCE,
        source_date="2026-05-24",
        classification="out_of_scope",
        public_body="",
        expected_rejection_reasons=(
            "runtime_surface_pre_return_gate_failed",
            "surface_template_major",
            "surface_grammar_warning",
            "malformed_nominalization_risk",
            "malformed_phrase_unit",
        ),
        expected_action="block",
        expected_public_status_after_gate="not_passed",
        notes=(
            "no visible body was shown in the device screenshot; inventory locks backend fail-closed diagnostic family only",
            "do not infer RN bug from this fixture",
        ),
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
