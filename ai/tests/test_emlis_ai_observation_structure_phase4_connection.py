from __future__ import annotations

import json
from typing import Any, Mapping

import pytest

from emlis_ai_conversation_composer_service import (
    build_conversation_composer_payload,
    compose_emlis_conversation_candidate,
)
from emlis_ai_display_gate import decide_emlis_observation_display
from emlis_ai_observation_structure_material_service import (
    OBSERVATION_STRUCTURE_MATERIAL_PHASE,
    assert_observation_structure_material_contract,
    build_observation_structure_material,
    observation_structure_material_composer_payload,
    observation_structure_material_forward_meta,
    observation_structure_material_gate_report,
)
from emlis_ai_observation_structure_connection_service import (
    build_observation_structure_connection,
    observation_structure_connection_forward_composer_meta,
)
from cocolon_environment_state_output_frame import (
    ENVIRONMENT_STATE_OUTPUT_FRAME_MATERIAL_ID,
    ENVIRONMENT_STATE_OUTPUT_FRAME_SCHEMA_VERSION,
)
from emlis_ai_types import (
    AddresseeNotes,
    EvidenceSpan,
    GraphClaim,
    GroundingReport,
    ListenerReaderReport,
    ObservationGraph,
    TemplateEchoReport,
)


def _graph() -> ObservationGraph:
    return ObservationGraph(
        primary_state=GraphClaim(
            claim_id="c1",
            claim_type="state",
            text="current input state",
            evidence_span_ids=["s1"],
            confidence=0.8,
        ),
        addressee_notes=AddresseeNotes(display_name_call="Mash様"),
    )


def _evidence() -> list[EvidenceSpan]:
    return [
        EvidenceSpan(span_id="s1", raw_text="大丈夫", source_field="memo", detected_type="thought", confidence=1.0),
        EvidenceSpan(span_id="s2", raw_text="悲しみ", source_field="emotion_details", detected_type="emotion", confidence=1.0),
        EvidenceSpan(span_id="s3", raw_text="仕事", source_field="category", detected_type="category", confidence=1.0),
    ]


def _contains_exact_key(value: Any, key_name: str) -> bool:
    if isinstance(value, Mapping):
        return any(str(key) == key_name or _contains_exact_key(child, key_name) for key, child in value.items())
    if isinstance(value, list):
        return any(_contains_exact_key(child, key_name) for child in value)
    return False


def test_phase4_material_selects_state_text_gap_without_raw_text_or_completed_reply() -> None:
    material = build_observation_structure_material(
        current_input={
            "id": "emo-1",
            "created_at": "2026-05-21T00:00:00Z",
            "memo": "大丈夫",
            "memo_action": "",
            "emotion_details": [{"type": "悲しみ", "strength": "strong"}],
            "category": ["仕事"],
        },
        evidence_ledger=_evidence(),
    )

    meta = material.as_meta()
    assert meta["source_phase"] == OBSERVATION_STRUCTURE_MATERIAL_PHASE
    assert meta["observation_structure_dictionary_connected"] is True
    assert meta["gate_connected"] is True
    assert meta["composer_connected"] is True
    assert "gap_word_daijoubu" in meta["selected_entry_ids"]
    assert "state_text_gap" in meta["selected_relation_ids"]
    assert "s1" in meta["evidence_span_ids"]
    assert meta["dictionary_is_observation_material_only"] is True
    assert meta["dictionary_returns_completed_reply"] is False
    assert meta["comment_text_generated"] is False
    assert meta["raw_input_included"] is False
    assert meta["raw_text_included"] is False
    assert_observation_structure_material_contract(meta)

    dumped = json.dumps(observation_structure_material_forward_meta(material), ensure_ascii=False)
    assert "大丈夫" not in dumped
    assert "rawText" not in dumped
    assert "commentText" not in dumped
    assert '"comment_text_generated": false' in dumped
    assert '"raw_text_included": false' in dumped


def test_phase4_material_carries_environment_state_output_frame_projection_only() -> None:
    current_input = {
        "id": "emo-eso-phase4-1",
        "created_at": "2026-05-25T04:00:00Z",
        "memo": "この職場でやっていけるか不安",
        "memo_action": "職場で新しい仕事を任された",
        "emotion_details": [{"type": "不安", "strength": "medium"}],
        "category": ["仕事"],
    }

    material = build_observation_structure_material(current_input=current_input)
    meta = material.as_meta()
    composer_payload = observation_structure_material_composer_payload(material)
    frame = meta["environment_state_output_frame"]
    encoded = json.dumps(composer_payload, ensure_ascii=False, sort_keys=True)

    assert meta["environment_state_output_frame_connected"] is True
    assert meta["environment_state_output_frame_material_id"] == ENVIRONMENT_STATE_OUTPUT_FRAME_MATERIAL_ID
    assert meta["environment_state_output_frame_schema_version"] == ENVIRONMENT_STATE_OUTPUT_FRAME_SCHEMA_VERSION
    assert meta["environment_state_output_frame_single_record_only"] is True
    assert frame["projection_kind"] == "phase4_gate_composer_safe_projection"
    assert frame["axis_presence"]["has_all_single_record_axes"] is True
    assert frame["environment_axis"]["category_labels"] == ["仕事"]
    assert frame["state_axis"]["emotion_types"] == ["不安"]
    assert "continuation_concern" in frame["output_axis"]["output_theme_ids"]
    assert frame["time_axis"]["period_scope"] == "single_record"
    assert frame["frame_policy"]["single_record_only"] is True
    assert frame["frame_policy"]["period_tendency_from_single_record"] is False
    assert frame["frame_policy"]["recovery_prescription_allowed"] is False
    assert composer_payload["environment_state_output_frame_connected"] is True
    assert composer_payload["period_tendency_from_single_record"] is False
    assert composer_payload["recovery_prescription_allowed"] is False
    assert _contains_exact_key(composer_payload, "surface_policy") is False
    assert "この職場でやっていけるか不安" not in encoded
    assert "職場で新しい仕事を任された" not in encoded
    assert '"comment_text_generated": false' in encoded
    assert_observation_structure_material_contract(meta)


def test_phase4_connection_exposes_environment_state_output_summary_without_public_surface() -> None:
    current_input = {
        "id": "emo-eso-phase4-2",
        "created_at": "2026-05-25T05:00:00Z",
        "memo": "この職場でやっていけるか不安",
        "memo_action": "職場で新しい仕事を任された",
        "emotion_details": [{"type": "不安", "strength": "medium"}],
        "category": ["仕事"],
    }

    connection = build_observation_structure_connection(current_input=current_input)
    meta = connection.as_meta()
    composer_meta = observation_structure_connection_forward_composer_meta(connection)
    encoded = json.dumps(composer_meta, ensure_ascii=False, sort_keys=True)

    assert meta["environment_state_output_frame_connected"] is True
    assert meta["environment_state_output_frame_material_id"] == ENVIRONMENT_STATE_OUTPUT_FRAME_MATERIAL_ID
    assert meta["environment_state_output_frame_single_record_only"] is True
    assert meta["period_tendency_from_single_record"] is False
    assert meta["recovery_prescription_allowed"] is False
    assert "continuation_concern" in meta["environment_state_output_frame_output_theme_ids"]
    assert composer_meta["environment_state_output_frame_connected"] is True
    assert composer_meta["environment_state_output_frame_single_record_only"] is True
    assert composer_meta["period_tendency_from_single_record"] is False
    assert composer_meta["recovery_prescription_allowed"] is False
    assert "この職場でやっていけるか不安" not in encoded
    assert "職場で新しい仕事を任された" not in encoded
    assert '"comment_text_generated": false' in encoded


def test_phase4_material_distinguishes_category_parallel_and_overlap() -> None:
    parallel = build_observation_structure_material(
        current_input={
            "memo": "無理",
            "memo_action": "",
            "emotion_details": [{"type": "不安", "strength": "strong"}],
            "category": ["仕事", "健康"],
        }
    ).as_meta()
    assert "category_parallel" in parallel["selected_relation_ids"]
    assert "category_overlap" not in parallel["selected_relation_ids"]

    overlap = build_observation_structure_material(
        current_input={
            "memo": "体が持たない気がする",
            "memo_action": "残業が続いて眠れていない",
            "emotion_details": [{"type": "不安", "strength": "strong"}],
            "category": ["仕事", "健康"],
        }
    ).as_meta()
    assert "category_parallel" in overlap["selected_relation_ids"]
    assert "category_overlap" in overlap["selected_relation_ids"]


def test_phase4_material_selects_thought_action_discrepancy_and_self_insight() -> None:
    discrepancy = build_observation_structure_material(
        current_input={
            "memo": "本当は嫌だった",
            "memo_action": "笑って対応した",
            "emotion_details": [{"type": "怒り", "strength": "strong"}],
            "category": ["人間関係"],
        }
    ).as_meta()
    assert "thought_action_discrepancy" in discrepancy["selected_relation_ids"]

    self_insight = build_observation_structure_material(
        current_input={
            "memo": "私は人に合わせすぎてたのかもしれない",
            "memo_action": "",
            "emotion_details": [{"type": "自己理解", "strength": "medium"}],
            "category": ["価値観"],
        }
    ).as_meta()
    assert "self_insight" in self_insight["selected_entry_ids"]
    assert "self_insight_discovery" in self_insight["selected_relation_ids"]


class _EchoComposerClient:
    def __init__(self) -> None:
        self.payload: Mapping[str, Any] | None = None

    def generate(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        self.payload = payload
        return {
            "response_schema_version": "emlis.composer.response.v1",
            "composer_source": "ai_generated",
            "comment_text": "Emlisは、今の入力を受け取っています。",
            "used_evidence_span_ids": ["s1"],
            "confidence": 0.8,
            "composer_meta": {},
        }


def test_phase4_composer_payload_receives_dictionary_material_only() -> None:
    material = build_observation_structure_material(
        current_input={
            "memo": "大丈夫",
            "memo_action": "",
            "emotion_details": [{"type": "悲しみ", "strength": "strong"}],
            "category": ["仕事"],
        },
        evidence_ledger=_evidence(),
    )
    payload = build_conversation_composer_payload(
        graph=_graph(),
        evidence_spans=_evidence(),
        observation_structure_material=material,
    )

    assert payload["composition_contract"]["use_observation_structure_dictionary_as_material_only"] is True
    assert payload["composition_contract"]["dictionary_must_not_generate_completed_sentence"] is True
    assert payload["observation_structure_material"]["dictionary_is_observation_material_only"] is True
    assert payload["observation_structure_material"]["dictionary_returns_completed_reply"] is False
    assert "state_text_gap" in payload["observation_structure_material"]["selected_relation_ids"]
    assert payload["observation_structure_material"]["environment_state_output_frame_connected"] is True
    assert payload["observation_structure_material"]["environment_state_output_frame"]["material_id"] == ENVIRONMENT_STATE_OUTPUT_FRAME_MATERIAL_ID

    client = _EchoComposerClient()
    candidate = compose_emlis_conversation_candidate(
        graph=_graph(),
        evidence_spans=_evidence(),
        composer_client=client,
        observation_structure_material=material,
    )
    assert candidate.composer_source == "ai_generated"
    assert candidate.composer_meta["observation_structure_dictionary_connected"] is True
    assert candidate.composer_meta["dictionary_must_not_generate_completed_sentence"] is True
    assert client.payload is not None
    assert "observation_structure_material" in client.payload


def test_phase4_display_gate_trace_receives_structure_gate_report_without_relaxing_gate() -> None:
    material = build_observation_structure_material(
        current_input={
            "memo": "大丈夫",
            "memo_action": "",
            "emotion_details": [{"type": "悲しみ", "strength": "strong"}],
            "category": ["仕事"],
        }
    )
    gate_report = observation_structure_material_gate_report(material)
    decision = decide_emlis_observation_display(
        comment_text="",
        reader_report=ListenerReaderReport(
            understandable=True,
            addressee_clear=True,
            speaker_integrity_ok=True,
            conversational=True,
            report_like=False,
            confidence=1.0,
        ),
        grounding_report=GroundingReport(
            passed=False,
            rejection_reasons=["empty_comment_text_without_candidate"],
        ),
        template_echo_report=TemplateEchoReport(passed=True),
        composer_source="unavailable",
        phase_completion_ready=False,
        observation_structure_gate_report=gate_report,
    )

    assert decision.observation_status == "unavailable"
    assert decision.comment_text == ""
    assert decision.gate_trace["observation_structure"]["selected_relation_ids"]
    assert "state_text_gap" in decision.gate_trace["observation_structure"]["selected_relation_ids"]
    assert decision.gate_trace["observation_structure"]["display_gate_relaxed"] is False
    assert decision.gate_trace["observation_structure"]["environment_state_output_frame_connected"] is True
    assert decision.gate_trace["display_gate"]["display_gate_relaxed"] is False


_PHASE3_ACTION_CONVERSION_MATERIAL_CASES: tuple[Mapping[str, Any], ...] = (
    {
        "case_id": "phase3_unexpressed_output_stop_could_not_say_single_word",
        "current_input": {
            "id": "action-update-001",
            "created_at": "2026-05-22T00:00:00Z",
            "memo": "言えなかった",
            "memo_action": "",
            "emotion_details": [{"type": "悲しみ", "strength": "medium"}],
            "category": ["人間関係"],
        },
        "expected_entry_ids": {"word_could_not_say"},
        "expected_relation_ids": {"unexpressed_output_stop"},
        "forbidden_relation_ids": {"thought_action_discrepancy", "user_agency_prompt"},
        "expected_low_information_candidate": False,
    },
    {
        "case_id": "phase3_unexpressed_output_stop_with_thought_action_gap",
        "current_input": {
            "id": "action-update-002",
            "created_at": "2026-05-22T00:01:00Z",
            "memo": "本当は嫌だったけど言えなかった",
            "memo_action": "笑って対応した",
            "emotion_details": [{"type": "怒り", "strength": "strong"}],
            "category": ["人間関係"],
        },
        "expected_entry_ids": {"word_could_not_say"},
        "expected_relation_ids": {"unexpressed_output_stop", "thought_action_discrepancy"},
        "forbidden_relation_ids": set(),
        "expected_low_information_candidate": False,
    },
    {
        "case_id": "phase3_self_shape_alignment_single_word",
        "current_input": {
            "id": "action-update-003",
            "created_at": "2026-05-22T00:02:00Z",
            "memo": "合わせた",
            "memo_action": "",
            "emotion_details": [{"type": "平穏", "strength": "weak"}],
            "category": ["人間関係"],
        },
        "expected_entry_ids": {"word_aligned_to_context"},
        "expected_relation_ids": {"self_shape_alignment"},
        "forbidden_relation_ids": {"thought_action_discrepancy", "priority_pressure"},
        "expected_low_information_candidate": False,
    },
    {
        "case_id": "phase3_action_conversion_history_gaman_single_word",
        "current_input": {
            "id": "action-update-004",
            "created_at": "2026-05-22T00:03:00Z",
            "memo": "我慢した",
            "memo_action": "",
            "emotion_details": [{"type": "悲しみ", "strength": "medium"}],
            "category": ["人間関係"],
        },
        "expected_entry_ids": {"word_gaman"},
        "expected_relation_ids": {"action_conversion_history"},
        "forbidden_relation_ids": {"thought_action_discrepancy", "conversion_history_closure", "load_accumulation"},
        "expected_low_information_candidate": False,
    },
    {
        "case_id": "phase3_action_conversion_history_with_thought_action_gap",
        "current_input": {
            "id": "action-update-005",
            "created_at": "2026-05-22T00:04:00Z",
            "memo": "本当は嫌だったけど我慢した",
            "memo_action": "言わずに対応した",
            "emotion_details": [{"type": "怒り", "strength": "strong"}],
            "category": ["人間関係"],
        },
        "expected_entry_ids": {"word_gaman"},
        "expected_relation_ids": {"action_conversion_history", "thought_action_discrepancy"},
        "forbidden_relation_ids": {"conversion_history_closure", "load_accumulation"},
        "expected_low_information_candidate": False,
    },
    {
        "case_id": "phase3_conversion_history_closure_with_unfinished_evidence",
        "current_input": {
            "id": "action-update-006",
            "created_at": "2026-05-22T00:05:00Z",
            "memo": "我慢したけど、まだ引っかかっている",
            "memo_action": "言わずに対応した",
            "emotion_details": [{"type": "悲しみ", "strength": "strong"}],
            "category": ["人間関係"],
        },
        "expected_entry_ids": {"word_gaman"},
        "expected_relation_ids": {"action_conversion_history", "conversion_history_closure", "thought_action_discrepancy"},
        "forbidden_relation_ids": set(),
        "expected_low_information_candidate": False,
    },
    {
        "case_id": "phase3_unformed_self_insight_wakaranai",
        "current_input": {
            "id": "action-update-007",
            "created_at": "2026-05-22T00:06:00Z",
            "memo": "わからない",
            "memo_action": "",
            "emotion_details": [{"type": "不安", "strength": "medium"}],
            "category": ["自分"],
        },
        "expected_entry_ids": {"word_wakaranai"},
        "expected_relation_ids": {"unformed_self_insight"},
        "forbidden_relation_ids": set(),
        "expected_low_information_candidate": None,
    },
)


@pytest.mark.parametrize("case", _PHASE3_ACTION_CONVERSION_MATERIAL_CASES, ids=lambda case: str(case["case_id"]))
def test_phase3_action_conversion_update_material_selection_is_evidence_bound(case: Mapping[str, Any]) -> None:
    material_meta = build_observation_structure_material(current_input=case["current_input"]).as_meta()
    selected_entry_ids = set(material_meta["selected_entry_ids"])
    selected_relation_ids = set(material_meta["selected_relation_ids"])

    assert set(case["expected_entry_ids"]).issubset(selected_entry_ids)
    assert set(case["expected_relation_ids"]).issubset(selected_relation_ids)
    assert set(case["forbidden_relation_ids"]).isdisjoint(selected_relation_ids)

    expected_low_information = case["expected_low_information_candidate"]
    if expected_low_information is not None:
        assert material_meta["low_information_candidate"] is expected_low_information
    if case["case_id"] == "phase3_unformed_self_insight_wakaranai":
        assert selected_relation_ids != {"low_information_weight"}
        assert "unformed_self_insight" in selected_relation_ids
