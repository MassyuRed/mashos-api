# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path


def _repo_ai_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (_repo_ai_root() / relative_path).read_text(encoding="utf-8")


def test_phase14_final_verification_memo_exists_and_keeps_no_destructive_boundary() -> None:
    memo_path = _repo_ai_root() / "docs" / "Cocolon_TextGenerationCore_Phase14_FinalVerification_2026_05_11.md"
    assert memo_path.exists()

    text = memo_path.read_text(encoding="utf-8")
    required_boundary_tokens = (
        "DB physical name",
        "DB write path",
        "DB rename / drop",
        "既存 public API route",
        "既存 request / response key",
        "input_feedback.comment_text",
        "observation_status",
        "piece_text",
        "content_json",
        "Emlisの観測",
        "外部 AI 導入",
        "固定観測文 fallback",
    )
    for token in required_boundary_tokens:
        assert token in text


def test_phase14_three_core_contracts_still_use_existing_public_shapes() -> None:
    import core_contract_registry as registry

    contracts = {entry.core_id: entry for entry in registry.iter_core_contracts()}

    emlis = contracts["emlis_ai"]
    assert emlis.primary_route == "POST /emotion/submit"
    assert "input_feedback.comment_text" in (emlis.notes or "")
    assert "input_feedback" in emlis.storage_owner

    piece = contracts["piece"]
    assert piece.primary_route == "POST /emotion/piece/preview + POST /emotion/piece/publish"
    assert piece.publish_policy == "preview_ready_to_published_status_only"
    assert "mymodel_reflections" in piece.storage_owner

    analysis = contracts["analysis"]
    assert analysis.primary_route == "/analysis/* + /self-structure/*"
    assert "content_json" in analysis.storage_owner
    assert analysis.quality_gate == "analysis_report_validity_gate"


def test_phase14_public_payload_keys_and_visible_names_remain_in_source() -> None:
    emlis_reply = _read("services/ai_inference/emlis_ai_reply_service.py")
    piece_api = _read("services/ai_inference/api_emotion_piece.py")
    analysis_api = _read("services/ai_inference/api_analysis_reports.py")
    analysis_gate = _read("services/ai_inference/analysis_report_validity_gate.py")

    assert '"visible_name": "Emlisの観測"' in emlis_reply
    assert "comment_text" in emlis_reply
    assert "observation_status" in emlis_reply

    assert '@app.post("/emotion/piece/preview"' in piece_api
    assert '@app.post("/emotion/piece/publish"' in piece_api
    assert "piece_text" in piece_api

    assert "content_json" in analysis_api
    assert "standardReport" in analysis_api
    assert "contentText" in analysis_api
    assert 'TEXT_GENERATION_META_KEY = "textGenerationCore"' in analysis_gate
    assert '"standardReport_contract_untouched": True' in analysis_gate
    assert '"contentText_contract_untouched": True' in analysis_gate


def test_phase14_common_core_exports_all_three_connected_composers_without_runtime_rename() -> None:
    import cocolon_text_generation_core as core

    assert core.EMLIS_OBSERVATION_COMPOSER_ADAPTER_NAME == "emlis_observation_composer_adapter.v1"
    assert core.PIECE_COMPOSER_ADAPTER_NAME == "piece_composer.v1"
    assert core.ANALYSIS_COMPOSER_ADAPTER_NAME == "analysis_composer.v1"

    assert core.CORE_ID_EMLIS == "emlis"
    assert core.CORE_ID_PIECE == "piece"
    assert core.CORE_ID_ANALYSIS == "analysis"
    assert set(core.KNOWN_CORE_IDS) == {"emlis", "piece", "analysis"}
    assert core.PIECE_LEGACY_BOUNDARY_NAMES == ("reflection", "mymodel_qna")


def test_phase14_does_not_add_text_generation_core_db_migration_files() -> None:
    root = _repo_ai_root()
    candidate_paths = list(root.rglob("*text_generation_core*.sql")) + list(root.rglob("*cocolon_text_generation_core*.sql"))
    assert candidate_paths == []
