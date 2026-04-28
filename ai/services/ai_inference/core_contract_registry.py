# -*- coding: utf-8 -*-
"""Internal national-core contract registry.

The public API registry lists external routes.  This registry fixes the three
Cocolon national cores as internal responsibilities so future changes can be
checked against input/output/storage/gate boundaries without renaming DB tables
or retiring legacy compatibility routes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

CORE_CONTRACT_POLICY_VERSION = "2026-04-27.new-national-system.v1"

CORE_EMLIS_AI = "emlis_ai"
CORE_ANALYSIS = "analysis"
CORE_PIECE = "piece"


@dataclass(frozen=True)
class CoreContractEntry:
    core_id: str
    core_name: str
    input_owner: str
    output_owner: str
    primary_route: str
    storage_owner: str
    read_surface: str
    quality_gate: str
    safety_gate: str
    publish_policy: str
    access_policy: str
    contract_id: str
    metrics_key: str
    notes: Optional[str] = None


CORE_CONTRACTS: Tuple[CoreContractEntry, ...] = (
    CoreContractEntry(
        core_id=CORE_EMLIS_AI,
        core_name="EmlisAI",
        input_owner="emotion_submit_service.persist_emotion_submission",
        output_owner="emlis_ai_reply_service.render_emlis_ai_reply",
        primary_route="POST /emotion/submit",
        storage_owner="emotion_entries + input_feedback additive meta",
        read_surface="InputScreen feedback modal",
        quality_gate="emlis_ai_observation_kernel + emlis_ai_quality_gate",
        safety_gate="observation overclaim / diagnosis prevention",
        publish_policy="not_public",
        access_policy="owner_only_immediate_feedback",
        contract_id="core.emlis_ai.v1",
        metrics_key="core.emlis_ai",
        notes="input_feedback.comment_text is stable; input_feedback.emlis_ai is additive-only.",
    ),
    CoreContractEntry(
        core_id=CORE_ANALYSIS,
        core_name="分析構造",
        input_owner="analysis_engine_adapter + astor_self_structure_report",
        output_owner="api_analysis_reports + api_self_structure_reports",
        primary_route="/analysis/* + /self-structure/*",
        storage_owner="analysis_results / analysis_reports / self_structure_reports content_json",
        read_surface="Analysis and SelfStructure RN screens via API boundary",
        quality_gate="analysis_report_validity_gate",
        safety_gate="diagnosis / overclaim / material sufficiency prevention",
        publish_policy="owner_facing_report_artifact",
        access_policy="report_access_policy",
        contract_id="core.analysis.v1",
        metrics_key="core.analysis",
        notes="Emotion analysis and self-structure analysis must not mix material domains.",
    ),
    CoreContractEntry(
        core_id=CORE_PIECE,
        core_name="Piece生成機構",
        input_owner="api_emotion_piece.EmotionPiecePreviewRequest",
        output_owner="emotion_piece_generation_service.generate_emotion_reflection_preview",
        primary_route="POST /emotion/piece/preview + POST /emotion/piece/publish",
        storage_owner="mymodel_reflections content_json.national_core",
        read_surface="EmotionPiecePreviewModal + Piece/Nexus read APIs",
        quality_gate="piece_generation_policy",
        safety_gate="piece_text_formatter + piece_generation_policy",
        publish_policy="preview_ready_to_published_status_only",
        access_policy="piece_access_policy / viewer_access_policy",
        contract_id="core.piece.v1",
        metrics_key="core.piece",
        notes="Preview text and published text must stay identical; publish must not regenerate text.",
    ),
)

_CONTRACTS_BY_CORE_ID: Dict[str, CoreContractEntry] = {entry.core_id: entry for entry in CORE_CONTRACTS}


def iter_core_contracts() -> Tuple[CoreContractEntry, ...]:
    return CORE_CONTRACTS


def get_core_contract(core_id: str) -> Optional[CoreContractEntry]:
    return _CONTRACTS_BY_CORE_ID.get(str(core_id or "").strip())


def core_contract_ids() -> Tuple[str, ...]:
    return tuple(entry.contract_id for entry in CORE_CONTRACTS)


def core_ids() -> Tuple[str, ...]:
    return tuple(entry.core_id for entry in CORE_CONTRACTS)


__all__ = [
    "CORE_ANALYSIS",
    "CORE_CONTRACT_POLICY_VERSION",
    "CORE_EMLIS_AI",
    "CORE_PIECE",
    "CORE_CONTRACTS",
    "CoreContractEntry",
    "core_contract_ids",
    "core_ids",
    "get_core_contract",
    "iter_core_contracts",
]
