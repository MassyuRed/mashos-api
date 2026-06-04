from __future__ import annotations

from pathlib import Path

DOC_PATH = (
    Path(__file__).resolve().parents[1]
    / "docs"
    / "Cocolon_EmlisAI_構造辞書更新運用_華恋用_2026-06-02.md"
)


def _doc_text() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def test_phase8_design_doc_exists_and_is_process_design_only() -> None:
    text = _doc_text()

    assert "Phase8" in text
    assert "Mash構造知識" in text
    assert "process_design_only: true" in text
    assert "runtime_dictionary_file_created: false" in text
    assert "runtime_config_written: false" in text
    assert "runtime_surface_added: false" in text
    assert "comment_text_written: false" in text
    assert "public_response_key_added: false" in text
    assert "api_route_changed: false" in text
    assert "db_physical_name_changed: false" in text
    assert "rn_visible_contract_changed: false" in text
    assert "product_gate_ready: false" in text
    assert "public_release_applied: false" in text


def test_phase8_keeps_mash_source_ledger_before_karen_normalization() -> None:
    text = _doc_text()

    required_terms = [
        "source_ledger",
        "source_owner: Mash",
        "original_wording_retained: true",
        "karen_paraphrase_is_canonical: false",
        "mash_original_meaning",
        "karen_structuring_note",
        "not_equivalent_to",
        "open_boundary",
        "Mash知識が華恋の言い換えで歪まない",
    ]
    for term in required_terms:
        assert term in text


def test_phase8_dictionary_candidate_requires_relation_questions_forbidden_soft_policy_and_qa() -> None:
    text = _doc_text()

    required_terms = [
        "relation_pattern",
        "internal_question",
        "trigger_requirements",
        "allowed_observation_claim",
        "forbidden_claim",
        "soft_surface_policy",
        "qa_requirements",
        "fixture_family_required: true",
        "blind_qa_required: true",
        "implementation_candidate_requires_evidence_forbidden_and_qa: true",
        "evidence_boundary",
        "fixture_family",
        "blind_qa_questions",
    ]
    for term in required_terms:
        assert term in text


def test_phase8_keeps_dictionary_boundaries_out_of_general_diagnosis_and_personality_claims() -> None:
    text = _doc_text()

    forbidden_boundary_terms = [
        "一般論辞書にならない",
        "診断辞書にならない",
        "性格辞書にならない",
        "personality_claim",
        "diagnosis",
        "cause_claim_without_evidence",
        "period_tendency_from_single_record",
        "target_judgement_agreement",
        "category_as_cause",
        "emotion_as_cause",
        "completed_runtime_sentence_forbidden: true",
    ]
    for term in forbidden_boundary_terms:
        assert term in text


def test_phase8_documents_boundaries_with_cocolon_philosophy_observation_and_reception_dictionaries() -> None:
    text = _doc_text()

    required_sections = [
        "### 2.1 Cocolon思想資料との境界",
        "### 2.2 Emlis観測専用辞書との境界",
        "### 2.3 受け取り補助辞書との境界",
        "### 2.4 Phase7 Structure Insight候補との境界",
        "入力語・入力束・関係・内部問い・推論鎖・表面化方針",
        "follow shape",
        "tone family",
        "Phase7 moduleへ直接relationを追加しない",
    ]
    for term in required_sections:
        assert term in text


def test_phase8_requires_fixture_and_blind_qa_before_dictionary_candidate() -> None:
    text = _doc_text()

    required = [
        "expected_v1_effect",
        "expected_v2_effect",
        "red_or_repair_risk",
        "machine metricsでread_feelingやinsight_deltaを自動補完しない",
        "QA_FIXTURE_REQUIRED",
        "BLIND_QA_PENDING",
        "DICTIONARY_CANDIDATE",
        "IMPLEMENTATION_APPROVED_LATER_PHASE",
    ]
    for term in required:
        assert term in text
