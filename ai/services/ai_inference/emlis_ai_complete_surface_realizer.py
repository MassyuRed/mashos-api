# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step 7 Surface Realizer 2.0 for EmlisAI Complete Composer initial version.

Surface Realizer 2.0 turns a binding-first ``CompleteSentencePlanV2`` into
internal surface text using grammar parts: subject policy, role phrase,
particle, connector, predicate, ending, distance, and variation keys.  It does
not choose completed observation sentences by coverage group and it does not
write the public ``input_feedback.comment_text`` key.  Later Grounding /
Template / Display gates decide whether the internal surface can be promoted to
visible Emlis observation text.

The module is additive: DB physical names, API routes, public response keys and
RN display behavior are not changed.
"""

from dataclasses import dataclass, field as dataclass_field, is_dataclass, asdict
import re
from typing import Any, Iterable, Mapping, Sequence, Tuple

from emlis_ai_complete_composer_initial_meta import build_complete_composer_initial_term_meta
from emlis_ai_complete_composer_types import (
    COMPLETE_COMPOSER_STAGE,
    CompleteSentencePlanLine,
    CompleteSentencePlanV2,
)
from emlis_ai_complete_sentence_planner import (
    COMPLETE_SENTENCE_PLAN_STAGE,
    build_complete_sentence_plan_v2,
    build_complete_sentence_binding_bundle_meta,
)
from emlis_ai_complete_tone_policy import (
    COMPLETE_PRODUCT_QUALITY_TONE_ENGINE_VERSION,
    COMPLETE_TONE_ENGINE_STAGE,
    COMPLETE_TONE_ENGINE_VERSION,
    COMPLETE_TONE_ENGINE_2_1_VERSION,
    COMPLETE_TONE_POLICY_VERSION,
    COMPLETE_TONE_POLICY_2_1_VERSION,
    CompleteTonePolicy,
    build_complete_tone_guard_report,
    build_complete_tone_policy,
    build_complete_tone_policy_contract_meta,
    coerce_complete_tone_policy,
)
from emlis_ai_limited_relation_taxonomy import (
    canonical_relation_type,
    normalize_relation_type,
    relation_family,
)
from emlis_ai_relation_surface_contract import (
    RELATION_SURFACE_CONTRACT_VERSION,
    detect_relation_surface,
    relation_marker_key,
    relation_marker_meta,
)
from emlis_ai_complete_surface_realizer_anti_template import (
    COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_POLICY_VERSION,
    COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_STEP,
    COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_VERSION,
    build_surface_realizer_anti_template_policy_meta,
    build_surface_realizer_anti_template_report,
    connector_family_key as _anti_template_connector_family_key,
    ending_family_key as _anti_template_ending_family_key,
    opening_family_key as _anti_template_opening_family_key,
    predicate_family_key as _anti_template_predicate_family_key,
)
from emlis_ai_observation_surface_realizer import (
    OBSERVATION_SURFACE_REALIZER_STEP,
    OBSERVATION_SURFACE_REALIZER_VERSION,
    build_observation_surface_realizer_contract_meta,
)

COMPLETE_SURFACE_REALIZER_VERSION = "emlis.complete_surface_realizer.v2_1"
COMPLETE_SURFACE_REALIZER_2_0_VERSION = "emlis.complete_surface_realizer.v2"
COMPLETE_SURFACE_REALIZER_SERVICE_VERSION = COMPLETE_SURFACE_REALIZER_VERSION
COMPLETE_SURFACE_REALIZER_SCHEMA_VERSION = "emlis.complete_surface_realization.v2"
COMPLETE_SURFACE_LINE_SCHEMA_VERSION = "emlis.complete_surface_line.v2"
COMPLETE_SURFACE_SIGNATURE_SCHEMA_VERSION = "emlis.complete_surface_signature.v2"
COMPLETE_PRODUCT_QUALITY_SURFACE_VARIATION_VERSION = "emlis.complete_product_quality_surface_variation.v2"
COMPLETE_PRODUCT_QUALITY_SURFACE_VARIATION_STEP = "Step3_Surface_variation_strengthening"
COMPLETE_PRODUCT_QUALITY_SURFACE_VARIATION_SCHEMA_VERSION = "emlis.complete_product_quality_surface_variation_report.v2"
COMPLETE_SURFACE_VARIATION_POLICY_VERSION = "emlis.complete_surface_variation_policy.v2"
COMPLETE_SURFACE_VARIATION_PROFILE_VERSION = "emlis.complete_surface_variation_profile.v2"
COMPLETE_SURFACE_REALIZER_2_1_ANTI_TEMPLATE_VERSION = COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_VERSION
COMPLETE_SURFACE_REALIZER_2_1_ANTI_TEMPLATE_STEP = COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_STEP
COMPLETE_SURFACE_REALIZER_STAGE = "Step7_Surface_Realizer_2_0"
COMPLETE_SURFACE_REALIZER_STEP = COMPLETE_SURFACE_REALIZER_STAGE
COMPLETE_SURFACE_REALIZER_TARGET_STEP = COMPLETE_SURFACE_REALIZER_STAGE
COMPLETE_SURFACE_REALIZER_IMPLEMENTATION_UNIT = "Commit 7"
COMPLETE_SURFACE_RECOVERY_RELATION_LINE_ALIGNMENT_STEP = "Step4_Surface_recovery_relation_line_alignment"

COMPLETE_SURFACE_STATUS_READY = "ready"
COMPLETE_SURFACE_STATUS_UNAVAILABLE = "unavailable"
EMLIS_TWO_STAGE_SURFACE_REALIZATION_SCHEMA_VERSION = "cocolon.emlis_two_stage.surface_realization.v1"
EMLIS_TWO_STAGE_SURFACE_REALIZATION_SOURCE_PHASE = "Phase16_4_complete_surface_realizer_two_stage_comment_text"
EMLIS_TWO_STAGE_DAILY_UNPLEASANT_SURFACE_QUALITY_SCHEMA_VERSION = "cocolon.emlis_two_stage.daily_unpleasant_surface_quality.v1"
EMLIS_TWO_STAGE_DAILY_UNPLEASANT_SURFACE_QUALITY_SOURCE_PHASE = "Phase16_5_daily_unpleasant_reception_surface_quality"
EMLIS_TWO_STAGE_INTERNAL_ROLE_SURFACE_POLICY_SCHEMA_VERSION = "cocolon.emlis_two_stage.internal_role_surface_policy.v1"
EMLIS_TWO_STAGE_INTERNAL_ROLE_SURFACE_POLICY_SOURCE_PHASE = "Phase17_2_internal_role_surface_phrase_bank"
EMLIS_TWO_STAGE_INTERNAL_ROLE_SURFACE_PHRASE_SCHEMA_VERSION = EMLIS_TWO_STAGE_INTERNAL_ROLE_SURFACE_POLICY_SCHEMA_VERSION
EMLIS_TWO_STAGE_INTERNAL_ROLE_SURFACE_PHRASE_SOURCE_PHASE = EMLIS_TWO_STAGE_INTERNAL_ROLE_SURFACE_POLICY_SOURCE_PHASE
EMLIS_TWO_STAGE_MODE_SPECIFIC_SURFACE_POLICY_SCHEMA_VERSION = "cocolon.emlis_two_stage.mode_specific_surface_policy.v1"
EMLIS_TWO_STAGE_MODE_SPECIFIC_SURFACE_POLICY_SOURCE_PHASE = "Phase17_3_mode_specific_two_stage_surface_policy"
EMLIS_TWO_STAGE_MODE_CONTEXT_SCHEMA_VERSION = "cocolon.emlis.two_stage.mode_context.v1"
EMLIS_TWO_STAGE_MODE_CONTEXT_SOURCE_PHASE = "Phase18_product_quality_stabilization"
EMLIS_TWO_STAGE_PRODUCT_VISIBLE_SURFACE_POLICY_SCHEMA_VERSION = EMLIS_TWO_STAGE_MODE_SPECIFIC_SURFACE_POLICY_SCHEMA_VERSION
EMLIS_TWO_STAGE_PRODUCT_VISIBLE_SURFACE_POLICY_SOURCE_PHASE = EMLIS_TWO_STAGE_MODE_SPECIFIC_SURFACE_POLICY_SOURCE_PHASE
EMLIS_TWO_STAGE_PHASE17_SELF_REPAIR_REASON_SCHEMA_VERSION = "cocolon.emlis_two_stage.self_repair_unavailable_reason.v1"
EMLIS_TWO_STAGE_PHASE17_SELF_REPAIR_REASON_SOURCE_PHASE = "Phase17_7_self_repair_unavailable_reason"
EMLIS_TWO_STAGE_PHASE17_REASON_SURFACE_MODE_POLICY_MISSING = "phase17_surface_mode_policy_missing"
EMLIS_TWO_STAGE_PHASE17_REASON_INTERNAL_ROLE_LABEL_LEAK = "phase17_internal_role_label_leak"
EMLIS_TWO_STAGE_PHASE17_REASON_RELATION_SKELETON_LEAK = "phase17_relation_skeleton_leak"
EMLIS_TWO_STAGE_PHASE17_REASON_SECTION_BUDGET_MISMATCH = "phase17_section_budget_mismatch"
EMLIS_TWO_STAGE_PHASE17_REASON_GROUNDING_RELATION_BINDING_MISSING = "phase17_grounding_relation_binding_missing"
EMLIS_TWO_STAGE_PHASE17_REASON_PRODUCT_VISIBLE_FIXTURE_NOT_REACHED = "phase17_product_visible_fixture_not_reached"
EMLIS_TWO_STAGE_PHASE17_REASON_CODES: tuple[str, ...] = (
    EMLIS_TWO_STAGE_PHASE17_REASON_SURFACE_MODE_POLICY_MISSING,
    EMLIS_TWO_STAGE_PHASE17_REASON_INTERNAL_ROLE_LABEL_LEAK,
    EMLIS_TWO_STAGE_PHASE17_REASON_RELATION_SKELETON_LEAK,
    EMLIS_TWO_STAGE_PHASE17_REASON_SECTION_BUDGET_MISMATCH,
    EMLIS_TWO_STAGE_PHASE17_REASON_GROUNDING_RELATION_BINDING_MISSING,
    EMLIS_TWO_STAGE_PHASE17_REASON_PRODUCT_VISIBLE_FIXTURE_NOT_REACHED,
)
EMLIS_TWO_STAGE_DAILY_UNPLEASANT_RECEPTION_MODE_ID = "daily_unpleasant_reception"
EMLIS_TWO_STAGE_DAILY_UNPLEASANT_RATIO_REASON = "daily_unpleasant_reception_light"
EMLIS_TWO_STAGE_MODE_ID_BY_RATIO_REASON: dict[str, str] = {
    EMLIS_TWO_STAGE_DAILY_UNPLEASANT_RATIO_REASON: EMLIS_TWO_STAGE_DAILY_UNPLEASANT_RECEPTION_MODE_ID,
    "self_understanding_learning_shift": "self_understanding_learning_shift",
    "relationship_end_gratitude_recovery": "relationship_gratitude_recovery",
}
EMLIS_TWO_STAGE_COMMENT_TEXT_SHAPE = "labelled_two_stage_text"
EMLIS_TWO_STAGE_OBSERVATION_SECTION_ID = "observation"
EMLIS_TWO_STAGE_RECEPTION_SECTION_ID = "reception"
EMLIS_TWO_STAGE_SECTION_ORDER: tuple[str, str] = (
    EMLIS_TWO_STAGE_OBSERVATION_SECTION_ID,
    EMLIS_TWO_STAGE_RECEPTION_SECTION_ID,
)
EMLIS_TWO_STAGE_DEFAULT_COMMENT_TEXT_SECTION_LABELS: dict[str, str] = {
    EMLIS_TWO_STAGE_OBSERVATION_SECTION_ID: "見えたこと：",
    EMLIS_TWO_STAGE_RECEPTION_SECTION_ID: "Emlisから：",
}
EMLIS_TWO_STAGE_SELF_DENIAL_SUPPORT_MODE_IDS: frozenset[str] = frozenset({
    "self_denial_support",
    "uncertainty_support",
})
EMLIS_TWO_STAGE_DAILY_POSITIVE_RECEPTION_MODE_IDS: frozenset[str] = frozenset({
    "daily_positive_reception",
})
EMLIS_TWO_STAGE_SELF_UNDERSTANDING_FOLLOW_MODE_IDS: frozenset[str] = frozenset({
    "self_understanding_follow",
})
EMLIS_TWO_STAGE_SELF_UNDERSTANDING_LEARNING_SHIFT_MODE_IDS: frozenset[str] = frozenset({
    "self_understanding_learning_shift",
})
EMLIS_TWO_STAGE_RELATIONSHIP_GRATITUDE_RECOVERY_MODE_IDS: frozenset[str] = frozenset({
    "relationship_gratitude_recovery",
})
EMLIS_TWO_STAGE_EFFORT_PACE_MODE_IDS: frozenset[str] = frozenset({
    "standard_state_answer",
    "effort_support",
})
EMLIS_TWO_STAGE_MODE_SPECIFIC_SURFACE_POLICY_MODE_IDS: frozenset[str] = frozenset({
    EMLIS_TWO_STAGE_DAILY_UNPLEASANT_RECEPTION_MODE_ID,
    *EMLIS_TWO_STAGE_SELF_DENIAL_SUPPORT_MODE_IDS,
    *EMLIS_TWO_STAGE_DAILY_POSITIVE_RECEPTION_MODE_IDS,
    *EMLIS_TWO_STAGE_SELF_UNDERSTANDING_FOLLOW_MODE_IDS,
    *EMLIS_TWO_STAGE_SELF_UNDERSTANDING_LEARNING_SHIFT_MODE_IDS,
    *EMLIS_TWO_STAGE_RELATIONSHIP_GRATITUDE_RECOVERY_MODE_IDS,
    *EMLIS_TWO_STAGE_EFFORT_PACE_MODE_IDS,
})

SELF_DENIAL_SUPPORT_MODE_IDS = EMLIS_TWO_STAGE_SELF_DENIAL_SUPPORT_MODE_IDS
DAILY_POSITIVE_RECEPTION_MODE_IDS = EMLIS_TWO_STAGE_DAILY_POSITIVE_RECEPTION_MODE_IDS
SELF_UNDERSTANDING_FOLLOW_MODE_IDS = EMLIS_TWO_STAGE_SELF_UNDERSTANDING_FOLLOW_MODE_IDS
SELF_UNDERSTANDING_LEARNING_SHIFT_MODE_IDS = EMLIS_TWO_STAGE_SELF_UNDERSTANDING_LEARNING_SHIFT_MODE_IDS
RELATIONSHIP_GRATITUDE_RECOVERY_MODE_IDS = EMLIS_TWO_STAGE_RELATIONSHIP_GRATITUDE_RECOVERY_MODE_IDS
EFFORT_PACE_MODE_IDS = EMLIS_TWO_STAGE_EFFORT_PACE_MODE_IDS
TWO_STAGE_PRODUCT_VISIBLE_MODE_IDS = frozenset({
    EMLIS_TWO_STAGE_DAILY_UNPLEASANT_RECEPTION_MODE_ID,
    *EMLIS_TWO_STAGE_MODE_SPECIFIC_SURFACE_POLICY_MODE_IDS,
})

ANTI_TEMPLATE_SUPPRESSED_CONNECTOR_KEYS = {"sono_nakademo", "core_center"}
ANTI_TEMPLATE_GENERIC_CENTER_PREDICATE_KEYS = {"center_core"}

PHASE17_INTERNAL_ROLE_LABEL_RE = re.compile(
    r"\b(?:achievement|positive[ _]state|perfection[ _]fear|pressure[ _]or[ _]limit|role_[0-9a-zA-Z_\-]+)\b",
    re.IGNORECASE,
)
PHASE17_RELATION_SKELETON_RE = re.compile(
    r"同じ流れ|同じ場所|片方だけに寄らず|別々の向き|重なりを保っています|一方向には決まりきっていません"
)

RAW_INPUT_META_KEYS = {
    "raw_text",
    "raw_input",
    "input_text",
    "user_input",
    "current_input",
    "memo",
    "memo_text",
    "memo_action",
    "raw_user_text",
    "original_text",
    "source_text",
}

# Internal structural labels only.  They never come from raw input and are used
# only to decide whether a planned recovery relation line may mention prior load.
RECOVERY_PRIOR_LOAD_ROLE_KEYS = {
    "fatigue_accumulation",
    "load_accumulation",
    "limit_pressure",
    "pressure",
    "burden_fear",
    "hurt_core",
    "hurt_residue",
    "anticipation_loop",
    "small_wobble",
    "residue",
    "pressure_or_load",
}

# Roles from Material/Relation/SentencePlan.  Values are noun fragments, not
# completed observations.  They can be combined with particles and predicates.
ROLE_PHRASE_BANK: dict[str, tuple[str, str]] = {
    "fatigue_accumulation": ("疲れの蓄積", "load_accumulation"),
    "small_repair": ("小さな回復", "small_repair"),
    "value_wish": ("大切にしたい願い", "value_wish"),
    "wish_to_rely": ("近づきたい気持ち", "approach_wish"),
    "burden_fear": ("負担になる怖さ", "burden_fear"),
    "avoidance_wish": ("避けたい気持ち", "avoidance_wish"),
    "hurt_core": ("あとに残る痛み", "hurt_residue"),
    "anticipation_loop": ("先を考え続ける流れ", "anticipation_loop"),
    "known_action": ("前から続いている流れ", "known_context"),
    "safe_home": ("安心できる場所", "safe_place"),
    "current_expression": ("今出ている感覚", "current_expression"),
    "small_wobble": ("小さな揺れ", "small_wobble"),
    "limit_pressure": ("限界に近い圧力", "limit_pressure"),
    "relationship_distance": ("距離感の揺れ", "relationship_distance"),
    "self_reference": ("自分の側に残る反応", "self_side_response"),
    "primary_phrase": ("いま扱う核", "primary_phrase"),
    "explicit_negative_reaction": ("不快さや怖さを含む反応", "explicit_negative_reaction"),
    "negative_daily_reaction": ("日常の中で残った嫌な反応", "negative_daily_reaction"),
    "daily_event_fact": ("日常の出来事", "daily_event_fact"),
    "daily_unpleasant_event": ("日常の不快な出来事", "daily_unpleasant_event"),
    "fear_reaction": ("怖さを含む反応", "fear_reaction"),
    "anger_reaction": ("怒りを含む反応", "anger_reaction"),
    "disgust_reaction": ("不快さを含む反応", "disgust_reaction"),

    # Phase17-2: product-visible surface phrases for internal role labels.
    # These are role fragments, not completed reply templates. They prevent
    # English/internal labels from leaking into visible two-stage comment_text.
    "self_confidence_uncertainty": ("自信をつけたい気持ちと不安", "self_confidence_uncertainty"),
    "confidence_uncertainty": ("自信をつけたい気持ちと不安", "self_confidence_uncertainty"),
    "self_confidence_wish": ("自信をつけたい気持ち", "self_confidence_wish"),
    "self_denial": ("自分を否定する言葉", "self_denial_surface"),
    "attempt_to_change": ("直したい気持ち", "attempt_to_change"),
    "challenge_attempt": ("試している動き", "challenge_attempt"),
    "small_action": ("少し動けたこと", "small_action_surface"),
    "achievement": ("気持ちが動いた変化", "positive_change_movement"),
    "positive_change": ("気持ちが動いた変化", "positive_change_movement"),
    "joy_or_surprise": ("嬉しさと動揺", "joy_surprise_mixed"),
    "conversation_wish": ("誰かと話したい気持ち", "conversation_wish"),
    "work_fatigue": ("仕事後の疲れ", "work_fatigue"),
    "relieved_weight": ("少し軽くなった感じ", "relieved_weight_surface"),
    "perfection_fear": ("完璧に元気でいようとする怖さ", "perfection_fear_surface"),
    "self_blame_flow": ("自分を責める流れ", "self_blame_flow"),
    "gentle_self_observation": ("自分の気持ちを少し優しく見ようとする方向", "gentle_self_observation"),
    "positive_state": ("少し整えようとする動き", "gentle_recovery_direction"),
    "independence_intention": ("自立したい気持ち", "independence_intention"),
    "life_context": ("生活のこと", "life_context"),
    "health_pace": ("体調を見ながら続けるペース", "health_pace"),
    "money_context": ("お金のこと", "money_context"),
    "sustainable_pace": ("長く続けられるペース", "sustainable_pace"),
    "pressure_or_limit": ("急がせない境目", "pressure_or_limit_surface"),
    "closing": ("最後に残る受け取り", "closing_surface"),
}

INTERNAL_ROLE_SURFACE_FORBIDDEN_KEYS: frozenset[str] = frozenset({
    "achievement",
    "positive_state",
    "perfection_fear",
    "pressure_or_limit",
})
UNKNOWN_INTERNAL_ROLE_SURFACE_PHRASE = "根拠のある材料"
UNKNOWN_INTERNAL_ROLE_SURFACE_KEY = "unknown_internal_structural_label"
INTERNAL_ROLE_SURFACE_FORBIDDEN_PATTERN = re.compile(
    r"\b(?:achievement|positive\s+state|perfection\s+fear|pressure\s+or\s+limit)\b|role_",
    re.IGNORECASE,
)
UNKNOWN_ROLE_SURFACE_PHRASE_RULES: tuple[tuple[re.Pattern[str], tuple[str, str]], ...] = (
    (re.compile(r"(?:fear|scare|anxiety|worry|uncertain|uncertainty)"), ("不安や怖さを含む反応", "unknown_fear_or_uncertainty")),
    (re.compile(r"(?:wish|want|intention|desire)"), ("残っている願い", "unknown_wish_intention")),
    (re.compile(r"(?:change|repair|recover|recovery|movement|attempt|challenge)"), ("変えようとする動き", "unknown_change_movement")),
    (re.compile(r"(?:fatigue|tired|load|burden|pressure)"), ("負荷として残るもの", "unknown_load_or_pressure")),
    (re.compile(r"(?:self|inner|feeling|state)"), ("自分の中にある状態", "unknown_self_state")),
    (re.compile(r"(?:money|health|life|pace|work)"), ("生活の中で見ている材料", "unknown_life_context")),
)

DAILY_UNPLEASANT_REACTION_ROLE_KEYS = {
    "explicit_negative_reaction",
    "negative_daily_reaction",
    "anger_reaction",
    "anger_irritation",
    "fear_reaction",
    "disgust",
    "disgust_reaction",
    "negative_reaction",
    "daily_unpleasant_reaction",
}
DAILY_UNPLEASANT_EVENT_ROLE_KEYS = {
    "daily_event_fact",
    "event_fact",
    "action_event_fact",
    "daily_event_encounter",
    "public_unpleasant_encounter",
    "unpleasant_event_fact",
}

TECHNICAL_ROLE_KEYS = {
    "evidence_ids",
    "phrase_unit_ids",
    "relation_ids",
    "relation_type",
    "primary_phrase",
}

# Short grammar components.  These are parts, not complete observation strings.
PREDICATE_BANK: dict[str, tuple[tuple[str, str, str, str], ...]] = {
    "pressure": (
        ("が", "前面にあります", "pressure_foreground", "aru"),
        ("が", "強く残っています", "pressure_remain", "nokoru"),
        ("として", "続いています", "pressure_continue", "tsuzuku"),
    ),
    "recovery": (
        ("が", "少し戻ってきています", "recovery_return", "modoru"),
        ("として", "形を取り直しています", "recovery_reshape", "naosu"),
        ("も", "消えずにあります", "recovery_still_there", "aru"),
    ),
    "contrast": (
        ("が", "別々の向きで並んでいます", "contrast_parallel", "narabu"),
        ("として", "片方だけに寄らずにあります", "contrast_not_one_side", "aru"),
        ("も", "同じ場所に残っています", "contrast_same_place", "nokoru"),
    ),
    "coexistence": (
        ("として", "重なりを保っています", "coexistence_overlap", "tamotsu"),
        ("も", "片方だけに減らずに残っています", "coexistence_not_reduced", "nokoru"),
        ("が", "同じ流れの中で並んでいます", "coexistence_flow_parallel", "narabu"),
        ("として", "同じ場面の中で並んでいます", "coexistence_scene_parallel", "narabu"),
    ),
    "approach_avoidance": (
        ("が", "近づく動きと止まる動きの両方を持っています", "approach_avoidance_both", "motsu"),
        ("として", "一方向には決まりきっていません", "approach_avoidance_not_one", "kimaranai"),
        ("も", "同じ線上に残っています", "approach_avoidance_line", "nokoru"),
    ),
    "residue": (
        ("が", "あとに残っています", "residue_after", "nokoru"),
        ("として", "終わったあとにも残っています", "residue_after_end", "nokoru"),
        ("も", "まだ薄くあります", "residue_light", "aru"),
    ),
    "limit": (
        ("が", "限界に近い場所まで来ています", "limit_near", "kuru"),
        ("として", "これ以上を急がせない形であります", "limit_no_push", "aru"),
        ("も", "境目として残っています", "limit_boundary", "nokoru"),
    ),
    "context": (
        ("が", "背景として支えています", "context_support", "sasaeru"),
        ("として", "今の流れに接続しています", "context_connect", "tsunagu"),
        ("も", "根拠のある範囲で残っています", "context_bound", "nokoru"),
    ),
    "center": (
        ("が", "いま前に出ています", "center_front", "deru"),
        ("として", "言葉の中に置かれています", "center_placed", "oku"),
        ("も", "軸として残っています", "center_axis", "nokoru"),
        ("が", "根拠のある範囲にあります", "center_grounded_exists", "aru"),
    ),
}

DEFAULT_PREDICATES: tuple[tuple[str, str, str, str], ...] = (
    ("が", "根拠のある範囲であります", "grounded_exists", "aru"),
    ("として", "文の中に置かれています", "grounded_placed", "oku"),
    ("も", "消えずに残っています", "grounded_remain", "nokoru"),
)

CONNECTOR_BANK: dict[str, dict[str, tuple[str, str]]] = {
    "opening": {
        "default": ("", "none"),
        "pressure": ("まず、", "opening_pressure_first"),
        "recovery": ("はじめに、", "opening_recovery_first"),
    },
    "core": {
        "default": ("その中で、", "core_inside"),
        "pressure": ("その中で、", "core_inside_pressure"),
        "recovery": ("そこに、", "core_recovery_there"),
    },
    "relation": {
        "default": ("同時に、", "relation_same_time"),
        "contrast": ("ただ、", "relation_contrast_but"),
        "coexistence": ("同時に、", "relation_coexistence_same_time"),
        "pressure": ("その圧力の中で、", "relation_pressure_inside"),
        "recovery": ("それでも、", "relation_recovery_after_load"),
        "approach_avoidance": ("近づきたい方と止まりたい方が、", "relation_approach_avoidance"),
    },
    "closing": {
        "default": ("最後は、", "closing_default"),
        "recovery": ("締めでは、", "closing_recovery"),
        "pressure": ("締めでは、", "closing_pressure"),
    },
}

# Product-quality Step3: connector candidates are still grammar parts, not
# completed sentences.  They let the realizer avoid repeating the same transition
# shape while staying inside the relation declared by the SentencePlan.
CONNECTOR_VARIATION_BANK: dict[str, dict[str, tuple[tuple[str, str], ...]]] = {
    "opening": {
        "default": (("", "none"),),
        "pressure": (("まず、", "opening_pressure_first"), ("はじめに、", "opening_pressure_begin")),
        "recovery": (("はじめに、", "opening_recovery_first"), ("最初に、", "opening_recovery_begin")),
    },
    "core": {
        "default": (("そこでは、", "core_there"), ("続いて、", "core_continue"), ("その中で、", "core_inside")),
        "pressure": (("その重さの中で、", "core_pressure_weight"), ("圧力のある場面として、", "core_pressure_scene"), ("その中で、", "core_inside_pressure")),
        "recovery": (("戻る流れとして、", "core_recovery_flow"), ("そこに、", "core_recovery_there")),
        "contrast": (("もう一方では、", "core_contrast_other_side"), ("別の向きとして、", "core_contrast_direction"), ("その中で、", "core_inside_contrast")),
        "coexistence": (("重なりとして、", "core_coexistence_overlap"), ("同じ流れの中で、", "core_coexistence_flow"), ("その中で、", "core_inside_coexistence")),
        "approach_avoidance": (("その線上で、", "core_approach_avoidance_line"), ("同じ場所に、", "core_approach_avoidance_place")),
    },
    "relation": {
        "default": (("並んで、", "relation_parallel"), ("同時に、", "relation_same_time")),
        "contrast": (("一方で、", "relation_contrast_other_side"), ("ただ、", "relation_contrast_but")),
        "coexistence": (("重なって、", "relation_coexistence_overlap"), ("同じ流れの中で、", "relation_coexistence_flow"), ("同時に、", "relation_coexistence_same_time")),
        "pressure": (("その重さの中で、", "relation_pressure_weight"), ("その圧力の中で、", "relation_pressure_inside")),
        "recovery": (("戻る流れとして、", "relation_recovery_flow"), ("それでも、", "relation_recovery_after_load")),
        "approach_avoidance": (("向かう動きと止まる動きが、", "relation_approach_avoidance_motion"), ("近づきたい方と止まりたい方が、", "relation_approach_avoidance")),
    },
    "closing": {
        "default": (("最後は、", "closing_default"), ("締めでは、", "closing_soft")),
        "recovery": (("締めでは、", "closing_recovery"), ("最後は、", "closing_recovery_last")),
        "pressure": (("締めでは、", "closing_pressure"), ("最後は、", "closing_pressure_last")),
        "contrast": (("最後は、", "closing_contrast_last"), ("締めでは、", "closing_contrast_soft")),
        "coexistence": (("最後は、", "closing_coexistence_last"), ("締めでは、", "closing_coexistence_soft")),
        "approach_avoidance": (("最後は、", "closing_approach_avoidance_last"), ("締めでは、", "closing_approach_avoidance_soft")),
    },
}

CONNECTOR_VARIATION_FALLBACKS: dict[str, tuple[tuple[str, str], ...]] = {
    "opening": (
        ("", "none"),
        ("最初に、", "opening_initial"),
        ("ここでは、", "opening_here"),
    ),
    "core": (
        ("そこでは、", "core_there"),
        ("続いて、", "core_continue"),
        ("もう一つは、", "core_another"),
        ("その中で、", "core_inside"),
    ),
    "relation": (
        ("重なって、", "relation_overlap"),
        ("その一方で、", "relation_other_side"),
        ("並んで、", "relation_parallel"),
        ("同時に、", "relation_same_time"),
        ("ただ、", "relation_contrast_but"),
    ),
    "closing": (
        ("最後は、", "closing_default"),
        ("締めでは、", "closing_wrap"),
        ("残る形として、", "closing_residue"),
    ),
}

DISTANCE_POLICY_KEYS = {
    "opening": "receive_without_generalization",
    "core": "observe_without_overclaim",
    "relation": "hold_relation_without_deciding_true_side",
    "closing": "close_without_instruction_or_diagnosis",
}

FORBIDDEN_SURFACE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("internal_role_label_leak", INTERNAL_ROLE_SURFACE_FORBIDDEN_PATTERN),
    ("second_person_overuse", re.compile(r"あなたは|あなたの|あなたが|あなたに")),
    ("diagnosis_like", re.compile(r"診断|治療|症状|トラウマ|障害|ADHD|うつ|鬱|PTSD")),
    ("action_instruction", re.compile(r"(?:するべき|してください|しなければ|行動しましょう|変えましょう)")),
    ("over_comfort", re.compile(r"もう大丈夫|必ず良く|絶対に")),
    ("generic_fixed_closing", re.compile(r"急いで片づけず|一緒に見ます|小さく扱いません|軽く扱いません")),
    ("might_repetition_phrase", re.compile(r"かもしれません")),
)

DAILY_UNPLEASANT_SURFACE_QUALITY_FORBIDDEN_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("daily_unpleasant_anticipation_loop_skeleton", re.compile(r"先を考え続ける流れ")),
    ("daily_unpleasant_pressure_or_limit_skeleton", re.compile(r"pressure\s+or\s+limit|限界に近い圧力", re.IGNORECASE)),
    ("daily_unpleasant_relation_skeleton", re.compile(r"同じ流れ|同じ場所|重なりとして[^。！？!?\n]{0,80}として重なり|重なりを保って|片方だけに減らず")),
    ("daily_unpleasant_low_information_prompt_escape", re.compile(r"何があったか[^。！？!?\n]{0,16}残してみませんか|まだ詳しい出来事までは見えません|出来事までは見えません")),
    ("daily_unpleasant_target_judgement_agreement", re.compile(r"相手が悪い|あなたの怒りは正しい|その人は最低|おじさん[^。！？!?\n]{0,20}(?:悪い|最低)")),
    ("daily_unpleasant_risk_overclaim", re.compile(r"危険な目に遭いました|トラウマになりそう|トラウマになった")),
    ("daily_unpleasant_analytic_register", re.compile(r"構造|関係性|要素|分類|パターン|傾向|深層|価値線")),
    ("daily_unpleasant_structural_label_leak", re.compile(r"explicit negative reaction|daily event fact|pressure_or_limit|anticipation_loop", re.IGNORECASE)),
)

_SPACE_RE = re.compile(r"\s+")
_TRIM = " \t\r\n　、,。.!！?？『』\"'「」（）()[]【】"


def _clean(value: Any, *, limit: int = 0) -> str:
    text = _SPACE_RE.sub(" ", str(value or "").replace("\u3000", " ").replace("\r", " ").replace("\n", " ")).strip(_TRIM)
    if limit > 0 and len(text) > limit:
        text = text[:limit].rstrip(_TRIM)
    return text


def _clean_token(value: Any) -> str:
    return re.sub(r"[^0-9a-zA-Z_\-.]+", "_", str(value or "").strip().lower()).strip("_")


def _dedupe(values: Iterable[Any] | Any | None) -> Tuple[str, ...]:
    if values is None:
        return tuple()
    if isinstance(values, (str, bytes)):
        src: Iterable[Any] = [values]
    elif isinstance(values, Iterable):
        src = values
    else:
        src = [values]
    out: list[str] = []
    seen: set[str] = set()
    for raw in src:
        item = _clean(raw)
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return tuple(out)


def _json_safe_value(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, Mapping):
        return _json_safe_mapping(value)
    if isinstance(value, (list, tuple, set)):
        return [_json_safe_value(item) for item in value]
    if is_dataclass(value):
        return _json_safe_mapping(asdict(value))
    return str(value)


def _json_safe_mapping(value: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    out: dict[str, Any] = {}
    for key, item in value.items():
        key_text = _clean(key)
        if not key_text or key_text in RAW_INPUT_META_KEYS:
            continue
        out[key_text] = _json_safe_value(item)
    return out


def _as_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    if is_dataclass(value):
        return asdict(value)
    out: dict[str, Any] = {}
    for key in (
        "sentence_id",
        "line_role",
        "relation_type",
        "focus_rank",
        "phrase_unit_ids",
        "evidence_span_ids",
        "used_phrase_unit_ids",
        "used_evidence_span_ids",
        "must_include_roles",
        "optional_roles",
        "forbidden_surface_keys",
        "max_chars",
        "surface_intent",
        "repair_policy",
        "meta",
    ):
        if hasattr(value, key):
            out[key] = getattr(value, key)
    return out


def _coerce_plan_line(value: CompleteSentencePlanLine | Mapping[str, Any]) -> CompleteSentencePlanLine | None:
    if isinstance(value, CompleteSentencePlanLine):
        return value
    if isinstance(value, Mapping):
        return CompleteSentencePlanLine(
            sentence_id=value.get("sentence_id") or value.get("id") or "",
            line_role=value.get("line_role") or value.get("role") or "core",
            relation_type=value.get("relation_type") or value.get("relation") or "center",
            focus_rank=value.get("focus_rank") or value.get("rank") or 1,
            phrase_unit_ids=value.get("phrase_unit_ids") or value.get("used_phrase_unit_ids") or (),
            evidence_span_ids=value.get("evidence_span_ids") or value.get("used_evidence_span_ids") or (),
            must_include_roles=value.get("must_include_roles") or (),
            optional_roles=value.get("optional_roles") or (),
            forbidden_surface_keys=value.get("forbidden_surface_keys") or (),
            max_chars=value.get("max_chars") or 120,
            surface_intent=value.get("surface_intent") or "",
            repair_policy=value.get("repair_policy") or (),
            meta=value.get("meta") or {},
        )
    return None


def _coerce_sentence_plan(value: CompleteSentencePlanV2 | Mapping[str, Any] | None) -> CompleteSentencePlanV2 | None:
    if isinstance(value, CompleteSentencePlanV2):
        return value
    if isinstance(value, Mapping):
        return CompleteSentencePlanV2(
            plan_id=value.get("plan_id") or "complete_sentence_plan_v2",
            sentence_budget=value.get("sentence_budget") or value.get("planned_sentence_count") or 2,
            coverage_group=value.get("coverage_group") or value.get("coverage_scope") or "unknown",
            sentence_plans=value.get("sentence_plans") or value.get("lines") or (),
            meta=value.get("meta") or {},
        )
    return None


def _surface_relation(relation_type: Any) -> str:
    relation = normalize_relation_type(relation_type)
    if not relation:
        return "center"
    return relation

def _observation_line_meta(line: CompleteSentencePlanLine | Mapping[str, Any] | None) -> dict[str, Any]:
    if line is None:
        return {}
    if hasattr(line, "as_meta"):
        meta = line.as_meta()
    elif isinstance(line, Mapping):
        meta = dict(line)
    else:
        meta = {}
    nested = meta.get("meta") if isinstance(meta.get("meta"), Mapping) else {}
    out = dict(nested)
    for key in (
        "observation_roles",
        "sentence_plan_observation_roles",
        "observation_reply_kind",
        "question_required",
        "known_scope_only",
        "unknown_slots",
        "inference_depth",
        "user_fact_grounding_mode",
        "surface_role_merge",
    ):
        if key in meta and key not in out:
            out[key] = meta[key]
    return out


def _observation_roles_for_line(line: CompleteSentencePlanLine | Mapping[str, Any] | None) -> Tuple[str, ...]:
    meta = _observation_line_meta(line)
    roles = meta.get("observation_roles") or meta.get("sentence_plan_observation_roles") or ()
    return _dedupe(roles)


def _observation_surface_signature_meta(line: CompleteSentencePlanLine | Mapping[str, Any] | None) -> dict[str, Any]:
    meta = _observation_line_meta(line)
    roles = list(_observation_roles_for_line(line))
    unknown_slots = list(_dedupe(meta.get("unknown_slots")))
    try:
        depth = int(meta.get("inference_depth") or 0)
    except (TypeError, ValueError):
        depth = 0
    if depth < 0:
        depth = 0
    if depth > 3:
        depth = 3
    return {
        "observation_surface_realizer_step": OBSERVATION_SURFACE_REALIZER_STEP,
        "observation_surface_realizer_version": OBSERVATION_SURFACE_REALIZER_VERSION,
        "observation_roles": roles,
        "sentence_plan_observation_roles": roles,
        "observation_reply_kind": _clean_token(meta.get("observation_reply_kind")),
        "question_required": bool(meta.get("question_required")),
        "known_scope_only": bool(meta.get("known_scope_only")),
        "unknown_slots": unknown_slots,
        "inference_depth": depth or None,
        "user_fact_grounding_mode": _clean_token(meta.get("user_fact_grounding_mode")),
        "surface_role_merge": list(_dedupe(meta.get("surface_role_merge"))),
        "comment_text_generated": False,
        "raw_input_included": False,
    }


def _meaning_roles(line: CompleteSentencePlanLine) -> Tuple[str, ...]:
    roles = []
    for raw in tuple(line.must_include_roles or ()) + tuple(line.optional_roles or ()):  # preserve plan order
        role = _clean_token(raw)
        if role and role not in TECHNICAL_ROLE_KEYS and role not in roles:
            roles.append(role)
    return tuple(roles)


def _role_phrase(role: str) -> tuple[str, str]:
    role_key = _clean_token(role)
    if role_key in ROLE_PHRASE_BANK:
        return ROLE_PHRASE_BANK[role_key]
    if not role_key:
        return "根拠のある材料", "grounded_material"
    # Phase17-2: unknown internal role labels are development structure, not
    # user-facing language.  Do not render ``role_key.replace("_", " ")`` into
    # visible text; keep the original role only in the private diagnostic key.
    for pattern, fallback in UNKNOWN_ROLE_SURFACE_PHRASE_RULES:
        if pattern.search(role_key):
            phrase, key = fallback
            diagnostic_prefix = "blocked_internal_role" if role_key in INTERNAL_ROLE_SURFACE_FORBIDDEN_KEYS else key
            return phrase, f"{diagnostic_prefix}_{role_key}"
    if role_key in INTERNAL_ROLE_SURFACE_FORBIDDEN_KEYS:
        return UNKNOWN_INTERNAL_ROLE_SURFACE_PHRASE, f"blocked_internal_role_{role_key}"
    return UNKNOWN_INTERNAL_ROLE_SURFACE_PHRASE, f"{UNKNOWN_INTERNAL_ROLE_SURFACE_KEY}_{role_key}"


def _phrase_for_line(line: CompleteSentencePlanLine) -> tuple[str, str, Tuple[str, ...]]:
    roles = _meaning_roles(line)
    if not roles:
        roles = ("primary_phrase",)
    phrases: list[str] = []
    keys: list[str] = []
    for role in roles[:2]:
        phrase, key = _role_phrase(role)
        if phrase not in phrases:
            phrases.append(phrase)
        if key not in keys:
            keys.append(key)
    if line.line_role == "relation" and len(phrases) >= 2:
        return "と".join(phrases[:2]), "relation_pair", tuple(keys)
    if line.line_role == "opening" and keys and keys[0] == "primary_phrase":
        # Step7 / Surface Realizer 2.1 Anti-Template: keep the source role
        # binding, but do not surface the opening as the screenshot-like
        # "center phrase + center predicate" skeleton.
        return "今出ている感覚", "opening_current_expression", _dedupe(("opening_current_expression", *keys))
    return phrases[0], keys[0], tuple(keys)


def _internal_role_surface_phrase_meta(role_phrase_keys: Sequence[str]) -> dict[str, Any]:
    keys = list(_dedupe(role_phrase_keys))
    fallback_used = any(
        key == UNKNOWN_INTERNAL_ROLE_SURFACE_KEY
        or key.startswith(f"{UNKNOWN_INTERNAL_ROLE_SURFACE_KEY}_")
        or key.startswith("blocked_internal_role_")
        for key in keys
    )
    return {
        "internal_role_surface_phrase_schema_version": EMLIS_TWO_STAGE_INTERNAL_ROLE_SURFACE_PHRASE_SCHEMA_VERSION,
        "internal_role_surface_phrase_source_phase": EMLIS_TWO_STAGE_INTERNAL_ROLE_SURFACE_PHRASE_SOURCE_PHASE,
        "internal_role_surface_phrase_applied": True,
        "internal_role_visible_english_label_suppressed": True,
        "unknown_internal_role_surface_fallback_used": fallback_used,
        "unknown_internal_role_visible_label_suppressed": fallback_used,
        "internal_role_surface_phrase_public_response_key_added": False,
        "internal_role_surface_phrase_fixed_sentence_template_used": False,
        "internal_role_surface_phrase_raw_input_included": False,
    }


def _connector_candidates(line_role: str, relation_type: str, sequence_index: int) -> tuple[tuple[str, str], ...]:
    if sequence_index <= 0 and line_role == "opening":
        return (("", "none"),)
    role = _clean_token(line_role) or "core"
    relation = _surface_relation(relation_type)
    variation_bank = CONNECTOR_VARIATION_BANK.get(role) or CONNECTOR_VARIATION_BANK["core"]
    legacy_bank = CONNECTOR_BANK.get(role) or CONNECTOR_BANK["core"]
    candidates: list[tuple[str, str]] = []
    variation_pairs = (
        *(variation_bank.get(relation) or ()),
        *(variation_bank.get(canonical_relation_type(relation)) or ()),
        *(variation_bank.get("default") or ()),
    )
    legacy_pairs = (
        legacy_bank.get(relation),
        legacy_bank.get(canonical_relation_type(relation)),
        legacy_bank.get("default"),
        *(CONNECTOR_VARIATION_FALLBACKS.get(role) or ()),
    )
    for pair in (*variation_pairs, *legacy_pairs):
        if not pair:
            continue
        connector, key = pair
        row = (_clean(connector), _clean_token(key) or "none")
        if row[1] in ANTI_TEMPLATE_SUPPRESSED_CONNECTOR_KEYS:
            continue
        if row not in candidates:
            candidates.append(row)
    return tuple(candidates or (("", "none"),))


def _connector_for(
    line_role: str,
    relation_type: str,
    sequence_index: int,
    used_connector_keys: Sequence[str] | None = None,
) -> tuple[str, str]:
    used = {key for key in (used_connector_keys or ()) if key and key != "none"}
    used_families = {_anti_template_connector_family_key(key) for key in used}
    previous_key = (tuple(used_connector_keys or ())[-1] if used_connector_keys else "")
    previous_family = _anti_template_connector_family_key(previous_key)
    candidates = _connector_candidates(line_role, relation_type, sequence_index)
    for connector, key in candidates:
        family = _anti_template_connector_family_key(key, connector)
        if key == "none" or (key not in used and family not in used_families):
            return connector, key
    for connector, key in candidates:
        family = _anti_template_connector_family_key(key, connector)
        if key == "none" or family != previous_family:
            return connector, key
    return candidates[0]


def _predicate_candidates(relation_type: str, line_role: str) -> tuple[tuple[str, str, str, str], ...]:
    relation = _surface_relation(relation_type)
    candidates = list(PREDICATE_BANK.get(relation) or PREDICATE_BANK.get(canonical_relation_type(relation)) or DEFAULT_PREDICATES)
    if line_role == "closing":
        candidates.extend([
            ("として", "静かに残っています", "closing_quiet_remain", "nokoru"),
            ("が", "結論にされずにあります", "closing_no_forced_conclusion", "aru"),
        ])
    if line_role == "opening":
        candidates = [row for row in candidates if row[2] not in ANTI_TEMPLATE_GENERIC_CENTER_PREDICATE_KEYS]
        if relation in {"center", "context"}:
            candidates = [
                ("が", "いま前に出ています", "opening_current_front", "deru"),
                ("として", "言葉の中に置かれています", "opening_word_placed", "oku"),
                *candidates,
            ]
    if line_role == "relation":
        candidates.extend([
            ("として", "分かれずに扱われています", "relation_not_split", "atsukau"),
            ("が", "同じ流れの中で並んでいます", "relation_flow_parallel", "narabu"),
        ])
    return tuple(candidates)


def _choose_predicate(*, relation_type: str, line_role: str, used_predicate_keys: Sequence[str], used_ending_keys: Sequence[str]) -> tuple[str, str, str, str]:
    used_predicates = set(used_predicate_keys or ())
    used_endings = set(used_ending_keys or ())
    used_predicate_families = {_anti_template_predicate_family_key(key) for key in used_predicates}
    used_ending_families = {_anti_template_ending_family_key(key) for key in used_endings}
    candidates = _predicate_candidates(relation_type, line_role)
    for particle, predicate, predicate_key, ending_key in candidates:
        predicate_family = _anti_template_predicate_family_key(predicate_key, ending_key)
        ending_family = _anti_template_ending_family_key(ending_key)
        if (
            predicate_key not in used_predicates
            and ending_key not in used_endings
            and predicate_family not in used_predicate_families
            and ending_family not in used_ending_families
        ):
            return particle, predicate, predicate_key, ending_key
    for particle, predicate, predicate_key, ending_key in candidates:
        predicate_family = _anti_template_predicate_family_key(predicate_key, ending_key)
        if predicate_key not in used_predicates and predicate_family not in used_predicate_families:
            return particle, predicate, predicate_key, ending_key
    for particle, predicate, predicate_key, ending_key in candidates:
        if predicate_key not in used_predicates:
            return particle, predicate, predicate_key, ending_key
    return candidates[0] if candidates else DEFAULT_PREDICATES[0]


def _tone_constraint_for_line(tone_policy: CompleteTonePolicy | Mapping[str, Any] | None, line: CompleteSentencePlanLine, relation: str) -> dict[str, Any]:
    policy = coerce_complete_tone_policy(tone_policy, coverage_group=getattr(line, 'coverage_group', '') if hasattr(line, 'coverage_group') else '')
    constraint = policy.constraint_for(sentence_id=line.sentence_id, line_role=line.line_role, relation_type=relation)
    return constraint.as_meta()


def _tone_guard_keys(constraint: Mapping[str, Any]) -> Tuple[str, ...]:
    return _dedupe(constraint.get('guard_keys'))


def _truncate_sentence(sentence: str, max_chars: int) -> str:
    text = _clean(sentence)
    if not text:
        return ""
    if not text.endswith(("。", "！", "？")):
        text = f"{text}。"
    if max_chars > 0 and len(text) > max_chars:
        text = text[: max(8, max_chars - 1)].rstrip(_TRIM) + "。"
    return text



def _line_meta_flag(line: CompleteSentencePlanLine, key: str) -> bool:
    meta = line.meta if isinstance(line.meta, Mapping) else {}
    value = meta.get(key)
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return str(value or "").strip().lower() in {"1", "true", "yes", "on", "present", "detected"}


def _relation_surface_context_flags(line: CompleteSentencePlanLine, relation: str) -> dict[str, Any]:
    roles = set(_meaning_roles(line))
    meta = line.meta if isinstance(line.meta, Mapping) else {}
    prior_load_present = (
        canonical_relation_type(relation) == "recovery"
        and (
            bool(roles.intersection(RECOVERY_PRIOR_LOAD_ROLE_KEYS))
            or _line_meta_flag(line, "prior_load_present")
            or bool(meta.get("prior_load_hint"))
            or bool(meta.get("prior_load_roles"))
        )
    )
    return {
        "prior_load_present": bool(prior_load_present),
        "role_keys": sorted(roles),
        "raw_input_included": False,
    }


def _relation_surface_alignment_for_line(
    line: CompleteSentencePlanLine,
    *,
    relation: str,
    text: str,
) -> tuple[str, dict[str, Any]]:
    """Align recovery relation lines with the shared surface contract.

    This does not relax Reader.  It only rewrites an already-planned recovery
    relation line to a relation cue that Reader and Self-Repair share.
    """

    base_signal = detect_relation_surface(text, expected_relation_types=(relation,))
    if line.line_role != "relation" or canonical_relation_type(relation) != "recovery":
        return text, {
            "relation_surface_contract_version": RELATION_SURFACE_CONTRACT_VERSION,
            "surface_recovery_relation_line_aligned": False,
            "relation_surface_signal": base_signal,
            "reader_relation_signal_detected": bool(base_signal.get("reader_relation_signal_detected")),
            "reader_relation_signal_count": int(base_signal.get("reader_relation_signal_count") or base_signal.get("count") or 0),
            "reader_relation_signal_keys": list(base_signal.get("reader_relation_signal_keys") or base_signal.get("keys") or []),
            "raw_input_included": False,
        }

    context_flags = _relation_surface_context_flags(line, relation)
    marker = relation_marker_meta(relation, context_flags=context_flags)
    # Step4 aligns the Surface relation line itself with the same marker family
    # Self-Repair uses.  This keeps Reader / Surface / Repair on one contract
    # without relaxing the Gate and without creating a fallback observation.
    aligned_text = _truncate_sentence(marker.get("relation_marker_phrase") or text, int(line.max_chars or 120))
    marker_applied = aligned_text != text
    signal = detect_relation_surface(aligned_text, expected_relation_types=(relation,))
    marker_key = str(marker.get("relation_marker_key") or relation_marker_key(relation, context_flags=context_flags))
    return aligned_text, {
        "relation_surface_contract_version": RELATION_SURFACE_CONTRACT_VERSION,
        "surface_recovery_relation_line_aligned": True,
        "surface_recovery_relation_alignment_step": COMPLETE_SURFACE_RECOVERY_RELATION_LINE_ALIGNMENT_STEP,
        "surface_recovery_relation_marker_applied": marker_applied,
        "surface_relation_marker_key": marker_key,
        "relation_marker_key": marker_key,
        "relation_surface_signal": signal,
        "reader_relation_signal_detected": bool(signal.get("reader_relation_signal_detected") or signal.get("detected")),
        "reader_relation_signal_count": int(signal.get("reader_relation_signal_count") or signal.get("count") or 0),
        "reader_relation_signal_keys": list(signal.get("reader_relation_signal_keys") or signal.get("keys") or []),
        "reader_relation_signal_relation_types": list(signal.get("reader_relation_signal_relation_types") or signal.get("relation_types") or []),
        "expected_relation_types": list(signal.get("expected_relation_types") or [canonical_relation_type(relation)]),
        "relation_surface_context_flags": context_flags,
        "meaning_added": False,
        "gate_relaxed": False,
        "raw_input_included": False,
    }


def _surface_relation_contract_keys(relation_surface_meta: Mapping[str, Any] | None) -> dict[str, Any]:
    meta = _json_safe_mapping(relation_surface_meta)
    signal = meta.get("relation_surface_signal") if isinstance(meta.get("relation_surface_signal"), Mapping) else {}
    marker_key = _clean_token(meta.get("surface_relation_marker_key") or meta.get("relation_marker_key"))
    return {
        "relation_surface_contract_version": meta.get("relation_surface_contract_version") or RELATION_SURFACE_CONTRACT_VERSION,
        "surface_recovery_relation_line_aligned": bool(meta.get("surface_recovery_relation_line_aligned")),
        "surface_recovery_relation_alignment_step": meta.get("surface_recovery_relation_alignment_step") or "",
        "surface_recovery_relation_marker_applied": bool(meta.get("surface_recovery_relation_marker_applied")),
        "surface_relation_marker_key": marker_key,
        "relation_marker_key": marker_key,
        "relation_surface_signal_detected": bool(signal.get("reader_relation_signal_detected") or signal.get("detected")),
        "relation_surface_signal_count": int(signal.get("reader_relation_signal_count") or signal.get("count") or 0),
        "relation_surface_signal_keys": list(signal.get("reader_relation_signal_keys") or signal.get("keys") or []),
        "reader_relation_signal_detected": bool(meta.get("reader_relation_signal_detected") or signal.get("reader_relation_signal_detected") or signal.get("detected")),
        "reader_relation_signal_count": int(meta.get("reader_relation_signal_count") or signal.get("reader_relation_signal_count") or signal.get("count") or 0),
        "reader_relation_signal_keys": list(meta.get("reader_relation_signal_keys") or signal.get("reader_relation_signal_keys") or signal.get("keys") or []),
        "expected_relation_types": list(meta.get("expected_relation_types") or signal.get("expected_relation_types") or []),
        "meaning_added": False,
        "gate_relaxed": False,
        "raw_input_included": False,
    }


def _relation_surface_report_from_lines(lines: Sequence["CompleteSurfaceLineV2"] | None) -> dict[str, Any]:
    marker_keys: list[str] = []
    signal_keys: list[str] = []
    relation_types: list[str] = []
    aligned_sentence_ids: list[str] = []
    signal_count = 0
    signal_detected = False
    for line in tuple(lines or ()):  # defensive for mapping-created test rows
        meta = dict(line.meta) if isinstance(line.meta, Mapping) else {}
        signature = dict(line.surface_signature) if isinstance(line.surface_signature, Mapping) else {}
        if bool(meta.get("surface_recovery_relation_line_aligned") or signature.get("surface_recovery_relation_line_aligned")):
            aligned_sentence_ids.append(line.sentence_id)
        marker_key = _clean(meta.get("surface_relation_marker_key") or meta.get("relation_marker_key") or signature.get("surface_relation_marker_key") or signature.get("relation_marker_key"))
        if marker_key:
            marker_keys.append(marker_key)
        signal = meta.get("relation_surface_signal") or signature.get("relation_surface_signal") or {}
        if isinstance(signal, Mapping):
            signal_detected = signal_detected or bool(signal.get("reader_relation_signal_detected") or signal.get("detected"))
            try:
                signal_count += int(signal.get("reader_relation_signal_count") or signal.get("count") or 0)
            except (TypeError, ValueError):
                signal_count += 0
            signal_keys.extend(str(item) for item in signal.get("reader_relation_signal_keys") or signal.get("keys") or [])
            relation_types.extend(str(item) for item in signal.get("reader_relation_signal_relation_types") or signal.get("relation_types") or [])
        signal_keys.extend(str(item) for item in meta.get("reader_relation_signal_keys") or signature.get("reader_relation_signal_keys") or [])
        relation_types.extend(str(item) for item in meta.get("reader_relation_signal_relation_types") or signature.get("reader_relation_signal_relation_types") or [])
    marker_keys_tuple = _dedupe(marker_keys)
    signal_keys_tuple = _dedupe(signal_keys)
    relation_types_tuple = _dedupe(relation_types)
    signal_detected = bool(signal_detected or signal_keys_tuple)
    if signal_detected and signal_count <= 0:
        signal_count = len(signal_keys_tuple)
    return {
        "relation_surface_contract_version": RELATION_SURFACE_CONTRACT_VERSION,
        "surface_recovery_relation_line_alignment_step": COMPLETE_SURFACE_RECOVERY_RELATION_LINE_ALIGNMENT_STEP,
        "surface_recovery_relation_line_aligned": bool(aligned_sentence_ids),
        "surface_recovery_relation_line_sentence_ids": list(_dedupe(aligned_sentence_ids)),
        "surface_relation_marker_keys": list(marker_keys_tuple),
        "surface_relation_marker_key": marker_keys_tuple[0] if marker_keys_tuple else "",
        "reader_relation_signal_detected": signal_detected,
        "reader_relation_signal_count": signal_count,
        "reader_relation_signal_keys": list(signal_keys_tuple),
        "reader_relation_signal_relation_types": list(relation_types_tuple),
        "meaning_added": False,
        "gate_relaxed": False,
        "raw_input_included": False,
    }

def _surface_signature_row(*, line: CompleteSentencePlanLine, phrase_key: str, role_phrase_keys: Sequence[str], connector_key: str, particle: str, predicate_key: str, ending_key: str, distance_policy_key: str, variation_key: str, tone_policy_key: str = "", temperature_key: str = "", tone_guard_keys: Sequence[str] | None = None, closing_policy_key: str = "", read_feeling_policy_key: str = "", relation_surface_meta: Mapping[str, Any] | None = None) -> dict[str, Any]:
    relation = _surface_relation(line.relation_type)
    relation_contract = _surface_relation_contract_keys(relation_surface_meta)
    observation_surface_meta = _observation_surface_signature_meta(line)
    marker_key = _clean_token(relation_contract.get("surface_relation_marker_key") or relation_contract.get("relation_marker_key"))
    signature_relation_suffix = f":{marker_key}" if marker_key else ""
    connector_family = _anti_template_connector_family_key(connector_key)
    predicate_family = _anti_template_predicate_family_key(predicate_key, ending_key)
    ending_family = _anti_template_ending_family_key(ending_key)
    opening_family = _anti_template_opening_family_key(line.line_role, predicate_key, phrase_key)
    return {
        "version": COMPLETE_SURFACE_SIGNATURE_SCHEMA_VERSION,
        "sentence_id": line.sentence_id,
        "line_role": line.line_role,
        "relation_type": relation,
        "canonical_relation_type": canonical_relation_type(relation),
        "relation_family": relation_family(relation),
        "subject_policy_key": "omit_second_person_subject",
        "role_phrase_key": phrase_key,
        "role_phrase_keys": list(role_phrase_keys),
        "connector_key": connector_key,
        "connector_family_key": connector_family,
        "particle_key": particle,
        "predicate_key": predicate_key,
        "predicate_family_key": predicate_family,
        "ending_key": ending_key,
        "ending_family_key": ending_family,
        "opening_family_key": opening_family,
        "distance_policy_key": distance_policy_key,
        "tone_policy_key": _clean_token(tone_policy_key) or distance_policy_key,
        "temperature_key": _clean_token(temperature_key),
        "tone_guard_keys": list(_dedupe(tone_guard_keys)),
        "closing_policy_key": _clean_token(closing_policy_key),
        "read_feeling_policy_key": _clean_token(read_feeling_policy_key),
        **relation_contract,
        **observation_surface_meta,
        "tone_engine_version": COMPLETE_TONE_ENGINE_VERSION,
        "tone_engine_2_1_version": COMPLETE_TONE_ENGINE_2_1_VERSION,
        "tone_engine_2_1_policy_version": COMPLETE_TONE_POLICY_2_1_VERSION,
        "step9_tone_engine_2_1_ready": True,
        "tone_policy_version": COMPLETE_TONE_POLICY_VERSION,
        "product_quality_tone_engine_version": COMPLETE_PRODUCT_QUALITY_TONE_ENGINE_VERSION,
        "variation_key": variation_key,
        "signature": f"{line.line_role}:{relation}:{phrase_key}:{connector_key}:{particle}:{predicate_key}:{ending_key}:{distance_policy_key}:{_clean_token(tone_policy_key) or distance_policy_key}{signature_relation_suffix}",
        "product_quality_surface_variation_version": COMPLETE_PRODUCT_QUALITY_SURFACE_VARIATION_VERSION,
        "surface_realizer_anti_template_version": COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_VERSION,
        "surface_realizer_anti_template_policy_version": COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_POLICY_VERSION,
        "surface_realizer_2_1_anti_template_applied": True,
        "generic_center_opening": opening_family == "generic_center_opening",
        "surface_signature_for_template_guard": True,
        "completion_sentence_template_used": False,
        "role_completed_sentence_template_used": False,
        "input_specific_template_used": False,
        "raw_input_included": False,
    }

def _value_counts(values: Iterable[Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for raw in values:
        key = _clean(raw)
        if not key:
            continue
        counts[key] = counts.get(key, 0) + 1
    return counts


def _repeated_keys(values: Iterable[Any], *, min_count: int = 2, ignore: Iterable[str] | None = None) -> Tuple[str, ...]:
    ignore_set = set(ignore or ())
    counts = _value_counts(values)
    return tuple(key for key, count in counts.items() if count >= min_count and key not in ignore_set)


def _surface_variation_report_from_rows(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    row_list = [dict(row) for row in rows if isinstance(row, Mapping)]
    connector_keys = [_clean(row.get("connector_key")) for row in row_list if _clean(row.get("connector_key"))]
    predicate_keys = [_clean(row.get("predicate_key")) for row in row_list if _clean(row.get("predicate_key"))]
    ending_keys = [_clean(row.get("ending_key")) for row in row_list if _clean(row.get("ending_key"))]
    signatures = [_clean(row.get("signature")) for row in row_list if _clean(row.get("signature"))]
    repeated_connector_keys = _repeated_keys(connector_keys, min_count=3, ignore={"none"})
    repeated_ending_keys = _repeated_keys(ending_keys, min_count=3)
    repeated_signature_keys = _repeated_keys(signatures, min_count=2)
    anti_template_report = build_surface_realizer_anti_template_report(row_list)

    template_flags = [
        "completion_sentence_template_used",
        "role_completed_sentence_template_used",
        "input_specific_template_used",
        "fixed_sentence_template_used",
    ]
    flagged_template_rows = [
        str(row.get("sentence_id") or index)
        for index, row in enumerate(row_list, start=1)
        if any(bool(row.get(flag)) for flag in template_flags)
    ]
    raw_rows = [
        str(row.get("sentence_id") or index)
        for index, row in enumerate(row_list, start=1)
        if bool(row.get("raw_input_included") or row.get("raw_text_included"))
    ]

    blocker_reasons: list[str] = []
    if repeated_ending_keys:
        blocker_reasons.append("same_ending_major")
    if repeated_signature_keys:
        blocker_reasons.append("surface_signature_repeat")
    if repeated_connector_keys:
        blocker_reasons.append("surface_connector_repetition")
    if flagged_template_rows:
        blocker_reasons.append("surface_signature_template_flag")
    if raw_rows:
        blocker_reasons.append("surface_signature_raw_input_included")
    for reason in list(anti_template_report.get("anti_template_major_reasons") or []):
        marker = str(reason)
        if marker not in blocker_reasons:
            blocker_reasons.append(marker)

    anti_template_major_reasons = list(anti_template_report.get("anti_template_major_reasons") or [])
    return {
        "version": COMPLETE_PRODUCT_QUALITY_SURFACE_VARIATION_SCHEMA_VERSION,
        "surface_variation_version": COMPLETE_PRODUCT_QUALITY_SURFACE_VARIATION_VERSION,
        "surface_variation_step": COMPLETE_PRODUCT_QUALITY_SURFACE_VARIATION_STEP,
        "surface_signature_version": COMPLETE_SURFACE_SIGNATURE_SCHEMA_VERSION,
        "surface_signature_count": len(signatures),
        "surface_signature_repeat_count": len(repeated_signature_keys),
        "repeated_surface_signature_keys": list(repeated_signature_keys),
        "connector_keys": connector_keys,
        "unique_connector_key_count": len(set(connector_keys)),
        "repeated_connector_keys": list(repeated_connector_keys),
        "connector_repetition_major_count": len(repeated_connector_keys),
        "connector_family_keys": list(anti_template_report.get("connector_family_keys") or []),
        "predicate_keys": predicate_keys,
        "unique_predicate_key_count": len(set(predicate_keys)),
        "predicate_family_keys": list(anti_template_report.get("predicate_family_keys") or []),
        "ending_keys": ending_keys,
        "unique_ending_key_count": len(set(ending_keys)),
        "ending_family_keys": list(anti_template_report.get("ending_family_keys") or []),
        "opening_family_keys": list(anti_template_report.get("opening_family_keys") or []),
        "same_ending_major_count": len(repeated_ending_keys),
        "repeated_ending_keys": list(repeated_ending_keys),
        "surface_realizer_anti_template_version": COMPLETE_SURFACE_REALIZER_2_1_ANTI_TEMPLATE_VERSION,
        "anti_template_policy_version": COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_POLICY_VERSION,
        "surface_realizer_2_1_anti_template_version": COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_VERSION,
        "surface_realizer_2_1_anti_template_step": COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_STEP,
        "surface_realizer_2_1_anti_template_applied": True,
        "surface_anti_template_report": anti_template_report,
        "surface_realizer_anti_template_report": anti_template_report,
        "surface_anti_template_guard_passed": not bool(anti_template_report.get("anti_template_major_detected")),
        "generic_center_opening_count": int(anti_template_report.get("generic_center_opening_count") or 0),
        "same_connector_family_run_max": int(anti_template_report.get("same_connector_family_run_max") or 0),
        "same_connector_key_run_max": int(anti_template_report.get("same_connector_key_run_max") or 0),
        "same_predicate_family_count": int(anti_template_report.get("same_predicate_family_count") or 0),
        "same_ending_family_count": int(anti_template_report.get("same_ending_family_count") or 0),
        "anti_template_major_count": len(anti_template_major_reasons),
        "anti_template_major_reasons": anti_template_major_reasons,
        "completion_sentence_template_used": bool(flagged_template_rows),
        "flagged_template_sentence_ids": flagged_template_rows,
        "raw_input_included": bool(raw_rows),
        "raw_input_sentence_ids": raw_rows,
        "release_blocker": bool(blocker_reasons),
        "blocker_reasons": blocker_reasons,
        "passed": not blocker_reasons,
    }

def _forbidden_surface_hits(text: str) -> Tuple[str, ...]:
    hits: list[str] = []
    for key, pattern in FORBIDDEN_SURFACE_PATTERNS:
        if pattern.search(text or "") and key not in hits:
            hits.append(key)
    return tuple(hits)


def _phase17_self_repair_reason_codes_for_surface(
    *,
    lines: Sequence[Any] = (),
    validation_errors: Sequence[Any] = (),
    surface_variation_report: Mapping[str, Any] | None = None,
    two_stage_report: Mapping[str, Any] | None = None,
) -> Tuple[str, ...]:
    """Return Phase17-7 product-visible reason codes without carrying body text."""

    codes: list[str] = []
    validation_text = " ".join(str(reason or "") for reason in validation_errors)
    if "internal_role_label_leak" in validation_text or "two_stage_complete_surface_internal_label_leak" in validation_text:
        codes.append(EMLIS_TWO_STAGE_PHASE17_REASON_INTERNAL_ROLE_LABEL_LEAK)
    if "relation_skeleton_leak" in validation_text:
        codes.append(EMLIS_TWO_STAGE_PHASE17_REASON_RELATION_SKELETON_LEAK)
    if "section_budget" in validation_text or "section_empty" in validation_text:
        codes.append(EMLIS_TWO_STAGE_PHASE17_REASON_SECTION_BUDGET_MISMATCH)

    for line in tuple(lines or ()):  # type: ignore[assignment]
        text = str(getattr(line, "surface_text", "") or "")
        if PHASE17_INTERNAL_ROLE_LABEL_RE.search(text):
            codes.append(EMLIS_TWO_STAGE_PHASE17_REASON_INTERNAL_ROLE_LABEL_LEAK)
        if PHASE17_RELATION_SKELETON_RE.search(text):
            codes.append(EMLIS_TWO_STAGE_PHASE17_REASON_RELATION_SKELETON_LEAK)

    variation = _json_safe_mapping(surface_variation_report)
    anti = _json_safe_mapping(variation.get("surface_anti_template_report"))
    anti_reasons = tuple(str(reason or "") for reason in variation.get("anti_template_major_reasons") or anti.get("anti_template_major_reasons") or ())
    if (
        int(anti.get("same_predicate_family_count") or 0) > 0
        or int(anti.get("same_ending_family_count") or 0) > 0
        or any("ending_family_repetition" in reason or "same_predicate_family_stack" in reason for reason in anti_reasons)
    ):
        codes.append(EMLIS_TWO_STAGE_PHASE17_REASON_SURFACE_MODE_POLICY_MISSING)

    report = _json_safe_mapping(two_stage_report)
    counts = _json_safe_mapping(report.get("section_line_counts"))
    if counts:
        observation_count = int(counts.get(EMLIS_TWO_STAGE_OBSERVATION_SECTION_ID) or 0)
        reception_count = int(counts.get(EMLIS_TWO_STAGE_RECEPTION_SECTION_ID) or 0)
        if observation_count > 1 or reception_count < 1 or reception_count > 2:
            codes.append(EMLIS_TWO_STAGE_PHASE17_REASON_SECTION_BUDGET_MISMATCH)
    if report and not bool(report.get("applied", True)):
        codes.append(EMLIS_TWO_STAGE_PHASE17_REASON_SURFACE_MODE_POLICY_MISSING)

    return tuple(dict.fromkeys(code for code in codes if code))


def _body_text(value: Any, *, limit: int = 0) -> str:
    """Normalize generated internal body text without reading raw input."""

    text = _SPACE_RE.sub(" ", str(value or "").replace("\u3000", " ").replace("\r", " ").replace("\n", " ")).strip(" \t\r\n　")
    if limit > 0 and len(text) > limit:
        text = text[:limit].rstrip(" \t\r\n　")
    return text


def _two_stage_only(meta: Mapping[str, Any] | None) -> dict[str, Any]:
    safe = _json_safe_mapping(meta)
    return {key: value for key, value in safe.items() if str(key).startswith("two_stage_")}


def _two_stage_line_meta(line: Any) -> dict[str, Any]:
    """Return Phase16 section meta carried by a plan line or surface line."""

    if isinstance(line, CompleteSentencePlanLine):
        return _two_stage_only(line.meta)
    if isinstance(line, Mapping):
        source = line.get("source_sentence_plan_line") if isinstance(line.get("source_sentence_plan_line"), Mapping) else line
        source_meta = source.get("meta") if isinstance(source, Mapping) and isinstance(source.get("meta"), Mapping) else {}
        return {
            **_two_stage_only(source_meta),
            **_two_stage_only(line.get("surface_signature") if isinstance(line.get("surface_signature"), Mapping) else {}),
            **_two_stage_only(line.get("meta") if isinstance(line.get("meta"), Mapping) else {}),
        }
    source_line = getattr(line, "source_sentence_plan_line", {})
    source_meta = source_line.get("meta") if isinstance(source_line, Mapping) and isinstance(source_line.get("meta"), Mapping) else {}
    surface_signature = getattr(line, "surface_signature", {})
    line_meta = getattr(line, "meta", {})
    return {
        **_two_stage_only(source_meta),
        **_two_stage_only(surface_signature if isinstance(surface_signature, Mapping) else {}),
        **_two_stage_only(line_meta if isinstance(line_meta, Mapping) else {}),
    }


def _two_stage_source_plan_meta(source_plan: Any = None, fallback_meta: Mapping[str, Any] | None = None) -> dict[str, Any]:
    merged = _two_stage_only(fallback_meta)
    if isinstance(source_plan, CompleteSentencePlanV2):
        merged.update(_two_stage_only(source_plan.meta))
        try:
            plan_meta = source_plan.as_meta()
        except Exception:
            plan_meta = {}
        merged.update(_two_stage_only(plan_meta if isinstance(plan_meta, Mapping) else {}))
    elif isinstance(source_plan, Mapping):
        merged.update(_two_stage_only(source_plan))
        nested = source_plan.get("meta")
        if isinstance(nested, Mapping):
            merged.update(_two_stage_only(nested))
    return merged


def _two_stage_section_id_for_line(line: Any) -> str:
    return _clean_token(_two_stage_line_meta(line).get("two_stage_section_id"))


def _two_stage_expected_shape_from_lines(lines: Sequence[Any], *, source_plan: Any = None, meta: Mapping[str, Any] | None = None) -> str:
    plan_meta = _two_stage_source_plan_meta(source_plan, meta)
    shape = _clean_token(
        plan_meta.get("two_stage_expected_comment_text_shape")
        or plan_meta.get("two_stage_section_surface_plan_expected_comment_text_shape")
    )
    if shape:
        return shape
    for line in lines:
        shape = _clean_token(_two_stage_line_meta(line).get("two_stage_expected_comment_text_shape"))
        if shape:
            return shape
    return ""


def _two_stage_required_for_lines(lines: Sequence[Any], *, source_plan: Any = None, meta: Mapping[str, Any] | None = None) -> bool:
    line_tuple = tuple(lines or ())
    plan_meta = _two_stage_source_plan_meta(source_plan, meta)
    expected_shape = _two_stage_expected_shape_from_lines(line_tuple, source_plan=source_plan, meta=meta)
    if bool(
        plan_meta.get("two_stage_section_surface_plan_required")
        or plan_meta.get("two_stage_section_labels_required")
        or plan_meta.get("state_answer_two_stage_display_required")
        or expected_shape == EMLIS_TWO_STAGE_COMMENT_TEXT_SHAPE
    ):
        return True
    for line in line_tuple:
        line_meta = _two_stage_line_meta(line)
        if bool(line_meta.get("two_stage_section_surface_plan_required") or line_meta.get("two_stage_section_label_required")):
            return True
        if _clean_token(line_meta.get("two_stage_expected_comment_text_shape")) == EMLIS_TWO_STAGE_COMMENT_TEXT_SHAPE:
            return True
    return False


def _two_stage_label_for_section(section_id: str, lines: Sequence[Any]) -> str:
    for line in lines:
        if _two_stage_section_id_for_line(line) != section_id:
            continue
        meta = _two_stage_line_meta(line)
        label = _body_text(meta.get("two_stage_comment_text_section_label"))
        if label:
            return label if label.endswith(("：", ":")) else f"{label}："
        display_label = _body_text(meta.get("two_stage_display_label"))
        if display_label:
            return display_label if display_label.endswith(("：", ":")) else f"{display_label}："
    return EMLIS_TWO_STAGE_DEFAULT_COMMENT_TEXT_SECTION_LABELS[section_id]


def _two_stage_strip_existing_label(text: str) -> str:
    body = _body_text(text, limit=240)
    body = re.sub(r"^\s*(?:見えたこと|Emlisから)\s*[:：]\s*", "", body)
    body = body.replace("見えたこと：", "").replace("Emlisから：", "")
    body = body.replace("見えたこと:", "").replace("Emlisから:", "")
    return _body_text(body, limit=240)


def _surface_line_text(line: Any) -> str:
    if isinstance(line, Mapping):
        return str(line.get("surface_text") or "")
    return str(getattr(line, "surface_text", "") or "")


def _surface_line_private_meta(line: Any) -> Mapping[str, Any]:
    if isinstance(line, Mapping):
        meta = line.get("meta")
    else:
        meta = getattr(line, "meta", {})
    return _json_safe_mapping(meta if isinstance(meta, Mapping) else {})


def _daily_unpleasant_context_from_two_stage_meta(meta: Mapping[str, Any] | None) -> bool:
    safe = _json_safe_mapping(meta or {})
    mode_id = _clean_token(safe.get("two_stage_reception_mode_id") or safe.get("reception_mode_id"))
    ratio_reason = _clean_token(safe.get("two_stage_ratio_reason") or safe.get("ratio_reason"))
    return bool(
        mode_id == EMLIS_TWO_STAGE_DAILY_UNPLEASANT_RECEPTION_MODE_ID
        or ratio_reason == EMLIS_TWO_STAGE_DAILY_UNPLEASANT_RATIO_REASON
    )


def _daily_unpleasant_surface_quality_hits(text: Any, meta: Mapping[str, Any] | None = None) -> Tuple[str, ...]:
    if not _daily_unpleasant_context_from_two_stage_meta(meta):
        return tuple()
    body = str(text or "")
    return tuple(
        code
        for code, pattern in DAILY_UNPLEASANT_SURFACE_QUALITY_FORBIDDEN_PATTERNS
        if pattern.search(body)
    )


def _daily_unpleasant_surface_quality_rows(lines: Sequence[Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in tuple(lines or ()):  # surface lines or line mappings
        two_stage_meta = _two_stage_line_meta(line)
        if not _daily_unpleasant_context_from_two_stage_meta(two_stage_meta):
            continue
        private_meta = _surface_line_private_meta(line)
        hits = list(_daily_unpleasant_surface_quality_hits(_surface_line_text(line), two_stage_meta))
        rows.append({
            "sentence_id": str(getattr(line, "sentence_id", "") or (line.get("sentence_id") if isinstance(line, Mapping) else "")),
            "section_id": _clean_token(two_stage_meta.get("two_stage_section_id")),
            "applied": bool(private_meta.get("daily_unpleasant_surface_quality_applied")),
            "surface_quality_key": _clean_token(private_meta.get("daily_unpleasant_surface_quality_key")),
            "source_phase": private_meta.get("daily_unpleasant_surface_quality_source_phase") or EMLIS_TWO_STAGE_DAILY_UNPLEASANT_SURFACE_QUALITY_SOURCE_PHASE,
            "forbidden_surface_hits": hits,
            "comment_text_body_included": False,
            "raw_input_included": False,
            "fixed_sentence_template_used": False,
        })
    return rows


def _daily_unpleasant_surface_quality_summary(lines: Sequence[Any]) -> dict[str, Any]:
    rows = _daily_unpleasant_surface_quality_rows(lines)
    if not rows:
        return {}
    hits = tuple(dict.fromkeys(hit for row in rows for hit in row.get("forbidden_surface_hits", [])))
    applied_keys = tuple(_clean_token(row.get("surface_quality_key")) for row in rows if row.get("applied"))
    return {
        "schema_version": EMLIS_TWO_STAGE_DAILY_UNPLEASANT_SURFACE_QUALITY_SCHEMA_VERSION,
        "source_phase": EMLIS_TWO_STAGE_DAILY_UNPLEASANT_SURFACE_QUALITY_SOURCE_PHASE,
        "target_reception_mode_id": EMLIS_TWO_STAGE_DAILY_UNPLEASANT_RECEPTION_MODE_ID,
        "applied": all(bool(row.get("applied")) for row in rows),
        "line_count": len(rows),
        "section_ids": list(dict.fromkeys(_clean_token(row.get("section_id")) for row in rows if row.get("section_id"))),
        "surface_quality_keys": list(dict.fromkeys(key for key in applied_keys if key)),
        "observation_event_reaction_shape_applied": any(key.startswith("daily_unpleasant_observation") for key in applied_keys),
        "natural_short_reception_applied": any(key.startswith("daily_unpleasant") and ("reception" in key or "receiving" in key) for key in applied_keys),
        "forbidden_surface_hits": list(hits),
        "blocked_by_surface_quality": bool(hits),
        "no_pressure_or_limit_skeleton": not any(hit in hits for hit in ("daily_unpleasant_pressure_or_limit_skeleton", "daily_unpleasant_anticipation_loop_skeleton")),
        "no_relation_skeleton_leak": "daily_unpleasant_relation_skeleton" not in hits,
        "no_low_information_prompt_escape": "daily_unpleasant_low_information_prompt_escape" not in hits,
        "no_target_judgement_agreement": "daily_unpleasant_target_judgement_agreement" not in hits,
        "no_analytic_register": "daily_unpleasant_analytic_register" not in hits,
        "no_structural_label_leak": "daily_unpleasant_structural_label_leak" not in hits,
        "gate_relaxed": False,
        "comment_text_body_included": False,
        "surface_text_body_included": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "public_response_key_added": False,
        "rn_visible_contract_changed": False,
        "fixed_sentence_template_used": False,
        "fixed_string_renderer_used": False,
        "external_ai_used": False,
        "local_llm_used": False,
    }


def _daily_unpleasant_surface_quality_errors_for_lines(lines: Sequence[Any]) -> Tuple[str, ...]:
    rows = _daily_unpleasant_surface_quality_rows(lines)
    return tuple(dict.fromkeys(f"daily_unpleasant_surface_quality:{hit}" for row in rows for hit in row.get("forbidden_surface_hits", [])))


def _daily_unpleasant_surface_text_for_line(
    line: CompleteSentencePlanLine,
    *,
    section_id: str,
    two_stage_meta: Mapping[str, Any],
) -> tuple[str, dict[str, Any]]:
    if not _daily_unpleasant_context_from_two_stage_meta(two_stage_meta):
        return "", {}
    roles = set(_meaning_roles(line))
    allowed_intents = set(_dedupe(two_stage_meta.get("allowed_surface_intents") or ()))
    line_role = _clean_token(getattr(line, "line_role", ""))
    has_reaction_role = bool(roles.intersection(DAILY_UNPLEASANT_REACTION_ROLE_KEYS))
    has_event_role = bool(roles.intersection(DAILY_UNPLEASANT_EVENT_ROLE_KEYS))
    if section_id == EMLIS_TWO_STAGE_OBSERVATION_SECTION_ID:
        if has_reaction_role or "reaction_and_event_seen_without_over_explaining" in allowed_intents:
            text = "日常の嫌な出来事に触れて、不快さや怖さ、怒りの反応が強く残っているように見えます。"
            surface_key = "daily_unpleasant_observation_event_reaction"
        elif has_event_role:
            text = "日常の中で嫌な反応が強く残る出来事として見えています。"
            surface_key = "daily_unpleasant_observation_event"
        else:
            text = "日常の中で嫌な反応が強く残る場面として見えています。"
            surface_key = "daily_unpleasant_observation_short"
    elif section_id == EMLIS_TWO_STAGE_RECEPTION_SECTION_ID:
        if line_role == "relation" and (
            has_reaction_role
            or "fear_or_load_understanding" in allowed_intents
            or "not_over_explaining_daily_event" in allowed_intents
        ):
            text = "怖さや怒りが重なって残るのも自然です。"
            surface_key = "daily_unpleasant_fear_or_load_receiving"
        elif has_event_role or "explicit_reaction_receiving" in allowed_intents:
            text = "嫌さや怖さが並んで残る、軽く流しにくい場面として受け取れます。"
            surface_key = "daily_unpleasant_natural_short_reception"
        elif has_reaction_role:
            text = "その反応は、いくつか並んで自然に残るものとして受け取れます。"
            surface_key = "daily_unpleasant_reaction_receiving"
        else:
            text = "嫌だった反応が並んで残るものとして自然に受け取れます。"
            surface_key = "daily_unpleasant_brief_receiving"
    else:
        return "", {}
    surface_ending_key = surface_key
    return text, {
        "daily_unpleasant_surface_quality_applied": True,
        "daily_unpleasant_surface_quality_source_phase": EMLIS_TWO_STAGE_DAILY_UNPLEASANT_SURFACE_QUALITY_SOURCE_PHASE,
        "daily_unpleasant_surface_quality_key": surface_key,
        "daily_unpleasant_surface_ending_key": surface_ending_key,
        "daily_unpleasant_reception_mode_id": EMLIS_TWO_STAGE_DAILY_UNPLEASANT_RECEPTION_MODE_ID,
        "daily_unpleasant_surface_role_keys": sorted(roles),
        "daily_unpleasant_allowed_surface_intents": sorted(allowed_intents),
        "daily_unpleasant_body_source": "role_and_section_meta",
        "daily_unpleasant_no_pressure_or_limit_skeleton": True,
        "daily_unpleasant_no_relation_skeleton_leak": True,
        "daily_unpleasant_no_prompt_escape": True,
        "daily_unpleasant_no_target_judgement_agreement": True,
        "daily_unpleasant_no_analytic_register": True,
        "daily_unpleasant_no_structural_label_leak": True,
        "daily_unpleasant_comment_text_body_included": False,
        "daily_unpleasant_surface_text_body_included": False,
        "raw_input_included": False,
        "comment_text_body_included": False,
        "public_response_key_added": False,
        "fixed_sentence_template_used": False,
        "fixed_string_renderer_used": False,
    }



def _two_stage_mode_specific_surface_policy_meta(
    *,
    mode_id: str,
    section_id: str,
    surface_key: str,
    roles: Iterable[Any] | None = None,
    allowed_intents: Iterable[Any] | None = None,
) -> dict[str, Any]:
    role_keys = sorted(_clean_token(role) for role in _dedupe(roles or ()) if _clean_token(role))
    intent_keys = sorted(_clean_token(intent) for intent in _dedupe(allowed_intents or ()) if _clean_token(intent))
    return {
        "two_stage_mode_specific_surface_policy_schema_version": EMLIS_TWO_STAGE_MODE_SPECIFIC_SURFACE_POLICY_SCHEMA_VERSION,
        "two_stage_mode_specific_surface_policy_source_phase": EMLIS_TWO_STAGE_MODE_SPECIFIC_SURFACE_POLICY_SOURCE_PHASE,
        "two_stage_mode_specific_surface_policy_applied": True,
        "two_stage_mode_specific_surface_mode_id": _clean_token(mode_id),
        "two_stage_mode_specific_surface_section_id": _clean_token(section_id),
        "two_stage_mode_specific_surface_key": _clean_token(surface_key),
        "two_stage_mode_specific_surface_role_keys": role_keys,
        "two_stage_mode_specific_surface_allowed_surface_intents": intent_keys,
        "two_stage_mode_specific_surface_body_source": "mode_role_section_policy",
        "two_stage_mode_specific_surface_case_id_branch_used": False,
        "two_stage_mode_specific_surface_relation_skeleton_suppressed": True,
        "two_stage_mode_specific_surface_internal_role_label_suppressed": True,
        "two_stage_mode_specific_surface_display_gate_relaxed": False,
        "two_stage_mode_specific_surface_grounding_gate_relaxed": False,
        "two_stage_mode_specific_surface_comment_text_body_included": False,
        "two_stage_mode_specific_surface_text_body_included": False,
        "two_stage_mode_specific_surface_public_response_key_added": False,
        "two_stage_mode_specific_surface_fixed_sentence_template_used": False,
        "two_stage_mode_specific_surface_fixed_string_renderer_used": False,
        "two_stage_mode_specific_surface_raw_input_included": False,
        "raw_input_included": False,
        "comment_text_body_included": False,
        "public_response_key_added": False,
        "fixed_sentence_template_used": False,
        "fixed_string_renderer_used": False,
    }


def _two_stage_mode_id_from_ratio_reason(ratio_reason: Any) -> str:
    return EMLIS_TWO_STAGE_MODE_ID_BY_RATIO_REASON.get(_clean_token(ratio_reason), "")


def _two_stage_mode_from_meta(two_stage_meta: Mapping[str, Any] | None) -> str:
    safe = dict(two_stage_meta or {})
    mode_id = _clean_token(safe.get("two_stage_reception_mode_id") or safe.get("reception_mode_id"))
    if mode_id and mode_id != "standard_state_answer":
        return mode_id
    ratio_mode_id = _two_stage_mode_id_from_ratio_reason(safe.get("two_stage_ratio_reason") or safe.get("ratio_reason"))
    return ratio_mode_id or mode_id


def _two_stage_mode_context_meta(
    two_stage_meta: Mapping[str, Any] | None,
    *,
    section_id: str,
    resolved_mode_id: str,
) -> dict[str, Any]:
    safe = dict(two_stage_meta or {})
    raw_mode_id = _clean_token(safe.get("two_stage_reception_mode_id") or safe.get("reception_mode_id"))
    ratio_reason = _clean_token(safe.get("two_stage_ratio_reason") or safe.get("ratio_reason"))
    ratio_mode_id = _two_stage_mode_id_from_ratio_reason(ratio_reason)
    if raw_mode_id and raw_mode_id != "standard_state_answer":
        source = "two_stage_reception_mode_id"
    elif ratio_mode_id:
        source = "two_stage_ratio_reason"
    else:
        source = "fallback_or_empty"
    return {
        "two_stage_mode_context_schema_version": EMLIS_TWO_STAGE_MODE_CONTEXT_SCHEMA_VERSION,
        "two_stage_mode_context_source_phase": EMLIS_TWO_STAGE_MODE_CONTEXT_SOURCE_PHASE,
        "two_stage_mode_context_section_id": _clean_token(section_id),
        "two_stage_mode_context_reception_mode_id": _clean_token(resolved_mode_id),
        "two_stage_mode_context_ratio_reason": ratio_reason,
        "two_stage_mode_context_source": source,
        "two_stage_mode_context_raw_mode_id": raw_mode_id,
        "two_stage_mode_context_ratio_mode_id": ratio_mode_id,
        "two_stage_mode_context_propagated_to_surface_realizer": bool(resolved_mode_id),
        "two_stage_mode_context_coverage_group_only_mode_selection_used": False,
        "two_stage_mode_context_case_id_branch_used": False,
        "two_stage_mode_context_comment_text_body_included": False,
        "two_stage_mode_context_public_response_key_added": False,
        "two_stage_mode_context_rn_visible_contract_changed": False,
        "raw_input_included": False,
        "comment_text_body_included": False,
        "public_response_key_added": False,
    }


def _line_index_from_two_stage_meta(two_stage_meta: Mapping[str, Any] | None) -> int:
    safe = dict(two_stage_meta or {})
    for key in ("two_stage_section_line_index", "two_stage_section_order_index"):
        try:
            return int(safe.get(key))
        except (TypeError, ValueError):
            continue
    return 0


def _self_denial_support_surface_text_for_line(
    line: CompleteSentencePlanLine,
    *,
    section_id: str,
    mode_id: str,
    two_stage_meta: Mapping[str, Any],
) -> tuple[str, dict[str, Any]]:
    roles = set(_meaning_roles(line))
    allowed_intents = set(_dedupe(two_stage_meta.get("allowed_surface_intents") or ()))
    line_role = _clean_token(getattr(line, "line_role", ""))
    line_index = _line_index_from_two_stage_meta(two_stage_meta)
    if section_id == EMLIS_TWO_STAGE_OBSERVATION_SECTION_ID:
        if line_index <= 0 or line_role == "opening":
            text = "少し立て直そうとする動きとして、自信をつけたい気持ちと不安が同時に出ているように見えます。"
            surface_key = "self_denial_observation_confidence_uncertainty_visible"
            ending_key = "self_denial_confidence_uncertainty_miemasu"
        else:
            text = "立て直そうとする流れの中で、直したい気持ちや試している動きも残っています。"
            surface_key = "self_denial_observation_attempt_remains"
            ending_key = "self_denial_attempt_nokoru"
    elif section_id == EMLIS_TWO_STAGE_RECEPTION_SECTION_ID:
        if canonical_relation_type(line.relation_type) == "recovery":
            if line_index <= 1:
                text = "不安がある中でも、挑戦したい気持ちが前の重さから少し戻る流れとして受け取れます。"
                surface_key = "self_denial_reception_recovery_attempt_received"
                ending_key = "self_denial_recovery_attempt_uketoremasu"
            else:
                text = "直したい気持ちや試している動きが、その前の負荷から少し戻る流れとして残っています。"
                surface_key = "self_denial_reception_recovery_attempt_remains"
                ending_key = "self_denial_recovery_attempt_nokoru"
        else:
            text = "不安の中でも、挑戦したい気持ちや直したい動きが消えずに残っています。"
            surface_key = "self_denial_reception_attempt_received"
            ending_key = "self_denial_attempt_uketoremasu"
    else:
        return "", {}
    return text, {
        **_two_stage_mode_specific_surface_policy_meta(
            mode_id=mode_id,
            section_id=section_id,
            surface_key=surface_key,
            roles=roles,
            allowed_intents=allowed_intents,
        ),
        "two_stage_mode_specific_surface_ending_key": ending_key,
        "two_stage_mode_specific_surface_feature_families": [
            "self_confidence_wish",
            "uncertainty_present",
            "attempt_or_challenge_present",
            "self_denial_not_accepted_as_fact",
        ],
    }


def _daily_positive_surface_text_for_line(
    line: CompleteSentencePlanLine,
    *,
    section_id: str,
    mode_id: str,
    two_stage_meta: Mapping[str, Any],
) -> tuple[str, dict[str, Any]]:
    roles = set(_meaning_roles(line))
    allowed_intents = set(_dedupe(two_stage_meta.get("allowed_surface_intents") or ()))
    line_role = _clean_token(getattr(line, "line_role", ""))
    if section_id == EMLIS_TWO_STAGE_OBSERVATION_SECTION_ID:
        text = "仕事後の疲れの負荷と、誰かと話したい気持ちが同時に出ているように見えています。"
        surface_key = "daily_positive_observation_work_fatigue_conversation_wish"
        ending_key = "daily_positive_observation_miemasu"
    elif section_id == EMLIS_TWO_STAGE_RECEPTION_SECTION_ID:
        if line_role == "relation" and canonical_relation_type(line.relation_type) == "recovery":
            text = "少し戻る流れとして、前の疲れと話したい方向が切り離されずに受け取れます。"
            surface_key = "daily_positive_reception_recovery_fatigue_bridge"
            ending_key = "daily_positive_recovery_bridge_uketoremasu"
        elif line_role == "closing":
            text = "嬉しさや動揺が、気持ちが小さく動いたサインとして残っています。"
            surface_key = "daily_positive_reception_small_change_not_overclaim"
            ending_key = "daily_positive_small_change_mimasu"
        else:
            text = "気持ちが動いた変化や嬉しさが、前の疲れから少し戻る流れとして小さく残っています。"
            surface_key = "daily_positive_reception_joy_surprise_received"
            ending_key = "daily_positive_joy_surprise_uketoremasu"
    else:
        return "", {}
    return text, {
        **_two_stage_mode_specific_surface_policy_meta(
            mode_id=mode_id,
            section_id=section_id,
            surface_key=surface_key,
            roles=roles,
            allowed_intents=allowed_intents,
        ),
        "two_stage_mode_specific_surface_ending_key": ending_key,
        "two_stage_mode_specific_surface_feature_families": [
            "work_fatigue_present",
            "conversation_wish_present",
            "positive_change_seen",
            "joy_and_surprise_coexistence_received",
        ],
    }


def _self_understanding_surface_text_for_line(
    line: CompleteSentencePlanLine,
    *,
    section_id: str,
    mode_id: str,
    two_stage_meta: Mapping[str, Any],
) -> tuple[str, dict[str, Any]]:
    roles = set(_meaning_roles(line))
    allowed_intents = set(_dedupe(two_stage_meta.get("allowed_surface_intents") or ()))
    line_role = _clean_token(getattr(line, "line_role", ""))
    line_index = _line_index_from_two_stage_meta(two_stage_meta)
    if section_id == EMLIS_TWO_STAGE_OBSERVATION_SECTION_ID:
        if line_index <= 0 or line_role == "opening":
            text = "自分を責める流れと、気持ちを少し優しく見ようとする方向が同時に残っています。"
            surface_key = "self_understanding_observation_self_blame_to_gentle_view"
            ending_key = "self_understanding_gentle_view_miemasu"
        elif line_role == "relation":
            text = "怖さや痛みを決めつけず、責める流れと見直そうとする動きが並んで残っています。"
            surface_key = "self_understanding_observation_relation_without_skeleton"
            ending_key = "self_understanding_relation_miteiru"
        else:
            text = "否定だけで終わらせない動きと、昨日の自分を見直そうとする動きが一方だけではなく並んであります。"
            surface_key = "self_understanding_observation_not_end_with_denial"
            ending_key = "self_understanding_review_miemasu"
    elif section_id == EMLIS_TWO_STAGE_RECEPTION_SECTION_ID:
        if line_index <= 1 and not (line_role == "relation" or canonical_relation_type(line.relation_type) == "recovery"):
            text = "気持ちを放置すると一番しんどくなるという見直しも、一方で受け取れます。"
            surface_key = "self_understanding_reception_feeling_observation_effort_received"
            ending_key = "self_understanding_effort_uketoremasu"
        else:
            text = "もう一方として、完璧に元気になることじゃなく、しんどさに気づいて否定だけで終わらせずに見る方向として受け取れます。"
            surface_key = "self_understanding_reception_not_end_with_denial_received"
            ending_key = "self_understanding_not_end_uketoremasu"
    else:
        return "", {}
    return text, {
        **_two_stage_mode_specific_surface_policy_meta(
            mode_id=mode_id,
            section_id=section_id,
            surface_key=surface_key,
            roles=roles,
            allowed_intents=allowed_intents,
        ),
        "two_stage_mode_specific_surface_ending_key": ending_key,
        "two_stage_mode_specific_surface_feature_families": [
            "self_blame_flow_seen",
            "gentle_self_observation_direction_seen",
            "not_end_with_self_denial_received",
            "feeling_observation_effort_received",
        ],
    }


def _learning_shift_surface_text_for_line(
    line: CompleteSentencePlanLine,
    *,
    section_id: str,
    mode_id: str,
    two_stage_meta: Mapping[str, Any],
) -> tuple[str, dict[str, Any]]:
    roles = set(_meaning_roles(line))
    allowed_intents = set(_dedupe(two_stage_meta.get("allowed_surface_intents") or ()))
    line_role = _clean_token(getattr(line, "line_role", ""))
    line_index = _line_index_from_two_stage_meta(two_stage_meta)
    if section_id == EMLIS_TWO_STAGE_OBSERVATION_SECTION_ID:
        if line_index <= 0 or line_role == "opening":
            text = "人へ向いていた疑問が物や環境を見る方向へ移り、人とのやり取りで考え込みすぎていた負荷に少し余白が生まれているように見えます。"
            surface_key = "learning_shift_observation_object_focus_load_margin"
            ending_key = "learning_shift_load_margin_miemasu"
        else:
            text = "人への疑問だけに寄りすぎていた負荷が、物や環境を見る視点へ移って少し整理されています。"
            surface_key = "learning_shift_observation_object_focus_rebalanced"
            ending_key = "learning_shift_rebalanced_miemasu"
    elif section_id == EMLIS_TWO_STAGE_RECEPTION_SECTION_ID:
        if line_index <= 1:
            text = "その負荷を離れて、授業で得た視点を日常の観察やメモへ移す行動にもつながっています。"
            surface_key = "learning_shift_reception_learning_observation_action"
            ending_key = "learning_shift_observation_action_tsunarimasu"
        else:
            text = "少しずつ進んでいる実感も、考え込みすぎの重さから行動へ向き直る流れとして受け取れます。"
            surface_key = "learning_shift_reception_small_progress_action_flow"
            ending_key = "learning_shift_progress_flow_uketoremasu"
    else:
        return "", {}
    return text, {
        **_two_stage_mode_specific_surface_policy_meta(
            mode_id=mode_id,
            section_id=section_id,
            surface_key=surface_key,
            roles=roles,
            allowed_intents=allowed_intents,
        ),
        **_two_stage_mode_context_meta(
            two_stage_meta,
            section_id=section_id,
            resolved_mode_id=mode_id,
        ),
        "two_stage_mode_specific_surface_ending_key": ending_key,
        "two_stage_mode_specific_surface_feature_families": [
            "object_focus_shift",
            "communication_load_reduced",
            "learning_observation_action",
            "immediate_action_courage",
            "small_progress_self_reassurance",
        ],
        "two_stage_mode_specific_surface_family": "self_understanding_learning_shift",
    }


def _relationship_gratitude_surface_text_for_line(
    line: CompleteSentencePlanLine,
    *,
    section_id: str,
    mode_id: str,
    two_stage_meta: Mapping[str, Any],
) -> tuple[str, dict[str, Any]]:
    roles = set(_meaning_roles(line))
    allowed_intents = set(_dedupe(two_stage_meta.get("allowed_surface_intents") or ()))
    line_role = _clean_token(getattr(line, "line_role", ""))
    line_index = _line_index_from_two_stage_meta(two_stage_meta)
    if section_id == EMLIS_TWO_STAGE_OBSERVATION_SECTION_ID:
        text = "少し戻る動きとして、その前の悲しさを残しながら、友達の優しさや自分のために怒ってくれる存在を受け取れているように見えます。"
        surface_key = "relationship_gratitude_observation_recovery_load_support"
        ending_key = "relationship_gratitude_recovery_sadness_support_miemasu"
    elif section_id == EMLIS_TWO_STAGE_RECEPTION_SECTION_ID:
        if line_index <= 1 or line_role in {"opening", "core"}:
            text = "形を取り直す感覚として、前の関係が終わった痛みを消すものではなく、友達とのつながりや区切りを見直す形として受け取れます。"
            surface_key = "relationship_gratitude_reception_boundary_friend_connection"
            ending_key = "relationship_gratitude_boundary_uketoremasu"
        else:
            text = "回復の入口として、前の痛みを残したまま、受け取った優しさを別の形で返したい意図も残っています。"
            surface_key = "relationship_gratitude_reception_return_kindness_intent"
            ending_key = "relationship_gratitude_return_kindness_recovery_nokoru"
    else:
        return "", {}
    return text, {
        **_two_stage_mode_specific_surface_policy_meta(
            mode_id=mode_id,
            section_id=section_id,
            surface_key=surface_key,
            roles=roles,
            allowed_intents=allowed_intents,
        ),
        **_two_stage_mode_context_meta(
            two_stage_meta,
            section_id=section_id,
            resolved_mode_id=mode_id,
        ),
        "two_stage_mode_specific_surface_ending_key": ending_key,
        "two_stage_mode_specific_surface_feature_families": [
            "relationship_end",
            "friend_support_remains",
            "friend_anger_for_user",
            "gratitude_for_care",
            "sadness_and_kindness_coexist",
            "boundary_growth",
            "return_kindness_intent",
        ],
        "two_stage_mode_specific_surface_family": "relationship_gratitude_recovery",
        "two_stage_mode_specific_surface_no_ex_partner_judgement": True,
        "two_stage_mode_specific_surface_no_anger_amplification": True,
        "two_stage_mode_specific_surface_no_sadness_flattening": True,
        "two_stage_mode_specific_surface_no_next_action_advice": True,
    }


def _effort_pace_surface_text_for_line(
    line: CompleteSentencePlanLine,
    *,
    section_id: str,
    mode_id: str,
    two_stage_meta: Mapping[str, Any],
) -> tuple[str, dict[str, Any]]:
    roles = set(_meaning_roles(line))
    allowed_intents = set(_dedupe(two_stage_meta.get("allowed_surface_intents") or ()))
    line_role = _clean_token(getattr(line, "line_role", ""))
    line_index = _line_index_from_two_stage_meta(two_stage_meta)
    if section_id == EMLIS_TWO_STAGE_OBSERVATION_SECTION_ID:
        if line_index <= 0 or line_role == "opening":
            text = "自立したい気持ちと、生活・体調・お金を確かめながら続けるペースが一緒に出ているように見えます。"
            surface_key = "effort_pace_observation_independence_life_health_money"
            ending_key = "effort_pace_context_miemasu"
        else:
            text = "生活のことと体調を確かめながら続ける形が、同時に残っています。"
            surface_key = "effort_pace_observation_sustainable_context"
            ending_key = "effort_pace_context_nokoru"
    elif section_id == EMLIS_TWO_STAGE_RECEPTION_SECTION_ID:
        if line_index <= 1:
            text = "無理に頑張り切るより、生活・体調・お金を見ながら続けるペースを探す動きも同時に残っています。"
            surface_key = "effort_pace_reception_sustainable_pace_received"
            ending_key = "effort_pace_sustainable_pace_narabu"
        else:
            text = "体調をちゃんと確かめながら、長く続けられる形を探している状態です。"
            surface_key = "effort_pace_reception_not_overeffort_received"
            ending_key = "effort_pace_not_overeffort_uketoremasu"
    else:
        return "", {}
    return text, {
        **_two_stage_mode_specific_surface_policy_meta(
            mode_id=mode_id,
            section_id=section_id,
            surface_key=surface_key,
            roles=roles,
            allowed_intents=allowed_intents,
        ),
        "two_stage_mode_specific_surface_ending_key": ending_key,
        "two_stage_mode_specific_surface_feature_families": [
            "independence_intention_seen",
            "life_health_money_context_seen",
            "sustainable_pace_received",
            "not_overeffort_received",
        ],
    }


def _two_stage_mode_specific_relation_surface_meta(
    *,
    line: CompleteSentencePlanLine,
    relation: str,
    text: str,
    previous_meta: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    signal = detect_relation_surface(text, expected_relation_types=(relation,))
    previous = _json_safe_mapping(previous_meta)
    marker_key = _clean_token(previous.get("surface_relation_marker_key") or previous.get("relation_marker_key"))
    return {
        "relation_surface_contract_version": RELATION_SURFACE_CONTRACT_VERSION,
        "surface_recovery_relation_line_aligned": False,
        "surface_recovery_relation_alignment_step": previous.get("surface_recovery_relation_alignment_step") or "",
        "surface_recovery_relation_marker_applied": False,
        "surface_relation_marker_key": marker_key,
        "relation_marker_key": marker_key,
        "relation_surface_signal": signal,
        "reader_relation_signal_detected": bool(signal.get("reader_relation_signal_detected") or signal.get("detected")),
        "reader_relation_signal_count": int(signal.get("reader_relation_signal_count") or signal.get("count") or 0),
        "reader_relation_signal_keys": list(signal.get("reader_relation_signal_keys") or signal.get("keys") or []),
        "reader_relation_signal_relation_types": list(signal.get("reader_relation_signal_relation_types") or signal.get("relation_types") or []),
        "expected_relation_types": list(signal.get("expected_relation_types") or [canonical_relation_type(relation)]),
        "meaning_added": False,
        "gate_relaxed": False,
        "raw_input_included": False,
    }


def _two_stage_mode_specific_surface_text_for_line(
    line: CompleteSentencePlanLine,
    *,
    section_id: str,
    two_stage_meta: Mapping[str, Any],
) -> tuple[str, dict[str, Any]]:
    mode_id = _two_stage_mode_from_meta(two_stage_meta)
    if mode_id == EMLIS_TWO_STAGE_DAILY_UNPLEASANT_RECEPTION_MODE_ID:
        text, meta = _daily_unpleasant_surface_text_for_line(line, section_id=section_id, two_stage_meta=two_stage_meta)
        if text:
            surface_key = _clean_token(meta.get("daily_unpleasant_surface_quality_key")) or "daily_unpleasant_surface_quality"
            return text, {
                **meta,
                **_two_stage_mode_specific_surface_policy_meta(
                    mode_id=mode_id,
                    section_id=section_id,
                    surface_key=surface_key,
                    roles=_meaning_roles(line),
                    allowed_intents=two_stage_meta.get("allowed_surface_intents") or (),
                ),
                **_two_stage_mode_context_meta(
                    two_stage_meta,
                    section_id=section_id,
                    resolved_mode_id=mode_id,
                ),
                "two_stage_mode_specific_surface_ending_key": _clean_token(meta.get("daily_unpleasant_surface_ending_key")) or surface_key,
                "two_stage_mode_specific_surface_feature_families": [
                    "daily_unpleasant_observation",
                    "fear_or_anger_seen",
                    "reaction_received",
                ],
            }
        return "", {}
    if mode_id in EMLIS_TWO_STAGE_SELF_DENIAL_SUPPORT_MODE_IDS:
        return _self_denial_support_surface_text_for_line(line, section_id=section_id, mode_id=mode_id, two_stage_meta=two_stage_meta)
    if mode_id in EMLIS_TWO_STAGE_DAILY_POSITIVE_RECEPTION_MODE_IDS:
        return _daily_positive_surface_text_for_line(line, section_id=section_id, mode_id=mode_id, two_stage_meta=two_stage_meta)
    if mode_id in EMLIS_TWO_STAGE_SELF_UNDERSTANDING_LEARNING_SHIFT_MODE_IDS:
        return _learning_shift_surface_text_for_line(line, section_id=section_id, mode_id=mode_id, two_stage_meta=two_stage_meta)
    if mode_id in EMLIS_TWO_STAGE_RELATIONSHIP_GRATITUDE_RECOVERY_MODE_IDS:
        return _relationship_gratitude_surface_text_for_line(line, section_id=section_id, mode_id=mode_id, two_stage_meta=two_stage_meta)
    if mode_id in EMLIS_TWO_STAGE_SELF_UNDERSTANDING_FOLLOW_MODE_IDS:
        return _self_understanding_surface_text_for_line(line, section_id=section_id, mode_id=mode_id, two_stage_meta=two_stage_meta)
    if mode_id in EMLIS_TWO_STAGE_EFFORT_PACE_MODE_IDS:
        return _effort_pace_surface_text_for_line(line, section_id=section_id, mode_id=mode_id, two_stage_meta=two_stage_meta)
    return "", {}


def _two_stage_mode_context_summary(lines: Sequence[Any]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for line in tuple(lines or ()):  # summary only; body is never included
        meta = _two_stage_line_meta(line)
        if not meta:
            continue
        mode_id = _clean_token(meta.get("two_stage_mode_context_reception_mode_id")) or _two_stage_mode_from_meta(meta)
        ratio_reason = _clean_token(meta.get("two_stage_mode_context_ratio_reason") or meta.get("two_stage_ratio_reason") or meta.get("ratio_reason"))
        if not mode_id and not ratio_reason:
            continue
        rows.append({
            "section_id": _clean_token(meta.get("two_stage_mode_context_section_id") or meta.get("two_stage_section_id")),
            "reception_mode_id": mode_id,
            "ratio_reason": ratio_reason,
            "mode_context_source": _clean_token(meta.get("two_stage_mode_context_source") or "two_stage_section_surface_plan"),
            "mode_context_propagated_to_sentence_line": bool(meta.get("two_stage_mode_context_propagated_to_sentence_line") or meta.get("two_stage_section_id")),
            "mode_context_propagated_to_surface_realizer": bool(meta.get("two_stage_mode_context_propagated_to_surface_realizer")),
            "coverage_group_only_mode_selection_used": bool(meta.get("two_stage_mode_context_coverage_group_only_mode_selection_used") or meta.get("two_stage_coverage_group_only_mode_selection_used")),
            "case_id_branch_used": bool(meta.get("two_stage_mode_context_case_id_branch_used") or meta.get("two_stage_case_id_branch_used")),
        })
    if not rows:
        return {}
    mode_ids = list(dict.fromkeys(row["reception_mode_id"] for row in rows if row.get("reception_mode_id")))
    ratio_reasons = list(dict.fromkeys(row["ratio_reason"] for row in rows if row.get("ratio_reason")))
    return {
        "schema_version": EMLIS_TWO_STAGE_MODE_CONTEXT_SCHEMA_VERSION,
        "source_phase": EMLIS_TWO_STAGE_MODE_CONTEXT_SOURCE_PHASE,
        "section_ids": list(dict.fromkeys(row["section_id"] for row in rows if row.get("section_id"))),
        "reception_mode_ids": mode_ids,
        "reception_mode_id": mode_ids[0] if mode_ids else "",
        "ratio_reasons": ratio_reasons,
        "ratio_reason": ratio_reasons[0] if ratio_reasons else "",
        "mode_context_sources": list(dict.fromkeys(row["mode_context_source"] for row in rows if row.get("mode_context_source"))),
        "mode_context_propagated_to_sentence_line": all(bool(row.get("mode_context_propagated_to_sentence_line")) for row in rows),
        "mode_context_propagated_to_surface_realizer": all(bool(row.get("mode_context_propagated_to_surface_realizer")) for row in rows),
        "coverage_group_only_mode_selection_used": any(bool(row.get("coverage_group_only_mode_selection_used")) for row in rows),
        "case_id_branch_used": any(bool(row.get("case_id_branch_used")) for row in rows),
        "public_response_key_added": False,
        "rn_visible_contract_changed": False,
        "comment_text_body_included": False,
        "surface_text_body_included": False,
        "raw_input_included": False,
    }


def _two_stage_mode_specific_surface_policy_rows(lines: Sequence[Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in tuple(lines or ()):  # summary only; body is never included
        meta = _two_stage_line_meta(line)
        if not bool(meta.get("two_stage_mode_specific_surface_policy_applied")):
            continue
        rows.append({
            "sentence_id": str(getattr(line, "sentence_id", "") or (line.get("sentence_id") if isinstance(line, Mapping) else "")),
            "section_id": _clean_token(meta.get("two_stage_mode_specific_surface_section_id") or meta.get("two_stage_section_id")),
            "mode_id": _clean_token(meta.get("two_stage_mode_specific_surface_mode_id") or meta.get("two_stage_reception_mode_id")),
            "surface_key": _clean_token(meta.get("two_stage_mode_specific_surface_key")),
            "feature_families": list(_dedupe(meta.get("two_stage_mode_specific_surface_feature_families") or ())),
            "case_id_branch_used": bool(meta.get("two_stage_mode_specific_surface_case_id_branch_used")),
            "relation_skeleton_suppressed": bool(meta.get("two_stage_mode_specific_surface_relation_skeleton_suppressed")),
            "internal_role_label_suppressed": bool(meta.get("two_stage_mode_specific_surface_internal_role_label_suppressed")),
        })
    return rows


def _two_stage_mode_specific_surface_policy_summary(lines: Sequence[Any]) -> dict[str, Any]:
    rows = _two_stage_mode_specific_surface_policy_rows(lines)
    if not rows:
        return {}
    modes = list(dict.fromkeys(row["mode_id"] for row in rows if row.get("mode_id")))
    surface_keys = list(dict.fromkeys(row["surface_key"] for row in rows if row.get("surface_key")))
    feature_families = list(dict.fromkeys(feature for row in rows for feature in row.get("feature_families", []) if feature))
    return {
        "schema_version": EMLIS_TWO_STAGE_MODE_SPECIFIC_SURFACE_POLICY_SCHEMA_VERSION,
        "source_phase": EMLIS_TWO_STAGE_MODE_SPECIFIC_SURFACE_POLICY_SOURCE_PHASE,
        "applied": True,
        "line_count": len(rows),
        "mode_ids": modes,
        "surface_keys": surface_keys,
        "feature_families": feature_families,
        "case_id_branch_used": any(row.get("case_id_branch_used") for row in rows),
        "relation_skeleton_suppressed": all(row.get("relation_skeleton_suppressed") for row in rows),
        "internal_role_label_suppressed": all(row.get("internal_role_label_suppressed") for row in rows),
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "comment_text_body_included": False,
        "surface_text_body_included": False,
        "raw_input_included": False,
        "public_response_key_added": False,
        "fixed_sentence_template_used": False,
        "fixed_string_renderer_used": False,
        "completed_reply_template_used": False,
        "external_ai_used": False,
        "local_llm_used": False,
    }


def _two_stage_product_surface_text_for_line(
    line: CompleteSentencePlanLine,
    *,
    section_id: str,
    two_stage_meta: Mapping[str, Any],
) -> tuple[str, dict[str, Any]]:
    return _two_stage_mode_specific_surface_text_for_line(
        line,
        section_id=section_id,
        two_stage_meta=two_stage_meta,
    )


def _mode_specific_two_stage_surface_policy_summary(lines: Sequence[Any]) -> dict[str, Any]:
    return _two_stage_mode_specific_surface_policy_summary(lines)


def _two_stage_mode_specific_surface_summary(lines: Sequence[Any]) -> dict[str, Any]:
    return _two_stage_mode_specific_surface_policy_summary(lines)


def _two_stage_lines_by_section(lines: Sequence[Any]) -> dict[str, list[Any]]:
    grouped: dict[str, list[Any]] = {section_id: [] for section_id in EMLIS_TWO_STAGE_SECTION_ORDER}
    for line in tuple(lines or ()):  # keep sentence-plan order inside each section
        section_id = _two_stage_section_id_for_line(line)
        if section_id in grouped:
            grouped[section_id].append(line)
    return grouped


def _two_stage_section_body(lines: Sequence[Any]) -> str:
    parts = [_two_stage_strip_existing_label(_surface_line_text(line)) for line in tuple(lines or ())]
    compacted: list[str] = []
    for raw_part in parts:
        part = str(raw_part or "").strip()
        if not part:
            continue
        duplicate_or_prefix_repeat = False
        for existing in compacted:
            if part == existing or part.startswith(existing):
                duplicate_or_prefix_repeat = True
                break
            if existing.startswith(part):
                duplicate_or_prefix_repeat = True
                break
        if duplicate_or_prefix_repeat:
            continue
        compacted.append(part)
    return "\n".join(compacted).strip()


def _two_stage_section_ids_in_order(lines: Sequence[Any]) -> tuple[str, ...]:
    return tuple(section_id for section_id in (_two_stage_section_id_for_line(line) for line in tuple(lines or ())) if section_id)


def _two_stage_section_order_valid(lines: Sequence[Any]) -> bool:
    ordered_ids = _two_stage_section_ids_in_order(lines)
    if EMLIS_TWO_STAGE_OBSERVATION_SECTION_ID not in ordered_ids or EMLIS_TWO_STAGE_RECEPTION_SECTION_ID not in ordered_ids:
        return False
    return ordered_ids.index(EMLIS_TWO_STAGE_OBSERVATION_SECTION_ID) < ordered_ids.index(EMLIS_TWO_STAGE_RECEPTION_SECTION_ID)


def _two_stage_body_contains_label(text: str) -> bool:
    body = str(text or "")
    return any(label in body for label in ("見えたこと：", "Emlisから：", "見えたこと:", "Emlisから:"))


def _two_stage_validation_errors_for_lines(lines: Sequence[Any], *, source_plan: Any = None, meta: Mapping[str, Any] | None = None) -> Tuple[str, ...]:
    line_tuple = tuple(lines or ())
    if not _two_stage_required_for_lines(line_tuple, source_plan=source_plan, meta=meta):
        return tuple()
    grouped = _two_stage_lines_by_section(line_tuple)
    observation_lines = grouped[EMLIS_TWO_STAGE_OBSERVATION_SECTION_ID]
    reception_lines = grouped[EMLIS_TWO_STAGE_RECEPTION_SECTION_ID]
    observation_body = _two_stage_section_body(observation_lines)
    reception_body = _two_stage_section_body(reception_lines)
    errors: list[str] = []
    if not observation_lines:
        errors.append("two_stage_complete_sentence_plan_observation_section_missing")
    if not reception_lines:
        errors.append("two_stage_complete_sentence_plan_reception_section_missing")
    if observation_lines and not observation_body:
        errors.append("two_stage_observation_section_empty")
    if reception_lines and not reception_body:
        errors.append("two_stage_reception_section_empty")
    if not _two_stage_section_order_valid(line_tuple):
        errors.append("two_stage_section_order_invalid")
    if _two_stage_body_contains_label(observation_body) or _two_stage_body_contains_label(reception_body):
        errors.append("two_stage_section_body_contains_label")
    errors.extend(_daily_unpleasant_surface_quality_errors_for_lines(line_tuple))
    return tuple(dict.fromkeys(errors))


def _two_stage_joined_comment_text_from_lines(lines: Sequence[Any], *, source_plan: Any = None, meta: Mapping[str, Any] | None = None) -> str:
    line_tuple = tuple(lines or ())
    if _two_stage_validation_errors_for_lines(line_tuple, source_plan=source_plan, meta=meta):
        return ""
    grouped = _two_stage_lines_by_section(line_tuple)
    observation_body = _two_stage_section_body(grouped[EMLIS_TWO_STAGE_OBSERVATION_SECTION_ID])
    reception_body = _two_stage_section_body(grouped[EMLIS_TWO_STAGE_RECEPTION_SECTION_ID])
    if not observation_body or not reception_body:
        return ""
    observation_label = _two_stage_label_for_section(EMLIS_TWO_STAGE_OBSERVATION_SECTION_ID, line_tuple)
    reception_label = _two_stage_label_for_section(EMLIS_TWO_STAGE_RECEPTION_SECTION_ID, line_tuple)
    return f"{observation_label}\n{observation_body}\n\n{reception_label}\n{reception_body}"


def _two_stage_surface_realization_report_from_lines(
    lines: Sequence[Any],
    *,
    source_plan: Any = None,
    meta: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    line_tuple = tuple(lines or ())
    if not any(_two_stage_section_id_for_line(line) for line in line_tuple) and not _two_stage_required_for_lines(line_tuple, source_plan=source_plan, meta=meta):
        return {}
    grouped = _two_stage_lines_by_section(line_tuple)
    observation_body = _two_stage_section_body(grouped[EMLIS_TWO_STAGE_OBSERVATION_SECTION_ID])
    reception_body = _two_stage_section_body(grouped[EMLIS_TWO_STAGE_RECEPTION_SECTION_ID])
    joined = _two_stage_joined_comment_text_from_lines(line_tuple, source_plan=source_plan, meta=meta)
    validation_errors = list(_two_stage_validation_errors_for_lines(line_tuple, source_plan=source_plan, meta=meta))
    daily_unpleasant_quality = _daily_unpleasant_surface_quality_summary(line_tuple)
    mode_context_summary = _two_stage_mode_context_summary(line_tuple)
    mode_specific_policy = _two_stage_mode_specific_surface_policy_summary(line_tuple)
    labels = {
        EMLIS_TWO_STAGE_OBSERVATION_SECTION_ID: _two_stage_label_for_section(EMLIS_TWO_STAGE_OBSERVATION_SECTION_ID, line_tuple),
        EMLIS_TWO_STAGE_RECEPTION_SECTION_ID: _two_stage_label_for_section(EMLIS_TWO_STAGE_RECEPTION_SECTION_ID, line_tuple),
    }
    return {
        "schema_version": EMLIS_TWO_STAGE_SURFACE_REALIZATION_SCHEMA_VERSION,
        "source_phase": EMLIS_TWO_STAGE_SURFACE_REALIZATION_SOURCE_PHASE,
        "required": _two_stage_required_for_lines(line_tuple, source_plan=source_plan, meta=meta),
        "applied": bool(joined and not validation_errors),
        "expected_comment_text_shape": _two_stage_expected_shape_from_lines(line_tuple, source_plan=source_plan, meta=meta) or EMLIS_TWO_STAGE_COMMENT_TEXT_SHAPE,
        "labels_present": bool(joined.startswith(f"{labels[EMLIS_TWO_STAGE_OBSERVATION_SECTION_ID]}\n") and f"\n\n{labels[EMLIS_TWO_STAGE_RECEPTION_SECTION_ID]}\n" in joined),
        "section_order_valid": _two_stage_section_order_valid(line_tuple),
        "section_order": list(EMLIS_TWO_STAGE_SECTION_ORDER),
        "observed_section_order": list(_two_stage_section_ids_in_order(line_tuple)),
        "observation_section_non_empty": bool(observation_body),
        "reception_section_non_empty": bool(reception_body),
        "observation_label": labels[EMLIS_TWO_STAGE_OBSERVATION_SECTION_ID],
        "reception_label": labels[EMLIS_TWO_STAGE_RECEPTION_SECTION_ID],
        "section_line_counts": {
            EMLIS_TWO_STAGE_OBSERVATION_SECTION_ID: len(grouped[EMLIS_TWO_STAGE_OBSERVATION_SECTION_ID]),
            EMLIS_TWO_STAGE_RECEPTION_SECTION_ID: len(grouped[EMLIS_TWO_STAGE_RECEPTION_SECTION_ID]),
        },
        "section_sentence_ids": {
            section_id: [str(getattr(line, "sentence_id", "") or (line.get("sentence_id") if isinstance(line, Mapping) else "")) for line in grouped[section_id]]
            for section_id in EMLIS_TWO_STAGE_SECTION_ORDER
        },
        "comment_text_generated": bool(joined),
        "two_stage_comment_text_generated": bool(joined),
        "comment_text_body_included": False,
        "surface_text_body_included": False,
        "public_response_key_added": False,
        "observation_text_public_response_key_added": False,
        "reception_text_public_response_key_added": False,
        "comment_text_key_written": False,
        "comment_text_publicly_assigned": False,
        "public_comment_text_assigned": False,
        "rn_visible_contract_changed": False,
        "db_physical_name_changed": False,
        "api_route_changed": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "completed_reply_template_used": False,
        "fixed_sentence_template_used": False,
        "fixed_string_renderer_used": False,
        "external_ai_used": False,
        "local_llm_used": False,
        "daily_unpleasant_reception_surface_quality": daily_unpleasant_quality,
        "daily_unpleasant_surface_quality": daily_unpleasant_quality,
        "daily_unpleasant_surface_quality_evaluated": bool(daily_unpleasant_quality),
        "daily_unpleasant_surface_quality_applied": bool(daily_unpleasant_quality.get("applied")) if daily_unpleasant_quality else False,
        "daily_unpleasant_surface_quality_forbidden_hits": list(daily_unpleasant_quality.get("forbidden_surface_hits") or []) if daily_unpleasant_quality else [],
        "daily_unpleasant_surface_quality_gate_relaxed": False,
        "two_stage_mode_context": mode_context_summary,
        "two_stage_mode_context_schema_version": EMLIS_TWO_STAGE_MODE_CONTEXT_SCHEMA_VERSION,
        "two_stage_mode_context_source_phase": EMLIS_TWO_STAGE_MODE_CONTEXT_SOURCE_PHASE,
        "two_stage_mode_context_propagated_to_sentence_line": bool(mode_context_summary.get("mode_context_propagated_to_sentence_line")) if mode_context_summary else False,
        "two_stage_mode_context_propagated_to_surface_realizer": bool(mode_context_summary.get("mode_context_propagated_to_surface_realizer")) if mode_context_summary else False,
        "two_stage_mode_context_coverage_group_only_mode_selection_used": bool(mode_context_summary.get("coverage_group_only_mode_selection_used")) if mode_context_summary else False,
        "two_stage_mode_context_case_id_branch_used": bool(mode_context_summary.get("case_id_branch_used")) if mode_context_summary else False,
        "two_stage_mode_context_comment_text_body_included": False,
        "two_stage_mode_context_public_response_key_added": False,
        "two_stage_mode_specific_surface_policy": mode_specific_policy,
        "two_stage_mode_specific_surface_applied": bool(mode_specific_policy.get("applied")) if mode_specific_policy else False,
        "mode_specific_two_stage_surface_policy": mode_specific_policy,
        "mode_specific_two_stage_surface_policy_applied": bool(mode_specific_policy.get("applied")) if mode_specific_policy else False,
        "product_visible_surface_policy": mode_specific_policy,
        "product_visible_surface_policy_applied": bool(mode_specific_policy.get("applied")) if mode_specific_policy else False,
        "product_visible_surface_policy_source_phase": EMLIS_TWO_STAGE_PRODUCT_VISIBLE_SURFACE_POLICY_SOURCE_PHASE,
        "two_stage_mode_specific_surface_source_phase": EMLIS_TWO_STAGE_PRODUCT_VISIBLE_SURFACE_POLICY_SOURCE_PHASE,
        "mode_specific_two_stage_surface_policy_source_phase": EMLIS_TWO_STAGE_PRODUCT_VISIBLE_SURFACE_POLICY_SOURCE_PHASE,
        "surface_section_join_shape_fixed": True,
        "surface_body_fixed_by_phase16_4": False,
        "line_body_source": "complete_surface_line_v2.surface_text",
        "validation_errors": validation_errors,
        "gate_relaxed": False,
    }


def _repeat_instance_count(values: Sequence[str], *, min_count: int = 2, ignore: Sequence[str] = ("", "none")) -> int:
    return sum(max(0, values.count(key) - 1) for key in _repeated_keys(values, min_count=min_count, ignore=ignore))


def _consecutive_repeat_count(values: Sequence[str], *, ignore: Sequence[str] = ("", "none")) -> int:
    ignored = set(ignore)
    count = 0
    previous = ""
    for value in values:
        if value and value not in ignored and value == previous:
            count += 1
        previous = value
    return count


def _realize_line(
    line: CompleteSentencePlanLine,
    *,
    sequence_index: int,
    used_predicate_keys: Sequence[str],
    used_ending_keys: Sequence[str],
    used_connector_keys: Sequence[str] | None = None,
    tone_policy: CompleteTonePolicy | Mapping[str, Any] | None = None,
) -> "CompleteSurfaceLineV2":
    relation = _surface_relation(line.relation_type)
    tone_constraint = _tone_constraint_for_line(tone_policy, line, relation)
    phrase, phrase_key, role_phrase_keys = _phrase_for_line(line)
    connector, connector_key = _connector_for(line.line_role, relation, sequence_index, used_connector_keys=used_connector_keys)
    particle, predicate, predicate_key, ending_key = _choose_predicate(
        relation_type=relation,
        line_role=line.line_role,
        used_predicate_keys=used_predicate_keys,
        used_ending_keys=used_ending_keys,
    )
    if line.line_role == "relation" and connector_key == "relation_approach_avoidance":
        body = f"{connector}{phrase}{particle}{predicate}"
    else:
        body = f"{connector}{phrase}{particle}{predicate}"
    max_chars = int(line.max_chars or 120)
    text = _truncate_sentence(body, max_chars)
    text, relation_surface_meta = _relation_surface_alignment_for_line(line, relation=relation, text=text)
    if relation_surface_meta.get("surface_recovery_relation_line_aligned"):
        marker_key = _clean_token(relation_surface_meta.get("surface_relation_marker_key") or relation_surface_meta.get("relation_marker_key"))
        if marker_key == "recovery_load_bridge_v1":
            connector_key = "relation_recovery_contract_load_bridge"
            predicate_key = "recovery_load_bridge_contract"
            phrase_key = "recovery_load_bridge"
            role_phrase_keys = _dedupe(tuple(role_phrase_keys) + ("recovery_load_bridge",))
        elif marker_key == "recovery_connected_flow_v1":
            connector_key = "relation_recovery_contract_connected_flow"
            predicate_key = "recovery_connected_flow_contract"
            phrase_key = "recovery_connected_flow"
            role_phrase_keys = _dedupe(tuple(role_phrase_keys) + ("recovery_connected_flow",))
        particle = "が"
        ending_key = "tsunagaru"
    distance_policy_key = _clean_token(tone_constraint.get("distance_policy_key")) or DISTANCE_POLICY_KEYS.get(line.line_role, "observe_without_overclaim")
    tone_policy_key = distance_policy_key
    temperature_key = _clean_token(tone_constraint.get("temperature_key"))
    closing_policy_key = _clean_token(tone_constraint.get("closing_policy_key"))
    read_feeling_policy_key = _clean_token(tone_constraint.get("read_feeling_policy_key"))
    tone_guard_keys = _tone_guard_keys(tone_constraint)
    variation_key = f"v{(sequence_index % 3) + 1}"
    observation_surface_meta = _observation_surface_signature_meta(line)
    two_stage_line_meta = _two_stage_line_meta(line)
    source_line_meta = getattr(line, "meta", None)
    daily_context_meta = {
        **(dict(source_line_meta) if isinstance(source_line_meta, Mapping) else {}),
        **two_stage_line_meta,
    }
    mode_specific_text, mode_specific_meta = _two_stage_mode_specific_surface_text_for_line(
        line,
        section_id=_clean_token(two_stage_line_meta.get("two_stage_section_id")),
        two_stage_meta=daily_context_meta,
    )
    daily_quality_meta = {key: value for key, value in mode_specific_meta.items() if str(key).startswith("daily_unpleasant_")}
    mode_context_surface_meta = {key: value for key, value in mode_specific_meta.items() if str(key).startswith("two_stage_mode_context_")}
    mode_specific_surface_meta = {
        key: value
        for key, value in mode_specific_meta.items()
        if str(key).startswith("two_stage_mode_specific_") or str(key).startswith("two_stage_mode_context_")
    }
    if mode_specific_text:
        text = _truncate_sentence(mode_specific_text, max_chars)
        connector_key = "none"
        particle = ""
        phrase_key = (
            _clean_token(mode_specific_meta.get("two_stage_mode_specific_surface_key"))
            or _clean_token(mode_specific_meta.get("daily_unpleasant_surface_quality_key"))
            or "two_stage_mode_specific_surface_policy"
        )
        predicate_key = phrase_key
        ending_key = (
            _clean_token(mode_specific_meta.get("two_stage_mode_specific_surface_ending_key"))
            or _clean_token(mode_specific_meta.get("daily_unpleasant_surface_ending_key"))
            or phrase_key
        )
        policy_marker = "daily_unpleasant_surface_quality" if daily_quality_meta else "two_stage_mode_specific_surface_policy"
        role_phrase_keys = _dedupe(tuple(role_phrase_keys) + (phrase_key, policy_marker))
        relation_surface_meta = _two_stage_mode_specific_relation_surface_meta(
            line=line,
            relation=relation,
            text=text,
            previous_meta=relation_surface_meta,
        )
    role_surface_phrase_meta = _internal_role_surface_phrase_meta(role_phrase_keys)
    signature = _surface_signature_row(
        line=line,
        phrase_key=phrase_key,
        role_phrase_keys=role_phrase_keys,
        connector_key=connector_key,
        particle=particle,
        predicate_key=predicate_key,
        ending_key=ending_key,
        distance_policy_key=distance_policy_key,
        variation_key=variation_key,
        tone_policy_key=tone_policy_key,
        temperature_key=temperature_key,
        tone_guard_keys=tone_guard_keys,
        closing_policy_key=closing_policy_key,
        read_feeling_policy_key=read_feeling_policy_key,
        relation_surface_meta=relation_surface_meta,
    )
    signature = {
        **signature,
        **role_surface_phrase_meta,
    }
    if two_stage_line_meta:
        signature = {
            **signature,
            **two_stage_line_meta,
            "two_stage_surface_signature_section_meta_present": True,
            "two_stage_surface_signature_body_included": False,
        }
    if daily_quality_meta:
        signature = {
            **signature,
            **daily_quality_meta,
            "daily_unpleasant_surface_signature_body_included": False,
        }
    if mode_context_surface_meta:
        signature = {
            **signature,
            **mode_context_surface_meta,
            "two_stage_mode_context_surface_signature_body_included": False,
        }
    if mode_specific_surface_meta:
        signature = {
            **signature,
            **mode_specific_surface_meta,
            "two_stage_mode_specific_surface_signature_body_included": False,
        }
    return CompleteSurfaceLineV2(
        sentence_id=line.sentence_id,
        line_role=line.line_role,
        relation_type=relation,
        surface_text=text,
        phrase_unit_ids=line.phrase_unit_ids,
        evidence_span_ids=line.evidence_span_ids,
        role_phrase_key=phrase_key,
        role_phrase_keys=role_phrase_keys,
        subject_policy_key="omit_second_person_subject",
        connector_key=connector_key,
        particle_key=particle,
        predicate_key=predicate_key,
        ending_key=ending_key,
        distance_policy_key=distance_policy_key,
        tone_policy_key=tone_policy_key,
        temperature_key=temperature_key,
        tone_guard_keys=tone_guard_keys,
        closing_policy_key=closing_policy_key,
        read_feeling_policy_key=read_feeling_policy_key,
        variation_key=variation_key,
        surface_signature=signature,
        forbidden_surface_keys=line.forbidden_surface_keys,
        source_sentence_plan_line=line.as_meta(),
        meta={
            "source_step": COMPLETE_SENTENCE_PLAN_STAGE,
            "target_step": COMPLETE_SURFACE_REALIZER_STAGE,
            "surface_intent": line.surface_intent,
            "repair_policy": list(line.repair_policy),
            "surface_realizer_followed_plan": True,
            **relation_surface_meta,
            **observation_surface_meta,
            **two_stage_line_meta,
            **daily_quality_meta,
            **mode_context_surface_meta,
            **mode_specific_surface_meta,
            **role_surface_phrase_meta,
            "two_stage_surface_line_section_meta_present": bool(two_stage_line_meta),
            "daily_unpleasant_surface_line_body_included": False,
            "two_stage_mode_specific_surface_line_body_included": False,
            "two_stage_surface_line_body_included": False,
            "tone_constraint": tone_constraint,
            "tone_policy_key": tone_policy_key,
            "temperature_key": temperature_key,
            "tone_guard_keys": list(tone_guard_keys),
            "tone_meaning_added": False,
            "raw_input_included": False,
        },
    )


@dataclass(frozen=True)
class CompleteSurfaceLineV2:
    """One internal realized surface line bound to a sentence plan line."""

    sentence_id: str
    line_role: str
    relation_type: str
    surface_text: str
    phrase_unit_ids: Iterable[str] = dataclass_field(default_factory=tuple)
    evidence_span_ids: Iterable[str] = dataclass_field(default_factory=tuple)
    role_phrase_key: str = ""
    role_phrase_keys: Iterable[str] = dataclass_field(default_factory=tuple)
    subject_policy_key: str = "omit_second_person_subject"
    connector_key: str = "none"
    particle_key: str = ""
    predicate_key: str = ""
    ending_key: str = ""
    distance_policy_key: str = "observe_without_overclaim"
    tone_policy_key: str = "observe_without_overclaim"
    temperature_key: str = "steady_warm"
    tone_guard_keys: Iterable[str] = dataclass_field(default_factory=tuple)
    closing_policy_key: str = "none"
    read_feeling_policy_key: str = "input_specific_structure_reflected"
    variation_key: str = "v1"
    surface_signature: Mapping[str, Any] = dataclass_field(default_factory=dict)
    forbidden_surface_keys: Iterable[str] = dataclass_field(default_factory=tuple)
    source_sentence_plan_line: Mapping[str, Any] = dataclass_field(default_factory=dict)
    meta: Mapping[str, Any] = dataclass_field(default_factory=dict)
    schema_version: str = COMPLETE_SURFACE_LINE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        relation = _surface_relation(self.relation_type)
        object.__setattr__(self, "sentence_id", _clean_token(self.sentence_id))
        object.__setattr__(self, "line_role", _clean_token(self.line_role) or "core")
        object.__setattr__(self, "relation_type", relation)
        object.__setattr__(self, "surface_text", _truncate_sentence(self.surface_text, 240))
        object.__setattr__(self, "phrase_unit_ids", _dedupe(self.phrase_unit_ids))
        object.__setattr__(self, "evidence_span_ids", _dedupe(self.evidence_span_ids))
        object.__setattr__(self, "role_phrase_key", _clean_token(self.role_phrase_key))
        object.__setattr__(self, "role_phrase_keys", _dedupe(self.role_phrase_keys))
        object.__setattr__(self, "subject_policy_key", _clean_token(self.subject_policy_key) or "omit_second_person_subject")
        object.__setattr__(self, "connector_key", _clean_token(self.connector_key) or "none")
        object.__setattr__(self, "particle_key", _clean(self.particle_key) or "が")
        object.__setattr__(self, "predicate_key", _clean_token(self.predicate_key))
        object.__setattr__(self, "ending_key", _clean_token(self.ending_key))
        object.__setattr__(self, "distance_policy_key", _clean_token(self.distance_policy_key) or "observe_without_overclaim")
        object.__setattr__(self, "tone_policy_key", _clean_token(self.tone_policy_key) or _clean_token(self.distance_policy_key) or "observe_without_overclaim")
        object.__setattr__(self, "temperature_key", _clean_token(self.temperature_key) or "steady_warm")
        object.__setattr__(self, "tone_guard_keys", _dedupe(self.tone_guard_keys))
        object.__setattr__(self, "closing_policy_key", _clean_token(self.closing_policy_key) or "none")
        object.__setattr__(self, "read_feeling_policy_key", _clean_token(self.read_feeling_policy_key) or "input_specific_structure_reflected")
        object.__setattr__(self, "variation_key", _clean_token(self.variation_key) or "v1")
        object.__setattr__(self, "surface_signature", _json_safe_mapping(self.surface_signature))
        object.__setattr__(self, "forbidden_surface_keys", _dedupe(self.forbidden_surface_keys))
        object.__setattr__(self, "source_sentence_plan_line", _json_safe_mapping(self.source_sentence_plan_line))
        object.__setattr__(self, "meta", _json_safe_mapping(self.meta))
        object.__setattr__(self, "schema_version", _clean(self.schema_version) or COMPLETE_SURFACE_LINE_SCHEMA_VERSION)

    @property
    def forbidden_surface_hits(self) -> Tuple[str, ...]:
        return _forbidden_surface_hits(self.surface_text)

    @property
    def validation_errors(self) -> Tuple[str, ...]:
        errors: list[str] = []
        if not self.sentence_id:
            errors.append("sentence_id_missing")
        if not self.surface_text:
            errors.append("surface_text_missing")
        if not self.evidence_span_ids:
            errors.append("evidence_span_ids_missing")
        if not self.phrase_unit_ids:
            errors.append("phrase_unit_ids_missing")
        if not self.relation_type:
            errors.append("relation_type_missing")
        if not self.predicate_key:
            errors.append("predicate_key_missing")
        for hit in self.forbidden_surface_hits:
            errors.append(f"forbidden_surface:{hit}")
        return tuple(dict.fromkeys(errors))

    @property
    def usable(self) -> bool:
        return not self.validation_errors

    def as_grounding_row(self) -> dict[str, Any]:
        source_line = dict(self.source_sentence_plan_line)
        def role_values(value: Any) -> list[Any]:
            if value is None:
                return []
            if isinstance(value, (list, tuple, set)):
                return list(value)
            return [value]
        phrase_roles = _dedupe(
            list(self.role_phrase_keys)
            + ([self.role_phrase_key] if self.role_phrase_key else [])
            + role_values(source_line.get("must_include_roles"))
            + role_values(source_line.get("phrase_unit_roles"))
        )
        relation_contract = _surface_relation_contract_keys(self.meta)
        if self.surface_signature:
            signature_contract = _surface_relation_contract_keys(self.surface_signature)
            if signature_contract.get("surface_recovery_relation_line_aligned"):
                relation_contract = signature_contract
        return {
            "version": self.schema_version,
            "sentence_id": self.sentence_id,
            "surface_text": self.surface_text,
            "line_role": self.line_role,
            "relation_type": self.relation_type,
            "used_evidence_span_ids": list(self.evidence_span_ids),
            "used_phrase_unit_ids": list(self.phrase_unit_ids),
            "role_phrase_key": self.role_phrase_key,
            "role_phrase_keys": list(self.role_phrase_keys),
            **_observation_surface_signature_meta(self.source_sentence_plan_line),
            **_two_stage_line_meta(self),
            **{key: value for key, value in self.meta.items() if str(key).startswith("daily_unpleasant_") or str(key).startswith("two_stage_mode_specific_surface_") or str(key).startswith("two_stage_mode_context_") or str(key).startswith("internal_role_") or str(key).startswith("unknown_internal_role_")},
            "two_stage_surface_line_body_included": False,
            "daily_unpleasant_surface_line_body_included": False,
            "phrase_unit_roles": list(phrase_roles),
            "source_sentence_plan_line": source_line,
            "surface_signature": dict(self.surface_signature),
            "relation_surface_contract_version": relation_contract["relation_surface_contract_version"],
            "surface_recovery_relation_line_aligned": relation_contract["surface_recovery_relation_line_aligned"],
            "surface_recovery_relation_alignment_step": relation_contract["surface_recovery_relation_alignment_step"],
            "surface_relation_marker_key": relation_contract["surface_relation_marker_key"],
            "relation_marker_key": relation_contract["relation_marker_key"],
            "reader_relation_signal_detected": relation_contract["reader_relation_signal_detected"],
            "reader_relation_signal_count": relation_contract["reader_relation_signal_count"],
            "reader_relation_signal_keys": relation_contract["reader_relation_signal_keys"],
            "tone_policy_key": self.tone_policy_key,
            "temperature_key": self.temperature_key,
            "tone_guard_keys": list(self.tone_guard_keys),
            "closing_policy_key": self.closing_policy_key,
            "read_feeling_policy_key": self.read_feeling_policy_key,
            "tone_engine_version": COMPLETE_TONE_ENGINE_VERSION,
            "tone_engine_2_1_version": COMPLETE_TONE_ENGINE_2_1_VERSION,
            "tone_engine_2_1_policy_version": COMPLETE_TONE_POLICY_2_1_VERSION,
            "step9_tone_engine_2_1_ready": True,
            "tone_policy_version": COMPLETE_TONE_POLICY_VERSION,
            "tone_completion_requires_blind_qa": True,
            "machine_metrics_used_for_read_feeling": False,
            "read_feeling_auto_filled_from_machine_metrics": False,
            "source_step": COMPLETE_SURFACE_REALIZER_STAGE,
            "target_step": "Step8_Binding_aware_Grounding",
            "product_quality_grounding_ready": True,
            "completion_sentence_template_used": False,
            "raw_input_included": False,
        }

    def as_meta(self, *, include_surface_text: bool = True) -> dict[str, Any]:
        two_stage_meta = _two_stage_line_meta(self)
        meta = {
            "version": self.schema_version,
            "schema_version": self.schema_version,
            "sentence_id": self.sentence_id,
            "line_role": self.line_role,
            "relation_type": self.relation_type,
            "canonical_relation_type": canonical_relation_type(self.relation_type),
            "relation_family": relation_family(self.relation_type),
            "used_evidence_span_ids": list(self.evidence_span_ids),
            "used_phrase_unit_ids": list(self.phrase_unit_ids),
            "role_phrase_key": self.role_phrase_key,
            "role_phrase_keys": list(self.role_phrase_keys),
            **_observation_surface_signature_meta(self.source_sentence_plan_line),
            **_two_stage_line_meta(self),
            **{key: value for key, value in self.meta.items() if str(key).startswith("daily_unpleasant_") or str(key).startswith("two_stage_mode_specific_surface_") or str(key).startswith("two_stage_mode_context_") or str(key).startswith("internal_role_") or str(key).startswith("unknown_internal_role_")},
            "two_stage_surface_line_body_included": False,
            "daily_unpleasant_surface_line_body_included": False,
            "subject_policy_key": self.subject_policy_key,
            "connector_key": self.connector_key,
            "particle_key": self.particle_key,
            "predicate_key": self.predicate_key,
            "ending_key": self.ending_key,
            "distance_policy_key": self.distance_policy_key,
            "tone_policy_key": self.tone_policy_key,
            "temperature_key": self.temperature_key,
            "tone_guard_keys": list(self.tone_guard_keys),
            "closing_policy_key": self.closing_policy_key,
            "read_feeling_policy_key": self.read_feeling_policy_key,
            "tone_engine_version": COMPLETE_TONE_ENGINE_VERSION,
            "tone_engine_2_1_version": COMPLETE_TONE_ENGINE_2_1_VERSION,
            "tone_engine_2_1_policy_version": COMPLETE_TONE_POLICY_2_1_VERSION,
            "step9_tone_engine_2_1_ready": True,
            "tone_policy_version": COMPLETE_TONE_POLICY_VERSION,
            "product_quality_tone_engine_version": COMPLETE_PRODUCT_QUALITY_TONE_ENGINE_VERSION,
            "tone_completion_requires_blind_qa": True,
            "machine_metrics_used_for_read_feeling": False,
            "read_feeling_auto_filled_from_machine_metrics": False,
            "tone_meaning_added": False,
            "variation_key": self.variation_key,
            "surface_signature": dict(self.surface_signature),
            "two_stage_section_id": _clean_token(two_stage_meta.get("two_stage_section_id")),
            "two_stage_section_role": _clean_token(two_stage_meta.get("two_stage_section_role")),
            "two_stage_display_label": _body_text(two_stage_meta.get("two_stage_display_label")),
            "two_stage_section_label_required": bool(two_stage_meta.get("two_stage_section_label_required")),
            "two_stage_section_order_index": two_stage_meta.get("two_stage_section_order_index"),
            "two_stage_expected_comment_text_shape": _clean_token(two_stage_meta.get("two_stage_expected_comment_text_shape")),
            "relation_surface_contract_version": self.surface_signature.get("relation_surface_contract_version") or self.meta.get("relation_surface_contract_version") or RELATION_SURFACE_CONTRACT_VERSION,
            "surface_recovery_relation_line_aligned": bool(self.surface_signature.get("surface_recovery_relation_line_aligned") or self.meta.get("surface_recovery_relation_line_aligned")),
            "surface_recovery_relation_alignment_step": self.surface_signature.get("surface_recovery_relation_alignment_step") or self.meta.get("surface_recovery_relation_alignment_step") or "",
            "surface_relation_marker_key": self.surface_signature.get("surface_relation_marker_key") or self.meta.get("surface_relation_marker_key") or self.meta.get("relation_marker_key") or "",
            "relation_marker_key": self.surface_signature.get("relation_marker_key") or self.meta.get("relation_marker_key") or "",
            "reader_relation_signal_detected": bool(self.surface_signature.get("reader_relation_signal_detected") or self.meta.get("reader_relation_signal_detected")),
            "reader_relation_signal_count": int(self.surface_signature.get("reader_relation_signal_count") or self.meta.get("reader_relation_signal_count") or 0),
            "reader_relation_signal_keys": list(self.surface_signature.get("reader_relation_signal_keys") or self.meta.get("reader_relation_signal_keys") or []),
            "surface_text_present": bool(self.surface_text),
            "surface_text_length": len(self.surface_text),
            "forbidden_surface_keys": list(self.forbidden_surface_keys),
            "forbidden_surface_hits": list(self.forbidden_surface_hits),
            "source_sentence_plan_line": dict(self.source_sentence_plan_line),
            "usable": self.usable,
            "validation_errors": list(self.validation_errors),
            "completion_sentence_template_used": False,
            "role_completed_sentence_template_used": False,
            "input_specific_template_used": False,
            "fixed_sentence_template_used": False,
            "raw_text_included": False,
            "raw_input_included": False,
            "meta": dict(self.meta),
        }
        if include_surface_text:
            meta["surface_text"] = self.surface_text
        return meta


@dataclass(frozen=True)
class CompleteSurfaceRealizationV2:
    """Internal realized text bundle for Complete Composer initial version."""

    plan_id: str
    coverage_group: str
    surface_lines: Iterable[CompleteSurfaceLineV2 | Mapping[str, Any]] = dataclass_field(default_factory=tuple)
    source_sentence_plan: CompleteSentencePlanV2 | Mapping[str, Any] | None = None
    meta: Mapping[str, Any] = dataclass_field(default_factory=dict)
    status: str = COMPLETE_SURFACE_STATUS_READY
    schema_version: str = COMPLETE_SURFACE_REALIZER_SCHEMA_VERSION

    def __post_init__(self) -> None:
        lines: list[CompleteSurfaceLineV2] = []
        for item in tuple(self.surface_lines or ()):  # mapping support for tests and future repair
            if isinstance(item, CompleteSurfaceLineV2):
                lines.append(item)
            elif isinstance(item, Mapping):
                lines.append(
                    CompleteSurfaceLineV2(
                        sentence_id=item.get("sentence_id") or "",
                        line_role=item.get("line_role") or "core",
                        relation_type=item.get("relation_type") or "center",
                        surface_text=item.get("surface_text") or "",
                        phrase_unit_ids=item.get("phrase_unit_ids") or item.get("used_phrase_unit_ids") or (),
                        evidence_span_ids=item.get("evidence_span_ids") or item.get("used_evidence_span_ids") or (),
                        role_phrase_key=item.get("role_phrase_key") or "",
                        role_phrase_keys=item.get("role_phrase_keys") or (),
                        subject_policy_key=item.get("subject_policy_key") or "omit_second_person_subject",
                        connector_key=item.get("connector_key") or "none",
                        particle_key=item.get("particle_key") or "",
                        predicate_key=item.get("predicate_key") or "",
                        ending_key=item.get("ending_key") or "",
                        distance_policy_key=item.get("distance_policy_key") or "observe_without_overclaim",
                        tone_policy_key=item.get("tone_policy_key") or item.get("distance_policy_key") or "observe_without_overclaim",
                        temperature_key=item.get("temperature_key") or "steady_warm",
                        tone_guard_keys=item.get("tone_guard_keys") or (),
                        closing_policy_key=item.get("closing_policy_key") or "none",
                        read_feeling_policy_key=item.get("read_feeling_policy_key") or "input_specific_structure_reflected",
                        variation_key=item.get("variation_key") or "v1",
                        surface_signature=item.get("surface_signature") or {},
                        forbidden_surface_keys=item.get("forbidden_surface_keys") or (),
                        source_sentence_plan_line=item.get("source_sentence_plan_line") or {},
                        meta=item.get("meta") or {},
                    )
                )
        source_plan = _coerce_sentence_plan(self.source_sentence_plan)
        safe_meta = _json_safe_mapping(self.meta)
        object.__setattr__(self, "plan_id", _clean_token(self.plan_id) or (source_plan.plan_id if source_plan else "complete_surface_realization_v2"))
        object.__setattr__(self, "coverage_group", _clean_token(self.coverage_group) or (source_plan.coverage_group if source_plan else "unknown"))
        object.__setattr__(self, "surface_lines", tuple(lines))
        object.__setattr__(self, "source_sentence_plan", source_plan)
        object.__setattr__(self, "meta", safe_meta)
        object.__setattr__(self, "schema_version", _clean(self.schema_version) or COMPLETE_SURFACE_REALIZER_SCHEMA_VERSION)
        status = _clean_token(self.status) or COMPLETE_SURFACE_STATUS_READY
        if status not in {COMPLETE_SURFACE_STATUS_READY, COMPLETE_SURFACE_STATUS_UNAVAILABLE}:
            status = COMPLETE_SURFACE_STATUS_UNAVAILABLE
        if not lines or any(not line.usable for line in lines):
            status = COMPLETE_SURFACE_STATUS_UNAVAILABLE
        if _two_stage_validation_errors_for_lines(tuple(lines), source_plan=source_plan, meta=safe_meta):
            status = COMPLETE_SURFACE_STATUS_UNAVAILABLE
        object.__setattr__(self, "status", status)

    @property
    def ready(self) -> bool:
        return self.status == COMPLETE_SURFACE_STATUS_READY and not self.validation_errors

    @property
    def realized_text(self) -> str:
        return "".join(line.surface_text for line in self.surface_lines if line.surface_text)

    @property
    def two_stage_surface_realization(self) -> dict[str, Any]:
        return _two_stage_surface_realization_report_from_lines(
            tuple(self.surface_lines),
            source_plan=self.source_sentence_plan,
            meta=self.meta,
        )

    @property
    def two_stage_comment_text(self) -> str:
        return _two_stage_joined_comment_text_from_lines(
            tuple(self.surface_lines),
            source_plan=self.source_sentence_plan,
            meta=self.meta,
        )

    @property
    def comment_text(self) -> str:
        # Internal candidate text for later gates.  It is not written to the
        # public response key here; ``comment_text_publicly_assigned`` remains
        # false in meta.
        two_stage_text = self.two_stage_comment_text
        if two_stage_text and self.status == COMPLETE_SURFACE_STATUS_READY:
            return two_stage_text
        return self.realized_text if self.status == COMPLETE_SURFACE_STATUS_READY else ""

    @property
    def used_evidence_span_ids(self) -> Tuple[str, ...]:
        return _dedupe(item for line in self.surface_lines for item in line.evidence_span_ids)

    @property
    def used_phrase_unit_ids(self) -> Tuple[str, ...]:
        return _dedupe(item for line in self.surface_lines for item in line.phrase_unit_ids)

    @property
    def relation_types(self) -> Tuple[str, ...]:
        return _dedupe(line.relation_type for line in self.surface_lines)

    @property
    def ending_keys(self) -> Tuple[str, ...]:
        return tuple(line.ending_key for line in self.surface_lines if line.ending_key)

    @property
    def connector_keys(self) -> Tuple[str, ...]:
        return tuple(line.connector_key for line in self.surface_lines if line.connector_key)

    @property
    def predicate_keys(self) -> Tuple[str, ...]:
        return tuple(line.predicate_key for line in self.surface_lines if line.predicate_key)

    @property
    def surface_variation_report(self) -> dict[str, Any]:
        return _surface_variation_report_from_rows([dict(line.surface_signature) for line in self.surface_lines])

    @property
    def surface_anti_template_report(self) -> dict[str, Any]:
        report = self.surface_variation_report.get("surface_anti_template_report")
        if isinstance(report, Mapping):
            return dict(report)
        return build_surface_realizer_anti_template_report([dict(line.surface_signature) for line in self.surface_lines])

    @property
    def surface_anti_template_guard_passed(self) -> bool:
        return not bool(self.surface_anti_template_report.get("anti_template_major_detected"))

    @property
    def same_ending_repeat_count(self) -> int:
        counts = _value_counts(self.ending_keys)
        return sum(max(0, count - 1) for count in counts.values() if count >= 2)

    @property
    def same_ending_consecutive_count(self) -> int:
        endings = list(self.ending_keys)
        return sum(1 for index in range(1, len(endings)) if endings[index] == endings[index - 1])

    @property
    def surface_signature_repeat_count(self) -> int:
        return int(self.surface_variation_report.get("surface_signature_repeat_count") or 0)

    @property
    def surface_variation_profile(self) -> dict[str, Any]:
        report = dict(self.surface_variation_report)
        report.setdefault("version", COMPLETE_SURFACE_VARIATION_PROFILE_VERSION)
        report.setdefault("policy_version", COMPLETE_SURFACE_VARIATION_POLICY_VERSION)
        report.setdefault("source_step", COMPLETE_SURFACE_REALIZER_STAGE)
        report.setdefault("surface_variation_guard_passed", bool(report.get("passed", True)))
        report.setdefault("surface_realizer_anti_template_version", COMPLETE_SURFACE_REALIZER_2_1_ANTI_TEMPLATE_VERSION)
        report.setdefault("anti_template_policy_version", COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_POLICY_VERSION)
        report.setdefault("surface_anti_template_guard_passed", bool(report.get("surface_anti_template_guard_passed", True)))
        report.setdefault("same_ending_repeat_count", self.same_ending_repeat_count)
        report.setdefault("same_ending_consecutive_count", self.same_ending_consecutive_count)
        report.setdefault("surface_signature_repeat_count", self.surface_signature_repeat_count)
        report.setdefault("anti_template_policy", build_surface_realizer_anti_template_policy_meta())
        report.setdefault("surface_realizer_anti_template_report", build_surface_realizer_anti_template_report([dict(line.surface_signature) for line in self.surface_lines]))
        report.setdefault("surface_realizer_2_1_anti_template_applied", True)
        report.setdefault("completion_sentence_template_used", False)
        report.setdefault("role_completed_sentence_template_used", False)
        report.setdefault("input_specific_template_used", False)
        report.setdefault("raw_input_included", False)
        return report

    @property
    def tone_policy_meta(self) -> dict[str, Any]:
        item = self.meta.get("tone_policy") if isinstance(self.meta, Mapping) else None
        return dict(item) if isinstance(item, Mapping) else {}

    @property
    def tone_guard_report(self) -> dict[str, Any]:
        return build_complete_tone_guard_report(surface_realization=self, tone_policy=self.tone_policy_meta, comment_text=self.realized_text)

    @property
    def tone_guard_major_count(self) -> int:
        return int(self.tone_guard_report.get("tone_guard_major_count") or 0)

    @property
    def same_ending_major_count(self) -> int:
        counts: dict[str, int] = {}
        for key in self.ending_keys:
            counts[key] = counts.get(key, 0) + 1
        return sum(1 for count in counts.values() if count >= 3)

    @property
    def surface_signatures(self) -> Tuple[str, ...]:
        return tuple(str(line.surface_signature.get("signature") or "") for line in self.surface_lines if line.surface_signature.get("signature"))

    @property
    def validation_errors(self) -> Tuple[str, ...]:
        errors: list[str] = []
        if not self.surface_lines:
            errors.append("surface_lines_missing")
        for index, line in enumerate(self.surface_lines):
            for reason in line.validation_errors:
                errors.append(f"line_{index}:{reason}")
        for reason in _two_stage_validation_errors_for_lines(tuple(self.surface_lines), source_plan=self.source_sentence_plan, meta=self.meta):
            errors.append(str(reason))
        if self.same_ending_major_count > 0:
            errors.append("same_ending_major_detected")
        variation_report = self.surface_variation_report
        for reason in list(variation_report.get("blocker_reasons") or []):
            errors.append(str(reason))
        tone_report = self.tone_guard_report
        for reason in list(tone_report.get("blocker_reasons") or []):
            errors.append(f"tone_guard:{reason}")
        source_plan = self.source_sentence_plan
        if isinstance(source_plan, CompleteSentencePlanV2):
            plan_sentence_ids = {line.sentence_id for line in source_plan.sentence_plans}
            surface_sentence_ids = {line.sentence_id for line in self.surface_lines}
            if plan_sentence_ids and plan_sentence_ids != surface_sentence_ids:
                errors.append("surface_sentence_ids_do_not_match_plan")
            if len(self.surface_lines) != len(source_plan.sentence_plans):
                errors.append("surface_line_count_does_not_match_plan")
        return tuple(dict.fromkeys(errors))

    def as_grounding_input(self) -> dict[str, Any]:
        relation_surface_report = _relation_surface_report_from_lines(self.surface_lines)
        return {
            "version": COMPLETE_SURFACE_REALIZER_SCHEMA_VERSION,
            "source_step": COMPLETE_SURFACE_REALIZER_STAGE,
            "target_step": "Step8_Binding_aware_Grounding",
            "plan_id": self.plan_id,
            "coverage_group": self.coverage_group,
            "realized_text": self.realized_text,
            "two_stage_surface_realization": self.two_stage_surface_realization,
            "surface_lines": [line.as_grounding_row() for line in self.surface_lines],
            "used_evidence_span_ids": list(self.used_evidence_span_ids),
            "used_phrase_unit_ids": list(self.used_phrase_unit_ids),
            "relation_types": list(self.relation_types),
            "surface_signatures": list(self.surface_signatures),
            "surface_variation_report": self.surface_variation_report,
            "surface_anti_template_report": self.surface_variation_report.get("surface_anti_template_report") or {},
            "surface_realizer_2_1_anti_template_version": COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_VERSION,
            "surface_realizer_2_1_anti_template_step": COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_STEP,
            "surface_realizer_2_1_anti_template_applied": True,
            "surface_anti_template_guard_passed": bool(self.surface_variation_report.get("surface_anti_template_guard_passed", True)),
            "anti_template_major_count": int(self.surface_variation_report.get("anti_template_major_count") or 0),
            "anti_template_major_reasons": list(self.surface_variation_report.get("anti_template_major_reasons") or []),
            "connector_family_keys": list((self.surface_variation_report.get("surface_anti_template_report") or {}).get("connector_family_keys") or []),
            "predicate_family_keys": list((self.surface_variation_report.get("surface_anti_template_report") or {}).get("predicate_family_keys") or []),
            "ending_family_keys": list((self.surface_variation_report.get("surface_anti_template_report") or {}).get("ending_family_keys") or []),
            "generic_center_opening_count": int((self.surface_variation_report.get("surface_anti_template_report") or {}).get("generic_center_opening_count") or 0),
            "relation_line_forced_for_all_inputs": False,
            "completed_sentence_templates_added_by_step7": False,
            "input_specific_runtime_branching_added_by_step7": False,
            "relation_surface_contract_version": relation_surface_report["relation_surface_contract_version"],
            "surface_recovery_relation_line_alignment_step": relation_surface_report["surface_recovery_relation_line_alignment_step"],
            "surface_recovery_relation_line_aligned": relation_surface_report["surface_recovery_relation_line_aligned"],
            "surface_recovery_relation_line_sentence_ids": relation_surface_report["surface_recovery_relation_line_sentence_ids"],
            "surface_relation_marker_keys": relation_surface_report["surface_relation_marker_keys"],
            "reader_relation_signal_detected": relation_surface_report["reader_relation_signal_detected"],
            "reader_relation_signal_count": relation_surface_report["reader_relation_signal_count"],
            "reader_relation_signal_keys": relation_surface_report["reader_relation_signal_keys"],
            "reader_relation_signal_relation_types": relation_surface_report["reader_relation_signal_relation_types"],
            "relation_surface_report": relation_surface_report,
            "tone_policy": self.tone_policy_meta,
            "tone_guard_report": self.tone_guard_report,
            "tone_engine_2_1_report": self.tone_guard_report.get("tone_engine_2_1_report") or self.tone_guard_report.get("step9_tone_engine_2_1_report") or {},
            "step9_tone_engine_2_1_report": self.tone_guard_report.get("step9_tone_engine_2_1_report") or self.tone_guard_report.get("tone_engine_2_1_report") or {},
            "tone_engine_version": COMPLETE_TONE_ENGINE_VERSION,
            "tone_engine_2_1_version": COMPLETE_TONE_ENGINE_2_1_VERSION,
            "tone_engine_2_1_policy_version": COMPLETE_TONE_POLICY_2_1_VERSION,
            "step9_tone_engine_2_1_ready": True,
            "tone_completion_requires_blind_qa": True,
            "machine_metrics_used_for_read_feeling": False,
            "read_feeling_auto_filled_from_machine_metrics": False,
            "product_quality_tone_engine_version": COMPLETE_PRODUCT_QUALITY_TONE_ENGINE_VERSION,
            "product_quality_surface_variation_version": COMPLETE_PRODUCT_QUALITY_SURFACE_VARIATION_VERSION,
            "raw_input_included": False,
        }

    def as_meta(self, *, include_realized_text: bool = True) -> dict[str, Any]:
        term_meta = build_complete_composer_initial_term_meta(include_legacy_aliases=False)
        source_binding = build_complete_sentence_binding_bundle_meta(self.source_sentence_plan) if isinstance(self.source_sentence_plan, CompleteSentencePlanV2) else {}
        relation_surface_report = _relation_surface_report_from_lines(self.surface_lines)
        two_stage_summary = self.two_stage_surface_realization
        daily_unpleasant_summary = two_stage_summary.get("daily_unpleasant_reception_surface_quality") if isinstance(two_stage_summary.get("daily_unpleasant_reception_surface_quality"), Mapping) else {}
        mode_specific_policy_summary = two_stage_summary.get("two_stage_mode_specific_surface_policy") if isinstance(two_stage_summary.get("two_stage_mode_specific_surface_policy"), Mapping) else {}
        mode_context_summary = two_stage_summary.get("two_stage_mode_context") if isinstance(two_stage_summary.get("two_stage_mode_context"), Mapping) else {}
        two_stage_comment_text_generated = bool(two_stage_summary.get("applied") and self.two_stage_comment_text)
        phase17_surface_repair_reason_codes = _phase17_self_repair_reason_codes_for_surface(
            lines=self.surface_lines,
            validation_errors=self.validation_errors,
            surface_variation_report=self.surface_variation_report,
            two_stage_report=two_stage_summary,
        )
        meta = {
            "version": self.schema_version,
            "schema_version": self.schema_version,
            "service_version": COMPLETE_SURFACE_REALIZER_VERSION,
            "target_step": COMPLETE_SURFACE_REALIZER_STAGE,
            "step": COMPLETE_SURFACE_REALIZER_STAGE,
            "source_step": COMPLETE_SENTENCE_PLAN_STAGE,
            "stage": COMPLETE_COMPOSER_STAGE,
            "implementation_unit": COMPLETE_SURFACE_REALIZER_IMPLEMENTATION_UNIT,
            "target_composer_term": term_meta["target_composer_term"],
            "target_composer_family_term": term_meta["target_composer_family_term"],
            "complete_composer_initial_term": term_meta["complete_composer_initial_term"],
            "status": self.status,
            "ready": self.ready,
            "plan_id": self.plan_id,
            "coverage_group": self.coverage_group,
            "surface_realizer_2_0_added": True,
            "surface_realizer_added": True,
            "surface_text_generated": bool(self.realized_text),
            "internal_realized_text_generated": bool(self.realized_text),
            "comment_text_generated": two_stage_comment_text_generated,
            "comment_text_body_included": False,
            "comment_text_key_written": False,
            "comment_text_publicly_assigned": False,
            "public_comment_text_assigned": False,
            "comment_text_contract": "passed_only",
            "two_stage_surface_realization_supported": True,
            "internal_role_surface_policy_schema_version": EMLIS_TWO_STAGE_INTERNAL_ROLE_SURFACE_POLICY_SCHEMA_VERSION,
            "internal_role_surface_policy_source_phase": EMLIS_TWO_STAGE_INTERNAL_ROLE_SURFACE_POLICY_SOURCE_PHASE,
            "internal_role_surface_phrase_bank_added": True,
            "unknown_role_fallback_leaks_english_role_label": False,
            "unknown_role_fallback_meta_only": True,
            "internal_role_surface_completion_template_used": False,
            "two_stage_surface_realization_applied": bool(two_stage_summary.get("applied", False)),
            "two_stage_comment_text_generated": two_stage_comment_text_generated,
            "two_stage_surface_realization": two_stage_summary,
            "two_stage_surface_realization_raw_input_included": False,
            "two_stage_surface_realization_comment_text_body_included": False,
            "daily_unpleasant_reception_surface_quality": dict(daily_unpleasant_summary),
            "daily_unpleasant_surface_quality_supported": True,
            "two_stage_mode_specific_surface_schema_version": EMLIS_TWO_STAGE_MODE_SPECIFIC_SURFACE_POLICY_SCHEMA_VERSION,
            "two_stage_mode_specific_surface_source_phase": EMLIS_TWO_STAGE_MODE_SPECIFIC_SURFACE_POLICY_SOURCE_PHASE,
            "two_stage_mode_specific_surface_supported": True,
            "two_stage_mode_specific_surface_applied": bool(mode_specific_policy_summary.get("applied", False)),
            "two_stage_mode_specific_surface_policy": dict(mode_specific_policy_summary),
            "two_stage_mode_specific_surface_case_id_branch_used": bool(mode_specific_policy_summary.get("case_id_branch_used", False)),
            "two_stage_mode_specific_surface_fixed_sentence_template_used": False,
            "two_stage_mode_specific_surface_raw_input_included": False,
            "two_stage_mode_specific_surface_comment_text_body_included": False,
            "two_stage_mode_specific_surface_schema_version": EMLIS_TWO_STAGE_PRODUCT_VISIBLE_SURFACE_POLICY_SCHEMA_VERSION,
            "two_stage_mode_specific_surface_source_phase": EMLIS_TWO_STAGE_PRODUCT_VISIBLE_SURFACE_POLICY_SOURCE_PHASE,
            "two_stage_mode_specific_surface_supported": True,
            "two_stage_mode_specific_surface_applied": bool(mode_specific_policy_summary.get("applied", False)),
            "two_stage_mode_specific_surface_uses_case_id_branch": False,
            "two_stage_mode_specific_surface_fixed_sentence_template_used": False,
            "two_stage_mode_specific_surface_raw_input_included": False,
            "two_stage_mode_specific_surface_comment_text_body_included": False,
            "phase17_internal_role_surface_phrase_bank_supported": True,
            "phase17_unknown_role_surface_text_leak_blocked": True,
            "phase17_7_self_repair_unavailable_reason_schema_version": EMLIS_TWO_STAGE_PHASE17_SELF_REPAIR_REASON_SCHEMA_VERSION,
            "phase17_7_self_repair_unavailable_reason_source_phase": EMLIS_TWO_STAGE_PHASE17_SELF_REPAIR_REASON_SOURCE_PHASE,
            "phase17_7_surface_repair_reason_supported": True,
            "phase17_7_surface_repair_reason_codes": list(phase17_surface_repair_reason_codes),
            "phase17_7_surface_repair_reason_summary_only": True,
            "phase17_7_surface_repair_comment_text_body_included": False,
            "phase17_7_surface_repair_raw_input_included": False,
            "phase17_7_surface_repair_display_gate_relaxed": False,
            "phase17_7_surface_repair_grounding_gate_relaxed": False,
            "phase17_7_surface_repair_fixed_sentence_template_used": False,
            "two_stage_mode_specific_surface_policy_schema_version": EMLIS_TWO_STAGE_MODE_SPECIFIC_SURFACE_POLICY_SCHEMA_VERSION,
            "two_stage_mode_specific_surface_policy_source_phase": EMLIS_TWO_STAGE_MODE_SPECIFIC_SURFACE_POLICY_SOURCE_PHASE,
            "two_stage_mode_specific_surface_policy_supported": True,
            "two_stage_mode_specific_surface_policy_applied": bool(mode_specific_policy_summary.get("applied", False)),
            "two_stage_mode_specific_surface_policy_case_id_branch_used": bool(mode_specific_policy_summary.get("case_id_branch_used", False)),
            "two_stage_mode_specific_surface_policy_comment_text_body_included": False,
            "two_stage_mode_specific_surface_policy_public_response_key_added": False,
            "two_stage_mode_specific_surface_policy_fixed_sentence_template_used": False,
            "mode_specific_two_stage_surface_policy_schema_version": EMLIS_TWO_STAGE_MODE_SPECIFIC_SURFACE_POLICY_SCHEMA_VERSION,
            "mode_specific_two_stage_surface_policy_source_phase": EMLIS_TWO_STAGE_MODE_SPECIFIC_SURFACE_POLICY_SOURCE_PHASE,
            "mode_specific_two_stage_surface_policy_supported": True,
            "mode_specific_two_stage_surface_policy_applied": bool(mode_specific_policy_summary.get("applied", False)),
            "mode_specific_two_stage_surface_policy": dict(mode_specific_policy_summary),
            "mode_specific_two_stage_surface_policy_case_id_branch_used": bool(mode_specific_policy_summary.get("case_id_branch_used", False)),
            "mode_specific_two_stage_surface_policy_fixed_sentence_template_used": False,
            "mode_specific_two_stage_surface_policy_raw_input_included": False,
            "mode_specific_two_stage_surface_policy_comment_text_body_included": False,
            "daily_unpleasant_surface_quality_applied": bool(daily_unpleasant_summary.get("applied", False)),
            "daily_unpleasant_surface_quality_passed": bool(not daily_unpleasant_summary.get("forbidden_surface_hits")),
            "daily_unpleasant_surface_quality_comment_text_body_included": False,
            "daily_unpleasant_surface_quality_raw_input_included": False,
            "daily_unpleasant_surface_quality_body_included": False,
            "two_stage_mode_context": dict(mode_context_summary),
            "two_stage_mode_context_schema_version": EMLIS_TWO_STAGE_MODE_CONTEXT_SCHEMA_VERSION,
            "two_stage_mode_context_source_phase": EMLIS_TWO_STAGE_MODE_CONTEXT_SOURCE_PHASE,
            "two_stage_mode_context_propagated_to_sentence_line": bool(mode_context_summary.get("mode_context_propagated_to_sentence_line")),
            "two_stage_mode_context_propagated_to_surface_realizer": bool(mode_context_summary.get("mode_context_propagated_to_surface_realizer")),
            "two_stage_mode_context_coverage_group_only_mode_selection_used": bool(mode_context_summary.get("coverage_group_only_mode_selection_used")),
            "two_stage_mode_context_case_id_branch_used": bool(mode_context_summary.get("case_id_branch_used")),
            "two_stage_mode_context_comment_text_body_included": False,
            "two_stage_mode_context_public_response_key_added": False,
            "two_stage_mode_context_raw_input_included": False,
            "daily_unpleasant_surface_quality_fixed_sentence_template_used": False,
            "daily_unpleasant_surface_quality_fixed_string_renderer_used": False,
            "daily_unpleasant_surface_quality_gate_relaxed": False,
            "source_sentence_plan_step": COMPLETE_SENTENCE_PLAN_STAGE,
            "sentence_plan_followed": not any("plan" in reason for reason in self.validation_errors),
            "surface_realizer_must_follow_plan": True,
            "surface_realizer_free_invention_blocked": True,
            "sentence_plan_line_count": len(tuple(self.source_sentence_plan.sentence_plans)) if isinstance(self.source_sentence_plan, CompleteSentencePlanV2) else None,
            "surface_line_count": len(self.surface_lines),
            "surface_component_row_count": len(self.surface_lines),
            "surface_text_in_meta": False,
            "surface_tail_key_count": len(self.ending_keys),
            "unique_tail_key_count": len(set(self.ending_keys)),
            "repeated_tail_keys": [key for key in dict.fromkeys(self.ending_keys) if self.ending_keys.count(key) > 1],
            "same_ending_detected": len(set(self.ending_keys)) != len(self.ending_keys),
            "used_evidence_span_ids": list(self.used_evidence_span_ids),
            "used_phrase_unit_ids": list(self.used_phrase_unit_ids),
            "relation_types": list(self.relation_types),
            "surface_signature_version": COMPLETE_SURFACE_SIGNATURE_SCHEMA_VERSION,
            "surface_signatures": list(self.surface_signatures),
            "surface_signature_rows": [dict(line.surface_signature) for line in self.surface_lines],
            "product_quality_surface_variation_version": COMPLETE_PRODUCT_QUALITY_SURFACE_VARIATION_VERSION,
            "product_quality_surface_variation_step": COMPLETE_PRODUCT_QUALITY_SURFACE_VARIATION_STEP,
            "product_quality_surface_variation": True,
            "surface_variation_strengthened": True,
            "surface_variation_report": self.surface_variation_report,
            "surface_anti_template_report": self.surface_variation_report.get("surface_anti_template_report") or {},
            "surface_realizer_2_1_anti_template_version": COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_VERSION,
            "surface_realizer_2_1_anti_template_step": COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_STEP,
            "surface_realizer_2_1_anti_template_applied": True,
            "surface_anti_template_guard_passed": bool(self.surface_variation_report.get("surface_anti_template_guard_passed", True)),
            "anti_template_major_count": int(self.surface_variation_report.get("anti_template_major_count") or 0),
            "anti_template_major_reasons": list(self.surface_variation_report.get("anti_template_major_reasons") or []),
            "connector_family_keys": list((self.surface_variation_report.get("surface_anti_template_report") or {}).get("connector_family_keys") or []),
            "predicate_family_keys": list((self.surface_variation_report.get("surface_anti_template_report") or {}).get("predicate_family_keys") or []),
            "ending_family_keys": list((self.surface_variation_report.get("surface_anti_template_report") or {}).get("ending_family_keys") or []),
            "generic_center_opening_count": int((self.surface_variation_report.get("surface_anti_template_report") or {}).get("generic_center_opening_count") or 0),
            "relation_line_forced_for_all_inputs": False,
            "completed_sentence_templates_added_by_step7": False,
            "input_specific_runtime_branching_added_by_step7": False,
            "relation_surface_contract_version": relation_surface_report["relation_surface_contract_version"],
            "surface_recovery_relation_line_alignment_step": relation_surface_report["surface_recovery_relation_line_alignment_step"],
            "surface_recovery_relation_line_aligned": relation_surface_report["surface_recovery_relation_line_aligned"],
            "surface_recovery_relation_line_sentence_ids": relation_surface_report["surface_recovery_relation_line_sentence_ids"],
            "surface_relation_marker_keys": relation_surface_report["surface_relation_marker_keys"],
            "reader_relation_signal_detected": relation_surface_report["reader_relation_signal_detected"],
            "reader_relation_signal_count": relation_surface_report["reader_relation_signal_count"],
            "reader_relation_signal_keys": relation_surface_report["reader_relation_signal_keys"],
            "reader_relation_signal_relation_types": relation_surface_report["reader_relation_signal_relation_types"],
            "relation_surface_report": relation_surface_report,
            "connector_keys": list(self.connector_keys),
            "unique_connector_key_count": len(set(self.connector_keys)),
            "repeated_connector_keys": list(self.surface_variation_report.get("repeated_connector_keys") or []),
            "predicate_keys": list(self.predicate_keys),
            "unique_predicate_key_count": len(set(self.predicate_keys)),
            "same_ending_major_count": self.same_ending_major_count,
            "same_ending_guard_passed": self.same_ending_major_count == 0,
            "second_person_subject_omitted": all(line.subject_policy_key == "omit_second_person_subject" for line in self.surface_lines),
            "subject_policy_applied": True,
            "subject_policy_enabled": True,
            "connector_policy_applied": True,
            "connector_policy_enabled": True,
            "predicate_bank_applied": True,
            "predicate_bank_enabled": True,
            "ending_policy_applied": True,
            "ending_policy_enabled": True,
            "distance_policy_applied": True,
            "distance_policy_enabled": True,
            "tone_engine_version": COMPLETE_TONE_ENGINE_VERSION,
            "tone_engine_2_1_version": COMPLETE_TONE_ENGINE_2_1_VERSION,
            "tone_engine_2_1_policy_version": COMPLETE_TONE_POLICY_2_1_VERSION,
            "tone_policy_version": COMPLETE_TONE_POLICY_VERSION,
            "product_quality_tone_engine_version": COMPLETE_PRODUCT_QUALITY_TONE_ENGINE_VERSION,
            "tone_completion_requires_blind_qa": True,
            "machine_metrics_used_for_read_feeling": False,
            "read_feeling_auto_filled_from_machine_metrics": False,
            "tone_engine_added": True,
            "tone_policy_added": True,
            "tone_policy_applied": True,
            "tone_policy": self.tone_policy_meta,
            "tone_guard_report": self.tone_guard_report,
            "tone_engine_2_1_report": self.tone_guard_report.get("tone_engine_2_1_report") or self.tone_guard_report.get("step9_tone_engine_2_1_report") or {},
            "step9_tone_engine_2_1_report": self.tone_guard_report.get("step9_tone_engine_2_1_report") or self.tone_guard_report.get("tone_engine_2_1_report") or {},
            "tone_engine_2_1_ready": bool(self.tone_guard_report.get("step9_tone_engine_2_1_ready") or self.tone_guard_report.get("tone_engine_2_1_ready")),
            "step9_tone_engine_2_1_ready": True,
            "tone_guard_major_count": self.tone_guard_major_count,
            "tone_guard_passed": self.tone_guard_major_count == 0,
            "over_empathy_guard_passed": bool(self.tone_guard_report.get("over_empathy_guard_passed", True)),
            "diagnostic_tone_guard_passed": bool(self.tone_guard_report.get("diagnostic_tone_guard_passed", True)),
            "advice_like_guard_passed": bool(self.tone_guard_report.get("advice_like_guard_passed", True)),
            "generic_comfort_guard_passed": bool(self.tone_guard_report.get("generic_comfort_guard_passed", True)),
            "temperature_policy_applied": True,
            "closing_policy_applied": True,
            "read_feeling_policy_applied": True,
            "tone_is_surface_constraint_not_post_decoration": True,
            "meaning_added_by_tone_policy": False,
            "variation_policy_applied": True,
            "variation_policy_enabled": True,
            "surface_signature_recorded": True,
            "predicate_keys": [line.predicate_key for line in self.surface_lines if line.predicate_key],
            "tail_keys": list(self.ending_keys),
            "used_tail_keys": list(self.ending_keys),
            "surface_tail_key_count": len(self.ending_keys),
            "unique_tail_key_count": len(set(self.ending_keys)),
            "repeated_tail_keys": [key for key in dict.fromkeys(self.ending_keys) if self.ending_keys.count(key) >= 2],
            "same_ending_detected": len(set(self.ending_keys)) != len(self.ending_keys),
            "same_ending_major_detected": self.same_ending_major_count > 0,
            "surface_signature_repeat_detected": self.surface_signature_repeat_count > 0,
            "surface_variation_major_detected": not self.surface_variation_profile["surface_variation_guard_passed"],
            "surface_component_rows": [line.as_meta(include_surface_text=False) for line in self.surface_lines],
            "surface_component_row_count": len(self.surface_lines),
            "surface_lines": [line.as_meta(include_surface_text=include_realized_text) for line in self.surface_lines],
            "surface_component_rows": [_surface_component_row_meta(line) for line in self.surface_lines],
            "grounding_input": self.as_grounding_input(),
            "source_sentence_binding_bundle": source_binding,
            "completion_sentence_template_used": False,
            "role_completed_sentence_template_used": False,
            "input_specific_template_used": False,
            "fixed_sentence_template_used": False,
            "fixed_sentence_template_added": False,
            "completion_sentence_templates_added": False,
            "external_ai_used": False,
            "external_ai_allowed": False,
            "local_llm_used": False,
            "local_llm_allowed": False,
            "response_shape_changed": False,
            "public_response_key_change": False,
            "api_route_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_title_changed": False,
            "raw_text_included": False,
            "raw_input_included": False,
            "raw_input_required_for_improvement": False,
            "display_gate_relaxed": False,
            "grounding_gate_relaxed": False,
            "template_gate_relaxed": False,
            "validation_errors": list(dict.fromkeys(list(self.validation_errors) + list(self.meta.get("validation_errors") or []))),
            "meta": dict(self.meta),
        }
        if include_realized_text:
            meta["realized_text"] = self.realized_text
        return meta




def _surface_component_row_meta(line: "CompleteSurfaceLineV2") -> dict[str, Any]:
    """Return a text-free component row for Template/Echo Guard style checks."""

    if isinstance(line, CompleteSurfaceLineV2):
        row = line.as_meta(include_surface_text=False)
        row.pop("surface_text", None)
        row["surface_text_in_meta"] = False
        row["componentized_surface_realizer"] = True
        row["grammar_parts_only"] = True
        row["raw_input_included"] = False
        return row
    return {}

def build_complete_surface_realizer_contract_meta() -> dict[str, Any]:
    term_meta = build_complete_composer_initial_term_meta(include_legacy_aliases=False)
    return {
        "version": COMPLETE_SURFACE_REALIZER_VERSION,
        "service_version": COMPLETE_SURFACE_REALIZER_VERSION,
        "target_step": COMPLETE_SURFACE_REALIZER_STAGE,
        "step": COMPLETE_SURFACE_REALIZER_STAGE,
        "source_step": COMPLETE_SENTENCE_PLAN_STAGE,
        "stage": COMPLETE_COMPOSER_STAGE,
        "implementation_unit": COMPLETE_SURFACE_REALIZER_IMPLEMENTATION_UNIT,
        "target_composer_term": term_meta["target_composer_term"],
        "target_composer_family_term": term_meta["target_composer_family_term"],
        "complete_composer_initial_term": term_meta["complete_composer_initial_term"],
        "surface_realizer_2_0_added": True,
        "surface_realizer_2_1_anti_template_added": True,
        "surface_realizer_anti_template_version": COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_VERSION,
        "surface_realizer_anti_template_policy_version": COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_POLICY_VERSION,
        "surface_realizer_anti_template_step": COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_STEP,
        "surface_realizer_anti_template_policy": build_surface_realizer_anti_template_policy_meta(),
        "surface_realizer_added": True,
        "product_quality_surface_variation_added": True,
        "surface_realizer_2_1_anti_template_added": True,
        "surface_realizer_2_1_anti_template_enabled": True,
        "surface_realizer_2_1_anti_template_version": COMPLETE_SURFACE_REALIZER_2_1_ANTI_TEMPLATE_VERSION,
        "surface_realizer_2_1_anti_template_step": COMPLETE_SURFACE_REALIZER_2_1_ANTI_TEMPLATE_STEP,
        "surface_realizer_anti_template_policy": build_surface_realizer_anti_template_policy_meta(),
        "surface_realizer_anti_template_policy_version": COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_POLICY_VERSION,
        "generic_center_opening_policy_enabled": True,
        "same_connector_consecutive_guard_enabled": True,
        "predicate_family_stack_guard_enabled": True,
        "ending_family_stack_guard_enabled": True,
        "relation_line_not_forced_for_all_inputs": True,
        "anti_template_completion_sentence_bank_added": False,
        "input_specific_surface_branch_added": False,
        "surface_realizer_2_1_anti_template_relaxes_gate": False,
        "surface_variation_policy_version": COMPLETE_SURFACE_VARIATION_POLICY_VERSION,
        "surface_variation_profile_version": COMPLETE_SURFACE_VARIATION_PROFILE_VERSION,
        "surface_realizer_2_0_version": COMPLETE_SURFACE_REALIZER_2_0_VERSION,
        "surface_realizer_2_1_anti_template_added": True,
        "surface_realizer_2_1_anti_template_enabled": True,
        "surface_realizer_2_1_anti_template_version": COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_VERSION,
        "surface_realizer_2_1_anti_template_policy_version": COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_POLICY_VERSION,
        "surface_realizer_2_1_anti_template_step": COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_STEP,
        "surface_realizer_2_1_anti_template_policy": build_surface_realizer_anti_template_policy_meta(),
        "generic_center_opening_policy_enabled": True,
        "connector_family_run_suppression_enabled": True,
        "predicate_family_distribution_enabled": True,
        "ending_family_distribution_enabled": True,
        "relation_line_forced_for_all_inputs": False,
        "completion_sentence_templates_added_by_step7": False,
        "input_specific_runtime_branching_added_by_step7": False,
        "accepts_sentence_plan_2_0": True,
        "accepts_complete_sentence_plan_v2": True,
        "sentence_plan_must_be_followed": True,
        "surface_realizer_must_follow_plan": True,
        "observation_surface_realizer_version": OBSERVATION_SURFACE_REALIZER_VERSION,
        "observation_surface_realizer_step": OBSERVATION_SURFACE_REALIZER_STEP,
        "surface_realizer_observation_roles_supported": True,
        "eligible_observation_roles_supported": True,
        "low_information_observation_roles_supported": True,
        "unknown_slot_question_ending_policy_enabled": True,
        "eligible_state_verbalization_relation_required": True,
        "template_skeleton_guard_enabled": True,
        "observation_surface_realizer_contract": build_observation_surface_realizer_contract_meta(include_nested_contract=False),
        "subject_policy_enabled": True,
        "predicate_bank_enabled": True,
        "connector_policy_enabled": True,
        "ending_policy_enabled": True,
        "distance_policy_enabled": True,
        "variation_policy_enabled": True,
        "surface_signature_recorded": True,
        "subject_policy_added": True,
        "subject_policy_enabled": True,
        "predicate_bank_added": True,
        "predicate_bank_enabled": True,
        "connector_policy_added": True,
        "connector_policy_enabled": True,
        "ending_policy_added": True,
        "ending_policy_enabled": True,
        "distance_policy_added": True,
        "distance_policy_enabled": True,
        "tone_engine_added": True,
        "tone_policy_added": True,
        "tone_engine_version": COMPLETE_TONE_ENGINE_VERSION,
        "tone_engine_2_1_version": COMPLETE_TONE_ENGINE_2_1_VERSION,
        "tone_engine_2_1_policy_version": COMPLETE_TONE_POLICY_2_1_VERSION,
        "step9_tone_engine_2_1_ready": True,
        "tone_policy_version": COMPLETE_TONE_POLICY_VERSION,
        "product_quality_tone_engine_version": COMPLETE_PRODUCT_QUALITY_TONE_ENGINE_VERSION,
        "tone_policy_contract": build_complete_tone_policy_contract_meta(),
        "temperature_policy_added": True,
        "closing_policy_added": True,
        "read_feeling_policy_added": True,
        "over_empathy_guard_added": True,
        "diagnostic_tone_guard_added": True,
        "advice_like_guard_added": True,
        "generic_comfort_guard_added": True,
        "tone_is_surface_constraint_not_post_decoration": True,
        "meaning_added_by_tone_policy": False,
        "variation_policy_added": True,
        "variation_policy_enabled": True,
        "surface_signature_added": True,
        "surface_signature_recorded": True,
        "surface_signature_enabled": True,
        "surface_signature_to_template_guard": True,
        "relation_surface_contract_version": RELATION_SURFACE_CONTRACT_VERSION,
        "surface_recovery_relation_line_alignment_step": COMPLETE_SURFACE_RECOVERY_RELATION_LINE_ALIGNMENT_STEP,
        "surface_recovery_relation_line_alignment_added": True,
        "surface_recovery_relation_line_uses_contract": True,
        "surface_recovery_relation_line_fixed_fallback": False,
        "surface_recovery_relation_line_completion_template": False,
        "product_quality_surface_variation_version": COMPLETE_PRODUCT_QUALITY_SURFACE_VARIATION_VERSION,
        "product_quality_surface_variation_step": COMPLETE_PRODUCT_QUALITY_SURFACE_VARIATION_STEP,
        "product_quality_surface_variation": True,
        "surface_variation_strengthened": True,
        "surface_realizer_2_1_anti_template": True,
        "surface_realizer_2_1_anti_template_changes_public_contract": False,
        "surface_realizer_2_1_anti_template_adds_completed_sentence_templates": False,
        "surface_realizer_2_1_anti_template_uses_fixture_strings": False,
        "same_ending_guard_enabled": True,
        "raw_echo_guard_material_exposed": True,
        "surface_signature_repeat_guard_enabled": True,
        "surface_text_internal_only": True,
        "two_stage_surface_realization_supported": True,
        "two_stage_surface_realization_schema_version": EMLIS_TWO_STAGE_SURFACE_REALIZATION_SCHEMA_VERSION,
        "two_stage_surface_realization_uses_sentence_plan_meta": True,
        "two_stage_surface_join_shape_fixed": True,
        "two_stage_surface_body_fixed_template_used": False,
        "two_stage_surface_public_response_key_added": False,
        "internal_role_surface_policy_schema_version": EMLIS_TWO_STAGE_INTERNAL_ROLE_SURFACE_POLICY_SCHEMA_VERSION,
        "internal_role_surface_policy_source_phase": EMLIS_TWO_STAGE_INTERNAL_ROLE_SURFACE_POLICY_SOURCE_PHASE,
        "internal_role_surface_phrase_bank_added": True,
        "unknown_role_fallback_leaks_english_role_label": False,
        "unknown_role_fallback_meta_only": True,
        "internal_role_surface_completion_template_used": False,
        "two_stage_mode_specific_surface_policy_schema_version": EMLIS_TWO_STAGE_MODE_SPECIFIC_SURFACE_POLICY_SCHEMA_VERSION,
        "two_stage_mode_specific_surface_policy_source_phase": EMLIS_TWO_STAGE_MODE_SPECIFIC_SURFACE_POLICY_SOURCE_PHASE,
        "two_stage_mode_specific_surface_policy_supported": True,
        "two_stage_mode_specific_surface_policy_case_id_branch_used": False,
        "two_stage_mode_specific_surface_policy_public_response_key_added": False,
        "two_stage_mode_specific_surface_policy_fixed_sentence_template_used": False,
        "phase17_7_self_repair_unavailable_reason_schema_version": EMLIS_TWO_STAGE_PHASE17_SELF_REPAIR_REASON_SCHEMA_VERSION,
        "phase17_7_self_repair_unavailable_reason_source_phase": EMLIS_TWO_STAGE_PHASE17_SELF_REPAIR_REASON_SOURCE_PHASE,
        "phase17_7_surface_repair_reason_supported": True,
        "phase17_7_surface_repair_reason_codes": list(EMLIS_TWO_STAGE_PHASE17_REASON_CODES),
        "phase17_7_surface_repair_reason_summary_only": True,
        "phase17_7_surface_repair_comment_text_body_included": False,
        "phase17_7_surface_repair_raw_input_included": False,
        "phase17_7_surface_repair_display_gate_relaxed": False,
        "phase17_7_surface_repair_grounding_gate_relaxed": False,
        "phase17_7_surface_repair_fixed_sentence_template_used": False,
        "comment_text_generated": False,
        "comment_text_key_written": False,
        "comment_text_publicly_assigned": False,
        "public_comment_text_assigned": False,
        "comment_text_contract": "passed_only",
        "surface_realizer_anti_template_relaxes_gate": False,
        "surface_realizer_anti_template_changes_public_contract": False,
        "surface_realizer_anti_template_adds_fixed_sentence_templates": False,
        "surface_realizer_anti_template_uses_input_specific_branching": False,
        "completion_sentence_template_used": False,
        "completed_sentence_template_allowed": False,
        "role_completed_sentence_template_used": False,
        "role_completed_sentence_template_added": False,
        "input_specific_template_used": False,
        "fixed_sentence_template_added": False,
        "fixed_sentence_template_allowed": False,
        "coverage_group_completed_sentence_added": False,
        "completion_sentence_templates_added": False,
        "external_ai_used": False,
        "external_ai_allowed": False,
        "local_llm_used": False,
        "local_llm_allowed": False,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_title_changed": False,
        "raw_text_included": False,
        "raw_input_included": False,
        "raw_input_required_for_improvement": False,
    }


def build_complete_surface_realization_v2(
    *,
    sentence_plan: CompleteSentencePlanV2 | Mapping[str, Any] | None = None,
    sentence_plan_v2: CompleteSentencePlanV2 | Mapping[str, Any] | None = None,
    plan: CompleteSentencePlanV2 | Mapping[str, Any] | None = None,
    observation_graph: Any = None,
    relation_graph: Any = None,
    coverage_plan: Any = None,
    material_bundle: Any = None,
    focus_selector_input: Mapping[str, Any] | None = None,
    evidence_spans: Sequence[Any] | None = None,
    phrase_units: Sequence[Any] | None = None,
    sentence_plan_seed: Mapping[str, Any] | None = None,
    coverage_group: str = "",
    tone_policy: CompleteTonePolicy | Mapping[str, Any] | None = None,
    meta: Mapping[str, Any] | None = None,
    **planner_kwargs: Any,
) -> CompleteSurfaceRealizationV2:
    source_plan = _coerce_sentence_plan(sentence_plan or sentence_plan_v2 or plan)
    if source_plan is None:
        source_plan = build_complete_sentence_plan_v2(
            observation_graph=observation_graph,
            relation_graph=relation_graph,
            coverage_plan=coverage_plan,
            material_bundle=material_bundle,
            focus_selector_input=focus_selector_input,
            evidence_spans=evidence_spans,
            phrase_units=phrase_units,
            sentence_plan_seed=sentence_plan_seed,
            coverage_group=coverage_group,
            **planner_kwargs,
        )
    tone_policy_obj = coerce_complete_tone_policy(tone_policy, sentence_plan=source_plan, coverage_group=source_plan.coverage_group)
    if not source_plan.usable:
        return CompleteSurfaceRealizationV2(
            plan_id=source_plan.plan_id,
            coverage_group=source_plan.coverage_group,
            surface_lines=(),
            source_sentence_plan=source_plan,
            status=COMPLETE_SURFACE_STATUS_UNAVAILABLE,
            meta={
                **build_complete_surface_realizer_contract_meta(),
                **_json_safe_mapping(meta),
                "validation_errors": list(source_plan.validation_errors),
                "reason": "sentence_plan_unusable",
                "raw_input_included": False,
                "tone_policy": tone_policy_obj.as_meta(),
                "tone_engine_version": COMPLETE_TONE_ENGINE_VERSION,
            },
        )
    used_predicate_keys: list[str] = []
    used_ending_keys: list[str] = []
    used_connector_keys: list[str] = []
    surface_lines: list[CompleteSurfaceLineV2] = []
    for index, line in enumerate(source_plan.sentence_plans):
        surface_line = _realize_line(
            line,
            sequence_index=index,
            used_predicate_keys=used_predicate_keys,
            used_ending_keys=used_ending_keys,
            used_connector_keys=used_connector_keys,
            tone_policy=tone_policy_obj,
        )
        surface_lines.append(surface_line)
        used_predicate_keys.append(surface_line.predicate_key)
        used_ending_keys.append(surface_line.ending_key)
        used_connector_keys.append(surface_line.connector_key)
    realization = CompleteSurfaceRealizationV2(
        plan_id=source_plan.plan_id,
        coverage_group=source_plan.coverage_group,
        surface_lines=surface_lines,
        source_sentence_plan=source_plan,
        status=COMPLETE_SURFACE_STATUS_READY,
        meta={
            **build_complete_surface_realizer_contract_meta(),
            **_json_safe_mapping(meta),
            "source_plan_summary": {
                "version": source_plan.schema_version,
                "source_step": COMPLETE_SENTENCE_PLAN_STAGE,
                "plan_id": source_plan.plan_id,
                "coverage_group": source_plan.coverage_group,
                "sentence_budget": source_plan.sentence_budget,
                "raw_input_included": False,
            },
            "tone_policy": tone_policy_obj.as_meta(),
            "tone_engine_version": COMPLETE_TONE_ENGINE_VERSION,
            "product_quality_tone_engine_version": COMPLETE_PRODUCT_QUALITY_TONE_ENGINE_VERSION,
        },
    )
    return realization


def build_complete_surface_realizer_v2(**kwargs: Any) -> CompleteSurfaceRealizationV2:
    return build_complete_surface_realization_v2(**kwargs)


def build_complete_surface_realizer(**kwargs: Any) -> CompleteSurfaceRealizationV2:
    return build_complete_surface_realization_v2(**kwargs)


def realize_complete_surface(**kwargs: Any) -> CompleteSurfaceRealizationV2:
    return build_complete_surface_realization_v2(**kwargs)


def build_complete_surface_signature(realization: CompleteSurfaceRealizationV2 | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(realization, CompleteSurfaceRealizationV2):
        rows = [dict(line.surface_signature) for line in realization.surface_lines]
        signatures = list(realization.surface_signatures)
        ending_keys = list(realization.ending_keys)
        relation_surface_report = _relation_surface_report_from_lines(realization.surface_lines)
        return {
            "version": COMPLETE_SURFACE_SIGNATURE_SCHEMA_VERSION,
            "source_step": COMPLETE_SURFACE_REALIZER_STAGE,
            "signature_count": len(signatures),
            "surface_signatures": signatures,
            "surface_signature_rows": rows,
            "ending_keys": ending_keys,
            "surface_variation_profile": dict(realization.surface_variation_profile),
            "surface_realizer_anti_template_report": dict(realization.surface_variation_profile.get("surface_realizer_anti_template_report") or {}),
            "surface_realizer_anti_template_policy": build_surface_realizer_anti_template_policy_meta(),
            "surface_realizer_2_1_anti_template_applied": True,
            "relation_surface_contract_version": relation_surface_report["relation_surface_contract_version"],
            "surface_recovery_relation_line_aligned": relation_surface_report["surface_recovery_relation_line_aligned"],
            "surface_relation_marker_keys": relation_surface_report["surface_relation_marker_keys"],
            "reader_relation_signal_detected": relation_surface_report["reader_relation_signal_detected"],
            "reader_relation_signal_keys": relation_surface_report["reader_relation_signal_keys"],
            "relation_surface_report": relation_surface_report,
            "tone_engine_version": COMPLETE_TONE_ENGINE_VERSION,
            "tone_policy_version": COMPLETE_TONE_POLICY_VERSION,
            "product_quality_tone_engine_version": COMPLETE_PRODUCT_QUALITY_TONE_ENGINE_VERSION,
            "tone_policy_applied": True,
            "tone_guard_report": realization.tone_guard_report,
            "tone_guard_major_count": realization.tone_guard_major_count,
            "tone_guard_passed": realization.tone_guard_major_count == 0,
            "same_ending_repeat_count": realization.same_ending_repeat_count,
            "same_ending_consecutive_count": realization.same_ending_consecutive_count,
            "same_ending_major_count": realization.same_ending_major_count,
            "surface_signature_repeat_count": realization.surface_signature_repeat_count,
            "same_ending_guard_passed": realization.same_ending_major_count == 0,
            "surface_variation_guard_passed": realization.surface_variation_profile["surface_variation_guard_passed"],
            "surface_anti_template_guard_passed": realization.surface_anti_template_guard_passed,
            "completion_sentence_template_used": False,
            "raw_input_included": False,
        }
    if isinstance(realization, Mapping):
        rows = list(realization.get("surface_signature_rows") or realization.get("surface_signatures") or ())
        return {
            "version": COMPLETE_SURFACE_SIGNATURE_SCHEMA_VERSION,
            "source_step": COMPLETE_SURFACE_REALIZER_STAGE,
            "signature_count": len(rows),
            "surface_signature_rows": _json_safe_value(rows),
            "surface_variation_profile": _json_safe_value(realization.get("surface_variation_profile") or {}),
            "surface_anti_template_report": _json_safe_value(realization.get("surface_anti_template_report") or {}),
            "surface_anti_template_guard_passed": bool(realization.get("surface_anti_template_guard_passed", True)),
            "relation_surface_contract_version": realization.get("relation_surface_contract_version") or RELATION_SURFACE_CONTRACT_VERSION,
            "surface_recovery_relation_line_aligned": bool(realization.get("surface_recovery_relation_line_aligned")),
            "same_ending_major_count": int(realization.get("same_ending_major_count") or 0),
            "surface_signature_repeat_count": int(realization.get("surface_signature_repeat_count") or 0),
            "surface_variation_guard_passed": bool(realization.get("surface_variation_guard_passed", True)),
            "completion_sentence_template_used": False,
            "raw_input_included": False,
        }
    return {
        "version": COMPLETE_SURFACE_SIGNATURE_SCHEMA_VERSION,
        "source_step": COMPLETE_SURFACE_REALIZER_STAGE,
        "signature_count": 0,
        "surface_signatures": [],
        "completion_sentence_template_used": False,
        "raw_input_included": False,
    }


def build_complete_surface_realizer_meta(*, include_realized_text: bool = True, **kwargs: Any) -> dict[str, Any]:
    realization = build_complete_surface_realization_v2(**kwargs)
    meta = realization.as_meta(include_realized_text=include_realized_text)
    meta["surface_signature"] = build_complete_surface_signature(realization)
    meta["surface_signature_meta"] = meta["surface_signature"]
    return meta


def build_complete_surface_realizer_v2_meta(*, include_realized_text: bool = True, **kwargs: Any) -> dict[str, Any]:
    return build_complete_surface_realizer_meta(include_realized_text=include_realized_text, **kwargs)


def build_complete_surface_realization_meta(*, include_realized_text: bool = True, **kwargs: Any) -> dict[str, Any]:
    return build_complete_surface_realizer_meta(include_realized_text=include_realized_text, **kwargs)


def build_complete_product_quality_surface_variation_report(
    realization: CompleteSurfaceRealizationV2 | Mapping[str, Any] | None = None,
    *,
    sentence_plan: CompleteSentencePlanV2 | Mapping[str, Any] | None = None,
    sentence_plan_seed: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Return the Step3 product-quality surface variation report.

    The report is text-independent where possible. It verifies that Surface
    Realizer produced sentence-plan-bound grammar parts, non-repeated endings,
    connector variation, and surface signatures for Template/Echo Guard.  It
    never writes public ``comment_text`` and never introduces fallback text.
    """

    if isinstance(realization, CompleteSurfaceRealizationV2):
        target = realization
    elif isinstance(realization, Mapping):
        rows = realization.get("surface_signature_rows") or realization.get("surface_lines") or ()
        return _surface_variation_report_from_rows([row for row in rows if isinstance(row, Mapping)])
    else:
        target = build_complete_surface_realization_v2(
            sentence_plan=sentence_plan,
            sentence_plan_seed=sentence_plan_seed,
            **kwargs,
        )
    report = dict(target.surface_variation_report)
    report.update(
        {
            "status": target.status,
            "ready": target.ready,
            "plan_id": target.plan_id,
            "coverage_group": target.coverage_group,
            "surface_line_count": len(target.surface_lines),
            "used_evidence_span_ids": list(target.used_evidence_span_ids),
            "used_phrase_unit_ids": list(target.used_phrase_unit_ids),
            "relation_types": list(target.relation_types),
            "surface_signatures": list(target.surface_signatures),
            "completion_sentence_template_used": bool(report.get("completion_sentence_template_used", False)),
            "fixed_sentence_template_used": False,
            "role_completed_sentence_template_used": False,
            "input_specific_template_used": False,
            "raw_input_included": bool(report.get("raw_input_included", False)),
            "comment_text_key_written": False,
            "public_comment_text_assigned": False,
            "display_gate_relaxed": False,
            "grounding_gate_relaxed": False,
            "template_gate_relaxed": False,
        }
    )
    return report


# Compatibility aliases for concise import names in future Step 8/9 work.
CompleteSurfaceLine = CompleteSurfaceLineV2
CompleteSurfaceRealization = CompleteSurfaceRealizationV2
CompleteSurfaceRealizerResult = CompleteSurfaceRealizationV2

__all__ = [
    "build_complete_product_quality_surface_variation_report",
    "COMPLETE_PRODUCT_QUALITY_SURFACE_VARIATION_VERSION",
    "COMPLETE_SURFACE_REALIZER_2_1_ANTI_TEMPLATE_VERSION",
    "COMPLETE_SURFACE_REALIZER_2_1_ANTI_TEMPLATE_STEP",
    "COMPLETE_PRODUCT_QUALITY_SURFACE_VARIATION_STEP",
    "COMPLETE_PRODUCT_QUALITY_SURFACE_VARIATION_SCHEMA_VERSION",
    "COMPLETE_SURFACE_LINE_SCHEMA_VERSION",
    "COMPLETE_SURFACE_REALIZER_SCHEMA_VERSION",
    "COMPLETE_SURFACE_REALIZER_SERVICE_VERSION",
    "COMPLETE_SURFACE_REALIZER_STAGE",
    "COMPLETE_SURFACE_REALIZER_STEP",
    "COMPLETE_SURFACE_REALIZER_TARGET_STEP",
    "COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_POLICY_VERSION",
    "COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_STEP",
    "COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_VERSION",
    "COMPLETE_SURFACE_REALIZER_VERSION",
    "COMPLETE_SURFACE_SIGNATURE_SCHEMA_VERSION",
    "COMPLETE_SURFACE_VARIATION_POLICY_VERSION",
    "COMPLETE_SURFACE_VARIATION_PROFILE_VERSION",
    "CompleteSurfaceLine",
    "CompleteSurfaceLineV2",
    "CompleteSurfaceRealization",
    "CompleteSurfaceRealizationV2",
    "CompleteSurfaceRealizerResult",
    "build_complete_surface_realization_meta",
    "build_complete_surface_realization_v2",
    "build_complete_surface_realizer",
    "build_complete_surface_realizer_contract_meta",
    "build_complete_surface_realizer_meta",
    "build_complete_surface_realizer_v2",
    "build_complete_surface_realizer_v2_meta",
    "build_complete_surface_signature",
    "realize_complete_surface",
]
