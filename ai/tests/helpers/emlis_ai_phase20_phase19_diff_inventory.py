# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase20-0 inventory for Phase19 EmlisAI diffs.

This module is test-only documentation.  It does not change production runtime.
Phase20-0 treats Phase19 A/B/C/D cases as regression fixtures and classifies
Phase19-added runtime routes, cues, mode priorities, surfaces, and public/RN
boundary tests before any later delete/quarantine/generalize work is applied.
"""

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, field
from typing import Any, Final

PHASE20_PHASE19_DIFF_REVIEW_SCHEMA_VERSION: Final = "cocolon.emlis.phase20.phase19_diff_review.v1"
PHASE20_PHASE19_DIFF_REVIEW_SOURCE_PHASE: Final = "Phase20-0_current_inventory_phase19_diff_classification"

DECISION_DELETE: Final = "delete"
DECISION_QUARANTINE: Final = "quarantine"
DECISION_GENERALIZE: Final = "generalize"
DECISION_RETAIN: Final = "retain"
PHASE20_ALLOWED_DECISIONS: Final = frozenset(
    {
        DECISION_DELETE,
        DECISION_QUARANTINE,
        DECISION_GENERALIZE,
        DECISION_RETAIN,
    }
)
PHASE20_ALLOWED_PHASE19_CASES: Final = frozenset({"A", "B", "C", "D", "boundary", "unknown"})

PHASE20_RUNTIME_TARGET_FILES: Final = frozenset(
    {
        "ai/services/ai_inference/config/emlis_reception_assistance_dictionary.v1.json",
        "ai/services/ai_inference/emlis_ai_shared_reception_evidence.py",
        "ai/services/ai_inference/emlis_ai_reception_mode_resolver.py",
        "ai/services/ai_inference/emlis_ai_two_stage_section_surface_plan.py",
        "ai/services/ai_inference/emlis_ai_complete_surface_realizer.py",
        "ai/services/ai_inference/emlis_ai_reply_service.py",
        "ai/services/ai_inference/emlis_ai_observation_display_repair_integration.py",
        "ai/services/ai_inference/emotion_submit_service.py",
    }
)
PHASE20_TEST_TARGET_FILES: Final = frozenset(
    {
        "ai/tests/test_emotion_submit_phase19_real_device_abcd_public_feedback_e2e.py",
        "ai/tests/helpers/emlis_ai_phase19_public_feedback_matrix.py",
        "ai/tests/test_emlis_ai_phase19_public_feedback_matrix.py",
        "ai/tests/test_emotion_submit_phase19_public_feedback_boundary_e2e.py",
        "Cocolon/tests/rn-screen-contracts.test.js",
    }
)


@dataclass(frozen=True)
class Phase20Phase19DiffReviewEntry:
    file_path: str
    symbol_name: str
    introduced_for_phase19_case: str
    current_decision: str
    reason: str
    replacement_design: str | None
    requires_test_update: bool
    runtime_mainline: bool = False
    exact_fixture: bool = False
    source_tokens: tuple[str, ...] = field(default_factory=tuple)

    def schema_payload(self) -> dict[str, Any]:
        """Return the Phase20 design-schema-shaped payload."""

        return {
            "file_path": self.file_path,
            "symbol_name": self.symbol_name,
            "introduced_for_phase19_case": self.introduced_for_phase19_case,
            "current_decision": self.current_decision,
            "reason": self.reason,
            "replacement_design": self.replacement_design,
            "requires_test_update": self.requires_test_update,
        }

    def meta_payload(self) -> dict[str, Any]:
        """Return a test-only payload with trace tokens for source verification."""

        payload = asdict(self)
        payload["schema_version"] = PHASE20_PHASE19_DIFF_REVIEW_SCHEMA_VERSION
        payload["source_phase"] = PHASE20_PHASE19_DIFF_REVIEW_SOURCE_PHASE
        return payload


PHASE20_PHASE19_DIFF_REVIEW_ENTRIES: Final[tuple[Phase20Phase19DiffReviewEntry, ...]] = (
    Phase20Phase19DiffReviewEntry(
        file_path="ai/services/ai_inference/config/emlis_reception_assistance_dictionary.v1.json",
        symbol_name="reaction_cues.self_understanding_learning_shift",
        introduced_for_phase19_case="C",
        current_decision=DECISION_DELETE,
        reason="C実機入力の語彙列をruntime cueにしており、例文語彙のruntime条件化に当たる。",
        replacement_design="Phase20-3で入力束のmaterial slot / relation unitへ分解し、case modeを持たない汎用材料へ移す。",
        requires_test_update=True,
        runtime_mainline=True,
        source_tokens=("\"cue_id\": \"self_understanding_learning_shift\"", "\"surface_patterns\""),
    ),
    Phase20Phase19DiffReviewEntry(
        file_path="ai/services/ai_inference/config/emlis_reception_assistance_dictionary.v1.json",
        symbol_name="reaction_cues.relationship_gratitude_recovery",
        introduced_for_phase19_case="D",
        current_decision=DECISION_DELETE,
        reason="D実機入力の関係語彙をruntime cueにしており、D専用routeの入口になっている。",
        replacement_design="Phase20-3/6で関係終了・支援・感謝・返したい意図を汎用relation materialへ移す。",
        requires_test_update=True,
        runtime_mainline=True,
        source_tokens=("\"cue_id\": \"relationship_gratitude_recovery\"", "\"surface_patterns\""),
    ),
    Phase20Phase19DiffReviewEntry(
        file_path="ai/services/ai_inference/config/emlis_reception_assistance_dictionary.v1.json",
        symbol_name="event_hints.relationship_end_gratitude_recovery_context",
        introduced_for_phase19_case="D",
        current_decision=DECISION_GENERALIZE,
        reason="関係終了と支援の同時存在は汎用材料として使えるが、現在はD専用modeを支えるhintになっている。",
        replacement_design="relationship_end / support_remains / return_intent の汎用event/relation slotに再分類する。",
        requires_test_update=True,
        runtime_mainline=True,
        source_tokens=("\"hint_id\": \"relationship_end_gratitude_recovery_context\"", "\"can_support_modes\""),
    ),
    Phase20Phase19DiffReviewEntry(
        file_path="ai/services/ai_inference/config/emlis_reception_assistance_dictionary.v1.json",
        symbol_name="reception_modes.self_understanding_learning_shift",
        introduced_for_phase19_case="C",
        current_decision=DECISION_DELETE,
        reason="C専用modeとしてratio / activation / reception policyを持っている。",
        replacement_design="self_understanding_follow等の汎用modeへ寄せず、response_kind + sentence plan材料へ吸収する。",
        requires_test_update=True,
        runtime_mainline=True,
        source_tokens=("\"mode_id\": \"self_understanding_learning_shift\"", "\"ratio_preset\": \"self_understanding_learning_shift\""),
    ),
    Phase20Phase19DiffReviewEntry(
        file_path="ai/services/ai_inference/config/emlis_reception_assistance_dictionary.v1.json",
        symbol_name="reception_modes.relationship_gratitude_recovery",
        introduced_for_phase19_case="D",
        current_decision=DECISION_DELETE,
        reason="D専用modeとしてactivation / ratio / sentence countを持っている。",
        replacement_design="関係・感情・支援・区切りを汎用materialとboundary policyに戻す。",
        requires_test_update=True,
        runtime_mainline=True,
        source_tokens=("\"mode_id\": \"relationship_gratitude_recovery\"", "\"ratio_preset\": \"relationship_end_gratitude_recovery\""),
    ),
    Phase20Phase19DiffReviewEntry(
        file_path="ai/services/ai_inference/config/emlis_reception_assistance_dictionary.v1.json",
        symbol_name="follow_shape_families.self_understanding_learning_shift_receiving",
        introduced_for_phase19_case="C",
        current_decision=DECISION_GENERALIZE,
        reason="完成文ではないが、C専用mode_idへ紐づくshape familyになっている。",
        replacement_design="object_focus_shift等のallowed intentだけを汎用sentence-plan断片へ移し、mode_id依存を外す。",
        requires_test_update=True,
        runtime_mainline=True,
        source_tokens=("\"shape_family_id\": \"self_understanding_learning_shift_receiving\"",),
    ),
    Phase20Phase19DiffReviewEntry(
        file_path="ai/services/ai_inference/config/emlis_reception_assistance_dictionary.v1.json",
        symbol_name="follow_shape_families.relationship_gratitude_recovery_receiving",
        introduced_for_phase19_case="D",
        current_decision=DECISION_GENERALIZE,
        reason="D専用mode_idへ紐づくshape familyで、後続surfaceのD専用化を支えている。",
        replacement_design="relationship support / sadness coexist / return intent を汎用surface ruleへ移す。",
        requires_test_update=True,
        runtime_mainline=True,
        source_tokens=("\"shape_family_id\": \"relationship_gratitude_recovery_receiving\"",),
    ),
    Phase20Phase19DiffReviewEntry(
        file_path="ai/services/ai_inference/emlis_ai_shared_reception_evidence.py",
        symbol_name="_REACTION_CUE_PATTERNS['self_understanding_learning_shift']",
        introduced_for_phase19_case="C",
        current_decision=DECISION_DELETE,
        reason="Cの入力例に近い語をEvidence Builderのruntime cueにしている。",
        replacement_design="語彙cueではなく、event/target/change/action/value/unknown slotの材料量判定へ移す。",
        requires_test_update=True,
        runtime_mainline=True,
        source_tokens=("\"self_understanding_learning_shift\": (", "疑問の対象"),
    ),
    Phase20Phase19DiffReviewEntry(
        file_path="ai/services/ai_inference/emlis_ai_shared_reception_evidence.py",
        symbol_name="_REACTION_CUE_PATTERNS['relationship_gratitude_recovery']",
        introduced_for_phase19_case="D",
        current_decision=DECISION_DELETE,
        reason="Dの入力例に近い語をEvidence Builderのruntime cueにしている。",
        replacement_design="関係終了・支援・怒り・感謝・返礼意図を汎用relation featureへ再分類する。",
        requires_test_update=True,
        runtime_mainline=True,
        source_tokens=("\"relationship_gratitude_recovery\": (", "彼氏と別れ"),
    ),
    Phase20Phase19DiffReviewEntry(
        file_path="ai/services/ai_inference/emlis_ai_shared_reception_evidence.py",
        symbol_name="_derive_reception_candidate_mode_ids.relationship_gratitude_recovery_branch",
        introduced_for_phase19_case="D",
        current_decision=DECISION_DELETE,
        reason="relationship_gratitude_feature条件からD専用modeをappendする本線route。",
        replacement_design="汎用relationship materialを作るだけにし、mode appendは撤回する。",
        requires_test_update=True,
        runtime_mainline=True,
        source_tokens=("modes.append(\"relationship_gratitude_recovery\")", "relationship_support_features"),
    ),
    Phase20Phase19DiffReviewEntry(
        file_path="ai/services/ai_inference/emlis_ai_shared_reception_evidence.py",
        symbol_name="_derive_reception_candidate_mode_ids.self_understanding_learning_shift_branch",
        introduced_for_phase19_case="C",
        current_decision=DECISION_DELETE,
        reason="learning_shift_feature条件からC専用modeをappendする本線route。",
        replacement_design="自己理解・学習・行動変化を汎用materialへ移し、case mode appendを撤回する。",
        requires_test_update=True,
        runtime_mainline=True,
        source_tokens=("modes.append(\"self_understanding_learning_shift\")", "learning_shift_features"),
    ),
    Phase20Phase19DiffReviewEntry(
        file_path="ai/services/ai_inference/emlis_ai_shared_reception_evidence.py",
        symbol_name="_mode_reason Phase19-specific reasons",
        introduced_for_phase19_case="C",
        current_decision=DECISION_DELETE,
        reason="primary_reasonがC/D専用mode名へ寄るため、後続resolverとsurfaceを固定する。",
        replacement_design="material_quality / relation_presence / change_presence等の汎用reasonへ置き換える。",
        requires_test_update=True,
        runtime_mainline=True,
        source_tokens=("return \"relationship_end_gratitude_recovery\"", "return \"self_understanding_learning_shift_present\""),
    ),
    Phase20Phase19DiffReviewEntry(
        file_path="ai/services/ai_inference/emlis_ai_shared_reception_evidence.py",
        symbol_name="EmlisSharedReceptionEvidence.as_meta Phase19 feature-family keys",
        introduced_for_phase19_case="C",
        current_decision=DECISION_GENERALIZE,
        reason="publicではないが、C/D専用feature family名がdiagnostic materialとして残る。",
        replacement_design="Phase20-3でvisible_material_slots / unknown_slots / relation feature idsへ一般化する。",
        requires_test_update=True,
        runtime_mainline=True,
        source_tokens=("learning_shift_feature_family", "relationship_gratitude_feature_family"),
    ),
    Phase20Phase19DiffReviewEntry(
        file_path="ai/services/ai_inference/emlis_ai_reception_mode_resolver.py",
        symbol_name="MODE_SELF_UNDERSTANDING_LEARNING_SHIFT",
        introduced_for_phase19_case="C",
        current_decision=DECISION_DELETE,
        reason="C専用modeがresolverの内部mode定数として本線に入っている。",
        replacement_design="response_kindと汎用sentence plan materialへ吸収し、mode定数は撤回する。",
        requires_test_update=True,
        runtime_mainline=True,
        source_tokens=("MODE_SELF_UNDERSTANDING_LEARNING_SHIFT", "self_understanding_learning_shift"),
    ),
    Phase20Phase19DiffReviewEntry(
        file_path="ai/services/ai_inference/emlis_ai_reception_mode_resolver.py",
        symbol_name="MODE_RELATIONSHIP_GRATITUDE_RECOVERY",
        introduced_for_phase19_case="D",
        current_decision=DECISION_DELETE,
        reason="D専用modeがresolverの内部mode定数として本線に入っている。",
        replacement_design="relationship material + boundary policyへ分解し、mode定数は撤回する。",
        requires_test_update=True,
        runtime_mainline=True,
        source_tokens=("MODE_RELATIONSHIP_GRATITUDE_RECOVERY", "relationship_gratitude_recovery"),
    ),
    Phase20Phase19DiffReviewEntry(
        file_path="ai/services/ai_inference/emlis_ai_reception_mode_resolver.py",
        symbol_name="_MODE_PRIORITY Phase19 C/D entries",
        introduced_for_phase19_case="C",
        current_decision=DECISION_DELETE,
        reason="C/D専用modeがpriority tuple内で通常modeより前に選ばれる。",
        replacement_design="内部response_kindとmaterial_qualityで選ぶ。case mode priorityは置かない。",
        requires_test_update=True,
        runtime_mainline=True,
        source_tokens=("_MODE_PRIORITY", "MODE_RELATIONSHIP_GRATITUDE_RECOVERY", "MODE_SELF_UNDERSTANDING_LEARNING_SHIFT"),
    ),
    Phase20Phase19DiffReviewEntry(
        file_path="ai/services/ai_inference/emlis_ai_reception_mode_resolver.py",
        symbol_name="_RATIO_PRESET_BY_INTERNAL_MODE Phase19 C/D presets",
        introduced_for_phase19_case="C",
        current_decision=DECISION_DELETE,
        reason="C/D専用modeからratio presetを固定し、surface planの専用経路へ送る。",
        replacement_design="response kind / sentence plan の汎用比率に戻す。",
        requires_test_update=True,
        runtime_mainline=True,
        source_tokens=("_RATIO_PRESET_BY_INTERNAL_MODE", "relationship_end_gratitude_recovery"),
    ),
    Phase20Phase19DiffReviewEntry(
        file_path="ai/services/ai_inference/emlis_ai_reception_mode_resolver.py",
        symbol_name="_choose_reception_mode Phase19 early returns and loop entries",
        introduced_for_phase19_case="D",
        current_decision=DECISION_DELETE,
        reason="eligible modeにC/D専用modeが含まれると優先採用される本線route。",
        replacement_design="関係・変化・支援材料の有無を汎用routeへ渡し、case-specific mode returnを撤回する。",
        requires_test_update=True,
        runtime_mainline=True,
        source_tokens=("return MODE_RELATIONSHIP_GRATITUDE_RECOVERY", "return MODE_SELF_UNDERSTANDING_LEARNING_SHIFT"),
    ),
    Phase20Phase19DiffReviewEntry(
        file_path="ai/services/ai_inference/emlis_ai_reception_mode_resolver.py",
        symbol_name="EmlisReceptionModeResolution.as_meta.relationship_gratitude_feature_ids",
        introduced_for_phase19_case="D",
        current_decision=DECISION_GENERALIZE,
        reason="D専用feature idをdiagnosticに残している。public leakではないが次Phaseで汎用relation idsへ変える。",
        replacement_design="relationship_relation_feature_ids / support_feature_ids等へ一般化する。",
        requires_test_update=True,
        runtime_mainline=True,
        source_tokens=("relationship_gratitude_feature_ids", "relationship_gratitude_recovery_detected"),
    ),
    Phase20Phase19DiffReviewEntry(
        file_path="ai/services/ai_inference/emlis_ai_two_stage_section_surface_plan.py",
        symbol_name="_SECTION_BUDGET_BY_MODE Phase19 C/D entries",
        introduced_for_phase19_case="C",
        current_decision=DECISION_DELETE,
        reason="C/D専用modeに文数budgetを持たせており、mode別surfaceを支える。",
        replacement_design="response_kind / material quality / relation depthからbudgetを決める。",
        requires_test_update=True,
        runtime_mainline=True,
        source_tokens=("\"self_understanding_learning_shift\": {", "\"relationship_gratitude_recovery\": {"),
    ),
    Phase20Phase19DiffReviewEntry(
        file_path="ai/services/ai_inference/emlis_ai_two_stage_section_surface_plan.py",
        symbol_name="_RECEPTION_MODE_BY_RATIO_REASON Phase19 C/D aliases",
        introduced_for_phase19_case="D",
        current_decision=DECISION_DELETE,
        reason="ratio reasonからC/D専用reception modeへ戻すaliasがある。",
        replacement_design="ratio reasonをcase modeへ戻さず、汎用sentence-plan reasonへする。",
        requires_test_update=True,
        runtime_mainline=True,
        source_tokens=("_RECEPTION_MODE_BY_RATIO_REASON", "relationship_end_gratitude_recovery"),
    ),
    Phase20Phase19DiffReviewEntry(
        file_path="ai/services/ai_inference/emlis_ai_complete_surface_realizer.py",
        symbol_name="EMLIS_TWO_STAGE_MODE_ID_BY_RATIO_REASON Phase19 C/D aliases",
        introduced_for_phase19_case="C",
        current_decision=DECISION_DELETE,
        reason="ratio reasonをC/D専用modeへ戻してSurface Realizer dispatchへ接続している。",
        replacement_design="汎用surface dispatcherへ移し、ratioからcase modeを復元しない。",
        requires_test_update=True,
        runtime_mainline=True,
        source_tokens=("EMLIS_TWO_STAGE_MODE_ID_BY_RATIO_REASON", "\"self_understanding_learning_shift\": \"self_understanding_learning_shift\""),
    ),
    Phase20Phase19DiffReviewEntry(
        file_path="ai/services/ai_inference/emlis_ai_complete_surface_realizer.py",
        symbol_name="EMLIS_TWO_STAGE_SELF_UNDERSTANDING_LEARNING_SHIFT_MODE_IDS",
        introduced_for_phase19_case="C",
        current_decision=DECISION_DELETE,
        reason="C専用surface dispatch set。",
        replacement_design="汎用self-understanding/change/action sentence planへ統合する。",
        requires_test_update=True,
        runtime_mainline=True,
        source_tokens=("EMLIS_TWO_STAGE_SELF_UNDERSTANDING_LEARNING_SHIFT_MODE_IDS",),
    ),
    Phase20Phase19DiffReviewEntry(
        file_path="ai/services/ai_inference/emlis_ai_complete_surface_realizer.py",
        symbol_name="EMLIS_TWO_STAGE_RELATIONSHIP_GRATITUDE_RECOVERY_MODE_IDS",
        introduced_for_phase19_case="D",
        current_decision=DECISION_DELETE,
        reason="D専用surface dispatch set。",
        replacement_design="汎用relationship support / boundary / gratitude sentence planへ統合する。",
        requires_test_update=True,
        runtime_mainline=True,
        source_tokens=("EMLIS_TWO_STAGE_RELATIONSHIP_GRATITUDE_RECOVERY_MODE_IDS",),
    ),
    Phase20Phase19DiffReviewEntry(
        file_path="ai/services/ai_inference/emlis_ai_complete_surface_realizer.py",
        symbol_name="EMLIS_TWO_STAGE_MODE_SPECIFIC_SURFACE_POLICY_MODE_IDS Phase19 inclusions",
        introduced_for_phase19_case="D",
        current_decision=DECISION_DELETE,
        reason="C/D専用modeをmode-specific surface policyに登録している。",
        replacement_design="mode-specific surface bankではなく、material slot + boundary policyから組み立てる。",
        requires_test_update=True,
        runtime_mainline=True,
        source_tokens=("EMLIS_TWO_STAGE_MODE_SPECIFIC_SURFACE_POLICY_MODE_IDS", "*EMLIS_TWO_STAGE_RELATIONSHIP_GRATITUDE_RECOVERY_MODE_IDS"),
    ),
    Phase20Phase19DiffReviewEntry(
        file_path="ai/services/ai_inference/emlis_ai_complete_surface_realizer.py",
        symbol_name="_learning_shift_surface_text_for_line",
        introduced_for_phase19_case="C",
        current_decision=DECISION_DELETE,
        reason="C mode別完成surface文bankであり、入力根拠から組み立てる構造ではない。",
        replacement_design="Generic SentencePlan / Surface RealizerでSourceAnchor・RelationUnit・TonePolicyから生成する。",
        requires_test_update=True,
        runtime_mainline=True,
        source_tokens=("def _learning_shift_surface_text_for_line", "learning_shift_observation_object_focus_load_margin"),
    ),
    Phase20Phase19DiffReviewEntry(
        file_path="ai/services/ai_inference/emlis_ai_complete_surface_realizer.py",
        symbol_name="_relationship_gratitude_surface_text_for_line",
        introduced_for_phase19_case="D",
        current_decision=DECISION_DELETE,
        reason="D mode別完成surface文bankであり、D fixture通過用のsurfaceに近い。",
        replacement_design="Generic SentencePlan / Surface Realizerで関係・悲しさ・支援・返礼意図を根拠内で構成する。",
        requires_test_update=True,
        runtime_mainline=True,
        source_tokens=("def _relationship_gratitude_surface_text_for_line", "relationship_gratitude_observation_recovery_load_support"),
    ),
    Phase20Phase19DiffReviewEntry(
        file_path="ai/services/ai_inference/emotion_submit_service.py",
        symbol_name="_PUBLIC_SAFE_MODE_ID_ALIASES",
        introduced_for_phase19_case="boundary",
        current_decision=DECISION_RETAIN,
        reason="publicへ内部mode名を漏らさないための汎用安全alias枠で、route追加ではない。",
        replacement_design="Phase20-9でC/D専用aliasは撤回し、空の汎用public-safe alias枠だけを保持する。",
        requires_test_update=True,
        runtime_mainline=True,
        source_tokens=("_PUBLIC_SAFE_MODE_ID_ALIASES", "_phase14_public_safe_reception_mode_id"),
    ),
    Phase20Phase19DiffReviewEntry(
        file_path="ai/services/ai_inference/emlis_ai_reply_service.py",
        symbol_name="_PHASE19_LOW_INFORMATION_STATE_SIGNAL_RE",
        introduced_for_phase19_case="A",
        current_decision=DECISION_GENERALIZE,
        reason="低情報応答は必要だが、短文疲労compact signalに寄っている。",
        replacement_design="Phase20-3で入力束のmaterial_quality / visible_slots / unknown_slotsによる汎用low-information routerへ移す。",
        requires_test_update=True,
        runtime_mainline=True,
        source_tokens=("_PHASE19_LOW_INFORMATION_STATE_SIGNAL_RE",),
    ),
    Phase20Phase19DiffReviewEntry(
        file_path="ai/services/ai_inference/emlis_ai_reply_service.py",
        symbol_name="_phase19_complete_initial_low_information_repair_ownership_meta",
        introduced_for_phase19_case="A",
        current_decision=DECISION_GENERALIZE,
        reason="Aを通すためのComplete Initial低情報repair ownershipだが、低情報応答自体は本線に必要。",
        replacement_design="Phase20-1/3/4でinternal response_kindと汎用low_information_observationへ再設計する。",
        requires_test_update=True,
        runtime_mainline=True,
        source_tokens=("def _phase19_complete_initial_low_information_repair_ownership_meta", "Phase19-2_A_low_information_repair_ownership"),
    ),
    Phase20Phase19DiffReviewEntry(
        file_path="ai/services/ai_inference/emlis_ai_reply_service.py",
        symbol_name="render_emlis_ai_reply.complete_initial_low_information_repair_ownership usage",
        introduced_for_phase19_case="A",
        current_decision=DECISION_GENERALIZE,
        reason="Step10 repairへPhase19 ownership metaを渡しており、A型compact signalに依存する。",
        replacement_design="汎用Input Material Bundleからrepair_contextを作る。",
        requires_test_update=True,
        runtime_mainline=True,
        source_tokens=("complete_initial_low_information_repair_ownership = _phase19_complete_initial_low_information_repair_ownership_meta", "repair_context=complete_initial_low_information_repair_ownership"),
    ),
    Phase20Phase19DiffReviewEntry(
        file_path="ai/services/ai_inference/emlis_ai_observation_display_repair_integration.py",
        symbol_name="COMPLETE_INITIAL_LOW_INFORMATION_REPAIR_OWNERSHIP_SCHEMA_VERSION",
        introduced_for_phase19_case="A",
        current_decision=DECISION_GENERALIZE,
        reason="低情報repair context schemaがPhase19/A ownership名のまま残っている。",
        replacement_design="Phase20-1/3でresponse contract / material bundle由来のrepair contextへ置き換える。",
        requires_test_update=True,
        runtime_mainline=True,
        source_tokens=("COMPLETE_INITIAL_LOW_INFORMATION_REPAIR_OWNERSHIP_SCHEMA_VERSION", "cocolon.emlis.phase19.complete_initial_low_information_repair_ownership.v1"),
    ),
    Phase20Phase19DiffReviewEntry(
        file_path="ai/services/ai_inference/emlis_ai_observation_display_repair_integration.py",
        symbol_name="_complete_initial_low_information_repair_context_allowed",
        introduced_for_phase19_case="A",
        current_decision=DECISION_GENERALIZE,
        reason="低情報repair適用条件がPhase19 ownership schemaに依存している。",
        replacement_design="material_quality=low_information と safety_triage_kind を使う汎用条件へ移す。",
        requires_test_update=True,
        runtime_mainline=True,
        source_tokens=("def _complete_initial_low_information_repair_context_allowed", "repair_allowed_under_complete_initial"),
    ),
    Phase20Phase19DiffReviewEntry(
        file_path="ai/services/ai_inference/emlis_ai_observation_display_repair_integration.py",
        symbol_name="ObservationDisplayRepairIntegrationResult.as_meta.phase19_complete_initial_low_information_repair_ownership",
        introduced_for_phase19_case="A",
        current_decision=DECISION_GENERALIZE,
        reason="diagnostic metaにPhase19名のaliasを残している。publicではないが次Phaseで一般化対象。",
        replacement_design="gate_recovery_event / repair_attempts metaへ吸収する。",
        requires_test_update=True,
        runtime_mainline=True,
        source_tokens=("phase19_complete_initial_low_information_repair_ownership", "complete_initial_low_information_repair_allowed"),
    ),
    Phase20Phase19DiffReviewEntry(
        file_path="ai/tests/test_emotion_submit_phase19_real_device_abcd_public_feedback_e2e.py",
        symbol_name="PHASE19_REAL_DEVICE_ABCD_CASES.B_safety_boundary_self_harm_adjacent",
        introduced_for_phase19_case="B",
        current_decision=DECISION_RETAIN,
        reason="B exact入力は自己否定・安全境界の回帰fixtureとして保持する。ただし一律非表示固定を成功目標にしない。",
        replacement_design="Phase20-2でself_denial_safe_state_answerとsafety_blocked_emergencyへ分ける。expected exact comment_textは置かない。",
        requires_test_update=True,
        runtime_mainline=False,
        exact_fixture=True,
        source_tokens=("phase19_real_device_B_safety_boundary_self_harm_adjacent", "expected_observation_status"),
    ),
    Phase20Phase19DiffReviewEntry(
        file_path="ai/tests/test_emotion_submit_phase19_real_device_abcd_public_feedback_e2e.py",
        symbol_name="PHASE19_REAL_DEVICE_ABCD_CASES",
        introduced_for_phase19_case="boundary",
        current_decision=DECISION_RETAIN,
        reason="A/B/C/D exact inputは成功目標ではなく、無応答・case専用route・safety境界破壊の回帰fixtureとして必要。",
        replacement_design="expected exact comment_textを置かず、public shape / response_kind / safety boundaryで評価する。",
        requires_test_update=True,
        runtime_mainline=False,
        exact_fixture=True,
        source_tokens=("PHASE19_REAL_DEVICE_ABCD_CASES", "expected_comment_text_non_empty"),
    ),
    Phase20Phase19DiffReviewEntry(
        file_path="ai/tests/helpers/emlis_ai_phase19_public_feedback_matrix.py",
        symbol_name="build_phase19_public_feedback_recovery_matrix",
        introduced_for_phase19_case="boundary",
        current_decision=DECISION_QUARANTINE,
        reason="Phase19診断matrixはtest-onlyで保持し、runtimeやpublic responseへ持ち込まない。",
        replacement_design="Phase20-8でQA Matrixへ再構築するまで、失敗再現・境界確認として隔離保持する。",
        requires_test_update=True,
        runtime_mainline=False,
        source_tokens=("def build_phase19_public_feedback_recovery_matrix", "test diagnostic object only"),
    ),
    Phase20Phase19DiffReviewEntry(
        file_path="ai/tests/test_emlis_ai_phase19_public_feedback_matrix.py",
        symbol_name="test_phase19_1_public_feedback_recovery_matrix_*",
        introduced_for_phase19_case="boundary",
        current_decision=DECISION_QUARANTINE,
        reason="Phase19 matrixのshape guardはtest-onlyで、production success指標ではない。",
        replacement_design="Phase20-8でQA matrix familyへ移行する。",
        requires_test_update=True,
        runtime_mainline=False,
        source_tokens=("test_phase19_1_public_feedback_recovery_matrix",),
    ),
    Phase20Phase19DiffReviewEntry(
        file_path="ai/tests/test_emotion_submit_phase19_public_feedback_boundary_e2e.py",
        symbol_name="Phase19 public feedback boundary tests",
        introduced_for_phase19_case="boundary",
        current_decision=DECISION_RETAIN,
        reason="public input_feedback境界、raw/internal leak防止、non-passed非表示は保持対象。",
        replacement_design="exact generated textではなくpublic shape / safety / meta sanitizer境界として継続する。",
        requires_test_update=True,
        runtime_mainline=False,
        source_tokens=("test_phase19_5_real_device_abcd_reaches_final_public_feedback_boundary", "_assert_no_internal_payload_leak"),
    ),
    Phase20Phase19DiffReviewEntry(
        file_path="Cocolon/tests/rn-screen-contracts.test.js",
        symbol_name="Phase19-6 RN ABCD public feedback fixtures",
        introduced_for_phase19_case="boundary",
        current_decision=DECISION_RETAIN,
        reason="RN productionは保持し、passed + comment_text表示境界と内部meta非表示を守る。",
        replacement_design="Phase20-0でfixture本文をbackend exact期待ではなくsample payloadとして扱う。Phase20-7でshape/behavior contractへ完全移行する。",
        requires_test_update=True,
        runtime_mainline=False,
        exact_fixture=True,
        source_tokens=("Phase19-6 RN contract keeps ABCD public feedback display behind passed plus comment_text only",),
    ),
)


def phase20_phase19_diff_review_schema_payloads() -> tuple[dict[str, Any], ...]:
    return tuple(entry.schema_payload() for entry in PHASE20_PHASE19_DIFF_REVIEW_ENTRIES)


def phase20_phase19_runtime_mainline_entries() -> tuple[Phase20Phase19DiffReviewEntry, ...]:
    return tuple(entry for entry in PHASE20_PHASE19_DIFF_REVIEW_ENTRIES if entry.runtime_mainline)


def phase20_phase19_exact_fixture_entries() -> tuple[Phase20Phase19DiffReviewEntry, ...]:
    return tuple(entry for entry in PHASE20_PHASE19_DIFF_REVIEW_ENTRIES if entry.exact_fixture)


def validate_phase20_phase19_diff_review_entry(entry: Phase20Phase19DiffReviewEntry) -> None:
    payload = entry.schema_payload()
    assert set(payload.keys()) == {
        "file_path",
        "symbol_name",
        "introduced_for_phase19_case",
        "current_decision",
        "reason",
        "replacement_design",
        "requires_test_update",
    }
    assert isinstance(entry.file_path, str) and entry.file_path.strip()
    assert isinstance(entry.symbol_name, str) and entry.symbol_name.strip()
    assert entry.introduced_for_phase19_case in PHASE20_ALLOWED_PHASE19_CASES
    assert entry.current_decision in PHASE20_ALLOWED_DECISIONS
    assert isinstance(entry.reason, str) and entry.reason.strip()
    assert entry.replacement_design is None or isinstance(entry.replacement_design, str)
    assert isinstance(entry.requires_test_update, bool)
    assert isinstance(entry.runtime_mainline, bool)
    assert isinstance(entry.exact_fixture, bool)
    assert isinstance(entry.source_tokens, tuple)
    assert all(isinstance(token, str) and token for token in entry.source_tokens)


def validate_phase20_phase19_diff_review_inventory(
    entries: Iterable[Phase20Phase19DiffReviewEntry] = PHASE20_PHASE19_DIFF_REVIEW_ENTRIES,
) -> None:
    seen: set[tuple[str, str]] = set()
    entries_tuple = tuple(entries)
    assert entries_tuple
    for entry in entries_tuple:
        validate_phase20_phase19_diff_review_entry(entry)
        key = (entry.file_path, entry.symbol_name)
        assert key not in seen, key
        seen.add(key)

    decisions = {entry.current_decision for entry in entries_tuple}
    assert decisions == PHASE20_ALLOWED_DECISIONS
    cases = {entry.introduced_for_phase19_case for entry in entries_tuple}
    assert {"A", "B", "C", "D", "boundary"}.issubset(cases)

    runtime_files = {entry.file_path for entry in entries_tuple if entry.runtime_mainline}
    assert PHASE20_RUNTIME_TARGET_FILES.issubset(runtime_files)

    test_files = {entry.file_path for entry in entries_tuple if not entry.runtime_mainline}
    assert PHASE20_TEST_TARGET_FILES.issubset(test_files)


def entries_by_file_path(file_path: str) -> tuple[Phase20Phase19DiffReviewEntry, ...]:
    return tuple(entry for entry in PHASE20_PHASE19_DIFF_REVIEW_ENTRIES if entry.file_path == file_path)


__all__ = [
    "DECISION_DELETE",
    "DECISION_GENERALIZE",
    "DECISION_QUARANTINE",
    "DECISION_RETAIN",
    "PHASE20_ALLOWED_DECISIONS",
    "PHASE20_PHASE19_DIFF_REVIEW_ENTRIES",
    "PHASE20_PHASE19_DIFF_REVIEW_SCHEMA_VERSION",
    "PHASE20_PHASE19_DIFF_REVIEW_SOURCE_PHASE",
    "PHASE20_RUNTIME_TARGET_FILES",
    "PHASE20_TEST_TARGET_FILES",
    "Phase20Phase19DiffReviewEntry",
    "entries_by_file_path",
    "phase20_phase19_diff_review_schema_payloads",
    "phase20_phase19_exact_fixture_entries",
    "phase20_phase19_runtime_mainline_entries",
    "validate_phase20_phase19_diff_review_entry",
    "validate_phase20_phase19_diff_review_inventory",
]
